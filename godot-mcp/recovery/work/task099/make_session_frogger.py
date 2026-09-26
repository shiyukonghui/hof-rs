# -*- coding: utf-8 -*-
"""TASK-099: build the Frogger session (editor + game phases).

Same shape as the TASK-098 Asteroids / Pac-Man generators, with the same three
rules the ledger recorded as the reusable template:

  * the static nodes go in through ONE editor_add_nodes_batch call;
  * the scene's batch is run a SECOND time on purpose, so the TASK-097 D-3
    refusal is part of this game's own evidence;
  * every multi-frame sample is started BEFORE the state it observes changes,
    and the state is then pinned with ONE ForceTestState call.
"""
import io
import json
import os

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", ".."))
SESSION_DIR = os.path.join(ROOT, "tools", "sessions", "frogger")
OUT = os.path.join(SESSION_DIR, "session.json")

BG = {"type": "ColorRect", "name": "Background", "parent_path": ".",
      "properties": {"offset_left": 0, "offset_top": 0, "offset_right": 800,
                     "offset_bottom": 600, "color": {"r": 0.02, "g": 0.03, "b": 0.04, "a": 1}}}
HUD = {"type": "Label", "name": "Hud", "parent_path": ".",
       "properties": {"offset_left": 20, "offset_top": 8, "offset_right": 560,
                      "offset_bottom": 46, "text": "SCORE 0  LIVES 3  HOMES 0/5",
                      "theme_override_font_sizes/font_size": 26}}
STATUS = {"type": "Label", "name": "Status", "parent_path": ".",
          "properties": {"offset_left": 560, "offset_top": 8, "offset_right": 795,
                         "offset_bottom": 46, "text": "HOMES 0/5",
                         "theme_override_font_sizes/font_size": 24}}
STATIC_BATCH = [BG, HUD, STATUS]

# The five cars start on the five road rows; index i is car i (rows 9..13).
CARS_START = "0,9|12,10|3,11|9,12|6,13"
# The five logs start on the five river rows; index i is log i (rows 3..7).
LOGS_START = "0,3|11,4|4,5|8,6|1,7"

calls = []


def e(tag, tool, arguments, note):
    calls.append({"tag": tag, "port": "editor", "tool": tool,
                  "arguments": arguments, "note": note})


def g(tag, tool, arguments, note):
    calls.append({"tag": tag, "port": "game", "tool": tool,
                  "arguments": arguments, "note": note})


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


def force(tag, spec, note):
    g(tag, "running_game_execute_gdscript",
      code('return get_parent().ForceTestState("%s")' % spec), note)


def hook(tag, expr, note):
    g(tag, "running_game_execute_gdscript", code("return get_parent()." + expr), note)


# =============================================================================
# editor phase (16 calls)
# =============================================================================
e("e01-edit-game", "project_edit_script",
  {"path": "res://src/FroggerGame.cs", "content_file": "payload/FroggerGame.cs"},
  "the whole game is written through the MCP script writer (the template stub is replaced)")
e("e02-open-scene", "editor_open_scene", {"path": "res://scenes/main.tscn"},
  "the template scene carries the root Main (Node2D) the script is attached to")
e("e03-batch-add-static", "editor_add_nodes_batch", {"nodes": STATIC_BATCH},
  "the three static nodes of the scene, through the batch tool: a background and two labels; "
  "the terrain strips, the five cars, the five logs and the frog are all created at run time")
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
e("e10-action-left", "editor_add_input_action", {"action": "frog_left", "key": "A"},
  "the four directions the frog can poll")
e("e11-action-right", "editor_add_input_action", {"action": "frog_right", "key": "D"}, "right")
e("e12-action-up", "editor_add_input_action", {"action": "frog_up", "key": "W"}, "up")
e("e13-action-down", "editor_add_input_action", {"action": "frog_down", "key": "S"}, "down")
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
  "the running tree: the three static nodes plus the strips, the cars, the logs and the frog "
  "created at run time")
g("g02-readback-t0", "running_game_execute_gdscript", code("return get_parent().Dump()"),
  "the whole board as one line")
assert_state("g03-assert-frog-col", "Main", "FrogCol", "eq", 6, "the frog starts on column 6")
assert_state("g04-assert-frog-row", "Main", "FrogRow", "eq", 14, "and on the start bank row")
assert_state("g05-assert-score-0", "Main", "Score", "eq", 0, "nothing has been scored yet")
assert_state("g06-assert-lives-3", "Main", "Lives", "eq", 3, "the game starts with three lives")
assert_state("g07-assert-homes-0", "Main", "HomesReached", "eq", 0, "no home is filled")
assert_state("g08-assert-total-homes", "Main", "TotalHomes", "eq", 5, "five homes clear the course")
assert_state("g09-assert-cars", "Main", "CarCount", "eq", 5, "one car per road lane")
assert_state("g10-assert-logs", "Main", "LogCount", "eq", 5, "one log per river row")
assert_state("g11-assert-not-over", "Main", "GameOver", "eq", False, "the game starts alive")
shot("g12-shot-t0", "frog-t0", "the first frame: the grid, the five cars, the five logs, the frog")
samples("g13-samples-frozen", ["FrogCol", "FrogRow", "Car0Col", "Log0Col", "Ticks"], 12,
        "determinism baseline: with CarSpeed 0 and PollInput false nothing moves while the clock "
        "runs (frog and both traffic heads constant, Ticks increasing)")
