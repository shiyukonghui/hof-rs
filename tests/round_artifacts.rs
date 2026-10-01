//! DR-73 ③(b) — the round directory must carry the **process** exit code.
//!
//! `TASK-SMOKE-T10-ACCEPTANCE.md` T10A-4 (minor, evidence preservation): the claim
//! "exit code 0, three readings agree" had only **two** readings in the frozen
//! artifacts — `runs/<id>/exit_code` (`30 0A`) and `meta.json.exit_code` (`0`).
//! The third (`console.txt → ROUND_EXIT=0`) came from the report's own wrapper
//! script `scripts/run_round.ps1:14`, which printed it to the **outer** console and
//! was never frozen: the frozen `round/console.txt` is 13 lines of `hoh`'s own
//! stdout and contains no `ROUND_EXIT` at all.  D280(b) therefore put "persist the
//! process exit code itself" in scope.
//!
//! These tests drive the real writer and the real finalisation; they do not need a
//! live round, and they do not invent a second exit-code computation — the artifact
//! is written from the same number `finalize_run` persists.

mod common;

use std::path::Path;

use common::{read, write};
use hof_rs::cli_impl::{
    finalize_run, process_exit_code_for, record_process_exit_code_from_env,
    write_process_exit_code, PROCESS_EXIT_CODE_FILE, RUN_DIR_ENV,
};
use hof_rs::model::{ArtifactGate, PrdCoverage, Usage};
use hof_rs::runtime::run_loop::{failed_run_summary, RunSummary};

/// A run directory with the two artifacts `finalize_run` reads and writes.
fn run_dir_with_meta(root: &Path) -> std::path::PathBuf {
    let run_dir = root.join("runs").join("run-1");
    write(
        &run_dir.join("meta.json"),
        "{\n  \"run_id\": \"run-1\",\n  \"exit_code\": null\n}\n",
    );
    run_dir
}

fn ok_summary() -> RunSummary {
    RunSummary {
        run_id: "run-1".to_string(),
        iterations_completed: 1,
        final_version_id: Some("ed98d1b8".to_string()),
        total_usage: Usage::default(),
        ok: true,
        artifact_gate: ArtifactGate {
            applicable: true,
            launchable: true,
            reasons: Vec::new(),
        },
        prd_coverage: PrdCoverage::default(),
        failure_exit_code: None,
    }
}

/// The recorded artifact is the same `<code>\n` byte shape as
/// `runs/<id>/exit_code`, and the function is idempotent.
#[test]
fn the_process_exit_code_artifact_has_the_same_byte_shape_as_the_round_artifact() {
    let temp = tempfile::tempdir().unwrap();
    let run_dir = run_dir_with_meta(temp.path());

    write_process_exit_code(&run_dir, 0).expect("the artifact must be writable");
    let path = run_dir.join(PROCESS_EXIT_CODE_FILE);
    assert_eq!(
        std::fs::read(&path).unwrap(),
        b"0\n",
        "the process reading must be comparable byte for byte with `exit_code`"
    );

    // Idempotent: a re-run of the same round rewrites the same bytes.
    write_process_exit_code(&run_dir, 0).unwrap();
    assert_eq!(std::fs::read(&path).unwrap(), b"0\n");
    // A non-zero verdict is carried through, not collapsed to a pass.
    write_process_exit_code(&run_dir, 2).unwrap();
    assert_eq!(std::fs::read(&path).unwrap(), b"2\n");
}

/// The three readings of one round's verdict — `exit_code`, `meta.json.exit_code`
/// and the process code — are the same number, from the **same** decision point.
#[test]
fn the_three_exit_code_readings_are_the_same_number() {
    let temp = tempfile::tempdir().unwrap();
    let run_dir = run_dir_with_meta(temp.path());
    let summary = ok_summary();

    let code = process_exit_code_for(&summary);
    let persisted = finalize_run(&run_dir, &summary).expect("the finalisation must succeed");
    assert_eq!(
        code, persisted,
        "the value the process records must be the value `finalize_run` persists"
    );

    // ① the round's own artifact.
    assert_eq!(
        read(&run_dir.join("exit_code")),
        format!("{persisted}\n"),
        "`runs/<id>/exit_code` is the bare number plus a newline"
    );
    // ② the metadata copy.
    let meta: serde_json::Value =
        serde_json::from_str(&read(&run_dir.join("meta.json"))).expect("meta.json parses");
    assert_eq!(
        meta["exit_code"],
        serde_json::json!(persisted),
        "meta.json must carry the same verdict: {meta}"
    );
    // ③ the process reading — written from the code the process is about to
    //    return, which is `code` above.
    write_process_exit_code(&run_dir, code).unwrap();
    let process = read(&run_dir.join(PROCESS_EXIT_CODE_FILE));
    assert_eq!(
        process,
        read(&run_dir.join("exit_code")),
        "the two artifacts must be byte-identical"
    );

    // …and out of order: recording first must not change what `finalize_run`
    // writes, because both go through one computation.
    let temp2 = tempfile::tempdir().unwrap();
    let run_dir2 = run_dir_with_meta(temp2.path());
    write_process_exit_code(&run_dir2, process_exit_code_for(&summary)).unwrap();
    finalize_run(&run_dir2, &summary).unwrap();
    assert_eq!(
        read(&run_dir2.join(PROCESS_EXIT_CODE_FILE)),
        read(&run_dir2.join("exit_code")),
        "order must not matter"
    );
}

