# -*- coding: utf-8 -*-
"""TASK-101: build the Bomberman session (editor + game phases).

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

THE INDEPENDENT RECOMPUTATION.  ``BSim`` below is a second implementation of the
payload's own rules -- level parsing, the player's legality test, the blast
spread with its wall/brick stops, the chain reaction, the enemy chase policy,
the brick and grid hashes -- written from the rules rather than translated from
the C#.  Every blast literal this generator bakes into the session is the one
``BSim`` produced, so a blast the C# gets wrong shows up as a FAILED assertion.
"""
import io
import json
import os

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", ".."))
SESSION_DIR = os.path.join(ROOT, "tools", "sessions", "bomberman")
OUT = os.path.join(SESSION_DIR, "session.json")

BG = {"type": "ColorRect", "name": "Background", "parent_path": ".",
      "properties": {"offset_left": 0, "offset_top": 0, "offset_right": 800,
                     "offset_bottom": 600, "color": {"r": 0.05, "g": 0.06, "b": 0.09, "a": 1}}}
HUD = {"type": "Label", "name": "Hud", "parent_path": ".",
       "properties": {"offset_left": 14, "offset_top": 8, "offset_right": 600,
                      "offset_bottom": 42, "text": "BRICKS 10/10  ENEMIES 2/2  LIVES 3  SCORE 0  BOMBS 0",
                      "theme_override_font_sizes/font_size": 22}}
STATUS = {"type": "Label", "name": "Status", "parent_path": ".",
          "properties": {"offset_left": 600, "offset_top": 8, "offset_right": 795,
                         "offset_bottom": 42, "text": "BOMB THE BRICKS",
                         "theme_override_font_sizes/font_size": 22}}
STATIC_BATCH = [BG, HUD, STATUS]

LEVEL0 = ("#############/#@..........#/#.#.#.#.#.#.#/#.B.B.B.B.B.#/#...........#"
          "/#.B.B.B.B.B.#/#.#.#.#.#.#.#/#E.........E#/#############")
LEVEL1 = ("#############/#@..........#/#...........#/#.....B.....#/#...........#"
          "/#...........#/#.....E.....#/#...........#/#############")
# an open field for the deterministic hooks: three bricks, and the bomb's cell is
# FLOOR.  r1/r2 pinned the bomb on a brick cell -- a state the game can never reach
# (PlaceBomb only fires on the player's own cell and the player can never stand on a
# brick) -- and the blast then destroyed the bomb's own brick as well, clearing the
# board and deciding the level before the sample even started, so the "the bomb goes
# off" sample watched a frozen board.  This board keeps the bomb on floor, leaves one
# brick out of the blast, and therefore cannot be won by the clock (defect B-3).
BIG = ("############/#..........#/#..........#/#...B......#/#..........#"
       "/#...B......#/#....B.....#/############")
# one bomb in a corridor of bricks: the first brick each way takes the hit
# and stops the spread, and the walls stop it in the other two directions.
CORRIDOR = "##########/#@.......#/#........#/##########"
# two bombs two cells apart: setting off the first one sets off the second
CHAIN = "########/#@.....#/#......#/#......#/########"
# the player and one enemy, one brick elsewhere so the board cannot be won
CONTACT = "########/#@.E...#/#......B#/########"

DIRS = {"up": (-1, 0), "down": (1, 0), "left": (0, -1), "right": (0, 1)}


