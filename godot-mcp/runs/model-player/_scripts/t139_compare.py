# -*- coding: utf-8 -*-
"""TASK-139 §1.C.7: the OLD vs NEW distribution comparison, with every run named.

Reads the recorded sweeps and prints, per arm:
  * the distribution of top-level verdicts (parsed into PASS / PASS(baseline only) / FAIL /
    INCONCLUSIVE, plus the new WINDOW_TOO_SHORT prefix when it appears),
  * the per-game old -> new table with the flip flagged,
  * the two readings this batch added (legal refusals, real progress).

Old side: TASK-136's recorded distributions (quoted from its own sweep result files:
`t136_scripted_results_t136-scripted-final.json`, `t136_model_results_jev.json`) and TASK-138's
re-run (`t138_results_scripted.json`, `t138_results_model.json`).

Usage (cmd):
    D:\\Anaconda\\python.exe runs\\model-player\\_scripts\\t139_compare.py
"""
from __future__ import print_function

import glob
import io
import json
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.abspath(os.path.join(HERE, "..", "..", ".."))
RUNS = os.path.join(ROOT, "runs", "model-player")

GAMES = ("asteroids", "bomberman", "breakout", "flappy", "frogger", "game2048",
         "lunarlander", "match3", "minesweeper", "missilecommand", "pacman", "platformer",
         "pong", "puzzlebobble", "rtype", "snake", "sokoban", "spaceinvaders", "tetris",
         "towerdefense")


def kind(v):
    """Collapse a verdict string into its distribution bucket."""
    v = v or "<missing>"
    if v.startswith("WINDOW_TOO_SHORT"):
        return "WINDOW_TOO_SHORT(%s)" % kind(v.split(" ", 1)[1] if " " in v else "")
    if v.startswith("PASS(baseline"):
        return "PASS(baseline only)"
    if v == "PASS":
        return "PASS"
    if v.startswith("INCONCLUSIVE"):
        return "INCONCLUSIVE"
    if v == "FAIL":
        return "FAIL"
    return v


def dist(rows):
    out = {}
    for _, v in rows:
        out[kind(v)] = out.get(kind(v), 0) + 1
    return out


def from_results(path):
    """`[{game, summary:{verdict,...}}]` -> {game: summary}."""
    if not os.path.isfile(path):
        return {}
    rows = json.load(io.open(path, encoding="utf-8"))
    return {r.get("game"): (r.get("summary") or {}) for r in rows if r.get("game")}


def from_prefix(prefix, player):
    """`<prefix>/<game>/<player>/player.json` -> {game: summary}.

    `player` may be a tuple of candidate backend directory names; the first one that exists
    for a game wins.  The directory is named after the BACKEND (`jev` for the text service,
    `playjev` for the vision one, `scripted` for the local policy), so a caller that knows
    only the arm passes both candidates.
    """
    base = os.path.join(RUNS, prefix)
    out = {}
    names = (player,) if isinstance(player, str) else tuple(player)
    if not os.path.isdir(base):
        return out
    for g in sorted(os.listdir(base)):
        for nm in names:
            p = os.path.join(base, g, nm, "player.json")
            if os.path.isfile(p):
                out[g] = json.load(io.open(p, encoding="utf-8"))
                break
    return out


