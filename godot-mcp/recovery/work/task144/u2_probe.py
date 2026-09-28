# -*- coding: utf-8 -*-
"""Scratch: what the contract declares for the two U2 simulate tools, and what
TASK-143's live probe recorded for them (TASK-144 item C)."""
import io
import json
import os

ROOT = os.path.abspath(os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", ".."))
CONTRACT = os.path.join(ROOT, "godot", "modules", "mcp_server", "docs", "tools_list.renamed.json")
cov = json.load(io.open(os.path.join(ROOT, "coverage.json"), encoding="utf-8"))
rows = {r["tool"]: r for r in cov["tools"]}
doc = json.load(io.open(CONTRACT, encoding="utf-8"))
tools = {t["name"]: t for t in doc["result"]["tools"]}

for name in ["editor_simulate_mouse_click", "editor_simulate_mouse_move",
             "editor_simulate_key", "editor_simulate_input_action",
             "editor_simulate_input_sequence"]:
    t = tools[name]
    schema = t["inputSchema"]
    props = schema.get("properties") or {}
    print("== %s  required=%s  properties=%s" % (name, schema.get("required"), sorted(props)))
    r = rows[name]
    print("   calls=%d boundary=%d status=%s channel=%s unreachable=%s"
          % (r["calls"], r["boundary"], r["status"], r["evidence_channel"],
             r["unreachable_category"]))

probe_path = os.path.join(ROOT, "recovery", "work", "task143", "probe-live.json")
if os.path.isfile(probe_path):
    probe = json.load(io.open(probe_path, encoding="utf-8"))
    for name in ["editor_simulate_mouse_click", "editor_simulate_mouse_move"]:
        entry = (probe.get("tools") or {}).get(name)
        print("probe %s -> %s" % (name, json.dumps(entry, ensure_ascii=False)[:400]))
