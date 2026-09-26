# -*- coding: utf-8 -*-
"""Apply every recorded edit that matches the candidate exactly, repeatedly.

Passes: an edit whose `old` occurs exactly once is applied; later edits may
create new exact matches, so the pass repeats until a fixpoint.  A second,
anchor-based pass handles edits whose `old` no longer matches whole but whose
first and last lines both survive.

usage: python editchain.py <abs-path> <candidate> --out F [--report F] [--epoch MS]
"""
from __future__ import print_function
import io, json, os, sys
sys.path.insert(0, r"C:\Users\wyl\AppData\Local\Temp\mcp-recovery\work\task087")
import rep

IDX = r"C:\Users\wyl\AppData\Local\Temp\mcp-recovery\staging\__payload-index"


def norm(p):
    return (p or "").replace("/", "\\").lower()


def applied(e):
    return not (e.get("result") or "").lstrip().startswith("Error")


def main():
    target = sys.argv[1]
    cand = sys.argv[2]
    argv = sys.argv[3:]
    out = argv[argv.index("--out") + 1] if "--out" in argv else None
    if "--report" in argv:
        rep.set_report(argv[argv.index("--report") + 1])
    epoch = int(argv[argv.index("--epoch") + 1]) if "--epoch" in argv else 0

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
            if norm(o.get("path") or "") == norm(target) and applied(o) and (o.get("time", 0) or 0) > epoch:
                edits.append(o)
    edits.sort(key=lambda x: (x.get("time", 0), x.get("seq") or 0))
    buf = io.open(cand, encoding="utf-8", errors="replace").read()
    rep.log("candidate=%s bytes=%d  edits available=%d" % (os.path.basename(cand), len(buf.encode("utf-8")), len(edits)))

    done = set()
    rounds = 0
    while True:
        rounds += 1
        changed = 0
        for i, e in enumerate(edits):
            if i in done:
                continue
            old = e.get("old") or ""
            if old and buf.count(old) == 1:
                buf = buf.replace(old, e.get("new") or "", 1)
                done.add(i)
                changed += 1
        if changed == 0 or rounds > 40:
            break
    rep.log("exact pass: applied=%d in %d rounds; bytes=%d" % (len(done), rounds, len(buf.encode("utf-8"))))

    anchored = 0
    for i, e in enumerate(edits):
        if i in done:
            continue
        old = e.get("old") or ""
        new = e.get("new") or ""
        ol = old.split("\n")
        nl = new.split("\n")
        while ol and ol[-1] == "":
            ol.pop()
        while nl and nl[-1] == "":
            nl.pop()
        if not ol:
            continue
        h = buf.find(ol[0])
        if h < 0:
            continue
        if len(ol) == 1:
            buf = buf[:h] + "\n".join(nl) + buf[h + len(ol[0]):]
            done.add(i)
            anchored += 1
            continue
        t = buf.find(ol[-1], h + len(ol[0]))
        if t < 0:
            continue
        buf = buf[:h] + "\n".join(nl) + buf[t + len(ol[-1]):]
        done.add(i)
        anchored += 1
    rep.log("anchor pass: applied=%d; total=%d/%d" % (anchored, len(done), len(edits)))
    for i, e in enumerate(edits):
        if i not in done:
            rep.log("  UNUSED seq=%-6s t=%-14s | %s" % (e.get("seq"), e.get("time"), (e.get("old") or "").split("\n")[0][:100]))
    rep.log("final bytes=%d lines=%d" % (len(buf.encode("utf-8")), buf.count("\n") + 1))
    if out:
        with io.open(out, "w", encoding="utf-8", newline="\n") as f:
            f.write(buf)
        rep.log("wrote %s" % out)
    rep.flush()


if __name__ == "__main__":
    main()
