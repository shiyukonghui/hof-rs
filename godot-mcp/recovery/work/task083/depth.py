# -*- coding: utf-8 -*-
"""TASK-083: report paren/brace depth after every top-level construct, then the
first line where the depth fails to return to the expected level."""
import os
import sys

sys.path.insert(0, r"C:\Users\wyl\AppData\Local\Temp\mcp-recovery\work\task083")
import splice  # noqa: E402


def depths(lines):
    dc = dp = 0
    state = None
    delim = None
    out = []
    for src in lines:
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
                if c == "{":
                    dc += 1
                elif c == "}":
                    dc -= 1
                elif c == "(":
                    dp += 1
                elif c == ")":
                    dp -= 1
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
        out.append((dc, dp, state))
    return out


def main():
    rel = sys.argv[1]
    p = os.path.join(splice.TREE, rel.replace("/", os.sep))
    L = splice.read_plain(p)
    d = depths(L)
    bad = []
    for i, (dc, dp, st) in enumerate(d, 1):
        if (dc == 0 and dp != 0) or (dp == 0 and dc != 0) or (dp < 0) or (dc < 0):
            bad.append((i, dc, dp, st, L[i - 1][:100]))
    print("lines=%d  final=%s" % (len(L), d[-1]))
    print("odd-depth lines (first 30):")
    for i, dc, dp, st, t in bad[:30]:
        print("  %5d brace=%-3d paren=%-3d state=%-6s | %s" % (i, dc, dp, st, t))


if __name__ == "__main__":
    main()
