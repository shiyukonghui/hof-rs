"""Scan test_mcp_server.h for registry-size assertions and stale generation numbers."""
import re, sys, io, json

PATH = r"H:\rebuild\godot\modules\mcp_server\tests\test_mcp_server.h"

STALE = {"48", "76", "59", "35", "31", "24", "40", "175", "176", "153", "72", "66", "49", "11", "13"}
NEW = {"73", "177", "154", "50"}

PATTERNS = [
    ("tool_count", re.compile(r"get_tool_count\(\)\s*==\s*(\d+)")),
    ("visible_true", re.compile(r"get_visible_tool_count\(true\)\s*==\s*(\d+)")),
    ("visible_false", re.compile(r"get_visible_tool_count\(false\)\s*==\s*(\d+)")),
    ("list_true", re.compile(r"build_tools_list\(true\)\.size\(\)\s*==\s*(\d+)")),
    ("list_false", re.compile(r"build_tools_list\(false\)\.size\(\)\s*==\s*(\d+)")),
    ("editor_list_sz", re.compile(r"editor_list\.size\(\)\s*==\s*(\d+)")),
    ("game_list_sz", re.compile(r"game_list\.size\(\)\s*==\s*(\d+)")),
]

lines = io.open(PATH, encoding="utf-8", errors="replace").read().splitlines()
hits = []
for i, ln in enumerate(lines, 1):
    for kind, pat in PATTERNS:
        for m in pat.finditer(ln):
            hits.append((i, kind, m.group(1), ln.strip()))

print("total registry-size assertion sites:", len(hits))
byval = {}
for i, kind, v, txt in hits:
    byval.setdefault(v, []).append((i, kind))

print("\n--- value census ---")
for v in sorted(byval, key=lambda x: (len(x), x)):
    print(f"  {v:>4} : {len(byval[v]):>3} sites   lineages={sorted(set(k for _, k in byval[v]))}")

print("\n--- sites with STALE values ---")
for i, kind, v, txt in hits:
    if v in STALE:
        print(f"  line {i:>6} [{kind}] == {v}   | {txt}")
