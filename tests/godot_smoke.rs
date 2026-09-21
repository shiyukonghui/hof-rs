//! E1-E6 -- real-dependency smoke tests.
//!
//! **Every test in this file is `#[ignore]`.**  They require three external
//! preconditions that the offline suite deliberately does not depend on:
//!
//! 1. The `model.base_url` endpoint declared in `config/hoh.yaml` answers
//!    `/chat/completions` with the configured `wire_model_name`, and
//!    `HOH_MODEL_API_KEY` (or `OPENAI_API_KEY`) holds its credential (C5, D6,
//!    DR-14/DR-15/DR-16 — the endpoint and model are configuration, not code).
//! 2. The Godot 4.7 editor has `.workspace/mario` open with the
//!    `godot_mcp_rs` addon enabled, so `http://127.0.0.1:9877/mcp` answers
//!    (C3/C4).
//! 3. The HoH workspace exists and is writable.
//!
//! Run them explicitly:
//!
//! ```text
//! cargo test --test godot_smoke -- --ignored --test-threads=1
//! ```
//!
//! `e1_...` performs the real run and materializes `runs/godot-smoke/`; the
//! other tests analyze that run's artifacts.
//!
//! **DR-9:** a missing precondition is a *failure*, never a silent skip.
//!
//! Two gates, both hard panics:
//! 1. every test requires `HOH_SMOKE=1`; without it the whole `--ignored` run
//!    fails immediately instead of reporting a green "0 assertions" suite;
//! 2. E2-E6 additionally require the real run artifact and print its path when
//!    it is missing.
//!
//! Real invocation:
//!
//! ```text
//! set HOH_SMOKE=1   # then:
//! cargo test --test godot_smoke -- --ignored --test-threads=1
//! ```
//!
//! A reviewer who runs the command above *without* the environment variable (or
//! without the run artifacts) must see failures, never `passed`.

use std::path::PathBuf;

use hof_rs::adapter::{GodotAdapter, ProjectAdapter};
use hof_rs::config::{load_config, load_spec};
use hof_rs::harness::MiniHarness;
use hof_rs::runtime::policy::{hash_tree, HashExcludes};
use hof_rs::runtime::run_loop::{self, Orchestrator};
use hof_rs::tools::bridge::channel_for;

const SMOKE_RUN_ID: &str = "godot-smoke";

/// DR-9 gate 1: these tests drive real external services (the configured model
/// endpoint, the Godot editor).  Running them by accident — or expecting them
/// to "skip" — must fail loudly rather than pass vacuously.
fn require_smoke_mode() {
    if std::env::var("HOH_SMOKE").ok().as_deref() != Some("1") {
        panic!(
            "SMOKE PRECONDITION MISSING: HOH_SMOKE=1 is not set. These tests drive the model \
             endpoint declared in config/hoh.yaml (with HOH_MODEL_API_KEY / OPENAI_API_KEY set) \
             and the Godot editor MCP endpoint (127.0.0.1:9877); set HOH_SMOKE=1 explicitly when \
             you really intend to run them."
        );
    }
}

fn manifest_dir() -> PathBuf {
    PathBuf::from(env!("CARGO_MANIFEST_DIR"))
}

fn smoke_run_dir() -> PathBuf {
    manifest_dir().join("runs").join(SMOKE_RUN_ID)
}

struct Smoke {
    run_dir: PathBuf,
    workspace: PathBuf,
}

/// Load the real configuration with the workspace pinned to the repo.
fn smoke_config() -> hof_rs::config::HohConfig {
    let specs = vec![
        "config/hoh.yaml".to_string(),
        format!(
            "runtime.workspace={}",
            manifest_dir().join(".workspace/mario").display()
        ),
        format!(
            "runtime.spec={}",
            manifest_dir().join(".spec/hof-rs/PRD-mario.md").display()
        ),
        format!("runtime.runs_dir={}", manifest_dir().join("runs").display()),
        "runtime.iterations=1".to_string(),
    ];
    load_config(&specs).expect("config/hoh.yaml must load")
}

