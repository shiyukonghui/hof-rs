# -*- coding: utf-8 -*-
"""TASK-083: inspect one module source file (balance, raw strings, tail)."""
import io
import os
import sys

sys.path.insert(0, r"C:\Users\wyl\AppData\Local\Temp\mcp-recovery\work\task083")
import splice  # noqa: E402


def main():
    rel = sys.argv[1]
    ntail = int(sys.argv[2]) if len(sys.argv) > 2 else 20
    p = os.path.join(splice.TREE, rel.replace("/", os.sep))
    L = splice.read_plain(p)
    print("file=%s lines=%d balance=%s" % (p, len(L), splice.balance(L)))
    print("--- lines containing R\" or unbalanced quotes ---")
    for i, l in enumerate(L, 1):
        if 'R"' in l:
            print("%5d| %s" % (i, l[:160]))
    print("--- tail %d ---" % ntail)
    for i in range(max(1, len(L) - ntail + 1), len(L) + 1):
        print("%5d| %s" % (i, L[i - 1][:160]))


if __name__ == "__main__":
    main()
