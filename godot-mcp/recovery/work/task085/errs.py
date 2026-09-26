# -*- coding: utf-8 -*-
"""Extract module compile errors from a build log (cp936 or utf-8 bytes).

usage: python errs.py <log> [file-filter] [--list]
"""
import io
import re
import sys

PAT = re.compile(r"^(.*?)\((\d+)\)\s*:\s*(?:fatal )?error\s+([A-Z]+\d+):\s*(.*)$")


def read(path):
    raw = io.open(path, "rb").read()
    for enc in ("utf-8", "cp936", "gbk", "latin-1"):
        try:
            return raw.decode(enc)
        except UnicodeDecodeError:
            continue
    return raw.decode("latin-1")


def main():
    path = sys.argv[1]
    filt = None
    for a in sys.argv[2:]:
        if not a.startswith("--"):
            filt = a
    text = read(path)
    n = 0
    for line in text.split("\n"):
        m = PAT.match(line.strip())
        if not m:
            continue
        f, ln, code, msg = m.group(1).strip(), m.group(2), m.group(3), m.group(4)
        if filt and filt not in f:
            continue
        n += 1
        if "--list" in sys.argv:
            print("%s(%s): %s: %s" % (f, ln, code, msg[:160]))
    print("total %d" % n)


if __name__ == "__main__":
    main()
