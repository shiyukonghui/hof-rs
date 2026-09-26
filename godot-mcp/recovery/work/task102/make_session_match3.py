# -*- coding: utf-8 -*-
"""TASK-102: build the Match-3 session (editor + game phases).

Same shape as the TASK-098/099/100/101 generators, with the template that is now fixed:

  * the static nodes go in through ONE editor_add_nodes_batch call;
  * the scene's batch is run a SECOND time on purpose, so the TASK-097 D-3
    refusal is part of this game's own evidence;
  * every multi-frame sample is started BEFORE the state it observes changes,
    and the state is then pinned with ONE ForceTestState call;
  * any clock is a FLOAT ACCUMULATOR (Elapsed += delta, _autoAccum += delta*rate),
    never (int)(delta*rate) -- the F-1 lesson -- and each producer owns its own
    property (LastHookSteps vs LastAutoSteps): two producers, two properties;
  * one property, one writer.

THE INDEPENDENT RECOMPUTATION.  ``MSim`` below is a second implementation of the
payload's own rules -- the run scan in both directions, the clear, the per-column
gravity with the exact fill order, the linear congruential refill, the chain
scoring, the legality test a swap must pass -- written from the rules rather than
translated from the C#.  Every literal this generator bakes into the session (the
resulting board, both hashes, the cleared count, the chain length, the score)
is the one ``MSim`` produced, so a cascade the C# resolves differently shows up
as a FAILED assertion.
"""
import io
import json
import os

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.abspath(os.path.join(HERE, "..", "..", ".."))
SESSION_DIR = os.path.join(ROOT, "tools", "sessions", "match3")
OUT = os.path.join(SESSION_DIR, "session.json")

COLS = 8
ROWS = 8
COLORS = 6
POINTS = 10
CELL = 56
DEFAULT_SEED = 12345


def i32(v):
    v &= 0xFFFFFFFF
    return v - 0x100000000 if v >= 0x80000000 else v


class MSim(object):
    """A second implementation of Match-3's rules, written from the spec."""

    def __init__(self, board, seed=DEFAULT_SEED, score=0, moves=0, target=500,
                 move_limit=30):
        if isinstance(board, str):
            raw = board.split("/")
            self.rows = len(raw)
            self.cols = max(len(line) for line in raw)
            self.cell = [[int(ch) for ch in line] for line in raw]
        else:
            self.cell = [list(row) for row in board]
            self.rows = len(self.cell)
            self.cols = len(self.cell[0])
        self.seed = seed
        self.score = score
        self.moves = moves
        self.target = target
        self.move_limit = move_limit
        self.rejected = 0
        self.refills = 0
        self.last_cleared = 0
        self.total_cleared = 0
        self.last_chain = 0
        self.max_chain = 0
        self.cascades = 0
        self.last_swap = ""
        self.won = self.score >= self.target
        self.game_over = self.won or self.moves >= self.move_limit

    # --- the generator ---------------------------------------------------------
    def next_gem(self):
        self.seed = (self.seed * 1103515245 + 12345) & 0x7FFFFFFF
        return (self.seed >> 16) % COLORS

    # --- the board -------------------------------------------------------------
    def find_matches(self):
        flag = [[False] * self.cols for _ in range(self.rows)]
        for r in range(self.rows):
            c = 0
            while c < self.cols:
                value = self.cell[r][c]
                run = 1
                while c + run < self.cols and self.cell[r][c + run] == value:
                    run += 1
                if value >= 0 and run >= 3:
                    for k in range(run):
                        flag[r][c + k] = True
                c += run
        for c in range(self.cols):
            r = 0
            while r < self.rows:
                value = self.cell[r][c]
                run = 1
                while r + run < self.rows and self.cell[r + run][c] == value:
                    run += 1
                if value >= 0 and run >= 3:
                    for k in range(run):
                        flag[r + k][c] = True
                r += run
        return [(r, c) for r in range(self.rows) for c in range(self.cols) if flag[r][c]]

    def collapse(self):
        for c in range(self.cols):
            write = self.rows - 1
            for r in range(self.rows - 1, -1, -1):
                value = self.cell[r][c]
                if value >= 0:
                    self.cell[write][c] = value
                    if write != r:
                        self.cell[r][c] = -1
                    write -= 1
            for r in range(write, -1, -1):
                self.cell[r][c] = self.next_gem()
                self.refills += 1

    def resolve_cascade(self):
        chain = 0
        cleared = 0
        guard = 0
        while True:
            matches = self.find_matches()
            if not matches or guard >= 64:
                break
            guard += 1
            chain += 1
            count = len(matches)
            cleared += count
            self.score += POINTS * count * chain
            for (r, c) in matches:
                self.cell[r][c] = -1
            self.collapse()
        self.last_chain = chain
        self.last_cleared = cleared
        self.total_cleared += cleared
        self.max_chain = max(self.max_chain, chain)
        if chain > 0:
            self.cascades += 1
        return chain

    def board(self):
        return "/".join("".join(str(v) if v >= 0 else "-" for v in row) for row in self.cell)

    def board_hash(self):
        h = 17
        for r in range(self.rows):
            for c in range(self.cols):
                h = i32(h * 31 + (self.cell[r][c] + 1))
        return h

    def recompute(self):
        self.won = self.score >= self.target
        self.game_over = self.won or self.moves >= self.move_limit

    # --- the hooks -------------------------------------------------------------
    def makes_line(self, r1, c1, r2, c2):
        a = self.cell[r1][c1]
        self.cell[r1][c1], self.cell[r2][c2] = self.cell[r2][c2], a
        found = len(self.find_matches()) > 0
        a = self.cell[r1][c1]
        self.cell[r1][c1], self.cell[r2][c2] = self.cell[r2][c2], a
        return found

    def in_bounds(self, r, c):
        return 0 <= r < self.rows and 0 <= c < self.cols

    def swap(self, r1, c1, r2, c2):
        if not self.in_bounds(r1, c1) or not self.in_bounds(r2, c2):
            self.rejected += 1
            return "out_of_bounds"
        if abs(r1 - r2) + abs(c1 - c2) != 1:
            self.rejected += 1
            return "not_adjacent"
        if self.game_over:
            self.rejected += 1
            return "game_over"
        a = self.cell[r1][c1]
        b = self.cell[r2][c2]
        self.cell[r1][c1], self.cell[r2][c2] = b, a
        if not self.find_matches():
            self.cell[r1][c1] = a
            self.cell[r2][c2] = b
            self.rejected += 1
            return "no_match"
        self.moves += 1
        self.last_swap = "%d,%d>%d,%d" % (r1, c1, r2, c2)
        self.resolve_cascade()
        self.recompute()
        return "applied"

    def auto_step(self, steps):
        applied = 0
        for _ in range(steps):
            if self.game_over:
                break
            found = False
            for r in range(self.rows):
                for c in range(self.cols):
                    if c + 1 < self.cols and self.makes_line(r, c, r, c + 1):
                        self.swap(r, c, r, c + 1)
                        found = True
                        break
                    if r + 1 < self.rows and self.makes_line(r, c, r + 1, c):
                        self.swap(r, c, r + 1, c)
                        found = True
                        break
                if found:
                    break
            if not found:
                break
            applied += 1
        return applied

    def legal_swaps(self):
        out = []
        for r in range(self.rows):
            for c in range(self.cols):
                if c + 1 < self.cols and self.makes_line(r, c, r, c + 1):
                    out.append((r, c, r, c + 1))
                if r + 1 < self.rows and self.makes_line(r, c, r + 1, c):
                    out.append((r, c, r + 1, c))
        return out


