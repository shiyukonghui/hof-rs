# -*- coding: utf-8 -*-
"""Group the events of one file by their session file (`f`) and by time range."""
import io
import json
import os
import sys
from collections import defaultdict

IDX = r"C:\Users\wyl\AppData\Local\Temp\mcp-recovery\staging\__payload-index"


def norm(p):
    return (p or "").replace("/", "\\").lower()


target = norm(sys.argv[1])
for which in ("events-write.jsonl", "events-edit.jsonl", "events-read.jsonl"):
    groups = defaultdict(list)
    with io.open(os.path.join(IDX, which), "r", encoding="utf-8", errors="replace") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            r = json.loads(line)
            if target not in norm(r.get("path")):
                continue
            groups[r.get("f")].append(r)
    print("== %s : %d session files, %d rows" % (which, len(groups), sum(len(v) for v in groups.values())))
    for k, rows in sorted(groups.items(), key=lambda kv: min(r.get("time", 0) for r in kv[1])):
        ts = [r.get("time", 0) for r in rows]
        print("   n=%-4d t[%s .. %s]  %s" % (len(rows), min(ts), max(ts), k))
