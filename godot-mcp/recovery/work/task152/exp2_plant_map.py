"""TASK-152 non-vacuity experiment 2: plant a wrong mapping in the rename map.

This is the second half of the falsification requirement - "or make one
`old_name -> new_name` mapping wrong". It attacks the *map* rather than the
baseline, so it isolates the blame onto a single check: the new_name is
rewritten to an old-style name (wrong channel prefix), which D1 (the L1 pattern
lint over all 174 new_name values) is the only check able to see. The baseline
is left untouched, so B0/B1/B2 all stay green.

Byte-exact: only the one name token inside `docs/tool-rename-map.json` changes.
"""

import hashlib
import os
import subprocess
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import utf8_stdout  # noqa: F401

REPO = r"F:\moonbit-hof-rs\godot-mcp\godot"
MAP = os.path.join(REPO, "modules", "mcp_server", "docs", "tool-rename-map.json")
BASELINE = os.path.join(REPO, "modules", "mcp_server", "docs", "rename-baseline-tools-list.json")
GATE = os.path.join(REPO, "modules", "mcp_server", "docs", "scripts", "check_rename_map.py")

VICTIM = b'"new_name": "editor_capture_screenshot"'
PLANTED = b'"new_name": "capture_screenshot"'

raw = open(MAP, "rb").read()
print("PLANT map victim name        : %s" % VICTIM.decode())
print("PLANT map victim occurrences : %d" % raw.count(VICTIM))
print("PLANT map bytes %d -> %d" % (len(raw), len(raw) - len(VICTIM) + len(PLANTED)))
assert raw.count(VICTIM) == 1, "map victim pattern is not unique"

out = raw.replace(VICTIM, PLANTED)
with open(MAP, "wb") as fh:
    fh.write(out)
print("PLANT planted map sha256     : %s" % hashlib.sha256(out).hexdigest())
print("PLANT baseline untouched sha : %s"
      % hashlib.sha256(open(BASELINE, "rb").read()).hexdigest())
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
