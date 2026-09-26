# -*- coding: utf-8 -*-
"""TASK-098 item B3: settle the copy-count discrepancy between TASK-096 and TASK-097.

TASK-096's report and MCP-TRACEABILITY section 7.1 record the duplicate layer as
"Pong 5 / Breakout 18 / Snake 37"; TASK-097's cleanup session records what it actually
deleted as "Pong 8 / Breakout 20 / Snake 37". Both numbers are quotes from real runs, so
this script re-reads the pre-cleanup scene the cleanup session itself read off disk and
counts the automatic names by type. That is the evidence the reconciliation rests on.

    python copy_count_evidence.py <run-dir> <tag-of-the-read-before-call>

The scene text comes from the run's `project_read_text_file` response, i.e. from the
engine, not from a file this task edited.
"""
import io
import json
import os
import re
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from callread import load, text_of  # noqa: E402


def main():
    run = sys.argv[1]
    tag = sys.argv[2]
    doc = load(run, tag)
    text = text_of(doc)
    try:
        body = json.loads(text)
    except ValueError:
        print("could not parse the read response")
        return 1
    content = body.get("text")
    if content is None:
        content = body.get("content")
    if content is None:
        print("no scene text in this response (keys: %s)" % sorted(body.keys()))
        return 1
    if body.get("text_omitted"):
        print("WARNING: the tool says the text was omitted/truncated; counts below are partial")
    names = re.findall(r'\[node name="([^"]+)"', content)
    auto = [n for n in names if n.startswith("@")]
    by_type = {}
    for n in auto:
        m = re.match(r'@([A-Za-z0-9_]+)@', n)
        key = m.group(1) if m else "?"
        by_type[key] = by_type.get(key, 0) + 1
    print("== %s / %s" % (run, tag))
    print("   scene bytes: %d   total [node] entries: %d" % (len(content), len(names)))
    print("   automatic names (@Type@N): %d" % len(auto))
    for key in sorted(by_type):
        print("     @%s@ -> %d" % (key, by_type[key]))
    print("   named nodes: %d" % (len(names) - len(auto)))
    print("   first automatic names: %s" % (auto[:6] or "none"))
    return 0


if __name__ == "__main__":
    sys.exit(main())
