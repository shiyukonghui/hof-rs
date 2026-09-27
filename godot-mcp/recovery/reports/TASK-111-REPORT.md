# TASK-111 — 覆盖驱动循环第二批：可达未覆盖归零 + H1/H2/H3 三族整族证伪 + 台账两条读者缺陷修在根上

> 本报告的数字全部由 `coverage.json`（`python tools/tool_coverage.py` 重算）与各批次的
> `verify_coverage_batch.py` 输出重算得到，没有从任何报告表格转抄。
> `projects/` 下 20 款正式工程与 `runs/` 下的历史内容**只读未动**；本轮新增的一切都在
> `projects/_exercises/`、`runs/_exercises/`、`tools/sessions/_exercises/` 下。
> **引擎侧本轮零改动**（没有重建、没有重跑十道门），三条引擎缺陷只登记（§C2）。

---

## 0. 一句话结论

**做完了 A 段全量、B 段三族全量，并在此过程中找到台帐自己的两个缺陷与引擎的三个缺陷。**

1. **A 批（20 条可达未覆盖 + 5 条待补证据 + 3 条 setup）**：c4（163 次）＋ c5（13 次）两个会话，
   25 条目标**全部**达到「≥5 次调用 + ≥1 次边界失败 + facts 齐备」；16 条同时达到台账口径的
   「达标」。全语料的**「可达但未覆盖（<5 且非不可达）」由 20 归零**。
2. **B 三族（H1 3D 7 条 / H2 动画 14 条 / H3 TileMap 7 条）**：三份练习工程 + 三个会话
   （h1 45 次 / h2 100 次 / h3 48 次），**28 条全部被真实调用**，每条 ≥5 次 + 1 次边界探针；
   登记表据此**改判 28 条**（含 TASK-110 的 6 条，累计改判 34/74）。三族的
   `--headless --quit-after 5` 退出码**全部 0**。
3. **缺陷**：台账侧两条**修在根上**（`capture` 动词的生效口径；截断回包被误判
   `result_unparseable`，修复后达标 91 → 92）；引擎侧三条**只登记**，其中
   **D-T111-1 是阻塞级**：`project_create_resource` 的原子保存把资源 UID 注册到
   `*.mcp-tmp.tres`，导致之后保存的场景**按 UID 解析到不存在的临时文件**（退出码仍是 0）。

**必须同时说清的边界（§C2/§D3）**：25 条 A 目标里有 **9 条**、三族 28 条里有 **25 条**，
台账口径的「有效调用」仍是 0 —— 不是没有调用，而是 ledger 的 `scene_effect` 是**编辑器 2D
视口的截图差**，而 rename / 挂脚本 / 组 / 物理层掩码 / 动画 / 3D 这些写入**不改 2D 视口像素**。
它们的「真实生效」有**响应内的引擎读回**作证（§B4、§D3 逐条给出），但台账没有为它们放宽规则。

---

## 1. 交付物与证据路径

| 交付物 | 路径 | 说明 |
|---|---|---|
| 会话生成器（新增 c4/c5/h1/h2/h3 五个批次） | `tools/gen_coverage_session.py` | 单真源；`python tools/gen_coverage_session.py --batch <b>` 重生成 session + manifest |
| 批次校验器 | `tools/verify_coverage_batch.py` | 按 manifest 判「≥5 + ≥1 生效 + ≥1 边界」 |
| 台账工具（本轮修 2 处读者规则） | `tools/tool_coverage.py` | `python tools/tool_coverage.py` 随时重跑 |
| 台账 | `TOOL-COVERAGE.md` / `coverage.json` | 177 行总表 + 分桶 + <5 清单 + 不可达联动视图 |
| 不可达登记表（本轮 +28 改判） | `tools/tool_coverage_unreachable.json` | 见 `reclassified`（累计 34 条） |
| 练习工程 | `projects/_exercises/{ex_write,ex_write6,ex_3d,ex_anim2,ex_grid}` | 每份都从 `projects/pong` 复制（只读源）+ 现造资产 |
| 三族前置构造脚本 | `ex_3d/mk_probe.gd`、`ex_grid/mk_probe.gd`、`ex_anim2/mk_probe.gd` | **用引擎自己的 `ResourceSaver` 造 `.tres`/`.tscn`**，不手写 Godot 文本格式 |
| 会话与清单 | `tools/sessions/_exercises/{ex_write/c4,ex_write6/c5,ex_3d/h1,ex_anim/h2,ex_grid/h3}-{session,manifest}.json` | 可原样重放 |
| 运行证据 | `runs/_exercises/{ex_write5/c4-v5-task111,ex_write6/c5-task111,ex_3d/h1-task111,ex_anim2/h2b-task111,ex_grid/h3-task111}/` | trace + ledger + 逐调用请求/响应 + 截图（`runs/` 按既有政策不入库，只留在盘上） |
| 分析/派生脚本 | `recovery/work/task111/{dump_schemas,analyze_calls,reclassify,final_numbers,report_tables,remaining,why_unparseable}.py` | 本轮每个数字与判定都可重跑 |
| 决策 | `DECISIONS.md` **D156** | 选项、否决理由、回滚点 |

**批量会话（每一批的真实退出码/规模）**：

