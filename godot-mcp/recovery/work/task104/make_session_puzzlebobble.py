#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""TASK-104 (B, game 19): the Puzzle Bobble session generator, with the Python
second implementation of the payload's rules.

The payload is `tools/sessions/puzzlebobble/payload/PuzzleBobbleGame.cs`. `BSim`
below re-implements its rules from the *rules*: the linear congruential generator
that fills the initial board and its stabilising loop, the five integer aim
directions and the side-wall reflection, the attach rule, the same-colour
4-connected group test, the generation-by-generation fall of disconnected
bubbles, the chain multiplier and both end conditions. Every literal a
`running_game_assert_node_state` compares against -- including the initial board
and its hash -- is produced by `BSim` and by nothing else.

Written by a Python writer, never by a shell redirect (iron rule 1).
"""

import io
import json
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.abspath(os.path.join(HERE, "..", "..", ".."))
SESSION_DIR = os.path.join(ROOT, "tools", "sessions", "puzzlebobble")
OUT = os.path.join(SESSION_DIR, "session.json")
PAYLOAD = "payload/PuzzleBobbleGame.cs"

COLS = 8
ROWS = 12
CELL = 40
COLORS = 6
FILL_ROWS = 4
INIT_SEED = 20251040
FAIL_ROW = 10
CLEAR_SCORE = 10
DROP_SCORE = 20
MAX_CHAIN = 24
ANGLE_DC = [-2, -1, 0, 1, 2]
ANGLE_DR = [-1, -1, -1, -1, -1]


def sign32(value):
    value &= 0xFFFFFFFF
    return value - 0x100000000 if value >= 0x80000000 else value


def build_initial_board():
    """The payload's LCG fill plus its stabilising loop, re-implemented from the rules."""
    board = [-1] * (COLS * ROWS)
    seed = INIT_SEED
    for row in range(FILL_ROWS):
        for col in range(COLS):
            seed = (seed * 1103515245 + 12345) % (1 << 31)
            board[row * COLS + col] = (seed >> 16) % COLORS
    for row in range(FILL_ROWS):
        for col in range(COLS):
            index = row * COLS + col
            for _ in range(COLORS):
                value = board[index]
                bad = False
                if col >= 2 and board[index - 1] == value and board[index - 2] == value:
                    bad = True
                if row >= 2 and board[index - COLS] == value and board[index - 2 * COLS] == value:
                    bad = True
                if not bad:
                    break
                board[index] = (value + 1) % COLORS
    return board


