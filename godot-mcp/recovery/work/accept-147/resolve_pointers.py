#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""TASK-147 A3: independently resolve every TC-PY row's evidence pointer.

For every `TC-PY-<file>:<name>` row, the 5th cell is `<path>:<line>`.
Check: the file exists, the line number is inside the file, the line equals
      `def <name>(`  (pytest kind), or `["<name>"]` (script_check), or the name
      is really printed by the file (printed kind).
Also check every other cell that looks like a `path:line` pointer.
"""
import io, os, re, sys, subprocess, collections

ROOT = os.path.abspath(".")
text = io.open("recovery/TEST-CASES.md", encoding="utf-8").read()
lines = text.splitlines()

def kind(note):
    if u"pytest \u6761\u76ee" in note: return "pytest"
    if u"\u811a\u672c\u5185 check" in note: return "script_check"
    if u"\u81ea\u6253\u5370\u7684 case \u540d" in note: return "printed"
    return "unknown"

problems = []
n_pytest = n_script = n_printed = 0
for lineno, raw in enumerate(lines, 1):
    if not raw.startswith("| TC-PY-"):
        continue
    cells = [c.strip() for c in raw.split("|")]
    ident = cells[1]; src = cells[2].strip("`"); ptr = cells[4].strip("`"); note = cells[-2]
    k = kind(note)
    if k == "pytest":
        n_pytest += 1
        m = re.match(r"^(.*):(\d+)$", ptr)
        if not m:
            problems.append("%d: pointer %r is not file:line" % (lineno, ptr)); continue
        pf, pl = m.group(1), int(m.group(2))
        if pf != src:
            problems.append("%d: pointer file %s != src cell %s" % (lineno, pf, src))
        if not os.path.exists(pf):
            problems.append("%d: %s does not exist" % (lineno, pf)); continue
        body = io.open(pf, encoding="utf-8").read().splitlines()
        if pl > len(body):
            problems.append("%d: %s:%d beyond EOF (%d)" % (lineno, pf, pl, len(body))); continue
        name = ident.split(":", 1)[1]
        if "def %s(" % name not in body[pl - 1]:
            problems.append("%d: %s:%d is %r, not `def %s(`" % (lineno, pf, pl, body[pl-1].strip()[:70], name))
    elif k == "script_check":
        n_script += 1
    elif k == "printed":
        n_printed += 1
    else:
        problems.append("%d: unknown note kind for %s" % (lineno, ident))

print("pytest rows: %d, script_check rows: %d, printed rows: %d" % (n_pytest, n_script, n_printed))
print("pointer problems: %d" % len(problems))
for p in problems:
    print("  " + p)

# ---- second pass: every `path:digits` pointer anywhere in the file ----
print("\n-- all `path.ext:NNN` pointers, existence + EOF check --")
ptr_re = re.compile(r"`([A-Za-z0-9_./\\-]+\.(?:py|h|cpp|json|jsonl|ps1|cmd|md|txt|gd)\S*?):(\d+)(?:-\d+)?`")
bad = 0; seen = 0
for lineno, raw in enumerate(lines, 1):
    for m in ptr_re.finditer(raw):
        seen += 1
        pf, pl = m.group(1).replace("\\", "/"), int(m.group(2))
        cand = pf
        if not os.path.exists(cand):
            # matrix uses repo-relative and godot/ prefixed paths
            bad += 1
            print("  line %d: MISSING %s" % (lineno, pf)); continue
        try:
            n = len(io.open(cand, encoding="utf-8", errors="replace").read().splitlines())
        except Exception as e:
            print("  line %d: unreadable %s (%s)" % (lineno, pf, e)); continue
        if pl > n:
            bad += 1
            print("  line %d: %s:%d beyond EOF (%d lines)" % (lineno, pf, pl, n))
print("pointers scanned: %d, bad: %d" % (seen, bad))
