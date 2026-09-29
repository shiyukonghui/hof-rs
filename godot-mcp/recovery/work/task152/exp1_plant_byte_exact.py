"""TASK-152 non-vacuity experiment 1 (byte-exact): plant a rename regression in
the engine-side baseline and show g05 goes red on the B2 rename check ALONE.

The injection is a pure byte substitution of the tool name inside the frozen
baseline (`"name": "get_project_info"` -> `"name": "project_mcp_get_info"`).
Every other byte, including the file's whitespace and key order, is untouched -
which is exactly the property the gate's `contract-only` / `map-only` diff is
supposed to react to.

The injected name is absent from the rename map as an old_name AND as a
new_name, so the B-section diff is the only check that can move: B0 stays green
(isolating the blame) and B1 stays green (still 174 entries).
"""

import hashlib
import io
import json
import os
import subprocess
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import utf8_stdout  # noqa: F401

REPO = r"F:\moonbit-hof-rs\godot-mcp\godot"
BASELINE = os.path.join(REPO, "modules", "mcp_server", "docs", "rename-baseline-tools-list.json")
MAP = os.path.join(REPO, "modules", "mcp_server", "docs", "tool-rename-map.json")
GATE = os.path.join(REPO, "modules", "mcp_server", "docs", "scripts", "check_rename_map.py")

VICTIM = b'"name":"get_project_info"'
PLANTED = b'"name":"project_mcp_get_info"'

with io.open(MAP, encoding="utf-8") as fh:
    rmap = json.load(fh)["tools"]
old_names = {t["old_name"] for t in rmap}
new_names = {t["new_name"] for t in rmap}

raw = open(BASELINE, "rb").read()
print("PLANT victim name           : %s" % VICTIM.decode())
print("PLANT victim occurrences    : %d" % raw.count(VICTIM))
print("PLANT victim in map old_name: %s" % ("get_project_info" in old_names))
print("PLANT injected in map old   : %s" % ("project_mcp_get_info" in old_names))
print("PLANT injected in map new   : %s" % ("project_mcp_get_info" in new_names))
print("PLANT baseline bytes %d -> %d" % (len(raw), len(raw) - len(VICTIM) + len(PLANTED)))

assert raw.count(VICTIM) == 1, "victim pattern is not unique"
out = raw.replace(VICTIM, PLANTED)
with open(BASELINE, "wb") as fh:
    fh.write(out)
print("PLANT planted baseline sha256: %s" % hashlib.sha256(out).hexdigest())
print("PLANT only-the-name-differs  : %s"
      % (len(out) - len(raw) == len(PLANTED) - len(VICTIM)))
print("")

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
