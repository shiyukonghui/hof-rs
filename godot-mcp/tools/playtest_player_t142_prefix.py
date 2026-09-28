#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""playtest_player.py -- TASK-132: the MODEL-PLAYER loop (image in -> action out -> inject -> watch).

What this tool is
-----------------
TASK-131's gate asked "does the game's state/pixels move when a *scripted* action is
injected".  The user's TASK-132 ruling changes the standard: the passing condition is now
that **a model acting as a simulated human player looks at a picture of the game, chooses
an input, and the game accepts it AND the picture changes** -- and that a human reading the
two pictures agrees the change is what that game's rules call for.

So this tool is deliberately NOT another gate criterion.  It is a closed loop with three
separate verdicts per step, each with its own evidence:

    1. the model really looked at the pixels  -> request body carries a base64 PNG, exactly
       1 image + 1 question (kept verbatim in <out>/<step>/request.json)
    2. the GAME accepted the input (ack)      -> the game's OWN InputMap says the action is
       pressed at injection time, plus the game's own state delta / refusal record
    3. the VIEWPORT changed (change)          -> before/after frame sha256 + pixel diff,
       **compared with an equal-length no-input control window**, plus the game's declared
       gameplay observables (`tools/playability_controls.json -> gameplay_observables`)

The user's FAIL condition is exactly the conjunction of (2) and the NEGATION of (3):
"the model produced an action AND the game accepted it AND the picture did not change".

Two backends, on purpose
------------------------
`jev` (8080) is the text-strong / vision-weak model; `playjev` (8081) is the vision
fine-tuned sibling.  The user's standard demands *looking at the picture*, so both are run
and the difference is reported -- degrading Jev to "text state only" is explicitly
forbidden by the task.

Iron rules honoured (TASK-132 §3)
---------------------------------
* no shell redirection anywhere: every artifact is written by Python file handles
  (`io.open(..., "w")` / `open(..., "wb")`) or by the gate's own `write_json`;
* the 20 official projects are opened READ-ONLY and never written (the loop only adds
  `runs/model-player/**`); `projects/_exercises/neg_*` are also read-only;
* one unique high port per run, checked for occupancy against the gate's own
  `kill_what_holds` before the game starts (never 9877/9888/9889/8080/8081);
* the two model services share one GPU, so all calls are serialised (one step at a time,
  one backend at a time) and 429/529 honour `Retry-After` (inside `playtest_agent`).