/// E0: scaffold the `A0` starting artifact at `.workspace/mario`.
///
/// This one needs neither LM Studio nor the editor: it only materializes the
/// minimal Godot project plus the `godot_mcp_rs` addon skeleton (OPEN-4).
///
/// DR-9: `force_init` is deliberately **not** passed -- it would destroy
/// existing work.  Instead this test asserts the property that makes
/// `force_init` unnecessary: `initialize` is idempotent on an already
/// initialized workspace.
#[test]
#[ignore]
fn e0_initialize_workspace() {
    require_smoke_mode();
    let config = smoke_config();
    let workspace = config.runtime.workspace.clone();
    let adapter = GodotAdapter::new(config.adapter.godot.clone(), false);

    adapter
        .initialize(&workspace)
        .expect("scaffolding A0 must succeed without --force-init");
    let project = workspace.join("project.godot");
    assert!(project.is_file(), "{} is missing", project.display());
    let first = std::fs::read_to_string(&project).expect("project.godot");
    assert_eq!(
        first
            .matches("res://addons/godot_mcp_rs/plugin.cfg")
            .count(),
        1,
        "the MCP plugin must be enabled exactly once (DR-4)"
    );

    // Second call: a no-op.  Same bytes, nothing added twice.
    adapter
        .initialize(&workspace)
        .expect("initialize must be idempotent");
    let second = std::fs::read_to_string(&project).expect("project.godot");
    assert_eq!(
        first, second,
        "a second initialize must not modify project.godot"
    );
}

/// E1: one real Planner -> Developer -> QA loop.
#[tokio::test]
#[ignore]
async fn e1_single_iteration_smoke() {
    require_smoke_mode();
    let config = smoke_config();
    let workspace = config.runtime.workspace.clone();
    let spec = load_spec(&config.runtime.spec).expect("spec");
    let adapter = GodotAdapter::new(config.adapter.godot.clone(), false);
    let tools = std::sync::Arc::new(channel_for(&config));

    let run_dir = config.runtime.runs_dir.join(SMOKE_RUN_ID);
    assert!(
        !run_dir.exists(),
        "{} already exists; delete it to re-run the smoke test",
        run_dir.display()
    );

    let orchestrator = Orchestrator {
        harness: Box::new(MiniHarness::new()),
        adapter: Box::new(adapter),
        tools,
        cfg: config,
        ablation: hof_rs::model::Ablation::default(),
        force_init: false,
        start_state: hof_rs::runtime::start_state::StartState::as_is(),
    };
    let summary = run_loop::run(&orchestrator, &spec, SMOKE_RUN_ID)
        .await
        .expect("the real run must complete");

    assert_eq!(summary.iterations_completed, 1);
    assert!(summary.ok);

    for name in ["plan.md", "evidence.json", "qa_report.md", "result.json"] {
        assert!(
            run_dir.join("iter-1").join(name).is_file(),
            "missing {name}"
        );
    }
    assert!(run_dir.join("meta.json").is_file());
    let _ = workspace;
}

/// Shared preconditions for E2-E6.
///
/// DR-9: a missing run artifact must **panic**, printing the path it needs.
/// Returning early here is what produced five green "tests" that asserted
/// nothing.
fn smoke() -> Smoke {
    require_smoke_mode();
    let config = smoke_config();
    let run_dir = smoke_run_dir();
    let evidence = run_dir.join("iter-1/evidence.json");
    if !evidence.is_file() {
        panic!(
            "SMOKE PRECONDITION MISSING: {} does not exist. Run the real loop first with \
             `cargo test --test godot_smoke -- --ignored e1_single_iteration_smoke`, which \
             requires the configured model endpoint (plus HOH_MODEL_API_KEY / OPENAI_API_KEY) \
             and the Godot editor with the godot_mcp_rs addon listening on 127.0.0.1:9877.",
            evidence.display()
        );
    }
    Smoke {
        run_dir,
        workspace: config.runtime.workspace,
    }
}

fn iter_dir(smoke: &Smoke) -> PathBuf {
    smoke.run_dir.join("iter-1")
}

fn evidence(smoke: &Smoke) -> serde_json::Value {
    let raw = std::fs::read_to_string(iter_dir(smoke).join("evidence.json")).expect("evidence");
    serde_json::from_str(&raw).expect("evidence json")
}

fn deterministic_observations(smoke: &Smoke) -> String {
    let dir = iter_dir(smoke).join("candidate/.hoh/deterministic");
    let mut text = String::new();
    if let Ok(entries) = std::fs::read_dir(dir) {
        for entry in entries.flatten() {
            text.push_str(&std::fs::read_to_string(entry.path()).unwrap_or_default());
            text.push('\n');
        }
    }
    text
}

/// E2: the produced project starts -- `play_scene` succeeded and the editor
/// reported no script errors.
#[test]
#[ignore]
fn e2_project_boots() {
    let smoke = smoke();
    let observations = deterministic_observations(&smoke);
    assert!(
        !observations.is_empty(),
        "no deterministic build records were produced"
    );
    assert!(
        observations.contains("editor has no errors"),
        "the editor reported errors: {observations}"
    );
    assert!(
        observations.contains("main scene booted"),
        "play_scene did not boot the main scene: {observations}"
    );
}

