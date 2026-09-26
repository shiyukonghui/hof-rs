# -*- coding: utf-8 -*-
"""task088 (4): extract every recorded `"map_path"` value from the evidence
streams, with the surrounding tool-name context, to decide whether the pinned
contract's `_meta.map_path` value can be replayed.

usage: python find_map_path.py <outfile>
"""
from __future__ import print_function
import io, json, os, re, sys

IDX = r"C:\Users\wyl\AppData\Local\Temp\mcp-recovery\staging\__payload-index"
STREAMS = ["events-termdump.jsonl", "events-termfile.jsonl", "events-write.jsonl"]
PAT = re.compile(r'"map_path"\s*:\s*"((?:[^"\\]|\\.)*)"')


def main():
    out = sys.argv[1]
    values = {}
    for stream in STREAMS:
        path = os.path.join(IDX, stream)
        if not os.path.exists(path):
            continue
        with io.open(path, encoding="utf-8", errors="replace") as fh:
            for lineno, line in enumerate(fh, 1):
                for m in PAT.finditer(line):
                    raw = m.group(1).replace("\\\\", "\\")
                    values.setdefault(raw, []).append("%s:%d" % (stream, lineno))
    lines = []
    for raw, where in sorted(values.items(), key=lambda kv: -len(kv[1])):
        lines.append("count=%-4d value=%s" % (len(where), raw))
        lines.append("           first: %s" % where[0])
    data = "\n".join(lines) + "\n"
    io.open(out, "w", encoding="utf-8", newline="\n").write(data)
    print("distinct recorded map_path values: %d" % len(values))
    for raw, where in sorted(values.items(), key=lambda kv: -len(kv[1])):
        print("  count=%-4d %s" % (len(where), raw))
    print("wrote %s" % out)


if __name__ == "__main__":
    main()
