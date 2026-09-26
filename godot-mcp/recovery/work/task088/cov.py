# -*- coding: utf-8 -*-
"""task088: per-skeleton coverage report for one recorded path.

usage: python cov.py <abs-path> <outfile>
"""
from __future__ import print_function
import io, json, os, sys

IDX = r"C:\Users\wyl\AppData\Local\Temp\mcp-recovery\staging\__payload-index"


def norm(p):
    return (p or "").replace("/", "\\").lower()


def main():
    target = norm(sys.argv[1])
    out = sys.argv[2]
    reads = []
    with io.open(os.path.join(IDX, "events-read.jsonl"), encoding="utf-8", errors="replace") as fh:
        for ln in fh:
            ln = ln.strip()
            if not ln:
                continue
            try:
                o = json.loads(ln)
            except Exception:
                continue
            if norm(o.get("path")) == target:
                reads.append(o)
    lines = []
    lines.append("path=%s total read rows=%d" % (target, len(reads)))
    by_sk = {}
    for r in reads:
        by_sk.setdefault(r.get("totalLines") or 0, []).append(r)
    for sk in sorted(by_sk):
        rows = by_sk[sk]
        cov = set()
        for r in rows:
            off = r.get("offset") or 1
            for i in range(len(r.get("lines") or [])):
                cov.add(off + i)
        holes = [n for n in range(1, sk + 1) if n not in cov]
        newest = max((r.get("time", 0) for r in rows), default=0)
        lines.append("skeleton=%-6d windows=%-4d covered=%-6d holes=%-6d newest_t=%s"
                     % (sk, len(rows), len(cov), len(holes), newest))
    data = "\n".join(lines) + "\n"
    io.open(out, "w", encoding="utf-8", newline="\n").write(data)
    print(data)


if __name__ == "__main__":
    main()
