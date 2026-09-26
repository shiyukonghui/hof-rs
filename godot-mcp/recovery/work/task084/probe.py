# -*- coding: utf-8 -*-
"""TASK-084 forensics: per-file read-window survey.

usage:  python probe.py <subpath>            -> summary of every read window + target
        python probe.py <subpath> <a> <b>    -> dump lines a..b from every window (rev desc)
        python probe.py <subpath> <a> <b> <rev> -> dump lines a..b of one revision's windows
"""
import io
import json
import os
import sys

IDX = r"C:\Users\wyl\AppData\Local\Temp\mcp-recovery\staging\__payload-index"


def norm(p):
    return p.replace("/", "\\").lower()


def load_events(sub):
    rows = []
    with io.open(os.path.join(IDX, "events-read.jsonl"), "r", encoding="utf-8", errors="replace") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            r = json.loads(line)
            if sub in norm(r.get("path", "")):
                rows.append(r)
    return rows


def target_of(sub):
    """(target_rev, target_lines, read_cov) from reconstruction.jsonl, if recorded."""
    out = None
    p = os.path.join(IDX, "reconstruction.jsonl")
    if not os.path.exists(p):
        return out
    with io.open(p, "r", encoding="utf-8", errors="replace") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            r = json.loads(line)
            if sub in norm(r.get("path", "") or r.get("sub", "")):
                out = r
    return out


def main():
    sub = norm(sys.argv[1])
    rows = load_events(sub)
    total_of = lambda r: r.get("totalLines") or 0
    if len(sys.argv) == 2:
        t = target_of(sub)
        print("== reconstruction entry: %s" % json.dumps(t, ensure_ascii=False))
        print("== %d read windows" % len(rows))
        byrev = {}
        for r in rows:
            byrev.setdefault(total_of(r), []).append(r)
        for rev in sorted(byrev, reverse=True):
            ws = byrev[rev]
            lo = min(min((x[0] for x in (w.get("lines") or [[0, ""]])), default=0) for w in ws)
            hi = max(max((x[0] for x in (w.get("lines") or [[0, ""]])), default=0) for w in ws)
            nlines = len(set(x[0] for w in ws for x in (w.get("lines") or [])))
            print("rev%-6s windows=%-3d union-lines=%-5d span=%d..%d  times=%s" % (
                rev, len(ws), nlines, lo, hi, ",".join(str(w.get("time")) for w in ws[:4])))
        return

    a = int(sys.argv[2])
    b = int(sys.argv[3])
    if len(sys.argv) > 4:
        rev = int(sys.argv[4])
        rows = [r for r in rows if total_of(r) == rev]
    rows.sort(key=lambda r: (total_of(r), r.get("time", 0)), reverse=True)
    for r in rows:
        lns = [x for x in (r.get("lines") or []) if a <= x[0] <= b]
        if not lns:
            continue
        print("--- rev%s t=%s seq=%s f=%s  (%d/%d lines in range)" % (
            r.get("totalLines"), r.get("time"), r.get("seq"), r.get("f"), len(lns), b - a + 1))
        for no, txt in lns:
            print("  %5d| %s" % (no, txt[:200]))


if __name__ == "__main__":
    main()
