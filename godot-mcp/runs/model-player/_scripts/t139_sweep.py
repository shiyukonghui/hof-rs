# -*- coding: utf-8 -*-
"""TASK-139 §1.C: re-run every judgement under the NEW criterion, at TWO window lengths.

Arms
----
    scripted   all 20 games, `--backend scripted --variant V1` (local, no service)
    model      all 20 games, `--backend jev --variant V3 --change-margin strict`
    playjev    the vision arm, `--backend playjev --variant V3` (>= 8 games if budget allows)

Each arm is run at TWO `--window-frames` values (TASK-139 §1.A asks for at least two rungs):
the TASK-138 value 30 and the longer 90.  The window length is the ONLY thing that changes
between the two rungs of one arm -- same backend, same variant, same margin, same port
family, same steps -- so a verdict that flips between them is attributable to the window
length and is reported as `SENSITIVE` with the affected steps named.

Iron rule 4: the model service is SERIAL (one GPU).  Iron rule 1: no shell redirection --
each run's console output goes to its own file through a Python handle, and the command that
produced it is appended to the shared ledger by `t139_cmd.run`.

Usage (cmd):
    D:\\Anaconda\\python.exe runs\\model-player\\_scripts\\t139_sweep.py --arm scripted --window 30
    D:\\Anaconda\\python.exe runs\\model-player\\_scripts\\t139_sweep.py --arm scripted --window 90
    D:\\Anaconda\\python.exe runs\\model-player\\_scripts\\t139_sweep.py --arm model --window 30
    D:\\Anaconda\\python.exe runs\\model-player\\_scripts\\t139_sweep.py --arm playjev --window 30
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
LOG = os.path.join(HERE, "t139_sweep.log")

GAMES = ("asteroids", "bomberman", "breakout", "flappy", "frogger", "game2048",
         "lunarlander", "match3", "minesweeper", "missilecommand", "pacman", "platformer",
         "pong", "puzzlebobble", "rtype", "snake", "sokoban", "spaceinvaders", "tetris",
         "towerdefense")

# TASK-139 §1.C: `playjev` runs "if the budget allows", on at least 8 games.  The games are
# chosen to cover the four verdict classes of the TASK-138 scripted arm plus the two games the
# window question is about, NOT to flatter the arm.
PLAYJEV_GAMES = ("tetris", "pong", "asteroids", "snake", "game2048", "rtype", "match3",
                 "pacman", "sokoban", "minesweeper")

ARMS = {
    # arm      prefix                port      backend   player    variant margin
    "scripted": ("t139-scripted", 9961, "scripted", "scripted", "V1", None),
    "model": ("t139-jev-v3", 9963, "jev", "model", "V3", "strict"),
    "playjev": ("t139-playjev-v3", 9965, "playjev", "model", "V3", "strict"),
}
# The evidence DIRECTORY is named after the BACKEND (`scripted` / `jev` / `playjev`), not
# after the `--player` role: measured on TASK-138's trees
# (`t136-jev-v3/tetris/jev/player.json`, `t136-playjev-v3/pong/playjev/player.json`).
DIR_OF_BACKEND = {"scripted": "scripted", "jev": "jev", "playjev": "playjev"}
# TASK-139 iron rule 6: one unique high port per RUNNING arm.  The two window rungs of one
# arm are separate processes, so they get different ports (+1) -- 9961/9962, 9963/9964,
# 9965/9966 -- and no port is ever shared by two live runs.
PORT_STEP = {30: 0, 90: 1}

KEYS = ("verdict", "counts_as_pass", "strict_verdict", "baseline_verdict",
        "game_side_verdict", "strict_game_side_verdict", "baseline_game_side_verdict",
        "steps", "injected_steps", "accepted_steps", "changed_steps_of_accepted",
        "accepted_and_changed_rate", "strict_accepted_and_changed_rate",
        "baseline_accepted_and_changed_rate", "rated_step_count", "rated_and_changed_rate",
        "refused_steps", "refused_step_count", "real_progress_step_count",
        "refusal_only_run", "refusal_only_run", "progress_step_count",
        "progress_step_count_strict", "fail_steps", "strict_fail_steps",
        "match_seconds_in_game_clock", "MODEL_FIXED_POINT", "MODEL_NO_PROGRESS",
        "window_too_short", "window_too_short_steps", "verdict_before_window_check")


def log(msg):
    line = "[%s] %s" % (time.strftime("%H:%M:%S"), msg)
    print(line, flush=True)
    with io.open(LOG, "a", encoding="utf-8") as fh:
        fh.write(line + u"\n")


def summary_of(prefix, game, player, backend=None):
    """Read the run's `player.json` from the BACKEND-named evidence directory."""
    d = DIR_OF_BACKEND.get(backend or player, backend or player)
    pj = os.path.join(ROOT, "runs", "model-player", prefix, game, d, "player.json")
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
    out["window_steps"] = wf.get("steps")
    fa = s.get("frame_alignment") or {}
    out["frame_alignment_reading"] = fa.get("reading")
    out["frame_alignment_residual_max_abs"] = (fa.get("residual_frames") or {}).get("max_abs")
    out["frame_alignment_matched"] = fa.get("matched_step_count")
    out["ack_missing_count"] = (s.get("ack_missing") or {}).get("count")
    out["player_json"] = pj
    return out


