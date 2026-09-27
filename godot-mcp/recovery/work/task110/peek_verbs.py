#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""TASK-110 recon: the contract's verb taxonomy and how it lands on real tools."""
import io
import json
import os
from collections import Counter

D = r"F:\moonbit-hof-rs\godot-mcp\godot\modules\mcp_server\docs"
with io.open(os.path.join(D, "tool-rename-map.json"), "r", encoding="utf-8") as h:
    ren = json.load(h)
print("verb_closed_set:", ren["convention"].get("verb_closed_set"))
print("mutating_semantics:", json.dumps(ren["convention"].get("mutating_semantics"), ensure_ascii=False)[:300])
verbs = Counter(t.get("verb") for t in ren["tools"])
print("verb histogram:", dict(sorted(verbs.items(), key=lambda kv: -kv[1])))
print()
# added tools have no verb in the map
with io.open(os.path.join(D, "tools_list.renamed.json"), "r", encoding="utf-8") as h:
    contract = json.load(h)
names = [t["name"] for t in contract["result"]["tools"]]
mapped = {t["new_name"]: t for t in ren["tools"]}
print("contract tools missing from rename map:")
for n in names:
    if n not in mapped:
        print("   ", n, "(meta.added_tools)" if n in (contract.get("_meta") or {}).get("added_tools", []) else "")
print()
print("verb by contract tool for the 29 already-called tools:")
import collections
DOCS = r"F:\moonbit-hof-rs\godot-mcp\dist\review_data.json"
for n in sorted(names):
    pass
# verbs that are neither clearly-read nor clearly-write:
for v in sorted(verbs):
    if v not in ("get", "read", "search", "list", "find", "analyze", "detect", "convert", "validate", "check",
                 "create", "edit", "set", "add", "remove", "delete", "write", "build", "save", "open"):
        print("  unclassified verb %-12s tools: %s" % (v, [t["new_name"] for t in ren["tools"] if t.get("verb") == v][:8]))
