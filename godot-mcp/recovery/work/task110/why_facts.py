#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""TASK-110 recon: which reconstructible fact is missing on an ok row?"""
import importlib.util
import io
import json
import os
import sys

ROOT = r"F:\moonbit-hof-rs\godot-mcp"
spec = importlib.util.spec_from_file_location(
    "ledger", os.path.join(ROOT, "godot", "modules", "mcp_server", "scripts", "mcp_trace_ledger.py"))
ledger = importlib.util.module_from_spec(spec)
spec.loader.exec_module(ledger)

trace = sys.argv[1] if len(sys.argv) > 1 else os.path.join(
    ROOT, "runs", "_exercises", "ex_files", "c1-task110", "trace-editor.jsonl")
records, broken = ledger.load(trace)
rows = ledger.build(records, trace)
missing = {}
ok_missing = {}
for r in rows:
    for k, v in r["facts"].items():
        if not v:
            missing[k] = missing.get(k, 0) + 1
            if r["ok"]:
                ok_missing[k] = ok_missing.get(k, 0) + 1
print("rows=%d broken=%d" % (len(rows), broken))
print("facts missing (all rows):", missing)
print("facts missing (ok rows only):", ok_missing)
ok_rows = [r for r in rows if r["ok"]]
if ok_rows:
    r = ok_rows[0]
    print()
    print("sample ok row: tool=%s verdict=%s file_effect=%s capture=%s" %
          (r["tool"], r["verdict"], r["file_effect"], r["capture_mode"]))
    print("  facts:", r["facts"])
    print("  raw keys on the line: check 'error_code' in record ->",
          "error_code" in [k for k in ("error_code",)])
# raw record check
for rec in records:
    if rec.get("method") == "tools/call" and rec.get("ok"):
        print("raw ok record keys:", sorted(rec.keys()))
        print("  has error_code:", "error_code" in rec, "| has capture:", isinstance(rec.get("capture"), dict))
        print("  scene evidence present:", rec.get("capture", {}).get("status"))
        break
