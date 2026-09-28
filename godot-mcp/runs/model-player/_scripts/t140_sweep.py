# -*- coding: utf-8 -*-
"""TASK-140 §1.A.4 / §1.C.6: re-run every judgement at the REPORTING window, TWICE.

Arms
----
    scripted   all 20 games, `--backend scripted --player scripted --variant V1` (local)
    model      all 20 games, `--backend jev --variant V3 --change-margin strict`
    playjev    the vision arm, `--backend playjev --variant V3` (>= 10 games if budget allows)

Every run is at the DECLARED reporting window (`--window-frames <n>`, default 90) and every
run carries `--round <k>`, so each verdict in the artifacts and in the report says WHICH
window and WHICH round produced it (TASK-140 §1.A.3).  Two rounds of the same arm+window are
what the `UNSTABLE` judgement is computed from (§1.A.2).

Iron rule 4: the model service is SERIAL (one GPU).  Iron rule 6: one unique high port per
RUNNING arm -- the port comes from `--port-base`, and every (arm, round) pair in this batch
gets its own base, so two live probes can never share a port.  Iron rule 1: no shell
redirection -- each run's console output goes to its own file through a Python handle.

Usage (cmd, through the ledger wrapper):
    t140_cmd.py --cwd F:\\moonbit-hof-rs\\godot-mcp -- <py> runs\\model-player\\_scripts\\t140_sweep.py \\
        --arm scripted --window 90 --round 1 --port-base 9971
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
import t140_cmd  # noqa: E402

PY = r"D:\Anaconda\python.exe"
TOOL = os.path.join(ROOT, "tools", "playtest_player.py")
LOG = os.path.join(HERE, "t140_sweep.log")

GAMES = ("asteroids", "bomberman", "breakout", "flappy", "frogger", "game2048",
         "lunarlander", "match3", "minesweeper", "missilecommand", "pacman", "platformer",
         "pong", "puzzlebobble", "rtype", "snake", "sokoban", "spaceinvaders", "tetris",
         "towerdefense")

# TASK-139 §1.C's playjev set, kept byte-for-byte so the two batches' playjev columns are
# the same ten games.
PLAYJEV_GAMES = ("tetris", "pong", "asteroids", "snake", "game2048", "rtype", "match3",
                 "pacman", "sokoban", "minesweeper")

ARMS = {
    # arm        prefix-stem         backend   player      variant
    "scripted": ("t140-scripted", "scripted", "scripted", "V1"),
    "model": ("t140-jev-v3", "jev", "model", "V3"),
    "playjev": ("t140-playjev-v3", "playjev", "model", "V3"),
}
DIR_OF_BACKEND = {"scripted": "scripted", "jev": "jev", "playjev": "playjev"}

KEYS = ("verdict", "counts_as_pass", "pass", "strict_verdict", "baseline_verdict",
        "game_side_verdict", "steps", "injected_steps", "accepted_steps",
        "changed_steps_of_accepted", "accepted_and_changed_rate",
        "strict_accepted_and_changed_rate", "rated_step_count", "rated_and_changed_rate",
        "refused_steps", "refused_step_count", "real_progress_step_count",
        "refusal_only_run", "fail_steps", "strict_fail_steps", "MODEL_FIXED_POINT",
        "MODEL_NO_PROGRESS", "window_too_short", "window_too_short_steps",
        "verdict_before_window_check", "verdict_context", "qualified_verdict",
        "reporting_window", "why")


def log(msg):
    line = "[%s] %s" % (time.strftime("%H:%M:%S"), msg)
    print(line, flush=True)
    with io.open(LOG, "a", encoding="utf-8") as fh:
        fh.write(line + u"\n")


def player_json_path(prefix, game, backend):
    d = DIR_OF_BACKEND.get(backend, backend)
    return os.path.join(ROOT, "runs", "model-player", prefix, game, d, "player.json")


def summary_of(prefix, game, backend):
    pj = player_json_path(prefix, game, backend)
    if not os.path.isfile(pj):
        return {"error": "no player.json", "path": pj}
    with io.open(pj, encoding="utf-8") as fh:
        s = json.load(fh)
    out = {}
    for k in KEYS:
        out[k] = s.get(k)
    wf = s.get("window_frames") or {}
    out["window_min_frames"] = wf.get("min_frames")
    out["window_state"] = wf.get("state")
    out["window_nominal_frames"] = (s.get("verdict_context") or {}).get("window_frames")
    out["verdict_round"] = (s.get("verdict_context") or {}).get("round")
    fa = s.get("frame_alignment") or {}
    out["frame_alignment_reading"] = fa.get("reading")
    out["frame_alignment_residual_max_abs"] = (fa.get("residual_frames") or {}).get("max_abs")
    out["frame_alignment_matched"] = fa.get("matched_step_count")
    out["ack_missing_count"] = (s.get("ack_missing") or {}).get("count")
    out["player_json"] = pj
    return out


def main(argv):
    arm = "scripted"
    window = 90
    rnd = 1
    port = None
    if "--arm" in argv:
        arm = argv[argv.index("--arm") + 1]
    if "--window" in argv:
        window = int(argv[argv.index("--window") + 1])
    if "--round" in argv:
        rnd = int(argv[argv.index("--round") + 1])
    if "--port-base" in argv:
        port = int(argv[argv.index("--port-base") + 1])
    if argames(argv):
        games = argames(argv)
    elif "--games" in argv:
        games = argv[argv.index("--games") + 1:]
    else:
        games = list(PLAYJEV_GAMES) if arm == "playjev" else list(GAMES)
    if arm not in ARMS:
        print("unknown --arm %r (scripted | model | playjev)" % arm)
        return 2
    if port is None:
        print("--port-base is required (iron rule 6: one unique high port per live run)")
        return 2
    prefix_stem, backend, player, variant = ARMS[arm]
    prefix = "%s-w%d-r%d" % (prefix_stem, window, rnd)
    if "--prefix" in argv:
        prefix = argv[argv.index("--prefix") + 1]
    log("=" * 78)
    log("TASK-140 sweep arm=%s window=%d round=%d games=%d prefix=%s port=%d backend=%s"
        % (arm, window, rnd, len(games), prefix, port, backend))
    results = []
    for g in games:
        cmd = [PY, TOOL, "run", "--game", g, "--backend", backend, "--player", player,
               "--variant", variant, "--image-form", "full",
               "--steps", "12", "--port", str(port),
               "--window-frames", str(window), "--round", str(rnd),
               "--change-margin", "strict",
               "--out-prefix", prefix]
        outpath = os.path.join(HERE, "t140_%s_%s.out.txt" % (prefix, g))
        t0 = time.time()
        log("START %s" % g)
        rc, out, err = t140_cmd.run(cmd, cwd=ROOT)
        with io.open(outpath, "w", encoding="utf-8") as fh:
            fh.write(u"$ %s\n" % u" ".join(cmd))
            fh.write(u"----- stdout -----\n%s\n" % out)
            fh.write(u"----- stderr -----\n%s\n" % err)
        dt = round(time.time() - t0, 1)
        summ = summary_of(prefix, g, backend)
        log("DONE  %-14s rc=%s %5.1fs verdict=%-30s ctx=%s refused=%s real=%s rate=%s"
            % (g, rc, dt, summ.get("verdict"), summ.get("verdict_context"),
               summ.get("refused_steps"), summ.get("real_progress_step_count"),
               summ.get("accepted_and_changed_rate")))
        results.append({"game": g, "rc": rc, "seconds": dt, "summary": summ,
                        "cmd": cmd, "stdout": outpath, "arm": arm, "window": window,
                        "round": rnd, "prefix": prefix, "port": port})
        time.sleep(2)
    outp = os.path.join(HERE, "t140_results_%s.json" % prefix)
    with io.open(outp, "w", encoding="utf-8") as fh:
        fh.write(json.dumps(results, ensure_ascii=False, indent=1))
    log("sweep arm=%s window=%d round=%d done (%d runs) -> %s"
        % (arm, window, rnd, len(results), outp))
    return 0


def argames(argv):
    """Positional game names: everything that is not an option or an option's value."""
    opts_with_values = {"--arm", "--window", "--round", "--port-base", "--prefix"}
    out = []
    i = 0
    while i < len(argv):
        a = argv[i]
        if a in opts_with_values:
            i += 2
            continue
        if a.startswith("-"):
            i += 1
            continue
        out.append(a)
        i += 1
    return out


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
