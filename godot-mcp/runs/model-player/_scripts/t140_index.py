# -*- coding: utf-8 -*-
"""TASK-140 §1.C.8: build the artifact index for this batch and print its identity.

Steps (all through this process, no shell):
  1. remove the smoke/preview files this batch created for testing;
  2. run `tools/playtest_artifact_index.py` over THIS batch's run prefixes
     (`--full` off: a per-directory digest, exactly like TASK-139's index);
  3. print the index files' paths, sizes and sha256 so the report can quote them.

Usage (through the ledger wrapper):
    t140_cmd.py --cwd F:\\moonbit-hof-rs\\godot-mcp -- <py> runs\\model-player\\_scripts\\t140_index.py
"""
from __future__ import print_function

import hashlib
import io
import os
import subprocess
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.abspath(os.path.join(HERE, "..", "..", ".."))
PY = r"D:\Anaconda\python.exe"
IDX = os.path.join(ROOT, "tools", "playtest_artifact_index.py")

ROOTS = [
    "t140-prefix4-w90-r1", "t140-postfix4-w90-r1", "t140-postfix4-w90-r2",
    "t140-postfix4-w90-r3",
    "t140-scripted-w90-r1", "t140-scripted-w90-r2",
    "t140-jev-v3-w90-r1", "t140-jev-v3-w90-r2",
    "t140-playjev-v3-w90-r1", "t140-playjev-v3-w90-r2",
    "t140-w30-demo", "t140-respawn-demo",
]
STALE = ["ARTIFACTS-TASK-140-SMOKE.json", "ARTIFACTS-TASK-140-SMOKE.md",
         "t140_stability_model_r1preview.json"]


def sha(p):
    h = hashlib.sha256()
    with open(p, "rb") as fh:
        for c in iter(lambda: fh.read(1 << 16), b""):
            h.update(c)
    return h.hexdigest()


def main():
    for name in STALE:
        for d in (os.path.join(ROOT, "runs", "model-player", "_index"), HERE):
            p = os.path.join(d, name)
            if os.path.isfile(p):
                os.remove(p)
                print("removed stale %s" % p)
    out = os.path.join(ROOT, "runs", "model-player", "_index", "ARTIFACTS-TASK-140.json")
    outmd = os.path.join(ROOT, "runs", "model-player", "_index", "ARTIFACTS-TASK-140.md")
    cmd = [PY, IDX, "--task", "TASK-140", "--roots"] + ROOTS + \
          ["--out", out, "--out-md", outmd]
    p = subprocess.Popen(cmd, cwd=ROOT, stdout=subprocess.PIPE,
                         stderr=subprocess.STDOUT, shell=False)
    o, _ = p.communicate()
    print(o.decode("utf-8", "replace").strip())
    print("index exit=%s" % p.returncode)
    for f in (out, outmd):
        if os.path.isfile(f):
            print("%s  bytes=%d sha256=%s" % (f, os.path.getsize(f), sha(f)))
    return 0 if p.returncode == 0 else 1


if __name__ == "__main__":
    sys.exit(main())
