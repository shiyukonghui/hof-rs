#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""playjev_visual_calibrate.py -- TASK-129 C/V6/D: fit and audit the VISION threshold.

What it consumes (all produced by `tools/playability_gate.py --visual-agent=playjev`)
-------------------------------------------------------------------------------------
    runs\\playability\\t129-pos\\<game>\\playjev.json     20 fixed games (positives)
    runs\\playability\\negatives\\<neg_*>\\playjev.json    4 declared failure modes (negatives)
and, read-only, for the comparisons the task asks for:
    runs\\playability\\playjev-probe.json   TASK-127's DERIVED negative frames
    runs\\playability\\playability.json     TASK-116's fixed-game gate results (history)
    runs\\playability\\agent-jev-neg\\playability.json  TASK-128's pre-fix export results

What it computes
----------------
1. the `playable` distribution per class, per FRAME and per GAME (the gate's rule is "every
   used frame must clear the threshold", so the per-game value is the minimum);
2. a threshold sweep that counts BOTH error kinds at both granularities -- a false alarm
   (a fixed game called unplayable) and a miss (a declared-broken variant called playable)
   are counted apart because they cost different things;
3. the comparison with the TASK-127 derived-frame anchors (black / flat / content-missing);
4. the `score` observation's direction on REAL frames and the flip-legend probe result
   (declared, never in the decision path);
5. the conflict matrix: PlayJev vision vs Jev state vs P1..P6 machine vs the historical
   TASK-116/128 conclusion, with every disagreement named.

It does NOT write `uncalibrated: false`.  A separation fit on a few dozen frames is not a
probability calibration; there is no NLL/Brier/ECE here and the report says so.

Usage
-----
    python tools\\playjev_visual_calibrate.py
        --pos-root runs\\playability\\t129-pos
        --neg-root runs\\playability\\negatives
        --out runs\\playability\\t129-playjev-fit.json

Iron rules: no shell redirect, read-only over the run roots, no network.
"""

from __future__ import print_function

import argparse
import io
import json
import os
import sys
import time

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
RUNS = os.path.join(ROOT, "runs", "playability")

# The negative variants are DECLARED broken (three of them are engine-declared failures,
# `neg_hud_missing` is declared as a blind spot).  The LABEL used for the error counts is
# not "we said so" though -- it is the machine gate's P1..P6 verdict on that artifact, which
# is exactly how TASK-128 labelled its negative set (`dist/exe-task109-pre-fix`: the exports
# the gate really judged not_playable; the four it judged playable were excluded).  The
# declared construction is kept in every row, so the two can be compared rather than merged.
NEGATIVE_LABEL = {
    "neg_input_dead": "broken-by-construction: input path disabled (PollInput=false)",
    "neg_black_screen": "broken-by-construction: nothing is rendered (root invisible)",
    "neg_frozen": "broken-by-construction: game loop disabled (process_mode=4)",
    "neg_hud_missing": "degraded: HUD removed, game logic intact (declared gate blind spot)",
}


def expected_playable_for(row, cls):
    """The label a sample is counted under.

    Positives: the fixed games, which TASK-116 fixed and this run re-measured -> playable.
    Negatives: the machine gate's own verdict on THAT artifact (D-A: the exported artifact
    is the authority for "what the player gets"; for a project-tree copy, the same gate on
    the same copy).  A "negative" the gate calls playable is therefore NOT counted as a miss
    -- it is a sample whose breakage the machine cannot see, and it is reported as such.
    """
    if cls == "positive":
        return True, "fixed game (TASK-116) re-measured by this run"
    return (row["machine_verdict"] == "playable",
            "machine P1..P6 verdict on this artifact (%s)" % row["machine_verdict"])



# ---------------------------------------------------------------------------
def read_json(path):
    if not os.path.isfile(path):
        return None
    try:
        with io.open(path, encoding="utf-8") as fh:
            return json.load(fh)
    except Exception:  # noqa: BLE001
        return None


def describe(xs):
    vals = sorted(x for x in (xs or []) if isinstance(x, (int, float)))
    if not vals:
        return {"n": 0, "min": None, "max": None, "median": None, "mean": None, "values": []}
    n = len(vals)
    med = vals[n // 2] if n % 2 else 0.5 * (vals[n // 2 - 1] + vals[n // 2])
    return {"n": n, "min": vals[0], "max": vals[-1], "median": med,
            "mean": sum(vals) / float(n), "values": vals}


def load_classes(pos_root, neg_roots):
    """-> {"positive": [game rows], "negative": [game rows from every negative root]}"""
    out = {"positive": [], "negative": []}
    jobs = [("positive", pos_root)]
    for r in (neg_roots if isinstance(neg_roots, (list, tuple)) else [neg_roots]):
        if r:
            jobs.append(("negative", r))
    for cls, root in jobs:
        if not os.path.isdir(root):
            continue
        for game in sorted(os.listdir(root)):
            pj = read_json(os.path.join(root, game, "playjev.json"))
            if not pj or not pj.get("observations"):
                continue
            gate = read_json(os.path.join(root, game, "gate.json")) or {}
            agent = read_json(os.path.join(root, game, "agent.json")) or {}
            crit = gate.get("criteria") or {}
            frames = []
            for o in pj["observations"]:
                frames.append({
                    "label": o.get("frame_label"),
                    "sha256": o.get("frame_sha256"),
                    "file": o.get("frame_file"),
                    "playable": o.get("playable"),
                    "score": (o.get("score_observation") or {}).get("values", {}).get(
                        pj.get("score_observation", {}).get("score_key") or "brokenness"),
                    "abstain": o.get("abstain"),
                    "http_status": o.get("http_status"),
                    "confidence": ((o.get("questions") or {}).get(
                        pj.get("playable_key") or "playable") or {}).get("confidence"),
                    "model": o.get("model"),
                })
            vals = [f["playable"] for f in frames if isinstance(f["playable"], (int, float))]
            machine_verdict = ("playable" if all(
                (crit.get(k) or {}).get("pass") for k in ("P1", "P2", "P3", "P4",
                                                          "P5", "P6")) else "not_playable")
            row = {
                "class": cls,
                "game": game,
                "root": root,
                "label": NEGATIVE_LABEL.get(game),
                "declared_broken_by_construction": (cls == "negative"
                                                    and game in NEGATIVE_LABEL),
                "frames": frames,
                "frame_count": len(frames),
                "distinct_frame_sha256": len(set(f["sha256"] for f in frames if f.get("sha256"))),
                "playable_values": vals,
                "playable_min": min(vals) if vals else None,
                "playable_max": max(vals) if vals else None,
                "playable_mean": (sum(vals) / float(len(vals))) if vals else None,
                "score_values": [f["score"] for f in frames
                                 if isinstance(f["score"], (int, float))],
                "abstained_frames": [f["label"] for f in frames if f["abstain"]],
                "visual_verdict": pj.get("verdict"),
                "visual_sample_size": pj.get("visual_sample_size"),
                "visual_frame_selection_note": pj.get("frame_selection_note"),
                "legend_probe": pj.get("legend_probe"),
                "machine_verdict": machine_verdict,
                "machine_failed": [k for k in ("P1", "P2", "P3", "P4", "P5", "P6")
                                   if not (crit.get(k) or {}).get("pass")],
                "machine_why": dict((k, (crit.get(k) or {}).get("why"))
                                    for k in ("P1", "P2", "P3", "P4", "P5", "P6")),
                "jev_sample_size": agent.get("sample_size"),
                "jev_threshold_verdict": agent.get("threshold_verdict"),
                "jev_observations": [],
            }
            row["expected_playable"], row["label_source"] = expected_playable_for(row, cls)
            out[cls].append(row)
    return out


def sweep(classes, prior=0.5):
    """Count both error kinds at both granularities over every observed boundary."""
    pos_frames, neg_frames = [], []
    pos_games, neg_games = [], []
    for r in classes["positive"]:
        for v in r["playable_values"]:
            pos_frames.append((r["game"], v))
        if r["playable_min"] is not None:
            pos_games.append((r["game"], r["playable_min"]))
    for r in classes["negative"]:
        if r["expected_playable"]:
            continue          # declared degraded-but-playable: not a negative for errors
        for v in r["playable_values"]:
            neg_frames.append((r["game"], v))
        if r["playable_min"] is not None:
            neg_games.append((r["game"], r["playable_min"]))
    cands = sorted(set([v for _g, v in pos_frames] + [v for _g, v in neg_frames] + [prior]))
    rows = []
    for t in cands:
        pf = sorted(set(g for g, v in pos_frames if v < t))
        nfp = sorted(set(g for g, v in neg_frames if v >= t))
        pg = sorted(set(g for g, v in pos_games if v < t))
        ngp = sorted(set(g for g, v in neg_games if v >= t))
        rows.append({"t": t,
                     "pos_frames_below": len([1 for _g, v in pos_frames if v < t]),
                     "neg_frames_at_or_above": len([1 for _g, v in neg_frames if v >= t]),
                     "frame_errors": len([1 for _g, v in pos_frames if v < t])
                                     + len([1 for _g, v in neg_frames if v >= t]),
                     "pos_games_below": pg, "neg_games_at_or_above": ngp,
                     "game_errors": len(pg) + len(ngp),
                     "pos_frames_below_games": pf,
                     "neg_frames_at_or_above_games": nfp})
    return {"candidates": cands, "rows": rows,
            "positive_frames": pos_frames, "negative_frames": neg_frames,
            "positive_games": pos_games, "negative_games": neg_games}


def choose(fit, prior=0.5):
    """The joint minimum by GAME errors, ties broken towards the prior, then the wide gap."""
    rows = fit["rows"]
    if not rows:
        return {"playable_min_p_true": prior, "why": "no observations: the prior is kept"}
    best = min(r["game_errors"] for r in rows)
    ties = [r for r in rows if r["game_errors"] == best]
    ties.sort(key=lambda r: (abs(r["t"] - prior), r["frame_errors"]))
    chosen = ties[0]
    fbest = min(r["frame_errors"] for r in rows)
    ftie = min((r for r in rows if r["frame_errors"] == fbest),
               key=lambda r: (abs(r["t"] - prior), r["game_errors"]))
    return {"playable_min_p_true": round(chosen["t"], 6),
            "game_error_minimum": best,
            "chosen": chosen,
            "all_game_error_ties": [{"t": r["t"], "game_errors": r["game_errors"],
                                     "frame_errors": r["frame_errors"]} for r in ties],
            "frame_error_minimum": fbest,
            "frame_optimum": {"t": ftie["t"], "frame_errors": ftie["frame_errors"],
                              "game_errors": ftie["game_errors"]},
            "prior": prior,
            "why": ("the game-level error minimum (%d); ties are broken towards the prior "
                    "%.3f, then by the frame-level errors.  The frame-level minimum is "
                    "reported separately because the gate's rule (every frame must clear "
                    "the threshold) makes the game-level minimum the operative one."
                    % (best, prior))}


def derived_anchor(probe_path):
    """TASK-127's derived frames -> the same `playable` number, for the comparison."""
    doc = read_json(probe_path)
    if not doc:
        return {"available": False, "path": probe_path}
    out = {"available": True, "path": probe_path,
           "kind": "DERIVED frames (a real capture repainted: every pixel zeroed / the "
                   "background colour / the content bbox painted over) -- NOT frames of a "
                   "running broken game, and TASK-129 replaces them with the real ones",
           "samples": []}
    for s in doc.get("samples") or []:
        crit = {c.get("id"): c for c in ((s.get("verdict") or {}).get("criteria") or [])}
        prov = s.get("provenance") or {}
        out["samples"].append({
            "sample": s.get("sample"),
            "kind": prov.get("kind"),
            "recipe": prov.get("recipe"),
            "playable": (crit.get("noul:playable_frame") or {}).get("value"),
            "score": (crit.get("score:brokenness") or {}).get("value"),
            "is_negative": prov.get("kind") == "derived"})
    return out


