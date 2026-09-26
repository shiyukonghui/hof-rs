# -*- coding: utf-8 -*-
"""TASK-083: find unmatched ( and { with their line numbers."""
import os
import sys

sys.path.insert(0, r"C:\Users\wyl\AppData\Local\Temp\mcp-recovery\work\task083")
import splice  # noqa: E402


def main():
    rel = sys.argv[1]
    p = os.path.join(splice.TREE, rel.replace("/", os.sep))
    L = splice.read_plain(p)
    stack = []
    state = None
    delim = None
    for ln, src in enumerate(L, 1):
        i = 0
        n = len(src)
        while i < n:
            c = src[i]
            nx = src[i + 1] if i + 1 < n else ""
            if state is None:
                if c == "/" and nx == "/":
                    break
                if c == "/" and nx == "*":
                    state = "block"
                    i += 2
                    continue
                if c == "R" and nx == '"':
                    j = src.find("(", i + 2)
                    if j != -1:
                        delim = src[i + 2:j]
                        state = "raw"
                        i = j + 1
                        continue
                if c == '"':
                    state = "str"
                    i += 1
                    continue
                if c == "'":
                    state = "chr"
                    i += 1
                    continue
                if c in "({":
                    stack.append((c, ln))
                elif c in ")}":
                    want = "(" if c == ")" else "{"
                    if stack and stack[-1][0] == want:
                        stack.pop()
                    else:
                        print("UNMATCHED close %r at line %d: %s" % (c, ln, src[:120]))
                i += 1
                continue
            if state == "block":
                if c == "*" and nx == "/":
                    state = None
                    i += 2
                    continue
                i += 1
                continue
            if state == "raw":
                if c == ")" and src[i + 1:i + 1 + len(delim)] == delim and src[i + 1 + len(delim):i + 2 + len(delim)] == '"':
                    state = None
                    i += 2 + len(delim)
                    continue
                i += 1
                continue
            if state in ("str", "chr"):
                if c == "\\":
                    i += 2
                    continue
                if (state == "str" and c == '"') or (state == "chr" and c == "'"):
                    state = None
                i += 1
                continue
    print("unmatched openers at EOF (%d):" % len(stack))
    for c, ln in stack[:40]:
        print("  %r opened at line %d : %s" % (c, ln, L[ln - 1][:120]))


if __name__ == "__main__":
    main()
