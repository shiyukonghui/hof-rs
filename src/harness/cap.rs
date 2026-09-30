//! DR-69 ③ — a ceiling on what one tool result may put into the model context.
//!
//! `smoke-t9`' attempt A died with `llm-connector chat request failed` (exit 5):
//! the Developer's step 93 (`dir /s /b /a "%TEMP%" | findstr …`) produced
//! **15,570,803 bytes** of stdout, that whole string became the next message's
//! observation, and the following chat request could not be sent.  The round's
//! trajectory was then unrecoverable.
//!
//! The harness reaches the shell through mini's [`Environment`] trait, so this
//! is the one boundary where "a tool result" becomes "the next request's
//! payload".  [`CappedEnvironment`] wraps whatever environment the harness
//! builds and bounds every result **before** it can be replayed:
//!
//! * the carried text is at most the ceiling plus the annotation;
//! * the annotation states the original size and that the remainder was
//!   dropped, so nobody can read a truncated result as a complete one; and
//! * a truncation is recorded in `Output::extra`, which mini serializes into
//!   the trajectory — the run's own record says a result was cut.

use mini_swe_agent::{Action, Environment, Output, Result as MiniResult};
use serde_json::{json, Value};

/// DR-69 ③: how many bytes of one tool result may enter the model context.
///
/// 64 KiB is generous for a command's output (the largest legitimate payload in
/// the recorded rounds is the battery's own evidence, which never travels
/// through this path) and three orders of magnitude below the 15.5 MB that
/// killed attempt A.
pub const DEFAULT_MAX_TOOL_OUTPUT_BYTES: usize = 64 * 1024;

/// DR-69 ③: the marker appended to a truncated result.
///
/// It is a *statement about the payload*, not a decoration: a reader (or the
/// model) must be able to tell that the result is incomplete.
pub const TRUNCATION_MARKER: &str =
    "[hoh: tool output truncated — the bytes above are only the head of the result]";

/// DR-69 ③: one capped tool result.
#[derive(Clone, Debug, PartialEq, Eq)]
pub struct CappedOutput {
    /// What may be carried into a later request.
    pub text: String,
    /// Whether anything was dropped.
    pub truncated: bool,
    /// The size of the result as the environment produced it.
    pub original_bytes: usize,
}

impl CappedOutput {
    /// The size of the carried text, including the annotation.
    pub fn carried_bytes(&self) -> usize {
        self.text.len()
    }
}

/// DR-69 ③: the annotation that replaces the dropped bytes.
fn truncation_note(shown: usize, total: usize) -> String {
    format!(
        "\n{TRUNCATION_MARKER}\n[hoh: {shown} of {total} bytes were carried; the remaining {} \
         bytes were dropped and are NOT part of this result. Re-run the command narrower, or \
         write its output to a file under the scratch directory and read a slice of it.]\n",
        total.saturating_sub(shown)
    )
}

/// DR-69 ③: bound one tool result.
///
/// The **head** is kept: for a shell result the first lines normally name what
/// failed, and a tail-only cut would silently drop the command's own diagnostic.
/// The cut respects UTF-8 boundaries, so the carried text is always valid.
pub fn cap_tool_output(text: &str, limit: usize) -> CappedOutput {
    let original_bytes = text.len();
    if original_bytes <= limit {
        return CappedOutput {
            text: text.to_string(),
            truncated: false,
            original_bytes,
        };
    }
    let mut cut = limit.min(original_bytes);
    while cut > 0 && !text.is_char_boundary(cut) {
        cut -= 1;
    }
    let mut capped = String::with_capacity(cut + 256);
    capped.push_str(&text[..cut]);
    capped.push_str(&truncation_note(cut, original_bytes));
    CappedOutput {
        text: capped,
        truncated: true,
        original_bytes,
    }
}

/// DR-69 ③: the environment the harness gives a role, with a ceiling on every
/// result.
pub struct CappedEnvironment {
    inner: Box<dyn Environment>,
    limit: usize,
}

impl CappedEnvironment {
    pub fn new(inner: Box<dyn Environment>, limit: usize) -> Self {
        Self { inner, limit }
    }

    /// The ceiling in force.
    pub fn limit(&self) -> usize {
        self.limit
    }
}

#[async_trait::async_trait]
impl Environment for CappedEnvironment {
    async fn execute(
        &self,
        action: &Action,
        cwd: Option<&str>,
        timeout: Option<u64>,
    ) -> MiniResult<Output> {
        let mut output = self.inner.execute(action, cwd, timeout).await?;
        let capped = cap_tool_output(&output.output, self.limit);
        if !capped.truncated {
            return Ok(output);
        }
        output.output = capped.text;
        // mini serializes `extra` into the trajectory, so the run's own record
        // says that this result was cut and by how much.
        output
            .extra
            .insert("hoh_output_truncated".to_string(), json!(true));
        output.extra.insert(
            "hoh_output_original_bytes".to_string(),
            json!(capped.original_bytes),
        );
        output
            .extra
            .insert("hoh_output_limit_bytes".to_string(), json!(self.limit));
        Ok(output)
    }

    fn get_template_vars(&self) -> Value {
        self.inner.get_template_vars()
    }

    fn serialize(&self) -> Value {
        self.inner.serialize()
    }

    fn cleanup(&self) -> anyhow::Result<()> {
        self.inner.cleanup()
    }
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn a_result_within_the_ceiling_is_unchanged() {
        let capped = cap_tool_output("abc", DEFAULT_MAX_TOOL_OUTPUT_BYTES);
        assert_eq!(
            capped,
            CappedOutput {
                text: "abc".to_string(),
                truncated: false,
                original_bytes: 3,
            }
        );
    }

    /// DR-69 ③: the cut never splits a multi-byte character.
    #[test]
    fn the_cut_respects_utf8_boundaries() {
        let text = "é".repeat(10);
        let capped = cap_tool_output(&text, 5);
        assert!(capped.truncated);
        assert!(
            capped.text.starts_with("éé"),
            "the head must be whole characters: {:?}",
            &capped.text[..8]
        );
        assert_eq!(capped.carried_bytes() > 0, true);
    }

    /// A zero ceiling must still produce a usable, annotated result.
    #[test]
    fn a_zero_ceiling_still_carries_the_annotation() {
        let capped = cap_tool_output("abcdef", 0);
        assert!(capped.truncated);
        assert!(capped.text.contains(TRUNCATION_MARKER));
        assert_eq!(capped.original_bytes, 6);
    }
}
