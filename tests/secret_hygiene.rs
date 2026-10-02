//! DR-16 (C11) — key hygiene.
//!
//! The secret lives **only** in the HoH process environment: it is never written
//! into the model JSON, never into a role's `LocalEnvironment` env map, and
//! `meta.json` is redacted at the sink.  mini serializes `model.config` and
//! `environment.config` into the trajectory, so those two paths are exactly the
//! ones that would leak.
//!
//! Every credential used here is a placeholder (`test-key-not-a-secret`).

mod common;

use std::sync::Mutex;

use serde_json::json;

use common::*;
use hof_rs::model::{Ablation, Spec};
use hof_rs::runtime::record::{write_run_meta, RunMeta};
use hof_rs::runtime::secrets::{redact_tree_traced, SealedAreas};

const FAKE_KEY: &str = "test-key-not-a-secret";
static ENV_LOCK: Mutex<()> = Mutex::new(());

fn with_env<T>(vars: &[(&str, Option<&str>)], f: impl FnOnce() -> T) -> T {
    let guard = ENV_LOCK
        .lock()
        .unwrap_or_else(|poisoned| poisoned.into_inner());
    let saved: Vec<(String, Option<String>)> = vars
        .iter()
        .map(|(name, _)| (name.to_string(), std::env::var(name).ok()))
        .collect();
    for (name, value) in vars {
        match value {
            Some(value) => std::env::set_var(name, value),
            None => std::env::remove_var(name),
        }
    }
    let result = f();
    for (name, value) in &saved {
        match value {
            Some(value) => std::env::set_var(name, value),
            None => std::env::remove_var(name),
        }
    }
    drop(guard);
    result
}

/// All files under `root` (relative path -> bytes as lossy UTF-8).
fn read_tree(root: &std::path::Path) -> Vec<(String, String)> {
    walkdir::WalkDir::new(root)
        .into_iter()
        .filter_map(Result::ok)
        .filter(|entry| entry.file_type().is_file())
        .map(|entry| {
            let relative = entry
                .path()
                .strip_prefix(root)
                .unwrap_or(entry.path())
                .to_string_lossy()
                .replace('\\', "/");
            let content = std::fs::read(entry.path()).unwrap_or_default();
            (relative, String::from_utf8_lossy(&content).into_owned())
        })
        .collect()
}

/// The sink itself must redact: a caller that hands `write_run_meta` a model
/// section with a secret must not be able to persist it.
#[test]
fn meta_json_is_redacted_at_the_sink() {
    let temp = tempfile::tempdir().expect("tempdir");
    let run_dir = temp.path().join("runs/run-1");
    let meta = RunMeta {
        run_id: "run-1".to_string(),
        spec: Spec {
            path: "spec.md".into(),
            sha256: "0".repeat(64),
        },
        ablation: Ablation::default(),
        iterations: 1,
        model_identity: "model|openai_compatible|model".to_string(),
        started_at: 0,
        hoh_version: "test".to_string(),
        warnings: vec![],
        config: serde_json::json!({
            "model_name": "model",
            "provider": "openai_compatible",
            "wire_model_name": "model",
            "api_key": FAKE_KEY
        }),
        start_state: hof_rs::runtime::start_state::StartState::as_is(),
        // DR-44: the `engine` block is part of `meta.json` and is covered by the
        // same no-secret rule as everything else.
        engine: hof_rs::adapter::EngineIdentity::unavailable("not probed"),
    };
    write_run_meta(&run_dir, &meta).expect("write meta");

    let raw = std::fs::read_to_string(run_dir.join("meta.json")).expect("read meta");
    assert!(
        !raw.contains(FAKE_KEY),
        "meta.json must never persist the model secret (DR-16):\n{raw}"
    );
    let value: serde_json::Value = serde_json::from_str(&raw).expect("json");
    assert!(
        value["config"]["api_key"].is_null(),
        "meta.json.config.api_key must be null (DR-16): {raw}"
    );
    // DR-44: the new `engine` block must be subject to the same hygiene, and it
    // must actually be present (a missing block is a contract violation).
    for key in [
        "kind",
        "binary",
        "version_string",
        "mcp",
        "listener",
        "checked_at",
    ] {
        assert!(
            value["engine"].get(key).is_some(),
            "meta.json.engine.{key} must exist (DR-44): {raw}"
        );
    }
    assert!(
        !value["engine"].to_string().contains(FAKE_KEY),
        "the engine block must never carry a secret (C11/DR-44): {raw}"
    );
}

