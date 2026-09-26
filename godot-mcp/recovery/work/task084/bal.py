# -*- coding: utf-8 -*-
"""Brace/paren/bracket balance scan for the tree file and for the reconstruction."""
import io
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import rec  # noqa: E402

ROOT = r"H:\rebuild\godot"


def balance(lines):
    """returns (depth_end, first_negative_line)"""
    d = 0
    p = 0
    b = 0
    firstneg = None
    for i, l in enumerate(lines, 1):
        # crude: ignore string/comment content
        s = l
        if "//" in s:
            s = s.split("//", 1)[0]
        for ch in s:
            if ch == "{":
                d += 1
            elif ch == "}":
                d -= 1
                if d < 0 and firstneg is None:
                    firstneg = i
            elif ch == "(":
                p += 1
            elif ch == ")":
                p -= 1
                if p < 0 and firstneg is None:
                    firstneg = i
    return d, p, firstneg


def tree_lines(sub):
    with io.open(os.path.join(ROOT, sub), "r", encoding="utf-8", errors="replace") as f:
        t = f.read().split("\n")
    return t[:-1] if t and t[-1] == "" else t


def main():
    for sub in sys.argv[1:]:
        t = tree_lines(sub)
        try:
            r, info = rec.assemble(sub, verbose=False)
        except Exception as e:  # noqa: BLE001
            print("%-52s  REC FAILED %s" % (os.path.basename(sub), e))
            continue
        td, tp, tn = balance(t)
        rd, rp, rn = balance(r)
        print("%-52s target=%-5d tree=%-5d(depth %d,paren %d) rec=%-5d(depth %d,paren %d)" % (
            os.path.basename(sub), info["rev"], len(t), td, tp, len(r), rd, rp))
        if "--diff" in sys.argv:
            import difflib
            for l in difflib.unified_diff(t, r, "tree", "rec", lineterm="", n=2):
                print("   " + l[:200])


if __name__ == "__main__":
    main()
