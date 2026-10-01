//! DR-73 ② — **the layer that produced the defect**.
//!
//! `smoke-t10` ended with E3 `not_met` in a way no role could have avoided from
//! the text it was handed: the Developer's definition of done asked for
//! *movement*, a *stable named node* and a *property that changes when the player
//! acts*, and said nothing about a collectible actually being picked up or a win
//! condition actually being reachable.  The battery observed movement and
//! jumping only.  The Developer then wrote `coin.gd` (an `Area2D` with
//! `body_entered.connect`) and `goal.gd` (an `Area2D` with a `reached` flag) and
//! moved on, because nothing in the round asked whether either of them ever
//! fired — and the acceptance gate it wrote into `.hoh/plan.md` was "simulate
//! move_right … then simulate jump", i.e. the two behaviours that were already
//! covered.
//!
//! This is the **contract** for the fix.  It is deliberately about the **text the
//! pipeline hands the Developer and the Planner**, not about the sample game:
//! DR-73 may not hand-write the game for the pipeline, so the repair has to be
//! that the pipeline's own instructions require, and its own recipes show how to
//! produce, the two behaviours E3 names.  Nothing here asserts on
//! `.workspace/mario/**`.

mod common;

use common::{delivered_prompt, delivered_skill};
use hof_rs::adapter::godot::{
    COIN_COUNTER_PREFIX, GOAL_POSITION_NODE, GOAL_REACHED_PROPERTY, INTERACTION_DRIVE_ACTION,
};

/// The two behaviours `REQUIREMENTS.md:114` names that the round never produced.
const REQUIRED_BEHAVIOURS: [&str; 2] = ["a collectible picked up", "a reachable win condition"];

#[test]
fn the_developer_definition_of_done_requires_the_two_missing_behaviours() {
    let prompt = delivered_prompt(hof_rs::prompts::DEVELOPER_PROMPT);
    let lower = prompt.to_lowercase();
    for phrase in REQUIRED_BEHAVIOURS {
        assert!(
            lower.contains(phrase),
            "the Developer's definition of done must name `{phrase}`; the round that produced \
             `Coins: 0` and `Goal.reached=false` was never told it had to.\n--- prompt ---\n{prompt}"
        );
    }
    // …and it must say what makes them *observable*, not merely present in the
    // source: the round's own `coin.gd` had `body_entered.connect`, and the coin
    // was still never picked up.
    assert!(
        lower.contains("picked up") && lower.contains("hud") && lower.contains("counter"),
        "the requirement must name the observable that closes it (the HUD coin counter):\n{prompt}"
    );
    assert!(
        lower.contains("win condition") && lower.contains("reachable"),
        "the requirement must name the reachable win condition:\n{prompt}"
    );
    // The counter that judges `Coins: 0` is the specification's own wording.
    assert!(
        prompt.contains(COIN_COUNTER_PREFIX),
        "the delivered text must spell the counter the battery and the Tester read \
         (`{COIN_COUNTER_PREFIX}`):\n{prompt}"
    );
    assert!(
        prompt.contains(GOAL_REACHED_PROPERTY),
        "the delivered text must spell the goal flag `{GOAL_REACHED_PROPERTY}`:\n{prompt}"
    );
    // The exact recipe is in the skill; the prompt has to point at it.
    assert!(
        prompt.contains("godot-dev"),
        "the definition of done must point at the skill that carries the recipe:\n{prompt}"
    );
}

