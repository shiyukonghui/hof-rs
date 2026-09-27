#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""TASK-118: find a candidate content-level witness for the four count_only tools.

Scans every run's jsonl trace for the target writer's ok=true calls and for every
other tool call in the same run whose payload carries a literal written by the
writer. Prints the run, the writer call, the candidate reader call and the hit.
Output is printed, never redirected through the shell.
"""
import io
import json
import os
import re
import sys

ROOT = r"F:\moonbit-hof-rs\godot-mcp"
RUNS = os.path.join(ROOT, "runs")


def iter_traces():
    for base, _dirs, files in os.walk(RUNS):
        for name in files:
            if name.endswith(".jsonl"):
                yield os.path.join(base, name)


def rows(path):
    out = []
    with io.open(path, "r", encoding="utf-8", errors="replace") as fh:
        for line in fh:
            line = line.strip()
            if not line:
                continue
            try:
                doc = json.loads(line)
            except Exception:
                continue
            if doc.get("method") != "tools/call":
                continue
            out.append(doc)
    return out


def payload(doc):
    text = doc.get("result_json")
    if isinstance(text, str) and text:
        return text
    return ""


def main():
    target = sys.argv[1]
    literals = sys.argv[2:]
    for path in sorted(iter_traces()):
        rs = rows(path)
        writers = [r for r in rs if r.get("tool") == target and r.get("ok")]
        if not writers:
            continue
        rel = os.path.relpath(path, ROOT)
        print("== %s  (%d ok calls of %s)" % (rel, len(writers), target))
        for w in writers[:3]:
            print("   writer seq=%s args=%s res=%s" % (w.get("seq"), (w.get("args") or "")[:200],
                                                       payload(w)[:200]))
        for r in rs:
            p = payload(r)
            if not r.get("ok") or not p:
                continue
            if r.get("tool") == target:
                continue
            hits = [lit for lit in literals if lit in p]
            if hits:
                print("   HIT reader=%s seq=%s hits=%s payload=%s"
                      % (r.get("tool"), r.get("seq"), hits, p[:300]))
    print("done")


if __name__ == "__main__":
    main()
