# -*- coding: utf-8 -*-
"""Coverage of one recorded path by every evidence channel.

For a repo-relative target path (matching against the recorded absolute paths),
report:
  * writes (whole file) with byte size and time
  * read windows (offset, count, totalLines, time) merged into covered line ranges
  * edits in time order with old/new line counts and whether `old` is found in
    the current best buffer
  * termdump candidates whose output may contain the file body

Nothing here writes anything.
"""
from __future__ import print_function
import io, json, os, re, sys, collections

IDX = r"C:\Users\wyl\AppData\Local\Temp\mcp-recovery\staging\__payload-index"
W = os.path.join(IDX, "events-write.jsonl")
E = os.path.join(IDX, "events-edit.jsonl")
R = os.path.join(IDX, "events-read.jsonl")
TD = os.path.join(IDX, "events-termdump.jsonl")


def norm(p):
    return (p or "").replace("/", "\\").lower()


def rows_for(fp, target):
    """All rows whose path == target (case/sep insensitive), plus near matches."""
    exact, near = [], []
    t = norm(target)
    with io.open(fp, encoding="utf-8", errors="replace") as fh:
        for ln in fh:
            ln = ln.strip()
            if not ln:
                continue
            try:
                o = json.loads(ln)
            except Exception:
                continue
            p = norm(o.get("path") or "")
            if not p:
                continue
            if p == t:
                exact.append(o)
            elif t in p or os.path.basename(p) == os.path.basename(t):
                near.append(o)
    return exact, near


def coverage(reads):
    """Merge numbered windows into covered 1-based line ranges."""
    marks = collections.Counter()
    total_lines = collections.Counter()
    for r in reads:
        off = r.get("offset")
        lines = r.get("lines") or []
        tl = r.get("totalLines")
        total_lines[tl] += 1
        for i in range(len(lines)):
            marks[(off or 1) + i] += 1
    return marks, total_lines


def ranges(marks):
    ks = sorted(marks)
    out = []
    if not ks:
        return out
    s = p = ks[0]
    for k in ks[1:]:
        if k == p + 1:
            p = k
            continue
        out.append((s, p))
        s = p = k
    out.append((s, p))
    return out


def main():
    target = sys.argv[1]
    print("target: %s" % target)

    wr, wrn = rows_for(W, target)
    ed, edn = rows_for(E, target)
    rd, rdn = rows_for(R, target)
    print("writes=%d (near=%d)  edits=%d (near=%d)  reads=%d (near=%d)"
          % (len(wr), len(wrn), len(ed), len(edn), len(rd), len(rdn)))

    print("\n--- WRITES ---")
    for o in sorted(wr, key=lambda x: x.get("time", 0)):
        c = o.get("content") or ""
        print("  seq=%-6s t=%-14s bytes=%-8d lines=%-6d res=%s"
              % (o.get("seq"), o.get("time"), len(c.encode("utf-8")),
                 c.count("\n") + 1, (o.get("result") or "")[:40]))

    print("\n--- READS: totalLines census ---")
    for tl, n in total_lines if False else []:
        pass
    marks, tl = coverage(rd)
    for k in sorted(tl, key=lambda x: (x is None, x)):
        print("  totalLines=%s x%d" % (k, tl[k]))
    rgs = ranges(marks)
    print("  distinct lines covered: %d in %d ranges" % (len(marks), len(rgs)))
    print("  ranges:")
    for a, b in rgs:
        print("     %5d - %-5d  (%d lines)" % (a, b, b - a + 1))

    print("\n--- EDITS (time order, applied only) ---")
    applied = [e for e in ed if not (e.get("result") or "").lstrip().startswith("Error")]
    refused = [e for e in ed if (e.get("result") or "").lstrip().startswith("Error")]
    print("  applied=%d refused=%d" % (len(applied), len(refused)))
    for e in sorted(applied, key=lambda x: x.get("time", 0)):
        old = e.get("old") or ""
        new = e.get("new") or ""
        print("  seq=%-6s t=%-14s old=%-4d new=%-4d  %s"
              % (e.get("seq"), e.get("time"), old.count("\n") + 1, new.count("\n") + 1,
                 old.split("\n")[0][:90]))
    if refused:
        print("  -- refused --")
        for e in sorted(refused, key=lambda x: x.get("time", 0)):
            print("  seq=%-6s t=%-14s %s" % (e.get("seq"), e.get("time"),
                                             (e.get("result") or "")[:70]))
    return 0


if __name__ == "__main__":
    sys.exit(main())
