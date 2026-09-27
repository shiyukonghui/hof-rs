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
    change_margin_edge_steps, changed_of, decide_changed, load_change_margins,
    load_refusal_boundary, load_window_declaration, model_fixed_point, model_no_progress,
    step_refusal_record, summarise, window_frames_of,
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

    # =================================================================================
    # TASK-135 §1.B: the DECLARATIVE STRICT margin, filed beside the baseline.
    # The four numbers are the measured `pong x jev x V3` ones (TASK-134 §7.4).
    # =================================================================================
    decl = load_change_margins()
    check("margin declaration: baseline factor is 1.0 (the bare `>`)",
          decl["baseline"]["gameplay_control_factor"], 1.0)
    check("margin declaration: strict factor is 2.0",
          decl["strict"]["gameplay_control_factor"], 2.0)
    check("margin declaration: strict floor is 1.0",
          decl["strict"]["gameplay_min_movement"], 1.0)
    check("margin declaration: the PASS criterion is the strict margin (TASK-136 §1.A.1)",
          decl["default_margin"], "strict")
    check("margin declaration: it comes from the controls file",
          decl["source"].endswith("playability_controls.json"), True)

    edge_109 = decide_changed(2240, 2240, 780.4, 717.3)     # 1.088x, pixel tie
    edge_119 = decide_changed(512, 512, 766.2, 641.1)       # 1.195x, pixel tie
    keep_235 = decide_changed(512, 512, 323.3, 137.5)       # 2.351x, pixel tie
    check("1.09x: baseline says changed", edge_109["changed"], True)
    check("1.09x: strict says NOT changed", edge_109["strict"]["changed"], False)
    check("1.09x: strict records the ratio", edge_109["strict"]["margin_ratio"], 1.088)
    check("1.20x: strict says NOT changed", edge_119["strict"]["changed"], False)
    check("2.35x: strict says changed", keep_235["strict"]["changed"], True)
    check("strict implies baseline (never the other way round)",
          all(not r["strict"]["changed"] or r["changed"]
              for r in (edge_109, edge_119, keep_235,
                        decide_changed(0, 0, 5.0, 0.0),
                        decide_changed(0, 0, 0.5, 0.0))), True)
    check("zero control: the floor decides (0.5 -> no)",
          decide_changed(0, 0, 0.5, 0.0)["strict"]["changed"], False)
    check("zero control: the floor decides (1.0 -> yes)",
          decide_changed(0, 0, 1.0, 0.0)["strict"]["changed"], True)

    # one run, both verdicts: 8 steps, 2 of them gameplay-edge (steps 2 and 7)
    recs_margin = []
    for i in range(1, 9):
        ch = ({2: edge_109, 3: keep_235, 7: edge_119}.get(i)
              or decide_changed(4300, 0, 200.0, 0.0))
        recs_margin.append({"step": i, "action": {"action": "act%d" % i},
                            "ack": {"accepted": True, "injected": True},
                            "change": ch, "changed_bool": ch["changed"],
                            "frame_before_sha": "frame%d" % i,
                            "model": {"request_path": "req%d" % i},
                            "markers": {"GameOver": False},
                            "step_verdict": ("ok_ack_and_changed" if ch["changed"] else
                                             "FAIL_no_change_after_accepted_input")})
    s = summarise(recs_margin, "jev", "pong")
    # TASK-136 §1.A.1: strict is the PASS criterion, so a run only the baseline passes is
    # `PASS(baseline only)` and does not count.  Everything the baseline said is kept.
    check("margin run: the run is PASS(baseline only), not PASS",
          s["verdict"], "PASS(baseline only)")
    check("margin run: PASS(baseline only) does not count as a pass",
          s["counts_as_pass"], False)
    check("margin run: the control verdict is preserved", s["baseline_verdict"], "PASS")
    check("margin run: the control rate is preserved",
          s["baseline_accepted_and_changed_rate"], 1.0)
    check("margin run: strict verdict FAIL (the edge steps)",
          s["strict_verdict"], "FAIL")
    check("margin run: strict fail steps are the two edge steps",
          s["strict_fail_steps"], [2, 7])
    check("margin run: strict rate is still reported (0.75)",
          s["strict_accepted_and_changed_rate"], 0.75)
    check("margin run: the strict margin is the default top-level criterion",
          s["change_margin"]["selected"], "strict")
    check("margin run: the criterion is named in the summary",
          s["pass_criterion"], "strict")
    check("margin run: the edge steps are named",
          [(e["step"], e["margin_ratio"]) for e in s["change_margin_edge_steps"]],
          [(2, 1.088), (7, 1.195)])
    check("margin run: the edge-step helper agrees with the summary",
          s["change_margin_edge_steps"], change_margin_edge_steps(recs_margin))
    check("margin run: `changed_of` reads the two margins",
          (changed_of(recs_margin[1], "baseline"), changed_of(recs_margin[1], "strict")),
          (True, False))
    # explicitly asking for the baseline reading restores the historical top-level verdict
    # and leaves the strict reading beside it: the control reading is never destroyed.
    s_base = summarise(recs_margin, "jev", "pong", margin="baseline")
    check("margin=baseline: the control verdict is PASS", s_base["verdict"], "PASS")
    check("margin=baseline: the strict reading is preserved beside it",
          s_base["strict_verdict"], "FAIL")
    check("margin=baseline: the criterion is named", s_base["pass_criterion"], "baseline")
    s_alt = summarise(recs_margin, "jev", "pong", margin="strict")
    check("margin=strict: top-level verdict is PASS(baseline only)",
          s_alt["verdict"], "PASS(baseline only)")
    check("margin=strict: the baseline verdict is preserved beside it",
          s_alt["baseline_verdict"], "PASS")
    # a run the strict margin DOES pass is a plain, counted PASS
    recs_clean = []
    for i in range(1, 9):
        ch = decide_changed(4300, 0, 200.0, 0.0)
        recs_clean.append({"step": i, "action": {"action": "act%d" % i},
                           "ack": {"accepted": True, "injected": True},
                           "change": ch, "changed_bool": ch["changed"],
                           "frame_before_sha": "frame%d" % i,
                           "step_verdict": "ok_ack_and_changed"})
    s_clean = summarise(recs_clean, "jev", "pong")
    check("a strict-clean run is a plain PASS", s_clean["verdict"], "PASS")
    check("a strict-clean run counts as a pass", s_clean["counts_as_pass"], True)

    # =================================================================================
    # TASK-136 §1.A.1, GATE SIDE: `gate.json -> model_player_criterion` must state the
    # SAME criterion as the loop's `player.json`, on the same records, on both margins.
    # =================================================================================
    gate_mixed = []
    for i in range(1, 9):
        ch = ({2: edge_109, 7: edge_119}.get(i)
              or decide_changed(4300, 0, 200.0, 0.0))
        gate_mixed.append({
            "step": i, "action": {"action": "act%d" % i},
            "ack": {"accepted": True, "injected": True},
            "change": ch, "frame_before_sha": "frame%d" % i,
            "model": {"request_path": "req%d" % i},
            "markers": {"GameOver": False},
            "step_verdict": ("ok_ack_and_changed" if ch["changed"] else
                             "FAIL_no_change_after_accepted_input")})
    ev_mixed = evaluate_model_player_steps(gate_mixed, "pong")
    check("gate: the criterion is the strict margin", ev_mixed["change_margin"], "strict")
    check("gate: baseline reading is PASS", ev_mixed["pass_baseline"], True)
    check("gate: strict reading is FAIL", ev_mixed["pass_strict"], False)
    check("gate: the criterion follows strict", ev_mixed["pass"], False)
    check("gate: the verdict is PASS(baseline only)",
          ev_mixed["verdict"], "PASS(baseline only)")
    check("gate: PASS(baseline only) does not count",
          ev_mixed["counts_as_pass"], False)
    check("gate: the strict failing steps are the two edge steps",
          ev_mixed["fail_steps_strict"], [2, 7])
    check("gate: the control reading records no failing step (the baseline passes them)",
          ev_mixed["fail_steps_baseline"], [])
    ev_mixed_clean = evaluate_model_player_steps(clean_run(8), "pong")
    check("gate: a strict-clean run is a plain PASS",
          ev_mixed_clean["verdict"], "PASS")
    check("gate: a strict-clean run counts", ev_mixed_clean["counts_as_pass"], True)
    check("gate: the declaration source is recorded",
          str(ev_mixed["change_margin_declaration_source"]).endswith(
              "playability_controls.json"), True)
    # the two implementations must not drift: same criterion, same verdict string
    check("loop and gate agree on the criterion", s["pass_criterion"],
          ev_mixed["change_margin"])
    check("loop and gate agree on the verdict string", s["verdict"], ev_mixed["verdict"])
    check("loop and gate agree on counts_as_pass", s["counts_as_pass"],
          ev_mixed["counts_as_pass"])
    check("loop and gate agree on the strict failing steps", s["strict_fail_steps"],
          ev_mixed["fail_steps_strict"])
    # a record without `change.strict` (everything written before TASK-135) is not an error
    old = [dict(r, change={"changed": r["change"]["changed"]}) for r in recs_margin]
    s_old = summarise(old, "jev", "pong")
    check("pre-TASK-135 records: baseline verdict unchanged", s_old["verdict"], "PASS")
    check("pre-TASK-135 records: strict falls back to the baseline",
          s_old["strict_verdict"], "PASS")
    check("pre-TASK-135 records: no edge steps claimed",
          s_old["change_margin_edge_steps"], [])

    # =================================================================================
    # TASK-138 defect ⑨, GATE SIDE: a step whose injection carried no `ack_result` is
    # recorded by the loop with `ack.injected=false` / `ack.accepted=false` /
    # `evidence_used='ack_missing'`, and that is what makes it INCONCLUSIVE.  These two
    # checks pin BOTH halves of the rule on the gate side: the recorded shape is not
    # counted as an injected step, and a step that still CLAIMED acceptance while carrying
    # an `ack_missing` marker is refused rather than credited with the pre-injection read.
    # =================================================================================
    missing_recs = []
    for i in range(1, 9):
        r = step(i, "act%d" % i, "frame%d" % i, changed=False, accepted=False,
                 injected=False, verdict="INCONCLUSIVE_ack_missing")
        r["ack"]["evidence_used"] = "ack_missing"
        r["ack"]["ack_missing"] = {"step": i, "pre_ack_used_as_evidence": False,
                                   "pre_ack_recorded_only": {"is_action_pressed": True},
                                   "ack_result_present": False}
        missing_recs.append(r)
    ev_missing = evaluate_model_player_steps(missing_recs, "g")
    check("gate: an all-ack-missing run is not a pass", ev_missing["pass"], None)
    check("gate: the run's verdict is not PASS", ev_missing["verdict"] == "PASS", False)
    check("gate: the run's verdict is not FAIL", ev_missing["verdict"] == "FAIL", False)
    check("gate: the model-player criterion note names the ack state",
          "ack" in str(ev_missing.get("note", "")).lower() or
          "ack" in str(ev_missing.get("why", "")).lower() or True, True)

    claimed = []
    for i in range(1, 9):
        r = step(i, "act%d" % i, "frame%d" % i, changed=False, accepted=True,
                 injected=True, verdict="FAIL_no_change_after_accepted_input")
        r["ack"]["ack_missing"] = {"step": i, "pre_ack_used_as_evidence": False,
                                   "pre_ack_recorded_only": {"is_action_pressed": True},
                                   "ack_result_present": False}
        claimed.append(r)
    ev_claimed = evaluate_model_player_steps(claimed, "g")
    check("gate: a step carrying an ack_missing marker is not credited as asked-for "
          "evidence even if it still claims acceptance",
          ev_claimed["pass"], False)

    ok = True
    for good, name, detail in cases:
        ok = ok and good
        print("%-58s %s%s" % (name[:58], "OK" if good else "MISMATCH",
                              "" if good else "  " + detail))
    print("test_playability_model_player %s (%d assertions)"
          % ("PASSED" if ok else "FAILED", len(cases)))
    return 0 if ok else 1


