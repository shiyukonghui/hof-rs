# -*- coding: utf-8 -*-
"""TASK-085 fix for tools/project_validate_scripts.cpp.

Two recorded facts:
  * events-edit seq=645 t=1790263251918 rewrote the registration's description
    tail `counters.);` -> `counters.)desc"));` - i.e. the file must carry the
    contract description of `docs/tools_list.renamed.json` (which ends
    "the per-category counters.").
  * the recorded read window at rev374 shows ONE registration, at lines 366-374,
    *after* `static Dictionary _schema_from_json(...)`.

The tree carries that block twice: a copy at 87-95 (correct description, wrong
place, and it cannot see `_schema_from_json` / `_tool_validate_scripts`, which is
what C3861/C2065 report) and a stale copy at 376-384 (right place, description
from an earlier task).  And `_is_script_extension` ends with the tail of
`_schema_from_json` instead of `return false;`.

Fix: set the body back to `return false;`, and replace the block at 376-384 with
the block at 87-95, deleting the misplaced copy.

usage: python fix_validate_scripts.py [--apply]
"""
import io
import sys

TREE = r"H:\rebuild\godot\modules\mcp_server\tools\project_validate_scripts.cpp"
EARLY = (87, 95)
LATE = (376, 384)
BODY = 84


def main():
    t = io.open(TREE, encoding="utf-8", errors="replace").read().split("\n")
    if t and t[-1] == "":
        t.pop()
    print("tree lines: %d" % len(t))

    early = t[EARLY[0] - 1:EARLY[1]]
    late = t[LATE[0] - 1:LATE[1]]

    assert t[BODY - 1].strip() == "return json.get_data();", t[BODY - 1]
    assert early[0].strip() == "void register_project_validate_scripts_tools(MCPToolRegistry &r_registry) {", early[0]
    assert "the per-category counters." in early[3], early[3][-60:]
    assert early[3].endswith('counters.)desc"));'), early[3][-40:]
    assert late[0].strip() == "void register_project_validate_scripts_tools(MCPToolRegistry &r_registry) {", late[0]
    assert "project_build_csharp for a C# verdict." in late[3], late[3][-60:]
    assert len(early) == len(late) == 9, (len(early), len(late))

    out = []
    for i, line in enumerate(t, 1):
        if i == BODY:
            out.append("\treturn false;")
            continue
        if EARLY[0] <= i <= EARLY[1]:
            continue
        if LATE[0] <= i <= LATE[1]:
            if i == LATE[0]:
                out.extend(early)
            continue
        out.append(line)

    print("fixed _is_script_extension body at line %d" % BODY)
    print("moved the contract registration block %d-%d over the stale %d-%d" % (EARLY + LATE))
    print("new line count: %d" % len(out))
    if "--apply" not in sys.argv:
        print("(dry run; pass --apply to write)")
        return
    text = "\n".join(out) + "\n"
    with io.open(TREE, "w", encoding="utf-8", newline="\n") as f:
        f.write(text)
    assert io.open(TREE, encoding="utf-8", errors="replace").read() == text
    print("wrote %s, read-back OK" % TREE)


if __name__ == "__main__":
    main()
