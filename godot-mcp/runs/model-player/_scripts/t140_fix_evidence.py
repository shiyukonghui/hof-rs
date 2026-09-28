# -*- coding: utf-8 -*-
"""TASK-140 §1.B: the four games' PRE-FIX -> POST-FIX evidence table.

Reads the results files of
  * `t140-prefix4-w90-r1`  (the four games, HEAD code, reporting window),
  * `t140-postfix4-w90-r3` (the four games, final fixed code, reporting window),
and prints one row per game with the fields the fix is judged on: verdict class,
`counts_as_pass`, rated/rejected/real-progress counts, rate, and the per-step numbers the
specific defect is about (resolution: the two runs' own `steps.jsonl`).

Usage (through the ledger wrapper):
    t140_cmd.py --cwd F:\\moonbit-hof-rs\\godot-mcp -- <py> runs\\model-player\\_scripts\\t140_fix_evidence.py
"""
from __future__ import print_function

import io
import json
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.abspath(os.path.join(HERE, "..", "..", ".."))
RUNS = os.path.join(ROOT, "runs", "model-player")

PAIRS = [("t140-prefix4-w90-r1", "pre-fix"), ("t140-scripted-w90-r1", "post-fix r1"),
         ("t140-scripted-w90-r2", "post-fix r2")]
GAMES = ("asteroids", "frogger", "bomberman", "flappy")
KEYS = ("verdict", "qualified_verdict", "counts_as_pass", "strict_verdict",
        "baseline_verdict", "game_side_verdict", "steps", "injected_steps", "accepted_steps",
        "changed_steps_of_accepted", "accepted_and_changed_rate", "rated_step_count",
        "rated_and_changed_rate", "refused_steps", "real_progress_step_count",
        "refusal_only_run", "fail_steps", "strict_fail_steps", "MODEL_FIXED_POINT",
        "MODEL_NO_PROGRESS")


def load(prefix, game):
    p = os.path.join(RUNS, prefix, game, "scripted", "player.json")
    if not os.path.isfile(p):
        return None, None, p
    with io.open(p, encoding="utf-8") as fh:
        s = json.load(fh)
    return s, p, p


def main():
    out = {}
    for game in GAMES:
        rows = {}
        for prefix, label in PAIRS:
            s, p, path = load(prefix, game)
            if s is None:
                rows[label] = {"error": "no player.json", "path": path}
                continue
            r = dict((k, s.get(k)) for k in KEYS)
            wf = s.get("window_frames") or {}
            r["window_steps"] = wf.get("steps")
            r["frame_alignment"] = (s.get("frame_alignment") or {}).get("reading")
            r["player_json"] = p
            rows[label] = r
        out[game] = rows
        print("=" * 96)
        print("GAME %s" % game)
        for label in ("pre-fix", "post-fix r1", "post-fix r2"):
            r = rows[label]
            if r.get("error"):
                print("  %-9s %s" % (label, r))
                continue
            print("  %-9s verdict=%-24s counts_as_pass=%-5s rate=%-7s rated=%-3s refused=%-14s "
                  "real=%-3s fail=%s"
                  % (label, r.get("verdict"), r.get("counts_as_pass"),
                     r.get("accepted_and_changed_rate"), r.get("rated_step_count"),
                     r.get("refused_steps"), r.get("real_progress_step_count"),
                     r.get("fail_steps")))
            print("            qualified=%s" % r.get("qualified_verdict"))
            print("            strict=%s baseline=%s game_side=%s"
                  % (r.get("strict_verdict"), r.get("baseline_verdict"),
                     r.get("game_side_verdict")))
    with io.open(os.path.join(HERE, "t140_fix_evidence.json"), "w", encoding="utf-8") as fh:
        fh.write(json.dumps(out, ensure_ascii=False, indent=1))
    print("wrote %s" % os.path.join(HERE, "t140_fix_evidence.json"))
    return 0


if __name__ == "__main__":
    sys.exit(main())