class BSim(object):
    """A second implementation of Bomberman's rules, written from the spec."""

    def __init__(self, spec, player=None, bricks=None, enemies=None, bombs=None,
                 lives=3, blast_range=2, fuse=3, max_bombs=3):
        self.spec = spec
        raw = spec.split("/")
        self.rows = len(raw)
        self.cols = max(len(line) for line in raw)
        self.range = blast_range
        self.fuse_len = fuse
        self.max_bombs = max_bombs
        self.wall = [[False] * self.cols for _ in range(self.rows)]
        self.brick = [[False] * self.cols for _ in range(self.rows)]
        self.pr = self.pc = 0
        self.spawn = (0, 0)
        enemies_from_level = []
        for r, line in enumerate(raw):
            for c in range(self.cols):
                ch = line[c] if c < len(line) else "#"
                if ch == "#":
                    self.wall[r][c] = True
                elif ch == "B":
                    self.brick[r][c] = True
                elif ch == "@":
                    self.pr, self.pc = r, c
                    self.spawn = (r, c)
                elif ch == "E":
                    enemies_from_level.append((r, c))
        self.bricks_total = sum(1 for r in range(self.rows) for c in range(self.cols)
                                if self.brick[r][c])
        self.enemies = list(enemies_from_level)
        if bricks is not None:
            for r in range(self.rows):
                for c in range(self.cols):
                    self.brick[r][c] = False
            for (r, c) in bricks:
                self.brick[r][c] = True
            self.bricks_total = len(bricks)
        if enemies is not None:
            self.enemies = list(enemies)
        self.bombs = list(bombs or [])
        if player is not None:
            self.pr, self.pc = player
        self.bricks_total = sum(1 for r in range(self.rows) for c in range(self.cols)
                                if self.brick[r][c])
        self.bricks_remaining = self.bricks_total
        self.bricks_destroyed = 0
        self.bombs_placed = len(self.bombs)
        self.enemies_total = len(self.enemies)
        self.enemies_killed = 0
        self.lives = lives
        self.deaths = 0
        self.moves = 0
        self.rejected = 0
        self.exploded = False
        self.dead_by_enemy = False
        self.last_blast = []
        self.detonations = 0
        self.last_bomb = (-1, -1)

    # --- derived facts ---------------------------------------------------------
    def is_wall(self, r, c):
        return not (0 <= r < self.rows and 0 <= c < self.cols) or self.wall[r][c]

    def is_brick(self, r, c):
        return 0 <= r < self.rows and 0 <= c < self.cols and self.brick[r][c]

    def bomb_at(self, r, c):
        for i, (br, bc, _f) in enumerate(self.bombs):
            if (br, bc) == (r, c):
                return i
        return -1

    def enemy_at(self, r, c):
        for i, (er, ec) in enumerate(self.enemies):
            if (er, ec) == (r, c):
                return i
        return -1

    def grid_hash(self):
        h = 17
        for r in range(self.rows):
            for c in range(self.cols):
                code = 1 if self.wall[r][c] else (3 if self.brick[r][c] else 2)
                h = (h * 31 + code) & 0xFFFFFFFF
        return h - 0x100000000 if h >= 0x80000000 else h

    def unit_hash(self):
        h = 17
        for r in range(self.rows):
            for c in range(self.cols):
                v = 0
                if self.bomb_at(r, c) >= 0:
                    v += 5
                if self.enemy_at(r, c) >= 0:
                    v += 11
                if (r, c) == (self.pr, self.pc):
                    v += 23
                h = (h * 31 + v) & 0xFFFFFFFF
        return h - 0x100000000 if h >= 0x80000000 else h

    def bomb_list(self):
        return "|".join("%d,%d,%d" % (r, c, f) for (r, c, f) in self.bombs)

    def enemy_list(self):
        return "|".join("%d,%d" % (r, c) for (r, c) in self.enemies)

    def brick_list(self):
        return "|".join("%d,%d" % (r, c)
                        for r in range(self.rows) for c in range(self.cols) if self.brick[r][c])

    def blast_list(self):
        return "|".join("%d,%d" % (r, c) for (r, c) in self.last_blast)

    def won(self):
        return self.bricks_remaining == 0 and len(self.enemies) == 0

    def game_over(self):
        return self.won() or self.lives <= 0

    # --- the blast -------------------------------------------------------------
    def blast_cells(self, row, col):
        cells = [(row, col)]
        for dr, dc in ((-1, 0), (1, 0), (0, -1), (0, 1)):
            for step in range(1, self.range + 1):
                r, c = row + dr * step, col + dc * step
                if self.is_wall(r, c):
                    break
                cells.append((r, c))
                if self.is_brick(r, c):
                    break
        return cells

    def detonate(self, seeds):
        """seeds is a list of indices into self.bombs (ascending)."""
        queue = [(self.bombs[i][0], self.bombs[i][1]) for i in seeds]
        self.last_bomb = queue[-1]
        for i in sorted(seeds, reverse=True):
            self.bombs.pop(i)
        seen = []
        seen_set = set()
        head = 0
        while head < len(queue):
            br, bc = queue[head]
            head += 1
            for (r, c) in self.blast_cells(br, bc):
                if (r, c) not in seen_set:
                    seen_set.add((r, c))
                    seen.append((r, c))
                other = self.bomb_at(r, c)
                if other >= 0:
                    queue.append((self.bombs[other][0], self.bombs[other][1]))
                    self.bombs.pop(other)
        self.detonations += 1
        self.last_blast = seen
        for (r, c) in seen:
            if self.brick[r][c]:
                self.brick[r][c] = False
        for i in range(len(self.enemies) - 1, -1, -1):
            if self.enemies[i] in seen_set:
                self.enemies.pop(i)
                self.enemies_killed += 1
        if (self.pr, self.pc) in seen_set:
            self.kill_player("blast")
        self.refresh()

    def refresh(self):
        self.bricks_remaining = sum(1 for r in range(self.rows) for c in range(self.cols)
                                    if self.brick[r][c])
        self.bricks_destroyed = self.bricks_total - self.bricks_remaining

    def kill_player(self, reason):
        self.lives -= 1
        self.deaths += 1
        self.exploded = reason == "blast"
        self.dead_by_enemy = reason == "enemy"
        if self.lives > 0:
            self.pr, self.pc = self.spawn

    def step_fuse(self, steps):
        fired = 0
        for _ in range(steps):
            due = []
            for i in range(len(self.bombs)):
                r, c, f = self.bombs[i]
                self.bombs[i] = (r, c, f - 1)
            for i in range(len(self.bombs) - 1, -1, -1):
                if self.bombs[i][2] <= 0:
                    due.insert(0, i)
            if not due:
                continue
            self.detonate(due)
            fired += 1
        self.refresh()
        return fired

    # --- the player ------------------------------------------------------------
    def move(self, direction):
        if direction not in DIRS:
            self.rejected += 1
            return "bad_dir"
        if self.game_over():
            self.rejected += 1
            return "game_over"
        dr, dc = DIRS[direction]
        nr, nc = self.pr + dr, self.pc + dc
        if self.is_wall(nr, nc):
            self.rejected += 1
            return "wall"
        if self.is_brick(nr, nc):
            self.rejected += 1
            return "brick"
        if self.bomb_at(nr, nc) >= 0:
            self.rejected += 1
            return "bomb"
        self.pr, self.pc = nr, nc
        self.moves += 1
        if self.enemy_at(nr, nc) >= 0:
            self.kill_player("enemy")
            return "enemy"
        return "walk"

    def place_bomb(self):
        if self.game_over():
            self.rejected += 1
            return "game_over"
        if self.bomb_at(self.pr, self.pc) >= 0:
            self.rejected += 1
            return "bomb_already_here"
        if len(self.bombs) >= self.max_bombs:
            self.rejected += 1
            return "max_bombs"
        self.bombs.append((self.pr, self.pc, self.fuse_len))
        self.bombs_placed += 1
        self.last_bomb = (self.pr, self.pc)
        return "placed"

    # --- the enemies -----------------------------------------------------------
    def step_enemy(self, index):
        row, col = self.enemies[index]
        dr, dc = self.pr - row, self.pc - col
        sr = 0 if dr == 0 else (1 if dr > 0 else -1)
        sc = 0 if dc == 0 else (1 if dc > 0 else -1)
        vertical_first = abs(dr) >= abs(dc)
        first = (sr, 0) if vertical_first else (0, sc)
        second = (0, sc) if vertical_first else (sr, 0)
        for (mr, mc) in (first, second):
            if mr == 0 and mc == 0:
                continue
            nr, nc = row + mr, col + mc
            if self.is_wall(nr, nc) or self.is_brick(nr, nc):
                continue
            if self.bomb_at(nr, nc) >= 0:
                continue
            if self.enemy_at(nr, nc) >= 0:
                continue
            self.enemies[index] = (nr, nc)
            if (nr, nc) == (self.pr, self.pc):
                self.kill_player("enemy")
            return True
        return False

    def step_enemies(self, steps):
        moved = 0
        for _ in range(steps):
            if self.game_over():
                break
            for i in range(len(self.enemies)):
                if self.step_enemy(i):
                    moved += 1
                if self.game_over():
                    break
        return moved

    def step_tick(self, ticks):
        applied = 0
        for _ in range(ticks):
            if self.game_over():
                break
            self.step_fuse(1)
            applied += 1
            if self.game_over():
                break
            self.step_enemies(1)
        return applied


