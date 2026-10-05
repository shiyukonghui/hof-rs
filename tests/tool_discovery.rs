//! DR-26 — tool-schema discoverability, a known-good skeleton, and the
//! anti-exploration discipline.
//!
//! `smoke-t2` spent two thirds of the Developer's 150 steps reading HoH's own
//! `src/**` and the external `godot-mcp-pro` checkout to guess tool arguments,
//! while the Planner submitted ~20 times after its first successful `submit`.
//! The fixes are: a schema-backed `TOOLS.md`, a `PROJECT_MAP.md`, a
//! copy-pasteable skeleton that passes the DR-24 structure check, and prompts
//! that forbid the source-reading detour.

mod common;

use common::*;
use hof_rs::model::{Ablation, Role};
use serde_json::Value;

// ---------------------------------------------------------------------------
// ① TOOLS.md is generated from the real schema
// ---------------------------------------------------------------------------

#[test]
fn tools_markdown_carries_parameter_names_and_types() {
    let schemas = hof_rs::tools::index::embedded_tool_schemas();
    assert!(
        schemas.len() >= 100,
        "the embedded snapshot must be the real tools/list payload"
    );

    let developer = hof_rs::tools::index::render_tools_markdown(Role::Developer, &schemas);
    assert!(
        developer.contains("`running_game_get_node_property_samples`"),
        "{developer}"
    );
    assert!(developer.contains("`node_path`"));
    assert!(developer.contains("`properties`"));
    assert!(
        developer.contains("integer") && developer.contains("string"),
        "parameter types must be rendered"
    );
    assert!(developer.contains("| argument | type | required |"));
    assert!(
        developer.matches("tools call").count() >= 3,
        "at least two complete call examples are required"
    );
    assert!(
        developer.contains("\n## ") && developer.contains("\n### "),
        "the document must be grouped by category with per-tool sections"
    );
}

#[test]
fn tools_markdown_never_leaks_a_tool_the_role_may_not_call() {
    let schemas = hof_rs::tools::index::embedded_tool_schemas();

    let tester = hof_rs::tools::index::render_tools_markdown(Role::Tester, &schemas);
    assert!(tester.contains("### `running_game_get_node_property_samples`"));
    for tool in ["project_edit_script", "editor_add_node"] {
        // A denied tool must not be *listed* for the role.  The claim is about
        // the entry heading (`### \`name\``), not about the raw document text:
        // the four-channel contract's descriptions cross-reference other tools
        // by name (e.g. "use project_edit_script to edit"), and a denial that
        // leaked a description would still not be a callable entry.
        assert!(
            !tester.contains(&format!("### `{tool}`")),
            "a mutating tool must not be listed in the tester's index: {tool}"
        );
    }

    let planner = hof_rs::tools::index::render_tools_markdown(Role::Planner, &schemas);
    for tool in ["project_get_info", "editor_play_scene"] {
        assert!(
            !planner.contains(&format!("### `{tool}`")),
            "the planner owns no MCP tool: {tool}"
        );
    }
}

// ---------------------------------------------------------------------------
// ② PROJECT_MAP.md reaches the Developer with sizes
// ---------------------------------------------------------------------------

#[tokio::test]
async fn project_map_is_injected_into_the_developer_view() {
    let temp = tempfile::tempdir().unwrap();
    let root = temp.path();
    // The map describes the artifact *before* this iteration: seed A0.
    write(
        &root.join("workspace/project.godot"),
        "config_version=5\n\n[application]\n",
    );
    write(
        &root.join("workspace/scripts/player.gd"),
        "extends Node2D\n",
    );
    write(&root.join("workspace/scenes/main.tscn"), "[gd_scene]\n");

    let (result, records) = run_scenario(
        root,
        1,
        happy_script(),
        Ablation::default(),
        FakeAdapter::new(),
    )
    .await;
    result.expect("the happy path must complete");

    let developer = records
        .iter()
        .find(|record| record.role == Role::Developer)
        .expect("developer invocation");
    let map = developer
        .files
        .get(".hoh/PROJECT_MAP.md")
        .expect("PROJECT_MAP.md must be injected into the developer view");
    assert!(map.contains("project.godot"), "{map}");
    assert!(map.contains("bytes"), "sizes must be rendered: {map}");
    assert!(map.contains("scripts/player.gd"), "{map}");
    assert!(map.contains("## Top level"), "{map}");
    assert!(map.contains("## Key files"), "{map}");
    // The map is a developer-only input (the other roles do not need it).
    let tester = records
        .iter()
        .find(|record| record.role == Role::Tester)
        .expect("tester invocation");
    assert!(!tester.files.contains_key(".hoh/PROJECT_MAP.md"));
}

