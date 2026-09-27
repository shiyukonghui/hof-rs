# -*- coding: utf-8 -*-
"""TASK-139 recon: show the SHAPE of one recorded step record (keys, nesting, sizes)."""
from __future__ import print_function

import io
import json
import os
import sys

ROOT = os.path.abspath(os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", ".."))


def shape(obj, depth=0, maxdepth=4):
    pad = "  " * depth
    if isinstance(obj, dict):
        for k in sorted(obj):
            v = obj[k]
            if isinstance(v, (dict, list)) and depth < maxdepth:
                print("%s%s: %s(n=%s)" % (pad, k, type(v).__name__, len(v)))
                shape(v, depth + 1, maxdepth)
            else:
                s = json.dumps(v, ensure_ascii=False)
                print("%s%s = %s" % (pad, k, s[:120]))
    elif isinstance(obj, list):
        print("%s[list of %d]" % (pad, len(obj)))
        if obj and depth < maxdepth:
            shape(obj[0], depth + 1, maxdepth)


def main(argv):
    path = argv[0]
    idx = int(argv[1]) if len(argv) > 1 else 0
    lines = [l for l in io.open(path, encoding="utf-8").read().splitlines() if l.strip()]
    rec = json.loads(lines[idx])
    print("FILE %s  lines=%d  reading step index %d" % (path, len(lines), idx))
    print("TOP-LEVEL KEYS: %s" % sorted(rec.keys()))
    shape(rec)
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
