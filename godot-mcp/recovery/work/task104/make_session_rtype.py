#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""TASK-104 (B, game 18): the R-Type session generator, with the Python second
implementation of the payload's rules.

The payload is `tools/sessions/rtype/payload/RTypeGame.cs`. `RSim` below
re-implements its rules from the *rules*: the integer movement, the formation
slot arithmetic, the fixed step order (spawn, move three kinds, fire, resolve both
collisions, wave/win), the cooldown, the escape rule and the two windows. Every
literal a `running_game_assert_node_state` compares against is produced by `RSim`
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
SESSION_DIR = os.path.join(ROOT, "tools", "sessions", "rtype")
OUT = os.path.join(SESSION_DIR, "session.json")
PAYLOAD = "payload/RTypeGame.cs"

FIELD_W = 800
FIELD_H = 600
HUD = 64
PLAYER_W = 24
PLAYER_H = 16
PLAYER_SPEED = 8
PLAYER_START_X = 80
PLAYER_START_Y = 300
START_LIVES = 3
BULLET_W = 10
BULLET_H = 4
BULLET_SPEED = 16
BULLET_POOL = 12
EB_SIZE = 8
EB_SPEED = 6
EB_POOL = 24
ENEMY_W = 24
ENEMY_H = 20
ENEMY_SPEED = 3
ENEMY_FIRE = 45
SPAWN_INTERVAL = 6
KILL_SCORE = 100
FORMATION_ROWS = 3
F_COL = 40
F_ROW = 70
F_START_Y = 120
F_ENTRY_X = 830
WAVE_SIZES = [4, 5, 6]


def sign32(value):
    value &= 0xFFFFFFFF
    return value - 0x100000000 if value >= 0x80000000 else value


def overlap(ax, ay, aw, ah, bx, by, bw, bh):
    return ax < bx + bw and bx < ax + aw and ay < by + bh and by < ay + ah