| 批次 | 工程 | 调用 | 目标工具 | 边界探针 | 说明 |
|---|---|---|---|---|---|
| c4 | `_exercises/ex_write5` | 163 | 23 | 23 | A 段主体（编辑器 145 + 游戏 18） |
| c5 | `_exercises/ex_write6` | 13 | 1 | 1 | `editor_disconnect_signal`（c4 清单里点名却漏调的 1 条） |
| h1 | `_exercises/ex_3d` | 45 | 7 | 7 | H1 3D 族 |
| h2 | `_exercises/ex_anim2` | 100 | 14 | 14 | H2 动画族（首轮 94 次在 `ex_anim`，2 处会话侧缺口重跑） |
| h3 | `_exercises/ex_grid` | 48 | 7 | 7 | H3 TileMap/GridMap 族 |

---

## A. 可达但未覆盖的写工具与大族尾项（c4 + c5）

### A1. 判定口径与「边界」怎么写

* `边界调用` = `ok=false` 的调用；本批 25 条目标的边界**全部**是「设计出来、可审计」的：
  manifest 的 `intent=probe` 逐条记了它应当失败的理由，`analyze_calls.py` 把
  `intent` 与**运行目录里逐调用的真实响应** join 起来报 mismatch —— c4 的 163 次里
  **mismatch 只有 1 条**，而那 1 条正是本轮**故意**用来复现 D-T111-2 的那次（见 §C2）。
* 探针类型刻意选**类型错误 / 缺必填 / 不存在的对象**，不选「碰巧失败」的宽容输入；
  唯一一次「探针被接受」的历史（TASK-110 的 `max_lines:-1`、`max_depth:-2`）本轮换成
  `{"max_lines":"ten"}` / `{"max_depth":"deep"}`，两条都得到 `-32602`。

### A2. 25 条目标逐条结果

（`累计`/`有效`/`边界`/`状态` 取自 `coverage.json`（all-runs 口径，含本轮之前的历史调用）；
`本批` 是这一条主要由哪个会话贡献。三态：`达标` = 台账口径三项全满足。）

| # | tool | 累计 | 有效 | 边界 | facts | 状态 | 本批 | 真实生效的证据（当台账说 0 有效时） |
|---|---|---|---|---|---|---|---|---|
| 1 | `editor_add_node` | 30 | 10 | 5 | 30/30 | 达标 | c4 | — |
| 2 | `editor_add_scene_instance` | 30 | 0 | 5 | 30/30 | 计数达标缺证据 | c4 | 后续 `editor_reparent_node {"path":"C4Node2","new_parent":"Sub1"}` 成功（`Sub1` 按名可寻址），响应回 `moved:true` |
| 3 | `editor_add_raycast` | 33 | 16 | 9 | 33/33 | 达标 | c4 | — |
| 4 | `editor_add_resource_to_node_property` | 32 | 12 | 20 | 32/32 | 达标 | c4 | 直径/矩形 Shape2D 的 `radius` 变体 5/5 生效；**向量变体被拒**见 D-T111-2 |
| 5 | `editor_duplicate_node` | 30 | 5 | 7 | 30/30 | 达标 | c4 | — |
| 6 | `editor_rename_node` | 30 | 0 | 7 | 30/30 | 计数达标缺证据 | c4 | `editor_get_node_properties {"path":"Host/Ren1","properties":["name"]}` → `{"name":"Ren1"}` |
| 7 | `editor_reparent_node` | 30 | 3 | 14 | 30/30 | 达标 | c4 | — |
| 8 | `editor_disconnect_signal` | 6 | 0 | 1 | 6/6 | 计数达标缺证据 | **c5** | 断开后 `editor_list_signal_connections {"node_path":"Ball","scope":"user"}` → `count:0`（`counts.user=0`，`counts.internal=11`） |
| 9 | `editor_set_node_property_batch` | 30 | 15 | 5 | 30/30 | 达标 | c4 | — |
| 10 | `editor_set_node_property_updates` | 30 | 3 | 7 | 30/30 | 达标 | c4 | — |
| 11 | `editor_set_node_script` | 30 | 0 | 5 | 30/30 | 计数达标缺证据 | c4 | 每次响应回 `attached:true` + `script_path` + `previous_script_path`（引擎读回，不是回显） |
| 12 | `editor_set_node_groups` | 36 | 0 | 11 | 35/36 | 计数达标缺证据 | c4 | `editor_get_node_groups {"node_path":"Host"}` → `groups:["ex_host"]`；`{"added":[...],"removed":[...]}` 逐次给出增减 |
| 13 | `editor_setup_physics_body` | 24 | 0 | 7 | 24/24 | 计数达标缺证据 | c4 | 随后 `editor_setup_collision_shape` 以 `Host/PB3`、`Host/PB5` 为 `node_path` 成功（节点真在树里） |
| 14 | `editor_setup_collision_shape` | 31 | 9 | 11 | 31/31 | 达标 | c4 | — |
| 15 | `editor_set_physics_layers` | 24 | 0 | 6 | 24/24 | 计数达标缺证据 | c4 | `editor_get_node_properties {"path":"PB1","properties":["collision_layer","collision_mask"]}` → `{collision_layer:1, collision_mask:4}` |
| 16 | `editor_set_control_theme` | 24 | 0 | 5 | 24/24 | 计数达标缺证据 | c4 | 每次响应回 `applied:true` + `theme:{type:"Theme",value:"C4Theme…"}`（引擎读回） |
| 17 | `editor_set_anchor_preset` | 24 | 5 | 5 | 24/24 | 达标 | c4 | — |
| 18 | `editor_set_shader_material` | 24 | 3 | 6 | 24/24 | 达标 | c4 | — |
| 19 | `editor_set_shader_param` | 24 | 1 | 14 | 24/24 | 达标 | c4 | — |
| 20 | `editor_connect_signal` | 39 | 0 | 6 | 39/39 | 计数达标缺证据 | c4+c5 | 响应回 `connected:true, persisted:true`；c5 的断开读回反证它真的连上了 |
| 21 | `editor_get_output_log` | 36 | 32 | 4 | 36/36 | **达标** | c4 | 补边界：`{"max_lines":"ten"}` → `-32602` |
| 22 | `editor_get_scene_tree` | 108 | 50 | 4 | 108/108 | **达标** | c4 | 补边界：`{"max_depth":"deep"}` → `-32602` |
| 23 | `running_game_get_node_properties_batch` | 36 | 26 | 4 | 36/36 | **达标** | c4 | 补边界：`{"nodes":"Ball"}` → `-32602`（类型探针，不再是「仅是节点不存在」） |
| 24 | `running_game_capture_frames` | 36 | 6 | 6 | 30/36 | **达标** | c4 | `capture` 动词口径澄清（§C1-①）：5 帧/次内联 base64 就是它的载荷 |
| 25 | `running_game_capture_signal_emissions` | 36 | 26 | 10 | 26/36 | **达标** | c4 | 同上；实测捕到 `/root/Main/Tick` 的 `timeout` 1–2 次发射 |

