# -*- coding: utf-8 -*-
"""Scratch: does the ledger's own channel_evidence_count() reproduce the
channel_evidence stored in coverage.json for all 177 rows? (TASK-144 A)"""
import io
import json
import os
import sys

ROOT = os.path.abspath(os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", ".."))
sys.path.insert(0, os.path.join(ROOT, "tools"))
import tool_coverage as tc  # noqa: E402

cov = json.load(io.open(os.path.join(ROOT, "coverage.json"), encoding="utf-8"))
names = tc.contract_tools(ROOT)
_scopes, verbs = tc.scope_and_verb(ROOT)
channels, _doc = tc.load_channels(ROOT, names, verbs)

bad = []
for row in cov["tools"]:
    st = {"pixel_effect": row.get("pixel_effect_calls", 0),
          "file_effect": row.get("file_effect_calls", 0),
          "read_payload": row.get("read_payload_calls", 0)}
    ev = tc.channel_evidence_count(st, channels[row["tool"]]["channel"], row.get("readback"))
    if ev != row.get("channel_evidence") or channels[row["tool"]]["channel"] != row.get("evidence_channel"):
        bad.append((row["tool"], ev, row.get("channel_evidence"),
                    channels[row["tool"]]["channel"], row.get("evidence_channel")))

print("rows=%d mismatch=%d" % (len(cov["tools"]), len(bad)))
for item in bad[:10]:
    print("  %s" % (item,))
