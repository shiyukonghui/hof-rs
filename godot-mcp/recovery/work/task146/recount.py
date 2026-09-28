#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Recompute the per-family numbered-line counts of recovery/TEST-CASES.md
directly from the matrix row text (the body), and compare with the values
declared in the section 1.1 statistics table.

A "numbered line" is a markdown table row whose FIRST cell is an id of the
form TC-<FAMILY>-<rest>, i.e. the row literally starts with `| TC-`.
Blank/header rows and prose lines are ignored.

Usage:
  python recovery/work/task146/recount.py
Exit code 0 always (report tool); prints a machine readable block.
"""
import io
import os
import re
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.abspath(os.path.join(HERE, "..", "..", ".."))
MD = os.path.join(REPO, "recovery", "TEST-CASES.md")

FAMILY_RE = re.compile(r"^\|\s*(TC-(TOOL|GATE|M1|ENG|PY|CONS))-")

# Families and the exact id-prefix used to recognise them.
PREFIX = {
    "TC-TOOL-": "TOOL",
    "TC-GATE-": "GATE",
    "TC-M1-": "M1",
    "TC-ENG-": "ENG",
    "TC-PY-": "PY",
    "TC-CONS-": "CONS",
}


def read_md():
    with io.open(MD, "r", encoding="utf-8") as fh:
        return fh.readlines()


def count_rows(lines):
    counts = {k: 0 for k in PREFIX}
    ids = []
    for ln, line in enumerate(lines, 1):
        s = line.rstrip("\n")
        m = FAMILY_RE.match(s)
        if not m:
            continue
        name = m.group(1) + "-"
        counts[name] += 1
        first = s.split("|")[1].strip()
        ids.append((ln, first))
    return counts, ids


# --- parse the declared numbers out of the section 1.1 table -------------
DECL_RE = re.compile(r"^\|\s*`(TC-[A-Z0-9]+)-([^`]*)`\s*\|\s*\*{0,2}(\d+)")


def declared(lines):
    """Return {family_prefix: count} for the section 1.1 table, plus total."""
    start = None
    for i, line in enumerate(lines):
        if line.strip().startswith("### 1.1"):
            start = i
            break
    if start is None:
        raise SystemExit("section 1.1 not found")
    decl = {}
    total = None
    for line in lines[start:start + 40]:
        m = DECL_RE.match(line)
        if m:
            decl["%s-" % m.group(1)] = int(m.group(3))
        mm = re.match(r"^\|\s*\*\*合计\*\*\s*\|\s*\*\*(\d+)\*\*", line)
        if mm:
            total = int(mm.group(1))
    return decl, total


def main():
    lines = read_md()
    counts, ids = count_rows(lines)
    decl, total = declared(lines)
    body_total = sum(counts.values())
    ok = True
    print("TEST-CASES.md = %s" % MD)
    print("")
    print("%-12s %8s %8s %s" % ("family", "declared", "body", "status"))
    for pref in sorted(PREFIX):
        d = decl.get(pref)
        b = counts[pref]
        status = "OK" if d == b else "MISMATCH"
        if d != b:
            ok = False
        print("%-12s %8s %8d %s" % (pref, d, b, status))
    print("%-12s %8s %8d %s" % ("TOTAL", total, body_total,
                                "OK" if total == body_total else "MISMATCH"))
    if total != body_total:
        ok = False
    print("")
    print("per-family body counts: %s" % counts)
    print("SELF_CONSISTENT=%s" % ("YES" if ok else "NO"))
    return 0


if __name__ == "__main__":
    sys.exit(main())
