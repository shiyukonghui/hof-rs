# -*- coding: utf-8 -*-
"""TASK-102: build the Platformer session (editor + game phases).

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

THE INDEPENDENT RECOMPUTATION.  ``PSim`` below is a second implementation of the
payload's own rules -- the tile map, the integer kinematics of one fixed frame, the
axis-separated collision resolution, the pickups, the goal, the pit -- written from
the rules rather than translated from the C#.  Every literal this generator bakes
into the session (the frame-by-frame jump arc, the landing frame, the walk
positions, the collected counts, both hashes) is the one ``PSim`` produced, so a
frame the C# integrates differently shows up as a FAILED assertion.

The level data itself has ONE author: this file.  It writes the two literals into
``payload/PlatformerGame.cs`` (between the ``@LEVEL0@`` / ``@LEVEL1@`` markers) so
the payload and the re-implementation cannot disagree about the map.
"""
import io
import json
import os

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.abspath(os.path.join(HERE, "..", "..", ".."))
SESSION_DIR = os.path.join(ROOT, "tools", "sessions", "platformer")
PAYLOAD = os.path.join(SESSION_DIR, "payload", "PlatformerGame.cs")
OUT = os.path.join(SESSION_DIR, "session.json")

TILE = 20
COLS = 40
ROWS = 30
PW = 16
PH = 16
GRAVITY = 1
MAXFALL = 16
RUN = 4
JUMPVEL = 12
AIRJUMPVEL = 10
GEM_POINTS = 10


def blank_map():
    return [["." for _ in range(COLS)] for _ in range(ROWS)]


def put(rows, r, c, ch):
    rows[r][c] = ch


# --- LEVEL0: the full course -------------------------------------------------
L0 = blank_map()
# the ground, two rows thick, with a three-tile pit at 12..14 and a four-tile pit at 33..36
GROUND = "#" * 12 + "." * 3 + "#" * 18 + "." * 4 + "#" * 3
assert len(GROUND) == COLS, len(GROUND)
for c in range(COLS):
    put(L0, 28, c, GROUND[c])
    put(L0, 29, c, GROUND[c])
# four floating platforms
for (row, a, b) in ((22, 6, 11), (18, 14, 21), (14, 22, 28), (10, 30, 36)):
    for c in range(a, b + 1):
        put(L0, row, c, "#")
# collectibles sitting on top of each of them, plus three at ground level
for (row, cols) in ((21, (7, 9)), (17, (15, 17, 19)), (13, (23, 25, 27)),
                    (9, (31, 33, 35)), (27, (20, 25, 30))):
    for c in cols:
        put(L0, row, c, "C")
put(L0, 27, 2, "@")
put(L0, 27, 38, "G")
LEVEL0 = "/".join("".join(row) for row in L0)
assert len(LEVEL0.split("/")) == ROWS

# --- LEVEL1: a flat strip for the pure physics -------------------------------
L1 = blank_map()
for c in range(COLS):
    put(L1, 28, c, "#")
    put(L1, 29, c, "#")
put(L1, 27, 2, "@")
LEVEL1 = "/".join("".join(row) for row in L1)


def i32(v):
    v &= 0xFFFFFFFF
    return v - 0x100000000 if v >= 0x80000000 else v


