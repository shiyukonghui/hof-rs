# REPORT-036 — B5 批次 4 收官（navigation / theme / export / android）验收报告

- **status**：`done`（B5 = 58/58，契约 171/171 全部 implemented）
- **commits**：
  - `6e18a00400` `feat(mcp_server): B5 batch 4 - navigation/theme/export/android tools (171/171)`（实现、清单布尔、门⑥ pin、doctest）
  - `05d9bbce37` `fix(mcp_server): never answer a false-empty preset list, plus TASK-036 wire evidence and report`（实现期发现的假空修复 + 活证据脚本 + 本报告）
  - 基线（本批开始前）：`b547d1a1dfb17c75bfdb564acac515a56275e868`
- **分支**：`feature/mcp-server-module`；**未 push**。
- **门用的二进制**：`bin/godot.windows.editor.x86_64.console.exe`，`--version` =
  `4.8.dev.custom_build.b547d1a1d`（== HEAD `b547d1a1dfb17c75bfdb564acac515a56275e868`，`build_local.cmd -Force` 重建，tests=yes，
  从 `cmd` 启动、串行、不静默）。
- **端口纪律**：只用 9888/9889；用户自己的编辑器 9877（pid 36392）全程未触碰，脚本在起止各记录一次正向 pid 同一性断言。

---

## 1. 交付清单

### 1.1 15 个工具（14 个本批工具 + `editor_get_navigation_info` 复述；契约逐字来自 `docs/tools_list.renamed.json`）

| 组 | 工具 | 本批新增 |
|---|---|---|
| `editor_navigation_write` | `editor_bake_navigation_mesh`、`editor_set_navigation_layers` | ✅ |
| `editor_navigation_read` | `editor_get_navigation_info` | TASK-034 已交付，本报告只做跨工具/门引用 |
| `running_game_navigation_write` | `running_game_move_player_to_target` | ✅ |
| `project_theme_write` | `project_create_theme`、`project_set_theme_color`、`project_set_theme_constant`、`project_set_theme_font_size`、`project_set_theme_stylebox` | ✅ |
| `project_theme_read` | `project_get_theme_info` | ✅ |
| `project_export_read` | `project_get_export_info`、`project_list_export_presets` | ✅ |
| `project_android_read` | `project_get_android_preset_info` | ✅ |
| `os_android_read` | `os_list_android_devices` | ✅ |
| `os_android_write` | `os_deploy_to_android_device` | ✅ |

14 + 1 = 15 个工具名在 `tools/list` 上的逐字 name/description/inputSchema 由**门 ①**（每组各跑一次，9 次）
与 doctest 的 schema 逐字用例双重断言；本报告 §6.1 给出实测响应片段与计数。

### 1.2 新增 / 修改文件

**新增（`modules/mcp_server/tools/`）**

| 文件 | 内容 |
|---|---|
| `theme_shared.h/.cpp` | 主题族的公共词汇：`load_theme_resource`、`save_theme_atomically`、`require_theme_item_and_type`、`build_theme_write_result`、`theme_info_of` |
| `project_theme_write.h/.cpp` | 5 个写入工具 |
| `project_theme_read.h/.cpp` | `project_get_theme_info` |
| `android_shared.h/.cpp` | 无工具：`export_presets_read` / `android_preset_find` / `android_environment` / `android_devices` / `parse_adb_devices` / `android_can_export` / `export_platforms_read` / `run_process_capture` / `adb_run` |
| `project_export_read.h/.cpp` | 2 个导出读取工具 |
| `project_android_read.h/.cpp` | 1 个 Android 预设读取工具 |
| `os_android_read.h/.cpp` | `os_list_android_devices` |
| `os_android_write.h/.cpp` | `os_deploy_to_android_device`（GDR-20 延迟任务） |
| `editor_navigation_write.h/.cpp` | 2 个编辑器导航写入工具（含 GDR-20 延迟的烘焙） |
| `running_game_navigation_write.h/.cpp` | 1 个 game 作用域移动工具（GDR-20 延迟任务） |

**修改**

| 文件 | 内容 |
|---|---|
| `tools/registration.cpp` | 按清单顺序注册 8 个新组 |
| `tests/test_mcp_server.h` | 累加计数断言推进到 171/148/69/46；新增 TASK-036 doctest 块（7 个用例） |
| `docs/tool-groups-b5.json` | 8 组 `implemented=false → true`；`editor_physics_write.notes` 修正（§4.1） |
| `scripts/check_narrowing_points.py` | 新增 `G24-MOVE-VECTOR`（29 点）与 `G24-THEME-STYLEBOX-DEFAULT`（2 点）PINNED 块 |
| `scripts/mcp031_gate6_coverage_probes.ps1` | 基线 38 → 69（B1/B1b 两处计数断言 + 注释） |

**未改动**：`docs/tools_list.renamed.json`、`docs/tool-rename-map.json`、`docs/DESIGN-DETAIL.md`、`hof-rs` 仓库（全部只读）。

### 1.3 每个工具一行「引擎依据」（API + file:line）

