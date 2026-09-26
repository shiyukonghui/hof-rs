# -*- coding: utf-8 -*-
"""TASK-084 fixes C-E (all evidence-backed; recorded text or recorded intent).

C. hoisted-helper call sites (recorded intent, REPORT-017 section 14.4 D3):
   `_relative_path` / `_optional_dictionary` were deleted file-locally and
   hoisted to `MCPTools::relative_path` (`tool_helpers.h:608`) /
   `MCPTools::optional_dictionary` (`tool_helpers.h:736`); the recorded edits
   that removed each copy say so in their own NEW text.

D. `_number_fits_event` in editor_input_simulation.cpp: the definition was
   dropped by the 2A/2B splice.  Recorded text (edit seq=324) is replayed at its
   own recorded anchor, byte for byte.

E. `_require_editor_ui(r_error)` in editor_read_scene_inspector.cpp (3x) and
   editor_write_scene_editor.cpp (1x): the 1-argument file-local wrapper was
   removed by a recorded edit whose NEW text says the guard is called as
   `require_editor_ui(r_error, <wording>, <suggestion>)`.  The wording/hint used
   here is the one the *same tool group* already carries
   (editor_node_read.cpp:467 / editor_write_scene_editor.cpp:211), which is the
   most conservative choice available.

E2. editor_node_setup.cpp lines 794-798: a whole register-tool block
   (`editor_setup_world_environment`) sits inside the argument parsing of
   `_tool_setup_world_environment` - a TASK-083 splice artefact.  The identical
   block is already at 873-878, so removing the misplaced copy changes nothing.

usage: python fix_cf.py [--write]
"""
import io
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import rec  # noqa: E402

ROOT = r"H:\rebuild\godot"
SUB = "modules\\mcp_server\\tools\\"
WRITE = "--write" in sys.argv
BACKUP = r"C:\Users\wyl\AppData\Local\Temp\mcp-recovery\work\task084\backup084"


def load(name):
    p = os.path.join(ROOT, SUB + name)
    with io.open(p, "r", encoding="utf-8", errors="strict") as f:
        return f.read(), p


def put(name, text, path):
    os.makedirs(BACKUP, exist_ok=True)
    with io.open(path, "r", encoding="utf-8", errors="strict") as f:
        orig = f.read()
    with io.open(os.path.join(BACKUP, SUB.replace("\\", "__") + name), "w",
                 encoding="utf-8", newline="\n") as f:
        f.write(orig)
    with io.open(path, "w", encoding="utf-8", newline="\n") as f:
        f.write(text)
    print("   wrote %s (%d -> %d bytes)" % (name, len(orig.encode()), len(text.encode())))


def fix_rename(name, old_call, new_call, n=1):
    print("C. %s : %s -> %s" % (name, old_call, new_call))
    text, path = load(name)
    assert text.count(old_call + "(") == n, (name, text.count(old_call + "("))
    new = text.replace(old_call + "(", new_call + "(", n)
    assert new != text
    if WRITE:
        put(name, new, path)


def fix_number_fits():
    print("D. editor_input_simulation.cpp : replay recorded `_number_fits_event` definition")
    blk = None
    for r in rec.load(SUB + "editor_input_simulation.cpp")[1]:
        if str(r.get("seq")) == "324":
            blk = r["new"]
    assert blk, "edit seq=324 not found"
    lines = blk.split("\n")
    i = [k for k, l in enumerate(lines) if l.startswith("// Event construction.")][0]
    insert = lines[:i]
    while insert and insert[-1] == "":
        insert.pop()
    text, path = load("editor_input_simulation.cpp")
    assert "_number_fits_event(const Variant" not in text, "already present"
    anchor = "// ---------------------------------------------------------------------------\n// Event construction."
    assert text.count(anchor) == 1, text.count(anchor)
    new = text.replace(anchor, "\n".join(insert) + "\n\n" + anchor, 1)
    print("   inserting %d recorded lines before the 'Event construction' header" % len(insert))
    if WRITE:
        put("editor_input_simulation.cpp", new, path)


def fix_guard(name, wording, hint, n_expected):
    print("E. %s : %d x _require_editor_ui(r_error) -> require_editor_ui(r_error, wording, hint)" % (name, n_expected))
    text, path = load(name)
    old = "if (!_require_editor_ui(r_error)) {"
    assert text.count(old) == n_expected, (name, text.count(old))
    rep = ('if (!require_editor_ui(r_error, "%s",\n\t\t\t\t"%s")) {' % (wording, hint))
    new = text.replace(old, rep)
    if WRITE:
        put(name, new, path)


def fix_setup_block():
    print("E2. editor_node_setup.cpp : remove the misplaced register block inside the handler")
    text, path = load("editor_node_setup.cpp")
    block = ('\t\tToolBuilder builder("editor_setup_world_environment", String::utf8(R"desc(\u8bbe\u7f6e 3D \u73af\u5883)desc"));\n'
             '\t\tbuilder.channel("editor").verb("setup").scope(MCPToolScope::EDITOR).mutating(true);\n'
             '\t\tbuilder.schema(_schema_from_json(R"schema({"type":"object","properties":{"ambient_color":{"properties":{"b":{"type":"number"},"g":{"type":"number"},"r":{"type":"number"}},"type":"object"},"bg_color":{"properties":{"b":{"type":"number"},"g":{"type":"number"},"r":{"type":"number"}},"type":"object"},"world_env_path":{"type":"string"}},"required":[],"type":"object"})schema"));\n'
             '\t\tbuilder.handler(_tool_setup_world_environment).register_into(r_registry);\n'
             '\t}\n')
    assert text.count(block) == 2, text.count(block)
    # The misplaced copy is the *body* of `if (!optional_float(p_args,
    # "agent_height", ...))` (line 793).  Every sibling check in the same
    # function answers `return Variant();` there, so the block is replaced by
    # exactly that - the register block itself already exists at 873-878.
    first = text.index(block)
    repl = "\t\treturn Variant();\n\t}\n"
    new = text[:first] + repl + text[first + len(block):]
    assert new.count(block) == 1
    print("   replaced the misplaced copy with the sibling `return Variant();` body (%d -> %d bytes)"
          % (len(text), len(new)))
    if WRITE:
        put("editor_node_setup.cpp", new, path)


if __name__ == "__main__":
    print("mode: %s" % ("WRITE" if WRITE else "dry-run"))
    fix_rename("editor_control_layout_write.cpp", "_relative_path", "relative_path")
    fix_rename("editor_node_write.cpp", "_optional_dictionary", "optional_dictionary")
    fix_number_fits()
    fix_guard("editor_read_scene_inspector.cpp",
              "editor inspectors outside a running editor",
              "Start the MCP server inside the Godot editor to inspect the editor scene", 3)
    fix_guard("editor_write_scene_editor.cpp",
              "editor writes outside a running editor",
              "Start the MCP server inside the Godot editor to write editor state", 1)
    fix_setup_block()
