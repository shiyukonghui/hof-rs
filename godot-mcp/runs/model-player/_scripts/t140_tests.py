# -*- coding: utf-8 -*-
"""TASK-140: run the two suites and print a compact tail-free summary.

Run through the ledger wrapper:
    t140_cmd.py --cwd F:\\moonbit-hof-rs\\godot-mcp -- <py> runs\\model-player\\_scripts\\t140_tests.py
"""
from __future__ import print_function

import io
import os
import subprocess
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.abspath(os.path.join(HERE, "..", "..", ".."))
PY = r"D:\Anaconda\python.exe"

JOBS = [
    ("model-player unit tests", [PY, os.path.join("tools", "tests",
                                                  "test_playability_model_player.py")]),
    ("playtest_player selftest", [PY, os.path.join("tools", "playtest_player.py"), "selftest"]),
]


def main():
    rc_all = 0
    lines = []
    for name, cmd in JOBS:
        p = subprocess.Popen(cmd, cwd=ROOT, stdout=subprocess.PIPE,
                             stderr=subprocess.STDOUT, shell=False)
        out, _ = p.communicate()
        txt = out.decode("utf-8", "replace")
        tail = [ln for ln in txt.splitlines() if "PASSED" in ln or "FAILED" in ln or
                "MISMATCH" in ln]
        lines.append((name, p.returncode, tail))
        rc_all = rc_all or (0 if p.returncode == 0 else 1)
    for name, rc, tail in lines:
        print("%-28s exit=%s" % (name, rc))
        for t in tail:
            print("   %s" % t)
    print("ALL SUITES %s" % ("PASSED" if rc_all == 0 else "FAILED"))
    with io.open(os.path.join(HERE, "t140_tests.log"), "w", encoding="utf-8") as fh:
        for name, rc, tail in lines:
            fh.write(u"%s exit=%s\n" % (name, rc))
            for t in tail:
                fh.write(u"   %s\n" % t)
    return rc_all


if __name__ == "__main__":
    sys.exit(main())
