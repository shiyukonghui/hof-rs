#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""TASK-147: independent cross-checks of the TC-PY accounting."""
import io, os, re, json, collections

ROOT = "."
text = io.open("recovery/TEST-CASES.md", encoding="utf-8").read()
d = json.load(io.open("recovery/work/accept-147/recount.json", encoding="utf-8"))
rows = d["ids"]["TC-PY"]
per_file = collections.Counter(i.split(":", 1)[0] for _, i in rows)
print("TC-PY rows per file:", sorted(per_file.items()))
print("TC-PY rows total  :", sum(per_file.values()))

print("\n-- def test_ per file (independent regex) --")
for name in sorted(os.listdir("tools/tests")):
    if not name.endswith(".py"):
        continue
    src = io.open(os.path.join("tools/tests", name), encoding="utf-8").read()
    print("  %-40s %d" % (name, len(re.findall(r"^def test_[A-Za-z0-9_]*\(", src, re.M))))

print("\n-- note-kind breakdown of TC-PY rows --")


def kind(note):
    if u"pytest \u6761\u76ee" in note:
        return "pytest"
    if u"\u811a\u672c\u5185 check" in note:
        return "script_check"
    if u"\u81ea\u6253\u5370\u7684 case \u540d" in note:
        return "printed"
    return "unknown"

kinds = collections.Counter()
for ln, i in rows:
    # note is the second-to-last cell
    line = text.splitlines()[ln - 1]
    cells = [c.strip() for c in line.split("|")]
    kinds[kind(cells[-2])] += 1
print(dict(kinds))

print("\n-- TC-PY note-kind per src file --")
per = collections.defaultdict(collections.Counter)
for ln, i in rows:
    line = text.splitlines()[ln - 1]
    cells = [c.strip() for c in line.split("|")]
    per[i.split(":", 1)[0]][kind(cells[-2])] += 1
for k in sorted(per):
    print("  %-40s %s" % (k, dict(per[k])))
