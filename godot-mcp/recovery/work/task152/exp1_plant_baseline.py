"""TASK-152 non-vacuity experiment 1: plant a rename regression in the
engine-side baseline and show g05 goes red on the B2 check.

Renames the first baseline tool to a name that is not one of the map's
`old_name`s (and that is not one of the map's `new_name`s either, so the only
check that can react is B2). Prints the three names it touched so the report can
show the exact diff, then calls the gate.
"""

import io
import json
import os
import subprocess
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import utf8_stdout  # noqa: F401  (reconfigures stdout/stderr to UTF-8)

REPO = r"F:\moonbit-hof-rs\godot-mcp\godot"
BASELINE = os.path.join(REPO, "modules", "mcp_server", "docs", "rename-baseline-tools-list.json")
MAP = os.path.join(REPO, "modules", "mcp_server", "docs", "tool-rename-map.json")
GATE = os.path.join(REPO, "modules", "mcp_server", "docs", "scripts", "check_rename_map.py")

reason = sys.argv[1] if len(sys.argv) > 1 else "plant"

with io.open(MAP, encoding="utf-8") as fh:
    rmap = json.load(fh)["tools"]
old_names = {t["old_name"] for t in rmap}
new_names = {t["new_name"] for t in rmap}

raw = open(BASELINE, "rb").read()
doc = json.loads(raw.decode("utf-8"))
tools = doc["result"]["tools"]

victim = None
for t in tools:
    cand = "project_mcp_get_info"
    if t["name"] in old_names and cand not in old_names and cand not in new_names:
        victim = t
        break
if victim is None:
    sys.exit("no injectable baseline entry found")

old_name = victim["name"]
victim["name"] = "project_mcp_get_info"
merged = json.dumps(doc, ensure_ascii=False, sort_keys=True)
out = merged.encode("utf-8")

print("INJECT victim              : %s -> %s" % (old_name, victim["name"]))
print("INJECT victim in map old   : %s" % (old_name in old_names))
print("INJECT injected in map old : %s" % (victim["name"] in old_names))
print("INJECT injected in map new : %s" % (victim["name"] in new_names))
print("INJECT baseline bytes %d -> %d" % (len(raw), len(out)))

with open(BASELINE, "wb") as fh:
    fh.write(out)

res = subprocess.run(
    [sys.executable, GATE], cwd=REPO, stdout=subprocess.PIPE, stderr=subprocess.STDOUT
)
text = res.stdout.decode("utf-8", "replace")
print(text)
print("GATE_EXIT=%d" % res.returncode)
fails = [line for line in text.splitlines() if line.startswith("[FAIL]")]
print("FAIL_LINES=%d" % len(fails))
for line in fails:
    print("  " + line)
sys.exit(0)
