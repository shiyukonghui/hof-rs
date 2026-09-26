# -*- coding: utf-8 -*-
"""Grep every payload-index jsonl for a literal, printing file + count + a preview."""
import io
import json
import os
import sys

IDX = r"C:\Users\wyl\AppData\Local\Temp\mcp-recovery\staging\__payload-index"


def main():
    needle = sys.argv[1]
    filt = sys.argv[2] if len(sys.argv) > 2 else None
    for name in sorted(os.listdir(IDX)):
        if not name.endswith(".jsonl"):
            continue
        if filt and filt not in name:
            continue
        n = 0
        prev = []
        with io.open(os.path.join(IDX, name), "r", encoding="utf-8", errors="replace") as f:
            for line in f:
                if needle in line:
                    n += 1
                    if len(prev) < 3:
                        prev.append(line[:600])
        if n:
            print("### %s : %d hit(s)" % (name, n))
            for p in prev:
                print("    " + p.replace("\\n", " | ")[:600])


if __name__ == "__main__":
    main()
