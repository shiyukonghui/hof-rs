# -*- coding: utf-8 -*-
"""task088: reconstruct one recorded file at an exact revision skeleton.

Only read windows whose `totalLines == SK` are used, so the merge is within one
revision.  Newest text per line number wins; conflicts are reported.

usage: python recon_sk.py <abs-path> <SK> <outfile> [--replay-edits]
"""
from __future__ import print_function
import io, json, os, sys

IDX = r"C:\Users\wyl\AppData\Local\Temp\mcp-recovery\staging\__payload-index"


def norm(p):
    return (p or "").replace("/", "\\").lower()


def line_text(el):
    if isinstance(el, (list, tuple)):
        if len(el) >= 2:
            return el[1] if isinstance(el[1], str) else str(el[1])
        return str(el[0]) if el else ""
    if isinstance(el, str):
        for sep in ("\t", ": ", "\t "):
            i = el.find(sep)
            if i > 0 and el[:i].strip().isdigit():
                return el[i + len(sep):]
        return el
    return str(el)


def main():
    target = norm(sys.argv[1])
    sk = int(sys.argv[2])
    out = sys.argv[3]
    replay = "--replay-edits" in sys.argv
    rows = []
    with io.open(os.path.join(IDX, "events-read.jsonl"), encoding="utf-8", errors="replace") as fh:
        for ln in fh:
            ln = ln.strip()
            if not ln:
                continue
            try:
                o = json.loads(ln)
            except Exception:
                continue
            if norm(o.get("path")) != target:
                continue
            if (o.get("totalLines") or 0) != sk:
                continue
            rows.append(o)
    variants = {}
    chosen = {}
    chosen_key = {}
    for r in sorted(rows, key=lambda x: (x.get("time", 0), x.get("seq") or 0)):
        off = r.get("offset") or 1
        key = (r.get("time", 0), r.get("seq") or 0)
        for i, raw in enumerate(r.get("lines") or []):
            n = off + i
            txt = line_text(raw)
            variants.setdefault(n, {})
            variants[n][txt] = variants[n].get(txt, 0) + 1
            if n not in chosen_key or key >= chosen_key[n]:
                chosen[n] = txt
                chosen_key[n] = key
    total = max(chosen) if chosen else 0
    holes = [n for n in range(1, sk + 1) if n not in chosen]
    multi = [n for n in sorted(chosen) if len(variants[n]) > 1]
    buf = "\n".join(chosen.get(n, "") for n in range(1, total + 1))
    if not buf.endswith("\n"):
        buf += "\n"
    print("skeleton=%d rows=%d lines=%d holes=%d conflicts=%d bytes=%d"
          % (sk, len(rows), total, len(holes), len(multi), len(buf.encode("utf-8"))))
    if multi:
        print("first conflicts: %s" % multi[:20])
    if replay:
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
                if norm(o.get("path")) != target:
                    continue
                if (o.get("result") or "").lstrip().startswith("Error"):
                    continue
                edits.append(o)
        newest = max((r.get("time", 0) for r in rows), default=0)
        n = 0
        for e in sorted(edits, key=lambda x: (x.get("time", 0), x.get("seq") or 0)):
            old = e.get("old") or ""
            new = e.get("new") or ""
            if not old:
                continue
            c = buf.count(old)
            if c == 1:
                buf = buf.replace(old, new, 1)
                n += 1
        print("replayed %d exact edits (of %d after newest window t=%s); bytes=%d"
              % (n, len(edits), newest, len(buf.encode("utf-8"))))
    io.open(out, "w", encoding="utf-8", newline="\n").write(buf)
    print("wrote %s" % out)


if __name__ == "__main__":
    main()
