# -*- coding: utf-8 -*-
"""Verify the merged DESIGN-DETAIL.md candidate against the surviving tree copy."""
from __future__ import print_function
import io, re, sys, hashlib
sys.path.insert(0, r"C:\Users\wyl\AppData\Local\Temp\mcp-recovery\work\task087")
import rep

MERGED = r"C:\Users\wyl\AppData\Local\Temp\mcp-recovery\work\task087\dd_merged.md"
TREE = r"H:\rebuild\godot\modules\mcp_server\docs\DESIGN-DETAIL.md"


def load(p):
    return io.open(p, encoding="utf-8").read()


def main():
    a = load(MERGED)
    b = load(TREE)
    A = a.split("\n")
    B = b.split("\n")
    rep.log("merged bytes=%d lines=%d sha256=%s"
            % (len(a.encode("utf-8")), len(A), hashlib.sha256(a.encode("utf-8")).hexdigest()))
    rep.log("tree   bytes=%d lines=%d sha256=%s"
            % (len(b.encode("utf-8")), len(B), hashlib.sha256(b.encode("utf-8")).hexdigest()))

    # common prefix / suffix
    i = 0
    while i < min(len(A), len(B)) and A[i] == B[i]:
        i += 1
    j = 0
    while j < min(len(A) - i, len(B) - i) and A[len(A) - 1 - j] == B[len(B) - 1 - j]:
        j += 1
    rep.log("common prefix=%d lines, common suffix=%d lines" % (i, j))
    rep.log("tree-unique tail starts at line %d" % (len(B) - j + 1))
    rep.log("")
    rep.log("--- merged lines the tree lost (first 40 of %d) ---" % (len(A) - i - j))
    for k in range(i, min(len(A) - j, i + 40)):
        rep.log("  M%-5d %s" % (k + 1, A[k][:160]))
    rep.log("")
    rep.log("--- merged headings ---")
    for n, l in enumerate(A, 1):
        if re.match(r"^#{1,4} ", l):
            rep.log("  %5d  %s" % (n, l[:120]))
    rep.log("")
    rep.log("--- tree headings ---")
    for n, l in enumerate(B, 1):
        if re.match(r"^#{1,4} ", l):
            rep.log("  %5d  %s" % (n, l[:120]))
    rep.flush()


if __name__ == "__main__":
    main()
