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

// ---------------------------------------------------------------------------
// DR-68 ① — the evidence record shape reaches the model on the FIRST attempt
// ---------------------------------------------------------------------------

/// The `smoke-t8` artifact, in shape: valid JSON, every top-level field present,
/// but each `execution_records[*]` carries only `path`/`observation` (no `type`)
/// and its claim carries no `claim_id`.  `validate_evidence_shape` therefore
/// passes it to serde, which rejects it with the `missing field \`type\`` message
/// the real round recorded.
fn t8_evidence() -> String {
    r#"{
  "iteration": 1,
  "qa_status": "partial",
  "verified_records": [
    {
      "claim": "player moves right",
      "execution_records": [
        {
          "path": ".hoh/evidence/move.json",
          "observation": "position.x increased from 0 to 32"
        }
      ],
      "status": "verified",
      "type": "verified"
    }
  ],
  "gap_records": [],
  "planner_handoff": {
    "preservation_constraints": [],
    "update_targets": [],
    "validation_requirements": []
  }
}
"#
    .to_string()
}

/// `smoke-t8`'s Tester was never told the record shape: `EVIDENCE_SKELETON` was
/// handed out **only** as retry context, and the retry that would have carried
/// it was suppressed by the `limits` break.  The first attempt must be told.
#[tokio::test]
async fn the_first_tester_attempt_is_told_the_evidence_record_shape() {
    let temp = tempfile::tempdir().unwrap();
    let view = temp.path().join("candidate");
    let traj = temp.path().join("traj");

    let harness = FakeHarness::new(vec![
        FakeStep::new(Role::Tester).writing(".hoh/evidence.json", &t8_evidence())
    ]);
    let model = serde_json::json!({"model_name": "openai/qwen/qwen3.8-27b"});
    let base = role_invocation(
        &view,
        Role::Tester,
        1,
        &traj.join("tester.attempt1.json"),
        model,
    );

    let _ = gate_evidence(&harness, &base, "candidate-1", 0).await;

    let records = harness.records();
    assert_eq!(records.len(), 1);
    let first = records[0].retry_context.as_deref().unwrap_or_default();
    for needle in [
        "claim_id",          // the record key serde reports *second*
        "\"type\"",          // the record key serde reports *first*
        "execution_records", // the enclosing field
        "screenshot|replay", // the legal `type` values, spelled out
    ] {
        assert!(
            first.contains(needle),
            "DR-68 ①: the first attempt must already carry `{needle}` in its shape block; \
             it received: {first:?}"
        );
    }
}

/// The other half of the `smoke-t8` mechanism: attempt 1 ended with
/// `LimitsExceeded` *and* left a present-but-invalid artifact behind, and the
/// `if limits { break; }` rule stopped the loop before the shape-carrying retry
/// could run (`schema failure for role Tester after 1 attempt(s)`).  A retry
/// that can still repair a present artifact gets exactly one attempt.
#[tokio::test]
async fn a_present_but_invalid_artifact_still_gets_one_shape_retry() {
    let temp = tempfile::tempdir().unwrap();
    let view = temp.path().join("candidate");
    let traj = temp.path().join("traj");

    let harness = FakeHarness::new(vec![
        FakeStep::new(Role::Tester)
            .writing(".hoh/evidence.json", &t8_evidence())
            .exiting("LimitsExceeded"),
        FakeStep::new(Role::Tester)
            .writing(".hoh/evidence/move.json", "{}\n")
            .writing(".hoh/evidence.json", &ok_evidence(1, "")),
    ]);
    let model = serde_json::json!({"model_name": "openai/qwen/qwen3.8-27b"});
    let base = role_invocation(
        &view,
        Role::Tester,
        1,
        &traj.join("tester.attempt1.json"),
        model,
    );

    let bundle = gate_evidence(&harness, &base, "candidate-1", 2)
        .await
        .expect("the shape retry must be allowed to recover the present artifact");
    assert_eq!(bundle.verified_records.len(), 1);

    let records = harness.records();
    assert_eq!(
        records.len(),
        2,
        "attempt 1 + exactly one shape retry: {records:?}"
    );
    let retry = records[1].retry_context.as_deref().unwrap_or_default();
    assert!(
        retry.contains("SCHEMA VALIDATION FAILED") && retry.contains("missing the required field"),
        "the retry must carry the concrete rejection: {retry:?}"
    );
    assert!(
        retry.contains("`claim_id`") && retry.contains("`type`"),
        "DR-68 ①: the retry must name *both* missing record fields in one error, \
         because serde reports them one at a time: {retry:?}"
    );
}

/// DR-68 ①(c): the shape must also be *documented*, not only injected.  The
/// prompt's output contract listed `verified_records: []`/`gap_records: []` and
/// named neither `claim_id` nor the execution record's `type`.
#[test]
fn the_tester_prompt_documents_the_evidence_record_shape() {
    let prompt = delivered_prompt(hof_rs::prompts::TESTER_PROMPT);
    for needle in [
        "claim_id",
        "\"type\"",
        "execution_records",
        "player_impact",
        "recommended_update",
    ] {
        assert!(
            prompt.contains(needle),
            "DR-68 ①(c): tester.md must document `{needle}` in its output contract"
        );
    }
}
