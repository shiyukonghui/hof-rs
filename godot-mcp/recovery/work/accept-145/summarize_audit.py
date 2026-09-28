#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import io, json, collections, os
p = os.path.join(os.path.dirname(os.path.abspath(__file__)), "audit_tool_rows.json")
d = json.load(io.open(p, "r", encoding="utf-8"))
c = collections.Counter(m["what"] for m in d["mismatches"])
print("mismatch kinds:", json.dumps(c, ensure_ascii=False))
for k in c:
    print("----", k)
    for m in [x for x in d["mismatches"] if x["what"] == k][:3]:
        print(json.dumps(m, ensure_ascii=False)[:400])
