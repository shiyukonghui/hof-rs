#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""TASK-149: re-resolve a sample of the `path:line` pointers the matrix publishes.

TASK-147 already validated all 890 pointers; this re-checks a sample after TASK-149's own
edits, so a doc fix cannot silently invalidate a pointer. Read-only, stdout only.
"""
from __future__ import print_function

import io
import os
import re
import sys

ROOT = r"F:\moonbit-hof-rs\godot-mcp"


def main():
    limit = int(sys.argv[1]) if len(sys.argv) > 1 else 400
    with io.open(os.path.join(ROOT, "recovery", "TEST-CASES.md"),
                 "r", encoding="utf-8") as handle:
        text = handle.read()
    # `path.ext:NNN` pointers
    ptr_re = re.compile(r"`([A-Za-z0-9_./\\-]+\.(?:py|ps1|h|cpp|json|jsonl|md|txt|cmd)):(\d+)")
    seen = []
    for match in ptr_re.finditer(text):
        seen.append((match.group(1), int(match.group(2))))
    # de-duplicate, keep order
    uniq = []
    for item in seen:
        if item not in uniq:
            uniq.append(item)
    print("distinct path:line pointers: %d (of %d occurrences)" % (len(uniq), len(seen)))
    bad_eof = []
    missing = []
    checked = 0
    for rel, line in uniq[:limit]:
        cand = rel.replace("\\", "/")
        full = None
        for base in (ROOT, os.path.join(ROOT, "godot"),
                     os.path.join(ROOT, "godot", "modules", "mcp_server")):
            probe = os.path.join(base, cand.replace("/", os.sep))
            if os.path.exists(probe):
                full = probe
                break
        if full is None:
            missing.append((rel, line))
            continue
        with io.open(full, "r", encoding="utf-8", errors="replace") as handle:
            n = sum(1 for _ in handle)
        checked += 1
        if line > n:
            bad_eof.append((rel, line, n))
    print("checked: %d" % checked)
    print("missing files: %d" % len(missing))
    for rel, line in missing[:20]:
        print("    MISSING %s:%d" % (rel, line))
    print("line beyond EOF: %d" % len(bad_eof))
    for rel, line, n in bad_eof[:20]:
        print("    BEYOND  %s:%d (file has %d lines)" % (rel, line, n))


if __name__ == "__main__":
    main()
