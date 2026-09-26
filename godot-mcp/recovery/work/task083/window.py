# -*- coding: utf-8 -*-
"""TASK-083: dump every read window covering a line range of one file, newest
revision first, so a dropped span can be recovered verbatim."""
import io
import json
import os
import sys

IDX = r"C:\Users\wyl\AppData\Local\Temp\mcp-recovery\staging\__payload-index"


def norm(p):
    return p.replace("/", "\\").lower()


def main():
    sub = norm(sys.argv[1])
    a = int(sys.argv[2])
    b = int(sys.argv[3])
    rows = []
    with io.open(os.path.join(IDX, "events-read.jsonl"), "r", encoding="utf-8", errors="replace") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            r = json.loads(line)
            if sub in norm(r.get("path", "")):
                rows.append(r)
    rows.sort(key=lambda r: ((r.get("totalLines") or 0), r.get("time", 0)), reverse=True)
    print("rows=%d (sorted by revision desc, then time desc)" % len(rows))
    for r in rows:
        lns = [x for x in (r.get("lines") or []) if a <= x[0] <= b]
        if not lns:
            continue
        print("--- rev%s time=%s seq=%s f=%s" % (r.get("totalLines"), r.get("time"), r.get("seq"), r.get("f")))
        for no, txt in lns:
            print("   %5d| %s" % (no, txt[:150]))


if __name__ == "__main__":
    main()
