#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""TASK-113 helper: list every `ok=true` payload of one tool in one run.

Read-only. Usage:
    python recovery/work/task113/dump_run_tool.py RUN_DIR TOOL [TOOL...]
    python recovery/work/task113/dump_run_tool.py RUN_DIR TOOL --find NEEDLE
"""
import io
import os
import sys
import importlib.util

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.abspath(os.path.join(HERE, "..", "..", ".."))
SPEC = os.path.join(ROOT, "tools", "tool_coverage.py")


def main(argv):
    if len(argv) < 3:
        print(__doc__)
        return 2
    needle = None
    if "--find" in argv:
        index = argv.index("--find")
        needle = argv[index + 1]
        argv = argv[:index]
    run_dir = argv[1]
    wanted = set(argv[2:])
    spec = importlib.util.spec_from_file_location("tool_coverage", SPEC)
    cov = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(cov)
    ledger = cov.load_module(os.path.join(ROOT, cov.LEDGER), "mcp_trace_ledger")
    base = run_dir if os.path.isabs(run_dir) else os.path.join(ROOT, run_dir)
    for name in sorted(os.listdir(base)):
        if not (name.startswith("trace-") and name.endswith(".jsonl")):
            continue
        path = os.path.join(base, name)
        records, _broken = ledger.load(path)
        for row in ledger.build(records, path):
            if row.get("tool") not in wanted or not row["ok"]:
                continue
            text = row.get("result_json") or ""
            if row.get("result_json_evidence") == "sidecar_verified":
                side = (row.get("result_json_sidecar_detail") or {}).get("resolved_path")
                if side and os.path.isfile(side):
                    with io.open(side, "r", encoding="utf-8", errors="replace") as h:
                        text = h.read()
            print("=== %s seq=%s %s (%d bytes)" % (name, row.get("call_id"), row.get("tool"), len(text)))
            if needle is None:
                print("    %s" % text[:3000])
                continue
            start = 0
            hits = 0
            while hits < 6:
                at = text.find(needle, start)
                if at < 0:
                    break
                print("    @%d ... %s" % (at, text[max(0, at - 60):at + 300]))
                start = at + 1
                hits += 1
            if hits == 0:
                print("    (needle absent)")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
