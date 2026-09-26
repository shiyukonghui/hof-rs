# TASK-097 helper: dump the inputSchema of several tools to one UTF-8 file.
import io
import json
import sys

contract = sys.argv[1]
out_path = sys.argv[2]
names = sys.argv[3:]
doc = json.load(open(contract, encoding="utf-8"))
by_name = {t["name"]: t for t in doc["result"]["tools"]}
lines = []
for name in names:
    entry = by_name.get(name)
    if entry is None:
        lines.append("== %s : NOT IN CONTRACT" % name)
        continue
    lines.append("== %s" % name)
    lines.append("desc: %s" % entry["description"])
    lines.append(json.dumps(entry["inputSchema"], ensure_ascii=False, indent=1))
with io.open(out_path, "w", encoding="utf-8", newline="\n") as handle:
    handle.write("\n".join(lines) + "\n")
print("wrote %s" % out_path)
