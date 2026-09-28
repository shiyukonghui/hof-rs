# -*- coding: utf-8 -*-
"""Scratch: the raw failure evidence of the 3 genuine reds (TASK-144 A.2)."""
import importlib.util
import io
import json
import os

ROOT = os.path.abspath(os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", ".."))
LEDGER = os.path.join(ROOT, "godot", "modules", "mcp_server", "scripts", "mcp_trace_ledger.py")

spec = importlib.util.spec_from_file_location("mcp_trace_ledger", LEDGER)
ledger = importlib.util.module_from_spec(spec)
spec.loader.exec_module(ledger)

WANT = {
    "runs/_exercises/ex_editor/h7-task115": ["editor_set_auto_dismiss_dialogs"],
    "runs/_exercises/ex_grid/c7-task118": ["os_deploy_to_android_device",
                                           "project_get_android_preset_info"],
}
for run, tools in WANT.items():
    path = os.path.join(ROOT, run.replace("/", os.sep))
    name = [f for f in sorted(os.listdir(path)) if f.startswith("trace-")][0]
    records, broken = ledger.load(os.path.join(path, name))
    rows = ledger.build(records, os.path.join(path, name))
    print("== %s/%s  (%d rows, %d malformed)" % (run, name, len(rows), broken))
    for row in rows:
        if row.get("tool") not in tools:
            continue
        print("   seq=%s tool=%s ok=%s verdict=%s file_effect=%s" %
              (row.get("call_id"), row.get("tool"), row.get("ok"), row.get("verdict"),
               row.get("file_effect")))
        for key in sorted(row):
            if "err" in key.lower():
                print("       %s=%r" % (key, str(row[key])[:300]))
        print("       facts_complete=%s error_flags=%s result_flags=%s" %
              (row.get("facts_complete"), row.get("error_flags"), row.get("result_flags")))
