#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""C: diff the regenerated ledger against the committed coverage.json."""
import io, json, os, collections
ROOT = r"F:\moonbit-hof-rs\godot-mcp"
HERE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(HERE, "coverage_diff.json")
old = json.load(io.open(os.path.join(ROOT, "coverage.json"), "r", encoding="utf-8"))
new = json.load(io.open(os.path.join(HERE, "coverage.regen.json"), "r", encoding="utf-8"))
top_diff = [k for k in set(old) | set(new) if old.get(k) != new.get(k)]
old_rows = {r["tool"]: r for r in old["tools"]}
new_rows = {r["tool"]: r for r in new["tools"]}
row_diff = []
for t in set(old_rows) | set(new_rows):
    a, b = old_rows.get(t), new_rows.get(t)
    if a != b:
        row_diff.append({"tool": t, "old": a, "new": b})
# line-by-line text comparison
old_text = io.open(os.path.join(ROOT, "coverage.json"), "r", encoding="utf-8").read().split("\n")
new_text = io.open(os.path.join(HERE, "coverage.regen.json"), "r", encoding="utf-8").read().split("\n")
text_diffs = sum(1 for a, b in zip(old_text, new_text) if a != b) + abs(len(old_text) - len(new_text))
out = {"top_level_differing_keys": top_diff, "differing_tool_rows": len(row_diff),
       "differing_tool_names": [d["tool"] for d in row_diff][:10],
       "old_lines": len(old_text), "new_lines": len(new_text), "differing_text_lines": text_diffs,
       "old_roles": {k: old.get(k) for k in ("mode", "generated_utc", "status_counts", "evidence_channel_counts")},
       "new_roles": {k: new.get(k) for k in ("mode", "generated_utc", "status_counts", "evidence_channel_counts")}}
with io.open(OUT, "w", encoding="utf-8", newline="\n") as h:
    h.write(json.dumps(out, ensure_ascii=False, indent=2))
print(json.dumps(out, ensure_ascii=False, indent=2)[:3000])
