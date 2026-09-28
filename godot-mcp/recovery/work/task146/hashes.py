#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""sha256 + size of the TASK-146 artifacts (written through a file handle)."""
import hashlib
import io
import os

HERE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.abspath(os.path.join(HERE, "..", "..", ".."))
FILES = [
    "recovery/TEST-CASES.md",
    "tools/tests/test_matrix_self_consistency.py",
    "recovery/work/task146/recount.py",
    "recovery/work/task146/py_rows.py",
    "recovery/work/task146/probe_names.py",
    "recovery/work/task146/red_proof.py",
    "recovery/work/task146/red-proof.json",
]


def main():
    for rel in FILES:
        path = os.path.join(REPO, rel.replace("/", os.sep))
        digest = hashlib.sha256()
        with io.open(path, "rb") as handle:
            for chunk in iter(lambda: handle.read(65536), b""):
                digest.update(chunk)
        print("%s  %d  %s" % (digest.hexdigest().upper(), os.path.getsize(path), rel))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
