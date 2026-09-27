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
CHANGE_MARGIN_DEFAULT = "baseline"


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
    return out


CHANGE_MARGIN_DECLARATION = load_change_margins()


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
              margin=None):
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
                    "beside it and is never used to replace it" % margin),
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
    return out


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
    changed = [r for r in accepted if changed_of(r, margin)]
    # The FAIL condition, read under THIS margin.  Under `baseline` this set is exactly the
    # set of steps whose recorded `step_verdict` is FAIL (that verdict is the baseline
    # reading, written by the loop while the run was happening); under `strict` it is the
    # same question asked with the stricter margin, and the baseline set is kept beside it.
    fail_steps = [r["step"] for r in steps
                  if r.get("step_verdict") == "FAIL_no_change_after_accepted_input"] \
        if margin == "baseline" else \
        [r["step"] for r in accepted if not changed_of(r, "strict")]
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
    same_action_fixed_point = bool(
        len(fail_steps) >= 2 and len(fail_actions) == 1 and
        (len(fail_reqs) <= 1 or len(fail_frames) <= 1))
    # TASK-133 §1.C.1: the model's fixed point as its OWN conclusion, on its own
    # threshold (>= 3 identical action + identical frame).  It is a statement about the
    # model, so it lives beside the game verdict instead of inside it.
    fixed = model_fixed_point(steps)
    # TASK-134 §1.C.1: the second, wider model-side conclusion.  Computed and REPORTED
    # here; it deliberately does not enter any branch of the game verdict below, so the
    # game's FAIL/PASS/INCONCLUSIVE reading is byte-for-byte the rule TASK-132/133 used.
    noprog = model_no_progress(steps)
    # TASK-134 §1.A: the GAME-side numbers, which answer "can this game be played" on
    # their own.  `progress_steps` counts the SENT steps whose picture advanced more than
    # its own no-input control window: the same predicate `decide_changed` already uses.
    injected_steps_list = [r for r in steps if (r.get("ack") or {}).get("injected")]
    progress_steps = [r["step"] for r in injected_steps_list
                      if changed_of(r, margin)]
    # TASK-135 §1.B: the same count under the OTHER margin, so a reader of `player.json`
    # never has to open the step files to see whether the two readings differ.
    progress_steps_baseline = [r["step"] for r in injected_steps_list
                               if changed_of(r, "baseline")]
    progress_steps_strict = [r["step"] for r in injected_steps_list
                             if changed_of(r, "strict")]
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
        "change_margin_used": margin,
        "match_seconds_in_game_clock": match_seconds,
        "game_clock_first_last_ms": ([stamps[0][0], stamps[-1][0]] if len(stamps) >= 2
                                     else None),
        "steps_without_an_action_from_the_model": no_action,
        "injected_steps": len(model_steps),
        "accepted_steps": len(accepted), "changed_steps_of_accepted": len(changed),
        "accepted_and_changed_rate": (round(len(changed) / float(len(accepted)), 4)
                                      if accepted else None),
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
                "baseline_*/strict_* and in `change_margin`"
                % (PASS_MIN_STEPS, PASS_MIN_RATE, MODEL_FIXED_POINT_MIN_RUN,
                   MODEL_NO_PROGRESS_MIN_RUN, margin,
                   CHANGE_MARGIN_DECLARATION[margin]["gameplay_control_factor"]),
    }
    if fail_steps and not same_action_fixed_point and not unchanged_terminal:
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
    elif out["accepted_and_changed_rate"] < PASS_MIN_RATE:
        out["verdict"] = "FAIL"
        out["why"] = ("accepted-and-changed rate %.4f < %.2f over %d accepted step(s)"
                      % (out["accepted_and_changed_rate"], PASS_MIN_RATE, len(accepted)))
    else:
        out["verdict"] = "PASS"
        out["why"] = ("%d/%d accepted steps changed the viewport (%.4f) over %d step(s); "
                      "the reader's per-frame check corroborates it"
                      % (len(changed), len(accepted), out["accepted_and_changed_rate"], n))
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
        elif out["progress_rate_of_accepted"] < PASS_MIN_RATE:
            out["game_side_verdict"] = "FAIL"
            out["game_side_why"] = ("game-side progress rate %.4f < %.2f over %d accepted "
                                    "step(s)" % (out["progress_rate_of_accepted"],
                                                 PASS_MIN_RATE, len(accepted)))
        else:
            out["game_side_verdict"] = "PASS"
            out["game_side_why"] = ("%d/%d accepted steps advanced the game (%.4f) over %d "
                                    "step(s) of a deterministic human-like policy; the "
                                    "model-evidence clauses (one-action loop, fixed point) "
                                    "do not apply to a scripted policy"
                                    % (len(progress_steps), len(accepted),
                                       out["progress_rate_of_accepted"], n))
        out["game_side_rule"] = ("same thresholds as the model arm (>= %d injected steps, "
                                 ">= %.2f progress, FAIL on any accepted-but-unchanged "
                                 "step); only the two MODEL-evidence clauses are dropped, "
                                 "and they are dropped because a scripted policy has no "
                                 "'stopped playing' ambiguity to resolve"
                                 % (PASS_MIN_STEPS, PASS_MIN_RATE))
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
        return ("hold the game's InputMap action '%s' (bound key(s): %s)"
                % (name, keys or "?"))

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
                crit[name] = self.action_effect(name, ks, self.current_readable_state)
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

        # --- the no-input control window, on the SAME frame budget ---------
        # Measured FIRST and from the same `frame_count` the action window will start at,
        # so the two windows are the same length in GAME FRAMES, not merely in wall time.
        ctl = self.control_window(f_before, s_before, w0)
        control_px = ctl["pixel_diff"]
        control_gp = ctl["gameplay_changes"]

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

        # --- observe: wait out the SAME number of game frames --------------
        f_after, s_after, win_ev = self.window_after(w0, "%02d_after" % i)

        delta, gp = gameplay_delta(s_before.get("state"), s_after.get("state"),
                                   self.gameplay_decl)
        gp_keys = [c.get("key") for c in gp]
        px = png_changed(f_before["path"], f_after["path"]) if f_after else {
            "comparable": False, "changed_pixels": None}
        refuse = refusal_hit(delta, self.refusal_decl)
        mv, mv_detail = movement_magnitude(gp)
        real_info = None
        ack_state_for_verdict = None
        if injectable and isinstance(inj, dict):
            ack_state_for_verdict = inj.get("ack_result") or pre_ack
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
        ack = ack_verdict(act_name, None, None, gp_keys, refusal=refuse,
                          real_key=real_info, action_state=ack_state_for_verdict)
        change = decide_changed(px.get("changed_pixels"), control_px, mv, ctl["movement"])
        change["gameplay_detail"] = mv_detail
        change["gameplay_changes"] = gp_keys
        change["control_gameplay_changes"] = ctl["gameplay_changes"]
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
            "control_diff": dict(ctl, state_delta=len(ctl["delta"])),
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

    def wait_frames(self, w0, target=None):
        """Wait until the game has DRAWN `target` more frames than `w0` (from the game)."""
        target = int(target if target is not None else self.args.window_frames)
        ev = {"start_drawn": w0, "target_delta": target, "polls": 0}
        t0 = time.time()
        last = None
        while time.time() - t0 < self.args.window_timeout:
            st, _r = self.gd(probe_state_source(), "wait:frames")
            ev["polls"] += 1
            last = (st or {}).get("drawn") if isinstance(st, dict) else None
            if w0 is not None and isinstance(last, int) and (last - w0) >= target:
                break
            time.sleep(0.02)
        ev["end_drawn"] = last
        ev["achieved_delta"] = ((last - w0) if isinstance(last, int) and w0 is not None
                                else None)
        ev["seconds"] = round(time.time() - t0, 3)
        ev["timed_out"] = bool(ev["achieved_delta"] is None or
                               ev["achieved_delta"] < target)
        return ev

    def control_window(self, f_before, s_before, w0):
        """The equal-length, NO-input control window: same frame budget, no input at all."""
        wev = self.wait_frames(w0)
        c_end = self.capture("ctl_end")
        c_state = self.sample_state("ctl_end")
        px = png_changed(f_before["path"], c_end["path"]) if c_end else {
            "changed_pixels": None}
        delta, gp = gameplay_delta(s_before.get("state"), c_state.get("state"),
                                   self.gameplay_decl)
        mv, _detail = movement_magnitude(gp)
        return {
            "pixel_diff": max(0, px.get("changed_pixels") or 0),
            "gameplay_changes": [c.get("key") for c in gp],
            "movement": mv,
            "delta": delta,
            "frame_budget": wev,
            "frame_end_file": os.path.basename((c_end or {}).get("path") or ""),
            "rule": "same number of DRAWN game frames as the action window, zero input; "
                    "the two windows are therefore the same length in game frames, not "
                    "merely in wall time",
        }

    def window_after(self, w0, label):
        wev = self.wait_frames(w0)
        f = self.capture(label)
        s = self.sample_state(label)
        return f, s, wev

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
            "state_markers": self.marker_decl,
            "declarations_source": os.path.join(HERE, "playability_controls.json"),
            "channel": args.channel,
            "measurement_window": {
                "unit": "drawn game frames (Engine.get_frames_drawn(), read by "
                        "playability_gate.probe_state_source)",
                "frames": args.window_frames,
                "wall_clock_cap_s": args.window_timeout,
                "control": "the same frame budget with ZERO input, measured immediately "
                           "before each injection",
                "why": "the two windows must be the same length in GAME frames: an "
                       "equal-wall-clock window can contain a different number of frames "
                       "around an MCP round trip, and the first pong run measured exactly "
                       "that artefact (the action window and the control window both "
                       "reported 1100 changed pixels)",
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
                            margin=getattr(args, "change_margin", CHANGE_MARGIN_DEFAULT))
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
        log("VERDICT %s/%s: %s -- %s" % (self.game, self.backend, summary["verdict"],
                                         summary["why"]))
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
                      margin=pj.get("change_margin_selected") or CHANGE_MARGIN_DEFAULT)
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
    check("margin run: baseline verdict is PASS", s_margin["verdict"], "PASS")
    check("margin run: baseline rate is 1.0", s_margin["accepted_and_changed_rate"], 1.0)
    check("margin run: strict rate is 0.75", s_margin["strict_accepted_and_changed_rate"],
          0.75)
    check("margin run: the strict reading of that run FAILS (the two edge steps)",
          s_margin["strict_verdict"], "FAIL")
    check("margin run: strict names the two edge steps", s_margin["strict_fail_steps"],
          [2, 7])
    check("margin run: the baseline verdict is still the top-level one by default",
          s_margin["change_margin"]["selected"], "baseline")
    check("margin run: edge steps are named", len(s_margin["change_margin_edge_steps"]), 2)
    check("margin run: edge steps list their ratios",
          [e["margin_ratio"] for e in s_margin["change_margin_edge_steps"]], [1.088, 1.195])
    check("margin run: the declaration is recorded",
          s_margin["change_margin"]["declaration_source"].endswith(
              "playability_controls.json"), True)
    # --change-margin=strict moves the top-level verdict and leaves the baseline beside it
    s_strict = summarise(recs_margin, "jev", "pong", margin="strict")
    check("margin=strict: the top-level verdict is the strict one",
          s_strict["verdict"], "FAIL")
    check("margin=strict: the baseline verdict is preserved beside it",
          s_strict["baseline_verdict"], "PASS")
    check("margin=strict: baseline rate still reported",
          s_strict["baseline_accepted_and_changed_rate"], 1.0)
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
    check("a pre-TASK-135 record: baseline verdict unchanged", s_old["verdict"], "PASS")
    check("a pre-TASK-135 record: strict falls back to the baseline reading",
          s_old["strict_verdict"], "PASS")
    check("a pre-TASK-135 record: no edge steps claimed",
          s_old["change_margin_edge_steps"], [])

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
                        "with: 'baseline' (TASK-132: gameplay movement > control movement; "
                        "the default, and byte-for-byte the historical rule) or 'strict' "
                        "(TASK-135 §1.B: >= %.1fx the control window's movement, floor "
                        "%.1f).  BOTH readings are always reported; the declaration lives "
                        "in tools/playability_controls.json -> model_player_change_margin"
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
                        "accident")
    r.add_argument("--window-timeout", type=float, default=8.0,
                   help="wall-clock cap while waiting for --window-frames to elapse")
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

    f = sub.add_parser("failcase", help="Y5: render the FAIL condition from a run's records")
    f.add_argument("--path", required=True, help="a <game>/<backend> evidence directory")
    f.add_argument("--out", default="", help="default <path>/failcase.png")

    args = ap.parse_args(argv)
    if args.cmd == "prep":
        return prep()
    if args.cmd == "selftest":
        return selftest()
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
