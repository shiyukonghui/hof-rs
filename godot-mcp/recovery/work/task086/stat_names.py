# -*- coding: utf-8 -*-
"""Statical list of the tool names a group file registers.

Every registration in this module is `ToolBuilder builder("<name>", ...)`
followed by `builder.register_into(...)`. A `ToolBuilder` that is never
registered (a probe) is reported separately.
"""
import glob
import io
import os
import re
import sys

ROOT = r"H:\rebuild\godot\modules\mcp_server\tools"
NAME = re.compile(r'ToolBuilder\s+builder\s*\(\s*"([^"]+)"')


def names_of(path):
    text = io.open(path, encoding="utf-8", errors="replace").read()
    return NAME.findall(text)


def main():
    allnames = {}
    for path in sorted(glob.glob(os.path.join(ROOT, "*.cpp"))):
        ns = names_of(path)
        if ns:
            allnames[os.path.basename(path)] = ns
    total = 0
    for f in sorted(allnames):
        print("%-46s %2d  %s" % (f, len(allnames[f]), ", ".join(allnames[f])[:150]))
        total += len(allnames[f])
    print("TOTAL ToolBuilder declarations = %d" % total)
    if len(sys.argv) > 1:
        import json
        c = json.load(io.open(os.path.join(os.path.dirname(ROOT), "docs", "tools_list.renamed.json"), encoding="utf-8"))
        contract = set(t["name"] for t in c["result"]["tools"])
        have = set()
        for f in allnames:
            have.update(allnames[f])
        print("contract entries = %d ; declared in tools/ = %d" % (len(contract), len(have)))
        print("IN CONTRACT, NOT DECLARED (%d):" % len(contract - have))
        for n in sorted(contract - have):
            print("   %s" % n)
        print("DECLARED, NOT IN CONTRACT (%d):" % len(have - contract))
        for n in sorted(have - contract):
            print("   %s" % n)


main()
