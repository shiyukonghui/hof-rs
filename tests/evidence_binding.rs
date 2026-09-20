//! R4/R7 — evidence binding: verified/gap partition, candidate stamping, and
//! the counter-examples that must never pass.
//!
//! The run-loop level counter-examples (`rejects_contaminated_candidate`,
//! `rejects_workspace_drift`, `rejects_direct_real_workspace_write`) live in
//! this file as well; `bind` is the pure half of the same contract.

mod common;

use std::path::Path;

use common::*;
use hof_rs::errors::{as_hof_error, HofError};
use hof_rs::model::{Ablation, ContractViolation, EvidenceBundle, IssueCode, Role};
use hof_rs::runtime::evidence::bind;
use hof_rs::runtime::schema::gate_evidence;

fn load_fixture(name: &str) -> EvidenceBundle {
    let raw = std::fs::read_to_string(format!("tests/fixtures/{name}")).expect("fixture");
    serde_json::from_str(&raw).expect("fixture must deserialize")
}

fn codes(issues: &[hof_rs::model::SchemaIssue]) -> Vec<IssueCode> {
    issues.iter().map(|issue| issue.code).collect()
}

fn fixture_view(temp: &Path, with_evidence_file: bool) -> std::path::PathBuf {
    let view = temp.join("candidate");
    std::fs::create_dir_all(view.join(".hoh/evidence")).unwrap();
    if with_evidence_file {
        std::fs::write(view.join(".hoh/evidence/move.json"), "{\"ok\":true}").unwrap();
    }
    view
}

#[test]
fn bind_stamps_candidate_and_preserves_text() {
    let temp = tempfile::tempdir().unwrap();
    let view = fixture_view(temp.path(), true);
    let mut bundle = load_fixture("evidence_ok.json");
    let before: Vec<String> = bundle
        .verified_records
        .iter()
        .chain(bundle.gap_records.iter())
        .map(|record| record.claim.clone())
        .collect();

    bind(&mut bundle, "cand-1", &view).expect("binding must succeed");

    for record in bundle
        .verified_records
        .iter()
        .chain(bundle.gap_records.iter())
    {
        for exec in &record.execution_records {
            assert_eq!(exec.candidate_id, "cand-1");
        }
    }
    let after: Vec<String> = bundle
        .verified_records
        .iter()
        .chain(bundle.gap_records.iter())
        .map(|record| record.claim.clone())
        .collect();
    // The runtime must never rewrite the Tester's assessment.
    assert_eq!(before, after);
    assert!(bundle
        .gap_records
        .iter()
        .all(|record| record.player_impact.is_some() && record.recommended_update.is_some()));
}

#[test]
fn verified_gap_partition() {
    // {verified} ∩ {gap} == ∅ is a hard error.
    let duplicate = load_fixture("evidence_dup_claim.json");
    let issues = hof_rs::model::validate_evidence(&duplicate, "cand").unwrap_err();
    assert!(codes(&issues).contains(&IssueCode::DuplicateClaimId));

    // A gap claim without guidance is a hard error.
    let mut missing_guidance = load_fixture("evidence_ok.json");
    missing_guidance.gap_records[0].recommended_update = None;
    let issues = hof_rs::model::validate_evidence(&missing_guidance, "cand").unwrap_err();
    assert!(codes(&issues).contains(&IssueCode::GapMissingGuidance));

    // A verified claim without execution records is a hard error.
    let mut unsupported = load_fixture("evidence_ok.json");
    unsupported.verified_records[0].execution_records.clear();
    let issues = hof_rs::model::validate_evidence(&unsupported, "cand").unwrap_err();
    assert!(codes(&issues).contains(&IssueCode::UnsupportedVerified));

    // The well-formed fixture passes both the pure validation and binding.
    let temp = tempfile::tempdir().unwrap();
    let view = fixture_view(temp.path(), true);
    let mut ok = load_fixture("evidence_ok.json");
    assert!(hof_rs::model::validate_evidence(&ok, "cand").is_ok());
    assert!(bind(&mut ok, "cand", &view).is_ok());
}

#[test]
fn rejects_dangling_evidence() {
    let temp = tempfile::tempdir().unwrap();
    // The referenced screenshot is deliberately absent from the candidate view.
    let view = fixture_view(temp.path(), false);
    let mut bundle = load_fixture("evidence_dangling.json");

    let issues = bind(&mut bundle, "cand", &view).unwrap_err();
    assert!(codes(&issues).contains(&IssueCode::DanglingEvidence));
}

#[test]
fn rejects_candidate_mismatch() {
    let temp = tempfile::tempdir().unwrap();
    let view = fixture_view(temp.path(), true);
    let mut bundle = load_fixture("evidence_ok.json");
    bundle.verified_records[0].execution_records[0].candidate_id = "other-candidate".to_string();

    let issues = bind(&mut bundle, "cand", &view).unwrap_err();
    assert!(codes(&issues).contains(&IssueCode::CandidateMismatch));
}

