# TASK-097 (B): independently recompute the pixel differences of one run.
#
#   python pixel_recompute.py <run-dir> [<run-dir> ...]
#
# This is deliberately NOT a call into tools/game_report.py: it re-reads the run's
# own `trace-editor.jsonl` / `trace-game.jsonl`, takes every `capture` / `done`
# record's before/after PNG pair, and recomputes the difference itself, twice:
#
#   * `engine`  - max(|dr|,|dg|,|db|) > 10, the rule `mcp_capture.cpp:68`
#                 documents, so the number can be compared with the ledger's;
#   * `any`     - any byte difference at all (a strictly stronger rule), so a
#                 "0" can never be an artefact of the threshold.
#
# It also reports the number of distinct PNG digests the run produced (all-equal
# digests is the signature of the frozen picture the D-1 ledger line describes).
import hashlib
import json
import os
import sys

import numpy as np
from PIL import Image


def digest(path):
    handle = open(path, "rb")
    try:
        return hashlib.sha256(handle.read()).hexdigest().upper()
    finally:
        handle.close()


def diff(a, b):
    ia = np.asarray(Image.open(a).convert("RGBA"), dtype=np.int16)
    ib = np.asarray(Image.open(b).convert("RGBA"), dtype=np.int16)
    if ia.shape != ib.shape:
        return {"comparable": False, "shape_a": list(ia.shape), "shape_b": list(ib.shape)}
    rgb = np.abs(ia[:, :, :3] - ib[:, :, :3])
    max_diff = rgb.max(axis=2)
    return {
        "comparable": True,
        "any": int((rgb.sum(axis=2) > 0).sum()),
        "engine": int((max_diff > 10).sum()),
        "total": int(ia.shape[0] * ia.shape[1]),
    }


for run in sys.argv[1:]:
    print("== %s" % run)
    for name in ("trace-editor.jsonl", "trace-game.jsonl"):
        path = os.path.join(run, name)
        if not os.path.isfile(path):
            print("   %s: ABSENT" % name)
            continue
        pairs = []
        digests = {}
        for line in open(path, encoding="utf-8"):
            line = line.strip()
            if not line:
                continue
            try:
                rec = json.loads(line)
            except ValueError:
                continue
            if rec.get("event") != "capture" or rec.get("status") != "done":
                continue
            before = (rec.get("before") or {}).get("path")
            after = (rec.get("after") or {}).get("path")
            if not before or not after:
                continue
            for p in (before, after):
                if os.path.isfile(p):
                    digests[digest(p)] = digests.get(digest(p), 0) + 1
            if not (os.path.isfile(before) and os.path.isfile(after)):
                pairs.append({"seq": rec.get("seq"), "tool": rec.get("tool"), "missing": True})
                continue
            entry = diff(before, after)
            entry["seq"] = rec.get("seq")
            entry["tool"] = rec.get("tool")
            entry["reported"] = rec.get("changed_pixels")
            entry["reported_changed"] = rec.get("changed")
            pairs.append(entry)
        comparable = [p for p in pairs if p.get("comparable")]
        nonzero_any = [p for p in comparable if p["any"] > 0]
        nonzero_engine = [p for p in comparable if p["engine"] > 0]
        print("   %s: pairs=%d comparable=%d nondistinct_digests=%d" % (
            name, len(pairs), len(comparable), len(digests)))
        print("      non-zero by engine rule (>10): %d/%d ; by any-difference rule: %d/%d" % (
            len(nonzero_engine), len(comparable), len(nonzero_any), len(comparable)))
        mismatch = [p for p in comparable if p["reported"] is not None and p["reported"] != p["engine"]]
        print("      pairs whose reported changed_pixels != the recomputed engine number: %d" % len(mismatch))
        for p in mismatch[:5]:
            print("        seq=%s tool=%s reported=%s recomputed=%s" % (
                p.get("seq"), p.get("tool"), p.get("reported"), p["engine"]))
        for p in comparable[:6]:
            print("        seq=%-4s %-42s any=%-7d engine=%-7d reported=%s" % (
                p.get("seq"), p.get("tool"), p["any"], p["engine"], p.get("reported")))
