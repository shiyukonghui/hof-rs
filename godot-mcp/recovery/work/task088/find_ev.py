# -*- coding: utf-8 -*-
"""task088: search events-edit.jsonl for edits of one path whose old/new matches a needle.

usage: python find_ev.py <path-substring> <needle> [old|new|both] [outfile]
"""
from __future__ import print_function
import io, json, os, sys

IDX = r"C:\Users\wyl\AppData\Local\Temp\mcp-recovery\staging\__payload-index"


def main():
    psub = sys.argv[1]
    needle = sys.argv[2]
    where = sys.argv[3] if len(sys.argv) > 3 else "both"
    out = sys.argv[4] if len(sys.argv) > 4 else None
    rows = []
    with io.open(os.path.join(IDX, "events-edit.jsonl"), encoding="utf-8", errors="replace") as fh:
        for ln in fh:
            ln = ln.strip()
            if not ln:
                continue
            o = json.loads(ln)
            p = (o.get("path") or "").replace("/", "\\")
            if psub.lower() not in p.lower():
                continue
            o_t = o.get("old") or ""
            n_t = o.get("new") or ""
            hit = False
            if where in ("old", "both") and needle in o_t:
                hit = True
            if where in ("new", "both") and needle in n_t:
                hit = True
            if not hit:
                continue
            rows.append(o)
    lines = []
    for o in rows:
        lines.append("seq=%s time=%s path=%s old_bytes=%d new_bytes=%d old_lines=%d new_lines=%d" % (
            o.get("seq"), o.get("time"), o.get("path"),
            len((o.get("old") or "").encode("utf-8")), len((o.get("new") or "").encode("utf-8")),
            (o.get("old") or "").count("\n") + 1, (o.get("new") or "").count("\n") + 1))
    text = "\n".join(lines) + "\n"
    if out:
        io.open(out, "w", encoding="utf-8", newline="\n").write(text)
    print("matches=%d" % len(rows))
    for l in lines:
        print(l)


if __name__ == "__main__":
    main()
