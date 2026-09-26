# -*- coding: utf-8 -*-
"""List every recorded edit of one file in time order (metadata only), or dump
one edit's full old/new text.

usage: python evlist.py <path-substr>            -> metadata list
       python evlist.py <path-substr> <seq> <old|new>  -> full text
"""
import io
import json
import os
import sys

IDX = r"C:\Users\wyl\AppData\Local\Temp\mcp-recovery\staging\__payload-index"


def norm(p):
    return (p or "").replace("/", "\\").lower()


sub = norm(sys.argv[1])
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

if len(sys.argv) > 3:
    seq = str(sys.argv[2])
    field = sys.argv[3]
    for r in rows:
        if str(r.get("seq")) == seq:
            print(r.get(field) or "")
            raise SystemExit(0)
    raise SystemExit("seq %s not found" % seq)

print("%d edits for %s" % (len(rows), sub))
for r in rows:
    old = r.get("old") or ""
    new = r.get("new") or ""
    print("seq=%-6s t=%-14s old=%-5d new=%-5d ok=%-5s  OLD> %-70s  NEW> %s" % (
        r.get("seq"), r.get("time"), len(old.split("\n")), len(new.split("\n")),
        not (r.get("result") or "").lstrip().startswith("Error"),
        old.split("\n")[0][:70] if old else "",
        new.split("\n")[0][:70] if new else ""))
