# -*- coding: utf-8 -*-
"""TASK-083 recon 8: reconstruction-index entries for a set of module paths."""
import io
import json
import os
import sys

IDX = r"C:\Users\wyl\AppData\Local\Temp\mcp-recovery\staging\__payload-index"

WANT = [
    "tools\\editor_node_read.cpp",
    "tools\\running_game_read_scene.cpp",
    "tools\\project_write_resource_scene.cpp",
    "tools\\running_game_frame_observation.cpp",
    "tools\\running_game_node_write.cpp",
    "tools\\tool_helpers.h",
    "tools\\project_read_files.h",
    "tools\\tool_helpers.cpp",
    "tools\\project_validate_scripts.cpp",
    "tool_registry.cpp",
    "tools\\editor_input_simulation.cpp",
    "tools\\editor_node_batch_write.cpp",
    "tools\\editor_node_setup.cpp",
    "tools\\editor_node_write.cpp",
    "tools\\editor_write_scene_editor.cpp",
    "tools\\running_game_script_execution.cpp",
    "tools\\running_game_test_execution.cpp",
    "tools\\editor_testing_read.cpp",
    "tools\\tool_builder.h",
]


def main():
    rows = []
    with io.open(os.path.join(IDX, "reconstruction.jsonl"), "r", encoding="utf-8", errors="replace") as f:
        for line in f:
            line = line.strip()
            if line:
                rows.append(json.loads(line))
    for w in WANT:
        hits = [r for r in rows if r.get("rel", "").endswith("mcp_server\\" + w)]
        if not hits:
            print("== %-45s NO ENTRY" % w)
            continue
        for r in hits:
            print("== %-45s conf=%-8s chosen=%-14s bytes=%-7s cov=%-6s pct=%-6s miss=%-5s tail=%-3s failed=%s" % (
                w, r.get("conf"), r.get("chosen"), r.get("bytes"), r.get("read_cov"),
                r.get("read_cov_pct"), r.get("read_missing_n"), r.get("miss_tail"),
                r.get("n_failed")))
            for n in (r.get("notes") or [])[:3]:
                print("      note: %s" % n)


if __name__ == "__main__":
    main()
