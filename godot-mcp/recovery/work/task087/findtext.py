# -*- coding: utf-8 -*-
"""Find recorded payloads whose TEXT contains an exact source snippet."""
from __future__ import print_function
import io, json, os, sys
sys.path.insert(0, r"C:\Users\wyl\AppData\Local\Temp\mcp-recovery\work\task087")
import rep

IDX = r"C:\Users\wyl\AppData\Local\Temp\mcp-recovery\staging\__payload-index"


def main():
    needles = sys.argv[1:]
    if "--report" in needles:
        rep.set_report(needles[needles.index("--report") + 1])
        needles = [n for n in needles if n != "--report" and n != rep._PATH]
    for fn in ("events-write.jsonl", "events-edit.jsonl"):
        p = os.path.join(IDX, fn)
        with io.open(p, encoding="utf-8", errors="replace") as fh:
            for ln in fh:
                ln = ln.strip()
                if not ln:
                    continue
                try:
                    o = json.loads(ln)
                except Exception:
                    continue
                for k in ("content", "new", "old"):
                    v = o.get(k)
                    if not isinstance(v, str):
                        continue
                    for nd in needles:
                        if nd in v:
                            rep.log("%-20s seq=%-6s t=%-14s field=%-8s bytes=%-8d path=%s"
                                    % (fn, o.get("seq"), o.get("time"), k,
                                       len(v.encode("utf-8")), (o.get("path") or "")[-60:]))
    rep.flush()


if __name__ == "__main__":
    main()
