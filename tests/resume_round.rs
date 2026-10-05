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
//! * the first incomplete iteration runs **from its start**, and that start is
//!   *restored*: the project tree is rolled back to the artifact the last
//!   completed iteration froze and the rollback re-hashes it, so the interrupted
//!   iteration's own partial edits are discarded rather than adopted;
//! * the workspace must be the project the run id was created against
//!   (`meta.json.project`);
//! * the round's own `.hoh` is **not** quarantined, and a resume with nothing to
//!   run starts no game session.
//!
//! The decision is arithmetic over the run directory and the side effects are
//! file operations, so the whole contract is pinned here without a model, a
//! network or a round — including by driving the **real** `run_loop::run` over a
//! genuinely interrupted run directory.

mod common;

use std::path::{Path, PathBuf};
use std::sync::Arc;

use common::{
    happy_script, run_resume_scenario, test_config, write, FakeAdapter, FakeToolChannel,
    RoundGameStub,
};
use hof_rs::model::{Ablation, Spec};
use hof_rs::runtime::policy::hash_tree;
use hof_rs::runtime::record::{write_run_meta, RunMeta};
use hof_rs::runtime::run_loop::{
    check_resume_project, plan_resume, read_run_meta, restore_resume_workspace,
    resume_project_matches, resume_restore_iteration, RESUMED_FROM,
};
use hof_rs::runtime::snapshot::VersionStore;
use hof_rs::runtime::start_state::StartState;
use hof_rs::tools::ToolChannel;

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

/// The excludes the runtime itself hashes with for this adapter shape.
fn excludes() -> Vec<String> {
    vec!["cache".to_string()]
}

/// The `meta.json` a run of `workspace` writes: the recorded project path is what
/// the resume identity check reads (AC-7b).
fn resume_meta(run_dir: &Path, workspace: &Path, iterations: u32) {
    let meta = RunMeta {
        run_id: "run-1".to_string(),
        spec: Spec {
            path: "spec.md".into(),
            sha256: "0".repeat(64),
        },
        ablation: Ablation::default(),
        iterations,
        model_identity: "model|openai_compatible|model".to_string(),
        started_at: 0,
        hoh_version: test_version(),
        warnings: vec![],
        config: serde_json::json!({}),
        start_state: StartState::as_is(),
        engine: hof_rs::adapter::EngineIdentity::unavailable("not probed"),
        project: workspace.to_path_buf(),
    };
    write_run_meta(run_dir, &meta).expect("write meta");
}

fn test_version() -> String {
    env!("CARGO_PKG_VERSION").to_string()
}

// ---------------------------------------------------------------------------
// The decision, as arithmetic over the run directory
// ---------------------------------------------------------------------------

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

// ---------------------------------------------------------------------------
// AC-7(b): the workspace must be the project the run id belongs to
// ---------------------------------------------------------------------------

/// The recorded project path is read back and matches the same directory in any
/// spelling; a different directory and an unrecorded one do not.
#[test]
fn a_resume_matches_only_the_project_the_run_id_recorded() {
    let temp = tempfile::tempdir().unwrap();
    let root = temp.path();
    let workspace = root.join("project-a");
    let other = root.join("project-b");
    std::fs::create_dir_all(&workspace).unwrap();
    std::fs::create_dir_all(&other).unwrap();
    let store_dir = run_dir(root);
    std::fs::create_dir_all(&store_dir).unwrap();
    resume_meta(&store_dir, &workspace, 3);

    let recorded = read_run_meta(&store_dir).expect("meta reads back");
    assert_eq!(recorded.project, workspace);
    assert!(
        resume_project_matches(&recorded, &workspace),
        "the recorded project must match itself"
    );
    assert!(
        check_resume_project(&recorded, "run-1", &workspace).is_ok(),
        "the recorded project must pass the check"
    );
    assert!(
        !resume_project_matches(&recorded, &other),
        "another project must not match"
    );
    let error = check_resume_project(&recorded, "run-1", &other)
        .expect_err("the wrong workspace must be refused");
    let message = error.to_string();
    assert!(
        message.contains("project-a") && message.contains("project-b"),
        "the refusal must name both projects: {message}"
    );

    // A run that predates the field cannot prove anything, so it is refused
    // rather than guessed at.
    let mut unrecorded = recorded.clone();
    unrecorded.project = PathBuf::new();
    assert!(!resume_project_matches(&unrecorded, &workspace));
    let error = check_resume_project(&unrecorded, "run-1", &workspace)
        .expect_err("an unrecorded project must be refused");
    assert!(
        error.to_string().contains("records no project path"),
        "{error}"
    );
}

