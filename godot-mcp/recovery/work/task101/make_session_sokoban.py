# -*- coding: utf-8 -*-
"""TASK-101: build the Sokoban session (editor + game phases).

Same shape as the TASK-098/099/100 generators, with the template that is now fixed:

  * the static nodes go in through ONE editor_add_nodes_batch call;
  * the scene's batch is run a SECOND time on purpose, so the TASK-097 D-3
    refusal is part of this game's own evidence;
  * every multi-frame sample is started BEFORE the state it observes changes,
    and the state is then pinned with ONE ForceTestState call;
  * any clock is a FLOAT ACCUMULATOR (Elapsed += delta, _autoAccum += delta*rate),
    never (int)(delta*rate) -- the F-1 lesson -- and each producer owns its own
    property (LastHookSteps vs LastAutoSteps): two producers, two properties;
  * one property, one writer.

THE INDEPENDENT RECOMPUTATION.  ``Sim`` below is a second implementation of the
payload's own rules -- level parsing, the move/push legality test, the undo
stack, the simple corner/2x2 deadlock test and the board hash -- written from the
rules rather than translated from the C#, and the expected literals this generator
bakes into the session are the ones it produces.  A push that the C# gets wrong
therefore shows up as a FAILED assertion, not as a transcription.
"""
import io
import json
import os

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", ".."))
SESSION_DIR = os.path.join(ROOT, "tools", "sessions", "sokoban")
OUT = os.path.join(SESSION_DIR, "session.json")

BG = {"type": "ColorRect", "name": "Background", "parent_path": ".",
      "properties": {"offset_left": 0, "offset_top": 0, "offset_right": 800,
                     "offset_bottom": 600, "color": {"r": 0.05, "g": 0.06, "b": 0.08, "a": 1}}}
HUD = {"type": "Label", "name": "Hud", "parent_path": ".",
       "properties": {"offset_left": 16, "offset_top": 8, "offset_right": 620,
                      "offset_bottom": 44, "text": "LEVEL 1  BOXES 0/1  STEPS 0  PUSHES 0  UNDO 0",
                      "theme_override_font_sizes/font_size": 24}}
STATUS = {"type": "Label", "name": "Status", "parent_path": ".",
          "properties": {"offset_left": 620, "offset_top": 8, "offset_right": 795,
                         "offset_bottom": 44, "text": "PUSH THE BOXES",
                         "theme_override_font_sizes/font_size": 22}}
STATIC_BATCH = [BG, HUD, STATUS]

LEVELS = {
    0: "#######/#     #/# .$@ #/#     #/#######",
    1: "#######/#  .  #/#  $  #/#. $ @#/#     #/#######",
    2: "########/# .  . #/# $  $ #/#   @  #/########",
    3: "######/##.  #/#$   #/#  @ #/######",
}
# an open field with nothing in it: the patrol clock can walk for ever without
# ever finishing the level, so the multi-frame sample watches the PLAYER move.
OPEN = "#######/#     #/#     #/#  @  #/#     #/#######"
# a box under the top wall, nothing beside it: pushing it north runs into the wall
# while the board itself is still alive (it must NOT start already deadlocked, or the
# game-over guard would refuse the move for a different reason).
BLOCKED = "######/# $  #/#  @ #/######"
# a box that can be pushed west, into a corner, in exactly one move.
INTOCORNER = "######/##.  #/# $  #/#  @ #/######"

DIRS = {"up": (-1, 0), "down": (1, 0), "left": (0, -1), "right": (0, 1)}
PATROL = ["up", "right", "down", "left"]


