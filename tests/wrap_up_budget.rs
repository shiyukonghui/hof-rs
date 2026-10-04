//! DR-18 — step budget and the "close out first" discipline.
//!
//! The first real smoke run spent 5/5 calls on `LimitsExceeded` without ever
//! producing an artifact.  These tests pin the three mechanisms that fix it:
//! the rendered budget text, the early stop of the schema retry loop, and the
//! single bounded wrap-up retry.

mod common;

use common::*;
use hof_rs::config::{load_config, AgentLimits};
use hof_rs::model::{Ablation, Role};
use hof_rs::runtime::invoke::{is_limits_exceeded, render_prompt_with_budget};
use serde_json::Value;

fn read_json(path: &std::path::Path) -> Value {
    serde_json::from_str(&read(path)).expect("json")
}

/// A main scene that passes the DR-24 structure check and names a real script.
const VALID_DEV_SCENE: &str = "[gd_scene load_steps=2 format=3]\n\n\
[ext_resource type=\"Script\" path=\"res://scripts/player.gd\" id=\"1\"]\n\n\
[node name=\"Main\" type=\"Node2D\"]\n\
script = ExtResource(\"1\")\n";

fn result_json(root: &std::path::Path) -> Value {
    read_json(&root.join("runs/run-1/iter-1/result.json"))
}

#[test]
fn config_carries_the_new_budget_and_readiness_keys() {
    let config = load_config(&[]).expect("default config");
    assert_eq!(config.agent.step_limit, 150, "DR-18 step_limit");
    assert_eq!(config.agent.wrap_up_steps, 25, "DR-18 wrap_up_steps");
    assert_eq!(
        config.tools.ready_timeout_seconds, 30,
        "DR-20 ready_timeout_seconds"
    );
    assert_eq!(
        config.runtime.max_evidence_bytes,
        8 * 1024 * 1024,
        "DR-36 max_evidence_bytes defaults to 8 MiB"
    );
    // Defaults must agree with the file so a minimal config keeps working.
    let defaults = AgentLimits::default();
    assert_eq!(defaults.step_limit, 150);
    assert_eq!(defaults.wrap_up_steps, 25);
}

#[test]
fn every_role_prompt_renders_the_budget_and_the_discipline() {
    let limits = AgentLimits {
        step_limit: 150,
        wrap_up_steps: 25,
        ..AgentLimits::default()
    };
    for template in [
        hof_rs::prompts::PLANNER_PROMPT,
        hof_rs::prompts::DEVELOPER_PROMPT,
        hof_rs::prompts::TESTER_PROMPT,
    ] {
        let rendered = render_prompt_with_budget(template, 1, &limits);
        assert!(
            !rendered.contains("{{"),
            "an unrendered placeholder survived: {rendered}"
        );
        assert!(rendered.contains("150"), "missing step_limit: {rendered}");
        assert!(rendered.contains("25"), "missing wrap_up_steps: {rendered}");
        assert!(
            rendered.contains("immediately"),
            "the close-out discipline must be explicit: {rendered}"
        );
    }
}

/// DR-18 order discipline: the Tester must write a minimal artifact first.
#[test]
fn tester_prompt_requires_the_early_skeleton() {
    let prompt =
        render_prompt_with_budget(hof_rs::prompts::TESTER_PROMPT, 1, &AgentLimits::default());
    assert!(prompt.contains("first few steps"), "{prompt}");
    assert!(prompt.contains(".hoh/evidence.json"), "{prompt}");
    assert!(!prompt.contains("{{"), "{prompt}");
}

#[test]
fn limits_detection_is_case_insensitive_and_narrow() {
    assert!(is_limits_exceeded("LimitsExceeded"));
    assert!(is_limits_exceeded("limitsexceeded"));
    assert!(!is_limits_exceeded("Submitted"));
    assert!(!is_limits_exceeded(""));
}

