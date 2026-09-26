# -*- coding: utf-8 -*-
"""Scan modules/mcp_server/tools/*.cpp for generated registration blocks and
report which ones are EMPTY (a group that registers nothing)."""
import glob
import io
import os
import re

ROOT = r"H:\rebuild\godot\modules\mcp_server\tools"

for path in sorted(glob.glob(os.path.join(ROOT, "*.cpp"))):
    lines = io.open(path, encoding="utf-8", errors="replace").read().split("\n")
    for i, l in enumerate(lines):
        if "BEGIN generated" not in l:
            continue
        j = None
        for k in range(i + 1, len(lines)):
            if "END generated" in lines[k]:
                j = k
                break
        body = [x for x in lines[i + 1:j if j is not None else len(lines)] if x.strip()]
        # count registrations: lines mentioning register_tool / ToolBuilder / builder(
        regs = len(re.findall(r"register_into|\.register_tool|register_tool\(|ToolBuilder", "\n".join(body)))
        print("%-46s line %-5d body_lines=%-4d regs=%-3d %s" % (
            os.path.basename(path), i + 1, len(body), regs, "EMPTY" if not body else ""))