Evidence layout (`runs/model-player/**`, this tool's own directory)
------------------------------------------------------------------
    _env/prep.json                       services / ports / engines, read-only probe
    <game>/<backend>/session.json        pid / port / engine / viewport / action-set source
    <game>/<backend>/steps.jsonl         one JSON object per step (schema in the task)
    <game>/<backend>/frames/*.png        every frame the loop captured
    <game>/<backend>/states/*.json       every state snapshot the loop read
    <game>/<backend>/<step>/request.json the RAW request body the model received (base64 kept)
    <game>/<backend>/<step>/response.json the RAW response body the service returned
    <game>/<backend>/demo.png            left = frame sequence, right = the model's action+probs
    <game>/<backend>/filmstrip.png       the gate's filmstrip format, for human re-checks
    <game>/<backend>/player.json         the verdict + per-step summary + counts

Self-test without a game and without a model
--------------------------------------------
    python tools\\playtest_player.py prep
        read-only environment probe: `GET /health` on both services, the occupancy of the
        ports this tool may use, the engine binary, and the exported exes.  Writes
        `runs/model-player/_env/prep.json` (every number in the report can be traced here).

    python tools\\playtest_player.py selftest
        exercises the pure decision helpers (`decide_changed`, `step_record`,
        `summarise`, `model_fixed_point`) on constructed records: a "game accepted it and
        NOTHING moved" record must come back FAIL, a moving record must come back PASS, a
        record whose control window moved just as much must NOT count as a change, and a
        record whose model repeated one action on one frame must come back
        MODEL_FIXED_POINT (reported on its own, never a game FAIL and never a PASS).
"""

from __future__ import print_function

import argparse
import base64
import io
import json
import os
import sys
import time

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
sys.path.insert(0, HERE)

import playability_gate as pg                                   # noqa: E402
from playability_gate import (                                   # noqa: E402
    GameProcess, Mcp, write_json, sha256_file, analyse_frame, png_changed, state_delta,
    build_filmstrip, probe_state_source, parse_project, kill_what_holds, process_tree,
    enumerate_windows, gameplay_declaration, marker_declaration, liveness_declaration,
    refusal_declaration, gameplay_changes, refusal_hit,
    terminal_conditions_met, marker_values,
)
from playtest_agent import build_agent, keycode_of, keyname_of  # noqa: E402

RUNS_PLAYER = os.path.join(ROOT, "runs", "model-player")
DEFAULT_PORT = 9951
DEFAULT_EXE_ROOT = os.path.join(ROOT, "dist", "exe")
DEFAULT_BACKENDS = {
    "jev": "http://127.0.0.1:8080",
    "playjev": "http://127.0.0.1:8081",
}
# TASK-132 §1.2: the user's thresholds, written down where the code can be held to them.
PASS_MIN_STEPS = 8
PASS_MIN_RATE = 0.75
# TASK-133 §1.C.1: the model's own fixed point, on its own scale.  The task's ruling
# names the threshold: with the same action AND the same frame hash for >= 3
# consecutive steps, the model is stuck, and that conclusion is kept separate from the
# game's FAIL (it is reported, never counted as a game defect, and never a PASS).
MODEL_FIXED_POINT_MIN_RUN = 3
# TASK-134 §1.C.1: the second model-side conclusion, and the one TASK-133's blind spot
# needed.  `MODEL_FIXED_POINT` requires the SAME action AND the SAME frame, so
# `pong x playjev` (TASK-133 §4.2a) escaped it: nine failing steps in which the model
# varied its action once.  `MODEL_NO_PROGRESS` drops the "same action" requirement
# entirely: >= 3 consecutive steps that were really SENT to the game and produced no
# gameplay progress.  Like the fixed point it is a statement about the RUN's evidence
# quality -- it is filed on its own, it is not a game defect, and it is never a PASS.
MODEL_NO_PROGRESS_MIN_RUN = 3
# A frame-to-frame change counts only if it beats the equal-length no-input control window.
# Two independent margins, both recorded per step:
#   * pixels   -- `> max(2.5 * control, 40)`.  The factor is higher than the gate's
#     `arm_evidence` 1.5 because the two windows here are MEASURED windows of a live game
#     (the gate's are bracketed by its own MCP round trips), so the comparison carries more
#     timing slack; 40 px is the gate's "a genuine frame-to-frame change, not noise".
#   * gameplay -- the declared observables must move MORE in the action window, where
#     "more" is the sum of the movement magnitudes: a position vector that travelled 200 px
#     beats one that travelled 2 px even though both "changed".
CHANGE_CONTROL_FACTOR = 2.5
CHANGE_MIN_PIXELS = pg.P3_MIN_CHANGED_PIXELS
# TASK-135 §1.B: the DECLARATIVE STRICT MARGIN, filed beside the baseline and never in
# place of it.  TASK-134 §7.4 measured that `pong x jev x V3`'s PASS rested on 3/8 steps
# decided by the GAMEPLAY term alone, one of them by 1.19x -- the rule itself is
# `mv > cmv`, which a game that is animating on its own can clear by a hair.  The strict
# reading asks the same question with a declared margin: the declared observables must
# move at least `STRICT_FACTOR` times as far as they moved in the equal-length no-input
# control window (>= 2x is the task's own example, and 2x is what the pixel term already
# requires at 2.5x).  Both readings are computed for EVERY step and both are reported;
# the baseline rule and every historical verdict are left byte-for-byte alone.
CHANGE_STRICT_CONTROL_FACTOR = 2.0
# A ratio against a ZERO control window is undefined; the floor is what "the observable
# really moved" means when the control did not move at all (1.0 = one whole unit of the
# declared quantity, e.g. a board string that advanced, or one pixel of travel).
CHANGE_STRICT_MIN_MOVEMENT = 1.0
CHANGE_MARGINS = ("baseline", "strict")
# TASK-136 §1.A.1: `strict` is now the DEFAULT PASS criterion.  Only a strict PASS is
# written as `PASS`; a run that passes only under the baseline margin is written as
# `PASS(baseline only)` and does NOT count as a pass (`counts_as_pass: false`).  The
# baseline rule itself is untouched -- it is still computed for every step and still
# reported -- so nothing about the old reading is lost, it is just no longer the gate.
CHANGE_MARGIN_DEFAULT_FALLBACK = "strict"
CHANGE_MARGIN_DEFAULT = CHANGE_MARGIN_DEFAULT_FALLBACK
# The verdict string a run gets when the strict margin does not pass it but the baseline
# margin does.  Deliberately NOT `PASS`: it must be impossible to count it as one by
# accident (see `counts_as_pass`).
PASS_BASELINE_ONLY = "PASS(baseline only)"
# TASK-138 defect ⑨: the step verdict written when the injection answered WITHOUT an
# `ack_result`.  It is not FAIL (the game was never shown to have accepted the input) and it
# is not a PASS either; it is the "the evidence cannot answer the question" state, and the
# step is excluded from the accepted rate by `ack.accepted = False`.
STEP_VERDICT_ACK_MISSING = "INCONCLUSIVE_ack_missing"
# TASK-140 §1.A.1: the DECLARED REPORTING WINDOW.  `model_player_window.min_frames` (TASK-139)
# is the FLOOR below which no judgement may be made at all; this is the level at which a
# judgement may be REPORTED AS A PASS.  The difference is the measured TASK-139 finding:
# `w30` verdicts were NOT reproducible across rounds (4 of 5 probed games changed class for
# the same command and the same code), while `w90` was consistent across both rounds.
# A run whose nominal `--window-frames` is below this declaration is kept, reported, and
# marked `BELOW_REPORTING_WINDOW`: it can never count as a pass (`counts_as_pass` is forced
# false), exactly like `WINDOW_TOO_SHORT` and `PASS(baseline only)`.
WINDOW_REPORTING_FRAMES_FALLBACK = 90
STEP_VERDICT_BELOW_REPORTING = "BELOW_REPORTING_WINDOW"
# TASK-140 §1.A.2: the cross-round judgement.  It is computed by aggregating >= 2 INDEPENDENT
# complete runs of the same game at the same window; a disagreement makes the run's class
# `UNSTABLE`, which can only ever REMOVE a pass (the `UNSTABLE` state is never a pass).
STABILITY_STATE_STABLE = "STABLE"
STABILITY_STATE_UNSTABLE = "UNSTABLE"
STABILITY_MIN_ROUNDS = 2


def load_change_margins(path=None):
    """TASK-135 §1.B: the two change-test margins, read from the declaration file.

    `tools/playability_controls.json -> model_player_change_margin`.  The file is the
    declaration (it carries the `why` for each number); the constants above are the
    fallback so the tool still runs if the block is missing.  A caller can also pin the
    numbers with `--change-margin`, which selects WHICH reading the verdict uses -- it
    never rewrites the declaration.
    """
    declared = {}
    p = path or os.path.join(HERE, "playability_controls.json")
    try:
        with io.open(p, encoding="utf-8") as fh:
            doc = json.load(fh)
        declared = doc.get("model_player_change_margin") or {}
    except Exception:  # noqa: BLE001 - a missing/!json declaration must not stop a run
        declared = {}
    base = declared.get("baseline") if isinstance(declared.get("baseline"), dict) else {}
    strict = declared.get("strict") if isinstance(declared.get("strict"), dict) else {}
    out = {
        "source": os.path.abspath(p),
        "declared": dict(declared),
        "baseline": {
            "name": "baseline" if "name" not in base else base["name"],
            "gameplay_control_factor": float(base.get("gameplay_control_factor",
                                                      1.0)),
            "gameplay_min_movement": float(base.get("gameplay_min_movement", 0.0)),
            "gameplay_rule": base.get("gameplay_rule", "strictly greater than the control"),
            "pixel_control_factor": float(base.get("pixel_control_factor",
                                                   CHANGE_CONTROL_FACTOR)),
            "min_pixels": int(base.get("min_pixels", CHANGE_MIN_PIXELS)),
        },
        "strict": {
            "name": "strict" if "name" not in strict else strict["name"],
            "gameplay_control_factor": float(strict.get("gameplay_control_factor",
                                                        CHANGE_STRICT_CONTROL_FACTOR)),
            "gameplay_min_movement": float(strict.get("gameplay_min_movement",
                                                      CHANGE_STRICT_MIN_MOVEMENT)),
            "gameplay_rule": strict.get("gameplay_rule", "at least N times the control"),
            "pixel_control_factor": float(strict.get("pixel_control_factor",
                                                     CHANGE_CONTROL_FACTOR)),
            "min_pixels": int(strict.get("min_pixels", CHANGE_MIN_PIXELS)),
        },
        "default_margin": declared.get("default_margin", CHANGE_MARGIN_DEFAULT),
    }
    if out["default_margin"] not in CHANGE_MARGINS:
        # a hand-edited declaration must never silently select a margin that does not exist
        out["default_margin"] = CHANGE_MARGIN_DEFAULT
    return out


CHANGE_MARGIN_DECLARATION = load_change_margins()
# TASK-136 §1.A.1: the declaration is the source of truth for WHICH margin is the pass
# criterion; the constant above is only the fallback for a missing/unreadable file.
CHANGE_MARGIN_DEFAULT = CHANGE_MARGIN_DECLARATION["default_margin"]


# ---------------------------------------------------------------------------
# TASK-139 §1.A: the DECLARED MINIMUM WINDOW LENGTH, and the `WINDOW_TOO_SHORT` state
# ---------------------------------------------------------------------------
# Why this exists.  `--window-frames` is a NOMINAL budget: the loop waits until the game's
# own `Engine.get_frames_drawn()` has advanced by that many frames, so the length a window
# really achieves is a measured quantity.  A judgement made over a window that is too short
# to contain one game reaction is not evidence about the game, and before this declaration
# the tool had no way to say so: a 3-frame window and a 300-frame window produced the same
# two verdict strings (`changed` / `not changed`).
#
# `model_player_change_margin.window.min_frames` is that declaration.  It is NOT a PASS
# gate: a run whose windows came out shorter than it is written `WINDOW_TOO_SHORT` and can
# never be counted as a PASS, exactly like `PASS(baseline only)`.
STEP_VERDICT_WINDOW_TOO_SHORT = "WINDOW_TOO_SHORT"
WINDOW_MIN_FRAMES_FALLBACK = 20


def load_window_declaration(path=None):
    """`model_player_window` -- the declared minimum frame count per window.

    Read from the same declaration file as the change margins, so `gate.json` and
    `player.json` can both quote the number the loop actually applied instead of a second
    copy of it.  Also accepts the block nested under
    `model_player_change_margin.window`, so a caller that declares it in either place gets
    the same reading.  The fallback is the documented one; an unreadable file is a recorded
    state, not an excuse to skip the check.
    """
    declared = {}
    p = path or os.path.join(HERE, "playability_controls.json")
    try:
        with io.open(p, encoding="utf-8") as fh:
            doc = json.load(fh)
        declared = doc.get("model_player_window") or {}
        if not declared:
            declared = ((doc.get("model_player_change_margin") or {}).get("window") or {})
    except Exception:  # noqa: BLE001
        declared = {}
    try:
        min_frames = int(declared.get("min_frames", WINDOW_MIN_FRAMES_FALLBACK))
    except Exception:  # noqa: BLE001
        min_frames = WINDOW_MIN_FRAMES_FALLBACK
    # TASK-140 §1.A.1: the reporting window lives in the SAME declaration block, so the tool
    # and the gate quote one number instead of two copies of it.
    try:
        reporting_frames = int(declared.get("reporting_frames",
                                            WINDOW_REPORTING_FRAMES_FALLBACK))
    except Exception:  # noqa: BLE001
        reporting_frames = WINDOW_REPORTING_FRAMES_FALLBACK
    return {
        "min_frames": min_frames,
        "reporting_frames": reporting_frames,
        "reporting_basis": declared.get("reporting_basis"),
        "reporting_state": STEP_VERDICT_BELOW_REPORTING,
        "reporting_counts_as_pass": False,
        "declared_by": declared.get("declared_by", "TASK-139 §1.A"),
        "basis": declared.get("basis"),
        "applies_to": declared.get("applies_to") or ["control_window", "action_window"],
        "state": STEP_VERDICT_WINDOW_TOO_SHORT,
        "counts_as_pass": False,
        "source": os.path.abspath(p),
        "fallback_used": not bool(declared),
    }


WINDOW_DECLARATION = load_window_declaration()
WINDOW_MIN_FRAMES = WINDOW_DECLARATION["min_frames"]
WINDOW_REPORTING_FRAMES = WINDOW_DECLARATION["reporting_frames"]


def window_frames_of(control_frames, action_frames, min_frames=WINDOW_MIN_FRAMES):
    """Judge ONE step's two windows against the declared minimum length.

    Both windows are judged: a verdict computed against a control window shorter than the
    declaration is no more evidence than one computed over a short action window.  `None`
    means the number was not recorded (a run from before this task, or an aborted step);
    that is `measured: False`, and it is reported as such rather than treated as "too
    short" -- the tool may not invent a measurement it does not have.
    """
    vals = {"control_frames": control_frames, "action_frames": action_frames}
    measured = [v for v in (control_frames, action_frames) if isinstance(v, int)]
    too_short = [k for k, v in vals.items() if isinstance(v, int) and v < int(min_frames)]
    return {
        "min_frames": int(min_frames),
        "control_frames": control_frames,
        "action_frames": action_frames,
        "measured": bool(measured),
        "short_windows": too_short,
        "too_short": bool(too_short),
        "state": (STEP_VERDICT_WINDOW_TOO_SHORT if too_short else
                  ("ok" if measured else "unmeasured")),
        "rule": ("a window is WINDOW_TOO_SHORT when its measured drawn-frame span is below "
                 "the declared `min_frames`; the run is then NOT a PASS"),
    }


# ---------------------------------------------------------------------------
# TASK-139 §1.B: LEGAL REFUSALS -- the boundary that lets a real refusal off, and the
# floor that stops "refused everything" from passing
# ---------------------------------------------------------------------------
# Why this exists.  TASK-136 §4.3/§12 registered a defect: five games (`match3`,
# `minesweeper`, `pacman`, `sokoban`, `towerdefense`) record a DELIBERATE refusal in their
# own exported counters (`RejectedMoves`, `InputRejectedSwaps`, `InputRejectedCursorActions`,
# `RejectedSteps`, `InputRejectedPlaces`), and the player's FAIL condition charged that
# refusal to the game as "accepted an input and nothing changed".  The gate has had this
# carve-out since TASK-131 X12 (`arm_evidence.refused`); the model-player loop never did.
#
# The boundary, in one sentence: a LEGAL REFUSAL may be dropped from the denominator (it is
# not evidence against the game), but it may never be counted FOR the game -- a run needs a
# declared number of steps of REAL progress, so "the game refused everything and nothing
# ever advanced" cannot reach PASS on refusals alone.
STEP_VERDICT_REFUSED = "refused_legal_no_progress"
MODEL_PLAYER_REFUSAL_FALLBACK = {"min_real_progress_steps": 4, "min_real_progress_rate": 0.5}


def load_refusal_boundary(path=None):
    """`model_player_refusal` -- the declared floor under the refusal carve-out."""
    declared = {}
    p = path or os.path.join(HERE, "playability_controls.json")
    try:
        with io.open(p, encoding="utf-8") as fh:
            doc = json.load(fh)
        declared = doc.get("model_player_refusal") or {}
    except Exception:  # noqa: BLE001
        declared = {}
    try:
        min_steps = int(declared.get("min_real_progress_steps",
                                     MODEL_PLAYER_REFUSAL_FALLBACK["min_real_progress_steps"]))
    except Exception:  # noqa: BLE001
        min_steps = MODEL_PLAYER_REFUSAL_FALLBACK["min_real_progress_steps"]
    try:
        min_rate = float(declared.get("min_real_progress_rate",
                                      MODEL_PLAYER_REFUSAL_FALLBACK["min_real_progress_rate"]))
    except Exception:  # noqa: BLE001
        min_rate = MODEL_PLAYER_REFUSAL_FALLBACK["min_real_progress_rate"]
    return {
        "min_real_progress_steps": min_steps,
        "min_real_progress_rate": min_rate,
        "declared_by": declared.get("declared_by", "TASK-139 §1.B"),
        "basis": declared.get("basis"),
        "source": os.path.abspath(p),
        "fallback_used": not bool(declared),
    }


REFUSAL_BOUNDARY = load_refusal_boundary()
REFUSAL_MIN_REAL_PROGRESS = REFUSAL_BOUNDARY["min_real_progress_steps"]
REFUSAL_MIN_REAL_PROGRESS_RATE = REFUSAL_BOUNDARY["min_real_progress_rate"]


def step_refusal_record(record, decl):
    """Was THIS step a LEGAL REFUSAL, per the game's own exported counters?

    The evidence is the game's, never the model's: the declaration
    (`games.<game>.refusal_evidence.game_side_fields` / `keys`) names the counters the
    project exports, and this reads them out of the same `state_delta` the verdict already
    uses.  It is deliberately stricter than the gate's `arm_evidence.refused`, which also
    demands that the control window did NOT move a refusal counter: a refusal counter that
    moved during the step is the game saying it saw the input and said no, and a control
    window that happened to tick the same counter does not turn the game's own record into
    a non-refusal.
    """
    delta = record.get("state_delta") or []
    # Only a COUNTER THAT MOVED is evidence: a refusal field that appears in the diff with
    # `from == to` (a state dump that lists every exported property) says nothing.
    moved = [c for c in delta
             if c.get("from") != c.get("to") or
             (isinstance(c.get("from"), str) and c.get("from") != c.get("to"))]
    decl = decl or {}
    pattern_keys = decl.get("keys") or ["LastRefusedInput", "Rejected"]
    exact = [c.get("key") for c in moved
             if any((c.get("key") or "").rsplit(".", 1)[-1] == str(f)
                    for f in (decl.get("game_side_fields") or []))]
    matched = [c["key"] for c in moved
               if any(s in (c.get("key") or "") for s in pattern_keys)]
    # TASK-139 §1.B: the evidence STRING names the game's own exported COUNTER first.  The
    # `game_side_fields` a game declares are the exact counters, so they are preferred over
    # any nested/derived field that merely matched one of the broad `keys` patterns
    # (`LastEvent`'s text also carries the refusal, but the counter is the declaration).
    ordered = list(exact) + [k for k in matched if k not in exact]
    if not ordered:
        return None
    primary = ordered[0]
    hit = None
    for c in moved:
        if c.get("key") == primary:
            hit = "%s: %r -> %r" % (c.get("key"), c.get("from"), c.get("to"))
            break
    if hit is None:
        hit = refusal_hit(moved, decl)
    return {
        "refusal_evidence": hit,
        "game_side_counter": primary,
        "game_side_counters_moved": ordered,
        "keys": ordered,
        "source": "the game's own exported state delta for this step (never the model)",
        "declaration": decl.get("declared_by"),
        "changed_keys_only": True,
    }


def _margin_reading(margins, name, pixel_diff, control_pixels, gameplay_movement,
                    control_movement):
    """One margin applied to one step's four numbers -- the whole rule, in one place."""
    spec = margins[name]
    px = max(0, int(pixel_diff or 0))
    ctl = max(0, int(control_pixels or 0))
    mv = float(gameplay_movement or 0.0)
    cmv = float(control_movement or 0.0)
    factor = float(spec["gameplay_control_factor"])
    floor = float(spec["gameplay_min_movement"])
    if factor > 1.0:
        # the STRICT shape: "the observables must move at least factor x as far as the
        # control did", with an absolute floor for the zero-control case.
        gameplay_wins = bool(mv >= factor * cmv and mv >= floor)
    else:
        # the BASELINE shape, unchanged from TASK-132: strictly more than the control.
        gameplay_wins = bool(mv > cmv)
    pixel_wins = px > max(int(ctl * float(spec["pixel_control_factor"])),
                          int(spec["min_pixels"]))
    ratio = (round(mv / cmv, 3) if cmv > 0 else None)
    if gameplay_wins:
        why = ("the declared gameplay observables moved %.3f in this window vs %.3f in "
               "the control window (ratio %s, rule: %s)"
               % (mv, cmv, ratio, spec["gameplay_rule"]))
    elif pixel_wins:
        why = ("the viewport changed %d px, over the control window's %d (needs > "
               "max(%.1f*control, %d))" % (px, ctl, spec["pixel_control_factor"],
                                           spec["min_pixels"]))
    else:
        why = ("neither the gameplay observables (moved %.3f vs control %.3f, ratio %s, "
               "rule: %s) nor the viewport (changed %d px vs control %d) beat the no-input "
               "control window" % (mv, cmv, ratio, spec["gameplay_rule"], px, ctl))
    return {
        "margin": name,
        "changed": bool(gameplay_wins or pixel_wins),
        "gameplay_wins": gameplay_wins,
        "pixel_wins": pixel_wins,
        "why_changed": why,
        "pixel_diff": px, "control_pixels": ctl,
        "gameplay_movement": mv, "control_movement": cmv,
        "margin_ratio": ratio,
        "gameplay_control_factor": factor,
        "gameplay_min_movement": floor,
        "pixel_control_factor": float(spec["pixel_control_factor"]),
        "min_pixels": int(spec["min_pixels"]),
        "rule": spec["gameplay_rule"],
    }


def log(msg):
    print(msg, flush=True)


# ---------------------------------------------------------------------------
# small state helpers
# ---------------------------------------------------------------------------
def canonical_state_sha(state):
    import hashlib
    return hashlib.sha256(json.dumps(state, sort_keys=True, ensure_ascii=False,
                                     default=str).encode("utf-8")).hexdigest()


def observed_fields(state, key_filter):
    """Every `nodes` entry whose key matches one of `key_filter` substrings.

    This is the loop's own reader for report tables; it deliberately does not touch the
    gate's rules.
    """
    nodes = (state or {}).get("nodes") or {}
    out = {}
    for path, entry in nodes.items():
        if any(s in path for s in (key_filter or [])):
            out[path] = dict((k, v) for k, v in entry.items()
                             if k not in ("script", "c", "name", "vis"))
    return out


def action_set_from_project(proj, only=None):
    """The `choice` criteria set: the game's own declared InputMap actions.

    TASK-132 §1.1 step 2: `criteria` = **the game's declared action set**, taken from
    `project.godot`'s InputMap via `playability_gate.parse_project`.  `only` narrows it
    (recorded in `session.json -> action_set_source`), it never invents an action.

    The `done` option of `playtest_agent.action_criteria` is REMOVED here, and that is a
    measured decision, not a preference: in the first full pong run Jev answered `done`
    (P=0.61) on steps 4..12 and never acted again once the ball had come to rest, so the
    loop stopped measuring the game and started measuring the model's stop-seeking.  This
    tool is a *player*, not a probe: the loop decides when to stop, not the model.  The
    evidence for that run is kept in `runs/model-player/_prefix-abandoned/pong/jev/`
    (its `steps.jsonl` shows the same request hash on steps 4..12).
    """
    acts = {}
    for name, spec in (proj.get("actions") or {}).items():
        if only and name not in only:
            continue
        acts[name] = spec.get("keys") or []
    return acts


def first_keycode(proj, action):
    spec = (proj.get("actions") or {}).get(action) or {}
    return next((c for c in spec.get("keycode") or [] if c), None)


# ---------------------------------------------------------------------------
# GDScript probes (the injection + ack channels)
# ---------------------------------------------------------------------------
def probe_action_kc_down(keycode, action):
    """The gate's faithful channel for a KEY: `Input.parse_input_event`."""
    return """
var ev = InputEventKey.new()
ev.keycode = %d
ev.pressed = true
ev.echo = false
Input.parse_input_event(ev)
return {"channel": "parse_input_event", "keycode": %d, "pressed": true,
        "action": "%s", "has_action": %s,
        "is_action_pressed": (Input.is_action_pressed("%s") if InputMap.has_action("%s") else null),
        "strength": (Input.get_action_strength("%s") if InputMap.has_action("%s") else null)}
""" % (int(keycode), int(keycode), action, ("true" if action else "false"),
       action, action, action, action)


def probe_action_kc_up(keycode, action):
    return """
var ev = InputEventKey.new()
ev.keycode = %d
ev.pressed = false
ev.echo = false
Input.parse_input_event(ev)
return {"channel": "parse_input_event", "keycode": %d, "pressed": false,
        "action": "%s", "has_action": %s,
        "is_action_pressed": (Input.is_action_pressed("%s") if InputMap.has_action("%s") else null)}
""" % (int(keycode), int(keycode), action, ("true" if action else "false"), action, action)


def probe_action_state(action):
    return pg.probe_action_state(action)


# ---------------------------------------------------------------------------
# pure decision helpers  (the part `selftest` exercises, no game and no model needed)
# ---------------------------------------------------------------------------
def gameplay_change_labels(changes, decl, limit=4):
    """The declared gameplay changes, labelled by the FIELD that moved, not the node.

    `state_delta` keys are `nodes` tree paths (`/root/Main/Ball`), so a raw key list says
    "this node's pos changed" and not which of the fields the game declares as gameplay did.
    Box2D-ish games export `pos` on a Node2D whose own position is always [0,0] (the child
    nodes move), so the useful reading is "<node>.<field>: <from> -> <to>".  The values are
    kept short enough for a demo panel; the full change list stays in `state_delta`.
    """
    out = []
    for c in gameplay_changes(changes, decl):
        key = c.get("key") or ""
        f, t = c.get("from"), c.get("to")
        if isinstance(f, (list, tuple)) or isinstance(t, (list, tuple)):
            out.append("%s.pos %s->%s" % (key, _short(f), _short(t)))
        else:
            out.append("%s %s->%s" % (key, _short(f), _short(t)))
    return out[:limit]


def _short(v):
    if isinstance(v, (list, tuple)):
        try:
            return "[%s]" % ",".join("%.1f" % float(x) for x in v)
        except (TypeError, ValueError):
            return str(v)
    return str(v)


def gameplay_delta(state_before, state_after, decl):
    """The changed entries, kept whole, plus the subset the game DECLARES as gameplay."""
    delta = state_delta(state_before, state_after)
    gp = gameplay_changes(delta, decl)
    return delta, gp


def movement_magnitude(changes):
    """How far the declared gameplay observables MOVED, not merely whether they changed.

    For a vector field (`pos`, `Velocity`) it is the Euclidean distance between the before
    and after values; for a scalar field it is the absolute difference.  Non-numeric fields
    get 1.0 per change (a board string that advanced "changed", and that is all we can say).

    Why this exists: "the list of changed keys differs between the two windows" is too weak
    on a game that is animating on its own.  pong's ball keeps flying whether or not the
    model pressed anything, so `Ball.pos` appears in BOTH lists and the count comparison
    cannot see the input.  The MAGNITUDE of the movement can: a paddle driven 200 px by a
    key beats a control window in which nothing moved 2.5 px.
    """
    total = 0.0
    detail = []
    for c in changes or []:
        f, t = c.get("from"), c.get("to")
        m = None
        if isinstance(f, (list, tuple)) and isinstance(t, (list, tuple)) and \
                len(f) == len(t) >= 2:
            try:
                m = sum((float(b) - float(a)) ** 2 for a, b in zip(f, t)) ** 0.5
            except (TypeError, ValueError):
                m = None
        elif isinstance(f, (int, float)) and isinstance(t, (int, float)) and \
                not isinstance(f, bool) and not isinstance(t, bool):
            m = abs(float(t) - float(f))
        if m is None:
            m = 1.0
        total += m
        detail.append({"key": c.get("key"), "magnitude": round(m, 3),
                       "from": f, "to": t})
    return round(total, 3), detail


def decide_changed(pixel_diff, control_pixels, gameplay_movement, control_movement,
                   margins=None):
    """The user's TASK-132 §1.1 step 5 change test, as one pure function.

    `changed` is true when the action window beat its own equal-length no-input control
    window in a way the game's own declaration calls gameplay:

      * the declared gameplay observables travelled FURTHER during the action window than
        during the control window, or
      * the viewport changed more than the control did -- `> max(2.5*control, 40 px)`.

    Both terms are needed: the pixel term alone would call a game that animates by itself
    "responsive", and the movement term alone would miss a game whose only visible response
    is a pixel-level effect (a flash, a cleared line) with no exported position.

    TASK-135 §1.B adds a SECOND, DECLARATIVE reading and files it beside the first one:
    `result["strict"]` applies the same two terms with the declared strict margin (the
    observables must move >= 2x as far as in the control window, with a declared floor for
    a zero control).  The top-level `changed` is still the baseline rule, byte-for-byte:
    every historical verdict recomputed from a recorded run stays what it was, and the
    strict reading can only ever ADD a number a reader can disagree with.
    """
    m = margins or CHANGE_MARGIN_DECLARATION
    baseline = _margin_reading(m, "baseline", pixel_diff, control_pixels,
                               gameplay_movement, control_movement)
    strict = _margin_reading(m, "strict", pixel_diff, control_pixels,
                             gameplay_movement, control_movement)
    out = dict(baseline)
    out.pop("margin", None)
    out["strict"] = strict
    out["margins_declared"] = {"source": m.get("source"),
                               "baseline": m.get("baseline"),
                               "strict": m.get("strict")}
    return out



def ack_verdict(action, down_result, up_result, gp_keys, refusal=None,
                real_key=None, action_state=None):
    """TASK-132 §1.1 step 4: did the GAME accept this input?  Named evidence, not a claim.

    The evidence hierarchy, strongest first (all are the GAME's own words, never the
    model's):
      `action_pressed`     the game's own InputMap says the action is down right after the
                           injection -- `Input.is_action_pressed()` inside the game process
      `state_moved`        a declared gameplay observable moved across the injection window
      `refused_recorded`   the game itself recorded a deliberate refusal (it SAW the input
                           and said no: a wall, the board edge) -- acceptance of the event,
                           refusal of the move, and reported as such
      `nothing`            none of the above: no evidence the input was ever accepted

    A step where the model produced NO injectable action (an empty choice, a `wait`, a
    transport error) has `injected=False`: nothing was sent, so nothing can have been
    accepted, and the step is excluded from the rate instead of counting as a failure of
    the GAME.  The `state_moved` shortcut is suppressed in that case, because a game that
    keeps animating by itself would otherwise be credited with accepting an input that was
    never sent.
    """
    ev = []
    pressed = None
    if isinstance(down_result, dict):
        pressed = down_result.get("is_action_pressed")
    if pressed is None and isinstance(action_state, dict):
        # `playability_gate.probe_action_state` reports the InputMap read as `pressed`
        # (verbatim: `{"pressed": Input.is_action_pressed(action)}`); the synthetic arm also
        # carries `is_action_pressed` from its own probe.  Both are the GAME's own reading,
        # so both are accepted -- reading only one of them is what made the first real-key
        # run report `state_moved` as its strongest evidence while the game was in fact
        # reporting `pressed: true`.
        pressed = action_state.get("is_action_pressed")
        if pressed is None:
            pressed = action_state.get("pressed")
    injected = bool(action) and (action_state is not None or pressed is not None)
    if pressed:
        ev.append("action_pressed")
    if injected and gp_keys:
        ev.append("state_moved")
    if injected and refusal:
        ev.append("refused_recorded")
    if real_key and real_key.get("is_action_pressed"):
        ev.append("real_key_action_pressed")
    primary = ev[0] if ev else "nothing"
    return {
        "accepted": bool(ev and ev[0] != "nothing"),
        "injected": bool(injected),
        "evidence_used": primary,
        "evidence_all": ev,
        "action_pressed": pressed,
        "state_moved_keys": list(gp_keys or []) if injected else [],
        "refusal": refusal if injected else None,
        "real_key": real_key,
        "note": ("the action's InputMap state was read inside the game process; the model's "
                 "own statement is never used as evidence"),
    }


def step_verdict(ack, change):
    """The user's FAIL condition, spelled out.

    FAIL  = the model produced an action AND the game accepted it AND the viewport did not
            show a dynamic change (per `decide_changed`).
    """
    accepted = bool((ack or {}).get("accepted"))
    changed = bool((change or {}).get("changed"))
    if accepted and not changed:
        return "FAIL_no_change_after_accepted_input"
    if accepted and changed:
        return "ok_ack_and_changed"
    if not accepted and changed:
        return "changed_but_ack_missing"
    return "no_ack_no_change"


def changed_of(record, margin=CHANGE_MARGIN_DEFAULT):
    """One step's change reading under one of the two declared margins (TASK-135 §1.B).

    `baseline` reads the top-level `changed` field (the TASK-132 rule; every recorded run
    written before this task has it and nothing else).  `strict` reads the declaration's
    stricter margin, which `decide_changed` now computes for every step.  A record written
    before TASK-135 therefore reports `strict == baseline` instead of an error.
    """
    ch = record.get("change") or {}
    if margin == "strict":
        s = ch.get("strict")
        if isinstance(s, dict) and "changed" in s:
            return bool(s.get("changed"))
        return bool(ch.get("changed"))
    return bool(ch.get("changed"))


def change_margin_edge_steps(records, limit=40):
    """The steps where the two margins DISAGREE -- "which steps are the edge steps".

    TASK-135 §1.B asks for the edge steps to be named, so this is a first-class reading
    rather than something a reader has to dig out of the step files.  Every entry carries
    the four numbers the decision used and the ratio between them, so "1.19x" is visible
    as a number and not as an adjective.
    """
    out = []
    for r in records or []:
        ack = r.get("ack") or {}
        if not (ack.get("injected") and ack.get("accepted")):
            continue
        ch = r.get("change") or {}
        base = bool(ch.get("changed"))
        strict = changed_of(r, "strict")
        if base == strict:
            continue
        st = ch.get("strict") or {}
        out.append({
            "step": r.get("step"),
            "action": (r.get("action") or {}).get("action"),
            "baseline_changed": base,
            "strict_changed": strict,
            "pixel_diff": ch.get("pixel_diff"),
            "control_pixels": ch.get("control_pixels"),
            "gameplay_movement": ch.get("gameplay_movement"),
            "control_movement": ch.get("control_movement"),
            "margin_ratio": st.get("margin_ratio") if isinstance(st, dict) else None,
            "step_verdict": r.get("step_verdict"),
            "reading": ("baseline counted this step as a change; under the strict margin "
                        "(>= %.1fx the control window) it does NOT"
                        % float((st or {}).get("gameplay_control_factor") or
                                CHANGE_STRICT_CONTROL_FACTOR)),
        })
        if len(out) >= limit:
            break
    return out


def model_fixed_point(records, min_run=MODEL_FIXED_POINT_MIN_RUN):
    """TASK-133 §1.C.1 (TASK-132 §N.3): the MODEL's fixed point, on its own.

    A model that answers the SAME action and is handed a byte-identical frame for
    `min_run` consecutive steps is stuck.  That is a fact about the MODEL, not about the
    game: it is reported as its own conclusion (`MODEL_FIXED_POINT`), it is never
    counted as a game defect, and it must never be quoted as evidence that the game is
    playable either.  The run that motivated it: PlayJev answered `tetris_left` (P=0.58)
    for nine straight steps and `pong_right_down` (P=0.63) for nine straight steps, each
    time on a byte-identical frame, so "the game ignored my input" and "I stopped
    playing" could not be told apart (TASK-132 §N.3).

    Returns the longest run as `{found, min_run, length, steps, action, frame_sha,
    confidence, reading}`.  Counted over the steps that carried an injected action.
    """
    best = {"found": False, "min_run": int(min_run), "length": 0, "steps": [],
            "action": None, "frame_sha": None, "confidence": None}
    cur_len, cur_steps, cur_action, cur_sha = 0, [], None, None
    for r in records or []:
        if not (r.get("ack") or {}).get("injected"):
            cur_len, cur_steps, cur_action, cur_sha = 0, [], None, None
            continue
        act = (r.get("action") or {}).get("action")
        sha = r.get("frame_before_sha")
        if act is not None and act == cur_action and sha is not None and sha == cur_sha:
            cur_len += 1
            cur_steps.append(r.get("step"))
        else:
            cur_len, cur_steps, cur_action, cur_sha = 1, [r.get("step")], act, sha
        if cur_len > best["length"]:
            best.update({"found": cur_len >= int(min_run), "length": cur_len,
                         "steps": list(cur_steps), "action": cur_action,
                         "frame_sha": cur_sha, "confidence": r.get("confidence")})
    if not best["found"]:
        best["reading"] = ("no run of >= %d consecutive steps shared one action AND one "
                           "byte-identical frame" % int(min_run))
    else:
        best["reading"] = ("the MODEL is stuck: %d consecutive steps all answered '%s' on "
                           "the byte-identical frame %s (confidence %s).  This is a fact "
                           "about the model, NOT about the game -- it is not a game defect, "
                           "and it is not evidence that the game is playable either"
                           % (best["length"], best["action"],
                              (best["frame_sha"] or "")[:8], best["confidence"]))
    return best


def step_made_progress(record):
    """Did this step ADVANCE the game?  The per-step predicate `MODEL_NO_PROGRESS` uses.

    It is deliberately the narrowest reading, and it is the one the user's criterion
    already defines: the model produced an action, the action was really sent to the game
    (`ack.injected`), and the picture did not change more than the equal-length no-input
    control window (`change.changed` is false).  A step where no action was sent is not a
    measurement of the game at all, so it neither counts as progress nor as its absence --
    it BREAKS a run (see `model_no_progress`).

    Note what this predicate does NOT look at: the action's identity, and the frame hash.
    That is the whole point of the new rule -- `pong x playjev` varied its action once and
    the fixed-point rule therefore missed it (TASK-133 §4.2a).
    """
    injected = bool((record.get("ack") or {}).get("injected"))
    if not injected:
        return None                      # not measured: neither progress nor its absence
    return bool((record.get("change") or {}).get("changed"))


def model_no_progress(records, min_run=MODEL_NO_PROGRESS_MIN_RUN):
    """TASK-134 §1.C.1: >= `min_run` consecutive SENT steps with NO gameplay progress.

    This is the companion to `model_fixed_point` and it exists because the fixed point has
    a measured blind spot: it demands the SAME action on the SAME frame, so a sequence that
    varies its action once (exactly `pong x playjev`, TASK-133 §4.2a: nine failing steps,
    `rate 0.25`, `same_action_fixed_point` NOT triggered) is invisible to it.  This rule
    drops the action requirement and keeps only "was it sent, and did anything advance".

    The conclusion is about the RUN, and TASK-134 §1.C.3 fixes its status: it is reported
    under its own key, it is NOT a game defect (it does not make the game FAIL) and it is
    NOT a PASS (it is never evidence that the game is playable).  It is also NOT a licence
    to stop failing a game: the existing `FAIL_no_change_after_accepted_input` reading is
    unchanged and is still recorded beside it.

    Returns the longest run as `{found, min_run, length, steps, actions, length_note,
    reading}`.
    """
    best = {"found": False, "min_run": int(min_run), "length": 0, "steps": [],
            "actions": [], "distinct_actions": []}
    cur_len, cur_steps, cur_acts = 0, [], []
    for r in records or []:
        progress = step_made_progress(r)
        if progress is None:
            cur_len, cur_steps, cur_acts = 0, [], []
            continue
        if progress:
            cur_len, cur_steps, cur_acts = 0, [], []
            continue
        cur_len += 1
        cur_steps.append(r.get("step"))
        cur_acts.append((r.get("action") or {}).get("action"))
        if cur_len > best["length"]:
            best.update({"found": cur_len >= int(min_run), "length": cur_len,
                         "steps": list(cur_steps), "actions": list(cur_acts),
                         "distinct_actions": sorted(set(a for a in cur_acts if a))})
    if not best["found"]:
        best["length_note"] = ("no run of >= %d consecutive SENT steps without gameplay "
                               "progress (the longest was %d)"
                               % (int(min_run), best["length"]))
        best["reading"] = best["length_note"]
    else:
        best["reading"] = ("%d consecutive steps were SENT to the game and nothing "
                           "advanced: steps %s, actions %s.  This is a statement about the "
                           "RUN's evidence (the model produced no progress), NOT a game "
                           "defect, and NOT a PASS -- it is filed separately from FAIL"
                           % (best["length"], best["steps"], best["distinct_actions"]))
    best["what"] = ("TASK-134 §1.C.1: >= %d consecutive injected steps with no gameplay "
                    "progress, EVEN IF the actions differ (the fixed point's blind spot).  "
                    "NOT a game defect, NOT a PASS; reported separately from FAIL."
                    % int(min_run))
    return best


def summarise(records, backend=None, game=None, state=None, player="model",
              margin=None, nominal_frames=None, round_index=None):
    """`steps.jsonl` -> the TASK-132 §1.2 three-state verdict, under BOTH margins.

    TASK-135 §1.B: the verdict is computed twice from the same records -- once with the
    baseline TASK-132 change rule and once with the declared STRICT margin -- and both are
    returned.  `margin` selects which of the two is the top-level verdict (`baseline` by
    default, so every existing reader and every historical verdict is unchanged); the other
    one is always present as `strict_*` / `baseline_*` fields together with the list of
    steps the two readings disagree about.  Relaxing or tightening a margin can therefore
    never silently move a verdict: both numbers, and the steps that separate them, are in
    the same document.
    """
    margin = margin or CHANGE_MARGIN_DEFAULT
    if margin not in CHANGE_MARGINS:
        raise ValueError("unknown change margin %r (known: %s)" % (margin, CHANGE_MARGINS))
    base = _summarise_core(records, backend, game, state, player, "baseline")
    strict = _summarise_core(records, backend, game, state, player, "strict")
    out = dict(strict if margin == "strict" else base)
    edges = change_margin_edge_steps(records)
    out["change_margin"] = {
        "selected": margin,
        "known": list(CHANGE_MARGINS),
        "declaration_source": CHANGE_MARGIN_DECLARATION.get("source"),
        "baseline": CHANGE_MARGIN_DECLARATION.get("baseline"),
        "strict": CHANGE_MARGIN_DECLARATION.get("strict"),
        "reading": ("the verdict above uses the %r margin; the other reading is reported "
                    "beside it and is never used to replace it.  TASK-136 §1.A.1: %r is the "
                    "PASS criterion, `baseline` is the control; a run the control passes "
                    "and the criterion does not is %r (counts_as_pass=false)"
                    % (margin, CHANGE_MARGIN_DEFAULT, PASS_BASELINE_ONLY)),
        "edge_step_count": len(edges),
        "edge_steps": edges,
        "what": ("TASK-135 §1.B: the baseline rule is TASK-132's `gameplay movement > "
                 "control movement`; the strict rule requires the declared observables to "
                 "move at least %sx as far as the control window did (floor %s), which is "
                 "the margin TASK-134 §7.4 asked for after `pong x jev x V3` passed on "
                 "3/8 steps decided by ratios as small as 1.19x"
                 % (CHANGE_MARGIN_DECLARATION["strict"]["gameplay_control_factor"],
                    CHANGE_MARGIN_DECLARATION["strict"]["gameplay_min_movement"])),
    }
    out["baseline_verdict"] = base["verdict"]
    out["baseline_why"] = base["why"]
    out["baseline_accepted_and_changed_rate"] = base["accepted_and_changed_rate"]
    out["baseline_fail_steps"] = base["fail_steps"]
    out["baseline_game_side_verdict"] = base.get("game_side_verdict")
    out["strict_verdict"] = strict["verdict"]
    out["strict_why"] = strict["why"]
    out["strict_accepted_and_changed_rate"] = strict["accepted_and_changed_rate"]
    out["strict_fail_steps"] = strict["fail_steps"]
    out["strict_changed_steps_of_accepted"] = strict["changed_steps_of_accepted"]
    out["strict_game_side_verdict"] = strict.get("game_side_verdict")
    out["strict_game_side_why"] = strict.get("game_side_why")
    out["change_margin_edge_steps"] = edges
    # -- TASK-136 §1.A.1: the strict margin is the PASS criterion ------------------------
    # The rule, in full:
    #   * strict PASS                        -> `PASS`,                counts_as_pass True
    #   * strict not PASS but baseline PASS  -> `PASS(baseline only)`, counts_as_pass False
    #   * neither PASS                       -> the STRICT verdict,   counts_as_pass False
    # `strict` can only ever be harder than `baseline` (its gameplay term implies the
    # baseline term and its pixel term is identical), so `strict PASS => baseline PASS`;
    # the middle case is therefore exactly "the stricter reading refused what the older
    # reading allowed", which is the number the task asks to be counted separately.
    if margin == "strict":
        if strict["verdict"] == "PASS":
            out["verdict"] = "PASS"
        elif base["verdict"] == "PASS":
            out["verdict"] = PASS_BASELINE_ONLY
        else:
            out["verdict"] = strict["verdict"]
    out["counts_as_pass"] = bool(out.get("verdict") == "PASS")
    out["pass"] = out["counts_as_pass"]
    # -- TASK-138 defect ⑧ / ⑨: the two measurement facts this batch had to fix, folded in --
    # Both are read back OUT of the step records (not accumulated in a side channel), so a
    # `resummarise` of an old run and a fresh run go through exactly the same code.
    align = []
    for r in records or []:
        wb = r.get("frame_budget") or {}
        cb = (r.get("control_diff") or {}).get("frame_budget") or {}
        if not wb and not cb:
            continue
        entry = {
            "step": r.get("step"),
            "control_frames": cb.get("achieved_delta"),
            "action_frames": (wb.get("action_frames") if wb.get("action_frames") is not None
                              else wb.get("achieved_delta")),
            "control_start_drawn": cb.get("start_drawn"),
            "control_end_drawn": cb.get("end_drawn"),
            "action_start_drawn": wb.get("step_frame_start"),
            "action_end_drawn": wb.get("step_frame_end"),
            "target_delta": wb.get("target_delta"),
            "control_target_delta": cb.get("target_delta"),
            "matched": None,
        }
        if isinstance(entry["control_frames"], int) and \
                isinstance(entry["action_frames"], int):
            entry["matched"] = bool(entry["control_frames"] == entry["action_frames"])
        align.append(entry)
    matched_n = sum(1 for a in align if a.get("matched"))
    residual = [a["action_frames"] - a["control_frames"] for a in align
                if isinstance(a.get("action_frames"), int) and
                isinstance(a.get("control_frames"), int)]
    out["frame_alignment"] = {
        "what": ("TASK-138 defect ⑧: for every step, the number of the game's OWN drawn "
                 "frames the zero-input control window spanned and the number the action "
                 "window spanned.  Both are `Engine.get_frames_drawn()` deltas from the "
                 "window's own first read to the `drawn` its wait reported -- the same "
                 "quantity measured the same way; `matched` is "
                 "`control_frames == action_frames`."),
        "how": ("the action window is given the control window's achieved span as an ABSOLUTE "
                "`drawn` target, so the equality does not depend on a nominal --window-frames "
                "budget -- one MCP round trip moves `drawn` by 30..120 frames"),
        "steps": align,
        "step_count": len(align),
        "matched_step_count": matched_n,
        "all_matched": bool(align and matched_n == len(align)),
        "residual_frames": {
            "min": min(residual) if residual else None,
            "max": max(residual) if residual else None,
            "max_abs": max(abs(r) for r in residual) if residual else None,
            "within_5": sum(1 for r in residual if abs(r) <= 5),
            "within_10": sum(1 for r in residual if abs(r) <= 10),
            "n": len(residual),
            "what": ("action_frames - control_frames per step; the residual left after the "
                     "absolute-target alignment is the game's own frame-to-frame jitter "
                     "between the two waits, and it is reported rather than described"),
        },
        "reading": ("%d/%d steps have the two windows on the SAME achieved drawn-frame count "
                    "(max |residual| = %s frame(s))"
                    % (matched_n, len(align),
                       (max(abs(r) for r in residual) if residual else "?"))),
        "legacy_note": ("a run recorded before TASK-138 has no `frame_budget.absolute_target` / "
                        "`step_frame_start`, so its rows are the old nominal-budget windows; "
                        "the values above are whatever the records carry"),
    }
    missing = [{"step": r.get("step"),
                "action": (r.get("action") or {}).get("action"),
                "ack_missing": (r.get("ack") or {}).get("ack_missing"),
                "step_verdict": r.get("step_verdict")}
               for r in records or []
               if (r.get("ack") or {}).get("ack_missing")]
    out["ack_missing"] = {
        "what": ("TASK-138 defect ⑨: steps whose injection answered without an `ack_result`.  "
                 "There is no game-side read of the InputMap state taken AFTER that "
                 "injection, so the step cannot be judged: it is INCONCLUSIVE, the "
                 "pre-injection `pre_ack` is never used as evidence, and the step is excluded "
                 "from the accepted rate (`ack.accepted=false`)."),
        "count": len(missing),
        "steps": missing,
        "step_verdict": STEP_VERDICT_ACK_MISSING,
        "pre_ack_fallback": False,
        "reading": ("%d step(s) had no post-injection ack; each of them is INCONCLUSIVE and "
                    "none of them used the pre-injection reading" % len(missing)),
    }
    out["pass_criterion"] = margin
    out["pass_criterion_reading"] = (
        "TASK-136 §1.A.1: the PASS criterion is the %r margin.  `baseline` is kept as the "
        "CONTROL reading and is still reported for every step and every run; a run that the "
        "baseline passes and the strict margin does not is written as %r and has "
        "`counts_as_pass: false`, so it can never be counted as a pass"
        % (margin, PASS_BASELINE_ONLY))

    # -- TASK-139 §1.A: WINDOW_TOO_SHORT, applied LAST so it covers BOTH margins ------------
    # The check reads the SAME per-step entries `frame_alignment` was built from (the two
    # windows' measured drawn-frame spans), so the number the boundary judges and the number
    # the alignment reports cannot drift apart.  Ordering matters: this is evaluated after
    # the margin/PASS(baseline only) reading, because "the window was too short" is a
    # statement about the MEASUREMENT, not about the game, and it must be able to take a run
    # out of `PASS` but never to put one in.
    win_steps = []
    for a in (out.get("frame_alignment") or {}).get("steps") or []:
        w = window_frames_of(a.get("control_frames"), a.get("action_frames"))
        w["step"] = a.get("step")
        win_steps.append(w)
    short = [w for w in win_steps if w.get("too_short")]
    out["window_frames"] = {
        "declared_by": WINDOW_DECLARATION.get("declared_by"),
        "source": WINDOW_DECLARATION.get("source"),
        "min_frames": WINDOW_MIN_FRAMES,
        "basis": WINDOW_DECLARATION.get("basis"),
        "applies_to": WINDOW_DECLARATION.get("applies_to"),
        "steps": win_steps,
        "step_count": len(win_steps),
        "too_short_steps": [w["step"] for w in short],
        "too_short_step_count": len(short),
        "measured_step_count": sum(1 for w in win_steps if w.get("measured")),
        "state": (STEP_VERDICT_WINDOW_TOO_SHORT if short else
                  ("ok" if win_steps else "unmeasured")),
        "rule": ("TASK-139 §1.A: a step whose control or action window spanned fewer than "
                 "the declared `min_frames` drawn frames is %s; the run is then NOT counted "
                 "as a PASS and the state is kept on the verdict string itself"
                 % STEP_VERDICT_WINDOW_TOO_SHORT),
        "not_a_loosening": [
            "the check can only take a run OUT of PASS, never put one in",
            "it does not change the nominal `--window-frames` budget or either ruler's "
            "formula; it only refuses to judge what was measured over too short a window",
            "the measured spans are the game's own `Engine.get_frames_drawn()` deltas "
            "(TASK-138 defect ⑧), not a wall-clock estimate",
        ],
    }
    out["window_too_short"] = bool(short)
    out["window_too_short_steps"] = [w["step"] for w in short]
    out["verdict_before_window_check"] = out.get("verdict")
    if short:
        out["verdict"] = "%s %s" % (STEP_VERDICT_WINDOW_TOO_SHORT, out.get("verdict"))
        out["counts_as_pass"] = False
        out["pass"] = False
        out["window_why"] = ("step(s) %s had a window shorter than the declared minimum of "
                             "%d drawn frames, so the run is %s and cannot be a PASS"
                             % (out["window_too_short_steps"], WINDOW_MIN_FRAMES,
                                STEP_VERDICT_WINDOW_TOO_SHORT))
    else:
        out["window_why"] = ("every measured window spans >= %d drawn frames (declared "
                             "minimum); the verdict is not a WINDOW_TOO_SHORT"
                             % WINDOW_MIN_FRAMES)

    # -- TASK-140 §1.A.1: the REPORTING WINDOW, applied after the short-window check ---------
    # `min_frames` refuses to judge below 20 drawn frames; `reporting_frames` refuses to
    # REPORT A PASS below its own level (declared 90, on the measured ground that w30 verdicts
    # were not reproducible across rounds while w90's were).  Same discipline as every other
    # boundary in this file: it can only take a run OUT of PASS.
    nominal = None
    if nominal_frames is not None:
        try:
            nominal = int(nominal_frames)
        except Exception:  # noqa: BLE001
            nominal = None
    below_reporting = bool(nominal is not None and nominal < WINDOW_REPORTING_FRAMES)
    out["reporting_window"] = {
        "declared_by": WINDOW_DECLARATION.get("declared_by"),
        "required_frames": WINDOW_REPORTING_FRAMES,
        "nominal_frames": nominal,
        "at_reporting_window": (None if nominal is None else (not below_reporting)),
        "state": (("unrecorded" if nominal is None else
                   (STEP_VERDICT_BELOW_REPORTING if below_reporting else "ok"))),
        "counts_as_pass": (False if below_reporting else None),
        "basis": WINDOW_DECLARATION.get("reporting_basis"),
        "rule": ("TASK-140 §1.A.1: a verdict produced at a nominal `--window-frames` below "
                 "the declared reporting window is REPORTED (as reference) and can never be "
                 "a PASS.  It is a statement about the MEASUREMENT's reproducibility -- "
                 "TASK-139 measured that w30 verdicts changed class between rounds for the "
                 "same command and the same code, while w90's did not."),
        "not_a_loosening": [
            "the check can only take a run OUT of PASS, never put one in",
            "it does not change `--window-frames`, `min_frames`, or either ruler's formula",
            "a run at or above the reporting window is byte-for-byte unaffected",
        ],
    }
    out["verdict_before_reporting_check"] = out.get("verdict")
    if below_reporting:
        out["counts_as_pass"] = False
        out["pass"] = False
        out["reporting_why"] = ("the run's nominal window is %d frames, below the declared "
                                "reporting window of %d, so its verdict is reported as a "
                                "REFERENCE and cannot count as a pass (TASK-140 §1.A.1)"
                                % (nominal, WINDOW_REPORTING_FRAMES))
    elif nominal is None:
        out["reporting_why"] = ("the nominal window was not recorded for this run, so the "
                                "reporting-window rule could not be applied (no PASS is "
                                "created or removed by a missing measurement)")
    else:
        out["reporting_why"] = ("the run's nominal window is %d frames >= the declared "
                                "reporting window of %d" % (nominal,
                                                            WINDOW_REPORTING_FRAMES))

    # -- TASK-140 §1.A.3: EVERY verdict carries its window and its round --------------------
    # A bare `PASS` is not attributable: TASK-139 measured that the same game can read PASS in
    # one round and INCONCLUSIVE in the next at w30.  The machine string in `verdict` is left
    # byte-for-byte alone (readers match on it), and the attribution lives beside it in
    # `verdict_context` / `qualified_verdict`.
    ctx = {
        "verdict": out.get("verdict"),
        "window_frames": nominal,
        "round": round_index,
        "reporting_frames": WINDOW_REPORTING_FRAMES,
        "at_reporting_window": (None if nominal is None else (not below_reporting)),
        "backend": backend,
        "player": player,
        "game": game,
        "change_margin": margin,
        "counts_as_pass": out.get("counts_as_pass"),
        "what": ("TASK-140 §1.A.3: a verdict is only attributable together with the window "
                 "budget it was measured at and the round (independent complete run) it came "
                 "from; TASK-139 measured that w30 verdicts were not reproducible across "
                 "rounds, so a bare verdict string is not evidence of a class"),
    }
    out["verdict_context"] = ctx
    out["qualified_verdict"] = qualified_verdict(out.get("verdict"), ctx)
    return out


def verdict_class(verdict):
    """The CLASS a verdict string belongs to (the thing `UNSTABLE` compares).

    TASK-140 §1.A.2: two runs are INCONSISTENT when their class differs.  `PASS` and
    `PASS(baseline only)` are deliberately different classes -- TASK-136 made the second one
    `counts_as_pass: false`, and TASK-139 measured `pong` flipping between exactly those two
    strings across rounds.  The prefix states (`WINDOW_TOO_SHORT ...`, `MODEL_*`) are classes
    of their own, as §1.A.2 requires.
    """
    v = "%s" % (verdict if verdict is not None else "")
    if v.startswith(STEP_VERDICT_WINDOW_TOO_SHORT):
        return STEP_VERDICT_WINDOW_TOO_SHORT
    for prefix in ("MODEL_FIXED_POINT", "MODEL_NO_PROGRESS"):
        if v.startswith(prefix):
            return prefix
    if v == PASS_BASELINE_ONLY:
        return PASS_BASELINE_ONLY
    if v == "PASS":
        return "PASS"
    if v.startswith("FAIL"):
        return "FAIL"
    if v.startswith("INCONCLUSIVE") or v.startswith(STEP_VERDICT_ACK_MISSING):
        return "INCONCLUSIVE"
    return v or "NONE"


def step_criterion_reading(rec):
    """The per-step criteria `UNSTABLE` names when two rounds disagree (TASK-140 §1.A.2)."""
    ack = rec.get("ack") or {}
    ch = rec.get("change") or {}
    strict = ch.get("strict") if isinstance(ch.get("strict"), dict) else {}
    return {
        "injected": ack.get("injected"),
        "accepted": ack.get("accepted"),
        "ack_missing": ack.get("ack_missing"),
        "changed": ch.get("changed"),
        "changed_strict": strict.get("changed"),
        "step_verdict": rec.get("step_verdict"),
        "pixel_diff": rec.get("pixel_diff"),
    }


def divergence_between(records_a, records_b, limit=40):
    """Which STEP and which CRITERION the two rounds disagree about (TASK-140 §1.A.2).

    Only the ATTRIBUTABLE per-step criteria are compared: whether the injection landed
    (`injected`), whether the game accepted it (`accepted`), whether the ack survived
    (`ack_missing`), and whether the picture moved under each margin (`changed` /
    `changed_strict` / `step_verdict`).  Raw pixel counts are recorded as CONTEXT, never as
    the disagreement itself -- they are expected to differ between rounds (TASK-139 measured
    6-12 `step_diffs` even inside one round).
    """
    by_a = dict((r.get("step"), r) for r in (records_a or []) if r.get("step"))
    by_b = dict((r.get("step"), r) for r in (records_b or []) if r.get("step"))
    out = []
    for s in sorted(set(list(by_a) + list(by_b))):
        ra, rb = by_a.get(s), by_b.get(s)
        if ra is None or rb is None:
            out.append({"step": s, "criterion": "step_present",
                        "round_a": ra is not None, "round_b": rb is not None})
            continue
        ca, cb = step_criterion_reading(ra), step_criterion_reading(rb)
        for k in ("injected", "accepted", "ack_missing", "changed", "changed_strict",
                  "step_verdict"):
            if ca.get(k) != cb.get(k):
                out.append({"step": s, "criterion": k, "round_a": ca.get(k),
                            "round_b": cb.get(k),
                            "context": {"pixel_diff": [ca.get("pixel_diff"),
                                                       cb.get("pixel_diff")]}})
        if len(out) >= limit:
            break
    return out[:limit]


def stability_summary(runs, min_rounds=STABILITY_MIN_ROUNDS):
    """TASK-140 §1.A.2: `UNSTABLE` -- do >= 2 independent rounds of ONE game agree?

    `runs` is a list of run summaries.  Each may carry `verdict_context` (written by
    `summarise`, TASK-140) and/or explicit `round` / `window_frames`; a run may also carry its
    per-step `records` (or a `steps_path`, which is read) so the disagreement can be named to
    the STEP and the CRITERION rather than merely counted.

    The rule, in full:
      * fewer than `min_rounds` runs                -> `INSUFFICIENT_ROUNDS` (no judgement);
      * every round in the same verdict CLASS       -> `STABLE`;
      * any round in a different class              -> `UNSTABLE`, with the divergent rounds
        and the per-step divergence points listed.

    `counts_as_pass` is true only for a STABLE set whose every round is a literal `PASS`; an
    `UNSTABLE` set can never pass -- the judgement can only REMOVE a pass (TASK-140 §2.7).
    """
    rounds = []
    for r in runs or []:
        ctx = r.get("verdict_context") or {}
        recs = r.get("records")
        if recs is None and r.get("steps_path") and os.path.isfile(r["steps_path"]):
            recs = load_jsonl(r["steps_path"])
        rounds.append({
            "round": r.get("round", ctx.get("round")),
            "window_frames": r.get("window_frames", ctx.get("window_frames")),
            "game": r.get("game", ctx.get("game")),
            "verdict": r.get("verdict", ctx.get("verdict")),
            "counts_as_pass": r.get("counts_as_pass", ctx.get("counts_as_pass")),
            "records": recs,
            "source": r.get("player_json") or r.get("source"),
        })
    rounds.sort(key=lambda x: (x["round"] is None, x["round"]))
    game = next((x["game"] for x in rounds if x.get("game")), None)
    windows = sorted(set(x["window_frames"] for x in rounds
                         if x.get("window_frames") is not None))
    out = {
        "state": None,
        "game": game,
        "window_frames": windows[0] if len(windows) == 1 else windows,
        "rounds": [x["round"] for x in rounds],
        "round_count": len(rounds),
        "min_rounds": int(min_rounds),
        "verdicts_by_round": dict((str(x["round"]), x["verdict"]) for x in rounds),
        "classes_by_round": dict((str(x["round"]), verdict_class(x["verdict"]))
                                 for x in rounds),
        "qualified_verdicts_by_round": dict(
            (str(x["round"]),
             qualified_verdict(x["verdict"], {"window_frames": x["window_frames"],
                                              "round": x["round"]})) for x in rounds),
        "counts_as_pass": False,
        "rule": ("TASK-140 §1.A.2: the same game run at the same window for >= %d independent "
                 "rounds is UNSTABLE when its verdict CLASS is not identical in every round; "
                 "an UNSTABLE game is listed with the divergent rounds and the step/criterion "
                 "they disagree about, and it NEVER counts as a pass" % int(min_rounds)),
        "not_a_loosening": [
            "the judgement can only REMOVE a pass: a stable all-PASS set passes, everything "
            "else fails to count, and an UNSTABLE set is never a pass",
            "the per-round verdicts are left untouched in their own `player.json`",
            "the class comparison includes `PASS(baseline only)` and `WINDOW_TOO_SHORT ...` "
            "as classes of their own, so a window-vs-window flip is not hidden",
        ],
    }
    if len(rounds) < int(min_rounds):
        out["state"] = "INSUFFICIENT_ROUNDS"
        out["why"] = ("only %d round(s) recorded; %d independent complete runs at the same "
                      "window are required before a stability judgement is made"
                      % (len(rounds), int(min_rounds)))
        return out
    classes = [verdict_class(x["verdict"]) for x in rounds]
    distinct = sorted(set(classes))
    out["distinct_classes"] = distinct
    if len(distinct) == 1:
        out["state"] = STABILITY_STATE_STABLE
        out["divergent_rounds"] = []
        out["divergence_points"] = []
        out["counts_as_pass"] = bool(distinct[0] == "PASS" and
                                     all(x.get("counts_as_pass") for x in rounds))
        out["why"] = ("all %d round(s) read the same class %r" % (len(rounds), distinct[0]))
        return out
    out["state"] = STABILITY_STATE_UNSTABLE
    out["counts_as_pass"] = False
    out["divergent_rounds"] = [x["round"] for x in rounds]
    pts = []
    base = rounds[0]
    for other in rounds[1:]:
        if verdict_class(other["verdict"]) == verdict_class(base["verdict"]):
            continue
        pts.extend(divergence_between(base.get("records"), other.get("records")))
    out["divergence_points"] = pts
    out["divergence_point_count"] = len(pts)
    out["compared_round_pair"] = [base["round"], [x["round"] for x in rounds[1:]]]
    out["why"] = ("the rounds disagree: %s -- the same game at the same window is not "
                  "reproducible, so its verdict is %s and cannot count as a pass"
                  % (", ".join("%s=%s" % (k, v) for k, v in
                               sorted(out["classes_by_round"].items())),
                     STABILITY_STATE_UNSTABLE))
    return out


def stability_from_paths(paths, min_rounds=STABILITY_MIN_ROUNDS):
    """`stability_summary` over a list of `player.json` paths (or run directories)."""
    runs = []
    for p in paths or []:
        pj = p
        if os.path.isdir(p):
            pj = os.path.join(p, "player.json")
        with io.open(pj, encoding="utf-8") as fh:
            doc = json.load(fh)
        steps_path = os.path.join(os.path.dirname(os.path.abspath(pj)), "steps.jsonl")
        runs.append({"player_json": os.path.abspath(pj),
                     "steps_path": steps_path if os.path.isfile(steps_path) else None,
                     "verdict": doc.get("verdict"),
                     "counts_as_pass": doc.get("counts_as_pass"),
                     "verdict_context": doc.get("verdict_context") or {},
                     "game": (doc.get("verdict_context") or {}).get("game")})
    return stability_summary(runs, min_rounds=min_rounds)


def nominal_frames_of_run(run_dir, context=None, player_doc=None):
    """The NOMINAL `--window-frames` a run was measured at -- including for OLD runs.

    `verdict_context.window_frames` is the first source (TASK-140 §1.A.3).  A run recorded
    before this batch does not have it, but it is still a FACT about that run: TASK-139's
    `session.json -> measurement_window.frames` carries the very budget the loop used.
    Reading it closes the hole where a historical `--window-frames 30` run kept counting as a
    pass because the new field was absent -- the absence of a field is not evidence that the
    window was long enough.

    Returns `(frames, source)`; `(None, None)` when the run really did not record it (then no
    reporting-window judgement is made: the tool may not invent a measurement).
    """
    ctx = context or {}
    if ctx.get("window_frames") is not None:
        try:
            return int(ctx["window_frames"]), "player.json->verdict_context"
        except Exception:  # noqa: BLE001
            pass
    vc = (player_doc or {}).get("verdict_context") or {}
    if vc.get("window_frames") is not None:
        try:
            return int(vc["window_frames"]), "player.json->verdict_context"
        except Exception:  # noqa: BLE001
            pass
    p = os.path.join(run_dir or "", "session.json")
    if run_dir and os.path.isfile(p):
        try:
            with io.open(p, encoding="utf-8") as fh:
                doc = json.load(fh)
            f = (doc.get("measurement_window") or {}).get("frames")
            if f is not None:
                return int(f), "session.json->measurement_window.frames"
        except Exception:  # noqa: BLE001
            pass
    return None, None


def qualified_verdict(verdict, context):
    """`PASS @w90 r2` -- the verdict string with its window and round appended.

    TASK-140 §1.A.3.  The plain `verdict` is never rewritten (`counts_as_pass` and every
    existing reader depend on its exact spelling); this is the human/audit-facing label, and
    it is written into `player.json`, printed by the tool, and quoted by the report.
    """
    ctx = context or {}
    v = "%s" % (verdict,)
    w = ctx.get("window_frames")
    r = ctx.get("round")
    if w is None and r is None:
        return "%s (@window unrecorded, round unrecorded)" % v
    label = "%s @w%s r%s" % (v, "?" if w is None else w, "?" if r is None else r)
    if ctx.get("at_reporting_window") is False:
        label += " [reference only: window %s < reporting %s]" % (w,
                                                                 ctx.get("reporting_frames"))
    return label


def _summarise_core(records, backend=None, game=None, state=None, player="model",
                    margin=CHANGE_MARGIN_DEFAULT):
    """`steps.jsonl` -> the TASK-132 §1.2 three-state verdict.

    * FAIL   : at least one step is `FAIL_no_change_after_accepted_input` (the user's
               qualifying condition), or the accepted-but-static ratio is below the bar;
    * PASS   : >= 8 steps, and among the ACCEPTED steps >= 75% changed, and the loop was
               not stuck on one action forever (the INCONCLUSIVE guard);
    * INCONCLUSIVE: fewer than 8 steps, an all-one-action loop, a refusal/abstain that
               made "accepted?" unanswerable, or too few accepted steps to compute a rate.
    The per-step `changed` is the game-facing half; the "does this change match the game's
    rules" half is the reader's judgement (TASK-132 §1.3) and is passed in separately.

    `margin` selects the change reading this ONE pass uses (TASK-135 §1.B); the public
    `summarise` runs both and files them side by side.
    """
    steps = [r for r in (records or []) if r.get("step")]
    n = len(steps)
    # A step where the model produced NO injectable action was never sent to the game:
    # it is evidence about the MODEL, not about the game, and it is counted separately.
    model_steps = [r for r in steps if (r.get("ack") or {}).get("injected")]
    no_action = [r["step"] for r in steps if not (r.get("ack") or {}).get("injected")]
    accepted = [r for r in model_steps if (r.get("ack") or {}).get("accepted")]
    # -- TASK-139 §1.B: the LEGAL-REFUSAL carve-out, as a predicate inside the ONE summary --
    # `refused` is the game's own record that it saw this input and deliberately said no.
    # Such a step may NOT be charged to the game as "accepted and nothing changed": it is
    # dropped from the denominator AND from the FAIL set, and the run must still clear
    # `min_real_progress_steps` of REAL progress.  A run with NO refusals is byte-for-byte
    # unchanged (every list below is empty and every rate has the same denominator).
    def _is_refused(r):
        sr = r.get("step_refusal")
        if isinstance(sr, dict):
            return bool(sr.get("refused_legal"))
        return bool((r.get("ack") or {}).get("refusal"))

    refused = [r for r in accepted if _is_refused(r)]
    refused_steps = [r["step"] for r in refused]
    refused_set = set(refused_steps)
    # The denominator of every rate below: accepted steps that were NOT a legal refusal.
    rated = [r for r in accepted if r["step"] not in refused_set]
    # TASK-139 §1.B: `changed` and every rate below are computed over the RATED steps.  A
    # legal refusal is not evidence against the game, so it must not sit in the denominator
    # either -- and it is never counted as a change (it did not change anything).  With no
    # refusals `rated == accepted` and every number is byte-for-byte the pre-TASK-139 value.
    changed = [r for r in rated if changed_of(r, margin)]
    # "Real progress" = a step with no legal refusal that beat its own control window.  It is
    # the quantity the refusal boundary's floor counts, so a refusal can never be progress.
    real_progress = [r["step"] for r in accepted
                     if r["step"] not in refused_set and changed_of(r, margin)]
    # The unavoidable twin of the carve-out: a run that was refused everywhere made NO
    # progress at all, and is reported under its own key with counts_as_pass=false.
    refusal_only_run = bool(refused and not real_progress and not rated)
    # The FAIL condition, read under THIS margin.  Under `baseline` this set is exactly the
    # set of steps whose recorded `step_verdict` is FAIL (that verdict is the baseline
    # reading, written by the loop while the run was happening); under `strict` it is the
    # same question asked with the stricter margin, and the baseline set is kept beside it.
    fail_steps = [r["step"] for r in steps
                  if r.get("step_verdict") == "FAIL_no_change_after_accepted_input"] \
        if margin == "baseline" else \
        [r["step"] for r in accepted if not changed_of(r, "strict")]
    # TASK-139 §1.B: a legal refusal is not a FAIL of the game.  The step verdict recorded
    # while the run was happening (`FAIL_no_change_after_accepted_input`) is left alone --
    # it is the raw per-step reading -- but the VERDICT's FAIL set drops the refused steps,
    # and they are listed separately as `refused_steps` with their own evidence.  The raw
    # set is kept beside it so the carve-out can never hide how much it removed.
    fail_steps_raw = list(fail_steps)
    fail_steps = [s for s in fail_steps if s not in refused_set]
    fail_recs = [r for r in steps if r["step"] in fail_steps]

    actions = [r.get("action", {}).get("action") for r in steps]
    distinct = sorted(set(a for a in actions if a))
    # --- evidence quality of the FAIL steps (a distinction the verdict MUST carry) -----
    # The user's FAIL condition can be reached two ways, and they mean different things:
    #   (a) the model VARIED its action and the game still would not move  -> a real
    #       "accepted input, frozen picture" signal about the GAME;
    #   (b) the model stayed on ONE action and was handed a byte-identical frame every
    #       step (its fixed point) -> the run cannot separate "the game ignores this input"
    #       from "the model stopped playing"; TASK-132 §1.2 lists exactly this as
    #       INCONCLUSIVE evidence, so it is reported as such instead of being amplified
    #       into a game verdict by repetition.
    fail_actions = sorted(set(r.get("action", {}).get("action") for r in fail_recs))
    fail_reqs = sorted(set((r.get("model") or {}).get("request_path") for r in fail_recs))
    fail_frames = sorted(set(r.get("frame_before_sha") for r in fail_recs))
    unchanged_terminal = (state or {}).get("terminal_stop") or None
    # TASK-139 §1.B: a LEGAL REFUSAL is not a model-side fixed-point candidate either.  The
    # fixed-point clause exists to separate "the game ignores this input" from "the model
    # stopped playing", and a refused input is neither: the game demonstrably saw it.
    # Refused steps are excluded from the fixed-point set (the raw per-step verdict is left
    # untouched) so a run whose only static steps were refusals is judged by the run, not by
    # a model clause that does not apply to it.
    fail_recs_fp = [r for r in fail_recs if r["step"] not in refused_set]
    fp_actions = sorted(set(r.get("action", {}).get("action") for r in fail_recs_fp))
    fp_reqs = sorted(set((r.get("model") or {}).get("request_path") for r in fail_recs_fp))
    fp_frames = sorted(set(r.get("frame_before_sha") for r in fail_recs_fp))
    same_action_fixed_point = bool(
        len(fail_steps) >= 2 and len(fp_actions) == 1 and
        (len(fp_reqs) <= 1 or len(fp_frames) <= 1))
    # TASK-133 §1.C.1: the model's fixed point as its OWN conclusion, on its own
    # threshold (>= 3 identical action + identical frame).  It is a statement about the
    # model, so it lives beside the game verdict instead of inside it.  TASK-139 §1.B: legal
    # refusals are excluded -- a refused step is the game saying it saw the input, so it
    # cannot be a sample of "the model stopped playing".
    fixed = model_fixed_point([r for r in steps if r["step"] not in refused_set])
    # TASK-134 §1.C.1: the second, wider model-side conclusion.  Computed and REPORTED
    # here; it deliberately does not enter any branch of the game verdict below, so the
    # game's FAIL/PASS/INCONCLUSIVE reading is byte-for-byte the rule TASK-132/133 used.
    noprog = model_no_progress([r for r in steps if r["step"] not in refused_set])
    # TASK-134 §1.A: the GAME-side numbers, which answer "can this game be played" on
    # their own.  `progress_steps` counts the SENT steps whose picture advanced more than
    # its own no-input control window: the same predicate `decide_changed` already uses.
    injected_steps_list = [r for r in steps if (r.get("ack") or {}).get("injected")]
    progress_steps = [r["step"] for r in injected_steps_list
                      if changed_of(r, margin)]
    # TASK-139 §1.B: a step the game's own counters record as a deliberate refusal is not
    # progress in EITHER reading, whatever it did to the picture.  The list above is
    # therefore filtered by refusal first, and the same filter is applied to the two
    # per-margin readings so `progress_step_count*` and the refusal floor can never
    # disagree about whether a refused step advanced the game.
    progress_steps = [s for s in progress_steps if s not in refused_set]
    # TASK-135 §1.B: the same count under the OTHER margin, so a reader of `player.json`
    # never has to open the step files to see whether the two readings differ.
    progress_steps_baseline = [s for s in (r["step"] for r in injected_steps_list
                                           if changed_of(r, "baseline"))
                               if s not in refused_set]
    progress_steps_strict = [s for s in (r["step"] for r in injected_steps_list
                                         if changed_of(r, "strict"))
                             if s not in refused_set]
    # `real_progress` (computed above) is the same set as `progress_steps`; it is what the
    # refusal boundary's floor counts, and these are its per-margin twins.
    real_progress_steps = list(progress_steps)
    real_progress_steps_baseline = list(progress_steps_baseline)
    real_progress_steps_strict = list(progress_steps_strict)
    rated_step_list = [r["step"] for r in rated]
    stamps = [(r.get("ts_ms"), r.get("step")) for r in steps
              if isinstance(r.get("ts_ms"), (int, float))]
    match_seconds = None
    if len(stamps) >= 2:
        match_seconds = round((stamps[-1][0] - stamps[0][0]) / 1000.0, 3)
    out = {
        "backend": backend, "game": game, "steps": n,
        "player": player,
        "model_fixed_point": fixed,
        "MODEL_FIXED_POINT": bool(fixed.get("found")),
        "MODEL_FIXED_POINT_reading": fixed.get("reading"),
        "model_no_progress": noprog,
        "MODEL_NO_PROGRESS": bool(noprog.get("found")),
        "MODEL_NO_PROGRESS_reading": noprog.get("reading"),
        "MODEL_NO_PROGRESS_what": noprog.get("what"),
        "progress_steps": progress_steps,
        "progress_step_count": len(progress_steps),
        "progress_steps_baseline": progress_steps_baseline,
        "progress_steps_strict": progress_steps_strict,
        "progress_step_count_baseline": len(progress_steps_baseline),
        "progress_step_count_strict": len(progress_steps_strict),
        "progress_rate_of_injected": (round(len(progress_steps) / float(len(injected_steps_list)), 4)
                                      if injected_steps_list else None),
        "progress_rate_of_accepted": (round(len(progress_steps) / float(len(accepted)), 4)
                                      if accepted else None),
        # TASK-139 §1.B: the same rate over the RATED steps (accepted steps that were not a
        # legal refusal).  This is the rate the game-side verdict uses, and it is what the
        # refusal carve-out is allowed to change; `progress_rate_of_accepted` above keeps
        # the pre-TASK-139 denominator so both readings are visible side by side.
        "progress_rate_of_rated": (round(len(progress_steps) / float(len(rated)), 4)
                                   if rated else None),
        "change_margin_used": margin,
        "match_seconds_in_game_clock": match_seconds,
        "game_clock_first_last_ms": ([stamps[0][0], stamps[-1][0]] if len(stamps) >= 2
                                     else None),
        "steps_without_an_action_from_the_model": no_action,
        "injected_steps": len(model_steps),
        "accepted_steps": len(accepted), "changed_steps_of_accepted": len(changed),
        # TASK-139 §1.B: the denominator is the RATED steps (accepted, minus legal refusals).
        # When no step was a refusal this is identical to `accepted_steps`, so every number
        # this field ever held before is unchanged.
        "rated_denominator": len(rated),
        "accepted_and_changed_rate": (round(len(changed) / float(len(rated)), 4)
                                      if rated else None),
        # -- TASK-139 §1.B: the legal-refusal reading, beside the raw one ------------------
        "refused_steps": refused_steps,
        "refused_step_count": len(refused),
        "refusal_steps_evidence": [
            {"step": r["step"], "action": (r.get("action") or {}).get("action"),
             "refusal": r.get("step_refusal"),
             "step_verdict_recorded": r.get("step_verdict")}
            for r in refused],
        "rated_steps": rated_step_list,
        "rated_step_count": len(rated),
        "rated_and_changed_rate": (round(len(changed) / float(len(rated)), 4)
                                   if rated else None),
        "real_progress_steps": real_progress_steps,
        "real_progress_step_count": len(real_progress_steps),
        "real_progress_steps_baseline": real_progress_steps_baseline,
        "real_progress_step_count_baseline": len(real_progress_steps_baseline),
        "real_progress_steps_strict": real_progress_steps_strict,
        "real_progress_step_count_strict": len(real_progress_steps_strict),
        "real_progress_rate_of_rated": (round(len(real_progress_steps) / float(len(rated)), 4)
                                        if rated else None),
        "refusal_only_run": refusal_only_run,
        "refusal_boundary": {
            "declared_by": REFUSAL_BOUNDARY.get("declared_by"),
            "source": REFUSAL_BOUNDARY.get("source"),
            "min_real_progress_steps": REFUSAL_MIN_REAL_PROGRESS,
            "min_real_progress_rate": REFUSAL_MIN_REAL_PROGRESS_RATE,
            "basis": REFUSAL_BOUNDARY.get("basis"),
            "rule": ("a step the game's own counters record as a DELIBERATE refusal is "
                     "dropped from the FAIL set and from the rate's denominator; it is never "
                     "counted as progress, and a run must still show >= "
                     "%d steps of real progress (>= %.2f of its rated steps) to PASS"
                     % (REFUSAL_MIN_REAL_PROGRESS, REFUSAL_MIN_REAL_PROGRESS_RATE)),
            "not_a_loosening": [
                "the refusal carve-out can only remove a FAIL that the game itself recorded "
                "as a refusal; it can never turn a 'not changed' into a 'changed'",
                "every run needs min_real_progress_steps of REAL progress, so a game that "
                "refused every input cannot PASS on refusals",
                "a run with no refusals has an empty refused set and every number below is "
                "the pre-TASK-139 number",
            ],
        },
        "fail_steps_before_refusal_carve_out": fail_steps_raw,
        "fail_steps_dropped_as_legal_refusals": [s for s in fail_steps_raw
                                                 if s in refused_set],
        "fail_steps": fail_steps,
        "fail_evidence": {
            "distinct_actions_in_the_failing_steps": fail_actions,
            "distinct_request_bodies_in_the_failing_steps": len(fail_reqs),
            "distinct_before_frames_in_the_failing_steps": len(fail_frames),
            "same_action_fixed_point": same_action_fixed_point,
            "game_reached_a_terminal_state": bool(unchanged_terminal),
            "reading": ("the model varied its action and the game still did not move: the "
                        "strong reading of the user's FAIL condition"
                        if not same_action_fixed_point else
                        "the model locked onto ONE action and was given a byte-identical "
                        "frame each step, so the run cannot separate 'the game ignores this "
                        "action' from 'the model stopped playing' (TASK-132 §1.2 marks that "
                        "INCONCLUSIVE)"),
        },
        "distinct_actions": distinct,
        "one_action_loop": bool(len(model_steps) >= PASS_MIN_STEPS and len(distinct) <= 1),
        "thresholds": {"min_steps": PASS_MIN_STEPS, "min_rate": PASS_MIN_RATE,
                       "model_fixed_point_min_run": MODEL_FIXED_POINT_MIN_RUN,
                       "model_no_progress_min_run": MODEL_NO_PROGRESS_MIN_RUN,
                       "min_real_progress_steps": REFUSAL_MIN_REAL_PROGRESS,
                       "min_real_progress_rate": REFUSAL_MIN_REAL_PROGRESS_RATE,
                       "window_min_frames": WINDOW_MIN_FRAMES,
                       "change_margin": margin,
                       "change_margin_gameplay_control_factor":
                           CHANGE_MARGIN_DECLARATION[margin]["gameplay_control_factor"],
                       "change_margin_pixel_control_factor":
                           CHANGE_MARGIN_DECLARATION[margin]["pixel_control_factor"]},
        "rule": "PASS = >=%d injected steps AND accepted-and-changed rate >= %.2f AND the "
                "reader confirmed the changes match the game's declared logic; FAIL = an "
                "accepted input left the viewport unchanged; INCONCLUSIVE = the evidence "
                "cannot separate the two.  MODEL_FIXED_POINT is a separate conclusion about "
                "the MODEL (>= %d steps of the same action on the same frame) and "
                "MODEL_NO_PROGRESS is its wider twin (>= %d consecutive sent steps with no "
                "gameplay progress even if the actions differ): NEITHER is a game defect and "
                "NEITHER is ever a PASS, and neither is allowed to change the game verdict.  "
                "TASK-135 §1.B: `changed` above uses the %r change margin (gameplay "
                "movement factor %.2f); the other margin's reading is filed beside it as "
                "baseline_*/strict_* and in `change_margin`.  TASK-139 §1.B: a step the "
                "game's OWN counters record as a deliberate refusal is not a FAIL and is "
                "dropped from the rate's denominator, but it is never progress and a run "
                "must still show >= %d steps of real progress"
                % (PASS_MIN_STEPS, PASS_MIN_RATE, MODEL_FIXED_POINT_MIN_RUN,
                   MODEL_NO_PROGRESS_MIN_RUN, margin,
                   CHANGE_MARGIN_DECLARATION[margin]["gameplay_control_factor"],
                   REFUSAL_MIN_REAL_PROGRESS),
    }
    # TASK-139 §1.B: without a refusal carve-out this run would have been FAIL already.
    # With one, the refusal is not evidence against the game -- but it is not evidence FOR
    # it either, and a run in which NOTHING ever advanced is an explicit FAIL.  Varied
    # actions/frames are the case this branch exists for; a single repeated action is
    # already caught above by the model-side fixed-point clauses (also not a PASS).
    if refusal_only_run:
        out["verdict"] = "FAIL"
        out["why"] = ("every rated step was a DELIBERATE refusal recorded by the game's own "
                      "counters (steps %s) and no step produced real progress, so the "
                      "refusal carve-out has nothing to stand on: a game that refuses "
                      "everything is not a game that can be played (TASK-139 §1.B)"
                      % refused_steps)
    elif fail_steps and not same_action_fixed_point and not unchanged_terminal:
        out["verdict"] = "FAIL"
        out["why"] = ("%d step(s) had an ACCEPTED input and an unchanged viewport "
                      "(user's FAIL condition): %s" % (len(fail_steps), fail_steps))
    elif fail_steps and same_action_fixed_point:
        out["verdict"] = "INCONCLUSIVE"
        out["why"] = ("the user's FAIL condition did occur on step(s) %s, but every failing "
                      "step shows the SAME action (%s) and the model was handed a "
                      "byte-identical frame, so the evidence cannot separate 'the game "
                      "ignores this input' from 'the model stopped playing' (TASK-132 §1.2)"
                      % (fail_steps, fail_actions))
    elif unchanged_terminal:
        out["verdict"] = "INCONCLUSIVE"
        out["why"] = ("the game declared a TERMINAL state at step %s, so every later frame "
                      "is frozen by the game's own rule and the run cannot show what the "
                      "model could have done with a live game (TASK-132 §1.2)%s"
                      % ((unchanged_terminal or {}).get("step"),
                         ("" if not fail_steps else
                          "; the FAIL condition also occurred on step(s) %s" % fail_steps)))
    elif fixed.get("found"):
        # TASK-133 §1.C.1: a run that is mostly the model's fixed point cannot produce a
        # game verdict.  The fixed point is reported, the game verdict says why it is not
        # a FAIL.
        out["verdict"] = "INCONCLUSIVE"
        out["why"] = ("the MODEL reached a fixed point (%s), so this run cannot produce a "
                      "verdict about the GAME: %s"
                      % (fixed.get("steps"), fixed.get("reading")))
    elif out["one_action_loop"]:
        out["verdict"] = "INCONCLUSIVE"
        out["why"] = ("the model produced the SAME action (%s) on every one of %d injected "
                      "steps, so 'did it accept / did it change' cannot be told apart from "
                      "'the model never really played'" % (distinct, len(model_steps)))
    elif len(model_steps) < PASS_MIN_STEPS:
        out["verdict"] = "INCONCLUSIVE"
        out["why"] = ("only %d step(s) carried an injectable action (of %d run); the user's "
                      "PASS rule needs >= %d.  %s"
                      % (len(model_steps), n, PASS_MIN_STEPS,
                         "The run stopped early because the game declared a TERMINAL state "
                         "-- see `terminal_stop`: after that every frame is frozen by the "
                         "game's own rule, so no further steps could measure anything."
                         if (state or {}).get("terminal_stop") else ""))
    elif not accepted:
        out["verdict"] = "INCONCLUSIVE"
        out["why"] = "no step's input was acknowledged by the game, so there is no rate"
    elif refused_steps and len(real_progress) < REFUSAL_MIN_REAL_PROGRESS:
        # The floor under the carve-out.  It is reached ONLY when refusals removed the
        # denominator: a run with NO refusals is judged by the rate alone, exactly as before
        # TASK-139, so this clause can never tighten a run the old criterion passed.  (When
        # there ARE refusals, the floor stops "mostly refused, barely advanced" from being
        # carried by the refusals that were dropped.)
        out["verdict"] = "INCONCLUSIVE"
        out["why"] = ("only %d step(s) of REAL progress (%s) after the legal-refusal "
                      "carve-out removed step(s) %s; the boundary needs >= %d, because a "
                      "game that mostly refuses has not shown it can be played "
                      "(TASK-139 §1.B)"
                      % (len(real_progress), real_progress, refused_steps,
                         REFUSAL_MIN_REAL_PROGRESS))
    elif out["accepted_and_changed_rate"] < PASS_MIN_RATE:
        out["verdict"] = "FAIL"
        out["why"] = ("accepted-and-changed rate %.4f < %.2f over %d rated step(s)%s"
                      % (out["accepted_and_changed_rate"], PASS_MIN_RATE, len(rated),
                         ("" if not refused_steps else
                          " (the %d legal refusal(s) on step(s) %s are excluded from the "
                          "FAIL set and from this denominator but are NOT counted as "
                          "progress)" % (len(refused_steps), refused_steps))))
    else:
        out["verdict"] = "PASS"
        out["why"] = ("%d/%d rated steps changed the viewport (%.4f) over %d step(s)%s; "
                      "the reader's per-frame check corroborates it"
                      % (len(changed), len(rated), out["accepted_and_changed_rate"], n,
                         ("" if not refused_steps else
                          ", with %d step(s) (%s) dropped as LEGAL REFUSALS recorded by the "
                          "game's own counters (they are not counted as progress either)"
                          % (len(refused_steps), refused_steps))))
    # TASK-134 §1.A.3: the GAME-side verdict, reported beside the model verdict and only
    # when the arm that produced the records was the SCRIPTED player.
    #
    # Why a second reading is legitimate here, and why it is not a loosening: the two
    # clauses it drops (`one_action_loop`, `MODEL_FIXED_POINT`) are by construction
    # statements about a MODEL's behaviour -- they exist because "the model stopped
    # playing" cannot be told apart from "the game ignored the input".  A deterministic
    # scripted policy has no such ambiguity, and it is deliberately allowed to repeat an
    # action.  Every numeral in this reading (>= 8 injected steps, >= 75% progress,
    # FAIL on any accepted-but-unchanged step) is the SAME threshold the model arm is held
    # to; only the two model-evidence clauses are inapplicable.  The model arm's own
    # `verdict` below/above is untouched and remains the only verdict used for the model.
    if player == "scripted":
        if fail_steps:
            out["game_side_verdict"] = "FAIL"
            out["game_side_why"] = ("%d SENT action(s) left the picture unchanged vs the "
                                    "same-frame-budget no-input control window: steps %s"
                                    % (len(fail_steps), fail_steps))
        elif len(injected_steps_list) < PASS_MIN_STEPS:
            out["game_side_verdict"] = "INCONCLUSIVE"
            out["game_side_why"] = ("only %d step(s) carried an injectable action; the "
                                    "game-side rule needs >= %d"
                                    % (len(injected_steps_list), PASS_MIN_STEPS))
        elif not accepted:
            out["game_side_verdict"] = "INCONCLUSIVE"
            out["game_side_why"] = "no step's input was acknowledged by the game"
        elif refusal_only_run:
            # TASK-139 §1.B: the same boundary the model verdict applies, applied to the
            # game-side reading.  `progress_rate_of_accepted` divides by the RATED steps, so
            # without this branch a game that refused everything would divide 0 by 0.
            out["game_side_verdict"] = "FAIL"
            out["game_side_why"] = ("the game recorded a DELIBERATE refusal on every rated "
                                    "step (%s) and no step produced real progress, so 'all "
                                    "refused' cannot be a PASS (TASK-139 §1.B)"
                                    % refused_steps)
        elif len(real_progress) < REFUSAL_MIN_REAL_PROGRESS and refused_steps:
            out["game_side_verdict"] = "INCONCLUSIVE"
            out["game_side_why"] = ("only %d step(s) of REAL progress after the legal-refusal "
                                    "carve-out; the boundary needs >= %d"
                                    % (len(real_progress), REFUSAL_MIN_REAL_PROGRESS))
        elif out["progress_rate_of_rated"] < PASS_MIN_RATE:
            out["game_side_verdict"] = "FAIL"
            out["game_side_why"] = ("game-side progress rate %.4f < %.2f over %d rated "
                                    "step(s)%s" % (out["progress_rate_of_rated"],
                                                   PASS_MIN_RATE, len(rated),
                                                   ("" if not refused_steps else
                                                    " (legal refusals %s excluded)"
                                                    % refused_steps)))
        else:
            out["game_side_verdict"] = "PASS"
            out["game_side_why"] = ("%d/%d rated steps advanced the game (%.4f) over %d "
                                    "step(s) of a deterministic human-like policy%s; the "
                                    "model-evidence clauses (one-action loop, fixed point) "
                                    "do not apply to a scripted policy"
                                    % (len(progress_steps), len(rated),
                                       out["progress_rate_of_rated"], n,
                                       ("" if not refused_steps else
                                        ", with %s dropped as legal refusals"
                                        % refused_steps)))
        out["game_side_rule"] = ("same thresholds as the model arm (>= %d injected steps, "
                                 ">= %.2f progress, FAIL on any accepted-but-unchanged "
                                 "step, >= %d steps of real progress); only the two "
                                 "MODEL-evidence clauses are dropped, and they are dropped "
                                 "because a scripted policy has no 'stopped playing' "
                                 "ambiguity to resolve"
                                 % (PASS_MIN_STEPS, PASS_MIN_RATE,
                                    REFUSAL_MIN_REAL_PROGRESS))
    return out