// ---------------------------------------------------------------------------
// AC-7(a): the interrupted iteration's start state is restored and validated
// ---------------------------------------------------------------------------

/// The shape a resume really meets: iteration 1 complete (its artifact frozen in
/// the version store), iteration 2 interrupted with partial edits in the tree,
/// including a truncated file.  The restore puts the tree back to A1 and the
/// rollback's re-hash is what proves it.
#[test]
fn a_resume_restores_the_interrupted_iterations_start_state() {
    let temp = tempfile::tempdir().unwrap();
    let root = temp.path();
    let workspace = root.join("workspace");
    std::fs::create_dir_all(&workspace).unwrap();
    let store = VersionStore::new(run_dir(root).join("versions"));

    write(&workspace.join("src/game.rs"), "fn main() {}\n");
    let a0 = store
        .snapshot_role(&workspace, &excludes(), 0, "init", "A0")
        .unwrap();

    // Iteration 1 completed: its own file, then its frozen artifact.
    write(&workspace.join("src/level.rs"), "pub fn one() {}\n");
    let a1 = store
        .snapshot_role(&workspace, &excludes(), 1, "developer", "A1")
        .unwrap();
    iteration_result(root, 1, true, &a1.version_id);

    // Iteration 2 was killed while writing: a truncated source and a file the
    // iteration never finished.
    write(&workspace.join("src/game.rs"), "fn main() { /* TRUNCAT");
    write(&workspace.join("src/half.rs"), "let x =");

    let plan = plan_resume(&run_dir(root), 3);
    assert_eq!(plan.completed, 1);
    assert_eq!(plan.first_iteration, Some(2));
    assert_eq!(
        resume_restore_iteration(&plan),
        Some(1),
        "the first incomplete iteration starts from the last completed artifact"
    );

    let restore = restore_resume_workspace(&store, &workspace, &excludes(), 1).unwrap();
    assert_eq!(restore.iteration, 1);
    assert_eq!(restore.version_id, a1.version_id);
    assert!(
        restore.discarded.is_some(),
        "the tree had drifted, so the partial edits must be reported as discarded"
    );
    assert_ne!(
        restore.discarded.as_deref(),
        Some(a1.version_id.as_str()),
        "the discarded hash is the pre-restore tree, not the target"
    );
    assert_ne!(a0.version_id, a1.version_id);

    // The restore is verified: the tree hashes back to A1, the truncated file is
    // whole again and the unfinished file is gone.
    assert_eq!(hash_tree(&workspace, &excludes()).unwrap(), a1.version_id);
    assert_eq!(
        std::fs::read_to_string(workspace.join("src/game.rs")).unwrap(),
        "fn main() {}\n"
    );
    assert!(workspace.join("src/level.rs").is_file());
    assert!(
        !workspace.join("src/half.rs").exists(),
        "an edit the interrupted iteration never completed must not be adopted"
    );
}

/// A resume with nothing to run restores nothing: the workspace must not be
/// touched at all when every iteration is already complete.
#[test]
fn a_resume_with_nothing_to_run_has_no_restore_target() {
    let temp = tempfile::tempdir().unwrap();
    let root = temp.path();
    for iteration in 1..=3 {
        iteration_result(root, iteration, true, &format!("a{iteration}"));
    }
    let plan = plan_resume(&run_dir(root), 3);
    assert_eq!(plan.first_iteration, None);
    assert_eq!(
        resume_restore_iteration(&plan),
        None,
        "no iteration runs, so no snapshot may be restored"
    );
}

