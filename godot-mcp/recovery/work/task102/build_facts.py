# -*- coding: utf-8 -*-
"""TASK-102: the build / validate / errors verdicts of one run, from its own responses.

    python build_facts.py <run-dir>

The task書 asks for `project_build_csharp` exit code, `project_validate_scripts`
`invalid_count` and `editor_get_errors` `count` -- read here from the run's saved
responses rather than from report.json.
"""
import glob
import io
import json
import os
import sys


def body_of(path):
    with io.open(path, "r", encoding="utf-8-sig", errors="replace") as handle:
        doc = json.load(handle)
    if "error" in doc:
        return doc["error"]
    content = (doc.get("result") or {}).get("content") or []
    if not content:
        return None
    try:
        return json.loads(content[0].get("text", ""))
    except ValueError:
        return None


def main():
    run = sys.argv[1]
    for path in sorted(glob.glob(os.path.join(run, "*.json"))):
        tag = os.path.basename(path)[:-5]
        if tag.endswith(".request"):
            continue
        body = body_of(path)
        if not isinstance(body, dict):
            continue
        keys = set(body.keys())
        if {"exit_code"} & keys or {"invalid_count"} & keys or {"count"} & keys:
            print("%-30s %s" % (tag, json.dumps(
                {k: v for k, v in body.items()
                 if k in ("exit_code", "success", "errors_count", "warnings_count", "duration_ms",
                          "invalid_count", "valid_count", "count", "errors", "diagnostics")},
                ensure_ascii=False)[:400]))


if __name__ == "__main__":
    main()
