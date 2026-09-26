# -*- coding: utf-8 -*-
"""TASK-098: independently recompute the `user://` screenshot chain of a game.

    python frames_recompute.py <game> <prefix> [<run-dir>]

The per-call capture pairs already have an independent recomputation
(`pixel_recompute.py`). The frames a session saves by name are the ones the
evidence column actually quotes -- "the win screen looks like this" -- so they get
their own recomputation here, from the PNG bytes on disk, with:

  * sha256 of every frame, so "these two frames are the same picture" is checkable;
  * both diff rules (>10 and any-difference);
  * a comparison against the number `tools/game_report.py` wrote in report.json,
    when a run directory is given.

The frames are found by mtime order, which is the order the session wrote them.
"""
import glob
import hashlib
import io
import json
import os
import sys

import numpy as np
from PIL import Image

USER = os.path.join(os.environ.get("APPDATA", ""), "Godot", "app_userdata")


def sha256(path):
    handle = open(path, "rb")
    try:
        return hashlib.sha256(handle.read()).hexdigest().upper()
    finally:
        handle.close()


def diff(a, b):
    ia = np.asarray(Image.open(a).convert("RGBA"), dtype=np.int16)
    ib = np.asarray(Image.open(b).convert("RGBA"), dtype=np.int16)
    if ia.shape != ib.shape:
        return {"comparable": False}
    rgb = np.abs(ia[:, :, :3] - ib[:, :, :3])
    return {
        "comparable": True,
        "engine": int((rgb.max(axis=2) > 10).sum()),
        "any": int((rgb.sum(axis=2) > 0).sum()),
        "total": int(ia.shape[0] * ia.shape[1]),
    }


def main():
    game = sys.argv[1]
    prefix = sys.argv[2]
    run = sys.argv[3] if len(sys.argv) > 3 else None
    directory = os.path.join(USER, game)
    paths = sorted(glob.glob(os.path.join(directory, prefix + "*.png")),
                   key=os.path.getmtime)
    print("== %s : %d frame(s) in %s" % (game, len(paths), directory))
    if not paths:
        return 1

    reported = {}
    if run:
        with io.open(os.path.join(run, "report.json"), "r", encoding="utf-8") as handle:
            rep = json.load(handle)
        for frame in (rep.get("saved_frames") or {}).get("frames") or []:
            reported[frame["name"]] = frame

    rows = []
    for path in paths:
        name = os.path.basename(path)
        with Image.open(path) as im:
            size = [im.width, im.height]
        rows.append({"name": name, "path": path, "bytes": os.path.getsize(path),
                     "sha256": sha256(path), "size": size})

    print("  %-12s %-9s %8s  %-16s %s" % ("frame", "size", "bytes", "sha256[0:16]", "vs report"))
    for row in rows:
        ref = reported.get(row["name"])
        agree = "-"
        if ref is not None:
            agree = "same" if (ref["sha256"] == row["sha256"]
                               and ref["bytes"] == row["bytes"]) else "DIFFERS"
        print("  %-12s %-9s %8d  %-16s %s"
              % (row["name"], "x".join(str(v) for v in row["size"]), row["bytes"],
                 row["sha256"][:16], agree))
    print("  distinct sha256 among the frames: %d/%d"
          % (len(set(r["sha256"] for r in rows)), len(rows)))

    mismatches = 0
    print("  pair diffs (recomputed here):")
    for i in range(1, len(rows)):
        a, b = rows[i - 1], rows[i]
        result = diff(a["path"], b["path"])
        if not result.get("comparable"):
            print("    %-16s -> %-16s NOT COMPARABLE (size %s vs %s)"
                  % (a["name"], b["name"], a["size"], b["size"]))
            continue
        rep_num = None
        ref = reported.get(b["name"])
        if ref is not None:
            rep_num = (ref.get("diff_vs_prev") or {}).get("changed_pixels")
        flag = ""
        if rep_num is not None and rep_num != result["engine"]:
            flag = "  <<< DISAGREES with report.json (%s)" % rep_num
            mismatches += 1
        elif rep_num is not None:
            flag = "  (report.json agrees)"
        print("    %-12s -> %-12s engine=%-7d any=%-7d total=%d%s"
              % (a["name"], b["name"], result["engine"], result["any"], result["total"], flag))
    print("  pairs where the report and this recomputation disagree: %d" % mismatches)
    return 0


if __name__ == "__main__":
    sys.exit(main())
