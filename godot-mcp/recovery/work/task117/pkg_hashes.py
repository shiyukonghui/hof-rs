#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""TASK-117: write dist\\godot-mcp-20games-playable-<ts>.sha256.txt for the two parts."""
import hashlib
import io
import json
import os

ROOT = r"F:\moonbit-hof-rs\godot-mcp"
WORK = os.path.join(ROOT, "recovery", "work", "task117")
DIST = os.path.join(ROOT, "dist")


def sha256(path):
    h = hashlib.sha256()
    with open(path, "rb") as fh:
        for c in iter(lambda: fh.read(1 << 20), b""):
            h.update(c)
    return h.hexdigest()


def main():
    recs = json.load(io.open(os.path.join(WORK, "package-results.json"), encoding="utf-8-sig"))
    stamp = None
    lines = []
    for r in recs:
        p = r["zip"]
        got = sha256(p)
        size = os.path.getsize(p)
        ok = (got == r["zip_sha256"] and size == r["zip_bytes"])
        lines.append("%s  %d  %s  %s" % (got, size, os.path.basename(p),
                                         "MATCHES-package-results" if ok else "MISMATCH"))
        name = os.path.basename(p)
        m = name.replace("godot-mcp-20games-playable-", "").split("-part")[0]
        stamp = stamp or m
        print("%s  %d  %s" % (got, size, name))
    out = os.path.join(DIST, "godot-mcp-20games-playable-%s.sha256.txt" % stamp)
    with io.open(out, "w", encoding="utf-8", newline="\n") as fh:
        fh.write("# TASK-117 -- 20 games, playable re-export (TASK-116 fix included)\n")
        fh.write("# format: <sha256>  <bytes>  <file>  <verification>\n")
        fh.write("\n".join(lines) + "\n")
    print("wrote %s" % out)


if __name__ == "__main__":
    main()
