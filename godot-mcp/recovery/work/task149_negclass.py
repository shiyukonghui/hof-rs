#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""TASK-149: recompute the `-32602` provenance split from the ORIGINAL evidence.

Evidence inputs (read-only):
  * recovery/work/task143/probe-live.json -- TASK-143 live probe of the 177 tools;
  * recovery/work/task144/probe-u2.json   -- TASK-144's two mouse probes.

Output: per-message-kind totals for every live -32602, and the same split restricted to
`editor_simulate_mouse_click` / `editor_simulate_mouse_move`.

No shell redirection; everything is printed to stdout by this process.
"""
from __future__ import print_function

import io
import json
import os
import re

ROOT = r"F:\moonbit-hof-rs\godot-mcp"
MISSING_COLON_RE = re.compile(r"^Missing required parameter: ")
MISSING_NO_COLON_RE = re.compile(r"^Missing required parameter '")
WRONG_TYPE_RE = re.compile(r"^Parameter '[^']*' must be\b")
UNKNOWN_ARG_RE = re.compile(r"^Unknown parameter ")

CATEGORIES = ("missing_required_colon", "missing_required_no_colon", "wrong_type",
              "unknown_argument", "other")


def kind_of(message):
    m = "%s" % (message or "")
    if MISSING_COLON_RE.match(m):
        return "missing_required_colon"
    if MISSING_NO_COLON_RE.match(m):
        return "missing_required_no_colon"
    if WRONG_TYPE_RE.match(m):
        return "wrong_type"
    if UNKNOWN_ARG_RE.match(m):
        return "unknown_argument"
    return "other"


def collect_entries(doc):
    """[(tool_name, code, message)] from either probe file's `tools` map."""
    out = []
    tools = doc.get("tools") or {}
    if isinstance(tools, dict):
        items = tools.items()
    else:
        items = [("%s" % i, v) for i, v in enumerate(tools)]
    for name, probe in items:
        if not isinstance(probe, dict):
            continue
        code = probe.get("code", probe.get("error_code"))
        message = probe.get("message", probe.get("error_message", ""))
        if isinstance(probe.get("error"), dict):
            code = probe["error"].get("code", code)
            message = probe["error"].get("message", message)
        out.append((name, code, "%s" % (message or "")))
    return out


def main():
    grand = dict((c, 0) for c in CATEGORIES)
    per_source = {}
    for label, rel in (("TASK-143 probe-live.json", "recovery/work/task143/probe-live.json"),
                       ("TASK-144 probe-u2.json", "recovery/work/task144/probe-u2.json")):
        path = os.path.join(ROOT, rel.replace("/", os.sep))
        print("=" * 78)
        print("SOURCE %s" % rel)
        if not os.path.exists(path):
            print("  MISSING")
            continue
        with io.open(path, "r", encoding="utf-8") as handle:
            doc = json.load(handle)
        print("  counters: %s" % json.dumps(doc.get("counters", {}), ensure_ascii=False))
        entries = collect_entries(doc)
        print("  probe entries: %d" % len(entries))
        counts = dict((c, 0) for c in CATEGORIES)
        negatives = []
        for name, code, message in entries:
            if code != -32602:
                continue
            kind = kind_of(message)
            counts[kind] += 1
            grand[kind] += 1
            negatives.append((name, kind, message))
        print("  live -32602 total: %d" % sum(counts.values()))
        for c in CATEGORIES:
            if counts[c]:
                print("    %-26s %d" % (c, counts[c]))
        per_source[label] = counts
        for name, kind, message in negatives[:6]:
            print("    eg %-34s %-24s %s" % (name, kind, message[:60]))

    print("=" * 78)
    print("GRAND TOTAL over both probe files")
    for c in CATEGORIES:
        print("  %-26s %d" % (c, grand[c]))
    print("  total live -32602:      %d" % sum(grand.values()))
    handler_side = grand["missing_required_colon"] + grand["wrong_type"]
    print("  HANDLER-side (-32602 not from the registry gate): %d" % handler_side)
    print("  no-colon (own handler message, NOT tool_builder): %d"
          % grand["missing_required_no_colon"])


if __name__ == "__main__":
    main()
