# TOOL-COVERAGE — 契约工具覆盖台账（only-final）

> 本文件由 `tool_coverage.py` 自动生成，**随时可重跑刷新**。命令行：
> `python tools/tool_coverage.py --only-final`

口径（mode）：**only-final**；语料：**20 个 run 目录 / 40 个 trace 文件 / 2612 次 `tools/call`**（`ok=false` 37 次、解析失败行 0、sidecar 校验通过 57）

生成时间（UTC）：2026-09-27T01:37:23Z

**「有效调用」的判定**（由 `mcp_trace_ledger.py` 的 verdict 词汇给出，不另立一套）：

- `边界调用` = 该工具 `ok=false` 的调用次数（失败/拒绝即边界证据）。
- `有效调用`：**读类动词**（get/read/search/list/find/analyze/detect/convert/validate/check）= `ok=true` 且回包是实质载荷（读类调用不会动像素/字节，回包本身就是证据）；
  **其余动词**（create/edit/set/add/remove/write/build…）= ledger 的 `ok_effect_observed` / `ok_file_effect_observed`，即真的改了画面或文件。带 `assertion_failed` / `created_conflict` / `scenario_errors` 的 ok 调用不计有效。
- `状态`：`达标` = 调用≥5 且 有效≥1 且 边界≥1；`计数达标缺证据` = 调用≥5 但缺有效或边界；`未达(1-4)` / `未达(0)`；`不可达` 不在本表状态里，见 §4 登记表。

## 0. 分桶与状态

| 桶 | 工具数 |
|---|---|
| `0` 次 | 150 |
| `1-4` 次 | 2 |
| `>=5` 次 | 25 |
| **合计** | **177** |

| 状态 | 工具数 |
|---|---|
| 达标 | 3 |
| 计数达标缺证据 | 22 |
| 未达(1-4) | 2 |
| 未达(0) | 150 |

| scope | 契约条数 | 被调用过 | 0 次 | ≥5 次 |
|---|---|---|---|---|
| both | 50 | 5 | 45 | 5 |
| editor | 104 | 11 | 93 | 10 |
| game | 23 | 11 | 12 | 10 |

## 1. 总表（177 条契约工具，逐条一行）

