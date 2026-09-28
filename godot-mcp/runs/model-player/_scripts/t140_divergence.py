# -*- coding: utf-8 -*-
"""TASK-140 §1.A.2: print the UNSTABLE games' divergence points from a stability result.

Usage (through the ledger wrapper):
    t140_cmd.py --cwd F:\\moonbit-hof-rs\\godot-mcp -- <py> runs\\model-player\\_scripts\\t140_divergence.py model
"""
from __future__ import print_function

import io
import json
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))


def main(argv):
    arm = argv[0] if argv else "model"
    p = os.path.join(HERE, "t140_stability_%s.json" % arm)
    with io.open(p, encoding="utf-8") as fh:
        doc = json.load(fh)
    print("%s: UNSTABLE games = %s" % (arm, doc.get("unstable_games")))
    for row in doc["games"]:
        st = row["stability"]
        if not row["unstable"]:
            continue
        print("=" * 88)
        print("GAME %s  state=%s  why=%s" % (row["game"], st.get("state"), st.get("why")))
        print("  verdicts by round: %s" % st.get("verdicts_by_round"))
        print("  classes by round : %s" % st.get("classes_by_round"))
        print("  qualified        : %s" % st.get("qualified_verdicts_by_round"))
        print("  divergent rounds : %s   divergence points: %s"
              % (st.get("divergent_rounds"), st.get("divergence_point_count")))
        for pt in (st.get("divergence_points") or [])[:24]:
            print("   step %-3s %-14s round_a=%-8s round_b=%-8s ctx=%s"
                  % (pt.get("step"), pt.get("criterion"), pt.get("round_a"),
                     pt.get("round_b"), pt.get("context")))
        print("  per-round readings:")
        for r in row["readings"]:
            print("   %-22s class=%-22s counts=%-5s rate=%-8s refused=%-16s real=%s"
                  % (r["label"], r["class"], r["counts_as_pass"],
                     r["accepted_and_changed_rate"], r["refused_steps"],
                     r["real_progress_step_count"]))
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