class BSim(object):
    """The payload's rules, re-implemented from the rules."""

    def __init__(self):
        self.reset()

    def reset(self):
        self.board = build_initial_board()
        self.score = 0
        self.shots = 0
        self.cleared = 0
        self.dropped = 0
        self.last_chain = 0
        self.last_cleared = 0
        self.last_dropped = 0
        self.attach = (-1, -1)
        self.failed = False
        self.won = False
        self.over = False
        self.shooter_col = COLS // 2
        self.color = 0
        self.next_color = 1 % COLORS
        self.angle = 2
        self.proj_active = False
        self.proj_col = -1
        self.proj_row = -1
        self.proj_color = -1
        self.moves = 0
        self.rejected = 0
        self.steps = 0

    # --- the board ---------------------------------------------------------------

    def occupied(self, col, row):
        if not (0 <= col < COLS and 0 <= row < ROWS):
            return False
        return self.board[row * COLS + col] >= 0

    def color_at(self, col, row):
        if not (0 <= col < COLS and 0 <= row < ROWS):
            return -1
        return self.board[row * COLS + col]

    def board_string(self):
        rows = []
        for row in range(ROWS):
            text = []
            for col in range(COLS):
                value = self.board[row * COLS + col]
                text.append('.' if value < 0 else str(value))
            rows.append("".join(text))
        return "/".join(rows)

    def board_hash(self):
        value = 0
        for index in range(len(self.board)):
            value = sign32(value * 31 + (self.board[index] + 1))
        return value

    def bubbles_in_use(self):
        return len([v for v in self.board if v >= 0])

    def lowest_row(self):
        lowest = -1
        for row in range(ROWS):
            for col in range(COLS):
                if self.board[row * COLS + col] >= 0 and row > lowest:
                    lowest = row
        return lowest

    # --- the rules ---------------------------------------------------------------

    def find_group(self, col, row):
        if not self.occupied(col, row):
            return []
        color = self.color_at(col, row)
        seen = set()
        stack = [row * COLS + col]
        seen.add(stack[0])
        out = []
        while stack:
            cell = stack.pop()
            out.append(cell)
            cc = cell % COLS
            cr = cell // COLS
            for dc, dr in ((1, 0), (-1, 0), (0, 1), (0, -1)):
                nc, nr = cc + dc, cr + dr
                if not (0 <= nc < COLS and 0 <= nr < ROWS):
                    continue
                if self.color_at(nc, nr) != color:
                    continue
                nxt = nr * COLS + nc
                if nxt not in seen:
                    seen.add(nxt)
                    stack.append(nxt)
        return out

    def floating_cells(self):
        reachable = set()
        stack = []
        for col in range(COLS):
            if self.occupied(col, 0):
                cell = col
                reachable.add(cell)
                stack.append(cell)
        while stack:
            cell = stack.pop()
            cc = cell % COLS
            cr = cell // COLS
            for dc, dr in ((1, 0), (-1, 0), (0, 1), (0, -1)):
                nc, nr = cc + dc, cr + dr
                if not (0 <= nc < COLS and 0 <= nr < ROWS):
                    continue
                if not self.occupied(nc, nr):
                    continue
                nxt = nr * COLS + nc
                if nxt not in reachable:
                    reachable.add(nxt)
                    stack.append(nxt)
        return [i for i in range(len(self.board)) if self.board[i] >= 0 and i not in reachable]

    def resolve(self, col, row):
        chain = 0
        cleared = 0
        dropped = 0
        group = self.find_group(col, row)
        if len(group) < 3:
            self.last_chain = 0
            self.last_cleared = 0
            self.last_dropped = 0
            self.attach = (col, row)
            return
        chain = 1
        cleared += len(group)
        self.score += len(group) * CLEAR_SCORE * chain
        for cell in group:
            self.board[cell] = -1
        guard = 0
        while chain < MAX_CHAIN and guard < MAX_CHAIN:
            guard += 1
            floating = self.floating_cells()
            if not floating:
                break
            layer = []
            for cell in floating:
                cc = cell % COLS
                cr = cell // COLS
                if not self.occupied(cc, cr + 1):
                    layer.append(cell)
            if not layer:
                layer = floating
            chain += 1
            dropped += len(layer)
            self.score += len(layer) * DROP_SCORE * chain
            for cell in layer:
                self.board[cell] = -1
        self.cleared += cleared
        self.dropped += dropped
        self.last_chain = chain
        self.last_cleared = cleared
        self.last_dropped = dropped
        self.attach = (col, row)

    def check_end(self):
        if self.over:
            return
        lowest = self.lowest_row()
        if lowest >= FAIL_ROW:
            self.failed = True
            self.over = True
            self.won = False
            return
        if lowest < 0:
            self.won = True
            self.over = True

    def tick(self):
        if self.over:
            return
        self.steps += 1
        if not self.proj_active:
            return
        dc = ANGLE_DC[self.angle]
        dr = ANGLE_DR[self.angle]
        nx = self.proj_col + dc
        ny = self.proj_row + dr
        if nx < 0 or nx >= COLS:
            dc = -dc
            nx = self.proj_col + dc
        if ny < 0 or self.occupied(nx, ny):
            self.attach_now()
            return
        self.proj_col = nx
        self.proj_row = ny

    def attach_now(self):
        col = self.proj_col
        row = self.proj_row
        if row < 0:
            row = 0
        if self.occupied(col, row):
            probe = row
            while probe < ROWS and self.occupied(col, probe):
                probe += 1
            if probe >= ROWS:
                self.proj_active = False
                return
            row = probe
        self.board[row * COLS + col] = self.proj_color
        self.proj_active = False
        self.proj_col = -1
        self.proj_row = -1
        self.resolve(col, row)
        self.check_end()
        self.color = self.next_color
        self.next_color = (self.next_color + 1) % COLORS

    def step(self, count):
        applied = 0
        for _ in range(count):
            if self.over:
                break
            self.tick()
            applied += 1
        return applied

    # --- the actions ---------------------------------------------------------------

    def aim(self, index):
        if self.over:
            self.rejected += 1
            return
        value = max(0, min(len(ANGLE_DC) - 1, index))
        if value == self.angle:
            self.rejected += 1
            return
        self.angle = value
        self.moves += 1

    def shoot(self):
        if self.over or self.proj_active:
            self.rejected += 1
            return
        self.proj_active = True
        self.proj_color = self.color
        self.proj_col = self.shooter_col
        self.proj_row = ROWS - 1
        self.shots += 1
        self.last_chain = 0
        self.last_cleared = 0
        self.last_dropped = 0
        self.attach = (-1, -1)

    def force(self, cells=None, color=None, next_color=None, angle=None, score=None):
        self.reset()
        if cells is not None:
            self.board = [-1] * (COLS * ROWS)
            for (col, row), value in cells.items():
                self.board[row * COLS + col] = value
        if color is not None:
            self.color = color
        if next_color is not None:
            self.next_color = next_color
        if angle is not None:
            self.angle = max(0, min(len(ANGLE_DC) - 1, angle))
        if score is not None:
            self.score = score

    def probe_state(self, col, row):
        if not (0 <= col < COLS and 0 <= row < ROWS):
            return "outside", -1
        if self.proj_active and self.proj_col == col and self.proj_row == row:
            return "projectile", self.proj_color
        if self.board[row * COLS + col] >= 0:
            return "occupied", self.board[row * COLS + col]
        if col == self.shooter_col and row == ROWS - 1:
            return "shooter", -1
        return "empty", -1


