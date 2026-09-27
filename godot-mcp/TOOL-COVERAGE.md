# TOOL-COVERAGE — 契约工具覆盖台账（all-runs）

> 本文件由 `tool_coverage.py` 自动生成，**随时可重跑刷新**。命令行：
> `python tools/tool_coverage.py`

口径（mode）：**all-runs**；语料：**102 个 run 目录 / 168 个 trace 文件 / 8444 次 `tools/call`**（`ok=false` 601 次、解析失败行 0、sidecar 校验通过 273）

生成时间（UTC）：2026-09-27T03:25:24Z

**「有效调用」的判定**（由 `mcp_trace_ledger.py` 的 verdict 词汇给出，不另立一套）：

- `边界调用` = 该工具 `ok=false` 的调用次数（失败/拒绝即边界证据）。
- `有效调用`：**读类动词**（get/read/search/list/find/analyze/detect/convert/validate/check/assert/execute/evaluate，后三个的生效证据就是它回包的那个值或判词）= `ok=true` 且回包是实质载荷（读类调用不会动像素/字节，回包本身就是证据）；
  **其余动词**（create/edit/set/add/remove/write/build…）= ledger 的 `ok_effect_observed` / `ok_file_effect_observed`，即真的改了画面或文件。带 `assertion_failed` / `created_conflict` / `scenario_errors` 的 ok 调用不计有效。
- `状态`：`达标` = 调用≥5 且 有效≥1 且 边界≥1；`计数达标缺证据` = 调用≥5 但缺有效或边界；`未达(1-4)` / `未达(0)`；`不可达` 不在本表状态里，见 §4 登记表。

**「证据档位」的判定**（TASK-112 B；档位由强到弱，一个工具只落一档）：

| 档位 | 判据 | 工具数 |
|---|---|---|
| `pixel_effect` | ok_effect_observed（画面/视口真的变了） | 34 |
| `file_effect` | ok_file_effect_observed（文件真的变了） | 24 |
| `readback` | readback：另一次独立读调用读回佐证（witness_read）或读类工具自己的载荷（own_payload） | 87 |
| `count_only` | 只有计数与边界，没有生效证据 | 12 |
| `no_calls` | 0 次调用 | 20 |

- `readback` 有两种 **互不混同** 的 kind：`witness_read`（写类工具，效果由**另一次独立的读调用**在同一 run 内读回佐证）与 `own_payload`（读类动词，回包本身即测量结果，不存在可等的第二次调用）。
- `witness_read` **不是推断**：配对写在会话 manifest 的 `readback` 数组里，本工具会回到该 run 的 trace 里把见证调用**再找一次**（必须 `ok=true` 且回包是实质载荷），找不到就不给档位（见 §0.1 的 rejected 列表）。
- **内容级复核（TASK-113 C）**：声明可带 `expect`（一个或一组字面量），本工具在**见证调用的回包**里逐字搜它（回包被 trace 截断时读已核验的 sidecar）；搜不到就**不给档位**并记入 rejected，理由逐条写出。所以 `witness_read` 现在证明的是「写进去的值能从引擎自己的回答里读回来」，不再只是「那一次读调用发生过」。
- **不得**把「写工具自己响应里说成功了」当作 readback：那条路径只能落在 `count_only`。

### 0.1 readback 声明与见证（TASK-112 B；内容级 `expect` 复核见 TASK-113 C）

声明 **38** 条（来源：`tools/sessions/_exercises/**/*-manifest.json` 的 `readback` 数组）；**经 trace 复核通过 33 条**，被拒 5 条；其中带 `expect` 的声明 **33** 条、**逐字命中 33** 条。

下表只列 `kind = witness_read` 的档位（**有**独立读调用可以点名的那一类，共 33 条）；另外 60 条是 `own_payload`（读类动词，回包即证据、没有第二次调用可点名），它们逐条列在 §0.2。

| 写工具 | kind | 见证读调用 | run | 见证 seq | 内容级 `expect`（逐字） | `expect_absent` | 读回的是什么 |
|---|---|---|---|---|---|---|---|
| `editor_add_scene_instance` | `witness_read` | `editor_get_scene_tree` | runs/_exercises/ex_write5/c4-v5-task111 | 132 | `"Sub1"` | - | 挂载的实例必须出现在编辑场景树里（editor_get_scene_tree 列出被实例化出来的节点） |
| `editor_rename_node` | `witness_read` | `editor_get_node_properties` | runs/_exercises/ex_write5/c4-v5-task111 | 138 | `"name":"Ren1"` | - | 读回被改名节点的 name（重命名后按新名字仍可寻址） |
| `editor_disconnect_signal` | `witness_read` | `editor_list_signal_connections` | runs/_exercises/ex_write6/c5-task111 | 13 | `"count":0` | - | 断开之后再读一次连接表：count=0（同一次运行、同一个节点） |
| `editor_set_node_groups` | `witness_read` | `editor_get_node_groups` | runs/_exercises/ex_write5/c4-v5-task111 | 143 | `"ex_host"` | - | 读回被写节点的 groups 列表 |
| `editor_set_viewport_3d_camera` | `witness_read` | `editor_get_viewport_3d_camera` | runs/_exercises/ex_3d/h1-task111 | 27 | `"position":{"x":1.0,"y":1.0,"z":1.0}` | - | 下一次调用读回上一次写入的 fov/position |
| `running_game_create_input_recording` | `witness_read` | `running_game_stop_input_recording` | runs/_exercises/ex_rec/h9-task113 | 5 | `"event_count":2` | - | the stop call's answer carries the events of the session create started (event_count > 0) |
| `running_game_stop_input_recording` | `witness_read` | `running_game_get_node_properties` | runs/_exercises/ex_rec/h9-task113 | 2 | `"position"` | - | the position read after the stop differs from the position read before the session (the recorded keys moved the player) |
| `editor_create_animation` | `witness_read` | `editor_list_animations` | runs/_exercises/ex_anim2/h2b-task111 | 23 | `"Anim5"` | - | 读回动画列表，新建的动画在其中 |
| `editor_add_animation_track` | `witness_read` | `editor_get_animation_info` | runs/_exercises/ex_anim2/h2b-task111 | 29 | `"path":"Target:scale"` | - | 读回同一动画的轨道表 |
| `editor_set_animation_keyframe` | `witness_read` | `editor_get_animation_info` | runs/_exercises/ex_anim2/h2b-task111 | 29 | `"easing":2.0` ; `"time":1.0` | - | 读回同一动画的关键帧 |
| `editor_set_physics_layers` | `witness_read` | `editor_get_node_properties` | runs/_exercises/ex_write5/c4-v5-task111 | 139 | `"collision_layer":1` | - | 读回同一个节点的 collision_layer / collision_mask |
| `editor_setup_physics_body` | `witness_read` | `editor_get_scene_tree` | runs/_exercises/ex_write5/c4-v5-task111 | 132 | `"PB1"` | - | 建出来的物理体节点必须出现在编辑场景树里 |
| `editor_add_audio_player` | `witness_read` | `editor_get_node_properties` | runs/_exercises/ex_audio/h5-task113 | 42 | `AudioStreamPlayer2D` | - | the node editor_add_audio_player created must be in the scene as an AudioStreamPlayer2D |
| `editor_add_audio_bus` | `witness_read` | `editor_get_audio_bus_layout` | runs/_exercises/ex_audio/h5-task113 | 22 | `"Music"` | - | the bus editor_add_audio_bus created must appear in the engine's bus layout |
| `editor_set_audio_bus_property` | `witness_read` | `editor_get_audio_bus_layout` | runs/_exercises/ex_audio/h5-task113 | 43 | `"volume_db":-6` | - | the written volume_db must be the bus's real value in the layout |
| `editor_add_audio_bus_effect` | `witness_read` | `editor_get_audio_bus_layout` | runs/_exercises/ex_audio/h5-task113 | 22 | `AudioEffectAmplify` | - | the effect must appear in the bus's effect list with the engine's class name |
| `editor_create_animation_tree` | `witness_read` | `editor_get_animation_tree_structure` | runs/_exercises/ex_anim2/h2b-task111 | 88 | `"parameters/BT/B1/blend_amount"` | - | 读回 AnimationTree 的结构（tree_root / 状态机） |
| `editor_add_state_machine_state` | `witness_read` | `editor_get_animation_tree_structure` | runs/_exercises/ex_anim2/h2b-task111 | 88 | `"Walk"` | - | 读回状态机里的状态列表 |
| `editor_remove_state_machine_state` | `witness_read` | `editor_get_animation_tree_structure` | runs/_exercises/ex_anim2/h2b-task111 | 91 | `"node_path":"AT4"` | `Extra0` ; `Extra4` | 读回状态机里的状态列表，被删的状态不在了 |
| `editor_add_state_machine_transition` | `witness_read` | `editor_get_animation_tree_structure` | runs/_exercises/ex_anim2/h2b-task111 | 88 | `"Idle"` | - | 读回状态机里的迁移列表 |
| `editor_remove_state_machine_transition` | `witness_read` | `editor_get_animation_tree_structure` | runs/_exercises/ex_anim2/h2b-task111 | 88 | `"transition_count":5` | `"from":"Idle","index":0,"switch_mode":"immediate","to":"Walk"` | 读回状态机里的迁移列表，被删的迁移不在了 |
| `editor_set_blend_tree_node` | `witness_read` | `editor_get_animation_tree_structure` | runs/_exercises/ex_anim2/h2b-task111 | 88 | `parameters/BT/T1/scale` | - | 读回混合树节点真的挂在树上 |
| `editor_set_animation_tree_parameter` | `witness_read` | `editor_get_animation_tree_structure` | runs/_exercises/ex_anim2/h2b-task111 | 88 | `parameters/Walk/backward` | - | 读回参数表里出现被写的参数 |
| `editor_setup_navigation_region` | `witness_read` | `editor_get_navigation_info` | runs/_exercises/ex_nav/h4-task113 | 27 | `"RegionA"` | - | the created NavigationRegion2D must appear in editor_get_navigation_info's region list with its real class and layer mask |
| `editor_setup_navigation_agent` | `witness_read` | `editor_get_navigation_info` | runs/_exercises/ex_nav/h4-task113 | 27 | `"max_speed"` | - | the created NavigationAgent2D must appear in the agent list with the radius and max_speed the tool wrote |
| `editor_set_navigation_layers` | `witness_read` | `editor_get_navigation_info` | runs/_exercises/ex_nav/h4-task113 | 27 | `"navigation_layers":2` | - | the mask editor_set_navigation_layers wrote must be in the read-back record |
| `editor_create_particles` | `witness_read` | `editor_get_particle_info` | runs/_exercises/ex_particles/h6-task113 | 34 | `"process_material_slot":"process_material"` | - | the created system must answer as a GPUParticles2D with its own process_material |

**被拒的声明（找不到合格的见证调用，或内容级 `expect` 未命中；档位不授予）**：

- `editor_add_gridmap` <- `editor_get_scene_tree` @ `runs/_exercises/ex_grid/h3-task111`（声明于 `tools/sessions/_exercises/ex_grid/h3-manifest.json`）：no `ok=true` substantive call of `editor_get_scene_tree` in that run
- `editor_connect_signal` <- `editor_list_signal_connections` @ `runs/_exercises/ex_write5/c4-v5-task111`（声明于 `tools/sessions/_exercises/ex_write/c4-manifest.json`）：no `ok=true` substantive call of `editor_list_signal_connections` in that run
- `editor_remove_animation` <- `editor_list_animations` @ `runs/_exercises/ex_anim2/h2b-task111`（声明于 `tools/sessions/_exercises/ex_anim/h2-manifest.json`）：no content-level `expect`/`expect_absent` declared: the witness would only prove that a read call happened (TASK-113 item C requires the written value, or the removal it addresses, to be readable back)
- `editor_set_control_theme` <- `editor_get_node_properties` @ `runs/_exercises/ex_write5/c4-v5-task111`（声明于 `tools/sessions/_exercises/ex_write/c4-manifest.json`）：no content-level `expect`/`expect_absent` declared: the witness would only prove that a read call happened (TASK-113 item C requires the written value, or the removal it addresses, to be readable back)
- `editor_set_node_script` <- `editor_get_node_properties` @ `runs/_exercises/ex_write5/c4-v5-task111`（声明于 `tools/sessions/_exercises/ex_write/c4-manifest.json`）：no content-level `expect`/`expect_absent` declared: the witness would only prove that a read call happened (TASK-113 item C requires the written value, or the removal it addresses, to be readable back)

### 0.2 逐档工具清单（TASK-112 B）

- **`pixel_effect`**（34）：`editor_open_scene` `editor_add_node` `editor_delete_node` `editor_set_node_property` `editor_duplicate_node` `editor_reparent_node` `editor_add_resource_to_node_property` `editor_set_anchor_preset` `running_game_capture_screenshot` `running_game_get_scene_tree` `running_game_get_node_properties` `running_game_set_node_property` `running_game_get_node_property_samples` `running_game_execute_gdscript` `running_game_play_input_recording` `running_game_simulate_button_click_by_text` `running_game_move_player_to_target` `editor_set_node_property_batch` `editor_add_nodes_batch` `editor_remove_all_tilemap_cells` `editor_set_tilemap_cell` `editor_set_tilemap_cells_in_rect` `editor_set_shader_material` `editor_set_shader_param` `editor_add_raycast` `editor_setup_collision_shape` `editor_bake_navigation_mesh` `editor_set_particle_material` `editor_set_particle_color_gradient` `editor_set_particle_preset` `editor_get_particle_info` `running_game_run_test_scenario` `running_game_run_stress_test` `editor_set_node_property_updates`
- **`file_effect`**（24）：`project_set_setting` `project_delete_scene_file` `editor_save_scene` `project_create_scene_file` `editor_capture_screenshot` `project_create_script` `project_edit_script` `editor_add_input_action` `project_set_node_property_across_scenes` `project_add_autoload` `project_remove_autoload` `project_edit_resource` `project_create_resource` `project_create_shader` `project_edit_shader` `project_create_theme` `project_set_theme_color` `project_set_theme_constant` `project_set_theme_font_size` `project_set_theme_stylebox` `running_game_assert_node_state` `running_game_assert_screen_text` `project_build_csharp` `project_write_text_file`
- **`readback`**（87）：`project_get_info` `project_get_filesystem_tree` `project_search_file_names` `project_search_file_contents` `project_get_settings` `project_convert_uid_to_path` `project_convert_path_to_uid` `editor_get_scene_tree` `project_read_scene_file_content` `editor_add_scene_instance` `project_get_scene_exports` `editor_rename_node` `editor_get_node_properties` `editor_disconnect_signal` `editor_get_node_groups` `editor_set_node_groups` `editor_find_nodes_in_group` `editor_get_selection` `editor_execute_gdscript` `editor_get_errors` `editor_get_output_log` `editor_get_node_signals` `editor_get_viewport_3d_camera` `editor_set_viewport_3d_camera` `running_game_capture_frames` `running_game_create_input_recording` `running_game_stop_input_recording` `running_game_find_nodes_by_script` `running_game_get_autoload_node` `running_game_get_node_properties_batch` `running_game_find_ui_elements` `running_game_find_nearby_nodes` `running_game_capture_signal_emissions` `editor_get_performance_monitors` `project_list_scripts` `project_read_script` `editor_get_open_scripts` `project_validate_script` `editor_get_input_actions` `editor_find_nodes_by_type` `editor_list_signal_connections` `project_find_files_referencing_symbol` `project_get_scene_dependencies` `editor_list_animations` `editor_create_animation` `editor_add_animation_track` `editor_set_animation_keyframe` `editor_get_animation_info` `editor_get_tilemap_info` `editor_get_tilemap_used_cells` `editor_get_tilemap_cell` `project_read_resource` `project_get_resource_preview` `project_read_shader` `project_get_shader_params` `editor_set_physics_layers` `editor_get_physics_layers` `editor_setup_physics_body` `editor_get_collision_info` `editor_add_audio_player` `editor_get_audio_info` `editor_get_audio_bus_layout` `editor_add_audio_bus` `editor_set_audio_bus_property` `editor_add_audio_bus_effect` `project_get_theme_info` `editor_create_animation_tree` `editor_get_animation_tree_structure` `editor_add_state_machine_state` `editor_remove_state_machine_state` `editor_add_state_machine_transition` `editor_remove_state_machine_transition` `editor_set_blend_tree_node` `editor_set_animation_tree_parameter` `editor_setup_navigation_region` `editor_setup_navigation_agent` `editor_set_navigation_layers` `editor_get_navigation_info` `editor_create_particles` `project_find_unused_resources` `editor_analyze_signal_flow` `project_analyze_scene_complexity` `project_find_script_references` `project_detect_circular_dependencies` `project_get_statistics` `project_validate_scripts` `project_read_text_file`
- **`count_only`**（12）：`editor_connect_signal` `running_game_find_node_when_available` `editor_set_node_script` `editor_remove_animation` `editor_add_mesh_instance` `editor_setup_camera_3d` `editor_setup_lighting` `editor_set_material_3d` `editor_setup_world_environment` `editor_add_gridmap` `editor_set_control_theme` `editor_set_node_script_batch`
- **`no_calls`**（20）：`editor_play_scene` `editor_stop_scene` `editor_set_node_selection` `editor_remove_node_selection` `editor_remove_output_log` `editor_reload_plugin` `editor_rescan_project_filesystem` `editor_analyze_screenshot_diff` `editor_set_auto_dismiss_dialogs` `editor_simulate_key` `editor_simulate_mouse_click` `editor_simulate_mouse_move` `editor_simulate_input_action` `editor_simulate_input_sequence` `project_get_export_info` `project_list_export_presets` `editor_get_test_report` `os_list_android_devices` `project_get_android_preset_info` `os_deploy_to_android_device`

## 0. 分桶与状态

| 桶 | 工具数 |
|---|---|
| `0` 次 | 20 |
| `1-4` 次 | 0 |
| `>=5` 次 | 157 |
| **合计** | **177** |

| 状态 | 工具数 |
|---|---|
| 达标 | 102 |
| 计数达标缺证据 | 55 |
| 未达(1-4) | 0 |
| 未达(0) | 20 |

| scope | 契约条数 | 被调用过 | 0 次 | ≥5 次 |
|---|---|---|---|---|
| both | 50 | 45 | 5 | 45 |
| editor | 104 | 89 | 15 | 89 |
| game | 23 | 23 | 0 | 23 |

## 1. 总表（177 条契约工具，逐条一行）

