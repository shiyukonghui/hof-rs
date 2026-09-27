import json

p = r"F:\moonbit-hof-rs\godot-mcp\tools\tool_coverage_unreachable.json"
d = json.load(open(p, encoding="utf-8"))
print("top keys:", list(d))
print("total:", d.get("total"))
print("members type:", type(d.get("members")))
mem = d.get("members")
if isinstance(mem, dict):
    for k, v in mem.items():
        print("MEMBER", k, json.dumps(v, ensure_ascii=False)[:300])
else:
    for v in mem[:3]:
        print("MEMBER", json.dumps(v, ensure_ascii=False)[:300])
print()
print("categories:", json.dumps(d.get("categories"), ensure_ascii=False)[:900])
print()
rc = d.get("reclassified")
print("reclassified type:", type(rc), "len:", len(rc) if hasattr(rc, "__len__") else "?")
if isinstance(rc, list) and rc:
    print("first reclassified:", json.dumps(rc[0], ensure_ascii=False, indent=2)[:900])
elif isinstance(rc, dict):
    k = list(rc)[0]
    print("first reclassified key:", k, json.dumps(rc[k], ensure_ascii=False, indent=2)[:900])
    for kk in list(rc):
        if "export" in kk:
            print("H8 entry:", kk, json.dumps(rc[kk], ensure_ascii=False, indent=2)[:900])
