# -*- coding: utf-8 -*-
"""TASK-083: find every read window containing a token, and print the window with
its revision - so a dropped function body can be recovered verbatim.

usage: findtoken.py <module-relpath> <token> [before] [after]
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
    token = sys.argv[2]
    before = int(sys.argv[3]) if len(sys.argv) > 3 else 4
    after = int(sys.argv[4]) if len(sys.argv) > 4 else 40
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
    seen = set()
    for r in rows:
        lns = dict((no, t) for no, t in (r.get("lines") or []))
        for no in sorted(lns):
            if token in lns[no]:
                key = (r.get("totalLines"), no)
                if key in seen:
                    continue
                seen.add(key)
                print("=== rev%s line %d (%s)" % (r.get("totalLines"), no, r.get("f")))
                for i in range(no - before, no + after + 1):
                    if i in lns:
                        print("   %5d| %s" % (i, lns[i]))
                break


if __name__ == "__main__":
    main()
