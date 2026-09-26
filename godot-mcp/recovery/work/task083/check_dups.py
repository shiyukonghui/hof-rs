# -*- coding: utf-8 -*-
"""TASK-083 check: duplicate top-level definitions / structural sanity."""
import collections
import io
import os
import re

TREE = r"H:\rebuild\godot\modules\mcp_server"

FILES = [
    "mcp_server.cpp",
    "tools/editor_node_read.cpp",
    "tools/running_game_read_scene.cpp",
    "tools/project_write_resource_scene.cpp",
    "tools/running_game_frame_observation.cpp",
    "tools/running_game_node_write.cpp",
    "tools/tool_helpers.h",
    "tool_registry.cpp",
    "tools/editor_input_simulation.cpp",
    "tools/editor_node_batch_write.cpp",
    "tools/editor_node_setup.cpp",
    "tools/editor_node_write.cpp",
    "tools/editor_write_scene_editor.cpp",
    "tools/running_game_script_execution.cpp",
    "tools/running_game_test_execution.cpp",
    "tools/editor_testing_read.cpp",
]

DEF = re.compile(r"^[A-Za-z_][A-Za-z0-9_:<>,\* &]*\([^;{}]*\)\s*(const)?\s*\{\s*$")


def main():
    for rel in FILES:
        p = os.path.join(TREE, rel.replace("/", os.sep))
        if not os.path.exists(p):
            print("%-45s MISSING" % rel)
            continue
        L = io.open(p, encoding="utf-8", errors="replace").read().split("\n")
        defs = [l.strip() for l in L if DEF.match(l.strip()) and "::" in l and not l.startswith("\t")]
        c = collections.Counter(defs)
        dup = sorted(k for k, v in c.items() if v > 1)
        print("%-45s lines=%-5d defs=%-4d dups=%d %s" % (rel, len(L), len(defs), len(dup), dup[:3]))


if __name__ == "__main__":
    main()