| # | tool | scope | verb | 累计调用 | 有效调用 | 边界调用 | 证据档位 | 档位证据 | 证据路径 | 状态 |
|---|---|---|---|---|---|---|---|---|---|---|
| 1 | `project_get_info` | both | get | 8 | 6 | 2 | `readback` | own_payload ×6（读类回包即证据） | runs/_exercises/ex_files/c1-task110(6) ; runs/_exercises/ex_files/c1-smoke(2) | 达标 |
| 2 | `project_get_filesystem_tree` | both | get | 6 | 5 | 1 | `readback` | own_payload ×5（读类回包即证据） | runs/_exercises/ex_files/c1-task110(6) | 达标 |
| 3 | `project_search_file_names` | both | search | 12 | 11 | 1 | `readback` | own_payload ×11（读类回包即证据） | runs/_exercises/ex_files/c1-task110(6) ; runs/_exercises/ex_files/c1b-task110(6) | 达标 |
| 4 | `project_search_file_contents` | both | search | 12 | 11 | 1 | `readback` | own_payload ×11（读类回包即证据） | runs/_exercises/ex_files/c1-task110(6) ; runs/_exercises/ex_files/c1b-task110(6) | 达标 |
| 5 | `project_get_settings` | both | get | 7 | 6 | 1 | `readback` | own_payload ×6（读类回包即证据） | runs/_exercises/ex_files/c1-task110(6) ; runs/_exercises/ex_files/c1-smoke(1) | 达标 |
| 6 | `project_set_setting` | both | set | 6 | 5 | 1 | `file_effect` | ok_file_effect_observed ×5 | runs/_exercises/ex_files/c1-task110(6) | 达标 |
| 7 | `project_convert_uid_to_path` | both | convert | 8 | 6 | 2 | `readback` | own_payload ×6（读类回包即证据） | runs/_exercises/ex_files/c1-task110(6) ; runs/_exercises/ex_files/c1-smoke(2) | 达标 |
| 8 | `project_convert_path_to_uid` | both | convert | 6 | 5 | 1 | `readback` | own_payload ×5（读类回包即证据） | runs/_exercises/ex_files/c1-task110(6) | 达标 |
| 9 | `editor_get_scene_tree` | editor | get | 109 | 105 | 4 | `readback` | own_payload ×105（读类回包即证据） | runs/_exercises/ex_write5/c4-v5-task111(7) ; runs/_exercises/ex_scene/c23-task110(6) | 达标 |
| 10 | `project_read_scene_file_content` | both | read | 6 | 5 | 1 | `readback` | own_payload ×5（读类回包即证据） | runs/_exercises/ex_files/c1-task110(6) | 达标 |
| 11 | `editor_open_scene` | editor | open | 80 | 8 | 0 | `pixel_effect` | ok_effect_observed ×8 | runs/breakout/breakout-clean-task097(2) ; runs/pong/pong-clean-task097(2) | 计数达标缺证据 |
| 12 | `project_delete_scene_file` | both | delete | 10 | 8 | 2 | `file_effect` | ok_file_effect_observed ×8 | runs/_exercises/ex_files/c1-task110(6) ; runs/pong/d3-after(2) | 达标 |
| 13 | `editor_add_scene_instance` | editor | add | 30 | 0 | 5 | `readback` | witness `editor_get_scene_tree`@runs/_exercises/ex_write5/c4-v5-task111 seq=132 | runs/_exercises/ex_write/c4-task111(6) ; runs/_exercises/ex_write2/c4b-task111(6) | 计数达标缺证据 |
| 14 | `project_get_scene_exports` | both | get | 6 | 5 | 1 | `readback` | own_payload ×5（读类回包即证据） | runs/_exercises/ex_files/c1-task110(6) | 达标 |
| 15 | `editor_play_scene` | editor | play | 0 | 0 | 0 | `no_calls` | - | - | 未达(0) |
| 16 | `editor_stop_scene` | editor | stop | 0 | 0 | 0 | `no_calls` | - | - | 未达(0) |
| 17 | `editor_save_scene` | editor | save | 123 | 77 | 0 | `file_effect` | ok_file_effect_observed ×77 | runs/lunarlander/ll-task104-r1(3) ; runs/missilecommand/mc-task103-r1(3) | 计数达标缺证据 |
| 18 | `project_create_scene_file` | both | create | 20 | 18 | 2 | `file_effect` | ok_file_effect_observed ×18 | runs/_exercises/ex_files/c1-task110(6) ; runs/_exercises/ex_files/c1c-task110(6) | 达标 |
| 19 | `editor_add_node` | editor | add | 30 | 10 | 5 | `pixel_effect` | ok_effect_observed ×10 | runs/_exercises/ex_write/c4-task111(6) ; runs/_exercises/ex_write2/c4b-task111(6) | 达标 |
| 20 | `editor_delete_node` | editor | delete | 65 | 5 | 0 | `pixel_effect` | ok_effect_observed ×5 | runs/snake/snake-clean-task097(37) ; runs/breakout/breakout-clean-task097(20) | 计数达标缺证据 |
| 21 | `editor_rename_node` | editor | rename | 30 | 0 | 7 | `readback` | witness `editor_get_node_properties`@runs/_exercises/ex_write5/c4-v5-task111 seq=138 | runs/_exercises/ex_write/c4-task111(6) ; runs/_exercises/ex_write2/c4b-task111(6) | 计数达标缺证据 |
| 22 | `editor_set_node_property` | editor | set | 41 | 12 | 0 | `pixel_effect` | ok_effect_observed ×12 | runs/pong/pong-clean-task097(3) ; runs/pong/pong-control-task093(3) | 计数达标缺证据 |
| 23 | `editor_get_node_properties` | editor | get | 74 | 62 | 12 | `readback` | own_payload ×62（读类回包即证据） | runs/breakout/breakout-clean-task097(10) ; runs/pong/pong-clean-task097(9) | 达标 |
| 24 | `editor_duplicate_node` | editor | duplicate | 30 | 5 | 7 | `pixel_effect` | ok_effect_observed ×5 | runs/_exercises/ex_write/c4-task111(6) ; runs/_exercises/ex_write2/c4b-task111(6) | 达标 |
| 25 | `editor_connect_signal` | editor | connect | 39 | 0 | 6 | `count_only` | - | runs/_exercises/ex_write/c4-task111(6) ; runs/_exercises/ex_write2/c4b-task111(6) | 计数达标缺证据 |
| 26 | `editor_disconnect_signal` | editor | disconnect | 6 | 0 | 1 | `readback` | witness `editor_list_signal_connections`@runs/_exercises/ex_write6/c5-task111 seq=13 | runs/_exercises/ex_write6/c5-task111(6) | 计数达标缺证据 |
| 27 | `editor_reparent_node` | editor | reparent | 30 | 3 | 14 | `pixel_effect` | ok_effect_observed ×3 | runs/_exercises/ex_write/c4-task111(6) ; runs/_exercises/ex_write2/c4b-task111(6) | 达标 |
| 28 | `editor_add_resource_to_node_property` | editor | add | 33 | 12 | 20 | `pixel_effect` | ok_effect_observed ×12 | runs/_exercises/ex_write4/c4-final-task111(7) ; runs/_exercises/ex_write5/c4-v5-task111(7) | 达标 |
| 29 | `editor_set_anchor_preset` | editor | set | 24 | 5 | 5 | `pixel_effect` | ok_effect_observed ×5 | runs/_exercises/ex_write/c4-task111(6) ; runs/_exercises/ex_write3/c4c-task111(6) | 达标 |
| 30 | `editor_get_node_groups` | editor | get | 13 | 11 | 2 | `readback` | own_payload ×11（读类回包即证据） | runs/_exercises/ex_scene/c23-task110(6) ; runs/_exercises/ex_scene2/c23-after-task110(6) | 达标 |
| 31 | `editor_set_node_groups` | editor | set | 36 | 0 | 11 | `readback` | witness `editor_get_node_groups`@runs/_exercises/ex_write5/c4-v5-task111 seq=143 | runs/_exercises/ex_write/c4-task111(7) ; runs/_exercises/ex_write3/c4c-task111(7) | 计数达标缺证据 |
| 32 | `editor_find_nodes_in_group` | editor | find | 12 | 10 | 2 | `readback` | own_payload ×10（读类回包即证据） | runs/_exercises/ex_scene/c23-task110(6) ; runs/_exercises/ex_scene2/c23-after-task110(6) | 达标 |
| 33 | `editor_get_selection` | editor | get | 12 | 10 | 2 | `readback` | own_payload ×10（读类回包即证据） | runs/_exercises/ex_scene/c23-task110(6) ; runs/_exercises/ex_scene2/c23-after-task110(6) | 达标 |
| 34 | `editor_set_node_selection` | editor | set | 0 | 0 | 0 | `no_calls` | - | - | 未达(0) |
| 35 | `editor_remove_node_selection` | editor | remove | 0 | 0 | 0 | `no_calls` | - | - | 未达(0) |
| 36 | `editor_execute_gdscript` | editor | execute | 12 | 10 | 2 | `readback` | own_payload ×10（读类回包即证据） | runs/_exercises/ex_scene/c23-task110(6) ; runs/_exercises/ex_scene2/c23-after-task110(6) | 达标 |
| 37 | `editor_get_errors` | editor | get | 50 | 50 | 0 | `readback` | own_payload ×50（读类回包即证据） | runs/asteroids/ast-task098-r1(1) ; runs/asteroids/ast-task098-r2(1) | 计数达标缺证据 |
| 38 | `editor_get_output_log` | editor | get | 36 | 32 | 4 | `readback` | own_payload ×32（读类回包即证据） | runs/_exercises/ex_scene/c23-task110(6) ; runs/_exercises/ex_scene2/c23-after-task110(6) | 达标 |
| 39 | `editor_capture_screenshot` | editor | capture | 25 | 25 | 0 | `file_effect` | ok_file_effect_observed ×15 | runs/breakout/breakout-clean-task097(1) ; runs/breakout/breakout-task093(1) | 计数达标缺证据 |
| 40 | `running_game_capture_screenshot` | game | capture | 298 | 298 | 0 | `pixel_effect` | ok_effect_observed ×1 | runs/match3/m3-task102-r1(7) ; runs/match3/m3-task102-r2(7) | 计数达标缺证据 |
| 41 | `editor_remove_output_log` | editor | remove | 0 | 0 | 0 | `no_calls` | - | - | 未达(0) |
| 42 | `editor_reload_plugin` | editor | reload | 0 | 0 | 0 | `no_calls` | - | - | 未达(0) |
| 43 | `editor_rescan_project_filesystem` | editor | rescan | 0 | 0 | 0 | `no_calls` | - | - | 未达(0) |
| 44 | `editor_get_node_signals` | editor | get | 12 | 10 | 2 | `readback` | own_payload ×10（读类回包即证据） | runs/_exercises/ex_scene/c23-task110(6) ; runs/_exercises/ex_scene2/c23-after-task110(6) | 达标 |
| 45 | `editor_analyze_screenshot_diff` | editor | analyze | 0 | 0 | 0 | `no_calls` | - | - | 未达(0) |
| 46 | `editor_set_auto_dismiss_dialogs` | editor | set | 0 | 0 | 0 | `no_calls` | - | - | 未达(0) |
| 47 | `editor_get_viewport_3d_camera` | editor | get | 6 | 5 | 1 | `readback` | own_payload ×5（读类回包即证据） | runs/_exercises/ex_3d/h1-task111(6) | 达标 |
| 48 | `editor_set_viewport_3d_camera` | editor | set | 6 | 0 | 1 | `readback` | witness `editor_get_viewport_3d_camera`@runs/_exercises/ex_3d/h1-task111 seq=27 | runs/_exercises/ex_3d/h1-task111(6) | 计数达标缺证据 |
| 49 | `running_game_get_scene_tree` | game | get | 123 | 123 | 0 | `pixel_effect` | ok_effect_observed ×1 | runs/asteroids/ast-task098-r1(2) ; runs/asteroids/ast-task098-r2(2) | 计数达标缺证据 |
| 50 | `running_game_get_node_properties` | game | get | 58 | 56 | 2 | `pixel_effect` | ok_effect_observed ×8 | runs/_exercises/ex_scene/c23-task110(6) ; runs/_exercises/ex_scene2/c23-after-task110(6) | 达标 |
| 51 | `running_game_set_node_property` | game | set | 49 | 28 | 2 | `pixel_effect` | ok_effect_observed ×28 | runs/pong/pong-clean-task097(5) ; runs/pong/pong-control-task093(5) | 达标 |
| 52 | `running_game_capture_frames` | game | capture | 36 | 30 | 6 | `readback` | own_payload ×30（读类回包即证据） | runs/_exercises/ex_scene/c23-task110(6) ; runs/_exercises/ex_scene2/c23-after-task110(6) | 达标 |
| 53 | `running_game_get_node_property_samples` | game | get | 122 | 122 | 0 | `pixel_effect` | ok_effect_observed ×35 | runs/spaceinvaders/si-task097-r1(5) ; runs/tetris/tetris-task096(4) | 计数达标缺证据 |
| 54 | `running_game_execute_gdscript` | game | execute | 1626 | 1593 | 33 | `pixel_effect` | ok_effect_observed ×873 | runs/rtype/rt-task104-r1(98) ; runs/rtype/rt-task104-r2(98) | 达标 |
| 55 | `running_game_create_input_recording` | game | create | 7 | 0 | 1 | `readback` | witness `running_game_stop_input_recording`@runs/_exercises/ex_rec/h9-task113 seq=5 | runs/_exercises/ex_rec/h9-task113(7) | 计数达标缺证据 |
| 56 | `running_game_stop_input_recording` | game | stop | 7 | 0 | 0 | `readback` | witness `running_game_get_node_properties`@runs/_exercises/ex_rec/h9-task113 seq=2 | runs/_exercises/ex_rec/h9-task113(7) | 计数达标缺证据 |
| 57 | `running_game_play_input_recording` | game | play | 7 | 6 | 1 | `pixel_effect` | ok_effect_observed ×6 | runs/_exercises/ex_rec/h9-task113(7) | 达标 |
| 58 | `running_game_find_nodes_by_script` | game | find | 12 | 10 | 2 | `readback` | own_payload ×10（读类回包即证据） | runs/_exercises/ex_scene/c23-task110(6) ; runs/_exercises/ex_scene2/c23-after-task110(6) | 达标 |
| 59 | `running_game_get_autoload_node` | game | get | 12 | 10 | 2 | `readback` | own_payload ×10（读类回包即证据） | runs/_exercises/ex_scene/c23-task110(6) ; runs/_exercises/ex_scene2/c23-after-task110(6) | 达标 |
| 60 | `running_game_get_node_properties_batch` | game | get | 36 | 32 | 4 | `readback` | own_payload ×32（读类回包即证据） | runs/_exercises/ex_scene/c23-task110(6) ; runs/_exercises/ex_scene2/c23-after-task110(6) | 达标 |
| 61 | `running_game_find_ui_elements` | game | find | 12 | 10 | 2 | `readback` | own_payload ×10（读类回包即证据） | runs/_exercises/ex_scene/c23-task110(6) ; runs/_exercises/ex_scene2/c23-after-task110(6) | 达标 |
| 62 | `running_game_simulate_button_click_by_text` | game | simulate | 12 | 2 | 2 | `pixel_effect` | ok_effect_observed ×2 | runs/_exercises/ex_scene/c23-task110(6) ; runs/_exercises/ex_scene2/c23-after-task110(6) | 达标 |
| 63 | `running_game_find_node_when_available` | game | find | 8 | 0 | 8 | `count_only` | - | runs/breakout/breakout-clean-task097(1) ; runs/breakout/breakout-task093(1) | 计数达标缺证据 |
| 64 | `running_game_find_nearby_nodes` | game | find | 12 | 10 | 2 | `readback` | own_payload ×10（读类回包即证据） | runs/_exercises/ex_scene/c23-task110(6) ; runs/_exercises/ex_scene2/c23-after-task110(6) | 达标 |
| 65 | `running_game_move_player_to_target` | game | move | 6 | 5 | 1 | `pixel_effect` | ok_effect_observed ×5 | runs/_exercises/ex_nav/h4-task113(6) | 达标 |
| 66 | `running_game_capture_signal_emissions` | game | capture | 36 | 26 | 10 | `readback` | own_payload ×26（读类回包即证据） | runs/_exercises/ex_scene/c23-task110(6) ; runs/_exercises/ex_scene2/c23-after-task110(6) | 达标 |
| 67 | `editor_get_performance_monitors` | editor | get | 12 | 10 | 2 | `readback` | own_payload ×10（读类回包即证据） | runs/_exercises/ex_scene/c23-task110(6) ; runs/_exercises/ex_scene2/c23-after-task110(6) | 达标 |
| 68 | `project_list_scripts` | both | list | 6 | 5 | 1 | `readback` | own_payload ×5（读类回包即证据） | runs/_exercises/ex_files/c1-task110(6) | 达标 |
| 69 | `project_read_script` | both | read | 8 | 6 | 2 | `readback` | own_payload ×6（读类回包即证据） | runs/_exercises/ex_files/c1-task110(6) ; runs/_exercises/ex_files/c1-smoke(2) | 达标 |
| 70 | `project_create_script` | both | create | 76 | 43 | 1 | `file_effect` | ok_file_effect_observed ×43 | runs/_exercises/ex_files/c1-task110(6) ; runs/_exercises/ex_files/c1b-task110(6) | 达标 |
| 71 | `project_edit_script` | both | edit | 60 | 52 | 0 | `file_effect` | ok_file_effect_observed ×52 | runs/tetris/tetris-task096-r2(2) ; runs/asteroids/ast-task098-r1(1) | 计数达标缺证据 |
| 72 | `editor_set_node_script` | editor | set | 30 | 0 | 5 | `count_only` | - | runs/_exercises/ex_write/c4-task111(6) ; runs/_exercises/ex_write2/c4b-task111(6) | 计数达标缺证据 |
| 73 | `editor_get_open_scripts` | editor | get | 12 | 10 | 2 | `readback` | own_payload ×10（读类回包即证据） | runs/_exercises/ex_scene/c23-task110(6) ; runs/_exercises/ex_scene2/c23-after-task110(6) | 达标 |
| 74 | `project_validate_script` | both | validate | 18 | 3 | 15 | `readback` | own_payload ×3（读类回包即证据） | runs/_exercises/ex_files/c1-task110(6) ; runs/_exercises/ex_files/c1b-task110(6) | 达标 |
| 75 | `editor_simulate_key` | editor | simulate | 0 | 0 | 0 | `no_calls` | - | - | 未达(0) |
| 76 | `editor_simulate_mouse_click` | editor | simulate | 0 | 0 | 0 | `no_calls` | - | - | 未达(0) |
| 77 | `editor_simulate_mouse_move` | editor | simulate | 0 | 0 | 0 | `no_calls` | - | - | 未达(0) |
| 78 | `editor_simulate_input_action` | editor | simulate | 0 | 0 | 0 | `no_calls` | - | - | 未达(0) |
| 79 | `editor_get_input_actions` | editor | get | 12 | 10 | 2 | `readback` | own_payload ×10（读类回包即证据） | runs/_exercises/ex_scene/c23-task110(6) ; runs/_exercises/ex_scene2/c23-after-task110(6) | 达标 |
| 80 | `editor_add_input_action` | editor | add | 189 | 122 | 0 | `file_effect` | ok_file_effect_observed ×122 | runs/pong/pong-clean-task097(5) ; runs/pong/pong-control-task093(5) | 计数达标缺证据 |
| 81 | `editor_simulate_input_sequence` | editor | simulate | 0 | 0 | 0 | `no_calls` | - | - | 未达(0) |
| 82 | `editor_find_nodes_by_type` | editor | find | 12 | 10 | 2 | `readback` | own_payload ×10（读类回包即证据） | runs/_exercises/ex_scene/c23-task110(6) ; runs/_exercises/ex_scene2/c23-after-task110(6) | 达标 |
| 83 | `editor_set_node_property_batch` | editor | set | 30 | 15 | 5 | `pixel_effect` | ok_effect_observed ×15 | runs/_exercises/ex_write/c4-task111(6) ; runs/_exercises/ex_write2/c4b-task111(6) | 达标 |
| 84 | `editor_list_signal_connections` | editor | list | 13 | 9 | 4 | `readback` | own_payload ×9（读类回包即证据） | runs/_exercises/ex_scene/c23-task110(6) ; runs/_exercises/ex_scene2/c23-after-task110(6) | 达标 |
| 85 | `editor_add_nodes_batch` | editor | add | 106 | 47 | 42 | `pixel_effect` | ok_effect_observed ×47 | runs/pong/d3-after(3) ; runs/pong/d3-after-r2(3) | 达标 |
| 86 | `project_find_files_referencing_symbol` | both | find | 12 | 11 | 1 | `readback` | own_payload ×11（读类回包即证据） | runs/_exercises/ex_files/c1-task110(6) ; runs/_exercises/ex_files/c1b-task110(6) | 达标 |
| 87 | `project_get_scene_dependencies` | both | get | 6 | 5 | 1 | `readback` | own_payload ×5（读类回包即证据） | runs/_exercises/ex_files/c1-task110(6) | 达标 |
| 88 | `project_set_node_property_across_scenes` | both | set | 18 | 1 | 1 | `file_effect` | ok_file_effect_observed ×1 | runs/_exercises/ex_files/c1-task110(6) ; runs/_exercises/ex_files/c1b-task110(6) | 达标 |
| 89 | `editor_list_animations` | editor | list | 12 | 10 | 2 | `readback` | own_payload ×10（读类回包即证据） | runs/_exercises/ex_anim/h2-task111(6) ; runs/_exercises/ex_anim2/h2b-task111(6) | 达标 |
| 90 | `editor_create_animation` | editor | create | 18 | 0 | 2 | `readback` | witness `editor_list_animations`@runs/_exercises/ex_anim2/h2b-task111 seq=23 | runs/_exercises/ex_anim/h2-task111(9) ; runs/_exercises/ex_anim2/h2b-task111(9) | 计数达标缺证据 |
| 91 | `editor_add_animation_track` | editor | add | 12 | 0 | 2 | `readback` | witness `editor_get_animation_info`@runs/_exercises/ex_anim2/h2b-task111 seq=29 | runs/_exercises/ex_anim/h2-task111(6) ; runs/_exercises/ex_anim2/h2b-task111(6) | 计数达标缺证据 |
| 92 | `editor_set_animation_keyframe` | editor | set | 12 | 0 | 2 | `readback` | witness `editor_get_animation_info`@runs/_exercises/ex_anim2/h2b-task111 seq=29 | runs/_exercises/ex_anim/h2-task111(6) ; runs/_exercises/ex_anim2/h2b-task111(6) | 计数达标缺证据 |
| 93 | `editor_get_animation_info` | editor | get | 12 | 10 | 2 | `readback` | own_payload ×10（读类回包即证据） | runs/_exercises/ex_anim/h2-task111(6) ; runs/_exercises/ex_anim2/h2b-task111(6) | 达标 |
| 94 | `editor_remove_animation` | editor | remove | 12 | 0 | 2 | `count_only` | - | runs/_exercises/ex_anim/h2-task111(6) ; runs/_exercises/ex_anim2/h2b-task111(6) | 计数达标缺证据 |
| 95 | `editor_get_tilemap_info` | editor | get | 6 | 5 | 1 | `readback` | own_payload ×5（读类回包即证据） | runs/_exercises/ex_grid/h3-task111(6) | 达标 |
| 96 | `editor_get_tilemap_used_cells` | editor | get | 6 | 5 | 1 | `readback` | own_payload ×5（读类回包即证据） | runs/_exercises/ex_grid/h3-task111(6) | 达标 |
| 97 | `editor_remove_all_tilemap_cells` | editor | remove | 6 | 5 | 1 | `pixel_effect` | ok_effect_observed ×5 | runs/_exercises/ex_grid/h3-task111(6) | 达标 |
| 98 | `editor_set_tilemap_cell` | editor | set | 10 | 9 | 1 | `pixel_effect` | ok_effect_observed ×9 | runs/_exercises/ex_grid/h3-task111(10) | 达标 |
| 99 | `editor_set_tilemap_cells_in_rect` | editor | set | 6 | 5 | 1 | `pixel_effect` | ok_effect_observed ×5 | runs/_exercises/ex_grid/h3-task111(6) | 达标 |
| 100 | `editor_get_tilemap_cell` | editor | get | 6 | 5 | 1 | `readback` | own_payload ×5（读类回包即证据） | runs/_exercises/ex_grid/h3-task111(6) | 达标 |
| 101 | `project_read_resource` | both | read | 6 | 5 | 1 | `readback` | own_payload ×5（读类回包即证据） | runs/_exercises/ex_files/c1-task110(6) | 达标 |
| 102 | `project_add_autoload` | both | add | 8 | 7 | 1 | `file_effect` | ok_file_effect_observed ×7 | runs/_exercises/ex_files/c1-task110(6) ; runs/_exercises/ex_scene/c23-task110(1) | 达标 |
| 103 | `project_remove_autoload` | both | remove | 6 | 5 | 1 | `file_effect` | ok_file_effect_observed ×5 | runs/_exercises/ex_files/c1-task110(6) | 达标 |
| 104 | `project_edit_resource` | both | edit | 6 | 5 | 1 | `file_effect` | ok_file_effect_observed ×5 | runs/_exercises/ex_files/c1-task110(6) | 达标 |
| 105 | `project_create_resource` | both | create | 7 | 6 | 1 | `file_effect` | ok_file_effect_observed ×6 | runs/_exercises/ex_files/c1-task110(6) ; runs/_exercises/ex_3d/h1-task111(1) | 达标 |
| 106 | `project_get_resource_preview` | both | get | 12 | 5 | 7 | `readback` | own_payload ×5（读类回包即证据） | runs/_exercises/ex_files/c1-task110(6) ; runs/_exercises/ex_files/c1b-task110(6) | 达标 |
| 107 | `project_get_export_info` | both | get | 0 | 0 | 0 | `no_calls` | - | - | 未达(0) |
| 108 | `project_list_export_presets` | both | list | 0 | 0 | 0 | `no_calls` | - | - | 未达(0) |
| 109 | `project_read_shader` | both | read | 7 | 6 | 1 | `readback` | own_payload ×6（读类回包即证据） | runs/_exercises/ex_files/c1-task110(6) ; runs/_exercises/ex_files/c1-smoke(1) | 达标 |
| 110 | `project_create_shader` | both | create | 12 | 11 | 1 | `file_effect` | ok_file_effect_observed ×11 | runs/_exercises/ex_files/c1-task110(6) ; runs/_exercises/ex_files/c1-smoke(1) | 达标 |
| 111 | `project_edit_shader` | both | edit | 8 | 7 | 1 | `file_effect` | ok_file_effect_observed ×7 | runs/_exercises/ex_files/c1-task110(6) ; runs/_exercises/ex_write4/c4-final-task111(1) | 达标 |
| 112 | `editor_set_shader_material` | editor | set | 24 | 3 | 6 | `pixel_effect` | ok_effect_observed ×3 | runs/_exercises/ex_write/c4-task111(6) ; runs/_exercises/ex_write3/c4c-task111(6) | 达标 |
| 113 | `editor_set_shader_param` | editor | set | 24 | 1 | 14 | `pixel_effect` | ok_effect_observed ×1 | runs/_exercises/ex_write/c4-task111(6) ; runs/_exercises/ex_write3/c4c-task111(6) | 达标 |
| 114 | `project_get_shader_params` | both | get | 6 | 5 | 1 | `readback` | own_payload ×5（读类回包即证据） | runs/_exercises/ex_files/c1-task110(6) | 达标 |
| 115 | `editor_add_raycast` | editor | add | 36 | 16 | 11 | `pixel_effect` | ok_effect_observed ×16 | runs/_exercises/ex_write3/c4c-task111(7) ; runs/_exercises/ex_write4/c4-final-task111(7) | 达标 |
| 116 | `editor_setup_collision_shape` | editor | setup | 31 | 9 | 11 | `pixel_effect` | ok_effect_observed ×9 | runs/_exercises/ex_write/c4-task111(7) ; runs/_exercises/ex_write3/c4c-task111(7) | 达标 |
| 117 | `editor_set_physics_layers` | editor | set | 24 | 0 | 6 | `readback` | witness `editor_get_node_properties`@runs/_exercises/ex_write5/c4-v5-task111 seq=139 | runs/_exercises/ex_write/c4-task111(6) ; runs/_exercises/ex_write3/c4c-task111(6) | 计数达标缺证据 |
| 118 | `editor_get_physics_layers` | editor | get | 12 | 6 | 6 | `readback` | own_payload ×6（读类回包即证据） | runs/_exercises/ex_scene/c23-task110(6) ; runs/_exercises/ex_scene2/c23-after-task110(6) | 达标 |
| 119 | `editor_setup_physics_body` | editor | setup | 24 | 0 | 7 | `readback` | witness `editor_get_scene_tree`@runs/_exercises/ex_write5/c4-v5-task111 seq=132 | runs/_exercises/ex_write/c4-task111(6) ; runs/_exercises/ex_write3/c4c-task111(6) | 计数达标缺证据 |
| 120 | `editor_get_collision_info` | editor | get | 12 | 8 | 4 | `readback` | own_payload ×8（读类回包即证据） | runs/_exercises/ex_scene/c23-task110(6) ; runs/_exercises/ex_scene2/c23-after-task110(6) | 达标 |
| 121 | `editor_add_mesh_instance` | editor | add | 6 | 0 | 1 | `count_only` | - | runs/_exercises/ex_3d/h1-task111(6) | 计数达标缺证据 |
| 122 | `editor_setup_camera_3d` | editor | setup | 6 | 0 | 1 | `count_only` | - | runs/_exercises/ex_3d/h1-task111(6) | 计数达标缺证据 |
| 123 | `editor_setup_lighting` | editor | setup | 6 | 0 | 1 | `count_only` | - | runs/_exercises/ex_3d/h1-task111(6) | 计数达标缺证据 |
| 124 | `editor_set_material_3d` | editor | set | 6 | 0 | 3 | `count_only` | - | runs/_exercises/ex_3d/h1-task111(6) | 计数达标缺证据 |
| 125 | `editor_setup_world_environment` | editor | setup | 6 | 0 | 1 | `count_only` | - | runs/_exercises/ex_3d/h1-task111(6) | 计数达标缺证据 |
| 126 | `editor_add_gridmap` | editor | add | 6 | 0 | 1 | `count_only` | - | runs/_exercises/ex_grid/h3-task111(6) | 计数达标缺证据 |
| 127 | `editor_add_audio_player` | editor | add | 6 | 0 | 1 | `readback` | witness `editor_get_node_properties`@runs/_exercises/ex_audio/h5-task113 seq=42 | runs/_exercises/ex_audio/h5-task113(6) | 计数达标缺证据 |
| 128 | `editor_get_audio_info` | editor | get | 6 | 5 | 1 | `readback` | own_payload ×5（读类回包即证据） | runs/_exercises/ex_audio/h5-task113(6) | 达标 |
| 129 | `editor_get_audio_bus_layout` | editor | get | 7 | 6 | 1 | `readback` | own_payload ×6（读类回包即证据） | runs/_exercises/ex_audio/h5-task113(7) | 达标 |
| 130 | `editor_add_audio_bus` | editor | add | 7 | 0 | 2 | `readback` | witness `editor_get_audio_bus_layout`@runs/_exercises/ex_audio/h5-task113 seq=22 | runs/_exercises/ex_audio/h5-task113(7) | 计数达标缺证据 |
| 131 | `editor_set_audio_bus_property` | editor | set | 8 | 0 | 3 | `readback` | witness `editor_get_audio_bus_layout`@runs/_exercises/ex_audio/h5-task113 seq=43 | runs/_exercises/ex_audio/h5-task113(8) | 计数达标缺证据 |
| 132 | `editor_add_audio_bus_effect` | editor | add | 7 | 0 | 2 | `readback` | witness `editor_get_audio_bus_layout`@runs/_exercises/ex_audio/h5-task113 seq=22 | runs/_exercises/ex_audio/h5-task113(7) | 计数达标缺证据 |
| 133 | `project_create_theme` | both | create | 11 | 10 | 1 | `file_effect` | ok_file_effect_observed ×10 | runs/_exercises/ex_files/c1-task110(6) ; runs/_exercises/ex_write/c4-task111(1) | 达标 |
| 134 | `project_set_theme_color` | both | set | 6 | 5 | 1 | `file_effect` | ok_file_effect_observed ×5 | runs/_exercises/ex_files/c1-task110(6) | 达标 |
| 135 | `project_set_theme_constant` | both | set | 6 | 5 | 1 | `file_effect` | ok_file_effect_observed ×5 | runs/_exercises/ex_files/c1-task110(6) | 达标 |
| 136 | `project_set_theme_font_size` | both | set | 6 | 5 | 1 | `file_effect` | ok_file_effect_observed ×5 | runs/_exercises/ex_files/c1-task110(6) | 达标 |
| 137 | `project_set_theme_stylebox` | both | set | 6 | 5 | 1 | `file_effect` | ok_file_effect_observed ×5 | runs/_exercises/ex_files/c1-task110(6) | 达标 |
| 138 | `editor_set_control_theme` | editor | set | 24 | 0 | 5 | `count_only` | - | runs/_exercises/ex_write/c4-task111(6) ; runs/_exercises/ex_write3/c4c-task111(6) | 计数达标缺证据 |
| 139 | `project_get_theme_info` | both | get | 6 | 5 | 1 | `readback` | own_payload ×5（读类回包即证据） | runs/_exercises/ex_files/c1-task110(6) | 达标 |
| 140 | `editor_create_animation_tree` | editor | create | 12 | 0 | 2 | `readback` | witness `editor_get_animation_tree_structure`@runs/_exercises/ex_anim2/h2b-task111 seq=88 | runs/_exercises/ex_anim/h2-task111(6) ; runs/_exercises/ex_anim2/h2b-task111(6) | 计数达标缺证据 |
| 141 | `editor_get_animation_tree_structure` | editor | get | 12 | 10 | 2 | `readback` | own_payload ×10（读类回包即证据） | runs/_exercises/ex_anim/h2-task111(6) ; runs/_exercises/ex_anim2/h2b-task111(6) | 达标 |
| 142 | `editor_add_state_machine_state` | editor | add | 18 | 0 | 2 | `readback` | witness `editor_get_animation_tree_structure`@runs/_exercises/ex_anim2/h2b-task111 seq=88 | runs/_exercises/ex_anim2/h2b-task111(12) ; runs/_exercises/ex_anim/h2-task111(6) | 计数达标缺证据 |
| 143 | `editor_remove_state_machine_state` | editor | remove | 12 | 0 | 7 | `readback` | witness `editor_get_animation_tree_structure`@runs/_exercises/ex_anim2/h2b-task111 seq=91 | runs/_exercises/ex_anim/h2-task111(6) ; runs/_exercises/ex_anim2/h2b-task111(6) | 计数达标缺证据 |
| 144 | `editor_add_state_machine_transition` | editor | add | 22 | 0 | 2 | `readback` | witness `editor_get_animation_tree_structure`@runs/_exercises/ex_anim2/h2b-task111 seq=88 | runs/_exercises/ex_anim/h2-task111(11) ; runs/_exercises/ex_anim2/h2b-task111(11) | 计数达标缺证据 |
| 145 | `editor_remove_state_machine_transition` | editor | remove | 12 | 0 | 2 | `readback` | witness `editor_get_animation_tree_structure`@runs/_exercises/ex_anim2/h2b-task111 seq=88 | runs/_exercises/ex_anim/h2-task111(6) ; runs/_exercises/ex_anim2/h2b-task111(6) | 计数达标缺证据 |
| 146 | `editor_set_blend_tree_node` | editor | set | 12 | 0 | 7 | `readback` | witness `editor_get_animation_tree_structure`@runs/_exercises/ex_anim2/h2b-task111 seq=88 | runs/_exercises/ex_anim/h2-task111(6) ; runs/_exercises/ex_anim2/h2b-task111(6) | 计数达标缺证据 |
| 147 | `editor_set_animation_tree_parameter` | editor | set | 12 | 0 | 4 | `readback` | witness `editor_get_animation_tree_structure`@runs/_exercises/ex_anim2/h2b-task111 seq=88 | runs/_exercises/ex_anim/h2-task111(6) ; runs/_exercises/ex_anim2/h2b-task111(6) | 计数达标缺证据 |
| 148 | `editor_setup_navigation_region` | editor | setup | 6 | 0 | 1 | `readback` | witness `editor_get_navigation_info`@runs/_exercises/ex_nav/h4-task113 seq=27 | runs/_exercises/ex_nav/h4-task113(6) | 计数达标缺证据 |
| 149 | `editor_bake_navigation_mesh` | editor | bake | 6 | 1 | 1 | `pixel_effect` | ok_effect_observed ×1 | runs/_exercises/ex_nav/h4-task113(6) | 达标 |
| 150 | `editor_setup_navigation_agent` | editor | setup | 6 | 0 | 1 | `readback` | witness `editor_get_navigation_info`@runs/_exercises/ex_nav/h4-task113 seq=27 | runs/_exercises/ex_nav/h4-task113(6) | 计数达标缺证据 |
| 151 | `editor_set_navigation_layers` | editor | set | 7 | 0 | 2 | `readback` | witness `editor_get_navigation_info`@runs/_exercises/ex_nav/h4-task113 seq=27 | runs/_exercises/ex_nav/h4-task113(7) | 计数达标缺证据 |
| 152 | `editor_get_navigation_info` | editor | get | 6 | 5 | 1 | `readback` | own_payload ×5（读类回包即证据） | runs/_exercises/ex_nav/h4-task113(6) | 达标 |
| 153 | `editor_create_particles` | editor | create | 8 | 0 | 3 | `readback` | witness `editor_get_particle_info`@runs/_exercises/ex_particles/h6-task113 seq=34 | runs/_exercises/ex_particles/h6-task113(8) | 计数达标缺证据 |
| 154 | `editor_set_particle_material` | editor | set | 8 | 5 | 3 | `pixel_effect` | ok_effect_observed ×5 | runs/_exercises/ex_particles/h6-task113(8) | 达标 |
| 155 | `editor_set_particle_color_gradient` | editor | set | 9 | 6 | 3 | `pixel_effect` | ok_effect_observed ×6 | runs/_exercises/ex_particles/h6-task113(9) | 达标 |
| 156 | `editor_set_particle_preset` | editor | set | 7 | 5 | 2 | `pixel_effect` | ok_effect_observed ×5 | runs/_exercises/ex_particles/h6-task113(7) | 达标 |
| 157 | `editor_get_particle_info` | editor | get | 7 | 6 | 1 | `pixel_effect` | ok_effect_observed ×6 | runs/_exercises/ex_particles/h6-task113(7) | 达标 |
| 158 | `project_find_unused_resources` | both | find | 6 | 5 | 1 | `readback` | own_payload ×5（读类回包即证据） | runs/_exercises/ex_files/c1-task110(6) | 达标 |
| 159 | `editor_analyze_signal_flow` | editor | analyze | 12 | 8 | 4 | `readback` | own_payload ×8（读类回包即证据） | runs/_exercises/ex_scene/c23-task110(6) ; runs/_exercises/ex_scene2/c23-after-task110(6) | 达标 |
| 160 | `project_analyze_scene_complexity` | both | analyze | 6 | 5 | 1 | `readback` | own_payload ×5（读类回包即证据） | runs/_exercises/ex_files/c1-task110(6) | 达标 |
| 161 | `project_find_script_references` | both | find | 12 | 11 | 1 | `readback` | own_payload ×11（读类回包即证据） | runs/_exercises/ex_files/c1-task110(6) ; runs/_exercises/ex_files/c1b-task110(6) | 达标 |
| 162 | `project_detect_circular_dependencies` | both | detect | 6 | 5 | 1 | `readback` | own_payload ×5（读类回包即证据） | runs/_exercises/ex_files/c1-task110(6) | 达标 |
| 163 | `project_get_statistics` | both | get | 7 | 5 | 2 | `readback` | own_payload ×5（读类回包即证据） | runs/_exercises/ex_files/c1-task110(6) ; runs/_exercises/ex_files/c1-smoke(1) | 达标 |
| 164 | `running_game_run_test_scenario` | game | run | 185 | 131 | 0 | `pixel_effect` | ok_effect_observed ×1 | runs/snake/snake-clean-task097(8) ; runs/snake/snake-task093(8) | 计数达标缺证据 |
| 165 | `running_game_assert_node_state` | game | assert | 2903 | 2719 | 115 | `file_effect` | ok_file_effect_observed ×2788 | runs/lunarlander/ll-task104-r1(149) ; runs/bomberman/bomb-task101-r4(144) | 达标 |
| 166 | `running_game_assert_screen_text` | game | assert | 80 | 65 | 0 | `file_effect` | ok_file_effect_observed ×80 | runs/asteroids/ast-task098-r1(2) ; runs/asteroids/ast-task098-r2(2) | 计数达标缺证据 |
| 167 | `running_game_run_stress_test` | game | run | 27 | 5 | 0 | `pixel_effect` | ok_effect_observed ×5 | runs/breakout/breakout-clean-task097(1) ; runs/breakout/breakout-task093(1) | 计数达标缺证据 |
| 168 | `editor_get_test_report` | editor | get | 0 | 0 | 0 | `no_calls` | - | - | 未达(0) |
| 169 | `os_list_android_devices` | both | list | 0 | 0 | 0 | `no_calls` | - | - | 未达(0) |
| 170 | `project_get_android_preset_info` | both | get | 0 | 0 | 0 | `no_calls` | - | - | 未达(0) |
| 171 | `os_deploy_to_android_device` | both | deploy | 0 | 0 | 0 | `no_calls` | - | - | 未达(0) |
| 172 | `project_build_csharp` | both | build | 66 | 62 | 0 | `file_effect` | ok_file_effect_observed ×62 | runs/_exercises/ex_files/c1b-task110(1) ; runs/_exercises/ex_scene/c23-task110(1) | 计数达标缺证据 |
| 173 | `project_write_text_file` | both | write | 7 | 6 | 1 | `file_effect` | ok_file_effect_observed ×6 | runs/_exercises/ex_files/c1-task110(6) ; runs/_exercises/ex_files/c1-smoke(1) | 达标 |
| 174 | `project_validate_scripts` | both | validate | 84 | 80 | 0 | `readback` | own_payload ×80（读类回包即证据） | runs/breakout/breakout-clean-task097(2) ; runs/breakout/breakout-task093(2) | 计数达标缺证据 |
| 175 | `editor_set_node_script_batch` | editor | set | 50 | 0 | 0 | `count_only` | - | runs/breakout/breakout-clean-task097(2) ; runs/breakout/breakout-task093(2) | 计数达标缺证据 |
| 176 | `editor_set_node_property_updates` | editor | set | 30 | 3 | 7 | `pixel_effect` | ok_effect_observed ×3 | runs/_exercises/ex_write/c4-task111(6) ; runs/_exercises/ex_write2/c4b-task111(6) | 达标 |
| 177 | `project_read_text_file` | both | read | 86 | 85 | 1 | `readback` | own_payload ×85（读类回包即证据） | runs/_exercises/ex_files/c1-task110(6) ; runs/pong/d3-after(3) | 达标 |

