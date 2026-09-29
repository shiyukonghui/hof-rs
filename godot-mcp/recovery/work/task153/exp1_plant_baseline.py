#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""TASK-153 non-vacuity experiment 1 (mandated): plant a real difference in the
ENGINE-INTERNAL baseline.

The plant is a same-length, byte-exact, single-token substitution of one tool
`name` in the frozen baseline. It keeps the JSON valid, keeps the byte count
IDENTICAL (so the generator cannot be passing/failing on a length heuristic)
and leaves every other byte of the file untouched. The generator must then fail
(non-zero exit); the caller captures its output. A separate script restores and
proves the restore.
"""
import hashlib
import json
import os
import sys

REPO = r"F:\moonbit-hof-rs\godot-mcp\godot"
BASE = os.path.join(REPO, "modules", "mcp_server", "docs", "rename-baseline-tools-list.json")
MAP = os.path.join(REPO, "modules", "mcp_server", "docs", "tool-rename-map.json")


def sha(path):
    return hashlib.sha256(open(path, "rb").read()).hexdigest()


raw = open(BASE, "rb").read()
print("PLANT baseline bytes        :", len(raw))
print("PLANT baseline sha256       :", hashlib.sha256(raw).hexdigest())
print("PLANT frozen sha256         :",
      "8f8051c4c0f8941089f0b21a193cef7c51fa7c41d7e312b1463ea8593f313c54")

mapping = json.load(open(MAP, encoding="utf-8"))
old_names = {e["old_name"] for e in mapping["tools"]}
contract = json.loads(raw.decode("utf-8"))
names = [t["name"] for t in contract["result"]["tools"]]
print("PLANT tool names in baseline:", len(names))
print("PLANT all names are map old_names:", set(names) == old_names)

victim = sorted(old_names)[0]
print("PLANT victim name           :", repr(victim))
needle = ('"name":"%s"' % victim).encode("ascii")
count = raw.count(needle)
print("PLANT needle occurrences    :", count)
if count != 1:
    sys.exit("PLANT: the needle is not unique; refusing to plant")

# Same-length edit: the LAST character of the victim name becomes 'x'. The file
# size therefore does not move a single byte.
injected = victim[:-1] + ("x" if victim[-1] != "x" else "y")
replacement = '"name":"%s"' % injected
print("PLANT injected name         :", repr(injected))
planted = raw.replace(needle, replacement.encode("ascii"))
print("PLANT baseline bytes %d -> %d" % (len(raw), len(planted)))
if len(planted) != len(raw):
    sys.exit("PLANT: the substitution changed the byte count; refusing to plant")
open(BASE, "wb").write(planted)
print("PLANT planted sha256        :", sha(BASE))
print("PLANT JSON still parses     :", bool(json.loads(open(BASE, encoding="utf-8").read())))
print("PLANT byte count unchanged  :", os.path.getsize(BASE) == len(raw))
back = planted.replace(replacement.encode("ascii"), needle)
print("PLANT reversal restores the original bytes:", back == raw)
