# -*- coding: utf-8 -*-
"""TASK-083: report the brace depth right after every top-level `}` so a lost or
extra brace can be located."""
import os
import sys

sys.path.insert(0, r"C:\Users\wyl\AppData\Local\Temp\mcp-recovery\work\task083")
import depth as D  # noqa: E402
import splice  # noqa: E402


def main():
    p = sys.argv[1]
    if not os.path.isabs(p):
        p = os.path.join(splice.TREE, p.replace("/", os.sep))
    L = splice.read_plain(p)
    d = D.depths(L)
    print("lines=%d final=%s" % (len(L), d[-1]))
    for i, (b, pa, st) in enumerate(d, 1):
        t = L[i - 1]
        if t.startswith("}") or t.startswith("namespace") or t.startswith("using ") or b < 0:
            print("  %5d brace=%-3d paren=%-3d state=%-6s | %s" % (i, b, pa, st or "", t[:90]))


if __name__ == "__main__":
    main()
