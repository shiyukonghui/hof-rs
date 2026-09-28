#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import io, json, os
HERE = os.path.dirname(os.path.abspath(__file__))
d = json.load(io.open(os.path.join(HERE, "structural_audit.json"), "r", encoding="utf-8"))
print("TC-GATE mismatches:", json.dumps(d["TC-GATE"]["mismatch"], ensure_ascii=False, indent=2))
ROOT = r"F:\moonbit-hof-rs\godot-mcp"
res = []
for m in d["TC-PY"]["missing_symbol"]:
    path = os.path.join(ROOT, m["src"])
    text = io.open(path, "r", encoding="utf-8", errors="replace").read()
    name = m.get("name", "")
    pref = name[:35]
    res.append({"id": m["id"], "prefix35_in_file": pref in text, "prefix": pref})
print("missing TC-PY rows:", len(res))
print("with 35-char prefix present:", sum(1 for r in res if r["prefix35_in_file"]))
for r in res:
    print(("OK  " if r["prefix35_in_file"] else "GONE"), r["prefix"])
