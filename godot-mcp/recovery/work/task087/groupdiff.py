# -*- coding: utf-8 -*-
"""Which contract tools are not declared by any tool-groups manifest (new names)?"""
from __future__ import print_function
import io, json, os, sys
sys.path.insert(0, r"C:\Users\wyl\AppData\Local\Temp\mcp-recovery\work\task087")
import rep

ROOT = r"H:\rebuild\godot\modules\mcp_server"
DOCS = os.path.join(ROOT, "docs")
MANIFESTS = ["tool-groups.json", "tool-groups-b2.json", "tool-groups-b3.json",
             "tool-groups-b4.json", "tool-groups-b5.json", "tool-groups-added.json"]


def main():
    contract = json.loads(io.open(os.path.join(DOCS, "tools_list.renamed.json"),
                                  encoding="utf-8-sig").read())
    new_names = set(t["name"] for t in contract["result"]["tools"])
    mapping = json.loads(io.open(os.path.join(DOCS, "tool-rename-map.json"),
                                 encoding="utf-8-sig").read())
    old2new = {}
    for e in mapping["tools"]:
        old2new[e["old_name"]] = e["new_name"]
    decl = {}
    for mf in MANIFESTS:
        p = os.path.join(DOCS, mf)
        if not os.path.exists(p):
            rep.log("%-26s MISSING" % mf)
            continue
        j = json.loads(io.open(p, encoding="utf-8-sig").read())
        impl = 0
        for g in j.get("groups") or []:
            if not g.get("implemented"):
                continue
            impl += 1
            for t in g.get("tools") or []:
                decl[old2new.get(t, t)] = mf
        rep.log("%-26s groups=%d implemented=%d" % (mf, len(j.get("groups") or []), impl))

    undeclared = sorted(n for n in new_names if n not in decl)
    rep.log("")
    rep.log("contract tools = %d ; declared in some implemented group = %d"
            % (len(new_names), len(new_names) - len(undeclared)))
    rep.log("NOT declared (%d):" % len(undeclared))
    for n in undeclared:
        rep.log("  %s" % n)
    rep.log("")
    extra = sorted(n for n in decl if n not in new_names)
    rep.log("declared but not in contract (%d): %s" % (len(extra), extra))
    rep.flush()


if __name__ == "__main__":
    main()
