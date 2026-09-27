#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""playjev_probe.py -- the LOCAL end-to-end probe for the PlayJev service (TASK-127 §2.5).

What it does
------------
For each sample frame it sends ONE request to the deployed PlayJev service carrying
**one image and three questions**:

    move        a Choice over the game's declared actions   (the action question)
    playable    a yes/no Choice                             (the `noul` question)
    brokenness  an ordered-levels Choice, 1..5              (the `score` question)

-- because PlayJev's `serve.py` serves `type: "choice"` only, so the Jev `noul`/`score`
question types cannot be used at all (see `playtest_agent.py`, PlayJevAgent).  Every
request and every response is stored VERBATIM in the output JSON, together with the
HTTP status, the measured latency and the agent's classification of the answers.

The samples
-----------
POSITIVE frames are our own real captures, taken from the exported-executable gate runs
(`runs/playability-exe/<game>/frames/*.png`).  Our captures contain NO degenerate frame
(all 836 of them have content_fraction >= 0.005), so the NEGATIVE frames are derived
from those real captures by a reproducible, documented recipe and written next to the
probe output with their provenance:

    black            every pixel zeroed              -> "flat black screen"
    flat            every pixel = the frame's own background colour -> "blank render"
    content_missing the content bbox painted over     -> "the game drew nothing"

