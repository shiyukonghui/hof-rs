# -*- coding: utf-8 -*-
"""TASK-139 recon: for the 5 games with a known 'legal refusal' defect, list which steps
FAILed and whether the game's own refusal field moved (i.e. was a legitimate refusal).
"""
from __future__ import print_function

import io
import json
import os
import sys

ROOT = os.path.abspath(os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", ".."))
GAMES = ("match3", "minesweeper", "pacman", "sokoban", "towerdefense")


def main(argv):
    prefix = argv[0] if argv else "t138-scripted"
    for g in GAMES:
        p = os.path.join(ROOT, "runs", "model-player", prefix, g, "scripted", "steps.jsonl")
        if not os.path.isfile(p):
            print("== %s: NO FILE %s" % (g, p))
            continue
        recs = [json.loads(l) for l in io.open(p, encoding="utf-8").read().splitlines()
                if l.strip()]
        pj = json.load(io.open(os.path.join(os.path.dirname(p), "player.json"), encoding="utf-8"))
        print("== %s  verdict=%s strict=%s game_side=%s injected=%s accepted=%s changed=%s "
              "fail=%s" % (g, pj.get("verdict"), pj.get("strict_verdict"),
                           pj.get("game_side_verdict"), pj.get("injected_steps"),
                           pj.get("accepted_steps"), pj.get("changed_steps_of_accepted"),
                           pj.get("fail_steps")))
        for r in recs:
            ack = r.get("ack") or {}
            log = r.get("change") or {}
            dl = r.get("state_delta") or []
            keys = [d.get("key", "").rsplit(".", 1)[-1] for d in dl]
            ref = [k for k in keys if "refus" in k.lower() or "reject" in k.lower()]
            print("   step=%2s act=%-16s verdict=%-34s accepted=%-5s changed=%-5s "
                  "px=%s ctl=%s mv=%s refkeys=%s"
                  % (r.get("step"), (r.get("action") or {}).get("action"),
                     r.get("step_verdict"), ack.get("accepted"), log.get("changed"),
                     r.get("pixel_diff"), (log.get("control_pixels")),
                     log.get("gameplay_movement"), ref))
            if r.get("step_verdict") == "FAIL_no_change_after_accepted_input":
                print("        delta keys: %s" % keys)
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
