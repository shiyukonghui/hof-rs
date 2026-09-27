import json, sys

d = json.load(open(r"F:\moonbit-hof-rs\godot-mcp\coverage.json", encoding="utf-8"))

want = ["project_get_export_info", "project_list_export_presets"]
tools = d["tools"]
by_name = {}
if isinstance(tools, dict):
    by_name = tools
else:
    for rec in tools:
        by_name[rec.get("tool") or rec.get("name")] = rec
for name in want:
    rec = by_name.get(name)
    if rec is None:
        print("MISSING", name)
        continue
    keep = {k: v for k, v in rec.items() if k not in ("calls_detail",)}
    print(name, json.dumps(keep, ensure_ascii=False, indent=2)[:1600])
    print("-" * 60)

print("buckets:", d["buckets"])
print("status :", d["status_counts"])
print("tiers  :", d["evidence_tier_counts"])
print("corpus :", d["corpus"])
