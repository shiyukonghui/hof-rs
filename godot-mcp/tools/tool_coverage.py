#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""tool_coverage.py -- the refreshable tool-coverage ledger (TASK-110 item A).

TASK-108 measured coverage once, by hand, and wrote the answer into a report.
This script is that measurement made executable and repeatable: point it at the
contract and at `runs/**/trace-*.jsonl` and it re-derives, from the trace原文,
the two things the ledger has to answer:

    * how many times was each of the 177 contract tools called, and
    * is that a *coverage* number or just a *count* - was at least one call
      effective, and was at least one call a boundary/failure?

Two corpus modes, never mixed (they answer different questions):

    --only-final   the 20 final-run tags of dist/review_data.json (the TASK-108
                   section 3 corpus)
    (default)      every `runs/**/trace-*.jsonl` (the TASK-108 section 4 corpus),
                   which now also contains the TASK-110 exercise runs.

Per-call facts come from `mcp_trace_ledger.py` itself, imported as a module, so
"effective" and "boundary" use that reader's verdict vocabulary instead of a
second, drifting definition:

    boundary  = the call answered `ok=false`.
    effective = for a READ-verb tool (get/read/search/list/find/analyze/detect/
                convert/validate/check): the call answered ok and returned a
                substantive payload; a read never moves a pixel or a byte, so the
                payload IS its evidence.
                for every other verb (create/edit/set/add/remove/write/build...):
                the ledger's own ok_effect_observed / ok_file_effect_observed -
                i.e. the call really changed the screen or a file.

Outputs (both are fully regenerated on every run):

    TOOL-COVERAGE.md   总表 + 分桶 + <5 清单 + 不可达登记表的联动视图
    coverage.json      the same data, machine readable

TASK-112 item B adds the **evidence tier** ladder. "effective >= 1" is a
pass/fail bit, and a bit cannot say *how strong* the evidence behind it is; the
ledger therefore labels every tool with one tier:

    pixel_effect > file_effect > readback > count_only        (no_calls = 0 calls)

and `readback` has two explicitly distinct kinds:

    * `witness_read` - a **write**-class tool's effect corroborated by an
      INDEPENDENT READ CALL in the same run. The pairing is not inferred here:
      it is **declared in a session manifest** (`readback` array, see
      `tools/sessions/_exercises/**/*-manifest.json`) and this reader only
      accepts a declaration whose witness call it can find again in the run's
      trace, answering `ok=true` with a substantive payload. A tool's own
      response saying "success" is *not* a readback witness.

TASK-113 item C upgrades that witness from the *call* level to the *content*
level. A declaration may carry `expect`: one literal string, or a list of them,
that must appear **verbatim** in the payload of the witness call this reader
found (the call's `result_json`, or the verified sidecar file when the payload
was over the inline budget). The check is a plain byte-level `in` test on the
payload, so "the witness call happened" is no longer enough - the value the
writer claims to have written has to be readable back out of the engine's own
answer. A declaration whose `expect` cannot be matched grants **no** tier and is
reported under the rejected list with that reason, exactly like a missing
witness call.
    * `own_payload`  - a READ-verb tool: its answer *is* the measurement, so
      there is no separate call to wait for (the TASK-111 `READ_VERBS` rule).

Usage:
    python tools/tool_coverage.py [--only-final] [--runs DIR] [--exclude NAME]
                                  [--targets FILE] [--md PATH] [--json PATH]

