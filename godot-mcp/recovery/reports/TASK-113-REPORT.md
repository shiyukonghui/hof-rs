# TASK-113 — 覆盖驱动循环第四批：C 段（H4 导航 / H5 音频 / H9 录放 / H6 粒子，20 条 0 次工具全部上线）+ D-T111-2/-3 的修后线上对比 + 见证从调用级升级到内容级

> 本报告的数字来自 `coverage.json`（`python tools/tool_coverage.py` 重算）、五份真实会话的
> `runs/_exercises/**/trace-*.jsonl` 与 `ledger-*.txt`，以及四个练习工程 `--quit-after 5` 的
> **真实退出码**。**没有从任何报告表格转抄**。
> `projects/` 下 **20 款正式工程**与它们的历史 `runs/` **只读未动**。
> **本轮引擎侧零改动**（没有碰 `godot/modules/mcp_server/`），因此按铁律 7 的重建条件**未触发**：
> 没有重建两变体、没有重跑十道门。二进制的 `--version` 仍是 `4.8.dev.mono.custom_build.3fdabe2d9`
> —— 这正是 TASK-112 §A4 声明的那个「包含三条缺陷修复」的锚点，本轮所有线上会话都在它上面跑。

---

## 0. 一句话结论与如实边界

**A 段（四族 20 条工具）、B 段（修后线上对比）、C 段（内容级见证）、D 段（台账/登记表/决策/提交）全部完成。**

1. **A 段**：新建 4 个练习工程（`projects/_exercises/ex_nav`、`ex_audio`、`ex_rec`、`ex_particles`）
   + 5 组会话（h4 40 次、h5 43、h6 40、h9 28，另加 B 段的 b-fix 7 次，共 **158 次新调用**）。
   H4 6 条 / H5 6 条 / H6 5 条 / H9 3 条**全部 ≥5 次调用**（实测 6–9 次），**可构造的边界全部造出**，
   每条新调用都带同 run 的内容级读回见证。四个工程 `--headless --quit-after 5` **退出码全 0**。
2. **B 段**：在**修后二进制**上用真实会话重发了 TASK-111 的两个缺陷请求。
   D-T111-2 `{"size":{"x":48,"y":48}}`：**修前 `-32602`（工具自己的报错点名要的正是这种写法）→ 修后 `ok`**，
   回答含 `properties_set:["size"]` 与 `changed.size = {new:{48,48}, old:{20,20}}`；
   D-T111-3 `dimension:"4d"`：**修前 `ok` + 静默造出 `RayCast3D` → 修后 `-32602
   'dimension' must be one of '2d' or '3d'; got '4d'` + `data.suggestion`**，`"2D"` 同样被拒、
   `"2d"` 正常建 `RayCast2D`（正面对照）。修前修后逐字并列见 §B。
3. **C 段**：`readback` 见证从**调用级**升级为**内容级**：manifest 的 `readback` 声明新增
   `expect`（必须**逐字**出现在见证调用回包里的键/值）与 `expect_absent`（减法型写入的「读回来的
   东西不在了」，以 `expect` 作同一主体的锚点）。**未声明内容级期望的声明一律不再授予档位**——
   这不是装饰，它当场把 TASK-112 的三条「只是发生过一次读调用」的见证降级（§C3）。
   38 条声明 → 复核通过 **33**（**33 条全部逐字命中**）、被拒 **5**（含 2 条 TASK-112 就拒过的）。
4. **D 段**：`TOOL-COVERAGE.md` / `coverage.json` 重算（102 run / 168 trace / 8444 调用 / **157** 出现过）；
   不可达登记表**改判 20 条**（H4/H5/H6 全部 + H9 三条）；`DECISIONS.md` **D158**；主仓提交；本报告。
5. **全语料前后**：0 次 **40 → 20**、≥5 次 137 → **157**、达标 **92 → 102**、
   证据档位 `pixel_effect` 27→**34**、`file_effect` 24→24、`readback` 77→**87**、
   `count_only` 9→**12**、`no_calls` 40→**20**。

**必须同时说清的边界（本轮没有做到 / 证据强度不足的地方）**：

* **H6 的 `pixel_effect` 档位有已知混淆**：`editor_create_particles` 造出的 GPUParticles2D 默认
  `emitting:true`，编辑器 2D 视口里的粒子在动，于是**任意相邻两次截图都会不同**。这不是推断：
  **只读的 `editor_get_particle_info` 也报出 70–95 像素差**，而读调用不可能动画面。
  因此 H6 写工具落到 `pixel_effect` 档是台账规则自己给的，**真正把调用与效果绑起来的是内容级读回**
  （`editor_get_particle_info` 读回 preset/param/gradient 的真值）。这条不许被读成「像素证明」。
