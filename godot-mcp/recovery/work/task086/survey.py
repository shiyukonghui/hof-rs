# -*- coding: utf-8 -*-
"""Survey one recorded file: all writes (by time) + edit counts after each."""
import io
import json
import os
import sys

IDX = r"C:\Users\wyl\AppData\Local\Temp\mcp-recovery\staging\__payload-index"


def norm(p):
    return (p or "").replace("/", "\\").lower()


def load(which):
    out = []
    p = os.path.join(IDX, which)
    with io.open(p, "r", encoding="utf-8", errors="replace") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            out.append(json.loads(line))
    return out


def main():
    exact = norm(sys.argv[1])
    only = sys.argv[2] if len(sys.argv) > 2 else None
    writes = load("events-write.jsonl")
    edits = load("events-edit.jsonl")
    reads = load("events-read.jsonl")
    w = [r for r in writes if exact == norm(r.get("path"))]
    e = [r for r in edits if exact == norm(r.get("path"))]
    rd = [r for r in reads if exact == norm(r.get("path"))]
    print("target: %s" % exact)
    print("writes=%d edits=%d reads=%d" % (len(w), len(e), len(rd)))
    w.sort(key=lambda r: r.get("time", 0))
    for r in w:
        print("  WRITE seq=%-6s t=%-14s bytes=%-8d lines=%-6d result=%s" % (
            r.get("seq"), r.get("time"), len(r.get("content") or ""),
            len((r.get("content") or "").split("\n")),
            (r.get("result") or "")[:60]))
    e.sort(key=lambda r: r.get("time", 0))
    if only == "edits":
        for r in e:
            print("  EDIT seq=%-6s t=%-14s old=%-5d new=%-5d ok=%s  %s" % (
                r.get("seq"), r.get("time"), len((r.get("old") or "").split("\n")),
                len((r.get("new") or "").split("\n")),
                not (r.get("result") or "").lstrip().startswith("Error"),
                (r.get("result") or "")[:60]))
    rd.sort(key=lambda r: r.get("time", 0))
    if only == "reads":
        for r in rd[-25:]:
            print("  READ  t=%-14s totalLines=%-6s window=%s" % (
                r.get("time"), r.get("totalLines"), len(r.get("lines") or [])))
    # max totalLines
    if rd:
        print("  max totalLines = %s" % max((r.get("totalLines") or 0) for r in rd))


main()
