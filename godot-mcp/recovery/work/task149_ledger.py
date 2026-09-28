#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""TASK-149: recompute the TASK-140 command-ledger erratum (194-vs-186) from the ledger.

TASK-142 §K.1 declared the authoritative count to be 194, with the cut defined as
"the first ledger entry whose `source` is `t140-wrapper-call` (index 501) through the last
`t140_scan_redirects.py` entry (index 694)". This script re-derives that from the ledger the
report names, so ERRATA.md can publish a number a machine can reproduce.

The ledger is `runs/model-player/_scripts/t136_commands.jsonl`. If it is absent (runs/** is
ignored by git and machine-local), the script says so instead of guessing.

Read-only; stdout only.
"""
from __future__ import print_function

import io
import json
import os
import sys

ROOT = r"F:\moonbit-hof-rs\godot-mcp"
LEDGER = os.path.join(ROOT, "runs", "model-player", "_scripts", "t136_commands.jsonl")
SCAN = os.path.join(ROOT, "runs", "model-player", "_scripts",
                    "t142_redirect_scan.json")


def main():
    print("=" * 78)
    print("ledger: %s" % LEDGER)
    if not os.path.exists(LEDGER):
        print("  MISSING on this machine (runs/** is gitignored) -- cannot recompute")
    else:
        entries = []
        with io.open(LEDGER, "r", encoding="utf-8") as handle:
            for lineno, line in enumerate(handle, 1):
                line = line.strip()
                if not line:
                    continue
                try:
                    entries.append(json.loads(line))
                except ValueError:
                    entries.append({"_unparsed": lineno})
        print("  entries: %d" % len(entries))
        first = None
        last_scan = None
        for idx, entry in enumerate(entries, 1):
            argv = " ".join(entry.get("argv") or [])
            if first is None and entry.get("source") == "t140-wrapper-call":
                first = idx
            if "t142_scan_redirects.py" in argv or "t140_scan_redirects.py" in argv:
                last_scan = idx
        print("  first `source == t140-wrapper-call`: %s" % first)
        print("  last  *_scan_redirects.py entry    : %s" % last_scan)
        if first and last_scan:
            print("  count = last - first + 1           = %d" % (last_scan - first + 1))
        after = None
        if first:
            after = sum(1 for e in entries[last_scan:] if e)
            print("  entries after the last scan        = %d" % (len(entries) - last_scan))
        print("  TASK-142 §K.1 claims               : first=501 last=694 count=194 now=209 after=15")

    print("=" * 78)
    print("erratum anchor: %s" % SCAN)
    if not os.path.exists(SCAN):
        print("  MISSING on this machine (runs/** is gitignored) -- cannot recompute")
    else:
        with io.open(SCAN, "r", encoding="utf-8") as handle:
            doc = json.load(handle)
        anchor = doc.get("task140_ledger_erratum")
        print("  task140_ledger_erratum = %s"
              % json.dumps(anchor, ensure_ascii=False)[:600] if anchor else
              "  no `task140_ledger_erratum` key")


if __name__ == "__main__":
    main()
