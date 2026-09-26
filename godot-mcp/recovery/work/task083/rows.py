# -*- coding: utf-8 -*-
"""TASK-083: list read windows (revision, offset, span) for one module path."""
import io
import json
import os
import sys

IDX = r"C:\Users\wyl\AppData\Local\Temp\mcp-recovery\staging\__payload-index"


def norm(p):
    return p.replace("/", "\\").lower()


def main():
    sub = norm(sys.argv[1])
    rows = []
    with io.open(os.path.join(IDX, "events-read.jsonl"), "r", encoding="utf-8", errors="replace") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            r = json.loads(line)
            if sub in norm(r.get("path", "")):
                rows.append(r)
    rows.sort(key=lambda r: ((r.get("totalLines") or 0), r.get("time", 0)))
    print("%d rows" % len(rows))
    for r in rows:
        lns = r.get("lines") or []
        lo = min(x[0] for x in lns) if lns else -1
        hi = max(x[0] for x in lns) if lns else -1
        print("  rev%-5s offset=%-5s span=%d-%d n=%-4d time=%s f=%s" % (
            r.get("totalLines"), r.get("offset"), lo, hi, len(lns), r.get("time"), r.get("f")))


if __name__ == "__main__":
    main()
