#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Find one ok=true trace record for a sample of tools and show its shape."""
import io, json, os, glob
ROOT = r"F:\moonbit-hof-rs\godot-mcp"
targets = ["project_get_filesystem_tree", "editor_add_audio_bus", "editor_add_node"]
found = {}
for f in glob.glob(os.path.join(ROOT, "runs", "**", "trace-*.jsonl"), recursive=True):
    try:
        with io.open(f, "r", encoding="utf-8", errors="replace") as h:
            for ln, line in enumerate(h, 1):
                line = line.strip()
                if not line or '"tool"' not in line:
                    continue
                try:
                    r = json.loads(line)
                except Exception:
                    continue
                t = r.get("tool")
                if t in targets and r.get("ok") is True and r.get("method") == "tools/call" and t not in found:
                    found[t] = {"file": f, "line": ln, "keys": sorted(r.keys()),
                                "result_bytes": r.get("result_bytes")}
    except Exception as e:
        pass
    if len(found) == len(targets):
        break
with io.open(os.path.join(os.path.dirname(os.path.abspath(__file__)), "ok_trace_shape.json"), "w", encoding="utf-8", newline="\n") as h:
    h.write(json.dumps(found, ensure_ascii=False, indent=2))
print(json.dumps(found, ensure_ascii=False, indent=2))