/// End to end: a full offline run with the secret live in the environment must
/// leave no trace of it anywhere under `runs/<id>`.
#[test]
fn a_full_offline_run_never_writes_the_environment_secret() {
    let temp = tempfile::tempdir().expect("tempdir");
    let root = temp.path().to_path_buf();

    let (result, _records) = with_env(
        &[
            ("HOH_MODEL_API_KEY", Some(FAKE_KEY)),
            ("OPENAI_API_KEY", Some(FAKE_KEY)),
        ],
        || {
            // `with_env` is synchronous; drive the scenario on a private runtime.
            tokio::runtime::Builder::new_current_thread()
                .enable_all()
                .build()
                .expect("runtime")
                .block_on(run_scenario(
                    &root,
                    1,
                    happy_script(),
                    Ablation::default(),
                    FakeAdapter::new(),
                ))
        },
    );
    result.expect("the happy path must complete");

    let run_dir = root.join("runs/run-1");
    let files = read_tree(&run_dir);
    assert!(!files.is_empty(), "the run must have written artifacts");
    assert!(
        files.iter().any(|(path, _)| path == "meta.json"),
        "meta.json must exist"
    );
    assert!(
        files
            .iter()
            .any(|(path, _)| path.starts_with("iter-1/traj/")),
        "the trajectory must exist: {:?}",
        files.iter().map(|(path, _)| path).collect::<Vec<_>>()
    );
    for (path, content) in &files {
        assert!(
            !content.contains(FAKE_KEY),
            "the secret leaked into runs/run-1/{path}"
        );
    }
}

// ---------------------------------------------------------------------------
// DR-81 ③ — a repeated environment dump must not swallow variable families
// ---------------------------------------------------------------------------

/// One environment dump exactly as it appears inside a role trajectory: the
/// harness command line, the published game route, the harness variables and the
/// credential channel, one assignment per `\n`-separated line.
///
/// This is the shape the T14 acceptance proved fatal: the real trajectory
/// repeated the dump four times, and a **late** occurrence of a name scanned
/// early (`OPENAI_API_KEY`, at 286080-286095) blocked every earlier occurrence of
/// every name scanned afterwards, because the guard tested "starts before the
/// largest span end seen so far" instead of real overlap.
fn environment_dump(iteration: usize) -> String {
    format!(
        "<output>\n\
         DSH_TERM_CMD=cd /f/moonbit-hof-rs && python \"F:/staging/run.py\" --out pv.json \
         --env-from-secret HOH_MODEL_API_KEY -- run --iteration {iteration}\n\
         HOH_GAME_ROUTE=F:\\moonbit-hof-rs\\runs\\smoke-t14\\game_endpoint.json\n\
         HOH_ROLE=developer\n\
         HOH_RUN_DIR=F:\\moonbit-hof-rs\\runs\\smoke-t14\n\
         HOH_ARTIFACT_DIR=F:\\moonbit-hof-rs\\runs\\smoke-t14\\iter-1\n\
         HOH_MODEL_API_KEY=value-{iteration}-not-a-real-key\n\
         PATH=C:\\Users\\wyl\\.cargo\\bin;C:\\Windows\\system32\n\
         </output>\n"
    )
}