#[test]
fn rejects_absolute_path_evidence_outside_the_view() {
    // §4.6: an absolute path is never resolved against the view root; the
    // record is rejected unless it is a relative path inside the candidate.
    let temp = tempfile::tempdir().unwrap();
    let view = fixture_view(temp.path(), true);
    let mut bundle = load_fixture("evidence_ok.json");
    bundle.verified_records[0].execution_records[0].path =
        Some("C:/Windows/not-in-the-view.png".to_string());

    let issues = bind(&mut bundle, "cand", &view).unwrap_err();
    assert!(codes(&issues).contains(&IssueCode::DanglingEvidence));
}

#[tokio::test]
async fn gate_evidence_accepts_a_bound_candidate() {
    let temp = tempfile::tempdir().unwrap();
    let view = fixture_view(temp.path(), true);
    let traj = temp.path().join("traj");
    let harness = FakeHarness::new(vec![
        FakeStep::new(Role::Tester).writing(".hoh/evidence.json", &ok_evidence(1, ""))
    ]);
    let model = serde_json::json!({"model_name": "openai/qwen/qwen3.8-27b"});
    let base = role_invocation(
        &view,
        Role::Tester,
        1,
        &traj.join("tester.attempt1.json"),
        model,
    );

    let bundle = gate_evidence(&harness, &base, "cand-1", 2)
        .await
        .expect("valid evidence must pass the gate");
    assert_eq!(bundle.verified_records.len(), 1);
    assert_eq!(bundle.gap_records.len(), 1);
    assert_eq!(
        bundle.verified_records[0].execution_records[0].candidate_id,
        "cand-1"
    );
}

// ---------------------------------------------------------------------------
// R4 at run-loop level: the QA candidate is frozen, and the real artifact is
// checked around the QA stage as well (the copy alone cannot stop an absolute
// path write).
// ---------------------------------------------------------------------------

fn result_json(root: &Path) -> serde_json::Value {
    let path = root.join("runs/run-1/iter-1/result.json");
    serde_json::from_str(&std::fs::read_to_string(path).expect("result.json")).expect("json")
}

fn assert_contract(error: &anyhow::Error, expected: ContractViolation) {
    let hof = as_hof_error(error).expect("typed error");
    match hof {
        HofError::Contract { violation, .. } => assert_eq!(*violation, expected),
        other => panic!("unexpected error: {other:?}"),
    }
}

#[tokio::test]
async fn rejects_contaminated_candidate() {
    let temp = tempfile::tempdir().unwrap();
    let root = temp.path();
    let script = vec![
        FakeStep::new(Role::Planner).writing(".hoh/plan.md", OK_PLAN),
        FakeStep::new(Role::Developer).writing("project.godot", "config_version=5\n"),
        FakeStep::new(Role::Tester)
            .writing(".hoh/evidence/move.json", "{}\n")
            .writing("scripts/cheat.gd", "extends Node\n")
            .writing(".hoh/evidence.json", &ok_evidence(1, "")),
    ];
    let (result, _) = run_scenario(root, 1, script, Ablation::default(), FakeAdapter::new()).await;
    let error = result.expect_err("QA must not modify the frozen candidate");
    assert_contract(&error, ContractViolation::QaContaminatedCandidate);
    assert_eq!(
        result_json(root)["failed_role"],
        serde_json::json!("tester")
    );
}

#[tokio::test]
async fn rejects_workspace_drift() {
    let temp = tempfile::tempdir().unwrap();
    let root = temp.path();
    // The deterministic stage simulates the editor (MCP) changing the real
    // project after A_t was hashed.
    let adapter = FakeAdapter::new().with_drift(
        root.join("workspace"),
        "drifted.gd",
        "# the editor project moved under the QA candidate\n",
    );
    let (result, _) = run_scenario(root, 1, happy_script(), Ablation::default(), adapter).await;
    let error = result.expect_err("QA must be rejected when the artifact drifted");
    assert_contract(&error, ContractViolation::WorkspaceDriftBeforeQa);
    assert_eq!(
        result_json(root)["failed_role"],
        serde_json::json!("tester")
    );
}

#[tokio::test]
async fn rejects_direct_real_workspace_write() {
    let temp = tempfile::tempdir().unwrap();
    let root = temp.path();
    let script = vec![
        FakeStep::new(Role::Planner).writing(".hoh/plan.md", OK_PLAN),
        FakeStep::new(Role::Developer).writing("project.godot", "config_version=5\n"),
        FakeStep::new(Role::Tester)
            .writing(".hoh/evidence/move.json", "{}\n")
            .writing(".hoh/evidence.json", &ok_evidence(1, ""))
            .outside(
                root.join("workspace/scripts/hacked_by_tester.gd"),
                "extends Node\n",
            ),
    ];
    let (result, _) = run_scenario(root, 1, script, Ablation::default(), FakeAdapter::new()).await;
    let error = result.expect_err("QA must not write the real artifact through an absolute path");
    assert_contract(&error, ContractViolation::ReadOnlyRoleWroteArtifact);
    assert_eq!(
        result_json(root)["failed_role"],
        serde_json::json!("tester")
    );
}
