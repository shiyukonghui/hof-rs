# -*- coding: utf-8 -*-
"""Find the edits of one file whose old/new text contains a needle, in time
order, and print the matching span of the text.

usage: python evhit.py <path-substr> "<needle>" [which: old|new|both] [max]
"""
import io
import json
import os
import sys

IDX = r"C:\Users\wyl\AppData\Local\Temp\mcp-recovery\staging\__payload-index"


def norm(p):
    return (p or "").replace("/", "\\").lower()


sub = norm(sys.argv[1])
needle = sys.argv[2]
which = sys.argv[3] if len(sys.argv) > 3 else "new"
maxhits = int(sys.argv[4]) if len(sys.argv) > 4 else 30

rows = []
with io.open(os.path.join(IDX, "events-edit.jsonl"), "r", encoding="utf-8", errors="replace") as f:
    for line in f:
        line = line.strip()
        if not line:
            continue
        r = json.loads(line)
        if sub not in norm(r.get("path")):
            continue
        rows.append(r)
rows.sort(key=lambda r: r.get("time", 0))
print("%d edits for %s" % (len(rows), sub))
n = 0
for r in rows:
    for field in (("old", "new") if which == "both" else (which,)):
        v = r.get(field) or ""
        k = v.find(needle)
        if k < 0:
            continue
        n += 1
        if n > maxhits:
            raise SystemExit("(stopping at %d hits)" % maxhits)
        print("=" * 100)
        print("seq=%s t=%s field=%s  old=%d new=%d lines  ok=%s" % (
            r.get("seq"), r.get("time"), field,
            len((r.get("old") or "").split("\n")), len((r.get("new") or "").split("\n")),
            not (r.get("result") or "").lstrip().startswith("Error")))
        print("  result: %s" % (r.get("result") or "")[:120].replace("\n", " "))
        a = max(0, k - 900)
        b = min(len(v), k + 2600)
        print(v[a:b])
