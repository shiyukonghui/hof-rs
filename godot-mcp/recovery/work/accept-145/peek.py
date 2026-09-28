#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Peek at the artifact formats (read-only)."""
import io
import json
import os

ROOT = r"F:\moonbit-hof-rs\godot-mcp"
DOCS = os.path.join(ROOT, "godot", "modules", "mcp_server", "docs")

def head(path, n=3):
    with io.open(path, "r", encoding="utf-8") as h:
        d = json.load(h)
    return d

# tools_list
tl = head(os.path.join(DOCS, "tools_list.renamed.json"))
print("tools_list type:", type(tl).__name__)
if isinstance(tl, dict):
    print("keys:", list(tl.keys())[:8])
    tools = tl.get("tools") or tl.get("result", {}).get("tools")
else:
    tools = tl
print("n tools:", len(tools) if tools else None)
print("first tool:", json.dumps(tools[0], ensure_ascii=False)[:800] if tools else None)

ch = head(os.path.join(ROOT, "tools", "tool_channels.json"))
print("\nchannels keys:", list(ch.keys())[:8])
print("declared_at:", ch.get("declared_at"))
t = ch.get("tools")
print("channels tools type:", type(t).__name__, "n=", len(t) if t else None)
if isinstance(t, dict):
    k = next(iter(t))
    print("sample:", k, json.dumps(t[k], ensure_ascii=False))
elif isinstance(t, list):
    print("sample:", json.dumps(t[0], ensure_ascii=False))

cov = head(os.path.join(ROOT, "coverage.json"))
print("\ncoverage top keys:", list(cov.keys()))
print("mode:", cov.get("mode"))
rows = cov.get("tools")
print("n rows:", len(rows))
row = next(r for r in rows if r["tool"] == "project_get_filesystem_tree")
print("sample row:", json.dumps(row, ensure_ascii=False)[:1500])