**A 段小计**：25/25 达到「≥5 次 + ≥1 边界 + facts 齐备」；16/25 达到台账的「达标」。
3 条 setup 工具（`editor_connect_signal` **39** 次、`editor_set_node_groups` **36** 次、
`editor_setup_collision_shape` **31** 次）全部由 2–4 次补到 ≥5。

### A3. 两个会话各自的唯一 mismatch（如实列出）

| 批次 | mismatch | 性质 |
|---|---|---|
| c4 | `c4-040-editor_add_resource_to_node_property`（intent=ok 却得 `-32602`） | **故意的缺陷复现**（D-T111-2），manifest 的 note 写明「DEFECT REPRO」 |
| c5 | 无 | — |

**「下一步还没做」的一条**：c5 的 target 只有 1 条（`editor_disconnect_signal`）。
它本是 c4 清单第 8 条，我在写 c4 时只写了 setup 的 5 条连接而**漏写了目标调用**；
这个漏项在 `final_numbers.py` 报出「可达但 <5：`editor_disconnect_signal`」时被抓到，
于是补了 c5。**没有把它藏进 c4 的成功叙述里。**

---

## B. 三族练习工程（H1 / H2 / H3，共 28 条）

### B1. 每个族缺的到底是什么（逐族证伪「结构性不可达」）

| 族 | TASK-108 的推断 | 本轮实际缺的东西 | 怎么造的 |
|---|---|---|---|
| **H1** 3D（7 条） | 「20 款游戏全部是 2D，工程里没有任何 Mesh/Camera3D/光照/WorldEnvironment 资产」 | **一个 Node3D 场景 + 一个带 mesh 的 MeshInstance3D**（`editor_set_material_3d` 明确拒绝没有 mesh 的实例） | `ex_3d/mk_probe.gd`：`PackedScene.pack(Node3D + MeshInstance3D(BoxMesh))` → `ResourceSaver.save` |
| **H2** 动画（14 条） | 「没有 AnimationPlayer / AnimationTree / 状态机」 | **一个带默认 library 的 AnimationPlayer + 一个可寻址的 track 目标** | `ex_anim2/mk_probe.gd`：`AnimationPlayer.add_animation_library("", AnimationLibrary.new())` → `anim.tscn` |
| **H3** TileMap（7 条） | 「没有 TileMapLayer / GridMap / TileSet 资源」；且契约自述写工具「在可预见的调用序列里无法成功」 | **一份自带 `TileSetAtlasSource` 的 `.tres`**（+ `MeshLibrary` 给 `editor_add_gridmap`）。契约原话就是「要么在项目里自带一个含 source 的 `.tres`」 | `ex_grid/mk_probe.gd`：`TileSetAtlasSource + create_tile(Vector2i(0,0))` → `add_source` → `ResourceSaver.save`；另造 `MeshLibrary` 与 `grid.tscn` |

**为什么用 GDScript 而不是手写 `.tres`**：手写文本格式会让「前置成立」依赖我对 Godot 序列化
格式的记忆；用引擎自己的 `ResourceSaver` 写出来的 `.tres` 只可能被引擎读回。
脚本的 stdout 就是前置的凭据（`MKGRID tileset sources=1 sid=0 tiles=1 save_err=0`、
`MKANIM root_node=.. libraries=[&""]`、`MK3D saved=… surfaces=1`）。

### B2. 逐族门（工程能跑 + 每条 ≥5 + 生效 + 边界）

