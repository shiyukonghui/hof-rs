# -*- coding: utf-8 -*-
"""TASK-144: sha256 of the key artifacts, printed ASCII-only."""
import hashlib
import io
import os

ROOT = r"F:\moonbit-hof-rs\godot-mcp"
REPO = r"F:\moonbit-hof-rs"
PATHS = [
    os.path.join(REPO, "DECISIONS.md"),
    os.path.join(ROOT, "tools", "verify_coverage_batch.py"),
    os.path.join(ROOT, "tools", "tests", "test_coverage_batch_consistency.py"),
    os.path.join(ROOT, "tools", "tool_channels.json"),
    os.path.join(ROOT, "coverage.json"),
    os.path.join(ROOT, "recovery", "TEST-CASES.md"),
    os.path.join(ROOT, "recovery", "work", "task144", "batch-before.json"),
    os.path.join(ROOT, "recovery", "work", "task144", "batch-after.json"),
    os.path.join(ROOT, "recovery", "work", "task144", "probe-u2.json"),
    os.path.join(ROOT, "recovery", "work", "task144", "probe_u2.py"),
    os.path.join(ROOT, "recovery", "work", "task144", "check_recompute.py"),
    os.path.join(ROOT, "recovery", "work", "task144", "three_reds.py"),
    os.path.join(ROOT, "recovery", "work", "task144", "three_reds_trace.py"),
    os.path.join(ROOT, "recovery", "work", "task144", "build-local.log"),
    os.path.join(ROOT, "recovery", "work", "task144", "build-mono.log"),
    os.path.join(ROOT, "runs", "gates", "task144", "summary.txt"),
    os.path.join(ROOT, "godot", "bin", "godot.windows.editor.x86_64.console.exe"),
    os.path.join(ROOT, "godot", "bin", "godot.windows.editor.x86_64.mono.console.exe"),
]
for path in PATHS:
    if not os.path.isfile(path):
        print("MISSING            %s" % path)
        continue
    digest = hashlib.sha256()
    with io.open(path, "rb") as handle:
        for chunk in iter(lambda: handle.read(1 << 20), b""):
            digest.update(chunk)
    print("%s  %10d  %s" % (digest.hexdigest().upper(), os.path.getsize(path), path))
