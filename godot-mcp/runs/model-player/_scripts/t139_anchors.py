# -*- coding: utf-8 -*-
"""TASK-139 §1.C.9: assemble the frame + anchor table for the images that get read.

For each requested `<prefix>/<game>/<backend>` it prints, per step, the BEFORE/AFTER frame
paths and sha256, the per-step verdict, the changed reading, the refusal reading, and the
DECLARED game-state fields as of that step (`steps.jsonl -> markers` and the declared
`gameplay_observables` keys from `readable_state.values`), so a `read_image` description can
carry a machine-checkable anchor on the SAME line.

Usage (cmd):
    D:\\Anaconda\\python.exe runs\\model-player\\_scripts\\t139_anchors.py t139-scripted-w30 asteroids scripted
    D:\\Anaconda\\python.exe runs\\model-player\\_scripts\\t139_anchors.py t139-jev-v3-w30 asteroids jev 3 4
"""
from __future__ import print_function

import io
import json
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.abspath(os.path.join(HERE, "..", "..", ".."))
RUNS = os.path.join(ROOT, "runs", "model-player")


def main(argv):
    prefix = argv[0]
    game = argv[1]
    backend = argv[2]
    want = [int(x) for x in argv[3:] if x.isdigit()]
    d = os.path.join(RUNS, prefix, game, backend)
    pj = os.path.join(d, "player.json")
    print("RUN %s  dir=%s" % (prefix, d))
    if os.path.isfile(pj):
        s = json.load(io.open(pj, encoding="utf-8"))
        for k in ("verdict", "counts_as_pass", "strict_verdict", "baseline_verdict",
                  "game_side_verdict", "injected_steps", "accepted_steps",
                  "changed_steps_of_accepted", "accepted_and_changed_rate",
                  "rated_step_count", "rated_and_changed_rate", "refused_steps",
                  "real_progress_step_count", "fail_steps", "window_too_short",
                  "window_too_short_steps"):
            print("  %-28s = %s" % (k, s.get(k)))
        wf = s.get("window_frames") or {}
        print("  %-28s = %s" % ("window_frames.state", wf.get("state")))
        for w in (wf.get("steps") or []):
            if not want or w.get("step") in want:
                print("     window step %s: control=%s action=%s too_short=%s"
                      % (w.get("step"), w.get("control_frames"), w.get("action_frames"),
                         w.get("too_short")))
        fa = s.get("frame_alignment") or {}
        print("  %-28s = %s" % ("frame_alignment", fa.get("reading")))
    else:
        print("  no player.json at %s" % pj)
    st = os.path.join(d, "steps.jsonl")
    if not os.path.isfile(st):
        print("  no steps.jsonl")
        return 0
    frames_dir = os.path.join(d, "frames")
    print("  frames dir: %s" % frames_dir)
    for line in io.open(st, encoding="utf-8"):
        line = line.strip()
        if not line:
            continue
        r = json.loads(line)
        if want and r.get("step") not in want:
            continue
        ch = r.get("change") or {}
        rs = r.get("readable_state") or {}
        vals = rs.get("values") or {}
        print("-" * 90)
        print("STEP %s  action=%s  step_verdict=%s  changed=%s(strict %s)  px=%s ctl_px=%s"
              % (r.get("step"), (r.get("action") or {}).get("action"),
                 r.get("step_verdict"), ch.get("changed"),
                 ((ch.get("strict") or {}).get("changed")), r.get("pixel_diff"),
                 ch.get("control_pixels")))
        print("   refused=%s evidence=%s" % (
            bool((r.get("step_refusal") or {}).get("refused_legal")),
            (r.get("step_refusal") or {}).get("refusal_evidence")))
        print("   gameplay_movement=%s control_movement=%s keys=%s"
              % (r.get("gameplay_movement"), ch.get("control_movement"),
                 r.get("gameplay_changes")))
        fb = r.get("frame_budget") or {}
        cb = (r.get("control_diff") or {}).get("frame_budget") or {}
        print("   window: control_start=%s control_end=%s control_frames=%s | "
              "action_start=%s action_end=%s action_frames=%s"
              % (cb.get("start_drawn"), cb.get("end_drawn"), cb.get("achieved_delta"),
                 fb.get("step_frame_start"), fb.get("step_frame_end"),
                 fb.get("action_frames")))
        print("   frame_before=%s sha=%s" % (r.get("frame_before_file"),
                                             (r.get("frame_before_sha") or "")[:16]))
        print("   frame_after =%s sha=%s" % (r.get("frame_after_file"),
                                             (r.get("frame_after_sha") or "")[:16]))
        print("   markers=%s" % json.dumps(r.get("markers"), ensure_ascii=False))
        keys = [k for k in vals if k in ("ShipX", "ShipY", "ShipAngle", "ShipVelX",
                                         "ShipVelY", "BulletActive", "ShotsFired", "Score",
                                         "Lives", "PacCol", "PacRow", "PacX", "PacY",
                                         "PelletsEaten", "RejectedSteps", "CursorCol",
                                         "CursorRow", "Board", "Moves", "RejectedMoves",
                                         "InputRejectedSwaps", "RealBoard")]
        if keys:
            print("   declared fields: %s"
                  % json.dumps({k: vals[k] for k in sorted(keys)}, ensure_ascii=False))
        for d_ in (r.get("state_delta") or []):
            print("      delta %s %r -> %r" % (d_.get("key"), d_.get("from"), d_.get("to")))
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
