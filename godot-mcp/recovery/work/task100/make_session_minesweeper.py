# -*- coding: utf-8 -*-
"""TASK-100: build the Minesweeper session (editor + game phases).

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

The default minefield is a pure function of the seed (a fixed LCG), so this
generator recomputes the layout with the SAME rule in Python and bakes the
expected `MineList` literal into the session: the assertion is an independent
recomputation of the payload's placement rule, not a transcription of it.
"""
import io
import json
import os

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", ".."))
SESSION_DIR = os.path.join(ROOT, "tools", "sessions", "minesweeper")
OUT = os.path.join(SESSION_DIR, "session.json")

BG = {"type": "ColorRect", "name": "Background", "parent_path": ".",
      "properties": {"offset_left": 0, "offset_top": 0, "offset_right": 800,
                     "offset_bottom": 600, "color": {"r": 0.06, "g": 0.07, "b": 0.09, "a": 1}}}
HUD = {"type": "Label", "name": "Hud", "parent_path": ".",
       "properties": {"offset_left": 20, "offset_top": 8, "offset_right": 560,
                      "offset_bottom": 46, "text": "MINES 10  FLAGS 0  SAFE LEFT 71",
                      "theme_override_font_sizes/font_size": 26}}
STATUS = {"type": "Label", "name": "Status", "parent_path": ".",
          "properties": {"offset_left": 560, "offset_top": 8, "offset_right": 795,
                         "offset_bottom": 46, "text": "SWEEP THE FIELD",
                         "theme_override_font_sizes/font_size": 24}}
STATIC_BATCH = [BG, HUD, STATUS]

COLS = 9
ROWS = 9
MINE_TARGET = 10
MINE_SEED = 12345

# --- recompute the payload's own placement rule, in Python --------------------
_seed = MINE_SEED
_placed = set()
while len(_placed) < MINE_TARGET:
    _seed = (_seed * 1664525 + 1013904223) % (2 ** 32)
    _placed.add(_seed % (COLS * ROWS))