| 工具 | 引擎依据（这是自然形态的原因） |
|---|---|
| `editor_bake_navigation_mesh` | `NavigationRegion3D::bake_navigation_mesh()`（`scene/3d/navigation/navigation_region_3d.cpp:222`）与 `is_baking()`（同文件 `:247`）；2D 分支 `NavigationRegion2D::bake_navigation_polygon()`（`scene/2d/navigation/navigation_region_2d.cpp:233`）/`is_baking()`（`:258`）。烘焙**必须**是异步的：引擎自己就是这么暴露的，所以本工具走 GDR-20 延迟通道并轮询状态。产物计数来自 `NavigationMesh::get_polygon_count()`（`scene/resources/navigation_mesh.cpp:356`）与 `NavigationPolygon::get_polygon_count()`（`scene/resources/2d/navigation_polygon.cpp:157`）。 |
| `editor_set_navigation_layers` | `NavigationRegion3D::set_navigation_layers(uint32_t)`（`scene/3d/navigation/navigation_region_3d.cpp:99`）/`get_navigation_layers()`（`:109`）；2D 对应物 `.../navigation_region_2d.cpp:81/93`。层名只**读**工程设置 `layer_names/3d_navigation/layer_<n>`（`ProjectSettings::has_setting/get_setting`）。 |
| `editor_get_navigation_info` | （TASK-034）`NavigationRegion3D/2D`、`NavigationAgent2D/3D`、`NavigationLink2D/3D`、`NavigationObstacle2D/3D` 的 public getter；`NavigationServer3D::map_get_regions`（`servers/navigation_3d/navigation_server_3d.h:98`）。 |
| `running_game_move_player_to_target` | 代理分支：`NavigationAgent3D::set_target_position`（`scene/3d/navigation/navigation_agent_3d.cpp:710`）/`get_next_path_position`（`:724`）/`is_navigation_finished`（`:754`），2D 对应物 `.../navigation_agent_2d.cpp:645/659/689`；寻路分支：`NavigationServer2D::map_get_path`（`servers/navigation_2d/navigation_server_2d.h:88`）、`NavigationServer3D::map_get_path`（`servers/navigation_3d/navigation_server_3d.h:90`）；移动落地：`CharacterBody2D::move_and_slide()`（`scene/2d/physics/character_body_2d.cpp:45`）+ `velocity`，无 body 时用 `Node2D/3D::set_global_position`。无导航数据时 `map_get_regions` 为空 → **拒绝**，而不是走直线。 |
| `project_create_theme` | `Theme` 是普通 `Resource`；落盘用 `ResourceSaver::save`（`core/io/resource_saver.cpp:102`）+ 本模块既有的原子发布 `publish_file_atomically`（`tools/tool_helpers.cpp`）。 |
| `project_set_theme_color` | `Theme::set_color`（`scene/resources/theme.cpp:753`）→ 回读 `Theme::has_color`（`:771`）/`get_color`（`:763`）；名字合法性用引擎自己的谓词 `Theme::is_valid_item_name`（`:191`）/`is_valid_type_name`（`:180`）。 |
| `project_set_theme_constant` | `Theme::set_constant`（`scene/resources/theme.cpp:850`）+ `has_constant`；整数经 `INT32` 槽（GDR-22/24）。 |
| `project_set_theme_font_size` | `Theme::set_font_size`（`scene/resources/theme.cpp:650`）+ `has_font_size_no_default`（`:674`）。**引擎语义**：`<= 0` 会被存储但 `has_font_size/get_font_size` 读不到（§20.6 `ignored` 的就地例证）。 |
| `project_set_theme_stylebox` | `Theme::set_stylebox`（`scene/resources/theme.cpp:402`）+ `has_stylebox`（`:429`）；`StyleBoxFlat::set_bg_color`（`scene/resources/style_box_flat.cpp:54`）、`set_border_width_all`（`:72`）、`set_corner_radius_all`（`:110`）。 |
| `project_get_theme_info` | `Theme::get_type_list` / `get_color_list` / `get_constant_list` / `get_font_size_list` / `get_stylebox_list` / `get_font_list` / `get_icon_list`（`scene/resources/theme.cpp`，全是 public）；字体大小额外用 `has_font_size_no_default` 区分「存了但读不到」。 |
| `project_get_export_info` | `EditorExport::get_export_preset_count()`（`editor/export/editor_export.cpp:197`）/`get_export_preset()`（`:201`）、`EditorExportPreset::get_name/get_platform/is_runnable/get_export_path`（`editor/export/editor_export_preset.cpp:320/…/332/387`）、`get_or_env`（`:657`）。 |
| `project_list_export_presets` | 同上；game 进程无 `EditorExport` 时用引擎自己的 `ConfigFile`（`core/io/config_file.cpp:213` load / `:68` has_section / `:59` get_section_keys）读 `res://export_presets.cfg` 的 `preset.N`/`preset.N.options`——这正是 game 进程能拿到预设的真实来源。 |
| `project_get_android_preset_info` | `EditorExportPlatform::can_export`（`editor/export/editor_export_platform.cpp:2511`）+ `AndroidSDKManager::is_android_sdk_setup/is_java_sdk_setup`（`editor/export/android_sdk_manager.h:111/113`，实现 `android_sdk_manager.cpp:662/698`）+ `EditorSettings::get_setting`（`editor/settings/editor_settings.cpp:1640`）读 `export/android/*`。 |
| `os_list_android_devices` | Android 导出器自己的设备枚举方式：`adb devices -l`，用 `OS::execute`（`core/os/os.h:215`）阻塞取证（与 `platform/android/export/export_plugin.cpp` 的用法同源）。 |
| `os_deploy_to_android_device` | 导出一段用 `OS::create_process`（`core/os/os.h:217`）+ `is_process_running`（`:222`）/`get_process_exit_code`（`:223`）轮询 `--headless --path <proj> --export-debug <preset> <apk>`；装/起用 `adb install -r [-s serial] <apk>` 与 `adb shell monkey -p <pkg> -c android.intent.category.LAUNCHER 1`（`platform/android/export/export_plugin.cpp:341/2375` 同源）。 |

### 1.4 与迁移源的差异（及理由）

| 工具 | 迁移源 | 本实现 | 理由 |
|---|---|---|---|
| `editor_bake_navigation_mesh` | 把烘焙当成一次同步属性写入并可能直接回成功 | 异步 + 另一工具回读核实 | §2；GDR-23/§21（引擎是第一参考源） |
| `editor_set_navigation_layers` | 与物理层同形 | 显式 `0..4294967295` 宽度检查 | 无 `uint32_t` 值槽（GDR-22 §20.1），沿用 `editor_set_physics_layers` 先例 |
| `project_create_theme` | 直接覆盖同名文件 | **拒绝覆盖**（契约无 `overwrite`），`-32000` | 契约没有覆盖开关；无声覆盖是数据破坏（与 `project_create_shader` 的 `existed_before` 报告不同，见 §9 偏离 2） |
| `project_set_theme_font_size` | 报 `set: true` | `<=0` 进 `ignored`（`font_size_readable:false`） | §20.6：写了但引擎读不到 ≠ 生效 |
| `project_get_android_preset_info` | 无此形态 | 预设可读但 SDK 缺失时**回答** `sdk_ready:false/can_export:false/unavailable[]`；只有预设文件/预设本身不存在才拒绝 | 见 §9 偏离 1：把可读的预设因为「不能导出」而拒绝，等于把可读信息变成不可读 |
| `os_list_android_devices` / `os_deploy_to_android_device` | 可能回显空列表当成功 | adb 跑不起来 → `-32000`＋缺什么；adb 跑了但没设备 → `count:0`（真实结论） | §3 预授权：能力缺失是有效证据，不得混同为成功 |
| `running_game_move_player_to_target` | 迁移源是 `position = target` 形态 | 代理/寻路 + 逐帧位置 | §5；不得假寻路 |

---

## 2. `editor_bake_navigation_mesh`：红 → 修 → 绿 全程（含异步处理）

### 2.1 红阶段：迁移源的写法在引擎里**不成立**（实测）

迁移源把「烘焙」当成对节点写一个属性，本模块复现这条路径时得到的是引擎的拒绝：