| # | tool | scope | verb | 累计调用 | 有效调用 | 边界调用 | 证据路径 | 状态 |
|---|---|---|---|---|---|---|---|---|
| 1 | `project_get_info` | both | get | 0 | 0 | 0 | - | 未达(0) |
| 2 | `project_get_filesystem_tree` | both | get | 0 | 0 | 0 | - | 未达(0) |
| 3 | `project_search_file_names` | both | search | 0 | 0 | 0 | - | 未达(0) |
| 4 | `project_search_file_contents` | both | search | 0 | 0 | 0 | - | 未达(0) |
| 5 | `project_get_settings` | both | get | 0 | 0 | 0 | - | 未达(0) |
| 6 | `project_set_setting` | both | set | 0 | 0 | 0 | - | 未达(0) |
| 7 | `project_convert_uid_to_path` | both | convert | 0 | 0 | 0 | - | 未达(0) |
| 8 | `project_convert_path_to_uid` | both | convert | 0 | 0 | 0 | - | 未达(0) |
| 9 | `editor_get_scene_tree` | editor | get | 24 | 19 | 0 | runs/breakout/breakout-clean-task097(3) ; runs/pong/pong-clean-task097(3) | 计数达标缺证据 |
| 10 | `project_read_scene_file_content` | both | read | 0 | 0 | 0 | - | 未达(0) |
| 11 | `editor_open_scene` | editor | open | 21 | 0 | 0 | runs/breakout/breakout-clean-task097(2) ; runs/pong/pong-clean-task097(2) | 计数达标缺证据 |
| 12 | `project_delete_scene_file` | both | delete | 0 | 0 | 0 | - | 未达(0) |
| 13 | `editor_add_scene_instance` | editor | add | 0 | 0 | 0 | - | 未达(0) |
| 14 | `project_get_scene_exports` | both | get | 0 | 0 | 0 | - | 未达(0) |
| 15 | `editor_play_scene` | editor | play | 0 | 0 | 0 | - | 未达(0) |
| 16 | `editor_stop_scene` | editor | stop | 0 | 0 | 0 | - | 未达(0) |
| 17 | `editor_save_scene` | editor | save | 42 | 21 | 0 | runs/lunarlander/ll-task104-r1(3) ; runs/missilecommand/mc-task103-r3(3) | 计数达标缺证据 |
| 18 | `project_create_scene_file` | both | create | 0 | 0 | 0 | - | 未达(0) |
| 19 | `editor_add_node` | editor | add | 0 | 0 | 0 | - | 未达(0) |
| 20 | `editor_delete_node` | editor | delete | 28 | 5 | 0 | runs/breakout/breakout-clean-task097(20) ; runs/pong/pong-clean-task097(8) | 计数达标缺证据 |
| 21 | `editor_rename_node` | editor | rename | 0 | 0 | 0 | - | 未达(0) |
| 22 | `editor_set_node_property` | editor | set | 5 | 0 | 0 | runs/pong/pong-clean-task097(3) ; runs/breakout/breakout-clean-task097(2) | 计数达标缺证据 |
| 23 | `editor_get_node_properties` | editor | get | 20 | 19 | 1 | runs/breakout/breakout-clean-task097(10) ; runs/pong/pong-clean-task097(9) | 达标 |
| 24 | `editor_duplicate_node` | editor | duplicate | 0 | 0 | 0 | - | 未达(0) |
| 25 | `editor_connect_signal` | editor | connect | 0 | 0 | 0 | - | 未达(0) |
| 26 | `editor_disconnect_signal` | editor | disconnect | 0 | 0 | 0 | - | 未达(0) |
| 27 | `editor_reparent_node` | editor | reparent | 0 | 0 | 0 | - | 未达(0) |
| 28 | `editor_add_resource_to_node_property` | editor | add | 0 | 0 | 0 | - | 未达(0) |
| 29 | `editor_set_anchor_preset` | editor | set | 0 | 0 | 0 | - | 未达(0) |
| 30 | `editor_get_node_groups` | editor | get | 0 | 0 | 0 | - | 未达(0) |
| 31 | `editor_set_node_groups` | editor | set | 0 | 0 | 0 | - | 未达(0) |
| 32 | `editor_find_nodes_in_group` | editor | find | 0 | 0 | 0 | - | 未达(0) |
| 33 | `editor_get_selection` | editor | get | 0 | 0 | 0 | - | 未达(0) |
| 34 | `editor_set_node_selection` | editor | set | 0 | 0 | 0 | - | 未达(0) |
| 35 | `editor_remove_node_selection` | editor | remove | 0 | 0 | 0 | - | 未达(0) |
| 36 | `editor_execute_gdscript` | editor | execute | 0 | 0 | 0 | - | 未达(0) |
| 37 | `editor_get_errors` | editor | get | 17 | 17 | 0 | runs/asteroids/ast-task098-r2(1) ; runs/breakout/breakout-clean-task097(1) | 计数达标缺证据 |
| 38 | `editor_get_output_log` | editor | get | 0 | 0 | 0 | - | 未达(0) |
| 39 | `editor_capture_screenshot` | editor | capture | 3 | 2 | 0 | runs/breakout/breakout-clean-task097(1) ; runs/pong/pong-clean-task097(1) | 未达(1-4) |
| 40 | `running_game_capture_screenshot` | game | capture | 102 | 44 | 0 | runs/match3/m3-task102-r3(7) ; runs/platformer/plat-task102-r2(7) | 计数达标缺证据 |
| 41 | `editor_remove_output_log` | editor | remove | 0 | 0 | 0 | - | 未达(0) |
| 42 | `editor_reload_plugin` | editor | reload | 0 | 0 | 0 | - | 未达(0) |
| 43 | `editor_rescan_project_filesystem` | editor | rescan | 0 | 0 | 0 | - | 未达(0) |
| 44 | `editor_get_node_signals` | editor | get | 0 | 0 | 0 | - | 未达(0) |
| 45 | `editor_analyze_screenshot_diff` | editor | analyze | 0 | 0 | 0 | - | 未达(0) |
| 46 | `editor_set_auto_dismiss_dialogs` | editor | set | 0 | 0 | 0 | - | 未达(0) |
| 47 | `editor_get_viewport_3d_camera` | editor | get | 0 | 0 | 0 | - | 未达(0) |
| 48 | `editor_set_viewport_3d_camera` | editor | set | 0 | 0 | 0 | - | 未达(0) |
| 49 | `running_game_get_scene_tree` | game | get | 40 | 18 | 0 | runs/asteroids/ast-task098-r2(2) ; runs/bomberman/bomb-task101-r4(2) | 计数达标缺证据 |
| 50 | `running_game_get_node_properties` | game | get | 5 | 5 | 0 | runs/pong/pong-clean-task097(3) ; runs/breakout/breakout-clean-task097(2) | 计数达标缺证据 |
| 51 | `running_game_set_node_property` | game | set | 6 | 6 | 0 | runs/pong/pong-clean-task097(5) ; runs/breakout/breakout-clean-task097(1) | 计数达标缺证据 |
| 52 | `running_game_capture_frames` | game | capture | 0 | 0 | 0 | - | 未达(0) |
| 53 | `running_game_get_node_property_samples` | game | get | 49 | 49 | 0 | runs/spaceinvaders/si-task097-r1(5) ; runs/tetris/tetris-task096-r2(4) | 计数达标缺证据 |
| 54 | `running_game_execute_gdscript` | game | execute | 668 | 668 | 0 | runs/rtype/rt-task104-r2(98) ; runs/bomberman/bomb-task101-r4(61) | 计数达标缺证据 |
| 55 | `running_game_create_input_recording` | game | create | 0 | 0 | 0 | - | 未达(0) |
| 56 | `running_game_stop_input_recording` | game | stop | 0 | 0 | 0 | - | 未达(0) |
| 57 | `running_game_play_input_recording` | game | play | 0 | 0 | 0 | - | 未达(0) |
| 58 | `running_game_find_nodes_by_script` | game | find | 0 | 0 | 0 | - | 未达(0) |
| 59 | `running_game_get_autoload_node` | game | get | 0 | 0 | 0 | - | 未达(0) |
| 60 | `running_game_get_node_properties_batch` | game | get | 0 | 0 | 0 | - | 未达(0) |
| 61 | `running_game_find_ui_elements` | game | find | 0 | 0 | 0 | - | 未达(0) |
| 62 | `running_game_simulate_button_click_by_text` | game | simulate | 0 | 0 | 0 | - | 未达(0) |
| 63 | `running_game_find_node_when_available` | game | find | 1 | 0 | 1 | runs/breakout/breakout-clean-task097(1) | 未达(1-4) |
| 64 | `running_game_find_nearby_nodes` | game | find | 0 | 0 | 0 | - | 未达(0) |
| 65 | `running_game_move_player_to_target` | game | move | 0 | 0 | 0 | - | 未达(0) |
| 66 | `running_game_capture_signal_emissions` | game | capture | 0 | 0 | 0 | - | 未达(0) |
| 67 | `editor_get_performance_monitors` | editor | get | 0 | 0 | 0 | - | 未达(0) |
| 68 | `project_list_scripts` | both | list | 0 | 0 | 0 | - | 未达(0) |
| 69 | `project_read_script` | both | read | 0 | 0 | 0 | - | 未达(0) |
| 70 | `project_create_script` | both | create | 6 | 2 | 0 | runs/breakout/breakout-clean-task097(2) ; runs/pong/pong-clean-task097(2) | 计数达标缺证据 |
| 71 | `project_edit_script` | both | edit | 21 | 18 | 0 | runs/tetris/tetris-task096-r2(2) ; runs/asteroids/ast-task098-r2(1) | 计数达标缺证据 |
| 72 | `editor_set_node_script` | editor | set | 0 | 0 | 0 | - | 未达(0) |
| 73 | `editor_get_open_scripts` | editor | get | 0 | 0 | 0 | - | 未达(0) |
| 74 | `project_validate_script` | both | validate | 0 | 0 | 0 | - | 未达(0) |
| 75 | `editor_simulate_key` | editor | simulate | 0 | 0 | 0 | - | 未达(0) |
| 76 | `editor_simulate_mouse_click` | editor | simulate | 0 | 0 | 0 | - | 未达(0) |
| 77 | `editor_simulate_mouse_move` | editor | simulate | 0 | 0 | 0 | - | 未达(0) |
| 78 | `editor_simulate_input_action` | editor | simulate | 0 | 0 | 0 | - | 未达(0) |
| 79 | `editor_get_input_actions` | editor | get | 0 | 0 | 0 | - | 未达(0) |
| 80 | `editor_add_input_action` | editor | add | 52 | 44 | 0 | runs/pong/pong-clean-task097(5) ; runs/snake/snake-task106-r1(5) | 计数达标缺证据 |
| 81 | `editor_simulate_input_sequence` | editor | simulate | 0 | 0 | 0 | - | 未达(0) |
| 82 | `editor_find_nodes_by_type` | editor | find | 0 | 0 | 0 | - | 未达(0) |
| 83 | `editor_set_node_property_batch` | editor | set | 0 | 0 | 0 | - | 未达(0) |
| 84 | `editor_list_signal_connections` | editor | list | 0 | 0 | 0 | - | 未达(0) |
| 85 | `editor_add_nodes_batch` | editor | add | 35 | 17 | 18 | runs/asteroids/ast-task098-r2(2) ; runs/bomberman/bomb-task101-r4(2) | 达标 |
| 86 | `project_find_files_referencing_symbol` | both | find | 0 | 0 | 0 | - | 未达(0) |
| 87 | `project_get_scene_dependencies` | both | get | 0 | 0 | 0 | - | 未达(0) |
| 88 | `project_set_node_property_across_scenes` | both | set | 0 | 0 | 0 | - | 未达(0) |
| 89 | `editor_list_animations` | editor | list | 0 | 0 | 0 | - | 未达(0) |
| 90 | `editor_create_animation` | editor | create | 0 | 0 | 0 | - | 未达(0) |
| 91 | `editor_add_animation_track` | editor | add | 0 | 0 | 0 | - | 未达(0) |
| 92 | `editor_set_animation_keyframe` | editor | set | 0 | 0 | 0 | - | 未达(0) |
| 93 | `editor_get_animation_info` | editor | get | 0 | 0 | 0 | - | 未达(0) |
| 94 | `editor_remove_animation` | editor | remove | 0 | 0 | 0 | - | 未达(0) |
| 95 | `editor_get_tilemap_info` | editor | get | 0 | 0 | 0 | - | 未达(0) |
| 96 | `editor_get_tilemap_used_cells` | editor | get | 0 | 0 | 0 | - | 未达(0) |
| 97 | `editor_remove_all_tilemap_cells` | editor | remove | 0 | 0 | 0 | - | 未达(0) |
| 98 | `editor_set_tilemap_cell` | editor | set | 0 | 0 | 0 | - | 未达(0) |
| 99 | `editor_set_tilemap_cells_in_rect` | editor | set | 0 | 0 | 0 | - | 未达(0) |
| 100 | `editor_get_tilemap_cell` | editor | get | 0 | 0 | 0 | - | 未达(0) |
| 101 | `project_read_resource` | both | read | 0 | 0 | 0 | - | 未达(0) |
| 102 | `project_add_autoload` | both | add | 0 | 0 | 0 | - | 未达(0) |
| 103 | `project_remove_autoload` | both | remove | 0 | 0 | 0 | - | 未达(0) |
| 104 | `project_edit_resource` | both | edit | 0 | 0 | 0 | - | 未达(0) |
| 105 | `project_create_resource` | both | create | 0 | 0 | 0 | - | 未达(0) |
| 106 | `project_get_resource_preview` | both | get | 0 | 0 | 0 | - | 未达(0) |
| 107 | `project_get_export_info` | both | get | 0 | 0 | 0 | - | 未达(0) |
| 108 | `project_list_export_presets` | both | list | 0 | 0 | 0 | - | 未达(0) |
| 109 | `project_read_shader` | both | read | 0 | 0 | 0 | - | 未达(0) |
| 110 | `project_create_shader` | both | create | 0 | 0 | 0 | - | 未达(0) |
| 111 | `project_edit_shader` | both | edit | 0 | 0 | 0 | - | 未达(0) |
| 112 | `editor_set_shader_material` | editor | set | 0 | 0 | 0 | - | 未达(0) |
| 113 | `editor_set_shader_param` | editor | set | 0 | 0 | 0 | - | 未达(0) |
| 114 | `project_get_shader_params` | both | get | 0 | 0 | 0 | - | 未达(0) |
| 115 | `editor_add_raycast` | editor | add | 0 | 0 | 0 | - | 未达(0) |
| 116 | `editor_setup_collision_shape` | editor | setup | 0 | 0 | 0 | - | 未达(0) |
| 117 | `editor_set_physics_layers` | editor | set | 0 | 0 | 0 | - | 未达(0) |
| 118 | `editor_get_physics_layers` | editor | get | 0 | 0 | 0 | - | 未达(0) |
| 119 | `editor_setup_physics_body` | editor | setup | 0 | 0 | 0 | - | 未达(0) |
| 120 | `editor_get_collision_info` | editor | get | 0 | 0 | 0 | - | 未达(0) |
| 121 | `editor_add_mesh_instance` | editor | add | 0 | 0 | 0 | - | 未达(0) |
| 122 | `editor_setup_camera_3d` | editor | setup | 0 | 0 | 0 | - | 未达(0) |
| 123 | `editor_setup_lighting` | editor | setup | 0 | 0 | 0 | - | 未达(0) |
| 124 | `editor_set_material_3d` | editor | set | 0 | 0 | 0 | - | 未达(0) |
| 125 | `editor_setup_world_environment` | editor | setup | 0 | 0 | 0 | - | 未达(0) |
| 126 | `editor_add_gridmap` | editor | add | 0 | 0 | 0 | - | 未达(0) |
| 127 | `editor_add_audio_player` | editor | add | 0 | 0 | 0 | - | 未达(0) |
| 128 | `editor_get_audio_info` | editor | get | 0 | 0 | 0 | - | 未达(0) |
| 129 | `editor_get_audio_bus_layout` | editor | get | 0 | 0 | 0 | - | 未达(0) |
| 130 | `editor_add_audio_bus` | editor | add | 0 | 0 | 0 | - | 未达(0) |
| 131 | `editor_set_audio_bus_property` | editor | set | 0 | 0 | 0 | - | 未达(0) |
| 132 | `editor_add_audio_bus_effect` | editor | add | 0 | 0 | 0 | - | 未达(0) |
| 133 | `project_create_theme` | both | create | 0 | 0 | 0 | - | 未达(0) |
| 134 | `project_set_theme_color` | both | set | 0 | 0 | 0 | - | 未达(0) |
| 135 | `project_set_theme_constant` | both | set | 0 | 0 | 0 | - | 未达(0) |
| 136 | `project_set_theme_font_size` | both | set | 0 | 0 | 0 | - | 未达(0) |
| 137 | `project_set_theme_stylebox` | both | set | 0 | 0 | 0 | - | 未达(0) |
| 138 | `editor_set_control_theme` | editor | set | 0 | 0 | 0 | - | 未达(0) |
| 139 | `project_get_theme_info` | both | get | 0 | 0 | 0 | - | 未达(0) |
| 140 | `editor_create_animation_tree` | editor | create | 0 | 0 | 0 | - | 未达(0) |
| 141 | `editor_get_animation_tree_structure` | editor | get | 0 | 0 | 0 | - | 未达(0) |
| 142 | `editor_add_state_machine_state` | editor | add | 0 | 0 | 0 | - | 未达(0) |
| 143 | `editor_remove_state_machine_state` | editor | remove | 0 | 0 | 0 | - | 未达(0) |
| 144 | `editor_add_state_machine_transition` | editor | add | 0 | 0 | 0 | - | 未达(0) |
| 145 | `editor_remove_state_machine_transition` | editor | remove | 0 | 0 | 0 | - | 未达(0) |
| 146 | `editor_set_blend_tree_node` | editor | set | 0 | 0 | 0 | - | 未达(0) |
| 147 | `editor_set_animation_tree_parameter` | editor | set | 0 | 0 | 0 | - | 未达(0) |
| 148 | `editor_setup_navigation_region` | editor | setup | 0 | 0 | 0 | - | 未达(0) |
| 149 | `editor_bake_navigation_mesh` | editor | bake | 0 | 0 | 0 | - | 未达(0) |
| 150 | `editor_setup_navigation_agent` | editor | setup | 0 | 0 | 0 | - | 未达(0) |
| 151 | `editor_set_navigation_layers` | editor | set | 0 | 0 | 0 | - | 未达(0) |
| 152 | `editor_get_navigation_info` | editor | get | 0 | 0 | 0 | - | 未达(0) |
| 153 | `editor_create_particles` | editor | create | 0 | 0 | 0 | - | 未达(0) |
| 154 | `editor_set_particle_material` | editor | set | 0 | 0 | 0 | - | 未达(0) |
| 155 | `editor_set_particle_color_gradient` | editor | set | 0 | 0 | 0 | - | 未达(0) |
| 156 | `editor_set_particle_preset` | editor | set | 0 | 0 | 0 | - | 未达(0) |
| 157 | `editor_get_particle_info` | editor | get | 0 | 0 | 0 | - | 未达(0) |
| 158 | `project_find_unused_resources` | both | find | 0 | 0 | 0 | - | 未达(0) |
| 159 | `editor_analyze_signal_flow` | editor | analyze | 0 | 0 | 0 | - | 未达(0) |
| 160 | `project_analyze_scene_complexity` | both | analyze | 0 | 0 | 0 | - | 未达(0) |
| 161 | `project_find_script_references` | both | find | 0 | 0 | 0 | - | 未达(0) |
| 162 | `project_detect_circular_dependencies` | both | detect | 0 | 0 | 0 | - | 未达(0) |
| 163 | `project_get_statistics` | both | get | 0 | 0 | 0 | - | 未达(0) |
| 164 | `running_game_run_test_scenario` | game | run | 39 | 38 | 0 | runs/snake/snake-task106-r1(8) ; runs/breakout/breakout-clean-task097(6) | 计数达标缺证据 |
| 165 | `running_game_assert_node_state` | game | assert | 1308 | 1287 | 17 | runs/lunarlander/ll-task104-r1(149) ; runs/bomberman/bomb-task101-r4(144) | 达标 |
| 166 | `running_game_assert_screen_text` | game | assert | 30 | 29 | 0 | runs/asteroids/ast-task098-r2(2) ; runs/bomberman/bomb-task101-r4(2) | 计数达标缺证据 |
| 167 | `running_game_run_stress_test` | game | run | 5 | 3 | 0 | runs/breakout/breakout-clean-task097(1) ; runs/pong/pong-clean-task097(1) | 计数达标缺证据 |
| 168 | `editor_get_test_report` | editor | get | 0 | 0 | 0 | - | 未达(0) |
| 169 | `os_list_android_devices` | both | list | 0 | 0 | 0 | - | 未达(0) |
| 170 | `project_get_android_preset_info` | both | get | 0 | 0 | 0 | - | 未达(0) |
| 171 | `os_deploy_to_android_device` | both | deploy | 0 | 0 | 0 | - | 未达(0) |
| 172 | `project_build_csharp` | both | build | 20 | 20 | 0 | runs/asteroids/ast-task098-r2(1) ; runs/bomberman/bomb-task101-r4(1) | 计数达标缺证据 |
| 173 | `project_write_text_file` | both | write | 0 | 0 | 0 | - | 未达(0) |
| 174 | `project_validate_scripts` | both | validate | 23 | 20 | 0 | runs/breakout/breakout-clean-task097(2) ; runs/pong/pong-clean-task097(2) | 计数达标缺证据 |
| 175 | `editor_set_node_script_batch` | editor | set | 6 | 0 | 0 | runs/breakout/breakout-clean-task097(2) ; runs/pong/pong-clean-task097(2) | 计数达标缺证据 |
| 176 | `editor_set_node_property_updates` | editor | set | 0 | 0 | 0 | - | 未达(0) |
| 177 | `project_read_text_file` | both | read | 36 | 34 | 0 | runs/asteroids/ast-task098-r2(2) ; runs/bomberman/bomb-task101-r4(2) | 计数达标缺证据 |

