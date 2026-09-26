# -*- coding: utf-8 -*-
"""TASK-083: full-module structural scan - unmatched ( ) { } per source file."""
import io
import os
import sys

sys.path.insert(0, r"C:\Users\wyl\AppData\Local\Temp\mcp-recovery\work\task083")
import splice  # noqa: E402

TREE = r"H:\rebuild\godot\modules\mcp_server"
OUT = r"C:\Users\wyl\AppData\Local\Temp\mcp-recovery\work\task083"


def scan(lines):
    stack = []
    state = None
    delim = None
    unmatched_close = []
    for ln, src in enumerate(lines, 1):
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
                        unmatched_close.append((c, ln))
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
    return stack, unmatched_close, state


def main():
    rows = []
    for root, dirs, files in os.walk(TREE):
        for fn in files:
            if not fn.endswith((".cpp", ".h")):
                continue
            p = os.path.join(root, fn)
            rel = os.path.relpath(p, TREE)
            if rel.startswith("docs") or rel.startswith("tests"):
                continue
            try:
                L = splice.read_plain(p)
            except Exception as e:
                rows.append((rel, "READ-ERROR %s" % e, 0, 0, []))
                continue
            stack, uc, st = scan(L)
            if stack or uc or st:
                rows.append((rel, "OPEN=%d CLOSE=%d state=%s" % (len(stack), len(uc), st),
                             len(stack), len(uc), (stack[:3], uc[:3])))
    rows.sort(key=lambda r: -(r[2] + r[3]))
    with io.open(os.path.join(OUT, "structural-scan.txt"), "w", encoding="utf-8", newline="\n") as f:
        for rel, msg, a, b, det in rows:
            f.write("%-60s %s\n" % (rel, msg))
            if det:
                for c, ln in det[0]:
                    f.write("      unclosed %r at line %d\n" % (c, ln))
                for c, ln in det[1]:
                    f.write("      stray    %r at line %d\n" % (c, ln))
    print("files with structural problems: %d" % len(rows))
    for rel, msg, a, b, det in rows:
        print("  %-58s %s" % (rel, msg))


if __name__ == "__main__":
    main()
