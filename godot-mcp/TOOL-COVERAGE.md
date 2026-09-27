# TOOL-COVERAGE — 契约工具覆盖台账（all-runs）

> 本文件由 `tool_coverage.py` 自动生成，**随时可重跑刷新**。命令行：
> `python tools/tool_coverage.py`

口径（mode）：**all-runs**；语料：**111 个 run 目录 / 180 个 trace 文件 / 8712 次 `tools/call`**（`ok=false` 655 次、解析失败行 0、sidecar 校验通过 277）

生成时间（UTC）：2026-09-27T06:43:01Z

**「有效调用」的判定**（由 `mcp_trace_ledger.py` 的 verdict 词汇给出，不另立一套）：

- `边界调用` = 该工具 `ok=false` 的调用次数（失败/拒绝即边界证据）。
- `有效调用`：**读类动词**（get/read/search/list/find/analyze/detect/convert/validate/check/assert/execute/evaluate，后三个的生效证据就是它回包的那个值或判词）= `ok=true` 且回包是实质载荷（读类调用不会动像素/字节，回包本身就是证据）；
  **其余动词**（create/edit/set/add/remove/write/build…）= ledger 的 `ok_effect_observed` / `ok_file_effect_observed`，即真的改了画面或文件。带 `assertion_failed` / `created_conflict` / `scenario_errors` 的 ok 调用不计有效。
- `状态`（**TASK-118 A 起按声明的证据通道判定**）：`达标` = 调用≥5 且 **该工具声明的那条通道**上有内容级证据 ≥1 且 边界≥1；`计数达标缺证据` = 调用≥5 但该通道缺证据（或缺边界）；`未达(1-4)` / `未达(0)`；`不可达` 不在本表状态里，见 §4 登记表。（旧口径「像素或文件动了就算有效」仍列在 `coverage.json` 的 `status_legacy` 与 `effective` 里，供对照。）

**「证据档位」的判定**（TASK-112 B；档位由强到弱，一个工具只落一档）：

| 档位 | 判据 | 工具数 |
|---|---|---|
| `pixel_effect` | ok_effect_observed（画面/视口真的变了） | 34 |
| `file_effect` | ok_file_effect_observed（文件真的变了） | 24 |
| `readback` | readback：另一次独立读调用读回佐证（witness_read）或读类工具自己的载荷（own_payload） | 111 |
| `count_only` | 只有计数与边界，没有生效证据 | 3 |
| `no_calls` | 0 次调用 | 5 |

- `readback` 有两种 **互不混同** 的 kind：`witness_read`（写类工具，效果由**另一次独立的读调用**在同一 run 内读回佐证）与 `own_payload`（读类动词，回包本身即测量结果，不存在可等的第二次调用）。
- `witness_read` **不是推断**：配对写在会话 manifest 的 `readback` 数组里，本工具会回到该 run 的 trace 里把见证调用**再找一次**（必须 `ok=true` 且回包是实质载荷），找不到就不给档位（见 §0.1 的 rejected 列表）。
- **内容级复核（TASK-113 C）**：声明可带 `expect`（一个或一组字面量），本工具在**见证调用的回包**里逐字搜它（回包被 trace 截断时读已核验的 sidecar）；搜不到就**不给档位**并记入 rejected，理由逐条写出。所以 `witness_read` 现在证明的是「写进去的值能从引擎自己的回答里读回来」，不再只是「那一次读调用发生过」。
- **不得**把「写工具自己响应里说成功了」当作 readback：那条路径只能落在 `count_only`。

### 0.0 权威证据通道声明（TASK-118 A；声明表：`tools/tool_channels.json`）

每条契约工具**声明一条**权威证据通道；`达标` 只在该通道上以内容级证据判定。声明由 `recovery/work/task118/gen_channels.py` 生成、本工具加载，**覆盖不到契约时本工具直接拒绝运行**（缺一条工具＝那条工具会悄悄退回旧口径）。

| 通道 | 判据 | 声明条数 | 有通道证据 | 通道证据观测数 | 其中达标 | 计数达标缺证据 | 未达(0) |
|---|---|---|---|---|---|---|---|
| `file_effect` | 盘上的文件（ok_file_effect_observed） | 22 | 22 | 484 | 17 | 5 | 0 |
| `pixel_effect` | 渲染出的画面/视口（ok_effect_observed） | 28 | 28 | 238 | 23 | 5 | 0 |
| `editor_state` | 进程内的存在态：另一次独立读调用逐字读回（verified witness_read + expect） | 51 | 45 | 45 | 44 | 2 | 5 |
| `payload` | 查询类：ok=true 且回包是实质载荷（回包即测量结果） | 76 | 74 | 5933 | 68 | 8 | 0 |

- `editor_state` 通道的判据就是 TASK-113 C 的内容级见证：**另一次独立读调用**在同一 run 内、`ok=true`、回包是实质载荷，且其回包里**逐字**包含被写入的值（会话 manifest 的 `readback` 数组 + `expect`）。本工具会回到 trace 里把见证再找一次；写工具自己回包里的成功字样**不是**这条通道的证据。
- 一个工具只在**一条**通道上被判定：声明为 `editor_state` 的工具即使顺手动了像素也不算达标，声明为 `payload` 的工具不会被要求交截图。

**因通道声明而新达标 44 条**（旧口径下它们落在 `计数达标缺证据`，因为它们的效果既不在盘上、也不在这个工程的 2D 视口里）：

| tool | 声明通道 | 累计 | 边界 | 通道证据 | 证据路径 | 判定依据（逐字来自声明表） |
|---|---|---|---|---|---|---|
| `editor_add_scene_instance` | `editor_state` | 30 | 5 | 1 | runs/_exercises/ex_write/c4-task111(6) ; runs/_exercises/ex_write2/c4b-task111(6) | editor_state：内存里活场景树上的实例节点。判定依据：契约改变的状态既不在盘上、也不（在这个工程的视口里）可靠地反映成像素：它是编辑器进程自己的 GUI / 插件 / 文件系统状态，或运行中游戏进程的内存态。这条通道只接受**另一次独立读调用**在自己的回包里**逐字**包含被写入的值的证据（会话 manifest 的 witness_read + expect，本工具会回到 trace 里再核一次）；写工具自己的回包不算。 |
| `editor_play_scene` | `editor_state` | 7 | 2 | 1 | runs/_exercises/ex_editor/h7-task115(7) | editor_state：编辑器的运行条状态（EditorInterface.is_playing_scene()）。判定依据：契约改变的状态既不在盘上、也不（在这个工程的视口里）可靠地反映成像素：它是编辑器进程自己的 GUI / 插件 / 文件系统状态，或运行中游戏进程的内存态。这条通道只接受**另一次独立读调用**在自己的回包里**逐字**包含被写入的值的证据（会话 manifest 的 witness_read + expect，本工具会回到 trace 里再核一次）；写工具自己的回包不算。 |
| `editor_stop_scene` | `editor_state` | 7 | 1 | 1 | runs/_exercises/ex_editor/h7-task115(7) | editor_state：编辑器的运行条状态（EditorInterface.is_playing_scene()）。判定依据：契约改变的状态既不在盘上、也不（在这个工程的视口里）可靠地反映成像素：它是编辑器进程自己的 GUI / 插件 / 文件系统状态，或运行中游戏进程的内存态。这条通道只接受**另一次独立读调用**在自己的回包里**逐字**包含被写入的值的证据（会话 manifest 的 witness_read + expect，本工具会回到 trace 里再核一次）；写工具自己的回包不算。 |
| `editor_rename_node` | `editor_state` | 30 | 7 | 1 | runs/_exercises/ex_write/c4-task111(6) ; runs/_exercises/ex_write2/c4b-task111(6) | editor_state：内存里活场景的节点名。判定依据：契约改变的状态既不在盘上、也不（在这个工程的视口里）可靠地反映成像素：它是编辑器进程自己的 GUI / 插件 / 文件系统状态，或运行中游戏进程的内存态。这条通道只接受**另一次独立读调用**在自己的回包里**逐字**包含被写入的值的证据（会话 manifest 的 witness_read + expect，本工具会回到 trace 里再核一次）；写工具自己的回包不算。 |
| `editor_connect_signal` | `editor_state` | 45 | 7 | 1 | runs/_exercises/ex_grid/c6-task118(6) ; runs/_exercises/ex_write/c4-task111(6) | editor_state：内存里活场景的连接表。判定依据：契约改变的状态既不在盘上、也不（在这个工程的视口里）可靠地反映成像素：它是编辑器进程自己的 GUI / 插件 / 文件系统状态，或运行中游戏进程的内存态。这条通道只接受**另一次独立读调用**在自己的回包里**逐字**包含被写入的值的证据（会话 manifest 的 witness_read + expect，本工具会回到 trace 里再核一次）；写工具自己的回包不算。 |
| `editor_disconnect_signal` | `editor_state` | 6 | 1 | 1 | runs/_exercises/ex_write6/c5-task111(6) | editor_state：内存里活场景的连接表。判定依据：契约改变的状态既不在盘上、也不（在这个工程的视口里）可靠地反映成像素：它是编辑器进程自己的 GUI / 插件 / 文件系统状态，或运行中游戏进程的内存态。这条通道只接受**另一次独立读调用**在自己的回包里**逐字**包含被写入的值的证据（会话 manifest 的 witness_read + expect，本工具会回到 trace 里再核一次）；写工具自己的回包不算。 |
| `editor_set_node_groups` | `editor_state` | 36 | 11 | 1 | runs/_exercises/ex_write/c4-task111(7) ; runs/_exercises/ex_write3/c4c-task111(7) | editor_state：内存里活场景节点的 groups。判定依据：契约改变的状态既不在盘上、也不（在这个工程的视口里）可靠地反映成像素：它是编辑器进程自己的 GUI / 插件 / 文件系统状态，或运行中游戏进程的内存态。这条通道只接受**另一次独立读调用**在自己的回包里**逐字**包含被写入的值的证据（会话 manifest 的 witness_read + expect，本工具会回到 trace 里再核一次）；写工具自己的回包不算。 |
| `editor_set_node_selection` | `editor_state` | 9 | 1 | 1 | runs/_exercises/ex_editor/h7-task115(9) | editor_state：编辑器自己的 EditorSelection。判定依据：契约改变的状态既不在盘上、也不（在这个工程的视口里）可靠地反映成像素：它是编辑器进程自己的 GUI / 插件 / 文件系统状态，或运行中游戏进程的内存态。这条通道只接受**另一次独立读调用**在自己的回包里**逐字**包含被写入的值的证据（会话 manifest 的 witness_read + expect，本工具会回到 trace 里再核一次）；写工具自己的回包不算。 |
| `editor_remove_node_selection` | `editor_state` | 6 | 1 | 1 | runs/_exercises/ex_editor/h7-task115(6) | editor_state：编辑器自己的 EditorSelection。判定依据：契约改变的状态既不在盘上、也不（在这个工程的视口里）可靠地反映成像素：它是编辑器进程自己的 GUI / 插件 / 文件系统状态，或运行中游戏进程的内存态。这条通道只接受**另一次独立读调用**在自己的回包里**逐字**包含被写入的值的证据（会话 manifest 的 witness_read + expect，本工具会回到 trace 里再核一次）；写工具自己的回包不算。 |
| `editor_remove_output_log` | `editor_state` | 6 | 1 | 1 | runs/_exercises/ex_editor/h7-task115(6) | editor_state：编辑器 Output 面板的日志缓冲。判定依据：契约改变的状态既不在盘上、也不（在这个工程的视口里）可靠地反映成像素：它是编辑器进程自己的 GUI / 插件 / 文件系统状态，或运行中游戏进程的内存态。这条通道只接受**另一次独立读调用**在自己的回包里**逐字**包含被写入的值的证据（会话 manifest 的 witness_read + expect，本工具会回到 trace 里再核一次）；写工具自己的回包不算。 |
| `editor_reload_plugin` | `editor_state` | 6 | 1 | 1 | runs/_exercises/ex_editor/h7-task115(6) | editor_state：editor_plugins/enabled 里的 addon 与插件实例。判定依据：契约改变的状态既不在盘上、也不（在这个工程的视口里）可靠地反映成像素：它是编辑器进程自己的 GUI / 插件 / 文件系统状态，或运行中游戏进程的内存态。这条通道只接受**另一次独立读调用**在自己的回包里**逐字**包含被写入的值的证据（会话 manifest 的 witness_read + expect，本工具会回到 trace 里再核一次）；写工具自己的回包不算。 |
| `editor_rescan_project_filesystem` | `editor_state` | 6 | 1 | 1 | runs/_exercises/ex_editor/h7-task115(6) | editor_state：编辑器 FileSystem dock 的扫描结果。判定依据：契约改变的状态既不在盘上、也不（在这个工程的视口里）可靠地反映成像素：它是编辑器进程自己的 GUI / 插件 / 文件系统状态，或运行中游戏进程的内存态。这条通道只接受**另一次独立读调用**在自己的回包里**逐字**包含被写入的值的证据（会话 manifest 的 witness_read + expect，本工具会回到 trace 里再核一次）；写工具自己的回包不算。 |
| `editor_set_viewport_3d_camera` | `editor_state` | 6 | 1 | 1 | runs/_exercises/ex_3d/h1-task111(6) | editor_state：编辑器 3D 视口相机。判定依据：契约改变的状态既不在盘上、也不（在这个工程的视口里）可靠地反映成像素：它是编辑器进程自己的 GUI / 插件 / 文件系统状态，或运行中游戏进程的内存态。这条通道只接受**另一次独立读调用**在自己的回包里**逐字**包含被写入的值的证据（会话 manifest 的 witness_read + expect，本工具会回到 trace 里再核一次）；写工具自己的回包不算。 |
| `running_game_create_input_recording` | `editor_state` | 7 | 1 | 1 | runs/_exercises/ex_rec/h9-task113(7) | editor_state：运行期游戏的输入录制缓冲（由 stop 的回包逐字读回）。判定依据：契约改变的状态既不在盘上、也不（在这个工程的视口里）可靠地反映成像素：它是编辑器进程自己的 GUI / 插件 / 文件系统状态，或运行中游戏进程的内存态。这条通道只接受**另一次独立读调用**在自己的回包里**逐字**包含被写入的值的证据（会话 manifest 的 witness_read + expect，本工具会回到 trace 里再核一次）；写工具自己的回包不算。 |
| `editor_set_node_script` | `editor_state` | 36 | 6 | 1 | runs/_exercises/ex_write/c4-task111(6) ; runs/_exercises/ex_write2/c4b-task111(6) | editor_state：节点挂载的脚本（Node.get_script().resource_path）。判定依据：契约改变的状态既不在盘上、也不（在这个工程的视口里）可靠地反映成像素：它是编辑器进程自己的 GUI / 插件 / 文件系统状态，或运行中游戏进程的内存态。这条通道只接受**另一次独立读调用**在自己的回包里**逐字**包含被写入的值的证据（会话 manifest 的 witness_read + expect，本工具会回到 trace 里再核一次）；写工具自己的回包不算。 |
| `editor_create_animation` | `editor_state` | 23 | 2 | 1 | runs/_exercises/ex_anim/h2-task111(9) ; runs/_exercises/ex_anim2/h2b-task111(9) | editor_state：动画库里的动画（AnimationPlayer）。判定依据：契约改变的状态既不在盘上、也不（在这个工程的视口里）可靠地反映成像素：它是编辑器进程自己的 GUI / 插件 / 文件系统状态，或运行中游戏进程的内存态。这条通道只接受**另一次独立读调用**在自己的回包里**逐字**包含被写入的值的证据（会话 manifest 的 witness_read + expect，本工具会回到 trace 里再核一次）；写工具自己的回包不算。 |
| `editor_add_animation_track` | `editor_state` | 12 | 2 | 1 | runs/_exercises/ex_anim/h2-task111(6) ; runs/_exercises/ex_anim2/h2b-task111(6) | editor_state：动画的轨道表（Animation）。判定依据：契约改变的状态既不在盘上、也不（在这个工程的视口里）可靠地反映成像素：它是编辑器进程自己的 GUI / 插件 / 文件系统状态，或运行中游戏进程的内存态。这条通道只接受**另一次独立读调用**在自己的回包里**逐字**包含被写入的值的证据（会话 manifest 的 witness_read + expect，本工具会回到 trace 里再核一次）；写工具自己的回包不算。 |
| `editor_set_animation_keyframe` | `editor_state` | 12 | 2 | 1 | runs/_exercises/ex_anim/h2-task111(6) ; runs/_exercises/ex_anim2/h2b-task111(6) | editor_state：动画的关键帧（Animation）。判定依据：契约改变的状态既不在盘上、也不（在这个工程的视口里）可靠地反映成像素：它是编辑器进程自己的 GUI / 插件 / 文件系统状态，或运行中游戏进程的内存态。这条通道只接受**另一次独立读调用**在自己的回包里**逐字**包含被写入的值的证据（会话 manifest 的 witness_read + expect，本工具会回到 trace 里再核一次）；写工具自己的回包不算。 |
| `editor_remove_animation` | `editor_state` | 18 | 3 | 1 | runs/_exercises/ex_anim/h2-task111(6) ; runs/_exercises/ex_anim2/h2b-task111(6) | editor_state：动画库里的动画（AnimationPlayer）。判定依据：契约改变的状态既不在盘上、也不（在这个工程的视口里）可靠地反映成像素：它是编辑器进程自己的 GUI / 插件 / 文件系统状态，或运行中游戏进程的内存态。这条通道只接受**另一次独立读调用**在自己的回包里**逐字**包含被写入的值的证据（会话 manifest 的 witness_read + expect，本工具会回到 trace 里再核一次）；写工具自己的回包不算。 |
| `editor_set_physics_layers` | `editor_state` | 24 | 6 | 1 | runs/_exercises/ex_write/c4-task111(6) ; runs/_exercises/ex_write3/c4c-task111(6) | editor_state：节点的 collision_layer/mask。判定依据：契约改变的状态既不在盘上、也不（在这个工程的视口里）可靠地反映成像素：它是编辑器进程自己的 GUI / 插件 / 文件系统状态，或运行中游戏进程的内存态。这条通道只接受**另一次独立读调用**在自己的回包里**逐字**包含被写入的值的证据（会话 manifest 的 witness_read + expect，本工具会回到 trace 里再核一次）；写工具自己的回包不算。 |
| `editor_setup_physics_body` | `editor_state` | 24 | 7 | 1 | runs/_exercises/ex_write/c4-task111(6) ; runs/_exercises/ex_write3/c4c-task111(6) | editor_state：内存里活场景树上的物理体节点。判定依据：契约改变的状态既不在盘上、也不（在这个工程的视口里）可靠地反映成像素：它是编辑器进程自己的 GUI / 插件 / 文件系统状态，或运行中游戏进程的内存态。这条通道只接受**另一次独立读调用**在自己的回包里**逐字**包含被写入的值的证据（会话 manifest 的 witness_read + expect，本工具会回到 trace 里再核一次）；写工具自己的回包不算。 |
| `editor_add_mesh_instance` | `editor_state` | 18 | 3 | 1 | runs/_exercises/ex_3d/h1-task111(6) ; runs/_exercises/ex_3d/h1b-task115(6) | editor_state：内存里活场景树上的 MeshInstance3D。判定依据：契约改变的状态既不在盘上、也不（在这个工程的视口里）可靠地反映成像素：它是编辑器进程自己的 GUI / 插件 / 文件系统状态，或运行中游戏进程的内存态。这条通道只接受**另一次独立读调用**在自己的回包里**逐字**包含被写入的值的证据（会话 manifest 的 witness_read + expect，本工具会回到 trace 里再核一次）；写工具自己的回包不算。 |
| `editor_setup_camera_3d` | `editor_state` | 18 | 3 | 1 | runs/_exercises/ex_3d/h1-task111(6) ; runs/_exercises/ex_3d/h1b-task115(6) | editor_state：内存里活场景树上的 Camera3D。判定依据：契约改变的状态既不在盘上、也不（在这个工程的视口里）可靠地反映成像素：它是编辑器进程自己的 GUI / 插件 / 文件系统状态，或运行中游戏进程的内存态。这条通道只接受**另一次独立读调用**在自己的回包里**逐字**包含被写入的值的证据（会话 manifest 的 witness_read + expect，本工具会回到 trace 里再核一次）；写工具自己的回包不算。 |
| `editor_setup_lighting` | `editor_state` | 18 | 3 | 1 | runs/_exercises/ex_3d/h1-task111(6) ; runs/_exercises/ex_3d/h1b-task115(6) | editor_state：内存里活场景树上的 Light3D。判定依据：契约改变的状态既不在盘上、也不（在这个工程的视口里）可靠地反映成像素：它是编辑器进程自己的 GUI / 插件 / 文件系统状态，或运行中游戏进程的内存态。这条通道只接受**另一次独立读调用**在自己的回包里**逐字**包含被写入的值的证据（会话 manifest 的 witness_read + expect，本工具会回到 trace 里再核一次）；写工具自己的回包不算。 |
| `editor_set_material_3d` | `editor_state` | 18 | 5 | 1 | runs/_exercises/ex_3d/h1-task111(6) ; runs/_exercises/ex_3d/h1b-task115(6) | editor_state：节点的 surface override material。判定依据：契约改变的状态既不在盘上、也不（在这个工程的视口里）可靠地反映成像素：它是编辑器进程自己的 GUI / 插件 / 文件系统状态，或运行中游戏进程的内存态。这条通道只接受**另一次独立读调用**在自己的回包里**逐字**包含被写入的值的证据（会话 manifest 的 witness_read + expect，本工具会回到 trace 里再核一次）；写工具自己的回包不算。 |
| `editor_setup_world_environment` | `editor_state` | 18 | 3 | 1 | runs/_exercises/ex_3d/h1-task111(6) ; runs/_exercises/ex_3d/h1b-task115(6) | editor_state：内存里活场景树上的 WorldEnvironment。判定依据：契约改变的状态既不在盘上、也不（在这个工程的视口里）可靠地反映成像素：它是编辑器进程自己的 GUI / 插件 / 文件系统状态，或运行中游戏进程的内存态。这条通道只接受**另一次独立读调用**在自己的回包里**逐字**包含被写入的值的证据（会话 manifest 的 witness_read + expect，本工具会回到 trace 里再核一次）；写工具自己的回包不算。 |
| `editor_add_gridmap` | `editor_state` | 12 | 2 | 1 | runs/_exercises/ex_grid/c6-task118(6) ; runs/_exercises/ex_grid/h3-task111(6) | editor_state：内存里活场景树上的 GridMap 节点。判定依据：契约改变的状态既不在盘上、也不（在这个工程的视口里）可靠地反映成像素：它是编辑器进程自己的 GUI / 插件 / 文件系统状态，或运行中游戏进程的内存态。这条通道只接受**另一次独立读调用**在自己的回包里**逐字**包含被写入的值的证据（会话 manifest 的 witness_read + expect，本工具会回到 trace 里再核一次）；写工具自己的回包不算。 |
| `editor_add_audio_player` | `editor_state` | 6 | 1 | 1 | runs/_exercises/ex_audio/h5-task113(6) | editor_state：内存里活场景树上的音频节点。判定依据：契约改变的状态既不在盘上、也不（在这个工程的视口里）可靠地反映成像素：它是编辑器进程自己的 GUI / 插件 / 文件系统状态，或运行中游戏进程的内存态。这条通道只接受**另一次独立读调用**在自己的回包里**逐字**包含被写入的值的证据（会话 manifest 的 witness_read + expect，本工具会回到 trace 里再核一次）；写工具自己的回包不算。 |
| `editor_add_audio_bus` | `editor_state` | 7 | 2 | 1 | runs/_exercises/ex_audio/h5-task113(7) | editor_state：内存里的音频总线布局（AudioServer）。判定依据：契约改变的状态既不在盘上、也不（在这个工程的视口里）可靠地反映成像素：它是编辑器进程自己的 GUI / 插件 / 文件系统状态，或运行中游戏进程的内存态。这条通道只接受**另一次独立读调用**在自己的回包里**逐字**包含被写入的值的证据（会话 manifest 的 witness_read + expect，本工具会回到 trace 里再核一次）；写工具自己的回包不算。 |
| `editor_set_audio_bus_property` | `editor_state` | 8 | 3 | 1 | runs/_exercises/ex_audio/h5-task113(8) | editor_state：内存里的音频总线布局（AudioServer）。判定依据：契约改变的状态既不在盘上、也不（在这个工程的视口里）可靠地反映成像素：它是编辑器进程自己的 GUI / 插件 / 文件系统状态，或运行中游戏进程的内存态。这条通道只接受**另一次独立读调用**在自己的回包里**逐字**包含被写入的值的证据（会话 manifest 的 witness_read + expect，本工具会回到 trace 里再核一次）；写工具自己的回包不算。 |
| `editor_add_audio_bus_effect` | `editor_state` | 7 | 2 | 1 | runs/_exercises/ex_audio/h5-task113(7) | editor_state：内存里的音频总线效果链（AudioServer）。判定依据：契约改变的状态既不在盘上、也不（在这个工程的视口里）可靠地反映成像素：它是编辑器进程自己的 GUI / 插件 / 文件系统状态，或运行中游戏进程的内存态。这条通道只接受**另一次独立读调用**在自己的回包里**逐字**包含被写入的值的证据（会话 manifest 的 witness_read + expect，本工具会回到 trace 里再核一次）；写工具自己的回包不算。 |
| `editor_set_control_theme` | `editor_state` | 30 | 6 | 1 | runs/_exercises/ex_write/c4-task111(6) ; runs/_exercises/ex_write3/c4c-task111(6) | editor_state：Control 节点挂载的 Theme。判定依据：契约改变的状态既不在盘上、也不（在这个工程的视口里）可靠地反映成像素：它是编辑器进程自己的 GUI / 插件 / 文件系统状态，或运行中游戏进程的内存态。这条通道只接受**另一次独立读调用**在自己的回包里**逐字**包含被写入的值的证据（会话 manifest 的 witness_read + expect，本工具会回到 trace 里再核一次）；写工具自己的回包不算。 |
| `editor_create_animation_tree` | `editor_state` | 12 | 2 | 1 | runs/_exercises/ex_anim/h2-task111(6) ; runs/_exercises/ex_anim2/h2b-task111(6) | editor_state：内存里活场景树上的 AnimationTree。判定依据：契约改变的状态既不在盘上、也不（在这个工程的视口里）可靠地反映成像素：它是编辑器进程自己的 GUI / 插件 / 文件系统状态，或运行中游戏进程的内存态。这条通道只接受**另一次独立读调用**在自己的回包里**逐字**包含被写入的值的证据（会话 manifest 的 witness_read + expect，本工具会回到 trace 里再核一次）；写工具自己的回包不算。 |
| `editor_add_state_machine_state` | `editor_state` | 18 | 2 | 1 | runs/_exercises/ex_anim2/h2b-task111(12) ; runs/_exercises/ex_anim/h2-task111(6) | editor_state：AnimationTree 状态机里的状态。判定依据：契约改变的状态既不在盘上、也不（在这个工程的视口里）可靠地反映成像素：它是编辑器进程自己的 GUI / 插件 / 文件系统状态，或运行中游戏进程的内存态。这条通道只接受**另一次独立读调用**在自己的回包里**逐字**包含被写入的值的证据（会话 manifest 的 witness_read + expect，本工具会回到 trace 里再核一次）；写工具自己的回包不算。 |
| `editor_remove_state_machine_state` | `editor_state` | 12 | 7 | 1 | runs/_exercises/ex_anim/h2-task111(6) ; runs/_exercises/ex_anim2/h2b-task111(6) | editor_state：AnimationTree 状态机里的状态。判定依据：契约改变的状态既不在盘上、也不（在这个工程的视口里）可靠地反映成像素：它是编辑器进程自己的 GUI / 插件 / 文件系统状态，或运行中游戏进程的内存态。这条通道只接受**另一次独立读调用**在自己的回包里**逐字**包含被写入的值的证据（会话 manifest 的 witness_read + expect，本工具会回到 trace 里再核一次）；写工具自己的回包不算。 |
| `editor_add_state_machine_transition` | `editor_state` | 22 | 2 | 1 | runs/_exercises/ex_anim/h2-task111(11) ; runs/_exercises/ex_anim2/h2b-task111(11) | editor_state：AnimationTree 状态机里的迁移。判定依据：契约改变的状态既不在盘上、也不（在这个工程的视口里）可靠地反映成像素：它是编辑器进程自己的 GUI / 插件 / 文件系统状态，或运行中游戏进程的内存态。这条通道只接受**另一次独立读调用**在自己的回包里**逐字**包含被写入的值的证据（会话 manifest 的 witness_read + expect，本工具会回到 trace 里再核一次）；写工具自己的回包不算。 |
| `editor_remove_state_machine_transition` | `editor_state` | 12 | 2 | 1 | runs/_exercises/ex_anim/h2-task111(6) ; runs/_exercises/ex_anim2/h2b-task111(6) | editor_state：AnimationTree 状态机里的迁移。判定依据：契约改变的状态既不在盘上、也不（在这个工程的视口里）可靠地反映成像素：它是编辑器进程自己的 GUI / 插件 / 文件系统状态，或运行中游戏进程的内存态。这条通道只接受**另一次独立读调用**在自己的回包里**逐字**包含被写入的值的证据（会话 manifest 的 witness_read + expect，本工具会回到 trace 里再核一次）；写工具自己的回包不算。 |
| `editor_set_blend_tree_node` | `editor_state` | 12 | 7 | 1 | runs/_exercises/ex_anim/h2-task111(6) ; runs/_exercises/ex_anim2/h2b-task111(6) | editor_state：AnimationTree 的混合树节点。判定依据：契约改变的状态既不在盘上、也不（在这个工程的视口里）可靠地反映成像素：它是编辑器进程自己的 GUI / 插件 / 文件系统状态，或运行中游戏进程的内存态。这条通道只接受**另一次独立读调用**在自己的回包里**逐字**包含被写入的值的证据（会话 manifest 的 witness_read + expect，本工具会回到 trace 里再核一次）；写工具自己的回包不算。 |
| `editor_set_animation_tree_parameter` | `editor_state` | 12 | 4 | 1 | runs/_exercises/ex_anim/h2-task111(6) ; runs/_exercises/ex_anim2/h2b-task111(6) | editor_state：AnimationTree 的参数表。判定依据：契约改变的状态既不在盘上、也不（在这个工程的视口里）可靠地反映成像素：它是编辑器进程自己的 GUI / 插件 / 文件系统状态，或运行中游戏进程的内存态。这条通道只接受**另一次独立读调用**在自己的回包里**逐字**包含被写入的值的证据（会话 manifest 的 witness_read + expect，本工具会回到 trace 里再核一次）；写工具自己的回包不算。 |
| `editor_setup_navigation_region` | `editor_state` | 6 | 1 | 1 | runs/_exercises/ex_nav/h4-task113(6) | editor_state：内存里活场景树上的 NavigationRegion。判定依据：契约改变的状态既不在盘上、也不（在这个工程的视口里）可靠地反映成像素：它是编辑器进程自己的 GUI / 插件 / 文件系统状态，或运行中游戏进程的内存态。这条通道只接受**另一次独立读调用**在自己的回包里**逐字**包含被写入的值的证据（会话 manifest 的 witness_read + expect，本工具会回到 trace 里再核一次）；写工具自己的回包不算。 |
| `editor_setup_navigation_agent` | `editor_state` | 6 | 1 | 1 | runs/_exercises/ex_nav/h4-task113(6) | editor_state：内存里活场景树上的 NavigationAgent。判定依据：契约改变的状态既不在盘上、也不（在这个工程的视口里）可靠地反映成像素：它是编辑器进程自己的 GUI / 插件 / 文件系统状态，或运行中游戏进程的内存态。这条通道只接受**另一次独立读调用**在自己的回包里**逐字**包含被写入的值的证据（会话 manifest 的 witness_read + expect，本工具会回到 trace 里再核一次）；写工具自己的回包不算。 |
| `editor_set_navigation_layers` | `editor_state` | 7 | 2 | 1 | runs/_exercises/ex_nav/h4-task113(7) | editor_state：导航层掩码。判定依据：契约改变的状态既不在盘上、也不（在这个工程的视口里）可靠地反映成像素：它是编辑器进程自己的 GUI / 插件 / 文件系统状态，或运行中游戏进程的内存态。这条通道只接受**另一次独立读调用**在自己的回包里**逐字**包含被写入的值的证据（会话 manifest 的 witness_read + expect，本工具会回到 trace 里再核一次）；写工具自己的回包不算。 |
| `editor_create_particles` | `editor_state` | 8 | 3 | 1 | runs/_exercises/ex_particles/h6-task113(8) | editor_state：内存里活场景树上的粒子系统。判定依据：契约改变的状态既不在盘上、也不（在这个工程的视口里）可靠地反映成像素：它是编辑器进程自己的 GUI / 插件 / 文件系统状态，或运行中游戏进程的内存态。这条通道只接受**另一次独立读调用**在自己的回包里**逐字**包含被写入的值的证据（会话 manifest 的 witness_read + expect，本工具会回到 trace 里再核一次）；写工具自己的回包不算。 |
| `editor_set_node_script_batch` | `editor_state` | 56 | 1 | 1 | runs/_exercises/ex_grid/c6-task118(6) ; runs/breakout/breakout-clean-task097(2) | editor_state：一批节点挂载的脚本（Node.get_script().resource_path）。判定依据：契约改变的状态既不在盘上、也不（在这个工程的视口里）可靠地反映成像素：它是编辑器进程自己的 GUI / 插件 / 文件系统状态，或运行中游戏进程的内存态。这条通道只接受**另一次独立读调用**在自己的回包里**逐字**包含被写入的值的证据（会话 manifest 的 witness_read + expect，本工具会回到 trace 里再核一次）；写工具自己的回包不算。 |

