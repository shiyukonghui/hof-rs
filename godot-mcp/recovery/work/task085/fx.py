# -*- coding: utf-8 -*-
"""TASK-085 evidence engine.

Authoritative sources, per the driver's ruling (A):
  events-write.jsonl  -> the whole new text of a recorded write
  events-edit.jsonl   -> each edit's full OLD and NEW text

For one file this reports, in time order:
  * every whole-file write (seq / time / line count)
  * every edit (seq / time / old lines / new lines / exact-match status)
  * every read window per totalLines (rev / time span / union lines)

usage:
  python fx.py <subpath>              -> the survey above
  python fx.py <subpath> --writes     -> also dump write line counts + sha
"""
import collections
import hashlib
import io
import json
import os
import sys

IDX = r"C:\Users\wyl\AppData\Local\Temp\mcp-recovery\staging\__payload-index"


def norm(p):
    return (p or "").replace("/", "\\").lower()


def load(which, sub):
    out = []
    p = os.path.join(IDX, which)
    if not os.path.exists(p):
        return out
    with io.open(p, "r", encoding="utf-8", errors="replace") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            r = json.loads(line)
            if sub in norm(r.get("path", "")):
                out.append(r)
    return out


def sha(s):
    return hashlib.sha256(s.encode("utf-8", "replace")).hexdigest()[:16]


def main():
    sub = norm(sys.argv[1])
    writes = load("events-write.jsonl", sub)
    edits = load("events-edit.jsonl", sub)
    reads = load("events-read.jsonl", sub)

    writes.sort(key=lambda r: r.get("time", 0))
    edits.sort(key=lambda r: r.get("time", 0))

    print("== subpath %s" % sub)
    print("== %d writes, %d edits, %d read windows" % (len(writes), len(edits), len(reads)))

    print("\n-- whole-file writes (time order) --")
    for w in writes:
        c = w.get("content") or ""
        print("  seq=%-6s t=%-14s lines=%-5d sha=%s path=%s" % (
            w.get("seq"), w.get("time"), len(c.split("\n")), sha(c), w.get("path")))

    print("\n-- edits (time order) --")
    for e in edits:
        o = e.get("old") or ""
        n = e.get("new") or ""
        print("  seq=%-6s t=%-14s old=%-5d new=%-5d  %s" % (
            e.get("seq"), e.get("time"), len(o.split("\n")), len(n.split("\n")),
            o.split("\n")[0][:88]))

    print("\n-- read windows by revision --")
    byrev = collections.defaultdict(list)
    for r in reads:
        byrev[r.get("totalLines") or 0].append(r)
    for rev in sorted(byrev, reverse=True):
        ws = byrev[rev]
        times = [w.get("time", 0) for w in ws]
        n = len(set(x[0] for w in ws for x in (w.get("lines") or [])))
        print("  rev=%-6d windows=%-3d union-lines=%-5d times=%s..%s" % (
            rev, len(ws), n, min(times), max(times)))

    if "--writes" in sys.argv:
        print("\n-- write bodies --")
        for w in writes:
            print("  seq=%s t=%s" % (w.get("seq"), w.get("time")))
            for i, l in enumerate((w.get("content") or "").split("\n")[:40], 1):
                print("    %4d| %s" % (i, l[:180]))


if __name__ == "__main__":
    main()
