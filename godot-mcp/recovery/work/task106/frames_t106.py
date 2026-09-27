#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""TASK-106 part A: independently recompute the pixel differences of the frames
the re-run saved by name (`snake-t0/t1/t2/final.png`), not of the whole `user://`
directory.

`tools/game_report.py` diffs every PNG in `user://` against the previous frame of
the same size, which is why its table also carries probes left over from earlier
tasks. This script takes only the four frames of this task's session, in the order
the session wrote them, and applies both rules itself:

  * `engine` - max(|dr|,|dg|,|db|) > 10, the rule `mcp_capture.cpp:68` documents;
  * `any`    - any byte difference at all (strictly stronger).

It also recomputes the capture-pair column from the traces with the same two rules
and prints every non-zero pair, so the report's aggregate can be re-derived.

    python frames_t106.py <run-dir> <user-dir>
"""
import glob
import hashlib
import io
import json
import os
import sys

import numpy as np
from PIL import Image

NAMES = ["snake-t0.png", "snake-t1.png", "snake-t2.png", "snake-final.png"]
RESULT = []


def say(line=""):
    print(line)
    RESULT.append(line)


def sha256(path):
    with open(path, "rb") as handle:
        return hashlib.sha256(handle.read()).hexdigest().upper()


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
    run = os.path.abspath(sys.argv[1])
    user = os.path.abspath(sys.argv[2])

    say("== frames saved by this session (user:// = %s)" % user)
    frames = []
    for name in NAMES:
        path = os.path.join(user, name)
        if not os.path.isfile(path):
            say("   %-16s ABSENT" % name)
            continue
        with Image.open(path) as im:
            size = (im.width, im.height)
        frames.append({"name": name, "path": path, "size": size,
                       "bytes": os.path.getsize(path), "sha256": sha256(path),
                       "mtime": os.path.getmtime(path)})
        say("   %-16s %s  %d B  sha256=%s  mtime=%.1f" % (
            name, "x".join(str(v) for v in size), os.path.getsize(path),
            sha256(path)[:16], os.path.getmtime(path)))

    say("")
    say("== consecutive diffs among those frames (recomputed here, both rules)")
    if len(frames) >= 2:
        say("   %-16s -> %-16s %-9s %-9s %s" % ("before", "after", "engine>10", "any", "total"))
        for a, b in zip(frames, frames[1:]):
            d = diff(a["path"], b["path"])
            if not d.get("comparable"):
                say("   %-16s -> %-16s NOT COMPARABLE" % (a["name"], b["name"]))
                continue
            say("   %-16s -> %-16s %-9d %-9d %d" % (
                a["name"], b["name"], d["engine"], d["any"], d["total"]))
    say("   distinct frame sha256 values: %d (frames kept: %d)" % (
        len(set(f["sha256"] for f in frames)), len(frames)))

    say("")
    say("== capture pairs recomputed from the run's own traces")
    for trace in ("trace-editor.jsonl", "trace-game.jsonl"):
        path = os.path.join(run, trace)
        if not os.path.isfile(path):
            say("   %s ABSENT" % trace)
            continue
        pairs = []
        with io.open(path, encoding="utf-8-sig") as handle:
            for line in handle:
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
                if not (before and after and os.path.isfile(before) and os.path.isfile(after)):
                    continue
                d = diff(before, after)
                d["seq"] = rec.get("seq")
                d["tool"] = rec.get("tool")
                d["reported"] = rec.get("changed_pixels")
                pairs.append(d)
        comparable = [p for p in pairs if p.get("comparable")]
        nonzero = [p for p in comparable if p["engine"] > 0]
        mismatch = [p for p in comparable if p["reported"] is not None and p["reported"] != p["engine"]]
        say("   %s: pairs=%d comparable=%d non-zero=%d" % (trace, len(pairs), len(comparable), len(nonzero)))
        for p in nonzero:
            say("     seq=%-4s %-42s engine=%-7d any=%-7d reported=%s" % (
                p["seq"], p["tool"], p["engine"], p["any"], p["reported"]))
        say("     reported != recomputed: %d" % len(mismatch))
        for p in mismatch:
            say("       seq=%s reported=%s recomputed=%s" % (p["seq"], p["reported"], p["engine"]))

    if len(sys.argv) > 3:
        with io.open(sys.argv[3], "w", encoding="utf-8", newline="\n") as handle:
            handle.write("\n".join(RESULT) + "\n")
    return 0


if __name__ == "__main__":
    sys.exit(main())
