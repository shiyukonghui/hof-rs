# -*- coding: utf-8 -*-
"""TASK-139 recon: current refusal_evidence + gameplay items for the 5 games under test."""
from __future__ import print_function

import io
import json
import os
import sys

ROOT = os.path.abspath(os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", ".."))
CTRL = os.path.join(ROOT, "tools", "playability_controls.json")
GAMES = ("match3", "minesweeper", "pacman", "sokoban", "towerdefense")


def main(argv):
    doc = json.load(io.open(CTRL, encoding="utf-8"))
    print("TOP-LEVEL KEYS: %s" % list(doc.keys()))
    for g in GAMES:
        d = (doc.get("games") or {}).get(g) or {}
        print("== %s keys=%s" % (g, sorted(d.keys())))
        print("   refusal_evidence: %s" % json.dumps(d.get("refusal_evidence"),
                                                      ensure_ascii=False)[:600])
        obs = d.get("gameplay_observables") or {}
        print("   gameplay items: %s" % (obs.get("items")))
        print("   capabilities: %s" % json.dumps(d.get("capabilities"), ensure_ascii=False))
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
