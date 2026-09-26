# -*- coding: utf-8 -*-
"""TASK-100: build the 2048 session (editor + game phases).

Same shape as the TASK-098 / TASK-099 generators, with the same rules the ledger
recorded as the reusable template:

  * the static nodes go in through ONE editor_add_nodes_batch call;
  * the scene's batch is run a SECOND time on purpose, so the TASK-097 D-3
    refusal is part of this game's own evidence;
  * every multi-frame sample is started BEFORE the state it observes changes,
    and the state is then pinned with ONE ForceTestState call;
  * any clock is a FLOAT ACCUMULATOR (Elapsed += delta, _autoAccum += delta*rate),
    never (int)(delta*rate) -- the F-1 lesson -- and the frame-rate independent
    delta (LastAutoSteps) is its own exported property.
"""
import io
import json
import os

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", ".."))
SESSION_DIR = os.path.join(ROOT, "tools", "sessions", "game2048")
OUT = os.path.join(SESSION_DIR, "session.json")

BG = {"type": "ColorRect", "name": "Background", "parent_path": ".",
      "properties": {"offset_left": 0, "offset_top": 0, "offset_right": 800,
                     "offset_bottom": 600, "color": {"r": 0.04, "g": 0.04, "b": 0.06, "a": 1}}}
HUD = {"type": "Label", "name": "Hud", "parent_path": ".",
       "properties": {"offset_left": 20, "offset_top": 8, "offset_right": 560,
                      "offset_bottom": 46, "text": "SCORE 0  MOVES 0  MAX 0",
                      "theme_override_font_sizes/font_size": 26}}
STATUS = {"type": "Label", "name": "Status", "parent_path": ".",
          "properties": {"offset_left": 560, "offset_top": 8, "offset_right": 795,
                         "offset_bottom": 46, "text": "JOIN THE TILES",
                         "theme_override_font_sizes/font_size": 24}}
STATIC_BATCH = [BG, HUD, STATUS]

ZERO = "0,0,0,0|0,0,0,0|0,0,0,0|0,0,0,0"
AUTO_GRID = "0,0,0,2|0,0,0,0|0,0,0,0|4,0,0,0"

calls = []


def e(tag, tool, arguments, note):
    calls.append({"tag": tag, "port": "editor", "tool": tool,
                  "arguments": arguments, "note": note})


def g(tag, tool, arguments, note):
    calls.append({"tag": tag, "port": "game", "tool": tool,
                  "arguments": arguments, "note": note})


def code(expr):
    return {"code": expr}


def assert_state(tag, prop, op, expected, note):
    g(tag, "running_game_assert_node_state",
      {"node_path": "Main", "property": prop, "operator": op, "expected": expected}, note)


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
  {"path": "res://src/Game2048Game.cs", "content_file": "payload/Game2048Game.cs"},
  "the whole game is written through the MCP script writer (the template stub is replaced)")
e("e02-open-scene", "editor_open_scene", {"path": "res://scenes/main.tscn"},
  "the template scene carries the root Main (Node2D) the script is attached to")
e("e03-batch-add-static", "editor_add_nodes_batch", {"nodes": STATIC_BATCH},
  "the three static nodes of the scene, through the batch tool: a background and two labels; "
  "the board frame and all sixteen tiles are created at run time")
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
e("e10-action-up", "editor_add_input_action", {"action": "m2048_up", "key": "W"}, "the four directions")
e("e11-action-right", "editor_add_input_action", {"action": "m2048_right", "key": "D"}, "right")
e("e12-action-down", "editor_add_input_action", {"action": "m2048_down", "key": "S"}, "down")
e("e13-action-left", "editor_add_input_action", {"action": "m2048_left", "key": "A"}, "left")
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
  "the running tree: the three static nodes plus the board frame and the sixteen tiles created "
  "at run time")
