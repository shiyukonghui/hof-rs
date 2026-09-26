import io, json, os, hashlib

R = r"C:\Users\wyl\AppData\Local\Temp\mcp-recovery"
W = os.path.join(R, "rebuild", "work2b")

gen = json.load(io.open(os.path.join(R, "rebuild", "godot", "modules", "mcp_server", "docs", "tools_list.renamed.json"), encoding="utf-8"))
lc = json.load(io.open(os.path.join(R, "rebuild", "_low-confidence", "modules", "mcp_server", "docs", "tools_list.renamed.json"), encoding="utf-8"))
print("generated: count=%s added_count=%s gen_version=%s tools=%d overrides=%s" % (
    gen["_meta"].get("count"), gen["_meta"].get("added_count"), gen["_meta"].get("generator_version"),
    len(gen["result"]["tools"]), len(gen["_meta"].get("overrides", []))))
print("low-conf archived contract: count=%s added_count=%s gen_version=%s tools=%d overrides=%s" % (
    lc["_meta"].get("count"), lc["_meta"].get("added_count"), lc["_meta"].get("generator_version"),
    len(lc["result"]["tools"]), len(lc["_meta"].get("overrides", []))))

def byname(obj):
    return {t["name"]: t for t in obj["result"]["tools"]}

A = byname(gen)
B = byname(lc)
print("names equal:", set(A) == set(B))
onlyA = sorted(set(A) - set(B)); onlyB = sorted(set(B) - set(A))
print("only in generated:", onlyA)
print("only in low-conf  :", onlyB)
diff_desc = [n for n in sorted(set(A) & set(B)) if A[n]["description"] != B[n]["description"]]
diff_sch = [n for n in sorted(set(A) & set(B)) if json.dumps(A[n]["inputSchema"], sort_keys=True, ensure_ascii=False) != json.dumps(B[n]["inputSchema"], sort_keys=True, ensure_ascii=False)]
print("descriptions differing vs archived contract: %d" % len(diff_desc), diff_desc)
print("schemas differing vs archived contract: %d" % len(diff_sch), diff_sch)
for n in diff_desc[:5]:
    print("   %s: gen=%d chars, archived=%d chars" % (n, len(A[n]["description"]), len(B[n]["description"])))
# meta diff
print("meta keys gen:", sorted(gen["_meta"].keys()))
print("meta keys low:", sorted(lc["_meta"].keys()))
for k in sorted(set(gen["_meta"]) | set(lc["_meta"])):
    a = gen["_meta"].get(k); b = lc["_meta"].get(k)
    if k == "overrides":
        continue
    if a != b:
        print("   meta.%s: gen=%r low=%r" % (k, a, b))
