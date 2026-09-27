#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""playability_gate.py -- TASK-116 items A/B/C: the "playability gate".

Why this tool exists (the decision this file implements)
--------------------------------------------------------
A user played 20 games and reported that *some of them are not playable*.  The
evidence we had before this tool was all `shots-editor`: `editor_capture_screenshot`
photographs the **whole editor window** (2978x1793 on this machine) with the running
game embedded in a small sub-window inside it, so a "512 px changed" measurement
was a measurement of a tiny embedded region, not of what a player sees.

This tool therefore measures the thing the report is about:

  * it starts the game as a **real game process** -- the engine binary without
    `-e`, a real OS window, **never `--headless`** -- with the MCP endpoint on the
    **game side** (`--mcp-port`, no `--mcp-capture`, because the frames are taken
    on purpose, one at a time);
  * it captures **full-window** frames through `running_game_capture_screenshot`,
    which reads the game's **root viewport** (`mcp_capture.cpp:270-296`: on the
    game side the viewport is always `tree->get_root()`, whatever
    `--mcp-capture-viewport` says);
  * every frame is stored with the **window geometry** next to it: the OS window
    size (`DisplayServer.window_get_size`), the root viewport size
    (`Viewport.get_visible_rect`), and the size the project *declares*
    (`display/window/size/viewport_width|height`), plus whether they agree.