#[test]
fn the_godot_dev_skill_carries_an_executable_recipe_for_both_behaviours() {
    let skill = delivered_skill("godot-dev.md");
    let lower = skill.to_lowercase();

    // ① a collectible that really fires: the Area2D rules that make
    //    `body_entered` reachable, with the signals/layers the round got wrong.
    assert!(
        lower.contains("body_entered"),
        "the skill must name the signal the pickup travels through:\n{skill}"
    );
    assert!(
        lower.contains("monitoring"),
        "the skill must say an `Area2D` needs `monitoring` (a disabled one never fires \
         `body_entered`):\n{skill}"
    );
    assert!(
        lower.contains("collision_layer") && lower.contains("collision_mask"),
        "the skill must say the layers and masks have to match on both sides:\n{skill}"
    );
    assert!(
        lower.contains("add_to_group") && lower.contains("is_in_group"),
        "the skill must show the group handshake the pickup handler checks:\n{skill}"
    );
    assert!(
        skill.contains(COIN_COUNTER_PREFIX),
        "the skill must spell the counter the battery reads (`{COIN_COUNTER_PREFIX}`):\n{skill}"
    );
    assert!(
        lower.contains("queue_free") || lower.contains("free()"),
        "the skill must say the collectible disappears:\n{skill}"
    );

    // ② a reachable win condition: the trigger has to be inside the traversable
    //    level.  DR-76 ③: this comment used to say "the round put it at x=6400
    //    with no ground beyond x≈3800" — **that was false**.  The frozen
    //    `Ground` is one 6800x40 `RectangleShape2D` centred at x=3400, covering
    //    x in [0,6800] with an enabled collision shape, i.e. continuous under the
    //    goal; the only obstacle before it is a 32x60 wall whose top is 28 px up,
    //    inside the 66 px jump apex.  The true cause of the missing win was
    //    **replay coverage**, and the skill now says so (and keeps the old
    //    wording marked superseded).  `the_godot_dev_skill_retracts_the_
    //    impassable_level_claim` pins the correction.
    assert!(
        lower.contains("reachable"),
        "the skill must state that the win trigger has to be reachable by walking:\n{skill}"
    );
    assert!(
        lower.contains("jump") && lower.contains("gap"),
        "the skill must warn about the intended horizontal gap (a jump does not cross it):\n{skill}"
    );
    assert!(
        skill.contains(GOAL_REACHED_PROPERTY),
        "the skill must spell the exported flag `{GOAL_REACHED_PROPERTY}` the shape check reads:\n{skill}"
    );
    assert!(
        lower.contains("victory") || lower.contains("win"),
        "the skill must describe the visible victory state as well as the flag:\n{skill}"
    );

    // ③ the way the Developer can check it *before* the battery does, without
    //    starting a game of its own (the runtime owns the session).
    assert!(
        lower.contains("battery") && lower.contains("tester"),
        "the skill must say who observes the running game, so the Developer does not build a \
         second session to check itself:\n{skill}"
    );

    // ④ the drive the battery uses is named too, so the round's level is designed
    //    against the same action.
    assert!(
        skill.contains(INTERACTION_DRIVE_ACTION),
        "the skill must name the action the window drives (`{INTERACTION_DRIVE_ACTION}`):\n{skill}"
    );
}

#[test]
fn the_planner_acceptance_gate_must_cover_the_interaction_behaviours() {
    let prompt = delivered_prompt(hof_rs::prompts::PLANNER_PROMPT);
    let lower = prompt.to_lowercase();
    assert!(
        lower.contains("acceptance gate"),
        "the planner prompt must keep its acceptance-gate section:\n{prompt}"
    );
    // The measured defect: the plan `smoke-t10` produced had an Acceptance Gate
    // that covered movement and jumping only, so "the iteration succeeded" was
    // provable without a coin ever being collected.
    assert!(
        lower.contains("interact") || lower.contains("collect"),
        "the planner must be told the acceptance gate has to cover an interaction, not only \
         movement:\n{prompt}"
    );
    assert!(
        lower.contains("win") || lower.contains("victory"),
        "the planner must be told the acceptance gate has to cover the win condition:\n{prompt}"
    );
    assert!(
        lower.contains("movement") || lower.contains("jump"),
        "the planner must be told movement and jumping alone are not enough:\n{prompt}"
    );
    assert!(
        prompt.contains(GOAL_REACHED_PROPERTY),
        "the planner must see the property the win is judged by (`{GOAL_REACHED_PROPERTY}`):\n{prompt}"
    );
}

