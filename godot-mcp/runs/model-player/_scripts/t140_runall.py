# -*- coding: utf-8 -*-
"""TASK-140 §1.A.4: the whole reporting-window sweep, SERIAL, in one ledgered driver.

Order (iron rule 4: the model service is serial; iron rule 6: every run has its own port):

    scripted w90 r1 (20)  -> scripted w90 r2 (20)
    model    w90 r1 (20)  -> model    w90 r2 (20)
    playjev  w90 r1 (10)  -> playjev  w90 r2 (10)

Each arm/round is a separate `t140_sweep.py` call, so the per-game commands and their console
outputs land in the ledger and in their own `.out.txt` files exactly as in a hand-typed run.

Usage (through the ledger wrapper):
    t140_cmd.py --cwd F:\\moonbit-hof-rs\\godot-mcp -- <py> runs\\model-player\\_scripts\\t140_runall.py
"""
from __future__ import print_function

import io
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.abspath(os.path.join(HERE, "..", "..", ".."))
sys.path.insert(0, HERE)
import t140_cmd  # noqa: E402

PY = r"D:\Anaconda\python.exe"
SWEEP = os.path.join(HERE, "t140_sweep.py")

PLAN = [
    ("scripted", 1, 9981),
    ("scripted", 2, 9982),
    ("model", 1, 9983),
    ("model", 2, 9984),
    ("playjev", 1, 9985),
    ("playjev", 2, 9986),
]


def main(argv):
    only = None
    if "--only" in argv:
        only = argv[argv.index("--only") + 1]
    rc_all = 0
    for arm, rnd, port in PLAN:
        if only and only != ("%s%d" % (arm, rnd)) and only != arm:
            continue
        cmd = [PY, SWEEP, "--arm", arm, "--window", "90", "--round", str(rnd),
               "--port-base", str(port)]
        out = os.path.join(HERE, "t140_runall_%s-r%d.out.txt" % (arm, rnd))
        rc, o, e = t140_cmd.run_to_file(cmd, out, cwd=ROOT)
        print("%-9s r%d port=%d rc=%s  log=%s" % (arm, rnd, port, rc, out))
        if rc != 0:
            print("   stderr tail: %s" % e.strip().splitlines()[-1:] if e else "")
            rc_all = 1
    print("SWEEP CHAIN %s" % ("OK" if rc_all == 0 else "HAD FAILURES"))
    return rc_all


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