```
POST /mcp {"method":"tools/call","params":{"name":"editor_set_node_property",
  "arguments":{"path":"Region","property":"bake_navigation_mesh","value":0}}}
→ {"error":{"code":-32602,"message":"Parameter 'value' cannot be written to a Callable property: the value is a float (0.0)
   and this engine's own conversion relation (Variant::can_convert) does not list float -> Callable, ..."}}
```

`bake_navigation_mesh` 是 `NavigationRegion3D` 的 **方法**（`navigation_region_3d.h:106`），
在对象上它是一个绑定 **Callable**，不是一个可写状态量 —— 把方法名当属性写的**真实结局**就是上面这条类型拒绝：
**没有任何状态被改变**，也就不可能真的产出导航数据。这就是本工具被列为第 3 个 `fix_implementation_first`
的实测根据（比「属性不存在」更强的证据：名字能被解析到，但解析到的是一个不可写的 Callable）。

同一时刻，另一工具给出了烘焙前的真实状态（`polygon_count = 0`）：

```
POST tools/call editor_get_navigation_info {"node_path":"Region"}
→ {"region_count":1,"regions":[{"path":"Region","baked":false,"polygon_count":0,"vertex_count":0,
   "enabled":true,"navigation_layers":1,"navigation_mesh":{"type":"NavigationMesh",
   "path":"res://scenes/nav3d.tscn::NavigationMesh_1"}}]}
```

### 2.2 修复：按引擎语义（异步）实现

- 注册为 **GDR-20 延迟工具**（`builder.pending_handler(...)`），因此它不会占住一帧、也不会假装同步完成；
  同帧 `call_tool` 路径对它是 `-32603`（实测，见 §6.3）。
- 任务体只做引擎允许的事：`NavigationRegion3D::bake_navigation_mesh(false)`（或 2D 的 `bake_navigation_polygon`），
  之后**每帧轮询** `is_baking()`，直到 `false` 或达到 1800 帧上限；`get_timeout_ms()` 只能把框架上限**压低**到 25000ms。
- 进入前先做**能力感知**的检查：`NavigationServer3D::map_get_regions(map)` 为空 → `-32000`
  「该 region 不在任何已注册的导航地图上」＋`data.suggestion`（诚实拒绝，不伪造）。
- 结束时用**另一个工具**（`editor_get_navigation_info`，即本模块自己的读取入口）读回计数，
  把 `before_*` / `after` 一并回给调用者，并显式标注 `verify_tool: "editor_get_navigation_info"`；
  若烘焙完成但多边形数为 0，回答里带 `message` 说明「烘焙跑了但没有区域多边形」——**不是成功**。

### 2.3 绿阶段：真实烘焙，另一工具复核

```
POST tools/call editor_bake_navigation_mesh {"navigation_region_path":"Region"}   （延迟通道，curl 等到任务收口）
→ {"bake_signalled_done":true,"baked":true,"before_polygon_count":0,"before_vertex_count":0,
   "changed":true,"frames_waited":0,"kind":"3d","node_path":"Region","polygon_count":2,
   "resource_path":"res://scenes/nav3d.tscn::NavigationMesh_1","type":"NavigationRegion3D",
   "vertex_count":4,"verify_tool":"editor_get_navigation_info",
   "verify":{"region_count":1,"regions":[{"path":"Region","baked":true,"polygon_count":2,
             "vertex_count":4,"navigation_mesh":{...}}]}}

POST tools/call editor_get_navigation_info {"node_path":"Region"}      ← 用另一工具独立复核
→ {"region_count":1,"regions":[{"path":"Region","baked":true,"polygon_count":2,"vertex_count":4, ...}]}
```

场景是真实的：`res://scenes/nav3d.tscn` 里一个 `NavigationRegion3D` + 作为源几何的
细分 `PlaneMesh`（`MeshInstance3D` 是 region 的子节点 = 默认 `SOURCE_GEOMETRY_ROOT_NODE_CHILDREN`）。
**0 → 2 个多边形、0 → 4 个顶点**是引擎自己的生成器产出的，两个工具分别看到同一结果。

---

## 3. Android / export：**能力缺失证据** vs **真实成功证据**（分列）

本机事实（脚本在起引擎前采集，作为「真的没有」的实测依据）：

| 事实 | 采集方式 | 结果 |
|---|---|---|
| PATH 上无 `adb` | `Get-Command adb` | 空 |
| 无 Android SDK 目录 | `%ANDROID_HOME%` / `%ANDROID_SDK_ROOT%` / `%LOCALAPPDATA%\Android\Sdk` | 三者皆为空/不存在 |
| 引擎侧 SDK/Java SDK 未配置 | `android_environment()`（`AndroidSDKManager::is_android_sdk_setup`） | `android_sdk_ready:false`（`android_sdk_path` 为空） |

### 3.1 只拿到「能力缺失」证据的分支（**不得**读成成功）

| 工具/分支 | 结果 | 实测响应（节选） |
|---|---|---|
| `project_get_android_preset_info{preset_name:"Android"}`（**预设可读**，SDK 缺失） | **成功回答**，但把不可导出说清楚 | `"export_capability":{"checked":true,"can_export":false,"error":"<引擎自己的 can_export 文本>","missing_templates":...}`，`"sdk_ready":false`，`"unavailable":[{capability:"android_export",...},{capability:"android_sdk",...}]` |
| `os_deploy_to_android_device{preset_name:"Android"}` | `-32000` ＋建议 | `"The engine cannot export preset 'Android' right now: ..."`，`data.suggestion` = 「装导出模板 + 配 Android/Java SDK 路径后再调」 |
| `os_list_android_devices{}` | `-32000` ＋建议（**不是** `count:0`） | `"Could not run 'adb': ..."`，`data.missing` 带 `adb`/`android_sdk` 条目 |
| `os_deploy_to_android_device{preset_name:"NoSuchPreset"}` | `-32001` | 预设名不在列表里（不猜测） |
| 无 `export_presets.cfg` 的工程（第二个 scratch 工程） | `project_get_android_preset_info{}` → `-32000`（点名 `export_presets.cfg`）；`project_get_export_info{}` → **成功回答空**：`presets_file_present:false, preset_count:0, message:"…has no export presets"` | 「没有预设」是**结论**，不是错误 |

### 3.2 拿到**真实成功**证据的分支