* **`running_game_stop_input_recording` 无边界可造**：它的实现里 `(void)r_error;`，**没有任何失败路径**
  （进程无录制时它也是成功——「没有东西可收」是答案）。因此它只能落在 `计数达标缺证据`，
  即使它有 7 次调用、内容级见证通过。**这是我造不出边界，不是没造。**
* **本轮没做 H1 那 5 条 `count_only`**（`editor_add_mesh_instance`、`editor_setup_camera_3d`、
  `editor_setup_lighting`、`editor_set_material_3d`、`editor_setup_world_environment`）：
  它们的见证读在 `h1` run 里缺失（只读了 `editor_get_viewport_3d_camera`，不读被建的节点）。
  要补必须**重跑一次 h1 会话并把节点级读调用加进去**，本轮预算没做到。**这是待办，不是结论。**
* **3 条 TASK-112 的 `witness_read` 被本轮降级**（`editor_set_node_script`、`editor_set_control_theme`、
  `editor_remove_animation`）：读完它们的声明 run 后发现见证回包里**没有**被写的值
  （`editor_get_node_properties` 在该 run 只读了 name / collision_layer / wait_time），
  `editor_remove_animation` 的列表读更是在删除**之前**。旧口径下它们能过，正是「调用级」的证据下限太低；
  新口径下它们回到 `count_only`。§C3 逐条给出原因。
* **`projects/` 与 `runs/` 不入库**（沿用 TASK-110/111/112 的既有状态：`runs/` 被 gitignore，
  `projects/_exercises/*` 一直是未跟踪目录）。可复现性靠**已入库的生成器**
  `recovery/work/task113/gen_family_sessions.py prepare`（它把每个工程的 `mk_probe.gd` 逐字节写在源码里），
  而不是靠把 `.godot/` 缓存与 PNG 拖进 git。

---

## 1. 交付物与证据路径

| 交付物 | 路径 | 说明 |
|---|---|---|
| 四个练习工程 | `projects/_exercises/{ex_nav,ex_audio,ex_rec,ex_particles}/` | 每个都从 `ex_grid` 拷贝骨架，前置由引擎自己的 API 生成（`mk_probe.gd`） |
| 场景/素材生成器 | `projects/_exercises/*/mk_probe.gd` | ex_nav/ex_rec：Node2D 根 + NavigationRegion2D（带 outline 的 NavigationPolygon）+ CharacterBody2D Player（带可见 Polygon2D + NavigationAgent2D）+ Goal + HUD；ex_audio：AudioServer 场景 + 5 个真 RIFF WAVE；ex_particles：带一个 GPUParticles2D 的场景 |
| 会话与声明 | `tools/sessions/_exercises/{ex_nav/h4,ex_audio/h5,ex_rec/h9,ex_particles/h6}/` | 每组一份 `*-session.json` + 一份带 `readback`/`expect` 的 `*-manifest.json` |
| B 段会话 | `tools/sessions/_exercises/ex_write4/b-fix-session.json` | 修后重发 D-T111-2/-3 的原请求 |
| 台账（内容级） | `tools/tool_coverage.py` | 新增 `expect` / `expect_absent` 复核、payload 变体匹配、拒绝理由 |
| 台账产物 | `TOOL-COVERAGE.md` / `coverage.json` | 重算 |
| 登记表 | `tools/tool_coverage_unreachable.json` | `reclassified` +20（H4/H5/H6/H9） |
| 派生脚本 | `recovery/work/task113/{gen_family_sessions,add_expects,probe_expects,dump_witnesses,dump_run_tool,pre_post_defects,reclassify,tier_delta}.py` | 生成、声明、**复核**与前后对比都可重跑 |
| 决策 | `F:\moonbit-hof-rs\DECISIONS.md` **D158** | 选项、否决理由、回滚点 |
| 会话账 | `runs/_exercises/{ex_nav/h4-task113,ex_audio/h5-task113,ex_rec/h9-task113,ex_particles/h6-task113,ex_write4/b-fix-task113}/` | trace + ledger + shots（`runs/` 不入库，见 §0） |

---

## A. 四族线上覆盖（逐族清单、次数、档位、边界）

