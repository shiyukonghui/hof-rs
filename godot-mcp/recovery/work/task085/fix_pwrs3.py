# -*- coding: utf-8 -*-
"""TASK-085 finish for tools/project_write_resource_scene.cpp (ruling C), v3.

Four edits, three of them verbatim recorded text and one a marker-registered
minimal completion:

  1. `_property_table()`      - recorded: replay lines 196-209.
  2. `MCPTools::resource_bag_name_is_addressable()` - recorded: replay 235-241.
  3. `_tool_delete_scene_file()` + its comment - recorded: rev775 t=1790229066466
     lines 440-490 (its definition is used by the registration and was missing
     from the tree).
  4. forward declaration of `_require_properties` before its first use (it is
     defined at 564 and used at 375) - a declaration, no body moved.
  5. `_write_resource_properties`'s `if (is_label == nullptr) {` branch: the tree
     opens `MCPToolError::invalid_params(vformat(` and then jumps into the older
     revision's tail. The branch is closed with the minimal completion the
     surrounding recorded comment prescribes, using the two refusal sentences
     recorded verbatim in the rev775/rev768 windows, marked
     `// [REBUILT-2C low-confidence: verify]`.

usage: python fix_pwrs3.py [--apply]
"""
import io
import sys

sys.path.insert(0, ".")
import evfetch as E  # noqa: E402

TREE = r"H:\rebuild\godot\modules\mcp_server\tools\project_write_resource_scene.cpp"
REPLAY = r"C:\Users\wyl\AppData\Local\Temp\mcp-recovery\work\task085\rep_pwrs.cpp"
SUB = r"modules\mcp_server\tools\project_write_resource_scene.cpp"

MARK = "\t\t\t\t// [REBUILT-2C low-confidence: verify]"


def window(sub, rev, t):
    for r in E.reads(sub):
        if r.get("totalLines") == rev and r.get("time") == t:
            return {no: txt.rstrip("\r") for no, txt in r.get("lines") or []}
    raise SystemExit("window rev%s t=%s not found" % (rev, t))


def main():
    rep = E.lines_of(REPLAY)
    prop_table = list(rep[195:209])
    addr = list(rep[234:241])
    w775 = window(SUB, 775, 1790229066466)
    delete_tool = [w775[n] for n in range(440, 491)]
    assert "static Variant _tool_delete_scene_file(" in "\n".join(delete_tool)
    assert delete_tool[-1] == "}", repr(delete_tool[-1])

    lines = E.lines_of(TREE)
    print("tree %d lines" % len(lines))

    # 1 + 2 -------------------------------------------------------------------
    anchor = "\treturn String(p_name).is_valid_identifier();"
    ai = [i for i, l in enumerate(lines) if l == anchor]
    assert len(ai) == 1 and lines[ai[0] + 1].strip() == "}"
    ins = ai[0] + 2
    lines = lines[:ins] + [""] + prop_table + [""] + addr + [""] + lines[ins:]
    print("1+2: inserted %d recorded lines (_property_table, resource_bag_name_is_addressable)" % (len(prop_table) + len(addr)))

    # 3 -----------------------------------------------------------------------
    di = [i for i, l in enumerate(lines) if l.strip() == "// TASK-037 D2: the one `properties` bag writer of the two resource tools."]
    assert len(di) == 1, "TASK-037 comment anchor: %d" % len(di)
    assert lines[di[0] - 1].strip() == "// ---------------------------------------------------------------------------", lines[di[0] - 1]
    lines = lines[:di[0] - 1] + delete_tool + [""] + lines[di[0] - 1:]
    print("3: inserted the recorded _tool_delete_scene_file block (%d lines)" % len(delete_tool))

    # 4 -----------------------------------------------------------------------
    fwd = "\tstatic bool _require_properties(const Dictionary &p_args, Dictionary &r_out, MCPToolError &r_error);"
    fi = [i for i, l in enumerate(lines)
          if l == "\t\tDictionary &r_changed, Dictionary &r_ignored, Array &r_properties_set, MCPToolError &r_error);"]
    assert len(fi) == 1, "forward-declaration anchor: %d" % len(fi)
    lines = lines[:fi[0] + 1] + ["", "\t// The body stays where the recorded revision keeps it (next to `project_edit_resource`);", "\t// `_tool_create_resource` calls it long before that.", fwd] + lines[fi[0] + 1:]
    print("4: forward-declared _require_properties after line %d" % (fi[0] + 1))

    # 5 -----------------------------------------------------------------------
    si = [i for i, l in enumerate(lines) if l == "\t\t\tif (!resource_bag_name_is_addressable(key)) {"]
    assert len(si) == 1, "addressable gate: %d" % len(si)
    s = si[0]
    assert lines[s + 1].strip() == "r_error = MCPToolError::invalid_params(vformat("
    assert lines[s + 2].strip().startswith("const Variant::Type target_type = property_type_of("), lines[s + 2]
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
    print("5: closed the is_label==nullptr branch at line %d (%d lines, marked)" % (s + 2, len(close)))
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