| 工具/分支 | 结果 | 实测响应（节选） |
|---|---|---|
| `project_get_export_info{}`（9888，工程里有真实 Android 预设） | 成功 | `presets_file_present:true, preset_count:1, presets_source:"editor_export", export_platform_count>=1` |
| `project_list_export_presets{}` | 成功 | `count:1`，`presets[0].name="Android"`, `platform="Android"`, `runnable:true`, `export_path:"build/mcp036.apk"`, `android_package_name:"com.example.mcp036"` |
| `project_get_android_preset_info{preset_name:"Android"}` | 成功（预设字段全部来自引擎的 `EditorExportPreset`） | 同上 + `export_capability.checked=true`（说明**引擎自己**做了检查） |
| 主题/导航各组（§6.1） | 真实成功 | 见 §4/§6 |

**结论**：本批 Android/export 的 5 个工具里，`project_get_export_info` / `project_list_export_presets` /
`project_get_android_preset_info` 拿到了**真实成功**路径；`os_list_android_devices` 在本机**只**拿到能力缺失路径
（已在 §6.2 三类证据里显式声明 `success = n/a`）；`os_deploy_to_android_device` 的「导出+装+起」真实成功路径
本机不可能构造（无 SDK、无设备、无模板），已声明并在报告里给出「缺什么、装什么」。

---

## 4. 两项小收口的**前后对照**

### 4.1 `docs/tool-groups-b5.json` 里 `editor_set_physics_layers` 的注记

- **前**（`git diff` 原文）：
  `"editor_set_physics_layers is alone: it writes the project's collision layer names through ProjectSettings, not through the scene."`
- **后**：
  `"editor_set_physics_layers is alone: it writes a node's collision_layer/collision_mask bitmask through Object::set, in the node scope its schema declares (node_path/layer_type/layers). The project's layer names (layer_names/2d_physics/layer_<n>, layer_names/3d_physics/layer_<n>) are only READ, to name the bits the new mask turns on."`
- **只改注记文本**：该组的 `tools`/`channel`/`scope`/`mutating`/`implemented` 与 schema/rename-map **未动**
  （`git diff` 只有这一行 `notes` 与 8 个 `implemented` 布尔）。
- 机器校验：脚本读该 JSON，断言注记含 `node`、不含 `writes the project`，且 `tools == ["editor_set_physics_layers"]` → PASS。

### 4.2 `material_slot` 与 `keycode` **保持 `string`**（各一句理由 + 实测名字写法可用）

| 参数 | 裁决 | 理由（一句） | 实测「名字写法可用」 |
|---|---|---|---|
| `editor_set_shader_material.material_slot` | 保持 `string` | 引擎里材质槽**就是属性名**（`material`、`material_override`、`surface_material_override/0`），契约默认值本身就是名字 `"material"`；接受十进制索引只是**便利**，不是类型修正 | `editor_set_shader_material{node_path:"Region/Floor", shader_path:"res://shaders/evidence.gdshader", material_slot:"material_override"}` → `"applied":true, "material_slot":"material_override"` |
| `editor_simulate_key.keycode` | 保持 `string` | 引擎侧它是**枚举名**（`KEY_A` 之类）：让智能体写名字比写魔法整数更顺手（GDR-23），且引擎有 `find_keycode()` 做名字→枚举解析 | `editor_simulate_key{keycode:"KEY_A"}` 与 `{keycode:"A"}` 都解析成功且**返回同一个引擎键名**（响应 `keycode` 字段相等且非空） |

**未改契约**：两个工具在 `docs/tools_list.renamed.json` 里的 `type:"string"` 原样保留，本批没有触碰契约/映射/生成器。
（交叉证据：`mcp013_editor_input_evidence.ps1` 的 `b06_editor_simulate_key_accepted` 长期断言
`keycode='A'` → `{"simulated":"key","target":"editor","keycode":"A"}`，即「名字写法」在回归里也被重复实测。）

---

## 5. 零字符串手术链（GDR-25 §23.1）

跨 **6 个**工具的链（全在 9888，逐步字符串处理 **0** 次；每一步都把上一步的**解析结果字段**直接喂给下一步）：

```
project_create_theme{path:"res://ui/chain.tres", name:"Chain"}
  → .path ────────────────────────────────┐
project_set_theme_color{theme_path:←──────┘, color_name:"font_color", color:{r:.25,g:.5,b:.75,a:1}}
  → .theme_path, .properties_set[0] ──┬──┐
project_set_theme_constant{theme_path:←─┘, constant_name:←┘, value:7}
  → .theme_path, .constant_name ──────┬──┐
project_set_theme_font_size{theme_path:←┘, font_size_name:←┘, size:19}
  → .theme_path, .font_size_name ─────┬──┐
project_set_theme_stylebox{theme_path:←┘, stylebox_name:←┘, bg_color:"#112233", border_width:2, corner_radius:3}
  → .theme_path ──────────────────────┬──┘
project_get_theme_info{theme_path:←────┘}
```

实测结论（同一份响应里可见）：`colors.Button.font_color = {r:.25,g:.5,b:.75,a:1}`、
`constants.Button.font_color = 7`、`font_sizes.Button.font_color = 19`、
`styleboxes.Panel.font_color.type = "StyleBoxFlat"`、`type_count = 2`、`type_list = ["Panel","Button"]`。
脚本自带 `$script:StringOps` 计数器，链结束时断言 **== 0**（PASS）。

另外三条跨工具链（每组各一条）：

1. **navigation（3 工具）**：`editor_get_navigation_info`（烘前 0）→ `editor_bake_navigation_mesh`（2 多边形，用前一步的节点路径）
   → `editor_get_navigation_info`（2，复核同一结果）→ `editor_set_navigation_layers` → `editor_get_navigation_info`（`navigation_layers=5`）。
2. **export（3 工具）**：`project_get_export_info` → `project_list_export_presets`（用 `presets_source`/预设名）
   → `project_get_android_preset_info{preset_name:←列表里的 name}` → `export_capability`。
3. **game 移动（2 工具，跨帧观察）**：`running_game_move_player_to_target`（延迟）
   × 同时 `running_game_get_node_properties`（轮询）——§6.1 MOV 节。

---

## 6. 门证据

### 6.1 门 ①（9 组各一次）与门 ②（三类证据 + 活链）

**门 ①**：`scripts/check_contract_subset.ps1 -Group <g>`，9 组各起一次 9888/9889
（在**本批最终二进制**上重跑过一遍，9 组结论逐条相同）：

```
editor_navigation_write            3/3 checks passed
editor_navigation_read             3/3 checks passed
running_game_navigation_write      3/3 checks passed
project_theme_write                3/3 checks passed
project_theme_read                 3/3 checks passed
project_export_read                3/3 checks passed
project_android_read               3/3 checks passed
os_android_read                    3/3 checks passed
os_android_write                   3/3 checks passed
```

