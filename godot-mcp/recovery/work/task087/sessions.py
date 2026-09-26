# -*- coding: utf-8 -*-
"""Which recorded transcript gives the most complete snapshot of one revision?

For every transcript file `f`, report the union of line numbers it read and the
max line number, so a single-session full snapshot (the cleanest possible base)
can be identified.

usage: python sessions.py <abs-path> [--report F]
"""
from __future__ import print_function
import io, json, os, sys, collections
sys.path.insert(0, r"C:\Users\wyl\AppData\Local\Temp\mcp-recovery\work\task087")
import rep

IDX = r"C:\Users\wyl\AppData\Local\Temp\mcp-recovery\staging\__payload-index"


def norm(p):
    return (p or "").replace("/", "\\").lower()


def main():
    target = sys.argv[1]
    if "--report" in sys.argv:
        rep.set_report(sys.argv[sys.argv.index("--report") + 1])
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
    g = collections.defaultdict(lambda: {"marks": set(), "mx": 0, "t": 0, "tl": set(), "rows": 0})
    for o in rows:
        k = o.get("f") or "?"
        off = o.get("offset") or 1
        d = g[k]
        d["rows"] += 1
        d["t"] = max(d["t"], o.get("time", 0) or 0)
        d["tl"].add(o.get("totalLines"))
        for i in range(len(o.get("lines") or [])):
            d["marks"].add(off + i)
        d["mx"] = max(d["mx"], off + len(o.get("lines") or []) - 1)
    rep.log("target=%s reads=%d transcripts=%d" % (target, len(rows), len(g)))
    rep.log("%-46s %-6s %-8s %-10s %-16s %s" % ("file", "rows", "max", "covered", "totalLines", "t"))
    for k, d in sorted(g.items(), key=lambda kv: -(len(kv[1]["marks"]) / max(1, kv[1]["mx"]))):
        cov = len(d["marks"])
        pct = 100.0 * cov / max(1, d["mx"])
        rep.log("%-46s %-6d %-8d %-10s %-16s %d"
                % (k[:46], d["rows"], d["mx"], "%d (%.0f%%)" % (cov, pct),
                   sorted(x for x in d["tl"] if x is not None), d["t"]))
    rep.flush()


if __name__ == "__main__":
    main()
