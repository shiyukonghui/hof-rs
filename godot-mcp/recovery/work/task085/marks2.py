# -*- coding: utf-8 -*-
"""Count, per recorded revision, how many read-window lines contain a marker.

usage: python marks2.py <subpath> <marker>
"""
import sys

import evfetch as E


def main():
    sub, marker = sys.argv[1], sys.argv[2]
    rows = E.reads(sub)
    per = {}
    for r in rows:
        hit = [(no, txt.strip()) for no, txt in (r.get("lines") or []) if marker in txt]
        if not hit:
            continue
        per.setdefault(r.get("totalLines"), []).append((r.get("time"), hit))
    for rev in sorted(per, reverse=True):
        print("rev=%s" % rev)
        for t, hit in sorted(per[rev])[:3]:
            print("   t=%s  %s" % (t, [(n, s[:60]) for n, s in hit]))


if __name__ == "__main__":
    main()
