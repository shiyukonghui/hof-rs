# -*- coding: utf-8 -*-
"""TASK-085 finish for tools/project_write_resource_scene.cpp (ruling C), v4.

Recorded sources:
  * replay (events-write + events-edit)            -> `_property_table`,
    `MCPTools::resource_bag_name_is_addressable`
  * rev697 t=1790165880935, lines 379-459          -> the whole
    `_tool_create_scene_file` body (the tree's copy is a splice of the
    *resource* body with the *delete-scene* tail, and the real tail is left
    orphaned outside any function at tree 470-475)
  * rev775 t=1790229066466, lines 440-490          -> `_tool_delete_scene_file`,
    whose definition the tree has lost entirely
  * the tree's own comment + the rev775/rev768 windows -> the two refusal
    sentences closing the `is_label == nullptr` branch (marked
    `// [REBUILT-2C low-confidence: verify]`)

usage: python fix_pwrs4.py [--apply]
"""
import io
import sys

sys.path.insert(0, ".")
import evfetch as E  # noqa: E402

TREE = r"H:\rebuild\godot\modules\mcp_server\tools\project_write_resource_scene.cpp"
REPLAY = r"C:\Users\wyl\AppData\Local\Temp\mcp-recovery\work\task085\rep_pwrs.cpp"
SUB = r"modules\mcp_server\tools\project_write_resource_scene.cpp"

MARK = "\t\t\t\t// [REBUILT-2C low-confidence: verify]"
RULE = "// ---------------------------------------------------------------------------"


def window(sub, rev, t):
    for r in E.reads(sub):
        if r.get("totalLines") == rev and r.get("time") == t:
            return {no: txt.rstrip("\r") for no, txt in r.get("lines") or []}
    raise SystemExit("window rev%s t=%s not found" % (rev, t))


def main():
    rep = E.lines_of(REPLAY)
    prop_table = list(rep[195:209])
    addr = list(rep[234:241])
    w697 = window(SUB, 697, 1790165880935)
    w775 = window(SUB, 775, 1790229066466)
    create_body = [w697[n] for n in range(379, 460)]
    delete_tool = [w775[n] for n in range(446, 491)]
    assert create_body[0].startswith("static Variant _tool_create_scene_file(")
    assert create_body[-1] == "}"
    assert "\tString type_name;" in create_body and "\tString root_name = requested_name;" in "\n".join(create_body)
    assert "project_delete_scene_file (old `delete_scene`, scene.rs:251)" in "\n".join(delete_tool)
    assert delete_tool[-1] == "}"

    lines = E.lines_of(TREE)
    print("tree %d lines" % len(lines))

    # 1: replace the corrupted _tool_create_scene_file (its head through the
    #    orphaned tail that follows the closing brace).
    st = [i for i, l in enumerate(lines) if l == "static Variant _tool_create_scene_file(const Dictionary &p_args, MCPToolError &r_error) {"]
    assert len(st) == 1, "create_scene_file: %d" % len(st)
    depth = 0
    en = None
    for j in range(st[0], len(lines)):
        s = lines[j].split("//", 1)[0]
        depth += s.count("{") - s.count("}")
        if j > st[0] and depth == 0:
            en = j
            break
    assert en is not None, "unbalanced _tool_create_scene_file"
    print("1: replacing tree %d-%d (%d lines) with the recorded rev697 body (%d lines)"
          % (st[0] + 1, en + 1, en + 1 - st[0], len(create_body)))
    lines = lines[:st[0]] + create_body + lines[en + 1:]

    # 2 + 3: the two missing helpers behind the local helper block.
    anchor = "\treturn String(p_name).is_valid_identifier();"
    ai = [i for i, l in enumerate(lines) if l == anchor]
    assert len(ai) == 1 and lines[ai[0] + 1].strip() == "}"
    lines = lines[:ai[0] + 2] + [""] + prop_table + [""] + addr + [""] + lines[ai[0] + 2:]
    print("2+3: inserted %d recorded lines (_property_table, resource_bag_name_is_addressable)"
          % (len(prop_table) + len(addr)))

    # 4: forward declaration.
    fwd = "\tstatic bool _require_properties(const Dictionary &p_args, Dictionary &r_out, MCPToolError &r_error);"
    fi = [i for i, l in enumerate(lines)
          if l == "\t\tDictionary &r_changed, Dictionary &r_ignored, Array &r_properties_set, MCPToolError &r_error);"]
    assert len(fi) == 1, "forward anchor: %d" % len(fi)
    lines = lines[:fi[0] + 1] + ["", "\t// The body stays where the recorded revision keeps it (next to `project_edit_resource`);", "\t// `_tool_create_resource` calls it long before that.", fwd] + lines[fi[0] + 1:]
    print("4: forward-declared _require_properties after line %d" % (fi[0] + 1))

    # 5: the lost _tool_delete_scene_file, in front of the TASK-037 comment.
    di = [i for i, l in enumerate(lines) if l.strip() == "// TASK-037 D2: the one `properties` bag writer of the two resource tools."]
    assert len(di) == 1 and lines[di[0] - 1].strip() == RULE
    lines = lines[:di[0] - 1] + delete_tool + [""] + lines[di[0] - 1:]
    print("5: inserted the recorded _tool_delete_scene_file block (%d lines)" % len(delete_tool))

    # 6: close the is_label == nullptr branch.
    si = [i for i, l in enumerate(lines) if l == "\t\t\tif (!resource_bag_name_is_addressable(key)) {"]
    assert len(si) == 1, "addressable gate: %d" % len(si)
    s = si[0]
    assert lines[s + 1].strip() == "r_error = MCPToolError::invalid_params(vformat("
    assert lines[s + 2].strip().startswith("const Variant::Type target_type = property_type_of(")
    close = [
        MARK,
        "\t\t\t\tr_error = MCPToolError::invalid_params(vformat(",
        '\t\t\t\t\t\t"Property name \'%s\' is not a settable property name: Object::set() takes a non-empty identifier",',
        "\t\t\t\t\t\tString(key)));",
        "\t\t\t\treturn false;",
        "\t\t\t}",
        "\t\t\tr_error = MCPToolError::not_found(",
        '\t\t\t\t\tvformat("Property \'%s\' on %s", String(key), p_resource->get_class()),',
        '\t\t\t\t\tvformat("\'%s\' is not a property of %s; read the properties this resource really has with "',
        '\t\t\t\t\t\t\t"project_read_resource (its \'properties\' object is exactly what this tool takes back)",',
        "\t\t\t\t\t\t\tString(key), p_resource->get_class()));",
        "\t\t\treturn false;",
        "\t\t}",
    ]
    lines = lines[:s + 1] + close + lines[s + 2:]
    print("6: closed the is_label==nullptr branch (%d lines, marked)" % len(close))
    print("new line count: %d" % len(lines))

    if "--apply" not in sys.argv:
        print("(dry run; pass --apply to write)")
        return
    text = "\n".join(lines) + "\n"
    with io.open(TREE, "w", encoding="utf-8", newline="\n") as f:
        f.write(text)
    assert io.open(TREE, encoding="utf-8", errors="replace").read() == text
    print("wrote %s, read-back OK" % TREE)


if __name__ == "__main__":
    main()
