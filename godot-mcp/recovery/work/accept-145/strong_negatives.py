#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Adversarial audit of the 'strong counterexample' claim: 177/177."""
import io, json, os, re, collections
ROOT = r"F:\moonbit-hof-rs\godot-mcp"
OUT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "strong_negatives.json")

tools = json.load(io.open(os.path.join(ROOT, "godot", "modules", "mcp_server", "docs", "tools_list.renamed.json"), "r", encoding="utf-8"))["result"]["tools"]
names = [t["name"] for t in tools]
cov = {r["tool"]: r for r in json.load(io.open(os.path.join(ROOT, "coverage.json"), "r", encoding="utf-8"))["tools"]}
probe = json.load(io.open(os.path.join(ROOT, "recovery", "work", "task143", "probe-live.json"), "r", encoding="utf-8"))["tools"]
probe_u2 = json.load(io.open(os.path.join(ROOT, "recovery", "work", "task144", "probe-u2.json"), "r", encoding="utf-8"))
traces = json.load(io.open(os.path.join(ROOT, "recovery", "work", "task143", "traces.json"), "r", encoding="utf-8"))["tools"]

# probe-u2 structure
u2 = {}
def find_u2(obj, acc):
    if isinstance(obj, dict):
        if "tool" in obj and "error_code" in obj:
            acc[obj["tool"]] = obj
        for v in obj.values():
            find_u2(v, acc)
    elif isinstance(obj, list):
        for v in obj:
            find_u2(v, acc)
find_u2(probe_u2, u2)

lines = io.open(os.path.join(ROOT, "recovery", "TEST-CASES.md"), "r", encoding="utf-8").read().split("\n")
rows = {}
for i, l in enumerate(lines, 1):
    if l.startswith("| TC-TOOL-"):
        c = [x.strip() for x in l.strip().strip("|").split("|")]
        if len(c) == 9:
            rows[c[1].strip("`")] = {"line": i, "cells": c}

rep = {"per_tool": {}, "counts": {}}
have_trace_real = 0
have_probe = 0
have_boundary = 0
none = []
soft_only = []
for n in names:
    t = traces.get(n) or {}
    codes = t.get("error_codes") or {}
    real = {c: v for c, v in codes.items() if c not in ("0", "")}
    soft = bool(t.get("soft_failures"))
    pr = probe.get(n) or {}
    pu = u2.get(n)
    cov_r = cov.get(n) or {}
    b = cov_r.get("boundary", 0)
    if real:
        have_trace_real += 1
    if pr.get("verdict") == "refused_-32602" or pu:
        have_probe += 1
    if b and b >= 1:
        have_boundary += 1
    if not real and not (pr.get("verdict") == "refused_-32602" or pu) and not (b and b >= 1):
        none.append(n)
    if not real and soft and not (pr.get("verdict") == "refused_-32602" or pu) and not (b and b >= 1):
        soft_only.append(n)
    cell_neg = rows[n]["cells"][6] if n in rows else ""
    rep["per_tool"][n] = {
        "has_trace_real_failure": bool(real),
        "trace_codes": real,
        "trace_soft_failures": bool(soft),
        "probe_verdict": pr.get("verdict"),
        "probe_kind": pr.get("probe_kind"),
        "probe_message": pr.get("error_message"),
        "probe_count_unit": pr.get("probe_count_unit"),
        "u2_probe": ({k: pu[k] for k in pu if k in ("error_code", "error_message", "request_arguments", "response_excerpt")} if pu else None),
        "boundary": b,
        "status": cov_r.get("status"),
        "channel": cov_r.get("evidence_channel"),
        "matrix_state": rows[n]["cells"][7] if n in rows else None,
        "neg_cell_has_trace_pointer": bool(re.search(r"trace-[a-z]+\.jsonl:\d+", cell_neg)),
        "neg_cell_mentions_probe": ("探针" in cell_neg or "probe" in cell_neg.lower()),
        "neg_cell": cell_neg[:300],
    }

rep["counts"] = {
    "tools": len(names),
    "tools_with_real_trace_failure": have_trace_real,
    "tools_with_probe_32602": have_probe,
    "tools_with_boundary_ge1": have_boundary,
    "tools_with_no_strong_evidence": len(none),
    "no_strong_evidence": none,
    "soft_only": soft_only,
    "probe_missing_required": sum(1 for n in names if (probe.get(n) or {}).get("probe_kind") == "missing_required"),
    "probe_wrong_type": sum(1 for n in names if (probe.get(n) or {}).get("probe_kind") == "wrong_type_optional"),
    "probe_unknown_parameter": sum(1 for n in names if (probe.get(n) or {}).get("probe_kind") == "unknown_parameter") + len(u2),
    "matrix_rows_with_trace_pointer_in_neg": sum(1 for n in names if rows.get(n) and re.search(r"trace-[a-z]+\.jsonl:\d+", rows[n]["cells"][6])),
    "matrix_rows_with_probe_mention_in_neg": sum(1 for n in names if rows.get(n) and ("探针" in rows[n]["cells"][6] or "probe" in rows[n]["cells"][6].lower())),
    "matrix_rows_missing": [n for n in names if n not in rows],
    "u2_tools": sorted(u2.keys()),
}
with io.open(OUT, "w", encoding="utf-8", newline="\n") as h:
    h.write(json.dumps(rep, ensure_ascii=False, indent=2))
print(json.dumps(rep["counts"], ensure_ascii=False, indent=2))
print("u2 record:", json.dumps({k: {kk: vv for kk, vv in v.items() if kk in ('error_code','error_message')} for k, v in u2.items()}, ensure_ascii=False))
