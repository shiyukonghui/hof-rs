#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""test_contract_forms.py -- the contract-layer INPUT-FORM matrix of all 177 tools.

WHY THIS EXISTS (TASK-143 section B1/B3, section C item 4)
----------------------------------------------------------
The 177 contract tools have a rich per-tool evidence chain (the contract itself,
`tools/tool_channels.json`, `coverage.json`, the engine's `[MCPServer]` suite and
the trace corpus), but until now **nothing checked the tools' declared INPUT
FORMS as a matrix**: every tool's required/optional split, its defaults, its
enums and the schema's internal consistency were only ever inspected inside the
large engine test cases, and 94 of the 177 tools are not named by any engine
`TEST_CASE` at all. A tool could therefore have declared a required member it did
not list in `properties`, or a `default` on a required member, and no test in the
repository would say so.

What is asserted here is deliberately OFFLINE and STATIC (no engine, no network,
no service), so it costs a fraction of a second and can run on every change:

  1. the three per-tool tables cover the SAME 177 names, in both directions
     (contract vs `tool_channels.json` vs `coverage.json`);
  2. every name passes the naming lint of the frozen contract
     (`^(editor|running_game|project|os)_[a-z0-9_]+$`);
  3. every `inputSchema` is a well-formed object schema: `required` is a subset
     of `properties`, and required members carry no `default` (that is a
     contradiction: an absent argument would then have both "must be supplied"
     and "assumed" as its meaning);
  4. every declared `enum` is a non-empty list, and any member carrying a
     declared `type` uses one of the JSON Schema primitive spellings;
  5. every tool declares exactly one of the four evidence channels.

Each of the five checks is paired with a NEGATIVE that mutates an in-memory copy
and requires the very same check to FAIL, so a check that quietly stopped
asserting anything (the TASK-059 D-2 tautology class) turns this file red instead
of green.

Run:
    D:\\Anaconda\\python.exe -m pytest tools\\tests\\test_contract_forms.py -q
    D:\\Anaconda\\python.exe tools\\tests\\test_contract_forms.py