class PSim(object):
    """A second implementation of Platformer's integer kinematics, from the spec."""

    def __init__(self, spec, player=None, gems=None, goal=None, lives=3, vel=None,
                 ground=False, double_jump=True):
        self.spec = spec
        raw = spec.split("/")
        self.rows = len(raw)
        self.cols = max(len(line) for line in raw)
        self.solid = [[False] * self.cols for _ in range(self.rows)]
        self.gem = [[False] * self.cols for _ in range(self.rows)]
        self.goal = [[False] * self.cols for _ in range(self.rows)]
        self.spawn_row = self.spawn_col = 0
        self.goal_row = self.goal_col = -1
        for r, line in enumerate(raw):
            for c in range(self.cols):
                ch = line[c] if c < len(line) else "."
                if ch == "#":
                    self.solid[r][c] = True
                elif ch == "C":
                    self.gem[r][c] = True
                elif ch == "G":
                    self.goal[r][c] = True
                    self.goal_row, self.goal_col = r, c
                elif ch == "@":
                    self.spawn_row, self.spawn_col = r, c
        self.spawn_x = self.spawn_col * TILE + (TILE - PW) // 2
        self.spawn_y = self.spawn_row * TILE + (TILE - PH) // 2
        if gems is not None:
            self.gem = [[False] * self.cols for _ in range(self.rows)]
            for (r, c) in gems:
                self.gem[r][c] = True
        if goal is not None:
            self.goal = [[False] * self.cols for _ in range(self.rows)]
            if goal:
                self.goal[goal[0]][goal[1]] = True
                self.goal_row, self.goal_col = goal
            else:
                self.goal_row = self.goal_col = -1
        self.gems_total = sum(1 for r in range(self.rows) for c in range(self.cols)
                              if self.gem[r][c])
        self.x, self.y = player if player else (self.spawn_x, self.spawn_y)
        self.vx, self.vy = vel if vel else (0, 0)
        self.on_ground = ground
        self.facing = 1
        self.double_jump = double_jump
        self.gems_remaining = self.gems_total
        self.collected = 0
        self.score = 0
        self.lives = lives
        self.falls = 0
        self.won = False
        self.game_over = False
        self.frames = 0
        self.jumps = 0
        self.air_jumps = 0
        self.jumps_rejected = 0
        self.wall_hits = 0
        self.landings = 0
        self.arc = []

    # --- the map ---------------------------------------------------------------
    def in_bounds(self, r, c):
        return 0 <= r < self.rows and 0 <= c < self.cols

    def out_of_map_solid(self, r, c):
        if r < 0:
            return True
        if c < 0 or c >= self.cols:
            return True
        if r >= self.rows:
            return False
        return self.solid[r][c]

    def overlaps(self, x, y):
        if x < 0 or y < 0:
            return True
        if x + PW > self.cols * TILE:
            return True
        c0, c1 = x // TILE, (x + PW - 1) // TILE
        r0, r1 = y // TILE, (y + PH - 1) // TILE
        for r in range(r0, r1 + 1):
            for c in range(c0, c1 + 1):
                if self.out_of_map_solid(r, c):
                    return True
        return False

    def map_hash(self):
        h = 17
        for r in range(self.rows):
            for c in range(self.cols):
                code = 1 if self.solid[r][c] else (5 if self.goal[r][c] else (3 if self.gem[r][c] else 2))
                h = i32(h * 31 + code)
        return h

    def state_hash(self):
        h = 17
        for v in (self.x, self.y, self.vx, self.vy, 1 if self.on_ground else 0):
            h = i32(h * 31 + v)
        return h

    def recompute(self):
        remaining = sum(1 for r in range(self.rows) for c in range(self.cols) if self.gem[r][c])
        self.gems_remaining = remaining
        self.collected = self.gems_total - remaining
        self.score = self.collected * GEM_POINTS

    # --- the fixed frame -------------------------------------------------------
    def frame(self):
        if self.game_over:
            return
        self.frames += 1
        self.x += self.vx
        if self.overlaps(self.x, self.y):
            # the world's own edges are exact pixel clamps; the tile-relative formulas assume the
            # leading edge is inside a tile (PL-1 in the payload's first run)
            if self.x < 0:
                self.x = 0
            elif self.x + PW > self.cols * TILE:
                self.x = self.cols * TILE - PW
            elif self.vx > 0:
                self.x = ((self.x + PW - 1) // TILE) * TILE - PW
            elif self.vx < 0:
                self.x = (self.x // TILE + 1) * TILE
            else:
                self.x = self.spawn_x
            self.vx = 0
            self.wall_hits += 1
        self.vy += GRAVITY
        if self.vy > MAXFALL:
            self.vy = MAXFALL
        self.y += self.vy
        self.on_ground = False
        if self.overlaps(self.x, self.y):
            if self.y < 0:
                self.y = 0
            elif self.vy > 0:
                self.y = ((self.y + PH - 1) // TILE) * TILE - PH
                self.on_ground = True
            elif self.vy < 0:
                self.y = (self.y // TILE + 1) * TILE
            self.vy = 0
            self.landings += 1
        self.check_pickups()
        if self.y > self.rows * TILE:
            self.fall()
        self.recompute()

    def check_pickups(self):
        c0, c1 = self.x // TILE, (self.x + PW - 1) // TILE
        r0, r1 = self.y // TILE, (self.y + PH - 1) // TILE
        for r in range(r0, r1 + 1):
            for c in range(c0, c1 + 1):
                if not self.in_bounds(r, c):
                    continue
                if self.gem[r][c]:
                    self.gem[r][c] = False
                    self.collected += 1
                    self.score += GEM_POINTS
                if self.goal[r][c]:
                    self.won = True
                    self.game_over = True

    def fall(self):
        self.falls += 1
        self.lives -= 1
        if self.lives <= 0:
            self.game_over = True
            self.won = False
            return
        self.x, self.y = self.spawn_x, self.spawn_y
        self.vx = self.vy = 0
        self.on_ground = False

    # --- the hooks -------------------------------------------------------------
    def set_run(self, direction):
        d = -1 if direction < 0 else (1 if direction > 0 else 0)
        self.vx = d * RUN
        if d:
            self.facing = d

    def jump(self):
        if self.game_over:
            self.jumps_rejected += 1
            return "game_over"
        if self.on_ground:
            self.vy = -JUMPVEL
            self.on_ground = False
            self.jumps += 1
            return "ground"
        if self.double_jump and self.air_jumps < 1:
            self.vy = -AIRJUMPVEL
            self.on_ground = False
            self.air_jumps += 1
            self.jumps += 1
            return "air"
        self.jumps_rejected += 1
        return "rejected"

    def step(self, n):
        applied = 0
        for _ in range(n):
            if self.game_over:
                break
            self.frame()
            applied += 1
            self.arc.append((self.frames, self.x, self.y, self.vy, self.on_ground))
        return applied


def spec_of(level, **kwargs):
    parts = ["level=" + level]
    for key in ("player", "gems", "goal", "lives", "vel", "ground"):
        if key in kwargs and kwargs[key] is not None:
            parts.append("%s=%s" % (key, kwargs[key]))
    return ";".join(parts)


# =============================================================================
# the scenarios, each one in EXACTLY the order the session's hooks appear in
# =============================================================================
L0S = PSim(LEVEL0)
L1S = PSim(LEVEL1)

# --- B: the landing after the spawn drop on the default board -----------------
DROP = PSim(LEVEL0)
DROP.step(4)
DROP_X, DROP_Y, DROP_GROUND = DROP.x, DROP.y, DROP.on_ground
DROP_VY, DROP_LANDINGS = DROP.vy, DROP.landings

# --- C: running left into the world wall --------------------------------------
WALL = PSim(LEVEL0)
WALL.set_run(-1)
WALL.step(30)

# --- D: the pure jump arc on the flat strip (the independent recomputation) ---
ARC_SPEC = spec_of(LEVEL1, player="100,544", gems="", vel="0,0", ground="1")
ARC = PSim(LEVEL1, player=(100, 544), gems=[], goal=None,
           vel=(0, 0), ground=True)
ARC.kind = ARC.jump()
ARC.ARCAFTER = (ARC.x, ARC.y, ARC.vy, ARC.on_ground)
ARC_CHECKPOINTS = []
ARC_STEPS = []
for step in (1, 5, 5, 1, 1, 5, 5, 1):
    ARC.step(step)
    ARC_STEPS.append(step)
    ARC_CHECKPOINTS.append((ARC.frames, ARC.x, ARC.y, ARC.vy, ARC.on_ground,
                            ARC.landings))
ARC_AIR_FRAME_23 = ARC_CHECKPOINTS[6]
ARC_LAND_FRAME_24 = ARC_CHECKPOINTS[7]

# --- E: the double jump --------------------------------------------------------
DJ_SPEC = spec_of(LEVEL1, player="100,544", gems="", vel="0,0", ground="1")
DJ = PSim(LEVEL1, player=(100, 544), gems=[], goal=None, vel=(0, 0), ground=True)
DJ.jump()          # the ground jump: jumps=1, air=0, vy=-12
DJ.step(3)         # three frames of the arc
DJ_AFTER3 = (DJ.x, DJ.y, DJ.vy, DJ.on_ground, DJ.air_jumps, DJ.jumps)
DJ.kind2 = DJ.jump()   # the mid-air jump: air=1, jumps=2, vy=-10
DJ_AFTER_AIR = (DJ.vy, DJ.air_jumps, DJ.jumps)
DJ.step(1)
DJ_AFTER_AIR1 = (DJ.x, DJ.y, DJ.vy)
DJ.kind3 = DJ.jump()   # refused: no jump left
DJ_AFTER_REFUSE = (DJ.jumps_rejected, DJ.air_jumps, DJ.jumps, DJ.vy)

DJ2 = PSim(LEVEL1, player=(100, 544), gems=[], goal=None, vel=(0, 0), ground=True,
           double_jump=False)
DJ2.jump()
DJ2.step(3)
DJ2_AFTER3 = (DJ2.x, DJ2.y, DJ2.vy)
DJ2.kind2 = DJ2.jump()  # refused: the optional mid-air jump is switched off
DJ2_AFTER_REFUSE = (DJ2.jumps_rejected, DJ2.air_jumps, DJ2.jumps)

# --- F: the collectibles -------------------------------------------------------
GEM_SPEC = spec_of(LEVEL1, player="40,544", gems="27,3|27,4", vel="0,0", ground="1")
GEM = PSim(LEVEL1, player=(40, 544), gems=[(27, 3), (27, 4)], goal=None,
           vel=(0, 0), ground=True)
GEM.set_run(1)
GEM.step(5)
GEM_AFTER5 = (GEM.x, GEM.collected, GEM.score, GEM.gems_remaining)
GEM.step(5)
GEM_AFTER10 = (GEM.x, GEM.collected, GEM.score, GEM.gems_remaining, GEM.map_hash())
GEM.step(5)
GEM_AFTER15 = (GEM.x, GEM.collected, GEM.score)

# --- G: the goal ---------------------------------------------------------------
GOAL_SPEC = spec_of(LEVEL0, player="740,544", vel="0,0", ground="1")
GOAL = PSim(LEVEL0, player=(740, 544), vel=(0, 0), ground=True)
GOAL.set_run(1)
GOAL.step(5)
GOAL_AT = (GOAL.x, GOAL.won, GOAL.game_over, GOAL.collected)
GOAL_AFTER_OVER = GOAL.step(3)

# --- H: the pit -----------------------------------------------------------------
PIT_SPEC = spec_of(LEVEL0, player="244,544", vel="0,0")
PIT = PSim(LEVEL0, player=(244, 544), vel=(0, 0))
PIT.step(10)
PIT_BEFORE = (PIT.x, PIT.y, PIT.lives, PIT.falls, PIT.game_over)
PIT.step(1)
PIT_AFTER = (PIT.x, PIT.y, PIT.lives, PIT.falls, PIT.game_over)

PIT_LAST_SPEC = spec_of(LEVEL0, player="244,544", vel="0,0", lives="1")
PIT_LAST = PSim(LEVEL0, player=(244, 544), vel=(0, 0), lives=1)
PIT_LAST.step(11)
PIT_LAST_AFTER = (PIT_LAST.lives, PIT_LAST.falls, PIT_LAST.game_over, PIT_LAST.won)

# --- I: the frame-rate independent increment ------------------------------------
INC_SPEC = spec_of(LEVEL1, player="100,544", gems="", vel="0,0", ground="1")
INC = PSim(LEVEL1, player=(100, 544), gems=[], goal=None, vel=(0, 0), ground=True)
INC.set_run(1)
INC.step(3)
INC_X, INC_Y, INC_GROUND = INC.x, INC.y, INC.on_ground

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


BG = {"type": "ColorRect", "name": "Background", "parent_path": ".",
      "properties": {"offset_left": 0, "offset_top": 0, "offset_right": 800,
                     "offset_bottom": 600, "color": {"r": 0.04, "g": 0.05, "b": 0.08, "a": 1}}}
HUD = {"type": "Label", "name": "Hud", "parent_path": ".",
       "properties": {"offset_left": 14, "offset_top": 8, "offset_right": 640,
                      "offset_bottom": 42, "text": "GEMS 0/14  SCORE 0  LIVES 3  AIR 0  TILE 2,27",
                      "theme_override_font_sizes/font_size": 22}}
STATUS = {"type": "Label", "name": "Status", "parent_path": ".",
          "properties": {"offset_left": 632, "offset_top": 8, "offset_right": 795,
                         "offset_bottom": 42, "text": "RUN AND JUMP",
                         "theme_override_font_sizes/font_size": 22}}
STATIC_BATCH = [BG, HUD, STATUS]

# =============================================================================
# editor phase (14 calls)
# =============================================================================
e("e01-edit-game", "project_edit_script",
  {"path": "res://src/PlatformerGame.cs", "content_file": "payload/PlatformerGame.cs"},
  "the whole game is written through the MCP script writer (the template stub is replaced)")
e("e02-open-scene", "editor_open_scene", {"path": "res://scenes/main.tscn"},
  "the template scene carries the root Main (Node2D) the script is attached to")
e("e03-batch-add-static", "editor_add_nodes_batch", {"nodes": STATIC_BATCH},
  "the three static nodes of the scene, through the batch tool: a background and two labels; "
  "every tile, every collectible, the goal and the player are created at run time")
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
e("e10-action-left", "editor_add_input_action", {"action": "plat_left", "key": "A"}, "run left")
e("e11-action-right", "editor_add_input_action", {"action": "plat_right", "key": "D"}, "run right")
e("e12-action-jump", "editor_add_input_action", {"action": "plat_jump", "key": "Space"}, "jump")
e("e13-build-csharp", "project_build_csharp",
  {"configuration": "Debug", "timeout_ms": 300000, "rescan": True},
  "compile the game the MCP script writer just wrote")
e("e14-validate-scripts", "project_validate_scripts", {}, "the engine's own per-file verdict")

# =============================================================================
# game phase
# =============================================================================
g("g01-scene-tree", "running_game_get_scene_tree", {},
  "the running tree: the three static nodes plus the solid tiles, the gems, the goal and the "
  "player created at run time")
hook("g02-readback-t0", "Dump()", "the whole map as one line plus every fact")
assert_state("g03-assert-cols", "Cols", "eq", L0S.cols, "the course is forty tiles wide")
assert_state("g04-assert-rows", "Rows", "eq", L0S.rows, "and thirty tiles tall")
assert_state("g05-assert-tile", "Tile", "eq", TILE, "twenty pixels a tile")
assert_state("g06-assert-level", "LevelIndex", "eq", 0, "the default level is the full course")
assert_state("g07-assert-gems-total", "GemsTotal", "eq", L0S.gems_total,
             "fourteen collectibles")
assert_state("g08-assert-gems-left", "GemsRemaining", "eq", L0S.gems_remaining,
             "all fourteen still on the map")
assert_state("g09-assert-collected-0", "Collected", "eq", 0, "none taken yet")
assert_state("g10-assert-score-0", "Score", "eq", 0, "and no points")
assert_state("g11-assert-map-hash", "MapHash", "eq", L0S.map_hash(),
             "the map hash is the one the Python re-implementation computes from the same rule")
assert_state("g12-assert-spawn-row", "SpawnRow", "eq", L0S.spawn_row, "the spawn tile from the '@'")
assert_state("g13-assert-spawn-col", "SpawnCol", "eq", L0S.spawn_col, "and the spawn column")
assert_state("g14-assert-spawn-x", "SpawnX", "eq", L0S.spawn_x, "the spawn pixel, centred in the tile")
assert_state("g15-assert-spawn-y", "SpawnY", "eq", L0S.spawn_y, "in both axes")
assert_state("g16-assert-player-x", "PlayerX", "eq", L0S.x, "the player starts here")
assert_state("g17-assert-player-y", "PlayerY", "eq", L0S.y, "in both axes")
assert_state("g18-assert-vel", "VelY", "eq", 0, "at rest")
assert_state("g19-assert-not-ground", "OnGround", "eq", False,
             "the spawn sits two pixels above the ground, so the player is not standing yet")
assert_state("g20-assert-goal-row", "GoalRow", "eq", L0S.goal_row, "the goal tile was read from the 'G'")
assert_state("g21-assert-goal-col", "GoalCol", "eq", L0S.goal_col, "and its column")
assert_state("g22-assert-lives", "Lives", "eq", 3, "three lives")
assert_state("g23-assert-not-won", "Won", "eq", False, "the goal is not reached")
assert_state("g24-assert-not-over", "GameOver", "eq", False, "and the game is running")
probe("g25-probe-solid", 28, 0, "the ground")
assert_state("g26-assert-probe-solid", "ProbeState", "eq", "solid", "it reads as solid")
probe("g27-probe-empty", 27, 5, "an open tile")
assert_state("g28-assert-probe-empty", "ProbeState", "eq", "empty", "it reads as empty")
probe("g29-probe-gem", 27, 20, "one of the ground-level collectibles")
assert_state("g30-assert-probe-gem", "ProbeState", "eq", "gem", "it reads as a gem")
probe("g31-probe-goal", 27, 38, "the goal tile")
assert_state("g32-assert-probe-goal", "ProbeState", "eq", "goal", "it reads as the goal")
probe("g33-probe-player", 27, 2, "the tile the player occupies")
assert_state("g34-assert-probe-player", "ProbeState", "eq", "player", "it reads as the player")
shot("g35-shot-t0", "plat-t0", "the first frame: the full course with fourteen gems and the goal")
samples("g36-samples-frozen",
        ["MapHash", "GemsRemaining", "PlayerX", "PlayerY", "OnGround", "Elapsed", "Ticks"], 12,
        "determinism baseline: with AutoClock 0 nothing in the world moves while the clock runs "
        "(map hash / gems / player position / ground flag constant, Elapsed and Ticks both "
        "increasing)")
assert_state("g37-assert-last-auto-0", "LastAutoSteps", "eq", 0,
             "the clock's per-frame delta is zero while the clock is off")
# --- B: the spawn drop, frame by frame -----------------------------------------
hook("g38-step-4", "StepFrames(4)", "four fixed frames: the player falls the two pixels to the ground")
assert_state("g39-assert-drop-x", "PlayerX", "eq", DROP_X, "no horizontal motion")
assert_state("g40-assert-drop-y", "PlayerY", "eq", DROP_Y,
             "exactly the ground row the re-implementation lands on")
assert_state("g41-assert-drop-ground", "OnGround", "eq", DROP_GROUND, "and the player is standing")
assert_state("g42-assert-drop-vy", "VelY", "eq", DROP_VY, "with the vertical speed cleared")
assert_state("g43-assert-landings", "Landings", "eq", DROP_LANDINGS,
             "the landing count is the re-implementation's")
assert_state("g44-assert-last-hook", "LastHookSteps", "eq", 4,
             "the hook reports the frames it actually applied")
assert_state("g45-assert-state-hash", "StateHash", "eq", DROP.state_hash(),
             "the kinematic state hash agrees with the re-implementation")
# --- C: the wall ---------------------------------------------------------------
hook("g46-run-left", "SetRun(-1)", "hold left")
hook("g47-step-30", "StepFrames(30)", "thirty frames: the player crosses to the left wall")
assert_state("g48-assert-x", "PlayerX", "eq", WALL.x,
             "the wall stops the box at the map edge, at exactly the re-implementation's pixel")
assert_state("g49-assert-wall-hits", "WallHits", "eq", WALL.wall_hits, "one wall stop")
assert_state("g50-assert-vx-0", "VelX", "eq", 0, "and the horizontal speed is cleared")
assert_state("g51-assert-facing", "Facing", "eq", -1, "the player was facing left")
assert_state("g52-assert-ground", "OnGround", "eq", True, "and is still standing on the ground")
shot("g53-shot-t1", "plat-t1", "the player is against the left wall")
# --- D: the jump arc, frame by frame (the parabolic landing, recomputed) --------
force("g54-arc-setup", ARC_SPEC,
      "a flat strip, the player standing on the ground, everything else switched off")
assert_state("g55-assert-ground", "OnGround", "eq", True, "pinned standing")
assert_state("g56-assert-y", "PlayerY", "eq", 544, "at the pinned height")
hook("g57-jump", "Jump()", "the ground jump")
assert_state("g58-assert-vy", "VelY", "eq", -JUMPVEL, "the jump's exact launch speed")
assert_state("g59-assert-jumps", "Jumps", "eq", 1, "one jump on the record")
assert_state("g60-assert-air-0", "AirJumps", "eq", 0, "and no mid-air jump yet")
assert_state("g61-assert-not-ground", "OnGround", "eq", False, "the player is airborne")
_arc_tags = []
_steps = ARC_STEPS
_labels = ["frame 1", "frame 6", "frame 11 (apex)", "frame 12 (apex, vy flips sign)",
           "frame 13", "frame 18", "frame 23 (back at ground height but still airborne)",
           "frame 24 (the landing frame)"]
for index, (step, (frame, x, y, vy, grounded, landings)) in enumerate(
        zip(_steps, ARC_CHECKPOINTS)):
    tag = "g%02d" % (62 + index * 5)
    hook(tag + "-step", "StepFrames(%d)" % step,
         "advance the arc to %s" % _labels[index])
    assert_state(tag + "a-assert-y", "PlayerY", "eq", y,
                 "%s: y = %.0f, the value the Python integration of the same integer kinematics "
                 "predicts" % (_labels[index], y))
    assert_state(tag + "b-assert-vy", "VelY", "eq", vy,
                 "%s: the vertical speed the re-implementation predicts at that frame" % _labels[index])
    assert_state(tag + "c-assert-ground", "OnGround", "eq", grounded,
                 "%s: still airborne, or landed -- the re-implementation decides" % _labels[index])
    assert_state(tag + "d-assert-x", "PlayerX", "eq", x, "no horizontal input, so x never moves")
    _arc_tags.append(tag)
assert_state("g102-assert-landed-y", "PlayerY", "eq", ARC_LAND_FRAME_24[2],
             "the landing frame snapped the box exactly onto the platform top")
assert_state("g103-assert-landed-ground", "OnGround", "eq", True, "and the player is standing")
assert_state("g104-assert-landed-vy", "VelY", "eq", 0, "with the vertical speed cleared")
assert_state("g105-assert-frame23-y", "PlayerY", "eq", ARC_AIR_FRAME_23[2],
             "one frame earlier the box was ALREADY at the ground height but still in the air -- "
             "the y alone does not decide a landing, the resolution does")
assert_state("g106-assert-jumps-1", "Jumps", "eq", 1, "still exactly one jump")
shot("g107-shot-t2", "plat-t2", "the player is back on the ground after the arc")
# --- E: the double jump --------------------------------------------------------
force("g108-dj-setup", DJ_SPEC, "the same flat strip for the double-jump test")
hook("g109-dj-ground", "Jump()", "the ground jump")
hook("g110-dj-step3", "StepFrames(3)", "three frames of the first arc")
assert_state("g111-assert-dj-vy", "VelY", "eq", DJ_AFTER3[2],
             "the ascent is well under way, at the re-implementation's speed")
assert_state("g112-assert-dj-x", "PlayerX", "eq", DJ_AFTER3[0], "and the horizontal position agrees")
assert_state("g113-assert-dj-air-0", "AirJumps", "eq", DJ_AFTER3[4], "no mid-air jump used yet")
hook("g114-dj-air", "Jump()", "the optional SECOND, mid-air jump")
assert_state("g115-assert-dj-air-1", "AirJumps", "eq", DJ_AFTER_AIR[1], "one mid-air jump used")
assert_state("g116-assert-dj-jumps-2", "Jumps", "eq", DJ_AFTER_AIR[2], "two jumps on the record")
assert_state("g117-assert-dj-vy-air", "VelY", "eq", DJ_AFTER_AIR[0],
             "the mid-air jump relaunches at its own, smaller speed")
hook("g118-dj-step1", "StepFrames(1)", "one frame of the second arc")
assert_state("g119-assert-dj-y", "PlayerY", "eq", DJ_AFTER_AIR1[1], "the re-implementation's height")
hook("g120-dj-third", "Jump()", "a third jump in the air is refused -- there is only one")
assert_state("g121-assert-dj-rejected", "JumpsRejected", "eq", DJ_AFTER_REFUSE[0],
             "the refusal is counted")
assert_state("g122-assert-dj-air-still-1", "AirJumps", "eq", DJ_AFTER_REFUSE[1],
             "and the air-jump count did not move")
assert_state("g123-assert-dj-vy-intact", "VelY", "eq", DJ_AFTER_REFUSE[3],
             "the refused jump left the speed alone")
# --- E2: the optional mid-air jump can be switched off -------------------------
force("g124-dj-off-setup", DJ_SPEC, "the same strip again")
hook("g125-dj-off", "SetDoubleJump(false)", "switch the optional second jump off")
hook("g126-dj-ground2", "Jump()", "the ground jump still works")
hook("g127-dj-step3b", "StepFrames(3)", "three frames")
hook("g128-dj-air-refused", "Jump()", "and now the mid-air jump is refused")
assert_state("g129-assert-dj-off-rejected", "JumpsRejected", "eq", DJ2_AFTER_REFUSE[0],
             "the refusal is counted")
assert_state("g130-assert-dj-off-air-0", "AirJumps", "eq", DJ2_AFTER_REFUSE[1],
             "and no mid-air jump happened")
assert_state("g131-assert-dj-off-y", "PlayerY", "eq", DJ2_AFTER3[1],
             "the arc is the same as the single-jump one")
hook("g132-dj-on-again", "SetDoubleJump(true)", "back on")
# --- F: the collectibles -------------------------------------------------------
force("g133-gem-setup", GEM_SPEC, "two collectibles on the flat strip, one run to the right")
hook("g134-run-right", "SetRun(1)", "hold right")
hook("g135-step-5", "StepFrames(5)", "five frames: the player's box reaches the first gem")
assert_state("g136-assert-collected-1", "Collected", "eq", GEM_AFTER5[1], "one gem taken")
assert_state("g137-assert-score-10", "Score", "eq", GEM_AFTER5[2], "ten points")
assert_state("g138-assert-left-1", "GemsRemaining", "eq", GEM_AFTER5[3], "one left")
assert_state("g139-assert-x-5", "PlayerX", "eq", GEM_AFTER5[0], "at the re-implementation's pixel")
hook("g140-step-5b", "StepFrames(5)", "five more frames: the second gem")
assert_state("g141-assert-collected-2", "Collected", "eq", GEM_AFTER10[1], "two gems taken")
assert_state("g142-assert-score-20", "Score", "eq", GEM_AFTER10[2], "twenty points")
assert_state("g143-assert-left-0", "GemsRemaining", "eq", GEM_AFTER10[3], "and none left")
assert_state("g144-assert-gem-hash", "MapHash", "eq", GEM_AFTER10[4],
             "the map hash moved to the re-implementation's post-collection value")
hook("g145-step-5c", "StepFrames(5)", "five more frames over the empty tiles")
assert_state("g146-assert-collected-still-2", "Collected", "eq", GEM_AFTER15[1],
             "a gem is only ever taken once")
assert_state("g147-assert-score-still-20", "Score", "eq", GEM_AFTER15[2], "so the score stands")
# --- G: the goal ---------------------------------------------------------------
force("g148-goal-setup", GOAL_SPEC, "the player two tiles short of the goal on the full course")
hook("g149-run-right", "SetRun(1)", "hold right")
hook("g150-step-5", "StepFrames(5)", "five frames: the box reaches the goal tile")
assert_state("g151-assert-won", "Won", "eq", GOAL_AT[1], "the goal tile ends the level in a win")
assert_state("g152-assert-over", "GameOver", "eq", GOAL_AT[2], "and the game is over")
assert_state("g153-assert-x-goal", "PlayerX", "eq", GOAL_AT[0], "at the re-implementation's pixel")
hook("g154-run-after-over", "SetRun(-1)", "a direction after the game is over is refused")
assert_state("g155-assert-reason-over", "LastEvent", "contains", "reason=game_over",
             "the refusal names the rule")
hook("g156-step-after-over", "StepFrames(3)", "and the frame hook applies nothing")
assert_state("g157-assert-hook-0", "LastHookSteps", "eq", 0,
             "the hook reports zero frames applied because the level is finished")
shot("g158-shot-t3", "plat-t3", "the goal frame: GOAL REACHED on the status label")
g("g159-assert-screen-win", "running_game_assert_screen_text", {"text": "GOAL REACHED"},
  "the status label really is on the captured screen")
# --- H: the pit -----------------------------------------------------------------
force("g160-pit-setup", PIT_SPEC, "the player standing over the first pit, with no input at all")
hook("g161-step-10", "StepFrames(10)", "ten frames of free fall: still above the map's bottom")
assert_state("g162-assert-pit-y", "PlayerY", "eq", PIT_BEFORE[1],
             "the fall is exactly the integer sum of 1+2+...+10 the re-implementation predicts")
assert_state("g163-assert-pit-lives", "Lives", "eq", PIT_BEFORE[2], "no life lost yet")
assert_state("g164-assert-pit-falls", "Falls", "eq", 0, "and no fall on the record")
hook("g165-step-11", "StepFrames(1)", "one more frame: the box is past the bottom")
assert_state("g166-assert-fell", "Falls", "eq", PIT_AFTER[3], "the fall is counted")
assert_state("g167-assert-pit-lives-2", "Lives", "eq", PIT_AFTER[2], "one life gone")
assert_state("g168-assert-respawn-x", "PlayerX", "eq", PIT_AFTER[0], "the player is back at the spawn")
assert_state("g169-assert-respawn-y", "PlayerY", "eq", PIT_AFTER[1], "in both axes")
assert_state("g170-assert-not-over", "GameOver", "eq", False, "two lives are left, so the game goes on")
force("g171-last-life", PIT_LAST_SPEC, "the same pit with a single life")
hook("g172-step-11", "StepFrames(11)", "fall again, with the last life")
assert_state("g173-assert-lives-0", "Lives", "eq", PIT_LAST_AFTER[0], "no life is left")
assert_state("g174-assert-over", "GameOver", "eq", PIT_LAST_AFTER[2], "and the game is over")
assert_state("g175-assert-not-won", "Won", "eq", PIT_LAST_AFTER[3], "a fall is not a win")
assert_state("g176-assert-falls", "Falls", "eq", PIT_LAST_AFTER[1], "one fall on the record")
shot("g177-shot-t4", "plat-t4", "the game-over frame: ALL LIVES LOST on the status label")
g("g178-assert-screen-over", "running_game_assert_screen_text", {"text": "ALL LIVES LOST"},
  "the status label really is on the captured screen")
# --- I: the frame-rate independent increment, and the clock ---------------------
force("g179-inc-setup", INC_SPEC, "the flat strip once more, for the increment test")
hook("g180-inc-run", "SetRun(1)", "hold right")
hook("g181-inc-step3", "StepFrames(3)", "exactly three fixed frames")
assert_state("g182-assert-inc-hook-3", "LastHookSteps", "eq", 3,
             "the DELTA of that call is exact -- this is the frame-rate independent quantity")
assert_state("g183-assert-inc-x", "PlayerX", "eq", INC_X, "and the position agrees with the re-implementation")
assert_state("g184-assert-inc-ground", "OnGround", "eq", INC_GROUND, "still on the ground")
assert_state("g185-assert-inc-auto-0", "LastAutoSteps", "eq", 0,
             "and it is a DIFFERENT property from the clock's own per-frame delta, which is 0 "
             "while the clock is off")
hook("g186-clock-on", "SetAutoClock(60.0)",
     "the one sample that watches the world move asks for motion explicitly")
assert_state("g187-assert-hook-intact", "LastHookSteps", "eq", 3,
             "the clock has been running for several frames and the hook's own delta is still "
             "exactly what the hook wrote -- two producers, two properties")
samples("g188-samples-clock",
        ["PlayerX", "PlayerY", "OnGround", "VelY", "Landings", "GemsRemaining", "AutoTicks",
         "LastAutoSteps", "Elapsed", "Ticks"], 30,
        "multi-frame property sample of the auto clock: the player runs right frame by frame "
        "(PlayerX changes every frame, Landings counts up) while Elapsed and Ticks advance -- "
        "'the game moves' as a sequence of values, not as an adjective")
assert_state("g189-assert-moved", "PlayerX", "gt", INC_X,
             "the clock really carried the player past the position the hook left them at")
assert_state("g190-assert-auto-ticks", "AutoTicks", "gt", 2,
             "and it kept stepping after the sample began")
assert_state("g191-assert-still-ground", "OnGround", "eq", True,
             "on the flat strip the run never leaves the ground")
hook("g192-clock-off", "SetAutoClock(0.0)", "back to frozen")
assert_state("g193-assert-auto-0-again", "LastAutoSteps", "eq", 0, "the per-frame delta is zero again")
assert_state("g194-assert-hook-intact-2", "LastHookSteps", "eq", 3,
             "while the hook's own delta is untouched by the clock, before or after it runs")
shot("g195-shot-t5", "plat-t5", "the frame after the clock carried the player east")
# --- J: the declared input path really drives the game --------------------------
force("g196-input-setup", INC_SPEC, "a flat strip for the input test")
hook("g197-poll-on", "SetPollInput(true)",
     "the input path is off by default; the test switches it on explicitly")
hook("g198-clock-on-input", "SetAutoClock(60.0)", "the world has to advance for the key to matter")
g("g199-input-right", "running_game_run_test_scenario",
  {"steps": [{"type": "input", "action": "plat_right", "pressed": True},
             {"type": "wait", "seconds": 0.45},
             {"type": "assert", "node_path": "Main", "property": "PlayerX",
              "operator": "gt", "expected": 100}]},
  "the declared action really runs the player east")
assert_state("g200-assert-input-moves-1", "InputMoves", "eq", 1,
             "the declared action fires on the PRESS EDGE, so a scenario's never-released key "
             "performs exactly one action instead of repeating at the frame rate")
assert_state("g201-assert-player-moved", "PlayerX", "gt", 100,
             "and the player is east of where the strip pinned them")
g("g202-input-jump", "running_game_run_test_scenario",
  {"steps": [{"type": "input", "action": "plat_jump", "pressed": True},
             {"type": "wait", "seconds": 0.45},
             {"type": "assert", "node_path": "Main", "property": "Jumps",
              "operator": "gte", "expected": 1}]},
  "the declared jump action really launches the player")
assert_state("g203-assert-input-jumps-1", "InputJumps", "eq", 1, "one jump arrived by input")
assert_state("g204-assert-jumps-1", "Jumps", "gte", 1, "and it is on the record")
hook("g205-poll-off", "SetPollInput(false)",
     "polling off again: nothing after this can drift because a key is still marked held")
hook("g206-clock-off-input", "SetAutoClock(0.0)", "and the world stops again")
# --- positive control: a node created at run time is drawn ----------------------
g("g207-runtime-overlay", "running_game_execute_gdscript",
  code('var main = get_parent()\nvar c = ColorRect.new()\nc.name = StringName("ProbeOverlay")\n'
       'c.position = Vector2(20, 556)\nc.size = Vector2(120, 30)\n'
       'c.color = Color(0.95, 0.35, 0.95, 1.0)\nmain.add_child(c)\nreturn "overlay added"'),
  "a node created at run time, in the same session, as the positive control for 'a run-time node "
  "is drawn'")
# --- DECLARED FAILURE: the error path of the assertion tool ---------------------
g("g208-assert-unknown-property", "running_game_assert_node_state",
  {"node_path": "Main", "property": "NoSuchProperty", "operator": "eq", "expected": 1},
  "DECLARED FAILURE: a boundary call asking for a property that does not exist (-32001), so the "
  "error path of the assertion tool is on the record too")
shot("g209-shot-t6", "plat-t6", "the overlay is visible in this frame and not in t5")
force("g210-final-level", spec_of("0"), "ask for the full course once more")
assert_state("g211-assert-gems", "GemsTotal", "eq", L0S.gems_total, "the course is back")
assert_state("g212-assert-hash", "MapHash", "eq", L0S.map_hash(),
             "and it reproduces the very same hash the Python re-implementation predicted")
hook("g213-final-readback", "Dump()", "the final map as one line")
g("g214-final-tree", "running_game_get_scene_tree", {},
  "the final tree, including the run-time overlay")

# =============================================================================
# write the level literals into the payload, then write the session
# =============================================================================
with io.open(PAYLOAD, "r", encoding="utf-8") as handle:
    source = handle.read()
before = source
source = source.replace('"@LEVEL0@"', '"%s"' % LEVEL0)
source = source.replace('"@LEVEL1@"', '"%s"' % LEVEL1)
if source != before:
    with io.open(PAYLOAD, "w", encoding="utf-8", newline="\n") as handle:
        handle.write(source)
    print("payload  : the two level literals were (re)written into %s" % PAYLOAD)
else:
    print("payload  : the two level literals were already in place")
for token in ('"@LEVEL0@"', '"@LEVEL1@"'):
    if token in source:
        raise SystemExit("FATAL: %s survived in the payload" % token)
if ('"%s"' % LEVEL0) not in source or ('"%s"' % LEVEL1) not in source:
    raise SystemExit("FATAL: the level literals are not in the payload")

doc = {"import": True, "calls": calls}
os.makedirs(os.path.dirname(OUT), exist_ok=True)
with io.open(OUT, "w", encoding="utf-8", newline="\n") as handle:
    handle.write(json.dumps(doc, ensure_ascii=False, indent=1) + "\n")

print("wrote %s calls=%d" % (OUT, len(calls)))
print("L0 map_hash=%d gems=%d spawn=%d,%d goal=%d,%d" % (
    L0S.map_hash(), L0S.gems_total, L0S.spawn_row, L0S.spawn_col, L0S.goal_row, L0S.goal_col))
print("L1 map_hash=%d" % L1S.map_hash())
print("DROP  x=%d y=%d ground=%s vy=%d landings=%d hash=%d" % (
    DROP_X, DROP_Y, DROP_GROUND, DROP_VY, DROP_LANDINGS, DROP.state_hash()))
print("WALL  x=%d wall_hits=%d vy=%d ground=%s" % (WALL.x, WALL.wall_hits, WALL.vy, WALL.on_ground))
print("ARC   launch=%s after=%s" % (ARC.kind, ARC.ARCAFTER))
for index, checkpoint in enumerate(ARC_CHECKPOINTS):
    print("      frame=%-3d x=%-4d y=%-4d vy=%-4d ground=%-5s landings=%d" % checkpoint)
print("DJ    after3=%s air=%s after_air=%s after1=%s refuse=%s kind3=%s" % (
    DJ_AFTER3, DJ.kind2, DJ_AFTER_AIR, DJ_AFTER_AIR1, DJ_AFTER_REFUSE, DJ.kind3))
print("DJ2   after3=%s refuse=%s kind2=%s" % (DJ2_AFTER3, DJ2_AFTER_REFUSE, DJ2.kind2))
print("GEM   after5=%s after10=%s after15=%s" % (GEM_AFTER5, GEM_AFTER10, GEM_AFTER15))
print("GOAL  at=%s frames_applied_after_over=%d" % (GOAL_AT, GOAL_AFTER_OVER))
print("PIT   before=%s after=%s last=%s" % (PIT_BEFORE, PIT_AFTER, PIT_LAST_AFTER))
print("INC   x=%d y=%d ground=%s" % (INC_X, INC_Y, INC_GROUND))
