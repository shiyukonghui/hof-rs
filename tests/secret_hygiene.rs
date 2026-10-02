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
