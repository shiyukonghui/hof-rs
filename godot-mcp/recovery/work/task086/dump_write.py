# -*- coding: utf-8 -*-
"""Print the full recorded whole-file content of one write (by path substring)."""
import io
import json
import os
import sys

IDX = r"C:\Users\wyl\AppData\Local\Temp\mcp-recovery\staging\__payload-index"

needle = (sys.argv[1] or "").replace("/", "\\").lower()
stream = sys.argv[2] if len(sys.argv) > 2 else "events-write.jsonl"
seq = sys.argv[3] if len(sys.argv) > 3 else None

p = os.path.join(IDX, stream)
with io.open(p, "r", encoding="utf-8", errors="replace") as f:
    for line in f:
        if needle not in line.replace("/", "\\").lower():
            continue
        line = line.strip()
        if not line:
            continue
        r = json.loads(line)
        if needle not in (r.get("path") or "").replace("/", "\\").lower():
            continue
        if seq is not None and str(r.get("seq")) != str(seq):
            continue
        print("### seq=%s t=%s path=%s" % (r.get("seq"), r.get("time"), r.get("path")))
        print(r.get("content") or r.get("new") or "")
        print("### END")
