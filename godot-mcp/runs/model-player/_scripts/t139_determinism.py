# -*- coding: utf-8 -*-
"""TASK-139 §1.A: the REPEAT / DETERMINISM probe.

The sensitivity matrix compares two runs that differ in ONE declared way (`--window-frames`).
For that comparison to mean anything about the WINDOW, the measurement itself has to be
repeatable: if the same invocation gives a different verdict twice, the two rungs differ for
an unstated reason.  This probe runs the SAME command twice (same game, same arm, same window,
same port number on its own port) and reports, per step, whether the reading moved.

It is deliberately narrow: 3 games chosen for the three things the question is about --
`asteroids` (the run TASK-138 flipped), `pacman` (a game with legal refusals) and `tetris`
(a plain PASS).

Usage (cmd):
    D:\\Anaconda\\python.exe runs\\model-player\\_scripts\\t139_determinism.py
    D:\\Anaconda\\python.exe runs\\model-player\\_scripts\\t139_determinism.py --arm scripted --window 30
"""
from __future__ import print_function

import io
import json
import os
import sys
import time

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.abspath(os.path.join(HERE, "..", "..", ".."))
sys.path.insert(0, HERE)
import t139_cmd  # noqa: E402

PY = r"D:\Anaconda\python.exe"
TOOL = os.path.join(ROOT, "tools", "playtest_player.py")
RUNS = os.path.join(ROOT, "runs", "model-player")
LOG = os.path.join(HERE, "t139_determinism.log")

GAMES = ("asteroids", "pacman", "tetris")
ARMS = {
    "scripted": ("t139-determinism", 9967, "scripted", "scripted", "V1", None),
    "model": ("t139-det-jev-v3", 9968, "jev", "model", "V3", "strict"),
}
# the evidence directory is named after the BACKEND, not after the `--player` role
DIR_OF_BACKEND = {"scripted": "scripted", "jev": "jev", "playjev": "playjev"}
# TASK-139 iron rule 6: the two window rungs run as SEPARATE processes, so they must not
# share a port.  (First draft did, at 9967; the second process's `kill_what_holds` then
# killed the first process's game mid-run and produced a batch of `rc=1` rows that were an
# artefact of the collision, not a measurement.  Ports are now per-window.)
PORT_STEP = {30: 0, 90: 1}
STEP_KEYS = ("step_verdict", "changed", "refused_legal", "pixel_diff", "control_frames",
             "action_frames", "gameplay_movement")
SUMMARY_KEYS = ("verdict", "counts_as_pass", "strict_verdict", "baseline_verdict",
                "game_side_verdict", "injected_steps", "accepted_steps",
                "changed_steps_of_accepted", "accepted_and_changed_rate",
                "rated_step_count", "refused_steps", "real_progress_step_count",
                "fail_steps", "window_too_short", "window_too_short_steps",
                "MODEL_FIXED_POINT", "MODEL_NO_PROGRESS")


def log(msg):
    line = "[%s] %s" % (time.strftime("%H:%M:%S"), msg)
    print(line, flush=True)
    with io.open(LOG, "a", encoding="utf-8") as fh:
        fh.write(line + u"\n")


def read_run(prefix, game, backend):
    d = os.path.join(RUNS, prefix, game, DIR_OF_BACKEND.get(backend, backend))
    pj = os.path.join(d, "player.json")
    if not os.path.isfile(pj):
        return None
    s = json.load(io.open(pj, encoding="utf-8"))
    out = {k: s.get(k) for k in SUMMARY_KEYS}
    out["_summary"] = dict(out)
    st = os.path.join(d, "steps.jsonl")
    steps = {}
    if os.path.isfile(st):
        for line in io.open(st, encoding="utf-8"):
            line = line.strip()
            if not line:
                continue
            r = json.loads(line)
            steps[r.get("step")] = {
                "step_verdict": r.get("step_verdict"),
                "changed": bool((r.get("change") or {}).get("changed")),
                "changed_strict": bool(((r.get("change") or {}).get("strict") or {}
                                        ).get("changed")),
                "refused_legal": bool((r.get("step_refusal") or {}).get("refused_legal")),
                "pixel_diff": r.get("pixel_diff"),
                "control_frames": ((r.get("control_diff") or {}).get("frame_budget") or {}
                                   ).get("achieved_delta"),
                "action_frames": (r.get("frame_budget") or {}).get("action_frames"),
                "gameplay_movement": r.get("gameplay_movement"),
                "action": (r.get("action") or {}).get("action"),
            }
    out["_steps"] = steps
    return out


