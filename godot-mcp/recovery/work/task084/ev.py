# -*- coding: utf-8 -*-
"""Extract one recorded edit event's old/new text (or a whole file's edits) so a
gap can be filled with recorded text instead of a guess.

usage: python ev.py <subpath>                       -> list events (seq/time/lines)
       python ev.py <subpath> <seq>                 -> print OLD and NEW of that edit
       python ev.py <subpath> <seq> new > out.txt   -> print only NEW
"""
import io
import json
import os
import sys

IDX = r"C:\Users\wyl\AppData\Local\Temp\mcp-recovery\staging\__payload-index"


def norm(p):
    return (p or "").replace("/", "\\").lower()


def load(sub, which="events-edit.jsonl"):
    rows = []
    p = os.path.join(IDX, which)
    with io.open(p, "r", encoding="utf-8", errors="replace") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            r = json.loads(line)
            if sub not in norm(r.get("path", "")):
                continue
            rows.append(r)
    return rows


def main():
    sub = sys.argv[1]
    rows = load(sub)
    if len(sys.argv) == 2:
        rows.sort(key=lambda r: r.get("time", 0))
        print("%d edits" % len(rows))
        for r in rows:
            o = len((r.get("old") or "").split("\n"))
            n = len((r.get("new") or "").split("\n"))
            first = (r.get("old") or "").split("\n")[0][:90]
            print("seq=%-6s t=%-14s old=%-4d new=%-4d  %s" % (r.get("seq"), r.get("time"), o, n, first))
        return
    seq = int(sys.argv[2])
    what = sys.argv[3] if len(sys.argv) > 3 else "both"
    for r in rows:
        if str(r.get("seq")) != str(seq):
            continue
        if what in ("both", "old"):
            sys.stdout.write("--- OLD ---\n" + (r.get("old") or "") + "\n")
        if what in ("both", "new"):
            sys.stdout.write("--- NEW ---\n" + (r.get("new") or "") + "\n")
        return
    raise SystemExit("seq %s not found" % seq)


if __name__ == "__main__":
    main()
