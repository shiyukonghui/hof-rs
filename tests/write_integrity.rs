//! DR-86 ①②④ — the delivery boundary, the retry diagnostics and the frozen view.
//!
//! Three independent defects of the `smoke-t16` round are pinned here, each one
//! by the property it must establish rather than by the file that happened to
//! break it:
//!
//! 1. a delivered text file that is a **fragment** (or carries a foreign shell
//!    escape) is named in the round's own warnings and closes the artifact gate
//!    with its own reason — it is never treated as a delivered artifact;
//! 2. a wrap-up retry that can still write is handed the **verbatim** defect list
//!    its previous attempt was rejected for, so "write the artifact NOW" is never
//!    the whole prompt again;
//! 3. a role that writes into the **frozen** candidate view no longer ends the
//!    round with a contract violation and no gate verdict: the frozen bytes are
//!    restored from the `A_t` snapshot, the stray bytes are preserved, and the
//!    round reaches its verdict.

mod common;

use common::*;
use hof_rs::errors::{as_hof_error, HofError};
use hof_rs::model::{Ablation, ContractViolation, Role};
use serde_json::Value;
use std::path::Path;

/// The 20-byte shape the round of record produced, used only as a *fixture of
/// the class*: a line tail that carries a closer nothing opened.  The production
/// check never looks for these bytes (see `runtime::integrity`).
const FRAGMENT_SCENE: &str = "visible = false)  \r\n";

/// A script whose `$` was consumed by another shell's escaping.
const ESCAPED_SCRIPT: &str = "@onready var coins: Label = \\$HUD/Coins\n";

fn read_json(path: &Path) -> Value {
    serde_json::from_str(&read(path)).expect("json")
}

fn result_json(root: &Path) -> Value {
    read_json(&root.join("runs/run-1/iter-1/result.json"))
}

fn gate_reasons(root: &Path) -> Vec<String> {
    result_json(root)["artifact_gate"]["reasons"]
        .as_array()
        .map(|reasons| {
            reasons
                .iter()
                .filter_map(Value::as_str)
                .map(ToOwned::to_owned)
                .collect()
        })
        .unwrap_or_default()
}

fn warnings(root: &Path) -> Vec<String> {
    result_json(root)["warnings"]
        .as_array()
        .map(|items| {
            items
                .iter()
                .filter_map(Value::as_str)
                .map(ToOwned::to_owned)
                .collect()
        })
        .unwrap_or_default()
}

fn warning_log(root: &Path) -> String {
    std::fs::read_to_string(root.join("runs/run-1/warnings.log")).unwrap_or_default()
}

/// One complete round whose Developer writes `scene` as the main scene and
/// `script` as its entry script.
fn developer_round(scene: &str, script: &str) -> Vec<FakeStep> {
    vec![
        FakeStep::new(Role::Planner).writing(".hoh/plan.md", OK_PLAN),
        FakeStep::new(Role::Developer)
            .writing("scenes/main.tscn", scene)
            .writing("scripts/player.gd", script),
        FakeStep::new(Role::Tester)
            .writing(".hoh/evidence/move.json", "{}\n")
            .writing(".hoh/evidence.json", &ok_evidence(1, "")),
    ]
}

// ---------------------------------------------------------------------------
// ① the production measurement: the defect list the retries are handed
// ---------------------------------------------------------------------------

