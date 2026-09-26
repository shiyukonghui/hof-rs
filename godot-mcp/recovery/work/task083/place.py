# -*- coding: utf-8 -*-
"""TASK-083 recon 5: place read windows at their true line numbers, with
provenance, preferring the highest totalLines revision (then newest time)."""
import io
import json
import os
import sys

IDX = r"C:\Users\wyl\AppData\Local\Temp\mcp-recovery\staging\__payload-index"
OUT = r"C:\Users\wyl\AppData\Local\Temp\mcp-recovery\work\task083"


def norm(p):
    return p.replace("/", "\\").lower()


def main():
    sub = sys.argv[1]
    total = int(sys.argv[2])
    tag = sys.argv[3]
    rows = []
    with io.open(os.path.join(IDX, "events-read.jsonl"), "r", encoding="utf-8", errors="replace") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            try:
                r = json.loads(line)
            except Exception:
                continue
            if norm(sub) in norm(r.get("path", "")):
                rows.append(r)
    best = {}
    for r in rows:
        key = (r.get("totalLines") or 0, r.get("time", 0))
        for ln in (r.get("lines") or []):
            no, txt = ln[0], ln[1]
            if no > total:
                continue
            if no not in best or best[no][0] < key:
                best[no] = (key, txt, r.get("totalLines"), r.get("time"))
    miss = [i for i in range(1, total + 1) if i not in best]
    rng = []
    for m in miss:
        if rng and m == rng[-1][1] + 1:
            rng[-1][1] = m
        else:
            rng.append([m, m])
    # provenance of the covered lines, compressed
    prov = []
    for i in range(1, total + 1):
        if i in best:
            tl = best[i][2]
            if prov and prov[-1][2] == tl and prov[-1][1] == i - 1:
                prov[-1][1] = i
            else:
                prov.append([i, i, tl])
    print("rows=%d covered=%d missing=%d" % (len(rows), total - len(miss), len(miss)))
    print("missing ranges: %s" % rng)
    print("provenance (line ranges by source revision totalLines):")
    for a, b, tl in prov:
        print("   %4d-%-4d  <- rev%d" % (a, b, tl))
    with io.open(os.path.join(OUT, tag + ".placed.txt"), "w", encoding="utf-8", newline="\n") as f:
        for i in range(1, total + 1):
            t = best[i][1] if i in best else "@@MISSING@@"
            f.write("%5d| %s\n" % (i, t))
    print("written %s" % os.path.join(OUT, tag + ".placed.txt"))


if __name__ == "__main__":
    main()
