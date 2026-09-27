#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""TASK-110: derive tools/tool_coverage_unreachable.json from the TASK-108 report.

The registry is data, not code: tool_coverage.py reads it to print the
"unreachable register" view. This one-off generator makes the derivation
auditable - every member row and every category definition is copied out of
recovery/reports/TOOL-COVERAGE-TASK-108.md section 5.3 (the INFERENCE section),
so the registry cannot silently drift from the report it summarises.

Writes exactly one file: tools/tool_coverage_unreachable.json
"""
import io
import json
import os
import re

ROOT = r"F:\moonbit-hof-rs\godot-mcp"
REPORT = os.path.join(ROOT, "recovery", "reports", "TOOL-COVERAGE-TASK-108.md")
OUT = os.path.join(ROOT, "tools", "tool_coverage_unreachable.json")

with io.open(REPORT, "r", encoding="utf-8") as h:
    lines = h.read().split("\n")

# --- the category definitions, from the H1..H9 table ---------------------------
cat_re = re.compile(r"^\|\s*\*\*(H[1-9])\*\*\s*\|\s*([^|]+)\|\s*([^|]+)\|\s*([^|]+)\|\s*$")
categories = {}
for ln in lines:
    m = cat_re.match(ln)
    if m:
        code, label, why, evidence = m.group(1), m.group(2).strip(), m.group(3).strip(), m.group(4).strip()
        categories[code] = {"code": code, "label": label, "why_unreachable": why,
                            "supporting_evidence": evidence}

# --- the membership rows -------------------------------------------------------
mem_re = re.compile(r"^\|\s*\d+\s*\|\s*`([a-z0-9_]+)`\s*\|\s*([a-z]+)\s*\|\s*(H[1-9])\s*\|\s*$")
members = []
for ln in lines:
    m = mem_re.match(ln)
    if m:
        members.append({"tool": m.group(1), "scope": m.group(2), "category": m.group(3)})

by_cat = {}
for item in members:
    by_cat.setdefault(item["category"], []).append(item)

payload = {
    "_comment": ("TASK-110 tool coverage ledger - the structurally-unreachable register. "
                 "Derived verbatim from recovery/reports/TOOL-COVERAGE-TASK-108.md section 5.3, "
                 "which is explicitly an INFERENCE (missing subsystem/asset/precondition), not a "
                 "runtime measurement. A tool listed here is reported as 'unreachable(registry)' by "
                 "tools/tool_coverage.py; it is NOT counted as a coverage miss. Delete an entry only "
                 "by demonstrating the missing subsystem now exists in the measured corpus - and if "
                 "you do, record the demonstration under `reclassified` instead of deleting it "
                 "silently, so the inference's error stays auditable."),
    "_source_report": "recovery/reports/TOOL-COVERAGE-TASK-108.md",
    "_source_section": "5.3 (5) which of them are structurally unreachable in this loop (INFERENCE)",
    "categories": {k: dict(v, tools=[i["tool"] for i in by_cat.get(k, [])])
                   for k, v in sorted(categories.items())},
    "members": sorted(members, key=lambda x: (x["category"], x["tool"])),
    "total": len(members),
    # TASK-110 measured six of the inference's members being called for real. They
    # are listed here rather than deleted, because the register's whole purpose is
    # to keep an inference falsifiable: a reader can see both the original claim
    # and the measurement that killed it.
    "_reclassified_comment": ("TASK-110 batch c23 called these six for real (>=5 calls each, with "
                              "an effective call and a boundary probe). They are removed from the "
                              "'unreachable' set that tool_coverage.py reports, and kept here with "
                              "the run that did it."),
    "reclassified": [
        {"tool": "editor_get_selection", "from": "H7",
         "why": "the editor's own GUI selection state is readable through the editor endpoint: no "
                "selection is a valid answer ({\"count\":0,\"nodes\":[],\"top_only\":false}).",
         "evidence": "runs/_exercises/ex_scene/c23-task110/trace-editor.jsonl"},
        {"tool": "editor_get_open_scripts", "from": "H7",
         "why": "the open-script list is answerable with none open ({\"count\":0,\"scripts\":[]}).",
         "evidence": "runs/_exercises/ex_scene/c23-task110/trace-editor.jsonl"},
        {"tool": "editor_get_output_log", "from": "H7",
         "why": "the editor's Output panel is readable in-process; the answer carries "
                "available/in_process/log_path plus the lines.",
         "evidence": "runs/_exercises/ex_scene/c23-task110/trace-editor.jsonl"},
        {"tool": "editor_get_performance_monitors", "from": "H7",
         "why": "60 monitors reported from the editor process; no subsystem is missing.",
         "evidence": "runs/_exercises/ex_scene/c23-task110/trace-editor.jsonl"},
        {"tool": "running_game_capture_frames", "from": "H9",
         "why": "frame capture needs no pre-registered mode: count/frame_interval are enough and "
                "the frames come back inline (base64 PNG).",
         "evidence": "runs/_exercises/ex_scene/c23-task110/trace-game.jsonl"},
        {"tool": "running_game_capture_signal_emissions", "from": "H9",
         "why": "it registers the watch itself and reports what fired inside duration_ms "
                "(measured: 1 and 2 emissions for Tick.timeout).",
         "evidence": "runs/_exercises/ex_scene/c23-task110/trace-game.jsonl"},
    ],
}

with io.open(OUT, "w", encoding="utf-8", newline="\n") as h:
    h.write(json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=False) + "\n")

print("categories=%d members=%d" % (len(categories), len(members)))
for k in sorted(categories):
    print("  %s %-28s %d" % (k, categories[k]["label"][:28], len(by_cat.get(k, []))))
print("wrote %s" % OUT)