/// The production adapter's own diagnosis of the two shapes the round of record
/// produced, with no round and no engine: the fragment is named by its path, its
/// byte size and the missing node declaration; the escaped script is named by the
/// escape that GDScript does not define.  A whole project produces no defect at
/// all, so the list is not a blanket refusal.
#[test]
fn the_production_adapter_names_the_fragment_and_the_foreign_escape() {
    let temp = tempfile::tempdir().unwrap();
    let workspace = temp.path().join("workspace");
    let write_file = |relative: &str, content: &str| {
        let path = workspace.join(relative);
        std::fs::create_dir_all(path.parent().unwrap()).unwrap();
        std::fs::write(path, content).unwrap();
    };
    write_file("project.godot", "config_version=5\n");
    write_file("scenes/main.tscn", FRAGMENT_SCENE);
    write_file("scripts/player.gd", ESCAPED_SCRIPT);

    let excludes = hof_rs::runtime::policy::HashExcludes::default().merged();
    let defects = hof_rs::adapter::godot::developer_artifact_defects_in(
        &workspace,
        "res://scenes/main.tscn",
        &excludes,
    );
    let text = defects.join("\n");
    assert!(
        text.contains("scenes/main.tscn") && text.contains("artifact_write_truncated"),
        "the fragment must be named with its path and its class: {text}"
    );
    assert!(
        text.contains(&format!("{} byte(s) on disk", FRAGMENT_SCENE.len())),
        "the defect must quote the measurement, not a guess: {text}"
    );
    assert!(
        text.contains("scripts/player.gd") && text.contains("artifact_shell_residue"),
        "the foreign escape must be named too: {text}"
    );
    let mut unique = defects.clone();
    unique.sort();
    unique.dedup();
    assert_eq!(
        unique.len(),
        defects.len(),
        "no defect may be quoted twice: {defects:?}"
    );

    // A whole project: nothing to report.
    write_file(
        "scenes/main.tscn",
        "[gd_scene format=3]\n\n[ext_resource type=\"Script\" path=\"res://scripts/player.gd\" id=\"1\"]\n\n\
         [node name=\"Main\" type=\"Node2D\"]\nscript = ExtResource(\"1\")\n",
    );
    write_file("scripts/player.gd", "extends Node\n");
    let clean = hof_rs::adapter::godot::developer_artifact_defects_in(
        &workspace,
        "res://scenes/main.tscn",
        &excludes,
    );
    assert!(
        clean.is_empty(),
        "a whole project has no defects: {clean:?}"
    );
}

// ---------------------------------------------------------------------------
// ① the round: named in the warnings, closed at the gate
// ---------------------------------------------------------------------------

/// A round whose Developer delivers a fragment scene and an escaped script still
/// finishes — but the fragment is named in `result.json.warnings` and in
/// `warnings.log`, and it closes the artifact gate with a reason of its own, so
/// the round can neither treat the fragment as delivered nor hide behind the
/// editor's downstream parse error.
#[tokio::test]
async fn a_truncated_write_closes_the_gate_with_its_own_reason() {
    let temp = tempfile::tempdir().unwrap();
    let root = temp.path();
    let script = developer_round(FRAGMENT_SCENE, ESCAPED_SCRIPT);
    let (result, _records) =
        run_scenario(root, 1, script, Ablation::default(), FakeAdapter::new()).await;
    result.expect("the round completes: the gate is what judges the artifact");

    let warnings = warnings(root);
    let truncated = warnings
        .iter()
        .find(|warning| warning.contains("artifact_write_truncated"))
        .unwrap_or_else(|| panic!("the fragment must be named in warnings: {warnings:?}"));
    assert!(
        truncated.contains("scenes/main.tscn"),
        "the warning must name the file: {truncated}"
    );
    assert!(
        warnings
            .iter()
            .any(|warning| warning.contains("artifact_shell_residue")
                && warning.contains("scripts/player.gd")),
        "the escaped script must be named too: {warnings:?}"
    );
    let log = warning_log(root);
    assert!(
        log.contains("DR-86 delivered-artifact integrity")
            && log.contains("artifact_write_truncated"),
        "the run's own log must carry the finding: {log}"
    );

    let json = result_json(root);
    assert_eq!(
        json["artifact_gate"]["applicable"],
        Value::Bool(true),
        "an integrity finding is a gate check that always applies: {json}"
    );
    assert_eq!(json["artifact_gate"]["launchable"], Value::Bool(false));
    let reasons = gate_reasons(root);
    assert!(
        reasons
            .iter()
            .any(|reason| reason.starts_with("artifact_integrity:")
                && reason.contains("scenes/main.tscn")),
        "the gate must name the truncation itself: {reasons:?}"
    );
    assert!(
        reasons
            .iter()
            .any(|reason| reason.contains("artifact_shell_residue")),
        "the gate must name the escape too: {reasons:?}"
    );
}

// ---------------------------------------------------------------------------
// ② every write-capable retry carries a diagnostic
// ---------------------------------------------------------------------------

