#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""TASK-111: the numbers the report quotes, recomputed from coverage.json + the registry."""
import io
import json
import os

ROOT = r"F:\moonbit-hof-rs\godot-mcp"


def load(rel):
    with io.open(os.path.join(ROOT, rel), "r", encoding="utf-8") as handle:
        return json.load(handle)


cov = load("coverage.json")
reg = load("tools/tool_coverage_unreachable.json")
reclass = {e["tool"] for e in reg["reclassified"]}
members = {m["tool"] for m in reg["members"]}
still_unreachable = members - reclass
rows = {r["tool"]: r for r in cov["tools"]}

under5 = [t for t, r in rows.items() if r["calls"] < 5]
reachable_under5 = sorted(t for t in under5 if t not in still_unreachable)
unreachable_under5 = sorted(t for t in under5 if t in still_unreachable)

print("corpus : runs=%d traces=%d calls=%d tools=%d" % (
    cov["corpus"]["run_dirs"], cov["corpus"]["trace_files"], cov["corpus"]["calls"],
    cov["corpus"]["distinct_tools"]))
buckets = {"0": 0, "1-4": 0, ">=5": 0}
status = {}
for r in rows.values():
    n = r["calls"]
    buckets["0" if n == 0 else ("1-4" if n < 5 else ">=5")] += 1
    status[r["status"]] = status.get(r["status"], 0) + 1
print("buckets: %s" % buckets)
print("status : %s" % status)
print("registry: members=%d reclassified=%d stillUnreachable=%d" % (
    len(members), len(reclass), len(still_unreachable)))
print("reachable but <5 : %d -> %s" % (len(reachable_under5), ", ".join(reachable_under5)))
print("unreachable <5   : %d" % len(unreachable_under5))
one_to_four = sorted(t for t, r in rows.items() if 0 < r["calls"] < 5)
print("1-4 calls: %d -> %s" % (len(one_to_four), ", ".join(one_to_four) or "-"))
