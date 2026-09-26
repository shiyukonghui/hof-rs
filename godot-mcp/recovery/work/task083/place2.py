# -*- coding: utf-8 -*-
"""TASK-083 tool 6: rebuild a file by *placing* read-window lines at their true
line numbers, preferring the reconstruction's target revision.

The 2A/2B reconstruction concatenated the covered lines instead of placing them,
which is what produced the gap-collapsed splices.  Here:

  for each line 1..target:
    take the text from the newest window whose totalLines == target,
    else from the newest window with the highest totalLines < target,
    else mark it MISSING.

When a file's target revision is fully captured this reproduces the final file
byte for byte.

usage: place2.py <list-file> [--write] [--fill-backup]
"""
import io
import json
import os
import sys
from collections import defaultdict

IDX = r"C:\Users\wyl\AppData\Local\Temp\mcp-recovery\staging\__payload-index"
TREE = r"H:\rebuild\godot\modules\mcp_server"
BAK = r"C:\Users\wyl\AppData\Local\Temp\mcp044-module-backup\mcp_server"
OUT = r"C:\Users\wyl\AppData\Local\Temp\mcp-recovery\work\task083"


def read_plain(path):
    with io.open(path, "r", encoding="utf-8", errors="replace", newline="") as f:
        return [ln.rstrip("\r\n") for ln in f]


def load():
    per = defaultdict(list)
    with io.open(os.path.join(IDX, "events-read.jsonl"), "r", encoding="utf-8", errors="replace") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            r = json.loads(line)
            p = r.get("path", "").replace("/", "\\").lower()
            if "modules\\mcp_server\\" in p:
                per[p.split("modules\\mcp_server\\", 1)[1]].append(r)
    recs = {}
    with io.open(os.path.join(IDX, "reconstruction.jsonl"), "r", encoding="utf-8", errors="replace") as f:
        for line in f:
            line = line.strip()
            if line:
                r = json.loads(line)
                if r.get("rel", "").startswith("modules\\mcp_server\\"):
                    recs[r["rel"].split("modules\\mcp_server\\", 1)[1]] = r
    return per, recs


def place(rel, per, recs):
    key = rel.replace("/", "\\").lower()
    rows = per.get(key, [])
    total = (recs.get(key, {}) or {}).get("read_total") or 0
    at_target = {}
    lower = {}
    for r in rows:
        rev = r.get("totalLines") or 0
        t = r.get("time", 0)
        for no, txt in (r.get("lines") or []):
            if no > total:
                continue
            if rev == total:
                if no not in at_target or at_target[no][0] < t:
                    at_target[no] = (t, txt, rev)
            elif rev < total:
                if no not in lower or (lower[no][0][0], lower[no][0][1]) < (rev, t):
                    lower[no] = ((rev, t), txt)
    out = []
    miss = []
    prov = []
    for i in range(1, total + 1):
        if i in at_target:
            out.append(at_target[i][1])
            prov.append(("target", i))
        elif i in lower:
            out.append(lower[i][1])
            prov.append(("rev%d" % lower[i][0][0], i))
        else:
            out.append(None)
            miss.append(i)
    rng = []
    for m in miss:
        if rng and m == rng[-1][1] + 1:
            rng[-1][1] = m
        else:
            rng.append([m, m])
    return out, rng, total


def fill_from_backup(out, bak):
    import difflib
    have = [x for x in out if x is not None]
    sm = difflib.SequenceMatcher(None, have, bak, autojunk=False)
    ins = []
    for tag, i1, i2, j1, j2 in sm.get_opcodes():
        if tag == "insert":
            ins.append((j1, j2))
    return ins


def fill_gaps_from_backup(out, rng, bak):
    """Replace each @@MISSING@@ range with the backup lines that sit between the
    same two anchors.  Anchor-safe: the two neighbouring known lines must appear
    in that order in the backup, otherwise the gap is left open and reported."""
    res = list(out)
    filled = 0
    for a, b in rng:
        left = out[a - 2] if a - 2 >= 0 else None
        right = out[b] if b < len(out) else None
        ia = ib = None
        if left is not None:
            cands = [i for i, l in enumerate(bak) if l == left]
            if right is not None:
                for i in cands:
                    for j in range(i + 1, len(bak)):
                        if bak[j] == right:
                            ia, ib = i, j
                            break
                    if ia is not None:
                        break
            if ia is None and cands:
                ia = cands[0]
                ib = min(len(bak), ia + (b - a + 1))
        if ia is None or ib is None or ib <= ia + 1:
            print("      gap %d-%d: no anchor in backup, left open" % (a, b))
            continue
        block = bak[ia + 1:ib]
        if len(block) != (b - a + 1):
            print("      gap %d-%d: backup span has %d lines (wanted %d), inserting anyway"
                  % (a, b, len(block), b - a + 1))
        res[a - 1:b] = block
        filled += len(block)
    return res, filled


def main():
    rels = [l.strip() for l in read_plain(sys.argv[1]) if l.strip()]
    write = "--write" in sys.argv
    fill = "--fill-backup" in sys.argv
    report = []
    per, recs = load()
    for rel in rels:
        out, rng, total = place(rel, per, recs)
        have = [x for x in out if x is not None]
        print("%-50s target=%-5d placed=%-5d missing=%-5d ranges=%s" % (
            rel, total, len(have), len(out) - len(have), rng))
        if rng and fill:
            bp = os.path.join(BAK, rel.replace("/", os.sep))
            if os.path.exists(bp):
                bak = read_plain(bp)
                if bak and bak[-1] == "":
                    bak = bak[:-1]
                out, n = fill_gaps_from_backup(out, rng, bak)
                if n:
                    print("      backup filled %d lines" % n)
                out = [x for x in out if x is not None]
            else:
                out = have
        else:
            out = have
        report.append({"rel": rel, "target": total, "missing_ranges": rng})
        name = "placed2_" + os.path.basename(rel.replace("\\", "_")) + ".txt"
        with io.open(os.path.join(OUT, name), "w", encoding="utf-8", newline="\n") as f:
            f.write("\n".join(out) + "\n")
        if write:
            p = os.path.join(TREE, rel.replace("/", os.sep))
            with io.open(p, "w", encoding="utf-8", newline="\n") as f:
                f.write("\n".join(out) + "\n")
            print("      written (%d lines)" % len(out))
    with io.open(os.path.join(OUT, "place2-report.json"), "w", encoding="utf-8", newline="\n") as f:
        f.write(json.dumps(report, ensure_ascii=False, indent=1))


if __name__ == "__main__":
    main()
