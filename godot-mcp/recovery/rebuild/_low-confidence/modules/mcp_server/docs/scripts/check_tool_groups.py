# -*- coding: utf-8 -*-
"""Verify docs/tool-groups.json against the frozen B1 list and the contract.

TASK-002 section 2.3.1 makes `docs/tool-groups.json` the *only* input of the
follow-up parallel porting batches, so it has to be exact. This checker is the
executable form of that requirement:

  1. the B1 old-name list is re-derived from `docs/DESIGN-DETAIL.md` section 10
     (the two B1 paragraphs) and from `docs/tool-rename-map.json`;
  2. `get_editor_performance` is dropped (GDR-17 lossless merge, already
     registered elsewhere), leaving exactly 41 tools;
  3. every one of the 41 appears in the manifest **exactly once** (no missing,
     no duplicate, no foreign name);
  4. every group is one `channel` + one `mutating` value and its declared value
     matches the rename map for every member;
  5. group sizes respect the <=10 cap of section 2.3.1;
  6. no tool name is accidentally taken from the 130 non-B1 contract entries.

TASK-010 adds the sister manifest `docs/tool-groups-b2.json` and extends this
checker with `--batch B2`. The B1 path is deliberately untouched: with no
argument the output and the assertions are byte for byte the ones TASK-002
froze, so the B1 gate cannot be weakened by the B2 addition. The B2 path applies
the same invariants to the 25 tools of DESIGN-DETAIL.md section 10's B2
paragraph, plus the `scope` check the B2 manifest declares per group (scope is
part of the B2 partition axis, so it is asserted against the rename map too).

TASK-015 adds `--batch B3|B4|B5` (one manifest each, the same invariants), and
TASK-037 D1 makes `--batch B1` an **alias of the no-argument path**: the usage
string had always advertised `B1`, but the dispatch answered `unknown batch: B1`
and exited 1, so the documented spelling contradicted the code (REPORT-AUDIT-B5
D1). `--batch B1` now runs the same frozen `main()` - same assertions, same exit
code - so the usage text is true and no invariant is weakened.

Usage:  python modules/mcp_server/docs/scripts/check_tool_groups.py [--batch B1|B2|B3|B4|B5]
                                                                   [--added] [--generator-version]
                                                                   [--check-completeness]
Standard library only (Python 3.9).

TASK-057 adds `--generator-version` (R-B2): the same assertion `--added` runs,
on its own, so the three generator versions can be demonstrated to be one
string and the drift can be reproduced on purpose.
"""

import collections
import io
import json
import os
import re
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
DOCS = os.path.dirname(HERE)

DETAIL_MD = os.path.join(DOCS, "DESIGN-DETAIL.md")
MAP_JSON = os.path.join(DOCS, "tool-rename-map.json")
CONTRACT_JSON = os.path.join(DOCS, "tools_list.renamed.json")
GROUPS_JSON = os.path.join(DOCS, "tool-groups.json")
GROUPS_B2_JSON = os.path.join(DOCS, "tool-groups-b2.json")

EXPECTED_B1_OLD = 42
EXPECTED_PORTED = 41
EXPECTED_GROUPS = 7
MAX_GROUP_SIZE = 10

# TASK-010: the B2 batch (DESIGN-DETAIL.md section 10) has 25 old tools, none of
# which is merged away (`disposition = rename` for all of them), so the batch
# count and the ported count are the same number.
EXPECTED_B2_OLD = 25


def ev(line):
    print(line)


def read_b1_old_names():
    """Re-derive the B1 old-name list from DESIGN-DETAIL.md section 10.

    The section declares `**B1 ... — 42 个**：` followed by backticked names."""
    text = io.open(DETAIL_MD, encoding="utf-8").read()
    match = re.search(r"\*\*B1[^*]*?(\d+)\s*个\*\*：(.*?)\n\n", text, re.S)
    if not match:
        sys.exit("FATAL: cannot locate the B1 paragraph in DESIGN-DETAIL.md")
    declared = int(match.group(1))
    names = re.findall(r"`([a-z0-9_]+)`", match.group(2))
    if declared != EXPECTED_B1_OLD:
        sys.exit("FATAL: DESIGN-DETAIL.md declares %d B1 tools, expected %d" % (declared, EXPECTED_B1_OLD))
    if len(names) != EXPECTED_B1_OLD:
        sys.exit("FATAL: parsed %d B1 names, expected %d" % (len(names), EXPECTED_B1_OLD))
    ev("SOURCE  DESIGN-DETAIL.md section 10: B1 declares %d old tools, parsed %d/%d"
       % (declared, len(names), EXPECTED_B1_OLD))
    return names


def main():
    raw = open(GROUPS_JSON, "rb").read()
    groups_doc = json.loads(raw.decode("utf-8"))
    rename_map = json.loads(open(MAP_JSON, "rb").read().decode("utf-8"))
    contract = json.loads(open(CONTRACT_JSON, "rb").read().decode("utf-8"))

    by_old = dict((t["old_name"], t) for t in rename_map["tools"])
    contract_names = [t["name"] for t in contract["result"]["tools"]]

    old_names = read_b1_old_names()
    missing_from_map = [n for n in old_names if n not in by_old]
    if missing_from_map:
        sys.exit("FATAL: B1 old names missing from the rename map: %s" % missing_from_map)

    excluded = [n for n in old_names if by_old[n]["disposition"] == "merge_into"]
    ported = [by_old[n]["new_name"] for n in old_names if n not in excluded]
    if len(ported) != EXPECTED_PORTED:
        sys.exit("FATAL: expected %d ported B1 tools, got %d" % (EXPECTED_PORTED, len(ported)))
    ev("DERIVE  excluded (merge_into) = %s" % ", ".join(excluded))
    ev("DERIVE  B1 tools to port = %d - %d = %d" % (EXPECTED_B1_OLD, len(excluded), len(ported)))

    groups = groups_doc["groups"]
    if len(groups) != EXPECTED_GROUPS:
        sys.exit("FATAL: expected %d groups, got %d" % (EXPECTED_GROUPS, len(groups)))

    seen = collections.Counter()
    for group in groups:
        name = group["name"]
        tools = group["tools"]
        if not tools:
            sys.exit("FATAL: group %s is empty" % name)
        if len(tools) > MAX_GROUP_SIZE:
            sys.exit("FATAL: group %s has %d tools (> %d)" % (name, len(tools), MAX_GROUP_SIZE))
        if group["channel"] not in ("editor", "running_game", "project", "os"):
            sys.exit("FATAL: group %s has an illegal channel %r" % (name, group["channel"]))
        if not isinstance(group["mutating"], bool):
            sys.exit("FATAL: group %s must declare a boolean mutating" % name)
        for tool in tools:
            seen[tool] += 1
            entry = [t for t in rename_map["tools"] if t["new_name"] == tool]
            if not entry:
                sys.exit("FATAL: group %s lists unknown tool %s" % (name, tool))
            if entry[0]["channel"] != group["channel"]:
                sys.exit("FATAL: %s is %s but group %s declares channel %s"
                         % (tool, entry[0]["channel"], name, group["channel"]))
            if bool(entry[0]["mutating"]) != group["mutating"]:
                sys.exit("FATAL: %s mutating=%s but group %s declares %s"
                         % (tool, entry[0]["mutating"], name, group["mutating"]))
        ev("GROUP   %-28s channel=%-12s mutating=%-5s implemented=%-5s tools=%d"
           % (name, group["channel"], group["mutating"], group["implemented"], len(tools)))

    duplicates = sorted(n for n, c in seen.items() if c > 1)
    if duplicates:
        sys.exit("FATAL: tool(s) listed more than once: %s" % duplicates)
    foreign = sorted(set(seen) - set(ported))
    if foreign:
        sys.exit("FATAL: tool(s) that are not B1 tools: %s" % foreign)
    absent = sorted(set(ported) - set(seen))
    if absent:
        sys.exit("FATAL: B1 tool(s) missing from the manifest: %s" % absent)

    not_in_contract = [n for n in seen if n not in contract_names]
    if not_in_contract:
        sys.exit("FATAL: manifest name(s) absent from the contract: %s" % not_in_contract)

    ev("ASSERT  distinct tools in manifest = %d" % len(seen))
    ev("ASSERT  B1 tools to port        = %d" % len(ported))
    ev("ASSERT  every B1 tool appears exactly once: PASS (duplicates=0, missing=0, foreign=0)")
    ev("ASSERT  every name exists in the 171 entry contract: PASS")
    ev("ASSERT  every group is one channel + one mutating value: PASS")
    ev("ASSERT  41 == %d - %d: PASS" % (EXPECTED_B1_OLD, len(excluded)))
    print("BYTES %d" % len(raw))
    print("SHA256 " + __import__("hashlib").sha256(raw).hexdigest())
    print("TOOL-GROUPS CHECK PASS")
    return 0