所有数字直接取自 `coverage.json`（重算后）。`有效/边界` 按台账口径（`ok_effect_observed` /
`ok_file_effect_observed` / 读类回包 / `ok=false`）。

| 族 | tool | 调用 | 有效 | 边界 | 证据档位 | 状态 | 内容级见证（读回的东西） |
|---|---|---|---|---|---|---|---|
| H4 | `editor_setup_navigation_region` | 6 | 0 | 1 | `readback` | 计数达标缺证据 | `editor_get_navigation_info` → `"RegionA"` |
| H4 | `editor_setup_navigation_agent` | 6 | 0 | 1 | `readback` | 计数达标缺证据 | 同上 → `"max_speed"` |
| H4 | `editor_set_navigation_layers` | 7 | 0 | 2 | `readback` | 计数达标缺证据 | 同上 → `"navigation_layers":2` |
| H4 | `editor_bake_navigation_mesh` | 6 | **1** | 1 | `pixel_effect` | **达标** | 同上 → `"baked":true` |
| H4 | `editor_get_navigation_info` | 6 | 5 | 1 | `readback`（own_payload） | **达标** | 读类回包即证据 |
| H4 | `running_game_move_player_to_target` | 6 | **5** | 1 | `pixel_effect` | **达标** | `running_game_get_node_properties` → `"position"` |
| H5 | `editor_add_audio_bus` | 7 | 0 | 2 | `readback` | 计数达标缺证据 | `editor_get_audio_bus_layout` → `"Music"` |
| H5 | `editor_add_audio_bus_effect` | 7 | 0 | 2 | `readback` | 计数达标缺证据 | 同上 → `AudioEffectAmplify` |
| H5 | `editor_add_audio_player` | 6 | 0 | 1 | `readback` | 计数达标缺证据 | `editor_get_node_properties` → `AudioStreamPlayer2D` |
| H5 | `editor_get_audio_bus_layout` | 7 | 6 | 1 | `readback`（own_payload） | **达标** | 读类回包即证据 |
| H5 | `editor_get_audio_info` | 6 | 5 | 1 | `readback`（own_payload） | **达标** | 读类回包即证据 |
| H5 | `editor_set_audio_bus_property` | 8 | 0 | 3 | `readback` | 计数达标缺证据 | `editor_get_audio_bus_layout` → `"volume_db":-6` |
| H9 | `running_game_create_input_recording` | 7 | 0 | 1 | `readback` | 计数达标缺证据 | `running_game_stop_input_recording` → `"event_count":2` |
| H9 | `running_game_play_input_recording` | 7 | **6** | 1 | `pixel_effect` | **达标** | `running_game_get_node_properties` → `"position"` |
| H9 | `running_game_stop_input_recording` | 7 | 0 | **0** | `readback` | 计数达标缺证据 | 同上 → `"position"` |
| H6 | `editor_create_particles` | 8 | 0 | 3 | `readback` | 计数达标缺证据 | `editor_get_particle_info` → `"process_material_slot":"process_material"` |
| H6 | `editor_set_particle_preset` | 7 | 5 | 2 | `pixel_effect`（有混淆，见 §0） | **达标** | 同上 → `"amount":24` |
| H6 | `editor_set_particle_material` | 8 | 5 | 3 | `pixel_effect`（有混淆） | **达标** | 同上 → `"damping_min"` |
| H6 | `editor_set_particle_color_gradient` | 9 | 6 | 3 | `pixel_effect`（有混淆） | **达标** | 同上 → `"color_stop_count":2` |
| H6 | `editor_get_particle_info` | 7 | 6 | 1 | `pixel_effect`（有混淆） | **达标** | 读类回包即证据 |

**20 条里 10 条 `达标`、10 条 `计数达标缺证据`**（後者全部带内容级 `readback` 档位、全部 ≥5 次调用；
它们的「有效」为 0 是因为它们不动像素/文件，而不是因为没生效——生效由同 run 的引擎读回逐字证明）。

### A1. 各族会话的真实数字与工程可用性

