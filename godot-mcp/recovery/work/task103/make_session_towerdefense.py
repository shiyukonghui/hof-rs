#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""TASK-103 (B, game 16): the Tower Defense session generator, with the Python
second implementation of the payload's rules.

The payload is `tools/sessions/towerdefense/payload/TowerDefenseGame.cs`. `TSim`
below re-implements its rules from the *rules* -- the ASCII map and the
deterministic path walk, the integer movement, the tower targeting and cooldown,
the spawn/wave machinery and the LCG-free (fully pinned) enemy list. Every
literal a `running_game_assert_node_state` compares against is produced by `TSim`
and by nothing else, so the session is a statement about the rules and not about
what the payload happened to print.

The session drives the game through MCP calls only: `project_edit_script` writes
the C# payload, `editor_add_nodes_batch` builds the three static nodes exactly
once (and is replayed once for the D-3 `-32000` refusal), `editor_add_input_action`
declares the one action the input scenario uses, and every rule assertion is a
`running_game_*` call on the running game.

Written by a Python writer, never by a shell redirect (iron rule 1).
"""

import io
import json
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.abspath(os.path.join(HERE, "..", "..", ".."))
SESSION_DIR = os.path.join(ROOT, "tools", "sessions", "towerdefense")
OUT = os.path.join(SESSION_DIR, "session.json")
PAYLOAD = "payload/TowerDefenseGame.cs"

MAP_ROWS = [
    "................",
    "S###############",
    "...............#",
    "################",
    "#...............",
    "################",
    "...............#",
    "################",
    "#...............",
    "################",
    "...............#",
    "E###############",
]
COLS = 16
ROWS = 12
TILE = 50
RANGE = 3
COST = 50
DAMAGE = 10
COOLDOWN = 3
BOUNTY = 10
WAVE_COUNTS = [4, 5, 6]
WAVE_HPS = [30, 45, 60]
WAVE_SPEEDS = [5, 4, 4]
WAVE_INTERVALS = [10, 10, 8]


def div_floor(a, b):
    """Python's `//` floors; the payload spells the same floor out in C#."""
    return a // b


def build_path():
    start = None
    for row in range(ROWS):
        for col in range(COLS):
            if MAP_ROWS[row][col] == 'S':
                start = (col, row)
    if start is None:
        raise SystemExit("no spawn cell")
    order = [(1, 0), (0, 1), (-1, 0), (0, -1)]
    col, row = start
    previous = (-1, -1)
    path = []
    for _ in range(COLS * ROWS):
        path.append((col, row))
        if MAP_ROWS[row][col] == 'E':
            break
        moved = False
        for dc, dr in order:
            nc, nr = col + dc, row + dr
            if not (0 <= nc < COLS and 0 <= nr < ROWS):
                continue
            if (nc, nr) == previous:
                continue
            if MAP_ROWS[nr][nc] not in '#SE':
                continue
            previous = (col, row)
            col, row = nc, nr
            moved = True
            break
        if not moved:
            break
    return path


def map_string():
    return "/".join(MAP_ROWS)


def map_hash():
    value = 0
    for row in MAP_ROWS:
        for ch in row:
            weight = 1 if ch == '#' else 4 if ch == 'S' else 5 if ch == 'E' else 2
            value = sign32(value * 31 + weight)
    return value


def path_hash(path):
    value = 0
    for col, row in path:
        value = sign32(value * 31 + row * COLS + col)
    return value


def sign32(value):
    value &= 0xFFFFFFFF
    return value - 0x100000000 if value >= 0x80000000 else value


PATH = build_path()
CELL_INDEX = {cell: index for index, cell in enumerate(PATH)}


