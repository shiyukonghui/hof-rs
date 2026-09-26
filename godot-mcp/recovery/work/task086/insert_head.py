# -*- coding: utf-8 -*-
"""Insert the head of a recorded edit's `new` (the part between a marker and the
shared anchor) in front of the anchor inside the target file.

usage: python insert_head.py <event-path-substr> <seq> "<marker>" "<anchor>" <target>
"""
import io
import json
import os
import sys

IDX = r"C:\Users\wyl\AppData\Local\Temp\mcp-recovery\staging\__payload-index"


def norm(p):
    return (p or "").replace("/", "\\").lower()


sub = norm(sys.argv[1])
seq = str(sys.argv[2])
marker = sys.argv[3]
anchor = sys.argv[4]
target = sys.argv[5]

row = None
with io.open(os.path.join(IDX, "events-edit.jsonl"), "r", encoding="utf-8", errors="replace") as f:
    for line in f:
        line = line.strip()
        if not line:
            continue
        r = json.loads(line)
        if str(r.get("seq")) == seq and sub in norm(r.get("path")):
            row = r
            break
if row is None:
    raise SystemExit("FATAL: no edit seq=%s for %s" % (seq, sub))
new = row.get("new") or ""

mi = new.find(marker)
if mi < 0:
    raise SystemExit("FATAL: marker not found in the recorded new")
ai = new.find(anchor, mi)
if ai < 0:
    raise SystemExit("FATAL: anchor not found after the marker in the recorded new")
# back up to the start of the marker's line
line_start = new.rfind("\n", 0, mi) + 1
head = new[line_start:ai]
print("inserting %d bytes of recorded text before the anchor" % len(head))

text = io.open(target, encoding="utf-8").read()
n = text.count(anchor)
print("anchor occurrences in the target = %d" % n)
if n != 1:
    raise SystemExit("FATAL: refusing (anchor is not unique)")
if head in text:
    raise SystemExit("FATAL: the head is already present in the target")
updated = text.replace(anchor, head + anchor, 1)
io.open(target, "w", encoding="utf-8", newline="").write(updated)
print("inserted: %d bytes -> %d bytes" % (len(text), len(updated)))
