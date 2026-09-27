# -*- coding: utf-8 -*-
"""TASK-139: run a short sequence of commands, one at a time, through the ledger wrapper.

Written because two long jobs cannot share a port, and the queue helpers in this batch are
themselves part of its command record.  Each step is executed as a child process with a fresh
`t139_cmd.py` invocation, so every one of them lands in the shared ledger.

Usage (cmd):
    D:\\Anaconda\\python.exe runs\\model-player\\_scripts\\t139_chain.py
"""
from __future__ import print_function

import os
import subprocess
import sys
import time

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.abspath(os.path.join(HERE, "..", "..", ".."))
PY = r"D:\Anaconda\python.exe"
CWD = ROOT if os.path.basename(ROOT) == "godot-mcp" else os.path.join(ROOT, "godot-mcp")
CMD = os.path.join(HERE, "t139_cmd.py")

STEPS = [
    # 1. a clean determinism probe at w90 (the earlier attempt collided on a shared port)
    [PY, os.path.join(HERE, "t139_determinism.py"), "--arm", "scripted", "--window", "90",
     "--games", "asteroids", "pacman", "tetris", "pong", "breakout"],
    # 2. a COMPLETE scripted sweep at w90, so that rung's results file is a full 20-game
    #    record rather than the 5 rows a partial re-run left in it
    [PY, os.path.join(HERE, "t139_sweep.py"), "--arm", "scripted", "--window", "90"],
    # 3. the same for w30
    [PY, os.path.join(HERE, "t139_sweep.py"), "--arm", "scripted", "--window", "30"],
]


def main(argv):
    for i, cmd in enumerate(STEPS, 1):
        print("=" * 78)
        print("CHAIN step %d/%d: %s" % (i, len(STEPS), " ".join(cmd)), flush=True)
        t0 = time.time()
        rc = subprocess.call([PY, CMD, "--cwd", CWD, "--"] + cmd, cwd=CWD)
        print("CHAIN step %d done rc=%s in %.1fs" % (i, rc, time.time() - t0), flush=True)
    print("CHAIN complete")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