class TSim(object):
    """The payload's rules, re-implemented from the rules."""

    def __init__(self):
        self.reset()

    def reset(self):
        self.gold = 100
        self.lives = 5
        self.wave = 1
        self.wave_max = len(WAVE_COUNTS)
        self.wave_left = WAVE_COUNTS[0]
        self.countdown = 0
        self.spawned = 0
        self.killed = 0
        self.leaked = 0
        self.score = 0
        self.steps = 0
        self.won = False
        self.over = False
        # each enemy: [hp, path_index, accum, speed]
        self.enemies = []
        # each tower: [col, row, cooldown]
        self.towers = []
        self.placed = 0

    def buildable(self, col, row):
        if not (0 <= col < COLS and 0 <= row < ROWS):
            return False
        return MAP_ROWS[row][col] == '.'

    def place(self, col, row):
        if self.over:
            return "rejected reason=game_over at=%d,%d" % (col, row)
        if not (0 <= col < COLS and 0 <= row < ROWS):
            return "rejected reason=out_of_bounds at=%d,%d" % (col, row)
        if MAP_ROWS[row][col] != '.':
            return "rejected reason=not_buildable at=%d,%d" % (col, row)
        if any(t[0] == col and t[1] == row for t in self.towers):
            return "rejected reason=occupied at=%d,%d" % (col, row)
        if self.gold < COST:
            return "rejected reason=no_gold at=%d,%d gold=%d cost=%d" % (col, row, self.gold, COST)
        self.gold -= COST
        self.towers.append([col, row, 0])
        self.placed += 1
        return "tower placed at=%d,%d towers=%d gold=%d" % (col, row, self.placed, self.gold)

    def force(self, gold=None, lives=None, wave=None, left=None, countdown=None,
              maxwave=None, score=None, towers=None, enemies=None):
        self.reset()
        if gold is not None:
            self.gold = gold
        if lives is not None:
            self.lives = lives
        if score is not None:
            self.score = score
        if maxwave is not None:
            self.wave_max = maxwave
        if wave is not None:
            self.wave = wave
        self.wave_left = left if left is not None else WAVE_COUNTS[self.wave - 1]
        self.countdown = countdown if countdown is not None else 0
        if towers:
            for col, row in towers:
                self.towers.append([col, row, 0])
            self.placed = len(self.towers)
        if enemies:
            for hp, path_index, accum, speed in enemies:
                self.enemies.append([hp, path_index, accum, speed])
            self.spawned = len(self.enemies)

    def tick(self):
        if self.over:
            return
        self.steps += 1
        # 1. spawn
        if self.wave_left > 0:
            if self.countdown <= 0:
                self.enemies.append([WAVE_HPS[self.wave - 1], 0, 0, WAVE_SPEEDS[self.wave - 1]])
                self.spawned += 1
                self.wave_left -= 1
                self.countdown = WAVE_INTERVALS[self.wave - 1]
            else:
                self.countdown -= 1
        # 2. move
        for enemy in self.enemies:
            enemy[2] += 1
            if enemy[2] >= enemy[3]:
                enemy[2] = 0
                enemy[1] += 1
        # 3. leak (reverse order, order preserved on removal)
        for index in range(len(self.enemies) - 1, -1, -1):
            if self.enemies[index][1] >= len(PATH) - 1:
                del self.enemies[index]
                self.leaked += 1
                self.lives -= 1
        if self.lives <= 0:
            self.lives = 0
            self.over = True
            self.won = False
            return
        # 4. towers fire
        for tower in self.towers:
            if tower[2] > 0:
                tower[2] -= 1
                continue
            best = -1
            best_path = -1
            for index, enemy in enumerate(self.enemies):
                if enemy[1] >= len(PATH):
                    continue
                col, row = PATH[enemy[1]]
                distance = max(abs(col - tower[0]), abs(row - tower[1]))
                if distance > RANGE:
                    continue
                if enemy[1] > best_path:
                    best_path = enemy[1]
                    best = index
            if best < 0:
                continue
            tower[2] = COOLDOWN
            self.enemies[best][0] -= DAMAGE
            if self.enemies[best][0] <= 0:
                del self.enemies[best]
                self.killed += 1
                self.score += BOUNTY
                self.gold += BOUNTY
        # 5. wave transition / win
        if self.wave_left == 0 and not self.enemies:
            if self.wave >= self.wave_max:
                self.won = True
                self.over = True
                return
            self.wave += 1
            self.wave_left = WAVE_COUNTS[self.wave - 1]
            self.countdown = 0

    def step(self, count):
        applied = 0
        for _ in range(count):
            if self.over:
                break
            self.tick()
            applied += 1
        return applied

    def enemy_list(self):
        return "|".join("%d,%d,%d,%d" % (e[0], e[1], e[2], e[3]) for e in self.enemies)

    def tower_list(self):
        return "|".join("%d,%d" % (t[0], t[1]) for t in self.towers)


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