class Sim(object):
    """A second implementation of Sokoban's rules, written from the spec."""

    def __init__(self, spec):
        self.spec = spec
        raw = spec.split("/")
        self.rows = len(raw)
        self.cols = max(len(line) for line in raw)
        self.wall = [[False] * self.cols for _ in range(self.rows)]
        self.void = [[False] * self.cols for _ in range(self.rows)]
        self.goal = [[False] * self.cols for _ in range(self.rows)]
        self.box = [[False] * self.cols for _ in range(self.rows)]
        self.pr = self.pc = 0
        self.steps = 0
        self.pushes = 0
        self.undone = 0
        self.rejected = 0
        self.undo = []
        self.patrol = 0
        for r, line in enumerate(raw):
            for c in range(self.cols):
                ch = line[c] if c < len(line) else " "
                if ch == "#":
                    self.wall[r][c] = True
                elif ch == "%":
                    self.void[r][c] = True
                elif ch == ".":
                    self.goal[r][c] = True
                elif ch == "$":
                    self.box[r][c] = True
                elif ch == "*":
                    self.box[r][c] = True
                    self.goal[r][c] = True
                elif ch == "@":
                    self.pr, self.pc = r, c
                elif ch == "+":
                    self.pr, self.pc = r, c
                    self.goal[r][c] = True

    # --- derived facts ---------------------------------------------------------
    def blocked(self, r, c):
        if not (0 <= r < self.rows and 0 <= c < self.cols):
            return True
        return self.wall[r][c] or self.void[r][c]

    def boxes(self):
        out = []
        for r in range(self.rows):
            for c in range(self.cols):
                if self.box[r][c]:
                    out.append((r, c))
        return out

    def goals(self):
        out = []
        for r in range(self.rows):
            for c in range(self.cols):
                if self.goal[r][c]:
                    out.append((r, c))
        return out

    def on_goal(self):
        return len([1 for (r, c) in self.boxes() if self.goal[r][c]])

    def dead_boxes(self):
        dead = []
        for (r, c) in self.boxes():
            if self.goal[r][c]:
                continue
            up, down = self.blocked(r - 1, c), self.blocked(r + 1, c)
            left, right = self.blocked(r, c - 1), self.blocked(r, c + 1)
            if (up and left) or (up and right) or (down and left) or (down and right):
                dead.append((r, c))
                continue
            solid = False
            for dr in (-1, 0):
                for dc in (-1, 0):
                    ok = True
                    for a in (0, 1):
                        for b in (0, 1):
                            rr, cc = r + dr + a, c + dc + b
                            if not (0 <= rr < self.rows and 0 <= cc < self.cols):
                                ok = False
                            elif not (self.wall[rr][cc] or self.box[rr][cc]):
                                ok = False
                    if ok:
                        solid = True
            if solid:
                dead.append((r, c))
        return dead

    def won(self):
        b = self.boxes()
        return len(b) > 0 and self.on_goal() == len(b)

    def deadlocked(self):
        return len(self.dead_boxes()) > 0

    def game_over(self):
        return self.won() or self.deadlocked()

    def cell_code(self, r, c):
        if not (0 <= r < self.rows and 0 <= c < self.cols):
            return 0
        if self.void[r][c]:
            return 0
        if self.wall[r][c]:
            return 2
        isp = (r, c) == (self.pr, self.pc)
        if self.box[r][c] and self.goal[r][c]:
            return 9 if isp else 5
        if self.box[r][c]:
            return 8 if isp else 4
        if self.goal[r][c]:
            return 7 if isp else 3
        return 6 if isp else 1

    def board_hash(self):
        h = 17
        for r in range(self.rows):
            for c in range(self.cols):
                h = (h * 31 + self.cell_code(r, c)) & 0xFFFFFFFF
        return h - 0x100000000 if h >= 0x80000000 else h

    def box_list(self):
        return "|".join("%d,%d" % (r, c) for (r, c) in self.boxes())

    def goal_list(self):
        return "|".join("%d,%d" % (r, c) for (r, c) in self.goals())

    def dead_list(self):
        return "|".join("%d,%d" % (r, c) for (r, c) in self.dead_boxes())

    # --- the move --------------------------------------------------------------
    def move(self, direction):
        if direction not in DIRS:
            self.rejected += 1
            return "bad_dir"
        if self.game_over():
            self.rejected += 1
            return "game_over"
        dr, dc = DIRS[direction]
        nr, nc = self.pr + dr, self.pc + dc
        if self.blocked(nr, nc):
            self.rejected += 1
            return "wall"
        pushed = False
        if self.box[nr][nc]:
            br, bc = nr + dr, nc + dc
            if self.blocked(br, bc) or self.box[br][bc]:
                self.rejected += 1
                return "blocked_box"
            self.box[nr][nc] = False
            self.box[br][bc] = True
            pushed = True
            self.pushes += 1
            self.undo.append(("push", self.pr, self.pc, nr, nc, br, bc))
        else:
            self.undo.append(("walk", self.pr, self.pc, -1, -1, -1, -1))
        self.pr, self.pc = nr, nc
        self.steps += 1
        return "push" if pushed else "walk"

    def undo_one(self):
        if not self.undo:
            self.rejected += 1
            return "nothing"
        kind, was_r, was_c, br, bc, tr, tc = self.undo.pop()
        if kind == "push":
            self.box[tr][tc] = False
            self.box[br][bc] = True
            self.pushes -= 1
        self.pr, self.pc = was_r, was_c
        self.steps -= 1
        self.undone += 1
        return kind

    def auto_step(self, n):
        accepted = 0
        for _ in range(n):
            if self.game_over():
                break
            direction = PATROL[self.patrol % 4]
            self.patrol += 1
            before = self.steps
            self.move(direction)
            if self.steps > before:
                accepted += 1
        return accepted

    def can_move(self):
        if self.game_over():
            return False
        for direction in PATROL:
            dr, dc = DIRS[direction]
            nr, nc = self.pr + dr, self.pc + dc
            if self.blocked(nr, nc):
                continue
            if self.box[nr][nc]:
                br, bc = nr + dr, nc + dc
                if self.blocked(br, bc) or self.box[br][bc]:
                    continue
            return True
        return False


