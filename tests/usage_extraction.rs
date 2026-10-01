//! R12 — token usage is extracted from the persisted mini trajectory and never
//! invented: a missing usage block is recorded as `usage_known = false` with
//! `None` token fields, never as zeros.

use hof_rs::model::{Role, Usage};
use hof_rs::runtime::usage::{extract_usage, merge_usage, usage_from_attempts};

const FIXTURE: &str = "tests/fixtures/traj_with_usage.json";

#[test]
fn sums_usage_across_messages() {
    let usage = extract_usage(std::path::Path::new(FIXTURE), Role::Developer, 1).unwrap();
    assert_eq!(usage.role, "developer");
    assert_eq!(usage.iteration, 1);
    assert_eq!(usage.calls, 2);
    assert_eq!(usage.prompt_tokens, Some(150));
    assert_eq!(usage.completion_tokens, Some(30));
    // message 2 omits `total_tokens`; it is refilled from prompt+completion.
    assert_eq!(usage.total_tokens, Some(180));
    assert_eq!(usage.cache_hit_tokens, Some(40));
    assert_eq!(usage.cache_miss_tokens, Some(60));
    assert!(usage.usage_known);
}

#[test]
fn unknown_when_absent() {
    let temp = tempfile::tempdir().unwrap();
    let path = temp.path().join("traj.json");
    std::fs::write(
        &path,
        r#"{
  "info": {"exit_status": "Submitted"},
  "messages": [
    {"role": "system", "content": "hello"},
    {"role": "assistant", "content": "world", "extra": {"actions": []}}
  ],
  "trajectory_format": "mini-swe-agent-1.1"
}"#,
    )
    .unwrap();

    let usage = extract_usage(&path, Role::Tester, 2).unwrap();
    assert_eq!(usage.calls, 0);
    assert!(!usage.usage_known);
    assert_eq!(usage.prompt_tokens, None);
    assert_eq!(usage.completion_tokens, None);
    assert_eq!(usage.total_tokens, None);
    assert_eq!(usage.cache_hit_tokens, None);
    assert_eq!(usage.cache_miss_tokens, None);
    assert_eq!(usage.role, "tester");
    assert_eq!(usage.iteration, 2);
}

#[test]
fn merges_partial() {
    let mut left = Usage {
        role: "developer".to_string(),
        iteration: 1,
        calls: 1,
        prompt_tokens: Some(10),
        completion_tokens: None,
        total_tokens: Some(15),
        cache_hit_tokens: None,
        cache_miss_tokens: Some(3),
        usage_known: true,
    };
    let right = Usage {
        role: "tester".to_string(),
        iteration: 1,
        calls: 2,
        prompt_tokens: None,
        completion_tokens: Some(5),
        total_tokens: None,
        cache_hit_tokens: Some(7),
        cache_miss_tokens: None,
        usage_known: false,
    };
    merge_usage(&mut left, &right);

    assert_eq!(left.role, "developer");
    assert_eq!(left.calls, 3);
    assert_eq!(left.prompt_tokens, Some(10));
    assert_eq!(left.completion_tokens, Some(5));
    assert_eq!(left.total_tokens, Some(15));
    assert_eq!(left.cache_hit_tokens, Some(7));
    assert_eq!(left.cache_miss_tokens, Some(3));
    assert!(left.usage_known);

    let mut unknown = Usage::default();
    merge_usage(&mut unknown, &Usage::default());
    assert!(!unknown.usage_known);
    assert_eq!(unknown.calls, 0);
}

/// DR-79 ②: the DR-72 ② redacted **sidecar** is a copy of one attempt, not a
/// second attempt.
///
/// `smoke-t12` and `smoke-t13` both carried `planner.attempt1.json` **and**
/// `planner.attempt1.redacted.json`; `usage_from_attempts`'s name filter
/// (`starts_with("<role>.attempt") && ends_with(".json")`) matched both, so the
/// same usage block was merged twice and the round-level planner count was
/// exactly 2× the attempt's (272,378 tokens in `smoke-t13`).  The ratio must be
/// 1.0 whenever the only extra file is a sidecar, and 2.0 only when a genuine
/// second attempt exists.
#[test]
fn a_redacted_sidecar_is_not_a_second_attempt() {
    let temp = tempfile::tempdir().unwrap();
    let traj = temp.path().join("traj");
    std::fs::create_dir_all(&traj).unwrap();
    let body = r#"{"messages":[
        {"role":"assistant","extra":{"response":{"usage":{"prompt_tokens":90000,
         "completion_tokens":1000,"total_tokens":91000}}}}]}"#;
    let attempt = traj.join("planner.attempt1.json");
    std::fs::write(&attempt, body).unwrap();
    std::fs::write(traj.join("planner.attempt1.redacted.json"), body).unwrap();

    let single = extract_usage(&attempt, Role::Planner, 1).unwrap();
    assert!(single.calls > 0, "the fixture must carry one usage block");
    let merged = usage_from_attempts(&traj, Role::Planner, 1).unwrap();

    assert_eq!(
        merged.calls, single.calls,
        "the redacted sidecar must not be counted as a second attempt"
    );
    assert_eq!(merged.total_tokens, single.total_tokens);
    let ratio = merged.calls as f64 / single.calls as f64;
    assert_eq!(ratio, 1.0, "with a sidecar the planner ratio must be 1.0");

    // The counter-direction: a genuine second attempt is still merged, so the
    // fix cannot pass by ignoring every file.
    std::fs::write(traj.join("planner.attempt2.json"), body).unwrap();
    let merged = usage_from_attempts(&traj, Role::Planner, 1).unwrap();
    assert_eq!(
        merged.calls,
        single.calls * 2,
        "two real attempts must still be summed"
    );
}

#[test]
fn missing_trajectory_is_an_error() {
    let error = extract_usage(
        std::path::Path::new("tests/fixtures/does_not_exist.json"),
        Role::Planner,
        1,
    )
    .expect_err("a missing trajectory must not silently report zero usage");
    assert!(error.to_string().contains("trajectory"));
}
