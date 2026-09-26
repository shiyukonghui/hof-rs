# -*- coding: utf-8 -*-
"""TASK-096: build the round-2 replay session for the Tetris project.

Round 1 built the project and the scene (and recorded two payload defects, T-1 and
T-2, plus one test-design defect, T-3). Round 2 must NOT re-run the scene-building
editor calls: `editor_add_nodes_batch` + `editor_save_scene` on a scene that already
has those names is exactly what polluted Pong / Breakout / Snake (see D-1 in
GAME-LOOP-LOG.md). So round 2 replays only: edit the two scripts, rebuild, validate,
then the whole game phase.
"""
import io
import json
import sys


def main(src, dst):
    with io.open(src, "r", encoding="utf-8") as handle:
        doc = json.load(handle)

    editor = [
        {"tag": "r01-edit-tetromino", "port": "editor", "tool": "project_edit_script",
         "arguments": {"path": "res://src/Tetromino.cs", "content_file": "payload/Tetromino.cs"},
         "note": "round 2: rewrite (never create) the shape table"},
        {"tag": "r02-edit-game", "port": "editor", "tool": "project_edit_script",
         "arguments": {"path": "res://src/TetrisGame.cs", "content_file": "payload/TetrisGame.cs"},
         "note": "round 2: the two payload fixes (T-1: WriteBoard accepts '|'; T-2: HardDrop reports the post-lock state)"},
        {"tag": "r03-build-csharp", "port": "editor", "tool": "project_build_csharp",
         "arguments": {"configuration": "Debug", "timeout_ms": 300000, "rescan": True},
         "note": "the .NET build, driven by MCP"},
        {"tag": "r04-validate-scripts", "port": "editor", "tool": "project_validate_scripts",
         "arguments": {"paths": ["res://src/Tetromino.cs", "res://src/TetrisGame.cs"]},
         "note": "per-file verdict after the fix"},
        {"tag": "r05-errors", "port": "editor", "tool": "editor_get_errors",
         "arguments": {}, "note": "editor log read"},
        {"tag": "r06-scene-still-clean", "port": "editor", "tool": "editor_get_scene_tree",
         "arguments": {}, "note": "the scene must be the same 4-node scene: no @ColorRect@ duplicate may exist"},
    ]
    game = [c for c in doc["calls"] if c.get("port") == "game"]

    out = {
        "_comment": "TASK-096 round 2 -- the defect-fix replay. The scene-building calls are deliberately absent: "
                    "re-running editor_add_nodes_batch + editor_save_scene on a populated scene is what created the "
                    "duplicate @ColorRect@ layer that D-1 is (GAME-LOOP-LOG.md). Only the scripts are rewritten.",
        "game": "tetris",
        "import": False,
        "calls": editor + game,
    }
    with io.open(dst, "w", encoding="utf-8", newline="\n") as handle:
        handle.write(json.dumps(out, ensure_ascii=False, indent=2) + "\n")
    print("wrote %s: editor=%d game=%d total=%d" % (dst, len(editor), len(game), len(out["calls"])))
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1], sys.argv[2]))
