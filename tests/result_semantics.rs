//! DR-27 — "the loop completed" must never be confused with "the artifact is
//! usable".
//!
//! `smoke-t2` ended with `result.json.ok = true` while `A_1` could not start and
//! 6/7 battery steps had failed.  The exit code, the `status` table and
//! `exit_code` file all have to tell the two apart.

mod common;

use std::path::{Path, PathBuf};
use std::process::Command;
use std::sync::{Arc, Mutex};

use common::*;
use hof_rs::adapter::godot::{BatteryLimits, GodotAdapter};
use hof_rs::config::{GodotConfig, HohConfig};
use hof_rs::model::{Ablation, ArtifactGate, Role, Usage};
use hof_rs::runtime::run_loop::RunSummary;
use hof_rs::tools::mcp::McpError;
use hof_rs::tools::{ToolChannel, ToolResult};
use serde_json::{json, Value};

fn binary() -> PathBuf {
    PathBuf::from(env!("CARGO_BIN_EXE_hoh"))
}

fn manifest() -> PathBuf {
    PathBuf::from(env!("CARGO_MANIFEST_DIR"))
}

fn summary_with(gate: ArtifactGate) -> RunSummary {
    RunSummary {
        run_id: "run-1".to_string(),
        iterations_completed: 1,
        final_version_id: Some("cand".to_string()),
        total_usage: Usage::default(),
        ok: true,
        artifact_gate: gate,
        // DR-39: the summary carries a third axis; it never affects the exit code.
        prd_coverage: hof_rs::model::PrdCoverage::default(),
        // DR-67: this fixture describes a *successful* round, so there is no
        // failure code to carry; the exit code comes from the artifact gate
        // alone (DR-27).  The failure code is exercised in `e1_increment.rs`
        // against a real error.
        failure_exit_code: None,
    }
}

fn closed_gate() -> ArtifactGate {
    ArtifactGate {
        applicable: true,
        launchable: false,
        reasons: vec!["editor_errors_baseline: Invalid scene".to_string()],
    }
}

fn open_gate() -> ArtifactGate {
    ArtifactGate {
        applicable: true,
        launchable: true,
        reasons: Vec::new(),
    }
}

// ---------------------------------------------------------------------------
// ①/③ exit code and the `exit_code` file
// ---------------------------------------------------------------------------

#[test]
fn a_closed_gate_exits_six_and_writes_the_code() {
    let temp = tempfile::tempdir().unwrap();
    let run_dir = temp.path().join("runs/run-1");
    std::fs::create_dir_all(&run_dir).unwrap();

    let code = hof_rs::cli_impl::finalize_run(&run_dir, &summary_with(closed_gate())).unwrap();
    assert_eq!(
        code, 6,
        "a completed loop over an unlaunchable artifact must exit 6 (DR-27)"
    );
    let written = std::fs::read_to_string(run_dir.join("exit_code")).expect("exit_code file");
    assert_eq!(written, "6\n", "the file is a bare number plus a newline");
    assert!(run_dir.join("exit_code").is_file());
}

#[test]
fn an_open_gate_exits_zero_and_writes_the_code() {
    let temp = tempfile::tempdir().unwrap();
    let run_dir = temp.path().join("runs/run-1");
    std::fs::create_dir_all(&run_dir).unwrap();

    let code = hof_rs::cli_impl::finalize_run(&run_dir, &summary_with(open_gate())).unwrap();
    assert_eq!(code, 0);
    assert_eq!(
        std::fs::read_to_string(run_dir.join("exit_code")).unwrap(),
        "0\n"
    );
}

#[test]
fn a_gate_that_did_not_apply_never_exits_six() {
    let gate = ArtifactGate::not_applicable("no gate for the test adapter");
    assert_eq!(hof_rs::cli_impl::run_exit_code(&gate), 0);
    assert_eq!(hof_rs::cli_impl::run_exit_code(&closed_gate()), 6);
    assert_eq!(hof_rs::cli_impl::run_exit_code(&open_gate()), 0);
}

// ---------------------------------------------------------------------------
// ①b DR-68 ⑦ — a gate that did not apply is not an open gate
// ---------------------------------------------------------------------------

