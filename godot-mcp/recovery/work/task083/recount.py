# -*- coding: utf-8 -*-
"""TASK-083: re-count TASK-082's build-3 log with this task's counter so the
1575 -> 448 comparison is apples to apples."""
import io
import os
import re
import sys
from collections import Counter

LOGDIR = r"C:\Users\wyl\AppData\Local\Temp\mcp-recovery\logs"
ERR_RE = re.compile(r"^([A-Za-z]:\\[^(]*|modules\\[^(]*)\((\d+)\)\s*:\s*(fatal )?(error|warning)\s+([A-Z]+\d+)")


def count(path):
    raw = open(path, "rb").read()
    for enc in ("cp936", "utf-8"):
        try:
            text = raw.decode(enc)
            break
        except Exception:
            text = raw.decode("utf-8", "replace")
    n = 0
    files = set()
    codes = Counter()
    for line in text.split("\n"):
        m = ERR_RE.match(line)
        if m:
            n += 1
            files.add(os.path.basename(m.group(1)))
            codes[m.group(5)] += 1
    return n, files, codes


def main():
    for fn in sorted(os.listdir(LOGDIR)):
        if not fn.endswith(".txt") or "task082" not in fn:
            continue
        n, files, codes = count(os.path.join(LOGDIR, fn))
        if n == 0:
            continue
        print("%-46s error-lines=%-6d files=%-4d top=%s" % (fn, n, len(files), dict(codes.most_common(5))))
    for fn in ["task083_build1_notests.stderr.txt", "task083_build2_keepgoing_notests.stderr.txt"]:
        p = os.path.join(LOGDIR, fn)
        if os.path.exists(p):
            n, files, codes = count(p)
            print("%-46s error-lines=%-6d files=%-4d top=%s" % (fn, n, len(files), dict(codes.most_common(5))))


if __name__ == "__main__":
    main()