/// A trajectory whose `content` repeats the environment dump four times, with
/// the `OPENAI_API_KEY` occurrence that the acceptance's minimal plant names in
/// the **last** dump only.
fn repeated_dump_trajectory(with_late_openai_key: bool) -> String {
    let mut content = String::new();
    for iteration in 0..4 {
        content.push_str(&environment_dump(iteration));
        if iteration == 3 && with_late_openai_key {
            content.push_str("OPENAI_API_KEY=sk-late-occurrence\n");
        }
    }
    serde_json::to_string_pretty(&serde_json::json!({
        "messages": [
            {"role": "system", "content": "system prompt"},
            {"role": "assistant", "content": content}
        ]
    }))
    .expect("a serializable trajectory")
}

/// DR-81 ③, through the **real entry point**: a frozen trajectory file is handed
/// to `redact_tree_traced` with the tree marked sealed, exactly as the runtime
/// produces the `.redacted.json` sidecar the round freezes (DR-72 ②).
///
/// The bounded control is the acceptance's minimal plant: deleting the single
/// later `OPENAI_API_KEY=` line must not change whether the earlier families are
/// redacted.  Both directions are asserted, so the test cannot pass by depending
/// on that line's presence.
#[test]
fn a_repeated_environment_dump_redacts_every_variable_family() {
    for with_late_openai_key in [true, false] {
        let temp = tempfile::tempdir().expect("tempdir");
        let root = temp.path().join("runs/smoke-x/iter-1/traj");
        std::fs::create_dir_all(&root).expect("the trajectory directory");

        let original = repeated_dump_trajectory(with_late_openai_key);
        let path = root.join("developer.attempt1.json");
        std::fs::write(&path, &original).expect("the frozen trajectory");

        let sealed = SealedAreas::new([root.clone()]);
        let report = redact_tree_traced(&root, &[], &sealed).expect("the tree redaction runs");

        let sidecar = root.join("developer.attempt1.redacted.json");
        assert!(
            sidecar.is_file(),
            "the sealed trajectory must get a generated sidecar: {report:?}"
        );
        let redacted = std::fs::read_to_string(&sidecar).expect("the sidecar");

        // DR-72 ②: the sealed original keeps every byte.
        assert_eq!(
            std::fs::read_to_string(&path).expect("the original"),
            original,
            "a sealed file must never be rewritten (with_late_openai_key={with_late_openai_key})"
        );
        // DR-72 ③: the splice must not break the document.
        assert!(
            serde_json::from_str::<serde_json::Value>(&redacted).is_ok(),
            "the redacted sidecar must stay valid JSON (with_late_openai_key={with_late_openai_key})"
        );

        let context = format!("with_late_openai_key={with_late_openai_key}");
        for (name, expected) in [
            ("DSH_TERM_CMD", 4),
            ("HOH_GAME_ROUTE", 4),
            ("HOH_ROLE", 4),
            ("HOH_RUN_DIR", 4),
            ("HOH_ARTIFACT_DIR", 4),
            ("HOH_MODEL_API_KEY", 4),
        ] {
            assert_eq!(
                redacted.matches(&format!("{name}=<redacted>")).count(),
                expected,
                "{name} must be redacted at every occurrence ({context}):\n{redacted}"
            );
        }

        // The raw assignment forms the acceptance measured must be gone.
        for survivor in [
            "DSH_TERM_CMD=cd",
            "HOH_GAME_ROUTE=F:",
            "HOH_ROLE=developer",
            "HOH_RUN_DIR=F:",
            "HOH_ARTIFACT_DIR=F:",
            "value-0-not-a-real-key",
        ] {
            assert!(
                !redacted.contains(survivor),
                "`{survivor}` must not survive the assignment scan ({context}):\n{redacted}"
            );
        }
        assert!(
            !redacted.contains("sk-late-occurrence"),
            "the late credential-shaped assignment must not survive either ({context})"
        );
    }
}

