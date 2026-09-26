# -*- coding: utf-8 -*-
"""Print the recorded read windows of one file (newest last), optionally
filtering the printed lines by a substring.

usage: python reads.py <substr> [pattern] [last_n_windows]
"""
import io
import json
import os
import sys

IDX = r"C:\Users\wyl\AppData\Local\Temp\mcp-recovery\staging\__payload-index"


def norm(p):
    return (p or "").replace("/", "\\").lower()


sub = norm(sys.argv[1])
pat = sys.argv[2] if len(sys.argv) > 2 and sys.argv[2] != "-" else None
last = int(sys.argv[3]) if len(sys.argv) > 3 else 20

rows = []
with io.open(os.path.join(IDX, "events-read.jsonl"), "r", encoding="utf-8", errors="replace") as f:
    for line in f:
        if "test_mcp_server" not in line and "DESIGN" not in line:
            pass
        line = line.strip()
        if not line:
            continue
        r = json.loads(line)
        if sub not in norm(r.get("path")):
            continue
        rows.append(r)
rows.sort(key=lambda r: r.get("time", 0))
print("%d read windows" % len(rows))
for r in rows[-last:]:
    lns = r.get("lines") or []
    sel = [(no, t) for no, t in lns if pat is None or pat in (t or "")]
    print("--- t=%s totalLines=%s window_lines=%d  selected=%d  f=%s" % (
        r.get("time"), r.get("totalLines"), len(lns), len(sel), (r.get("f") or "")[:8]))
    for no, t in sel:
        print("    %6s| %s" % (no, t))
