//! R6 — schema validation with bounded retries, and the "silence is failure"
//! rule: a missing artifact still consumes an attempt and never passes.

mod common;

use common::*;
use hof_rs::errors::{as_hof_error, HofError};
use hof_rs::model::Role;
use hof_rs::runtime::schema::{gate_evidence, gate_plan};

#[tokio::test]
async fn plan_retry_then_success() {
    let temp = tempfile::tempdir().unwrap();
    let view = temp.path().join("planner-view");
    let traj = temp.path().join("traj");

    let harness = FakeHarness::new(vec![
        FakeStep::new(Role::Planner).writing(".hoh/plan.md", BAD_PLAN),
        FakeStep::new(Role::Planner).writing(".hoh/plan.md", OK_PLAN),
    ]);
    let model = serde_json::json!({"model_name": "openai/qwen/qwen3.8-27b"});
    let base = role_invocation(
        &view,
        Role::Planner,
        1,
        &traj.join("planner.attempt1.json"),
        model,
    );

    let doc = gate_plan(&harness, &base, 2)
        .await
        .expect("plan must be accepted");
    assert_eq!(doc.priorities.len(), 1);
    assert_eq!(doc.iteration, 1);

    // Two attempts were made, and the second one received the schema issues.
    let records = harness.records();
    assert_eq!(records.len(), 2);
    assert!(traj.join("planner.attempt1.json").exists());
    assert!(traj.join("planner.attempt2.json").exists());
    let retry = records[1].retry_context.as_deref().unwrap_or_default();
    assert!(retry.contains("missing_section"), "retry context: {retry}");
    assert!(retry.contains(".hoh/plan.md"), "retry context: {retry}");
}

#[tokio::test]
async fn evidence_retry_exhausted() {
    let temp = tempfile::tempdir().unwrap();
    let view = temp.path().join("candidate");
    let traj = temp.path().join("traj");

    let harness = FakeHarness::new(vec![
        FakeStep::new(Role::Tester).writing(".hoh/evidence.json", &bad_evidence()),
        FakeStep::new(Role::Tester).writing(".hoh/evidence.json", &bad_evidence()),
        FakeStep::new(Role::Tester).writing(".hoh/evidence.json", &bad_evidence()),
    ]);
    let model = serde_json::json!({"model_name": "openai/qwen/qwen3.8-27b"});
    let base = role_invocation(
        &view,
        Role::Tester,
        1,
        &traj.join("tester.attempt1.json"),
        model,
    );

    let error = gate_evidence(&harness, &base, "candidate-1", 2)
        .await
        .expect_err("three invalid attempts must fail");
    let hof = as_hof_error(&error).expect("typed error");
    match hof {
        HofError::SchemaFailure {
            role,
            attempts,
            issues,
        } => {
            assert_eq!(*role, Role::Tester);
            assert_eq!(*attempts, 3);
            assert_eq!(issues.len(), 3);
        }
        other => panic!("unexpected error: {other:?}"),
    }
    assert_eq!(hof.exit_code(), 3);
    assert_eq!(harness.records().len(), 3);
}

#[tokio::test]
async fn missing_artifact_counts_as_attempt() {
    let temp = tempfile::tempdir().unwrap();
    let view = temp.path().join("candidate");
    // Note: the view exists but no artifact is ever produced.
    std::fs::create_dir_all(&view).unwrap();
    let traj = temp.path().join("traj");

    let harness = FakeHarness::new(vec![FakeStep::new(Role::Tester)]);
    let model = serde_json::json!({"model_name": "openai/qwen/qwen3.8-27b"});
    let base = role_invocation(
        &view,
        Role::Tester,
        1,
        &traj.join("tester.attempt1.json"),
        model,
    );

    let error = gate_evidence(&harness, &base, "candidate-1", 0)
        .await
        .expect_err("a missing artifact must fail, never pass silently");
    let hof = as_hof_error(&error).expect("typed error");
    match hof {
        HofError::SchemaFailure {
            attempts, issues, ..
        } => {
            assert_eq!(*attempts, 1);
            assert_eq!(issues.len(), 1);
            assert_eq!(issues[0][0].code, hof_rs::model::IssueCode::Json);
            assert!(issues[0][0].message.contains(".hoh/evidence.json"));
        }
        other => panic!("unexpected error: {other:?}"),
    }
}
