//! DR-66 ④ — E1 reachability, and the **false green** that hid its failure.
//!
//! The diagnosis (`TASK-DR64-REPORT.md`, accepted with corrections by
//! `TASK-DR64-ACCEPTANCE.md`) measured the root cause: `smoke-t7`'s round ended
//! with
//!
//! ```text
//! result.json:  ok = true,  failed_role = null,  reason = "ok"
//! runs/smoke-t7/exit_code: 0
//! A_0 == A_1 == fc78d299…   (the Developer produced no project increment)
//! warnings: ["qa_scope: …", "harness_source_read", "no_progress"]
//! ```
//!
//! while `REQUIREMENTS.md:112`'s E1 requires the Developer to produce a Godot
//! project increment.  Nothing boolean turned red: `no_progress` was a
//! `warnings` string, `ok` described "the loop ran to the end", and both the
//! exit code and `artifact_gate.launchable` stayed green.  A green round that
//! cannot go red for this failure class makes every future green worthless.
//!
//! This file pins both halves:
//!
//! 1. the measurement itself — an engineering write **is** visible to
//!    `hash_tree`, and a scratch write is not (so the criterion is reachable and
//!    the exclusion set is the one the runtime actually uses);
//! 2. the automation — a round in exactly `smoke-t7`'s state now reports a
//!    violation, `ok = false` and a non-zero exit code.
//!
//! The exclusion set is **derived from the runtime configuration**
//! (`config/hoh.yaml` → `adapter.godot.cache_excludes`), never hard-coded:
//! otherwise moving a real artifact path into `cache_excludes` — the DR-11
//! failure mode that silently switches off write detection — would leave this
//! test green.

mod common;

use std::path::Path;

use common::*;
use hof_rs::adapter::godot::GodotAdapter;
use hof_rs::adapter::ProjectAdapter;
use hof_rs::config::load_config;
use hof_rs::model::{Ablation, ArtifactGate, ContractViolation, Role};
use hof_rs::runtime::policy::{diff_manifests, hash_tree, tree_manifest, HashExcludes};
use hof_rs::runtime::run_loop::{developer_write_deadline, RunSummary};
use serde_json::{json, Value};

// ---------------------------------------------------------------------------
// The exclusion set the runtime uses, taken from the adapter the runtime uses
// ---------------------------------------------------------------------------

/// `run_loop.rs` builds its excludes exactly this way:
/// `HashExcludes::new(orchestrator.adapter.cache_excludes()).merged()`.
///
/// DR-67 (DEF-7): the source is the **adapter**, not the raw configuration.
/// `GodotAdapter::cache_excludes()` currently returns `.hoh` + `.git` + the
/// configured `cache_excludes`, so both spellings agree today; but an exclusion
/// the adapter hard-codes on top of the configuration would be invisible to a
/// test that reads the configuration directly — and that is exactly the DR-11
/// trap this file exists to catch.
fn configured_excludes() -> Vec<String> {
    let config = load_config(&[]).expect("config/hoh.yaml must load");
    let adapter = GodotAdapter::new(config.adapter.godot.clone(), false);
    HashExcludes::new(adapter.cache_excludes()).merged()
}