def read_b2_old_names():
    """Re-derive the B2 old-name list from DESIGN-DETAIL.md section 10.

    The paragraph is `**B2（游戏进程运行时 + 输入 + 证据）— 25 个**（**E3 解锁点**）：`
    followed by backticked names. The B1 paragraph's regex cannot be re-used: the
    B2 header carries a parenthesised annotation between the batch label and the
    count, and another bold run right after the count."""
    text = io.open(DETAIL_MD, encoding="utf-8").read()
    match = re.search(r"\*\*B2[^*]*?(\d+)\s*个\*\*(.*?)\n\n", text, re.S)
    if not match:
        sys.exit("FATAL: cannot locate the B2 paragraph in DESIGN-DETAIL.md")
    declared = int(match.group(1))
    names = re.findall(r"`([a-z0-9_]+)`", match.group(2))
    if declared != EXPECTED_B2_OLD:
        sys.exit("FATAL: DESIGN-DETAIL.md declares %d B2 tools, expected %d" % (declared, EXPECTED_B2_OLD))
    if len(names) != EXPECTED_B2_OLD:
        sys.exit("FATAL: parsed %d B2 names, expected %d" % (len(names), EXPECTED_B2_OLD))
    ev("SOURCE  DESIGN-DETAIL.md section 10: B2 declares %d old tools, parsed %d/%d"
       % (declared, len(names), EXPECTED_B2_OLD))
    return names


def main_b2():
    """Verify docs/tool-groups-b2.json (TASK-010 section 1).

    The invariant list is the B1 one - exactly once, <= 10 per group, one channel
    and one mutating value per group and both agreeing with the rename map, every
    name present in the 171 entry contract - plus the `scope` the B2 manifest
    declares per group, which is the axis TASK-010 partitions by. The checks are
    spelled out again instead of being routed through `main()` on purpose: the B1
    gate is frozen, and a shared code path would make a B2 change able to weaken
    it."""
    raw = open(GROUPS_B2_JSON, "rb").read()
    groups_doc = json.loads(raw.decode("utf-8"))
    rename_map = json.loads(open(MAP_JSON, "rb").read().decode("utf-8"))
    contract = json.loads(open(CONTRACT_JSON, "rb").read().decode("utf-8"))

    by_old = dict((t["old_name"], t) for t in rename_map["tools"])
    by_new = dict((t["new_name"], t) for t in rename_map["tools"])
    contract_names = [t["name"] for t in contract["result"]["tools"]]

    old_names = read_b2_old_names()
    missing_from_map = [n for n in old_names if n not in by_old]
    if missing_from_map:
        sys.exit("FATAL: B2 old names missing from the rename map: %s" % missing_from_map)

    excluded = [n for n in old_names if by_old[n]["disposition"] == "merge_into"]
    ported = [by_old[n]["new_name"] for n in old_names if n not in excluded]
    ev("DERIVE  excluded (merge_into) = %s" % (", ".join(excluded) if excluded else "(none)"))
    ev("DERIVE  B2 tools to port = %d - %d = %d" % (EXPECTED_B2_OLD, len(excluded), len(ported)))
    if len(ported) != EXPECTED_B2_OLD:
        sys.exit("FATAL: expected %d ported B2 tools, got %d" % (EXPECTED_B2_OLD, len(ported)))

    if groups_doc.get("batch") != "B2":
        sys.exit("FATAL: docs/tool-groups-b2.json must declare batch=B2")
    if int(groups_doc.get("total", -1)) != EXPECTED_B2_OLD:
        sys.exit("FATAL: manifest total is %r, expected %d" % (groups_doc.get("total"), EXPECTED_B2_OLD))

    groups = groups_doc["groups"]
    seen = collections.Counter()
    for group in groups:
        name = group["name"]
        tools = group["tools"]
        if not tools:
            sys.exit("FATAL: group %s is empty" % name)
        if len(tools) > MAX_GROUP_SIZE:
            sys.exit("FATAL: group %s has %d tools (> %d)" % (name, len(tools), MAX_GROUP_SIZE))
        if group["channel"] not in ("editor", "running_game", "project", "os"):
            sys.exit("FATAL: group %s has an illegal channel %r" % (name, group["channel"]))
        if not isinstance(group["mutating"], bool):
            sys.exit("FATAL: group %s must declare a boolean mutating" % name)
        if group.get("scope") not in ("editor", "game", "both"):
            sys.exit("FATAL: group %s must declare the scope of its members" % name)
        for tool in tools:
            seen[tool] += 1
            entry = by_new.get(tool)
            if entry is None:
                sys.exit("FATAL: group %s lists unknown tool %s" % (name, tool))
            if entry["channel"] != group["channel"]:
                sys.exit("FATAL: %s is %s but group %s declares channel %s"
                         % (tool, entry["channel"], name, group["channel"]))
            if bool(entry["mutating"]) != group["mutating"]:
                sys.exit("FATAL: %s mutating=%s but group %s declares %s"
                         % (tool, entry["mutating"], name, group["mutating"]))
            if entry["scope"] != group["scope"]:
                sys.exit("FATAL: %s scope=%s but group %s declares scope %s"
                         % (tool, entry["scope"], name, group["scope"]))
            derived_channel, derived_verb = _derive_channel_verb(tool)
            if derived_channel != entry["channel"]:
                sys.exit("FATAL: %s is channel %s in the map but the name says %s"
                         % (tool, entry["channel"], derived_channel))
            if derived_verb != entry["verb"]:
                sys.exit("FATAL: %s is verb %s in the map but the name says %s"
                         % (tool, entry["verb"], derived_verb))
        ev("GROUP   %-30s channel=%-12s scope=%-6s mutating=%-5s implemented=%-5s tools=%d"
           % (name, group["channel"], group["scope"], group["mutating"], group["implemented"], len(tools)))

    duplicates = sorted(n for n, c in seen.items() if c > 1)
    if duplicates:
        sys.exit("FATAL: tool(s) listed more than once: %s" % duplicates)
    foreign = sorted(set(seen) - set(ported))
    if foreign:
        sys.exit("FATAL: tool(s) that are not B2 tools: %s" % foreign)
    absent = sorted(set(ported) - set(seen))
    if absent:
        sys.exit("FATAL: B2 tool(s) missing from the manifest: %s" % absent)

    not_in_contract = [n for n in seen if n not in contract_names]
    if not_in_contract:
        sys.exit("FATAL: manifest name(s) absent from the contract: %s" % not_in_contract)

    implemented = [t for g in groups if g.get("implemented") is True for t in g["tools"]]
    ev("ASSERT  distinct tools in manifest = %d" % len(seen))
    ev("ASSERT  B2 tools to port        = %d" % len(ported))
    ev("ASSERT  every B2 tool appears exactly once: PASS (duplicates=0, missing=0, foreign=0)")
    ev("ASSERT  every name exists in the 171 entry contract: PASS")
    ev("ASSERT  every group is one channel + one scope + one mutating value: PASS")
    ev("ASSERT  group sizes <= %d: PASS" % MAX_GROUP_SIZE)
    ev("ASSERT  %d == %d - %d: PASS" % (EXPECTED_B2_OLD, EXPECTED_B2_OLD, len(excluded)))
    ev("ASSERT  implemented=true groups = %d, carrying %d tool(s): %s"
       % (len([g for g in groups if g.get("implemented") is True]), len(implemented), ", ".join(implemented)))
    print("BYTES %d" % len(raw))
    print("SHA256 " + __import__("hashlib").sha256(raw).hexdigest())
    print("TOOL-GROUPS-B2 CHECK PASS")
    return 0