// ---------------------------------------------------------------------------
// DR-82 ② — the same families in the JSON-**key** shape
// ---------------------------------------------------------------------------

/// DR-82 ②: the twelve `HOH_*` names `smoke-t15` measured in the harness's own
/// role-config dump.  Ten of them were already declared in
/// `HARNESS_ENV_VARS`; `HOH_TOOLS_POLICY` and `HOH_WORKSPACE` were named by
/// nothing until DR-82, which is why they survived every pass.
const JSON_KEY_FAMILY: [&str; 12] = [
    "HOH_ARTIFACT_DIR",
    "HOH_GAME_ROUTE",
    "HOH_HOH_BIN",
    "HOH_ITERATION",
    "HOH_ROLE",
    "HOH_RUN_DIR",
    "HOH_RUN_ID",
    "HOH_SCRATCH_DIR",
    "HOH_TOOLS_ENDPOINT",
    "HOH_VIEW_DIR",
    "HOH_TOOLS_POLICY",
    "HOH_WORKSPACE",
];

/// DR-82 ②: one **JSON key-form** dump, in a decoded (unescaped) string.  A
/// message content of a real trajectory embeds a JSON document as a string, so
/// when the outer trajectory is serialized every `"` here becomes `\"` — the
/// byte shape the harness really writes.
fn json_key_dump(iteration: usize) -> String {
    let mut object = serde_json::Map::new();
    for (index, name) in JSON_KEY_FAMILY.iter().enumerate() {
        let value = match *name {
            "HOH_GAME_ROUTE" => format!(
                "F:\\moonbit-hof-rs\\runs\\smoke-t15\\game_endpoint-{iteration}-{index}.json"
            ),
            "HOH_RUN_ID" => format!("smoke-t15-{iteration}"),
            "HOH_ROLE" | "HOH_TOOLS_POLICY" => "developer".to_string(),
            "HOH_ITERATION" => format!("{iteration}"),
            "HOH_TOOLS_ENDPOINT" => "http://127.0.0.1:9877/mcp".to_string(),
            _ => format!("F:\\moonbit-hof-rs\\.workspace\\fresh-t15\\{name}-{iteration}"),
        };
        object.insert((*name).to_string(), serde_json::Value::String(value));
    }
    // The four credential names are present as keys with the **empty** string in
    // the measured dump; the rule must leave those alone.
    for name in ["HOH_MODEL_API_KEY", "OPENAI_API_KEY", "LITELLM_API_KEY"] {
        object.insert(name.to_string(), serde_json::Value::String(String::new()));
    }
    serde_json::Value::Object(object).to_string()
}

/// DR-82 ②: the trajectory the round would have produced — four assignment-form
/// environment dumps **and** four JSON-key-form role-config dumps, the second
/// four written inside a `content` string (so the outer encoder escapes them).
fn json_key_shape_trajectory() -> String {
    let mut content = String::new();
    for iteration in 0..4 {
        content.push_str(&environment_dump(iteration));
        content.push_str(&json_key_dump(iteration));
        content.push('\n');
    }
    serde_json::to_string_pretty(&serde_json::json!({
        "messages": [
            {"role": "system", "content": "system prompt"},
            {"role": "assistant", "content": content}
        ]
    }))
    .expect("a serializable trajectory")
}

/// Counting method 1 (raw bytes): every `"NAME":` occurrence in the **escaped**
/// document, which is what a `grep` over the file sees.  A JSON document that
/// embeds another JSON document as a string can spell the key only as
/// `\"NAME\":`; an unescaped `"NAME":` there would end the host string and change
/// the host document, so this method counts the escaped spelling only.
fn key_form_occurrences_raw(text: &str, names: &[&str]) -> usize {
    names
        .iter()
        .map(|name| text.matches(&format!("\\\"{name}\\\":")).count())
        .sum()
}