- **被新口径降级的工具：0 条**（旧口径达标、新口径不达标——这一栏必须为空，不为空说明有工具在它自己声明的通道上根本拿不出证据，是需要解释的缺陷）。**0 条**

**声明通道上仍不达标 25 条**（逐条给原因）：

| tool | 声明通道 | 累计 | 边界 | 通道证据 | 原因 |
|---|---|---|---|---|---|
| `editor_open_scene` | `pixel_effect` | 86 | 0 | 9 | channel-evidence=9 but no boundary call |
| `editor_save_scene` | `file_effect` | 123 | 0 | 77 | channel-evidence=77 but no boundary call |
| `editor_delete_node` | `pixel_effect` | 65 | 0 | 5 | channel-evidence=5 but no boundary call |
| `editor_set_node_property` | `pixel_effect` | 41 | 0 | 12 | channel-evidence=12 but no boundary call |
| `editor_get_errors` | `payload` | 50 | 0 | 50 | channel-evidence=50 but no boundary call |
| `editor_capture_screenshot` | `file_effect` | 25 | 0 | 15 | channel-evidence=15 but no boundary call |
| `running_game_capture_screenshot` | `payload` | 298 | 0 | 298 | channel-evidence=298 but no boundary call |
| `editor_set_auto_dismiss_dialogs` | `editor_state` | 7 | 7 | 0 | channel-evidence=0 on the declared channel `editor_state` |
| `running_game_get_scene_tree` | `payload` | 123 | 0 | 123 | channel-evidence=123 but no boundary call |
| `running_game_get_node_property_samples` | `payload` | 122 | 0 | 122 | channel-evidence=122 but no boundary call |
| `running_game_stop_input_recording` | `editor_state` | 7 | 0 | 1 | channel-evidence=1 but no boundary call |
| `project_edit_script` | `file_effect` | 60 | 0 | 52 | channel-evidence=52 but no boundary call |
| `editor_simulate_key` | `editor_state` | 0 | 0 | 0 | calls<5 |
| `editor_simulate_mouse_click` | `editor_state` | 0 | 0 | 0 | calls<5 |
| `editor_simulate_mouse_move` | `editor_state` | 0 | 0 | 0 | calls<5 |
| `editor_simulate_input_action` | `editor_state` | 0 | 0 | 0 | calls<5 |
| `editor_add_input_action` | `file_effect` | 189 | 0 | 122 | channel-evidence=122 but no boundary call |
| `editor_simulate_input_sequence` | `editor_state` | 0 | 0 | 0 | calls<5 |
| `running_game_run_test_scenario` | `pixel_effect` | 185 | 0 | 1 | channel-evidence=1 but no boundary call |
| `running_game_assert_screen_text` | `payload` | 80 | 0 | 65 | channel-evidence=65 but no boundary call |
| `running_game_run_stress_test` | `pixel_effect` | 27 | 0 | 5 | channel-evidence=5 but no boundary call |
| `project_get_android_preset_info` | `payload` | 6 | 6 | 0 | channel-evidence=0 on the declared channel `payload` |
| `os_deploy_to_android_device` | `payload` | 6 | 6 | 0 | channel-evidence=0 on the declared channel `payload` |
| `project_build_csharp` | `file_effect` | 67 | 0 | 63 | channel-evidence=63 but no boundary call |
| `project_validate_scripts` | `payload` | 84 | 0 | 80 | channel-evidence=80 but no boundary call |

**逐条工具的通道声明与判定依据**（177 条；`subject` 是这条工具作用的对象，`basis` 是为什么它是这条通道而不是另一条）：