# ===========================================================================
# TASK-015: the B3 / B4 / B5 manifests.
#
# `main_b2()` above and `main()` at the top are frozen: TASK-002 and TASK-010
# fixed their output and their assertions, and the three new batches must not be
# able to weaken either gate. Everything below is therefore a *new* code path;
# no line of the two frozen ones changes.
#
# The three new manifests have one property the two older ones do not need, and
# it is the reason `--check-completeness` exists as a separate mode: together
# they are supposed to cover **every** contract entry that is not implemented
# yet, so a tool that no batch claims is a hole in the port plan, and a tool two
# batches claim is double booked work. `main_batch()` checks one manifest in
# isolation; `main_completeness()` checks the union of all five.
# ===========================================================================

GROUPS_B3_JSON = os.path.join(DOCS, "tool-groups-b3.json")
GROUPS_B4_JSON = os.path.join(DOCS, "tool-groups-b4.json")
GROUPS_B5_JSON = os.path.join(DOCS, "tool-groups-b5.json")

# TASK-052 section 0 (DESIGN-DETAIL.md section 26 / GDR-28 point 3): the tools
# that are *not* ports of the frozen rename map get their own manifest. It is a
# sister file like the batch manifests - no historical batch file is edited -
# and `main_added()` below checks it with the same group rules plus the one the
# batch files do not need: its union is the contract's own `_meta.added_tools`.
GROUPS_ADDED_JSON = os.path.join(DOCS, "tool-groups-added.json")
ADDED_BATCH = "ADDED"
# GDR-28 point 2 fixes the arithmetic the completeness proof now has to make:
# `171 + N = 66 + 105 + N`, where 66 is the union of every group the B1/B2
# manifests mark implemented, 105 is the union of B3/B4/B5, and N is the number
# of added tools (`_meta.added_count`). None of the three numbers is hard-coded
# here except the two the manifests themselves declare as their totals; the
# count of ported tools (171) is derived as `contract - added`.
EXPECTED_IMPLEMENTED_B1B2 = 66
EXPECTED_IMPLEMENTED_B3B4B5 = 105

# The three new batches partition the *unimplemented* contract entries. The
# number is not hard-coded: it is derived below as
# `len(contract) - len(implemented union)` and printed with the subtraction, so
# the checker fails loudly if the contract ever grows or a batch is marked
# implemented without its tools really being registered.
BATCH_FILES = {"B3": GROUPS_B3_JSON, "B4": GROUPS_B4_JSON, "B5": GROUPS_B5_JSON}


def _load_manifest(path):
    return json.loads(open(path, "rb").read().decode("utf-8"))


# ===========================================================================
# TASK-057 section 2 (R-B2): the generator version, machine checked.
#
# Why this exists: the version of `gen_renamed_contract.py` that produced the
# contract was recorded in three places, and only two of them were ever read by
# a machine (`_meta.generator_version` is what the generator writes, and nothing
# compared it with the generator's own constant). The third one,
# `docs/tool-groups-added.json`, spelled the version inside `source.entries` as
# free prose - and drifted twice: once against the generator, once again in
# TASK-056 D2. A number that lives in a sentence cannot be asserted on, so
# TASK-057 gives it a field of its own (`source.generator_version`) and this
# function makes the three places one string or a failure.
#
# The free text is still checked, but only for *containing* the version: prose
# may say more than the number, it may not say a different number.
# ===========================================================================

GEN_SCRIPT_JSON = os.path.join(os.path.dirname(DOCS), "scripts", "gen_renamed_contract.py")
VERSION_FIELD_RE = r'^GENERATOR_VERSION\s*=\s*"([^"]+)"\s*$'
SEMVER_RE = r"^\d+\.\d+\.\d+$"


def _generator_constant_version():
    """`GENERATOR_VERSION` as written in gen_renamed_contract.py."""
    text = io.open(GEN_SCRIPT_JSON, encoding="utf-8").read()
    match = re.search(VERSION_FIELD_RE, text, re.M)
    if not match:
        sys.exit("FATAL: cannot locate `GENERATOR_VERSION = \"x.y.z\"` in %s" % GEN_SCRIPT_JSON)
    return match.group(1)


