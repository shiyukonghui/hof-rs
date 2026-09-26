# -*- coding: utf-8 -*-
"""TASK-102: look up one call's ledger verdict by matching the trace's own order.

    python trace_lookup.py <run-dir> <tool> <n-th>       (1-based)

Prints the capture/verdict records for the n-th call of that tool, so a session
item can be tied to the verdict the ledger gave it without trusting report.json.
"""
import io
import json
import os
import sys


def main():
    run, tool, nth = sys.argv[1], sys.argv[2], int(sys.argv[3])
    path = os.path.join(run, "trace-game.jsonl")
    count = 0
    for line in io.open(path, encoding="utf-8", errors="replace"):
        line = line.strip()
        if not line:
            continue
        try:
            rec = json.loads(line)
        except ValueError:
            continue
        if rec.get("event") != "capture" or rec.get("tool") != tool:
            continue
        count += 1
        if count == nth:
            print(json.dumps({k: rec.get(k) for k in
                              ("seq", "tool", "status", "changed", "changed_pixels",
                               "before", "after")}, ensure_ascii=False, indent=1))
            return 0
    print("only %d records for %s" % (count, tool))
    return 1


if __name__ == "__main__":
    sys.exit(main())
