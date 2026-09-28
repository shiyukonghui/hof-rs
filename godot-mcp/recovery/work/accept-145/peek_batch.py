#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import io, json, os
ROOT = r"F:\moonbit-hof-rs\godot-mcp"
for name in ("batch-before.json", "batch-after.json"):
    d = json.load(io.open(os.path.join(ROOT, "recovery", "work", "task144", name), "r", encoding="utf-8"))
    print(name, "top:", list(d.keys()))
    r0 = d["results"][0]
    print("  result keys:", list(r0.keys()))
    print("  counts:", {k: d.get(k) for k in ("targets", "passed", "failed", "targets_pass", "targets_fail", "fail", "pass") if k in d})
