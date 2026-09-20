//! R4/R7 — evidence binding: verified/gap partition, candidate stamping, and
//! the counter-examples that must never pass.
//!
//! The run-loop level counter-examples (`rejects_contaminated_candidate`,
//! `rejects_workspace_drift`, `rejects_direct_real_workspace_write`) live in
//! this file as well; `bind` is the pure half of the same contract.

mod common;

use std::path::Path;

use common::*;
use hof_rs::model::{EvidenceBundle, IssueCode, Role};
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