## 2. 分桶明细

### 2.1 `>=5` 次（157 条）

| tool | scope | 累计 | 有效 | 边界 | 档位 | 状态 | 证据 |
|---|---|---|---|---|---|---|---|
| `project_get_info` | both | 8 | 6 | 2 | `readback` | 达标 | runs/_exercises/ex_files/c1-task110(6) ; runs/_exercises/ex_files/c1-smoke(2) |
| `project_get_filesystem_tree` | both | 6 | 5 | 1 | `readback` | 达标 | runs/_exercises/ex_files/c1-task110(6) |
| `project_search_file_names` | both | 12 | 11 | 1 | `readback` | 达标 | runs/_exercises/ex_files/c1-task110(6) ; runs/_exercises/ex_files/c1b-task110(6) |
| `project_search_file_contents` | both | 12 | 11 | 1 | `readback` | 达标 | runs/_exercises/ex_files/c1-task110(6) ; runs/_exercises/ex_files/c1b-task110(6) |
| `project_get_settings` | both | 7 | 6 | 1 | `readback` | 达标 | runs/_exercises/ex_files/c1-task110(6) ; runs/_exercises/ex_files/c1-smoke(1) |
| `project_set_setting` | both | 6 | 5 | 1 | `file_effect` | 达标 | runs/_exercises/ex_files/c1-task110(6) |
| `project_convert_uid_to_path` | both | 8 | 6 | 2 | `readback` | 达标 | runs/_exercises/ex_files/c1-task110(6) ; runs/_exercises/ex_files/c1-smoke(2) |
| `project_convert_path_to_uid` | both | 6 | 5 | 1 | `readback` | 达标 | runs/_exercises/ex_files/c1-task110(6) |
| `editor_get_scene_tree` | editor | 109 | 105 | 4 | `readback` | 达标 | runs/_exercises/ex_write5/c4-v5-task111(7) ; runs/_exercises/ex_scene/c23-task110(6) ; runs/_exercises/ex_scene2/c23-after-task110(6) |
| `project_read_scene_file_content` | both | 6 | 5 | 1 | `readback` | 达标 | runs/_exercises/ex_files/c1-task110(6) |
| `editor_open_scene` | editor | 80 | 8 | 0 | `pixel_effect` | 计数达标缺证据 | runs/breakout/breakout-clean-task097(2) ; runs/pong/pong-clean-task097(2) ; runs/snake/snake-clean-task097(2) |
| `project_delete_scene_file` | both | 10 | 8 | 2 | `file_effect` | 达标 | runs/_exercises/ex_files/c1-task110(6) ; runs/pong/d3-after(2) ; runs/pong/d3-after-r2(2) |
| `editor_add_scene_instance` | editor | 30 | 0 | 5 | `readback` | 计数达标缺证据 | runs/_exercises/ex_write/c4-task111(6) ; runs/_exercises/ex_write2/c4b-task111(6) ; runs/_exercises/ex_write3/c4c-task111(6) |
| `project_get_scene_exports` | both | 6 | 5 | 1 | `readback` | 达标 | runs/_exercises/ex_files/c1-task110(6) |
| `editor_save_scene` | editor | 123 | 77 | 0 | `file_effect` | 计数达标缺证据 | runs/lunarlander/ll-task104-r1(3) ; runs/missilecommand/mc-task103-r1(3) ; runs/missilecommand/mc-task103-r2(3) |
| `project_create_scene_file` | both | 20 | 18 | 2 | `file_effect` | 达标 | runs/_exercises/ex_files/c1-task110(6) ; runs/_exercises/ex_files/c1c-task110(6) ; runs/_exercises/ex_write/c4-task111(1) |
| `editor_add_node` | editor | 30 | 10 | 5 | `pixel_effect` | 达标 | runs/_exercises/ex_write/c4-task111(6) ; runs/_exercises/ex_write2/c4b-task111(6) ; runs/_exercises/ex_write3/c4c-task111(6) |
| `editor_delete_node` | editor | 65 | 5 | 0 | `pixel_effect` | 计数达标缺证据 | runs/snake/snake-clean-task097(37) ; runs/breakout/breakout-clean-task097(20) ; runs/pong/pong-clean-task097(8) |
| `editor_rename_node` | editor | 30 | 0 | 7 | `readback` | 计数达标缺证据 | runs/_exercises/ex_write/c4-task111(6) ; runs/_exercises/ex_write2/c4b-task111(6) ; runs/_exercises/ex_write3/c4c-task111(6) |
| `editor_set_node_property` | editor | 41 | 12 | 0 | `pixel_effect` | 计数达标缺证据 | runs/pong/pong-clean-task097(3) ; runs/pong/pong-control-task093(3) ; runs/pong/pong-run1(3) |
| `editor_get_node_properties` | editor | 74 | 62 | 12 | `readback` | 达标 | runs/breakout/breakout-clean-task097(10) ; runs/pong/pong-clean-task097(9) ; runs/snake/snake-clean-task097(9) |
| `editor_duplicate_node` | editor | 30 | 5 | 7 | `pixel_effect` | 达标 | runs/_exercises/ex_write/c4-task111(6) ; runs/_exercises/ex_write2/c4b-task111(6) ; runs/_exercises/ex_write3/c4c-task111(6) |
| `editor_connect_signal` | editor | 39 | 0 | 6 | `count_only` | 计数达标缺证据 | runs/_exercises/ex_write/c4-task111(6) ; runs/_exercises/ex_write2/c4b-task111(6) ; runs/_exercises/ex_write3/c4c-task111(6) |
| `editor_disconnect_signal` | editor | 6 | 0 | 1 | `readback` | 计数达标缺证据 | runs/_exercises/ex_write6/c5-task111(6) |
| `editor_reparent_node` | editor | 30 | 3 | 14 | `pixel_effect` | 达标 | runs/_exercises/ex_write/c4-task111(6) ; runs/_exercises/ex_write2/c4b-task111(6) ; runs/_exercises/ex_write3/c4c-task111(6) |
| `editor_add_resource_to_node_property` | editor | 33 | 12 | 20 | `pixel_effect` | 达标 | runs/_exercises/ex_write4/c4-final-task111(7) ; runs/_exercises/ex_write5/c4-v5-task111(7) ; runs/_exercises/ex_write/c4-task111(6) |
| `editor_set_anchor_preset` | editor | 24 | 5 | 5 | `pixel_effect` | 达标 | runs/_exercises/ex_write/c4-task111(6) ; runs/_exercises/ex_write3/c4c-task111(6) ; runs/_exercises/ex_write4/c4-final-task111(6) |
| `editor_get_node_groups` | editor | 13 | 11 | 2 | `readback` | 达标 | runs/_exercises/ex_scene/c23-task110(6) ; runs/_exercises/ex_scene2/c23-after-task110(6) ; runs/_exercises/ex_write5/c4-v5-task111(1) |
| `editor_set_node_groups` | editor | 36 | 0 | 11 | `readback` | 计数达标缺证据 | runs/_exercises/ex_write/c4-task111(7) ; runs/_exercises/ex_write3/c4c-task111(7) ; runs/_exercises/ex_write4/c4-final-task111(7) |
| `editor_find_nodes_in_group` | editor | 12 | 10 | 2 | `readback` | 达标 | runs/_exercises/ex_scene/c23-task110(6) ; runs/_exercises/ex_scene2/c23-after-task110(6) |
| `editor_get_selection` | editor | 12 | 10 | 2 | `readback` | 达标 | runs/_exercises/ex_scene/c23-task110(6) ; runs/_exercises/ex_scene2/c23-after-task110(6) |
| `editor_execute_gdscript` | editor | 12 | 10 | 2 | `readback` | 达标 | runs/_exercises/ex_scene/c23-task110(6) ; runs/_exercises/ex_scene2/c23-after-task110(6) |
| `editor_get_errors` | editor | 50 | 50 | 0 | `readback` | 计数达标缺证据 | runs/asteroids/ast-task098-r1(1) ; runs/asteroids/ast-task098-r2(1) ; runs/breakout/breakout-clean-task097(1) |
| `editor_get_output_log` | editor | 36 | 32 | 4 | `readback` | 达标 | runs/_exercises/ex_scene/c23-task110(6) ; runs/_exercises/ex_scene2/c23-after-task110(6) ; runs/_exercises/ex_write/c4-task111(6) |
| `editor_capture_screenshot` | editor | 25 | 25 | 0 | `file_effect` | 计数达标缺证据 | runs/breakout/breakout-clean-task097(1) ; runs/breakout/breakout-task093(1) ; runs/breakout/breakout-task093-r2(1) |
| `running_game_capture_screenshot` | game | 298 | 298 | 0 | `pixel_effect` | 计数达标缺证据 | runs/match3/m3-task102-r1(7) ; runs/match3/m3-task102-r2(7) ; runs/match3/m3-task102-r3(7) |
| `editor_get_node_signals` | editor | 12 | 10 | 2 | `readback` | 达标 | runs/_exercises/ex_scene/c23-task110(6) ; runs/_exercises/ex_scene2/c23-after-task110(6) |
| `editor_get_viewport_3d_camera` | editor | 6 | 5 | 1 | `readback` | 达标 | runs/_exercises/ex_3d/h1-task111(6) |
| `editor_set_viewport_3d_camera` | editor | 6 | 0 | 1 | `readback` | 计数达标缺证据 | runs/_exercises/ex_3d/h1-task111(6) |
| `running_game_get_scene_tree` | game | 123 | 123 | 0 | `pixel_effect` | 计数达标缺证据 | runs/asteroids/ast-task098-r1(2) ; runs/asteroids/ast-task098-r2(2) ; runs/bomberman/bomb-task101-r1(2) |
| `running_game_get_node_properties` | game | 58 | 56 | 2 | `pixel_effect` | 达标 | runs/_exercises/ex_scene/c23-task110(6) ; runs/_exercises/ex_scene2/c23-after-task110(6) ; runs/_exercises/ex_rec/h9-task113(5) |
| `running_game_set_node_property` | game | 49 | 28 | 2 | `pixel_effect` | 达标 | runs/pong/pong-clean-task097(5) ; runs/pong/pong-control-task093(5) ; runs/pong/pong-run1(5) |
| `running_game_capture_frames` | game | 36 | 30 | 6 | `readback` | 达标 | runs/_exercises/ex_scene/c23-task110(6) ; runs/_exercises/ex_scene2/c23-after-task110(6) ; runs/_exercises/ex_write/c4-task111(6) |
| `running_game_get_node_property_samples` | game | 122 | 122 | 0 | `pixel_effect` | 计数达标缺证据 | runs/spaceinvaders/si-task097-r1(5) ; runs/tetris/tetris-task096(4) ; runs/tetris/tetris-task096-r2(4) |
| `running_game_execute_gdscript` | game | 1626 | 1593 | 33 | `pixel_effect` | 达标 | runs/rtype/rt-task104-r1(98) ; runs/rtype/rt-task104-r2(98) ; runs/bomberman/bomb-task101-r2(61) |
| `running_game_create_input_recording` | game | 7 | 0 | 1 | `readback` | 计数达标缺证据 | runs/_exercises/ex_rec/h9-task113(7) |
| `running_game_stop_input_recording` | game | 7 | 0 | 0 | `readback` | 计数达标缺证据 | runs/_exercises/ex_rec/h9-task113(7) |
| `running_game_play_input_recording` | game | 7 | 6 | 1 | `pixel_effect` | 达标 | runs/_exercises/ex_rec/h9-task113(7) |
| `running_game_find_nodes_by_script` | game | 12 | 10 | 2 | `readback` | 达标 | runs/_exercises/ex_scene/c23-task110(6) ; runs/_exercises/ex_scene2/c23-after-task110(6) |
| `running_game_get_autoload_node` | game | 12 | 10 | 2 | `readback` | 达标 | runs/_exercises/ex_scene/c23-task110(6) ; runs/_exercises/ex_scene2/c23-after-task110(6) |
| `running_game_get_node_properties_batch` | game | 36 | 32 | 4 | `readback` | 达标 | runs/_exercises/ex_scene/c23-task110(6) ; runs/_exercises/ex_scene2/c23-after-task110(6) ; runs/_exercises/ex_write/c4-task111(6) |
| `running_game_find_ui_elements` | game | 12 | 10 | 2 | `readback` | 达标 | runs/_exercises/ex_scene/c23-task110(6) ; runs/_exercises/ex_scene2/c23-after-task110(6) |
| `running_game_simulate_button_click_by_text` | game | 12 | 2 | 2 | `pixel_effect` | 达标 | runs/_exercises/ex_scene/c23-task110(6) ; runs/_exercises/ex_scene2/c23-after-task110(6) |
| `running_game_find_node_when_available` | game | 8 | 0 | 8 | `count_only` | 计数达标缺证据 | runs/breakout/breakout-clean-task097(1) ; runs/breakout/breakout-task093(1) ; runs/breakout/breakout-task093-r2(1) |
| `running_game_find_nearby_nodes` | game | 12 | 10 | 2 | `readback` | 达标 | runs/_exercises/ex_scene/c23-task110(6) ; runs/_exercises/ex_scene2/c23-after-task110(6) |
| `running_game_move_player_to_target` | game | 6 | 5 | 1 | `pixel_effect` | 达标 | runs/_exercises/ex_nav/h4-task113(6) |
| `running_game_capture_signal_emissions` | game | 36 | 26 | 10 | `readback` | 达标 | runs/_exercises/ex_scene/c23-task110(6) ; runs/_exercises/ex_scene2/c23-after-task110(6) ; runs/_exercises/ex_write/c4-task111(6) |
| `editor_get_performance_monitors` | editor | 12 | 10 | 2 | `readback` | 达标 | runs/_exercises/ex_scene/c23-task110(6) ; runs/_exercises/ex_scene2/c23-after-task110(6) |
| `project_list_scripts` | both | 6 | 5 | 1 | `readback` | 达标 | runs/_exercises/ex_files/c1-task110(6) |
| `project_read_script` | both | 8 | 6 | 2 | `readback` | 达标 | runs/_exercises/ex_files/c1-task110(6) ; runs/_exercises/ex_files/c1-smoke(2) |
| `project_create_script` | both | 76 | 43 | 1 | `file_effect` | 达标 | runs/_exercises/ex_files/c1-task110(6) ; runs/_exercises/ex_files/c1b-task110(6) ; runs/_exercises/ex_files/c1c-task110(6) |
| `project_edit_script` | both | 60 | 52 | 0 | `file_effect` | 计数达标缺证据 | runs/tetris/tetris-task096-r2(2) ; runs/asteroids/ast-task098-r1(1) ; runs/asteroids/ast-task098-r2(1) |
| `editor_set_node_script` | editor | 30 | 0 | 5 | `count_only` | 计数达标缺证据 | runs/_exercises/ex_write/c4-task111(6) ; runs/_exercises/ex_write2/c4b-task111(6) ; runs/_exercises/ex_write3/c4c-task111(6) |
| `editor_get_open_scripts` | editor | 12 | 10 | 2 | `readback` | 达标 | runs/_exercises/ex_scene/c23-task110(6) ; runs/_exercises/ex_scene2/c23-after-task110(6) |
| `project_validate_script` | both | 18 | 3 | 15 | `readback` | 达标 | runs/_exercises/ex_files/c1-task110(6) ; runs/_exercises/ex_files/c1b-task110(6) ; runs/_exercises/ex_files/c1c-task110(6) |
| `editor_get_input_actions` | editor | 12 | 10 | 2 | `readback` | 达标 | runs/_exercises/ex_scene/c23-task110(6) ; runs/_exercises/ex_scene2/c23-after-task110(6) |
| `editor_add_input_action` | editor | 189 | 122 | 0 | `file_effect` | 计数达标缺证据 | runs/pong/pong-clean-task097(5) ; runs/pong/pong-control-task093(5) ; runs/pong/pong-run1(5) |
| `editor_find_nodes_by_type` | editor | 12 | 10 | 2 | `readback` | 达标 | runs/_exercises/ex_scene/c23-task110(6) ; runs/_exercises/ex_scene2/c23-after-task110(6) |
| `editor_set_node_property_batch` | editor | 30 | 15 | 5 | `pixel_effect` | 达标 | runs/_exercises/ex_write/c4-task111(6) ; runs/_exercises/ex_write2/c4b-task111(6) ; runs/_exercises/ex_write3/c4c-task111(6) |
| `editor_list_signal_connections` | editor | 13 | 9 | 4 | `readback` | 达标 | runs/_exercises/ex_scene/c23-task110(6) ; runs/_exercises/ex_scene2/c23-after-task110(6) ; runs/_exercises/ex_write6/c5-task111(1) |
| `editor_add_nodes_batch` | editor | 106 | 47 | 42 | `pixel_effect` | 达标 | runs/pong/d3-after(3) ; runs/pong/d3-after-r2(3) ; runs/asteroids/ast-task098-r1(2) |
| `project_find_files_referencing_symbol` | both | 12 | 11 | 1 | `readback` | 达标 | runs/_exercises/ex_files/c1-task110(6) ; runs/_exercises/ex_files/c1b-task110(6) |
| `project_get_scene_dependencies` | both | 6 | 5 | 1 | `readback` | 达标 | runs/_exercises/ex_files/c1-task110(6) |
| `project_set_node_property_across_scenes` | both | 18 | 1 | 1 | `file_effect` | 达标 | runs/_exercises/ex_files/c1-task110(6) ; runs/_exercises/ex_files/c1b-task110(6) ; runs/_exercises/ex_files/c1c-task110(6) |
| `editor_list_animations` | editor | 12 | 10 | 2 | `readback` | 达标 | runs/_exercises/ex_anim/h2-task111(6) ; runs/_exercises/ex_anim2/h2b-task111(6) |
| `editor_create_animation` | editor | 18 | 0 | 2 | `readback` | 计数达标缺证据 | runs/_exercises/ex_anim/h2-task111(9) ; runs/_exercises/ex_anim2/h2b-task111(9) |
| `editor_add_animation_track` | editor | 12 | 0 | 2 | `readback` | 计数达标缺证据 | runs/_exercises/ex_anim/h2-task111(6) ; runs/_exercises/ex_anim2/h2b-task111(6) |
| `editor_set_animation_keyframe` | editor | 12 | 0 | 2 | `readback` | 计数达标缺证据 | runs/_exercises/ex_anim/h2-task111(6) ; runs/_exercises/ex_anim2/h2b-task111(6) |
| `editor_get_animation_info` | editor | 12 | 10 | 2 | `readback` | 达标 | runs/_exercises/ex_anim/h2-task111(6) ; runs/_exercises/ex_anim2/h2b-task111(6) |
| `editor_remove_animation` | editor | 12 | 0 | 2 | `count_only` | 计数达标缺证据 | runs/_exercises/ex_anim/h2-task111(6) ; runs/_exercises/ex_anim2/h2b-task111(6) |
| `editor_get_tilemap_info` | editor | 6 | 5 | 1 | `readback` | 达标 | runs/_exercises/ex_grid/h3-task111(6) |
| `editor_get_tilemap_used_cells` | editor | 6 | 5 | 1 | `readback` | 达标 | runs/_exercises/ex_grid/h3-task111(6) |
| `editor_remove_all_tilemap_cells` | editor | 6 | 5 | 1 | `pixel_effect` | 达标 | runs/_exercises/ex_grid/h3-task111(6) |
| `editor_set_tilemap_cell` | editor | 10 | 9 | 1 | `pixel_effect` | 达标 | runs/_exercises/ex_grid/h3-task111(10) |
| `editor_set_tilemap_cells_in_rect` | editor | 6 | 5 | 1 | `pixel_effect` | 达标 | runs/_exercises/ex_grid/h3-task111(6) |
| `editor_get_tilemap_cell` | editor | 6 | 5 | 1 | `readback` | 达标 | runs/_exercises/ex_grid/h3-task111(6) |
| `project_read_resource` | both | 6 | 5 | 1 | `readback` | 达标 | runs/_exercises/ex_files/c1-task110(6) |
| `project_add_autoload` | both | 8 | 7 | 1 | `file_effect` | 达标 | runs/_exercises/ex_files/c1-task110(6) ; runs/_exercises/ex_scene/c23-task110(1) ; runs/_exercises/ex_scene2/c23-after-task110(1) |
| `project_remove_autoload` | both | 6 | 5 | 1 | `file_effect` | 达标 | runs/_exercises/ex_files/c1-task110(6) |
| `project_edit_resource` | both | 6 | 5 | 1 | `file_effect` | 达标 | runs/_exercises/ex_files/c1-task110(6) |
| `project_create_resource` | both | 7 | 6 | 1 | `file_effect` | 达标 | runs/_exercises/ex_files/c1-task110(6) ; runs/_exercises/ex_3d/h1-task111(1) |
| `project_get_resource_preview` | both | 12 | 5 | 7 | `readback` | 达标 | runs/_exercises/ex_files/c1-task110(6) ; runs/_exercises/ex_files/c1b-task110(6) |
| `project_read_shader` | both | 7 | 6 | 1 | `readback` | 达标 | runs/_exercises/ex_files/c1-task110(6) ; runs/_exercises/ex_files/c1-smoke(1) |
| `project_create_shader` | both | 12 | 11 | 1 | `file_effect` | 达标 | runs/_exercises/ex_files/c1-task110(6) ; runs/_exercises/ex_files/c1-smoke(1) ; runs/_exercises/ex_write/c4-task111(1) |
| `project_edit_shader` | both | 8 | 7 | 1 | `file_effect` | 达标 | runs/_exercises/ex_files/c1-task110(6) ; runs/_exercises/ex_write4/c4-final-task111(1) ; runs/_exercises/ex_write5/c4-v5-task111(1) |
| `editor_set_shader_material` | editor | 24 | 3 | 6 | `pixel_effect` | 达标 | runs/_exercises/ex_write/c4-task111(6) ; runs/_exercises/ex_write3/c4c-task111(6) ; runs/_exercises/ex_write4/c4-final-task111(6) |
| `editor_set_shader_param` | editor | 24 | 1 | 14 | `pixel_effect` | 达标 | runs/_exercises/ex_write/c4-task111(6) ; runs/_exercises/ex_write3/c4c-task111(6) ; runs/_exercises/ex_write4/c4-final-task111(6) |
| `project_get_shader_params` | both | 6 | 5 | 1 | `readback` | 达标 | runs/_exercises/ex_files/c1-task110(6) |
| `editor_add_raycast` | editor | 36 | 16 | 11 | `pixel_effect` | 达标 | runs/_exercises/ex_write3/c4c-task111(7) ; runs/_exercises/ex_write4/c4-final-task111(7) ; runs/_exercises/ex_write5/c4-v5-task111(7) |
| `editor_setup_collision_shape` | editor | 31 | 9 | 11 | `pixel_effect` | 达标 | runs/_exercises/ex_write/c4-task111(7) ; runs/_exercises/ex_write3/c4c-task111(7) ; runs/_exercises/ex_write4/c4-final-task111(7) |
| `editor_set_physics_layers` | editor | 24 | 0 | 6 | `readback` | 计数达标缺证据 | runs/_exercises/ex_write/c4-task111(6) ; runs/_exercises/ex_write3/c4c-task111(6) ; runs/_exercises/ex_write4/c4-final-task111(6) |
| `editor_get_physics_layers` | editor | 12 | 6 | 6 | `readback` | 达标 | runs/_exercises/ex_scene/c23-task110(6) ; runs/_exercises/ex_scene2/c23-after-task110(6) |
| `editor_setup_physics_body` | editor | 24 | 0 | 7 | `readback` | 计数达标缺证据 | runs/_exercises/ex_write/c4-task111(6) ; runs/_exercises/ex_write3/c4c-task111(6) ; runs/_exercises/ex_write4/c4-final-task111(6) |
| `editor_get_collision_info` | editor | 12 | 8 | 4 | `readback` | 达标 | runs/_exercises/ex_scene/c23-task110(6) ; runs/_exercises/ex_scene2/c23-after-task110(6) |
| `editor_add_mesh_instance` | editor | 6 | 0 | 1 | `count_only` | 计数达标缺证据 | runs/_exercises/ex_3d/h1-task111(6) |
| `editor_setup_camera_3d` | editor | 6 | 0 | 1 | `count_only` | 计数达标缺证据 | runs/_exercises/ex_3d/h1-task111(6) |
| `editor_setup_lighting` | editor | 6 | 0 | 1 | `count_only` | 计数达标缺证据 | runs/_exercises/ex_3d/h1-task111(6) |
| `editor_set_material_3d` | editor | 6 | 0 | 3 | `count_only` | 计数达标缺证据 | runs/_exercises/ex_3d/h1-task111(6) |
| `editor_setup_world_environment` | editor | 6 | 0 | 1 | `count_only` | 计数达标缺证据 | runs/_exercises/ex_3d/h1-task111(6) |
| `editor_add_gridmap` | editor | 6 | 0 | 1 | `count_only` | 计数达标缺证据 | runs/_exercises/ex_grid/h3-task111(6) |
| `editor_add_audio_player` | editor | 6 | 0 | 1 | `readback` | 计数达标缺证据 | runs/_exercises/ex_audio/h5-task113(6) |
| `editor_get_audio_info` | editor | 6 | 5 | 1 | `readback` | 达标 | runs/_exercises/ex_audio/h5-task113(6) |
| `editor_get_audio_bus_layout` | editor | 7 | 6 | 1 | `readback` | 达标 | runs/_exercises/ex_audio/h5-task113(7) |
| `editor_add_audio_bus` | editor | 7 | 0 | 2 | `readback` | 计数达标缺证据 | runs/_exercises/ex_audio/h5-task113(7) |
| `editor_set_audio_bus_property` | editor | 8 | 0 | 3 | `readback` | 计数达标缺证据 | runs/_exercises/ex_audio/h5-task113(8) |
| `editor_add_audio_bus_effect` | editor | 7 | 0 | 2 | `readback` | 计数达标缺证据 | runs/_exercises/ex_audio/h5-task113(7) |
| `project_create_theme` | both | 11 | 10 | 1 | `file_effect` | 达标 | runs/_exercises/ex_files/c1-task110(6) ; runs/_exercises/ex_write/c4-task111(1) ; runs/_exercises/ex_write2/c4b-task111(1) |
| `project_set_theme_color` | both | 6 | 5 | 1 | `file_effect` | 达标 | runs/_exercises/ex_files/c1-task110(6) |
| `project_set_theme_constant` | both | 6 | 5 | 1 | `file_effect` | 达标 | runs/_exercises/ex_files/c1-task110(6) |
| `project_set_theme_font_size` | both | 6 | 5 | 1 | `file_effect` | 达标 | runs/_exercises/ex_files/c1-task110(6) |
| `project_set_theme_stylebox` | both | 6 | 5 | 1 | `file_effect` | 达标 | runs/_exercises/ex_files/c1-task110(6) |
| `editor_set_control_theme` | editor | 24 | 0 | 5 | `count_only` | 计数达标缺证据 | runs/_exercises/ex_write/c4-task111(6) ; runs/_exercises/ex_write3/c4c-task111(6) ; runs/_exercises/ex_write4/c4-final-task111(6) |
| `project_get_theme_info` | both | 6 | 5 | 1 | `readback` | 达标 | runs/_exercises/ex_files/c1-task110(6) |
| `editor_create_animation_tree` | editor | 12 | 0 | 2 | `readback` | 计数达标缺证据 | runs/_exercises/ex_anim/h2-task111(6) ; runs/_exercises/ex_anim2/h2b-task111(6) |
| `editor_get_animation_tree_structure` | editor | 12 | 10 | 2 | `readback` | 达标 | runs/_exercises/ex_anim/h2-task111(6) ; runs/_exercises/ex_anim2/h2b-task111(6) |
| `editor_add_state_machine_state` | editor | 18 | 0 | 2 | `readback` | 计数达标缺证据 | runs/_exercises/ex_anim2/h2b-task111(12) ; runs/_exercises/ex_anim/h2-task111(6) |
| `editor_remove_state_machine_state` | editor | 12 | 0 | 7 | `readback` | 计数达标缺证据 | runs/_exercises/ex_anim/h2-task111(6) ; runs/_exercises/ex_anim2/h2b-task111(6) |
| `editor_add_state_machine_transition` | editor | 22 | 0 | 2 | `readback` | 计数达标缺证据 | runs/_exercises/ex_anim/h2-task111(11) ; runs/_exercises/ex_anim2/h2b-task111(11) |
| `editor_remove_state_machine_transition` | editor | 12 | 0 | 2 | `readback` | 计数达标缺证据 | runs/_exercises/ex_anim/h2-task111(6) ; runs/_exercises/ex_anim2/h2b-task111(6) |
| `editor_set_blend_tree_node` | editor | 12 | 0 | 7 | `readback` | 计数达标缺证据 | runs/_exercises/ex_anim/h2-task111(6) ; runs/_exercises/ex_anim2/h2b-task111(6) |
| `editor_set_animation_tree_parameter` | editor | 12 | 0 | 4 | `readback` | 计数达标缺证据 | runs/_exercises/ex_anim/h2-task111(6) ; runs/_exercises/ex_anim2/h2b-task111(6) |
| `editor_setup_navigation_region` | editor | 6 | 0 | 1 | `readback` | 计数达标缺证据 | runs/_exercises/ex_nav/h4-task113(6) |
| `editor_bake_navigation_mesh` | editor | 6 | 1 | 1 | `pixel_effect` | 达标 | runs/_exercises/ex_nav/h4-task113(6) |
| `editor_setup_navigation_agent` | editor | 6 | 0 | 1 | `readback` | 计数达标缺证据 | runs/_exercises/ex_nav/h4-task113(6) |
| `editor_set_navigation_layers` | editor | 7 | 0 | 2 | `readback` | 计数达标缺证据 | runs/_exercises/ex_nav/h4-task113(7) |
| `editor_get_navigation_info` | editor | 6 | 5 | 1 | `readback` | 达标 | runs/_exercises/ex_nav/h4-task113(6) |
| `editor_create_particles` | editor | 8 | 0 | 3 | `readback` | 计数达标缺证据 | runs/_exercises/ex_particles/h6-task113(8) |
| `editor_set_particle_material` | editor | 8 | 5 | 3 | `pixel_effect` | 达标 | runs/_exercises/ex_particles/h6-task113(8) |
| `editor_set_particle_color_gradient` | editor | 9 | 6 | 3 | `pixel_effect` | 达标 | runs/_exercises/ex_particles/h6-task113(9) |
| `editor_set_particle_preset` | editor | 7 | 5 | 2 | `pixel_effect` | 达标 | runs/_exercises/ex_particles/h6-task113(7) |
| `editor_get_particle_info` | editor | 7 | 6 | 1 | `pixel_effect` | 达标 | runs/_exercises/ex_particles/h6-task113(7) |
| `project_find_unused_resources` | both | 6 | 5 | 1 | `readback` | 达标 | runs/_exercises/ex_files/c1-task110(6) |
| `editor_analyze_signal_flow` | editor | 12 | 8 | 4 | `readback` | 达标 | runs/_exercises/ex_scene/c23-task110(6) ; runs/_exercises/ex_scene2/c23-after-task110(6) |
| `project_analyze_scene_complexity` | both | 6 | 5 | 1 | `readback` | 达标 | runs/_exercises/ex_files/c1-task110(6) |
| `project_find_script_references` | both | 12 | 11 | 1 | `readback` | 达标 | runs/_exercises/ex_files/c1-task110(6) ; runs/_exercises/ex_files/c1b-task110(6) |
| `project_detect_circular_dependencies` | both | 6 | 5 | 1 | `readback` | 达标 | runs/_exercises/ex_files/c1-task110(6) |
| `project_get_statistics` | both | 7 | 5 | 2 | `readback` | 达标 | runs/_exercises/ex_files/c1-task110(6) ; runs/_exercises/ex_files/c1-smoke(1) |
| `running_game_run_test_scenario` | game | 185 | 131 | 0 | `pixel_effect` | 计数达标缺证据 | runs/snake/snake-clean-task097(8) ; runs/snake/snake-task093(8) ; runs/snake/snake-task093-r2(8) |
| `running_game_assert_node_state` | game | 2903 | 2719 | 115 | `file_effect` | 达标 | runs/lunarlander/ll-task104-r1(149) ; runs/bomberman/bomb-task101-r4(144) ; runs/bomberman/bomb-task101-r3(142) |
| `running_game_assert_screen_text` | game | 80 | 65 | 0 | `file_effect` | 计数达标缺证据 | runs/asteroids/ast-task098-r1(2) ; runs/asteroids/ast-task098-r2(2) ; runs/bomberman/bomb-task101-r1(2) |
| `running_game_run_stress_test` | game | 27 | 5 | 0 | `pixel_effect` | 计数达标缺证据 | runs/breakout/breakout-clean-task097(1) ; runs/breakout/breakout-task093(1) ; runs/breakout/breakout-task093-r2(1) |
| `project_build_csharp` | both | 66 | 62 | 0 | `file_effect` | 计数达标缺证据 | runs/_exercises/ex_files/c1b-task110(1) ; runs/_exercises/ex_scene/c23-task110(1) ; runs/_exercises/ex_scene2/c23-after-task110(1) |
| `project_write_text_file` | both | 7 | 6 | 1 | `file_effect` | 达标 | runs/_exercises/ex_files/c1-task110(6) ; runs/_exercises/ex_files/c1-smoke(1) |
| `project_validate_scripts` | both | 84 | 80 | 0 | `readback` | 计数达标缺证据 | runs/breakout/breakout-clean-task097(2) ; runs/breakout/breakout-task093(2) ; runs/breakout/breakout-task093-r2(2) |
| `editor_set_node_script_batch` | editor | 50 | 0 | 0 | `count_only` | 计数达标缺证据 | runs/breakout/breakout-clean-task097(2) ; runs/breakout/breakout-task093(2) ; runs/breakout/breakout-task093-r2(2) |
| `editor_set_node_property_updates` | editor | 30 | 3 | 7 | `pixel_effect` | 达标 | runs/_exercises/ex_write/c4-task111(6) ; runs/_exercises/ex_write2/c4b-task111(6) ; runs/_exercises/ex_write3/c4c-task111(6) |
| `project_read_text_file` | both | 86 | 85 | 1 | `readback` | 达标 | runs/_exercises/ex_files/c1-task110(6) ; runs/pong/d3-after(3) ; runs/pong/d3-after-r2(3) |

