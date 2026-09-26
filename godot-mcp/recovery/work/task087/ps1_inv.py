# -*- coding: utf-8 -*-
"""Inventory a candidate accept_m1.ps1: case names, functions, and header comment."""
from __future__ import print_function
import io, re, sys
sys.path.insert(0, r"C:\Users\wyl\AppData\Local\Temp\mcp-recovery\work\task087")
import rep


def main():
    p = sys.argv[1]
    if len(sys.argv) > 2:
        rep.set_report(sys.argv[2])
    L = io.open(p, encoding="utf-8", errors="replace").read().split("\n")
    rep.log("path=%s lines=%d bytes=%d" % (p, len(L), len(io.open(p, "rb").read())))
    rep.log("--- functions ---")
    for n, l in enumerate(L, 1):
        if re.match(r"^\s*function\s+\S+", l):
            rep.log("  %5d %s" % (n, l.strip()[:110]))
    rep.log("--- cases ---")
    for n, l in enumerate(L, 1):
        for m in re.finditer(r"Invoke-Case\s+'([^']+)'", l):
            rep.log("  %5d %s" % (n, m.group(1)))
    rep.log("--- headings / section comments ---")
    for n, l in enumerate(L, 1):
        if re.match(r"^\s*#\s*(---|\*\*|##)", l) or re.match(r"^\s*#  ", l):
            rep.log("  %5d %s" % (n, l.strip()[:130]))
    rep.log("--- tool name list ---")
    for n, l in enumerate(L, 1):
        if "$ToolNames" in l or "$EditorToolNames" in l or "$GameToolNames" in l:
            rep.log("  %5d %s" % (n, l.strip()[:130]))
    rep.flush()


if __name__ == "__main__":
    main()
