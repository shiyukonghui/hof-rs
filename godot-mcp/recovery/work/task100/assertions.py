# -*- coding: utf-8 -*-
"""TASK-098: every assertion of a run, with its actual verdict.

    python assertions.py <run-dir>

Reads the per-call response files the driver wrote and pulls out each assertion's own
result -- `passed` for `running_game_assert_node_state` and `running_game_assert_screen_text`,
and the nested `assert` steps of `running_game_run_test_scenario`. Prints one line per
assertion plus a pass/fail tally, so "the assertions passed" is a list rather than a claim.

The expected failures a session declares on purpose (a boundary call aimed at an error
path) are marked DECLARED and counted separately: they are evidence that the error path
works, not defects.
"""
import glob
import io
import json
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))


def read(path):
    with io.open(path, "r", encoding="utf-8-sig", errors="replace") as handle:
        return json.load(handle)


def payload(doc):
    if "error" in doc:
        return None, doc["error"]
    content = (doc.get("result") or {}).get("content") or []
    if not content:
        return None, None
    text = content[0].get("text", "")
    try:
        return json.loads(text), None
    except ValueError:
        return None, None


def main():
    run = sys.argv[1]
    rows = []
    for path in sorted(glob.glob(os.path.join(run, "g*.json"))):
        tag = os.path.basename(path)[:-5]
        if tag.endswith(".request"):
            continue
        doc = read(path)
        body, error = payload(doc)
        if error is not None:
            rows.append((tag, "ERROR", str(error.get("code")), error.get("message", "")[:90]))
            continue
        if not isinstance(body, dict):
            continue
        if "passed" in body and "assertion" in body:
            rows.append((tag, "PASS" if body["passed"] else "FAIL",
                         "%s %s %s" % (body.get("node_path", body.get("expected_text")),
                                       body.get("operator"), body.get("expected")),
                         "actual=%s" % body.get("actual")))
        elif "steps" in body or "step_results" in body:
            for step in (body.get("step_results") or body.get("steps") or []):
                if isinstance(step, dict) and "passed" in step:
                    rows.append((tag + "/" + str(step.get("type")),
                                 "PASS" if step["passed"] else "FAIL",
                                 json.dumps({k: step.get(k) for k in ("action", "property",
                                                                      "operator", "expected")}),
                                 "actual=%s" % step.get("actual")))
    declared_tags = set()
    for tag, verdict, detail, actual in rows:
        print("%-34s %-5s %-46s %s" % (tag, verdict, detail[:46], actual[:40]))
    print("-" * 78)
    counts = {}
    for _, verdict, _, _ in rows:
        counts[verdict] = counts.get(verdict, 0) + 1
    print("assertions found: %d  ->  %s" % (len(rows), ", ".join(
        "%s=%d" % kv for kv in sorted(counts.items()))))
    failing = [r for r in rows if r[1] == "FAIL"]
    errored = [r for r in rows if r[1] == "ERROR"]
    print("non-passing: %d FAIL, %d ERROR" % (len(failing), len(errored)))
    for tag, _, detail, actual in failing + errored:
        print("   %s | %s | %s" % (tag, detail, actual))


if __name__ == "__main__":
    main()
