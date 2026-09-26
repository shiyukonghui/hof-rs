# -*- coding: utf-8 -*-
"""TASK-083: decode a build log (the compiler writes cp936 under the cmd code
page) and inventory the errors by owning file."""
import io
import os
import re
import sys
from collections import Counter

OUT = r"C:\Users\wyl\AppData\Local\Temp\mcp-recovery\work\task083"
ERR_RE = re.compile(r"^([A-Za-z]:\\[^(]*|modules\\[^(]*)\((\d+)\)\s*:\s*(fatal )?(error|warning)\s+(C\d+|[A-Z]+\d+)")


def main():
    tag = sys.argv[1]
    for kind in ("stderr", "stdout"):
        src = r"C:\Users\wyl\AppData\Local\Temp\mcp-recovery\logs\%s.%s.txt" % (tag, kind)
        if not os.path.exists(src):
            continue
        raw = open(src, "rb").read()
        try:
            text = raw.decode("cp936")
        except Exception:
            text = raw.decode("utf-8", "replace")
        dst = os.path.join(OUT, "%s.%s.utf8.txt" % (tag, kind))
        with io.open(dst, "w", encoding="utf-8", newline="\n") as f:
            f.write(text)
        lines = text.split("\n")
        errs = []
        codes = Counter()
        files = Counter()
        for i, l in enumerate(lines):
            m = ERR_RE.match(l)
            if m:
                errs.append((m.group(1), int(m.group(2)), m.group(3) or "", m.group(4), m.group(5)))
                codes[m.group(5)] += 1
                files[os.path.basename(m.group(1))] += 1
        print("=== %s (%s) bytes=%d lines=%d" % (tag, kind, len(raw), len(lines)))
        print("    decoded -> %s" % dst)
        print("    error lines=%d" % len(errs))
        if errs:
            print("    error codes: %s" % dict(codes.most_common(12)))
            print("    top files:")
            for f, n in files.most_common(20):
                print("      %-52s %d" % (f, n))
            print("    first 25 errors:")
            for p, ln, fat, k, c in errs[:25]:
                print("      %s(%d): %s %s %s" % (os.path.basename(p), ln, fat, k, c))
            print("    last 8 errors:")
            for p, ln, fat, k, c in errs[-8:]:
                print("      %s(%d): %s %s %s" % (os.path.basename(p), ln, fat, k, c))
        tail = [l for l in lines if l.strip()][-6:]
        print("    tail:")
        for l in tail:
            print("      %s" % l[:150])


if __name__ == "__main__":
    main()
