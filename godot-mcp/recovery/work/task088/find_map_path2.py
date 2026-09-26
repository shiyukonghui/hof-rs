# -*- coding: utf-8 -*-
"""task088 (4): print the text around every `map_path` occurrence in the evidence.

usage: python find_map_path2.py <outfile>
"""
from __future__ import print_function
import io, os, sys

IDX = r"C:\Users\wyl\AppData\Local\Temp\mcp-recovery\staging\__payload-index"
STREAMS = ["events-termdump.jsonl", "events-termfile.jsonl", "events-write.jsonl"]


def main():
    out = sys.argv[1]
    lines = []
    for stream in STREAMS:
        path = os.path.join(IDX, stream)
        if not os.path.exists(path):
            continue
        with io.open(path, encoding="utf-8", errors="replace") as fh:
            for lineno, line in enumerate(fh, 1):
                start = 0
                while True:
                    i = line.find("map_path", start)
                    if i < 0:
                        break
                    lines.append("%s:%d ...%s..." % (stream, lineno, line[i:i + 160].replace("\\n", " ")))
                    start = i + 8
                    if len(lines) > 40:
                        break
    data = "\n".join(lines) + "\n"
    io.open(out, "w", encoding="utf-8", newline="\n").write(data)
    print("occurrences: %d" % len(lines))
    for l in lines[:12]:
        print("  " + l)


if __name__ == "__main__":
    main()