/// The Developer's wrap-up retry — the call that wrote the 20-byte scene in
/// `smoke-t16` with a prompt that carried nothing — is handed the verbatim defect
/// list, and is told to rewrite the whole file rather than patch the fragment.
#[tokio::test]
async fn a_developer_wrap_up_retry_is_handed_the_verbatim_defects() {
    let temp = tempfile::tempdir().unwrap();
    let root = temp.path();
    let script = vec![
        FakeStep::new(Role::Planner).writing(".hoh/plan.md", OK_PLAN),
        // Burns its budget without leaving a usable artifact.
        FakeStep::new(Role::Developer).exiting("LimitsExceeded"),
        // The single wrap-up retry writes a whole project.
        FakeStep::new(Role::Developer)
            .writing("project.godot", "config_version=5\n")
            .writing("scenes/main.tscn", "[gd_scene format=3]\n"),
        FakeStep::new(Role::Tester)
            .writing(".hoh/evidence/move.json", "{}\n")
            .writing(".hoh/evidence.json", &ok_evidence(1, "")),
    ];
    let defect = "scenes/main.tscn (20 byte(s) on disk): no `[node ...]` declaration was found";
    let adapter = FakeAdapter::new().with_developer_artifact_defects(vec![defect.to_string()]);
    let (result, records) = run_scenario(root, 1, script, Ablation::default(), adapter).await;
    result.expect("the wrap-up retry completes the round");

    assert_eq!(records.len(), 4, "planner + 2 developer attempts + tester");
    let retry = records[2]
        .retry_context
        .as_deref()
        .unwrap_or_default()
        .to_string();
    assert!(retry.contains("STEP BUDGET EXHAUSTED"), "{retry}");
    assert!(
        retry.contains(defect),
        "the write-capable retry must be handed the runtime's own measurement: {retry}"
    );
    assert!(
        retry.contains("Rewrite the **whole** file"),
        "and it must be told a whole write is what is wanted: {retry}"
    );
    assert_eq!(
        result_json(root)["wrap_up_retry_used"],
        Value::Bool(true),
        "the retry really was the wrap-up"
    );
}

/// The Planner's wrap-up retry carries the schema issues the previous attempt was
/// rejected for; before this, the wrap-up path replaced them with the bare
/// instruction plus the shape block.
#[tokio::test]
async fn a_role_wrap_up_retry_is_handed_the_schema_issues() {
    let temp = tempfile::tempdir().unwrap();
    let root = temp.path();
    let script = vec![
        FakeStep::new(Role::Planner).exiting("LimitsExceeded"),
        FakeStep::new(Role::Planner).writing(".hoh/plan.md", OK_PLAN),
        FakeStep::new(Role::Developer).writing("project.godot", "config_version=5\n"),
        FakeStep::new(Role::Tester)
            .writing(".hoh/evidence/move.json", "{}\n")
            .writing(".hoh/evidence.json", &ok_evidence(1, "")),
    ];
    let (result, records) =
        run_scenario(root, 1, script, Ablation::default(), FakeAdapter::new()).await;
    result.expect("the wrap-up retry writes a valid plan");

    let retry = records[1]
        .retry_context
        .as_deref()
        .unwrap_or_default()
        .to_string();
    assert!(
        retry.contains("the planner artifact is missing"),
        "the rejected attempt's own issue must be quoted: {retry}"
    );
    assert!(retry.contains("STEP BUDGET EXHAUSTED"), "{retry}");
    assert!(
        retry.contains("REQUIRED ARTIFACT SHAPE"),
        "the shape block must still travel with it: {retry}"
    );
}

/// The same for the Tester, whose artifact the round's verdict depends on.
///
/// The candidate view carries an **empty** `.hoh/evidence.json` placeholder, so a
/// tester that runs out of budget is the DR-68 ①(b) shape: the in-gate loop spends
/// its one shape-carrying retry, then stops, and the wrap-up retry is the call
/// that must be handed the issues.
#[tokio::test]
async fn the_tester_wrap_up_retry_is_handed_the_schema_issues() {
    let temp = tempfile::tempdir().unwrap();
    let root = temp.path();
    let script = vec![
        FakeStep::new(Role::Planner).writing(".hoh/plan.md", OK_PLAN),
        FakeStep::new(Role::Developer).writing("project.godot", "config_version=5\n"),
        FakeStep::new(Role::Tester).exiting("LimitsExceeded"),
        FakeStep::new(Role::Tester).exiting("LimitsExceeded"),
        FakeStep::new(Role::Tester)
            .writing(".hoh/evidence/move.json", "{}\n")
            .writing(".hoh/evidence.json", &ok_evidence(1, "")),
    ];
    let (result, records) =
        run_scenario(root, 1, script, Ablation::default(), FakeAdapter::new()).await;
    result.expect("the wrap-up retry writes a valid evidence bundle");

    assert_eq!(records.len(), 5, "planner + developer + 3 tester attempts");
    let retry = records[4]
        .retry_context
        .as_deref()
        .unwrap_or_default()
        .to_string();
    assert!(
        retry.contains("the tester artifact is missing")
            || retry.contains("evidence is not valid JSON"),
        "the rejected attempt's own issue must be quoted: {retry}"
    );
    assert!(retry.contains("STEP BUDGET EXHAUSTED"), "{retry}");
}

