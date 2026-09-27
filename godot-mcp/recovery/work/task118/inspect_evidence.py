#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""TASK-118 evidence inspection: what can already witness the four count_only tools?

Reads the per-call JSON files plus the jsonl traces of the candidate runs and prints,
verbatim, the payloads that matter. No shell redirection is used anywhere: every
output file is written through Python file IO.
"""
import io
import json
import os
import sys

ROOT = r"F:\moonbit-hof-rs\godot-mcp"


def load(path):
    with io.open(path, "r", encoding="utf-8", errors="replace") as fh:
        return json.load(fh)


def call_files(run_rel):
    d = os.path.join(ROOT, run_rel)
    if not os.path.isdir(d):
        return []
    out = []
    for name in sorted(os.listdir(d)):
        if name.endswith(".json") and not name.endswith(".request.json"):
            out.append(os.path.join(d, name))
    return out


def show(run_rel, tool_filter):
    lines = []
    for path in call_files(run_rel):
        try:
            doc = load(path)
        except Exception as exc:  # noqa
            lines.append("[unparseable] %s %s" % (os.path.basename(path), exc))
            continue
        tool = doc.get("tool") or ""
        if tool_filter and tool not in tool_filter:
            continue
        ok = doc.get("ok")
        res = doc.get("result_json")
        if res is None:
            res = doc.get("error")
        txt = json.dumps(res, ensure_ascii=False)
        lines.append("%-55s ok=%s %s" % (os.path.basename(path), ok, txt[:400]))
    return lines


def main():
    argv = sys.argv[1:]
    run_rel = argv[0]
    tools = set(argv[1:]) if len(argv) > 1 else None
    for line in show(run_rel, tools):
        print(line)


if __name__ == "__main__":
    main()