# ---------------------------------------------------------------------------
# TASK-134 §1.A/§1.B: the readable state, and the two arms that consume it
# ---------------------------------------------------------------------------
# The declared fields each game exports that a HUMAN would read off the screen to play it.
# This table lives here (not in `playability_controls.json`) on purpose: it is the
# DECLARATIVE VARIANT's payload, not the game's capability declaration, and TASK-134 says
# every such addition must be switchable, side-by-side with the baseline and evidenced --
# which is what `--variant=V2` does.  The values themselves come from the game's own
# `probe_state_source` read, i.e. from inside the running game.
READABLE_STATE_FIELDS = {
    "pong": ["Ball.pos", "Ball.Velocity", "PaddleLeft.pos", "PaddleRight.pos",
             "ScoreLeft.text", "ScoreRight.text", "WinLabel.text", "WinScore"],
    "snake": ["HeadX", "HeadY", "DirectionX", "DirectionY", "Food.CellX", "Food.CellY",
              "FoodsEaten", "Length", "Score", "GameOver", "WaitingForStart", "Started",
              "Paused", "Ticks", "Columns", "Rows", "LastRefusedInput"],
    "tetris": ["PieceX", "PieceY", "PieceRot", "PieceKind", "NextKind", "Gravity",
               "DropInterval", "Lines", "Score", "Level", "FilledCells", "GameOver",
               "Ticks"],
    "game2048": ["GridString", "Score", "MoveCount", "EmptyCells", "MaxTile",
                 "CanMoveAny", "GameOver", "TilesInUse", "MovesRejected",
                 "LastMoveDir", "LastMoveMoved"],
    "puzzlebobble": ["ShooterCol", "ShooterColor", "NextColor", "AngleIndex", "Board",
                     "Score", "Shots", "TotalCleared", "TotalDropped", "ProjActive",
                     "ProjCol", "ProjRow", "GameOver", "Failed", "ShooterCol"],
    # TASK-136 §1.B: the other FIFTEEN games.  Every name below was read out of the game's
    # own exported fields (the settle-state dump of its last recorded run, re-read with
    # `runs/model-player/_scripts/t136_fields.py`), not guessed: a scripted policy may only
    # read what the running game really exports, and `readable_state` reports anything it
    # could not find under `fields_the_game_did_not_export` instead of inventing a zero.
    "asteroids": ["ShipX", "ShipY", "ShipVelX", "ShipVelY", "ShipAngle", "Thrusting",
                  "BulletActive", "BulletX", "BulletY", "ShotsFired", "AsteroidsRemaining",
                  "AsteroidsDestroyed", "Score", "Lives", "GameOver", "Won", "Ticks"],
    "bomberman": ["PlayerCol", "PlayerRow", "BombsActive", "BombsPlaced", "BricksDestroyed",
                  "BricksRemaining", "Detonations", "Exploded", "EnemiesAlive", "Lives",
                  "Score", "GameOver", "RejectedMoves", "FuseSteps", "Ticks"],
    "breakout": ["Ball.pos", "BallX", "BallY", "BallSpeedX", "BallSpeedY", "Launched",
                 "Paddle.pos", "Paddle.MinX", "Paddle.MaxX", "PaddleBounces",
                 "BricksBroken", "BricksRemaining", "Score", "Ticks", "Over", "Won"],
    "flappy": ["BirdX", "BirdY", "BirdVelocity", "PipesPassed", "PipesRecycled", "Score",
               "GameOver", "Won", "Restarts", "FrameCount", "Ticks", "Pipe0X", "Pipe0GapY"],
    "frogger": ["FrogCol", "FrogRow", "FrogX", "FrogY", "Score", "Lives", "HomesReached",
                "GameOver", "Won", "RejectedSteps", "Ticks", "Car0X", "Log0X"],
    "lunarlander": ["Lx", "Ly", "Vx", "Vy", "AngleDeg", "AngleIndex", "Fuel", "FuelUsed",
                    "ThrustOn", "ThrustCount", "Rotations", "Crashed", "Landed", "GameOver",
                    "Won", "Steps", "Score", "Ticks"],
    "match3": ["Board", "CursorCol", "CursorRow", "TotalCleared", "MaxChain", "Cascades",
               "Refills", "LastCleared", "Score", "Moves", "MovesLimit", "GameOver", "Won",
               "Ticks"],
    "minesweeper": ["CursorCol", "CursorRow", "RevealedCount", "RemainingSafe",
                    "FlaggedCount", "FlagToggles", "RevealsAccepted", "Exploded",
                    "ExplodedCol", "ExplodedRow", "GameOver", "Won", "Moves", "Ticks"],
    "missilecommand": ["CursorX", "CursorY", "Ammo", "Fired", "InterceptorAlive",
                       "IncomingAlive", "ExplosionsActive", "CitiesAlive", "Destroyed",
                       "Leaked", "Spawned", "Score", "Wave", "GameOver", "Won", "Ticks"],
    "pacman": ["PacCol", "PacRow", "PacX", "PacY", "PelletsEaten", "PelletsRemaining",
               "Score", "Lives", "GameOver", "Won", "RejectedSteps", "Ghost0X", "Ghost0Y",
               "GhostCount", "Ticks"],
    "platformer": ["PlayerX", "PlayerY", "VelX", "VelY", "OnGround", "Facing", "Jumps",
                   "AirJumps", "JumpsRejected", "Collected", "GemsRemaining", "Score",
                   "Lives", "GameOver", "Won", "Frames", "Ticks"],
    "rtype": ["PlayerX", "PlayerY", "BulletsActive", "BulletsFired", "EnemiesAlive",
              "EnemiesKilled", "EnemiesSpawned", "EnemiesEscaped", "Score", "Lives",
              "GameOver", "Won", "Moves", "Steps", "Wave", "Ticks"],
    "sokoban": ["PlayerCol", "PlayerRow", "Steps", "Pushes", "UndoDepth", "BoxesOnGoal",
                "BoxesOffGoal", "BoxesTotal", "CanMoveAny", "Deadlocked", "LastPush",
                "RejectedMoves", "Won", "Ticks"],
    "spaceinvaders": ["PlayerX", "BulletX", "BulletY", "BulletActive", "ShotsFired",
                      "InvadersKilled", "InvadersRemaining", "Score", "Lives", "GameOver",
                      "Won", "WaveX", "WaveY", "WaveDir", "WaveSteps", "Ticks"],
    "towerdefense": ["CursorCol", "CursorRow", "Gold", "TowersPlaced", "EnemiesAlive",
                     "EnemiesSpawned", "EnemiesKilled", "EnemiesLeaked", "Lives", "Score",
                     "GameOver", "Won", "Steps", "Wave", "SpawnCountdown", "Ticks"],
}


