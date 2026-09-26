# -*- coding: utf-8 -*-
"""Coverage report per recorded path (UTF-8 safe output)."""
from __future__ import print_function
import io, json, os, sys, collections
sys.path.insert(0, r"C:\Users\wyl\AppData\Local\Temp\mcp-recovery\work\task087")
import rep

IDX = r"C:\Users\wyl\AppData\Local\Temp\mcp-recovery\staging\__payload-index"


def norm(p):
    return (p or "").replace("/", "\\").lower()


def load(fp, target):
    out = []
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
            if norm(o.get("path") or "") == t:
                out.append(o)
    return out


def applied(e):
    return not (e.get("result") or "").lstrip().startswith("Error")


def main():
    target = sys.argv[1]
    rep.log("== target: %s" % target)
    wr = load(os.path.join(IDX, "events-write.jsonl"), target)
    ed = load(os.path.join(IDX, "events-edit.jsonl"), target)
    rd = load(os.path.join(IDX, "events-read.jsonl"), target)
    rep.log("writes=%d edits=%d reads=%d" % (len(wr), len(ed), len(rd)))

    for o in sorted(wr, key=lambda x: x.get("time", 0)):
        c = o.get("content") or ""
        rep.log("  WRITE seq=%s t=%s bytes=%d lines=%d res=%s"
                % (o.get("seq"), o.get("time"), len(c.encode("utf-8")),
                   c.count("\n") + 1, (o.get("result") or "")[:50]))

    marks = collections.Counter()
    tlc = collections.Counter()
    for r in sorted(rd, key=lambda x: x.get("time", 0)):
        off = r.get("offset") or 1
        tl = r.get("totalLines")
        lines = r.get("lines") or []
        tlc[tl] += 1
        for i in range(len(lines)):
            marks[off + i] += 1
    rep.log("--- reads: totalLines census ---")
    for k in sorted(tlc, key=lambda x: (x is None, x)):
        rep.log("   totalLines=%s x%d" % (k, tlc[k]))
    ks = sorted(marks)
    rngs = []
    if ks:
        s = p = ks[0]
        for k in ks[1:]:
            if k == p + 1:
                p = k
                continue
            rngs.append((s, p))
            s = p = k
        rngs.append((s, p))
    rep.log("   covered lines=%d in %d ranges (max line %s)"
            % (len(marks), len(rngs), max(ks) if ks else None))
    for a, b in rngs[:60]:
        rep.log("      %6d - %-6d (%d)" % (a, b, b - a + 1))
    if len(rngs) > 60:
        rep.log("      ... %d more ranges" % (len(rngs) - 60))

    ap = [e for e in ed if applied(e)]
    rf = [e for e in ed if not applied(e)]
    rep.log("--- edits: applied=%d refused=%d ---" % (len(ap), len(rf)))
    for e in sorted(ed, key=lambda x: x.get("time", 0)):
        old = e.get("old") or ""
        new = e.get("new") or ""
        rep.log("  %s seq=%-6s t=%-14s old=%-4d new=%-4d | %s"
                % ("OK " if applied(e) else "REF", e.get("seq"), e.get("time"),
                   old.count("\n") + 1, new.count("\n") + 1,
                   old.split("\n")[0][:100]))
    rep.flush()


if __name__ == "__main__":
    main()
