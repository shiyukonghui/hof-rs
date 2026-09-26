#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""TASK-103: keep the doctest's hard-coded `running_game_execute_gdscript`
description in step with the regenerated contract.

The literal in `tests/test_mcp_server.h` (the `running_game_script_execution`
group case) is a byte-exact copy of the contract's description, so changing the
description means changing it in three places at once: the generator's override,
the regenerated `docs/tools_list.renamed.json`, and this literal. The first two are
produced by the generator; this script produces the third from the second, so the
literal cannot drift by a transcription error.

It rewrites exactly one line - the `CHECK(String(listed["description"]) == ...)`
line - and refuses to run when that line cannot be found exactly once.
"""

import io
import json
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.abspath(os.path.join(HERE, "..", "..", ".."))
MODULE = os.path.join(ROOT, "godot", "modules", "mcp_server")
CONTRACT = os.path.join(MODULE, "docs", "tools_list.renamed.json")
TESTS = os.path.join(MODULE, "tests", "test_mcp_server.h")
TOOL = "running_game_execute_gdscript"
MARKER = 'CHECK(String(listed["description"]) == String::utf8('


def cpp_escape(text):
    out = []
    for ch in text:
        if ch == "\\":
            out.append("\\\\")
        elif ch == '"':
            out.append('\\"')
        elif ch == "\n":
            out.append("\\n")
        elif ch == "\t":
            out.append("\\t")
        elif ch == "\r":
            out.append("\\r")
        else:
            out.append(ch)
    return "".join(out)


def main():
    with io.open(CONTRACT, encoding="utf-8") as handle:
        contract = json.load(handle)
    entry = None
    for tool in contract["result"]["tools"]:
        if tool["name"] == TOOL:
            entry = tool
            break
    if entry is None:
        sys.exit("FATAL: %s is not in the contract" % TOOL)

    with io.open(TESTS, encoding="utf-8", newline="") as handle:
        lines = handle.read().split("\n")

    hits = [i for i, line in enumerate(lines) if MARKER in line]
    if len(hits) != 1:
        sys.exit("FATAL: expected exactly one description literal for %s, found %d" % (TOOL, len(hits)))
    index = hits[0]
    old = lines[index]
    indent = old[:len(old) - len(old.lstrip("\t"))]
    new = '%sCHECK(String(listed["description"]) == String::utf8("%s"));' % (indent, cpp_escape(entry["description"]))
    if old == new:
        print("description literal already up to date (%d chars)" % len(entry["description"]))
        return
    lines[index] = new
    with io.open(TESTS, "w", encoding="utf-8", newline="") as handle:
        handle.write("\n".join(lines))
    print("rewrote line %d of %s (%d -> %d chars)"
          % (index + 1, os.path.basename(TESTS), len(old), len(new)))


if __name__ == "__main__":
    main()