## 2. 分桶明细

### 2.1 `>=5` 次（25 条）

| tool | scope | 累计 | 有效 | 边界 | 状态 | 证据 |
|---|---|---|---|---|---|---|
| `editor_get_scene_tree` | editor | 24 | 19 | 0 | 计数达标缺证据 | runs/breakout/breakout-clean-task097(3) ; runs/pong/pong-clean-task097(3) ; runs/asteroids/ast-task098-r2(1) |
| `editor_open_scene` | editor | 21 | 0 | 0 | 计数达标缺证据 | runs/breakout/breakout-clean-task097(2) ; runs/pong/pong-clean-task097(2) ; runs/asteroids/ast-task098-r2(1) |
| `editor_save_scene` | editor | 42 | 21 | 0 | 计数达标缺证据 | runs/lunarlander/ll-task104-r1(3) ; runs/missilecommand/mc-task103-r3(3) ; runs/puzzlebobble/pb-task104-r1(3) |
| `editor_delete_node` | editor | 28 | 5 | 0 | 计数达标缺证据 | runs/breakout/breakout-clean-task097(20) ; runs/pong/pong-clean-task097(8) |
| `editor_set_node_property` | editor | 5 | 0 | 0 | 计数达标缺证据 | runs/pong/pong-clean-task097(3) ; runs/breakout/breakout-clean-task097(2) |
| `editor_get_node_properties` | editor | 20 | 19 | 1 | 达标 | runs/breakout/breakout-clean-task097(10) ; runs/pong/pong-clean-task097(9) ; runs/snake/snake-task106-r1(1) |
| `editor_get_errors` | editor | 17 | 17 | 0 | 计数达标缺证据 | runs/asteroids/ast-task098-r2(1) ; runs/breakout/breakout-clean-task097(1) ; runs/flappy/flappy-task099-r2(1) |
| `running_game_capture_screenshot` | game | 102 | 44 | 0 | 计数达标缺证据 | runs/match3/m3-task102-r3(7) ; runs/platformer/plat-task102-r2(7) ; runs/asteroids/ast-task098-r2(6) |
| `running_game_get_scene_tree` | game | 40 | 18 | 0 | 计数达标缺证据 | runs/asteroids/ast-task098-r2(2) ; runs/bomberman/bomb-task101-r4(2) ; runs/breakout/breakout-clean-task097(2) |
| `running_game_get_node_properties` | game | 5 | 5 | 0 | 计数达标缺证据 | runs/pong/pong-clean-task097(3) ; runs/breakout/breakout-clean-task097(2) |
| `running_game_set_node_property` | game | 6 | 6 | 0 | 计数达标缺证据 | runs/pong/pong-clean-task097(5) ; runs/breakout/breakout-clean-task097(1) |
| `running_game_get_node_property_samples` | game | 49 | 49 | 0 | 计数达标缺证据 | runs/spaceinvaders/si-task097-r1(5) ; runs/tetris/tetris-task096-r2(4) ; runs/asteroids/ast-task098-r2(3) |
| `running_game_execute_gdscript` | game | 668 | 668 | 0 | 计数达标缺证据 | runs/rtype/rt-task104-r2(98) ; runs/bomberman/bomb-task101-r4(61) ; runs/platformer/plat-task102-r2(59) |
| `project_create_script` | both | 6 | 2 | 0 | 计数达标缺证据 | runs/breakout/breakout-clean-task097(2) ; runs/pong/pong-clean-task097(2) ; runs/snake/snake-task106-r1(2) |
| `project_edit_script` | both | 21 | 18 | 0 | 计数达标缺证据 | runs/tetris/tetris-task096-r2(2) ; runs/asteroids/ast-task098-r2(1) ; runs/bomberman/bomb-task101-r4(1) |
| `editor_add_input_action` | editor | 52 | 44 | 0 | 计数达标缺证据 | runs/pong/pong-clean-task097(5) ; runs/snake/snake-task106-r1(5) ; runs/asteroids/ast-task098-r2(4) |
| `editor_add_nodes_batch` | editor | 35 | 17 | 18 | 达标 | runs/asteroids/ast-task098-r2(2) ; runs/bomberman/bomb-task101-r4(2) ; runs/flappy/flappy-task099-r2(2) |
| `running_game_run_test_scenario` | game | 39 | 38 | 0 | 计数达标缺证据 | runs/snake/snake-task106-r1(8) ; runs/breakout/breakout-clean-task097(6) ; runs/pong/pong-clean-task097(4) |
| `running_game_assert_node_state` | game | 1308 | 1287 | 17 | 达标 | runs/lunarlander/ll-task104-r1(149) ; runs/bomberman/bomb-task101-r4(144) ; runs/platformer/plat-task102-r2(140) |
| `running_game_assert_screen_text` | game | 30 | 29 | 0 | 计数达标缺证据 | runs/asteroids/ast-task098-r2(2) ; runs/bomberman/bomb-task101-r4(2) ; runs/flappy/flappy-task099-r2(2) |
| `running_game_run_stress_test` | game | 5 | 3 | 0 | 计数达标缺证据 | runs/breakout/breakout-clean-task097(1) ; runs/pong/pong-clean-task097(1) ; runs/snake/snake-task106-r1(1) |
| `project_build_csharp` | both | 20 | 20 | 0 | 计数达标缺证据 | runs/asteroids/ast-task098-r2(1) ; runs/bomberman/bomb-task101-r4(1) ; runs/breakout/breakout-clean-task097(1) |
| `project_validate_scripts` | both | 23 | 20 | 0 | 计数达标缺证据 | runs/breakout/breakout-clean-task097(2) ; runs/pong/pong-clean-task097(2) ; runs/snake/snake-task106-r1(2) |
| `editor_set_node_script_batch` | editor | 6 | 0 | 0 | 计数达标缺证据 | runs/breakout/breakout-clean-task097(2) ; runs/pong/pong-clean-task097(2) ; runs/snake/snake-task106-r1(2) |
| `project_read_text_file` | both | 36 | 34 | 0 | 计数达标缺证据 | runs/asteroids/ast-task098-r2(2) ; runs/bomberman/bomb-task101-r4(2) ; runs/breakout/breakout-clean-task097(2) |

