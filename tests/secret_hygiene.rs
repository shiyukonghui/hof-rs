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
