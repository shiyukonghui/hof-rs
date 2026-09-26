# -*- coding: utf-8 -*-
"""TASK-084: run the recorded-text reconstruction over every module source and
report which files the tree already matches and which ones it does not.

usage: python scan84.py [--all | file1 file2 ...]
"""
import difflib
import io
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import rec  # noqa: E402

ROOT = r"H:\rebuild\godot"
MOD = "modules\\mcp_server"


def tree_lines(sub):
    p = os.path.join(ROOT, sub)
    with io.open(p, "r", encoding="utf-8", errors="replace") as f:
        t = f.read().split("\n")
    if t and t[-1] == "":
        t = t[:-1]
    return t


def all_sources():
    out = []
    base = os.path.join(ROOT, MOD)
    for dp, _dn, fn in os.walk(base):
        if "\\docs\\" in dp or "\\tests\\" in dp:
            continue
        for f in fn:
            if f.endswith((".cpp", ".h")):
                full = os.path.join(dp, f)
                out.append(os.path.relpath(full, ROOT))
    return sorted(out)


def main():
    if "--all" in sys.argv or len(sys.argv) == 1:
        files = all_sources()
    else:
        files = sys.argv[1:]
    print("%-58s %6s %6s %5s %5s %s" % ("file", "rev", "tree", "gaps", "hunks", "status"))
    bad = []
    for sub in files:
        try:
            res, info = rec.assemble(sub, verbose=False)
        except Exception as e:  # noqa: BLE001
            print("%-58s  EXC %s" % (sub.replace(MOD + "\\", ""), e))
            continue
        t = tree_lines(sub)
        sm = difflib.SequenceMatcher(None, t, res, autojunk=False)
        hunks = [h for h in sm.get_opcodes() if h[0] != "equal"]
        ndiff = sum(max(h[2] - h[1], h[4] - h[3]) for h in hunks)
        st = info["stats"]
        status = "OK" if not hunks else "DIFF"
        print("%-58s %6d %6d %5d %5d %s  applied=%d skipped=%d" % (
            sub.replace(MOD + "\\", ""), info["rev"], len(t), len(info["gaps"]), len(hunks), status,
            st["applied"], len(st["skipped"])))
        if hunks:
            bad.append((sub, t, res, hunks, ndiff, st))
    print("\n%d file(s) differ; %d hunk lines total" % (len(bad), sum(b[4] for b in bad)))
    for sub, t, res, hunks, ndiff, st in bad:
        print("\n### %s  (%d differing lines)" % (sub, ndiff))
        for h in hunks:
            tag = h[0]
            print("   %s tree[%d:%d] -> rec[%d:%d]" % (tag, h[1] + 1, h[2], h[3] + 1, h[4]))


if __name__ == "__main__":
    main()