Exit 0 when the ledger was written, 2 on a usage/IO error.
"""
import argparse
import datetime
import hashlib
import importlib.util
import io
import json
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)

CONTRACT = os.path.join("godot", "modules", "mcp_server", "docs", "tools_list.renamed.json")
RENAME_MAP = os.path.join("godot", "modules", "mcp_server", "docs", "tool-rename-map.json")
GROUP_FILES = ["tool-groups.json", "tool-groups-b2.json", "tool-groups-b3.json",
               "tool-groups-b4.json", "tool-groups-b5.json", "tool-groups-added.json"]
GROUPS_DIR = os.path.join("godot", "modules", "mcp_server", "docs")
REVIEW_DATA = os.path.join("dist", "review_data.json")
LEDGER = os.path.join("godot", "modules", "mcp_server", "scripts", "mcp_trace_ledger.py")
REGISTRY = os.path.join("tools", "tool_coverage_unreachable.json")

# The rename map's verb closed set, split into "a payload is its evidence" and
# "a state change is its evidence". `assert` / `execute` / `evaluate` are on the
# read side because their whole result *is* the payload they answer with (an
# assertion verdict, the value an executed snippet computed) - a read never moves
# a pixel or a byte, so demanding a screen/file delta from it would report a
# working reader as ineffective.
#
# TASK-111 rule clarification: `capture` joins the read side, on the same ground.
# The four capture tools (editor_capture_screenshot, running_game_capture_screenshot,
# running_game_capture_frames, running_game_capture_signal_emissions) take a
# snapshot of a live stream and answer *with that snapshot*: frames inline as
# base64, or the emission records they observed. The handlers write no persistent
# state - `running_game_capture_screenshot` may additionally drop a file, which the
# file-effect verdict already reports when it happens. Judging them by
# `ok_effect_observed` therefore demanded a screen/file delta from a reader whose
# payload is the delta itself, which is why TASK-110 reported the two running_game
# rows as "counter met, evidence missing" with 5/5 substantive payloads each.
READ_VERBS = {"get", "read", "search", "list", "find", "analyze", "detect",
              "convert", "validate", "check", "assert", "execute", "evaluate",
              "capture"}
EFFECT_VERDICTS = {"ok_effect_observed", "ok_file_effect_observed"}
NEGATIVE_FLAGS = {"assertion_failed", "created_conflict",
                  "scenario_assertion_failed", "scenario_errors"}
BUCKETS = ("0", "1-4", ">=5")

# ---------------------------------------------------------------------------
# TASK-112 item B: the evidence tier ladder.
#
# The order is the strength order and is the only place it is written down;
# `render_md` and `coverage.json` both read it from here.
# ---------------------------------------------------------------------------
TIER_PIXEL = "pixel_effect"
TIER_FILE = "file_effect"
TIER_READBACK = "readback"
TIER_COUNT = "count_only"
TIER_NONE = "no_calls"
TIER_ORDER = (TIER_PIXEL, TIER_FILE, TIER_READBACK, TIER_COUNT, TIER_NONE)
TIER_LABEL = {
    TIER_PIXEL: "ok_effect_observed（画面/视口真的变了）",
    TIER_FILE: "ok_file_effect_observed（文件真的变了）",
    TIER_READBACK: "readback：另一次独立读调用读回佐证（witness_read）或读类工具自己的载荷（own_payload）",
    TIER_COUNT: "只有计数与边界，没有生效证据",
    TIER_NONE: "0 次调用",
}
# The declared-witness source. One directory level up from the batch files, so a
# new exercise family only has to drop its manifest next to its session.
SESSIONS_DIR = os.path.join("tools", "sessions", "_exercises")
READBACK_KIND_WITNESS = "witness_read"
READBACK_KIND_OWN = "own_payload"
# How many substantive payloads of one tool in one run are kept for the
# TASK-113 item C content check. A witness is normally the first such call; the
# cap only bounds memory on a tool read hundreds of times in one run.
PAYLOAD_KEEP = 12


def sha256_file(path):
    digest = hashlib.sha256()
    with open(path, "rb") as handle:
        for chunk in iter(lambda: handle.read(1 << 20), b""):
            digest.update(chunk)
    return digest.hexdigest().upper()


def load_json(path):
    with io.open(path, "r", encoding="utf-8") as handle:
        return json.load(handle)


def load_module(path, name):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def contract_tools(root):
    return [t["name"] for t in load_json(os.path.join(root, CONTRACT))["result"]["tools"]]


def scope_and_verb(root):
    """(scopes, verbs) joined by name, exactly as TASK-108 section 1.2 describes."""
    scopes, verbs = {}, {}
    for entry in load_json(os.path.join(root, RENAME_MAP))["tools"]:
        name = entry.get("new_name")
        if not name:
            continue
        scopes.setdefault(name, entry.get("scope"))
        verbs.setdefault(name, entry.get("verb"))
    for fname in GROUP_FILES:
        doc = load_json(os.path.join(root, GROUPS_DIR, fname))
        for group in doc.get("groups") or []:
            scope = group.get("scope")
            for name in group.get("tools") or []:
                if scope:
                    scopes.setdefault(name, scope)
    return scopes, verbs


def final_run_dirs(root):
    doc = load_json(os.path.join(root, REVIEW_DATA))
    out = []
    for game in doc.get("games") or []:
        tag = game.get("run_tag")
        name = game.get("game")
        if tag and name:
            out.append(os.path.join("runs", name, tag))
    return out


def iter_traces(root, runs_dir, only_final, excludes):
    """[(relative run dir, absolute trace path)]. Order is deterministic."""
    found = []
    if only_final:
        bases = [os.path.join(root, d) for d in final_run_dirs(root)]
    else:
        base = runs_dir if os.path.isabs(runs_dir) else os.path.join(root, runs_dir)
        bases = []
        for dirpath, _dirnames, filenames in os.walk(base):
            if any(f.startswith("trace-") and f.endswith(".jsonl") for f in filenames):
                bases.append(dirpath)
        bases.sort()
    for base_dir in bases:
        if not os.path.isdir(base_dir):
            continue
        rel = os.path.relpath(base_dir, root).replace("\\", "/")
        if any(x and x in rel for x in excludes):
            continue
        for fname in sorted(os.listdir(base_dir)):
            if fname.startswith("trace-") and fname.endswith(".jsonl"):
                found.append((rel, os.path.join(base_dir, fname)))
    return found


def substantive(raw):
    if not isinstance(raw, str) or raw.strip() == "":
        return False
    try:
        body = json.loads(raw)
    except ValueError:
        return False
    if isinstance(body, dict):
        return len(body) > 0
    if isinstance(body, list):
        return len(body) > 0
    return bool(body)


def load_readback_declarations(root):
    """Every `readback` declaration the session manifests carry.

    A declaration is one object:

        {"tool": "<the writer>", "witness_tool": "<the reader>",
         "run": "runs/_exercises/<project>/<batch>", "why": "<what is read back>",
         "expect": "<literal that must be in the witness payload>"  (TASK-113 C)
                  or ["<literal>", ...], "witness_seq": <optional>}

    The reader is only a *declaration*: `verify_readback` re-finds the witness
    call in that run's trace - and, when `expect` is given, searches that call's
    payload for the literal - before the tier is granted, so a stale or invented
    declaration cannot promote a tool.
    """
    base = os.path.join(root, SESSIONS_DIR)
    found = []
    if not os.path.isdir(base):
        return found
    for dirpath, _dirnames, filenames in os.walk(base):
        for fname in sorted(filenames):
            if not fname.endswith("-manifest.json"):
                continue
            path = os.path.join(dirpath, fname)
            try:
                doc = load_json(path)
            except (IOError, ValueError):
                continue
            for item in doc.get("readback") or []:
                if not isinstance(item, dict) or not item.get("tool") or not item.get("witness_tool"):
                    continue
                entry = dict(item)
                entry["declared_in"] = os.path.relpath(path, root).replace("\\", "/")
                found.append(entry)
    found.sort(key=lambda e: (e["tool"], e.get("run", ""), e.get("witness_tool", "")))
    return found


def expected_literals(declaration):
    """The declared `expect` as a list of literals ([] when not declared)."""
    raw = declaration.get("expect")
    if raw is None:
        return []
    if isinstance(raw, str):
        return [raw] if raw != "" else []
    if isinstance(raw, list):
        return [x for x in raw if isinstance(x, str) and x != ""]
    return []


def forbidden_literals(declaration):
    """The declared `expect_absent` as a list of literals ([] when not declared).

    A subtractive write (a removal, a clear) has no value to find in the
    read-back; what proves it is the *absence* of the thing it removed. That
    absence is only meaningful on the **same subject**, so the check requires a
    payload matched by `expect` (usually the subject anchor, e.g. the node the
    removal addressed) in which none of the `expect_absent` literals appears.
    """
    raw = declaration.get("expect_absent")
    if raw is None:
        return []
    if isinstance(raw, str):
        return [raw] if raw != "" else []
    if isinstance(raw, list):
        return [x for x in raw if isinstance(x, str) and x != ""]
    return []


def payload_variants(text):
    """Every spelling of a witness payload the literal may have to match.

    The trace stores a tool's answer in one of two shapes depending on the
    reader that wrote it: the answer itself, or the JSON-RPC envelope with the
    answer escaped inside `content[0].text`. Both are the same bytes the engine
    answered with, so the content check searches the payload *and* its unescaped
    / unwrapped spellings instead of depending on the trace's shape.
    """
    variants = [text]
    unescaped = text.replace('\\"', '"').replace("\\n", "\n").replace("\\\\", "\\")
    if unescaped != text:
        variants.append(unescaped)
    stripped = text.strip()
    if stripped.startswith("{"):
        try:
            body = json.loads(stripped)
        except ValueError:
            body = None
        if isinstance(body, dict):
            content = body.get("content")
            if isinstance(content, list):
                for item in content:
                    if isinstance(item, dict) and isinstance(item.get("text"), str):
                        variants.append(item["text"])
    return variants


def expect_matches(literals, text):
    """True when every literal appears verbatim in one spelling of the payload."""
    if text is None:
        return False
    for variant in payload_variants(text):
        if all(literal in variant for literal in literals):
            return True
    return False


def expect_forbids(forbidden, text):
    """True when none of the forbidden literals appears in any spelling."""
    if text is None:
        return False
    for variant in payload_variants(text):
        if any(literal in variant for literal in forbidden):
            return False
    return True


def witness_payload_text(payload):
    """The witness call's own answer as text: inline, or the verified sidecar.

    A payload larger than the trace's inline budget is not on the call line; the
    ledger has already re-hashed and re-measured its sidecar, so reading that
    file is reading the same bytes the engine answered with.
    """
    if payload.get("sidecar_path"):
        try:
            with io.open(payload["sidecar_path"], "r", encoding="utf-8", errors="replace") as handle:
                return handle.read()
        except IOError:
            return None
    text = payload.get("text")
    return text if isinstance(text, str) else None


def verify_readback(declaration, run_index):
    """(verified pointer, rejection reason). Pointer is None when not confirmed.

    A witness counts only if, inside the declared run, a call of the declared
    reader tool exists, answered `ok=true`, and carried a substantive payload
    (or a verified sidecar - the TASK-111 rule). TASK-113 item C: when the
    declaration carries `expect`, the payload of one such call must contain
    every declared literal verbatim; the call that matched is the one reported.
    """
    run = declaration.get("run")
    witness = declaration.get("witness_tool")
    if not run or not witness:
        return None, "the declaration names no run/witness_tool"
    per_tool = run_index.get(run)
    if not per_tool:
        return None, "the declared run is not in the corpus"
    st = per_tool.get(witness)
    if not st or st["ok"] < 1 or st["substantive"] < 1:
        return None, "no `ok=true` substantive call of `%s` in that run" % witness

    expects = expected_literals(declaration)
    forbids = forbidden_literals(declaration)
    if not expects and not forbids:
        # TASK-113 item C: the witness has to be checkable at the content level.
        # A declaration that names no literal at all stays at the call level and
        # is therefore NOT granted a tier any more - that is the whole point of
        # the upgrade, and the rejection reason says so.
        return None, ("no content-level `expect`/`expect_absent` declared: the witness would only "
                      "prove that a read call happened (TASK-113 item C requires the written value, "
                      "or the removal it addresses, to be readable back)")
    chosen = None
    for payload in st["payloads"]:
        text = witness_payload_text(payload)
        if not expect_matches(expects, text):
            continue
        if forbids and not expect_forbids(forbids, text):
            continue
        chosen = {"seq": payload["seq"], "matched": expects}
        break
    if chosen is None:
        return None, ("none of the %d substantive `%s` payload(s) satisfies expect %s%s"
                      % (len(st["payloads"]), witness,
                         " and ".join("'%s'" % x for x in expects) or "(none)",
                         (" and expect_absent " + " and ".join("'%s'" % x for x in forbids))
                         if forbids else ""))
    pointer = {
        "witness_tool": witness,
        "run": run,
        "witness_seq": chosen["seq"],
        "why": declaration.get("why", ""),
        "declared_in": declaration.get("declared_in", ""),
        "expect": expects,
        "expect_absent": forbids,
        "expect_matched": True,
    }
    return pointer, None



def verb_of(name, verbs):
    """The contract's verb for one tool.

    The six `_meta.added_tools` have no entry in the rename map, so their verb is
    the name's own second segment (`project_read_text_file` -> `read`); without
    this fallback every added tool would be judged as if it were a writer and a
    working reader would be reported ineffective.
    """
    verb = verbs.get(name)
    if verb:
        return verb
    parts = name.split("_")
    return parts[1] if len(parts) > 1 else None


def classify(row, verb):
    """(effective, boundary) for one ledger row.

    TASK-111 fix: a read verb's payload is its evidence, and for a body larger
    than the trace's inline budget the payload is *not* on the call line - the
    line carries its first 4096 bytes plus `result_json_truncated: true` and a
    sidecar entry (`result_json_sidecar` + sha256) that `mcp_trace_ledger.build`
    has already found, re-hashed and re-measured (`result_json_evidence ==
    "sidecar_verified"`). Parsing the truncated inline copy can only ever fail,
    so `editor_get_tilemap_used_cells` (6 591 B) was reported
    `result_unparseable` / ineffective although its complete answer was on disk
    the whole time. A verified sidecar means the body exists and is larger than
    the inline budget, i.e. it is non-empty by construction.
    """
    if not row["ok"]:
        return False, True
    flags = set(row.get("result_flags") or [])
    if flags & NEGATIVE_FLAGS:
        return False, False
    if row["verdict"] in EFFECT_VERDICTS:
        return True, False
    if verb in READ_VERBS and (row.get("result_json_evidence") == "sidecar_verified"
                               or substantive(row.get("result_json"))):
        return True, False
    return False, False


def build_rows(root, ledger, traces, verbs, scopes):
    stats = {}
    # TASK-112 item B: `{run: {tool: {ok, substantive, first_substantive_seq}}}`,
    # the index a readback declaration is verified against. It is built from the
    # same rows the rest of the ledger uses, so a declaration can never be
    # "verified" by a call the ledger does not have.
    run_index = {}
    corpus = {"trace_files": 0, "run_dirs": 0, "calls": 0, "malformed_lines": 0,
              "ok": 0, "failed": 0, "distinct_tools": 0, "sidecars_verified": 0}
    seen_dirs = set()
    for rel, path in traces:
        records, broken = ledger.load(path)
        rows = ledger.build(records, path)
        corpus["trace_files"] += 1
        corpus["malformed_lines"] += broken
        if rel not in seen_dirs:
            seen_dirs.add(rel)
            corpus["run_dirs"] += 1
        run_tools = run_index.setdefault(rel, {})
        for row in rows:
            name = row.get("tool")
            if not name:
                continue
            corpus["calls"] += 1
            corpus["ok"] += 1 if row["ok"] else 0
            corpus["failed"] += 0 if row["ok"] else 1
            if row.get("args_evidence") == "sidecar_verified" or \
               row.get("result_json_evidence") == "sidecar_verified":
                corpus["sidecars_verified"] += 1
            substantive_payload = (row.get("result_json_evidence") == "sidecar_verified"
                                   or substantive(row.get("result_json")))
            rt = run_tools.setdefault(name, {"ok": 0, "substantive": 0,
                                             "first_substantive_seq": None,
                                             "payloads": []})
            if row["ok"]:
                rt["ok"] += 1
            if row["ok"] and substantive_payload:
                rt["substantive"] += 1
                if rt["first_substantive_seq"] is None:
                    rt["first_substantive_seq"] = row.get("call_id")
                # TASK-113 item C: the payload itself, so a declared `expect`
                # can be matched against the engine's own answer instead of
                # against the mere fact that the call happened.
                if len(rt["payloads"]) < PAYLOAD_KEEP:
                    sidecar = (row.get("result_json_sidecar_detail") or {}).get("resolved_path")
                    if row.get("result_json_evidence") != "sidecar_verified":
                        sidecar = None
                    rt["payloads"].append({"seq": row.get("call_id"),
                                           "text": row.get("result_json"),
                                           "sidecar_path": sidecar})
            st = stats.setdefault(name, {
                "tool": name, "calls": 0, "ok": 0, "failed": 0, "effective": 0,
                "verdicts": {}, "file_effects": {}, "runs": {}, "first_ts": None,
                "last_ts": None, "truncated_args": 0, "flags": {}, "facts_complete": 0,
                "pixel_effect": 0, "file_effect": 0, "read_payload": 0})
            st["calls"] += 1
            st["ok"] += 1 if row["ok"] else 0
            st["failed"] += 0 if row["ok"] else 1
            st["verdicts"][row["verdict"]] = st["verdicts"].get(row["verdict"], 0) + 1
            st["file_effects"][row["file_effect"]] = st["file_effects"].get(row["file_effect"], 0) + 1
            st["runs"][rel] = st["runs"].get(rel, 0) + 1
            if row.get("facts_complete"):
                st["facts_complete"] += 1
            if row.get("args_truncated"):
                st["truncated_args"] += 1
            for flag in row.get("result_flags") or []:
                st["flags"][flag] = st["flags"].get(flag, 0) + 1
            for flag in row.get("error_flags") or []:
                st["flags"][flag] = st["flags"].get(flag, 0) + 1
            eff, bnd = classify(row, verb_of(name, verbs))
            st["effective"] += 1 if eff else 0
            # TASK-112 item B: the tier a tool ends up on is read off the same
            # verdicts `classify` uses, so the two can never disagree.
            if row["ok"] and row["verdict"] == "ok_effect_observed":
                st["pixel_effect"] += 1
            if row["ok"] and row["verdict"] == "ok_file_effect_observed":
                st["file_effect"] += 1
            if eff and verb_of(name, verbs) in READ_VERBS:
                st["read_payload"] += 1
            ts = row.get("ended_ts_ms")
            if isinstance(ts, (int, float)):
                if st["first_ts"] is None or ts < st["first_ts"]:
                    st["first_ts"] = ts
                if st["last_ts"] is None or ts > st["last_ts"]:
                    st["last_ts"] = ts
    corpus["distinct_tools"] = len(stats)
    return stats, corpus, run_index


def evidence_tier(st, verb, readback):
    """The strongest evidence this tool's calls carry (TASK-112 item B).

    `readback` is the verified witness pointer (write tools) - a READ-verb tool
    is `own_payload` on the same ladder rung, because its answer *is* the
    measurement and none of its callers could wait for a second call.
    """
    if st is None or st["calls"] < 1:
        return TIER_NONE, None
    if st.get("pixel_effect"):
        return TIER_PIXEL, None
    if st.get("file_effect"):
        return TIER_FILE, None
    if verb in READ_VERBS and st.get("read_payload"):
        return TIER_READBACK, {"kind": READBACK_KIND_OWN, "witness_tool": None,
                               "run": None, "witness_seq": None,
                               "why": "读类动词：回包本身即测量结果（TASK-111 的 READ_VERBS 规则），"
                                      "不存在「另一次读调用」可等",
                               "declared_in": None}
    if readback:
        entry = dict(readback)
        entry["kind"] = READBACK_KIND_WITNESS
        return TIER_READBACK, entry
    return TIER_COUNT, None


def status_of(st, registry_members):
    if st is None:
        calls = 0
        eff = 0
        bnd = 0
    else:
        calls, eff, bnd = st["calls"], st["effective"], st["failed"]
    if calls >= 5 and eff >= 1 and bnd >= 1:
        return "达标"
    if calls >= 5:
        return "计数达标缺证据"
    if calls >= 1:
        return "未达(1-4)"
    return "未达(0)"


def bucket_of(calls):
    if calls >= 5:
        return ">=5"
    if calls >= 1:
        return "1-4"
    return "0"


def build_payload(args):
    root = os.path.abspath(args.root)
    contract_path = os.path.join(root, CONTRACT)
    names = contract_tools(root)
    scopes, verbs = scope_and_verb(root)
    ledger = load_module(os.path.join(root, LEDGER), "mcp_trace_ledger")
    traces = iter_traces(root, args.runs, args.only_final, args.exclude or [])
    stats, corpus, run_index = build_rows(root, ledger, traces, verbs, scopes)

    # TASK-112 item B: every declared readback witness is re-verified against the
    # run's own rows; an unverifiable declaration is reported as rejected instead
    # of silently granting a tier. TASK-113 item C: a declaration that carries
    # `expect` is only verified when the witness payload really contains it.
    declarations = load_readback_declarations(root)
    verified_readback = {}
    readback_rejected = []
    content_checked = 0
    for declaration in declarations:
        pointer, reason = verify_readback(declaration, run_index)
        if pointer is None:
            rejected = dict(declaration)
            rejected["reason"] = reason
            readback_rejected.append(rejected)
            continue
        if pointer.get("expect_matched"):
            content_checked += 1
        # The strongest (first) verified witness of a tool wins.
        verified_readback.setdefault(declaration["tool"], pointer)

    registry = {"categories": {}, "members": [], "reclassified": []}
    reg_path = os.path.join(root, REGISTRY)
    if os.path.isfile(reg_path):
        registry = load_json(reg_path)
    # A tool the register once called unreachable but the corpus has since called
    # for real is NOT unreachable; the register keeps the entry for audit and this
    # reader takes it out of the set it reports.
    reclassified = {r["tool"]: r for r in registry.get("reclassified") or []}
    reg_members = {m["tool"]: m["category"] for m in registry.get("members") or []
                   if m["tool"] not in reclassified}

    tools = []
    for name in names:
        st = stats.get(name)
        calls = st["calls"] if st else 0
        eff = st["effective"] if st else 0
        bnd = st["failed"] if st else 0
        runs = sorted((st["runs"] if st else {}).items(), key=lambda kv: (-kv[1], kv[0]))
        tier, readback = evidence_tier(st, verb_of(name, verbs), verified_readback.get(name))
        row = {
            "tool": name,
            "scope": scopes.get(name),
            "verb": verb_of(name, verbs),
            "calls": calls,
            "ok": st["ok"] if st else 0,
            "boundary": bnd,
            "effective": eff,
            "evidence_tier": tier,
            "evidence_tier_label": TIER_LABEL[tier],
            "readback": readback,
            "pixel_effect_calls": st["pixel_effect"] if st else 0,
            "file_effect_calls": st["file_effect"] if st else 0,
            "read_payload_calls": st["read_payload"] if st else 0,
            "facts_complete": st["facts_complete"] if st else 0,
            "bucket": bucket_of(calls),
            "status": status_of(st, reg_members),
            "unreachable_category": reg_members.get(name),
            "verdicts": st["verdicts"] if st else {},
            "file_effects": st["file_effects"] if st else {},
            "flags": st["flags"] if st else {},
            "evidence": [{"run": r, "calls": c} for r, c in runs[:5]],
            "first_ts_ms": st["first_ts"] if st else None,
            "last_ts_ms": st["last_ts"] if st else None,
        }
        row["gate"] = bool(calls >= 5 and eff >= 1 and bnd >= 1)
        tools.append(row)

    by_status = {}
    by_bucket = {}
    by_scope = {}
    by_tier = {}
    for row in tools:
        by_status[row["status"]] = by_status.get(row["status"], 0) + 1
        by_bucket[row["bucket"]] = by_bucket.get(row["bucket"], 0) + 1
        by_tier[row["evidence_tier"]] = by_tier.get(row["evidence_tier"], 0) + 1
        key = row["scope"] or "?"
        slot = by_scope.setdefault(key, {"tools": 0, "called": 0, ">=5": 0, "0": 0})
        slot["tools"] += 1
        slot["called"] += 1 if row["calls"] else 0
        slot["0"] += 1 if row["calls"] == 0 else 0
        slot["..."] = None
        if row["bucket"] == ">=5":
            slot[">=5"] += 1
    for key in by_scope:
        by_scope[key].pop("...", None)

    registry_view = []
    for item in registry.get("members") or []:
        st = stats.get(item["tool"])
        calls = st["calls"] if st else 0
        gone = item["tool"] in reclassified
        registry_view.append({
            "tool": item["tool"], "scope": item["scope"], "category": item["category"],
            "measured_calls": calls,
            "drift": calls > 0,
            "reclassified": gone,
            "evidence": sorted((st["runs"] if st else {}).items(), key=lambda kv: (-kv[1], kv[0]))[:3],
        })

    targets = None
    if args.targets:
        with io.open(args.targets, "r", encoding="utf-8") as handle:
            targets = [ln.strip() for ln in handle
                       if ln.strip() and not ln.strip().startswith("#")]

    fingerprints = {}
    for rel in (CONTRACT, RENAME_MAP, REVIEW_DATA):
        p = os.path.join(root, rel)
        if os.path.isfile(p):
            fingerprints[rel] = {"bytes": os.path.getsize(p), "sha256": sha256_file(p)}

    return {
        "generated_utc": datetime.datetime.now(datetime.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "mode": "only-final" if args.only_final else "all-runs",
        "root": root,
        "runs_dir": args.runs,
        "excludes": args.exclude or [],
        "corpus": corpus,
        "fingerprints": fingerprints,
        "buckets": by_bucket,
        "status_counts": by_status,
        "evidence_tier_counts": by_tier,
        "evidence_tier_order": list(TIER_ORDER),
        "readback_declarations": {
            "declared": len(declarations),
            "verified": len(verified_readback),
            "rejected": readback_rejected,
            "content_checked": content_checked,
            "declared_with_expect": len([d for d in declarations
                                         if expected_literals(d) or forbidden_literals(d)]),
            "verified_by_tool": verified_readback,
        },
        "scope_counts": by_scope,
        "targets": targets,
        "targets_view": [r for r in tools if targets and r["tool"] in set(targets)],
        "tools": tools,
        "unreachable_registry": {
            "source": registry.get("_source_report"),
            "section": registry.get("_source_section"),
            "categories": registry.get("categories") or {},
            "members_total": len(registry_view),
            "drift": [r for r in registry_view if r["drift"]],
            "reclassified": registry.get("reclassified") or [],
            "members": registry_view,
        },
    }


def md_evidence(row, limit=2):
    parts = ["%s(%d)" % (e["run"], e["calls"]) for e in row["evidence"][:limit]]
    return " ; ".join(parts) if parts else "-"


def md_tier_evidence(row):
    """The one-line reason for the tool's evidence tier."""
    tier = row.get("evidence_tier")
    if tier == TIER_PIXEL:
        return "ok_effect_observed ×%d" % row.get("pixel_effect_calls", 0)
    if tier == TIER_FILE:
        return "ok_file_effect_observed ×%d" % row.get("file_effect_calls", 0)
    if tier == TIER_READBACK:
        entry = row.get("readback") or {}
        if entry.get("kind") == READBACK_KIND_OWN:
            return "own_payload ×%d（读类回包即证据）" % row.get("read_payload_calls", 0)
        return "witness `%s`@%s seq=%s" % (entry.get("witness_tool"), entry.get("run"),
                                           entry.get("witness_seq"))
    return "-"


