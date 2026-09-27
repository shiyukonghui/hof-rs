# -*- coding: utf-8 -*-
"""TASK-139 §1.B: give the 5 known-refusal games an EXPLICIT `refusal_evidence` declaration.

TASK-131 X12 left them on the generic `["LastRefusedInput", "Rejected"]` pattern list, which
matches `RejectedMoves` / `InputRejectedSwaps` / `RejectedSteps` / `InputRejectedPlaces` by
substring.  That is how the counters were found -- but "found by a substring" is not a
declaration, and TASK-139 §1.B asks for the game-side counter to be NAMED.

This script adds, per game:
  * `game_side_fields` -- the exact field names read out of the game's own exported state
    (every one of them was observed in `steps.jsonl -> state_delta` of the TASK-138
    `t138-scripted` run, so they are measured, not guessed);
  * `how_read` -- the exact tool + path the value comes from;
  * `identifies` -- what the counter means;
  * `min_real_progress_steps` -- the per-game copy of the boundary floor (read from the
    shared `model_player_refusal.min_real_progress_steps`).

It is IDEMPOTENT and only ever ADDS keys.
"""
from __future__ import print_function

import io
import json
import os
import sys

ROOT = os.path.abspath(os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", ".."))
CTRL = os.path.join(ROOT, "tools", "playability_controls.json")

HOW_READ = ("the game's own exported property, read inside the game process by "
            "tools/playability_gate.probe_state_source() (executed through the MCP tool "
            "`running_game_execute_gdscript`), sampled before and after each injection and "
            "diffed into `steps.jsonl -> state_delta`; this tool then matches the diffed key "
            "against `game_side_fields`.  The model's own statement is never used.")

GAMES = {
    "match3": {
        "game_side_fields": ["RejectedMoves", "InputRejectedSwaps"],
        "identifies": ("`m3_swap` on a pair whose swap matches no run of three: the game "
                       "records it in `RejectedMoves` and `InputRejectedSwaps` and moves "
                       "nothing.  Measured on TASK-138 scripted steps 2/4/6/10, where both "
                       "counters advanced and no gameplay observable changed.  The "
                       "neighbouring field `InputSwaps` is the ATTEMPT counter (it counts a "
                       "legal swap too) and is deliberately NOT in this list -- it is not "
                       "evidence of a refusal."),
        "action_that_refuses": "m3_swap",
    },
    "minesweeper": {
        "game_side_fields": ["RejectedMoves", "InputRejectedCursorActions"],
        "identifies": ("`mine_reveal` on a cell the game will not reveal (an already-revealed "
                       "or flagged cell): `RejectedMoves` and `InputRejectedCursorActions` "
                       "advance while `RevealedCount` and the picture stay put.  Measured on "
                       "TASK-138 scripted steps 3/5/7/9/11.  The attempt counters "
                       "(`InputCursorReveals`, `InputCursorActions`) are deliberately NOT in "
                       "this list."),
        "action_that_refuses": "mine_reveal",
    },
    "pacman": {
        "game_side_fields": ["RejectedSteps"],
        "identifies": ("a direction step into a wall: `RejectedSteps` advances and PacCol/"
                       "PacX stay put.  Measured on TASK-138 scripted steps 3/6/8/10/12."),
        "action_that_refuses": "pac_up|pac_down|pac_left|pac_right",
    },
    "sokoban": {
        "game_side_fields": ["RejectedMoves"],
        "identifies": ("walking into a wall or pushing a box that cannot move: "
                       "`RejectedMoves` advances, PlayerCol/PlayerRow stay put.  Measured on "
                       "TASK-138 scripted steps 3/5/11."),
        "action_that_refuses": "soko_up|soko_down|soko_left|soko_right",
    },
    "towerdefense": {
        "game_side_fields": ["InputRejectedPlaces"],
        "identifies": ("`td_place` on a cell where a tower may not be built (occupied, or not "
                       "enough gold): `InputRejectedPlaces` advances while `TowersPlaced` and "
                       "`Gold` stay put.  Measured on TASK-138 scripted steps 6/9/12.  The "
                       "attempt counter `InputPlaces` is deliberately NOT in this list."),
        "action_that_refuses": "td_place",
    },
}

STEP_RULE = (
    "a step is a LEGAL REFUSAL when `game_side_fields` (or `keys`) appears among the keys of "
    "`steps.jsonl -> state_delta` for that step -- i.e. the game itself recorded that it saw "
    "the input and refused the move.  Such a step is removed from the FAIL set and from the "
    "rate's denominator, is NEVER counted as real progress, and the run must still show "
    "`min_real_progress_steps` steps of real progress (`model_player_refusal`) or it cannot "
    "PASS.  A run in which EVERY rated step was refused and nothing advanced is an explicit "
    "FAIL (`refusal_only_run`).")


def main(argv):
    doc = json.load(io.open(CTRL, encoding="utf-8"))
    floor = ((doc.get("model_player_refusal") or {}).get("min_real_progress_steps"))
    games = doc.get("games") or {}
    changed = []
    for g, spec in GAMES.items():
        d = games.get(g)
        if not isinstance(d, dict):
            print("MISSING GAME %s" % g)
            continue
        re_ = d.get("refusal_evidence")
        if not isinstance(re_, dict):
            re_ = {}
            d["refusal_evidence"] = re_
        re_["declared_by"] = "TASK-131 X12 (carve-out); TASK-139 §1.B (game-side fields)"
        re_["game_side_fields"] = spec["game_side_fields"]
        re_["action_that_refuses"] = spec["action_that_refuses"]
        re_["identifies"] = spec["identifies"]
        re_["how_read"] = HOW_READ
        re_["step_rule"] = STEP_RULE
        re_["min_real_progress_steps"] = floor
        # `keys` is what `playability_gate.refusal_hit` matches on.  It is replaced by the
        # EXACT game-side field names plus the generic `Rejected` pattern: TASK-131's
        # `LastRefusedInput` was dropped because it fires on ANY value (including a
        # non-refusal such as an "accepted" message), and `value_words` is emptied for the
        # same reason.  For these five games the counters are NAMED now, so a substring
        # heuristic is no longer needed and is no longer used.
        re_["keys"] = sorted(set(spec["game_side_fields"] + ["Rejected"]))
        re_["value_words"] = []
        re_["keys_before_task139"] = ["LastRefusedInput", "Rejected"]
        changed.append(g)
    io.open(CTRL, "w", encoding="utf-8", newline="\n").write(
        json.dumps(doc, ensure_ascii=False, indent=1) + "\n")
    check = json.load(io.open(CTRL, encoding="utf-8"))
    for g in changed:
        re_ = check["games"][g]["refusal_evidence"]
        print("%-14s game_side_fields=%s keys=%s min_real_progress_steps=%s"
              % (g, re_["game_side_fields"], re_["keys"], re_["min_real_progress_steps"]))
    print("WROTE %s (games updated: %s)" % (CTRL, changed))
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