def spec_of(level, **kwargs):
    """Render a ForceTestState spec the way the session writes it."""
    parts = ["level=" + level]
    for key in ("player", "bricks", "enemies", "bombs", "lives"):
        if key in kwargs and kwargs[key] is not None:
            parts.append("%s=%s" % (key, kwargs[key]))
    return ";".join(parts)


L0 = BSim(LEVEL0)
L1 = BSim(LEVEL1)
BIG_SIM = BSim(BIG)

# --- scenario 1: a bomb at (3,1) on the default board ------------------------
# The mutation order here is EXACTLY the order the session's hooks appear in below.
BOMB1 = BSim(LEVEL0)
BOMB1.move("left")        # refused: the border wall
BOMB1.move("down")        # (2,1)
BOMB1.move("down")        # (3,1)
BOMB1.move("right")       # refused: the brick at (3,2)
BOMB1.move("north")       # refused: not a direction
BOMB1.place_bomb()        # the bomb at (3,1), fuse 3
BOMB1.place_bomb()        # refused: a bomb is already on this cell
BOMB1.move("up")          # (2,1)
BOMB1.move("down")        # refused: a live bomb blocks (3,1)
BOMB1.move("up")          # (1,1)
BOMB1.move("right")       # (1,2) -- clear of the blast
BOMB1.step_fuse(2)
BOMB1.step_fuse(1)
BOMB1_BLAST = BOMB1.blast_list()

# --- scenario 2: the win on level 2 -----------------------------------------
# Again in session order: three downs, five rights, the bomb, three lefts, the fuse.
WIN = BSim(LEVEL1)
for _m in ["down", "down", "down"]:
    WIN.move(_m)
for _m in ["right"] * 5:
    WIN.move(_m)
WIN.place_bomb()
for _m in ["left", "left", "left"]:
    WIN.move(_m)
WIN.step_fuse(3)
WIN_BLAST = WIN.blast_list()

# --- scenario 3: a corridor of bricks stops the spread ----------------------
CORRIDOR_BRICKS = [(1, 1), (1, 4), (2, 4)]
CORRIDOR_SPEC = spec_of(CORRIDOR, player="2,1", bricks="1,1|1,4|2,4", bombs="1,3,1")
CORRIDOR_SIM = BSim(CORRIDOR, player=(2, 1), bricks=CORRIDOR_BRICKS, bombs=[(1, 3, 1)])
CORRIDOR_SIM.step_fuse(1)
CORRIDOR_BLAST = CORRIDOR_SIM.blast_list()

CORRIDOR_KILL_SPEC = spec_of(CORRIDOR, player="1,2", bricks="1,1|1,4|2,4", bombs="1,3,1")
CORRIDOR_KILL = BSim(CORRIDOR, player=(1, 2), bricks=CORRIDOR_BRICKS, bombs=[(1, 3, 1)])
CORRIDOR_KILL.step_fuse(1)

# --- scenario 4: the chain reaction -----------------------------------------
CHAIN_BOMBS = [(1, 1, 1), (1, 2, 3)]
CHAIN_SPEC = spec_of(CHAIN, player="2,4", bombs="1,1,1|1,2,3")
CHAIN_SIM = BSim(CHAIN, player=(2, 4), bombs=CHAIN_BOMBS)
CHAIN_SIM.step_fuse(1)
CHAIN_BLAST = CHAIN_SIM.blast_list()

# --- scenario 5: the enemy chase --------------------------------------------
CHASE_SPEC = spec_of(LEVEL0)
CHASE = BSim(LEVEL0)
CHASE.step_enemies(3)
CHASE_LIST3 = CHASE.enemy_list()
CHASE_HASH3 = CHASE.unit_hash()
CHASE.step_enemies(1)
CHASE_LIST4 = CHASE.enemy_list()

# --- scenario 6: walking into an enemy ---------------------------------------
CONTACT_SPEC = spec_of(CONTACT)
CONTACT_SIM = BSim(CONTACT)
CONTACT_SIM.move("right")
CONTACT_SIM.move("right")
CONTACT_HASH = CONTACT_SIM.unit_hash()

# --- scenario 7: the clock sample -------------------------------------------
# The bomb sits on FLOOR at (4,4): its blast reaches the bricks at (3,4) and (5,4) and
# leaves the one at (6,5) standing, so the level can never be won inside the sample.
#
# THE FUSE IS SIZED FROM THE MEASURED CLOCK RATE.  The accumulator is wall-clock based
# (`_autoAccum += delta * AutoClock`), so a 30-frame sample at 60 ticks/s is about
# `60 * 0.478 s ~= 29` ticks whatever the frame rate is.  A fuse of 24 therefore
# ALWAYS runs out inside the sample (29 > 24) and ALWAYS survives the two or three
# MCP calls that separate SetAutoClock from the first sampled frame (measured at about
# six ticks).  r2's fuse of 8 ran out before the sample began, so the sample watched a
# board that was already decided (defect B-3); r3's fuse of 8 did the same because the
# two assert calls in between burned the remaining ticks.
CLOCK_FUSE = 24
CLOCK_SPEC = spec_of(BIG, player="1,1", bombs="4,4,%d" % CLOCK_FUSE)
CLOCK_SIM = BSim(BIG, player=(1, 1), bombs=[(4, 4, CLOCK_FUSE)])
CLOCK_BLAST = "|".join("%d,%d" % c for c in CLOCK_SIM.blast_cells(4, 4))
CLOCK_BLAST_COUNT = len(CLOCK_SIM.blast_cells(4, 4))
CLOCK_BRICKS_LEFT = CLOCK_SIM.bricks_total - 2