### 2.2 `1-4` 次（0 条）

| tool | scope | 累计 | 有效 | 边界 | 档位 | 状态 | 证据 |
|---|---|---|---|---|---|---|---|

### 2.3 `0` 次（20 条）

（按前缀分组，均为 0 次；其中登记为「不可达」的见 §4）

- **editor_**（15）：`editor_play_scene` `editor_stop_scene` `editor_set_node_selection` `editor_remove_node_selection` `editor_remove_output_log` `editor_reload_plugin` `editor_rescan_project_filesystem` `editor_analyze_screenshot_diff` `editor_set_auto_dismiss_dialogs` `editor_simulate_key` `editor_simulate_mouse_click` `editor_simulate_mouse_move` `editor_simulate_input_action` `editor_simulate_input_sequence` `editor_get_test_report`
- **os_**（2）：`os_list_android_devices` `os_deploy_to_android_device`
- **project_**（3）：`project_get_export_info` `project_list_export_presets` `project_get_android_preset_info`

## 3. `<5` 清单（本轮仍未达标的工具）

共 **20** 条（占契约 11.3%）：`0` 次 20 条、`1-4` 次 0 条。

| tool | scope | verb | 累计 | 有效 | 边界 | 档位 | 登记不可达 | 状态 |
|---|---|---|---|---|---|---|---|---|
| `editor_play_scene` | editor | play | 0 | 0 | 0 | `no_calls` | H7 | 未达(0) |
| `editor_stop_scene` | editor | stop | 0 | 0 | 0 | `no_calls` | H7 | 未达(0) |
| `editor_set_node_selection` | editor | set | 0 | 0 | 0 | `no_calls` | H7 | 未达(0) |
| `editor_remove_node_selection` | editor | remove | 0 | 0 | 0 | `no_calls` | H7 | 未达(0) |
| `editor_remove_output_log` | editor | remove | 0 | 0 | 0 | `no_calls` | H7 | 未达(0) |
| `editor_reload_plugin` | editor | reload | 0 | 0 | 0 | `no_calls` | H7 | 未达(0) |
| `editor_rescan_project_filesystem` | editor | rescan | 0 | 0 | 0 | `no_calls` | H7 | 未达(0) |
| `editor_analyze_screenshot_diff` | editor | analyze | 0 | 0 | 0 | `no_calls` | H7 | 未达(0) |
| `editor_set_auto_dismiss_dialogs` | editor | set | 0 | 0 | 0 | `no_calls` | H7 | 未达(0) |
| `editor_simulate_key` | editor | simulate | 0 | 0 | 0 | `no_calls` | H7 | 未达(0) |
| `editor_simulate_mouse_click` | editor | simulate | 0 | 0 | 0 | `no_calls` | H7 | 未达(0) |
| `editor_simulate_mouse_move` | editor | simulate | 0 | 0 | 0 | `no_calls` | H7 | 未达(0) |
| `editor_simulate_input_action` | editor | simulate | 0 | 0 | 0 | `no_calls` | H7 | 未达(0) |
| `editor_simulate_input_sequence` | editor | simulate | 0 | 0 | 0 | `no_calls` | H7 | 未达(0) |
| `project_get_export_info` | both | get | 0 | 0 | 0 | `no_calls` | H8 | 未达(0) |
| `project_list_export_presets` | both | list | 0 | 0 | 0 | `no_calls` | H8 | 未达(0) |
| `editor_get_test_report` | editor | get | 0 | 0 | 0 | `no_calls` | H7 | 未达(0) |
| `os_list_android_devices` | both | list | 0 | 0 | 0 | `no_calls` | H8 | 未达(0) |
| `project_get_android_preset_info` | both | get | 0 | 0 | 0 | `no_calls` | H8 | 未达(0) |
| `os_deploy_to_android_device` | both | deploy | 0 | 0 | 0 | `no_calls` | H8 | 未达(0) |

