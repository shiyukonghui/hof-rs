# -*- coding: utf-8 -*-
"""TASK-140 §1.B.1 / §3.Y6: the asteroids RESPAWN, driven directly (no model, no arm).

The two arms measure the game but they decide when to act and they stop early, and in every
TASK-140 arm run the ship happened not to be hit.  This probe puts the ship on a rock with the
game's OWN `ForceTestState` hook, then samples the game's OWN exported properties while the hit
and the respawn happen, and captures frames.  It runs the same experiment TWICE:

  * `switchable_variant` -- `RespawnDelay = 0` set through the game's own property (the
    pre-TASK-140 behaviour), so "the ship never comes back and the world freezes" is measured,
    not remembered;
  * `default`            -- the shipped default (`RespawnDelay = 1.0`, `RespawnInvuln = 1.5`).

Every number is the game's: `Lives`, `ShipAlive`, `RespawnTimer`, `InvulnTimer`,
`ShipInvulnerable`, `ShipVisible`, `Respawns`, `LastEvent`, plus a pixel-difference count
computed from the captured frames (same measure the criterion's `pixel_diff` is).

Usage (through the ledger wrapper):
    t140_cmd.py --cwd F:\\moonbit-hof-rs\\godot-mcp -- <py> runs\\model-player\\_scripts\\t140_respawn_probe.py
"""
from __future__ import print_function

import base64
import io
import json
import os
import sys
import time

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.abspath(os.path.join(HERE, "..", "..", ".."))
TOOLS = os.path.join(ROOT, "tools")
sys.path.insert(0, TOOLS)

import playability_gate as pg  # noqa: E402

OUT = os.path.join(ROOT, "runs", "model-player", "t140-respawn-probe")
PORT = 9989
WATCH = ("Lives", "ShipAlive", "RespawnTimer", "InvulnTimer", "ShipInvulnerable",
         "ShipVisible", "Respawns", "GameOver", "Ticks", "ShipX", "ShipY", "ShipVelX",
         "ShipVelY", "FirstRockX", "FirstRockY", "LastEvent")


def pixels_diff(a, b):
    """Count the pixels that differ between two PNGs (the criterion's own measure)."""
    try:
        from PIL import Image
        ia = Image.open(a).convert("RGB")
        ib = Image.open(b).convert("RGB")
        if ia.size != ib.size:
            return None
        da = ia.tobytes()
        db = ib.tobytes()
        return sum(1 for i in range(0, len(da), 3) if da[i:i + 3] != db[i:i + 3])
    except Exception as e:  # noqa: BLE001
        return "error: %s" % type(e).__name__


class Game(object):
    def __init__(self, name, port):
        self.name = name
        self.port = port
        self.dir = os.path.join(OUT, name)
        self.calls = os.path.join(self.dir, "mcp-calls")
        self.frames = os.path.join(self.dir, "frames")
        for d in (self.dir, self.frames):
            if not os.path.isdir(d):
                os.makedirs(d)
        self.gp = None
        self.mcp = None
        self.nframes = 0

    def start(self):
        self.gp = pg.GameProcess(self.name, self.port, self.dir)
        ok, secs = self.gp.start(240)
        if not ok:
            raise SystemExit("game %s never came up on port %d" % (self.name, self.port))
        self.mcp = pg.Mcp(self.port, self.calls)
        self.mcp.tools_list()
        time.sleep(3.0)
        return secs

    def stop(self):
        if self.gp:
            self.gp.stop()

    def gd(self, code, at="probe"):
        r = self.mcp.call_tool("running_game_execute_gdscript", {"code": code}, timeout=60)
        if not r.get("ok"):
            return {"__error": r.get("error"), "__at": at}
        return r["value"].get("result")

    def state(self):
        nodes = self.gd(pg.probe_state_source(), "state")
        if not isinstance(nodes, dict) or "nodes" not in nodes:
            return {}
        best = None
        for path, entry in (nodes.get("nodes") or {}).items():
            if path.rsplit("/", 1)[-1] == "Main":
                if best is None or len(path) < len(best[0]):
                    best = (path, entry)
        if best is None:
            return {}
        return dict((k, v) for k, v in best[1].items()
                    if k not in ("script", "c", "name", "vis"))

    def frame(self, label):
        r = self.mcp.call_tool("running_game_capture_screenshot", {})
        if not r.get("ok"):
            return None
        b64 = r["value"].get("image_base64")
        if not b64:
            return None
        self.nframes += 1
        p = os.path.join(self.frames, "%03d_%s.png" % (self.nframes, label))
        with open(p, "wb") as fh:
            fh.write(base64.b64decode(b64))
        return p

    def put_on_rock(self):
        """The game's own hook: place the ship exactly on the rock at (650, 130)."""
        return self.gd('var n = get_node("/root/Main")\n'
                       'var r = n.ForceTestState("ship=650,130")\n'
                       'return {"force": r, "dump": n.Dump()}', "put_on_rock")