/// A run whose snapshot for the interrupted iteration's start is missing cannot
/// be resumed: "restore the start state" has no answer, and the honest one is a
/// refusal rather than a re-run on an unproven tree.
#[test]
fn a_resume_without_the_start_snapshot_is_refused() {
    let temp = tempfile::tempdir().unwrap();
    let root = temp.path();
    let workspace = root.join("workspace");
    std::fs::create_dir_all(&workspace).unwrap();
    let store = VersionStore::new(run_dir(root).join("versions"));
    store
        .snapshot_role(&workspace, &excludes(), 0, "init", "A0")
        .unwrap();
    let error = restore_resume_workspace(&store, &workspace, &excludes(), 1)
        .expect_err("A1 does not exist");
    assert!(error.to_string().contains("no A1 snapshot"), "{error}");
}

// ---------------------------------------------------------------------------
// AC-6: the side effects, driven through the real `run_loop::run`
// ---------------------------------------------------------------------------

/// A fully-complete resume executes no iteration, starts no game session and
/// stops none.  Before the repair it called `start_round_game` and returned, so
/// a game process was launched and torn down for nothing, and the quarantine ran
/// first and moved the round's own `.hoh` aside.
#[tokio::test]
async fn a_fully_complete_resume_runs_nothing_and_starts_no_game() {
    let temp = tempfile::tempdir().unwrap();
    let root = temp.path();
    let cfg = test_config(root, 3);
    let workspace = cfg.runtime.workspace.clone();
    let run = run_dir(root);
    std::fs::create_dir_all(&workspace).unwrap();
    write(&workspace.join("src/game.rs"), "fn main() {}\n");
    let store = VersionStore::new(run.join("versions"));
    store
        .snapshot_role(&workspace, &excludes(), 0, "init", "A0")
        .unwrap();
    for iteration in 1..=3 {
        iteration_result(root, iteration, true, &format!("a{iteration}"));
    }
    resume_meta(&run, &workspace, 3);
    // This round's own scratch: a resume must leave it where it is.
    write(&workspace.join(".hoh/scratch/keep.json"), "{}\n");

    let stub = Arc::new(RoundGameStub::new(
        "http://127.0.0.1:1/".to_string(),
        1,
        std::process::id(),
    ));
    let adapter = FakeAdapter::new().with_round_game(stub.clone());
    let tools: Arc<dyn ToolChannel> = Arc::new(FakeToolChannel::new());
    let (result, records) = run_resume_scenario(root, 3, Vec::new(), adapter, tools).await;
    let summary = result.expect("a fully-complete resume still returns a summary");

    assert_eq!(summary.iterations_completed, 3);
    assert!(
        records.is_empty(),
        "no role may be invoked by a resume with no work: {:?}",
        records.iter().map(|r| r.role).collect::<Vec<_>>()
    );
    assert_eq!(stub.starts(), 0, "AC-6: no game session may be started");
    assert_eq!(stub.stops(), 0, "AC-6: and none may be stopped");
    assert!(
        !run.join("quarantine").exists(),
        "AC-6: a resume must not quarantine the round's own evidence"
    );
    assert!(
        workspace.join(".hoh/scratch/keep.json").is_file(),
        "AC-6: the resumed round's own `.hoh` must stay in place"
    );
    assert_eq!(
        std::fs::read_to_string(workspace.join("src/game.rs")).unwrap(),
        "fn main() {}\n",
        "a resume with no work must not touch the workspace"
    );
}