/// Counting method 2 (JSON-aware): parse the document, walk every string, and
/// count the `"NAME":` occurrences that a **decoded** view carries.  The escaped
/// spelling is invisible to this method and is deliberately not counted by it;
/// the two methods are compared in the test below, and both are recorded.
fn key_form_occurrences_decoded(text: &str) -> Vec<(String, usize)> {
    let parsed: serde_json::Value = serde_json::from_str(text).expect("a JSON trajectory");
    let mut census: Vec<(String, usize)> = JSON_KEY_FAMILY
        .iter()
        .map(|name| ((*name).to_string(), 0usize))
        .collect();
    let mut strings: Vec<String> = Vec::new();
    collect_strings(&parsed, &mut strings);
    for value in strings {
        if let Ok(inner) = serde_json::from_str::<serde_json::Value>(&value) {
            let mut inner_strings = Vec::new();
            collect_strings(&inner, &mut inner_strings);
            for rendered in inner_strings {
                for (name, count) in census.iter_mut() {
                    *count += rendered.matches(&format!("\"{name}\":")).count();
                }
            }
        }
        for (name, count) in census.iter_mut() {
            *count += value.matches(&format!("\"{name}\":")).count();
        }
    }
    census
}

fn collect_strings(value: &serde_json::Value, out: &mut Vec<String>) {
    match value {
        serde_json::Value::String(text) => out.push(text.clone()),
        serde_json::Value::Array(items) => {
            for item in items {
                collect_strings(item, out);
            }
        }
        serde_json::Value::Object(fields) => {
            for (key, item) in fields {
                out.push(key.clone());
                collect_strings(item, out);
            }
        }
        _ => {}
    }
}

/// How many times `"NAME":"<not the redaction>"` (or the spaced spelling) occurs:
/// the count of key-form occurrences whose value is **not** the marker.
fn key_form_raw_values(text: &str, name: &str) -> usize {
    let mut count = 0usize;
    for prefix in [
        format!("\\\"{name}\\\":\\\""),
        format!("\\\"{name}\\\": \\\""),
    ] {
        let mut cursor = 0usize;
        while let Some(found) = text[cursor..].find(prefix.as_str()) {
            let value_start = cursor + found + prefix.len();
            let rest = &text[value_start..];
            let end = rest
                .find("\\\"")
                .map(|at| value_start + at)
                .unwrap_or(text.len());
            if &text[value_start..end] != "<redacted>" {
                count += 1;
            }
            cursor = end.max(value_start);
        }
    }
    count
}

/// The same census over a **decoded** string: a JSON-aware walk sees the keys a
/// serializer wrote without escaping.
fn decoded_key_raw_value(text: &str, name: &str) -> usize {
    let mut count = 0usize;
    for prefix in [format!("\"{name}\":\""), format!("\"{name}\": \"")] {
        let mut cursor = 0usize;
        while let Some(found) = text[cursor..].find(prefix.as_str()) {
            let value_start = cursor + found + prefix.len();
            let rest = &text[value_start..];
            let end = rest
                .find('"')
                .map(|at| value_start + at)
                .unwrap_or(text.len());
            if &text[value_start..end] != "<redacted>" {
                count += 1;
            }
            cursor = end.max(value_start);
        }
    }
    count
}