def fresh(spec):
    return Sim(spec)


L0 = Sim(LEVELS[0])
L1 = Sim(LEVELS[1])
L2 = Sim(LEVELS[2])
L3 = Sim(LEVELS[3])
OPEN_SIM = Sim(OPEN)
BLOCKED_SIM = Sim(BLOCKED)
CORNER_SIM = Sim(INTOCORNER)

# --- the scenarios, replayed in the simulator -------------------------------
PUSH_WIN = Sim(LEVELS[0])
PUSH_WIN.move("left")
PUSH_WIN_HASH = PUSH_WIN.board_hash()

L1_MOVES = ["left", "left", "left", "right", "up"]
L1_WIN = Sim(LEVELS[1])
for _m in L1_MOVES:
    L1_WIN.move(_m)
L1_WIN_HASH = L1_WIN.board_hash()
L1_AFTER_UNDO = Sim(LEVELS[1])
for _m in L1_MOVES:
    L1_AFTER_UNDO.move(_m)
L1_AFTER_UNDO.undo_one()
L1_UNDO_HASH = L1_AFTER_UNDO.board_hash()

# the box that one west push wedges into a corner
CORNER_BEFORE = Sim(INTOCORNER)
CORNER_BEFORE.move("up")
CORNER_AFTER = Sim(INTOCORNER)
CORNER_AFTER.move("up")
CORNER_AFTER.move("left")
CORNER_AFTER_HASH = CORNER_AFTER.board_hash()

# a push whose target is a wall
BLOCKED_RUN = Sim(BLOCKED)
BLOCKED_RUN.move("left")
BLOCKED_RUN.move("up")

# the patrol, two calls on the open field.
# NOTE (S-1, found by this game's own r1 run): the facts asserted after the FIRST
# AutoStep call must be the state after the FIRST call.  r1 asserted the simulator's
# post-two-calls values at that point and two assertions failed (Steps 5 vs 2,
# PlayerCol 3 vs 4).  The C# was right; the session was reading the wrong moment.
# Hence the explicit snapshots.
AUTO2 = Sim(OPEN)
AUTO2_ACCEPT2 = AUTO2.auto_step(2)
AUTO2_STEPS2 = AUTO2.steps
AUTO2_PR2 = AUTO2.pr
AUTO2_PC2 = AUTO2.pc
AUTO2_ACCEPT3 = AUTO2.auto_step(3)

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


def moves(tag_prefix, sim, directions, note):
    """One hook call per move, then the facts the simulator says must hold."""
    for i, direction in enumerate(directions):
        hook("%s%02d-%s" % (tag_prefix, i + 1, direction), 'Move("%s")' % direction,
             "move %d of %d: %s" % (i + 1, len(directions), note))
    return sim


# =============================================================================
# editor phase (14 calls)
# =============================================================================
e("e01-edit-game", "project_edit_script",
  {"path": "res://src/SokobanGame.cs", "content_file": "payload/SokobanGame.cs"},
  "the whole game is written through the MCP script writer (the template stub is replaced)")
e("e02-open-scene", "editor_open_scene", {"path": "res://scenes/main.tscn"},
  "the template scene carries the root Main (Node2D) the script is attached to")
e("e03-batch-add-static", "editor_add_nodes_batch", {"nodes": STATIC_BATCH},
  "the three static nodes of the scene, through the batch tool: a background and two labels; "
  "every board cell is created at run time")
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
e("e10-action-up", "editor_add_input_action", {"action": "soko_up", "key": "W"}, "walk up")
e("e11-action-right", "editor_add_input_action", {"action": "soko_right", "key": "D"}, "walk right")
e("e12-build-csharp", "project_build_csharp",
  {"configuration": "Debug", "timeout_ms": 300000, "rescan": True},
  "compile the game the MCP script writer just wrote")
e("e13-validate-scripts", "project_validate_scripts", {}, "the engine's own per-file verdict")
e("e14-errors", "editor_get_errors", {}, "the editor log's ERROR lines after the build")

# =============================================================================
# game phase
# =============================================================================
g("g01-scene-tree", "running_game_get_scene_tree", {},
  "the running tree: the three static nodes plus the board cells created at run time")
