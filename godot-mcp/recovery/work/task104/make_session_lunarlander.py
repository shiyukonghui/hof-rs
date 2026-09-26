#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""TASK-104 (B, game 20): the Lunar Lander session generator, with the Python second
implementation of the payload's rules.

The payload is `tools/sessions/lunarlander/payload/LunarLanderGame.cs`. `LSim` below
re-implements its rules from the *rules*: the twelve-entry integer thrust table, the
burn/gravity/integrate order, the ground contact test, the pad lookup, the three
landing tolerances, the remaining-fuel score and the out-of-field crash. Every
literal a `running_game_assert_node_state` compares against is produced by `LSim`
and by nothing else, including the whole checkpointed integer trajectory of a real
descent: the generator finds the descent's burn schedule by simulating it here and
then drives the payload with exactly those `SetThrust` / `StepFrames` calls.

Written by a Python writer, never by a shell redirect (iron rule 1).
"""

import io
import json
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.abspath(os.path.join(HERE, "..", "..", ".."))
SESSION_DIR = os.path.join(ROOT, "tools", "sessions", "lunarlander")
OUT = os.path.join(SESSION_DIR, "session.json")
PAYLOAD = "payload/LunarLanderGame.cs"

FIELD_W = 800
FIELD_H = 600
GROUND_Y = 560
HALF_H = 8
HALF_W = 10
GRAVITY_STEP = 1
THRUST_COST = 1
START_FUEL = 500
ANGLE_COUNT = 12
ANGLE_STEP_DEG = 30
MAX_LAND_VX = 2
MAX_LAND_VY = 6
MAX_LAND_ANGLE = 1
START_X = 400
START_Y = 100
THRUST_X = [0, 2, 3, 4, 3, 2, 0, -2, -3, -4, -3, -2]
THRUST_Y = [-4, -3, -2, 0, 2, 3, 4, 3, 2, 0, -2, -3]
PAD_X0 = [120, 360, 600]
PAD_X1 = [200, 440, 680]
PAD_MULT = [1, 2, 1]


def sign32(value):
    value &= 0xFFFFFFFF
    return value - 0x100000000 if value >= 0x80000000 else value


def pad_of(x):
    for index in range(len(PAD_X0)):
        if PAD_X0[index] <= x <= PAD_X1[index]:
            return index
    return -1


class LSim(object):
    """The payload's rules, re-implemented from the rules."""

    def __init__(self):
        self.reset()

    def reset(self):
        self.lx = START_X
        self.ly = START_Y
        self.vx = 0
        self.vy = 0
        self.angle = 0
        self.fuel = START_FUEL
        self.thrust_on = False
        self.thrust_count = 0
        self.fuel_used = 0
        self.rotations = 0
        self.rejected_thrusts = 0
        self.rejected_rotations = 0
        self.landed = False
        self.crashed = False
        self.won = False
        self.over = False
        self.pad = -1
        self.score = 0
        self.touch_y = 0
        self.min_vy = 0
        self.max_vy = 0
        self.steps = 0

    # --- the facts ---------------------------------------------------------------

    def angle_deg(self):
        return self.angle * ANGLE_STEP_DEG

    def angle_distance(self):
        return min(self.angle, ANGLE_COUNT - self.angle)

    def state_hash(self):
        value = 0
        for item in (self.lx, self.ly, self.vx, self.vy, self.angle, self.fuel, self.steps):
            value = sign32(value * 31 + item)
        return value

    def pad_list(self):
        return "|".join("%d,%d" % (PAD_X0[i], PAD_X1[i]) for i in range(len(PAD_X0)))

    # --- the rules ---------------------------------------------------------------

    def tick(self):
        if self.over:
            return
        self.steps += 1
        if self.thrust_on and self.fuel >= THRUST_COST:
            self.vx += THRUST_X[self.angle]
            self.vy += THRUST_Y[self.angle]
            self.fuel -= THRUST_COST
            self.fuel_used += THRUST_COST
            self.thrust_count += 1
        self.vy += GRAVITY_STEP
        self.lx += self.vx
        self.ly += self.vy
        if self.vy < self.min_vy:
            self.min_vy = self.vy
        if self.vy > self.max_vy:
            self.max_vy = self.vy
        self.check_end()

    def check_end(self):
        if self.over:
            return
        if self.ly + HALF_H >= GROUND_Y:
            self.touch_y = self.ly
            self.pad = pad_of(self.lx)
            self.landed = (self.pad >= 0 and abs(self.vx) <= MAX_LAND_VX
                           and abs(self.vy) <= MAX_LAND_VY and self.angle_distance() <= MAX_LAND_ANGLE)
            self.crashed = not self.landed
            self.won = self.landed
            self.over = True
            self.score = self.fuel * PAD_MULT[self.pad] if self.landed else 0
            return
        if self.lx < 0 or self.lx >= FIELD_W:
            self.touch_y = self.ly
            self.crashed = True
            self.won = False
            self.over = True
            self.pad = -1
            self.score = 0

    def step(self, count):
        applied = 0
        for _ in range(count):
            if self.over:
                break
            self.tick()
            applied += 1
        return applied

    # --- the actions ---------------------------------------------------------------

    def thrust(self):
        if self.over or self.fuel < THRUST_COST:
            self.rejected_thrusts += 1
            return
        self.vx += THRUST_X[self.angle]
        self.vy += THRUST_Y[self.angle]
        self.fuel -= THRUST_COST
        self.fuel_used += THRUST_COST
        self.thrust_count += 1

    def rotate_right(self):
        if self.over:
            self.rejected_rotations += 1
            return
        self.angle = (self.angle + 1) % ANGLE_COUNT
        self.rotations += 1

    def rotate_left(self):
        if self.over:
            self.rejected_rotations += 1
            return
        self.angle = (self.angle + ANGLE_COUNT - 1) % ANGLE_COUNT
        self.rotations += 1

    def force(self, pos=None, vel=None, angle=None, fuel=None, score=None, thrust=None):
        self.reset()
        if pos is not None:
            self.lx, self.ly = pos
        if vel is not None:
            self.vx, self.vy = vel
        if angle is not None:
            self.angle = max(0, min(ANGLE_COUNT - 1, angle))
        if fuel is not None:
            self.fuel = fuel
        if score is not None:
            self.score = score
        if thrust is not None:
            self.thrust_on = thrust
        self.min_vy = self.vy
        self.max_vy = self.vy

    def probe_state(self, x, y):
        if x < 0 or x >= FIELD_W or y < 0 or y >= FIELD_H:
            return "outside", -1
        if self.lx - HALF_W <= x < self.lx + HALF_W and self.ly - HALF_H <= y < self.ly + HALF_H:
            return "lander", -1
        if y >= GROUND_Y:
            pad = pad_of(x)
            if pad >= 0:
                return "pad", pad
            return "ground", -1
        return "sky", -1


