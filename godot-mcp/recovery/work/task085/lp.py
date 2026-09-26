# -*- coding: utf-8 -*-
"""Line-presence comparison between the tree file and a reconstruction buffer.

Reports how many tree lines are absent from the reconstruction (and vice versa),
grouped into contiguous "absent" runs, so a real loss can be told apart from a
difflib block move.

usage: python lp.py <tree-subpath> <recon-path> [tree|rec]
"""
import collections
import io
import os
import sys

ROOT = r"H:\rebuild\godot"


def runs(nos):
    out = []
    if not nos:
        return out
    s = p = nos[0]
    for n in nos[1:]:
        if n == p + 1:
            p = n
            continue
        out.append((s, p))
        s = p = n
    out.append((s, p))
    return out


def main():
    sub, recp = sys.argv[1], sys.argv[2]
    t = io.open(os.path.join(ROOT, sub), encoding="utf-8", errors="replace").read().split("\n")
    r = io.open(recp, encoding="utf-8", errors="replace").read().split("\n")
    if t and t[-1] == "":
        t.pop()
    if r and r[-1] == "":
        r.pop()
    tset = collections.Counter(x.rstrip() for x in t)
    rset = collections.Counter(x.rstrip() for x in r)
    print("TREE %d lines   REC %d lines" % (len(t), len(r)))

    missing_t = [i + 1 for i, x in enumerate(t) if tset[x.rstrip()] > rset[x.rstrip()]]
    missing_r = [i + 1 for i, x in enumerate(r) if rset[x.rstrip()] > tset[x.rstrip()]]
    print("tree lines with no counterpart in REC: %d" % len(missing_t))
    print("rec  lines with no counterpart in TREE: %d" % len(missing_r))
    want = sys.argv[3] if len(sys.argv) > 3 else "tree"
    src, nos = (t, missing_t) if want == "tree" else (r, missing_r)
    for a, b in runs(nos):
        n = b - a + 1
        empty = all(not src[i - 1].strip() for i in range(a, b + 1))
        print("  %s %4d-%-4d (%d lines%s)" % (want, a, b, n, ", blank-run" if empty else ""))
        if not empty and n <= 60:
            for i in range(a, b + 1):
                print("       %5d| %s" % (i, src[i - 1][:150]))


if __name__ == "__main__":
    main()