#[test]
fn the_tester_is_told_which_battery_steps_prove_the_two_behaviours() {
    // The Tester reads `.hoh/deterministic/battery.json` and the playbook, not a
    // prompt about a file.  The window has to be **in the battery the round
    // runs** and named in the playbook's step table, or the Tester cannot turn
    // `interaction_evidence` into a claim about F10/F13.  This asserts the one
    // wiring point (`run`) plus the table row; the behavioural half is
    // `tests/evidence_battery.rs`.
    let source = std::fs::read_to_string(
        std::path::Path::new(env!("CARGO_MANIFEST_DIR")).join("src/adapter/godot.rs"),
    )
    .expect("the adapter source is readable");
    assert!(
        source.contains("self.step_interaction_evidence(scene_tree.clone()).await?"),
        "the window must be wired into the battery's run order, before the node assertions"
    );
    assert!(
        source.contains("| `interaction_evidence` | F10, F13"),
        "the playbook's step table must document the window and what it supports"
    );
    for verdict in [
        "COIN_PICKED_UP",
        "WIN_DRIVEN",
        "COIN_NOT_PICKED_UP",
        "WIN_NOT_DRIVEN",
        "COIN_COUNTER_UNREADABLE",
        // DR-76 ②: the two diagnoses `WIN_NOT_DRIVEN` used to collapse.
        "WIN_UNREACHED_WITHIN_BUDGET",
        "WIN_UNREACHABLE_GEOMETRICALLY",
        // DR-76 ②: the number the split is made of.
        "coverage_shortfall_px",
    ] {
        assert!(
            source.contains(verdict),
            "the playbook must name `{verdict}` so the Tester can judge the claim"
        );
    }
    assert_eq!(GOAL_POSITION_NODE, "Goal");
}

/// DR-76 ③: the delivered skill must retract the "the level is impassable" claim.
///
/// The DR-73 report and the skill's 3b said the frozen level had "no ground past
/// x ≈ 3800", that the goal was positionally unreachable and that the level was
/// impassable.  The acceptance's A3 proved the opposite from the frozen scene: the
/// `Ground` body is a single `6800 × 40` `RectangleShape2D` centred at `x = 3400`,
/// covering `x ∈ [0, 6800]` with an enabled collision shape — continuous under the
/// goal — and the only obstacle before it is a `32 × 60` wall whose top is `28 px`
/// above the surface, inside the `66 px` apex the same report computed.  The true
/// cause of "the win was never driven" is **replay coverage**.
///
/// This is delivered text: left standing, it would send the next Developer to
/// shorten a level that was already fine.  The old wording is allowed to survive
/// only inside a block that marks itself superseded and says it was false.
#[test]
fn the_godot_dev_skill_retracts_the_impassable_level_claim() {
    let skill = delivered_skill("godot-dev.md");
    let lower = skill.to_lowercase();

    // The fact: the ground is continuous to x=6800, and the recipe says so.
    assert!(
        lower.contains("6800"),
        "the skill must state the ground's real extent (6800 px):\n{skill}"
    );
    assert!(
        lower.contains("continuous"),
        "the skill must say the ground is continuous under the goal:\n{skill}"
    );
    // The cause: coverage, not geometry.
    assert!(
        lower.contains("coverage"),
        "the skill must name replay coverage as the true cause:\n{skill}"
    );
    assert!(
        lower.contains("superseded"),
        "the retraction must be marked and the old wording preserved as superseded:\n{skill}"
    );
    // The split, so the next round cannot read a coverage gap as geometry.
    assert!(
        skill.contains("WIN_UNREACHED_WITHIN_BUDGET")
            && skill.contains("WIN_UNREACHABLE_GEOMETRICALLY"),
        "the skill must name both verdicts so the Developer/Tester can tell coverage from \
         geometry:\n{skill}"
    );

    // The false claim may survive **only** as marked-superseded prose: every
    // paragraph that carries it must also call it false.
    //
    // The delivered skill is a **CRLF** document (`.gitattributes` does not pin
    // it, and this machine checks it out with CRLF), so the blocks are split on a
    // normalised copy: splitting the raw text on `"\n\n"` would find no boundary
    // at all and make the whole file one paragraph — which is exactly the kind of
    // vacuity that let the DR-73 fixture hide its defect.  (The plant that puts
    // the old sentence back into the standing bullet reddens this check.)
    let normalized = skill.replace("\r\n", "\n").replace('\r', "\n");
    for paragraph in normalized.split("\n\n") {
        if !paragraph.to_lowercase().contains("no ground past") {
            continue;
        }
        let paragraph_lower = paragraph.to_lowercase();
        assert!(
            paragraph_lower.contains("superseded") && paragraph_lower.contains("false"),
            "the old wording may only survive marked as superseded and called false; this \
             paragraph still stands as a claim:\n{paragraph}"
        );
    }
}
