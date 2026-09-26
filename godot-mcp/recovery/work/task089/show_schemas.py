import io
import json
import sys

contract = json.load(io.open(r"H:\rebuild\godot\modules\mcp_server\docs\tools_list.renamed.json", encoding="utf-8"))
tools = {t["name"]: t for t in contract["result"]["tools"]}
wanted = [
    "project_write_text_file", "project_read_text_file", "project_create_script",
    "project_edit_script", "editor_open_scene", "editor_get_scene_tree",
    "editor_get_node_properties", "editor_set_node_property", "editor_save_scene",
    "project_create_scene_file", "project_create_resource", "project_delete_scene_file",
    "project_set_setting", "project_get_settings", "project_get_statistics",
    "project_analyze_scene_complexity", "project_search_file_contents",
    "project_read_script", "editor_capture_screenshot", "editor_get_errors",
    "running_game_get_scene_tree", "running_game_get_node_properties",
    "running_game_execute_gdscript", "running_game_set_node_property",
    "running_game_assert_node_state", "running_game_assert_screen_text",
    "running_game_simulate_button_click_by_text", "running_game_capture_screenshot",
]
for name in wanted:
    t = tools.get(name)
    if t is None:
        print("%-46s NOT IN CONTRACT" % name)
        continue
    schema = t.get("inputSchema", {})
    props = schema.get("properties", {})
    req = schema.get("required", [])
    print("%-46s required=%s props=%s" % (name, req, sorted(props.keys())))
