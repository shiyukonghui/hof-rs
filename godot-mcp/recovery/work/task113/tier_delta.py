#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""TASK-113: per-tool evidence-tier / status movement, HEAD's ledger vs the new one.

Reads the committed `godot-mcp/coverage.json` out of git (read-only) and the
working-tree one, then prints every tool whose tier or status changed.

Usage:
    python recovery/work/task113/tier_delta.py
"""
import io
import json
import os
import subprocess
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.abspath(os.path.join(HERE, "..", "..", ".."))
NEW = os.path.join(ROOT, "coverage.json")


def main():
    raw = subprocess.check_output(
        ["git", "-C", ROOT, "show", "HEAD:godot-mcp/coverage.json"])
    old = json.loads(raw.decode("utf-8"))
    with io.open(NEW, "r", encoding="utf-8") as handle:
        new = json.load(handle)
    old_by = {r["tool"]: r for r in old["tools"]}
    new_by = {r["tool"]: r for r in new["tools"]}
    print("tier totals  old=%s" % old["evidence_tier_counts"])
    print("tier totals  new=%s" % new["evidence_tier_counts"])
    print("status       old=%s" % old["status_counts"])
    print("status       new=%s" % new["status_counts"])
    print("bucket       old=%s" % old["buckets"])
    print("bucket       new=%s" % new["buckets"])
    print()
    print("%-42s %-14s %-14s %-12s %-12s %s" % ("tool", "tier old", "tier new",
                                                "status old", "status new", "calls"))
    for name in sorted(new_by):
        o = old_by.get(name)
        n = new_by[name]
        ot = o["evidence_tier"] if o else "(absent)"
        os_ = o["status"] if o else "(absent)"
        if ot == n["evidence_tier"] and os_ == n["status"]:
            continue
        print("%-42s %-14s %-14s %-12s %-12s %d" % (name, ot, n["evidence_tier"],
                                                    os_, n["status"], n["calls"]))
    return 0


if __name__ == "__main__":
    sys.exit(main())
