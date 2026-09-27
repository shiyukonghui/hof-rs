#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""test_playability_model_player.py -- TASK-133/TASK-134: the gate-side model-player rules.

What this test is for
---------------------
TASK-132 put the model-player criterion beside P1..P7 in `gate.json`, and TASK-133
added two rules that must not drift between the loop (`playtest_player.summarise`) and
the gate (`playability_gate.evaluate_model_player_steps`):

  * `MODEL_FIXED_POINT` (TASK-133 §1.C.1): when the model answers the SAME action on a
    byte-identical frame for >= 3 consecutive steps it is stuck.  That is a fact about
    the MODEL: it must be recorded separately from FAIL, it must never be turned into a
    game defect, and it must never be turned into a PASS either.
  * `done` removed from the option set (TASK-133 §1.C.2): a live game has no "stop
    probing" input, so the probe no longer offers it (`wait` stays).

TASK-134 adds the fixed point's WIDER twin, because TASK-133 measured the fixed point's
blind spot (`pong x playjev`: nine accepted-but-frozen steps, the action varied once, so
`same_action_fixed_point` never fired):

  * `MODEL_NO_PROGRESS` (TASK-134 §1.C.1): >= 3 consecutive SENT steps with no gameplay
    progress, EVEN IF the actions differ.  §1.C.3 fixes its status exactly like the fixed
    point's: reported on its own, never a game defect, never a PASS, never a licence to
    stop failing a run that really did leave the picture frozen.

No engine, no service, no network, no file writes.  Run:

    D:\\Anaconda\\python.exe tools\\tests\\test_playability_model_player.py
    D:\\Anaconda\\python.exe -m pytest tools\\tests\\test_playability_model_player.py -q
