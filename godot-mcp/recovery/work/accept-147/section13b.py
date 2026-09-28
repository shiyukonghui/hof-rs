#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""TASK-147: replicate inventory.py's [MCPServer] case segmentation and recompute section 1.3."""
import io, re

H = "godot/modules/mcp_server/tests/test_mcp_server.h"
lines = io.open(H, encoding="utf-8", errors="replace").read().splitlines()
CASE_RE = re.compile(r'^TEST_CASE\("\[MCPServer\] (.*)"\) \{')
starts = [(i, CASE_RE.match(l).group(1)) for i, l in enumerate(lines) if CASE_RE.match(l)]
print("cases matched by the inventory regex:", len(starts))
bodies = []
for idx, (i, name) in enumerate(starts):
    end = starts[idx + 1][0] if idx + 1 < len(starts) else len(lines)
    bodies.append("\n".join(lines[i:end]))

NEG = ("-32602", "-32601", "-32700", "-32001", "-32000", "expect_invalid", "invalid_params",
       "Missing required parameter", "must be a", "must not", "refuse", "reject", "is_error()",
       "never reports", "never writes", "never corrupt", "ERROR")
BND = ("empty", "zero", "cap", "limit", "over the", "too large", "oversized",
       "missing", "absent", "no_scene", "boundary", "edge", "max", "min")
ERR = ("error.code", "error.message", "error.data", "message ==", "message.contains")
EFF = ("FileAccess", "file_exists", "DirAccess", "wrote", "written", "file",
       "pixel", "frame", "screenshot", "PNG", "png")
IDEM = ("identical", "idempotent", "twice", "again", "second call", "same-content",
        "byte-identical", "already there")


def cnt(keys):
    return sum(1 for b in bodies if any(k in b for k in keys))


print("illegal      : %d   (matrix 114)" % cnt(NEG))
print("boundary     : %d   (matrix 114)" % cnt(BND))
print("error+message: %d   (matrix 67)" % cnt(ERR))
print("side effect  : %d   (matrix 83)" % cnt(EFF))
print("idempotence  : %d   (matrix 34)" % cnt(IDEM))