# --- scenario 8: StepTick, the frame-rate independent increment ---------------
TICK_SPEC = spec_of(BIG, player="1,1", bombs="4,4,%d" % CLOCK_FUSE)
TICK_SIM = BSim(BIG, player=(1, 1), bombs=[(4, 4, CLOCK_FUSE)])
TICK_ACCEPT2 = TICK_SIM.step_tick(2)

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


def walk(prefix, sim, directions, note):
    for i, direction in enumerate(directions):
        hook("%s%02d-%s" % (prefix, i + 1, direction), 'Move("%s")' % direction,
             "move %d of %d: %s" % (i + 1, len(directions), note))


# =============================================================================
# editor phase (14 calls)
# =============================================================================
e("e01-edit-game", "project_edit_script",
  {"path": "res://src/BombermanGame.cs", "content_file": "payload/BombermanGame.cs"},
  "the whole game is written through the MCP script writer (the template stub is replaced)")
e("e02-open-scene", "editor_open_scene", {"path": "res://scenes/main.tscn"},
  "the template scene carries the root Main (Node2D) the script is attached to")
e("e03-batch-add-static", "editor_add_nodes_batch", {"nodes": STATIC_BATCH},
  "the three static nodes of the scene, through the batch tool: a background and two labels; "
  "every field cell is created at run time")
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
e("e10-action-up", "editor_add_input_action", {"action": "bomb_up", "key": "W"}, "walk up")
e("e11-action-right", "editor_add_input_action", {"action": "bomb_right", "key": "D"}, "walk right")
e("e12-action-place", "editor_add_input_action", {"action": "bomb_place", "key": "Space"},
  "drop a bomb")
e("e13-build-csharp", "project_build_csharp",
  {"configuration": "Debug", "timeout_ms": 300000, "rescan": True},
  "compile the game the MCP script writer just wrote")
e("e14-validate-scripts", "project_validate_scripts", {}, "the engine's own per-file verdict")

# =============================================================================
# game phase
# =============================================================================
g("g01-scene-tree", "running_game_get_scene_tree", {},
  "the running tree: the three static nodes plus the field cells created at run time")
hook("g02-readback-t0", "Dump()", "the whole field as one line plus every fact")
assert_state("g03-assert-cols", "Cols", "eq", L0.cols, "the classic field is thirteen columns wide")
assert_state("g04-assert-rows", "Rows", "eq", L0.rows, "and nine rows tall")
assert_state("g05-assert-level", "LevelIndex", "eq", 0, "the default level is the classic board")
assert_state("g06-assert-bricks-total", "BricksTotal", "eq", L0.bricks_total,
             "ten destructible bricks")
assert_state("g07-assert-bricks-left", "BricksRemaining", "eq", L0.bricks_remaining,
             "all ten still standing")
assert_state("g08-assert-bricks-destroyed", "BricksDestroyed", "eq", 0, "none destroyed yet")
assert_state("g09-assert-grid-hash", "GridHash", "eq", L0.grid_hash(),
             "the grid hash is the one the Python re-implementation computes from the same rule")
assert_state("g10-assert-unit-hash", "UnitHash", "eq", L0.unit_hash(),
             "and so is the unit hash")
assert_state("g11-assert-spawn-row", "SpawnRow", "eq", L0.spawn[0], "the spawn row from the '@'")
assert_state("g12-assert-spawn-col", "SpawnCol", "eq", L0.spawn[1], "and the spawn column")
assert_state("g13-assert-player", "PlayerRow", "eq", L0.pr, "the player starts here")
assert_state("g14-assert-player-col", "PlayerCol", "eq", L0.pc, "in both axes")
assert_state("g15-assert-enemies-total", "EnemiesTotal", "eq", 2, "two enemies")
assert_state("g16-assert-enemies-alive", "EnemiesAlive", "eq", 2, "both alive")
assert_state("g17-assert-enemy-list", "EnemyList", "eq", L0.enemy_list(),
             "exactly where the re-implementation puts them")
assert_state("g18-assert-lives", "Lives", "eq", 3, "three lives")
assert_state("g19-assert-range", "BlastRange", "eq", 2, "a blast reaches two cells")
assert_state("g20-assert-fuse", "FuseSteps", "eq", 3, "a bomb burns for three ticks")
assert_state("g21-assert-bombs-0", "BombsActive", "eq", 0, "no bomb is live")
assert_state("g22-assert-bombs-placed-0", "BombsPlaced", "eq", 0, "and none was ever placed")
assert_state("g23-assert-not-won", "Won", "eq", False, "the field is not cleared")
assert_state("g24-assert-not-over", "GameOver", "eq", False, "and the game is running")
assert_state("g25-assert-score-0", "Score", "eq", 0, "no points yet")
probe("g26-probe-wall", 0, 0, "the corner cell is a hard wall")
assert_state("g27-assert-probe-wall", "ProbeState", "eq", "wall", "it reads as a wall")
probe("g28-probe-floor", 1, 2, "an open cell")
assert_state("g29-assert-probe-floor", "ProbeState", "eq", "floor", "it reads as floor")
probe("g30-probe-brick", 3, 2, "a destructible brick")
assert_state("g31-assert-probe-brick", "ProbeState", "eq", "brick", "it reads as a brick")
probe("g32-probe-enemy", 7, 1, "an enemy")
assert_state("g33-assert-probe-enemy", "ProbeState", "eq", "enemy", "it reads as an enemy")
probe("g34-probe-player", 1, 1, "the player")
assert_state("g35-assert-probe-player", "ProbeState", "eq", "player", "it reads as the player")
shot("g36-shot-t0", "bomb-t0", "the first frame: the classic field with ten bricks and two enemies")
samples("g37-samples-frozen", ["GridHash", "BricksRemaining", "PlayerRow", "Elapsed", "Ticks"], 12,
        "determinism baseline: with AutoClock 0 the field does not change while the clock runs "
        "(grid hash / bricks / player row constant, Elapsed and Ticks both increasing)")
assert_state("g38-assert-last-auto-0", "LastAutoSteps", "eq", 0,
             "the clock's per-frame delta is zero while the clock is off")
