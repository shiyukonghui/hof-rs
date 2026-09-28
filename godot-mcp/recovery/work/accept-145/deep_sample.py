#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Independent re-derivation of the trace corpus + deep check of sampled matrix rows."""
import io
import json
import os
import re

ROOT = r"F:\moonbit-hof-rs\godot-mcp"
RUNS = os.path.join(ROOT, "runs")
MATRIX = os.path.join(ROOT, "recovery", "TEST-CASES.md")
OUT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "deep_sample.json")

SAMPLE = ["project_get_info", "project_get_filesystem_tree", "project_search_file_names",
          "project_set_setting", "project_get_settings", "editor_add_audio_bus",
          "editor_add_node", "editor_open_scene", "editor_get_selection",
          "editor_set_node_selection", "editor_simulate_mouse_click",
          "editor_simulate_mouse_move", "editor_set_auto_dismiss_dialogs",
          "project_get_android_preset_info", "os_deploy_to_android_device"]

# ---- (a) independent walk -------------------------------------------------
facts = {}
files = 0
calls = 0
malformed = 0
for base, _dirs, names in os.walk(RUNS):
    for name in sorted(n for n in names if n.startswith("trace-") and n.endswith(".jsonl")):
        files += 1
        rel = os.path.relpath(os.path.join(base, name), ROOT).replace("\\", "/")
        with io.open(os.path.join(base, name), "r", encoding="utf-8", errors="replace") as h:
            for lineno, line in enumerate(h, 1):
                line = line.strip()
                if not line:
                    continue
                if rel.endswith("trace-editor.jsonl") and "copy" in name:
                    pass
                try:
                    rec = json.loads(line)
                except ValueError:
                    malformed += 1
                    continue
                tool = rec.get("tool")
                if not tool or "ok" not in rec:
                    continue
                calls += 1
                f = facts.setdefault(tool, {"calls": 0, "ok": 0, "failed": 0, "codes": {},
                                            "first_neg": None, "success_keys": None,
                                            "success_pointer": None})
                f["calls"] += 1
                if rec.get("ok") is True:
                    f["ok"] += 1
                    raw = rec.get("result_json")
                    if f["success_keys"] is None and isinstance(raw, str) and raw.strip():
                        try:
                            body = json.loads(raw)
                        except ValueError:
                            body = None
                        if isinstance(body, dict):
                            f["success_keys"] = sorted(body.keys())
                            f["success_pointer"] = "%s:%d" % (rel, lineno)
                        elif isinstance(body, list):
                            f["success_keys"] = ["<array len=%d>" % len(body)]
                            f["success_pointer"] = "%s:%d" % (rel, lineno)
                else:
                    f["failed"] += 1
                    code = rec.get("error_code")
                    if code:
                        f["codes"][str(code)] = f["codes"].get(str(code), 0) + 1
                        if f["first_neg"] is None:
                            f["first_neg"] = {"code": code, "message": rec.get("error_message") or "",
                                              "pointer": "%s:%d" % (rel, lineno)}

# ---- (b) compare with the claimed traces.json -----------------------------
claimed = json.load(io.open(os.path.join(ROOT, "recovery", "work", "task143", "traces.json"),
                            "r", encoding="utf-8"))
diff = []
for tool, cf in claimed["tools"].items():
    mf = facts.get(tool)
    if mf is None:
        diff.append({"tool": tool, "what": "claimed but not found in my walk"})
        continue
    for k, ck in (("calls", "calls"), ("ok", "ok"), ("failed", "failed")):
        if cf.get(ck) != mf.get(k):
            diff.append({"tool": tool, "what": k, "claimed": cf.get(ck), "mine": mf.get(k)})
    if cf.get("success_keys") != mf.get("success_keys"):
        diff.append({"tool": tool, "what": "success_keys", "claimed": cf.get("success_keys"),
                     "mine": mf.get("success_keys")})
for tool in set(facts) - set(claimed["tools"]):
    diff.append({"tool": tool, "what": "in my walk but not claimed"})