def spec_of(board, **kwargs):
    parts = ["board=" + board]
    for key in ("seed", "score", "moves", "target", "movelimit"):
        if key in kwargs and kwargs[key] is not None:
            parts.append("%s=%s" % (key, kwargs[key]))
    return ";".join(parts)


def generated_board(seed=DEFAULT_SEED):
    """Reproduce the payload's `BuildBoard()`: fill every cell row-major from the LCG
    starting at ``seed``, then clear any match that the random fill happened to make
    (without scoring) until the board is quiet. Same generator, same order, same
    quieting loop -- so the default board is a recomputed fact and not a guess.
    (TASK-102 M3-1: the first session simply GUESSED that cell (3,5) held a 5.)"""
    sim = MSim([[0] * COLS for _ in range(ROWS)])
    sim.seed = seed
    sim.refills = 0
    for r in range(ROWS):
        for c in range(COLS):
            sim.cell[r][c] = sim.next_gem()
    guard = 0
    waves = 0
    while True:
        matches = sim.find_matches()
        if not matches or guard >= 64:
            break
        guard += 1
        waves += 1
        for (r, c) in matches:
            sim.cell[r][c] = -1
        sim.collapse()
    sim.quiet_waves = waves
    return sim


# =============================================================================
# the boards
# =============================================================================
# P: the alternating board -- quiet, and with NO legal swap at all, which is what
# makes it the natural board for "the auto step finds nothing and says so".
P_ROWS = ["01234501", "23450123", "45012345", "01234501",
          "23450123", "45012345", "01234501", "23450123"]
PLAIN = "/".join(P_ROWS)

# Q: P with two cells changed so that ONE swap is legal: exchanging (3,4) and (3,5)
# puts a fifth 5 into column 4, where rows 1 and 2 already hold two of them.
Q_ROWS = list(P_ROWS)
Q_ROWS[1] = "23455123"
Q_ROWS[2] = "45015345"
SWAP_BOARD = "/".join(Q_ROWS)

P_SIM = MSim(PLAIN)
SWAP_SIM = MSim(SWAP_BOARD)
if P_SIM.find_matches():
    raise SystemExit("FATAL: board P is not quiet")
if SWAP_SIM.find_matches():
    raise SystemExit("FATAL: board Q is not quiet")
if P_SIM.legal_swaps():
    raise SystemExit("FATAL: board P was supposed to have no legal swap: %s" % P_SIM.legal_swaps())
if not SWAP_SIM.makes_line(3, 4, 3, 5):
    raise SystemExit("FATAL: board Q's designated swap (3,4)<->(3,5) is not legal")

# --- the designated legal swap on Q, resolved by the second implementation -----
APPLY = MSim(SWAP_BOARD, seed=1000, target=100000, move_limit=1000)
APPLY_KIND = APPLY.swap(3, 4, 3, 5)
APPLY_BOARD = APPLY.board()
APPLY_HASH = APPLY.board_hash()
APPLY_SCORE = APPLY.score
APPLY_CHAIN = APPLY.last_chain
APPLY_CLEARED = APPLY.last_cleared
APPLY_TOTAL = APPLY.total_cleared
APPLY_MOVES = APPLY.moves
APPLY_SEED = APPLY.seed
APPLY_REFILLS = APPLY.refills
APPLY_CASCADES = APPLY.cascades
APPLY_MAXCHAIN = APPLY.max_chain

