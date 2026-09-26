# -*- coding: utf-8 -*-
"""TASK-083 recon 9: list write payloads touching the damaged module files."""
import io
import json
import os

IDX = r"C:\Users\wyl\AppData\Local\Temp\mcp-recovery\staging\__payload-index"

WANT = [
    "mcp_server.cpp",
    "tools\\editor_node_read.cpp",
    "tools\\running_game_read_scene.cpp",
    "tools\\project_write_resource_scene.cpp",
    "tools\\running_game_frame_observation.cpp",
    "tools\\running_game_node_write.cpp",
    "tools\\tool_helpers.h",
    "tools\\project_read_files.h",
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


def rows(fn):
    with io.open(os.path.join(IDX, fn), "r", encoding="utf-8", errors="replace") as f:
        for line in f:
            line = line.strip()
            if line:
                yield json.loads(line)


def main():
    writes = {}
    for r in rows("events-write.jsonl"):
        p = r.get("path", "").replace("/", "\\")
        if "modules\\mcp_server\\" not in p:
            continue
        rel = p.split("modules\\mcp_server\\", 1)[1]
        writes.setdefault(rel, []).append(r)
    for w in WANT:
        rs = writes.get(w, [])
        print("== %-45s writes=%d" % (w, len(rs)))
        for r in sorted(rs, key=lambda x: x.get("time", 0)):
            c = r.get("content") or ""
            print("     time=%s seq=%-5s len=%d lines=%d  f=%s" % (
                r.get("time"), r.get("seq"), len(c), c.count("\n") + 1, r.get("f")))


if __name__ == "__main__":
    main()
