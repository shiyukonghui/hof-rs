"""TASK-114 C4 -- record the two H8 reclassifications in the unreachable registry.

The registry's own rule is: never delete a member, only add a `reclassified` entry that
says the member is no longer unreachable and why. This script is idempotent -- re-running
it replaces its own two entries instead of duplicating them.
"""

import json

P = r"F:\moonbit-hof-rs\godot-mcp\tools\tool_coverage_unreachable.json"

NEW = [
    {
        "tool": "project_get_export_info",
        "from": "H8",
        "why": (
            "the two export-read tools only need res://export_presets.cfg, not a real export. "
            "Ex_export (2 presets: Windows Desktop + Web) drove the real success branch on BOTH "
            "endpoints -- editor answers capabilities={editor_export:true,editor_process:true,"
            "presets_source:'editor_export'} with preset_count=2, the game process answers "
            "editor_export:false,editor_process:false,presets_source:'export_presets.cfg' with the "
            "same preset_count=2. Ex_export_np (no export_presets.cfg at all) drove the "
            "capability-missing branch: presets_file_present=false, count=0, message=\"'res://"
            "export_presets.cfg' does not exist: this project has no export presets\", and on the "
            "editor endpoint unavailable[] carries the export_presets entry -- i.e. a missing file "
            "is an answer, not an error. The empty inputSchema also gives a constructible boundary: "
            "any argument is refused with -32602 \"accepts no parameters\" (4x, both endpoints)."
        ),
        "evidence": (
            "runs/_exercises/ex_export/h8-task114/trace-editor.jsonl, "
            "runs/_exercises/ex_export/h8-task114/trace-game.jsonl, "
            "runs/_exercises/ex_export_np/h8n-task114/trace-editor.jsonl, "
            "runs/_exercises/ex_export_np/h8n-task114/trace-game.jsonl"
        ),
        "batch": "h8",
        "task": "TASK-114",
    },
    {
        "tool": "project_list_export_presets",
        "from": "H8",
        "why": (
            "same two runs: count=2 with the preset records read straight out of export_presets.cfg "
            "on both endpoints, and count=0 + presets_file_present=false + message on the project "
            "without the file. The unknown-argument gate refuses preset_name and index with -32602."
        ),
        "evidence": (
            "runs/_exercises/ex_export/h8-task114/trace-editor.jsonl, "
            "runs/_exercises/ex_export/h8-task114/trace-game.jsonl, "
            "runs/_exercises/ex_export_np/h8n-task114/trace-editor.jsonl, "
            "runs/_exercises/ex_export_np/h8n-task114/trace-game.jsonl"
        ),
        "batch": "h8",
        "task": "TASK-114",
    },
]

d = json.load(open(P, encoding="utf-8"))
before = len(d["reclassified"])
names = {e["tool"] for e in NEW}
kept = [e for e in d["reclassified"] if e.get("tool") not in names]
d["reclassified"] = kept + NEW
after = len(d["reclassified"])

with open(P, "w", encoding="utf-8") as fh:
    json.dump(d, fh, ensure_ascii=False, indent=2)
    fh.write("\n")

print("reclassified: %d -> %d (replaced %d of my own prior entries)" % (before, after, before - len(kept)))
for e in NEW:
    print("  +", e["tool"], "from", e["from"])
print("members still declared:", len(d["members"]), "total:", d.get("total"))
