# -*- coding: utf-8 -*-
"""Inventory: which module paths appear in each event stream."""
import io
import json
import os
import sys
from collections import defaultdict

IDX = r"C:\Users\wyl\AppData\Local\Temp\mcp-recovery\staging\__payload-index"

WHICH = ["events-write.jsonl", "events-edit.jsonl", "events-read.jsonl"]


def norm(p):
    return (p or "").replace("/", "\\").lower()


def main():
    needle = norm(sys.argv[1]) if len(sys.argv) > 1 else ""
    want = sys.argv[2] if len(sys.argv) > 2 else "counts"
    for which in WHICH:
        p = os.path.join(IDX, which)
        n = 0
        perpath = defaultdict(int)
        times = defaultdict(list)
        with io.open(p, "r", encoding="utf-8", errors="replace") as f:
            for line in f:
                line = line.strip()
                if not line:
                    continue
                try:
                    r = json.loads(line)
                except Exception:
                    continue
                np = norm(r.get("path", ""))
                if needle and needle not in np:
                    continue
                n += 1
                perpath[np] += 1
                times[np].append(r.get("time", 0))
        print("== %s : %d rows matching %r" % (which, n, needle))
        if want == "paths":
            for k in sorted(perpath):
                print("   %6d  %s  t[%s..%s]" % (perpath[k], k, min(times[k]), max(times[k])))


if __name__ == "__main__":
    main()