| 会话 | run | 调用 | 失败（边界） | 关键取证 |
|---|---|---|---|---|
| h4 导航 | `runs/_exercises/ex_nav/h4-task113` | 33（editor）+ 7（game） | editor 6 / game 1 | 第 1 次 bake 让编辑器 2D 视口变化 **155 978 像素**（`report.md` 独立复算一致）、bake 回答 `before_polygon_count:0 → polygon_count:1 / baked:true`；5 次移动 `distance_traveled` = 178.09 / 399.29 / 181.44 / 166.56 / 461.23 |
| h5 音频 | `runs/_exercises/ex_audio/h5-task113` | 43 | 10 | 6 条总线（含插在 index 0 之后的 `Ui`）、5 个效果、5 个播放器；`editor_get_audio_bus_layout` 读回 `volume_db:-6` |
| h6 粒子 | `runs/_exercises/ex_particles/h6-task113` | 40 | 12 | 5 个系统 + fire/smoke/magic/explosion/rain 预设 + 5 组参数 + 5 条渐变；`editor_get_particle_info` 读回 `amount` 24/16/24、`color_stop_count` 2/3/2/2 |
| h9 录放 | `runs/_exercises/ex_rec/h9-task113` | 28（game） | 2 | 5 轮 create→play(显式 2 事件)→stop，每轮 `event_count:2`、`event_types.key:2`；随后 **create→stop→play（不带 `events`）真的把 Player 从 x=100 移到 x=151**（重算像素差 1152），`set_node_property` 复位后可复算 |
| b 段 | `runs/_exercises/ex_write4/b-fix-task113` | 7 | 2 | 见 §B |

四个练习工程（`--headless --quit-after 5`，cmd 启动，**无重定向**）：

```
EX_NAV_EXIT=0      EX_AUDIO_EXIT=0      EX_REC_EXIT=0      EX_PARTICLES_EXIT=0
```

五组会话的 `import` 与 `ledger-*.txt` 生成**都 exit 0**（`run_game_session.ps1` 的 `import : exit 0`、
`editor: ledger exit 0` / `game: ledger exit 0`）。

### A2. 值得单独说的三条覆盖事实

1. **`editor_bake_navigation_mesh` 的「生效」是像素级的，不是推断**：它的第一次 bake 让编辑器视口
   变化 155 978 像素，且 `report.md` 用自己的 Pillow 复算得到同一个数（`155978`）。
   前提是 `NavigationPolygon` **带 outline** ——`NavMeshGenerator2D::generator_bake_from_source_geometry_data`
   读的正是 `get_outline(i)`（`modules/navigation_2d/2d/nav_mesh_generator_2d.cpp:337`），
   所以练习工程的 `mk_probe.gd` 用引擎自己的 `NavigationPolygon::add_outline()` 造前置，
   **不是**手写 `.tres`。
2. **H9 的「回放真的动了」是按要求的**：`running_game_play_input_recording` 通过
   `Input::parse_input_event` 注入录制事件（`running_game_input.cpp:532`），玩家脚本
   `Input.is_key_pressed(KEY_RIGHT)` 轮询（`core/input/input.cpp:895-901` 直接维护 `keys_pressed`），
   复位到 x=100 后再回放 → x=151。**回放用的是 create→stop 得到的录制（不传 `events`）**，
   即完整链 `create → play → stop` 的自然延伸，而不是手喂一个数组充数。
3. **H5 的素材是真音频**：`assets/tone{1..5}.wav` 是生成器写出的真 RIFF/PCM（440/660/880/静音/220 Hz），
   `--import` 把它们当资产导入（导入日志逐条列出 `tone1..5.wav`）。

---

## B. D-T111-2 / D-T111-3 的修后线上对比（真实会话，非 doctest）

**修前**（TASK-111 的原始 trace，本轮只读，逐字引自
`runs/_exercises/ex_write4/c4-final-task111/trace-editor.jsonl` 与
`runs/_exercises/ex_write3/c4c-task111/trace-editor.jsonl`）：

| # | 请求（逐字） | 修前 |
|---|---|---|
| D-T111-2 | `{"node_path":"BodyA/CollisionShape2D","property":"shape","resource_properties":{"size":{"x":48.0,"y":48.0}},"resource_type":"RectangleShape2D"}` | `ok:false` / `-32602` / `Parameter 'resource_properties' cannot be written to a Vector2 property: … Send the property type's own shape: a JSON object naming its components for a vector/colour …`（**它点名要的写法正是它拒绝的写法**） |
| D-T111-3 | `{"dimension":"4d","name":"Ray4d"}` | `ok:true` / `{"added":true,"name":"Ray4d","node_path":"Ray4d","type":"RayCast3D"}`（**静默造出一个 3D 射线**，且在 ex_write4 的场景里留下了 `Ray4d` 这个节点） |