hook("g02-readback-t0", "Dump()", "the whole board as one line")
assert_state("g03-assert-cols", "Cols", "eq", 4, "the board is four columns wide")
assert_state("g04-assert-rows", "Rows", "eq", 4, "and four rows tall")
assert_state("g05-assert-target", "TargetTile", "eq", 2048, "2048 is the winning tile")
assert_state("g06-assert-used-0", "TilesInUse", "eq", 0, "the board starts empty")
assert_state("g07-assert-empty-16", "EmptyCells", "eq", 16, "so all sixteen cells are free")
assert_state("g08-assert-max-0", "MaxTile", "eq", 0, "no tile yet")
assert_state("g09-assert-score-0", "Score", "eq", 0, "nothing has been scored yet")
assert_state("g10-assert-moves-0", "MoveCount", "eq", 0, "no move has been made")
assert_state("g11-assert-can-move", "CanMoveAny", "eq", True, "an empty board always has a move")
assert_state("g12-assert-over-0", "GameOver", "eq", False, "the game starts alive")
assert_state("g13-assert-won-0", "Won", "eq", False, "and unwon")
shot("g14-shot-t0", "g2048-t0", "the first frame: the empty 4x4 board, the HUD and the status label")
samples("g15-samples-frozen", ["GridHash", "TilesInUse", "MoveCount", "Elapsed", "Ticks"], 12,
        "determinism baseline: with AutoPlay 0 nothing on the board moves while the clock runs "
        "(grid hash and move count constant, Elapsed and Ticks both increasing)")
assert_state("g16-assert-last-auto-0", "LastAutoSteps", "eq", 0,
             "the auto-play delta is zero while the clock is off")
# --- left: 2,2 merges into 4 and the original 4 stays -------------------------
force("g17-left-setup", "grid=2,2,4,0|0,0,0,0|0,0,0,0|0,0,0,0",
      "pin one row with a mergeable pair and a lone 4")
assert_state("g18-assert-grid-before", "GridString", "eq",
             "2,2,4,0/0,0,0,0/0,0,0,0/0,0,0,0", "the forced row really is on the board")
assert_state("g19-assert-used-3", "TilesInUse", "eq", 3, "three tiles")
hook("g20-move-left", "Move(3)", "one left move")
assert_state("g21-assert-grid-after", "GridString", "eq",
             "4,4,0,0/0,0,0,0/0,0,0,0/0,0,0,0",
             "the pair merged into a 4 at the left edge and the lone 4 slid next to it")
assert_state("g22-assert-score-4", "Score", "eq", 4, "the merge scored its own value")
assert_state("g23-assert-last-gain", "LastMoveGain", "eq", 4, "the delta of that call is exact")
assert_state("g24-assert-last-merges", "LastMoveMerges", "eq", 1, "exactly one merge")
assert_state("g25-assert-moves-1", "MoveCount", "eq", 1, "one accepted move")
assert_state("g26-assert-rejected-0", "MovesRejected", "eq", 0, "and nothing refused")
assert_state("g27-assert-max-4", "MaxTile", "eq", 4, "the largest tile is the new 4")
assert_state("g28-assert-moved-true", "LastMoveMoved", "eq", True, "the move really changed the board")
# --- second left merges 4,4 into 8 --------------------------------------------
hook("g29-move-left-2", "Move(3)", "a second left move")
assert_state("g30-assert-grid-8", "GridString", "eq",
             "8,0,0,0/0,0,0,0/0,0,0,0/0,0,0,0", "the two 4s merged into an 8")
assert_state("g31-assert-score-12", "Score", "eq", 12, "4 + 8")
assert_state("g32-assert-merges-2", "TotalMerges", "eq", 2, "two merges over the game")
assert_state("g33-assert-moves-2", "MoveCount", "eq", 2, "two accepted moves")
shot("g34-shot-t1", "g2048-t1", "after two merges: one 8 at the top left corner")
# --- an illegal move: the board is already packed left ------------------------
hook("g35-move-left-3", "Move(3)", "a third left move changes nothing")
assert_state("g36-assert-moves-still-2", "MoveCount", "eq", 2,
             "the illegal move was refused: the move count did not grow")
