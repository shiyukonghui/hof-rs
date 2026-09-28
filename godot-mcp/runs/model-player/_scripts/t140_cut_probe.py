# -*- coding: utf-8 -*-
"""TASK-140 §2.1: PROVE the ledger cut independently of the scanner.

`t140_scan_redirects.py` cuts the shared append-only ledger at the first entry whose `source`
is `t140-wrapper-call` or whose argv names a `t140_*` script.  The TASK-139 batch learned that
a wrong cut silently changes the count, so this prints the first TASK-140 entry, the
TASK-139 entry before it, and both candidate cuts (by `source`, by argv substring).

Usage (through the ledger wrapper):
    t140_cmd.py --cwd F:\\moonbit-hof-rs\\godot-mcp -- <py> runs\\model-player\\_scripts\\t140_cut_probe.py
"""
from __future__ import print_function

import io
import json
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
LEDGER = os.path.join(HERE, "t136_commands.jsonl")


def main():
    entries = []
    with io.open(LEDGER, encoding="utf-8") as fh:
        for line in fh:
            line = line.strip()
            if line:
                entries.append(json.loads(line))
    print("ledger lines: %d" % len(entries))
    by_source = None
    by_argv = None
    for i, e in enumerate(entries):
        argv = " ".join(str(a) for a in (e.get("argv") or []))
        if by_source is None and e.get("source") == "t140-wrapper-call":
            by_source = i
        if by_argv is None and "t140" in argv:
            by_argv = i
    for name, i in (("by source", by_source), ("by argv substring", by_argv)):
        print("--- cut %s: idx=%s" % (name, i))
        if i is None:
            continue
        e = entries[i]
        print("    first : ts=%s source=%s argv=%s"
              % (e.get("ts"), e.get("source"),
                 " ".join(str(a) for a in (e.get("argv") or []))[:200]))
        if i > 0:
            p = entries[i - 1]
            print("    before: ts=%s source=%s argv=%s"
                  % (p.get("ts"), p.get("source"),
                     " ".join(str(a) for a in (p.get("argv") or []))[:200]))
        print("    this batch's commands from that index: %d" % (len(entries) - i))
    # the last TASK-139 entry, as a sanity cross-check
    last139 = None
    for i, e in enumerate(entries):
        argv = " ".join(str(a) for a in (e.get("argv") or []))
        if "t139" in argv or e.get("source") == "t139-wrapper-call":
            last139 = i
    print("last TASK-139 entry idx=%s (falls before the TASK-140 cut: %s)"
          % (last139, (last139 is not None and by_source is not None
                       and last139 < by_source)))
    return 0


if __name__ == "__main__":
    sys.exit(main())