def render_md(payload, title, cmdline):
    lines = []
    corpus = payload["corpus"]
    buckets = payload["buckets"]
    status = payload["status_counts"]
    total = len(payload["tools"])
    lines.append("# %s" % title)
    lines.append("")
    lines.append("> 本文件由 `%s` 自动生成，**随时可重跑刷新**。命令行：" % os.path.basename(__file__))
    lines.append("> `%s`" % cmdline)
    lines.append("")
    lines.append("口径（mode）：**%s**；语料：**%d 个 run 目录 / %d 个 trace 文件 / %d 次 "
                 "`tools/call`**（`ok=false` %d 次、解析失败行 %d、sidecar 校验通过 %d）"
                 % (payload["mode"], corpus["run_dirs"], corpus["trace_files"], corpus["calls"],
                    corpus["failed"], corpus["malformed_lines"], corpus["sidecars_verified"]))
    if payload["excludes"]:
        lines.append("；已剔除路径片段：%s" % ", ".join("`%s`" % x for x in payload["excludes"]))
    lines.append("")
    lines.append("生成时间（UTC）：%s" % payload["generated_utc"])
    lines.append("")
    lines.append("**「有效调用」的判定**（由 `mcp_trace_ledger.py` 的 verdict 词汇给出，不另立一套）：")
    lines.append("")
    lines.append("- `边界调用` = 该工具 `ok=false` 的调用次数（失败/拒绝即边界证据）。")
    lines.append("- `有效调用`：**读类动词**（get/read/search/list/find/analyze/detect/convert/validate/check/"
                 "assert/execute/evaluate，后三个的生效证据就是它回包的那个值或判词）"
                 "= `ok=true` 且回包是实质载荷（读类调用不会动像素/字节，回包本身就是证据）；")
    lines.append("  **其余动词**（create/edit/set/add/remove/write/build…）= ledger 的 `ok_effect_observed` / "
                 "`ok_file_effect_observed`，即真的改了画面或文件。"
                 "带 `assertion_failed` / `created_conflict` / `scenario_errors` 的 ok 调用不计有效。")
    lines.append("- `状态`：`达标` = 调用≥5 且 有效≥1 且 边界≥1；`计数达标缺证据` = 调用≥5 但缺有效或边界；"
                 "`未达(1-4)` / `未达(0)`；`不可达` 不在本表状态里，见 §4 登记表。")
    lines.append("")
    lines.append("**「证据档位」的判定**（TASK-112 B；档位由强到弱，一个工具只落一档）：")
    lines.append("")
    lines.append("| 档位 | 判据 | 工具数 |")
    lines.append("|---|---|---|")
    tier_counts = payload.get("evidence_tier_counts", {})
    for tier in payload.get("evidence_tier_order", TIER_ORDER):
        lines.append("| `%s` | %s | %d |" % (tier, TIER_LABEL[tier], tier_counts.get(tier, 0)))
    lines.append("")
    lines.append("- `readback` 有两种 **互不混同** 的 kind：`witness_read`（写类工具，效果由**另一次独立的读调用**"
                 "在同一 run 内读回佐证）与 `own_payload`（读类动词，回包本身即测量结果，不存在可等的第二次调用）。")
    lines.append("- `witness_read` **不是推断**：配对写在会话 manifest 的 `readback` 数组里，"
                 "本工具会回到该 run 的 trace 里把见证调用**再找一次**（必须 `ok=true` 且回包是实质载荷），"
                 "找不到就不给档位（见 §0.1 的 rejected 列表）。")
    lines.append("- **内容级复核（TASK-113 C）**：声明可带 `expect`（一个或一组字面量），"
                 "本工具在**见证调用的回包**里逐字搜它（回包被 trace 截断时读已核验的 sidecar）；"
                 "搜不到就**不给档位**并记入 rejected，理由逐条写出。"
                 "所以 `witness_read` 现在证明的是「写进去的值能从引擎自己的回答里读回来」，"
                 "不再只是「那一次读调用发生过」。")
    lines.append("- **不得**把「写工具自己响应里说成功了」当作 readback：那条路径只能落在 `count_only`。")
    lines.append("")
    lines.append("### 0.1 readback 声明与见证（TASK-112 B；内容级 `expect` 复核见 TASK-113 C）")
    lines.append("")
    rb = payload.get("readback_declarations") or {}
    lines.append("声明 **%d** 条（来源：`%s/**/*-manifest.json` 的 `readback` 数组）；"
                 "**经 trace 复核通过 %d 条**，被拒 %d 条；其中带 `expect` 的声明 **%d** 条、"
                 "**逐字命中 %d** 条。"
                 % (rb.get("declared", 0), SESSIONS_DIR.replace("\\", "/"),
                    rb.get("verified", 0), len(rb.get("rejected") or []),
                    rb.get("declared_with_expect", 0), rb.get("content_checked", 0)))
    lines.append("")
    own = [r for r in payload["tools"]
           if r.get("readback") and r["readback"].get("kind") == READBACK_KIND_OWN]
    lines.append("下表只列 `kind = witness_read` 的档位（**有**独立读调用可以点名的那一类，共 %d 条）；"
                 "另外 %d 条是 `own_payload`（读类动词，回包即证据、没有第二次调用可点名），"
                 "它们逐条列在 §0.2。" % (rb.get("verified", 0), len(own)))
    lines.append("")
    lines.append("| 写工具 | kind | 见证读调用 | run | 见证 seq | 内容级 `expect`（逐字） | `expect_absent` | 读回的是什么 |")
    lines.append("|---|---|---|---|---|---|---|---|")
    for row in payload["tools"]:
        entry = row.get("readback")
        if not entry or entry.get("kind") != READBACK_KIND_WITNESS:
            continue
        expect = entry.get("expect") or []
        absent = entry.get("expect_absent") or []
        expect_text = " ; ".join("`%s`" % x.replace("`", "'") for x in expect) if expect else "（未声明）"
        absent_text = " ; ".join("`%s`" % x.replace("`", "'") for x in absent) if absent else "-"
        lines.append("| `%s` | `%s` | `%s` | %s | %s | %s | %s | %s |"
                     % (row["tool"], entry.get("kind", ""),
                        entry["witness_tool"] if entry.get("witness_tool") else "-",
                        entry.get("run") or "-",
                        entry.get("witness_seq") if entry.get("witness_seq") is not None else "-",
                        expect_text, absent_text,
                        entry.get("why") or "-"))
    lines.append("")
    if rb.get("rejected"):
        lines.append("**被拒的声明（找不到合格的见证调用，或内容级 `expect` 未命中；档位不授予）**：")
        lines.append("")
        for item in rb["rejected"]:
            lines.append("- `%s` <- `%s` @ `%s`（声明于 `%s`）：%s"
                         % (item.get("tool"), item.get("witness_tool"), item.get("run"),
                            item.get("declared_in"), item.get("reason") or "无理由字段"))
        lines.append("")
    lines.append("### 0.2 逐档工具清单（TASK-112 B）")
    lines.append("")
    for tier in payload.get("evidence_tier_order", TIER_ORDER):
        rows = [r for r in payload["tools"] if r["evidence_tier"] == tier]
        lines.append("- **`%s`**（%d）：%s"
                     % (tier, len(rows),
                        " ".join("`%s`" % r["tool"] for r in rows) if rows else "（无）"))
    lines.append("")
    lines.append("## 0. 分桶与状态")
    lines.append("")
    lines.append("| 桶 | 工具数 |")
    lines.append("|---|---|")
    for key in BUCKETS:
        lines.append("| `%s` 次 | %d |" % (key, buckets.get(key, 0)))
    lines.append("| **合计** | **%d** |" % total)
    lines.append("")
    lines.append("| 状态 | 工具数 |")
    lines.append("|---|---|")
    for key in ("达标", "计数达标缺证据", "未达(1-4)", "未达(0)"):
        lines.append("| %s | %d |" % (key, status.get(key, 0)))
    lines.append("")
    lines.append("| scope | 契约条数 | 被调用过 | 0 次 | ≥5 次 |")
    lines.append("|---|---|---|---|---|")
    for key in sorted(payload["scope_counts"]):
        s = payload["scope_counts"][key]
        lines.append("| %s | %d | %d | %d | %d |" % (key, s["tools"], s["called"], s["0"], s[">=5"]))
    lines.append("")
    lines.append("## 1. 总表（177 条契约工具，逐条一行）")
    lines.append("")
    lines.append("| # | tool | scope | verb | 累计调用 | 有效调用 | 边界调用 | 证据档位 | 档位证据 | 证据路径 | 状态 |")
    lines.append("|---|---|---|---|---|---|---|---|---|---|---|")
    for i, row in enumerate(payload["tools"], 1):
        lines.append("| %d | `%s` | %s | %s | %d | %d | %d | `%s` | %s | %s | %s |"
                     % (i, row["tool"], row["scope"] or "?", row["verb"] or "?", row["calls"],
                        row["effective"], row["boundary"], row["evidence_tier"],
                        md_tier_evidence(row), md_evidence(row), row["status"]))
    lines.append("")
    lines.append("## 2. 分桶明细")
    lines.append("")
    for index, key in enumerate((">=5", "1-4", "0"), 1):
        rows = [r for r in payload["tools"] if r["bucket"] == key]
        lines.append("### 2.%d `%s` 次（%d 条）" % (index, key, len(rows)))
        if key == "0":
            lines.append("")
            lines.append("（按前缀分组，均为 0 次；其中登记为「不可达」的见 §4）")
            lines.append("")
            grouped = {}
            for r in rows:
                grouped.setdefault(r["tool"].split("_")[0], []).append(r["tool"])
            for prefix in sorted(grouped):
                lines.append("- **%s_**（%d）：%s" % (prefix, len(grouped[prefix]),
                                                     " ".join("`%s`" % x for x in grouped[prefix])))
        else:
            lines.append("")
            lines.append("| tool | scope | 累计 | 有效 | 边界 | 档位 | 状态 | 证据 |")
            lines.append("|---|---|---|---|---|---|---|---|")
            for r in rows:
                lines.append("| `%s` | %s | %d | %d | %d | `%s` | %s | %s |"
                             % (r["tool"], r["scope"], r["calls"], r["effective"], r["boundary"],
                                r["evidence_tier"], r["status"], md_evidence(r, 3)))
        lines.append("")
    lines.append("## 3. `<5` 清单（本轮仍未达标的工具）")
    lines.append("")
    under = [r for r in payload["tools"] if r["calls"] < 5]
    lines.append("共 **%d** 条（占契约 %.1f%%）：`0` 次 %d 条、`1-4` 次 %d 条。"
                 % (len(under), 100.0 * len(under) / max(total, 1),
                    buckets.get("0", 0), buckets.get("1-4", 0)))
    lines.append("")
    lines.append("| tool | scope | verb | 累计 | 有效 | 边界 | 档位 | 登记不可达 | 状态 |")
    lines.append("|---|---|---|---|---|---|---|---|---|")
    for r in under:
        lines.append("| `%s` | %s | %s | %d | %d | %d | `%s` | %s | %s |"
                     % (r["tool"], r["scope"] or "?", r["verb"] or "?", r["calls"],
                        r["effective"], r["boundary"], r["evidence_tier"],
                        r["unreachable_category"] or "-", r["status"]))
    lines.append("")
    lines.append("## 4. 不可达登记表的联动视图（H1–H9）")
    lines.append("")
    reg = payload["unreachable_registry"]
    lines.append("登记来源：`%s` §%s（**推断**，判据是「缺少本循环不具备的子系统/资产/前置运行态」）。"
                 "本视图把登记表与本轮实测**对在一起**：`实测调用` 列不为 0 的条目就是登记漂移，"
                 "必须在下一轮从登记表里移除或改判。" % (reg.get("source"), reg.get("section")))
    lines.append("")
    lines.append("登记成员 **%d** 条；其中实测**已被调用**（登记漂移）**%d** 条，其中 **%d** 条已按实测证据"
                 "改判并记入登记表的 `reclassified`（下表 `改判` 列打 `YES`），其余为待复核漂移。"
                 % (reg.get("members_total", 0), len(reg.get("drift") or []),
                    len([r for r in (reg.get("drift") or []) if r.get("reclassified")])))
    lines.append("")
    for code in sorted(reg.get("categories") or {}):
        cat = reg["categories"][code]
        lines.append("### %s %s" % (code, cat.get("label", "")))
        lines.append("")
        lines.append("- 为何不可达（推断）：%s" % cat.get("why_unreachable", ""))
        lines.append("- 支撑证据（只读观察）：%s" % cat.get("supporting_evidence", ""))
        lines.append("")
        lines.append("| tool | scope | 实测调用 | 漂移 | 改判 | 证据 |")
        lines.append("|---|---|---|---|---|---|")
        for item in reg["members"]:
            if item["category"] != code:
                continue
            ev = " ; ".join("%s(%d)" % (r, c) for r, c in item["evidence"]) or "-"
            lines.append("| `%s` | %s | %d | %s | %s | %s |"
                         % (item["tool"], item["scope"], item["measured_calls"],
                            "**YES**" if item["drift"] else "-",
                            "YES" if item.get("reclassified") else "-", ev))
        lines.append("")
    if reg.get("reclassified"):
        lines.append("")
        lines.append("#### 已改判的条目（推断被实测推翻，逐条留证）")
        lines.append("")
        lines.append("| tool | 原类别 | 为什么可以删掉这条「不可达」 | 证据 |")
        lines.append("|---|---|---|---|")
        for item in reg["reclassified"]:
            lines.append("| `%s` | %s | %s | `%s` |"
                         % (item["tool"], item["from"], item.get("why", ""), item.get("evidence", "")))
        lines.append("")
    tv = payload.get("targets_view")
    if tv is not None:
        lines.append("## 5. 本轮批次进度（--targets）")
        lines.append("")
        done = [r for r in tv if r["gate"]]
        lines.append("批次 **%d** 条：达标 **%d**、计数达标缺证据 **%d**、未达 **%d**。"
                     % (len(tv), len(done),
                        len([r for r in tv if r["calls"] >= 5 and not r["gate"]]),
                        len([r for r in tv if r["calls"] < 5])))
        lines.append("")
        lines.append("`facts` 列 = trace 里字段齐备的调用数 / 总调用数（request_id、tool、args、"
                     "times、result、capture、scene_evidence、file_effect、error_data 全部在场）。")
        lines.append("")
        lines.append("| tool | scope | 累计 | 有效 | 边界 | facts | 状态 | 证据 |")
        lines.append("|---|---|---|---|---|---|---|---|")
        for r in sorted(tv, key=lambda x: (x["calls"], x["tool"])):
            lines.append("| `%s` | %s | %d | %d | %d | %d/%d | %s | %s |"
                         % (r["tool"], r["scope"], r["calls"], r["effective"], r["boundary"],
                            r.get("facts_complete", 0), r["calls"], r["status"], md_evidence(r, 3)))
        lines.append("")
    lines.append("## 输入指纹")
    lines.append("")
    lines.append("| 文件 | 字节 | sha256 |")
    lines.append("|---|---|---|")
    for rel in sorted(payload["fingerprints"]):
        fp = payload["fingerprints"][rel]
        lines.append("| `%s` | %d | `%s` |" % (rel, fp["bytes"], fp["sha256"]))
    lines.append("")
    return "\n".join(lines) + "\n"