/// The **repair** call is the one retry that already received a diagnostic; it now
/// also receives the integrity audit, so a fragment is named to it in the same
/// place the battery's own failures are.
#[tokio::test]
async fn the_repair_call_is_handed_the_integrity_audit() {
    let temp = tempfile::tempdir().unwrap();
    let root = temp.path();
    let script = vec![
        FakeStep::new(Role::Planner).writing(".hoh/plan.md", OK_PLAN),
        // Delivers the fragment; the deterministic gate then refuses the project.
        FakeStep::new(Role::Developer).writing("scenes/main.tscn", FRAGMENT_SCENE),
        // The one allowed targeted repair.
        FakeStep::new(Role::Developer).writing("scenes/main.tscn", "[gd_scene format=3]\n"),
        FakeStep::new(Role::Tester)
            .writing(".hoh/evidence/move.json", "{}\n")
            .writing(".hoh/evidence.json", &ok_evidence(1, "")),
    ];
    let adapter = FakeAdapter::new().with_gate_failure("the project does not launch");
    let (result, records) = run_scenario(root, 1, script, Ablation::default(), adapter).await;
    result.expect("the round completes with a red gate, not a contract violation");

    assert_eq!(records.len(), 4, "planner + developer + repair + tester");
    let repair = records[2]
        .retry_context
        .as_deref()
        .unwrap_or_default()
        .to_string();
    assert!(
        repair.contains("LAUNCH GATE FAILED"),
        "the battery's own diagnostic must still be there: {repair}"
    );
    assert!(
        repair.contains("Delivered-artifact integrity audit")
            && repair.contains("artifact_write_truncated")
            && repair.contains("scenes/main.tscn"),
        "the repair must be told which file is a fragment: {repair}"
    );
    assert_eq!(
        result_json(root)["artifact_gate"]["launchable"],
        Value::Bool(false),
        "the repair did not clear the adapter's declared gate failure"
    );
}

// ---------------------------------------------------------------------------
// ④ the frozen view
// ---------------------------------------------------------------------------

