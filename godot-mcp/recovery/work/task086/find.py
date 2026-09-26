# -*- coding: utf-8 -*-
"""Search the three authoritative event streams for a literal string.

Prints, for every hit, the stream, the record's path/seq/time and a window of
context around the hit (so recorded text can be read out of the log).

usage: python find.py "<needle>" [window] [maxhits]
"""
import io
import json
import os
import sys

IDX = r"C:\Users\wyl\AppData\Local\Temp\mcp-recovery\staging\__payload-index"
STREAMS = ["events-write.jsonl", "events-edit.jsonl", "events-read.jsonl"]

needle = sys.argv[1]
win = int(sys.argv[2]) if len(sys.argv) > 2 else 400
maxhits = int(sys.argv[3]) if len(sys.argv) > 3 else 20

hits = 0
for which in STREAMS:
    p = os.path.join(IDX, which)
    with io.open(p, "r", encoding="utf-8", errors="replace") as f:
        for line in f:
            if needle not in line:
                continue
            line = line.strip()
            if not line:
                continue
            r = json.loads(line)
            hits += 1
            if hits > maxhits:
                raise SystemExit("(stopping at %d hits)" % maxhits)
            print("=" * 100)
            print("%s  seq=%s  t=%s  path=%s" % (which, r.get("seq"), r.get("time"), r.get("path")))
            if "result" in r:
                print("  result: %s" % (r.get("result") or "")[:160].replace("\n", " "))
            for field in ("content", "old", "new"):
                v = r.get(field)
                if not isinstance(v, str):
                    continue
                k = v.find(needle)
                if k < 0:
                    # read windows carry the text inside `lines`
                    continue
                a = max(0, k - win)
                b = min(len(v), k + len(needle) + win)
                print("  --- %s [%d..%d of %d] ---" % (field, a, b, len(v)))
                print(v[a:b])
            lines = r.get("lines")
            if isinstance(lines, list):
                for no, txt in lines:
                    if isinstance(txt, str) and needle in txt:
                        print("  --- read line %s: %s" % (no, txt))
print("total hits = %d" % hits)
