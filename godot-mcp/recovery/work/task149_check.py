#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""TASK-149 read-only reconnaissance: sizes, hashes, line counts, grep hits.

No shell redirection is used anywhere: everything is printed to stdout by this process.
"""
import hashlib
import io
import json
import os
import subprocess
import sys

ROOT = r"F:\moonbit-hof-rs"
MCP = os.path.join(ROOT, "godot-mcp")


def sha256(p):
    h = hashlib.sha256()
    with open(p, "rb") as fh:
        for chunk in iter(lambda: fh.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def wc(p):
    try:
        with io.open(p, "rb") as fh:
            return fh.read().count(b"\n") + 1
    except Exception as exc:  # noqa: BLE001
        return "ERR:%s" % exc


def main():
    targets = json.loads(sys.argv[1])
    for rel in targets:
        p = os.path.join(ROOT, rel)
        if not os.path.exists(p):
            print("MISSING %s" % rel)
            continue
        print("%s | bytes=%d | lines=%s | sha256=%s" % (
            rel, os.path.getsize(p), wc(p), sha256(p)))


if __name__ == "__main__":
    main()
