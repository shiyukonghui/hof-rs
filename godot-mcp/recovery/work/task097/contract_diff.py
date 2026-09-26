# TASK-097 helper: show exactly what the contract regeneration changed.
import json
import sys

before = json.load(open(sys.argv[1], encoding="utf-8"))
after = json.load(open(sys.argv[2], encoding="utf-8"))


def tools(doc):
    return {t["name"]: t for t in doc["result"]["tools"]}


b = tools(before)
a = tools(after)
print("before tools=%d after tools=%d" % (len(b), len(a)))
print("added names: %s" % sorted(set(a) - set(b)))
print("removed names: %s" % sorted(set(b) - set(a)))
for name in sorted(set(a) & set(b)):
    if b[name] != a[name]:
        print("--- changed entry: %s" % name)
        old, new = b[name], a[name]
        for key in ("description", "inputSchema"):
            if old[key] != new[key]:
                print("    field: %s" % key)
                if key == "description":
                    print("      before: %s" % old[key])
                    print("      after : %s" % new[key])
                else:
                    op, np_ = old[key], new[key]
                    print("      before properties: %s" % sorted(op.get("properties", {})))
                    print("      after  properties: %s" % sorted(np_.get("properties", {})))
                    for prop in np_.get("properties", {}):
                        if op.get("properties", {}).get(prop) != np_["properties"][prop]:
                            print("      changed property: %s" % prop)
                            print("        before: %s" % json.dumps(op.get("properties", {}).get(prop), ensure_ascii=False))
                            print("        after : %s" % json.dumps(np_["properties"][prop], ensure_ascii=False))
                    if op.get("required") != np_.get("required"):
                        print("      required before=%s after=%s" % (op.get("required"), np_.get("required")))
bm, am = before["_meta"], after["_meta"]
for key in sorted(set(bm) | set(am)):
    if key == "overrides":
        print("overrides before=%d after=%d" % (len(bm.get(key, [])), len(am.get(key, []))))
        continue
    if bm.get(key) != am.get(key):
        print("_meta[%s] before=%s after=%s" % (key, bm.get(key), am.get(key)))
print("SHAPES after: count=%d added_count=%d generator_version=%s" % (
    am["count"], am["added_count"], am["generator_version"]))
