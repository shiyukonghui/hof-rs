#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""TASK-110 recon: compact schema summary for the TASK-110 target tool families."""
import io
import json
import os

ROOT = r"F:\moonbit-hof-rs\godot-mcp"
SCH = os.path.join(ROOT, "recovery", "work", "task110", "schemas")
OUTF = os.path.join(ROOT, "recovery", "work", "task110", "target-tools.txt")

FAMILY1 = """project_add_autoload project_analyze_scene_complexity project_convert_path_to_uid
project_convert_uid_to_path project_create_resource project_create_scene_file project_create_shader
project_create_theme project_delete_scene_file project_detect_circular_dependencies project_edit_resource
project_edit_shader project_find_files_referencing_symbol project_find_script_references
project_find_unused_resources project_get_filesystem_tree project_get_info project_get_resource_preview
project_get_scene_dependencies project_get_scene_exports project_get_settings project_get_shader_params
project_get_statistics project_get_theme_info project_list_scripts project_read_resource
project_read_scene_file_content project_read_script project_read_shader project_remove_autoload
project_search_file_contents project_search_file_names project_set_node_property_across_scenes
project_set_setting project_set_theme_color project_set_theme_constant project_set_theme_font_size
project_set_theme_stylebox project_validate_script project_write_text_file""".split()

FAMILY2 = """editor_find_nodes_by_type editor_find_nodes_in_group editor_get_collision_info
editor_get_input_actions editor_get_node_groups editor_get_node_signals editor_get_physics_layers
editor_list_signal_connections editor_get_open_scripts editor_get_output_log editor_get_selection
editor_get_performance_monitors editor_analyze_signal_flow editor_execute_gdscript
editor_get_node_properties editor_get_scene_tree editor_get_animation_info editor_list_animations""".split()

FAMILY3 = """running_game_find_nearby_nodes running_game_find_nodes_by_script running_game_find_ui_elements
running_game_get_autoload_node running_game_get_node_properties_batch
running_game_simulate_button_click_by_text running_game_get_node_properties running_game_capture_frames
running_game_capture_signal_emissions""".split()


def summarize(name):
    path = os.path.join(SCH, name + ".json")
    with io.open(path, "r", encoding="utf-8") as h:
        t = json.load(h)
    sch = t.get("inputSchema") or {}
    props = sch.get("properties") or {}
    req = sch.get("required") or []
    lines = ["### %s" % name]
    desc = (t.get("description") or "").strip().split("\n")
    lines.append("  desc: " + " / ".join(x.strip() for x in desc[:3])[:500])
    lines.append("  required: %s   additionalProperties=%s" % (req, sch.get("additionalProperties")))
    for k in sorted(props):
        p = props[k]
        bits = []
        if isinstance(p, dict):
            if "type" in p:
                bits.append(str(p["type"]))
            if "enum" in p:
                bits.append("enum=" + ",".join(str(x) for x in p["enum"]))
            if "items" in p and isinstance(p["items"], dict) and "type" in p["items"]:
                bits.append("items:" + str(p["items"]["type"]))
            if "default" in p:
                bits.append("default=" + json.dumps(p["default"], ensure_ascii=False))
            d = (p.get("description") or "").strip().replace("\n", " ")
            if d:
                bits.append(d[:180])
        lines.append("    - %s : %s" % (k, "  ".join(bits)))
    return "\n".join(lines)


buf = []
for label, fam in (("FAMILY 1 - project_* zero-call", FAMILY1),
                   ("FAMILY 2 - editor read/inspect zero-call", FAMILY2),
                   ("FAMILY 3 - running_game query zero-call", FAMILY3)):
    buf.append("=" * 100)
    buf.append(label + "   (%d tools)" % len(fam))
    buf.append("=" * 100)
    for n in fam:
        buf.append(summarize(n))
        buf.append("")
with io.open(OUTF, "w", encoding="utf-8", newline="\n") as h:
    h.write("\n".join(buf))
print("wrote %s (%d bytes)" % (OUTF, os.path.getsize(OUTF)))
