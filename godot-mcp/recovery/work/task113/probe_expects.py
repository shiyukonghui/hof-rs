#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""TASK-113 item C: test candidate `expect` literals against the real payloads.

Read-only. The candidate file is JSON: {"<writer tool>": ["<literal>", ...], ...}.
For every readback declaration of that writer the script reports the first
witness payload in which *every* literal appears (its seq), or NONE.

Usage:
    python recovery/work/task113/probe_expects.py recovery/work/task113/expects.json
"""
import io
import json
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.abspath(os.path.join(HERE, "..", "..", ".."))
SPEC = os.path.join(ROOT, "tools", "tool_coverage.py")


def main(argv):
    if len(argv) < 2:
        print(__doc__)
        return 2
    with io.open(argv[1], "r", encoding="utf-8") as handle:
        candidates = json.load(handle)

    import importlib.util
    spec = importlib.util.spec_from_file_location("tool_coverage", SPEC)
    cov = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(cov)
    ledger = cov.load_module(os.path.join(ROOT, cov.LEDGER), "mcp_trace_ledger")

    declarations = cov.load_readback_declarations(ROOT)
    traces = {}
    for rel, path in cov.iter_traces(ROOT, "runs", False, []):
        traces.setdefault(rel, []).append(path)

    cache = {}

    def payloads_for(run, tool):
        key = (run, tool)
        if key in cache:
            return cache[key]
        found = []
        for path in traces.get(run, []):
            records, _broken = ledger.load(path)
            for row in ledger.build(records, path):
                if row.get("tool") != tool or not row["ok"]:
                    continue
                text = row.get("result_json")
                if row.get("result_json_evidence") == "sidecar_verified":
                    side = (row.get("result_json_sidecar_detail") or {}).get("resolved_path")
                    if side and os.path.isfile(side):
                        with io.open(side, "r", encoding="utf-8", errors="replace") as h:
                            text = h.read()
                if not cov.substantive(row.get("result_json")) and \
                        row.get("result_json_evidence") != "sidecar_verified":
                    continue
                found.append({"seq": row.get("call_id"), "text": text or ""})
        cache[key] = found
        return found

    for declaration in declarations:
        tool = declaration["tool"]
        wants = candidates.get(tool)
        if wants is None:
            continue
        found = payloads_for(declaration.get("run"), declaration.get("witness_tool"))
        hit = None
        for payload in found:
            if cov.expect_matches(wants, payload["text"]):
                hit = payload["seq"]
                break
        print("%-44s %-38s %s   literals=%s" % (
            tool, declaration.get("witness_tool"),
            ("MATCH seq=%s" % hit) if hit is not None else "NONE",
            json.dumps(wants, ensure_ascii=False)))
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
