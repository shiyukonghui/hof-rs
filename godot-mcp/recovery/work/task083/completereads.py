# -*- coding: utf-8 -*-
"""TASK-083 tool 3: for every module source path, find the best *complete* read
window (offset 1, contiguous 1..totalLines) and report the highest revision that
has one.  A complete window at the final revision restores the file verbatim."""
import io
import json
import os
from collections import defaultdict

IDX = r"C:\Users\wyl\AppData\Local\Temp\mcp-recovery\staging\__payload-index"
TREE = r"H:\rebuild\godot\modules\mcp_server"
OUT = r"C:\Users\wyl\AppData\Local\Temp\mcp-recovery\work\task083"


def norm(p):
    return p.replace("/", "\\").lower()


def main():
    per = defaultdict(list)
    with io.open(os.path.join(IDX, "events-read.jsonl"), "r", encoding="utf-8", errors="replace") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            r = json.loads(line)
            p = norm(r.get("path", ""))
            if "modules\\mcp_server\\" not in p:
                continue
            rel = p.split("modules\\mcp_server\\", 1)[1]
            per[rel].append(r)

    lines = []
    complete_files = []
    for rel in sorted(per):
        if not rel.endswith((".cpp", ".h")):
            continue
        if rel.startswith("docs") or rel.startswith("tests"):
            continue
        rows = per[rel]
        by_rev = defaultdict(list)
        for r in rows:
            by_rev[r.get("totalLines")].append(r)
        best = None  # (rev, time, row)
        for rev, rs in by_rev.items():
            if not rev:
                continue
            for r in rs:
                lns = r.get("lines") or []
                nos = sorted(x[0] for x in lns)
                if nos and nos[0] == 1 and nos[-1] == rev and len(nos) == rev:
                    key = (rev, r.get("time", 0))
                    if best is None or key > best[0]:
                        best = (key, r)
        tp = os.path.join(TREE, rel.replace("/", os.sep))
        cur = None
        if os.path.exists(tp):
            with io.open(tp, "r", encoding="utf-8", errors="replace", newline="") as f:
                cur = sum(1 for _ in f)
        if best:
            (rev, t), r = best
            lines.append("%-58s COMPLETE rev%-5d time=%s current=%s f=%s" % (rel, rev, t, cur, r.get("f")))
            complete_files.append((rel, rev, t, r))
        else:
            maxrev = max([x for x in by_rev if x] or [0])
            lines.append("%-58s no-complete-read maxrev=%-5s current=%s" % (rel, maxrev, cur))
    with io.open(os.path.join(OUT, "complete-reads.txt"), "w", encoding="utf-8", newline="\n") as f:
        f.write("\n".join(lines) + "\n")
    with io.open(os.path.join(OUT, "complete-reads.json"), "w", encoding="utf-8", newline="\n") as f:
        f.write(json.dumps([{"rel": a, "rev": b, "time": c, "f": d.get("f"), "seq": d.get("seq")}
                            for a, b, c, d in complete_files], ensure_ascii=False, indent=1))
    print("source paths with any complete read: %d / %d" % (len(complete_files), len(lines)))
    for l in lines:
        print("  " + l)


if __name__ == "__main__":
    main()
