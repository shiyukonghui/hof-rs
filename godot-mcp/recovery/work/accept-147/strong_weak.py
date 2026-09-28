#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""TASK-147 B5 (independent): derive the strong/weak negative split from the raw artefacts.

A tool counts as having a STRONG negative when it has at least one of:
  * a failed trace call whose error_code is a real contract code (-32602/-32001/-32000/...)
    recorded in the corpus (coverage.json tracks failures per tool, runs/**/*.jsonl carry them);
  * the TASK-143 live probe refused it with -32602 AND the message came from the
    handler-side readers (`Missing required parameter:` / `Parameter '...' must be`);
  * a ledger boundary >= 1.
A tool whose only negative is the registry's unknown-argument gate
(`Unknown parameter '<x>' for tool ...`) counts as WEAK.
"""
import io, json, re, os, collections

cov = json.load(io.open("coverage.json", encoding="utf-8"))
tools = {t["tool"]: t for t in cov["tools"]}
probe = json.load(io.open("recovery/work/task143/probe-live.json", encoding="utf-8"))["tools"]
u2 = json.load(io.open("recovery/work/task144/probe-u2.json", encoding="utf-8"))

# --- trace failures per tool, scanned straight from the corpus ---
failed_codes = collections.defaultdict(list)
n_lines = 0
for root, _dirs, files in os.walk("runs"):
    for fn in files:
        if not (fn.startswith("trace-") and fn.endswith(".jsonl")):
            continue
        for raw in io.open(os.path.join(root, fn), encoding="utf-8", errors="replace"):
            raw = raw.strip()
            if not raw:
                continue
            n_lines += 1
            try:
                rec = json.loads(raw)
            except Exception:
                continue
            if rec.get("ok") is False and rec.get("error_code") is not None:
                failed_codes[rec.get("tool")].append(rec["error_code"])
print("trace lines scanned: %d, tools with failed calls: %d" % (n_lines, len(failed_codes)))

REGISTRY_GATE = "Unknown parameter '"
handler_probe = {}
weak_probe = {}
for name, rec in probe.items():
    if rec.get("verdict") != "refused_-32602":
        continue
    msg = rec.get("error_message") or ""
    if msg.startswith(REGISTRY_GATE):
        weak_probe[name] = msg
    else:
        handler_probe[name] = msg

strong = []
weak_only = []
none_at_all = []
for name in sorted(tools):
    t = tools[name]
    has_trace = bool(failed_codes.get(name))
    has_handler_probe = name in handler_probe
    has_boundary = (t.get("boundary") or 0) >= 1
    has_weak_probe = name in weak_probe
    if has_trace or has_handler_probe or has_boundary:
        strong.append(name)
    elif has_weak_probe:
        weak_only.append(name)
    else:
        none_at_all.append(name)

print("\nSTRONG-negatives (trace failure / handler-side -32602 / boundary>=1): %d" % len(strong))
print("WEAK-only (registry unknown-argument gate only)                  : %d -> %s"
      % (len(weak_only), weak_only))
print("NO negative at all                                              : %d -> %s"
      % (len(none_at_all), none_at_all))
print("total tools: %d" % len(tools))
print()
print("handler-side probe families:")
fam = collections.Counter()
for name, msg in handler_probe.items():
    fam["missing_required" if msg.startswith("Missing required parameter:") else
        ("wrong_type" if msg.startswith("Parameter '") and "must be" in msg else "other")] += 1
print("  ", dict(fam))
print("   probe-live entries not in the handler families:")
for name, msg in handler_probe.items():
    if not (msg.startswith("Missing required parameter:") or
            (msg.startswith("Parameter '") and "must be" in msg)):
        print("     %s -> %r" % (name, msg))
print()
print("weak probe names:", sorted(weak_probe))
print("trace-failure sweeps sample:", {k: collections.Counter(v) for k, v in list(failed_codes.items())[:3]})