/// `smoke-t8`'s **failed** round persisted
/// `artifact_gate = {"applicable": false, "launchable": true}` — the shape
/// `ArtifactGate::not_applicable` builds — and `ArtifactGate::is_open()` looked
/// only at `launchable`, so a failure read as a pass.  "Not applicable" is not
/// "open": nothing was checked, so nothing may be reported as passable.
#[test]
fn a_gate_that_did_not_apply_is_not_open() {
    let gate = ArtifactGate::not_applicable("the round failed; no artifact gate was produced");
    assert!(!gate.applicable, "the honest not-applicable answer");
    assert!(
        !gate.launchable,
        "DR-68 ⑦: a gate that did not apply must not report launchable=true"
    );
    assert!(
        !gate.is_open(),
        "DR-68 ⑦: is_open() must consider `applicable`, not only `launchable`"
    );

    // The raw field combination is the one a future reader can still meet; it
    // must not read as open either.
    let forged = ArtifactGate {
        applicable: false,
        launchable: true,
        reasons: Vec::new(),
    };
    assert!(
        !forged.is_open(),
        "applicability decides, even when launchable=true"
    );

    // The control: an applicable, launchable gate is still open, so the fix
    // cannot be read as "every gate is closed now".
    assert!(open_gate().is_open());
    assert!(!closed_gate().is_open());
}

/// The `status` column is the other reader of the same field.  A result that
/// says "no gate was evaluated" must not print `gate=ok`; it is neither a pass
/// nor a fail.
#[test]
fn status_does_not_report_an_unevaluated_gate_as_ok() {
    let temp = tempfile::tempdir().unwrap();
    let runs = temp.path().join("runs");
    let iter = runs.join("demo-run/iter-1");
    std::fs::create_dir_all(&iter).unwrap();
    std::fs::write(
        iter.join("result.json"),
        r#"{"ok":false,"failed_role":"tester","reason":"schema_failure","issues":[],"warnings":[],
            "candidate_id":null,"version_id":null,"usage":[],"durations_ms":[],
            "artifact_gate":{"applicable":false,"launchable":true,
                             "reasons":["the round failed; no artifact gate was produced"]}}"#,
    )
    .unwrap();

    let output = Command::new(binary())
        .args([
            "status",
            "--runs-dir",
            runs.to_str().unwrap(),
            "--run-id",
            "demo-run",
        ])
        .current_dir(manifest())
        .output()
        .unwrap();
    let stdout = String::from_utf8_lossy(&output.stdout);
    assert!(
        stdout.contains("gate=unknown"),
        "an unevaluated gate is unknown, not ok: {stdout}"
    );
    assert!(
        !stdout.contains("gate=ok"),
        "DR-68 ⑦: a non-applicable gate must never be printed as ok: {stdout}"
    );
}

