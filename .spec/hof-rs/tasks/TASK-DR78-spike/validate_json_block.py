"""TASK-DR78: the fence-aware validator for the report's machine-readable block.

It splits the document on ``` fences, takes only the blocks whose info string is
`json`, and runs `json.loads` on each.  It also checks that the block agrees with
the prose on the headline numbers.
"""

import json
import sys

path = sys.argv[1]
text = open(path, encoding="utf-8").read()
lines = text.split("\n")

blocks = []
in_fence = False
info = ""
buf = []
for line in lines:
    stripped = line.strip()
    if stripped.startswith("```"):
        if not in_fence:
            in_fence = True
            info = stripped[3:].strip()
            buf = []
        else:
            in_fence = False
            if info == "json":
                blocks.append("\n".join(buf))
        continue
    if in_fence:
        buf.append(line)

print("json-fenced blocks = %d" % len(blocks))
failures = 0
parsed = None
for index, block in enumerate(blocks):
    try:
        parsed = json.loads(block)
        print("block %d: json.loads OK, %d top-level key(s)" % (index, len(parsed)))
    except Exception as error:  # noqa: BLE001
        failures += 1
        print("block %d: json.loads FAILED: %s" % (index, error))

if parsed is not None:
    gate = parsed["gate"]
    for key in ("verdict", "task", "criteria", "gate"):
        if key not in parsed:
            failures += 1
            print("missing top-level key:", key)
    checks = [
        ("passed==546", gate["passed"] == 546),
        ("failed==0", gate["failed"] == 0),
        ("ignored==7", gate["ignored"] == 7),
        ("list==553", gate["list_count"] == 553),
        ("removed==1", gate["fn_declarations"]["removed"] == 1),
        ("prose says 546/0/7", "546 passed / 0 failed / 7 ignored" in text),
        ("prose says 553", "**553**" in text),
        ("prose names the smoke-t6 digest", "c144ef3219e21dd322978e41a5531d53dee270619c026585505920f9277a9c03" in text),
        ("prose names the six-plant count", "6 处" in text),
    ]
    for label, ok in checks:
        print("  %-38s %s" % (label, ok))
        if not ok:
            failures += 1

print("failures =", failures)
sys.exit(1 if failures else 0)
