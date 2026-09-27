#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""TASK-110 recon: show the shape of the scope sources (read-only)."""
import io
import json
import os

D = r"F:\moonbit-hof-rs\godot-mcp\godot\modules\mcp_server\docs"


def peek(name, limit=2):
    p = os.path.join(D, name)
    with io.open(p, "r", encoding="utf-8") as h:
        doc = json.load(h)
    print("== %s ==" % name)
    if isinstance(doc, dict):
        print("  top keys:", sorted(doc.keys()))
        for k, v in sorted(doc.items()):
            if isinstance(v, list):
                print("  %s: list[%d]" % (k, len(v)))
                for item in v[:limit]:
                    print("     sample:", json.dumps(item, ensure_ascii=False)[:300])
            elif isinstance(v, dict):
                print("  %s: dict keys=%s" % (k, sorted(v.keys())[:10]))
            else:
                print("  %s: %r" % (k, v))


for n in ("tool-rename-map.json", "tool-groups.json", "tool-groups-added.json",
          "tool-groups-b2.json", "tool-groups-b3.json", "tool-groups-b4.json", "tool-groups-b5.json"):
    try:
        peek(n)
    except Exception as exc:  # noqa
        print("== %s == FAILED %s" % (n, exc))
