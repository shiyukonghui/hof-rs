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
        None,
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
    submit_in(args, cwd, artifact_dir, None)
}

/// DR-34: the same, with `HOH_VIEW_DIR` set as the third resolution base.
fn submit_in(
    args: &[&str],
    cwd: &Path,
    artifact_dir: &Path,
    view_dir: Option<&Path>,
) -> std::process::Output {
    let mut command = Command::new(binary());
    command
        .args(args)
        .env("HOH_ARTIFACT_DIR", artifact_dir)
        .current_dir(cwd);
    match view_dir {
        Some(view) => {
            command.env("HOH_VIEW_DIR", view);
        }
        None => {
            command.env_remove("HOH_VIEW_DIR");
        }
    }
    command.output().expect("the hoh binary must be runnable")
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

/// DR-34 ①: the Developer habitually writes `.hoh/args/x.json` relative to the
/// **project root**; `submit --file .hoh/plan.md` from that same cwd must now
/// find the artefact instead of looking at `<view>/.hoh/.hoh/plan.md`.
#[test]
fn a_developer_style_relative_submit_finds_the_artifact() {
    let temp = tempfile::tempdir().unwrap();
    let view = temp.path().join("view");
    let artifact_dir = view.join(".hoh");
    std::fs::create_dir_all(&artifact_dir).unwrap();
    std::fs::write(artifact_dir.join("plan.md"), plan_fixture()).unwrap();

    let output = submit(
        &["submit", "--role", "planner", "--file", ".hoh/plan.md"],
        &view, // cwd == the project root, exactly like the Developer role
        &artifact_dir,
    );
    assert_eq!(
        output.status.code(),
        Some(0),
        "stdout: {}\nstderr: {}",
        String::from_utf8_lossy(&output.stdout),
        String::from_utf8_lossy(&output.stderr)
    );
}

/// DR-34 ②③: the view directory is the last base, and when nothing exists the
/// refusal lists every candidate absolute path.
#[test]
fn a_relative_submit_falls_back_to_the_view_dir_then_reports_all_candidates() {
    let temp = tempfile::tempdir().unwrap();
    let view = temp.path().join("view");
    let artifact_dir = view.join(".hoh");
    std::fs::create_dir_all(&artifact_dir).unwrap();
    std::fs::write(artifact_dir.join("plan.md"), plan_fixture()).unwrap();

    // cwd is `temp` (nothing there), the artifact dir has no `.hoh/plan.md`, and
    // only the view dir resolves the argument.
    let output = submit_in(
        &["submit", "--role", "planner", "--file", ".hoh/plan.md"],
        temp.path(),
        &artifact_dir,
        Some(&view),
    );
    assert_eq!(
        output.status.code(),
        Some(0),
        "stdout: {}\nstderr: {}",
        String::from_utf8_lossy(&output.stdout),
        String::from_utf8_lossy(&output.stderr)
    );

    let output = submit_in(
        &["submit", "--role", "planner", "--file", "nowhere/plan.md"],
        temp.path(),
        &artifact_dir,
        Some(&view),
    );
    assert_eq!(output.status.code(), Some(2));
    let stdout = String::from_utf8_lossy(&output.stdout).to_string();
    let payload: Value = serde_json::from_str(&stdout).expect("a structured refusal");
    assert_eq!(payload["error"], serde_json::json!("source_not_found"));
    let listed: Vec<String> = payload["candidates"]
        .as_array()
        .expect("the candidate list")
        .iter()
        .map(|entry| entry.as_str().unwrap().to_string())
        .collect();
    for candidate in [
        temp.path().join("nowhere/plan.md"),
        artifact_dir.join("nowhere/plan.md"),
        view.join("nowhere/plan.md"),
    ] {
        assert!(
            listed.contains(&candidate.to_string_lossy().to_string()),
            "the refusal must list `{}`: {listed:?}",
            candidate.display()
        );
    }
    assert!(
        payload["os_error"]
            .as_str()
            .unwrap_or("")
            .contains("os error"),
        "the operating system's reason must survive: {payload}"
    );
    assert!(
        !artifact_dir.join("plan.md").join("plan.md").exists(),
        "nothing may be written for a missing source"
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
// ③b DR-34: the resolution is "first existing" across three bases
// ---------------------------------------------------------------------------

/// DR-34: a relative source is resolved against the **first existing** of
/// ① the current directory, ② `HOH_ARTIFACT_DIR`, ③ `HOH_VIEW_DIR`.
///
/// `smoke-t3` still produced four `os error 3`: DR-25 made the artifact dir the
/// only base, but the Developer's cwd is the project root and it naturally wrote
/// `.hoh/args/x.json` (project-root relative) — which DR-25 then looked for at
/// `<workspace>/.hoh/.hoh/args/x.json`.
#[test]
fn a_relative_source_resolves_to_the_first_existing_base() {
    let temp = tempfile::tempdir().unwrap();
    let root = temp.path();
    let cwd = root.join("project");
    let view = root.join("view");
    let artifact = view.join(".hoh");
    std::fs::create_dir_all(&cwd).unwrap();
    std::fs::create_dir_all(&artifact).unwrap();

    let bases = bridge::source_bases(Some(&artifact), Some(&view), &cwd);
    assert_eq!(
        bases,
        vec![cwd.clone(), artifact.clone(), view.clone()],
        "the documented order is cwd → HOH_ARTIFACT_DIR → HOH_VIEW_DIR"
    );

    // ① the cwd (Developer's reading of `.hoh/args/x.json`)
    write(&cwd.join(".hoh/args/x.json"), r#"{"from":"cwd"}"#);
    let resolved = bridge::resolve_source(Path::new(".hoh/args/x.json"), &bases);
    assert!(resolved.existed);
    assert_eq!(resolved.path, cwd.join(".hoh/args/x.json"));

    // ② the artifact dir (this is where the artefact actually lives)
    write(&artifact.join("args/x.json"), r#"{"from":"artifact"}"#);
    let resolved = bridge::resolve_source(Path::new("args/x.json"), &bases);
    assert_eq!(resolved.path, artifact.join("args/x.json"));

    // ③ the view dir (a role that thinks `.hoh` is implicit)
    write(&view.join("plan.md"), "view plan\n");
    let resolved = bridge::resolve_source(Path::new("plan.md"), &bases);
    assert_eq!(resolved.path, view.join("plan.md"));

    // ④ the artifact-dir candidate must still win when the cwd has no such file
    assert_eq!(
        bridge::resolve_args_file_with_view(Path::new("args/x.json"), Some(&artifact), Some(&view)),
        artifact.join("args/x.json")
    );
}

/// DR-34: when none of the candidates exists, the error names **all** of them
/// and keeps the operating system's own message.
#[test]
fn a_missing_relative_source_lists_every_candidate() {
    let temp = tempfile::tempdir().unwrap();
    let root = temp.path();
    let cwd = root.join("project");
    let view = root.join("view");
    let artifact = view.join(".hoh");
    std::fs::create_dir_all(&cwd).unwrap();
    std::fs::create_dir_all(&artifact).unwrap();

    let error = bridge::parse_args_with_bases(
        None,
        Some(Path::new("args/missing.json")),
        Some(&artifact),
        Some(&view),
        &cwd,
    )
    .expect_err("no candidate exists");
    let text = error.to_string();
    for candidate in [
        cwd.join("args/missing.json"),
        artifact.join("args/missing.json"),
        view.join("args/missing.json"),
    ] {
        assert!(
            text.contains(&candidate.to_string_lossy().to_string()),
            "the error must list `{}`: {text}",
            candidate.display()
        );
    }
    assert!(
        text.contains("os error") || text.contains("The system cannot find"),
        "the operating system's own reason must survive: {text}"
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
        resume: false,
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

/// DR-79 ①: a **root-level temporary** the Developer left behind is the one
/// bounded exception to "the runtime only reports".  The round removes the
/// temporaries it watched appear, records the removal in `warnings.log`, and
/// still lists the write in `out_of_tree_writes` — so the record keeps the
/// fact and the repository root stops accumulating litter.  `smoke-t13` left
/// `.tmp_coin.json` / `.tmp_goal.json` / `.tmp_hud.json` (108/68/46 B) in
/// `F:\moonbit-hof-rs` with nothing to clean them.
#[tokio::test]
async fn a_round_removes_its_own_root_temporary_and_records_it() {
    let temp = tempfile::tempdir().unwrap();
    let root = temp.path();
    let mut cfg = test_config(root, 1);
    cfg.runtime.spec = root.join("spec.md");
    cfg.runtime.out_of_tree_root = Some(root.to_path_buf());
    let spec = write_spec(root);
    let stray = root.join(".tmp_probe.json");
    let script = vec![
        FakeStep::new(Role::Planner).writing(".hoh/plan.md", OK_PLAN),
        FakeStep::new(Role::Developer)
            .writing("project.godot", "config_version=5\n")
            .outside(stray.clone(), "{}\n"),
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
        resume: false,
    };
    hof_rs::runtime::run_loop::run(&orchestrator, &spec, "run-1")
        .await
        .expect("the stray write is a report, not a failure");

    assert!(
        !stray.exists(),
        "the round's own root temporary must be cleaned at close: {}",
        stray.display()
    );
    let result: Value =
        serde_json::from_str(&read(&root.join("runs/run-1/iter-1/result.json"))).unwrap();
    let writes = result["out_of_tree_writes"].as_array().expect("list");
    assert!(
        writes.iter().any(|path| path == ".tmp_probe.json"),
        "the removal must not erase the write from the record: {writes:?}"
    );
    let warnings = read(&root.join("runs/run-1/warnings.log"));
    assert!(
        warnings.contains("out_of_tree_cleanup"),
        "the cleanup must leave a trace in the record: {warnings}"
    );
    assert!(
        warnings.contains(".tmp_probe.json"),
        "the trace must name what was removed: {warnings}"
    );
}
