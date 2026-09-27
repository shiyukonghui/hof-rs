#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""TASK-106 / iron rule 6: the sha256 manifest of one directory tree, written
BEFORE anything is moved, archived or removed.

    python hash_tree.py <directory> <manifest.json>

Every regular file is recorded with its size and its sha256, sorted by relative
path, so the archived evidence can be re-verified byte for byte afterwards.
Written by a Python writer, never by a shell redirect (iron rule 1).

Adapted from recovery/work/task103/hash_tree.py (same tool, new task).
"""
import hashlib
import io
import json
import os
import sys


def sha256(path):
    handle = open(path, "rb")
    try:
        digest = hashlib.sha256()
        while True:
            chunk = handle.read(1 << 20)
            if not chunk:
                break
            digest.update(chunk)
        return digest.hexdigest()
    finally:
        handle.close()


def main():
    directory = os.path.abspath(sys.argv[1])
    manifest_path = os.path.abspath(sys.argv[2])
    entries = []
    total = 0
    for root, dirs, files in os.walk(directory):
        dirs.sort()
        for name in sorted(files):
            path = os.path.join(root, name)
            relative = os.path.relpath(path, directory).replace("\\", "/")
            size = os.path.getsize(path)
            total += size
            entries.append({"path": relative, "bytes": size, "sha256": sha256(path)})
    manifest = {"root": directory, "files": len(entries), "bytes": total, "entries": entries}
    os.makedirs(os.path.dirname(manifest_path), exist_ok=True)
    with io.open(manifest_path, "w", encoding="utf-8", newline="\n") as handle:
        json.dump(manifest, handle, ensure_ascii=False, indent=1)
        handle.write("\n")
    print("manifest: %s" % manifest_path)
    print("files   : %d" % len(entries))
    print("bytes   : %d" % total)


if __name__ == "__main__":
    main()
