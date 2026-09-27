#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""TASK-111: the still-unreachable tail, grouped by the register's category."""
import io
import json
import os

ROOT = r"F:\moonbit-hof-rs\godot-mcp"


def load(rel):
    with io.open(os.path.join(ROOT, rel), "r", encoding="utf-8") as handle:
        return json.load(handle)


reg = load("tools/tool_coverage_unreachable.json")
cov = {r["tool"]: r for r in load("coverage.json")["tools"]}
rec = {e["tool"] for e in reg["reclassified"]}
cat = {}
labels = {c["code"]: c["label"] for c in reg["categories"].values()}
for member in reg["members"]:
    if member["tool"] in rec:
        continue
    cat.setdefault(member["category"], []).append(member["tool"])

for code in sorted(cat):
    print("%s %s -- %d" % (code, labels.get(code, ""), len(cat[code])))
    for tool in cat[code]:
        print("    %-44s calls=%d" % (tool, cov[tool]["calls"]))
print("total %d" % sum(len(v) for v in cat.values()))
