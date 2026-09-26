# TASK-097 helper: assert that the C++ registration literals of one tool are the
# contract's own text, before spending a build on it.
#   python check_literal.py <cpp-file> <contract.json> <tool-name>
import json
import sys

cpp_path, contract_path, tool_name = sys.argv[1], sys.argv[2], sys.argv[3]
text = open(cpp_path, encoding="utf-8").read()
anchor = 'ToolBuilder builder("%s"' % tool_name
start = text.find(anchor)
if start < 0:
    sys.exit("FATAL: no registration block for %s in %s" % (tool_name, cpp_path))
window = text[start:]
desc_open = window.find('R"desc(')
desc_close = window.find(')desc"')
schema_open = window.find('R"schema(')
schema_close = window.find(')schema"')
if -1 in (desc_open, desc_close, schema_open, schema_close):
    sys.exit("FATAL: could not find both literals after the anchor")
literal_desc = window[desc_open + len('R"desc('):desc_close]
literal_schema = window[schema_open + len('R"schema('):schema_close]

doc = json.load(open(contract_path, encoding="utf-8"))
entry = [t for t in doc["result"]["tools"] if t["name"] == tool_name][0]

ok = True
if literal_desc != entry["description"]:
    ok = False
    print("DESCRIPTION MISMATCH")
    print("  cpp     : %s" % literal_desc)
    print("  contract: %s" % entry["description"])
else:
    print("description: byte-identical (%d chars)" % len(literal_desc))

got = json.loads(literal_schema)
if got != entry["inputSchema"]:
    ok = False
    print("SCHEMA MISMATCH")
    print("  cpp     : %s" % json.dumps(got, ensure_ascii=False, sort_keys=True))
    print("  contract: %s" % json.dumps(entry["inputSchema"], ensure_ascii=False, sort_keys=True))
else:
    print("inputSchema: object-identical (properties=%s)" % sorted(got["properties"]))
print("RESULT: %s" % ("PASS" if ok else "FAIL"))
sys.exit(0 if ok else 1)