hook("g14-traffic-on", "SetCarSpeed(8.0)",
     "the one test that watches the traffic roll asks for motion explicitly")
samples("g15-samples-traffic", ["Car0Col", "Log0Col", "Ticks"], 30,
        "multi-frame property sample of the traffic: both heads change column frame by frame, "
        "because their cells are real exported properties")
hook("g16-traffic-off", "SetCarSpeed(0.0)",
     "back to frozen, so the next move and its readback are the same fact")
hook("g17-traffic-hook", "StepTraffic(5)",
     "the fixed-step traffic hook, so a step count is a property of the call")
assert_state("g18-assert-hook-took-5", "Main", "LastTrafficSteps", "eq", 5,
             "and the hook advanced the traffic by exactly that many steps -- the DELTA, because "
             "the total also carries the steps the 30-frame sample above let the clock take")
assert_state("g19-assert-total-grew", "Main", "TrafficSteps", "gt", 5,
             "the running total is at least the hook's 5 plus whatever the clock contributed")
# --- the board edge blocks a move ---------------------------------------------
force("g20-edge-setup", "frog=0,14;cars=none;logs=none",
      "pin the frog on the left edge with no traffic, so 'off the board' is a property of the cell")
hook("g21-step-off-board", "StepFrog(-1, 0)", "step left, off the board")
assert_state("g22-assert-not-moved-col", "Main", "FrogCol", "eq", 0, "the edge is not a move")
assert_state("g23-assert-not-moved-row", "Main", "FrogRow", "eq", 14, "and the row did not change")
# --- a road cell with no car is a safe step ------------------------------------
force("g24-road-setup", "frog=6,13;cars=none;logs=none",
      "pin the frog on the nearest road row with no cars at all")
assert_state("g25-assert-on-road", "Main", "FrogRow", "eq", 13, "the forced board really has it there")
hook("g26-step-up-road", "StepFrog(0, -1)", "one step up, from row 13 to row 12")
assert_state("g27-assert-road-moved", "Main", "FrogRow", "eq", 12,
             "an empty road cell is a move, not a hit")
# --- a car hit costs one life --------------------------------------------------
force("g28-car-setup",
      "frog=6,14;cars=%s;logs=none;lives=3" % CARS_START,
      "put car 4 on the cell above the frog, so the hit is a property of the cells")
assert_state("g29-assert-lives-3", "Main", "Lives", "eq", 3, "three lives before the hit")
hook("g30-step-into-car", "StepFrog(0, -1)", "step onto the car's cell")
assert_state("g31-assert-lives-2", "Main", "Lives", "eq", 2, "a car costs exactly one life")
assert_state("g32-assert-reset-row", "Main", "FrogRow", "eq", 14,
             "and the frog goes back to the start bank")
assert_state("g33-assert-not-over", "Main", "GameOver", "eq", False,
             "two lives left is not a game over")
shot("g34-shot-t1", "frog-t1", "after the hit: the frog is back on the start bank")
# --- a drowned frog costs one life ---------------------------------------------
force("g35-river-setup",
      "frog=6,4;cars=none;logs=%s" % LOGS_START,
      "put the frog on a river cell no log covers: row 4's log is at column 11")
assert_state("g36-assert-lives-3", "Main", "Lives", "eq", 3, "three lives before the drowning")
hook("g37-traffic-into-water", "StepTraffic(1)", "one traffic step: the frog is in the water")
assert_state("g38-assert-lives-2", "Main", "Lives", "eq", 2, "bare water costs exactly one life")
assert_state("g39-assert-reset-row", "Main", "FrogRow", "eq", 14,
             "and the frog goes back to the start bank")
# --- a log carries the frog ----------------------------------------------------
force("g40-log-setup",
      "frog=6,4;cars=none;logs=0,3|6,4|4,5|8,6|1,7",
      "put row 4's log under the frog: the carry is a property of the cells")
assert_state("g41-assert-on-log", "Main", "FrogCol", "eq", 6, "the frog starts on the log's left cell")
hook("g42-traffic-carries", "StepTraffic(1)",
     "one traffic step: log 1 moves left one cell and carries the frog with it")
assert_state("g43-assert-carried", "Main", "FrogCol", "eq", 5,
             "the frog moved with the log, not against it")
