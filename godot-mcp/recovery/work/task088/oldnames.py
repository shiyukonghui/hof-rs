# -*- coding: utf-8 -*-
"""task088: print the fixture `old_name` for each new tool name.

usage: python oldnames.py <new-name> [...]
"""
from __future__ import print_function
import io, json, os, sys

REPO = r"H:\rebuild\godot"
MAP = os.path.join(REPO, "modules", "mcp_server", "docs", "tool-rename-map.json")


def main():
    m = json.load(io.open(MAP, encoding="utf-8"))
    by_new = dict((t["new_name"], t.get("old_name")) for t in m["tools"])
    for name in sys.argv[1:]:
        print("%-40s old_name=%s" % (name, by_new.get(name, "<not a ported tool>")))


if __name__ == "__main__":
    main()
