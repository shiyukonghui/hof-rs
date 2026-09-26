# -*- coding: utf-8 -*-
"""TASK-085 fix for tools/editor_write_scene_editor.cpp.

The tree's `_tool_set_viewport_3d_camera` body (tree 730-780) is a duplicate of
the `_tool_add_resource_to_node_property` body: it declares `property` /
`resource_type` / `resource_properties`, then calls `ClassDB::get_singleton()`
(which the file's own recorded comment says does not exist: "`ClassDB` in this
fork has no singleton accessor"), then uses `node_path` without declaring it.
That block is also what leaves a stray `{` open (C1070 at 1061).

The recorded read windows carry the real body:
  * rev1088 t=1790180050322, lines 718-749  (signature + head; hoisted
    `vector3_from_json` spelling, same as the tree uses elsewhere);
  * rev1046 t=1790093622477, lines 721-760  (Node3DEditor/EditorInterface tail).
Their alignment is pinned by two shared anchors:
    rev1088 718 == rev1099 729   (the function signature; the tree has it at 729)
    rev1046 717 == rev1088 746   (the Node3DEditor::get_singleton() guard)
so rev1088 719..789 == the target's 730..800, i.e. 71 lines.

Everything written is recorded text; nothing is invented.

usage: python fix_ewse.py [--apply]
"""
import io
import sys

sys.path.insert(0, ".")
import evfetch as E  # noqa: E402

SUB = r"modules\mcp_server\tools\editor_write_scene_editor.cpp"
TREE = r"H:\rebuild\godot\modules\mcp_server\tools\editor_write_scene_editor.cpp"
FIRST = 730   # first tree line of the bad body
LAST = 780    # last tree line of the bad body


def window(sub, rev, t):
    for r in E.reads(sub):
        if r.get("totalLines") == rev and r.get("time") == t:
            return {no: txt.rstrip("\r") for no, txt in r.get("lines") or []}
    raise SystemExit("window rev%s t=%s not found" % (rev, t))


def main():
    w1088 = window(SUB, 1088, 1790180050322)
    w1046 = window(SUB, 1046, 1790093622477)
    assert w1088[718].strip().startswith("static Variant _tool_set_viewport_3d_camera"), w1088[718]
    assert w1046[717].strip() == "if (Node3DEditor::get_singleton() == nullptr) {", w1046[717]
    assert w1088[746].strip() == w1046[717].strip()
    body = [w1088[n] for n in range(719, 750)] + [w1046[n] for n in range(721, 761)]
    assert body[0].strip() == "bool has_position = false;", body[0]
    assert body[-1] == "}", repr(body[-1])
    assert "#ifdef MCP_EDITOR_TOOLS_ENABLED" in body and "#endif" in body
    assert sum(1 for l in body if l.startswith("#endif")) == 1

    lines = E.lines_of(TREE)
    assert lines[728].strip().startswith("static Variant _tool_set_viewport_3d_camera"), lines[728]
    assert lines[729].strip() == "String property;", lines[729]
    assert lines[LAST - 1].strip() == "if (instance != nullptr) {", lines[LAST - 1]
    assert lines[LAST].strip().startswith("// `saved_path`. Both key sets are the reference's."), lines[LAST]

    print("tree %d lines; replacing %d-%d (%d bad lines) with %d recorded lines"
          % (len(lines), FIRST, LAST, LAST - FIRST + 1, len(body)))
    out = lines[:FIRST - 1] + body + lines[LAST:]
    print("new line count: %d (recorded rev1099 = 1099)" % len(out))
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
