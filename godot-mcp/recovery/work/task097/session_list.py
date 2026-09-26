# TASK-097 helper: print one session file's call list as one line per call.
#   python session_list.py <session.json>
import json
import sys

doc = json.load(open(sys.argv[1], encoding="utf-8"))
calls = doc["calls"]
print("%s: %d calls, import=%s" % (sys.argv[1], len(calls), doc.get("import", True)))
for call in calls:
    if "sleep_ms" in call:
        print("  sleep %6d ms  %s" % (call["sleep_ms"], call.get("note", "")))
        continue
    args = json.dumps(call.get("arguments", {}), ensure_ascii=False)
    if len(args) > 150:
        args = args[:150] + "..."
    print("  %-34s %-6s %-38s %s" % (call.get("tag"), call.get("port"), call.get("tool") or call.get("method"), args))