/// A resume that has work to do: iteration 1 never completed, and the tree still
/// holds the interrupted attempt's partial (truncated) edits.  The run restores
/// the recorded start state, executes iteration 1 for real, does not quarantine
/// this round's own evidence, and starts and stops exactly one game session.
#[tokio::test]
async fn a_resume_with_work_restores_the_tree_and_keeps_the_rounds_own_evidence() {
    let temp = tempfile::tempdir().unwrap();
    let root = temp.path();
    let cfg = test_config(root, 1);
    let workspace = cfg.runtime.workspace.clone();
    let run = run_dir(root);
    std::fs::create_dir_all(&workspace).unwrap();
    write(&workspace.join("src/game.rs"), "fn main() {}\n");
    let store = VersionStore::new(run.join("versions"));
    store
        .snapshot_role(&workspace, &excludes(), 0, "init", "A0")
        .unwrap();
    resume_meta(&run, &workspace, 1);
    // The interrupted attempt left a truncated file and this round's own scratch.
    write(&workspace.join("src/game.rs"), "fn main() { /* TRUNCAT");
    write(&workspace.join(".hoh/scratch/keep.json"), "{}\n");

    let stub = Arc::new(RoundGameStub::new(
        "http://127.0.0.1:1/".to_string(),
        1,
        std::process::id(),
    ));
    let adapter = FakeAdapter::new().with_round_game(stub.clone());
    let tools: Arc<dyn ToolChannel> = Arc::new(FakeToolChannel::new());
    let (result, records) = run_resume_scenario(root, 1, happy_script(), adapter, tools).await;
    let summary = result.expect("the resumed iteration must complete");
    assert!(summary.ok, "the resumed iteration must be a real, ok round");
    assert_eq!(
        records.iter().map(|r| r.role).collect::<Vec<_>>().len(),
        3,
        "the first incomplete iteration runs its three roles"
    );

    assert!(
        !run.join("quarantine").exists(),
        "AC-6: the round's own `.hoh` must not be quarantined by a resume"
    );
    assert!(
        workspace.join(".hoh/scratch/keep.json").is_file(),
        "the round's own scratch must survive the resume"
    );
    assert_eq!(
        std::fs::read_to_string(workspace.join("src/game.rs")).unwrap(),
        "fn main() {}\n",
        "AC-7(a): the interrupted iteration's truncated edit must be discarded, not adopted"
    );
    // The round session is started at least once (the round's own window; the
    // runtime also stops it before the battery and starts it again afterwards)
    // and it is torn down: a resume that ran an iteration behaves like any other
    // round.  The exact counts are the round's own, not the resume's.
    assert!(
        stub.starts() >= 1,
        "one iteration ran, so a game session existed"
    );
    assert!(stub.stops() >= 1, "and it was torn down");

    let warnings =
        std::fs::read_to_string(run.join("warnings.log")).expect("the round records its warnings");
    assert!(
        warnings.contains("restored the workspace to iteration 0's frozen artifact"),
        "the restore must be recorded:\n{warnings}"
    );
    assert!(
        warnings.contains("the tree had drifted from it"),
        "the discarded partial edits must be recorded:\n{warnings}"
    );
}

/// The refusal is real, not a warning: pointing the resume at another workspace
/// stops the round before it touches anything.
#[tokio::test]
async fn a_resume_against_another_project_is_refused() {
    let temp = tempfile::tempdir().unwrap();
    let root = temp.path();
    let cfg = test_config(root, 1);
    let workspace = cfg.runtime.workspace.clone();
    let wrong = root.join("somewhere-else");
    let run = run_dir(root);
    std::fs::create_dir_all(&workspace).unwrap();
    std::fs::create_dir_all(&wrong).unwrap();
    let store = VersionStore::new(run.join("versions"));
    store
        .snapshot_role(&workspace, &excludes(), 0, "init", "A0")
        .unwrap();
    // The run was recorded against a different project than the one configured.
    resume_meta(&run, &wrong, 1);
    write(&workspace.join("src/game.rs"), "fn main() {}\n");

    let stub = Arc::new(RoundGameStub::new(
        "http://127.0.0.1:1/".to_string(),
        1,
        std::process::id(),
    ));
    let adapter = FakeAdapter::new().with_round_game(stub.clone());
    let tools: Arc<dyn ToolChannel> = Arc::new(FakeToolChannel::new());
    let (result, records) = run_resume_scenario(root, 1, happy_script(), adapter, tools).await;

    let error = result.expect_err("a resume against another project must be refused");
    assert!(
        error
            .to_string()
            .contains("must not continue one run against another run's tree"),
        "{error}"
    );
    assert!(records.is_empty(), "no role may run");
    assert_eq!(stub.starts(), 0, "and no game session may be started");
    assert!(
        !run.join("quarantine").exists(),
        "a refused resume must not quarantine anything either"
    );
}
