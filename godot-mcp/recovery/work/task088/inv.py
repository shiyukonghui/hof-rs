# -*- coding: utf-8 -*-
"""task088: inventory every recorded event touching one path (all streams).

usage: python inv.py <path-substring> <outfile> [max_read_windows]
"""
from __future__ import print_function
import io, json, os, sys

IDX = r"C:\Users\wyl\AppData\Local\Temp\mcp-recovery\staging\__payload-index"
STREAMS = ["events-write.jsonl", "events-edit.jsonl", "events-read.jsonl",
           "events-diff.jsonl", "events-termfile.jsonl", "gen-runs.jsonl",
           "events-termdump.jsonl"]


def main():
    psub = sys.argv[1].lower()
    out = sys.argv[2]
    maxwin = int(sys.argv[3]) if len(sys.argv) > 3 else 400
    lines = []
    for s in STREAMS:
        path = os.path.join(IDX, s)
        if not os.path.exists(path):
            continue
        n = 0
        windows = 0
        with io.open(path, encoding="utf-8", errors="replace") as fh:
            for ln in fh:
                ln = ln.strip()
                if not ln:
                    continue
                if psub not in ln.lower():
                    continue
                try:
                    o = json.loads(ln)
                except Exception:
                    continue
                p = (o.get("path") or o.get("file") or "").replace("/", "\\").lower()
                if psub not in p:
                    continue
                n += 1
                if s == "events-read.jsonl":
                    windows += 1
                    if windows > maxwin:
                        continue
                keys = {}
                for k in ("seq", "time", "totalLines", "bytes", "size", "len", "call", "t"):
                    if k in o:
                        keys[k] = o[k]
                if "content" in o:
                    keys["content_bytes"] = len((o.get("content") or "").encode("utf-8"))
                if "new" in o:
                    keys["new_bytes"] = len((o.get("new") or "").encode("utf-8"))
                    keys["old_bytes"] = len((o.get("old") or "").encode("utf-8"))
                if "lines" in o:
                    keys["lines"] = len(o.get("lines") or [])
                keys["nbytes"] = len(ln.encode("utf-8"))
                lines.append("%-22s %s" % (s, json.dumps(keys, ensure_ascii=False, sort_keys=True)))
        lines.append("== %s : %d rows matching (read windows listed: %d)" % (s, n, windows))
    text = "\n".join(lines) + "\n"
    io.open(out, "w", encoding="utf-8", newline="\n").write(text)
    print("wrote %s (%d lines)" % (out, len(lines)))


if __name__ == "__main__":
    main()