hook("g02-readback-t0", "Dump()", "the whole board as one line plus every fact")
assert_state("g03-assert-cols", "Cols", "eq", L0.cols, "level 1 is seven columns wide")
assert_state("g04-assert-rows", "Rows", "eq", L0.rows, "and five rows tall")
assert_state("g05-assert-level", "LevelIndex", "eq", 0, "the default level is the intro board")
assert_state("g06-assert-goals", "GoalsTotal", "eq", len(L0.goals()), "one goal")
assert_state("g07-assert-boxes", "BoxesTotal", "eq", len(L0.boxes()), "one box")
assert_state("g08-assert-on-goal", "BoxesOnGoal", "eq", L0.on_goal(), "it does not start on the goal")
assert_state("g09-assert-box-list", "BoxList", "eq", L0.box_list(),
             "the box is exactly where the Python re-implementation says it is")
assert_state("g10-assert-goal-list", "GoalList", "eq", L0.goal_list(), "and so is the goal")
assert_state("g11-assert-hash", "BoardHash", "eq", L0.board_hash(),
             "the board hash is the one the Python re-implementation computes from the same rule")
assert_state("g12-assert-player-row", "PlayerRow", "eq", L0.pr, "the player starts in this row")
assert_state("g13-assert-player-col", "PlayerCol", "eq", L0.pc, "and this column")
assert_state("g14-assert-steps-0", "Steps", "eq", 0, "no move yet")
assert_state("g15-assert-pushes-0", "Pushes", "eq", 0, "no push yet")
assert_state("g16-assert-undo-0", "UndoDepth", "eq", 0, "the undo stack is empty")
assert_state("g17-assert-not-dead", "Deadlocked", "eq", False, "the board is alive")
assert_state("g18-assert-not-won", "Won", "eq", False, "and unwon")
assert_state("g19-assert-not-over", "GameOver", "eq", False, "the level is running")
assert_state("g20-assert-can-move", "CanMoveAny", "eq", True, "and a legal move exists")
probe("g21-probe-wall", 0, 0, "the top-left cell is a wall")
assert_state("g22-assert-probe-wall", "ProbeState", "eq", "wall", "it reads as a wall")
probe("g23-probe-floor", 1, 1, "an interior cell is ordinary floor")
assert_state("g24-assert-probe-floor", "ProbeState", "eq", "floor", "it reads as floor")
probe("g25-probe-goal", 2, 2, "the goal cell under the box's destination")
assert_state("g26-assert-probe-goal", "ProbeState", "eq", "goal", "it reads as a goal")
probe("g27-probe-box", 2, 3, "the box")
assert_state("g28-assert-probe-box", "ProbeState", "eq", "box", "it reads as a box")
probe("g29-probe-player", 2, 4, "the player")
assert_state("g30-assert-probe-player", "ProbeState", "eq", "player", "it reads as the player")
probe("g31-probe-void", 99, 99, "a cell outside the grid")
assert_state("g32-assert-probe-void", "ProbeState", "eq", "void", "it reads as the void")
shot("g33-shot-t0", "soko-t0", "the first frame: the intro board with the box and the goal")
samples("g34-samples-frozen", ["BoardHash", "BoxesOnGoal", "Steps", "Elapsed", "Ticks"], 12,
        "determinism baseline: with AutoPush 0 the board does not change while the clock runs "
        "(hash / boxes-on-goal / steps constant, Elapsed and Ticks both increasing)")
assert_state("g35-assert-last-auto-0", "LastAutoSteps", "eq", 0,
             "the clock's per-frame delta is zero while the clock is off")
# --- the one push that finishes the intro board --------------------------------
hook("g36-push-left", 'Move("left")',
     "the player walks left and pushes the box onto the goal -- one accepted move")
assert_state("g37-assert-steps-1", "Steps", "eq", PUSH_WIN.steps, "one accepted move")
assert_state("g38-assert-pushes-1", "Pushes", "eq", PUSH_WIN.pushes, "and it was a push")
assert_state("g39-assert-on-goal-1", "BoxesOnGoal", "eq", PUSH_WIN.on_goal(),
             "the box is on the goal now")
assert_state("g40-assert-off-goal-0", "BoxesOffGoal", "eq", 0, "none is off a goal")
assert_state("g41-assert-won", "Won", "eq", True, "that is the win")
assert_state("g42-assert-over", "GameOver", "eq", True, "and the level is over")
assert_state("g43-assert-not-dead", "Deadlocked", "eq", False, "won, not deadlocked")
assert_state("g44-assert-player-moved", "PlayerRow", "eq", PUSH_WIN.pr, "the player took the cell")
assert_state("g45-assert-player-col", "PlayerCol", "eq", PUSH_WIN.pc, "the box left behind")
assert_state("g46-assert-box-list", "BoxList", "eq", PUSH_WIN.box_list(),
             "the box is where the Python re-implementation says the push put it")