"""
from __future__ import print_function

import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
TOOLS = os.path.dirname(HERE)
sys.path.insert(0, TOOLS)

from playability_gate import evaluate_model_player_steps  # noqa: E402
from playtest_agent import action_criteria  # noqa: E402
from playtest_player import (  # noqa: E402
    model_fixed_point, model_no_progress, summarise,
)


def step(i, action, frame, changed=True, accepted=True, injected=True, verdict=None):
    return {
        "step": i,
        "action": {"action": action, "type": "action" if action else "wait"},
        "ack": {"accepted": accepted, "injected": injected},
        "change": {"changed": changed},
        "frame_before_sha": frame,
        "model": {"request_path": "req-%s" % action},
        "markers": {"GameOver": False},
        "step_verdict": verdict or ("ok_ack_and_changed" if changed
                                    else "FAIL_no_change_after_accepted_input"),
    }


def clean_run(n=8):
    """A game that responds to every one of n distinct actions on distinct frames."""
    return [step(i, "act%d" % i, "frame%d" % i) for i in range(1, n + 1)]


def stuck_run(n=8, action="pong_right_down", frame="sameframe"):
    """The PlayJev failure mode: one action, one frame, repeated."""
    return [step(i, action, frame) for i in range(1, n + 1)]


def mixed_static_run(n=9, frame_every_step=True):
    """TASK-134's motivating sequence (`pong x playjev`): the actions DIFFER, nothing moves.

    Every step was really sent to the game and left both the picture and the declared
    gameplay observables unchanged, so `change.changed` is false and the step verdict is
    the user's FAIL condition.  The actions differ on purpose: that is what made the
    fixed-point rule miss this run (TASK-133 §4.2a measured `rate 0.25` with
    `same_action_fixed_point` NOT triggered).
    """
    out = []
    for i in range(1, n + 1):
        frame = ("frame%02d" % i) if frame_every_step else "oneframe"
        r = step(i, "act%d" % ((i % 3) + 1), frame, changed=False)
        r["change"] = {"changed": False}
        r["step_verdict"] = "FAIL_no_change_after_accepted_input"
        out.append(r)
    return out


def main():
    cases = []

    def check(name, got, want):
        cases.append((got == want, name, "got=%r want=%r" % (got, want)))

    # ---- the clean run: a real game verdict, no fixed point -------------------------
    ev = evaluate_model_player_steps(clean_run(), "g")
    check("clean run -> no MODEL_FIXED_POINT", ev["MODEL_FIXED_POINT"], False)
    check("clean run -> pass=True", ev["pass"], True)
    check("clean run -> fixed-point reading is a string",
          isinstance(ev["model_fixed_point"]["reading"], str), True)

    # ---- the model's fixed point, on the gate side ----------------------------------
    ev_fp = evaluate_model_player_steps(stuck_run(), "g")
    check("8 identical action+frame steps -> MODEL_FIXED_POINT", ev_fp["MODEL_FIXED_POINT"],
          True)
    check("fixed point -> pass is NOT False (not a game defect)", ev_fp["pass"], None)
    check("fixed point -> why names it", "MODEL_FIXED_POINT" in ev_fp["why"], True)
    check("fixed point -> run length", ev_fp["model_fixed_point"]["length"], 8)
    check("fixed point -> steps listed",
          ev_fp["model_fixed_point"]["steps"], [1, 2, 3, 4, 5, 6, 7, 8])
    check("fixed point -> action named", ev_fp["model_fixed_point"]["action"],
          "pong_right_down")
    check("fixed point -> threshold recorded",
          ev_fp["thresholds"]["model_fixed_point_min_run"], 3)
    check("fixed point -> marked as neither defect nor PASS",
          "NOT a game defect" in ev_fp["model_fixed_point"]["what"], True)

    # the threshold boundary, exactly as the task states it
    check("2 identical steps -> NOT a fixed point",
          evaluate_model_player_steps(stuck_run(2), "g")["MODEL_FIXED_POINT"], False)
    check("3 identical steps -> a fixed point",
          evaluate_model_player_steps(stuck_run(3), "g")["MODEL_FIXED_POINT"], True)

    # the same action on DIFFERENT frames is not a fixed point: the model is reading a
    # picture that is moving
    moving = [step(i, "same", "frame%d" % i) for i in range(1, 9)]
    check("same action, moving frames -> NOT a fixed point",
          evaluate_model_player_steps(moving, "g")["MODEL_FIXED_POINT"], False)

    # a `wait` (not injected) breaks the run
    broken = stuck_run(8)
    broken[4] = step(5, None, "sameframe", accepted=False, injected=False,
                     verdict="no_ack_no_change")
    check("a `wait` step breaks the fixed-point run",
          evaluate_model_player_steps(broken, "g")["model_fixed_point"]["length"], 4)

    # ---- the game-side FAIL is unchanged by the new conclusion ----------------------
    # two distinct actions, one accepted static step, no terminal state -> the real FAIL
    mixed = clean_run(8)
    mixed[3] = step(4, "act4", "frame4", changed=False)
    ev_fail = evaluate_model_player_steps(mixed, "g")
    check("varied actions + one static step -> pass=False (real FAIL)", ev_fail["pass"],
          False)
    check("that FAIL is not relabelled a fixed point", ev_fail["MODEL_FIXED_POINT"], False)

    # ---- the loop's own summary agrees with the gate's reading -----------------------
    s_fp = summarise(stuck_run(), "playjev", "g")
    check("loop: MODEL_FIXED_POINT", s_fp["MODEL_FIXED_POINT"], True)
    check("loop: fixed point is not a PASS", s_fp["verdict"] == "PASS", False)
    check("loop: fixed point is not a FAIL", s_fp["verdict"] == "FAIL", False)
    s_ok = summarise(clean_run(), "jev", "g")
    check("loop: clean run still PASS", s_ok["verdict"], "PASS")
    check("loop: clean run has no fixed point", s_ok["MODEL_FIXED_POINT"], False)

    # the two implementations are one rule: same length, same steps, same action
    fp_loop = model_fixed_point(stuck_run())
    fp_gate = ev_fp["model_fixed_point"]
    check("loop and gate agree on the run length", fp_loop["length"], fp_gate["length"])
    check("loop and gate agree on the steps", fp_loop["steps"], fp_gate["steps"])
    check("loop and gate agree on the action", fp_loop["action"], fp_gate["action"])

    # ---- done removed from the option set --------------------------------------------
    crit = action_criteria({"actions": {"a_up": ["W"]}, "keys": []})
    check("probe criteria no longer offer `done`", "done" in crit, False)
    check("probe criteria still offer `wait`", "wait" in crit, True)
    check("probe criteria still offer the declared action", "a_up" in crit, True)

    # =================================================================================
    # TASK-134 §1.C.1-§1.C.4: MODEL_NO_PROGRESS, the fixed point's wider twin.
    # =================================================================================

    # (1) THE REQUIRED CASE: "mixed in a different action but no progress" MUST be caught.
    mixed = mixed_static_run(9)
    ev_np = evaluate_model_player_steps(mixed, "pong")
    check("mixed actions + no progress -> MODEL_NO_PROGRESS", ev_np["MODEL_NO_PROGRESS"], True)
    check("... and the run really did vary its action",
          len(ev_np["model_no_progress"]["distinct_actions"]) > 1, True)
    check("... the whole 9-step run is the no-progress run",
          ev_np["model_no_progress"]["length"], 9)
    check("... its steps are listed",
          ev_np["model_no_progress"]["steps"], list(range(1, 10)))
    check("... it is NOT reported as a fixed point (the actions differ)",
          ev_np["MODEL_FIXED_POINT"], False)
    check("... the game verdict is still the user's FAIL",
          ev_np["pass"], False)
    check("... the failing steps are still recorded",
          ev_np["fail_steps"], list(range(1, 10)))
    check("no-progress is marked neither defect nor PASS",
          "NOT a game defect" in ev_np["model_no_progress"]["what"], True)
    check("no-progress threshold recorded",
          ev_np["thresholds"]["model_no_progress_min_run"], 3)

    # (2) THE SAME-ACTION CASE still yields MODEL_FIXED_POINT.
    ev_fp_static = evaluate_model_player_steps(
        [dict(r, change={"changed": False},
              step_verdict="FAIL_no_change_after_accepted_input")
         for r in stuck_run(8)], "pong")
    check("same action + same frame -> MODEL_FIXED_POINT", ev_fp_static["MODEL_FIXED_POINT"],
          True)
    check("... and the wider rule sees it too (both conclusions coexist)",
          ev_fp_static["MODEL_NO_PROGRESS"], True)

    # (3) THE PROGRESSING CASE triggers NEITHER.
    ev_ok = evaluate_model_player_steps(clean_run(8), "pong")
    check("a progressing run -> no MODEL_NO_PROGRESS", ev_ok["MODEL_NO_PROGRESS"], False)
    check("a progressing run -> no MODEL_FIXED_POINT", ev_ok["MODEL_FIXED_POINT"], False)
    check("a progressing run -> still pass=True", ev_ok["pass"], True)

    # (4) the threshold is 3, exactly like the fixed point's
    check("2 static steps -> NOT MODEL_NO_PROGRESS",
          evaluate_model_player_steps(mixed_static_run(2), "pong")["MODEL_NO_PROGRESS"],
          False)
    check("3 static steps -> MODEL_NO_PROGRESS",
          evaluate_model_player_steps(mixed_static_run(3), "pong")["MODEL_NO_PROGRESS"], True)

    # (5) a `wait` step (nothing was sent) breaks the run: it is not a measurement of the
    #     game, so it can be neither progress nor its absence.
    broken_np = mixed_static_run(9)
    broken_np[4] = step(5, None, "frame05", accepted=False, injected=False,
                        verdict="no_ack_no_change")
    check("a `wait` step breaks the no-progress run",
          evaluate_model_player_steps(broken_np, "pong")["model_no_progress"]["length"], 4)

    # (6) a step that DID move the picture resets the run.
    one_moved = mixed_static_run(9)
    one_moved[4] = step(5, "act2", "frame05", changed=True)
    check("one progressing step resets the no-progress run",
          evaluate_model_player_steps(one_moved, "pong")["model_no_progress"]["length"], 4)

    # (7) the loop's twin reaches the SAME answer on the same records: one rule, two files.
    np_loop = model_no_progress(mixed)
    np_gate = ev_np["model_no_progress"]
    check("loop and gate agree: found", np_loop["found"], np_gate["found"])
    check("loop and gate agree: length", np_loop["length"], np_gate["length"])
    check("loop and gate agree: steps", np_loop["steps"], np_gate["steps"])
    check("loop and gate agree: distinct actions",
          np_loop["distinct_actions"], np_gate["distinct_actions"])

    # (8) the game verdict is NOT relaxed by the new conclusion -- the FAIL survives it.
    s_np = summarise(mixed, "playjev", "pong")
    check("loop: MODEL_NO_PROGRESS reported", s_np["MODEL_NO_PROGRESS"], True)
    check("loop: that run is still FAIL (not softened to INCONCLUSIVE)",
          s_np["verdict"], "FAIL")
    check("loop: no-progress is not a PASS", s_np["verdict"] == "PASS", False)

    ok = True
    for good, name, detail in cases:
        ok = ok and good
        print("%-58s %s%s" % (name[:58], "OK" if good else "MISMATCH",
                              "" if good else "  " + detail))
    print("test_playability_model_player %s (%d assertions)"
          % ("PASSED" if ok else "FAILED", len(cases)))
    return 0 if ok else 1


def test_model_player_rules():
    assert main() == 0


if __name__ == "__main__":
    sys.exit(main())
