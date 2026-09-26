# -*- coding: utf-8 -*-
"""TASK-083: show 'namespace' lines in a file (work-dir name or tree path)."""
import os
import sys

sys.path.insert(0, r"C:\Users\wyl\AppData\Local\Temp\mcp-recovery\work\task083")
import splice  # noqa: E402


def main():
    for p in sys.argv[1:]:
        if not os.path.isabs(p):
            p = os.path.join(r"C:\Users\wyl\AppData\Local\Temp\mcp-recovery\work\task083", p)
        L = splice.read_plain(p)
        print("%s lines=%d" % (p, len(L)))
        for i, l in enumerate(L, 1):
            if "namespace" in l:
                print("  %5d| %s" % (i, l[:110]))


if __name__ == "__main__":
    main()
