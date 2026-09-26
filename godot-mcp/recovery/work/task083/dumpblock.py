# -*- coding: utf-8 -*-
"""TASK-083: dump a contiguous block of lines from a specific read revision."""
import io
import json
import os
import sys

IDX = r"C:\Users\wyl\AppData\Local\Temp\mcp-recovery\staging\__payload-index"


def norm(p):
    return p.replace("/", "\\").lower()


def main():
    sub = norm(sys.argv[1])
    rev = int(sys.argv[2])
    a = int(sys.argv[3])
    b = int(sys.argv[4])
    out = []
    with io.open(os.path.join(IDX, "events-read.jsonl"), "r", encoding="utf-8", errors="replace") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            r = json.loads(line)
            if sub not in norm(r.get("path", "")) or r.get("totalLines") != rev:
                continue
            lns = dict((no, t) for no, t in (r.get("lines") or []))
            got = [no for no in range(a, b + 1) if no in lns]
            if got:
                out.append((r.get("time", 0), lns, r.get("f")))
    if not out:
        print("no window")
        return
    out.sort()
    _, lns, f = out[-1]
    print("(revision %d, transcript %s)" % (rev, f))
    for no in range(a, b + 1):
        if no in lns:
            print("%5d| %s" % (no, lns[no]))
        else:
            print("%5d| @@ABSENT@@" % no)


if __name__ == "__main__":
    main()