# ---- matrix rows ----------------------------------------------------------
lines = io.open(MATRIX, "r", encoding="utf-8").read().split("\n")
rows = {}
for i, l in enumerate(lines, 1):
    if l.startswith("| TC-TOOL-"):
        cells = [c.strip() for c in l.strip().strip("|").split("|")]
        if len(cells) == 9:
            rows[cells[1].strip("`")] = {"line": i, "cells": cells}

CH_ABBR = {"editor_state": "state", "pixel_effect": "pixel", "file_effect": "file", "payload": "payload"}
channels = json.load(io.open(os.path.join(ROOT, "tools", "tool_channels.json"), "r", encoding="utf-8"))["channels"]
covrows = {r["tool"]: r for r in json.load(
    io.open(os.path.join(ROOT, "coverage.json"), "r", encoding="utf-8"))["tools"]}

deep = {}
chan_bad = []
for tool, r in rows.items():
    ch = (channels.get(tool) or {}).get("channel")
    out = r["cells"][5]
    if ch and ("回读=%s/" % CH_ABBR[ch]) not in out:
        chan_bad.append({"tool": tool, "channel": ch, "out": out[:120]})

for tool in SAMPLE:
    r = rows.get(tool)
    rec = {"matrix_line": r["line"] if r else None}
    if r:
        in_cell, out_cell, neg = r["cells"][4], r["cells"][5], r["cells"][6]
        rec["in"] = in_cell
        rec["out"] = out_cell
        rec["neg"] = neg
        rec["state"] = r["cells"][7]
        rec["note"] = r["cells"][8]
        m = re.search(r"成功=\{([^}]*)\}", out_cell)
        rec["matrix_success"] = sorted(x.strip() for x in m.group(1).split(",")) if m else None
        mc = re.search(r"错误码=(-?\d+)", out_cell)
        rec["matrix_error_code"] = int(mc.group(1)) if mc else None
    f = facts.get(tool)
    rec["trace_facts"] = f
    cov = covrows.get(tool) or {}
    rec["ledger"] = {k: cov.get(k) for k in ("calls", "ok", "boundary", "effective", "evidence_channel",
                                             "channel_evidence", "channel_evidence_ok", "status",
                                             "ledger_class", "scope")}
    rec["channel_declared"] = (channels.get(tool) or {}).get("channel")
    if f and rec.get("matrix_success") is not None:
        rec["success_keys_match"] = (rec["matrix_success"] == f["success_keys"])
    if f and rec.get("matrix_error_code") is not None:
        rec["error_code_seen_in_trace"] = str(rec["matrix_error_code"]) in (f["codes"] or {})
    deep[tool] = rec

out = {"independent_walk": {"files": files, "calls": calls, "malformed": malformed,
                            "tools_with_facts": len(facts),
                            "tools_with_failed_call": sum(1 for f in facts.values() if f["failed"]),
                            "tools_with_success_keys": sum(1 for f in facts.values() if f["success_keys"])},
       "claimed_traces_json": {"trace_files": claimed["trace_files"], "calls": claimed["calls"],
                               "malformed": claimed["malformed"], "tools": len(claimed["tools"])},
       "trace_json_diffs": diff,
       "channel_abbrev_mismatches": chan_bad,
       "deep_sample": deep}
with io.open(OUT, "w", encoding="utf-8", newline="\n") as h:
    h.write(json.dumps(out, ensure_ascii=False, indent=2))

print(json.dumps(out["independent_walk"], ensure_ascii=False))
print("claimed:", json.dumps(out["claimed_traces_json"], ensure_ascii=False))
print("trace_json_diffs:", len(diff))
for d in diff[:15]:
    print("  ", json.dumps(d, ensure_ascii=False)[:300])
print("channel_abbrev_mismatches:", len(chan_bad))
for d in chan_bad[:15]:
    print("  ", json.dumps(d, ensure_ascii=False)[:200])
for t in SAMPLE:
    r = deep[t]
    print("SAMPLE", t, "success_match=", r.get("success_keys_match"),
          "code_seen=", r.get("error_code_seen_in_trace"),
          "ledger=", json.dumps(r["ledger"], ensure_ascii=False))
