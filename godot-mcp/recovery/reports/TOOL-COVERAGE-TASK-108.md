# TOOL-COVERAGE-TASK-108 — contract-wide tool coverage across the 20-game loop

> **只读测量报告。** 本任务只读取 `runs/`、`godot/modules/mcp_server/docs/`、`dist/`、`GAME-LOOP-LOG.md` 与台账脚本，
> 未修改任何被测量文件，也没有改写 `runs/`、`projects/`、模块源码的任何一个字节；本文件是唯一被写入的文件。
> 所有数字都是自己从 trace 原文与契约原文重算的，没有转抄任何报告表格。
> （过程声明：测量中曾用一个脚本误建 `recovery/reports/_h.tmp` 空文件，已在同一步删除，未触碰任何被测量文件。）

## 0. 一句话结论

**回答「是否每个工具都 ≥ 5 次」：不是。** 在 20 个**最终轮**里，177 条契约工具中只有 **25 条 ≥5 次**，
**2 条**落在 `1-4` 次，**150 条 0 次**。把 `runs/` 下**全部 81 个 run 目录**（含历史中间轮与探针）一起算，
也只有 **27 条 ≥5 次**、**2 条 1-4 次**、**148 条 0 次**。

20 款游戏的试测循环实际上是一条**很窄的工具带**：最终轮 2612 次调用只碰到 **27 个工具名**（占契约 15.3%），
其中前 5 个工具就吃掉 **83.4%** 的调用量（`running_game_assert_node_state` 一条占 50.1%）。

输入指纹（本次实测，非转抄）：

| 输入 | 字节 | sha256 |
|---|---|---|
| `godot/modules/mcp_server/docs/tools_list.renamed.json`（契约） | 153330 | `BD68E80472C8E15D674C45BF5816EE708EA08CF71F209A0E0114373D6067B640` |
| `godot/modules/mcp_server/docs/tool-rename-map.json`（scope 来源） | 70917 | `2F552719F6A23FE328DF0A2944C6048824C1B2A750AEBC0FE2CABBCD3529C2BD` |
| `dist/review_data.json`（20 个最终 tag 来源） | 25937 | `E9CF20F5039511C99C488C149D90E2938BBA4F3153DEA41C88D72FF70B624F77` |
| `GAME-LOOP-LOG.md`（台账，用于交叉核对） | 155384 | `2668AACF3C7615EA7411B0E5655B15A6D55CE83B6A1FD7CDF72232F878D5742C` |

trace 语料实测规模：**81 个 run 目录 / 140 个 `trace-*.jsonl` / 6618 条 `tools/call` 行 / 0 行解析失败**。

## 1. Method and accounting rules

### 1.1 契约工具名从哪里来

`godot/modules/mcp_server/docs/tools_list.renamed.json` 是 MCP `tools/list` 的应答体（`id` / `jsonrpc` / `result` / `_meta`）。
工具名逐个取自 `result.tools[i].name`，共 **177** 条。该文件**自己不携带 scope**（每个 tool 对象只有 `description` /
`inputSchema` / `name` 三个键），所以任务书里说的「177 条工具名与 scope」是把两份东西合起来读的。

### 1.2 scope 怎么来

按 `name` 逐字 join 两个来源，**177/177 全部命中**：

1. `docs/tool-rename-map.json` 的 `tools[]`，每条有 `new_name` 与 `scope`（174 条，`convention.scope_enum = ["editor","game","both"]`）。
   注意 174 条里有 1 条 `merged` 重复（`get_editor_performance` → `editor_get_performance_monitors`，`merged_into` 指向另一条），
   所以能唯一命中的 `new_name` 是 173 个。
2. `docs/tool-groups.json` + `tool-groups-b2..b5.json` + `tool-groups-added.json` 的 `groups[].tools[]`，组级 `scope`。
   map 里缺的 6 条**全是 `_meta.added_tools`**（新增工具，不在 rename map 里），由 `tool-groups-added.json` 补齐。

结果：`editor = 104`、`both = 50`、`game = 23`（合计 177）。这与 `docs/reports/evidence/task075/gate1_contract_subset.txt`
里 `check_contract_subset.ps1` 自报的 `scope : editor-only=104 game-only=23 both/shared=50` **逐字一致**，两条独立路径互证。

**scope 语义**（`docs/TOOL-NAMING.md:167`）：`editor` = 只出现在编辑器端点（9888）；`game` = 只出现在游戏端点（9889）；
`both` = 两端点都注册。本循环**两个端点都用了**，所以没有任何工具是「因为端点没开而不可达」。

### 1.3 trace 怎么提取工具名

```
runs/**/trace-*.jsonl   →   逐行 json.loads   →   只保留 method == "tools/call"   →   取该行顶层 "tool" 字段
```

* 工具名取**行上的 `tool` 字段**，不是从 `args` 里解析、也不是从 sidecar 文件里回读 —— 所以参数被截断（`args_truncated`）
  或被挪进 sidecar（`args_sidecar`）都**不影响计数**。
* 每个文件里还有 `event: "trace_opened"` 140 行、`event: "capture"` 6618 行、`method: "tools/list"` 25 行。
  **只有 `tools/call` 计入**；`tools/list` 是建连时的契约握手，不是工具调用（这一条正是 review_data 的数字比本报告多 1 的原因，见 §6.3）。
* 140 个文件、6758 条非 `method` 行（open/capture）、0 条 JSON 解析失败、0 条 `tools/call` 缺 `tool` 字段、0 条重复行。

### 1.4 最终轮怎么认定

以 `dist/review_data.json` 的 `games[]` 为准：它恰好 **20 个条目**，每条给出 `game` 与 `run_tag`（外加 `run_path`），
这就是「20 个最终 tag」。逐条解析成 `runs/<game>/<run_tag>/trace-{editor,game}.jsonl`（每个最终目录恰好 2 个 trace 文件，合计 40 个）。

