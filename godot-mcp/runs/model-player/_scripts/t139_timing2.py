# -*- coding: utf-8 -*-
"""TASK-139 recon: per-game wall clock of a previous sweep's results json."""
from __future__ import print_function

import io
import json
import os
import sys

ROOT = os.path.abspath(os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", ".."))


def main(argv):
    rel = argv[0]
    p = os.path.join(ROOT, rel) if not os.path.isabs(rel) else rel
    data = json.load(io.open(p, encoding="utf-8"))
    rows = data if isinstance(data, list) else (data.get("results") or [])
    tot = 0.0
    for r in rows:
        g = r.get("game") or (r.get("summary") or {}).get("game")
        sec = r.get("seconds")
        tot += float(sec or 0)
        print("%-16s rc=%s %8.1fs  verdict=%s" % (g, r.get("rc"), float(sec or 0),
                                                  (r.get("summary") or {}).get("verdict")))
    print("TOTAL %.1f s = %.1f min over %d runs" % (tot, tot / 60.0, len(rows)))
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
