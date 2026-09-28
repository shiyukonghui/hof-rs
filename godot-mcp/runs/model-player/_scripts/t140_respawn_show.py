# -*- coding: utf-8 -*-
"""TASK-140 §1.B.1: print the respawn probe's per-sample series compactly.

Usage (through the ledger wrapper):
    t140_cmd.py --cwd F:\\moonbit-hof-rs\\godot-mcp -- <py> runs\\model-player\\_scripts\\t140_respawn_show.py
"""
from __future__ import print_function

import io
import json
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.abspath(os.path.join(HERE, "..", "..", ".."))
P = os.path.join(ROOT, "runs", "model-player", "t140-respawn-probe", "probe.json")


def main():
    with io.open(P, encoding="utf-8") as fh:
        doc = json.load(fh)
    print("what: %s" % doc["what"])
    print("settle: %s" % (doc.get("settle") or "")[:200])
    print("settle_frame: %s" % doc.get("settle_frame"))
    for c in doc["cases"]:
        print("=" * 90)
        print("CASE %s  setup=%s" % (c["tag"], c["setup"]))
        print("  before      : %s" % c["before"])
        print("  right after : %s" % c["right_after_put"])
        print("  %-4s %-7s %-9s %-9s %-9s %-6s %-7s %-6s %s"
              % ("i", "pxdiff", "alive", "lives", "respawns", "invuln", "vis", "timer",
                 "last_event"))
        for r in c["samples"]:
            s = r["state"]
            print("  %-4s %-7s %-9s %-9s %-9s %-6s %-7s %-6s %s"
                  % (r["i"], r["pixel_diff_vs_prev_frame"], s["ShipAlive"], s["Lives"],
                     s["Respawns"], s["InvulnTimer"], s["ShipVisible"], s["RespawnTimer"],
                     str(s["LastEvent"])[:60]))
    return 0


if __name__ == "__main__":
    sys.exit(main())