#[test]
fn the_run_directory_caches_the_generated_tool_index() {
    let temp = tempfile::tempdir().unwrap();
    let root = temp.path();
    let mut cfg = test_config(root, 1);
    cfg.runtime.spec = root.join("spec.md");
    let spec = write_spec(root);
    let workspcae_run_dir = cfg.runtime.runs_dir.join("run-1");
    let orchestrator = hof_rs::runtime::run_loop::Orchestrator {
        harness: Box::new(FakeHarness::new(happy_script())),
        adapter: Box::new(FakeAdapter::new()),
        tools: std::sync::Arc::new(FakeToolChannel::new()),
        cfg,
        ablation: Ablation::default(),
        force_init: true,
        start_state: hof_rs::runtime::start_state::StartState::as_is(),
        resume: false,
    };
    tokio::runtime::Runtime::new().unwrap().block_on(async {
        hof_rs::runtime::run_loop::run(&orchestrator, &spec, "run-1")
            .await
            .expect("run");
    });
    let cached = std::fs::read_to_string(workspcae_run_dir.join("TOOLS.md")).expect("TOOLS.md");
    assert!(cached.contains("DR-26"), "{cached}");
}

// ---------------------------------------------------------------------------
// ④ prompts forbid the source-reading detour and repeated submits
// ---------------------------------------------------------------------------

#[test]
fn every_role_prompt_forbids_the_harness_sources() {
    // DR-66: the delivered prompt, not the template — the scratch-directory
    // needle below is a shell variable, so it must be checked in the syntax the
    // role's real shell understands.
    let scratch = hof_rs::runtime::shell::ShellFlavor::HOST.var("HOH_SCRATCH_DIR");
    for (name, prompt) in [
        ("planner", delivered_prompt(hof_rs::prompts::PLANNER_PROMPT)),
        (
            "developer",
            delivered_prompt(hof_rs::prompts::DEVELOPER_PROMPT),
        ),
        ("tester", delivered_prompt(hof_rs::prompts::TESTER_PROMPT)),
    ] {
        for needle in [
            "src/**",
            ".spec/**",
            "tests/**",
            ".git/**",
            "F:\\RustProjects\\**",
            scratch.as_str(),
        ] {
            assert!(
                prompt.contains(needle),
                "{name}.md must forbid/mandate `{needle}`:\n{prompt}"
            );
        }
    }
}

#[test]
fn the_submitting_roles_are_told_one_submit_is_enough() {
    for prompt in [
        hof_rs::prompts::PLANNER_PROMPT,
        hof_rs::prompts::TESTER_PROMPT,
    ] {
        let lower = prompt.to_lowercase();
        assert!(
            lower.contains("do not submit again"),
            "a successful submit must end the phase: {prompt}"
        );
    }
}

// ---------------------------------------------------------------------------
// ⑤ reading a forbidden path is traced as a warning
// ---------------------------------------------------------------------------

