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
    runs\\playability\\<game>\\gate.json                  P1..P6 verdicts + evidence
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
P1_MIN_CONTENT_FRACTION = 0.004   # >=0.4% of the window's pixels are content
P1_MIN_BBOX_COVERAGE = 0.12       # content bbox spans >=12% of the window area
P2_FRAMES = 45                    # "within N frames": 45 drawn frames (~0.75 s @60)
P2_SETTLE_S = 0.45
P3_MIN_CHANGED_PIXELS = 40        # a genuine frame-to-frame change, not noise
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
                                "P6": {"pass": False, "why": "no game process"}}
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
            note = "P1..P6 = %s" % " ".join(
                "%s:%s" % (k, "pass" if (verdict.get(k) or {}).get("pass") else "FAIL")
                for k in ("P1", "P2", "P3", "P4", "P5", "P6"))
            build_filmstrip(frames, os.path.join(outdir, "filmstrip.png"),
                            "%s -- full-window frames (game endpoint, real game process)" % game,
                            note=(oc or "") + "   " + note)
    except Exception as e:  # noqa: BLE001
        gate["errors"].append({"at": "filmstrip", "error": "%s: %s" % (type(e).__name__, e)})
    write_json(os.path.join(outdir, "gate.json"), gate)
    log("=== %s : %s" % (game, " ".join(
        "%s=%s" % (k, "PASS" if (gate["criteria"].get(k) or {}).get("pass") else "FAIL")
        for k in ("P1", "P2", "P3", "P4", "P5", "P6"))))
    for k in ("P1", "P2", "P3", "P4", "P5", "P6"):
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
           "task": "TASK-129 C/D-E",
           "one_image_plus_n_questions": True,
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
        out["frames_used"].append({"label": f.get("label"), "index": f.get("index"),
                                   "file": os.path.basename(f.get("path") or ""),
                                   "path": f.get("path"), "sha256": f.get("sha256")})
        t0 = time.time()
        action = agent.decide([frame_rec], {}, goal)
        wall = round(time.time() - t0, 3)
        ev = agent.last_evidence or {}
        q = per_question(ev)
        verdict = agent.threshold_verdict()
        obs = {"frame_label": f.get("label"), "frame_index": f.get("index"),
               "frame_file": os.path.basename(f.get("path") or ""),
               "frame_path": f.get("path"), "frame_sha256": f.get("sha256"),
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
    crit = {}

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
        p1_pass = (not flat) and cf >= P1_MIN_CONTENT_FRACTION and bc >= P1_MIN_BBOX_COVERAGE
        why = "best frame #%s: content %.4f%% (>=%.2f%%), bbox coverage %.4f%% (>=%.2f%%), bbox=%s, bg=%s" % (
            best.get("index"), 100.0 * cf, 100.0 * P1_MIN_CONTENT_FRACTION,
            100.0 * bc, 100.0 * P1_MIN_BBOX_COVERAGE, best.get("bbox"),
            best.get("background_rgb"))
        if flat:
            why = "the frame is a single flat colour (0 content pixels): %s" % why
        crit["P1"] = {"pass": bool(p1_pass), "why": why,
                      "best_frame": frame_evidence(best),
                      "worst_frame": frame_evidence(worst),
                      "thresholds": {"min_content_fraction": P1_MIN_CONTENT_FRACTION,
                                     "min_bbox_coverage": P1_MIN_BBOX_COVERAGE,
                                     "pixel_delta": PIXEL_DELTA},
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
    tested = gate.get("actions_tested") or []
    responded = [a for a in tested if a.get("responds")]
    mismatched = [a for a in tested if a.get("mismatch")]
    suspicious = [a for a in tested if a.get("suspicious_mismatch")]
    if not tested:
        crit["P2"] = {"pass": False, "why": "there was no declared action to inject"}
    else:
        p2 = len(responded) == len(tested)
        crit["P2"] = {
            "pass": bool(p2),
            "why": "%d/%d declared actions produced a state or pixel change within %d frames "
                   "through the faithful channel (`Input.parse_input_event`, the path a real key "
                   "press takes): %d/%d; of the failures, %d answered only `Viewport.push_input` "
                   "(an `_Input`-reader) and %d answered only `Input.action_press`"
                   % (len(responded), len(tested), P2_FRAMES,
                      sum(1 for a in tested if a.get("responds_to_real_key")), len(tested),
                      sum(1 for a in tested if a.get("responds_to_push_input_only")),
                      sum(1 for a in tested if a.get("responds_to_action_state_only"))),
            "actions": [{k: a.get(k) for k in ("action", "key", "responds",
                                               "responds_to_real_key",
                                               "responds_to_push_input_only",
                                               "responds_to_action_state_only",
                                               "suspicious_mismatch")}
                        for a in tested],
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
    # the layered delta: everything that moved during the input round, taken from
    # the per-action evidence (before -> after)
    input_delta_count = 0
    for a in tested:
        for ch in (a.get("channels") or {}).values():
            input_delta_count += ((ch.get("action") or {}).get("state_change_count") or 0)
    p3_pass = loop_advanced and (
        len(auto_delta) > 0 or len(post_delta) > 0 or pixel_auto >= P3_MIN_CHANGED_PIXELS
        or input_delta_count > 0)
    crit["P3"] = {
        "pass": bool(p3_pass),
        "why": "frames_drawn %s -> %s (advanced=%s); autonomous state changes=%d; "
               "pixel change over the autonomous+post frames=%d; state changes seen "
               "during the input round=%d"
               % (drawn[0] if drawn else None, drawn[-1] if drawn else None,
                  loop_advanced, len(auto_delta), pixel_auto, input_delta_count),
        "frames_drawn_samples": drawn,
        "autonomous_state_changes": auto_delta[:15],
        "autonomous_change_count": len(auto_delta),
        "total_state_changes_since_settle": post_delta[:15],
        "total_change_count": len(post_delta),
        "max_pixel_change_autonomous": pixel_auto,
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
    return crit


def frame_evidence(f):
    return {"index": f.get("index"), "label": f.get("label"),
            "file": os.path.basename(f.get("path", "")),
            "width": f.get("width"), "height": f.get("height"),
            "window": f.get("window"), "content_fraction": f.get("content_fraction"),
            "bbox": f.get("bbox"), "bbox_coverage": f.get("bbox_coverage"),
            "background_rgb": f.get("background_rgb"),
            "changed_pixels_vs_prev": f.get("changed_pixels_vs_prev"),
            "sha256": f.get("sha256")}


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
                   "P3_min_changed_pixels": P3_MIN_CHANGED_PIXELS},
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
        summary["games"].append({
            "game": g["game"],
            "target": g.get("target"),
            "verdict": "playable" if all((crit.get(k) or {}).get("pass") for k in
                                         ("P1", "P2", "P3", "P4", "P5", "P6")) else "not_playable",
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
                                    if k == "P6" else {}))
                         for k in ("P1", "P2", "P3", "P4", "P5", "P6")},
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
        "per_criterion_fail": {k: sum(1 for x in summary["games"]
                                      if not x["criteria"][k]["pass"])
                               for k in ("P1", "P2", "P3", "P4", "P5", "P6")},
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
        "P6 from tools/playability_controls.json"
        % (P1_MIN_CONTENT_FRACTION, P1_MIN_BBOX_COVERAGE, PIXEL_DELTA, P2_FRAMES,
           P3_MIN_CHANGED_PIXELS))

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