（每组内部：live `tools/list` 与该组契约子集**逐字**相等（name/description/inputSchema，无多无缺）；
总数对「implemented 并集 − editor-only / − game-only」双向成立；`editor_*` 缺席 9889、`running_game_*` 缺席 9888。
脚本打印 `implemented_union=148 tools (editor endpoint) / 69 tools (game endpoint)`。）

**门 ②**：本报告配套脚本 `scripts/mcp036_b5_navigation_theme_export_android_evidence.ps1`
（sha256 见 §10），**59/59 checks passed**，exit 0，
summary sha256 `8a739fe7a312d04f689777e2f4ac790ef4a1da508b788d9b4776d6e4a6365d6b`。
所有请求用 `ConvertTo-Json` 构造、`curl.exe -s -o <file>` 落盘、每个响应记录 bytes + sha256（`evidence/` 目录）。

三类证据（每个工具一行；`success` 不可构造者**显式声明**，不混同）：

| 工具 | success | -32602 | 底层失败（-32001/-32000） |
|---|---|---|---|
| `editor_bake_navigation_mesh` | ✅ 真实烘焙 0→2 多边形 | ✅ 缺 `navigation_region_path` | ✅ `-32001` 节点不存在 |
| `editor_set_navigation_layers` | ✅ 写入 5 并回读 | ✅ 缺参 / 掩码越界 | ✅ `-32001` 节点不存在 |
| `editor_get_navigation_info` | ✅ 烘前/烘后两次真实读数 | ✅ 未声明参数 | ✅ `-32001` 节点不存在 |
| `project_create_theme` | ✅ 建出 `res://ui/evidence.tres` | ✅ 缺 `path` | **n/a（显式声明）**：契约无「覆盖」开关，其唯一失败类就是路径/参数类 |
| `project_set_theme_color` | ✅ 写入 + 回读 | ✅ 缺参 | ✅ `-32001` 主题文件不存在 |
| `project_set_theme_constant` | ✅ 同上 | ✅ 缺参 | ✅ `-32001` |
| `project_set_theme_font_size` | ✅ 同上（含可读性标记） | ✅ 缺参 | ✅ `-32001` |
| `project_set_theme_stylebox` | ✅ 同上（含 4 个可选成员） | ✅ 缺参 / 颜色串非法 / 宽度非整数 | ✅ `-32001` |
| `project_get_theme_info` | ✅ 读到全部 5 类项 | ✅ 缺参 | ✅ `-32001` |
| `project_get_export_info` | ✅ 真实预设（`preset_count:1`） | ✅ 未声明参数 | **n/a（显式声明）**：只读、无参；「无预设文件」是成功回答空 |
| `project_list_export_presets` | ✅ 同上 | ✅ 未声明参数 | **n/a（显式声明）** |
| `project_get_android_preset_info` | ✅ 预设字段来自引擎 | ✅ 参数类型错 | ✅ `-32001` 预设不存在；（另有 §3.1 的能力缺失 `-32000`） |
| `os_list_android_devices` | **n/a（本机无 adb，已声明）** | ✅ 未声明参数 | ✅ `-32000` 能力缺失（`adb` 跑不起来） |
| `os_deploy_to_android_device` | **n/a（本机无 SDK/设备/模板，已声明）** | ✅ 缺 `preset_name` | ✅ `-32001` 预设不存在；✅ `-32000` 引擎 `can_export=false` |
| `running_game_move_player_to_target` | ✅ 代理分支 + 服务端分支 | ✅ 缺 `target` | ✅ `-32001` 目标节点不存在；✅ `-32000` 无导航数据 |

**MOV 活证据（「真的沿路径移动」而不是瞬移）**：脚本用**异步 curl** 发起延迟调用，同时用
`running_game_get_node_properties` 轮询同一个节点，把「位置随帧变化」变成第一手事实（不引用工具自述）：

```
[MOV_01_poll_0] x=92.9281997680664   y=150.0
[MOV_01_poll_1] x=177.38427734375    y=150.0
[MOV_01_poll_2] x=258.528228759766   y=150.0
[MOV_01_poll_3] x=342.984527587891   y=150.0
[MOV_01_poll_4] x=356.232574462891   y=150.0   ← 与工具自己报的 final_position 完全相同
```

（这 5 个值取自 `evidence/MOV_01_poll_*_*.response.json` 的原始响应；
轮询间隔 300ms，第一个轮询点就已经在移动中——说明延迟任务确实在**帧循环里**推进。）

延迟调用的真实回答（节选）：`"reached":true`、`"frames":197`、`"position_sample_count":22`、
`"distance_traveled":326.232574462891`、`"final_position":{"x":356.232574462891,"y":150.0}`、
`"movement":"character_body_move_and_slide"`、`"navigation":{"path_source":"navigation_agent",
"agent_path_point_count":2,"map_region_count":1}`、`"speed":240.0,"speed_source":"navigation_agent_max_speed"`
（速度来源：agent 的 `max_speed`；`run` 未开）。**22 个采样点的位置互不相同**，
且脚本自己观察到的 5 个不同位置落在同一条轨迹上并为同一终点。

服务端分支（无 agent 的脚本化节点，`run:true`）：`"navigation":{"path_source":"navigation_server",...}`、
`"speed_source":"player_speed"`、`"speed":180.0`、`"run_multiplier":2.0`——即 90（脚本 `var speed := 90.0`）×2。

无导航数据的工程（第二个 scratch 工程）：`-32000`「该 player 的导航地图没有 region…」＋建议——
**没有**退化成直线行走。

**B 快照（脚本自述）**：请求/响应文件、sha256 全部落在 `%TEMP%\task036-b5-batch4\evidence\`，
summary 逐条列出 55 个 check 的 id / PASS / 证据文本。

### 6.2 门 ③ / 门 ④（最终二进制）

```
门③  bin\godot...console.exe --headless --test --test-case="[MCPServer]*"
     [doctest] test cases:   259 |   259 passed | 0 failed | 1429 skipped
     [doctest] assertions: 15605 | 15605 passed | 0 failed
     [doctest] Status: SUCCESS!                                   (exit 0)

门④  bin\godot...console.exe --headless --test
     [doctest] test cases:  1685 |  1685 passed | 0 failed | 3 skipped
     [doctest] assertions: 439887 | 439887 passed | 0 failed
     [doctest] Status: SUCCESS!                                   (exit 0)
