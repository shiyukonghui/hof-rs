# -*- coding: utf-8 -*-
"""Find which recorded read window carries a symbol definition.

usage: python find_sym.py <subpath-substring> <symbol>
"""
import io
import json
import os
import sys

IDX = r"C:\Users\wyl\AppData\Local\Temp\mcp-recovery\staging\__payload-index"


def norm(p):
    return (p or "").replace("/", "\\").lower()


def main():
    sub, sym = sys.argv[1], sys.argv[2]
    p = os.path.join(IDX, "events-read.jsonl")
    hits = {}
    with io.open(p, encoding="utf-8", errors="replace") as f:
        for line in f:
            if sym not in line:
                continue
            r = json.loads(line)
            if sub and sub not in norm(r.get("path", "")):
                continue
            for no, txt in r.get("lines") or []:
                if sym in txt:
                    key = (r.get("totalLines"), r.get("time"), r.get("path"))
                    if key not in hits:
                        hits[key] = []
                    hits[key].append((no, txt.strip()))
    for (rev, t, path), v in sorted(hits.items(), key=lambda kv: str(kv[0][1])):
        print("rev=%s t=%s path=%s" % (rev, t, (path or "")[-60:]))
        for no, txt in v[:4]:
            print("   %5d| %s" % (no, txt[:150]))


if __name__ == "__main__":
    main()