def score_direction(classes, derived):
    """Is the expected breakage level inverted on REAL frames, as TASK-127 saw on derived?"""
    pos = describe([v for r in classes["positive"] for v in r["score_values"]])
    neg = describe([v for r in classes["negative"] if not r["expected_playable"]
                    for v in r["score_values"]])
    dpos = describe([s["score"] for s in derived.get("samples", []) if not s["is_negative"]])
    dneg = describe([s["score"] for s in derived.get("samples", []) if s["is_negative"]])
    inverted_real = (pos["median"] is not None and neg["median"] is not None
                     and pos["median"] < neg["median"])
    inverted_derived = (dpos["median"] is not None and dneg["median"] is not None
                        and dpos["median"] < dneg["median"])
    return {"in_decision_path": False, "direction": "suspect", "uncalibrated": True,
            "positive_real_frames": pos, "negative_real_frames": neg,
            "derived_positive_frames": dpos, "derived_negative_frames": dneg,
            "lower_is_better_legend": "1 = fully working .. 5 = unusable",
            "inverted_on_real_frames": inverted_real,
            "inverted_on_derived_frames": inverted_derived,
            "reading": ("A WORKING frame should score LOWER than a broken one. "
                        "`inverted_*` true means the measured order is the wrong way "
                        "round, which is why D-E keeps this number out of the verdict.")}