assert_state("g47-assert-hash", "BoardHash", "eq", PUSH_WIN_HASH,
             "and the board hash matches the re-implementation")
assert_state("g48-assert-last-dir", "LastDir", "eq", "left", "the last accepted direction")
assert_state("g49-assert-last-push", "LastPush", "eq", True, "the last accepted move was a push")
assert_state("g50-assert-undo-depth", "UndoDepth", "eq", 1, "one move is on the undo stack")
assert_state("g51-assert-cannot-move", "CanMoveAny", "eq", False, "a finished level offers no move")
hook("g52-move-after-win", 'Move("left")', "every move after the win is refused")
assert_state("g53-assert-rejected-1", "RejectedMoves", "eq", 1, "the refusal is counted")
assert_state("g54-assert-still-1", "Steps", "eq", 1, "and nothing was accepted")
assert_state("g55-assert-reason-over", "LastEvent", "contains", "reason=game_over",
             "the refusal names the rule")
# --- undo rolls the player AND the box back together ---------------------------
hook("g56-undo", "Undo()", "take the winning push back")
assert_state("g57-assert-undo-1", "Undone", "eq", 1, "one undo accepted")
assert_state("g58-assert-steps-0", "Steps", "eq", 0, "the move counter went back")
assert_state("g59-assert-pushes-0", "Pushes", "eq", 0, "and so did the push counter")
assert_state("g60-assert-on-goal-0", "BoxesOnGoal", "eq", 0, "the box is off the goal again")
assert_state("g61-assert-won-0", "Won", "eq", False, "the level is un-won")
assert_state("g62-assert-over-0", "GameOver", "eq", False, "and running")
assert_state("g63-assert-player-back", "PlayerCol", "eq", L0.pc, "the player is back where it was")
assert_state("g64-assert-box-back", "BoxList", "eq", L0.box_list(), "and so is the box")
assert_state("g65-assert-hash-back", "BoardHash", "eq", L0.board_hash(),
             "the board hash is bit-for-bit the starting one again")
hook("g66-undo-empty", "Undo()", "undo with an empty stack is refused")
assert_state("g67-assert-rejected-2", "RejectedMoves", "eq", 2, "the refusal is counted")
assert_state("g68-assert-reason-undo", "LastEvent", "contains", "reason=nothing_to_undo",
             "the refusal names the rule")
shot("g69-shot-t1", "soko-t1", "the board back in its starting shape")
# --- level 2: two boxes, two goals, three pushes and one undo ------------------
force("g70-level2", "level=1", "pin the corridor board")
assert_state("g71-assert-cols", "Cols", "eq", L1.cols, "seven columns")
assert_state("g72-assert-rows", "Rows", "eq", L1.rows, "six rows")
assert_state("g73-assert-goals-2", "GoalsTotal", "eq", 2, "two goals")
assert_state("g74-assert-boxes-2", "BoxesTotal", "eq", 2, "two boxes")
assert_state("g75-assert-box-list", "BoxList", "eq", L1.box_list(),
             "the two boxes are where the re-implementation says")
assert_state("g76-assert-hash", "BoardHash", "eq", L1.board_hash(), "and the hash matches")
assert_state("g77-assert-player", "PlayerRow", "eq", L1.pr, "the player's row")
assert_state("g78-assert-player-col", "PlayerCol", "eq", L1.pc, "and column")
hook("g79-left-1", 'Move("left")', "step 1: plain walk")
hook("g80-left-2", 'Move("left")', "step 2: push the first box west")
hook("g81-left-3", 'Move("left")', "step 3: push the same box onto its goal")
assert_state("g82-assert-on-goal-1", "BoxesOnGoal", "eq", 1, "one of the two is home")
hook("g83-right-1", 'Move("right")', "step 4: step around to the other box")
hook("g84-up-1", 'Move("up")', "step 5: push the second box north onto its goal")
assert_state("g85-assert-on-goal-2", "BoxesOnGoal", "eq", L1_WIN.on_goal(), "both are home")
assert_state("g86-assert-steps-5", "Steps", "eq", L1_WIN.steps, "five accepted moves")
assert_state("g87-assert-pushes-3", "Pushes", "eq", L1_WIN.pushes, "three of them pushed")
assert_state("g88-assert-won", "Won", "eq", True, "the level is cleared")
assert_state("g89-assert-box-list", "BoxList", "eq", L1_WIN.box_list(),
             "both boxes are exactly where the re-implementation put them")
