#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import io, json, os
ch = json.load(io.open(r"F:\moonbit-hof-rs\godot-mcp\tools\tool_channels.json", "r", encoding="utf-8"))
out = {"top": {k: (v if not isinstance(v, (dict, list)) else "<%s len=%d>" % (type(v).__name__, len(v))) for k, v in ch.items()},
       "channels_type": type(ch["channels"]).__name__}
if isinstance(ch["channels"], dict):
    ks = list(ch["channels"].keys())[:5]
    out["sample_keys"] = ks
    out["sample"] = {k: ch["channels"][k] for k in ks}
elif isinstance(ch["channels"], list):
    out["sample"] = ch["channels"][:5]
out["channel_counts"] = ch.get("channel_counts")
with io.open(r"F:\moonbit-hof-rs\godot-mcp\recovery\work\accept-145\channels_peek.json", "w", encoding="utf-8", newline="\n") as h:
    h.write(json.dumps(out, ensure_ascii=False, indent=2))
print("done")
