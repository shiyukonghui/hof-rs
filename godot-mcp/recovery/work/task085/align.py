# -*- coding: utf-8 -*-
"""Walk a file against a recorded read skeleton and report where the alignment
drifts: for each skeleton line, the position in the file that the running cursor
can reach, and the offset jumps.

usage: python align.py <subpath> <path-to-file> [rev]
"""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import evfetch as E  # noqa: E402


def main():
    sub, path = sys.argv[1], sys.argv[2]
    rev = int(sys.argv[3]) if len(sys.argv) > 3 else None
    skel, rev = E.skeleton(sub, rev)
    lines = E.lines_of(path)
    print("%s: %d lines; skeleton rev=%s covering %d lines" % (os.path.basename(path), len(lines), rev, len(skel)))
    index = {}
    for i, l in enumerate(lines):
        index.setdefault(l.rstrip("\r"), []).append(i)
    cursor = 0
    prev_off = None
    bad = []
    for no in sorted(skel):
        want = skel[no].rstrip("\r")
        cands = [i for i in index.get(want, []) if i >= cursor - 2]
        if not cands:
            cands = index.get(want, [])
        if not cands:
            bad.append((no, "ABSENT", want[:100], None))
            continue
        pos = cands[0]
        off = pos - (no - 1)
        if prev_off is not None and off != prev_off:
            print("  line %5d: offset %+d -> %+d  (%s)" % (no, prev_off, off, want[:70]))
        prev_off = off
        cursor = pos + 1
    print("mismatched/absent skeleton lines: %d" % len(bad))
    for no, what, want, _ in bad[:40]:
        print("  %5d %s | %s" % (no, what, want))


if __name__ == "__main__":
    main()
