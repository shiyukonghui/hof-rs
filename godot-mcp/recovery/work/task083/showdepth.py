# -*- coding: utf-8 -*-
"""TASK-083: print one file with the running brace/paren depth, so a dropped
'(' or ')' can be located by eye."""
import os
import sys

sys.path.insert(0, r"C:\Users\wyl\AppData\Local\Temp\mcp-recovery\work\task083")
import depth as D  # noqa: E402
import splice  # noqa: E402


def main():
    rel = sys.argv[1]
    a = int(sys.argv[2])
    b = int(sys.argv[3])
    p = os.path.join(splice.TREE, rel.replace("/", os.sep))
    L = splice.read_plain(p)
    d = D.depths(L)
    for i in range(a, min(b, len(L)) + 1):
        dc, dp, st = d[i - 1]
        print("%5d b%-3d p%-3d %-6s| %s" % (i, dc, dp, st or "", L[i - 1][:130]))


if __name__ == "__main__":
    main()