### 2.2 `1-4` 次（2 条）

| tool | scope | 累计 | 有效 | 边界 | 状态 | 证据 |
|---|---|---|---|---|---|---|
| `editor_capture_screenshot` | editor | 3 | 2 | 0 | 未达(1-4) | runs/breakout/breakout-clean-task097(1) ; runs/pong/pong-clean-task097(1) ; runs/snake/snake-task106-r1(1) |
| `running_game_find_node_when_available` | game | 1 | 0 | 1 | 未达(1-4) | runs/breakout/breakout-clean-task097(1) |

### 2.3 `0` 次（150 条）

（按前缀分组，均为 0 次；其中登记为「不可达」的见 §4）

- **editor_**（93）：`editor_add_scene_instance` `editor_play_scene` `editor_stop_scene` `editor_add_node` `editor_rename_node` `editor_duplicate_node` `editor_connect_signal` `editor_disconnect_signal` `editor_reparent_node` `editor_add_resource_to_node_property` `editor_set_anchor_preset` `editor_get_node_groups` `editor_set_node_groups` `editor_find_nodes_in_group` `editor_get_selection` `editor_set_node_selection` `editor_remove_node_selection` `editor_execute_gdscript` `editor_get_output_log` `editor_remove_output_log` `editor_reload_plugin` `editor_rescan_project_filesystem` `editor_get_node_signals` `editor_analyze_screenshot_diff` `editor_set_auto_dismiss_dialogs` `editor_get_viewport_3d_camera` `editor_set_viewport_3d_camera` `editor_get_performance_monitors` `editor_set_node_script` `editor_get_open_scripts` `editor_simulate_key` `editor_simulate_mouse_click` `editor_simulate_mouse_move` `editor_simulate_input_action` `editor_get_input_actions` `editor_simulate_input_sequence` `editor_find_nodes_by_type` `editor_set_node_property_batch` `editor_list_signal_connections` `editor_list_animations` `editor_create_animation` `editor_add_animation_track` `editor_set_animation_keyframe` `editor_get_animation_info` `editor_remove_animation` `editor_get_tilemap_info` `editor_get_tilemap_used_cells` `editor_remove_all_tilemap_cells` `editor_set_tilemap_cell` `editor_set_tilemap_cells_in_rect` `editor_get_tilemap_cell` `editor_set_shader_material` `editor_set_shader_param` `editor_add_raycast` `editor_setup_collision_shape` `editor_set_physics_layers` `editor_get_physics_layers` `editor_setup_physics_body` `editor_get_collision_info` `editor_add_mesh_instance` `editor_setup_camera_3d` `editor_setup_lighting` `editor_set_material_3d` `editor_setup_world_environment` `editor_add_gridmap` `editor_add_audio_player` `editor_get_audio_info` `editor_get_audio_bus_layout` `editor_add_audio_bus` `editor_set_audio_bus_property` `editor_add_audio_bus_effect` `editor_set_control_theme` `editor_create_animation_tree` `editor_get_animation_tree_structure` `editor_add_state_machine_state` `editor_remove_state_machine_state` `editor_add_state_machine_transition` `editor_remove_state_machine_transition` `editor_set_blend_tree_node` `editor_set_animation_tree_parameter` `editor_setup_navigation_region` `editor_bake_navigation_mesh` `editor_setup_navigation_agent` `editor_set_navigation_layers` `editor_get_navigation_info` `editor_create_particles` `editor_set_particle_material` `editor_set_particle_color_gradient` `editor_set_particle_preset` `editor_get_particle_info` `editor_analyze_signal_flow` `editor_get_test_report` `editor_set_node_property_updates`
- **os_**（2）：`os_list_android_devices` `os_deploy_to_android_device`
- **project_**（43）：`project_get_info` `project_get_filesystem_tree` `project_search_file_names` `project_search_file_contents` `project_get_settings` `project_set_setting` `project_convert_uid_to_path` `project_convert_path_to_uid` `project_read_scene_file_content` `project_delete_scene_file` `project_get_scene_exports` `project_create_scene_file` `project_list_scripts` `project_read_script` `project_validate_script` `project_find_files_referencing_symbol` `project_get_scene_dependencies` `project_set_node_property_across_scenes` `project_read_resource` `project_add_autoload` `project_remove_autoload` `project_edit_resource` `project_create_resource` `project_get_resource_preview` `project_get_export_info` `project_list_export_presets` `project_read_shader` `project_create_shader` `project_edit_shader` `project_get_shader_params` `project_create_theme` `project_set_theme_color` `project_set_theme_constant` `project_set_theme_font_size` `project_set_theme_stylebox` `project_get_theme_info` `project_find_unused_resources` `project_analyze_scene_complexity` `project_find_script_references` `project_detect_circular_dependencies` `project_get_statistics` `project_get_android_preset_info` `project_write_text_file`
- **running_**（12）：`running_game_capture_frames` `running_game_create_input_recording` `running_game_stop_input_recording` `running_game_play_input_recording` `running_game_find_nodes_by_script` `running_game_get_autoload_node` `running_game_get_node_properties_batch` `running_game_find_ui_elements` `running_game_simulate_button_click_by_text` `running_game_find_nearby_nodes` `running_game_move_player_to_target` `running_game_capture_signal_emissions`

