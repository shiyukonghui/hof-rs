# -*- coding: utf-8 -*-
"""TASK-139 §1.A.2/§1.A.3: the WINDOW-LENGTH SENSITIVITY MATRIX.

For every arm and every game it puts the TWO RUNG runs side by side -- same backend, same
variant, same margin, same step budget, only `--window-frames` differs (30 vs 90) -- and
answers three questions with numbers:

  1. per game, the verdict under each rung;
  2. every game whose verdict FLIPS between the rungs is drawn up, and the steps that moved
     are NAMED (`SENSITIVE`), with each step's per-step verdict / changed reading under both
     rungs;
  3. `asteroids` gets its own section (TASK-138 flipped it from `PASS(baseline only)` to
     `PASS`), with its per-step evidence under both rungs.

It reads the run artifacts only; it starts no game and touches no service.

Usage (cmd):
    D:\\Anaconda\\python.exe runs\\model-player\\_scripts\\t139_sensitivity.py
"""
from __future__ import print_function

import io
import json
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.abspath(os.path.join(HERE, "..", "..", ".."))
RUNS = os.path.join(ROOT, "runs", "model-player")

ARMS = [
    {"arm": "scripted", "player": "scripted", "rungs": [30, 90],
     "prefix": "t139-scripted-w%d"},
    {"arm": "model", "player": "jev", "rungs": [30, 90],
     "prefix": "t139-jev-v3-w%d"},
    {"arm": "playjev", "player": "playjev", "rungs": [30],
     "prefix": "t139-playjev-v3-w%d"},
]

VERDICT_KEYS = ("verdict", "counts_as_pass", "strict_verdict", "baseline_verdict",
                "game_side_verdict", "accepted_and_changed_rate", "rated_and_changed_rate",
                "rated_step_count", "real_progress_step_count", "refused_steps",
                "refusal_only_run", "fail_steps", "window_too_short",
                "window_too_short_steps")


def load_json(p):
    with io.open(p, encoding="utf-8") as fh:
        return json.load(fh)


def run_dir(prefix, game, player):
    return os.path.join(RUNS, prefix, game, player)


def summary(prefix, game, player):
    p = os.path.join(run_dir(prefix, game, player), "player.json")
    if not os.path.isfile(p):
        return None
    s = load_json(p)
    out = {k: s.get(k) for k in VERDICT_KEYS}
    fa = s.get("frame_alignment") or {}
    out["frame_alignment_reading"] = fa.get("reading")
    out["frame_alignment_all_matched"] = fa.get("all_matched")
    out["window_min_frames"] = (s.get("window_frames") or {}).get("min_frames")
    out["player_json"] = os.path.relpath(p, ROOT).replace("\\", "/")
    return out


def steps(prefix, game, player):
    p = os.path.join(run_dir(prefix, game, player), "steps.jsonl")
    if not os.path.isfile(p):
        return {}
    out = {}
    for line in io.open(p, encoding="utf-8"):
        line = line.strip()
        if not line:
            continue
        r = json.loads(line)
        out[r.get("step")] = {
            "action": (r.get("action") or {}).get("action"),
            "step_verdict": r.get("step_verdict"),
            "changed": bool((r.get("change") or {}).get("changed")),
            "changed_strict": bool(((r.get("change") or {}).get("strict") or {}).get("changed")),
            "pixel_diff": r.get("pixel_diff"),
            "control_pixels": (r.get("change") or {}).get("control_pixels"),
            "gameplay_movement": r.get("gameplay_movement"),
            "control_movement": (r.get("change") or {}).get("control_movement"),
            "gameplay_changes": r.get("gameplay_changes"),
            "refused_legal": bool((r.get("step_refusal") or {}).get("refused_legal")),
            "control_frames": ((r.get("control_diff") or {}).get("frame_budget") or {}
                               ).get("achieved_delta"),
            "action_frames": (r.get("frame_budget") or {}).get("action_frames"),
        }
    return out


