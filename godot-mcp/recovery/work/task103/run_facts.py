#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""TASK-103: the handful of per-run facts the report quotes, read out of the run's
own response files (never out of `report.json`, so they are a second reading).

    python run_facts.py <run-dir> [<tag> ...]

Prints `tag field value` lines for: the build's exit code and duration, the script
validator's counters, the editor error count, the '@'-auto-name count over every
scene-tree answer, and the Dump() line of the first and last readback.
"""
import glob
import io
import json
import os
import sys


def answers(directory):
    out = {}
    for path in sorted(glob.glob(os.path.join(directory, "*.json"))):
        name = os.path.basename(path)
        if name.startswith(("import", "session", "call-index", "ledger", "report")):
            continue
        tag = name[:-len(".json")]
        if tag.endswith(".request"):
            continue
        try:
            with io.open(path, encoding="utf-8-sig") as handle:
                body = json.load(handle)
        except Exception:  # noqa: BLE001
            continue
        if "result" not in body:
            continue
        content = (body["result"] or {}).get("content") or []
        if not content:
            continue
        try:
            out[tag] = json.loads(content[0].get("text", ""))
        except ValueError:
            out[tag] = {"__text__": content[0].get("text", "")}
    return out


def main():
    directory = sys.argv[1]
    wanted = sys.argv[2:]
    found = answers(directory)
    for tag in wanted:
        if tag not in found:
            print("%-34s MISSING" % tag)
            continue
        print("%-34s %s" % (tag, json.dumps(found[tag], ensure_ascii=False)[:400]))
    # every scene-tree answer, counted for '@'-auto names
    total = 0
    auto = 0
    trees = 0
    for tag, answer in found.items():
        if tag not in ("g01-scene-tree", "g90-final-tree", "g69-final-tree", "g122-final-tree",
                       "e07-tree-after-refusal", "g01-scene-tree"):
            continue
        if not isinstance(answer, dict) or "tree" not in answer:
            continue
        trees += 1
        stack = [answer["tree"]]
        while stack:
            node = stack.pop()
            name = node.get("name", "")
            total += 1
            if name.startswith("@"):
                auto += 1
            for child in node.get("children", []) or []:
                stack.append(child)
    print("scene trees read: %d, node names: %d, names starting with '@': %d" % (trees, total, auto))


if __name__ == "__main__":
    main()