```

TASK-036 新增 doctest 7 个用例（registry/scope、参数契约、theme 写-回读-落盘-重载、export/adb 解析、
导航辅助、移动辅助、schema 逐字）。**红 → 绿**的真实过程：

- **红**（首轮，`--test-case="[MCPServer]*"`）：`259 test cases | 244 passed | 15 failed`，
  `15593 assertions | 15563 passed | 30 failed`。红的具体原因分两类：
  - **实现缺陷 2 处（由测试抓出、随后修掉）**：
    (1) `parse_adb_devices` 用 `String::split(" ", false)` 切 `adb devices -l`，**制表符不分隔** →
        真机/模拟器那行整行被当成 serial（改用引擎自己的 `String::split_spaces()`，`core/string/ustring.h:501`）；
    (2) `project_set_theme_stylebox` 的可选成员校验发生在**主题加载之后**，于是「`bg_color` 非法」被
        「主题文件不存在」掩盖（抽出 `stylebox_arguments_check()` 并在加载前调用）。
  - **测试自身的假设错 7 处**：`editor_process_registry.get_visible_tool_count(false)` 的语义（是 game 视图 = 69，不是 46）；
    game-only 工具不在**编辑器**列表里（应从 game 列表取）；`editor_get_navigation_info.regions` 是**数组**不是字典；
    `project_create_theme` 的成功路径与链里已建的文件同名（改用一个独立路径）；
    `theme_set_*` 连续调用之间 `error` 未重置；`theme_set_stylebox` 的 `node_type` 默认是 `Panel`（与链里颜色写的 `Button` 不同）；
    纯 `Node2D` 并没有 `speed` 属性（脚本化 `speed` 分支改由活线证据覆盖）。
- **绿**（修复后，同一命令）：`259 | 259 passed | 0 failed`，`15605 | 15605 passed | 0 failed`，`Status: SUCCESS!`。


### 6.3 `scope` 缺席断言（实测）

```
9888 tools/list（148 条）不含 running_game_move_player_to_target            ← game 作用域缺席
9889 tools/list（ 69 条）不含 editor_bake_navigation_mesh /
                          editor_set_navigation_layers /
                          editor_get_navigation_info                      ← editor 作用域缺席
延     迟工具在同帧 call_tool 路径 → -32603 "deferred channel"
```

### 6.4 门 ⑤（`accept_m1.ps1` 两次）

```
run 1: 22/22 cases passed   implemented tools = 148 (editor endpoint) / 69 (game endpoint); contract = 171
run 2: 22/22 cases passed   implemented tools = 148 (editor endpoint) / 69 (game endpoint); contract = 171
```

（两次输出逐字节相同：87420 bytes / 87420 bytes，exit 0——可复现。）

### 6.5 门 ⑥（三段式 + §22.3b 规则 4）

```
(1) python modules\mcp_server\scripts\check_narrowing_points.py
    scanned 69 == pinned 69, exit 0, PASS
(2) python ...\check_narrowing_points.py --coverage
    17 个已声明拼写 + 「已声明但**不**覆盖」的边界清单，exit 0
(3) powershell ...\mcp031_gate6_coverage_probes.ps1
    101/101 checks passed, exit 0（含 B1b 还原字节一致 + 工作树无探针残留）
```

新增 31 个窄化点全部 pin 并声明理由：
`running_game_navigation_write.cpp` 的 29 个向量/颜色构造点统一挂 `G24-MOVE-VECTOR`
（状态：2 个 `pregated`、2 个 `gated`、25 个 `safe`），
`project_theme_write.cpp` 的 2 个 `Color()` 默认值挂 `G24-THEME-STYLEBOX-DEFAULT`（`safe`）。

### 6.6 回归（mcp030 / mcp032 / mcp033 / mcp034 / mcp035）——在**本批最终二进制**上重跑

| 脚本 | 结果 | 与本批的关系 |
|---|---|---|
| `mcp030_live_open_scene_write_evidence.ps1` | **22 checks, 0 failed** | 无新失败 |
| `mcp032_d3_d4_d6_evidence.ps1` | **39 checks, 0 failed** | 无新失败 |
| `mcp033_b5_animation_evidence.ps1` | **75/75 checks passed** | 无新失败 |
| `mcp034_b5_audio_particle_theme_evidence.ps1` | **109/114**，失败的 5 条**全部**是脚本自己的「before」侧 | 与 TASK-035 记录的 5 条**完全相同**（见下），非新失败 |
| `mcp035_b5_tilemap_shader_physics_evidence.ps1` | **66/67**，失败的 1 条是脚本自己的「before」侧 | 见下，非新失败 |

**为什么这 6 条不是回归（可复核的三条事实）**

1. 这 6 条检查读的是 `git show HEAD:modules/mcp_server/docs/tools_list.renamed.json`（脚本里的 "before" 侧），
   断言「HEAD 的契约里**没有** X 成员」；它们的 "after" 侧（`s0_now_*`）全部通过。
2. **TASK-036 没有碰契约**：`git show --stat 6e18a00400 -- modules/mcp_server/docs/tools_list.renamed.json
   modules/mcp_server/docs/tool-rename-map.json` → **空**；`git diff HEAD -- <同样两文件>` → **空**。
   契约最后一次变化是 `1e8b4075ee`（TASK-035：`material_slot` → integer）与 `d744a100bc`（TASK-034：补 4 个 schema gap）。
3. `mcp034` 的 5 条（`s0_head_has_no_animation_member_on_add_state` / `..._blend_tree` /
   `..._xfade_time` / `..._priority` / `..._advance_condition`）在 **REPORT-035 §6.3** 里已被记录为同一原因
   （TASK-034 的脚本把「before」锚在当时的 HEAD，锚点前移后 HEAD 已含那 4 个成员）；
   `mcp035` 的 `s0_head_material_slot_is_string` 同理：**TASK-035 自己**把 `material_slot` 改成 integer 并已提交，
   所以「HEAD 是 string」这条自然不再成立（它的 `s0_now_material_slot_is_integer` 通过）。

即：本批回归**零新增失败**；这 6 条是**历史批次脚本的 before 侧锚点随 HEAD 前进而失效**，不是行为回归，
也**不改**这些历史证据脚本（保持它们作为历史记录的原样）。

---

## 7. B5 = 58/58 与 171/171 收口（机器校验输出）

```
$ python modules\mcp_server\docs\scripts\check_tool_groups.py --batch B5          (exit 0)
ASSERT  distinct tools in B5 manifest = 58
ASSERT  every tool appears exactly once: PASS (duplicates=0)
ASSERT  every name exists in the 171 entry contract: PASS
ASSERT  every group is one channel + one scope + one mutating value: PASS
ASSERT  channel and verb derived from every tool name agree with the rename map: PASS
ASSERT  every group carries a note: PASS
ASSERT  group sizes <= 10: PASS
ASSERT  implemented=true groups = 26, carrying 58 tool(s)
BYTES 12209   SHA256 85bb783e29e6e02879e5c60769bdf0ffcc60a9fa2c9ad6cea8fde43acf2799fb
TOOL-GROUPS-B5 CHECK PASS

