#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""TASK-147 B5: independently recount the -32602 message families in the live probe."""
import io, json, collections, re, sys

p = "recovery/work/task143/probe-live.json"
d = json.load(io.open(p, encoding="utf-8"))
print("top-level keys:", sorted(d.keys())[:20] if isinstance(d, dict) else type(d))
tools = d.get("tools", d)
print("n tools:", len(tools))

kinds = collections.Counter()
msgmap = collections.defaultdict(list)
for name, rec in sorted(tools.items()):
    if not isinstance(rec, dict):
        continue
    code = rec.get("code")
    msg = rec.get("message") or ""
    if code == -32602:
        if msg.startswith("Missing required parameter:"):
            k = "missing_required"
        elif msg.startswith("Parameter '") and "must be" in msg:
            k = "wrong_type"
        elif msg.startswith("Unknown parameter"):
            k = "unknown_parameter"
        else:
            k = "other:" + msg[:40]
        kinds[k] += 1
        msgmap[k].append(name)
print("\n-32602 message families in probe-live.json:")
for k, v in kinds.most_common():
    print("  %-30s %d" % (k, v))
print()
for k in sorted(msgmap):
    print("  %s: %s" % (k, ", ".join(msgmap[k][:8]) + (" ..." if len(msgmap[k]) > 8 else "")))

p2 = "recovery/work/task144/probe-u2.json"
d2 = json.load(io.open(p2, encoding="utf-8"))
print("\n--- probe-u2.json ---")
print(json.dumps(d2, ensure_ascii=False, indent=1)[:3000])
