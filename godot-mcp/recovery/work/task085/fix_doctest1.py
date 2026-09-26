# -*- coding: utf-8 -*-
"""doctest cannot decompose `CHECK(a && (String)x->get(k) == v)` (C2338
"Expression Too Complex").  Parenthesising the whole expression makes it one
bool operand; the assertion's meaning is unchanged.

Recorded context: the line is test_mcp_server.h:3622.
"""
import io

P = r"H:\rebuild\godot\modules\mcp_server\tests\test_mcp_server.h"
OLD = '\tCHECK(written.is_valid() && (String)written->get("resource_name") == "mcp_created");'
NEW = '\tCHECK((written.is_valid() && (String)written->get("resource_name") == "mcp_created"));'

lines = io.open(P, encoding="utf-8").read().split("\n")
hit = [i for i, l in enumerate(lines) if l == OLD]
assert len(hit) == 1, "hits: %d" % len(hit)
lines[hit[0]] = NEW
text = "\n".join(lines) + "\n"
with io.open(P, "w", encoding="utf-8", newline="\n") as f:
    f.write(text)
assert io.open(P, encoding="utf-8", errors="replace").read() == text
print("parenthesised test_mcp_server.h:%d" % (hit[0] + 1))
