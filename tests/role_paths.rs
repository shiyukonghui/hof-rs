//! DR-25 — absolute role environments, canonical submissions and out-of-tree
//! write detection.
//!
//! `smoke-t2` passed `HOH_ARTIFACT_DIR` as a **relative** path while the role
//! shell's cwd was already the view root, so `hoh submit` wrote the plan to
//! `runs/<id>/iter-1/planner-view/runs/<id>/iter-1/planner-view/.hoh/plan.md`.
//! Tester also failed twice on a relative `--args-file` (`os error 3`).

mod common;

use std::path::{Path, PathBuf};
use std::process::Command;
use std::sync::Arc;

use common::*;
use hof_rs::model::{Ablation, Role};
use hof_rs::tools::bridge;
use serde_json::Value;

fn binary() -> PathBuf {
    PathBuf::from(env!("CARGO_BIN_EXE_hoh"))
}

fn manifest() -> PathBuf {
    PathBuf::from(env!("CARGO_MANIFEST_DIR"))
}

// ---------------------------------------------------------------------------
// ① every path-shaped env var is absolute
// ---------------------------------------------------------------------------

const PATH_VARS: &[&str] = &[
    "HOH_ARTIFACT_DIR",
    "HOH_HOH_BIN",
    "HOH_RUN_DIR",
    "HOH_WORKSPACE",
    "HOH_VIEW_DIR",
    "HOH_SCRATCH_DIR",
];

#[tokio::test]
async fn every_path_env_var_handed_to_a_role_is_absolute() {
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

    for record in &records {
        for name in PATH_VARS {
            let value = record
                .env
                .get(*name)
                .unwrap_or_else(|| panic!("{name} is missing from {:?}", record.role));
            assert!(
                Path::new(value).is_absolute(),
                "{name} must be absolute for {:?}, got `{value}`",
                record.role
            );
        }
        let artifact = record.env.get("HOH_ARTIFACT_DIR").unwrap();
        let scratch = record.env.get("HOH_SCRATCH_DIR").unwrap();
        let view = record.env.get("HOH_VIEW_DIR").unwrap();
        assert!(
            scratch.starts_with(artifact),
            "HOH_SCRATCH_DIR must live under HOH_ARTIFACT_DIR: {scratch} vs {artifact}"
        );
        assert!(
            scratch.contains(".hoh"),
            "the scratch directory must be hash-excluded (inside .hoh): {scratch}"
        );
        assert_eq!(Path::new(view).join(".hoh").to_string_lossy(), *artifact);
        assert!(
            Path::new(scratch).is_dir(),
            "the scratch directory must be created before the role runs: {scratch}"
        );
    }
}

#[test]
fn role_env_absolutizes_a_relative_view() {
    let cfg = hof_rs::config::load_config(&[]).unwrap();
    let env = hof_rs::runtime::invoke::role_env(
        &cfg,
        "run-relative",
        Role::Tester,
        1,
        Path::new("relative/view"),
    );
    for name in PATH_VARS {
        let value = env.get(*name).unwrap();
        assert!(
            Path::new(value).is_absolute(),
            "{name} must be absolute, got `{value}`"
        );
    }
}

// ---------------------------------------------------------------------------
// ② `hoh submit` only ever lands on the canonical artifact path
// ---------------------------------------------------------------------------

fn plan_fixture() -> String {
    std::fs::read_to_string(manifest().join("tests/fixtures/plan_ok.md")).expect("plan fixture")
}

fn submit(args: &[&str], cwd: &Path, artifact_dir: &Path) -> std::process::Output {
    Command::new(binary())
        .args(args)
        .env("HOH_ARTIFACT_DIR", artifact_dir)
        .current_dir(cwd)
        .output()
        .expect("the hoh binary must be runnable")
}

#[test]
fn a_relative_submit_lands_on_the_canonical_path_from_any_cwd() {
    let temp = tempfile::tempdir().unwrap();
    let artifact_dir = temp.path().join("view/.hoh");
    std::fs::create_dir_all(&artifact_dir).unwrap();
    std::fs::write(artifact_dir.join("plan.md"), plan_fixture()).unwrap();

    let output = submit(
        &["submit", "--role", "planner", "--file", "plan.md"],
        temp.path(), // deliberately *not* the view root
        &artifact_dir,
    );
    assert_eq!(
        output.status.code(),
        Some(0),
        "stdout: {}\nstderr: {}",
        String::from_utf8_lossy(&output.stdout),
        String::from_utf8_lossy(&output.stderr)
    );
    assert!(artifact_dir.join("plan.md").is_file());
    assert!(
        String::from_utf8_lossy(&output.stdout).contains("plan.md"),
        "the written path must be reported"
    );
}

