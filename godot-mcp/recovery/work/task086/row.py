# -*- coding: utf-8 -*-
"""Dump one event row's metadata (no content) for a path/stream."""
import io
import json
import os
import sys

IDX = r"C:\Users\wyl\AppData\Local\Temp\mcp-recovery\staging\__payload-index"


def norm(p):
    return (p or "").replace("/", "\\").lower()


which = sys.argv[1]
needle = norm(sys.argv[2])
lim = int(sys.argv[3]) if len(sys.argv) > 3 else 5
p = os.path.join(IDX, which)
n = 0
with io.open(p, "r", encoding="utf-8", errors="replace") as f:
    for i, line in enumerate(f):
        if needle not in norm(line):
            continue
        n += 1
        if n > lim:
            break
        try:
            r = json.loads(line)
        except Exception as e:
            print("line %d UNPARSED %s" % (i + 1, e))
            continue
        meta = {k: (len(v) if isinstance(v, str) else v) for k, v in r.items()}
        print("line %d: %s" % (i + 1, json.dumps(meta, ensure_ascii=False)[:600]))
print("total matching lines (scan) = %d" % n)
