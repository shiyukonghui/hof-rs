#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""TASK-111: emit the report's per-tool markdown tables from coverage.json."""
import io
import json
import os

ROOT = r"F:\moonbit-hof-rs\godot-mcp"
with io.open(os.path.join(ROOT, "coverage.json"), "r", encoding="utf-8") as h:
    cov = json.load(h)
rows = {r["tool"]: r for r in cov["tools"]}

A = ["editor_add_node", "editor_add_scene_instance", "editor_add_raycast",
     "editor_add_resource_to_node_property", "editor_duplicate_node", "editor_rename_node",
     "editor_reparent_node", "editor_disconnect_signal",
     "editor_set_node_property_batch", "editor_set_node_property_updates",
     "editor_set_node_script", "editor_set_node_groups",
     "editor_setup_physics_body", "editor_setup_collision_shape", "editor_set_physics_layers",
     "editor_set_control_theme", "editor_set_anchor_preset",
     "editor_set_shader_material", "editor_set_shader_param", "editor_connect_signal",
     "editor_get_output_log", "editor_get_scene_tree",
     "running_game_get_node_properties_batch", "running_game_capture_frames",
     "running_game_capture_signal_emissions"]
H1 = ["editor_add_mesh_instance", "editor_set_material_3d", "editor_setup_camera_3d",
      "editor_set_viewport_3d_camera", "editor_get_viewport_3d_camera", "editor_setup_lighting",
      "editor_setup_world_environment"]
H2 = ["editor_create_animation", "editor_add_animation_track", "editor_set_animation_keyframe",
      "editor_remove_animation", "editor_list_animations", "editor_get_animation_info",
      "editor_create_animation_tree", "editor_get_animation_tree_structure",
      "editor_add_state_machine_state", "editor_add_state_machine_transition",
      "editor_remove_state_machine_state", "editor_remove_state_machine_transition",
      "editor_set_blend_tree_node", "editor_set_animation_tree_parameter"]
H3 = ["editor_add_gridmap", "editor_get_tilemap_cell", "editor_get_tilemap_info",
      "editor_get_tilemap_used_cells", "editor_remove_all_tilemap_cells",
      "editor_set_tilemap_cell", "editor_set_tilemap_cells_in_rect"]

BATCH = {"editor_disconnect_signal": "c5"}
for tool in A:
    BATCH.setdefault(tool, "c4")


def table(title, tools):
    print("### %s" % title)
    print()
    print("| # | tool | scope | 累计 | 有效 | 边界 | facts | 状态 | 本批 |")
    print("|---|---|---|---|---|---|---|---|---|")
    for i, tool in enumerate(tools, 1):
        r = rows.get(tool)
        if not r:
            print("| %d | `%s` | - | 0 | 0 | 0 | - | MISSING | - |" % (i, tool))
            continue
        print("| %d | `%s` | %s | %d | %d | %d | %d/%d | %s | %s |" % (
            i, tool, r.get("scope", "-"), r["calls"], r["effective"], r["boundary"],
            r.get("facts_complete", 0), r["calls"], r["status"], BATCH.get(tool, "-")))
    print()


table("A 批（20 条可达未覆盖 + 5 条待补证据 + 3 条 setup 工具）", A)
table("① H1 3D 族（7 条）", H1)
table("② H2 动画 / AnimationTree / 状态机族（14 条）", H2)
table("③ H3 TileMap / GridMap 族（7 条）", H3)
