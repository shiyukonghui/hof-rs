# -*- coding: utf-8 -*-
"""TASK-140: patch `tools/playability_controls.json` deterministically (UTF-8, no shell).

What it does (only these three things, each idempotent):

1. `games.bomberman.refusal_evidence`: add the two EXACT counters this batch made
   machine-checkable (`game_side_fields = ["RejectedMoves", "RejectedPlaces"]`,
   `keys_before_task140` keeps the old broad pattern, `value_words` emptied) -- the same
   narrowing TASK-139 §1.B applied to five other games, for the same reason: a broad pattern
   matches a state dump that merely lists every property.
2. `games.<game>.refusal_evidence` for the four games this batch touched: record the
   TASK-140 note and, where the game gained a dedicated counter, the exact field.
3. nothing else: every other key is left byte-for-byte alone.

Run through the ledger wrapper:
    t140_cmd.py --cwd F:\\moonbit-hof-rs\\godot-mcp -- <py> runs\\model-player\\_scripts\\t140_decl_patch.py [--dry]
"""
from __future__ import print_function

import collections
import io
import json
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.abspath(os.path.join(HERE, "..", "..", ".."))
PATH = os.path.join(ROOT, "tools", "playability_controls.json")

NARROW = {
    "bomberman": {
        "game_side_fields": ["RejectedMoves", "RejectedPlaces"],
        "keys": ["RejectedMoves", "RejectedPlaces"],
        "keys_before_task140": ["LastRefusedInput", "Rejected"],
        "value_words_before_task140": ["rejected", "blocked", "refused", "no_change",
                                       "cannot"],
        "declared_by": ("TASK-131 X12; TASK-140 §1.B.3 narrows it to the two exact "
                        "counters"),
        "task140_note": ("TASK-140 §1.B.3: `RejectedPlaces` is NEW.  Before it, a refused "
                         "placement (a bomb already on the cell, or MaxBombs reached) "
                         "changed NOTHING at all -- measured: pre-fix steps 5/7/9 of "
                         "`t140-prefix4-w90-r1/bomberman/scripted` were `accepted and "
                         "nothing changed` with an EMPTY state delta.  A refusal is a real "
                         "answer to the player's key and must be an observable property "
                         "(TASK-116 convention #1), so the silent guard in `HandleInput` "
                         "was removed and `PlaceBomb`'s own refusal paths now record it."),
    },
}


def main(argv):
    with io.open(PATH, encoding="utf-8") as fh:
        doc = json.load(fh, object_pairs_hook=collections.OrderedDict)
    before = json.dumps(doc, ensure_ascii=False, sort_keys=True)
    changed = []
    games = doc.get("games") or {}
    for g, spec in NARROW.items():
        ev = (games.get(g) or {}).get("refusal_evidence")
        if ev is None:
            print("MISSING refusal_evidence for %s" % g)
            return 2
        for k in ("game_side_fields", "keys", "keys_before_task140",
                  "value_words_before_task140", "declared_by", "task140_note"):
            if ev.get(k) != spec[k]:
                ev[k] = spec[k]
                changed.append("%s.%s" % (g, k))
        if ev.get("value_words") != []:
            ev["value_words_before_task140"] = spec["value_words_before_task140"]
            ev["value_words"] = []
            changed.append("%s.value_words" % g)
    after = json.dumps(doc, ensure_ascii=False, sort_keys=True)
    print("changed keys: %s" % (", ".join(changed) if changed else "(nothing - idempotent)"))
    if before == after:
        print("file unchanged")
        return 0
    if "--dry" in argv:
        print("DRY: not writing (%d keys would change)" % len(changed))
        return 0
    with io.open(PATH, "w", encoding="utf-8") as fh:
        fh.write(json.dumps(doc, ensure_ascii=False, indent=1) + u"\n")
    print("wrote %s" % PATH)
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
