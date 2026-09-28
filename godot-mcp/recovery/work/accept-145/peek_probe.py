#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import io, json, os, collections, re
ROOT = r"F:\moonbit-hof-rs\godot-mcp"
p = os.path.join(ROOT, "recovery", "work", "task143", "probe-live.json")
d = json.load(io.open(p, "r", encoding="utf-8"))
print("top:", list(d.keys()))
for k, v in d.items():
    if not isinstance(v, (dict, list)):
        print("  %s = %s" % (k, v))
tools = d.get("tools") or {}
print("n tools entries:", len(tools))
kinds = collections.Counter()
probed = []
not_probed = []
for name, rec in tools.items():
    if rec.get("probed") or rec.get("status") == "probed" or rec.get("code") == -32602:
        probed.append(name)
    if rec.get("not_probed") or rec.get("status") == "not_probed":
        not_probed.append(name)
print("probed-ish:", len(probed), "not_probed-ish:", len(not_probed))
sample_keys = list(tools.items())[:3]
out = {"top": {k: (v if not isinstance(v, (dict, list)) else "<%s len=%d>" % (type(v).__name__, len(v))) for k, v in d.items()},
       "first3": sample_keys,
       "not_probed_names": sorted(not_probed)}
with io.open(os.path.join(os.path.dirname(os.path.abspath(__file__)), "probe_live_peek.json"), "w", encoding="utf-8", newline="\n") as h:
    h.write(json.dumps(out, ensure_ascii=False, indent=2)[:200000])
print("not_probed names:", len(not_probed))
