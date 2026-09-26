# -*- coding: utf-8 -*-
"""Overlay the recorded read skeleton onto a source file, line for line.

Every line the read windows of the target revision cover is taken from the
recorded window (it is the authority); every other line is kept from the source
buffer.  The result has exactly the source's line count, so no line is invented
and no line is dropped.

usage: python overlay.py <subpath> <source-path> [--out PATH] [--report]
"""
import io
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import evfetch as E  # noqa: E402


def overlay(sub, src_lines):
    skel, rev = E.skeleton(sub)
    out = [x.rstrip("\r") for x in src_lines]
    changed = 0
    for no in sorted(skel):
        if 1 <= no <= len(out):
            want = skel[no].rstrip("\r")
            if out[no - 1] != want:
                changed += 1
            out[no - 1] = want
    return out, rev, len(skel), changed


def main():
    sub, src = sys.argv[1], sys.argv[2]
    argv = sys.argv[3:]
    lines, rev, cov, changed = overlay(sub, E.lines_of(src))
    print("source %d lines; skeleton rev=%s covers %d; replaced %d lines" % (
        len(lines), rev, cov, changed))
    if "--report" in argv:
        skel, _ = E.skeleton(sub)
        for no in sorted(skel):
            if no <= len(lines):
                pass
    out = None
    if "--out" in argv:
        out = argv[argv.index("--out") + 1]
    if out:
        with io.open(out, "w", encoding="utf-8", newline="\n") as f:
            f.write("\n".join(lines) + "\n")
        print("wrote %s" % out)


if __name__ == "__main__":
    main()
