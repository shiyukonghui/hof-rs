# -*- coding: utf-8 -*-
"""TASK-096 helper: print the result payload of chosen calls of one run, decoded."""
import io
import json
import os
import sys


def payload(path):
    with io.open(path, "r", encoding="utf-8-sig", errors="replace") as handle:
        text = handle.read()
    try:
        outer = json.loads(text)
    except ValueError as exc:
        return "UNPARSEABLE (%s): %s" % (exc, text[:200])
    if "error" in outer:
        return "ERROR %s" % json.dumps(outer["error"], ensure_ascii=False)
    try:
        inner = outer["result"]["content"][0]["text"]
    except Exception:
        return json.dumps(outer, ensure_ascii=False)[:400]
    try:
        return json.loads(inner).get("result", inner)
    except ValueError:
        return inner


def main(run, tags):
    for tag in tags:
        path = os.path.join(run, tag + ".json")
        if not os.path.exists(path):
            print("%-28s MISSING" % tag)
            continue
        value = payload(path)
        if not isinstance(value, str):
            value = json.dumps(value, ensure_ascii=False)
        print("=== %s ===" % tag)
        print(value)
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1], sys.argv[2:]))
