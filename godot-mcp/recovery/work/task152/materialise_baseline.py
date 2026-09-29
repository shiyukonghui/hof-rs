"""TASK-152 step 1: materialise the engine-internal rename baseline.

The baseline is the verbatim bytes of the old-contract fixture as it stood
before hof-rs re-captured it (hof-rs commit db2eed7). It is read out of the
hof-rs object store with `git cat-file` (a pure read; nothing on the hof-rs
side is written), then frozen inside the engine repo so that gate g05 no
longer reaches across repository boundaries.
"""

import hashlib
import json
import os
import subprocess
import sys

HOF = r"F:\moonbit-hof-rs"
BLOB = "543b49b2583bf06c3aba2a320649a31eda272e3e"
FROZEN_SHA = "8f8051c4c0f8941089f0b21a193cef7c51fa7c41d7e312b1463ea8593f313c54"
OUT = (
    r"F:\moonbit-hof-rs\godot-mcp\godot\modules\mcp_server\docs"
    r"\rename-baseline-tools-list.json"
)

res = subprocess.run(
    ["git", "cat-file", "blob", BLOB], cwd=HOF, stdout=subprocess.PIPE, stderr=subprocess.PIPE
)
if res.returncode != 0:
    sys.exit("git cat-file failed: %s" % res.stderr.decode("utf-8", "replace"))
raw = res.stdout
sha = hashlib.sha256(raw).hexdigest()
tools = json.loads(raw.decode("utf-8"))["result"]["tools"]
print("blob        %s" % BLOB)
print("bytes       %d" % len(raw))
print("crlf=%d lf=%d bare_cr=%d" % (raw.count(b"\r\n"), raw.count(b"\n"), raw.count(b"\r")))
print("sha256      %s" % sha)
print("tools       %d" % len(tools))
assert sha == FROZEN_SHA, "blob sha %s != frozen %s" % (sha, FROZEN_SHA)
assert len(tools) == 174, "tools %d != 174" % len(tools)

with open(OUT, "wb") as fh:
    fh.write(raw)

back = open(OUT, "rb").read()
print("written     %s" % OUT)
print("written_sha %s" % hashlib.sha256(back).hexdigest())
print("equal       %s" % (back == raw))
assert back == raw
