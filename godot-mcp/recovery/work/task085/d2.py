# -*- coding: utf-8 -*-
"""Show the diff between the tree file and a reconstruction buffer.

usage: python d2.py <tree-subpath> <reconstruction-path> [a b]
"""
import io
import os
import sys
import difflib

ROOT = r"H:\rebuild\godot"


def main():
    sub = sys.argv[1]
    recp = sys.argv[2]
    t = io.open(os.path.join(ROOT, sub), encoding="utf-8", errors="replace").read().split("\n")
    if t and t[-1] == "":
        t = t[:-1]
    r = io.open(recp, encoding="utf-8", errors="replace").read().split("\n")
    if r and r[-1] == "":
        r = r[:-1]
    print("TREE %d lines  REC %d lines" % (len(t), len(r)))
    a = b = None
    if len(sys.argv) > 4:
        a, b = int(sys.argv[3]), int(sys.argv[4])
        r = r[a - 1:b]
        t = t[a - 1:b] if len(t) >= b else t
    n = 0
    for l in difflib.unified_diff(t, r, "TREE", "REC", lineterm="", n=2):
        print(l[:200])
        n += 1
        if n > 600:
            print("... (truncated)")
            break


if __name__ == "__main__":
    main()