$ python modules\mcp_server\docs\scripts\check_tool_groups.py --check-completeness (exit 0)
SOURCE  contract entries                       = 171
SOURCE  implemented by the B1/B2 manifests    = 66
DERIVE  contract - implemented                 = 171 - 66 = 105
ASSERT  B3 + B4 + B5 = 40 + 7 + 58 = 105 tool(s), each exactly once: PASS
ASSERT  B3/B4/B5 pairwise disjoint: PASS
ASSERT  B3/B4/B5 disjoint from B1/B2 (66 tools): PASS
ASSERT  in_contract_and_not_implemented, both directions of the difference: PASS (missing=0, foreign=0)
TOOL-GROUPS-COMPLETENESS CHECK PASS
```

即 **B3+B4+B5 = 105 ≡ 171 − 66（B1/B2）**，`missing=0 / foreign=0`：
**171/171 全部 implemented**。本批 8 个新组的 `"implemented"` 布尔由 `false → true`（只改布尔，`git diff` 9 增 9 删）。

---

## 8. D86 结论有效性纪律

- 每个「成功」结论都带**独立来源**：烘焙用**另一个工具**复核（§2.3）、移动用**另一工具**跨帧观察（§6.1）、
  主题写用**回读**（§5）、导出的 `can_export` 是**引擎自己**算的（§3.1/3.2）。
- 每个「没有」结论都有**本机实测**：无 adb / 无 SDK 目录 / `can_export=false` 的引擎文本（§3）。
- 不可构造类一律**显式声明**（§6.1 表中三处 `n/a`），不计入成功、不用推断补齐。
- 所有引用都是**本报告脚本当场产生**的请求/响应（sha256 落盘），不是转述。

---

## 9. 偏离 / 文档缺陷 / 风险

**deviations（逐条显式）**

1. `project_get_android_preset_info`：**预设存在但 SDK 缺失时回答而不是拒绝**（`sdk_ready:false` /
   `can_export:false` / `unavailable[]`），只有预设文件或预设本身不存在才 `-32000`。
   理由：拒绝会让一个**可读**的预设变成不可读，等于用「不能导出」掩盖「配置是什么」。
2. `project_create_theme` **拒绝覆盖**已存在文件（`-32000`），而 `project_create_shader` 覆盖并回报
   `existed_before`。理由：主题契约里没有 `overwrite` 开关，无声覆盖是数据破坏；
   着色器契约的历史形态已定，本批**不改**另一组的契约。
3. `running_game_move_player_to_target` 的速度来源不在契约里（契约只有 `run`）：
   取值顺序 agent `max_speed` → 节点 `speed` 属性 → 200.0（迁移源文档化的默认值），`run` 时 ×2；
   回答里带 `speed` / `speed_source` / `run_multiplier` 让调用者可核对。
4. 到达判定半径：契约无 `arrival_radius` 时默认 10.0（迁移源默认值）；超时由框架 deadline 处理
   （与 TASK-011 先例一致，而不是自己造一个定时器）。
5. `os_list_android_devices` / `os_deploy_to_android_device` 的 adb 调用用**阻塞** `OS::execute`
   （与引擎自己的 Android 导出器同源）；导出那一段用非阻塞 `OS::create_process` + 轮询。
6. `android_shared.cpp` 的 `export_presets_read`：只有 `EditorExport::get_export_preset_count() > 0` 时才用
   引擎的已加载列表；否则回落到 `ConfigFile` 读同一个文件。**原因**：`EditorExport` 只在
   `NOTIFICATION_ENTER_TREE` 读一次配置（`editor/export/editor_export.cpp:248-252`），
   若文件在编辑器启动后才写入，旧逻辑会回答「0 个预设，source=editor_export」——**假空**。
   这是实现期发现并修掉的缺陷（§12 决策记录）。
7. `editor_get_navigation_info`（TASK-034 交付）在本批被重新用作**核实工具**，其输出形状
   （`regions` 是数组而非字典）在本报告的脚本与 doctest 中都按数组处理；**未改动该工具**。

**文档/契约层面的观察（不改契约，只报）**

- `docs/tool-groups-b5.json` 的 `_comment`/`counts` 仍是历史值（各批不动别人的清单头），
  真实一致性由 `check_tool_groups.py` 判定（§7）。
- 契约里 `editor_set_shader_material.material_slot` 与 `editor_simulate_key.keycode` 的 `string` 类型
  已由决策者裁决保留（§4.2），本批**未改**。

**风险 / 局限**

1. 本机无 Android SDK/设备/导出模板：`os_deploy_to_android_device` 的「导出→装→起」全程成功路径
   **未被本批实测**（工具的实现按引擎 CLI 导出 + adb 的既有路径编写，能力检查在任务创建前完成）。
   已列入下一批可验证项。
2. 烘焙的场景是**单个 plane**（0→2 多边形）；更大/带洞几何的烘焙鲁棒性未覆盖。
3. `navigation_layer_names_of_mask` 只在工程设置里已定义 `layer_names/.../layer_N` 时给名字，
   未定义时给空串（不伪造名字）——这是**诚实**但调用者要能接受空串。
4. 移动工具在「无 SceneTree/无 World3D」时会 `-32000`（不在 viewport 里），这一点在 doctest 里
   只能测到参数与拒绝路径（构造 `NavigationRegion2D/3D` 在全量 `--test` 下会 SIGSEGV，见 REPORT-016 的同类记录），
   真实成功路径只在活线证据里覆盖。

---

## 10. 复现命令

```powershell
# 0) 重建（cmd，串行，不静默，tests=yes）——脚本自己会打 --version
cd /d F:\RustProjects\godot-mcp-pro\code\godot\modules\mcp_server\scripts
set MCP_BUILD_LOG=%TEMP%\mcp036_build.log
build_local.cmd -Force
bin\godot.windows.editor.x86_64.console.exe --version     # 4.8.dev.custom_build.b547d1a1d == HEAD b547d1a1df

# 1) 本模块 doctest（门③）
bin\godot.windows.editor.x86_64.console.exe --headless --test --test-case="[MCPServer]*"
# 2) 全量回归（门④）
bin\godot.windows.editor.x86_64.console.exe --headless --test

# 3) 门①（9 组各一次；脚本自己起 9888/9889 并只杀自己起的 pid）
for /d ... powershell -NoProfile -ExecutionPolicy Bypass -File check_contract_subset.ps1 -Group <g>

# 4) 门②（本批活证据，55 个 check + evidence/ 目录与 sha256）
powershell -NoProfile -ExecutionPolicy Bypass -File mcp036_b5_navigation_theme_export_android_evidence.ps1

