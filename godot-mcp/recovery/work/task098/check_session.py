# TASK-097: pre-flight a session file before any engine is started.
#   python check_session.py <session.json>
# Parses the JSON, checks the documented shape (calls[].tag/port/tool|method,
# resolvable content_file, sleep_ms numbers, editor/game port values) and prints
# one line per call so the run's call count is known before the run.
import json
import os
import sys

path = sys.argv[1]
with open(path, "rb") as handle:
    raw = handle.read()
try:
    text = raw.decode("utf-8")
except UnicodeDecodeError as error:
    sys.exit("FATAL: %s is not valid UTF-8: %s" % (path, error))
doc = json.loads(text)
calls = doc.get("calls")
if not isinstance(calls, list) or not calls:
    sys.exit("FATAL: 'calls' must be a non-empty array")
base = os.path.dirname(os.path.abspath(path))
tags = set()
ports = {}
for index, call in enumerate(calls):
    if not isinstance(call, dict):
        sys.exit("FATAL: calls[%d] is not an object" % index)
    if "sleep_ms" in call:
        if not isinstance(call["sleep_ms"], int) or call["sleep_ms"] <= 0:
            sys.exit("FATAL: calls[%d].sleep_ms must be a positive integer" % index)
        print("  [%02d] sleep %6d ms  %s" % (index, call["sleep_ms"], call.get("note", "")))
        continue
    tag = call.get("tag")
    port = call.get("port")
    if not tag or not isinstance(tag, str):
        sys.exit("FATAL: calls[%d] needs a string 'tag'" % index)
    if tag in tags:
        sys.exit("FATAL: duplicate tag %s" % tag)
    tags.add(tag)
    if port not in ("editor", "game"):
        sys.exit("FATAL: calls[%d].port must be editor|game (got %r)" % (index, port))
    if not call.get("tool") and not call.get("method"):
        sys.exit("FATAL: calls[%d] needs 'tool' or 'method'" % index)
    ports[port] = ports.get(port, 0) + 1
    arguments = call.get("arguments")
    if arguments is not None and not isinstance(arguments, dict):
        sys.exit("FATAL: calls[%d].arguments must be an object" % index)
    if isinstance(arguments, dict) and "content_file" in arguments:
        target = os.path.join(base, arguments["content_file"])
        if not os.path.isfile(target):
            sys.exit("FATAL: calls[%d].content_file not found: %s" % (index, target))
    print("  [%02d] %-28s port=%-6s tool=%s" % (index, tag, port, call.get("tool") or call.get("method")))
print("OK: %s (%d calls, ports=%s, import=%s)" % (path, len(calls), ports, doc.get("import", True)))
