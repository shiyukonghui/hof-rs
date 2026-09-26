# -*- coding: utf-8 -*-
"""TASK-096 helper: validate a session file before it is replayed.

Caught a real class of bug before (TASK-095: sessions/probe10/session.json was
not valid JSON at all). Every session this task runs goes through this first.
"""
import json
import re
import sys
import io

def main(path):
    with io.open(path, "r", encoding="utf-8") as handle:
        doc = json.load(handle)
    calls = doc.get("calls") or []
    print("JSON OK  calls=%d  game=%s  import=%s" % (len(calls), doc.get("game"), doc.get("import")))
    tags = []
    for c in calls:
        if c.get("tag"):
            tags.append(c["tag"])
        code = ((c.get("arguments") or {}).get("code")) or ""
        m = re.search(r"board=([.#|]+)", code)
        if m:
            rows = m.group(1).split("|")
            print("  %-24s board rows=%d  widths=%s  last=%s"
                  % (c["tag"], len(rows), sorted(set(len(r) for r in rows)), rows[-1]))
    dupes = [t for t in set(tags) if tags.count(t) > 1]
    print("tags=%d  duplicates=%s" % (len(tags), dupes or "none"))
    return 0

if __name__ == "__main__":
    sys.exit(main(sys.argv[1]))
