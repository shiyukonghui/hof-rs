#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""TASK-143 negative demonstration for tools/tests/test_contract_forms.py.

Runs each of the new file's checkers against a MUTATED in-memory contract /
channel table and prints the verdict it produces. This is the "the negative was
really run" evidence: a checker that had silently stopped asserting anything
would print an empty complaint list here.
"""
import io
import json
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
TOOLS = r"F:\moonbit-hof-rs\godot-mcp\tools\tests"
sys.path.insert(0, TOOLS)

import test_contract_forms as t  # noqa: E402


def mut(fn):
    tools = json.loads(json.dumps(t.TOOLS))
    fn(tools)
    return tools


def main():
    out = {}

    tools = mut(lambda x: x[0].__setitem__("name", "editor_update_node_property"))
    out["N1_banned_update_name"] = {"check": "check_names", "complaints": t.check_names(tools)}

    tools = mut(lambda x: x[0].setdefault("inputSchema", {}).setdefault("required", []).append("__not_declared__"))
    out["N2_required_outside_properties"] = {"check": "check_schema_shape",
                                             "complaints": t.check_schema_shape(tools)}

    target = None
    for i, e in enumerate(t.TOOLS):
        if e["inputSchema"].get("required"):
            target = (i, e["inputSchema"]["required"][0])
            break
    idx, key = target
    tools = mut(lambda x: x[idx]["inputSchema"]["properties"][key].__setitem__("default", "impossible"))
    out["N3_required_with_default"] = {"mutated_tool": t.TOOLS[idx]["name"], "mutated_member": key,
                                       "check": "check_schema_shape",
                                       "complaints": t.check_schema_shape(tools)}

    def drop_required(x):
        for e in x:
            if e["name"] not in t.NO_REQUIRED_LIST_PINNED:
                e["inputSchema"].pop("required", None)
                return
    tools = mut(drop_required)
    out["N4_new_required_omission"] = {"check": "check_schema_shape",
                                       "complaints": t.check_schema_shape(tools)}

    tools = mut(lambda x: x[0]["inputSchema"].setdefault("properties", {}).__setitem__(
        "__empty_enum__", {"type": "string", "enum": []}))
    out["N5_empty_enum"] = {"check": "check_enums_and_types",
                            "complaints": t.check_enums_and_types(tools)}

    rows = json.loads(json.dumps(t.COVERAGE_ROWS))
    rows[0]["evidence_channel"] = "vibes"
    out["N6_unknown_channel"] = {"check": "check_channels", "tool": rows[0]["tool"],
                                 "complaints": t.check_channels(rows)}

    out["N7_channel_table_missing_a_tool"] = {
        "check": "check_coverage",
        "complaints": t.check_coverage(t.TOOLS, t.CHANNEL_NAMES[:-1], t.COVERAGE_NAMES)}

    # the checks are not simply always-red: the real artifacts are clean
    out["POSITIVE_control"] = {
        "check_coverage": t.check_coverage(t.TOOLS, t.CHANNEL_NAMES, t.COVERAGE_NAMES),
        "check_names": t.check_names(t.TOOLS),
        "check_schema_shape": t.check_schema_shape(t.TOOLS),
        "check_enums_and_types": t.check_enums_and_types(t.TOOLS),
        "check_channels": t.check_channels(t.COVERAGE_ROWS),
    }

    for name in sorted(out):
        entry = out[name]
        print("[%s] %s" % (name, entry.get("check")))
        if entry.get("mutated_tool"):
            print("    mutated: %s/%s" % (entry["mutated_tool"], entry["mutated_member"]))
        n = len(entry.get("complaints") or [])
        print("    complaints=%d" % n)
        for c in (entry.get("complaints") or [])[:3]:
            print("      - %s" % c)

    path = os.path.join(HERE, "negative-demo.json")
    with io.open(path, "w", encoding="utf-8", newline="\n") as h:
        h.write(json.dumps(out, ensure_ascii=False, indent=1))
    print("\nwrote %s" % path)
    # exit 0 only when every negative really produced a complaint and the control is clean
    ok = all(len(v.get("complaints") or []) > 0 for k, v in out.items() if k.startswith("N"))
    clean = all(not v for k, v in out["POSITIVE_control"].items())
    print("negatives all fired: %s ; control clean: %s" % (ok, clean))
    return 0 if (ok and clean) else 1


if __name__ == "__main__":
    sys.exit(main())
