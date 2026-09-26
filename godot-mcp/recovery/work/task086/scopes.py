# -*- coding: utf-8 -*-
"""Count the registry sizes the contract predicts, per scope.

The contract (docs/tools_list.renamed.json) is the name authority; the rename
map (docs/tool-rename-map.json) is the channel/verb/scope/mutating authority.
`registered in an editor process` = every entry; `registered in a game process`
= BOTH + GAME (ToolBuilder skips EDITOR outside an editor).
"""
import io
import json
import os
from collections import Counter

MOD = r"H:\rebuild\godot\modules\mcp_server"
contract = json.load(io.open(os.path.join(MOD, "docs", "tools_list.renamed.json"), encoding="utf-8"))
rm = json.load(io.open(os.path.join(MOD, "docs", "tool-rename-map.json"), encoding="utf-8"))

names = [t["name"] for t in contract["result"]["tools"]]
by_new = {t["new_name"]: t for t in rm["tools"]}
missing = [n for n in names if n not in by_new]
print("contract entries        : %d" % len(names))
print("rename-map entries      : %d" % len(rm["tools"]))
print("contract names NOT in rename map: %d %s" % (len(missing), missing[:10]))
scope = Counter(by_new[n]["scope"] for n in names if n in by_new)
print("scope counts            : %s" % dict(scope))
print("editor-process table    : %d" % sum(scope.values()))
print("game-process table      : %d" % (scope["both"] + scope["game"]))
print("editor-visible (true)   : %d" % (scope["both"] + scope["editor"]))
print("game-visible (false)    : %d" % (scope["both"] + scope["game"]))
print()
print("_meta of the contract   : %s" % json.dumps(contract.get("_meta", {}), ensure_ascii=False)[:800])
print()
print("rename-map top keys     : %s" % sorted(rm.keys()))
for k in sorted(rm.keys()):
    v = rm[k]
    if k != "tools":
        print("   %s = %s" % (k, json.dumps(v, ensure_ascii=False)[:400]))