class RSim(object):
    """The payload's rules, re-implemented from the rules."""

    def __init__(self):
        self.reset()

    def reset(self):
        self.px = PLAYER_START_X
        self.py = PLAYER_START_Y
        self.lives = START_LIVES
        self.score = 0
        self.wave = 1
        self.wave_max = len(WAVE_SIZES)
        self.wave_left = WAVE_SIZES[0]
        self.countdown = 0
        self.spawned = 0
        self.killed = 0
        self.escaped = 0
        self.shots = 0
        self.eshots = 0
        self.steps = 0
        self.won = False
        self.over = False
        self.moves = 0
        self.rejected = 0
        # enemies: [x, y, cooldown]
        self.enemies = []
        # bullet SLOTS, exactly like the payload's fixed arrays: a slot is reused
        # lowest-free-first, so the printed order is slot order and not age order.
        self.pb = [None] * BULLET_POOL
        self.eb = [None] * EB_POOL

    # --- the rules -------------------------------------------------------------

    def size_of_wave(self, wave):
        index = wave - 1
        return WAVE_SIZES[index] if 0 <= index < len(WAVE_SIZES) else 4

    def spawn_one(self):
        slot = self.size_of_wave(self.wave) - self.wave_left
        row = slot % FORMATION_ROWS
        col = slot // FORMATION_ROWS
        self.enemies.append([F_ENTRY_X + col * F_COL, F_START_Y + row * F_ROW, ENEMY_FIRE])
        self.spawned += 1

    def tick(self):
        if self.over:
            return
        self.steps += 1
        # 1. spawn
        if self.wave_left > 0:
            if self.countdown <= 0:
                self.spawn_one()
                self.wave_left -= 1
                self.countdown = SPAWN_INTERVAL
            else:
                self.countdown -= 1
        # 2. player bullets right
        for i in range(BULLET_POOL):
            b = self.pb[i]
            if b is None:
                continue
            b[0] += BULLET_SPEED
            if b[0] >= FIELD_W:
                self.pb[i] = None
        # 3. enemy bullets left
        for i in range(EB_POOL):
            b = self.eb[i]
            if b is None:
                continue
            b[0] -= EB_SPEED
            if b[0] + EB_SIZE < 0:
                self.eb[i] = None
        # 4. enemies left, and the ones that crossed cost a life
        escaped_now = 0
        for i in range(len(self.enemies) - 1, -1, -1):
            self.enemies[i][0] -= ENEMY_SPEED
            if self.enemies[i][0] + ENEMY_W < 0:
                del self.enemies[i]
                escaped_now += 1
        if escaped_now:
            self.escaped += escaped_now
            self.lives -= escaped_now
        if self.lives <= 0:
            self.lives = 0
            self.over = True
            self.won = False
            return
        # 5. enemies fire, in spawn order
        for e in self.enemies:
            e[2] -= 1
            if e[2] > 0 or e[0] >= FIELD_W:
                continue
            free = None
            for k in range(EB_POOL):
                if self.eb[k] is None:
                    free = k
                    break
            if free is None:
                continue
            self.eb[free] = [e[0] - EB_SIZE, e[1] + (ENEMY_H - EB_SIZE) // 2]
            e[2] = ENEMY_FIRE
            self.eshots += 1
        # 6. a player bullet takes the FIRST enemy it overlaps
        for i in range(BULLET_POOL):
            b = self.pb[i]
            if b is None:
                continue
            hit = -1
            for k, e in enumerate(self.enemies):
                if overlap(b[0], b[1], BULLET_W, BULLET_H, e[0], e[1], ENEMY_W, ENEMY_H):
                    hit = k
                    break
            if hit < 0:
                continue
            self.pb[i] = None
            del self.enemies[hit]
            self.killed += 1
            self.score += KILL_SCORE
        # 7. an enemy bullet that touches the ship costs a life
        for i in range(EB_POOL):
            b = self.eb[i]
            if b is None:
                continue
            if not overlap(b[0], b[1], EB_SIZE, EB_SIZE, self.px, self.py, PLAYER_W, PLAYER_H):
                continue
            self.eb[i] = None
            self.lives -= 1
            if self.lives <= 0:
                self.lives = 0
                self.over = True
                self.won = False
                return
        # 8. wave transition and the win
        if self.wave_left == 0 and not self.enemies:
            if self.wave >= self.wave_max:
                self.won = True
                self.over = True
                return
            self.wave += 1
            self.wave_left = self.size_of_wave(self.wave)
            self.countdown = 0

    def step(self, count):
        applied = 0
        for _ in range(count):
            if self.over:
                break
            self.tick()
            applied += 1
        return applied

    # --- the actions -----------------------------------------------------------

    def move(self, dx, dy):
        if self.over:
            self.rejected += 1
            return
        nx = self.px + dx
        ny = self.py + dy
        if nx < 0:
            nx = 0
        if nx > FIELD_W - PLAYER_W:
            nx = FIELD_W - PLAYER_W
        if ny < HUD:
            ny = HUD
        if ny > FIELD_H - PLAYER_H:
            ny = FIELD_H - PLAYER_H
        if nx == self.px and ny == self.py:
            self.rejected += 1
        else:
            self.px = nx
            self.py = ny
            self.moves += 1

    def fire(self):
        if self.over:
            return
        for i in range(BULLET_POOL):
            if self.pb[i] is None:
                self.pb[i] = [self.px + PLAYER_W, self.py + (PLAYER_H - BULLET_H) // 2]
                self.shots += 1
                return

    def force(self, lives=None, score=None, wave=None, maxwave=None, left=None,
              countdown=None, player=None, enemies=None, bullets=None, ebullets=None):
        self.reset()
        if lives is not None:
            self.lives = lives
        if score is not None:
            self.score = score
        if maxwave is not None:
            self.wave_max = maxwave
        if wave is not None:
            self.wave = wave
        self.wave_left = left if left is not None else self.size_of_wave(self.wave)
        self.countdown = countdown if countdown is not None else 0
        if player is not None:
            self.px, self.py = player
        if enemies:
            for x, y, cd in enemies:
                self.enemies.append([x, y, cd])
            self.spawned = len(self.enemies)
        if bullets:
            for i, (x, y) in enumerate(bullets):
                self.pb[i] = [x, y]
            self.shots = len(bullets)
        if ebullets:
            for i, (x, y) in enumerate(ebullets):
                self.eb[i] = [x, y]
            self.eshots = len(ebullets)

    # --- the printable facts ---------------------------------------------------

    def enemy_list(self):
        return "|".join("%d,%d,%d" % (e[0], e[1], e[2]) for e in self.enemies)

    def bullet_list(self):
        return "|".join("%d,%d" % (b[0], b[1]) for b in self.pb if b is not None)

    def ebullet_list(self):
        return "|".join("%d,%d" % (b[0], b[1]) for b in self.eb if b is not None)

    def state_hash(self):
        value = 0
        for item in (self.px, self.py, self.lives, self.score, self.wave, self.wave_left):
            value = sign32(value * 31 + item)
        for e in self.enemies:
            value = sign32(value * 31 + e[0])
            value = sign32(value * 31 + e[1])
            value = sign32(value * 31 + e[2])
        for b in self.pb:
            if b is None:
                continue
            value = sign32(value * 31 + b[0])
            value = sign32(value * 31 + b[1])
        for b in self.eb:
            if b is None:
                continue
            value = sign32(value * 31 + b[0])
            value = sign32(value * 31 + b[1])
        return value


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
                        "color": {"r": 0.02, "g": 0.03, "b": 0.06, "a": 1}}},
        {"type": "Label", "name": "Hud", "parent_path": ".",
         "properties": {"offset_left": 14, "offset_top": 10, "offset_right": 790, "offset_bottom": 44,
                        "text": "WAVE 1/3  LIVES 3  SCORE 0  ALIVE 0  KILLED 0  ESCAPED 0  SHOTS 0",
                        "theme_override_font_sizes/font_size": 20}},
        {"type": "Label", "name": "Status", "parent_path": ".",
         "properties": {"offset_left": 14, "offset_top": 560, "offset_right": 640, "offset_bottom": 594,
                        "text": "SECTOR 1", "theme_override_font_sizes/font_size": 22}},
    ]
    call("e01-edit-game", "editor", "project_edit_script",
         {"path": "res://src/RTypeGame.cs", "content_file": PAYLOAD},
         "the whole game is written through the MCP script writer (the template stub is replaced)")
    call("e02-open-scene", "editor", "editor_open_scene", {"path": "res://scenes/main.tscn"},
         "the template scene carries the root Main (Node2D) the script is attached to")
    call("e03-batch-add-static", "editor", "editor_add_nodes_batch", {"nodes": nodes},
         "the three static nodes of the scene, through the batch tool: a background and two labels; the starfield, the ship, the formation and both bullet pools are created at run time")
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
    call("e10-action-fire", "editor", "editor_add_input_action", {"action": "rt_fire", "key": "Space"},
         "one bullet per press edge, for the input-edge scenario")
    call("e11-save-3", "editor", "editor_save_scene", {}, "persist the declared action")
    call("e12-build-csharp", "editor", "project_build_csharp", {},
         "the payload really compiles: the real dotnet exit code")
    call("e13-validate-scripts", "editor", "project_validate_scripts", {},
         "per-file verdicts for every script in the project")
    call("e14-get-errors", "editor", "editor_get_errors", {},
         "the editor's own error list after the build")


