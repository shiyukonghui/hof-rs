# -*- coding: utf-8 -*-
"""TASK-139 §1.A/§1.B: insert the two declaration blocks into playability_controls.json.

Written as a script rather than a text editor because the file is UTF-8 JSON with 1-space
indent and the insertion point must be found structurally, not by quoting a literal.

It is IDEMPOTENT: if `model_player_window` is already present it does nothing.
"""
from __future__ import print_function

import io
import json
import os
import sys

ROOT = os.path.abspath(os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", ".."))
CTRL = os.path.join(ROOT, "tools", "playability_controls.json")

WINDOW_COMMENT = [
    "TASK-139 §1.A -- the DECLARED MINIMUM MEASUREMENT WINDOW, and the `WINDOW_TOO_SHORT` state.",
    "",
    "Why this exists.  `--window-frames` is a NOMINAL budget: the loop waits until the game's",
    "own `Engine.get_frames_drawn()` has advanced by that many frames, so the length a window",
    "really achieves is a MEASURED quantity, and TASK-138 defect ⑧ already records it per step",
    "(`frame_alignment.steps[].control_frames` / `.action_frames`).  Before this declaration the",
    "tool had no way to say 'this judgement was made over a window too short to contain a game",
    "reaction': a 3-frame window and a 300-frame window produced the same two verdict strings.",
    "",
    "`min_frames` is deliberately NOT a PASS gate.  It can only take a run OUT of PASS: a run",
    "whose control or action window came out shorter than this is written",
    "`WINDOW_TOO_SHORT <verdict>` with `counts_as_pass: false`, and the measured spans stay in",
    "the artifact.  It never turns a non-PASS into a PASS and it does not move either ruler's",
    "formula (both are unchanged from TASK-135/TASK-136).",
    "",
    "BASIS for 20 (measured, not guessed): TASK-138 recorded 61 steps across its 20 games, and",
    "the achieved span of BOTH windows ran 29..34 drawn frames -- no window in that sweep was",
    "ever shorter than 29.  20 is therefore BELOW every recorded run's own floor: it flags",
    "nothing in that batch's evidence, it is comfortably above one MCP round trip (TASK-138",
    "defect ⑧ measured a single round trip at 30..120 drawn frames, so a window is at most that",
    "resolution), and at ~60 Hz it is about a third of a second -- 1/3 of the 1.0 s the change",
    "test compares against.  A window shorter than 20 drawn frames cannot contain a full",
    "input-release -> game-loop -> observable read-back cycle with any margin, which is exactly",
    "the judgement this state refuses to make.",
]

WINDOW_BLOCK = {
    "declared_by": "TASK-139 §1.A",
    "min_frames": 20,
    "applies_to": ["control_window", "action_window"],
    "state": "WINDOW_TOO_SHORT",
    "state_counts_as_pass": False,
    "how_used": ("tools/playtest_player.py `load_window_declaration` / `window_frames_of` / "
                 "`summarise` writes `player.json -> window_frames` (per step: the two measured "
                 "spans, `too_short`, `short_windows`) and prefixes the verdict with "
                 "`WINDOW_TOO_SHORT ` when any measured span is below `min_frames`; "
                 "`counts_as_pass` and `pass` are forced false.  `gate.json -> "
                 "model_player_criterion` reads the same block."),
    "basis": ("MEASURED: TASK-138 recorded 61 steps over its 20 games and the achieved span of "
              "both windows ran 29..34 drawn frames (nothing below 29); 20 sits below that "
              "floor, above one MCP round trip (30..120 frames, TASK-138 defect ⑧), and at "
              "~60 Hz is about 1/3 s of game time."),
    "not_a_loosening": [
        "the check only ever removes a PASS; it can never create one",
        "`--window-frames` and both rulers' formulas are unchanged from TASK-135/TASK-136",
        "the spans it judges are the game's own `Engine.get_frames_drawn()` deltas, not a "
        "wall-clock estimate",
    ],
}

REFUSAL_COMMENT = [
    "TASK-139 §1.B -- the LEGAL-REFUSAL boundary.",
    "",
    "TASK-136 §4.3/§12 registered the defect: five games (`match3`, `minesweeper`, `pacman`,",
    "`sokoban`, `towerdefense`) record a DELIBERATE refusal in their own exported counters, and",
    "the model-player loop's FAIL condition charged that refusal to the game as 'accepted an",
    "input and nothing changed'.  The gate has had this carve-out since TASK-131 X12",
    "(`arm_evidence.refused`); the loop never did, so a legitimate 'I saw your key and I will",
    "not move that way' was reported as a game defect.",
    "",
    "The boundary, declared here so it can be argued with: a LEGAL REFUSAL may be dropped from",
    "the FAIL set and from the rate's denominator -- it is not evidence AGAINST the game -- but",
    "it may NEVER be counted as progress.  A run must still show `min_real_progress_steps` of",
    "real progress, so 'the game refused everything and nothing ever advanced' can never reach",
    "PASS on refusals alone (the assertion lives in",
    "tools/tests/test_playability_model_player.py).",
    "",
    "BASIS for 4: the PASS rule needs >= 8 injected steps, and TASK-132's accepted-and-changed",
    "bar is 75%.  8 * 0.75 = 6, so a run that met the bar WITHOUT any refusals always carries",
    ">= 6 real progress steps and 4 cannot touch it -- the floor is provably only reachable",
    "when the carve-out removed part of the denominator.  4 is the number below which the",
    "remaining evidence is too thin to describe a playable game at all (it is half the minimum",
    "step count).",
]

REFUSAL_BLOCK = {
    "declared_by": "TASK-139 §1.B",
    "min_real_progress_steps": 4,
    "min_real_progress_rate": 0.5,
    "rule": ("a step the game's own exported counters record as a deliberate refusal is (1) "
             "removed from the model-player FAIL set, (2) removed from the rate's denominator, "
             "and (3) NEVER counted as progress.  A run is FAIL when every rated step was "
             "refused and no step produced real progress (`refusal_only_run`), and "
             "INCONCLUSIVE when fewer than `min_real_progress_steps` steps of real progress "
             "remain after the carve-out."),
    "evidence_source": ("the game's own exported state delta for the step (`steps.jsonl -> "
                        "state_delta`), matched against "
                        "`games.<game>.refusal_evidence.game_side_fields` / `.keys`; the "
                        "model's own statement is never used"),
    "how_used": ("tools/playtest_player.py `step_refusal_record` (per step, written as "
                 "`steps.jsonl -> step_refusal`), `_summarise_core` (the FAIL set, the rated "
                 "denominator, `refusal_only_run`, `real_progress_step_count`); the numbers are "
                 "in `player.json -> refusal_boundary`"),
    "basis": ("MEASURED: the PASS rule needs >= 8 injected steps and the accepted-and-changed "
              "bar is 0.75, so a run that met the bar with no refusals always has >= 6 real "
              "progress steps; 4 is below that and half the minimum step count."),
    "not_a_loosening": [
        "the carve-out can only remove a FAIL the GAME ITSELF recorded as a refusal",
        "it can never turn a 'not changed' into a 'changed': refusals are excluded from both "
        "the FAIL set and the progress set",
        "`refusal_only_run` is an explicit FAIL branch, so 'all refused, zero progress' cannot "
        "PASS",
        "a run with no refusals has an empty refused set and every number is the pre-TASK-139 "
        "number",
    ],
}


def main(argv):
    lines = io.open(CTRL, encoding="utf-8").read().splitlines()
    doc = json.loads("\n".join(lines))
    if "model_player_window" in doc and "model_player_refusal" in doc:
        print("ALREADY PRESENT: nothing to do")
        return 0
    idx = None
    for i, l in enumerate(lines):
        if l == ' "games": {':
            idx = i
            break
    if idx is None:
        print("ANCHOR NOT FOUND: no line equal to ' \"games\": {'")
        return 2
    blob = []
    if "model_player_window" not in doc:
        blob.append(' "_model_player_window_comment": %s,'
                    % json.dumps(WINDOW_COMMENT, ensure_ascii=False, indent=1))
        blob.append(' "model_player_window": %s,'
                    % json.dumps(WINDOW_BLOCK, ensure_ascii=False, indent=1))
    if "model_player_refusal" not in doc:
        blob.append(' "_model_player_refusal_comment": %s,'
                    % json.dumps(REFUSAL_COMMENT, ensure_ascii=False, indent=1))
        blob.append(' "model_player_refusal": %s,'
                    % json.dumps(REFUSAL_BLOCK, ensure_ascii=False, indent=1))
    new = lines[:idx] + "\n".join(blob).splitlines() + lines[idx:]
    io.open(CTRL, "w", encoding="utf-8", newline="\n").write("\n".join(new) + "\n")
    check = json.loads(io.open(CTRL, encoding="utf-8").read())
    print("WROTE %s: model_player_window=%s model_player_refusal=%s top-level keys=%s"
          % (CTRL, "model_player_window" in check, "model_player_refusal" in check,
             list(check.keys())))
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
