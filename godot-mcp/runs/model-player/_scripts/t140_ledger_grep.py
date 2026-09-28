# -*- coding: utf-8 -*-
"""TASK-140 §2.1 helper: search the shared command ledger for a substring.

Usage (through the ledger wrapper):
    t140_cmd.py --cwd F:\\moonbit-hof-rs\\godot-mcp -- <py> runs\\model-player\\_scripts\\t140_ledger_grep.py <substr> [--limit N] [--full]
"""
from __future__ import print_function

import io
import json
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
LEDGER = os.path.join(HERE, "t136_commands.jsonl")


def main(argv):
    needle = argv[0]
    limit = 8
    if "--limit" in argv:
        limit = int(argv[argv.index("--limit") + 1])
    full = "--full" in argv
    rows = []
    with io.open(LEDGER, encoding="utf-8") as fh:
        for line in fh:
            line = line.strip()
            if not line:
                continue
            try:
                e = json.loads(line)
            except Exception:  # noqa: BLE001
                continue
            rows.append(e)
    hits = [e for e in rows if needle in " ".join(str(a) for a in (e.get("argv") or []))]
    print("ledger lines: %d   hits for %r: %d" % (len(rows), needle, len(hits)))
    for e in hits[-limit:]:
        a = " ".join(str(x) for x in (e.get("argv") or []))
        print("[%s] (%s) %s" % (e.get("ts"), e.get("source"), a if full else a[:300]))
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
