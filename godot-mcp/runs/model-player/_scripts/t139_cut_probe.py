# -*- coding: utf-8 -*-
"""TASK-139: find the TRUE first ledger entry that belongs to this batch.

Prints the first entries that mention `t139_` (or carry `source == "t139-wrapper-call"`),
with their index, so the scanner's cut point can be checked against the real ledger instead of
being assumed.  It also prints the entry that immediately precedes it, which is what defines
"previous batch's last entry".

Usage (cmd):
    D:\\Anaconda\\python.exe runs\\model-player\\_scripts\\t139_cut_probe.py
"""
from __future__ import print_function

import io
import json
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
LEDGER = os.path.join(HERE, "t136_commands.jsonl")


def main(argv):
    entries = []
    for line in io.open(LEDGER, encoding="utf-8"):
        line = line.strip()
        if line:
            entries.append(json.loads(line))
    hits = []
    for i, e in enumerate(entries):
        joined = " ".join(str(a) for a in (e.get("argv") or []))
        if (e.get("source") or "") == "t139-wrapper-call" or "t139" in joined:
            hits.append((i, e))
    print("ledger lines: %d   entries naming t139: %d" % (len(entries), len(hits)))
    for i, e in hits[:8]:
        joined = " ".join(str(a) for a in (e.get("argv") or []))
        print("  idx=%d ts=%s source=%s" % (i, e.get("ts"), e.get("source")))
        print("     %s" % joined[:200])
    if hits:
        first = hits[0][0]
        print("FIRST t139 entry idx=%d; the entry before it:" % first)
        if first > 0:
            e = entries[first - 1]
            print("  idx=%d ts=%s source=%s %s" % (first - 1, e.get("ts"), e.get("source"),
                                                   " ".join(str(a) for a in
                                                            (e.get("argv") or []))[:200]))
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
