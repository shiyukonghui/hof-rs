# -*- coding: utf-8 -*-
"""TASK-098: build the Asteroids session (editor + game phases).

The session is the same shape TASK-097 used for Space Invaders, with the two lesson
corrections the TASK-097 report asked for:

  * the multi-frame flight sample is started BEFORE the state that ends the flight is
    produced (the bullet is placed far enough away that the kill lands inside the
    sample window, instead of being sampled after it);
  * the scene's batch add is run twice on purpose, so the D-3 refusal appears in this
    game's own evidence as a declared failure rather than as a surprise.

Written as a generator so the file can be regenerated verbatim from a review of it.
"""
import io
import json
import os

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", ".."))
SESSION_DIR = os.path.join(ROOT, "tools", "sessions", "asteroids")
OUT = os.path.join(SESSION_DIR, "session.json")

BG = {"type": "ColorRect", "name": "Background", "parent_path": ".",
      "properties": {"offset_left": 0, "offset_top": 0, "offset_right": 800,
                     "offset_bottom": 600, "color": {"r": 0.02, "g": 0.02, "b": 0.06, "a": 1}}}
HUD = {"type": "Label", "name": "Hud", "parent_path": ".",
       "properties": {"offset_left": 20, "offset_top": 12, "offset_right": 620,
                      "offset_bottom": 56, "text": "SCORE 0  LIVES 3  ROCKS 4",
                      "theme_override_font_sizes/font_size": 26}}
STATUS = {"type": "Label", "name": "Status", "parent_path": ".",
          "properties": {"offset_left": 560, "offset_top": 12, "offset_right": 790,
                         "offset_bottom": 56, "text": "ASTEROIDS 4",
                         "theme_override_font_sizes/font_size": 22}}
STATIC_BATCH = [BG, HUD, STATUS]

calls = []


def e(tag, tool, arguments, note):
    calls.append({"tag": tag, "port": "editor", "tool": tool,
                  "arguments": arguments, "note": note})


def g(tag, tool, arguments, note):
    calls.append({"tag": tag, "port": "game", "tool": tool,
                  "arguments": arguments, "note": note})


def sleep(ms, note):
    calls.append({"sleep_ms": ms, "port": "game", "note": note})


def code(expr):
    return {"code": expr}


def assert_state(tag, node, prop, op, expected, note):
    g(tag, "running_game_assert_node_state",
      {"node_path": node, "property": prop, "operator": op, "expected": expected}, note)


def samples(tag, props, frames, note, interval=1):
    g(tag, "running_game_get_node_property_samples",
      {"node_path": "Main", "properties": props, "frame_count": frames,
       "frame_interval": interval}, note)


def shot(tag, name, note):
    # `save_path` is what makes the frame land in user://: without it the tool
    # answers the PNG inline and nothing is written to disk, and the report's
    # "saved frames" table (the pixel-diff evidence) comes back empty.
    g(tag, "running_game_capture_screenshot", {"save_path": "user://" + name + ".png"}, note)


# =============================================================================
# editor phase -- everything the game needs is written through MCP calls
# =============================================================================
e("e01-edit-game", "project_edit_script",
  {"path": "res://src/AsteroidsGame.cs", "content_file": "payload/AsteroidsGame.cs"},
  "the whole game is written through the MCP script writer (the template stub is replaced)")
e("e02-open-scene", "editor_open_scene", {"path": "res://scenes/main.tscn"},
  "the template scene carries the root Main (Node2D) the script is attached to")
e("e03-batch-add-static", "editor_add_nodes_batch", {"nodes": STATIC_BATCH},
  "the three static nodes of the scene, through the batch tool: a background and two labels; "
  "the ship, the bullet and every rock are created at run time")
e("e04-save-1", "editor_save_scene", {}, "the scene with the three static nodes on disk: sha A")
e("e05-read-1", "project_read_text_file", {"path": "res://scenes/main.tscn"},
  "sha A and the exact bytes")
e("e06-batch-add-static-again", "editor_add_nodes_batch", {"nodes": STATIC_BATCH},
  "REAL-DEVELOPMENT PROOF of the TASK-097 fix: the same batch a second time must be REFUSED "
  "(-32000, one conflict per node) instead of the engine renaming it into a duplicate layer")
e("e07-tree-after-refusal", "editor_get_scene_tree", {},
  "the tree after the refusal: Main + the three named nodes, no @Type@N automatic name")
e("e08-save-2", "editor_save_scene", {}, "saving after the refusal must reproduce the same file")
e("e09-read-2", "project_read_text_file", {"path": "res://scenes/main.tscn"},
  "sha B; A == B is the proof that the refused batch wrote nothing")
e("e10-action-left", "editor_add_input_action", {"action": "ast_left", "key": "A"},
  "the turn-left action the game polls")
e("e11-action-right", "editor_add_input_action", {"action": "ast_right", "key": "D"},
  "the turn-right action")
e("e12-action-thrust", "editor_add_input_action", {"action": "ast_thrust", "key": "W"},
  "the thrust action")
e("e13-action-fire", "editor_add_input_action", {"action": "ast_fire", "key": "Space"},
  "declared even though the deterministic tests fire through an explicit hook")