/// DR-18 ②: first call ends with `LimitsExceeded` and no artifact; the runtime
/// spends exactly one small wrap-up retry, which succeeds.
#[tokio::test]
async fn limits_exceeded_then_one_wrap_up_retry_succeeds() {
    let temp = tempfile::tempdir().unwrap();
    let root = temp.path();
    let script = vec![
        // Call 1: burns its budget without writing the artifact.
        FakeStep::new(Role::Planner).exiting("LimitsExceeded"),
        // The single wrap-up retry writes a valid artifact immediately.
        FakeStep::new(Role::Planner).writing(".hoh/plan.md", OK_PLAN),
        FakeStep::new(Role::Developer).writing("project.godot", "config_version=5\n"),
        FakeStep::new(Role::Tester)
            .writing(".hoh/evidence/move.json", "{}\n")
            .writing(".hoh/evidence.json", &ok_evidence(1, "")),
    ];
    let (result, records) =
        run_scenario(root, 1, script, Ablation::default(), FakeAdapter::new()).await;
    result.expect("the wrap-up retry must save the round");

    assert_eq!(records.len(), 4, "attempt 1 + wrap-up + developer + tester");
    assert_eq!(records[0].role, Role::Planner);
    assert_eq!(records[1].role, Role::Planner);

    let retry = records[1].retry_context.as_deref().unwrap_or_default();
    assert!(
        retry.contains("STEP BUDGET EXHAUSTED"),
        "wrap-up context: {retry}"
    );
    assert!(
        retry.to_lowercase().contains("artifact"),
        "wrap-up context must demand the artifact: {retry}"
    );
    assert!(
        records[1].limits.contains("step_limit: 25"),
        "the wrap-up budget must be min(wrap_up_steps, 30): {}",
        records[1].limits
    );
    assert!(
        records[1].system_prompt.contains("25"),
        "the wrap-up call must be told its real budget: {}",
        records[1].system_prompt
    );
    assert!(
        !records[0].system_prompt.contains("{{"),
        "prompts are rendered before the harness sees them"
    );

    // The trajectory numbering keeps increasing: no attempt overwrites another.
    let traj = root.join("runs/run-1/iter-1/traj");
    assert!(traj.join("planner.attempt1.json").is_file());
    assert!(traj.join("planner.attempt2.json").is_file());

    let json = result_json(root);
    assert_eq!(json["ok"], Value::Bool(true));
    assert_eq!(json["wrap_up_retry_used"], Value::Bool(true));
}

/// DR-18 ③: two consecutive `LimitsExceeded` calls stop there — no second
/// wrap-up retry, and the run fails as a whole.
#[tokio::test]
async fn consecutive_limits_failures_stop_after_one_retry() {
    let temp = tempfile::tempdir().unwrap();
    let root = temp.path();
    let script = vec![
        FakeStep::new(Role::Planner).exiting("LimitsExceeded"),
        FakeStep::new(Role::Planner).exiting("LimitsExceeded"),
    ];
    let (result, records) =
        run_scenario(root, 1, script, Ablation::default(), FakeAdapter::new()).await;

    let error = result.expect_err("the round must fail");
    assert_eq!(
        hof_rs::errors::as_hof_error(&error)
            .expect("typed error")
            .exit_code(),
        3,
        "schema retries exhausted -> exit 3"
    );
    assert_eq!(
        records.len(),
        2,
        "exactly one wrap-up retry is allowed, never more: {records:?}"
    );

    let json = result_json(root);
    assert_eq!(json["ok"], Value::Bool(false));
    assert_eq!(json["failed_role"], serde_json::json!("planner"));
    assert_eq!(json["wrap_up_retry_used"], Value::Bool(true));
}

// ---------------------------------------------------------------------------
// DR-37 — the wrap-up retry is only spent when the artifact is really missing
// ---------------------------------------------------------------------------

/// One iteration whose Developer ends exactly as scripted, with a Tester step so
/// the round can still complete.
fn developer_script(developer: FakeStep) -> Vec<FakeStep> {
    vec![
        FakeStep::new(Role::Planner).writing(".hoh/plan.md", OK_PLAN),
        developer,
        FakeStep::new(Role::Tester)
            .writing(".hoh/evidence/move.json", "{}\n")
            .writing(".hoh/evidence.json", &ok_evidence(1, "")),
    ]
}