def _node_by_leaf(nodes, leaf):
    """The shallowest node whose path's last segment is `leaf` (path, entry) or None."""
    best = None
    for path, e in (nodes or {}).items():
        if path.rsplit("/", 1)[-1] == leaf:
            if best is None or len(path) < len(best[0]):
                best = (path, e)
    return best


def readable_state(game, state, marker_decl=None, last=None, extra_fields=None):
    """TASK-134 §1.B/V2: the readable state, as the model would have to read the screen.

    Everything in it is read out of the RUNNING GAME's own exported properties (the same
    `probe_state_source` read the gate already trusts): the ball and paddle positions, the
    snake's head/direction/food, the falling piece, the 2048 board string, the bubble
    board.  `last` carries what the previous step did (its action, whether it changed
    anything, and which declared gameplay observables moved) -- TASK-134 §1.B/V4 requires
    exactly that sentence to be available to the model.

    Returns a flat, deliberately small dict: the `jev` backend caps `state` at 2048 tokens
    (measured ratios in JEV_TOKEN_SAFETY_BASIS), and V2's whole point is to add the state
    WITHOUT dropping the image.
    """
    nodes = (state or {}).get("nodes") or {}
    values, missing = {}, []
    for spec in list(READABLE_STATE_FIELDS.get(game) or []) + list(extra_fields or []):
        if "." in spec:
            leaf, field = spec.rsplit(".", 1)
        else:
            leaf, field = "Main", spec
        hit = _node_by_leaf(nodes, leaf)
        val = (hit[1] or {}).get(field) if hit else None
        if val is None:
            # fall back to any node that carries the field name (the root script node is
            # the usual case, and it is what the gate's own declaration points at)
            for _p, e in nodes.items():
                if field in e:
                    val = e[field]
                    break
        if val is None:
            missing.append(spec)
        values[spec] = val
    out = {"game": game,
           "frame_drawn": (state or {}).get("drawn"),
           "game_time_ms": (state or {}).get("ms"),
           "values": values}
    if missing:
        out["fields_the_game_did_not_export"] = missing
    if marker_decl:
        out["markers"] = marker_values(state, marker_decl)
    if last:
        out["previous_step"] = {
            "action": last.get("action"),
            "result": last.get("result"),
            "viewport_pixels_changed": last.get("pixel_diff"),
            "declared_gameplay_observables_that_moved": last.get("gameplay_changes"),
            "note": last.get("note"),
        }
    return out


def readable_state_text(rs, max_chars=1400):
    """The readable state as a compact, model-facing sentence block (V2/V4 on playjev).

    PlayJev's serve.py has no text-state channel (a text `state` is a 400: serve.py:41-42),
    so the V2 payload is carried in the action question's own free-text `instructions`
    instead.  What the model is told is exactly the same content, and the run records the
    text verbatim, so the two backends' V2 arms are comparable.
    """
    parts = []
    for k, v in sorted((rs.get("values") or {}).items()):
        if v is None:
            continue
        parts.append("%s=%s" % (k, json.dumps(v, ensure_ascii=False)))
    body = "READABLE GAME STATE: " + "; ".join(parts)
    prev = rs.get("previous_step") or {}
    if prev.get("action"):
        body += ("\nPREVIOUS STEP: action=%s result=%s."
                 % (prev.get("action"), prev.get("result")))
    return body[:max_chars]


# The declarative variants (TASK-134 §1.B).  Each is switchable on the command line, each
# is filed beside the baseline rather than replacing it, and each run's verbatim request
# body is on disk.  `--variant=V1` is byte-identical to the pre-TASK-134 baseline.
VARIANT_IDS = ("V1", "V2", "V3", "V4", "V5")
VARIANT_NOTES = {
    "V1": "baseline: ONE full-window image + ONE `choice` question whose criteria are the "
          "game's declared actions (the TASK-132/133 arm, unchanged)",
    "V2": "image + structured readable STATE (jev: the request's own `state` field; "
          "playjev: serve.py refuses a text state, so the same text is carried in the "
          "action question's `instructions` and the run records that)",
    "V3": "the question asks which action PUSHES THE GAME FORWARD and every criterion "
          "describes what THAT ACTION WILL DO to the picture/state, instead of naming it",
    "V4": "V3 plus the anti-repeat rule: when the previous action produced no change it is "
          "written into the state AND REMOVED from the candidate list",
    "V5": "the image FORM varies (full 800x600 / cropped to the game viewport / "
          "downsampled to 400x300); `--image-form` selects it",
}

VARIANT_INSTRUCTIONS = {
    "V1": ("Look at the picture of the game and choose the single next input a human "
           "player would press, to keep playing. Answer with one of the listed actions."),
    "V3": ("Look at the picture of the game. Which single action NOW PUSHES THE GAME "
           "FORWARD? Each option below says what that action will do to the picture and to "
           "the game state. Choose the one that advances the game, and answer with one of "
           "the listed options."),
    "V4": ("Look at the picture of the game. Which single action NOW PUSHES THE GAME "
           "FORWARD? Each option below says what that action will do to the picture and to "
           "the game state. An action that produced no change on the previous step has "
           "already been REMOVED from the list -- do not look for it. Answer with one of "
           "the listed options."),
}


def image_for_model(rec, form, outdir):
    """TASK-134 §1.B/V5: which IMAGE FORM the model is shown, recorded as a fact.

    `full` keeps the 800x600 full-window frame the baseline uses.  `crop` cuts to the
    content bbox the frame analysis already measured (the game viewport, with 12 px of
    padding), and `downsample` resizes to 400x300.  The derived PNG is a REAL file on disk
    with its own sha256, so the exact bytes the model received are checkable; the frame the
    CHANGE test uses is always the original full frame, so V5 can never move the goalposts
    of the change measurement.
    """
    from PIL import Image

    src = rec.get("path")
    out = {"form": form, "source_path": src, "source_sha256": rec.get("sha256"),
           "source_width_height": [rec.get("width"), rec.get("height")]}
    if not src or not os.path.isfile(src):
        out["error"] = "no readable source frame"
        return out
    if form == "full":
        out.update({"path": src, "sha256": rec.get("sha256"),
                    "width": rec.get("width"), "height": rec.get("height")})
        return out
    im = Image.open(src).convert("RGB")
    if form == "crop":
        bb = rec.get("bbox")
        if bb and bb[2] > 32 and bb[3] > 32:
            pad = 12
            x0 = max(0, int(bb[0]) - pad)
            y0 = max(0, int(bb[1]) - pad)
            x1 = min(im.width, int(bb[0]) + int(bb[2]) + pad)
            y1 = min(im.height, int(bb[1]) + int(bb[3]) + pad)
            im = im.crop((x0, y0, x1, y1))
            out["crop_box"] = [x0, y0, x1, y1]
        else:
            out["crop_box"] = None
            out["crop_note"] = ("the frame analysis found no usable content bbox, so the "
                                "crop fell back to the full 800x600 frame")
    elif form == "downsample":
        im = im.resize((400, 300), Image.LANCZOS)
    else:
        out["error"] = "unknown image form %r" % form
        out.update({"path": src, "sha256": rec.get("sha256")})
        return out
    dst = os.path.join(outdir, "%03d_model_image_%s.png" % (rec.get("index"), form))
    im.save(dst, format="PNG")
    out.update({"path": dst, "sha256": sha256_file(dst),
                "width": im.width, "height": im.height})
    return out


_2048_MOVES = {"m2048_left": (-1, 0), "m2048_right": (1, 0),
               "m2048_up": (0, -1), "m2048_down": (0, 1)}


def _2048_parse(grid_string, n=4):
    rows = []
    for line in str(grid_string or "").split("/")[:n]:
        cells = []
        for c in line.split(",")[:n]:
            try:
                cells.append(int(c))
            except (TypeError, ValueError):
                cells.append(0)
        while len(cells) < n:
            cells.append(0)
        rows.append(cells)
    while len(rows) < n:
        rows.append([0] * n)
    return rows


def _2048_slide(line):
    """compress + merge left (the game's own rule, applied in the client for the POLICY)."""
    vals = [v for v in line if v]
    out, i = [], 0
    while i < len(vals):
        if i + 1 < len(vals) and vals[i] == vals[i + 1]:
            out.append(vals[i] * 2)
            i += 2
        else:
            out.append(vals[i])
            i += 1
    return out + [0] * (len(line) - len(out))


def _2048_moved(grid, action, n=4):
    dx, dy = _2048_MOVES[action]
    if dx:
        for r in range(n):
            line = grid[r] if dx < 0 else list(reversed(grid[r]))
            new = _2048_slide(line)
            new = new if dx < 0 else list(reversed(new))
            if new != grid[r]:
                return True
        return False
    for c in range(n):
        col = [grid[r][c] for r in range(n)]
        line = col if dy < 0 else list(reversed(col))
        new = _2048_slide(line)
        new = new if dy < 0 else list(reversed(new))
        if new != col:
            return True
    return False


