# -*- coding: utf-8 -*-
"""task088: list the contract tool names matching a substring, with their scope.

usage: python names.py <substr> [<substr> ...]
"""
from __future__ import print_function
import io, json, os, sys

REPO = r"H:\rebuild\godot"
DOCS = os.path.join(REPO, "modules", "mcp_server", "docs")


def main():
    contract = json.load(io.open(os.path.join(DOCS, "tools_list.renamed.json"), encoding="utf-8"))
    rename = json.load(io.open(os.path.join(DOCS, "tool-rename-map.json"), encoding="utf-8"))
    scope = dict((t["new_name"], t.get("scope")) for t in rename["tools"])
    added = json.load(io.open(os.path.join(DOCS, "tool-groups-added.json"), encoding="utf-8"))
    for g in added["groups"]:
        for t in g["tools"]:
            scope[t] = g.get("scope")
    needles = [s.lower() for s in sys.argv[1:]]
    for tool in contract["result"]["tools"]:
        name = tool["name"]
        if needles and not any(n in name.lower() for n in needles):
            continue
        print("%-45s scope=%-8s desc=%s" % (name, scope.get(name, "?"), (tool["description"] or "")[:60]))


if __name__ == "__main__":
    main()
