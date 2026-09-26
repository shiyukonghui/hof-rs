# -*- coding: utf-8 -*-
"""Pretty-print a ps1_parse.ps1 JSON result."""
from __future__ import print_function
import io, json, sys
sys.path.insert(0, r"C:\Users\wyl\AppData\Local\Temp\mcp-recovery\work\task087")
import rep


def main():
    p = sys.argv[1]
    if len(sys.argv) > 2:
        rep.set_report(sys.argv[2])
    o = json.load(io.open(p, encoding="utf-8-sig"))
    rep.log("path=%s bytes=%s lines=%s errors=%s"
            % (o.get("path"), o.get("bytes"), o.get("lines"), o.get("errorCount")))
    for e in o.get("errors") or []:
        rep.log("  L%-5s C%-4s %-18s %s" % (e.get("line"), e.get("col"), e.get("errorId"), e.get("message")))
        rep.log("        text=%r" % (e.get("text"),))
    rep.flush()


if __name__ == "__main__":
    main()