def main(argv):
    arm = "scripted"
    window = 30
    games = list(GAMES)
    if "--arm" in argv:
        arm = argv[argv.index("--arm") + 1]
    if "--window" in argv:
        window = int(argv[argv.index("--window") + 1])
    if "--games" in argv:
        i = argv.index("--games")
        games = [a for a in argv[i + 1:] if not a.startswith("-")]
    repeats = 2
    if "--repeats" in argv:
        repeats = int(argv[argv.index("--repeats") + 1])
    if "--prefix-suffix" in argv:
        prefix_suffix = argv[argv.index("--prefix-suffix") + 1]
    else:
        prefix_suffix = ""
    prefix, port, backend, player, variant, margin = ARMS[arm]
    port = port + PORT_STEP.get(window, 0)
    prefix = "%s-w%d%s" % (prefix, window, prefix_suffix)
    log("=" * 78)
    log("TASK-139 determinism arm=%s window=%d games=%s prefix=%s port=%d"
        % (arm, window, tuple(games), prefix, port))
    results = []
    for g in games:
        for rep in range(1, repeats + 1):
            cmd = [PY, TOOL, "run", "--game", g, "--backend", backend, "--player", player,
                   "--variant", variant, "--image-form", "full", "--steps", "12",
                   "--port", str(port), "--window-frames", str(window),
                   "--out-prefix", prefix]
            if margin:
                cmd[cmd.index("--steps"):cmd.index("--steps")] = ["--change-margin", margin]
            log("START %s repeat %d" % (g, rep))
            rc, out, err = t139_cmd.run(cmd, cwd=ROOT)
            run = read_run(prefix, g, backend)
            log("DONE  %-12s rep=%d rc=%s verdict=%-22s"
                % (g, rep, rc, (run or {}).get("verdict")))
            results.append({"game": g, "repeat": rep, "rc": rc, "cmd": cmd, "run": run})
            time.sleep(2)
    # -- compare the repeats -------------------------------------------------------------
    comparison = []
    verdicts_by_game = {}
    for g in games:
        rows = [r for r in results if r["game"] == g]
        rows.sort(key=lambda r: r["repeat"])
        ra = (rows[0].get("run") if rows else None) or {}
        rb = (rows[-1].get("run") if rows else None) or {}
        vs = [(r.get("run") or {}).get("verdict") for r in rows]
        verdicts_by_game[g] = vs
        summ_diff = {k: [ra.get(k), rb.get(k)] for k in SUMMARY_KEYS
                     if ra.get(k) != rb.get(k)}
        step_diff = []
        sa, sb = ra.get("_steps") or {}, rb.get("_steps") or {}
        for st in sorted(set(sa) | set(sb)):
            x, y = sa.get(st), sb.get(st)
            if x != y:
                step_diff.append({"step": st, "repeat1": x, "repeat2": y})
        comparison.append({"game": g,
                           "repeats": len(rows),
                           "verdicts": vs,
                           "verdict_repeat1": ra.get("verdict"),
                           "verdict_repeat2": rb.get("verdict"),
                           "verdict_stable": len(set(vs)) == 1,
                           "rc_by_repeat": [r.get("rc") for r in rows],
                           "summary_differences": summ_diff,
                           "step_differences": step_diff,
                           "step_difference_count": len(step_diff)})
    doc = {"task": "TASK-139", "section": "A -- repeat / determinism probe", "arm": arm,
           "window": window, "games": list(games), "repeats": repeats, "runs": results,
           "comparison": comparison, "verdicts_by_game": verdicts_by_game,
           "all_rc_zero": all(r.get("rc") == 0 for r in results),
           "all_verdicts_stable": all(c["verdict_stable"] for c in comparison)}
    outp = os.path.join(HERE, "t139_determinism_%s.json" % prefix)
    with io.open(outp, "w", encoding="utf-8") as fh:
        fh.write(json.dumps(doc, ensure_ascii=False, indent=1))
    print("=" * 78)
    for c in comparison:
        print("%-12s verdicts=%-60s stable=%-5s rc=%s step_diffs=%d"
              % (c["game"], json.dumps(c["verdicts"], ensure_ascii=False),
                 c["verdict_stable"], c["rc_by_repeat"], c["step_difference_count"]))
        for d in c["step_differences"][:6]:
            print("     step %s: %s" % (d["step"], json.dumps(d, ensure_ascii=False)[:220]))
    print("all_rc_zero=%s  all_verdicts_stable=%s"
          % (doc["all_rc_zero"], doc["all_verdicts_stable"]))
    print("wrote %s" % outp)
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
