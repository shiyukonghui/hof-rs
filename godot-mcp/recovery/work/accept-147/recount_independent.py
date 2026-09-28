#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""TASK-147 independent recount: count numbered rows straight from TEST-CASES.md body.

A "numbered row" is defined (per TEST-CASES.md 1.1) as a Markdown table line whose
first cell starts with `TC-<family>-`.  We deliberately re-implement this from scratch
instead of reusing recovery/work/task146/recount.py so that the two implementations can
be cross-checked.

Usage:
  python recount_independent.py <path-to-TEST-CASES.md> [--json OUT]
No behaviour depends on the CWD.
"""
import io
import json
import re
import sys

FAMILIES = ["TC-TOOL", "TC-GATE", "TC-M1", "TC-ENG", "TC-PY", "TC-CONS"]


def count(path):
    with io.open(path, "r", encoding="utf-8") as fh:
        text = fh.read()
    lines = text.splitlines()
    counts = {f: 0 for f in FAMILIES}
    unknown = 0
    per_file = {}          # for TC-PY: file part -> row count
    byid = {f: [] for f in FAMILIES}
    row_re = re.compile(r"^\|\s*(TC-[A-Z0-9]+)-(.*?)\s*\|")
    for lineno, raw in enumerate(lines, 1):
        m = row_re.match(raw)
        if not m:
            continue
        full_fam, rest = m.group(1), m.group(2)
        if full_fam not in FAMILIES:
            unknown += 1
            continue
        counts[full_fam] += 1
        byid[full_fam].append((lineno, full_fam + "-" + rest))
        if full_fam == "TC-PY":
            # id form: TC-PY-<file>:<entry>
            fid = rest.split(":", 1)[0]
            per_file[fid] = per_file.get(fid, 0) + 1
    return counts, byid, per_file, unknown, len(lines)


def main():
    path = sys.argv[1]
    out = None
    if "--json" in sys.argv:
        out = sys.argv[sys.argv.index("--json") + 1]
    counts, byid, per_file, unknown, nlines = count(path)
    total = sum(counts.values())
    print("file            : %s" % path)
    print("total lines     : %d" % nlines)
    for f in FAMILIES:
        print("  %-8s      : %d" % (f, counts[f]))
    print("  TOTAL         : %d" % total)
    print("  unmatched TC-* family rows: %d" % unknown)
    print("TC-PY per file:")
    for k in sorted(per_file):
        print("  %-36s %d" % (k, per_file[k]))
    if out:
        with io.open(out, "w", encoding="utf-8") as fh:
            fh.write(json.dumps({
                "counts": counts, "total": total, "unknown_family": unknown,
                "per_file_py": per_file, "nlines": nlines,
                "ids": {k: v for k, v in byid.items()},
            }, ensure_ascii=False, indent=1))


main()
