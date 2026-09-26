# -*- coding: utf-8 -*-
"""TASK-099: build the Flappy Bird session (editor + game phases).

Same shape as the TASK-098 Asteroids / Pac-Man generators and as the Frogger one
written in the same task:

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
SESSION_DIR = os.path.join(ROOT, "tools", "sessions", "flappy")
OUT = os.path.join(SESSION_DIR, "session.json")

BG = {"type": "ColorRect", "name": "Background", "parent_path": ".",
      "properties": {"offset_left": 0, "offset_top": 0, "offset_right": 800,
                     "offset_bottom": 600, "color": {"r": 0.05, "g": 0.10, "b": 0.20, "a": 1}}}
HUD = {"type": "Label", "name": "Hud", "parent_path": ".",
       "properties": {"offset_left": 20, "offset_top": 8, "offset_right": 580,
                      "offset_bottom": 46, "text": "SCORE 0  PASSED 0/5  FRAME 0",
                      "theme_override_font_sizes/font_size": 26}}
STATUS = {"type": "Label", "name": "Status", "parent_path": ".",
          "properties": {"offset_left": 560, "offset_top": 8, "offset_right": 795,
                         "offset_bottom": 46, "text": "PIPES 0/5",
                         "theme_override_font_sizes/font_size": 24}}
STATIC_BATCH = [BG, HUD, STATUS]

ALL_PIPES_GAP300 = "600:300|900:300|1200:300"
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
  {"path": "res://src/FlappyBirdGame.cs", "content_file": "payload/FlappyBirdGame.cs"},
  "the whole game is written through the MCP script writer (the template stub is replaced)")
e("e02-open-scene", "editor_open_scene", {"path": "res://scenes/main.tscn"},
  "the template scene carries the root Main (Node2D) the script is attached to")
e("e03-batch-add-static", "editor_add_nodes_batch", {"nodes": STATIC_BATCH},
  "the three static nodes of the scene, through the batch tool: a background and two labels; "
  "the bird and the three pipes are all created at run time")
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
e("e10-action-flap", "editor_add_input_action", {"action": "flap", "key": "Space"},
  "the one action the bird polls")
e("e11-action-restart", "editor_add_input_action", {"action": "flappy_restart", "key": "R"},
  "a second action, so this game's input map has a real neighbour for flap")
e("e12-build-csharp", "project_build_csharp",
  {"configuration": "Debug", "timeout_ms": 300000, "rescan": True},
  "compile the game the MCP script writer just wrote")
e("e13-validate-scripts", "project_validate_scripts", {},
  "the engine's own per-file verdict")
e("e14-errors", "editor_get_errors", {}, "the editor log's ERROR lines after the build")

# =============================================================================
# game phase
# =============================================================================
g("g01-scene-tree", "running_game_get_scene_tree", {},
  "the running tree: the three static nodes plus the bird and the three pipes created at run time")
g("g02-readback-t0", "running_game_execute_gdscript", code("return get_parent().Dump()"),
  "the whole world as one line")
assert_state("g03-assert-bird-y", "Main", "BirdY", "eq", 300, "the bird starts at its launch height")
assert_state("g04-assert-velocity", "Main", "BirdVelocity", "eq", 0, "and is not moving yet")
assert_state("g05-assert-score-0", "Main", "Score", "eq", 0, "no pipe has been passed")
assert_state("g06-assert-passed-0", "Main", "PipesPassed", "eq", 0, "the counter agrees")
assert_state("g07-assert-pipes", "Main", "PipeCount", "eq", 3, "three pipes on the screen")
assert_state("g08-assert-to-clear", "Main", "PipesToClear", "eq", 5, "five pipes clear the course")
assert_state("g09-assert-gravity", "Main", "Gravity", "eq", 1400, "the gravity is the declared one")
assert_state("g10-assert-frames-0", "Main", "FrameCount", "eq", 0,
             "no fixed frame has been simulated yet")
assert_state("g11-assert-not-over", "Main", "GameOver", "eq", False, "the game starts alive")
shot("g12-shot-t0", "flappy-t0", "the first frame: the bird and the three pipes")
samples("g13-samples-frozen", ["BirdY", "Pipe0X", "Ticks"], 12,
        "determinism baseline: with AutoRun false the world does NOT advance -- the bird and the "
        "pipes are constant while the engine's own frame counter runs")
# --- a flap really moves the bird ----------------------------------------------
hook("g14-flap", "Flap()", "the one input the game has, through the fixed-step hook")
assert_state("g15-assert-flap-velocity", "Main", "BirdVelocity", "eq", -420,
             "a flap sets the velocity to exactly the upward impulse")
hook("g16-step-10", "StepFrames(10)", "ten exact 1/60 s frames of gravity on that velocity")
assert_state("g17-assert-rose", "Main", "BirdY", "lt", 300, "the bird is still above its start")
assert_state("g18-assert-velocity-spent", "Main", "BirdVelocity", "lt", 0,
             "and gravity has not spent the whole flap yet")
# --- gravity alone --------------------------------------------------------------
force("g19-gravity-setup", "bird=100,0;pipes=none",
      "pin the bird and remove the pipes, so the fall is the only thing happening")
hook("g20-step-1", "StepFrames(1)", "one frame of free fall")
assert_state("g21-assert-velocity", "Main", "BirdVelocity", "gt", 23,
             "one frame of 1400 px/s^2 at 60 fps is 23.33 px/s")
assert_state("g22-assert-fell", "Main", "BirdY", "gt", 100, "and the bird moved down")
# --- the ceiling is a clamp, not a death ---------------------------------------
force("g23-ceiling-setup", "bird=5,-400;pipes=none", "pin the bird above the ceiling, rising")
hook("g24-step-ceiling", "StepFrames(1)", "one frame into the ceiling")
assert_state("g25-assert-clamped", "Main", "BirdY", "eq", 0,
             "the ceiling clamps the bird to y = 0")
assert_state("g26-assert-velocity-zero", "Main", "BirdVelocity", "eq", 0,
             "and kills the upward velocity")
# --- the ground ends the run ----------------------------------------------------
force("g27-ground-setup", "bird=560,400;pipes=none", "pin the bird just above the ground, falling")
hook("g28-step-ground", "StepFrames(10)", "let it fall")
assert_state("g29-assert-over", "Main", "GameOver", "eq", True, "the ground is the loss")
assert_state("g30-assert-not-won", "Main", "Won", "eq", False, "a ground hit is not a win")
assert_state("g31-assert-resting", "Main", "BirdY", "eq", 564,
             "and the bird rests exactly one body above the world's floor")
shot("g32-shot-t1", "flappy-t1", "the loss screen: the status label says GAME OVER")
g("g33-assert-screen-text-loss", "running_game_assert_screen_text", {"text": "GAME OVER"},
  "the loss label really is on the captured screen")
# --- a pipe hit ends the run ----------------------------------------------------
force("g34-pipe-setup", "bird=100,0;pipes=160:300|900:210|1200:390",
      "pin pipe 0 so its body covers the bird's column, with the gap far below the bird")
hook("g35-step-collide", "StepFrames(1)", "one frame into the pipe")
assert_state("g36-assert-over", "Main", "GameOver", "eq", True, "the pipe is the loss")
assert_state("g37-assert-not-won", "Main", "Won", "eq", False, "a pipe hit is not a win")
assert_state("g38-assert-no-score", "Main", "Score", "eq", 0, "and nothing was scored by hitting it")
# --- the world scrolls only when the clock is on --------------------------------
force("g39-scroll-setup", "bird=300,0;pipes=%s;gravity=0;speed=180" % ALL_PIPES_GAP300,
      "pin the bird in the middle of all three gaps, with gravity 0 so the bird cannot fall")
assert_state("g40-assert-pipe0-x", "Main", "Pipe0X", "eq", 600, "pipe 0 is where it was pinned")
hook("g41-step-5", "StepFrames(5)", "five frames of scroll at 180 px/s = 3 px per frame")
assert_state("g42-assert-scrolled", "Main", "Pipe0X", "eq", 585,
             "the world really moved exactly 15 px")
hook("g43-autorun-on", "SetAutoRun(true)",
     "the self-running clock is switched on explicitly for the multi-frame sample")
samples("g44-samples-scroll", ["Pipe0X", "BirdY", "Ticks"], 30,
        "multi-frame property sample of the scroll: pipe 0 changes frame by frame while the bird "
        "stays on its line, because both are real exported properties")
hook("g45-autorun-off", "SetAutoRun(false)", "back to frozen, so the next aim and readback agree")
# --- passing a pipe scores, and the fifth clears the course ---------------------
force("g46-pass-setup", "bird=300,0;pipes=%s;gravity=0;speed=180" % ALL_PIPES_GAP300,
      "pin the bird in the gaps and pin the three pipes back to their start x")
assert_state("g47-assert-pipe0-x", "Main", "Pipe0X", "eq", 600, "pipe 0 is back at 600")
hook("g48-until-pass-1", "StepUntilPass(400)", "step until the first pipe is behind the bird")
assert_state("g49-assert-delta-1", "Main", "LastPassDelta", "eq", 1, "exactly one pipe was passed")
assert_state("g50-assert-frames-164", "Main", "LastPassFrames", "eq", 164,
             "and it took exactly 164 fixed frames -- the deterministic value")
assert_state("g51-assert-passed-1", "Main", "PipesPassed", "eq", 1, "the counter agrees")
assert_state("g52-assert-score-10", "Main", "Score", "eq", 10, "one pipe = 10 points")
hook("g53-until-pass-2", "StepUntilPass(400)", "the second pipe")
assert_state("g54-assert-frames-100", "Main", "LastPassFrames", "eq", 100,
             "the spacing makes the next pass 100 frames away")
assert_state("g55-assert-score-20", "Main", "Score", "eq", 20, "two pipes = 20 points")
shot("g56-shot-t2", "flappy-t2", "two pipes passed: the score label and the pipe layout moved")
hook("g57-until-pass-3", "StepUntilPass(400)", "the third pipe")
assert_state("g58-assert-passed-3", "Main", "PipesPassed", "eq", 3, "three pipes passed")
hook("g59-until-pass-4", "StepUntilPass(400)", "the first recycled pipe")
assert_state("g60-assert-passed-4", "Main", "PipesPassed", "eq", 4, "four pipes passed")
assert_state("g61-assert-recycled", "Main", "PipesRecycled", "gt", 0,
             "the pipes really were recycled to the right edge")
hook("g62-until-pass-5", "StepUntilPass(400)", "the fifth pipe")
assert_state("g63-assert-passed-5", "Main", "PipesPassed", "eq", 5, "all five pipes are passed")
assert_state("g64-assert-score-50", "Main", "Score", "eq", 50, "five pipes = 50 points")
assert_state("g65-assert-won", "Main", "Won", "eq", True, "passing every pipe clears the course")
assert_state("g66-assert-over-by-win", "Main", "GameOver", "eq", True, "and that is the win")
hook("g67-readback-won", "Dump()", "the whole world at the win")
shot("g68-shot-t3", "flappy-t3", "the win screen: the status label says COURSE CLEARED")
g("g69-assert-screen-text-win", "running_game_assert_screen_text", {"text": "COURSE CLEARED"},
  "the win label really is on the captured screen")
# --- DECLARED FAILURE: the error path of the assertion tool --------------------
g("g70-assert-unknown-property", "running_game_assert_node_state",
  {"node_path": "Main", "property": "NoSuchProperty", "operator": "eq", "expected": 1},
  "DECLARED FAILURE: a boundary call asking for a property that does not exist (-32001), so the "
  "error path of the assertion tool is on the record too")
# --- the declared input path really drives the game ---------------------------
force("g71-reset-for-input", "bird=300,0;pipes=none;gravity=0", "a clean world for the input test")
hook("g72-poll-on", "SetPollInput(true)",
     "the input path is off by default; the test switches it on explicitly")
g("g73-input-flap", "running_game_run_test_scenario",
  {"steps": [{"type": "input", "action": "flap", "pressed": True},
             {"type": "wait", "seconds": 0.25},
             {"type": "assert", "node_path": "Main", "property": "BirdVelocity",
              "operator": "lt", "expected": 0}]},
  "the declared action really flaps the bird (its velocity becomes the upward impulse)")
hook("g74-poll-off", "SetPollInput(false)",
     "polling off again: nothing after this can drift because a key is still marked held")
# --- positive control: a node created at run time is drawn --------------------
g("g75-runtime-overlay", "running_game_execute_gdscript",
  code('var main = get_parent()\nvar c = ColorRect.new()\nc.name = StringName("ProbeOverlay")\n'
       'c.position = Vector2(20, 552)\nc.size = Vector2(120, 34)\n'
       'c.color = Color(0.95, 0.35, 0.95, 1.0)\nmain.add_child(c)\nreturn "overlay added"'),
  "a node created at run time, in the same session, as the positive control for 'a run-time node "
  "is drawn' (and the bird and the three pipes are four more of those)")
shot("g76-shot-t4", "flappy-t4", "the overlay is visible in this frame and not in t3")
hook("g77-final-readback", "Dump()", "the final world as one line")
g("g78-final-tree", "running_game_get_scene_tree", {},
  "the final tree, including the run-time overlay")

doc = {"import": True, "calls": calls}
os.makedirs(os.path.dirname(OUT), exist_ok=True)
with io.open(OUT, "w", encoding="utf-8", newline="\n") as handle:
    handle.write(json.dumps(doc, ensure_ascii=False, indent=1) + "\n")
print("wrote %s calls=%d" % (OUT, len(calls)))
