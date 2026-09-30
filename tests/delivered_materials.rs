//! DR-70 ③: no delivered text may send a role to a channel it cannot reach.
//!
//! The acceptance's D5 found the same contradiction DR-69 had fixed in
//! `developer.md` still standing in the skill that role is handed:
//! `src/prompts/skills/godot-dev.md` §5 told the Developer to prove its own work
//! with `running_game_get_node_property_samples` and required
//! `samples[*].position.x` to change, and §6 told it to call
//! `running_game_get_scene_tree` after `editor_play_scene` — while
//! `tests/developer_contract.rs` still *required* that string.
//!
//! DR-70 ① changes the fact underneath: the round's route is now published for
//! the whole round, so the Developer **can** reach the game endpoint.  The
//! channel is still not its verification channel, because the game that window
//! covers was started **before the Developer's edits** — it runs the previous
//! revision, so an observation of it cannot confirm the increment.  These tests
//! therefore pin an **audience-aware** rule rather than a blanket ban:
//!
//! * the Developer-facing documents carry no concrete `running_game_<tool>`
//!   instruction, and the skill says why;
//! * the Tester-facing documents keep the game-process recipe (otherwise the
//!   rule would be satisfied by deleting the channel everywhere, which is not a
//!   fix);
//! * the generated `TOOLS.md` index is a catalogue, not an instruction.

use hof_rs::config::AgentLimits;
use hof_rs::model::Role;
use hof_rs::prompts::skill_documents;
use hof_rs::runtime::invoke::render_prompt_with_budget_and_shell;
use hof_rs::runtime::shell::ShellFlavor;
use hof_rs::tools::{McpChannel, ToolChannel};

/// The concrete `running_game_<tool>` name in `text`, when there is one.
///
/// The wildcard form `running_game_*` is deliberately **not** a concrete name:
/// `developer.md` uses it to explain that the channel exists and is still not the
/// role's proof obligation, and forbidding the explanation would forbid the fix.
fn concrete_game_tool(text: &str) -> Option<String> {
    let mut rest = text;
    while let Some(found) = rest.find("running_game_") {
        let after = &rest[found + "running_game_".len()..];
        let name: String = after
            .chars()
            .take_while(|character| character.is_ascii_alphanumeric() || *character == '_')
            .collect();
        if !name.is_empty() {
            return Some(format!("running_game_{name}"));
        }
        rest = after;
    }
    None
}

/// A prompt as its role actually receives it (shell placeholders resolved).
fn delivered_prompt(template: &str) -> String {
    render_prompt_with_budget_and_shell(template, 1, &AgentLimits::default(), ShellFlavor::HOST)
}

/// Whitespace-normalized, lower-cased text: the delivered documents are wrapped
/// prose, so a phrase that matters must not be missed because a line break fell
/// inside it.
fn normalized(text: &str) -> String {
    text.split_whitespace()
        .collect::<Vec<_>>()
        .join(" ")
        .to_lowercase()
}

/// A skill file as it is injected into a role's `.hoh/skills/**`.
fn delivered_skill(name: &str) -> String {
    skill_documents(ShellFlavor::HOST)
        .into_iter()
        .find(|(file, _)| file == name)
        .unwrap_or_else(|| panic!("skill {name} is not embedded"))
        .1
}

/// The generated tool index a role receives (DR-26), built from the embedded
/// snapshot when the editor cannot be reached.
fn generated_tool_index(role: Role) -> String {
    let channel = McpChannel::new("http://127.0.0.1:1/mcp", 1, 0);
    channel.index_markdown(role)
}

/// The Developer-facing materials must not name a game-process tool as the
/// Developer's own evidence channel.
#[test]
fn no_developer_facing_material_sends_the_role_to_the_game_process() {
    let skill = delivered_skill("godot-dev.md");
    for (label, text) in [
        (
            "developer.md",
            delivered_prompt(hof_rs::prompts::DEVELOPER_PROMPT),
        ),
        ("godot-dev.md", skill.clone()),
    ] {
        assert!(
            concrete_game_tool(&text).is_none(),
            "{label} still points the Developer at the game process via `{}`: DR-70 ① publishes \
             the route for the whole round, but the game that window covers was started before \
             the Developer's edits, so it cannot confirm them",
            concrete_game_tool(&text).unwrap_or_default()
        );
    }
}

/// …and the skill must say *why*, because "do not use it" without a reason is the
/// kind of instruction a role reads as a puzzle to solve.
#[test]
fn the_developer_skill_explains_why_the_game_process_is_not_its_self_test() {
    let skill = delivered_skill("godot-dev.md");
    let lower = normalized(&skill);

    assert!(
        lower.contains("before you changed the code"),
        "godot-dev.md must state that the round's game predates the Developer's edits"
    );
    assert!(
        lower.contains("editor_get_errors"),
        "godot-dev.md must give the Developer the editor-side substitute"
    );
    assert!(
        !lower.contains("tools call editor_play_scene"),
        "godot-dev.md must not tell the Developer to boot a second game while the runtime owns \
         the round's session (DR-70 ①)"
    );
}

/// The non-vacuity half: the Tester's materials keep the game-process recipe.
/// Nothing here should tempt anyone to "fix" the rule by removing the channel.
#[test]
fn the_tester_facing_materials_still_receive_the_game_process_recipe() {
    let testing = delivered_skill("godot-testing.md");
    assert!(
        concrete_game_tool(&testing).is_some(),
        "godot-testing.md must keep the game-process evidence recipe: the Tester's window is \
         exactly what DR-70 ① publishes the route for"
    );
}

/// `TOOLS.md` is generated from the live schema; it is a catalogue of what a role
/// may call, not a recipe telling it to call something.  It must never grow an
/// imperative call line for the game channel.
#[test]
fn the_generated_tool_index_is_a_catalogue_not_an_instruction() {
    let index = generated_tool_index(Role::Developer);
    assert!(
        !index.contains("tools call running_game_"),
        "the generated TOOLS.md must not carry an imperative game-channel call"
    );
}

/// The third site: `developer.md` itself.  Its DR-69 text described the *old*
/// window ("that route exists only after the battery's own `editor_play_scene`
/// step ... so during your call it may be unavailable"), which DR-70 ① makes
/// false.  The delivered prompt must state the new fact — and must not claim the
/// channel is unavailable.
#[test]
fn the_developer_prompt_states_the_round_wide_route_and_its_staleness() {
    let prompt = delivered_prompt(hof_rs::prompts::DEVELOPER_PROMPT);
    let lower = normalized(&prompt);

    assert!(
        lower.contains("for the whole round"),
        "developer.md must state that the route is published for the whole round (DR-70 ①):\
         \n{prompt}"
    );
    assert!(
        lower.contains("before your edits"),
        "developer.md must state that the game the route names predates the Developer's edits:\
         \n{prompt}"
    );
    assert!(
        !lower.contains("during your call it may be unavailable"),
        "developer.md still carries the superseded claim that the route may be unavailable:\
         \n{prompt}"
    );
}
