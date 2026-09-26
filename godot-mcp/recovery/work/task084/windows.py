# -*- coding: utf-8 -*-
"""Dump, for every window of a file, the lines in a range, tagged with the window's
own totalLines/time, to find a contiguous run that stitches into a reference revision.

usage: python windows.py <subpath> <a> <b> [rev]
"""
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
    rev = int(sys.argv[4]) if len(sys.argv) > 4 else None
    rows = []
    with io.open(os.path.join(IDX, "events-read.jsonl"), "r", encoding="utf-8", errors="replace") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            r = json.loads(line)
            if sub not in norm(r.get("path", "")):
                continue
            if rev is not None and (r.get("totalLines") or 0) != rev:
                continue
            rows.append(r)
    rows.sort(key=lambda r: (r.get("time", 0)))
    for r in rows:
        lns = [x for x in (r.get("lines") or []) if a <= x[0] <= b]
        if not lns:
            continue
        print("=== rev%s t=%s seq=%s  covers %d..%d in range" % (
            r.get("totalLines"), r.get("time"), r.get("seq"),
            min(x[0] for x in lns), max(x[0] for x in lns)))
        for no, txt in lns:
            print("  %5d| %s" % (no, txt[:200]))


if __name__ == "__main__":
    main()
