# -*- coding: utf-8 -*-
"""Count compiler errors in a build log (cp936 bytes) and group them by file.

usage: python recount84.py <stderr.txt> [--list]
"""
import collections
import io
import re
import sys

PAT = re.compile(r"^(.*?)\((\d+)\)\s*:\s*(?:fatal )?error\s+([A-Z]+\d+):")


def main():
    path = sys.argv[1]
    raw = io.open(path, "rb").read()
    for enc in ("utf-8", "cp936", "gbk", "latin-1"):
        try:
            text = raw.decode(enc)
            break
        except Exception:  # noqa: BLE001
            continue
    byfile = collections.Counter()
    bycode = collections.Counter()
    first = {}
    total = 0
    lines = []
    for line in text.split("\n"):
        m = PAT.match(line.strip())
        if not m:
            continue
        total += 1
        f = m.group(1).strip()
        byfile[f] += 1
        bycode[m.group(3)] += 1
        first.setdefault(f, (int(m.group(2)), m.group(3)))
        lines.append(line.strip()[:200])
    print("error lines: %d   files: %d" % (total, len(byfile)))
    print("codes: %s" % ", ".join("%s x%d" % (c, n) for c, n in bycode.most_common()))
    print("")
    for f, n in byfile.most_common():
        print("%5d  %-58s first line %-6d %s" % (n, f, first[f][0], first[f][1]))
    if "--list" in sys.argv:
        print("\n".join(lines))


if __name__ == "__main__":
    main()
