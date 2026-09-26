#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""TASK-103 scratch: print the tag/tool/port of every call of a session file."""
import io
import json
import os
import sys

ROOT = r"F:\moonbit-hof-rs\godot-mcp"


def main():
    path = sys.argv[1]
    if not os.path.isabs(path):
        path = os.path.join(ROOT, path)
    with io.open(path, encoding="utf-8") as handle:
        doc = json.load(handle)
    for call in doc.get("calls", []):
        if "sleep_ms" in call:
            print("%-28s sleep %s" % (call.get("tag", ""), call["sleep_ms"]))
            continue
        print("%-28s %-26s %s" % (call.get("tag", ""), call.get("tool", call.get("method", "")), call.get("port", "")))
    print("TOTAL %d" % len(doc.get("calls", [])))


if __name__ == "__main__":
    main()
