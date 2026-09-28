#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""TASK-147 A3: every path-ish token referenced by the matrix must exist."""
import io, os, re, collections

t = io.open("recovery/TEST-CASES.md", encoding="utf-8").read()
pat = re.compile(r"`([A-Za-z0-9_./\\-]+\.(?:py|ps1|cmd|json|jsonl|h|cpp|md))`")
miss = collections.Counter()
seen = 0
for m in pat.finditer(t):
    seen += 1
    p = m.group(1).replace("\\", "/")
    if p.startswith("./"):
        p = p[2:]
    if not os.path.exists(p):
        miss[p] += 1
print("referenced file tokens: %d" % seen)
print("missing files: %d" % len(miss))
for p, n in sorted(miss.items()):
    print("   %-60s x%d" % (p, n))

print()
# bare basenames (e.g. `tool_registry.cpp:864`), resolved anywhere under godot-mcp
index = {}
for root, dirs, files in os.walk("."):
    dirs[:] = [d for d in dirs if d not in (".git", "node_modules", "__pycache__", "runs")]
    for fn in files:
        if fn.endswith((".cpp", ".h", ".py", ".ps1", ".json")):
            index.setdefault(fn, []).append(os.path.join(root, fn))
bare = re.compile(r"`([A-Za-z0-9_]+\.(?:cpp|h|py|ps1|json))(?::(\d+)(?:-(\d+))?)?`")
missing_bare = collections.Counter()
for m in bare.finditer(t):
    if "/" in m.group(0):
        continue
    fn = m.group(1)
    if fn not in index:
        missing_bare[m.group(0)] += 1
print("bare basenames not present anywhere under godot-mcp:")
for k, n in sorted(missing_bare.items()):
    print("   %-40s x%d" % (k, n))
print("(none)" if not missing_bare else "")
