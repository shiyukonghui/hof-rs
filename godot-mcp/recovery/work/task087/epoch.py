# -*- coding: utf-8 -*-
"""Read-epoch analysis: which recorded revision's skeleton matches the target size?

Prints, for the newest N read rows (time desc): seq, time, totalLines, offset,
count, and the union skeleton that the NEWEST window of that revision plus all
other windows within EPOCH_WINDOW ms of it would produce (line count only).

usage: python epoch.py <abs-path> [N]
"""
from __future__ import print_function
import io, json, os, sys
sys.path.insert(0, r"C:\Users\wyl\AppData\Local\Temp\mcp-recovery\work\task087")
import rep

IDX = r"C:\Users\wyl\AppData\Local\Temp\mcp-recovery\staging\__payload-index"


def norm(p):
    return (p or "").replace("/", "\\").lower()


def main():
    target = sys.argv[1]
    n = int(sys.argv[2]) if len(sys.argv) > 2 else 12
    rows = []
    with io.open(os.path.join(IDX, "events-read.jsonl"), encoding="utf-8", errors="replace") as fh:
        for ln in fh:
            ln = ln.strip()
            if not ln:
                continue
            try:
                o = json.loads(ln)
            except Exception:
                continue
            if norm(o.get("path") or "") == norm(target):
                rows.append(o)
    rows.sort(key=lambda x: (x.get("time", 0), x.get("seq") or 0))
    rep.log("target %s  reads=%d" % (target, len(rows)))
    rep.log("%-6s %-15s %-10s %-8s %-6s %s" % ("seq", "time", "totalLines", "offset", "count", "f"))
    for o in rows[-n:]:
        rep.log("%-6s %-15s %-10s %-8s %-6s %s"
                % (o.get("seq"), o.get("time"), o.get("totalLines"), o.get("offset"),
                   len(o.get("lines") or []), (o.get("f") or "")[:40]))
    rep.log("")
    # per-revision skeleton: group by totalLines, report coverage of that group
    import collections
    g = collections.defaultdict(list)
    for o in rows:
        g[o.get("totalLines")].append(o)
    rep.log("%-10s %-6s %-8s %s" % ("totalLines", "rows", "newest_t", "covered/max"))
    for tl in sorted(g, key=lambda x: (x is None, x)):
        rs = g[tl]
        marks = set()
        for o in rs:
            off = o.get("offset") or 1
            for i in range(len(o.get("lines") or [])):
                marks.add(off + i)
        rep.log("%-10s %-6d %-8s %d/%d"
                % (tl, len(rs), max(r.get("time", 0) for r in rs) if rs else 0,
                   len(marks), max(marks) if marks else 0))
    rep.flush()


if __name__ == "__main__":
    main()