def assert_generator_version_consistency(groups_doc, contract, manifest_path=GROUPS_ADDED_JSON):
    """TASK-057 R-B2: the three generator versions must be one string.

    The three are

      1. `GENERATOR_VERSION` in `scripts/gen_renamed_contract.py` (what the
         generator *is now*);
      2. `_meta.generator_version` in `docs/tools_list.renamed.json` (what
         produced the tracked contract);
      3. `source.generator_version` in the manifest passed in (what the manifest
         claims produced its tool list).

    (1) and (2) differing means the contract is stale; (3) differing from them
    means the manifest is stale. Either way a silent drift is exactly what the
    two real incidents were, so all three are compared and the free-text
    `source.entries` sentence must at least mention the same number.

    Returns the common version so a caller can print it."""
    source = groups_doc.get("source")
    if not isinstance(source, dict):
        sys.exit("FATAL: %s has no `source` object to read a generator version from" % manifest_path)
    declared = source.get("generator_version")
    if not isinstance(declared, str) or not re.match(SEMVER_RE, declared):
        sys.exit("FATAL: %s source.generator_version is %r - expected the exact `x.y.z` string "
                 "(a free-text mention is what TASK-057 replaced; R-B2)" % (manifest_path, declared))

    constant = _generator_constant_version()
    meta = contract.get("_meta", {})
    contract_version = meta.get("generator_version")

    ev("SOURCE  GENERATOR_VERSION (%s)            = %s"
       % (os.path.relpath(GEN_SCRIPT_JSON, DOCS).replace("\\", "/"), constant))
    ev("SOURCE  contract _meta.generator_version             = %r" % (contract_version,))
    ev("SOURCE  %s source.generator_version = %r"
       % (os.path.relpath(manifest_path, DOCS).replace("\\", "/"), declared))

    failures = []
    if not isinstance(contract_version, str) or not re.match(SEMVER_RE, contract_version):
        failures.append("contract _meta.generator_version is %r, expected the exact `x.y.z` string"
                        % (contract_version,))
    if constant != contract_version:
        failures.append("the generator says %s but the tracked contract was generated by %r"
                        % (constant, contract_version))
    if declared != contract_version:
        failures.append("%s says %s but the contract was generated by %r"
                        % (manifest_path, declared, contract_version))

    # The prose may say more than the number; it may not say a different number.
    entries = source.get("entries")
    if not isinstance(entries, str) or declared not in entries:
        failures.append("source.entries does not even mention %s, so the sentence and the field "
                        "disagree: %r" % (declared, entries))

    if failures:
        for failure in failures:
            ev("FATAL   %s" % failure)
        sys.exit("FATAL: generator version consistency failed (TASK-057 R-B2): all three of "
                 "GENERATOR_VERSION, _meta.generator_version and source.generator_version must be "
                 "the same string; got %r / %r / %r"
                 % (constant, contract_version, declared))

    ev("ASSERT  GENERATOR_VERSION == _meta.generator_version == source.generator_version: PASS (%s)"
       % declared)
    ev("ASSERT  source.entries contains the same version string: PASS")
    return declared


def main_added():
    """Verify docs/tool-groups-added.json (TASK-052, GDR-28 point 3).

    The same invariants as `main_batch()` - every tool exactly once, <= 10 per
    group, one channel + one scope + one mutating value per group - with two
    differences that exist because an added tool has no `tool-rename-map.json`
    row:

      * `channel` and `verb` cannot be read from the map, so the group has to
        declare its `verb` as well, and the name-derived channel/verb pair is
        compared with that declaration (the same derivation
        `MCPToolRegistry::parse_tool_name` implements);
      * the ownership check is not "the manifest equals the contract minus the
        batches" but "the manifest equals `_meta.added_tools`", both directions.
        That is the invariant that keeps the generator's table and this manifest
        from drifting: a name added to one and not the other fails here.

    An added verb is legal only when the map's closed set contains it or
    `verb_extensions` carries a record for it, and every record has to be used
    by a group - so the set of verbs the contract ever invented is printed on
    every run instead of accumulating silently."""
    raw = open(GROUPS_ADDED_JSON, "rb").read()
    groups_doc = json.loads(raw.decode("utf-8"))
    rename_map = json.loads(open(MAP_JSON, "rb").read().decode("utf-8"))
    contract = json.loads(open(CONTRACT_JSON, "rb").read().decode("utf-8"))

    closed_set = set(rename_map["convention"]["verb_closed_set"])
    contract_names = [t["name"] for t in contract["result"]["tools"]]
    contract_set = set(contract_names)
    meta = contract.get("_meta", {})
    added_meta = list(meta.get("added_tools", []))
    if int(meta.get("added_count", -1)) != len(added_meta):
        sys.exit("FATAL: contract _meta.added_count %r != len(added_tools) %d"
                 % (meta.get("added_count"), len(added_meta)))
    if len(set(added_meta)) != len(added_meta):
        sys.exit("FATAL: contract _meta.added_tools has duplicates: %s" % added_meta)

    if groups_doc.get("batch") != ADDED_BATCH:
        sys.exit("FATAL: %s must declare batch=%s" % (GROUPS_ADDED_JSON, ADDED_BATCH))

    # TASK-057 section 2 (R-B2): before anything else is believed about this
    # manifest, the generator that produced its tool list has to be the one that
    # produced the contract (and both have to be the one in the source tree).
    assert_generator_version_consistency(groups_doc, contract, GROUPS_ADDED_JSON)

    extensions = {}
    for record in groups_doc.get("verb_extensions", []):
        verb = record.get("verb", "")
        if not verb or not str(record.get("reason", "")).strip():
            sys.exit("FATAL: every verb_extension needs a non-empty verb and reason: %r" % (record,))
        if verb in closed_set:
            sys.exit("FATAL: verb_extension '%s' is already in the map's closed set - a stale record"
                     % verb)
        if verb in extensions:
            sys.exit("FATAL: verb_extension '%s' is declared twice" % verb)
        extensions[verb] = record["reason"]
    ev("SOURCE  map closed set = %d verb(s); added verb_extension(s) = %s"
       % (len(closed_set), ", ".join(sorted(extensions)) if extensions else "(none)"))

    groups = groups_doc["groups"]
    if not groups:
        sys.exit("FATAL: %s has no groups" % GROUPS_ADDED_JSON)

    seen = collections.Counter()
    extensions_used = set()
    for group in groups:
        name = group["name"]
        tools = group["tools"]
        if not tools:
            sys.exit("FATAL: group %s is empty" % name)
        if len(tools) > MAX_GROUP_SIZE:
            sys.exit("FATAL: group %s has %d tools (> %d)" % (name, len(tools), MAX_GROUP_SIZE))
        if group.get("batch") != ADDED_BATCH:
            sys.exit("FATAL: group %s declares batch %r, expected %s" % (name, group.get("batch"), ADDED_BATCH))
        if group["channel"] not in ("editor", "running_game", "project", "os"):
            sys.exit("FATAL: group %s has an illegal channel %r" % (name, group["channel"]))
        if not isinstance(group["mutating"], bool):
            sys.exit("FATAL: group %s must declare a boolean mutating" % name)
        if group.get("scope") not in ("editor", "game", "both"):
            sys.exit("FATAL: group %s must declare the scope of its members" % name)
        if group.get("implemented") is not True and group.get("implemented") is not False:
            sys.exit("FATAL: group %s must declare a boolean implemented" % name)
        if not group.get("notes"):
            sys.exit("FATAL: group %s must carry a note explaining its grouping" % name)
        declared_verb = group.get("verb")
        if declared_verb is None:
            sys.exit("FATAL: group %s must declare the verb of its members (there is no rename map row)"
                     % name)
        for tool in tools:
            seen[tool] += 1
            if tool not in contract_set:
                sys.exit("FATAL: group %s lists %s, which is not in the contract" % (name, tool))
            derived_channel, derived_verb = _derive_channel_verb(tool)
            if derived_channel != group["channel"]:
                sys.exit("FATAL: %s is channel %s in the group but the name says %s"
                         % (tool, group["channel"], derived_channel))
            if derived_verb != declared_verb:
                sys.exit("FATAL: %s is verb %s in the group but the name says %s"
                         % (tool, declared_verb, derived_verb))
            if derived_verb not in closed_set and derived_verb not in extensions:
                sys.exit("FATAL: verb '%s' of %s is outside the map's closed set and has no "
                         "verb_extensions record" % (derived_verb, tool))
            if derived_verb in extensions:
                extensions_used.add(derived_verb)
        ev("GROUP   %-30s channel=%-12s scope=%-6s mutating=%-5s implemented=%-5s verb=%-8s tools=%d"
           % (name, group["channel"], group["scope"], group["mutating"], group["implemented"],
              declared_verb, len(tools)))

    duplicates = sorted(n for n, c in seen.items() if c > 1)
    if duplicates:
        sys.exit("FATAL: tool(s) listed more than once in %s: %s" % (ADDED_BATCH, duplicates))
    stale_extensions = sorted(set(extensions) - extensions_used)
    if stale_extensions:
        sys.exit("FATAL: verb_extension record(s) never used by a group: %s" % stale_extensions)

    foreign = sorted(set(seen) - set(added_meta))
    if foreign:
        sys.exit("FATAL: manifest tool(s) that _meta.added_tools does not list: %s" % foreign)
    absent = sorted(set(added_meta) - set(seen))
    if absent:
        sys.exit("FATAL: _meta.added_tools name(s) missing from this manifest: %s" % absent)

    if int(groups_doc.get("total", -1)) != len(seen):
        sys.exit("FATAL: %s total is %r, expected %d" % (GROUPS_ADDED_JSON, groups_doc.get("total"), len(seen)))

    ev("ASSERT  distinct added tools in manifest = %d" % len(seen))
    ev("ASSERT  manifest = contract _meta.added_tools, both directions: PASS (missing=0, foreign=0)")
    ev("ASSERT  every added tool appears exactly once: PASS (duplicates=0)")
    ev("ASSERT  every name exists in the %d entry contract: PASS" % len(contract_names))
    ev("ASSERT  every group is one channel + one scope + one mutating value: PASS")
    ev("ASSERT  channel and verb derived from every tool name agree with the group declaration: PASS")
    ev("ASSERT  every added verb is in the closed set or has a used verb_extensions record: PASS")
    ev("ASSERT  group sizes <= %d: PASS" % MAX_GROUP_SIZE)
    print("BYTES %d" % len(raw))
    print("SHA256 " + __import__("hashlib").sha256(raw).hexdigest())
    print("TOOL-GROUPS-ADDED CHECK PASS")
    return 0


