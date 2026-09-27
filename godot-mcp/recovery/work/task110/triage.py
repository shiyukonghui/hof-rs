#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""TASK-110 defect triage: read specific saved calls from a run and print the
request arguments next to the response body, plus what the contract declares.

Usage: python triage.py <run-rel> <tag-substring> [<tag-substring> ...]
"""
import io
import json
import os
import sys

ROOT = r"F:\moonbit-hof-rs\godot-mcp"
CONTRACT = os.path.join(ROOT, "godot", "modules", "mcp_server", "docs", "tools_list.renamed.json")
with io.open(CONTRACT, "r", encoding="utf-8") as h:
    CONTRACT_DOC = json.load(h)
SCHEMAS = {t["name"]: t.get("inputSchema") for t in CONTRACT_DOC["result"]["tools"]}

run = os.path.join(ROOT, sys.argv[1])
needles = sys.argv[2:]
for fname in sorted(os.listdir(run)):
    if not fname.endswith(".request.json"):
        continue
    tag = fname[:-len(".request.json")]
    if not any(n in tag for n in needles):
        continue
    with io.open(os.path.join(run, fname), "r", encoding="utf-8-sig") as h:
        req = json.loads(h.read())
    params = req.get("params") or {}
    tool = params.get("name")
    args = params.get("arguments")
    print("=" * 100)
    print("TAG  :", tag)
    print("TOOL :", tool)
    print("ARGS :", json.dumps(args, ensure_ascii=False)[:400])
    sch = SCHEMAS.get(tool) or {}
    print("SCHEMA required=%s" % (sch.get("required"),))
    for k, v in sorted((sch.get("properties") or {}).items()):
        print("        %-16s %s" % (k, json.dumps(v, ensure_ascii=False)[:220]))
    rp = os.path.join(run, tag + ".json")
    if os.path.isfile(rp):
        with io.open(rp, "r", encoding="utf-8-sig", errors="replace") as h:
            raw = h.read()
        try:
            doc = json.loads(raw)
        except ValueError:
            print("RESP : <unparseable>", raw[:200])
            continue
        if "error" in doc:
            print("RESP : ERROR", json.dumps(doc["error"], ensure_ascii=False)[:600])
        else:
            text = ""
            try:
                text = doc["result"]["content"][0]["text"]
            except Exception:
                text = json.dumps(doc)[:400]
            print("RESP : OK", text[:600])
