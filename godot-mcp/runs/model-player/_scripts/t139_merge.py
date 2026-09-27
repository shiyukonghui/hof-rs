# -*- coding: utf-8 -*-
"""TASK-139: merge per-game sweep result rows written by later, partial re-runs.

A partial re-run (e.g. the 5 legal-refusal games re-measured after the refusal EVIDENCE
STRING was changed to name the declared counter) writes its own
`t139_results_<prefix>-<suffix>.json`.  This merges those rows into the arm's full
`t139_results_<prefix>.json`, one row per game, so the arm's outcome file stays a complete
20-game record while the partial run's own file remains the evidence for what it changed.

Usage (cmd):
    D:\\Anaconda\\python.exe runs\\model-player\\_scripts\\t139_merge.py t139-scripted-w30 counterev
    D:\\Anaconda\\python.exe runs\\model-player\\_scripts\\t139_merge.py t139-scripted-w90 counterev
"""
from __future__ import print_function

import io
import json
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.abspath(os.path.join(HERE, "..", "..", ".."))


def load(p):
    if not os.path.isfile(p):
        return []
    return json.load(io.open(p, encoding="utf-8"))


def main(argv):
    if len(argv) < 2:
        print("usage: t139_merge.py <prefix> <suffix>")
        return 2
    prefix, suffix = argv[0], argv[1]
    base_p = os.path.join(HERE, "t139_results_%s.json" % prefix)
    part_p = os.path.join(HERE, "t139_results_%s-%s.json" % (prefix, suffix))
    base = load(base_p)
    part = load(part_p)
    by_game = {}
    for r in base:
        by_game[r.get("game")] = r
    replaced = []
    for r in part:
        g = r.get("game")
        if not g or r.get("verdict") is None and not (r.get("summary") or {}).get("verdict"):
            continue
        if g in by_game:
            replaced.append(g)
        by_game[g] = r
    rows = [by_game[g] for g in sorted(by_game)]
    with io.open(base_p, "w", encoding="utf-8") as fh:
        fh.write(json.dumps(rows, ensure_ascii=False, indent=1))
    print("merged %s <- %s: %d rows (%d replaced: %s)"
          % (os.path.basename(base_p), os.path.basename(part_p), len(rows), len(replaced),
             sorted(replaced)))
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
