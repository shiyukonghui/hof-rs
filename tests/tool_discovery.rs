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
use hof_rs::adapter::godot::validate_scene_structure;
use hof_rs::model::{Ablation, Role};
use serde_json::Value;

fn skill(name: &str) -> String {
    hof_rs::prompts::skills()
        .into_iter()
        .find(|(file, _)| *file == name)
        .unwrap_or_else(|| panic!("skill {name} is not embedded"))
        .1
        .to_string()
}

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
    assert!(developer.contains("`monitor_properties`"), "{developer}");
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
    assert!(tester.contains("`monitor_properties`"));
    assert!(
        !tester.contains("edit_script") && !tester.contains("add_node"),
        "a mutating tool must not appear in the tester's index"
    );

    let planner = hof_rs::tools::index::render_tools_markdown(Role::Planner, &schemas);
    assert!(
        !planner.contains("`get_project_info`") && !planner.contains("`play_scene`"),
        "the planner owns no MCP tool"
    );
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
// ③ the known-good skeleton passes the DR-24 structure check
// ---------------------------------------------------------------------------

/// The scene text of the skill's skeleton: everything from `[gd_scene` to the
/// closing fence of that code block.
fn skeleton_scene(dev: &str) -> String {
    let start = dev
        .find("[gd_scene")
        .unwrap_or_else(|| panic!("the skill has no [gd_scene] skeleton:\n{dev}"));
    let rest = &dev[start..];
    let end = rest
        .find("\n```")
        .expect("the skeleton code block is not closed");
    rest[..end].to_string()
}

#[test]
fn the_godot_dev_skeleton_is_a_valid_scene() {
    let dev = skill("godot-dev.md");
    let scene = skeleton_scene(&dev);
    let report = validate_scene_structure(&scene);
    assert!(
        report.ok,
        "the known-good skeleton must pass DR-24's structure check: {:?}",
        report.problems
    );
    assert!(scene.contains("[node name=\"Main\" type=\"Node2D\"]"));
    assert!(scene.contains("parent=\".\""));
    assert!(scene.contains("SubResource(\"RectangleShape2D_player\")"));
    assert!(scene.contains("ExtResource(\"1_player\")"));
    assert!(scene.contains("type=\"Label\""));
    assert!(scene.contains("text = \"Score: 0\""));

    // The GDScript half must be real, not an empty placeholder.
    assert!(dev.contains("extends CharacterBody2D"));
    assert!(dev.contains("move_and_slide()"));
    assert!(dev.contains("Input.is_action_pressed(\"jump\")"));
    assert!(dev.contains("gravity"));
}

// ---------------------------------------------------------------------------
// ④ prompts forbid the source-reading detour and repeated submits
// ---------------------------------------------------------------------------

#[test]
fn every_role_prompt_forbids_the_harness_sources() {
    for (name, prompt) in [
        ("planner", hof_rs::prompts::PLANNER_PROMPT),
        ("developer", hof_rs::prompts::DEVELOPER_PROMPT),
        ("tester", hof_rs::prompts::TESTER_PROMPT),
    ] {
        for needle in [
            "src/**",
            ".spec/**",
            "tests/**",
            ".git/**",
            "F:\\RustProjects\\**",
            "$HOH_SCRATCH_DIR",
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
                "Do not read src/adapter/godot.rs or F:\\RustProjects\\** .",
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
            .trajectory_mentioning("grep -n play_scene src/runtime/run_loop.rs"),
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