e("e14-build-csharp", "project_build_csharp",
  {"configuration": "Debug", "timeout_ms": 300000, "rescan": True},
  "compile the game the MCP script writer just wrote")
e("e15-validate-scripts", "project_validate_scripts", {},
  "the engine's own per-file verdict")
e("e16-errors", "editor_get_errors", {}, "the editor log's ERROR lines after the build")

# =============================================================================
# game phase -- readback, samples, assertions, captures
# =============================================================================
g("g01-scene-tree", "running_game_get_scene_tree", {},
  "the running tree: the three static nodes plus the ship, the bullet and four rocks created "
  "at run time")
g("g02-readback-t0", "running_game_execute_gdscript", code("return get_parent().Dump()"),
  "the whole state as one line")
assert_state("g03-assert-score-0", "Main", "Score", "eq", 0, "nothing has scored yet")
assert_state("g04-assert-lives-3", "Main", "Lives", "eq", 3, "the game starts with three lives")
assert_state("g05-assert-rocks-4", "Main", "AsteroidsRemaining", "eq", 4,
             "the starting field is four large rocks")
assert_state("g06-assert-not-over", "Main", "GameOver", "eq", False, "the game starts alive")
shot("g07-shot-t0", "ast-t0", "the first frame of the evidence pair chain: four large rocks and the ship")
samples("g08-samples-frozen", ["ShipX", "ShipY", "FirstRockX", "Ticks"], 12,
        "determinism baseline: with DriftSpeed 0 and PollInput false the rocks and the ship do "
        "NOT move while the clock runs (ShipX/FirstRockX constant, Ticks increasing)")
g("g09-drift-on", "running_game_execute_gdscript", code("return get_parent().SetDrift(90.0)"),
  "the one test that watches the rocks move asks for motion explicitly")
samples("g10-samples-drift", ["FirstRockX", "FirstRockY", "Ticks"], 30,
        "multi-frame property sample of the drifting rocks: the first rock's own coordinates "
        "change, frame by frame, because they are real exported properties")
g("g11-drift-off", "running_game_execute_gdscript", code("return get_parent().SetDrift(0.0)"),
  "back to frozen, so the next aim and its readback are the same fact")
# --- the split: aim from far enough away that the flight IS the sample window -----
g("g12-force-split-setup", "running_game_execute_gdscript",
  code('return get_parent().ForceTestState("rocks=200,150,3;ship=400,300,0")'),
  "pin the board: one large rock at 200,150 and the ship at the centre")
assert_state("g13-assert-rocks-1", "Main", "AsteroidsRemaining", "eq", 1,
             "the forced field really has one rock")
g("g14-aim-bullet", "running_game_execute_gdscript",
  code("return get_parent().AimBulletAtRock(0, 150.0)"),
  "place the bullet 150 px BELOW the rock heading straight up: the flight is ~0.36 s, so the "
  "sample below starts while the bullet is still in flight and the hit lands inside its window "
  "(the TASK-097 sampling limitation, corrected)")
samples("g15-samples-flight", ["BulletActive", "BulletY", "Score", "AsteroidsRemaining"], 40,
        "the flight frame by frame, ending on the split it caused: BulletActive is true on the "
        "early frames and the score/rock count change inside the same window")
assert_state("g16-assert-split-1", "Main", "AsteroidsSplit", "eq", 1, "one large rock split once")
assert_state("g17-assert-destroyed-1", "Main", "AsteroidsDestroyed", "eq", 1, "one rock destroyed")
assert_state("g18-assert-rocks-2", "Main", "AsteroidsRemaining", "eq", 2,
             "large -> two medium: the field went from one rock to two")
assert_state("g19-assert-score-20", "Main", "Score", "eq", 20, "one large rock = 20 points")
assert_state("g20-assert-size-2", "Main", "FirstRockSize", "eq", 2,
             "and the two rocks that replaced it really are the next size down")
g("g21-rock-list", "running_game_execute_gdscript", code("return get_parent().RockList()"),
  "the split evidence as an exact list: two size-2 rocks at the large rock's position")
shot("g22-shot-t1", "ast-t1", "after the split: the large rock is gone and two smaller ones are there")
# --- rotation and thrust ------------------------------------------------------
g("g23-thrust-step", "running_game_execute_gdscript", code("return get_parent().ThrustStep(0.5)"),
  "a fixed-step thrust: the ship's motion is a property of the call, not of the frame clock")
assert_state("g24-assert-ship-moved", "Main", "ShipX", "gt", 420.0,
             "the ship travelled to the right")
assert_state("g25-assert-velocity", "Main", "ShipVelX", "gt", 0.0, "and it carries the velocity")
g("g26-rotate", "running_game_execute_gdscript", code("return get_parent().RotateShip(-45.0)"),
  "a fixed-step rotation: -45 degrees")
assert_state("g27-assert-angle", "Main", "ShipAngle", "eq", -45.0, "the ship really turned")
shot("g28-shot-t2", "ast-t2", "after the thrust and the turn: the ship is somewhere else, at a new angle")
g("g29-respawn", "running_game_execute_gdscript", code("return get_parent().RespawnShip()"),
  "put the ship back in the middle")
