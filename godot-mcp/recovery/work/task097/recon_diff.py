# TASK-097: show the first differing line of the reconstructed (before minus
# duplicates) scene text against the after text.
#   python recon_diff.py <run-dir>
import difflib
import json
import os
import re
import sys

RUN = sys.argv[1]


def load(tag):
    doc = json.loads(open(os.path.join(RUN, tag + ".json"), encoding="utf-8-sig").read())
    return json.loads(doc["result"]["content"][0]["text"])["text"]


AUTO = re.compile(r"^@[A-Za-z0-9_]+@\d+$")
before = load("c03-read-before")
after = load("c08-read-after")
positions = [(m.start(), m.group(1)) for m in re.finditer(r'^\[node name="([^"]+)"', before, re.M)]
stripped = before[:positions[0][0]]
for index, (start, name) in enumerate(positions):
    end = positions[index + 1][0] if index + 1 < len(positions) else len(before)
    if not AUTO.match(name):
        stripped += before[start:end]

print("same after rstrip: %s" % (stripped.rstrip("\n") == after.rstrip("\n")))
for line in difflib.unified_diff(stripped.rstrip("\n").splitlines(), after.rstrip("\n").splitlines(),
                                 "before-minus-duplicates", "after", lineterm="", n=1):
    print(line)