def legend_probe_summary(classes):
    rows = []
    for cls in ("positive", "negative"):
        for r in classes[cls]:
            lp = r.get("legend_probe") or {}
            if not lp:
                continue
            frames = r["frames"]
            normal = next((f["score"] for f in frames
                           if f.get("label") == lp.get("frame_label")), None)
            rows.append({"class": cls, "game": r["game"],
                         "frame_label": lp.get("frame_label"),
                         "score_normal_legend": normal,
                         "score_flipped_legend": lp.get("score_with_flipped_legend"),
                         "playable_in_flipped_request": lp.get("playable_flipped_run"),
                         "playable_normal": r["frames"][0]["playable"] if frames else None,
                         "in_decision_path": False})
    deltas = [abs(x["score_normal_legend"] - x["score_flipped_legend"])
              for x in rows if isinstance(x["score_normal_legend"], (int, float))
              and isinstance(x["score_flipped_legend"], (int, float))]
    # The two hypotheses, stated as arithmetic on a 1..5 legend:
    #   * the answer follows the LABELS  -> flipped == normal
    #   * the answer follows the SLOTS   -> flipped == 6 - normal (the mirror of the level)
    mirrors = [{"game": x["game"],
                "mirror_of_normal": (6.0 - x["score_normal_legend"])
                if isinstance(x["score_normal_legend"], (int, float)) else None,
                "score_flipped_legend": x["score_flipped_legend"],
                "delta_from_mirror": (x["score_flipped_legend"]
                                      - (6.0 - x["score_normal_legend"]))
                if isinstance(x["score_normal_legend"], (int, float))
                and isinstance(x["score_flipped_legend"], (int, float)) else None}
               for x in rows]
    from_mirror = [abs(m["delta_from_mirror"]) for m in mirrors
                   if isinstance(m["delta_from_mirror"], (int, float))]
    playable_same = [x for x in rows
                     if x["playable_normal"] == x["playable_in_flipped_request"]]
    return {"declared_probe": True, "in_decision_path": False,
            "purpose": "does the SAME frame get a different expected level when the option "
                       "order is reversed?  Two hypotheses, both checkable arithmetically: "
                       "the answer follows the LABELS (flipped == normal) or it follows the "
                       "option SLOTS (flipped == 6 - normal).",
            "rows": rows, "abs_delta": describe(deltas),
            "mirror_analysis": {"rows": mirrors,
                                "abs_delta_from_mirror": describe(from_mirror)},
            "playable_question_unchanged_under_the_flip":
                {"n": len(playable_same), "of": len(rows)},
            "reading": ("|flipped - normal| ~ 0 means the score reads the labels and the "
                        "reversal is not an artefact; |flipped - (6-normal)| ~ 0 means the "
                        "answer follows the option ORDER, so the number is a slot "
                        "preference and the measured direction is at least partly an "
                        "artefact of the legend.  Neither reading enters the verdict "
                        "(TASK-129 D-E).")}


