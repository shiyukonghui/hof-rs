//! DR-69 ③ — a ceiling on what one tool result may put into the model context.
//!
//! `smoke-t9`' attempt A died with `llm-connector chat request failed` (exit 5)
//! because step 93's `dir /s /b /a "%TEMP%" | findstr …` produced **15,570,803
//! bytes** of stdout and the whole thing was replayed into the next chat
//! request as the tool observation.  The round's own trajectory was then
//! unrecoverable.
//!
//! The rule is: a single tool result is **capped**, the cap is **stated in the
//! result itself**, and the oversized bytes never enter a later request's
//! payload.  Everything here is offline: the only command executed is a local
//! `type` of a file this test created in a temporary directory.

use hof_rs::harness::cap::{
    cap_tool_output, CappedEnvironment, DEFAULT_MAX_TOOL_OUTPUT_BYTES, TRUNCATION_MARKER,
};
use mini_swe_agent::environments::{LocalEnvironment, LocalEnvironmentConfig};
use mini_swe_agent::{Action, Environment, Output, Result as MiniResult};
use serde_json::{json, Value};

/// The exact stdout size the real incident measured.
const INCIDENT_BYTES: usize = 15_570_803;

/// An environment double that returns one oversized result, so the ceiling can
/// be tested without running anything.
struct HugeOutputEnvironment {
    bytes: usize,
}

#[async_trait::async_trait]
impl Environment for HugeOutputEnvironment {
    async fn execute(
        &self,
        _action: &Action,
        _cwd: Option<&str>,
        _timeout: Option<u64>,
    ) -> MiniResult<Output> {
        Ok(Output::success("x".repeat(self.bytes), 0))
    }

    fn get_template_vars(&self) -> Value {
        json!({})
    }

    fn serialize(&self) -> Value {
        json!({})
    }
}

/// The mandated red test: an oversized tool result must be truncated, annotated,
/// and bounded — and the bounded text is exactly what a later request carries.
#[test]
fn an_oversized_tool_result_is_truncated_and_annotated() {
    let huge = "x".repeat(INCIDENT_BYTES);
    let capped = cap_tool_output(&huge, DEFAULT_MAX_TOOL_OUTPUT_BYTES);

    assert!(capped.truncated, "15.5 MB must exceed the ceiling");
    assert_eq!(
        capped.original_bytes, INCIDENT_BYTES,
        "the original size must be recorded, not guessed"
    );
    assert!(
        capped.text.len() < INCIDENT_BYTES / 10,
        "the carried text must be bounded, got {}",
        capped.text.len()
    );
    assert!(
        capped.text.starts_with('x'),
        "the head of the result is the useful part"
    );
    assert!(
        capped.text.contains(TRUNCATION_MARKER),
        "the truncation must be explicit in the carried text: {}",
        &capped.text[capped.text.len().saturating_sub(200)..]
    );
    assert!(
        capped.text.contains(&INCIDENT_BYTES.to_string()),
        "the annotation must name how many bytes were dropped"
    );
    // `text` **is** the payload: there is no second copy of the oversized bytes.
    assert!(
        !capped
            .text
            .contains(&"x".repeat(DEFAULT_MAX_TOOL_OUTPUT_BYTES + 1)),
        "the capped text may not still carry an over-ceiling run of bytes"
    );

    // A result under the ceiling is passed through byte for byte.
    let small = cap_tool_output("hello\n", DEFAULT_MAX_TOOL_OUTPUT_BYTES);
    assert!(!small.truncated);
    assert_eq!(small.text, "hello\n");
    assert_eq!(small.original_bytes, 6);
}

/// The ceiling is enforced at the environment boundary — the one place a tool
/// result becomes the next request's observation.
#[tokio::test]
async fn the_capped_environment_bounds_what_a_later_request_would_carry() {
    let inner: Box<dyn Environment> = Box::new(HugeOutputEnvironment {
        bytes: INCIDENT_BYTES,
    });
    let environment = CappedEnvironment::new(inner, DEFAULT_MAX_TOOL_OUTPUT_BYTES);
    let output = environment
        .execute(&Action::new("irrelevant"), None, None)
        .await
        .expect("the double always answers");

    assert!(
        output.output.len() < INCIDENT_BYTES / 10,
        "the observation a request would carry must be bounded, got {}",
        output.output.len()
    );
    assert!(output.output.contains(TRUNCATION_MARKER));
    let recorded = output
        .extra
        .get("hoh_output_truncated")
        .cloned()
        .unwrap_or(Value::Null);
    assert_eq!(
        recorded,
        json!(true),
        "the truncation must be recorded: {recorded}"
    );
    assert_eq!(
        output.extra.get("hoh_output_original_bytes"),
        Some(&json!(INCIDENT_BYTES)),
        "the dropped size must be recorded"
    );
}

/// The ceiling must survive contact with the **real** environment the harness
/// uses (mini's `LocalEnvironment`, i.e. `cmd.exe` on Windows), not only with a
/// double.
#[tokio::test]
async fn the_ceiling_holds_for_the_real_local_environment() {
    let temp = tempfile::tempdir().unwrap();
    let path = temp.path().join("big.txt");
    std::fs::write(&path, "y".repeat(2 * 1024 * 1024)).unwrap();

    let config = LocalEnvironmentConfig {
        cwd: temp.path().to_string_lossy().into_owned(),
        timeout: 60,
        ..LocalEnvironmentConfig::default()
    };
    let inner: Box<dyn Environment> = Box::new(LocalEnvironment::new(config));
    let environment = CappedEnvironment::new(inner, DEFAULT_MAX_TOOL_OUTPUT_BYTES);
    let output = environment
        .execute(&Action::new(format!("type {}", path.display())), None, None)
        .await
        .expect("the local shell answers");

    assert!(
        output.output.len() <= DEFAULT_MAX_TOOL_OUTPUT_BYTES + TRUNCATION_MARKER.len() + 256,
        "a real 2 MiB result must be capped, got {}",
        output.output.len()
    );
    assert!(
        output.output.contains(TRUNCATION_MARKER),
        "{}",
        output.output.len()
    );
    assert_eq!(output.extra.get("hoh_output_truncated"), Some(&json!(true)));
}

/// A `CappedEnvironment` must not change anything else about the result.
#[tokio::test]
async fn a_result_under_the_ceiling_is_untouched() {
    let inner: Box<dyn Environment> = Box::new(HugeOutputEnvironment { bytes: 8 });
    let environment = CappedEnvironment::new(inner, DEFAULT_MAX_TOOL_OUTPUT_BYTES);
    let output = environment
        .execute(&Action::new("irrelevant"), None, None)
        .await
        .expect("the double always answers");

    assert_eq!(output.output, "xxxxxxxx");
    assert_eq!(output.returncode, 0);
    assert!(
        output.extra.get("hoh_output_truncated").is_none(),
        "a clean result must not be marked: {:?}",
        output.extra
    );
}