/// The `smoke-t16` first-round shape: the Tester writes a stray file into the
/// frozen candidate view (plus a modified frozen file).  D295(b) rules that the
/// round **rejects** — R4/R13 say a QA write into the frozen snapshot is a
/// violation, and a criterion measures compliance, not repairability — while the
/// acts that make the violation auditable still happen: the frozen bytes come
/// back from the `A_t` snapshot, the stray bytes are preserved as evidence under
/// `tester-writes/`, the fact is recorded, and the **verdict the battery already
/// produced** travels with the failure instead of being replaced by a
/// `not_applicable` stub.
#[tokio::test]
async fn a_tester_write_into_the_frozen_view_is_restored_and_the_round_rejects() {
    let temp = tempfile::tempdir().unwrap();
    let root = temp.path();
    let script = vec![
        FakeStep::new(Role::Planner).writing(".hoh/plan.md", OK_PLAN),
        FakeStep::new(Role::Developer)
            .writing("project.godot", "config_version=5\n")
            .writing("scenes/main.tscn", "[gd_scene format=3]\n"),
        FakeStep::new(Role::Tester)
            // The stray write: the relative path is the frozen candidate view.
            .writing("({type", "")
            .writing("Coins", "2288\r\n")
            .writing(".hoh/evidence/move.json", "{}\n")
            .writing(".hoh/evidence.json", &ok_evidence(1, "")),
    ];
    let (result, _records) =
        run_scenario(root, 1, script, Ablation::default(), FakeAdapter::new()).await;
    let error = result.expect_err("D295(b): a Tester write into the frozen view must be rejected");
    match as_hof_error(&error).expect("typed error") {
        HofError::Contract { violation, .. } => {
            assert_eq!(*violation, ContractViolation::QaContaminatedCandidate)
        }
        other => panic!("unexpected error: {other:?}"),
    }

    let json = result_json(root);
    assert_eq!(json["ok"], Value::Bool(false), "{json}");
    assert_eq!(json["reason"], Value::String("contract_violation".into()));
    assert_eq!(json["failed_role"], Value::String("tester".into()));
    assert!(
        warnings(root)
            .iter()
            .any(|warning| warning == "qa_contaminated_candidate_restored"),
        "the round must say the view was contaminated, restored and preserved: {:?}",
        warnings(root)
    );
    let log = warning_log(root);
    assert!(
        log.contains("qa_contaminated_candidate_restored")
            && log.contains("DR-86 ④")
            && log.contains("({type"),
        "the run log must carry the difference verbatim: {log}"
    );

    let iter = root.join("runs/run-1/iter-1");
    assert!(
        !iter.join("candidate/({type").exists(),
        "the frozen view must not keep a stray file"
    );
    assert_eq!(
        std::fs::read(iter.join("tester-writes/candidate/({type")).unwrap(),
        b"",
        "the stray bytes are preserved, never deleted"
    );
    assert_eq!(
        std::fs::read(iter.join("tester-writes/candidate/Coins")).unwrap(),
        b"2288\r\n"
    );
    assert_eq!(
        std::fs::read_to_string(iter.join("candidate/scenes/main.tscn")).unwrap(),
        "[gd_scene format=3]\n",
        "the frozen bytes are back even though the round is rejected"
    );

    // The gate verdict the round exists to produce is present and is the real
    // one, not a `not_applicable` stub: this adapter declares no battery step to
    // judge, and the stub's own reason string must not be the one published.
    assert!(
        json["artifact_gate"]["reasons"]
            .as_array()
            .map(|reasons| reasons
                .iter()
                .filter_map(Value::as_str)
                .all(|reason| !reason.contains("no artifact gate was produced")))
            .unwrap_or(true),
        "the verdict must be the one the battery produced, not the failure stub: {json}"
    );
    assert!(
        !json["battery_passes"]
            .as_array()
            .map(|passes| passes.is_empty())
            .unwrap_or(true),
        "the battery that produced the verdict must be in the record: {json}"
    );
    assert!(
        json["candidate_id"].is_string() && json["version_id"].is_string(),
        "the frozen identity must survive the rejection: {json}"
    );
    assert!(
        warnings(root)
            .iter()
            .any(|warning| warning == "qa_contaminated_candidate"),
        "the violation code must be recorded alongside the restore token: {:?}",
        warnings(root)
    );
}

/// A round that fails **after** the battery still publishes the gate verdict it
/// really produced, instead of replacing it with the `not_applicable` stub.
#[tokio::test]
async fn a_late_failure_keeps_the_gate_verdict_it_produced() {
    let temp = tempfile::tempdir().unwrap();
    let root = temp.path();
    let script = vec![
        FakeStep::new(Role::Planner).writing(".hoh/plan.md", OK_PLAN),
        FakeStep::new(Role::Developer).writing("project.godot", "config_version=5\n"),
        // The one allowed targeted repair (the declared gate failure is red).
        FakeStep::new(Role::Developer).writing("project.godot", "config_version=5\n"),
        // The Tester never produces a valid bundle: its in-gate shape retry and
        // its one wrap-up retry all run out of budget, so the round fails after
        // the battery has already answered.
        FakeStep::new(Role::Tester).exiting("LimitsExceeded"),
        FakeStep::new(Role::Tester).exiting("LimitsExceeded"),
        FakeStep::new(Role::Tester).exiting("LimitsExceeded"),
    ];
    let adapter = FakeAdapter::new().with_gate_failure("the project does not launch");
    let (result, _records) = run_scenario(root, 1, script, Ablation::default(), adapter).await;
    let error = result.expect_err("a tester that never submits must fail the round");
    assert!(
        error.to_string().to_lowercase().contains("tester"),
        "{error}"
    );

    let json = result_json(root);
    assert_eq!(json["ok"], Value::Bool(false));
    assert_eq!(
        json["artifact_gate"]["applicable"],
        Value::Bool(true),
        "a gate that really ran must not be published as not-applicable: {json}"
    );
    assert_eq!(json["artifact_gate"]["launchable"], Value::Bool(false));
    assert!(
        !gate_reasons(root).is_empty(),
        "the reasons the gate was red must survive too: {}",
        json["artifact_gate"]
    );
}