**修后**（本轮 `runs/_exercises/ex_write4/b-fix-task113/trace-editor.jsonl`，同一台机器、同一个
`projects/_exercises/ex_write4/scenes/main.tscn`，其中 `BodyA/CollisionShape2D` 与旧的 `Ray4d` 都还在）：

| # | 请求（逐字） | 修后 |
|---|---|---|
| D-T111-2 | 同上 | `ok:true` / `{"changed":{"size":{"new":{"x":48.0,"y":48.0},"old":{"x":20.0,"y":20.0}}},"ignored":{},"ignored_count":0,"node_path":"BodyA/CollisionShape2D","properties_set":["size"],"property":"shape","resource_type":"RectangleShape2D"}` —— **含 `properties_set`**，且 `changed.size.old` 是上一枚 `RectangleShape2D` 的 (20,20)，即真的替换了子资源 |
| 读回 | `editor_get_node_properties {"path":"BodyA/CollisionShape2D","properties":["shape"]}` | `ok:true` / `{"node_path":"BodyA/CollisionShape2D","properties":{"shape":{"type":"RectangleShape2D","val…` —— 引擎自己的视图 |
| D-T111-3 | `{"dimension":"4d","name":"Ray4dPost"}` | `ok:false` / `-32602` / `'dimension' must be one of '2d' or '3d'; got '4d'` / `data.suggestion: Parameter 'dimension' accepts a string, one of: 2d\|3d, optional (default "2d")` |
| 同上 | `{"dimension":"2D","name":"Ray2DUp"}` | `ok:false` / `-32602` / `… got '2D'`（同一闭集，大小写不放松） |
| 正面对照 | `{"dimension":"2d","name":"Ray2dPost"}` | `ok:true` / `{"added":true,"name":"Ray2dPost","node_path":"Ray2dPost","type":"RayCast2D"}`（**合法值不被 dimension 规则拒绝**） |

取证脚本：`recovery/work/task113/pre_post_defects.py pre` / `… post <run_dir>`（只读 trace）。

---

## C. 见证升级：从「那一次读调用发生过」到「写进去的值能从引擎自己的回答里读回来」

### C1. 机制（`tools/tool_coverage.py`）

* 声明新增两个字段（写在会话 manifest 的 `readback` 数组里）：
  * `expect`：一个或一组**字面量**，必须逐字出现在**见证调用的回包**里；
  * `expect_absent`：减法型写入（删除/清空）用的「读回来的东西不在了」，**必须与 `expect` 同时声明**
    ——`expect` 里的主体锚点（例如 `"node_path":"AT4"`）保证「不在」是在**同一个主体**上判的，
    而不是在别的节点上碰巧不在。
* 比对文本取回包本身；trace 若存的是 JSON-RPC 信封（把答案转义在 `content[0].text` 里），
  本工具会**同时搜未转义/解包后的拼写**（`payload_variants()`），并读取已核验的 sidecar（回包超内联预算时）。
* **没声明任何内容级期望的声明不再授予档位**，拒绝理由逐条写出（这是升级的用意所在）。

### C2. 结果（38 条声明）

| | 数量 |
|---|---|
| 声明总数 | **38**（TASK-112 的 22 + 本轮 16） |
| 复核通过 | **33**（**33 条全部带内容级期望并逐字命中**） |
| 被拒 | **5** |
| 未被内容复核的 | **0** |

被拒的 5 条（`coverage.json` 的 `readback_declarations.rejected` 逐条带理由）：

| tool | 拒绝理由（台账原文） |
|---|---|
| `editor_add_gridmap` | `no ok=true substantive call of editor_get_scene_tree in that run`（TASK-112 已拒） |
| `editor_connect_signal` | `no ok=true substantive call of editor_list_signal_connections in that run`（TASK-112 已拒） |
| `editor_set_node_script` | `no content-level expect/expect_absent declared: the witness would only prove that a read call happened` |
| `editor_set_control_theme` | 同上 |
| `editor_remove_animation` | 同上 |

### C3. 三条被降级的 TASK-112 见证：为什么没有「诚实的字面量」可写

这三条不是「懒得写」，是把它们的声明 run 读完之后**找不到**任何能把写入与读回绑起来的载荷：

* `editor_set_node_script` ← `editor_get_node_properties` @ `ex_write5/c4-v5-task111`：该 run 里
  `editor_get_node_properties` 只有 3 条合格回包，逐字为
  `{"node_path":"Host/Ren1","properties":{"name":"Ren1"},…}`、
  `{"node_path":"PB1","properties":{"collision_layer":1,"collision_mask":4},…}`、
  `{"node_path":"Tick","properties":{"wait_time":0.75},…}` —— **没有一条读 `script`**
  （会话里那次 `{"path":"C4Node1","properties":["script"]}` 在该 run 里根本没有合格回包）。
