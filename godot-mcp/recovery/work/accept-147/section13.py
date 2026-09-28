#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""TASK-147: independent recomputation of the section 1.3 derived counts."""
import io, re, sys

H = "godot/modules/mcp_server/tests/test_mcp_server.h"
text = io.open(H, encoding="utf-8", errors="replace").read()
lines = text.splitlines()

# every TEST_CASE with tag [MCPServer]
starts = []
for i, l in enumerate(lines):
    if "TEST_CASE(" in l:
        # tag may be on a later line; scan forward a few lines
        chunk = "\n".join(lines[i:i + 6])
        if "[MCPServer]" in chunk:
            starts.append(i)
            m = re.search(r'TEST_CASE\(\s*"([^"]*)"', chunk)
            _ = m.group(1) if m else "?"
print("TEST_CASE with [MCPServer] tag:", len(starts))
bodies = []
for idx, s in enumerate(starts):
    e = starts[idx + 1] if idx + 1 < len(starts) else len(lines)
    bodies.append("\n".join(lines[s:e]))

ILLEGAL = ["-32602", "-32601", "-32700", "-32001", "-32000", "expect_invalid",
           "invalid_params", "Missing required parameter", "must be a", "must not",
           "refuse", "reject", "is_error()", "never "]
BOUNDARY = ["empty", "zero", "cap", "limit", "over the", "too large", "oversized",
            "missing", "absent", "no_scene", "boundary", "edge", "max", "min"]
ERRCODE = ["error.code", "error.message", "error.data"]
SIDE = ["FileAccess", "DirAccess", "file", "pixel", "frame", "PNG"]
IDEM = ["identical", "idempotent", "twice", "again", "byte-identical"]


def hit_count(kws):
    return sum(1 for b in bodies if any(k in b for k in kws))


print("illegal      : %d   (matrix 114)" % hit_count(ILLEGAL))
print("boundary     : %d   (matrix 114)" % hit_count(BOUNDARY))
print("error+message: %d   (matrix 67)" % hit_count(ERRCODE))
print("side effect  : %d   (matrix 83)" % hit_count(SIDE))
print("idempotence  : %d   (matrix 34)" % hit_count(IDEM))
