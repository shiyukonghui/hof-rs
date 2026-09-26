# -*- coding: utf-8 -*-
"""Locate the edit events that introduced each generation of the duplicated
`serialize_variant` switch cases.

usage: python gen_edits.py <subpath> [marker ...]
"""
import io
import json
import os
import sys

IDX = r"C:\Users\wyl\AppData\Local\Temp\mcp-recovery\staging\__payload-index"

MARKERS = [
    "TASK-024 E-3: the packed containers",
    "The element's own kind",
    "case Variant::VECTOR4:",
    "case Variant::VECTOR4I:",
    "case Variant::PACKED_BYTE_ARRAY:",
    "case Variant::PACKED_COLOR_ARRAY:",
    "case Variant::RECT2I:",
    "TASK-021 A-3",
]


def norm(p):
    return (p or "").replace("/", "\\").lower()


def main():
    sub = sys.argv[1]
    markers = sys.argv[2:] or MARKERS
    rows = []
    with io.open(os.path.join(IDX, "events-edit.jsonl"), encoding="utf-8", errors="replace") as f:
        for l in f:
            if not l.strip():
                continue
            r = json.loads(l)
            if sub in norm(r.get("path")):
                rows.append(r)
    rows.sort(key=lambda r: r.get("time", 0))
    print("%d edits for %s" % (len(rows), sub))
    for r in rows:
        blob = (r.get("old") or "") + (r.get("new") or "")
        marks = [m for m in markers if m in blob]
        if not marks:
            continue
        ok = "FAIL" if (r.get("result") or "").lstrip().startswith("Error") else "OK"
        print("%-6s t=%-14s %-4s old=%-4d new=%-4d  %s" % (
            r.get("seq"), r.get("time"), ok,
            len((r.get("old") or "").split("\n")), len((r.get("new") or "").split("\n")),
            "; ".join(m[:34] for m in marks)))


if __name__ == "__main__":
    main()
