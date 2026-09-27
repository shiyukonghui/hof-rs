#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""TASK-118: print the verbatim payloads the report quotes."""
import io
import json
import os

ROOT = r"F:\moonbit-hof-rs\godot-mcp"
ITEMS = [
    ("runs/_exercises/ex_grid/c6-task118", "c6-009-editor_get_scene_tree-witness"),
    ("runs/_exercises/ex_grid/c6-task118", "c6-016-editor_execute_gdscript-witness"),
    ("runs/_exercises/ex_grid/c6-task118", "c6-023-editor_list_signal_connections-witness"),
    ("runs/_exercises/ex_grid/c6-task118", "c6-024-running_game_find_node_when_available-ok"),
    ("runs/_exercises/ex_grid/c6-task118", "c6-029-running_game_find_node_when_available-probe"),
    ("runs/_exercises/ex_grid/c7-task118", "c7-001-os_list_android_devices-ok"),
    ("runs/_exercises/ex_grid/c7-task118", "c7-007-project_get_android_preset_info-ok"),
    ("runs/_exercises/ex_grid/c7-task118", "c7-013-os_deploy_to_android_device-probe"),
]


def main():
    for run, name in ITEMS:
        path = os.path.join(ROOT, run, name + ".json")
        with io.open(path, "r", encoding="utf-8-sig") as fh:
            doc = json.load(fh)
        if "result" in doc:
            text = doc["result"]["content"][0]["text"]
        else:
            text = json.dumps(doc.get("error"), ensure_ascii=False)
        print("%s :: %s" % (name, text[:600]))
        print()


if __name__ == "__main__":
    main()
