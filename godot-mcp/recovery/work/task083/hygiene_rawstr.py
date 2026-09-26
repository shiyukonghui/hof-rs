# -*- coding: utf-8 -*-
"""TASK-083 hygiene: over every module source, close a raw-string literal whose
line came back truncated from a read window.  Idempotent; read-only unless
--write."""
import io
import os
import re
import sys

sys.path.insert(0, r"C:\Users\wyl\AppData\Local\Temp\mcp-recovery\work\task083")
import splice  # noqa: E402

TREE = r"H:\rebuild\godot\modules\mcp_server"


def main():
    write = "--write" in sys.argv
    nfix = 0
    for root, dirs, files in os.walk(TREE):
        if "docs" in root.split(os.sep) or "tests" in root.split(os.sep):
            continue
        for fn in sorted(files):
            if not fn.endswith((".cpp", ".h")):
                continue
            p = os.path.join(root, fn)
            rel = os.path.relpath(p, TREE)
            L = splice.read_plain(p)
            changed = False
            for i, line in enumerate(L):
                m = re.search(r'R"([A-Za-z0-9_]*)\(', line)
                if not m:
                    continue
                delim = m.group(1)
                if (")" + delim + '"') in line[m.end():]:
                    continue
                body = line[:-1] if line.endswith(";") else line
                if body.endswith(')' + delim + '"'):
                    body = body + ")"
                elif body.endswith(")"):
                    body = body + delim + '"))'
                else:
                    print("  !! %-52s line %d unrepairable: %r" % (rel, i + 1, line[-50:]))
                    continue
                L[i] = body + ";"
                changed = True
                nfix += 1
                print("  fix %-52s line %d: %d -> %d bytes tail=%r" % (rel, i + 1, len(line), len(L[i]), L[i][-20:]))
            if changed and write:
                with io.open(p, "w", encoding="utf-8", newline="\n") as f:
                    f.write("\n".join(L) + "\n")
    print("raw-string holes repaired: %d%s" % (nfix, "" if write else " (dry run)"))


if __name__ == "__main__":
    main()
