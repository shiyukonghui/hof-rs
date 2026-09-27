#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""TASK-110 recon: why are the >=5 tools not passing the effect+boundary gate?"""
import io
import json
import os
import sys

path = sys.argv[1] if len(sys.argv) > 1 else r"F:\moonbit-hof-rs\godot-mcp\coverage-final20.json"
with io.open(path, "r", encoding="utf-8") as h:
    doc = json.load(h)
rows = [r for r in doc["tools"] if r["calls"] >= 5]
print("%-40s %6s %5s %5s %-16s %s" % ("tool", "calls", "eff", "bnd", "status", "verdicts"))
for r in sorted(rows, key=lambda x: -x["calls"]):
    v = ",".join("%s=%d" % (k, n) for k, n in sorted(r["verdicts"].items(), key=lambda kv: -kv[1])[:3])
    print("%-40s %6d %5d %5d %-16s %s" % (r["tool"], r["calls"], r["effective"], r["boundary"],
                                          r["status"], v))
print()
print("gate failures:", [r["tool"] for r in rows if not r["gate"]])
