#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""TASK-113 item C helper: dump each declared witness call's payload.

Read-only. Prints one block per declaration: the writer, the witness tool, the
run and the payloads of every `ok=true` substantive call of the witness tool in
that run, so a content-level `expect` can be chosen from what the engine really
answered instead of from what the writer claims.

Usage:
    python recovery/work/task113/dump_witnesses.py [TOOL ...]
"""
import io
import importlib.util
import json
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.abspath(os.path.join(HERE, "..", "..", ".."))
SPEC = os.path.join(ROOT, "tools", "tool_coverage.py")


def load_coverage():
    spec = importlib.util.spec_from_file_location("tool_coverage", SPEC)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def main(argv):
    cov = load_coverage()
    ledger = cov.load_module(os.path.join(ROOT, cov.LEDGER), "mcp_trace_ledger")
    traces = cov.iter_traces(ROOT, "runs", False, [])
    declarations = cov.load_readback_declarations(ROOT)
    wanted = set(argv[1:])
    if wanted:
        declarations = [d for d in declarations if d["tool"] in wanted]

    per_run = {}
    for declaration in declarations:
        run = declaration.get("run")
        witness = declaration.get("witness_tool")
        if run not in per_run:
            per_run[run] = {}
            for rel, path in traces:
                if rel != run:
                    continue
                records, _broken = ledger.load(path)
                for row in ledger.build(records, path):
                    name = row.get("tool")
                    if not name or not row["ok"]:
                        continue
                    text = row.get("result_json")
                    evidence = row.get("result_json_evidence")
                    if evidence == "sidecar_verified":
                        side = (row.get("result_json_sidecar_detail") or {}).get("resolved_path")
                        if side and os.path.isfile(side):
                            with io.open(side, "r", encoding="utf-8", errors="replace") as h:
                                text = h.read()
                    if not cov.substantive(row.get("result_json")) and evidence != "sidecar_verified":
                        continue
                    per_run[run].setdefault(name, []).append(
                        {"seq": row.get("call_id"), "text": text})
        payloads = per_run[run].get(witness) or []
        print("=" * 78)
        print("%s  <-  %s" % (declaration["tool"], witness))
        print("  run        : %s" % run)
        print("  declared   : %s" % declaration.get("declared_in"))
        print("  why        : %s" % declaration.get("why"))
        print("  payloads   : %d" % len(payloads))
        for payload in payloads:
            text = payload["text"] or ""
            print("  --- seq=%s (%d bytes)" % (payload["seq"], len(text)))
            print("      %s" % text[:700].replace("\n", " "))
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
