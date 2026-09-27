# -*- coding: utf-8 -*-
"""TASK-139: run one sweep arm, after waiting for a given set of other runs to finish.

Usage (cmd):
    D:\\Anaconda\\python.exe runs\\model-player\\_scripts\\t139_after.py --wait-prefix t139-jev-v3-w30 --arm model --window 90
    D:\\Anaconda\\python.exe runs\\model-player\\_scripts\\t139_after.py --wait-prefix t139-jev-v3-w90 --arm playjev --window 30

Why: the engine is shared by every arm (one game process at a time is the safe assumption),
so a later arm waits for the earlier one's `player.json` count to stop growing instead of
starting a fourth engine process.  Bounded: it gives up after `--timeout` seconds and says so.
"""
from __future__ import print_function

import io
import json
import os
import subprocess
import sys
import time

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.abspath(os.path.join(HERE, "..", "..", ".."))
RUNS = os.path.join(ROOT, "runs", "model-player")
PY = r"D:\Anaconda\python.exe"
SWEEP = os.path.join(HERE, "t139_sweep.py")


def count_runs(prefix):
    base = os.path.join(RUNS, prefix)
    n = 0
    if not os.path.isdir(base):
        return 0
    for g in os.listdir(base):
        for backend in ("scripted", "jev", "playjev", "model"):
            if os.path.isfile(os.path.join(base, g, backend, "player.json")):
                n += 1
                break
    return n


def main(argv):
    wait_prefix = None
    wait_for = 20
    timeout = 3600
    if "--wait-prefix" in argv:
        wait_prefix = argv[argv.index("--wait-prefix") + 1]
    if "--wait-for" in argv:
        wait_for = int(argv[argv.index("--wait-for") + 1])
    if "--timeout" in argv:
        timeout = int(argv[argv.index("--timeout") + 1])
    t0 = time.time()
    if wait_prefix:
        # wait until the count has reached the target AND stayed there for 3 polls
        stable = 0
        last = -1
        while time.time() - t0 < timeout:
            n = count_runs(wait_prefix)
            if n >= wait_for and n == last:
                stable += 1
                if stable >= 3:
                    break
            else:
                stable = 0
            last = n
            time.sleep(10)
        print("wait done: %s has %d player.json after %.1fs"
              % (wait_prefix, count_runs(wait_prefix), time.time() - t0))
    cmd = [PY, SWEEP] + [a for a in argv if a not in ("--wait-prefix", wait_prefix)
                         and a not in ("--wait-for", "--timeout")]
    # strip the numeric arguments of the flags we consumed
    out = []
    skip = False
    for i, a in enumerate(argv):
        if a in ("--wait-prefix", "--wait-for", "--timeout"):
            skip = True
            continue
        if skip:
            skip = False
            continue
        out.append(a)
    cmd = [PY, SWEEP] + out
    print("running: %s" % " ".join(cmd))
    return subprocess.call(cmd, cwd=ROOT)


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