def force(spec, label=""):
    return 'var g = get_parent()\nreturn g.ForceTestState("%s")' % spec


def invoke(expression):
    return "var g = get_parent()\nreturn g.%s" % expression


def editor_phase():
    nodes = [
        {"type": "ColorRect", "name": "Background", "parent_path": ".",
         "properties": {"offset_left": 0, "offset_top": 0, "offset_right": 800, "offset_bottom": 600,
                        "color": {"r": 0.04, "g": 0.05, "b": 0.07, "a": 1}}},
        {"type": "Label", "name": "Hud", "parent_path": ".",
         "properties": {"offset_left": 14, "offset_top": 10, "offset_right": 780, "offset_bottom": 44,
                        "text": "WAVE 1/3  LIVES 5  GOLD 100  ALIVE 0  KILLED 0  LEAK 0  STEP 0",
                        "theme_override_font_sizes/font_size": 20}},
        {"type": "Label", "name": "Status", "parent_path": ".",
         "properties": {"offset_left": 14, "offset_top": 560, "offset_right": 640, "offset_bottom": 594,
                        "text": "DEFEND THE PATH", "theme_override_font_sizes/font_size": 22}},
    ]
    call("e01-edit-game", "editor", "project_edit_script",
         {"path": "res://src/TowerDefenseGame.cs", "content_file": PAYLOAD},
         "the whole game is written through the MCP script writer (the template stub is replaced)")
    call("e02-open-scene", "editor", "editor_open_scene", {"path": "res://scenes/main.tscn"},
         "the template scene carries the root Main (Node2D) the script is attached to")
    call("e03-batch-add-static", "editor", "editor_add_nodes_batch", {"nodes": nodes},
         "the three static nodes of the scene, through the batch tool: a background and two labels; every path tile, tower and enemy is created at run time")
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
    call("e10-action-step", "editor", "editor_add_input_action", {"action": "td_auto_step", "key": "Space"},
         "one deterministic simulation step, for the input-edge scenario")
    call("e11-save-3", "editor", "editor_save_scene", {}, "persist the declared action")
    call("e12-build-csharp", "editor", "project_build_csharp", {},
         "the payload really compiles: the real dotnet exit code")
    call("e13-validate-scripts", "editor", "project_validate_scripts", {},
         "per-file verdicts for every script in the project")
    call("e14-get-errors", "editor", "editor_get_errors", {},
         "the editor's own error list after the build")


