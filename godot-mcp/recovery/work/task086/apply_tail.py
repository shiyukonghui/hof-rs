# -*- coding: utf-8 -*-
"""Apply the tail of one recorded edit: the part of the recorded `old` that
starts at `anchor`, replaced by the matching part of the recorded `new`
(everything after the same anchor, or the whole `new` when `--new-all`).

The anchor must occur exactly once in the recorded `old` and exactly once in the
target, otherwise the edit is refused.

usage:
  python apply_tail.py <event-path-substr> <seq> "<anchor>" <target-file> [--check] [--new-all]
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
anchor = sys.argv[3]
target = sys.argv[4]
check_only = "--check" in sys.argv
new_all = "--new-all" in sys.argv

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

old = row.get("old") or ""
new = row.get("new") or ""
res = (row.get("result") or "").lstrip()
if res.startswith("Error"):
    raise SystemExit("FATAL: the recorded edit was refused: %s" % res[:120])
if old.count(anchor) != 1:
    raise SystemExit("FATAL: the anchor occurs %d times in the recorded old" % old.count(anchor))

old_tail = old[old.index(anchor):]
new_tail = new if new_all else new[new.index(anchor):]
if not new_all and new.count(anchor) != 1:
    raise SystemExit("FATAL: the anchor occurs %d times in the recorded new" % new.count(anchor))

text = io.open(target, encoding="utf-8").read()
n = text.count(old_tail)
print("target=%s bytes=%d  recorded old-tail (%d bytes) occurrences = %d" % (target, len(text), len(old_tail), n))
if n != 1:
    raise SystemExit("FATAL: the recorded old-tail is not present exactly once (refusing)")
if check_only:
    print("CHECK OK")
    raise SystemExit(0)
updated = text.replace(old_tail, new_tail, 1)
io.open(target, "w", encoding="utf-8", newline="").write(updated)
print("applied seq=%s tail from anchor: %d bytes -> %d bytes" % (seq, len(text), len(updated)))
