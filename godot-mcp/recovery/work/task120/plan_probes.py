#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""TASK-120 item C plan: which endpoint each of the 17 boundary-less tools lives on.

For every tool that has channel evidence but no boundary call, print
  * the trace kinds (`editor` / `game`) its calls actually appear on in the corpus;
  * the number of declared `inputSchema.properties` (the TASK-032 registry gate that
    `-32602 Unknown parameter` comes from only fires for tools that have a
    `properties` object - `tool_registry.cpp:812-855`).

Run:  python recovery/work/task120/plan_probes.py
"""
import io
import json
import os
import sys

ROOT = os.path.abspath(os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", ".."))
sys.path.insert(0, os.path.join(ROOT, "tools"))
import tool_coverage as tc  # noqa: E402


def main():
    cov = json.load(io.open(os.path.join(ROOT, "coverage.json"), encoding="utf-8"))
    contract = json.load(io.open(os.path.join(ROOT, tc.CONTRACT), encoding="utf-8"))["result"]["tools"]
    schema = {t["name"]: (t.get("inputSchema") or {}) for t in contract}
    seventeen = [r["tool"] for r in cov["tools"]
                 if r["calls"] >= 5 and r["channel_evidence"] >= 1 and r["boundary"] == 0]

    kinds = {}
    base = os.path.join(ROOT, "runs")
    for dirpath, _d, filenames in os.walk(base):
        for fname in filenames:
            if not (fname.startswith("trace-") and fname.endswith(".jsonl")):
                continue
            kind = fname[len("trace-"):-len(".jsonl")]
            with io.open(os.path.join(dirpath, fname), "r", encoding="utf-8", errors="replace") as h:
                for line in h:
                    if '"tools/call"' not in line:
                        continue
                    try:
                        rec = json.loads(line)
                    except ValueError:
                        continue
                    tool = rec.get("tool")
                    if tool in seventeen:
                        kinds.setdefault(tool, set()).add(kind)
    print("%-42s %-14s %-18s %s" % ("tool", "trace kinds", "n_properties", "props"))
    for tool in seventeen:
        props = (schema.get(tool) or {}).get("properties")
        n = len(props) if isinstance(props, dict) else -1
        print("%-42s %-14s %-18s %s" % (tool, ",".join(sorted(kinds.get(tool, []))) or "NONE",
                                        n, ",".join(sorted(props)) if isinstance(props, dict) else "-"))


if __name__ == "__main__":
    main()
