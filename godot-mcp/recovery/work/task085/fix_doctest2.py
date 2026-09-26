# -*- coding: utf-8 -*-
"""doctest's decomposition cannot handle `CHECK(a && <comparison>)` (C2338).
Wrap such expressions in one more pair of parentheses so the whole thing is a
single bool operand.  Only lines of the exact shape `CHECK(<expr>)` whose inner
expression contains both `&&` and a comparison operator are touched.
"""
import io

P = r"H:\rebuild\godot\modules\mcp_server\tests\test_mcp_server.h"

lines = io.open(P, encoding="utf-8").read().split("\n")
changed = []
for i, l in enumerate(lines):
    s = l.strip()
    if not (s.startswith("CHECK(") and s.endswith(");")):
        continue
    if s.startswith("CHECK((") and s.endswith("));"):
        continue
    if s.startswith("CHECK_FALSE("):
        continue
    inner = s[len("CHECK("):-2]
    if "&&" not in inner:
        continue
    if not any(op in inner for op in (" == ", " != ", " < ", " > ", " <= ", " >= ")):
        continue
    indent = l[:len(l) - len(l.lstrip())]
    lines[i] = "%sCHECK((%s));" % (indent, inner)
    changed.append((i + 1, s))

for no, s in changed:
    print("%5d  %s" % (no, s[:130]))
print("total %d" % len(changed))

if "--apply" in __import__("sys").argv:
    text = "\n".join(lines) + "\n"
    with io.open(P, "w", encoding="utf-8", newline="\n") as f:
        f.write(text)
    assert io.open(P, encoding="utf-8", errors="replace").read() == text
    print("wrote %s" % P)
