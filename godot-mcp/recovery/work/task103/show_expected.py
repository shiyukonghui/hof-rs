#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""TASK-103 scratch: print the expected value of chosen assertion tags of a session."""
import io
import json
import os
import sys

ROOT = r"F:\moonbit-hof-rs\godot-mcp"


def main():
    path = sys.argv[1]
    if not os.path.isabs(path):
        path = os.path.join(ROOT, path)
    wanted = set(sys.argv[2].split(","))
    with io.open(path, encoding="utf-8") as handle:
        doc = json.load(handle)
    for call in doc["calls"]:
        tag = call.get("tag")
        if tag in wanted:
            args = call.get("arguments", {})
            print("%-34s %-22s %-4s %r" % (tag, args.get("property"), args.get("operator"), args.get("expected")))
        elif call.get("tool") == "running_game_execute_gdscript" and any(w in call.get("tag", "") for w in wanted):
            print("%-34s CODE %s" % (tag, args.get("code", "").replace("\n", "\\n")[:200]))
        elif call.get("tool") == "running_game_capture_screenshot" and tag in wanted:
            print("%-34s SHOT %s" % (tag, args.get("save_path")))


if __name__ == "__main__":
    main()
