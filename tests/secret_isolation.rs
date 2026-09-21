//! DR-19 — the model secret must not reach a role subprocess, and must not
//! survive anywhere under `runs/<id>/**`.
//!
//! Root cause (first real smoke run): mini's `LocalEnvironment` inherits the
//! parent environment, so a single `cmd /c set HOH` from a role echoed the
//! credential into its trajectory and into the model context.
//!
//! Every credential used here is a placeholder (`test-key-not-a-secret`).

mod common;

use std::sync::Mutex;

use common::*;
use hof_rs::model::{Ablation, Role};
use hof_rs::runtime::secrets::{blocked_env, SECRET_ENV_VARS};

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

/// DR-19 ①: every role environment blocks the inheritance explicitly.
#[tokio::test]
async fn every_role_environment_blocks_the_secret_variables() {
    let temp = tempfile::tempdir().unwrap();
    let root = temp.path();
    let (result, records) = run_scenario(
        root,
        1,
        happy_script(),
        Ablation::default(),
        FakeAdapter::new(),
    )
    .await;
    result.expect("the happy path must complete");
    assert_eq!(records.len(), 3);

    let blocked = blocked_env();
    assert_eq!(blocked.len(), 4, "all four known variables are overridden");
    for record in &records {
        for name in SECRET_ENV_VARS {
            assert_eq!(
                record.env.get(*name).map(String::as_str),
                Some(""),
                "role {:?} must set {name} to the empty string (DR-19)",
                record.role
            );
        }
    }
    // The explicit assignment must also happen for the role that is most
    // likely to be interrogated with `set`/`env`.
    let tester = records
        .iter()
        .find(|record| record.role == Role::Tester)
        .expect("tester runs");
    assert_eq!(tester.env.get("OPENAI_API_KEY").unwrap(), "");
    assert_eq!(tester.env.get("HOH_MODEL_API_KEY").unwrap(), "");
}

/// DR-19 ②: a secret written into a role view by a role/tool is erased from
/// the run directory and counted in `result.json`.
#[test]
fn a_leaked_secret_is_erased_and_counted() {
    let temp = tempfile::tempdir().unwrap();
    let root = temp.path().to_path_buf();

    // The role writes a file containing the (fake) credential, exactly as a
    // tool echoing its environment would.
    let script = vec![
        FakeStep::new(Role::Planner)
            .writing(".hoh/plan.md", OK_PLAN)
            .writing("env-dump.txt", &format!("HOH_MODEL_API_KEY={FAKE_KEY}\n")),
        FakeStep::new(Role::Developer).writing("project.godot", "config_version=5\n"),
        FakeStep::new(Role::Tester)
            .writing(".hoh/evidence/move.json", "{}\n")
            .writing(".hoh/evidence.json", &ok_evidence(1, "")),
    ];

    let (result, _records) = with_env(&[("HOH_MODEL_API_KEY", Some(FAKE_KEY))], || {
        tokio::runtime::Builder::new_current_thread()
            .enable_all()
            .build()
            .expect("runtime")
            .block_on(run_scenario(
                &root,
                1,
                script,
                Ablation::default(),
                FakeAdapter::new(),
            ))
    });
    result.expect("the happy path must complete");

    let run_dir = root.join("runs/run-1");
    let leak = std::fs::read_to_string(run_dir.join("iter-1/planner-view/env-dump.txt"))
        .expect("the leaked file still exists (erased, not deleted)");
    assert!(
        !leak.contains(FAKE_KEY),
        "the secret survived in the run directory: {leak}"
    );
    assert!(leak.contains("<redacted>"), "{leak}");

    let result_json: serde_json::Value =
        serde_json::from_str(&read(&run_dir.join("iter-1/result.json"))).unwrap();
    assert!(
        result_json["secret_redactions"].as_u64().unwrap_or(0) >= 1,
        "result.json must count the redaction: {result_json}"
    );
}

/// DR-19 ③: neither `meta.json` nor any trajectory may contain the literal.
#[test]
fn meta_and_trajectories_are_free_of_the_secret() {
    let temp = tempfile::tempdir().unwrap();
    let root = temp.path().to_path_buf();
    let (result, _) = with_env(&[("HOH_MODEL_API_KEY", Some(FAKE_KEY))], || {
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
    });
    result.expect("the happy path must complete");

    let run_dir = root.join("runs/run-1");
    let files = read_tree(&run_dir);
    assert!(files.iter().any(|(path, _)| path == "meta.json"));
    assert!(files
        .iter()
        .any(|(path, _)| path.starts_with("iter-1/traj/")));
    for (path, content) in &files {
        assert!(
            !content.contains(FAKE_KEY),
            "the secret leaked into runs/run-1/{path}"
        );
    }
}
