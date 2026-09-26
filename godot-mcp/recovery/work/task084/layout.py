# -*- coding: utf-8 -*-
"""List the function-level layout of one revision of one file (newest window wins)."""
import io
import json
import os
import re
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from cmp import build_newest  # noqa: E402

RX = re.compile(r"^(static |bool |void |Dictionary |Variant |String |int |Array |MCPToolError |const |struct |class )")


def main():
    sub = sys.argv[1]
    rev = int(sys.argv[2])
    w = build_newest(sub, rev)
    print("rev%d covered %d lines" % (rev, len(w)))
    for no in sorted(w):
        l = w[no]
        if RX.match(l) and ("(" in l) and (";" not in l):
            print("%5d| %s" % (no, l[:140]))


if __name__ == "__main__":
    main()
