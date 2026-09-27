# -*- coding: utf-8 -*-
"""TASK-139: print the per-step detail behind one SENSITIVE entry from t139_sensitivity.json.

Usage (cmd):
    D:\\Anaconda\\python.exe runs\\model-player\\_scripts\\t139_flip.py model asteroids
    D:\\Anaconda\\python.exe runs\\model-player\\_scripts\\t139_flip.py scripted pong
"""
from __future__ import print_function

import io
import json
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
SRC = os.path.join(HERE, "t139_sensitivity.json")


def main(argv):
    arm = argv[0]
    game = argv[1]
    rep = json.load(io.open(SRC, encoding="utf-8"))
    for a in rep["arms"]:
        if a["arm"] != arm:
            continue
        e = a["games"].get(game)
        if not e:
            print("no such game %s in arm %s" % (game, arm))
            return 2
        print("ARM %s GAME %s" % (arm, game))
        print("verdict_by_window: %s" % json.dumps(e["verdict_by_window"]))
        print("pass_by_window:    %s" % json.dumps(e["pass_by_window"]))
        print("player_json:       %s" % json.dumps(e["player_json"]))
        for w, r in sorted(e["runs"].items()):
            print("  window %s: %s" % (w, json.dumps(r, ensure_ascii=False)))
        print("affected steps: %s" % e.get("affected_step_numbers"))
        for x in (e.get("affected_steps") or []):
            print("---- step %s action=%s" % (x.get("step"), x.get("action")))
            print("     differences: %s" % json.dumps(x.get("differences"),
                                                      ensure_ascii=False))
            print("     rung A: %s" % json.dumps(x.get("rung_a"), ensure_ascii=False))
            print("     rung B: %s" % json.dumps(x.get("rung_b"), ensure_ascii=False))
        if rep.get("asteroids") and game == "asteroids" and arm == "model":
            print("ASTEROIDS DETAIL:")
            for w, sd in sorted((rep["asteroids"].get("steps_by_window") or {}).items()):
                print("  window %s:" % w)
                for st, v in sorted((sd or {}).items(), key=lambda kv: int(kv[0])):
                    print("    step %s %s" % (st, json.dumps(v, ensure_ascii=False)))
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
