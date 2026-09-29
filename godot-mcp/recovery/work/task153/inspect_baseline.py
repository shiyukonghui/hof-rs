#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Show the exact byte shape of the baseline around the first `name` key."""
import os

BASE = r"F:\moonbit-hof-rs\godot-mcp\godot\modules\mcp_server\docs\rename-baseline-tools-list.json"
raw = open(BASE, "rb").read()
print("bytes:", len(raw))
print("newlines:", raw.count(b"\n"), "crlf:", raw.count(b"\r\n"))
i = raw.find(b'"name"')
print("first name key offset:", i)
print("context:", raw[i - 40:i + 80])
for probe in (b'"name":"', b'"name": "', b'"name"'):
    print("count", probe, "=", raw.count(probe))
