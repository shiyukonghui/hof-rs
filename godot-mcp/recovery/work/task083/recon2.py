# -*- coding: utf-8 -*-
"""TASK-083 recon 2: unified diffs tree-vs-backup for the damaged files."""
import difflib
import io
import os

TREE = r"H:\rebuild\godot\modules\mcp_server"
BAK = r"C:\Users\wyl\AppData\Local\Temp\mcp044-module-backup\mcp_server"
OUT = r"C:\Users\wyl\AppData\Local\Temp\mcp-recovery\work\task083"

TARGETS = [
    ("mcp_server.cpp", 51),
    ("tools/editor_node_read.cpp", 0),
    ("tools/running_game_read_scene.cpp", 0),
    ("tools/project_write_resource_scene.cpp", 0),
    ("tools/running_game_frame_observation.cpp", 0),
    ("tools/running_game_node_write.cpp", 0),
    ("tools/tool_helpers.h", 0),
    ("tools/project_read_files.h", 0),
]


def readlines(p):
    with io.open(p, "r", encoding="utf-8", errors="replace", newline="") as f:
        return f.readlines()


def main():
    for rel, skip in TARGETS:
        p = os.path.join(TREE, rel.replace("/", os.sep))
        b = os.path.join(BAK, rel.replace("/", os.sep))
        if not os.path.exists(b):
            continue
        tl = readlines(p)
        bl = readlines(b)[skip:]
        d = list(difflib.unified_diff(
            tl, bl,
            fromfile="tree/" + rel, tofile="backup[%d:]/%s" % (skip, rel),
            n=2))
        name = rel.replace("/", "_") + ".diff.txt"
        with io.open(os.path.join(OUT, name), "w", encoding="utf-8", newline="\n") as f:
            f.write("".join(d))
        print("%-45s tree=%-5d bak=%-5d difflines=%d" % (rel, len(tl), len(bl), len(d)))


if __name__ == "__main__":
    main()
