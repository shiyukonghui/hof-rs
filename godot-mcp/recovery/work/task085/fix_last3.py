# -*- coding: utf-8 -*-
"""TASK-085 fixes for two of the last three modules.

A. tools/editor_node_write.cpp (6 x C3861)
   TASK-016/017 hoisted the three helpers into `tools/tool_helpers.*`:
   `MCPTools::edited_scene_root()` (tool_helpers.h:602),
   `MCPTools::find_node()`        (tool_helpers.h:680),
   `MCPTools::relative_path()`    (tool_helpers.h:608).
   The file uses the hoisted spellings everywhere except six call sites at lines
   390/395/418 and 448/453/464, which still carry the old private names.  Fix:
   rename exactly those six, matching the file's own established spelling
   (`MCPTools::` for the two that are also spelled that way at 502/507, bare
   `relative_path(` which is how the other twelve sites call it).

B. tools/project_write_resource_scene.cpp (15 errors)
   The tree copy has lost `_property_table` entirely, `_require_properties` is
   defined after its first use, and a brace in `_write_resource_properties` is
   unmatched (C1075 at 482).  The strict replay of the recorded write + edits is
   internally coherent and carries both helpers, so it replaces the tree copy.
   Recorded shortfall: the replay is 775 lines against the read-recorded revision
   852, i.e. 77 lines of that revision are in no recorded write or edit.

usage: python fix_last3.py [--apply]
"""
import io
import sys

sys.path.insert(0, ".")
import evfetch as E  # noqa: E402

ENW = r"H:\rebuild\godot\modules\mcp_server\tools\editor_node_write.cpp"
PWRS = r"H:\rebuild\godot\modules\mcp_server\tools\project_write_resource_scene.cpp"
PWRS_REPLAY = r"C:\Users\wyl\AppData\Local\Temp\mcp-recovery\work\task085\rep_pwrs.cpp"

RENAMES = [
    ("\tNode *root = _edited_scene_root();", "\tNode *root = MCPTools::edited_scene_root();"),
    ("\tNode *parent = _find_node(root, parent_path);", "\tNode *parent = MCPTools::find_node(root, parent_path);"),
    ('\tresult["node_path"] = _relative_path(root, node);', '\tresult["node_path"] = relative_path(root, node);'),
    ("\tNode *node = _find_node(root, path);", "\tNode *node = MCPTools::find_node(root, path);"),
    ("\tconst String resolved = _relative_path(root, node);", "\tconst String resolved = relative_path(root, node);"),
]


def fix_enw(apply):
    lines = E.lines_of(ENW)
    for old, new in RENAMES:
        hits = [i for i, l in enumerate(lines) if l == old]
        print("  %-58s -> %d site(s)" % (old.strip()[:56], len(hits)))
        for i in hits:
            lines[i] = new
    left = [(i + 1, l) for i, l in enumerate(lines)
            if "_edited_scene_root" in l or "_find_node" in l or "_relative_path" in l]
    assert not left, "old spellings left: %s" % left
    print("  editor_node_write.cpp: %d lines, no old helper name left" % len(lines))
    if apply:
        text = "\n".join(lines) + "\n"
        with io.open(ENW, "w", encoding="utf-8", newline="\n") as f:
            f.write(text)
        assert io.open(ENW, encoding="utf-8", errors="replace").read() == text


def fix_pwrs(apply):
    lines = E.lines_of(PWRS_REPLAY)
    txt = "\n".join(lines) + "\n"
    assert "_property_table" in txt and "_require_properties" in txt
    print("  project_write_resource_scene.cpp: replacing the tree copy with the %d-line replay" % len(lines))
    if apply:
        with io.open(PWRS, "w", encoding="utf-8", newline="\n") as f:
            f.write(txt)
        assert io.open(PWRS, encoding="utf-8", errors="replace").read() == txt


def main():
    apply = "--apply" in sys.argv
    print("A. editor_node_write.cpp")
    fix_enw(apply)
    print("B. project_write_resource_scene.cpp")
    fix_pwrs(apply)
    if not apply:
        print("(dry run; pass --apply to write)")


if __name__ == "__main__":
    main()