/// DR-37 ①: `smoke-t5` burned 0.94M tokens / 3.1 minutes on a wrap-up retry for
/// a Developer whose artifact was already valid.  `LimitsExceeded` alone is not
/// a trigger any more.
#[tokio::test]
async fn a_valid_artifact_does_not_trigger_the_wrap_up_retry() {
    let temp = tempfile::tempdir().unwrap();
    let root = temp.path();
    let script = developer_script(
        FakeStep::new(Role::Developer)
            .writing("project.godot", "config_version=5\n")
            .exiting("LimitsExceeded"),
    );
    let adapter = FakeAdapter::new().with_developer_artifact_valid(true);
    let (result, records) = run_scenario(root, 1, script, Ablation::default(), adapter).await;
    result.expect("the round completes: the artifact was valid");

    let developer_calls = records
        .iter()
        .filter(|record| record.role == Role::Developer)
        .count();
    assert_eq!(
        developer_calls, 1,
        "a valid artifact must not buy a wrap-up retry: {records:?}"
    );

    let json = result_json(root);
    assert_eq!(json["wrap_up_retry_used"], Value::Bool(false));
    assert_eq!(
        json["wrap_up_retry_reason"],
        serde_json::json!("not_triggered"),
        "result.json must say why the retry did not happen"
    );
}

/// DR-37 ②: the budget ran out *and* the artifact is not usable — that is the
/// case the wrap-up retry exists for, and the reason is recorded verbatim.
#[tokio::test]
async fn a_missing_artifact_triggers_the_wrap_up_retry_with_a_reason() {
    let temp = tempfile::tempdir().unwrap();
    let root = temp.path();
    let script = vec![
        FakeStep::new(Role::Planner).writing(".hoh/plan.md", OK_PLAN),
        FakeStep::new(Role::Developer).exiting("LimitsExceeded"),
        FakeStep::new(Role::Developer)
            .writing("project.godot", "config_version=5\n")
            .writing("scenes/main.tscn", VALID_DEV_SCENE),
        FakeStep::new(Role::Tester)
            .writing(".hoh/evidence/move.json", "{}\n")
            .writing(".hoh/evidence.json", &ok_evidence(1, "")),
    ];
    let (result, records) =
        run_scenario(root, 1, script, Ablation::default(), FakeAdapter::new()).await;
    result.expect("the wrap-up retry must save the round");

    let developer_calls = records
        .iter()
        .filter(|record| record.role == Role::Developer)
        .count();
    assert_eq!(developer_calls, 2, "one wrap-up retry: {records:?}");

    let json = result_json(root);
    assert_eq!(json["wrap_up_retry_used"], Value::Bool(true));
    assert_eq!(
        json["wrap_up_retry_reason"],
        serde_json::json!("artifact_missing")
    );
}

/// DR-37 ③: the pre-existing behaviour of a role that ends **normally** without
/// submitting anything is untouched — the schema gate still spends its retry,
/// and because no wrap-up retry was used the reason stays `not_triggered`.
#[tokio::test]
async fn a_normal_finish_without_an_artifact_keeps_its_existing_retry() {
    let temp = tempfile::tempdir().unwrap();
    let root = temp.path();
    let script = vec![
        // Ends normally, submits nothing -> the schema gate retries.
        FakeStep::new(Role::Planner).exiting("Submitted"),
        FakeStep::new(Role::Planner).writing(".hoh/plan.md", OK_PLAN),
        FakeStep::new(Role::Developer).writing("project.godot", "config_version=5\n"),
        FakeStep::new(Role::Tester)
            .writing(".hoh/evidence/move.json", "{}\n")
            .writing(".hoh/evidence.json", &ok_evidence(1, "")),
    ];
    let (result, records) =
        run_scenario(root, 1, script, Ablation::default(), FakeAdapter::new()).await;
    result.expect("the schema retry must still save the round");

    let planner_calls = records
        .iter()
        .filter(|record| record.role == Role::Planner)
        .count();
    assert_eq!(
        planner_calls, 2,
        "a missing artifact still costs a schema retry: {records:?}"
    );
    let json = result_json(root);
    assert_eq!(json["wrap_up_retry_used"], Value::Bool(false));
    assert_eq!(
        json["wrap_up_retry_reason"],
        serde_json::json!("not_triggered")
    );
}