| # | tool | scope | verb | 声明通道 | subject | basis |
|---|---|---|---|---|---|---|
| 1 | `project_get_info` | both | get | `payload` | 项目元信息 | payload：项目元信息。判定依据：契约是查询：回包本身就是测量结果，不存在「另一次调用」可等（TASK-111 的 READ_VERBS 规则）。内容级证据 = ok=true 且回包是实质载荷。 |
| 2 | `project_get_filesystem_tree` | both | get | `payload` | 项目文件树 | payload：项目文件树。判定依据：契约是查询：回包本身就是测量结果，不存在「另一次调用」可等（TASK-111 的 READ_VERBS 规则）。内容级证据 = ok=true 且回包是实质载荷。 |
| 3 | `project_search_file_names` | both | search | `payload` | 按文件名搜索的结果 | payload：按文件名搜索的结果。判定依据：契约是查询：回包本身就是测量结果，不存在「另一次调用」可等（TASK-111 的 READ_VERBS 规则）。内容级证据 = ok=true 且回包是实质载荷。 |
| 4 | `project_search_file_contents` | both | search | `payload` | 按内容搜索的结果 | payload：按内容搜索的结果。判定依据：契约是查询：回包本身就是测量结果，不存在「另一次调用」可等（TASK-111 的 READ_VERBS 规则）。内容级证据 = ok=true 且回包是实质载荷。 |
| 5 | `project_get_settings` | both | get | `payload` | ProjectSettings 的当前值 | payload：ProjectSettings 的当前值。判定依据：契约是查询：回包本身就是测量结果，不存在「另一次调用」可等（TASK-111 的 READ_VERBS 规则）。内容级证据 = ok=true 且回包是实质载荷。 |
| 6 | `project_set_setting` | both | set | `file_effect` | project.godot 的设置项 | file_effect：project.godot 的设置项。判定依据：契约写的是盘上的产物：它落盘之后可以被任何一次 project_read_* / project_get_filesystem_tree 重新读到，所以权威证据是文件本身，不是回包里的成功字样，也不是编辑器画面。 |
| 7 | `project_convert_uid_to_path` | both | convert | `payload` | uid→path 的换算结果 | payload：uid→path 的换算结果。判定依据：契约是查询：回包本身就是测量结果，不存在「另一次调用」可等（TASK-111 的 READ_VERBS 规则）。内容级证据 = ok=true 且回包是实质载荷。 |
| 8 | `project_convert_path_to_uid` | both | convert | `payload` | path→uid 的换算结果 | payload：path→uid 的换算结果。判定依据：契约是查询：回包本身就是测量结果，不存在「另一次调用」可等（TASK-111 的 READ_VERBS 规则）。内容级证据 = ok=true 且回包是实质载荷。 |
| 9 | `editor_get_scene_tree` | editor | get | `payload` | 编辑场景的树 | payload：编辑场景的树。判定依据：契约是查询：回包本身就是测量结果，不存在「另一次调用」可等（TASK-111 的 READ_VERBS 规则）。内容级证据 = ok=true 且回包是实质载荷。 |
| 10 | `project_read_scene_file_content` | both | read | `payload` | 场景文件的文本 | payload：场景文件的文本。判定依据：契约是查询：回包本身就是测量结果，不存在「另一次调用」可等（TASK-111 的 READ_VERBS 规则）。内容级证据 = ok=true 且回包是实质载荷。 |
| 11 | `editor_open_scene` | editor | open | `pixel_effect` | 编辑器视口里换了一整个场景 | pixel_effect：编辑器视口里换了一整个场景。判定依据：契约改变的是被渲染的画面：编辑器视口或运行中游戏的帧，ledger 的 ok_effect_observed（截图前后真的变了像素）就是这条通道的内容级证据，回包里的成功字样不算。 |
| 12 | `project_delete_scene_file` | both | delete | `file_effect` | 被删掉的 .tscn | file_effect：被删掉的 .tscn。判定依据：契约写的是盘上的产物：它落盘之后可以被任何一次 project_read_* / project_get_filesystem_tree 重新读到，所以权威证据是文件本身，不是回包里的成功字样，也不是编辑器画面。 |
| 13 | `editor_add_scene_instance` | editor | add | `editor_state` | 内存里活场景树上的实例节点 | editor_state：内存里活场景树上的实例节点。判定依据：契约改变的状态既不在盘上、也不（在这个工程的视口里）可靠地反映成像素：它是编辑器进程自己的 GUI / 插件 / 文件系统状态，或运行中游戏进程的内存态。这条通道只接受**另一次独立读调用**在自己的回包里**逐字**包含被写入的值的证据（会话 manifest 的 witness_read + expect，本工具会回到 trace 里再核一次）；写工具自己的回包不算。 |
| 14 | `project_get_scene_exports` | both | get | `payload` | 场景的导出清单 | payload：场景的导出清单。判定依据：契约是查询：回包本身就是测量结果，不存在「另一次调用」可等（TASK-111 的 READ_VERBS 规则）。内容级证据 = ok=true 且回包是实质载荷。 |
| 15 | `editor_play_scene` | editor | play | `editor_state` | 编辑器的运行条状态（EditorInterface.is_playing_scene()） | editor_state：编辑器的运行条状态（EditorInterface.is_playing_scene()）。判定依据：契约改变的状态既不在盘上、也不（在这个工程的视口里）可靠地反映成像素：它是编辑器进程自己的 GUI / 插件 / 文件系统状态，或运行中游戏进程的内存态。这条通道只接受**另一次独立读调用**在自己的回包里**逐字**包含被写入的值的证据（会话 manifest 的 witness_read + expect，本工具会回到 trace 里再核一次）；写工具自己的回包不算。 |
| 16 | `editor_stop_scene` | editor | stop | `editor_state` | 编辑器的运行条状态（EditorInterface.is_playing_scene()） | editor_state：编辑器的运行条状态（EditorInterface.is_playing_scene()）。判定依据：契约改变的状态既不在盘上、也不（在这个工程的视口里）可靠地反映成像素：它是编辑器进程自己的 GUI / 插件 / 文件系统状态，或运行中游戏进程的内存态。这条通道只接受**另一次独立读调用**在自己的回包里**逐字**包含被写入的值的证据（会话 manifest 的 witness_read + expect，本工具会回到 trace 里再核一次）；写工具自己的回包不算。 |
| 17 | `editor_save_scene` | editor | save | `file_effect` | 被保存的 .tscn | file_effect：被保存的 .tscn。判定依据：契约写的是盘上的产物：它落盘之后可以被任何一次 project_read_* / project_get_filesystem_tree 重新读到，所以权威证据是文件本身，不是回包里的成功字样，也不是编辑器画面。 |
| 18 | `project_create_scene_file` | both | create | `file_effect` | 新建的 .tscn | file_effect：新建的 .tscn。判定依据：契约写的是盘上的产物：它落盘之后可以被任何一次 project_read_* / project_get_filesystem_tree 重新读到，所以权威证据是文件本身，不是回包里的成功字样，也不是编辑器画面。 |
| 19 | `editor_add_node` | editor | add | `pixel_effect` | 编辑场景里新增的节点（视口可见） | pixel_effect：编辑场景里新增的节点（视口可见）。判定依据：契约改变的是被渲染的画面：编辑器视口或运行中游戏的帧，ledger 的 ok_effect_observed（截图前后真的变了像素）就是这条通道的内容级证据，回包里的成功字样不算。 |
| 20 | `editor_delete_node` | editor | delete | `pixel_effect` | 编辑场景里被删的节点（视口可见） | pixel_effect：编辑场景里被删的节点（视口可见）。判定依据：契约改变的是被渲染的画面：编辑器视口或运行中游戏的帧，ledger 的 ok_effect_observed（截图前后真的变了像素）就是这条通道的内容级证据，回包里的成功字样不算。 |
| 21 | `editor_rename_node` | editor | rename | `editor_state` | 内存里活场景的节点名 | editor_state：内存里活场景的节点名。判定依据：契约改变的状态既不在盘上、也不（在这个工程的视口里）可靠地反映成像素：它是编辑器进程自己的 GUI / 插件 / 文件系统状态，或运行中游戏进程的内存态。这条通道只接受**另一次独立读调用**在自己的回包里**逐字**包含被写入的值的证据（会话 manifest 的 witness_read + expect，本工具会回到 trace 里再核一次）；写工具自己的回包不算。 |
| 22 | `editor_set_node_property` | editor | set | `pixel_effect` | 节点属性（视口可见的那些） | pixel_effect：节点属性（视口可见的那些）。判定依据：契约改变的是被渲染的画面：编辑器视口或运行中游戏的帧，ledger 的 ok_effect_observed（截图前后真的变了像素）就是这条通道的内容级证据，回包里的成功字样不算。 |
| 23 | `editor_get_node_properties` | editor | get | `payload` | 节点属性值 | payload：节点属性值。判定依据：契约是查询：回包本身就是测量结果，不存在「另一次调用」可等（TASK-111 的 READ_VERBS 规则）。内容级证据 = ok=true 且回包是实质载荷。 |
| 24 | `editor_duplicate_node` | editor | duplicate | `pixel_effect` | 复制出来的节点（视口可见） | pixel_effect：复制出来的节点（视口可见）。判定依据：契约改变的是被渲染的画面：编辑器视口或运行中游戏的帧，ledger 的 ok_effect_observed（截图前后真的变了像素）就是这条通道的内容级证据，回包里的成功字样不算。 |
| 25 | `editor_connect_signal` | editor | connect | `editor_state` | 内存里活场景的连接表 | editor_state：内存里活场景的连接表。判定依据：契约改变的状态既不在盘上、也不（在这个工程的视口里）可靠地反映成像素：它是编辑器进程自己的 GUI / 插件 / 文件系统状态，或运行中游戏进程的内存态。这条通道只接受**另一次独立读调用**在自己的回包里**逐字**包含被写入的值的证据（会话 manifest 的 witness_read + expect，本工具会回到 trace 里再核一次）；写工具自己的回包不算。 |
| 26 | `editor_disconnect_signal` | editor | disconnect | `editor_state` | 内存里活场景的连接表 | editor_state：内存里活场景的连接表。判定依据：契约改变的状态既不在盘上、也不（在这个工程的视口里）可靠地反映成像素：它是编辑器进程自己的 GUI / 插件 / 文件系统状态，或运行中游戏进程的内存态。这条通道只接受**另一次独立读调用**在自己的回包里**逐字**包含被写入的值的证据（会话 manifest 的 witness_read + expect，本工具会回到 trace 里再核一次）；写工具自己的回包不算。 |
| 27 | `editor_reparent_node` | editor | reparent | `pixel_effect` | 节点的父级改变（视口位置随之变） | pixel_effect：节点的父级改变（视口位置随之变）。判定依据：契约改变的是被渲染的画面：编辑器视口或运行中游戏的帧，ledger 的 ok_effect_observed（截图前后真的变了像素）就是这条通道的内容级证据，回包里的成功字样不算。 |
| 28 | `editor_add_resource_to_node_property` | editor | add | `pixel_effect` | 挂到节点属性上的资源（视口可见） | pixel_effect：挂到节点属性上的资源（视口可见）。判定依据：契约改变的是被渲染的画面：编辑器视口或运行中游戏的帧，ledger 的 ok_effect_observed（截图前后真的变了像素）就是这条通道的内容级证据，回包里的成功字样不算。 |
| 29 | `editor_set_anchor_preset` | editor | set | `pixel_effect` | Control 的锚点（视口布局随之变） | pixel_effect：Control 的锚点（视口布局随之变）。判定依据：契约改变的是被渲染的画面：编辑器视口或运行中游戏的帧，ledger 的 ok_effect_observed（截图前后真的变了像素）就是这条通道的内容级证据，回包里的成功字样不算。 |
| 30 | `editor_get_node_groups` | editor | get | `payload` | 节点的 groups 列表 | payload：节点的 groups 列表。判定依据：契约是查询：回包本身就是测量结果，不存在「另一次调用」可等（TASK-111 的 READ_VERBS 规则）。内容级证据 = ok=true 且回包是实质载荷。 |
| 31 | `editor_set_node_groups` | editor | set | `editor_state` | 内存里活场景节点的 groups | editor_state：内存里活场景节点的 groups。判定依据：契约改变的状态既不在盘上、也不（在这个工程的视口里）可靠地反映成像素：它是编辑器进程自己的 GUI / 插件 / 文件系统状态，或运行中游戏进程的内存态。这条通道只接受**另一次独立读调用**在自己的回包里**逐字**包含被写入的值的证据（会话 manifest 的 witness_read + expect，本工具会回到 trace 里再核一次）；写工具自己的回包不算。 |
| 32 | `editor_find_nodes_in_group` | editor | find | `payload` | 按组检索的结果 | payload：按组检索的结果。判定依据：契约是查询：回包本身就是测量结果，不存在「另一次调用」可等（TASK-111 的 READ_VERBS 规则）。内容级证据 = ok=true 且回包是实质载荷。 |
| 33 | `editor_get_selection` | editor | get | `payload` | 编辑器自己的 EditorSelection | payload：编辑器自己的 EditorSelection。判定依据：契约是查询：回包本身就是测量结果，不存在「另一次调用」可等（TASK-111 的 READ_VERBS 规则）。内容级证据 = ok=true 且回包是实质载荷。 |
| 34 | `editor_set_node_selection` | editor | set | `editor_state` | 编辑器自己的 EditorSelection | editor_state：编辑器自己的 EditorSelection。判定依据：契约改变的状态既不在盘上、也不（在这个工程的视口里）可靠地反映成像素：它是编辑器进程自己的 GUI / 插件 / 文件系统状态，或运行中游戏进程的内存态。这条通道只接受**另一次独立读调用**在自己的回包里**逐字**包含被写入的值的证据（会话 manifest 的 witness_read + expect，本工具会回到 trace 里再核一次）；写工具自己的回包不算。 |
| 35 | `editor_remove_node_selection` | editor | remove | `editor_state` | 编辑器自己的 EditorSelection | editor_state：编辑器自己的 EditorSelection。判定依据：契约改变的状态既不在盘上、也不（在这个工程的视口里）可靠地反映成像素：它是编辑器进程自己的 GUI / 插件 / 文件系统状态，或运行中游戏进程的内存态。这条通道只接受**另一次独立读调用**在自己的回包里**逐字**包含被写入的值的证据（会话 manifest 的 witness_read + expect，本工具会回到 trace 里再核一次）；写工具自己的回包不算。 |
| 36 | `editor_execute_gdscript` | editor | execute | `payload` | 被求值的表达式返回值 | payload：被求值的表达式返回值。判定依据：契约是查询：回包本身就是测量结果，不存在「另一次调用」可等（TASK-111 的 READ_VERBS 规则）。内容级证据 = ok=true 且回包是实质载荷。 |
| 37 | `editor_get_errors` | editor | get | `payload` | 错误列表 | payload：错误列表。判定依据：契约是查询：回包本身就是测量结果，不存在「另一次调用」可等（TASK-111 的 READ_VERBS 规则）。内容级证据 = ok=true 且回包是实质载荷。 |
| 38 | `editor_get_output_log` | editor | get | `payload` | 编辑器 Output 面板的日志行 | payload：编辑器 Output 面板的日志行。判定依据：契约是查询：回包本身就是测量结果，不存在「另一次调用」可等（TASK-111 的 READ_VERBS 规则）。内容级证据 = ok=true 且回包是实质载荷。 |
| 39 | `editor_capture_screenshot` | editor | capture | `file_effect` | 落盘的 PNG 截图 | file_effect：落盘的 PNG 截图。判定依据：契约写的是盘上的产物：它落盘之后可以被任何一次 project_read_* / project_get_filesystem_tree 重新读到，所以权威证据是文件本身，不是回包里的成功字样，也不是编辑器画面。 |
| 40 | `running_game_capture_screenshot` | game | capture | `payload` | 帧截图载荷（回包里的 base64 图） | payload：帧截图载荷（回包里的 base64 图）。判定依据：契约是查询：回包本身就是测量结果，不存在「另一次调用」可等（TASK-111 的 READ_VERBS 规则）。内容级证据 = ok=true 且回包是实质载荷。 |
| 41 | `editor_remove_output_log` | editor | remove | `editor_state` | 编辑器 Output 面板的日志缓冲 | editor_state：编辑器 Output 面板的日志缓冲。判定依据：契约改变的状态既不在盘上、也不（在这个工程的视口里）可靠地反映成像素：它是编辑器进程自己的 GUI / 插件 / 文件系统状态，或运行中游戏进程的内存态。这条通道只接受**另一次独立读调用**在自己的回包里**逐字**包含被写入的值的证据（会话 manifest 的 witness_read + expect，本工具会回到 trace 里再核一次）；写工具自己的回包不算。 |
| 42 | `editor_reload_plugin` | editor | reload | `editor_state` | editor_plugins/enabled 里的 addon 与插件实例 | editor_state：editor_plugins/enabled 里的 addon 与插件实例。判定依据：契约改变的状态既不在盘上、也不（在这个工程的视口里）可靠地反映成像素：它是编辑器进程自己的 GUI / 插件 / 文件系统状态，或运行中游戏进程的内存态。这条通道只接受**另一次独立读调用**在自己的回包里**逐字**包含被写入的值的证据（会话 manifest 的 witness_read + expect，本工具会回到 trace 里再核一次）；写工具自己的回包不算。 |
| 43 | `editor_rescan_project_filesystem` | editor | rescan | `editor_state` | 编辑器 FileSystem dock 的扫描结果 | editor_state：编辑器 FileSystem dock 的扫描结果。判定依据：契约改变的状态既不在盘上、也不（在这个工程的视口里）可靠地反映成像素：它是编辑器进程自己的 GUI / 插件 / 文件系统状态，或运行中游戏进程的内存态。这条通道只接受**另一次独立读调用**在自己的回包里**逐字**包含被写入的值的证据（会话 manifest 的 witness_read + expect，本工具会回到 trace 里再核一次）；写工具自己的回包不算。 |
| 44 | `editor_get_node_signals` | editor | get | `payload` | 节点的信号表 | payload：节点的信号表。判定依据：契约是查询：回包本身就是测量结果，不存在「另一次调用」可等（TASK-111 的 READ_VERBS 规则）。内容级证据 = ok=true 且回包是实质载荷。 |
| 45 | `editor_analyze_screenshot_diff` | editor | analyze | `payload` | 两图差异的数值判词 | payload：两图差异的数值判词。判定依据：契约是查询：回包本身就是测量结果，不存在「另一次调用」可等（TASK-111 的 READ_VERBS 规则）。内容级证据 = ok=true 且回包是实质载荷。 |
| 46 | `editor_set_auto_dismiss_dialogs` | editor | set | `editor_state` | 编辑器对话框自动关闭开关（本引擎没有这个进程级开关，provider 恒为 -32000） | editor_state：编辑器对话框自动关闭开关（本引擎没有这个进程级开关，provider 恒为 -32000）。判定依据：契约改变的状态既不在盘上、也不（在这个工程的视口里）可靠地反映成像素：它是编辑器进程自己的 GUI / 插件 / 文件系统状态，或运行中游戏进程的内存态。这条通道只接受**另一次独立读调用**在自己的回包里**逐字**包含被写入的值的证据（会话 manifest 的 witness_read + expect，本工具会回到 trace 里再核一次）；写工具自己的回包不算。 |
| 47 | `editor_get_viewport_3d_camera` | editor | get | `payload` | 编辑器 3D 视口相机参数 | payload：编辑器 3D 视口相机参数。判定依据：契约是查询：回包本身就是测量结果，不存在「另一次调用」可等（TASK-111 的 READ_VERBS 规则）。内容级证据 = ok=true 且回包是实质载荷。 |
| 48 | `editor_set_viewport_3d_camera` | editor | set | `editor_state` | 编辑器 3D 视口相机 | editor_state：编辑器 3D 视口相机。判定依据：契约改变的状态既不在盘上、也不（在这个工程的视口里）可靠地反映成像素：它是编辑器进程自己的 GUI / 插件 / 文件系统状态，或运行中游戏进程的内存态。这条通道只接受**另一次独立读调用**在自己的回包里**逐字**包含被写入的值的证据（会话 manifest 的 witness_read + expect，本工具会回到 trace 里再核一次）；写工具自己的回包不算。 |
| 49 | `running_game_get_scene_tree` | game | get | `payload` | 运行中游戏的场景树 | payload：运行中游戏的场景树。判定依据：契约是查询：回包本身就是测量结果，不存在「另一次调用」可等（TASK-111 的 READ_VERBS 规则）。内容级证据 = ok=true 且回包是实质载荷。 |
| 50 | `running_game_get_node_properties` | game | get | `payload` | 运行期节点属性值 | payload：运行期节点属性值。判定依据：契约是查询：回包本身就是测量结果，不存在「另一次调用」可等（TASK-111 的 READ_VERBS 规则）。内容级证据 = ok=true 且回包是实质载荷。 |
| 51 | `running_game_set_node_property` | game | set | `pixel_effect` | 运行中节点的属性（画面随之变） | pixel_effect：运行中节点的属性（画面随之变）。判定依据：契约改变的是被渲染的画面：编辑器视口或运行中游戏的帧，ledger 的 ok_effect_observed（截图前后真的变了像素）就是这条通道的内容级证据，回包里的成功字样不算。 |
| 52 | `running_game_capture_frames` | game | capture | `payload` | 连续帧的载荷 | payload：连续帧的载荷。判定依据：契约是查询：回包本身就是测量结果，不存在「另一次调用」可等（TASK-111 的 READ_VERBS 规则）。内容级证据 = ok=true 且回包是实质载荷。 |
| 53 | `running_game_get_node_property_samples` | game | get | `payload` | 属性随时间的采样 | payload：属性随时间的采样。判定依据：契约是查询：回包本身就是测量结果，不存在「另一次调用」可等（TASK-111 的 READ_VERBS 规则）。内容级证据 = ok=true 且回包是实质载荷。 |
| 54 | `running_game_execute_gdscript` | game | execute | `payload` | 游戏进程里被求值的返回值 | payload：游戏进程里被求值的返回值。判定依据：契约是查询：回包本身就是测量结果，不存在「另一次调用」可等（TASK-111 的 READ_VERBS 规则）。内容级证据 = ok=true 且回包是实质载荷。 |
| 55 | `running_game_create_input_recording` | game | create | `editor_state` | 运行期游戏的输入录制缓冲（由 stop 的回包逐字读回） | editor_state：运行期游戏的输入录制缓冲（由 stop 的回包逐字读回）。判定依据：契约改变的状态既不在盘上、也不（在这个工程的视口里）可靠地反映成像素：它是编辑器进程自己的 GUI / 插件 / 文件系统状态，或运行中游戏进程的内存态。这条通道只接受**另一次独立读调用**在自己的回包里**逐字**包含被写入的值的证据（会话 manifest 的 witness_read + expect，本工具会回到 trace 里再核一次）；写工具自己的回包不算。 |
| 56 | `running_game_stop_input_recording` | game | stop | `editor_state` | 运行期游戏的输入录制缓冲（回包里的 event_count/events） | editor_state：运行期游戏的输入录制缓冲（回包里的 event_count/events）。判定依据：契约改变的状态既不在盘上、也不（在这个工程的视口里）可靠地反映成像素：它是编辑器进程自己的 GUI / 插件 / 文件系统状态，或运行中游戏进程的内存态。这条通道只接受**另一次独立读调用**在自己的回包里**逐字**包含被写入的值的证据（会话 manifest 的 witness_read + expect，本工具会回到 trace 里再核一次）；写工具自己的回包不算。 |
| 57 | `running_game_play_input_recording` | game | play | `pixel_effect` | 回放按键驱动出的画面 | pixel_effect：回放按键驱动出的画面。判定依据：契约改变的是被渲染的画面：编辑器视口或运行中游戏的帧，ledger 的 ok_effect_observed（截图前后真的变了像素）就是这条通道的内容级证据，回包里的成功字样不算。 |
| 58 | `running_game_find_nodes_by_script` | game | find | `payload` | 按脚本检索的结果 | payload：按脚本检索的结果。判定依据：契约是查询：回包本身就是测量结果，不存在「另一次调用」可等（TASK-111 的 READ_VERBS 规则）。内容级证据 = ok=true 且回包是实质载荷。 |
| 59 | `running_game_get_autoload_node` | game | get | `payload` | autoload 节点查询 | payload：autoload 节点查询。判定依据：契约是查询：回包本身就是测量结果，不存在「另一次调用」可等（TASK-111 的 READ_VERBS 规则）。内容级证据 = ok=true 且回包是实质载荷。 |
| 60 | `running_game_get_node_properties_batch` | game | get | `payload` | 批量属性值 | payload：批量属性值。判定依据：契约是查询：回包本身就是测量结果，不存在「另一次调用」可等（TASK-111 的 READ_VERBS 规则）。内容级证据 = ok=true 且回包是实质载荷。 |
| 61 | `running_game_find_ui_elements` | game | find | `payload` | UI 元素清单 | payload：UI 元素清单。判定依据：契约是查询：回包本身就是测量结果，不存在「另一次调用」可等（TASK-111 的 READ_VERBS 规则）。内容级证据 = ok=true 且回包是实质载荷。 |
| 62 | `running_game_simulate_button_click_by_text` | game | simulate | `pixel_effect` | 点击按钮引发的画面变化 | pixel_effect：点击按钮引发的画面变化。判定依据：契约改变的是被渲染的画面：编辑器视口或运行中游戏的帧，ledger 的 ok_effect_observed（截图前后真的变了像素）就是这条通道的内容级证据，回包里的成功字样不算。 |
| 63 | `running_game_find_node_when_available` | game | find | `payload` | 等到的节点（{"found":true,...} 就是测量结果） | payload：等到的节点（{"found":true,...} 就是测量结果）。判定依据：契约是查询：回包本身就是测量结果，不存在「另一次调用」可等（TASK-111 的 READ_VERBS 规则）。内容级证据 = ok=true 且回包是实质载荷。 |
| 64 | `running_game_find_nearby_nodes` | game | find | `payload` | 附近节点清单 | payload：附近节点清单。判定依据：契约是查询：回包本身就是测量结果，不存在「另一次调用」可等（TASK-111 的 READ_VERBS 规则）。内容级证据 = ok=true 且回包是实质载荷。 |
| 65 | `running_game_move_player_to_target` | game | move | `pixel_effect` | 玩家被移到的位置（画面随之变） | pixel_effect：玩家被移到的位置（画面随之变）。判定依据：契约改变的是被渲染的画面：编辑器视口或运行中游戏的帧，ledger 的 ok_effect_observed（截图前后真的变了像素）就是这条通道的内容级证据，回包里的成功字样不算。 |
| 66 | `running_game_capture_signal_emissions` | game | capture | `payload` | 信号发射记录 | payload：信号发射记录。判定依据：契约是查询：回包本身就是测量结果，不存在「另一次调用」可等（TASK-111 的 READ_VERBS 规则）。内容级证据 = ok=true 且回包是实质载荷。 |
| 67 | `editor_get_performance_monitors` | editor | get | `payload` | 性能监视器的采样 | payload：性能监视器的采样。判定依据：契约是查询：回包本身就是测量结果，不存在「另一次调用」可等（TASK-111 的 READ_VERBS 规则）。内容级证据 = ok=true 且回包是实质载荷。 |
| 68 | `project_list_scripts` | both | list | `payload` | 脚本清单 | payload：脚本清单。判定依据：契约是查询：回包本身就是测量结果，不存在「另一次调用」可等（TASK-111 的 READ_VERBS 规则）。内容级证据 = ok=true 且回包是实质载荷。 |
| 69 | `project_read_script` | both | read | `payload` | 脚本文件的文本 | payload：脚本文件的文本。判定依据：契约是查询：回包本身就是测量结果，不存在「另一次调用」可等（TASK-111 的 READ_VERBS 规则）。内容级证据 = ok=true 且回包是实质载荷。 |
| 70 | `project_create_script` | both | create | `file_effect` | 新建的脚本文件 | file_effect：新建的脚本文件。判定依据：契约写的是盘上的产物：它落盘之后可以被任何一次 project_read_* / project_get_filesystem_tree 重新读到，所以权威证据是文件本身，不是回包里的成功字样，也不是编辑器画面。 |
| 71 | `project_edit_script` | both | edit | `file_effect` | 被改写的脚本文件 | file_effect：被改写的脚本文件。判定依据：契约写的是盘上的产物：它落盘之后可以被任何一次 project_read_* / project_get_filesystem_tree 重新读到，所以权威证据是文件本身，不是回包里的成功字样，也不是编辑器画面。 |
| 72 | `editor_set_node_script` | editor | set | `editor_state` | 节点挂载的脚本（Node.get_script().resource_path） | editor_state：节点挂载的脚本（Node.get_script().resource_path）。判定依据：契约改变的状态既不在盘上、也不（在这个工程的视口里）可靠地反映成像素：它是编辑器进程自己的 GUI / 插件 / 文件系统状态，或运行中游戏进程的内存态。这条通道只接受**另一次独立读调用**在自己的回包里**逐字**包含被写入的值的证据（会话 manifest 的 witness_read + expect，本工具会回到 trace 里再核一次）；写工具自己的回包不算。 |
| 73 | `editor_get_open_scripts` | editor | get | `payload` | 打开的脚本文档 | payload：打开的脚本文档。判定依据：契约是查询：回包本身就是测量结果，不存在「另一次调用」可等（TASK-111 的 READ_VERBS 规则）。内容级证据 = ok=true 且回包是实质载荷。 |
| 74 | `project_validate_script` | both | validate | `payload` | 校验判词 | payload：校验判词。判定依据：契约是查询：回包本身就是测量结果，不存在「另一次调用」可等（TASK-111 的 READ_VERBS 规则）。内容级证据 = ok=true 且回包是实质载荷。 |
| 75 | `editor_simulate_key` | editor | simulate | `editor_state` | 编辑器进程自己的输入队列（D59/GDR-21 范围排除：本循环不驱动编辑器输入） | editor_state：编辑器进程自己的输入队列（D59/GDR-21 范围排除：本循环不驱动编辑器输入）。判定依据：契约改变的状态既不在盘上、也不（在这个工程的视口里）可靠地反映成像素：它是编辑器进程自己的 GUI / 插件 / 文件系统状态，或运行中游戏进程的内存态。这条通道只接受**另一次独立读调用**在自己的回包里**逐字**包含被写入的值的证据（会话 manifest 的 witness_read + expect，本工具会回到 trace 里再核一次）；写工具自己的回包不算。 |
| 76 | `editor_simulate_mouse_click` | editor | simulate | `editor_state` | 编辑器进程自己的输入队列（D59/GDR-21 范围排除） | editor_state：编辑器进程自己的输入队列（D59/GDR-21 范围排除）。判定依据：契约改变的状态既不在盘上、也不（在这个工程的视口里）可靠地反映成像素：它是编辑器进程自己的 GUI / 插件 / 文件系统状态，或运行中游戏进程的内存态。这条通道只接受**另一次独立读调用**在自己的回包里**逐字**包含被写入的值的证据（会话 manifest 的 witness_read + expect，本工具会回到 trace 里再核一次）；写工具自己的回包不算。 |
| 77 | `editor_simulate_mouse_move` | editor | simulate | `editor_state` | 编辑器进程自己的输入队列（D59/GDR-21 范围排除） | editor_state：编辑器进程自己的输入队列（D59/GDR-21 范围排除）。判定依据：契约改变的状态既不在盘上、也不（在这个工程的视口里）可靠地反映成像素：它是编辑器进程自己的 GUI / 插件 / 文件系统状态，或运行中游戏进程的内存态。这条通道只接受**另一次独立读调用**在自己的回包里**逐字**包含被写入的值的证据（会话 manifest 的 witness_read + expect，本工具会回到 trace 里再核一次）；写工具自己的回包不算。 |
| 78 | `editor_simulate_input_action` | editor | simulate | `editor_state` | 编辑器进程自己的输入队列（D59/GDR-21 范围排除） | editor_state：编辑器进程自己的输入队列（D59/GDR-21 范围排除）。判定依据：契约改变的状态既不在盘上、也不（在这个工程的视口里）可靠地反映成像素：它是编辑器进程自己的 GUI / 插件 / 文件系统状态，或运行中游戏进程的内存态。这条通道只接受**另一次独立读调用**在自己的回包里**逐字**包含被写入的值的证据（会话 manifest 的 witness_read + expect，本工具会回到 trace 里再核一次）；写工具自己的回包不算。 |
| 79 | `editor_get_input_actions` | editor | get | `payload` | InputMap 动作表 | payload：InputMap 动作表。判定依据：契约是查询：回包本身就是测量结果，不存在「另一次调用」可等（TASK-111 的 READ_VERBS 规则）。内容级证据 = ok=true 且回包是实质载荷。 |
| 80 | `editor_add_input_action` | editor | add | `file_effect` | project.godot 的 InputMap 段 | file_effect：project.godot 的 InputMap 段。判定依据：契约写的是盘上的产物：它落盘之后可以被任何一次 project_read_* / project_get_filesystem_tree 重新读到，所以权威证据是文件本身，不是回包里的成功字样，也不是编辑器画面。 |
| 81 | `editor_simulate_input_sequence` | editor | simulate | `editor_state` | 编辑器进程自己的输入队列（D59/GDR-21 范围排除） | editor_state：编辑器进程自己的输入队列（D59/GDR-21 范围排除）。判定依据：契约改变的状态既不在盘上、也不（在这个工程的视口里）可靠地反映成像素：它是编辑器进程自己的 GUI / 插件 / 文件系统状态，或运行中游戏进程的内存态。这条通道只接受**另一次独立读调用**在自己的回包里**逐字**包含被写入的值的证据（会话 manifest 的 witness_read + expect，本工具会回到 trace 里再核一次）；写工具自己的回包不算。 |
| 82 | `editor_find_nodes_by_type` | editor | find | `payload` | 按类型检索的结果 | payload：按类型检索的结果。判定依据：契约是查询：回包本身就是测量结果，不存在「另一次调用」可等（TASK-111 的 READ_VERBS 规则）。内容级证据 = ok=true 且回包是实质载荷。 |
| 83 | `editor_set_node_property_batch` | editor | set | `pixel_effect` | 一批节点的属性（视口可见） | pixel_effect：一批节点的属性（视口可见）。判定依据：契约改变的是被渲染的画面：编辑器视口或运行中游戏的帧，ledger 的 ok_effect_observed（截图前后真的变了像素）就是这条通道的内容级证据，回包里的成功字样不算。 |
| 84 | `editor_list_signal_connections` | editor | list | `payload` | 场景的连接表 | payload：场景的连接表。判定依据：契约是查询：回包本身就是测量结果，不存在「另一次调用」可等（TASK-111 的 READ_VERBS 规则）。内容级证据 = ok=true 且回包是实质载荷。 |
| 85 | `editor_add_nodes_batch` | editor | add | `pixel_effect` | 批量新增的节点（视口可见） | pixel_effect：批量新增的节点（视口可见）。判定依据：契约改变的是被渲染的画面：编辑器视口或运行中游戏的帧，ledger 的 ok_effect_observed（截图前后真的变了像素）就是这条通道的内容级证据，回包里的成功字样不算。 |
| 86 | `project_find_files_referencing_symbol` | both | find | `payload` | 引用检索的结果 | payload：引用检索的结果。判定依据：契约是查询：回包本身就是测量结果，不存在「另一次调用」可等（TASK-111 的 READ_VERBS 规则）。内容级证据 = ok=true 且回包是实质载荷。 |
| 87 | `project_get_scene_dependencies` | both | get | `payload` | 场景依赖清单 | payload：场景依赖清单。判定依据：契约是查询：回包本身就是测量结果，不存在「另一次调用」可等（TASK-111 的 READ_VERBS 规则）。内容级证据 = ok=true 且回包是实质载荷。 |
| 88 | `project_set_node_property_across_scenes` | both | set | `file_effect` | 一批 .tscn 文件里的节点属性 | file_effect：一批 .tscn 文件里的节点属性。判定依据：契约写的是盘上的产物：它落盘之后可以被任何一次 project_read_* / project_get_filesystem_tree 重新读到，所以权威证据是文件本身，不是回包里的成功字样，也不是编辑器画面。 |
| 89 | `editor_list_animations` | editor | list | `payload` | 动画库清单 | payload：动画库清单。判定依据：契约是查询：回包本身就是测量结果，不存在「另一次调用」可等（TASK-111 的 READ_VERBS 规则）。内容级证据 = ok=true 且回包是实质载荷。 |
| 90 | `editor_create_animation` | editor | create | `editor_state` | 动画库里的动画（AnimationPlayer） | editor_state：动画库里的动画（AnimationPlayer）。判定依据：契约改变的状态既不在盘上、也不（在这个工程的视口里）可靠地反映成像素：它是编辑器进程自己的 GUI / 插件 / 文件系统状态，或运行中游戏进程的内存态。这条通道只接受**另一次独立读调用**在自己的回包里**逐字**包含被写入的值的证据（会话 manifest 的 witness_read + expect，本工具会回到 trace 里再核一次）；写工具自己的回包不算。 |
| 91 | `editor_add_animation_track` | editor | add | `editor_state` | 动画的轨道表（Animation） | editor_state：动画的轨道表（Animation）。判定依据：契约改变的状态既不在盘上、也不（在这个工程的视口里）可靠地反映成像素：它是编辑器进程自己的 GUI / 插件 / 文件系统状态，或运行中游戏进程的内存态。这条通道只接受**另一次独立读调用**在自己的回包里**逐字**包含被写入的值的证据（会话 manifest 的 witness_read + expect，本工具会回到 trace 里再核一次）；写工具自己的回包不算。 |
| 92 | `editor_set_animation_keyframe` | editor | set | `editor_state` | 动画的关键帧（Animation） | editor_state：动画的关键帧（Animation）。判定依据：契约改变的状态既不在盘上、也不（在这个工程的视口里）可靠地反映成像素：它是编辑器进程自己的 GUI / 插件 / 文件系统状态，或运行中游戏进程的内存态。这条通道只接受**另一次独立读调用**在自己的回包里**逐字**包含被写入的值的证据（会话 manifest 的 witness_read + expect，本工具会回到 trace 里再核一次）；写工具自己的回包不算。 |
| 93 | `editor_get_animation_info` | editor | get | `payload` | 动画的轨道/关键帧 | payload：动画的轨道/关键帧。判定依据：契约是查询：回包本身就是测量结果，不存在「另一次调用」可等（TASK-111 的 READ_VERBS 规则）。内容级证据 = ok=true 且回包是实质载荷。 |
| 94 | `editor_remove_animation` | editor | remove | `editor_state` | 动画库里的动画（AnimationPlayer） | editor_state：动画库里的动画（AnimationPlayer）。判定依据：契约改变的状态既不在盘上、也不（在这个工程的视口里）可靠地反映成像素：它是编辑器进程自己的 GUI / 插件 / 文件系统状态，或运行中游戏进程的内存态。这条通道只接受**另一次独立读调用**在自己的回包里**逐字**包含被写入的值的证据（会话 manifest 的 witness_read + expect，本工具会回到 trace 里再核一次）；写工具自己的回包不算。 |
| 95 | `editor_get_tilemap_info` | editor | get | `payload` | TileMap/GridMap 信息 | payload：TileMap/GridMap 信息。判定依据：契约是查询：回包本身就是测量结果，不存在「另一次调用」可等（TASK-111 的 READ_VERBS 规则）。内容级证据 = ok=true 且回包是实质载荷。 |
| 96 | `editor_get_tilemap_used_cells` | editor | get | `payload` | 已用格子坐标 | payload：已用格子坐标。判定依据：契约是查询：回包本身就是测量结果，不存在「另一次调用」可等（TASK-111 的 READ_VERBS 规则）。内容级证据 = ok=true 且回包是实质载荷。 |
| 97 | `editor_remove_all_tilemap_cells` | editor | remove | `pixel_effect` | 清空后的 TileMap（视口画出来了） | pixel_effect：清空后的 TileMap（视口画出来了）。判定依据：契约改变的是被渲染的画面：编辑器视口或运行中游戏的帧，ledger 的 ok_effect_observed（截图前后真的变了像素）就是这条通道的内容级证据，回包里的成功字样不算。 |
| 98 | `editor_set_tilemap_cell` | editor | set | `pixel_effect` | TileMap 格子（视口画出来了） | pixel_effect：TileMap 格子（视口画出来了）。判定依据：契约改变的是被渲染的画面：编辑器视口或运行中游戏的帧，ledger 的 ok_effect_observed（截图前后真的变了像素）就是这条通道的内容级证据，回包里的成功字样不算。 |
| 99 | `editor_set_tilemap_cells_in_rect` | editor | set | `pixel_effect` | TileMap 矩形区域（视口画出来了） | pixel_effect：TileMap 矩形区域（视口画出来了）。判定依据：契约改变的是被渲染的画面：编辑器视口或运行中游戏的帧，ledger 的 ok_effect_observed（截图前后真的变了像素）就是这条通道的内容级证据，回包里的成功字样不算。 |
| 100 | `editor_get_tilemap_cell` | editor | get | `payload` | 单个格子的值 | payload：单个格子的值。判定依据：契约是查询：回包本身就是测量结果，不存在「另一次调用」可等（TASK-111 的 READ_VERBS 规则）。内容级证据 = ok=true 且回包是实质载荷。 |
| 101 | `project_read_resource` | both | read | `payload` | 资源文件的文本 | payload：资源文件的文本。判定依据：契约是查询：回包本身就是测量结果，不存在「另一次调用」可等（TASK-111 的 READ_VERBS 规则）。内容级证据 = ok=true 且回包是实质载荷。 |
| 102 | `project_add_autoload` | both | add | `file_effect` | project.godot 的 autoload 段 | file_effect：project.godot 的 autoload 段。判定依据：契约写的是盘上的产物：它落盘之后可以被任何一次 project_read_* / project_get_filesystem_tree 重新读到，所以权威证据是文件本身，不是回包里的成功字样，也不是编辑器画面。 |
| 103 | `project_remove_autoload` | both | remove | `file_effect` | project.godot 的 autoload 段 | file_effect：project.godot 的 autoload 段。判定依据：契约写的是盘上的产物：它落盘之后可以被任何一次 project_read_* / project_get_filesystem_tree 重新读到，所以权威证据是文件本身，不是回包里的成功字样，也不是编辑器画面。 |
| 104 | `project_edit_resource` | both | edit | `file_effect` | 被改写的 .tres | file_effect：被改写的 .tres。判定依据：契约写的是盘上的产物：它落盘之后可以被任何一次 project_read_* / project_get_filesystem_tree 重新读到，所以权威证据是文件本身，不是回包里的成功字样，也不是编辑器画面。 |
| 105 | `project_create_resource` | both | create | `file_effect` | 新建的 .tres | file_effect：新建的 .tres。判定依据：契约写的是盘上的产物：它落盘之后可以被任何一次 project_read_* / project_get_filesystem_tree 重新读到，所以权威证据是文件本身，不是回包里的成功字样，也不是编辑器画面。 |
| 106 | `project_get_resource_preview` | both | get | `payload` | 资源预览 | payload：资源预览。判定依据：契约是查询：回包本身就是测量结果，不存在「另一次调用」可等（TASK-111 的 READ_VERBS 规则）。内容级证据 = ok=true 且回包是实质载荷。 |
| 107 | `project_get_export_info` | both | get | `payload` | 导出信息 | payload：导出信息。判定依据：契约是查询：回包本身就是测量结果，不存在「另一次调用」可等（TASK-111 的 READ_VERBS 规则）。内容级证据 = ok=true 且回包是实质载荷。 |
| 108 | `project_list_export_presets` | both | list | `payload` | 预设清单 | payload：预设清单。判定依据：契约是查询：回包本身就是测量结果，不存在「另一次调用」可等（TASK-111 的 READ_VERBS 规则）。内容级证据 = ok=true 且回包是实质载荷。 |
| 109 | `project_read_shader` | both | read | `payload` | shader 源码文本 | payload：shader 源码文本。判定依据：契约是查询：回包本身就是测量结果，不存在「另一次调用」可等（TASK-111 的 READ_VERBS 规则）。内容级证据 = ok=true 且回包是实质载荷。 |
| 110 | `project_create_shader` | both | create | `file_effect` | 新建的 .gdshader | file_effect：新建的 .gdshader。判定依据：契约写的是盘上的产物：它落盘之后可以被任何一次 project_read_* / project_get_filesystem_tree 重新读到，所以权威证据是文件本身，不是回包里的成功字样，也不是编辑器画面。 |
| 111 | `project_edit_shader` | both | edit | `file_effect` | 被改写的 .gdshader | file_effect：被改写的 .gdshader。判定依据：契约写的是盘上的产物：它落盘之后可以被任何一次 project_read_* / project_get_filesystem_tree 重新读到，所以权威证据是文件本身，不是回包里的成功字样，也不是编辑器画面。 |
| 112 | `editor_set_shader_material` | editor | set | `pixel_effect` | 材质/shader 挂载（视口着色随之变） | pixel_effect：材质/shader 挂载（视口着色随之变）。判定依据：契约改变的是被渲染的画面：编辑器视口或运行中游戏的帧，ledger 的 ok_effect_observed（截图前后真的变了像素）就是这条通道的内容级证据，回包里的成功字样不算。 |
| 113 | `editor_set_shader_param` | editor | set | `pixel_effect` | shader uniform（视口着色随之变） | pixel_effect：shader uniform（视口着色随之变）。判定依据：契约改变的是被渲染的画面：编辑器视口或运行中游戏的帧，ledger 的 ok_effect_observed（截图前后真的变了像素）就是这条通道的内容级证据，回包里的成功字样不算。 |
| 114 | `project_get_shader_params` | both | get | `payload` | shader 参数表 | payload：shader 参数表。判定依据：契约是查询：回包本身就是测量结果，不存在「另一次调用」可等（TASK-111 的 READ_VERBS 规则）。内容级证据 = ok=true 且回包是实质载荷。 |
| 115 | `editor_add_raycast` | editor | add | `pixel_effect` | 射线探测节点（视口可见） | pixel_effect：射线探测节点（视口可见）。判定依据：契约改变的是被渲染的画面：编辑器视口或运行中游戏的帧，ledger 的 ok_effect_observed（截图前后真的变了像素）就是这条通道的内容级证据，回包里的成功字样不算。 |
| 116 | `editor_setup_collision_shape` | editor | setup | `pixel_effect` | 碰撞形状（视口可见） | pixel_effect：碰撞形状（视口可见）。判定依据：契约改变的是被渲染的画面：编辑器视口或运行中游戏的帧，ledger 的 ok_effect_observed（截图前后真的变了像素）就是这条通道的内容级证据，回包里的成功字样不算。 |
| 117 | `editor_set_physics_layers` | editor | set | `editor_state` | 节点的 collision_layer/mask | editor_state：节点的 collision_layer/mask。判定依据：契约改变的状态既不在盘上、也不（在这个工程的视口里）可靠地反映成像素：它是编辑器进程自己的 GUI / 插件 / 文件系统状态，或运行中游戏进程的内存态。这条通道只接受**另一次独立读调用**在自己的回包里**逐字**包含被写入的值的证据（会话 manifest 的 witness_read + expect，本工具会回到 trace 里再核一次）；写工具自己的回包不算。 |
| 118 | `editor_get_physics_layers` | editor | get | `payload` | 物理层掩码 | payload：物理层掩码。判定依据：契约是查询：回包本身就是测量结果，不存在「另一次调用」可等（TASK-111 的 READ_VERBS 规则）。内容级证据 = ok=true 且回包是实质载荷。 |
| 119 | `editor_setup_physics_body` | editor | setup | `editor_state` | 内存里活场景树上的物理体节点 | editor_state：内存里活场景树上的物理体节点。判定依据：契约改变的状态既不在盘上、也不（在这个工程的视口里）可靠地反映成像素：它是编辑器进程自己的 GUI / 插件 / 文件系统状态，或运行中游戏进程的内存态。这条通道只接受**另一次独立读调用**在自己的回包里**逐字**包含被写入的值的证据（会话 manifest 的 witness_read + expect，本工具会回到 trace 里再核一次）；写工具自己的回包不算。 |
| 120 | `editor_get_collision_info` | editor | get | `payload` | 碰撞体信息 | payload：碰撞体信息。判定依据：契约是查询：回包本身就是测量结果，不存在「另一次调用」可等（TASK-111 的 READ_VERBS 规则）。内容级证据 = ok=true 且回包是实质载荷。 |
| 121 | `editor_add_mesh_instance` | editor | add | `editor_state` | 内存里活场景树上的 MeshInstance3D | editor_state：内存里活场景树上的 MeshInstance3D。判定依据：契约改变的状态既不在盘上、也不（在这个工程的视口里）可靠地反映成像素：它是编辑器进程自己的 GUI / 插件 / 文件系统状态，或运行中游戏进程的内存态。这条通道只接受**另一次独立读调用**在自己的回包里**逐字**包含被写入的值的证据（会话 manifest 的 witness_read + expect，本工具会回到 trace 里再核一次）；写工具自己的回包不算。 |
| 122 | `editor_setup_camera_3d` | editor | setup | `editor_state` | 内存里活场景树上的 Camera3D | editor_state：内存里活场景树上的 Camera3D。判定依据：契约改变的状态既不在盘上、也不（在这个工程的视口里）可靠地反映成像素：它是编辑器进程自己的 GUI / 插件 / 文件系统状态，或运行中游戏进程的内存态。这条通道只接受**另一次独立读调用**在自己的回包里**逐字**包含被写入的值的证据（会话 manifest 的 witness_read + expect，本工具会回到 trace 里再核一次）；写工具自己的回包不算。 |
| 123 | `editor_setup_lighting` | editor | setup | `editor_state` | 内存里活场景树上的 Light3D | editor_state：内存里活场景树上的 Light3D。判定依据：契约改变的状态既不在盘上、也不（在这个工程的视口里）可靠地反映成像素：它是编辑器进程自己的 GUI / 插件 / 文件系统状态，或运行中游戏进程的内存态。这条通道只接受**另一次独立读调用**在自己的回包里**逐字**包含被写入的值的证据（会话 manifest 的 witness_read + expect，本工具会回到 trace 里再核一次）；写工具自己的回包不算。 |
| 124 | `editor_set_material_3d` | editor | set | `editor_state` | 节点的 surface override material | editor_state：节点的 surface override material。判定依据：契约改变的状态既不在盘上、也不（在这个工程的视口里）可靠地反映成像素：它是编辑器进程自己的 GUI / 插件 / 文件系统状态，或运行中游戏进程的内存态。这条通道只接受**另一次独立读调用**在自己的回包里**逐字**包含被写入的值的证据（会话 manifest 的 witness_read + expect，本工具会回到 trace 里再核一次）；写工具自己的回包不算。 |
| 125 | `editor_setup_world_environment` | editor | setup | `editor_state` | 内存里活场景树上的 WorldEnvironment | editor_state：内存里活场景树上的 WorldEnvironment。判定依据：契约改变的状态既不在盘上、也不（在这个工程的视口里）可靠地反映成像素：它是编辑器进程自己的 GUI / 插件 / 文件系统状态，或运行中游戏进程的内存态。这条通道只接受**另一次独立读调用**在自己的回包里**逐字**包含被写入的值的证据（会话 manifest 的 witness_read + expect，本工具会回到 trace 里再核一次）；写工具自己的回包不算。 |
| 126 | `editor_add_gridmap` | editor | add | `editor_state` | 内存里活场景树上的 GridMap 节点 | editor_state：内存里活场景树上的 GridMap 节点。判定依据：契约改变的状态既不在盘上、也不（在这个工程的视口里）可靠地反映成像素：它是编辑器进程自己的 GUI / 插件 / 文件系统状态，或运行中游戏进程的内存态。这条通道只接受**另一次独立读调用**在自己的回包里**逐字**包含被写入的值的证据（会话 manifest 的 witness_read + expect，本工具会回到 trace 里再核一次）；写工具自己的回包不算。 |
| 127 | `editor_add_audio_player` | editor | add | `editor_state` | 内存里活场景树上的音频节点 | editor_state：内存里活场景树上的音频节点。判定依据：契约改变的状态既不在盘上、也不（在这个工程的视口里）可靠地反映成像素：它是编辑器进程自己的 GUI / 插件 / 文件系统状态，或运行中游戏进程的内存态。这条通道只接受**另一次独立读调用**在自己的回包里**逐字**包含被写入的值的证据（会话 manifest 的 witness_read + expect，本工具会回到 trace 里再核一次）；写工具自己的回包不算。 |
| 128 | `editor_get_audio_info` | editor | get | `payload` | 音频节点信息 | payload：音频节点信息。判定依据：契约是查询：回包本身就是测量结果，不存在「另一次调用」可等（TASK-111 的 READ_VERBS 规则）。内容级证据 = ok=true 且回包是实质载荷。 |
| 129 | `editor_get_audio_bus_layout` | editor | get | `payload` | 总线布局 | payload：总线布局。判定依据：契约是查询：回包本身就是测量结果，不存在「另一次调用」可等（TASK-111 的 READ_VERBS 规则）。内容级证据 = ok=true 且回包是实质载荷。 |
| 130 | `editor_add_audio_bus` | editor | add | `editor_state` | 内存里的音频总线布局（AudioServer） | editor_state：内存里的音频总线布局（AudioServer）。判定依据：契约改变的状态既不在盘上、也不（在这个工程的视口里）可靠地反映成像素：它是编辑器进程自己的 GUI / 插件 / 文件系统状态，或运行中游戏进程的内存态。这条通道只接受**另一次独立读调用**在自己的回包里**逐字**包含被写入的值的证据（会话 manifest 的 witness_read + expect，本工具会回到 trace 里再核一次）；写工具自己的回包不算。 |
| 131 | `editor_set_audio_bus_property` | editor | set | `editor_state` | 内存里的音频总线布局（AudioServer） | editor_state：内存里的音频总线布局（AudioServer）。判定依据：契约改变的状态既不在盘上、也不（在这个工程的视口里）可靠地反映成像素：它是编辑器进程自己的 GUI / 插件 / 文件系统状态，或运行中游戏进程的内存态。这条通道只接受**另一次独立读调用**在自己的回包里**逐字**包含被写入的值的证据（会话 manifest 的 witness_read + expect，本工具会回到 trace 里再核一次）；写工具自己的回包不算。 |
| 132 | `editor_add_audio_bus_effect` | editor | add | `editor_state` | 内存里的音频总线效果链（AudioServer） | editor_state：内存里的音频总线效果链（AudioServer）。判定依据：契约改变的状态既不在盘上、也不（在这个工程的视口里）可靠地反映成像素：它是编辑器进程自己的 GUI / 插件 / 文件系统状态，或运行中游戏进程的内存态。这条通道只接受**另一次独立读调用**在自己的回包里**逐字**包含被写入的值的证据（会话 manifest 的 witness_read + expect，本工具会回到 trace 里再核一次）；写工具自己的回包不算。 |
| 133 | `project_create_theme` | both | create | `file_effect` | 新建的 .tres 主题 | file_effect：新建的 .tres 主题。判定依据：契约写的是盘上的产物：它落盘之后可以被任何一次 project_read_* / project_get_filesystem_tree 重新读到，所以权威证据是文件本身，不是回包里的成功字样，也不是编辑器画面。 |
| 134 | `project_set_theme_color` | both | set | `file_effect` | 主题资源里的颜色项 | file_effect：主题资源里的颜色项。判定依据：契约写的是盘上的产物：它落盘之后可以被任何一次 project_read_* / project_get_filesystem_tree 重新读到，所以权威证据是文件本身，不是回包里的成功字样，也不是编辑器画面。 |
| 135 | `project_set_theme_constant` | both | set | `file_effect` | 主题资源里的常量项 | file_effect：主题资源里的常量项。判定依据：契约写的是盘上的产物：它落盘之后可以被任何一次 project_read_* / project_get_filesystem_tree 重新读到，所以权威证据是文件本身，不是回包里的成功字样，也不是编辑器画面。 |
| 136 | `project_set_theme_font_size` | both | set | `file_effect` | 主题资源里的字号项 | file_effect：主题资源里的字号项。判定依据：契约写的是盘上的产物：它落盘之后可以被任何一次 project_read_* / project_get_filesystem_tree 重新读到，所以权威证据是文件本身，不是回包里的成功字样，也不是编辑器画面。 |
| 137 | `project_set_theme_stylebox` | both | set | `file_effect` | 主题资源里的 StyleBox 项 | file_effect：主题资源里的 StyleBox 项。判定依据：契约写的是盘上的产物：它落盘之后可以被任何一次 project_read_* / project_get_filesystem_tree 重新读到，所以权威证据是文件本身，不是回包里的成功字样，也不是编辑器画面。 |
| 138 | `editor_set_control_theme` | editor | set | `editor_state` | Control 节点挂载的 Theme | editor_state：Control 节点挂载的 Theme。判定依据：契约改变的状态既不在盘上、也不（在这个工程的视口里）可靠地反映成像素：它是编辑器进程自己的 GUI / 插件 / 文件系统状态，或运行中游戏进程的内存态。这条通道只接受**另一次独立读调用**在自己的回包里**逐字**包含被写入的值的证据（会话 manifest 的 witness_read + expect，本工具会回到 trace 里再核一次）；写工具自己的回包不算。 |
| 139 | `project_get_theme_info` | both | get | `payload` | 主题（Theme）内容 | payload：主题（Theme）内容。判定依据：契约是查询：回包本身就是测量结果，不存在「另一次调用」可等（TASK-111 的 READ_VERBS 规则）。内容级证据 = ok=true 且回包是实质载荷。 |
| 140 | `editor_create_animation_tree` | editor | create | `editor_state` | 内存里活场景树上的 AnimationTree | editor_state：内存里活场景树上的 AnimationTree。判定依据：契约改变的状态既不在盘上、也不（在这个工程的视口里）可靠地反映成像素：它是编辑器进程自己的 GUI / 插件 / 文件系统状态，或运行中游戏进程的内存态。这条通道只接受**另一次独立读调用**在自己的回包里**逐字**包含被写入的值的证据（会话 manifest 的 witness_read + expect，本工具会回到 trace 里再核一次）；写工具自己的回包不算。 |
| 141 | `editor_get_animation_tree_structure` | editor | get | `payload` | AnimationTree 结构 | payload：AnimationTree 结构。判定依据：契约是查询：回包本身就是测量结果，不存在「另一次调用」可等（TASK-111 的 READ_VERBS 规则）。内容级证据 = ok=true 且回包是实质载荷。 |
| 142 | `editor_add_state_machine_state` | editor | add | `editor_state` | AnimationTree 状态机里的状态 | editor_state：AnimationTree 状态机里的状态。判定依据：契约改变的状态既不在盘上、也不（在这个工程的视口里）可靠地反映成像素：它是编辑器进程自己的 GUI / 插件 / 文件系统状态，或运行中游戏进程的内存态。这条通道只接受**另一次独立读调用**在自己的回包里**逐字**包含被写入的值的证据（会话 manifest 的 witness_read + expect，本工具会回到 trace 里再核一次）；写工具自己的回包不算。 |
| 143 | `editor_remove_state_machine_state` | editor | remove | `editor_state` | AnimationTree 状态机里的状态 | editor_state：AnimationTree 状态机里的状态。判定依据：契约改变的状态既不在盘上、也不（在这个工程的视口里）可靠地反映成像素：它是编辑器进程自己的 GUI / 插件 / 文件系统状态，或运行中游戏进程的内存态。这条通道只接受**另一次独立读调用**在自己的回包里**逐字**包含被写入的值的证据（会话 manifest 的 witness_read + expect，本工具会回到 trace 里再核一次）；写工具自己的回包不算。 |
| 144 | `editor_add_state_machine_transition` | editor | add | `editor_state` | AnimationTree 状态机里的迁移 | editor_state：AnimationTree 状态机里的迁移。判定依据：契约改变的状态既不在盘上、也不（在这个工程的视口里）可靠地反映成像素：它是编辑器进程自己的 GUI / 插件 / 文件系统状态，或运行中游戏进程的内存态。这条通道只接受**另一次独立读调用**在自己的回包里**逐字**包含被写入的值的证据（会话 manifest 的 witness_read + expect，本工具会回到 trace 里再核一次）；写工具自己的回包不算。 |
| 145 | `editor_remove_state_machine_transition` | editor | remove | `editor_state` | AnimationTree 状态机里的迁移 | editor_state：AnimationTree 状态机里的迁移。判定依据：契约改变的状态既不在盘上、也不（在这个工程的视口里）可靠地反映成像素：它是编辑器进程自己的 GUI / 插件 / 文件系统状态，或运行中游戏进程的内存态。这条通道只接受**另一次独立读调用**在自己的回包里**逐字**包含被写入的值的证据（会话 manifest 的 witness_read + expect，本工具会回到 trace 里再核一次）；写工具自己的回包不算。 |
| 146 | `editor_set_blend_tree_node` | editor | set | `editor_state` | AnimationTree 的混合树节点 | editor_state：AnimationTree 的混合树节点。判定依据：契约改变的状态既不在盘上、也不（在这个工程的视口里）可靠地反映成像素：它是编辑器进程自己的 GUI / 插件 / 文件系统状态，或运行中游戏进程的内存态。这条通道只接受**另一次独立读调用**在自己的回包里**逐字**包含被写入的值的证据（会话 manifest 的 witness_read + expect，本工具会回到 trace 里再核一次）；写工具自己的回包不算。 |
| 147 | `editor_set_animation_tree_parameter` | editor | set | `editor_state` | AnimationTree 的参数表 | editor_state：AnimationTree 的参数表。判定依据：契约改变的状态既不在盘上、也不（在这个工程的视口里）可靠地反映成像素：它是编辑器进程自己的 GUI / 插件 / 文件系统状态，或运行中游戏进程的内存态。这条通道只接受**另一次独立读调用**在自己的回包里**逐字**包含被写入的值的证据（会话 manifest 的 witness_read + expect，本工具会回到 trace 里再核一次）；写工具自己的回包不算。 |
| 148 | `editor_setup_navigation_region` | editor | setup | `editor_state` | 内存里活场景树上的 NavigationRegion | editor_state：内存里活场景树上的 NavigationRegion。判定依据：契约改变的状态既不在盘上、也不（在这个工程的视口里）可靠地反映成像素：它是编辑器进程自己的 GUI / 插件 / 文件系统状态，或运行中游戏进程的内存态。这条通道只接受**另一次独立读调用**在自己的回包里**逐字**包含被写入的值的证据（会话 manifest 的 witness_read + expect，本工具会回到 trace 里再核一次）；写工具自己的回包不算。 |
| 149 | `editor_bake_navigation_mesh` | editor | bake | `pixel_effect` | 烘焙出的导航网格（视口可见） | pixel_effect：烘焙出的导航网格（视口可见）。判定依据：契约改变的是被渲染的画面：编辑器视口或运行中游戏的帧，ledger 的 ok_effect_observed（截图前后真的变了像素）就是这条通道的内容级证据，回包里的成功字样不算。 |
| 150 | `editor_setup_navigation_agent` | editor | setup | `editor_state` | 内存里活场景树上的 NavigationAgent | editor_state：内存里活场景树上的 NavigationAgent。判定依据：契约改变的状态既不在盘上、也不（在这个工程的视口里）可靠地反映成像素：它是编辑器进程自己的 GUI / 插件 / 文件系统状态，或运行中游戏进程的内存态。这条通道只接受**另一次独立读调用**在自己的回包里**逐字**包含被写入的值的证据（会话 manifest 的 witness_read + expect，本工具会回到 trace 里再核一次）；写工具自己的回包不算。 |
| 151 | `editor_set_navigation_layers` | editor | set | `editor_state` | 导航层掩码 | editor_state：导航层掩码。判定依据：契约改变的状态既不在盘上、也不（在这个工程的视口里）可靠地反映成像素：它是编辑器进程自己的 GUI / 插件 / 文件系统状态，或运行中游戏进程的内存态。这条通道只接受**另一次独立读调用**在自己的回包里**逐字**包含被写入的值的证据（会话 manifest 的 witness_read + expect，本工具会回到 trace 里再核一次）；写工具自己的回包不算。 |
| 152 | `editor_get_navigation_info` | editor | get | `payload` | 导航区域/代理信息 | payload：导航区域/代理信息。判定依据：契约是查询：回包本身就是测量结果，不存在「另一次调用」可等（TASK-111 的 READ_VERBS 规则）。内容级证据 = ok=true 且回包是实质载荷。 |
| 153 | `editor_create_particles` | editor | create | `editor_state` | 内存里活场景树上的粒子系统 | editor_state：内存里活场景树上的粒子系统。判定依据：契约改变的状态既不在盘上、也不（在这个工程的视口里）可靠地反映成像素：它是编辑器进程自己的 GUI / 插件 / 文件系统状态，或运行中游戏进程的内存态。这条通道只接受**另一次独立读调用**在自己的回包里**逐字**包含被写入的值的证据（会话 manifest 的 witness_read + expect，本工具会回到 trace 里再核一次）；写工具自己的回包不算。 |
| 154 | `editor_set_particle_material` | editor | set | `pixel_effect` | 粒子材质（视口可见） | pixel_effect：粒子材质（视口可见）。判定依据：契约改变的是被渲染的画面：编辑器视口或运行中游戏的帧，ledger 的 ok_effect_observed（截图前后真的变了像素）就是这条通道的内容级证据，回包里的成功字样不算。 |
| 155 | `editor_set_particle_color_gradient` | editor | set | `pixel_effect` | 粒子渐变（视口可见） | pixel_effect：粒子渐变（视口可见）。判定依据：契约改变的是被渲染的画面：编辑器视口或运行中游戏的帧，ledger 的 ok_effect_observed（截图前后真的变了像素）就是这条通道的内容级证据，回包里的成功字样不算。 |
| 156 | `editor_set_particle_preset` | editor | set | `pixel_effect` | 粒子预设（视口可见） | pixel_effect：粒子预设（视口可见）。判定依据：契约改变的是被渲染的画面：编辑器视口或运行中游戏的帧，ledger 的 ok_effect_observed（截图前后真的变了像素）就是这条通道的内容级证据，回包里的成功字样不算。 |
| 157 | `editor_get_particle_info` | editor | get | `payload` | 粒子系统信息 | payload：粒子系统信息。判定依据：契约是查询：回包本身就是测量结果，不存在「另一次调用」可等（TASK-111 的 READ_VERBS 规则）。内容级证据 = ok=true 且回包是实质载荷。 |
| 158 | `project_find_unused_resources` | both | find | `payload` | 未使用资源清单 | payload：未使用资源清单。判定依据：契约是查询：回包本身就是测量结果，不存在「另一次调用」可等（TASK-111 的 READ_VERBS 规则）。内容级证据 = ok=true 且回包是实质载荷。 |
| 159 | `editor_analyze_signal_flow` | editor | analyze | `payload` | 信号流向分析 | payload：信号流向分析。判定依据：契约是查询：回包本身就是测量结果，不存在「另一次调用」可等（TASK-111 的 READ_VERBS 规则）。内容级证据 = ok=true 且回包是实质载荷。 |
| 160 | `project_analyze_scene_complexity` | both | analyze | `payload` | 复杂度分析结果 | payload：复杂度分析结果。判定依据：契约是查询：回包本身就是测量结果，不存在「另一次调用」可等（TASK-111 的 READ_VERBS 规则）。内容级证据 = ok=true 且回包是实质载荷。 |
| 161 | `project_find_script_references` | both | find | `payload` | 脚本引用清单 | payload：脚本引用清单。判定依据：契约是查询：回包本身就是测量结果，不存在「另一次调用」可等（TASK-111 的 READ_VERBS 规则）。内容级证据 = ok=true 且回包是实质载荷。 |
| 162 | `project_detect_circular_dependencies` | both | detect | `payload` | 环依赖判词 | payload：环依赖判词。判定依据：契约是查询：回包本身就是测量结果，不存在「另一次调用」可等（TASK-111 的 READ_VERBS 规则）。内容级证据 = ok=true 且回包是实质载荷。 |
| 163 | `project_get_statistics` | both | get | `payload` | 项目统计 | payload：项目统计。判定依据：契约是查询：回包本身就是测量结果，不存在「另一次调用」可等（TASK-111 的 READ_VERBS 规则）。内容级证据 = ok=true 且回包是实质载荷。 |
| 164 | `running_game_run_test_scenario` | game | run | `pixel_effect` | 场景脚本跑出的画面/状态 | pixel_effect：场景脚本跑出的画面/状态。判定依据：契约改变的是被渲染的画面：编辑器视口或运行中游戏的帧，ledger 的 ok_effect_observed（截图前后真的变了像素）就是这条通道的内容级证据，回包里的成功字样不算。 |
| 165 | `running_game_assert_node_state` | game | assert | `payload` | 断言判词（assert 动词：判词即证据） | payload：断言判词（assert 动词：判词即证据）。判定依据：契约是查询：回包本身就是测量结果，不存在「另一次调用」可等（TASK-111 的 READ_VERBS 规则）。内容级证据 = ok=true 且回包是实质载荷。 |
| 166 | `running_game_assert_screen_text` | game | assert | `payload` | 断言判词（assert 动词：判词即证据） | payload：断言判词（assert 动词：判词即证据）。判定依据：契约是查询：回包本身就是测量结果，不存在「另一次调用」可等（TASK-111 的 READ_VERBS 规则）。内容级证据 = ok=true 且回包是实质载荷。 |
| 167 | `running_game_run_stress_test` | game | run | `pixel_effect` | 压力测试跑出的画面/状态 | pixel_effect：压力测试跑出的画面/状态。判定依据：契约改变的是被渲染的画面：编辑器视口或运行中游戏的帧，ledger 的 ok_effect_observed（截图前后真的变了像素）就是这条通道的内容级证据，回包里的成功字样不算。 |
| 168 | `editor_get_test_report` | editor | get | `payload` | 游戏进程持久化的测试报告 / 本进程累加器 | payload：游戏进程持久化的测试报告 / 本进程累加器。判定依据：契约是查询：回包本身就是测量结果，不存在「另一次调用」可等（TASK-111 的 READ_VERBS 规则）。内容级证据 = ok=true 且回包是实质载荷。 |
| 169 | `os_list_android_devices` | both | list | `payload` | adb devices -l 的解析结果（本机 adb 在、设备为空） | payload：adb devices -l 的解析结果（本机 adb 在、设备为空）。判定依据：契约是查询：回包本身就是测量结果，不存在「另一次调用」可等（TASK-111 的 READ_VERBS 规则）。内容级证据 = ok=true 且回包是实质载荷。 |
| 170 | `project_get_android_preset_info` | both | get | `payload` | Android 预设信息（本机没有 Android 预设，只测到缺失） | payload：Android 预设信息（本机没有 Android 预设，只测到缺失）。判定依据：契约是查询：回包本身就是测量结果，不存在「另一次调用」可等（TASK-111 的 READ_VERBS 规则）。内容级证据 = ok=true 且回包是实质载荷。 |
| 171 | `os_deploy_to_android_device` | both | deploy | `payload` | 部署报告（效果落在外接设备上；本机只能测到它的拒绝分支） | payload：部署报告（效果落在外接设备上；本机只能测到它的拒绝分支）。判定依据：契约是查询：回包本身就是测量结果，不存在「另一次调用」可等（TASK-111 的 READ_VERBS 规则）。内容级证据 = ok=true 且回包是实质载荷。 |
| 172 | `project_build_csharp` | both | build | `file_effect` | dotnet build 产生的程序集 | file_effect：dotnet build 产生的程序集。判定依据：契约写的是盘上的产物：它落盘之后可以被任何一次 project_read_* / project_get_filesystem_tree 重新读到，所以权威证据是文件本身，不是回包里的成功字样，也不是编辑器画面。 |
| 173 | `project_write_text_file` | both | write | `file_effect` | 被写出的文本文件 | file_effect：被写出的文本文件。判定依据：契约写的是盘上的产物：它落盘之后可以被任何一次 project_read_* / project_get_filesystem_tree 重新读到，所以权威证据是文件本身，不是回包里的成功字样，也不是编辑器画面。 |
| 174 | `project_validate_scripts` | both | validate | `payload` | 批量校验判词 | payload：批量校验判词。判定依据：契约是查询：回包本身就是测量结果，不存在「另一次调用」可等（TASK-111 的 READ_VERBS 规则）。内容级证据 = ok=true 且回包是实质载荷。 |
| 175 | `editor_set_node_script_batch` | editor | set | `editor_state` | 一批节点挂载的脚本（Node.get_script().resource_path） | editor_state：一批节点挂载的脚本（Node.get_script().resource_path）。判定依据：契约改变的状态既不在盘上、也不（在这个工程的视口里）可靠地反映成像素：它是编辑器进程自己的 GUI / 插件 / 文件系统状态，或运行中游戏进程的内存态。这条通道只接受**另一次独立读调用**在自己的回包里**逐字**包含被写入的值的证据（会话 manifest 的 witness_read + expect，本工具会回到 trace 里再核一次）；写工具自己的回包不算。 |
| 176 | `editor_set_node_property_updates` | editor | set | `pixel_effect` | 逐帧属性更新（视口随之变） | pixel_effect：逐帧属性更新（视口随之变）。判定依据：契约改变的是被渲染的画面：编辑器视口或运行中游戏的帧，ledger 的 ok_effect_observed（截图前后真的变了像素）就是这条通道的内容级证据，回包里的成功字样不算。 |
| 177 | `project_read_text_file` | both | read | `payload` | 任意文本文件的字节 | payload：任意文本文件的字节。判定依据：契约是查询：回包本身就是测量结果，不存在「另一次调用」可等（TASK-111 的 READ_VERBS 规则）。内容级证据 = ok=true 且回包是实质载荷。 |

