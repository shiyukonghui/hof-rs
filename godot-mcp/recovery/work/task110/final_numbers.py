#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""TASK-110: the closing numbers for the report, computed from coverage.json.

Writes a compact block to stdout (no shell redirection anywhere).
"""
import io
import json
import os
import sys

ROOT = r"F:\moonbit-hof-rs\godot-mcp"
with io.open(os.path.join(ROOT, "coverage.json"), "r", encoding="utf-8") as h:
    doc = json.load(h)
tools = doc["tools"]
corpus = doc["corpus"]
reg = doc["unreachable_registry"]
reg_members = {m["tool"] for m in reg["members"] if not m.get("reclassified")}

print("MODE          :", doc["mode"])
print("CORPUS        : runs=%d trace_files=%d calls=%d distinct=%d ok=%d failed=%d"
      % (corpus["run_dirs"], corpus["trace_files"], corpus["calls"], corpus["distinct_tools"],
         corpus["ok"], corpus["failed"]))
print("BUCKETS       : 0=%d 1-4=%d >=5=%d" % (doc["buckets"].get("0", 0),
                                             doc["buckets"].get("1-4", 0), doc["buckets"].get(">=5", 0)))
print("STATUS        :", json.dumps(doc["status_counts"], ensure_ascii=False))
print("SCOPE         :", json.dumps(doc["scope_counts"], ensure_ascii=False))
print("REGISTRY      : members=%d (still unreachable=%d, reclassified=%d)"
      % (reg["members_total"], len(reg_members), len(reg["reclassified"])))

under = [t for t in tools if t["calls"] < 5]
print()
print("UNDER 5       : %d" % len(under))
left_unreachable = [t["tool"] for t in under if t["tool"] in reg_members]
left_reachable = [t["tool"] for t in under if t["tool"] not in reg_members]
print("  of which unreachable(registry)     : %d" % len(left_unreachable))
print("  of which REACHABLE but uncovered   : %d" % len(left_reachable))
for name in sorted(left_reachable):
    row = [t for t in tools if t["tool"] == name][0]
    print("     %-45s %-6s calls=%d" % (name, row["scope"], row["calls"]))
print()
print("REACHABLE COVERAGE: %d/%d contract tools called at least once (>=5: %d)"
      % (len([t for t in tools if t["calls"] > 0]), len(tools),
         len([t for t in tools if t["calls"] >= 5])))
print("TARGETS VIEW  :", "n/a" if not doc.get("targets") else len(doc["targets_view"]))
