#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""TASK-110 recon: dump the contract's per-tool inputSchema to single files.

Read-only against the contract; writes only under recovery/work/task110/schemas/.
No shell redirection is used anywhere - this script owns its own file writes.
"""
import io
import json
import os
import sys

ROOT = r"F:\moonbit-hof-rs\godot-mcp"
CONTRACT = os.path.join(ROOT, "godot", "modules", "mcp_server", "docs", "tools_list.renamed.json")
OUT = os.path.join(ROOT, "recovery", "work", "task110", "schemas")

with io.open(CONTRACT, "r", encoding="utf-8") as h:
    doc = json.load(h)
tools = doc["result"]["tools"]
if not os.path.isdir(OUT):
    os.makedirs(OUT)

index = {}
for t in tools:
    name = t["name"]
    index[name] = {
        "keys": sorted(t.keys()),
        "description": (t.get("description") or "")[:400],
        "inputSchema": t.get("inputSchema"),
    }
    with io.open(os.path.join(OUT, name + ".json"), "w", encoding="utf-8", newline="\n") as h:
        h.write(json.dumps(t, ensure_ascii=False, indent=2, sort_keys=True) + "\n")

with io.open(os.path.join(OUT, "_index.json"), "w", encoding="utf-8", newline="\n") as h:
    h.write(json.dumps(index, ensure_ascii=False, indent=2, sort_keys=True) + "\n")
print("tools=%d written to %s" % (len(tools), OUT))
