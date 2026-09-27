#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""TASK-131 X12: re-score P2/P3 from RECORDED gate evidence, under both rules.

Why this exists
---------------
The before/after comparison the task asks for ("收紧前/收紧后对 20 款 + 负变体的重跑对比")
is only trustworthy if the two columns are computed from the SAME evidence.  This tool
does exactly that: it reads a `gate.json` (plus `states/00_settle.json`) written by any
past gate run, and evaluates

    * the OLD P2/P3 rules, line for line as they were before TASK-131, so the recorded
      verdict can be REPRODUCED from the record (a validation of the tool), and
    * the NEW P2/P3 rules, which are imported from `tools/playability_gate.py` -- one
      implementation, never a second copy.

Usage
-----
    python tools/playability_rescore.py --runs-root runs/playability \
        --games pong snake ... [--negatives-root runs/playability/negatives] [--json out]

Every number it prints comes from a file whose path it also prints.
"""

from __future__ import annotations

import argparse
import io
import json
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
sys.path.insert(0, HERE)

import playability_gate as pg  # noqa: E402

POSITIVES = ["asteroids", "bomberman", "breakout", "flappy", "frogger", "game2048",
             "lunarlander", "match3", "minesweeper", "missilecommand", "pacman",
             "platformer", "pong", "puzzlebobble", "rtype", "snake", "sokoban",
             "spaceinvaders", "tetris", "towerdefense"]
NEGATIVES = ["neg_input_dead", "neg_black_screen", "neg_frozen", "neg_hud_missing",
             "neg_ui_offscreen"]


def read_json(path):
    with io.open(path, encoding="utf-8") as fh:
        return json.load(fh)


def old_rules(gate):
    """The P2/P3 rules exactly as they stood before TASK-131 (frozen history)."""
    tested = gate.get("actions_tested") or []

    def arm(ch):
        ctl, act = ch.get("control") or {}, ch.get("action") or {}
        ctl_px = max(0, (ctl.get("pixels") or {}).get("changed_pixels") or 0)
        act_px = max(0, (act.get("pixels") or {}).get("changed_pixels") or 0)
        state_wins = len(act.get("state_changes") or []) > len(ctl.get("state_changes") or [])
        pixel_wins = act_px > max(int(ctl_px * 1.5), pg.P3_MIN_CHANGED_PIXELS)
        return bool(state_wins or pixel_wins)

    responds = []
    for a in tested:
        ch = a.get("channels") or {}
        ok = False
        for name in ("parse", "push_input", "action"):
            if ch.get(name):
                ok = ok or arm(ch[name])
        responds.append(ok)
    p2 = (len(tested) > 0 and all(responds))

    p3rec = (gate.get("criteria") or {}).get("P3") or {}
    drawn = [d for d in (p3rec.get("frames_drawn_samples") or []) if isinstance(d, int)]
    loop_advanced = len(drawn) >= 2 and drawn[-1] > drawn[0]
    auto_n = len(p3rec.get("autonomous_state_changes") or [])
    post_n = len(p3rec.get("total_state_changes_since_settle") or [])
    pixel_auto = p3rec.get("max_pixel_change_autonomous") or 0
    input_delta_count = 0
    for a in tested:
        for ch in (a.get("channels") or {}).values():
            input_delta_count += ((ch.get("action") or {}).get("state_change_count") or 0)
    p3 = bool(loop_advanced and (auto_n > 0 or post_n > 0
                                 or pixel_auto >= pg.P3_MIN_CHANGED_PIXELS
                                 or input_delta_count > 0))
    return {"P2": p2, "P3": p3, "responds_per_action": responds}


def new_rules(gate, controls, settle_state):
    game = gate.get("game")
    decl = pg.gameplay_declaration(controls, game)
    refdecl = pg.refusal_declaration(controls, game)
    tested = gate.get("actions_tested") or []
    evs = []
    for a in tested:
        ev = pg.arm_evidence((a.get("channels") or {}).get("parse") or {}, decl,
                            refusal_decl=refdecl)
        evs.append({"action": a.get("action"), **ev})
    responded = [e for e in evs if e["responds"]]
    intent_only = [e for e in evs if not e["responds"] and not e["refused"]]
    p2 = bool(tested) and not intent_only and bool(responded)

    liv = pg.liveness_declaration(controls, game)
    terminal = pg.terminal_conditions_met(settle_state or {}, liv)
    p3rec = (gate.get("criteria") or {}).get("P3") or {}
    drawn = [d for d in (p3rec.get("frames_drawn_samples") or []) if isinstance(d, int)]
    loop_advanced = len(drawn) >= 2 and drawn[-1] > drawn[0]
    auto = p3rec.get("autonomous_state_changes") or []
    post = p3rec.get("total_state_changes_since_settle") or []
    pixel_auto = p3rec.get("max_pixel_change_autonomous") or 0
    auto_g = pg.gameplay_changes(auto, decl) + pg.gameplay_changes(post, decl)
    autonomous_evidence = bool(auto_g) or pixel_auto >= pg.P3_MIN_CHANGED_PIXELS
    input_evidence = any(e["gameplay_wins"] or e["pixel_wins"] for e in evs)
    p3 = bool(loop_advanced and not terminal and (autonomous_evidence or input_evidence))
    return {"P2": p2, "P3": p3, "actions": evs,
            "declared_gameplay_observables": decl.get("items") or [],
            "meta_only_actions": [e["action"] for e in intent_only
                                  if e.get("meta_only")],
            "intent_only_actions": [e["action"] for e in intent_only],
            "refused_actions": [e["action"] for e in evs if e["refused"]],
            "actions_that_moved_gameplay": [e["action"] for e in responded],
            "terminal_at_settle": terminal,
            "autonomous_gameplay_changes": [c.get("key") for c in auto_g],
            "autonomous_evidence": autonomous_evidence,
            "input_round_evidence": input_evidence}


def p1_of_new_rule(gate):
    """What the NEW P1 threshold says about the recorded best settle frame."""
    p1 = (gate.get("criteria") or {}).get("P1") or {}
    bf = p1.get("best_frame") or {}
    cf = bf.get("content_fraction")
    bc = bf.get("bbox_coverage")
    if cf is None:
        return {"pass": None}
    return {"pass": bool((cf or 0) > 0
                         and cf >= pg.P1_MIN_CONTENT_FRACTION
                         and (bc or 0) >= pg.P1_MIN_BBOX_COVERAGE),
            "content_fraction": cf, "bbox_coverage": bc,
            "threshold": pg.P1_MIN_CONTENT_FRACTION}


def main(argv=None):
    ap = argparse.ArgumentParser()
    ap.add_argument("--runs-root", default=os.path.join(ROOT, "runs", "playability"))
    ap.add_argument("--negatives-root", default="")
    ap.add_argument("--games", nargs="*", default=None)
    ap.add_argument("--json", default="")
    ap.add_argument("--controls", default="")
    ap.add_argument("--extra-roots", nargs="*", default=[],
                    help="additional roots searched for <root>/<game>/gate.json, in order "
                         "after --runs-root and --negatives-root")
    args = ap.parse_args(argv)

    controls = pg.load_controls(args.controls or None)
    neg_root = args.negatives_root or os.path.join(args.runs_root, "negatives")
    want = args.games or (POSITIVES + NEGATIVES)
    rows = []
    for game in want:
        cands = [os.path.join(args.runs_root, game, "gate.json"),
                 os.path.join(neg_root, game, "gate.json")]
        cands += [os.path.join(r, game, "gate.json") for r in args.extra_roots]
        path = next((p for p in cands if os.path.isfile(p)), None)
        if not path:
            rows.append({"game": game, "error": "no gate.json found in %s" % cands})
            continue
        gate = read_json(path)
        outdir = os.path.dirname(path)
        sp = os.path.join(outdir, "states", "00_settle.json")
        settle = read_json(sp) if os.path.isfile(sp) else None
        rec = (gate.get("criteria") or {})
        o = old_rules(gate)
        n = new_rules(gate, controls, settle)
        rows.append({
            "game": game, "gate_json": path, "settle_state": sp,
            "recorded_P2": (rec.get("P2") or {}).get("pass"),
            "recorded_P3": (rec.get("P3") or {}).get("pass"),
            "recorded_P1": (rec.get("P1") or {}).get("pass"),
            "old_P2": o["P2"], "old_P3": o["P3"],
            "old_rule_reproduces_record": bool(
                o["P2"] == (rec.get("P2") or {}).get("pass")
                and o["P3"] == (rec.get("P3") or {}).get("pass")),
            "new_P2": n["P2"], "new_P3": n["P3"], "new_P1": p1_of_new_rule(gate),
            "flip_P2": (o["P2"] and not n["P2"]),
            "flip_P3": (o["P3"] and not n["P3"]),
            "flip_P1": (bool((rec.get("P1") or {}).get("pass"))
                        and p1_of_new_rule(gate).get("pass") is False),
            "meta_only_actions": n["meta_only_actions"],
            "intent_only_actions": n["intent_only_actions"],
            "refused_actions": n["refused_actions"],
            "actions_that_moved_gameplay": n["actions_that_moved_gameplay"],
            "declared_gameplay_observables": n["declared_gameplay_observables"],
            "terminal_at_settle": n["terminal_at_settle"],
            "autonomous_gameplay_changes": n["autonomous_gameplay_changes"],
            "autonomous_evidence": n["autonomous_evidence"],
            "input_round_evidence": n["input_round_evidence"],
        })

    hdr = ("%-18s %-4s %-4s | %-4s %-4s %-5s | %-5s %-5s %-5s | %s"
           % ("game", "recP2", "recP3", "oldP2", "oldP3", "repro",
              "newP2", "newP3", "newP1", "why it flipped / notes"))
    print(hdr)
    print("-" * len(hdr))
    for r in rows:
        if r.get("error"):
            print("%-18s ERROR %s" % (r["game"], r["error"]))
            continue
        note = []
        if r["flip_P2"]:
            note.append("P2 RED: intent-only=%s refused=%s moved=%s"
                        % (r["intent_only_actions"] or "-",
                           r["refused_actions"] or "-",
                           r["actions_that_moved_gameplay"] or "-"))
        if r["flip_P3"]:
            note.append("P3 RED: terminal=%s auto_ev=%s input_ev=%s"
                        % ([t["field"] for t in r["terminal_at_settle"]] or "-",
                           r["autonomous_evidence"], r["input_round_evidence"]))
        if r["flip_P1"]:
            note.append("P1 RED: content=%.4f%%"
                        % (100.0 * (r["new_P1"].get("content_fraction") or 0)))
        if not r["old_rule_reproduces_record"]:
            note.append("!! the frozen OLD rule does NOT reproduce the recorded verdict")
        print("%-18s %-4s %-4s | %-4s %-4s %-5s | %-5s %-5s %-5s | %s"
              % (r["game"], r["recorded_P2"], r["recorded_P3"], r["old_P2"], r["old_P3"],
                 r["old_rule_reproduces_record"], r["new_P2"], r["new_P3"],
                 r["new_P1"].get("pass"), "; ".join(note)))
    if args.json:
        pg.write_json(args.json, {"rows": rows,
                                  "thresholds": {"P1_MIN_CONTENT_FRACTION":
                                                 pg.P1_MIN_CONTENT_FRACTION}})
        print("wrote %s" % os.path.abspath(args.json))
    bad = [r for r in rows if r.get("error") or not r.get("old_rule_reproduces_record")]
    print("\nreproduction failures: %d" % len(bad))
    return 0


if __name__ == "__main__":
    sys.exit(main())