## 3. `<5` 清单（本轮仍未达标的工具）

共 **152** 条（占契约 85.9%）：`0` 次 150 条、`1-4` 次 2 条。

| tool | scope | verb | 累计 | 有效 | 边界 | 登记不可达 | 状态 |
|---|---|---|---|---|---|---|---|
| `project_get_info` | both | get | 0 | 0 | 0 | - | 未达(0) |
| `project_get_filesystem_tree` | both | get | 0 | 0 | 0 | - | 未达(0) |
| `project_search_file_names` | both | search | 0 | 0 | 0 | - | 未达(0) |
| `project_search_file_contents` | both | search | 0 | 0 | 0 | - | 未达(0) |
| `project_get_settings` | both | get | 0 | 0 | 0 | - | 未达(0) |
| `project_set_setting` | both | set | 0 | 0 | 0 | - | 未达(0) |
| `project_convert_uid_to_path` | both | convert | 0 | 0 | 0 | - | 未达(0) |
| `project_convert_path_to_uid` | both | convert | 0 | 0 | 0 | - | 未达(0) |
| `project_read_scene_file_content` | both | read | 0 | 0 | 0 | - | 未达(0) |
| `project_delete_scene_file` | both | delete | 0 | 0 | 0 | - | 未达(0) |
| `editor_add_scene_instance` | editor | add | 0 | 0 | 0 | - | 未达(0) |
| `project_get_scene_exports` | both | get | 0 | 0 | 0 | - | 未达(0) |
| `editor_play_scene` | editor | play | 0 | 0 | 0 | H7 | 未达(0) |
| `editor_stop_scene` | editor | stop | 0 | 0 | 0 | H7 | 未达(0) |
| `project_create_scene_file` | both | create | 0 | 0 | 0 | - | 未达(0) |
| `editor_add_node` | editor | add | 0 | 0 | 0 | - | 未达(0) |
| `editor_rename_node` | editor | rename | 0 | 0 | 0 | - | 未达(0) |
| `editor_duplicate_node` | editor | duplicate | 0 | 0 | 0 | - | 未达(0) |
| `editor_connect_signal` | editor | connect | 0 | 0 | 0 | - | 未达(0) |
| `editor_disconnect_signal` | editor | disconnect | 0 | 0 | 0 | - | 未达(0) |
| `editor_reparent_node` | editor | reparent | 0 | 0 | 0 | - | 未达(0) |
| `editor_add_resource_to_node_property` | editor | add | 0 | 0 | 0 | - | 未达(0) |
| `editor_set_anchor_preset` | editor | set | 0 | 0 | 0 | - | 未达(0) |
| `editor_get_node_groups` | editor | get | 0 | 0 | 0 | - | 未达(0) |
| `editor_set_node_groups` | editor | set | 0 | 0 | 0 | - | 未达(0) |
| `editor_find_nodes_in_group` | editor | find | 0 | 0 | 0 | - | 未达(0) |
| `editor_get_selection` | editor | get | 0 | 0 | 0 | H7 | 未达(0) |
| `editor_set_node_selection` | editor | set | 0 | 0 | 0 | H7 | 未达(0) |
| `editor_remove_node_selection` | editor | remove | 0 | 0 | 0 | H7 | 未达(0) |
| `editor_execute_gdscript` | editor | execute | 0 | 0 | 0 | - | 未达(0) |
| `editor_get_output_log` | editor | get | 0 | 0 | 0 | H7 | 未达(0) |
| `editor_capture_screenshot` | editor | capture | 3 | 2 | 0 | - | 未达(1-4) |
| `editor_remove_output_log` | editor | remove | 0 | 0 | 0 | H7 | 未达(0) |
| `editor_reload_plugin` | editor | reload | 0 | 0 | 0 | H7 | 未达(0) |
| `editor_rescan_project_filesystem` | editor | rescan | 0 | 0 | 0 | H7 | 未达(0) |
| `editor_get_node_signals` | editor | get | 0 | 0 | 0 | - | 未达(0) |
| `editor_analyze_screenshot_diff` | editor | analyze | 0 | 0 | 0 | H7 | 未达(0) |
| `editor_set_auto_dismiss_dialogs` | editor | set | 0 | 0 | 0 | H7 | 未达(0) |
| `editor_get_viewport_3d_camera` | editor | get | 0 | 0 | 0 | H1 | 未达(0) |
| `editor_set_viewport_3d_camera` | editor | set | 0 | 0 | 0 | H1 | 未达(0) |
| `running_game_capture_frames` | game | capture | 0 | 0 | 0 | H9 | 未达(0) |
| `running_game_create_input_recording` | game | create | 0 | 0 | 0 | H9 | 未达(0) |
| `running_game_stop_input_recording` | game | stop | 0 | 0 | 0 | H9 | 未达(0) |
| `running_game_play_input_recording` | game | play | 0 | 0 | 0 | H9 | 未达(0) |
| `running_game_find_nodes_by_script` | game | find | 0 | 0 | 0 | - | 未达(0) |
| `running_game_get_autoload_node` | game | get | 0 | 0 | 0 | - | 未达(0) |
| `running_game_get_node_properties_batch` | game | get | 0 | 0 | 0 | - | 未达(0) |
| `running_game_find_ui_elements` | game | find | 0 | 0 | 0 | - | 未达(0) |
| `running_game_simulate_button_click_by_text` | game | simulate | 0 | 0 | 0 | - | 未达(0) |
| `running_game_find_node_when_available` | game | find | 1 | 0 | 1 | - | 未达(1-4) |
| `running_game_find_nearby_nodes` | game | find | 0 | 0 | 0 | - | 未达(0) |
| `running_game_move_player_to_target` | game | move | 0 | 0 | 0 | H4 | 未达(0) |
| `running_game_capture_signal_emissions` | game | capture | 0 | 0 | 0 | H9 | 未达(0) |
| `editor_get_performance_monitors` | editor | get | 0 | 0 | 0 | H7 | 未达(0) |
| `project_list_scripts` | both | list | 0 | 0 | 0 | - | 未达(0) |
| `project_read_script` | both | read | 0 | 0 | 0 | - | 未达(0) |
| `editor_set_node_script` | editor | set | 0 | 0 | 0 | - | 未达(0) |
| `editor_get_open_scripts` | editor | get | 0 | 0 | 0 | H7 | 未达(0) |
| `project_validate_script` | both | validate | 0 | 0 | 0 | - | 未达(0) |
| `editor_simulate_key` | editor | simulate | 0 | 0 | 0 | H7 | 未达(0) |
| `editor_simulate_mouse_click` | editor | simulate | 0 | 0 | 0 | H7 | 未达(0) |
| `editor_simulate_mouse_move` | editor | simulate | 0 | 0 | 0 | H7 | 未达(0) |
| `editor_simulate_input_action` | editor | simulate | 0 | 0 | 0 | H7 | 未达(0) |
| `editor_get_input_actions` | editor | get | 0 | 0 | 0 | - | 未达(0) |
| `editor_simulate_input_sequence` | editor | simulate | 0 | 0 | 0 | H7 | 未达(0) |
| `editor_find_nodes_by_type` | editor | find | 0 | 0 | 0 | - | 未达(0) |
| `editor_set_node_property_batch` | editor | set | 0 | 0 | 0 | - | 未达(0) |
| `editor_list_signal_connections` | editor | list | 0 | 0 | 0 | - | 未达(0) |
| `project_find_files_referencing_symbol` | both | find | 0 | 0 | 0 | - | 未达(0) |
| `project_get_scene_dependencies` | both | get | 0 | 0 | 0 | - | 未达(0) |
| `project_set_node_property_across_scenes` | both | set | 0 | 0 | 0 | - | 未达(0) |
| `editor_list_animations` | editor | list | 0 | 0 | 0 | H2 | 未达(0) |
| `editor_create_animation` | editor | create | 0 | 0 | 0 | H2 | 未达(0) |
| `editor_add_animation_track` | editor | add | 0 | 0 | 0 | H2 | 未达(0) |
| `editor_set_animation_keyframe` | editor | set | 0 | 0 | 0 | H2 | 未达(0) |
| `editor_get_animation_info` | editor | get | 0 | 0 | 0 | H2 | 未达(0) |
| `editor_remove_animation` | editor | remove | 0 | 0 | 0 | H2 | 未达(0) |
| `editor_get_tilemap_info` | editor | get | 0 | 0 | 0 | H3 | 未达(0) |
| `editor_get_tilemap_used_cells` | editor | get | 0 | 0 | 0 | H3 | 未达(0) |
| `editor_remove_all_tilemap_cells` | editor | remove | 0 | 0 | 0 | H3 | 未达(0) |
| `editor_set_tilemap_cell` | editor | set | 0 | 0 | 0 | H3 | 未达(0) |
| `editor_set_tilemap_cells_in_rect` | editor | set | 0 | 0 | 0 | H3 | 未达(0) |
| `editor_get_tilemap_cell` | editor | get | 0 | 0 | 0 | H3 | 未达(0) |
| `project_read_resource` | both | read | 0 | 0 | 0 | - | 未达(0) |
| `project_add_autoload` | both | add | 0 | 0 | 0 | - | 未达(0) |
| `project_remove_autoload` | both | remove | 0 | 0 | 0 | - | 未达(0) |
| `project_edit_resource` | both | edit | 0 | 0 | 0 | - | 未达(0) |
| `project_create_resource` | both | create | 0 | 0 | 0 | - | 未达(0) |
| `project_get_resource_preview` | both | get | 0 | 0 | 0 | - | 未达(0) |
| `project_get_export_info` | both | get | 0 | 0 | 0 | H8 | 未达(0) |
| `project_list_export_presets` | both | list | 0 | 0 | 0 | H8 | 未达(0) |
| `project_read_shader` | both | read | 0 | 0 | 0 | - | 未达(0) |
| `project_create_shader` | both | create | 0 | 0 | 0 | - | 未达(0) |
| `project_edit_shader` | both | edit | 0 | 0 | 0 | - | 未达(0) |
| `editor_set_shader_material` | editor | set | 0 | 0 | 0 | - | 未达(0) |
| `editor_set_shader_param` | editor | set | 0 | 0 | 0 | - | 未达(0) |
| `project_get_shader_params` | both | get | 0 | 0 | 0 | - | 未达(0) |
| `editor_add_raycast` | editor | add | 0 | 0 | 0 | - | 未达(0) |
| `editor_setup_collision_shape` | editor | setup | 0 | 0 | 0 | - | 未达(0) |
| `editor_set_physics_layers` | editor | set | 0 | 0 | 0 | - | 未达(0) |
| `editor_get_physics_layers` | editor | get | 0 | 0 | 0 | - | 未达(0) |
| `editor_setup_physics_body` | editor | setup | 0 | 0 | 0 | - | 未达(0) |
| `editor_get_collision_info` | editor | get | 0 | 0 | 0 | - | 未达(0) |
| `editor_add_mesh_instance` | editor | add | 0 | 0 | 0 | H1 | 未达(0) |
| `editor_setup_camera_3d` | editor | setup | 0 | 0 | 0 | H1 | 未达(0) |
| `editor_setup_lighting` | editor | setup | 0 | 0 | 0 | H1 | 未达(0) |
| `editor_set_material_3d` | editor | set | 0 | 0 | 0 | H1 | 未达(0) |
| `editor_setup_world_environment` | editor | setup | 0 | 0 | 0 | H1 | 未达(0) |
| `editor_add_gridmap` | editor | add | 0 | 0 | 0 | H3 | 未达(0) |
| `editor_add_audio_player` | editor | add | 0 | 0 | 0 | H5 | 未达(0) |
| `editor_get_audio_info` | editor | get | 0 | 0 | 0 | H5 | 未达(0) |
| `editor_get_audio_bus_layout` | editor | get | 0 | 0 | 0 | H5 | 未达(0) |
| `editor_add_audio_bus` | editor | add | 0 | 0 | 0 | H5 | 未达(0) |
| `editor_set_audio_bus_property` | editor | set | 0 | 0 | 0 | H5 | 未达(0) |
| `editor_add_audio_bus_effect` | editor | add | 0 | 0 | 0 | H5 | 未达(0) |
| `project_create_theme` | both | create | 0 | 0 | 0 | - | 未达(0) |
| `project_set_theme_color` | both | set | 0 | 0 | 0 | - | 未达(0) |
| `project_set_theme_constant` | both | set | 0 | 0 | 0 | - | 未达(0) |
| `project_set_theme_font_size` | both | set | 0 | 0 | 0 | - | 未达(0) |
| `project_set_theme_stylebox` | both | set | 0 | 0 | 0 | - | 未达(0) |
| `editor_set_control_theme` | editor | set | 0 | 0 | 0 | - | 未达(0) |
| `project_get_theme_info` | both | get | 0 | 0 | 0 | - | 未达(0) |
| `editor_create_animation_tree` | editor | create | 0 | 0 | 0 | H2 | 未达(0) |
| `editor_get_animation_tree_structure` | editor | get | 0 | 0 | 0 | H2 | 未达(0) |
| `editor_add_state_machine_state` | editor | add | 0 | 0 | 0 | H2 | 未达(0) |
| `editor_remove_state_machine_state` | editor | remove | 0 | 0 | 0 | H2 | 未达(0) |
| `editor_add_state_machine_transition` | editor | add | 0 | 0 | 0 | H2 | 未达(0) |
| `editor_remove_state_machine_transition` | editor | remove | 0 | 0 | 0 | H2 | 未达(0) |
| `editor_set_blend_tree_node` | editor | set | 0 | 0 | 0 | H2 | 未达(0) |
| `editor_set_animation_tree_parameter` | editor | set | 0 | 0 | 0 | H2 | 未达(0) |
| `editor_setup_navigation_region` | editor | setup | 0 | 0 | 0 | H4 | 未达(0) |
| `editor_bake_navigation_mesh` | editor | bake | 0 | 0 | 0 | H4 | 未达(0) |
| `editor_setup_navigation_agent` | editor | setup | 0 | 0 | 0 | H4 | 未达(0) |
| `editor_set_navigation_layers` | editor | set | 0 | 0 | 0 | H4 | 未达(0) |
| `editor_get_navigation_info` | editor | get | 0 | 0 | 0 | H4 | 未达(0) |
| `editor_create_particles` | editor | create | 0 | 0 | 0 | H6 | 未达(0) |
| `editor_set_particle_material` | editor | set | 0 | 0 | 0 | H6 | 未达(0) |
| `editor_set_particle_color_gradient` | editor | set | 0 | 0 | 0 | H6 | 未达(0) |
| `editor_set_particle_preset` | editor | set | 0 | 0 | 0 | H6 | 未达(0) |
| `editor_get_particle_info` | editor | get | 0 | 0 | 0 | H6 | 未达(0) |
| `project_find_unused_resources` | both | find | 0 | 0 | 0 | - | 未达(0) |
| `editor_analyze_signal_flow` | editor | analyze | 0 | 0 | 0 | - | 未达(0) |
| `project_analyze_scene_complexity` | both | analyze | 0 | 0 | 0 | - | 未达(0) |
| `project_find_script_references` | both | find | 0 | 0 | 0 | - | 未达(0) |
| `project_detect_circular_dependencies` | both | detect | 0 | 0 | 0 | - | 未达(0) |
| `project_get_statistics` | both | get | 0 | 0 | 0 | - | 未达(0) |
| `editor_get_test_report` | editor | get | 0 | 0 | 0 | H7 | 未达(0) |
| `os_list_android_devices` | both | list | 0 | 0 | 0 | H8 | 未达(0) |
| `project_get_android_preset_info` | both | get | 0 | 0 | 0 | H8 | 未达(0) |
| `os_deploy_to_android_device` | both | deploy | 0 | 0 | 0 | H8 | 未达(0) |
| `project_write_text_file` | both | write | 0 | 0 | 0 | - | 未达(0) |
| `editor_set_node_property_updates` | editor | set | 0 | 0 | 0 | - | 未达(0) |

