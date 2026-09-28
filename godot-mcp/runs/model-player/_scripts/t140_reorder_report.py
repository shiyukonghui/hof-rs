# -*- coding: utf-8 -*-
"""TASK-140: put the report's top-level sections back in order (0, A..J).

The report was assembled in several passes, so the `## ` sections ended up as
A, B, C, E, F, I, J, D, G, H.  This rewrites the same bytes in the intended order and
prints the resulting header list, so the reordering is auditable (no content is edited).

Usage (through the ledger wrapper):
    t140_cmd.py --cwd F:\\moonbit-hof-rs\\godot-mcp -- <py> runs\\model-player\\_scripts\\t140_reorder_report.py
"""
from __future__ import print_function

import io
import os
import re
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.abspath(os.path.join(HERE, "..", "..", ".."))
P = os.path.join(ROOT, "recovery", "reports", "TASK-140-REPORT.md")

ORDER = ["## 0.", "## A.", "## B.", "## C.", "## D.", "## E.", "## F.", "## G.", "## H.",
         "## I.", "## J."]


def key_of(header):
    for i, pref in enumerate(ORDER):
        if header.startswith(pref):
            return i
    return len(ORDER)


def main():
    with io.open(P, encoding="utf-8") as fh:
        text = fh.read()
    parts = re.split(r"(?m)^(## .*)$", text)
    head = parts[0]
    blocks = []
    for i in range(1, len(parts), 2):
        header = parts[i]
        body = parts[i + 1] if i + 1 < len(parts) else ""
        blocks.append((key_of(header), header, body))
    bad = [h for k, h, _b in blocks if k == len(ORDER)]
    blocks.sort(key=lambda b: b[0])
    out = head + "".join(h + b for _k, h, b in blocks)
    with io.open(P, "w", encoding="utf-8", newline="\n") as fh:
        fh.write(out)
    print("sections reordered: %d" % len(blocks))
    for k, h, b in blocks:
        print("  %2d  %-52s (%d chars)" % (k, h, len(b)))
    if bad:
        print("UNKNOWN SECTIONS (left in place): %s" % bad)
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