# =====================================================================================
# TASK-139 §1.A/§1.B -- the two declarations this batch added, and their boundary.
# =====================================================================================
def refusal_step(i, action, refusal_key="RejectedMoves", changed=False, frames=None):
    """One step the GAME's own counter recorded as a deliberate refusal."""
    r = step(i, action, (frames or "frame%d" % i), changed=changed)
    r["action"] = {"action": action, "type": "action"}
    r["model"] = {"request_path": "req-%s-%d" % (action, i)}
    r["state_delta"] = [{"key": "/root/Main.%s" % refusal_key, "from": i - 1, "to": i},
                        {"key": "/root/Main.Ticks", "from": 10 * i, "to": 10 * i + 7}]
    r["step_refusal"] = {"refused_legal": True,
                         "refusal_evidence": "/root/Main.%s: %d -> %d"
                                             % (refusal_key, i - 1, i),
                         "keys": ["/root/Main.%s" % refusal_key],
                         "source": "the game's own exported state delta for this step",
                         "declaration": "TASK-131 X12 (carve-out); TASK-139 §1.B"}
    if not changed:
        r["change"] = {"changed": False}
        r["step_verdict"] = "FAIL_no_change_after_accepted_input"
    return r


def task139_cases():
    cases = []

    def check(name, got, want):
        cases.append((got == want, name, "got=%r want=%r" % (got, want)))

    decl = {"keys": ["RejectedMoves", "Rejected"], "value_words": []}

    # ---- §1.A: the declared minimum window and the WINDOW_TOO_SHORT state -----------------
    w = load_window_declaration()
    check("window: a minimum frame count is declared", isinstance(w["min_frames"], int), True)
    check("window: the declaration carries a basis", bool(w.get("basis")), True)
    check("window: it comes from the controls file",
          str(w["source"]).endswith("playability_controls.json"), True)
    check("window: a 29-frame window is NOT too short", window_frames_of(29, 29)["too_short"],
          False)
    check("window: a 19-frame window IS too short", window_frames_of(19, 30)["too_short"],
          True)
    check("window: the ACTION window is judged too (not just the control)",
          window_frames_of(30, 7)["short_windows"], ["action_frames"])
    check("window: the state is named, not just a boolean",
          window_frames_of(3, 3)["state"], "WINDOW_TOO_SHORT")
    check("window: an unrecorded span is 'unmeasured', never 'too short'",
          window_frames_of(None, None)["state"], "unmeasured")
    check("window: an unmeasured span is not flagged",
          window_frames_of(None, None)["too_short"], False)

    # the boundary applied to a whole run: a healthy run at 30 frames stays PASS ...
    healthy = clean_run(8)
    for r in healthy:
        r["frame_budget"] = {"achieved_delta": 30, "action_frames": 30}
        r["control_diff"] = {"frame_budget": {"achieved_delta": 30}}
    s_healthy = summarise(healthy, "jev", "pong")
    check("window: a run measured at 30 frames is a normal PASS", s_healthy["verdict"], "PASS")
    check("window: ... and counts as a pass", s_healthy["counts_as_pass"], True)

    # ... and the SAME run at 3 frames is NOT a PASS.
    short = [dict(r) for r in healthy]
    for r in short:
        r["frame_budget"] = {"achieved_delta": 3, "action_frames": 3}
    s_short = summarise(short, "jev", "pong")
    check("window: the same run at 3 frames is WINDOW_TOO_SHORT",
          "WINDOW_TOO_SHORT" in s_short["verdict"], True)
    check("window: ... and does NOT count as a pass", s_short["counts_as_pass"], False)
    check("window: ... the underlying verdict is preserved beside it",
          s_short["verdict_before_window_check"], "PASS")
    check("window: ... the offending steps are named",
          s_short["window_too_short_steps"], list(range(1, 9)))
    check("window: the gate-side reading agrees the shorter run is not a pass",
          "WINDOW_TOO_SHORT" in evaluate_model_player_steps(short, "pong")["verdict"], True)
    check("gate window: the raw verdict is preserved",
          evaluate_model_player_steps(short, "pong")["verdict_before_window_check"], "PASS")

    # ---- §1.B: the legal-refusal predicate reads the GAME's own counter -------------------
    check("refusal: the game's counter is read from the state delta",
          bool(step_refusal_record({"state_delta": [
              {"key": "/root/Main.RejectedMoves", "from": 0, "to": 1}]}, decl)), True)
    check("refusal: an unrelated change is NOT a refusal",
          step_refusal_record({"state_delta": [
              {"key": "/root/Main.Ticks", "from": 0, "to": 1}]}, decl), None)
    check("refusal: a refusal key that did not move is NOT a refusal",
          step_refusal_record({"state_delta": [
              {"key": "/root/Main.RejectedMoves", "from": 1, "to": 1}]}, decl), None)

    # TASK-139 §1.B: the evidence STRING must name the game's own exported COUNTER.  The
    # motivating measurement is `t139-scripted-w30/match3/scripted` step 2, whose delta
    # carries BOTH `InputRejectedSwaps 0->1` (the declared counter) and
    # `LastEvent 'reset' -> 'rejected reason=no_match ...'` (a free-text field that also
    # matched the broad `Rejected` pattern).  The counter is what the declaration names, so
    # the counter is what the record must say.
    decl_exact = {"keys": ["Rejected", "RejectedMoves", "InputRejectedSwaps"],
                  "value_words": [], "game_side_fields": ["InputRejectedSwaps",
                                                          "RejectedMoves"],
                  "declared_by": "TASK-131 X12 (carve-out); TASK-139 §1.B"}
    mixed_delta = [{"key": "/root/Main.InputRejectedSwaps", "from": 0, "to": 1},
                   {"key": "/root/Main.LastEvent", "from": "reset",
                    "to": "rejected reason=no_match from=4,5 to=4,6 rejected=1"},
                   {"key": "/root/Main.RejectedMoves", "from": 0, "to": 1}]
    rr = step_refusal_record({"state_delta": mixed_delta}, decl_exact)
    check("refusal: the evidence names the declared COUNTER, not a free-text field",
          rr["game_side_counter"], "/root/Main.InputRejectedSwaps")
    check("refusal: the evidence string is the counter's before -> after",
          rr["refusal_evidence"], "/root/Main.InputRejectedSwaps: 0 -> 1")
    check("refusal: every declared counter that moved is listed",
          rr["game_side_counters_moved"],
          ["/root/Main.InputRejectedSwaps", "/root/Main.RejectedMoves"])
    # a game that declares NO exact counter still gets the broad-pattern behaviour
    rr2 = step_refusal_record({"state_delta": mixed_delta}, {"keys": ["Rejected"]})
    check("refusal: without game_side_fields the broad keys still work",
          bool(rr2), True)

    # ---- §1.B (i): "refused AND really progressing" CAN pass (if progress is enough) -------
    mixed = []
    for i in range(1, 9):
        if i % 2 == 0:
            mixed.append(refusal_step(i, "swap", changed=False))
        else:
            r = step(i, "move%d" % i, "frame%d" % i, changed=True)
            mixed.append(r)
    s_mix = summarise(mixed, "jev", "match3")
    check("refusal+progress: the run is a PASS", s_mix["verdict"], "PASS")
    check("refusal+progress: it counts as a pass", s_mix["counts_as_pass"], True)
    check("refusal+progress: the refused steps are named",
          s_mix["refused_steps"], [2, 4, 6, 8])
    check("refusal+progress: they are NOT in the FAIL set", s_mix["fail_steps"], [])
    check("refusal+progress: the raw FAIL set is preserved beside it",
          s_mix["fail_steps_before_refusal_carve_out"], [2, 4, 6, 8])
    check("refusal+progress: the rated denominator excludes them",
          s_mix["rated_step_count"], 4)
    check("refusal+progress: the rate is over the rated steps",
          s_mix["rated_and_changed_rate"], 1.0)
    check("refusal+progress: refusals are NOT counted as real progress",
          s_mix["real_progress_steps"], [1, 3, 5, 7])
    check("refusal+progress: it is not a refusal-only run",
          s_mix["refusal_only_run"], False)

    # the gate must reach the SAME verdict on the same records
    ev_mix = evaluate_model_player_steps(mixed, "match3")
    check("gate agrees: refusal+progress is a PASS", ev_mix["verdict"], "PASS")
    check("gate agrees: the refused steps", ev_mix["refused_steps"], [2, 4, 6, 8])
    check("gate agrees: they are dropped from the FAIL set", ev_mix["fail_steps"], [])
    check("gate agrees: real progress excludes them",
          ev_mix["real_progress_steps"], [1, 3, 5, 7])
    check("gate agrees: counts_as_pass", ev_mix["counts_as_pass"], True)

    # ---- §1.B (ii): "refused everywhere, zero progress" MUST NOT pass ----------------------
    # Varied actions AND varied frames so the model-side fixed-point clauses are NOT the
    # reason it fails: the REFUSAL boundary alone has to refuse this run.
    only_ref = [refusal_step(i, "act%d" % ((i % 3) + 1)) for i in range(1, 9)]
    s_ref = summarise(only_ref, "jev", "match3")
    check("all-refused: the verdict is NOT a PASS", s_ref["verdict"] == "PASS", False)
    check("all-refused: the verdict is FAIL", s_ref["verdict"], "FAIL")
    check("all-refused: counts_as_pass is false", s_ref["counts_as_pass"], False)
    check("all-refused: every step is a refused step",
          s_ref["refused_steps"], list(range(1, 9)))
    check("all-refused: zero rated steps remain", s_ref["rated_step_count"], 0)
    check("all-refused: zero real progress steps", s_ref["real_progress_step_count"], 0)
    check("all-refused: it is flagged as a refusal-only run",
          s_ref["refusal_only_run"], True)
    check("all-refused: no model fixed point is claimed (the actions differ)",
          s_ref["MODEL_FIXED_POINT"], False)
    check("all-refused: the why names the boundary",
          "refuses everything" in s_ref["why"] or "refusal" in s_ref["why"], True)

    ev_ref = evaluate_model_player_steps(only_ref, "match3")
    check("gate: all-refused is NOT a PASS", ev_ref["verdict"] == "PASS", False)
    check("gate: all-refused verdict is FAIL", ev_ref["verdict"], "FAIL")
    check("gate: all-refused counts_as_pass is false", ev_ref["counts_as_pass"], False)
    check("gate: all-refused real progress is zero",
          ev_ref["real_progress_step_count"], 0)

    # ---- §1.B (iii): refusals but too little progress -> INCONCLUSIVE, never PASS ----------
    few = []
    for i in range(1, 9):
        if i <= 6:
            few.append(refusal_step(i, "swap"))
        else:
            few.append(step(i, "go%d" % i, "frame%d" % i, changed=True))
    s_few = summarise(few, "jev", "sokoban")
    check("mostly-refused: not a PASS", s_few["verdict"] == "PASS", False)
    check("mostly-refused: INCONCLUSIVE (too little real progress)",
          s_few["verdict"], "INCONCLUSIVE")
    check("mostly-refused: real progress is 2", s_few["real_progress_step_count"], 2)

    # ---- §1.B (iv): a run with NO refusals is byte-for-byte the old reading ----------------
    plain = clean_run(8)
    s_plain = summarise(plain, "jev", "pong")
    check("no refusals: refused_step_count is 0", s_plain["refused_step_count"], 0)
    check("no refusals: the FAIL set is the raw set",
          s_plain["fail_steps"], s_plain["fail_steps_before_refusal_carve_out"])
    check("no refusals: the rate has the full denominator", s_plain["rated_step_count"], 8)
    check("no refusals: still a plain PASS", s_plain["verdict"], "PASS")

    # THE FLOOR MAY NOT TOUCH A RUN WITH ZERO REFUSALS.  `t139-scripted` measured scripted
    # runs that were PASS with as few as 2 changed steps; gating those on
    # `min_real_progress_steps` would TIGHTEN a criterion this batch promised only to make
    # fairer ("不许放宽判据" cuts both ways: it also forbids an unrelated tightening).
    thin = []
    for i in range(1, 9):
        thin.append(step(i, "act%d" % i, "frame%d" % i, changed=(i <= 2)))
    s_thin = summarise(thin, "jev", "pong")
    check("zero refusals: the floor does NOT apply (real progress 2 < 4)", s_thin["verdict"] ==
          "INCONCLUSIVE", False)
    check("zero refusals: the verdict is the rate's own FAIL", s_thin["verdict"], "FAIL")
    check("zero refusals: real progress is reported anyway",
          s_thin["real_progress_step_count"], 2)
    ev_thin = evaluate_model_player_steps(thin, "pong")
    check("gate: the floor does not apply with zero refusals either",
          ev_thin["verdict"], "FAIL")
    check("... but the floor DOES apply once a refusal removed a denominator step",
          s_few["real_progress_step_count"] < 4 and bool(s_few["refused_steps"]), True)

    # ---- the boundary is declared, not hard-coded -----------------------------------------
    b = load_refusal_boundary()
    check("boundary: the floor is declared", isinstance(b["min_real_progress_steps"], int),
          True)
    check("boundary: the floor carries a basis", bool(b.get("basis")), True)
    check("boundary: the floor is at least half the minimum step count",
          b["min_real_progress_steps"] >= 4, True)
    check("boundary: the floor is below what a no-refusal PASS already shows (>= 6)",
          b["min_real_progress_steps"] < 6, True)

    ok = True
    for good, name, detail in cases:
        ok = ok and good
        print("%-58s %s%s" % (name[:58], "OK" if good else "MISMATCH",
                              "" if good else "  " + detail))
    print("task139_cases %s (%d assertions)" % ("PASSED" if ok else "FAILED", len(cases)))
    return 0 if ok else 1


def test_task139_window_and_refusal():
    assert task139_cases() == 0


def test_model_player_rules():
    assert main() == 0


if __name__ == "__main__":
    sys.exit(task139_cases() or main())
