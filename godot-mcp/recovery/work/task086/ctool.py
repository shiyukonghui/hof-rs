# -*- coding: utf-8 -*-
"""Print the contract entries of some tools (name/description/schema keys)."""
import io
import json
import os
import sys

MOD = r"H:\rebuild\godot\modules\mcp_server"
c = json.load(io.open(os.path.join(MOD, "docs", "tools_list.renamed.json"), encoding="utf-8"))
by = {t["name"]: t for t in c["result"]["tools"]}
for name in sys.argv[1:]:
    t = by.get(name)
    if t is None:
        print("== %s : NOT IN CONTRACT" % name)
        continue
    print("== %s" % name)
    print("   description: %s" % t["description"])
    print("   schema keys: %s" % sorted(t["inputSchema"].get("properties", {}).keys()))
print()
print("contract _meta keys: %s" % sorted(c["_meta"].keys()))
ov = c["_meta"].get("overrides")
print("overrides records   : %d" % (len(ov) if ov else 0))
if ov:
    for r in ov:
        print("   %-14s %s" % (r.get("kind"), r.get("old_name")))
