//! Round-1 write-path batch — a role that never wrote its declared artifact is
//! a **first-class fact in the harness**.
//!
//! Round 1's Developer spent 140 model calls, 54.4 minutes and 10.4M prompt
//! tokens and ended with `RepeatedFormatError` — an exit status of the external
//! coding agent that appears nowhere in `src/`.  From the harness's own records
//! a round in which a role never managed to write its artifact therefore could
//! not be told apart from one in which it wrote everything and stopped cleanly.
//!
//! These tests drive the production `run_loop` with a fake harness and pin the
//! harness's own judgement:
//!
//! * a Developer stage that changed nothing, whose call ended with a failure
//!   status, produces a `write_failures` entry in `result.json` **and** a
//!   `role_write_failure:` line in `warnings.log`;
//! * a Developer stage that *did* write produces none, whatever its exit status
//!   was;
//! * the assessment itself is a pure function, so the rules are checkable
//!   without a round.

mod common;

use std::path::Path;

use common::*;
use hof_rs::harness::guard::REPEATED_ACTION_STATUS;
use hof_rs::model::{Ablation, Role};
use hof_rs::runtime::write_failure::{assess, DECLARED_DEVELOPER};
use serde_json::Value;

/// The external agent's status round 1 ended with; it is a string this crate
/// does not define, which is exactly why the harness must judge it itself.
const REPEATED_FORMAT_STATUS: &str = "RepeatedFormatError";

/// A Developer stage that writes only into the hash-excluded scratch directory.
fn scratch_only_developer(status: &str) -> Vec<FakeStep> {
    vec![
        FakeStep::new(Role::Planner).writing(".hoh/plan.md", OK_PLAN),
        FakeStep::new(Role::Developer)
            .writing(".hoh/scratch/experiment.py", "print('probe')\n")
            .exiting(status),
        FakeStep::new(Role::Tester)
            .writing(".hoh/evidence/move.json", "{}\n")
            .writing(".hoh/evidence.json", &ok_evidence(1, "")),
    ]
}

async fn run_scratch_only(root: &Path, status: &str) -> Value {
    let script = scratch_only_developer(status);
    let (_result, _records) = run_scenario(
        root,
        1,
        script,
        Ablation::default(),
        FakeAdapter::new().with_developer_artifact_valid(true),
    )
    .await;
    serde_json::from_str(&read(&root.join("runs/run-1/iter-1/result.json"))).unwrap()
}

/// The round-1 shape, in the harness's own words: the Developer's call ended
/// with an external agent's failure status and the artifact tree did not move.
#[tokio::test]
async fn a_failed_developer_call_that_wrote_nothing_is_recorded_as_a_write_failure() {
    let temp = tempfile::tempdir().unwrap();
    let root = temp.path();
    write(&root.join("workspace/project.godot"), "config_version=5\n");

    let result_json = run_scratch_only(root, "RepeatedFormatError").await;

    let failures = result_json["write_failures"]
        .as_array()
        .unwrap_or_else(|| panic!("`write_failures` must be an array: {result_json}"));
    assert_eq!(
        failures.len(),
        1,
        "the Developer never wrote the project, so exactly one write failure must be recorded: \
         {result_json}"
    );
    let failure = &failures[0];
    assert_eq!(failure["role"], "developer", "{failure}");
    assert_eq!(failure["attempt"], 1, "{failure}");
    assert_eq!(failure["exit_status"], "RepeatedFormatError", "{failure}");
    assert_eq!(failure["artifact_written"], false, "{failure}");
    assert!(
        failure["declared_artifact"]
            .as_str()
            .unwrap_or_default()
            .contains("inside the project"),
        "the record must name the artifact that was not written: {failure}"
    );
    assert!(
        failure["reason"]
            .as_str()
            .unwrap_or_default()
            .contains("RepeatedFormatError"),
        "the reason must quote the status it judged: {failure}"
    );

    // The evidence file carries the same fact, so a reader of the round's
    // `warnings.log` sees it without parsing `result.json`.
    let warnings = read(&root.join("runs/run-1/warnings.log"));
    assert!(
        warnings.contains("role_write_failure:"),
        "the write failure must be in the round's warning log: {warnings}"
    );
    assert!(
        warnings.contains("RepeatedFormatError"),
        "the log line must name the status verbatim: {warnings}"
    );
}

