# -*- coding: utf-8 -*-
"""task088: report generator version + override entry counts + override keys.

usage: python ovcount.py <outfile> <file1> <file2> ...
"""
from __future__ import print_function
import io, re, sys


def block(t, name):
    i = t.find(name)
    if i < 0:
        return None
    j = t.find("{", i)
    if j < 0:
        return None
    d = 0
    k = j
    while k < len(t):
        if t[k] == "{":
            d += 1
        elif t[k] == "}":
            d -= 1
            if d == 0:
                break
        k += 1
    return t[j:k + 1]


def main():
    out = sys.argv[1]
    lines = []
    for p in sys.argv[2:]:
        t = io.open(p, encoding="utf-8", errors="replace").read()
        m = re.search(r"GENERATOR_VERSION\s*=\s*[\"']([^\"']+)[\"']", t)
        lines.append("%s lines=%d bytes=%d genver=%s" % (
            p, t.count("\n") + 1, len(t.encode("utf-8")), m.group(1) if m else "?"))
        for name in ("DESCRIPTION_OVERRIDES", "SCHEMA_OVERRIDES"):
            b = block(t, name)
            if b is None:
                lines.append("   %s MISSING" % name)
                continue
            keys = re.findall(r"^\s+\"([^\"]+)\"\s*:", b, re.M)
            lines.append("   %s entries=%d keys=%s" % (name, len(keys), ",".join(keys)))
    data = "\n".join(lines) + "\n"
    io.open(out, "w", encoding="utf-8", newline="\n").write(data)
    print(data)


if __name__ == "__main__":
    main()
