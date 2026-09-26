#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""TASK-103 (B, game 17): the Missile Command session generator, with the Python
second implementation of the payload's rules.

The payload is `tools/sessions/missilecommand/payload/MissileCommandGame.cs`.
`MSim` below re-implements its rules from the rules: the linear congruential spawn
generator, the floor-division trajectory (`x0 + (tx-x0)*k // dur`, with Python's
flooring `//` matching the C# `DivFloor` the payload spells out for negative
numerators), the interceptor launch, the explosion coverage (integer squared
distance), the city blast and the wave machinery. Every literal a
`running_game_assert_node_state` compares against comes from `MSim`, and the
session's own screenshots are recomputed separately by `recompute_mc.py`.

The session drives the game through MCP calls only, exactly like game 16.

Written by a Python writer, never by a shell redirect (iron rule 1).
"""

import io
import json
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.abspath(os.path.join(HERE, "..", "..", ".."))
SESSION_DIR = os.path.join(ROOT, "tools", "sessions", "missilecommand")
OUT = os.path.join(SESSION_DIR, "session.json")
PAYLOAD = "payload/MissileCommandGame.cs"

FIELD_W = 800
FIELD_H = 600
CITY_XS = [80, 200, 320, 440, 560, 680]
CITY_Y = 548
BATTERY_XS = [40, 400, 760]
BATTERY_Y = 586
AMMO_PER_BATTERY = 10
INTERCEPTOR_SPEED = 12
EXPLOSION_TICKS = 8
EXPLOSION_RADIUS = 34
BLAST_RADIUS = 28
POINTS_PER_KILL = 25
POINTS_PER_CITY = 100
WAVE_COUNTS = [4, 6, 8]
WAVE_SPEEDS = [8, 10, 12]
WAVE_INTERVALS = [45, 36, 30]
SEED = 20250927


def div_floor(a, b):
    return a // b


def pos_at(start, end, step, duration):
    if duration <= 0:
        return end
    return start + div_floor((end - start) * step, duration)


def sign32(value):
    value &= 0xFFFFFFFF
    return value - 0x100000000 if value >= 0x80000000 else value


class MSim(object):
    """The payload's rules, re-implemented from the rules."""

    def __init__(self):
        self.reset()

    def reset(self):
        self.cities = [True] * len(CITY_XS)
        self.ammo = [AMMO_PER_BATTERY] * len(BATTERY_XS)
        # each missile: [x, y, tx, ty, k, dur, x0, y0]
        self.incoming = []
        self.interceptors = []
        # each explosion: [x, y, ticks]
        self.explosions = []
        self.rand = SEED
        self.wave = 1
        self.wave_max = len(WAVE_COUNTS)
        self.wave_left = WAVE_COUNTS[0]
        self.countdown = 0
        self.spawned = 0
        self.destroyed = 0
        self.leaked = 0
        self.fired = 0
        self.cities_lost = 0
        self.score = 0
        self.steps = 0
        self.won = False
        self.over = False

    def next_rand(self):
        self.rand = (self.rand * 1103515245 + 12345) & 0x7FFFFFFF
        return self.rand

    def cities_alive(self):
        return sum(1 for alive in self.cities if alive)

    def spawn(self):
        r1 = self.next_rand()
        x0 = 20 + ((r1 >> 16) % 760)
        r2 = self.next_rand()
        selector = (r2 >> 16) % 8
        if selector < len(CITY_XS):
            tx, ty = CITY_XS[selector], CITY_Y
        else:
            tx, ty = 20 + ((r2 >> 16) % 760), FIELD_H
        span = max(abs(tx - x0), abs(ty))
        dur = max(1, -(-span // WAVE_SPEEDS[self.wave - 1]))
        self.incoming.append([x0, 0, tx, ty, 0, dur, x0, 0])
        self.spawned += 1

    def fire(self, x, y):
        if self.over:
            return "rejected reason=game_over"
        if x < 0 or x > FIELD_W or y < 0 or y > FIELD_H:
            return "rejected reason=out_of_bounds at=%d,%d" % (x, y)
        pick = -1
        best = 0
        for index, bx in enumerate(BATTERY_XS):
            if self.ammo[index] <= 0:
                continue
            distance = abs(bx - x)
            if pick < 0 or distance < best:
                pick = index
                best = distance
        if pick < 0:
            return "rejected reason=no_ammo"
        bx, by = BATTERY_XS[pick], BATTERY_Y
        span = max(abs(x - bx), abs(y - by))
        dur = max(1, -(-span // INTERCEPTOR_SPEED))
        self.interceptors.append([bx, by, x, y, 0, dur, bx, by])
        self.ammo[pick] -= 1
        self.fired += 1
        return "fired from=%d,%d to=%d,%d dur=%d battery=%d ammo=%d" % (bx, by, x, y, dur, pick, self.ammo[pick])

    def force(self, cities=None, ammo=None, seed=None, wave=None, maxwave=None, left=None,
              countdown=None, score=None, incoming=None, interceptors=None, blasts=None):
        self.reset()
        if cities is not None:
            self.cities = [flag == 1 for flag in cities]
        if ammo is not None:
            self.ammo = list(ammo)
        if seed is not None:
            self.rand = seed
        if score is not None:
            self.score = score
        if maxwave is not None:
            self.wave_max = maxwave
        if wave is not None:
            self.wave = wave
        self.wave_left = left if left is not None else WAVE_COUNTS[self.wave - 1]
        self.countdown = countdown if countdown is not None else 0
        for record in incoming or []:
            x0, y0, tx, ty, k, dur = record
            self.incoming.append([pos_at(x0, tx, k, dur), pos_at(y0, ty, k, dur), tx, ty, k, dur, x0, y0])
        for record in interceptors or []:
            x0, y0, tx, ty, k, dur = record
            self.interceptors.append([pos_at(x0, tx, k, dur), pos_at(y0, ty, k, dur), tx, ty, k, dur, x0, y0])
        for x, y, ticks in blasts or []:
            self.explosions.append([x, y, ticks])

    def tick(self):
        if self.over:
            return
        self.steps += 1
        # 1. spawn
        if self.wave_left > 0:
            if self.countdown <= 0:
                self.spawn()
                self.wave_left -= 1
                self.countdown = WAVE_INTERVALS[self.wave - 1]
            else:
                self.countdown -= 1
        # 2. move incoming
        for m in self.incoming:
            m[4] += 1
            m[0] = pos_at(m[6], m[2], m[4], m[5])
            m[1] = pos_at(m[7], m[3], m[4], m[5])
        # 3. arrivals take a city with them
        for index in range(len(self.incoming) - 1, -1, -1):
            m = self.incoming[index]
            if m[4] >= m[5]:
                tx, ty = m[2], m[3]
                del self.incoming[index]
                self.leaked += 1
                for c, alive in enumerate(self.cities):
                    if not alive:
                        continue
                    dx, dy = CITY_XS[c] - tx, CITY_Y - ty
                    if dx * dx + dy * dy <= BLAST_RADIUS * BLAST_RADIUS:
                        self.cities[c] = False
                        self.cities_lost += 1
        if self.cities_alive() == 0:
            self.over = True
            self.won = False
            return
        # 4. move interceptors; arrivals become explosions
        for index in range(len(self.interceptors) - 1, -1, -1):
            m = self.interceptors[index]
            m[4] += 1
            m[0] = pos_at(m[6], m[2], m[4], m[5])
            m[1] = pos_at(m[7], m[3], m[4], m[5])
            if m[4] >= m[5]:
                del self.interceptors[index]
                self.explosions.append([m[2], m[3], EXPLOSION_TICKS])
        # 5. explosions destroy what is inside them
        for blast in self.explosions:
            for index in range(len(self.incoming) - 1, -1, -1):
                dx = self.incoming[index][0] - blast[0]
                dy = self.incoming[index][1] - blast[1]
                if dx * dx + dy * dy <= EXPLOSION_RADIUS * EXPLOSION_RADIUS:
                    del self.incoming[index]
                    self.destroyed += 1
                    self.score += POINTS_PER_KILL
        # 6. age explosions
        for index in range(len(self.explosions) - 1, -1, -1):
            self.explosions[index][2] -= 1
            if self.explosions[index][2] <= 0:
                del self.explosions[index]
        # 7. wave transition / win
        if self.wave_left == 0 and not self.incoming and not self.interceptors:
            if self.wave >= self.wave_max:
                self.score += POINTS_PER_CITY * self.cities_alive()
                self.won = True
                self.over = True
                return
            self.score += POINTS_PER_CITY * self.cities_alive()
            self.wave += 1
            self.wave_left = WAVE_COUNTS[self.wave - 1]
            self.countdown = 0
            self.ammo = [AMMO_PER_BATTERY] * len(BATTERY_XS)

    def step(self, count):
        applied = 0
        for _ in range(count):
            if self.over:
                break
            self.tick()
            applied += 1
        return applied

    def state(self):
        return {
            "cities": self.cities_alive(),
            "city_list": "|".join("1" if alive else "0" for alive in self.cities),
            "ammo": sum(self.ammo),
            "ammo_list": "|".join(str(value) for value in self.ammo),
            "incoming_alive": len(self.incoming),
            "incoming_list": "|".join(",".join(str(f) for f in m) for m in self.incoming),
            "interceptor_alive": len(self.interceptors),
            "interceptor_list": "|".join(",".join(str(f) for f in m) for m in self.interceptors),
            "blasts_active": len(self.explosions),
            "blast_list": "|".join(",".join(str(f) for f in b) for b in self.explosions),
            "destroyed": self.destroyed,
            "leaked": self.leaked,
            "spawned": self.spawned,
            "fired": self.fired,
            "cities_lost": self.cities_lost,
            "score": self.score,
            "wave": self.wave,
            "wave_left": self.wave_left,
            "steps": self.steps,
            "won": self.won,
            "over": self.over,
        }


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
                        "color": {"r": 0.03, "g": 0.03, "b": 0.06, "a": 1}}},
        {"type": "Label", "name": "Hud", "parent_path": ".",
         "properties": {"offset_left": 14, "offset_top": 10, "offset_right": 780, "offset_bottom": 44,
                        "text": "WAVE 1/3  CITIES 6  AMMO 30  INCOMING 0  BLASTS 0  SCORE 0",
                        "theme_override_font_sizes/font_size": 20}},
        {"type": "Label", "name": "Status", "parent_path": ".",
         "properties": {"offset_left": 14, "offset_top": 556, "offset_right": 640, "offset_bottom": 576,
                        "text": "DEFEND THE CITIES", "theme_override_font_sizes/font_size": 20}},
    ]
    call("e01-edit-game", "editor", "project_edit_script",
         {"path": "res://src/MissileCommandGame.cs", "content_file": PAYLOAD},
         "the whole game is written through the MCP script writer (the template stub is replaced)")
    call("e02-open-scene", "editor", "editor_open_scene", {"path": "res://scenes/main.tscn"},
         "the template scene carries the root Main (Node2D) the script is attached to")
    call("e03-batch-add-static", "editor", "editor_add_nodes_batch", {"nodes": nodes},
         "the three static nodes of the scene, through the batch tool: a background and two labels; the cities, the batteries and every missile are created at run time")
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
    call("e10-action-fire", "editor", "editor_add_input_action", {"action": "mc_auto_fire", "key": "Space"},
         "one deterministic shot, for the input-edge scenario")
    call("e11-save-3", "editor", "editor_save_scene", {}, "persist the declared action")
    call("e12-build-csharp", "editor", "project_build_csharp", {},
         "the payload really compiles: the real dotnet exit code")
    call("e13-validate-scripts", "editor", "project_validate_scripts", {},
         "per-file verdicts for every script in the project")
    call("e14-get-errors", "editor", "editor_get_errors", {},
         "the editor's own error list after the build")


def game_phase():
    sim0 = MSim()
    # --- the field, the cities, the batteries ---------------------------------
    call("g01-scene-tree", "game", "running_game_get_scene_tree", {},
         "the running game's tree: three static nodes, no @-auto names")
    assert_ok("g02-assert-field-w", "FieldW", FIELD_W, "the playfield is 800 pixels wide")
    assert_ok("g03-assert-field-h", "FieldH", FIELD_H, "and 600 tall")
    assert_ok("g04-assert-city-y", "CityY", CITY_Y, "the cities sit on one line")
    assert_ok("g05-assert-city-count", "CitiesAlive", sim0.cities_alive(), "six cities stand at the start")
    assert_ok("g06-assert-city-list", "CityList", sim0.state()["city_list"], "and the list names all six")
    assert_ok("g07-assert-ammo", "Ammo", sim0.state()["ammo"], "three batteries hold ten shots each")
    assert_ok("g08-assert-ammo-list", "AmmoList", sim0.state()["ammo_list"], "one entry per battery")
    assert_ok("g09-assert-wave", "Wave", 1, "a fresh game starts in wave 1")
    assert_ok("g10-assert-wave-max", "WaveMax", len(WAVE_COUNTS), "three waves make a full game")
    assert_ok("g11-assert-spawned", "Spawned", 0, "and nothing has been launched yet")
    exec_code("g12-readback-t0", invoke("Dump()"),
              "the whole state on one line: the lists, the counters and the world hash")
    shot("g13-shot-t0", "mc-t0", "the first frame: six cities, three batteries, an empty sky")

    # --- the frozen baseline ----------------------------------------------------
    samples("g14-samples-frozen", ["Steps", "IncomingAlive", "CitiesAlive", "Score", "Won", "Elapsed", "Ticks"], 12,
            "determinism baseline: AutoClock is 0, so the simulation facts are constant while Elapsed and Ticks both advance")
    assert_ok("g15-assert-frozen-steps", "Steps", 0, "with the clock off and no hook called, not one simulation step has run")
    assert_ok("g16-assert-frozen-auto", "LastAutoSteps", 0, "and the auto clock applied nothing")
    assert_ok("g17-assert-frozen-hook", "LastHookSteps", 0, "and the hook applied nothing either")

    # --- probing the field -------------------------------------------------------
    # Each state assertion sits directly behind the probe it is about. The first
    # version of this block put the three state assertions after the loop, so they
    # read the state of the LAST probe -- the same class of defect as PL-3 / K-1 /
    # M1 ("the expectation must reference the moment it is about"), caught by the
    # session's own assertion on its second run.
    for tag, x, y, state, expected in (("g18", 80, 548, "city", 0),
                                       ("g19", 40, 586, "battery", 0),
                                       ("g20", 400, 300, "ground", -1)):
        exec_code("%s-probe" % tag, invoke("ProbePoint(%d, %d)" % (x, y)),
                  "the probe names what stands at one point, so the two assertions right behind it are about that point")
        assert_ok("%sa-assert-probe-value" % tag, "ProbeValue", expected,
                  "the probe at (%d,%d) names index %d" % (x, y, expected))
        assert_ok("%sb-assert-probe-state" % tag, "ProbeState", state,
                  "and says what stands there: %s" % state)
    exec_code("g21-probe-outside", invoke("ProbePoint(900, 900)"), "outside the playfield")
    assert_ok("g21a-assert-probe-state", "ProbeState", "outside", "a point outside is named as such")

    # --- the pinned sky: one explosion, one kill, one survivor -------------------
    sky = MSim()
    sky.force(cities=[1, 1, 1, 1, 1, 1], ammo=[10, 10, 10], wave=1, maxwave=3, left=0,
              incoming=[(320, 530, 320, 548, 0, 12), (700, 100, 700, 600, 0, 40)],
              blasts=[(320, 548, EXPLOSION_TICKS)])
    exec_code("g22-sky-setup",
              force("cities=1,1,1,1,1,1;ammo=10,10,10;wave=1;maxwave=3;left=0;seed=1;"
                    "incoming=320,530,320,548,0,12|700,100,700,600,0,40;blasts=320,548,8"),
              "a pinned sky: one missile inside the blast, one far away, and one explosion already burning")
    assert_ok("g22a-assert-incoming-list", "IncomingList", sky.state()["incoming_list"],
              "the pinned sky, exactly as forced (x,y,tx,ty,k,dur,x0,y0 per missile)")
    assert_ok("g22b-assert-blast-list", "ExplosionList", sky.state()["blast_list"],
              "the pinned explosion and its remaining life")
    sky.step(1)
    exec_code("g23-sky-step", invoke("StepFrames(1)"), "one step: the explosion resolves, both missiles move")
    assert_ok("g23a-assert-incoming-list", "IncomingList", sky.state()["incoming_list"],
              "only the far missile survived: Python computes the same list (%s)" % sky.state()["incoming_list"])
    assert_ok("g23b-assert-destroyed", "Destroyed", sky.state()["destroyed"],
              "the missile inside the %d-pixel radius was destroyed" % EXPLOSION_RADIUS)
    assert_ok("g23c-assert-score", "Score", sky.state()["score"],
              "one kill is worth %d points" % POINTS_PER_KILL)
    assert_ok("g23d-assert-blasts", "ExplosionsActive", sky.state()["blasts_active"],
              "and the explosion is still burning")
    assert_ok("g23e-assert-blast-life", "ExplosionList", sky.state()["blast_list"],
              "one step older: %s" % sky.state()["blast_list"])

    # --- the interceptor: a launch, a flight, an explosion -----------------------
    shot_plan = MSim()
    shot_plan.force(cities=[1, 1, 1, 1, 1, 1], ammo=[10, 10, 10], wave=1, maxwave=3, left=0,
                    incoming=[(310, 540, 320, 548, 0, 30)])
    # The lead: the point on the missile's own trajectory that the interceptor can reach in exactly
    # the number of steps the missile needs to get there. The fixed point is computed here, and the
    # two numbers the session uses come out of it -- so the shot is aimed by arithmetic, not by luck.
    target = shot_plan.incoming[0]
    lead = 0
    point = (target[0], target[1])
    for _ in range(40):
        point = (pos_at(target[6], target[2], lead, target[5]), pos_at(target[7], target[3], lead, target[5]))
        pick = min(range(len(BATTERY_XS)), key=lambda i: (abs(BATTERY_XS[i] - point[0]), i))
        span = max(abs(point[0] - BATTERY_XS[pick]), abs(point[1] - BATTERY_Y))
        duration = max(1, -(-span // INTERCEPTOR_SPEED))
        if duration == lead:
            break
        lead = duration
    exec_code("g24-shot-setup",
              force("cities=1,1,1,1,1,1;ammo=10,10,10;wave=1;maxwave=3;left=0;seed=1;"
                    "incoming=310,540,320,548,0,30"),
              "one pinned missile, thirty steps from its target")
    shot_plan.fire(point[0], point[1])
    exec_code("g25-shot-fire", invoke("Fire(%d, %d)" % (point[0], point[1])),
              "fire at (%d,%d): the point on the missile's trajectory that the interceptor reaches in "
              "the same number of steps (%d), so the explosion forms where the missile will be" % (point[0], point[1], lead))
    assert_ok("g25a-assert-interceptor-list", "InterceptorList", shot_plan.state()["interceptor_list"],
              "the interceptor's whole trajectory is in the answer (Python computes the same launch)")
    assert_ok("g25b-assert-fired", "Fired", shot_plan.state()["fired"], "one interceptor is in the air")
    assert_ok("g25c-assert-ammo", "Ammo", shot_plan.state()["ammo"], "and the battery paid one shot")
    assert_ok("g25d-assert-ammo-list", "AmmoList", shot_plan.state()["ammo_list"], "the battery that fired is the busy one")
    duration_shot = shot_plan.interceptors[0][5]
    shot_plan.step(duration_shot)
    exec_code("g26-shot-flight", invoke("StepFrames(%d)" % duration_shot),
              "let the interceptor fly the %d steps the launch computed" % duration_shot)
    assert_ok("g26a-assert-interceptor-none", "InterceptorAlive", shot_plan.state()["interceptor_alive"],
              "it arrived, so it is no longer in flight")
    assert_ok("g26b-assert-blast-list", "ExplosionList", shot_plan.state()["blast_list"],
              "and it became an explosion exactly where it was sent")
    assert_ok("g26c-assert-destroyed", "Destroyed", shot_plan.state()["destroyed"],
              "the missile it was aimed at was inside that explosion")
    assert_ok("g26d-assert-leaked", "Leaked", shot_plan.state()["leaked"],
              "and nothing reached the cities")
    assert_ok("g26e-assert-score", "Score", shot_plan.state()["score"],
              "score %d before the wave bookkeeping" % shot_plan.state()["score"])
    assert_ok("g26f-assert-wave", "Wave", shot_plan.state()["wave"],
              "the sky is clear, so the wave advanced (Python: wave %d)" % shot_plan.state()["wave"])
    assert_ok("g26g-assert-ammo-refilled", "AmmoList", shot_plan.state()["ammo_list"],
              "and the next wave refilled every battery")

    # --- a launch with no ammo, and a launch out of bounds ------------------------
    exec_code("g27-nothing-setup", force("cities=1,1,1,1,1,1;ammo=0,0,0;wave=1;maxwave=3;left=0;seed=1"),
              "every battery empty")
    exec_code("g28-fire-no-ammo", invoke("Fire(400, 300)"), "a shot with no shots left")
    assert_ok("g28a-assert-fired-still", "Fired", 0, "the refused shot fired nothing")
    exec_code("g29-fire-outside", invoke("Fire(900, 900)"), "a shot at a point outside the playfield")
    assert_ok("g29a-assert-fired-still", "Fired", 0, "and neither did that one")

    # --- an incoming missile takes a city ----------------------------------------
    hit = MSim()
    hit.force(cities=[1, 1, 1, 1, 1, 1], ammo=[10, 10, 10], wave=1, maxwave=3, left=0,
              incoming=[(320, 540, 320, 548, 0, 1)])
    hit.step(1)
    exec_code("g30-city-setup",
              force("cities=1,1,1,1,1,1;ammo=10,10,10;wave=1;maxwave=3;left=0;seed=1;"
                    "incoming=320,540,320,548,0,1"),
              "one missile one step from the third city")
    exec_code("g31-city-step", invoke("StepFrames(1)"), "one step: it arrives")
    assert_ok("g31a-assert-leaked", "Leaked", hit.state()["leaked"], "one missile got through")
    assert_ok("g31b-assert-cities", "CitiesAlive", hit.state()["cities"], "and the city is gone")
    assert_ok("g31c-assert-city-list", "CityList", hit.state()["city_list"],
              "the list names exactly which one: %s" % hit.state()["city_list"])
    assert_ok("g31d-assert-cities-lost", "CitiesLost", hit.state()["cities_lost"], "one city lost")
    assert_ok("g31e-assert-incoming-none", "IncomingAlive", hit.state()["incoming_alive"], "the sky is empty")
    assert_ok("g31f-assert-hook-applied", "LastHookSteps", 1, "the hook's own property is what it applied")

    # --- losing every city ---------------------------------------------------------
    dead = MSim()
    pinned = "|".join("%d,547,%d,548,0,1" % (x, x) for x in CITY_XS)
    dead.force(cities=[1, 1, 1, 1, 1, 1], ammo=[10, 10, 10], wave=1, maxwave=3, left=0,
               incoming=[(x, 547, x, 548, 0, 1) for x in CITY_XS])
    dead_applied = dead.step(3)
    exec_code("g32-lose-setup",
              force("cities=1,1,1,1,1,1;ammo=10,10,10;wave=1;maxwave=3;left=0;seed=1;incoming=%s" % pinned),
              "six missiles, each one step from a different city")
    exec_code("g33-lose-step", invoke("StepFrames(3)"), "three steps: they all arrive")
    assert_ok("g33a-assert-cities-zero", "CitiesAlive", dead.state()["cities"], "no city is left")
    assert_ok("g33b-assert-over", "GameOver", dead.state()["over"], "so the game is over")
    assert_ok("g33c-assert-not-won", "Won", dead.state()["won"], "and it was not won")
    assert_ok("g33d-assert-hook-applied", "LastHookSteps", dead_applied,
              "the hook stopped at the end: %d of the three steps ran" % dead_applied)
    exec_code("g34-fire-after-lose", invoke("Fire(400, 300)"), "a shot after the game ended")
    assert_ok("g34a-assert-fired-still", "Fired", 0, "refused: nothing was fired")
    shot("g35-shot-lost", "mc-t1", "the lost field: the status label and six ruined cities")

    # --- winning: the last wave cleared with cities standing ------------------------
    win = MSim()
    win.force(cities=[1, 1, 1, 1, 1, 0], ammo=[10, 10, 10], wave=1, maxwave=1, left=0)
    win_applied = win.step(1)
    exec_code("g36-win-setup",
              force("cities=1,1,1,1,1,0;ammo=10,10,10;wave=1;maxwave=1;left=0;seed=1"),
              "the last wave, already spawned out and intercepted; five cities stand")
    exec_code("g37-win-step", invoke("StepFrames(1)"), "one step: the wave-end check runs")
    assert_ok("g37a-assert-won", "Won", win.state()["won"], "the game is won")
    assert_ok("g37b-assert-over", "GameOver", win.state()["over"], "and it ended")
    assert_ok("g37c-assert-score", "Score", win.state()["score"],
              "the wave bonus pays %d per surviving city (Python: %d)" % (POINTS_PER_CITY, win.state()["score"]))
    assert_ok("g37d-assert-cities", "CitiesAlive", win.state()["cities"], "five cities survived")
    assert_ok("g37e-assert-hook-applied", "LastHookSteps", win_applied, "the hook applied its one step")
    shot("g38-shot-won", "mc-t2", "the won field: the status label and the surviving cities")
    call("g39-assert-screen-win", "game", "running_game_assert_screen_text", {"text": "SECTOR SAVED"},
         "the status label really is on the captured screen")

    # --- the input edge -------------------------------------------------------------
    edge = MSim()
    edge.force(cities=[1, 1, 1, 1, 1, 1], ammo=[10, 10, 10], wave=1, maxwave=3, left=3,
               incoming=[(300, 200, 320, 548, 0, 60)])
    exec_code("g40-input-setup",
              force("cities=1,1,1,1,1,1;ammo=10,10,10;wave=1;maxwave=3;left=3;seed=1;"
                    "incoming=300,200,320,548,0,60"),
              "a pinned sky for the declared-input scenario")
    exec_code("g41-poll-on", invoke("SetPollInput(true)"), "start listening to the declared action")
    call("g42-input-fire", "game", "running_game_run_test_scenario",
         {"steps": [{"type": "input", "action": "mc_auto_fire", "pressed": True},
                    {"type": "wait", "seconds": 0.45},
                    {"type": "assert", "node_path": "Main", "property": "Fired", "operator": "gte",
                     "expected": 1}]},
         "the declared action really fires (a press edge, so exactly one shot)")
    edge.fire(300, 200)
    assert_ok("g43-assert-input-shots", "InputShots", 1, "the edge fired exactly once")
    assert_ok("g44-assert-fired", "Fired", edge.state()["fired"], "and a shot really left a battery")
    assert_ok("g45-assert-ammo", "Ammo", edge.state()["ammo"], "the battery paid for it")
    assert_ok("g46-assert-interceptor", "InterceptorAlive", edge.state()["interceptor_alive"],
              "the interceptor is in the air")
    exec_code("g47-poll-off", invoke("SetPollInput(false)"), "stop listening again")

    # --- the clock: multi-frame sampling with a must-move assertion ------------------
    clock = MSim()
    clock.force(cities=[1, 1, 1, 1, 1, 1], ammo=[10, 10, 10], wave=1, maxwave=3)
    exec_code("g48-clock-setup",
              force("cities=1,1,1,1,1,1;ammo=10,10,10;wave=1;maxwave=3;seed=%d" % SEED),
              "a fresh, playable state for the clock to move")
    assert_ok("g49-assert-clock-steps-0", "Steps", 0, "the clock is off, so nothing has moved yet")
    exec_code("g50-clock-on", invoke("SetAutoClock(60.0)"),
              "the clock ticks 60 times a second (a float accumulator, F-1's fix)")
    samples("g51-samples-clock", ["Steps", "Spawned", "IncomingAlive", "CitiesAlive", "Score", "Elapsed", "Ticks"],
            30, "thirty frames with the clock running: the simulation facts, the spawn counter, Elapsed and Ticks")
    assert_state("g52-assert-clock-moved", "Steps", "gt", 0,
                 "MUST MOVE: if the clock is frozen this assertion FAILS (the M3-4 lesson)")
    assert_state("g53-assert-clock-spawned", "Spawned", "gt", 0,
                 "MUST SPAWN: a live clock has to launch missiles")
    assert_state("g54-assert-clock-auto-ticks", "AutoTicks", "gte", 1, "the clock applied at least one step")
    exec_code("g55-clock-off", invoke("SetAutoClock(0.0)"), "stop the clock")
    assert_ok("g56-assert-clock-off-auto", "LastAutoSteps", 0, "with the clock off the frame contributes nothing")
    shot("g57-shot-clock", "mc-t3", "the field after the clock ran")

    # --- the two producers, two properties -------------------------------------------
    hook = MSim()
    hook.force(cities=[1, 1, 1, 1, 1, 1], ammo=[10, 10, 10], wave=1, maxwave=3, left=3,
               incoming=[(300, 200, 320, 548, 0, 60)])
    exec_code("g58-hook-setup",
              force("cities=1,1,1,1,1,1;ammo=10,10,10;wave=1;maxwave=3;left=3;seed=1;"
                    "incoming=300,200,320,548,0,60"),
              "a pinned state again")
    hook.step(3)
    exec_code("g59-hook-step-3", invoke("StepFrames(3)"), "three hook steps")
    assert_ok("g60-assert-hook-3", "LastHookSteps", 3, "the hook's own property")
    assert_ok("g61-assert-steps-3", "Steps", hook.state()["steps"], "the simulation moved three steps")
    samples("g62-samples-quiet", ["Steps", "IncomingList", "Elapsed", "Ticks"], 12,
            "the clock is off, so the frame loop advances Elapsed and Ticks and nothing else")
    assert_ok("g63-assert-hook-still-3", "LastHookSteps", 3,
              "after twelve frames the hook's property is STILL 3: the clock never writes it (the G1 lesson)")
    assert_ok("g64-assert-auto-0", "LastAutoSteps", 0, "while the clock's own property is 0")
    assert_ok("g65-assert-still-no-auto", "AutoTicks", 0, "and it applied nothing at all")
    assert_ok("g66-assert-steps-still", "Steps", hook.state()["steps"], "the simulation did not move on its own")

    # --- the final readback, the scene tree, and one declared boundary ---------------
    exec_code("g67-final-readback", invoke("Dump()"),
              "the final state on one line: every counter this session asserted")
    shot("g68-shot-final", "mc-t4", "the final frame")
    call("g69-final-tree", "game", "running_game_get_scene_tree", {},
         "the final tree: every node name is one this game made, no @-auto names")
    assert_state("g70-assert-boundary", "NoSuchPropertyAtAll", "eq", 0,
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
    # `actual` every call really reported.
    manifest = []
    for entry in CALLS:
        if entry.get("tool") != "running_game_assert_node_state":
            continue
        args = entry["arguments"]
        manifest.append({"tag": entry["tag"], "property": args["property"],
                         "operator": args["operator"], "expected": args["expected"],
                         "declared_boundary": args["property"].startswith("NoSuchProperty")})
    manifest_path = os.path.join(HERE, "expectations-missilecommand.json")
    with io.open(manifest_path, "w", encoding="utf-8", newline="\n") as handle:
        json.dump(manifest, handle, ensure_ascii=False, indent=1)
        handle.write("\n")
    editor = len([c for c in CALLS if c["port"] == "editor"])
    game = len([c for c in CALLS if c["port"] == "game"])
    print("wrote %s" % OUT)
    print("calls: %d (editor %d / game %d)" % (len(CALLS), editor, game))
    print("expectations: %d -> %s" % (len(manifest), manifest_path))
    with io.open(OUT, "r", encoding="utf-8") as handle:
        again = json.load(handle)
    assert len(again["calls"]) == len(CALLS)
    print("json round-trip: OK (%d calls)" % len(again["calls"]))
    return 0


if __name__ == "__main__":
    sys.exit(main())