## 4. 不可达登记表的联动视图（H1–H9）

登记来源：`recovery/reports/TOOL-COVERAGE-TASK-108.md` §5.3 (5) which of them are structurally unreachable in this loop (INFERENCE)（**推断**，判据是「缺少本循环不具备的子系统/资产/前置运行态」）。本视图把登记表与本轮实测**对在一起**：`实测调用` 列不为 0 的条目就是登记漂移，必须在下一轮从登记表里移除或改判。

登记成员 **74** 条；其中本轮实测**已被调用**（登记漂移）**0** 条。

### H1 3D 内容管线

- 为何不可达（推断）：20 款游戏**全部是 2D**，世界由 `ColorRect` / `Label` 在运行期或加载期拼出；工程里没有任何 Mesh / Camera3D / 光照 / WorldEnvironment 资产，也没有 `.tscn` 里能寻址的 3D 节点
- 支撑证据（只读观察）：模块侧 `tools/editor_scene_3d_write.cpp`；20 款游戏的载荷全部为 2D 坐标（台账逐条记 `ColorRect`/`Label`/像素差）

| tool | scope | 实测调用 | 漂移 | 证据 |
|---|---|---|---|---|
| `editor_add_mesh_instance` | editor | 0 | - | - |
| `editor_get_viewport_3d_camera` | editor | 0 | - | - |
| `editor_set_material_3d` | editor | 0 | - | - |
| `editor_set_viewport_3d_camera` | editor | 0 | - | - |
| `editor_setup_camera_3d` | editor | 0 | - | - |
| `editor_setup_lighting` | editor | 0 | - | - |
| `editor_setup_world_environment` | editor | 0 | - | - |

