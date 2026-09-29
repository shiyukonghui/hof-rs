#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""TASK-153 non-vacuity experiment 2 (depth): plant a WRONG MAPPING.

The map's sha256 is not frozen in the generator, so this experiment bypasses
the frozen-hash path of experiment 1 entirely: it proves the generator's
SEMANTIC self-checks still fire on a real old->new inconsistency. The plant is
a byte-exact, single-token substitution of one `new_name` (its channel prefix
is dropped, which is the L1 violation the generator lints for). Restore is
proved by a separate script.
"""
import hashlib
import json
import os
import sys

REPO = r"F:\moonbit-hof-rs\godot-mcp\godot"
MAP = os.path.join(REPO, "modules", "mcp_server", "docs", "tool-rename-map.json")

raw = open(MAP, "rb").read()
print("PLANT2 map bytes           :", len(raw))
print("PLANT2 map sha256          :", hashlib.sha256(raw).hexdigest())

mapping = json.loads(raw.decode("utf-8"))
pairs = [(e["old_name"], e["new_name"]) for e in mapping["tools"]]
print("PLANT2 map entries         :", len(pairs))
victim = sorted(n for _, n in pairs if n.startswith("editor_"))[0]
print("PLANT2 victim new_name     :", repr(victim))

needle = ('"new_name": "%s"' % victim).encode("ascii")
if raw.count(needle) != 1:
    # Compact form fallback.
    needle = ('"new_name":"%s"' % victim).encode("ascii")
print("PLANT2 needle occurrences  :", raw.count(needle))
if raw.count(needle) != 1:
    sys.exit("PLANT2: the needle is not unique; refusing to plant")

injected = victim.split("_", 1)[1]  # drop the channel prefix -> L1 violation
replacement = needle.decode("ascii").replace(victim, injected)
print("PLANT2 injected new_name   :", repr(injected))
planted = raw.replace(needle, replacement.encode("ascii"))
open(MAP, "wb").write(planted)
print("PLANT2 map bytes %d -> %d" % (len(raw), len(planted)))
print("PLANT2 planted sha256      :", hashlib.sha256(open(MAP, "rb").read()).hexdigest())
print("PLANT2 JSON still parses   :", bool(json.loads(open(MAP, encoding="utf-8").read())))
