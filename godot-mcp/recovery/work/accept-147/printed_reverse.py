#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""TASK-147 A3b: reverse-direction check -- does any printed case lack a matrix row?"""
import io, re, subprocess, sys, os, html

text = io.open("recovery/TEST-CASES.md", encoding="utf-8").read()
lines = text.splitlines()


def rows_for(src, kindmarker):
    out = []
    for raw in lines:
        if not raw.startswith("| TC-PY-" + src):
            continue
        cells = [c.strip() for c in raw.split("|")]
        if kindmarker in cells[-2]:
            out.append(cells[3].strip("`"))
    return out


for src, base in [("test_playability_p7.py", "test_playability_p7.py"),
                  ("test_playability_model_player.py", "test_playability_model_player.py")]:
    proc = subprocess.run([sys.executable, "tools/tests/" + base],
                          stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
    out = proc.stdout.decode("utf-8", "replace").splitlines()
    names = []
    for line in out:
        line = line.rstrip("\r")
        if base == "test_playability_p7.py":
            if line.startswith("ok  ") or line.startswith("FAIL"):
                names.append(line[6:].rstrip())
        else:
            tail = line[59:] if len(line) > 59 else ""
            if len(line) >= 58 and (tail.startswith("OK") or tail.startswith("MISMATCH")):
                names.append(line[:58].rstrip())
    matrix = [html.unescape(n) for n in rows_for(src, u"\u81ea\u6253\u5370")]
    real = names
    print("%s: exit=%d real printed=%d matrix rows=%d" % (base, proc.returncode, len(real), len(matrix)))
    print("   printed but NOT in matrix:", [n for n in real if n not in matrix])
    print("   in matrix but NOT printed:", [n for n in matrix if n not in real])
    print("   duplicate rows in matrix  :",
          [k for k, v in __import__("collections").Counter(matrix).items() if v > 1])
