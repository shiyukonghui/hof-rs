# -*- coding: utf-8 -*-
"""TASK-083: does any module source contain bytes that are not valid UTF-8?
(If so, the splice must not round-trip it through a decoded string.)"""
import io
import os
import sys

TREE = r"H:\rebuild\godot\modules\mcp_server"


def main():
    bad = []
    for root, dirs, files in os.walk(TREE):
        for fn in files:
            if not fn.endswith((".cpp", ".h", ".py", ".json", ".ps1")):
                continue
            p = os.path.join(root, fn)
            b = io.open(p, "rb").read()
            try:
                b.decode("utf-8")
            except UnicodeDecodeError as e:
                bad.append((os.path.relpath(p, TREE), str(e)))
    print("files with non-UTF-8 bytes: %d" % len(bad))
    for rel, e in bad:
        print("  %-60s %s" % (rel, e))


if __name__ == "__main__":
    main()
