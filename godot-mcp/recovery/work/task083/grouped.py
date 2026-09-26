# -*- coding: utf-8 -*-
"""TASK-083: group a build log's errors by owning file, with decoded messages."""
import io
import os
import re
import sys
from collections import Counter, OrderedDict

OUT = r"C:\Users\wyl\AppData\Local\Temp\mcp-recovery\work\task083"
ERR_RE = re.compile(r"^([A-Za-z]:\\[^(]*|modules\\[^(]*)\((\d+)\)\s*:\s*(fatal )?(error|warning)\s+([A-Z]+\d+)\s*:\s*(.*)$")


def main():
    tag = sys.argv[1]
    src = os.path.join(OUT, tag + ".stderr.utf8.txt")
    per = OrderedDict()
    codes = Counter()
    with io.open(src, "r", encoding="utf-8", errors="replace") as f:
        for line in f:
            m = ERR_RE.match(line.rstrip("\n"))
            if not m:
                continue
            p = m.group(1).replace("/", "\\")
            key = p.split("modules\\mcp_server\\", 1)[-1] if "modules\\mcp_server\\" in p else p
            per.setdefault(key, []).append((int(m.group(2)), m.group(5), m.group(3) or "", m.group(6)))
            codes[m.group(5)] += 1
    print("files with errors: %d   error lines: %d" % (len(per), sum(len(v) for v in per.values())))
    print("codes: %s" % dict(codes.most_common(15)))
    print()
    for key, errs in sorted(per.items(), key=lambda kv: -len(kv[1])):
        print("%-52s %d" % (key, len(errs)))
        shown = set()
        for ln, code, fat, msg in errs:
            if code in shown:
                continue
            shown.add(code)
            print("    %5d  %s%-7s %s" % (ln, fat, code, msg[:130]))
            if len(shown) >= 4:
                break


if __name__ == "__main__":
    main()
