# -*- coding: utf-8 -*-
"""TASK-084: rebuild a file from the read windows of one revision (line-number
placement, newest window wins) and diff it against the tree, so we can tell a
genuinely damaged file from a purely cascading compile error.

usage: python cmp.py <subpath> <rev>
"""
import io
import json
import os
import sys
import difflib

IDX = r"C:\Users\wyl\AppData\Local\Temp\mcp-recovery\staging\__payload-index"
ROOT = r"H:\rebuild\godot"


def norm(p):
    return p.replace("/", "\\").lower()


def build(sub, rev):
    lines = {}
    with io.open(os.path.join(IDX, "events-read.jsonl"), "r", encoding="utf-8", errors="replace") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            r = json.loads(line)
            if sub not in norm(r.get("path", "")):
                continue
            if (r.get("totalLines") or 0) != rev:
                continue
            for no, txt in (r.get("lines") or []):
                lines.setdefault(no, txt)  # first hit = newest window (jsonl read order is time asc; refine below)
    return lines


def build_newest(sub, rev):
    """Newest window wins per line."""
    best = {}
    with io.open(os.path.join(IDX, "events-read.jsonl"), "r", encoding="utf-8", errors="replace") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            r = json.loads(line)
            if sub not in norm(r.get("path", "")):
                continue
            if (r.get("totalLines") or 0) != rev:
                continue
            t = r.get("time", 0)
            for no, txt in (r.get("lines") or []):
                if no not in best or t > best[no][0]:
                    best[no] = (t, txt)
    return {no: v[1] for no, v in best.items()}


def tree_lines(sub):
    p = os.path.join(ROOT, sub)
    with io.open(p, "r", encoding="utf-8", errors="replace") as f:
        return f.read().split("\n")


def main():
    sub = sys.argv[1]
    rev = int(sys.argv[2])
    w = build_newest(sub, rev)
    t = tree_lines(sub)
    print("rev%d covered lines=%d   tree lines=%d (last empty=%s)" % (rev, len(w), len(t), t[-1] == ""))
    if t and t[-1] == "":
        t = t[:-1]
    maxno = max(w) if w else 0
    same = 0
    diff = []
    for no in range(1, min(maxno, len(t)) + 1):
        if no in w:
            if w[no].rstrip("\r") == t[no - 1].rstrip("\r"):
                same += 1
            else:
                diff.append((no, w[no], t[no - 1]))
    print("overlap compared=%d  identical=%d  different=%d" % (min(maxno, len(t)), same, len(diff)))
    for no, a, b in diff[:60]:
        print("  %5d rev: %s" % (no, a[:160]))
        print("        tree: %s" % (b[:160]))
    if len(diff) > 60:
        print("  ... %d more" % (len(diff) - 60))
    missing = [no for no in range(1, maxno + 1) if no not in w]
    if missing:
        runs = []
        s = missing[0]
        prev = missing[0]
        for no in missing[1:]:
            if no == prev + 1:
                prev = no
                continue
            runs.append((s, prev))
            s = prev = no
        runs.append((s, prev))
        print("uncovered runs in rev%d: %s" % (rev, ", ".join("%d-%d" % r for r in runs)))


if __name__ == "__main__":
    main()