# 5) 门⑤
powershell -NoProfile -ExecutionPolicy Bypass -File accept_m1.ps1     # ×2

# 6) 门⑥ 三段
python modules\mcp_server\scripts\check_narrowing_points.py            # scanned == pinned == 69
python modules\mcp_server\scripts\check_narrowing_points.py --coverage
powershell -NoProfile -ExecutionPolicy Bypass -File mcp031_gate6_coverage_probes.ps1   # 101/101

# 7) B5 收口机器校验
python modules\mcp_server\docs\scripts\check_tool_groups.py --batch B5
python modules\mcp_server\docs\scripts\check_tool_groups.py --check-completeness

# 8) 回归脚本
powershell ... -File mcp035_b5_tilemap_shader_physics_evidence.ps1   （+ mcp034 / mcp033 / mcp032 / mcp030）
```

**本批改动文件的 sha256**（本批**没有**动契约/映射/生成器，故给的是实现与证据脚本的指纹，
供独立验收逐字节复核）

| 文件 | sha256 |
|---|---|
| `tools/theme_shared.cpp` | `1d433c09387442198a284e54fa9f2f8ad6028959ac1c053e5165a3c32c969c20` |
| `tools/project_theme_write.cpp` | `2059d734483cdc0a7a8ea736bc1de6f3119bb446baade9c7132ec7b8a9dd5e40` |
| `tools/project_theme_read.cpp` | `870fc911fd30456f7ff9dc1148a27326c23e3785cb29b962ec5f4fd7f67e2f79` |
| `tools/android_shared.cpp` | `e47b8c3b3b07379456b5b3d3cb86f0d0fdc741c9f77a4aea54003bd115a58f1a` |
| `tools/project_export_read.cpp` | `1b6ac619930469bbde3b87eb690a1903f3a051dd649c37d64b63ac582b472a5c` |
| `tools/project_android_read.cpp` | `34af439f2d183d753fb9478c301c8c34d0cafa96ef14b61746621ab7cc04ed19` |
| `tools/os_android_read.cpp` | `b172d2c1349cb415de2d4fc0bc6f3375fb795e00d7d0088d98cfe9b102d080d2` |
| `tools/os_android_write.cpp` | `3f3076d66585a3e51ca73d8cb23d36295d2754f74a302c69e9bc28403d27230f` |
| `tools/editor_navigation_write.cpp` | `f394d82d86f1998d00a24438bf21d95c5377e7bd75673c2b364cec832ebf5efd` |
| `tools/running_game_navigation_write.cpp` | `8b2d3148ae57b37617043c2cf70490a0ba89bd8fa7a8f0f5ea0b2d5f168613d4` |
| `tools/registration.cpp` | `3cac4499d0855c56a96fdca391cd8d0f40ac8af6852388b1b0bedad965cc2dc5` |
| `tests/test_mcp_server.h` | `9bdf2d437caf044b87ec2b581a6bd9daa1343acba52a4dd4f26ca2e27a2d34af` |
| `docs/tool-groups-b5.json` | `85bb783e29e6e02879e5c60769bdf0ffcc60a9fa2c9ad6cea8fde43acf2799fb` |
| `scripts/check_narrowing_points.py` | `f5b5b03466b7269bc2f6cb7ca53282e614345b3a363b859840207e7c45e7325b` |
| `scripts/mcp031_gate6_coverage_probes.ps1` | `ba561b20fc0bb31a85cf1d15c4f4c833ee4ded56bf85e5b82fc4ae0f36b12d57` |
| `scripts/mcp036_b5_navigation_theme_export_android_evidence.ps1` | `b9d2b926a2659ff59e34190a53be52c8f6268bf74e9f1a7d8f237b2bd3f0cd59` |

（`docs/tool-groups-b5.json` 的 sha256 与 §7 的 `check_tool_groups.py --batch B5` 打印值一致：
`85bb783e29e6e02879e5c60769bdf0ffcc60a9fa2c9ad6cea8fde43acf2799fb`。）

---

## 11. 提交

```
6e18a00400  feat(mcp_server): B5 batch 4 - navigation/theme/export/android tools (171/171)
            新增 8 组 14 工具 + 2 个共用头文件；registry 计数推进到 171/148/69/46；
            tool-groups-b5.json 八组 implemented=true 且修正 editor_physics_write 注记；
            门⑥ 新增 31 个 pin；TASK-036 doctest 块（含 count 断言重排）。

05d9bbce37  fix(mcp_server): never answer a false-empty preset list, plus TASK-036 wire evidence and report
            android_shared.cpp：只有引擎已加载的预设列表才作数，否则回落到文件
            （旧逻辑会把「引擎还没重读」答成「0 个预设」的假空）；
            + mcp036 活证据脚本（59 checks, exit 0）+ 本报告。

工作树收尾：只剩既有未跟踪物 .graphifyignore / build-m0.cmd / graphify-out/ / install-deps-m0.cmd；
未 push。基线 HEAD（本批开始前）= b547d1a1dfb17c75bfdb564acac515a56275e868。
```

---

## 12. 决策记录（供决策者追加到 hof-rs `DECISIONS.md` 的摘要）

> PLAYBOOK §1/§7.2 明令本 fork **不得**新建 `DECISIONS.md` 或竞争性规范文档，决策日志在
> `F:\moonbit-hof-rs\DECISIONS.md`（对本模块只读）。因此本批的决策记录由**本报告 + 提交信息**承担，
> 下表即决策者可直接转录的条目；这也是 TASK-023/025 等批次的既有处置方式。

| 触发问题 | 考虑的选项 | 最终选择 | 理由 / 回滚点 |
|---|---|---|---|
| 「烘焙」在引擎里是异步 API | 同步等一帧 / 假成功 / GDR-20 延迟 + 轮询 | **GDR-20 延迟 + 轮询 + 另一工具复核** | §2；回滚点：只改本工具的注册方式，不影响其它组 |
| `EditorExport` 的空缓存会把已写文件答成「0 预设」 | 保持原样 / 回落 `ConfigFile` | **只在引擎列表非空时用引擎列表，否则读文件** | §9 偏离 6；回滚点：`android_shared.cpp` 一个 if |
| `theme_set_stylebox` 的可选参数校验发生在主题加载之后 | 保持 / 把校验前移 | **前移**（`stylebox_arguments_check`） | 参数错误应先于 I/O 报出；回滚点：删掉两处调用之一 |
| 预设可读但 SDK 缺失 | 拒绝 / 回答并标注不可导出 | **回答** | §9 偏离 1；回滚点：`project_android_read.cpp` 一处分支 |
