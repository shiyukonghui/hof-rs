#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""TC-PY row audit: rows per source file, duplicate ids, section 1.1 declared count."""
import collections
import io
import json
import os
import re

MATRIX = r"F:\moonbit-hof-rs\godot-mcp\recovery\TEST-CASES.md"
OUT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "tcpy_rows.json")
with io.open(MATRIX, "r", encoding="utf-8") as h:
    lines = h.read().split("\n")

rows = []
for i, l in enumerate(lines, 1):
    if l.startswith("| TC-PY-"):
        cid = l.split("|")[1].strip()
        src = l.split("|")[2].strip().strip("`")
        rows.append((i, cid, src))

by_file = collections.Counter(r[2] for r in rows)
dups = {k: v for k, v in collections.Counter(r[1] for r in rows).items() if v > 1}

# lines that start a row but have no closing pipe count / weird
malformed = [i for i, l in enumerate(lines, 1)
             if l.startswith("| TC-PY-") and l.count("|") < 8]

# pytest tests actually defined in tools/tests
tests_dir = r"F:\moonbit-hof-rs\godot-mcp\tools\tests"
pytest_defs = {}
for fn in sorted(os.listdir(tests_dir)):
    if not fn.endswith(".py"):
        continue
    with io.open(os.path.join(tests_dir, fn), "r", encoding="utf-8", errors="replace") as h:
        txt = h.read()
    defs = re.findall(r"^def (test_[A-Za-z0-9_]+)\s*\(", txt, re.M)
    pytest_defs[fn] = defs

out = {"total_rows": len(rows), "distinct_ids": len(set(r[1] for r in rows)),
       "by_file": dict(by_file), "duplicate_ids": dups, "malformed_row_lines": malformed,
       "pytest_defs_by_file": {k: len(v) for k, v in pytest_defs.items()},
       "pytest_defs": pytest_defs}
with io.open(OUT, "w", encoding="utf-8", newline="\n") as h:
    h.write(json.dumps(out, ensure_ascii=False, indent=2))
print(json.dumps(out, ensure_ascii=False, indent=2)[:6000])
