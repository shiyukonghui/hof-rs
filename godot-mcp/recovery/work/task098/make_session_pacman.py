# -*- coding: utf-8 -*-
"""TASK-098: build the Pac-Man session (editor + game phases).

Same shape as the Asteroids session, with the same two corrections from TASK-097:
the multi-frame samples are started BEFORE the state they are meant to observe changes,
and the scene's batch add is run twice on purpose so the D-3 refusal is part of this
game's own evidence.
"""
import io
import json
import os

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", ".."))
SESSION_DIR = os.path.join(ROOT, "tools", "sessions", "pacman")
OUT = os.path.join(SESSION_DIR, "session.json")

BG = {"type": "ColorRect", "name": "Background", "parent_path": ".",
      "properties": {"offset_left": 0, "offset_top": 0, "offset_right": 800,
                     "offset_bottom": 600, "color": {"r": 0.02, "g": 0.02, "b": 0.03, "a": 1}}}
HUD = {"type": "Label", "name": "Hud", "parent_path": ".",
       "properties": {"offset_left": 20, "offset_top": 10, "offset_right": 560,
                      "offset_bottom": 50, "text": "SCORE 0  LIVES 3  PELLETS 125",
                      "theme_override_font_sizes/font_size": 26}}
STATUS = {"type": "Label", "name": "Status", "parent_path": ".",
          "properties": {"offset_left": 570, "offset_top": 10, "offset_right": 790,
                         "offset_bottom": 50, "text": "PELLETS 125",
                         "theme_override_font_sizes/font_size": 24}}
STATIC_BATCH = [BG, HUD, STATUS]

TOTAL_PELLETS = 125

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
    g(tag, "running_game_capture_screenshot", {"save_path": "user://" + name + ".png"}, note)


# =============================================================================
# editor phase
# =============================================================================
e("e01-edit-game", "project_edit_script",
  {"path": "res://src/PacManGame.cs", "content_file": "payload/PacManGame.cs"},
  "the whole game is written through the MCP script writer (the template stub is replaced)")
e("e02-open-scene", "editor_open_scene", {"path": "res://scenes/main.tscn"},
  "the template scene carries the root Main (Node2D) the script is attached to")
e("e03-batch-add-static", "editor_add_nodes_batch", {"nodes": STATIC_BATCH},
  "the three static nodes of the scene, through the batch tool: a background and two labels; "
  "the maze walls, the 125 pellets, the four ghosts and Pac-Man are all created at run time")
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
e("e10-action-left", "editor_add_input_action", {"action": "pac_left", "key": "A"},
  "the four directions the game can poll")
e("e11-action-right", "editor_add_input_action", {"action": "pac_right", "key": "D"},
  "right")
e("e12-action-up", "editor_add_input_action", {"action": "pac_up", "key": "W"}, "up")
e("e13-action-down", "editor_add_input_action", {"action": "pac_down", "key": "S"}, "down")
e("e14-build-csharp", "project_build_csharp",
  {"configuration": "Debug", "timeout_ms": 300000, "rescan": True},
  "compile the game the MCP script writer just wrote")
e("e15-validate-scripts", "project_validate_scripts", {},
  "the engine's own per-file verdict")
e("e16-errors", "editor_get_errors", {}, "the editor log's ERROR lines after the build")

# =============================================================================
# game phase
# =============================================================================
g("g01-scene-tree", "running_game_get_scene_tree", {},
  "the running tree: the three static nodes plus the maze, the pellets, the ghosts and Pac-Man "
  "created at run time")
g("g02-readback-t0", "running_game_execute_gdscript", code("return get_parent().Dump()"),
  "the whole board as one line")
assert_state("g03-assert-score-0", "Main", "Score", "eq", 0, "nothing has been eaten yet")
assert_state("g04-assert-total", "Main", "TotalPellets", "eq", TOTAL_PELLETS,
             "the maze as written carries exactly %d pellets" % TOTAL_PELLETS)
assert_state("g05-assert-remaining", "Main", "PelletsRemaining", "eq", TOTAL_PELLETS,
             "and all of them are on the board")
assert_state("g06-assert-lives-3", "Main", "Lives", "eq", 3, "the game starts with three lives")
assert_state("g07-assert-ghosts-4", "Main", "GhostCount", "eq", 4, "four ghosts are patrolling")
assert_state("g08-assert-not-over", "Main", "GameOver", "eq", False, "the game starts alive")
shot("g09-shot-t0", "pac-t0", "the first frame: the full maze, every pellet, four ghosts and Pac-Man")
samples("g10-samples-frozen", ["Ghost0Col", "Ghost0Row", "PacCol", "Ticks"], 12,
        "determinism baseline: with GhostSpeed 0 and PollInput false nothing moves while the "
        "clock runs (ghost 0 and Pac-Man constant, Ticks increasing)")