# --- the same board with the generator's first wave worked out by hand, as a
# second, independent cross-check of the collapse + refill + chain machinery ----
HAND = MSim(SWAP_BOARD, seed=1000, target=100000, move_limit=1000)
HAND.cell[3][4], HAND.cell[3][5] = HAND.cell[3][5], HAND.cell[3][4]
HAND_FIRST = HAND.find_matches()
if len(HAND_FIRST) != 3 or set(HAND_FIRST) != {(1, 4), (2, 4), (3, 4)}:
    raise SystemExit("FATAL: the first wave is not the three cells the design intends: %s"
                     % (HAND_FIRST,))
HAND.score += POINTS * 3 * 1
for (r, c) in HAND_FIRST:
    HAND.cell[r][c] = -1
HAND.collapse()
HAND_AFTER_FIRST = HAND.board()
HAND_SEED_AFTER_FIRST = HAND.seed
# and the generator's own full cascade must agree with that hand-worked first wave
APPLY_FIRST_NOTE = "first wave=%d cells, after the collapse the board is %s" % (
    len(HAND_FIRST), HAND_AFTER_FIRST)

# --- the illegal swap: byte-identical board, a counted refusal -----------------
REFUSE = MSim(SWAP_BOARD, seed=1000, target=100000, move_limit=1000)
REFUSE_KIND = REFUSE.swap(3, 0, 3, 1)
REFUSE_BOARD = REFUSE.board()
REFUSE_HASH = REFUSE.board_hash()

# --- the default board the payload generates in _Ready -------------------------
GEN = generated_board()
GEN_BOARD = GEN.board()
GEN_HASH = GEN.board_hash()
GEN_SEED = GEN.seed
GEN_00 = GEN.cell[0][0]
GEN_35 = GEN.cell[3][5]

# --- the three shape refusals, on ONE accumulating board, in session order ------
# (TASK-102 M3-2: the first session modelled each refusal on its own fresh copy, so
# the expected counts were 1/1/1 while the session's own board accumulated 1/2/3.)
SHAPE = MSim(SWAP_BOARD, seed=1000, target=100000, move_limit=1000)
SHAPE_KIND1 = SHAPE.swap(3, 0, 3, 1)
SHAPE_REJ_1 = SHAPE.rejected
SHAPE_BOARD_1 = SHAPE.board()
SHAPE_HASH_1 = SHAPE.board_hash()
SHAPE_KIND2 = SHAPE.swap(0, 0, 0, 2)
SHAPE_REJ_2 = SHAPE.rejected
SHAPE_KIND3 = SHAPE.swap(0, 0, 0, 9)
SHAPE_REJ_3 = SHAPE.rejected
SHAPE_BOARD_3 = SHAPE.board()

# --- AutoStep on the board with no legal move ----------------------------------
P_AUTO = MSim(PLAIN, seed=1000, target=100000, move_limit=1000)
P_AUTO_APPLIED = P_AUTO.auto_step(3)

# --- AutoStep(1) on Q: once, exactly -------------------------------------------
Q_AUTO = MSim(SWAP_BOARD, seed=1000, target=100000, move_limit=1000)
Q_AUTO_APPLIED = Q_AUTO.auto_step(1)
Q_AUTO_BOARD = Q_AUTO.board()
Q_AUTO_HASH = Q_AUTO.board_hash()
Q_AUTO_MOVES = Q_AUTO.moves
Q_AUTO_SCORE = Q_AUTO.score
Q_AUTO_SWAP = Q_AUTO.last_swap
Q_AUTO_SEED = Q_AUTO.seed
Q_AUTO_REFILLS = Q_AUTO.refills

# --- the win: a score pinned just below the target -----------------------------
WIN = MSim(SWAP_BOARD, seed=1000, score=490, target=500, move_limit=1000)
WIN_KIND = WIN.swap(3, 4, 3, 5)
WIN_SCORE = WIN.score
WIN_WON = WIN.won
WIN_OVER = WIN.game_over

# --- the loss: a single move allowed, and not enough points --------------------
LOSS = MSim(SWAP_BOARD, seed=1000, target=100000, move_limit=1)
LOSS_KIND = LOSS.swap(3, 4, 3, 5)
LOSS_MOVES = LOSS.moves
LOSS_WON = LOSS.won
LOSS_OVER = LOSS.game_over
LOSS_AFTER = LOSS.swap(0, 0, 0, 1)
LOSS_REJECTED = LOSS.rejected

# --- a cascade of two or more waves, searched for deterministically ------------
def search_cascade(min_chain):
    """Change one cell of P at a time (value 0..5) and look for a legal swap whose
    cascade is at least ``min_chain`` waves long. Deterministic: the scan order is
    fixed, so the board it finds is the board the session pins."""
    for r in range(ROWS):
        for c in range(COLS):
            for value in range(COLORS):
                rows = [[int(ch) for ch in line] for line in P_ROWS]
                if rows[r][c] == value:
                    continue
                rows[r][c] = value
                text = "/".join("".join(str(v) for v in row) for row in rows)
                sim = MSim(text)
                if sim.find_matches():
                    continue
                for (r1, c1, r2, c2) in sim.legal_swaps():
                    trial = MSim(text, seed=1000)
                    trial.swap(r1, c1, r2, c2)
                    if trial.last_chain >= min_chain:
                        return {
                            "board": text, "change": (r, c, value), "swap": (r1, c1, r2, c2),
                            "chain": trial.last_chain, "cleared": trial.last_cleared,
                            "score": trial.score, "board_after": trial.board(),
                            "hash_after": trial.board_hash(), "seed_after": trial.seed,
                            "refills": trial.refills, "total": trial.total_cleared,
                            "max_chain": trial.max_chain, "cascades": trial.cascades,
                        }
    return None


