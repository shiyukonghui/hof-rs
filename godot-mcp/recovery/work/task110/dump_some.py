#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""TASK-110 recon: compact schema summary for an arbitrary tool list (setup tools)."""
import io
import json
import os
import sys

SCH = r"F:\moonbit-hof-rs\godot-mcp\recovery\work\task110\schemas"


def summarize(name):
    with io.open(os.path.join(SCH, name + ".json"), "r", encoding="utf-8") as h:
        t = json.load(h)
    sch = t.get("inputSchema") or {}
    props = sch.get("properties") or {}
    print("### %s" % name)
    print("  desc:", (t.get("description") or "").strip().replace("\n", " ")[:220])
    print("  required:", sch.get("required"))
    for k in sorted(props):
        p = props[k]
        bits = []
        if isinstance(p, dict):
            if "type" in p:
                bits.append(str(p["type"]))
            if "enum" in p:
                bits.append("enum=" + ",".join(str(x) for x in p["enum"]))
            if isinstance(p.get("items"), dict):
                bits.append("items:" + json.dumps(p["items"], ensure_ascii=False)[:220])
            if "default" in p:
                bits.append("default=" + json.dumps(p["default"], ensure_ascii=False)[:80])
            d = (p.get("description") or "").strip().replace("\n", " ")
            if d:
                bits.append(d[:150])
        print("    - %s : %s" % (k, "  ".join(bits)))
    print()


for n in sys.argv[1:]:
    summarize(n)