#[test]
fn a_relative_submission_to_another_name_is_refused() {
    let temp = tempfile::tempdir().unwrap();
    let artifact_dir = temp.path().join("view/.hoh");
    std::fs::create_dir_all(&artifact_dir).unwrap();
    std::fs::write(artifact_dir.join("other.md"), plan_fixture()).unwrap();

    let output = submit(
        &["submit", "--role", "planner", "--file", "other.md"],
        temp.path(),
        &artifact_dir,
    );
    assert_eq!(
        output.status.code(),
        Some(2),
        "a submission that would not land on the canonical path must exit 2: {}",
        String::from_utf8_lossy(&output.stdout)
    );
    let stdout = String::from_utf8_lossy(&output.stdout);
    let payload: Value = serde_json::from_str(&stdout).expect("structured refusal");
    assert_eq!(
        payload["error"],
        serde_json::json!("artifact_path_violation")
    );
    assert!(
        payload["expected"]
            .as_str()
            .unwrap_or("")
            .ends_with("plan.md"),
        "expected path must be reported: {payload}"
    );
    assert!(
        payload["actual"]
            .as_str()
            .unwrap_or("")
            .ends_with("other.md"),
        "actual path must be reported: {payload}"
    );
    assert!(
        !artifact_dir.join("plan.md").exists(),
        "a refused submission must write nothing"
    );
}

#[test]
fn a_relative_artifact_dir_is_refused_instead_of_nesting() {
    let temp = tempfile::tempdir().unwrap();
    let cwd = temp.path().join("view");
    std::fs::create_dir_all(cwd.join(".hoh")).unwrap();
    std::fs::write(cwd.join(".hoh/plan.md"), plan_fixture()).unwrap();

    let output = submit(
        &["submit", "--role", "planner", "--file", "plan.md"],
        &cwd,
        Path::new(".hoh"), // the smoke-t2 shape: a relative artifact dir
    );
    assert_eq!(
        output.status.code(),
        Some(2),
        "a relative HOH_ARTIFACT_DIR is the exact bug DR-25 closes: {}",
        String::from_utf8_lossy(&output.stdout)
    );
    assert!(
        !cwd.join(".hoh/plan.md").join("plan.md").exists(),
        "no nested fake path may be created"
    );
}

// ---------------------------------------------------------------------------
// ③ `--args-file` is resolved against the artifact dir, not the shell cwd
// ---------------------------------------------------------------------------

#[test]
fn a_relative_args_file_is_resolved_against_the_artifact_dir() {
    let temp = tempfile::tempdir().unwrap();
    let artifact_dir = temp.path().join("view/.hoh");
    std::fs::create_dir_all(&artifact_dir).unwrap();
    std::fs::write(artifact_dir.join("args.json"), r#"{"node_path":"Player"}"#).unwrap();

    let resolved = bridge::resolve_args_file(Path::new("args.json"), Some(&artifact_dir));
    assert_eq!(resolved, artifact_dir.join("args.json"));
    let parsed = bridge::parse_args_in(Some("{}"), Some(&resolved), None).unwrap();
    assert_eq!(parsed["node_path"], serde_json::json!("Player"));

    // A relative path with no artifact dir keeps falling back to the cwd.
    let resolved = bridge::resolve_args_file(Path::new("args.json"), None);
    assert_eq!(resolved, std::env::current_dir().unwrap().join("args.json"));
    // An absolute path is never rewritten.
    let absolute = artifact_dir.join("args.json");
    assert_eq!(
        bridge::resolve_args_file(&absolute, Some(&artifact_dir)),
        absolute
    );
}

// ---------------------------------------------------------------------------
// ④ a write outside the project tree is reported
// ---------------------------------------------------------------------------

#[tokio::test]
async fn a_role_writing_outside_the_project_is_reported() {
    let temp = tempfile::tempdir().unwrap();
    let root = temp.path();
    // The "HoH working directory" the runtime scans: everything under it that
    // is not the project is out of bounds.
    let mut cfg = test_config(root, 1);
    cfg.runtime.spec = root.join("spec.md");
    cfg.runtime.out_of_tree_root = Some(root.to_path_buf());
    let spec = write_spec(root);
    let stray = root.join("stray_dir/probe.txt");
    let script = vec![
        FakeStep::new(Role::Planner).writing(".hoh/plan.md", OK_PLAN),
        FakeStep::new(Role::Developer)
            .writing("project.godot", "config_version=5\n")
            .outside(stray.clone(), "out of tree\n"),
        FakeStep::new(Role::Tester)
            .writing(".hoh/evidence/move.json", "{}\n")
            .writing(".hoh/evidence.json", &ok_evidence(1, "")),
    ];
    let harness = FakeHarness::new(script);
    let orchestrator = hof_rs::runtime::run_loop::Orchestrator {
        harness: Box::new(harness),
        adapter: Box::new(FakeAdapter::new()),
        tools: Arc::new(FakeToolChannel::new()),
        cfg,
        ablation: Ablation::default(),
        force_init: true,
        start_state: hof_rs::runtime::start_state::StartState::as_is(),
    };
    hof_rs::runtime::run_loop::run(&orchestrator, &spec, "run-1")
        .await
        .expect("the stray write is a report, not a failure");

    let result: Value =
        serde_json::from_str(&read(&root.join("runs/run-1/iter-1/result.json"))).unwrap();
    let writes = result["out_of_tree_writes"].as_array().expect("list");
    assert!(
        writes.iter().any(|path| path == "stray_dir/probe.txt"),
        "the out-of-tree write must be reported relative to the scanned root: {writes:?}"
    );
    // Report-only: the runtime never deletes anything.
    assert!(stray.is_file());
}
