#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""TASK-113 item B: pull the two pre-fix defect reproductions out of TASK-111's
traces, and print them next to the post-fix session's answers.

Read-only: it only reads `runs/**/trace-*.jsonl`.

Usage:
    python recovery/work/task113/pre_post_defects.py pre
    python recovery/work/task113/pre_post_defects.py post RUN_DIR
"""
import io
import json
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.abspath(os.path.join(HERE, "..", "..", ".."))
RUNS = os.path.join(ROOT, "runs")

# The two registrations: (tool, a distinctive fragment of the args that only the
# defect-reproduction call carries).
TARGETS = [
    ("editor_add_raycast", '"4d"'),
    ("editor_add_resource_to_node_property", '"x":48'),
]


def iter_traces():
    for dirpath, _dirs, files in os.walk(RUNS):
        for name in sorted(files):
            if name.startswith("trace-") and name.endswith(".jsonl"):
                yield os.path.join(dirpath, name)


def rows(path):
    with io.open(path, "r", encoding="utf-8", errors="replace") as handle:
        for line in handle:
            line = line.strip()
            if not line:
                continue
            try:
                record = json.loads(line)
            except ValueError:
                continue
            yield record


def pre():
    for tool, fragment in TARGETS:
        print("=" * 78)
        print("PRE-FIX  %s   (args fragment %s)" % (tool, fragment))
        for path in iter_traces():
            for record in rows(path):
                if record.get("tool") != tool or record.get("event") == "capture":
                    continue
                args = record.get("args") or ""
                if fragment not in args:
                    continue
                rel = os.path.relpath(path, ROOT).replace("\\", "/")
                print("- run      : %s" % rel)
                print("  seq      : %s" % record.get("seq"))
                print("  args     : %s" % args)
                print("  ok       : %s" % record.get("ok"))
                print("  err_code : %s  message: %s"
                      % (record.get("error_code"), record.get("error_message")))
                print("  err_data : %s" % record.get("error_data_json"))
                print("  result   : %s" % record.get("result_json"))
    return 0


def post(run_dir):
    base = run_dir if os.path.isabs(run_dir) else os.path.join(ROOT, run_dir)
    print("POST-FIX session: %s" % base)
    for path in sorted(os.listdir(base)):
        if not (path.startswith("trace-") and path.endswith(".jsonl")):
            continue
        full = os.path.join(base, path)
        for record in rows(full):
            tool = record.get("tool")
            if tool not in ("editor_add_resource_to_node_property", "editor_add_raycast"):
                continue
            if record.get("event") == "capture":
                continue
            print("- %s  seq=%s" % (path, record.get("seq")))
            print("  args     : %s" % record.get("args"))
            print("  ok       : %s" % record.get("ok"))
            print("  err_code : %s  message: %s"
                  % (record.get("error_code"), record.get("error_message")))
            print("  err_data : %s" % record.get("error_data_json"))
            print("  result   : %s" % record.get("result_json"))
    return 0


def main(argv):
    if len(argv) >= 2 and argv[1] == "pre":
        return pre()
    if len(argv) >= 3 and argv[1] == "post":
        return post(argv[2])
    print(__doc__)
    return 2


if __name__ == "__main__":
    sys.exit(main(sys.argv))
