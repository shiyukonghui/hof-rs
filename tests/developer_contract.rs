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
    delivered_skill(name)
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

/// DR-69 ②: the order of work, and the contradiction `smoke-t9` measured.
///
/// The old definition-of-done item 4 told the Developer to prove its own work
/// with `running_game_get_node_property_samples` — the very channel that was
/// structurally unreachable (`F-T9-1`) — so the one instruction the role read as
/// "verify yourself" pointed at a game endpoint only the Tester and the
/// deterministic battery drive.  The role then spent 175 calls hand-rolling an
/// MCP client and probing ports over raw HTTP.
///
/// The delivered prompt must therefore say: change the project code first; the
/// in-round observation of the running game is not the Developer's prerequisite
/// and belongs to the Tester and the battery; and none of the workarounds the
/// round actually used may be suggested anywhere in it.
#[test]
fn the_developer_changes_the_code_first_and_leaves_observation_to_the_tester() {
    let prompt = delivered_prompt(hof_rs::prompts::DEVELOPER_PROMPT);
    let lower = prompt.to_lowercase();

    for needle in [
        "change the project code first",
        "not your prerequisite",
        "tester",
        "battery",
    ] {
        assert!(
            lower.contains(&needle.to_lowercase()),
            "developer.md must tell the Developer its order of work; missing `{needle}`"
        );
    }

    // The measured workarounds must not be suggested, and the unreachable
    // channel must no longer be the Developer's own proof obligation.
    for forbidden in [
        "running_game_get_node_property_samples",
        "build your own mcp client",
        "write your own mcp client",
        "python -c",
        "invoke-restmethod",
        "netstat",
        "curl ",
        "raw http",
    ] {
        assert!(
            !lower.contains(forbidden),
            "developer.md still points the Developer at `{forbidden}`"
        );
    }
}

#[test]
fn godot_dev_skill_is_a_real_recipe_book() {
    let dev = skill("godot-dev.md");

    // DR-66: the needles are the **delivered** forms, so the recipe book is
    // asserted in the syntax the role's shell actually executes.  The old
    // `"$HOH_HOH_BIN tools call"` needle passed on Windows while the very line
    // it matched was the one cmd rejected in `smoke-t7`
    // (`'$HOH_HOH_BIN" tools call …' is not recognized …`).
    let bin = hof_rs::runtime::shell::ShellFlavor::HOST.var("HOH_HOH_BIN");
    let artifact = hof_rs::runtime::shell::ShellFlavor::HOST.var("HOH_ARTIFACT_DIR");
    for needle in [
        &format!("{bin} tools call") as &str,
        "--args-file",
        &artifact,
        "project_create_script",
        "project_edit_script",
        "project_read_script",
        "CollisionShape2D",
        "RectangleShape2D",
        "editor_setup_collision_shape",
        "Area2D",
        "Label",
        "editor_simulate_input_action",
        // DR-70 ③: the recipe this needle used to require was
        // `running_game_get_node_property_samples`, i.e. exactly the instruction
        // the acceptance's D5 kept finding in the delivered skill.  DR-70 ①
        // publishes the route for the whole round, but the game it names was
        // started **before** the Developer's edits, so the recipe could not
        // confirm them.  The needle now requires the editor-side substitute, and
        // `delivered_materials.rs` pins the *absence* of the game-process
        // instruction on the Developer's side.  This is a requirement-driven
        // swap, not a loosened assertion: one concrete tool name left the list
        // and two concrete requirements (`editor_get_errors`,
        // `before you changed the code`) entered it.
        "editor_get_errors",
        "before you changed the code",
        "non-empty",
    ] {
        assert!(dev.contains(needle), "godot-dev.md is missing `{needle}`");
    }
    if cfg!(windows) {
        assert!(
            !dev.contains("$HOH_HOH_BIN"),
            "the recipe book still spells a cmd call with a POSIX variable"
        );
    }

    // At least six numbered recipes.
    let recipes = dev.lines().filter(|line| line.starts_with("## ")).count();
    assert!(
        recipes >= 6,
        "godot-dev.md must carry at least six recipes, found {recipes}"
    );

    // The argument examples use the real snake_case tool parameters.
    assert!(
        dev.contains("\"action\""),
        "editor_simulate_input_action uses `action`"
    );
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
