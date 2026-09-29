"""Pick concrete, safe plant targets for the independent acceptance plants."""
import io
import json
import collections

ENGINE = r"F:\moonbit-hof-rs\godot-mcp\godot"
MAP = ENGINE + r"\modules\mcp_server\docs\tool-rename-map.json"
BASE = ENGINE + r"\modules\mcp_server\docs\rename-baseline-tools-list.json"

m = json.loads(io.open(MAP, "rb").read().decode("utf-8"))
print("closed_set:", m["convention"]["verb_closed_set"])

ent = m["tools"]
by_len = collections.defaultdict(list)
for e in ent:
    by_len[len(e["new_name"])].append(e)

print("\n-- entries whose new_name is NOT unique-length (candidates for duplicate plant) --")
for L, group in sorted(by_len.items()):
    if len(group) >= 2:
        for e in group:
            print("   len=%d old=%-42s new=%-46s verb=%-10s ch=%s disp=%s"
                  % (L, e["old_name"], e["new_name"], e["verb"], e["channel"], e["disposition"]))
        break

print("\n-- entries that are plain 'rename' and whose verb differs from another same-length verb --")
for e in ent[:8]:
    print("   %-45s verb=%-10s ch=%-12s disp=%-12s new=%s"
          % (e["old_name"], e["verb"], e["channel"], e["disposition"], e["new_name"]))

base = json.loads(io.open(BASE, "rb").read().decode("utf-8"))
names = [t["name"] for t in base["result"]["tools"]]
print("\nbaseline first 3 names:", names[:3])
# lengths
lens = collections.Counter(len(n) for n in names)
dup_len = [L for L, c in lens.items() if c >= 2]
print("baseline names sharing a length exist:", bool(dup_len))
for n in names:
    if len(n) == dup_len[0]:
        print("   candidate baseline name len=%d: %s" % (dup_len[0], n))
        if sum(1 for x in names if len(x) == dup_len[0]) > 1:
            pass
# print first tool object shape
print("baseline tool[0] keys:", sorted(base["result"]["tools"][0].keys()))
print("baseline tool[0] name:", base["result"]["tools"][0]["name"])
