#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""TASK-103 scratch: print the full call objects of a session for chosen tools/tags."""
import io
import json
import os
import sys

ROOT = r"F:\moonbit-hof-rs\godot-mcp"


def main():
    path = sys.argv[1]
    if not os.path.isabs(path):
        path = os.path.join(ROOT, path)
    wanted = sys.argv[2].split(",")
    with io.open(path, encoding="utf-8") as handle:
        doc = json.load(handle)
    seen = set()
    for call in doc.get("calls", []):
        tool = call.get("tool", "")
        tag = call.get("tag", "")
        if tag in wanted or tool in wanted:
            if tool in wanted and tool in seen:
                continue
            seen.add(tool)
            print(json.dumps(call, ensure_ascii=False, indent=1)[:2500])
            print("---")


if __name__ == "__main__":
    main()