def board_spec(cells):
    rows = []
    for row in range(ROWS):
        text = []
        for col in range(COLS):
            value = cells.get((col, row), -1) if cells else -1
            text.append('.' if value < 0 else str(value))
        rows.append("".join(text))
    return "|".join(rows)


# ---------------------------------------------------------------------------
# The session
# ---------------------------------------------------------------------------

CALLS = []


def call(tag, port, tool, arguments, note):
    CALLS.append({"tag": tag, "port": port, "tool": tool, "arguments": arguments, "note": note})


def exec_code(tag, code, note):
    call(tag, "game", "running_game_execute_gdscript", {"code": code}, note)


def assert_state(tag, prop, operator, expected, note, node="Main"):
    call(tag, "game", "running_game_assert_node_state",
         {"node_path": node, "property": prop, "operator": operator, "expected": expected}, note)


def assert_ok(tag, prop, expected, note):
    assert_state(tag, prop, "eq", expected, note)


def shot(tag, name, note):
    call(tag, "game", "running_game_capture_screenshot", {"save_path": "user://%s.png" % name}, note)


def samples(tag, properties, frames, note):
    call(tag, "game", "running_game_get_node_property_samples",
         {"node_path": "Main", "properties": properties, "frame_count": frames, "frame_interval": 1}, note)


def force(spec):
    return 'var g = get_parent()\nreturn g.ForceTestState("%s")' % spec


def invoke(expression):
    return "var g = get_parent()\nreturn g.%s" % expression


def editor_phase():
    nodes = [
        {"type": "ColorRect", "name": "Background", "parent_path": ".",
         "properties": {"offset_left": 0, "offset_top": 0, "offset_right": 800, "offset_bottom": 600,
                        "color": {"r": 0.05, "g": 0.04, "b": 0.08, "a": 1}}},
        {"type": "Label", "name": "Hud", "parent_path": ".",
         "properties": {"offset_left": 14, "offset_top": 10, "offset_right": 790, "offset_bottom": 44,
                        "text": "SHOT 0  COLOR 0  NEXT 1  ANGLE 2  BUBBLES 0  CLEARED 0  DROPPED 0  SCORE 0",
                        "theme_override_font_sizes/font_size": 18}},
        {"type": "Label", "name": "Status", "parent_path": ".",
         "properties": {"offset_left": 14, "offset_top": 574, "offset_right": 790, "offset_bottom": 600,
                        "text": "AIM AND FIRE", "theme_override_font_sizes/font_size": 18}},
    ]
    call("e01-edit-game", "editor", "project_edit_script",
         {"path": "res://src/PuzzleBobbleGame.cs", "content_file": PAYLOAD},
         "the whole game is written through the MCP script writer (the template stub is replaced)")
    call("e02-open-scene", "editor", "editor_open_scene", {"path": "res://scenes/main.tscn"},
         "the template scene carries the root Main (Node2D) the script is attached to")
    call("e03-batch-add-static", "editor", "editor_add_nodes_batch", {"nodes": nodes},
         "the three static nodes of the scene, through the batch tool; the 96 grid sprites, the failure line, the shooter and the projectile are created at run time")
    call("e04-save-1", "editor", "editor_save_scene", {}, "the scene with the three static nodes on disk: sha A")
    call("e05-read-1", "editor", "project_read_text_file", {"path": "res://scenes/main.tscn"},
         "sha A and the exact bytes")
    call("e06-batch-add-static-again", "editor", "editor_add_nodes_batch", {"nodes": nodes},
         "the deliberate replay of the same batch: D-3's refusal (-32000, data.conflicts) must appear in every round's evidence")
    call("e07-tree-after-refusal", "editor", "editor_get_scene_tree", {},
         "the refused batch wrote nothing: the tree still has exactly the three static nodes")
    call("e08-save-2", "editor", "editor_save_scene", {}, "save again after the refusal")
    call("e09-read-2", "editor", "project_read_text_file", {"path": "res://scenes/main.tscn"},
         "sha B: byte-identical to sha A, because the refused batch changed no byte")
    call("e10-action-shoot", "editor", "editor_add_input_action", {"action": "pb_shoot", "key": "Space"},
         "one shot per press edge, for the input-edge scenario")
    call("e11-save-3", "editor", "editor_save_scene", {}, "persist the declared action")
    call("e12-build-csharp", "editor", "project_build_csharp", {},
         "the payload really compiles: the real dotnet exit code")
    call("e13-validate-scripts", "editor", "project_validate_scripts", {},
         "per-file verdicts for every script in the project")
    call("e14-get-errors", "editor", "editor_get_errors", {},
         "the editor's own error list after the build")