def game_phase():
    # --- g01..g10: the shape of the world, and the first frame -----------------
    call("g01-scene-tree", "game", "running_game_get_scene_tree", {},
         "the running game's tree: three static nodes, no @-auto names")
    sim0 = TSim()
    assert_ok("g02-assert-cols", "Cols", COLS, "the grid is sixteen columns wide")
    assert_ok("g03-assert-rows", "Rows", ROWS, "and twelve rows tall")
    assert_ok("g04-assert-tile", "Tile", TILE, "one cell is fifty pixels")
    assert_ok("g05-assert-path-length", "PathLength", len(PATH),
              "the derived path has exactly %d cells (independently walked in Python)" % len(PATH))
    assert_ok("g06-assert-map-hash", "MapHash", map_hash(),
              "the map hash, recomputed in Python from the same printed ASCII grid")
    assert_ok("g07-assert-path-hash", "PathHash", path_hash(PATH),
              "the hash of the ordered path, recomputed in Python by the same walk")
    assert_ok("g08-assert-wave-max", "WaveMax", len(WAVE_COUNTS), "three waves make a full game")
    assert_ok("g09-assert-gold-start", "Gold", sim0.gold, "a fresh game starts with %d gold" % sim0.gold)
    assert_ok("g10-assert-lives-start", "Lives", sim0.lives, "and %d lives" % sim0.lives)
    exec_code("g11-readback-t0", invoke("Dump()"),
              "the whole state on one line: the map, the path facts and every counter")
    shot("g12-shot-t0", "td-t0", "the first frame: the generated path on an empty field")

    # --- the frozen baseline: nothing moves while the clock is off -------------
    samples("g13-samples-frozen", ["Steps", "EnemiesAlive", "Gold", "Lives", "Won", "Elapsed", "Ticks"], 12,
            "determinism baseline: AutoClock is 0, so the simulation facts are constant while Elapsed and Ticks both advance")
    assert_ok("g14-assert-frozen-steps", "Steps", 0, "with the clock off and no hook called, not one simulation step has run")
    assert_ok("g15-assert-frozen-auto", "LastAutoSteps", 0, "and the auto clock applied nothing")
    assert_ok("g16-assert-frozen-hook", "LastHookSteps", 0, "and the hook applied nothing either")

    # --- the path walk, cell by cell -------------------------------------------
    for tag, col, row in (("g17", 0, 1), ("g18", 15, 1), ("g19", 0, 11), ("g20", 3, 5)):
        index = CELL_INDEX[(col, row)]
        exec_code("%s-probe-%d-%d" % (tag, col, row), invoke("ProbeCell(%d, %d)" % (col, row)),
                  "the probe names what stands on one cell, so the assertion below is about that cell")
        assert_ok("%sa-assert-probe-value" % tag, "ProbeValue", index,
                  "cell (%d,%d) is path index %d (Python walked the same map)" % (col, row, index))
    exec_code("g21-probe-ground", invoke("ProbeCell(3, 0)"), "a buildable cell next to the first straight run")
    assert_ok("g21a-assert-probe-value", "ProbeValue", -1, "ground is not on the path")
    assert_ok("g21b-assert-probe-state", "ProbeState", "ground", "and the probe says so")
    exec_code("g22-probe-spawn", invoke("ProbeCell(0, 1)"), "the spawn cell itself")
    assert_ok("g22a-assert-probe-state", "ProbeState", "spawn", "the walk starts here")
    exec_code("g23-probe-exit", invoke("ProbeCell(0, 11)"), "the exit cell itself")
    assert_ok("g23a-assert-probe-state", "ProbeState", "exit", "and ends here")
    exec_code("g24-probe-outside", invoke("ProbeCell(99, 99)"), "outside the grid")
    assert_ok("g24a-assert-probe-state", "ProbeState", "outside", "a point outside is named as such")

    # --- placing towers: every refusal is a named reason -----------------------
    exec_code("g25-place-setup", force("gold=100;lives=5;wave=1;maxwave=3;left=0"),
              "a pinned state with exactly 100 gold and no wave to spawn")
    assert_ok("g25a-assert-gold-pinned", "Gold", 100, "the pinned gold")
    exec_code("g26-place-first", invoke("PlaceTower(0, 0)"), "one tower above the first straight run")
    assert_ok("g26a-assert-gold-after-first", "Gold", 100 - COST, "the tower cost %d gold" % COST)
    assert_ok("g26b-assert-towers-placed", "TowersPlaced", 1, "and it is the first tower")
    assert_ok("g26c-assert-tower-list", "TowerList", "0,0", "the tower list names it")
    exec_code("g27-place-second", invoke("PlaceTower(15, 4)"), "a second tower on the other side")
    assert_ok("g27a-assert-gold-after-second", "Gold", 100 - 2 * COST, "two towers cost twice")
    assert_ok("g27b-assert-tower-list-2", "TowerList", "0,0|15,4", "in build order")
    exec_code("g28-place-occupied", invoke("PlaceTower(0, 0)"), "the same cell again")
    assert_ok("g28a-assert-placed-still", "TowersPlaced", 2, "a refused placement adds no tower")
    exec_code("g29-place-on-path", invoke("PlaceTower(1, 1)"), "a path cell")
    exec_code("g30-place-outside", invoke("PlaceTower(99, 99)"), "a cell outside the grid")
    exec_code("g31-place-no-gold", invoke("PlaceTower(1, 0)"), "ground, but the pinned gold is spent")
    assert_ok("g31a-assert-gold-still", "Gold", 0, "a refused placement costs nothing")

    # --- one tower shot, one step at a time ------------------------------------
    damage = TSim()
    damage.force(gold=0, lives=5, wave=1, maxwave=3, left=5, towers=[(0, 0)],
                 enemies=[(30, 1, 0, 5)])
    exec_code("g32-damage-setup",
              force("gold=0;lives=5;wave=1;maxwave=3;left=5;towers=0,0;enemies=30,1,0,5"),
              "an enemy pinned one cell into the path, in range of a tower at (0,0)")
    assert_ok("g32a-assert-enemy-list", "EnemyList", damage.enemy_list(),
              "the pinned enemy list, exactly as forced")
    damage.step(1)
    exec_code("g33-damage-step-1", invoke("StepFrames(1)"),
              "one step: the enemy accumulates one move tick and the tower fires")
    assert_ok("g33a-assert-enemy-after-1", "EnemyList", damage.enemy_list(),
              "Python: %d hit points left, still on path index %d" % (damage.enemies[0][0], damage.enemies[0][1]))
    assert_ok("g33b-assert-alive-after-1", "EnemiesAlive", len(damage.enemies), "one enemy is alive")
    assert_ok("g33c-assert-killed-after-1", "EnemiesKilled", damage.killed, "nothing died yet")
    damage.step(4)
    exec_code("g34-damage-step-4", invoke("StepFrames(4)"),
              "four more steps: the enemy moves to path index 2 and the tower fires twice more (cooldown %d)" % COOLDOWN)
    assert_ok("g34a-assert-enemy-after-5", "EnemyList", damage.enemy_list(),
              "Python: %s" % damage.enemy_list())
    assert_ok("g34b-assert-steps-after-5", "Steps", damage.steps, "five steps ran")
    assert_ok("g34c-assert-hook-after-4", "LastHookSteps", 4,
              "the hook's OWN property is what it applied: the frame-rate independent delta")

    # --- a kill is worth its bounty --------------------------------------------
    kill = TSim()
    kill.force(gold=0, lives=5, wave=1, maxwave=3, left=5, towers=[(0, 0)], enemies=[(10, 1, 0, 5)])
    exec_code("g35-kill-setup", force("gold=0;lives=5;wave=1;maxwave=3;left=5;towers=0,0;enemies=10,1,0,5"),
              "an enemy with exactly one shot of hit points left")
    kill.step(1)
    exec_code("g36-kill-step", invoke("StepFrames(1)"), "one step: the tower's shot kills it")
    assert_ok("g36a-assert-alive", "EnemiesAlive", len(kill.enemies),
              "the pinned enemy died, and the one that spawned this step is the only survivor")
    assert_ok("g36b-assert-killed", "EnemiesKilled", kill.killed, "one kill")
    assert_ok("g36c-assert-score", "Score", kill.score, "the kill is worth %d points" % BOUNTY)
    assert_ok("g36d-assert-gold", "Gold", kill.gold, "and hands back %d gold as bounty" % BOUNTY)
    assert_ok("g36e-assert-enemy-list", "EnemyList", kill.enemy_list(),
              "the enemy list is exactly what Python says: %s" % kill.enemy_list())

    # --- the leak, and the life it costs ---------------------------------------
    leak = TSim()
    leak.force(gold=0, lives=5, wave=1, maxwave=3, left=0, enemies=[(30, len(PATH) - 2, 0, 1)])
    exec_code("g37-leak-setup",
              force("gold=0;lives=5;wave=1;maxwave=3;left=0;enemies=30,%d,0,1" % (len(PATH) - 2)),
              "an enemy one step from the exit, with no tower in range")
    leak.step(1)
    exec_code("g38-leak-step", invoke("StepFrames(1)"), "one step: it steps onto the exit")
    assert_ok("g38a-assert-leaked", "EnemiesLeaked", leak.leaked, "one enemy reached the exit")
    assert_ok("g38b-assert-lives", "Lives", leak.lives, "and that costs exactly one life")
    assert_ok("g38c-assert-alive", "EnemiesAlive", len(leak.enemies), "the path is empty again")
    assert_ok("g38d-assert-wave", "Wave", leak.wave,
              "with the wave spawned out and nothing alive, the next wave starts (Python: wave %d)" % leak.wave)
    assert_ok("g38e-assert-wave-left", "WaveLeftToSpawn", leak.wave_left,
              "and it has all %d of its enemies still to spawn" % leak.wave_left)

    # --- losing ------------------------------------------------------------------
    lose = TSim()
    lose.force(gold=0, lives=1, wave=1, maxwave=3, left=0, enemies=[(30, len(PATH) - 2, 0, 1)])
    exec_code("g39-lose-setup",
              force("gold=0;lives=1;wave=1;maxwave=3;left=0;enemies=30,%d,0,1" % (len(PATH) - 2)),
              "the last life, and an enemy one step from the exit")
    lose_applied = lose.step(3)
    exec_code("g40-lose-step", invoke("StepFrames(3)"), "three steps: it arrives, the life is gone")
    assert_ok("g40a-assert-lives-zero", "Lives", lose.lives, "no lives left")
    assert_ok("g40b-assert-over", "GameOver", lose.over, "so the game is over")
    assert_ok("g40c-assert-not-won", "Won", lose.won, "and it was not won")
    assert_ok("g40d-assert-hook-applied", "LastHookSteps", lose_applied,
              "the hook stopped at the end of the game: %d of the three steps ran" % lose_applied)
    exec_code("g41-place-after-lose", invoke("PlaceTower(3, 0)"), "a placement after the game ended")
    assert_ok("g41a-assert-placed", "TowersPlaced", lose.placed, "refused: no tower was added")
    shot("g42-shot-lost", "td-t1", "the lost game: the status label and the empty path")

    # --- the input edge ----------------------------------------------------------
    edge = TSim()
    edge.force(gold=0, lives=5, wave=1, maxwave=3, left=5)
    exec_code("g43-input-setup", force("gold=0;lives=5;wave=1;maxwave=3;left=5"),
              "a pinned state for the declared-input scenario")
    exec_code("g44-poll-on", invoke("SetPollInput(true)"), "start listening to the declared action")
    call("g45-input-step", "game", "running_game_run_test_scenario",
         {"steps": [{"type": "input", "action": "td_auto_step", "pressed": True},
                    {"type": "wait", "seconds": 0.45},
                    {"type": "assert", "node_path": "Main", "property": "Steps", "operator": "gte",
                     "expected": 1}]},
         "the declared action really advances the simulation (a press edge, so exactly one step)")
    edge.step(1)
    assert_ok("g46-assert-input-steps", "InputSteps", 1, "the edge performed exactly one step")
    assert_ok("g47-assert-steps", "Steps", edge.steps, "and the simulation really moved")
    exec_code("g48-poll-off", invoke("SetPollInput(false)"), "stop listening again, so the rest of the session is deterministic")

    # --- a full game, cleared by three towers ------------------------------------
    play = TSim()
    play.force(gold=1000, lives=5, wave=1, maxwave=3)
    exec_code("g49-play-setup", force("gold=1000;lives=5;wave=1;maxwave=3"),
              "a pinned, well-funded state: the whole game will be played from here by three towers")
    for tag, col, row in (("g50", 0, 0), ("g51", 15, 4), ("g52", 1, 8)):
        exec_code("%s-place" % tag, invoke("PlaceTower(%d, %d)" % (col, row)),
                  "build the tower the Python second implementation also builds")
        play.place(col, row)
    assert_ok("g53-assert-towers", "TowersPlaced", play.placed, "three towers stand")
    assert_ok("g53a-assert-gold", "Gold", play.gold, "and the gold says so (%d left)" % play.gold)
    applied = play.step(4000)
    exec_code("g54-play-to-end", invoke("StepFrames(4000)"),
              "let the whole game run through the same rules Python runs, to its end")
    assert_ok("g55-assert-won", "Won", play.won, "Python says this board is cleared: Won must be true")
    assert_ok("g56-assert-over", "GameOver", play.over, "and the game ended")
    assert_ok("g57-assert-killed", "EnemiesKilled", play.killed,
              "Python killed %d enemies (all %d that spawned)" % (play.killed, play.spawned))
    assert_ok("g58-assert-leaked", "EnemiesLeaked", play.leaked, "and leaked %d" % play.leaked)
    assert_ok("g59-assert-lives", "Lives", play.lives, "%d lives left" % play.lives)
    assert_ok("g60-assert-steps", "Steps", play.steps, "the game took exactly %d steps" % play.steps)
    assert_ok("g61-assert-score", "Score", play.score, "score %d" % play.score)
    assert_ok("g62-assert-hook-applied", "LastHookSteps", applied,
              "the hook stopped at the end of the game: %d of the 4000 steps ran" % applied)
    assert_ok("g63-assert-wave", "Wave", play.wave, "the last wave reached")
    shot("g64-shot-won", "td-t2", "the cleared course: the status label and the towers")
    call("g65-assert-screen-win", "game", "running_game_assert_screen_text", {"text": "PATH HELD"},
         "the status label really is on the captured screen")

    # --- the clock: multi-frame sampling with a must-move assertion -------------
    clock = TSim()
    clock.force(gold=1000, lives=5, wave=1, maxwave=3)
    for col, row in ((0, 0), (15, 4), (1, 8)):
        clock.place(col, row)
    exec_code("g66-clock-setup", force("gold=1000;lives=5;wave=1;maxwave=3"),
              "a fresh, playable state for the clock to move")
    exec_code("g67-clock-towers", invoke('PlaceTower(0, 0)'), "tower 1")
    clock.place(0, 0)
    exec_code("g68-clock-towers-2", invoke('PlaceTower(15, 4)'), "tower 2")
    clock.place(15, 4)
    exec_code("g69-clock-towers-3", invoke('PlaceTower(1, 8)'), "tower 3")
    clock.place(1, 8)
    assert_ok("g70-assert-clock-steps-0", "Steps", 0, "the clock is off, so nothing has moved yet")
    assert_ok("g71-assert-clock-hash-0", "TowerList", clock.tower_list(), "the three towers, pinned")
    exec_code("g72-clock-on", invoke("SetAutoClock(60.0)"),
              "the clock ticks 60 times a second (a float accumulator, F-1's fix)")
    samples("g73-samples-clock", ["Steps", "EnemiesSpawned", "EnemiesAlive", "Score", "Won", "Elapsed", "Ticks"],
            30,
            "thirty frames with the clock running: the simulation facts, the spawn counter, Elapsed and Ticks")
    assert_state("g74-assert-clock-moved", "Steps", "gt", 0,
                 "MUST MOVE: if the clock is frozen this assertion FAILS (the M3-4 lesson)")
    assert_state("g75-assert-clock-spawned", "EnemiesSpawned", "gt", 0,
                 "MUST SPAWN: a live clock has to put enemies on the path")
    assert_state("g76-assert-clock-auto-ticks", "AutoTicks", "gte", 1, "the clock applied at least one step")
    exec_code("g77-clock-off", invoke("SetAutoClock(0.0)"), "stop the clock")
    assert_ok("g78-assert-clock-off-auto", "LastAutoSteps", 0, "with the clock off the frame contributes nothing")
    shot("g79-shot-clock", "td-t3", "the field after the clock ran")

    # --- the two producers, two properties --------------------------------------
    hook = TSim()
    hook.force(gold=0, lives=5, wave=1, maxwave=3, left=5, towers=[(0, 0)], enemies=[(30, 1, 0, 5)])
    exec_code("g80-hook-setup", force("gold=0;lives=5;wave=1;maxwave=3;left=5;towers=0,0;enemies=30,1,0,5"),
              "a pinned state again")
    hook.step(3)
    exec_code("g81-hook-step-3", invoke("StepFrames(3)"), "three hook steps")
    assert_ok("g82-assert-hook-3", "LastHookSteps", 3, "the hook's own property")
    samples("g83-samples-quiet", ["Steps", "EnemyList", "Elapsed", "Ticks"], 12,
            "the clock is off, so the frame loop advances Elapsed and Ticks and nothing else")
    assert_ok("g84-assert-hook-still-3", "LastHookSteps", 3,
              "after twelve frames the hook's property is STILL 3: the clock never writes it (the G1 lesson)")
    assert_ok("g85-assert-auto-0", "LastAutoSteps", 0, "while the clock's own property is 0")
    assert_ok("g86-assert-still-no-auto", "AutoTicks", 0, "and it applied nothing at all")
    assert_ok("g87-assert-steps-still", "Steps", hook.steps, "the simulation did not move on its own")

    # --- the final readback, the scene tree, and one declared boundary ----------
    exec_code("g88-final-readback", invoke("Dump()"),
              "the final state on one line: every counter this session asserted")
    shot("g89-shot-final", "td-t4", "the final frame")
    call("g90-final-tree", "game", "running_game_get_scene_tree", {},
         "the final tree: every node name is one this game made, no @-auto names")
    assert_state("g91-assert-boundary", "NoSuchPropertyAtAll", "eq", 0,
                 "the declared boundary failure: an assertion on a property that does not exist (-32001)")


