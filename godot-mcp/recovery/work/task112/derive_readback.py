#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""TASK-112 item B: enumerate the read calls that could serve as a `readback`
witness for each `count_only` writer, per run.

Read-only analysis. Prints, for every writer the ledger leaves on `count_only`,
the read-verb calls of its strongest run that answered ok with a substantive
payload - the candidates a manifest declaration may name. The declaration is
written by hand (recovery/work/task112/readback-declarations.py) and is then
re-verified by `tool_coverage.py` against the same trace rows; this script only
says what is *available* to point at.
"""
import io
import json
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.abspath(os.path.join(HERE, "..", "..", ".."))
sys.path.insert(0, os.path.join(ROOT, "tools"))

import importlib.util

LEDGER = os.path.join(ROOT, "godot", "modules", "mcp_server", "scripts", "mcp_trace_ledger.py")
spec = importlib.util.spec_from_file_location("mcp_trace_ledger", LEDGER)
ledger = importlib.util.module_from_spec(spec)
spec.loader.exec_module(ledger)

READ_VERBS = {"get", "read", "search", "list", "find", "analyze", "detect",
              "convert", "validate", "check", "assert", "execute", "evaluate",
              "capture"}


def verb_of(name):
    parts = name.split("_")
    return parts[1] if len(parts) > 1 else None


def substantive(raw):
    if not isinstance(raw, str) or not raw.strip():
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


def main(argv):
    target = argv[1] if len(argv) > 1 else os.path.join(ROOT, "coverage.json")
    with io.open(target, "r", encoding="utf-8") as handle:
        payload = json.load(handle)
    wanted = [r for r in payload["tools"] if r["evidence_tier"] == "count_only"]

    # run -> tool -> [(seq, ok, substantive)]
    runs = {}
    base = os.path.join(ROOT, "runs")
    for dirpath, _dirs, files in os.walk(base):
        for fname in sorted(files):
            if not (fname.startswith("trace-") and fname.endswith(".jsonl")):
                continue
            path = os.path.join(dirpath, fname)
            rel = os.path.relpath(dirpath, ROOT).replace("\\", "/")
            records, _broken = ledger.load(path)
            rows = ledger.build(records, path)
            per = runs.setdefault(rel, {})
            for row in rows:
                name = row.get("tool")
                if not name:
                    continue
                per.setdefault(name, []).append({
                    "seq": row.get("call_id"), "ok": bool(row["ok"]),
                    "substantive": substantive(row.get("result_json"))
                                   or row.get("result_json_evidence") == "sidecar_verified",
                })

    for row in wanted:
        name = row["tool"]
        print("=" * 78)
        print("%s  calls=%d boundary=%d verb=%s" % (name, row["calls"], row["boundary"], row["verb"]))
        for ev in row["evidence"][:2]:
            rel = ev["run"]
            per = runs.get(rel) or {}
            reads = []
            for other, calls in per.items():
                if other == name or verb_of(other) not in READ_VERBS:
                    continue
                good = [c for c in calls if c["ok"] and c["substantive"]]
                if good:
                    reads.append((other, good[0]["seq"], len(good)))
            reads.sort(key=lambda x: (-x[2], x[0]))
            print("  run %s" % rel)
            for other, seq, count in reads:
                print("      witness %-45s seq=%-5s ok+payload=%d" % (other, seq, count))
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