assert_state("g44-assert-still-river", "Main", "FrogRow", "eq", 4, "and is still on the log's row")
# --- the last home clears the course -------------------------------------------
force("g45-home-setup", "frog=6,1;cars=none;logs=none;homes=4",
      "pin four homes filled and the frog one step below the goal line")
assert_state("g46-assert-homes-4", "Main", "HomesReached", "eq", 4, "four homes before the step")
hook("g47-step-onto-goal", "StepFrog(0, -1)", "step onto the goal line")
assert_state("g48-assert-homes-5", "Main", "HomesReached", "eq", 5, "the fifth home is filled")
assert_state("g49-assert-score-50", "Main", "Score", "eq", 50, "one home = 50 points")
assert_state("g50-assert-won", "Main", "Won", "eq", True, "five homes clear the course")
assert_state("g51-assert-over-by-win", "Main", "GameOver", "eq", True, "and that is the win")
hook("g52-readback-won", "Dump()", "the whole board at the win")
shot("g53-shot-t2", "frog-t2", "the win screen: the status label says ALL HOMES FILLED")
g("g54-assert-screen-text-win", "running_game_assert_screen_text", {"text": "ALL HOMES FILLED"},
  "the status label really is on the captured screen")
# --- the last life by a car ----------------------------------------------------
force("g55-loss-setup",
      "frog=6,14;cars=%s;logs=none;lives=1" % CARS_START,
      "pin the last life with the same car above the frog")
hook("g56-step-into-car", "StepFrog(0, -1)", "step onto it again")
assert_state("g57-assert-lives-0", "Main", "Lives", "eq", 0, "the last life is gone")
assert_state("g58-assert-over-by-loss", "Main", "GameOver", "eq", True, "that is the loss")
assert_state("g59-assert-not-won", "Main", "Won", "eq", False, "a loss is not a win")
hook("g60-readback-lost", "Dump()", "the whole board at the loss")
shot("g61-shot-t3", "frog-t3", "the loss screen: the status label says GAME OVER")
g("g62-assert-screen-text-loss", "running_game_assert_screen_text", {"text": "GAME OVER"},
  "the loss label really is on the captured screen")
# --- the declared input path really drives the game ---------------------------
force("g63-reset-for-input", "frog=6,14;cars=none;logs=none", "a clean board for the input test")
hook("g64-poll-on", "SetPollInput(true)",
     "the input path is off by default; the test switches it on explicitly")
g("g65-input-up", "running_game_run_test_scenario",
  {"steps": [{"type": "input", "action": "frog_up", "pressed": True},
             {"type": "wait", "seconds": 0.45},
             {"type": "assert", "node_path": "Main", "property": "FrogRow",
              "operator": "lt", "expected": 14}]},
  "the declared action really moves the frog, at most one cell per InputRepeat")
hook("g66-poll-off", "SetPollInput(false)",
     "polling off again: nothing after this can drift because a key is still marked held")
# --- positive control: a node created at run time is drawn --------------------
g("g67-runtime-overlay", "running_game_execute_gdscript",
  code('var main = get_parent()\nvar c = ColorRect.new()\nc.name = StringName("ProbeOverlay")\n'
       'c.position = Vector2(20, 552)\nc.size = Vector2(120, 34)\n'
       'c.color = Color(0.95, 0.35, 0.95, 1.0)\nmain.add_child(c)\nreturn "overlay added"'),
  "a node created at run time, in the same session, as the positive control for 'a run-time node "
  "is drawn' (and the five cars, five logs and the frog are eleven more of those)")
# --- DECLARED FAILURE: the error path of the assertion tool --------------------
g("g68-assert-unknown-property", "running_game_assert_node_state",
  {"node_path": "Main", "property": "NoSuchProperty", "operator": "eq", "expected": 1},
  "DECLARED FAILURE: a boundary call asking for a property that does not exist (-32001), so the "
  "error path of the assertion tool is on the record too")
# --- final: the overlay frame and the exact step hook --------------------------
shot("g69-shot-t4", "frog-t4", "the overlay is visible in this frame and not in t3")
force("g70-final-setup", "frog=6,14;cars=none;logs=none", "a clean board for the final readback")
hook("g71-traffic-hook-3", "StepTraffic(3)", "three more traffic steps on the final board")
assert_state("g72-assert-last-3", "Main", "LastTrafficSteps", "eq", 3,
             "the delta of that hook call is exact")
hook("g73-final-readback", "Dump()", "the final board as one line")
g("g74-final-tree", "running_game_get_scene_tree", {},
  "the final tree, including the run-time overlay")

doc = {"import": True, "calls": calls}
os.makedirs(os.path.dirname(OUT), exist_ok=True)
with io.open(OUT, "w", encoding="utf-8", newline="\n") as handle:
    handle.write(json.dumps(doc, ensure_ascii=False, indent=1) + "\n")
print("wrote %s calls=%d" % (OUT, len(calls)))
