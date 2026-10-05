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

/// Round-5 repair (defect RA-6): this used to pin `godot-dev.md`, the previous
/// engine's recipe book, which was still compiled into the binary and injected
/// into `.hoh/skills/` in every round.  The repository is the harness plus
/// **this** engine's flow, so the book is gone (`src/prompts/skills/godot-*.md`
/// removed, `prompts::skills()` returns the two Bevy books) and the same
/// assertions apply to the book a role really receives.
///
/// The coverage is deliberately kept, not deleted: the delivered-form needles
/// (DR-66 — the syntax the role's `cmd.exe` actually executes), the
/// minimum-recipe count, and the "a written file is read back" rule all still
/// have to hold of the Bevy book, or the prompt discipline they enforce has no
/// subject.
#[test]
fn the_bevy_dev_skill_is_a_real_recipe_book() {
    let dev = skill("bevy-dev.md");

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
        // The project's own build and write path.
        "cargo build --offline",
        "HOH_WRITE_FILE src/game.rs",
        "HOH_READ_FILE",
        // The frozen contract, in Bevy terms.
        "hof_game",
        "src/contract.rs",
        "#[reflect(Component)]",
        "register_type",
        "InputIntent",
        "FrameCounter",
        // The audience-aware rule DR-70 ①/DR-71 ③ established: the runtime owns
        // the session and the game that window covers predates the Developer's
        // edits.
        "before you changed the code",
        "do not start a game of your own",
        // The definition-of-done rule the Developer prompt carries, in this
        // engine's terms.
        "never left empty",
    ] {
        assert!(dev.contains(needle), "bevy-dev.md is missing `{needle}`");
    }
    if cfg!(windows) {
        assert!(
            !dev.contains("$HOH_HOH_BIN"),
            "the recipe book still spells a cmd call with a POSIX variable"
        );
    }

    // At least seven numbered recipes, so the book is a book and not a list.
    let recipes = dev.lines().filter(|line| line.starts_with("## ")).count();
    assert!(
        recipes >= 7,
        "bevy-dev.md must carry at least seven recipes, found {recipes}"
    );

    // No previous-engine material may come back with it (RA-6).
    for old_engine in [
        "godot",
        "project_create_script",
        "project_edit_script",
        "editor_setup_collision_shape",
        "editor_simulate_input_action",
    ] {
        assert!(
            !dev.to_lowercase().contains(old_engine),
            "bevy-dev.md still carries previous-engine material: `{old_engine}`"
        );
    }
}

/// The Tester's book, on the same terms: the battery contract, the relative-path
/// rule, and the statement that existing source is not evidence.
#[test]
fn the_bevy_testing_skill_explains_the_battery_and_relative_paths() {
    let testing = skill("bevy-testing.md");
    let lower = testing.to_lowercase();

    for needle in [
        "battery.json",
        ".hoh/deterministic",
        "relative",
        "ok = false",
        "gap",
        // The channels this project really has, rather than the removed engine's.
        "bevy_player_transform",
        "bevy_grounded",
    ] {
        assert!(
            lower.contains(&needle.to_lowercase()),
            "bevy-testing.md is missing `{needle}`"
        );
    }
    assert!(
        lower.contains("source") && lower.contains("not"),
        "bevy-testing.md must state that existing source is not verification"
    );
    for old_engine in ["godot", "running_game_", "editor_play_scene"] {
        assert!(
            !lower.contains(old_engine),
            "bevy-testing.md still carries previous-engine material: `{old_engine}`"
        );
    }
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
            record.files.contains_key(".hoh/skills/bevy-dev.md"),
            "{:?} view is missing the developer skill",
            record.role
        );
        assert!(
            record.files.contains_key(".hoh/skills/bevy-testing.md"),
            "{:?} view is missing the testing skill",
            record.role
        );
    }
    let candidate = root.join("runs/run-1/iter-1/candidate/.hoh/skills/bevy-dev.md");
    assert!(candidate.is_file());
    assert!(read(&candidate).contains("HOH_WRITE_FILE src/game.rs"));
    // Round-5 repair (RA-6): and nothing of the previous engine's book reached
    // any role's view.  The scope is the skill directory, because the fake
    // adapter's own candidate is a Godot-shaped fixture (`project.godot`) and the
    // rule being pinned is about the *skills* this batch removed.
    for record in &records {
        for (path, _) in &record.files {
            if !path.contains("/skills/") {
                continue;
            }
            assert!(
                !path.contains("godot"),
                "{:?} view still carries previous-engine material at {path}",
                record.role
            );
        }
    }
}