def main(argv):
    report = {"task": "TASK-139", "section": "A -- window-length sensitivity",
              "arms": [], "sensitive_games": [], "asteroids": None}
    for a in ARMS:
        arm_entry = {"arm": a["arm"], "rungs": a["rungs"], "games": {}, "flips": []}
        rungs = a["rungs"]
        prefixes = [a["prefix"] % w for w in rungs]
        games = set()
        for pfx in prefixes:
            base = os.path.join(RUNS, pfx)
            if os.path.isdir(base):
                games |= set(d for d in os.listdir(base)
                             if os.path.isdir(os.path.join(base, d)))
        for g in sorted(games):
            per_rung = {}
            for w, pfx in zip(rungs, prefixes):
                s = summary(pfx, g, a["player"])
                if s:
                    s["steps_detail"] = steps(pfx, g, a["player"])
                per_rung[w] = s
            vals = [per_rung.get(w) for w in rungs]
            verdicts = [v.get("verdict") if v else None for v in vals]
            flip = len(set(verdicts)) > 1
            entry = {"verdict_by_window": dict(zip([str(w) for w in rungs], verdicts)),
                     "flip": flip,
                     "pass_by_window": {str(w): (v or {}).get("counts_as_pass")
                                        for w, v in zip(rungs, vals)},
                     "runs": {str(w): ({k: v[k] for k in VERDICT_KEYS if k in v}
                                       if v else None)
                              for w, v in zip(rungs, vals)},
                     "player_json": {str(w): (v or {}).get("player_json")
                                     for w, v in zip(rungs, vals)}}
            affected = []
            if flip and all(vals):
                base_steps = (vals[0] or {}).get("steps_detail") or {}
                other_steps = (vals[-1] or {}).get("steps_detail") or {}
                for st in sorted(set(base_steps) | set(other_steps)):
                    b = base_steps.get(st)
                    o = other_steps.get(st)
                    if not b or not o:
                        affected.append({"step": st, "why": "present in only one rung",
                                         "rung_a": b, "rung_b": o})
                        continue
                    keys = ("step_verdict", "changed", "changed_strict", "refused_legal",
                            "pixel_diff", "gameplay_movement")
                    diff = {k: [b.get(k), o.get(k)] for k in keys if b.get(k) != o.get(k)}
                    if diff:
                        affected.append({"step": st, "action": b.get("action"),
                                         "differences": diff, "rung_a": b, "rung_b": o})
                entry["affected_steps"] = affected
                entry["affected_step_numbers"] = [x["step"] for x in affected]
            arm_entry["games"][g] = entry
            if flip and len(rungs) > 1:
                rep = {"arm": a["arm"], "game": g,
                       "verdict_by_window": entry["verdict_by_window"],
                       "affected_step_numbers": entry.get("affected_step_numbers"),
                       "affected_steps": entry.get("affected_steps"),
                       "reading": ("SENSITIVE: the verdict changes with the measurement "
                                   "window length; the steps above are the ones whose "
                                   "per-step reading moved")}
                arm_entry["flips"].append(rep)
                report["sensitive_games"].append(rep)
            if a["arm"] != "playjev" and g == "asteroids":
                report["asteroids"] = {"arm": a["arm"], "windows": rungs,
                                       "verdict_by_window": entry["verdict_by_window"],
                                       "pass_by_window": entry["pass_by_window"],
                                       "runs": entry["runs"],
                                       "steps_by_window": {
                                           str(w): ((per_rung.get(w) or {}).get("steps_detail")
                                                    or {}) for w in rungs},
                                       "still_pass_at_every_rung": all(
                                           v.get("counts_as_pass") for v in vals if v)}
        report["arms"].append(arm_entry)
    outp = os.path.join(HERE, "t139_sensitivity.json")
    with io.open(outp, "w", encoding="utf-8") as fh:
        fh.write(json.dumps(report, ensure_ascii=False, indent=1))
    print("=" * 78)
    for a in report["arms"]:
        print("ARM %s  games=%d  flips=%d" % (a["arm"], len(a["games"]), len(a["flips"])))
        for g, e in sorted(a["games"].items()):
            print("  %-16s %-42s flip=%s" % (g, e["verdict_by_window"], e["flip"]))
        for f in a["flips"]:
            print("  SENSITIVE %s: %s  affected steps %s"
                  % (f["game"], f["verdict_by_window"], f["affected_step_numbers"]))
    if report["asteroids"]:
        print("ASTEROIDS: %s  still_pass_at_every_rung=%s"
              % (report["asteroids"]["verdict_by_window"],
                 report["asteroids"]["still_pass_at_every_rung"]))
    print("wrote %s" % outp)
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
