# -*- coding: utf-8 -*-
"""Replace one span of the tree with the recorded `new` of an edit.

The tree span is given by a start line and an end line (1-based, inclusive) and
both boundaries are asserted before the write.

usage: python span_from_edit.py <event-path-substr> <seq> <target> <start> <end>
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
target = sys.argv[3]
start = int(sys.argv[4])
end = int(sys.argv[5])

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
if (row.get("result") or "").lstrip().startswith("Error"):
    raise SystemExit("FATAL: the recorded edit was refused")

text = io.open(target, encoding="utf-8").read()
lines = text.split("\n")
print("start line: %r" % lines[start - 1][:90])
print("end   line: %r" % lines[end - 1][:90])
if not lines[start - 1].startswith("// ---"):
    raise SystemExit("FATAL: the start line is not a comment rule")
if lines[end - 1].rstrip() != "}":
    raise SystemExit("FATAL: the end line is not a closing brace")
block = "\n".join(lines[start - 1:end])
print("tree span bytes=%d lines=%d ; recorded new bytes=%d lines=%d" % (
    len(block), end - start + 1, len(new), len(new.split("\n"))))
if text.count(block) != 1:
    raise SystemExit("FATAL: the tree span is not unique")
out = text.replace(block, new.rstrip("\n"), 1)
io.open(target, "w", encoding="utf-8", newline="").write(out)
print("replaced: %d bytes -> %d bytes" % (len(text), len(out)))