| 族 | `--headless --quit-after 5` 退出码 | 目标数 | calls≥5 | 边界≥1 | facts 齐备 | 台账「达标」 |
|---|---|---|---|---|---|---|
| H1 | **0**（`res://scenes/probe3d.tscn`；含 §C2-D-T111-1 的 `ext_resource` 解析错误） | 7 | 7/7 | 7/7 | 7/7 | 1/7 |
| H2 | **0**（`res://scenes/anim.tscn`） | 14 | 14/14 | 14/14 | 14/14 | 3/14 |
| H3 | **0**（`res://scenes/grid.tscn`） | 7 | 7/7 | 7/7 | 7/7 | 5/7 |

### B3. 三族逐条结果

**① H1（3D 内容管线，7 条）**

| # | tool | 累计 | 有效 | 边界 | 状态 | 真实生效的证据 |
|---|---|---|---|---|---|---|
| 1 | `editor_add_mesh_instance` | 6 | 0 | 1 | 计数达标缺证据 | 后续 `editor_setup_camera_3d`/`editor_setup_lighting` 以 `MeshA`/`MeshB` 为父成功（节点真在树里）；场景存盘里可见 `[node name="MeshA" type="MeshInstance3D"]` |
| 2 | `editor_set_material_3d` | 6 | 0 | 3 | 计数达标缺证据 | `probe3d.tscn` 的 `surface_material_override/0 = ExtResource(material)`；`editor_get_node_properties` 可读回 |
| 3 | `editor_setup_camera_3d` | 6 | 0 | 1 | 计数达标缺证据 | 响应回 `created:true, current:true` + 引擎给的真实 `node_path`（含重名时的 `@Camera3D@20956`） |
| 4 | `editor_set_viewport_3d_camera` | 6 | 0 | 1 | 计数达标缺证据 | **下一次调用读回上一次写的值**（`fov` 70.01→60→75、`position` 逐次变化） |
| 5 | `editor_get_viewport_3d_camera` | 6 | 5 | 1 | **达标** | 读类，回包即证据 |
| 6 | `editor_setup_lighting` | 6 | 0 | 1 | 计数达标缺证据 | 三种 `light_type` → `DirectionalLight3D`/`OmniLight3D`/`SpotLight3D`，响应回 `setup:true` + 真实 `node_path` |
| 7 | `editor_setup_world_environment` | 6 | 0 | 1 | 计数达标缺证据 | 第 1 次 `environment_created:true`，后 4 次 `false`（复用）——**这个 false 本身就是引擎读回**；场景存盘里有 `[sub_resource type="Environment"]` 与 `WorldEnvironment` |

**② H2（动画 / AnimationTree / 状态机，14 条）**

| # | tool | 累计 | 有效 | 边界 | 状态 | 真实生效的证据 |
|---|---|---|---|---|---|---|
| 1 | `editor_create_animation` | 18 | 0 | 2 | 计数达标缺证据 | 响应回 `animation_count` 递增 1→8、`length` 为请求值 |
| 2 | `editor_add_animation_track` | 12 | 0 | 2 | 计数达标缺证据 | 回 `track_index` / `track_path` / `key_count=0`；`track_index` 0/1/2 递增 |
| 3 | `editor_set_animation_keyframe` | 12 | 0 | 2 | 计数达标缺证据 | 回 `key_index` / `key_count` 1→2；`editor_get_animation_info` 读回 keys |
| 4 | `editor_remove_animation` | 12 | 0 | 2 | 计数达标缺证据 | 回 `removed:1` + `animation_count` 8→3 |
| 5 | `editor_list_animations` | 12 | 10 | 2 | **达标** | 读类 |
| 6 | `editor_get_animation_info` | 12 | 10 | 2 | **达标** | 读类 |
| 7 | `editor_create_animation_tree` | 12 | 0 | 2 | 计数达标缺证据 | 回 `tree_root:"AnimationNodeStateMachine"`、`animation_player:"Player"`、`animation_player_path_from_tree` |
| 8 | `editor_get_animation_tree_structure` | 12 | 8 | 2 | **达标** | 读类 |
| 9 | `editor_add_state_machine_state` | 18 | 0 | 2 | 计数达标缺证据 | 11 个状态全部 `added:true`；后续读取报 `This machine holds: BT, End, Fall, Idle, Jump, Run, Start, Walk` |
| 10 | `editor_add_state_machine_transition` | 22 | 0 | 2 | 计数达标缺证据 | 10 条 `added:true`；`remove_state_machine_transition` 读出 `machine has 5 transition(s)` |
| 11 | `editor_remove_state_machine_state` | 12 | 0 | 7 | 计数达标缺证据 | 回 `removed:1` + `state_count` 6→2（5 条历史失败是首轮 `ex_anim` 的会话缺口，见 §B5） |
| 12 | `editor_remove_state_machine_transition` | 12 | 0 | 2 | 计数达标缺证据 | 回 `removed:1` |
| 13 | `editor_set_blend_tree_node` | 12 | 0 | 7 | 计数达标缺证据 | 回 `added:true` + `bt_node_name`/`bt_node_type`；之后参数表里出现 `parameters/BT/B1/blend_amount` |
| 14 | `editor_set_animation_tree_parameter` | 12 | 0 | 4 | 计数达标缺证据 | 回 `changed:{old:0.0,new:0.5}` / `{old:false,new:true}` —— **新旧值是引擎读回** |

**③ H3（TileMap / GridMap，7 条）**