def main():
    editor_phase()
    game_phase()
    session = {"import": True, "calls": CALLS}
    with io.open(OUT, "w", encoding="utf-8", newline="\n") as handle:
        json.dump(session, handle, ensure_ascii=False, indent=1)
        handle.write("\n")
    # The tag -> expected manifest: what every assertion was asked to compare. The
    # post-hoc recomputation (`recompute_readbacks.py`) aligns this against the
    # `actual` every call really reported, so "the literal came from the Python
    # second implementation" is checkable and not a claim.
    manifest = []
    for entry in CALLS:
        if entry.get("tool") != "running_game_assert_node_state":
            continue
        args = entry["arguments"]
        manifest.append({"tag": entry["tag"], "property": args["property"],
                         "operator": args["operator"], "expected": args["expected"],
                         "declared_boundary": args["property"].startswith("NoSuchProperty")})
    manifest_path = os.path.join(HERE, "expectations-towerdefense.json")
    with io.open(manifest_path, "w", encoding="utf-8", newline="\n") as handle:
        json.dump(manifest, handle, ensure_ascii=False, indent=1)
        handle.write("\n")
    editor = len([c for c in CALLS if c["port"] == "editor"])
    game = len([c for c in CALLS if c["port"] == "game"])
    print("wrote %s" % OUT)
    print("calls: %d (editor %d / game %d)" % (len(CALLS), editor, game))
    print("expectations: %d -> %s" % (len(manifest), manifest_path))
    print("path length: %d  map hash: %d  path hash: %d" % (len(PATH), map_hash(), path_hash(PATH)))
    # The two facts the session's own verdicts rest on, printed so the generator
    # cannot be the only place they are known.
    play = TSim()
    play.force(gold=1000, lives=5, wave=1, maxwave=3)
    for col, row in ((0, 0), (15, 4), (1, 8)):
        play.place(col, row)
    applied = play.step(4000)
    print("full game: won=%s over=%s steps=%d applied=%d killed=%d leaked=%d lives=%d score=%d wave=%d"
          % (play.won, play.over, play.steps, applied, play.killed, play.leaked, play.lives, play.score, play.wave))
    if not play.won:
        print("WARNING: the pinned full-game configuration does not win")
    # Round-trip so a malformed file can never be handed to the driver.
    with io.open(OUT, "r", encoding="utf-8") as handle:
        again = json.load(handle)
    assert len(again["calls"]) == len(CALLS)
    print("json round-trip: OK (%d calls)" % len(again["calls"]))
    return 0


if __name__ == "__main__":
    sys.exit(main())