def history_verdicts():
    """TASK-116 / TASK-128's recorded conclusions, as the `history` column."""
    hist = {}
    fixed = read_json(os.path.join(RUNS, "playability.json")) or {}
    for g in fixed.get("games") or []:
        hist[g.get("game")] = {"source": "runs/playability/playability.json (TASK-116/128 "
                                         "fixed project tree)",
                               "verdict": g.get("verdict")}
    prefix = read_json(os.path.join(RUNS, "agent-jev-neg", "playability.json")) or {}
    for g in prefix.get("games") or []:
        hist["pre-fix:" + str(g.get("game"))] = {
            "source": "runs/playability/agent-jev-neg/playability.json (TASK-128 pre-fix export)",
            "verdict": g.get("verdict")}
    return hist


def conflict_matrix(classes, hist):
    rows = []
    for cls in ("positive", "negative"):
        for r in classes[cls]:
            jv = r.get("jev_threshold_verdict") or {}
            pj = r.get("visual_verdict") or {}
            rows.append({
                "game": r["game"], "class": cls,
                "declared": r.get("label") or "fixed game (TASK-116: playable)",
                "expected_playable": r["expected_playable"],
                "label_source": r["label_source"],
                "machine_P1_P6": r["machine_verdict"],
                "machine_failed": r["machine_failed"],
                "jev_state_verdict": (jv.get("pass") if jv else None),
                "jev_rule": jv.get("rule") or (jv.get("thresholds") or {}),
                "playjev_vision_verdict": pj.get("pass"),
                "playjev_rule": (r.get("playable_min"), ),
                "playjev_worst_playable": pj.get("worst_playable"),
                "history": hist.get(r["game"], {}).get("verdict")
                           or hist.get("pre-fix:" + r["game"], {}).get("verdict"),
            })
    conflicts = []
    for row in rows:
        expected_playable = (row["class"] == "positive"
                             or row["expected_playable"])
        if row["playjev_vision_verdict"] is not None \
                and bool(row["playjev_vision_verdict"]) != bool(expected_playable):
            conflicts.append({"game": row["game"], "who": "playjev",
                              "kind": "false alarm" if expected_playable else "miss",
                              "detail": "vision says %s, the label says %s"
                                        % (row["playjev_vision_verdict"],
                                           "playable" if expected_playable else "broken")})
        if row["machine_P1_P6"] != ("playable" if expected_playable else "not_playable"):
            conflicts.append({"game": row["game"], "who": "P1..P6",
                              "kind": "false alarm" if expected_playable else "miss",
                              "detail": "machine says %s (failed %s)"
                                        % (row["machine_P1_P6"], row["machine_failed"])})
    return {"rows": rows, "conflicts": conflicts,
            "note": "every disagreement is listed; the model's semantic boundary (it judges "
                    "whether a FRAME/state looks playable, not whether the game logic is "
                    "correct or fun) is recorded in the report"}


