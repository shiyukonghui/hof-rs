# -*- coding: utf-8 -*-
"""TASK-139 debug: why does the loop say FAIL where the gate says PASS for the mixed run?"""
from __future__ import print_function

import io
import json
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.abspath(os.path.join(HERE, "..", "..", ".."))
sys.path.insert(0, os.path.join(ROOT, "tools"))
sys.path.insert(0, os.path.join(ROOT, "tools", "tests"))

from playtest_player import summarise  # noqa: E402
from test_playability_model_player import clean_run, refusal_step, step  # noqa: E402


def main(argv):
    mixed = []
    for i in range(1, 9):
        if i % 2 == 0:
            mixed.append(refusal_step(i, "swap", changed=False))
        else:
            mixed.append(step(i, "move%d" % i, "frame%d" % i, changed=True))
    s = summarise(mixed, "jev", "match3")
    for k in ("verdict", "why", "strict_verdict", "baseline_verdict", "counts_as_pass",
              "fail_steps", "fail_steps_before_refusal_carve_out", "refused_steps",
              "rated_step_count", "real_progress_step_count", "refusal_only_run",
              "MODEL_FIXED_POINT", "distinct_actions", "one_action_loop",
              "fail_evidence"):
        print("%-22s = %s" % (k, json.dumps(s.get(k), ensure_ascii=False)[:400]))
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
