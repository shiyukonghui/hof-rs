# -*- coding: utf-8 -*-
"""For each interesting line, which recorded revision shows it and where.

usage: python marks.py <subpath> <marker> [marker ...]
"""
import sys

import evfetch as E


def main():
    sub = sys.argv[1]
    markers = sys.argv[2:]
    rows = E.reads(sub)
    for m in markers:
        hits = {}
        for r in rows:
            for no, txt in r.get("lines") or []:
                if m in txt:
                    hits.setdefault(r.get("totalLines"), set()).add(no)
        print("%-46s %s" % (m, {k: sorted(v)[:4] for k, v in sorted(hits.items())}))


if __name__ == "__main__":
    main()
