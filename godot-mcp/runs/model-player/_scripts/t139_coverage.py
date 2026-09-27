# -*- coding: utf-8 -*-
"""TASK-139: print the games present in each arm's results file and in its run tree.

Why this exists: a partial re-run of one arm once OVERWROTE that arm's full results file with
its 5 rows, and an accidental partial re-run later overwrote the other rung's file.  "How many
games does this arm's record actually cover" therefore has to be a checked number, not an
assumption.  This is that check.

Usage (cmd):
    D:\\Anaconda\\python.exe runs\\model-player\\_scripts\\t139_coverage.py
"""
from __future__ import print_function

import io
import json
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.abspath(os.path.join(HERE, "..", "..", ".."))
RUNS = os.path.join(ROOT, "runs", "model-player")

GAMES = ("asteroids", "bomberman", "breakout", "flappy", "frogger", "game2048",
         "lunarlander", "match3", "minesweeper", "missilecommand", "pacman", "platformer",
         "pong", "puzzlebobble", "rtype", "snake", "sokoban", "spaceinvaders", "tetris",
         "towerdefense")
PLAYJEV = ("tetris", "pong", "asteroids", "snake", "game2048", "rtype", "match3", "pacman",
           "sokoban", "minesweeper")
PREFIXES = [("t139-scripted-w30", "scripted", GAMES),
            ("t139-scripted-w90", "scripted", GAMES),
            ("t139-jev-v3-w30", "jev", GAMES),
            ("t139-jev-v3-w90", "jev", GAMES),
            ("t139-playjev-v3-w30", "playjev", PLAYJEV),
            ("t139-determinism-w30", "scripted", ("asteroids", "pacman", "tetris", "pong",
                                                  "breakout")),
            ("t139-determinism-w90", "scripted", ("asteroids", "pacman", "tetris", "pong",
                                                  "breakout"))]


def main(argv):
    for prefix, backend, want in PREFIXES:
        base = os.path.join(RUNS, prefix)
        got = []
        if os.path.isdir(base):
            for g in sorted(os.listdir(base)):
                if os.path.isfile(os.path.join(base, g, backend, "player.json")):
                    got.append(g)
        # the per-arm results file
        rp = os.path.join(HERE, "t139_results_%s.json" % prefix)
        rows = None
        if os.path.isfile(rp):
            rows = [r.get("game") for r in json.load(io.open(rp, encoding="utf-8"))]
        missing = [g for g in want if g not in got]
        print("%-24s backend=%-8s evidence=%2d/%2d results_file=%s %s"
              % (prefix, backend, len(got), len(want),
                 (len(rows) if rows is not None else "MISSING"),
                 ("MISSING " + json.dumps(missing) if missing else "complete")))
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