g("g11-patrol-on", "running_game_execute_gdscript", code("return get_parent().SetGhostSpeed(8.0)"),
  "the one test that watches the ghosts patrol asks for motion explicitly")
samples("g12-samples-patrol", ["Ghost0Col", "Ghost0Row", "GhostSteps"], 30,
        "multi-frame property sample of the patrol: ghost 0's own cell changes frame by frame, "
        "because its column and row are real exported properties")
g("g13-patrol-off", "running_game_execute_gdscript", code("return get_parent().SetGhostSpeed(0.0)"),
  "back to frozen, so the next move and its readback are the same fact")
g("g14-steps-hook", "running_game_execute_gdscript", code("return get_parent().StepGhosts(12)"),
  "the fixed-step patrol hook, so a patrol count is a property of the call")
assert_state("g15-assert-patrol-took-12", "Main", "LastPatrolSteps", "eq", 12,
             "and the hook advanced the patrol by exactly that many steps -- the DELTA, because "
             "the total also carries the steps the 30-frame patrol sample above let the clock take")
assert_state("g16-assert-patrol-total-grew", "Main", "GhostSteps", "gt", 12,
             "the running total is at least the hook's 12 plus whatever the clock contributed")
# --- eating a pellet ----------------------------------------------------------
g("g17-force-eat-setup", "running_game_execute_gdscript",
  code('return get_parent().ForceTestState("pellets=10,9|5,5;pac=9,9;ghosts=none")'),
  "pin the board: exactly two pellets, Pac-Man on the empty start cell, no ghosts in the way")
assert_state("g18-assert-remaining-2", "Main", "PelletsRemaining", "eq", 2,
             "the forced board really has two pellets")
assert_state("g19-assert-eaten-0", "Main", "PelletsEaten", "eq", 0, "and none has been eaten yet")
g("g20-step-onto-pellet", "running_game_execute_gdscript", code("return get_parent().StepPac(1, 0)"),
  "one cell to the right, onto a pellet")
assert_state("g21-assert-score-10", "Main", "Score", "eq", 10, "one pellet = 10 points")
assert_state("g22-assert-remaining-1", "Main", "PelletsRemaining", "eq", 1, "and it left the board")
assert_state("g23-assert-eaten-1", "Main", "PelletsEaten", "eq", 1, "the eat counter agrees")
assert_state("g24-assert-pac-moved", "Main", "PacCol", "eq", 10, "Pac-Man really entered that cell")
shot("g25-shot-t1", "pac-t1", "after the eat: one pellet is gone from the picture and Pac-Man moved")
# --- a wall blocks a move -----------------------------------------------------
g("g26-wall-setup", "running_game_execute_gdscript",
  code('return get_parent().ForceTestState("pellets=all;pac=9,9;ghosts=none")'),
  "put the full maze back with Pac-Man on the start cell, where the cell above is a wall")
g("g27-step-into-wall", "running_game_execute_gdscript",
  code("return get_parent().StepPac(0, -1)"), "step up, into a wall")
assert_state("g28-assert-not-moved", "Main", "PacRow", "eq", 9, "a wall is not a move")
assert_state("g29-assert-still-full", "Main", "PelletsRemaining", "eq", TOTAL_PELLETS,
             "and nothing was eaten")
# --- win: eat the last pellet -------------------------------------------------
g("g30-force-last-pellet", "running_game_execute_gdscript",
  code('return get_parent().ForceTestState("pellets=10,9;pac=9,9;ghosts=none")'),
  "pin a single pellet, so 'the last pellet clears the maze' is a property of the state")
assert_state("g31-assert-remaining-1", "Main", "PelletsRemaining", "eq", 1,
             "the forced board really is one pellet")
g("g32-eat-last", "running_game_execute_gdscript", code("return get_parent().StepPac(1, 0)"),
  "eat it")
assert_state("g33-assert-won", "Main", "Won", "eq", True, "the last pellet was eaten")
assert_state("g34-assert-over-by-win", "Main", "GameOver", "eq", True, "and that is the win")
assert_state("g35-assert-remaining-0", "Main", "PelletsRemaining", "eq", 0, "the board is empty")
assert_state("g36-assert-score-10", "Main", "Score", "eq", 10, "one pellet, ten points")
g("g37-readback-won", "running_game_execute_gdscript", code("return get_parent().Dump()"),
  "the whole board at the win: no dot anywhere in it")
shot("g38-shot-t2", "pac-t2", "the win screen: the maze is empty of pellets, the label says MAZE CLEARED")
g("g39-assert-screen-text-win", "running_game_assert_screen_text", {"text": "MAZE CLEARED"},
  "the status label really is on the captured screen")