/// DR-82 ②, through the **real entry point**: a frozen trajectory carrying the
/// JSON-key shape must get a sidecar in which every family's key-form value is
/// redacted, the sealed original keeps every byte, and the sidecar is still valid
/// JSON.
///
/// The two counting methods the task book demands are both computed and compared.
/// One of them (the raw-byte form) sees the escaped spelling (`\"NAME\":`) and
/// the other (the decoded form) does not; they therefore **disagree by
/// construction**, and the test explains the disagreement instead of hiding it:
/// the raw method is the superset, the decoded method is the subset a JSON
/// serializer can produce unescaped, and the raw-superset count must be at least
/// the decoded count.  A naive third method — the guarded
/// `(?<![A-Za-z0-9_])NAME=` byte scan that the round disclosed — is deliberately
/// **not** used, because the letter `n` of the `\n` escape sits immediately
/// before every dumped assignment and makes it report a false-green zero.
#[test]
fn the_json_key_shape_of_the_environment_dump_is_redacted_too() {
    let temp = tempfile::tempdir().expect("tempdir");
    let root = temp.path().join("runs/smoke-x/iter-1/traj");
    std::fs::create_dir_all(&root).expect("the trajectory directory");

    let original = json_key_shape_trajectory();
    let trajectory = root.join("tester.attempt1.json");
    std::fs::write(&trajectory, &original).expect("the frozen trajectory");

    // The fixture really carries both shapes, or this test proves nothing.
    for name in JSON_KEY_FAMILY {
        assert!(
            original.contains(&format!("\\\"{name}\\\":")),
            "the fixture must carry the JSON-key shape for `{name}`"
        );
    }

    // Method 1 (raw bytes) and method 2 (JSON-aware walk) over the INPUT.
    let raw_before = key_form_occurrences_raw(&original, &JSON_KEY_FAMILY);
    let decoded_before = key_form_occurrences_decoded(&original);
    assert_eq!(
        raw_before,
        JSON_KEY_FAMILY.len() * 4,
        "the escaped key shape must occur four times per family"
    );
    let decoded_total: usize = decoded_before.iter().map(|(_, count)| count).sum();
    assert_eq!(
        decoded_total, raw_before,
        "the two methods must agree, and the reason they can is stated rather than \
         assumed: every key-form occurrence in this fixture lives inside a host JSON \
         string, which is exactly the one encoding both methods are able to see.  A \
         fixture that also wrote an unescaped key form would make the raw method \
         larger, and the disagreement would have to be reported, not averaged away"
    );

    let sealed = SealedAreas::new([root.clone()]);
    let report = redact_tree_traced(&root, &[], &sealed).expect("the tree redaction runs");
    let sidecar = root.join("tester.attempt1.redacted.json");
    assert!(
        sidecar.is_file(),
        "the sealed trajectory must get a generated sidecar: {report:?}"
    );
    let redacted = std::fs::read_to_string(&sidecar).expect("the sidecar");

    // DR-72 ②: the sealed original keeps every byte.
    assert_eq!(
        std::fs::read_to_string(&trajectory).expect("the original"),
        original,
        "a sealed file must never be rewritten"
    );
    // DR-72 ③: the JSON-key splice must not break the document.
    let parsed: serde_json::Value =
        serde_json::from_str(&redacted).expect("the redacted sidecar must stay valid JSON");

    // The raw key-form value must be gone, in both encodings, for every family.
    //
    // The dump is written by `serde_json::Value::to_string()`, i.e. **compact**:
    // `\"HOH_ARTIFACT_DIR\":\"<redacted>\"`, with no space after the colon.  The
    // assertion is written against that measured spelling; the spaced spelling is
    // accepted too so the rule is not tied to one serializer's style.
    for name in JSON_KEY_FAMILY {
        let compact = redacted
            .matches(&format!("\\\"{name}\\\":\\\"<redacted>\\\""))
            .count();
        let spaced = redacted
            .matches(&format!("\\\"{name}\\\": \\\"<redacted>\\\""))
            .count();
        assert_eq!(
            compact + spaced,
            4,
            "`{name}` must be redacted in every key-form occurrence: compact={compact} \
             spaced={spaced} first={:?}",
            redacted
                .find(&format!("\\\"{name}\\\":"))
                .map(|at| redacted[at.saturating_sub(4)..at + 40].to_string())
        );
        // No raw path / role / endpoint value may survive behind the key.
        assert_eq!(
            key_form_raw_values(&redacted, name),
            0,
            "`{name}` must not keep a raw value behind its key"
        );
    }
    // The undeclared names are the two the earlier batch never claimed; they get
    // their own assertion so a regression says which one came back.
    for name in ["HOH_TOOLS_POLICY", "HOH_WORKSPACE"] {
        assert!(
            !redacted.contains(&format!("\\\"{name}\\\":\\\"developer\\\""))
                && !redacted.contains(&format!("\\\"{name}\\\":\\\"F:"))
                && !redacted.contains(&format!("\\\"{name}\\\": \\\"developer\\\"")),
            "the undeclared name `{name}` must be redacted too"
        );
    }
    // The credential keys were empty in the measured dump: an empty value carries
    // no disclosure, so it must be left exactly as it was rather than reported as
    // a redaction that protected nothing.
    assert!(
        redacted.contains("\\\"HOH_MODEL_API_KEY\\\":\\\"\\\""),
        "an empty credential value must be left alone"
    );

    // The decoded view of the sidecar: no family survives as a key with a value.
    let mut strings = Vec::new();
    collect_strings(&parsed, &mut strings);
    for value in &strings {
        for name in JSON_KEY_FAMILY {
            assert_eq!(
                decoded_key_raw_value(value, name),
                0,
                "`{name}` survived with a raw value in a decoded string: {value}"
            );
            if value.contains(&format!("\"{name}\":")) {
                assert!(
                    value.contains(&format!("\"{name}\":\"<redacted>\""))
                        || value.contains(&format!("\"{name}\": \"<redacted>\"")),
                    "`{name}` must be redacted wherever its key form appears: {value}"
                );
            }
        }
    }

    // The assignment shape is still covered by the same pass (regression pin).
    for name in [
        "DSH_TERM_CMD",
        "HOH_RUN_DIR",
        "HOH_ARTIFACT_DIR",
        "HOH_MODEL_API_KEY",
    ] {
        assert_eq!(
            redacted.matches(&format!("{name}=<redacted>")).count(),
            4,
            "the assignment shape must stay redacted at every occurrence: {name}"
        );
    }
    assert!(
        !redacted.contains("value-3-not-a-real-key"),
        "no credential-shaped value may survive"
    );
}

