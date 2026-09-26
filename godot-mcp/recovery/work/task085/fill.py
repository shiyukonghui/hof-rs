# -*- coding: utf-8 -*-
"""Skeleton-anchored assembly.

The recorded read windows of the target revision are the backbone: every covered
line goes to its recorded absolute line number.  Each uncovered run is filled
with the recorded text that sits between the same anchors in a *source* buffer
(the tree file, or a replay buffer), which must itself be recorded text.

No line is invented: the output is either a read-window line or a source line.

usage:
  python fill.py <subpath> <source-path> [--out PATH] [--anchor N]
"""
import io
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import evfetch as E  # noqa: E402


def runs_of(nos):
    out = []
    if not nos:
        return out
    s = p = nos[0]
    for n in nos[1:]:
        if n == p + 1:
            p = n
            continue
        out.append((s, p))
        s = p = n
    out.append((s, p))
    return out


def assemble(sub, src_lines, anchor, verbose=True):
    skel, rev = E.skeleton(sub)
    covered = [n for n in range(1, rev + 1) if n in skel]
    gaps = runs_of([n for n in range(1, rev + 1) if n not in skel])
    if verbose:
        print("skeleton rev=%s: %d/%d lines covered, %d gap runs" % (rev, len(covered), rev, len(gaps)))
    skel = {n: skel[n].rstrip("\r") for n in skel}
    buf = [x.rstrip("\r") for x in src_lines]

    pos = 0
    res = []
    nxt = 1
    for a, b in gaps:
        while nxt < a:
            res.append(skel[nxt])
            nxt += 1
        before = [skel[n] for n in range(max(1, a - anchor), a) if n in skel]
        after = [skel[n] for n in range(b + 1, min(rev, b + anchor) + 1) if n in skel]
        i0 = None
        if before:
            for i in range(pos, len(buf) - len(before) + 1):
                if buf[i:i + len(before)] == before:
                    i0 = i + len(before)
                    break
        if i0 is None:
            i0 = pos
        i1 = None
        if after:
            for j in range(i0, len(buf) - len(after) + 1):
                if buf[j:j + len(after)] == after:
                    i1 = j
                    break
        if i1 is None:
            i1 = i0 + (b - a + 1)
        piece = buf[i0:i1]
        want = b - a + 1
        if verbose:
            print("  gap %4d-%-4d want %-4d got %-4d %s" % (
                a, b, want, len(piece), "OK" if len(piece) == want else "*** SIZE MISMATCH ***"))
        res.extend(piece)
        nxt = b + 1
        pos = max(pos, i1)
    while nxt <= rev:
        res.append(skel[nxt])
        nxt += 1
    if verbose:
        print("assembled %d lines (target %d)" % (len(res), rev))
    return res, rev


def main():
    sub, src = sys.argv[1], sys.argv[2]
    argv = sys.argv[3:]
    anchor = 4
    if "--anchor" in argv:
        anchor = int(argv[argv.index("--anchor") + 1])
    out = None
    if "--out" in argv:
        out = argv[argv.index("--out") + 1]
    res, rev = assemble(sub, E.lines_of(src), anchor)
    if out:
        with io.open(out, "w", encoding="utf-8", newline="\n") as f:
            f.write("\n".join(res) + "\n")
        print("wrote %s" % out)


if __name__ == "__main__":
    main()
