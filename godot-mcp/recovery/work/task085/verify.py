# -*- coding: utf-8 -*-
"""Validate a reconstruction against the recorded read windows of one revision:
every line the newest windows cover must appear, byte for byte, at that line
number.

usage: python verify.py <subpath> <recon-path> [rev]
"""
import io
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import evfetch as E  # noqa: E402


def main():
    sub = sys.argv[1]
    recp = sys.argv[2]
    rev = int(sys.argv[3]) if len(sys.argv) > 3 else None
    skel, rev = E.skeleton(sub, rev)
    lines = E.lines_of(recp)
    print("recon %d lines   skeleton rev=%s covering %d lines" % (len(lines), rev, len(skel)))
    bad = []
    for no in sorted(skel):
        if no < 1 or no > len(lines):
            bad.append((no, skel[no], "<out of range>"))
            continue
        if lines[no - 1].rstrip("\r") != skel[no].rstrip("\r"):
            bad.append((no, skel[no], lines[no - 1]))
    print("line mismatches: %d / %d" % (len(bad), len(skel)))
    for no, want, got in bad[:60]:
        print("  %5d WANT| %s" % (no, want[:150]))
        print("        GOT | %s" % (got[:150]))


if __name__ == "__main__":
    main()