| # | tool | 累计 | 有效 | 边界 | 状态 | 真实生效的证据 |
|---|---|---|---|---|---|---|
| 1 | `editor_add_gridmap` | 6 | 0 | 1 | 计数达标缺证据 | 回 `created:true, mesh_library_set:true`；`mesh_library_path` 不存在时 `-32001` 且**不建节点** |
| 2 | `editor_get_tilemap_cell` | 6 | 5 | 1 | **达标** | 读类；读回 `atlas_coords:{0,0}`、`empty:false` |
| 3 | `editor_get_tilemap_info` | 6 | 5 | 1 | **达标** | 读类；读回 `cell_count:33` |
| 4 | `editor_get_tilemap_used_cells` | 6 | 5 | 1 | **达标** | 读类；6 591 B 的完整 cell 列表 —— **修台账 §C1-② 之前它被判 `result_unparseable`** |
| 5 | `editor_remove_all_tilemap_cells` | 6 | 5 | 1 | **达标** | 回 `cell_count_before:33→1→1→1→1`、`cleared:true`（每次清的都是真有的格子） |
| 6 | `editor_set_tilemap_cell` | 10 | 9 | 1 | **达标** | 回 `applied:true` + 引擎读回的 cell 结构；`has_tile_set:true` |
| 7 | `editor_set_tilemap_cells_in_rect` | 6 | 5 | 1 | **达标** | 回 `filled:16/4/3/3/4`、`cell_count` 与 rect 面积一致 |

### B4. 「有效」为什么在多数写工具上是 0 —— 一个必须说清的口径

台账的 `有效调用` 对写类动词只有两个来源：`ok_effect_observed`（屏幕/视口变化）或
`ok_file_effect_observed`（文件变化）。而 ledger 的 `scene_effect` 是
**编辑器 2D 视口的截图差**（`_scene_of` 只读 capture 行的 `changed`）：

* **H1 的 3D 写入在 2D 视口里什么都看不见** —— 6/7 条的「有效」只能是 0；
* **H2 的动画资源不画进视口** —— 11/14 条为 0；
* **A 批的 rename / 挂脚本 / 组 / 物理层掩码 / 建预制体**同样不改像素。

本轮**没有**为此放宽台账规则（TASK-110 §F 的立场保持不变），而是：
①用**同一批次里的读回调用**把引擎自己的答案留在 trace 上（§A2、§B3 的最后一列）；
②把「这些写入的真实生效需要一个非像素见证」作为**下一批的口径决策**提出（§E）。

---

## C. 缺陷

### C1. 【已修·台账侧】两条读者规则缺陷

**① `capture` 动词不在读侧** —— 四个 capture 工具（`editor_capture_screenshot`、
`running_game_capture_screenshot`、`running_game_capture_frames`、
`running_game_capture_signal_emissions`）**不写持久状态**，它们的回包**就是**证据：
内联 base64 帧、或它们注册监听后观测到的发射记录。
修法：`READ_VERBS` 加入 `capture`，并把理由写进注释（与 `assert`/`execute` 同一ground）。
效果：`running_game_capture_frames` / `capture_signal_emissions` 从「计数达标缺证据」转为**达标**
（TASK-110 §B4 当时只差这一条口径）。

**② 截断回包的 sidecar 被忽略** —— `substantive()` 只解析 trace 行内联的前 4096 字节；
超过预算的回包 line 上带 `result_json_truncated: true` 且**必然解析失败**，
于是 `editor_get_tilemap_used_cells`（6 591 B）被判 `result_unparseable` / 无效。
证据（逐字）：
```
seq=26 tool=editor_get_tilemap_used_cells result_bytes=6591 result_json_bytes=5700
result_json_truncated=True
result_json_sidecar={path: runs/.../trace-editor.sidecar/0026-result.json,
                     sha256: 987d22525fccbc707ecad144471aa08add1404cd9b7154dbb787623608ec3e48}
--- result_json 内联副本 len=4096 → parse error: Expecting property name ... char 4096
```
而 `mcp_trace_ledger.build` 早已把完整体核过 sha（`result_json_evidence == "sidecar_verified"`）。
修法：`classify()` 接受「已核验 sidecar ⇒ 载荷非空」。
**前后对比**：达标 **91 → 92**；`editor_get_tilemap_used_cells` 由 `计数达标缺证据` 转 `达标`。

### C2. 【只登记·未修】三条引擎侧缺陷（根因明确，但修法需契约/行为/集成决策）

**D-T111-1 ｜【阻塞级】`project_create_resource` 的原子保存把资源 UID 注册到临时文件名**
* 证据链：`ex_3d` 工程里 `.godot/uid_cache.bin` **含字符串 `res://assets/mat3d.mcp-tmp.tres`**；
  `probe3d.tscn` 第 2 行是 `[ext_resource type="Material" uid="uid://pssr3ffdcvet" path="res://assets/mat3d.tres"]`；
  用引擎跑同一场景可**稳定复现**（两次）：
  ```
  ERROR: Cannot open file 'res://assets/mat3d.mcp-tmp.tres'.
  ERROR: Failed loading resource: res://assets/mat3d.mcp-tmp.tres.
  ERROR: res://scenes/probe3d.tscn:17 - Parse Error: [ext_resource] referenced non-existent resource
  GATE_3D_EXIT=0     <- 退出码仍是 0
  ```
