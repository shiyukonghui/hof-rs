# -*- coding: utf-8 -*-
"""TASK-139 debug: what terminal-state evidence did the asteroids runs record?"""
from __future__ import print_function

import io
import json
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.abspath(os.path.join(HERE, "..", "..", ".."))
RUNS = os.path.join(ROOT, "runs", "model-player")


def main(argv):
    for rel in argv:
        p = os.path.join(RUNS, rel)
        pj = os.path.join(p, "player.json")
        if not os.path.isfile(pj):
            print("MISSING %s" % pj)
            continue
        s = json.load(io.open(pj, encoding="utf-8"))
        print("== %s" % rel)
        for k in ("verdict", "counts_as_pass", "accepted_and_changed_rate", "fail_steps",
                  "unchanged_terminal", "terminal_stop", "settle_liveness_terminal",
                  "liveness", "injected_steps", "steps"):
            print("   %-28s = %s" % (k, json.dumps(s.get(k), ensure_ascii=False)[:220]))
        print("   keys: %s" % sorted(k for k in s.keys() if "term" in k or "live" in k))
        # the markers of the last steps
        st = os.path.join(p, "steps.jsonl")
        if os.path.isfile(st):
            recs = [json.loads(l) for l in io.open(st, encoding="utf-8") if l.strip()]
            for r in recs:
                m = r.get("markers") or {}
                if m.get("Lives") in (0, 1) or r.get("step_verdict", "").startswith("FAIL"):
                    print("   step %s action=%s lives=%s gameover=%s px=%s mv=%s verdict=%s"
                          % (r.get("step"), (r.get("action") or {}).get("action"),
                             m.get("Lives"), m.get("GameOver"), r.get("pixel_diff"),
                             r.get("gameplay_movement"), r.get("step_verdict")))
            print("   last-step markers: %s" % json.dumps(recs[-1].get("markers"),
                                                           ensure_ascii=False))
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
