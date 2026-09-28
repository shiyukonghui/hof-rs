#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""TASK-149: print the real shape of the probe evidence files (read-only, stdout only)."""
from __future__ import print_function

import io
import json
import os

ROOT = r"F:\moonbit-hof-rs\godot-mcp"


def main():
    for rel in ("recovery/work/task143/probe-live.json",
                "recovery/work/task144/probe-u2.json"):
        path = os.path.join(ROOT, rel.replace("/", os.sep))
        with io.open(path, "r", encoding="utf-8") as handle:
            doc = json.load(handle)
        print("=" * 78)
        print(rel)
        print("  doc keys: %s" % sorted(doc.keys()))
        tools = doc.get("tools")
        print("  tools type: %s, n=%s" % (type(tools).__name__,
                                          len(tools) if hasattr(tools, "__len__") else "?"))
        if isinstance(tools, dict):
            for i, (name, probe) in enumerate(tools.items()):
                if i >= 2:
                    break
                print("  sample %s -> keys=%s" % (name, sorted(probe.keys())))
                print("    %s" % json.dumps(probe, ensure_ascii=False)[:600])
        elif isinstance(tools, list):
            for i, probe in enumerate(tools[:2]):
                print("  sample[%d] keys=%s" % (i, sorted(probe.keys())))
                print("    %s" % json.dumps(probe, ensure_ascii=False)[:600])
        for key in ("undeclared_argument", "targets", "counters"):
            if key in doc:
                print("  %s = %s" % (key, json.dumps(doc[key], ensure_ascii=False)[:400]))


if __name__ == "__main__":
    main()
