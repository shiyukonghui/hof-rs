# -*- coding: utf-8 -*-
"""TASK-140 §1.C.7: full sha256 (+ size, + pixel dimensions) for the frames that are read.

Usage (through the ledger wrapper):
    t140_cmd.py --cwd F:\\moonbit-hof-rs\\godot-mcp -- <py> runs\\model-player\\_scripts\\t140_sha.py \\
        runs\\model-player\\<prefix>\\<game>\\<backend>\\frames\\<name>.png [more...]
Globs are accepted (shell-free: this script expands them itself).
"""
from __future__ import print_function

import glob
import hashlib
import io
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.abspath(os.path.join(HERE, "..", "..", ".."))


def sha(p):
    h = hashlib.sha256()
    with open(p, "rb") as fh:
        for chunk in iter(lambda: fh.read(65536), b""):
            h.update(chunk)
    return h.hexdigest()


def dims(p):
    try:
        from PIL import Image
        with Image.open(p) as im:
            return list(im.size)
    except Exception as e:  # noqa: BLE001
        return "? (%s)" % type(e).__name__


def main(argv):
    paths = []
    for a in argv:
        if a.startswith("--"):
            continue
        full = a if os.path.isabs(a) else os.path.join(ROOT, a)
        got = sorted(glob.glob(full))
        paths.extend(got if got else [])
    if not paths:
        print("no files matched")
        return 2
    seen = set()
    for p in paths:
        if p in seen:
            continue
        seen.add(p)
        print("%s\n   bytes=%d dims=%s sha256=%s"
              % (os.path.abspath(p), os.path.getsize(p), dims(p), sha(p)))
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
