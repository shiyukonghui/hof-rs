# -*- coding: utf-8 -*-
"""TASK-140 §1.A.2/§1.A.5 + §1.C: the cross-round (`UNSTABLE`) and cross-window (`SENSITIVE`)
analysis over this batch's sweeps, and the per-arm distributions.

Inputs are the SWEEP RESULTS files this batch writes (`t140_results_<prefix>.json`, one entry
per game with its `summary` and its `player.json` path) plus, optionally, TASK-139's recorded
results files so the window-sensitivity column can be computed against a recording rather than
against a memory.

Outputs (both in `runs/model-player/_scripts/`):
  * `t140_stability.json` -- the whole reading, machine-checkable;
  * `t140_stability.md`   -- the same rows as markdown tables, ready to paste into the report.

Usage (cmd, through the ledger wrapper):
    t140_cmd.py --cwd F:\\moonbit-hof-rs\\godot-mcp -- <py> runs\\model-player\\_scripts\\t140_stability.py \\
        --arm scripted --results t140_results_t140-scripted-w90-r1.json \\
               --results t140_results_t140-scripted-w90-r2.json \\
        --other-window t139_results_t139-scripted-w30.json
"""
from __future__ import print_function

import io
import json
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.abspath(os.path.join(HERE, "..", "..", ".."))
sys.path.insert(0, os.path.join(ROOT, "tools"))
sys.path.insert(0, HERE)

from playtest_player import (  # noqa: E402
    STABILITY_STATE_UNSTABLE, stability_summary, verdict_class)
import t140_cmd  # noqa: E402

PY = r"D:\Anaconda\python.exe"


def load(path):
    with io.open(path if os.path.isabs(path) else os.path.join(HERE, path),
                 encoding="utf-8") as fh:
        return json.load(fh)


def reading_of(entry, label):
    s = entry.get("summary") or {}
    ctx = s.get("verdict_context") or {}
    return {
        "label": label,
        "game": entry.get("game"),
        "verdict": s.get("verdict"),
        "counts_as_pass": s.get("counts_as_pass"),
        "class": verdict_class(s.get("verdict")),
        "window_frames": ctx.get("window_frames", entry.get("window")),
        "round": ctx.get("round", entry.get("round")),
        "player_json": s.get("player_json"),
        "qualified_verdict": s.get("qualified_verdict"),
        "refused_steps": s.get("refused_steps"),
        "real_progress_step_count": s.get("real_progress_step_count"),
        "accepted_and_changed_rate": s.get("accepted_and_changed_rate"),
        "steps": s.get("steps"),
        "injected_steps": s.get("injected_steps"),
    }


def analyse(arm, rounds, others, cross):
    """`rounds`: [(label, entries)]; `others`: [(label, entries)] recorded other windows;
    `cross`: [(label, entries)] SAME-WINDOW readings recorded by another batch (so a
    disagreement is a cross-batch reproducibility fact, not a window-length fact)."""
    games = sorted(set([e["game"] for _l, ents in rounds for e in ents] +
                       [e["game"] for _l, ents in others for e in ents] +
                       [e["game"] for _l, ents in cross for e in ents]))
    by_round = {}
    for label, ents in rounds:
        by_round[label] = dict((e["game"], reading_of(e, label)) for e in ents)
    by_other = {}
    for label, ents in others:
        by_other[label] = dict((e["game"], reading_of(e, label)) for e in ents)
    by_cross = {}
    for label, ents in cross:
        by_cross[label] = dict((e["game"], reading_of(e, label)) for e in ents)
    labels = [l for l, _e in rounds]
    other_labels = [l for l, _e in others]
    cross_labels = [l for l, _e in cross]
    rows = []
    for g in games:
        rs = []
        for label in labels:
            r = by_round.get(label, {}).get(g)
            if r:
                rs.append({"round": r["round"], "window_frames": r["window_frames"],
                           "verdict": r["verdict"], "counts_as_pass": r["counts_as_pass"],
                           "game": g,
                           "steps_path": os.path.join(os.path.dirname(r["player_json"]),
                                                      "steps.jsonl")
                           if r.get("player_json") else None,
                           "source": r.get("player_json"), "label": label})
        stab = stability_summary(rs)
        allr = []
        for label in labels:
            r = by_round.get(label, {}).get(g)
            if r:
                allr.append(r)
        for label in other_labels:
            r = by_other.get(label, {}).get(g)
            if r:
                allr.append(r)
        pairs = []
        for i in range(len(allr)):
            for j in range(i + 1, len(allr)):
                a, b = allr[i], allr[j]
                if a["class"] != b["class"]:
                    pairs.append({"a": a["label"], "b": b["label"],
                                  "a_verdict": a["verdict"], "b_verdict": b["verdict"],
                                  "a_class": a["class"], "b_class": b["class"],
                                  "window_a": a["window_frames"], "window_b": b["window_frames"]})
        cross_pairs = []
        for label in cross_labels:
            r = by_cross.get(label, {}).get(g)
            if not r:
                continue
            for mine in [by_round.get(l, {}).get(g) for l in labels]:
                if not mine:
                    continue
                if mine["class"] != r["class"]:
                    cross_pairs.append({"mine": mine["label"], "theirs": label,
                                        "my_verdict": mine["verdict"],
                                        "their_verdict": r["verdict"],
                                        "my_class": mine["class"],
                                        "their_class": r["class"]})
                    break
        rows.append({
            "game": g,
            "readings": allr,
            "cross_batch_readings": [dict(x, label=l)
                                     for l, ents in cross
                                     if (by_cross.get(l, {}).get(g)) is not None
                                     for x in [by_cross[l][g]]],
            "rounds": labels,
            "stability": stab,
            "unstable": stab["state"] == STABILITY_STATE_UNSTABLE,
            "sensitive": bool(pairs),
            "sensitivity_pairs": pairs,
            "cross_batch": bool(cross_pairs),
            "cross_batch_pairs": cross_pairs,
            "pass_basis": [{"label": r["label"], "window_frames": r["window_frames"],
                            "counts_as_pass": r["counts_as_pass"]} for r in allr],
        })
    out = {"arm": arm, "round_labels": labels, "other_window_labels": other_labels,
           "cross_batch_labels": cross_labels,
           "games": rows,
           "unstable_games": [r["game"] for r in rows if r["unstable"]],
           "sensitive_games": [r["game"] for r in rows if r["sensitive"]],
           "cross_batch_differing_games": [r["game"] for r in rows if r["cross_batch"]],
           "distributions": {}}
    for label in labels:
        d = {"PASS": 0, "PASS(baseline only)": 0, "FAIL": 0, "INCONCLUSIVE": 0,
             "WINDOW_TOO_SHORT": 0, "OTHER": 0, "counts_as_pass": 0}
        for g in games:
            r = by_round.get(label, {}).get(g)
            if not r:
                continue
            c = r["class"]
            if c in d:
                d[c] += 1
            else:
                d["OTHER"] += 1
            if r.get("counts_as_pass"):
                d["counts_as_pass"] += 1
        out["distributions"][label] = d
    for label in other_labels:
        d = {"PASS": 0, "PASS(baseline only)": 0, "FAIL": 0, "INCONCLUSIVE": 0,
             "WINDOW_TOO_SHORT": 0, "OTHER": 0, "counts_as_pass": 0}
        for g in games:
            r = by_other.get(label, {}).get(g)
            if not r:
                continue
            c = r["class"]
            if c in d:
                d[c] += 1
            else:
                d["OTHER"] += 1
            if r.get("counts_as_pass"):
                d["counts_as_pass"] += 1
        out["distributions"][label] = d
    return out


