# -*- coding: utf-8 -*-
"""TASK-100: the assertions the node-state helper cannot see.

    python extra_assertions.py <run-dir>

`assertions.py` (TASK-098) reads the node-state assertions and the scenario runner's
per-step records. Two other tools also carry a verdict, and both are part of a run's
assertion tally:

  * `running_game_assert_screen_text` - `{"passed", "expected_text", "matched_element", ...}`;
  * `running_game_run_test_scenario`  - `{"all_passed", "passed", "failed", "results": [...]}`,
    whose nested `assert` steps carry their own `passed`.

This script prints them with their real values, so "the assertions all passed" is a list
rather than a claim.
"""
import glob
import io
import json
import os
import sys


def read(path):
    with io.open(path, "r", encoding="utf-8-sig", errors="replace") as handle:
        return json.load(handle)


def body_of(doc):
    if "error" in doc:
        return None, doc["error"]
    content = (doc.get("result") or {}).get("content") or []
    if not content:
        return None, None
    try:
        return json.loads(content[0].get("text", "")), None
    except ValueError:
        return None, None


def main():
    run = sys.argv[1]
    rows = []
    for path in sorted(glob.glob(os.path.join(run, "*.json"))):
        tag = os.path.basename(path)[:-5]
        if tag.endswith(".request") or not tag.startswith(("g", "e")):
            continue
        doc = read(path)
        body, error = body_of(doc)
        if error is not None or not isinstance(body, dict):
            continue
        if "expected_text" in body and "passed" in body:
            matched = (body.get("matched_element") or {}).get("text")
            rows.append((tag, "PASS" if body["passed"] else "FAIL",
                         "screen_text %r" % body["expected_text"],
                         "matched=%r source=%s" % (matched, body.get("source"))))
        elif "results" in body and "all_passed" in body:
            steps = [s for s in body["results"] if isinstance(s, dict) and "passed" in s]
            for step in steps:
                rows.append(("%s/step%s" % (tag, step.get("step")),
                             "PASS" if step["passed"] else "FAIL",
                             "scenario %s %s %s" % (step.get("property"), step.get("operator"),
                                                    step.get("expected")),
                             "actual=%s" % step.get("actual")))
            if not steps:
                rows.append((tag, "PASS" if body["all_passed"] else "FAIL",
                             "scenario (no assert step)", "steps=%s" % body.get("total_steps")))
                continue
            print("%-26s all_passed=%-5s steps=%s passed=%s failed=%s errors=%s duration_ms=%s" % (
                tag, body.get("all_passed"), body.get("total_steps"), body.get("passed"),
                body.get("failed"), body.get("errors"), body.get("duration_ms")))
    for tag, verdict, detail, actual in rows:
        print("%-26s %-5s %-44s %s" % (tag, verdict, detail[:44], actual[:56]))
    print("-" * 78)
    counts = {}
    for _, verdict, _, _ in rows:
        counts[verdict] = counts.get(verdict, 0) + 1
    print("extra assertions found: %d  ->  %s" % (len(rows), ", ".join(
        "%s=%d" % kv for kv in sorted(counts.items()))))


if __name__ == "__main__":
    main()
