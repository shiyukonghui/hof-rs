//! DR-22 — record/log symmetry.
//!
//! The first smoke run had no `logs/planner.log` at all and named the developer
//! trajectory `traj/developer.json`, so a failed round could not be attributed
//! to a single attempt.  Every attempt must now leave exactly one trajectory and
//! one log, both stating the same facts.

mod common;

use std::collections::BTreeSet;

use common::*;
use hof_rs::model::{Ablation, Role};
use serde_json::Value;

fn names(dir: &std::path::Path, suffix: &str) -> BTreeSet<String> {
    std::fs::read_dir(dir)
        .unwrap_or_else(|error| panic!("{dir:?}: {error}"))
        .map(|entry| entry.unwrap().file_name().to_string_lossy().into_owned())
        .filter(|name| name.ends_with(suffix))
        .map(|name| name.trim_end_matches(suffix).to_string())
        .collect()
}

/// Two schema retries on purpose: five attempts in total across three roles.
fn retry_script() -> Vec<FakeStep> {
    vec![
        FakeStep::new(Role::Planner).writing(".hoh/plan.md", BAD_PLAN),
        FakeStep::new(Role::Planner).writing(".hoh/plan.md", OK_PLAN),
        FakeStep::new(Role::Developer).writing("project.godot", "config_version=5\n"),
        FakeStep::new(Role::Tester).writing(".hoh/evidence.json", &bad_evidence()),
        FakeStep::new(Role::Tester)
            .writing(".hoh/evidence/move.json", "{}\n")
            .writing(".hoh/evidence.json", &ok_evidence(1, "")),
    ]
}

#[tokio::test]
async fn every_attempt_has_matching_trajectory_and_log() {
    let temp = tempfile::tempdir().unwrap();
    let root = temp.path();
    let (result, _) = run_scenario(
        root,
        1,
        retry_script(),
        Ablation::default(),
        FakeAdapter::new(),
    )
    .await;
    result.expect("the retried happy path must complete");

    let iter_dir = root.join("runs/run-1/iter-1");
    let traj = names(&iter_dir.join("traj"), ".json");
    let logs = names(&iter_dir.join("logs"), ".log");
    assert_eq!(
        traj, logs,
        "the trajectory and log name sets must correspond one-to-one"
    );
    assert_eq!(
        traj,
        [
            "developer.attempt1",
            "planner.attempt1",
            "planner.attempt2",
            "tester.attempt1",
            "tester.attempt2",
        ]
        .into_iter()
        .map(str::to_string)
        .collect::<BTreeSet<_>>()
    );

    for stem in &traj {
        let log: Value =
            serde_json::from_str(&read(&iter_dir.join(format!("logs/{stem}.log")))).unwrap();
        for key in ["exit_status", "duration_ms", "usage", "artifact_path"] {
            assert!(log.get(key).is_some(), "log {stem} is missing {key}: {log}");
        }
        assert_eq!(
            log["role"].as_str().unwrap(),
            stem.split('.').next().unwrap()
        );

        let trajectory: Value =
            serde_json::from_str(&read(&iter_dir.join(format!("traj/{stem}.json")))).unwrap();
        let hoh = trajectory
            .get("hoh")
            .unwrap_or_else(|| panic!("trajectory {stem} has no hoh block: {trajectory}"));
        for key in ["exit_status", "duration_ms", "usage", "artifact_path"] {
            assert!(
                hoh.get(key).is_some(),
                "trajectory {stem} is missing hoh.{key}"
            );
        }
    }
}

#[tokio::test]
async fn usage_json_details_every_attempt_and_keeps_the_summary() {
    let temp = tempfile::tempdir().unwrap();
    let root = temp.path();
    let (result, _) = run_scenario(
        root,
        1,
        retry_script(),
        Ablation::default(),
        FakeAdapter::new(),
    )
    .await;
    result.expect("the retried happy path must complete");

    let iter_dir = root.join("runs/run-1/iter-1");
    let usage: Value = serde_json::from_str(&read(&iter_dir.join("usage.json"))).unwrap();

    let summary = usage["summary"]
        .as_array()
        .unwrap_or_else(|| panic!("usage.json must keep the per-role summary: {usage}"));
    assert_eq!(summary.len(), 3, "one summary entry per role");
    assert_eq!(summary[0]["role"], serde_json::json!("planner"));

    let attempts = usage["attempts"]
        .as_array()
        .unwrap_or_else(|| panic!("usage.json must detail every attempt: {usage}"));
    let pairs: BTreeSet<(String, u64)> = attempts
        .iter()
        .map(|entry| {
            (
                entry["role"].as_str().unwrap().to_string(),
                entry["attempt"].as_u64().unwrap(),
            )
        })
        .collect();
    assert_eq!(
        pairs,
        [
            ("developer".to_string(), 1u64),
            ("planner".to_string(), 1),
            ("planner".to_string(), 2),
            ("tester".to_string(), 1),
            ("tester".to_string(), 2),
        ]
        .into_iter()
        .collect::<BTreeSet<_>>()
    );
    for entry in attempts {
        assert!(entry.get("calls").is_some(), "{entry}");
        assert!(entry.get("exit_status").is_some(), "{entry}");
    }
}

/// `status` must keep reading both the legacy array form and the new object.
#[test]
fn status_reads_both_usage_shapes() {
    let legacy: Value = serde_json::json!([{"role": "planner", "usage_known": true}]);
    let modern: Value = serde_json::json!({"schema": 1, "summary": [{"role": "planner"}]});
    assert_eq!(hof_rs::runtime::usage::usage_summary_of(&legacy).len(), 1);
    assert_eq!(hof_rs::runtime::usage::usage_summary_of(&modern).len(), 1);
    assert!(hof_rs::runtime::usage::usage_summary_of(&serde_json::json!(null)).is_empty());
}
