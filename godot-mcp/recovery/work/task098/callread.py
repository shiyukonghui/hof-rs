# -*- coding: utf-8 -*-
"""TASK-098: read a per-call response JSON from a run directory.

The driver writes each call's response with PowerShell's Set-Content -Encoding UTF8,
i.e. with a BOM, so every read here goes through utf-8-sig.
"""
import io
import json
import os
import sys


def load(run, tag):
    path = os.path.join(run, tag + ".json")
    with io.open(path, "r", encoding="utf-8-sig", errors="replace") as handle:
        doc = json.load(handle)
    return doc


def text_of(doc):
    """The tool's own JSON payload as a string, or the error as a string."""
    if "error" in doc:
        return json.dumps(doc["error"], ensure_ascii=False)
    content = doc.get("result", {}).get("content") or []
    if content:
        return content[0].get("text", "")
    return json.dumps(doc, ensure_ascii=False)


def main():
    run = sys.argv[1]
    for tag in sys.argv[2:]:
        print("=== %s ===" % tag)
        doc = load(run, tag)
        text = text_of(doc)
        try:
            parsed = json.loads(text)
            print(json.dumps(parsed, ensure_ascii=False, indent=1)[:6000])
        except ValueError:
            print(text[:6000])
        print()


if __name__ == "__main__":
    main()