def markdown(res):
    L = []
    L.append(u"### arm `%s` -- rounds: %s   other-window recordings: %s   same-window other batch: %s"
             % (res["arm"], ", ".join(res["round_labels"]),
                ", ".join(res["other_window_labels"]) or "(none)",
                ", ".join(res["cross_batch_labels"]) or "(none)"))
    L.append(u"")
    labels = res["round_labels"] + res["other_window_labels"] + res["cross_batch_labels"]
    L.append(u"| game | " + u" | ".join(labels) +
             u" | UNSTABLE | SENSITIVE | CROSS-BATCH |")
    L.append(u"|---|" + u"---|" * (len(labels) + 3))
    for r in res["games"]:
        cells = []
        for lab in labels:
            rd = next((x for x in r["readings"] if x["label"] == lab), None)
            if rd is None:
                rd = next((x for x in (r.get("cross_batch_readings") or [])
                           if x["label"] == lab), None)
            cells.append((u"`%s`%s" % (rd["class"], u"*" if rd["counts_as_pass"] else u""))
                         if rd else u"-")
        L.append(u"| `%s` | %s | %s | %s | %s |"
                 % (r["game"], u" | ".join(cells),
                    u"**UNSTABLE**" if r["unstable"] else u"",
                    u"**SENSITIVE**" if r["sensitive"] else u"",
                    u"**DIFFERS**" if r["cross_batch"] else u""))
    L.append(u"")
    L.append(u"(`*` = `counts_as_pass: true`; a class without it is reported but never "
             u"counted.  `UNSTABLE` = the two rounds of THIS batch at the SAME window disagree; "
             u"`SENSITIVE` = two DIFFERENT windows disagree (either TASK-139's own two rungs, or "
             u"this batch's w90 against a TASK-139 recording); `CROSS-BATCH` = this batch's w90 "
             u"reading differs from TASK-139's w90 reading of the same arm -- a third "
             u"independent reading at the reporting window that does NOT agree with the two "
             u"TASK-139 had.)")
    L.append(u"")
    return u"\n".join(L)


def main(argv):
    arm = argv[argv.index("--arm") + 1] if "--arm" in argv else "scripted"
    rounds, others, cross = [], [], []
    i = 0
    while i < len(argv):
        if argv[i] == "--results":
            rounds.append((argv[i + 1].replace("t140_results_", "").replace(".json", ""),
                           load(argv[i + 1])))
            i += 2
            continue
        if argv[i] == "--other-window":
            others.append((argv[i + 1].replace("t139_results_", "").replace(".json", ""),
                           load(argv[i + 1])))
            i += 2
            continue
        if argv[i] == "--cross-batch":
            cross.append((argv[i + 1].replace("t139_results_", "").replace(".json", ""),
                          load(argv[i + 1])))
            i += 2
            continue
        i += 1
    res = analyse(arm, rounds, others, cross)
    outp = os.path.join(HERE, "t140_stability_%s.json" % arm)
    with io.open(outp, "w", encoding="utf-8") as fh:
        fh.write(json.dumps(res, ensure_ascii=False, indent=1))
    md = markdown(res)
    with io.open(os.path.join(HERE, "t140_stability_%s.md" % arm), "w", encoding="utf-8") as fh:
        fh.write(md)
    print(md)
    print("UNSTABLE: %s" % (", ".join(res["unstable_games"]) or "(none)"))
    print("SENSITIVE: %s" % (", ".join(res["sensitive_games"]) or "(none)"))
    print("CROSS-BATCH (same window, other batch): %s"
          % (", ".join(res["cross_batch_differing_games"]) or "(none)"))
    for lab, d in res["distributions"].items():
        print("%-32s %s" % (lab, json.dumps(d, ensure_ascii=False)))
    print("wrote %s" % outp)
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
