//! DR-8 / FIX-10 — CLI exits and display discipline for `status` and
//! `rollback`.  Everything runs offline against a `tempfile` runs directory;
//! no MCP endpoint and no LM Studio are touched.

use std::path::{Path, PathBuf};
use std::process::{Command, Output};

fn binary() -> PathBuf {
    PathBuf::from(env!("CARGO_BIN_EXE_hoh"))
}

fn manifest() -> PathBuf {
    PathBuf::from(env!("CARGO_MANIFEST_DIR"))
}

fn hoh(args: &[&str], cwd: &Path) -> Output {
    Command::new(binary())
        .args(args)
        .current_dir(cwd)
        .output()
        .expect("the hoh binary must be runnable")
}

fn write(path: &Path, content: &str) {
    if let Some(parent) = path.parent() {
        std::fs::create_dir_all(parent).unwrap();
    }
    std::fs::write(path, content).unwrap();
}

/// One complete run with a known-token iteration and an unknown-token iteration.
fn fixture_runs_dir(root: &Path) -> PathBuf {
    let runs = root.join("runs");
    let iter_one = runs.join("demo-run/iter-1");
    write(
        &iter_one.join("result.json"),
        r#"{"ok":true,"failed_role":null,"reason":"ok","issues":[],"warnings":[],
            "candidate_id":"cand-abc","version_id":"cand-abc","usage":[],"durations_ms":[],
            "artifact_gate":{"applicable":true,"launchable":true,"reasons":[]},
            "prd_coverage":{"verified":0,"gap":17,"verified_ids":[],"gap_ids":["F1"]}}"#,
    );
    write(
        &iter_one.join("usage.json"),
        r#"[
            {"role":"planner","iteration":1,"calls":1,"prompt_tokens":100,
             "completion_tokens":20,"total_tokens":120,
             "cache_hit_tokens":0,"cache_miss_tokens":0,"usage_known":true},
            {"role":"developer","iteration":1,"calls":1,"prompt_tokens":null,
             "completion_tokens":null,"total_tokens":null,
             "cache_hit_tokens":null,"cache_miss_tokens":null,"usage_known":false}
        ]"#,
    );
    runs
}

#[test]
fn status_reports_the_iteration_and_marks_unknown_usage() {
    let temp = tempfile::tempdir().unwrap();
    let runs = fixture_runs_dir(temp.path());

    let output = hoh(
        &[
            "status",
            "--runs-dir",
            runs.to_str().unwrap(),
            "--run-id",
            "demo-run",
        ],
        &manifest(),
    );
    assert_eq!(
        output.status.code(),
        Some(0),
        "stderr: {}",
        String::from_utf8_lossy(&output.stderr)
    );
    let stdout = String::from_utf8_lossy(&output.stdout);
    assert!(stdout.contains("# run demo-run"), "stdout: {stdout}");
    assert!(stdout.contains("iter-1"), "stdout: {stdout}");
    assert!(stdout.contains("cand-abc"), "stdout: {stdout}");
    // DR-39: three columns per iteration — the loop completed, the artifact is
    // usable, and how much of the PRD was actually verified.
    assert!(
        stdout.contains("harness=") && stdout.contains("gate=") && stdout.contains("prd=0/17"),
        "the per-iteration line must carry harness=/gate=/prd=: {stdout}"
    );
    // DR-8: a missing usage value must never be summed as zero.
    assert!(
        stdout.contains("total tokens: 120 (1 iteration unknown)"),
        "stdout: {stdout}"
    );
}

#[test]
fn status_without_any_known_usage_says_unknown() {
    let temp = tempfile::tempdir().unwrap();
    let runs = temp.path().join("runs");
    write(
        &runs.join("demo-run/iter-1/result.json"),
        r#"{"ok":true,"reason":"ok","issues":[],"warnings":[],"usage":[],"durations_ms":[]}"#,
    );
    write(
        &runs.join("demo-run/iter-1/usage.json"),
        r#"[{"role":"planner","iteration":1,"calls":1,"usage_known":false}]"#,
    );

    let output = hoh(
        &[
            "status",
            "--runs-dir",
            runs.to_str().unwrap(),
            "--run-id",
            "demo-run",
        ],
        &manifest(),
    );
    let stdout = String::from_utf8_lossy(&output.stdout);
    assert_eq!(output.status.code(), Some(0), "stdout: {stdout}");
    assert!(
        stdout.contains("total tokens: unknown (1 iteration unknown)"),
        "stdout: {stdout}"
    );
}

#[test]
fn status_with_a_missing_runs_dir_exits_two() {
    let temp = tempfile::tempdir().unwrap();
    let missing = temp.path().join("no-such-runs");

    let output = hoh(
        &["status", "--runs-dir", missing.to_str().unwrap()],
        &manifest(),
    );
    assert_eq!(
        output.status.code(),
        Some(2),
        "a missing runs directory is a usage error (exit 2), not a harness error"
    );
    let stderr = String::from_utf8_lossy(&output.stderr);
    assert!(stderr.contains("hoh:"), "stderr: {stderr}");
}

#[test]
fn status_with_an_unknown_run_id_exits_two() {
    let temp = tempfile::tempdir().unwrap();
    let runs = temp.path().join("runs");
    std::fs::create_dir_all(&runs).unwrap();

    // Empty runs directory and no --run-id: there is nothing to report.
    let output = hoh(
        &["status", "--runs-dir", runs.to_str().unwrap()],
        &manifest(),
    );
    assert_eq!(output.status.code(), Some(2));

    // An explicit, non-existent run id is a usage error as well.
    let output = hoh(
        &[
            "status",
            "--runs-dir",
            runs.to_str().unwrap(),
            "--run-id",
            "ghost",
        ],
        &manifest(),
    );
    assert_eq!(output.status.code(), Some(2));
}

#[test]
fn rollback_with_a_missing_version_exits_two() {
    let temp = tempfile::tempdir().unwrap();
    let runs = temp.path().join("runs");
    write(
        &runs.join("demo-run/versions/index.json"),
        r#"{"schema":1,"versions":[]}"#,
    );
    let workspace = temp.path().join("workspace");
    std::fs::create_dir_all(&workspace).unwrap();

    let output = hoh(
        &[
            "rollback",
            "--runs-dir",
            runs.to_str().unwrap(),
            "--run-id",
            "demo-run",
            "--to",
            "deadbeef",
            "--project",
            workspace.to_str().unwrap(),
        ],
        &manifest(),
    );
    assert_eq!(
        output.status.code(),
        Some(2),
        "a missing version must be a typed usage error (exit 2), stderr: {}",
        String::from_utf8_lossy(&output.stderr)
    );
}