assert_state("g90-assert-hash", "BoardHash", "eq", L1_WIN_HASH, "and the hash matches")
assert_state("g91-assert-player", "PlayerRow", "eq", L1_WIN.pr, "the player's final row")
assert_state("g92-assert-player-col", "PlayerCol", "eq", L1_WIN.pc, "and column")
hook("g93-undo", "Undo()", "undo the winning push")
assert_state("g94-assert-pushes-2", "Pushes", "eq", L1_AFTER_UNDO.pushes, "the push went back")
assert_state("g95-assert-steps-4", "Steps", "eq", L1_AFTER_UNDO.steps, "and so did the step")
assert_state("g96-assert-not-won", "Won", "eq", False, "the level is un-won")
assert_state("g97-assert-box-list", "BoxList", "eq", L1_AFTER_UNDO.box_list(),
             "the undone box is back under the goal")
assert_state("g98-assert-hash", "BoardHash", "eq", L1_UNDO_HASH,
             "and the hash is the re-implementation's undone one")
hook("g99-up-again", 'Move("up")', "push it home again")
assert_state("g100-assert-won", "Won", "eq", True, "the level is cleared again")
assert_state("g101-assert-hash", "BoardHash", "eq", L1_WIN_HASH,
             "and the board is bit-for-bit the same winning one")
shot("g102-shot-t2", "soko-t2", "the cleared corridor board")
g("g103-assert-screen-win", "running_game_assert_screen_text", {"text": "LEVEL CLEARED"},
  "the status label really is on the captured screen")
# --- a push whose target is a wall is refused with no board change -------------
force("g104-blocked-setup", "level=" + BLOCKED, "a box under the top wall, an open board")
assert_state("g105-assert-box-list", "BoxList", "eq", BLOCKED_SIM.box_list(), "the box's cell")
assert_state("g105b-assert-not-dead", "Deadlocked", "eq", False, "the board is alive to begin with")
hook("g106-left-1", 'Move("left")', "walk under the box's column")
hook("g107-up-blocked", 'Move("up")', "push the box north -- into the wall")
assert_state("g109-assert-rejected-1", "RejectedMoves", "eq", BLOCKED_RUN.rejected,
             "the impossible push is refused")
assert_state("g110-assert-steps-2", "Steps", "eq", BLOCKED_RUN.steps, "and nothing was accepted")
assert_state("g111-assert-pushes-0", "Pushes", "eq", 0, "no push happened")
assert_state("g112-assert-box-put", "BoxList", "eq", BLOCKED_RUN.box_list(),
             "the box did not move a cell")
assert_state("g113-assert-player-put", "PlayerRow", "eq", BLOCKED_RUN.pr, "the player did not move")
assert_state("g114-assert-player-col", "PlayerCol", "eq", BLOCKED_RUN.pc, "in either axis")
assert_state("g115-assert-hash", "BoardHash", "eq", BLOCKED_RUN.board_hash(),
             "the board hash is unchanged by the refusal")
assert_state("g116-assert-reason", "LastEvent", "contains", "reason=blocked_box",
             "the refusal names the rule")
hook("g117-bad-dir", 'Move("north")', "a direction that is not one of the four")
assert_state("g118-assert-bad-dir", "LastEvent", "contains", "reason=bad_dir",
             "it is refused by name")
assert_state("g119-assert-rejected-2", "RejectedMoves", "eq", BLOCKED_RUN.rejected + 1,
             "and counted")
# --- one push wedges a box into a corner: the simple deadlock rule -------------
force("g120-corner-before", "level=" + INTOCORNER, "a box with a wall above and to its left")
assert_state("g121-assert-not-dead", "Deadlocked", "eq", False, "it is not stuck yet")
assert_state("g122-assert-dead-zero", "DeadlockCount", "eq", 0, "no dead box")
hook("g123-up", 'Move("up")', "move under the box")
hook("g124-push-into-corner", 'Move("left")', "push it west, into the corner")
assert_state("g125-assert-dead", "Deadlocked", "eq", CORNER_AFTER.deadlocked(),
             "the simple corner rule fires on the push")
assert_state("g126-assert-dead-count", "DeadlockCount", "eq", len(CORNER_AFTER.dead_boxes()),
             "exactly one box is dead")
assert_state("g127-assert-dead-list", "DeadlockList", "eq", CORNER_AFTER.dead_list(),
             "and it is the cell the re-implementation names")
assert_state("g128-assert-not-won", "Won", "eq", False, "a deadlock is not a win")
assert_state("g129-assert-over", "GameOver", "eq", True, "but it does end the level")
assert_state("g130-assert-cannot", "CanMoveAny", "eq", False, "a dead board offers no move")
assert_state("g131-assert-hash", "BoardHash", "eq", CORNER_AFTER_HASH,
             "the dead board's hash matches the re-implementation")
