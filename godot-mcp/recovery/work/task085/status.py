# -*- coding: utf-8 -*-
"""One-line-per-file status: tree lines, strict-replay lines, target revision,
breaks, refused edits, and how much of the target skeleton the replay covers.

usage: python status.py
"""
import io
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import evfetch as E  # noqa: E402
import replay2 as R  # noqa: E402

ROOT = r"H:\rebuild\godot"

FILES = [
    r"modules\mcp_server\tool_registry.cpp",
    r"modules\mcp_server\tools\running_game_test_execution.cpp",
    r"modules\mcp_server\tools\running_game_frame_observation.cpp",
    r"modules\mcp_server\tools\editor_write_scene_editor.cpp",
    r"modules\mcp_server\tools\project_write_resource_scene.cpp",
    r"modules\mcp_server\tools\running_game_node_write.cpp",
    r"modules\mcp_server\tools\tool_helpers.cpp",
    r"modules\mcp_server\tools\editor_node_write.cpp",
    r"modules\mcp_server\tools\project.cpp",
    r"modules\mcp_server\tools\project_validate_scripts.cpp",
]


def main():
    print("%-46s %6s %6s %6s %5s %5s %5s" % ("file", "tree", "replay", "target", "brk", "ref", "skel-miss"))
    for sub in FILES:
        name = os.path.basename(sub)
        try:
            tree = E.lines_of(os.path.join(ROOT, sub))
        except Exception:  # noqa: BLE001
            tree = []
        buf, info = R.replay(sub, verbose=False)
        rep = buf.split("\n")
        if rep and rep[-1] == "":
            rep.pop()
        skel, rev = E.skeleton(sub)
        miss = 0
        for no in sorted(skel):
            if skel[no].rstrip("\r") not in [x.rstrip("\r") for x in rep]:
                miss += 1
        print("%-46s %6d %6d %6s %5d %5d %5d" % (
            name, len(tree), len(rep), rev, len(info["breaks"]), len(info["refused"]), miss))


if __name__ == "__main__":
    main()
