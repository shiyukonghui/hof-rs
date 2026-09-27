#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""TASK-111: why does the ledger flag editor_get_tilemap_used_cells as result_unparseable?"""
import io
import json

PATH = r"F:\moonbit-hof-rs\godot-mcp\runs\_exercises\ex_grid\h3-task111\trace-editor.jsonl"

with io.open(PATH, "r", encoding="utf-8") as handle:
    for line in handle:
        if "editor_get_tilemap_used_cells" not in line:
            continue
        doc = json.loads(line)
        for key in sorted(doc):
            value = doc[key]
            if isinstance(value, str):
                value = value[:120].replace("\n", " ")
            print("%-28s %s" % (key, value))
        raw = doc.get("result_json")
        if isinstance(raw, str):
            print("--- result_json len=%d tail=%s" % (len(raw), raw[-80:].replace("\n", " ")))
            try:
                json.loads(raw)
                print("--- parses OK")
            except ValueError as exc:
                print("--- parse error: %s" % exc)
        break
