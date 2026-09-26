# -*- coding: utf-8 -*-
"""For every applied recorded edit, test whether its `old` matches a candidate.

An edit that matches a candidate proves the candidate is at/around that edit's
revision, and that the edit's `new` text belongs in the end state.

usage: python editmatch.py <abs-path> <candidate-file> [candidate-file ...]
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
    argv = sys.argv[2:]
    if "--report" in argv:
        rep.set_report(argv[argv.index("--report") + 1])
    cands = [a for a in argv if not a.startswith("--") and a != (argv[argv.index("--report") + 1] if "--report" in argv else None)]
    edits = []
    with io.open(os.path.join(IDX, "events-edit.jsonl"), encoding="utf-8", errors="replace") as fh:
        for ln in fh:
            ln = ln.strip()
            if not ln:
                continue
            try:
                o = json.loads(ln)
            except Exception:
                continue
            if norm(o.get("path") or "") == norm(target):
                edits.append(o)
    edits.sort(key=lambda x: (x.get("time", 0), x.get("seq") or 0))
    bufs = []
    for c in cands:
        bufs.append((c, io.open(c, encoding="utf-8", errors="replace").read()))

    rep.log("%-6s %-15s %-8s %s" % ("seq", "time", "ok", " ".join("c%d" % i for i in range(len(cands)))))
    tally = [0] * len(bufs)
    applied = [e for e in edits if not (e.get("result") or "").lstrip().startswith("Error")]
    for e in applied:
        old = e.get("old") or ""
        marks = []
        for i, (c, b) in enumerate(bufs):
            n = b.count(old) if old else 0
            if n == 1:
                tally[i] += 1
            marks.append("+" if n == 1 else ("x%d" % n if n else "-"))
        rep.log("%-6s %-15s %-8s %s  | %s"
                % (e.get("seq"), e.get("time"), "OK", " ".join(marks),
                   old.split("\n")[0][:80]))
    rep.log("")
    rep.log("applied edits = %d" % len(applied))
    for i, (c, b) in enumerate(bufs):
        rep.log("  %-60s matched %d/%d  bytes=%d" % (os.path.basename(c), tally[i], len(applied), len(b.encode("utf-8"))))
    rep.flush()


if __name__ == "__main__":
    main()