#[tokio::test]
async fn reading_harness_sources_is_recorded_as_a_warning() {
    let temp = tempfile::tempdir().unwrap();
    let root = temp.path();
    let script = vec![
        FakeStep::new(Role::Planner)
            .writing(".hoh/plan.md", OK_PLAN)
            .trajectory_mentioning("cat src/config.rs"),
        FakeStep::new(Role::Developer).writing("project.godot", "config_version=5\n"),
        FakeStep::new(Role::Tester)
            .writing(".hoh/evidence/move.json", "{}\n")
            .writing(".hoh/evidence.json", &ok_evidence(1, "")),
    ];
    let (result, _) = run_scenario(root, 1, script, Ablation::default(), FakeAdapter::new()).await;
    result.expect("the warning never fails the round");

    let json: Value =
        serde_json::from_str(&read(&root.join("runs/run-1/iter-1/result.json"))).unwrap();
    let warnings = json["warnings"].as_array().expect("warnings");
    assert!(
        warnings
            .iter()
            .any(|warning| warning == "harness_source_read"),
        "the source read must be traced: {warnings:?}"
    );
}

/// DR-32 ①: the prompt itself lists the forbidden paths ("do not read
/// `src/**`, `.spec/**`, ...").  `smoke-t3` reported `harness_source_read`
/// **unconditionally** because that list was scanned as if it were evidence.
/// A prompt without a read command must stay silent.
#[tokio::test]
async fn a_prompt_that_lists_forbidden_paths_is_not_a_source_read() {
    let temp = tempfile::tempdir().unwrap();
    let root = temp.path();
    let script = vec![
        FakeStep::new(Role::Planner)
            .writing(".hoh/plan.md", OK_PLAN)
            .trajectory_prompt_containing(
                "Never read src/** , src/runtime/run_loop.rs, .spec/** or tests/common/** .",
            ),
        FakeStep::new(Role::Developer)
            .writing("project.godot", "config_version=5\n")
            .trajectory_prompt_containing(
                "Do not read src/adapter/bevy/mod.rs or F:\\RustProjects\\** .",
            ),
        FakeStep::new(Role::Tester)
            .writing(".hoh/evidence/move.json", "{}\n")
            .trajectory_prompt_containing("Stay out of .spec/ and .git/ .")
            .writing(".hoh/evidence.json", &ok_evidence(1, "")),
    ];
    let (result, _) = run_scenario(root, 1, script, Ablation::default(), FakeAdapter::new()).await;
    result.expect("the happy path must complete");

    let json: Value =
        serde_json::from_str(&read(&root.join("runs/run-1/iter-1/result.json"))).unwrap();
    let warnings = json["warnings"].as_array().expect("warnings");
    assert!(
        !warnings
            .iter()
            .any(|warning| warning == "harness_source_read"),
        "a prompt that merely names the forbidden paths is not a source read: {warnings:?}"
    );
}

/// DR-32 ②: a real read command in the action stream — and only that — is the
/// evidence.
#[tokio::test]
async fn only_a_tool_command_that_reads_a_source_is_recorded() {
    let temp = tempfile::tempdir().unwrap();
    let root = temp.path();
    let script = vec![
        FakeStep::new(Role::Planner).writing(".hoh/plan.md", OK_PLAN),
        FakeStep::new(Role::Developer)
            .writing("project.godot", "config_version=5\n")
            .trajectory_prompt_containing("never read src/runtime/**")
            .trajectory_mentioning("grep -n editor_play_scene src/runtime/run_loop.rs"),
        FakeStep::new(Role::Tester)
            .writing(".hoh/evidence/move.json", "{}\n")
            .writing(".hoh/evidence.json", &ok_evidence(1, "")),
    ];
    let (result, _) = run_scenario(root, 1, script, Ablation::default(), FakeAdapter::new()).await;
    result.expect("the happy path must complete");

    let json: Value =
        serde_json::from_str(&read(&root.join("runs/run-1/iter-1/result.json"))).unwrap();
    let warnings = json["warnings"].as_array().expect("warnings");
    assert!(
        warnings
            .iter()
            .any(|warning| warning == "harness_source_read"),
        "the concrete read command must be traced: {warnings:?}"
    );
}

// ---------------------------------------------------------------------------
// DR-38 — the marker set must cover the whole harness repository
// ---------------------------------------------------------------------------