def jev_multistate(classes, prior_t=0.25):
    """TASK-129 V1/D-B: what the TEXT backend's >= 3 independent states look like.

    Reads `agent.json -> observations[*].threshold_verdict.criteria`, i.e. the noul answers
    of EVERY call with the state it was given -- the thing TASK-128 could not measure
    because all three calls shared one state.  The sweep is the same rule TASK-128 fitted
    (`noul_min_p_true`), re-run on per-OBSERVATION values instead of per-game last calls.
    """
    rows = []
    for cls in ("positive", "negative"):
        for r in classes[cls]:
            agent = read_json(os.path.join(r["root"], r["game"], "agent.json")) or {}
            obs = []
            for ob in agent.get("observations") or []:
                crit = (ob.get("threshold_verdict") or {}).get("criteria") or []
                vals = dict((str(c.get("id")).split(":", 1)[1], c.get("value"))
                            for c in crit
                            if str(c.get("id", "")).startswith("noul:")
                            and isinstance(c.get("value"), (int, float)))
                if vals:
                    obs.append({"state_label": ob.get("state_label"),
                                "state_sha256": ob.get("state_sha256"),
                                "noul": vals, "min_noul": min(vals.values())})
            rows.append({"class": cls, "game": r["game"], "root": r["root"],
                         "expected_playable": r["expected_playable"],
                         "sample_size": agent.get("sample_size"),
                         "sample_size_required": agent.get("sample_size_required"),
                         "sample_size_is_independent": agent.get("sample_size_is_independent"),
                         "state_retries": [len((ob.get("evidence") or {})
                                               .get("state_budget_retries") or [])
                                           for ob in (agent.get("observations") or [])],
                         "observations": obs})
    pos = [(r["game"], o["min_noul"]) for r in rows if r["class"] == "positive"
           for o in r["observations"]]
    neg = [(r["game"], o["min_noul"]) for r in rows
           if r["class"] == "negative" and not r["expected_playable"]
           for o in r["observations"]]
    cands = sorted(set([v for _g, v in pos] + [v for _g, v in neg] + [prior_t]))
    srows = [{"t": t,
              "pos_below": len([1 for _g, v in pos if v < t]),
              "neg_at_or_above": len([1 for _g, v in neg if v >= t]),
              "errors": len([1 for _g, v in pos if v < t]) + len([1 for _g, v in neg if v >= t]),
              "pos_fail_games": sorted(set(g for g, v in pos if v < t)),
              "neg_pass_games": sorted(set(g for g, v in neg if v >= t))}
             for t in cands]
    # the operative aggregate once the gate really samples several states: a game is
    # playable only if EVERY sampled state passes -> the worst observation per game.
    pos_w, neg_w = [], []
    for r in rows:
        mins = [o["min_noul"] for o in r["observations"]
                if isinstance(o["min_noul"], (int, float))]
        if not mins:
            continue
        (pos_w if r["expected_playable"] else neg_w).append((r["game"], min(mins)))
    wc = sorted(set([v for _g, v in pos_w] + [v for _g, v in neg_w] + [prior_t]))
    wrows = [{"t": t,
              "pos_games_below": sorted(set(g for g, v in pos_w if v < t)),
              "neg_games_at_or_above": sorted(set(g for g, v in neg_w if v >= t)),
              "errors": len(set(g for g, v in pos_w if v < t))
                        + len(set(g for g, v in neg_w if v >= t))}
             for t in wc]
    return {"rule": "noul_min_p_true: every noul P(true) >= t",
            "per_game": rows,
            "positive_observations": describe([v for _g, v in pos]),
            "negative_observations": describe([v for _g, v in neg]),
            "sweep": srows,
            "game_worst_case": {
                "rule": "a game passes only if EVERY sampled state passes (min over "
                        "observations); this is what gate.agent.aggregate_over_observations "
                        "records",
                "positive_games": describe([v for _g, v in pos_w]),
                "negative_games": describe([v for _g, v in neg_w]),
                "sweep": wrows,
                "best": (min(wrows, key=lambda r: (r["errors"], abs(r["t"] - prior_t)))
                         if wrows else None)},
            "task128_threshold": prior_t,
            "at_task128_threshold": next((r for r in srows if abs(r["t"] - prior_t) < 1e-9),
                                         None),
            "at_task128_threshold_worst_case": next(
                (r for r in wrows if abs(r["t"] - prior_t) < 1e-9), None),
            "note": ("TASK-128 fitted 0.25 on ONE observation per game (the last call, which "
                     "was the POST-INPUT state -- the highest-noul phase).  Here the same "
                     "rule is evaluated on EVERY independent state and on the worst-case "
                     "aggregate, so the sample is larger and the two classes can overlap "
                     "differently.  The value in tools/playability_controls.json is changed "
                     "only if the re-run shows it should be; the report records both.")}


