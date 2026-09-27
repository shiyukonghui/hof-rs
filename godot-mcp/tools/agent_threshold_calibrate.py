#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""agent_threshold_calibrate.py -- TASK-128: fit `agent_thresholds` on our own labels.

Why this exists (the decision this file implements)
---------------------------------------------------
The vendor reports NO NLL/Brier/ECE calibration for NeoHorse-Jev and says, verbatim,
"Set thresholds on an independent dataset."  Until TASK-128 the values in
`tools/playability_controls.json` -> `agent_thresholds` were a PRIOR (`noul_min_p_true`
= 0.5, `score_max_expected` = 2.5) chosen by eye.  This tool turns that prior into a
choice that can be argued with, using the only labelled dataset we own:

    positives : the 20 fixed games, gated from the project tree
                runs\\playability\\agent-jev\\<game>\\agent.json
    negatives : the pre-fix exports whose input was disabled
                runs\\playability\\agent-jev-neg\\<game>\\agent.json

What it computes -- and what it deliberately does NOT
-----------------------------------------------------
For every question the jev backend asks it reports, per class, the full small-sample
summary (`n`, `min`, `max`, `median`, `mean`, the raw list) plus an explicit overlap
test, because with 20-odd samples a mean is not a distribution.  It then sweeps both
thresholds over the observed values and counts the misclassifications each cut would
produce.  That is a *separation* fit.

It is NOT a probability calibration.  A threshold that separates two small labelled
sets does not make `noul` a calibrated P(playable), and this tool never writes
`uncalibrated: false`: with ~20 positives and ~20 negatives an ECE would be a number
about noise.  The caller keeps that flag set.

Usage
-----
    python tools\\agent_threshold_calibrate.py
        --pos-root runs\\playability\\agent-jev
        --neg-root runs\\playability\\agent-jev-neg
        --out runs\\playability\\agent-thresholds-fit.json

