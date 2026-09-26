# TASK-097: show the text of one node's serialized block in the before/after scene
# readback of a cleanup run, so a diff can be read instead of guessed.
#   python block_diff.py <run-dir> <node-name> [<node-name> ...]
import json
import os
import re
import sys

RUN = sys.argv[1]
NAMES = sys.argv[2:]


def load(tag):
    doc = json.loads(open(os.path.join(RUN, tag + ".json"), encoding="utf-8-sig").read())
    return json.loads(doc["result"]["content"][0]["text"])["text"]


def block(text, name):
    positions = [(m.start(), m.group(1)) for m in re.finditer(r'^\[node name="([^"]+)"', text, re.M)]
    for index, (start, key) in enumerate(positions):
        if key != name:
            continue
        end = positions[index + 1][0] if index + 1 < len(positions) else len(text)
        return text[start:end]
    return None


before = load("c03-read-before")
after = load("c08-read-after")
for name in NAMES:
    b = block(before, name)
    a = block(after, name)
    print("== %s : %s" % (name, "identical" if b == a else "DIFFERENT"))
    if b != a:
        print("--- before")
        print(b)
        print("--- after")
        print(a)