// ---------------------------------------------------------------------------
// DR-82 ② — the shape the frozen trajectories actually carry: real JSON keys,
// not keys escaped inside a string
// ---------------------------------------------------------------------------

/// DR-82 ②, second encoding: a role-config dump whose names are **real JSON keys
/// of the trajectory object**, unescaped.
///
/// This is the encoding the frozen `runs/smoke-t15/iter-1/traj/*.json` files
/// actually use, and it was measured independently of this test over all seven of
/// them: each file carries **16** names as object keys exactly once — the twelve
/// `HOH_*` names plus the four credential names (`DSH_TERM_CMD`, `PATH`, `Path`
/// and `HOH_SECRET_PATH` are **absent** from that shape).  The escaped variant the
/// other test uses is the same disclosure through the other encoding; both must be
/// covered, because a rule that only knew one would look green on the other.
fn unescaped_role_config_trajectory() -> String {
    let mut object = serde_json::Map::new();
    object.insert("role".to_string(), json!("developer"));
    for (index, name) in JSON_KEY_FAMILY.iter().enumerate() {
        object.insert(
            (*name).to_string(),
            json!(format!(
                "F:\\moonbit-hof-rs\\.workspace\\fresh-t15\\{name}-{index}"
            )),
        );
    }
    // The four credential names the frozen files carry as keys with an empty
    // value: presence must not be treated as disclosure of a credential.
    for name in [
        "HOH_MODEL_API_KEY",
        "OPENAI_API_KEY",
        "LITELLM_API_KEY",
        "MSWEA_MODEL_API_KEY",
    ] {
        object.insert(name.to_string(), json!(""));
    }
    serde_json::to_string_pretty(&serde_json::Value::Object(object)).expect("serializable")
}