## 4. 不可达登记表的联动视图（H1–H9）

登记来源：`recovery/reports/TOOL-COVERAGE-TASK-108.md` §5.3 (5) which of them are structurally unreachable in this loop (INFERENCE)（**推断**，判据是「缺少本循环不具备的子系统/资产/前置运行态」）。本视图把登记表与本轮实测**对在一起**：`实测调用` 列不为 0 的条目就是登记漂移，必须在下一轮从登记表里移除或改判。

登记成员 **74** 条；其中实测**已被调用**（登记漂移）**54** 条，其中 **54** 条已按实测证据改判并记入登记表的 `reclassified`（下表 `改判` 列打 `YES`），其余为待复核漂移。

### H1 3D 内容管线

- 为何不可达（推断）：20 款游戏**全部是 2D**，世界由 `ColorRect` / `Label` 在运行期或加载期拼出；工程里没有任何 Mesh / Camera3D / 光照 / WorldEnvironment 资产，也没有 `.tscn` 里能寻址的 3D 节点
- 支撑证据（只读观察）：模块侧 `tools/editor_scene_3d_write.cpp`；20 款游戏的载荷全部为 2D 坐标（台账逐条记 `ColorRect`/`Label`/像素差）

| tool | scope | 实测调用 | 漂移 | 改判 | 证据 |
|---|---|---|---|---|---|
| `editor_add_mesh_instance` | editor | 6 | **YES** | YES | runs/_exercises/ex_3d/h1-task111(6) |
| `editor_get_viewport_3d_camera` | editor | 6 | **YES** | YES | runs/_exercises/ex_3d/h1-task111(6) |
| `editor_set_material_3d` | editor | 6 | **YES** | YES | runs/_exercises/ex_3d/h1-task111(6) |
| `editor_set_viewport_3d_camera` | editor | 6 | **YES** | YES | runs/_exercises/ex_3d/h1-task111(6) |
| `editor_setup_camera_3d` | editor | 6 | **YES** | YES | runs/_exercises/ex_3d/h1-task111(6) |
| `editor_setup_lighting` | editor | 6 | **YES** | YES | runs/_exercises/ex_3d/h1-task111(6) |
| `editor_setup_world_environment` | editor | 6 | **YES** | YES | runs/_exercises/ex_3d/h1-task111(6) |