assert_state("g37-assert-rejected-1", "MovesRejected", "eq", 1, "it is counted as one refusal")
assert_state("g38-assert-moved-false", "LastMoveMoved", "eq", False, "and reported as not moving")
assert_state("g39-assert-grid-unchanged", "GridString", "eq",
             "8,0,0,0/0,0,0,0/0,0,0,0/0,0,0,0", "the board is exactly as it was")
assert_state("g40-assert-reason", "LastEvent", "contains", "rejected reason=no_change",
             "and the refusal says why")
hook("g41-move-up", "Move(0)", "an up move on the same left-packed board is refused too")
assert_state("g42-assert-rejected-2", "MovesRejected", "eq", 2, "a second refusal")
assert_state("g43-assert-grid-still", "GridString", "eq",
             "8,0,0,0/0,0,0,0/0,0,0,0/0,0,0,0", "still byte-for-byte the same board")
# --- right: the same pair packs to the right edge ------------------------------
force("g44-right-setup", "grid=2,2,4,0|0,0,0,0|0,0,0,0|0,0,0,0", "the same row again")
hook("g45-move-right", "Move(1)", "one right move")
assert_state("g46-assert-grid-right", "GridString", "eq",
             "0,0,4,4/0,0,0,0/0,0,0,0/0,0,0,0",
             "the pair merged at the right edge, so right is a real second direction")
assert_state("g47-assert-score-right", "Score", "eq", 4, "the merge scored once")
# --- up: a column merges --------------------------------------------------------
force("g48-up-setup", "grid=2,0,0,0|2,0,0,0|4,0,0,0|0,0,0,0", "a column with a mergeable pair")
hook("g49-move-up", "Move(0)", "one up move")
assert_state("g50-assert-grid-up", "GridString", "eq",
             "4,0,0,0/4,0,0,0/0,0,0,0/0,0,0,0", "the column packed upward and merged")
assert_state("g51-assert-score-up", "Score", "eq", 4, "the merge scored once")
assert_state("g52-assert-merges-up", "LastMoveMerges", "eq", 1, "one merge")
# --- down: the same column packs downward ---------------------------------------
force("g53-down-setup", "grid=2,0,0,0|2,0,0,0|4,0,0,0|0,0,0,0", "the same column again")
hook("g54-move-down", "Move(2)", "one down move")
assert_state("g55-assert-grid-down", "GridString", "eq",
             "0,0,0,0/0,0,0,0/4,0,0,0/4,0,0,0", "the column packed downward and merged")
assert_state("g56-assert-score-down", "Score", "eq", 4, "the merge scored once")
# --- reaching 2048 is the win ---------------------------------------------------
force("g57-win-setup", "grid=1024,1024,0,0|0,0,0,0|0,0,0,0|0,0,0,0",
      "two 1024 tiles are one left move away from the target")
assert_state("g58-assert-max-before", "MaxTile", "eq", 1024, "1024 is the largest tile")
assert_state("g59-assert-not-won-yet", "Won", "eq", False, "and the target is not reached")
hook("g60-move-into-2048", "Move(3)", "merge them")
assert_state("g61-assert-max-2048", "MaxTile", "eq", 2048, "the merged tile is the target")
assert_state("g62-assert-won", "Won", "eq", True, "reaching the target is the win")
assert_state("g63-assert-not-over-yet", "GameOver", "eq", False,
             "a win alone does not end the game: there are still empty cells to move into")
