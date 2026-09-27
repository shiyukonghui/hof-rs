# -*- coding: utf-8 -*-
"""TASK-139 recon: model call cost per run, from a recorded player.json / model.json."""
from __future__ import print_function

import io
import json
import os
import sys

ROOT = os.path.abspath(os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", ".."))


def main(argv):
    for rel in argv:
        p = os.path.join(ROOT, rel)
        if not os.path.isfile(p):
            print("MISSING %s" % p)
            continue
        s = json.load(io.open(p, encoding="utf-8"))
        print("%s" % rel)
        for k in ("verdict", "steps", "injected_steps", "accepted_steps",
                  "changed_steps_of_accepted", "accepted_and_changed_rate",
                  "progress_step_count", "match_seconds_in_game_clock"):
            print("   %s = %s" % (k, s.get(k)))
        print("   keys: %s" % sorted(s.keys()))
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
