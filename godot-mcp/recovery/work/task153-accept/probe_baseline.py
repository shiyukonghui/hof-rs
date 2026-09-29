"""Independent acceptance probe for TASK-153 baseline facts."""
import hashlib
import io
import json
import os

ENGINE = r"F:\moonbit-hof-rs\godot-mcp\godot"
BASE = os.path.join(ENGINE, r"modules\mcp_server\docs\rename-baseline-tools-list.json")
MAP = os.path.join(ENGINE, r"modules\mcp_server\docs\tool-rename-map.json")
FIX = r"F:\moonbit-hof-rs\tests\fixtures\mcp\tools_list.json"

for label, p in (("engine baseline", BASE), ("engine map", MAP), ("hof-rs fixture", FIX)):
    raw = io.open(p, "rb").read()
    d = json.loads(raw.decode("utf-8"))
    tools = d.get("result", {}).get("tools", d.get("tools"))
    print("%-16s bytes=%-7d cr=%d lf=%d sha256=%s"
          % (label, len(raw), raw.count(b"\r"), raw.count(b"\n"),
             hashlib.sha256(raw).hexdigest()))
    print("%-16s tools=%s" % ("", len(tools) if tools is not None else "n/a"))

raw = io.open(BASE, "rb").read()
d = json.loads(raw.decode("utf-8"))
names = [t["name"] for t in d["result"]["tools"]]
print("baseline tools=%d unique=%d" % (len(names), len(set(names))))

m = json.loads(io.open(MAP, "rb").read().decode("utf-8"))
mt = m["tools"]
print("map entries=%d" % len(mt))
print("map first entry keys=%s" % sorted(mt[0].keys()))
# find a compact needle we can safely plant against, print a few sample names
print("sample old->new:")
for e in mt[:3]:
    print("   %s -> %s (%s)" % (e.get("old_name"), e.get("new_name"), e.get("disposition")))
