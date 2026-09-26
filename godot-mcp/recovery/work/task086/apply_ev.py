# -*- coding: utf-8 -*-
"""Apply one recorded edit (events-edit `seq`) to a file in the tree.

The recorded `old` must appear EXACTLY ONCE in the target, otherwise the edit is
refused (no guessing). The recorded `new` is written verbatim.

usage: python apply_ev.py <event-path-substr> <seq> <target-file> [--check]
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
check_only = "--check" in sys.argv

row = None
with io.open(os.path.join(IDX, "events-edit.jsonl"), "r", encoding="utf-8", errors="replace") as f:
    for line in f:
        line = line.strip()
        if not line:
            continue
        r = json.loads(line)
        if str(r.get("seq")) != seq:
            continue
        if sub not in norm(r.get("path")):
            continue
        row = r
        break
if row is None:
    raise SystemExit("FATAL: no edit seq=%s for %s" % (seq, sub))

old = row.get("old") or ""
new = row.get("new") or ""
if not old:
    raise SystemExit("FATAL: the recorded edit has an empty old text")
res = row.get("result") or ""
if res.lstrip().startswith("Error"):
    raise SystemExit("FATAL: the recorded edit was REFUSED by the tool: %s" % res[:120])

text = io.open(target, encoding="utf-8").read()
n = text.count(old)
print("target=%s bytes=%d  occurrences of the recorded old = %d" % (target, len(text), n))
if n != 1:
    raise SystemExit("FATAL: the recorded old does not appear exactly once in the target (refusing)")
if check_only:
    print("CHECK OK - the recorded old is present exactly once")
    raise SystemExit(0)
updated = text.replace(old, new, 1)
io.open(target, "w", encoding="utf-8", newline="").write(updated)
print("applied seq=%s: %d bytes -> %d bytes" % (seq, len(text), len(updated)))