### 0.1 readback 声明与见证（TASK-112 B；内容级 `expect` 复核见 TASK-113 C）

声明 **51** 条（来源：`tools/sessions/_exercises/**/*-manifest.json` 的 `readback` 数组）；**经 trace 复核通过 51 条**，被拒 0 条；其中带 `expect` 的声明 **51** 条、**逐字命中 51** 条。

下表只列 `kind = witness_read` 的档位（**有**独立读调用可以点名的那一类，共 51 条）；另外 66 条是 `own_payload`（读类动词，回包即证据、没有第二次调用可点名），它们逐条列在 §0.2。

| 写工具 | kind | 见证读调用 | run | 见证 seq | 内容级 `expect`（逐字） | `expect_absent` | 读回的是什么 |
|---|---|---|---|---|---|---|---|
| `editor_add_scene_instance` | `witness_read` | `editor_get_scene_tree` | runs/_exercises/ex_write5/c4-v5-task111 | 132 | `"Sub1"` | - | 挂载的实例必须出现在编辑场景树里（editor_get_scene_tree 列出被实例化出来的节点） |
| `editor_play_scene` | `witness_read` | `editor_execute_gdscript` | runs/_exercises/ex_editor/h7-task115 | 59 | `"result":true` | - | the editor's own run bar reports playing after the tool answered playing:true, and reports not playing after the matching stop |
| `editor_stop_scene` | `witness_read` | `editor_execute_gdscript` | runs/_exercises/ex_editor/h7-task115 | 61 | `"result":false` | - | after the stop the editor's own run bar reports is_playing_scene() == false |
| `editor_rename_node` | `witness_read` | `editor_get_node_properties` | runs/_exercises/ex_write5/c4-v5-task111 | 138 | `"name":"Ren1"` | - | 读回被改名节点的 name（重命名后按新名字仍可寻址） |
| `editor_connect_signal` | `witness_read` | `editor_list_signal_connections` | runs/_exercises/ex_grid/c6-task118 | 23 | `"method":"_c6_a"` ; `"source":"Ball"` | - | the connection the tool reported as persisted is in the editor's own connection table, read back with scope=user (the same call's counts block answers user:5), and the boundary probe's source (NoSuchNode) is not in it |
| `editor_disconnect_signal` | `witness_read` | `editor_list_signal_connections` | runs/_exercises/ex_write6/c5-task111 | 13 | `"count":0` | - | 断开之后再读一次连接表：count=0（同一次运行、同一个节点） |
| `editor_set_node_groups` | `witness_read` | `editor_get_node_groups` | runs/_exercises/ex_write5/c4-v5-task111 | 143 | `"ex_host"` | - | 读回被写节点的 groups 列表 |
| `editor_set_node_selection` | `witness_read` | `editor_get_selection` | runs/_exercises/ex_editor/h7-task115 | 13 | `"name":"Box"` ; `"type":"ColorRect"` | - | the editor's own EditorSelection really answers with the node the tool selected |
| `editor_remove_node_selection` | `witness_read` | `editor_get_selection` | runs/_exercises/ex_editor/h7-task115 | 22 | `"count":0` ; `"nodes":[]` | - | after the clear the editor's own EditorSelection really is empty, while the same reader had answered a non-empty list earlier in the run |
| `editor_remove_output_log` | `witness_read` | `editor_get_output_log` | runs/_exercises/ex_editor/h7-task115 | 6 | `"in_process":true` | `Godot Engine v4.8.dev` | the Output panel of THIS editor process is readable in-process, and after the clear the engine's own log no longer holds the startup lines it held before it (count 10 -> 1 empty line) |
| `editor_reload_plugin` | `witness_read` | `project_get_settings` | runs/_exercises/ex_editor/h7-task115 | 37 | `res://addons/probe_plugin/plugin.cfg` | - | the addon the tool disabled and enabled again is the one ProjectSettings really lists as enabled |
| `editor_rescan_project_filesystem` | `witness_read` | `project_get_filesystem_tree` | runs/_exercises/ex_editor/h7-task115 | 82 | `editor_probe.tscn` | - | after the rescan the project's own filesystem tree still answers with the scene it swept |
| `editor_set_viewport_3d_camera` | `witness_read` | `editor_get_viewport_3d_camera` | runs/_exercises/ex_3d/h1-task111 | 27 | `"position":{"x":1.0,"y":1.0,"z":1.0}` | - | 下一次调用读回上一次写入的 fov/position |
| `running_game_create_input_recording` | `witness_read` | `running_game_stop_input_recording` | runs/_exercises/ex_rec/h9-task113 | 5 | `"event_count":2` | - | the stop call's answer carries the events of the session create started (event_count > 0) |
| `running_game_stop_input_recording` | `witness_read` | `running_game_get_node_properties` | runs/_exercises/ex_rec/h9-task113 | 2 | `"position"` | - | the position read after the stop differs from the position read before the session (the recorded keys moved the player) |
| `editor_set_node_script` | `witness_read` | `editor_execute_gdscript` | runs/_exercises/ex_write5/c4b-task115 | 12 | `S:res://src/exc4b.gd` | - | the node the tool named really carries that script: the engine's own Node.get_script().resource_path answers it (editor_get_node_properties cannot answer 'script' by name at all - measured -32001 in c4-v5-task111 seq 141) |
| `editor_create_animation` | `witness_read` | `editor_list_animations` | runs/_exercises/ex_anim2/h2b-task111 | 23 | `"Anim5"` | - | 读回动画列表，新建的动画在其中 |
| `editor_add_animation_track` | `witness_read` | `editor_get_animation_info` | runs/_exercises/ex_anim2/h2b-task111 | 29 | `"path":"Target:scale"` | - | 读回同一动画的轨道表 |
| `editor_set_animation_keyframe` | `witness_read` | `editor_get_animation_info` | runs/_exercises/ex_anim2/h2b-task111 | 29 | `"easing":2.0` ; `"time":1.0` | - | 读回同一动画的关键帧 |
| `editor_remove_animation` | `witness_read` | `editor_list_animations` | runs/_exercises/ex_anim2/h2c-task115 | 14 | `"node_path":"Player"` | `DelA` ; `DelB` ; `DelC` ; `DelD` ; `DelE` | the same AnimationPlayer is read back after the removals, and none of the five names this run created and removed is in the library any more (the run's own earlier read, before the removals, is skipped because it still holds them) |
| `editor_set_physics_layers` | `witness_read` | `editor_get_node_properties` | runs/_exercises/ex_write5/c4-v5-task111 | 139 | `"collision_layer":1` | - | 读回同一个节点的 collision_layer / collision_mask |
| `editor_setup_physics_body` | `witness_read` | `editor_get_scene_tree` | runs/_exercises/ex_write5/c4-v5-task111 | 132 | `"PB1"` | - | 建出来的物理体节点必须出现在编辑场景树里 |
| `editor_add_mesh_instance` | `witness_read` | `editor_get_scene_tree` | runs/_exercises/ex_3d/h1b2-task115 | 11 | `"name":"N1"` ; `"type":"MeshInstance3D"` | - | the MeshInstance3D the tool created is in the edited scene tree under the exact name it was given |
| `editor_setup_camera_3d` | `witness_read` | `editor_execute_gdscript` | runs/_exercises/ex_3d/h1b2-task115 | 25 | `C:Camera3D` | - | the node the tool created under the named parent really is a Camera3D |
| `editor_setup_lighting` | `witness_read` | `editor_execute_gdscript` | runs/_exercises/ex_3d/h1b2-task115 | 32 | `L:DirectionalLight3D` | - | the node the tool created under the named parent really is the DirectionalLight3D the first call asked for |
| `editor_set_material_3d` | `witness_read` | `editor_execute_gdscript` | runs/_exercises/ex_3d/h1b2-task115 | 18 | `M:res://assets/mat3d_b.tres` | - | the engine's own MeshInstance3D::get_surface_override_material(0) answers with the material this run assigned |
| `editor_setup_world_environment` | `witness_read` | `editor_execute_gdscript` | runs/_exercises/ex_3d/h1b2-task115 | 39 | `E:WorldEnvironment` | - | the node the tool created for world_env_path really is a WorldEnvironment |
| `editor_add_gridmap` | `witness_read` | `editor_get_scene_tree` | runs/_exercises/ex_grid/c6-task118 | 9 | `"name":"GM6"` ; `"type":"GridMap"` | - | the GridMap the tool created is in the edited scene tree under the exact name it was given, with the engine's own class name; the same tree lists every sibling it created (GM7..GM10) and does NOT list the boundary probe's GMX |
| `editor_add_audio_player` | `witness_read` | `editor_get_node_properties` | runs/_exercises/ex_audio/h5-task113 | 42 | `AudioStreamPlayer2D` | - | the node editor_add_audio_player created must be in the scene as an AudioStreamPlayer2D |
| `editor_add_audio_bus` | `witness_read` | `editor_get_audio_bus_layout` | runs/_exercises/ex_audio/h5-task113 | 22 | `"Music"` | - | the bus editor_add_audio_bus created must appear in the engine's bus layout |
| `editor_set_audio_bus_property` | `witness_read` | `editor_get_audio_bus_layout` | runs/_exercises/ex_audio/h5-task113 | 43 | `"volume_db":-6` | - | the written volume_db must be the bus's real value in the layout |
| `editor_add_audio_bus_effect` | `witness_read` | `editor_get_audio_bus_layout` | runs/_exercises/ex_audio/h5-task113 | 22 | `AudioEffectAmplify` | - | the effect must appear in the bus's effect list with the engine's class name |
| `editor_set_control_theme` | `witness_read` | `editor_execute_gdscript` | runs/_exercises/ex_write5/c4b-task115 | 19 | `T:res://themes/c4b.tres` | - | the Control the tool named really carries that theme: the engine's own Control.theme.resource_path answers it |
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
| `editor_set_node_script_batch` | `witness_read` | `editor_execute_gdscript` | runs/_exercises/ex_grid/c6-task118 | 16 | `S:res://src/Paddle.cs` | - | the node the batch attached to (Background) really carries that script: the engine's own Node.get_script().resource_path answers it. editor_get_node_properties is NOT the witness here - TASK-115 measured it answering -32001 for the property named 'script' (c4-v5-task111 seq 141) |

### 0.2 逐档工具清单（TASK-112 B）

- **`pixel_effect`**（34）：`editor_open_scene` `editor_add_node` `editor_delete_node` `editor_set_node_property` `editor_duplicate_node` `editor_reparent_node` `editor_add_resource_to_node_property` `editor_set_anchor_preset` `running_game_capture_screenshot` `running_game_get_scene_tree` `running_game_get_node_properties` `running_game_set_node_property` `running_game_get_node_property_samples` `running_game_execute_gdscript` `running_game_play_input_recording` `running_game_simulate_button_click_by_text` `running_game_move_player_to_target` `editor_set_node_property_batch` `editor_add_nodes_batch` `editor_remove_all_tilemap_cells` `editor_set_tilemap_cell` `editor_set_tilemap_cells_in_rect` `editor_set_shader_material` `editor_set_shader_param` `editor_add_raycast` `editor_setup_collision_shape` `editor_bake_navigation_mesh` `editor_set_particle_material` `editor_set_particle_color_gradient` `editor_set_particle_preset` `editor_get_particle_info` `running_game_run_test_scenario` `running_game_run_stress_test` `editor_set_node_property_updates`
- **`file_effect`**（24）：`project_set_setting` `project_delete_scene_file` `editor_save_scene` `project_create_scene_file` `editor_capture_screenshot` `project_create_script` `project_edit_script` `editor_add_input_action` `project_set_node_property_across_scenes` `project_add_autoload` `project_remove_autoload` `project_edit_resource` `project_create_resource` `project_create_shader` `project_edit_shader` `project_create_theme` `project_set_theme_color` `project_set_theme_constant` `project_set_theme_font_size` `project_set_theme_stylebox` `running_game_assert_node_state` `running_game_assert_screen_text` `project_build_csharp` `project_write_text_file`
- **`readback`**（111）：`project_get_info` `project_get_filesystem_tree` `project_search_file_names` `project_search_file_contents` `project_get_settings` `project_convert_uid_to_path` `project_convert_path_to_uid` `editor_get_scene_tree` `project_read_scene_file_content` `editor_add_scene_instance` `project_get_scene_exports` `editor_play_scene` `editor_stop_scene` `editor_rename_node` `editor_get_node_properties` `editor_connect_signal` `editor_disconnect_signal` `editor_get_node_groups` `editor_set_node_groups` `editor_find_nodes_in_group` `editor_get_selection` `editor_set_node_selection` `editor_remove_node_selection` `editor_execute_gdscript` `editor_get_errors` `editor_get_output_log` `editor_remove_output_log` `editor_reload_plugin` `editor_rescan_project_filesystem` `editor_get_node_signals` `editor_analyze_screenshot_diff` `editor_get_viewport_3d_camera` `editor_set_viewport_3d_camera` `running_game_capture_frames` `running_game_create_input_recording` `running_game_stop_input_recording` `running_game_find_nodes_by_script` `running_game_get_autoload_node` `running_game_get_node_properties_batch` `running_game_find_ui_elements` `running_game_find_node_when_available` `running_game_find_nearby_nodes` `running_game_capture_signal_emissions` `editor_get_performance_monitors` `project_list_scripts` `project_read_script` `editor_set_node_script` `editor_get_open_scripts` `project_validate_script` `editor_get_input_actions` `editor_find_nodes_by_type` `editor_list_signal_connections` `project_find_files_referencing_symbol` `project_get_scene_dependencies` `editor_list_animations` `editor_create_animation` `editor_add_animation_track` `editor_set_animation_keyframe` `editor_get_animation_info` `editor_remove_animation` `editor_get_tilemap_info` `editor_get_tilemap_used_cells` `editor_get_tilemap_cell` `project_read_resource` `project_get_resource_preview` `project_get_export_info` `project_list_export_presets` `project_read_shader` `project_get_shader_params` `editor_set_physics_layers` `editor_get_physics_layers` `editor_setup_physics_body` `editor_get_collision_info` `editor_add_mesh_instance` `editor_setup_camera_3d` `editor_setup_lighting` `editor_set_material_3d` `editor_setup_world_environment` `editor_add_gridmap` `editor_add_audio_player` `editor_get_audio_info` `editor_get_audio_bus_layout` `editor_add_audio_bus` `editor_set_audio_bus_property` `editor_add_audio_bus_effect` `editor_set_control_theme` `project_get_theme_info` `editor_create_animation_tree` `editor_get_animation_tree_structure` `editor_add_state_machine_state` `editor_remove_state_machine_state` `editor_add_state_machine_transition` `editor_remove_state_machine_transition` `editor_set_blend_tree_node` `editor_set_animation_tree_parameter` `editor_setup_navigation_region` `editor_setup_navigation_agent` `editor_set_navigation_layers` `editor_get_navigation_info` `editor_create_particles` `project_find_unused_resources` `editor_analyze_signal_flow` `project_analyze_scene_complexity` `project_find_script_references` `project_detect_circular_dependencies` `project_get_statistics` `editor_get_test_report` `os_list_android_devices` `project_validate_scripts` `editor_set_node_script_batch` `project_read_text_file`
- **`count_only`**（3）：`editor_set_auto_dismiss_dialogs` `project_get_android_preset_info` `os_deploy_to_android_device`
- **`no_calls`**（5）：`editor_simulate_key` `editor_simulate_mouse_click` `editor_simulate_mouse_move` `editor_simulate_input_action` `editor_simulate_input_sequence`

## 0. 分桶与状态

| 桶 | 工具数 |
|---|---|
| `0` 次 | 5 |
| `1-4` 次 | 0 |
| `>=5` 次 | 172 |
| **合计** | **177** |

| 状态 | 工具数 |
|---|---|
| 达标 | 152 |
| 计数达标缺证据 | 20 |
| 未达(1-4) | 0 |
| 未达(0) | 5 |

| scope | 契约条数 | 被调用过 | 0 次 | ≥5 次 |
|---|---|---|---|---|
| both | 50 | 50 | 0 | 50 |
| editor | 104 | 99 | 5 | 99 |
| game | 23 | 23 | 0 | 23 |

## 1. 总表（177 条契约工具，逐条一行）

| # | tool | scope | verb | 累计调用 | 有效调用 | 边界调用 | 证据档位 | 档位证据 | 证据路径 | 声明通道 | 通道证据 | 状态 |
|---|---|---|---|---|---|---|---|---|---|---|---|---|
| 1 | `project_get_info` | both | get | 8 | 6 | 2 | `readback` | own_payload ×6（读类回包即证据） | runs/_exercises/ex_files/c1-task110(6) ; runs/_exercises/ex_files/c1-smoke(2) | `payload` | 6 | 达标 |
| 2 | `project_get_filesystem_tree` | both | get | 7 | 6 | 1 | `readback` | own_payload ×6（读类回包即证据） | runs/_exercises/ex_files/c1-task110(6) ; runs/_exercises/ex_editor/h7-task115(1) | `payload` | 6 | 达标 |
| 3 | `project_search_file_names` | both | search | 12 | 11 | 1 | `readback` | own_payload ×11（读类回包即证据） | runs/_exercises/ex_files/c1-task110(6) ; runs/_exercises/ex_files/c1b-task110(6) | `payload` | 11 | 达标 |
| 4 | `project_search_file_contents` | both | search | 12 | 11 | 1 | `readback` | own_payload ×11（读类回包即证据） | runs/_exercises/ex_files/c1-task110(6) ; runs/_exercises/ex_files/c1b-task110(6) | `payload` | 11 | 达标 |
| 5 | `project_get_settings` | both | get | 8 | 7 | 1 | `readback` | own_payload ×7（读类回包即证据） | runs/_exercises/ex_files/c1-task110(6) ; runs/_exercises/ex_editor/h7-task115(1) | `payload` | 7 | 达标 |
| 6 | `project_set_setting` | both | set | 6 | 5 | 1 | `file_effect` | ok_file_effect_observed ×5 | runs/_exercises/ex_files/c1-task110(6) | `file_effect` | 5 | 达标 |
| 7 | `project_convert_uid_to_path` | both | convert | 8 | 6 | 2 | `readback` | own_payload ×6（读类回包即证据） | runs/_exercises/ex_files/c1-task110(6) ; runs/_exercises/ex_files/c1-smoke(2) | `payload` | 6 | 达标 |
| 8 | `project_convert_path_to_uid` | both | convert | 6 | 5 | 1 | `readback` | own_payload ×5（读类回包即证据） | runs/_exercises/ex_files/c1-task110(6) | `payload` | 5 | 达标 |
| 9 | `editor_get_scene_tree` | editor | get | 113 | 109 | 4 | `readback` | own_payload ×109（读类回包即证据） | runs/_exercises/ex_write5/c4-v5-task111(7) ; runs/_exercises/ex_scene/c23-task110(6) | `payload` | 109 | 达标 |
| 10 | `project_read_scene_file_content` | both | read | 6 | 5 | 1 | `readback` | own_payload ×5（读类回包即证据） | runs/_exercises/ex_files/c1-task110(6) | `payload` | 5 | 达标 |
| 11 | `editor_open_scene` | editor | open | 86 | 9 | 0 | `pixel_effect` | ok_effect_observed ×9 | runs/breakout/breakout-clean-task097(2) ; runs/pong/pong-clean-task097(2) | `pixel_effect` | 9 | 计数达标缺证据 |
| 12 | `project_delete_scene_file` | both | delete | 10 | 8 | 2 | `file_effect` | ok_file_effect_observed ×8 | runs/_exercises/ex_files/c1-task110(6) ; runs/pong/d3-after(2) | `file_effect` | 8 | 达标 |
| 13 | `editor_add_scene_instance` | editor | add | 30 | 0 | 5 | `readback` | witness `editor_get_scene_tree`@runs/_exercises/ex_write5/c4-v5-task111 seq=132 | runs/_exercises/ex_write/c4-task111(6) ; runs/_exercises/ex_write2/c4b-task111(6) | `editor_state` | 1 | 达标 |
| 14 | `project_get_scene_exports` | both | get | 6 | 5 | 1 | `readback` | own_payload ×5（读类回包即证据） | runs/_exercises/ex_files/c1-task110(6) | `payload` | 5 | 达标 |
| 15 | `editor_play_scene` | editor | play | 7 | 0 | 2 | `readback` | witness `editor_execute_gdscript`@runs/_exercises/ex_editor/h7-task115 seq=59 | runs/_exercises/ex_editor/h7-task115(7) | `editor_state` | 1 | 达标 |
| 16 | `editor_stop_scene` | editor | stop | 7 | 0 | 1 | `readback` | witness `editor_execute_gdscript`@runs/_exercises/ex_editor/h7-task115 seq=61 | runs/_exercises/ex_editor/h7-task115(7) | `editor_state` | 1 | 达标 |
| 17 | `editor_save_scene` | editor | save | 123 | 77 | 0 | `file_effect` | ok_file_effect_observed ×77 | runs/lunarlander/ll-task104-r1(3) ; runs/missilecommand/mc-task103-r1(3) | `file_effect` | 77 | 计数达标缺证据 |
| 18 | `project_create_scene_file` | both | create | 20 | 18 | 2 | `file_effect` | ok_file_effect_observed ×18 | runs/_exercises/ex_files/c1-task110(6) ; runs/_exercises/ex_files/c1c-task110(6) | `file_effect` | 18 | 达标 |
| 19 | `editor_add_node` | editor | add | 36 | 10 | 5 | `pixel_effect` | ok_effect_observed ×10 | runs/_exercises/ex_write/c4-task111(6) ; runs/_exercises/ex_write2/c4b-task111(6) | `pixel_effect` | 10 | 达标 |
| 20 | `editor_delete_node` | editor | delete | 65 | 5 | 0 | `pixel_effect` | ok_effect_observed ×5 | runs/snake/snake-clean-task097(37) ; runs/breakout/breakout-clean-task097(20) | `pixel_effect` | 5 | 计数达标缺证据 |
| 21 | `editor_rename_node` | editor | rename | 30 | 0 | 7 | `readback` | witness `editor_get_node_properties`@runs/_exercises/ex_write5/c4-v5-task111 seq=138 | runs/_exercises/ex_write/c4-task111(6) ; runs/_exercises/ex_write2/c4b-task111(6) | `editor_state` | 1 | 达标 |
| 22 | `editor_set_node_property` | editor | set | 41 | 12 | 0 | `pixel_effect` | ok_effect_observed ×12 | runs/pong/pong-clean-task097(3) ; runs/pong/pong-control-task093(3) | `pixel_effect` | 12 | 计数达标缺证据 |
| 23 | `editor_get_node_properties` | editor | get | 74 | 62 | 12 | `readback` | own_payload ×62（读类回包即证据） | runs/breakout/breakout-clean-task097(10) ; runs/pong/pong-clean-task097(9) | `payload` | 62 | 达标 |
| 24 | `editor_duplicate_node` | editor | duplicate | 30 | 5 | 7 | `pixel_effect` | ok_effect_observed ×5 | runs/_exercises/ex_write/c4-task111(6) ; runs/_exercises/ex_write2/c4b-task111(6) | `pixel_effect` | 5 | 达标 |
| 25 | `editor_connect_signal` | editor | connect | 45 | 0 | 7 | `readback` | witness `editor_list_signal_connections`@runs/_exercises/ex_grid/c6-task118 seq=23 | runs/_exercises/ex_grid/c6-task118(6) ; runs/_exercises/ex_write/c4-task111(6) | `editor_state` | 1 | 达标 |
| 26 | `editor_disconnect_signal` | editor | disconnect | 6 | 0 | 1 | `readback` | witness `editor_list_signal_connections`@runs/_exercises/ex_write6/c5-task111 seq=13 | runs/_exercises/ex_write6/c5-task111(6) | `editor_state` | 1 | 达标 |
| 27 | `editor_reparent_node` | editor | reparent | 30 | 3 | 14 | `pixel_effect` | ok_effect_observed ×3 | runs/_exercises/ex_write/c4-task111(6) ; runs/_exercises/ex_write2/c4b-task111(6) | `pixel_effect` | 3 | 达标 |
| 28 | `editor_add_resource_to_node_property` | editor | add | 33 | 12 | 20 | `pixel_effect` | ok_effect_observed ×12 | runs/_exercises/ex_write4/c4-final-task111(7) ; runs/_exercises/ex_write5/c4-v5-task111(7) | `pixel_effect` | 12 | 达标 |
| 29 | `editor_set_anchor_preset` | editor | set | 24 | 5 | 5 | `pixel_effect` | ok_effect_observed ×5 | runs/_exercises/ex_write/c4-task111(6) ; runs/_exercises/ex_write3/c4c-task111(6) | `pixel_effect` | 5 | 达标 |
| 30 | `editor_get_node_groups` | editor | get | 13 | 11 | 2 | `readback` | own_payload ×11（读类回包即证据） | runs/_exercises/ex_scene/c23-task110(6) ; runs/_exercises/ex_scene2/c23-after-task110(6) | `payload` | 11 | 达标 |
| 31 | `editor_set_node_groups` | editor | set | 36 | 0 | 11 | `readback` | witness `editor_get_node_groups`@runs/_exercises/ex_write5/c4-v5-task111 seq=143 | runs/_exercises/ex_write/c4-task111(7) ; runs/_exercises/ex_write3/c4c-task111(7) | `editor_state` | 1 | 达标 |
| 32 | `editor_find_nodes_in_group` | editor | find | 12 | 10 | 2 | `readback` | own_payload ×10（读类回包即证据） | runs/_exercises/ex_scene/c23-task110(6) ; runs/_exercises/ex_scene2/c23-after-task110(6) | `payload` | 10 | 达标 |
| 33 | `editor_get_selection` | editor | get | 17 | 15 | 2 | `readback` | own_payload ×15（读类回包即证据） | runs/_exercises/ex_scene/c23-task110(6) ; runs/_exercises/ex_scene2/c23-after-task110(6) | `payload` | 15 | 达标 |
| 34 | `editor_set_node_selection` | editor | set | 9 | 0 | 1 | `readback` | witness `editor_get_selection`@runs/_exercises/ex_editor/h7-task115 seq=13 | runs/_exercises/ex_editor/h7-task115(9) | `editor_state` | 1 | 达标 |
| 35 | `editor_remove_node_selection` | editor | remove | 6 | 0 | 1 | `readback` | witness `editor_get_selection`@runs/_exercises/ex_editor/h7-task115 seq=22 | runs/_exercises/ex_editor/h7-task115(6) | `editor_state` | 1 | 达标 |
| 36 | `editor_execute_gdscript` | editor | execute | 26 | 24 | 2 | `readback` | own_payload ×24（读类回包即证据） | runs/_exercises/ex_scene/c23-task110(6) ; runs/_exercises/ex_scene2/c23-after-task110(6) | `payload` | 24 | 达标 |
| 37 | `editor_get_errors` | editor | get | 50 | 50 | 0 | `readback` | own_payload ×50（读类回包即证据） | runs/asteroids/ast-task098-r1(1) ; runs/asteroids/ast-task098-r2(1) | `payload` | 50 | 计数达标缺证据 |
| 38 | `editor_get_output_log` | editor | get | 38 | 34 | 4 | `readback` | own_payload ×34（读类回包即证据） | runs/_exercises/ex_scene/c23-task110(6) ; runs/_exercises/ex_scene2/c23-after-task110(6) | `payload` | 34 | 达标 |
| 39 | `editor_capture_screenshot` | editor | capture | 25 | 25 | 0 | `file_effect` | ok_file_effect_observed ×15 | runs/breakout/breakout-clean-task097(1) ; runs/breakout/breakout-task093(1) | `file_effect` | 15 | 计数达标缺证据 |
| 40 | `running_game_capture_screenshot` | game | capture | 298 | 298 | 0 | `pixel_effect` | ok_effect_observed ×1 | runs/match3/m3-task102-r1(7) ; runs/match3/m3-task102-r2(7) | `payload` | 298 | 计数达标缺证据 |
| 41 | `editor_remove_output_log` | editor | remove | 6 | 0 | 1 | `readback` | witness `editor_get_output_log`@runs/_exercises/ex_editor/h7-task115 seq=6 | runs/_exercises/ex_editor/h7-task115(6) | `editor_state` | 1 | 达标 |
| 42 | `editor_reload_plugin` | editor | reload | 6 | 0 | 1 | `readback` | witness `project_get_settings`@runs/_exercises/ex_editor/h7-task115 seq=37 | runs/_exercises/ex_editor/h7-task115(6) | `editor_state` | 1 | 达标 |
| 43 | `editor_rescan_project_filesystem` | editor | rescan | 6 | 0 | 1 | `readback` | witness `project_get_filesystem_tree`@runs/_exercises/ex_editor/h7-task115 seq=82 | runs/_exercises/ex_editor/h7-task115(6) | `editor_state` | 1 | 达标 |
| 44 | `editor_get_node_signals` | editor | get | 12 | 10 | 2 | `readback` | own_payload ×10（读类回包即证据） | runs/_exercises/ex_scene/c23-task110(6) ; runs/_exercises/ex_scene2/c23-after-task110(6) | `payload` | 10 | 达标 |
| 45 | `editor_analyze_screenshot_diff` | editor | analyze | 8 | 5 | 3 | `readback` | own_payload ×5（读类回包即证据） | runs/_exercises/ex_editor/h7-task115(8) | `payload` | 5 | 达标 |
| 46 | `editor_set_auto_dismiss_dialogs` | editor | set | 7 | 0 | 7 | `count_only` | - | runs/_exercises/ex_editor/h7-task115(7) | `editor_state` | 0 | 计数达标缺证据 |
| 47 | `editor_get_viewport_3d_camera` | editor | get | 6 | 5 | 1 | `readback` | own_payload ×5（读类回包即证据） | runs/_exercises/ex_3d/h1-task111(6) | `payload` | 5 | 达标 |
| 48 | `editor_set_viewport_3d_camera` | editor | set | 6 | 0 | 1 | `readback` | witness `editor_get_viewport_3d_camera`@runs/_exercises/ex_3d/h1-task111 seq=27 | runs/_exercises/ex_3d/h1-task111(6) | `editor_state` | 1 | 达标 |
| 49 | `running_game_get_scene_tree` | game | get | 123 | 123 | 0 | `pixel_effect` | ok_effect_observed ×1 | runs/asteroids/ast-task098-r1(2) ; runs/asteroids/ast-task098-r2(2) | `payload` | 123 | 计数达标缺证据 |
| 50 | `running_game_get_node_properties` | game | get | 58 | 56 | 2 | `pixel_effect` | ok_effect_observed ×8 | runs/_exercises/ex_scene/c23-task110(6) ; runs/_exercises/ex_scene2/c23-after-task110(6) | `payload` | 56 | 达标 |
| 51 | `running_game_set_node_property` | game | set | 49 | 28 | 2 | `pixel_effect` | ok_effect_observed ×28 | runs/pong/pong-clean-task097(5) ; runs/pong/pong-control-task093(5) | `pixel_effect` | 28 | 达标 |
| 52 | `running_game_capture_frames` | game | capture | 36 | 30 | 6 | `readback` | own_payload ×30（读类回包即证据） | runs/_exercises/ex_scene/c23-task110(6) ; runs/_exercises/ex_scene2/c23-after-task110(6) | `payload` | 30 | 达标 |
| 53 | `running_game_get_node_property_samples` | game | get | 122 | 122 | 0 | `pixel_effect` | ok_effect_observed ×35 | runs/spaceinvaders/si-task097-r1(5) ; runs/tetris/tetris-task096(4) | `payload` | 122 | 计数达标缺证据 |
| 54 | `running_game_execute_gdscript` | game | execute | 1626 | 1593 | 33 | `pixel_effect` | ok_effect_observed ×873 | runs/rtype/rt-task104-r1(98) ; runs/rtype/rt-task104-r2(98) | `payload` | 1593 | 达标 |
| 55 | `running_game_create_input_recording` | game | create | 7 | 0 | 1 | `readback` | witness `running_game_stop_input_recording`@runs/_exercises/ex_rec/h9-task113 seq=5 | runs/_exercises/ex_rec/h9-task113(7) | `editor_state` | 1 | 达标 |
| 56 | `running_game_stop_input_recording` | game | stop | 7 | 0 | 0 | `readback` | witness `running_game_get_node_properties`@runs/_exercises/ex_rec/h9-task113 seq=2 | runs/_exercises/ex_rec/h9-task113(7) | `editor_state` | 1 | 计数达标缺证据 |
| 57 | `running_game_play_input_recording` | game | play | 7 | 6 | 1 | `pixel_effect` | ok_effect_observed ×6 | runs/_exercises/ex_rec/h9-task113(7) | `pixel_effect` | 6 | 达标 |
| 58 | `running_game_find_nodes_by_script` | game | find | 12 | 10 | 2 | `readback` | own_payload ×10（读类回包即证据） | runs/_exercises/ex_scene/c23-task110(6) ; runs/_exercises/ex_scene2/c23-after-task110(6) | `payload` | 10 | 达标 |
| 59 | `running_game_get_autoload_node` | game | get | 12 | 10 | 2 | `readback` | own_payload ×10（读类回包即证据） | runs/_exercises/ex_scene/c23-task110(6) ; runs/_exercises/ex_scene2/c23-after-task110(6) | `payload` | 10 | 达标 |
| 60 | `running_game_get_node_properties_batch` | game | get | 36 | 32 | 4 | `readback` | own_payload ×32（读类回包即证据） | runs/_exercises/ex_scene/c23-task110(6) ; runs/_exercises/ex_scene2/c23-after-task110(6) | `payload` | 32 | 达标 |
| 61 | `running_game_find_ui_elements` | game | find | 12 | 10 | 2 | `readback` | own_payload ×10（读类回包即证据） | runs/_exercises/ex_scene/c23-task110(6) ; runs/_exercises/ex_scene2/c23-after-task110(6) | `payload` | 10 | 达标 |
| 62 | `running_game_simulate_button_click_by_text` | game | simulate | 12 | 2 | 2 | `pixel_effect` | ok_effect_observed ×2 | runs/_exercises/ex_scene/c23-task110(6) ; runs/_exercises/ex_scene2/c23-after-task110(6) | `pixel_effect` | 2 | 达标 |
| 63 | `running_game_find_node_when_available` | game | find | 14 | 5 | 9 | `readback` | own_payload ×5（读类回包即证据） | runs/_exercises/ex_grid/c6-task118(6) ; runs/breakout/breakout-clean-task097(1) | `payload` | 5 | 达标 |
| 64 | `running_game_find_nearby_nodes` | game | find | 12 | 10 | 2 | `readback` | own_payload ×10（读类回包即证据） | runs/_exercises/ex_scene/c23-task110(6) ; runs/_exercises/ex_scene2/c23-after-task110(6) | `payload` | 10 | 达标 |
| 65 | `running_game_move_player_to_target` | game | move | 6 | 5 | 1 | `pixel_effect` | ok_effect_observed ×5 | runs/_exercises/ex_nav/h4-task113(6) | `pixel_effect` | 5 | 达标 |
| 66 | `running_game_capture_signal_emissions` | game | capture | 36 | 26 | 10 | `readback` | own_payload ×26（读类回包即证据） | runs/_exercises/ex_scene/c23-task110(6) ; runs/_exercises/ex_scene2/c23-after-task110(6) | `payload` | 26 | 达标 |
| 67 | `editor_get_performance_monitors` | editor | get | 12 | 10 | 2 | `readback` | own_payload ×10（读类回包即证据） | runs/_exercises/ex_scene/c23-task110(6) ; runs/_exercises/ex_scene2/c23-after-task110(6) | `payload` | 10 | 达标 |
| 68 | `project_list_scripts` | both | list | 6 | 5 | 1 | `readback` | own_payload ×5（读类回包即证据） | runs/_exercises/ex_files/c1-task110(6) | `payload` | 5 | 达标 |
| 69 | `project_read_script` | both | read | 8 | 6 | 2 | `readback` | own_payload ×6（读类回包即证据） | runs/_exercises/ex_files/c1-task110(6) ; runs/_exercises/ex_files/c1-smoke(2) | `payload` | 6 | 达标 |
| 70 | `project_create_script` | both | create | 77 | 44 | 1 | `file_effect` | ok_file_effect_observed ×44 | runs/_exercises/ex_files/c1-task110(6) ; runs/_exercises/ex_files/c1b-task110(6) | `file_effect` | 44 | 达标 |
| 71 | `project_edit_script` | both | edit | 60 | 52 | 0 | `file_effect` | ok_file_effect_observed ×52 | runs/tetris/tetris-task096-r2(2) ; runs/asteroids/ast-task098-r1(1) | `file_effect` | 52 | 计数达标缺证据 |
| 72 | `editor_set_node_script` | editor | set | 36 | 0 | 6 | `readback` | witness `editor_execute_gdscript`@runs/_exercises/ex_write5/c4b-task115 seq=12 | runs/_exercises/ex_write/c4-task111(6) ; runs/_exercises/ex_write2/c4b-task111(6) | `editor_state` | 1 | 达标 |
| 73 | `editor_get_open_scripts` | editor | get | 12 | 10 | 2 | `readback` | own_payload ×10（读类回包即证据） | runs/_exercises/ex_scene/c23-task110(6) ; runs/_exercises/ex_scene2/c23-after-task110(6) | `payload` | 10 | 达标 |
| 74 | `project_validate_script` | both | validate | 18 | 3 | 15 | `readback` | own_payload ×3（读类回包即证据） | runs/_exercises/ex_files/c1-task110(6) ; runs/_exercises/ex_files/c1b-task110(6) | `payload` | 3 | 达标 |
| 75 | `editor_simulate_key` | editor | simulate | 0 | 0 | 0 | `no_calls` | - | - | `editor_state` | 0 | 未达(0) |
| 76 | `editor_simulate_mouse_click` | editor | simulate | 0 | 0 | 0 | `no_calls` | - | - | `editor_state` | 0 | 未达(0) |
| 77 | `editor_simulate_mouse_move` | editor | simulate | 0 | 0 | 0 | `no_calls` | - | - | `editor_state` | 0 | 未达(0) |
| 78 | `editor_simulate_input_action` | editor | simulate | 0 | 0 | 0 | `no_calls` | - | - | `editor_state` | 0 | 未达(0) |
| 79 | `editor_get_input_actions` | editor | get | 12 | 10 | 2 | `readback` | own_payload ×10（读类回包即证据） | runs/_exercises/ex_scene/c23-task110(6) ; runs/_exercises/ex_scene2/c23-after-task110(6) | `payload` | 10 | 达标 |
| 80 | `editor_add_input_action` | editor | add | 189 | 122 | 0 | `file_effect` | ok_file_effect_observed ×122 | runs/pong/pong-clean-task097(5) ; runs/pong/pong-control-task093(5) | `file_effect` | 122 | 计数达标缺证据 |
| 81 | `editor_simulate_input_sequence` | editor | simulate | 0 | 0 | 0 | `no_calls` | - | - | `editor_state` | 0 | 未达(0) |
| 82 | `editor_find_nodes_by_type` | editor | find | 12 | 10 | 2 | `readback` | own_payload ×10（读类回包即证据） | runs/_exercises/ex_scene/c23-task110(6) ; runs/_exercises/ex_scene2/c23-after-task110(6) | `payload` | 10 | 达标 |
| 83 | `editor_set_node_property_batch` | editor | set | 30 | 15 | 5 | `pixel_effect` | ok_effect_observed ×15 | runs/_exercises/ex_write/c4-task111(6) ; runs/_exercises/ex_write2/c4b-task111(6) | `pixel_effect` | 15 | 达标 |
| 84 | `editor_list_signal_connections` | editor | list | 14 | 10 | 4 | `readback` | own_payload ×10（读类回包即证据） | runs/_exercises/ex_scene/c23-task110(6) ; runs/_exercises/ex_scene2/c23-after-task110(6) | `payload` | 10 | 达标 |
| 85 | `editor_add_nodes_batch` | editor | add | 106 | 47 | 42 | `pixel_effect` | ok_effect_observed ×47 | runs/pong/d3-after(3) ; runs/pong/d3-after-r2(3) | `pixel_effect` | 47 | 达标 |
| 86 | `project_find_files_referencing_symbol` | both | find | 12 | 11 | 1 | `readback` | own_payload ×11（读类回包即证据） | runs/_exercises/ex_files/c1-task110(6) ; runs/_exercises/ex_files/c1b-task110(6) | `payload` | 11 | 达标 |
| 87 | `project_get_scene_dependencies` | both | get | 6 | 5 | 1 | `readback` | own_payload ×5（读类回包即证据） | runs/_exercises/ex_files/c1-task110(6) | `payload` | 5 | 达标 |
| 88 | `project_set_node_property_across_scenes` | both | set | 18 | 1 | 1 | `file_effect` | ok_file_effect_observed ×1 | runs/_exercises/ex_files/c1-task110(6) ; runs/_exercises/ex_files/c1b-task110(6) | `file_effect` | 1 | 达标 |
| 89 | `editor_list_animations` | editor | list | 15 | 13 | 2 | `readback` | own_payload ×13（读类回包即证据） | runs/_exercises/ex_anim/h2-task111(6) ; runs/_exercises/ex_anim2/h2b-task111(6) | `payload` | 13 | 达标 |
| 90 | `editor_create_animation` | editor | create | 23 | 0 | 2 | `readback` | witness `editor_list_animations`@runs/_exercises/ex_anim2/h2b-task111 seq=23 | runs/_exercises/ex_anim/h2-task111(9) ; runs/_exercises/ex_anim2/h2b-task111(9) | `editor_state` | 1 | 达标 |
| 91 | `editor_add_animation_track` | editor | add | 12 | 0 | 2 | `readback` | witness `editor_get_animation_info`@runs/_exercises/ex_anim2/h2b-task111 seq=29 | runs/_exercises/ex_anim/h2-task111(6) ; runs/_exercises/ex_anim2/h2b-task111(6) | `editor_state` | 1 | 达标 |
| 92 | `editor_set_animation_keyframe` | editor | set | 12 | 0 | 2 | `readback` | witness `editor_get_animation_info`@runs/_exercises/ex_anim2/h2b-task111 seq=29 | runs/_exercises/ex_anim/h2-task111(6) ; runs/_exercises/ex_anim2/h2b-task111(6) | `editor_state` | 1 | 达标 |
| 93 | `editor_get_animation_info` | editor | get | 12 | 10 | 2 | `readback` | own_payload ×10（读类回包即证据） | runs/_exercises/ex_anim/h2-task111(6) ; runs/_exercises/ex_anim2/h2b-task111(6) | `payload` | 10 | 达标 |
| 94 | `editor_remove_animation` | editor | remove | 18 | 0 | 3 | `readback` | witness `editor_list_animations`@runs/_exercises/ex_anim2/h2c-task115 seq=14 | runs/_exercises/ex_anim/h2-task111(6) ; runs/_exercises/ex_anim2/h2b-task111(6) | `editor_state` | 1 | 达标 |
| 95 | `editor_get_tilemap_info` | editor | get | 6 | 5 | 1 | `readback` | own_payload ×5（读类回包即证据） | runs/_exercises/ex_grid/h3-task111(6) | `payload` | 5 | 达标 |
| 96 | `editor_get_tilemap_used_cells` | editor | get | 6 | 5 | 1 | `readback` | own_payload ×5（读类回包即证据） | runs/_exercises/ex_grid/h3-task111(6) | `payload` | 5 | 达标 |
| 97 | `editor_remove_all_tilemap_cells` | editor | remove | 6 | 5 | 1 | `pixel_effect` | ok_effect_observed ×5 | runs/_exercises/ex_grid/h3-task111(6) | `pixel_effect` | 5 | 达标 |
| 98 | `editor_set_tilemap_cell` | editor | set | 10 | 9 | 1 | `pixel_effect` | ok_effect_observed ×9 | runs/_exercises/ex_grid/h3-task111(10) | `pixel_effect` | 9 | 达标 |
| 99 | `editor_set_tilemap_cells_in_rect` | editor | set | 6 | 5 | 1 | `pixel_effect` | ok_effect_observed ×5 | runs/_exercises/ex_grid/h3-task111(6) | `pixel_effect` | 5 | 达标 |
| 100 | `editor_get_tilemap_cell` | editor | get | 6 | 5 | 1 | `readback` | own_payload ×5（读类回包即证据） | runs/_exercises/ex_grid/h3-task111(6) | `payload` | 5 | 达标 |
| 101 | `project_read_resource` | both | read | 6 | 5 | 1 | `readback` | own_payload ×5（读类回包即证据） | runs/_exercises/ex_files/c1-task110(6) | `payload` | 5 | 达标 |
| 102 | `project_add_autoload` | both | add | 8 | 7 | 1 | `file_effect` | ok_file_effect_observed ×7 | runs/_exercises/ex_files/c1-task110(6) ; runs/_exercises/ex_scene/c23-task110(1) | `file_effect` | 7 | 达标 |
| 103 | `project_remove_autoload` | both | remove | 6 | 5 | 1 | `file_effect` | ok_file_effect_observed ×5 | runs/_exercises/ex_files/c1-task110(6) | `file_effect` | 5 | 达标 |
| 104 | `project_edit_resource` | both | edit | 6 | 5 | 1 | `file_effect` | ok_file_effect_observed ×5 | runs/_exercises/ex_files/c1-task110(6) | `file_effect` | 5 | 达标 |
| 105 | `project_create_resource` | both | create | 9 | 7 | 2 | `file_effect` | ok_file_effect_observed ×7 | runs/_exercises/ex_files/c1-task110(6) ; runs/_exercises/ex_3d/h1-task111(1) | `file_effect` | 7 | 达标 |
| 106 | `project_get_resource_preview` | both | get | 12 | 5 | 7 | `readback` | own_payload ×5（读类回包即证据） | runs/_exercises/ex_files/c1-task110(6) ; runs/_exercises/ex_files/c1b-task110(6) | `payload` | 5 | 达标 |
| 107 | `project_get_export_info` | both | get | 13 | 11 | 2 | `readback` | own_payload ×11（读类回包即证据） | runs/_exercises/ex_export/h8-task114(8) ; runs/_exercises/ex_export_np/h8n-task114(5) | `payload` | 11 | 达标 |
| 108 | `project_list_export_presets` | both | list | 14 | 12 | 2 | `readback` | own_payload ×12（读类回包即证据） | runs/_exercises/ex_export/h8-task114(9) ; runs/_exercises/ex_export_np/h8n-task114(5) | `payload` | 12 | 达标 |
| 109 | `project_read_shader` | both | read | 7 | 6 | 1 | `readback` | own_payload ×6（读类回包即证据） | runs/_exercises/ex_files/c1-task110(6) ; runs/_exercises/ex_files/c1-smoke(1) | `payload` | 6 | 达标 |
| 110 | `project_create_shader` | both | create | 12 | 11 | 1 | `file_effect` | ok_file_effect_observed ×11 | runs/_exercises/ex_files/c1-task110(6) ; runs/_exercises/ex_files/c1-smoke(1) | `file_effect` | 11 | 达标 |
| 111 | `project_edit_shader` | both | edit | 8 | 7 | 1 | `file_effect` | ok_file_effect_observed ×7 | runs/_exercises/ex_files/c1-task110(6) ; runs/_exercises/ex_write4/c4-final-task111(1) | `file_effect` | 7 | 达标 |
| 112 | `editor_set_shader_material` | editor | set | 24 | 3 | 6 | `pixel_effect` | ok_effect_observed ×3 | runs/_exercises/ex_write/c4-task111(6) ; runs/_exercises/ex_write3/c4c-task111(6) | `pixel_effect` | 3 | 达标 |
| 113 | `editor_set_shader_param` | editor | set | 24 | 1 | 14 | `pixel_effect` | ok_effect_observed ×1 | runs/_exercises/ex_write/c4-task111(6) ; runs/_exercises/ex_write3/c4c-task111(6) | `pixel_effect` | 1 | 达标 |
| 114 | `project_get_shader_params` | both | get | 6 | 5 | 1 | `readback` | own_payload ×5（读类回包即证据） | runs/_exercises/ex_files/c1-task110(6) | `payload` | 5 | 达标 |
| 115 | `editor_add_raycast` | editor | add | 36 | 16 | 11 | `pixel_effect` | ok_effect_observed ×16 | runs/_exercises/ex_write3/c4c-task111(7) ; runs/_exercises/ex_write4/c4-final-task111(7) | `pixel_effect` | 16 | 达标 |
| 116 | `editor_setup_collision_shape` | editor | setup | 31 | 9 | 11 | `pixel_effect` | ok_effect_observed ×9 | runs/_exercises/ex_write/c4-task111(7) ; runs/_exercises/ex_write3/c4c-task111(7) | `pixel_effect` | 9 | 达标 |
| 117 | `editor_set_physics_layers` | editor | set | 24 | 0 | 6 | `readback` | witness `editor_get_node_properties`@runs/_exercises/ex_write5/c4-v5-task111 seq=139 | runs/_exercises/ex_write/c4-task111(6) ; runs/_exercises/ex_write3/c4c-task111(6) | `editor_state` | 1 | 达标 |
| 118 | `editor_get_physics_layers` | editor | get | 12 | 6 | 6 | `readback` | own_payload ×6（读类回包即证据） | runs/_exercises/ex_scene/c23-task110(6) ; runs/_exercises/ex_scene2/c23-after-task110(6) | `payload` | 6 | 达标 |
| 119 | `editor_setup_physics_body` | editor | setup | 24 | 0 | 7 | `readback` | witness `editor_get_scene_tree`@runs/_exercises/ex_write5/c4-v5-task111 seq=132 | runs/_exercises/ex_write/c4-task111(6) ; runs/_exercises/ex_write3/c4c-task111(6) | `editor_state` | 1 | 达标 |
| 120 | `editor_get_collision_info` | editor | get | 12 | 8 | 4 | `readback` | own_payload ×8（读类回包即证据） | runs/_exercises/ex_scene/c23-task110(6) ; runs/_exercises/ex_scene2/c23-after-task110(6) | `payload` | 8 | 达标 |
| 121 | `editor_add_mesh_instance` | editor | add | 18 | 0 | 3 | `readback` | witness `editor_get_scene_tree`@runs/_exercises/ex_3d/h1b2-task115 seq=11 | runs/_exercises/ex_3d/h1-task111(6) ; runs/_exercises/ex_3d/h1b-task115(6) | `editor_state` | 1 | 达标 |
| 122 | `editor_setup_camera_3d` | editor | setup | 18 | 0 | 3 | `readback` | witness `editor_execute_gdscript`@runs/_exercises/ex_3d/h1b2-task115 seq=25 | runs/_exercises/ex_3d/h1-task111(6) ; runs/_exercises/ex_3d/h1b-task115(6) | `editor_state` | 1 | 达标 |
| 123 | `editor_setup_lighting` | editor | setup | 18 | 0 | 3 | `readback` | witness `editor_execute_gdscript`@runs/_exercises/ex_3d/h1b2-task115 seq=32 | runs/_exercises/ex_3d/h1-task111(6) ; runs/_exercises/ex_3d/h1b-task115(6) | `editor_state` | 1 | 达标 |
| 124 | `editor_set_material_3d` | editor | set | 18 | 0 | 5 | `readback` | witness `editor_execute_gdscript`@runs/_exercises/ex_3d/h1b2-task115 seq=18 | runs/_exercises/ex_3d/h1-task111(6) ; runs/_exercises/ex_3d/h1b-task115(6) | `editor_state` | 1 | 达标 |
| 125 | `editor_setup_world_environment` | editor | setup | 18 | 0 | 3 | `readback` | witness `editor_execute_gdscript`@runs/_exercises/ex_3d/h1b2-task115 seq=39 | runs/_exercises/ex_3d/h1-task111(6) ; runs/_exercises/ex_3d/h1b-task115(6) | `editor_state` | 1 | 达标 |
| 126 | `editor_add_gridmap` | editor | add | 12 | 0 | 2 | `readback` | witness `editor_get_scene_tree`@runs/_exercises/ex_grid/c6-task118 seq=9 | runs/_exercises/ex_grid/c6-task118(6) ; runs/_exercises/ex_grid/h3-task111(6) | `editor_state` | 1 | 达标 |
| 127 | `editor_add_audio_player` | editor | add | 6 | 0 | 1 | `readback` | witness `editor_get_node_properties`@runs/_exercises/ex_audio/h5-task113 seq=42 | runs/_exercises/ex_audio/h5-task113(6) | `editor_state` | 1 | 达标 |
| 128 | `editor_get_audio_info` | editor | get | 6 | 5 | 1 | `readback` | own_payload ×5（读类回包即证据） | runs/_exercises/ex_audio/h5-task113(6) | `payload` | 5 | 达标 |
| 129 | `editor_get_audio_bus_layout` | editor | get | 7 | 6 | 1 | `readback` | own_payload ×6（读类回包即证据） | runs/_exercises/ex_audio/h5-task113(7) | `payload` | 6 | 达标 |
| 130 | `editor_add_audio_bus` | editor | add | 7 | 0 | 2 | `readback` | witness `editor_get_audio_bus_layout`@runs/_exercises/ex_audio/h5-task113 seq=22 | runs/_exercises/ex_audio/h5-task113(7) | `editor_state` | 1 | 达标 |
| 131 | `editor_set_audio_bus_property` | editor | set | 8 | 0 | 3 | `readback` | witness `editor_get_audio_bus_layout`@runs/_exercises/ex_audio/h5-task113 seq=43 | runs/_exercises/ex_audio/h5-task113(8) | `editor_state` | 1 | 达标 |
| 132 | `editor_add_audio_bus_effect` | editor | add | 7 | 0 | 2 | `readback` | witness `editor_get_audio_bus_layout`@runs/_exercises/ex_audio/h5-task113 seq=22 | runs/_exercises/ex_audio/h5-task113(7) | `editor_state` | 1 | 达标 |
| 133 | `project_create_theme` | both | create | 12 | 11 | 1 | `file_effect` | ok_file_effect_observed ×11 | runs/_exercises/ex_files/c1-task110(6) ; runs/_exercises/ex_write/c4-task111(1) | `file_effect` | 11 | 达标 |
| 134 | `project_set_theme_color` | both | set | 6 | 5 | 1 | `file_effect` | ok_file_effect_observed ×5 | runs/_exercises/ex_files/c1-task110(6) | `file_effect` | 5 | 达标 |
| 135 | `project_set_theme_constant` | both | set | 6 | 5 | 1 | `file_effect` | ok_file_effect_observed ×5 | runs/_exercises/ex_files/c1-task110(6) | `file_effect` | 5 | 达标 |
| 136 | `project_set_theme_font_size` | both | set | 6 | 5 | 1 | `file_effect` | ok_file_effect_observed ×5 | runs/_exercises/ex_files/c1-task110(6) | `file_effect` | 5 | 达标 |
| 137 | `project_set_theme_stylebox` | both | set | 6 | 5 | 1 | `file_effect` | ok_file_effect_observed ×5 | runs/_exercises/ex_files/c1-task110(6) | `file_effect` | 5 | 达标 |
| 138 | `editor_set_control_theme` | editor | set | 30 | 0 | 6 | `readback` | witness `editor_execute_gdscript`@runs/_exercises/ex_write5/c4b-task115 seq=19 | runs/_exercises/ex_write/c4-task111(6) ; runs/_exercises/ex_write3/c4c-task111(6) | `editor_state` | 1 | 达标 |
| 139 | `project_get_theme_info` | both | get | 6 | 5 | 1 | `readback` | own_payload ×5（读类回包即证据） | runs/_exercises/ex_files/c1-task110(6) | `payload` | 5 | 达标 |
| 140 | `editor_create_animation_tree` | editor | create | 12 | 0 | 2 | `readback` | witness `editor_get_animation_tree_structure`@runs/_exercises/ex_anim2/h2b-task111 seq=88 | runs/_exercises/ex_anim/h2-task111(6) ; runs/_exercises/ex_anim2/h2b-task111(6) | `editor_state` | 1 | 达标 |
| 141 | `editor_get_animation_tree_structure` | editor | get | 12 | 10 | 2 | `readback` | own_payload ×10（读类回包即证据） | runs/_exercises/ex_anim/h2-task111(6) ; runs/_exercises/ex_anim2/h2b-task111(6) | `payload` | 10 | 达标 |
| 142 | `editor_add_state_machine_state` | editor | add | 18 | 0 | 2 | `readback` | witness `editor_get_animation_tree_structure`@runs/_exercises/ex_anim2/h2b-task111 seq=88 | runs/_exercises/ex_anim2/h2b-task111(12) ; runs/_exercises/ex_anim/h2-task111(6) | `editor_state` | 1 | 达标 |
| 143 | `editor_remove_state_machine_state` | editor | remove | 12 | 0 | 7 | `readback` | witness `editor_get_animation_tree_structure`@runs/_exercises/ex_anim2/h2b-task111 seq=91 | runs/_exercises/ex_anim/h2-task111(6) ; runs/_exercises/ex_anim2/h2b-task111(6) | `editor_state` | 1 | 达标 |
| 144 | `editor_add_state_machine_transition` | editor | add | 22 | 0 | 2 | `readback` | witness `editor_get_animation_tree_structure`@runs/_exercises/ex_anim2/h2b-task111 seq=88 | runs/_exercises/ex_anim/h2-task111(11) ; runs/_exercises/ex_anim2/h2b-task111(11) | `editor_state` | 1 | 达标 |
| 145 | `editor_remove_state_machine_transition` | editor | remove | 12 | 0 | 2 | `readback` | witness `editor_get_animation_tree_structure`@runs/_exercises/ex_anim2/h2b-task111 seq=88 | runs/_exercises/ex_anim/h2-task111(6) ; runs/_exercises/ex_anim2/h2b-task111(6) | `editor_state` | 1 | 达标 |
| 146 | `editor_set_blend_tree_node` | editor | set | 12 | 0 | 7 | `readback` | witness `editor_get_animation_tree_structure`@runs/_exercises/ex_anim2/h2b-task111 seq=88 | runs/_exercises/ex_anim/h2-task111(6) ; runs/_exercises/ex_anim2/h2b-task111(6) | `editor_state` | 1 | 达标 |
| 147 | `editor_set_animation_tree_parameter` | editor | set | 12 | 0 | 4 | `readback` | witness `editor_get_animation_tree_structure`@runs/_exercises/ex_anim2/h2b-task111 seq=88 | runs/_exercises/ex_anim/h2-task111(6) ; runs/_exercises/ex_anim2/h2b-task111(6) | `editor_state` | 1 | 达标 |
| 148 | `editor_setup_navigation_region` | editor | setup | 6 | 0 | 1 | `readback` | witness `editor_get_navigation_info`@runs/_exercises/ex_nav/h4-task113 seq=27 | runs/_exercises/ex_nav/h4-task113(6) | `editor_state` | 1 | 达标 |
| 149 | `editor_bake_navigation_mesh` | editor | bake | 6 | 1 | 1 | `pixel_effect` | ok_effect_observed ×1 | runs/_exercises/ex_nav/h4-task113(6) | `pixel_effect` | 1 | 达标 |
| 150 | `editor_setup_navigation_agent` | editor | setup | 6 | 0 | 1 | `readback` | witness `editor_get_navigation_info`@runs/_exercises/ex_nav/h4-task113 seq=27 | runs/_exercises/ex_nav/h4-task113(6) | `editor_state` | 1 | 达标 |
| 151 | `editor_set_navigation_layers` | editor | set | 7 | 0 | 2 | `readback` | witness `editor_get_navigation_info`@runs/_exercises/ex_nav/h4-task113 seq=27 | runs/_exercises/ex_nav/h4-task113(7) | `editor_state` | 1 | 达标 |
| 152 | `editor_get_navigation_info` | editor | get | 6 | 5 | 1 | `readback` | own_payload ×5（读类回包即证据） | runs/_exercises/ex_nav/h4-task113(6) | `payload` | 5 | 达标 |
| 153 | `editor_create_particles` | editor | create | 8 | 0 | 3 | `readback` | witness `editor_get_particle_info`@runs/_exercises/ex_particles/h6-task113 seq=34 | runs/_exercises/ex_particles/h6-task113(8) | `editor_state` | 1 | 达标 |
| 154 | `editor_set_particle_material` | editor | set | 8 | 5 | 3 | `pixel_effect` | ok_effect_observed ×5 | runs/_exercises/ex_particles/h6-task113(8) | `pixel_effect` | 5 | 达标 |
| 155 | `editor_set_particle_color_gradient` | editor | set | 9 | 6 | 3 | `pixel_effect` | ok_effect_observed ×6 | runs/_exercises/ex_particles/h6-task113(9) | `pixel_effect` | 6 | 达标 |
| 156 | `editor_set_particle_preset` | editor | set | 7 | 5 | 2 | `pixel_effect` | ok_effect_observed ×5 | runs/_exercises/ex_particles/h6-task113(7) | `pixel_effect` | 5 | 达标 |
| 157 | `editor_get_particle_info` | editor | get | 7 | 6 | 1 | `pixel_effect` | ok_effect_observed ×6 | runs/_exercises/ex_particles/h6-task113(7) | `payload` | 6 | 达标 |
| 158 | `project_find_unused_resources` | both | find | 6 | 5 | 1 | `readback` | own_payload ×5（读类回包即证据） | runs/_exercises/ex_files/c1-task110(6) | `payload` | 5 | 达标 |
| 159 | `editor_analyze_signal_flow` | editor | analyze | 12 | 8 | 4 | `readback` | own_payload ×8（读类回包即证据） | runs/_exercises/ex_scene/c23-task110(6) ; runs/_exercises/ex_scene2/c23-after-task110(6) | `payload` | 8 | 达标 |
| 160 | `project_analyze_scene_complexity` | both | analyze | 6 | 5 | 1 | `readback` | own_payload ×5（读类回包即证据） | runs/_exercises/ex_files/c1-task110(6) | `payload` | 5 | 达标 |
| 161 | `project_find_script_references` | both | find | 12 | 11 | 1 | `readback` | own_payload ×11（读类回包即证据） | runs/_exercises/ex_files/c1-task110(6) ; runs/_exercises/ex_files/c1b-task110(6) | `payload` | 11 | 达标 |
| 162 | `project_detect_circular_dependencies` | both | detect | 6 | 5 | 1 | `readback` | own_payload ×5（读类回包即证据） | runs/_exercises/ex_files/c1-task110(6) | `payload` | 5 | 达标 |
| 163 | `project_get_statistics` | both | get | 7 | 5 | 2 | `readback` | own_payload ×5（读类回包即证据） | runs/_exercises/ex_files/c1-task110(6) ; runs/_exercises/ex_files/c1-smoke(1) | `payload` | 5 | 达标 |
| 164 | `running_game_run_test_scenario` | game | run | 185 | 131 | 0 | `pixel_effect` | ok_effect_observed ×1 | runs/snake/snake-clean-task097(8) ; runs/snake/snake-task093(8) | `pixel_effect` | 1 | 计数达标缺证据 |
| 165 | `running_game_assert_node_state` | game | assert | 2903 | 2719 | 115 | `file_effect` | ok_file_effect_observed ×2788 | runs/lunarlander/ll-task104-r1(149) ; runs/bomberman/bomb-task101-r4(144) | `payload` | 2719 | 达标 |
| 166 | `running_game_assert_screen_text` | game | assert | 80 | 65 | 0 | `file_effect` | ok_file_effect_observed ×80 | runs/asteroids/ast-task098-r1(2) ; runs/asteroids/ast-task098-r2(2) | `payload` | 65 | 计数达标缺证据 |
| 167 | `running_game_run_stress_test` | game | run | 27 | 5 | 0 | `pixel_effect` | ok_effect_observed ×5 | runs/breakout/breakout-clean-task097(1) ; runs/breakout/breakout-task093(1) | `pixel_effect` | 5 | 计数达标缺证据 |
| 168 | `editor_get_test_report` | editor | get | 6 | 5 | 1 | `readback` | own_payload ×5（读类回包即证据） | runs/_exercises/ex_editor/h7-task115(6) | `payload` | 5 | 达标 |
| 169 | `os_list_android_devices` | both | list | 6 | 5 | 1 | `readback` | own_payload ×5（读类回包即证据） | runs/_exercises/ex_grid/c7-task118(6) | `payload` | 5 | 达标 |
| 170 | `project_get_android_preset_info` | both | get | 6 | 0 | 6 | `count_only` | - | runs/_exercises/ex_grid/c7-task118(6) | `payload` | 0 | 计数达标缺证据 |
| 171 | `os_deploy_to_android_device` | both | deploy | 6 | 0 | 6 | `count_only` | - | runs/_exercises/ex_grid/c7-task118(6) | `payload` | 0 | 计数达标缺证据 |
| 172 | `project_build_csharp` | both | build | 67 | 63 | 0 | `file_effect` | ok_file_effect_observed ×63 | runs/_exercises/ex_files/c1b-task110(1) ; runs/_exercises/ex_grid/c6-task118(1) | `file_effect` | 63 | 计数达标缺证据 |
| 173 | `project_write_text_file` | both | write | 7 | 6 | 1 | `file_effect` | ok_file_effect_observed ×6 | runs/_exercises/ex_files/c1-task110(6) ; runs/_exercises/ex_files/c1-smoke(1) | `file_effect` | 6 | 达标 |
| 174 | `project_validate_scripts` | both | validate | 84 | 80 | 0 | `readback` | own_payload ×80（读类回包即证据） | runs/breakout/breakout-clean-task097(2) ; runs/breakout/breakout-task093(2) | `payload` | 80 | 计数达标缺证据 |
| 175 | `editor_set_node_script_batch` | editor | set | 56 | 0 | 1 | `readback` | witness `editor_execute_gdscript`@runs/_exercises/ex_grid/c6-task118 seq=16 | runs/_exercises/ex_grid/c6-task118(6) ; runs/breakout/breakout-clean-task097(2) | `editor_state` | 1 | 达标 |
| 176 | `editor_set_node_property_updates` | editor | set | 30 | 3 | 7 | `pixel_effect` | ok_effect_observed ×3 | runs/_exercises/ex_write/c4-task111(6) ; runs/_exercises/ex_write2/c4b-task111(6) | `pixel_effect` | 3 | 达标 |
| 177 | `project_read_text_file` | both | read | 86 | 85 | 1 | `readback` | own_payload ×85（读类回包即证据） | runs/_exercises/ex_files/c1-task110(6) ; runs/pong/d3-after(3) | `payload` | 85 | 达标 |

## 2. 分桶明细

### 2.1 `>=5` 次（172 条）

| tool | scope | 累计 | 有效 | 边界 | 档位 | 状态 | 证据 |
|---|---|---|---|---|---|---|---|
| `project_get_info` | both | 8 | 6 | 2 | `readback` | 达标 | runs/_exercises/ex_files/c1-task110(6) ; runs/_exercises/ex_files/c1-smoke(2) |
| `project_get_filesystem_tree` | both | 7 | 6 | 1 | `readback` | 达标 | runs/_exercises/ex_files/c1-task110(6) ; runs/_exercises/ex_editor/h7-task115(1) |
| `project_search_file_names` | both | 12 | 11 | 1 | `readback` | 达标 | runs/_exercises/ex_files/c1-task110(6) ; runs/_exercises/ex_files/c1b-task110(6) |
| `project_search_file_contents` | both | 12 | 11 | 1 | `readback` | 达标 | runs/_exercises/ex_files/c1-task110(6) ; runs/_exercises/ex_files/c1b-task110(6) |
| `project_get_settings` | both | 8 | 7 | 1 | `readback` | 达标 | runs/_exercises/ex_files/c1-task110(6) ; runs/_exercises/ex_editor/h7-task115(1) ; runs/_exercises/ex_files/c1-smoke(1) |
| `project_set_setting` | both | 6 | 5 | 1 | `file_effect` | 达标 | runs/_exercises/ex_files/c1-task110(6) |
| `project_convert_uid_to_path` | both | 8 | 6 | 2 | `readback` | 达标 | runs/_exercises/ex_files/c1-task110(6) ; runs/_exercises/ex_files/c1-smoke(2) |
| `project_convert_path_to_uid` | both | 6 | 5 | 1 | `readback` | 达标 | runs/_exercises/ex_files/c1-task110(6) |
| `editor_get_scene_tree` | editor | 113 | 109 | 4 | `readback` | 达标 | runs/_exercises/ex_write5/c4-v5-task111(7) ; runs/_exercises/ex_scene/c23-task110(6) ; runs/_exercises/ex_scene2/c23-after-task110(6) |
| `project_read_scene_file_content` | both | 6 | 5 | 1 | `readback` | 达标 | runs/_exercises/ex_files/c1-task110(6) |
| `editor_open_scene` | editor | 86 | 9 | 0 | `pixel_effect` | 计数达标缺证据 | runs/breakout/breakout-clean-task097(2) ; runs/pong/pong-clean-task097(2) ; runs/snake/snake-clean-task097(2) |
| `project_delete_scene_file` | both | 10 | 8 | 2 | `file_effect` | 达标 | runs/_exercises/ex_files/c1-task110(6) ; runs/pong/d3-after(2) ; runs/pong/d3-after-r2(2) |
| `editor_add_scene_instance` | editor | 30 | 0 | 5 | `readback` | 达标 | runs/_exercises/ex_write/c4-task111(6) ; runs/_exercises/ex_write2/c4b-task111(6) ; runs/_exercises/ex_write3/c4c-task111(6) |
| `project_get_scene_exports` | both | 6 | 5 | 1 | `readback` | 达标 | runs/_exercises/ex_files/c1-task110(6) |
| `editor_play_scene` | editor | 7 | 0 | 2 | `readback` | 达标 | runs/_exercises/ex_editor/h7-task115(7) |
| `editor_stop_scene` | editor | 7 | 0 | 1 | `readback` | 达标 | runs/_exercises/ex_editor/h7-task115(7) |
| `editor_save_scene` | editor | 123 | 77 | 0 | `file_effect` | 计数达标缺证据 | runs/lunarlander/ll-task104-r1(3) ; runs/missilecommand/mc-task103-r1(3) ; runs/missilecommand/mc-task103-r2(3) |
| `project_create_scene_file` | both | 20 | 18 | 2 | `file_effect` | 达标 | runs/_exercises/ex_files/c1-task110(6) ; runs/_exercises/ex_files/c1c-task110(6) ; runs/_exercises/ex_write/c4-task111(1) |
| `editor_add_node` | editor | 36 | 10 | 5 | `pixel_effect` | 达标 | runs/_exercises/ex_write/c4-task111(6) ; runs/_exercises/ex_write2/c4b-task111(6) ; runs/_exercises/ex_write3/c4c-task111(6) |
| `editor_delete_node` | editor | 65 | 5 | 0 | `pixel_effect` | 计数达标缺证据 | runs/snake/snake-clean-task097(37) ; runs/breakout/breakout-clean-task097(20) ; runs/pong/pong-clean-task097(8) |
| `editor_rename_node` | editor | 30 | 0 | 7 | `readback` | 达标 | runs/_exercises/ex_write/c4-task111(6) ; runs/_exercises/ex_write2/c4b-task111(6) ; runs/_exercises/ex_write3/c4c-task111(6) |
| `editor_set_node_property` | editor | 41 | 12 | 0 | `pixel_effect` | 计数达标缺证据 | runs/pong/pong-clean-task097(3) ; runs/pong/pong-control-task093(3) ; runs/pong/pong-run1(3) |
| `editor_get_node_properties` | editor | 74 | 62 | 12 | `readback` | 达标 | runs/breakout/breakout-clean-task097(10) ; runs/pong/pong-clean-task097(9) ; runs/snake/snake-clean-task097(9) |
| `editor_duplicate_node` | editor | 30 | 5 | 7 | `pixel_effect` | 达标 | runs/_exercises/ex_write/c4-task111(6) ; runs/_exercises/ex_write2/c4b-task111(6) ; runs/_exercises/ex_write3/c4c-task111(6) |
| `editor_connect_signal` | editor | 45 | 0 | 7 | `readback` | 达标 | runs/_exercises/ex_grid/c6-task118(6) ; runs/_exercises/ex_write/c4-task111(6) ; runs/_exercises/ex_write2/c4b-task111(6) |
| `editor_disconnect_signal` | editor | 6 | 0 | 1 | `readback` | 达标 | runs/_exercises/ex_write6/c5-task111(6) |
| `editor_reparent_node` | editor | 30 | 3 | 14 | `pixel_effect` | 达标 | runs/_exercises/ex_write/c4-task111(6) ; runs/_exercises/ex_write2/c4b-task111(6) ; runs/_exercises/ex_write3/c4c-task111(6) |
| `editor_add_resource_to_node_property` | editor | 33 | 12 | 20 | `pixel_effect` | 达标 | runs/_exercises/ex_write4/c4-final-task111(7) ; runs/_exercises/ex_write5/c4-v5-task111(7) ; runs/_exercises/ex_write/c4-task111(6) |
| `editor_set_anchor_preset` | editor | 24 | 5 | 5 | `pixel_effect` | 达标 | runs/_exercises/ex_write/c4-task111(6) ; runs/_exercises/ex_write3/c4c-task111(6) ; runs/_exercises/ex_write4/c4-final-task111(6) |
| `editor_get_node_groups` | editor | 13 | 11 | 2 | `readback` | 达标 | runs/_exercises/ex_scene/c23-task110(6) ; runs/_exercises/ex_scene2/c23-after-task110(6) ; runs/_exercises/ex_write5/c4-v5-task111(1) |
| `editor_set_node_groups` | editor | 36 | 0 | 11 | `readback` | 达标 | runs/_exercises/ex_write/c4-task111(7) ; runs/_exercises/ex_write3/c4c-task111(7) ; runs/_exercises/ex_write4/c4-final-task111(7) |
| `editor_find_nodes_in_group` | editor | 12 | 10 | 2 | `readback` | 达标 | runs/_exercises/ex_scene/c23-task110(6) ; runs/_exercises/ex_scene2/c23-after-task110(6) |
| `editor_get_selection` | editor | 17 | 15 | 2 | `readback` | 达标 | runs/_exercises/ex_scene/c23-task110(6) ; runs/_exercises/ex_scene2/c23-after-task110(6) ; runs/_exercises/ex_editor/h7-task115(5) |
| `editor_set_node_selection` | editor | 9 | 0 | 1 | `readback` | 达标 | runs/_exercises/ex_editor/h7-task115(9) |
| `editor_remove_node_selection` | editor | 6 | 0 | 1 | `readback` | 达标 | runs/_exercises/ex_editor/h7-task115(6) |
| `editor_execute_gdscript` | editor | 26 | 24 | 2 | `readback` | 达标 | runs/_exercises/ex_scene/c23-task110(6) ; runs/_exercises/ex_scene2/c23-after-task110(6) ; runs/_exercises/ex_3d/h1b-task115(4) |
| `editor_get_errors` | editor | 50 | 50 | 0 | `readback` | 计数达标缺证据 | runs/asteroids/ast-task098-r1(1) ; runs/asteroids/ast-task098-r2(1) ; runs/breakout/breakout-clean-task097(1) |
| `editor_get_output_log` | editor | 38 | 34 | 4 | `readback` | 达标 | runs/_exercises/ex_scene/c23-task110(6) ; runs/_exercises/ex_scene2/c23-after-task110(6) ; runs/_exercises/ex_write/c4-task111(6) |
| `editor_capture_screenshot` | editor | 25 | 25 | 0 | `file_effect` | 计数达标缺证据 | runs/breakout/breakout-clean-task097(1) ; runs/breakout/breakout-task093(1) ; runs/breakout/breakout-task093-r2(1) |
| `running_game_capture_screenshot` | game | 298 | 298 | 0 | `pixel_effect` | 计数达标缺证据 | runs/match3/m3-task102-r1(7) ; runs/match3/m3-task102-r2(7) ; runs/match3/m3-task102-r3(7) |
| `editor_remove_output_log` | editor | 6 | 0 | 1 | `readback` | 达标 | runs/_exercises/ex_editor/h7-task115(6) |
| `editor_reload_plugin` | editor | 6 | 0 | 1 | `readback` | 达标 | runs/_exercises/ex_editor/h7-task115(6) |
| `editor_rescan_project_filesystem` | editor | 6 | 0 | 1 | `readback` | 达标 | runs/_exercises/ex_editor/h7-task115(6) |
| `editor_get_node_signals` | editor | 12 | 10 | 2 | `readback` | 达标 | runs/_exercises/ex_scene/c23-task110(6) ; runs/_exercises/ex_scene2/c23-after-task110(6) |
| `editor_analyze_screenshot_diff` | editor | 8 | 5 | 3 | `readback` | 达标 | runs/_exercises/ex_editor/h7-task115(8) |
| `editor_set_auto_dismiss_dialogs` | editor | 7 | 0 | 7 | `count_only` | 计数达标缺证据 | runs/_exercises/ex_editor/h7-task115(7) |
| `editor_get_viewport_3d_camera` | editor | 6 | 5 | 1 | `readback` | 达标 | runs/_exercises/ex_3d/h1-task111(6) |
| `editor_set_viewport_3d_camera` | editor | 6 | 0 | 1 | `readback` | 达标 | runs/_exercises/ex_3d/h1-task111(6) |
| `running_game_get_scene_tree` | game | 123 | 123 | 0 | `pixel_effect` | 计数达标缺证据 | runs/asteroids/ast-task098-r1(2) ; runs/asteroids/ast-task098-r2(2) ; runs/bomberman/bomb-task101-r1(2) |
| `running_game_get_node_properties` | game | 58 | 56 | 2 | `pixel_effect` | 达标 | runs/_exercises/ex_scene/c23-task110(6) ; runs/_exercises/ex_scene2/c23-after-task110(6) ; runs/_exercises/ex_rec/h9-task113(5) |
| `running_game_set_node_property` | game | 49 | 28 | 2 | `pixel_effect` | 达标 | runs/pong/pong-clean-task097(5) ; runs/pong/pong-control-task093(5) ; runs/pong/pong-run1(5) |
| `running_game_capture_frames` | game | 36 | 30 | 6 | `readback` | 达标 | runs/_exercises/ex_scene/c23-task110(6) ; runs/_exercises/ex_scene2/c23-after-task110(6) ; runs/_exercises/ex_write/c4-task111(6) |
| `running_game_get_node_property_samples` | game | 122 | 122 | 0 | `pixel_effect` | 计数达标缺证据 | runs/spaceinvaders/si-task097-r1(5) ; runs/tetris/tetris-task096(4) ; runs/tetris/tetris-task096-r2(4) |
| `running_game_execute_gdscript` | game | 1626 | 1593 | 33 | `pixel_effect` | 达标 | runs/rtype/rt-task104-r1(98) ; runs/rtype/rt-task104-r2(98) ; runs/bomberman/bomb-task101-r2(61) |
| `running_game_create_input_recording` | game | 7 | 0 | 1 | `readback` | 达标 | runs/_exercises/ex_rec/h9-task113(7) |
| `running_game_stop_input_recording` | game | 7 | 0 | 0 | `readback` | 计数达标缺证据 | runs/_exercises/ex_rec/h9-task113(7) |
| `running_game_play_input_recording` | game | 7 | 6 | 1 | `pixel_effect` | 达标 | runs/_exercises/ex_rec/h9-task113(7) |
| `running_game_find_nodes_by_script` | game | 12 | 10 | 2 | `readback` | 达标 | runs/_exercises/ex_scene/c23-task110(6) ; runs/_exercises/ex_scene2/c23-after-task110(6) |
| `running_game_get_autoload_node` | game | 12 | 10 | 2 | `readback` | 达标 | runs/_exercises/ex_scene/c23-task110(6) ; runs/_exercises/ex_scene2/c23-after-task110(6) |
| `running_game_get_node_properties_batch` | game | 36 | 32 | 4 | `readback` | 达标 | runs/_exercises/ex_scene/c23-task110(6) ; runs/_exercises/ex_scene2/c23-after-task110(6) ; runs/_exercises/ex_write/c4-task111(6) |
| `running_game_find_ui_elements` | game | 12 | 10 | 2 | `readback` | 达标 | runs/_exercises/ex_scene/c23-task110(6) ; runs/_exercises/ex_scene2/c23-after-task110(6) |
| `running_game_simulate_button_click_by_text` | game | 12 | 2 | 2 | `pixel_effect` | 达标 | runs/_exercises/ex_scene/c23-task110(6) ; runs/_exercises/ex_scene2/c23-after-task110(6) |
| `running_game_find_node_when_available` | game | 14 | 5 | 9 | `readback` | 达标 | runs/_exercises/ex_grid/c6-task118(6) ; runs/breakout/breakout-clean-task097(1) ; runs/breakout/breakout-task093(1) |
| `running_game_find_nearby_nodes` | game | 12 | 10 | 2 | `readback` | 达标 | runs/_exercises/ex_scene/c23-task110(6) ; runs/_exercises/ex_scene2/c23-after-task110(6) |
| `running_game_move_player_to_target` | game | 6 | 5 | 1 | `pixel_effect` | 达标 | runs/_exercises/ex_nav/h4-task113(6) |
| `running_game_capture_signal_emissions` | game | 36 | 26 | 10 | `readback` | 达标 | runs/_exercises/ex_scene/c23-task110(6) ; runs/_exercises/ex_scene2/c23-after-task110(6) ; runs/_exercises/ex_write/c4-task111(6) |
| `editor_get_performance_monitors` | editor | 12 | 10 | 2 | `readback` | 达标 | runs/_exercises/ex_scene/c23-task110(6) ; runs/_exercises/ex_scene2/c23-after-task110(6) |
| `project_list_scripts` | both | 6 | 5 | 1 | `readback` | 达标 | runs/_exercises/ex_files/c1-task110(6) |
| `project_read_script` | both | 8 | 6 | 2 | `readback` | 达标 | runs/_exercises/ex_files/c1-task110(6) ; runs/_exercises/ex_files/c1-smoke(2) |
| `project_create_script` | both | 77 | 44 | 1 | `file_effect` | 达标 | runs/_exercises/ex_files/c1-task110(6) ; runs/_exercises/ex_files/c1b-task110(6) ; runs/_exercises/ex_files/c1c-task110(6) |
| `project_edit_script` | both | 60 | 52 | 0 | `file_effect` | 计数达标缺证据 | runs/tetris/tetris-task096-r2(2) ; runs/asteroids/ast-task098-r1(1) ; runs/asteroids/ast-task098-r2(1) |
| `editor_set_node_script` | editor | 36 | 0 | 6 | `readback` | 达标 | runs/_exercises/ex_write/c4-task111(6) ; runs/_exercises/ex_write2/c4b-task111(6) ; runs/_exercises/ex_write3/c4c-task111(6) |
| `editor_get_open_scripts` | editor | 12 | 10 | 2 | `readback` | 达标 | runs/_exercises/ex_scene/c23-task110(6) ; runs/_exercises/ex_scene2/c23-after-task110(6) |
| `project_validate_script` | both | 18 | 3 | 15 | `readback` | 达标 | runs/_exercises/ex_files/c1-task110(6) ; runs/_exercises/ex_files/c1b-task110(6) ; runs/_exercises/ex_files/c1c-task110(6) |
| `editor_get_input_actions` | editor | 12 | 10 | 2 | `readback` | 达标 | runs/_exercises/ex_scene/c23-task110(6) ; runs/_exercises/ex_scene2/c23-after-task110(6) |
| `editor_add_input_action` | editor | 189 | 122 | 0 | `file_effect` | 计数达标缺证据 | runs/pong/pong-clean-task097(5) ; runs/pong/pong-control-task093(5) ; runs/pong/pong-run1(5) |
| `editor_find_nodes_by_type` | editor | 12 | 10 | 2 | `readback` | 达标 | runs/_exercises/ex_scene/c23-task110(6) ; runs/_exercises/ex_scene2/c23-after-task110(6) |
| `editor_set_node_property_batch` | editor | 30 | 15 | 5 | `pixel_effect` | 达标 | runs/_exercises/ex_write/c4-task111(6) ; runs/_exercises/ex_write2/c4b-task111(6) ; runs/_exercises/ex_write3/c4c-task111(6) |
| `editor_list_signal_connections` | editor | 14 | 10 | 4 | `readback` | 达标 | runs/_exercises/ex_scene/c23-task110(6) ; runs/_exercises/ex_scene2/c23-after-task110(6) ; runs/_exercises/ex_grid/c6-task118(1) |
| `editor_add_nodes_batch` | editor | 106 | 47 | 42 | `pixel_effect` | 达标 | runs/pong/d3-after(3) ; runs/pong/d3-after-r2(3) ; runs/asteroids/ast-task098-r1(2) |
| `project_find_files_referencing_symbol` | both | 12 | 11 | 1 | `readback` | 达标 | runs/_exercises/ex_files/c1-task110(6) ; runs/_exercises/ex_files/c1b-task110(6) |
| `project_get_scene_dependencies` | both | 6 | 5 | 1 | `readback` | 达标 | runs/_exercises/ex_files/c1-task110(6) |
| `project_set_node_property_across_scenes` | both | 18 | 1 | 1 | `file_effect` | 达标 | runs/_exercises/ex_files/c1-task110(6) ; runs/_exercises/ex_files/c1b-task110(6) ; runs/_exercises/ex_files/c1c-task110(6) |
| `editor_list_animations` | editor | 15 | 13 | 2 | `readback` | 达标 | runs/_exercises/ex_anim/h2-task111(6) ; runs/_exercises/ex_anim2/h2b-task111(6) ; runs/_exercises/ex_anim2/h2c-task115(3) |
| `editor_create_animation` | editor | 23 | 0 | 2 | `readback` | 达标 | runs/_exercises/ex_anim/h2-task111(9) ; runs/_exercises/ex_anim2/h2b-task111(9) ; runs/_exercises/ex_anim2/h2c-task115(5) |
| `editor_add_animation_track` | editor | 12 | 0 | 2 | `readback` | 达标 | runs/_exercises/ex_anim/h2-task111(6) ; runs/_exercises/ex_anim2/h2b-task111(6) |
| `editor_set_animation_keyframe` | editor | 12 | 0 | 2 | `readback` | 达标 | runs/_exercises/ex_anim/h2-task111(6) ; runs/_exercises/ex_anim2/h2b-task111(6) |
| `editor_get_animation_info` | editor | 12 | 10 | 2 | `readback` | 达标 | runs/_exercises/ex_anim/h2-task111(6) ; runs/_exercises/ex_anim2/h2b-task111(6) |
| `editor_remove_animation` | editor | 18 | 0 | 3 | `readback` | 达标 | runs/_exercises/ex_anim/h2-task111(6) ; runs/_exercises/ex_anim2/h2b-task111(6) ; runs/_exercises/ex_anim2/h2c-task115(6) |
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
| `project_create_resource` | both | 9 | 7 | 2 | `file_effect` | 达标 | runs/_exercises/ex_files/c1-task110(6) ; runs/_exercises/ex_3d/h1-task111(1) ; runs/_exercises/ex_3d/h1b-task115(1) |
| `project_get_resource_preview` | both | 12 | 5 | 7 | `readback` | 达标 | runs/_exercises/ex_files/c1-task110(6) ; runs/_exercises/ex_files/c1b-task110(6) |
| `project_get_export_info` | both | 13 | 11 | 2 | `readback` | 达标 | runs/_exercises/ex_export/h8-task114(8) ; runs/_exercises/ex_export_np/h8n-task114(5) |
| `project_list_export_presets` | both | 14 | 12 | 2 | `readback` | 达标 | runs/_exercises/ex_export/h8-task114(9) ; runs/_exercises/ex_export_np/h8n-task114(5) |
| `project_read_shader` | both | 7 | 6 | 1 | `readback` | 达标 | runs/_exercises/ex_files/c1-task110(6) ; runs/_exercises/ex_files/c1-smoke(1) |
| `project_create_shader` | both | 12 | 11 | 1 | `file_effect` | 达标 | runs/_exercises/ex_files/c1-task110(6) ; runs/_exercises/ex_files/c1-smoke(1) ; runs/_exercises/ex_write/c4-task111(1) |
| `project_edit_shader` | both | 8 | 7 | 1 | `file_effect` | 达标 | runs/_exercises/ex_files/c1-task110(6) ; runs/_exercises/ex_write4/c4-final-task111(1) ; runs/_exercises/ex_write5/c4-v5-task111(1) |
| `editor_set_shader_material` | editor | 24 | 3 | 6 | `pixel_effect` | 达标 | runs/_exercises/ex_write/c4-task111(6) ; runs/_exercises/ex_write3/c4c-task111(6) ; runs/_exercises/ex_write4/c4-final-task111(6) |
| `editor_set_shader_param` | editor | 24 | 1 | 14 | `pixel_effect` | 达标 | runs/_exercises/ex_write/c4-task111(6) ; runs/_exercises/ex_write3/c4c-task111(6) ; runs/_exercises/ex_write4/c4-final-task111(6) |
| `project_get_shader_params` | both | 6 | 5 | 1 | `readback` | 达标 | runs/_exercises/ex_files/c1-task110(6) |
| `editor_add_raycast` | editor | 36 | 16 | 11 | `pixel_effect` | 达标 | runs/_exercises/ex_write3/c4c-task111(7) ; runs/_exercises/ex_write4/c4-final-task111(7) ; runs/_exercises/ex_write5/c4-v5-task111(7) |
| `editor_setup_collision_shape` | editor | 31 | 9 | 11 | `pixel_effect` | 达标 | runs/_exercises/ex_write/c4-task111(7) ; runs/_exercises/ex_write3/c4c-task111(7) ; runs/_exercises/ex_write4/c4-final-task111(7) |
| `editor_set_physics_layers` | editor | 24 | 0 | 6 | `readback` | 达标 | runs/_exercises/ex_write/c4-task111(6) ; runs/_exercises/ex_write3/c4c-task111(6) ; runs/_exercises/ex_write4/c4-final-task111(6) |
| `editor_get_physics_layers` | editor | 12 | 6 | 6 | `readback` | 达标 | runs/_exercises/ex_scene/c23-task110(6) ; runs/_exercises/ex_scene2/c23-after-task110(6) |
| `editor_setup_physics_body` | editor | 24 | 0 | 7 | `readback` | 达标 | runs/_exercises/ex_write/c4-task111(6) ; runs/_exercises/ex_write3/c4c-task111(6) ; runs/_exercises/ex_write4/c4-final-task111(6) |
| `editor_get_collision_info` | editor | 12 | 8 | 4 | `readback` | 达标 | runs/_exercises/ex_scene/c23-task110(6) ; runs/_exercises/ex_scene2/c23-after-task110(6) |
| `editor_add_mesh_instance` | editor | 18 | 0 | 3 | `readback` | 达标 | runs/_exercises/ex_3d/h1-task111(6) ; runs/_exercises/ex_3d/h1b-task115(6) ; runs/_exercises/ex_3d/h1b2-task115(6) |
| `editor_setup_camera_3d` | editor | 18 | 0 | 3 | `readback` | 达标 | runs/_exercises/ex_3d/h1-task111(6) ; runs/_exercises/ex_3d/h1b-task115(6) ; runs/_exercises/ex_3d/h1b2-task115(6) |
| `editor_setup_lighting` | editor | 18 | 0 | 3 | `readback` | 达标 | runs/_exercises/ex_3d/h1-task111(6) ; runs/_exercises/ex_3d/h1b-task115(6) ; runs/_exercises/ex_3d/h1b2-task115(6) |
| `editor_set_material_3d` | editor | 18 | 0 | 5 | `readback` | 达标 | runs/_exercises/ex_3d/h1-task111(6) ; runs/_exercises/ex_3d/h1b-task115(6) ; runs/_exercises/ex_3d/h1b2-task115(6) |
| `editor_setup_world_environment` | editor | 18 | 0 | 3 | `readback` | 达标 | runs/_exercises/ex_3d/h1-task111(6) ; runs/_exercises/ex_3d/h1b-task115(6) ; runs/_exercises/ex_3d/h1b2-task115(6) |
| `editor_add_gridmap` | editor | 12 | 0 | 2 | `readback` | 达标 | runs/_exercises/ex_grid/c6-task118(6) ; runs/_exercises/ex_grid/h3-task111(6) |
| `editor_add_audio_player` | editor | 6 | 0 | 1 | `readback` | 达标 | runs/_exercises/ex_audio/h5-task113(6) |
| `editor_get_audio_info` | editor | 6 | 5 | 1 | `readback` | 达标 | runs/_exercises/ex_audio/h5-task113(6) |
| `editor_get_audio_bus_layout` | editor | 7 | 6 | 1 | `readback` | 达标 | runs/_exercises/ex_audio/h5-task113(7) |
| `editor_add_audio_bus` | editor | 7 | 0 | 2 | `readback` | 达标 | runs/_exercises/ex_audio/h5-task113(7) |
| `editor_set_audio_bus_property` | editor | 8 | 0 | 3 | `readback` | 达标 | runs/_exercises/ex_audio/h5-task113(8) |
| `editor_add_audio_bus_effect` | editor | 7 | 0 | 2 | `readback` | 达标 | runs/_exercises/ex_audio/h5-task113(7) |
| `project_create_theme` | both | 12 | 11 | 1 | `file_effect` | 达标 | runs/_exercises/ex_files/c1-task110(6) ; runs/_exercises/ex_write/c4-task111(1) ; runs/_exercises/ex_write2/c4b-task111(1) |
| `project_set_theme_color` | both | 6 | 5 | 1 | `file_effect` | 达标 | runs/_exercises/ex_files/c1-task110(6) |
| `project_set_theme_constant` | both | 6 | 5 | 1 | `file_effect` | 达标 | runs/_exercises/ex_files/c1-task110(6) |
| `project_set_theme_font_size` | both | 6 | 5 | 1 | `file_effect` | 达标 | runs/_exercises/ex_files/c1-task110(6) |
| `project_set_theme_stylebox` | both | 6 | 5 | 1 | `file_effect` | 达标 | runs/_exercises/ex_files/c1-task110(6) |
| `editor_set_control_theme` | editor | 30 | 0 | 6 | `readback` | 达标 | runs/_exercises/ex_write/c4-task111(6) ; runs/_exercises/ex_write3/c4c-task111(6) ; runs/_exercises/ex_write4/c4-final-task111(6) |
| `project_get_theme_info` | both | 6 | 5 | 1 | `readback` | 达标 | runs/_exercises/ex_files/c1-task110(6) |
| `editor_create_animation_tree` | editor | 12 | 0 | 2 | `readback` | 达标 | runs/_exercises/ex_anim/h2-task111(6) ; runs/_exercises/ex_anim2/h2b-task111(6) |
| `editor_get_animation_tree_structure` | editor | 12 | 10 | 2 | `readback` | 达标 | runs/_exercises/ex_anim/h2-task111(6) ; runs/_exercises/ex_anim2/h2b-task111(6) |
| `editor_add_state_machine_state` | editor | 18 | 0 | 2 | `readback` | 达标 | runs/_exercises/ex_anim2/h2b-task111(12) ; runs/_exercises/ex_anim/h2-task111(6) |
| `editor_remove_state_machine_state` | editor | 12 | 0 | 7 | `readback` | 达标 | runs/_exercises/ex_anim/h2-task111(6) ; runs/_exercises/ex_anim2/h2b-task111(6) |
| `editor_add_state_machine_transition` | editor | 22 | 0 | 2 | `readback` | 达标 | runs/_exercises/ex_anim/h2-task111(11) ; runs/_exercises/ex_anim2/h2b-task111(11) |
| `editor_remove_state_machine_transition` | editor | 12 | 0 | 2 | `readback` | 达标 | runs/_exercises/ex_anim/h2-task111(6) ; runs/_exercises/ex_anim2/h2b-task111(6) |
| `editor_set_blend_tree_node` | editor | 12 | 0 | 7 | `readback` | 达标 | runs/_exercises/ex_anim/h2-task111(6) ; runs/_exercises/ex_anim2/h2b-task111(6) |
| `editor_set_animation_tree_parameter` | editor | 12 | 0 | 4 | `readback` | 达标 | runs/_exercises/ex_anim/h2-task111(6) ; runs/_exercises/ex_anim2/h2b-task111(6) |
| `editor_setup_navigation_region` | editor | 6 | 0 | 1 | `readback` | 达标 | runs/_exercises/ex_nav/h4-task113(6) |
| `editor_bake_navigation_mesh` | editor | 6 | 1 | 1 | `pixel_effect` | 达标 | runs/_exercises/ex_nav/h4-task113(6) |
| `editor_setup_navigation_agent` | editor | 6 | 0 | 1 | `readback` | 达标 | runs/_exercises/ex_nav/h4-task113(6) |
| `editor_set_navigation_layers` | editor | 7 | 0 | 2 | `readback` | 达标 | runs/_exercises/ex_nav/h4-task113(7) |
| `editor_get_navigation_info` | editor | 6 | 5 | 1 | `readback` | 达标 | runs/_exercises/ex_nav/h4-task113(6) |
| `editor_create_particles` | editor | 8 | 0 | 3 | `readback` | 达标 | runs/_exercises/ex_particles/h6-task113(8) |
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
| `editor_get_test_report` | editor | 6 | 5 | 1 | `readback` | 达标 | runs/_exercises/ex_editor/h7-task115(6) |
| `os_list_android_devices` | both | 6 | 5 | 1 | `readback` | 达标 | runs/_exercises/ex_grid/c7-task118(6) |
| `project_get_android_preset_info` | both | 6 | 0 | 6 | `count_only` | 计数达标缺证据 | runs/_exercises/ex_grid/c7-task118(6) |
| `os_deploy_to_android_device` | both | 6 | 0 | 6 | `count_only` | 计数达标缺证据 | runs/_exercises/ex_grid/c7-task118(6) |
| `project_build_csharp` | both | 67 | 63 | 0 | `file_effect` | 计数达标缺证据 | runs/_exercises/ex_files/c1b-task110(1) ; runs/_exercises/ex_grid/c6-task118(1) ; runs/_exercises/ex_scene/c23-task110(1) |
| `project_write_text_file` | both | 7 | 6 | 1 | `file_effect` | 达标 | runs/_exercises/ex_files/c1-task110(6) ; runs/_exercises/ex_files/c1-smoke(1) |
| `project_validate_scripts` | both | 84 | 80 | 0 | `readback` | 计数达标缺证据 | runs/breakout/breakout-clean-task097(2) ; runs/breakout/breakout-task093(2) ; runs/breakout/breakout-task093-r2(2) |
| `editor_set_node_script_batch` | editor | 56 | 0 | 1 | `readback` | 达标 | runs/_exercises/ex_grid/c6-task118(6) ; runs/breakout/breakout-clean-task097(2) ; runs/breakout/breakout-task093(2) |
| `editor_set_node_property_updates` | editor | 30 | 3 | 7 | `pixel_effect` | 达标 | runs/_exercises/ex_write/c4-task111(6) ; runs/_exercises/ex_write2/c4b-task111(6) ; runs/_exercises/ex_write3/c4c-task111(6) |
| `project_read_text_file` | both | 86 | 85 | 1 | `readback` | 达标 | runs/_exercises/ex_files/c1-task110(6) ; runs/pong/d3-after(3) ; runs/pong/d3-after-r2(3) |

### 2.2 `1-4` 次（0 条）

| tool | scope | 累计 | 有效 | 边界 | 档位 | 状态 | 证据 |
|---|---|---|---|---|---|---|---|

### 2.3 `0` 次（5 条）

（按前缀分组，均为 0 次；其中登记为「不可达」的见 §4）

- **editor_**（5）：`editor_simulate_key` `editor_simulate_mouse_click` `editor_simulate_mouse_move` `editor_simulate_input_action` `editor_simulate_input_sequence`

## 3. `<5` 清单（本轮仍未达标的工具）

共 **5** 条（占契约 2.8%）：`0` 次 5 条、`1-4` 次 0 条。

| tool | scope | verb | 累计 | 有效 | 边界 | 档位 | 登记不可达 | 状态 |
|---|---|---|---|---|---|---|---|---|
| `editor_simulate_key` | editor | simulate | 0 | 0 | 0 | `no_calls` | H7 | 未达(0) |
| `editor_simulate_mouse_click` | editor | simulate | 0 | 0 | 0 | `no_calls` | H7 | 未达(0) |
| `editor_simulate_mouse_move` | editor | simulate | 0 | 0 | 0 | `no_calls` | H7 | 未达(0) |
| `editor_simulate_input_action` | editor | simulate | 0 | 0 | 0 | `no_calls` | H7 | 未达(0) |
| `editor_simulate_input_sequence` | editor | simulate | 0 | 0 | 0 | `no_calls` | H7 | 未达(0) |

## 4. 不可达登记表的联动视图（H1–H9）

登记来源：`recovery/reports/TOOL-COVERAGE-TASK-108.md` §5.3 (5) which of them are structurally unreachable in this loop (INFERENCE)（**推断**，判据是「缺少本循环不具备的子系统/资产/前置运行态」）。本视图把登记表与本轮实测**对在一起**：`实测调用` 列不为 0 的条目就是登记漂移，必须在下一轮从登记表里移除或改判。

登记成员 **74** 条；其中实测**已被调用**（登记漂移）**69** 条，其中 **69** 条已按实测证据改判并记入登记表的 `reclassified`（下表 `改判` 列打 `YES`），其余为待复核漂移。

**与「不可达」分开计的两栏**（TASK-118 C/D：它们不是不可达，不能加进上一段的数字里）：

| 栏 | 工具数 | 工具 | 登记位置 |
|---|---|---|---|
| `scope-excluded`（按 D59 / GDR-21 范围决定排除） | 5 | `editor_simulate_key` `editor_simulate_mouse_click` `editor_simulate_mouse_move` `editor_simulate_input_action` `editor_simulate_input_sequence` | `H7` |
| `needs-an-external-device`（本机实测：缺设备/缺预设） | 3 | `os_list_android_devices` `os_deploy_to_android_device` `project_get_android_preset_info` | `H8` |

`needs-an-external-device` 的本机实测命令与结果写在登记表 `categories.H8.external_device.measured_on_this_machine` 里，调用证据在 `runs/_exercises/ex_grid/c7-task118`。

### H1 3D 内容管线

- 为何不可达（推断）：20 款游戏**全部是 2D**，世界由 `ColorRect` / `Label` 在运行期或加载期拼出；工程里没有任何 Mesh / Camera3D / 光照 / WorldEnvironment 资产，也没有 `.tscn` 里能寻址的 3D 节点
- 支撑证据（只读观察）：模块侧 `tools/editor_scene_3d_write.cpp`；20 款游戏的载荷全部为 2D 坐标（台账逐条记 `ColorRect`/`Label`/像素差）

| tool | scope | 实测调用 | 漂移 | 改判 | 证据 |
|---|---|---|---|---|---|
| `editor_add_mesh_instance` | editor | 18 | **YES** | YES | runs/_exercises/ex_3d/h1-task111(6) ; runs/_exercises/ex_3d/h1b-task115(6) ; runs/_exercises/ex_3d/h1b2-task115(6) |
| `editor_get_viewport_3d_camera` | editor | 6 | **YES** | YES | runs/_exercises/ex_3d/h1-task111(6) |
| `editor_set_material_3d` | editor | 18 | **YES** | YES | runs/_exercises/ex_3d/h1-task111(6) ; runs/_exercises/ex_3d/h1b-task115(6) ; runs/_exercises/ex_3d/h1b2-task115(6) |
| `editor_set_viewport_3d_camera` | editor | 6 | **YES** | YES | runs/_exercises/ex_3d/h1-task111(6) |
| `editor_setup_camera_3d` | editor | 18 | **YES** | YES | runs/_exercises/ex_3d/h1-task111(6) ; runs/_exercises/ex_3d/h1b-task115(6) ; runs/_exercises/ex_3d/h1b2-task115(6) |
| `editor_setup_lighting` | editor | 18 | **YES** | YES | runs/_exercises/ex_3d/h1-task111(6) ; runs/_exercises/ex_3d/h1b-task115(6) ; runs/_exercises/ex_3d/h1b2-task115(6) |
| `editor_setup_world_environment` | editor | 18 | **YES** | YES | runs/_exercises/ex_3d/h1-task111(6) ; runs/_exercises/ex_3d/h1b-task115(6) ; runs/_exercises/ex_3d/h1b2-task115(6) |

### H2 动画 / AnimationTree / 状态机

- 为何不可达（推断）：运动一律由**载荷自己的整数运动学**推进（`StepFrames(n)`、`_Process` 里 `x+=vx`），从不使用 `AnimationPlayer` / `AnimationTree`；没有动画资源可读写，也没有状态机可建
- 支撑证据（只读观察）：`tools/editor_animation_read.cpp`、`editor_animation_write.cpp`、`editor_animation_tree_write.cpp`、`tools/animation_shared.cpp`；契约 override 里 `add_state_machine_state` 的 `animation` 成员是「结构性不可达」的已知缺口

| tool | scope | 实测调用 | 漂移 | 改判 | 证据 |
|---|---|---|---|---|---|
| `editor_add_animation_track` | editor | 12 | **YES** | YES | runs/_exercises/ex_anim/h2-task111(6) ; runs/_exercises/ex_anim2/h2b-task111(6) |
| `editor_add_state_machine_state` | editor | 18 | **YES** | YES | runs/_exercises/ex_anim2/h2b-task111(12) ; runs/_exercises/ex_anim/h2-task111(6) |
| `editor_add_state_machine_transition` | editor | 22 | **YES** | YES | runs/_exercises/ex_anim/h2-task111(11) ; runs/_exercises/ex_anim2/h2b-task111(11) |
| `editor_create_animation` | editor | 23 | **YES** | YES | runs/_exercises/ex_anim/h2-task111(9) ; runs/_exercises/ex_anim2/h2b-task111(9) ; runs/_exercises/ex_anim2/h2c-task115(5) |
| `editor_create_animation_tree` | editor | 12 | **YES** | YES | runs/_exercises/ex_anim/h2-task111(6) ; runs/_exercises/ex_anim2/h2b-task111(6) |
| `editor_get_animation_info` | editor | 12 | **YES** | YES | runs/_exercises/ex_anim/h2-task111(6) ; runs/_exercises/ex_anim2/h2b-task111(6) |
| `editor_get_animation_tree_structure` | editor | 12 | **YES** | YES | runs/_exercises/ex_anim/h2-task111(6) ; runs/_exercises/ex_anim2/h2b-task111(6) |
| `editor_list_animations` | editor | 15 | **YES** | YES | runs/_exercises/ex_anim/h2-task111(6) ; runs/_exercises/ex_anim2/h2b-task111(6) ; runs/_exercises/ex_anim2/h2c-task115(3) |
| `editor_remove_animation` | editor | 18 | **YES** | YES | runs/_exercises/ex_anim/h2-task111(6) ; runs/_exercises/ex_anim2/h2b-task111(6) ; runs/_exercises/ex_anim2/h2c-task115(6) |
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
| `editor_add_gridmap` | editor | 12 | **YES** | YES | runs/_exercises/ex_grid/c6-task118(6) ; runs/_exercises/ex_grid/h3-task111(6) |
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

- 为何不可达（推断）：SUPERSEDED BY MEASUREMENT (TASK-115). The original inference below was a single claim about a mixed family, and it was wrong for ten of its nineteen members: the editor's own GUI state (selection, Output panel, run bar, addon list, test-report bridge file, screenshot diff) is fully readable and writable through the editor endpoint. What is really left is the five editor_simulate_* tools, whose exclusion is a scope decision (D59 / GDR-21), not a missing subsystem - see `still_out`. ORIGINAL TEXT, kept for audit: 这类工具的输入是**编辑器进程自己的 GUI 状态**（当前选择、打开的脚本、Output 面板、对话框、已装插件）或**编辑器自己的播放器/输入队列**。本循环里编辑器端点只做「开场景 / 加节点 / 存场景 / 建脚本 / 编译 / 读错误」；所有行为验证都走游戏端点，且**刻意不用**编辑器侧输入注入（B2 说明：`editor_simulate_*` 注入的是编辑器进程的输入，不能用来驱动游戏进程 —— D59 / GDR-21 的边界）
- 支撑证据（只读观察）：TASK-115: runs/_exercises/ex_editor/h7-task115 (82 calls, 169 named tools in the whole corpus after the batch); tools/sessions/_exercises/ex_editor/h7-manifest.json (7 content-level read-back declarations, all verified). ORIGINAL TEXT, kept for audit: `tools/editor_playback.cpp`、`editor_input_simulation.cpp`、`editor_profiling_read.cpp`、`editor_testing_read.cpp`、`editor_script_write.cpp`、`editor_read_scene_inspector.cpp`；`editor_get_test_report` / `editor_analyze_screenshot_diff` 需要「编辑器侧测试运行」，而本循环的测试运行发生在游戏端点

| tool | scope | 实测调用 | 漂移 | 改判 | 证据 |
|---|---|---|---|---|---|
| `editor_analyze_screenshot_diff` | editor | 8 | **YES** | YES | runs/_exercises/ex_editor/h7-task115(8) |
| `editor_get_open_scripts` | editor | 12 | **YES** | YES | runs/_exercises/ex_scene/c23-task110(6) ; runs/_exercises/ex_scene2/c23-after-task110(6) |
| `editor_get_output_log` | editor | 38 | **YES** | YES | runs/_exercises/ex_scene/c23-task110(6) ; runs/_exercises/ex_scene2/c23-after-task110(6) ; runs/_exercises/ex_write/c4-task111(6) |
| `editor_get_performance_monitors` | editor | 12 | **YES** | YES | runs/_exercises/ex_scene/c23-task110(6) ; runs/_exercises/ex_scene2/c23-after-task110(6) |
| `editor_get_selection` | editor | 17 | **YES** | YES | runs/_exercises/ex_scene/c23-task110(6) ; runs/_exercises/ex_scene2/c23-after-task110(6) ; runs/_exercises/ex_editor/h7-task115(5) |
| `editor_get_test_report` | editor | 6 | **YES** | YES | runs/_exercises/ex_editor/h7-task115(6) |
| `editor_play_scene` | editor | 7 | **YES** | YES | runs/_exercises/ex_editor/h7-task115(7) |
| `editor_reload_plugin` | editor | 6 | **YES** | YES | runs/_exercises/ex_editor/h7-task115(6) |
| `editor_remove_node_selection` | editor | 6 | **YES** | YES | runs/_exercises/ex_editor/h7-task115(6) |
| `editor_remove_output_log` | editor | 6 | **YES** | YES | runs/_exercises/ex_editor/h7-task115(6) |
| `editor_rescan_project_filesystem` | editor | 6 | **YES** | YES | runs/_exercises/ex_editor/h7-task115(6) |
| `editor_set_auto_dismiss_dialogs` | editor | 7 | **YES** | YES | runs/_exercises/ex_editor/h7-task115(7) |
| `editor_set_node_selection` | editor | 9 | **YES** | YES | runs/_exercises/ex_editor/h7-task115(9) |
| `editor_simulate_input_action` | editor | 0 | - | - | - |
| `editor_simulate_input_sequence` | editor | 0 | - | - | - |
| `editor_simulate_key` | editor | 0 | - | - | - |
| `editor_simulate_mouse_click` | editor | 0 | - | - | - |
| `editor_simulate_mouse_move` | editor | 0 | - | - | - |
| `editor_stop_scene` | editor | 7 | **YES** | YES | runs/_exercises/ex_editor/h7-task115(7) |

### H8 发布 / 导出 / Android 部署路径

- 为何不可达（推断）：循环的终点是「游戏跑起来 + 可复算证据」，从不打包、不导出、不连真机；`project_export_game` 甚至被契约 `_meta.excluded` 排除、`project_get_export_info` 等只在发布路径生效
- 支撑证据（只读观察）：`tools/project_export_read.cpp`、`os_android_read.cpp`、`os_android_write.cpp`、`project_android_read.cpp`；契约 `_meta.excluded = ["navigate_to","export_project"]`

| tool | scope | 实测调用 | 漂移 | 改判 | 证据 |
|---|---|---|---|---|---|
| `os_deploy_to_android_device` | both | 6 | **YES** | YES | runs/_exercises/ex_grid/c7-task118(6) |
| `os_list_android_devices` | both | 6 | **YES** | YES | runs/_exercises/ex_grid/c7-task118(6) |
| `project_get_android_preset_info` | both | 6 | **YES** | YES | runs/_exercises/ex_grid/c7-task118(6) |
| `project_get_export_info` | both | 13 | **YES** | YES | runs/_exercises/ex_export/h8-task114(8) ; runs/_exercises/ex_export_np/h8n-task114(5) |
| `project_list_export_presets` | both | 14 | **YES** | YES | runs/_exercises/ex_export/h8-task114(9) ; runs/_exercises/ex_export_np/h8n-task114(5) |

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
| `project_get_export_info` | H8 | the two export-read tools only need res://export_presets.cfg, not a real export. Ex_export (2 presets: Windows Desktop + Web) drove the real success branch on BOTH endpoints -- editor answers capabilities={editor_export:true,editor_process:true,presets_source:'editor_export'} with preset_count=2, the game process answers editor_export:false,editor_process:false,presets_source:'export_presets.cfg' with the same preset_count=2. Ex_export_np (no export_presets.cfg at all) drove the capability-missing branch: presets_file_present=false, count=0, message="'res://export_presets.cfg' does not exist: this project has no export presets", and on the editor endpoint unavailable[] carries the export_presets entry -- i.e. a missing file is an answer, not an error. The empty inputSchema also gives a constructible boundary: any argument is refused with -32602 "accepts no parameters" (4x, both endpoints). | `runs/_exercises/ex_export/h8-task114/trace-editor.jsonl, runs/_exercises/ex_export/h8-task114/trace-game.jsonl, runs/_exercises/ex_export_np/h8n-task114/trace-editor.jsonl, runs/_exercises/ex_export_np/h8n-task114/trace-game.jsonl` |
| `project_list_export_presets` | H8 | same two runs: count=2 with the preset records read straight out of export_presets.cfg on both endpoints, and count=0 + presets_file_present=false + message on the project without the file. The unknown-argument gate refuses preset_name and index with -32602. | `runs/_exercises/ex_export/h8-task114/trace-editor.jsonl, runs/_exercises/ex_export/h8-task114/trace-game.jsonl, runs/_exercises/ex_export_np/h8n-task114/trace-editor.jsonl, runs/_exercises/ex_export_np/h8n-task114/trace-game.jsonl` |
| `editor_play_scene` | H7 | the editor's own scene player IS reachable from the editor endpoint: five releases of the project's main/current/custom scene each really created a game child process (--mcp-port 61849/61856/61861/61865/9899 answered in args_injected, pid + endpoint in the answer), and the editor's own run bar state was read back by editor_execute_gdscript -> EditorInterface.is_playing_scene(), true after play and false after the matching stop. The tools that start and stop the editor's player were never about the game endpoint. | `runs/_exercises/ex_editor/h7-task115/trace-editor.jsonl` |
| `editor_stop_scene` | H7 | same run: five stops each answered stopped:true and killed the child, a sixth answered {stopped:false, 'No scene playing'} (the documented honest answer, not a failure), and is_playing_scene() read back false. The stop tool is the module's only 'no orphan game process' lever, and this run used it five times with no orphan left (post-run tasklist shows no godot process). | `runs/_exercises/ex_editor/h7-task115/trace-editor.jsonl` |
| `editor_set_node_selection` | H7 | the editor's own EditorSelection is writable through the editor endpoint: nine calls (node_paths, node_path, mode=replace/add) each answered with the selection the engine holds, and editor_get_selection read the same node back by name and type (five content-level witnesses). | `runs/_exercises/ex_editor/h7-task115/trace-editor.jsonl` |
| `editor_remove_node_selection` | H7 | same run: five clears answered cleared:1/1/1/3/0 and editor_get_selection then answered {"count":0,"nodes":[]} - the empty selection is a valid, verifiable answer, which is what the register's 'GUI state is not reachable' inference got wrong. | `runs/_exercises/ex_editor/h7-task115/trace-editor.jsonl` |
| `editor_remove_output_log` | H7 | the Output panel of the editor process is both readable and clearable here: the panel held 10 lines (including 'Godot Engine v4.8.dev.custom_build') before the clear and one empty line after it, read back by editor_get_output_log in the same run (expect 'in_process':true + expect_absent 'Godot Engine v4.8.dev'). | `runs/_exercises/ex_editor/h7-task115/trace-editor.jsonl` |
| `editor_reload_plugin` | H7 | with a real addon enabled (projects/_exercises/ex_editor/addons/probe_plugin, listed by ProjectSettings' editor_plugins/enabled) five calls each answered {reloading:true, plugins:['res://addons/probe_plugin/plugin.cfg']}; the enabled list itself was read back by project_get_settings. NOTE: the success is NOT pixel/file observable (verdict ok_no_effect_observed), so this tool's only honest evidence channel is the read-back. | `runs/_exercises/ex_editor/h7-task115/trace-editor.jsonl` |
| `editor_rescan_project_filesystem` | H7 | EditorFileSystem::scan() is reachable through the editor endpoint: five calls each answered {reloaded:true}, and project_get_filesystem_tree read the project back with its scenes and addon files after the rescan. | `runs/_exercises/ex_editor/h7-task115/trace-editor.jsonl` |
| `editor_get_test_report` | H7 | the register's 'it needs an editor-side test run' inference is wrong by measurement: the tool reads the user:// bridge file the GAME process persists and otherwise answers honestly from this process' accumulator. Five calls each answered source=editor_process with no_results:true (total 0), the opt-in clear:true arm answered cleared:['editor_process'], and a mistyped clear is -32602. It is a read tool, so its own payload is substantive evidence: counted 达标 by tools/tool_coverage.py. | `runs/_exercises/ex_editor/h7-task115/trace-editor.jsonl` |
| `editor_analyze_screenshot_diff` | H7 | same class of correction: the comparison is CPU-side (Image::load / load_png_from_buffer) and needs no display server and no editor-side test run at all. Five calls measured real pairs (8x8 identical -> changed_pixels 0; two differing 8x8 PNGs -> changed_pixels 32; threshold 0 and 255 at the inclusive/exclusive ends) and three refusals were measured (missing image -32001, 8x8 vs 16x16 size mismatch -32602, threshold 300 -32602). Counted 达标. | `runs/_exercises/ex_editor/h7-task115/trace-editor.jsonl` |
| `editor_set_auto_dismiss_dialogs` | H7 | called seven times, and every well-formed call is the honest -32000 the implementation documents ('this engine has no process-wide auto-dismiss setting for editor dialogs'), plus two -32602 for the malformed ones. So the tool is REACHABLE and its contract is exercised, but it can never produce a success: its provider is a deliberate not-implemented, not a missing subsystem. It therefore stays at evidence tier count_only (7 boundary calls, 0 effective) BY DESIGN, and the register entry for it should read 'measured, boundary-only' rather than 'unreachable'. | `runs/_exercises/ex_editor/h7-task115/trace-editor.jsonl` |
| `os_list_android_devices` | H8 | TASK-118 measured it instead of assuming: the Android SDK is installed off-PATH, the run started adb and the tool answered a real empty device list (count=0, devices=[]), which is an ok substantive payload on its declared `payload` channel. 5 ok calls + 1 boundary -> 达标. | `runs/_exercises/ex_grid/c7-task118` |
| `project_get_android_preset_info` | H8 | TASK-118 called it 6 times: every call is refused because no project in this repository has an Android preset. That is a measured boundary, not an unreachable claim, so it moves out of the register's unreachable set and into `categories.H8.external_device`. | `runs/_exercises/ex_grid/c7-task118` |
| `os_deploy_to_android_device` | H8 | TASK-118 called it 6 times with skip_export=true: every call is refused before the export child process starts (no such preset, then the parameter rule). Measured boundary only; the deploy path needs an Android preset and a device. | `runs/_exercises/ex_grid/c7-task118` |

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

