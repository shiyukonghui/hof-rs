#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""TASK-104: the per-run facts the report quotes, read out of the run's own
response files and its own ledgers (never out of `report.json`, so they are a
second reading).

    python game_facts.py <run-dir>
"""
import glob
import io
import json
import os
import re
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
            if "error" in body:
                out[tag] = {"__error__": body["error"]}
            continue
        content = (body["result"] or {}).get("content") or []
        if not content:
            continue
        try:
            out[tag] = json.loads(content[0].get("text", ""))
        except ValueError:
            out[tag] = {"__text__": content[0].get("text", "")}
    return out


def walk(node, counter):
    counter[0] += 1
    if str(node.get("name", "")).startswith("@"):
        counter[1] += 1
    for child in node.get("children", []) or []:
        walk(child, counter)


def main():
    directory = sys.argv[1]
    found = answers(directory)

    # the build / validator / editor-error facts, and the Dump lines
    dumps = []
    for tag, answer in sorted(found.items()):
        if not isinstance(answer, dict):
            continue
        if "exit_code" in answer and "duration_ms" in answer:
            print("build            %-24s exit=%s duration_ms=%s" % (tag, answer.get("exit_code"),
                                                                     answer.get("duration_ms")))
        if "invalid_count" in answer or "valid_count" in answer:
            print("validate         %-24s valid=%s invalid=%s files=%s"
                  % (tag, answer.get("valid_count"), answer.get("invalid_count"),
                     answer.get("file_count", answer.get("count"))))
        if tag == "e14-get-errors":
            print("editor errors    %-24s %s" % (tag, json.dumps(answer, ensure_ascii=False)[:200]))
        if isinstance(answer, dict) and "result" in answer and isinstance(answer["result"], str):
            text = answer["result"]
            if " last=" in text:
                dumps.append((tag, text))

    # '@'-auto names over every scene-tree answer
    total = 0
    auto = 0
    trees = 0
    for tag, answer in sorted(found.items()):
        if not isinstance(answer, dict) or "tree" not in answer:
            continue
        trees += 1
        counter = [0, 0]
        walk(answer["tree"], counter)
        total += counter[0]
        auto += counter[1]
    print("scene trees read %d, node names %d, names starting with '@' %d" % (trees, total, auto))

    for tag, text in dumps:
        print("reading          %-24s %s" % (tag, text[:220]))

    # the verdict distribution and the reconstructible-fact completeness, from the ledgers
    for name in ("ledger-editor.txt", "ledger-game.txt"):
        path = os.path.join(directory, name)
        if not os.path.isfile(path):
            print("%-16s ABSENT" % name)
            continue
        text = io.open(path, encoding="utf-8-sig").read()
        for line in text.splitlines():
            if line.startswith("calls="):
                print("%-16s %s" % (name, line.strip()))
            if line.startswith("verdicts:"):
                print("%-16s %s" % (name, line.strip()))
            if "reconstructible facts are all present" in line:
                print("%-16s %s" % (name, line.strip()))
    # the pixel column, from the ledger headers of the report
    report = os.path.join(directory, "report.json")
    if os.path.isfile(report):
        with io.open(report, encoding="utf-8") as handle:
            data = json.load(handle)
        print("pixel_evidence   %s" % json.dumps(data.get("pixel_evidence"), ensure_ascii=False))
        frames = (data.get("saved_frames") or {}).get("frames") or []
        print("saved frames     %d" % len(frames))
        for frame in frames:
            print("  %-12s %-8s %8s %-18s diff_vs_prev=%s"
                  % (frame["name"], "x".join(str(v) for v in frame["size"]), frame["bytes"],
                     frame["sha256"][:16],
                     (frame.get("diff_vs_prev") or {}).get("changed_pixels")))


if __name__ == "__main__":
    main()