#[test]
fn the_runtime_exclude_set_comes_from_the_configuration() {
    let excludes = configured_excludes();
    for required in [".hoh", ".git", ".godot", ".import"] {
        assert!(
            excludes.contains(&required.to_string()),
            "the runtime exclude set must contain `{required}`; got {excludes:?}"
        );
    }
    // The set is built from the adapter's own answer, so both a configuration
    // change and a hard-coded addition inside the adapter change this result.
    // DR-67 (DEF-7).
    let config = load_config(&[]).unwrap();
    assert_eq!(
        config.adapter.godot.cache_excludes,
        vec![".godot".to_string(), ".import".to_string()],
        "the shipped `cache_excludes` changed; the E1 reachability argument depends on it"
    );
    let adapter = GodotAdapter::new(config.adapter.godot.clone(), false);
    assert_eq!(
        adapter.cache_excludes(),
        vec![
            ".hoh".to_string(),
            ".git".to_string(),
            ".godot".to_string(),
            ".import".to_string()
        ],
        "the adapter's exclusion set is what the runtime hashes with; if this grew an \
         exclusion on top of the configuration, `configured_excludes()` must follow it"
    );
    // Non-vacuity of the DEF-7 fix: `configured_excludes()` is not a literal — it
    // really is the adapter's own answer.
    assert_eq!(
        excludes,
        HashExcludes::new(adapter.cache_excludes()).merged(),
        "the test must derive its set from the adapter the runtime uses"
    );

    // Non-vacuity: the entry that makes the criterion reachable is a *project*
    // path and must NOT be excluded.
    for project_path in ["project.godot", "scenes/main.tscn", "scripts/player.gd"] {
        assert!(
            !hof_rs::runtime::policy::is_excluded(project_path, &excludes),
            "`{project_path}` is a real artifact path and must be hashed"
        );
    }
    // And the scratch path the prompts prescribe must be excluded (DR-28).
    assert!(hof_rs::runtime::policy::is_excluded(
        ".hoh/scratch/probe.gd",
        &excludes
    ));
}

// ---------------------------------------------------------------------------
// ① an engineering write moves the digest; a scratch write does not
// ---------------------------------------------------------------------------

fn seed_project(root: &Path) -> anyhow::Result<()> {
    let files: [(&str, &str); 3] = [
        ("project.godot", "config_version=5\n"),
        ("scenes/main.tscn", "[gd_scene format=3]\n"),
        ("scripts/player.gd", "extends CharacterBody2D\n"),
    ];
    for (rel, content) in files {
        let path = root.join(rel);
        std::fs::create_dir_all(path.parent().unwrap())?;
        std::fs::write(path, content)?;
    }
    Ok(())
}

#[test]
fn the_measurement_sees_an_engineering_write_and_ignores_scratch() -> anyhow::Result<()> {
    let temp = tempfile::tempdir()?;
    let workspace = temp.path().join("workspace");
    seed_project(&workspace)?;
    let excludes = configured_excludes();

    let a0 = hash_tree(&workspace, &excludes)?;
    assert_eq!(
        a0,
        hash_tree(&workspace, &excludes)?,
        "hashing the same tree twice must be stable"
    );

    // (a) A real engineering write: one new 5-byte script.
    let before = tree_manifest(&workspace, &excludes)?;
    std::fs::write(workspace.join("scripts/hoh_probe.gd"), "pass\n")?;
    let after = tree_manifest(&workspace, &excludes)?;
    let a1 = hash_tree(&workspace, &excludes)?;
    assert_ne!(
        a1, a0,
        "one new project file must change the artifact identity: E1 is reachable"
    );
    let diff = diff_manifests(&before, &after);
    assert_eq!(
        diff.added,
        vec!["scripts/hoh_probe.gd".to_string()],
        "the file-level difference must name the engineering write"
    );
    assert!(diff.modified.is_empty() && diff.removed.is_empty());

    // (b) A scratch write only: invisible by construction (DR-11/DR-28).
    std::fs::create_dir_all(workspace.join(".hoh/scratch"))?;
    std::fs::write(workspace.join(".hoh/scratch/probe.txt"), "pass\n")?;
    assert_eq!(
        hash_tree(&workspace, &excludes)?,
        a1,
        "`.hoh/**` is hash-excluded: a scratch-only round is a real zero increment"
    );
    Ok(())
}

/// The DR-11 counter-example, both ways: excluding a **real** artifact path
/// really does blind the measurement.  If this ever stops holding, the check
/// above is no longer evidence about the runtime's configuration.
#[test]
fn a_real_artifact_path_in_the_exclude_set_blinds_the_measurement() -> anyhow::Result<()> {
    let temp = tempfile::tempdir()?;
    let workspace = temp.path().join("workspace");
    seed_project(&workspace)?;

    let mut excludes = configured_excludes();
    excludes.push("scripts".to_string());
    let blinded = hash_tree(&workspace, &excludes)?;
    std::fs::write(workspace.join("scripts/hoh_probe.gd"), "pass\n")?;
    assert_eq!(
        hash_tree(&workspace, &excludes)?,
        blinded,
        "with `scripts` excluded the write is invisible - the exact DR-11 trap"
    );
    assert_ne!(
        hash_tree(&workspace, &configured_excludes())?,
        blinded,
        "…while the shipped configuration still sees it"
    );
    Ok(())
}

