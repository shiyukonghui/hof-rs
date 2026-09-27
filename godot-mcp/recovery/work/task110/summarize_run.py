#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""TASK-110: read the batch run's own results without dumping the whole log.

Answers, per tool: calls, ok, failed, and the failing tools' error codes/messages
straight from the run's saved `<tag>.json` responses (the driver writes one file
per call). No shell redirection: this script owns its writes.
"""
import io
import json
import os
import sys

ROOT = r"F:\moonbit-hof-rs\godot-mcp"
runs = sys.argv[1:] or ["runs/_exercises/ex_files/c1-task110"]
out_lines = []
for rel in runs:
    d = os.path.join(ROOT, rel)
    if not os.path.isdir(d):
        print("missing run dir: %s" % d)
        continue
    idx = os.path.join(d, "call-index.txt")
    tags = []
    if os.path.isfile(idx):
        with io.open(idx, "r", encoding="utf-8-sig", errors="replace") as h:
            for line in h:
                parts = line.rstrip("\n").split("|")
                if parts and parts[0]:
                    tags.append(parts[0])
    print("== %s : %d calls ==" % (rel, len(tags)))
    fails = []
    for tag in tags:
        jp = os.path.join(d, tag + ".json")
        if not os.path.isfile(jp):
            fails.append((tag, "NO_RESPONSE_FILE", ""))
            continue
        with io.open(jp, "r", encoding="utf-8-sig", errors="replace") as h:
            raw = h.read()
        try:
            doc = json.loads(raw)
        except ValueError:
            fails.append((tag, "UNPARSEABLE", raw[:120]))
            continue
        if isinstance(doc, dict) and "error" in doc:
            err = doc["error"]
            data = err.get("data") or {}
            fails.append((tag, str(err.get("code")), (err.get("message") or "")[:150],
                          (data.get("suggestion") or "")[:150]))
    print("failures: %d / %d" % (len(fails), len(tags)))
    for item in fails:
        sys.stdout.write("  %-60s %s\n" % (item[0], " | ".join(str(x) for x in item[1:])))
