# -*- coding: utf-8 -*-
"""Search every read window of a file for lines matching a regex."""
import io
import json
import os
import re
import sys

IDX = r"C:\Users\wyl\AppData\Local\Temp\mcp-recovery\staging\__payload-index"


def norm(p):
    return p.replace("/", "\\").lower()


def main():
    sub = norm(sys.argv[1])
    rx = re.compile(sys.argv[2])
    seen = {}
    with io.open(os.path.join(IDX, "events-read.jsonl"), "r", encoding="utf-8", errors="replace") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            r = json.loads(line)
            if sub not in norm(r.get("path", "")):
                continue
            for no, txt in (r.get("lines") or []):
                if rx.search(txt):
                    key = (txt,)
                    seen.setdefault(key, []).append((r.get("totalLines"), no, r.get("time")))
    for (txt,), hits in sorted(seen.items(), key=lambda kv: -len(kv[1])):
        revs = ",".join("rev%s:%s" % (h[0], h[1]) for h in hits[:6])
        print("%3dx  %-70s  %s" % (len(hits), txt[:70], revs))


if __name__ == "__main__":
    main()