// ---------------------------------------------------------------------------
// ② a zero-engineering-write round must go red
// ---------------------------------------------------------------------------

/// Exactly `smoke-t7`'s shape: the Developer spends its whole step budget and
/// writes only into the hash-excluded runtime paths.
///
/// The Tester step is present on purpose: with the DR-66 gate removed, the round
/// runs to completion, so this test fails on the assertion it is *about* (`ok`
/// must be false / the exit code must not be 0) rather than on a missing
/// harness step.
fn zero_increment_script() -> Vec<FakeStep> {
    vec![
        FakeStep::new(Role::Planner).writing(".hoh/plan.md", OK_PLAN),
        FakeStep::new(Role::Developer)
            .writing(".hoh/scratch/experiment.py", "print('probe')\n")
            .writing(".hoh/scratch/project.godot.pre_iter1", "config_version=5\n")
            .exiting("LimitsExceeded"),
        FakeStep::new(Role::Tester)
            .writing(".hoh/evidence/move.json", "{}\n")
            .writing(".hoh/evidence.json", &ok_evidence(1, "")),
    ]
}

#[tokio::test]
async fn a_zero_engineering_write_round_fails_instead_of_reporting_ok() {
    let temp = tempfile::tempdir().unwrap();
    let root = temp.path();
    // `smoke-t7`: the workspace's project.godot already exists at A_0.
    write(&root.join("workspace/project.godot"), "config_version=5\n");

    let (result, _records) = run_scenario(
        root,
        1,
        zero_increment_script(),
        Ablation::default(),
        // DR-37: a *valid* artifact keeps the wrap-up retry out of the way, so
        // the round isolates the increment question (its project.godot is
        // launchable) instead of conflating it with the budget-retry rule.
        FakeAdapter::new().with_developer_artifact_valid(true),
    )
    .await;

    // The round must NOT be reported as a success…
    let error = result.expect_err("a zero-increment Developer round must fail the round");
    let typed = hof_rs::errors::as_hof_error(&error)
        .expect("the failure must be a typed HofError, not a harness error");
    assert!(
        matches!(
            typed,
            hof_rs::errors::HofError::Contract {
                violation: ContractViolation::NoEngineeringWrite,
                ..
            }
        ),
        "the violation must be `no_engineering_write`, got {typed:?}"
    );

    // …and `result.json` — the file a launcher reads — must say so.
    let result_path = root.join("runs/run-1/iter-1/result.json");
    let raw = std::fs::read_to_string(&result_path).unwrap_or_else(|error| {
        let mut found = Vec::new();
        for entry in walkdir::WalkDir::new(root.join("runs")) {
            if let Ok(entry) = entry {
                found.push(entry.path().to_string_lossy().into_owned());
            }
        }
        panic!(
            "could not read {}: {error}; under runs/: {found:?}",
            result_path.display()
        )
    });
    let result_json: Value = serde_json::from_str(&raw).unwrap();
    assert_eq!(
        result_json["ok"],
        json!(false),
        "`ok` must be false for an E1-class failure: {result_json}"
    );
    assert_eq!(
        result_json["failed_role"],
        json!("developer"),
        "the developer stage is what failed: {result_json}"
    );
    assert!(
        result_json["warnings"]
            .as_array()
            .unwrap()
            .iter()
            .any(|warning| warning == "no_engineering_write"),
        "the independent violation code must be recorded: {result_json}"
    );
    // The old, description-only warning still describes the same measurement —
    // it is no longer the only trace of it.
    assert!(
        result_json["warnings"]
            .as_array()
            .unwrap()
            .iter()
            .any(|warning| warning == "no_progress"),
        "the measurement description must survive: {result_json}"
    );

    // DR-68 ⑦: a failed round evaluated no artifact gate at all, so the gate
    // must be honestly *not applicable* — and a not-applicable gate must not
    // say `launchable = true`.  `smoke-t8`'s failed round carried exactly that
    // combination, so a reader that only looked at `launchable` read a failure
    // as a pass.
    assert_eq!(
        result_json["artifact_gate"]["applicable"],
        json!(false),
        "no gate was evaluated for this round: {result_json}"
    );
    assert_eq!(
        result_json["artifact_gate"]["launchable"],
        json!(false),
        "DR-68 ⑦: a failed round must not report a launchable gate: {result_json}"
    );

    // DR-67 (DEF-2): the two persisted locations must be written by the
    // **production failure path**, from the round's own error — not by a
    // `RunSummary` this test builds for itself.  First prove the round really
    // stopped before the finaliser (so the assertions below cannot pass because
    // something else already wrote these files)…
    assert!(
        !root.join("runs/run-1/exit_code").exists(),
        "the failed round must not have an exit code yet: that is the DEF-2 gap"
    );
    let meta_before: Value =
        serde_json::from_str(&read(&root.join("runs/run-1/meta.json"))).unwrap();
    assert!(
        meta_before.get("exit_code").is_none(),
        "the failed round's meta.json must not carry an exit code yet: {meta_before}"
    );

    // …then apply the production failure finalisation, in the same order and
    // with the same two production functions `cli_impl::run`'s error branch
    // calls, on the real error object:
    //
    //     let failed = run_loop::failed_run_summary(&run_id, &error);
    //     let _ = finalize_run(&run_dir, &failed);
    //
    // This test cannot call `cli_impl::run` itself (its mandatory doctor pre-check
    // performs a model/chat probe, which this offline batch may not do), so the
    // plant that breaks either production function turns the assertions below red.
    let summary = hof_rs::runtime::run_loop::failed_run_summary("run-1", &error);
    assert!(!summary.ok, "the failed summary must not claim success");
    let code = hof_rs::cli_impl::finalize_run(&root.join("runs/run-1"), &summary).unwrap();
    assert_ne!(code, 0, "a failed round must not exit 0");
    assert_eq!(
        code,
        hof_rs::errors::exit_code_of(&error),
        "the persisted code must be the real error's class, not a literal"
    );
    assert_eq!(
        code,
        hof_rs::errors::HofError::contract(ContractViolation::NoEngineeringWrite).exit_code(),
        "the round exit code must be the contract-violation class"
    );
    assert_eq!(
        read(&root.join("runs/run-1/exit_code")).trim(),
        code.to_string(),
        "`runs/<id>/exit_code` must carry the round's code"
    );
    let meta: Value = serde_json::from_str(&read(&root.join("runs/run-1/meta.json"))).unwrap();
    assert_eq!(meta["exit_code"], json!(code));
    // DR-68 ⑦: the production finaliser writes the same honest gate into
    // `meta.json` — `smoke-t8`'s failure persisted `launchable = true` there.
    assert_eq!(
        meta["artifact_gate"]["launchable"],
        json!(false),
        "the failed round's meta.json must not advertise a launchable gate: {meta}"
    );
}

