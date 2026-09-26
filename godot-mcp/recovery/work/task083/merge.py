# -*- coding: utf-8 -*-
"""TASK-083 recon 4: newest-wins merge of all read windows for one path."""
import io
import json
import os
import sys
from collections import defaultdict

IDX = r"C:\Users\wyl\AppData\Local\Temp\mcp-recovery\staging\__payload-index"
OUT = r"C:\Users\wyl\AppData\Local\Temp\mcp-recovery\work\task083"


def norm(p):
    return p.replace("/", "\\").lower()


def collect(target_sub, total_filter=None):
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
            p = norm(r.get("path", ""))
            if target_sub not in p:
                continue
            if total_filter is not None and r.get("totalLines") != total_filter:
                continue
            rows.append(r)
    return rows


def merge(rows, total):
    best = {}   # lineno -> (time, seq, text)
    for r in rows:
        t = r.get("time", 0)
        seq = r.get("seq", 0)
        for ln in (r.get("lines") or []):
            no, txt = ln[0], ln[1]
            key = (t, seq)
            if no not in best or best[no][0] <= t:
                best[no] = (t, seq, txt, r.get("f"))
    return best


def main():
    target = sys.argv[1] if len(sys.argv) > 1 else "modules\\mcp_server\\mcp_server.cpp"
    total = int(sys.argv[2]) if len(sys.argv) > 2 else 760
    rows = collect(target, total)
    print("rows with totalLines=%d: %d" % (total, len(rows)))
    best = merge(rows, total)
    lines = []
    missing = []
    for i in range(1, total + 1):
        if i in best:
            lines.append(best[i][2])
        else:
            lines.append("\t@@MISSING@@")
            missing.append(i)
    ranges = []
    for m in missing:
        if ranges and m == ranges[-1][1] + 1:
            ranges[-1][1] = m
        else:
            ranges.append([m, m])
    print("covered=%d missing=%d" % (total - len(missing), len(missing)))
    print("missing ranges: %s" % ranges)
    base = os.path.basename(target.replace("\\", "_"))
    with io.open(os.path.join(OUT, base + ".merged%d.txt" % total), "w", encoding="utf-8", newline="\n") as f:
        for i, t in enumerate(lines, 1):
            f.write("%5d| %s\n" % (i, t))
    print("written: %s" % os.path.join(OUT, base + ".merged%d.txt" % total))


if __name__ == "__main__":
    main()
