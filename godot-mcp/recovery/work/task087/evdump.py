# -*- coding: utf-8 -*-
"""Dump the recorded payloads (write content / edit old+new) that contain a needle.

usage: python evdump.py <needle> [--field content|new|old|any] [--limit N] [--report F]
"""
from __future__ import print_function
import io, json, os, sys
sys.path.insert(0, r"C:\Users\wyl\AppData\Local\Temp\mcp-recovery\work\task087")
import rep

IDX = r"C:\Users\wyl\AppData\Local\Temp\mcp-recovery\staging\__payload-index"
FILES = ["events-write.jsonl", "events-edit.jsonl"]


def main():
    needle = sys.argv[1]
    argv = sys.argv[2:]
    field = argv[argv.index("--field") + 1] if "--field" in argv else "any"
    limit = int(argv[argv.index("--limit") + 1]) if "--limit" in argv else 5
    if "--report" in argv:
        rep.set_report(argv[argv.index("--report") + 1])
    n = 0
    for fn in FILES:
        with io.open(os.path.join(IDX, fn), encoding="utf-8", errors="replace") as fh:
            for ln in fh:
                ln = ln.strip()
                if not ln:
                    continue
                try:
                    o = json.loads(ln)
                except Exception:
                    continue
                if needle not in json.dumps(o, ensure_ascii=False):
                    continue
                n += 1
                if n > limit and limit > 0:
                    return rep.flush()
                rep.log("=" * 100)
                rep.log("%s seq=%s t=%s path=%s result=%s"
                        % (fn, o.get("seq"), o.get("time"), o.get("path"), (o.get("result") or "")[:60]))
                for k in ("content", "new", "old"):
                    if field not in ("any", k):
                        continue
                    v = o.get(k)
                    if isinstance(v, str) and needle in v:
                        rep.log("--- %s (%d bytes, %d lines) ---" % (k, len(v.encode("utf-8")), v.count("\n") + 1))
                        rep.log(v)
    rep.flush()


if __name__ == "__main__":
    main()