/// DR-67 (DEF-2): the code of a failed round must come from the **real error**,
/// through the same production functions the dispatcher's error branch calls,
/// and must reach both persisted locations.
///
/// The contract-class error cannot distinguish "carried from the error" from
/// "re-derived by the `!ok` branch", because both are `2` — so this also drives
/// an error of a **different class**, whose `4` no constant in that branch could
/// produce.
#[test]
fn a_failed_round_persists_the_real_errors_class() {
    let temp = tempfile::tempdir().unwrap();
    let root = temp.path();
    let run_dir = root.join("runs/run-1");
    std::fs::create_dir_all(&run_dir).unwrap();
    std::fs::write(run_dir.join("meta.json"), r#"{"run_id":"run-1"}"#).unwrap();

    // (1) The contract class the E1 failure uses.
    let error: anyhow::Error =
        hof_rs::errors::HofError::contract(ContractViolation::NoEngineeringWrite).into();
    let summary = hof_rs::runtime::run_loop::failed_run_summary("run-1", &error);
    assert_eq!(
        summary.failure_exit_code,
        Some(hof_rs::errors::exit_code_of(&error)),
        "the summary must carry the code of the error it was built from"
    );
    let code = hof_rs::cli_impl::finalize_run(&run_dir, &summary).unwrap();
    assert_eq!(code, 2, "contract violations are class 2");
    assert_eq!(read(&run_dir.join("exit_code")).trim(), "2");

    // (2) A class the `!ok` branch cannot produce on its own.
    let external: anyhow::Error = hof_rs::errors::HofError::External("endpoint down".into()).into();
    let summary = hof_rs::runtime::run_loop::failed_run_summary("run-1", &external);
    let code = hof_rs::cli_impl::finalize_run(&run_dir, &summary).unwrap();
    assert_eq!(
        code, 4,
        "an external failure is class 4: the code must follow the error, not a literal"
    );
    assert_eq!(
        read(&run_dir.join("exit_code")).trim(),
        "4",
        "the persisted code must be the real error's class"
    );
    let meta: Value = serde_json::from_str(&read(&run_dir.join("meta.json"))).unwrap();
    assert_eq!(meta["exit_code"], json!(4));
}

/// A `RunSummary` with `ok = false` and a *launchable* artifact gate: the exact
/// combination `smoke-t7` produced, and the reason the artifact axis alone
/// cannot express the failure.
///
/// DR-67: kept as a gate-level control (it is also the shape
/// `run_exit_code_for`'s `!ok` branch describes), but the end-to-end assertions
/// above no longer use it — they go through `failed_run_summary` on a real error.
fn failed_summary() -> RunSummary {
    RunSummary {
        run_id: "run-1".to_string(),
        iterations_completed: 0,
        final_version_id: None,
        total_usage: hof_rs::model::Usage::default(),
        ok: false,
        artifact_gate: ArtifactGate {
            applicable: true,
            launchable: true,
            reasons: Vec::new(),
        },
        prd_coverage: hof_rs::model::PrdCoverage::default(),
        failure_exit_code: None,
    }
}

/// DR-67 (DEF-2): `cli_impl::run_round_in` is the half of the dispatcher that
/// still runs the loop — the half whose error the caller finalises.
///
/// Not a tautology: it builds a real `Orchestrator`, runs a **successful** round
/// through the function, and asserts the artifacts the loop writes exist.  A
/// function that merely returned an error would fail the first assertion, and one
/// that did nothing at all would fail all three.
#[tokio::test]
async fn run_round_in_still_runs_the_loop() {
    use std::sync::Arc;

    let temp = tempfile::tempdir().unwrap();
    let root = temp.path();
    let mut cfg = test_config(root, 1);
    cfg.runtime.spec = root.join("spec.md");
    let spec = write_spec(root);
    let orchestrator = hof_rs::runtime::run_loop::Orchestrator {
        harness: Box::new(FakeHarness::new(happy_script())),
        adapter: Box::new(FakeAdapter::new().with_developer_artifact_valid(true)),
        tools: Arc::new(FakeToolChannel::new()),
        cfg,
        ablation: Ablation::default(),
        force_init: true,
        start_state: hof_rs::runtime::start_state::StartState::as_is(),
    };
    let summary = hof_rs::cli_impl::run_round_in(orchestrator, &spec, "run-1")
        .await
        .expect("a happy round must complete through the dispatcher's round half");
    assert_eq!(
        summary.iterations_completed, 1,
        "the summary must describe the round that ran"
    );
    assert!(
        root.join("runs/run-1/iter-1/result.json").is_file(),
        "the loop's own per-iteration record must exist"
    );
}

/// The control: the artifact axis is unchanged, so the new code cannot be read
/// as "the gate now reports failures it never saw".
#[test]
fn a_launchable_artifact_still_exits_zero_when_the_round_succeeded() {
    let mut summary = failed_summary();
    summary.ok = true;
    assert_eq!(hof_rs::cli_impl::run_exit_code_for(&summary), 0);
    summary.artifact_gate.launchable = false;
    assert_eq!(hof_rs::cli_impl::run_exit_code_for(&summary), 6);
    summary.ok = false;
    assert_eq!(
        hof_rs::cli_impl::run_exit_code_for(&summary),
        hof_rs::errors::HofError::contract(ContractViolation::NoEngineeringWrite).exit_code()
    );
}

// ---------------------------------------------------------------------------
// ②b DEF-3 — the gate must not depend on *why* the Developer stopped
// ---------------------------------------------------------------------------

/// The residual false green DR-66 left behind, now closed.
///
/// DR-66 narrowed the gate to "zero increment **and** the Developer's last
/// attempt ended with `LimitsExceeded`", and justified the narrowing with
/// "any zero increment would collide with the existing offline fixtures".  The
/// independent acceptance disproved that reason: of the **32**
/// `FakeStep::new(Role::Developer)` blocks under `tests/**`, the only one whose
/// every write lands under `.hoh/**` is this file's own zero-increment fixture
/// (`devsteps2.py`, DR-67 §3).  With the reason gone, so is the narrowing: a
/// Developer stage that touched nothing in the project is the same *measurement*
/// however it ended, and reporting it green is the failure class E1 is about.
///
/// This fixture differs from `zero_increment_script()` in exactly one way: the
/// Developer **finishes normally** (`Submitted`, the `FakeStep` default) instead
/// of exhausting its budget.
fn zero_increment_script_that_finishes_normally() -> Vec<FakeStep> {
    vec![
        FakeStep::new(Role::Planner).writing(".hoh/plan.md", OK_PLAN),
        FakeStep::new(Role::Developer)
            .writing(".hoh/scratch/experiment.py", "print('probe')\n")
            .writing(".hoh/scratch/project.godot.pre_iter1", "config_version=5\n"),
        FakeStep::new(Role::Tester)
            .writing(".hoh/evidence/move.json", "{}\n")
            .writing(".hoh/evidence.json", &ok_evidence(1, "")),
    ]
}

#[tokio::test]
async fn a_zero_increment_round_that_finishes_normally_also_fails() {
    let temp = tempfile::tempdir().unwrap();
    let root = temp.path();
    write(&root.join("workspace/project.godot"), "config_version=5\n");

    let (result, _records) = run_scenario(
        root,
        1,
        zero_increment_script_that_finishes_normally(),
        Ablation::default(),
        FakeAdapter::new().with_developer_artifact_valid(true),
    )
    .await;

    // The fixture really is the "finished normally" shape: the recorded attempt
    // says so (`exit_was_limits = false`, `exit_status = "Submitted"`), so this
    // test cannot pass merely by re-exercising the smoke-t7 fixture.
    let attempt: Value = serde_json::from_str(&read(
        &root.join("runs/run-1/iter-1/logs/developer.attempt1.log"),
    ))
    .unwrap();
    assert_eq!(attempt["exit_was_limits"], json!(false), "{attempt}");
    assert_eq!(attempt["exit_status"], json!("Submitted"), "{attempt}");

    // …and the round is still a contract violation, not a green run.
    let error = result
        .expect_err("a zero-increment Developer round must fail whatever its exit status was");
    let typed = hof_rs::errors::as_hof_error(&error)
        .expect("the failure must be a typed HofError, not a harness error");
    assert!(
        matches!(
            typed,
            hof_rs::errors::HofError::Contract {
                violation: ContractViolation::NoEngineeringWrite,
                ..
            }
        ),
        "the violation must be `no_engineering_write`, got {typed:?}"
    );

    let result_json: Value =
        serde_json::from_str(&read(&root.join("runs/run-1/iter-1/result.json"))).unwrap();
    assert_eq!(result_json["ok"], json!(false), "{result_json}");
    assert!(
        result_json["warnings"]
            .as_array()
            .unwrap()
            .iter()
            .any(|warning| warning == "no_engineering_write"),
        "the violation code must be recorded: {result_json}"
    );
}

/// The gate's own explanation must describe what the gate checks (DEF-5).
///
/// The DR-66 wording claimed the trigger was "inside the first K steps" while
/// `developer_write_deadline` was never compared against anything at run time.
/// The delivered prompt may still *state the requirement* (a prompt is an
/// instruction, and a rigid step-counter would false-positive on an agent that
/// starts writing at step 26), but no runtime message may claim a check that
/// does not exist.
#[test]
fn the_gate_message_describes_the_condition_the_gate_checks() {
    let source = std::fs::read_to_string(concat!(
        env!("CARGO_MANIFEST_DIR"),
        "/src/runtime/run_loop.rs"
    ))
    .expect("the runtime source must be readable");
    let marker = "contract violation {} (the developer stage";
    let at = source
        .find(marker)
        .expect("the gate message must still exist; update this test if it moved");
    let message: String = source[at..].chars().take(600).collect();

    assert!(
        !message.contains("step budget") && !message.contains("within the first"),
        "the gate message must not claim a step-budget or K-step check that does not exist:\n{message}"
    );
    assert!(
        message.contains("no file") && message.contains("excluded"),
        "the gate message must describe the zero-increment condition it does check:\n{message}"
    );
}

// ---------------------------------------------------------------------------
// ②c DEF-6 — the prompt's exclusion account must match the runtime's set
// ---------------------------------------------------------------------------

/// The prompt may only promise what the hash actually ignores.
///
/// DR-66's `[budget]` said "`.hoh/**` does not count", but the runtime excludes
/// `.godot` and `.import` as well (`config/hoh.yaml` → `cache_excludes`), so a
/// round that only wrote under `.godot/**` would also be recorded as
/// `no_engineering_write` while the prompt implied otherwise.
#[test]
fn the_prompt_names_every_excluded_path_not_just_the_scratch_dir() {
    let prompt = delivered_prompt(hof_rs::prompts::DEVELOPER_PROMPT);
    for excluded in [".hoh", ".godot", ".import"] {
        assert!(
            prompt.contains(excluded),
            "the prompt must account for the `{excluded}` exclusion it is subject to:\n{prompt}"
        );
    }
    // And the set it names is the set the runtime uses, not an aspirational one.
    let excludes = configured_excludes();
    for excluded in [".hoh", ".godot", ".import"] {
        assert!(
            excludes.contains(&excluded.to_string()),
            "`{excluded}` must really be excluded; got {excludes:?}"
        );
    }
}

// ---------------------------------------------------------------------------
// ③ the deadline the prompt states is the deadline the runtime publishes
// ---------------------------------------------------------------------------

#[test]
fn the_developer_prompt_states_the_write_deadline_the_runtime_computes() {
    let limits = hof_rs::config::AgentLimits::default();
    let deadline = developer_write_deadline(&limits);
    assert_eq!(
        deadline, 25,
        "150 steps / 4 = 37, capped at wrap_up_steps (25): the deadline must sit before wrap-up"
    );
    assert!(
        deadline <= limits.wrap_up_steps,
        "the deadline must sit inside the exploring band, not past wrap-up"
    );
    let rendered = delivered_prompt(hof_rs::prompts::DEVELOPER_PROMPT);
    assert!(
        rendered.contains(&format!("first {deadline} steps")),
        "the delivered prompt must name the deadline the runtime uses:\n{rendered}"
    );
    assert!(
        rendered.contains("no_engineering_write"),
        "the prompt must name the violation code the runtime records"
    );
    assert!(
        !rendered.contains("{{write_deadline_steps}}"),
        "the deadline placeholder must be rendered"
    );
}

// ---------------------------------------------------------------------------
// ④ the de-noised definition of done
// ---------------------------------------------------------------------------

/// DR-66 ③: the completion definition must stop pointing the Developer at the
/// deterministic battery (which runs *after* it, and whose own failures were
/// harness defects) while keeping a real, checkable increment requirement.
#[test]
fn the_completion_definition_keeps_the_increment_and_drops_the_battery_ownership() {
    let prompt = delivered_prompt(hof_rs::prompts::DEVELOPER_PROMPT);
    let lower = prompt.to_lowercase();

    // Still a completion definition, still demanding an increment.
    assert!(lower.contains("definition-of-done") || lower.contains("definition of done"));
    assert!(
        lower.contains("candidate increment"),
        "the increment requirement must stay explicit:\n{prompt}"
    );
    assert!(lower.contains("non-empty"), "an empty file stays forbidden");
    assert!(lower.contains("n1") && lower.contains("n2"));
    assert!(prompt.contains("editor_get_errors") && prompt.contains("editor_play_scene"));
    // The Developer must still prove observability itself, on the live path it
    // can actually reach.
    assert!(prompt.contains("editor_simulate_input_action"));
    // DR-69 ②: **requirement-driven update of this assertion.**  The pre-DR-69
    // form required `running_game_get_node_property_samples` in the Developer's
    // own definition of done — the structurally unreachable channel `smoke-t9`
    // measured (`F-T9-1`), and the contradiction the round's zero increment came
    // from.  The Developer's duty is the *structure* (a named node and a
    // property that changes); driving the running game belongs to the Tester and
    // the deterministic battery.  This is not a loosened assertion: it names the
    // channel that must be absent, and `developer_contract.rs` pins the positive
    // direction (the ordering sentence and the forbidden workarounds).
    assert!(
        !prompt.contains("running_game_get_node_property_samples"),
        "the Developer's definition of done must not point at the game endpoint: {prompt}"
    );

    // …and the battery is now stated as harness-side, not as the role's gate.
    assert!(
        lower.contains("harness-side"),
        "the battery's own defects must be attributed to the harness:\n{prompt}"
    );
    assert!(
        prompt.contains("`.hoh/deterministic/**`"),
        "the prompt must name the battery directory it must not repair"
    );
    let battery_at = lower.find("battery").unwrap_or(0);
    let window: String = lower
        .chars()
        .skip(battery_at.saturating_sub(200))
        .take(600)
        .collect();
    let normalized = lower.split_whitespace().collect::<Vec<_>>().join(" ");
    assert!(
        normalized.contains("runs the battery after your call"),
        "the prompt must say when the battery runs, so 'done' cannot mean 'the battery passed'; \
         window around the first `battery`:\n{window}"
    );
    // The removed sentence pointed at a battery that had not run yet.
    assert!(
        !lower.contains(
            "can be observed from the **deterministic evidence battery that runs after you**"
        ),
        "the impossible completion condition must be gone:\n{prompt}"
    );
}

/// Sanity: the fixtures above really are set up so a normal result would be
/// reported (a wrong harness script would otherwise make the assertions pass
/// for the wrong reason).
#[tokio::test]
async fn the_same_harness_script_reports_ok_when_the_developer_writes() {
    let temp = tempfile::tempdir().unwrap();
    let root = temp.path();
    write(&root.join("workspace/project.godot"), "config_version=5\n");
    let script: Vec<FakeStep> = vec![
        FakeStep::new(Role::Planner).writing(".hoh/plan.md", OK_PLAN),
        FakeStep::new(Role::Developer)
            .writing(".hoh/scratch/experiment.py", "print('probe')\n")
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
    let summary = result.expect("one engineering write must keep the round alive");
    assert!(
        summary.ok,
        "the round completed; only the artifact axis may be closed here"
    );
    let result_json: Value =
        serde_json::from_str(&read(&root.join("runs/run-1/iter-1/result.json"))).unwrap();
    assert_eq!(result_json["ok"], json!(true), "{result_json}");
    let warnings: Vec<String> = result_json["warnings"]
        .as_array()
        .unwrap()
        .iter()
        .map(|warning| warning.as_str().unwrap_or_default().to_string())
        .collect();
    assert!(
        !warnings.contains(&"no_progress".to_string())
            && !warnings.contains(&"no_engineering_write".to_string()),
        "an increment must produce neither the description nor the violation: {warnings:?}"
    );
}