SEED_MINE_LIST = "|".join("%d,%d" % (i // COLS, i % COLS) for i in sorted(_placed))

# --- pinned layouts -----------------------------------------------------------
AUTO_MINES = "0,0|0,2|0,4|0,6|0,8|2,0|2,2|2,4|2,6|2,8"
WIN_MINES = "0,0|8,0|8,1|8,2|8,3|8,4|8,5|8,6|8,7|8,8"
HINT_MINES = "4,4|4,5|5,4"
FOUR_MINES = "0,0|4,4|4,5|5,4"

AUTO_SPEC = "mines=%s;first=yes" % AUTO_MINES
AUTO_SPEC_REVEAL = "mines=%s;first=yes" % AUTO_MINES

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
# editor phase (14 calls)
# =============================================================================
e("e01-edit-game", "project_edit_script",
  {"path": "res://src/MinesweeperGame.cs", "content_file": "payload/MinesweeperGame.cs"},
  "the whole game is written through the MCP script writer (the template stub is replaced)")
e("e02-open-scene", "editor_open_scene", {"path": "res://scenes/main.tscn"},
  "the template scene carries the root Main (Node2D) the script is attached to")
e("e03-batch-add-static", "editor_add_nodes_batch", {"nodes": STATIC_BATCH},
  "the three static nodes of the scene, through the batch tool: a background and two labels; "
  "all eighty-one cells are created at run time")
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
e("e10-action-reveal", "editor_add_input_action", {"action": "mine_reveal_next", "key": "R"},
  "reveal the next hidden safe cell")
e("e11-action-flag", "editor_add_input_action", {"action": "mine_flag_next", "key": "F"},
  "flag the next hidden safe cell")
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
  "the running tree: the three static nodes plus the eighty-one cells created at run time")
hook("g02-readback-t0", "Dump()", "the whole board as one line plus every fact")
assert_state("g03-assert-cols", "Cols", "eq", 9, "the board is nine columns wide")
assert_state("g04-assert-rows", "Rows", "eq", 9, "and nine rows tall")
assert_state("g05-assert-target", "MineTarget", "eq", 10, "the seed places ten mines")
assert_state("g06-assert-mines", "MineCount", "eq", 10, "and ten mines are on the board")
assert_state("g07-assert-minelist", "MineList", "eq", SEED_MINE_LIST,
             "the LCG layout is exactly the one recomputed independently in Python from the same rule")
assert_state("g08-assert-safe", "SafeCells", "eq", 71, "71 of the 81 cells are safe")
assert_state("g09-assert-revealed-0", "RevealedCount", "eq", 0, "nothing is revealed yet")
assert_state("g10-assert-flags-0", "FlaggedCount", "eq", 0, "nothing is flagged yet")
assert_state("g11-assert-remaining", "RemainingSafe", "eq", 71, "all 71 safe cells are still hidden")
assert_state("g12-assert-first-not-done", "FirstRevealDone", "eq", False,
             "the first reveal has not happened")
assert_state("g13-assert-exploded-0", "Exploded", "eq", False, "no mine has been hit")
assert_state("g14-assert-over-0", "GameOver", "eq", False, "the game starts alive")
assert_state("g15-assert-won-0", "Won", "eq", False, "and unwon")
assert_state("g16-assert-can-reveal", "CanRevealAny", "eq", True, "there is a cell to reveal")
shot("g17-shot-t0", "mine-t0", "the first frame: 81 covered cells, the HUD and the status label")
samples("g18-samples-frozen", ["RevealHash", "RevealedCount", "FlaggedCount", "Elapsed", "Ticks"], 12,
        "determinism baseline: with AutoReveal 0 the board does not change while the clock runs "
        "(reveal hash / revealed / flagged constant, Elapsed and Ticks both increasing)")
assert_state("g19-assert-last-auto-0", "LastAutoSteps", "eq", 0,
             "the auto-sweep delta is zero while the clock is off")
# --- the first flip is safe -----------------------------------------------------
force("g20-first-setup", "mines=0,0;first=no",
      "put the only mine exactly under the first click")
assert_state("g21-assert-mines-1", "MineCount", "eq", 1, "one mine")
g("g22-probe-before", "running_game_execute_gdscript",
  code("return get_parent().ProbeCell(0, 0)"), "look at the cell before the first flip")
assert_state("g23-assert-probe-mine", "ProbeMine", "eq", True, "the mine really is there")
assert_state("g24-assert-probe-state", "ProbeState", "eq", "mine", "and it is still covered")
hook("g25-first-reveal", "Reveal(0, 0)", "the first flip, straight onto the mine")
assert_state("g26-assert-relocated", "MinesRelocated", "eq", 1,
             "the first-click-safety rule moved the mine instead of exploding")
assert_state("g27-assert-not-exploded", "Exploded", "eq", False, "nothing exploded")
assert_state("g28-assert-not-over", "GameOver", "eq", False, "and the game goes on")
assert_state("g29-assert-first-done", "FirstRevealDone", "eq", True, "the first flip is recorded")
assert_state("g30-assert-minelist-moved", "MineList", "eq", "0,1",
             "the mine moved to the first mine-free cell in row-major order")
assert_state("g31-assert-mine-count", "MineCount", "eq", 1, "the mine was moved, not removed")
g("g32-probe-arrival", "running_game_execute_gdscript",
  code("return get_parent().ProbeCell(0, 1)"), "look where the mine went")
assert_state("g33-assert-arrival-mine", "ProbeMine", "eq", True, "the relocated mine is there")
assert_state("g34-assert-arrival-state", "ProbeState", "eq", "mine", "and it is covered")
g("g35-probe-clicked", "running_game_execute_gdscript",
  code("return get_parent().ProbeCell(0, 0)"), "look at the cell that was clicked")
assert_state("g36-assert-clicked-revealed", "ProbeState", "eq", "revealed", "it is revealed")
assert_state("g37-assert-hint-1", "ProbeHint", "eq", 1, "and its number is 1, the relocated mine")
assert_state("g38-assert-revealed-1", "RevealedCount", "eq", 1,
             "a numbered cell floods nowhere, so exactly one cell is open")
assert_state("g39-assert-moves-1", "Moves", "eq", 1, "one operation was accepted")
assert_state("g40-assert-reveals-1", "RevealsAccepted", "eq", 1, "it was a reveal")
assert_state("g41-assert-rejected-0", "RejectedMoves", "eq", 0, "and nothing was refused")
# --- the number shown on a cell is its adjacent-mine count ----------------------
force("g42-hint-setup", "mines=%s;first=yes" % HINT_MINES, "three mines around one cell")
g("g43-probe-three", "running_game_execute_gdscript",
  code("return get_parent().ProbeCell(5, 5)"), "probe the cell those three mines touch")
assert_state("g44-assert-hint-3", "ProbeHint", "eq", 3, "the number is exactly 3")
assert_state("g45-assert-hidden", "ProbeState", "eq", "hidden", "and the cell is still covered")
assert_state("g46-assert-not-mine", "ProbeMine", "eq", False, "the probed cell is not a mine")
g("g47-probe-mine-cell", "running_game_execute_gdscript",
  code("return get_parent().ProbeCell(4, 4)"), "and the cell that carries one")
assert_state("g48-assert-hint-2", "ProbeHint", "eq", 2, "two of its neighbours are mines")
assert_state("g49-assert-is-mine", "ProbeMine", "eq", True, "and it is one itself")
# --- flagging ------------------------------------------------------------------
force("g50-flag-setup", "mines=%s;first=yes" % FOUR_MINES, "a four-mine board")
hook("g51-flag-on", "ToggleFlag(0, 0)", "put a flag on a hidden cell")
assert_state("g52-assert-flags-1", "FlaggedCount", "eq", 1, "one flag")
assert_state("g53-assert-toggles-1", "FlagToggles", "eq", 1, "one accepted toggle")
assert_state("g54-assert-moves-1", "Moves", "eq", 1, "and one accepted operation")
g("g55-probe-flagged", "running_game_execute_gdscript",
  code("return get_parent().ProbeCell(0, 0)"), "look at the flagged cell")
assert_state("g56-assert-flagged-state", "ProbeState", "eq", "flagged", "it reads as flagged")
assert_state("g57-assert-flagged-mine", "ProbeMine", "eq", True, "and it really is a mine")
hook("g58-flag-off", "ToggleFlag(0, 0)", "take the flag off again")
assert_state("g59-assert-flags-0", "FlaggedCount", "eq", 0, "no flag is left")
g("g60-probe-unflagged", "running_game_execute_gdscript",
  code("return get_parent().ProbeCell(0, 0)"), "look at it once more")
assert_state("g61-assert-mine-again", "ProbeState", "eq", "mine", "it is a covered mine again")
assert_state("g62-assert-toggles-2", "FlagToggles", "eq", 2, "two toggles")
assert_state("g63-assert-moves-2", "Moves", "eq", 2, "two accepted operations")
# --- illegal operations are refused with no board change ------------------------
force("g64-illegal-setup", "mines=%s;revealed=0,8;first=yes" % FOUR_MINES,
      "one cell is already revealed, so a second reveal of it must be refused")
assert_state("g65-assert-revealed-1", "RevealedCount", "eq", 1, "one cell is open")
assert_state("g66-assert-moves-0", "Moves", "eq", 0, "no operation yet")
hook("g67-reveal-open-cell", "Reveal(0, 8)", "reveal the cell that is already open")
assert_state("g68-assert-rejected-1", "RejectedMoves", "eq", 1, "the illegal reveal is refused")
assert_state("g69-assert-moves-still-0", "Moves", "eq", 0, "and nothing was accepted")
assert_state("g70-assert-revealed-still-1", "RevealedCount", "eq", 1, "the board did not change")
assert_state("g71-assert-reason-open", "LastEvent", "contains", "reason=already_revealed",
             "the refusal names the rule")
hook("g72-flag-open-cell", "ToggleFlag(0, 8)", "flagging a revealed cell is refused as well")
assert_state("g73-assert-rejected-2", "RejectedMoves", "eq", 2, "a second refusal")
assert_state("g74-assert-flags-0", "FlaggedCount", "eq", 0, "no flag was written")
hook("g75-flag-hidden", "ToggleFlag(0, 1)", "flagging a hidden cell is accepted")
assert_state("g76-assert-flags-1", "FlaggedCount", "eq", 1, "one flag")
hook("g77-reveal-flagged", "Reveal(0, 1)", "revealing a flagged cell is refused")
assert_state("g78-assert-rejected-3", "RejectedMoves", "eq", 3, "a third refusal")
assert_state("g79-assert-revealed-still-1b", "RevealedCount", "eq", 1, "still one open cell")
assert_state("g80-assert-reason-flagged", "LastEvent", "contains", "reason=flagged",
             "and the refusal says the cell is flagged")
# --- the last safe cell clears the field ----------------------------------------
force("g81-win-setup", "mines=%s;first=no" % WIN_MINES,
      "ten mines packed into the bottom row plus one: the rest of the field is one open region")
assert_state("g82-assert-mines-10", "MineCount", "eq", 10, "ten mines")
assert_state("g83-assert-safe-71", "SafeCells", "eq", 71, "71 safe cells")
assert_state("g84-assert-can-reveal", "CanRevealAny", "eq", True, "the field is still playable")
hook("g85-flood-reveal", "Reveal(4, 4)", "reveal a cell with no adjacent mine: the flood runs")
assert_state("g86-assert-revealed-71", "RevealedCount", "eq", 71,
             "the flood opened every safe cell on the board")
assert_state("g87-assert-remaining-0", "RemainingSafe", "eq", 0, "none is left hidden")
assert_state("g88-assert-won", "Won", "eq", True, "that is the win")
assert_state("g89-assert-over", "GameOver", "eq", True, "and the game is over")
assert_state("g90-assert-not-exploded", "Exploded", "eq", False, "without ever hitting a mine")
assert_state("g91-assert-moves-1", "Moves", "eq", 1, "one accepted operation did all of it")
hook("g92-reveal-after-win", "Reveal(0, 1)", "every reveal after the win is refused")
assert_state("g93-assert-rejected-1", "RejectedMoves", "eq", 1, "the refusal is counted")
assert_state("g94-assert-cannot-reveal", "CanRevealAny", "eq", False, "and there is nothing to reveal")
shot("g95-shot-t1", "mine-t1", "the win screen: the whole field open and the status label CLEARED")
g("g96-assert-screen-text-win", "running_game_assert_screen_text", {"text": "CLEARED"},
  "the status label really is on the captured screen")
# --- revealing a mine is the loss -----------------------------------------------
force("g97-loss-setup", "mines=%s;first=yes" % FOUR_MINES,
      "the first flip has already happened, so a mine under the next one explodes")
assert_state("g98-assert-not-over", "GameOver", "eq", False, "the game is still alive")
hook("g99-reveal-mine", "Reveal(4, 4)", "reveal a mine")
assert_state("g100-assert-exploded", "Exploded", "eq", True, "it exploded")
assert_state("g101-assert-over", "GameOver", "eq", True, "and that ends the game")
assert_state("g102-assert-not-won", "Won", "eq", False, "a loss is not a win")
assert_state("g103-assert-boom-row", "ExplodedRow", "eq", 4, "the loss names the row")
assert_state("g104-assert-boom-col", "ExplodedCol", "eq", 4, "and the column")
assert_state("g105-assert-revealed-0", "RevealedCount", "eq", 0,
             "a revealed mine is not a revealed safe cell")
g("g106-probe-boom", "running_game_execute_gdscript",
  code("return get_parent().ProbeCell(4, 4)"), "look at the mine that was hit")
assert_state("g107-assert-boom-state", "ProbeState", "eq", "exploded", "it reads as exploded")
assert_state("g108-assert-mine-list", "MineList", "eq", FOUR_MINES, "and the layout is unchanged")
shot("g109-shot-t2", "mine-t2", "the loss screen: one red mine and BOOM - GAME OVER")
g("g110-assert-screen-text-loss", "running_game_assert_screen_text",
  {"text": "BOOM - GAME OVER"}, "the status label really is on the captured screen")
# --- the frame-rate independent increment: one hook call, one exact delta --------
force("g111-autostep-setup", AUTO_SPEC_REVEAL,
      "a ten-mine board whose row-major auto policy has one reveal after another")
hook("g112-autostep-2", "AutoStep(2)", "exactly two deterministic auto-sweep reveals")
assert_state("g113-assert-last-hook-2", "LastHookSteps", "eq", 2,
             "the DELTA of that call is exact -- this is the frame-rate independent quantity")
assert_state("g113b-assert-last-auto-0", "LastAutoSteps", "eq", 0,
             "and it is a DIFFERENT property from the clock's own per-frame delta, which is 0 while "
             "the clock is off")
assert_state("g114-assert-auto-total-2", "AutoSteps", "eq", 2, "and the total agrees")
assert_state("g115-assert-revealed-2", "RevealedCount", "eq", 2, "two cells were opened")
assert_state("g116-assert-moves-2", "Moves", "eq", 2, "two accepted operations")
assert_state("g117-assert-rejected-0", "RejectedMoves", "eq", 0, "with no refusal in between")
# --- multi-frame sample of the auto-sweep CLOCK: the board really moves ----------
# NOTE: this block deliberately does NOT call ForceTestState again. r1 of this game did,
# and its closing assertion then read 0: ForceTestState pins the WHOLE state, so it zeroes
# the hook's delta as well (the A-1 lesson). Keeping one pinned board across the hook, the
# clock and the two deltas is what makes "the clock does not write the hook's property" a
# fact rather than an assumption.
hook("g118-autoreveal-on", "SetAutoReveal(120.0)",
     "the one sample that watches the field move asks for motion explicitly")
assert_state("g118b-assert-hook-intact", "LastHookSteps", "eq", 2,
             "the clock has been running for several frames and the hook's own delta is still "
             "exactly what the hook wrote -- the two producers have two properties")
samples("g119-samples-autoreveal",
        ["RevealedCount", "RevealHash", "AutoSteps", "LastAutoSteps", "Elapsed", "Ticks"], 30,
        "multi-frame property sample of the auto-sweep clock: the revealed count and the reveal hash "
        "change frame by frame while Elapsed and Ticks advance -- 'the field moves' as a sequence of "
        "values, not as an adjective")
assert_state("g120-assert-revealed-grew", "RevealedCount", "gt", 2,
             "the clock opened cells past the two the hook opened")
assert_state("g121-assert-auto-grew", "AutoSteps", "gt", 2, "and the clock's own total grew")
hook("g122-autoreveal-off", "SetAutoReveal(0.0)", "back to frozen")
assert_state("g123-assert-last-auto-0", "LastAutoSteps", "eq", 0, "the per-frame delta is zero again")
assert_state("g124-assert-hook-intact", "LastHookSteps", "eq", 2,
             "while the hook's own delta is untouched by the clock, before or after it runs")
shot("g125-shot-t3", "mine-t3", "the field after the auto-sweep sample: cells are open")
# --- the declared input path really drives the game ------------------------------
force("g126-input-setup", AUTO_SPEC, "a clean board for the input test")
assert_state("g126b-assert-hook-zeroed", "LastHookSteps", "eq", 0,
             "ForceTestState pins the WHOLE state, so it zeroes the hook's delta too -- the A-1 "
             "lesson stated as an assertion instead of an assumption")
hook("g127-poll-on", "SetPollInput(true)",
     "the input path is off by default; the test switches it on explicitly")
g("g128-input-reveal", "running_game_run_test_scenario",
  {"steps": [{"type": "input", "action": "mine_reveal_next", "pressed": True},
             {"type": "wait", "seconds": 0.45},
             {"type": "assert", "node_path": "Main", "property": "RevealedCount",
              "operator": "gt", "expected": 0}]},
  "the declared action really opens a cell")
assert_state("g129-assert-input-reveals-1", "InputReveals", "eq", 1,
             "the declared action fires on the PRESS EDGE, so a scenario's never-released key "
             "performs exactly one reveal instead of repeating at the frame rate")
hook("g130-poll-off", "SetPollInput(false)",
     "polling off again: nothing after this can drift because a key is still marked held")
# --- positive control: a node created at run time is drawn ----------------------
g("g131-runtime-overlay", "running_game_execute_gdscript",
  code('var main = get_parent()\nvar c = ColorRect.new()\nc.name = StringName("ProbeOverlay")\n'
       'c.position = Vector2(20, 552)\nc.size = Vector2(120, 34)\n'
       'c.color = Color(0.95, 0.35, 0.95, 1.0)\nmain.add_child(c)\nreturn "overlay added"'),
  "a node created at run time, in the same session, as the positive control for 'a run-time node "
  "is drawn' (and the eighty-one cells are eighty-one more of those)")
# --- DECLARED FAILURE: the error path of the assertion tool ---------------------
g("g132-assert-unknown-property", "running_game_assert_node_state",
  {"node_path": "Main", "property": "NoSuchProperty", "operator": "eq", "expected": 1},
  "DECLARED FAILURE: a boundary call asking for a property that does not exist (-32001), so the "
  "error path of the assertion tool is on the record too")
# --- final: the overlay frame and the seed layout once more ---------------------
shot("g133-shot-t4", "mine-t4", "the overlay is visible in this frame and not in t3")
force("g134-seed-again", "mines=seed:%d;first=no" % MINE_SEED,
      "ask for the LCG layout again instead of an explicit list")
assert_state("g135-assert-seed-mines", "MineCount", "eq", 10, "the seed still places ten mines")
assert_state("g136-assert-seed-list", "MineList", "eq", SEED_MINE_LIST,
             "and it reproduces the very same layout the Python recomputation predicted")
hook("g137-final-readback", "Dump()", "the final board as one line")
g("g138-final-tree", "running_game_get_scene_tree", {},
  "the final tree, including the run-time overlay")

doc = {"import": True, "calls": calls}
os.makedirs(os.path.dirname(OUT), exist_ok=True)
with io.open(OUT, "w", encoding="utf-8", newline="\n") as handle:
    handle.write(json.dumps(doc, ensure_ascii=False, indent=1) + "\n")
print("wrote %s calls=%d seed_mine_list=%s" % (OUT, len(calls), SEED_MINE_LIST))
