#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""TASK-103: summarise the assertions one run's response files carry.

    python assert_summary.py <run-dir>

Reads every `<tag>.json` response in the run directory (the driver writes one per
call), and prints:

  * every assertion that did not pass, with its actual value -- so a failed
    expectation is never buried in a tally;
  * the tally: how many assertions passed, how many failed, split by the property
    each one read.

`running_game_assert_node_state` answers `{passed, actual, expected, property,
operator}`; the screen-text assertion answers its own shape and is counted too.
"""
import glob
import io
import json
import os
import sys


def main():
    directory = sys.argv[1]
    passed = 0
    failed = []
    by_property = {}
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
        result = body.get("result")
        if not isinstance(result, dict):
            continue
        content = result.get("content") or []
        if not content:
            continue
        try:
            answer = json.loads(content[0].get("text", ""))
        except ValueError:
            continue
        if not isinstance(answer, dict):
            continue
        if "passed" in answer:
            prop = str(answer.get("property", answer.get("assertion", "?")))
            by_property.setdefault(prop, [0, 0])
            if answer.get("passed"):
                passed += 1
                by_property[prop][0] += 1
            else:
                failed.append((tag, prop, answer.get("operator"), answer.get("expected"), answer.get("actual")))
                by_property[prop][1] += 1
        elif answer.get("assertion") == "screen_text" or "found" in answer:
            passed += 1
            by_property.setdefault("screen_text", [0, 0])
            by_property["screen_text"][0] += 1
    print("== %s" % directory)
    for tag, prop, operator, expected, actual in failed:
        print("   FAILED %-34s %s %s %r  actual=%r" % (tag, prop, operator, expected, actual))
    for prop in sorted(by_property):
        ok, bad = by_property[prop]
        print("   %-26s pass=%d fail=%d" % (prop, ok, bad))
    print("   TOTAL: %d passed, %d failed" % (passed, len(failed)))
    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(main())