def _implemented_from(groups_doc):
    """The tool names of every group the manifest marks `implemented: true`."""
    return set(t for g in groups_doc["groups"] if g.get("implemented") is True for t in g["tools"])


# TASK-015 section 1.2: "channel/verb/scope/mutating must agree with
# docs/tool-rename-map.json, entry by entry". The three manifests carry
# channel/scope/mutating explicitly (the same fields the B1/B2 manifests have);
# `verb` is *derived from the name* exactly the way `MCPToolRegistry::parse_tool_name`
# derives it (longest channel prefix, then the first underscore-separated
# segment) and compared with the map. That closes the loop without inventing a
# fourth field in the manifest: the name's own verb, the declared verb and the
# map's verb cannot drift apart for any tool of the three batches.
CHANNEL_PREFIXES = ("editor_", "running_game_", "project_", "os_")


def _derive_channel_verb(tool_name):
    channel = None
    for prefix in CHANNEL_PREFIXES:
        if tool_name.startswith(prefix):
            channel = prefix[:-1]
            remainder = tool_name[len(prefix):]
            break
    if channel is None:
        return None, None
    verb = remainder.split("_", 1)[0] if remainder else ""
    return channel, verb


def main_batch(batch):
    """Verify one of the TASK-015 manifests (B3 / B4 / B5).

    Same invariants as B2 - every tool exactly once, <= 10 per group, one
    channel + one scope + one mutating value per group and all three agreeing
    with the rename map, every name present in the 171 entry contract - plus the
    verb derivation described above. It drops only the "batch list re-derived
    from DESIGN-DETAIL.md section 10" step: that section names B3/B4/B5 by
    subsystem and by example, not as a frozen enumeration, so the batch
    membership is checked against the *contract and the other batches* instead
    (see `main_completeness`)."""
    path = BATCH_FILES[batch]
    raw = open(path, "rb").read()
    groups_doc = json.loads(raw.decode("utf-8"))
    rename_map = json.loads(open(MAP_JSON, "rb").read().decode("utf-8"))
    contract = json.loads(open(CONTRACT_JSON, "rb").read().decode("utf-8"))

    by_new = dict((t["new_name"], t) for t in rename_map["tools"])
    contract_names = [t["name"] for t in contract["result"]["tools"]]

    if groups_doc.get("batch") != batch:
        sys.exit("FATAL: %s must declare batch=%s" % (path, batch))
    groups = groups_doc["groups"]
    if not groups:
        sys.exit("FATAL: %s has no groups" % path)

    seen = collections.Counter()
    implemented = []
    for group in groups:
        name = group["name"]
        tools = group["tools"]
        if not tools:
            sys.exit("FATAL: group %s is empty" % name)
        if len(tools) > MAX_GROUP_SIZE:
            sys.exit("FATAL: group %s has %d tools (> %d)" % (name, len(tools), MAX_GROUP_SIZE))
        if group.get("batch") != batch:
            sys.exit("FATAL: group %s declares batch %r, expected %s" % (name, group.get("batch"), batch))
        if group["channel"] not in ("editor", "running_game", "project", "os"):
            sys.exit("FATAL: group %s has an illegal channel %r" % (name, group["channel"]))
        if not isinstance(group["mutating"], bool):
            sys.exit("FATAL: group %s must declare a boolean mutating" % name)
        if group.get("scope") not in ("editor", "game", "both"):
            sys.exit("FATAL: group %s must declare the scope of its members" % name)
        if group.get("implemented") is not True and group.get("implemented") is not False:
            sys.exit("FATAL: group %s must declare a boolean implemented" % name)
        if not group.get("notes"):
            sys.exit("FATAL: group %s must carry a note explaining its grouping" % name)
        if group.get("implemented") is True:
            implemented.extend(tools)
        for tool in tools:
            seen[tool] += 1
            entry = by_new.get(tool)
            if entry is None:
                sys.exit("FATAL: group %s lists unknown tool %s" % (name, tool))
            if entry["channel"] != group["channel"]:
                sys.exit("FATAL: %s is %s but group %s declares channel %s"
                         % (tool, entry["channel"], name, group["channel"]))
            if bool(entry["mutating"]) != group["mutating"]:
                sys.exit("FATAL: %s mutating=%s but group %s declares %s"
                         % (tool, entry["mutating"], name, group["mutating"]))
            if entry["scope"] != group["scope"]:
                sys.exit("FATAL: %s scope=%s but group %s declares scope %s"
                         % (tool, entry["scope"], name, group["scope"]))
            derived_channel, derived_verb = _derive_channel_verb(tool)
            if derived_channel != entry["channel"]:
                sys.exit("FATAL: %s is channel %s in the map but the name says %s"
                         % (tool, entry["channel"], derived_channel))
            if derived_verb != entry["verb"]:
                sys.exit("FATAL: %s is verb %s in the map but the name says %s"
                         % (tool, entry["verb"], derived_verb))
        ev("GROUP   %-30s channel=%-12s scope=%-6s mutating=%-5s implemented=%-5s tools=%d"
           % (name, group["channel"], group["scope"], group["mutating"], group["implemented"], len(tools)))

    duplicates = sorted(n for n, c in seen.items() if c > 1)
    if duplicates:
        sys.exit("FATAL: tool(s) listed more than once in %s: %s" % (batch, duplicates))

    not_in_contract = sorted(n for n in seen if n not in contract_names)
    if not_in_contract:
        sys.exit("FATAL: manifest name(s) absent from the contract: %s" % not_in_contract)

    if int(groups_doc.get("total", -1)) != len(seen):
        sys.exit("FATAL: %s total is %r, expected %d" % (path, groups_doc.get("total"), len(seen)))

    ev("ASSERT  distinct tools in %s manifest = %d" % (batch, len(seen)))
    ev("ASSERT  every tool appears exactly once: PASS (duplicates=0)")
    ev("ASSERT  every name exists in the 171 entry contract: PASS")
    ev("ASSERT  every group is one channel + one scope + one mutating value: PASS")
    ev("ASSERT  channel and verb derived from every tool name agree with the rename map: PASS")
    ev("ASSERT  every group carries a note: PASS")
    ev("ASSERT  group sizes <= %d: PASS" % MAX_GROUP_SIZE)
    ev("ASSERT  implemented=true groups = %d, carrying %d tool(s): %s"
       % (len([g for g in groups if g.get("implemented") is True]), len(implemented), ", ".join(implemented)))
    print("BYTES %d" % len(raw))
    print("SHA256 " + __import__("hashlib").sha256(raw).hexdigest())
    print("TOOL-GROUPS-%s CHECK PASS" % batch)
    return 0