CHAIN_FOUND = search_cascade(2)
if CHAIN_FOUND is None:
    raise SystemExit("FATAL: no single-cell variant of P produced a two-wave cascade")

# --- the board the auto-clock sample pins ---------------------------------------
# (TASK-102 M3-4: r2 pinned board Q, which has exactly ONE legal swap. The clock
# consumed it in the two or three calls between SetAutoClock and the first sampled
# frame, so the 30-frame sample recorded a board that could not change -- AutoTicks
# climbed 4 -> 33 while Moves, Score, BoardHash and Refills never moved once -- and
# every assertion still passed. A sample board must be one the game can keep
# PLAYING for the whole window, and the endurance below is checked here, in Python,
# before the session is written.)
CLOCK_BOARD = GEN_BOARD
CLOCK_SEED = 1000
CLOCK_ENDURANCE = 40
CLOCK_PROBE = MSim(CLOCK_BOARD, seed=CLOCK_SEED, target=100000, move_limit=1000)
CLOCK_APPLIED = CLOCK_PROBE.auto_step(CLOCK_ENDURANCE)
CLOCK_AFTER = CLOCK_PROBE.board()
CLOCK_AFTER_HASH = CLOCK_PROBE.board_hash()
CLOCK_MOVES = CLOCK_PROBE.moves
CLOCK_CLEARED = CLOCK_PROBE.total_cleared
if CLOCK_APPLIED < CLOCK_ENDURANCE or CLOCK_AFTER_HASH == GEN_HASH:
    raise SystemExit("FATAL: the clock board cannot play %d auto steps (applied %d)"
                     % (CLOCK_ENDURANCE, CLOCK_APPLIED))

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


def probe(tag, row, col, note):
    hook(tag, "ProbeCell(%d, %d)" % (row, col), note)


def swap(tag, r1, c1, r2, c2, note):
    hook(tag, "Swap(%d, %d, %d, %d)" % (r1, c1, r2, c2), note)


BG = {"type": "ColorRect", "name": "Background", "parent_path": ".",
      "properties": {"offset_left": 0, "offset_top": 0, "offset_right": 800,
                     "offset_bottom": 600, "color": {"r": 0.05, "g": 0.04, "b": 0.08, "a": 1}}}
HUD = {"type": "Label", "name": "Hud", "parent_path": ".",
       "properties": {"offset_left": 14, "offset_top": 10, "offset_right": 640,
                      "offset_bottom": 44, "text": "TARGET 500  SCORE 0  MOVES 0/30  CHAIN 0  CLEARED 0",
                      "theme_override_font_sizes/font_size": 22}}
STATUS = {"type": "Label", "name": "Status", "parent_path": ".",
          "properties": {"offset_left": 612, "offset_top": 10, "offset_right": 795,
                         "offset_bottom": 44, "text": "MATCH AND CLEAR",
                         "theme_override_font_sizes/font_size": 22}}
STATIC_BATCH = [BG, HUD, STATUS]

# =============================================================================
# editor phase (14 calls)
# =============================================================================
e("e01-edit-game", "project_edit_script",
  {"path": "res://src/Match3Game.cs", "content_file": "payload/Match3Game.cs"},
  "the whole game is written through the MCP script writer (the template stub is replaced)")
e("e02-open-scene", "editor_open_scene", {"path": "res://scenes/main.tscn"},
  "the template scene carries the root Main (Node2D) the script is attached to")
e("e03-batch-add-static", "editor_add_nodes_batch", {"nodes": STATIC_BATCH},
  "the three static nodes of the scene, through the batch tool: a background and two labels; "
  "every gem cell is created at run time")
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
e("e10-action-move", "editor_add_input_action", {"action": "m3_auto_move", "key": "Space"},
  "one deterministic auto move")
e("e11-action-left", "editor_add_input_action", {"action": "m3_left", "key": "A"},
  "a declared direction (unused by the payload's move selection, declared for parity)")
e("e12-action-right", "editor_add_input_action", {"action": "m3_right", "key": "D"},
  "a declared direction")
e("e13-build-csharp", "project_build_csharp",
  {"configuration": "Debug", "timeout_ms": 300000, "rescan": True},
  "compile the game the MCP script writer just wrote")
e("e14-validate-scripts", "project_validate_scripts", {}, "the engine's own per-file verdict")

# =============================================================================
# game phase
# =============================================================================
g("g01-scene-tree", "running_game_get_scene_tree", {},
  "the running tree: the three static nodes plus the sixty-four gem cells created at run time")
hook("g02-readback-t0", "Dump()", "the whole board as one line plus every fact")
assert_state("g03-assert-cols", "Cols", "eq", COLS, "the board is eight columns wide")
assert_state("g04-assert-rows", "Rows", "eq", ROWS, "and eight rows tall")
assert_state("g05-assert-colors", "Colors", "eq", COLORS, "six gem colours")
assert_state("g06-assert-cell", "Cell", "eq", CELL, "fifty-six pixels a cell")
hook("g07-assert-default-board", "Dump()",
     "the default board generated from the seed, for the record")
assert_state("g07a-assert-default-board", "Board", "eq", GEN_BOARD,
             "the default board the payload generates in _Ready is the one the Python "
             "re-implementation of the same LCG and the same quieting loop produces")