### H2 动画 / AnimationTree / 状态机

- 为何不可达（推断）：运动一律由**载荷自己的整数运动学**推进（`StepFrames(n)`、`_Process` 里 `x+=vx`），从不使用 `AnimationPlayer` / `AnimationTree`；没有动画资源可读写，也没有状态机可建
- 支撑证据（只读观察）：`tools/editor_animation_read.cpp`、`editor_animation_write.cpp`、`editor_animation_tree_write.cpp`、`tools/animation_shared.cpp`；契约 override 里 `add_state_machine_state` 的 `animation` 成员是「结构性不可达」的已知缺口

| tool | scope | 实测调用 | 漂移 | 改判 | 证据 |
|---|---|---|---|---|---|
| `editor_add_animation_track` | editor | 12 | **YES** | YES | runs/_exercises/ex_anim/h2-task111(6) ; runs/_exercises/ex_anim2/h2b-task111(6) |
| `editor_add_state_machine_state` | editor | 18 | **YES** | YES | runs/_exercises/ex_anim2/h2b-task111(12) ; runs/_exercises/ex_anim/h2-task111(6) |
| `editor_add_state_machine_transition` | editor | 22 | **YES** | YES | runs/_exercises/ex_anim/h2-task111(11) ; runs/_exercises/ex_anim2/h2b-task111(11) |
| `editor_create_animation` | editor | 18 | **YES** | YES | runs/_exercises/ex_anim/h2-task111(9) ; runs/_exercises/ex_anim2/h2b-task111(9) |
| `editor_create_animation_tree` | editor | 12 | **YES** | YES | runs/_exercises/ex_anim/h2-task111(6) ; runs/_exercises/ex_anim2/h2b-task111(6) |
| `editor_get_animation_info` | editor | 12 | **YES** | YES | runs/_exercises/ex_anim/h2-task111(6) ; runs/_exercises/ex_anim2/h2b-task111(6) |
| `editor_get_animation_tree_structure` | editor | 12 | **YES** | YES | runs/_exercises/ex_anim/h2-task111(6) ; runs/_exercises/ex_anim2/h2b-task111(6) |
| `editor_list_animations` | editor | 12 | **YES** | YES | runs/_exercises/ex_anim/h2-task111(6) ; runs/_exercises/ex_anim2/h2b-task111(6) |
| `editor_remove_animation` | editor | 12 | **YES** | YES | runs/_exercises/ex_anim/h2-task111(6) ; runs/_exercises/ex_anim2/h2b-task111(6) |
| `editor_remove_state_machine_state` | editor | 12 | **YES** | YES | runs/_exercises/ex_anim/h2-task111(6) ; runs/_exercises/ex_anim2/h2b-task111(6) |
| `editor_remove_state_machine_transition` | editor | 12 | **YES** | YES | runs/_exercises/ex_anim/h2-task111(6) ; runs/_exercises/ex_anim2/h2b-task111(6) |
| `editor_set_animation_keyframe` | editor | 12 | **YES** | YES | runs/_exercises/ex_anim/h2-task111(6) ; runs/_exercises/ex_anim2/h2b-task111(6) |
| `editor_set_animation_tree_parameter` | editor | 12 | **YES** | YES | runs/_exercises/ex_anim/h2-task111(6) ; runs/_exercises/ex_anim2/h2b-task111(6) |
| `editor_set_blend_tree_node` | editor | 12 | **YES** | YES | runs/_exercises/ex_anim/h2-task111(6) ; runs/_exercises/ex_anim2/h2b-task111(6) |

### H3 TileMap / GridMap

- 为何不可达（推断）：棋盘、迷宫、格点全部是**运行期新建的独立 `ColorRect`**（如 Pac-Man 的 125 颗豆子、Sokoban 的箱子、Match-3 的 8×8），20 个工程里没有 `TileMapLayer`、没有 `GridMap`、也没有 `TileSet` 资源，因此整族都没有作用对象
- 支撑证据（只读观察）：`tools/editor_tilemap_read.cpp`、`editor_tilemap_write.cpp`、`tilemap_shared.cpp`。**额外证据（契约自述）**：`editor_set_tilemap_cell` / `editor_set_tilemap_cells_in_rect` 的 `description` 明写「当前工具集没有任何『给 TileSet 添加 atlas source / texture / tile』的入口，所以在可预见的调用序列里本工具无法成功 —— 这是一处如实声明的能力缺口」；同一条 override 另注明该缺口句只挂在两个**写**工具上，`editor_get_tilemap_info/_used_cells/_cell` 与 `editor_remove_all_tilemap_cells` 不要求 source 存在（即有 TileMapLayer 时它们是可达的）

| tool | scope | 实测调用 | 漂移 | 改判 | 证据 |
|---|---|---|---|---|---|
| `editor_add_gridmap` | editor | 6 | **YES** | YES | runs/_exercises/ex_grid/h3-task111(6) |
| `editor_get_tilemap_cell` | editor | 6 | **YES** | YES | runs/_exercises/ex_grid/h3-task111(6) |
| `editor_get_tilemap_info` | editor | 6 | **YES** | YES | runs/_exercises/ex_grid/h3-task111(6) |
| `editor_get_tilemap_used_cells` | editor | 6 | **YES** | YES | runs/_exercises/ex_grid/h3-task111(6) |
| `editor_remove_all_tilemap_cells` | editor | 6 | **YES** | YES | runs/_exercises/ex_grid/h3-task111(6) |
| `editor_set_tilemap_cell` | editor | 10 | **YES** | YES | runs/_exercises/ex_grid/h3-task111(10) |
| `editor_set_tilemap_cells_in_rect` | editor | 6 | **YES** | YES | runs/_exercises/ex_grid/h3-task111(6) |

### H4 导航

- 为何不可达（推断）：需要先有 `NavigationRegion2D` + 烘焙过的 `NavigationMesh` + `NavigationAgent`；本循环的寻路是载荷自己手写的格点/路径算法（Tower Defense 的 101 格蛇形走廊由 ASCII 地图确定性导出，Python 复算 `PathHash`），没有任何导航资产
- 支撑证据（只读观察）：`tools/editor_navigation_read.cpp`、`editor_navigation_write.cpp`、`running_game_navigation_write.cpp`（`running_game_move_player_to_target` 就在这个文件里，前置条件即导航代理）

| tool | scope | 实测调用 | 漂移 | 改判 | 证据 |
|---|---|---|---|---|---|
| `editor_bake_navigation_mesh` | editor | 6 | **YES** | YES | runs/_exercises/ex_nav/h4-task113(6) |
| `editor_get_navigation_info` | editor | 6 | **YES** | YES | runs/_exercises/ex_nav/h4-task113(6) |
| `editor_set_navigation_layers` | editor | 7 | **YES** | YES | runs/_exercises/ex_nav/h4-task113(7) |
| `editor_setup_navigation_agent` | editor | 6 | **YES** | YES | runs/_exercises/ex_nav/h4-task113(6) |
| `editor_setup_navigation_region` | editor | 6 | **YES** | YES | runs/_exercises/ex_nav/h4-task113(6) |
| `running_game_move_player_to_target` | game | 6 | **YES** | YES | runs/_exercises/ex_nav/h4-task113(6) |

### H5 音频

- 为何不可达（推断）：20 款游戏**没有一个有声音**，没有 `AudioStreamPlayer`、没有 bus 布局，也没有音频资产
- 支撑证据（只读观察）：`tools/editor_audio_read.cpp`、`editor_audio_write.cpp`、`audio_shared.cpp`

| tool | scope | 实测调用 | 漂移 | 改判 | 证据 |
|---|---|---|---|---|---|
| `editor_add_audio_bus` | editor | 7 | **YES** | YES | runs/_exercises/ex_audio/h5-task113(7) |
| `editor_add_audio_bus_effect` | editor | 7 | **YES** | YES | runs/_exercises/ex_audio/h5-task113(7) |
| `editor_add_audio_player` | editor | 6 | **YES** | YES | runs/_exercises/ex_audio/h5-task113(6) |
| `editor_get_audio_bus_layout` | editor | 7 | **YES** | YES | runs/_exercises/ex_audio/h5-task113(7) |
| `editor_get_audio_info` | editor | 6 | **YES** | YES | runs/_exercises/ex_audio/h5-task113(6) |
| `editor_set_audio_bus_property` | editor | 8 | **YES** | YES | runs/_exercises/ex_audio/h5-task113(8) |

### H6 粒子

- 为何不可达（推断）：全部视觉证据是「节点位置/颜色 → 像素差」，没有任何 `GPUParticles2D` / 粒子材质 / 渐变
- 支撑证据（只读观察）：`tools/editor_particle_read.cpp`、`editor_particle_write.cpp`、`particle_shared.cpp`

| tool | scope | 实测调用 | 漂移 | 改判 | 证据 |
|---|---|---|---|---|---|
| `editor_create_particles` | editor | 8 | **YES** | YES | runs/_exercises/ex_particles/h6-task113(8) |
| `editor_get_particle_info` | editor | 7 | **YES** | YES | runs/_exercises/ex_particles/h6-task113(7) |
| `editor_set_particle_color_gradient` | editor | 9 | **YES** | YES | runs/_exercises/ex_particles/h6-task113(9) |
| `editor_set_particle_material` | editor | 8 | **YES** | YES | runs/_exercises/ex_particles/h6-task113(8) |
| `editor_set_particle_preset` | editor | 7 | **YES** | YES | runs/_exercises/ex_particles/h6-task113(7) |

