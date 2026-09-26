# -*- coding: utf-8 -*-
"""TASK-083 tool 4: cross-reference the reconstruction target revision with the
best complete read, and list which damaged files can be restored verbatim."""
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
            per[p.split("modules\\mcp_server\\", 1)[1]].append(r)
    recs = {}
    with io.open(os.path.join(IDX, "reconstruction.jsonl"), "r", encoding="utf-8", errors="replace") as f:
        for line in f:
            line = line.strip()
            if line:
                r = json.loads(line)
                if r.get("rel", "").startswith("modules\\mcp_server\\"):
                    recs[r["rel"].split("modules\\mcp_server\\", 1)[1]] = r

    out = []
    for rel in sorted(recs):
        if not rel.endswith((".cpp", ".h")) or rel.startswith(("docs", "tests")):
            continue
        rec = recs[rel]
        target = rec.get("read_total") or 0
        comp = None
        for r in per.get(rel, []):
            lns = r.get("lines") or []
            nos = sorted(x[0] for x in lns)
            rev = r.get("totalLines") or 0
            if nos and nos[0] == 1 and nos[-1] == rev and len(nos) == rev:
                key = (rev, r.get("time", 0))
                if comp is None or key > comp[0]:
                    comp = (key, r)
        tp = os.path.join(TREE, rel.replace("/", os.sep))
        cur = 0
        if os.path.exists(tp):
            with io.open(tp, "r", encoding="utf-8", errors="replace", newline="") as f:
                cur = sum(1 for _ in f)
        miss = rec.get("read_missing_n") or 0
        comprev = comp[0][0] if comp else 0
        verdict = "OK" if (comp and comprev == target) else ("PARTIAL" if comp else "none")
        out.append("%-52s target=%-5d bestComplete=%-5d cur=%-5d missing=%-5d %s" % (
            rel, target, comprev, cur, miss, verdict))
    with io.open(os.path.join(OUT, "target-vs-complete.txt"), "w", encoding="utf-8", newline="\n") as f:
        f.write("\n".join(out) + "\n")
    for l in out:
        print(l)


if __name__ == "__main__":
    main()
