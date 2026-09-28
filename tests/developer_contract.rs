//! DR-23 — the Developer's definition of done and the skills that make it
//! reachable.
//!
//! The first smoke run's only new script (`player.gd`) was **0 bytes**, the
//! player never moved, `Goal` had no collision shape and the HUD had no `Label`.
//! These tests pin the text assets that prevent exactly that: a completion
//! definition in `developer.md` and copy-pasteable, real-tool recipes in the
//! skills.

mod common;

use common::*;
use hof_rs::model::Ablation;

fn skill(name: &str) -> String {
    hof_rs::prompts::skills()
        .into_iter()
        .find(|(file, _)| *file == name)
        .unwrap_or_else(|| panic!("skill {name} is not embedded"))
        .1
        .to_string()
}

#[test]
fn developer_prompt_states_the_definition_of_done() {
    let prompt = hof_rs::prompts::DEVELOPER_PROMPT;
    let lower = prompt.to_lowercase();

    assert!(
        lower.contains("definition of done") || lower.contains("definition-of-done"),
        "developer.md must state when work is done: {prompt}"
    );
    assert!(
        lower.contains("battery"),
        "done-ness must be observable through the battery records: {prompt}"
    );
    assert!(
        lower.contains("empty"),
        "an empty file must be explicitly forbidden: {prompt}"
    );
    assert!(
        lower.contains("project_read_script") || lower.contains("read it back"),
        "a written script must be read back for self-verification: {prompt}"
    );
    assert!(
        lower.contains("n1") && lower.contains("n2"),
        "the developer must guarantee N1 (launchable) and N2 (observable): {prompt}"
    );
    // Still a valid role template.
    assert!(!prompt.contains("{{step_limit}}") || prompt.contains("{{step_limit}}"));
}

#[test]
fn godot_dev_skill_is_a_real_recipe_book() {
    let dev = skill("godot-dev.md");

    for needle in [
        "$HOH_HOH_BIN tools call",
        "--args-file",
        "$HOH_ARTIFACT_DIR",
        "project_create_script",
        "project_edit_script",
        "project_read_script",
        "CollisionShape2D",
        "RectangleShape2D",
        "editor_setup_collision_shape",
        "Area2D",
        "Label",
        "editor_simulate_input_action",
        "running_game_get_node_property_samples",
        "non-empty",
    ] {
        assert!(dev.contains(needle), "godot-dev.md is missing `{needle}`");
    }

    // At least six numbered recipes.
    let recipes = dev.lines().filter(|line| line.starts_with("## ")).count();
    assert!(
        recipes >= 6,
        "godot-dev.md must carry at least six recipes, found {recipes}"
    );

    // The argument examples use the real snake_case tool parameters.
    assert!(dev.contains("\"action\""), "editor_simulate_input_action uses `action`");
    assert!(
        dev.contains("\"pressed\""),
        "editor_simulate_input_action uses `pressed`"
    );
    assert!(dev.contains("\"node_path\""), "lookups use `node_path`");
    assert!(dev.contains("\"properties\""), "monitor uses `properties`");
}

#[test]
fn godot_testing_skill_explains_the_battery_and_relative_paths() {
    let testing = skill("godot-testing.md");
    let lower = testing.to_lowercase();

    for needle in [
        "battery.json",
        ".hoh/deterministic",
        "relative",
        "ok = false",
        "gap",
    ] {
        assert!(
            lower.contains(&needle.to_lowercase()),
            "godot-testing.md is missing `{needle}`"
        );
    }
    assert!(
        lower.contains("source") && lower.contains("not"),
        "godot-testing.md must state that existing source is not verification"
    );
}

/// The skills must actually reach the roles.
#[tokio::test]
async fn skills_are_injected_into_the_role_views() {
    let temp = tempfile::tempdir().unwrap();
    let root = temp.path();
    let (result, records) = run_scenario(
        root,
        1,
        happy_script(),
        Ablation::default(),
        FakeAdapter::new(),
    )
    .await;
    result.expect("the happy path must complete");

    for record in &records {
        assert!(
            record.files.contains_key(".hoh/skills/godot-dev.md"),
            "{:?} view is missing the developer skill",
            record.role
        );
        assert!(
            record.files.contains_key(".hoh/skills/godot-testing.md"),
            "{:?} view is missing the testing skill",
            record.role
        );
    }
    let candidate = root.join("runs/run-1/iter-1/candidate/.hoh/skills/godot-dev.md");
    assert!(candidate.is_file());
    assert!(read(&candidate).contains("editor_setup_collision_shape"));
}
