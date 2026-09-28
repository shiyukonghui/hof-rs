#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""TASK-149: find `path:line` pointers in the audited documents that have gone STALE.

For a pointer `tools/foo.py:NNN` the line is judged stale when the token that appears on
that line today obviously belongs to a different construct -- the tractable, non-guessing
test is: the document names a SYMBOL next to the pointer (``summarise()``,
``playtest_player.py:722-801``), and that symbol is defined at a very different line now.

Rather than infer intent, this script prints the CONTEXT (the symbols defined within +/- 60
lines of the pointer) so a human can see whether the pointer still lands where the document
says it does. A pointer whose neighbourhood contains the named symbol is fine.

Read-only; stdout only.
"""
from __future__ import print_function

import io
import os
import re
import sys

ROOT = r"F:\moonbit-hof-rs\godot-mcp"

# Documents and the code files whose pointers are worth re-resolving.
DOCS = [
    ("recovery/reports/ACCEPTANCE-TASK-137.md", ["tools/playtest_player.py"]),
    ("recovery/reports/ACCEPTANCE-TASK-141.md", ["tools/playtest_player.py"]),
    ("recovery/reports/ACCEPTANCE-TASK-147.md", ["tools/tests/test_matrix_self_consistency.py",
                                                 "recovery/TEST-CASES.md"]),
    ("recovery/reports/TASK-142-REPORT.md", ["tools/playtest_player.py"]),
    ("recovery/TEST-CASES.md", ["tools/playtest_player.py"]),
    ("recovery/tasks/TEMPLATE-logic-feedback.md", ["tools/playtest_player.py"]),
]

SYM_RE = re.compile(r"^\s*(?:def|class)\s+([A-Za-z_][A-Za-z0-9_]*)")
PTR_RE = re.compile(r"([A-Za-z0-9_./\\-]+\.(?:py|ps1|h|cpp))[:：](\d+)")
NAME_RE = re.compile(r"`([A-Za-z_][A-Za-z0-9_]*)\(\)`")


def lines_of(rel):
    with io.open(os.path.join(ROOT, rel.replace("/", os.sep)),
                 "r", encoding="utf-8", errors="replace") as handle:
        return handle.readlines()


def symbols(lines, lo, hi, limit=8):
    out = []
    for i in range(max(1, lo), min(len(lines), hi) + 1):
        m = SYM_RE.match(lines[i - 1])
        if m:
            out.append("%d:%s" % (i, m.group(1)))
        if len(out) >= limit:
            break
    return out


def main():
    target = sys.argv[1] if len(sys.argv) > 1 else None
    for doc, codefiles in DOCS:
        if target and target not in doc:
            continue
        print("=" * 78)
        print("DOC %s" % doc)
        with io.open(os.path.join(ROOT, doc.replace("/", os.sep)),
                     "r", encoding="utf-8", errors="replace") as handle:
            dlines = handle.readlines()
        cache = {}
        for idx, line in enumerate(dlines, 1):
            for raw, num in PTR_RE.findall(line):
                rel = raw.replace("\\", "/")
                base = os.path.basename(rel)
                match = [c for c in codefiles if os.path.basename(c) == base]
                if not match:
                    continue
                code = match[0]
                if code not in cache:
                    cache[code] = lines_of(code)
                code_lines = cache[code]
                n = int(num)
                near = symbols(code_lines, n - 60, n + 60)
                names = NAME_RE.findall(line)
                here = code_lines[n - 1].strip()[:70] if n <= len(code_lines) else "<past EOF>"
                interesting = ""
                if names:
                    for nm in names:
                        hit = [s for s in near if s.endswith(":" + nm) or s.endswith(":" + nm)]
                        all_defs = [i for i, l in enumerate(code_lines, 1)
                                    if re.match(r"\s*(?:def|class)\s+%s\b" % re.escape(nm), l)]
                        if all_defs and abs(all_defs[0] - n) > 30:
                            interesting = ("  ** STALE? doc names %s() defined at %d **"
                                           % (nm, all_defs[0]))
                        elif all_defs:
                            interesting = "  (%s() at %d)" % (nm, all_defs[0])
                print("  L%-5d %-46s :%-5d %s%s"
                      % (idx, code.replace("tools/", ""), n, here, interesting))
                print("        nearby defs: %s" % (", ".join(near) or "<none>"))


if __name__ == "__main__":
    main()
