# -*- coding: utf-8 -*-
"""TASK-139: freeze the CODE REVISION the sweeps are run against.

A batch that changes the tool and then measures with it has to say WHICH revision produced
the numbers.  This prints (and records) the sha256 + size of every file this batch owns or
changed, so "the sweep used this code" is checkable after the fact even though the files
themselves keep moving during the batch.

Writes `t139_code_revision.json` (append-style: one snapshot per call, newest last).
"""
from __future__ import print_function

import hashlib
import io
import json
import os
import sys
import time

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.abspath(os.path.join(HERE, "..", "..", ".."))
OUT = os.path.join(HERE, "t139_code_revision.json")

FILES = ["tools/playtest_player.py", "tools/playability_gate.py",
         "tools/playability_controls.json", "tools/playtest_artifact_index.py",
         "tools/tests/test_playability_model_player.py",
         "runs/model-player/_scripts/t139_cmd.py",
         "runs/model-player/_scripts/t139_sweep.py",
         "runs/model-player/_scripts/t139_sensitivity.py",
         "runs/model-player/_scripts/t139_determinism.py",
         "runs/model-player/_scripts/t139_compare.py",
         "runs/model-player/_scripts/t139_scan_redirects.py"]


def sha256_file(p):
    h = hashlib.sha256()
    with open(p, "rb") as fh:
        for chunk in iter(lambda: fh.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def main(argv):
    label = argv[0] if argv else "snapshot"
    snap = {"when": time.strftime("%Y-%m-%dT%H:%M:%S"), "label": label, "files": {}}
    for rel in FILES:
        p = os.path.join(ROOT, rel)
        if os.path.isfile(p):
            snap["files"][rel.replace("\\", "/")] = {
                "sha256": sha256_file(p), "bytes": os.path.getsize(p)}
        else:
            snap["files"][rel.replace("\\", "/")] = {"missing": True}
    hist = []
    if os.path.isfile(OUT):
        try:
            hist = json.load(io.open(OUT, encoding="utf-8"))
        except Exception:  # noqa: BLE001
            hist = []
    hist.append(snap)
    with io.open(OUT, "w", encoding="utf-8") as fh:
        fh.write(json.dumps(hist, ensure_ascii=False, indent=1))
    for rel, v in sorted(snap["files"].items()):
        print("%-58s %s %s" % (rel, v.get("sha256", "<missing>")[:16], v.get("bytes")))
    print("snapshot %r appended to %s (%d snapshots)" % (label, OUT, len(hist)))
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