"""
from __future__ import print_function

import io
import json
import os
import re
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(os.path.dirname(HERE))
CONTRACT = os.path.join(ROOT, "godot", "modules", "mcp_server", "docs",
                        "tools_list.renamed.json")
CHANNELS = os.path.join(ROOT, "tools", "tool_channels.json")
COVERAGE = os.path.join(ROOT, "coverage.json")

NAME_LINT = re.compile(r"^(editor|running_game|project|os)_[a-z0-9_]+$")
BANNED_SUBSTRING = "update_"
CHANNEL_ENUM = ("file_effect", "pixel_effect", "editor_state", "payload")
PRIMITIVES = ("string", "integer", "number", "boolean", "array", "object")

# ---------------------------------------------------------------------------
# PINNED DIVERGENCE (TASK-143 section C item 4, registered in
# recovery/TEST-CASES.md as TC-TOOL-* finding F1):
#
# JSON Schema makes `required` optional, and 3 of the 177 contract entries omit
# it entirely while every other entry carries at least an empty list:
#
#   editor_get_selection          all-optional arguments
#   editor_set_node_selection     one-of(node_path, node_paths) - not expressible
#                                 in this schema dialect, yet the server refuses
#                                 an empty bag with -32602 "node_paths or node_path"
#   editor_remove_node_selection  no arguments at all
#
# The live `tools/list` publishes exactly these three schemas (accept_m1 case 3
# compares it verbatim, 154/154 editor), so this is a contract-SHAPE divergence,
# not a server/client disagreement, and the frozen contract must not be edited to
# make a test look tidier. Instead the set is PINNED here: it may not grow, and a
# tool leaving it is also a change this test reports.
# ---------------------------------------------------------------------------
NO_REQUIRED_LIST_PINNED = frozenset((
    "editor_get_selection",
    "editor_set_node_selection",
    "editor_remove_node_selection",
))


def _load(path):
    with io.open(path, "r", encoding="utf-8") as handle:
        return json.load(handle)


def load_contract(path=CONTRACT):
    return _load(path)["result"]["tools"]


def load_channel_names(path=CHANNELS):
    return list((_load(path).get("channels") or {}).keys())


def load_coverage_names(path=COVERAGE):
    return [row["tool"] for row in _load(path)["tools"]]


# ---------------------------------------------------------------------------
# the five checks. Each returns a list of complaint strings; [] means clean.
# ---------------------------------------------------------------------------
def check_coverage(tools, channel_names, coverage_names):
    """1. the three tables cover the same names, in both directions."""
    bad = []
    names = [t["name"] for t in tools]
    for label, other in (("tool_channels.json", channel_names),
                         ("coverage.json", coverage_names)):
        missing = sorted(set(names) - set(other))
        extra = sorted(set(other) - set(names))
        if missing:
            bad.append("%s is missing %d contract tool(s): %s" % (label, len(missing), ", ".join(missing[:5])))
        if extra:
            bad.append("%s carries %d tool(s) outside the contract: %s" % (label, len(extra), ", ".join(extra[:5])))
    return bad


def check_names(tools):
    """2. the naming lint of the frozen contract (shape + the banned verb)."""
    bad = []
    for t in tools:
        if not NAME_LINT.match(t["name"]):
            bad.append("%s does not match %s" % (t["name"], NAME_LINT.pattern))
        if BANNED_SUBSTRING in t["name"]:
            bad.append("%s contains the banned verb '%s' (GDR-16 L4)" % (t["name"], BANNED_SUBSTRING))
    return bad


def check_schema_shape(tools):
    """3. required subset of properties, no default on a required member.

    An absent `required` is legal JSON Schema but is pinned to the 3 declared
    divergences (NO_REQUIRED_LIST_PINNED) so it can neither grow nor be quietly
    normalised away.
    """
    bad = []
    without = set()
    for t in tools:
        schema = t.get("inputSchema") or {}
        props = schema.get("properties") or {}
        required = schema.get("required")
        if required is None:
            without.add(t["name"])
            continue
        if not isinstance(required, list):
            bad.append("%s declares `required` as %s, not a list" % (t["name"], type(required).__name__))
            continue
        if schema.get("type") != "object":
            bad.append("%s declares inputSchema.type=%r, not 'object'" % (t["name"], schema.get("type")))
        outside = [k for k in required if k not in props]
        if outside:
            bad.append("%s requires %s but does not declare them in properties" % (t["name"], ", ".join(outside)))
        for key in required:
            spec = props.get(key)
            if isinstance(spec, dict) and "default" in spec:
                bad.append("%s requires '%s' AND gives it a default %r - a required member with a default is a contradiction"
                           % (t["name"], key, spec["default"]))
        for key, spec in props.items():
            if not isinstance(spec, dict):
                bad.append("%s/%s is not a schema object" % (t["name"], key))
    if without != set(NO_REQUIRED_LIST_PINNED):
        appeared = sorted(without - NO_REQUIRED_LIST_PINNED)
        vanished = sorted(NO_REQUIRED_LIST_PINNED - without)
        if appeared:
            bad.append("%d tool(s) newly omit `required`: %s (pinned set: %s)"
                       % (len(appeared), ", ".join(appeared), ", ".join(sorted(NO_REQUIRED_LIST_PINNED))))
        if vanished:
            bad.append("%s no longer omits `required`; the pinned divergence list must be updated deliberately"
                       % ", ".join(vanished))
    return bad


def check_enums_and_types(tools):
    """4. enums are non-empty lists; declared types are primitive spellings."""
    bad = []
    for t in tools:
        props = (t.get("inputSchema") or {}).get("properties") or {}
        for key, spec in props.items():
            if not isinstance(spec, dict):
                continue
            enum = spec.get("enum")
            if enum is not None:
                if not isinstance(enum, list) or not enum:
                    bad.append("%s/%s declares enum=%r, which is not a non-empty list" % (t["name"], key, enum))
            declared = spec.get("type")
            if declared is not None and declared not in PRIMITIVES:
                bad.append("%s/%s declares type=%r, outside %s" % (t["name"], key, declared, list(PRIMITIVES)))
    return bad


def check_channels(coverage_rows):
    """5. exactly one of the four evidence channels per tool."""
    bad = []
    for row in coverage_rows:
        ch = row.get("evidence_channel")
        if ch not in CHANNEL_ENUM:
            bad.append("%s declares evidence_channel=%r, outside %s" % (row.get("tool"), ch, list(CHANNEL_ENUM)))
    return bad


# ---------------------------------------------------------------------------
# the real data, loaded once
# ---------------------------------------------------------------------------
TOOLS = load_contract()
CHANNEL_NAMES = load_channel_names()
COVERAGE = _load(COVERAGE)
COVERAGE_ROWS = COVERAGE["tools"]
COVERAGE_NAMES = [r["tool"] for r in COVERAGE_ROWS]


def test_the_contract_carries_177_tools():
    assert len(TOOLS) == 177, "the frozen contract carries %d tools, not 177" % len(TOOLS)


def test_the_three_tables_cover_the_same_names():
    assert check_coverage(TOOLS, CHANNEL_NAMES, COVERAGE_NAMES) == []


def test_every_tool_name_passes_the_naming_lint():
    assert check_names(TOOLS) == []


def test_every_input_schema_is_internally_consistent():
    assert check_schema_shape(TOOLS) == []


def test_the_tools_without_a_required_list_are_exactly_the_pinned_ones():
    """Finding F1: 3 entries omit `required`; the set is pinned, not tolerated blindly."""
    without = set(t["name"] for t in TOOLS if "required" not in (t.get("inputSchema") or {}))
    assert without == set(NO_REQUIRED_LIST_PINNED), \
        "the `required`-omitting set moved: %s vs pinned %s" % (sorted(without), sorted(NO_REQUIRED_LIST_PINNED))


def test_every_declared_enum_and_type_is_well_formed():
    assert check_enums_and_types(TOOLS) == []


def test_every_tool_declares_one_known_evidence_channel():
    assert check_channels(COVERAGE_ROWS) == []


# ---------------------------------------------------------------------------
# the negatives: the same checkers must REJECT a mutated copy
# ---------------------------------------------------------------------------
def _mutated(mutate):
    tools = json.loads(json.dumps(TOOLS))
    mutate(tools)
    return tools


def test_negative_naming_lint_rejects_a_banned_verb():
    """A tool renamed to the banned `update_` form must be rejected."""
    def mutate(tools):
        tools[0]["name"] = "editor_update_node_property"
    complaints = check_names(_mutated(mutate))
    assert complaints, "the naming lint accepted a banned `update_` name"
    assert "editor_update_node_property" in complaints[0]
    # and the honest name is still accepted, i.e. the check is not simply always red
    assert check_names(TOOLS) == []


def test_negative_schema_check_rejects_a_required_member_outside_properties():
    """`required` naming a member that `properties` does not declare must be caught."""
    def mutate(tools):
        tools[0].setdefault("inputSchema", {}).setdefault("required", []).append("__not_declared__")
    complaints = check_schema_shape(_mutated(mutate))
    assert any("__not_declared__" in c for c in complaints), \
        "the schema check accepted a required member absent from properties"


def test_negative_schema_check_rejects_a_required_member_with_a_default():
    """A required member carrying a `default` must be caught."""
    target = None
    for i, t in enumerate(TOOLS):
        if t["inputSchema"].get("required"):
            target = (i, t["inputSchema"]["required"][0])
            break
    assert target is not None, "no contract tool has a required member to mutate"
    idx, key = target

    def mutate(tools):
        tools[idx]["inputSchema"]["properties"][key]["default"] = "impossible"
    complaints = check_schema_shape(_mutated(mutate))
    assert any("contradiction" in c and key in c for c in complaints), \
        "the schema check accepted a required member with a default"


def test_negative_schema_check_rejects_a_new_required_omission():
    """A tool newly omitting `required` must break the pinned divergence list."""
    def mutate(tools):
        for t in tools:
            if t["name"] not in NO_REQUIRED_LIST_PINNED:
                t["inputSchema"].pop("required", None)
                return
    complaints = check_schema_shape(_mutated(mutate))
    assert any("newly omit `required`" in c for c in complaints), \
        "the schema check accepted a tool newly omitting `required`"


def test_negative_enum_check_rejects_an_empty_enum():
    """An empty enum must be caught (it makes every input illegal)."""
    target = None
    for i, t in enumerate(TOOLS):
        for k, spec in (t["inputSchema"].get("properties") or {}).items():
            if isinstance(spec, dict) and spec.get("enum"):
                target = (i, k)
                break
        if target:
            break
    assert target is not None, "no contract tool declares an enum to mutate"
    idx, key = target

    def mutate(tools):
        tools[idx]["inputSchema"]["properties"][key]["enum"] = []
    complaints = check_enums_and_types(_mutated(mutate))
    assert any("enum" in c for c in complaints), "the enum check accepted an empty enum"


def test_negative_channel_check_rejects_an_unknown_channel():
    """An unknown evidence channel must be caught."""
    rows = json.loads(json.dumps(COVERAGE_ROWS))
    rows[0]["evidence_channel"] = "vibes"

    complaints = check_channels(rows)
    assert complaints and rows[0]["tool"] in complaints[0], \
        "the channel check accepted an unknown evidence channel"


def test_negative_table_check_rejects_a_dropped_tool():
    """A tool missing from the channel table must be caught."""
    complaints = check_coverage(TOOLS, CHANNEL_NAMES[:-1], COVERAGE_NAMES)
    assert complaints, "the table check accepted a channel table missing a contract tool"
    assert "missing" in complaints[0]


def main():
    cases = []
    cases.append(("the contract carries 177 tools", len(TOOLS) == 177, len(TOOLS)))
    cases.append(("the three tables cover the same names",
                  check_coverage(TOOLS, CHANNEL_NAMES, COVERAGE_NAMES) == [],
                  check_coverage(TOOLS, CHANNEL_NAMES, COVERAGE_NAMES)[:2]))
    cases.append(("every tool name passes the naming lint",
                  check_names(TOOLS) == [], check_names(TOOLS)[:2]))
    shape = check_schema_shape(TOOLS)
    cases.append(("every input schema is internally consistent", shape == [], shape[:2]))
    without = set(t["name"] for t in TOOLS if "required" not in (t.get("inputSchema") or {}))
    cases.append(("the `required`-omitting set is exactly the pinned 3 (finding F1)",
                  without == set(NO_REQUIRED_LIST_PINNED),
                  {"without": sorted(without), "pinned": sorted(NO_REQUIRED_LIST_PINNED)}))
    enums = check_enums_and_types(TOOLS)
    cases.append(("every declared enum and type is well formed", enums == [], enums[:2]))
    chans = check_channels(COVERAGE_ROWS)
    cases.append(("every tool declares one known evidence channel", chans == [], chans[:2]))

    # the negatives, run for real
    def mut(m):
        t = json.loads(json.dumps(TOOLS))
        m(t)
        return t

    neg_name = check_names(mut(lambda t: t[0].__setitem__("name", "editor_update_node_property")))
    cases.append(("NEGATIVE: a banned `update_` name is rejected", bool(neg_name), neg_name[:1]))

    neg_outside = check_schema_shape(mut(lambda t: t[0].setdefault("inputSchema", {}).setdefault("required", []).append("__x__")))
    cases.append(("NEGATIVE: a required member outside properties is rejected",
                  any("__x__" in c for c in neg_outside), neg_outside[:1]))

    def drop_required(t):
        for e in t:
            if e["name"] not in NO_REQUIRED_LIST_PINNED:
                e["inputSchema"].pop("required", None)
                return
    neg_omit = check_schema_shape(mut(drop_required))
    cases.append(("NEGATIVE: a newly `required`-omitting tool is rejected",
                  any("newly omit" in c for c in neg_omit), neg_omit[:1]))

    neg_enum_rows = check_enums_and_types(mut(lambda t: t[0].setdefault("inputSchema", {}).setdefault("properties", {}).__setitem__("__e__", {"enum": []})))
    cases.append(("NEGATIVE: an empty enum is rejected", bool(neg_enum_rows), neg_enum_rows[:1]))

    neg_ch = check_channels([dict(COVERAGE_ROWS[0], evidence_channel="vibes")])
    cases.append(("NEGATIVE: an unknown evidence channel is rejected", bool(neg_ch), neg_ch[:1]))

    failed = [c for c in cases if not c[1]]
    for ok, name, detail in cases:
        print("%s  %s" % ("ok  " if ok else "FAIL", name))
        if not ok:
            print("      detail: %s" % (detail,))
    print("\n%d/%d checks passed" % (len(cases) - len(failed), len(cases)))
    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(main())
