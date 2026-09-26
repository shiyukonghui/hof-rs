# -*- coding: utf-8 -*-
"""task088 (4): report the six limbs of the generated contract.

usage: python meta6.py <outfile>
"""
from __future__ import print_function
import hashlib, io, json, os, sys

REPO = r"H:\rebuild\godot"
DOCS = os.path.join(REPO, "modules", "mcp_server", "docs")
CONTRACT = os.path.join(DOCS, "tools_list.renamed.json")
PINNED_SHA = "a5c59853c1e5a4913d600c663c8e972f058f7144869ec20337ab41b7a7bb17ea"


def main():
    out = sys.argv[1]
    raw = io.open(CONTRACT, "rb").read()
    sha = hashlib.sha256(raw).hexdigest()
    c = json.loads(raw.decode("utf-8"))
    meta = c["_meta"]
    rename = json.load(io.open(os.path.join(DOCS, "tool-rename-map.json"), encoding="utf-8"))
    scope = dict((t["new_name"], t.get("scope")) for t in rename["tools"])
    added = json.load(io.open(os.path.join(DOCS, "tool-groups-added.json"), encoding="utf-8"))
    for g in added["groups"]:
        for t in g["tools"]:
            scope[t] = g.get("scope")
    names = [t["name"] for t in c["result"]["tools"]]
    editor = [n for n in names if scope.get(n) != "game"]
    game = [n for n in names if scope.get(n) != "editor"]
    overrides = meta.get("overrides") or []
    kinds = {}
    for rec in overrides:
        kinds[rec["kind"]] = kinds.get(rec["kind"], 0) + 1
    lines = [
        "path            = %s" % CONTRACT,
        "bytes           = %d" % len(raw),
        "sha256          = %s" % sha,
        "pinned sha256   = %s" % PINNED_SHA,
        "sha equal       = %s" % (sha == PINNED_SHA),
        "",
        "count           = %s" % meta.get("count"),
        "added_count     = %s" % meta.get("added_count"),
        "generator_ver   = %s" % meta.get("generator_version"),
        "tool_count_in   = %s" % meta.get("tool_count_in"),
        "excluded        = %s" % meta.get("excluded"),
        "merged          = %s" % meta.get("merged"),
        "order_normative = %s" % meta.get("order_normative"),
        "editor visible  = %d" % len(editor),
        "game visible    = %d" % len(game),
        "overrides       = %d  (description=%d, inputSchema=%d)"
        % (len(overrides), kinds.get("description", 0), kinds.get("inputSchema", 0)),
        "override names  = %s" % ", ".join(sorted(set(r["old_name"] for r in overrides))),
        "",
        "map_path        = %s" % meta.get("map_path"),
        "map_sha256      = %s" % meta.get("map_sha256"),
        "generated_from  = %s" % meta.get("generated_from"),
    ]
    data = "\n".join(lines) + "\n"
    io.open(out, "w", encoding="utf-8", newline="\n").write(data)
    print(data)


if __name__ == "__main__":
    main()