### H2 动画 / AnimationTree / 状态机

- 为何不可达（推断）：运动一律由**载荷自己的整数运动学**推进（`StepFrames(n)`、`_Process` 里 `x+=vx`），从不使用 `AnimationPlayer` / `AnimationTree`；没有动画资源可读写，也没有状态机可建
- 支撑证据（只读观察）：`tools/editor_animation_read.cpp`、`editor_animation_write.cpp`、`editor_animation_tree_write.cpp`、`tools/animation_shared.cpp`；契约 override 里 `add_state_machine_state` 的 `animation` 成员是「结构性不可达」的已知缺口

| tool | scope | 实测调用 | 漂移 | 证据 |
|---|---|---|---|---|
| `editor_add_animation_track` | editor | 0 | - | - |
| `editor_add_state_machine_state` | editor | 0 | - | - |
| `editor_add_state_machine_transition` | editor | 0 | - | - |
| `editor_create_animation` | editor | 0 | - | - |
| `editor_create_animation_tree` | editor | 0 | - | - |
| `editor_get_animation_info` | editor | 0 | - | - |
| `editor_get_animation_tree_structure` | editor | 0 | - | - |
| `editor_list_animations` | editor | 0 | - | - |
| `editor_remove_animation` | editor | 0 | - | - |
| `editor_remove_state_machine_state` | editor | 0 | - | - |
| `editor_remove_state_machine_transition` | editor | 0 | - | - |
| `editor_set_animation_keyframe` | editor | 0 | - | - |
| `editor_set_animation_tree_parameter` | editor | 0 | - | - |
| `editor_set_blend_tree_node` | editor | 0 | - | - |

### H3 TileMap / GridMap

- 为何不可达（推断）：棋盘、迷宫、格点全部是**运行期新建的独立 `ColorRect`**（如 Pac-Man 的 125 颗豆子、Sokoban 的箱子、Match-3 的 8×8），20 个工程里没有 `TileMapLayer`、没有 `GridMap`、也没有 `TileSet` 资源，因此整族都没有作用对象
- 支撑证据（只读观察）：`tools/editor_tilemap_read.cpp`、`editor_tilemap_write.cpp`、`tilemap_shared.cpp`。**额外证据（契约自述）**：`editor_set_tilemap_cell` / `editor_set_tilemap_cells_in_rect` 的 `description` 明写「当前工具集没有任何『给 TileSet 添加 atlas source / texture / tile』的入口，所以在可预见的调用序列里本工具无法成功 —— 这是一处如实声明的能力缺口」；同一条 override 另注明该缺口句只挂在两个**写**工具上，`editor_get_tilemap_info/_used_cells/_cell` 与 `editor_remove_all_tilemap_cells` 不要求 source 存在（即有 TileMapLayer 时它们是可达的）

| tool | scope | 实测调用 | 漂移 | 证据 |
|---|---|---|---|---|
| `editor_add_gridmap` | editor | 0 | - | - |
| `editor_get_tilemap_cell` | editor | 0 | - | - |
| `editor_get_tilemap_info` | editor | 0 | - | - |
| `editor_get_tilemap_used_cells` | editor | 0 | - | - |
| `editor_remove_all_tilemap_cells` | editor | 0 | - | - |
| `editor_set_tilemap_cell` | editor | 0 | - | - |
| `editor_set_tilemap_cells_in_rect` | editor | 0 | - | - |

