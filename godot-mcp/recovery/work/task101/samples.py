# -*- coding: utf-8 -*-
"""TASK-098: summarise a multi-frame property sample from a run directory.

Prints, for each sampled property: the number of distinct values, the first and
the last value, and the frame index of every change. The point of a multi-frame
sample is that the change is visible frame by frame rather than asserted once.
"""
import io
import json
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from callread import load, text_of  # noqa: E402  (the local helper module)


def main():
    run = sys.argv[1]
    for tag in sys.argv[2:]:
        doc = load(run, tag)
        payload = json.loads(text_of(doc))
        rows = payload.get("samples") or []
        print("=== %s (%d frames) ===" % (tag, len(rows)))
        if not rows:
            print("  no samples")
            continue
        props = [k for k in rows[0].keys()]
        for prop in props:
            values = [row.get(prop) for row in rows]
            changes = [i for i in range(1, len(values)) if values[i] != values[i - 1]]
            distinct = len(set(repr(v) for v in values))
            print("  %-22s distinct=%-4d changes@=%s" % (prop, distinct, changes[:12]))
            print("      first=%r  last=%r" % (values[0], values[-1]))
        print()


if __name__ == "__main__":
    main()