def main(argv=None):
    parser = argparse.ArgumentParser(description="Refreshable tool-coverage ledger.")
    parser.add_argument("--root", default=ROOT)
    parser.add_argument("--runs", default="runs")
    parser.add_argument("--only-final", action="store_true",
                        help="measure dist/review_data.json's 20 final tags only")
    parser.add_argument("--exclude", action="append", default=[],
                        help="run-path substring to exclude (repeatable)")
    parser.add_argument("--targets", default=None,
                        help="a file with one tool name per line: adds the batch-progress view")
    parser.add_argument("--md", default=None)
    parser.add_argument("--json", default=None)
    args = parser.parse_args(argv)

    root = os.path.abspath(args.root)
    for rel in (CONTRACT, RENAME_MAP, LEDGER):
        if not os.path.isfile(os.path.join(root, rel)):
            sys.stderr.write("tool_coverage: missing %s\n" % os.path.join(root, rel))
            return 2
    if args.only_final and not os.path.isfile(os.path.join(root, REVIEW_DATA)):
        sys.stderr.write("tool_coverage: --only-final needs %s\n" % REVIEW_DATA)
        return 2

    try:
        payload = build_payload(args)
    except (IOError, ValueError) as exc:
        sys.stderr.write("tool_coverage: %s\n" % exc)
        return 2

    md_path = args.md or os.path.join(root, "TOOL-COVERAGE.md")
    json_path = args.json or os.path.join(root, "coverage.json")
    if args.only_final:
        md_path = os.path.join(root, "TOOL-COVERAGE-final20.md")
        json_path = os.path.join(root, "coverage-final20.json")

    title = "TOOL-COVERAGE — 契约工具覆盖台账（%s）" % payload["mode"]
    argv_used = ["python", "tools/tool_coverage.py"]
    if args.only_final:
        argv_used.append("--only-final")
    if args.runs != "runs":
        argv_used += ["--runs", args.runs]
    for x in args.exclude:
        argv_used += ["--exclude", x]
    if args.targets:
        argv_used += ["--targets", args.targets]
    cmdline = " ".join(argv_used)

    with io.open(md_path, "w", encoding="utf-8", newline="\n") as handle:
        handle.write(render_md(payload, title, cmdline))
    with io.open(json_path, "w", encoding="utf-8", newline="\n") as handle:
        handle.write(json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=False) + "\n")

    b = payload["buckets"]
    s = payload["status_counts"]
    print("tool_coverage: mode=%s runs=%d trace_files=%d calls=%d distinct=%d"
          % (payload["mode"], payload["corpus"]["run_dirs"], payload["corpus"]["trace_files"],
             payload["corpus"]["calls"], payload["corpus"]["distinct_tools"]))
    print("  buckets: 0=%d 1-4=%d >=5=%d | status: 达标=%d 缺证据=%d 未达1-4=%d 未达0=%d"
          % (b.get("0", 0), b.get("1-4", 0), b.get(">=5", 0),
             s.get("达标", 0), s.get("计数达标缺证据", 0), s.get("未达(1-4)", 0), s.get("未达(0)", 0)))
    print("  registry: %d members, %d drift" % (payload["unreachable_registry"]["members_total"],
                                                len(payload["unreachable_registry"]["drift"])))
    print("  wrote %s\n  wrote %s" % (md_path, json_path))
    return 0


if __name__ == "__main__":
    sys.exit(main())
