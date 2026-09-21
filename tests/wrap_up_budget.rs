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
