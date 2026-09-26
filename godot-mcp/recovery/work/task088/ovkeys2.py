# -*- coding: utf-8 -*-
"""task088 (4): compare the DESCRIPTION_/SCHEMA_OVERRIDES KEYS of two generators.

usage: python ovkeys2.py <fileA> <fileB> <outfile>
"""
from __future__ import print_function
import io, re, sys


def block(text, name):
    m = re.search(r"^%s\s*=\s*\{" % name, text, re.M)
    if not m:
        return None
    j = text.find("{", m.start())
    d = 0
    k = j
    while k < len(text):
        if text[k] == "{":
            d += 1
        elif text[k] == "}":
            d -= 1
            if d == 0:
                break
        k += 1
    return text[j:k + 1]


def keys(text, name):
    b = block(text, name)
    if b is None:
        return None
    out = []
    for line in b.split("\n")[1:]:
        m = re.match(r'^    "([^"]+)"\s*:', line)
        if m:
            out.append(m.group(1))
    return out


def main():
    a, b, out = sys.argv[1], sys.argv[2], sys.argv[3]
    ta = io.open(a, encoding="utf-8", errors="replace").read()
    tb = io.open(b, encoding="utf-8", errors="replace").read()
    lines = []
    for name in ("DESCRIPTION_OVERRIDES", "SCHEMA_OVERRIDES"):
        ka, kb = keys(ta, name), keys(tb, name)
        lines.append("%s: A=%d B=%d" % (name, -1 if ka is None else len(ka), -1 if kb is None else len(kb)))
        if ka is None or kb is None:
            continue
        sa, sb = set(ka), set(kb)
        lines.append("  A only: %s" % sorted(sa - sb))
        lines.append("  B only: %s" % sorted(sb - sa))
        lines.append("  A keys: %s" % ", ".join(ka))
        lines.append("  B keys: %s" % ", ".join(kb))
    data = "\n".join(lines) + "\n"
    io.open(out, "w", encoding="utf-8", newline="\n").write(data)
    print(data)


if __name__ == "__main__":
    main()