The five gate criteria (item B), each machine-checked and each leaving something
a human can look at:

  P1 visibility      full-window frame -> background = modal colour, content mask =
                     pixels differing from it by > PIXEL_DELTA.  Reports the content
                     fraction, the content bounding box and the bbox coverage.
                     FAIL when the game paints (almost) nothing or paints it in a
                     corner of the window.
  P2 input response  inject the key of every **declared action** (its own
                     `project.godot` InputMap) and require a state or pixel change
                     within P2_FRAMES frames.  Two independent channels are used,
                     and they are NOT the same thing:
                       `key`    -- a real `InputEventKey` pushed through
                                   `Viewport.push_input`, i.e. the path an OS key
                                   press takes to `_Input` / `_UnhandledInput`;
                       `action` -- `Input.action_press`, i.e. the path
                                   `Input.IsActionPressed` polling sees.
                     A game that answers one but not the other is reported as a
                     mismatch, not silently credited.
  P3 main loop       `Engine.get_frames_drawn()` must advance, and the game's
                     own quantities must move: either by themselves (autonomous
                     frames) or after a player action.  "Frozen but all asserts
                     are green" fails here by construction.
  P4 no crash/hang   the process is alive at the end, every MCP call answered
                     inside its timeout, and no **modal dialog** appeared: visible
                     top-level windows of the process tree are enumerated with
                     EnumWindows and any window that is not the game window is
                     evidence.
  P5 discoverability the actions declared in `project.godot` are cross-checked with
                     the keys the README claims, and every declared action is
                     *actually* exercised (P2's result is reused), so the answer is
                     "a human can find the controls and they do something", not
                     "the InputMap has entries".
  P6 capability      the curated capability table names, for every thing a player must be
                     able to do, the declared action that delivers it and the observable
                     that must move -- and P2's measured result is checked against it.
  P7 required UI     TASK-130: the game's own `required_ui` declaration names the UI/control
                     nodes a player needs (HUD readout, board container, next-piece
                     indicator, the food a snake must see ...).  A probe reads those nodes
                     out of the LIVE tree and every item must exist, be the declared class,
                     be visible IN THE TREE, keep an alpha above P7_MIN_ALPHA, cover at
                     least its declared area inside the viewport, and (where declared) not
                     be blank.  This is the criterion for the failure mode P1..P6 cannot
                     see: the interface is gone while the game itself is fine.
                     `--only-p7` runs just this one (and says so in the artifact).

Nothing here is a shell redirect, and nothing is deleted outside this tool's own
output directory: iron rule 1 (the game's stdout/stderr are owned by
`subprocess` file handles), iron rule 2 (every destructive path is checked
against `RUNS\\playability\\` first), iron rule 3 (the game is launched by
`cmd.exe /c <generated .cmd>`), iron rule 4 (one unique port, checked before use).

Usage
-----
    python tools\\playability_gate.py --games pong tetris        # a few
    python tools\\playability_gate.py --all                       # all 20
    python tools\\playability_gate.py --calibrate                 # metrics only
    python tools\\playability_gate.py --games pong --agent=openai # model in the loop

The REAL model service (TASK-128)
---------------------------------
`--agent=jev` is the only path that talks to a deployed NeoHorse-Jev.  It reaches the
service named by `--base-url` (new in TASK-128) or, when that is empty, by the
`PLAYTEST_BASE_URL` environment variable.  Nothing else changes it: there is no
hard-coded host, and an unset address is a recorded `wait` (never a silent success).

    :: window command -- this DOES hit the real 8080 service:
    set PLAYTEST_BASE_URL=http://127.0.0.1:8080
    set PLAYTEST_MODEL=NeoHorse-Jev-4B
    python tools\\playability_gate.py --all --agent=jev --base-url http://127.0.0.1:8080
    :: evidence of what was reached lands in runs\\playability\\<game>\\agent.json:
    ::   report.base_url, report.health.json.model, and per call
    ::   .response_status / .model / .usage / .confidence_header, plus the
    ::   `x-neohorse-confidence` and `x-neohorse-usage` response headers.

`--probe` / `--probe-jev` / `--probe-playjev` / `--selfcheck` on `playtest_agent.py`
are NOT a way to call a real service: they start a *dumb* in-process server and never
touch a deployed port (measured in TASK-125).  Only the `--agent=jev` /
`--agent=playjev` invocations above do.  `--base-url` deliberately does nothing for
`--agent=scripted`/`none`; it is recorded in `gate\\agent\\service`.

One measured trap on the jev path (TASK-128, fixed in TASK-129): the state is the game's
whole exported node tree and **15 of the 20 games exceed Jev's documented 2048-token
`state` cap**, so the service answers HTTP 422 `state exceeds 2048 tokens: N` and the model
never runs.  The client's `jev_estimate_tokens` was not the guard it read as: this JSON
tokenizes at ~2.1-2.4 real tokens per estimated one (client 1018 -> service 2160; client
1791 -> service 4229).  TASK-129 D-C fixes that estimator (a conservative x2.5 coefficient
calibrated on the service's own `usage`, plus a bounded "answer a real 422 by halving the
budget" retry); the flag `--agent-state-budget` trims the state's `nodes` in tree order and
records every dropped node.  **The unit changed**: `--agent-state-budget 2000` selects
exactly the state `--agent-state-budget 800` did in TASK-128 (2000/2.5), so the fitted jev
thresholds stay comparable.  The exact state text handed over is recorded as a sha256 + head
in `gate\\agent\\observations[i].state_for_agent`.

TASK-129 D-B, the sampling defect
---------------------------------
TASK-128 measured that the gate handed the SAME `s_end` to all three `decide()` calls, and
the three answers came back bit-identical -- i.e. one independent model observation per game,
not three.  `--agent-state-samples N` (default 3) now picks N states that are HASH-DIFFERENT
as the model sees them (preference: before input / after input / after the input round),
sends one per call, and records each call with the state it was given.  Fewer than N distinct
states => `sample_size: 1`, stated in the artifact.

The VISION service (TASK-127, wired into the gate in TASK-129 C)
----------------------------------------------------------------
Two ways to reach PlayJev 0.8B, the model that was actually fine-tuned on pixels:

  * `--agent=playjev` -- the image-state DECISION backend (TASK-127).  Its server answers
    the same `POST /v1/systemone` name as Jev but takes
    `{"state": {"frames": ["data:image/png;base64,..."]}}` and serves `type: "choice"`
    questions ONLY, so a `noul`/`score` question -- legal on Jev -- is a 400 there.  The
    backend expresses the invariants as yes/no Choices and the brokenness rating as an
    ordered-levels Choice, and it can carry ONE image + N questions in a single request.
    Its default address is `http://127.0.0.1:8081`; `PLAYTEST_BASE_URL` (or `--base-url`)
    overrides it.  An answer it cannot use is recorded as an ABSTAIN and never as a pass.
  * `--visual-agent=playjev` -- TASK-129's gate path: it runs BESIDE `--agent`, judges the
    frames this run captured (one request per frame, one image + N questions), asks the
    playability invariant as `playable`, and writes `gate["playjev"]` next to
    `gate["agent"]`.  `score` is recorded there as an explicitly UNCALIBRATED,
    DIRECTION-SUSPECT observation and is NOT in the decision path (D-E); the optional
    `--visual-legend-probe` asks one frame with the legend order reversed to test whether
    the inversion is a wording artefact, and its result never enters a verdict either.

    :: window command -- this DOES hit the real 8081 service:
    set PLAYTEST_BASE_URL=http://127.0.0.1:8081
    set PLAYTEST_MODEL=playjev-0.8b
    python tools\\playability_gate.py --games pong --agent=playjev --base-url http://127.0.0.1:8081

    :: TASK-129: both backends in one pass, negatives from an exercise tree:
    python tools\\playability_gate.py --games pong --agent=jev --base-url http://127.0.0.1:8080 --agent-state-budget 2000 --visual-agent=playjev
    python tools\\playability_gate.py --exercise neg_frozen --games neg_frozen --agent=jev --visual-agent=playjev --out-root runs\\playability\\negatives

    :: TASK-130: the declarative required-UI criterion alone, over every game (fast):
    python tools\\playability_gate.py --all --only-p7 --out-root runs\\playability\\t130-p7

    :: TASK-130 B: the same vision backend, but shown the CONTENT CROP of each frame:
    python tools\\playability_gate.py --games pong --visual-agent=playjev --visual-input-form crop

Declarative negative variants (TASK-129 D-D)
--------------------------------------------
`projects\\_exercises\\neg_*` holds COPIES of real projects whose scene file declares one
failure (input dead / black screen / frozen / HUD removed), so the four failure modes can be
sampled with REAL full-window frames without touching `projects\\<game>`.  `--exercise <name>`
makes such a directory addressable like a game; `--out-root` decides where its frames land.

Outputs
-------
    runs\\playability\\<game>\\frames\\NN_<label>.png     full-window frames
    runs\\playability\\<game>\\frames.json                per-frame geometry + metrics
    runs\\playability\\<game>\\filmstrip.png              all frames in one image
    runs\\playability\\<game>\\states\\NN_<label>.json    sampled game state
    runs\\playability\\<game>\\gate.json                  P1..P7 verdicts + evidence
                                                        (P7 carries `p7_probe`, the raw
                                                        node read it was judged from)
    runs\\playability\\<game>\\agent.json                 the text backend: every call,
                                                        every state it judged (D-B), and
                                                        every 422 budget retry (D-C)
    runs\\playability\\<game>\\playjev.json               the vision backend: per-frame
                                                        probabilities, the `playable`
                                                        answer, the score observation
                                                        and the flip-legend probe
    runs\\playability\\playability.json                   machine-readable, all games
    runs\\playability\\summary.txt                        the console log, verbatim
"""

from __future__ import print_function

import argparse
import base64
import hashlib
import io
import json
import os
import re
import shutil
import subprocess
import sys
import time

import numpy as np
from PIL import Image, ImageDraw

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)                       # ...\godot-mcp
PROJECTS = os.path.join(ROOT, "projects")
EXERCISES = os.path.join(PROJECTS, "_exercises")   # TASK-129 D-D negative variants live here
RUNS = os.path.join(ROOT, "runs", "playability")
ENGINE = os.path.join(ROOT, "godot", "bin", "godot.windows.editor.x86_64.mono.console.exe")
ENGINE_CWD = os.path.join(ROOT, "godot")
REPORTS = os.path.join(ROOT, "recovery", "reports")

# TASK-129 D-D: a declarative negative variant is a *copy* of a real project under
# `projects\_exercises\neg_*`, so the gate has to be told where to find it.  `--exercise`
# registers those names here; every path lookup for a game goes through `project_dir()`,
# which keeps `projects\<game>` the default and makes the exception explicit and recorded.
GAME_DIRS = {}


def project_dir(game):
    """Where this game's project lives: `projects\\<game>`, or the registered exercise."""
    return GAME_DIRS.get(game) or os.path.join(PROJECTS, game)


# TASK-117: the same gate must be able to judge **the exported artifact** instead of
# the project.  A game can be playable in the editor build and broken in the export
# (that is exactly the failure this switch exists to be able to see), so the two
# runs are kept apart by output root and the executable is what changes, nothing
# else.  `EXE_ROOT` is `<root>\dist\exe`; the gate then launches
# `<EXE_ROOT>\<game>\<game>.exe --mcp-port=N` with the game's own directory as cwd.
EXE_ROOT = None

sys.path.insert(0, HERE)
from playtest_agent import build_agent, keycode_of, keyname_of  # noqa: E402
from playtest_agent import jev_estimate_tokens, jev_render_state  # noqa: E402
from playtest_agent import JEV_TOKEN_SAFETY_FACTOR, PLAYJEV_SCORE_DIRECTION_NOTE  # noqa: E402

# --- gate constants, with the basis for each --------------------------------
# P1: a frame is "content" only where it differs from its own modal colour.
PIXEL_DELTA = 16              # 0..255 per channel; below this is film grain / dither
# P1 thresholds.  Basis: measured over the 20 games on 2026-xx-xx -- see
# PLAYABILITY-REPORT.md section "P1 threshold basis"; the whole sweep's numbers
# are in runs\playability\playability.json, so the threshold can be re-judged
# against its own data instead of being taken on faith.
#
# TASK-131 X14 RE-DERIVATION.  The old 0.004 was below every real game's own settle
# frame, so it never had a basis: measured over the 25 targets (runs/realinput/_scripts/
# p1_metrics.py prints the table), the settle-frame content fraction runs
#   snake 0.0060 (pathological: a 35%-alpha game-over overlay over an empty board)
#   rtype 0.01099, pong 0.0182, asteroids 0.0310, missilecommand 0.0458, ...
#   tetris 0.4860
# i.e. the lowest HEALTHY game is rtype at 1.099%.  0.008 is chosen as the largest round
# value that keeps all 20 positives green (1.37x margin under rtype) and still rejects
# snake's 0.0060 -- and it is 2x the old value.  It is FITTED FOR SEPARATION on one
# pathological example, not calibrated: with n=1 there is no calibration to claim.
P1_MIN_CONTENT_FRACTION = 0.008    # >=0.8% of the window's pixels are content
# TASK-131: bbox_coverage is kept at 0.12 but DEMOTED to a diagnostic, because the snake
# frame proves it is a SPAN metric, not a FILL metric: snake scored 33% "coverage" from
# two specks in opposite corners (a 24x24 pellet at (0,0) and a 96x24 snake at (576,240)),
# because the union bounding box of the two spans 600x264.  No threshold on a span can
# tell "content fills the frame" from "two dots in opposite corners", so P1 records
# `bbox_fill` (content pixels / bbox area) per frame and does not judge on it.
P1_MIN_BBOX_COVERAGE = 0.12       # content bbox spans >=12% of the window area
P2_FRAMES = 45                    # "within N frames": 45 drawn frames (~0.75 s @60)
P2_SETTLE_S = 0.45
P3_MIN_CHANGED_PIXELS = 40        # a genuine frame-to-frame change, not noise
# TASK-130 P7: a declared required-UI node whose modulate alpha is at or below this is
# treated as "not on screen" (the engine reports it visible_in_tree, the player sees
# nothing).  Basis: modulate.a is exactly 1.0 for every declared node of all 20 games
# measured at settle; 0.01 only separates "fully transparent" from "faded".
P7_MIN_ALPHA = 0.01
# TASK-131 X12: what may NOT be counted as "the game played".  Every pattern here has a
# measured counterpart in the recorded evidence -- `snake` passed P2 on `DirectionX` and
# `LastRefusedInput`, and P3 on `Ticks`-like clocks plus `frames_drawn`.  A change that
# matches any of these is an input acknowledgement, a clock, a refusal, a digest or a
# flag: it is evidence about the PLUMBING, never about the game world.
META_KEY_PATTERNS = [
    r"\.Ticks$", r"\.Elapsed$", r"\._logTimer$", r"\.AutoPlay$", r"\.AutoSteps$",
    r"\.LastAutoSteps$", r"\.LastHookSteps$",
    r"\.LastEvent$",                 # a STRING that describes the last input
    r"\.LastRefusedInput$", r"Rejected",
    r"\.Input[A-Z]",                 # input accounting: InputMoves/InputShots/InputAims..
    r"\.Paused$", r"\.GameOver$", r"\.LoseReason$", r"\.Won$", r"\.CanMoveAny$",
    r"\.Facing$", r"\.Direction[XY]$",     # an input intent, not a world position
    r"\.LastDir$", r"\.LastMoveDir$", r"\.LastSwap$", r"\.LastChain$",
    r"\.LastCleared$", r"\.AngleIndex$",   # the aim index: an intent, and animated by nothing
    r"\.Seed$",
    r"Hash$",                        # a digest OF the state, not the state
    r"\.text$",                      # a Label's rendering of some other value
    r"\.started$", r"\.Moved$",
]
DEFAULT_PORT = 9911
STATE_NODE_CAP = 4000

# ---------------------------------------------------------------------------
# logging
# ---------------------------------------------------------------------------
_LOG = []


def log(msg):
    line = str(msg)
    _LOG.append(line)
    print(line, flush=True)


# ---------------------------------------------------------------------------
# tiny helpers
# ---------------------------------------------------------------------------
def read_text(path):
    for enc in ("utf-8", "utf-8-sig", "gbk", "latin-1"):
        try:
            with io.open(path, "r", encoding=enc) as fh:
                return fh.read()
        except Exception:  # noqa: BLE001
            continue
    return ""


def write_json(path, obj):
    d = os.path.dirname(path)
    if d and not os.path.isdir(d):
        os.makedirs(d)
    with io.open(path, "w", encoding="utf-8") as fh:
        fh.write(json.dumps(obj, ensure_ascii=False, indent=1, sort_keys=False))


def sha256_file(path):
    h = hashlib.sha256()
    with open(path, "rb") as fh:
        for chunk in iter(lambda: fh.read(65536), b""):
            h.update(chunk)
    return h.hexdigest()


def assert_inside(path, prefix=None):
    # `prefix` is resolved at call time, not at def time: TASK-117 moves RUNS to
    # `runs\playability-exe` for the exported-artifact sweep, and the guard has to
    # move with it (otherwise the gate would refuse to clean its own new output).
    prefix = prefix or RUNS
    full = os.path.abspath(path)
    pre = os.path.abspath(prefix).rstrip("\\") + os.sep
    if not full.lower().startswith(pre.lower()):
        raise RuntimeError("REFUSED: '%s' is not inside '%s'" % (full, prefix))
    return full


# ---------------------------------------------------------------------------
# project.godot / README parsing  (the P5 audit's static half)
# ---------------------------------------------------------------------------
KEY_GLYPHS = {u"\u2191": "UP", u"\u2193": "DOWN", u"\u2190": "LEFT", u"\u2192": "RIGHT"}
README_KEY_TOKEN = re.compile(r"`([^`]{1,24})`")


def parse_project(game):
    pdir = project_dir(game)
    gd = read_text(os.path.join(pdir, "project.godot"))
    info = {"game": game, "dir": pdir, "dir_is_exercise": pdir.startswith(EXERCISES)}
    m = re.search(r"window/size/viewport_width=(\d+)", gd)
    m2 = re.search(r"window/size/viewport_height=(\d+)", gd)
    info["declared_viewport"] = [int(m.group(1)), int(m2.group(1))] if m and m2 else None
    m = re.search(r"window/size/window_width_override=(\d+)", gd)
    m2 = re.search(r"window/size/window_height_override=(\d+)", gd)
    info["declared_window_override"] = [int(m.group(1)), int(m2.group(1))] if m and m2 else None
    m = re.search(r'window/stretch/mode="([^"]*)"', gd)
    info["declared_stretch_mode"] = m.group(1) if m else None
    m = re.search(r'run/main_scene="([^"]*)"', gd)
    info["main_scene"] = m.group(1) if m else None

    # --- the InputMap the game itself declares ---------------------------
    block = re.search(r"\[input\]\n(.*?)(?=\n\[[a-z]|\Z)", gd, re.S)
    actions = {}
    if block:
        for am in re.finditer(r"^([A-Za-z0-9_]+)=\{(.*?)\n\}", block.group(1), re.M | re.S):
            name = am.group(1)
            body = am.group(2)
            codes = [int(x) for x in re.findall(r'"keycode": (\d+)', body)]
            phys = [int(x) for x in re.findall(r'"physical_keycode": (\d+)', body)]
            mb = re.findall(r'InputEventMouseButton', body)
            actions[name] = {"keycode": codes, "physical_keycode": phys,
                             "keys": [keyname_of(c) for c in codes if c],
                             "mouse": bool(mb),
                             "raw_events": len(re.findall(r"Object\(", body))}
    info["actions"] = actions
    info["actions_declared"] = list(actions.keys())

    # --- the keys the README claims --------------------------------------
    readme_path = os.path.join(pdir, "README.md")
    readme = read_text(readme_path) if os.path.isfile(readme_path) else ""
    info["readme_path"] = readme_path if os.path.isfile(readme_path) else None
    play = re.search(r"##\s*玩法(.*?)(?=\n##\s|\Z)", readme, re.S) if readme else None
    info["readme_play_section"] = play.group(1).strip() if play else None
    readme_keys = []
    if play:
        for tok in README_KEY_TOKEN.findall(play.group(1)):
            t = tok.strip()
            if t in KEY_GLYPHS:
                readme_keys.append(KEY_GLYPHS[t])
                continue
            kc = keycode_of(t)
            if kc is not None and (len(t) == 1 or t.upper() in ("SPACE", "ENTER", "UP", "DOWN",
                                                                "LEFT", "RIGHT")):
                readme_keys.append(keyname_of(kc))
    info["readme_keys"] = readme_keys
    # which declared action owns each README key
    claimed = []
    for k in readme_keys:
        kc = keycode_of(k)
        owners = [n for n, a in actions.items() if kc in a["keycode"]]
        claimed.append({"key": k, "keycode": kc, "actions": owners,
                        "known": bool(owners)})
    info["readme_key_claims"] = claimed
    return info


# ---------------------------------------------------------------------------
# MCP client (HTTP JSON-RPC, stdlib only)
# ---------------------------------------------------------------------------
class McpError(Exception):
    pass


class Mcp(object):
    def __init__(self, port, log_dir=None, timeout=40):
        self.port = port
        self.url = "http://127.0.0.1:%d/mcp" % port
        self.timeout = timeout
        self.log_dir = log_dir
        self.n = 0
        self.calls = []
        if log_dir and not os.path.isdir(log_dir):
            os.makedirs(log_dir)

    def _post(self, payload, tag=None):
        import urllib.request
        import urllib.error
        body = json.dumps(payload).encode("utf-8")
        req = urllib.request.Request(self.url, data=body, method="POST")
        req.add_header("Content-Type", "application/json")
        t0 = time.time()
        try:
            resp = urllib.request.urlopen(req, timeout=self.timeout)
            raw = resp.read().decode("utf-8", "replace")
        except Exception as e:  # noqa: BLE001
            raise McpError("%s: %s" % (type(e).__name__, e))
        dt = time.time() - t0
        if self.log_dir and tag:
            write_json(os.path.join(self.log_dir, tag + ".response.json"),
                       {"seconds": round(dt, 3), "raw": raw})
        return raw, dt

    def call_tool(self, name, args, timeout=None):
        self.n += 1
        old = self.timeout
        if timeout:
            self.timeout = timeout
        tag = "%03d_%s" % (self.n, name)
        try:
            raw, dt = self._post({"jsonrpc": "2.0", "id": self.n, "method": "tools/call",
                                  "params": {"name": name, "arguments": args}}, tag)
        finally:
            self.timeout = old
        rec = {"n": self.n, "tool": name, "args": args, "seconds": round(dt, 3),
               "raw_len": len(raw)}
        try:
            doc = json.loads(raw)
        except Exception as e:  # noqa: BLE001
            rec.update({"ok": False, "error": "bad json: %s" % e, "raw": raw[:400]})
            self.calls.append(rec)
            return rec
        if "error" in doc:
            rec.update({"ok": False, "error": doc["error"], "raw": raw[:600]})
            self.calls.append(rec)
            return rec
        res = doc.get("result") or {}
        rec["isError"] = bool(res.get("isError"))
        text = None
        for c in (res.get("content") or []):
            if c.get("type") == "text":
                text = c.get("text")
                break
        if text is None:
            rec.update({"ok": False, "error": "no text content", "raw": raw[:600]})
            self.calls.append(rec)
            return rec
        try:
            value = json.loads(text)
        except Exception:  # noqa: BLE001
            value = {"_raw_text": text}
        rec["ok"] = not rec["isError"]
        rec["value"] = value
        self.calls.append(rec)
        return rec

    def tools_list(self):
        self.n += 1
        raw, dt = self._post({"jsonrpc": "2.0", "id": self.n, "method": "tools/list",
                              "params": {}}, "%03d_tools_list" % self.n)
        doc = json.loads(raw)
        tools = [t["name"] for t in doc.get("result", {}).get("tools", [])]
        self.calls.append({"n": self.n, "tool": "tools/list", "ok": True,
                           "seconds": round(dt, 3), "count": len(tools)})
        return tools


# ---------------------------------------------------------------------------
# GDScript probes -- everything the gate learns about the game's own state is
# read *inside the game process*, never inferred from the outside.
# ---------------------------------------------------------------------------
PROBE_WINDOW = """
var w = get_window()
var vp = get_viewport()
var root = get_tree().root
var out = {}
out["display_window_size"] = [DisplayServer.window_get_size().x, DisplayServer.window_get_size().y]
out["display_window_position"] = [DisplayServer.window_get_position().x, DisplayServer.window_get_position().y]
out["display_window_mode"] = DisplayServer.window_get_mode()
out["screen_size"] = [DisplayServer.screen_get_size().x, DisplayServer.screen_get_size().y]
out["window_size"] = [w.size.x, w.size.y]
out["window_position"] = [w.position.x, w.position.y]
out["content_scale_factor"] = w.content_scale_factor
out["content_scale_mode"] = w.content_scale_mode
out["content_scale_aspect"] = w.content_scale_aspect
out["viewport_size"] = [vp.get_visible_rect().size.x, vp.get_visible_rect().size.y]
out["root_viewport_size"] = [root.get_visible_rect().size.x, root.get_visible_rect().size.y]
out["viewport_texture_size"] = [vp.get_texture().get_size().x, vp.get_texture().get_size().y]
out["video_adapter"] = RenderingServer.get_video_adapter_name()
out["main_scene"] = str(ProjectSettings.get_setting("application/run/main_scene"))
out["declared_viewport"] = [ProjectSettings.get_setting("display/window/size/viewport_width"),
                            ProjectSettings.get_setting("display/window/size/viewport_height")]
out["declared_window_override"] = [ProjectSettings.get_setting("display/window/size/window_width_override"),
                                   ProjectSettings.get_setting("display/window/size/window_height_override")]
out["declared_stretch_mode"] = str(ProjectSettings.get_setting("display/window/stretch/mode"))
out["declared_stretch_aspect"] = str(ProjectSettings.get_setting("display/window/stretch/aspect"))
out["current_scene"] = str(get_tree().current_scene.get_path()) if get_tree().current_scene != null else "<null>"
out["drawn"] = Engine.get_frames_drawn()
return out
"""

def probe_state_source(cap=STATE_NODE_CAP):
    return """
var out = {}
var nodes = {}
var stack = [get_tree().root]
var n_nodes = 0
while stack.size() > 0 and n_nodes < %d:
    var n = stack.pop_back()
    n_nodes += 1
    # the module's own server node is a plain Node: it has no `visible` and no
    # game state, and walking into it is what made the first draft of this probe
    # fail with "Invalid access to property or key 'visible' on MCPServer"
    if str(n.name) == "MCPServer":
        continue
    var p = str(n.get_path())
    var e = {}
    e["c"] = n.get_class()
    e["name"] = str(n.name)
    if n is CanvasItem:
        e["vis"] = n.visible
    if n is Node2D:
        e["pos"] = [float(n.position.x), float(n.position.y), float(n.rotation)]
    elif n is Control:
        e["pos"] = [float(n.position.x), float(n.position.y), float(n.size.x), float(n.size.y)]
    if n is Label:
        e["text"] = str(n.text)
    var sp = n.get_script()
    if sp != null:
        e["script"] = str(sp.resource_path)
        for pr in n.get_property_list():
            if (pr["usage"] & 4096) != 0:
                var nm = str(pr["name"])
                var v = n.get(nm)
                var t = typeof(v)
                if t == TYPE_INT or t == TYPE_FLOAT or t == TYPE_BOOL or t == TYPE_STRING:
                    e[nm] = v
                elif t == TYPE_VECTOR2 or t == TYPE_VECTOR2I:
                    e[nm] = [float(v.x), float(v.y)]
    nodes[p] = e
    for ch in n.get_children():
        stack.push_back(ch)
out["nodes"] = nodes
out["node_count"] = n_nodes
out["drawn"] = Engine.get_frames_drawn()
out["processed"] = Engine.get_process_frames()
out["physics"] = Engine.get_physics_frames()
out["fps"] = Engine.get_frames_per_second()
out["ms"] = Time.get_ticks_msec()
out["window_size"] = [DisplayServer.window_get_size().x, DisplayServer.window_get_size().y]
return out
""" % cap


def probe_required_ui_source(paths):
    """TASK-130 P7: read the DECLARED required UI nodes out of the running game's tree.

    Machine-only: it resolves each declared node path inside the game process and reports
    what the engine itself says about it -- `exists`, its class, whether it is visible IN
    THE TREE (not just its own `visible` flag), its modulate alpha, its global rect and
    whether any ancestor has been hidden.  Nothing here asks a model; the verdict is a
    comparison against the declaration in `tools/playability_controls.json`.

    `paths` is a list of node paths from `/root` (e.g. `/root/Main/Hud`).  JSON string
    arrays are valid GDScript array literals, so the paths are carried through verbatim.
    """
    return """
var out = {"items": {}, "viewport": [], "root": str(get_tree().root.get_path())}
var vr = get_viewport().get_visible_rect()
out["viewport"] = [float(vr.position.x), float(vr.position.y),
                   float(vr.size.x), float(vr.size.y)]
var wanted = %s
for p in wanted:
    var n = get_node_or_null(NodePath(p))
    var e = {"path": p, "exists": false}
    if n != null:
        e["exists"] = true
        e["name"] = str(n.name)
        e["class"] = n.get_class()
        e["is_canvas_item"] = n is CanvasItem
        e["is_control"] = n is Control
        e["is_label"] = n is Label
        e["visible"] = n.visible if n is CanvasItem else true
        e["visible_in_tree"] = n.is_visible_in_tree() if n is CanvasItem else true
        e["modulate_a"] = float(n.modulate.a) if n is CanvasItem else 1.0
        e["text"] = str(n.text) if n is Label else null
        e["node_path"] = str(n.get_path())
        if n is Control:
            var r = n.get_global_rect()
            e["global_rect"] = [float(r.position.x), float(r.position.y),
                                float(r.size.x), float(r.size.y)]
            e["size"] = [float(n.size.x), float(n.size.y)]
            e["anchor"] = [float(n.anchor_left), float(n.anchor_top),
                           float(n.anchor_right), float(n.anchor_bottom)]
        var hidden_by = []
        var par = n.get_parent()
        while par != null:
            if par is CanvasItem and not par.visible:
                hidden_by.append(str(par.get_path()))
            par = par.get_parent()
        e["hidden_by_ancestors"] = hidden_by
    out["items"][p] = e
return out
""" % json.dumps(list(paths or []), ensure_ascii=False)


def probe_key_event(keycode, pressed, channel="viewport_push_input"):
    if channel == "parse_input_event":
        send = "Input.parse_input_event(ev)"
    else:
        send = "get_viewport().push_input(ev)"
    return """
var ev = InputEventKey.new()
ev.keycode = %d
ev.pressed = %s
ev.echo = false
%s
return {"sent": %d, "pressed": %s, "channel": "%s"}
""" % (int(keycode), "true" if pressed else "false", send,
       int(keycode), "true" if pressed else "false", channel)


def probe_action(action, pressed, strength=1.0):
    return """
var has = InputMap.has_action("%s")
if not has:
    return {"action": "%s", "has_action": false, "pressed": %s}
if %s:
    Input.action_press("%s", %.2f)
else:
    Input.action_release("%s")
return {"action": "%s", "has_action": true, "pressed": %s,
        "strength": Input.get_action_strength("%s")}
""" % (action, action, "true" if pressed else "false",
       "true" if pressed else "false", action, strength, action,
       action, "true" if pressed else "false", action)


def probe_action_state(action):
    return """
if not InputMap.has_action("%s"):
    return {"action": "%s", "has_action": false}
return {"action": "%s", "has_action": true,
        "pressed": Input.is_action_pressed("%s"),
        "strength": Input.get_action_strength("%s")}
""" % (action, action, action, action, action)


# ---------------------------------------------------------------------------
# process + window management (psutil for the tree, ctypes for the windows)
# ---------------------------------------------------------------------------
def port_in_use(port):
    import socket
    s = socket.socket()
    try:
        s.settimeout(0.4)
        return s.connect_ex(("127.0.0.1", port)) == 0
    finally:
        s.close()


def enumerate_windows():
    """Every visible top-level window on the desktop: pid, class, title, rect."""
    import ctypes
    from ctypes import wintypes
    user32 = ctypes.windll.user32
    out = []

    WNDENUMPROC = ctypes.WINFUNCTYPE(wintypes.BOOL, wintypes.HWND, wintypes.LPARAM)

    def cb(hwnd, _lparam):
        if not user32.IsWindowVisible(hwnd):
            return True
        pid = wintypes.DWORD()
        user32.GetWindowThreadProcessId(hwnd, ctypes.byref(pid))
        cls = ctypes.create_unicode_buffer(256)
        user32.GetClassNameW(hwnd, cls, 256)
        ln = user32.GetWindowTextLengthW(hwnd)
        title = ctypes.create_unicode_buffer(ln + 2)
        user32.GetWindowTextW(hwnd, title, ln + 2)
        rect = wintypes.RECT()
        user32.GetWindowRect(hwnd, ctypes.byref(rect))
        out.append({"hwnd": int(hwnd), "pid": int(pid.value), "class": cls.value,
                    "title": title.value,
                    "rect": [rect.left, rect.top,
                             rect.right - rect.left, rect.bottom - rect.top]})
        return True

    user32.EnumWindows(WNDENUMPROC(cb), 0)
    return out


def process_tree(cmd_pid):
    import psutil
    try:
        p = psutil.Process(cmd_pid)
    except Exception:  # noqa: BLE001
        return []
    procs = [p]
    try:
        procs += p.children(recursive=True)
    except Exception:  # noqa: BLE001
        pass
    out = []
    for q in procs:
        try:
            out.append({"pid": q.pid, "name": q.name(),
                        "exe": q.exe(), "cmdline": " ".join(q.cmdline() or [])})
        except Exception:  # noqa: BLE001
            out.append({"pid": q.pid, "name": "?", "exe": "", "cmdline": ""})
    return out


def tree_pids_for_port(port):
    """Every live process whose command line carries this run's unique port.

    The observed failure that made this necessary: after a harness exception the
    cmd -> .console.exe -> engine chain survived `taskkill /T` ("the operation
    attempted is not supported" on a detached tree) and held both the port and
    `engine-game.stderr.txt`, so the *next* run could not even clean its output
    directory.  The port is unique to one run, so it is an exact, safe selector.
    """
    import psutil
    needle = "--mcp-port=%d" % port
    found = []
    for p in psutil.process_iter(["pid", "name", "cmdline"]):
        try:
            cl = " ".join(p.info.get("cmdline") or [])
        except Exception:  # noqa: BLE001
            continue
        if needle in cl:
            found.append({"pid": p.info["pid"], "name": p.info.get("name"), "cmdline": cl})
    return found


def kill_what_holds(port, wait=8.0):
    """Kill everything holding `port`.  Returns the evidence, not a booleans-only."""
    import psutil
    killed = []
    for attempt in range(3):
        holders = tree_pids_for_port(port)
        if not holders:
            break
        for h in holders:
            try:
                subprocess.run(["cmd.exe", "/c", "taskkill /PID %d /T /F" % h["pid"]],
                               stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
            except Exception:  # noqa: BLE001
                pass
            try:
                psutil.Process(h["pid"]).kill()
            except Exception:  # noqa: BLE001
                pass
            killed.append(h)
        t0 = time.time()
        while time.time() - t0 < wait / 3.0:
            if not tree_pids_for_port(port):
                break
            time.sleep(0.3)
    return {"killed": killed, "still_holding": tree_pids_for_port(port)}


class GameProcess(object):
    def __init__(self, game, port, outdir):
        self.game = game
        self.port = port
        self.outdir = outdir
        self.proc = None
        self.cmd_file = None
        self.launched = None
        self.stdout = os.path.join(outdir, "engine-game.stdout.txt")
        self.stderr = os.path.join(outdir, "engine-game.stderr.txt")
        self.cmdline = ""
        self._handles = []

    def start(self, ready_timeout=240):
        if EXE_ROOT:
            # TASK-117: judge the shipped executable.  No `--path`: the exported exe
            # finds its own sidecar `.pck` next to itself, which is the thing under
            # test (TASK-115 §C③ measured that it really does read the sidecar).
            game_dir = os.path.join(EXE_ROOT, self.game)
            exe = os.path.join(game_dir, self.game + ".exe")
            self.launched = exe
            self.cmdline = ('"%s" --mcp-port=%d' % (exe, self.port))
            cwd = game_dir
        else:
            project = project_dir(self.game)
            self.launched = ENGINE
            self.cmdline = ('"%s" --path "%s" --mcp-port=%d' % (ENGINE, project, self.port))
            cwd = ENGINE_CWD
        self.cmd_file = os.path.join(self.outdir, "run-game.cmd")
        batch = ["@echo off", "cd /d \"%s\"" % cwd, self.cmdline,
                 "echo GAME_EXIT=%ERRORLEVEL%"]
        with io.open(self.cmd_file, "w", encoding="ascii", newline="\r\n") as fh:
            fh.write("\n".join(batch) + "\n")
        fo = open(self.stdout, "wb")
        fe = open(self.stderr, "wb")
        self._handles = [fo, fe]
        # iron rule 3: cmd.exe launches it; python owns the two handles (no shell
        # redirection), exactly like Start-Process -RedirectStandardOutput does.
        # CREATE_NO_WINDOW, not DETACHED_PROCESS: a detached tree could not be
        # killed by taskkill /T (see tree_pids_for_port).
        self.proc = subprocess.Popen(["cmd.exe", "/c", self.cmd_file],
                                     cwd=cwd, stdout=fo, stderr=fe,
                                     stdin=subprocess.DEVNULL,
                                     creationflags=0x08000000)
        t0 = time.time()
        while time.time() - t0 < ready_timeout:
            if port_in_use(self.port):
                return True, round(time.time() - t0, 1)
            if self.proc.poll() is not None:
                return False, round(time.time() - t0, 1)
            time.sleep(0.5)
        return False, round(time.time() - t0, 1)

    def alive(self):
        return self.proc is not None and self.proc.poll() is None

    def tree_pids(self):
        return [p["pid"] for p in process_tree(self.proc.pid)] if self.proc else []

    def stop(self):
        """Bounded, tree-wide kill: a modal dialog must never hang the sweep."""
        if self.proc is None:
            return {"killed": False, "reason": "not started"}
        pids = self.tree_pids()
        code = None
        if pids:
            cmd = "taskkill " + " ".join("/PID %d /T /F" % p for p in pids)
            r = subprocess.run(["cmd.exe", "/c", cmd], stdout=subprocess.PIPE,
                               stderr=subprocess.STDOUT)
            code = r.returncode
        try:
            self.proc.wait(timeout=15)
        except Exception:  # noqa: BLE001
            try:
                self.proc.kill()
            except Exception:  # noqa: BLE001
                pass
        sweep = kill_what_holds(self.port)
        for fh in self._handles:
            try:
                fh.close()
            except Exception:  # noqa: BLE001
                pass
        return {"killed": True, "pids": pids, "taskkill_exit": code,
                "port_sweep": sweep}


# ---------------------------------------------------------------------------
# frame analysis (P1)
# ---------------------------------------------------------------------------
def analyse_frame(path):
    img = Image.open(path).convert("RGB")
    a = np.asarray(img).astype(np.int16)
    h, w = a.shape[0], a.shape[1]
    flat = a.reshape(-1, 3)
    # the modal exact colour, computed on a 4-bit-quantised histogram so a
    # dithered background does not hide itself
    q = (flat >> 4)
    key = (q[:, 0].astype(np.int32) << 8) | (q[:, 1].astype(np.int32) << 4) | q[:, 2].astype(np.int32)
    vals, counts = np.unique(key, return_counts=True)
    bg_key = int(vals[int(np.argmax(counts))])
    bg_q = np.array([(bg_key >> 8) & 0xF, (bg_key >> 4) & 0xF, bg_key & 0xF], dtype=np.int16)
    bg = bg_q * 16 + 8
    diff = np.abs(a - bg.reshape(1, 1, 3)).max(axis=2)
    mask = diff > PIXEL_DELTA
    content_pixels = int(mask.sum())
    total = int(w * h)
    res = {"file": os.path.basename(path), "width": w, "height": h,
           "total_pixels": total, "background_rgb": [int(x) for x in bg],
           "content_pixels": content_pixels,
           "content_fraction": round(content_pixels / float(total), 6)}
    if content_pixels:
        ys, xs = np.nonzero(mask)
        x0, x1, y0, y1 = int(xs.min()), int(xs.max()), int(ys.min()), int(ys.max())
        bbox = [x0, y0, x1 - x0 + 1, y1 - y0 + 1]
        res["bbox"] = bbox
        res["bbox_coverage"] = round((bbox[2] * bbox[3]) / float(total), 6)
        res["bbox_window_coverage"] = [round(bbox[2] / float(w), 4),
                                       round(bbox[3] / float(h), 4)]
    else:
        res["bbox"] = [0, 0, 0, 0]
        res["bbox_coverage"] = 0.0
        res["bbox_window_coverage"] = [0.0, 0.0]
    res["sha256"] = sha256_file(path)
    return res


def content_bbox_crop(src, dst, margin=0, pad=0, min_side=0):
    """TASK-130 B: crop a frame to its CONTENT bounding box, with the rule written down.

    The rule is the one P1 already uses to decide what "content" is -- no new constant, so
    a frame's crop and its P1 metrics cannot disagree:

      1. the background colour is the frame's modal colour, computed on a 4-bit-quantised
         histogram (`analyse_frame`), so a dithered/anti-aliased background still finds
         itself;
      2. a pixel is content when it differs from that colour by more than `PIXEL_DELTA`
         (16) in ANY channel;
      3. the box is the tight bounding box of the content pixels;
      4. it is then padded by `pad` px and kept only where the remaining box is at least
         `min_side` px on each side (a degenerate box is not a useful crop);
      5. `margin` first ignores a border band of that many pixels (it is the "the window
         frame / the editor gutter is content too" escape hatch; 0 by default);
      6. a frame with NO content pixels is returned as the whole frame, and that is
         recorded as `flat: true` instead of silently producing a 0x0 crop.

    Returns the crop description (source/dest size, box, sha256 of the result), so the
    input a model saw can be reconstructed from the artifact instead of from this code.
    """
    img = Image.open(src).convert("RGB")
    a = np.asarray(img).astype(np.int16)
    h, w = a.shape[0], a.shape[1]
    flat = a.reshape(-1, 3)
    q = (flat >> 4)
    key = ((q[:, 0].astype(np.int32) << 8) | (q[:, 1].astype(np.int32) << 4)
           | q[:, 2].astype(np.int32))
    vals, counts = np.unique(key, return_counts=True)
    bg_key = int(vals[int(np.argmax(counts))])
    bg_q = np.array([(bg_key >> 8) & 0xF, (bg_key >> 4) & 0xF, bg_key & 0xF], dtype=np.int16)
    bg = bg_q * 16 + 8
    diff = np.abs(a - bg.reshape(1, 1, 3)).max(axis=2)
    mask = diff > PIXEL_DELTA
    if margin > 0 and 2 * margin < min(h, w):
        keep = np.zeros_like(mask)
        keep[margin:h - margin, margin:w - margin] = True
        mask = mask & keep
    info = {"rule": "modal-colour (4-bit quantised) + PIXEL_DELTA>%d content mask, "
                    "tight bbox, then pad=%d margin=%d min_side=%d"
                    % (PIXEL_DELTA, pad, margin, min_side),
            "source": os.path.abspath(src), "source_size": [w, h],
            "background_rgb": [int(v) for v in bg],
            "margin": margin, "pad": pad, "min_side": min_side}
    if not mask.any():
        info.update({"flat": True, "box": [0, 0, w, h], "dest": os.path.abspath(dst),
                     "dest_size": [w, h], "cropped": False,
                     "why": "no content pixel at all: the whole frame is its own "
                            "background, so there is nothing to crop to"})
        if os.path.abspath(src) != os.path.abspath(dst):
            shutil.copyfile(src, dst)
        info["sha256"] = sha256_file(dst)
        return info
    ys, xs = np.nonzero(mask)
    x0, x1 = int(xs.min()), int(xs.max()) + 1
    y0, y1 = int(ys.min()), int(ys.max()) + 1
    x0 = max(0, x0 - pad)
    y0 = max(0, y0 - pad)
    x1 = min(w, x1 + pad)
    y1 = min(h, y1 + pad)
    degenerate = (x1 - x0) < max(1, min_side) or (y1 - y0) < max(1, min_side)
    if degenerate:
        info.update({"degenerate": True, "box": [0, 0, w, h],
                     "why": "the content box (%dx%d) is smaller than min_side=%d; the "
                            "whole frame is kept so the crop is not a hole"
                            % (x1 - x0, y1 - y0, min_side),
                     "dest": os.path.abspath(dst), "dest_size": [w, h], "cropped": False})
        if os.path.abspath(src) != os.path.abspath(dst):
            shutil.copyfile(src, dst)
        info["sha256"] = sha256_file(dst)
        return info
    cropped = img.crop((x0, y0, x1, y1))
    cropped.save(dst, format="PNG")
    info.update({"flat": False, "box": [x0, y0, x1 - x0, y1 - y0],
                 "dest": os.path.abspath(dst), "dest_size": [x1 - x0, y1 - y0],
                 "cropped": True,
                 "box_fraction_of_source": [round((x1 - x0) / float(w), 4),
                                            round((y1 - y0) / float(h), 4)],
                 "area_fraction_of_source": round(((x1 - x0) * (y1 - y0)) / float(w * h), 4)})
    info["sha256"] = sha256_file(dst)
    return info


def png_changed(a_path, b_path):
    a = np.asarray(Image.open(a_path).convert("RGB")).astype(np.int16)
    b = np.asarray(Image.open(b_path).convert("RGB")).astype(np.int16)
    if a.shape != b.shape:
        return {"comparable": False, "changed_pixels": -1,
                "why": "size mismatch %s vs %s" % (a.shape, b.shape)}
    d = np.abs(a - b).max(axis=2)
    return {"comparable": True,
            "changed_pixels": int((d > PIXEL_DELTA).sum()),
            "any_difference_pixels": int((d > 0).sum()),
            "max_channel_delta": int(d.max())}


# ---------------------------------------------------------------------------
# filmstrip (item A.2)
# ---------------------------------------------------------------------------
def build_filmstrip(frame_records, out_path, title, note="", thumb_w=210,
                    cols=5, label_h=34, header_h=46):
    if not frame_records:
        return None
    cells = []
    for fr in frame_records:
        if not fr.get("path") or not os.path.isfile(fr["path"]):
            continue
        im = Image.open(fr["path"]).convert("RGB")
        sc = thumb_w / float(im.width)
        im = im.resize((thumb_w, max(1, int(round(im.height * sc)))), Image.LANCZOS)
        cells.append((fr, im))
    cw = thumb_w
    ch = max(c[1].height for c in cells)
    rows = int(np.ceil(len(cells) / float(cols)))
    W = cols * (cw + 6) + 6
    H = header_h + rows * (ch + label_h + 6) + 6
    canvas = Image.new("RGB", (W, H), (18, 18, 22))
    dr = ImageDraw.Draw(canvas)
    dr.text((8, 6), title, fill=(255, 255, 255))
    if note:
        dr.text((8, 24), note, fill=(180, 200, 220))
    for i, (fr, im) in enumerate(cells):
        r, c = divmod(i, cols)
        x = 6 + c * (cw + 6)
        y = header_h + r * (ch + label_h + 6)
        canvas.paste(im, (x, y))
        lab1 = "#%02d %s" % (fr.get("index", i), fr.get("label", ""))
        lab2 = "%dx%d win=%s px=%s" % (
            fr.get("width", 0), fr.get("height", 0),
            "x".join(str(v) for v in (fr.get("window") or [])),
            ("%.2f%%" % (100.0 * fr["content_fraction"])) if fr.get("content_fraction") is not None else "?")
        lab3 = "bg=%s bbox=%s" % (fr.get("background_rgb", "?"), fr.get("bbox", "?"))
        lab4 = "changed_vs_prev=%s" % fr.get("changed_pixels_vs_prev", "-")
        dr.text((x + 2, y + im.height + 2), lab1, fill=(255, 255, 160))
        dr.text((x + 2, y + im.height + 12), lab2, fill=(200, 220, 255))
        dr.text((x + 2, y + im.height + 20), lab4, fill=(200, 255, 200))
        dr.text((x + 2, y + im.height + 28), lab3, fill=(200, 200, 200))
    canvas.save(out_path)
    return out_path


# ---------------------------------------------------------------------------
# the per-game gate run
# ---------------------------------------------------------------------------
def state_delta(a, b):
    """Which node properties moved between two samples.

    Two kinds of noise are removed *by rule*, because both of them produced a
    phantom "the action responded" in the first version of this gate:
      * the module's own GDScript executor mounts itself as a transient child of
        the current scene for the duration of one call, so every sample sees a
        different anonymous `@Node@N` appear and disappear;
      * `Engine.get_frames_drawn()` and friends always advance while the game is
        alive, which says nothing about a *player's* input.
    """
    def ignorable(path, entry):
        if "@Node@" in path:
            return True
        script = str((entry or {}).get("script") or "")
        if script.startswith("gdscript://"):
            return True
        return False

    changed = []
    na = (a or {}).get("nodes") or {}
    nb = (b or {}).get("nodes") or {}
    for path, ea in na.items():
        if ignorable(path, ea):
            continue
        eb = nb.get(path)
        if eb is None:
            changed.append({"key": path, "why": "node disappeared"})
            continue
        for k, v in ea.items():
            if k in ("script", "c"):
                continue
            if eb.get(k, "<missing>") != v:
                changed.append({"key": "%s.%s" % (path, k), "from": v, "to": eb.get(k)})
    for path, eb in nb.items():
        if path not in na and not ignorable(path, eb):
            changed.append({"key": path, "why": "node appeared"})
    return changed


def run_required_ui_probe(paths, gd):
    """TASK-130 P7: run the required-UI probe inside the game process.

    `gd(code, at)` is `run_gate`'s GDScript caller, so the call is recorded in the gate's
    own `errors` list exactly like every other probe.  The answer is returned verbatim
    (per-node class/visibility/rect/text + the viewport rect); the judging happens in
    `verdict_p7`, never here.
    """
    out = {"source": "running_game_execute_gdscript (live tree inside the game process)",
           "probe": "probe_required_ui_source", "declared_paths": list(paths or []),
           "items": {}, "viewport": None, "root": None, "error": None}
    if not paths:
        return out
    res = gd(probe_required_ui_source(paths), "p7_required_ui")
    if not isinstance(res, dict):
        out["error"] = "the required-UI probe returned %r, not a dictionary" % (res,)
        return out
    out["items"] = res.get("items") or {}
    out["viewport"] = res.get("viewport")
    out["root"] = res.get("root")
    return out


class OnlyP7Done(Exception):
    """TASK-130: raised by `run_gate` when `--only-p7` has collected what it came for.

    It is NOT an error path: it unwinds out of the `try` so the `finally` still stops the
    game process and the tail still writes `gate.json` / `frames.json`, exactly as a full
    run would.  `--only-p7` exists because the declarative required-UI check needs a real
    running game but none of P2..P6, so verifying the declaration across all 20 games does
    not have to pay for a full sweep.
    """


def run_gate(game, args):
    t_start = time.time()
    # iron rule 4, first thing: whatever this run is about to use the port for,
    # nothing from an earlier run may still be holding it.
    leftover = kill_what_holds(args.port)
    if leftover["killed"]:
        log("    cleaned up %d leftover process(es) still holding port %d: %s"
            % (len(leftover["killed"]), args.port,
               ", ".join(str(k["pid"]) for k in leftover["killed"])))
    if leftover["still_holding"]:
        raise RuntimeError("port %d is still held by %s (iron rule 4: one unique port, "
                           "checked before use)"
                           % (args.port, [k["pid"] for k in leftover["still_holding"]]))
    outdir = os.path.join(RUNS, game)
    if os.path.isdir(outdir) and args.fresh:
        shutil.rmtree(assert_inside(outdir))
    frames_dir = os.path.join(outdir, "frames")
    states_dir = os.path.join(outdir, "states")
    calls_dir = os.path.join(outdir, "calls")
    for d in (frames_dir, states_dir, calls_dir):
        if not os.path.isdir(d):
            os.makedirs(d)

    proj = parse_project(game)
    controls = load_controls()
    agent_thresholds = load_agent_thresholds()
    playjev_thresholds = load_playjev_thresholds()
    # TASK-131 X13: the per-frame marker declaration (Paused / clock / Ticks / Score ...).
    # Read here so `capture` -- defined below and called for every frame -- can stamp each
    # frame with the marker values of the state it was taken with.
    MARKERS = [marker_declaration(controls, game)]
    # TASK-129 D-B: every state the game was sampled in, in sampling order.  The agent
    # step below picks >= 3 of these that are HASH-DIFFERENT, so "3 calls" really is
    # "3 independent observations" (TASK-128 measured that it was not: the same s_end was
    # handed to all three calls and the answers came back bit-identical).
    state_pool = []
    write_json(os.path.join(outdir, "project.json"), proj)
    try:
        audit = audit_one(game)
    except Exception as e:  # noqa: BLE001
        audit = {"error": "%s: %s" % (type(e).__name__, e)}
    write_json(os.path.join(outdir, "static-audit.json"), audit)
    log("--- %s : declared viewport %s, %d declared actions, README keys %s" % (
        game, proj["declared_viewport"], len(proj["actions_declared"]), proj["readme_keys"]))

    port = args.port
    gp = GameProcess(game, port, outdir)

    # TASK-117: what exactly is under test.  For the exported sweep this is the
    # shipped exe (with its sidecar .pck and data dir), hashed here so the verdict
    # can be tied to one file rather than to "the export".
    target = {"mode": "exported-exe" if EXE_ROOT else "project",
              "engine": ENGINE, "exe_root": EXE_ROOT,
              "project_dir": project_dir(game),
              "project_dir_is_exercise": project_dir(game).startswith(EXERCISES)}
    if EXE_ROOT:
        exe_path = os.path.join(EXE_ROOT, game, game + ".exe")
        pck_path = os.path.join(EXE_ROOT, game, game + ".pck")
        data_dir = os.path.join(EXE_ROOT, game, "data_%s_windows_x86_64" % game)
        target["exe"] = {
            "path": exe_path,
            "exists": os.path.isfile(exe_path),
            "bytes": os.path.getsize(exe_path) if os.path.isfile(exe_path) else None,
            "sha256": sha256_file(exe_path) if os.path.isfile(exe_path) else None}
        target["pck"] = {
            "path": pck_path,
            "exists": os.path.isfile(pck_path),
            "bytes": os.path.getsize(pck_path) if os.path.isfile(pck_path) else None,
            "sha256": sha256_file(pck_path) if os.path.isfile(pck_path) else None}
        target["data_dir"] = {
            "path": data_dir,
            "exists": os.path.isdir(data_dir),
            "files": (sum(len(f) for _r, _d, f in os.walk(data_dir))
                      if os.path.isdir(data_dir) else 0)}

    gate = {"game": game, "started": time.strftime("%Y-%m-%d %H:%M:%S"),
            "engine": ENGINE, "cmdline": gp.cmdline, "port": port, "target": target,
            "project": proj, "static_audit": audit, "criteria": {}, "frames": [],
            "actions_tested": [], "errors": [], "notes": []}
    frames = []
    frame_index = [0]
    window_info = {"os_window": None, "root_viewport": None,
                   "declared": proj["declared_viewport"], "conforms": None}

    def record_state(label, value, extra=None):
        rec = {"label": label, "ms": value.get("ms") if isinstance(value, dict) else None,
               "drawn": value.get("drawn") if isinstance(value, dict) else None,
               "node_count": value.get("node_count") if isinstance(value, dict) else None}
        if extra:
            rec.update(extra)
        return rec

    def capture(label, mcp, state_after=None, note=""):
        r = mcp.call_tool("running_game_capture_screenshot", {})
        rec = {"label": label, "note": note, "ok": bool(r.get("ok"))}
        if not r.get("ok"):
            rec["error"] = r.get("error")
            gate["frames"].append(rec)
            return None
        v = r["value"]
        b64 = v.get("image_base64")
        if not b64:
            rec["error"] = "no image_base64 in the answer"
            gate["frames"].append(rec)
            return None
        png = base64.b64decode(b64)
        frame_index[0] += 1
        fname = "%02d_%s.png" % (frame_index[0], label)
        fpath = os.path.join(frames_dir, fname)
        with open(fpath, "wb") as fh:
            fh.write(png)
        ana = analyse_frame(fpath)
        rec.update({"index": frame_index[0], "path": fpath, "report_width": v.get("width"),
                    "report_height": v.get("height"), "bytes": len(png),
                    "seconds": r.get("seconds"),
                    "window": window_info["os_window"],
                    "root_viewport": window_info["root_viewport"],
                    "declared_viewport": window_info["declared"],
                    "window_conforms_to_declared": window_info["conforms"]})
        rec.update(ana)
        prev = frames[-1] if frames else None
        if prev and prev.get("path"):
            ch = png_changed(prev["path"], fpath)
            rec["changed_pixels_vs_prev"] = ch.get("changed_pixels")
            rec["change_vs_prev"] = ch
        else:
            rec["changed_pixels_vs_prev"] = None
        if state_after is not None:
            rec["state_summary"] = record_state(label, state_after)
        # TASK-131 X13: EVERY frame carries the declared marker timeline (Paused, the
        # clock fields, Ticks, ...) of the state read that goes with it, so "was this
        # static frame legal?" can be answered from the artifact instead of argued about.
        # Read out of the state the caller already sampled; no extra call is made.
        if state_after is not None and isinstance(state_after, dict):
            rec["markers"] = marker_values(state_after, MARKERS[0])
        frames.append(rec)
        gate["frames"].append({k: v_ for k, v_ in rec.items() if k != "path"})
        gate["frames"][-1]["file"] = fname
        return rec

    def sample_state(label, mcp, save=True):
        r = mcp.call_tool("running_game_execute_gdscript",
                          {"code": probe_state_source()}, timeout=args.call_timeout)
        if not r.get("ok"):
            gate["errors"].append({"at": "state:" + label, "error": r.get("error"),
                                   "seconds": r.get("seconds")})
            return None
        val = r["value"].get("result")
        if not isinstance(val, dict):
            gate["errors"].append({"at": "state:" + label,
                                   "error": "unexpected result_type %s" % r["value"].get("result_type")})
            return None
        if save:
            write_json(os.path.join(states_dir, label + ".json"), val)
        state_pool.append({"label": label, "state": val})
        return val

    def gd(mcp, code, at):
        r = mcp.call_tool("running_game_execute_gdscript", {"code": code},
                          timeout=args.call_timeout)
        if not r.get("ok"):
            gate["errors"].append({"at": at, "error": r.get("error"), "seconds": r.get("seconds")})
            return None
        return r["value"].get("result")

    try:
        ok, secs = gp.start(args.ready_timeout)
        gate["startup"] = {"port_up": ok, "seconds": secs, "alive": gp.alive()}
        if not ok:
            gate["errors"].append({"at": "startup",
                                   "error": "the game's MCP endpoint never came up"})
            gate["criteria"] = {"P1": {"pass": False, "why": "no game process"},
                                "P2": {"pass": False, "why": "no game process"},
                                "P3": {"pass": False, "why": "no game process"},
                                "P4": {"pass": False, "why": "process never served"},
                                "P5": {"pass": False, "why": "no game process"},
                                "P6": {"pass": False, "why": "no game process"},
                                "P7": {"pass": False, "why": "no game process"}}
            return gate

        mcp = Mcp(port, calls_dir)
        t0 = time.time()
        tools = mcp.tools_list()
        gate["tools_list_count"] = len(tools)
        gate["tools_list_seconds"] = round(time.time() - t0, 2)
        log("    endpoint up in %ss; tools/list -> %d tools" % (secs, len(tools)))

        # let the first frames render, then ask the game about its own window
        time.sleep(args.settle)
        w = gd(mcp, PROBE_WINDOW, "window")
        gate["window"] = w
        if isinstance(w, dict):
            log("    window: OS %s  root-viewport %s  declared %s  drawn=%s" % (
                w.get("display_window_size"), w.get("root_viewport_size"),
                w.get("declared_viewport"), w.get("drawn")))
            # window-size conformance (item A.3)
            dsz = w.get("display_window_size") or [0, 0]
            dec = proj["declared_viewport"] or [0, 0]
            wov = proj["declared_window_override"] or [0, 0]
            expect = [wov[0] or dec[0], wov[1] or dec[1]]
            gate["window_conformance"] = {
                "os_window": dsz, "declared_viewport": dec, "window_override": wov,
                "expected_os_window": expect,
                "matches_declared": dsz == expect,
                "root_viewport": w.get("root_viewport_size"),
                "root_viewport_matches_declared": w.get("root_viewport_size") == dec,
            }
            if not gate["window_conformance"]["matches_declared"]:
                gate["notes"].append("OS window %s != declared %s" % (dsz, expect))
            window_info["os_window"] = dsz
            window_info["root_viewport"] = w.get("root_viewport_size")
            window_info["conforms"] = bool(gate["window_conformance"]["matches_declared"])

        # ---------------- P1 + P3a: autonomous frames ----------------
        s0 = sample_state("00_settle", mcp)
        f0 = capture("settle", mcp, s0, note="first frame after %ss" % args.settle)
        # TASK-131 X10/X13: what does the player see FIRST, and is the game already in a
        # declared terminal state at that moment?  The snake defect lives exactly here.
        liv = liveness_declaration(controls, game)
        gate["settle_liveness"] = {
            "declaration": liv,
            "markers": marker_values(s0, MARKERS[0]),
            "terminal_conditions_met": terminal_conditions_met(s0, liv),
            "declared": bool(liv),
        }
        if gate["settle_liveness"]["terminal_conditions_met"]:
            gate["notes"].append(
                "the game is ALREADY in a declared terminal state at the settle frame: %s"
                % json.dumps(gate["settle_liveness"]["terminal_conditions_met"],
                             ensure_ascii=False))
            log("    SETTLE LIVENESS: already terminal at settle: %s"
                % json.dumps(gate["settle_liveness"]["terminal_conditions_met"],
                             ensure_ascii=False))

        # ---------------- TASK-130 P7: the DECLARED required UI ----------------
        # Machine check, no model: the declaration in tools/playability_controls.json names
        # the nodes a player needs (HUD readout, board container, next-piece indicator,
        # the food a snake must see ...).  The probe reads those very nodes out of the live
        # tree and `verdict_p7` compares.  This is the criterion for the failure mode P1..P6
        # could not see: a game whose interface is gone but whose logic is fine.
        ui_decl, ui_items = required_ui_items(controls, game)
        gate["required_ui_declaration"] = {
            "declared": bool(ui_items),
            "what": ui_decl.get("what"),
            "rule": ui_decl.get("rule"),
            "items": [dict(i) for i in ui_items],
            "source": os.path.join(HERE, "playability_controls.json"),
            "key": "games.%s.required_ui" % game}
        gate["p7_probe"] = run_required_ui_probe(
            [i.get("node") for i in ui_items if i.get("node")],
            lambda code, at: gd(mcp, code, at))
        log("    P7 probe: %d declared item(s), %d node(s) resolved in the live tree"
            % (len(ui_items), sum(1 for v in (gate["p7_probe"].get("items") or {}).values()
                                  if v.get("exists"))))
        if getattr(args, "only_p7", False):
            gate["criteria"] = {"P7": verdict_p7(game, controls, gate["p7_probe"])}
            gate["criteria_scope"] = ("P7 only (--only-p7): the declarative required-UI "
                                      "check; P1..P6 were deliberately not run")
            record_model_player_criterion(gate, args, game)
            log("    P7 (only run): %s -- %s"
                % ("PASS" if gate["criteria"]["P7"]["pass"] else "FAIL",
                   gate["criteria"]["P7"]["why"]))
            raise OnlyP7Done()

        auto_states = []
        for i in range(1, args.auto_frames + 1):
            time.sleep(args.auto_gap)
            st = sample_state("%02d_auto" % i, mcp)
            fr = capture("auto%d" % i, mcp, st, note="no input, %ss apart" % args.auto_gap)
            auto_states.append(st)
        s1 = auto_states[-1] if auto_states else None

        # ---------------- P2 + P5: per declared action ----------------
        # Attribution design (the reason this is not just "before vs after"): a
        # game whose ball/car/snake is already moving changes state on its own, so
        # a naive before->after delta credits *every* action.  Each action is
        # therefore measured against its OWN immediately preceding, same-length,
        # no-input control window, and it only counts as "responds" when it beats
        # that control.  This is what makes the verdict attributable instead of
        # plausible.
        order = list(proj["actions_declared"])[:args.max_actions]
        # How long a key is held.  The default (--hold) is deliberately longer than one
        # repetition interval for most games, but a game whose keyboard path repeats while
        # held can turn 0.5 s into four hops -- and in Frogger four hops into the road is
        # four deaths, which ends the game *before* the next action is even tested.  A game
        # may therefore declare its own `hold_ms` in tools/playability_controls.json; that
        # is a property of the game's input design, so it belongs in the game's own entry.
        hold_for = float((controls.get(game) or {}).get("hold_ms", args.hold * 1000.0)) / 1000.0

        def run_channel(channel, ai, action, kc):
            """One injection channel for one action, measured against its own control window."""
            hold = hold_for
            # ---- control window: same length, no input ----
            pre_state = sample_state("a%02d_%s_%s_pre" % (ai, action, channel), mcp)
            pre_frame = capture("a%02d_%s_%s_pre" % (ai, action, channel), mcp,
                                pre_state, note="control start")
            time.sleep(hold)
            ctl_state = sample_state("a%02d_%s_%s_ctl" % (ai, action, channel), mcp)
            ctl_frame = capture("a%02d_%s_%s_ctl" % (ai, action, channel), mcp,
                                ctl_state, note="control end (no input)")
            ctl_delta = state_delta(pre_state, ctl_state)
            ctl_px = png_changed(pre_frame["path"], ctl_frame["path"]) \
                if (pre_frame and ctl_frame) else {"comparable": False}
            # ---- inject ----
            if channel in ("parse", "push_input"):
                if kc is None:
                    return {"ok": False, "why": "the action has no key event"}
                mode = "parse_input_event" if channel == "parse" else "viewport_push_input"
                sent = gd(mcp, probe_key_event(kc, True, mode),
                          "inject:%s:%s" % (channel, action))
            else:
                has = gd(mcp, probe_action_state(action), "action_state:" + action)
                if not (has or {}).get("has_action"):
                    return {"ok": False,
                            "why": "InputMap.has_action('%s') is false" % action}
                sent = gd(mcp, probe_action(action, True), "inject:action:" + action)
            time.sleep(hold)
            # RELEASE IMMEDIATELY, before the state/frame readback. This is not cosmetic: a
            # state probe plus a full-window capture costs roughly 0.5 s each, so releasing
            # *after* them held the key for ~7x the intended interval. Measured consequence in
            # Frogger: a 150 ms key that should be one hop became eight, eight hops into the
            # road became eight deaths, and the game was over before the next action was even
            # tested -- runs/playability/frogger/states/a02_frog_up_parse_act.json recorded
            # `lives=0 game over` out of a 0.15 s hold.
            if channel in ("parse", "push_input"):
                mode = "parse_input_event" if channel == "parse" else "viewport_push_input"
                gd(mcp, probe_key_event(kc, False, mode),
                   "release:%s:%s" % (channel, action))
            else:
                gd(mcp, probe_action(action, False), "release:action:" + action)
            act_state = sample_state("a%02d_%s_%s_act" % (ai, action, channel), mcp)
            act_frame = capture("a%02d_%s_%s_act" % (ai, action, channel), mcp,
                                act_state, note="%s held via %s" % (action, channel))
            act_delta = state_delta(ctl_state, act_state)
            act_px = png_changed(ctl_frame["path"], act_frame["path"]) \
                if (ctl_frame and act_frame) else {"comparable": False}
            frames_waited = None
            if isinstance(ctl_state, dict) and isinstance(act_state, dict):
                frames_waited = (act_state.get("drawn", 0) or 0) - \
                                (ctl_state.get("drawn", 0) or 0)
            # the action must beat its own control
            ctl_px_n = max(0, ctl_px.get("changed_pixels", 0) or 0)
            act_px_n = max(0, act_px.get("changed_pixels", 0) or 0)
            state_wins = len(act_delta) > len(ctl_delta)
            pixel_wins = act_px_n > max(int(ctl_px_n * 1.5), P3_MIN_CHANGED_PIXELS)
            changed = bool(state_wins or pixel_wins)
            time.sleep(args.settle_input)
            return {
                "ok": True, "sent": sent,
                "control": {"state_changes": ctl_delta[:20],
                            "state_change_count": len(ctl_delta), "pixels": ctl_px},
                "action": {"state_changes": act_delta[:60],
                           "state_change_count": len(act_delta), "pixels": act_px},
                "frames_waited": frames_waited,
                "state_beats_control": state_wins,
                "pixels_beat_control": pixel_wins,
                "changed": changed,
                "within_N_frames": bool(changed and frames_waited is not None
                                        and frames_waited <= P2_FRAMES),
            }

        for ai, action in enumerate(order):
            spec = proj["actions"][action]
            kc = next((c for c in spec["keycode"] if c), None)
            kname = keyname_of(kc) if kc else None
            entry = {"action": action, "keycodes": spec["keycode"], "key": kname,
                     "declared": True, "channels": {}}
            # The PRIMARY channel is the faithful one: `Input.parse_input_event(ev)` is
            # what the display server calls when a human presses the key -- it updates
            # the InputMap action state (input.cpp:1113-1124) *and* dispatches the event
            # to the viewport (input.cpp:1126-1130).  The two diagnostic channels each
            # reproduce only one half: `push_input` dispatches without touching action
            # state (viewport.cpp:3502-3566), `action_press` sets state without
            # dispatching.  They run only when the primary channel fails, so a healthy
            # game costs no extra frames and a broken one comes back with a diagnosis
            # rather than a bare verdict.
            entry["channels"]["parse"] = run_channel("parse", ai, action, kc)
            key_ok = bool(entry["channels"]["parse"].get("changed"))
            entry["responds_to_real_key"] = key_ok
            if not key_ok and kc is not None:
                for diag in ("push_input", "action"):
                    entry["channels"][diag] = run_channel(diag, ai, action, kc)
            push_ok = bool((entry["channels"].get("push_input") or {}).get("changed"))
            act_ok = bool((entry["channels"].get("action") or {}).get("changed"))
            entry["responds_to_push_input_only"] = push_ok and not key_ok
            entry["responds_to_action_state_only"] = act_ok and not key_ok
            entry["responds_to_action_state"] = act_ok
            entry["suspicious_mismatch"] = act_ok and not key_ok
            entry["responds"] = key_ok or push_ok or act_ok
            gate["actions_tested"].append(entry)
            log("    action %-18s key=%-6s real_key=%-5s push_input=%-5s action_state=%-5s %s" % (
                action, kname, key_ok, push_ok, act_ok,
                "SUSPICIOUS(action-only)" if entry["suspicious_mismatch"]
                else ("event-only" if entry["responds_to_push_input_only"] else "")))

        # ---------------- TASK-131 X13: action side effects ----------------
        # An action sequence must not leave the game in a MODE and then keep sampling
        # frames as if nothing had happened.  `snake` is the measured case: the gate's own
        # `snake_pause` turned `Paused` false->true and never turned it back, so every
        # frame after it was necessarily static (SnakeGame.cs:159 `if (GameOver || Paused)
        # return;`).  Each declaration in `games.<game>.mode_actions` names the marker, the
        # value that means "the mode is on", and the action that turns it off; the audit
        # either restores the mode (recording the readback) or records explicitly that the
        # game was left in it, so every later frame's marker stamp can be judged.
        MODES = mode_declarations(controls, game)
        after_actions = sample_state("zz_after_actions", mcp)
        side = {"declarations": MODES,
                "before": marker_values(s0, MARKERS[0]),
                "after": marker_values(after_actions, MARKERS[0]),
                "left_in_mode": [], "restored": [], "not_restorable": []}
        for m in MODES:
            field = m.get("marker")
            armed = m.get("armed_value")
            mv = marker_values(after_actions, MARKERS[0])
            if not field or mv.get(field) != armed \
                    or marker_values(s0, MARKERS[0]).get(field) == armed:
                continue
            entry = {"action": m.get("action"), "marker": field,
                     "value_after_the_round": mv.get(field), "effect": m.get("effect"),
                     "restore_declaration": m.get("restore")}
            rest = m.get("restore") or {}
            r_action = rest.get("action")
            if r_action:
                rkc = next((c for c in (proj["actions"].get(r_action) or {}).get(
                    "keycode", []) if c), None)
                if rkc is not None:
                    gd(mcp, probe_key_event(rkc, True, "parse_input_event"),
                       "restore-press:" + r_action)
                    time.sleep(0.15)
                    gd(mcp, probe_key_event(rkc, False, "parse_input_event"),
                       "restore-release:" + r_action)
                    time.sleep(args.settle_input)
                    after_actions = sample_state("zz_after_restore", mcp)
                    back = marker_values(after_actions, MARKERS[0]).get(field)
                    entry["restored_to"] = back
                    entry["restored"] = back != armed
                    (side["restored"] if entry["restored"]
                     else side["not_restorable"]).append(entry)
                else:
                    entry["restored"] = False
                    entry["why"] = ("the declared restore action %r has no key code in the "
                                    "InputMap" % r_action)
                    side["not_restorable"].append(entry)
            else:
                entry["restored"] = False
                entry["why"] = ("no restore action is declared for %r: the game is left in "
                                "this mode and every later frame carries the marker"
                                % m.get("action"))
                side["not_restorable"].append(entry)
            side["left_in_mode"].append(entry)
        gate["action_side_effects"] = side
        if MODES:
            log("    action side effects: left_in_mode=%s restored=%s not_restorable=%s"
                % ([e["action"] for e in side["left_in_mode"]],
                   [e["action"] for e in side["restored"]],
                   [e["action"] for e in side["not_restorable"]]))
        s_after_actions = after_actions

        # ---------------- P3b: does anything keep moving after input ----------------
        post = []
        for i in range(1, args.post_frames + 1):
            time.sleep(args.auto_gap)
            st = sample_state("%02d_post" % i, mcp)
            fr = capture("post%d" % i, mcp, st, note="after the input round")
            post.append(st)
        s_end = post[-1] if post else None

        # ---------------- process / window health (P4) ----------------
        alive = gp.alive()
        tree = process_tree(gp.proc.pid)
        windows = enumerate_windows()
        tree_pids = set(p["pid"] for p in tree)
        own_windows = [w_ for w_ in windows if w_["pid"] in tree_pids]
        game_windows = [w_ for w_ in own_windows
                        if ("godot" in w_["class"].lower() or "godot" in w_["title"].lower()
                            or w_["rect"][2] > 200)]
        dialogs = [w_ for w_ in own_windows if w_["class"] in ("#32770", "Popup",
                                                              "TooltipWindowClass")]
        gate["p4"] = {"alive_at_end": alive, "process_tree": tree,
                      "own_visible_windows": own_windows,
                      "modal_candidates": dialogs,
                      "mcp_errors": [e for e in gate["errors"]]}
        log("    process alive=%s tree=%d visible windows=%d dialogs=%d" % (
            alive, len(tree), len(own_windows), len(dialogs)))

        # ---------------- verdicts ----------------
        gate["criteria"] = verdicts(game, gate, proj, frames, s0, s1, s_end, controls)

        # ---------------- TASK-132: the MODEL-PLAYER criterion ----------------
        record_model_player_criterion(gate, args, game)

        # ---------------- agent in the loop (item D) ----------------
        goal = {"game": game, "objective": args.objective or
                "make the game visibly respond to its own documented controls",
                "actions": {k: v["keys"] for k, v in proj["actions"].items()},
                "keys": proj["readme_keys"]}
        if args.agent and args.agent != "none":
            agent = build_agent(args.agent, game, goal["objective"],
                                {"plan": None, "hold_ms": int(args.hold * 1000),
                                 "decision_path": getattr(args, "decision_path", "") or "",
                                 "base_url": (getattr(args, "base_url", "") or
                                              os.environ.get("PLAYTEST_BASE_URL", "")),
                                 "max_state_retries": getattr(args, "max_state_retries", 2),
                                 "thresholds": agent_thresholds})
            acts = []
            # ---- TASK-129 D-B: >= 3 INDEPENDENT state observations ----------------
            # TASK-128 handed the SAME `s_end` to all three calls and measured that the
            # three answers came back bit-identical, i.e. every game had exactly ONE
            # independent model observation.  Here the pool of states the gate already
            # sampled (before any input / during the run / after the input round) is
            # deduplicated by the sha256 of the exact text handed over, and up to
            # --agent-state-samples distinct ones are sent, one per call.  If the game
            # cannot offer that many distinct states, the sample size is reported as 1
            # (D-B: "otherwise count the sample as 1 and say so"), never as 3.
            wanted = max(1, int(getattr(args, "agent_state_samples", 3)))
            budget = getattr(args, "agent_state_budget", 0)
            picked = pick_state_samples(
                state_pool, wanted,
                lambda st: state_fingerprint(trim_state_for_agent(st, budget)[0]))
            sample_size = len(picked)
            distinct_enough = sample_size >= wanted
            if not distinct_enough:
                log("    NOTE: only %d hash-different state(s) available (wanted %d); the "
                    "model sample size is counted as 1 per D-B" % (sample_size, wanted))
            observations = []
            frames_decide = frames_for_agent(frames)
            for si, item in enumerate(picked):
                st_agent, st_ev = trim_state_for_agent(item["state"], budget)
                st_ev = dict(st_ev or {})
                st_ev["fingerprint"] = state_fingerprint(st_agent)
                st_ev["source_label"] = item["label"]
                st_ev["source_state_sha256"] = item["source_sha256"]
                st_ev["independent_sample"] = bool(distinct_enough)
                action = agent.decide(frames_decide, st_agent, goal)
                try:
                    obs_verdict = agent.threshold_verdict()
                except Exception as e:  # noqa: BLE001
                    obs_verdict = {"error": "%s: %s" % (type(e).__name__, e)}
                observations.append({
                    "index": si, "state_label": item["label"],
                    "phase": item["phase"],
                    "state_sha256": st_ev["fingerprint"]["sha256"],
                    "source_state_sha256": item["source_sha256"],
                    "state_for_agent": st_ev,
                    "action": action,
                    "threshold_verdict": obs_verdict,
                    "evidence": agent.last_evidence})
                log("    agent observation %d/%d state=%s sha=%s noul=%s"
                    % (si + 1, sample_size, item["label"],
                       (st_ev["fingerprint"]["sha256"] or "")[:12],
                       {k: (o or {}).get("noul") for k, o in sorted(
                           (agent.last_noul or {}).items())}))
            action = observations[0]["action"] if observations else {"type": "wait",
                                                                    "why": "no state"}
            acts.append({"action": action, "why": "first decision"})
            # execute a couple of the agent's decisions so the interface is used
            # for real, not just called
            for step in range(args.agent_steps):
                if action.get("type") == "done":
                    break
                applied = apply_agent_action(mcp, action, gate, "agent%02d" % step)
                acts.append({"action": action, "applied": applied})
                time.sleep(args.settle_input)
                capture("agent%02d" % step, mcp, None, note="after the agent's action")
                action = agent.decide(frames_decide, observations[-1]["state_for_agent"]
                                      if observations else {}, goal)
            judge = agent.judge(frames_decide,
                                observations[-1]["state_for_agent"] if observations else {},
                                goal)
            threshold_verdict = None
            if hasattr(agent, "threshold_verdict"):
                try:
                    threshold_verdict = agent.threshold_verdict()
                except Exception as e:  # noqa: BLE001
                    threshold_verdict = {"error": "%s: %s" % (type(e).__name__, e)}
            gate["agent"] = {"report": agent.report(), "decisions": acts,
                             "judge": judge,
                             # TASK-129 D-B: the multi-state sampling evidence.  Every
                             # call is here with the state it was given (sha256 + what
                             # trimming cost), its action and its own noul/score answer.
                             "observations": observations,
                             "aggregate_over_observations": agent_aggregate(observations),
                             "sample_size": sample_size,
                             "sample_size_required": wanted,
                             "sample_size_is_independent": bool(distinct_enough),
                             "sample_size_note": (
                                 "%d hash-different state(s) were sent, one per call; "
                                 "TASK-128's one-state-three-calls construction is gone"
                                 % sample_size) if distinct_enough else
                                 ("only %d hash-different state(s) could be sampled, so "
                                  "the model sample size is 1 (D-B)" % sample_size),
                             "state_pool": [{"label": p["label"]}
                                            for p in state_pool],
                             # TASK-128 A1: which service was actually reached.  For the
                             # jev backend this is the deployed NeoHorse-Jev named by
                             # --base-url / PLAYTEST_BASE_URL -- NOT an in-process dumb
                             # server (those live only in playtest_agent.py --probe*).
                             "service": {
                                 "backend": getattr(agent, "name", args.agent),
                                 "base_url": getattr(agent, "base_url", None),
                                 "decision_path": getattr(agent, "decision_path", None),
                                 "model": getattr(agent, "model", None),
                                 "health": getattr(agent, "health", None)},
                             "state_for_agent": (observations[-1]["state_for_agent"]
                                                 if observations else None),
                             "token_estimator": {
                                 "name": "jev_estimate_tokens (TASK-129 D-C calibrated)",
                                 "safety_factor": JEV_TOKEN_SAFETY_FACTOR,
                                 "bridge": "budget 2000 here == budget 800 in TASK-128 "
                                           "(2000 / 2.5), verified on the 20 recorded "
                                           "positive states"},
                             # TASK-124 C: noul P(true) / score expected level against
                             # the CONFIGURABLE thresholds in tools/playability_controls.json
                             # (`agent_thresholds`).  Recorded, not silently trusted: the
                             # verdict carries its own `uncalibrated` flag.
                             "threshold_verdict": threshold_verdict,
                             "thresholds": dict(agent_thresholds),
                             "thresholds_source": os.path.join(HERE,
                                                               "playability_controls.json")}
            write_json(os.path.join(outdir, "agent.json"), gate["agent"])

        # ---------------- TASK-129 C/D-E: the VISION backend (PlayJev) ----------------
        if getattr(args, "visual_agent", "") and args.visual_agent != "none":
            try:
                gate["playjev"] = run_visual_agent(game, args, goal, frames,
                                                   playjev_thresholds, log)
                write_json(os.path.join(outdir, "playjev.json"), gate["playjev"])
            except Exception as e:  # noqa: BLE001
                import traceback
                gate["playjev"] = {"backend": args.visual_agent,
                                   "error": "%s: %s" % (type(e).__name__, e),
                                   "traceback": traceback.format_exc()[-2000:]}
                log("    playjev pass FAILED: %s: %s" % (type(e).__name__, e))

    except OnlyP7Done:
        pass
    except Exception as e:  # noqa: BLE001
        import traceback
        gate["errors"].append({"at": "run", "error": "%s: %s" % (type(e).__name__, e),
                               "traceback": traceback.format_exc()[-2000:]})
        log("    EXCEPTION: %s: %s" % (type(e).__name__, e))
    finally:
        gate["stop"] = gp.stop()
        gate["seconds"] = round(time.time() - t_start, 1)

    # frames.json + filmstrip
    try:
        write_json(os.path.join(outdir, "frames.json"), list(frames))
    except Exception as e:  # noqa: BLE001
        gate["errors"].append({"at": "frames.json", "error": "%s: %s" % (type(e).__name__, e)})
    try:
        if frames:
            oc = None
            if isinstance(gate.get("window"), dict):
                oc = "OS window %s  root viewport %s  declared %s  (%s)" % (
                    gate["window"].get("display_window_size"),
                    gate["window"].get("root_viewport_size"),
                    proj["declared_viewport"],
                    "MATCH" if (gate.get("window_conformance") or {}).get("matches_declared") else "MISMATCH")
            verdict = gate.get("criteria", {})
            note = "P1..P7 = %s" % " ".join(
                "%s:%s" % (k, "pass" if (verdict.get(k) or {}).get("pass") else
                           ("n/a" if k not in verdict else "FAIL"))
                for k in CRITERIA_ORDER)
            build_filmstrip(frames, os.path.join(outdir, "filmstrip.png"),
                            "%s -- full-window frames (game endpoint, real game process)" % game,
                            note=(oc or "") + "   " + note)
    except Exception as e:  # noqa: BLE001
        gate["errors"].append({"at": "filmstrip", "error": "%s: %s" % (type(e).__name__, e)})
    write_json(os.path.join(outdir, "gate.json"), gate)
    # TASK-130: report the criteria this run actually measured.  An `--only-p7` run covers
    # P7 alone and says so; printing P1..P6 as FAIL there would report untested criteria as
    # failures.
    measured = [k for k in CRITERIA_ORDER if k in gate["criteria"]]
    log("=== %s : %s" % (game, " ".join(
        "%s=%s" % (k, "PASS" if (gate["criteria"].get(k) or {}).get("pass") else "FAIL")
        for k in measured)))
    for k in measured:
        c = gate["criteria"].get(k) or {}
        if not c.get("pass"):
            log("      %s FAIL: %s" % (k, c.get("why")))
    return gate


def agent_aggregate(observations):
    """TASK-129 D-B: what a verdict over SEVERAL independent states should say.

    The single top-level `threshold_verdict` is TASK-124's shape (the last call): it is kept
    for every existing consumer.  But once the gate really samples >= 3 states, the honest
    aggregate is the WORST observation -- a game that looks unplayable in any state it was
    sampled in has not earned "playable" -- so it is computed and recorded separately, and
    the report says which number is which.  `noul_min_p_true` is applied to the MINIMUM
    noul over questions inside each observation, then the minimum over observations.
    """
    per_obs = []
    for ob in (observations or []):
        crit = (ob.get("threshold_verdict") or {}).get("criteria") or []
        vals = dict((str(c.get("id")).split(":", 1)[1], c.get("value")) for c in crit
                    if str(c.get("id", "")).startswith("noul:")
                    and isinstance(c.get("value"), (int, float)))
        threshold = ((ob.get("threshold_verdict") or {}).get("thresholds") or {}).get(
            "noul_min_p_true")
        pass_ok = None
        if vals and threshold is not None:
            noul_crit = [c for c in crit
                         if str(c.get("id", "")).startswith("noul:")]
            pass_ok = bool(noul_crit) and all(c.get("pass") for c in noul_crit)
        per_obs.append({"state_label": ob.get("state_label"),
                        "state_sha256": ob.get("state_sha256"),
                        "noul": vals, "min_noul": min(vals.values()) if vals else None,
                        "threshold": threshold,
                        "pass": pass_ok})
    mins = [o["min_noul"] for o in per_obs if isinstance(o["min_noul"], (int, float))]
    threshold = next((o["threshold"] for o in per_obs
                      if isinstance(o["threshold"], (int, float))), None)
    return {"rule": "the game is playable only if EVERY sampled state passes "
                    "(worst-case over observations)",
            "n_observations": len(per_obs),
            "per_observation": per_obs,
            "min_over_observations": min(mins) if mins else None,
            "threshold": threshold,
            "pass": (None if not mins or threshold is None
                     else bool(min(mins) >= threshold)),
            "note": "computed from the SAME independent states the calls used; the "
                    "top-level `threshold_verdict` remains the last call's (TASK-124 shape)"}


def frames_for_agent(frames):
    out = []
    for f in frames:
        out.append({k: f.get(k) for k in
                    ("index", "path", "width", "height", "content_fraction", "bbox",
                     "bbox_coverage", "background_rgb", "changed_pixels_vs_prev")})
    return out


def trim_state_for_agent(state, budget):
    """TASK-128: fit the sampled state into Jev's documented 2048-token `state` cap.

    Why this is needed at all (measured, not assumed): the gate's state is the game's
    whole exported node tree, and 15 of the 20 games exceed the cap.  Jev REFUSES an
    over-limit request (HTTP 422 `state exceeds 2048 tokens: N`) instead of truncating,
    and `playtest_agent.py`'s own ceiling check only refuses client-side -- it does not
    make the state fit.  The agent's `state_overflow="clip"` policy cannot help either:
    it drops whole top-level keys biggest-first, and the biggest key here is `nodes`,
    i.e. every game-specific field at once -- the model would then judge four scalars.

    So the gate trims *inside* `nodes`, in the state's own tree order (root and its
    first children are the ones that carry the movable objects), keeping every node it
    can and recording exactly which nodes it dropped.  It is opt-in (`--agent-state-budget`,
    default 0 = off), identical for positives and negatives, and the record is written to
    `gate\\agent\\state_for_agent`, so a trimmed judgement is never mistaken for a
    whole-state one.

    Returns (state_for_the_agent, evidence|None).
    """
    if not budget or not isinstance(state, dict):
        return state, None
    ev = {"policy": "keep the state's nodes in tree order until the estimated token count "
                    "fits the budget; drop the rest and name them",
          "budget_tokens_estimate": budget, "documented_limit": 2048,
          "note": "the client estimate is NOT an upper bound here: `jev_estimate_tokens` "
                  "assumes ~4 ASCII chars/token, but this JSON state tokenizes at "
                  "~1.7-2.4 real tokens per estimated one (measured: client 1018 -> "
                  "service 2160; client 1791 -> service 4229).  The budget is therefore "
                  "well below the documented cap, and the service's own count remains "
                  "the binding constraint."}
    before = jev_estimate_tokens(jev_render_state(state))
    ev["state_tokens_estimate_before"] = before
    if before <= budget:
        ev.update({"trimmed": False, "state_tokens_estimate": before,
                   "nodes_kept": None, "nodes_dropped": []})
        return state, ev
    nodes = state.get("nodes")
    if not isinstance(nodes, dict):
        ev.update({"trimmed": False, "state_tokens_estimate": before,
                   "nodes_kept": None, "nodes_dropped": [],
                   "why": "the state has no `nodes` object to trim; left unchanged"})
        return state, ev
    kept = {}
    dropped = []
    for key, value in nodes.items():
        kept[key] = value
        trial = dict(state)
        trial["nodes"] = kept
        if jev_estimate_tokens(jev_render_state(trial)) > budget:
            kept.pop(key, None)
            dropped.append(key)
    trimmed = dict(state)
    trimmed["nodes"] = kept
    ev.update({"trimmed": True, "state_tokens_estimate": jev_estimate_tokens(
        jev_render_state(trimmed)),
        "nodes_in_source": len(nodes), "nodes_kept": len(kept),
        "nodes_dropped": dropped,
        "state_keys_kept": sorted(trimmed.keys())})
    return trimmed, ev


def state_fingerprint(state):
    """TASK-128 A2: the exact state text handed to the model -- hash + a sample.

    `agent.json` must let a reviewer re-derive what the model judged without shipping
    the whole tree twice, so the rendered text is hashed and its head is kept.
    """
    text = jev_render_state(state)
    return {"sha256": hashlib.sha256(text.encode("utf-8")).hexdigest(),
            "chars": len(text), "tokens_estimate": jev_estimate_tokens(text),
            "head": text[:400]}


def state_phase(label):
    """Where in the run a sampled state was taken (D-B names three phases)."""
    if label == "00_settle":
        return "before-input"
    if label.startswith("post"):
        return "after-the-input-round"
    if label.endswith("_act"):
        return "after-input"
    if label.startswith("auto"):
        return "autonomous"
    if label.endswith("_pre") or label.endswith("_ctl"):
        return "no-input-control-window"
    return "other"


def pick_state_samples(pool, n, fingerprint_fn):
    """TASK-129 D-B: up to `n` states that are DIFFERENT as the model sees them.

    The gate samples a state before every action and after it, so the pool is large; what
    matters is that the picked ones are *independent observations*.  Identity is measured on
    the exact text that will be sent (`fingerprint_fn` = trim, then sha256), because two
    raw trees that trim to the same request are one observation, not two.  The preference
    order is D-B's own example -- before input / after input / a while later -- and the
    rest of the pool follows so a game that cannot offer those still gets a sample.

    Returns [{"label", "phase", "state", "sha256" (as sent), "source_sha256" (raw)}].
    """
    def sent_sha(state):
        try:
            return (fingerprint_fn(state) or {}).get("sha256")
        except Exception:  # noqa: BLE001
            return None

    by_label = dict((p["label"], p) for p in pool)
    order = []
    if "00_settle" in by_label:
        order.append("00_settle")
    for suffix, prefix in (("_act", None), (None, "post"), (None, "auto")):
        hits = [p["label"] for p in pool
                if (p["label"].endswith(suffix) if suffix else p["label"].startswith(prefix))]
        if hits:
            order.append(hits[-1])
    order += [p["label"] for p in pool]
    picked, seen = [], set()
    for label in order:
        if len(picked) >= n:
            break
        item = by_label.get(label)
        if item is None:
            continue
        sha = sent_sha(item["state"])
        if not sha or sha in seen:
            continue
        seen.add(sha)
        try:
            raw = state_fingerprint(item["state"])["sha256"]
        except Exception:  # noqa: BLE001
            raw = None
        picked.append({"label": label, "phase": state_phase(label), "state": item["state"],
                       "sha256": sha, "source_sha256": raw})
    return picked


def per_question(evidence):
    """`calls[-1]` -> {question key: the raw answer}, so no signal is summarised away."""
    out = {}
    for key, r in (evidence.get("answers_classified") or {}).items():
        out[key] = {"role": r.get("role"), "choice": r.get("choice"),
                    "noul": r.get("noul"), "score": r.get("score"),
                    "score_levels": r.get("score_levels"),
                    "legend_flipped": r.get("legend_flipped"),
                    "probabilities": r.get("probabilities"),
                    "confidence": r.get("confidence"),
                    "abstain": r.get("abstain"),
                    "abstain_reasons": r.get("abstain_reasons")}
    return out


def pick_visual_frames(usable, settled, n):
    """TASK-129 C: up to `n` frames that are DIFFERENT images, preferring the settle ones.

    TASK-128's lesson applies to pixels too: pong's screen is byte-identical for every
    automatic frame until the ball is served, so "3 frames" would have been ONE visual
    observation reported three times.  The preference order is settle/auto first (what a
    player sees when the game comes up), then an after-input frame and then a post frame,
    and identity is the file's sha256 -- the same hash the artifact records.
    """
    def sha(f):
        return f.get("sha256")

    order = []
    for f in settled:
        order.append(f)
    for f in usable:
        label = str(f.get("label", ""))
        if label.endswith("_act") and f not in order:
            order.append(f)
    for f in usable:
        if str(f.get("label", "")).startswith("post") and f not in order:
            order.append(f)
    for f in usable:
        if f not in order:
            order.append(f)
    picked, seen = [], set()
    for f in order:
        if len(picked) >= n:
            break
        s = sha(f)
        if not s or s in seen:
            continue
        seen.add(s)
        picked.append(f)
    note = ("%d hash-distinct frame(s) chosen from %d usable; %d settle/auto frame(s) "
            "were available, %d of them hash-distinct"
            % (len(picked), len(usable), len(settled),
               len(set(sha(f) for f in settled))))
    return picked, note


def run_visual_agent(game, args, goal, frames, playjev_thresholds, log_fn):
    """TASK-129 C: the VISION backend's pass over the frames this run captured.

    One image + N choice questions per request (PlayJev's `serve.py` shares ONE frame set
    between every question of a request), with the playability answer asked as `playable`
    and the brokenness answer kept as an observation that is NOT in the decision path
    (D-E).  Nothing here changes P1..P6: the result lands in `gate["playjev"]` beside
    `gate["agent"]`.
    """
    usable = [f for f in frames
              if f.get("ok") and f.get("path") and os.path.isfile(f["path"])]
    settled = [f for f in usable
               if f.get("label") == "settle" or str(f.get("label", "")).startswith("auto")]
    vis_frames, vis_note = pick_visual_frames(usable, settled,
                                              max(1, int(args.visual_frames)))
    base_url = (getattr(args, "playjev_base_url", "") or
                os.environ.get("PLAYTEST_PLAYJEV_BASE_URL", "") or
                os.environ.get("PLAYJEV_BASE_URL", ""))
    thresholds = visual_thresholds_for_agent(playjev_thresholds)
    opts = {"base_url": base_url,
            "model": "playjev-0.8b",
            "decision_path": "/v1/systemone",
            "invariant_questions": int(getattr(args, "playjev_invariant_questions", 3)),
            "score_question": True,
            "score_in_verdict": False,
            "verdict_invariant_keys": ["playable"],
            "abstain_min_confidence": float(
                getattr(args, "playjev_abstain_min_confidence", 0.0)),
            "timeout": float(getattr(args, "playjev_timeout", 300.0)),
            "thresholds": thresholds}
    agent = build_agent("playjev", game, goal.get("objective") or "", opts)
    questions, roles = {}, {}
    try:
        questions, roles = agent.build_questions(goal)
    except Exception as e:  # noqa: BLE001
        questions = {"error": "%s: %s" % (type(e).__name__, e)}
    out = {"backend": "playjev",
           "task": "TASK-129 C/D-E (+ TASK-130 B input form)",
           "one_image_plus_n_questions": True,
           # TASK-130 B: WHICH PIXELS the model was shown.  `native` is the frame exactly
           # as captured (the TASK-129 baseline); `crop` is the same frame cut down to its
           # content bounding box by `content_bbox_crop` (rule + box + sha256 recorded per
           # frame below), so "the game was a small part of what the model saw" stops being
           # an assumption and becomes a recorded, reproducible property of the input.
           "visual_input_form": getattr(args, "visual_input_form", "native"),
           "visual_input_form_note": (
               "native = the captured full-window frame, byte-identical to TASK-129"
               if getattr(args, "visual_input_form", "native") == "native" else
               "crop = content-bbox crop of the captured frame (%s)"
               % content_bbox_crop.__doc__.split("\n")[0].strip()),
           "playable_key": agent.playable_key,
           "score_in_decision_path": False,
           "score_direction_note": PLAYJEV_SCORE_DIRECTION_NOTE,
           "uncalibrated": bool(playjev_thresholds.get("uncalibrated", True)),
           "thresholds": thresholds,
           "thresholds_source_block": playjev_thresholds,
           "thresholds_source": os.path.join(HERE, "playability_controls.json"),
           "question_keys": list(questions) if isinstance(questions, dict) else None,
           "question_roles": dict((k, v["role"]) for k, v in roles.items()),
           "questions": questions if isinstance(questions, dict) else {"error": questions},
           "rule": "playable P(true) >= %.3f" % thresholds["noul_min_p_true"],
           "frames_used": [],
           "observations": [],
           "frames_available": len(usable),
           "frames_settle_available": len(settled),
           "frame_selection_note": vis_note,
           "notes": []}
    out["visual_sample_size"] = len(vis_frames)
    out["visual_sample_size_is_independent"] = bool(len(vis_frames) > 1)
    if not vis_frames:
        out["error"] = ("no usable full-window frame was captured, so the vision backend "
                        "has nothing to judge (PlayJev refuses a text state)")
        log_fn("    playjev: NO FRAME to judge")
        return out

    for f in vis_frames:
        frame_rec = {k: f.get(k) for k in
                     ("index", "path", "width", "height", "sha256", "content_fraction",
                      "bbox", "bbox_coverage", "background_rgb", "window",
                      "changed_pixels_vs_prev")}
        frame_rec["label"] = f.get("label")
        # TASK-130 B: hand the model the pixels the input form asks for, and keep the
        # provenance of BOTH images (the captured one and the derived one).
        crop_info = None
        form = getattr(args, "visual_input_form", "native")
        if form == "crop":
            crop_dir = os.path.join(RUNS, game, "frames_crop")
            if not os.path.isdir(crop_dir):
                os.makedirs(crop_dir)
            dst = os.path.join(crop_dir, os.path.basename(f.get("path") or "frame.png"))
            crop_info = content_bbox_crop(
                f["path"], dst,
                margin=int(getattr(args, "visual_crop_margin", 0)),
                pad=int(getattr(args, "visual_crop_pad", 0)),
                min_side=int(getattr(args, "visual_crop_min_side", 0)))
            frame_rec["path"] = dst
            frame_rec["sha256"] = crop_info.get("sha256")
            frame_rec["width"], frame_rec["height"] = crop_info.get("dest_size") or [None, None]
        out["frames_used"].append({"label": f.get("label"), "index": f.get("index"),
                                   "file": os.path.basename(f.get("path") or ""),
                                   "path": f.get("path"), "sha256": f.get("sha256"),
                                   "input_form": form,
                                   "model_image_path": frame_rec.get("path"),
                                   "model_image_sha256": frame_rec.get("sha256"),
                                   "crop": crop_info})
        t0 = time.time()
        action = agent.decide([frame_rec], {}, goal)
        wall = round(time.time() - t0, 3)
        ev = agent.last_evidence or {}
        q = per_question(ev)
        verdict = agent.threshold_verdict()
        obs = {"frame_label": f.get("label"), "frame_index": f.get("index"),
               "frame_file": os.path.basename(f.get("path") or ""),
               "frame_path": f.get("path"), "frame_sha256": f.get("sha256"),
               "input_form": form,
               "model_image_path": frame_rec.get("path"),
               "model_image_sha256": frame_rec.get("sha256"),
               "crop": crop_info,
               "content_fraction": f.get("content_fraction"), "bbox": f.get("bbox"),
               "http_status": (ev.get("transport") or {}).get("status"),
               "seconds": wall, "model": ev.get("model"), "timing": ev.get("timing"),
               "request_meta": ev.get("request_meta"),
               "transport": {"url": (ev.get("transport") or {}).get("url"),
                             "status": (ev.get("transport") or {}).get("status"),
                             "seconds": (ev.get("transport") or {}).get("seconds"),
                             "attempts": (ev.get("transport") or {}).get("attempts")},
               "action": action, "questions": q,
               "playable": q.get(agent.playable_key, {}).get("noul"),
               "abstain": bool(ev.get("abstain")),
               "abstained_questions": ev.get("abstained_questions"),
               "abstain_reasons": ev.get("abstain_reasons"),
               "verdict": verdict,
               "score_observation": ev.get("score_observation")}
        out["observations"].append(obs)
        log_fn("    playjev frame=%s status=%s playable=%s score=%s abstain=%s conf=%s"
               % (f.get("label"), obs["http_status"], obs["playable"],
                  (obs["score_observation"] or {}).get("values"),
                  obs["abstain"], q.get(agent.playable_key, {}).get("confidence")))

    # the gate-level vision verdict: every used frame must clear the `playable` rule and
    # no `playable` answer may abstain (an abstain is never a pass)
    vals = [o["playable"] for o in out["observations"]]
    abstained = [o for o in out["observations"]
                 if o["abstain"] and agent.playable_key in (o["abstained_questions"] or [])]
    if abstained:
        out["verdict"] = {"pass": None, "why": "%d frame(s) abstained on `playable`"
                                               % len(abstained)}
    elif any(not isinstance(v, (int, float)) for v in vals):
        out["verdict"] = {"pass": None, "why": "no usable `playable` answer"}
    else:
        worst = min(vals)
        out["verdict"] = {"pass": bool(worst >= thresholds["noul_min_p_true"]),
                          "why": "%d/%d frames clear `%s`: worst P(true)=%.6f vs %.3f"
                                 % (sum(1 for v in vals if v >= thresholds["noul_min_p_true"]),
                                    len(vals), out["rule"], worst,
                                    thresholds["noul_min_p_true"]),
                          "worst_playable": worst}
    out["playable_values"] = dict((o["frame_label"], o["playable"])
                                  for o in out["observations"])
    out["playable_distribution"] = describe_small(vals)
    out["score_observation"] = {
        "role": "observation", "in_decision_path": False, "direction": "suspect",
        "uncalibrated": True, "note": PLAYJEV_SCORE_DIRECTION_NOTE,
        "per_frame": dict((o["frame_label"],
                           (o["score_observation"] or {}).get("values"))
                          for o in out["observations"]),
        "distribution": describe_small(
            [(o["score_observation"] or {}).get("values", {}).get("brokenness")
             for o in out["observations"]])}
    out["service"] = {"backend": getattr(agent, "name", "playjev"),
                      "base_url": getattr(agent, "base_url", None),
                      "decision_path": getattr(agent, "decision_path", None),
                      "model": getattr(agent, "model", None),
                      "answer_model": (agent.last_evidence or {}).get("model"),
                      "health": getattr(agent, "health", None),
                      "case_evidence": "runs/playability/<out-root>/<game>/calls/*.json"}
    out["errors"] = list(agent.errors)

    # ---- D-E declarative probe: flip the legend order, and NEVER use the result ----
    if getattr(args, "visual_legend_probe", False):
        probe_opts = dict(opts)
        probe_opts["legend_flipped"] = True
        probe = build_agent("playjev", game, goal.get("objective") or "", probe_opts)
        f = vis_frames[0]
        frame_rec = {k: f.get(k) for k in
                     ("index", "path", "width", "height", "sha256", "content_fraction",
                      "bbox", "bbox_coverage", "background_rgb", "window",
                      "changed_pixels_vs_prev")}
        frame_rec["label"] = f.get("label")
        act = probe.decide([frame_rec], {}, goal)
        ev = probe.last_evidence or {}
        q = per_question(ev)
        out["legend_probe"] = {
            "declared_probe": True,
            "in_decision_path": False,
            "purpose": "test whether the measured score inversion is a wording/legend-order "
                       "artefact: the SAME frame is asked the SAME question with the option "
                       "order reversed",
            "frame_label": f.get("label"), "frame_sha256": f.get("sha256"),
            "order_used": ["5..1 (flipped)"],
            "http_status": (ev.get("transport") or {}).get("status"),
            "action": act,
            "questions": q,
            "playable_flipped_run": q.get(probe.playable_key, {}).get("noul"),
            "score_with_flipped_legend": q.get(probe.score_key, {}).get("score"),
            "score_with_flipped_legend_levels": q.get(probe.score_key, {}).get("score_levels"),
            "legend_flipped": True,
            "note": "NEVER ENTERS THE VERDICT (TASK-129 D-E); recorded so the direction "
                    "question can be argued with data"}
    return out


def describe_small(xs):
    """n/min/max/median/mean over a handful of numbers, with the raw values kept."""
    vals = sorted(x for x in (xs or []) if isinstance(x, (int, float)))
    if not vals:
        return {"n": 0, "min": None, "max": None, "median": None, "mean": None,
                "values": []}
    n = len(vals)
    med = vals[n // 2] if n % 2 else 0.5 * (vals[n // 2 - 1] + vals[n // 2])
    return {"n": n, "min": vals[0], "max": vals[-1], "median": med,
            "mean": sum(vals) / float(n), "values": vals}



def apply_agent_action(mcp, action, gate, tag):
    t = action.get("type")
    if t == "key" and isinstance(action.get("keycode"), int):
        code = probe_key_event(action["keycode"], bool(action.get("pressed", True)),
                               "parse_input_event")
    elif t == "action" and action.get("action"):
        code = probe_action(action["action"], bool(action.get("pressed", True)))
    elif t == "script" and action.get("code"):
        code = action["code"]
    elif t == "wait":
        time.sleep(min(5.0, float(action.get("ms", 200)) / 1000.0))
        return {"type": "wait", "slept_ms": action.get("ms", 200)}
    else:
        return {"type": t, "applied": False, "why": "not executable"}
    r = mcp.call_tool("running_game_execute_gdscript", {"code": code}, timeout=40)
    applied = {"type": t, "applied": bool(r.get("ok")), "result": r.get("value"),
               "error": r.get("error")}
    if t == "key":
        mcp.call_tool("running_game_execute_gdscript",
                      {"code": probe_key_event(action["keycode"], False,
                                               "parse_input_event")}, timeout=40)
    if t == "action":
        mcp.call_tool("running_game_execute_gdscript",
                      {"code": probe_action(action["action"], False)}, timeout=40)
    return applied


def load_controls(path=None):
    """The curated capability table (TASK-116 P6).

    P1..P5 can all be green on a game a human still cannot play -- a Lunar Lander
    with nothing but a thrust key is the textbook case.  P6 is the missing half:
    for every capability a player needs, it names the declared action that is
    supposed to deliver it *and the observable that must move when that action is
    injected*.  The table is authored by hand (that part is judgement) and every
    row of it is then machine-checked by the gate (that part is evidence).
    """
    p = path or os.path.join(HERE, "playability_controls.json")
    if not os.path.isfile(p):
        return {}
    doc = json.load(io.open(p, encoding="utf-8"))
    return doc.get("games") or {}


def load_agent_thresholds(path=None):
    """TASK-124 C: the configurable playability thresholds for the model-in-the-loop.

    They live next to the capability table because they answer a neighbouring question:
    P1..P6 are machine checks, while a `noul` P(true) / `score` expected level is a
    model opinion.  The values are PRIOR ONLY -- the vendor reports no NLL/Brier/ECE
    calibration and says to set thresholds on an independent dataset -- so the block
    carries an explicit `uncalibrated` flag and the calibration plan.
    """
    p = path or os.path.join(HERE, "playability_controls.json")
    if not os.path.isfile(p):
        return {}
    doc = json.load(io.open(p, encoding="utf-8"))
    return doc.get("agent_thresholds") or {}


def load_playjev_thresholds(path=None):
    """TASK-129 C/D-E: the VISION backend's own threshold block, INDEPENDENT of Jev's.

    They are separate on purpose: Jev judges a text `state` and PlayJev judges one frame,
    so a number fitted for one backend is not a number for the other.  The block also
    states, in the configuration itself, that `score` is not in the decision path.
    """
    p = path or os.path.join(HERE, "playability_controls.json")
    if not os.path.isfile(p):
        return {}
    doc = json.load(io.open(p, encoding="utf-8"))
    return doc.get("playjev_thresholds") or {}


def visual_thresholds_for_agent(block):
    """`playjev_thresholds.playable_min_p_true` -> the agent's `noul_min_p_true`.

    The mapping is explicit and recorded (the gate keeps the source block verbatim), so a
    reviewer can always see which number produced which verdict.
    """
    t = {"noul_min_p_true": 0.5, "score_max_expected": 2.5}
    if isinstance(block, dict):
        v = block.get("playable_min_p_true")
        if isinstance(v, (int, float)):
            t["noul_min_p_true"] = float(v)
        v = block.get("score_max_expected")
        if isinstance(v, (int, float)):
            t["score_max_expected"] = float(v)
    return t


def required_ui_items(controls, game):
    """The declaration half of P7: `games.<game>.required_ui.items` (TASK-130)."""
    decl = (controls.get(game) or {}).get("required_ui") or {}
    items = decl.get("items")
    return decl, (items if isinstance(items, list) else [])


# ---------------------------------------------------------------------------
# TASK-131 X12/X13: the gameplay-observable declaration, and what it judges
# ---------------------------------------------------------------------------
def gameplay_declaration(controls, game):
    """`games.<game>.gameplay_observables` -- TASK-131 X12."""
    return ((controls or {}).get(game) or {}).get("gameplay_observables") or {}


def marker_declaration(controls, game):
    """`games.<game>.state_markers` -- TASK-131 X13 (per-frame Paused/clock/Ticks)."""
    return ((controls or {}).get(game) or {}).get("state_markers") or {}


def mode_declarations(controls, game):
    """`games.<game>.mode_actions` -- TASK-131 X13 (actions with a persistent effect)."""
    v = ((controls or {}).get(game) or {}).get("mode_actions")
    return v if isinstance(v, list) else []


def liveness_declaration(controls, game):
    """`games.<game>.liveness` -- TASK-131 X10/X13 (the state the player is first shown)."""
    return ((controls or {}).get(game) or {}).get("liveness") or {}


def refusal_declaration(controls, game):
    """`games.<game>.refusal_evidence` -- TASK-131 X12.

    The one carve-out P2 keeps: an action that moved no gameplay observable may still be
    correct when the GAME ITSELF recorded a deliberate refusal (a wall, the board edge, an
    illegal direction).  That is the project convention TASK-116 wrote down.  The carve-out
    is deliberately NOT enough on its own: P2 also requires that at least one action of the
    game did move a gameplay observable, so "everything was refused, because the game is
    dead" (snake, game2048) still fails.
    """
    return ((controls or {}).get(game) or {}).get("refusal_evidence") or {}


def refusal_hit(changes, decl):
    """The first changed entry that records a deliberate refusal, or None."""
    keys = decl.get("keys") or ["LastRefusedInput", "Rejected"]
    words = decl.get("value_words") or ["rejected", "blocked", "refused", "no_change"]
    for c in changes or []:
        k = c.get("key") or ""
        if any(s in k for s in keys):
            return "%s: %r -> %r" % (k, c.get("from"), c.get("to"))
        v = c.get("to")
        if isinstance(v, str) and any(w in v.lower() for w in words):
            return "%s: %r" % (k, v)
    return None


def is_meta_key(key):
    return any(re.search(p, key or "") for p in META_KEY_PATTERNS)


def is_gameplay_key(key, decl):
    """Is a changed state key a statement about the GAME WORLD?

    Two gates, in this order: the key must name something the game's own declaration
    lists, and it must not match the uniform META patterns.  META wins, deliberately --
    otherwise a declaration could re-admit `Paused` by listing it.
    """
    items = decl.get("items") or []
    return bool(key) and any(s in key for s in items) and not is_meta_key(key)


def gameplay_changes(changes, decl):
    return [c for c in (changes or []) if is_gameplay_key(c.get("key") or "", decl)]


def arm_evidence(ch, decl, min_px=P3_MIN_CHANGED_PIXELS, refusal_decl=None):
    """What ONE injection arm shows, judged against its own immediately preceding,
    same-length, no-input control window (the attribution design P2 already used).

    What TASK-131 changes is only WHAT may be counted: the action must have moved a
    declared GAMEPLAY observable past its control, or changed pixels past its control.
    `meta_only` is the exact case that used to pass: the action did something, but every
    thing it did was plumbing (`snake`: `LastRefusedInput`, `DirectionX`, `Paused`).
    `refused` is the one accepted alternative -- the game's own refusal record moved and
    the control window did not -- reported separately so it can never masquerade as a
    gameplay response.
    """
    ctl = ch.get("control") or {}
    act = ch.get("action") or {}
    ctl_g = gameplay_changes(ctl.get("state_changes"), decl)
    act_g = gameplay_changes(act.get("state_changes"), decl)
    ctl_px = max(0, (ctl.get("pixels") or {}).get("changed_pixels") or 0)
    act_px = max(0, (act.get("pixels") or {}).get("changed_pixels") or 0)
    pixel_wins = act_px > max(int(ctl_px * 1.5), min_px)
    gameplay_wins = len(act_g) > len(ctl_g)
    ctl_ref = refusal_hit(ctl.get("state_changes"), refusal_decl or {})
    act_ref = refusal_hit(act.get("state_changes"), refusal_decl or {})
    refused = bool(act_ref) and not ctl_ref and not gameplay_wins and not pixel_wins
    meta_only = (not gameplay_wins) and (not pixel_wins) and not refused and \
        len(act.get("state_changes") or []) > len(ctl.get("state_changes") or [])
    return {
        "control_gameplay_count": len(ctl_g),
        "action_gameplay_count": len(act_g),
        "gameplay_changes": [c.get("key") for c in act_g],
        "gameplay_wins": bool(gameplay_wins),
        "control_changed_pixels": ctl_px,
        "action_changed_pixels": act_px,
        "pixel_wins": bool(pixel_wins),
        "refused": bool(refused),
        "refusal_evidence": act_ref,
        "control_refusal_evidence": ctl_ref,
        "meta_only": bool(meta_only),
        "responds": bool(gameplay_wins or pixel_wins),
        # what P2 ultimately asks per action: a gameplay response, or a refusal the game
        # itself recorded (and the run as a whole must still show at least one response)
        "acceptable": bool(gameplay_wins or pixel_wins or refused),
    }


# ---------------------------------------------------------------------------
# TASK-132: the MODEL-PLAYER criterion, as a gate-readable document
# ---------------------------------------------------------------------------
# The user's TASK-132 ruling replaced "does the state move when a scripted action is
# injected" with "does a MODEL acting as a simulated human player look at the picture,
# choose an input, and does the game accept it AND the picture change".  The loop that
# produces that evidence is `tools/playtest_player.py`; it writes `steps.jsonl`.  P1..P7
# are NOT the model-player criterion and must not be quoted as one -- they answer "can the
# code run" only.  This function is the single place the gate states the rule and can be
# handed a recorded run's steps.
MODEL_PLAYER_CRITERION_NOTE = (
    "TASK-132: P1..P7 answer 'can the game's code run and draw'; they are NOT the "
    "playability verdict.  The playability verdict is the MODEL-PLAYER loop "
    "(tools/playtest_player.py): a model looks at one full-window frame, answers a `choice` "
    "question whose criteria are the game's own declared InputMap actions, the action is "
    "injected through Input.parse_input_event, and the run records (a) the game's own "
    "InputMap read as the ack evidence, (b) the before/after frame sha256 and pixel diff "
    "against an equal-frame-budget NO-INPUT control window, and (c) every frame for a human "
    "to read.  FAIL = the model produced an action AND the game accepted it AND the picture "
    "did not change.  PASS = >= 8 steps with >= 75% accepted-and-changed AND the reader's "
    "per-frame check agreeing the changes match the game's declared logic.  Two MODEL-side "
    "conclusions are filed SEPARATELY from that verdict and are neither game defects nor "
    "PASSes: MODEL_FIXED_POINT (TASK-133: >= 3 steps of the same action on a byte-identical "
    "frame) and MODEL_NO_PROGRESS (TASK-134: >= 3 consecutive sent steps with no gameplay "
    "progress even if the actions differ -- the fixed point's measured blind spot).  "
    "TASK-136 §1.A.1: the CHANGE TEST is scored under TWO declared margins and the STRICT "
    "one is the pass criterion; the baseline margin is the control reading, so a run only "
    "it passes is written PASS(baseline only) with counts_as_pass=false and is NOT a pass."
)


def load_change_margins(path=None):
    """TASK-136 §1.A.1: the two declared model-player change margins, read by the gate.

    The loop (`tools/playtest_player.py`) is the authority and the declaration lives in
    `tools/playability_controls.json -> model_player_change_margin`; this function reads the
    SAME declaration so `gate.json` states the criterion the loop actually applied instead
    of a second, drifting copy of the rule.
    """
    p = path or os.path.join(HERE, "playability_controls.json")
    fallback = {"default_margin": "strict",
                "strict": {"gameplay_control_factor": 2.0, "gameplay_min_movement": 1.0,
                           "pixel_control_factor": 2.5, "min_pixels": P3_MIN_CHANGED_PIXELS},
                "baseline": {"gameplay_control_factor": 1.0, "gameplay_min_movement": 0.0,
                             "pixel_control_factor": 2.5,
                             "min_pixels": P3_MIN_CHANGED_PIXELS}}
    try:
        doc = json.load(io.open(p, encoding="utf-8"))
        block = doc.get("model_player_change_margin") or {}
        for name in ("baseline", "strict"):
            src = block.get(name) if isinstance(block.get(name), dict) else {}
            for key in fallback[name]:
                if key in src:
                    fallback[name][key] = src[key]
        if block.get("default_margin") in ("baseline", "strict"):
            fallback["default_margin"] = block["default_margin"]
        fallback["source"] = os.path.abspath(p)
    except Exception:  # noqa: BLE001 - the gate must run on a bare checkout
        pass
    return fallback


def record_model_player_criterion(gate, args, game):
    """File the TASK-132 model-player rule beside P1..P7 in `gate.json`.

    Called from BOTH paths (the full run and `--only-p7`) for the same reason: a reader who
    sees "P1..P7 pass" must also see, in the same document, that those seven are not the
    playability verdict.  With no `--model-player-steps` the note is recorded and the
    evidence is null -- an unmeasured criterion is left visibly unmeasured, never implied.
    """
    gate["model_player_criterion"] = {"note": MODEL_PLAYER_CRITERION_NOTE,
                                      "steps_file": None, "evidence": None}
    p = getattr(args, "model_player_steps", "")
    if not p:
        return gate["model_player_criterion"]
    try:
        with io.open(p, encoding="utf-8") as fh:
            mp_steps = [json.loads(line) for line in fh if line.strip()]
        gate["model_player_criterion"] = {
            "note": MODEL_PLAYER_CRITERION_NOTE,
            "steps_file": os.path.abspath(p),
            "evidence": evaluate_model_player_steps(mp_steps, game)}
        log("    model-player criterion: pass=%s (%s)"
            % (gate["model_player_criterion"]["evidence"]["pass"],
               gate["model_player_criterion"]["evidence"]["why"][:110]))
    except Exception as e:  # noqa: BLE001
        gate["model_player_criterion"]["error"] = "%s: %s" % (type(e).__name__, e)
        log("    model-player criterion could not be read: %s" % e)
    return gate["model_player_criterion"]


def _model_fixed_point_steps(injected_steps, min_run=3):
    """TASK-133 §1.C.1: the MODEL's fixed point, as a separate conclusion.

    `>= min_run` consecutive injected steps answering the SAME action on a
    byte-identical before-frame means the model is stuck.  It is a fact about the model:
    it is reported under its own key (`MODEL_FIXED_POINT`), it is never counted as a
    game defect, and it can never make a game PASS.  This is the gate-side twin of
    `playtest_player.model_fixed_point` (the same rule, so `gate.json` and `player.json`
    cannot disagree).
    """
    best = {"found": False, "min_run": int(min_run), "length": 0, "steps": [],
            "action": None, "frame_sha": None}
    run_len, run_steps, run_action, run_sha = 0, [], None, None
    # The run must be over INPUTTED, consecutive steps: a step the model answered with
    # `wait` (not injected) breaks it.  This walks the FULL step list -- not a
    # pre-filtered one -- so the gap is visible, exactly as in the loop's own
    # `model_fixed_point` (a first draft filtered first and reported 7 for a run broken in
    # the middle, while the loop-side twin reported 4; the two halves of one rule must
    # not disagree).
    for r in injected_steps or []:
        if not (r.get("ack") or {}).get("injected"):
            run_len, run_steps, run_action, run_sha = 0, [], None, None
            continue
        act = ((r.get("action") or {}).get("action"))
        sha = r.get("frame_before_sha")
        if act is not None and act == run_action and sha is not None and sha == run_sha:
            run_len += 1
            run_steps.append(r.get("step"))
        else:
            run_len, run_steps, run_action, run_sha = 1, [r.get("step")], act, sha
        if run_len > best["length"]:
            best.update({"found": run_len >= int(min_run), "length": run_len,
                         "steps": list(run_steps), "action": run_action,
                         "frame_sha": run_sha})
    if not best["found"]:
        best["reading"] = ("no run of >= %d consecutive steps shared one action AND one "
                           "byte-identical frame" % int(min_run))
    else:
        best["reading"] = ("the MODEL is stuck: %d consecutive steps all answered '%s' on "
                           "the byte-identical frame %s"
                           % (best["length"], best["action"],
                              (best["frame_sha"] or "")[:8]))
    best["what"] = ("TASK-133 §1.C.1: a model-side fixed point.  It is NOT a game defect "
                    "(do not fail the game for it) and NOT a PASS (do not accept it as "
                    "evidence the game is playable).  Reported separately from FAIL.")
    return best


def _model_no_progress_steps(steps, min_run=3):
    """TASK-134 §1.C.1: the MODEL-side "no progress" conclusion, gate-side twin.

    `MODEL_FIXED_POINT` demands the SAME action on the SAME frame, so `pong x playjev`'s
    sequence -- nine steps that were accepted and left the picture unchanged, with the
    action varied once -- slipped through it (TASK-133 §4.2a).  This rule keeps only the
    two facts that matter: the step was really SENT to the game, and nothing advanced
    (`change.changed` is false, i.e. the picture did not beat its own no-input control
    window).  `>= min_run` consecutive such steps is the conclusion.

    TASK-134 §1.C.3: it is filed under its own key, it is NOT a game defect (it never
    touches `pass`), and it is NOT a PASS.  It is the gate-side twin of
    `playtest_player.model_no_progress`, so `gate.json` and `player.json` cannot disagree.
    """
    best = {"found": False, "min_run": int(min_run), "length": 0, "steps": [],
            "actions": [], "distinct_actions": []}
    run_len, run_steps, run_acts = 0, [], []
    for r in steps or []:
        if not (r.get("ack") or {}).get("injected"):
            run_len, run_steps, run_acts = 0, [], []
            continue
        if (r.get("change") or {}).get("changed"):
            run_len, run_steps, run_acts = 0, [], []
            continue
        run_len += 1
        run_steps.append(r.get("step"))
        run_acts.append((r.get("action") or {}).get("action"))
        if run_len > best["length"]:
            best.update({"found": run_len >= int(min_run), "length": run_len,
                         "steps": list(run_steps), "actions": list(run_acts),
                         "distinct_actions": sorted(set(a for a in run_acts if a))})
    if not best["found"]:
        best["reading"] = ("no run of >= %d consecutive steps that were SENT to the game "
                           "and made no gameplay progress (the longest was %d)"
                           % (int(min_run), best["length"]))
    else:
        best["reading"] = ("%d consecutive steps were SENT to the game and nothing advanced "
                           "(actions: %s)" % (best["length"], best["distinct_actions"]))
    best["what"] = ("TASK-134 §1.C.1: >= %d consecutive injected steps with no gameplay "
                    "progress, EVEN IF the actions differ.  NOT a game defect (it does not "
                    "fail the game) and NOT a PASS; reported separately from FAIL."
                    % int(min_run))
    return best


def evaluate_model_player_steps(steps, game=None):
    """The TASK-132 rule, applied to a recorded `steps.jsonl` list.

    This is the gate-side reading of the model-player evidence: it states the rule in the
    same file as P1..P7 so a reader of `gate.json` can see that P1..P7 are not the verdict.
    The authoritative summary is the loop's own `player.json`; this function exists so the
    gate can record the criterion beside the other criteria without importing the tool.

    TASK-139 §1.A/§1.B: the two declarations this batch added are applied HERE too, so the
    gate cannot report a verdict the loop would not:
      * a window shorter than the declared `min_frames` makes the run WINDOW_TOO_SHORT (never
        a PASS), read from the same per-step measured spans the loop records;
      * a step the game's own counters recorded as a deliberate refusal is dropped from the
        FAIL set and the denominator, and a run refused everywhere cannot PASS.
    """
    steps = [r for r in (steps or []) if isinstance(r, dict) and r.get("step")]
    injected = [r for r in steps if (r.get("ack") or {}).get("injected")]
    accepted = [r for r in injected if (r.get("ack") or {}).get("accepted")]
    margins = load_change_margins()
    # the loop owns the refusal/window declarations; the import is deferred so this module
    # keeps loading first (playtest_player imports THIS file at module scope).
    try:
        from playtest_player import (load_refusal_boundary, load_window_declaration,
                                     step_refusal_record, window_frames_of)
        refusal_boundary = load_refusal_boundary()
        window_decl = load_window_declaration()
    except Exception as e:  # noqa: BLE001
        refusal_boundary = {"min_real_progress_steps": 4, "min_real_progress_rate": 0.5,
                            "declared_by": "TASK-139 §1.B", "load_error": str(e)}
        window_decl = {"min_frames": 20, "declared_by": "TASK-139 §1.A",
                       "load_error": str(e)}

        def step_refusal_record(rec, decl):
            return None

        def window_frames_of(c, a, min_frames=20):
            return {"min_frames": min_frames, "control_frames": c, "action_frames": a,
                    "measured": False, "too_short": False, "state": "unmeasured",
                    "short_windows": []}

    def _refused(rec):
        sr = rec.get("step_refusal")
        if isinstance(sr, dict):
            return bool(sr.get("refused_legal"))
        return bool((rec.get("ack") or {}).get("refusal"))

    def _changed(rec, margin):
        """One step under one margin: `change.strict` when the loop recorded it, else the
        step's own `change.changed` (which IS the baseline reading)."""
        ch = rec.get("change") or {}
        if margin == "strict" and isinstance(ch.get("strict"), dict):
            return bool(ch["strict"].get("changed"))
        return bool(ch.get("changed"))

    refused_recs = [r for r in accepted if _refused(r)]
    refused_steps = [r["step"] for r in refused_recs]
    refused_set = set(refused_steps)
    rated = [r for r in accepted if r["step"] not in refused_set]
    changed = [r for r in accepted if _changed(r, "baseline")]
    changed_strict = [r for r in accepted if _changed(r, "strict")]
    real_progress = [r["step"] for r in rated if _changed(r, "baseline")]
    real_progress_strict = [r["step"] for r in rated if _changed(r, "strict")]
    refusal_only_run = bool(refused_recs and not rated)
    fail = [r["step"] for r in steps
            if r.get("step_verdict") == "FAIL_no_change_after_accepted_input"]
    fail_raw = list(fail)
    fail = [s for s in fail if s not in refused_set]
    fail_strict = [r["step"] for r in accepted if not _changed(r, "strict")]
    fail_strict = [s for s in fail_strict if s not in refused_set]
    fail_recs = [r for r in steps if r["step"] in fail]
    actions = [r.get("action", {}).get("action") for r in steps
               if (r.get("action") or {}).get("action")]
    # The same two evidence-quality distinctions the loop's own `summarise` makes (a single
    # source of truth for the rule): a repeated action on a byte-identical frame, or a game
    # already in a declared terminal state, cannot support a game verdict.
    fail_actions = sorted(set((r.get("action") or {}).get("action") for r in fail_recs))
    fail_reqs = sorted(set((r.get("model") or {}).get("request_path") for r in fail_recs))
    fail_frames = sorted(set(r.get("frame_before_sha") for r in fail_recs))
    same_action = bool(len(injected) >= 2 and len(set(actions)) == 1)
    fixed_point = bool(len(fail) >= 2 and len(fail_actions) == 1 and
                       (len(fail_reqs) <= 1 or len(fail_frames) <= 1))
    terminal = any((r.get("markers") or {}).get("GameOver") is True for r in steps)
    # TASK-133 §1.C.1: the model's fixed point, on ITS OWN threshold (>= 3 consecutive
    # steps with the same action AND the same before-frame hash).  It is recorded as its
    # own conclusion beside the game verdict -- never folded into `pass`, because it says
    # nothing about the game.
    mp_fixed = _model_fixed_point_steps(steps, 3)
    # TASK-134 §1.C.1: the wider model-side conclusion.  Computed and REPORTED beside the
    # verdict; it deliberately appears in NO branch below, so `pass` is the rule
    # TASK-132/133 already used, unchanged.
    mp_noprog = _model_no_progress_steps(steps, 3)
    def _decide(margin):
        """The whole TASK-132 rule under ONE margin -> (pass, why).

        `pass` is True / False / None (None = the criterion stays UNMEASURED, exactly as
        TASK-132/133/134 already described it).  Everything that depends on the change
        reading is recomputed; everything that is a statement about the MODEL (fixed point,
        single-action loop, terminal state) is margin-independent by construction.
        """
        ch = changed_strict if margin == "strict" else changed
        fl = fail_strict if margin == "strict" else fail
        rp = real_progress_strict if margin == "strict" else real_progress
        # TASK-139 §1.B: the rates are over the RATED steps (accepted steps that were not a
        # legal refusal), and the floor under the carve-out is checked BEFORE the rate, so a
        # run refused everywhere can never reach the rate comparison.
        rate = (round(len(ch) / float(len(rated)), 4) if rated else None)
        if fl and not fixed_point and not terminal:
            return False, ("%d accepted input(s) left the viewport unchanged under the %s "
                           "margin (the user's FAIL condition): steps %s"
                           % (len(fl), margin, fl))
        if fl and fixed_point:
            return None, ("the FAIL condition occurred on steps %s under the %s margin, but "
                          "every failing step shows the SAME action (%s) and a "
                          "byte-identical frame, so 'the game ignored it' cannot be told "
                          "apart from 'the model stopped playing'"
                          % (fl, margin, fail_actions))
        if fl and terminal:
            return None, ("the FAIL condition occurred on steps %s under the %s margin, but "
                          "the game declared a TERMINAL state, so every later frame is "
                          "frozen by the game's own rule" % (fl, margin))
        if len(injected) < 8:
            return None, ("only %d injected step(s): the rule needs >= 8" % len(injected))
        if mp_fixed.get("found"):
            return None, ("MODEL_FIXED_POINT: %s.  A model-side fixed point is not a game "
                          "defect and is not a PASS; the game criterion stays unmeasured"
                          % mp_fixed.get("reading"))
        if same_action:
            return None, ("the model repeated ONE action over every injected step, so 'the "
                          "game ignored it' cannot be told apart from 'the model stopped "
                          "playing'")
        # -- TASK-139 §1.B: the refusal boundary -------------------------------------------
        if refusal_only_run:
            return False, ("every rated step was a DELIBERATE refusal recorded by the game's "
                           "own counters (steps %s) and no step produced real progress, so "
                           "'all refused' cannot PASS (TASK-139 §1.B)" % refused_steps)
        if len(rp) < int(refusal_boundary.get("min_real_progress_steps", 4)) and refused_recs:
            return None, ("only %d step(s) of REAL progress under the %s margin after the "
                          "legal-refusal carve-out; the boundary needs >= %s"
                          % (len(rp), margin,
                             refusal_boundary.get("min_real_progress_steps", 4)))
        if rate is not None and rate >= 0.75:
            return True, ("%d/%d rated steps changed the picture under the %s margin (%s)"
                          "(%.4f)" % (len(ch), len(rated), margin,
                                      (" with legal refusals %s excluded" % refused_steps)
                                      if refused_steps else "", rate))
        return False, ("accepted-and-changed rate under the %s margin %.4f < 0.75"
                       % (margin, rate or 0.0))

    pass_baseline, why_baseline = _decide("baseline")
    pass_strict, why_strict = _decide("strict")
    criterion = margins.get("default_margin", "strict")
    pass_criterion = pass_strict if criterion == "strict" else pass_baseline
    why_criterion = why_strict if criterion == "strict" else why_baseline
    if pass_criterion is True:
        verdict = "PASS"
    elif criterion == "strict" and pass_baseline is True:
        verdict = "PASS(baseline only)"
    elif pass_criterion is False:
        verdict = "FAIL"
    else:
        verdict = "INCONCLUSIVE"
    out = {"criterion": "MODEL_PLAYER", "what": MODEL_PLAYER_CRITERION_NOTE,
           "game": game, "evidence_source": "runs/model-player/<game>/<backend>/steps.jsonl",
           "steps": len(steps), "injected_steps": len(injected),
           "accepted_steps": len(accepted), "accepted_and_changed": len(changed),
           "rated_denominator": len(rated),
           "accepted_and_changed_rate": (round(len(changed) / float(len(rated)), 4)
                                         if rated else None),
           "fail_steps": fail, "distinct_actions": sorted(set(actions)),
           "one_action_loop": same_action,
           # -- TASK-136 §1.A.1: both readings, and which one is the pass criterion --------
           "change_margin": criterion,
           "change_margin_known": ["baseline", "strict"],
           "change_margin_declaration_source": margins.get("source"),
           "accepted_and_changed_strict": len(changed_strict),
           "accepted_and_changed_rate_strict": (round(len(changed_strict) /
                                                      float(len(rated)), 4)
                                                if rated else None),
           "fail_steps_baseline": fail,
           "fail_steps_strict": fail_strict,
           "pass_baseline": pass_baseline,
           "pass_strict": pass_strict,
           "why_baseline": why_baseline,
           "why_strict": why_strict,
           "verdict": verdict,
           "counts_as_pass": bool(verdict == "PASS"),
           "pass_criterion_reading": (
               "TASK-136 §1.A.1: `pass`/`verdict` use the %r margin.  Only a strict pass is "
               "`PASS`; a run the baseline passes and strict does not is `PASS(baseline "
               "only)` with counts_as_pass=false.  Both readings are reported."
               % criterion),
           "MODEL_FIXED_POINT": bool(mp_fixed.get("found")),
           "model_fixed_point": mp_fixed,
           "MODEL_NO_PROGRESS": bool(mp_noprog.get("found")),
           "model_no_progress": mp_noprog,
           "fail_evidence": {"distinct_actions_in_the_failing_steps": fail_actions,
                             "distinct_request_bodies_in_the_failing_steps": len(fail_reqs),
                             "distinct_before_frames_in_the_failing_steps": len(fail_frames),
                             "same_action_fixed_point": fixed_point},
           "declared_terminal_seen": bool(terminal),
           # -- TASK-139 §1.B: the legal-refusal reading, beside the raw one -----------------
           "refused_steps": refused_steps,
           "refused_step_count": len(refused_recs),
           "rated_steps": [r["step"] for r in rated],
           "rated_step_count": len(rated),
           "rated_and_changed_rate": (round(len(changed) / float(len(rated)), 4)
                                      if rated else None),
           "real_progress_steps": real_progress,
           "real_progress_step_count": len(real_progress),
           "refusal_only_run": refusal_only_run,
           "refusal_boundary": dict(refusal_boundary,
                                    rule=("a step the game's own counters recorded as a "
                                          "deliberate refusal is dropped from the FAIL set and "
                                          "from the rate's denominator, is NEVER counted as "
                                          "progress, and a run must still show >= %s steps of "
                                          "real progress"
                                          % refusal_boundary.get("min_real_progress_steps", 4)),
                                    not_a_loosening=[
                                        "the carve-out can only remove a FAIL the game "
                                        "itself recorded as a refusal",
                                        "it can never turn a 'not changed' into a 'changed'",
                                        "a run refused everywhere cannot PASS",
                                    ]),
           "fail_steps_before_refusal_carve_out": fail_raw,
           "fail_steps_dropped_as_legal_refusals": [s for s in fail_raw
                                                    if s in refused_set],
           "thresholds": {"min_steps": 8, "min_rate": 0.75,
                          "model_fixed_point_min_run": 3,
                          "model_no_progress_min_run": 3,
                          "min_real_progress_steps":
                              refusal_boundary.get("min_real_progress_steps", 4),
                          "window_min_frames": window_decl.get("min_frames", 20),
                          "change_margin": criterion,
                          "strict_gameplay_control_factor":
                              margins["strict"]["gameplay_control_factor"],
                          "strict_gameplay_min_movement":
                              margins["strict"]["gameplay_min_movement"]},
           "pass": pass_criterion, "why": why_criterion}
    # -- TASK-139 §1.A, GATE SIDE: the same window check the loop applies, applied last so
    #    it can take a run out of PASS but never put one in.
    win_steps = []
    for r in steps:
        wb = r.get("frame_budget") or {}
        cb = (r.get("control_diff") or {}).get("frame_budget") or {}
        af = wb.get("action_frames")
        if af is None:
            af = wb.get("achieved_delta")
        w = window_frames_of(cb.get("achieved_delta"), af, window_decl.get("min_frames", 20))
        w["step"] = r.get("step")
        win_steps.append(w)
    short = [w for w in win_steps if w.get("too_short")]
    out["window_frames"] = {
        "declared_by": window_decl.get("declared_by"),
        "min_frames": window_decl.get("min_frames", 20),
        "steps": win_steps,
        "step_count": len(win_steps),
        "too_short_steps": [w["step"] for w in short],
        "too_short_step_count": len(short),
        "state": ("WINDOW_TOO_SHORT" if short else
                  ("ok" if any(w.get("measured") for w in win_steps) else "unmeasured")),
        "rule": ("TASK-139 §1.A: a step whose control or action window spanned fewer than "
                 "the declared `min_frames` drawn frames is WINDOW_TOO_SHORT and the run is "
                 "NOT counted as a PASS"),
    }
    out["window_too_short"] = bool(short)
    out["window_too_short_steps"] = [w["step"] for w in short]
    out["verdict_before_window_check"] = verdict
    if short:
        out["verdict"] = "WINDOW_TOO_SHORT %s" % verdict
        out["counts_as_pass"] = False
        out["pass"] = False
    out["reader_judgement_required"] = True
    out["reader_judgement_note"] = (
        "the machine half above can only say whether the picture moved; the other half of "
        "the TASK-132 PASS condition is a human reading the before/after frames and saying "
        "whether the change is the one the game's rules call for -- it is recorded in the "
        "task's report and is NOT inferable from these numbers")
    return out


def marker_values(state, decl):
    """The X13 timeline sample: the declared marker fields, as of this state read."""
    fields = decl.get("fields") or ["Paused", "GameOver", "Ticks", "Score"]
    node = decl.get("node") or "/root/Main"
    nodes = (state or {}).get("nodes") or {}
    entry = nodes.get(node) or {}
    out = {}
    for f in fields:
        if f in entry:
            out[f] = entry[f]
    for k in ("ms", "drawn", "processed", "physics"):
        if k in (state or {}):
            out[k] = (state or {}).get(k)
    return out


def terminal_conditions_met(state, decl):
    """X10/X13: is the game ALREADY in a declared terminal state at this read?

    `games.<game>.liveness.terminal` is a list of {field, value, means}.  This is the
    snake defect expressed as a criterion: `/root/Main.GameOver == true` at the SETTLE
    frame, i.e. the first picture a player is shown is already the losing screen -- which
    is why 23 captured frames were byte-identical while P2/P3 said "it responded" and
    "it advanced".
    """
    terms = decl.get("terminal") or []
    node = decl.get("node") or "/root/Main"
    entry = ((state or {}).get("nodes") or {}).get(node) or {}
    hit = []
    for t in terms:
        f = t.get("field")
        if f in entry and entry.get(f) == t.get("value"):
            hit.append({"field": f, "value": entry.get(f), "means": t.get("means")})
    return hit


def rect_intersection_area(rect, viewport):
    """Overlap of two [x, y, w, h] rects, clamped at 0.  None when either is missing."""
    if not rect or not viewport:
        return None
    x0 = max(float(rect[0]), float(viewport[0]))
    y0 = max(float(rect[1]), float(viewport[1]))
    x1 = min(float(rect[0]) + float(rect[2]), float(viewport[0]) + float(viewport[2]))
    y1 = min(float(rect[1]) + float(rect[3]), float(viewport[1]) + float(viewport[3]))
    return max(0.0, x1 - x0) * max(0.0, y1 - y0)


def verdict_p7(game, controls, probe):
    """TASK-130 P7: is the DECLARED required UI actually on screen, right now?

    The declaration in `tools/playability_controls.json` says which nodes a player needs
    (a HUD readout, the board container, the next-piece indicator, the food the snake must
    see ...).  This function only compares a runtime read of those nodes (see
    `probe_required_ui_source`) against that declaration, clause by clause:

        exists            the path resolves in the live tree
        class             the node is the declared class
        visible_in_tree   the engine says it is visible (an ancestor being hidden counts)
        alpha             modulate.a is not ~0 (fading to nothing is invisible too)
        on_screen         its global rect overlaps the viewport by >= min_area_px
        text_nonempty     a Label declared to carry text is not blank

    Every check is recorded with the observed value, and `missing` names the items that
    failed -- "which declared thing is gone" is part of the verdict, not a footnote.
    """
    decl, items = required_ui_items(controls, game)
    out = {"pass": False, "criterion": "P7",
           "what": (decl.get("what") or
                    "the UI/controls a player needs on screen must exist and be visible"),
           "declaration_source": os.path.join(HERE, "playability_controls.json"),
           "declaration_rule": decl.get("rule"),
           "declared_items": [i.get("id") or i.get("node") for i in items],
           "items": [], "missing": []}
    if not items:
        out["why"] = ("no `required_ui.items` declaration for this game: nothing states "
                      "which UI a player needs, so 'the required UI is present' cannot be "
                      "claimed (same rule as P6's capability table)")
        return out
    if not isinstance(probe, dict) or not probe.get("items"):
        out["why"] = ("the runtime required-UI probe produced no answer, so the "
                      "declaration was not checked: %s"
                      % ((probe or {}).get("error") or "no probe result"))
        out["probe_error"] = (probe or {}).get("error")
        return out
    viewport = probe.get("viewport")
    out["probe_source"] = probe.get("source")
    out["root"] = probe.get("root")
    out["viewport"] = viewport
    seen = probe.get("items") or {}

    for it in items:
        path = it.get("node")
        iid = it.get("id") or path
        obs = seen.get(path) or {"path": path, "exists": False}
        checks = []

        def add(name, ok, why):
            checks.append({"check": name, "pass": bool(ok), "why": why})

        exists = bool(obs.get("exists"))
        add("exists", exists,
            ("the node is at %s" % path) if exists else "no node at %s in the live tree" % path)
        if exists:
            want_class = it.get("class")
            if want_class:
                got = obs.get("class")
                add("class", got == want_class,
                    "class is %r (declared %r)" % (got, want_class))
            if it.get("must_be_visible", True):
                vit = bool(obs.get("visible_in_tree"))
                hidden = obs.get("hidden_by_ancestors") or []
                add("visible_in_tree", vit,
                    ("is_visible_in_tree() is true (own visible=%s)" % obs.get("visible"))
                    if vit else
                    ("is_visible_in_tree() is false (own visible=%s; hidden by %s)"
                     % (obs.get("visible"), hidden or "the node itself")))
                alpha = obs.get("modulate_a")
                if isinstance(alpha, (int, float)):
                    add("alpha", alpha > P7_MIN_ALPHA,
                        "modulate.a = %.4f (must be > %.4f)" % (alpha, P7_MIN_ALPHA))
            min_area = it.get("min_area_px")
            if min_area:
                area = rect_intersection_area(obs.get("global_rect") or obs.get("rect"),
                                              viewport)
                add("on_screen", (area is not None) and area >= float(min_area),
                    "the part of its rect inside the viewport is %s px^2 (declared >= %s), "
                    "rect=%s" % (None if area is None else round(area, 1), min_area,
                                 obs.get("global_rect")))
            min_size = it.get("min_size_px")
            if min_size:
                size = obs.get("size") or [0, 0]
                add("size", size[0] >= min_size[0] and size[1] >= min_size[1],
                    "size is %s (declared >= %s)" % (size, min_size))
            if it.get("text_nonempty"):
                text = obs.get("text")
                add("text_nonempty", bool(text and str(text).strip()),
                    "text is %r" % (text,))
            if it.get("text_regex"):
                text = obs.get("text") or ""
                add("text_regex", re.search(it["text_regex"], str(text)) is not None,
                    "text %r against regex %r" % (text, it["text_regex"]))
        failed = [c for c in checks if not c["pass"]]
        row = {"id": iid, "need": it.get("need"), "node": path,
               "declared_class": it.get("class"),
               "declared_min_area_px": it.get("min_area_px"),
               "pass": not failed and exists,
               "observed": {k: obs.get(k) for k in
                            ("exists", "class", "visible", "visible_in_tree", "modulate_a",
                             "global_rect", "size", "text", "hidden_by_ancestors")},
               "checks": checks}
        if failed or not exists:
            row["failed_checks"] = [c["check"] for c in failed]
            out["missing"].append({"id": iid, "need": it.get("need"), "node": path,
                                   "failed_checks": row["failed_checks"],
                                   "why": "; ".join(c["why"] for c in failed)})
        out["items"].append(row)

    ok = sum(1 for r in out["items"] if r["pass"])
    out["pass"] = bool(ok == len(out["items"]))
    if out["pass"]:
        out["why"] = ("all %d declared UI item(s) are present, visible and on screen: %s"
                      % (len(out["items"]), ", ".join(r["id"] for r in out["items"])))
    else:
        out["why"] = ("%d/%d declared UI item(s) are NOT usable: %s"
                      % (len(out["items"]) - ok, len(out["items"]),
                         "; ".join("%s -> %s" % (m["id"], ",".join(m["failed_checks"]))
                                   for m in out["missing"])))
    return out


def verdict_p6(game, controls, tested):
    caps = (controls.get(game) or {}).get("capabilities") or []
    if not caps:
        return {"pass": False,
                "why": "no capability table entry: nothing states what a player must be "
                       "able to do in this game, so 'playable' cannot be claimed",
                "capabilities": []}
    by_action = {t["action"]: t for t in tested}
    rows = []
    ok = 0
    for cap in caps:
        action = cap.get("action")
        observable = cap.get("observable") or ""
        t = by_action.get(action)
        if not action:
            rows.append({"need": cap.get("need"), "action": None, "pass": False,
                         "why": "no declared action delivers this capability"})
            continue
        if t is None:
            rows.append({"need": cap.get("need"), "action": action, "pass": False,
                         "why": "the action is not in the game's InputMap"})
            continue
        if not t.get("responds"):
            rows.append({"need": cap.get("need"), "action": action, "pass": False,
                         "why": "injecting it changed nothing beyond the no-input control"})
            continue
        keys = []
        for ch in (t.get("channels") or {}).values():
            for k in ((ch.get("action") or {}).get("state_changes") or []):
                keys.append(k.get("key") or "")
        # `observable` may offer alternatives separated by '|': a turn-based game
        # legitimately refuses a move (a wall, the board edge, an illegal
        # direction), and the refusal is recorded in its own exported counter --
        # "the key did something" stays true either way.
        wanted = [w for w in (observable or "").split("|") if w]
        hit = [k for k in keys if any(w in k for w in wanted)]
        if wanted and not hit:
            rows.append({"need": cap.get("need"), "action": action, "pass": False,
                         "why": "the action responds, but none of `%s` moved; changed: %s"
                                % (observable, keys[:6])})
            continue
        ok += 1
        rows.append({"need": cap.get("need"), "action": action, "pass": True,
                     "why": ("`%s` moved %s" % (observable, hit[:3])) if hit
                     else "`%s` responds" % action})
    return {"pass": ok == len(caps), "why": "%d/%d required capabilities are delivered by a "
                                            "declared, responding action"
                                            % (ok, len(caps)),
            "goal": (controls.get(game) or {}).get("goal"),
            "capabilities": rows}


def verdicts(game, gate, proj, frames, s0, s1, s_end, controls=None):
    controls = controls or {}
    crit = {}
    decl = gameplay_declaration(controls, game)

    # ---- P1 -----------------------------------------------------------------
    usable = [f for f in frames if f.get("ok")]
    # P1 is judged on the frames taken BEFORE any input was injected, so the
    # verdict answers "what does a player see when the game comes up", not "what
    # does it look like after our own probe poked it".
    settled = [f for f in usable
               if f.get("label") == "settle" or f.get("label", "").startswith("auto")]
    pool = settled or usable
    if pool:
        best = max(pool, key=lambda f: f.get("content_fraction", 0) or 0)
        worst = min(pool, key=lambda f: f.get("content_fraction", 0) or 0)
        cf = best.get("content_fraction", 0) or 0
        bc = best.get("bbox_coverage", 0) or 0
        flat = (best.get("content_pixels", 0) or 0) == 0
        # TASK-131 X14: `bbox_fill` is the FILL fraction of the content bounding box, and
        # it is recorded -- not judged -- because the snake frame scored 33% bbox_coverage
        # from two specks in opposite corners (fill 1.8%), while rtype -- a legitimate
        # sparse shooter -- has a 95.6% span with only 1.1% fill.  A span threshold cannot
        # separate those, so the threshold that decides is the content fraction alone.
        bb = best.get("bbox") or [0, 0, 0, 0]
        bbox_area = max(1, (bb[2] or 0) * (bb[3] or 0))
        fill = round(((best.get("content_pixels", 0) or 0) / float(bbox_area)), 6)
        p1_pass = (not flat) and cf >= P1_MIN_CONTENT_FRACTION and bc >= P1_MIN_BBOX_COVERAGE
        why = "best frame #%s: content %.4f%% (>=%.2f%%), bbox coverage %.4f%% (>=%.2f%%), " \
              "bbox=%s, bbox_fill %.3f%% (recorded, NOT a threshold), bg=%s" % (
                  best.get("index"), 100.0 * cf, 100.0 * P1_MIN_CONTENT_FRACTION,
                  100.0 * bc, 100.0 * P1_MIN_BBOX_COVERAGE, best.get("bbox"),
                  100.0 * fill, best.get("background_rgb"))
        if flat:
            why = "the frame is a single flat colour (0 content pixels): %s" % why
        crit["P1"] = {"pass": bool(p1_pass), "why": why,
                      "best_frame": frame_evidence(best),
                      "worst_frame": frame_evidence(worst),
                      "thresholds": {"min_content_fraction": P1_MIN_CONTENT_FRACTION,
                                     "min_bbox_coverage": P1_MIN_BBOX_COVERAGE,
                                     "pixel_delta": PIXEL_DELTA,
                                     "bbox_fill_is_recorded_not_judged": True},
                      "bbox_fill_of_best_frame": fill,
                      # only the frames that were taken *before* any input, so this
                      # list stays readable instead of repeating every action's
                      # before-frame five times over
                      "settled_frames": [
                          frame_evidence(f) for f in pool
                          if f.get("label", "") in ("settle",)
                          or f.get("label", "").startswith("auto")]}
    else:
        crit["P1"] = {"pass": False, "why": "no frame could be captured at all"}

    # ---- P2 / P5 ------------------------------------------------------------
    # TASK-131 X12: an action "responds" only when it moves a declared GAMEPLAY
    # observable past its own no-input control window, or moves pixels past it.  Any
    # other change is an input acknowledgement (`LastRefusedInput`, `InputMoves`), a
    # clock (`Ticks`, `Elapsed`), an intent index (`DirectionX`, `AngleIndex`) or a mode
    # flag (`Paused`) and is reported as `meta_only`.
    tested = gate.get("actions_tested") or []
    refdecl = refusal_declaration(controls, game)
    for a in tested:
        ev = arm_evidence((a.get("channels") or {}).get("parse") or {}, decl,
                          refusal_decl=refdecl)
        a["gameplay_evidence"] = ev
        a["responds_gameplay"] = ev["responds"]
        a["refused"] = ev["refused"]
        a["responds_meta_only"] = ev["meta_only"]
    responded = [a for a in tested if a.get("responds_gameplay")]
    refused = [a for a in tested if a.get("refused")]
    intent_only = [a for a in tested
                   if not a.get("responds_gameplay") and not a.get("refused")]
    mismatched = [a for a in tested if a.get("mismatch")]
    suspicious = [a for a in tested if a.get("suspicious_mismatch")]
    if not tested:
        crit["P2"] = {"pass": False, "why": "there was no declared action to inject"}
    else:
        # TASK-131: every action must move a declared GAMEPLAY observable (or pixels) past
        # its own no-input control, or be a refusal the GAME ITSELF recorded; AND at least
        # one action must really have moved something.  The second half is what keeps
        # "everything was refused because the game is already over" (snake: `GameOver` at
        # the settle frame; game2048: an empty board every move says `no_change` about)
        # from passing on refusals alone.
        p2 = (len(intent_only) == 0) and bool(responded)
        crit["P2"] = {
            "pass": bool(p2),
            "why": "%d/%d declared actions moved a DECLARED GAMEPLAY observable (or pixels) "
                   "past their own no-input control window through the faithful channel "
                   "(`Input.parse_input_event`, the path a real key press takes); %d were "
                   "accepted as deliberate REFUSALS recorded by the game itself (%s); %d were "
                   "META-ONLY or INTENT-ONLY and count for nothing (%s).  Declared gameplay "
                   "observables: %s%s"
                   % (len(responded), len(tested), len(refused),
                      ", ".join("%s: %s" % (a.get("action"),
                                            (a.get("gameplay_evidence") or {})
                                            .get("refusal_evidence")) for a in refused)
                      or "-",
                      len(intent_only),
                      ", ".join("%s (%s)" % (
                          a.get("action"),
                          "meta-only" if a.get("responds_meta_only") else "no change at all")
                          for a in intent_only) or "-",
                      (decl.get("items") or []),
                      "" if responded else "  *** NO action moved anything: the game was "
                                           "never shown to play ***"),
            "actions": [{k: a.get(k) for k in ("action", "key", "responds",
                                               "responds_gameplay", "refused",
                                               "responds_meta_only",
                                               "responds_to_real_key",
                                               "responds_to_push_input_only",
                                               "responds_to_action_state_only",
                                               "suspicious_mismatch")}
                        for a in tested],
            "gameplay_evidence": [{"action": a.get("action"),
                                   **(a.get("gameplay_evidence") or {})}
                                  for a in tested],
            "meta_only_actions": [a.get("action") for a in intent_only
                                  if a.get("responds_meta_only")],
            "intent_only_actions": [a.get("action") for a in intent_only],
            "refused_actions": [a.get("action") for a in refused],
            "actions_that_moved_gameplay": [a.get("action") for a in responded],
            "requires_at_least_one_gameplay_response": True,
            "declaration_source": os.path.join(HERE, "playability_controls.json"),
            "declaration_keys": ["games.%s.gameplay_observables" % game,
                                 "games.%s.refusal_evidence" % game],
            "declared_gameplay_observables": (decl.get("items") or []),
            "refusal_declaration": refdecl,
            "channel_mismatches": [a["action"] for a in tested if a.get("suspicious_mismatch")],
            "suspicious_action_only_mismatches": [a["action"] for a in tested
                                                  if a.get("suspicious_mismatch")],
            "frames_budget": P2_FRAMES,
            "channels": {
                "parse": "Input.parse_input_event -- sets InputMap action state AND dispatches "
                         "to the viewport: what the display server does for a real key press",
                "push_input": "Viewport.push_input -- dispatch only (diagnostic, run on failure)",
                "action": "Input.action_press -- action state only (diagnostic, run on failure)",
            },
        }

    # ---- P3 -----------------------------------------------------------------
    # TASK-131 X12: `frames_drawn` is necessary and NOT sufficient.  The rendering loop
    # running is not the game advancing; a game that is over, frozen or waiting forever
    # still draws frames.  P3 now requires gameplay progress, and names where it came
    # from -- and it fails outright when the game was ALREADY in a declared terminal
    # state at the settle frame (X13's liveness declaration).
    drawn = []
    if isinstance(s0, dict):
        drawn.append(s0.get("drawn"))
    for st in (s1, s_end):
        if isinstance(st, dict):
            drawn.append(st.get("drawn"))
    drawn = [d for d in drawn if isinstance(d, int)]
    loop_advanced = len(drawn) >= 2 and drawn[-1] > drawn[0]
    auto_delta = state_delta(s0, s1) if isinstance(s0, dict) and isinstance(s1, dict) else []
    post_delta = state_delta(s0, s_end) if isinstance(s0, dict) and isinstance(s_end, dict) else []
    pixel_auto = 0
    for f in frames:
        if f.get("label", "").startswith("auto") or f.get("label", "").startswith("post"):
            pixel_auto = max(pixel_auto, f.get("changed_pixels_vs_prev") or 0)
    input_delta_count = 0
    for a in tested:
        for ch in (a.get("channels") or {}).values():
            input_delta_count += ((ch.get("action") or {}).get("state_change_count") or 0)
    auto_gameplay = gameplay_changes(auto_delta, decl) + gameplay_changes(post_delta, decl)
    autonomous_evidence = bool(auto_gameplay) or pixel_auto >= P3_MIN_CHANGED_PIXELS
    input_gameplay = [a.get("action") for a in tested
                      if (a.get("gameplay_evidence") or {}).get("gameplay_wins")]
    input_evidence = bool(input_gameplay) or any(
        (a.get("gameplay_evidence") or {}).get("pixel_wins") for a in tested)
    liveness = gate.get("settle_liveness") or {}
    terminal = liveness.get("terminal_conditions_met") or []
    declares_liveness = bool(liveness.get("declared"))
    p3_pass = (loop_advanced and not terminal
               and (autonomous_evidence or input_evidence))
    reasons = []
    if not loop_advanced:
        reasons.append("the render loop did not advance (frames_drawn %s -> %s)"
                       % (drawn[0] if drawn else None, drawn[-1] if drawn else None))
    if terminal:
        reasons.append("the game is ALREADY in a declared terminal state at the settle "
                       "frame (%s), so nothing it draws afterwards can be progress"
                       % json.dumps(terminal, ensure_ascii=False))
    if not (autonomous_evidence or input_evidence):
        reasons.append("no declared gameplay observable moved and no frame-to-frame pixel "
                       "change >= %d px was seen, in the no-input frames OR during the "
                       "input round" % P3_MIN_CHANGED_PIXELS)
    crit["P3"] = {
        "pass": bool(p3_pass),
        "why": "frames_drawn %s -> %s (advanced=%s); gameplay progress: autonomous=%s "
               "(from %s / pixel %d), input-round=%s (from %s); declared terminal at "
               "settle=%s; state changes seen during the input round=%d (of which "
               "gameplay=%d); %s"
               % (drawn[0] if drawn else None, drawn[-1] if drawn else None,
                  loop_advanced, autonomous_evidence,
                  [c.get("key") for c in auto_gameplay][:8], pixel_auto,
                  input_evidence, input_gameplay, bool(terminal), input_delta_count,
                  len(gameplay_changes([c for a in tested
                                        for ch in (a.get("channels") or {}).values()
                                        for c in ((ch.get("action") or {})
                                                  .get("state_changes") or [])], decl)),
                  "; ".join(reasons) if reasons else "progress was demonstrated"),
        "required": "loop advanced AND gameplay progress AND not already terminal at settle",
        "frames_drawn_samples": drawn,
        "autonomous_state_changes": auto_delta[:15],
        "autonomous_change_count": len(auto_delta),
        "autonomous_gameplay_changes": [c.get("key") for c in auto_gameplay][:15],
        "total_state_changes_since_settle": post_delta[:15],
        "total_change_count": len(post_delta),
        "max_pixel_change_autonomous": pixel_auto,
        "gameplay_progress": {"autonomous_evidence": autonomous_evidence,
                              "input_round_evidence": input_evidence,
                              "actions_with_gameplay_evidence": input_gameplay},
        "settle_liveness": liveness,
        "action_side_effects": gate.get("action_side_effects") or {},
        "marker_timeline": marker_timeline(frames),
    }

    # ---- P4 -----------------------------------------------------------------
    p4 = gate.get("p4") or {}
    if not p4:
        crit["P4"] = {"pass": False, "why": "the process health probe did not run"}
    else:
        dialogs = p4.get("modal_candidates") or []
        mcp_err = [e for e in (p4.get("mcp_errors") or [])
                   if "timeout" in json.dumps(e).lower() or "timed out" in json.dumps(e).lower()]
        p4_pass = bool(p4.get("alive_at_end")) and not dialogs and not mcp_err
        why = "process alive at end=%s; visible windows of the tree=%d; modal dialog candidates=%d; " \
              "MCP timeouts=%d" % (p4.get("alive_at_end"),
                                   len(p4.get("own_visible_windows") or []), len(dialogs),
                                   len(mcp_err))
        crit["P4"] = {"pass": bool(p4_pass), "why": why,
                      "alive_at_end": p4.get("alive_at_end"),
                      "modal_candidates": dialogs,
                      "mcp_timeouts": mcp_err,
                      "error_count": len(gate.get("errors") or []),
                      "errors": (gate.get("errors") or [])[:8]}
        if not p4.get("alive_at_end"):
            # find out why: the engine's own last words
            gdir = os.path.join(RUNS, gate.get("game", ""))
            out = read_text(os.path.join(gdir, "engine-game.stdout.txt"))
            err = read_text(os.path.join(gdir, "engine-game.stderr.txt"))
            crit["P4"]["engine_tail"] = {"stdout": out[-1500:], "stderr": err[-1500:]}

    # ---- P5 -----------------------------------------------------------------
    audit = gate.get("static_audit") or {}
    declared = proj["actions_declared"]
    claimed = proj["readme_key_claims"]
    unknown_claims = [c for c in claimed if not c["known"]]
    unverified = [a["action"] for a in tested if not a.get("responds")]
    untested = [a for a in declared if a not in [t["action"] for t in tested]]
    undeclared_used = audit.get("used_but_undeclared") or []
    dead_declared = audit.get("declared_but_never_referenced") or []
    dead_declared_direct = audit.get("declared_but_never_read") or []
    documented_keys = set(keycode_of(k) for k in proj["readme_keys"])
    undocumented_actions = []
    for a in declared:
        kcs = [c for c in proj["actions"][a]["keycode"] if c]
        if not any(c in documented_keys for c in kcs):
            undocumented_actions.append(a)
    p5_pass = (bool(claimed) and not unknown_claims and not unverified
               and not untested and not undeclared_used and not dead_declared)
    why = ("README documents %d keys (%s); the InputMap declares %d actions; the code "
           "reads %d actions it does NOT declare (%s); %d declared actions the code never "
           "reads (%s); %d tested actions do nothing (%s); %d never exercised (%s); "
           "README keys with no declared action: %s"
           % (len(claimed), proj["readme_keys"], len(declared), len(undeclared_used),
              undeclared_used, len(dead_declared), dead_declared, len(unverified),
              unverified, len(untested), untested, [c["key"] for c in unknown_claims]))
    if not claimed:
        why = ("the README documents no controls at all (no '## 玩法' section): a human "
               "cannot discover how to play. " + why)
    crit["P5"] = {"pass": bool(p5_pass), "why": why,
                  "readme_keys": proj["readme_keys"],
                  "readme_claim_details": claimed,
                  "declared_actions": declared,
                  "declared_action_keys": {a: proj["actions"][a]["keys"] for a in declared},
                  "actions_documented_in_readme": sorted(set(declared) - set(undocumented_actions)),
                  "declared_actions_not_documented": undocumented_actions,
                  "actions_read_by_the_code": audit.get("actions_read_by_the_code"),
                  "actions_referenced_by_the_code": audit.get("actions_referenced_by_the_code"),
                  "actions_read_but_not_declared": undeclared_used,
                  "undeclared_action_sites": audit.get("undeclared_sites"),
                  "declared_actions_the_code_never_reads": dead_declared,
                  "declared_actions_with_no_direct_IsAction_call": dead_declared_direct,
                  "actions_with_no_effect": unverified,
                  "actions_never_exercised": untested,
                  "readme_keys_without_an_action": [c["key"] for c in unknown_claims],
                  "readme_play_section": proj.get("readme_play_section")}

    # ---- P6: does the game let a human actually do the things it is about? ----
    crit["P6"] = verdict_p6(game, controls or {}, tested)

    # ---- P7: is the DECLARED required UI present, visible and on screen? (TASK-130)
    # Machine-read from the live tree by the probe run just after the settle frame; this
    # is the criterion for the failure mode P1..P6 are blind to (the interface is gone,
    # the game is not).  Its evidence travels with the gate: gate["p7_probe"] holds the
    # raw node read the verdict was computed from.
    crit["P7"] = verdict_p7(game, controls or {}, gate.get("p7_probe"))
    return crit


def marker_timeline(frames):
    """TASK-131 X13: every captured frame with the marker values it was taken at.

    This is the artifact that answers "was this static frame legal?": `Paused`, the clock
    fields, `Ticks` and the score are recorded beside each frame, so a reader can see
    that (for example) frames 1..19 of snake were static while `GameOver=true`, and that
    the gate's own `snake_pause` turned `Paused` on at frame 19.
    """
    out = []
    for f in frames or []:
        if not f.get("path"):
            continue
        out.append({"index": f.get("index"), "label": f.get("label"),
                    "file": os.path.basename(f.get("path") or ""),
                    "sha256": f.get("sha256"),
                    "changed_pixels_vs_prev": f.get("changed_pixels_vs_prev"),
                    "markers": f.get("markers")})
    return out


def frame_evidence(f):
    return {"index": f.get("index"), "label": f.get("label"),
            "file": os.path.basename(f.get("path", "")),
            "width": f.get("width"), "height": f.get("height"),
            "window": f.get("window"), "content_fraction": f.get("content_fraction"),
            "bbox": f.get("bbox"), "bbox_coverage": f.get("bbox_coverage"),
            "background_rgb": f.get("background_rgb"),
            "changed_pixels_vs_prev": f.get("changed_pixels_vs_prev"),
            "sha256": f.get("sha256"),
            "markers": f.get("markers")}


# ---------------------------------------------------------------------------
# the static P5 audit across all games (runs even when a game is not launched)
# ---------------------------------------------------------------------------
def audit_one(g):
    """The static half of P5 for one game: declared actions vs the ones the code reads."""
    proj = parse_project(g)
    src = []
    for dirpath, _dn, fns in os.walk(os.path.join(project_dir(g), "src")):
        for fn in fns:
            if fn.endswith(".cs"):
                src.append(os.path.join(dirpath, fn))
    declared = proj["actions_declared"]
    used = {}
    referenced = {}
    # Two strengths, and they are reported separately because they are not the same
    # claim:
    #   `read`      -- the action name is the literal argument of an
    #                  `IsAction*(...)` call.  This is the direct evidence.
    #   `referenced`-- the action name appears as a string literal somewhere in the
    #                  game's own C# (e.g. it is passed to a helper that then calls
    #                  `Input.IsActionPressed(helperArg)`).  Indirect, but it still
    #                  means the action is not dead.
    # Both spellings of the call are the same call on different receivers:
    #   Input.IsActionPressed("x")   (polling)  /  @event.IsActionPressed("x")  (_Input)
    for p in src:
        txt = read_text(p)
        fname = os.path.basename(p)
        for i, line in enumerate(txt.splitlines(), 1):
            for m in re.finditer(r'IsAction(?:Pressed|JustPressed|JustReleased|Released)'
                                 r'\(\s*"([^"]+)"', line):
                site = "%s:%d" % (fname, i)
                used.setdefault(m.group(1), [])
                if site not in used[m.group(1)]:
                    used[m.group(1)].append(site)
            for m in re.finditer(r'"([A-Za-z0-9_]{2,40})"', line):
                name = m.group(1)
                if name in declared:
                    site = "%s:%d" % (fname, i)
                    referenced.setdefault(name, [])
                    if site not in referenced[name]:
                        referenced[name].append(site)
    for a in used:
        referenced[a] = sorted(set(referenced.get(a, [])) | set(used[a]))
    return {
        "game": g,
        "declared_viewport": proj["declared_viewport"],
        "declared_actions": declared,
        "declared_action_keys": {a: proj["actions"][a]["keys"] for a in declared},
        "actions_read_by_the_code": sorted(used),
        "actions_referenced_by_the_code": sorted(referenced),
        "used_but_undeclared": sorted(a for a in used if a not in declared),
        "undeclared_sites": {a: used[a] for a in used if a not in declared},
        "declared_but_never_read": sorted(a for a in declared if a not in used),
        "declared_but_never_referenced": sorted(a for a in declared if a not in referenced),
        "readme_keys": proj["readme_keys"],
        "readme_has_play_section": proj.get("readme_play_section") is not None,
        "readme_key_claims": proj["readme_key_claims"],
    }


def static_audit(games):
    return [audit_one(g) for g in games]


# ---------------------------------------------------------------------------
# reports
# ---------------------------------------------------------------------------
CRITERIA_ORDER = ("P1", "P2", "P3", "P4", "P5", "P6", "P7")


def criteria_verdict(crit):
    """The overall verdict over the criteria that are PRESENT.

    TASK-130 added P7 and, with it, `--only-p7` runs whose gate.json carries P7 alone.
    Judging such a run against absent P1..P6 would report a failure that was never
    measured, so what the run covered is stated next to the verdict instead.
    """
    present = [k for k in CRITERIA_ORDER if k in (crit or {})]
    if not present:
        return "unjudged", []
    ok = all((crit.get(k) or {}).get("pass") for k in present)
    return ("playable" if ok else "not_playable"), present


def write_reports(gates, audit, args):
    all_games = [g["game"] for g in gates]
    summary = {"task": "TASK-116", "generated": time.strftime("%Y-%m-%d %H:%M:%S"),
               "tool": "tools/playability_gate.py",
               "engine": ENGINE,
               "target_mode": "exported-exe" if EXE_ROOT else "project",
               "exe_root": EXE_ROOT, "out_root": RUNS,
               "criteria_thresholds": {
                   "P1_min_content_fraction": P1_MIN_CONTENT_FRACTION,
                   "P1_min_bbox_coverage": P1_MIN_BBOX_COVERAGE,
                   "P1_pixel_delta": PIXEL_DELTA,
                   "P2_frames": P2_FRAMES,
                   "P3_min_changed_pixels": P3_MIN_CHANGED_PIXELS,
                   # TASK-130 P7: the only threshold is the alpha floor; the per-item
                   # area/class/text requirements come from the game's own declaration.
                   "P7_min_alpha": P7_MIN_ALPHA},
               "games": [], "static_audit": audit,
               # TASK-124 C: the model-in-the-loop thresholds are configurable and
               # explicitly UNCALIBRATED; copied into the summary so a verdict is never
               # separated from the numbers that produced it.
               "agent_thresholds": load_agent_thresholds(),
               # TASK-129 C: the VISION backend's own block, independent of Jev's.
               "playjev_thresholds": load_playjev_thresholds(),
               "visual_agent": getattr(args, "visual_agent", "") or None,
               "token_estimator": {"name": "jev_estimate_tokens (TASK-129 D-C)",
                                   "safety_factor": JEV_TOKEN_SAFETY_FACTOR,
                                   "agent_state_budget": getattr(args, "agent_state_budget", 0),
                                   "bridge": "budget 2000 (TASK-129) == budget 800 (TASK-128)"},
               "agent_state_samples": getattr(args, "agent_state_samples", 3)}
    for g in gates:
        crit = g.get("criteria") or {}
        pj = g.get("playjev") or {}
        verdict, covered = criteria_verdict(crit)
        summary["games"].append({
            "game": g["game"],
            "target": g.get("target"),
            "verdict": verdict,
            # TASK-130: which criteria this run actually measured (a --only-p7 run covers
            # P7 and says so, rather than being read as a P1..P6 failure).
            "criteria_covered": covered,
            "criteria_scope": g.get("criteria_scope"),
            # TASK-129 D-B: how many INDEPENDENT model observations this game produced.
            "agent_sample_size": ((g.get("agent") or {}).get("sample_size")),
            "agent_sample_size_required": ((g.get("agent") or {}).get("sample_size_required")),
            "agent_aggregate": (None if not (g.get("agent") or {}).get(
                "aggregate_over_observations") else {
                "rule": (g["agent"]["aggregate_over_observations"] or {}).get("rule"),
                "min_over_observations": (g["agent"]["aggregate_over_observations"] or {}
                                          ).get("min_over_observations"),
                "threshold": (g["agent"]["aggregate_over_observations"] or {}).get("threshold"),
                "pass": (g["agent"]["aggregate_over_observations"] or {}).get("pass")}),
            "playjev": (None if not pj else {
                "playable_values": pj.get("playable_values"),
                "playable_distribution": pj.get("playable_distribution"),
                "verdict": pj.get("verdict"),
                "frames_used": [f.get("file") for f in (pj.get("frames_used") or [])],
                "frames_used_sha256": [f.get("sha256") for f in (pj.get("frames_used") or [])],
                "thresholds": pj.get("thresholds"),
                "score_in_decision_path": pj.get("score_in_decision_path"),
                "score_observation_values": (pj.get("score_observation") or {}).get("per_frame"),
                "legend_probe": (None if not pj.get("legend_probe") else {
                    "score_with_flipped_legend":
                        pj["legend_probe"].get("score_with_flipped_legend"),
                    "in_decision_path": False}),
                "errors": pj.get("errors"),
            }),
            "criteria": {k: dict({"pass": (crit.get(k) or {}).get("pass"),
                                  "why": (crit.get(k) or {}).get("why")},
                                 **({"capabilities": (crit.get(k) or {}).get("capabilities"),
                                     "goal": (crit.get(k) or {}).get("goal")}
                                    if k == "P6" else {}),
                                 **({"declared_items": (crit.get(k) or {}).get("declared_items"),
                                     "missing": (crit.get(k) or {}).get("missing"),
                                     "items": (crit.get(k) or {}).get("items")}
                                    if k == "P7" else {}))
                         for k in CRITERIA_ORDER},
            "window": (g.get("window") or {}),
            "window_conformance": g.get("window_conformance"),
            "tools_list_count": g.get("tools_list_count"),
            "startup": g.get("startup"),
            "seconds": g.get("seconds"),
            "frames": [{"file": "frames/" + os.path.basename(f.get("path") or f.get("file") or ""),
                        "index": f.get("index"), "label": f.get("label"),
                        "width": f.get("width"), "height": f.get("height"),
                        "content_fraction": f.get("content_fraction"),
                        "bbox": f.get("bbox"),
                        "changed_pixels_vs_prev": f.get("changed_pixels_vs_prev"),
                        "sha256": f.get("sha256")} for f in g.get("frames", [])
                       if (f.get("path") or f.get("file"))],
            "actions": g.get("actions_tested"),
            "filmstrip": os.path.join(RUNS, g["game"], "filmstrip.png"),
            "gate_json": os.path.join(RUNS, g["game"], "gate.json"),
        })
    summary["totals"] = {
        "games": len(gates),
        "playable": sum(1 for x in summary["games"] if x["verdict"] == "playable"),
        "not_playable": sum(1 for x in summary["games"] if x["verdict"] != "playable"),
        "criteria_covered": sorted(set(k for x in summary["games"]
                                       for k in (x["criteria_covered"] or []))),
        "per_criterion_fail": {k: sum(1 for x in summary["games"]
                                      if k in (x["criteria_covered"] or [])
                                      and not (x["criteria"].get(k) or {}).get("pass"))
                               for k in CRITERIA_ORDER},
        "per_criterion_measured": {k: sum(1 for x in summary["games"]
                                          if k in (x["criteria_covered"] or []))
                                   for k in CRITERIA_ORDER},
    }
    write_json(os.path.join(RUNS, "playability.json"), summary)
    with io.open(os.path.join(RUNS, "summary.txt"), "w", encoding="utf-8") as fh:
        fh.write("\n".join(_LOG))
    return summary


def main(argv=None):
    ap = argparse.ArgumentParser(description="TASK-116 playability gate")
    ap.add_argument("--games", nargs="*", default=[])
    ap.add_argument("--all", action="store_true")
    ap.add_argument("--calibrate", action="store_true",
                    help="run the frames/metrics only; no verdict report is trusted")
    ap.add_argument("--agent", default="scripted",
                    help="scripted | openai | jev | playjev | none.  `jev` is "
                         "NeoHorse-Jev's native structured-decision protocol (TASK-124): "
                         "root URL in PLAYTEST_BASE_URL, GET /health readiness, POST "
                         "/v1/systemone (or --decision-path /v1/decision).  `playjev` is "
                         "PlayJev 0.8B's image-state server (TASK-127): the same "
                         "endpoint name but `state.frames` instead of a text state, "
                         "choice questions only, one image + N questions allowed, and an "
                         "abstain is never a pass.  `openai` is only for a model that "
                         "really speaks OpenAI chat-completions.")
    ap.add_argument("--agent-steps", type=int, default=2)
    ap.add_argument("--agent-state-samples", type=int, default=3,
                    help="TASK-129 D-B: how many HASH-DIFFERENT states to hand the agent, "
                         "one per call (default 3).  TASK-128 handed the same state to all "
                         "three calls, so every game had one independent observation; when "
                         "fewer than this many distinct states can be sampled the run "
                         "records `sample_size: 1` instead of pretending.")
    ap.add_argument("--max-state-retries", type=int, default=2,
                    help="TASK-129 D-C: how many times a REAL HTTP 422 "
                         "(`state exceeds N tokens`) may be answered by halving the state "
                         "and re-POSTing.  Bounded; every retry is recorded in "
                         "agent.json -> report.calls[*].state_budget_retries.")
    ap.add_argument("--visual-agent", default="",
                    help="TASK-129 C: a SECOND backend that judges the captured FRAMES "
                         "(only `playjev` is implemented).  It runs beside --agent, writes "
                         "gate[\"playjev\"] next to gate[\"agent\"], asks ONE image + N "
                         "choice questions per request, and its `score` answer is recorded "
                         "as a direction-suspect observation that is NOT in the decision "
                         "path (D-E).")
    ap.add_argument("--playjev-base-url", default="",
                    help="TASK-129: the PlayJev service root for --visual-agent=playjev.  "
                         "Empty falls back to PLAYTEST_PLAYJEV_BASE_URL / PLAYJEV_BASE_URL, "
                         "then to playtest_agent's default http://127.0.0.1:8081.")
    ap.add_argument("--visual-frames", type=int, default=3,
                    help="TASK-129: how many of the pre-input frames (settle + auto*) the "
                         "vision backend judges; one request per frame, one image + N "
                         "questions per request.")
    ap.add_argument("--playjev-invariant-questions", type=int, default=3,
                    help="TASK-129: how many invariant Choice questions to ask per frame. "
                         "The FIRST is always `playable`; the others are the remaining jev "
                         "invariants and are recorded as observations, not criteria.")
    ap.add_argument("--playjev-abstain-min-confidence", type=float, default=0.0,
                    help="TASK-129: a `playable` confidence below this is recorded as an "
                         "ABSTAIN (TASK-127's rule, reproducible against the real service).")
    ap.add_argument("--playjev-timeout", type=float, default=300.0)
    ap.add_argument("--visual-legend-probe", action="store_true",
                    help="TASK-129 D-E: also ask ONE frame with the brokenness legend "
                         "REVERSED, to test whether the measured score inversion is a "
                         "wording/legend-order artefact.  Its result is stored under "
                         "gate[\"playjev\"][\"legend_probe\"] and NEVER enters a verdict.")
    ap.add_argument("--exercise", nargs="*", default=[],
                    help="TASK-129 D-D: declarative negative variants under "
                         "projects/_exercises/.  Each name is a directory "
                         "`projects/_exercises/<name>` and is then addressable exactly "
                         "like a game (--games <name>).  Nothing under "
                         "projects/<game>/ is touched by this.")
    ap.add_argument("--only-p7", dest="only_p7", action="store_true",
                    help="TASK-130: run ONLY the declarative required-UI criterion (P7).  "
                         "The game is started, settled, probed and stopped, but P1..P6 are "
                         "not measured; gate.json and playability.json record that scope "
                         "(`criteria_scope` / `criteria_covered`) so an --only-p7 run is "
                         "never mistaken for a full verdict.")
    ap.add_argument("--model-player-steps", default="",
                    help="TASK-132: read a model-player run's steps.jsonl and record the "
                         "MODEL-PLAYER criterion beside P1..P7 in gate.json.  The verdict "
                         "itself lives in that run's player.json; this only makes the rule "
                         "and the numbers visible where the other criteria are read, so "
                         "P1..P7 are never mistaken for a playability verdict.")
    ap.add_argument("--visual-input-form", default="native", choices=("native", "crop"),
                    help="TASK-130 B: the pixels the VISION backend is shown.  `native` "
                         "(default) is the captured full-window frame -- byte-identical to "
                         "the TASK-129 baseline.  `crop` cuts each frame down to its "
                         "content bounding box first, using the same modal-colour rule P1 "
                         "uses (`content_bbox_crop`), and records box/sha256 per frame.")
    ap.add_argument("--visual-crop-margin", type=int, default=0,
                    help="TASK-130 B: ignore a border band of N px before looking for "
                         "content (0 = the whole frame is searched).")
    ap.add_argument("--visual-crop-pad", type=int, default=0,
                    help="TASK-130 B: pad the content box by N px (0 = the tight box).")
    ap.add_argument("--visual-crop-min-side", type=int, default=0,
                    help="TASK-130 B: if the content box is thinner than N px on a side, "
                         "keep the whole frame instead of a hole.")
    ap.add_argument("--decision-path", default="",
                    help="TASK-124: the jev backend's decision endpoint "
                         "(/v1/systemone default, or /v1/decision; env "
                         "PLAYTEST_DECISION_PATH)" )
    ap.add_argument("--base-url", default="",
                    help="TASK-128: the REAL model service root URL for "
                         "`--agent=jev`/`--agent=playjev`, e.g. "
                         "http://127.0.0.1:8080 (jev) or http://127.0.0.1:8081 "
                         "(playjev).  Empty falls back to the PLAYTEST_BASE_URL "
                         "environment variable.  This is the documented real-service "
                         "entry; `playtest_agent.py --probe*` never uses it and only "
                         "talks to an in-process dumb server.")
    ap.add_argument("--agent-state-budget", type=int, default=0,
                    help="TASK-128/TASK-129: trim the sampled state to this estimated token "
                         "count before handing it to the agent (0 = off).  Jev refuses a "
                         "state over its documented 2048-token cap with HTTP 422 and 15 of "
                         "the 20 games exceed it.  UNIT CHANGED IN TASK-129: "
                         "`jev_estimate_tokens` is now calibrated on the service's own "
                         "`usage` (x2.5, conservative), so --agent-state-budget 2000 "
                         "selects EXACTLY the state TASK-128's 800 did (2000/2.5) and the "
                         "fitted jev thresholds stay comparable.  A REAL 422 is additionally "
                         "answered by halving the budget, bounded by --max-state-retries.  "
                         "What was dropped is recorded in gate\\agent\\observations.")
    ap.add_argument("--objective", default="")
    ap.add_argument("--port", type=int, default=DEFAULT_PORT)
    ap.add_argument("--ready-timeout", type=float, default=240)
    ap.add_argument("--call-timeout", type=float, default=40)
    ap.add_argument("--settle", type=float, default=4.0)
    ap.add_argument("--auto-gap", type=float, default=0.6)
    ap.add_argument("--auto-frames", type=int, default=3)
    ap.add_argument("--post-frames", type=int, default=2)
    ap.add_argument("--hold", type=float, default=0.5)
    ap.add_argument("--settle-input", type=float, default=0.35)
    ap.add_argument("--max-actions", type=int, default=8)
    ap.add_argument("--fresh", action="store_true", default=True)
    ap.add_argument("--no-fresh", dest="fresh", action="store_false")
    ap.add_argument("--exe-root", default="",
                    help="TASK-117: gate the exported exe at "
                         "<exe-root>\\<game>\\<game>.exe instead of the project")
    ap.add_argument("--out-root", default="",
                    help="write per-game output somewhere other than runs\\playability "
                         "(TASK-117 uses runs\\playability-exe)")
    ap.add_argument("--no-report", action="store_true")
    args = ap.parse_args(argv)

    global RUNS, EXE_ROOT
    if args.out_root:
        RUNS = os.path.abspath(args.out_root)
    if args.exe_root:
        EXE_ROOT = os.path.abspath(args.exe_root.rstrip("\\/"))
        if not os.path.isdir(EXE_ROOT):
            raise SystemExit("--exe-root is not a directory: %s" % EXE_ROOT)

    all_games = sorted(d for d in os.listdir(PROJECTS)
                       if os.path.isdir(os.path.join(PROJECTS, d))
                       and not d.startswith("_") and not d.startswith("mcp"))
    # TASK-129 D-D: register the declarative negative variants.  They live under
    # projects\_exercises\ (a copy, never the real project), so they are invisible to
    # `all_games` by design and have to be named explicitly.
    for name in (args.exercise or []):
        d = os.path.join(EXERCISES, name)
        if not os.path.isdir(d):
            raise SystemExit("--exercise %r: %s is not a directory" % (name, d))
        if not os.path.isfile(os.path.join(d, "project.godot")):
            raise SystemExit("--exercise %r: %s has no project.godot" % (name, d))
        GAME_DIRS[name] = d
    all_games = sorted(all_games + [n for n in (args.exercise or []) if n not in all_games])
    games = all_games if (args.all or not args.games) else args.games
    for g in games:
        if g not in all_games:
            raise SystemExit("unknown game %r; known: %s" % (g, all_games))

    if not os.path.isdir(RUNS):
        os.makedirs(RUNS)
    log("=== playability gate (TASK-116) ===")
    log("engine   : %s" % ENGINE)
    log("target   : %s%s" % ("EXPORTED EXE under " + EXE_ROOT if EXE_ROOT else "project tree",
                             "" if not EXE_ROOT else " (no --path; sidecar pck)"))
    log("out root : %s" % RUNS)
    log("games    : %s" % ", ".join(games))
    log("ports    : %d (checked free before each game)" % args.port)
    log("agents   : text=%s (state samples=%d, state budget=%d, max 422 state retries=%d)"
        % (args.agent, args.agent_state_samples, args.agent_state_budget,
           args.max_state_retries))
    log("vision   : %s%s" % (args.visual_agent or "(off)",
                             " frames=%d, invariants=%d, legend-probe=%s"
                             % (args.visual_frames, args.playjev_invariant_questions,
                                args.visual_legend_probe) if args.visual_agent else ""))
    if GAME_DIRS:
        log("exercises: %s" % ", ".join("%s -> %s" % (k, v) for k, v in sorted(GAME_DIRS.items())))
    log("thresholds: P1 content>=%.4f bbox>=%.4f delta>%d | P2 %d frames | P3 %d px | "
        "P6 capabilities and P7 required_ui from tools/playability_controls.json "
        "(P7 alpha>%.4f)"
        % (P1_MIN_CONTENT_FRACTION, P1_MIN_BBOX_COVERAGE, PIXEL_DELTA, P2_FRAMES,
           P3_MIN_CHANGED_PIXELS, P7_MIN_ALPHA))
    if args.only_p7:
        log("scope    : --only-p7 -- the declarative required-UI criterion (P7) only; "
            "P1..P6 are NOT run and the gate.json records that scope")
    if args.visual_input_form != "native":
        log("vision input form: %s (+ --visual-crop-margin %d, --visual-crop-pad %d)"
            % (args.visual_input_form, args.visual_crop_margin, args.visual_crop_pad))

    gates = []
    for g in games:
        try:
            gate = run_gate(g, args)
        except Exception as e:  # noqa: BLE001
            import traceback
            log("!!! %s raised %s: %s" % (g, type(e).__name__, e))
            log(traceback.format_exc()[-1500:])
            gate = {"game": g, "criteria": {}, "errors": [{"at": "harness",
                                                           "error": str(e)}]}
        gates.append(gate)

    audit = static_audit(games)
    if not args.no_report:
        summary = write_reports(gates, audit, args)
        log("")
        log("=== totals ===")
        log(json.dumps(summary["totals"], ensure_ascii=False))
        log("playability.json : %s" % os.path.join(RUNS, "playability.json"))
    with io.open(os.path.join(RUNS, "summary.txt"), "w", encoding="utf-8") as fh:
        fh.write("\n".join(_LOG))
    return 0


if __name__ == "__main__":
    sys.exit(main())