def main_completeness():
    """The completeness proof, for all six manifests.

    TASK-015 section 1 asked for a machine checkable "the three manifests
    together are exactly the rest of the contract". The arithmetic in that task
    book ("171 - 2 unregister - 66 = 103") double counts the two
    `unregister_until_implemented` entries: those two names
    (`running_game_move_player_to_target_via_navigation` and
    `project_export_game`) are **not in the contract at all** - the generator
    dropped them when the contract was emitted - so they must not be subtracted
    a second time. The check below derives the expected size instead of
    repeating the literal, proves both facts about the two unregistered names,
    and fails if the derivation ever stops matching.

    TASK-052 (GDR-28 point 2) changes the union assertion from `171 = 66 + 105`
    to `**171 + N = 66 + 105 + N**`, with N = `_meta.added_count`. The added tools
    are a fourth, disjoint bucket: they are implemented (their manifest says so)
    and therefore leave `expected` exactly like B1/B2 do, but they are not bath
    members and "which file owns this name" has one answer for them too. Each of
    the four buckets is asserted to be disjoint from the other three, so the
    count identity can only hold when every name is in exactly one of them."""
    docs = {}
    docs["B1"] = _load_manifest(GROUPS_JSON)
    docs["B2"] = _load_manifest(GROUPS_B2_JSON)
    for batch in ("B3", "B4", "B5"):
        docs[batch] = _load_manifest(BATCH_FILES[batch])
    docs[ADDED_BATCH] = _load_manifest(GROUPS_ADDED_JSON)

    rename_map = json.loads(open(MAP_JSON, "rb").read().decode("utf-8"))
    contract = json.loads(open(CONTRACT_JSON, "rb").read().decode("utf-8"))
    contract_names = [t["name"] for t in contract["result"]["tools"]]
    contract_set = set(contract_names)
    by_new = dict((t["new_name"], t) for t in rename_map["tools"])

    implemented = set()
    for batch in ("B1", "B2"):
        implemented |= _implemented_from(docs[batch])
    implemented_b1b2 = len(implemented)

    # TASK-052: the added bucket. Its authority is the contract's own
    # `_meta.added_tools`; `main_added()` is what proves the manifest and the
    # meta agree, and the two lines below re-derive the size from `added_count`
    # so that a contract whose meta lied about its own list is caught here too.
    added = set(_implemented_from(docs[ADDED_BATCH]))
    added_meta = list(contract.get("_meta", {}).get("added_tools", []))
    if int(contract.get("_meta", {}).get("added_count", -1)) != len(added_meta):
        sys.exit("FATAL: contract _meta.added_count %r != len(added_tools) %d"
                 % (contract.get("_meta", {}).get("added_count"), len(added_meta)))
    if added != set(added_meta):
        sys.exit("FATAL: docs/tool-groups-added.json and _meta.added_tools differ: manifest-only=%s meta-only=%s"
                 % (sorted(added - set(added_meta)), sorted(set(added_meta) - added)))
    if added & implemented:
        sys.exit("FATAL: the added manifest and the B1/B2 manifests overlap: %s" % sorted(added & implemented))
    not_in_contract = sorted(n for n in added if n not in contract_set)
    if not_in_contract:
        sys.exit("FATAL: added tool(s) absent from the contract: %s" % not_in_contract)
    implemented |= added

    expected = [n for n in contract_names if n not in implemented]

    ev("SOURCE  contract entries                       = %d" % len(contract_names))
    ev("SOURCE  implemented by the B1/B2 manifests    = %d" % implemented_b1b2)
    ev("SOURCE  added tools (_meta.added_tools)       = %d (%s)"
       % (len(added_meta), ", ".join(added_meta) if added_meta else "(none)"))
    ev("DERIVE  contract - implemented                 = %d - %d = %d"
       % (len(contract_names), len(implemented), len(expected)))

    # The two unregister_until_implemented entries are map-only. Proven, not
    # assumed: if either ever entered the contract the derivation above would
    # have to subtract it, and this check is what would catch that.
    unregister = [t["new_name"] for t in rename_map["tools"]
                  if t["disposition"] == "unregister_until_implemented"]
    if len(unregister) != 2:
        sys.exit("FATAL: expected 2 unregister_until_implemented entries, got %d" % len(unregister))
    in_contract = [n for n in unregister if n in contract_set]
    if in_contract:
        sys.exit("FATAL: unregister_until_implemented name(s) present in the contract: %s" % in_contract)
    ev("ASSERT  the 2 unregister_until_implemented names are absent from the contract: PASS (%s)"
       % ", ".join(unregister))
    ev("ASSERT  they are therefore NOT subtracted a second time (the literal 103 of TASK-015"
       " section 1 double counts them; the derived size is %d)" % len(expected))

    # Every contract entry is either implemented or claimed by exactly one of
    # B3/B4/B5.
    missing = sorted(set(expected) - set(t for b in ("B3", "B4", "B5") for g in docs[b]["groups"] for t in g["tools"]))
    if missing:
        sys.exit("FATAL: unimplemented contract tool(s) claimed by no batch: %s" % missing)

    seen = collections.Counter()
    for batch in ("B3", "B4", "B5"):
        for group in docs[batch]["groups"]:
            for tool in group["tools"]:
                seen[tool] += 1
                if tool not in contract_set:
                    sys.exit("FATAL: %s/%s lists %s, which is not in the contract" % (batch, group["name"], tool))
                if tool in implemented:
                    sys.exit("FATAL: %s/%s lists %s, which B1/B2 or the added manifest already implemented"
                             % (batch, group["name"], tool))
    duplicates = sorted(n for n, c in seen.items() if c > 1)
    if duplicates:
        sys.exit("FATAL: tool(s) claimed by more than one of B3/B4/B5: %s" % duplicates)

    foreign = sorted(set(seen) - set(expected))
    if foreign:
        sys.exit("FATAL: manifest tool(s) that are not unimplemented contract entries: %s" % foreign)
    absent = sorted(set(expected) - set(seen))
    if absent:
        sys.exit("FATAL: unimplemented contract tool(s) missing from B3/B4/B5: %s" % absent)

    # The three manifests are pairwise disjoint and disjoint from B1/B2 and from
    # the added bucket. The counter above already proves the first half; this
    # states it explicitly so that a future edit which merged two manifests
    # cannot pass by accident.
    sets = {}
    for batch in ("B3", "B4", "B5"):
        sets[batch] = set(t for g in docs[batch]["groups"] for t in g["tools"])
    for a, b in (("B3", "B4"), ("B3", "B5"), ("B4", "B5")):
        if sets[a] & sets[b]:
            sys.exit("FATAL: %s and %s overlap: %s" % (a, b, sorted(sets[a] & sets[b])))
    for batch in ("B3", "B4", "B5"):
        if sets[batch] & implemented:
            sys.exit("FATAL: %s overlaps B1/B2 or the added manifest: %s" % (batch, sorted(sets[batch] & implemented)))
        if sets[batch] & added:
            sys.exit("FATAL: %s overlaps the added manifest: %s" % (batch, sorted(sets[batch] & added)))

    ev("ASSERT  B3 + B4 + B5 = %d + %d + %d = %d tool(s), each exactly once: PASS"
       % (len(sets["B3"]), len(sets["B4"]), len(sets["B5"]), len(seen)))
    ev("ASSERT  B3/B4/B5 pairwise disjoint: PASS")
    ev("ASSERT  B3/B4/B5 disjoint from B1/B2 (%d tools) and the added manifest (%d tools): PASS"
       % (implemented_b1b2, len(added)))
    ev("ASSERT  in_contract_and_not_implemented, both directions of the difference: PASS (missing=0, foreign=0)")
    ev("ASSERT  every claimed name exists in the %d entry contract: PASS" % len(contract_names))
    if len(seen) != len(expected):
        sys.exit("FATAL: classified %d tools, expected %d" % (len(seen), len(expected)))

    # GDR-28 point 2, the identity this whole mode exists for. Every term is
    # derived (the 171 is `contract - added`, 66 is the B1/B2 union, 105 is the
    # B3/B4/B5 union), so the printed equality is a proof and not a restatement.
    ported = len(contract_names) - len(added)
    if ported != implemented_b1b2 + len(seen):
        sys.exit("FATAL: 171 + N != 66 + 105 + N: ported=%d but %d + %d"
                 % (ported, implemented_b1b2, len(seen)))
    if implemented_b1b2 != EXPECTED_IMPLEMENTED_B1B2:
        sys.exit("FATAL: the B1/B2 manifests implement %d tools, expected %d"
                 % (implemented_b1b2, EXPECTED_IMPLEMENTED_B1B2))
    if len(seen) != EXPECTED_IMPLEMENTED_B3B4B5:
        sys.exit("FATAL: B3/B4/B5 carry %d tools, expected %d" % (len(seen), EXPECTED_IMPLEMENTED_B3B4B5))
    ev("ASSERT  %d + %d = %d + %d + %d: PASS (contract = B1/B2 union + B3/B4/B5 union + added)"
       % (ported, len(added), implemented_b1b2, len(seen), len(added)))
    ev("ASSERT  every one of the %d contract names is in exactly one of the four buckets: PASS"
       % len(contract_names))

    for batch in ("B3", "B4", "B5"):
        print("BYTES %s %d" % (batch, len(open(BATCH_FILES[batch], "rb").read())))
        print("SHA256 %s %s" % (batch, __import__("hashlib").sha256(open(BATCH_FILES[batch], "rb").read()).hexdigest()))
    print("BYTES %s %d" % (ADDED_BATCH, len(open(GROUPS_ADDED_JSON, "rb").read())))
    print("SHA256 %s %s" % (ADDED_BATCH, __import__("hashlib").sha256(open(GROUPS_ADDED_JSON, "rb").read()).hexdigest()))
    print("TOOL-GROUPS-COMPLETENESS CHECK PASS")
    return 0