* 根因：`tool_helpers.cpp:487-496` 的 `temporary_sibling_path()` 产出 `<base>.mcp-tmp.<ext>`，
  `publish_file_atomically()`（`:498-538`）让写入方把资源**保存到临时路径**再 `rename`；
  `ResourceSaver::save(res, temp_path)` 会把 `res->set_path(temp_path)` 并把 **UID 注册到
  `uid_cache.bin` 的临时路径上**，而 rename 只改了文件名、没有改回资源的 path、也没有更新 UID 缓存。
* 影响：**「用 `project_create_resource` 造资源 → 挂到节点 → `editor_save_scene`」这条最自然的
  序列产出的场景会加载失败**；因为按 `uid` 解析，`path="res://assets/mat3d.tres"` 这个正确属性
  **救不了它**。退出码为 0，所以只有看 stderr 才发现 —— 正是「静默的错误结果」。
* 修法选项（**需决策**）：①发布后把 `resource->set_path(destination)` 并更新 `ResourceUID`
  的映射（要动编辑器文件系统）；②临时文件**不要带可注册扩展名**（如 `.mcp-tmp` 无扩展），
  这样 `ResourceSaver` 不认为它是可注册的资源路径；③保存前用 `ResourceSaver::save` 之外
  的路径（`FileAccess` 直写）绕过 UID 注册。三者行为面不同，故只登记。

**D-T111-2 ｜`editor_add_resource_to_node_property` 的 `resource_properties` 缺 `shape_vector_from_json`**
* 证据：`c4-040`（`ex_write5/c4-v5-task111`）请求
  `{"resource_type":"RectangleShape2D","resource_properties":{"size":{"x":48,"y":48}}}` →
  `-32602`，消息逐字为：
  *「Parameter 'resource_properties' cannot be written to a Vector2 property: the value is a
  Dictionary ({"x":48.0,"y":48.0}) … **Send the property type's own shape: a JSON object naming
  its components for a vector/colour**」* —— 它点名要的那种写法**正是被它拒绝的那种**。
  对照：同一目标的 `{"radius":12.0}`（float）5/5 成功；兄弟工具
  `editor_setup_collision_shape` 用**同一个** `{"size":{"x":32,"y":32}}` 成功（`c4-007`）。
* 根因：`editor_write_scene_editor.cpp:725` 把 `property_value_from_json(...)` 的结果直接喂给
  `coerce_to_property_type`，**漏了 `shape_vector_from_json` 这一步**；
  `property_value_from_json` 的 DICTIONARY 分支（`tool_helpers.cpp:1647-1661`）**故意**保持
  Dictionary 不折成向量，向量折叠是 `shape_vector_from_json` 的职责。
  另外四处调用点（`project_write_resource_scene.cpp:128`、`project_setting_write.cpp:186/195`、
  `editor_shader_write.cpp:218`、`running_game_node_write.cpp:1128/1168`）**都先调了它**。
* 建议补丁（机械、语义唯一）：在 `:725` 前插入
  `shape_vector_from_json(resource_properties[keys[i]], target_type, "resource_properties", String(key), shaped, r_error)`，
  再 `coerce_to_property_type(shaped, ...)`；同时补一条针对向量属性的 doctest。
  之所以只登记不修：它会把「此前被拒的输入」变成成功，属于**行为面变更**，
  与 TASK-110 D2–D5 同类。**本批的缺陷复现调用留在 c4 的 manifest 里（intent=ok，note 写明 DEFECT REPRO）。**

**D-T111-3 ｜`editor_add_raycast` 的 `dimension` 完全不校验**
* 证据：`c4-033` 请求 `{"dimension":"4d","name":"Ray4d"}` → **成功**，回
  `{"added":true,"name":"Ray4d","node_path":"Ray4d","type":"RayCast3D"}`。
* 根因：`editor_node_instantiate.cpp:274`
  `Node *node = dimension == "2d" ? (Node *)memnew(RayCast2D) : (Node *)memnew(RayCast3D);`
  —— 除字面量 `"2d"` 之外的**任何**值（含 `"4d"`、拼错的 `"2D"`）都静默变成 3D 射线。
  这与同族 `editor_set_physics_layers`（`layer_type` 闭集，见 `editor_physics_write.cpp:68-81`）
  和 `editor_setup_navigation_region`（`mode` 闭集，`editor_node_setup.cpp:462`）的写法相反。
* 建议补丁：加 `resolve_raycast_dimension()`（照 `resolve_layer_property` 的形状），
  并考虑把契约 `dimension` 声明出 `enum:["2d","3d"]`（**契约面变更，需决策**）。

### C3. 【观察】一条会话侧的历史缺口（已修，非工具缺陷）

h2 首轮（`ex_anim/h2-task111`，94 次）有 2 处缺口，**根因都在会话侧**：
① `editor_remove_state_machine_state` 5/5 得 `-32001 State 'Extra0' … This machine holds: End, Start`
   —— 生成器的 `tool()` 辅助**只取前 5 个 ok**，我给的 11 条 `add_state_machine_state`
   （5 状态 + 1 blend_tree + 5 extras）被截成 5 条，于是 `BT` 与 `Extra0..4` 从未被创建，
   连带 `editor_set_blend_tree_node` 5/5 失败、`set_animation_tree_parameter` 的
   `BT/B1/blend_amount` 3 条失败；