Iron rules: no shell redirect (everything is a Python file handle or stdout),
no destructive command, read-only over the run roots.
"""

from __future__ import print_function

import argparse
import io
import json
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
DEFAULT_POS = os.path.join(ROOT, "runs", "playability", "agent-jev")
DEFAULT_NEG = os.path.join(ROOT, "runs", "playability", "agent-jev-neg")

# The question the backend asks whose answer is the brokenness score.  Named here so a
# rename in playtest_agent.py shows up as an empty column instead of silently fitting
# the wrong number.
FALLBACK_SCORE_KEYS = ("brokenness", "risk")


# ---------------------------------------------------------------------------
# reading
# ---------------------------------------------------------------------------
def load_agent_json(root, game):
    path = os.path.join(root, game, "agent.json")
    if not os.path.isfile(path):
        return None, {"game": game, "missing": path}
    try:
        with io.open(path, "r", encoding="utf-8") as fh:
            return json.load(fh), None
    except Exception as e:  # noqa: BLE001
        return None, {"game": game, "unreadable": path, "error": "%s: %s"
                      % (type(e).__name__, e)}


def games_in(root):
    if not os.path.isdir(root):
        return []
    return sorted(d for d in os.listdir(root)
                  if os.path.isdir(os.path.join(root, d))
                  and os.path.isfile(os.path.join(root, d, "agent.json")))


def extract(doc, game):
    """One row per model call, plus the last call the gate's verdict would use.

    A `noul` answer carries `noul` (P(true)); on `/v1/systemone` it carries neither
    `probabilities` nor `confidence` -- that is a protocol fact, not missing data, and
    the row says so rather than inventing a number.  `score` carries an ordered
    `probabilities` list and a `confidence`.
    """
    report = (doc or {}).get("report") or {}
    service = (doc or {}).get("service") or {}
    calls = []
    for c in report.get("calls") or []:
        if not isinstance(c, dict):
            continue
        noul = {}
        for key, a in (c.get("noul") or {}).items():
            if isinstance(a, dict) and isinstance(a.get("noul"), (int, float)):
                noul[key] = float(a["noul"])
        scores = {}
        score_probs = {}
        score_conf = {}
        for key, a in (c.get("scores") or {}).items():
            if not isinstance(a, dict):
                continue
            if isinstance(a.get("score"), (int, float)):
                scores[key] = float(a["score"])
            if isinstance(a.get("probabilities"), dict):
                score_probs[key] = a["probabilities"]
            if isinstance(a.get("confidence"), (int, float)):
                score_conf[key] = float(a["confidence"])
        choice = c.get("choice") or {}
        calls.append({
            "noul": noul,
            "noul_min": min(noul.values()) if noul else None,
            "scores": scores,
            "score_probabilities": score_probs,
            "score_confidences": score_conf,
            "choice": {"choice": choice.get("choice"),
                       "confidence": choice.get("confidence"),
                       "probabilities": choice.get("probabilities")},
            "status": c.get("response_status"),
            "model": c.get("model"),
            "usage": c.get("usage"),
            "seconds": (c.get("transport") or {}).get("seconds"),
            "answer_keys": sorted((c.get("answers_raw") or {}).keys()),
        })
    last = calls[-1] if calls else None
    score_value, score_key = None, None
    if last:
        for k in FALLBACK_SCORE_KEYS:
            if k in last["scores"]:
                score_value, score_key = last["scores"][k], k
                break
        if score_key is None and last["scores"]:
            score_key = sorted(last["scores"])[0]
            score_value = last["scores"][score_key]
    return {
        "game": game,
        "service": {"base_url": service.get("base_url"), "model": service.get("model"),
                    "health_status": (service.get("health") or {}).get("status")},
        "calls": calls,
        "call_count": len(calls),
        "errors": report.get("errors") or [],
        "last": last,
        "min_noul": last["noul_min"] if last else None,
        "score": score_value,
        "score_key": score_key,
        "threshold_verdict": (doc or {}).get("threshold_verdict"),
    }


# ---------------------------------------------------------------------------
# small-sample statistics, spelled out
# ---------------------------------------------------------------------------
def median(xs):
    xs = sorted(xs)
    if not xs:
        return None
    n = len(xs)
    return xs[n // 2] if n % 2 else 0.5 * (xs[n // 2 - 1] + xs[n // 2])


def describe(xs):
    xs = [x for x in xs if isinstance(x, (int, float))]
    if not xs:
        return {"n": 0, "min": None, "max": None, "median": None, "mean": None,
                "values": []}
    return {"n": len(xs), "min": min(xs), "max": max(xs), "median": median(xs),
            "mean": sum(xs) / float(len(xs)), "values": sorted(xs)}


def overlap(direction, pos, neg):
    """`direction='higher'` = a bigger number is more playable (noul).

    A clean separation is `pos.min() > neg.max()`; the gap is reported either way so
    an overlapping sample is visible as a negative gap, not smoothed away.
    """
    p = describe(pos)
    n = describe(neg)
    if not p["n"] or not n["n"]:
        return {"separable": None, "gap": None, "why": "one class is empty"}
    if direction == "higher":
        gap = p["min"] - n["max"]
    else:
        gap = n["min"] - p["max"]
    return {"separable": gap > 0, "gap": gap,
            "why": ("positives and negatives %s overlap"
                    % ("do not" if gap > 0 else "DO")),
            "pos_extreme": p["min"] if direction == "higher" else p["max"],
            "neg_extreme": n["max"] if direction == "higher" else n["min"]}


# ---------------------------------------------------------------------------
# threshold sweeps
# ---------------------------------------------------------------------------
def sweep_noul(rows, candidates):
    """`pos_fail` = a fixed game called not-playable; `neg_pass` = a broken game
    called playable.  Both are errors; they are counted apart because they cost
    different things (a false alarm wastes a human; a miss ships a broken game)."""
    out = []
    for t in candidates:
        pos_fail = [r["game"] for r in rows["pos"] if (r["min_noul"] is not None
                                                       and r["min_noul"] < t)]
        neg_pass = [r["game"] for r in rows["neg"] if (r["min_noul"] is not None
                                                       and r["min_noul"] >= t)]
        out.append({"noul_min_p_true": t, "pos_fail": len(pos_fail),
                    "neg_pass": len(neg_pass),
                    "errors": len(pos_fail) + len(neg_pass),
                    "pos_fail_games": pos_fail, "neg_pass_games": neg_pass})
    return out


def sweep_score(rows, candidates):
    out = []
    for t in candidates:
        pos_fail = [r["game"] for r in rows["pos"] if (r["score"] is not None
                                                       and r["score"] > t)]
        neg_pass = [r["game"] for r in rows["neg"] if (r["score"] is not None
                                                       and r["score"] <= t)]
        out.append({"score_max_expected": t, "pos_fail": len(pos_fail),
                    "neg_pass": len(neg_pass),
                    "errors": len(pos_fail) + len(neg_pass),
                    "pos_fail_games": pos_fail, "neg_pass_games": neg_pass})
    return out


def combine(rows, t_noul, t_score):
    """The gate's actual rule: playable iff every invariant's P(true) >= t_noul AND
    the expected brokenness <= t_score."""
    def verdict(r):
        if r["min_noul"] is None or r["score"] is None:
            return None
        return bool(r["min_noul"] >= t_noul and r["score"] <= t_score)
    pos_fail = [r["game"] for r in rows["pos"] if verdict(r) is False]
    neg_pass = [r["game"] for r in rows["neg"] if verdict(r) is True]
    undecided = ([r["game"] for r in rows["pos"] + rows["neg"] if verdict(r) is None])
    return {"noul_min_p_true": t_noul, "score_max_expected": t_score,
            "pos_fail": pos_fail, "neg_pass": neg_pass, "undecided": undecided,
            "errors": len(pos_fail) + len(neg_pass),
            "accuracy": ((len(rows["pos"]) + len(rows["neg"]) - len(pos_fail)
                          - len(neg_pass) - len(undecided))
                         / float(max(1, len(rows["pos"]) + len(rows["neg"]))))}


def sweep_joint(rows, grid_noul, grid_score, prior):
    """The two rules are NOT independent: tightening a rule that carries no signal only
    adds false alarms.  So choose the pair by the actual combined error count, and break
    ties toward the prior (fewest changed values, then smallest move)."""
    best = None
    for tn in grid_noul:
        for ts in grid_score:
            comb = combine(rows, tn, ts)
            key = (comb["errors"],
                   (0 if tn == prior[0] else 1) + (0 if ts == prior[1] else 1),
                   abs(tn - prior[0]) + abs(ts - prior[1]))
            if best is None or key < best[0]:
                best = (key, comb)
    return best[1] if best else None


def candidate_grid(values, default):
    """Every observed value, plus the prior, plus midpoints between the classes --
    a coarse grid so the printed sweep is short but still contains the optimum."""
    grid = set(default for _ in [0])
    grid.add(default)
    for v in values:
        if isinstance(v, (int, float)):
            grid.add(round(float(v), 4))
    grid = sorted(grid)
    mids = []
    for a, b in zip(grid, grid[1:]):
        mids.append(round(0.5 * (a + b), 4))
    return sorted(set(grid + mids))


# ---------------------------------------------------------------------------
def build(pos_root, neg_root, neg_exclude=()):
    pos_games = games_in(pos_root)
    neg_games = [g for g in games_in(neg_root) if g not in neg_exclude]
    excluded = [g for g in games_in(neg_root) if g in neg_exclude]
    pos, neg, problems = [], [], []
    for game in pos_games:
        doc, err = load_agent_json(pos_root, game)
        if err:
            problems.append(err)
            continue
        pos.append(extract(doc, game))
    for game in neg_games:
        doc, err = load_agent_json(neg_root, game)
        if err:
            problems.append(err)
            continue
        neg.append(extract(doc, game))
    rows = {"pos": pos, "neg": neg}

    noul_keys = sorted(set(k for r in pos + neg
                           for k in ((r["last"] or {}).get("noul") or {})))
    per_question = {}
    for key in noul_keys:
        p = [((r["last"] or {}).get("noul") or {}).get(key) for r in pos]
        n = [((r["last"] or {}).get("noul") or {}).get(key) for r in neg]
        p = [x for x in p if isinstance(x, (int, float))]
        n = [x for x in n if isinstance(x, (int, float))]
        per_question[key] = {"pos": describe(p), "neg": describe(n),
                             "overlap": overlap("higher", p, n)}

    score_keys = sorted(set(r["score_key"] for r in pos + neg if r["score_key"]))
    per_score_key = {}
    for key in score_keys:
        p, n, pc, nc = [], [], [], []
        for r in pos + neg:
            last = r["last"] or {}
            if key in (last.get("scores") or {}):
                v = last["scores"][key]
                c = (last.get("score_confidences") or {}).get(key)
                (p if r in pos else n).append(v)
                if isinstance(c, (int, float)):
                    (pc if r in pos else nc).append(c)
        per_score_key[key] = {"pos": describe(p), "neg": describe(n),
                              "overlap": overlap("lower", p, n),
                              "pos_confidence": describe(pc),
                              "neg_confidence": describe(nc)}

    noul_values = [r["min_noul"] for r in pos + neg]
    score_values = [r["score"] for r in pos + neg]
    grid_noul = candidate_grid(noul_values, 0.5)
    grid_score = candidate_grid(score_values, 2.5)
    s_noul = sweep_noul(rows, grid_noul)
    s_score = sweep_score(rows, grid_score)
    best_noul = sorted(s_noul, key=lambda x: (x["errors"], abs(x["noul_min_p_true"] - 0.5)))[0]
    best_score = sorted(s_score, key=lambda x: (x["errors"],
                                                abs(x["score_max_expected"] - 2.5)))[0]
    joint = sweep_joint(rows, grid_noul, grid_score, (0.5, 2.5))
    prior = combine(rows, 0.5, 2.5)
    # Is the score rule doing any work at the chosen noul cut?  If not, say so: a rule
    # that no negative ever trips is decoration, not evidence.
    chosen_noul = joint["noul_min_p_true"]
    score_effects = {}
    for t in (joint["score_max_expected"],):
        c = combine(rows, chosen_noul, t)
        score_effects["at_%s" % t] = {"pos_fail": c["pos_fail"], "neg_pass": c["neg_pass"]}
    score_alone = [r for r in s_score if r["errors"] == min(x["errors"] for x in s_score)]

    return {
        "roots": {"positives": pos_root, "negatives": neg_root},
        "counts": {"positives": len(pos), "negatives": len(neg),
                   "negatives_excluded": len(excluded),
                   "negatives_excluded_games": excluded,
                   "pos_unreadable": len([p for p in problems if p.get("game") in pos_games]),
                   "neg_unreadable": len([p for p in problems if p.get("game") in neg_games])},
        "problems": problems,
        "per_question_noul": per_question,
        "per_score_key": per_score_key,
        "per_game": [{"game": r["game"], "class": "pos", "min_noul": r["min_noul"],
                      "score": r["score"], "score_key": r["score_key"],
                      "calls": r["call_count"], "errors": r["errors"],
                      "service": r["service"], "noul_worst": _worst(r)} for r in pos]
                    + [{"game": r["game"], "class": "neg", "min_noul": r["min_noul"],
                        "score": r["score"], "score_key": r["score_key"],
                        "calls": r["call_count"], "errors": r["errors"],
                        "service": r["service"], "noul_worst": _worst(r)} for r in neg],
        "sweep_noul": s_noul,
        "sweep_score": s_score,
        "best_noul_alone": best_noul,
        "best_score_alone": best_score,
        "score_rule_effect": {"alone_best_errors": min(x["errors"] for x in s_score),
                              "at_chosen_noul": score_effects,
                              "score_carries_separation":
                                  min(x["errors"] for x in s_score) < len(rows["neg"])},
        "chosen": joint,
        "prior": prior,
        "calibration_statement": {
            "is_probability_calibration": False,
            "uncalibrated_remains_true": True,
            "why": ("These thresholds were chosen by SEPARATION on our own labels. "
                    "They are not a calibration of `noul`/`score`: the vendor reports "
                    "no NLL/Brier/ECE, `confidence` is a local distribution statistic, "
                    "and with ~20 positives / ~20 negatives an ECE would be noise. "
                    "The `uncalibrated: true` flag must stay set."),
            "sample_size": {"positives": len(pos), "negatives": len(neg)},
        },
    }


def _worst(r):
    last = r["last"] or {}
    noul = last.get("noul") or {}
    if not noul:
        return None
    key = min(noul, key=lambda k: noul[k])
    return {"question": key, "noul": noul[key]}


# ---------------------------------------------------------------------------
def fmt(x, nd=4):
    if x is None:
        return "-"
    if isinstance(x, float):
        return ("%%.%df" % nd) % x
    return str(x)


def report_lines(fit):
    L = []
    L.append("=== TASK-128 agent threshold fit (separation, NOT probability calibration) ===")
    L.append("positives: %s (%d games)" % (fit["roots"]["positives"],
                                           fit["counts"]["positives"]))
    L.append("negatives: %s (%d games)" % (fit["roots"]["negatives"],
                                           fit["counts"]["negatives"]))
    if fit["counts"].get("negatives_excluded_games"):
        L.append("excluded from the negative class (labelled, NOT negatives): %s"
                 % ", ".join(fit["counts"]["negatives_excluded_games"]))
    if fit["problems"]:
        L.append("problems : %s" % json.dumps(fit["problems"], ensure_ascii=False))
    L.append("")
    L.append("-- per-question noul P(true), last call of each game (what the verdict uses) --")
    L.append("%-22s %5s %8s %8s %8s | %5s %8s %8s %8s | %-6s %8s"
             % ("question", "nP", "P.min", "P.med", "P.max",
                "nN", "N.min", "N.med", "N.max", "sep?", "gap"))
    for key, v in sorted(fit["per_question_noul"].items()):
        p, n, o = v["pos"], v["neg"], v["overlap"]
        L.append("%-22s %5d %8s %8s %8s | %5d %8s %8s %8s | %-6s %8s"
                 % (key, p["n"], fmt(p["min"]), fmt(p["median"]), fmt(p["max"]),
                    n["n"], fmt(n["min"]), fmt(n["median"]), fmt(n["max"]),
                    str(o["separable"]), fmt(o["gap"])))
    L.append("")
    L.append("-- per-game brokenness score (expected level; lower is better) --")
    for key, v in sorted(fit["per_score_key"].items()):
        p, n, o = v["pos"], v["neg"], v["overlap"]
        L.append("question %r" % key)
        L.append("  pos: n=%d min=%s median=%s max=%s mean=%s"
                 % (p["n"], fmt(p["min"]), fmt(p["median"]), fmt(p["max"]), fmt(p["mean"])))
        L.append("  neg: n=%d min=%s median=%s max=%s mean=%s"
                 % (n["n"], fmt(n["min"]), fmt(n["median"]), fmt(n["max"]), fmt(n["mean"])))
        L.append("  separable=%s gap(pos.max-neg.min-ish)=%s" % (o["separable"], fmt(o["gap"])))
        L.append("  pos confidence: %s" % json.dumps(v["pos_confidence"], ensure_ascii=False))
        L.append("  neg confidence: %s" % json.dumps(v["neg_confidence"], ensure_ascii=False))
    L.append("")
    L.append("-- noul threshold sweep (pos_fail = fixed game called broken; "
             "neg_pass = broken game called fixed) --")
    L.append("%10s %8s %8s %8s" % ("t", "pos_fail", "neg_pass", "errors"))
    for row in fit["sweep_noul"]:
        L.append("%10s %8d %8d %8d" % (fmt(row["noul_min_p_true"], 4),
                                       row["pos_fail"], row["neg_pass"], row["errors"]))
    L.append("")
    L.append("-- score threshold sweep --")
    L.append("%10s %8s %8s %8s" % ("t", "pos_fail", "neg_pass", "errors"))
    for row in fit["sweep_score"]:
        L.append("%10s %8d %8d %8d" % (fmt(row["score_max_expected"], 4),
                                       row["pos_fail"], row["neg_pass"], row["errors"]))
    L.append("")
    L.append("-- chosen (joint minimum over BOTH rules; ties go to the prior) --")
    L.append(json.dumps(fit["chosen"], ensure_ascii=False, indent=1))
    L.append("-- best noul alone / best score alone (why the joint fit differs) --")
    L.append(json.dumps({"noul_alone": fit["best_noul_alone"],
                         "score_alone": fit["best_score_alone"],
                         "score_rule_effect": fit["score_rule_effect"]},
                        ensure_ascii=False, indent=1))
    L.append("-- prior, for comparison --")
    L.append(json.dumps(fit["prior"], ensure_ascii=False, indent=1))
    L.append("")
    L.append("-- per game --")
    L.append("%-15s %4s %10s %8s %6s %-32s" % ("game", "cls", "min_noul", "score",
                                               "calls", "worst invariant"))
    for r in fit["per_game"]:
        w = r["noul_worst"] or {}
        L.append("%-15s %4s %10s %8s %6s %-32s"
                 % (r["game"], r["class"], fmt(r["min_noul"]), fmt(r["score"]),
                    r["calls"], "%s=%s" % (w.get("question"), fmt(w.get("noul")))))
    L.append("")
    L.append(json.dumps(fit["calibration_statement"], ensure_ascii=False, indent=1))
    return L


def main(argv=None):
    ap = argparse.ArgumentParser(description="TASK-128 agent threshold fit")
    ap.add_argument("--pos-root", default=DEFAULT_POS)
    ap.add_argument("--neg-root", default=DEFAULT_NEG)
    ap.add_argument("--neg-exclude", nargs="*", default=[],
                    help="games inside the negative root that are NOT negatives.  "
                         "TASK-128 uses this for `pong`: the pre-fix export of pong was "
                         "measured playable BEFORE the fix (it is the 1/20 of TASK-116), "
                         "so counting it as a negative would be a mislabel.")
    ap.add_argument("--out", default="")
    args = ap.parse_args(argv)

    fit = build(os.path.abspath(args.pos_root), os.path.abspath(args.neg_root),
                args.neg_exclude)
    lines = report_lines(fit)
    for line in lines:
        print(line)
    if args.out:
        with io.open(args.out, "w", encoding="utf-8") as fh:
            fh.write(json.dumps(fit, ensure_ascii=False, indent=1))
        with io.open(args.out + ".txt", "w", encoding="utf-8") as fh:
            fh.write("\n".join(lines) + "\n")
        print("")
        print("wrote %s" % args.out)
        print("wrote %s.txt" % args.out)
    return 0


if __name__ == "__main__":
    sys.exit(main())
