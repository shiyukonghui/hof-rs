#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""TASK-103 scratch: list the capture pairs a run's traces recorded, and which of them changed."""
import io
import json
import os
import sys

for run in sys.argv[1:]:
    print("== %s" % run)
    for name in ("trace-editor.jsonl", "trace-game.jsonl"):
        path = os.path.join(run, name)
        if not os.path.isfile(path):
            print("   %s: ABSENT" % name)
            continue
        pairs = 0
        non_zero = 0
        for line in io.open(path, encoding="utf-8"):
            line = line.strip()
            if not line:
                continue
            try:
                record = json.loads(line)
            except ValueError:
                continue
            if record.get("event") != "capture":
                continue
            pairs += 1
            changed = record.get("changed_pixels")
            if changed:
                non_zero += 1
                print("   NONZERO %-4s %-42s changed=%s status=%s"
                      % (record.get("seq"), record.get("tool"), changed, record.get("status")))
        print("   %s: %d capture pair(s), %d non-zero" % (name, pairs, non_zero))
