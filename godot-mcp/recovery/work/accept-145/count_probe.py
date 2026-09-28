#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import io, json, os, collections
ROOT = r"F:\moonbit-hof-rs\godot-mcp"
d = json.load(io.open(os.path.join(ROOT, "recovery", "work", "task143", "probe-live.json"), "r", encoding="utf-8"))
tools = d["tools"]
verdicts = collections.Counter(t.get("verdict") for t in tools.values())
kinds = collections.Counter(t.get("probe_kind") for t in tools.values())
refused = sorted(k for k, v in tools.items() if v.get("verdict") == "refused_-32602")
not_probed = sorted(k for k, v in tools.items() if v.get("verdict") == "not_probed")
refused_kinds = collections.Counter(tools[k].get("probe_kind") for k in refused)
# which refused tools have "Missing required" message vs other
msg_kind = collections.Counter()
for k in refused:
    m = tools[k].get("error_message") or ""
    if m.startswith("Missing required"):
        msg_kind["missing_required"] += 1
    elif m.startswith("Unknown parameter"):
        msg_kind["unknown_parameter"] += 1
    elif "must be" in m or "must not" in m or "is not a valid" in m or "must name" in m:
        msg_kind["type_or_value_rule"] += 1
    else:
        msg_kind["other"] += 1
out = {"counters": d.get("counters"), "harness": d.get("harness"),
       "verdicts": dict(verdicts), "probe_kinds": dict(kinds),
       "refused_kinds": dict(refused_kinds), "refused_message_kinds": dict(msg_kind),
       "n_refused": len(refused), "n_not_probed": len(not_probed),
       "not_probed": {k: tools[k].get("why") for k in not_probed},
       "refused_names": refused}
with io.open(os.path.join(os.path.dirname(os.path.abspath(__file__)), "probe_counts.json"), "w", encoding="utf-8", newline="\n") as h:
    h.write(json.dumps(out, ensure_ascii=False, indent=2))
print(json.dumps({k: out[k] for k in ("counters", "verdicts", "probe_kinds", "refused_message_kinds", "n_refused", "n_not_probed")}, ensure_ascii=False, indent=2))