assert_state("g64-assert-gain-2048", "LastMoveGain", "eq", 2048, "the merge scored its own value")
assert_state("g65-assert-score-2048", "Score", "eq", 2048, "and that is the whole score")
shot("g66-shot-t2", "g2048-t2", "the win screen: one 2048 tile and the status label on 2048 REACHED")
g("g67-assert-screen-text-win", "running_game_assert_screen_text", {"text": "2048 REACHED"},
  "the status label really is on the captured screen")
# --- a full board with no legal move is the loss --------------------------------
force("g68-loss-setup", "grid=2,4,2,4|4,2,4,2|2,4,2,4|4,2,4,2",
      "a full checkerboard: no two orthogonal neighbours are equal")
assert_state("g69-assert-full", "TilesInUse", "eq", 16, "all sixteen cells carry a tile")
assert_state("g70-assert-empty-0", "EmptyCells", "eq", 0, "none is free")
assert_state("g71-assert-cannot-move", "CanMoveAny", "eq", False, "and no direction would change it")
assert_state("g72-assert-over", "GameOver", "eq", True, "so the game is over")
assert_state("g73-assert-not-won", "Won", "eq", False, "a loss is not a win")
hook("g74-move-when-over", "Move(3)", "every move is refused once the game is over")
assert_state("g75-assert-rejected-1", "MovesRejected", "eq", 1, "the refusal is counted")
assert_state("g76-assert-moves-0", "MoveCount", "eq", 0, "no move was accepted")
assert_state("g77-assert-grid-loss", "GridString", "eq",
             "2,4,2,4/4,2,4,2/2,4,2,4/4,2,4,2", "and the board did not change")
assert_state("g78-assert-reason-over", "LastEvent", "contains", "reason=game_over",
             "the refusal names the game-over rule")
shot("g79-shot-t3", "g2048-t3", "the loss screen: a full checkerboard and NO MOVES LEFT")
g("g80-assert-screen-text-loss", "running_game_assert_screen_text", {"text": "NO MOVES LEFT"},
  "the status label really is on the captured screen")
# --- a full board that still has a merge is NOT over ----------------------------
force("g81-merge-full-setup", "grid=2,2,4,8|4,8,16,32|2,4,8,16|4,8,16,32",
      "a full board whose only legal move is the merge on the top row")
assert_state("g82-assert-full-2", "TilesInUse", "eq", 16, "sixteen tiles")
assert_state("g83-assert-can-still-move", "CanMoveAny", "eq", True,
             "a full board with an equal neighbour is not stuck")
assert_state("g84-assert-not-over-2", "GameOver", "eq", False, "so it is not a loss")
# --- the frame-rate independent increment: one hook call, one exact delta -------
force("g85-autostep-setup", "grid=%s" % AUTO_GRID,
      "two tiles in opposite corners, so the deterministic policy has two legal moves in a row")
assert_state("g86-assert-moves-0", "MoveCount", "eq", 0, "a clean counter")
hook("g87-autostep-2", "AutoStep(2)", "exactly two deterministic auto-play moves")
assert_state("g88-assert-last-hook-2", "LastHookSteps", "eq", 2,
             "the DELTA of that call is exact -- this is the frame-rate independent quantity")
assert_state("g88b-assert-last-auto-0", "LastAutoSteps", "eq", 0,
             "and it is a DIFFERENT property from the clock's own per-frame delta, which is 0 while "
             "the clock is off: r1 of this game read 0 here because one property had two writers")
assert_state("g89-assert-auto-total-2", "AutoSteps", "eq", 2, "and the total agrees")
assert_state("g90-assert-moves-2", "MoveCount", "eq", 2, "the board really moved twice")
assert_state("g91-assert-no-merge", "Score", "eq", 0, "neither of those two moves merged anything")
# --- multi-frame sample of the auto-play CLOCK: the board really moves ----------
force("g92-autoclock-setup", "grid=%s" % AUTO_GRID, "the same two-corner board again")
hook("g93-autoplay-on", "SetAutoPlay(120.0)",
     "the one sample that watches the board move asks for motion explicitly")