② 修法是把这些**超出五条**的调用改用 `b.add(...)` 逐条追加。重跑（`ex_anim2/h2b-task111`，100 次）
  后 14 条目标全部 ≥5 次成功 + 1 次边界，失败数从 26 降到 14（全是探针）。

---

## D. 收尾：覆盖面变动、台账、决策、提交

### D1. 全语料口径（all-runs）前后对比

| 指标 | TASK-110（基线） | TASK-111（本轮） | 增量 |
|---|---|---|---|
| run 目录 / trace 文件 / `tools/call` | 87 / 148 / 7280 | 97 / 162 / **8286** | +10 / +14 / +1006 |
| 出现过的工具名 | 92 | **137** | **+45** |
| `0` 次 | 85 | **40** | **−45** |
| `1-4` 次 | 3 | **0** | −3 |
| `≥5` 次 | 89 | **137** | **+48** |
| `达标`（≥5 且 有效≥1 且 边界≥1） | 66 | **92** | **+26** |
| `计数达标缺证据` | 23 | 46 | +23 |
| 登记表「不可达」（仍登记） | 68 | **40** | **−28** |
| 登记表「已改判」 | 6 | **34** | +28 |
| **可达但未覆盖（<5 且非不可达）** | **20** | **0** | **−20** |

> 上述 `达标 92`、`call 8286` 是**两条台账读者缺陷修好之后**重算的值；
> 只修 `capture` 口径时是 91/8286，再修 sidecar 口径后是 **92/8286**。
> 契约口径仍是 **177 条**（`tools_list.renamed.json` 未变）。

### D2. 台账与决策

* `TOOL-COVERAGE.md` / `coverage.json` 由 `python tools/tool_coverage.py` 重跑生成
  （本轮最后一次：97 run / 162 trace / 8286 调用 / 137 工具）。
* 不可达登记表由 `recovery/work/task111/reclassify.py` 追加 **28 条 `reclassified`**
  （H1 7 + H2 14 + H3 7），每条带「为什么可以删」+ 证据 run；登记表现在
  `74 members / 34 reclassified / 40 still unreachable`。
* 决策记录：`DECISIONS.md` **D156**。

### D3. 如实声明：本轮**没有**做的事

* **没有改一行引擎代码**：三条引擎缺陷（§C2）逐条给了证据、根因 file:line 与建议补丁，
  但**没有重建、没有重跑十道门**（本轮引擎侧零改动，故不适用）。上一条已修的引擎缺陷仍是
  TASK-110 的 `3fdabe2d9a`。
* **没有为「非像素生效」放宽台账规则**：26 条写工具在台账上仍是「计数达标缺证据」，
  报告用**响应内引擎读回**给出真实生效证据，但**明说这是两种不同的证据强度**（§B4）。
* **没有碰 20 款正式工程与它们的历史 `runs/`**：只读。练习轮一律写在
  `runs/_exercises/` 与 `projects/_exercises/`（`projects/pong` 是复制源，本身零改动）。
* **没有做 H4 导航 / H5 音频 / H6 粒子 / H7 GUI / H8 导出 / H9 录放**：这 40 条是下一批的目标（§E）。
* **没有给 `runs/` 入库存档**：`.gitignore` 既有政策（第 43 行）排除 `godot-mcp/runs/`，
  报告引用的 trace/ledger 只留在盘上。

---

## E. 剩余 `<5` 清单与下一批建议

**仍登记为不可达的 40 条**（本轮把 H1/H2/H3 整族证伪之后剩下的全部）：

| 类 | 条数 | 工具 |
|---|---|---|
| **H4** 导航 | 6 | `editor_bake_navigation_mesh`、`editor_get_navigation_info`、`editor_set_navigation_layers`、`editor_setup_navigation_agent`、`editor_setup_navigation_region`、`running_game_move_player_to_target` |
| **H5** 音频 | 6 | `editor_add_audio_bus`、`editor_add_audio_bus_effect`、`editor_add_audio_player`、`editor_get_audio_bus_layout`、`editor_get_audio_info`、`editor_set_audio_bus_property` |
| **H6** 粒子 | 5 | `editor_create_particles`、`editor_get_particle_info`、`editor_set_particle_color_gradient`、`editor_set_particle_material`、`editor_set_particle_preset` |
| **H7** 编辑器 GUI/播放/输入注入 | 15 | `editor_analyze_screenshot_diff`、`editor_get_test_report`、`editor_play_scene`、`editor_reload_plugin`、`editor_remove_node_selection`、`editor_remove_output_log`、`editor_rescan_project_filesystem`、`editor_set_auto_dismiss_dialogs`、`editor_set_node_selection`、`editor_simulate_input_action`、`editor_simulate_input_sequence`、`editor_simulate_key`、`editor_simulate_mouse_click`、`editor_simulate_mouse_move`、`editor_stop_scene` |
| **H8** 导出 / Android | 5 | `os_deploy_to_android_device`、`os_list_android_devices`、`project_get_android_preset_info`、`project_get_export_info`、`project_list_export_presets` |
| **H9** 运行期录放 | 3 | `running_game_create_input_recording`、`running_game_play_input_recording`、`running_game_stop_input_recording` |

**「可达但未覆盖」已归零**，所以下一批的清单就是上表 40 条 —— 而且它们**需要先被逐族证伪一次**：