assert_state("g132-assert-pushes", "Pushes", "eq", CORNER_AFTER.pushes, "one push")
shot("g133-shot-t3", "soko-t3", "the deadlocked board: one box wedged in the corner")
g("g134-assert-screen-dead", "running_game_assert_screen_text", {"text": "STUCK - DEADLOCK"},
  "the status label really is on the captured screen")
# --- a level pinned with its box already dead ---------------------------------
force("g135-level4", "level=3", "the same board, pinned with the box already in the corner")
assert_state("g136-assert-dead", "Deadlocked", "eq", True, "the corner rule fires immediately")
assert_state("g137-assert-dead-list", "DeadlockList", "eq", L3.dead_list(), "on the pinned cell")
assert_state("g138-assert-over", "GameOver", "eq", True, "the pinned level is already lost")
assert_state("g139-assert-steps-0", "Steps", "eq", 0, "with no move on the record")
# --- the frame-rate independent increment: one hook call, one exact delta ------
force("g140-auto-setup", "level=" + OPEN, "an open field with nothing to push")
hook("g141-autostep-2", "AutoStep(2)", "exactly two deterministic patrol steps")
assert_state("g142-assert-last-hook", "LastHookSteps", "eq", AUTO2_ACCEPT2,
             "the DELTA of that call is exact -- this is the frame-rate independent quantity")
assert_state("g143-assert-last-auto-0", "LastAutoSteps", "eq", 0,
             "and it is a DIFFERENT property from the clock's own per-frame delta, which is 0 "
             "while the clock is off")
assert_state("g144-assert-auto-total", "AutoSteps", "eq", AUTO2_ACCEPT2, "the total agrees")
assert_state("g145-assert-steps", "Steps", "eq", AUTO2_STEPS2,
             "the move counter after exactly the two steps the first call asked for")
assert_state("g146-assert-player", "PlayerCol", "eq", AUTO2_PC2,
             "the patrol landed the player where the re-implementation says")
assert_state("g147-assert-player-row", "PlayerRow", "eq", AUTO2_PR2, "in both axes")
hook("g148-autostep-3", "AutoStep(3)", "three more patrol steps")
assert_state("g149-assert-last-hook-3", "LastHookSteps", "eq", AUTO2_ACCEPT3,
             "the second call's own delta")
assert_state("g150-assert-steps-5", "Steps", "eq", AUTO2.steps, "the move counter after five")
assert_state("g151-assert-not-over", "GameOver", "eq", False, "an empty field can never be won")
assert_state("g152-assert-rejected-0", "RejectedMoves", "eq", 0, "no refusal in between")
# --- multi-frame sample of the auto-push CLOCK: the player really moves --------
# NOTE: this block deliberately does NOT call ForceTestState again. Minesweeper's r1 run
# (TASK-100, defect M1) did, and its closing assertion then read 0: ForceTestState pins the
# WHOLE state, so it zeroes the hook's delta as well. One pinned board spans the hook, the
# clock and both deltas, which is what makes "the clock does not write the hook's property"
# a fact rather than an assumption.
hook("g153-autopush-on", "SetAutoPush(90.0)",
     "the one sample that watches the board move asks for motion explicitly")
assert_state("g154-assert-hook-intact", "LastHookSteps", "eq", AUTO2_ACCEPT3,
             "the clock has been running for several frames and the hook's own delta is still "
             "exactly what the hook wrote -- two producers, two properties")
samples("g155-samples-autopush",
        ["Steps", "PlayerRow", "PlayerCol", "AutoSteps", "LastAutoSteps", "Elapsed", "Ticks"], 30,
        "multi-frame property sample of the auto-push clock: the step counter and the player's "
        "cell change frame by frame while Elapsed and Ticks advance -- 'the player moves' as a "
        "sequence of values, not as an adjective")
assert_state("g156-assert-steps-grew", "Steps", "gt", AUTO2.steps,
             "the clock made moves past the five the hooks made")
assert_state("g157-assert-auto-grew", "AutoSteps", "gt", AUTO2_ACCEPT2 + AUTO2_ACCEPT3,
             "and the clock's own total grew")
hook("g158-autopush-off", "SetAutoPush(0.0)", "back to frozen")
assert_state("g159-assert-last-auto-0", "LastAutoSteps", "eq", 0, "the per-frame delta is zero again")
assert_state("g160-assert-hook-intact", "LastHookSteps", "eq", AUTO2_ACCEPT3,
             "while the hook's own delta is untouched by the clock, before or after it runs")