def main(argv=None):
    ap = argparse.ArgumentParser(description="TASK-129 vision-threshold fit")
    ap.add_argument("--pos-root", default=os.path.join(RUNS, "t129-pos"))
    ap.add_argument("--neg-root", nargs="*", default=[os.path.join(RUNS, "negatives")],
                    help="one or more roots of negative samples.  Two sets are kept apart "
                         "in the report: the four DECLARED variants "
                         "(runs/playability/negatives) and the pre-fix EXPORTED artifacts "
                         "(runs/playability/t129-neg-exe), which are D-A's authority for "
                         "'what the player gets'.")
    ap.add_argument("--derived-probe", default=os.path.join(RUNS, "playjev-probe.json"))
    ap.add_argument("--out", default=os.path.join(RUNS, "t129-playjev-fit.json"))
    ap.add_argument("--prior", type=float, default=0.5)
    args = ap.parse_args(argv)

    classes = load_classes(args.pos_root, args.neg_root)
    fit = sweep(classes, args.prior)
    derived = derived_anchor(args.derived_probe)
    doc = {
        "task": "TASK-129 C / V6 / D",
        "generated": time.strftime("%Y-%m-%d %H:%M:%S"),
        "inputs": {"pos_root": args.pos_root, "neg_roots": args.neg_root,
                   "derived_probe": args.derived_probe},
        "questions_in_decision_path": ["playable"],
        "score_in_decision_path": False,
        "uncalibrated": True,
        "counts": {"positive_games": len(classes["positive"]),
                   "negative_variants": len(classes["negative"]),
                   "positive_frames": sum(r["frame_count"] for r in classes["positive"]),
                   "negative_frames": sum(r["frame_count"] for r in classes["negative"]),
                   "positive_distinct_frames": sum(r["distinct_frame_sha256"]
                                                   for r in classes["positive"]),
                   "negative_distinct_frames": sum(r["distinct_frame_sha256"]
                                                   for r in classes["negative"])},
        "per_game": classes["positive"] + classes["negative"],
        "distribution": {
            "positive_frames": describe([v for _g, v in fit["positive_frames"]]),
            "negative_frames": describe([v for _g, v in fit["negative_frames"]]),
            "positive_game_min": describe([v for _g, v in fit["positive_games"]]),
            "negative_game_min": describe([v for _g, v in fit["negative_games"]]),
        },
        "overlap": {},
        "sweep": {"candidates": fit["candidates"], "rows": fit["rows"]},
        "chosen": choose(fit, args.prior),
        "derived_anchor_comparison": derived,
        "score_observation": score_direction(classes, derived),
        "legend_probe": legend_probe_summary(classes),
        "conflict_matrix": conflict_matrix(classes, history_verdicts()),
        "jev_multistate_fit": jev_multistate(classes),
        "semantic_boundary": (
            "The vision backend judges ONE full-window frame: 'does this frame look like a "
            "playable game?'.  It does NOT judge whether the game's logic is correct, "
            "whether the controls are discoverable, or whether the game is fun -- and it "
            "cannot see anything that happened before or after the frame.  It is a second "
            "signal beside P1..P6, never a replacement."),
    }
    for name, pos, neg in (("frames", fit["positive_frames"], fit["negative_frames"]),
                           ("game_min", fit["positive_games"], fit["negative_games"])):
        if pos and neg:
            pmin = min(v for _g, v in pos)
            nmax = max(v for _g, v in neg)
            doc["overlap"][name] = {
                "positive_min": pmin, "negative_max": nmax, "gap": pmin - nmax,
                "separable": pmin > nmax,
                "why": ("cleanly separable" if pmin > nmax else
                        "the classes OVERLAP: no threshold separates them")}
        else:
            doc["overlap"][name] = {"separable": None, "why": "one class is empty"}

    with io.open(args.out, "w", encoding="utf-8") as fh:
        fh.write(json.dumps(doc, ensure_ascii=False, indent=1, default=str))
    print("counts      : %s" % json.dumps(doc["counts"], ensure_ascii=False))
    print("distribution: pos frames %s | neg frames %s"
          % (json.dumps(doc["distribution"]["positive_frames"]),
             json.dumps(doc["distribution"]["negative_frames"])))
    print("game minima : pos %s | neg %s"
          % (json.dumps(doc["distribution"]["positive_game_min"]),
             json.dumps(doc["distribution"]["negative_game_min"])))
    print("overlap     : %s" % json.dumps(doc["overlap"], ensure_ascii=False))
    print("chosen      : %s" % json.dumps(doc["chosen"], ensure_ascii=False))
    print("conflicts   : %d" % len(doc["conflict_matrix"]["conflicts"]))
    for c in doc["conflict_matrix"]["conflicts"]:
        print("   - %s [%s] %s" % (c["game"], c["who"], c["detail"]))
    jm = doc["jev_multistate_fit"]
    print("jev multi-state: pos %s | neg %s" % (json.dumps(jm["positive_observations"]),
                                                json.dumps(jm["negative_observations"])))
    print("jev @0.25 per-obs: %s" % json.dumps(jm["at_task128_threshold"]))
    print("jev @0.25 worst-case: %s" % json.dumps(jm["at_task128_threshold_worst_case"]))
    print("jev best worst-case: %s" % json.dumps(jm["game_worst_case"]["best"]))
    print("legend probe: median |flipped-normal| %s | median |flipped-mirror| %s"
          % (doc["legend_probe"]["abs_delta"]["median"],
             doc["legend_probe"]["mirror_analysis"]["abs_delta_from_mirror"]["median"]))
    print("written     : %s" % os.path.abspath(args.out))
    return 0


if __name__ == "__main__":
    sys.exit(main())