* `editor_set_control_theme` ← 同一个见证工具、同一个 run：同样 3 条回包，**没有一条读 `theme`**。
* `editor_remove_animation` ← `editor_list_animations` @ `ex_anim2/h2b-task111`：5 条列表回包**全部在删除之前**
  （都含 `"count":8` 与 `Anim1..Anim8`），而删除发生在它们**之后** —— 事后读回不存在，
  所以既不能 `expect` 也不能 `expect_absent`。

**结论**：TASK-112 那句「`witness_read` 只是调用级」在报告里是**如实声明**的，本轮把它变成了**可机械执行的判定**，
代价就是这 3 条回到 `count_only`。要恢复它们，需要的是**新的读调用**（重跑一次带节点级读回的 c4 会话），
而不是放宽判定 —— 下一批的第一优先级就写在这里。

### C4. 档位变动（HEAD 的 `coverage.json` → 本轮，`tier_delta.py` 逐条输出）

| 档位 | TASK-112 | 本轮 | 说明 |
|---|---|---|---|
| `pixel_effect` | 27 | **34** | +7 全部来自新族：`editor_bake_navigation_mesh`、`running_game_move_player_to_target`、`running_game_play_input_recording`、`editor_get_particle_info`、`editor_set_particle_preset`、`editor_set_particle_material`、`editor_set_particle_color_gradient` |
| `file_effect` | 24 | 24 | 不变 |
| `readback` | 77 | **87** | −3（下面三条被降级）＋ 13 条新工具（H4 4 / H5 4 / H6 1 / H9 2 落到 `readback` 而非更强档） |
| `count_only` | 9 | **12** | −3 条被降级者：`editor_set_node_script`、`editor_set_control_theme`、`editor_remove_animation` |
| `no_calls` | 40 | **20** | −20（本轮上线） |

逐条变动（只列变了的）：

```
editor_bake_navigation_mesh          no_calls -> pixel_effect   未达(0) -> 达标
running_game_move_player_to_target   no_calls -> pixel_effect   未达(0) -> 达标
running_game_play_input_recording    no_calls -> pixel_effect   未达(0) -> 达标
editor_get_particle_info             no_calls -> pixel_effect   未达(0) -> 达标
editor_set_particle_preset           no_calls -> pixel_effect   未达(0) -> 达标
editor_set_particle_material         no_calls -> pixel_effect   未达(0) -> 达标
editor_set_particle_color_gradient   no_calls -> pixel_effect   未达(0) -> 达标
editor_get_navigation_info           no_calls -> readback       未达(0) -> 达标
editor_get_audio_bus_layout          no_calls -> readback       未达(0) -> 达标
editor_get_audio_info                no_calls -> readback       未达(0) -> 达标
editor_setup_navigation_region       no_calls -> readback       未达(0) -> 计数达标缺证据
editor_setup_navigation_agent        no_calls -> readback       未达(0) -> 计数达标缺证据
editor_set_navigation_layers         no_calls -> readback       未达(0) -> 计数达标缺证据
editor_add_audio_bus                 no_calls -> readback       未达(0) -> 计数达标缺证据
editor_add_audio_bus_effect          no_calls -> readback       未达(0) -> 计数达标缺证据
editor_add_audio_player              no_calls -> readback       未达(0) -> 计数达标缺证据
editor_set_audio_bus_property        no_calls -> readback       未达(0) -> 计数达标缺证据
editor_create_particles              no_calls -> readback       未达(0) -> 计数达标缺证据
running_game_create_input_recording  no_calls -> readback       未达(0) -> 计数达标缺证据
running_game_stop_input_recording    no_calls -> readback       未达(0) -> 计数达标缺证据
editor_set_node_script               readback -> count_only     （状态不变：计数达标缺证据）
editor_set_control_theme             readback -> count_only     （状态不变）
editor_remove_animation              readback -> count_only     （状态不变）
```

---

## D. 收尾

### D1. 全语料口径（all-runs）前后对比