/// The `ExitCode` type carries no number, so the process entry point records the
/// reading **in `cli_impl::run`** (where the verdict is computed) against the run
/// directory it exported.  This drives that real function through the environment
/// variable, and asserts the reading equals the artifact already on disk.
#[test]
fn the_process_entry_point_records_the_artifact_from_the_exported_run_directory() {
    let temp = tempfile::tempdir().unwrap();
    let run_dir = run_dir_with_meta(temp.path());
    // A non-zero verdict, so a constant `0` cannot pass.
    let summary = failed_run_summary("run-1", &anyhow::anyhow!("the round failed"));
    let code = finalize_run(&run_dir, &summary).expect("the finalisation must succeed");
    assert_ne!(
        code, 0,
        "the counter-example has to be a failure or the test proves nothing"
    );

    // Nothing is written while the round directory is not being named.
    let previous = std::env::var(RUN_DIR_ENV).ok();
    std::env::remove_var(RUN_DIR_ENV);
    record_process_exit_code_from_env();
    assert!(
        !run_dir.join(PROCESS_EXIT_CODE_FILE).exists(),
        "a process that is not a round must not write a round artifact"
    );

    std::env::set_var(RUN_DIR_ENV, &run_dir);
    record_process_exit_code_from_env();
    // An empty value is not a directory.
    std::env::set_var(RUN_DIR_ENV, "");
    record_process_exit_code_from_env();
    // A directory with no `exit_code` has no verdict to back up.
    let empty = temp.path().join("no-such-run");
    std::fs::create_dir_all(&empty).unwrap();
    std::env::set_var(RUN_DIR_ENV, &empty);
    record_process_exit_code_from_env();

    assert_eq!(
        read(&run_dir.join(PROCESS_EXIT_CODE_FILE)),
        format!("{code}\n"),
        "the exported run directory carries the verdict the round was finalised with"
    );
    assert!(
        !empty.join(PROCESS_EXIT_CODE_FILE).exists(),
        "a run directory without a verdict must stay untouched"
    );

    match previous {
        Some(value) => std::env::set_var(RUN_DIR_ENV, value),
        None => std::env::remove_var(RUN_DIR_ENV),
    }
}

/// The wiring is in the production entry point, and the round exports the
/// directory **before** any role runs (so the reading can never point at a
/// different round).
#[test]
fn the_entry_point_and_the_round_are_wired_to_the_recorder() {
    let source = |relative: &str| {
        std::fs::read_to_string(Path::new(env!("CARGO_MANIFEST_DIR")).join(relative))
            .unwrap_or_else(|error| panic!("{relative}: {error}"))
    };
    // `core.autocrlf = true` means the checkout's line endings are not the
    // committed ones, so the text is normalized before it is matched: a check
    // that only held on one of the two would be a platform-dependent test.
    let main = source("src/main.rs").replace("\r\n", "\n");
    assert!(
        main.contains("hof_rs::cli_impl::record_process_exit_code_from_env();"),
        "src/main.rs must record the process exit code before it returns:\n{main}"
    );
    assert!(
        main.contains("let code = hof_rs::cli::main_entry().await;") && main.contains("    code\n"),
        "the recorded reading must be the code the process returns:\n{main}"
    );

    let run = source("src/cli_impl.rs");
    assert!(
        run.contains("std::env::set_var(RUN_DIR_ENV, &run_dir);"),
        "`run` must export the round directory before the roles are invoked"
    );
    let export = run
        .find("std::env::set_var(RUN_DIR_ENV, &run_dir);")
        .unwrap();
    let first_role = run
        .find("run_round_and_finalize(orchestrator, &spec, &run_id, &run_dir)")
        .expect("the round entry point is called");
    assert!(
        export < first_role,
        "the directory must be exported before the round runs, not after"
    );
}
