# -*- coding: utf-8 -*-
"""TASK-140 §1.B: show each build log's tail, its warnings, and the produced dll's identity.

Run through the ledger wrapper.  Keeps "the build really recompiled the file I edited" checkable:
the log carries the compile inputs and the dll's mtime + sha256 are printed.
"""
from __future__ import print_function

import glob
import hashlib
import io
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.abspath(os.path.join(HERE, "..", "..", ".."))
BUILD = os.path.join(ROOT, "runs", "model-player", "t140-build")


def sha(p):
    h = hashlib.sha256()
    with open(p, "rb") as fh:
        for chunk in iter(lambda: fh.read(65536), b""):
            h.update(chunk)
    return h.hexdigest()


def main():
    for g in ("asteroids", "frogger", "bomberman", "flappy"):
        log = os.path.join(BUILD, "%s.txt" % g)
        if not os.path.isfile(log):
            print("%-12s NO LOG" % g)
            continue
        t = io.open(log, encoding="utf-8").read()
        warns = [ln for ln in t.splitlines() if ": warning " in ln]
        errs = [ln for ln in t.splitlines() if ": error " in ln]
        print("===== %s: %d error line(s), %d warning line(s)" % (g, len(errs), len(warns)))
        for w in warns:
            print("   WARN %s" % w.strip())
        print("   tail: %s" % " | ".join(t.strip().splitlines()[-4:]))
        dll = os.path.join(ROOT, "projects", g, ".godot", "mono", "temp", "bin", "Debug",
                           "%s.dll" % g)
        if os.path.isfile(dll):
            print("   dll %s  %d B  sha256=%s"
                  % (os.path.abspath(dll), os.path.getsize(dll), sha(dll)))
        srcs = glob.glob(os.path.join(ROOT, "projects", g, "src", "*.cs"))
        for s in srcs:
            print("   src %s sha256=%s" % (os.path.abspath(s), sha(s)))
    return 0


if __name__ == "__main__":
    sys.exit(main())
