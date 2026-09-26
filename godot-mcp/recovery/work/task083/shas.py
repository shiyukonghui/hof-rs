# -*- coding: utf-8 -*-
"""TASK-083: before/after sha manifest for every file this task touches."""
import hashlib
import io
import json
import os
import sys

TREE = r"H:\rebuild\godot\modules\mcp_server"
OUT = r"C:\Users\wyl\AppData\Local\Temp\mcp-recovery\work\task083"

FILES = [
    "mcp_server.cpp",
    "tools/editor_node_read.cpp",
    "tools/running_game_read_scene.cpp",
    "tools/project_write_resource_scene.cpp",
    "tools/running_game_frame_observation.cpp",
    "tools/running_game_node_write.cpp",
    "tools/tool_helpers.h",
    "tools/project_validate_scripts.cpp",
    "tools/project_read_files.h",
    "tools/project_read_template.cpp",
    "tools/project_cross_scene_write.h",
    "tool_registry.cpp",
    "tools/editor_input_simulation.cpp",
    "tools/editor_node_batch_write.cpp",
    "tools/editor_node_setup.cpp",
    "tools/editor_node_write.cpp",
    "tools/editor_write_scene_editor.cpp",
    "tools/running_game_script_execution.cpp",
    "tools/running_game_test_execution.cpp",
    "tools/editor_testing_read.cpp",
    "tools/tool_helpers.cpp",
    "tools/tool_builder.h",
    "tests/test_mcp_server.h",
]


def sha(p):
    h = hashlib.sha256()
    with open(p, "rb") as f:
        for c in iter(lambda: f.read(1 << 20), b""):
            h.update(c)
    return h.hexdigest().upper()


def main():
    tag = sys.argv[1] if len(sys.argv) > 1 else "before"
    rec = {}
    for rel in FILES:
        p = os.path.join(TREE, rel.replace("/", os.sep))
        if os.path.exists(p):
            rec[rel] = {"sha256": sha(p), "bytes": os.path.getsize(p)}
        else:
            rec[rel] = {"sha256": None, "bytes": None}
    with io.open(os.path.join(OUT, "shas-%s.json" % tag), "w", encoding="utf-8", newline="\n") as f:
        f.write(json.dumps(rec, ensure_ascii=False, indent=1, sort_keys=True))
    print("recorded %d entries -> shas-%s.json" % (len(rec), tag))


if __name__ == "__main__":
    main()
