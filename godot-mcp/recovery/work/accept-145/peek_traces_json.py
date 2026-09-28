#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import io, json, os
p = r"F:\moonbit-hof-rs\godot-mcp\recovery\work\task143\traces.json"
d = json.load(io.open(p, "r", encoding="utf-8"))
print("top keys:", list(d.keys()))
print("calls:", d.get("calls"), "trace_files:", d.get("trace_files"), "malformed:", d.get("malformed"))
tools = d["tools"]
print("n tools:", len(tools))
for k in ("project_get_filesystem_tree", "editor_add_audio_bus", "editor_simulate_mouse_click", "project_set_setting"):
    print("----", k)
    print(json.dumps(tools.get(k), ensure_ascii=False)[:1200])