def main_generator_version():
    """TASK-057 section 2 (R-B2): the version consistency assertion on its own.

    `main_added()` runs the same function, so the gate is not a second opinion -
    this mode exists so that the assertion can be aimed at, demonstrated and
    logged on its own (the failure demo of TASK-057 edits exactly one of the
    three places and expects a non-zero exit here and in `--added`)."""
    groups_doc = _load_manifest(GROUPS_ADDED_JSON)
    contract = json.loads(open(CONTRACT_JSON, "rb").read().decode("utf-8"))
    version = assert_generator_version_consistency(groups_doc, contract, GROUPS_ADDED_JSON)
    print("GENERATOR-VERSION CHECK PASS (%s)" % version)
    return 0


if __name__ == "__main__":
    # TASK-037 D1: the B1 invariants live in `main()`, which is the no-argument
    # path. The usage string nevertheless advertised `--batch B1`, and the
    # dispatch below then reported `unknown batch: B1` and exited 1 - so the
    # documented spelling contradicted the code (REPORT-AUDIT-B5 D1). `--batch B1`
    # is now *accepted* and routed to the same frozen `main()`: the gate is the
    # same code path and the same exit code, so no invariant is weakened and the
    # usage text becomes true. B2 keeps its own `main_b2()` (TASK-010), and
    # B3/B4/B5 keep `main_batch()`.
    #
    # TASK-052 adds `--added` (the new manifest of GDR-28 point 3). It is a new
    # code path like the TASK-015 trio was: no frozen path is edited.
    if len(sys.argv) == 2 and sys.argv[1] == "--added":
        sys.exit(main_added())
    # TASK-057: the R-B2 generator-version assertion on its own.
    if len(sys.argv) == 2 and sys.argv[1] == "--generator-version":
        sys.exit(main_generator_version())
    if len(sys.argv) == 3 and sys.argv[1] == "--batch" and sys.argv[2].upper() in BATCH_FILES:
        sys.exit(main_batch(sys.argv[2].upper()))
    if len(sys.argv) == 3 and sys.argv[1] == "--batch" and sys.argv[2].upper() == "B2":
        sys.exit(main_b2())
    if len(sys.argv) == 2 and sys.argv[1] == "--check-completeness":
        sys.exit(main_completeness())
    # TASK-015: the B1 fallback line below is byte for byte the one TASK-002
    # froze; the unknown-batch message was inserted before it by TASK-015 and
    # `--batch B1` is routed to the frozen path by TASK-037.
    if len(sys.argv) == 3 and sys.argv[1] == "--batch" and sys.argv[2].upper() == "B1":
        sys.exit(main())
    if len(sys.argv) == 3 and sys.argv[1] == "--batch":
        sys.exit("usage: check_tool_groups.py [--batch B1|B2|B3|B4|B5] [--added] [--generator-version] [--check-completeness]   (unknown batch: %s)" % sys.argv[2])
    if len(sys.argv) != 1:
        sys.exit("usage: check_tool_groups.py [--batch B1|B2|B3|B4|B5] [--added] [--generator-version] [--check-completeness]")
    sys.exit(main())

    rename_map = json.loads(open(MAP_JSON, "rb").read().decode("utf-8"))
    contract = json.loads(open(CONTRACT_JSON, "rb").read().decode("utf-8"))
    contract_names = [t["name"] for t in contract["result"]["tools"]]
    contract_set = set(contract_names)
    by_new = dict((t["new_name"], t) for t in rename_map["tools"])

    implemented = set()
    for batch in ("B1", "B2"):
        implemented |= _implemented_from(docs[batch])
    expected = [n for n in contract_names if n not in implemented]

    ev("SOURCE  contract entries                       = %d" % len(contract_names))
    ev("SOURCE  implemented by the B1/B2 manifests    = %d" % len(implemented))
    ev("DERIVE  contract - implemented                 = %d - %d = %d"
       % (len(contract_names), len(implemented), len(expected)))

    # The two unregister_until_implemented entries are map-only. Proven, not
    # assumed: if either ever entered the contract the derivation above would
    # have to subtract it, and this check is what would catch that.
    unregister = [t["new_name"] for t in rename_map["tools"]
                  if t["disposition"] == "unregister_until_implemented"]
    if len(unregister) != 2:
        sys.exit("FATAL: expected 2 unregister_until_implemented entries, got %d" % len(unregister))
    in_contract = [n for n in unregister if n in contract_set]
    if in_contract:
        sys.exit("FATAL: unregister_until_implemented name(s) present in the contract: %s" % in_contract)
    ev("ASSERT  the 2 unregister_until_implemented names are absent from the contract: PASS (%s)"
       % ", ".join(unregister))
    ev("ASSERT  they are therefore NOT subtracted a second time (the literal 103 of TASK-015"
       " section 1 double counts them; the derived size is %d)" % len(expected))

    # Every contract entry is either implemented or claimed by exactly one of
    # B3/B4/B5.
    missing = sorted(set(expected) - set(t for b in ("B3", "B4", "B5") for g in docs[b]["groups"] for t in g["tools"]))
    if missing:
        sys.exit("FATAL: unimplemented contract tool(s) claimed by no batch: %s" % missing)

    seen = collections.Counter()
    for batch in ("B3", "B4", "B5"):
        for group in docs[batch]["groups"]:
            for tool in group["tools"]:
                seen[tool] += 1
                if tool not in contract_set:
                    sys.exit("FATAL: %s/%s lists %s, which is not in the contract" % (batch, group["name"], tool))
                if tool in implemented:
                    sys.exit("FATAL: %s/%s lists %s, which B1/B2 already implemented" % (batch, group["name"], tool))
    duplicates = sorted(n for n, c in seen.items() if c > 1)
    if duplicates:
        sys.exit("FATAL: tool(s) claimed by more than one of B3/B4/B5: %s" % duplicates)

    foreign = sorted(set(seen) - set(expected))
    if foreign:
        sys.exit("FATAL: manifest tool(s) that are not unimplemented contract entries: %s" % foreign)
    absent = sorted(set(expected) - set(seen))
    if absent:
        sys.exit("FATAL: unimplemented contract tool(s) missing from B3/B4/B5: %s" % absent)

    # The three manifests are pairwise disjoint and disjoint from B1/B2. The
    # counter above already proves the first half; this states it explicitly so
    # that a future edit which merged two manifests cannot pass by accident.
    sets = {}
    for batch in ("B3", "B4", "B5"):
        sets[batch] = set(t for g in docs[batch]["groups"] for t in g["tools"])
    for a, b in (("B3", "B4"), ("B3", "B5"), ("B4", "B5")):
        if sets[a] & sets[b]:
            sys.exit("FATAL: %s and %s overlap: %s" % (a, b, sorted(sets[a] & sets[b])))
    for batch in ("B3", "B4", "B5"):
        if sets[batch] & implemented:
            sys.exit("FATAL: %s overlaps B1/B2: %s" % (batch, sorted(sets[batch] & implemented)))

    ev("ASSERT  B3 + B4 + B5 = %d + %d + %d = %d tool(s), each exactly once: PASS"
       % (len(sets["B3"]), len(sets["B4"]), len(sets["B5"]), len(seen)))
    ev("ASSERT  B3/B4/B5 pairwise disjoint: PASS")
    ev("ASSERT  B3/B4/B5 disjoint from B1/B2 (66 tools): PASS")
    ev("ASSERT  in_contract_and_not_implemented, both directions of the difference: PASS (missing=0, foreign=0)")
    ev("ASSERT  every claimed name exists in the 171 entry contract: PASS")
    if len(seen) != len(expected):
        sys.exit("FATAL: classified %d tools, expected %d" % (len(seen), len(expected)))

    for batch in ("B3", "B4", "B5"):
        print("BYTES %s %d" % (batch, len(open(BATCH_FILES[batch], "rb").read())))
        print("SHA256 %s %s" % (batch, __import__("hashlib").sha256(open(BATCH_FILES[batch], "rb").read()).hexdigest()))
    print("TOOL-GROUPS-COMPLETENESS CHECK PASS")
    return 0


