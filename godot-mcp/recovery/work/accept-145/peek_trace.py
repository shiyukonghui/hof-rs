#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import io, json, os
p = r"F:\moonbit-hof-rs\godot-mcp\runs\_exercises\ex_files\c1-task110\trace-editor.jsonl"
with io.open(p, "r", encoding="utf-8") as h:
    lines = h.readlines()
print("nlines", len(lines))
for ln in (131, 132):
    if ln < len(lines):
        print("---- line", ln + 1, "----")
        print(lines[ln].strip()[:1500])
