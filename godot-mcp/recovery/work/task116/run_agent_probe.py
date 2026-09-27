import io, json, os, sys

sys.path.insert(0, r"F:\moonbit-hof-rs\godot-mcp\tools")
import playtest_agent as pa

res = pa.probe(verbose=False)
out = r"F:\moonbit-hof-rs\godot-mcp\runs\playability\agent-probe.json"
with io.open(out, "w", encoding="utf-8") as fh:
    fh.write(json.dumps(res, ensure_ascii=False, indent=1))
print("ok =", res["ok"])
for k, v in res["checks"].items():
    print("  %-34s %s" % (k, v))
print("wrote", out)