assert_state("g07b-assert-default-hash", "BoardHash", "eq", GEN_HASH,
             "and its hash agrees")
assert_state("g07c-assert-default-seed", "Seed", "eq", GEN_SEED,
             "the generator advanced to exactly the re-implementation's state while the "
             "board was filled and quieted")
probe("g08-probe-0-0", 0, 0, "the top-left cell")
assert_state("g09-assert-probe-state", "ProbeState", "eq", "gem%d" % GEN_00,
             "it reads as the colour the generator puts there")
probe("g10-probe-3-5", 3, 5, "a cell from the middle")
assert_state("g11-assert-probe-value", "ProbeValue", "eq", GEN_35,
             "with the colour the generator puts there -- recomputed, not guessed")
shot("g12-shot-t0", "m3-t0", "the first frame: the generated board")
samples("g13-samples-frozen",
        ["BoardHash", "Moves", "Score", "TotalCleared", "Elapsed", "Ticks"], 12,
        "determinism baseline: with AutoClock 0 the board does not change while the clock runs "
        "(board hash / moves / score / cleared all constant, Elapsed and Ticks both increasing)")
assert_state("g14-assert-frozen-auto-0", "LastAutoSteps", "eq", 0,
             "the clock's per-frame delta is zero while the clock is off")
# --- the quiet board: no legal swap anywhere ----------------------------------
force("g15-plain-setup", spec_of(PLAIN, seed=1000, target=100000, movelimit=1000),
      "the alternating board: quiet, and with no legal swap at all")
assert_state("g16-assert-plain-board", "Board", "eq", PLAIN,
             "the board is exactly the pinned one")
assert_state("g17-assert-plain-hash", "BoardHash", "eq", P_SIM.board_hash(),
             "and its hash is the one the Python re-implementation computes")
assert_state("g18-assert-moves-0", "Moves", "eq", 0, "no move yet")
assert_state("g19-assert-rejected-0", "RejectedMoves", "eq", 0, "and no refusal")
hook("g20-plain-autostep", "AutoStep(3)",
     "three auto steps on a board with no legal swap: the hook must report zero applied")
assert_state("g21-assert-plain-applied-0", "LastHookSteps", "eq", P_AUTO_APPLIED,
             "the hook reports the steps it really applied -- zero, because there is no legal move")
assert_state("g22-assert-plain-moves-0", "Moves", "eq", 0, "and nothing moved")
assert_state("g23-assert-last-auto-0", "LastAutoSteps", "eq", 0,
             "while the clock's own per-frame delta is a different property and is zero too")
# --- the illegal swap: refused, board byte-identical ---------------------------
force("g24-refuse-setup", spec_of(SWAP_BOARD, seed=1000, target=100000, movelimit=1000),
      "a board where one designated swap is legal and others are not")
assert_state("g25-assert-setup-board", "Board", "eq", SWAP_BOARD, "the pinned board")
assert_state("g26-assert-setup-hash", "BoardHash", "eq", SWAP_SIM.board_hash(),
             "its hash, from the re-implementation")
swap("g27-swap-illegal", 3, 0, 3, 1, "a swap that makes no line: it must be refused")
assert_state("g28-assert-reason-nomatch", "LastEvent", "contains", "reason=no_match",
             "the refusal names the rule")
assert_state("g29-assert-rejected-1", "RejectedMoves", "eq", SHAPE_REJ_1,
             "the refusal is counted")
assert_state("g30-assert-board-unchanged", "Board", "eq", SHAPE_BOARD_1,
             "and the board is byte-identical to the board before the swap")
assert_state("g31-assert-hash-unchanged", "BoardHash", "eq", SHAPE_HASH_1,
             "the hash did not move either -- that is what 'refused' means")
assert_state("g32-assert-moves-still-0", "Moves", "eq", 0, "no move was accepted")
swap("g33-swap-not-adjacent", 0, 0, 0, 2, "a swap between two cells that are not neighbours")
assert_state("g34-assert-reason-nonadj", "LastEvent", "contains", "reason=not_adjacent",
             "refused by name")
assert_state("g35-assert-rejected-2", "RejectedMoves", "eq", SHAPE_REJ_2,
             "and counted -- on the SAME board, so the count is cumulative (M3-2: the first "
             "session modelled each refusal on its own fresh copy)")
swap("g36-swap-out-of-bounds", 0, 0, 0, 9, "a swap that leaves the board")
assert_state("g37-assert-reason-oob", "LastEvent", "contains", "reason=out_of_bounds",
             "refused by name")
assert_state("g38-assert-rejected-3", "RejectedMoves", "eq", SHAPE_REJ_3, "and counted")
assert_state("g39-assert-board-still", "Board", "eq", SHAPE_BOARD_3,
             "after three refusals the board is still exactly the pinned one")
# --- the legal swap: the cascade the re-implementation predicts ----------------
force("g40-apply-setup", spec_of(SWAP_BOARD, seed=1000, target=100000, movelimit=1000),
      "the same board, now for the legal swap")
assert_state("g41-assert-seed", "Seed", "eq", 1000, "the refill generator starts at the pinned seed")
swap("g42-swap-legal", 3, 4, 3, 5, "the designated legal swap")
assert_state("g43-assert-kind", "LastEvent", "contains", "chain=",
             "the hook names the cascade it ran")
