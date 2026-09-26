# -*- coding: utf-8 -*-
"""task088: dump recorded edit rows. seq is NOT unique across session files, so
select by (seq, path-substring, optional time).

usage: python ev.py <seq> <path-substring> <time|-> <outfile> [old|new|both]
"""
from __future__ import print_function
import io, json, os, sys

IDX = r"C:\Users\wyl\AppData\Local\Temp\mcp-recovery\staging\__payload-index"


def rows_for(seq, psub):
    out = []
    with io.open(os.path.join(IDX, "events-edit.jsonl"), encoding="utf-8", errors="replace") as fh:
        for ln in fh:
            ln = ln.strip()
            if not ln:
                continue
            o = json.loads(ln)
            if str(o.get("seq")) != str(seq):
                continue
            p = (o.get("path") or "").replace("/", "\\")
            if psub.lower() not in p.lower():
                continue
            out.append(o)
    return out


def main():
    seq = sys.argv[1]
    psub = sys.argv[2]
    want_time = sys.argv[3]
    out = sys.argv[4]
    field = sys.argv[5] if len(sys.argv) > 5 else "both"
    cands = rows_for(seq, psub)
    info = []
    for o in cands:
        info.append("time=%s old=%dB new=%dB f=%s" % (
            o.get("time"),
            len((o.get("old") or "").encode("utf-8")),
            len((o.get("new") or "").encode("utf-8")),
            o.get("f")))
    print("candidates seq=%s path~%s : %d" % (seq, psub, len(cands)))
    for i in info:
        print("  " + i)
    if want_time not in ("-", ""):
        cands = [o for o in cands if str(o.get("time")) == str(want_time)]
    if not cands:
        raise SystemExit("no candidate selected")
    if len(cands) > 1:
        raise SystemExit("ambiguous: %d candidates after time filter" % len(cands))
    hit = cands[0]
    buf = []
    for k in sorted(hit.keys()):
        if k in ("old", "new"):
            continue
        v = hit[k]
        if isinstance(v, (dict, list)):
            v = json.dumps(v, ensure_ascii=False)
        buf.append("%s=%s" % (k, v))
    buf.append("")
    parts = []
    if field in ("old", "both"):
        parts.append("old")
    if field in ("new", "both"):
        parts.append("new")
    for p in parts:
        t = hit.get(p) or ""
        buf.append("========== %s : %d bytes, %d lines ==========" % (p, len(t.encode("utf-8")), t.count("\n") + 1))
        buf.append(t)
        buf.append("")
    data = "\n".join(buf)
    io.open(out, "w", encoding="utf-8", newline="\n").write(data)
    print("wrote %s (%d bytes)" % (out, len(data.encode("utf-8"))))


if __name__ == "__main__":
    main()