# --- the three refusals --------------------------------------------------------
hook("g39-move-into-wall", 'Move("left")', "walk west, into the border wall")
assert_state("g40-assert-rejected-1", "RejectedMoves", "eq", 1, "the wall refusal is counted")
assert_state("g41-assert-reason-wall", "LastEvent", "contains", "reason=wall",
             "the refusal names the rule")
assert_state("g42-assert-moves-0", "Moves", "eq", 0, "and nothing was accepted")
hook("g43-move-down", 'Move("down")', "walk south")
hook("g44-move-down-2", 'Move("down")', "again")
assert_state("g45-assert-player-row", "PlayerRow", "eq", 3, "the player is level with the bricks")
hook("g46-move-into-brick", 'Move("right")', "walk east, into a brick")
assert_state("g47-assert-rejected-2", "RejectedMoves", "eq", 2, "the brick refusal is counted")
assert_state("g48-assert-reason-brick", "LastEvent", "contains", "reason=brick",
             "the refusal names the rule")
assert_state("g49-assert-still-2", "Moves", "eq", 2, "and the walk counter did not move")
hook("g50-bad-dir", 'Move("north")', "a direction that is not one of the four")
assert_state("g51-assert-bad-dir", "LastEvent", "contains", "reason=bad_dir", "refused by name")
assert_state("g52-assert-rejected-3", "RejectedMoves", "eq", 3, "and counted")
# --- a bomb, its fuse, and the blast the re-implementation predicts ------------
hook("g53-place-bomb", "PlaceBomb()", "drop one bomb on the cell the player is standing on")
assert_state("g54-assert-bombs-1", "BombsActive", "eq", 1, "one live bomb")
assert_state("g55-assert-bomb-list", "BombList", "eq", "3,1,3", "with the fixed three-tick fuse")
assert_state("g56-assert-last-bomb-row", "LastBombRow", "eq", 3, "its row")
assert_state("g57-assert-last-bomb-col", "LastBombCol", "eq", 1, "and its column")
hook("g58-place-again", "PlaceBomb()",
     "a second bomb on the same cell is refused -- this is the 'a live bomb blocks the cell' rule")
assert_state("g59-assert-rejected-4", "RejectedMoves", "eq", 4, "the refusal is counted")
assert_state("g60-assert-reason-bomb", "LastEvent", "contains", "reason=bomb_already_here",
             "refused by name")
hook("g61-move-off-bomb", 'Move("up")', "walk off the bomb's cell")
assert_state("g61b-assert-player", "PlayerRow", "eq", 2, "one cell north of the bomb")
hook("g62-move-onto-bomb", 'Move("down")', "walk back onto the bomb's cell")
assert_state("g62b-assert-reason-bomb-cell", "LastEvent", "contains", "reason=bomb",
             "a live bomb blocks the cell it sits on")
assert_state("g63-assert-rejected-5", "RejectedMoves", "eq", BOMB1.rejected,
             "and that refusal is counted too")
hook("g64-move-up", 'Move("up")', "walk north, away from the bomb")
hook("g64b-move-right", 'Move("right")', "then east: clear of the blast's arm")
assert_state("g64c-assert-player", "PlayerCol", "eq", BOMB1.pc, "the player is clear of the bomb")
assert_state("g64d-assert-player-row", "PlayerRow", "eq", BOMB1.pr, "in both axes")
assert_state("g64e-assert-moves", "Moves", "eq", BOMB1.moves,
             "the accepted-move count is the one the re-implementation reaches")
hook("g65-fuse-2", "StepFuse(2)", "burn two of the three ticks: nothing goes off yet")
assert_state("g66-assert-bombs-1", "BombsActive", "eq", 1, "the bomb is still live")
assert_state("g67-assert-fuse-1", "BombList", "eq", "3,1,1", "with one tick left")
assert_state("g68-assert-detonations-0", "Detonations", "eq", 0, "nothing has gone off")
hook("g69-fuse-last", "StepFuse(1)", "the third tick sets it off")
assert_state("g70-assert-detonations-1", "Detonations", "eq", 1, "one detonation")
assert_state("g71-assert-bombs-0", "BombsActive", "eq", 0, "no bomb is live")
assert_state("g72-assert-blast-count", "LastBlastCount", "eq", len(BOMB1.last_blast),
             "the blast covered exactly the cell count the re-implementation predicts")
assert_state("g73-assert-blast", "LastBlast", "eq", BOMB1_BLAST,
             "and exactly those cells, in exactly that order")
assert_state("g74-assert-bricks-left", "BricksRemaining", "eq", BOMB1.bricks_remaining,
             "one brick took the hit")
assert_state("g75-assert-bricks-destroyed", "BricksDestroyed", "eq", 1, "exactly one")
assert_state("g76-assert-score", "Score", "eq", BOMB1.bricks_destroyed * 10, "ten points a brick")
assert_state("g77-assert-enemies-alive", "EnemiesAlive", "eq", 2, "no enemy was in the blast")
assert_state("g78-assert-lives", "Lives", "eq", 3, "and the player was clear of it")
assert_state("g79-assert-grid-hash", "GridHash", "eq", BOMB1.grid_hash(),
             "the grid hash moved to the re-implementation's post-blast value")
shot("g80-shot-t1", "bomb-t1", "the field after the first blast: one brick is gone")
# --- the wall and the first brick both stop the spread -------------------------
force("g81-corridor", CORRIDOR_SPEC,
      "one bomb in a corridor: a wall above and below, a brick to the left and to the right")
assert_state("g82-assert-bricks", "BricksRemaining", "eq", 3, "three bricks pinned")
assert_state("g83-assert-player", "PlayerRow", "eq", 2, "the player is out of the way")
hook("g84-detonate", "StepFuse(1)", "set it off immediately -- the fuse was pinned at one tick")
assert_state("g85-assert-blast", "LastBlast", "eq", CORRIDOR_BLAST,
             "the blast is the one the re-implementation computes: the wall stops it north and "
             "south, and the FIRST brick each way takes the hit and stops it")
assert_state("g86-assert-blast-count", "LastBlastCount", "eq", len(CORRIDOR_SIM.last_blast),
             "five cells: the bomb, the two south cells, and one brick each way")
