# -*- coding: utf-8 -*-
"""TASK-140: print one run's per-step actions / acks / change numbers (evidence reader).

Usage (through the ledger wrapper):
    t140_cmd.py --cwd F:\\moonbit-hof-rs\\godot-mcp -- <py> runs\\model-player\\_scripts\\t140_steps.py <player.json or run dir> [n]
"""
from __future__ import print_function

import io
import json
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.abspath(os.path.join(HERE, "..", "..", ".."))


def main(argv):
    p = argv[0]
    if os.path.isdir(p):
        p = os.path.join(p, "steps.jsonl")
    n = int(argv[1]) if len(argv) > 1 else 40
    with io.open(p, encoding="utf-8") as fh:
        recs = [json.loads(line) for line in fh if line.strip()]
    print("run: %s   steps: %d" % (os.path.abspath(p), len(recs)))
    for r in recs[:n]:
        ack = r.get("ack") or {}
        ch = r.get("change") or {}
        st = ch.get("strict") if isinstance(ch.get("strict"), dict) else {}
        wb = r.get("frame_budget") or {}
        cb = (r.get("control_diff") or {}).get("frame_budget") or {}
        sd = r.get("state_delta") or []
        keys = ",".join(str(d.get("key")) for d in sd[:6])
        print("step %2s action=%-16s injected=%s accepted=%s ack_missing=%s verdict=%-34s "
              "px=%-6s ctl_px=%-6s mv=%-9s cmv=%-9s strict=%-5s frames=%s/%s keys=[%s]"
              % (r.get("step"), (r.get("action") or {}).get("action"), ack.get("injected"),
                 ack.get("accepted"), ack.get("ack_missing"), r.get("step_verdict"),
                 ch.get("pixel_diff"), ch.get("control_pixels"),
                 ch.get("gameplay_movement"), ch.get("control_movement"),
                 st.get("changed"), cb.get("achieved_delta"), wb.get("action_frames"), keys))
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
