# -*- coding: utf-8 -*-
"""TASK-098 item B3: re-read the numbers GAME-LOOP-LOG.md quotes, from the runs themselves.

Every row of the ledger cites a run directory. This script walks those directories, reads
each `report.json`, and prints exactly the four quantities the ledger quotes:

  * the call counts and `facts_complete` per endpoint and in total;
  * the verdict distribution;
  * the pixel column: comparable pairs, non-zero pairs, and the per-endpoint split;
  * the `user://` frame pairs and their recomputed diffs.

It does not decide whether the ledger is right -- it prints what the artifacts say, so the
comparison in TASK-098-REPORT.md can be checked line by line instead of trusted.
"""
import io
import json
import os
import sys

RUNS = [
    ("1 Pong        ", "runs/pong/pong-clean-task097"),
    ("1 Pong (092)  ", "runs/pong/pong-task092"),
    ("2 Breakout    ", "runs/breakout/breakout-clean-task097"),
    ("3 Snake       ", "runs/snake/snake-clean-task097"),
    ("4 Tetris      ", "runs/tetris/tetris-task096-r2"),
    ("4 Tetris r1   ", "runs/tetris/tetris-task096"),
    ("5 SpaceInv    ", "runs/spaceinvaders/si-task097-r1"),
    ("6 Asteroids   ", "runs/asteroids/ast-task098-r2"),
    ("7 Pac-Man     ", "runs/pacman/pac-task098-r2"),
]


def main():
    root = sys.argv[1] if len(sys.argv) > 1 else "."
    for label, rel in RUNS:
        run = os.path.join(root, rel.replace("/", os.sep))
        path = os.path.join(run, "report.json")
        if not os.path.isfile(path):
            print("%s  MISSING report.json (%s)" % (label, run))
            continue
        with io.open(path, "r", encoding="utf-8") as handle:
            rep = json.load(handle)
        print("== %s  %s" % (label, rel))
        total_calls = total_facts = 0
        verdicts = {}
        for name in ("editor", "game"):
            summary = rep["endpoints"][name]["ledger"]
            if summary is None:
                print("   %-7s NO LEDGER" % name)
                continue
            calls = summary["calls"] or 0
            total_calls += calls
            total_facts += summary["facts_complete"]
            for key, value in (summary["verdicts"] or {}).items():
                verdicts[key] = verdicts.get(key, 0) + value
            pairs = rep["endpoints"][name]["captures"]
            nz = len([p for p in pairs
                      if ((p.get("recomputed") or {}).get("changed_pixels") or 0) > 0])
            print("   %-7s calls=%-3d facts=%d/%d  pixels=%d/%d non-zero"
                  % (name, calls, summary["facts_complete"], calls, nz, len(pairs)))
        pairs_all = []
        for name in ("editor", "game"):
            pairs_all.extend(rep["endpoints"][name]["captures"])
        nz_all = len([p for p in pairs_all
                      if ((p.get("recomputed") or {}).get("changed_pixels") or 0) > 0])
        print("   TOTAL   calls=%-3d facts=%d/%d  pixels=%d/%d non-zero"
              % (total_calls, total_facts, total_calls, nz_all, len(pairs_all)))
        print("   verdicts: %s" % ", ".join("%s=%d" % kv for kv in sorted(verdicts.items())))
        frames = (rep.get("saved_frames") or {}).get("frames") or []
        # `diff_vs_prev` belongs to the frame it is stored on: it is the transition INTO
        # that frame. Label the pair, not the destination, or the chain reads off by one.
        chain = []
        for frame in frames:
            diff = frame.get("diff_vs_prev") or {}
            if not diff:
                continue
            chain.append("%s->%s=%s" % (
                (frame.get("diff_prev_name") or "?").replace(".png", ""),
                frame["name"].replace(".png", ""),
                diff.get("changed_pixels", "-")))
        print("   frames(%d, only same-size transitions):" % len(frames))
        for item in chain:
            print("      %s" % item)


if __name__ == "__main__":
    main()