shot("g161-shot-t4", "soko-t4", "the open field after the clock walked the player around")
# --- the declared input path really drives the game ----------------------------
force("g162-input-setup", "level=" + OPEN, "a clean open field for the input test")
assert_state("g163-assert-hook-zeroed", "LastHookSteps", "eq", 0,
             "ForceTestState pins the WHOLE state, so it zeroes the hook's delta too -- the M1 "
             "lesson stated as an assertion instead of an assumption")
hook("g164-poll-on", "SetPollInput(true)",
     "the input path is off by default; the test switches it on explicitly")
g("g165-input-right", "running_game_run_test_scenario",
  {"steps": [{"type": "input", "action": "soko_right", "pressed": True},
             {"type": "wait", "seconds": 0.45},
             {"type": "assert", "node_path": "Main", "property": "PlayerCol",
              "operator": "gt", "expected": OPEN_SIM.pc}]},
  "the declared action really walks the player one cell right")
assert_state("g166-assert-input-moves-1", "InputMoves", "eq", 1,
             "the declared action fires on the PRESS EDGE, so a scenario's never-released key "
             "performs exactly one move instead of repeating at the frame rate")
assert_state("g167-assert-player-moved", "PlayerCol", "eq", OPEN_SIM.pc + 1,
             "the player is exactly one cell right of where it started")
hook("g168-poll-off", "SetPollInput(false)",
     "polling off again: nothing after this can drift because a key is still marked held")
# --- positive control: a node created at run time is drawn ----------------------
g("g169-runtime-overlay", "running_game_execute_gdscript",
  code('var main = get_parent()\nvar c = ColorRect.new()\nc.name = StringName("ProbeOverlay")\n'
       'c.position = Vector2(20, 552)\nc.size = Vector2(120, 34)\n'
       'c.color = Color(0.95, 0.35, 0.95, 1.0)\nmain.add_child(c)\nreturn "overlay added"'),
  "a node created at run time, in the same session, as the positive control for 'a run-time node "
  "is drawn'")
# --- DECLARED FAILURE: the error path of the assertion tool ---------------------
g("g170-assert-unknown-property", "running_game_assert_node_state",
  {"node_path": "Main", "property": "NoSuchProperty", "operator": "eq", "expected": 1},
  "DECLARED FAILURE: a boundary call asking for a property that does not exist (-32001), so the "
  "error path of the assertion tool is on the record too")
shot("g171-shot-t5", "soko-t5", "the overlay is visible in this frame and not in t4")
force("g172-final-level", "level=0", "ask for the intro board by index once more")
assert_state("g173-assert-boxes", "BoxesTotal", "eq", L0.boxes().__len__(),
             "the intro board is back")
assert_state("g174-assert-hash", "BoardHash", "eq", L0.board_hash(),
             "and it reproduces the very same hash the Python re-implementation predicted")
hook("g175-final-readback", "Dump()", "the final board as one line")
g("g176-final-tree", "running_game_get_scene_tree", {},
  "the final tree, including the run-time overlay")

doc = {"import": True, "calls": calls}
os.makedirs(os.path.dirname(OUT), exist_ok=True)
with io.open(OUT, "w", encoding="utf-8", newline="\n") as handle:
    handle.write(json.dumps(doc, ensure_ascii=False, indent=1) + "\n")

print("wrote %s calls=%d" % (OUT, len(calls)))
print("L0 hash=%d box_list=%s goal_list=%s" % (L0.board_hash(), L0.box_list(), L0.goal_list()))
print("PUSH_WIN hash=%d box_list=%s player=%d,%d pushes=%d" % (
    PUSH_WIN_HASH, PUSH_WIN.box_list(), PUSH_WIN.pr, PUSH_WIN.pc, PUSH_WIN.pushes))
print("L1 hash=%d box_list=%s player=%d,%d" % (L1.board_hash(), L1.box_list(), L1.pr, L1.pc))
print("L1_WIN hash=%d box_list=%s steps=%d pushes=%d" % (
    L1_WIN_HASH, L1_WIN.box_list(), L1_WIN.steps, L1_WIN.pushes))
print("CORNER_AFTER hash=%d dead=%s pushes=%d player=%d,%d" % (
    CORNER_AFTER_HASH, CORNER_AFTER.dead_list(), CORNER_AFTER.pushes,
    CORNER_AFTER.pr, CORNER_AFTER.pc))
print("BLOCKED rejected=%d steps=%d player=%d,%d hash=%d" % (
    BLOCKED_RUN.rejected, BLOCKED_RUN.steps, BLOCKED_RUN.pr, BLOCKED_RUN.pc,
    BLOCKED_RUN.board_hash()))
print("AUTO2 accepted2=%d accepted3=%d steps=%d player=%d,%d" % (
    AUTO2_ACCEPT2, AUTO2_ACCEPT3, AUTO2.steps, AUTO2.pr, AUTO2.pc))
