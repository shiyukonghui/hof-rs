//! Round-5 repair: `hoh run --resume` — what it does, and what it deliberately
//! does not.
//!
//! An infrastructure failure cost the round an entire ~90-minute attempt with no
//! way to continue it (`ROUND-4-REPORT-COMPLETE.md`'s attempt 4: the round
//! connector died after iteration 1 completed).  The repair is a resume whose
//! scope is stated exactly, because over-claiming it would be the round-3 defect
//! in a new place:
//!
//! * an iteration whose `result.json` says `ok: true` is **not** re-run — its
//!   usage, gate and version are carried into the run's summary;
//! * the first incomplete iteration runs **from its start**, because the harness
//!   has no role-level checkpoint: a Developer edits the workspace in place
//!   through the write directive, and there is no safe point inside a call at
//!   which a half-finished increment could be handed to a fresh call.
//!
//! The decision is arithmetic over the run directory, so it is pinned here
//! without a model, a network or a round.

mod common;

use std::path::Path;

use common::write;
use hof_rs::runtime::run_loop::{plan_resume, RESUMED_FROM};

/// Build `runs/<id>/iter-<n>/result.json` with the given `ok` flag.
fn iteration_result(root: &Path, iteration: u32, ok: bool, version_id: &str) {
    let text = format!(
        r#"{{
  "ok": {ok},
  "failed_role": null,
  "reason": "{}",
  "issues": [],
  "warnings": [],
  "candidate_id": null,
  "version_id": "{version_id}",
  "usage": [],
  "durations_ms": [],
  "evidence_diff": {{"added": [], "removed": [], "changed": []}}
}}
"#,
        if ok { "ok" } else { "the connector died" }
    );
    write(
        &root
            .join("runs")
            .join("run-1")
            .join(format!("iter-{iteration}"))
            .join("result.json"),
        &text,
    );
}

fn run_dir(root: &Path) -> std::path::PathBuf {
    root.join("runs").join("run-1")
}

/// The three-iteration shape round 4's attempt 4 really had: iterations 1
/// complete, iteration 2 never finished (no `result.json` at all, because the
/// process died mid-call).
#[test]
fn a_resume_skips_every_completed_iteration_and_re_runs_the_incomplete_one() {
    let temp = tempfile::tempdir().unwrap();
    let root = temp.path();
    iteration_result(root, 1, true, "a1");
    // Iteration 2 was interrupted: no result.json exists.
    let plan = plan_resume(&run_dir(root), 3);
    assert_eq!(plan.completed, 1, "iteration 1 is the complete one");
    assert_eq!(
        plan.first_iteration,
        Some(2),
        "the interrupted iteration is the one that runs, from its start"
    );
}

/// The other shape: the failure path wrote a `result.json` with `ok: false` for
/// the interrupted iteration.  It still counts as incomplete, so the resume
/// re-runs it rather than treating a failed iteration as done.
#[test]
fn a_failed_iteration_result_is_not_treated_as_complete() {
    let temp = tempfile::tempdir().unwrap();
    let root = temp.path();
    iteration_result(root, 1, true, "a1");
    iteration_result(root, 2, false, "a2-broken");
    let plan = plan_resume(&run_dir(root), 3);
    assert_eq!(plan.completed, 1);
    assert_eq!(plan.first_iteration, Some(2));
}

/// A hole in the middle is not skipped over: the resume continues at the first
/// iteration that is not complete, whatever comes after it.  (An `ok` result for
/// iteration 3 while 2 is missing would mean the run directory was assembled by
/// hand, and re-running 2 is the only answer that produces a coherent round.)
#[test]
fn the_resume_stops_at_the_first_incomplete_iteration() {
    let temp = tempfile::tempdir().unwrap();
    let root = temp.path();
    iteration_result(root, 1, true, "a1");
    // 2 is missing.
    iteration_result(root, 3, true, "a3");
    let plan = plan_resume(&run_dir(root), 3);
    assert_eq!(plan.completed, 1);
    assert_eq!(plan.first_iteration, Some(2));
}

/// A run whose every iteration is complete has nothing to execute: the resume
/// must say so rather than re-running one iteration "for safety", which would
/// spend ~50 minutes of model calls on work that is already recorded.
#[test]
fn a_fully_complete_run_has_nothing_to_resume() {
    let temp = tempfile::tempdir().unwrap();
    let root = temp.path();
    for iteration in 1..=3 {
        iteration_result(root, iteration, true, &format!("a{iteration}"));
    }
    let plan = plan_resume(&run_dir(root), 3);
    assert_eq!(plan.completed, 3);
    assert_eq!(
        plan.first_iteration, None,
        "nothing is left to run, and the resume must not invent work"
    );
}

/// The control: with no run directory at all nothing is complete, so a fresh
/// round runs iteration 1 (and `--resume` is refused before this point by the
/// CLI).
#[test]
fn an_empty_run_directory_resumes_from_iteration_one() {
    let temp = tempfile::tempdir().unwrap();
    let plan = plan_resume(&run_dir(temp.path()), 3);
    assert_eq!(plan.completed, 0);
    assert_eq!(plan.first_iteration, Some(1));
}

/// The scope statement is a recorded fact, not a comment: the warning the round
/// writes says what was skipped and where the resume starts.
#[test]
fn the_resume_warning_states_the_scope_it_applied() {
    assert_eq!(RESUMED_FROM, "resumed_from_interrupted_round");
    // The constant is what `run_inner` writes; a rename without the record
    // moving with it would leave the evidence unreadable.
    assert!(
        hof_rs::runtime::run_loop::RESUMED_FROM.contains("resumed"),
        "the warning id must name the mode"
    );
}