### H4 导航

- 为何不可达（推断）：需要先有 `NavigationRegion2D` + 烘焙过的 `NavigationMesh` + `NavigationAgent`；本循环的寻路是载荷自己手写的格点/路径算法（Tower Defense 的 101 格蛇形走廊由 ASCII 地图确定性导出，Python 复算 `PathHash`），没有任何导航资产
- 支撑证据（只读观察）：`tools/editor_navigation_read.cpp`、`editor_navigation_write.cpp`、`running_game_navigation_write.cpp`（`running_game_move_player_to_target` 就在这个文件里，前置条件即导航代理）

| tool | scope | 实测调用 | 漂移 | 证据 |
|---|---|---|---|---|
| `editor_bake_navigation_mesh` | editor | 0 | - | - |
| `editor_get_navigation_info` | editor | 0 | - | - |
| `editor_set_navigation_layers` | editor | 0 | - | - |
| `editor_setup_navigation_agent` | editor | 0 | - | - |
| `editor_setup_navigation_region` | editor | 0 | - | - |
| `running_game_move_player_to_target` | game | 0 | - | - |

### H5 音频

- 为何不可达（推断）：20 款游戏**没有一个有声音**，没有 `AudioStreamPlayer`、没有 bus 布局，也没有音频资产
- 支撑证据（只读观察）：`tools/editor_audio_read.cpp`、`editor_audio_write.cpp`、`audio_shared.cpp`

| tool | scope | 实测调用 | 漂移 | 证据 |
|---|---|---|---|---|
| `editor_add_audio_bus` | editor | 0 | - | - |
| `editor_add_audio_bus_effect` | editor | 0 | - | - |
| `editor_add_audio_player` | editor | 0 | - | - |
| `editor_get_audio_bus_layout` | editor | 0 | - | - |
| `editor_get_audio_info` | editor | 0 | - | - |
| `editor_set_audio_bus_property` | editor | 0 | - | - |

### H6 粒子

- 为何不可达（推断）：全部视觉证据是「节点位置/颜色 → 像素差」，没有任何 `GPUParticles2D` / 粒子材质 / 渐变
- 支撑证据（只读观察）：`tools/editor_particle_read.cpp`、`editor_particle_write.cpp`、`particle_shared.cpp`

| tool | scope | 实测调用 | 漂移 | 证据 |
|---|---|---|---|---|
| `editor_create_particles` | editor | 0 | - | - |
| `editor_get_particle_info` | editor | 0 | - | - |
| `editor_set_particle_color_gradient` | editor | 0 | - | - |
| `editor_set_particle_material` | editor | 0 | - | - |
| `editor_set_particle_preset` | editor | 0 | - | - |

### H7 编辑器 GUI 状态 / 编辑器自有播放与输入注入 / 编辑器侧测试运行

- 为何不可达（推断）：这类工具的输入是**编辑器进程自己的 GUI 状态**（当前选择、打开的脚本、Output 面板、对话框、已装插件）或**编辑器自己的播放器/输入队列**。本循环里编辑器端点只做「开场景 / 加节点 / 存场景 / 建脚本 / 编译 / 读错误」；所有行为验证都走游戏端点，且**刻意不用**编辑器侧输入注入（B2 说明：`editor_simulate_*` 注入的是编辑器进程的输入，不能用来驱动游戏进程 —— D59 / GDR-21 的边界）
- 支撑证据（只读观察）：`tools/editor_playback.cpp`、`editor_input_simulation.cpp`、`editor_profiling_read.cpp`、`editor_testing_read.cpp`、`editor_script_write.cpp`、`editor_read_scene_inspector.cpp`；`editor_get_test_report` / `editor_analyze_screenshot_diff` 需要「编辑器侧测试运行」，而本循环的测试运行发生在游戏端点

| tool | scope | 实测调用 | 漂移 | 证据 |
|---|---|---|---|---|
| `editor_analyze_screenshot_diff` | editor | 0 | - | - |
| `editor_get_open_scripts` | editor | 0 | - | - |
| `editor_get_output_log` | editor | 0 | - | - |
| `editor_get_performance_monitors` | editor | 0 | - | - |
| `editor_get_selection` | editor | 0 | - | - |
| `editor_get_test_report` | editor | 0 | - | - |
| `editor_play_scene` | editor | 0 | - | - |
| `editor_reload_plugin` | editor | 0 | - | - |
| `editor_remove_node_selection` | editor | 0 | - | - |
| `editor_remove_output_log` | editor | 0 | - | - |
| `editor_rescan_project_filesystem` | editor | 0 | - | - |
| `editor_set_auto_dismiss_dialogs` | editor | 0 | - | - |
| `editor_set_node_selection` | editor | 0 | - | - |
| `editor_simulate_input_action` | editor | 0 | - | - |
| `editor_simulate_input_sequence` | editor | 0 | - | - |
| `editor_simulate_key` | editor | 0 | - | - |
| `editor_simulate_mouse_click` | editor | 0 | - | - |
| `editor_simulate_mouse_move` | editor | 0 | - | - |
| `editor_stop_scene` | editor | 0 | - | - |

### H8 发布 / 导出 / Android 部署路径

- 为何不可达（推断）：循环的终点是「游戏跑起来 + 可复算证据」，从不打包、不导出、不连真机；`project_export_game` 甚至被契约 `_meta.excluded` 排除、`project_get_export_info` 等只在发布路径生效
- 支撑证据（只读观察）：`tools/project_export_read.cpp`、`os_android_read.cpp`、`os_android_write.cpp`、`project_android_read.cpp`；契约 `_meta.excluded = ["navigate_to","export_project"]`

| tool | scope | 实测调用 | 漂移 | 证据 |
|---|---|---|---|---|
| `os_deploy_to_android_device` | both | 0 | - | - |
| `os_list_android_devices` | both | 0 | - | - |
| `project_get_android_preset_info` | both | 0 | - | - |
| `project_get_export_info` | both | 0 | - | - |
| `project_list_export_presets` | both | 0 | - | - |

### H9 运行期录放与特殊捕获（deferred / 条件态）

- 为何不可达（推断）：需要先进入某个**非默认运行态**才有效：`running_game_capture_frames` 需要开启逐帧捕获模式（本循环用的是整帧截图 `capture_screenshot`，298 次），信号发射捕获需要先注册监听，输入录制族需要「先 create → 再 play/stop」的三步会话。本循环的输入证据走的是**声明式 input action + 断言/场景驱动**，从未开过录制器
- 支撑证据（只读观察）：`tools/running_game_capture.cpp`、`input_recorder.cpp`、`running_game_input.cpp`；台账里所有输入证据都是 `editor_add_input_action` + `running_game_run_test_scenario`

| tool | scope | 实测调用 | 漂移 | 证据 |
|---|---|---|---|---|
| `running_game_capture_frames` | game | 0 | - | - |
| `running_game_capture_signal_emissions` | game | 0 | - | - |
| `running_game_create_input_recording` | game | 0 | - | - |
| `running_game_play_input_recording` | game | 0 | - | - |
| `running_game_stop_input_recording` | game | 0 | - | - |

## 5. 本轮批次进度（--targets）

批次 **0** 条：达标 **0**、计数达标缺证据 **0**、未达 **0**。

| tool | scope | 累计 | 有效 | 边界 | 状态 | 证据 |
|---|---|---|---|---|---|---|

## 输入指纹

| 文件 | 字节 | sha256 |
|---|---|---|
| `dist\review_data.json` | 25937 | `E9CF20F5039511C99C488C149D90E2938BBA4F3153DEA41C88D72FF70B624F77` |
| `godot\modules\mcp_server\docs\tool-rename-map.json` | 70917 | `2F552719F6A23FE328DF0A2944C6048824C1B2A750AEBC0FE2CABBCD3529C2BD` |
| `godot\modules\mcp_server\docs\tools_list.renamed.json` | 153330 | `BD68E80472C8E15D674C45BF5816EE708EA08CF71F209A0E0114373D6067B640` |

