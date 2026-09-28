#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Inventory of the TC-PY-* rows in recovery/TEST-CASES.md, grouped by the
file named in the row's SECOND cell, plus the line numbers."""
import io
import os
import re
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.abspath(os.path.join(HERE, "..", "..", ".."))
MD = os.path.join(REPO, "recovery", "TEST-CASES.md")

with io.open(MD, "r", encoding="utf-8") as fh:
    lines = fh.readlines()

groups = {}
order = []
for ln, line in enumerate(lines, 1):
    s = line.rstrip("\n")
    if not s.startswith("| TC-PY-"):
        continue
    cells = s.split("|")
    ident = cells[1].strip()
    src = cells[2].strip().strip("`")
    groups.setdefault(src, []).append((ln, ident))
    order.append(src)

print("TC-PY rows total: %d" % sum(len(v) for v in groups.values()))
for src in sorted(groups):
    print("%-60s %4d   lines %d..%d" % (src, len(groups[src]),
                                        groups[src][0][0], groups[src][-1][0]))

print("")
print("--- rows of test_coverage_batch_consistency.py ---")
for ln, ident in groups.get("tools/tests/test_coverage_batch_consistency.py", []):
    print("%d  %s" % (ln, ident))