if __name__ == "__main__":
    # TASK-037 D1: the B1 invariants live in `main()`, which is the no-argument
    # path. The usage string nevertheless advertised `--batch B1`, and the
    # dispatch below then reported `unknown batch: B1` and exited 1 - so the
    # documented spelling contradicted the code (REPORT-AUDIT-B5 D1). `--batch B1`
    # is now *accepted* and routed to the same frozen `main()`: the gate is the
    # same code path and the same exit code, so no invariant is weakened and the
    # usage text becomes true. B2 keeps its own `main_b2()` (TASK-010), and
    # B3/B4/B5 keep `main_batch()`.
    if len(sys.argv) == 3 and sys.argv[1] == "--batch" and sys.argv[2].upper() in BATCH_FILES:
        sys.exit(main_batch(sys.argv[2].upper()))
    if len(sys.argv) == 3 and sys.argv[1] == "--batch" and sys.argv[2].upper() == "B2":
        sys.exit(main_b2())
    if len(sys.argv) == 2 and sys.argv[1] == "--check-completeness":
        sys.exit(main_completeness())
    # TASK-015: the B1 fallback line below is byte for byte the one TASK-002
    # froze; the unknown-batch message was inserted before it by TASK-015 and
    # `--batch B1` is routed to the frozen path by TASK-037.
    if len(sys.argv) == 3 and sys.argv[1] == "--batch" and sys.argv[2].upper() == "B1":
        sys.exit(main())
    if len(sys.argv) == 3 and sys.argv[1] == "--batch":
        sys.exit("usage: check_tool_groups.py [--batch B1|B2|B3|B4|B5]   (unknown batch: %s)" % sys.argv[2])
    if len(sys.argv) != 1:
        sys.exit("usage: check_tool_groups.py [--batch B1|B2|B3|B4|B5]")
    sys.exit(main())
