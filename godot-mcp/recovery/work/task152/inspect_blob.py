import hashlib
import json
import subprocess
import sys

BLOB = "543b49b2583bf06c3aba2a320649a31eda272e3e"
raw = subprocess.run(
    ["git", "cat-file", "blob", BLOB],
    cwd=r"F:\moonbit-hof-rs",
    stdout=subprocess.PIPE,
    stderr=subprocess.PIPE,
).stdout
print("blob", BLOB)
print("bytes", len(raw))
print("sha256", hashlib.sha256(raw).hexdigest())
print("crlf", raw.count(b"\r\n"), "lf", raw.count(b"\n"))
d = json.loads(raw.decode("utf-8"))
tools = d["result"]["tools"]
print("len", len(tools))
print("top keys", list(d.keys()))
print("result keys", list(d["result"].keys()))
print("tool keys", sorted(tools[0].keys()))
print("first name", tools[0]["name"])
print("last name", tools[-1]["name"])