def game_phase():
    initial = BSim()

    # --- the generated board, and the shape of the world -------------------------
    call("g01-scene-tree", "game", "running_game_get_scene_tree", {},
         "the running game's tree: three static nodes, no @-auto names")
    assert_ok("g02-assert-cols", "Cols", COLS, "the playfield is eight columns wide")
    assert_ok("g03-assert-rows", "Rows", ROWS, "and twelve rows tall")
    assert_ok("g04-assert-cell", "Cell", CELL, "one cell is forty pixels")
    assert_ok("g05-assert-colors", "Colors", COLORS, "six colours")
    assert_ok("g06-assert-fail-row", "FailRow", FAIL_ROW, "a bubble resting at row 10 loses")
    assert_ok("g07-assert-fill-rows", "FillRows", FILL_ROWS, "four rows are filled at the start")
    assert_ok("g08-assert-seed", "InitSeed", INIT_SEED, "and they come from this seed")
    assert_ok("g09-assert-board", "Board", initial.board_string(),
              "the initial board, recomputed in Python from the same LCG and the same stabilising loop")
    assert_ok("g10-assert-board-hash", "BoardHash", initial.board_hash(),
              "and its multiply-31 hash, recomputed independently")
    assert_ok("g11-assert-bubbles", "BubblesInUse", initial.bubbles_in_use(),
              "the initial board carries %d bubbles" % initial.bubbles_in_use())
    assert_ok("g12-assert-shooter-col", "ShooterCol", initial.shooter_col, "the shooter sits under column 4")
    exec_code("g13-readback-t0", invoke("Dump()"),
              "the whole state on one line: the board, the shooter and every counter")
    shot("g14-shot-t0", "pb-t0", "the first frame: the generated board and the failure line")

    # --- the frozen baseline -------------------------------------------------------
    samples("g15-samples-frozen",
            ["Steps", "BubblesInUse", "BoardHash", "Score", "Elapsed", "Ticks"], 12,
            "determinism baseline: AutoClock is 0, so the board facts are constant while Elapsed and Ticks both advance")
    assert_ok("g16-assert-frozen-steps", "Steps", 0, "with the clock off, not one step has run")
    assert_ok("g17-assert-frozen-auto", "LastAutoSteps", 0, "and the auto clock applied nothing")
    assert_ok("g18-assert-frozen-hook", "LastHookSteps", 0, "and the hook applied nothing either")

    # --- the probe names what stands where ------------------------------------------
    empty_cells = {}
    probe = BSim()
    probe.force(cells=empty_cells, color=2, angle=2)
    exec_code("g19-probe-setup", force("board=%s;color=2;angle=2" % board_spec(empty_cells)),
              "an empty board, so the probe has nothing to confuse")
    for tag, col, row, state, value in (("g21", 0, 0, "empty", -1), ("g22", 4, 11, "shooter", -1),
                                        ("g23", 8, 0, "outside", -1), ("g24", 3, 5, "empty", -1)):
        exec_code("%s-probe" % tag, invoke("Probe(%d, %d)" % (col, row)),
                  "the probe names what stands on one cell, so the assertion below is about that cell")
        assert_ok("%sa-assert-state" % tag, "ProbeState", state, "(%d,%d) is %s" % (col, row, state))
        assert_ok("%sb-assert-value" % tag, "ProbeValue", value, "with no colour on it")
    one = {(2, 4): 3}
    exec_code("g25-probe-occupied-setup", force("board=%s;color=2;angle=2" % board_spec(one)),
              "one pinned bubble at (2,4)")
    assert_ok("g26-assert-bubbles", "BubblesInUse", 1, "the pinned board carries exactly one bubble")
    exec_code("g27-probe-occupied", invoke("Probe(2, 4)"), "the probe names it")
    assert_ok("g27a-assert-state", "ProbeState", "occupied", "the cell is occupied")
    assert_ok("g27b-assert-value", "ProbeValue", 3, "and its colour is the pinned one")

    # --- aiming: five integer directions, and the table clamps -------------------------
    aim = BSim()
    aim.force(cells=empty_cells, color=2, angle=2)
    exec_code("g28-aim-setup", force("board=%s;color=2;angle=2" % board_spec(empty_cells)),
              "a fresh empty board, aimed straight up")
    exec_code("g29-aim-left", invoke("Aim(0)"), "aim at the steepest left direction")
    aim.aim(0)
    assert_ok("g30-assert-angle", "AngleIndex", aim.angle, "the angle index is 0")
    assert_ok("g31-assert-moves", "Moves", aim.moves, "one aim was counted")
    exec_code("g32-aim-right", invoke("Aim(4)"), "aim at the steepest right direction")
    aim.aim(4)
    assert_ok("g33-assert-angle-4", "AngleIndex", aim.angle, "the angle index is 4")
    exec_code("g34-aim-same", invoke("Aim(4)"), "the same direction again is refused")
    aim.aim(4)
    assert_ok("g35-assert-rejected", "RejectedMoves", aim.rejected, "the refusal was counted")
    exec_code("g36-aim-clamp", invoke("Aim(9)"), "past the end of the table: the clamp decides")
    aim.aim(9)
    assert_ok("g37-assert-angle-clamped", "AngleIndex", aim.angle, "clamped to the last direction")

    # --- the shot flies, and the side wall reflects it ---------------------------------
    bounce = BSim()
    bounce.force(cells=empty_cells, color=2, angle=2)
    exec_code("g38-bounce-setup", force("board=%s;color=2;angle=2" % board_spec(empty_cells)),
              "an empty board to watch the flight on")
    exec_code("g39-bounce-aim", invoke("Aim(0)"), "aim two columns left per row")
    bounce.aim(0)
    exec_code("g40-bounce-shoot", invoke("Shoot()"), "fire: the shot starts in the shooter's cell")
    bounce.shoot()
    assert_ok("g41-assert-shots", "Shots", bounce.shots, "one shot was fired")
    assert_ok("g42-assert-proj-start", "ProjCol", bounce.proj_col,
              "the shot starts in column %d (Python)" % bounce.proj_col)
    assert_ok("g43-assert-proj-row", "ProjRow", bounce.proj_row,
              "and row %d" % bounce.proj_row)
    bounce.step(1)
    exec_code("g44-bounce-step-1", invoke("StepFrames(1)"), "one step: two columns left, one row up")
    assert_ok("g45-assert-proj-1", "ProjCol", bounce.proj_col, "column %d" % bounce.proj_col)
    assert_ok("g46-assert-proj-row-1", "ProjRow", bounce.proj_row, "row %d" % bounce.proj_row)
    bounce.step(1)
    exec_code("g47-bounce-step-2", invoke("StepFrames(1)"), "one more step: it reaches the wall column")
    assert_ok("g48-assert-proj-2", "ProjCol", bounce.proj_col, "column %d" % bounce.proj_col)
    bounce.step(1)
    exec_code("g49-bounce-step-3", invoke("StepFrames(1)"),
              "the third step would leave the field, so it reflects instead")
    assert_ok("g50-assert-proj-3", "ProjCol", bounce.proj_col,
              "reflected to column %d (Python)" % bounce.proj_col)
    assert_ok("g51-assert-proj-row-3", "ProjRow", bounce.proj_row, "and row %d" % bounce.proj_row)
    exec_code("g52-probe-projectile", invoke("Probe(%d, %d)" % (bounce.proj_col, bounce.proj_row)),
              "the probe names the shot in the air")
    assert_ok("g52a-assert-probe", "ProbeState", "projectile", "the cell really carries the shot")
    assert_ok("g52b-assert-probe-value", "ProbeValue", bounce.proj_color,
              "with the shooter's colour (%d)" % bounce.proj_color)

    # --- attaching to the ceiling -------------------------------------------------------
    ceil = BSim()
    ceil.force(cells=empty_cells, color=2, angle=2)
    exec_code("g53-ceil-setup", force("board=%s;color=2;angle=2" % board_spec(empty_cells)),
              "an empty board, straight up: the shot must come to rest on the ceiling row")
    exec_code("g54-ceil-shoot", invoke("Shoot()"), "fire")
    ceil.shoot()
    applied = ceil.step(12)
    exec_code("g55-ceil-steps", invoke("StepFrames(12)"),
              "twelve steps: eleven to reach row 0 and one to notice the ceiling")
    assert_ok("g56-assert-attach-col", "LastAttachCol", ceil.attach[0], "it attached at column %d" % ceil.attach[0])
    assert_ok("g57-assert-attach-row", "LastAttachRow", ceil.attach[1], "and row %d" % ceil.attach[1])
    assert_ok("g58-assert-chain-0", "LastChain", ceil.last_chain,
              "a lone bubble matches nothing, so the chain is 0")
    assert_ok("g59-assert-board", "Board", ceil.board_string(),
              "the board Python says: one bubble on the ceiling row")
    assert_ok("g60-assert-bubbles", "BubblesInUse", ceil.bubbles_in_use(), "one bubble in use")
    assert_ok("g61-assert-hook", "LastHookSteps", applied, "the hook applied %d steps" % applied)

    # --- same-colour three-in-a-row, and the bubble it detaches ---------------------------
    match_cells = {(0, 0): 0, (4, 2): 5, (3, 3): 1, (5, 3): 1}
    match = BSim()
    match.force(cells=match_cells, color=1, angle=2)
    exec_code("g62-match-setup",
              force("board=%s;color=1;angle=2" % board_spec(match_cells)),
              "a pinned board: a blocker above the flight path and two same-coloured bubbles beside where the shot comes to rest")
    exec_code("g63-match-shoot", invoke("Shoot()"), "fire the matching colour straight up")
    match.shoot()
    match.step(9)
    exec_code("g64-match-steps", invoke("StepFrames(9)"), "nine steps: the shot reaches the blocker")
    assert_ok("g65-assert-attach", "LastAttachCol", match.attach[0],
              "it attached at column %d (Python)" % match.attach[0])
    assert_ok("g66-assert-attach-row", "LastAttachRow", match.attach[1], "and row %d" % match.attach[1])
    assert_ok("g67-assert-cleared", "LastCleared", match.last_cleared,
              "three same-coloured bubbles were cleared")
    assert_ok("g68-assert-dropped", "LastDropped", match.last_dropped,
              "and %d bubble lost its support and fell" % match.last_dropped)
    assert_ok("g69-assert-chain", "LastChain", match.last_chain,
              "one match plus one fall generation = chain %d" % match.last_chain)
    assert_ok("g70-assert-score", "Score", match.score, "score %d" % match.score)
    assert_ok("g71-assert-board", "Board", match.board_string(),
              "the board Python says: %s" % match.board_string())
    assert_ok("g72-assert-board-hash", "BoardHash", match.board_hash(), "and its hash")

    # --- the cascade: a floating tower falls one layer per generation -------------------------
    fork_cells = {(0, 0): 0, (4, 3): 2, (4, 4): 2, (4, 5): 2, (3, 6): 1, (5, 6): 1}
    fork = BSim()
    fork.force(cells=fork_cells, color=1, angle=2)
    exec_code("g73-fork-setup",
              force("board=%s;color=1;angle=2" % board_spec(fork_cells)),
              "a pinned board whose shot clears a three, leaving a two-cell tower floating above it")
    exec_code("g74-fork-shoot", invoke("Shoot()"), "fire the matching colour straight up")
    fork.shoot()
    applied = fork.step(7)
    exec_code("g75-fork-steps", invoke("StepFrames(7)"),
              "seven steps: six to reach the row before the tower and one to attach")
    assert_ok("g76-assert-attach", "LastAttachRow", fork.attach[1],
              "the shot came to rest at row %d" % fork.attach[1])
    assert_ok("g77-assert-cleared", "LastCleared", fork.last_cleared, "three bubbles matched")
    assert_ok("g78-assert-dropped", "LastDropped", fork.last_dropped,
              "and the tower fell, one generation at a time (%d bubbles)" % fork.last_dropped)
    assert_ok("g79-assert-chain", "LastChain", fork.last_chain,
              "one match plus one generation per falling layer = chain %d" % fork.last_chain)
    assert_ok("g80-assert-score", "Score", fork.score,
              "the chain multiplier is applied to every generation: score %d" % fork.score)
    assert_ok("g81-assert-board", "Board", fork.board_string(),
              "the board Python says: %s" % fork.board_string())
    assert_ok("g82-assert-totals", "TotalDropped", fork.dropped, "the game-wide drop counter follows")

    # --- the failure line ----------------------------------------------------------------------
    fill = {(4, row): 5 for row in range(0, 10)}
    fail = BSim()
    fail.force(cells=fill, color=2, angle=2)
    exec_code("g83-fail-setup", force("board=%s;color=2;angle=2" % board_spec(fill)),
              "column 4 filled from the ceiling down to row 9: the next bubble rests on row 10")
    exec_code("g84-fail-shoot", invoke("Shoot()"), "fire a colour that matches nothing")
    fail.shoot()
    applied = fail.step(3)
    exec_code("g85-fail-steps", invoke("StepFrames(3)"), "three steps: the shot lands on the failure row")
    assert_ok("g86-assert-attach", "LastAttachRow", fail.attach[1],
              "it attached at row %d" % fail.attach[1])
    assert_ok("g87-assert-failed", "Failed", fail.failed, "a bubble rests at or below the failure line")
    assert_ok("g88-assert-over", "GameOver", fail.over, "so the game is over")
    assert_ok("g89-assert-not-won", "Won", fail.won, "and it was not won")
    assert_ok("g90-assert-score", "Score", fail.score, "no match, no score")
    shot("g91-shot-failed", "pb-t1", "the lost game: the status label and the filled column")

    # --- clearing the whole board is a win --------------------------------------------------------
    win_cells = {(4, 0): 3, (4, 1): 3}
    win = BSim()
    win.force(cells=win_cells, color=3, angle=2)
    exec_code("g92-win-setup", force("board=%s;color=3;angle=2" % board_spec(win_cells)),
              "a pinned board with exactly two bubbles of the shooter's colour hanging from the ceiling")
    exec_code("g93-win-shoot", invoke("Shoot()"), "fire")
    win.shoot()
    applied = win.step(16)
    exec_code("g94-win-steps", invoke("StepFrames(16)"), "the shot reaches the pair and completes the three")
    assert_ok("g95-assert-cleared", "LastCleared", win.last_cleared, "three bubbles were cleared")
    assert_ok("g96-assert-bubbles", "BubblesInUse", win.bubbles_in_use(),
              "the board is empty (%d)" % win.bubbles_in_use())
    assert_ok("g97-assert-won", "Won", win.won, "so the game is won")
    assert_ok("g98-assert-over", "GameOver", win.over, "and it ended")
    assert_ok("g99-assert-failed", "Failed", win.failed, "not by the failure line")
    assert_ok("g100-assert-score", "Score", win.score, "score %d" % win.score)
    shot("g101-shot-won", "pb-t2", "the cleared board")
    call("g102-assert-screen-win", "game", "running_game_assert_screen_text", {"text": "BOARD CLEARED"},
         "the status label really is on the captured screen")
    exec_code("g103-shoot-after-win", invoke("Shoot()"), "a shot after the game ended")
    assert_ok("g104-assert-shots", "Shots", win.shots, "refused: no shot was fired")

    # --- the input edge -----------------------------------------------------------------------------
    edge = BSim()
    edge.force(cells=empty_cells, color=2, angle=2)
    exec_code("g105-input-setup", force("board=%s;color=2;angle=2" % board_spec(empty_cells)),
              "a pinned empty board for the declared-input scenario")
    exec_code("g106-poll-on", invoke("SetPollInput(true)"), "start listening to the declared action")
    call("g107-input-shoot", "game", "running_game_run_test_scenario",
         {"steps": [{"type": "input", "action": "pb_shoot", "pressed": True},
                    {"type": "wait", "seconds": 0.45},
                    {"type": "assert", "node_path": "Main", "property": "Shots",
                     "operator": "gte", "expected": 1}]},
         "the declared action really fires (a press edge, so exactly one shot)")
    assert_ok("g108-assert-input-shots", "InputShots", 1, "the edge fired exactly once")
    exec_code("g109-poll-off", invoke("SetPollInput(false)"),
              "stop listening again, so the rest of the session is deterministic")

    # --- the clock: multi-frame sampling with a must-move assertion -----------------------------------
    clock_cells = {(0, 0): 0, (4, 2): 5, (3, 3): 1, (5, 3): 1}
    clock = BSim()
    clock.force(cells=clock_cells, color=1, angle=2)
    exec_code("g110-clock-setup",
              force("board=%s;color=1;angle=2" % board_spec(clock_cells)),
              "a pinned board with a whole shot's worth of work to do")
    exec_code("g111-clock-shoot", invoke("Shoot()"),
              "the shot is in the air BEFORE the clock starts, so the clock has something to move")
    clock.shoot()
    assert_ok("g112-assert-clock-steps-0", "Steps", 0, "the clock is off, so nothing has moved yet")
    hash0 = clock.board_hash()
    assert_ok("g113-assert-clock-hash-0", "BoardHash", hash0, "the pinned board hash")
    exec_code("g114-clock-on", invoke("SetAutoClock(60.0)"),
              "the clock ticks 60 times a second (a float accumulator, F-1's fix)")
    samples("g115-samples-clock",
            ["Steps", "ProjActive", "ProjRow", "BubblesInUse", "BoardHash", "Score", "Elapsed", "Ticks"], 30,
            "thirty frames with the clock running: the shot flies, the match resolves and the board hash moves")
    assert_state("g116-assert-clock-moved", "Steps", "gt", 0,
                 "MUST MOVE: if the clock is frozen this assertion FAILS (the M3-4 lesson)")
    assert_state("g117-assert-clock-hash-moved", "BoardHash", "neq", hash0,
                 "MUST CHANGE: a frozen board would keep the pinned hash (the M3-4 lesson)")
    assert_state("g118-assert-clock-auto-ticks", "AutoTicks", "gte", 1, "the clock applied at least one step")
    exec_code("g119-clock-off", invoke("SetAutoClock(0.0)"), "stop the clock")
    assert_ok("g120-assert-clock-off-auto", "LastAutoSteps", 0, "with the clock off the frame contributes nothing")

    # --- the two producers, two properties --------------------------------------------------------------
    hook = BSim()
    hook.force(cells=empty_cells, color=2, angle=2)
    exec_code("g121-hook-setup", force("board=%s;color=2;angle=2" % board_spec(empty_cells)),
              "a pinned empty board: with no shot in the air a step changes nothing")
    applied = hook.step(3)
    exec_code("g122-hook-step-3", invoke("StepFrames(3)"), "three hook steps")
    assert_ok("g123-assert-hook-3", "LastHookSteps", 3, "the hook's own property")
    samples("g124-samples-quiet", ["Steps", "BoardHash", "Elapsed", "Ticks"], 12,
            "the clock is off, so the frame loop advances Elapsed and Ticks and nothing else")
    assert_ok("g125-assert-hook-still-3", "LastHookSteps", 3,
              "after twelve frames the hook's property is STILL 3: the clock never writes it (the G1 lesson)")
    assert_ok("g126-assert-auto-0", "LastAutoSteps", 0, "while the clock's own property is 0")
    assert_ok("g127-assert-auto-ticks-0", "AutoTicks", 0, "and it applied nothing at all")
    assert_ok("g128-assert-steps-still", "Steps", hook.steps, "the simulation did not move on its own")

    # --- the final readback, the scene tree, and one declared boundary ------------------------------------
    exec_code("g129-final-readback", invoke("Dump()"),
              "the final state on one line: every counter this session asserted")
    shot("g130-shot-final", "pb-t3", "the final frame")
    call("g131-final-tree", "game", "running_game_get_scene_tree", {},
         "the final tree: every node name is one this game made, no @-auto names")
    assert_state("g132-assert-boundary", "NoSuchPropertyAtAll", "eq", 0,
                 "the declared boundary failure: an assertion on a property that does not exist (-32001)")


