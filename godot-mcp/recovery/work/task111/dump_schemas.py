#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""dump_schemas.py -- compact signature dump for TASK-111 target tools.

Reads the per-tool schema JSON dumped by TASK-110 (recovery/work/task110/schemas/)
and the renamed contract (docs/tools_list.renamed.json) and prints, per requested
tool, the property name / type / required / enum / default, so a coverage session
can be written against the real contract instead of guesswork.

Usage: python recovery/work/task111/dump_schemas.py tool_a tool_b ...
"""
import io
import json
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.abspath(os.path.join(HERE, "..", "..", ".."))
SCHEMAS = os.path.join(ROOT, "recovery", "work", "task110", "schemas")
CONTRACT = os.path.join(ROOT, "godot", "modules", "mcp_server", "docs",
                        "tools_list.renamed.json")


def load_contract():
    with io.open(CONTRACT, "r", encoding="utf-8") as h:
        doc = json.load(h)
    out = {}
    for t in doc["result"]["tools"]:
        out[t["name"]] = t
    return out


def fmt_type(prop):
    if not isinstance(prop, dict):
        return "?"
    t = prop.get("type", "?")
    if t == "array":
        items = prop.get("items") or {}
        it = items.get("type", "?")
        if it == "object":
            it = "object{%s}" % ",".join(sorted((items.get("properties") or {}).keys()))
        t = "array<%s>" % it
    if t == "object":
        t = "object{%s}" % ",".join(sorted((prop.get("properties") or {}).keys()))
    extra = []
    if "enum" in prop:
        extra.append("enum=" + "|".join(str(x) for x in prop["enum"]))
    if "default" in prop:
        extra.append("default=%s" % json.dumps(prop["default"], ensure_ascii=False))
    if "minimum" in prop or "maximum" in prop:
        extra.append("range=%s..%s" % (prop.get("minimum"), prop.get("maximum")))
    return " ".join([t] + extra)


def main(argv):
    contract = load_contract()
    for name in argv:
        print("=" * 78)
        print(name)
        entry = contract.get(name)
        if entry:
            print("  contract: %s" % (entry.get("description", "")[:400].replace("\n", " ")))
        local = os.path.join(SCHEMAS, name + ".json")
        schema = None
        if os.path.isfile(local):
            with io.open(local, "r", encoding="utf-8") as h:
                schema = json.load(h)
        if schema is not None and "inputSchema" in schema:
            schema = schema["inputSchema"]
        if schema is None and entry:
            schema = entry.get("inputSchema")
        if schema is None:
            print("  (no schema found)")
            continue
        req = set(schema.get("required") or [])
        props = schema.get("properties") or {}
        if not props:
            print("  (no properties)")
        for key in sorted(props):
            mark = "*" if key in req else " "
            print("  %s %-28s %s" % (mark, key, fmt_type(props[key])))
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
