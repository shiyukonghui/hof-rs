# -*- coding: utf-8 -*-
"""Structural diff of two tools_list.renamed.json files."""
import io
import json
import sys

a = json.load(io.open(sys.argv[1], encoding="utf-8"))
b = json.load(io.open(sys.argv[2], encoding="utf-8"))


def by(doc):
    return {t["name"]: t for t in doc["result"]["tools"]}


A, B = by(a), by(b)
print("tools: %d -> %d" % (len(A), len(B)))
print("names only in A: %s" % sorted(set(A) - set(B)))
print("names only in B: %s" % sorted(set(B) - set(A)))
diff = 0
for n in sorted(set(A) & set(B)):
    if A[n] != B[n]:
        diff += 1
        for field in sorted(set(A[n]) | set(B[n])):
            if A[n].get(field) != B[n].get(field):
                print("--- %s .%s" % (n, field))
                print("    A: %s" % json.dumps(A[n].get(field), ensure_ascii=False, sort_keys=True)[:400])
                print("    B: %s" % json.dumps(B[n].get(field), ensure_ascii=False, sort_keys=True)[:400])
print("tools whose entry differs: %d" % diff)
print()
ma, mb = a.get("_meta", {}), b.get("_meta", {})
for k in sorted(set(ma) | set(mb)):
    if k == "overrides":
        oa = [(r.get("kind"), r.get("old_name")) for r in ma.get(k, [])]
        ob = [(r.get("kind"), r.get("old_name")) for r in mb.get(k, [])]
        print("_meta.overrides: %d -> %d" % (len(oa), len(ob)))
        print("   added  : %s" % [x for x in ob if x not in oa])
        print("   removed: %s" % [x for x in oa if x not in ob])
        continue
    if ma.get(k) != mb.get(k):
        print("_meta.%s: %r -> %r" % (k, ma.get(k), mb.get(k)))
for k in sorted(set(a) | set(b) - set(a)):
    pass
print()
print("top-level keys: %s -> %s" % (sorted(a.keys()), sorted(b.keys())))