def sample(g, tag, n=24, gap=0.12):
    """Sample the game's own exported properties over `n` reads, capturing frames."""
    rows = []
    prev_frame = None
    for i in range(1, n + 1):
        st = g.state()
        fr = g.frame("%s_%02d" % (tag, i))
        px = pixels_diff(prev_frame, fr) if prev_frame and fr else None
        prev_frame = fr
        rows.append({"i": i, "t_ms": round(i * gap * 1000),
                     "frame": fr, "pixel_diff_vs_prev_frame": px,
                     "state": dict((k, st.get(k)) for k in WATCH)})
        time.sleep(gap)
    return rows


def run_case(g, tag, respawn_delay, respawn_invuln):
    case = {"tag": tag, "respawn_delay": respawn_delay, "respawn_invuln": respawn_invuln}
    setup = g.gd('var n = get_node("/root/Main")\n'
                 'n.RespawnDelay = %s\n'
                 'n.RespawnInvuln = %s\n'
                 'return {"respawn_delay": n.RespawnDelay, "respawn_invuln": n.RespawnInvuln}'
                 % (float(respawn_delay), float(respawn_invuln)), "setup_" + tag)
    case["setup"] = setup
    before = g.state()
    case["before"] = dict((k, before.get(k)) for k in WATCH)
    case["before_frame"] = g.frame("%s_before" % tag)
    case["hit"] = g.put_on_rock()
    time.sleep(0.05)
    after_hit = g.state()
    case["right_after_put"] = dict((k, after_hit.get(k)) for k in WATCH)
    case["samples"] = sample(g, tag, n=24, gap=0.12)
    case["pixel_diff_series"] = [r["pixel_diff_vs_prev_frame"] for r in case["samples"]]
    case["ship_alive_series"] = [r["state"]["ShipAlive"] for r in case["samples"]]
    case["lives_series"] = [r["state"]["Lives"] for r in case["samples"]]
    case["respawns_series"] = [r["state"]["Respawns"] for r in case["samples"]]
    case["invuln_series"] = [r["state"]["InvulnTimer"] for r in case["samples"]]
    case["frozen_after_hit"] = all(r["pixel_diff_vs_prev_frame"] == 0
                                   for r in case["samples"][4:])
    case["zero_diff_run_length"] = max(
        [0] + [len(list(grp)) for grp in _runs(case["pixel_diff_series"]) if grp == 0]) \
        if False else _longest_run(case["pixel_diff_series"], 0)
    return case


def _runs(seq):
    return []


def _longest_run(seq, value):
    best = cur = 0
    for x in seq:
        if x == value:
            cur += 1
            best = max(best, cur)
        else:
            cur = 0
    return best


def main():
    g = Game("asteroids", PORT)
    out = {"what": "TASK-140 §1.B.1: the ship is placed ON a rock with the game's own hook, "
                   "then the hit and the respawn are sampled from the game's own properties",
           "port": PORT, "cases": []}
    try:
        out["start_seconds"] = g.start()
        out["settle"] = g.gd('var n = get_node("/root/Main")\nreturn n.Dump()', "settle")
        out["settle_frame"] = g.frame("settle")
        out["cases"].append(run_case(g, "variant_respawn_delay_0", 0.0, 0.0))
        # put the world back to a clean deterministic state before the second case
        g.gd('var n = get_node("/root/Main")\nreturn n.ForceTestState("")', "reset")
        time.sleep(0.4)
        out["cases"].append(run_case(g, "default_respawn_1s", 1.0, 1.5))
    finally:
        g.stop()
    for c in out["cases"]:
        print("[%s] delay=%s invuln=%s  ship_alive=%s lives=%s respawns=%s "
              "longest_zero_pixel_run=%s frozen_after_hit=%s"
              % (c["tag"], c["respawn_delay"], c["respawn_invuln"],
                 c["ship_alive_series"][:12], c["lives_series"][:12],
                 c["respawns_series"][:12], c["zero_diff_run_length"], c["frozen_after_hit"]))
    with io.open(os.path.join(OUT, "probe.json"), "w", encoding="utf-8") as fh:
        fh.write(json.dumps(out, ensure_ascii=False, indent=1))
    print("wrote %s" % os.path.join(OUT, "probe.json"))
    return 0


if __name__ == "__main__":
    sys.exit(main())
