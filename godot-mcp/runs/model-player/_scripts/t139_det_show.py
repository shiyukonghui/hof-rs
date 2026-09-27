# -*- coding: utf-8 -*-
"""TASK-139: print the verdicts and rc of one determinism probe result file."""
from __future__ import print_function

import io
import json
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))


def main(argv):
    for name in argv:
        p = os.path.join(HERE, name)
        if not os.path.isfile(p):
            print("MISSING %s" % p)
            continue
        d = json.load(io.open(p, encoding="utf-8"))
        print("== %s  arm=%s window=%s repeats=%s all_rc_zero=%s all_stable=%s"
              % (name, d.get("arm"), d.get("window"), d.get("repeats"),
                 d.get("all_rc_zero"), d.get("all_verdicts_stable")))
        for c in d.get("comparison") or []:
            print("   %-14s verdicts=%-46s rc=%s stable=%s step_diffs=%s"
                  % (c.get("game"), json.dumps(c.get("verdicts"), ensure_ascii=False),
                     c.get("rc_by_repeat"), c.get("verdict_stable"),
                     c.get("step_difference_count")))
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
