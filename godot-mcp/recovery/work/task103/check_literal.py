#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""TASK-103: the registration literal of `running_game_execute_gdscript` against
the regenerated contract, checked *before* the build (the same check TASK-097 ran
with `check_literal.py`), so a description that only exists in the contract can
never reach a compiled binary.

It reads the contract entry's `description` and `inputSchema`, then asserts:

  * the description appears in the generated span of
    `tools/running_game_script_execution.cpp` as the second argument of the
    `ToolBuilder` construction, character for character;
  * the schema's three members (`properties` / `required` / `type`) are emitted by
    the generator in the shape `gen_b2_game_schema.py` writes (the object-identity
    check gate 4 makes live after the build is the authoritative one; this one is
    the cheap pre-build smoke test).
"""

import io
import json
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.abspath(os.path.join(HERE, "..", "..", ".."))
MODULE = os.path.join(ROOT, "godot", "modules", "mcp_server")
CONTRACT = os.path.join(MODULE, "docs", "tools_list.renamed.json")
CPP = os.path.join(MODULE, "tools", "running_game_script_execution.cpp")
TOOL = "running_game_execute_gdscript"


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

    with io.open(CPP, encoding="utf-8") as handle:
        source = handle.read()
    begin = source.find("// BEGIN generated")
    end = source.rfind("// END generated")
    if begin < 0 or end < 0:
        sys.exit("FATAL: no generated span in %s" % CPP)
    span = source[begin:end]

    failures = []
    description = entry["description"]
    literal = 'String::utf8("%s")' % cpp_escape(description)
    if literal in span:
        print("description: byte-identical in the C++ literal (%d chars)" % len(description))
    else:
        failures.append("description: NOT byte-identical in the C++ literal")

    schema = entry["inputSchema"]
    for key in sorted(schema.keys()):
        marker = 'schema[String::utf8("%s")]' % key
        if marker in span:
            print("inputSchema[%s]: emitted" % key)
        else:
            failures.append("inputSchema[%s]: not emitted" % key)
    if schema.get("required") != ["code"]:
        failures.append("inputSchema.required is %r, expected ['code']" % (schema.get("required"),))
    if list(schema.get("properties", {}).keys()) != ["code"]:
        failures.append("inputSchema.properties keys are %r, expected ['code']"
                        % (list(schema.get("properties", {}).keys()),))

    # The registration metadata is read from the rename map by the generator; the
    # four literals it must have written for this tool.
    for marker in ('ToolBuilder builder("running_game_execute_gdscript"',
                   'builder.channel("running_game").verb("execute").scope(MCPToolScope::GAME).mutating(true)',
                   'handler(_tool_execute_gdscript)'):
        if marker in span:
            print("registration: %s" % marker)
        else:
            failures.append("registration: missing %s" % marker)

    if failures:
        for item in failures:
            print("FAIL: %s" % item)
        sys.exit(1)
    print("CHECK_LITERAL OK")


if __name__ == "__main__":
    main()
