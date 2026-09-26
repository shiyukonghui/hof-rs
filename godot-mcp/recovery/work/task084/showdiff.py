# -*- coding: utf-8 -*-
"""Show the diff between the tree file and the reconstruction for a file,
optionally restricted to a line range of the target revision.

usage: python showdiff.py <subpath> [a b]
"""
import io
import os
import sys
import difflib

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import rec  # noqa: E402

ROOT = r"H:\rebuild\godot"


def main():
    sub = sys.argv[1]
    t = io.open(os.path.join(ROOT, sub), encoding="utf-8", errors="replace").read().split("\n")
    if t and t[-1] == "":
        t = t[:-1]
    r, info = rec.assemble(sub, verbose=True)
    if len(sys.argv) > 3:
        a, b = int(sys.argv[2]), int(sys.argv[3])
        r = r[a - 1:b]
        t = t[a - 1:b]
    n = 0
    for l in difflib.unified_diff(t, r, "TREE", "REC", lineterm="", n=2):
        print(l[:220])
        n += 1
        if n > 400:
            print("... (truncated)")
            break


if __name__ == "__main__":
    main()