# --- losing a life ------------------------------------------------------------
g("g40-force-ghost-on-pac", "running_game_execute_gdscript",
  code('return get_parent().ForceTestState("pellets=all;pac=9,9;ghosts=10,9|1,2|17,2|17,10")'),
  "pin ghost 0 on the cell to Pac-Man's right: the loss condition is a property of the cells")
assert_state("g41-assert-lives-3", "Main", "Lives", "eq", 3, "three lives before the catch")
g("g42-step-into-ghost", "running_game_execute_gdscript", code("return get_parent().StepPac(1, 0)"),
  "step onto the ghost")
assert_state("g43-assert-lives-2", "Main", "Lives", "eq", 2, "a ghost costs exactly one life")
assert_state("g44-assert-reset", "Main", "PacCol", "eq", 9, "and both actors go back to their start")
assert_state("g45-assert-not-over", "Main", "GameOver", "eq", False, "two lives left is not a game over")
# --- the last life ------------------------------------------------------------
g("g46-force-last-life", "running_game_execute_gdscript",
  code('return get_parent().ForceTestState("pellets=all;pac=9,9;ghosts=10,9|1,2|17,2|17,10;lives=1")'),
  "pin the last life with the same ghost")
g("g47-step-into-ghost", "running_game_execute_gdscript", code("return get_parent().StepPac(1, 0)"),
  "step onto it again")
assert_state("g48-assert-lives-0", "Main", "Lives", "eq", 0, "the last life is gone")
assert_state("g49-assert-over-by-loss", "Main", "GameOver", "eq", True, "that is the loss")
assert_state("g50-assert-not-won", "Main", "Won", "eq", False, "a loss is not a win")
g("g51-readback-lost", "running_game_execute_gdscript", code("return get_parent().Dump()"),
  "the whole board at the loss")
shot("g52-shot-t3", "pac-t3", "the loss screen: the label says GAME OVER")
g("g53-assert-screen-text-loss", "running_game_assert_screen_text", {"text": "GAME OVER"},
  "the loss label really is on the captured screen")
# --- the declared input path really drives the game ---------------------------
g("g54-reset-for-input", "running_game_execute_gdscript",
  code('return get_parent().ForceTestState("pellets=all;pac=9,9;ghosts=none")'),
  "a clean board for the input test")
g("g55-poll-on", "running_game_execute_gdscript", code("return get_parent().SetPollInput(true)"),
  "the input path is off by default; the test switches it on explicitly")
g("g56-input-right", "running_game_run_test_scenario",
  {"steps": [{"type": "input", "action": "pac_right", "pressed": True},
             {"type": "wait", "seconds": 0.45},
             {"type": "assert", "node_path": "Main", "property": "PacCol",
              "operator": "gt", "expected": 9}]},
  "the declared action really moves Pac-Man, at most one cell per InputRepeat")
g("g57-poll-off", "running_game_execute_gdscript", code("return get_parent().SetPollInput(false)"),
  "polling off again: nothing after this can drift because a key is still marked held")
# --- positive control: a node created at run time is drawn --------------------
g("g58-runtime-overlay", "running_game_execute_gdscript",
  code('var main = get_parent()\nvar c = ColorRect.new()\nc.name = StringName("ProbeOverlay")\n'
       'c.position = Vector2(620, 20)\nc.size = Vector2(140, 30)\n'
       'c.color = Color(0.1, 0.95, 0.4, 1.0)\nmain.add_child(c)\nreturn "overlay added"'),
  "a node created at run time, in the same session, as the positive control for 'a run-time node "
  "is drawn' (and the 125 pellets and four ghosts are 129 more of those)")
shot("g59-shot-t4", "pac-t4", "the overlay is visible in this frame and not in t3")
g("g60-assert-unknown-property", "running_game_assert_node_state",
  {"node_path": "Main", "property": "NoSuchProperty", "operator": "eq", "expected": 1},
  "DECLARED FAILURE: a boundary call asking for a property that does not exist (-32001), so the "
  "error path of the assertion tool is on the record too")
g("g61-steps-last", "running_game_execute_gdscript", code("return get_parent().StepGhosts(5)"),
  "five more patrol steps on the final board")
assert_state("g62-assert-last-patrol-5", "Main", "LastPatrolSteps", "eq", 5,
             "the delta of that hook call is exact")
g("g63-final-readback", "running_game_execute_gdscript", code("return get_parent().Dump()"),
  "the final board as one line")
g("g64-final-tree", "running_game_get_scene_tree", {},
  "the final tree, including the run-time overlay")

doc = {"import": True, "calls": calls}
os.makedirs(os.path.dirname(OUT), exist_ok=True)
with io.open(OUT, "w", encoding="utf-8", newline="\n") as handle:
    handle.write(json.dumps(doc, ensure_ascii=False, indent=1) + "\n")
print("wrote %s calls=%d" % (OUT, len(calls)))
