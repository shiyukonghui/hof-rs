#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""TASK-143 analyzer: derive per-case input/output/negative annotations mechanically.

Reads inventory.json, writes analysis.json (Python file handle, no shell redirect).

The annotations are KEYWORD-DERIVED from the case body / tool contract and every
annotation carries the line number that produced it, so a reader can audit the
classification instead of trusting it. The keyword tables are declared in
NEGATIVE_KEYS / OUTPUT_KEYS / BOUNDARY_KEYS below.
"""
import io
import json
import os
import re
import sys

HERE = os.path.dirname(os.path.abspath(__file__))

NEGATIVE_KEYS = (
    "-32602", "-32601", "-32700", "-32001", "-32000",
    "expect_invalid", "invalid_params", "Missing required parameter",
    "must be a", "must not", "refuse", "reject", "is_error()",
    "never reports", "never writes", "never corrupt", "ERROR",
)
BOUNDARY_KEYS = (
    "empty", "zero", "cap", "limit", "over the", "too large", "oversized",
    "missing", "absent", "no_scene", "boundary", "edge", "max", "min",
)
OUT_SUCCESS_KEYS = (
    "CHECK(", "has(", ".get(", "result", "payload", "content[0]",
)
OUT_ERROR_KEYS = (
    "error.code", "error.message", "error.data", "message ==", "message.contains",
)
OUT_READBACK_KEYS = (
    "read back", "readback", "read_back", "get_", "reported", "reports",
)
OUT_EFFECT_KEYS = (
    "FileAccess", "file_exists", "DirAccess", "wrote", "written", "file",
    "pixel", "frame", "screenshot", "PNG", "png",
)
OUT_IDEMPOTENT_KEYS = (
    "identical", "idempotent", "twice", "again", "second call", "same-content",
    "byte-identical", "already there",
)


def hits(text, keys):
    found = {}
    lines = text.split("\n")
    for k in keys:
        for i, line in enumerate(lines):
            if k in line:
                found.setdefault(k, i + 1)
                break
    return found


def case_annotation(body):
    neg = hits(body, NEGATIVE_KEYS)
    bnd = hits(body, BOUNDARY_KEYS)
    suc = hits(body, OUT_SUCCESS_KEYS)
    err = hits(body, OUT_ERROR_KEYS)
    rbk = hits(body, OUT_READBACK_KEYS)
    eff = hits(body, OUT_EFFECT_KEYS)
    idem = hits(body, OUT_IDEMPOTENT_KEYS)
    return {
        "illegal": sorted(neg.keys()),
        "illegal_lines": neg,
        "boundary": sorted(bnd.keys()),
        "boundary_lines": bnd,
        "success": bool(suc),
        "error_code": bool(err),
        "error_lines": err,
        "readback": bool(rbk),
        "side_effect": bool(eff),
        "idempotent": bool(idem),
        "idempotent_lines": idem,
    }


TOOL_LIT = None


def tool_mentions(text, names):
    out = {}
    for n in names:
        lit = '"%s"' % n
        idx = text.find(lit)
        if idx >= 0:
            out[n] = text[:idx].count("\n") + 1
    return out


def main():
    with io.open(os.path.join(HERE, "inventory.json"), "r", encoding="utf-8") as h:
        inv = json.load(h)
    # optional: the per-tool REAL trace facts and the live probe (written by traces.py / probe.py)
    tr = {}
    probe = {}
    tp = os.path.join(HERE, "traces.json")
    if os.path.isfile(tp):
        with io.open(tp, "r", encoding="utf-8") as h:
            tr = json.load(h).get("tools") or {}
    pp = os.path.join(HERE, "probe-live.json")
    if os.path.isfile(pp):
        with io.open(pp, "r", encoding="utf-8") as h:
            probe = json.load(h).get("tools") or {}
    names = [t["name"] for t in inv["contract"]["tools"]]
    contract = {t["name"]: t for t in inv["contract"]["tools"]}
    channels = inv["channels"]["channels"]
    cov = inv["coverage"]["rows"]
    rmap = inv["rename_map"]["map"]

    # ---- engine case -> the tools it mentions --------------------------------
    engine_cases = []
    tool_engine = {n: [] for n in names}
    for c in inv["engine"]["cases"]:
        ann = case_annotation(c["body"])
        mentioned = tool_mentions(c["body"], names)
        for n, rel_line in mentioned.items():
            tool_engine[n].append({"case": c["name"], "case_line": c["line"],
                                   "tool_line": c["line"] + rel_line - 1})
        engine_cases.append({"n": c["n"], "name": c["name"], "line": c["line"],
                             "end_line": c["end_line"], "body_lines": c["body_lines"],
                             "annotation": ann, "tools": sorted(mentioned.keys())})

    # ---- per tool -------------------------------------------------------------
    tools = []
    for n in names:
        cd = contract[n]
        ch = channels.get(n)
        row = cov.get(n)
        rm = rmap.get(n, {})
        ec = tool_engine[n]
        val_cases = [e for e in ec if re.search(
            r"validat|refus|reject|never|without|needs|require",
            e["case"], re.I)]
        # boundary evidence for THIS tool = the coverage ledger's failed-call count
        boundary_calls = (row or {}).get("boundary", 0)
        run_dirs = [ev["run"] for ev in ((row or {}).get("evidence") or [])]
        # ---- negative class (TASK-143): strong = a REAL observed failure ---------
        trow = tr.get(n) or {}
        prow = probe.get(n) or {}
        trace_negs = trow.get("negatives") or []
        probe_refused = prow.get("verdict") == "refused_-32602"
        engine_weak = None
        for e in ec:
            ann = next(c["annotation"] for c in engine_cases if c["name"] == e["case"] and c["line"] == e["case_line"])
            if ann["illegal"]:
                engine_weak = {"case": e["case"], "pointer": "%s:%d" % (inv["engine"]["path"], e["tool_line"]),
                               "keys": ann["illegal"][:3]}
                break
        if trace_negs or probe_refused or boundary_calls:
            negative_class = "strong"
        elif engine_weak:
            negative_class = "weak"
        else:
            negative_class = "none"
        neg = []
        if trace_negs:
            n0 = trace_negs[0]
            neg.append({"kind": "trace_failing_call",
                        "pointer": n0["pointer"],
                        "how": "a REAL failing call with error_code=%s and message=%r was recorded in that trace line"
                               % (n0.get("code"), n0.get("message"))})
        if probe_refused:
            neg.append({"kind": "live_probe",
                        "pointer": "recovery/work/task143/probe-live.json tools.%s" % n,
                        "how": "a live illegal-input call answered -32602: %r" % (prow.get("error_message"),)})
        if boundary_calls:
            neg.append({"kind": "ledger_boundary_call",
                        "pointer": "coverage.json row %s.boundary=%d" % (n, boundary_calls),
                        "how": "the ledger counted %d calls that answered ok=false in the trace corpus" % boundary_calls})
        if engine_weak:
            neg.append({"kind": "engine_mention_only", "pointer": engine_weak["pointer"],
                        "case": engine_weak["case"],
                        "how": "WEAK: a TEST_CASE that merely MENTIONS this tool and whose body contains an "
                               "illegal-input assertion (%s) - not proof the assertion is about this tool"
                               % ", ".join(engine_weak["keys"])})
        # state-unchanged detection: is there any case that asserts the effect really happened?
        state_proof = None
        if row:
            if row.get("evidence_tier") in ("pixel_effect", "file_effect"):
                state_proof = "%s (channel_evidence=%s/%s)" % (row["evidence_tier"],
                                                              row.get("channel_evidence"), row.get("calls"))
            elif row.get("evidence_tier") == "readback":
                rb = row.get("readback") or {}
                state_proof = "readback:%s witness=%s" % (rb.get("kind"), rb.get("witness_tool"))
        stale = []
        if ch is None:
            stale.append("no channel declaration")
        elif row is not None and ch.get("channel") != row.get("evidence_channel"):
            stale.append("channel declaration %s vs ledger %s" % (ch.get("channel"), row.get("evidence_channel")))
        if row is None:
            stale.append("no coverage row")
        if not ec:
            stale.append("no engine TEST_CASE mentions the tool")
        status = "present"
        if not ec:
            status = "missing"
        if any("channel declaration" in s or "no coverage row" in s for s in stale):
            status = "stale"
        tools.append({
            "name": n,
            "contract_line": cd["contract_line"],
            "scope": rm.get("scope"), "verb": rm.get("verb"), "old_name": rm.get("old_name"),
            "required": cd["required"], "optional": cd["optional"],
            "defaults": cd["defaults"], "enums": cd["enums"], "types": cd["types"],
            "channel": (ch or {}).get("channel"), "channel_line": (ch or {}).get("line"),
            "calls": (row or {}).get("calls"), "boundary": (row or {}).get("boundary"),
            "effective": (row or {}).get("effective"), "facts_complete": (row or {}).get("facts_complete"),
            "status_ledger": (row or {}).get("status"), "tier": (row or {}).get("evidence_tier"),
            "channel_evidence_ok": (row or {}).get("channel_evidence_ok"),
            "readback": (row or {}).get("readback"),
            "run_dirs": run_dirs,
            "engine_cases": ec, "validation_cases": val_cases,
            "engine_case_count": len(ec),
            "negative": neg,
            "negative_count": len(neg),
            "negative_class": negative_class,
            "trace_negative": trace_negs[0] if trace_negs else None,
            "probe_refused": probe_refused,
            "state_proof": state_proof,
            "stale": stale,
            "status": status,
        })

    # ---- cross-consistency -----------------------------------------------------
    cnames = set(names)
    chnames = set(channels)
    covnames = set(cov)
    consistency = {
        "contract_vs_channels": sorted(cnames ^ chnames),
        "contract_vs_coverage": sorted(cnames ^ covnames),
        "channel_mismatch": sorted(n for n in cnames & chnames & covnames
                                   if channels[n].get("channel") != cov[n].get("evidence_channel")),
        "unreachable_registry": inv["coverage"]["unreachable_registry"],
        "rename_map_has_no_new_name_for": sorted(
            n for n in cnames if n not in rmap),
        "engine_case_count": len(engine_cases),
    }

    # ---- statistics ------------------------------------------------------------
    stats = {
        "contract_tools": len(tools),
        "tools_with_engine_case": sum(1 for t in tools if t["engine_case_count"]),
        "tools_without_engine_case": sum(1 for t in tools if not t["engine_case_count"]),
        "tools_with_negative": sum(1 for t in tools if t["negative_count"]),
        "tools_without_negative": sum(1 for t in tools if not t["negative_count"]),
        "tools_negative_strong": sum(1 for t in tools if t["negative_class"] == "strong"),
        "tools_negative_weak_only": sum(1 for t in tools if t["negative_class"] == "weak"),
        "tools_negative_none": sum(1 for t in tools if t["negative_class"] == "none"),
        "tools_trace_negative": sum(1 for t in tools if t["trace_negative"]),
        "tools_probe_refused": sum(1 for t in tools if t["probe_refused"]),
        "tools_with_state_proof": sum(1 for t in tools if t["state_proof"]),
        "tools_without_state_proof": sum(1 for t in tools if not t["state_proof"]),
        "tools_status_missing": sum(1 for t in tools if t["status"] == "missing"),
        "tools_status_stale": sum(1 for t in tools if t["status"] == "stale"),
        "tools_required_optional": sum(1 for t in tools if t["required"] and t["optional"]),
        "tools_with_defaults": sum(1 for t in tools if t["defaults"]),
        "tools_with_enums": sum(1 for t in tools if t["enums"]),
        "tools_no_properties": sum(1 for t in tools if not t["required"] and not t["optional"]),
        "engine_cases": len(engine_cases),
        "engine_cases_with_illegal": sum(1 for c in engine_cases if c["annotation"]["illegal"]),
        "engine_cases_with_boundary": sum(1 for c in engine_cases if c["annotation"]["boundary"]),
        "engine_cases_with_error_code": sum(1 for c in engine_cases if c["annotation"]["error_code"]),
        "engine_cases_with_side_effect": sum(1 for c in engine_cases if c["annotation"]["side_effect"]),
        "engine_cases_with_idempotent": sum(1 for c in engine_cases if c["annotation"]["idempotent"]),
    }

    out = {"tools": tools, "engine_cases": engine_cases,
           "consistency": consistency, "stats": stats,
           "engine_path": inv["engine"]["path"]}
    path = os.path.join(HERE, "analysis.json")
    with io.open(path, "w", encoding="utf-8", newline="\n") as h:
        h.write(json.dumps(out, ensure_ascii=False, indent=1))
    print("wrote %s" % path)
    for k, v in stats.items():
        print("  %-34s %s" % (k, v))
    print("  consistency problems: %s" % json.dumps(
        {k: (len(v) if isinstance(v, list) else v) for k, v in consistency.items()},
        ensure_ascii=False))
    return 0


if __name__ == "__main__":
    sys.exit(main())