Nothing here is invented and nothing leaves the machine: the only endpoint contacted is
the local service (default http://127.0.0.1:8081).

Run (no shell redirection anywhere):

    python tools\\playjev_probe.py
    python tools\\playjev_probe.py --base-url http://127.0.0.1:8081 --out runs\\playability\\playjev-probe.json

Exit code 0 means every sample answered HTTP 200, parsed, and carried probabilities.
"""

from __future__ import print_function

import argparse
import base64
import hashlib
import json
import os
import sys
import time

HERE = os.path.dirname(os.path.abspath(__file__))
if HERE not in sys.path:
    sys.path.insert(0, HERE)

from playtest_agent import PlayJevAgent  # noqa: E402

REPO = os.path.dirname(HERE)
RUNS = os.path.join(REPO, "runs", "playability-exe")
OUT_DEFAULT = os.path.join(REPO, "runs", "playability", "playjev-probe.json")
FRAME_DIR_DEFAULT = os.path.join(REPO, "runs", "playability", "playjev-probe-frames")

# the goal shape the gate passes to an agent, for one of our own games
GOAL = {
    "game": "pong",
    "objective": "make the score advance",
    "keys": ["W", "S", "SPACE"],
    "actions": {"pong_left_up": ["W"], "pong_left_down": ["S"], "pong_serve": ["SPACE"]},
}

# (sample id, source frame relative to runs/playability-exe, what it represents)
POSITIVES = [
    ("pong_post1", "pong/frames/20_post1.png",
     "POSITIVE: a real full-window capture of our exported pong exe, just after the "
     "scripted probe's actions; the frame the gate itself judges."),
    ("tetris_auto3", "tetris/frames/04_auto3.png",
     "POSITIVE: a real full-window capture of our exported tetris exe during the "
     "automatic settle frames."),
    ("snake_act", "snake/frames/07_a00_snake_up_parse_act.png",
     "POSITIVE: a real full-window capture of our exported snake exe AFTER a real key "
     "was injected (the 'act' frame of the first documented action)."),
]
NEGATIVES = [
    ("pong_post1_black", "pong/frames/20_post1.png", "black",
     "NEGATIVE: the same real pong frame with every pixel zeroed -- the 'black screen' "
     "failure the gate must catch."),
    ("pong_post1_flat", "pong/frames/20_post1.png", "flat",
     "NEGATIVE: the same real pong frame repainted in its OWN background colour -- a "
     "blank render that is not literally black."),
    ("pong_post1_content_missing", "pong/frames/20_post1.png", "content_missing",
     "NEGATIVE: the same real pong frame with its content bounding box painted over -- "
     "the window is there, the game drew nothing in it."),
]


def sha256_file(path):
    h = hashlib.sha256()
    with open(path, "rb") as fh:
        for chunk in iter(lambda: fh.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def derive(src, dst, recipe, background=None, bbox=None):
    """Write one derived PNG.  Pillow only; no shell, no network."""
    from PIL import Image
    im = Image.open(src).convert("RGB")
    w, h = im.size
    if recipe == "black":
        out = Image.new("RGB", (w, h), (0, 0, 0))
    elif recipe == "flat":
        out = Image.new("RGB", (w, h), tuple(background or (0, 0, 0)))
    elif recipe == "content_missing":
        out = im.copy()
        px = out.load()
        colour = tuple(background or (0, 0, 0))
        x, y, bw, bh = bbox
        for yy in range(max(0, y), min(h, y + bh)):
            for xx in range(max(0, x), min(w, x + bw)):
                px[xx, yy] = colour
    else:
        raise ValueError("unknown recipe %r" % recipe)
    out.save(dst, "PNG")
    return dst


def frame_meta(path, index, sha):
    try:
        from PIL import Image
        with Image.open(path) as im:
            w, h = im.size
    except Exception:  # noqa: BLE001
        w = h = 0
    return {"index": index, "path": path, "width": w, "height": h,
            "window": [w, h], "declared": [w, h], "content_fraction": None,
            "bbox": None, "sha256": sha, "changed_pixels_vs_prev": None}


def read_frames_json(game):
    p = os.path.join(RUNS, game, "frames.json")
    if not os.path.isfile(p):
        return []
    with open(p, "r", encoding="utf-8") as fh:
        return json.load(fh)


def build_samples(frame_dir):
    """Return [(id, path, provenance, recipe)] -- positives first."""
    samples = []
    for sid, rel, note in POSITIVES:
        p = os.path.join(RUNS, rel)
        if os.path.isfile(p):
            samples.append((sid, p, {"kind": "real-capture", "source": rel,
                                     "source_sha256": sha256_file(p), "note": note},
                            None))
    os.makedirs(frame_dir, exist_ok=True)
    for sid, rel, recipe, note in NEGATIVES:
        src = os.path.join(RUNS, rel)
        if not os.path.isfile(src):
            continue
        game = rel.split("/", 1)[0]
        frames = read_frames_json(game)
        meta = None
        for f in frames:
            if f.get("file") and f["file"] in rel:
                meta = f
                break
        if meta is None and frames:
            meta = frames[-1]
        background = (meta or {}).get("background_rgb")
        bbox = (meta or {}).get("bbox")
        dst = os.path.join(frame_dir, "%s.png" % sid)
        # `content_missing` needs a bbox to paint over; without one it degrades to
        # `flat`, and the recorded recipe says which one was actually used.
        used = recipe
        if recipe == "content_missing" and not bbox:
            used = "flat"
        derive(src, dst, used, background=background, bbox=bbox)
        samples.append((sid, dst,
                        {"kind": "derived", "recipe": used,
                         "recipe_requested": recipe, "source": rel,
                         "source_sha256": sha256_file(src),
                         "derived_sha256": sha256_file(dst),
                         "background_rgb": background, "content_bbox": bbox,
                         "note": note}, used))
    return samples


def probe_one(agent, sample_id, path, provenance, sample_index):
    frames = [frame_meta(path, sample_index, provenance.get("source_sha256")
                         if provenance["kind"] == "real-capture"
                         else provenance.get("derived_sha256"))]
    t0 = time.time()
    action = agent.decide(frames, {}, GOAL)
    wall = round(time.time() - t0, 3)
    evidence = agent.calls[-1] if agent.calls else {}
    verdict = agent.threshold_verdict()
    return {"sample": sample_id, "provenance": provenance, "wall_seconds": wall,
            "action": action, "verdict": verdict, "evidence": evidence}


def run(argv=None):
    ap = argparse.ArgumentParser(description="local PlayJev end-to-end probe (TASK-127)")
    ap.add_argument("--base-url", default="")
    ap.add_argument("--out", default=OUT_DEFAULT)
    ap.add_argument("--frame-dir", default=FRAME_DIR_DEFAULT)
    ap.add_argument("--timeout", type=float, default=300.0)
    ap.add_argument("--action-steps", type=int, default=3)
    ap.add_argument("--abstain-min-confidence", type=float, default=0.0,
                    help="TASK-127 P9: a confidence below this is an ABSTAIN.  The "
                         "deployed serve.py never sends `abstain`, so this is how a REAL "
                         "abstain is constructed against the REAL service: run once with "
                         "0.0 (normal) and once above the observed confidence (e.g. 0.5) "
                         "and the same answers become undecidable instead of a pass.")
    args = ap.parse_args(argv)

    samples = build_samples(args.frame_dir)
    if not samples:
        print("no sample frames found under %s -- run the exe gate first" % RUNS)
        return 2

    opts = {"timeout": args.timeout, "invariant_questions": 1, "score_question": True,
            "abstain_min_confidence": args.abstain_min_confidence}
    if args.base_url:
        opts["base_url"] = args.base_url
    agent = PlayJevAgent("pong", GOAL["objective"], opts)

    health = agent.check_health()
    doc = {
        "task": "TASK-127",
        "purpose": "local end-to-end evidence: one real screenshot + 3 questions "
                   "(move / playable / brokenness) per request, against the LOCAL "
                   "PlayJev service only",
        "third_party_endpoints_used": [],
        "endpoint": agent.base_url + agent.decision_path,
        "model": agent.model,
        "answer_model": None,
        "abstain_min_confidence": agent.abstain_min_confidence,
        "health": health,
        "goal": GOAL,
        "questions": None,
        "samples": [],
        "started_utc": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "python": sys.version,
    }

    # one throwaway build to record the exact question set (no HTTP)
    try:
        q, roles = agent.build_questions(GOAL)
        doc["questions"] = {"questions": q, "roles": dict(
            (k, v["role"]) for k, v in roles.items())}
    except Exception as e:  # noqa: BLE001
        doc["questions_error"] = "%s: %s" % (type(e).__name__, e)

    checks = []
    for i, (sid, path, prov, _recipe) in enumerate(samples):
        r = probe_one(agent, sid, path, prov, i)
        doc["samples"].append(r)
        ev = r["evidence"] or {}
        st = (ev.get("transport") or {}).get("status")
        doc["answer_model"] = (ev.get("model") or doc["answer_model"])
        checks.append({
            "sample": sid,
            "http_200": st == 200,
            "parsed": bool(ev.get("answers_classified")),
            "questions_answered": sorted((ev.get("answers_classified") or {}).keys()),
            "abstain": ev.get("abstain"),
            "abstained_questions": ev.get("abstained_questions"),
            "probabilities_present": all(
                bool((a or {}).get("probabilities"))
                for a in (ev.get("answers_classified") or {}).values()),
            "action_type": (r["action"] or {}).get("type"),
        })
        print("[%d/%d] %-30s status=%s abstain=%s action=%s"
              % (i + 1, len(samples), sid, st, ev.get("abstain"),
                 (r["action"] or {}).get("type")))

    doc["checks"] = checks
    doc["ok"] = all(c["http_200"] and c["parsed"] and c["probabilities_present"]
                    for c in checks)
    doc["finished_utc"] = time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())
    doc["errors"] = agent.errors

    os.makedirs(os.path.dirname(args.out), exist_ok=True)
    with open(args.out, "w", encoding="utf-8") as fh:
        json.dump(doc, fh, ensure_ascii=False, indent=1)
    print("probe: ok=%s  samples=%d  written to %s" % (doc["ok"], len(checks),
                                                       os.path.abspath(args.out)))
    return 0 if doc["ok"] else 1


if __name__ == "__main__":
    sys.exit(run())