assert_state("g87-assert-bricks-left", "BricksRemaining", "eq", 1,
             "two of the three bricks were destroyed")
assert_state("g88-assert-bricks-destroyed", "BricksDestroyed", "eq", 2, "and one survived")
assert_state("g89-assert-lives", "Lives", "eq", 3, "the player was outside the blast")
probe("g90-probe-bomb-cell", 1, 3, "look at the cell the bomb was standing on")
assert_state("g90b-assert-probe-row", "ProbeRow", "eq", 1,
             "the probe records the row it looked at (B-2: r1 asserted a row with no probe before it)")
assert_state("g90c-assert-probe-floor", "ProbeState", "eq", "floor",
             "the bomb's cell is ordinary floor again")
probe("g91-probe-survivor", 2, 4, "look at the brick the blast did not reach")
assert_state("g92-assert-survivor", "ProbeState", "eq", "brick", "it is still standing")
assert_state("g93-assert-hash", "GridHash", "eq", CORRIDOR_SIM.grid_hash(),
             "the grid hash matches the re-implementation")
# --- the blast kills the player when it covers their cell ----------------------
force("g94-blast-on-player", CORRIDOR_KILL_SPEC, "the same corridor, with the player in the blast")
hook("g95-detonate", "StepFuse(1)", "set it off")
assert_state("g96-assert-exploded", "Exploded", "eq", True, "the player was caught by the blast")
assert_state("g97-assert-lives-2", "Lives", "eq", 2, "one life gone")
assert_state("g98-assert-deaths", "Deaths", "eq", 1, "one death on the record")
assert_state("g99-assert-respawn-row", "PlayerRow", "eq", 1, "the player is back at the spawn")
assert_state("g100-assert-respawn-col", "PlayerCol", "eq", 1, "in both axes")
assert_state("g101-assert-not-over", "GameOver", "eq", False, "two lives are left, so the game goes on")
assert_state("g102-assert-not-won", "Won", "eq", False, "and it is not a win")
# --- the chain reaction --------------------------------------------------------
force("g103-chain", CHAIN_SPEC,
      "two bombs two cells apart, the first with one tick left and the second with three")
assert_state("g104-assert-bombs-2", "BombsActive", "eq", 2, "two live bombs")
assert_state("g105-assert-bomb-list", "BombList", "eq", "1,1,1|1,2,3", "with their pinned fuses")
hook("g106-chain-off", "StepFuse(1)", "set the first one off")
assert_state("g107-assert-detonations-1", "Detonations", "eq", 1, "one detonation covers the chain")
assert_state("g108-assert-bombs-0", "BombsActive", "eq", 0, "and the second bomb is gone too")
assert_state("g109-assert-blast", "LastBlast", "eq", CHAIN_BLAST,
             "the union of both blasts, in the order the re-implementation generates it")
assert_state("g110-assert-blast-count", "LastBlastCount", "eq", len(CHAIN_SIM.last_blast),
             "eight cells")
# --- the enemies chase, deterministically --------------------------------------
force("g111-chase", CHASE_SPEC, "the classic field again, with no bomb anywhere")
assert_state("g112-assert-enemy-list", "EnemyList", "eq", L0.enemy_list(), "the enemies' start")
hook("g113-enemies-3", "StepEnemies(3)", "three deterministic chase steps")
assert_state("g114-assert-enemy-list", "EnemyList", "eq", CHASE_LIST3,
             "each enemy took the greedy step the re-implementation computes, vertical axis first "
             "when the vertical gap is the larger one")
assert_state("g115-assert-unit-hash", "UnitHash", "eq", CHASE_HASH3, "the unit hash agrees")
hook("g116-enemies-1", "StepEnemies(1)", "one more")
assert_state("g117-assert-enemy-list", "EnemyList", "eq", CHASE_LIST4, "and the list moved again")
assert_state("g118-assert-player", "PlayerRow", "eq", L0.pr, "the player has not moved at all")
assert_state("g119-assert-lives", "Lives", "eq", 3, "and has not been caught")
# --- walking into an enemy costs a life and respawns the player -----------------
force("g120-contact", CONTACT_SPEC, "the player and one enemy two cells apart")
hook("g121-step-right", 'Move("right")', "close the gap")
hook("g122-walk-into", 'Move("right")', "walk straight into the enemy")
assert_state("g123-assert-dead-by-enemy", "DeadByEnemy", "eq", True,
             "the death is recorded as an enemy catch, not a blast")
assert_state("g124-assert-exploded-0", "Exploded", "eq", False, "no blast was involved")
assert_state("g125-assert-lives-2", "Lives", "eq", 2, "one life gone")
assert_state("g126-assert-respawn", "PlayerRow", "eq", CONTACT_SIM.pr, "the player respawns")
assert_state("g127-assert-alive", "EnemiesAlive", "eq", 1, "and the enemy is still there")
assert_state("g128-assert-not-won", "Won", "eq", False, "the field is not cleared")
assert_state("g129-assert-unit-hash", "UnitHash", "eq", CONTACT_HASH,
             "the unit hash matches the re-implementation")
# --- the last life ends the game ----------------------------------------------
force("g130-last-life", spec_of(CONTACT, lives="1"), "the same board with a single life")
hook("g131-step-right", 'Move("right")', "close the gap")
hook("g132-walk-into", 'Move("right")', "walk into the enemy with the last life")
assert_state("g133-assert-lives-0", "Lives", "eq", 0, "no life is left")
assert_state("g134-assert-over", "GameOver", "eq", True, "and the game is over")
assert_state("g135-assert-not-won", "Won", "eq", False, "a loss is not a win")
hook("g136-move-after-over", 'Move("left")', "every move after that is refused")
assert_state("g137-assert-rejected", "RejectedMoves", "eq", 1, "the refusal is counted")
assert_state("g138-assert-reason", "LastEvent", "contains", "reason=game_over",
             "the refusal names the rule")
shot("g139-shot-t2", "bomb-t2", "the game-over frame: GAME OVER on the status label")
g("g140-assert-screen-over", "running_game_assert_screen_text", {"text": "GAME OVER"},
  "the status label really is on the captured screen")