def table(title, old, new, keys=("verdict",)):
    print("=" * 84)
    print(title)
    print("-" * 84)
    rows = []
    for g in GAMES:
        o = (old.get(g) or {}).get(keys[0])
        n = (new.get(g) or {}).get(keys[0])
        rows.append((g, o, n))
    print("OLD distribution: %s" % json.dumps(dist([(g, o) for g, o, _ in rows]),
                                             ensure_ascii=False))
    print("NEW distribution: %s" % json.dumps(dist([(g, n) for _, _, n in rows]),
                                             ensure_ascii=False))
    flips = [(g, o, n) for g, o, n in rows if kind(o) != kind(n)]
    print("FLIPS (kind-level): %d" % len(flips))
    for g, o, n in flips:
        print("   %-16s %-26s -> %-26s %s" % (g, o, n, "FLIP"))
    print("-" * 84)
    print("%-16s %-26s %-26s %s" % ("game", "old", "new", "extra"))
    for g in GAMES:
        o = (old.get(g) or {}).get(keys[0])
        n = (new.get(g) or {}).get(keys[0])
        nx = new.get(g) or {}
        extra = ("refused=%s real=%s rated=%s" % (nx.get("refused_steps"),
                                                  nx.get("real_progress_step_count"),
                                                  nx.get("rated_step_count")))
        print("%-16s %-26s %-26s %s" % (g, o, n, extra))
    return {"old_dist": dist([(g, o) for g, o, _ in rows]),
            "new_dist": dist([(g, n) for _, _, n in rows]),
            "flips": [{"game": g, "old": o, "new": n} for g, o, n in flips],
            "rows": [{"game": g, "old": o, "new": n,
                      "new_detail": {k: (new.get(g) or {}).get(k)
                                     for k in ("refused_steps", "real_progress_step_count",
                                               "rated_step_count", "counts_as_pass",
                                               "window_too_short", "window_frames")}}
                     for g, o, n in rows]}


def main(argv):
    report = {"task": "TASK-139", "section": "C -- old vs new distributions", "tables": {}}
    # --- scripted arm ------------------------------------------------------------------
    old_scripted = from_results(os.path.join(HERE,
                                             "t136_scripted_results_t136-scripted-final.json"))
    if not old_scripted:
        old_scripted = from_results(os.path.join(HERE, "t138_results_scripted.json"))
    new_scripted = from_prefix("t139-scripted-w30", "scripted")
    report["tables"]["scripted_old_vs_new_w30"] = table(
        "SCRIPTED ARM: TASK-136 recorded vs TASK-139 new-criterion w30",
        old_scripted, new_scripted)
    new_scripted90 = from_prefix("t139-scripted-w90", "scripted")
    report["tables"]["scripted_w30_vs_w90"] = table(
        "SCRIPTED ARM: TASK-139 w30 vs TASK-139 w90 (the window rungs)",
        new_scripted, new_scripted90)
    # --- model arm ---------------------------------------------------------------------
    old_model = from_results(os.path.join(HERE, "t136_model_results_jev.json"))
    new_model = from_prefix("t139-jev-v3-w30", ("jev", "model"))
    report["tables"]["model_old_vs_new_w30"] = table(
        "MODEL ARM (jev): TASK-136 recorded vs TASK-139 new-criterion w30",
        old_model, new_model)
    new_model90 = from_prefix("t139-jev-v3-w90", ("jev", "model"))
    report["tables"]["model_w30_vs_w90"] = table(
        "MODEL ARM (jev): TASK-139 w30 vs TASK-139 w90",
        new_model, new_model90)
    # --- playjev arm -------------------------------------------------------------------
    new_pj = from_prefix("t139-playjev-v3-w30", ("playjev", "model"))
    if new_pj:
        old_pj = from_prefix("t136-playjev-v3", ("playjev", "model")) or \
            from_prefix("t134-V3", ("playjev", "model"))
        report["tables"]["playjev_old_vs_new_w30"] = table(
            "PLAYJEV ARM (vision): recorded vs TASK-139 w30", old_pj, new_pj)
    # --- TASK-138's own re-run, for the like-for-like old side -------------------------
    t138_scripted = from_results(os.path.join(HERE, "t138_results_scripted.json"))
    if t138_scripted:
        report["tables"]["task138_vs_task139_scripted"] = table(
            "SCRIPTED ARM: TASK-138 (aligned windows, old criterion) vs TASK-139 (new criterion)",
            t138_scripted, new_scripted)
    outp = os.path.join(HERE, "t139_compare.json")
    with io.open(outp, "w", encoding="utf-8") as fh:
        fh.write(json.dumps(report, ensure_ascii=False, indent=1))
    print("=" * 84)
    print("wrote %s" % outp)
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