/// Our own fail-fast status is judged exactly like the external agent's: the
/// harness records the fact, not the vocabulary.
#[tokio::test]
async fn our_own_fail_fast_status_produces_the_same_first_class_fact() {
    let temp = tempfile::tempdir().unwrap();
    let root = temp.path();
    write(&root.join("workspace/project.godot"), "config_version=5\n");

    let result_json = run_scratch_only(root, REPEATED_ACTION_STATUS).await;
    let failures = result_json["write_failures"].as_array().expect("an array");
    assert_eq!(failures.len(), 1, "{result_json}");
    assert_eq!(
        failures[0]["exit_status"], REPEATED_ACTION_STATUS,
        "{result_json}"
    );
}

/// Non-vacuity: a Developer that **did** write produces no entry, whatever its
/// exit status was.  Without this, an implementation that always recorded a
/// failure would pass the test above.
#[tokio::test]
async fn a_developer_that_wrote_its_artifact_records_no_failure() {
    let temp = tempfile::tempdir().unwrap();
    let root = temp.path();
    write(&root.join("workspace/project.godot"), "config_version=5\n");
    let script: Vec<FakeStep> = vec![
        FakeStep::new(Role::Planner).writing(".hoh/plan.md", OK_PLAN),
        FakeStep::new(Role::Developer)
            .writing("scripts/player.gd", "extends CharacterBody2D\n")
            .exiting("LimitsExceeded"),
        FakeStep::new(Role::Tester)
            .writing(".hoh/evidence/move.json", "{}\n")
            .writing(".hoh/evidence.json", &ok_evidence(1, "")),
    ];
    let (result, _) = run_scenario(
        root,
        1,
        script,
        Ablation::default(),
        FakeAdapter::new().with_developer_artifact_valid(true),
    )
    .await;
    result.expect("one engineering write keeps the round alive");

    let result_json: Value =
        serde_json::from_str(&read(&root.join("runs/run-1/iter-1/result.json"))).unwrap();
    assert_eq!(
        result_json["write_failures"].as_array().map(Vec::len),
        Some(0),
        "a role that wrote its artifact is never reported, whatever its exit status: {result_json}"
    );
    assert!(
        !read(&root.join("runs/run-1/warnings.log")).contains("role_write_failure:"),
        "and the warning log must stay clean too"
    );
}

/// The assessment is a pure function, so its two rules are pinned without a
/// round: a failure status with no write is a fact, and a status the runtime
/// does not know is never quietly reclassified.
#[test]
fn the_assessment_rules_are_the_harnesss_own() {
    let failure = assess(
        Role::Developer,
        1,
        REPEATED_FORMAT_STATUS,
        false,
        DECLARED_DEVELOPER,
        Some(10_379_180),
        1_500_000,
    )
    .expect("round 1's shape");
    assert_eq!(failure.exit_status, REPEATED_FORMAT_STATUS);

    assert!(
        assess(
            Role::Developer,
            1,
            REPEATED_FORMAT_STATUS,
            true,
            DECLARED_DEVELOPER,
            None,
            1_500_000,
        )
        .is_none(),
        "writing the artifact is the fact under judgement"
    );
    assert!(
        assess(
            Role::Developer,
            1,
            "Submitted",
            false,
            DECLARED_DEVELOPER,
            Some(10),
            1_500_000,
        )
        .is_none(),
        "an unknown status must not be reclassified as a failure"
    );
}
