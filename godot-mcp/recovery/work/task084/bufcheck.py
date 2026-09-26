# -*- coding: utf-8 -*-
"""Inspect the replayed buffer of a file for marker symbols and duplicates."""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import rec  # noqa: E402


def main():
    sub = sys.argv[1]
    buf, st = rec.replay(sub, verbose=True)
    if buf and buf[-1] == "":
        buf = buf[:-1]
    print("buffer lines = %d" % len(buf))
    for sym in sys.argv[2:]:
        hits = [i + 1 for i, l in enumerate(buf) if sym in l]
        print("  %-40s %d hit(s) %s" % (sym, len(hits), hits[:12]))


if __name__ == "__main__":
    main()
