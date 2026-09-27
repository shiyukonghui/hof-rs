#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""TASK-113 helper: print the contract inputSchema of named tools (read-only)."""
import io
import json
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.abspath(os.path.join(HERE, "..", "..", ".."))
CONTRACT = os.path.join(ROOT, "godot", "modules", "mcp_server", "docs",
                        "tools_list.renamed.json")

def main():
    with io.open(CONTRACT, "r", encoding="utf-8") as h:
        doc = json.load(h)
    tools = {t["name"]: t for t in doc["result"]["tools"]}
    if len(sys.argv) < 2:
        print("usage: show_schema.py TOOL [TOOL...]")
        return 2
    for name in sys.argv[1:]:
        t = tools.get(name)
        if not t:
            print("== %s: NOT IN CONTRACT" % name)
            continue
        print("== %s" % name)
        print("   description:", (t.get("description") or "")[:600])
        print("   inputSchema:", json.dumps(t.get("inputSchema"), ensure_ascii=False))
    return 0

if __name__ == "__main__":
    sys.exit(main())