def main():
    editor_phase()
    game_phase()
    session = {"import": True, "calls": CALLS}
    with io.open(OUT, "w", encoding="utf-8", newline="\n") as handle:
        json.dump(session, handle, ensure_ascii=False, indent=1)
        handle.write("\n")
    manifest = []
    for entry in CALLS:
        if entry.get("tool") != "running_game_assert_node_state":
            continue
        args = entry["arguments"]
        manifest.append({"tag": entry["tag"], "property": args["property"],
                         "operator": args["operator"], "expected": args["expected"],
                         "declared_boundary": args["property"].startswith("NoSuchProperty")})
    manifest_path = os.path.join(HERE, "expectations-puzzlebobble.json")
    with io.open(manifest_path, "w", encoding="utf-8", newline="\n") as handle:
        json.dump(manifest, handle, ensure_ascii=False, indent=1)
        handle.write("\n")
    editor = len([c for c in CALLS if c["port"] == "editor"])
    game = len([c for c in CALLS if c["port"] == "game"])
    print("wrote %s" % OUT)
    print("calls: %d (editor %d / game %d)" % (len(CALLS), editor, game))
    print("expectations: %d -> %s" % (len(manifest), manifest_path))
    initial = BSim()
    print("initial board: %s" % initial.board_string())
    print("initial hash : %d  bubbles=%d" % (initial.board_hash(), initial.bubbles_in_use()))

    def scenario(name, cells, color, angle, steps):
        sim = BSim()
        sim.force(cells=cells, color=color, angle=angle)
        sim.shoot()
        applied = sim.step(steps)
        print("%-8s attach=%s chain=%d cleared=%d dropped=%d score=%d board=%s won=%s failed=%s applied=%d"
              % (name, sim.attach, sim.last_chain, sim.last_cleared, sim.last_dropped, sim.score,
                 sim.board_string(), sim.won, sim.failed, applied))
        return sim

    scenario("match", {(0, 0): 0, (4, 2): 5, (3, 3): 1, (5, 3): 1}, 1, 2, 9)
    scenario("fork", {(0, 0): 0, (4, 3): 2, (4, 4): 2, (4, 5): 2, (3, 6): 1, (5, 6): 1}, 1, 2, 7)
    scenario("fail", {(4, row): 5 for row in range(0, 10)}, 2, 2, 3)
    scenario("win", {(4, 0): 3, (4, 1): 3}, 3, 2, 16)
    scenario("ceiling", {}, 2, 2, 12)
    with io.open(OUT, "r", encoding="utf-8") as handle:
        again = json.load(handle)
    assert len(again["calls"]) == len(CALLS)
    print("json round-trip: OK (%d calls)" % len(again["calls"]))
    return 0


if __name__ == "__main__":
    sys.exit(main())