### H7 编辑器 GUI 状态 / 编辑器自有播放与输入注入 / 编辑器侧测试运行

- 为何不可达（推断）：这类工具的输入是**编辑器进程自己的 GUI 状态**（当前选择、打开的脚本、Output 面板、对话框、已装插件）或**编辑器自己的播放器/输入队列**。本循环里编辑器端点只做「开场景 / 加节点 / 存场景 / 建脚本 / 编译 / 读错误」；所有行为验证都走游戏端点，且**刻意不用**编辑器侧输入注入（B2 说明：`editor_simulate_*` 注入的是编辑器进程的输入，不能用来驱动游戏进程 —— D59 / GDR-21 的边界）
- 支撑证据（只读观察）：`tools/editor_playback.cpp`、`editor_input_simulation.cpp`、`editor_profiling_read.cpp`、`editor_testing_read.cpp`、`editor_script_write.cpp`、`editor_read_scene_inspector.cpp`；`editor_get_test_report` / `editor_analyze_screenshot_diff` 需要「编辑器侧测试运行」，而本循环的测试运行发生在游戏端点

| tool | scope | 实测调用 | 漂移 | 改判 | 证据 |
|---|---|---|---|---|---|
| `editor_analyze_screenshot_diff` | editor | 0 | - | - | - |
| `editor_get_open_scripts` | editor | 12 | **YES** | YES | runs/_exercises/ex_scene/c23-task110(6) ; runs/_exercises/ex_scene2/c23-after-task110(6) |
| `editor_get_output_log` | editor | 36 | **YES** | YES | runs/_exercises/ex_scene/c23-task110(6) ; runs/_exercises/ex_scene2/c23-after-task110(6) ; runs/_exercises/ex_write/c4-task111(6) |
| `editor_get_performance_monitors` | editor | 12 | **YES** | YES | runs/_exercises/ex_scene/c23-task110(6) ; runs/_exercises/ex_scene2/c23-after-task110(6) |
| `editor_get_selection` | editor | 12 | **YES** | YES | runs/_exercises/ex_scene/c23-task110(6) ; runs/_exercises/ex_scene2/c23-after-task110(6) |
| `editor_get_test_report` | editor | 0 | - | - | - |
| `editor_play_scene` | editor | 0 | - | - | - |
| `editor_reload_plugin` | editor | 0 | - | - | - |
| `editor_remove_node_selection` | editor | 0 | - | - | - |
| `editor_remove_output_log` | editor | 0 | - | - | - |
| `editor_rescan_project_filesystem` | editor | 0 | - | - | - |
| `editor_set_auto_dismiss_dialogs` | editor | 0 | - | - | - |
| `editor_set_node_selection` | editor | 0 | - | - | - |
| `editor_simulate_input_action` | editor | 0 | - | - | - |
| `editor_simulate_input_sequence` | editor | 0 | - | - | - |
| `editor_simulate_key` | editor | 0 | - | - | - |
| `editor_simulate_mouse_click` | editor | 0 | - | - | - |
| `editor_simulate_mouse_move` | editor | 0 | - | - | - |
| `editor_stop_scene` | editor | 0 | - | - | - |

### H8 发布 / 导出 / Android 部署路径

- 为何不可达（推断）：循环的终点是「游戏跑起来 + 可复算证据」，从不打包、不导出、不连真机；`project_export_game` 甚至被契约 `_meta.excluded` 排除、`project_get_export_info` 等只在发布路径生效
- 支撑证据（只读观察）：`tools/project_export_read.cpp`、`os_android_read.cpp`、`os_android_write.cpp`、`project_android_read.cpp`；契约 `_meta.excluded = ["navigate_to","export_project"]`

| tool | scope | 实测调用 | 漂移 | 改判 | 证据 |
|---|---|---|---|---|---|
| `os_deploy_to_android_device` | both | 0 | - | - | - |
| `os_list_android_devices` | both | 0 | - | - | - |
| `project_get_android_preset_info` | both | 0 | - | - | - |
| `project_get_export_info` | both | 0 | - | - | - |
| `project_list_export_presets` | both | 0 | - | - | - |

### H9 运行期录放与特殊捕获（deferred / 条件态）

- 为何不可达（推断）：需要先进入某个**非默认运行态**才有效：`running_game_capture_frames` 需要开启逐帧捕获模式（本循环用的是整帧截图 `capture_screenshot`，298 次），信号发射捕获需要先注册监听，输入录制族需要「先 create → 再 play/stop」的三步会话。本循环的输入证据走的是**声明式 input action + 断言/场景驱动**，从未开过录制器
- 支撑证据（只读观察）：`tools/running_game_capture.cpp`、`input_recorder.cpp`、`running_game_input.cpp`；台账里所有输入证据都是 `editor_add_input_action` + `running_game_run_test_scenario`

| tool | scope | 实测调用 | 漂移 | 改判 | 证据 |
|---|---|---|---|---|---|
| `running_game_capture_frames` | game | 36 | **YES** | YES | runs/_exercises/ex_scene/c23-task110(6) ; runs/_exercises/ex_scene2/c23-after-task110(6) ; runs/_exercises/ex_write/c4-task111(6) |
| `running_game_capture_signal_emissions` | game | 36 | **YES** | YES | runs/_exercises/ex_scene/c23-task110(6) ; runs/_exercises/ex_scene2/c23-after-task110(6) ; runs/_exercises/ex_write/c4-task111(6) |
| `running_game_create_input_recording` | game | 7 | **YES** | YES | runs/_exercises/ex_rec/h9-task113(7) |
| `running_game_play_input_recording` | game | 7 | **YES** | YES | runs/_exercises/ex_rec/h9-task113(7) |
| `running_game_stop_input_recording` | game | 7 | **YES** | YES | runs/_exercises/ex_rec/h9-task113(7) |


#### 已改判的条目（推断被实测推翻，逐条留证）