/// Run one scenario whose Developer ran `command`, and return the iteration
/// warnings.
///
/// DR-67: this helper is called several times over **one** temporary root, and
/// `FakeStep` writes the same `project.godot` bytes every time — so a repeat call
/// changed nothing in the project and the DR-67 zero-increment gate correctly
/// failed it, for a reason unrelated to what these tests measure.  The helper's
/// real intent is "a Developer *round* ran and the trace is report-only", so it
/// now also performs one genuine, **call-unique** project write (a counter, not
/// the command text, so two calls with the same command still differ).  The
/// fixture is strictly stronger: every round it exercises really did produce an
/// increment.
async fn warnings_for_developer_command(root: &std::path::Path, command: &str) -> Vec<Value> {
    static NEXT: std::sync::atomic::AtomicU64 = std::sync::atomic::AtomicU64::new(0);
    let nonce = NEXT.fetch_add(1, std::sync::atomic::Ordering::SeqCst);
    // The round's genuine increment is the Developer's own write below, made
    // **call-unique** by a counter: this helper runs several times over one
    // temporary root, and a `FakeStep` that writes identical bytes on every call
    // is — correctly — a zero increment on every call after the first, which
    // would fail these assertions for a reason they do not measure.
    write(
        &root.join("workspace/scripts/command_probe.gd"),
        &format!("extends Node\n# probe {nonce}: {command}\n"),
    );
    let script = vec![
        FakeStep::new(Role::Planner).writing(".hoh/plan.md", OK_PLAN),
        FakeStep::new(Role::Developer)
            .writing(
                "scripts/developer_write.gd",
                &format!("extends Node\n# developer write {nonce}\n"),
            )
            .trajectory_mentioning(command),
        FakeStep::new(Role::Tester)
            .writing(".hoh/evidence/move.json", "{}\n")
            .writing(".hoh/evidence.json", &ok_evidence(1, "")),
    ];
    let (result, _) = run_scenario(root, 1, script, Ablation::default(), FakeAdapter::new()).await;
    result.expect("the trace is report-only, it never fails the round");
    let json: Value =
        serde_json::from_str(&read(&root.join("runs/run-1/iter-1/result.json"))).unwrap();
    json["warnings"].as_array().cloned().unwrap_or_default()
}

/// DR-38 ①: `smoke-t5` listed the harness repository root without naming any
/// marker file.  The root is injected at runtime (`out_of_tree_root`, which
/// defaults to the process working directory), never hard-coded.
#[tokio::test]
async fn enumerating_the_harness_root_is_recorded_as_a_warning() {
    let temp = tempfile::tempdir().unwrap();
    let harness_root = std::env::current_dir().expect("the test process has a cwd");
    let command = format!("dir {}", harness_root.display());
    let warnings = warnings_for_developer_command(temp.path(), &command).await;
    assert!(
        warnings
            .iter()
            .any(|warning| warning == "harness_source_read"),
        "listing the harness root ({command}) must be traced: {warnings:?}"
    );
}

/// DR-38 ②: the second `smoke-t5` detour — a recursive YAML hunt piped into
/// `findstr hoh` — is a directory-enumeration aimed at the harness, even though
/// it names no path at all.
#[tokio::test]
async fn a_recursive_hoh_search_is_recorded_as_a_warning() {
    let temp = tempfile::tempdir().unwrap();
    let warnings =
        warnings_for_developer_command(temp.path(), "dir /b /s *.yaml | findstr hoh").await;
    assert!(
        warnings
            .iter()
            .any(|warning| warning == "harness_source_read"),
        "a recursive `*.yaml` hunt for `hoh` must be traced: {warnings:?}"
    );
}

/// DR-38 ③: a command that stays inside the project is not a harness read —
/// in particular the Tester's own `.hoh/...` evidence listings.
#[tokio::test]
async fn a_project_only_command_is_not_a_harness_read() {
    let temp = tempfile::tempdir().unwrap();
    for command in [
        "dir scenes\\*.tscn",
        "godot --headless --check-only res://scripts/player.gd",
        "ls .hoh/deterministic/*.json",
    ] {
        let warnings = warnings_for_developer_command(temp.path(), command).await;
        assert!(
            !warnings
                .iter()
                .any(|warning| warning == "harness_source_read"),
            "`{command}` stays inside the project: {warnings:?}"
        );
    }
}
