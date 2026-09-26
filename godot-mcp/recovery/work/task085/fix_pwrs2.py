# -*- coding: utf-8 -*-
"""TASK-085 finish for tools/project_write_resource_scene.cpp (ruling C).

The tree copy is the *later* revision (TASK-049 property-table writer) but it has
lost three things and has one glued-in stale tail:

  1. `_property_table()` - used at line 480, defined nowhere. Its body is
     recorded verbatim in the replay (events-write seq + the later edits):
     replay lines 196-209.
  2. `MCPTools::resource_bag_name_is_addressable()` - used at line 506, defined
     nowhere. Recorded verbatim: replay lines 235-241.
  3. `_require_properties()` is defined at 564 but first used at 375. A forward
     declaration in the file's own `namespace {` block restores the ordering
     without moving any recorded body.
  4. `_write_resource_properties`'s `if (is_label == nullptr) {` branch opens at
     507 and then jumps straight into the *older* revision's tail (tree 508-537,
     which is rev775's 548-577). The branch is closed with the minimal,
     behaviour-preserving completion the tree's own comment prescribes
     ("a name that is not a name at all is the argument's fault (-32602); a
     well-formed name the table does not carry is an unknown property (-32001,
     naming it)"), using the two refusal sentences recorded verbatim in the
     rev775/rev768 windows of this same helper. It is marked
     `// [REBUILT-2C low-confidence: verify]` and registered in
     REBUILT-2C-MANIFEST.md.

usage: python fix_pwrs2.py [--apply]
"""
import io
import sys

sys.path.insert(0, ".")
import evfetch as E  # noqa: E402

TREE = r"H:\rebuild\godot\modules\mcp_server\tools\project_write_resource_scene.cpp"
REPLAY = r"C:\Users\wyl\AppData\Local\Temp\mcp-recovery\work\task085\rep_pwrs.cpp"

MARK = "\t\t\t// [REBUILT-2C low-confidence: verify]"


def main():
    rep = E.lines_of(REPLAY)
    prop_table = [l for l in rep[195:209]]                 # replay 196-209
    addr = [l for l in rep[234:241]]                       # replay 235-241 (blank + ns + fn + close)
    assert prop_table[0].strip().startswith("static HashMap<StringName, bool> _property_table"), prop_table[0]
    assert prop_table[-1].strip() == "}"
    assert "namespace MCPTools {" in "\n".join(addr)
    assert "resource_bag_name_is_addressable" in "\n".join(addr)

    lines = E.lines_of(TREE)
    print("tree %d lines" % len(lines))

    # --- 1+2: insert the two missing helpers behind the local helper block -----
    anchor = "\treturn String(p_name).is_valid_identifier();"
    ai = [i for i, l in enumerate(lines) if l == anchor]
    assert len(ai) == 1, "is_settable_property_name body anchor: %d hits" % len(ai)
    assert lines[ai[0] + 1].strip() == "}", lines[ai[0] + 1]
    ins = ai[0] + 2
    block = [""] + prop_table + [""] + addr + [""]
    print("inserting %d recorded lines (_property_table + resource_bag_name_is_addressable) after line %d"
          % (len(block), ins))
    lines = lines[:ins] + block + lines[ins:]

    # --- 3: forward declaration of _require_properties ------------------------
    fwd = "\tstatic bool _require_properties(const Dictionary &p_args, Dictionary &r_out, MCPToolError &r_error);"
    assert fwd not in lines
    fi = [i for i, l in enumerate(lines) if l.strip() == "static bool _require_properties(const Dictionary &p_args, Dictionary &r_out, MCPToolError &r_error) {"]
    assert len(fi) == 1
    print("forward-declaring _require_properties before its first use")
    lines.insert(fi[0], fwd)
    lines.insert(fi[0], "\t// Declared before `_tool_create_scene_file`, which calls it; the body stays")
    lines.insert(fi[0], "\t// where the recorded revision has it.")

    # --- 4: close the is_label==nullptr branch --------------------------------
    start = [i for i, l in enumerate(lines) if l == "\t\t\tif (!resource_bag_name_is_addressable(key)) {"]
    assert len(start) == 1, "addressable gate: %d hits" % len(start)
    s = start[0]
    assert lines[s + 1].strip().startswith("r_error = MCPToolError::invalid_params(vformat("), lines[s + 1]
    assert lines[s + 2].strip().startswith("const Variant::Type target_type = property_type_of("), lines[s + 2]
    close = [
        MARK,
        "\t\t\t\t\tr_error = MCPToolError::invalid_params(vformat(",
        '\t\t\t\t\t\t\t"Property name \'%s\' is not a settable property name: Object::set() takes a non-empty identifier",',
        "\t\t\t\t\t\t\tString(key)));",
        "\t\t\t\t\treturn false;",
        "\t\t\t\t}",
        "\t\t\t\tr_error = MCPToolError::not_found(",
        '\t\t\t\t\t\tvformat("Property \'%s\' on %s", String(key), p_resource->get_class()),',
        '\t\t\t\t\t\tvformat("\'%s\' is not a property of %s; read the properties this resource really has with "',
        '\t\t\t\t\t\t\t\t"project_read_resource (its \'properties\' object is exactly what this tool takes back)",',
        "\t\t\t\t\t\t\t\tString(key), p_resource->get_class()));",
        "\t\t\t\treturn false;",
        "\t\t\t}",
    ]
    print("closing the is_label==nullptr branch at line %d with %d lines (marked low-confidence)"
          % (s + 2, len(close)))
    lines = lines[:s + 2] + close + lines[s + 2:]

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
