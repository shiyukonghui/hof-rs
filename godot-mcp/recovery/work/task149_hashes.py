#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""TASK-149 report helper: print the committed hashes of the key artifacts.

For each artifact listed in the report's section F, this prints
`path | git-blob-hash-at-HEAD | sha256-of-the-worktree-file | bytes | lines`.
The git blob hash is the durable identity (it does not depend on the worktree), and it is
what a later reader can recompute with `git rev-parse HEAD:<path>`.

Read-only; stdout only.
"""
from __future__ import print_function

import hashlib
import io
import os
import subprocess

ROOT = r"F:\moonbit-hof-rs"
ARTIFACTS = [
    "godot-mcp/recovery/reports/TASK-149-REPORT.md",
    "godot-mcp/recovery/reports/ERRATA.md",
    "godot-mcp/recovery/TEST-CASES.md",
    "godot-mcp/recovery/tasks/TASK-149.md",
    "DECISIONS.md",
    "godot-mcp/TOOL-COVERAGE.md",
    "godot-mcp/GAME-LOOP-LOG.md",
    "godot-mcp/recovery/reports/PLAYABILITY-REPORT.md",
    "godot-mcp/recovery/reports/PLAYABILITY-DEFECTS.md",
    "godot-mcp/recovery/tasks/README.md",
    "godot-mcp/recovery/tasks/TEMPLATE-logic-feedback.md",
    "godot-mcp/recovery/reports/ACCEPTANCE-TASK-137.md",
    "godot-mcp/recovery/reports/ACCEPTANCE-TASK-141.md",
    "godot-mcp/recovery/reports/ACCEPTANCE-TASK-145.md",
    "godot-mcp/recovery/reports/ACCEPTANCE-TASK-147.md",
    "godot-mcp/tools/playtest_player_t142_prefix.py",
    "godot-mcp/recovery/work/task149_docaudit.py",
    "godot-mcp/recovery/work/task149_ledger.py",
    "godot-mcp/recovery/work/task149_stalepointers.py",
    "godot-mcp/recovery/work/task149_frozenmap.py",
    "godot-mcp/recovery/work/task149_pointers.py",
    "godot-mcp/recovery/work/task149_negclass.py",
    "godot-mcp/recovery/work/task149_probeshape.py",
    "godot-mcp/recovery/work/task149_stage.py",
]


def sha256(path):
    digest = hashlib.sha256()
    with open(path, "rb") as handle:
        for chunk in iter(lambda: handle.read(1 << 20), b""):
            digest.update(chunk)
    return digest.hexdigest()


def git_blob(rel):
    proc = subprocess.run(["git", "rev-parse", "HEAD:" + rel], cwd=ROOT,
                          stdout=subprocess.PIPE, stderr=subprocess.DEVNULL)
    if proc.returncode != 0:
        return "<untracked>"
    return proc.stdout.decode().strip()


def main():
    print("%-58s %-41s %-64s %10s %7s"
          % ("path", "git blob @HEAD", "sha256 (worktree)", "bytes", "lines"))
    for rel in ARTIFACTS:
        full = os.path.join(ROOT, rel.replace("/", os.sep))
        if not os.path.exists(full):
            print("%-58s %-41s %-64s %10s %7s"
                  % (rel, "<missing>", "<missing>", "-", "-"))
            continue
        with io.open(full, "rb") as handle:
            lines = handle.read().count(b"\n") + 1
        print("%-58s %-41s %-64s %10d %7d"
              % (rel, git_blob(rel), sha256(full), os.path.getsize(full), lines))


if __name__ == "__main__":
    main()
