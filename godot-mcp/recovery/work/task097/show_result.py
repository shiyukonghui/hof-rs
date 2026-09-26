# TASK-097 helper: decode an MCP response file the driver wrote
# (<run>/<tag>.json holds the raw JSON-RPC answer, whose content[0].text is the
# tool's own JSON) and print it, or one dotted key path of it.
#   python show_result.py <response.json> [key.path]
import json
import sys

raw = open(sys.argv[1], encoding="utf-8-sig").read()
doc = json.loads(raw)
text = None
if isinstance(doc, dict) and "result" in doc:
    result = doc["result"]
    content = result.get("content") if isinstance(result, dict) else None
    if content:
        text = content[0].get("text")
    else:
        text = json.dumps(result, ensure_ascii=False)
elif isinstance(doc, dict) and "error" in doc:
    text = json.dumps(doc["error"], ensure_ascii=False)
payload = json.loads(text) if text else None

if len(sys.argv) < 3:
    print(json.dumps(payload, ensure_ascii=False, indent=1))
    sys.exit(0)
value = payload
for part in sys.argv[2].split("."):
    if isinstance(value, dict):
        value = value.get(part)
    elif isinstance(value, list):
        value = value[int(part)]
    else:
        value = None
        break
print(json.dumps(value, ensure_ascii=False, indent=1) if isinstance(value, (dict, list)) else value)