/// E3: player-facing behaviour is evidenced -- at least three public execution
/// records and at least one verified claim.
#[test]
#[ignore]
fn e3_behaviour_is_evidenced() {
    let smoke = smoke();
    let bundle = evidence(&smoke);
    let mut records = 0usize;
    for list in ["verified_records", "gap_records"] {
        for claim in bundle[list].as_array().cloned().unwrap_or_default() {
            records += claim["execution_records"]
                .as_array()
                .map(Vec::len)
                .unwrap_or(0);
        }
    }
    assert!(
        records >= 3,
        "expected at least 3 public execution records, found {records}"
    );
    assert!(
        !bundle["verified_records"]
            .as_array()
            .cloned()
            .unwrap_or_default()
            .is_empty(),
        "no claim was verified in the real run"
    );
}

/// E4: every verified claim points at a public record that really exists.
#[test]
#[ignore]
fn e4_verified_claims_are_reproducible() {
    let smoke = smoke();
    let bundle = evidence(&smoke);
    let candidate = iter_dir(&smoke).join("candidate");
    let root = candidate
        .canonicalize()
        .expect("the candidate view must exist");
    for claim in bundle["verified_records"]
        .as_array()
        .cloned()
        .unwrap_or_default()
    {
        let records = claim["execution_records"]
            .as_array()
            .cloned()
            .unwrap_or_default();
        assert!(
            !records.is_empty(),
            "verified claim {} has no execution records",
            claim["claim_id"]
        );
        for record in records {
            let path = record["path"].as_str().unwrap_or("");
            assert!(
                !path.is_empty(),
                "verified claim {} cites a record without a path",
                claim["claim_id"]
            );
            // DR-10: never `candidate.join(path)` naively -- an absolute path or
            // a `..` component would silently resolve outside the view.
            let normalized = path.replace('\\', "/");
            assert!(
                !normalized.starts_with('/')
                    && !normalized
                        .as_bytes()
                        .get(1)
                        .map(|byte| *byte == b':')
                        .unwrap_or(false),
                "verified claim {} cites the absolute path {path}",
                claim["claim_id"]
            );
            assert!(
                !normalized.split('/').any(|component| component == ".."),
                "verified claim {} cites the escaping path {path}",
                claim["claim_id"]
            );
            let resolved = candidate.join(&normalized);
            assert!(
                resolved.is_file(),
                "verified claim {} cites the missing record {path}",
                claim["claim_id"]
            );
            let target = resolved
                .canonicalize()
                .expect("the cited record must be canonicalizable");
            assert!(
                target.starts_with(&root),
                "verified claim {} cites {path}, which resolves outside the candidate view",
                claim["claim_id"]
            );
        }
    }
}

/// E5: QA did not modify A_1 -- the workspace still hashes to the candidate id.
#[test]
#[ignore]
fn e5_qa_did_not_modify_the_artifact() {
    let smoke = smoke();
    let result: serde_json::Value = serde_json::from_str(
        &std::fs::read_to_string(iter_dir(&smoke).join("result.json")).expect("result.json"),
    )
    .expect("result json");
    assert_eq!(result["ok"], serde_json::json!(true));
    let candidate_id = result["candidate_id"].as_str().expect("candidate id");
    let excludes = HashExcludes::new([".godot", ".import"]).merged();
    let current = hash_tree(&smoke.workspace, &excludes).expect("hash");
    assert_eq!(
        current, candidate_id,
        "the workspace changed after QA; the candidate was not frozen"
    );
}

/// E6: honest reporting -- gaps carry guidance, and verified claims never appear
/// without visible support.
#[test]
#[ignore]
fn e6_report_is_honest() {
    let smoke = smoke();
    let bundle = evidence(&smoke);
    for claim in bundle["gap_records"]
        .as_array()
        .cloned()
        .unwrap_or_default()
    {
        assert!(
            claim["player_impact"]
                .as_str()
                .map(str::trim)
                .is_some_and(|value| !value.is_empty()),
            "gap {} has no player_impact",
            claim["claim_id"]
        );
        assert!(
            claim["recommended_update"]
                .as_str()
                .map(str::trim)
                .is_some_and(|value| !value.is_empty()),
            "gap {} has no recommended_update",
            claim["claim_id"]
        );
    }
    for claim in bundle["verified_records"]
        .as_array()
        .cloned()
        .unwrap_or_default()
    {
        assert_eq!(claim["status"], serde_json::json!("verified"));
        assert!(
            !claim["execution_records"]
                .as_array()
                .cloned()
                .unwrap_or_default()
                .is_empty(),
            "verified claim {} cites no execution record",
            claim["claim_id"]
        );
    }
}
