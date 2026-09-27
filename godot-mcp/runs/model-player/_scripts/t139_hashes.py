# -*- coding: utf-8 -*-
"""TASK-139: the hash table this batch's report is built from.

Prints `path | sha256 | bytes` for the artifacts the report cites, so every number in the
report can be recomputed with `certutil -hashfile <path> SHA256` or by re-running this file.

Usage (cmd):
    D:\\Anaconda\\python.exe runs\\model-player\\_scripts\\t139_hashes.py
"""
from __future__ import print_function

import glob
import hashlib
import io
import json
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.abspath(os.path.join(HERE, "..", "..", ".."))   # ...\godot-mcp
REPO = os.path.dirname(ROOT)                                   # F:\moonbit-hof-rs

FILES = [
    "tools/playtest_player.py",
    "tools/playability_gate.py",
    "tools/playability_controls.json",
    "tools/playtest_artifact_index.py",
    "tools/tests/test_playability_model_player.py",
    "../DECISIONS.md",
    "recovery/tasks/TEMPLATE-logic-feedback.md",
    "recovery/tasks/TASK-139.md",
]
SCRIPT_FILES = sorted(glob.glob(os.path.join(HERE, "t139_*.py")))
DATA_FILES = sorted(glob.glob(os.path.join(HERE, "t139_*.json")))
LOG_FILES = sorted(glob.glob(os.path.join(HERE, "t139_*.log")))
INDEX_FILES = sorted(glob.glob(os.path.join(ROOT, "runs", "model-player", "_index",
                                            "ARTIFACTS-TASK-139.*")))


def sha256_file(p):
    h = hashlib.sha256()
    with open(p, "rb") as fh:
        for chunk in iter(lambda: fh.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def show(p, label=None):
    if not os.path.isfile(p):
        print("MISSING %s" % p)
        return
    print("%-64s %s %8d  %s"
          % (os.path.relpath(p, REPO).replace("\\", "/"), sha256_file(p),
             os.path.getsize(p), label or ""))


def main(argv):
    print("== code + documents ==")
    for rel in FILES:
        show(os.path.join(ROOT, rel))
    print("== this batch's scripts ==")
    for p in SCRIPT_FILES:
        show(p)
    print("== this batch's data ==")
    for p in DATA_FILES:
        show(p)
    print("== this batch's logs ==")
    for p in LOG_FILES:
        show(p)
    print("== committed index ==")
    for p in INDEX_FILES:
        show(p)
    print("== ledger ==")
    show(os.path.join(HERE, "t136_commands.jsonl"))
    print("== key run artifacts ==")
    for rel in ("t139-scripted-w30/asteroids/scripted",
                "t139-scripted-w90/asteroids/scripted",
                "t139-jev-v3-w30/asteroids/jev",
                "t139-jev-v3-w90/asteroids/jev",
                "t139-jev-v3-w90/asteroids/jev/frames/022_07_after.png",
                "t139-jev-v3-w90/asteroids/jev/frames/037_12_after.png",
                "t139-scripted-w30/match3/scripted",
                "t139-playjev-v3-w30/pacman/playjev"):
        p = os.path.join(ROOT, "runs", "model-player", rel)
        if os.path.isdir(p):
            for name in ("player.json", "steps.jsonl", "demo.png"):
                show(os.path.join(p, name))
        else:
            show(p)
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