#[test]
fn finalize_run_records_the_code_in_meta_json() {
    let temp = tempfile::tempdir().unwrap();
    let run_dir = temp.path().join("runs/run-1");
    std::fs::create_dir_all(&run_dir).unwrap();
    std::fs::write(run_dir.join("meta.json"), r#"{"run_id":"run-1"}"#).unwrap();

    hof_rs::cli_impl::finalize_run(&run_dir, &summary_with(closed_gate())).unwrap();
    let meta: Value =
        serde_json::from_str(&std::fs::read_to_string(run_dir.join("meta.json")).unwrap()).unwrap();
    assert_eq!(meta["exit_code"], json!(6));
    assert_eq!(meta["run_id"], json!("run-1"));
}

// ---------------------------------------------------------------------------
// ② a real round over a dead project reports gate=false
// ---------------------------------------------------------------------------

/// A channel where every MCP call fails: the battery can neither open the
/// scene nor read it, so the gate is closed and the second pass is identical.
struct DeadChannel {
    calls: Mutex<Vec<String>>,
}

#[async_trait::async_trait]
impl ToolChannel for DeadChannel {
    fn allowed(&self, _role: Role, _tool: &str) -> bool {
        true
    }

    fn index_markdown(&self, _role: Role) -> String {
        "# tools\n".to_string()
    }

    async fn call(&self, _role: Role, tool: &str, _args: Value) -> anyhow::Result<ToolResult> {
        self.calls.lock().unwrap().push(tool.to_string());
        Err(McpError::new(-32603, "Failed loading scene").into())
    }
}

#[tokio::test]
async fn a_round_over_a_dead_project_reports_a_closed_gate() {
    let temp = tempfile::tempdir().unwrap();
    let root = temp.path();
    let mut cfg: HohConfig = test_config(root, 1);
    cfg.runtime.spec = root.join("spec.md");
    let spec = write_spec(root);
    let script = vec![
        FakeStep::new(Role::Planner).writing(".hoh/plan.md", OK_PLAN),
        FakeStep::new(Role::Developer).writing("project.godot", "config_version=5\n"),
        // The one DR-24 repair attempt (the gate stays closed afterwards).
        FakeStep::new(Role::Developer),
        FakeStep::new(Role::Tester)
            .writing(".hoh/evidence/move.json", "{}\n")
            .writing(".hoh/evidence.json", &ok_evidence(1, "")),
    ];
    let adapter = GodotAdapter::new(
        GodotConfig {
            editor_binary: std::path::PathBuf::new(),
            cache_excludes: vec![".godot".to_string()],
            main_scene: "res://scenes/main.tscn".to_string(),
        },
        true,
    )
    .with_battery_limits(BatteryLimits {
        ready_timeout_seconds: 0,
        max_retries: 0,
        timeout_seconds: 5,
    });
    let channel = Arc::new(DeadChannel {
        calls: Mutex::new(Vec::new()),
    });
    let orchestrator = hof_rs::runtime::run_loop::Orchestrator {
        harness: Box::new(FakeHarness::new(script)),
        adapter: Box::new(adapter),
        tools: channel,
        cfg,
        ablation: Ablation::default(),
        force_init: true,
        start_state: hof_rs::runtime::start_state::StartState::as_is(),
    };
    let summary = hof_rs::runtime::run_loop::run(&orchestrator, &spec, "run-1")
        .await
        .expect("DR-24 keeps the loop alive");

    // `ok` stays what it always meant: the loop and the schema succeeded.
    assert!(summary.ok, "the loop itself completed");
    assert!(summary.artifact_gate.applicable);
    assert!(!summary.artifact_gate.launchable);
    assert_eq!(hof_rs::cli_impl::run_exit_code(&summary.artifact_gate), 6);

    let result: Value =
        serde_json::from_str(&read(&root.join("runs/run-1/iter-1/result.json"))).unwrap();
    assert_eq!(result["ok"], json!(true));
    assert_eq!(result["artifact_gate"]["launchable"], json!(false));
    assert!(result["artifact_gate"]["reasons"].as_array().unwrap().len() >= 2);
}

// ---------------------------------------------------------------------------
// ④ `status` shows both columns
// ---------------------------------------------------------------------------

#[test]
fn status_shows_the_harness_and_gate_columns() {
    let temp = tempfile::tempdir().unwrap();
    let runs = temp.path().join("runs");
    let iter = runs.join("demo-run/iter-1");
    std::fs::create_dir_all(&iter).unwrap();
    std::fs::write(
        iter.join("result.json"),
        r#"{"ok":true,"failed_role":null,"reason":"ok","issues":[],"warnings":[],
            "candidate_id":"cand-abc","version_id":"cand-abc","usage":[],"durations_ms":[],
            "artifact_gate":{"applicable":true,"launchable":false,"reasons":["A1 is not launchable"]}}"#,
    )
    .unwrap();
    std::fs::write(
        iter.join("usage.json"),
        r#"[{"role":"planner","iteration":1,"calls":1,"total_tokens":7,"usage_known":true}]"#,
    )
    .unwrap();

    let output = Command::new(binary())
        .args([
            "status",
            "--runs-dir",
            runs.to_str().unwrap(),
            "--run-id",
            "demo-run",
        ])
        .current_dir(manifest())
        .output()
        .unwrap();
    assert_eq!(
        output.status.code(),
        Some(0),
        "stderr: {}",
        String::from_utf8_lossy(&output.stderr)
    );
    let stdout = String::from_utf8_lossy(&output.stdout);
    assert!(stdout.contains("harness=ok"), "stdout: {stdout}");
    assert!(stdout.contains("gate=fail"), "stdout: {stdout}");

    // A run whose result predates the gate must not be reported as passing it.
    let iter = runs.join("demo-run/iter-2");
    std::fs::create_dir_all(&iter).unwrap();
    std::fs::write(
        iter.join("result.json"),
        r#"{"ok":true,"reason":"ok","issues":[],"warnings":[],"usage":[],"durations_ms":[]}"#,
    )
    .unwrap();
    let output = Command::new(binary())
        .args([
            "status",
            "--runs-dir",
            runs.to_str().unwrap(),
            "--run-id",
            "demo-run",
        ])
        .current_dir(manifest())
        .output()
        .unwrap();
    let stdout = String::from_utf8_lossy(&output.stdout);
    assert!(stdout.contains("gate=unknown"), "stdout: {stdout}");
}

#[test]
fn the_exit_code_helper_matches_the_documented_table() {
    // 0 success / 2 usage / 3 schema / 4 dependency / 5 harness / 6 gate.
    for (gate, expected) in [
        (open_gate(), 0),
        (closed_gate(), 6),
        (ArtifactGate::not_applicable("n/a"), 0),
    ] {
        assert_eq!(hof_rs::cli_impl::run_exit_code(&gate), expected);
    }
    let _ = Path::new(".");
}
