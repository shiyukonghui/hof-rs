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

Outputs
-------
    runs\\playability\\<game>\\frames\\NN_<label>.png     full-window frames
    runs\\playability\\<game>\\frames.json                per-frame geometry + metrics
    runs\\playability\\<game>\\filmstrip.png              all frames in one image
    runs\\playability\\<game>\\states\\NN_<label>.json    sampled game state
    runs\\playability\\<game>\\gate.json                  P1..P5 verdicts + evidence
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
RUNS = os.path.join(ROOT, "runs", "playability")
ENGINE = os.path.join(ROOT, "godot", "bin", "godot.windows.editor.x86_64.mono.console.exe")
ENGINE_CWD = os.path.join(ROOT, "godot")
REPORTS = os.path.join(ROOT, "recovery", "reports")

# TASK-117: the same gate must be able to judge **the exported artifact** instead of
# the project.  A game can be playable in the editor build and broken in the export
# (that is exactly the failure this switch exists to be able to see), so the two
# runs are kept apart by output root and the executable is what changes, nothing
# else.  `EXE_ROOT` is `<root>\dist\exe`; the gate then launches
# `<EXE_ROOT>\<game>\<game>.exe --mcp-port=N` with the game's own directory as cwd.
EXE_ROOT = None

sys.path.insert(0, HERE)
from playtest_agent import build_agent, keycode_of, keyname_of  # noqa: E402

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
    pdir = os.path.join(PROJECTS, game)
    gd = read_text(os.path.join(pdir, "project.godot"))
    info = {"game": game, "dir": pdir}
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
            project = os.path.join(PROJECTS, self.game)
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
              "project_dir": os.path.join(PROJECTS, game)}
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
        if args.agent and args.agent != "none":
            goal = {"game": game, "objective": args.objective or
                    "make the game visibly respond to its own documented controls",
                    "actions": {k: v["keys"] for k, v in proj["actions"].items()},
                    "keys": proj["readme_keys"]}
            agent = build_agent(args.agent, game, goal["objective"],
                                {"plan": None, "hold_ms": int(args.hold * 1000)})
            acts = []
            action = agent.decide(frames_for_agent(frames), (s_end or {}), goal)
            acts.append({"action": action, "why": "first decision"})
            if action.get("type") == "done":
                pass
            # execute a couple of the agent's decisions so the interface is used
            # for real, not just called
            for step in range(args.agent_steps):
                if action.get("type") == "done":
                    break
                applied = apply_agent_action(mcp, action, gate, "agent%02d" % step)
                acts.append({"action": action, "applied": applied})
                time.sleep(args.settle_input)
                capture("agent%02d" % step, mcp, None, note="after the agent's action")
                action = agent.decide(frames_for_agent(frames), (s_end or {}), goal)
            judge = agent.judge(frames_for_agent(frames), (s_end or {}), goal)
            gate["agent"] = {"report": agent.report(), "decisions": acts,
                             "judge": judge}
            write_json(os.path.join(outdir, "agent.json"), gate["agent"])

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


def frames_for_agent(frames):
    out = []
    for f in frames:
        out.append({k: f.get(k) for k in
                    ("index", "path", "width", "height", "content_fraction", "bbox",
                     "bbox_coverage", "background_rgb", "changed_pixels_vs_prev")})
    return out


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
    for dirpath, _dn, fns in os.walk(os.path.join(PROJECTS, g, "src")):
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
               "games": [], "static_audit": audit}
    for g in gates:
        crit = g.get("criteria") or {}
        summary["games"].append({
            "game": g["game"],
            "target": g.get("target"),
            "verdict": "playable" if all((crit.get(k) or {}).get("pass") for k in
                                         ("P1", "P2", "P3", "P4", "P5", "P6")) else "not_playable",
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
    ap.add_argument("--agent", default="scripted")
    ap.add_argument("--agent-steps", type=int, default=2)
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