assert_state("g44-assert-moves-1", "Moves", "eq", APPLY_MOVES, "one move accepted")
assert_state("g45-assert-last-swap", "LastSwap", "eq", "3,4>3,5", "and it is the swap that was asked for")
assert_state("g46-assert-cleared", "LastCleared", "eq", APPLY_CLEARED,
             "the first wave cleared exactly the three cells the design intends")
assert_state("g47-assert-chain", "LastChain", "eq", APPLY_CHAIN,
             "the cascade length the re-implementation computes")
assert_state("g48-assert-score", "Score", "eq", APPLY_SCORE,
             "ten points a gem times the chain index, as the re-implementation scores it")
assert_state("g49-assert-total", "TotalCleared", "eq", APPLY_TOTAL, "total cleared agrees")
assert_state("g50-assert-cascades", "Cascades", "eq", APPLY_CASCADES, "one cascade resolved")
assert_state("g51-assert-max-chain", "MaxChain", "eq", APPLY_MAXCHAIN, "and it is the longest so far")
assert_state("g52-assert-board-after", "Board", "eq", APPLY_BOARD,
             "the board after the whole cascade -- the clear, the fall, the refill and every "
             "follow-on wave -- is the board the second implementation produces")
assert_state("g53-assert-hash-after", "BoardHash", "eq", APPLY_HASH,
             "and so is its hash")
assert_state("g54-assert-seed-after", "Seed", "eq", APPLY_SEED,
             "the refill generator advanced to exactly the re-implementation's state")
assert_state("g55-assert-refills", "Refills", "eq", APPLY_REFILLS,
             "and it generated exactly that many gems")
shot("g56-shot-t1", "m3-t1", "the board after the cascade")
# --- the deterministic auto move, once -----------------------------------------
force("g57-auto-setup", spec_of(SWAP_BOARD, seed=1000, target=100000, movelimit=1000),
      "the same board for the auto step")
hook("g58-auto-step-1", "AutoStep(1)", "exactly one deterministic auto move")
assert_state("g59-assert-auto-applied-1", "LastHookSteps", "eq", Q_AUTO_APPLIED,
             "the DELTA of that call is exact -- this is the frame-rate independent quantity")
assert_state("g60-assert-auto-moves-1", "Moves", "eq", Q_AUTO_MOVES, "one move was played")
assert_state("g61-assert-auto-swap", "LastSwap", "eq", Q_AUTO_SWAP,
             "and it is the FIRST legal swap in row-major order, right before down")
assert_state("g62-assert-auto-score", "Score", "eq", Q_AUTO_SCORE, "with the re-implementation's score")
assert_state("g63-assert-auto-board", "Board", "eq", Q_AUTO_BOARD,
             "and the resulting board is the re-implementation's")
assert_state("g64-assert-auto-hash", "BoardHash", "eq", Q_AUTO_HASH, "hash agrees")
assert_state("g65-assert-auto-seed", "Seed", "eq", Q_AUTO_SEED, "seed agrees")
assert_state("g66-assert-auto-refills", "Refills", "eq", Q_AUTO_REFILLS, "refill count agrees")
# --- a cascade of two or more waves --------------------------------------------
CHAIN_SPEC = spec_of(CHAIN_FOUND["board"], seed=1000, target=100000, movelimit=1000)
force("g67-chain-setup", CHAIN_SPEC,
      "a board whose designated swap makes a line that, once cleared and refilled, makes another")
swap("g68-chain-swap", CHAIN_FOUND["swap"][0], CHAIN_FOUND["swap"][1],
     CHAIN_FOUND["swap"][2], CHAIN_FOUND["swap"][3],
     "the designated swap of the searched board: board=%s (one cell changed from the quiet "
     "board at %s), swap %s" % (CHAIN_FOUND["board"], CHAIN_FOUND["change"],
                                CHAIN_FOUND["swap"]))
assert_state("g69-assert-chain-len", "LastChain", "eq", CHAIN_FOUND["chain"],
             "the cascade really has that many waves -- a chain, not a single match")
assert_state("g70-assert-chain-len-gt1", "LastChain", "gt", 1, "and there is more than one wave")
assert_state("g71-assert-chain-cleared", "LastCleared", "eq", CHAIN_FOUND["cleared"],
             "the total the re-implementation clears across all waves")
assert_state("g72-assert-chain-score", "Score", "eq", CHAIN_FOUND["score"],
             "the chain-weighted score the re-implementation computes")
assert_state("g73-assert-chain-board", "Board", "eq", CHAIN_FOUND["board_after"],
             "the final board agrees")
assert_state("g74-assert-chain-hash", "BoardHash", "eq", CHAIN_FOUND["hash_after"], "hash agrees")
assert_state("g75-assert-chain-seed", "Seed", "eq", CHAIN_FOUND["seed_after"], "seed agrees")
assert_state("g76-assert-chain-max", "MaxChain", "eq", CHAIN_FOUND["max_chain"],
             "the longest chain on the record")
shot("g77-shot-t2", "m3-t2", "the board after the multi-wave cascade")
# --- the win -------------------------------------------------------------------
force("g78-win-setup", spec_of(SWAP_BOARD, seed=1000, score=490, target=500, movelimit=1000),
      "the score pinned just below the target")
assert_state("g79-assert-not-won-yet", "Won", "eq", False, "not there yet")
assert_state("g80-assert-score-pinned", "Score", "eq", 490, "at the pinned score")
swap("g81-win-swap", 3, 4, 3, 5, "the legal swap, which now crosses the target")
assert_state("g82-assert-score-win", "Score", "eq", WIN_SCORE, "the score the re-implementation reaches")
assert_state("g83-assert-won", "Won", "eq", WIN_WON, "the target ends the game in a win")
assert_state("g84-assert-over", "GameOver", "eq", WIN_OVER, "and the board is over")
swap("g85-swap-after-win", 0, 0, 0, 1, "a swap after the win is refused")
assert_state("g86-assert-reason-over", "LastEvent", "contains", "reason=game_over",
             "the refusal names the rule")
