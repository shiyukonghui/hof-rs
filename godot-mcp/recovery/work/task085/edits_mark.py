# -*- coding: utf-8 -*-
"""Show edits of one file that mention a marker, with their result.

usage: python edits_mark.py <subpath> <marker>
"""
import json
import os
import sys

IDX = r"C:\Users\wyl\AppData\Local\Temp\mcp-recovery\staging\__payload-index"


def norm(p):
    return (p or "").replace("/", "\\").lower()


def main():
    sub, marker = sys.argv[1], sys.argv[2]
    rows = []
    with open(os.path.join(IDX, "events-edit.jsonl"), encoding="utf-8", errors="replace") as f:
        for l in f:
            if not l.strip():
                continue
            r = json.loads(l)
            if sub in norm(r.get("path")):
                rows.append(r)
    rows.sort(key=lambda r: r.get("time", 0))
    print("%d edits for %s" % (len(rows), sub))
    for r in rows:
        blob = (r.get("old") or "") + (r.get("new") or "")
        if marker not in blob:
            continue
        ok = "FAIL" if (r.get("result") or "").lstrip().startswith("Error") else "OK"
        print("-- seq=%s t=%s %s old=%d new=%d" % (
            r.get("seq"), r.get("time"), ok,
            len((r.get("old") or "").split("\n")), len((r.get("new") or "").split("\n"))))
        if len(sys.argv) > 3:
            print("--- OLD ---\n%s" % (r.get("old") or ""))
            print("--- NEW ---\n%s" % (r.get("new") or ""))


if __name__ == "__main__":
    main()
