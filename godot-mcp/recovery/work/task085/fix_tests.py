# -*- coding: utf-8 -*-
"""TASK-085: two structural repairs in tests/test_mcp_server.h.

1. Ten TEST_CASEs between lines 3585 and 4111 use `ScratchProject` unqualified
   while the other sixteen sites write `TestMCPServer::ScratchProject`.  The
   recorded rev3846 window shows BOTH spellings in the reference (bare at 3705 /
   3748, qualified at 3409), i.e. the bare ones are inside a
   `namespace TestMCPServer { ... }` block whose opener/closer the tree lost.
   Qualifying the ten sites is the behaviour-identical repair and does not
   require guessing where that block started.

2. The preprocessor balance is off by one: the `#endif` at 8384 has no opener,
   so `-` every `#if` after it `-` the rest of the file is skipped.  The block it
   closes is the TEST_CASE that precedes it, whose `#ifdef
   MCP_EDITOR_TOOLS_ENABLED` line went missing.  The guard is restored right
   after that TEST_CASE's opening brace, matching the file's own pattern
   (`#ifdef MCP_EDITOR_TOOLS_ENABLED` immediately inside the case body).

usage: python fix_tests.py [--apply]
"""
import io
import sys

sys.path.insert(0, ".")
import evfetch as E  # noqa: E402

TREE = r"H:\rebuild\godot\modules\mcp_server\tests\test_mcp_server.h"


def main():
    lines = E.lines_of(TREE)
    print("test_mcp_server.h: %d lines" % len(lines))

    # 1. qualify the bare uses
    n = 0
    for i, l in enumerate(lines):
        if l.startswith("\tScratchProject ") or l.startswith("ScratchProject "):
            lines[i] = l.replace("ScratchProject ", "TestMCPServer::ScratchProject ", 1)
            n += 1
    print("1: qualified %d bare `ScratchProject` uses" % n)
    assert n == 10, "expected 10 bare uses, found %d" % n

    # 2. restore the missing #ifdef in front of the orphan #endif at 8384
    orphan = [i for i, l in enumerate(lines) if l.rstrip() == "#endif"]
    depth = 0
    orphan_idx = None
    for i, l in enumerate(lines):
        s = l.strip()
        if s.startswith("#if"):
            depth += 1
        elif s.startswith("#endif"):
            depth -= 1
            if depth < 0:
                orphan_idx = i
                break
    assert orphan_idx is not None and orphan_idx + 1 == 8384, "orphan #endif at %s" % (orphan_idx + 1)
    tc = None
    for j in range(orphan_idx, -1, -1):
        if lines[j].startswith("TEST_CASE("):
            tc = j
            break
    assert tc is not None, "TEST_CASE before the orphan #endif not found"
    print("2: orphan `#endif` at 8384 closes the TEST_CASE opened at line %d" % (tc + 1))
    insert_at = tc + 1
    guard = "#ifdef MCP_EDITOR_TOOLS_ENABLED"
    lines = lines[:insert_at] + [guard] + lines[insert_at:]

    # re-check the preprocessor balance
    depth = 0
    for l in lines:
        s = l.strip()
        if s.startswith("#if"):
            depth += 1
        elif s.startswith("#endif"):
            depth -= 1
    print("preprocessor depth after the repair: %d" % depth)
    assert depth == 0

    if "--apply" not in sys.argv:
        print("(dry run; pass --apply to write)")
        return
    text = "\n".join(lines) + "\n"
    with io.open(TREE, "w", encoding="utf-8", newline="\n") as f:
        f.write(text)
    assert io.open(TREE, encoding="utf-8", errors="replace").read() == text
    print("wrote %s (%d lines), read-back OK" % (TREE, len(lines)))


if __name__ == "__main__":
    main()