| 指标 | TASK-112（基线） | TASK-113（本轮） | 增量 |
|---|---|---|---|
| run 目录 / trace 文件 / `tools/call` | 97 / 162 / 8286 | **102 / 168 / 8444** | +5 / +6 / **+158** |
| 出现过的工具名 | 137 | **157** | **+20** |
| `0` 次 | 40 | **20** | **−20** |
| `>=5` 次 | 137 | **157** | +20 |
| `达标` | 92 | **102** | **+10** |
| `计数达标缺证据` | 45 | **55** | +10 |
| 证据档位 | pixel 27 / file 24 / readback 77 / count_only 9 / no_calls 40 | **pixel 34 / file 24 / readback 87 / count_only 12 / no_calls 20** | 见 §C4 |
| readback 声明 | 22 声明 / 20 通过 / 2 拒（调用级） | **38 声明 / 33 通过（全部内容级逐字命中）/ 5 拒** | 口径升级 |
| 登记表「不可达」 | 74 成员 / 34 改判 | **74 成员 / 54 改判**（+20） | H4/H5/H6/H9 全部改判 |
| 契约条数 | 177 | **177**（本轮**未改契约**） | 0 |

### D2. 不可达登记表

`tools/tool_coverage_unreachable.json` 新增 **20 条 `reclassified`**（`recovery/work/task113/reclassify.py` 写入），
每条带 `from` 类别、`why`（前置是什么、跑了什么、观察到什么）、`evidence`（trace 路径）、`batch`/`task`。
**没有删除任何条目**（登记表自己的规则如此）。仍登记为不可达的 **20 条**（H7 15 + H8 5）见 §E。

### D3. 决策与提交

* 决策记录：`DECISIONS.md` **D158**（选项、否决理由、三条被降级的见证、H6 混淆、回滚点）。
* 提交见 §F。

### D4. 如实声明：本轮**没有**做的事

* **没有改引擎**（`godot/modules/mcp_server/` 一个字节未动）→ 按铁律 7 **不触发**两变体重建与十道门。
* **没有做 H1 的 5 条 `count_only`**（见 §0）。
* **没有为 H6 消除像素混淆**（要消除得让所有粒子系统停发后再逐调用测量；混淆**已由只读调用也报像素差证明存在**）。
* **没有把 `projects/` 与 `runs/` 入库**（沿用既有状态；见 §0 的可复现性说明）。
* **没有碰 20 款正式工程与它们的历史 `runs/`**：只读（本轮所有新 run 都在 `runs/_exercises/` 下）。
* **一次铁律 1 的失误（如实披露）**：在核对四个工程 `--quit-after 5` 退出码时，我第一次用了
  `>nul 2>nul` 做静默，随后**立刻用无重定向的同一命令重跑并以该输出作为证据**（§A1 的四行 EXIT 来自重跑那次）。
  除这一次只读调用外，本轮所有构建/运行/核对都没有使用 shell 重定向（日志一律由
  `run_game_session.ps1` 自己的 `Start-Process -RedirectStandardOutput/Error` 产生）。

---

## E. 剩余 `<5` 与下一批建议

**剩余 20 条 0 次调用**（全部是 H7 与 H8；H4/H5/H6/H9 已清零）：

| 类 | 条数 | 工具 |
|---|---|---|
| **H7** 编辑器 GUI / 编辑器侧播放与输入注入 / 编辑器侧测试 | 15 | `editor_play_scene`、`editor_stop_scene`、`editor_set_node_selection`、`editor_remove_node_selection`、`editor_remove_output_log`、`editor_reload_plugin`、`editor_rescan_project_filesystem`、`editor_analyze_screenshot_diff`、`editor_set_auto_dismiss_dialogs`、`editor_simulate_key`、`editor_simulate_mouse_click`、`editor_simulate_mouse_move`、`editor_simulate_input_action`、`editor_simulate_input_sequence`、`editor_get_test_report` |
| **H8** 导出 / Android | 5 | `project_get_export_info`、`project_list_export_presets`、`os_list_android_devices`、`project_get_android_preset_info`、`os_deploy_to_android_device` |

**下一批建议（按价值排序）**

1. **先把 3 条被降级的见证补成真的内容级**：重跑一次 c4/c5 型会话，在读回阶段加上
   `editor_get_node_properties {"path":"C4Node1","properties":["script"]}`、
   `{"path":"Panel","properties":["theme"]}` 与**删除之后**的 `editor_list_animations`。
   这三条比新覆盖 20 条更重要 —— 它们证明的是**既有档位**的质量。
2. **H1 的 5 条 `count_only`**：重跑一次 h1 并在末尾加节点级读回
   （`editor_get_scene_tree` 读 `MeshA..MeshE` / `editor_get_node_properties` 读材质的 `material_override`），
   成本一次会话。