| tool | 原类别 | 为什么可以删掉这条「不可达」 | 证据 |
|---|---|---|---|
| `editor_get_selection` | H7 | the editor's own GUI selection state is readable through the editor endpoint: no selection is a valid answer ({"count":0,"nodes":[],"top_only":false}). | `runs/_exercises/ex_scene/c23-task110/trace-editor.jsonl` |
| `editor_get_open_scripts` | H7 | the open-script list is answerable with none open ({"count":0,"scripts":[]}). | `runs/_exercises/ex_scene/c23-task110/trace-editor.jsonl` |
| `editor_get_output_log` | H7 | the editor's Output panel is readable in-process; the answer carries available/in_process/log_path plus the lines. | `runs/_exercises/ex_scene/c23-task110/trace-editor.jsonl` |
| `editor_get_performance_monitors` | H7 | 60 monitors reported from the editor process; no subsystem is missing. | `runs/_exercises/ex_scene/c23-task110/trace-editor.jsonl` |
| `running_game_capture_frames` | H9 | frame capture needs no pre-registered mode: count/frame_interval are enough and the frames come back inline (base64 PNG). | `runs/_exercises/ex_scene/c23-task110/trace-game.jsonl` |
| `running_game_capture_signal_emissions` | H9 | it registers the watch itself and reports what fired inside duration_ms (measured: 1 and 2 emissions for Tick.timeout). | `runs/_exercises/ex_scene/c23-task110/trace-game.jsonl` |
| `editor_add_mesh_instance` | H1 | the corpus has no 3D scene, but the family needs only a project that ships one: projects/_exercises/ex_3d carries scenes/probe3d.tscn (Node3D root + a MeshInstance3D with a BoxMesh) and every member of H1 then ran for real - the camera tools answer with the engine's own viewport read-back, the lighting/environment tools create their nodes, and editor_set_material_3d assigns a StandardMaterial3D to the surface. | `runs/_exercises/ex_3d/h1-task111/trace-editor.jsonl` |
| `editor_set_material_3d` | H1 | the corpus has no 3D scene, but the family needs only a project that ships one: projects/_exercises/ex_3d carries scenes/probe3d.tscn (Node3D root + a MeshInstance3D with a BoxMesh) and every member of H1 then ran for real - the camera tools answer with the engine's own viewport read-back, the lighting/environment tools create their nodes, and editor_set_material_3d assigns a StandardMaterial3D to the surface. | `runs/_exercises/ex_3d/h1-task111/trace-editor.jsonl` |
| `editor_setup_camera_3d` | H1 | the corpus has no 3D scene, but the family needs only a project that ships one: projects/_exercises/ex_3d carries scenes/probe3d.tscn (Node3D root + a MeshInstance3D with a BoxMesh) and every member of H1 then ran for real - the camera tools answer with the engine's own viewport read-back, the lighting/environment tools create their nodes, and editor_set_material_3d assigns a StandardMaterial3D to the surface. | `runs/_exercises/ex_3d/h1-task111/trace-editor.jsonl` |
| `editor_set_viewport_3d_camera` | H1 | the corpus has no 3D scene, but the family needs only a project that ships one: projects/_exercises/ex_3d carries scenes/probe3d.tscn (Node3D root + a MeshInstance3D with a BoxMesh) and every member of H1 then ran for real - the camera tools answer with the engine's own viewport read-back, the lighting/environment tools create their nodes, and editor_set_material_3d assigns a StandardMaterial3D to the surface. | `runs/_exercises/ex_3d/h1-task111/trace-editor.jsonl` |
| `editor_get_viewport_3d_camera` | H1 | the corpus has no 3D scene, but the family needs only a project that ships one: projects/_exercises/ex_3d carries scenes/probe3d.tscn (Node3D root + a MeshInstance3D with a BoxMesh) and every member of H1 then ran for real - the camera tools answer with the engine's own viewport read-back, the lighting/environment tools create their nodes, and editor_set_material_3d assigns a StandardMaterial3D to the surface. | `runs/_exercises/ex_3d/h1-task111/trace-editor.jsonl` |
| `editor_setup_lighting` | H1 | the corpus has no 3D scene, but the family needs only a project that ships one: projects/_exercises/ex_3d carries scenes/probe3d.tscn (Node3D root + a MeshInstance3D with a BoxMesh) and every member of H1 then ran for real - the camera tools answer with the engine's own viewport read-back, the lighting/environment tools create their nodes, and editor_set_material_3d assigns a StandardMaterial3D to the surface. | `runs/_exercises/ex_3d/h1-task111/trace-editor.jsonl` |
| `editor_setup_world_environment` | H1 | the corpus has no 3D scene, but the family needs only a project that ships one: projects/_exercises/ex_3d carries scenes/probe3d.tscn (Node3D root + a MeshInstance3D with a BoxMesh) and every member of H1 then ran for real - the camera tools answer with the engine's own viewport read-back, the lighting/environment tools create their nodes, and editor_set_material_3d assigns a StandardMaterial3D to the surface. | `runs/_exercises/ex_3d/h1-task111/trace-editor.jsonl` |
| `editor_create_animation` | H2 | the corpus drives motion with its own integer kinematics, but the family needs only an AnimationPlayer with a default library plus a node for a track to address: projects/_exercises/ex_anim2 carries scenes/anim.tscn (AnimRoot / Target / Player). All 14 members ran: 8 animations, 3 value tracks with keys, 5 AnimationTrees whose root the tool makes an AnimationNodeStateMachine, 11 states, 10 transitions, 5 blend-tree nodes and 5 parameter writes, each with a boundary probe. | `runs/_exercises/ex_anim2/h2b-task111/trace-editor.jsonl` |
| `editor_add_animation_track` | H2 | the corpus drives motion with its own integer kinematics, but the family needs only an AnimationPlayer with a default library plus a node for a track to address: projects/_exercises/ex_anim2 carries scenes/anim.tscn (AnimRoot / Target / Player). All 14 members ran: 8 animations, 3 value tracks with keys, 5 AnimationTrees whose root the tool makes an AnimationNodeStateMachine, 11 states, 10 transitions, 5 blend-tree nodes and 5 parameter writes, each with a boundary probe. | `runs/_exercises/ex_anim2/h2b-task111/trace-editor.jsonl` |
| `editor_set_animation_keyframe` | H2 | the corpus drives motion with its own integer kinematics, but the family needs only an AnimationPlayer with a default library plus a node for a track to address: projects/_exercises/ex_anim2 carries scenes/anim.tscn (AnimRoot / Target / Player). All 14 members ran: 8 animations, 3 value tracks with keys, 5 AnimationTrees whose root the tool makes an AnimationNodeStateMachine, 11 states, 10 transitions, 5 blend-tree nodes and 5 parameter writes, each with a boundary probe. | `runs/_exercises/ex_anim2/h2b-task111/trace-editor.jsonl` |
| `editor_remove_animation` | H2 | the corpus drives motion with its own integer kinematics, but the family needs only an AnimationPlayer with a default library plus a node for a track to address: projects/_exercises/ex_anim2 carries scenes/anim.tscn (AnimRoot / Target / Player). All 14 members ran: 8 animations, 3 value tracks with keys, 5 AnimationTrees whose root the tool makes an AnimationNodeStateMachine, 11 states, 10 transitions, 5 blend-tree nodes and 5 parameter writes, each with a boundary probe. | `runs/_exercises/ex_anim2/h2b-task111/trace-editor.jsonl` |
| `editor_list_animations` | H2 | the corpus drives motion with its own integer kinematics, but the family needs only an AnimationPlayer with a default library plus a node for a track to address: projects/_exercises/ex_anim2 carries scenes/anim.tscn (AnimRoot / Target / Player). All 14 members ran: 8 animations, 3 value tracks with keys, 5 AnimationTrees whose root the tool makes an AnimationNodeStateMachine, 11 states, 10 transitions, 5 blend-tree nodes and 5 parameter writes, each with a boundary probe. | `runs/_exercises/ex_anim2/h2b-task111/trace-editor.jsonl` |
| `editor_get_animation_info` | H2 | the corpus drives motion with its own integer kinematics, but the family needs only an AnimationPlayer with a default library plus a node for a track to address: projects/_exercises/ex_anim2 carries scenes/anim.tscn (AnimRoot / Target / Player). All 14 members ran: 8 animations, 3 value tracks with keys, 5 AnimationTrees whose root the tool makes an AnimationNodeStateMachine, 11 states, 10 transitions, 5 blend-tree nodes and 5 parameter writes, each with a boundary probe. | `runs/_exercises/ex_anim2/h2b-task111/trace-editor.jsonl` |
| `editor_create_animation_tree` | H2 | the corpus drives motion with its own integer kinematics, but the family needs only an AnimationPlayer with a default library plus a node for a track to address: projects/_exercises/ex_anim2 carries scenes/anim.tscn (AnimRoot / Target / Player). All 14 members ran: 8 animations, 3 value tracks with keys, 5 AnimationTrees whose root the tool makes an AnimationNodeStateMachine, 11 states, 10 transitions, 5 blend-tree nodes and 5 parameter writes, each with a boundary probe. | `runs/_exercises/ex_anim2/h2b-task111/trace-editor.jsonl` |
| `editor_get_animation_tree_structure` | H2 | the corpus drives motion with its own integer kinematics, but the family needs only an AnimationPlayer with a default library plus a node for a track to address: projects/_exercises/ex_anim2 carries scenes/anim.tscn (AnimRoot / Target / Player). All 14 members ran: 8 animations, 3 value tracks with keys, 5 AnimationTrees whose root the tool makes an AnimationNodeStateMachine, 11 states, 10 transitions, 5 blend-tree nodes and 5 parameter writes, each with a boundary probe. | `runs/_exercises/ex_anim2/h2b-task111/trace-editor.jsonl` |
| `editor_add_state_machine_state` | H2 | the corpus drives motion with its own integer kinematics, but the family needs only an AnimationPlayer with a default library plus a node for a track to address: projects/_exercises/ex_anim2 carries scenes/anim.tscn (AnimRoot / Target / Player). All 14 members ran: 8 animations, 3 value tracks with keys, 5 AnimationTrees whose root the tool makes an AnimationNodeStateMachine, 11 states, 10 transitions, 5 blend-tree nodes and 5 parameter writes, each with a boundary probe. | `runs/_exercises/ex_anim2/h2b-task111/trace-editor.jsonl` |
| `editor_add_state_machine_transition` | H2 | the corpus drives motion with its own integer kinematics, but the family needs only an AnimationPlayer with a default library plus a node for a track to address: projects/_exercises/ex_anim2 carries scenes/anim.tscn (AnimRoot / Target / Player). All 14 members ran: 8 animations, 3 value tracks with keys, 5 AnimationTrees whose root the tool makes an AnimationNodeStateMachine, 11 states, 10 transitions, 5 blend-tree nodes and 5 parameter writes, each with a boundary probe. | `runs/_exercises/ex_anim2/h2b-task111/trace-editor.jsonl` |
| `editor_remove_state_machine_state` | H2 | the corpus drives motion with its own integer kinematics, but the family needs only an AnimationPlayer with a default library plus a node for a track to address: projects/_exercises/ex_anim2 carries scenes/anim.tscn (AnimRoot / Target / Player). All 14 members ran: 8 animations, 3 value tracks with keys, 5 AnimationTrees whose root the tool makes an AnimationNodeStateMachine, 11 states, 10 transitions, 5 blend-tree nodes and 5 parameter writes, each with a boundary probe. | `runs/_exercises/ex_anim2/h2b-task111/trace-editor.jsonl` |
| `editor_remove_state_machine_transition` | H2 | the corpus drives motion with its own integer kinematics, but the family needs only an AnimationPlayer with a default library plus a node for a track to address: projects/_exercises/ex_anim2 carries scenes/anim.tscn (AnimRoot / Target / Player). All 14 members ran: 8 animations, 3 value tracks with keys, 5 AnimationTrees whose root the tool makes an AnimationNodeStateMachine, 11 states, 10 transitions, 5 blend-tree nodes and 5 parameter writes, each with a boundary probe. | `runs/_exercises/ex_anim2/h2b-task111/trace-editor.jsonl` |
| `editor_set_blend_tree_node` | H2 | the corpus drives motion with its own integer kinematics, but the family needs only an AnimationPlayer with a default library plus a node for a track to address: projects/_exercises/ex_anim2 carries scenes/anim.tscn (AnimRoot / Target / Player). All 14 members ran: 8 animations, 3 value tracks with keys, 5 AnimationTrees whose root the tool makes an AnimationNodeStateMachine, 11 states, 10 transitions, 5 blend-tree nodes and 5 parameter writes, each with a boundary probe. | `runs/_exercises/ex_anim2/h2b-task111/trace-editor.jsonl` |
| `editor_set_animation_tree_parameter` | H2 | the corpus drives motion with its own integer kinematics, but the family needs only an AnimationPlayer with a default library plus a node for a track to address: projects/_exercises/ex_anim2 carries scenes/anim.tscn (AnimRoot / Target / Player). All 14 members ran: 8 animations, 3 value tracks with keys, 5 AnimationTrees whose root the tool makes an AnimationNodeStateMachine, 11 states, 10 transitions, 5 blend-tree nodes and 5 parameter writes, each with a boundary probe. | `runs/_exercises/ex_anim2/h2b-task111/trace-editor.jsonl` |
| `editor_add_gridmap` | H3 | the write half's own contract said the caller must supply a TileSet that already holds a TileSetAtlasSource, and none of the 20 games does. projects/_exercises/ex_grid supplies exactly that (assets/tileset.tres + scenes/grid.tscn, built by mk_probe.gd from the engine's own ResourceSaver, plus assets/meshlib.tres for editor_add_gridmap). With it, editor_set_tilemap_cell and editor_set_tilemap_cells_in_rect succeed - the exact precondition the description names - and the readers report the cells back. | `runs/_exercises/ex_grid/h3-task111/trace-editor.jsonl` |
| `editor_get_tilemap_cell` | H3 | the write half's own contract said the caller must supply a TileSet that already holds a TileSetAtlasSource, and none of the 20 games does. projects/_exercises/ex_grid supplies exactly that (assets/tileset.tres + scenes/grid.tscn, built by mk_probe.gd from the engine's own ResourceSaver, plus assets/meshlib.tres for editor_add_gridmap). With it, editor_set_tilemap_cell and editor_set_tilemap_cells_in_rect succeed - the exact precondition the description names - and the readers report the cells back. | `runs/_exercises/ex_grid/h3-task111/trace-editor.jsonl` |
| `editor_get_tilemap_info` | H3 | the write half's own contract said the caller must supply a TileSet that already holds a TileSetAtlasSource, and none of the 20 games does. projects/_exercises/ex_grid supplies exactly that (assets/tileset.tres + scenes/grid.tscn, built by mk_probe.gd from the engine's own ResourceSaver, plus assets/meshlib.tres for editor_add_gridmap). With it, editor_set_tilemap_cell and editor_set_tilemap_cells_in_rect succeed - the exact precondition the description names - and the readers report the cells back. | `runs/_exercises/ex_grid/h3-task111/trace-editor.jsonl` |
| `editor_get_tilemap_used_cells` | H3 | the write half's own contract said the caller must supply a TileSet that already holds a TileSetAtlasSource, and none of the 20 games does. projects/_exercises/ex_grid supplies exactly that (assets/tileset.tres + scenes/grid.tscn, built by mk_probe.gd from the engine's own ResourceSaver, plus assets/meshlib.tres for editor_add_gridmap). With it, editor_set_tilemap_cell and editor_set_tilemap_cells_in_rect succeed - the exact precondition the description names - and the readers report the cells back. | `runs/_exercises/ex_grid/h3-task111/trace-editor.jsonl` |
| `editor_remove_all_tilemap_cells` | H3 | the write half's own contract said the caller must supply a TileSet that already holds a TileSetAtlasSource, and none of the 20 games does. projects/_exercises/ex_grid supplies exactly that (assets/tileset.tres + scenes/grid.tscn, built by mk_probe.gd from the engine's own ResourceSaver, plus assets/meshlib.tres for editor_add_gridmap). With it, editor_set_tilemap_cell and editor_set_tilemap_cells_in_rect succeed - the exact precondition the description names - and the readers report the cells back. | `runs/_exercises/ex_grid/h3-task111/trace-editor.jsonl` |
| `editor_set_tilemap_cell` | H3 | the write half's own contract said the caller must supply a TileSet that already holds a TileSetAtlasSource, and none of the 20 games does. projects/_exercises/ex_grid supplies exactly that (assets/tileset.tres + scenes/grid.tscn, built by mk_probe.gd from the engine's own ResourceSaver, plus assets/meshlib.tres for editor_add_gridmap). With it, editor_set_tilemap_cell and editor_set_tilemap_cells_in_rect succeed - the exact precondition the description names - and the readers report the cells back. | `runs/_exercises/ex_grid/h3-task111/trace-editor.jsonl` |
| `editor_set_tilemap_cells_in_rect` | H3 | the write half's own contract said the caller must supply a TileSet that already holds a TileSetAtlasSource, and none of the 20 games does. projects/_exercises/ex_grid supplies exactly that (assets/tileset.tres + scenes/grid.tscn, built by mk_probe.gd from the engine's own ResourceSaver, plus assets/meshlib.tres for editor_add_gridmap). With it, editor_set_tilemap_cell and editor_set_tilemap_cells_in_rect succeed - the exact precondition the description names - and the readers report the cells back. | `runs/_exercises/ex_grid/h3-task111/trace-editor.jsonl` |
| `editor_bake_navigation_mesh` | H4 | the corpus has no navigation data, but the family needs only a project that ships a NavigationRegion2D with an outline-bearing NavigationPolygon plus a player: projects/_exercises/ex_nav carries scenes/main.tscn built by the engine's own API (mk_probe.gd). All six members ran for real: editor_setup_navigation_region / editor_setup_navigation_agent create their nodes, editor_set_navigation_layers writes the mask editor_get_navigation_info reads back, editor_bake_navigation_mesh really baked (the first bake moved 155978 pixels in the editor viewport and reported baked:true with polygon_count 1), and running_game_move_player_to_target moved the player along the engine's own NavigationServer path in all five calls (distance_traveled 178.1/399.3/181.4/166.6/461.2). | `runs/_exercises/ex_nav/h4-task113/trace-editor.jsonl` |
| `editor_get_navigation_info` | H4 | the corpus has no navigation data, but the family needs only a project that ships a NavigationRegion2D with an outline-bearing NavigationPolygon plus a player: projects/_exercises/ex_nav carries scenes/main.tscn built by the engine's own API (mk_probe.gd). All six members ran for real: editor_setup_navigation_region / editor_setup_navigation_agent create their nodes, editor_set_navigation_layers writes the mask editor_get_navigation_info reads back, editor_bake_navigation_mesh really baked (the first bake moved 155978 pixels in the editor viewport and reported baked:true with polygon_count 1), and running_game_move_player_to_target moved the player along the engine's own NavigationServer path in all five calls (distance_traveled 178.1/399.3/181.4/166.6/461.2). | `runs/_exercises/ex_nav/h4-task113/trace-editor.jsonl` |
| `editor_set_navigation_layers` | H4 | the corpus has no navigation data, but the family needs only a project that ships a NavigationRegion2D with an outline-bearing NavigationPolygon plus a player: projects/_exercises/ex_nav carries scenes/main.tscn built by the engine's own API (mk_probe.gd). All six members ran for real: editor_setup_navigation_region / editor_setup_navigation_agent create their nodes, editor_set_navigation_layers writes the mask editor_get_navigation_info reads back, editor_bake_navigation_mesh really baked (the first bake moved 155978 pixels in the editor viewport and reported baked:true with polygon_count 1), and running_game_move_player_to_target moved the player along the engine's own NavigationServer path in all five calls (distance_traveled 178.1/399.3/181.4/166.6/461.2). | `runs/_exercises/ex_nav/h4-task113/trace-editor.jsonl` |
| `editor_setup_navigation_agent` | H4 | the corpus has no navigation data, but the family needs only a project that ships a NavigationRegion2D with an outline-bearing NavigationPolygon plus a player: projects/_exercises/ex_nav carries scenes/main.tscn built by the engine's own API (mk_probe.gd). All six members ran for real: editor_setup_navigation_region / editor_setup_navigation_agent create their nodes, editor_set_navigation_layers writes the mask editor_get_navigation_info reads back, editor_bake_navigation_mesh really baked (the first bake moved 155978 pixels in the editor viewport and reported baked:true with polygon_count 1), and running_game_move_player_to_target moved the player along the engine's own NavigationServer path in all five calls (distance_traveled 178.1/399.3/181.4/166.6/461.2). | `runs/_exercises/ex_nav/h4-task113/trace-editor.jsonl` |
| `editor_setup_navigation_region` | H4 | the corpus has no navigation data, but the family needs only a project that ships a NavigationRegion2D with an outline-bearing NavigationPolygon plus a player: projects/_exercises/ex_nav carries scenes/main.tscn built by the engine's own API (mk_probe.gd). All six members ran for real: editor_setup_navigation_region / editor_setup_navigation_agent create their nodes, editor_set_navigation_layers writes the mask editor_get_navigation_info reads back, editor_bake_navigation_mesh really baked (the first bake moved 155978 pixels in the editor viewport and reported baked:true with polygon_count 1), and running_game_move_player_to_target moved the player along the engine's own NavigationServer path in all five calls (distance_traveled 178.1/399.3/181.4/166.6/461.2). | `runs/_exercises/ex_nav/h4-task113/trace-editor.jsonl` |
| `running_game_move_player_to_target` | H4 | the corpus has no navigation data, but the family needs only a project that ships a NavigationRegion2D with an outline-bearing NavigationPolygon plus a player: projects/_exercises/ex_nav carries scenes/main.tscn built by the engine's own API (mk_probe.gd). All six members ran for real: editor_setup_navigation_region / editor_setup_navigation_agent create their nodes, editor_set_navigation_layers writes the mask editor_get_navigation_info reads back, editor_bake_navigation_mesh really baked (the first bake moved 155978 pixels in the editor viewport and reported baked:true with polygon_count 1), and running_game_move_player_to_target moved the player along the engine's own NavigationServer path in all five calls (distance_traveled 178.1/399.3/181.4/166.6/461.2). | `runs/_exercises/ex_nav/h4-task113/trace-game.jsonl` |
| `editor_add_audio_bus` | H5 | no game has any sound, but the family's subjects are the editor process's own AudioServer and one AudioStreamPlayer2D node: projects/_exercises/ex_audio ships five real RIFF WAVE assets (generated by the TASK-113 generator and imported by --import). All six members ran: five buses were added (Music/Sfx/Ambient/Voice/Ui), five effects attached to them, five players created, and editor_get_audio_bus_layout / editor_get_audio_info read the engine's own bus list (including the volume_db -6.0 editor_set_audio_bus_property wrote) back. | `runs/_exercises/ex_audio/h5-task113/trace-editor.jsonl` |
| `editor_add_audio_bus_effect` | H5 | no game has any sound, but the family's subjects are the editor process's own AudioServer and one AudioStreamPlayer2D node: projects/_exercises/ex_audio ships five real RIFF WAVE assets (generated by the TASK-113 generator and imported by --import). All six members ran: five buses were added (Music/Sfx/Ambient/Voice/Ui), five effects attached to them, five players created, and editor_get_audio_bus_layout / editor_get_audio_info read the engine's own bus list (including the volume_db -6.0 editor_set_audio_bus_property wrote) back. | `runs/_exercises/ex_audio/h5-task113/trace-editor.jsonl` |
| `editor_add_audio_player` | H5 | no game has any sound, but the family's subjects are the editor process's own AudioServer and one AudioStreamPlayer2D node: projects/_exercises/ex_audio ships five real RIFF WAVE assets (generated by the TASK-113 generator and imported by --import). All six members ran: five buses were added (Music/Sfx/Ambient/Voice/Ui), five effects attached to them, five players created, and editor_get_audio_bus_layout / editor_get_audio_info read the engine's own bus list (including the volume_db -6.0 editor_set_audio_bus_property wrote) back. | `runs/_exercises/ex_audio/h5-task113/trace-editor.jsonl` |
| `editor_get_audio_bus_layout` | H5 | no game has any sound, but the family's subjects are the editor process's own AudioServer and one AudioStreamPlayer2D node: projects/_exercises/ex_audio ships five real RIFF WAVE assets (generated by the TASK-113 generator and imported by --import). All six members ran: five buses were added (Music/Sfx/Ambient/Voice/Ui), five effects attached to them, five players created, and editor_get_audio_bus_layout / editor_get_audio_info read the engine's own bus list (including the volume_db -6.0 editor_set_audio_bus_property wrote) back. | `runs/_exercises/ex_audio/h5-task113/trace-editor.jsonl` |
| `editor_get_audio_info` | H5 | no game has any sound, but the family's subjects are the editor process's own AudioServer and one AudioStreamPlayer2D node: projects/_exercises/ex_audio ships five real RIFF WAVE assets (generated by the TASK-113 generator and imported by --import). All six members ran: five buses were added (Music/Sfx/Ambient/Voice/Ui), five effects attached to them, five players created, and editor_get_audio_bus_layout / editor_get_audio_info read the engine's own bus list (including the volume_db -6.0 editor_set_audio_bus_property wrote) back. | `runs/_exercises/ex_audio/h5-task113/trace-editor.jsonl` |
| `editor_set_audio_bus_property` | H5 | no game has any sound, but the family's subjects are the editor process's own AudioServer and one AudioStreamPlayer2D node: projects/_exercises/ex_audio ships five real RIFF WAVE assets (generated by the TASK-113 generator and imported by --import). All six members ran: five buses were added (Music/Sfx/Ambient/Voice/Ui), five effects attached to them, five players created, and editor_get_audio_bus_layout / editor_get_audio_info read the engine's own bus list (including the volume_db -6.0 editor_set_audio_bus_property wrote) back. | `runs/_exercises/ex_audio/h5-task113/trace-editor.jsonl` |
| `editor_create_particles` | H6 | the corpus has no particles, but the family needs only GPUParticles2D nodes and a ParticleProcessMaterial: projects/_exercises/ex_particles ships a scene with one GPUParticles2D and editor_create_particles makes five more. All five members ran: two presets (fire/smoke/...), five process-material parameter writes and five colour gradients, each read back by editor_get_particle_info (params, colors and color_stop_count). | `runs/_exercises/ex_particles/h6-task113/trace-editor.jsonl` |
| `editor_get_particle_info` | H6 | the corpus has no particles, but the family needs only GPUParticles2D nodes and a ParticleProcessMaterial: projects/_exercises/ex_particles ships a scene with one GPUParticles2D and editor_create_particles makes five more. All five members ran: two presets (fire/smoke/...), five process-material parameter writes and five colour gradients, each read back by editor_get_particle_info (params, colors and color_stop_count). | `runs/_exercises/ex_particles/h6-task113/trace-editor.jsonl` |
| `editor_set_particle_color_gradient` | H6 | the corpus has no particles, but the family needs only GPUParticles2D nodes and a ParticleProcessMaterial: projects/_exercises/ex_particles ships a scene with one GPUParticles2D and editor_create_particles makes five more. All five members ran: two presets (fire/smoke/...), five process-material parameter writes and five colour gradients, each read back by editor_get_particle_info (params, colors and color_stop_count). | `runs/_exercises/ex_particles/h6-task113/trace-editor.jsonl` |
| `editor_set_particle_material` | H6 | the corpus has no particles, but the family needs only GPUParticles2D nodes and a ParticleProcessMaterial: projects/_exercises/ex_particles ships a scene with one GPUParticles2D and editor_create_particles makes five more. All five members ran: two presets (fire/smoke/...), five process-material parameter writes and five colour gradients, each read back by editor_get_particle_info (params, colors and color_stop_count). | `runs/_exercises/ex_particles/h6-task113/trace-editor.jsonl` |
| `editor_set_particle_preset` | H6 | the corpus has no particles, but the family needs only GPUParticles2D nodes and a ParticleProcessMaterial: projects/_exercises/ex_particles ships a scene with one GPUParticles2D and editor_create_particles makes five more. All five members ran: two presets (fire/smoke/...), five process-material parameter writes and five colour gradients, each read back by editor_get_particle_info (params, colors and color_stop_count). | `runs/_exercises/ex_particles/h6-task113/trace-editor.jsonl` |
| `running_game_create_input_recording` | H9 | input recording needs the three-step create -> play/stop session, which the corpus never opened: projects/_exercises/ex_rec carries a player script whose motion is driven by the key events the replay injects. All three members ran five times each: every create/stop round captured the two key events the explicit replay injected (event_count 2), and the final create -> stop -> play chain (no `events` argument) moved the player from x=100 to x=151 with a recomputed pixel diff of 1152 pixels - the replay really drives the running game. | `runs/_exercises/ex_rec/h9-task113/trace-game.jsonl` |
| `running_game_play_input_recording` | H9 | input recording needs the three-step create -> play/stop session, which the corpus never opened: projects/_exercises/ex_rec carries a player script whose motion is driven by the key events the replay injects. All three members ran five times each: every create/stop round captured the two key events the explicit replay injected (event_count 2), and the final create -> stop -> play chain (no `events` argument) moved the player from x=100 to x=151 with a recomputed pixel diff of 1152 pixels - the replay really drives the running game. | `runs/_exercises/ex_rec/h9-task113/trace-game.jsonl` |
| `running_game_stop_input_recording` | H9 | input recording needs the three-step create -> play/stop session, which the corpus never opened: projects/_exercises/ex_rec carries a player script whose motion is driven by the key events the replay injects. All three members ran five times each: every create/stop round captured the two key events the explicit replay injected (event_count 2), and the final create -> stop -> play chain (no `events` argument) moved the player from x=100 to x=151 with a recomputed pixel diff of 1152 pixels - the replay really drives the running game. | `runs/_exercises/ex_rec/h9-task113/trace-game.jsonl` |

## 5. 本轮批次进度（--targets）

批次 **0** 条：达标 **0**、计数达标缺证据 **0**、未达 **0**。

`facts` 列 = trace 里字段齐备的调用数 / 总调用数（request_id、tool、args、times、result、capture、scene_evidence、file_effect、error_data 全部在场）。

| tool | scope | 累计 | 有效 | 边界 | facts | 状态 | 证据 |
|---|---|---|---|---|---|---|---|

## 输入指纹

| 文件 | 字节 | sha256 |
|---|---|---|
| `dist\review_data.json` | 25937 | `E9CF20F5039511C99C488C149D90E2938BBA4F3153DEA41C88D72FF70B624F77` |
| `godot\modules\mcp_server\docs\tool-rename-map.json` | 70917 | `2F552719F6A23FE328DF0A2944C6048824C1B2A750AEBC0FE2CABBCD3529C2BD` |
| `godot\modules\mcp_server\docs\tools_list.renamed.json` | 154272 | `FD00C75E5174EC923D5A91C0323AFA0804F523B385EAE3D4F78D8C71E1F895DF` |