samples("g94-samples-autoplay",
        ["MoveCount", "GridHash", "AutoSteps", "LastAutoSteps", "Elapsed", "Ticks"], 30,
        "multi-frame property sample of the auto-play clock: the move count and the grid hash "
        "change frame by frame while Elapsed and Ticks advance -- 'the board moves' as a sequence "
        "of values, not as an adjective")
assert_state("g95-assert-moves-grew", "MoveCount", "gt", 2,
             "the clock pushed the board past the two moves the hook made")
assert_state("g96-assert-grid-changed", "AutoSteps", "gt", 2, "and the clock's own total grew")
hook("g97-autoplay-off", "SetAutoPlay(0.0)", "back to frozen")
assert_state("g98-assert-last-auto-0", "LastAutoSteps", "eq", 0, "the per-frame delta is zero again")
shot("g99-shot-t4", "g2048-t4", "the board after the auto-play sample: the two tiles have moved")
# --- the declared input path really drives the game -----------------------------
force("g100-input-setup", "grid=%s" % AUTO_GRID, "a clean board for the input test")
hook("g101-poll-on", "SetPollInput(true)",
     "the input path is off by default; the test switches it on explicitly")
g("g102-input-left", "running_game_run_test_scenario",
  {"steps": [{"type": "input", "action": "m2048_left", "pressed": True},
             {"type": "wait", "seconds": 0.45},
             {"type": "assert", "node_path": "Main", "property": "MoveCount",
              "operator": "gt", "expected": 0}]},
  "the declared action really moves the board")
assert_state("g103-assert-input-moves-1", "InputMoves", "eq", 1,
             "the declared action fires on the PRESS EDGE, so a scenario's never-released key "
             "performs exactly one move instead of repeating at the frame rate")
hook("g104-poll-off", "SetPollInput(false)",
     "polling off again: nothing after this can drift because a key is still marked held")
# --- positive control: a node created at run time is drawn ----------------------
g("g105-runtime-overlay", "running_game_execute_gdscript",
  code('var main = get_parent()\nvar c = ColorRect.new()\nc.name = StringName("ProbeOverlay")\n'
       'c.position = Vector2(20, 552)\nc.size = Vector2(120, 34)\n'
       'c.color = Color(0.95, 0.35, 0.95, 1.0)\nmain.add_child(c)\nreturn "overlay added"'),
  "a node created at run time, in the same session, as the positive control for 'a run-time node "
  "is drawn' (and the sixteen tiles are sixteen more of those)")
# --- DECLARED FAILURE: the error path of the assertion tool ---------------------
g("g106-assert-unknown-property", "running_game_assert_node_state",
  {"node_path": "Main", "property": "NoSuchProperty", "operator": "eq", "expected": 1},
  "DECLARED FAILURE: a boundary call asking for a property that does not exist (-32001), so the "
  "error path of the assertion tool is on the record too")
# --- final: the overlay frame and one more exact step hook ----------------------
shot("g107-shot-t5", "g2048-t5", "the overlay is visible in this frame and not in t4")
force("g108-final-setup", "grid=%s" % AUTO_GRID, "a clean board for the final readback")
hook("g109-autostep-3", "AutoStep(3)", "three more deterministic auto-play moves")
assert_state("g110-assert-last-hook-3", "LastHookSteps", "eq", 3,
             "the delta of that hook call is exact")
hook("g111-final-readback", "Dump()", "the final board as one line")
g("g112-final-tree", "running_game_get_scene_tree", {},
  "the final tree, including the run-time overlay")

doc = {"import": True, "calls": calls}
os.makedirs(os.path.dirname(OUT), exist_ok=True)
with io.open(OUT, "w", encoding="utf-8", newline="\n") as handle:
    handle.write(json.dumps(doc, ensure_ascii=False, indent=1) + "\n")
print("wrote %s calls=%d" % (OUT, len(calls)))
