# -*- coding: utf-8 -*-
"""TASK-140 §1.A.3: exercise the GATE-side criterion on a recorded run (no engine, no network).

Reads `<run>/player.json` and `<run>/steps.jsonl`, calls
`playability_gate.evaluate_model_player_steps(..., run_context=...)` exactly the way
`record_model_player_criterion` does, and prints the fields Y3 cares about (attribution) and
Y1 cares about (reporting window).

Usage (through the ledger wrapper):
    t140_cmd.py --cwd F:\\moonbit-hof-rs\\godot-mcp -- <py> runs\\model-player\\_scripts\\t140_gate_check.py \\
        runs\\model-player\\t140-scripted-w90-r1\\asteroids\\scripted
"""
from __future__ import print_function

import io
import json
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.abspath(os.path.join(HERE, "..", "..", ".."))
sys.path.insert(0, os.path.join(ROOT, "tools"))

from playability_gate import evaluate_model_player_steps  # noqa: E402
from playtest_player import nominal_frames_of_run  # noqa: E402


def main(argv):
    for d in argv:
        if d.startswith("--"):
            continue
        d = d if os.path.isabs(d) else os.path.join(ROOT, d)
        sp = os.path.join(d, "steps.jsonl")
        pj = os.path.join(d, "player.json")
        if not os.path.isfile(sp):
            print("%s: no steps.jsonl" % d)
            continue
        steps = [json.loads(l) for l in io.open(sp, encoding="utf-8") if l.strip()]
        ctx = None
        if os.path.isfile(pj):
            ctx = dict((json.load(io.open(pj, encoding="utf-8")).get("verdict_context") or {}))
            ctx["source"] = pj
        # TASK-140 §1.A.1: the same fallback `record_model_player_criterion` applies, so this
        # reader shows exactly what the real gate would record (including for pre-TASK-140
        # runs, whose nominal budget lives in their own session.json).
        frames, src = nominal_frames_of_run(d, ctx)
        if frames is not None:
            ctx = dict(ctx or {})
            ctx["window_frames"] = frames
            ctx["window_frames_source"] = src
        ev = evaluate_model_player_steps(steps, os.path.basename(os.path.dirname(d)),
                                         run_context=ctx)
        print("%s" % os.path.relpath(d, ROOT))
        print("   verdict=%-24s counts_as_pass=%-5s qualified=%s"
              % (ev["verdict"], ev["counts_as_pass"], ev.get("qualified_verdict")))
        print("   verdict_context=%s" % json.dumps(ev.get("verdict_context"),
                                                   ensure_ascii=False))
        print("   reporting_window=%s" % json.dumps(ev.get("reporting_window"),
                                                    ensure_ascii=False))
        print("   reporting_why=%s" % ev.get("reporting_why"))
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
