# -*- coding: utf-8 -*-
"""Print a line range of the tree file and of one or more revisions, tabs visible.

usage: python rgn.py <subpath> <a> <b> [rev ...]
"""
import io
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from cmp import build_newest  # noqa: E402

ROOT = r"H:\rebuild\godot"


def show(tag, lines):
    print("--- %s" % tag)
    for no, txt in lines:
        print("  %5d| %s" % (no, txt.replace("\t", "\u2502...")[:200]))


def main():
    sub = sys.argv[1]
    a, b = int(sys.argv[2]), int(sys.argv[3])
    revs = [int(x) for x in sys.argv[4:]]
    p = os.path.join(ROOT, sub)
    with io.open(p, "r", encoding="utf-8", errors="replace") as f:
        t = f.read().split("\n")
    show("TREE %s %d..%d" % (os.path.basename(sub), a, b),
         [(no, t[no - 1]) for no in range(a, min(b, len(t)) + 1)])
    for rev in revs:
        w = build_newest(sub, rev)
        show("rev%d %d..%d" % (rev, a, b), [(no, w[no]) for no in range(a, b + 1) if no in w])


if __name__ == "__main__":
    main()
