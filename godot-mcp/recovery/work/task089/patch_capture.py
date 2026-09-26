import io
import json
import sys

path = sys.argv[1]
rows = [json.loads(line) for line in io.open(path, encoding="utf-8") if line.strip()]
for row in rows:
    if row.get("method") == "tools/call" and row.get("seq", 0) <= 3:
        row.setdefault("capture", {"mode": "every_call", "viewport": "2d", "status": "pending"})
with io.open(path, "w", encoding="utf-8", newline="\n") as handle:
    for row in rows:
        handle.write(json.dumps(row, sort_keys=True) + "\n")
print("patched", path, len(rows), "rows")