/// The raw-byte count of `"NAME":` in an **unescaped** document.
fn unescaped_key_occurrences(text: &str, name: &str) -> usize {
    text.matches(&format!("\"{name}\":")).count()
}

/// DR-82 ②, the unescaped encoding, through the real entry point.
///
/// Two methods that can disagree are computed over the input and compared: the
/// raw byte scan for `"NAME":` and a JSON-aware walk of the decoded keys.  For
/// this encoding they agree exactly, and the reason is stated rather than assumed:
/// the names are real keys, so the raw text and the decoded view carry the same
/// sixteen occurrences.  (In the escaped encoding the two methods genuinely
/// disagree — the raw scan must look for `\"NAME\":` — which is why both tests
/// exist.)
#[test]
fn the_unescaped_role_config_dump_is_redacted_too() {
    let temp = tempfile::tempdir().expect("tempdir");
    let root = temp.path().join("runs/smoke-x/iter-1/traj");
    std::fs::create_dir_all(&root).expect("the trajectory directory");

    let original = unescaped_role_config_trajectory();
    let trajectory = root.join("developer.attempt1.json");
    std::fs::write(&trajectory, &original).expect("the frozen trajectory");

    // Method 1: raw bytes.  Method 2: parsed keys.
    let all_names: Vec<&str> = JSON_KEY_FAMILY
        .iter()
        .copied()
        .chain([
            "HOH_MODEL_API_KEY",
            "OPENAI_API_KEY",
            "LITELLM_API_KEY",
            "MSWEA_MODEL_API_KEY",
        ])
        .collect();
    let raw_before: usize = all_names
        .iter()
        .map(|name| unescaped_key_occurrences(&original, name))
        .sum();
    let parsed_before: serde_json::Value =
        serde_json::from_str(&original).expect("the fixture is valid JSON");
    let decoded_before = parsed_before
        .as_object()
        .expect("the fixture is an object")
        .keys()
        .filter(|key| all_names.contains(&key.as_str()))
        .count();
    assert_eq!(
        raw_before,
        all_names.len(),
        "the unescaped fixture must carry every name exactly once"
    );
    assert_eq!(
        raw_before, decoded_before,
        "the raw and the decoded methods must agree on this encoding: the names are real \
         object keys, so both views see the same occurrences.  They agree here and would \
         disagree on the escaped encoding, which is why that case has its own test"
    );

    let sealed = SealedAreas::new([root.clone()]);
    let report = redact_tree_traced(&root, &[], &sealed).expect("the tree redaction runs");
    let sidecar = root.join("developer.attempt1.redacted.json");
    assert!(
        sidecar.is_file(),
        "the sealed trajectory must get a generated sidecar: {report:?}"
    );
    let redacted = std::fs::read_to_string(&sidecar).expect("the sidecar");

    assert_eq!(
        std::fs::read_to_string(&trajectory).expect("the original"),
        original,
        "a sealed file must never be rewritten"
    );
    assert!(
        serde_json::from_str::<serde_json::Value>(&redacted).is_ok(),
        "the JSON-key splice must leave the document parseable"
    );

    // Every non-empty value is gone; the keys themselves stay.
    for name in &all_names {
        assert_eq!(
            unescaped_key_occurrences(&redacted, name),
            1,
            "`{name}` must still be a key exactly once (the key is not the span)"
        );
        if name.starts_with("HOH_MODEL")
            || name.starts_with("OPENAI")
            || name.starts_with("LITELLM")
            || name.starts_with("MSWEA")
        {
            assert!(
                redacted.contains(&format!("\"{name}\": \"\"")),
                "an empty credential value must be left alone: `{name}`"
            );
        } else {
            assert!(
                redacted.contains(&format!("\"{name}\": \"<redacted>\"")),
                "`{name}` must be redacted behind its key"
            );
            assert!(
                !redacted.contains(&format!("\"{name}\": \"F:")),
                "`{name}` must not keep a raw path value"
            );
        }
    }
}