# --- the win: destroy the last brick and the last enemy in one blast ------------
force("g141-win-setup", spec_of(LEVEL1), "one brick and one enemy, a bomb's reach apart")
assert_state("g142-assert-bricks", "BricksRemaining", "eq", 1, "one brick")
assert_state("g143-assert-enemies", "EnemiesAlive", "eq", 1, "one enemy")
walk("g144", WIN, ["down", "down", "down"], "walk down to the brick's row")
walk("g147", WIN, ["right", "right", "right", "right", "right"], "walk east to the brick's column")
assert_state("g152-assert-player", "PlayerCol", "eq", 6,
             "the player is under the brick (six columns east of its start) -- asserted with the "
             "column it must have RIGHT NOW, not the one the finished scenario ends on")
assert_state("g152b-assert-player-row", "PlayerRow", "eq", 4, "and on the brick's row")
assert_state("g152c-assert-moves", "Moves", "eq", 8, "eight accepted walks so far")
hook("g153-place", "PlaceBomb()", "drop the bomb on the enemy's column")
walk("g154", WIN, ["left", "left", "left"], "walk west, out of the blast")
hook("g157-fuse", "StepFuse(3)", "let the fuse run out")
assert_state("g158-assert-blast", "LastBlast", "eq", WIN_BLAST,
             "the blast the re-implementation computes: north into the brick, south onto the enemy")
assert_state("g159-assert-bricks-left-0", "BricksRemaining", "eq", 0, "the last brick is gone")
assert_state("g160-assert-enemies-alive-0", "EnemiesAlive", "eq", 0, "and the last enemy is dead")
assert_state("g161-assert-enemies-killed", "EnemiesKilled", "eq", 1, "one kill on the record")
assert_state("g162-assert-won", "Won", "eq", True, "every brick and every enemy gone is the win")
assert_state("g163-assert-over", "GameOver", "eq", True, "the level is over")
assert_state("g164-assert-not-exploded", "Exploded", "eq", False, "the player was clear")
assert_state("g165-assert-lives", "Lives", "eq", 3, "and kept all three lives")
assert_state("g166-assert-score", "Score", "eq", 110, "ten for the brick plus a hundred for the kill")
assert_state("g167-assert-hash", "GridHash", "eq", WIN.grid_hash(), "the grid hash agrees")
shot("g168-shot-t3", "bomb-t3", "the cleared field: FIELD CLEARED on the status label")
g("g169-assert-screen-win", "running_game_assert_screen_text", {"text": "FIELD CLEARED"},
  "the status label really is on the captured screen")
# --- the frame-rate independent increment: one hook call, one exact delta ------
force("g170-tick-setup", TICK_SPEC, "one bomb with a six-tick fuse and nothing else that moves")
hook("g171-steptick-2", "StepTick(2)", "exactly two deterministic ticks")
assert_state("g172-assert-last-hook", "LastHookSteps", "eq", TICK_ACCEPT2,
             "the DELTA of that call is exact -- this is the frame-rate independent quantity")
assert_state("g173-assert-last-auto-0", "LastAutoSteps", "eq", 0,
             "and it is a DIFFERENT property from the clock's own per-frame delta, which is 0 "
             "while the clock is off")
assert_state("g174-assert-bomb-fuse", "BombList", "eq", TICK_SIM.bomb_list(),
             "two ticks came off the fuse, exactly as the re-implementation says")
assert_state("g175-assert-detonations-0", "Detonations", "eq", 0, "nothing has gone off")
assert_state("g175b-assert-bombs-1", "BombsActive", "eq", 1, "and the bomb is still live")
# --- multi-frame sample of the auto clock: the fuse runs out and the field moves
# NOTE: this block deliberately does NOT call ForceTestState again. Minesweeper's r1 run
# (TASK-100, defect M1) did, and its closing assertion then read 0: ForceTestState pins the
# WHOLE state, so it zeroes the hook's delta as well. One pinned board spans the hook, the
# clock and both deltas, which is what makes "the clock does not write the hook's property"
# a fact rather than an assumption.
hook("g176-clock-on", "SetAutoClock(60.0)",
     "the one sample that watches the fuse burn asks for motion explicitly")
assert_state("g177-assert-hook-intact", "LastHookSteps", "eq", TICK_ACCEPT2,
             "the clock has been running for several frames and the hook's own delta is still "
             "exactly what the hook wrote -- two producers, two properties")
samples("g178-samples-clock",
        ["BombsActive", "BombList", "BricksRemaining", "GridHash", "LastBlastCount",
         "Detonations", "AutoTicks", "LastAutoSteps", "Elapsed", "Ticks"], 30,
        "multi-frame property sample of the auto clock: the fuse counts down frame by frame "
        "(BombList changes), then the bomb goes off (BombsActive drops, Detonations and "
        "LastBlastCount jump, GridHash and BricksRemaining change) while Elapsed and Ticks "
        "advance -- 'the bomb goes off' as a sequence of values, not as an adjective")
assert_state("g179-assert-fired", "Detonations", "eq", 1,
             "the clock set the bomb off exactly once inside the sample window")
assert_state("g179a-assert-bombs-0", "BombsActive", "eq", 0, "and no bomb is live any more")
assert_state("g179b-assert-blast", "LastBlast", "eq", CLOCK_BLAST,
             "and the blast is the re-implementation's")
assert_state("g179c-assert-blast-count", "LastBlastCount", "eq", CLOCK_BLAST_COUNT,
             "with the re-implementation's cell count")
assert_state("g179d-assert-auto-ticks", "AutoTicks", "gt", 4,
             "the clock ran for more than the four ticks that were left in the fuse -- i.e. it "
             "kept ticking after the blast instead of stopping on a decided board (B-3)")
assert_state("g180-assert-brick-gone", "BricksRemaining", "eq", CLOCK_BRICKS_LEFT,
             "exactly the two bricks the blast reached are gone, and the third is still standing")
assert_state("g180b-assert-not-over", "GameOver", "eq", False,
             "the sample's board was never decided -- that is what made B-3 a defect")