class ScriptedPlayerAgent(object):
    """TASK-134 §1.A.1: the deterministic, human-like SCRIPTED player arm.

    Why it exists
    -------------
    TASK-133 measured `pong x jev`'s "playable window" with `PONG_TICK` and read 23 s -> 18 s,
    which looked like "the game got worse"; the real cause was that the model never touched
    the left paddle (TASK-133 §4.2, `LEFT 5:0` -> `RIGHT 5:0`).  "The model did not play" and
    "the game cannot be played" had been folded into one number.  This arm separates them: it
    is a fixed policy, it reads the same exported state, it returns the SAME action dict the
    model arm returns, and the loop's injection channel, ack evidence and equal-frame-budget
    control-window change test are byte-for-byte the same code.  What it measures is the GAME.

    What it is NOT
    --------------
    Not a model, not a gate criterion, and not a substitute for the model arm.  It never
    communicates with 8080/8081.  Its `check_health` says so explicitly, and its per-step
    decision record is written to the run directory beside the model's verbatim requests.
    """

    name = "scripted"

    def __init__(self, game, objective="", options=None):
        self.game = game
        self.objective = objective or ""
        self.options = options or {}
        self.base_url = "scripted://local-policy/%s" % game
        self.hold_ms = int(self.options.get("hold_ms", 350))
        self.errors = []
        self.calls = []
        self.last_evidence = None
        self._mem = {}
        self.policy = {
            "pong": self._pong, "snake": self._snake, "tetris": self._tetris,
            "game2048": self._m2048, "puzzlebobble": self._pb,
            # TASK-136 §1.B: the other fifteen games.  Without these the scripted arm could
            # only answer "no scripted policy is declared for this game" -> `wait` -> zero
            # injected steps -> INCONCLUSIVE for 15 of the 20 games, which is exactly what
            # `TASK-136 §1.B` ("the scripted arm must cover 20/20") forbids.
            "asteroids": self._ast, "bomberman": self._bomberman,
            "breakout": self._breakout, "flappy": self._flappy, "frogger": self._frogger,
            "lunarlander": self._lunarlander, "match3": self._match3,
            "minesweeper": self._minesweeper, "missilecommand": self._missilecommand,
            "pacman": self._pacman, "platformer": self._platformer, "rtype": self._rtype,
            "sokoban": self._sokoban, "spaceinvaders": self._spaceinvaders,
            "towerdefense": self._towerdefense,
        }.get(game)

    def check_health(self):
        return {"url": None, "status": 200,
                "json": {"scripted": True, "game": self.game,
                         "policy": bool(self.policy),
                         "note": "TASK-134 §1.A.1 scripted player: no model service is "
                                 "contacted by this arm"}}

    def report(self):
        return {"backend": "scripted", "game": self.game, "objective": self.objective,
                "policy_available": bool(self.policy),
                "policy_memory": dict(self._mem),
                "calls": len(self.calls), "errors": self.errors,
                "note": "the scripted arm answers 'can the GAME be played'; the model arm "
                        "answers 'can the MODEL play it'"}

    # -- helpers -----------------------------------------------------------
    def _act(self, name, goal, why):
        acts = set((goal or {}).get("actions") or {})
        if not name or name not in acts:
            return {"type": "wait", "ms": 100,
                    "why": "policy wanted %r, which this game does not declare (%s)"
                           % (name, sorted(acts))}
        return {"type": "action", "action": name, "pressed": True,
                "hold_ms": self.hold_ms, "why": why}

    @staticmethod
    def _f(v, i, default=0.0):
        try:
            return float(v[i])
        except (TypeError, ValueError, IndexError):
            return default

    # -- policies ----------------------------------------------------------
    def _pong(self, v, goal):
        ball = v.get("Ball.pos") or [0, 0, 16, 16]
        vel = v.get("Ball.Velocity") or [0, 0]
        pl = v.get("PaddleLeft.pos") or [24, 0, 16, 100]
        by = self._f(ball, 1) + self._f(ball, 3, 16) / 2.0
        py = self._f(pl, 1) + self._f(pl, 3, 100) / 2.0
        if abs(self._f(vel, 0)) < 0.5 and abs(self._f(vel, 1)) < 0.5:
            return self._act("pong_serve", goal,
                             "the ball is parked (Velocity=0,0); a human serves with SPACE")
        if self._f(vel, 0) > 0:
            # the ball is travelling AWAY: re-centre, exactly as a human prepares
            target = 276.0
            return self._act("pong_left_up" if py > target + 10 else
                             ("pong_left_down" if py < target - 10 else "wait"),
                             goal, "ball is flying right; re-centre the left paddle")
        if py - by > 10:
            return self._act("pong_left_up", goal,
                             "ball centre y=%.1f is above paddle centre y=%.1f" % (by, py))
        if by - py > 10:
            return self._act("pong_left_down", goal,
                             "ball centre y=%.1f is below paddle centre y=%.1f" % (by, py))
        return self._act("wait", goal,
                         "paddle is already lined up with the ball (dy=%.1f)" % (by - py))

    def _snake(self, v, goal):
        if v.get("GameOver"):
            return self._act("snake_restart", goal, "GameOver; a human presses R to restart")
        if v.get("Paused"):
            return self._act("snake_pause", goal, "the game is paused; unpause")
        if v.get("WaitingForStart") or not v.get("Started"):
            return self._act("snake_right", goal,
                             "WaitingForStart: any direction key starts the run")
        hx, hy = v.get("HeadX"), v.get("HeadY")
        fx, fy = v.get("Food.CellX"), v.get("Food.CellY")
        dx, dy = v.get("DirectionX"), v.get("DirectionY")
        cols, rows = v.get("Columns") or 25, v.get("Rows") or 21
        if None in (hx, hy, fx, fy, dx, dy):
            return self._act("wait", goal, "the head/food/direction fields are not exported")
        cur = (dx, dy)
        name = {(-1, 0): "snake_left", (1, 0): "snake_right",
                (0, -1): "snake_up", (0, 1): "snake_down"}
        cands = []
        for cand in ((1, 0), (-1, 0), (0, 1), (0, -1)):
            if cand == (-cur[0], -cur[1]):
                continue                      # reversal = instant death
            nx, ny = hx + cand[0], hy + cand[1]
            if not (0 <= nx < cols and 0 <= ny < rows):
                continue                      # wall
            cands.append((abs(fx - nx) + abs(fy - ny), cand))
        if not cands:
            return self._act(name.get(cur), goal,
                             "cornered: only the current direction is legal")
        cands.sort(key=lambda t: t[0])
        # TASK-134: the game's OWN rule decides what a press does.  `SnakeGame.cs`
        # `TrySetDirection` steps the snake ONLY when the requested direction differs from
        # the current one ("a 'keep going' press is not a steering change", SnakeGame.cs
        # 414-421); pressing the direction it already faces is a no-op.  The DEFAULT policy
        # here is the naive human one -- steer toward the food -- and the declared
        # `--scripted-alternate` arm is the game-rule-aware one that always TURNS when it
        # wants to advance.  Both are recorded; neither changes the game.
        pick = None
        if self.options.get("snake_alternate_turns"):
            for _d, c in cands:
                if c != cur:
                    pick = c
                    break
        if pick is None:
            pick = cands[0][1]
        return self._act(name[pick], goal,
                         "head=(%s,%s) food=(%s,%s) dir=(%s,%s); steer toward the food "
                         "without reversing%s"
                         % (hx, hy, fx, fy, dx, dy,
                            " (alternate-turn policy: the request is a CHANGE of direction "
                            "because the game only steps on a change)" if pick != cur else
                            " (the only legal request is the current direction, which the "
                            "game treats as a no-op)"))

    def _tetris(self, v, goal):
        plan = self._mem.get("tet_plan") or []
        if plan:
            nxt = plan.pop(0)
            self._mem["tet_plan"] = plan
            return self._act(nxt, goal, "executing the plan for this piece (%d left)" % len(plan))
        px = v.get("PieceX")
        if px is None:
            return self._act("wait", goal, "PieceX is not exported")
        targets = [0, 9, 2, 7, 4]
        n = int(self._mem.get("tet_n") or 0)
        t = targets[n % len(targets)]
        self._mem["tet_n"] = n + 1
        kind = v.get("PieceKind")
        plan = []
        if kind is not None and int(kind) % 2 == 0:
            plan.append("tetris_rotate")
        plan += ["tetris_left"] * max(0, int(px) - t)
        plan += ["tetris_right"] * max(0, t - int(px))
        plan.append("tetris_drop")
        self._mem["tet_plan"] = plan[1:]
        self._mem["tet_target"] = t
        return self._act(plan[0], goal,
                         "piece at x=%s -> target column %d, then drop" % (px, t))

    def _m2048(self, v, goal):
        grid = _2048_parse(v.get("GridString"))
        acts = list((goal or {}).get("actions") or {})
        order = [a for a in ("m2048_left", "m2048_up", "m2048_right", "m2048_down")
                 if a in acts]
        if not v.get("CanMoveAny", True):
            return self._act("wait", goal, "the game reports CanMoveAny=false")
        for a in order:
            if _2048_moved(grid, a):
                return self._act(a, goal,
                                 "the first configured direction that really moves the "
                                 "board (grid=%s)" % v.get("GridString"))
        return self._act("wait", goal, "no configured direction moves the board")

    def _pb(self, v, goal):
        """Aim a little, then fire -- the loop a human actually plays here.

        MEASURED correction: `pb_left`/`pb_right` do NOT move the shooter sideways, they
        change the AIM ANGLE (`AngleIndex` 2->3->4->0->1 over the whole arc; `ShooterCol`
        stays at 4 in the TASK-133 build).  A first draft of this policy aimed by column
        and therefore never reached its "target" and never fired (`Shots` stayed 0 for 20
        steps).  The policy below is the corrected, declared one: it sweeps the aim and
        fires every fourth step, so the projectile, the attachment and the clear logic are
        all exercised.
        """
        if v.get("ProjActive"):
            return self._act("wait", goal, "a projectile is in flight; let it resolve")
        angle = v.get("AngleIndex")
        if angle is None:
            return self._act("wait", goal, "AngleIndex is not exported")
        n = int(self._mem.get("pb_aim") or 0) + 1
        self._mem["pb_aim"] = n
        self._mem["pb_angle_last"] = angle
        if n % 4 == 0:
            return self._act("pb_shoot", goal,
                             "aim has been swept for %d step(s) (AngleIndex=%s, "
                             "ShooterColor=%s, NextColor=%s); fire"
                             % (n, angle, v.get("ShooterColor"), v.get("NextColor")))
        return self._act("pb_right", goal,
                         "sweep the aim: AngleIndex %s -> %s (the aim dots move with it)"
                         % (angle, (int(angle) + 1) % 5))

    # -- TASK-136 §1.B: the other fifteen policies -------------------------
    #
    # Each one is a DECLARED, deterministic, human-shaped policy over the actions the game
    # itself declares in its InputMap.  Rules they all follow:
    #   * every action name is one the game declares (checked by `_act`, which answers the
    #     explicit "policy wanted X, which this game does not declare" `wait` otherwise);
    #   * the sequence is fixed, so the run is reproducible from the code alone;
    #   * the policy prefers the move a human would make (advance, aim, shoot), and only
    #     falls back to a sweep when the state it would need is not exported;
    #   * it NEVER presses a pause/restart key unless the game says it is over.
    def _cycle(self, v, goal, names, label):
        """Walk a fixed action cycle, skipping any action this game does not declare."""
        n = int(self._mem.get("cyc_n") or 0)
        self._mem["cyc_n"] = n + 1
        acts = (goal or {}).get("actions") or {}
        for k in range(len(names)):
            name = names[(n + k) % len(names)]
            if name in acts:
                return self._act(name, goal, "%s (cycle step %d)" % (label, n + 1))
        return self._act("wait", goal, "%s: none of %s is declared" % (label, names))

    def _ast(self, v, goal):
        if v.get("GameOver") or v.get("Lives") == 0:
            return self._act("wait", goal, "GameOver / no lives left")
        # rotate first (ShipAngle moves, the ship stays inside the field), fire on the
        # second beat, thrust on the fourth: a human's turn-shoot-drift loop.
        return self._cycle(v, goal,
                           ["ast_left", "ast_fire", "ast_right", "ast_thrust"], "asteroids")

    def _bomberman(self, v, goal):
        if v.get("GameOver"):
            return self._act("wait", goal, "GameOver")
        return self._cycle(v, goal,
                           ["bomb_place", "bomb_right", "bomb_place", "bomb_down",
                            "bomb_place", "bomb_left", "bomb_place", "bomb_up"],
                           "bomberman: plant a bomb, step away, plant again")

    def _breakout(self, v, goal):
        if v.get("Over") or v.get("Won"):
            return self._act("wait", goal, "the round is over")
        if not v.get("Launched"):
            return self._act("breakout_launch", goal,
                             "the ball is parked (Launched=false); a human serves")
        ball = v.get("Ball.pos") or [v.get("BallX"), v.get("BallY"), 14, 14]
        pad = v.get("Paddle.pos") or [352, 540, 96, 16]
        bx = self._f(ball, 0)
        px = self._f(pad, 0) + self._f(pad, 2, 96) / 2.0
        if bx > px + 8:
            return self._act("breakout_right", goal,
                             "ball x=%.1f is right of paddle centre %.1f" % (bx, px))
        if bx < px - 8:
            return self._act("breakout_left", goal,
                             "ball x=%.1f is left of paddle centre %.1f" % (bx, px))
        return self._act("wait", goal,
                         "paddle is under the ball (dx=%.1f); let the bounce happen"
                         % (bx - px))

    def _flappy(self, v, goal):
        if v.get("GameOver"):
            return self._act("flappy_restart", goal, "GameOver; a human presses R")
        y = v.get("BirdY")
        gap = v.get("Pipe0GapY")
        if y is None:
            return self._act("wait", goal, "BirdY is not exported")
        target = gap if gap is not None else 300.0
        if self._f([y], 0, 300.0) > self._f([target], 0, 300.0) - 20:
            return self._act("flap", goal,
                             "bird y=%.0f is at/below the gap centre y=%.0f; flap"
                             % (y, target))
        return self._act("wait", goal,
                         "bird y=%.0f is above the gap centre y=%.0f; let gravity work"
                         % (y, target))

    def _frogger(self, v, goal):
        if v.get("GameOver") or v.get("Lives") == 0:
            return self._act("wait", goal, "GameOver / no lives left")
        row = v.get("FrogRow")
        if row is None:
            return self._act("wait", goal, "FrogRow is not exported")
        if int(row) > int(v.get("GoalRow") if v.get("GoalRow") is not None else 0):
            # hop toward the goal row, with a sideways nudge every third hop so the frog
            # does not try to cross a solid goal post forever
            n = int(self._mem.get("frog_n") or 0)
            self._mem["frog_n"] = n + 1
            if n % 3 == 2:
                return self._act("frog_right" if (n // 3) % 2 == 0 else "frog_left", goal,
                                 "sideways nudge before the next hop (row=%s)" % row)
            return self._act("frog_up", goal, "hop up toward row 0 (now row=%s)" % row)
        return self._act("frog_down", goal, "back to the start strip to try again")

    def _lunarlander(self, v, goal):
        if v.get("GameOver") or v.get("Crashed") or v.get("Landed"):
            return self._act("wait", goal, "the run is over")
        # burn, correct the attitude, burn again: Fuel/ThrustCount and AngleDeg all move, so
        # the picture really changes even while the physics clock is stopped.
        return self._cycle(v, goal,
                           ["ll_thrust", "ll_rotate_left", "ll_rotate_right", "ll_thrust"],
                           "lunarlander: burn and hold the attitude")

    def _match3(self, v, goal):
        if v.get("GameOver"):
            return self._act("wait", goal, "GameOver")
        return self._cycle(v, goal,
                           ["m3_right", "m3_swap", "m3_down", "m3_swap",
                            "m3_left", "m3_swap", "m3_up", "m3_swap"],
                           "match3: move the cursor and swap")

    def _minesweeper(self, v, goal):
        if v.get("GameOver"):
            return self._act("wait", goal, "GameOver")
        return self._cycle(v, goal,
                           ["mine_reveal", "mine_right", "mine_reveal", "mine_down",
                            "mine_reveal", "mine_left", "mine_reveal", "mine_up"],
                           "minesweeper: reveal, move, reveal")

    def _missilecommand(self, v, goal):
        if v.get("GameOver"):
            return self._act("wait", goal, "GameOver")
        return self._cycle(v, goal,
                           ["mc_left", "mc_fire", "mc_right", "mc_fire"],
                           "missilecommand: sweep the battery and fire")

    def _pacman(self, v, goal):
        if v.get("GameOver") or v.get("Lives") == 0:
            return self._act("wait", goal, "GameOver / no lives left")
        # stay off the walls: reverse when the last move was refused, otherwise keep going
        return self._cycle(v, goal,
                           ["pac_left", "pac_up", "pac_right", "pac_down"], "pacman")

    def _platformer(self, v, goal):
        if v.get("GameOver") or v.get("Lives") == 0:
            return self._act("wait", goal, "GameOver / no lives left")
        # run right toward the goal, jump every other step
        n = int(self._mem.get("plat_n") or 0)
        self._mem["plat_n"] = n + 1
        if n % 2 == 1:
            return self._act("plat_jump", goal, "jump (step %d)" % (n + 1))
        return self._act("plat_right", goal, "run right toward the goal (step %d)" % (n + 1))

    def _rtype(self, v, goal):
        if v.get("GameOver") or v.get("Lives") == 0:
            return self._act("wait", goal, "GameOver / no lives left")
        return self._cycle(v, goal,
                           ["rt_left", "rt_fire", "rt_right", "rt_fire",
                            "rt_up", "rt_fire", "rt_down", "rt_fire"],
                           "rtype: weave and shoot")

    def _sokoban(self, v, goal):
        if v.get("Won"):
            return self._act("wait", goal, "the level is solved")
        if not v.get("CanMoveAny", True):
            return self._act("wait", goal, "the game reports CanMoveAny=false")
        # walk around the one box and push it: up/left/up/right, then repeat
        return self._cycle(v, goal,
                           ["soko_up", "soko_left", "soko_up", "soko_right",
                            "soko_up", "soko_left", "soko_down", "soko_right"],
                           "sokoban: walk and push")

    def _spaceinvaders(self, v, goal):
        if v.get("GameOver") or v.get("Lives") == 0:
            return self._act("wait", goal, "GameOver / no lives left")
        return self._cycle(v, goal,
                           ["si_fire", "si_left", "si_fire", "si_right"],
                           "spaceinvaders: fire and slide")

    def _towerdefense(self, v, goal):
        if v.get("GameOver") or v.get("Lives") == 0:
            return self._act("wait", goal, "GameOver / no lives left")
        # place a tower near the path, then move the cursor on
        return self._cycle(v, goal,
                           ["td_place", "td_right", "td_right", "td_place",
                            "td_down", "td_place", "td_left", "td_up"],
                           "towerdefense: place towers along the path")

    # -- the interface -----------------------------------------------------
    def decide(self, frames, state, goal):
        rs = state if isinstance(state, dict) else {}
        values = rs.get("values") if isinstance(rs.get("values"), dict) else {}
        if self.policy is None:
            self.errors.append({"kind": "policy",
                                "error": "no scripted policy for game %r" % self.game})
            act = {"type": "wait", "ms": 100,
                   "why": "no scripted policy is declared for this game"}
        else:
            try:
                act = self.policy(values, goal or {})
            except Exception as e:  # noqa: BLE001 - the loop must never die on the policy
                self.errors.append({"kind": "policy",
                                    "error": "%s: %s" % (type(e).__name__, e)})
                act = {"type": "wait", "ms": 100, "why": "policy raised: %s" % e}
        self.calls.append({"n": len(self.calls) + 1, "action": act, "state": rs})
        self.last_evidence = {
            "request_payload": {"kind": "scripted_policy", "game": self.game,
                                "policy": (self.policy.__name__ if self.policy else None),
                                "readable_state": rs},
            "request_meta": {"with_image": bool(frames), "question_count": 0,
                             "question_keys": [], "scripted_arm": True,
                             "note": "TASK-134 §1.A.1: this arm sends NOTHING to a model "
                                     "service; the record exists so the arm's decisions are "
                                     "auditable beside the model's verbatim requests"},
            "transport": {"status": None, "body": None, "headers": None, "attempts": []},
            "action": act,
        }
        return act


# ---------------------------------------------------------------------------
# the runner
# ---------------------------------------------------------------------------
class Player(object):
    def __init__(self, args):
        self.args = args
        self.game = args.game
        self.backend = args.backend
        # TASK-134 §1.A: `player` selects WHICH ARM runs.  `model` is the TASK-132/133 arm;
        # `scripted` is the deterministic human-like policy that answers the game-side
        # question.  `variant` is the declarative V1..V5 switch (§1.B) and `image_form` is
        # V5's payload.  All three are recorded in session.json and player.json, so no run
        # can be mistaken for another.
        self.player = getattr(args, "player", "model")
        self.variant = getattr(args, "variant", "V1")
        self.image_form = getattr(args, "image_form", "full")
        if self.player == "scripted":
            # the scripted arm contacts no service, so its run directory names the ARM, not
            # a model that was never called
            self.backend = "scripted"
        self.outdir = os.path.join(RUNS_PLAYER, args.out_prefix or "", self.game, self.backend)
        self.frames_dir = os.path.join(self.outdir, "frames")
        self.states_dir = os.path.join(self.outdir, "states")
        self.calls_dir = os.path.join(self.outdir, "calls")
        self.model_images_dir = os.path.join(self.outdir, "model-images")
        for d in (self.frames_dir, self.states_dir, self.calls_dir, self.model_images_dir):
            if not os.path.isdir(d):
                os.makedirs(d)
        self.steps = []
        self.frames = []
        self.frame_index = 0
        self.mcp = None
        self.gp = None
        self.errors = []
        self.osd = {}
        self.win = None
        self.proj = None
        self.controls = None
        self.terminal_stop = None
        self.terminal_at_settle = None
        # TASK-134 §1.B/V4: what the PREVIOUS step did, as the anti-repeat rule needs it.
        self.last_step_result = None
        self.excluded_action = None
        # TASK-134 §1.B: the readable state built for the CURRENT step, which
        # `choice_criteria` -> `action_effect` reads to describe each candidate.
        self.current_readable_state = {}
        # TASK-138 defect ⑨: one entry per step whose injection answered without an
        # `ack_result`.  Written into `player.json -> ack_missing` so a run that lost its ack
        # cannot look like a run that measured nothing wrong.
        self.ack_missing = []
        # TASK-138 defect ⑧: one entry per step recording the two windows' ACTUAL drawn-frame
        # counts and whether they matched.  Written into `player.json -> frame_alignment`.
        self.frame_alignment = []

    # -- MCP ---------------------------------------------------------------
    def gd(self, code, at):
        r = self.mcp.call_tool("running_game_execute_gdscript", {"code": code},
                               timeout=self.args.call_timeout)
        if not r.get("ok"):
            self.errors.append({"at": at, "error": r.get("error")})
            return None, r
        return r["value"].get("result"), r

    def sample_state(self, label):
        val, r = self.gd(probe_state_source(), "state:" + label)
        rec = {"label": label, "state": val, "call": r,
               "sha256": canonical_state_sha(val) if isinstance(val, dict) else None}
        if isinstance(val, dict):
            write_json(os.path.join(self.states_dir, label + ".json"), val)
        return rec

    def capture(self, label):
        r = self.mcp.call_tool("running_game_capture_screenshot", {})
        rec = {"label": label, "ok": bool(r.get("ok")), "call": r}
        if not r.get("ok"):
            rec["error"] = r.get("error")
            self.frames.append(rec)
            return None
        v = r["value"] or {}
        b64 = v.get("image_base64")
        if not b64:
            rec["error"] = "no image_base64 in the answer"
            self.frames.append(rec)
            return None
        png = base64.b64decode(b64)
        self.frame_index += 1
        idx = self.frame_index
        fname = "%03d_%s.png" % (idx, label)
        fpath = os.path.join(self.frames_dir, fname)
        with open(fpath, "wb") as fh:
            fh.write(png)
        rec.update(analyse_frame(fpath))
        rec["path"] = fpath
        rec["index"] = idx
        rec["sha256"] = sha256_file(fpath)
        rec["width_height"] = [rec.get("width"), rec.get("height")]
        rec["mcp_call_n"] = (r or {}).get("n")
        self.frames.append(rec)
        return rec

    def inject_action(self, action):
        """`Input.parse_input_event` for the action's own declared key (the gate's channel)."""
        kc = first_keycode(self.proj, action)
        if kc is None:
            return None, {"error": "action %r has no declared keycode" % action}
        res, call = self.gd(probe_action_kc_down(kc, action), "inject:" + action)
        seq = [(call or {}).get("n")]
        return res, {"channel": "Input.parse_input_event", "tool": "running_game_execute_gdscript",
                     "godot_keycode": kc, "key": keyname_of(kc), "seq": seq,
                     "call_args": {"code": probe_action_kc_down(kc, action)},
                     "result": res}

    def release_action(self, action):
        kc = first_keycode(self.proj, action)
        if kc is None:
            return None
        res, call = self.gd(probe_action_kc_up(kc, action), "release:" + action)
        return {"seq": (call or {}).get("n"), "result": res}

    def ack_after_inject(self, action):
        """Read the game's own InputMap state for the action, after a short settle.

        The delay matters and is recorded: an OS key arrives on the game's message queue and
        is turned into an `InputEventKey` by the DisplayServer, so a read issued in the same
        millisecond as `SendInput` can see the InputMap before the engine has processed the
        message.  The first real-key pong run measured exactly that (`state_moved` was the
        only ack evidence, while the identical synthetic arm read
        `Input.is_action_pressed()==true`).
        """
        if self.args.ack_read_delay_ms:
            time.sleep(self.args.ack_read_delay_ms / 1000.0)
        res, call = self.gd(probe_action_state(action), "ack:" + action)
        return res, (call or {}).get("n")

    # -- real OS key arm (TASK-132 §1.1 step 3, optional) -------------------
    def inject_real_key(self, action):
        from real_input_probe import (send_key, godot_key_to_vk, try_foreground,
                                      EXTENDED_VKS)
        kc = first_keycode(self.proj, action)
        vk = godot_key_to_vk(kc)
        if vk is None:
            return None, {"error": "no Windows VK for godot keycode %r" % kc}
        win = self.win
        foc = try_foreground(win["hwnd"]) if win else {"ok": False,
                                                       "why": "no game window found"}
        dn = send_key(vk, up=False, extended=vk in EXTENDED_VKS)
        time.sleep(self.args.hold_ms / 1000.0)
        st, n = self.ack_after_inject(action)
        # The InputMap-triggered events the game just processed: Godot records nothing
        # itself, so the receipt is read through the InputMap state above; the game's own
        # `_UnhandledInput`/`_Input` handlers are what turn it into gameplay.  What can be
        # said without guessing is recorded verbatim below.
        up = send_key(vk, up=True, extended=vk in EXTENDED_VKS)
        return {"channel": "OS_SendInput", "tool": "user32!SendInput",
                "godot_keycode": kc, "key": keyname_of(kc), "vk": vk,
                "keydown": dn, "keyup": up, "focus": foc,
                "is_action_pressed_while_down": (st or {}).get("is_action_pressed",
                                                               (st or {}).get("pressed")),
                "ack_seq": [n], "sent": [dn.get("returned"), up.get("returned")],
                "ack_read_delay_ms": self.args.ack_read_delay_ms,
                "ack_after_keydown": st,
                "focus_evidence": {"hwnd": (win or {}).get("hwnd"),
                                   "rect": (win or {}).get("rect"),
                                   "title": (win or {}).get("title"),
                                   "class": (win or {}).get("class")}}, None

    # -- model --------------------------------------------------------------
    def build_goal(self):
        acts = action_set_from_project(self.proj, self.args.actions)
        objective = (self.args.objective
                     or ((self.controls.get(self.controls_game) or {}).get("goal"))
                     or "play the game: choose the input a human player would choose next")
        # `keys: []` on purpose: the model's decision space is the game's OWN declared
        # InputMap actions.  `action_criteria` would otherwise add a `key_W`-style option
        # per README key, which both double-counts the same physical key and makes the
        # probability table harder to read (the model answered `key_SPACE` 0.228 next to
        # `pong_serve` 0.236 in the first smoke run, and those are the same key).
        return {"game": self.game, "objective": objective, "actions": acts, "keys": []}

    def make_agent(self):
        # TASK-134 §1.A.1: the SCRIPTED arm.  It is deliberately the same interface, so
        # every measurement downstream (injection channel, ack read, control window,
        # change test) is the same code as the model arm's.
        if self.player == "scripted":
            return ScriptedPlayerAgent(self.game, self.build_goal().get("objective"),
                                       {"hold_ms": int(self.args.hold_ms),
                                        "snake_alternate_turns": bool(
                                            getattr(self.args,
                                                    "scripted_alternate", False))})
        base = self.args.base_url or DEFAULT_BACKENDS[self.backend]
        # The instruction is part of the measurement: it must ask for exactly one game
        # input and must not offer stopping, because "stop probing" is not an answer this
        # loop can use (the loop decides when to stop).  Endings:
        #   "done" is removed from the criteria by `action_set_from_project`'s caller
        #   (`build_goal` -> the agent's `action_criteria` builds it from the action set
        #   plus `wait`; `done` is added by `action_criteria`'s own default, so the
        #   criteria are rebuilt here to drop it).
        # TASK-134 §1.B: for V3/V4 the question itself changes ("which action pushes the
        # game forward"), and for V4 a second sentence states that the last no-change
        # action was removed.  The default (V1) text is byte-identical to TASK-132/133.
        if self.args.action_instructions:
            instr = self.args.action_instructions
        else:
            instr = VARIANT_INSTRUCTIONS.get(self.variant, VARIANT_INSTRUCTIONS["V1"])
        opts = {"base_url": base, "send_images": True,
                "decision_path": "/v1/systemone", "hold_ms": int(self.args.hold_ms),
                "timeout": float(self.args.timeout),
                "max_state_retries": int(self.args.max_state_retries),
                "action_instructions": instr}
        if self.backend == "jev":
            # Hard protocol fact: an image request is EXACTLY 1 image + 1 question.  The
            # agent's own guard refuses anything else, and a refusal is recorded, never
            # silently trimmed.
            opts["image_multi_question"] = "error"
            opts["state_overflow"] = "clip"
            opts["invariant_questions"] = 0
            opts["score_question"] = False
            opts["action_key"] = "move"
        ag = build_agent(self.backend, self.game, self.build_goal().get("objective"), opts)
        # Drop `done` from the option set this agent asks about.  `build_questions` calls
        # `action_criteria` internally (TASK-127 lifted it out for exactly this reuse), so
        # the subclass hook is overridden here instead of duplicating the question builder.
        ag.build_action_criteria = lambda goal: self.choice_criteria(goal)
        return ag

    def action_effect(self, name, keys, rs):
        """TASK-134 §1.B/V3: what THIS action will do, in the game's own vocabulary.

        The baseline criterion is only the action's name and its bound key -- nothing tells
        the model what pressing it does.  V3 replaces that with a sentence built from the
        readable state: where the ball is and where the paddle is, how far the snake's head
        is from the food, where the falling piece is.  Every sentence is derived from the
        same exported fields the state dump carries, and it is written verbatim into the
        request body that is saved on disk.
        """
        v = (rs or {}).get("values") or {}

        def f(spec, i=0, d=0.0):
            try:
                return float((v.get(spec) or [])[i])
            except (TypeError, ValueError, IndexError):
                return d

        bound = (" (bound key(s): %s)" % keys) if keys else ""
        if name in ("pong_left_up", "pong_left_down"):
            by = f("Ball.pos", 1) + f("Ball.pos", 3, 16) / 2.0
            py = f("PaddleLeft.pos", 1) + f("PaddleLeft.pos", 3, 100) / 2.0
            return ("move the LEFT paddle %s: this changes the left paddle's y position "
                    "(now %.0f) and, if the ball reaches it, the ball's bounce direction. "
                    "The ball's centre is at y=%.0f%s"
                    % ("up" if name.endswith("up") else "down", py, by, bound))
        if name in ("pong_right_up", "pong_right_down"):
            return ("move the RIGHT paddle %s; it changes the right paddle's y position%s"
                    % ("up" if name.endswith("up") else "down", bound))
        if name == "pong_serve":
            return ("serve the ball: this starts a new rally only if the ball is parked. "
                    "Right now Ball.Velocity=%s%s" % (v.get("Ball.Velocity"), bound))
        if name.startswith("snake_") and name != "snake_pause":
            return ("turn the snake %s and take one step that way: this changes HeadX/HeadY "
                    "and moves the whole body. head=(%s,%s) food=(%s,%s) dir=(%s,%s)%s"
                    % (name.split("_")[1], v.get("HeadX"), v.get("HeadY"),
                       v.get("Food.CellX"), v.get("Food.CellY"),
                       v.get("DirectionX"), v.get("DirectionY"), bound))
        if name == "snake_restart":
            return "restart the run after GameOver%s" % bound
        if name == "snake_pause":
            return "pause/unpause: this freezes the game clock%s" % bound
        if name == "tetris_left" or name == "tetris_right":
            return ("shift the falling piece one column %s: PieceX %s -> %s.  The piece only "
                    "becomes part of the stack when it is dropped%s"
                    % (name.split("_")[1], v.get("PieceX"),
                       ("%d" % (int(v["PieceX"]) - 1)) if isinstance(v.get("PieceX"), int)
                       else "?", bound))
        if name == "tetris_rotate":
            return ("rotate the falling piece: PieceRot %s -> %s.  A rotation that does not "
                    "fit is refused by the game%s"
                    % (v.get("PieceRot"), ((int(v["PieceRot"]) + 1) % 4)
                       if isinstance(v.get("PieceRot"), int) else "?", bound))
        if name == "tetris_drop":
            return ("hard-drop the piece: it lands, the board's filled cells change and a "
                    "new piece spawns%s" % bound)
        if name == "tetris_down":
            return "step the piece down one row%s" % bound
        if name.startswith("m2048_"):
            d = name.split("_")[1]
            grid = v.get("GridString")
            nxt = _2048_slide([int(x) for x in (grid or "0,0,0,0").split("/")[0].split(",")]) \
                if grid else None
            return ("slide every tile %s and merge equal neighbours: the board string "
                    "changes and the score rises.  Only a direction that really moves "
                    "something is accepted by the game.  Board now: %s%s"
                    % ({"left": "left", "right": "right", "up": "up", "down": "down"}[d],
                       grid, bound))
        if name in ("pb_left", "pb_right"):
            return ("move the shooter one column %s: ShooterCol %s -> %s; the aim dots move "
                    "with it%s" % (name.split("_")[1], v.get("ShooterCol"),
                                   ("%d" % (int(v["ShooterCol"]) + (1 if name.endswith(
                                       "right") else -1)))
                                   if isinstance(v.get("ShooterCol"), int) else "?", bound))
        if name == "pb_shoot":
            return ("fire the bubble along the aim: a projectile spawns and lands on the "
                    "board.  ShooterCol=%s ShooterColor=%s%s"
                    % (v.get("ShooterCol"), v.get("ShooterColor"), bound))
        # No bespoke sentence for this action: return None so the caller can try the game's
        # own capability declaration (TASK-136 §1.B) before falling back to name+key.
        return None

    def declared_capability_text(self, name, rs):
        """TASK-136 §1.B: the V3 sentence for a game that has no bespoke description.

        Built ENTIRELY from the game's own declaration
        (`tools/playability_controls.json -> games.<game>.capabilities[]`, whose fields are
        `action` / `need` / `observable`) plus the current value of that observable read out
        of the running game.  Nothing is invented: if the declaration names no capability for
        this action the caller falls back to the bare name-and-key sentence it always used.
        The point is that V3 ("what will pressing this do") must not degrade to a name list
        on the fifteen games TASK-136 added to the scripted arm.
        """
        try:
            decl = (self.controls or {}).get(self.controls_game) or {}
            for cap in (decl.get("capabilities") or []):
                if cap.get("action") != name:
                    continue
                spec = cap.get("observable") or ""
                key = spec.replace("|", ".") if "|" in spec else spec
                val = ((rs or {}).get("values") or {}).get(key, "not exported")
                return ("%s: it should move the declared observable `%s` (currently %r) -- "
                        "that is this game's own capability declaration, not the model's "
                        "guess" % (cap.get("need") or name, spec, val))
        except Exception:  # noqa: BLE001 - a description must never break a run
            return None
        return None

    def choice_criteria(self, goal):
        """The criteria dict the model is asked to choose from, WITHOUT `done`.

        `playtest_agent.action_criteria` appends `done` ("stop probing: no further action is
        likely to help").  For a probe that is right; for a player it is a trap -- measured
        in the first pong run, where Jev answered `done` with P=0.61 for nine steps straight.
        `wait` is kept (it is a real move: deal with a ball already in flight), `done` is
        dropped, and what was dropped is recorded in `session.json`.

        TASK-134 §1.B: V3/V4 replace the name-only description with `action_effect(...)`,
        and V4 additionally REMOVES the action that produced no change on the previous step
        (`self.excluded_action`).  V1 keeps the TASK-132/133 text byte-for-byte, so the
        baseline arm cannot be mistaken for a variant.
        """
        described = self.variant in ("V3", "V4")
        crit = {}
        for name, keys in (goal.get("actions") or {}).items():
            if self.variant == "V4" and name == self.excluded_action:
                continue          # §1.B/V4: exclude the action that produced no change
            ks = ",".join(str(k) for k in keys) if isinstance(keys, (list, tuple)) else \
                ("" if keys is None else str(keys))
            if described:
                crit[name] = (self.action_effect(name, ks, self.current_readable_state)
                              or self.declared_capability_text(
                                  name, self.current_readable_state)
                              or ("hold the game's InputMap action '%s' (bound key(s): %s)"
                                  % (name, ks or "?")))
            else:
                crit[name] = ("hold the game's InputMap action '%s' (bound key(s): %s)"
                              % (name, ks or "?"))
        crit["wait"] = ("do nothing this step (hold position / observe)" if not described
                        else "do nothing this step: no state and no pixel changes")
        return crit

    # -- prep: make the game live before the model is asked to play ---------
    def run_prep(self, prep_actions):
        """Inject the game's own declared action(s) once, to get it into a live state.

        Not a trick and not a game change: pong's own documented rule is "a new process
        parks the ball in the middle and waits for an explicit serve", and its
        `AutoServe` then keeps re-serving after every point -- so the preps are exactly what
        a human does when they sit down (press SPACE).  The channel is the same faithful
        `Input.parse_input_event` the gate uses, and every prep is recorded with its own
        before/after frame and state.
        """
        out = []
        for pa in prep_actions:
            s0 = self.sample_state("prep_%s_before" % pa)
            f0 = self.capture("prep_%s_before" % pa)
            w0 = self.frame_count(s0)
            res, inj = self.inject_action(pa)
            time.sleep(self.args.hold_ms / 1000.0)
            ack_state, ack_seq = self.ack_after_inject(pa)
            if isinstance(inj, dict):
                inj["sent"] = True
                inj["ack_seq"] = (inj.get("seq") or []) + [ack_seq]
                inj["is_action_pressed_while_down"] = (ack_state or {}).get(
                    "is_action_pressed")
                inj["ack_result"] = ack_state
                inj["release"] = self.release_action(pa)
            f1, s1, wev = self.window_after(w0, "prep_%s_after" % pa)
            delta, gp = gameplay_delta(s0.get("state"), s1.get("state"), self.gameplay_decl)
            px = png_changed(f0["path"], f1["path"]) if (f0 and f1) else {}
            rec = {"action": pa, "channel": (inj or {}).get("channel"),
                   "injection": inj,
                   "acked": bool((ack_state or {}).get("is_action_pressed")),
                   "state_before_sha": s0.get("sha256"), "state_after_sha": s1.get("sha256"),
                   "frame_before_sha": (f0 or {}).get("sha256"),
                   "frame_after_sha": (f1 or {}).get("sha256"),
                   "pixel_diff": px.get("changed_pixels"),
                   "gameplay_changes": [c.get("key") for c in gp],
                   "frame_budget": wev}
            out.append(rec)
            log("  prep %s: acked=%s px=%s gameplay=%s"
                % (pa, rec["acked"], rec["pixel_diff"], rec["gameplay_changes"]))
            time.sleep(self.args.step_gap)
        return out

    # -- one step -----------------------------------------------------------
    def build_readable_state(self, s_before):
        """TASK-134 §1.B/V2: the readable state for this step, from the game's own read."""
        return readable_state(self.game, s_before.get("state"), self.marker_decl,
                              last=self.last_step_result)

    def run_step(self, i, agent, goal):
        args = self.args
        s_before = self.sample_state("%02d_before" % i)
        f_before = self.capture("%02d_before" % i)
        if not f_before:
            return {"step": i, "error": "no frame could be captured", "abort": True}
        w0 = self.frame_count(s_before)

        # --- TASK-134 §1.B: what this step's request will carry -------------------
        # The readable state is built for EVERY arm (the scripted policy needs it to play),
        # but which variant may PUT it in the request is the variant's own decision: V1
        # sends none (byte-identical to TASK-132/133), V2 sends the whole thing, V3/V4 send
        # it (V4 only the previous-step sentence) and describe the candidates with it.
        rs = self.build_readable_state(s_before)
        self.current_readable_state = rs
        if self.player == "scripted":
            state_for_agent = rs
        elif self.variant == "V2":
            state_for_agent = rs
        elif self.variant == "V4":
            state_for_agent = {"variant": "V4",
                               "previous_step": rs.get("previous_step"),
                               "rule": ("the action named in `previous_step.action` produced "
                                        "NO change and has been removed from the candidate "
                                        "list; pick a different one")}
        else:
            state_for_agent = {}
        # V4's anti-repeat input: only an action that was really SENT and really produced
        # nothing is excluded (a `wait` step or a step the game refused is not blamed).
        if self.variant == "V4" and self.last_step_result and \
                self.last_step_result.get("result") == "no change" and \
                self.last_step_result.get("injected"):
            self.excluded_action = self.last_step_result.get("action")
        else:
            self.excluded_action = None

        # --- the model really sees the picture -----------------------------
        img = image_for_model(f_before, self.image_form, self.model_images_dir)
        frame_for_model = {k: f_before.get(k) for k in
                           ("index", "path", "width", "height", "sha256",
                            "content_fraction", "bbox", "background_rgb")}
        if img.get("path"):
            frame_for_model["path"] = img["path"]
        frame_for_model["window"] = self.osd.get("display_window_size")
        frame_for_model["declared"] = self.osd.get("declared_viewport")
        if self.player == "model":
            # V2/V4 on playjev: serve.py has no text-state channel (a text `state` is a
            # 400, serve.py:41-42), so the same readable-state text rides in the action
            # question's free-text `instructions`.  Recorded verbatim like everything else.
            base_instr = (args.action_instructions
                          or VARIANT_INSTRUCTIONS.get(self.variant,
                                                      VARIANT_INSTRUCTIONS["V1"]))
            if self.backend == "playjev" and self.variant in ("V2", "V4") and \
                    hasattr(agent, "options"):
                agent.options["action_instructions"] = (
                    base_instr + "\n" + readable_state_text(rs))
        t0 = time.time()
        action = agent.decide([frame_for_model], state_for_agent, goal)
        wall = round(time.time() - t0, 3)
        ev = agent.last_evidence or {}
        payload = ev.get("request_payload")
        meta = ev.get("request_meta") or {}
        transport = ev.get("transport") or {}
        # keep the model's exact input and output, verbatim
        sdir = os.path.join(self.outdir, "%02d" % i)
        if not os.path.isdir(sdir):
            os.makedirs(sdir)
        write_json(os.path.join(sdir, "request.json"), payload)
        write_json(os.path.join(sdir, "response.json"),
                   {"status": transport.get("status"), "body_raw": transport.get("body"),
                    "headers": transport.get("headers"), "attempts": transport.get("attempts")})
        write_json(os.path.join(sdir, "request_meta.json"), meta)
        write_json(os.path.join(sdir, "readable_state.json"), rs)

        choice, probs, conf = choice_of(agent, self.backend, action)

        if self.player == "model" and (
                not isinstance(payload, dict) or "image" not in payload and
                not ((payload or {}).get("state") or {}).get("frames")):
            self.errors.append({"at": "step %d" % i,
                                "error": "the request carried NO image: the model was not "
                                         "shown the picture (TASK-132 forbids the text-only "
                                         "fallback)"})

        # --- ack pre-read: is the action already down? ---------------------
        act_name = action.get("action")
        injectable = bool(act_name) and action.get("type") in ("action", "key")
        pre_ack = None
        if injectable:
            pre_ack, _n = self.ack_after_inject(act_name)

        # --- the no-input control window -----------------------------------
        # TASK-138 defect ⑧: this window verifies nothing by its NOMINAL budget -- one MCP
        # round trip moves the game's drawn-frame counter by 30..120 frames, which is how a
        # "30 vs 30" budget produced the recorded 117..138 action frames against 31..58
        # control frames.  `achieved_delta` is the game's OWN frame delta from this window's
        # start read to the drawn value of its after-state read, and the action window is
        # given exactly that span from the frame the injection finished on.  The two windows
        # therefore do the same operations for the same number of frames.
        cw_start = self.frames_drawn("ctl:start")
        if not isinstance(cw_start, int):
            cw_start = w0
        ctl = self.control_window(f_before, s_before, cw_start)
        ctl_span = ctl.get("achieved_delta")

        # --- inject --------------------------------------------------------
        real_key = None
        inj = {"channel": None, "sent": False,
               "why": ("the model produced no injectable action (%r, type=%r)" %
                       (act_name, action.get("type")))}
        if injectable and args.channel == "real":
            got, err = self.inject_real_key(act_name)
            if err:
                self.errors.append({"at": "step %d" % i, "error": err})
                inj = err
            else:
                inj = got
        elif injectable:
            injected, got = self.inject_action(act_name)
            time.sleep(args.hold_ms / 1000.0)
            ack_state, ack_seq = self.ack_after_inject(act_name)
            if isinstance(got, dict):
                got["ack_seq"] = (got.get("seq") or []) + [ack_seq]
                got["is_action_pressed_while_down"] = (ack_state or {}).get(
                    "is_action_pressed")
                got["ack_result"] = ack_state
                got["sent"] = True
            up = self.release_action(act_name)
            if isinstance(got, dict):
                got["release"] = up
            inj = got

        # --- observe: the SAME span the control window achieved ------------
        # A `drawn` read is the first thing the action window does, exactly like the control
        # window's own first read, and the wait ends `ctl_span` drawn frames after it.
        inj_end = self.frames_drawn("step:inj_end")
        if not isinstance(inj_end, int):
            inj_end = w0
        target_end = (self.frame_target_for(inj_end, ctl_span)
                      if isinstance(ctl_span, int) else None)
        try:
            f_after, s_after, win_ev = self.window_after(inj_end, "%02d_after" % i,
                                                         absolute_target=target_end)
        except Exception as exc:  # noqa: BLE001
            self.errors.append({"at": "step %d" % i,
                                "error": "no frame could be captured: %s" % exc})
            return {"step": i, "error": "no frame could be captured", "abort": True}
        action_end = self.frame_count(s_after)
        # TASK-138 defect ⑧: the action span is measured with the SAME endpoint the control
        # span uses -- the `drawn` the wait loop itself reported -- because the screenshot and
        # state dump that follow the wait cost another ~10 frames of live game on this side
        # and nothing on the control side.  (The pixel term and the movement sum are still read
        # over the full after-bracket for both windows.)
        action_span_end = win_ev.get("end_drawn") if isinstance(win_ev, dict) else None
        action_frames = ((action_span_end - inj_end)
                         if (isinstance(action_span_end, int) and isinstance(inj_end, int))
                         else ((action_end - inj_end)
                               if (isinstance(action_end, int) and isinstance(inj_end, int))
                               else None))
        control_px = ctl["pixel_diff"]
        control_gp = ctl["gameplay_changes"]
        alignment = self.align_windows(ctl, action_frames)
        self.frame_alignment.append(dict(alignment, step=i))
        win_ev = dict(win_ev or {})
        win_ev["step_frame_start"] = inj_end
        win_ev["step_frame_end"] = action_end
        win_ev["action_frames"] = action_frames
        win_ev["control_frames_matched"] = ctl_span
        win_ev["wait_achieved_delta"] = win_ev.get("achieved_delta")
        win_ev["after_state_drawn"] = action_end
        win_ev["after_state_drawn_note"] = ("the drawn value of the after-state sample; the "
                                            "SPAN deliberately uses the wait's own end so "
                                            "both windows are measured at the same point")
        win_ev["achieved_delta"] = action_frames
        win_ev["achieved_delta_what"] = ("the DRAWN frames the action window really spanned, "
                                         "from its own first `drawn` read to the drawn value "
                                         "of its after-state read -- the same definition the "
                                         "control window's `achieved_delta` uses")
        win_ev["wait_achieved_delta_what"] = ("the DRAWN frames this wait loop itself saw; "
                                              "TASK-138 defect ⑧ reports it beside the span "
                                              "rather than treating it as the span")

        delta, gp = gameplay_delta(s_before.get("state"), s_after.get("state"),
                                   self.gameplay_decl)
        gp_keys = [c.get("key") for c in gp]
        px = png_changed(f_before["path"], f_after["path"]) if f_after else {
            "comparable": False, "changed_pixels": None}
        refuse = refusal_hit(delta, self.refusal_decl)
        # TASK-139 §1.B: the same game-side evidence, read on the ONE loop that produces the
        # verdict, so `summarise` never has to re-derive which steps were legal refusals
        # (and can never disagree with the run that recorded them).
        step_refusal = step_refusal_record(
            {"state_delta": delta}, self.refusal_decl)
        if step_refusal is not None:
            step_refusal["refused_legal"] = True
            step_refusal["note"] = ("the game's own exported refusal counter moved on this "
                                    "step: it saw the input and deliberately said no")
        mv, mv_detail = movement_magnitude(gp)
        real_info = None
        ack_state_for_verdict = None
        # TASK-138 defect ⑨: NO FALLBACK TO `pre_ack`.  `pre_ack` is the InputMap read taken
        # BEFORE the injection (the old `:2326` wrote `inj.get("ack_result") or pre_ack`), so
        # a residual key-down from the previous step could be credited as this step's ack.
        # If the injection tool answered without an `ack_result`, the step is now reported as
        # INCONCLUSIVE: the loop has no game-side evidence that THIS input was seen, and it
        # is not allowed to invent one out of a stale read.
        ack_missing = None
        if injectable and isinstance(inj, dict):
            if inj.get("channel") == "OS_SendInput":
                # the real-key ack is the game's own InputMap read taken WHILE the OS key was
                # down (`inj["ack_after_keydown"]`), not the synthetic arm's field
                real_ack = inj.get("ack_after_keydown")
                real_info = {"vk": inj.get("vk"),
                             "focus_ok": (inj.get("focus") or {}).get("ok"),
                             "keydown_returned": (inj.get("keydown") or {}).get("returned"),
                             "keyup_returned": (inj.get("keyup") or {}).get("returned"),
                             "is_action_pressed": inj.get("is_action_pressed_while_down"),
                             "ack_after_keydown": real_ack,
                             "window": inj.get("focus_evidence")}
                ack_state_for_verdict = real_ack or {
                    "is_action_pressed": inj.get("is_action_pressed_while_down")}
            else:
                ack_state_for_verdict = inj.get("ack_result")
                if not isinstance(ack_state_for_verdict, dict):
                    ack_missing = {
                        "step": i,
                        "action": act_name,
                        "why": ("the injection answered without `ack_result`, so there is no "
                                "game-side read of the InputMap state taken after THIS "
                                "injection; the pre-injection read `pre_ack` is NOT used "
                                "(TASK-138 defect ⑨)"),
                        "pre_ack_used_as_evidence": False,
                        "pre_ack_recorded_only": pre_ack,
                        "ack_result_present": False,
                        "injection_channel": inj.get("channel"),
                        "injection_keys": sorted(k for k in inj.keys()),
                    }
                    self.ack_missing.append(ack_missing)
                    self.errors.append({"at": "step %d" % i,
                                        "error": "ack missing: step recorded as "
                                                 "INCONCLUSIVE (no pre_ack fallback)"})
        ack = ack_verdict(act_name, None, None, gp_keys, refusal=refuse,
                          real_key=real_info, action_state=ack_state_for_verdict)
        change = decide_changed(px.get("changed_pixels"), control_px, mv, ctl["movement"])
        change["gameplay_detail"] = mv_detail
        change["gameplay_changes"] = gp_keys
        change["control_gameplay_changes"] = ctl["gameplay_changes"]
        if ack_missing is not None:
            # forced unconditionally: an ack the game never reported cannot produce "the
            # game accepted this input and nothing changed" (FAIL) NOR "accepted and
            # changed" (PASS).  It is the third state, and it is written as such.
            ack["injected"] = False
            ack["accepted"] = False
            ack["evidence_used"] = "ack_missing"
            ack["evidence_all"] = ["ack_missing"]
            ack["ack_missing"] = ack_missing
            ack["note"] = (ack_missing["why"] + "; the step is INCONCLUSIVE, not FAIL and "
                           "not PASS")
            sv = STEP_VERDICT_ACK_MISSING
        else:
            sv = step_verdict(ack, change)

        rec = {
            "step": i,
            "ts_ms": (s_after.get("state") or {}).get("ms"),
            "frame_before_sha": f_before.get("sha256"),
            "frame_after_sha": (f_after or {}).get("sha256"),
            "frame_before_file": os.path.basename(f_before.get("path") or ""),
            "frame_after_file": os.path.basename((f_after or {}).get("path") or ""),
            "pixel_diff": px.get("changed_pixels"),
            "pixel_diff_detail": px,
            "frame_count": (s_after.get("state") or {}).get("drawn"),
            "frame_budget": win_ev,
            "frame_alignment": alignment,
            "control_diff": dict(ctl, state_delta=len(ctl["delta"]),
                                 role=("the verdict's control term: a zero-input window with "
                                       "the same structure and the same achieved drawn-frame "
                                       "span as the action window")),
            "state_before_sha": s_before.get("sha256"),
            "state_after_sha": s_after.get("sha256"),
            "state_delta_count": len(delta),
            "state_delta": delta[:40],
            "gameplay_changes": gp_keys,
            "gameplay_change_labels": gameplay_change_labels(delta, self.gameplay_decl),
            "gameplay_movement": mv,
            "markers": marker_values(s_after.get("state"), self.marker_decl),
            "action": {"action": action.get("action"), "type": action.get("type"),
                       "pressed": action.get("pressed"), "hold_ms": action.get("hold_ms"),
                       "why": action.get("why"), "raw": action},
            "probs": probs, "confidence": conf, "choice": choice,
            "channel": (inj or {}).get("channel") if isinstance(inj, dict) else None,
            "injection": inj,
            "ack": ack, "ack_evidence": ack.get("evidence_used"),
            "ack_missing": ack_missing,
            "step_refusal": step_refusal,
            "step_refusal_reading": (
                "a LEGAL REFUSAL recorded by the game's own counters; such a step is not "
                "charged to the game as 'accepted and nothing changed' and is dropped from "
                "the rate's denominator, but it is never counted as progress "
                "(-- TASK-139 §1.B)" if step_refusal else
                "no refusal counter of this game moved on this step"),
            "ack_pre_read": {"read_before_injection": pre_ack,
                             "used_as_evidence": False,
                             "why": ("TASK-138 defect ⑨: recorded for diagnosis only; the "
                                     "verdict never falls back to it")},
            "change": change, "changed_bool": change.get("changed"),
            "step_verdict": sv,
            # TASK-134: which ARM and which VARIANT produced this step, what image the
            # model was actually shown, and whether the readable state was in the request.
            "arm": {"player": self.player, "variant": self.variant,
                    "image_form": self.image_form,
                    "image_sent": img,
                    "readable_state_in_request": bool(state_for_agent),
                    "readable_state_keys": sorted((state_for_agent or {}).keys()),
                    "readable_state_path": os.path.join(sdir, "readable_state.json"),
                    "excluded_action_this_step": self.excluded_action,
                    "instruction_text_sent": ((agent.options or {}).get(
                        "action_instructions") if hasattr(agent, "options") else None)},
            "readable_state": rs,
            "state_after_full": s_after.get("state"),
            "model": {"backend": self.backend, "seconds": wall,
                      "http_status": transport.get("status"),
                      "answer_model": ev.get("model"),
                      "usage": ev.get("usage"), "input_tokens": ev.get("input_tokens"),
                      "image_tokens": ev.get("image_tokens"),
                      # TASK-132 §0.1: an image request is 1 image + 1 question; the flag
                      # below is the agent's own reading of what it built.
                      "with_image": bool(meta.get("with_image")),
                      "question_count": meta.get("question_count"),
                      "question_keys": meta.get("question_keys"),
                      "image_field": ("image (top-level data URL)" if self.backend == "jev"
                                      else "state.frames[0] (data URL)"),
                      "image_bytes_decoded": meta.get("image_decoded_bytes"),
                      "request_meta": meta,
                      "request_path": os.path.join(sdir, "request.json"),
                      "response_path": os.path.join(sdir, "response.json"),
                      "errors": list(getattr(agent, "errors", []) or [])[-3:]},
        }
        self.steps.append(rec)
        rec.pop("state_after_full", None)
        rec["_state_after_full"] = s_after.get("state")
        # TASK-134 §1.B/V4: hand the NEXT step what this one did.  `result` is the SAME
        # `change.changed` reading the FAIL condition uses -- there is no second opinion.
        self.last_step_result = {
            "step": i, "action": act_name, "injected": bool(ack.get("injected")),
            "accepted": bool(ack.get("accepted")),
            "result": "changed" if change.get("changed") else "no change",
            "pixel_diff": px.get("changed_pixels"),
            "control_pixels": control_px,
            "gameplay_changes": gp_keys,
            "note": ("the previous action %r produced NO change in either the picture or "
                     "the declared gameplay observables" % act_name
                     if (ack.get("injected") and not change.get("changed"))
                     else "the previous action %r produced a change" % act_name),
        }
        log("  step %02d action=%-18s conf=%-7s http=%s | ack=%s(%s) px=%s vs ctl=%s "
            "mv=%s/%s | %s"
            % (i, rec["action"]["action"], conf, rec["model"]["http_status"],
               ack["accepted"], ack["evidence_used"], px.get("changed_pixels"), control_px,
               mv, ctl["movement"], sv))
        return rec

    # -- the two measurement windows, on one game-frame budget --------------
    @staticmethod
    def frame_count(state):
        s = (state or {}).get("state")
        return (s or {}).get("drawn") if isinstance(s, dict) else None

    def frame_target_for(self, w0, target=None):
        """The ABSOLUTE `Engine.get_frames_drawn()` the next wait must reach.

        TASK-138 defect ⑧: the two windows used to be driven by their own RELATIVE
        `target_delta`, and the drawn-frame counter does not advance one frame per poll --
        every MCP tool call advances the game by however many frames it took to answer
        (measured: single polls that moved `drawn` by 31, 113 or 117 frames).  A relative
        budget therefore overshoots by an amount nobody controls, which is exactly how a
        nominal "30 vs 30" turned into an achieved 117 vs 34.  Every wait in this loop now
        targets an ABSOLUTE frame index, and both windows are handed the SAME delta from
        their own start.
        """
        t = int(target if target is not None else self.args.window_frames)
        return (w0 + t) if isinstance(w0, int) else None

    def frames_drawn(self, at):
        """One cheap read of the game's own drawn-frame counter (no screenshot, no digest)."""
        st, _r = self.gd('return {"drawn": Engine.get_frames_drawn()}', at)
        return (st or {}).get("drawn") if isinstance(st, dict) else None

    def wait_frames(self, w0, target=None, absolute_target=None):
        """Wait until the game has DRAWN `target` more frames than `w0` (from the game).

        TASK-138 defect ⑧: `absolute_target` (a `drawn` value) is the form every window in
        `run_step` uses now -- `drawn` is not advanced by this loop's own polling, so a
        relative target lets each poll's answering cost be added to the window.
        """
        target = int(target if target is not None else self.args.window_frames)
        goal = (int(absolute_target) if absolute_target is not None
                else self.frame_target_for(w0, target))
        ev = {"start_drawn": w0, "target_delta": target, "polls": 0,
              "absolute_target": goal,
              "wait_kind": ("absolute" if absolute_target is not None else "relative"),
              "poll_gap_s": self.args.window_poll_gap}
        t0 = time.time()
        last = None
        while time.time() - t0 < self.args.window_timeout:
            st, _r = self.gd(probe_state_source(), "wait:frames")
            ev["polls"] += 1
            last = (st or {}).get("drawn") if isinstance(st, dict) else None
            if goal is not None and isinstance(last, int) and last >= goal:
                break
            time.sleep(self.args.window_poll_gap)
        ev["end_drawn"] = last
        ev["achieved_delta"] = ((last - w0) if isinstance(last, int) and w0 is not None
                                else None)
        ev["seconds"] = round(time.time() - t0, 3)
        ev["timed_out"] = bool(ev["achieved_delta"] is None or
                               (goal is not None and not (isinstance(last, int) and
                                                          last >= goal)) or
                               ev["achieved_delta"] < target)
        return ev

    def control_window(self, f_before, s_before, w0, target=None):
        """The NO-input control window, measured on the game's own drawn-frame counter.

        TASK-138 defect ⑧.  What this window IS, precisely:

        * its START is its own first `Engine.get_frames_drawn()` read (`w0`), taken after the
          model answered and immediately before the window;
        * its END is the same probe's `drawn` at the moment the wait loop stopped
          (`frame_budget.end_drawn`) -- deliberately NOT the drawn value of the after-state
          sample, because taking a screenshot + a state dump costs another ~10 frames of live
          game, and the ACTION window pays that cost on the far side of its own wait.  Using
          the wait's own end makes the two spans the same quantity;
        * its SPAN is `end_drawn - w0`, and the action window is handed exactly that span as
          an ABSOLUTE target, so the two windows cover the same number of the game's frames;
        * the picture and the declared observables are read over the same bracket (before
          capture -> after capture / after state), so the pixel term and the movement sum come
          from it too.
        """
        wev = self.wait_frames(w0, target)
        c_end = self.capture("ctl_end")
        c_state = self.sample_state("ctl_end")
        w_end = wev.get("end_drawn")
        span = ((w_end - w0) if (isinstance(w_end, int) and isinstance(w0, int)) else None)
        px = png_changed(f_before["path"], c_end["path"]) if c_end else {
            "changed_pixels": None}
        delta, gp = gameplay_delta(s_before.get("state"), c_state.get("state"),
                                   self.gameplay_decl)
        mv, _detail = movement_magnitude(gp)
        wev["span_from_start_drawn"] = span
        wev["span_end_drawn"] = w_end
        wev["span_what"] = ("the game's own drawn-frame delta from this window's start read "
                            "to the `drawn` it reported when its wait stopped; TASK-138 "
                            "defect ⑧ hands this exact number to the action window, which is "
                            "why it is the wait's end and not the after-state sample's drawn")
        return {
            "pixel_diff": max(0, px.get("changed_pixels") or 0),
            "gameplay_changes": [c.get("key") for c in gp],
            "movement": mv,
            "delta": delta,
            "frame_budget": wev,
            "frame_end_file": os.path.basename((c_end or {}).get("path") or ""),
            "start_drawn": w0,
            "end_drawn": w_end,
            "achieved_delta": span,
            "role": ("zero-input control window; its span (`achieved_delta`) is the exact "
                     "number of drawn frames the action window is then given (TASK-138 "
                     "defect ⑧)"),
            "rule": ("zero input over the declared frame budget, starting at its own "
                     "`start_drawn`; `achieved_delta` is the game's own drawn-frame delta "
                     "from that start to the wait's own end"),
        }

    def control_span(self, f_span_before, s_span_before, w_span_start, s_after, label):
        """Deprecated by TASK-138's final alignment design; kept out of the run path.

        The first draft of defect ⑧'s fix bracketed the control over the action window's whole
        range (injection included).  That measures the world's own motion over a window four
        times longer than the action's INPUT, so the reading stops separating "the input did
        something" from "the game animates by itself" -- pong's scripted arm measured an
        identical `gameplay_movement` (627.007) with and without the input.  The shipped
        design gives BOTH windows the same structure (a `drawn` read, a wait, a screenshot, a
        state read) and hands the action window the control window's achieved span, so the
        equality comes from the two windows having the same shape.  This helper is kept
        because `selftest` covers it and because a future reader may want the wide bracket as
        a second, explicitly-named diagnostic.
        """
        f_span_end = self.capture("ctl_span_end")
        w_span_end = self.frame_count(s_after) if s_after else None
        delta, gp = gameplay_delta(s_span_before.get("state"), s_after.get("state"),
                                   self.gameplay_decl)
        mv, _detail = movement_magnitude(gp)
        px = (png_changed(f_span_before["path"], f_span_end["path"])
              if (f_span_before and f_span_end) else {"changed_pixels": None})
        span = (w_span_end - w_span_start) if (isinstance(w_span_end, int) and
                                               isinstance(w_span_start, int)) else None
        return {
            "pixel_diff": max(0, px.get("changed_pixels") or 0),
            "gameplay_changes": [c.get("key") for c in gp],
            "movement": mv,
            "delta": delta,
            "start_drawn": w_span_start,
            "end_drawn": w_span_end,
            "achieved_delta": span,
            "frame_budget": {"start_drawn": w_span_start, "end_drawn": w_span_end,
                             "target_delta": None, "achieved_delta": span,
                             "wait_kind": "not_a_wait",
                             "why": "the span is bracketed by the step's own before/after "
                                    "reads, not by a wait loop"},
            "frame_span_before_file": os.path.basename((f_span_before or {}).get("path") or ""),
            "frame_span_end_file": os.path.basename((f_span_end or {}).get("path") or ""),
            "label": label,
            "role": "diagnostic (wide bracket), NOT the verdict's control term",
            "rule": ("zero input over the step's whole range, injection included -- kept as "
                     "a named diagnostic only (see the docstring for why it is not the "
                     "verdict's control term)"),
        }

    def window_after(self, w0, label, absolute_target=None):
        wev = self.wait_frames(w0, absolute_target=absolute_target)
        f = self.capture(label)
        s = self.sample_state(label)
        return f, s, wev

    @staticmethod
    def align_windows(ctl, action_frames):
        """TASK-138 defect ⑧: say, as numbers, whether the two windows really matched.

        `ctl` is the step's verdict-side control reading (`control_span`) and
        `action_frames` is the DRAWN-frame count the action window really spanned.  Both are
        `Engine.get_frames_drawn()` deltas over the same frame range, so `matched` is a
        checkable equality rather than a claim; `delta` is their difference and is what a
        reader should expect to be 0.
        """
        c = (ctl.get("frame_budget") or {}).get("achieved_delta")
        a = action_frames
        ok = (isinstance(c, int) and isinstance(a, int) and c == a)
        return {
            "control_frames": c,
            "action_frames": a,
            "delta": (a - c) if (isinstance(c, int) and isinstance(a, int)) else None,
            "matched": bool(ok),
            "control_start_drawn": ctl.get("start_drawn"),
            "control_end_drawn": ctl.get("end_drawn"),
            "what": ("TASK-138 defect ⑧: the counterfactual control reading and the action "
                     "reading span the same range of the game's OWN drawn frames "
                     "(`Engine.get_frames_drawn()`), from the frame the step's input went in "
                     "to the frame the step's after-state was read"),
        }

    # -- the run ------------------------------------------------------------
    def run(self):
        args = self.args
        if args.mode == "exe":
            pg.EXE_ROOT = args.exe_root
        else:
            pg.EXE_ROOT = None
        if args.project_dir:
            pg.GAME_DIRS[self.game] = os.path.abspath(args.project_dir)
        leftover = kill_what_holds(args.port)
        if leftover["still_holding"]:
            raise RuntimeError("port %d still held by %s"
                               % (args.port, [k["pid"] for k in leftover["still_holding"]]))
        self.proj = parse_project(self.game)
        self.controls = pg.load_controls()
        # A negative variant is a COPY of a real game (`projects/_exercises/neg_frozen` is a
        # copy of breakout), and the declaration lives under the SOURCE game's name.  The
        # loop may therefore be told which declaration to judge the variant by; it is
        # recorded verbatim in `session.json` so a variant can never silently borrow the
        # wrong declaration.
        self.controls_game = args.controls_game or self.game
        g = self.controls.get(self.controls_game) or {}
        self.gameplay_decl = gameplay_declaration(self.controls, self.controls_game)
        self.marker_decl = marker_declaration(self.controls, self.controls_game)
        self.liveness_decl = liveness_declaration(self.controls, self.controls_game)
        self.refusal_decl = refusal_declaration(self.controls, self.controls_game)
        goal = self.build_goal()
        if not goal["actions"]:
            raise SystemExit("REFUSED: game %r declares no InputMap action, so there is no "
                             "action set to ask the model about" % self.game)

        self.gp = GameProcess(self.game, args.port, self.outdir)
        ok, secs = self.gp.start(args.ready_timeout)
        if not ok:
            raise RuntimeError("the game's MCP endpoint never came up on port %d" % args.port)
        self.mcp = Mcp(args.port, self.calls_dir)
        tools = self.mcp.tools_list()
        time.sleep(args.settle)

        w, _ = self.gd(pg.PROBE_WINDOW, "window")
        self.osd = {"display_window_size": (w or {}).get("display_window_size"),
                    "root_viewport_size": (w or {}).get("root_viewport_size"),
                    "declared_viewport": (w or {}).get("declared_viewport"),
                    "current_scene": (w or {}).get("current_scene")}
        self.win = self.find_game_window()
        s0 = self.sample_state("00_settle")
        f0 = self.capture("settle")
        settle_liveness = terminal_conditions_met(s0.get("state"), self.liveness_decl)

        agent = self.make_agent()
        health = agent.check_health()
        session = {
            "task": "TASK-132", "task_context": "TASK-134 (arm/variant split)",
            "game": self.game, "backend": self.backend,
            # TASK-134 §1.A/§1.B: which arm, which declarative variant, which image form.
            "player": self.player, "variant": self.variant, "image_form": self.image_form,
            "variant_note": VARIANT_NOTES.get(self.variant),
            "arm_note": ("scripted deterministic human-like policy: answers 'can the GAME be "
                         "played' and contacts no model service"
                         if self.player == "scripted" else
                         "model player: answers 'can the MODEL play it'"),
            "scripted_policy": (getattr(agent, "policy", None).__name__
                                if self.player == "scripted" and
                                getattr(agent, "policy", None) else None),
            "scripted_alternate_turns": bool(getattr(args, "scripted_alternate", False)),
            "readable_state_fields": READABLE_STATE_FIELDS.get(self.game),
            "mode": args.mode, "exe_root": args.exe_root if args.mode == "exe" else None,
            "project_dir": pg.project_dir(self.game),
            "game_pid": self.gp.proc.pid if self.gp.proc else None,
            "process_tree": process_tree(self.gp.proc.pid) if self.gp.proc else [],
            "mcp_port": args.port, "mcp_endpoint": self.mcp.url,
            "mcp_tools_count": len(tools),
            "engine": pg.ENGINE, "engine_version": engine_version(),
            "game_stdout": os.path.abspath(self.gp.stdout),
            "game_cmdline": self.gp.cmdline,
            "chosen_window": self.win,
            "osd_window": self.osd,
            "settle_state_sha256": s0.get("sha256"),
            "settle_frame": {"file": os.path.basename(f0.get("path") or ""),
                             "sha256": f0.get("sha256"), "index": f0.get("index")},
            "settle_liveness_terminal": settle_liveness,
            "action_set_source": ("tools/playability_controls.json is the capability table, "
                                  "but the Choice criteria come from the game's OWN "
                                  "project.godot InputMap via playability_gate.parse_project"),
            "actions_offered": goal["actions"],
            "readme_keys": goal["keys"],
            "objective": goal["objective"],
            "controls_game": self.controls_game,
            "gameplay_observables": self.gameplay_decl.get("items"),
            "liveness": self.liveness_decl,
            "refusal_evidence": self.refusal_decl,
            # TASK-139 §1.B: the boundary that the refusal carve-out may not cross.
            "refusal_boundary": REFUSAL_BOUNDARY,
            "state_markers": self.marker_decl,
            "declarations_source": os.path.join(HERE, "playability_controls.json"),
            "channel": args.channel,
            "measurement_window": {
                "unit": "drawn game frames (Engine.get_frames_drawn(), read by "
                        "playability_gate.probe_state_source)",
                "frames": args.window_frames,
                "min_frames": WINDOW_MIN_FRAMES,
                "min_frames_declaration": WINDOW_DECLARATION,
                # TASK-140 §1.A.1/§1.A.3: the level a verdict may be REPORTED AS A PASS at,
                # and the round this run is (an independent complete run of this game).
                "reporting_frames": WINDOW_REPORTING_FRAMES,
                "round": getattr(args, "round", None),
                "reporting_state": STEP_VERDICT_BELOW_REPORTING,
                "too_short_state": STEP_VERDICT_WINDOW_TOO_SHORT,
                "wall_clock_cap_s": args.window_timeout,
                "poll_gap_s": args.window_poll_gap,
                "control": "a zero-input window with ZERO input, run immediately before the "
                           "injection, whose ACHIEVED drawn-frame span (start read -> the "
                           "drawn value of its after-state read) is the span the action "
                           "window is then given",
                "control_start": "a `drawn` read taken immediately before the control window "
                                 "(after the model answered)",
                "action_start": "a `drawn` read taken immediately after the injection's key "
                                "was released -- the action window's own first read, the "
                                "same way the control window starts",
                "action_end": "an ABSOLUTE `drawn` target (action start + the control "
                              "window's achieved span) -- TASK-138 defect ⑧",
                "alignment": "`frame_budget.achieved_delta` and "
                             "`control_diff.frame_budget.achieved_delta` are both the game's "
                             "own `Engine.get_frames_drawn()` deltas for their window, and "
                             "`player.json -> frame_alignment.matched` is their equality",
                "span_vs_wait": "`achieved_delta` is the window's SPAN (its first read to the "
                                "drawn value of its after-state read); "
                                "`wait_achieved_delta` is the wait loop's own reading and is "
                                "reported beside it, never instead of it",
                "why": "the two windows must be the same length in GAME frames: an "
                       "equal-wall-clock window can contain a different number of frames "
                       "around an MCP round trip, and the first pong run measured exactly "
                       "that artefact (the action window and the control window both "
                       "reported 1100 changed pixels).  TASK-138 defect ⑧ measured that a "
                       "RELATIVE per-window budget does not deliver that either -- one MCP "
                       "round trip moves `drawn` by 30..120 frames -- so the action window "
                       "is now matched to the count the control window actually achieved",
            },
            "hold_ms": args.hold_ms,
            # TASK-135 §1.B: which declared change margin the verdict will use, and the
            # declaration both readings come from (recorded in the run itself, so a reader
            # never has to guess which number a verdict was computed with).
            "change_margin": {
                "selected": getattr(args, "change_margin", CHANGE_MARGIN_DEFAULT),
                "known": list(CHANGE_MARGINS),
                "declaration_source": CHANGE_MARGIN_DECLARATION.get("source"),
                "baseline": CHANGE_MARGIN_DECLARATION.get("baseline"),
                "strict": CHANGE_MARGIN_DECLARATION.get("strict"),
                "what": "both readings are computed for every step; `selected` only decides "
                        "which one `player.json -> verdict` is; the other is filed as "
                        "strict_*/baseline_* beside it",
            },
            "model_service": {"base_url": getattr(agent, "base_url", None),
                              "health": health.get("json") if isinstance(health, dict) else None,
                              "health_url": getattr(agent, "health_path", None),
                              "decision_path": getattr(agent, "decision_path", None)},
        }
        write_json(os.path.join(self.outdir, "session.json"), session)

        preps = []
        try:
            if args.prep_actions:
                preps = self.run_prep(args.prep_actions)
                write_json(os.path.join(self.outdir, "prep.json"),
                           {"actions": args.prep_actions, "records": preps,
                            "channel": "Input.parse_input_event (the gate's faithful "
                                       "channel), the same one the model's actions use"})
            # TASK-132: if the game is ALREADY in its declared terminal state at settle, the
            # model must not be run at all.  In the first snake run it was (GameOver=true
            # 1.52 s after launch), the model answered `snake_down`, the InputMap read said
            # the action was down, and the frozen picture then looked like "the game
            # accepted an input and did nothing" -- which is the user's FAIL condition
            # reached on a game that was over before the model saw it.  Recording it that
            # way would blame the game for a criterion it was never given a chance to meet.
            live = self.sample_state("00_live_check")
            self.terminal_at_settle = terminal_conditions_met(live.get("state"),
                                                              self.liveness_decl)
            if self.terminal_at_settle and not args.ignore_terminal:
                log("  ABORT BEFORE ANY MODEL CALL: the game is already in its declared "
                    "terminal state %s" % self.terminal_at_settle)
            else:
                for i in range(1, args.steps + 1):
                    r = self.run_step(i, agent, goal)
                    if r.get("abort"):
                        break
                    # TASK-132: stop the moment the game declares itself over.  The frames
                    # after that are frozen BY RULE, so continuing would only manufacture
                    # more "accepted action, unchanged picture" instances out of a dead game
                    # -- exactly the trap TASK-131 found in snake (GameOver 1.52 s BEFORE the
                    # first frame).  The terminal read is the game's own declared field.
                    term = terminal_conditions_met(r.get("_state_after_full"),
                                                   self.liveness_decl)
                    if term:
                        self.terminal_stop = {
                            "step": i, "terminal": term,
                            "reason": "the game declared a terminal state; every later frame "
                                      "is frozen by rule, so the loop stops and reports it "
                                      "instead of manufacturing static steps",
                            "declaration": self.liveness_decl}
                        log("  STOP at step %02d: game declared terminal %s" % (i, term))
                        break
                    if r.get("step_verdict") == "ok_ack_and_changed" and args.patience and \
                            i >= PASS_MIN_STEPS:
                        tail = self.steps[-(PASS_MIN_STEPS):]
                        _m = getattr(args, "change_margin", CHANGE_MARGIN_DEFAULT)
                        if all(changed_of(t, _m) for t in tail) and \
                                len(set((t.get("action") or {}).get("action")
                                        for t in tail)) > 1:
                            log("  early stop: %d consecutive accepted+changed steps with "
                                "distinct actions" % len(tail))
                            break
                    time.sleep(args.step_gap)
        finally:
            stop = self.gp.stop()

        if self.terminal_at_settle:
            self.terminal_stop = self.terminal_stop or {
                "step": 0, "terminal": self.terminal_at_settle,
                "when": "at the settle frame, BEFORE the first model call",
                "reason": "the game was already over when the model was first shown it, so "
                          "no model-player verdict about the game can be formed from this "
                          "run; the run is recorded as INCONCLUSIVE with this as the reason",
                "declaration": self.liveness_decl}

        summary = summarise(self.steps, self.backend, self.game,
                            state={"terminal_stop": self.terminal_stop},
                            player=self.player,
                            margin=getattr(args, "change_margin", CHANGE_MARGIN_DEFAULT),
                            nominal_frames=getattr(args, "window_frames", None),
                            round_index=getattr(args, "round", None))
        summary["player"] = self.player
        summary["variant"] = self.variant
        summary["variant_note"] = VARIANT_NOTES.get(self.variant)
        summary["image_form"] = self.image_form
        summary["change_margin_selected"] = getattr(args, "change_margin",
                                                    CHANGE_MARGIN_DEFAULT)
        summary["readable_state_fields"] = READABLE_STATE_FIELDS.get(self.game)
        summary["scripted_policy"] = (getattr(agent, "policy", None).__name__
                                      if self.player == "scripted" and
                                      getattr(agent, "policy", None) else None)
        summary["scripted_alternate_turns"] = bool(getattr(args, "scripted_alternate", False))
        summary["prep_actions"] = list(args.prep_actions or [])
        summary["prep"] = preps
        summary["terminal_stop"] = self.terminal_stop
        summary["terminal_at_settle_before_the_first_model_call"] = self.terminal_at_settle
        summary["settle_liveness_terminal"] = settle_liveness
        summary["stop"] = stop
        summary["errors"] = self.errors
        summary["agent_errors"] = list(getattr(agent, "errors", []) or [])
        summary["agent_report"] = agent.report() if hasattr(agent, "report") else None
        summary["channel"] = args.channel
        write_json(os.path.join(self.outdir, "player.json"), summary)
        # the per-step records must stay serialisable and small: the full state snapshot of
        # every step is already in states/, so the private key is dropped before writing
        for r in self.steps:
            r.pop("_state_after_full", None)
        write_jsonl(os.path.join(self.outdir, "steps.jsonl"), self.steps)
        write_json(os.path.join(self.outdir, "frames.json"), self.frames)
        try:
            oc = ("OS window %s  root viewport %s  declared %s"
                  % (self.osd.get("display_window_size"), self.osd.get("root_viewport_size"),
                     self.osd.get("declared_viewport")))
            build_filmstrip(self.frames, os.path.join(self.outdir, "filmstrip.png"),
                            "%s -- %s model-player frames (full window, game endpoint)"
                            % (self.game, self.backend), note=oc)
        except Exception as e:  # noqa: BLE001
            self.errors.append({"at": "filmstrip", "error": "%s: %s" % (type(e).__name__, e)})
        try:
            build_demo(self.steps, self.frames_dir, self.game, self.backend,
                       os.path.join(self.outdir, "demo.png"),
                       verdict="%s -- %s" % (summary["verdict"], summary["why"]),
                       proj=self.proj)
        except Exception as e:  # noqa: BLE001
            self.errors.append({"at": "demo", "error": "%s: %s" % (type(e).__name__, e)})
        log("VERDICT %s/%s: %s -- %s" % (self.game, self.backend,
                                         summary.get("qualified_verdict"),
                                         summary["why"]))
        log("  verdict_context: %s" % json.dumps(summary.get("verdict_context"),
                                                ensure_ascii=False))
        return summary

    def find_game_window(self):
        pids = set()
        if self.gp and self.gp.proc:
            pids = set(p["pid"] for p in process_tree(self.gp.proc.pid))
        wins = [w for w in enumerate_windows() if w["pid"] in pids]
        wins.sort(key=lambda w: -(w["rect"][2] * w["rect"][3]))
        return wins[0] if wins else None


def engine_version():
    import subprocess
    try:
        r = subprocess.run([pg.ENGINE, "--version"], cwd=pg.ENGINE_CWD,
                           stdout=subprocess.PIPE, stderr=subprocess.STDOUT, timeout=60)
        return r.stdout.decode("utf-8", "replace").strip()
    except Exception as e:  # noqa: BLE001
        return "ERROR %s: %s" % (type(e).__name__, e)


def choice_of(agent, backend, action):
    """(choice, probabilities, confidence) as the SERVICE returned them (verbatim)."""
    ev = agent.last_evidence or {}
    if backend == "jev":
        a = ev.get("choice") or {}
        return (a.get("choice"), a.get("probabilities"), a.get("confidence"))
    ans = (ev.get("answers_raw") or {})
    key = getattr(agent, "action_key", "move")
    a = ans.get(key) or {}
    if not a:
        # playjev keeps its classified answers separately
        rec = (getattr(agent, "last_answers", {}) or {}).get(key) or {}
        return (rec.get("choice"), rec.get("probabilities"), rec.get("confidence"))
    return (a.get("choice"), a.get("probabilities"), a.get("confidence"))


def write_jsonl(path, records):
    with io.open(path, "w", encoding="utf-8") as fh:
        for r in records:
            fh.write(json.dumps(r, ensure_ascii=False, sort_keys=False))
            fh.write(u"\n")


def load_jsonl(path):
    out = []
    if not os.path.isfile(path):
        return out
    with io.open(path, encoding="utf-8") as fh:
        for line in fh:
            line = line.strip()
            if line:
                out.append(json.loads(line))
    return out


# ---------------------------------------------------------------------------
# demo.png -- the Jev-repo demo layout: games on the LEFT, the model on the RIGHT
# ---------------------------------------------------------------------------
def build_demo(records, frames_dir, game, backend, out_path, verdict="", proj=None,
               max_steps=10, thumb_w=300):
    """Left column = the frame the model SAW; right column = what it answered, aligned.

    TASK-132 §1.4: "left = the game's frame sequence, right = this step's Jev key/action
    (action name + probability; aligned with the left)".  One picture should let a reader
    see *what the model was playing* without opening any other file.
    """
    from PIL import Image, ImageDraw

    steps = list(records)[:max_steps]
    if not steps:
        return None
    rows = len(steps)
    thumb_h = int(round(thumb_w * 600.0 / 800.0))
    pad = 8
    right_w = 560
    head_h = 54
    row_h = thumb_h + 26
    W = pad * 3 + thumb_w + right_w
    H = head_h + rows * row_h + pad
    canvas = Image.new("RGB", (W, H), (16, 16, 20))
    dr = ImageDraw.Draw(canvas)
    dr.text((pad, 8), "TASK-132 model-player demo -- %s / %s" % (game, backend),
            fill=(255, 255, 255))
    dr.text((pad, 24),
            "left: the full-window frame the model was shown (game endpoint, 800x600)   "
            "right: the model's answer for that step (action + probabilities)",
            fill=(170, 195, 215))
    dr.text((pad, 38), "verdict: %s" % (verdict or ""), fill=(190, 210, 230))
    y = head_h
    for rec in steps:
        fb = os.path.join(frames_dir, rec.get("frame_before_file") or "")
        if os.path.isfile(fb):
            im = Image.open(fb).convert("RGB").resize((thumb_w, thumb_h), Image.LANCZOS)
            canvas.paste(im, (pad, y))
        else:
            dr.rectangle([pad, y, pad + thumb_w, y + thumb_h], outline=(120, 60, 60))
        dr.text((pad, y + thumb_h + 2),
                "step %02d  before %s  after %s  px %s vs ctl %s"
                % (rec.get("step"), (rec.get("frame_before_sha") or "")[:8],
                   (rec.get("frame_after_sha") or "")[:8], rec.get("pixel_diff"),
                   (rec.get("control_diff") or {}).get("pixel_diff")),
                fill=(150, 150, 160))
        x = pad * 2 + thumb_w
        a = rec.get("action") or {}
        ack = rec.get("ack") or {}
        dr.text((x, y + 4), "action: %s   (key %s)   conf %s"
                % (a.get("action"), key_of_action(proj, a.get("action")),
                   rec.get("confidence")), fill=(255, 230, 150))
        dr.text((x, y + 20), "ack: %s  [%s]   changed: %s   -> %s"
                % (ack.get("accepted"), ack.get("evidence_used"), rec.get("changed_bool"),
                   rec.get("step_verdict")),
                fill=(140, 230, 160) if rec.get("changed_bool") else (240, 130, 130))
        probs = rec.get("probs") or {}
        yy = y + 38
        for name, p in sorted(probs.items(), key=lambda kv: -(kv[1] or 0))[:5]:
            try:
                frac = float(p)
            except (TypeError, ValueError):
                frac = 0.0
            w = int(160 * max(0.0, min(1.0, frac)))
            dr.text((x, yy), "%-20s %.4f" % (name, frac), fill=(200, 200, 210))
            dr.rectangle([x + 300, yy + 1, x + 300 + w, yy + 9],
                         fill=(90, 150, 220) if name == a.get("action") else (90, 90, 110))
            yy += 13
        gp = rec.get("gameplay_change_labels") or rec.get("gameplay_changes") or []
        dr.text((x, y + thumb_h - 12),
                "gameplay observables moved: %s" % ("; ".join(gp) or "(none)"),
                fill=(200, 200, 210) if gp else (150, 150, 160))
        y += row_h
    canvas.save(out_path, format="PNG")
    return out_path


def rebuild_artifacts(bdir):
    """Rebuild demo.png (and report what would be in the filmstrip) from a run's records."""
    steps = load_jsonl(os.path.join(bdir, "steps.jsonl"))
    parts = os.path.abspath(bdir).split(os.sep)
    backend, game = parts[-1], parts[-2]
    pj = {}
    if os.path.isfile(os.path.join(bdir, "player.json")):
        pj = json.load(io.open(os.path.join(bdir, "player.json"), encoding="utf-8"))
    proj = None
    try:
        proj = parse_project(game)
    except Exception:  # noqa: BLE001
        pass
    out = os.path.join(bdir, "demo.png")
    return build_demo(steps, os.path.join(bdir, "frames"), game, backend, out,
                      verdict="%s -- %s" % (pj.get("verdict"), pj.get("why")), proj=proj)


def key_of_action(proj, action):
    kc = first_keycode(proj, action) if proj else None
    return keyname_of(kc) if kc else "?"


def resummarise(root):
    """Recompute every run's `player.json` from its recorded `steps.jsonl`.

    The verdict is a pure function of the recorded steps, so a change to the decision rule
    must be re-derivable from the SAME evidence -- otherwise the rule change would be
    indistinguishable from a rerun artefact.  This walks the tree under `root` looking for
    every directory that holds a `steps.jsonl` (runs may be nested under an
    `--out-prefix`, e.g. `realkey/pong/jev/`), keeps the run-level facts that are not in
    `steps.jsonl` (the terminal stop, the prep records, the counts, the stop evidence) and
    re-writes only the computed part.
    """
    out = []
    if not os.path.isdir(root):
        raise SystemExit("no such root: %s" % root)
    for dirpath, dirnames, filenames in os.walk(root):
        dirnames[:] = [d for d in dirnames if not d.startswith("_")]
        if "steps.jsonl" not in filenames:
            continue
        sp = os.path.join(dirpath, "steps.jsonl")
        rel = os.path.relpath(dirpath, root).replace("\\", "/")
        parts = rel.split("/")
        game, backend = parts[-2], parts[-1]
        steps = load_jsonl(sp)
        pj = {}
        if os.path.isfile(os.path.join(dirpath, "player.json")):
            pj = json.load(io.open(os.path.join(dirpath, "player.json"), encoding="utf-8"))
        s = summarise(steps, backend, game,
                      state={"terminal_stop": pj.get("terminal_stop")},
                      player=pj.get("player") or "model",
                      margin=pj.get("change_margin_selected") or CHANGE_MARGIN_DEFAULT,
                      # TASK-140 §1.A.3: the window/round a verdict belongs to are FACTS about
                      # the run, not derived quantities -- they are carried over from the
                      # run's own record (or, for a pre-TASK-140 run, from its `session.json`)
                      # so a resummarise cannot strip a verdict's attribution and silently
                      # promote a w30 reference reading into a pass.
                      nominal_frames=nominal_frames_of_run(dirpath, None, pj)[0],
                      round_index=(pj.get("verdict_context") or {}).get("round"))
        for k in ("prep_actions", "prep", "terminal_stop", "settle_liveness_terminal",
                  "stop", "errors", "agent_errors", "channel", "counts",
                  "terminal_at_settle_before_the_first_model_call",
                  "player", "variant", "variant_note", "image_form",
                  "change_margin_selected",
                  "readable_state_fields", "scripted_policy"):
            if k in pj:
                s[k] = pj[k]
        s["run_dir"] = os.path.abspath(dirpath)
        s["resummarised_from"] = os.path.abspath(sp)
        write_json(os.path.join(dirpath, "player.json"), s)
        out.append({"game": game, "backend": backend, "out_prefix": "/".join(parts[:-2]),
                    "verdict": s["verdict"], "steps": s["steps"],
                    "injected_steps": s.get("injected_steps"),
                    "accepted_steps": s.get("accepted_steps"),
                    "changed_steps_of_accepted": s.get("changed_steps_of_accepted"),
                    "accepted_and_changed_rate": s.get("accepted_and_changed_rate"),
                    "fail_steps": s["fail_steps"], "why": s["why"]})
        log("%-12s %-8s %-13s steps=%-3d injected=%-3s accepted=%-3s changed=%-3s rate=%-7s "
            "fail=%s" % (rel, game, s["verdict"], s["steps"], s.get("injected_steps"),
                         s.get("accepted_steps"), s.get("changed_steps_of_accepted"),
                         s.get("accepted_and_changed_rate"), s["fail_steps"]))
    write_json(os.path.join(root, "_resummary.json"), out)
    return out


# ---------------------------------------------------------------------------
# TASK-132 Y5: the FAIL rule, made self-demonstrating
# ---------------------------------------------------------------------------
def build_failcase(run_dir, out_path, max_steps=6, thumb_w=300):
    """Render the user's FAIL condition from a real run's own records.

    A reader should be able to see, without trusting any prose, that all three clauses
    held at once: the model produced an action, the GAME's own InputMap said the action was
    down, and the picture did not move -- while the equal-length no-input control window
    moved exactly as little.  Returns the JSON summary too.
    """
    from PIL import Image, ImageDraw

    steps = load_jsonl(os.path.join(run_dir, "steps.jsonl"))
    fails = [r for r in steps
             if r.get("step_verdict") == "FAIL_no_change_after_accepted_input"]
    frames_dir = os.path.join(run_dir, "frames")
    shown = (fails or steps)[:max_steps]
    rows = max(1, len(shown))
    thumb_h = int(round(thumb_w * 600.0 / 800.0))
    pad, right_w, head_h = 8, 620, 96
    row_h = thumb_h + 26
    canvas = Image.new("RGB", (pad * 3 + thumb_w + right_w, head_h + rows * row_h + pad),
                       (16, 16, 20))
    dr = ImageDraw.Draw(canvas)
    dr.text((pad, 8), "TASK-132 Y5 -- the user's FAIL condition, reproduced", fill=(255, 80, 80))
    dr.text((pad, 26), "FAIL = the model produced an action AND the game accepted the input "
                       "(its own InputMap says the action is down) AND the picture did not "
                       "change more than the no-input control window.", fill=(220, 220, 220))
    dr.text((pad, 44), "run: %s" % os.path.abspath(run_dir), fill=(150, 170, 190))
    dr.text((pad, 62), "FAIL steps in this run: %s   (verdict in player.json)"
                       % [r.get("step") for r in fails], fill=(200, 200, 210))
    dr.text((pad, 80), "left = the frame the model saw; right = the model's answer and the "
                       "three clauses, each with its own reading", fill=(150, 170, 190))
    y = head_h
    for rec in shown:
        fb = os.path.join(frames_dir, rec.get("frame_before_file") or "")
        fa = os.path.join(frames_dir, rec.get("frame_after_file") or "")
        if os.path.isfile(fb):
            canvas.paste(Image.open(fb).convert("RGB").resize((thumb_w, thumb_h),
                                                              Image.LANCZOS), (pad, y))
        dr.text((pad, y + thumb_h + 2),
                "step %02d  before %s / after %s"
                % (rec.get("step"), (rec.get("frame_before_sha") or "")[:8],
                   (rec.get("frame_after_sha") or "")[:8]), fill=(150, 150, 160))
        x = pad * 2 + thumb_w
        a = rec.get("action") or {}
        ack = rec.get("ack") or {}
        ch = rec.get("change") or {}
        ctl = rec.get("control_diff") or {}
        dr.text((x, y + 4), "1) model action: '%s'   (probs: %s)" % (
            a.get("action"), json.dumps(rec.get("probs") or {}, ensure_ascii=False)[:150]),
            fill=(255, 230, 150))
        dr.text((x, y + 22), "2) game acks: accepted=%s   evidence=%s   "
                             "Input.is_action_pressed=%s"
                % (ack.get("accepted"), ack.get("evidence_used"), ack.get("action_pressed")),
                fill=(140, 230, 160))
        dr.text((x, y + 40), "3) picture: changed=%s   px=%s   control px=%s   "
                             "gameplay movement %s vs control %s"
                % (rec.get("changed_bool"), rec.get("pixel_diff"), ctl.get("pixel_diff"),
                   ch.get("gameplay_movement"), ch.get("control_movement")),
                fill=(240, 130, 130))
        dr.text((x, y + 58), "verdict: %s" % rec.get("step_verdict"), fill=(255, 120, 120))
        for i, line in enumerate(_wrap(ch.get("why_changed") or "", 84)[:3]):
            dr.text((x, y + 78 + i * 13), line, fill=(170, 170, 180))
        y += row_h
    canvas.save(out_path, format="PNG")
    return {"run": os.path.abspath(run_dir), "fail_steps": [r.get("step") for r in fails],
            "rendered_steps": [r.get("step") for r in shown],
            "demo": os.path.abspath(out_path)}


def _wrap(text, width):
    words, lines, cur = text.split(), [], ""
    for w in words:
        if len(cur) + len(w) + 1 > width:
            lines.append(cur)
            cur = w
        else:
            cur = (cur + " " + w).strip()
    if cur:
        lines.append(cur)
    return lines


# ---------------------------------------------------------------------------
# selftest -- the pure decision rules, no game and no model
# ---------------------------------------------------------------------------
def selftest():
    ok = True

    def check(name, got, want):
        nonlocal ok
        good = got == want
        ok = ok and good
        log("%-58s got=%-24r want=%-24r %s" % (name, got, want, "OK" if good else "MISMATCH"))

    # 1. the user's FAIL: accepted + unchanged
    ch = decide_changed(0, 0, 0.0, 0.0)
    check("accepted + 0 px vs 0 control -> not changed", ch["changed"], False)
    check("step_verdict", step_verdict({"accepted": True}, ch),
          "FAIL_no_change_after_accepted_input")

    # 2. a real change
    ch2 = decide_changed(4300, 0, 200.0, 0.0)
    check("4300 px vs 0 control -> changed", ch2["changed"], True)
    check("step_verdict", step_verdict({"accepted": True}, ch2), "ok_ack_and_changed")

    # 3. a game that animates by itself must NOT count as a response
    ch3 = decide_changed(50, 48, 0.0, 0.0)
    check("50 px vs 48 control -> NOT changed", ch3["changed"], False)
    ch4 = decide_changed(100, 120, 0.0, 0.0)
    check("100 px vs 120 control -> NOT changed", ch4["changed"], False)
    ch4b = decide_changed(100, 20, 0.0, 0.0)
    check("100 px vs 20 control -> changed", ch4b["changed"], True)

    # 3b. the pong artefact that forced the magnitude rule: the ball flies in BOTH windows,
    #     so the changed-key COUNT is equal and only the distance tells them apart
    ch6 = decide_changed(1100, 1100, 1.7, 1.7)
    check("ball moved 1.7 px in both windows -> NOT changed", ch6["changed"], False)
    ch7 = decide_changed(1100, 1100, 202.0, 1.7)
    check("paddle moved 202 px vs ball's 1.7 -> changed", ch7["changed"], True)
    mv, det = movement_magnitude([{"key": "PaddleLeft.pos", "from": [24, 226],
                                   "to": [24, 26.67]},
                                  {"key": "Ticks", "from": 5, "to": 6}])
    check("magnitude of a 199 px move + 1 tick", round(mv, 2), 200.33)

    # 4. movement that is equal in both windows is not a response
    ch5 = decide_changed(0, 0, 3.0, 3.0)
    check("gameplay moved the same in control too -> NOT changed", ch5["changed"], False)

    # 5. the three-state summary
    recs = []
    for i in range(1, 9):
        recs.append({"step": i, "action": {"action": "a%d" % i},
                     "ack": {"accepted": True, "injected": True},
                     "change": {"changed": True},
                     "step_verdict": "ok_ack_and_changed"})
    s = summarise(recs, "jev", "g")
    check("8 distinct accepted+changed -> PASS", s["verdict"], "PASS")
    recs_bad = [dict(r) for r in recs]
    recs_bad[3]["change"] = {"changed": False}
    recs_bad[3]["step_verdict"] = "FAIL_no_change_after_accepted_input"
    recs_bad[3]["model"] = {"request_path": "req-3"}
    recs_bad[3]["frame_before_sha"] = "f3"
    # one FAILing step among varied actions, no terminal state -> the strong FAIL
    check("one accepted static step -> FAIL",
          summarise(recs_bad, "jev", "g")["verdict"], "FAIL")
    # the same FAIL, but the model never varied and was handed the same frame: evidence
    # that cannot separate "the game ignores this" from "the model stopped playing"
    recs_stuck = [dict(r) for r in recs]
    for r in recs_stuck[3:]:
        r["change"] = {"changed": False}
        r["step_verdict"] = "FAIL_no_change_after_accepted_input"
        r["action"] = {"action": "same"}
        r["model"] = {"request_path": "req-same"}
        r["frame_before_sha"] = "fsame"
    check("same action + same frame on every failing step -> INCONCLUSIVE",
          summarise(recs_stuck, "jev", "g")["verdict"], "INCONCLUSIVE")
    recs_one = [dict(r, action={"action": "same"}) for r in recs]
    check("one action repeated 8x -> INCONCLUSIVE",
          summarise(recs_one, "jev", "g")["verdict"], "INCONCLUSIVE")
    check("3 steps -> INCONCLUSIVE",
          summarise(recs[:3], "jev", "g")["verdict"], "INCONCLUSIVE")

    # 6. ack evidence naming
    a = ack_verdict("pong_left_up", {"is_action_pressed": True}, None, ["PaddleLeft.pos"])
    check("ack evidence prefers action_pressed", a["evidence_used"], "action_pressed")
    check("ack accepted", a["accepted"], True)
    a2 = ack_verdict("snake_left", {"is_action_pressed": False}, None, [],
                     refusal="LastRefusedInput: '1,0'")
    check("refusal is recorded as acceptance-of-event", a2["evidence_used"],
          "refused_recorded")
    a3 = ack_verdict("x", {"is_action_pressed": False}, None, [])
    check("nothing -> not accepted", a3["accepted"], False)
    # a step where the model produced NO action must never be credited to the game
    a4 = ack_verdict(None, None, None, ["Ball.pos"], action_state=None)
    check("no model action -> not injected", a4["injected"], False)
    check("no model action -> not accepted", a4["accepted"], False)
    recs_noaction = [dict(r, ack={"accepted": False, "injected": False},
                          step_verdict="no_ack_no_change") for r in recs]
    check("8 steps but the model never acted -> INCONCLUSIVE",
          summarise(recs_noaction, "jev", "g")["verdict"], "INCONCLUSIVE")

    # 7. TASK-133 §1.C.1: the MODEL's fixed point, as its own conclusion
    recs_fp = []
    for i in range(1, 9):
        recs_fp.append({"step": i, "action": {"action": "same"},
                        "ack": {"accepted": True, "injected": True},
                        "change": {"changed": True},
                        "frame_before_sha": "fpframe", "confidence": 0.58,
                        "step_verdict": "ok_ack_and_changed"})
    fp = model_fixed_point(recs_fp)
    check("8 identical action+frame steps -> fixed point found", fp["found"], True)
    check("fixed-point run length", fp["length"], 8)
    check("fixed-point steps", fp["steps"], [1, 2, 3, 4, 5, 6, 7, 8])
    check("fixed-point action", fp["action"], "same")
    # the threshold is 3: two identical steps are not a fixed point
    check("2 identical steps -> NOT a fixed point", model_fixed_point(recs_fp[:2])["found"],
          False)
    check("3 identical steps -> a fixed point", model_fixed_point(recs_fp[:3])["found"],
          True)
    # the same action on DIFFERENT frames is not a fixed point (the model is answering
    # the picture, the picture is moving)
    recs_moving = [dict(r) for r in recs_fp]
    for i, r in enumerate(recs_moving):
        r["frame_before_sha"] = "frame%02d" % i
    check("same action on different frames -> NOT a fixed point",
          model_fixed_point(recs_moving)["found"], False)
    # a non-injected step (the model answered `wait`) breaks the run
    recs_wait = [dict(r) for r in recs_fp]
    recs_wait[4] = dict(recs_wait[4], ack={"accepted": False, "injected": False},
                        action={"action": None})
    fp2 = model_fixed_point(recs_wait)
    check("a `wait` step breaks the run (4 = longest)", fp2["length"], 4)
    # the fixed point is REPORTED on the summary and does NOT make the game FAIL
    s_fp = summarise(recs_fp, "jev", "g")
    check("summary carries MODEL_FIXED_POINT", s_fp["MODEL_FIXED_POINT"], True)
    check("summary carries the fixed-point reading",
          isinstance(s_fp["MODEL_FIXED_POINT_reading"], str) and
          bool(s_fp["MODEL_FIXED_POINT_reading"]), True)
    check("fixed point is not a game FAIL", s_fp["verdict"], "INCONCLUSIVE")
    check("fixed point is not a game PASS", s_fp["verdict"] == "PASS", False)
    # a clean run has no fixed point at all
    check("clean run -> no fixed point", summarise(recs, "jev", "g")["MODEL_FIXED_POINT"],
          False)
    check("clean run -> still PASS", summarise(recs, "jev", "g")["verdict"], "PASS")

    # 7b. TASK-134 §1.C.1: MODEL_NO_PROGRESS -- the fixed point's wider twin.
    #     The measured blind spot: pong x playjev varied its action once, so the fixed-point
    #     rule (same action AND same frame) never fired, and nine failing steps were filed as
    #     the "strong" reading of a game FAIL.  The new rule must catch them anyway.
    recs_mixed = [dict(r) for r in recs]
    for i, r in enumerate(recs_mixed, 1):
        r["frame_before_sha"] = "frame%02d" % i          # a different frame every step
        r["action"] = {"action": "mixed%d" % i}          # ... and a different action
        r["change"] = {"changed": False}
        r["step_verdict"] = "FAIL_no_change_after_accepted_input"
        r["ack"] = {"accepted": True, "injected": True}
    npg = model_no_progress(recs_mixed)
    check("mixed actions + no progress -> MODEL_NO_PROGRESS", npg["found"], True)
    check("the whole run is the no-progress run", npg["length"], 8)
    check("the actions really did differ", npg["distinct_actions"],
          sorted("mixed%d" % i for i in range(1, 9)))
    check("no-progress reading names its status",
          "NOT a game defect" in npg["what"], True)
    # the same action AND the same frame, with no change, is BOTH conclusions at once --
    # exactly what the recorded `pong x playjev` run shows (TASK-133 §4.2a): the fixed
    # point fired for 8 steps and the wider rule sees the same 8 steps.
    recs_fp_static = [dict(r, change={"changed": False},
                           step_verdict="FAIL_no_change_after_accepted_input")
                      for r in recs_fp]
    check("same action+frame+no change -> BOTH conclusions",
          (model_fixed_point(recs_fp_static)["found"],
           model_no_progress(recs_fp_static)["found"]), (True, True))
    # ... but a fixed point that DID change the picture is not "no progress"
    check("same action+frame that DID change -> only the fixed point",
          (model_fixed_point(recs_fp)["found"], model_no_progress(recs_fp)["found"]),
          (True, False))
    # a run that progresses triggers neither
    check("clean run -> no MODEL_NO_PROGRESS",
          model_no_progress([dict(r) for r in recs])["found"], False)
    # ... and the threshold is 3, exactly like the fixed point's
    check("2 static steps -> NOT MODEL_NO_PROGRESS",
          model_no_progress(recs_mixed[:2])["found"], False)
    check("3 static steps -> MODEL_NO_PROGRESS",
          model_no_progress(recs_mixed[:3])["found"], True)
    # a `wait` step (nothing was sent) breaks the run: it is not a measurement of the game
    recs_gap = [dict(r) for r in recs_mixed]
    recs_gap[4] = dict(recs_gap[4], ack={"accepted": False, "injected": False},
                       action={"action": None})
    check("a `wait` step breaks the no-progress run", model_no_progress(recs_gap)["length"], 4)
    # the summary reports it, and it does NOT touch the game verdict
    s_np = summarise(recs_mixed, "playjev", "pong")
    check("summary carries MODEL_NO_PROGRESS", s_np["MODEL_NO_PROGRESS"], True)
    check("summary still says FAIL for that run", s_np["verdict"], "FAIL")
    check("no-progress is not a graph PASS", s_np["verdict"] == "PASS", False)
    check("no-progress threshold recorded",
          s_np["thresholds"]["model_no_progress_min_run"], 3)

    # 7c. TASK-134 §1.A: the scripted arm's GAME-side verdict, on the same records.
    recs_scripted = [dict(r) for r in recs]
    recs_scripted[0] = dict(recs_scripted[0], change={"changed": False},
                            step_verdict="FAIL_no_change_after_accepted_input")
    s_sc = summarise(recs_scripted, "scripted", "pong", player="scripted")
    check("scripted arm gets a game_side_verdict", s_sc.get("game_side_verdict"), "FAIL")
    s_sc_ok = summarise([dict(r) for r in recs], "scripted", "pong", player="scripted")
    check("scripted arm with 8/8 progress -> game-side PASS",
          s_sc_ok.get("game_side_verdict"), "PASS")
    check("the model arm does NOT get a game_side_verdict",
          "game_side_verdict" in summarise([dict(r) for r in recs], "jev", "pong"), False)

    # 8. TASK-133 §1.C.2: `done` is gone from the option set the probe offers
    from playtest_agent import action_criteria as _ac
    crit = _ac({"actions": {"a_up": ["W"]}, "keys": []})
    check("probe criteria no longer offer `done`", "done" in crit, False)
    check("probe criteria still offer `wait`", "wait" in crit, True)
    check("probe criteria still offer the declared action", "a_up" in crit, True)

    # 9. TASK-135 §1.B: the two change margins, on the four numbers TASK-134 §7.4 named.
    #    `pong x jev x V3` steps 2/3/7 (real measured values): the baseline counts all
    #    three, the strict margin must drop the 1.09x and 1.19x ones and keep the 2.35x one.
    ch_edge_a = decide_changed(2240, 2240, 780.4, 717.3)     # step 2: ratio 1.088
    check("baseline counts a 1.09x gameplay win", ch_edge_a["changed"], True)
    check("strict drops a 1.09x gameplay win",
          ch_edge_a["strict"]["changed"], False)
    check("strict records the ratio", ch_edge_a["strict"]["margin_ratio"], 1.088)
    ch_keep = decide_changed(512, 512, 323.3, 137.5)         # step 3: ratio 2.351
    check("strict keeps a 2.35x gameplay win (>= 2x)", ch_keep["strict"]["changed"], True)
    check("strict changed implies baseline changed",
          all(not decide_changed(px, ctl, mv, cmv)["strict"]["changed"] or
              decide_changed(px, ctl, mv, cmv)["changed"]
              for (px, ctl, mv, cmv) in ((2240, 2240, 780.4, 717.3),
                                         (512, 512, 323.3, 137.5),
                                         (0, 0, 5.0, 0.0),
                                         (100, 20, 0.0, 0.0),
                                         (0, 0, 0.0, 0.0))), True)
    # a zero-control window: the ratio is undefined, so the floor decides
    ch_zero = decide_changed(0, 0, 0.5, 0.0)
    check("zero control + 0.5 movement -> baseline changed", ch_zero["changed"], True)
    check("zero control + 0.5 movement -> strict NOT changed (below the floor)",
          ch_zero["strict"]["changed"], False)
    check("zero control + 1.0 movement -> strict changed",
          decide_changed(0, 0, 1.0, 0.0)["strict"]["changed"], True)
    check("the pixel term is the same in both margins (2.5x)",
          decide_changed(1000, 500, 0.0, 0.0)["strict"]["changed"],
          decide_changed(1000, 500, 0.0, 0.0)["changed"])
    # the two verdicts, side by side, on ONE run: 8 steps, 2 of them gameplay-edge
    # (the measured `pong x jev x V3` numbers: step 2 = 1.088x, step 3 = 2.351x,
    #  step 7 = 1.195x, the rest decided by the pixel term with a zero control window)
    recs_margin = []
    for i in range(1, 9):
        if i == 2:
            edge = decide_changed(2240, 2240, 780.4, 717.3)
        elif i == 3:
            edge = decide_changed(512, 512, 323.3, 137.5)
        elif i == 7:
            edge = decide_changed(512, 512, 766.2, 641.1)
        else:
            edge = decide_changed(4300, 0, 200.0, 0.0)
        recs_margin.append({"step": i, "action": {"action": "act%d" % i},
                            "ack": {"accepted": True, "injected": True},
                            "change": edge, "changed_bool": edge["changed"],
                            "frame_before_sha": "frame%d" % i,
                            "step_verdict": ("ok_ack_and_changed" if edge["changed"] else
                                             "FAIL_no_change_after_accepted_input")})
    s_margin = summarise(recs_margin, "jev", "pong")
    # TASK-136 §1.A.1: the strict margin is now the PASS criterion, so this run -- which the
    # baseline passes on 8/8 but the strict margin refuses on steps 2 and 7 -- is
    # `PASS(baseline only)` and is NOT counted as a pass.  That is the whole mechanism.
    check("margin run: the run is PASS(baseline only), not PASS",
          s_margin["verdict"], "PASS(baseline only)")
    check("margin run: PASS(baseline only) does NOT count as a pass",
          s_margin["counts_as_pass"], False)
    check("margin run: the control reading is preserved separately",
          s_margin["baseline_verdict"], "PASS")
    check("margin run: control rate is still 1.0",
          s_margin["baseline_accepted_and_changed_rate"], 1.0)
    check("margin run: the criterion rate is the strict one (0.75)",
          s_margin["accepted_and_changed_rate"], 0.75)
    check("margin run: strict rate is 0.75", s_margin["strict_accepted_and_changed_rate"],
          0.75)
    check("margin run: the strict reading of that run FAILS (the two edge steps)",
          s_margin["strict_verdict"], "FAIL")
    check("margin run: strict names the two edge steps", s_margin["strict_fail_steps"],
          [2, 7])
    check("margin run: the PASS criterion is `strict` by default",
          s_margin["change_margin"]["selected"], "strict")
    check("margin run: the top-level verdict is not a plain PASS",
          s_margin["verdict"] == "PASS", False)
    check("margin run: edge steps are named", len(s_margin["change_margin_edge_steps"]), 2)
    check("margin run: edge steps list their ratios",
          [e["margin_ratio"] for e in s_margin["change_margin_edge_steps"]], [1.088, 1.195])
    check("margin run: the declaration is recorded",
          s_margin["change_margin"]["declaration_source"].endswith(
              "playability_controls.json"), True)
    # A run the strict margin DOES pass must still be a plain `PASS` and count.
    s_margin_ok = summarise([dict(r) for r in recs], "jev", "pong")
    check("a run strict passes is a plain PASS", s_margin_ok["verdict"], "PASS")
    check("a run strict passes counts as a pass", s_margin_ok["counts_as_pass"], True)
    # Explicitly asking for the baseline reading gives the historical verdict, with the
    # strict reading kept beside it -- the control reading is never destroyed.
    s_base = summarise(recs_margin, "jev", "pong", margin="baseline")
    check("margin=baseline: the control verdict is PASS", s_base["verdict"], "PASS")
    check("margin=baseline: the strict reading is preserved beside it",
          s_base["strict_verdict"], "FAIL")
    check("margin=baseline: the criterion is named", s_base["pass_criterion"], "baseline")
    check("margin=baseline: the criterion reading is recorded",
          "TASK-136" in s_base["pass_criterion_reading"], True)
    try:
        summarise(recs_margin, "jev", "pong", margin="loose")
        check("an unknown margin raises", False, True)
    except ValueError:
        check("an unknown margin raises", True, True)
    # a record written BEFORE TASK-135 carries no `change.strict`: it must read as the
    # baseline, never as an error, and never as a different verdict
    recs_old = [dict(r) for r in recs_margin]
    for r in recs_old:
        r["change"] = {"changed": r["change"]["changed"]}
    s_old = summarise(recs_old, "jev", "pong")
    check("a pre-TASK-135 record: the criterion still passes", s_old["verdict"], "PASS")
    check("a pre-TASK-135 record: counts as a pass", s_old["counts_as_pass"], True)
    check("a pre-TASK-135 record: the control reading is the same",
          s_old["baseline_verdict"], "PASS")
    check("a pre-TASK-135 record: strict falls back to the baseline reading",
          s_old["strict_verdict"], "PASS")
    check("a pre-TASK-135 record: no edge steps claimed",
          s_old["change_margin_edge_steps"], [])

    # ---- TASK-138 defect ⑨: an injection with NO `ack_result` is INCONCLUSIVE --------
    # The old `inj.get("ack_result") or pre_ack` let the PRE-injection reading stand in for
    # the post-injection one.  These four checks pin the new rule: the step is not accepted,
    # the run is not PASS and not FAIL on those steps, and the pre-injection reading is
    # recorded but never credited.
    def ack_missing_step(i, pre_pressed=True):
        ack = {
            "accepted": False, "injected": False, "evidence_used": "ack_missing",
            "evidence_all": ["ack_missing"],
            "action_pressed": None,
            "ack_missing": {"step": i, "action": "act%d" % i,
                            "pre_ack_used_as_evidence": False,
                            "pre_ack_recorded_only": {"is_action_pressed": pre_pressed,
                                                      "strength": 1.0},
                            "ack_result_present": False},
            "note": "no post-injection ack",
        }
        return {
            "step": i,
            "action": {"action": "act%d" % i, "type": "action"},
            "ack": ack,
            "change": {"changed": False},
            "frame_before_sha": "frame%d" % i,
            "model": {"request_path": "req-%d" % i},
            "markers": {"GameOver": False},
            "step_verdict": STEP_VERDICT_ACK_MISSING,
            "frame_budget": {"achieved_delta": 30, "action_frames": 30,
                             "step_frame_start": 1000 + 40 * i,
                             "step_frame_end": 1030 + 40 * i},
            "control_diff": {"frame_budget": {"achieved_delta": 30, "start_drawn": 990,
                                              "end_drawn": 1020}},
        }

    recs_nock = [ack_missing_step(i) for i in range(1, 9)]
    s_nock = summarise(recs_nock, "jev", "g")
    check("ack missing: the run is NOT a pass", s_nock["counts_as_pass"], False)
    check("ack missing: the run is not written as PASS", s_nock["verdict"] == "PASS", False)
    check("ack missing: the run is not written as FAIL", s_nock["verdict"] == "FAIL", False)
    check("ack missing: every step is INCONCLUSIVE",
          s_nock["verdict"], "INCONCLUSIVE")
    check("ack missing: the count is reported", s_nock["ack_missing"]["count"], 8)
    check("ack missing: the fallback is declared off",
          s_nock["ack_missing"]["pre_ack_fallback"], False)
    check("ack missing: the step verdict is named",
          s_nock["ack_missing"]["step_verdict"], STEP_VERDICT_ACK_MISSING)
    check("ack missing: the pre-injection reading is filed as diagnosis only",
          s_nock["ack_missing"]["steps"][0]["ack_missing"]["pre_ack_used_as_evidence"],
          False)
    check("ack missing: the pre-injection reading is still recoverable verbatim",
          s_nock["ack_missing"]["steps"][0]["ack_missing"]["pre_ack_recorded_only"]
          ["is_action_pressed"], True)
    check("ack missing: no step is counted as accepted",
          s_nock["accepted_steps"], 0)
    check("ack missing: the accepted-and-changed rate is undefined, not 1.0",
          s_nock["accepted_and_changed_rate"], None)
    # the pre-injection reading really said "pressed": the OLD rule would have called this
    # step accepted and (with a static picture) FAIL.  The new rule must not.
    old_style = ack_missing_step(1)
    old_aware = ack_verdict("act1", None, None, [],
                            action_state=old_style["ack"]["ack_missing"]
                            ["pre_ack_recorded_only"])
    check("the pre-injection reading alone WOULD have said accepted (why the fallback "
          "mattered)", old_aware["accepted"], True)
    check("...and the recorded step still says it was not accepted",
          old_style["ack"]["accepted"], False)

    # ---- TASK-138 defect ⑧: the two windows' achieved frame counts are reported ------
    s_align = summarise(recs_nock, "jev", "g")
    check("frame alignment: every step is reported", s_align["frame_alignment"]
          ["step_count"], 8)
    check("frame alignment: equal windows are counted as matched",
          s_align["frame_alignment"]["matched_step_count"], 8)
    check("frame alignment: all_matched is True",
          s_align["frame_alignment"]["all_matched"], True)
    check("frame alignment: the control count is the recorded achieved delta",
          s_align["frame_alignment"]["steps"][0]["control_frames"], 30)
    check("frame alignment: the action count is the recorded achieved delta",
          s_align["frame_alignment"]["steps"][0]["action_frames"], 30)
    recs_skew = [dict(r) for r in recs_nock]
    for r in recs_skew:
        r["frame_budget"] = dict(r["frame_budget"], action_frames=47, achieved_delta=47)
    s_skew = summarise(recs_skew, "jev", "g")
    check("frame alignment: unequal windows are NOT reported as matched",
          s_skew["frame_alignment"]["matched_step_count"], 0)
    check("frame alignment: all_matched is False when they differ",
          s_skew["frame_alignment"]["all_matched"], False)
    check("frame alignment: the difference is visible as two numbers",
          [s_skew["frame_alignment"]["steps"][0]["control_frames"],
           s_skew["frame_alignment"]["steps"][0]["action_frames"]], [30, 47])
    check("frame alignment: the rule is declared in the summary",
          "SAME achieved drawn-frame count"
          in s_align["frame_alignment"]["reading"], True)
    # a run recorded BEFORE TASK-138 has no action_frames field and must fall back to the
    # old achieved_delta rather than inventing an alignment
    recs_legacywin = [dict(r) for r in recs_nock]
    for r in recs_legacywin:
        r["frame_budget"] = {"achieved_delta": 117, "target_delta": 30}
        r["control_diff"] = {"frame_budget": {"achieved_delta": 31, "target_delta": 30}}
    s_legacywin = summarise(recs_legacywin, "jev", "g")
    check("frame alignment: a pre-TASK-138 run reports its real achieved deltas",
          [s_legacywin["frame_alignment"]["steps"][0]["action_frames"],
           s_legacywin["frame_alignment"]["steps"][0]["control_frames"]], [117, 31])
    check("frame alignment: and is honestly reported as NOT matched",
          s_legacywin["frame_alignment"]["all_matched"], False)

    # ---- TASK-138 defect ⑧: the wait target is ABSOLUTE ------------------------------
    class _A(object):
        window_frames = 30
        window_timeout = 8.0
        window_poll_gap = 0.005

    pr = Player.__new__(Player)
    pr.args = _A()
    check("absolute target: start + delta", pr.frame_target_for(1000), 1030)
    check("absolute target: an explicit delta overrides the default",
          pr.frame_target_for(1000, 12), 1012)
    check("absolute target: no start frame -> no target", pr.frame_target_for(None), None)
    stub = {"frame_budget": {"achieved_delta": 30}, "movement": 0, "pixel_diff": 0}
    check("align_windows: equal counts match", Player.align_windows(stub, 30)["matched"],
          True)
    check("align_windows: unequal counts do not",
          Player.align_windows(stub, 31)["matched"], False)
    check("align_windows: the delta is the action minus the control",
          Player.align_windows(stub, 47)["delta"], 17)
    check("align_windows: a missing action count is not a match",
          Player.align_windows(stub, None)["matched"], False)

    log("selftest %s" % ("PASSED" if ok else "FAILED"))
    return 0 if ok else 1


# ---------------------------------------------------------------------------
# prep -- read-only environment probe
# ---------------------------------------------------------------------------
def probe_health(url, timeout=20):
    import urllib.request
    try:
        with urllib.request.urlopen(url, timeout=timeout) as r:
            return {"url": url, "status": r.status,
                    "body": r.read().decode("utf-8", "replace")[:600]}
    except Exception as e:  # noqa: BLE001
        return {"url": url, "status": None, "error": "%s: %s" % (type(e).__name__, e)}


def prep():
    import socket

    def free(p):
        s = socket.socket()
        try:
            s.settimeout(0.4)
            return s.connect_ex(("127.0.0.1", p)) != 0
        finally:
            s.close()

    games = (g for g in os.listdir(os.path.join(ROOT, "projects"))
             if g != "_exercises" and not g.startswith("_"))
    out = {
        "task": "TASK-132", "when": time.strftime("%Y-%m-%d %H:%M:%S"),
        "services": {"jev_8080": probe_health("http://127.0.0.1:8080/health"),
                     "playjev_8081": probe_health("http://127.0.0.1:8081/health")},
        "ports": dict((str(p), "free" if free(p) else "IN USE") for p in
                      (9921, 9931, 9932, 9933, 9941, 9951, 9952, 9961)),
        "engine": {"path": pg.ENGINE, "exists": os.path.isfile(pg.ENGINE),
                   "version": engine_version()},
        "exes": {},
        "playability_controls": os.path.join(HERE, "playability_controls.json"),
    }
    for g in sorted(games):
        exe = os.path.join(DEFAULT_EXE_ROOT, g, g + ".exe")
        out["exes"][g] = {"path": exe, "exists": os.path.isfile(exe),
                          "bytes": os.path.getsize(exe) if os.path.isfile(exe) else None}
    p = os.path.join(RUNS_PLAYER, "_env", "prep.json")
    write_json(p, out)
    log(json.dumps(out["services"], ensure_ascii=False))
    log(json.dumps(out["ports"], ensure_ascii=False))
    log("wrote %s" % os.path.abspath(p))
    return 0


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------
def main(argv=None):
    ap = argparse.ArgumentParser(
        description="TASK-132 model-player loop: image -> model action -> inject -> "
                    "ack/change evidence -> demo")
    sub = ap.add_subparsers(dest="cmd")

    r = sub.add_parser("run", help="run the model-player loop for one game and one backend")
    r.add_argument("--game", required=True)
    r.add_argument("--backend", default="jev", choices=("jev", "playjev", "scripted"))
    # TASK-134 §1.A: the two ARMS.  `model` = the TASK-132/133 model player; `scripted` =
    # the deterministic human-like policy that measures the GAME rather than the model.
    r.add_argument("--player", default="model", choices=("model", "scripted"),
                   help="model = the model-player arm (the TASK-132/133 criterion); "
                        "scripted = the deterministic human-like policy arm, which answers "
                        "'can the GAME be played' and calls no service")
    # TASK-134 §1.B: the declarative variants.  V1 is the untouched baseline.
    r.add_argument("--variant", default="V1", choices=VARIANT_IDS,
                   help="declarative request variant: V1 baseline (unchanged), V2 "
                        "image+readable state, V3 question/candidate descriptions, V4 "
                        "anti-repeat on top of V3, V5 image form (see --image-form).  "
                        "Every variant is filed beside the baseline, never in place of it")
    r.add_argument("--image-form", default="full",
                   choices=("full", "crop", "downsample"),
                   help="TASK-134 §1.B/V5: the image the model is shown -- 'full' is the "
                        "800x600 full-window frame the baseline uses; 'crop' cuts to the "
                        "measured content bbox; 'downsample' is 400x300")
    r.add_argument("--scripted-alternate", action="store_true",
                   help="scripted arm only: use the game-RULE-AWARE snake policy that "
                        "always asks for a CHANGE of direction (SnakeGame.cs only steps on "
                        "a direction change).  The default scripted snake policy steers "
                        "toward the food like a human would; this flag measures whether the "
                        "game's own rule, not the policy, is what limits progress")
    # TASK-135 §1.B: which of the two DECLARED change margins the verdict uses.  The other
    # reading is always computed and filed beside it, so this switch can never hide one.
    r.add_argument("--change-margin", default=CHANGE_MARGIN_DEFAULT,
                   choices=CHANGE_MARGINS,
                   help="which declared change margin `player.json -> verdict` is computed "
                        "with.  TASK-136 §1.A.1: the DEFAULT is 'strict' (>= %.1fx the "
                        "control window's movement, floor %.1f) and ONLY a strict pass is "
                        "written as PASS; 'baseline' (TASK-132: gameplay movement > control "
                        "movement) is kept as the CONTROL reading, and a run it passes while "
                        "strict does not is written as 'PASS(baseline only)' with "
                        "counts_as_pass=false.  BOTH readings are always reported; the "
                        "declaration lives in tools/playability_controls.json -> "
                        "model_player_change_margin"
                        % (CHANGE_STRICT_CONTROL_FACTOR, CHANGE_STRICT_MIN_MOVEMENT))
    r.add_argument("--base-url", default="",
                   help="override the service root (default 8080 for jev, 8081 for playjev)")
    r.add_argument("--mode", default="project", choices=("project", "exe"),
                   help="project = the source project under godot; exe = dist/exe/<game>")
    r.add_argument("--project-dir", default="",
                   help="override where the project lives (e.g. projects\\_exercises\\neg_frozen)")
    r.add_argument("--controls-game", default="",
                   help="which game's declaration in tools/playability_controls.json to "
                        "judge by (default: this game; a neg_* variant names its SOURCE "
                        "game, e.g. neg_frozen -> breakout)")
    r.add_argument("--exe-root", default=DEFAULT_EXE_ROOT)
    r.add_argument("--steps", type=int, default=10)
    r.add_argument("--actions", nargs="*", default=None,
                   help="narrow the Choice criteria to these declared actions (the default "
                        "is the game's whole InputMap)")
    r.add_argument("--prep-actions", nargs="*", default=[],
                   help="declare action(s) injected ONCE before the model plays, to bring "
                        "the game into the state a human starts from (pong parks the ball "
                        "and waits for SPACE; its own AutoServe then keeps re-serving).  "
                        "Recorded separately in prep.json, with its own before/after frames")
    r.add_argument("--objective", default="")
    r.add_argument("--action-instructions", default="",
                   help="override the text of the action question (recorded verbatim in "
                        "the saved request)")
    r.add_argument("--channel", default="parse", choices=("parse", "real"),
                   help="parse = Input.parse_input_event (the gate's faithful channel); "
                        "real = Win32 SendInput to the focused game window")
    r.add_argument("--hold-ms", type=int, default=350,
                   help="how long the action is held down (the InputMap state is read "
                        "while it is down, which is the ack evidence)")
    r.add_argument("--window-frames", type=int, default=30,
                   help="the measurement window, in DRAWN GAME FRAMES (default 30 = ~0.5 s "
                        "at 60 Hz).  The no-input control window and the action window use "
                        "the SAME budget, so a game that animates by itself cannot pass by "
                        "accident.  TASK-140 §1.A.3: the run RECORDS this nominal budget, "
                        "and a run below the declared reporting window (%d) cannot count as "
                        "a pass" % WINDOW_REPORTING_FRAMES)
    r.add_argument("--round", type=int, default=None,
                   help="TASK-140 §1.A.3: which INDEPENDENT COMPLETE RUN of this game at this "
                        "window this is (round 1, round 2, ...).  It is recorded in "
                        "`player.json -> verdict_context` and printed beside the verdict, so "
                        "no verdict in an artifact or a report is unattributed.  Two rounds "
                        "of the same game at the same window are what "
                        "`playtest_player.py stability` compares for the UNSTABLE judgement.  "
                        "The default (None) means 'unrecorded', which neither creates nor "
                        "removes a pass")
    r.add_argument("--window-timeout", type=float, default=8.0,
                   help="wall-clock cap while waiting for --window-frames to elapse")
    r.add_argument("--window-poll-gap", type=float, default=0.005,
                   help="TASK-138 defect ⑧: seconds slept between the two drawn-frame "
                        "polls of a measurement window.  It was hard-coded at 0.02; the "
                        "game advances several frames per MCP call, so a coarse gap is "
                        "what let an 'equal' 30-frame budget land on 34 vs 117 frames")
    r.add_argument("--ack-read-delay-ms", type=int, default=60,
                   help="settle before reading the game's own InputMap state for the ack; "
                        "an OS key is turned into an InputEventKey by the DisplayServer, so "
                        "a same-millisecond read can see the InputMap before the engine has "
                        "processed the message (measured in the first real-key run)")
    r.add_argument("--control-ms", type=int, default=0,
                   help="DEPRECATED: wall-clock control window; 0 means 'use the frame "
                        "budget instead' (see --window-frames)")
    r.add_argument("--step-gap", type=float, default=0.35)
    r.add_argument("--settle", type=float, default=4.0)
    r.add_argument("--port", type=int, default=DEFAULT_PORT)
    r.add_argument("--ready-timeout", type=float, default=240)
    r.add_argument("--call-timeout", type=float, default=60)
    r.add_argument("--timeout", type=float, default=180)
    r.add_argument("--max-state-retries", type=int, default=2)
    r.add_argument("--out-prefix", default="")
    r.add_argument("--no-patience", dest="patience", action="store_false", default=True,
                   help="disable the early stop after 8 consecutive accepted+changed steps")
    r.add_argument("--ignore-terminal", action="store_true",
                   help="run the model even when the game is already in its declared "
                        "terminal state at settle (the default is to abort before the first "
                        "model call and report INCONCLUSIVE, because a game that is over "
                        "cannot demonstrate anything about playability)")

    sub.add_parser("prep", help="read-only environment probe -> runs/model-player/_env/prep.json")
    sub.add_parser("selftest", help="exercise the pure decision rules; no game, no model")

    s = sub.add_parser("summary", help="re-print the three-state verdict for an existing run")
    s.add_argument("--path", required=True, help="a <game>/<backend> evidence directory")

    a = sub.add_parser("demo", help="rebuild demo.png + filmstrip.png from steps.jsonl")
    a.add_argument("--path", required=True, help="a <game>/<backend> evidence directory")

    rs = sub.add_parser("resummarise", help="recompute every player.json from steps.jsonl")
    rs.add_argument("--root", default=RUNS_PLAYER)

    st = sub.add_parser("stability",
                        help="TASK-140 §1.A.2: UNSTABLE -- do >= 2 rounds of one game agree?")
    st.add_argument("--run", action="append", default=[],
                    help="a run's player.json (or its evidence directory); give it once per "
                         "round.  At least two independent complete runs at the SAME window "
                         "are required before a stability judgement is made")
    st.add_argument("--min-rounds", type=int, default=STABILITY_MIN_ROUNDS)
    st.add_argument("--out", default="",
                    help="write the judgement here (default: print only)")
    st.add_argument("--require-engine-state", action="store_true",
                    help="exit 1 when the judgement is UNSTABLE (for a caller that must not "
                         "count an unstable game as a pass)")

    f = sub.add_parser("failcase", help="Y5: render the FAIL condition from a run's records")
    f.add_argument("--path", required=True, help="a <game>/<backend> evidence directory")
    f.add_argument("--out", default="", help="default <path>/failcase.png")

    args = ap.parse_args(argv)
    if args.cmd == "prep":
        return prep()
    if args.cmd == "selftest":
        return selftest()
    if args.cmd == "stability":
        if len(args.run) < args.min_rounds:
            log("stability: %d run(s) given; at least %d are required (TASK-140 §1.A.2)"
                % (len(args.run), args.min_rounds))
        out = stability_from_paths(args.run, min_rounds=args.min_rounds)
        log("STABILITY %s/%s: %s -- %s" % (out.get("game"), out.get("window_frames"),
                                           out.get("state"), out.get("why")))
        for p in out.get("divergence_points") or []:
            log("  divergence step %s criterion %s: round %s vs round %s"
                % (p.get("step"), p.get("criterion"), p.get("round_a"), p.get("round_b")))
        if args.out:
            write_json(args.out, out)
            log("wrote %s" % os.path.abspath(args.out))
        else:
            log(json.dumps(out, ensure_ascii=False, indent=1))
        if args.require_engine_state and out.get("state") == STABILITY_STATE_UNSTABLE:
            return 1
        return 0
    if args.cmd == "summary":
        p = os.path.join(args.path, "steps.jsonl")
        recs = load_jsonl(p)
        parts = os.path.abspath(args.path).split(os.sep)
        m = CHANGE_MARGIN_DEFAULT
        pj = os.path.join(args.path, "player.json")
        if os.path.isfile(pj):
            try:
                m = json.load(io.open(pj, encoding="utf-8")).get(
                    "change_margin_selected") or m
            except Exception:  # noqa: BLE001
                m = CHANGE_MARGIN_DEFAULT
        s = summarise(recs, parts[-1], parts[-2], margin=m)
        log(json.dumps(s, ensure_ascii=False, indent=1))
        return 0
    if args.cmd == "resummarise":
        resummarise(args.root)
        return 0
    if args.cmd == "failcase":
        out = args.out or os.path.join(args.path, "failcase.png")
        info = build_failcase(args.path, out)
        write_json(os.path.join(args.path, "failcase.json"), info)
        log(json.dumps(info, ensure_ascii=False, indent=1))
        return 0
    if args.cmd == "demo":
        log("rebuilt %s" % rebuild_artifacts(args.path))
        return 0
    if args.cmd != "run":
        ap.print_help()
        return 2
    run = Player(args)
    run.run()
    return 0


if __name__ == "__main__":
    sys.exit(main())
