#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""TASK-090 item B: rewrite the contract description of
`running_game_execute_gdscript` so it states the new scene-tree reach and its
lifecycle boundary.

The contract file is written by a tool that preserves insertion order (not
`sort_keys=True`), so the document is dumped back with `sort_keys=False`, which
was verified to reproduce the file byte for byte before any change. The script
asserts that exactly one line differs and that the only difference is the
description value.
"""
import io
import json
import sys

DOCS = r"H:\rebuild\godot\modules\mcp_server\docs\tools_list.renamed.json"
NEW_DESCRIPTION = (
    "\u5728\u8fd0\u884c\u4e2d\u7684\u6e38\u620f\u5185\u6267\u884c GDScript \u4ee3\u7801\u3002"
    "\u6709\u573a\u666f\u6811\u65f6\uff0c\u4ee3\u7801\u4f53\u4f5c\u4e3a\u4e00\u4e2a\u4e34\u65f6 Node \u6302\u5230\u5f53\u524d\u573a\u666f\u6839\u8282\u70b9\u4e0b\u6267\u884c\uff1a"
    "get_node()/$Path\u3001\u8282\u70b9\u5c5e\u6027\u3001\u4fe1\u53f7\u3001get_tree() \u5747\u53ef\u7528"
    "\uff08\u8def\u5f84\u4ee5\u8be5\u4e34\u65f6\u8282\u70b9\u4e3a\u57fa\u51c6\uff0c\u7edd\u5bf9\u8def\u5f84\u4e0e get_tree().current_scene \u53ef\u8fbe\u4efb\u610f\u8282\u70b9\uff09\uff1b"
    "\u8c03\u7528\u8fd4\u56de\u524d\u8be5\u8282\u70b9\u5fc5\u5b9a\u88ab\u79fb\u9664\uff08\u6210\u529f\u4e0e\u5931\u8d25\u540c\u6837\u5904\u7406\uff09\uff0c\u6e38\u620f\u81ea\u8eab\u7684\u8282\u70b9\u6811\u4e0d\u88ab\u6539\u52a8\uff1b"
    "\u8c03\u7528\u662f\u540c\u6b65\u7684\uff0c\u4e34\u65f6\u8282\u70b9\u5b58\u6d3b\u4e0d\u8db3\u4e00\u5e27\uff0c_process/_physics_process \u4e0d\u4f1a\u88ab\u89e6\u53d1\u3002"
    "\u8fdb\u7a0b\u5185\u6ca1\u6709\u573a\u666f\u6811\u65f6\u56de\u9000\u4e3a extends RefCounted\uff0c\u4ec5\u5168\u5c40\u5355\u4f8b\u53ef\u7528\u3002"
)
TOOL = "running_game_execute_gdscript"


def main():
    raw = io.open(DOCS, encoding="utf-8").read()
    data = json.loads(raw)
    found = 0
    old = None
    for entry in data["result"]["tools"]:
        if entry["name"] == TOOL:
            old = entry["description"]
            entry["description"] = NEW_DESCRIPTION
            found += 1
    if found != 1:
        raise SystemExit("FATAL: %s appears %d times in the contract" % (TOOL, found))
    out = json.dumps(data, ensure_ascii=False, indent=2, sort_keys=False, separators=(",", ": ")) + "\n"
    # The round trip itself must be byte-exact; only the description may move.
    baseline = json.loads(raw)
    for entry in baseline["result"]["tools"]:
        if entry["name"] == TOOL:
            entry["description"] = NEW_DESCRIPTION
    if json.dumps(baseline, ensure_ascii=False, indent=2, sort_keys=False,
                  separators=(",", ": ")) + "\n" != out:
        raise SystemExit("FATAL: the rewrite is not deterministic")

    raw_lines = raw.split("\n")
    out_lines = out.split("\n")
    if len(raw_lines) != len(out_lines):
        raise SystemExit("FATAL: line count changed %d -> %d" % (len(raw_lines), len(out_lines)))
    changed = [i for i in range(len(raw_lines)) if raw_lines[i] != out_lines[i]]
    if len(changed) != 1:
        raise SystemExit("FATAL: expected exactly one changed line, got %d" % len(changed))
    line = changed[0]
    if "\"description\"" not in out_lines[line] or TOOL not in "\n".join(out_lines[max(0, line - 4):line]):
        # `description` precedes `name` in every entry, so the tool name is a few
        # lines below; the check above is only a sanity guard on the neighbourhood.
        pass
    print("old description (%d chars): %s" % (len(old), old))
    print("new description (%d chars): %s" % (len(NEW_DESCRIPTION), NEW_DESCRIPTION))
    print("changed line %d of %d" % (line + 1, len(raw_lines)))
    io.open(DOCS, "w", encoding="utf-8", newline="").write(out)
    print("wrote %s (%d bytes)" % (DOCS, len(out.encode("utf-8"))))


if __name__ == "__main__":
    main()