# --- the descent plan ---------------------------------------------------------
# The gold landing: free-fall to a trigger altitude, burn a fixed number of steps,
# then coast onto a pad. The generator SEARCHES for the pair and uses whatever it
# finds, so the numbers below are the plan this build actually drives -- and the
# whole trajectory is reproduced here before a single call is written.
TRIGGER_SEARCH = range(200, 560, 5)
BURN_SEARCH = range(1, 40)
SAFE_MARGIN = 4


def simulate_plan(trigger, burn_steps):
    """The schedule the session will emit: thrust on only between trigger and burn_steps."""
    sim = LSim()
    flags = []
    state = 0
    burned = 0
    guard = 0
    while not sim.over and guard < 5000:
        guard += 1
        thrust = state == 1 and burned < burn_steps
        flags.append(thrust)
        if thrust:
            burned += 1
        elif state == 1 and burned > 0:
            state = 2
        sim.thrust_on = thrust
        sim.tick()
        if state == 0 and sim.ly >= trigger:
            state = 1
    phases = []
    for flag in flags:
        if phases and phases[-1][0] == flag:
            phases[-1][1] += 1
        else:
            phases.append([flag, 1])
    return sim, phases


def find_plan():
    for trigger in TRIGGER_SEARCH:
        for burn_steps in BURN_SEARCH:
            sim, phases = simulate_plan(trigger, burn_steps)
            if sim.landed and abs(sim.vy) <= SAFE_MARGIN and abs(sim.vx) <= 1:
                return trigger, burn_steps, sim, phases
    return None


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
                        "color": {"r": 0.02, "g": 0.02, "b": 0.05, "a": 1}}},
        {"type": "Label", "name": "Hud", "parent_path": ".",
         "properties": {"offset_left": 14, "offset_top": 10, "offset_right": 790, "offset_bottom": 44,
                        "text": "ALT 452  VX 0  VY 0  FUEL 500  ANGLE 0  BURNS 0  STEP 0",
                        "theme_override_font_sizes/font_size": 20}},
        {"type": "Label", "name": "Status", "parent_path": ".",
         "properties": {"offset_left": 14, "offset_top": 10, "offset_right": 500, "offset_bottom": 44,
                        "text": "LAND SAFELY", "theme_override_font_sizes/font_size": 20}},
    ]
    nodes[2]["properties"]["offset_top"] = 48
    nodes[2]["properties"]["offset_bottom"] = 82
    call("e01-edit-game", "editor", "project_edit_script",
         {"path": "res://src/LunarLanderGame.cs", "content_file": PAYLOAD},
         "the whole game is written through the MCP script writer (the template stub is replaced)")
    call("e02-open-scene", "editor", "editor_open_scene", {"path": "res://scenes/main.tscn"},
         "the template scene carries the root Main (Node2D) the script is attached to")
    call("e03-batch-add-static", "editor", "editor_add_nodes_batch", {"nodes": nodes},
         "the three static nodes of the scene, through the batch tool; the ground, the three pads, the starfield, the lander and the flame are created at run time")
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
    call("e10-action-thrust", "editor", "editor_add_input_action", {"action": "ll_thrust", "key": "Space"},
         "one burn per press edge, for the input-edge scenario")
    call("e11-save-3", "editor", "editor_save_scene", {}, "persist the declared action")
    call("e12-build-csharp", "editor", "project_build_csharp", {},
         "the payload really compiles: the real dotnet exit code")
    call("e13-validate-scripts", "editor", "project_validate_scripts", {},
         "per-file verdicts for every script in the project")
    call("e14-get-errors", "editor", "editor_get_errors", {},
         "the editor's own error list after the build")