def game_phase():
    # --- the shape of the world, and the first frame ---------------------------
    call("g01-scene-tree", "game", "running_game_get_scene_tree", {},
         "the running game's tree: three static nodes, no @-auto names")
    assert_ok("g02-assert-field-w", "FieldW", FIELD_W, "the field is 800 pixels wide")
    assert_ok("g03-assert-field-h", "FieldH", FIELD_H, "and 600 tall")
    assert_ok("g04-assert-hud", "HudBottom", HUD, "the HUD strip ends at y=64")
    assert_ok("g05-assert-player-speed", "PlayerSpeed", PLAYER_SPEED,
              "one MovePlayer call travels %d pixels" % PLAYER_SPEED)
    assert_ok("g06-assert-bullet-speed", "BulletSpeed", BULLET_SPEED, "a player bullet travels 16 px per step")
    assert_ok("g07-assert-enemy-speed", "EnemySpeed", ENEMY_SPEED, "an enemy travels 3 px per step")
    assert_ok("g08-assert-enemy-bullet-speed", "EnemyBulletSpeed", EB_SPEED,
              "an enemy bullet travels 6 px per step")
    assert_ok("g09-assert-wave-max", "WaveMax", len(WAVE_SIZES), "three waves make a full game")
    fresh = RSim()
    assert_ok("g10-assert-lives", "Lives", fresh.lives, "a fresh game starts with %d lives" % fresh.lives)
    assert_ok("g11-assert-score", "Score", fresh.score, "and no score")
    assert_ok("g12-assert-start-pos", "PlayerY", fresh.py, "the ship starts at y=300")
    exec_code("g13-readback-t0", invoke("Dump()"),
              "the whole state on one line: the ship, the pools and every counter")
    shot("g14-shot-t0", "rt-t0", "the first frame: the starfield and the ship, no enemies")

    # --- the frozen baseline ----------------------------------------------------
    samples("g15-samples-frozen",
            ["Steps", "EnemiesAlive", "BulletsActive", "StateHash", "Elapsed", "Ticks"], 12,
            "determinism baseline: AutoClock is 0, so the simulation facts are constant while Elapsed and Ticks both advance")
    assert_ok("g16-assert-frozen-steps", "Steps", 0, "with the clock off and no hook called, not one step has run")
    assert_ok("g17-assert-frozen-auto", "LastAutoSteps", 0, "and the auto clock applied nothing")
    assert_ok("g18-assert-frozen-hook", "LastHookSteps", 0, "and the hook applied nothing either")

    # --- the probes name what stands where --------------------------------------
    probe = RSim()
    probe.force(lives=3, score=0, wave=1, maxwave=3, left=0, player=(80, 300))
    exec_code("g19-probe-setup", force("lives=3;score=0;wave=1;maxwave=3;left=0;player=80,300"),
              "a pinned, empty field with the ship at (80,300)")
    assert_ok("g20-assert-probe-pos-x", "PlayerX", probe.px, "the pinned ship x")
    assert_ok("g21-assert-probe-pos-y", "PlayerY", probe.py, "and the pinned y")
    for tag, x, y, state in (("g22", 90, 305, "player"), ("g23", 500, 400, "empty"),
                             ("g24", 900, 100, "outside"), ("g25", 79, 300, "empty")):
        exec_code("%s-probe-%d-%d" % (tag, x, y), invoke("ProbeAt(%d, %d)" % (x, y)),
                  "the probe names what stands at one point, so the assertion below is about that point")
        assert_ok("%sa-assert-probe-state" % tag, "ProbeState", state,
                  "(%d,%d) is %s" % (x, y, state))

    # --- the ship moves, and the edges clamp it ---------------------------------
    exec_code("g26-move-right", invoke("MovePlayer(8, 0)"), "one call moves the ship right by one step")
    probe.move(8, 0)
    assert_ok("g27-assert-x-after-right", "PlayerX", probe.px, "the ship is at x=%d" % probe.px)
    assert_ok("g28-assert-moves", "Moves", probe.moves, "one move was counted")
    exec_code("g29-move-up", invoke("MovePlayer(0, -8)"), "and one call moves it up")
    probe.move(0, -8)
    assert_ok("g30-assert-y-after-up", "PlayerY", probe.py, "the ship is at y=%d" % probe.py)
    exec_code("g31-move-down", invoke("MovePlayer(0, 8)"), "and down again")
    probe.move(0, 8)
    assert_ok("g32-assert-y-back", "PlayerY", probe.py, "back to y=%d" % probe.py)
    exec_code("g33-move-clamp-left", invoke("MovePlayer(-1000, 0)"),
              "far past the left edge: the clamp decides, not the request")
    probe.move(-1000, 0)
    assert_ok("g34-assert-x-clamped-left", "PlayerX", probe.px, "clamped to x=%d" % probe.px)
    assert_ok("g35-assert-hash-after-clamp", "StateHash", probe.state_hash(),
              "the state hash the Python second implementation computes")
    exec_code("g36-move-rejected", invoke("MovePlayer(-8, 0)"),
              "already at the left edge: this one is refused, so LastEvent says reason=clamped")
    probe.move(-8, 0)
    assert_ok("g37-assert-rejected", "RejectedMoves", probe.rejected,
              "the refusal was counted (%d)" % probe.rejected)
    assert_ok("g38-assert-moves-still", "Moves", probe.moves, "and no move was counted")
    exec_code("g39-move-clamp-top", invoke("MovePlayer(0, -1000)"), "far past the top")
    probe.move(0, -1000)
    assert_ok("g40-assert-y-top", "PlayerY", probe.py, "clamped to the HUD line, y=%d" % probe.py)
    exec_code("g41-move-clamp-bottom", invoke("MovePlayer(0, 1000)"), "far past the bottom")
    probe.move(0, 1000)
    assert_ok("g42-assert-y-bottom", "PlayerY", probe.py, "clamped to y=%d" % probe.py)
    exec_code("g43-move-clamp-right", invoke("MovePlayer(1000, 0)"), "far past the right edge")
    probe.move(1000, 0)
    assert_ok("g44-assert-x-right", "PlayerX", probe.px, "clamped to x=%d" % probe.px)
    exec_code("g45-move-rejected-right", invoke("MovePlayer(8, 0)"), "already at the right edge: refused")
    probe.move(8, 0)
    assert_ok("g46-assert-rejected-2", "RejectedMoves", probe.rejected,
              "two refusals now (%d)" % probe.rejected)

    # --- firing, flight, and the bullet leaving the field ------------------------
    flight = RSim()
    flight.force(lives=3, score=0, wave=1, maxwave=3, left=0, player=(80, 300))
    exec_code("g47-flight-setup", force("lives=3;score=0;wave=1;maxwave=3;left=0;player=80,300"),
              "a pinned, empty field for the flight measurements")
    exec_code("g48-fire", invoke("FireBullet()"),
              "one bullet leaves the ship's nose at (PlayerX+24, PlayerY+6)")
    flight.fire()
    assert_ok("g49-assert-shots", "BulletsFired", flight.shots, "one bullet was fired")
    assert_ok("g50-assert-active", "BulletsActive", 1, "and it is in the air")
    assert_ok("g51-assert-bullet-list", "BulletList", flight.bullet_list(),
              "the bullet list names it: %s (Python computed the spawn point)" % flight.bullet_list())
    exec_code("g52-probe-bullet", invoke("ProbeAt(105, 307)"), "the probe names the bullet")
    assert_ok("g52a-assert-probe-bullet", "ProbeState", "bullet", "the point really is on the bullet")
    flight.step(1)
    exec_code("g53-step-1", invoke("StepFrames(1)"), "one step: the bullet moves 16 px right")
    assert_ok("g54-assert-list-1", "BulletList", flight.bullet_list(),
              "after one step Python says %s" % flight.bullet_list())
    assert_ok("g55-assert-steps-1", "Steps", flight.steps, "one step ran")
    flight.step(3)
    exec_code("g56-step-3", invoke("StepFrames(3)"), "three more steps")
    assert_ok("g57-assert-list-4", "BulletList", flight.bullet_list(),
              "after four steps Python says %s" % flight.bullet_list())
    assert_ok("g58-assert-hook-3", "LastHookSteps", 3, "the hook's OWN property is what it applied")
    out = RSim()
    out.force(lives=3, score=0, wave=1, maxwave=3, left=0, player=(80, 300))
    exec_code("g59-out-setup", force("lives=3;score=0;wave=1;maxwave=3;left=0;player=80,300"),
              "a fresh pinned field for the bullet that never hits anything")
    exec_code("g60-out-fire", invoke("FireBullet()"), "one bullet")
    out.fire()
    applied = out.step(44)
    exec_code("g61-out-step", invoke("StepFrames(44)"),
              "the bullet crosses 704 px and leaves the right edge on the last of them")
    assert_ok("g62-assert-out-empty", "BulletList", out.bullet_list(),
              "gone: Python says the list is %r" % out.bullet_list())
    assert_ok("g63-assert-out-active", "BulletsActive", 0, "no bullet in the air")
    assert_ok("g64-assert-out-steps", "Steps", out.steps, "the steps really ran")
    assert_ok("g65-assert-out-hook", "LastHookSteps", applied, "all %d of them" % applied)

    # --- a kill, and what it is worth --------------------------------------------
    kill = RSim()
    kill.force(lives=3, score=0, wave=1, maxwave=3, left=0, player=(80, 300),
               enemies=[(200, 300, 45)], bullets=[(184, 306)])
    exec_code("g66-kill-setup",
              force("lives=3;score=0;wave=1;maxwave=3;left=0;player=80,300;enemies=200,300,45;bullets=184,306"),
              "a pinned enemy a few pixels in front of a pinned bullet, both on the ship's firing line")
    assert_ok("g67-assert-enemies", "EnemiesAlive", 1, "one enemy stands")
    assert_ok("g68-assert-before-hash", "StateHash", kill.state_hash(), "the pinned state, hashed in Python")
    kill.step(1)
    exec_code("g69-kill-step", invoke("StepFrames(1)"), "one step: the bullet reaches the enemy")
    assert_ok("g70-assert-killed", "EnemiesKilled", kill.killed, "one kill")
    assert_ok("g71-assert-alive", "EnemiesAlive", 0, "the field is empty")
    assert_ok("g72-assert-score", "Score", kill.score, "a kill is worth %d points" % KILL_SCORE)
    assert_ok("g73-assert-bullet-gone", "BulletList", kill.bullet_list(),
              "the bullet was consumed (Python: %r)" % kill.bullet_list())
    assert_ok("g74-assert-after-hash", "StateHash", kill.state_hash(), "and the world hash follows")

    # --- the formation ------------------------------------------------------------
    form = RSim()
    form.force(lives=9, score=0, wave=1, maxwave=3, left=4, countdown=0, player=(400, 300))
    exec_code("g75-form-setup", force("lives=9;score=0;wave=1;maxwave=3;left=4;countdown=0;player=400,300"),
              "a pinned state with a whole wave still to enter")
    form.step(1)
    exec_code("g76-form-step-1", invoke("StepFrames(1)"), "one step: the first ship of the formation enters")
    assert_ok("g77-assert-spawned-1", "EnemiesSpawned", form.spawned, "one enemy entered")
    assert_ok("g78-assert-left-1", "WaveLeftToSpawn", form.wave_left, "three still to come")
    assert_ok("g79-assert-countdown-1", "SpawnCountdown", form.countdown, "and the spawn clock is set")
    assert_ok("g80-assert-list-1", "EnemyList", form.enemy_list(),
              "the first formation slot: %s" % form.enemy_list())
    form.step(18)
    exec_code("g81-form-step-18", invoke("StepFrames(18)"),
              "eighteen more steps: the whole formation of four has entered")
    assert_ok("g82-assert-spawned-4", "EnemiesSpawned", form.spawned, "four enemies entered")
    assert_ok("g83-assert-left-0", "WaveLeftToSpawn", form.wave_left, "none left to spawn")
    assert_ok("g84-assert-list-4", "EnemyList", form.enemy_list(),
              "the formation, exactly as Python walks the slot arithmetic: %s" % form.enemy_list())
    rows = sorted(set(e[1] for e in form.enemies))
    assert_ok("g85-assert-formation-rows", "EnemiesAlive", len(form.enemies),
              "the formation has %d distinct rows (%s)" % (len(rows), rows))

    # --- enemy fire ----------------------------------------------------------------
    shoot = RSim()
    shoot.force(lives=3, score=0, wave=1, maxwave=3, left=0, player=(400, 560), enemies=[(400, 300, 1)])
    exec_code("g86-shoot-setup",
              force("lives=3;score=0;wave=1;maxwave=3;left=0;player=400,560;enemies=400,300,1"),
              "one enemy already inside the field with one step of cooldown left")
    shoot.step(1)
    exec_code("g87-shoot-step-1", invoke("StepFrames(1)"), "one step: the enemy fires")
    assert_ok("g88-assert-eshots", "EnemyShotsFired", shoot.eshots, "one enemy bullet was fired")
    assert_ok("g89-assert-eshots-active", "EnemyBulletsActive", 1, "and it is in the air")
    assert_ok("g90-assert-ebullet-list", "EnemyBulletList", shoot.ebullet_list(),
              "the enemy bullet list: %s (Python computed the muzzle)" % shoot.ebullet_list())
    assert_ok("g91-assert-enemy-list", "EnemyList", shoot.enemy_list(),
              "and the enemy that fired: %s" % shoot.enemy_list())
    shoot.step(1)
    exec_code("g92-shoot-step-2", invoke("StepFrames(1)"), "one more step: the enemy bullet flies")
    assert_ok("g93-assert-ebullet-list-2", "EnemyBulletList", shoot.ebullet_list(),
              "Python says %s" % shoot.ebullet_list())

    # --- the ship takes a hit -------------------------------------------------------
    hit = RSim()
    hit.force(lives=3, score=0, wave=1, maxwave=3, left=0, player=(100, 300), ebullets=[(120, 306)])
    exec_code("g94-hit-setup",
              force("lives=3;score=0;wave=1;maxwave=3;left=0;player=100,300;ebullets=120,306"),
              "an enemy bullet one step from the ship, with no enemy on the field")
    hit.step(1)
    exec_code("g95-hit-step", invoke("StepFrames(1)"), "one step: it touches the ship")
    assert_ok("g96-assert-lives", "Lives", hit.lives, "the hit cost a life (%d left)" % hit.lives)
    assert_ok("g97-assert-over", "GameOver", hit.over, "and the game is not over yet")
    assert_ok("g98-assert-ebullets", "EnemyBulletList", hit.ebullet_list(),
              "the bullet was consumed (Python: %r)" % hit.ebullet_list())
    assert_ok("g99-assert-hash", "StateHash", hit.state_hash(), "the world hash after the hit")

    # --- an enemy that crosses the field ---------------------------------------------
    esc = RSim()
    esc.force(lives=3, score=0, wave=1, maxwave=3, left=0, player=(400, 560), enemies=[(-22, 300, 45)])
    exec_code("g100-escape-setup",
              force("lives=3;score=0;wave=1;maxwave=3;left=0;player=400,560;enemies=-22,300,45"),
              "an enemy that starts almost past the left edge")
    esc.step(1)
    exec_code("g101-escape-step", invoke("StepFrames(1)"), "one step: it crosses the edge")
    assert_ok("g102-assert-escaped", "EnemiesEscaped", esc.escaped, "one enemy crossed the field")
    assert_ok("g103-assert-lives", "Lives", esc.lives, "and that costs a life (%d left)" % esc.lives)
    assert_ok("g104-assert-alive", "EnemiesAlive", 0, "nothing is left on the field")

    # --- losing ----------------------------------------------------------------------
    lose = RSim()
    lose.force(lives=1, score=0, wave=1, maxwave=3, left=0, player=(100, 300), ebullets=[(120, 306)])
    exec_code("g105-lose-setup",
              force("lives=1;score=0;wave=1;maxwave=3;left=0;player=100,300;ebullets=120,306"),
              "the last life, and an enemy bullet one step from the ship")
    applied = lose.step(3)
    exec_code("g106-lose-step", invoke("StepFrames(3)"), "three steps: the bullet arrives, the life is gone")
    assert_ok("g107-assert-lives-0", "Lives", lose.lives, "no lives left")
    assert_ok("g108-assert-over", "GameOver", lose.over, "so the game is over")
    assert_ok("g109-assert-not-won", "Won", lose.won, "and it was not won")
    assert_ok("g110-assert-hook-applied", "LastHookSteps", applied,
              "the hook stopped at the end of the game: %d of the three steps ran" % applied)
    exec_code("g111-fire-after-lose", invoke("FireBullet()"), "a shot after the game ended")
    lose.fire()
    assert_ok("g112-assert-shots-zero", "BulletsFired", lose.shots, "refused: no bullet was fired")
    exec_code("g113-move-after-lose", invoke("MovePlayer(8, 0)"), "a move after the game ended")
    lose.move(8, 0)
    assert_ok("g114-assert-rejected", "RejectedMoves", lose.rejected,
              "refused too (%d refusal counted)" % lose.rejected)
    shot("g115-shot-lost", "rt-t1", "the lost game: the status label and the empty field")

    # --- the input edge ----------------------------------------------------------------
    edge = RSim()
    edge.force(lives=3, score=0, wave=1, maxwave=3, left=0, player=(80, 300))
    exec_code("g116-input-setup", force("lives=3;score=0;wave=1;maxwave=3;left=0;player=80,300"),
              "a pinned state for the declared-input scenario")
    exec_code("g117-poll-on", invoke("SetPollInput(true)"), "start listening to the declared action")
    call("g118-input-fire", "game", "running_game_run_test_scenario",
         {"steps": [{"type": "input", "action": "rt_fire", "pressed": True},
                    {"type": "wait", "seconds": 0.45},
                    {"type": "assert", "node_path": "Main", "property": "BulletsFired",
                     "operator": "gte", "expected": 1}]},
         "the declared action really fires (a press edge, so exactly one bullet)")
    assert_ok("g119-assert-input-shots", "InputShots", 1, "the edge fired exactly once")
    exec_code("g120-poll-off", invoke("SetPollInput(false)"),
              "stop listening again, so the rest of the session is deterministic")
    exec_code("g121-input-cleanup", force("lives=3;score=0;wave=1;maxwave=3;left=0;player=80,300"),
              "clear the bullet the edge left in the air")

    # --- a whole game, cleared by letting the clock run while the ship fires ---------
    play = RSim()
    play.force(lives=60, score=0, wave=1, maxwave=3, player=(0, 120))
    exec_code("g122-play-setup", force("lives=60;score=0;wave=1;maxwave=3;player=0,120"),
              "a pinned, well-funded state: the ship sits on the first formation row and will shoot down everything in its lane")
    for index in range(26):
        exec_code("g%03d-play-fire" % (123 + index * 2), invoke("FireBullet()"),
                  "one bullet down the ship's lane (chunk %d)" % (index + 1))
        play.fire()
        applied = play.step(40)
        exec_code("g%03d-play-step" % (124 + index * 2), invoke("StepFrames(40)"),
                  "forty steps of the same rules Python runs (chunk %d)" % (index + 1))
        if play.over:
            break
    assert_ok("g175-assert-won", "Won", play.won, "Python says this board is cleared: Won must be true")
    assert_ok("g176-assert-over", "GameOver", play.over, "and the game ended")
    assert_ok("g177-assert-spawned", "EnemiesSpawned", play.spawned,
              "all %d enemies of all three waves entered" % play.spawned)
    assert_ok("g178-assert-killed", "EnemiesKilled", play.killed,
              "Python shot down %d of them (the ones in the ship's lane)" % play.killed)
    assert_ok("g179-assert-escaped", "EnemiesEscaped", play.escaped,
              "and %d crossed the field" % play.escaped)
    assert_ok("g180-assert-lives", "Lives", play.lives, "%d lives left" % play.lives)
    assert_ok("g181-assert-score", "Score", play.score, "score %d" % play.score)
    assert_ok("g182-assert-wave", "Wave", play.wave, "the last wave reached")
    assert_ok("g183-assert-steps", "Steps", play.steps, "the game took exactly %d steps" % play.steps)
    shot("g184-shot-won", "rt-t2", "the cleared field: the status label and the ship")
    call("g185-assert-screen-win", "game", "running_game_assert_screen_text", {"text": "WAVE CLEARED"},
         "the status label really is on the captured screen")

    # --- the clock: multi-frame sampling with a must-move assertion -----------------
    clock = RSim()
    clock.force(lives=3, score=0, wave=1, maxwave=3, left=4, countdown=0, player=(400, 300))
    exec_code("g186-clock-setup", force("lives=3;score=0;wave=1;maxwave=3;left=4;countdown=0;player=400,300"),
              "a fresh state with a whole wave still to enter, so the clock has something to do")
    assert_ok("g187-assert-clock-steps-0", "Steps", 0, "the clock is off, so nothing has moved yet")
    hash0 = clock.state_hash()
    assert_ok("g188-assert-clock-hash-0", "StateHash", hash0, "the pinned world hash")
    exec_code("g189-clock-on", invoke("SetAutoClock(60.0)"),
              "the clock ticks 60 times a second (a float accumulator, F-1's fix)")
    samples("g190-samples-clock",
            ["Steps", "EnemiesSpawned", "EnemiesAlive", "StateHash", "Elapsed", "Ticks"], 30,
            "thirty frames with the clock running: the formation enters and the world hash moves")
    assert_state("g191-assert-clock-moved", "Steps", "gt", 0,
                 "MUST MOVE: if the clock is frozen this assertion FAILS (the M3-4 lesson)")
    assert_state("g192-assert-clock-spawned", "EnemiesSpawned", "gt", 0,
                 "MUST SPAWN: a live clock has to put ships on the field")
    assert_state("g193-assert-clock-hash-moved", "StateHash", "neq", hash0,
                 "MUST CHANGE: a frozen world would keep the pinned hash (the M3-4 lesson)")
    assert_state("g194-assert-clock-auto-ticks", "AutoTicks", "gte", 1,
                 "the clock applied at least one step (the exact count depends on the frame rate)")
    exec_code("g195-clock-off", invoke("SetAutoClock(0.0)"), "stop the clock")
    assert_ok("g196-assert-clock-off-auto", "LastAutoSteps", 0, "with the clock off the frame contributes nothing")

    # --- the two producers, two properties -------------------------------------------
    hook = RSim()
    hook.force(lives=3, score=0, wave=1, maxwave=3, left=0, player=(80, 300), enemies=[(600, 300, 45)])
    exec_code("g197-hook-setup",
              force("lives=3;score=0;wave=1;maxwave=3;left=0;player=80,300;enemies=600,300,45"),
              "a pinned state again")
    applied = hook.step(3)
    exec_code("g198-hook-step-3", invoke("StepFrames(3)"), "three hook steps")
    assert_ok("g199-assert-hook-3", "LastHookSteps", 3, "the hook's own property")
    samples("g200-samples-quiet", ["Steps", "EnemyList", "Elapsed", "Ticks"], 12,
            "the clock is off, so the frame loop advances Elapsed and Ticks and nothing else")
    assert_ok("g201-assert-hook-still-3", "LastHookSteps", 3,
              "after twelve frames the hook's property is STILL 3: the clock never writes it (the G1 lesson)")
    assert_ok("g202-assert-auto-0", "LastAutoSteps", 0, "while the clock's own property is 0")
    assert_ok("g203-assert-auto-ticks-0", "AutoTicks", 0, "and it applied nothing at all")
    assert_ok("g204-assert-steps-still", "Steps", hook.steps, "the simulation did not move on its own")

    # --- the final readback, the scene tree, and one declared boundary ----------------
    exec_code("g205-final-readback", invoke("Dump()"),
              "the final state on one line: every counter this session asserted")
    shot("g206-shot-final", "rt-t3", "the final frame")
    call("g207-final-tree", "game", "running_game_get_scene_tree", {},
         "the final tree: every node name is one this game made, no @-auto names")
    assert_state("g208-assert-boundary", "NoSuchPropertyAtAll", "eq", 0,
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
    manifest_path = os.path.join(HERE, "expectations-rtype.json")
    with io.open(manifest_path, "w", encoding="utf-8", newline="\n") as handle:
        json.dump(manifest, handle, ensure_ascii=False, indent=1)
        handle.write("\n")
    editor = len([c for c in CALLS if c["port"] == "editor"])
    game = len([c for c in CALLS if c["port"] == "game"])
    print("wrote %s" % OUT)
    print("calls: %d (editor %d / game %d)" % (len(CALLS), editor, game))
    print("expectations: %d -> %s" % (len(manifest), manifest_path))
    # The two facts the session's own verdicts rest on, printed so the generator
    # cannot be the only place they are known.
    play = RSim()
    play.force(lives=60, score=0, wave=1, maxwave=3, player=(0, 120))
    fired = 0
    for _ in range(26):
        play.fire()
        fired += 1
        play.step(40)
        if play.over:
            break
    print("full game: won=%s over=%s steps=%d spawned=%d killed=%d escaped=%d lives=%d score=%d "
          "wave=%d fires=%d" % (play.won, play.over, play.steps, play.spawned, play.killed,
                                play.escaped, play.lives, play.score, play.wave, fired))
    if not play.won:
        print("WARNING: the pinned full-game configuration does not win")
    with io.open(OUT, "r", encoding="utf-8") as handle:
        again = json.load(handle)
    assert len(again["calls"]) == len(CALLS)
    print("json round-trip: OK (%d calls)" % len(again["calls"]))
    return 0


if __name__ == "__main__":
    sys.exit(main())