# --- win: clear the last rock -------------------------------------------------
g("g30-force-last-rock", "running_game_execute_gdscript",
  code('return get_parent().ForceTestState("rocks=200,150,1;ship=400,300,0")'),
  "pin a single small rock, so 'the last hit clears the field' is a property of the state")
assert_state("g31-assert-rocks-1", "Main", "AsteroidsRemaining", "eq", 1,
             "the forced field really is one rock")
g("g32-aim-last", "running_game_execute_gdscript",
  code("return get_parent().AimBulletAtRock(0, 260.0)"),
  "aim at the last rock from 260 px away (0.62 s of flight), so the next call can still see the "
  "bullet in the air rather than after the kill")
assert_state("g33-assert-in-flight", "Main", "BulletActive", "eq", True,
             "the bullet is in flight when the assertion runs, i.e. before the kill")
sleep(900, "let the bullet travel and the kill land")
assert_state("g34-assert-won", "Main", "Won", "eq", True, "the small rock was the last one")
assert_state("g35-assert-over-by-win", "Main", "GameOver", "eq", True, "and it ends the game")
assert_state("g36-assert-score-100", "Main", "Score", "eq", 100,
             "the win's 100 points are the small rock alone: ForceTestState pins the WHOLE state, "
             "counters included, so the 20 points the earlier split scored were deliberately "
             "zeroed by g30 and g19 is where that 20 is pinned")
g("g37-readback-won", "running_game_execute_gdscript", code("return get_parent().Dump()"),
  "the whole state at the win")
shot("g38-shot-t3-won", "ast-t3", "the win screen: no rocks at all, the status label says FIELD CLEARED")
g("g39-assert-screen-text-win", "running_game_assert_screen_text", {"text": "FIELD CLEARED"},
  "the status label really is on the captured screen")
# --- losing a life, then the last life ---------------------------------------
g("g40-force-rock-on-ship", "running_game_execute_gdscript",
  code('return get_parent().ForceTestState("rocks=400,300,3")'),
  "pin a rock exactly on top of the ship: the loss condition is a property of the positions")
sleep(400, "one frame is enough for the collision check, the readback comes after the clock moved")
assert_state("g41-assert-lives-2", "Main", "Lives", "eq", 2, "a rock hitting the ship costs one life")
assert_state("g42-assert-ship-dead", "Main", "ShipAlive", "eq", False,
             "the ship is gone until something respawns it")
assert_state("g43-assert-not-over-yet", "Main", "GameOver", "eq", False,
             "two lives left is not a game over")
g("g44-force-last-life", "running_game_execute_gdscript",
  code('return get_parent().ForceTestState("rocks=400,300,3;lives=1")'),
  "pin the last life with a rock on the ship")
sleep(400, "the collision lands on the next frame")
assert_state("g45-assert-lives-0", "Main", "Lives", "eq", 0, "the last life is gone")
assert_state("g46-assert-over-by-loss", "Main", "GameOver", "eq", True, "that is the loss")
assert_state("g47-assert-not-won", "Main", "Won", "eq", False, "a loss is not a win")
g("g48-readback-lost", "running_game_execute_gdscript", code("return get_parent().Dump()"),
  "the whole state at the loss")
shot("g49-shot-t4-lost", "ast-t4", "the loss screen: the rock is on top of the ship, the label says GAME OVER")
g("g50-assert-screen-text-loss", "running_game_assert_screen_text", {"text": "GAME OVER"},
  "the loss label really is on the captured screen")
# --- positive control: a node created at run time is drawn --------------------
g("g51-runtime-overlay", "running_game_execute_gdscript",
  code('var main = get_parent()\nvar c = ColorRect.new()\nc.name = StringName("ProbeOverlay")\n'
       'c.position = Vector2(600, 520)\nc.size = Vector2(160, 56)\n'
       'c.color = Color(0.1, 0.9, 0.35, 1.0)\nmain.add_child(c)\nreturn "overlay added"'),
  "a node created at run time, in the same session, as the positive control for 'a run-time node "
  "is drawn'")
shot("g52-shot-t5-overlay", "ast-t5", "the overlay is visible in this frame and not in t4")
assert_state("g53-assert-unknown-property", "Main", "NoSuchProperty", "eq", 1,
             "DECLARED FAILURE: a boundary call asking for a property that does not exist "
             "(-32001), so the error path of the assertion tool is on the record too")
g("g54-final-readback", "running_game_execute_gdscript", code("return get_parent().Dump()"),
  "the final state as one line")
g("g55-final-tree", "running_game_get_scene_tree", {},
  "the final tree, including the run-time overlay")

# =============================================================================
doc = {"import": True, "calls": calls}
os.makedirs(os.path.dirname(OUT), exist_ok=True)
with io.open(OUT, "w", encoding="utf-8", newline="\n") as handle:
    handle.write(json.dumps(doc, ensure_ascii=False, indent=1) + "\n")
print("wrote %s calls=%d" % (OUT, len(calls)))