shot("g87-shot-t3", "m3-t3", "the win frame: TARGET REACHED on the status label")
g("g88-assert-screen-win", "running_game_assert_screen_text", {"text": "TARGET REACHED"},
  "the status label really is on the captured screen")
# --- the loss ------------------------------------------------------------------
force("g89-loss-setup", spec_of(SWAP_BOARD, seed=1000, target=100000, movelimit=1),
      "a single move allowed, and a target no single move can reach")
swap("g90-loss-swap", 3, 4, 3, 5, "play the one allowed move")
assert_state("g91-assert-loss-moves", "Moves", "eq", LOSS_MOVES, "the move is on the record")
assert_state("g92-assert-loss-over", "GameOver", "eq", LOSS_OVER,
             "running out of moves ends the game as a loss")
assert_state("g93-assert-loss-not-won", "Won", "eq", LOSS_WON, "and it is not a win")
swap("g94-loss-swap-after", 0, 0, 0, 1, "any further swap is refused")
assert_state("g95-assert-loss-reason", "LastEvent", "contains", "reason=game_over",
             "refused by name")
assert_state("g96-assert-loss-rejected", "RejectedMoves", "eq", LOSS_REJECTED, "and counted")
shot("g97-shot-t4", "m3-t4", "the loss frame: OUT OF MOVES on the status label")
g("g98-assert-screen-loss", "running_game_assert_screen_text", {"text": "OUT OF MOVES"},
  "the status label really is on the captured screen")
# --- the clock: the board really moves, frame after frame ----------------------
force("g99-clock-setup",
      spec_of(CLOCK_BOARD, seed=CLOCK_SEED, target=100000, movelimit=1000),
      "the board the clock sample pins; the target and the move limit are pinned out of reach so "
      "the board CANNOT be decided inside the window, and the board itself is one the Python "
      "re-implementation proves can keep playing for %d auto steps (M3-4)" % CLOCK_ENDURANCE)
assert_state("g99a-assert-clock-board", "Board", "eq", CLOCK_BOARD, "the pinned board")
assert_state("g99b-assert-clock-board-hash", "BoardHash", "eq", GEN_HASH,
             "and the hash it starts the window at -- the 'the board changed' assertion below "
             "compares against exactly this value")
assert_state("g99c-assert-clock-moves-0", "Moves", "eq", 0, "no move yet")
assert_state("g99d-assert-clock-cleared-0", "TotalCleared", "eq", 0, "and nothing cleared")
hook("g100-clock-on", "SetAutoClock(60.0)",
     "the one sample that watches the board move asks for motion explicitly")
samples("g101-samples-clock",
        ["BoardHash", "Moves", "Score", "TotalCleared", "MaxChain", "LastChain", "Refills",
         "AutoTicks", "LastAutoSteps", "Elapsed", "Ticks"], 30,
        "multi-frame property sample of the auto clock: the board is played move by move "
        "(BoardHash changes), the score and the cleared count climb, and Elapsed and Ticks "
        "advance -- 'the board moves' as a sequence of values, not as an adjective")
assert_state("g102-assert-clock-moves", "Moves", "gt", 1,
             "the clock really played several moves inside the sample window")
assert_state("g103-assert-clock-cleared", "TotalCleared", "gt", 0, "and gems were really cleared")
assert_state("g104-assert-clock-auto-ticks", "AutoTicks", "gt", 2, "the auto clock really ticked")
assert_state("g104a-assert-clock-board-moved", "BoardHash", "neq", GEN_HASH,
             "and the board is NOT the one the window started on -- the M3-4 lesson stated as an "
             "assertion: a frozen board now FAILS instead of merely looking quiet")
assert_state("g104b-assert-clock-score", "Score", "gt", 0, "the cascade scored inside the window")
assert_state("g105-assert-clock-not-over", "GameOver", "eq", False,
             "and the board was never decided inside the window -- the sample watched a live board")
hook("g106-clock-off", "SetAutoClock(0.0)", "back to frozen")
assert_state("g107-assert-clock-off-auto", "LastAutoSteps", "eq", 0, "the per-frame delta is zero again")
shot("g108-shot-t5", "m3-t5", "the board after the clock played it for a while")
# --- the declared input path really drives the game ----------------------------
force("g109-input-setup", spec_of(SWAP_BOARD, seed=1000, target=100000, movelimit=1000),
      "the same board for the input test")
hook("g110-poll-on", "SetPollInput(true)",
     "the input path is off by default; the test switches it on explicitly")
g("g111-input-move", "running_game_run_test_scenario",
  {"steps": [{"type": "input", "action": "m3_auto_move", "pressed": True},
             {"type": "wait", "seconds": 0.45},
             {"type": "assert", "node_path": "Main", "property": "Moves",
              "operator": "gte", "expected": 1}]},
  "the declared action really plays a move")
assert_state("g112-assert-input-moves-1", "InputMoves", "eq", 1,
             "the declared action fires on the PRESS EDGE, so a scenario's never-released key "
             "performs exactly one move instead of repeating at the frame rate")
assert_state("g113-assert-moves-ge-1", "Moves", "gte", 1, "and a move is on the record")
hook("g114-poll-off", "SetPollInput(false)",
     "polling off again: nothing after this can drift because a key is still marked held")
