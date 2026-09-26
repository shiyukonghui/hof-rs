# TASK-097 helper: print one tool's description and inputSchema as compact JSON
# (exactly what the C++ literal has to carry) plus the shape numbers.
import io
import json
import sys

contract = sys.argv[1]
want = sys.argv[2] if len(sys.argv) > 2 and sys.argv[2] != "-" else None
out_path = sys.argv[3] if len(sys.argv) > 3 else None

doc = json.load(open(contract, encoding="utf-8"))
tools = doc["result"]["tools"]
lines = []
if want:
    hit = [t for t in tools if t["name"] == want]
    if not hit:
        sys.exit("FATAL: no tool %s" % want)
    lines.append("DESCRIPTION:")
    lines.append(hit[0]["description"])
    lines.append("SCHEMA:")
    lines.append(json.dumps(hit[0]["inputSchema"], ensure_ascii=False, separators=(",", ":")))
else:
    meta = doc["_meta"]
    lines.append("count=%d added_count=%d generator_version=%s tools=%d" % (
        meta["count"], meta["added_count"], meta["generator_version"], len(tools)))
text = "\n".join(lines) + "\n"
if out_path:
    with io.open(out_path, "w", encoding="utf-8", newline="\n") as handle:
        handle.write(text)
    print("wrote %s (%d bytes)" % (out_path, len(text.encode("utf-8"))))
else:
    sys.stdout.write(text)