3. **H7 必须分类而不是继续笼统写「不可达」**：`editor_simulate_*` 5 条注入的是**编辑器进程**的输入，
   **结构性不可达（设计使然，D59/GDR-21）**，与「本轮没做」是两回事；
   而 `editor_get_selection`/`editor_set_node_selection`/`editor_remove_node_selection`/
   `editor_get_output_log`/`editor_remove_output_log`/`editor_set_auto_dismiss_dialogs`/
   `editor_reload_plugin`/`editor_rescan_project_filesystem` 在**编辑器端点存在**的前提下**很可能可达**
   （TASK-110 已经用 c23 证伪过其中 4 条）。建议先建一个 `ex_editor` 练习工程做一次「编辑器 GUI 状态」批次。
4. **H8 的 5 条**：`project_get_export_info` / `project_list_export_presets` 只需要 `export_presets.cfg`
   （每个工程都有，`project_get_export_info` 甚至可能不需要真导出），建议下一批直接试；
   `os_list_android_devices` / `os_deploy_to_android_device` / `project_get_android_preset_info`
   需要真机或 Android 预设，建议在登记表里明确写「需要外部设备」而不是「不可达」。
5. **H6 的像素混淆要记账**：若要用 `pixel_effect` 档位支撑粒子族，请在会话里**先停掉所有粒子发射**
   （`emitting=false`）再逐调用测量；否则该族应当只认内容级 `readback`。

---

## F. 提交

```
$ cd F:\moonbit-hof-rs && git log --oneline -2
<见下一条提交>  docs(godot-mcp): TASK-113 - the report and the D158 decision record
1a107bf          feat(godot-mcp): TASK-113 (D158) - the C batch of the coverage loop:
                 H4/H5/H6/H9 go from 0 calls to covered, and the readback witness is
                 upgraded from the call level to the content level
                 27 files changed, 7135 insertions(+), 1076 deletions(-)
```

* 提交顺序是有意的：**先落台账/声明/登记表/派生脚本**（`1a107bf`），再落**报告与决策**，
  这样「改动 → 提交 → 决策日志」三者可互查。
* **引擎仓（`F:\moonbit-hof-rs\godot-mcp\godot`）本轮无提交**：`git status` 干净，
  `godot/modules/mcp_server/` 一个字节未改，因此二进制仍是 `3fdabe2d9`，也无 push。
* 提交后仍未纳入工作树的主仓条目（**都不是本任务的产物，一律未删除**）：
  `godot-mcp/dist/`（TASK-107/109）、`godot-mcp/projects/_exercises/{ex_write2,ex_write3,ex_write4,ex_audio,ex_nav,ex_particles,ex_rec}/`
  （练习工程，沿用 TASK-110/111/112 的未跟踪状态；可由 `recovery/work/task113/gen_family_sessions.py prepare` 重建）、
  `godot-mcp/tools/__pycache__/`（本轮派生脚本 import `tool_coverage.py` 产生的字节码缓存）、
  `godot-mcp/recovery/reports/ACCEPTANCE-TASK-107.md`、
  `godot-mcp/recovery/work/task104/logs/git-housekeeping.{out,err}.txt`（TASK-104 的既有改动）。

---

## G. 铁律执行与跑后检查（铁律 4）

```
pre-h4   netstat LISTENING 9888/9889/9877 -> NONE ; tasklist godot -> NONE
pre-h5   netstat LISTENING 9888/9889/9877 -> NONE ; tasklist godot -> NONE
pre-h6   netstat LISTENING 9888/9889/9877 -> NONE ; tasklist godot -> NONE   （与 H6 启动同一条命令内先查）
pre-h9   netstat LISTENING 9888/9889/9877 -> NONE ; tasklist godot -> NONE   （同上）
pre-b    netstat LISTENING 9888/9889/9877 -> NONE ; tasklist godot -> NONE   （同上）
post     netstat LISTENING 9888/9889/9877 -> NONE ; tasklist godot -> NONE
```

每次会话**之前**都先查进程与端口，用户端口 **9877** 全程未被占用；所有构建/运行都由 **cmd** 启动
（`cd /d F:\moonbit-hof-rs\godot-mcp\godot && bin\godot.windows.editor.x86_64.mono.console.exe …`
与 `powershell -File tools\run_game_session.ps1 …`）；练习工程一律建在 `projects\_exercises\` 下。