# --- positive control: a node created at run time is drawn ---------------------
g("g115-runtime-overlay", "running_game_execute_gdscript",
  code('var main = get_parent()\nvar c = ColorRect.new()\nc.name = StringName("ProbeOverlay")\n'
       'c.position = Vector2(20, 556)\nc.size = Vector2(120, 30)\n'
       'c.color = Color(0.95, 0.35, 0.95, 1.0)\nmain.add_child(c)\nreturn "overlay added"'),
  "a node created at run time, in the same session, as the positive control for 'a run-time node "
  "is drawn'")
# --- DECLARED FAILURE: the error path of the assertion tool ---------------------
g("g116-assert-unknown-property", "running_game_assert_node_state",
  {"node_path": "Main", "property": "NoSuchProperty", "operator": "eq", "expected": 1},
  "DECLARED FAILURE: a boundary call asking for a property that does not exist (-32001), so the "
  "error path of the assertion tool is on the record too")
shot("g117-shot-t6", "m3-t6", "the overlay is visible in this frame and not in t5")
force("g118-final-board", spec_of(SWAP_BOARD, seed=1000, target=100000, movelimit=1000),
      "ask for the pinned board once more")
assert_state("g119-assert-final-board", "Board", "eq", SWAP_BOARD, "the board is back")
assert_state("g120-assert-final-hash", "BoardHash", "eq", SWAP_SIM.board_hash(),
             "and it reproduces the very same hash the Python re-implementation predicted")
hook("g121-final-readback", "Dump()", "the final board as one line")
g("g122-final-tree", "running_game_get_scene_tree", {},
  "the final tree, including the run-time overlay")

doc = {"import": True, "calls": calls}
os.makedirs(os.path.dirname(OUT), exist_ok=True)
with io.open(OUT, "w", encoding="utf-8", newline="\n") as handle:
    handle.write(json.dumps(doc, ensure_ascii=False, indent=1) + "\n")

print("wrote %s calls=%d" % (OUT, len(calls)))
print("GEN    board=%s" % GEN_BOARD)
print("       hash=%d seed=%d quiet_waves=%d cell(0,0)=%d cell(3,5)=%d"
      % (GEN_HASH, GEN_SEED, GEN.quiet_waves, GEN_00, GEN_35))
print("PLAIN  hash=%d legal_swaps=%d" % (P_SIM.board_hash(), len(P_SIM.legal_swaps())))
print("Q      board=%s hash=%d" % (SWAP_BOARD, SWAP_SIM.board_hash()))
print("APPLY  kind=%s moves=%d chain=%d cleared=%d score=%d total=%d cascades=%d max=%d "
      "seed=%d refills=%d" % (APPLY_KIND, APPLY_MOVES, APPLY_CHAIN, APPLY_CLEARED, APPLY_SCORE,
                              APPLY_TOTAL, APPLY_CASCADES, APPLY_MAXCHAIN, APPLY_SEED,
                              APPLY_REFILLS))
print("       board_after=%s hash=%d" % (APPLY_BOARD, APPLY_HASH))
print("HAND   first_wave=%s score_after_first=%d board_after_first=%s seed_after_first=%d"
      % (HAND_FIRST, HAND.score, HAND_AFTER_FIRST, HAND_SEED_AFTER_FIRST))
print("SHAPE  kind1=%s rej=%d kind2=%s rej=%d kind3=%s rej=%d board=%s"
      % (SHAPE_KIND1, SHAPE_REJ_1, SHAPE_KIND2, SHAPE_REJ_2, SHAPE_KIND3, SHAPE_REJ_3,
         SHAPE_BOARD_3))
print("REFUSE kind=%s board=%s" % (REFUSE_KIND, REFUSE_BOARD))
print("P_AUTO applied=%d  Q_AUTO applied=%d swap=%s moves=%d score=%d board=%s seed=%d"
      % (P_AUTO_APPLIED, Q_AUTO_APPLIED, Q_AUTO_SWAP, Q_AUTO_MOVES, Q_AUTO_SCORE,
         Q_AUTO_BOARD, Q_AUTO_SEED))
print("WIN    kind=%s score=%d won=%s over=%s" % (WIN_KIND, WIN_SCORE, WIN_WON, WIN_OVER))
print("LOSS   kind=%s moves=%d won=%s over=%s after=%s rejected=%d"
      % (LOSS_KIND, LOSS_MOVES, LOSS_WON, LOSS_OVER, LOSS_AFTER, LOSS_REJECTED))
print("CHAIN  change=%s board=%s" % (CHAIN_FOUND["change"], CHAIN_FOUND["board"]))
print("       swap=%s chain=%d cleared=%d score=%d board_after=%s seed=%d max=%d"
      % (CHAIN_FOUND["swap"], CHAIN_FOUND["chain"], CHAIN_FOUND["cleared"],
         CHAIN_FOUND["score"], CHAIN_FOUND["board_after"], CHAIN_FOUND["seed_after"],
         CHAIN_FOUND["max_chain"]))
print("CLOCK  board=%s seed=%d" % (CLOCK_BOARD, CLOCK_SEED))
print("       auto_step(%d) applied=%d moves=%d cleared=%d board_after=%s hash=%d"
      % (CLOCK_ENDURANCE, CLOCK_APPLIED, CLOCK_MOVES, CLOCK_CLEARED, CLOCK_AFTER,
         CLOCK_AFTER_HASH))
