#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""TASK-131 -- OS-level REAL-input probe + measurement (repeatable, parameterised).

Why this file exists
--------------------
`tools/playability_gate.py` injects input *inside* the game process
(`Input.parse_input_event`, `Viewport.push_input`, `Input.action_press`).  That whole
family sits **inside** the DisplayServer boundary: it can never answer the question
"does a key a human presses on the keyboard reach this window?".  Between the keyboard
and `Input::parse_input_event` there are three things the gate never measured:

    OS keyboard  ->  window manager / session  ->  FOCUS (which window owns the queue)
                 ->  DisplayServerWindows WM_KEYDOWN/WM_CHAR
                 ->  Input::parse_input_event        <- the gate starts here

This tool measures the first three.  It is deliberately honest about the boundary:

    `env`   read-only capability probe: is this session interactive, is the display
            active, how many monitors, can any window be made foreground, does
            `SendInput` return a non-zero count (X1).
    `run`   drives a real game, makes its window foreground, and sends the game's OWN
            declared key codes with Win32 `SendInput`, sampling MCP state + full-window
            frames before/after and ALSO running the synthetic `Input.parse_input_event`
            arm over the same action, so the two paths are compared on one instance
            (X2/X3/X4/X5/X7).

Evidence layout (all JSON, no shell redirection anywhere):

    runs/realinput/_env/env.json               the capability probe
    runs/realinput/<game>/session.json         pid / port / version / trace / exe hash
    runs/realinput/<game>/env.json             the capability probe taken in this run
    runs/realinput/<game>/steps.json           the step-correspondence table (B)
    runs/realinput/<game>/real_input.json      summary + verdict for the real-key arm
    runs/realinput/<game>/frames/*.png         every frame, with sha256 in steps.json
    runs/realinput/<game>/calls/*.json         the MCP trace of every call (X5)
    runs/realinput/<game>/engine-game.stdout.txt   the game's own stdout (delivery proof)

Iron rules honoured: no `>`, `>>`, `2>&1`; the game is launched through `cmd.exe` by
`playability_gate.GameProcess`; one unique high port, checked for occupancy up front.
"""

from __future__ import annotations

import argparse
import base64
import ctypes
import hashlib
import io
import json
import os
import subprocess
import sys
import time
from ctypes import wintypes

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
sys.path.insert(0, HERE)

import playability_gate as pg  # noqa: E402

RUNS_REAL = os.path.join(ROOT, "runs", "realinput")
DEFAULT_PORT = 9931
DEFAULT_EXE_ROOT = os.path.join(ROOT, "dist", "exe")

# ---------------------------------------------------------------------------
# Win32 plumbing
# ---------------------------------------------------------------------------
user32 = ctypes.WinDLL("user32", use_last_error=True)
kernel32 = ctypes.WinDLL("kernel32", use_last_error=True)

INPUT_KEYBOARD = 1
KEYEVENTF_EXTENDEDKEY = 0x0001
KEYEVENTF_KEYUP = 0x0002
SW_RESTORE = 9
ASFW_ANY = -1
SPI_GETFOREGROUNDLOCKTIMEOUT = 0x2000

SM_CXSCREEN, SM_CYSCREEN = 0, 1
SM_CMONITORS = 80
SM_CXVIRTUALSCREEN, SM_CYVIRTUALSCREEN = 78, 79
SM_REMOTESESSION = 0x1000

HMONITOR = wintypes.HANDLE
HDC = wintypes.HANDLE


class KEYBDINPUT(ctypes.Structure):
    _fields_ = [("wVk", wintypes.WORD), ("wScan", wintypes.WORD),
                ("dwFlags", wintypes.DWORD), ("time", wintypes.DWORD),
                ("dwExtraInfo", ctypes.c_void_p)]


class MOUSEINPUT(ctypes.Structure):
    _fields_ = [("dx", wintypes.LONG), ("dy", wintypes.LONG),
                ("mouseData", wintypes.DWORD), ("dwFlags", wintypes.DWORD),
                ("time", wintypes.DWORD), ("dwExtraInfo", ctypes.c_void_p)]


class HARDWAREINPUT(ctypes.Structure):
    _fields_ = [("uMsg", wintypes.DWORD), ("wParamL", wintypes.WORD),
                ("wParamH", wintypes.WORD)]


class _INPUTUNION(ctypes.Union):
    _fields_ = [("ki", KEYBDINPUT), ("mi", MOUSEINPUT), ("hi", HARDWAREINPUT)]


class INPUT(ctypes.Structure):
    _fields_ = [("type", wintypes.DWORD), ("u", _INPUTUNION)]


class MONITORINFOEXW(ctypes.Structure):
    _fields_ = [("cbSize", wintypes.DWORD), ("rcMonitor", wintypes.RECT),
                ("rcWork", wintypes.RECT), ("dwFlags", wintypes.DWORD),
                ("szDevice", ctypes.c_wchar * 32)]


# Every user32 entry point that takes an HWND gets explicit argtypes.  Without them
# ctypes marshals a Python int as a 32-bit C int and silently TRUNCATES the handle on
# x64 -- a window probe that reports "not foreground" for that reason would be a lie.
user32.SendInput.argtypes = (wintypes.UINT, ctypes.POINTER(INPUT), ctypes.c_int)
user32.SendInput.restype = wintypes.UINT
user32.GetAsyncKeyState.argtypes = (ctypes.c_int,)
user32.GetAsyncKeyState.restype = ctypes.c_short
user32.IsWindowVisible.argtypes = (wintypes.HWND,)
user32.IsWindowVisible.restype = wintypes.BOOL
user32.IsIconic.argtypes = (wintypes.HWND,)
user32.IsIconic.restype = wintypes.BOOL
user32.GetWindowTextLengthW.argtypes = (wintypes.HWND,)
user32.GetWindowTextLengthW.restype = ctypes.c_int
user32.GetWindowTextW.argtypes = (wintypes.HWND, wintypes.LPWSTR, ctypes.c_int)
user32.GetWindowTextW.restype = ctypes.c_int
user32.GetClassNameW.argtypes = (wintypes.HWND, wintypes.LPWSTR, ctypes.c_int)
user32.GetClassNameW.restype = ctypes.c_int
user32.GetWindowRect.argtypes = (wintypes.HWND, ctypes.POINTER(wintypes.RECT))
user32.GetWindowRect.restype = wintypes.BOOL
user32.GetWindowThreadProcessId.argtypes = (wintypes.HWND, ctypes.POINTER(wintypes.DWORD))
user32.GetWindowThreadProcessId.restype = wintypes.DWORD
user32.GetForegroundWindow.argtypes = ()
user32.GetForegroundWindow.restype = wintypes.HWND
user32.GetActiveWindow.argtypes = ()
user32.GetActiveWindow.restype = wintypes.HWND
user32.SetForegroundWindow.argtypes = (wintypes.HWND,)
user32.SetForegroundWindow.restype = wintypes.BOOL
user32.ShowWindow.argtypes = (wintypes.HWND, ctypes.c_int)
user32.ShowWindow.restype = wintypes.BOOL
user32.BringWindowToTop.argtypes = (wintypes.HWND,)
user32.BringWindowToTop.restype = wintypes.BOOL
user32.SetActiveWindow.argtypes = (wintypes.HWND,)
user32.SetActiveWindow.restype = wintypes.HWND
user32.AttachThreadInput.argtypes = (wintypes.DWORD, wintypes.DWORD, wintypes.BOOL)
user32.AttachThreadInput.restype = wintypes.BOOL
user32.GetSystemMetrics.argtypes = (ctypes.c_int,)
user32.GetSystemMetrics.restype = ctypes.c_int
user32.SystemParametersInfoW.argtypes = (wintypes.UINT, wintypes.UINT,
                                         ctypes.c_void_p, wintypes.UINT)
user32.SystemParametersInfoW.restype = wintypes.BOOL
user32.OpenInputDesktop.argtypes = (wintypes.DWORD, wintypes.BOOL, wintypes.DWORD)
user32.OpenInputDesktop.restype = wintypes.HANDLE
user32.CloseDesktop.argtypes = (wintypes.HANDLE,)
user32.CloseDesktop.restype = wintypes.BOOL
user32.GetUserObjectInformationW.argtypes = (wintypes.HANDLE, ctypes.c_int,
                                             ctypes.c_void_p, wintypes.DWORD,
                                             ctypes.POINTER(wintypes.DWORD))
user32.GetUserObjectInformationW.restype = wintypes.BOOL
user32.GetMonitorInfoW.argtypes = (HMONITOR, ctypes.c_void_p)
user32.GetMonitorInfoW.restype = wintypes.BOOL
kernel32.GetCurrentThreadId.argtypes = ()
kernel32.GetCurrentThreadId.restype = wintypes.DWORD
kernel32.ProcessIdToSessionId.argtypes = (wintypes.DWORD, ctypes.POINTER(wintypes.DWORD))
kernel32.ProcessIdToSessionId.restype = wintypes.BOOL

if ctypes.sizeof(INPUT) != 40:  # x64 layout guard: a wrong struct silently sends nothing
    raise SystemExit("REFUSED: sizeof(INPUT) is %d, expected 40 on x64" % ctypes.sizeof(INPUT))


def last_err():
    return int(ctypes.get_last_error())


def send_key(vk, up=False, extended=False, scan=0):
    """One Win32 `SendInput` keyboard event.  Returns the evidence, never a bare bool."""
    flags = 0
    if extended:
        flags |= KEYEVENTF_EXTENDEDKEY
    if up:
        flags |= KEYEVENTF_KEYUP
    ev = INPUT(type=INPUT_KEYBOARD,
               u=_INPUTUNION(ki=KEYBDINPUT(wVk=vk, wScan=scan, dwFlags=flags,
                                           time=0, dwExtraInfo=None)))
    ctypes.set_last_error(0)
    n = int(user32.SendInput(1, ctypes.byref(ev), ctypes.sizeof(INPUT)))
    return {"vk": vk, "vk_hex": "0x%02X" % vk, "up": bool(up),
            "extended": bool(extended), "scancode": scan,
            "requested": 1, "returned": n, "GetLastError": last_err()}


# ---------------------------------------------------------------------------
# Godot Key -> Windows virtual key  (inverse of KeyMappingWindows::get_keysym)
# ---------------------------------------------------------------------------
# Godot's `Key` enum (godot/core/os/keyboard.h): letters/digits/space are ASCII, the rest
# are `SPECIAL | n` with SPECIAL = 1 << 22 = 4194304.  The Windows side is the
# authoritative `vk_map` of godot/platform/windows/key_mapping_windows.cpp; for the keys a
# human actually binds in these 20 games the mapping is the standard VK table, written out
# here so the tool refuses an unknown key instead of guessing.
SPECIAL = 1 << 22
GODOT_TO_VK = {}
for _c in range(ord("A"), ord("Z") + 1):
    GODOT_TO_VK[_c] = _c                      # Key::A..Key::Z == VK_A..VK_Z (0x41..0x5A)
for _d in range(ord("0"), ord("9") + 1):
    GODOT_TO_VK[_d] = _d                      # Key::0..Key::9 == VK_0..VK_9 (0x30..0x39)
GODOT_TO_VK.update({
    0x20: 0x20,                               # SPACE
    SPECIAL | 0x01: 0x1B,                     # ESCAPE
    SPECIAL | 0x02: 0x09,                     # TAB
    SPECIAL | 0x04: 0x08,                     # BACKSPACE
    SPECIAL | 0x05: 0x0D,                     # ENTER
    SPECIAL | 0x06: 0x0D,                     # KP_ENTER
    SPECIAL | 0x08: 0x2E,                     # DELETE
    SPECIAL | 0x09: 0x2D,                     # INSERT
    SPECIAL | 0x0A: 0x24,                     # HOME
    SPECIAL | 0x0B: 0x23,                     # END
    SPECIAL | 0x0C: 0x21,                     # PAGEUP
    SPECIAL | 0x0D: 0x22,                     # PAGEDOWN
    SPECIAL | 0x0E: 0x2D,                     # INSERT (kp)
    SPECIAL | 0x0F: 0x25,                     # LEFT
    SPECIAL | 0x10: 0x26,                     # UP
    SPECIAL | 0x11: 0x27,                     # RIGHT
    SPECIAL | 0x12: 0x28,                     # DOWN
    SPECIAL | 0x15: 0x10,                     # SHIFT
    SPECIAL | 0x16: 0x11,                     # CTRL
    SPECIAL | 0x18: 0x12,                     # ALT
    0x2D: 0xBD,                               # MINUS
    0x3D: 0xBB,                               # EQUAL
    0x5B: 0xDB,                               # BRACKETLEFT
    0x5D: 0xDD,                               # BRACKETRIGHT
    0x5C: 0xDC,                               # BACKSLASH
    0x3B: 0xBA,                               # SEMICOLON
    0x27: 0xDE,                               # APOSTROPHE
    0x2C: 0xBC,                               # COMMA
    0x2E: 0xBE,                               # PERIOD
    0x2F: 0xBF,                               # SLASH
    0x60: 0xC0,                               # QUOTELEFT
})
for _i in range(12):                           # F1..F12 = SPECIAL|0x1C .. SPECIAL|0x27
    GODOT_TO_VK[SPECIAL | (0x1C + _i)] = 0x70 + _i

EXTENDED_VKS = {0x25, 0x26, 0x27, 0x28, 0x21, 0x22, 0x23, 0x24, 0x2D, 0x2E}


def godot_key_to_vk(kc):
    """Reverse of `KeyMappingWindows::get_keysym` for the bindable keys; None if unknown."""
    if kc is None:
        return None
    return GODOT_TO_VK.get(int(kc))


# ---------------------------------------------------------------------------
# read-only helpers
# ---------------------------------------------------------------------------
def window_info(hwnd):
    if not hwnd:
        return None
    pid = wintypes.DWORD()
    user32.GetWindowThreadProcessId(wintypes.HWND(hwnd), ctypes.byref(pid))
    cls = ctypes.create_unicode_buffer(256)
    user32.GetClassNameW(wintypes.HWND(hwnd), cls, 256)
    ln = user32.GetWindowTextLengthW(wintypes.HWND(hwnd))
    title = ctypes.create_unicode_buffer(ln + 2)
    user32.GetWindowTextW(wintypes.HWND(hwnd), title, ln + 2)
    rect = wintypes.RECT()
    user32.GetWindowRect(wintypes.HWND(hwnd), ctypes.byref(rect))
    return {"hwnd": int(hwnd), "pid": int(pid.value), "class": cls.value,
            "title": title.value, "visible": bool(user32.IsWindowVisible(wintypes.HWND(hwnd))),
            "iconic": bool(user32.IsIconic(wintypes.HWND(hwnd))),
            "rect": [rect.left, rect.top, rect.right - rect.left, rect.bottom - rect.top],
            "owner_thread": int(user32.GetWindowThreadProcessId(wintypes.HWND(hwnd), None))}


def foreground():
    return window_info(user32.GetForegroundWindow())


def monitors():
    out = []
    MONITORENUMPROC = ctypes.WINFUNCTYPE(wintypes.BOOL, HMONITOR, HDC,
                                         ctypes.POINTER(wintypes.RECT), wintypes.LPARAM)
    user32.EnumDisplayMonitors.argtypes = (HDC, ctypes.c_void_p, MONITORENUMPROC,
                                           wintypes.LPARAM)
    user32.EnumDisplayMonitors.restype = wintypes.BOOL

    def cb(hmon, _hdc, _rect, _data):
        mi = MONITORINFOEXW()
        mi.cbSize = ctypes.sizeof(MONITORINFOEXW)
        user32.GetMonitorInfoW(hmon, ctypes.byref(mi))
        out.append({"device": mi.szDevice,
                    "monitor": [mi.rcMonitor.left, mi.rcMonitor.top,
                                mi.rcMonitor.right - mi.rcMonitor.left,
                                mi.rcMonitor.bottom - mi.rcMonitor.top],
                    "work": [mi.rcWork.left, mi.rcWork.top,
                             mi.rcWork.right - mi.rcWork.left,
                             mi.rcWork.bottom - mi.rcWork.top],
                    "primary": bool(mi.dwFlags & 1)})
        return True

    user32.EnumDisplayMonitors(None, None, MONITORENUMPROC(cb), 0)
    return out


def input_desktop():
    """Is the session attached to an *interactive input desktop* (not the secure one)?"""
    h = user32.OpenInputDesktop(0, False, 0x0001)  # DESKTOP_READOBJECTS
    if not h:
        return {"opened": False, "GetLastError": last_err()}
    try:
        need = wintypes.DWORD()
        buf = ctypes.create_unicode_buffer(256)
        ok = user32.GetUserObjectInformationW(h, 2, ctypes.cast(buf, ctypes.c_void_p),
                                              ctypes.sizeof(buf), ctypes.byref(need))
        return {"opened": True, "name": buf.value if ok else None,
                "GetUserObjectInformation_ok": bool(ok)}
    finally:
        user32.CloseDesktop(h)


def foreground_lock_timeout():
    v = wintypes.DWORD()
    ok = user32.SystemParametersInfoW(SPI_GETFOREGROUNDLOCKTIMEOUT, 0, ctypes.byref(v), 0)
    return {"ok": bool(ok), "ms": int(v.value)}


def monitor_metrics():
    gsm = user32.GetSystemMetrics
    return {"SM_CMONITORS": int(gsm(SM_CMONITORS)),
            "SM_CXSCREEN": int(gsm(SM_CXSCREEN)), "SM_CYSCREEN": int(gsm(SM_CYSCREEN)),
            "SM_CXVIRTUALSCREEN": int(gsm(SM_CXVIRTUALSCREEN)),
            "SM_CYVIRTUALSCREEN": int(gsm(SM_CYVIRTUALSCREEN)),
            "SM_REMOTESESSION": int(gsm(SM_REMOTESESSION))}


def nvidia_smi():
    exe = os.path.join(os.environ.get("SystemRoot", r"C:\Windows"),
                       "System32", "nvidia-smi.exe")
    if not os.path.isfile(exe):
        exe = "nvidia-smi"
    queries = [
        ["--query-gpu=name,driver_version,display_active,display_mode,persistence_mode",
         "--format=csv"],
        ["--query-gpu=name,memory.total,utilization.gpu", "--format=csv"],
    ]
    out = []
    for q in queries:
        try:
            r = subprocess.run([exe] + q, stdout=subprocess.PIPE,
                               stderr=subprocess.STDOUT, timeout=30)
            out.append({"cmd": [exe] + q, "exit": r.returncode,
                        "stdout": r.stdout.decode("utf-8", "replace").strip()})
        except Exception as e:  # noqa: BLE001
            out.append({"cmd": [exe] + q, "error": "%s: %s" % (type(e).__name__, e)})
    return out


def session_of_this_process():
    sid = wintypes.DWORD()
    pid = os.getpid()
    ok = kernel32.ProcessIdToSessionId(pid, ctypes.byref(sid))
    return {"pid": pid, "session_id": int(sid.value) if ok else None,
            "ProcessIdToSessionId_ok": bool(ok)}


def try_foreground(hwnd):
    """Make `hwnd` foreground, recording EVERY attempt and its result (X1)."""
    res = {"target": window_info(hwnd), "before": foreground(), "attempts": []}
    if not hwnd:
        res["ok"] = False
        res["why"] = "no target window was given"
        return res
    user32.ShowWindow(wintypes.HWND(hwnd), SW_RESTORE)
    res["attempts"].append({"call": "ShowWindow(SW_RESTORE)"})
    ctypes.set_last_error(0)
    r = user32.SetForegroundWindow(wintypes.HWND(hwnd))
    res["attempts"].append({"call": "SetForegroundWindow", "returned": int(r),
                            "GetLastError": last_err()})
    if not r:
        # The classic foreground lock: a process that does not own the foreground may not
        # steal it.  Attaching to the foreground thread's input queue is the documented
        # workaround, and the outcome is recorded rather than assumed.
        fg = user32.GetForegroundWindow()
        fg_tid = user32.GetWindowThreadProcessId(fg, None) if fg else 0
        my_tid = kernel32.GetCurrentThreadId()
        att = user32.AttachThreadInput(my_tid, fg_tid, True) if fg_tid else 0
        res["attempts"].append({"call": "AttachThreadInput(my=%d, fg_thread=%d)"
                                        % (my_tid, fg_tid), "returned": int(att)})
        try:
            user32.BringWindowToTop(wintypes.HWND(hwnd))
            r2 = user32.SetForegroundWindow(wintypes.HWND(hwnd))
            res["attempts"].append({"call": "BringWindowToTop+SetForegroundWindow",
                                    "returned": int(r2), "GetLastError": last_err()})
            r = r or r2
        finally:
            if fg_tid:
                user32.AttachThreadInput(my_tid, fg_tid, False)
    time.sleep(0.25)
    res["after"] = foreground()
    res["ok"] = bool(res["after"] and res["after"]["hwnd"] == int(hwnd))
    res["is_foreground"] = res["ok"]
    res["get_active_window"] = window_info(user32.GetActiveWindow())
    res["foreground_lock"] = foreground_lock_timeout()
    return res


def sendinput_selftest(vk=0x87):
    """Send a real OS key press/release and report whether the desktop accepted it.

    `vk` defaults to F24 (0x87), which no game of the 20 binds, so the measurement cannot
    be confused with the game's own reaction.  `GetAsyncKeyState` is read between the
    press and the release: a non-zero high bit is the OS confirming the injected key is
    down, which is what makes "SendInput returned 1" more than a claim about the API.
    """
    out = {"vk": vk, "GetAsyncKeyState_before": int(user32.GetAsyncKeyState(vk))}
    out["keydown"] = send_key(vk, up=False)
    time.sleep(0.12)
    out["GetAsyncKeyState_while_down"] = int(user32.GetAsyncKeyState(vk))
    out["keyup"] = send_key(vk, up=True)
    time.sleep(0.08)
    out["GetAsyncKeyState_after"] = int(user32.GetAsyncKeyState(vk))
    out["accepted_by_desktop"] = bool(
        out["keydown"]["returned"] == 1 and out["keyup"]["returned"] == 1)
    out["os_reported_key_down"] = bool(out["GetAsyncKeyState_while_down"] & 0x8000)
    return out


def probe_env():
    fg = foreground()
    env = {
        "when": time.strftime("%Y-%m-%d %H:%M:%S"),
        "host": {"computername": os.environ.get("COMPUTERNAME"),
                 "username": os.environ.get("USERNAME"),
                 "cwd": os.getcwd()},
        "this_process": session_of_this_process(),
        "nvidia_smi": nvidia_smi(),
        "monitors": monitors(),
        "monitor_metrics": monitor_metrics(),
        "input_desktop": input_desktop(),
        "foreground_window": fg,
        "foreground_lock_timeout": foreground_lock_timeout(),
        "visible_windows": pg.enumerate_windows(),
    }
    # X1: can this process move the foreground at all?  First on whatever is foreground
    # now (a no-op that still proves the mechanism answers), then -- the part that really
    # measures capability -- on a DIFFERENT window, because "SetForegroundWindow returned
    # 1 for the window that was already foreground" proves nothing.
    target = (fg or {}).get("hwnd")
    if not target:
        ws = sorted(env["visible_windows"],
                    key=lambda w: -(w["rect"][2] * w["rect"][3]))
        target = ws[0]["hwnd"] if ws else None
    env["foreground_attempt"] = try_foreground(target)
    others = sorted([w for w in env["visible_windows"]
                     if w["hwnd"] != target and w["rect"][2] > 100 and w["rect"][3] > 100],
                    key=lambda w: -(w["rect"][2] * w["rect"][3]))
    if others:
        env["foreground_change_attempt"] = try_foreground(others[0]["hwnd"])
        env["foreground_restore_attempt"] = try_foreground(target)
    else:
        env["foreground_change_attempt"] = {
            "ok": None, "why": "the desktop has no other visible window to move the "
                               "foreground to, so a CHANGE could not be measured"}
    env["sendinput_selftest"] = sendinput_selftest()
    return env


# ---------------------------------------------------------------------------
# the measured run
# ---------------------------------------------------------------------------
def sha256_bytes(b):
    return hashlib.sha256(b).hexdigest()


def canonical_state_sha(state):
    return sha256_bytes(json.dumps(state, sort_keys=True, ensure_ascii=False,
                                  default=str).encode("utf-8"))


def fields_of(state, paths):
    """The game-logic fields the report table quotes, pulled out of a state snapshot."""
    nodes = (state or {}).get("nodes") or {}
    out = {}
    for p in paths:
        e = nodes.get(p)
        if e:
            out[p] = dict((k, v) for k, v in e.items() if k not in ("script",))
    return out


class Runner(object):
    def __init__(self, args):
        self.args = args
        self.outdir = os.path.join(RUNS_REAL, args.out_name or args.game)
        self.frames_dir = os.path.join(self.outdir, "frames")
        self.calls_dir = os.path.join(self.outdir, "calls")
        for d in (self.frames_dir, self.calls_dir):
            if os.path.isdir(d) and args.fresh:
                import shutil
                shutil.rmtree(d)
            if not os.path.isdir(d):
                os.makedirs(d)
        self.steps = []
        self.frames = []
        self.frame_index = 0
        self.mcp = None
        self.gp = None
        self.errors = []
        self._osd = {}

    # -- MCP wrappers that also record the step -----------------------------
    def gd(self, code, at):
        r = self.mcp.call_tool("running_game_execute_gdscript", {"code": code},
                               timeout=self.args.call_timeout)
        if not r.get("ok"):
            self.errors.append({"at": at, "error": r.get("error")})
            return None, r
        return r["value"].get("result"), r

    def sample_state(self, label):
        val, r = self.gd(pg.probe_state_source(), "state:" + label)
        return {"label": label, "state": val, "call": r,
                "state_sha256": canonical_state_sha(val) if isinstance(val, dict) else None}

    def capture(self, label, state=None, note=""):
        r = self.mcp.call_tool("running_game_capture_screenshot", {})
        rec = {"label": label, "note": note, "ok": bool(r.get("ok")), "call": r}
        if not r.get("ok"):
            rec["error"] = r.get("error")
            self.frames.append(rec)
            return None
        v = r["value"]
        b64 = v.get("image_base64")
        if not b64:
            rec["error"] = "no image_base64 in the answer"
            self.frames.append(rec)
            return None
        png = base64.b64decode(b64)
        idx = self.frame_index + 1
        self.frame_index = idx
        fname = "%02d_%s.png" % (idx, label)
        fpath = os.path.join(self.frames_dir, fname)
        with open(fpath, "wb") as fh:
            fh.write(png)
        rec.update(analyse_and_hash(fpath))
        # OSD window rect at capture time (X6: which viewport, at what resolution)
        rec["osd_window_rect"] = self.osd_window_rect
        prev = self.frames[-1] if self.frames else None
        if prev and prev.get("ok") and prev.get("path"):
            ch = pg.png_changed(prev["path"], fpath)
            rec["changed_pixels_vs_prev"] = ch.get("changed_pixels")
            rec["change_vs_prev"] = ch
        else:
            rec["changed_pixels_vs_prev"] = None
        rec["path"] = fpath
        rec["index"] = idx
        rec["sha256"] = sha256_bytes(png)
        if state:
            rec["state_sha256"] = state.get("state_sha256")
            rec["frame_count"] = state["state"].get("drawn") if isinstance(state["state"], dict) else None
            rec["ticks_ms"] = state["state"].get("ms") if isinstance(state["state"], dict) else None
        self.frames.append(rec)
        return rec

    def step(self, phase, note, injection=None, state=None, frame=None, extra=None):
        t = {
            "step": len(self.steps) + 1,
            "phase": phase,
            "note": note,
            "injection": injection,
            "state": None if not state else {
                "label": state["label"],
                "sha256": state.get("state_sha256"),
                "drawn": (state.get("state") or {}).get("drawn"),
                "processed": (state.get("state") or {}).get("processed"),
                "physics": (state.get("state") or {}).get("physics"),
                "fps": (state.get("state") or {}).get("fps"),
                "ticks_ms": (state.get("state") or {}).get("ms"),
                "mcp_call_n": (state.get("call") or {}).get("n"),
                "mcp_trace_file": self.trace_file(state.get("call")),
                "fields": fields_of(state.get("state"), self.args.show_nodes),
            },
            "frame": None if not frame else {
                "index": frame.get("index"), "file": os.path.basename(frame.get("path") or ""),
                "path": frame.get("path"), "sha256": frame.get("sha256"),
                "width": frame.get("width"), "height": frame.get("height"),
                "byte_identical_to_prev": (frame.get("changed_pixels_vs_prev") == 0),
                "changed_pixels_vs_prev": frame.get("changed_pixels_vs_prev"),
                "content_fraction": frame.get("content_fraction"),
                "bbox": frame.get("bbox"),
                "background_rgb": frame.get("background_rgb"),
                "mcp_call_n": (frame.get("call") or {}).get("n"),
                "mcp_trace_file": self.trace_file(frame.get("call")),
                "captured_at_ms": frame.get("ticks_ms"),
                "frame_count": frame.get("frame_count"),
                "osd_window_rect": frame.get("osd_window_rect"),
            },
            "focus": None,
        }
        if extra:
            t.update(extra)
        self.steps.append(t)
        return t

    def trace_file(self, call):
        if not call:
            return None
        return "%03d_%s.response.json" % (call.get("n", 0), call.get("tool", "?"))

    # -- window plumbing ----------------------------------------------------
    @property
    def osd_window_rect(self):
        return self._osd

    def find_game_window(self):
        pids = set()
        if self.gp and self.gp.proc:
            pids = set(p["pid"] for p in pg.process_tree(self.gp.proc.pid))
        wins = pg.enumerate_windows()
        cands = [w for w in wins if w["pid"] in pids]
        cands.sort(key=lambda w: -(w["rect"][2] * w["rect"][3]))
        return cands

    # -- the run ------------------------------------------------------------
    def run(self):
        args = self.args
        if args.mode == "exe":
            pg.EXE_ROOT = args.exe_root
        else:
            pg.EXE_ROOT = None
        # iron rule 4/6: one unique port, proven free before use
        leftover = pg.kill_what_holds(args.port)
        if leftover["still_holding"]:
            raise RuntimeError("port %d still held by %s"
                               % (args.port, [k["pid"] for k in leftover["still_holding"]]))
        proj = pg.parse_project(args.game)
        self.gp = pg.GameProcess(args.game, args.port, self.outdir)
        ok, secs = self.gp.start(args.ready_timeout)
        if not ok:
            raise RuntimeError("the game's MCP endpoint never came up on port %d" % args.port)
        self.mcp = pg.Mcp(args.port, self.calls_dir)
        tools = self.mcp.tools_list()
        t0 = time.time()
        time.sleep(args.settle)

        win = None
        w, _ = self.gd(pg.PROBE_WINDOW, "window")
        self._osd = {"display_window_size": (w or {}).get("display_window_size"),
                     "display_window_position": (w or {}).get("display_window_position"),
                     "root_viewport_size": (w or {}).get("root_viewport_size"),
                     "declared_viewport": (w or {}).get("declared_viewport"),
                     "screen_size": (w or {}).get("screen_size"),
                     "video_adapter": (w or {}).get("video_adapter"),
                     "current_scene": (w or {}).get("current_scene")}
        log("window: %s  root_viewport %s  declared %s  adapter %s"
            % (self._osd["display_window_size"], self._osd["root_viewport_size"],
               self._osd["declared_viewport"], self._osd["video_adapter"]))

        # --- same-instance identity (X5): four alignments -------------------
        version = engine_version()
        cands = self.find_game_window()
        win = cands[0] if cands else None
        identity = {
            "game_pid": self.gp.proc.pid,
            "process_tree": pg.process_tree(self.gp.proc.pid),
            "mcp_port": args.port,
            "mcp_endpoint": self.mcp.url,
            "mcp_tools_count": len(tools),
            "mcp_trace_dir": os.path.abspath(self.calls_dir),
            "game_stdout_log": os.path.abspath(self.gp.stdout),
            "engine_version_string": version,
            "engine_binary": pg.ENGINE,
            "engine_binary_sha256": pg.sha256_file(pg.ENGINE) if os.path.isfile(pg.ENGINE) else None,
            "game_process_cmdline": self.gp.cmdline,
            "window_candidates": cands,
            "chosen_window": win,
            "exe": None,
        }
        if args.mode == "exe":
            exe = os.path.join(args.exe_root, args.game, args.game + ".exe")
            pck = os.path.join(args.exe_root, args.game, args.game + ".pck")
            identity["exe"] = {
                "path": exe, "exists": os.path.isfile(exe),
                "bytes": os.path.getsize(exe) if os.path.isfile(exe) else None,
                "sha256": pg.sha256_file(exe) if os.path.isfile(exe) else None,
                "pck_sha256": pg.sha256_file(pck) if os.path.isfile(pck) else None}

        env = probe_env()
        pg.write_json(os.path.join(self.outdir, "env.json"), env)

        st_settle = self.sample_state("00_settle")
        fr_settle = self.capture("settle", st_settle, note="before any input")
        self.step("settle", "the state the player is given, before any input was injected",
                  injection=None, state=st_settle, frame=fr_settle)

        # --- optional prep: make the game live (e.g. pong's explicit serve) ---
        for pa in args.prep_actions:
            kc = first_keycode(proj, pa)
            pre = self.sample_state("prep_%s_pre" % pa)
            before = self.capture("prep_%s_pre" % pa, pre)
            vk = godot_key_to_vk(kc)
            # FOCUS FIRST.  Measured the hard way in the first pong run: a real SPACE
            # sent while the game window was NOT foreground went to whatever WAS in
            # front, so `pong_serve` never fired -- and yet the state sha256 changed
            # anyway (the game's `_logTimer` moved), which is the same "a changed hash
            # is not 'the key worked'" trap this whole task is about.  The evidence for
            # that failed take is kept in runs/realinput/pong-prep-without-focus/.
            foc = try_foreground(win["hwnd"]) if win else {
                "ok": False, "why": "no game window was found for this process tree"}
            sent_dn = send_key(vk, up=False, extended=vk in EXTENDED_VKS)
            time.sleep(args.hold)
            sent_up = send_key(vk, up=True, extended=vk in EXTENDED_VKS)
            self.step("prep", "prep action %s sent as a REAL OS key" % pa,
                      injection={"channel": "OS_SendInput", "tool": "user32!SendInput",
                                 "godot_keycode": kc, "vk": vk,
                                 "keydown": sent_dn, "keyup": sent_up,
                                 "sent": [sent_dn["returned"], sent_up["returned"]]},
                      state=pre, frame=before)
            self.steps[-1]["focus"] = foc
            aft = self.sample_state("prep_%s_post" % pa)
            after = self.capture("prep_%s_post" % pa, aft)
            self.step("prep", "after prep action %s" % pa, state=aft, frame=after,
                      extra={"delta_vs_prev": len(pg.state_delta(pre["state"], aft["state"])),
                             "focus": foc})
            time.sleep(args.settle_input)

        # --- per action PAIR: the interleaved cycle ------------------------
        # Why an inverse PAIR and not "real arm then synthetic arm on the same action":
        # many actions are IDEMPOTENT in the state they write.  Pressing LEFT twice leaves
        # `DirectionX` at -1, so a second identical arm starting from the state the first
        # one produced has nothing left to change and reports "no response" for a path
        # that in fact works.  MEASURED on snake (runs/realinput/snake-fixed-order):
        # REAL snake_left changed the direction and the synthetic snake_left that followed
        # changed nothing, purely because the state was already -1.
        #
        # The cycle removes the artefact WITHOUT touching one byte of game state.  For an
        # inverse pair (X, Y):
        #     REAL X   -> X is now the active value
        #     PARSE Y  -> Y is now the active value   (also proves the synthetic path)
        #     PARSE X  -> X again   <- same action as arm 1, other channel, non-idempotent
        #     REAL Y   -> Y again   <- same action as arm 2, other channel, non-idempotent
        # Every arm starts from the *opposite* value, so every arm has something to change,
        # and each action is measured on BOTH channels from the same preceding value.
        def do_arm(tag, channel, action, kc, vk, from_state, from_frame, note):
            extended = vk in EXTENDED_VKS
            inj = {"channel": ("OS_SendInput" if channel == "real"
                               else "Input.parse_input_event"),
                   "tool": ("user32!SendInput" if channel == "real"
                            else "running_game_execute_gdscript"),
                   "godot_keycode": kc, "vk": vk, "extended": extended}
            focus = None
            t = self.step("real_key" if channel == "real" else "synthetic", note,
                          injection=inj, state=from_state, frame=from_frame)
            if channel == "real":
                focus = try_foreground(win["hwnd"]) if win else {
                    "ok": False, "why": "no game window was found for this process tree"}
                t["focus"] = focus
                if win:
                    w2 = [w for w in self.find_game_window()
                          if w["hwnd"] == (win or {}).get("hwnd")]
                    if w2:
                        t["window_rect_after_focus"] = w2[0]["rect"]
                dn = send_key(vk, up=False, extended=extended)
                time.sleep(args.hold)
                up = send_key(vk, up=True, extended=extended)
                t["injection"]["keydown"] = dn
                t["injection"]["keyup"] = up
                t["injection"]["sent"] = [dn["returned"], up["returned"]]
            else:
                code_dn = pg.probe_key_event(kc, True, "parse_input_event")
                _r, call_dn = self.gd(code_dn, "inject:parse:%s" % action)
                time.sleep(args.hold)
                code_up = pg.probe_key_event(kc, False, "parse_input_event")
                _r2, call_up = self.gd(code_up, "release:parse:%s" % action)
                t["injection"].update({
                    "seq": [call_dn.get("n"), call_up.get("n")],
                    "args": {"code": code_dn}, "release_args": {"code": code_up},
                    "trace_files": [self.trace_file(call_dn), self.trace_file(call_up)],
                    "keydown": {"ok": call_dn.get("ok"), "MCP_call_n": call_dn.get("n")},
                    "keyup": {"ok": call_up.get("ok"), "MCP_call_n": call_up.get("n")}})
            time.sleep(args.settle_input)
            post = self.sample_state(tag + "_post")
            fr_post = self.capture(tag + "_post", post,
                                   note="after the %s arm of %s"
                                        % ("REAL OS key" if channel == "real"
                                           else "synthetic", action))
            t_post = self.step("real_key" if channel == "real" else "synthetic",
                              "immediately after that arm", state=post, frame=fr_post)
            px = pg.png_changed(from_frame["path"], fr_post["path"]) \
                if (from_frame and fr_post) else None
            delta = pg.state_delta(from_state["state"], post["state"])
            ev = {"action": action, "channel": inj["channel"], "injection": t["injection"],
                  "focus": focus,
                  "from": {"state_sha256": from_state.get("state_sha256"),
                           "frame_sha256": (from_frame or {}).get("sha256"),
                           "frame_file": os.path.basename((from_frame or {}).get("path") or ""),
                           "drawn": (from_state.get("state") or {}).get("drawn")},
                  "to": {"state_sha256": post.get("state_sha256"),
                         "frame_sha256": (fr_post or {}).get("sha256"),
                         "frame_file": os.path.basename((fr_post or {}).get("path") or ""),
                         "drawn": (post.get("state") or {}).get("drawn")},
                  "state_change_count": len(delta), "state_changes": delta[:20],
                  "changed_pixels": (px or {}).get("changed_pixels"),
                  "frames_waited": ((post.get("state") or {}).get("drawn", 0) or 0)
                                   - ((from_state.get("state") or {}).get("drawn", 0) or 0)}
            t_post["arm_result"] = {"state_change_count": len(delta),
                                    "changed_pixels": (px or {}).get("changed_pixels")}
            return ev, post, fr_post

        rows = []
        pairs = [args.actions[i:i + 2] for i in range(0, len(args.actions), 2)]
        if any(len(p) < 2 for p in pairs):
            raise SystemExit("REFUSED: --actions must be given as INVERSE PAIRS (e.g. "
                             "pong_left_up pong_left_down); a lone action cannot be "
                             "measured on both channels without an idempotence artefact.")
        for pi, (x, y) in enumerate(pairs):
            spec = {}
            for a in (x, y):
                kc = first_keycode(proj, a)
                vk = godot_key_to_vk(kc)
                if kc is None or vk is None:
                    raise SystemExit("REFUSED: action %r has no keycode this tool can map "
                                     "to a Windows VK (keycode=%r)" % (a, kc))
                spec[a] = {"kc": kc, "vk": vk}
            # one no-input control window per cycle: the yardstick every arm is judged on
            c0 = self.sample_state("p%02d_ctl_pre" % pi)
            f0 = self.capture("p%02d_ctl_pre" % pi, c0, note="control start (no input)")
            time.sleep(args.control_seconds)
            c1 = self.sample_state("p%02d_ctl_end" % pi)
            f1 = self.capture("p%02d_ctl_end" % pi, c1, note="control end (no input)")
            t_ctl = self.step("control", "no-input control window for the pair (%s,%s)"
                                         % (x, y), state=c1, frame=f1)
            t_ctl["control"] = {
                "seconds": args.control_seconds,
                "state_delta": pg.state_delta(c0["state"], c1["state"]),
                "pixel_delta": pg.png_changed(f0["path"], f1["path"]) if (f0 and f1) else None}
            ctl = t_ctl["control"]
            ctl_count = len(ctl.get("state_delta") or [])
            ctl_px = max(0, ((ctl.get("pixel_delta") or {}).get("changed_pixels") or 0))

            arms = []
            cur_state, cur_frame = c1, f1
            plan = [("real", x, "JUDGE: REAL OS key for %s" % x),
                    ("parse", y, "JUDGE: synthetic parse_input_event for %s" % y),
                    ("parse", x, "JUDGE: synthetic parse_input_event for %s (the same "
                                 "action as arm 1, from the opposite value)" % x),
                    ("real", y, "JUDGE: REAL OS key for %s (the same action as arm 2)" % y)]
            for arm_i, (channel, action, note) in enumerate(plan):
                if not args.synthetic and channel == "parse":
                    continue
                tag = "p%02d_arm%d_%s_%s" % (pi, arm_i + 1, action, channel)
                ev, cur_state, cur_frame = do_arm(tag, channel, action,
                                                  spec[action]["kc"], spec[action]["vk"],
                                                  cur_state, cur_frame, note)
                ev["pair"] = [x, y]
                ev["arm_index"] = arm_i + 1
                ev["control_state_change_count"] = ctl_count
                ev["control_changed_pixels"] = ctl_px
                ev["beats_control"] = bool(
                    ev["state_change_count"] > ctl_count
                    or max(0, ev["changed_pixels"] or 0)
                    > max(int(ctl_px * 1.5), pg.P3_MIN_CHANGED_PIXELS))
                rows.append(ev)
            for a in (x, y):
                mine = [r for r in rows if r["pair"] == [x, y] and r["action"] == a]
                for r in mine:
                    log("  pair %-16s arm%d %-22s %-8s state=%d px=%s beats_control=%s"
                        % (x + "/" + y, r["arm_index"], r["action"], r["channel"],
                           r["state_change_count"], r["changed_pixels"], r["beats_control"]))

        # --- tail: let it run a moment with the window still focused -------
        time.sleep(args.tail)
        tail = self.sample_state("zz_tail")
        fr_tail = self.capture("zz_tail", tail, note="after everything")
        self.step("tail", "after the input round", state=tail, frame=fr_tail)

        summary = self.summarise(proj, identity, rows)
        pg.write_json(os.path.join(self.outdir, "steps.json"),
                      {"game": args.game, "steps": self.steps})
        pg.write_json(os.path.join(self.outdir, "frames.json"), self.frames)
        pg.write_json(os.path.join(self.outdir, "session.json"), identity)
        pg.write_json(os.path.join(self.outdir, "real_input.json"), summary)
        if self.frames:
            note = ("OS window %s  root viewport %s  declared %s"
                    % (self._osd.get("display_window_size"),
                       self._osd.get("root_viewport_size"),
                       self._osd.get("declared_viewport")))
            try:
                pg.build_filmstrip(self.frames,
                                   os.path.join(self.outdir, "filmstrip.png"),
                                   "%s -- REAL OS keys via SendInput + synthetic arm" % args.game,
                                   note=note)
            except Exception as e:  # noqa: BLE001
                self.errors.append({"at": "filmstrip", "error": "%s: %s" % (type(e).__name__, e)})
        return summary

    def summarise(self, proj, identity, rows):
        """The two-path comparison table (X3) built from the interleaved arms."""
        mode = None
        real_arms = [r for r in rows if r["channel"] == "OS_SendInput"]
        syn_arms = [r for r in rows if r["channel"] == "Input.parse_input_event"]
        real_ok = [r for r in real_arms
                   if (r["injection"].get("keydown") or {}).get("returned") == 1
                   and r["beats_control"]]
        focus_ok = any((r["focus"] or {}).get("ok") for r in real_arms)
        sent_ok = all((r["injection"].get("keydown") or {}).get("returned") == 1
                      for r in real_arms) if real_arms else False
        if real_ok:
            mode = "1-real-key-works"
        elif not focus_ok or not sent_ok:
            mode = "2-local-environment-limit"
        else:
            mode = "3-defect-os-events-not-delivered"
        syn_ok = [r for r in syn_arms if r["beats_control"]]
        # per-action, cross-channel comparison: the two arms that share an action come from
        # the cycle (arm 1 REAL X vs arm 3 PARSE X; arm 2 PARSE Y vs arm 4 REAL Y)
        comparisons = []
        for action in dict.fromkeys([r["action"] for r in rows]):
            pair_arms = [r for r in rows if r["action"] == action]
            real = next((r for r in pair_arms if r["channel"] == "OS_SendInput"), None)
            syn = next((r for r in pair_arms if r["channel"] == "Input.parse_input_event"), None)
            comparisons.append({
                "action": action,
                "real_os_key": None if real is None else {
                    "arm_index": real["arm_index"],
                    "state_change_count": real["state_change_count"],
                    "state_changes": real["state_changes"],
                    "changed_pixels": real["changed_pixels"],
                    "beats_control": real["beats_control"],
                    "sent": (real["injection"] or {}).get("sent"),
                    "focus_ok": (real["focus"] or {}).get("ok"),
                    "from_state_sha256": real["from"]["state_sha256"],
                    "to_state_sha256": real["to"]["state_sha256"],
                    "from_frame": real["from"], "to_frame": real["to"]},
                "synthetic_parse": None if syn is None else {
                    "arm_index": syn["arm_index"],
                    "state_change_count": syn["state_change_count"],
                    "state_changes": syn["state_changes"],
                    "changed_pixels": syn["changed_pixels"],
                    "beats_control": syn["beats_control"],
                    "seq": (syn["injection"] or {}).get("seq"),
                    "from_state_sha256": syn["from"]["state_sha256"],
                    "to_state_sha256": syn["to"]["state_sha256"],
                    "from_frame": syn["from"], "to_frame": syn["to"]},
            })
        out = {
            "game": self.args.game,
            "when": time.strftime("%Y-%m-%d %H:%M:%S"),
            "mode": self.args.mode,
            "identity": identity,
            "declared_viewport": proj["declared_viewport"],
            "osd_window": self._osd,
            "actions": self.args.actions,
            "hold_seconds": self.args.hold,
            "protocol": {
                "cycle": "REAL X -> PARSE Y -> PARSE X -> REAL Y, one no-input control "
                         "window per cycle",
                "why": "many actions are idempotent in the value they write, so a second "
                       "identical arm from the state the first produced would report 'no "
                       "response' for a path that works; the cycle makes every arm start "
                       "from the opposite value without touching any game state",
                "attribution": "an arm counts only when it BEATS the no-input control "
                               "window (state changes > control, or pixels > "
                               "max(1.5*control, %d))" % pg.P3_MIN_CHANGED_PIXELS},
            "real_key_arm": {
                "arms": len(real_arms),
                "sendinput_sent_1_of_1": sent_ok,
                "focus_achieved": focus_ok,
                "arms_beating_control": len(real_ok),
                "rows": [{"pair": r["pair"], "arm_index": r["arm_index"],
                          "action": r["action"], "vk": r["injection"].get("vk"),
                          "focus_ok": (r["focus"] or {}).get("ok"),
                          "keydown": (r["injection"] or {}).get("keydown"),
                          "keyup": (r["injection"] or {}).get("keyup"),
                          "control_state_change_count": r["control_state_change_count"],
                          "control_changed_pixels": r["control_changed_pixels"],
                          "state_change_count": r["state_change_count"],
                          "state_changes": r["state_changes"],
                          "changed_pixels": r["changed_pixels"],
                          "beats_control": r["beats_control"],
                          "frames_waited": r["frames_waited"],
                          "from": r["from"], "to": r["to"]} for r in real_arms]},
            "synthetic_arm": {
                "channel": "Input.parse_input_event (inside the game process)",
                "arms": len(syn_arms),
                "arms_beating_control": len(syn_ok),
                "rows": [{"pair": r["pair"], "arm_index": r["arm_index"],
                          "action": r["action"],
                          "control_state_change_count": r["control_state_change_count"],
                          "control_changed_pixels": r["control_changed_pixels"],
                          "state_change_count": r["state_change_count"],
                          "state_changes": r["state_changes"],
                          "changed_pixels": r["changed_pixels"],
                          "beats_control": r["beats_control"],
                          "seq": (r["injection"] or {}).get("seq"),
                          "trace_files": (r["injection"] or {}).get("trace_files"),
                          "from": r["from"], "to": r["to"]} for r in syn_arms]},
            "comparison_table": comparisons,
            "conclusion": {
                "mode": mode,
                "real_key_effective": bool(real_ok),
                "focus_and_delivery_established": bool(focus_ok and sent_ok),
                "synthetic_effective": bool(syn_ok),
                "statement": REAL_INPUT_STATEMENT.get(mode),
            },
            "errors": self.errors,
        }
        return out


REAL_INPUT_STATEMENT = {
    "1-real-key-works":
        "Real OS keys ARE delivered: SendInput returned 1/1, the game window held the "
        "foreground, and the game's own state/pixels changed with the key.  Under this "
        "machine the real-key acceptance path is available.",
    "2-local-environment-limit":
        "Real OS keys could not be delivered (SendInput refused, or no window could hold "
        "the foreground).  This is a LOCAL ENVIRONMENT LIMIT of this session, not evidence "
        "about the game: with this limit, a human-key acceptance cannot be performed here.",
    "3-defect-os-events-not-delivered":
        "Real OS keys WERE sent (SendInput returned 1/1) and the game window DID hold the "
        "foreground, yet the game's state and pixels did not react, while the same action "
        "through Input.parse_input_event did.  That is a game-side input defect above "
        "Input::parse_input_event (the OS event never reaches the game), not a local "
        "environment limit.",
}


def analyse_and_hash(path):
    a = pg.analyse_frame(path)
    return a


def engine_version():
    try:
        r = subprocess.run([pg.ENGINE, "--version"], cwd=pg.ENGINE_CWD,
                           stdout=subprocess.PIPE, stderr=subprocess.STDOUT, timeout=60)
        return r.stdout.decode("utf-8", "replace").strip()
    except Exception as e:  # noqa: BLE001
        return "ERROR %s: %s" % (type(e).__name__, e)


def first_keycode(proj, action):
    spec = (proj.get("actions") or {}).get(action)
    if not spec:
        return None
    return next((c for c in spec.get("keycode", []) if c), None)


def log(msg):
    print(msg, flush=True)


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------
def main(argv=None):
    ap = argparse.ArgumentParser(description="TASK-131 OS-level real-input probe")
    sub = ap.add_subparsers(dest="cmd")

    e = sub.add_parser("env", help="read-only capability probe (X1)")
    e.add_argument("--out", default=os.path.join(RUNS_REAL, "_env", "env.json"))

    r = sub.add_parser("run", help="real OS key vs synthetic injection, on one instance")
    r.add_argument("--game", required=True)
    r.add_argument("--out-name", default="",
                   help="evidence directory under runs/realinput (default: the game name).  "
                        "Used when the same game is measured under two parameter sets.")
    r.add_argument("--mode", default="exe", choices=("exe", "project"))
    r.add_argument("--exe-root", default=DEFAULT_EXE_ROOT)
    r.add_argument("--actions", nargs="*", default=None,
                   help="actions to test; default = the game's own first N declared actions")
    r.add_argument("--prep-actions", nargs="*", default=[],
                   help="actions sent as REAL OS keys BEFORE the measured round (e.g. "
                        "pong_serve, so the game is live instead of parked)")
    r.add_argument("--hold", type=float, default=0.5)
    r.add_argument("--control-seconds", type=float, default=0.62,
                   help="length of the no-input control window each arm is judged against "
                        "(default 0.62 = the 0.5 s hold + 0.12 s of readback slack)")
    r.add_argument("--settle", type=float, default=4.0)
    r.add_argument("--settle-input", type=float, default=0.35)
    r.add_argument("--tail", type=float, default=1.0)
    r.add_argument("--port", type=int, default=DEFAULT_PORT)
    r.add_argument("--ready-timeout", type=float, default=240)
    r.add_argument("--call-timeout", type=float, default=40)
    r.add_argument("--max-actions", type=int, default=4,
                   help="how many declared actions to test when --actions is omitted; "
                        "rounded down to an even number because the protocol needs INVERSE "
                        "PAIRS (left/right, up/down)")
    r.add_argument("--no-synthetic", dest="synthetic", action="store_false", default=True)
    r.add_argument("--fresh", action="store_true", default=True)
    r.add_argument("--show-nodes", nargs="*", default=[],
                   help="node paths whose fields the step table quotes per step")

    s = sub.add_parser("selftest", help="the struct/send checks alone, no game started")
    s.add_argument("--vk", type=lambda x: int(x, 0), default=0x87)

    args = ap.parse_args(argv)

    if args.cmd == "env":
        env = probe_env()
        pg.write_json(args.out, env)
        log(json.dumps({k: env[k] for k in
                        ("this_process", "monitor_metrics", "input_desktop",
                         "foreground_lock_timeout", "sendinput_selftest")},
                       ensure_ascii=False, indent=1))
        log("wrote %s" % os.path.abspath(args.out))
        return 0

    if args.cmd == "selftest":
        out = {"sizeof_INPUT": ctypes.sizeof(INPUT), "sendinput": sendinput_selftest(args.vk)}
        log(json.dumps(out, ensure_ascii=False, indent=1))
        return 0

    if args.cmd == "run":
        if not args.actions:
            proj = pg.parse_project(args.game)
            n = max(2, args.max_actions - (args.max_actions % 2))
            args.actions = list(proj["actions_declared"])[:n]
        target_dir = os.path.join(RUNS_REAL, args.out_name or args.game)
        if os.path.isdir(target_dir) and args.fresh:
            import shutil
            shutil.rmtree(target_dir)
        runner = Runner(args)
        try:
            summary = runner.run()
        finally:
            if runner.gp:
                log("stop: %s" % json.dumps(runner.gp.stop()))
        log(json.dumps(summary["conclusion"], ensure_ascii=False, indent=1))
        log("wrote %s" % os.path.join(RUNS_REAL, args.out_name or args.game,
                                      "real_input.json"))
        return 0

    ap.print_help()
    return 2


if __name__ == "__main__":
    sys.exit(main())