1. **①H4 导航（6 条，最高收益）**：前置是 `NavigationRegion2D` + 烘焙过的 `NavigationMesh` +
   `NavigationAgent2D`。这一族**可能真的需要** `--headless` 跑一次烘焙，或至少一次
   `editor_bake_navigation_mesh`；与 H1/H3 同办法（练习工程自带 `NavigationRegion2D` 与
   一份 `NavigationPolygon`）值得先试 —— 预计能再证伪一整族。
2. **②H5 音频（6 条）**：前置是「有一个 bus 布局」；`AudioServer` 在任何 Godot 进程里都在，
   这一族最可能只是「没人建过 bus」。成本最低，建议紧随 H4。
3. **③H9 录放（3 条）**：`create/play/stop_input_recording` 是一个自洽状态机，
   与 TASK-110 已证伪的 `capture_*` 同类（「需要前置运行态」的推断错得最集中）。
4. **④H6 粒子（5 条）**：`editor_create_particles` 自己创建节点，前置只是「有一个 2D 场景」，
   大概是可达的；`set_particle_color_gradient` 需要一个粒子材质。
5. **⑤H7 剩余 15 条 / ⑥H8 5 条**：H7 里 `editor_set_node_selection`/`remove_node_selection`/
   `rescan_project_filesystem`/`remove_output_log`/`play_scene`/`stop_scene` 大概率可达
   （TASK-110 已证明同类的 4 条可达）；`editor_simulate_*` 5 条与 `analyze_screenshot_diff`、
   `get_test_report` 需要单独判断（前者注入的是**编辑器进程**的输入，不能驱动游戏进程）。
   H8 的 Android 部署需要真机/无；`project_get_export_info`/`list_export_presets` 只需
   `export_presets.cfg`（工程里有），**很可能可达**。

**方法与口径建议（两条，都指向 DECISIONS 而不是报告措辞）**：

1. **先补一条「非像素生效」的判定口径**（本轮把它留在 §B4 没有擅自决定）：
   建议把 manifest 的 `intent` 再分出一类 `readback`，由**同一批次内的读回调用**充当
   写类工具的生效见证（要求：读回调用必须在同一 run、同一工具域、且读的是被写对象），
   `verify_coverage_batch.py` 认这类见证但**明文标注证据等级**（`failed_call` > `file_effect`
   > `pixel_effect` > `readback`）。不这么做的话，rename/挂脚本/动画/3D 这一大类写工具
   会永远停在「计数达标缺证据」。
2. **把「契约 177 条 `inputSchema.properties` vs 注册 schema」做一次成员级对照**
   （TASK-110 §E 已建议，本轮又抓到 D-T111-2/D-T111-3 两条只靠调用侧探测发现的成员级问题）。
   现在有了 `recovery/work/task111/dump_schemas.py` 这个起点，做成一次性对照的边际成本已经很低。

---

## F. 提交与跑后的进程/端口检查

### F1. 主仓提交

```
$ git log --oneline -1
787e01a feat(godot-mcp): TASK-111 - coverage loop batch 2: ... (212 files changed, 18848 insertions(+), 1241 deletions(-))
```

**引擎仓本轮零改动**（`F:\moonbit-hof-rs\godot-mcp\godot` 未做任何提交；
工作树里没有本任务产生的改动）。上一轮已修的引擎缺陷仍是 TASK-110 的 `3fdabe2d9a`，
本轮**没有**重建、**没有**重跑十道门 —— 因为它们不是本任务产生的。

### F2. 提交后仍未纳入的工作树条目（逐条说明，都不是本任务的产物）

```
$ git status --short
 M godot-mcp/recovery/work/task104/logs/git-housekeeping.err.txt   <- TASK-104 收尾时的既有状态
 M godot-mcp/recovery/work/task104/logs/git-housekeeping.out.txt   <- 同上
?? godot-mcp/dist/                                                <- TASK-107/109 的产物
?? godot-mcp/recovery/reports/ACCEPTANCE-TASK-107.md              <- TASK-107 的产物
?? godot-mcp/projects/_exercises/ex_write2/                       <- 本任务被中途放弃的工程副本
?? godot-mcp/projects/_exercises/ex_write3/                       <- 同上
?? godot-mcp/projects/_exercises/ex_write4/                       <- 同上
```

`ex_write2` 是一次被**主动终止**的运行留下的半成品（会话文件当时是旧的，
用 `job_kill` 停掉后换了新工程），`ex_write3` / `ex_write4` 是会话修好前两次未收口的尝试。
三者**只留在盘上**、没有入库，因为入库的 `ex_write`（首轮，c4 的「修复前」对照）与
`ex_write5`（收口轮）已经覆盖了前后对比。**没有删除它们**（破坏性命令默认拒绝）。

### F3. 跑后的进程与端口检查（铁律 4）

```
$ netstat -ano | findstr "LISTENING" | findstr "9888 9889 9877"   ->  NO_LISTENERS
$ tasklist  | findstr /I godot                                    ->  NO_GODOT_PROC
```

本轮 6 次会话运行（c4 首轮 / c4c / c4-v5 / c5 / h1 / h2b / h3）全部用同一对端口
**9888 / 9889**，每次跑前都先确认这两个端口无监听、无 `godot` 进程；
用户端口 **9877** 全程未被占用（构建/导入用的一次性进程也在同一秒内退出）。

