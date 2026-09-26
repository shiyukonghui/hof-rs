# -*- coding: utf-8 -*-
"""Dump every recorded edit/write event for one file, in time order, in full.

usage: python edits.py <subpath> [--full] [--after <time>]
"""
import io
import json
import os
import sys

IDX = r"C:\Users\wyl\AppData\Local\Temp\mcp-recovery\staging\__payload-index"


def norm(p):
    return (p or "").replace("/", "\\").lower()


def main():
    sub = norm(sys.argv[1])
    full = "--full" in sys.argv
    after = 0
    if "--after" in sys.argv:
        after = int(sys.argv[sys.argv.index("--after") + 1])
    rows = []
    for name in ("events-edit.jsonl", "events-write.jsonl"):
        with io.open(os.path.join(IDX, name), "r", encoding="utf-8", errors="replace") as f:
            for line in f:
                line = line.strip()
                if not line:
                    continue
                r = json.loads(line)
                if sub not in norm(r.get("path", "")):
                    continue
                if r.get("time", 0) < after:
                    continue
                r["_k"] = name
                rows.append(r)
    rows.sort(key=lambda r: r.get("time", 0))
    print("%d events (after t=%d)" % (len(rows), after))
    for r in rows:
        print("\n===== %s seq=%s time=%s kind=%s" % (r.get("_k"), r.get("seq"), r.get("time"),
                                                    "edit" if "old" in r else "write"))
        if "old" in r:
            print("--- OLD:\n%s" % r.get("old", "")[:4000])
            print("--- NEW:\n%s" % r.get("new", "")[:8000])
        else:
            c = r.get("content", "")
            print("--- CONTENT (%d chars):\n%s" % (len(c), c[:8000] if full else c[:1500]))


if __name__ == "__main__":
    main()