def main(argv):
    arm = "scripted"
    window = 30
    if "--arm" in argv:
        arm = argv[argv.index("--arm") + 1]
    if "--window" in argv:
        window = int(argv[argv.index("--window") + 1])
    games = [a for a in argv[1:] if not a.startswith("-") and a != arm
             and not a.isdigit()]
    if arm not in ARMS:
        print("unknown --arm %r (scripted | model | playjev)" % arm)
        return 2
    prefix, port, backend, player, variant, margin = ARMS[arm]
    port = port + PORT_STEP.get(window, 0)
    if "--port-base" in argv:
        port = int(argv[argv.index("--port-base") + 1]) + PORT_STEP.get(window, 0)
    if not games:
        games = list(PLAYJEV_GAMES) if arm == "playjev" else list(GAMES)
    prefix = "%s-w%d" % (prefix, window)
    log("=" * 78)
    log("TASK-139 sweep arm=%s window=%d games=%d prefix=%s port=%d backend=%s"
        % (arm, window, len(games), prefix, port, backend))
    results = []
    for g in games:
        cmd = [PY, TOOL, "run", "--game", g, "--backend", backend, "--player", player,
               "--variant", variant, "--image-form", "full",
               "--steps", "12", "--port", str(port),
               "--window-frames", str(window),
               "--out-prefix", prefix]
        if margin:
            cmd[cmd.index("--steps"):cmd.index("--steps")] = ["--change-margin", margin]
        outpath = os.path.join(HERE, "t139_%s_%s.out.txt" % (prefix, g))
        t0 = time.time()
        log("START %s" % g)
        rc, out, err = t139_cmd.run(cmd, cwd=ROOT)
        with io.open(outpath, "w", encoding="utf-8") as fh:
            fh.write("$ %s\n" % " ".join(cmd))
            fh.write("----- stdout -----\n%s\n" % out)
            fh.write("----- stderr -----\n%s\n" % err)
        dt = round(time.time() - t0, 1)
        summ = summary_of(prefix, g, player, backend)
        log("DONE  %-14s rc=%s %5.1fs verdict=%-24s window=%-8s refused=%s real=%s "
            "rate=%s align=%s"
            % (g, rc, dt, summ.get("verdict"), summ.get("window_state"),
               summ.get("refused_steps"), summ.get("real_progress_step_count"),
               summ.get("accepted_and_changed_rate"),
               summ.get("frame_alignment_residual_max_abs")))
        results.append({"game": g, "rc": rc, "seconds": dt, "summary": summ,
                        "cmd": cmd, "stdout": outpath, "arm": arm, "window": window})
        time.sleep(2)
    outp = os.path.join(HERE, "t139_results_%s%s.json"
                        % (prefix, ("-" + argv[argv.index("--results-suffix") + 1])
                           if "--results-suffix" in argv else ""))
    with io.open(outp, "w", encoding="utf-8") as fh:
        fh.write(json.dumps(results, ensure_ascii=False, indent=1))
    log("sweep arm=%s window=%d done (%d runs) -> %s" % (arm, window, len(results), outp))
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