选 `review_data.json` 而不是从 `GAME-LOOP-LOG.md` 正文里正则抓路径的理由：台账某些行的「证据路径」列同时列了历史轮与最终轮
（例如 Pong 行写 `runs\pong\pong-run{1..4}\`、`runs\pong\pong-task092\`，而最终 tag 是 `pong-clean-task097`），
靠文本抓取会歧义；`review_data.json` 是审核包构建时**逐游戏选定**的那一个，语义唯一。两份来源交叉核对后一致（见 §6.7）。

### 1.5 「全部轮次」的口径

`runs/` 下递归全部 `trace-*.jsonl` = **81 个 run 目录 / 140 个文件 / 6618 行**。它**包含**最终轮的 2612 行，
额外多出的 **4006 行**来自：历史中间轮（`*-r1..r7`、`pong-run1..4`、`snake-task093*` 等）、
D-1/D-3 诊断探针（`pong/d3-before`、`pong/d3-after*`、`snake/task094-probe*`、`snake/task095-*`、`snake/task096-*`）、
X-1 对照（`match3/task103-x1-before|after`）以及 TASK-097 的 `*-clean-task097` 清理重放。

`runs/gates/` 下的 **20 个门跑子目录一个 trace 都没有**，完全不参与统计（不是 0 次，是「不在口径里」）。

## 2. (1) Contract total and scope split

- contract file: `godot/modules/mcp_server/docs/tools_list.renamed.json` -> `result.tools` = **177** tools
- scope is not stored in tools_list: it is joined by tool name from `docs/tool-rename-map.json` + the 6 manifests `docs/tool-groups*.json`
- editor = **104**, game = **23**, both = **50**
- cross-check: `docs/reports/evidence/task075/gate1_contract_subset.txt` prints `scope : editor-only=104 game-only=23 both/shared=50` - identical to the join above.

| # | tool | scope |
|---|---|---|
| 1 | `editor_add_animation_track` | editor |
| 2 | `editor_add_audio_bus` | editor |
| 3 | `editor_add_audio_bus_effect` | editor |
| 4 | `editor_add_audio_player` | editor |
| 5 | `editor_add_gridmap` | editor |
| 6 | `editor_add_input_action` | editor |
| 7 | `editor_add_mesh_instance` | editor |
| 8 | `editor_add_node` | editor |
| 9 | `editor_add_nodes_batch` | editor |
| 10 | `editor_add_raycast` | editor |
| 11 | `editor_add_resource_to_node_property` | editor |
| 12 | `editor_add_scene_instance` | editor |
| 13 | `editor_add_state_machine_state` | editor |
| 14 | `editor_add_state_machine_transition` | editor |
| 15 | `editor_analyze_screenshot_diff` | editor |
| 16 | `editor_analyze_signal_flow` | editor |
| 17 | `editor_bake_navigation_mesh` | editor |
| 18 | `editor_capture_screenshot` | editor |
| 19 | `editor_connect_signal` | editor |
| 20 | `editor_create_animation` | editor |
| 21 | `editor_create_animation_tree` | editor |
| 22 | `editor_create_particles` | editor |
| 23 | `editor_delete_node` | editor |
| 24 | `editor_disconnect_signal` | editor |
| 25 | `editor_duplicate_node` | editor |
| 26 | `editor_execute_gdscript` | editor |
| 27 | `editor_find_nodes_by_type` | editor |
| 28 | `editor_find_nodes_in_group` | editor |
| 29 | `editor_get_animation_info` | editor |
| 30 | `editor_get_animation_tree_structure` | editor |
| 31 | `editor_get_audio_bus_layout` | editor |
| 32 | `editor_get_audio_info` | editor |
| 33 | `editor_get_collision_info` | editor |
| 34 | `editor_get_errors` | editor |
| 35 | `editor_get_input_actions` | editor |
| 36 | `editor_get_navigation_info` | editor |
| 37 | `editor_get_node_groups` | editor |
| 38 | `editor_get_node_properties` | editor |
| 39 | `editor_get_node_signals` | editor |
| 40 | `editor_get_open_scripts` | editor |
| 41 | `editor_get_output_log` | editor |
| 42 | `editor_get_particle_info` | editor |
| 43 | `editor_get_performance_monitors` | editor |
| 44 | `editor_get_physics_layers` | editor |
| 45 | `editor_get_scene_tree` | editor |
| 46 | `editor_get_selection` | editor |
| 47 | `editor_get_test_report` | editor |
| 48 | `editor_get_tilemap_cell` | editor |
| 49 | `editor_get_tilemap_info` | editor |
| 50 | `editor_get_tilemap_used_cells` | editor |
| 51 | `editor_get_viewport_3d_camera` | editor |
| 52 | `editor_list_animations` | editor |
| 53 | `editor_list_signal_connections` | editor |
| 54 | `editor_open_scene` | editor |
| 55 | `editor_play_scene` | editor |
| 56 | `editor_reload_plugin` | editor |
| 57 | `editor_remove_all_tilemap_cells` | editor |
| 58 | `editor_remove_animation` | editor |
| 59 | `editor_remove_node_selection` | editor |
| 60 | `editor_remove_output_log` | editor |
| 61 | `editor_remove_state_machine_state` | editor |
| 62 | `editor_remove_state_machine_transition` | editor |
| 63 | `editor_rename_node` | editor |
| 64 | `editor_reparent_node` | editor |
| 65 | `editor_rescan_project_filesystem` | editor |
| 66 | `editor_save_scene` | editor |
| 67 | `editor_set_anchor_preset` | editor |
| 68 | `editor_set_animation_keyframe` | editor |
| 69 | `editor_set_animation_tree_parameter` | editor |
| 70 | `editor_set_audio_bus_property` | editor |
| 71 | `editor_set_auto_dismiss_dialogs` | editor |
| 72 | `editor_set_blend_tree_node` | editor |
| 73 | `editor_set_control_theme` | editor |
| 74 | `editor_set_material_3d` | editor |
| 75 | `editor_set_navigation_layers` | editor |
| 76 | `editor_set_node_groups` | editor |
| 77 | `editor_set_node_property` | editor |
| 78 | `editor_set_node_property_batch` | editor |
| 79 | `editor_set_node_property_updates` | editor |
| 80 | `editor_set_node_script` | editor |
| 81 | `editor_set_node_script_batch` | editor |
| 82 | `editor_set_node_selection` | editor |
| 83 | `editor_set_particle_color_gradient` | editor |
| 84 | `editor_set_particle_material` | editor |
| 85 | `editor_set_particle_preset` | editor |
| 86 | `editor_set_physics_layers` | editor |
| 87 | `editor_set_shader_material` | editor |
| 88 | `editor_set_shader_param` | editor |
| 89 | `editor_set_tilemap_cell` | editor |
| 90 | `editor_set_tilemap_cells_in_rect` | editor |
| 91 | `editor_set_viewport_3d_camera` | editor |
| 92 | `editor_setup_camera_3d` | editor |
| 93 | `editor_setup_collision_shape` | editor |
| 94 | `editor_setup_lighting` | editor |
| 95 | `editor_setup_navigation_agent` | editor |
| 96 | `editor_setup_navigation_region` | editor |
| 97 | `editor_setup_physics_body` | editor |
| 98 | `editor_setup_world_environment` | editor |
| 99 | `editor_simulate_input_action` | editor |
| 100 | `editor_simulate_input_sequence` | editor |
| 101 | `editor_simulate_key` | editor |
| 102 | `editor_simulate_mouse_click` | editor |
| 103 | `editor_simulate_mouse_move` | editor |
| 104 | `editor_stop_scene` | editor |
| 105 | `os_deploy_to_android_device` | both |
| 106 | `os_list_android_devices` | both |
| 107 | `project_add_autoload` | both |
| 108 | `project_analyze_scene_complexity` | both |
| 109 | `project_build_csharp` | both |
| 110 | `project_convert_path_to_uid` | both |
| 111 | `project_convert_uid_to_path` | both |
| 112 | `project_create_resource` | both |
| 113 | `project_create_scene_file` | both |
| 114 | `project_create_script` | both |
| 115 | `project_create_shader` | both |
| 116 | `project_create_theme` | both |
| 117 | `project_delete_scene_file` | both |
| 118 | `project_detect_circular_dependencies` | both |
| 119 | `project_edit_resource` | both |
| 120 | `project_edit_script` | both |
| 121 | `project_edit_shader` | both |
| 122 | `project_find_files_referencing_symbol` | both |
| 123 | `project_find_script_references` | both |
| 124 | `project_find_unused_resources` | both |
| 125 | `project_get_android_preset_info` | both |
| 126 | `project_get_export_info` | both |
| 127 | `project_get_filesystem_tree` | both |
| 128 | `project_get_info` | both |
| 129 | `project_get_resource_preview` | both |
| 130 | `project_get_scene_dependencies` | both |
| 131 | `project_get_scene_exports` | both |
| 132 | `project_get_settings` | both |
| 133 | `project_get_shader_params` | both |
| 134 | `project_get_statistics` | both |
| 135 | `project_get_theme_info` | both |
| 136 | `project_list_export_presets` | both |
| 137 | `project_list_scripts` | both |
| 138 | `project_read_resource` | both |
| 139 | `project_read_scene_file_content` | both |
| 140 | `project_read_script` | both |
| 141 | `project_read_shader` | both |
| 142 | `project_read_text_file` | both |
| 143 | `project_remove_autoload` | both |
| 144 | `project_search_file_contents` | both |
| 145 | `project_search_file_names` | both |
| 146 | `project_set_node_property_across_scenes` | both |
| 147 | `project_set_setting` | both |
| 148 | `project_set_theme_color` | both |
| 149 | `project_set_theme_constant` | both |
| 150 | `project_set_theme_font_size` | both |
| 151 | `project_set_theme_stylebox` | both |
| 152 | `project_validate_script` | both |
| 153 | `project_validate_scripts` | both |
| 154 | `project_write_text_file` | both |
| 155 | `running_game_assert_node_state` | game |
| 156 | `running_game_assert_screen_text` | game |
| 157 | `running_game_capture_frames` | game |
| 158 | `running_game_capture_screenshot` | game |
| 159 | `running_game_capture_signal_emissions` | game |
| 160 | `running_game_create_input_recording` | game |
| 161 | `running_game_execute_gdscript` | game |
| 162 | `running_game_find_nearby_nodes` | game |
| 163 | `running_game_find_node_when_available` | game |
| 164 | `running_game_find_nodes_by_script` | game |
| 165 | `running_game_find_ui_elements` | game |
| 166 | `running_game_get_autoload_node` | game |
| 167 | `running_game_get_node_properties` | game |
| 168 | `running_game_get_node_properties_batch` | game |
| 169 | `running_game_get_node_property_samples` | game |
| 170 | `running_game_get_scene_tree` | game |
| 171 | `running_game_move_player_to_target` | game |
| 172 | `running_game_play_input_recording` | game |
| 173 | `running_game_run_stress_test` | game |
| 174 | `running_game_run_test_scenario` | game |
| 175 | `running_game_set_node_property` | game |
| 176 | `running_game_simulate_button_click_by_text` | game |
| 177 | `running_game_stop_input_recording` | game |

## 3. (2) Per-tool calls over the 20 final runs

### 3.0 结论

20 个最终轮合计 **2612** 次 `tools/call`，只出现 **27 个不同的工具名**；契约的 177 条里有 **150 条一次都没被调用**。
「每个工具都 ≥5 次」这个命题在本循环里**不成立**，差得很远：达标率 **25/177 = 14.1%**。
（§6.2 还给出一次灵敏度检查：这 25 条里有 **8 条**的 `>=5` 只在 Pong / Breakout 两个目录达到。）

调用量高度集中（前 5 名占 83.4%）：

| 工具 | scope | 最终轮 | 占最终轮 |
|---|---|---|---|
| `running_game_assert_node_state` | game | 1308 | 50.1% |
| `running_game_execute_gdscript` | game | 668 | 25.6% |
| `running_game_capture_screenshot` | game | 102 | 3.9% |
| `editor_add_input_action` | editor | 52 | 2.0% |
| `running_game_get_node_property_samples` | game | 49 | 1.9% |

**这两个工具就是整条循环的引擎**：`assert_node_state`（把载荷属性当断言钉住）+ `execute_gdscript`（读回状态、采样、驱动测试）。
其余 22 个被用到的工具基本是「开场景 / 加节点 / 存场景 / 建脚本 / 编译 / 截图」的脚手架。

成功与否不影响本报告口径：2612 次里有 **37 次 `ok=false`**（`editor_add_nodes_batch` 18 次 —— D-3 的同名批量拒绝；
`running_game_assert_node_state` 17 次 —— 文件里声明过的「按设计失败」断言；另 2 个各 1 次），
2575 次 `ok=true`。计数口径是**调用次数**，失败调用同样计入。

### 3.1 scope 视角

| scope | 契约条数 | 最终轮被调用过 | 最终轮 ≥5 次 | 最终轮 0 次 |
|---|---|---|---|---|
| editor | 104 | 11 | 10 | 93 |
| both | 50 | 5 | 5 | 45 |
| game | 23 | 11 | 10 | 12 |
| 合计 | 177 | 27 | 25 | 150 |

`game` scope 的 23 条里被用了 11 条（47.8%，覆盖率最高），`both` 50 条里只用 5 条，
`editor` 104 条里只用 11 条 —— 编辑器侧被当作「建场景的最小写入口」，其余编辑能力整块闲置。


- final tag source: `dist/review_data.json` -> `games[].run_tag` (20 entries, one per game)
- total tools/call lines in the 20 final run dirs: **2612**
- distinct tools invoked: **27** of 177
- buckets over the 177 contract tools: 0x = **150**, 1-4x = **2**, >=5x = **25**

### 3.2 per-run call counts

| # | game | run_tag | trace files | tools/call lines |
|---|---|---|---|---|
| 1 | pong | `pong-clean-task097` | 2 | 74 |
| 2 | breakout | `breakout-clean-task097` | 2 | 89 |
| 3 | snake | `snake-task106-r1` | 2 | 53 |
| 4 | tetris | `tetris-task096-r2` | 2 | 42 |
| 5 | spaceinvaders | `si-task097-r1` | 2 | 59 |
| 6 | asteroids | `ast-task098-r2` | 2 | 71 |
| 7 | pacman | `pac-task098-r2` | 2 | 80 |
| 8 | frogger | `frog-task099-r1` | 2 | 90 |
| 9 | flappy | `flappy-task099-r2` | 2 | 92 |
| 10 | game2048 | `2048-task100-r2` | 2 | 129 |
| 11 | minesweeper | `mine-task100-r2` | 2 | 155 |
| 12 | sokoban | `soko-task101-r2` | 2 | 190 |
| 13 | bomberman | `bomb-task101-r4` | 2 | 233 |
| 14 | platformer | `plat-task102-r2` | 2 | 228 |
| 15 | match3 | `m3-task102-r3` | 2 | 145 |
| 16 | towerdefense | `td-task103-r3` | 2 | 145 |
| 17 | missilecommand | `mc-task103-r3` | 2 | 127 |
| 18 | rtype | `rt-task104-r2` | 2 | 223 |
| 19 | puzzlebobble | `pb-task104-r1` | 2 | 157 |
| 20 | lunarlander | `ll-task104-r1` | 2 | 230 |

### 3.3 per-tool counts (final runs)

| # | tool | scope | final calls | bucket |
|---|---|---|---|---|
| 1 | `running_game_assert_node_state` | game | 1308 | >=5 |
| 2 | `running_game_execute_gdscript` | game | 668 | >=5 |
| 3 | `running_game_capture_screenshot` | game | 102 | >=5 |
| 4 | `editor_add_input_action` | editor | 52 | >=5 |
| 5 | `running_game_get_node_property_samples` | game | 49 | >=5 |
| 6 | `editor_save_scene` | editor | 42 | >=5 |
| 7 | `running_game_get_scene_tree` | game | 40 | >=5 |
| 8 | `running_game_run_test_scenario` | game | 39 | >=5 |
| 9 | `project_read_text_file` | both | 36 | >=5 |
| 10 | `editor_add_nodes_batch` | editor | 35 | >=5 |
| 11 | `running_game_assert_screen_text` | game | 30 | >=5 |
| 12 | `editor_delete_node` | editor | 28 | >=5 |
| 13 | `editor_get_scene_tree` | editor | 24 | >=5 |
| 14 | `project_validate_scripts` | both | 23 | >=5 |
| 15 | `editor_open_scene` | editor | 21 | >=5 |
| 16 | `project_edit_script` | both | 21 | >=5 |
| 17 | `editor_get_node_properties` | editor | 20 | >=5 |
| 18 | `project_build_csharp` | both | 20 | >=5 |
| 19 | `editor_get_errors` | editor | 17 | >=5 |
| 20 | `editor_set_node_script_batch` | editor | 6 | >=5 |
| 21 | `project_create_script` | both | 6 | >=5 |
| 22 | `running_game_set_node_property` | game | 6 | >=5 |
| 23 | `editor_set_node_property` | editor | 5 | >=5 |
| 24 | `running_game_get_node_properties` | game | 5 | >=5 |
| 25 | `running_game_run_stress_test` | game | 5 | >=5 |
| 26 | `editor_capture_screenshot` | editor | 3 | 1-4 |
| 27 | `running_game_find_node_when_available` | game | 1 | 1-4 |
| 28 | `editor_add_animation_track` | editor | 0 | 0 |
| 29 | `editor_add_audio_bus` | editor | 0 | 0 |
| 30 | `editor_add_audio_bus_effect` | editor | 0 | 0 |
| 31 | `editor_add_audio_player` | editor | 0 | 0 |
| 32 | `editor_add_gridmap` | editor | 0 | 0 |
| 33 | `editor_add_mesh_instance` | editor | 0 | 0 |
| 34 | `editor_add_node` | editor | 0 | 0 |
| 35 | `editor_add_raycast` | editor | 0 | 0 |
| 36 | `editor_add_resource_to_node_property` | editor | 0 | 0 |
| 37 | `editor_add_scene_instance` | editor | 0 | 0 |
| 38 | `editor_add_state_machine_state` | editor | 0 | 0 |
| 39 | `editor_add_state_machine_transition` | editor | 0 | 0 |
| 40 | `editor_analyze_screenshot_diff` | editor | 0 | 0 |
| 41 | `editor_analyze_signal_flow` | editor | 0 | 0 |
| 42 | `editor_bake_navigation_mesh` | editor | 0 | 0 |
| 43 | `editor_connect_signal` | editor | 0 | 0 |
| 44 | `editor_create_animation` | editor | 0 | 0 |
| 45 | `editor_create_animation_tree` | editor | 0 | 0 |
| 46 | `editor_create_particles` | editor | 0 | 0 |
| 47 | `editor_disconnect_signal` | editor | 0 | 0 |
| 48 | `editor_duplicate_node` | editor | 0 | 0 |
| 49 | `editor_execute_gdscript` | editor | 0 | 0 |
| 50 | `editor_find_nodes_by_type` | editor | 0 | 0 |
| 51 | `editor_find_nodes_in_group` | editor | 0 | 0 |
| 52 | `editor_get_animation_info` | editor | 0 | 0 |
| 53 | `editor_get_animation_tree_structure` | editor | 0 | 0 |
| 54 | `editor_get_audio_bus_layout` | editor | 0 | 0 |
| 55 | `editor_get_audio_info` | editor | 0 | 0 |
| 56 | `editor_get_collision_info` | editor | 0 | 0 |
| 57 | `editor_get_input_actions` | editor | 0 | 0 |
| 58 | `editor_get_navigation_info` | editor | 0 | 0 |
| 59 | `editor_get_node_groups` | editor | 0 | 0 |
| 60 | `editor_get_node_signals` | editor | 0 | 0 |
| 61 | `editor_get_open_scripts` | editor | 0 | 0 |
| 62 | `editor_get_output_log` | editor | 0 | 0 |
| 63 | `editor_get_particle_info` | editor | 0 | 0 |
| 64 | `editor_get_performance_monitors` | editor | 0 | 0 |
| 65 | `editor_get_physics_layers` | editor | 0 | 0 |
| 66 | `editor_get_selection` | editor | 0 | 0 |
| 67 | `editor_get_test_report` | editor | 0 | 0 |
| 68 | `editor_get_tilemap_cell` | editor | 0 | 0 |
| 69 | `editor_get_tilemap_info` | editor | 0 | 0 |
| 70 | `editor_get_tilemap_used_cells` | editor | 0 | 0 |
| 71 | `editor_get_viewport_3d_camera` | editor | 0 | 0 |
| 72 | `editor_list_animations` | editor | 0 | 0 |
| 73 | `editor_list_signal_connections` | editor | 0 | 0 |
| 74 | `editor_play_scene` | editor | 0 | 0 |
| 75 | `editor_reload_plugin` | editor | 0 | 0 |
| 76 | `editor_remove_all_tilemap_cells` | editor | 0 | 0 |
| 77 | `editor_remove_animation` | editor | 0 | 0 |
| 78 | `editor_remove_node_selection` | editor | 0 | 0 |
| 79 | `editor_remove_output_log` | editor | 0 | 0 |
| 80 | `editor_remove_state_machine_state` | editor | 0 | 0 |
| 81 | `editor_remove_state_machine_transition` | editor | 0 | 0 |
| 82 | `editor_rename_node` | editor | 0 | 0 |
| 83 | `editor_reparent_node` | editor | 0 | 0 |
| 84 | `editor_rescan_project_filesystem` | editor | 0 | 0 |
| 85 | `editor_set_anchor_preset` | editor | 0 | 0 |
| 86 | `editor_set_animation_keyframe` | editor | 0 | 0 |
| 87 | `editor_set_animation_tree_parameter` | editor | 0 | 0 |
| 88 | `editor_set_audio_bus_property` | editor | 0 | 0 |
| 89 | `editor_set_auto_dismiss_dialogs` | editor | 0 | 0 |
| 90 | `editor_set_blend_tree_node` | editor | 0 | 0 |
| 91 | `editor_set_control_theme` | editor | 0 | 0 |
| 92 | `editor_set_material_3d` | editor | 0 | 0 |
| 93 | `editor_set_navigation_layers` | editor | 0 | 0 |
| 94 | `editor_set_node_groups` | editor | 0 | 0 |
| 95 | `editor_set_node_property_batch` | editor | 0 | 0 |
| 96 | `editor_set_node_property_updates` | editor | 0 | 0 |
| 97 | `editor_set_node_script` | editor | 0 | 0 |
| 98 | `editor_set_node_selection` | editor | 0 | 0 |
| 99 | `editor_set_particle_color_gradient` | editor | 0 | 0 |
| 100 | `editor_set_particle_material` | editor | 0 | 0 |
| 101 | `editor_set_particle_preset` | editor | 0 | 0 |
| 102 | `editor_set_physics_layers` | editor | 0 | 0 |
| 103 | `editor_set_shader_material` | editor | 0 | 0 |
| 104 | `editor_set_shader_param` | editor | 0 | 0 |
| 105 | `editor_set_tilemap_cell` | editor | 0 | 0 |
| 106 | `editor_set_tilemap_cells_in_rect` | editor | 0 | 0 |
| 107 | `editor_set_viewport_3d_camera` | editor | 0 | 0 |
| 108 | `editor_setup_camera_3d` | editor | 0 | 0 |
| 109 | `editor_setup_collision_shape` | editor | 0 | 0 |
| 110 | `editor_setup_lighting` | editor | 0 | 0 |
| 111 | `editor_setup_navigation_agent` | editor | 0 | 0 |
| 112 | `editor_setup_navigation_region` | editor | 0 | 0 |
| 113 | `editor_setup_physics_body` | editor | 0 | 0 |
| 114 | `editor_setup_world_environment` | editor | 0 | 0 |
| 115 | `editor_simulate_input_action` | editor | 0 | 0 |
| 116 | `editor_simulate_input_sequence` | editor | 0 | 0 |
| 117 | `editor_simulate_key` | editor | 0 | 0 |
| 118 | `editor_simulate_mouse_click` | editor | 0 | 0 |
| 119 | `editor_simulate_mouse_move` | editor | 0 | 0 |
| 120 | `editor_stop_scene` | editor | 0 | 0 |
| 121 | `os_deploy_to_android_device` | both | 0 | 0 |
| 122 | `os_list_android_devices` | both | 0 | 0 |
| 123 | `project_add_autoload` | both | 0 | 0 |
| 124 | `project_analyze_scene_complexity` | both | 0 | 0 |
| 125 | `project_convert_path_to_uid` | both | 0 | 0 |
| 126 | `project_convert_uid_to_path` | both | 0 | 0 |
| 127 | `project_create_resource` | both | 0 | 0 |
| 128 | `project_create_scene_file` | both | 0 | 0 |
| 129 | `project_create_shader` | both | 0 | 0 |
| 130 | `project_create_theme` | both | 0 | 0 |
| 131 | `project_delete_scene_file` | both | 0 | 0 |
| 132 | `project_detect_circular_dependencies` | both | 0 | 0 |
| 133 | `project_edit_resource` | both | 0 | 0 |
| 134 | `project_edit_shader` | both | 0 | 0 |
| 135 | `project_find_files_referencing_symbol` | both | 0 | 0 |
| 136 | `project_find_script_references` | both | 0 | 0 |
| 137 | `project_find_unused_resources` | both | 0 | 0 |
| 138 | `project_get_android_preset_info` | both | 0 | 0 |
| 139 | `project_get_export_info` | both | 0 | 0 |
| 140 | `project_get_filesystem_tree` | both | 0 | 0 |
| 141 | `project_get_info` | both | 0 | 0 |
| 142 | `project_get_resource_preview` | both | 0 | 0 |
| 143 | `project_get_scene_dependencies` | both | 0 | 0 |
| 144 | `project_get_scene_exports` | both | 0 | 0 |
| 145 | `project_get_settings` | both | 0 | 0 |
| 146 | `project_get_shader_params` | both | 0 | 0 |
| 147 | `project_get_statistics` | both | 0 | 0 |
| 148 | `project_get_theme_info` | both | 0 | 0 |
| 149 | `project_list_export_presets` | both | 0 | 0 |
| 150 | `project_list_scripts` | both | 0 | 0 |
| 151 | `project_read_resource` | both | 0 | 0 |
| 152 | `project_read_scene_file_content` | both | 0 | 0 |
| 153 | `project_read_script` | both | 0 | 0 |
| 154 | `project_read_shader` | both | 0 | 0 |
| 155 | `project_remove_autoload` | both | 0 | 0 |
| 156 | `project_search_file_contents` | both | 0 | 0 |
| 157 | `project_search_file_names` | both | 0 | 0 |
| 158 | `project_set_node_property_across_scenes` | both | 0 | 0 |
| 159 | `project_set_setting` | both | 0 | 0 |
| 160 | `project_set_theme_color` | both | 0 | 0 |
| 161 | `project_set_theme_constant` | both | 0 | 0 |
| 162 | `project_set_theme_font_size` | both | 0 | 0 |
| 163 | `project_set_theme_stylebox` | both | 0 | 0 |
| 164 | `project_validate_script` | both | 0 | 0 |
| 165 | `project_write_text_file` | both | 0 | 0 |
| 166 | `running_game_capture_frames` | game | 0 | 0 |
| 167 | `running_game_capture_signal_emissions` | game | 0 | 0 |
| 168 | `running_game_create_input_recording` | game | 0 | 0 |
| 169 | `running_game_find_nearby_nodes` | game | 0 | 0 |
| 170 | `running_game_find_nodes_by_script` | game | 0 | 0 |
| 171 | `running_game_find_ui_elements` | game | 0 | 0 |
| 172 | `running_game_get_autoload_node` | game | 0 | 0 |
| 173 | `running_game_get_node_properties_batch` | game | 0 | 0 |
| 174 | `running_game_move_player_to_target` | game | 0 | 0 |
| 175 | `running_game_play_input_recording` | game | 0 | 0 |
| 176 | `running_game_simulate_button_click_by_text` | game | 0 | 0 |
| 177 | `running_game_stop_input_recording` | game | 0 | 0 |

## 4. (3) Per-tool calls over ALL rounds under runs/

### 4.0 对照结论

| 口径 | 调用总次数 | 出现过的工具 | `0` 次 | `1-4` 次 | `>=5` 次 |
|---|---|---|---|---|---|
| **20 个最终轮** | 2612 | 27 | 150 | 2 | 25 |
| **runs/ 全部 81 个 run 目录** | 6618 | 29 | 148 | 2 | 27 |
| 差额（历史轮 + 探针） | +4006 | +2 | -2 | 0 | +2 |

把历史轮也算进来，只多出 **2 个工具的名字**，而且都是「先有后不用」的类型：

| 工具 | scope | 最终轮 | 全部轮次 | 说明 |
|---|---|---|---|---|
| `project_create_scene_file` | both | 0 | 3 | 只在 D-3 最小复现探针里出现（`pong/d3-before` 1 次、`pong/d3-after` 1 次、`pong/d3-after-r2` 1 次） |
| `project_delete_scene_file` | both | 0 | 4 | 同上，只在 `pong/d3-after` 与 `pong/d3-after-r2` 各 2 次 —— 探针造/删临时场景用得到，20 款游戏本体不用 |
| `editor_capture_screenshot` | editor | 3 | 25 | 最终轮的 3 次**全部**落在 TASK-097/TASK-106 的三个特殊目录里（pong-clean 1、breakout-clean 1、snake-task106-r1 1）；其余 17 款最终轮 0 次 |
| `running_game_find_node_when_available` | game | 1 | 8 | 「等节点出现」的探测；最终轮只被 Breakout 用到 1 次 |

后两条是从 `1-4` 桶**升进** `>=5` 桶的；前两条是从 `0` 桶**升进** `1-4` 桶的。
换句话说：**历史轮并不能把覆盖面拉宽**，它只把已经用到的那几千次调用重复了几遍。

成功与否：全量 6618 次里 `ok=false` **208** 次（6410 次 `ok=true`），同样计入。

#### 4.1 全量语料的原始计数

- corpus: **81** run directories, **140** trace files under `runs/`
- total tools/call lines: **6618** (of which 2612 are inside the 20 final run dirs; 4006 belong to historical/intermediate/probe rounds)
- distinct tools invoked: **29** of 177
- buckets over the 177 contract tools: 0x = **148**, 1-4x = **2**, >=5x = **27**

| # | tool | scope | all-run calls | bucket |
|---|---|---|---|---|
| 1 | `running_game_assert_node_state` | game | 2903 | >=5 |
| 2 | `running_game_execute_gdscript` | game | 1626 | >=5 |
| 3 | `running_game_capture_screenshot` | game | 298 | >=5 |
| 4 | `editor_add_input_action` | editor | 189 | >=5 |
| 5 | `running_game_run_test_scenario` | game | 185 | >=5 |
| 6 | `running_game_get_node_property_samples` | game | 122 | >=5 |
| 7 | `running_game_get_scene_tree` | game | 122 | >=5 |
| 8 | `editor_save_scene` | editor | 112 | >=5 |
| 9 | `editor_add_nodes_batch` | editor | 99 | >=5 |
| 10 | `project_validate_scripts` | both | 84 | >=5 |
| 11 | `project_read_text_file` | both | 80 | >=5 |
| 12 | `running_game_assert_screen_text` | game | 80 | >=5 |
| 13 | `editor_get_scene_tree` | editor | 71 | >=5 |
| 14 | `editor_delete_node` | editor | 65 | >=5 |
| 15 | `editor_open_scene` | editor | 64 | >=5 |
| 16 | `project_edit_script` | both | 60 | >=5 |
| 17 | `project_build_csharp` | both | 59 | >=5 |
| 18 | `editor_get_node_properties` | editor | 56 | >=5 |
| 19 | `editor_get_errors` | editor | 50 | >=5 |
| 20 | `project_create_script` | both | 49 | >=5 |
| 21 | `editor_set_node_script_batch` | editor | 48 | >=5 |
| 22 | `running_game_set_node_property` | game | 48 | >=5 |
| 23 | `editor_set_node_property` | editor | 41 | >=5 |
| 24 | `running_game_get_node_properties` | game | 40 | >=5 |
| 25 | `running_game_run_stress_test` | game | 27 | >=5 |
| 26 | `editor_capture_screenshot` | editor | 25 | >=5 |
| 27 | `running_game_find_node_when_available` | game | 8 | >=5 |
| 28 | `project_delete_scene_file` | both | 4 | 1-4 |
| 29 | `project_create_scene_file` | both | 3 | 1-4 |
| 30 | `editor_add_animation_track` | editor | 0 | 0 |
| 31 | `editor_add_audio_bus` | editor | 0 | 0 |
| 32 | `editor_add_audio_bus_effect` | editor | 0 | 0 |
| 33 | `editor_add_audio_player` | editor | 0 | 0 |
| 34 | `editor_add_gridmap` | editor | 0 | 0 |
| 35 | `editor_add_mesh_instance` | editor | 0 | 0 |
| 36 | `editor_add_node` | editor | 0 | 0 |
| 37 | `editor_add_raycast` | editor | 0 | 0 |
| 38 | `editor_add_resource_to_node_property` | editor | 0 | 0 |
| 39 | `editor_add_scene_instance` | editor | 0 | 0 |
| 40 | `editor_add_state_machine_state` | editor | 0 | 0 |
| 41 | `editor_add_state_machine_transition` | editor | 0 | 0 |
| 42 | `editor_analyze_screenshot_diff` | editor | 0 | 0 |
| 43 | `editor_analyze_signal_flow` | editor | 0 | 0 |
| 44 | `editor_bake_navigation_mesh` | editor | 0 | 0 |
| 45 | `editor_connect_signal` | editor | 0 | 0 |
| 46 | `editor_create_animation` | editor | 0 | 0 |
| 47 | `editor_create_animation_tree` | editor | 0 | 0 |
| 48 | `editor_create_particles` | editor | 0 | 0 |
| 49 | `editor_disconnect_signal` | editor | 0 | 0 |
| 50 | `editor_duplicate_node` | editor | 0 | 0 |
| 51 | `editor_execute_gdscript` | editor | 0 | 0 |
| 52 | `editor_find_nodes_by_type` | editor | 0 | 0 |
| 53 | `editor_find_nodes_in_group` | editor | 0 | 0 |
| 54 | `editor_get_animation_info` | editor | 0 | 0 |
| 55 | `editor_get_animation_tree_structure` | editor | 0 | 0 |
| 56 | `editor_get_audio_bus_layout` | editor | 0 | 0 |
| 57 | `editor_get_audio_info` | editor | 0 | 0 |
| 58 | `editor_get_collision_info` | editor | 0 | 0 |
| 59 | `editor_get_input_actions` | editor | 0 | 0 |
| 60 | `editor_get_navigation_info` | editor | 0 | 0 |
| 61 | `editor_get_node_groups` | editor | 0 | 0 |
| 62 | `editor_get_node_signals` | editor | 0 | 0 |
| 63 | `editor_get_open_scripts` | editor | 0 | 0 |
| 64 | `editor_get_output_log` | editor | 0 | 0 |
| 65 | `editor_get_particle_info` | editor | 0 | 0 |
| 66 | `editor_get_performance_monitors` | editor | 0 | 0 |
| 67 | `editor_get_physics_layers` | editor | 0 | 0 |
| 68 | `editor_get_selection` | editor | 0 | 0 |
| 69 | `editor_get_test_report` | editor | 0 | 0 |
| 70 | `editor_get_tilemap_cell` | editor | 0 | 0 |
| 71 | `editor_get_tilemap_info` | editor | 0 | 0 |
| 72 | `editor_get_tilemap_used_cells` | editor | 0 | 0 |
| 73 | `editor_get_viewport_3d_camera` | editor | 0 | 0 |
| 74 | `editor_list_animations` | editor | 0 | 0 |
| 75 | `editor_list_signal_connections` | editor | 0 | 0 |
| 76 | `editor_play_scene` | editor | 0 | 0 |
| 77 | `editor_reload_plugin` | editor | 0 | 0 |
| 78 | `editor_remove_all_tilemap_cells` | editor | 0 | 0 |
| 79 | `editor_remove_animation` | editor | 0 | 0 |
| 80 | `editor_remove_node_selection` | editor | 0 | 0 |
| 81 | `editor_remove_output_log` | editor | 0 | 0 |
| 82 | `editor_remove_state_machine_state` | editor | 0 | 0 |
| 83 | `editor_remove_state_machine_transition` | editor | 0 | 0 |
| 84 | `editor_rename_node` | editor | 0 | 0 |
| 85 | `editor_reparent_node` | editor | 0 | 0 |
| 86 | `editor_rescan_project_filesystem` | editor | 0 | 0 |
| 87 | `editor_set_anchor_preset` | editor | 0 | 0 |
| 88 | `editor_set_animation_keyframe` | editor | 0 | 0 |
| 89 | `editor_set_animation_tree_parameter` | editor | 0 | 0 |
| 90 | `editor_set_audio_bus_property` | editor | 0 | 0 |
| 91 | `editor_set_auto_dismiss_dialogs` | editor | 0 | 0 |
| 92 | `editor_set_blend_tree_node` | editor | 0 | 0 |
| 93 | `editor_set_control_theme` | editor | 0 | 0 |
| 94 | `editor_set_material_3d` | editor | 0 | 0 |
| 95 | `editor_set_navigation_layers` | editor | 0 | 0 |
| 96 | `editor_set_node_groups` | editor | 0 | 0 |
| 97 | `editor_set_node_property_batch` | editor | 0 | 0 |
| 98 | `editor_set_node_property_updates` | editor | 0 | 0 |
| 99 | `editor_set_node_script` | editor | 0 | 0 |
| 100 | `editor_set_node_selection` | editor | 0 | 0 |
| 101 | `editor_set_particle_color_gradient` | editor | 0 | 0 |
| 102 | `editor_set_particle_material` | editor | 0 | 0 |
| 103 | `editor_set_particle_preset` | editor | 0 | 0 |
| 104 | `editor_set_physics_layers` | editor | 0 | 0 |
| 105 | `editor_set_shader_material` | editor | 0 | 0 |
| 106 | `editor_set_shader_param` | editor | 0 | 0 |
| 107 | `editor_set_tilemap_cell` | editor | 0 | 0 |
| 108 | `editor_set_tilemap_cells_in_rect` | editor | 0 | 0 |
| 109 | `editor_set_viewport_3d_camera` | editor | 0 | 0 |
| 110 | `editor_setup_camera_3d` | editor | 0 | 0 |
| 111 | `editor_setup_collision_shape` | editor | 0 | 0 |
| 112 | `editor_setup_lighting` | editor | 0 | 0 |
| 113 | `editor_setup_navigation_agent` | editor | 0 | 0 |
| 114 | `editor_setup_navigation_region` | editor | 0 | 0 |
| 115 | `editor_setup_physics_body` | editor | 0 | 0 |
| 116 | `editor_setup_world_environment` | editor | 0 | 0 |
| 117 | `editor_simulate_input_action` | editor | 0 | 0 |
| 118 | `editor_simulate_input_sequence` | editor | 0 | 0 |
| 119 | `editor_simulate_key` | editor | 0 | 0 |
| 120 | `editor_simulate_mouse_click` | editor | 0 | 0 |
| 121 | `editor_simulate_mouse_move` | editor | 0 | 0 |
| 122 | `editor_stop_scene` | editor | 0 | 0 |
| 123 | `os_deploy_to_android_device` | both | 0 | 0 |
| 124 | `os_list_android_devices` | both | 0 | 0 |
| 125 | `project_add_autoload` | both | 0 | 0 |
| 126 | `project_analyze_scene_complexity` | both | 0 | 0 |
| 127 | `project_convert_path_to_uid` | both | 0 | 0 |
| 128 | `project_convert_uid_to_path` | both | 0 | 0 |
| 129 | `project_create_resource` | both | 0 | 0 |
| 130 | `project_create_shader` | both | 0 | 0 |
| 131 | `project_create_theme` | both | 0 | 0 |
| 132 | `project_detect_circular_dependencies` | both | 0 | 0 |
| 133 | `project_edit_resource` | both | 0 | 0 |
| 134 | `project_edit_shader` | both | 0 | 0 |
| 135 | `project_find_files_referencing_symbol` | both | 0 | 0 |
| 136 | `project_find_script_references` | both | 0 | 0 |
| 137 | `project_find_unused_resources` | both | 0 | 0 |
| 138 | `project_get_android_preset_info` | both | 0 | 0 |
| 139 | `project_get_export_info` | both | 0 | 0 |
| 140 | `project_get_filesystem_tree` | both | 0 | 0 |
| 141 | `project_get_info` | both | 0 | 0 |
| 142 | `project_get_resource_preview` | both | 0 | 0 |
| 143 | `project_get_scene_dependencies` | both | 0 | 0 |
| 144 | `project_get_scene_exports` | both | 0 | 0 |
| 145 | `project_get_settings` | both | 0 | 0 |
| 146 | `project_get_shader_params` | both | 0 | 0 |
| 147 | `project_get_statistics` | both | 0 | 0 |
| 148 | `project_get_theme_info` | both | 0 | 0 |
| 149 | `project_list_export_presets` | both | 0 | 0 |
| 150 | `project_list_scripts` | both | 0 | 0 |
| 151 | `project_read_resource` | both | 0 | 0 |
| 152 | `project_read_scene_file_content` | both | 0 | 0 |
| 153 | `project_read_script` | both | 0 | 0 |
| 154 | `project_read_shader` | both | 0 | 0 |
| 155 | `project_remove_autoload` | both | 0 | 0 |
| 156 | `project_search_file_contents` | both | 0 | 0 |
| 157 | `project_search_file_names` | both | 0 | 0 |
| 158 | `project_set_node_property_across_scenes` | both | 0 | 0 |
| 159 | `project_set_setting` | both | 0 | 0 |
| 160 | `project_set_theme_color` | both | 0 | 0 |
| 161 | `project_set_theme_constant` | both | 0 | 0 |
| 162 | `project_set_theme_font_size` | both | 0 | 0 |
| 163 | `project_set_theme_stylebox` | both | 0 | 0 |
| 164 | `project_validate_script` | both | 0 | 0 |
| 165 | `project_write_text_file` | both | 0 | 0 |
| 166 | `running_game_capture_frames` | game | 0 | 0 |
| 167 | `running_game_capture_signal_emissions` | game | 0 | 0 |
| 168 | `running_game_create_input_recording` | game | 0 | 0 |
| 169 | `running_game_find_nearby_nodes` | game | 0 | 0 |
| 170 | `running_game_find_nodes_by_script` | game | 0 | 0 |
| 171 | `running_game_find_ui_elements` | game | 0 | 0 |
| 172 | `running_game_get_autoload_node` | game | 0 | 0 |
| 173 | `running_game_get_node_properties_batch` | game | 0 | 0 |
| 174 | `running_game_move_player_to_target` | game | 0 | 0 |
| 175 | `running_game_play_input_recording` | game | 0 | 0 |
| 176 | `running_game_simulate_button_click_by_text` | game | 0 | 0 |
| 177 | `running_game_stop_input_recording` | game | 0 | 0 |

## 5. (4) Tools invoked < 5 times in the final runs

### 5.0 <5 次的两个桶

「< 5 次」= `0` 次 + `1-4` 次 = **152** 条（占契约 85.9%）。下面把两桶**逐条列名**。

读表须知：**「最终轮 0 次」不等于「结构上不可达」**。`all-run calls` 列是同一个工具在 `runs/` 全语料里的次数 ——
`project_create_scene_file`（0→3）与 `project_delete_scene_file`（0→4）就是反例：它们在最终轮没被调用，
但在 D-3 最小复现的探针轮（`pong/d3-before`、`pong/d3-after`、`pong/d3-after-r2`）里被调用过，说明工具**可达**，
只是这条工作流不需要它。§5.3 的「不可达」是**推断**，判据是「需要本循环根本不具备的子系统/资产/前置运行态」，
与「只是没人用」严格区分。

另外注意 `editor_capture_screenshot`：它在最终轮只有 3 次（`>=1` 但 `<5`），而这 3 次**全部**来自
TASK-097 清理重放与 TASK-106 重跑那三个特殊目录，17 款常规最终轮一次都没用编辑器截图
（它们用运行期 `running_game_capture_screenshot`，最终轮 102 次）。


### 5.1 bumped into 1-4 calls (2 tools)

| tool | scope | final calls | all-run calls |
|---|---|---|---|
| `editor_capture_screenshot` | editor | 3 | 25 |
| `running_game_find_node_when_available` | game | 1 | 8 |

### 5.2 never called in the final runs (150 tools)

note: the last column is the same tool counted over ALL rounds - the two rows with a non-zero all-run count were used by earlier rounds and are therefore NOT unreachable.

| tool | scope | final calls | all-run calls |
|---|---|---|---|
| `os_deploy_to_android_device` | both | 0 | 0 |
| `os_list_android_devices` | both | 0 | 0 |
| `project_add_autoload` | both | 0 | 0 |
| `project_analyze_scene_complexity` | both | 0 | 0 |
| `project_convert_path_to_uid` | both | 0 | 0 |
| `project_convert_uid_to_path` | both | 0 | 0 |
| `project_create_resource` | both | 0 | 0 |
| `project_create_scene_file` | both | 0 | 3 |
| `project_create_shader` | both | 0 | 0 |
| `project_create_theme` | both | 0 | 0 |
| `project_delete_scene_file` | both | 0 | 4 |
| `project_detect_circular_dependencies` | both | 0 | 0 |
| `project_edit_resource` | both | 0 | 0 |
| `project_edit_shader` | both | 0 | 0 |
| `project_find_files_referencing_symbol` | both | 0 | 0 |
| `project_find_script_references` | both | 0 | 0 |
| `project_find_unused_resources` | both | 0 | 0 |
| `project_get_android_preset_info` | both | 0 | 0 |
| `project_get_export_info` | both | 0 | 0 |
| `project_get_filesystem_tree` | both | 0 | 0 |
| `project_get_info` | both | 0 | 0 |
| `project_get_resource_preview` | both | 0 | 0 |
| `project_get_scene_dependencies` | both | 0 | 0 |
| `project_get_scene_exports` | both | 0 | 0 |
| `project_get_settings` | both | 0 | 0 |
| `project_get_shader_params` | both | 0 | 0 |
| `project_get_statistics` | both | 0 | 0 |
| `project_get_theme_info` | both | 0 | 0 |
| `project_list_export_presets` | both | 0 | 0 |
| `project_list_scripts` | both | 0 | 0 |
| `project_read_resource` | both | 0 | 0 |
| `project_read_scene_file_content` | both | 0 | 0 |
| `project_read_script` | both | 0 | 0 |
| `project_read_shader` | both | 0 | 0 |
| `project_remove_autoload` | both | 0 | 0 |
| `project_search_file_contents` | both | 0 | 0 |
| `project_search_file_names` | both | 0 | 0 |
| `project_set_node_property_across_scenes` | both | 0 | 0 |
| `project_set_setting` | both | 0 | 0 |
| `project_set_theme_color` | both | 0 | 0 |
| `project_set_theme_constant` | both | 0 | 0 |
| `project_set_theme_font_size` | both | 0 | 0 |
| `project_set_theme_stylebox` | both | 0 | 0 |
| `project_validate_script` | both | 0 | 0 |
| `project_write_text_file` | both | 0 | 0 |
| `editor_add_animation_track` | editor | 0 | 0 |
| `editor_add_audio_bus` | editor | 0 | 0 |
| `editor_add_audio_bus_effect` | editor | 0 | 0 |
| `editor_add_audio_player` | editor | 0 | 0 |
| `editor_add_gridmap` | editor | 0 | 0 |
| `editor_add_mesh_instance` | editor | 0 | 0 |
| `editor_add_node` | editor | 0 | 0 |
| `editor_add_raycast` | editor | 0 | 0 |
| `editor_add_resource_to_node_property` | editor | 0 | 0 |
| `editor_add_scene_instance` | editor | 0 | 0 |
| `editor_add_state_machine_state` | editor | 0 | 0 |
| `editor_add_state_machine_transition` | editor | 0 | 0 |
| `editor_analyze_screenshot_diff` | editor | 0 | 0 |
| `editor_analyze_signal_flow` | editor | 0 | 0 |
| `editor_bake_navigation_mesh` | editor | 0 | 0 |
| `editor_connect_signal` | editor | 0 | 0 |
| `editor_create_animation` | editor | 0 | 0 |
| `editor_create_animation_tree` | editor | 0 | 0 |
| `editor_create_particles` | editor | 0 | 0 |
| `editor_disconnect_signal` | editor | 0 | 0 |
| `editor_duplicate_node` | editor | 0 | 0 |
| `editor_execute_gdscript` | editor | 0 | 0 |
| `editor_find_nodes_by_type` | editor | 0 | 0 |
| `editor_find_nodes_in_group` | editor | 0 | 0 |
| `editor_get_animation_info` | editor | 0 | 0 |
| `editor_get_animation_tree_structure` | editor | 0 | 0 |
| `editor_get_audio_bus_layout` | editor | 0 | 0 |
| `editor_get_audio_info` | editor | 0 | 0 |
| `editor_get_collision_info` | editor | 0 | 0 |
| `editor_get_input_actions` | editor | 0 | 0 |
| `editor_get_navigation_info` | editor | 0 | 0 |
| `editor_get_node_groups` | editor | 0 | 0 |
| `editor_get_node_signals` | editor | 0 | 0 |
| `editor_get_open_scripts` | editor | 0 | 0 |
| `editor_get_output_log` | editor | 0 | 0 |
| `editor_get_particle_info` | editor | 0 | 0 |
| `editor_get_performance_monitors` | editor | 0 | 0 |
| `editor_get_physics_layers` | editor | 0 | 0 |
| `editor_get_selection` | editor | 0 | 0 |
| `editor_get_test_report` | editor | 0 | 0 |
| `editor_get_tilemap_cell` | editor | 0 | 0 |
| `editor_get_tilemap_info` | editor | 0 | 0 |
| `editor_get_tilemap_used_cells` | editor | 0 | 0 |
| `editor_get_viewport_3d_camera` | editor | 0 | 0 |
| `editor_list_animations` | editor | 0 | 0 |
| `editor_list_signal_connections` | editor | 0 | 0 |
| `editor_play_scene` | editor | 0 | 0 |
| `editor_reload_plugin` | editor | 0 | 0 |
| `editor_remove_all_tilemap_cells` | editor | 0 | 0 |
| `editor_remove_animation` | editor | 0 | 0 |
| `editor_remove_node_selection` | editor | 0 | 0 |
| `editor_remove_output_log` | editor | 0 | 0 |
| `editor_remove_state_machine_state` | editor | 0 | 0 |
| `editor_remove_state_machine_transition` | editor | 0 | 0 |
| `editor_rename_node` | editor | 0 | 0 |
| `editor_reparent_node` | editor | 0 | 0 |
| `editor_rescan_project_filesystem` | editor | 0 | 0 |
| `editor_set_anchor_preset` | editor | 0 | 0 |
| `editor_set_animation_keyframe` | editor | 0 | 0 |
| `editor_set_animation_tree_parameter` | editor | 0 | 0 |
| `editor_set_audio_bus_property` | editor | 0 | 0 |
| `editor_set_auto_dismiss_dialogs` | editor | 0 | 0 |
| `editor_set_blend_tree_node` | editor | 0 | 0 |
| `editor_set_control_theme` | editor | 0 | 0 |
| `editor_set_material_3d` | editor | 0 | 0 |
| `editor_set_navigation_layers` | editor | 0 | 0 |
| `editor_set_node_groups` | editor | 0 | 0 |
| `editor_set_node_property_batch` | editor | 0 | 0 |
| `editor_set_node_property_updates` | editor | 0 | 0 |
| `editor_set_node_script` | editor | 0 | 0 |
| `editor_set_node_selection` | editor | 0 | 0 |
| `editor_set_particle_color_gradient` | editor | 0 | 0 |
| `editor_set_particle_material` | editor | 0 | 0 |
| `editor_set_particle_preset` | editor | 0 | 0 |
| `editor_set_physics_layers` | editor | 0 | 0 |
| `editor_set_shader_material` | editor | 0 | 0 |
| `editor_set_shader_param` | editor | 0 | 0 |
| `editor_set_tilemap_cell` | editor | 0 | 0 |
| `editor_set_tilemap_cells_in_rect` | editor | 0 | 0 |
| `editor_set_viewport_3d_camera` | editor | 0 | 0 |
| `editor_setup_camera_3d` | editor | 0 | 0 |
| `editor_setup_collision_shape` | editor | 0 | 0 |
| `editor_setup_lighting` | editor | 0 | 0 |
| `editor_setup_navigation_agent` | editor | 0 | 0 |
| `editor_setup_navigation_region` | editor | 0 | 0 |
| `editor_setup_physics_body` | editor | 0 | 0 |
| `editor_setup_world_environment` | editor | 0 | 0 |
| `editor_simulate_input_action` | editor | 0 | 0 |
| `editor_simulate_input_sequence` | editor | 0 | 0 |
| `editor_simulate_key` | editor | 0 | 0 |
| `editor_simulate_mouse_click` | editor | 0 | 0 |
| `editor_simulate_mouse_move` | editor | 0 | 0 |
| `editor_stop_scene` | editor | 0 | 0 |
| `running_game_capture_frames` | game | 0 | 0 |
| `running_game_capture_signal_emissions` | game | 0 | 0 |
| `running_game_create_input_recording` | game | 0 | 0 |
| `running_game_find_nearby_nodes` | game | 0 | 0 |
| `running_game_find_nodes_by_script` | game | 0 | 0 |
| `running_game_find_ui_elements` | game | 0 | 0 |
| `running_game_get_autoload_node` | game | 0 | 0 |
| `running_game_get_node_properties_batch` | game | 0 | 0 |
| `running_game_move_player_to_target` | game | 0 | 0 |
| `running_game_play_input_recording` | game | 0 | 0 |
| `running_game_simulate_button_click_by_text` | game | 0 | 0 |
| `running_game_stop_input_recording` | game | 0 | 0 |

### 5.3 (5) which of them are structurally unreachable in this loop (INFERENCE)

Category membership below is a reasoned inference from the contract scope, the group manifests and the module source tree; it is NOT measured. Every member is verified to be in the 0-call set above.

#### 类别释义（H1–H9，均为推断）

| 代码 | 类别 | 为什么在本循环里结构上不可达（推断） | 支撑证据（只读观察） |
|---|---|---|---|
| **H1** | 3D 内容管线 | 20 款游戏**全部是 2D**，世界由 `ColorRect` / `Label` 在运行期或加载期拼出；工程里没有任何 Mesh / Camera3D / 光照 / WorldEnvironment 资产，也没有 `.tscn` 里能寻址的 3D 节点 | 模块侧 `tools/editor_scene_3d_write.cpp`；20 款游戏的载荷全部为 2D 坐标（台账逐条记 `ColorRect`/`Label`/像素差） |
| **H2** | 动画 / AnimationTree / 状态机 | 运动一律由**载荷自己的整数运动学**推进（`StepFrames(n)`、`_Process` 里 `x+=vx`），从不使用 `AnimationPlayer` / `AnimationTree`；没有动画资源可读写，也没有状态机可建 | `tools/editor_animation_read.cpp`、`editor_animation_write.cpp`、`editor_animation_tree_write.cpp`、`tools/animation_shared.cpp`；契约 override 里 `add_state_machine_state` 的 `animation` 成员是「结构性不可达」的已知缺口 |
| **H3** | TileMap / GridMap | 棋盘、迷宫、格点全部是**运行期新建的独立 `ColorRect`**（如 Pac-Man 的 125 颗豆子、Sokoban 的箱子、Match-3 的 8×8），20 个工程里没有 `TileMapLayer`、没有 `GridMap`、也没有 `TileSet` 资源，因此整族都没有作用对象 | `tools/editor_tilemap_read.cpp`、`editor_tilemap_write.cpp`、`tilemap_shared.cpp`。**额外证据（契约自述）**：`editor_set_tilemap_cell` / `editor_set_tilemap_cells_in_rect` 的 `description` 明写「当前工具集没有任何『给 TileSet 添加 atlas source / texture / tile』的入口，所以在可预见的调用序列里本工具无法成功 —— 这是一处如实声明的能力缺口」；同一条 override 另注明该缺口句只挂在两个**写**工具上，`editor_get_tilemap_info/_used_cells/_cell` 与 `editor_remove_all_tilemap_cells` 不要求 source 存在（即有 TileMapLayer 时它们是可达的） |
| **H4** | 导航 | 需要先有 `NavigationRegion2D` + 烘焙过的 `NavigationMesh` + `NavigationAgent`；本循环的寻路是载荷自己手写的格点/路径算法（Tower Defense 的 101 格蛇形走廊由 ASCII 地图确定性导出，Python 复算 `PathHash`），没有任何导航资产 | `tools/editor_navigation_read.cpp`、`editor_navigation_write.cpp`、`running_game_navigation_write.cpp`（`running_game_move_player_to_target` 就在这个文件里，前置条件即导航代理） |
| **H5** | 音频 | 20 款游戏**没有一个有声音**，没有 `AudioStreamPlayer`、没有 bus 布局，也没有音频资产 | `tools/editor_audio_read.cpp`、`editor_audio_write.cpp`、`audio_shared.cpp` |
| **H6** | 粒子 | 全部视觉证据是「节点位置/颜色 → 像素差」，没有任何 `GPUParticles2D` / 粒子材质 / 渐变 | `tools/editor_particle_read.cpp`、`editor_particle_write.cpp`、`particle_shared.cpp` |
| **H7** | 编辑器 GUI 状态 / 编辑器自有播放与输入注入 / 编辑器侧测试运行 | 这类工具的输入是**编辑器进程自己的 GUI 状态**（当前选择、打开的脚本、Output 面板、对话框、已装插件）或**编辑器自己的播放器/输入队列**。本循环里编辑器端点只做「开场景 / 加节点 / 存场景 / 建脚本 / 编译 / 读错误」；所有行为验证都走游戏端点，且**刻意不用**编辑器侧输入注入（B2 说明：`editor_simulate_*` 注入的是编辑器进程的输入，不能用来驱动游戏进程 —— D59 / GDR-21 的边界） | `tools/editor_playback.cpp`、`editor_input_simulation.cpp`、`editor_profiling_read.cpp`、`editor_testing_read.cpp`、`editor_script_write.cpp`、`editor_read_scene_inspector.cpp`；`editor_get_test_report` / `editor_analyze_screenshot_diff` 需要「编辑器侧测试运行」，而本循环的测试运行发生在游戏端点 |
| **H8** | 发布 / 导出 / Android 部署路径 | 循环的终点是「游戏跑起来 + 可复算证据」，从不打包、不导出、不连真机；`project_export_game` 甚至被契约 `_meta.excluded` 排除、`project_get_export_info` 等只在发布路径生效 | `tools/project_export_read.cpp`、`os_android_read.cpp`、`os_android_write.cpp`、`project_android_read.cpp`；契约 `_meta.excluded = ["navigate_to","export_project"]` |
| **H9** | 运行期录放与特殊捕获（deferred / 条件态） | 需要先进入某个**非默认运行态**才有效：`running_game_capture_frames` 需要开启逐帧捕获模式（本循环用的是整帧截图 `capture_screenshot`，298 次），信号发射捕获需要先注册监听，输入录制族需要「先 create → 再 play/stop」的三步会话。本循环的输入证据走的是**声明式 input action + 断言/场景驱动**，从未开过录制器 | `tools/running_game_capture.cpp`、`input_recorder.cpp`、`running_game_input.cpp`；台账里所有输入证据都是 `editor_add_input_action` + `running_game_run_test_scenario` |

**归类结果：H1–H9 共 74 条；其余 76 条 0 次工具判为「可达但这条工作流没用到」，在 §5.4 逐条列出以便复核。**

| # | tool | scope | category |
|---|---|---|---|
| 1 | `editor_add_mesh_instance` | editor | H1 |
| 2 | `editor_set_material_3d` | editor | H1 |
| 3 | `editor_setup_camera_3d` | editor | H1 |
| 4 | `editor_set_viewport_3d_camera` | editor | H1 |
| 5 | `editor_get_viewport_3d_camera` | editor | H1 |
| 6 | `editor_setup_lighting` | editor | H1 |
| 7 | `editor_setup_world_environment` | editor | H1 |
| 8 | `editor_create_animation` | editor | H2 |
| 9 | `editor_add_animation_track` | editor | H2 |
| 10 | `editor_set_animation_keyframe` | editor | H2 |
| 11 | `editor_remove_animation` | editor | H2 |
| 12 | `editor_list_animations` | editor | H2 |
| 13 | `editor_get_animation_info` | editor | H2 |
| 14 | `editor_create_animation_tree` | editor | H2 |
| 15 | `editor_get_animation_tree_structure` | editor | H2 |
| 16 | `editor_add_state_machine_state` | editor | H2 |
| 17 | `editor_add_state_machine_transition` | editor | H2 |
| 18 | `editor_remove_state_machine_state` | editor | H2 |
| 19 | `editor_remove_state_machine_transition` | editor | H2 |
| 20 | `editor_set_blend_tree_node` | editor | H2 |
| 21 | `editor_set_animation_tree_parameter` | editor | H2 |
| 22 | `editor_add_gridmap` | editor | H3 |
| 23 | `editor_get_tilemap_cell` | editor | H3 |
| 24 | `editor_get_tilemap_info` | editor | H3 |
| 25 | `editor_get_tilemap_used_cells` | editor | H3 |
| 26 | `editor_remove_all_tilemap_cells` | editor | H3 |
| 27 | `editor_set_tilemap_cell` | editor | H3 |
| 28 | `editor_set_tilemap_cells_in_rect` | editor | H3 |
| 29 | `editor_bake_navigation_mesh` | editor | H4 |
| 30 | `editor_get_navigation_info` | editor | H4 |
| 31 | `editor_set_navigation_layers` | editor | H4 |
| 32 | `editor_setup_navigation_agent` | editor | H4 |
| 33 | `editor_setup_navigation_region` | editor | H4 |
| 34 | `running_game_move_player_to_target` | game | H4 |
| 35 | `editor_add_audio_bus` | editor | H5 |
| 36 | `editor_add_audio_bus_effect` | editor | H5 |
| 37 | `editor_add_audio_player` | editor | H5 |
| 38 | `editor_get_audio_bus_layout` | editor | H5 |
| 39 | `editor_get_audio_info` | editor | H5 |
| 40 | `editor_set_audio_bus_property` | editor | H5 |
| 41 | `editor_create_particles` | editor | H6 |
| 42 | `editor_get_particle_info` | editor | H6 |
| 43 | `editor_set_particle_color_gradient` | editor | H6 |
| 44 | `editor_set_particle_material` | editor | H6 |
| 45 | `editor_set_particle_preset` | editor | H6 |
| 46 | `editor_play_scene` | editor | H7 |
| 47 | `editor_stop_scene` | editor | H7 |
| 48 | `editor_simulate_input_action` | editor | H7 |
| 49 | `editor_simulate_input_sequence` | editor | H7 |
| 50 | `editor_simulate_key` | editor | H7 |
| 51 | `editor_simulate_mouse_click` | editor | H7 |
| 52 | `editor_simulate_mouse_move` | editor | H7 |
| 53 | `editor_get_selection` | editor | H7 |
| 54 | `editor_set_node_selection` | editor | H7 |
| 55 | `editor_remove_node_selection` | editor | H7 |
| 56 | `editor_get_open_scripts` | editor | H7 |
| 57 | `editor_get_output_log` | editor | H7 |
| 58 | `editor_remove_output_log` | editor | H7 |
| 59 | `editor_set_auto_dismiss_dialogs` | editor | H7 |
| 60 | `editor_reload_plugin` | editor | H7 |
| 61 | `editor_get_performance_monitors` | editor | H7 |
| 62 | `editor_get_test_report` | editor | H7 |
| 63 | `editor_analyze_screenshot_diff` | editor | H7 |
| 64 | `editor_rescan_project_filesystem` | editor | H7 |
| 65 | `os_deploy_to_android_device` | both | H8 |
| 66 | `os_list_android_devices` | both | H8 |
| 67 | `project_get_export_info` | both | H8 |
| 68 | `project_list_export_presets` | both | H8 |
| 69 | `project_get_android_preset_info` | both | H8 |
| 70 | `running_game_capture_frames` | game | H9 |
| 71 | `running_game_capture_signal_emissions` | game | H9 |
| 72 | `running_game_create_input_recording` | game | H9 |
| 73 | `running_game_play_input_recording` | game | H9 |
| 74 | `running_game_stop_input_recording` | game | H9 |

hard-unreachable (H1-H9): 74 tools; remaining zero-call tools read as merely-unused-by-this-workflow: 76

The merely-unused remainder is listed in 5.4 so the split is auditable.

### 5.4 zero-call but NOT classified as structurally unreachable (76 tools)

| tool | scope |
|---|---|
| `editor_add_node` | editor |
| `editor_add_raycast` | editor |
| `editor_add_resource_to_node_property` | editor |
| `editor_add_scene_instance` | editor |
| `editor_analyze_signal_flow` | editor |
| `editor_connect_signal` | editor |
| `editor_disconnect_signal` | editor |
| `editor_duplicate_node` | editor |
| `editor_execute_gdscript` | editor |
| `editor_find_nodes_by_type` | editor |
| `editor_find_nodes_in_group` | editor |
| `editor_get_collision_info` | editor |
| `editor_get_input_actions` | editor |
| `editor_get_node_groups` | editor |
| `editor_get_node_signals` | editor |
| `editor_get_physics_layers` | editor |
| `editor_list_signal_connections` | editor |
| `editor_rename_node` | editor |
| `editor_reparent_node` | editor |
| `editor_set_anchor_preset` | editor |
| `editor_set_control_theme` | editor |
| `editor_set_node_groups` | editor |
| `editor_set_node_property_batch` | editor |
| `editor_set_node_property_updates` | editor |
| `editor_set_node_script` | editor |
| `editor_set_physics_layers` | editor |
| `editor_set_shader_material` | editor |
| `editor_set_shader_param` | editor |
| `editor_setup_collision_shape` | editor |
| `editor_setup_physics_body` | editor |
| `project_add_autoload` | both |
| `project_analyze_scene_complexity` | both |
| `project_convert_path_to_uid` | both |
| `project_convert_uid_to_path` | both |
| `project_create_resource` | both |
| `project_create_scene_file` | both |
| `project_create_shader` | both |
| `project_create_theme` | both |
| `project_delete_scene_file` | both |
| `project_detect_circular_dependencies` | both |
| `project_edit_resource` | both |
| `project_edit_shader` | both |
| `project_find_files_referencing_symbol` | both |
| `project_find_script_references` | both |
| `project_find_unused_resources` | both |
| `project_get_filesystem_tree` | both |
| `project_get_info` | both |
| `project_get_resource_preview` | both |
| `project_get_scene_dependencies` | both |
| `project_get_scene_exports` | both |
| `project_get_settings` | both |
| `project_get_shader_params` | both |
| `project_get_statistics` | both |
| `project_get_theme_info` | both |
| `project_list_scripts` | both |
| `project_read_resource` | both |
| `project_read_scene_file_content` | both |
| `project_read_script` | both |
| `project_read_shader` | both |
| `project_remove_autoload` | both |
| `project_search_file_contents` | both |
| `project_search_file_names` | both |
| `project_set_node_property_across_scenes` | both |
| `project_set_setting` | both |
| `project_set_theme_color` | both |
| `project_set_theme_constant` | both |
| `project_set_theme_font_size` | both |
| `project_set_theme_stylebox` | both |
| `project_validate_script` | both |
| `project_write_text_file` | both |
| `running_game_find_nearby_nodes` | game |
| `running_game_find_nodes_by_script` | game |
| `running_game_find_ui_elements` | game |
| `running_game_get_autoload_node` | game |
| `running_game_get_node_properties_batch` | game |
| `running_game_simulate_button_click_by_text` | game |

## 6. (6) 方法与 caveat

### 6.1 历史轮计入与否 —— 已分两个口径给出，不混用

§3 是**只看 20 个最终轮目录**（2612 次），§4 是**`runs/` 下全部 81 个目录**（6618 次，含历史中间轮与探针）。
两节各自独立分桶，差额在 §4.0 列出。**不要用 §4 的数字回答「最终轮覆盖多少」**，也不要用 §3 回答「历史上一共调过几次」。

### 6.2 两个最终目录里混着 TASK-097 的清理会话（会影响个别工具的归属）

`runs/pong/pong-clean-task097`（74 次）与 `runs/breakout/breakout-clean-task097`（89 次）不是「纯游戏会话」：
它们是 TASK-097 的 **D-1 结案清理会话 + 原会话重放**写进同一组 trace 文件的结果（`review_data.json` 用
`calls_total_in_trace` / `cleanup_calls` 两个字段显式区分：Pong 75 / 22、Breakout 90 / 34）。
本报告按**目录内全部 trace 行**计数，所以这两个目录的 74 / 89 比「会话本身」的 52 / 55 多出 22 / 34 次。

**最受影响的一条是 `editor_delete_node`：它在最终轮的 28 次调用 100% 来自这两个清理会话**
（Pong 删 8 个副本 + Breakout 删 20 个副本 = 8 + 20 = 28，与台账 D-3 行记的「8（5/3）/ 20（18/2）」逐数吻合），
其余 18 款游戏的最终轮**一次都没有**调用它 —— 这一条**可以靠计数算术完全定域**。也就是说这条工具的 `>=5` 桶身份
是**维护动作**而不是**试测动作**带来的；如果把清理会话剔掉，它是 0 次，`>=5` 会从 25 降到 24。

对**其他**编辑器/游戏工具，清理会话与重放**共用同一个 `trace_opened` 代**（同一文件、同一代、没有逐条标记），
因此**无法从 trace 原文里把「清理」与「重放」这两半切开**。本报告不假装能切，也没有把它们剔掉 ——
3.3 表的数字就是「目录内全部行」。但可以做一次**灵敏度检查**：把 `pong-clean-task097` 与
`breakout-clean-task097` **整目录**剔除后重算最终轮（注意这会同时剔掉清理动作与原会话重放，因此是**上界**效应），
`>=5` 桶会从 **25 降到 17**，`>=1` 的工具数从 **27 降到 22**。掉出 `>=5` 的 8 条是：

| 工具 | scope | 最终轮（20 目录） | 剔除这两个目录后 |
|---|---|---|---|
| `editor_delete_node` | editor | 28 | 0 |
| `editor_get_node_properties` | editor | 20 | 1 |
| `project_create_script` | both | 6 | 2 |
| `editor_set_node_script_batch` | editor | 6 | 2 |
| `running_game_set_node_property` | game | 6 | 0 |
| `editor_set_node_property` | editor | 5 | 0 |
| `running_game_get_node_properties` | game | 5 | 0 |
| `running_game_run_stress_test` | game | 5 | 3 |

读法：这 8 条的 `>=5` 身份**依赖** Pong/Breakout 这两个最终目录。其中 `editor_delete_node` 已被上面的计数算术
证明是纯清理动作；其余 7 条主要是**重放**带来的（重放本身就是「把该游戏原来的整份会话再跑一遍」，
所以它仍然落在「20 个最终轮」的口径内，只是这两个目录的构成与另外 18 款不同）——
换句话说，**25 条 ≥5 里有 8 条（32%）只在 Pong/Breakout 达到 ≥5，不是全 20 款共同覆盖的结果**。

### 6.3 与 `review_data.json` 的 `calls_total_in_trace` 差 1 的原因（已定域）

Pong 75、Breakout 90、Snake 54 都比本报告多 **1**，而其余 17 款逐数吻合。原因不是漏行，而是**口径**：
这三轮的 trace 里各有一条 `method: "tools/list"`（建连时拉契约），`review_data` 把它也算作一条「trace 里的调用」，
本报告**只数 `tools/call`**（`tools/list` 不是工具调用，且它没有 `tool` 字段）。
全语料共 25 条 `tools/list` 行，全部被本报告排除。

### 6.4 工具名与契约完全一致 —— 没有改名 / 别名 / 旧名残留

140 个文件里出现过的 **29 个不同的工具名，逐字 100% 命中契约的 177 个名字**（0 条例外）；
`tool-rename-map.json` 里的 **旧名（`old_name`）出现 0 次** —— 说明所有 trace 都是改名后的构建写的，
不存在「同一个工具被两个名字各记一半」的漏计风险。

契约与 rename map 的两个已知差异也已核对：
* map 里 **2 条目标名不在契约**：`project_export_game`、`running_game_move_player_to_target_via_navigation`
  （对应契约 `_meta.excluded = ["navigate_to", "export_project"]`）。trace 里**不存在**这两个名字。
* 契约 **6 条不在 map**：`project_build_csharp`、`project_write_text_file`、`project_validate_scripts`、
  `project_read_text_file`、`editor_set_node_script_batch`、`editor_set_node_property_updates`
  （`_meta.added_tools` 逐字相同）。它们的 scope 是本次从 `tool-groups-added.json` 补的。
  其中 5 条在循环里被用到，**只有 `project_write_text_file` 全量与最终轮都是 0 次**。

### 6.5 契约 177 = 174 − 2 − 1 + 6（可复算）

`tools_list.renamed.json` 的 `_meta` 自报：`tool_count_in = 174`（rename map）、`added_count = 6`、
`excluded = ["navigate_to","export_project"]`、`merged = 1`（`get_editor_performance` 被并入 `get_performance_monitors`）。
174 − 2 − 1 + 6 = **177** ✓。`gen_renamed_contract.py` 的 `generator_version = 1.22.0`。

### 6.6 截断 / sidecar / 代际（generation）对计数的影响 —— 无

* `args_truncated` **67** 行、`result_json_truncated` **138** 行、`error_data_json_truncated` **2** 行、`args_sidecar` **63** 行。
  工具名取自**行上的 `tool` 字段**，与 payload 是否被裁剪、是否被挪进 sidecar 完全无关；
  本报告也没有打开任何 sidecar 文件去补名字。所以这些行**一次都不会被漏数或重数**。
* `mcp_trace_ledger.py` 用 `event: "trace_opened"` 把文件切成「代」，因为 `seq` 只在同代内可比。
  本报告不依赖 `seq`，只按**行**计数，所以不需要切代；实测这 140 个文件每个**恰好只有 1 个 `trace_opened`**，
  即不存在跨代重连导致的重复行风险。
* 0 行 JSON 解析失败（`errors="replace"` 读，140 个文件全部可解析），0 条 `tools/call` 缺 `tool` 字段。

### 6.7 「最终 tag」的来源与台账的对照

* 采用 `dist/review_data.json` 的 `games[].run_tag`（20 条）。
* 与 `GAME-LOOP-LOG.md` 表格第 1–20 行的「证据路径」列逐行核对：**凡明确标出「最终 / 当前最终轮」的行都与该 tag 一致**
  （例：Snake 行明写「`runs\snake\snake-task106-r1`（当前最终轮）」；Tetris `tetris-task096-r2`；
  Bomberman `bomb-task101-r4`；Match-3 `m3-task102-r3`；Missile Command `mc-task103-r3`；
  R-Type `rt-task104-r2`；Tower Defense `td-task103-r3`；Platformer `plat-task102-r2`；Space Invaders `si-task097-r1`）。
  **但台账并没有为每一行都写出唯一 tag** —— 有些行（Pong、Breakout、Snake 的早期记法）只列历史轮与「中间轮」，
  这种行无法从正文唯一定出最终 tag；此时以 `review_data.json` 为准，两者不冲突。
* 台账里那些**同时列出历史轮**的行（Pong 列 `pong-run{1..4}` + `pong-task092`，Breakout/Snake 列 `-task093-r*`）
  是「证据溯源」写法，不是最终 tag；它们全部落在 §4 的全语料里。
* `gates` 是门跑器目录（20 个子目录）而不是第 21 款游戏，**没有 trace**，不参与任何数字。

### 6.8 本报告**没有**测量的东西（如实声明）

* **没有**核对调用参数/schema 是否符合契约（本任务只数次数）。
* **没有**判断「工具是否真的生效」（那是 `mcp_trace_ledger.py` 的 verdict 口径：`ok_effect_observed` /
  `ok_file_effect_observed` 等），本报告只区分 `ok` / `not ok` 的调用条数。
* **没有**把 `runs/gates/`、`projects/`、`recovery/work/` 里的任何产物纳入统计。
* §5.3 的 74 条「结构性不可达」是**推断**，判据是「缺少子系统/资产/前置运行态」+ 模块源码文件名与契约 override 的自述；
  它**不是**运行期实测（要实测就得真的去构造 3D 场景、导航网格、音频总线……那是另一个任务）。
  因此这一节请当作**可复核的假设清单**读，而不是结论。

## 7. Appendix A - run directories under runs/

| run directory (relative to runs/) | tools/call lines | used as a final tag? |
|---|---|---|
| asteroids/ast-task098-r1 | 71 |  |
| asteroids/ast-task098-r2 | 71 | YES |
| bomberman/bomb-task101-r1 | 224 |  |
| bomberman/bomb-task101-r2 | 226 |  |
| bomberman/bomb-task101-r3 | 231 |  |
| bomberman/bomb-task101-r4 | 233 | YES |
| breakout/breakout-clean-task097 | 89 | YES |
| breakout/breakout-task093-r2 | 50 |  |
| breakout/breakout-task093-r3 | 54 |  |
| breakout/breakout-task093-r4 | 54 |  |
| breakout/breakout-task093-r5 | 55 |  |
| breakout/breakout-task093-r6 | 55 |  |
| breakout/breakout-task093-r7 | 55 |  |
| breakout/breakout-task093 | 50 |  |
| flappy/flappy-task099-r1 | 92 |  |
| flappy/flappy-task099-r2 | 92 | YES |
| frogger/frog-task099-r1 | 90 | YES |
| game2048/2048-task100-r1 | 128 |  |
| game2048/2048-task100-r2 | 129 | YES |
| lunarlander/ll-task104-r1 | 230 | YES |
| match3/m3-task102-r1 | 136 |  |
| match3/m3-task102-r2 | 139 |  |
| match3/m3-task102-r3 | 145 | YES |
| match3/task103-x1-after | 6 |  |
| match3/task103-x1-before | 6 |  |
| minesweeper/mine-task100-r1 | 154 |  |
| minesweeper/mine-task100-r2 | 155 | YES |
| missilecommand/mc-task103-r1 | 127 |  |
| missilecommand/mc-task103-r2 | 127 |  |
| missilecommand/mc-task103-r3 | 127 | YES |
| pacman/pac-task098-r1 | 79 |  |
| pacman/pac-task098-r2 | 80 | YES |
| platformer/plat-task102-r1 | 228 |  |
| platformer/plat-task102-r2 | 228 | YES |
| pong/d3-after-r2 | 15 |  |
| pong/d3-after | 15 |  |
| pong/d3-before | 10 |  |
| pong/pong-clean-task097 | 74 | YES |
| pong/pong-control-task093 | 52 |  |
| pong/pong-run1 | 51 |  |
| pong/pong-run2 | 52 |  |
| pong/pong-run3 | 52 |  |
| pong/pong-run4 | 52 |  |
| pong/pong-task092 | 52 |  |
| pong/task094-pong-ab | 52 |  |
| puzzlebobble/pb-task104-r1 | 157 | YES |
| rtype/rt-task104-r1 | 223 |  |
| rtype/rt-task104-r2 | 223 | YES |
| snake/snake-clean-task097 | 102 |  |
| snake/snake-task093-r2 | 50 |  |
| snake/snake-task093-r3 | 50 |  |
| snake/snake-task093-r4 | 51 |  |
| snake/snake-task093-r5 | 51 |  |
| snake/snake-task093-r6 | 51 |  |
| snake/snake-task093 | 46 |  |
| snake/snake-task106-r1 | 53 | YES |
| snake/task094-probe10 | 5 |  |
| snake/task094-probe2 | 9 |  |
| snake/task094-probe3 | 10 |  |
| snake/task094-probe4 | 6 |  |
| snake/task094-probe5 | 4 |  |
| snake/task094-probe7 | 0 |  |
| snake/task094-probe8 | 0 |  |
| snake/task094-probe9 | 0 |  |
| snake/task094-probe | 7 |  |
| snake/task095-discriminate | 4 |  |
| snake/task095-loadednode | 7 |  |
| snake/task095-mirror2 | 7 |  |
| snake/task095-mirror | 7 |  |
| snake/task095-offscreen | 10 |  |
| snake/task095-rehost | 7 |  |
| snake/task096-loadednode-replay | 7 |  |
| snake/task096-occ | 10 |  |
| sokoban/soko-task101-r1 | 190 |  |
| sokoban/soko-task101-r2 | 190 | YES |
| spaceinvaders/si-task097-r1 | 59 | YES |
| tetris/tetris-task096-r2 | 42 | YES |
| tetris/tetris-task096 | 53 |  |
| towerdefense/td-task103-r1 | 144 |  |
| towerdefense/td-task103-r2 | 145 |  |
| towerdefense/td-task103-r3 | 145 | YES |

total run directories with traces: 81 ; total tools/call lines: 6618

