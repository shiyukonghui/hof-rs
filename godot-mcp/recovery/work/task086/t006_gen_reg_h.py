# -*- coding: utf-8 -*-
"""TASK-086 replay of the recorded generator
`C:\\Users\\wyl\\AppData\\Local\\Temp\\t006_gen_reg.py` (events-write seq=593,
t=1790023003060), which produced the registration block of
`tools/editor_read_scene_inspector.cpp` and left the placeholder
`// @@REGISTRATION_BLOCK@@` behind in the reconstruction.

The recorded script is copied verbatim except for the two absolute paths, which
pointed at the original F: checkout. Nothing else is changed: the ORDER table,
the emitted template, the literals and the contract read are all recorded text.
"""
import io
import json
import sys

sys.stdout.reconfigure(encoding="utf-8")

MOD = r"H:\rebuild\godot\modules\mcp_server"
CPP = MOD + r"\tools\editor_read_scene_inspector.cpp"
contract = json.load(io.open(MOD + r"\docs\tools_list.renamed.json", encoding="utf-8"))
tools = {t["name"]: t for t in contract["result"]["tools"]}

ORDER = [
    ("editor_get_errors", "get", "_tool_get_errors"),
    ("editor_get_output_log", "get", "_tool_get_output_log"),
    ("editor_get_open_scripts", "get", "_tool_get_open_scripts"),
    ("editor_get_scene_tree", "get", "_tool_get_scene_tree"),
    ("editor_get_selection", "get", "_tool_get_selection"),
    ("editor_get_viewport_3d_camera", "get", "_tool_get_viewport_3d_camera"),
    ("editor_analyze_signal_flow", "analyze", "_tool_analyze_signal_flow"),
]

blocks = []
for name, verb, handler in ORDER:
    entry = tools[name]
    assert 'R"schema(' not in name
    desc = json.dumps(entry["description"], ensure_ascii=False, sort_keys=True)
    schema = json.dumps(entry["inputSchema"], ensure_ascii=False, sort_keys=True, separators=(",", ":"))
    assert '")schema"' not in schema
    assert '")desc"' not in desc
    # The description JSON literal is a valid C++ string literal as well: the
    # contract's descriptions contain no backslashes or double quotes.
    assert "\\" not in desc and '"' not in desc[1:-1], desc
    block = (
        "\t{\n"
        '\t\tToolBuilder builder("%s", String::utf8(R"desc(%s)desc"));\n'
        '\t\tbuilder.channel("editor").verb("%s").scope(MCPToolScope::EDITOR).mutating(false);\n'
        '\t\tbuilder.schema(_schema_from_json(R"schema(%s)schema"));\n'
        "\t\tbuilder.handler(%s).register_into(r_registry);\n"
        "\t}\n" % (name, desc[1:-1], verb, schema, handler)
    )
    blocks.append(block)

body = "\n".join(blocks)
src = io.open(CPP, encoding="utf-8").read()
assert "// @@REGISTRATION_BLOCK@@" in src
src = src.replace("// @@REGISTRATION_BLOCK@@", body.rstrip("\n"))
io.open(CPP, "w", encoding="utf-8", newline="").write(src)
print("registration block written, %d tools" % len(ORDER))
