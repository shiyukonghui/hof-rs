# -*- coding: utf-8 -*-
"""TASK-083: scan module sources for U+FFFD (a sign that a round-trip through a
decoded string destroyed bytes)."""
import io
import os

TREE = r"H:\rebuild\godot\modules\mcp_server"
BAD = chr(0xFFFD)


def main():
    hits = []
    for root, dirs, files in os.walk(TREE):
        for fn in files:
            if not fn.endswith((".cpp", ".h")):
                continue
            p = os.path.join(root, fn)
            s = io.open(p, encoding="utf-8", errors="replace").read()
            if BAD in s:
                hits.append((os.path.relpath(p, TREE), s.count(BAD)))
    print("files containing U+FFFD: %d" % len(hits))
    for rel, n in hits:
        print("  %-60s %d" % (rel, n))


if __name__ == "__main__":
    main()