assert_state("g180c-assert-lives", "Lives", "eq", 3, "and the player was clear of the blast")
hook("g181-clock-off", "SetAutoClock(0.0)", "back to frozen")
assert_state("g182-assert-last-auto-0", "LastAutoSteps", "eq", 0, "the per-frame delta is zero again")
assert_state("g183-assert-hook-intact", "LastHookSteps", "eq", TICK_ACCEPT2,
             "while the hook's own delta is untouched by the clock, before or after it runs")
shot("g184-shot-t4", "bomb-t4", "the field after the clock burned the fuse down")
# --- the declared input path really drives the game ----------------------------
force("g185-input-setup", spec_of(LEVEL0), "a clean classic field for the input test")
assert_state("g186-assert-hook-zeroed", "LastHookSteps", "eq", 0,
             "ForceTestState pins the WHOLE state, so it zeroes the hook's delta too -- the M1 "
             "lesson stated as an assertion instead of an assumption")
hook("g187-poll-on", "SetPollInput(true)",
     "the input path is off by default; the test switches it on explicitly")
g("g188-input-right", "running_game_run_test_scenario",
  {"steps": [{"type": "input", "action": "bomb_right", "pressed": True},
             {"type": "wait", "seconds": 0.45},
             {"type": "assert", "node_path": "Main", "property": "PlayerCol",
              "operator": "gt", "expected": L0.pc}]},
  "the declared action really walks the player one cell east")
assert_state("g189-assert-input-moves-1", "InputMoves", "eq", 1,
             "the declared action fires on the PRESS EDGE, so a scenario's never-released key "
             "performs exactly one move instead of repeating at the frame rate")
assert_state("g190-assert-player-moved", "PlayerCol", "eq", L0.pc + 1,
             "the player is exactly one cell east of where it started")
g("g191-input-place", "running_game_run_test_scenario",
  {"steps": [{"type": "input", "action": "bomb_place", "pressed": True},
             {"type": "wait", "seconds": 0.45},
             {"type": "assert", "node_path": "Main", "property": "BombsActive",
              "operator": "gt", "expected": 0}]},
  "the declared place action really drops a bomb")
assert_state("g192-assert-input-bombs-1", "InputBombs", "eq", 1, "one bomb arrived by input")
assert_state("g193-assert-bombs-1", "BombsActive", "eq", 1, "and it is live")
hook("g194-poll-off", "SetPollInput(false)",
     "polling off again: nothing after this can drift because a key is still marked held")
# --- positive control: a node created at run time is drawn ----------------------
g("g195-runtime-overlay", "running_game_execute_gdscript",
  code('var main = get_parent()\nvar c = ColorRect.new()\nc.name = StringName("ProbeOverlay")\n'
       'c.position = Vector2(20, 552)\nc.size = Vector2(120, 34)\n'
       'c.color = Color(0.95, 0.35, 0.95, 1.0)\nmain.add_child(c)\nreturn "overlay added"'),
  "a node created at run time, in the same session, as the positive control for 'a run-time node "
  "is drawn'")
# --- DECLARED FAILURE: the error path of the assertion tool ---------------------
g("g196-assert-unknown-property", "running_game_assert_node_state",
  {"node_path": "Main", "property": "NoSuchProperty", "operator": "eq", "expected": 1},
  "DECLARED FAILURE: a boundary call asking for a property that does not exist (-32001), so the "
  "error path of the assertion tool is on the record too")
shot("g197-shot-t5", "bomb-t5", "the overlay is visible in this frame and not in t4")
force("g198-final-level", spec_of(LEVEL0), "ask for the classic field once more")
assert_state("g199-assert-bricks", "BricksTotal", "eq", L0.bricks_total, "the field is back")
assert_state("g200-assert-hash", "GridHash", "eq", L0.grid_hash(),
             "and it reproduces the very same hash the Python re-implementation predicted")
hook("g201-final-readback", "Dump()", "the final field as one line")
g("g202-final-tree", "running_game_get_scene_tree", {},
  "the final tree, including the run-time overlay")

doc = {"import": True, "calls": calls}
os.makedirs(os.path.dirname(OUT), exist_ok=True)
with io.open(OUT, "w", encoding="utf-8", newline="\n") as handle:
    handle.write(json.dumps(doc, ensure_ascii=False, indent=1) + "\n")

print("wrote %s calls=%d" % (OUT, len(calls)))
print("L0 grid=%d unit=%d bricks=%d enemies=%s" % (
    L0.grid_hash(), L0.unit_hash(), L0.bricks_total, L0.enemy_list()))
print("BOMB1 blast=%s (%d) bricks_left=%d hash=%d player=%d,%d moves=%d rejected=%d" % (
    BOMB1_BLAST, len(BOMB1.last_blast), BOMB1.bricks_remaining, BOMB1.grid_hash(),
    BOMB1.pr, BOMB1.pc, BOMB1.moves, BOMB1.rejected))
print("CORRIDOR blast=%s (%d) left=%d hash=%d" % (
    CORRIDOR_BLAST, len(CORRIDOR_SIM.last_blast), CORRIDOR_SIM.bricks_remaining,
    CORRIDOR_SIM.grid_hash()))
print("CORRIDOR_KILL lives=%d exploded=%s player=%d,%d" % (
    CORRIDOR_KILL.lives, CORRIDOR_KILL.exploded, CORRIDOR_KILL.pr, CORRIDOR_KILL.pc))
print("CHAIN blast=%s (%d)" % (CHAIN_BLAST, len(CHAIN_SIM.last_blast)))
print("CHASE list3=%s hash3=%d list4=%s" % (CHASE_LIST3, CHASE_HASH3, CHASE_LIST4))
print("CONTACT list=%s lives=%d player=%d,%d hash=%d" % (
    CONTACT_SIM.enemy_list(), CONTACT_SIM.lives, CONTACT_SIM.pr, CONTACT_SIM.pc, CONTACT_HASH))
print("WIN blast=%s (%d) bricks=%d enemies=%d score=%d hash=%d player=%d,%d" % (
    WIN_BLAST, len(WIN.last_blast), WIN.bricks_remaining, len(WIN.enemies),
    WIN.bricks_destroyed * 10 + WIN.enemies_killed * 100, WIN.grid_hash(), WIN.pr, WIN.pc))
print("TICK accepted=%d bomb_list=%s" % (TICK_ACCEPT2, TICK_SIM.bomb_list()))
