# -*- coding: utf-8 -*-
"""Show the raw bytes/strings of the failing CJK assertions in a doctest log."""
import io
import sys

sys.stdout.reconfigure(encoding="utf-8")

log = r"C:\Users\wyl\AppData\Local\Temp\mcp-recovery\logs\task086_run2.stdout.txt"
text = io.open(log, encoding="utf-8", errors="replace").read()
lines = text.split("\n")
for i, l in enumerate(lines):
    if "test_mcp_server.h(3240)" in l or "test_mcp_server.h(3286)" in l or "test_mcp_server.h(3302)" in l:
        print("---- line %d" % (i + 1))
        for j in range(i, min(i + 3, len(lines))):
            print(repr(lines[j]))