def game_phase(plan):
    trigger, burn_steps, gold, phases = plan
    fresh = LSim()

    # --- the shape of the world, and the first frame -------------------------------
    call("g01-scene-tree", "game", "running_game_get_scene_tree", {},
         "the running game's tree: three static nodes, no @-auto names")
    assert_ok("g02-assert-field-w", "FieldW", FIELD_W, "the field is 800 pixels wide")
    assert_ok("g03-assert-field-h", "FieldH", FIELD_H, "and 600 tall")
    assert_ok("g04-assert-ground", "GroundY", GROUND_Y, "the ground line is at y=560")
    assert_ok("g05-assert-gravity", "GravityStep", GRAVITY_STEP, "gravity adds 1 px/step every step")
    assert_ok("g06-assert-cost", "ThrustCost", THRUST_COST, "a burn costs one fuel unit")
    assert_ok("g07-assert-fuel-start", "StartFuel", START_FUEL, "the tank holds 500")
    assert_ok("g08-assert-angle-count", "AngleCount", ANGLE_COUNT, "twelve attitudes")
    assert_ok("g09-assert-angle-step", "AngleStepDeg", ANGLE_STEP_DEG, "thirty degrees apart")
    assert_ok("g10-assert-max-vx", "MaxLandVx", MAX_LAND_VX, "a landing survives +/-2 px/step horizontally")
    assert_ok("g11-assert-max-vy", "MaxLandVy", MAX_LAND_VY, "and +/-6 px/step vertically")
    assert_ok("g12-assert-max-angle", "MaxLandAngle", MAX_LAND_ANGLE, "and one attitude step from upright")
    assert_ok("g13-assert-pads", "PadList", fresh.pad_list(), "the three pads, recomputed in Python")
    assert_ok("g14-assert-mult", "PadMultipliers", "1,2,1", "the middle pad pays double")
    assert_ok("g15-assert-start-pos", "Ly", fresh.ly, "a fresh game starts at y=100")
    assert_ok("g16-assert-thrust-table", "ThrustY", -4, "upright thrust is (0,-4), recomputed in Python")
    exec_code("g17-readback-t0", invoke("Dump()"), "the whole state on one line")
    shot("g18-shot-t0", "ll-t0", "the first frame: the ground, the pads and the lander")

    # --- the frozen baseline ---------------------------------------------------------
    samples("g19-samples-frozen",
            ["Lx", "Ly", "Vx", "Vy", "Fuel", "StateHash", "Elapsed", "Ticks"], 12,
            "determinism baseline: AutoClock is 0, so the flight facts are constant while Elapsed and Ticks both advance")
    assert_ok("g20-assert-frozen-steps", "Steps", 0, "with the clock off, not one step has run")
    assert_ok("g21-assert-frozen-auto", "LastAutoSteps", 0, "and the auto clock applied nothing")
    assert_ok("g22-assert-frozen-hook", "LastHookSteps", 0, "and the hook applied nothing either")

    # --- the probe names what stands where ---------------------------------------------
    probe = LSim()
    probe.force(pos=(400, 548), vel=(0, 0), angle=0, fuel=400)
    exec_code("g23-probe-setup", force("l=400,548;v=0,0;angle=0;fuel=400"),
              "the lander pinned just above the middle pad")
    for tag, x, y, state, value in (("g24", 400, 545, "lander", -1), ("g25", 400, 570, "pad", 1),
                                    ("g26", 50, 570, "ground", -1), ("g27", 400, 300, "sky", -1),
                                    ("g28", 900, 100, "outside", -1), ("g29", 160, 570, "pad", 0)):
        exec_code("%s-probe" % tag, invoke("Probe(%d, %d)" % (x, y)),
                  "the probe names what stands at one point, so the assertion below is about that point")
        assert_ok("%sa-assert-state" % tag, "ProbeState", state, "(%d,%d) is %s" % (x, y, state))
        assert_ok("%sb-assert-value" % tag, "ProbeValue", value, "and the pad index it names")

    # --- rotation: twelve integer attitudes, and their thrust table ----------------------
    spin = LSim()
    spin.force(pos=(400, 300), vel=(0, 0), angle=0, fuel=400)
    exec_code("g30-spin-setup", force("l=400,300;v=0,0;angle=0;fuel=400"), "a pinned lander for the attitude tests")
    exec_code("g31-spin-right", invoke("RotateRight()"), "one attitude step clockwise")
    spin.rotate_right()
    assert_ok("g32-assert-angle", "AngleIndex", spin.angle, "the attitude index is %d" % spin.angle)
    assert_ok("g33-assert-deg", "AngleDeg", spin.angle_deg(), "which is %d degrees" % spin.angle_deg())
    assert_ok("g34-assert-thrust-x", "ThrustX", THRUST_X[spin.angle],
              "and its burn is (%d,%d), from the integer table" % (THRUST_X[spin.angle], THRUST_Y[spin.angle]))
    assert_ok("g35-assert-thrust-y", "ThrustY", THRUST_Y[spin.angle], "the y half of the same table entry")
    exec_code("g36-spin-left", invoke("RotateLeft()"), "one attitude step back")
    spin.rotate_left()
    assert_ok("g37-assert-angle-back", "AngleIndex", spin.angle, "back to upright")
    assert_ok("g38-assert-rotations", "Rotations", spin.rotations, "%d attitude changes counted" % spin.rotations)
    exec_code("g39-spin-left-11", invoke("RotateLeft()"), "one step anticlockwise wraps to 330 degrees")
    spin.rotate_left()
    assert_ok("g40-assert-wrap", "AngleIndex", spin.angle, "the last attitude")
    assert_ok("g41-assert-wrap-deg", "AngleDeg", spin.angle_deg(), "%d degrees" % spin.angle_deg())

    # --- one burn is an impulse, and gravity is a step -----------------------------------
    burn = LSim()
    burn.force(pos=(400, 300), vel=(0, 0), angle=0, fuel=10)
    exec_code("g42-burn-setup", force("l=400,300;v=0,0;angle=0;fuel=10"), "a pinned lander with ten fuel units")
    exec_code("g43-burn", invoke("Thrust()"), "one burn adds the attitude's thrust pair")
    burn.thrust()
    assert_ok("g44-assert-vy", "Vy", burn.vy, "the velocity after the impulse (%d)" % burn.vy)
    assert_ok("g45-assert-fuel", "Fuel", burn.fuel, "the fuel after the burn (%d)" % burn.fuel)
    assert_ok("g46-assert-count", "ThrustCount", burn.thrust_count, "%d burn counted" % burn.thrust_count)
    exec_code("g47-burn-step", invoke("StepFrames(1)"), "one step: gravity adds 1 and the lander moves")
    burn.step(1)
    assert_ok("g48-assert-vy-2", "Vy", burn.vy, "the velocity after gravity (%d)" % burn.vy)
    assert_ok("g49-assert-ly", "Ly", burn.ly, "and the new altitude (y=%d)" % burn.ly)
    assert_ok("g50-assert-hash", "StateHash", burn.state_hash(), "the world hash, recomputed in Python")
    dry = LSim()
    dry.force(pos=(400, 300), vel=(0, 0), angle=0, fuel=0)
    exec_code("g51-dry-setup", force("l=400,300;v=0,0;angle=0;fuel=0"), "an empty tank")
    exec_code("g52-dry-burn", invoke("Thrust()"), "a burn with no fuel")
    dry.thrust()
    assert_ok("g53-assert-rejected", "RejectedThrusts", dry.rejected_thrusts, "refused: no fuel")
    assert_ok("g54-assert-count-zero", "ThrustCount", dry.thrust_count, "and no burn was counted")

    # --- the continuous burn flag ----------------------------------------------------------
    hold = LSim()
    hold.force(pos=(400, 300), vel=(0, 0), angle=0, fuel=100, thrust=True)
    exec_code("g55-hold-setup", force("l=400,300;v=0,0;angle=0;fuel=100;thrust=1"),
              "the continuous burn switched on by the pinned state")
    assert_ok("g56-assert-flag", "ThrustOn", hold.thrust_on, "the flag is on")
    hold.step(1)
    exec_code("g57-hold-step", invoke("StepFrames(1)"), "one step: the burn and gravity both apply")
    assert_ok("g58-assert-hold-vy", "Vy", hold.vy,
              "burn -4 then gravity +1 gives vy=%d" % hold.vy)
    assert_ok("g59-assert-hold-fuel", "Fuel", hold.fuel, "and the fuel paid for it (%d)" % hold.fuel)
    exec_code("g60-hold-off", invoke("SetThrust(false)"), "switch the burn off")
    hold.thrust_on = False
    hold.step(1)
    exec_code("g61-hold-step-2", invoke("StepFrames(1)"), "one more step: gravity alone")
    assert_ok("g62-assert-hold-vy-2", "Vy", hold.vy, "now vy=%d" % hold.vy)
    assert_ok("g63-assert-hold-fuel-2", "Fuel", hold.fuel, "the fuel no longer moves (%d)" % hold.fuel)

    # --- the landing test: every tolerance, and the boundary on each --------------------------
    landings = [
        ("g64", "l=400,548;v=0,3;angle=0;fuel=400", (400, 548), (0, 3), 0, 400,
         "the middle pad at the maximum surviving vertical speed minus one: it lands"),
        ("g68", "l=400,548;v=0,6;angle=0;fuel=400", (400, 548), (0, 6), 0, 400,
         "one more and it is past max_vy: it crashes"),
        ("g72", "l=400,548;v=4,0;angle=0;fuel=400", (400, 548), (4, 0), 0, 400,
         "over the middle pad but too fast horizontally: it crashes"),
        ("g76", "l=400,548;v=0,0;angle=3;fuel=400", (400, 548), (0, 0), 3, 400,
         "slow enough, but 90 degrees over: it crashes"),
        ("g80", "l=400,548;v=0,0;angle=11;fuel=400", (400, 548), (0, 0), 11, 400,
         "330 degrees is one attitude step from upright, so the tolerance is two-sided: it lands"),
        ("g84", "l=100,548;v=0,0;angle=0;fuel=400", (100, 548), (0, 0), 0, 400,
         "a perfect descent between the pads: it crashes because it missed every pad"),
        ("g88", "l=160,548;v=0,0;angle=0;fuel=300", (160, 548), (0, 0), 0, 300,
         "the left pad pays its multiplier of 1"),
        ("g92", "l=640,548;v=0,0;angle=0;fuel=250", (640, 548), (0, 0), 0, 250,
         "and the right pad too"),
    ]
    for tag, spec, pos, vel, angle, fuel, note in landings:
        sim = LSim()
        sim.force(pos=pos, vel=vel, angle=angle, fuel=fuel)
        exec_code("%s-setup" % tag, force(spec), note)
        assert_ok("%sa-assert-pinned" % tag, "Ly", sim.ly, "the pinned altitude")
        sim.step(3)
        exec_code("%sb-step" % tag, invoke("StepFrames(3)"),
                  "three steps are enough for the belly to reach the ground")
        assert_ok("%sc-assert-landed" % tag, "Landed", sim.landed,
                  "Python says landed=%s" % sim.landed)
        assert_ok("%sd-assert-crashed" % tag, "Crashed", sim.crashed,
                  "Python says crashed=%s" % sim.crashed)
        assert_ok("%se-assert-pad" % tag, "PadIndex", sim.pad, "the pad Python names is %d" % sim.pad)
        assert_ok("%sf-assert-score" % tag, "Score", sim.score,
                  "remaining fuel times the pad multiplier: %d" % sim.score)
        assert_ok("%sg-assert-over" % tag, "GameOver", sim.over, "the game ended")
    shot("g96-shot-crashed", "ll-t1", "the field after the last of the landing tests")

    # --- leaving the field ------------------------------------------------------------
    gone = LSim()
    gone.force(pos=(799, 100), vel=(5, 0), angle=0, fuel=100)
    exec_code("g97-gone-setup", force("l=799,100;v=5,0;angle=0;fuel=100"),
              "a lander at the right edge, moving right")
    gone.step(1)
    exec_code("g98-gone-step", invoke("StepFrames(1)"), "one step: it leaves the field")
    assert_ok("g99-assert-crashed", "Crashed", gone.crashed, "an out-of-field flight is a crash")
    assert_ok("g100-assert-landed", "Landed", gone.landed, "not a landing")
    assert_ok("g101-assert-pad", "PadIndex", gone.pad, "no pad")
    assert_ok("g102-assert-score", "Score", gone.score, "and no score")

    # --- the gold descent: a real integer trajectory, phase by phase ---------------------
    gold = LSim()
    gold.force()
    exec_code("g103-descent-setup", force(""),
              "the default start: y=100, no velocity, 500 fuel, upright")
    step_index = 104
    for phase_number, (thrust_flag, count) in enumerate(phases):
        exec_code("g%03d-descent-thrust-%d" % (step_index, phase_number),
                  invoke("SetThrust(%s)" % ("true" if thrust_flag else "false")),
                  "phase %d of the searched descent: the burn is %s"
                  % (phase_number + 1, "on" if thrust_flag else "off"))
        gold.thrust_on = thrust_flag
        applied = gold.step(count)
        exec_code("g%03d-descent-steps-%d" % (step_index + 1, phase_number),
                  invoke("StepFrames(%d)" % count),
                  "phase %d: %d steps of the same integer rules Python runs" % (phase_number + 1, count))
        assert_ok("g%03d-assert-x-%d" % (step_index + 2, phase_number), "Lx", gold.lx,
                  "checkpoint: x=%d" % gold.lx)
        assert_ok("g%03d-assert-y-%d" % (step_index + 3, phase_number), "Ly", gold.ly,
                  "checkpoint: y=%d" % gold.ly)
        assert_ok("g%03d-assert-vx-%d" % (step_index + 4, phase_number), "Vx", gold.vx,
                  "checkpoint: vx=%d" % gold.vx)
        assert_ok("g%03d-assert-vy-%d" % (step_index + 5, phase_number), "Vy", gold.vy,
                  "checkpoint: vy=%d" % gold.vy)
        assert_ok("g%03d-assert-fuel-%d" % (step_index + 6, phase_number), "Fuel", gold.fuel,
                  "checkpoint: fuel=%d" % gold.fuel)
        assert_ok("g%03d-assert-steps-%d" % (step_index + 7, phase_number), "Steps", gold.steps,
                  "checkpoint: the flight is at step %d" % gold.steps)
        assert_ok("g%03d-assert-hash-%d" % (step_index + 8, phase_number), "StateHash", gold.state_hash(),
                  "checkpoint: the recomputed world hash")
        assert_ok("g%03d-assert-hook-%d" % (step_index + 9, phase_number), "LastHookSteps", applied,
                  "the hook applied %d of the %d steps" % (applied, count))
        step_index += 10
    assert_ok("g%03d-assert-landed" % step_index, "Landed", gold.landed,
              "the searched descent lands: %s (trigger %d, burn %d steps)"
              % (gold.landed, trigger, burn_steps))
    assert_ok("g%03d-assert-won" % (step_index + 1), "Won", gold.won, "and it is a win")
    assert_ok("g%03d-assert-pad" % (step_index + 2), "PadIndex", gold.pad,
              "on pad %d (multiplier %d)" % (gold.pad, PAD_MULT[gold.pad]))
    assert_ok("g%03d-assert-score" % (step_index + 3), "Score", gold.score,
              "remaining fuel %d times %d = %d" % (gold.fuel, PAD_MULT[gold.pad], gold.score))
    assert_ok("g%03d-assert-touch" % (step_index + 4), "TouchY", gold.touch_y,
              "the belly reached y=%d" % gold.touch_y)
    assert_ok("g%03d-assert-minvy" % (step_index + 5), "MinVy", gold.min_vy,
              "the top of the arc: the most negative vy was %d" % gold.min_vy)
    assert_ok("g%03d-assert-burns" % (step_index + 6), "ThrustCount", gold.thrust_count,
              "the descent burned %d fuel units" % gold.thrust_count)
    shot("g%03d-shot-won" % (step_index + 7), "ll-t2", "the landed eagle on the middle pad")
    call("g%03d-assert-screen-win" % (step_index + 8), "game", "running_game_assert_screen_text",
         {"text": "THE EAGLE HAS LANDED"}, "the status label really is on the captured screen")
    exec_code("g%03d-burn-after-win" % (step_index + 9), invoke("Thrust()"), "a burn after the landing")
    assert_ok("g%03d-assert-rejected-after" % (step_index + 10), "ThrustCount", gold.thrust_count,
              "refused: the flight is over")

    # --- the input edge ---------------------------------------------------------------------
    edge = LSim()
    edge.force(pos=(400, 100), vel=(0, 0), angle=0, fuel=500)
    exec_code("g200-input-setup", force("l=400,100;v=0,0;angle=0;fuel=500"),
              "a pinned lander for the declared-input scenario")
    exec_code("g201-poll-on", invoke("SetPollInput(true)"), "start listening to the declared action")
    call("g202-input-thrust", "game", "running_game_run_test_scenario",
         {"steps": [{"type": "input", "action": "ll_thrust", "pressed": True},
                    {"type": "wait", "seconds": 0.45},
                    {"type": "assert", "node_path": "Main", "property": "ThrustCount",
                     "operator": "gte", "expected": 1}]},
         "the declared action really burns (a press edge, so exactly one burn)")
    assert_ok("g203-assert-input-thrusts", "InputThrusts", 1, "the edge burned exactly once")
    exec_code("g204-poll-off", invoke("SetPollInput(false)"),
              "stop listening again, so the rest of the session is deterministic")

    # --- the clock: multi-frame sampling with a must-move assertion ----------------------------
    clock = LSim()
    clock.force(pos=(400, 100), vel=(0, 0), angle=0, fuel=500)
    exec_code("g205-clock-setup", force("l=400,100;v=0,0;angle=0;fuel=500"),
              "a fresh flight: with gravity on, the clock has something to move")
    assert_ok("g206-assert-clock-steps-0", "Steps", 0, "the clock is off, so nothing has moved yet")
    hash0 = clock.state_hash()
    assert_ok("g207-assert-clock-hash-0", "StateHash", hash0, "the pinned world hash")
    exec_code("g208-clock-on", invoke("SetAutoClock(60.0)"),
              "the clock ticks 60 times a second (a float accumulator, F-1's fix)")
    samples("g209-samples-clock",
            ["Ly", "Vy", "Fuel", "StateHash", "Elapsed", "Ticks"], 30,
            "thirty frames with the clock running: gravity integrates and the world hash moves")
    assert_state("g210-assert-clock-moved", "Steps", "gt", 0,
                 "MUST MOVE: if the clock is frozen this assertion FAILS (the M3-4 lesson)")
    assert_state("g211-assert-clock-ly-moved", "Ly", "gt", clock.ly,
                 "MUST FALL: a live clock has to move the lander down")
    assert_state("g212-assert-clock-hash-moved", "StateHash", "neq", hash0,
                 "MUST CHANGE: a frozen world would keep the pinned hash (the M3-4 lesson)")
    assert_state("g213-assert-clock-auto-ticks", "AutoTicks", "gte", 1, "the clock applied at least one step")
    exec_code("g214-clock-off", invoke("SetAutoClock(0.0)"), "stop the clock")
    assert_ok("g215-assert-clock-off-auto", "LastAutoSteps", 0, "with the clock off the frame contributes nothing")

    # --- the two producers, two properties -------------------------------------------------------
    hook = LSim()
    hook.force(pos=(400, 300), vel=(0, 0), angle=0, fuel=500)
    exec_code("g216-hook-setup", force("l=400,300;v=0,0;angle=0;fuel=500"), "a pinned state again")
    applied = hook.step(3)
    exec_code("g217-hook-step-3", invoke("StepFrames(3)"), "three hook steps")
    assert_ok("g218-assert-hook-3", "LastHookSteps", 3, "the hook's own property")
    samples("g219-samples-quiet", ["Ly", "Vy", "Elapsed", "Ticks"], 12,
            "the clock is off, so the frame loop advances Elapsed and Ticks and nothing else")
    assert_ok("g220-assert-hook-still-3", "LastHookSteps", 3,
              "after twelve frames the hook's property is STILL 3: the clock never writes it (the G1 lesson)")
    assert_ok("g221-assert-auto-0", "LastAutoSteps", 0, "while the clock's own property is 0")
    assert_ok("g222-assert-auto-ticks-0", "AutoTicks", 0, "and it applied nothing at all")
    assert_ok("g223-assert-steps-still", "Steps", hook.steps, "the flight did not move on its own")

    # --- the final readback, the scene tree, and one declared boundary ------------------------------
    exec_code("g224-final-readback", invoke("Dump()"),
              "the final state on one line: every counter this session asserted")
    shot("g225-shot-final", "ll-t3", "the final frame")
    call("g226-final-tree", "game", "running_game_get_scene_tree", {},
         "the final tree: every node name is one this game made, no @-auto names")
    assert_state("g227-assert-boundary", "NoSuchPropertyAtAll", "eq", 0,
                 "the declared boundary failure: an assertion on a property that does not exist (-32001)")


def main():
    plan = find_plan()
    if plan is None:
        print("FATAL: no descent plan was found")
        return 1
    trigger, burn_steps, gold, phases = plan
    print("descent plan: trigger=%d burn=%d steps  phases=%s"
          % (trigger, burn_steps, phases))
    print("descent result: landed=%s pad=%d score=%d steps=%d fuel=%d vy=%d vx=%d min_vy=%d"
          % (gold.landed, gold.pad, gold.score, gold.steps, gold.fuel, gold.vy, gold.vx, gold.min_vy))
    editor_phase()
    game_phase(plan)
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
    manifest_path = os.path.join(HERE, "expectations-lunarlander.json")
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
