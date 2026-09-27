# TASK-118 — 覆盖循环收口批次：按工具声明证据通道的达标口径 · 四条 `count_only` 收口 ·
# `editor_simulate_*` 登记为 scope-excluded · 三件 Android 工具按实测登记为 needs-an-external-device

> **本报告的每一个数字都来自本机真实命令的逐字输出**，没有从任何报告表格转抄。
> 「应该可以 / 已经通过」这类转述一律不写；没做到的写在 §E。
>
> **引擎侧零改动**（`godot/modules/mcp_server/` 一个字节未动），因此按铁律 7 **未触发**
> 两变体重建、未跑十道门、未跑 accept_m1、未 push 引擎仓。
> `projects/` 下 20 款正式工程与它们的历史 `runs/` **只读未动**（本轮只往
> `projects/_exercises/ex_grid` 之外没写任何工程文件；见 §D 的产物清单）。

---

## 0. 一句话结论与如实边界

**A（通道口径与声明表）、B（四条 `count_only` 收口）、C（5 条 `editor_simulate_*` 登记为
scope-excluded）、D（3 条 Android 按实测登记）、E（台账刷新 / 决策 / 提交 / 本报告）全部完成。**

1. **达标口径已改为「该工具声明的那条通道上的内容级证据」**，声明表
   `tools/tool_channels.json` 覆盖 177/177 条契约工具（缺一条 `tool_coverage.py` 直接拒绝运行）。
   台账随之从 **达标 106 → 152**、`计数达标缺证据` **63 → 20**、0 次 **8 → 5**，
   而**旧口径达标、新口径不达标的工具是 0 条**（这一栏为空是这次口径变更自洽的关键指标）。
2. **四条 `count_only` 全部收口**：`editor_connect_signal` / `editor_add_gridmap` /
   `editor_set_node_script_batch` 在新批次 `runs/_exercises/ex_grid/c6-task118` 里各拿到
   **同一 run 内的内容级见证读**；`running_game_find_node_when_available` 是读类动词，
   它成功的回包本身就是测量结果，同一批次里补了 5 次真成功 + 1 次超时边界。
   台账里这四条现在都是 **`readback` 档位 + `达标`**。
3. **5 条 `editor_simulate_*` 正式登记为 `scope-excluded`（不是不可达）**，与 `unreachable`
   **分栏计数**；登记表里写明源码行与「将来何时可测」。
4. **3 条 Android 工具按实测登记为 `needs-an-external-device`**：本轮**推翻了**「本机没装 Android SDK」
   的既有说法 —— SDK **装**在 `C:\Program Files (x86)\Android\android-sdk`（adb 1.0.41 / 36.0.0），
   只是不在 PATH；真缺的是**设备**与**Android 预设**。
   `os_list_android_devices` **达标**（真跑 adb、真答空设备表），另两条**只有拒绝分支**（如实登记）。

**必须同时说清的边界**：

* **17 条工具「通道证据充足但没有边界调用」，本轮没有把它们推成达标**。旧口径的 `达标` 一直要求
  「边界≥1」，本轮只被授权改**证据通道**，没有被授权改边界门槛。这些逐条列在台账 §0.0
  （例：`editor_save_scene` 77 次文件效果 / 0 次边界；`running_game_capture_screenshot` 298 次载荷 /
  0 次边界）。要改这一栏需要另一次显式口径决策。
* **`os_list_android_devices` 的达标需要一个进程内 PATH 前缀**：本机 SDK 的 `platform-tools` 不在
  PATH，本轮**只在这次会话进程内** prepend（`set "PATH=...;%PATH%"` 后启动驱动脚本），
  **没有改用户机器的 PATH / ANDROID_HOME，也没有安装任何东西**。工具自己回的
  `adb_present:false` 是在说它配置里的绝对路径为空 —— 而它**确实执行了** adb 并拿到空设备表
  （`source:"adb devices -l"`）。
* **`project_get_android_preset_info` 与 `os_deploy_to_android_device` 未达标**：本仓工程
  **没有任何** Android 预设，前者 6 次全部 `-32000`（含 1 次 `-32001` 边界），后者 6 次全部
  `-32001`/`-32602`。**没有构造假的 Android 预设来凑一个 ok 回包**。
* **`editor_set_auto_dismiss_dialogs` 仍是 `count_only`**：provider 恒为 `-32000 Not implemented`
  （引擎没有进程级开关），声明 `editor_state` 后它**没有**被推成达标 —— 这是设计使然，不是本轮缺陷。

---

## 1. 交付物与证据路径

| 交付物 | 路径 | 说明 |
|---|---|---|
| 通道声明表 | `tools/tool_channels.json` | 177 条；每条的 `channel` / `subject` / `basis` |
| 声明表生成器 | `recovery/work/task118/gen_channels.py` | 契约与声明表不一致时**拒绝生成**（missing/extra 都报错） |
| 台账读者（改口径） | `tools/tool_coverage.py` | 新增通道加载与校验、通道证据计数、通道口径 `status`、台账 §0.0 |
| 台账（重算） | `TOOL-COVERAGE.md` / `coverage.json` | 111 run / 180 trace / 8712 调用 / 172 个出现过 |
| c6 会话与声明 | `tools/sessions/_exercises/ex_close/{c6-session.json,c6-manifest.json}` | 29 次调用；**3 条**内容级见证声明 |
| c7 会话与声明 | `tools/sessions/_exercises/ex_close/{c7-session.json,c7-manifest.json}` | 18 次调用；Android 能力探针 |
| c6 run | `runs/_exercises/ex_grid/c6-task118/`（不入库） | editor trace 23 次（failed=3 / ok_effect=1 / ok_file=1 / ok_no_effect=18）、game trace 6 次（failed=1 / ok_no_effect=5），malformed 0 |
| c7 run | `runs/_exercises/ex_grid/c7-task118/`（不入库） | editor trace 18 次（failed=13 / ok_no_effect=5），malformed 0 |
| 登记表更新 | `tools/tool_coverage_unreachable.json` | `H7.still_out`（scope-excluded）、`H8.external_device`（实测）、两个顶层分栏、`reclassified` 66→69 |
| 派生脚本 | `recovery/work/task118/{mk_manifests,reclassify_c6,report_numbers,show_witnesses,inspect_evidence,find_witness}.py` | 全部可重跑；`reclassify_c6.py` **幂等**（第二遍输出 `[]`） |
| 决策 | `F:\moonbit-hof-rs\DECISIONS.md` **D163** | 六个选项的取舍与否决理由、影响面、回滚点 |

---

## A. 按工具声明证据通道的达标规则（任务书 A 段）

### A1. 规则（写进 `tool_coverage.py` 与台账 §0.0）

每条契约工具声明**一条**权威证据通道，`达标` 只在该通道上以**内容级证据**判定：

| 通道 | 判据（内容级） | 声明条数 |
|---|---|---|
| `file_effect` | `ok_file_effect_observed` —— 盘上的文件真的变了 | 22 |
| `pixel_effect` | `ok_effect_observed` —— 渲染出的画面/视口真的变了 | 28 |
| `editor_state` | **另一次独立读调用**在同一 run 内 `ok=true`、回包是实质载荷，且回包里**逐字**包含被写的值（即既有 `witness_read` + `expect` 机制；本工具回到 trace 里复核） | 51 |
| `payload` | `ok=true` 且回包是实质载荷（读类动词的回包**就是**测量结果） | 76 |
| **合计** | | **177** |

* 声明依据与逐条 `basis` 写在 `tools/tool_channels.json`，并**逐条**打印在 `TOOL-COVERAGE.md` §0.0
  （177 行的 `subject` + `basis` 表）。举例：写脚本/写场景 → `file_effect`；影响画面的运行期操作 →
  `pixel_effect`；编辑器 GUI 内存态（选中、输出日志、插件表、文件系统扫描、内存活场景）→ `editor_state`；
  只读查询 → `payload`。
* `达标` 的两个旧门槛**原样保留**：调用≥5、边界≥1。变的只是证据那一格。
* 旧口径仍留在 `coverage.json`（`status_legacy` / `effective`），任何「达标数变化」都能拆成
  「口径变化」与「真实新证据」两部分。

### A2. 按通道的达标计数（`python tools/tool_coverage.py` 的真实输出）

| 通道 | 声明 | 有通道证据 | 通道证据观测数 | 达标 | 计数达标缺证据 | 未达(0) |
|---|---|---|---|---|---|---|
| `file_effect` | 22 | 22 | 484 | 17 | 5 | 0 |
| `pixel_effect` | 28 | 28 | 238 | 23 | 5 | 0 |
| `editor_state` | 51 | 45 | 45 | 44 | 2 | 5 |
| `payload` | 76 | 74 | 5933 | 68 | 8 | 0 |

### A3. 因通道声明而新达标 **44 条**（旧口径它们达不到）

`editor_add_scene_instance` `editor_play_scene` `editor_stop_scene` `editor_rename_node`
`editor_connect_signal` `editor_disconnect_signal` `editor_set_node_groups` `editor_set_node_selection`
`editor_remove_node_selection` `editor_remove_output_log` `editor_reload_plugin`
`editor_rescan_project_filesystem` `editor_set_viewport_3d_camera` `running_game_create_input_recording`
`editor_set_node_script` `editor_create_animation` `editor_add_animation_track`
`editor_set_animation_keyframe` `editor_remove_animation` `editor_set_physics_layers`
`editor_setup_physics_body` `editor_add_mesh_instance` `editor_setup_camera_3d` `editor_setup_lighting`
`editor_set_material_3d` `editor_setup_world_environment` `editor_add_gridmap` `editor_add_audio_player`
`editor_add_audio_bus` `editor_set_audio_bus_property` `editor_add_audio_bus_effect`
`editor_set_control_theme` `editor_create_animation_tree` `editor_add_state_machine_state`
`editor_remove_state_machine_state` `editor_add_state_machine_transition`
`editor_remove_state_machine_transition` `editor_set_blend_tree_node`
`editor_set_animation_tree_parameter` `editor_setup_navigation_region` `editor_setup_navigation_agent`
`editor_set_navigation_layers` `editor_create_particles` `editor_set_node_script_batch`

（台账 §0.0 逐条给出声明通道、累计、边界、通道证据、证据路径与判定依据。）
**被新口径降级：0 条。**

### A4. 声明通道上**仍不达标 25 条**（逐条原因，台账 §0.0 同表）

| 原因 | 条数 | 工具 |
|---|---|---|
| 通道证据充足，但**没有边界调用**（旧门槛保留，未放松） | 17 | `editor_open_scene` `editor_save_scene` `editor_delete_node` `editor_set_node_property` `editor_get_errors` `editor_capture_screenshot` `running_game_capture_screenshot` `running_game_get_scene_tree` `running_game_get_node_property_samples` `running_game_stop_input_recording` `project_edit_script` `editor_add_input_action` `running_game_run_test_scenario` `running_game_assert_screen_text` `running_game_run_stress_test` `project_build_csharp` `project_validate_scripts` |
| 通道证据为 0（声明通道上只有拒绝分支） | 3 | `editor_set_auto_dismiss_dialogs`（设计性）、`project_get_android_preset_info`、`os_deploy_to_android_device`（缺设备/预设） |
| 0 次调用（scope-excluded） | 5 | `editor_simulate_key` `editor_simulate_mouse_click` `editor_simulate_mouse_move` `editor_simulate_input_action` `editor_simulate_input_sequence` |

> 说明：17 + 3 + 5 = **25**，与台账 §0.0 的机器输出逐条对齐（上一行那一栏的工具**有**内容级证据、
> 只是没测过失败/拒绝面；第三行那 5 条**没有**任何调用）。

---

## B. 四条 `count_only` 的补法（任务书 B 段）

### B1. 新批次与跑前/跑后检查（铁律 4）

```
pre-c6    netstat LISTENING 9901/9902 -> NONE ; tasklist godot -> NONE
pre-c7    netstat LISTENING 9903       -> NONE ; tasklist godot -> NONE
post-run  netstat LISTENING 9901/9902/9903/9904 -> NONE ; tasklist godot -> NONE
```

两个会话都跑在 `projects/_exercises/ex_grid`（它同时拥有 `assets/meshlib.tres` 与一个**可玩**的
`scenes/main.tscn`，所以一次 run 能同时服务 editor 与 game 两个端点）。端口 9901/9902 与 9903/9904
**互不重叠、都不占用用户端口 9877**。全部通过 `cmd.exe` 启动（铁律 3），
引擎 stdout/stderr 由 `Start-Process -RedirectStandardOutput/-RedirectStandardError` 接管（铁律 1，无 shell 重定向）。

```
runs/_exercises/ex_grid/c6-task118  editor: calls=23 malformed=0
    verdicts: failed=3, ok_effect_observed=1, ok_file_effect_observed=1, ok_no_effect_observed=18
    game  : calls=6  malformed=0  verdicts: failed=1, ok_no_effect_observed=5
runs/_exercises/ex_grid/c7-task118  editor: calls=18 malformed=0
    verdicts: failed=13, ok_no_effect_observed=5
```

### B2. 逐条：见证读与逐字 `expect`

| tool | 见证读（同 run） | `expect`（逐字） | 逐字回包 |
|---|---|---|---|
| `editor_add_gridmap` | `editor_get_scene_tree` @c6 seq=9 | `"name":"GM6"` ; `"type":"GridMap"` | 场景树里 `{"name":"GM6",...,"type":"GridMap"}`（同一个树里 GM7..GM10 也在；边界探针的 GMX **不在**） |
| `editor_set_node_script_batch` | `editor_execute_gdscript` @c6 seq=16 | `S:res://src/Paddle.cs` | `{"result":"S:res://src/Paddle.cs","result_type":"String"}` |
| `editor_connect_signal` | `editor_list_signal_connections` @c6 seq=23 | `"method":"_c6_a"` ; `"source":"Ball"` | `{"connections":[{"method":"_c6_b",...},{"method":"_c6_a","signal":"visibility_changed","source":"Ball","target":"."},...],"count":5,"counts":{"all":172,"internal":167,"user":5},"scope":"user"}` |
| `running_game_find_node_when_available` | **不需要**（读类动词，回包即测量） | —— | `{"found":true,"name":"Main","node_path":"/root/Main","type":"Node2D"}` ×5（Main/Ball/PaddleLeft/ScoreRight/`/root/Main/WinLabel`），边界：`{"code":-32000,...,"timeout_ms":1000}` |

**为什么见证工具这么选（TASK-115 的教训）**：`editor_set_node_script_batch` 的见证**不能**用
`editor_get_node_properties` —— TASK-115 已实测它对属性名 `script` 直接 `-32001`
（`c4-v5-task111` seq 141）。本轮改用 `editor_execute_gdscript` 读
`Node.get_script().resource_path`，并在 manifest 的 `why` 里写明。

**旧声明不删除**：TASK-113 那两条被拒声明（`editor_add_gridmap`@`h3-task111`、
`editor_connect_signal`@`c4-v5-task111`）被**移进** `readback_superseded`
（带 `superseded_by` + `superseded_reason`），于是台账的
声明 **51** 条、经 trace 复核通过 **51** 条、内容级逐字命中 **51** 条、**被拒 0 条**（此前被拒 2 条）。

### B3. 台账里的最终档位（这四条）

```
editor_connect_signal                  calls=45 bnd=7 ch=editor_state ev=1 status=达标 tier=readback
editor_add_gridmap                     calls=12 bnd=2 ch=editor_state ev=1 status=达标 tier=readback
editor_set_node_script_batch           calls=56 bnd=1 ch=editor_state ev=1 status=达标 tier=readback
running_game_find_node_when_available  calls=14 bnd=9 ch=payload      ev=5 status=达标 tier=readback
```

`count_only` 档位因此从 **5 → 3**（剩下 `editor_set_auto_dismiss_dialogs` 是设计性的，
另两条是 Android 的拒绝分支）。

---

## C. 5 条 `editor_simulate_*`：正式登记为 **scope-excluded**（任务书 C 段）

登记表 `tools/tool_coverage_unreachable.json` 新增顶层分栏 `scope_excluded`，
并在 `categories.H7.still_out` 里逐条写明：

* **为什么排除（不是不可达）**：它们**编译进了这个构建**、在编辑器端点是注册过的；真编辑器里它们
  需要的东西一定存在 —— 源码原话：*`Input` is created by `Main::setup2` in every engine process,
  so in a real editor these never fail*。它们做不到的是**驱动游戏**：注入的是**编辑器进程自己**的输入队列。
* **依据的源码行**：`godot/modules/mcp_server/tools/editor_input_simulation.cpp:53-112`（文件头注释：
  注入目标与范围规则）、`:121-144`（注入前的前置检查）。
* **将来何时可测**：出现一个「在编辑器侧观测输入」的批次 —— 用 Editorial 侧插件或
  `editor_execute_gdscript` 数 `Input` 事件，并在批次自述里写明「游戏端点不该看到任何东西」。
  在现有 ledger 规则下这样的批次最多到 `ok_no_effect_observed`，只买到计数与边界，买不到档位。
* **分栏统计**：台账 §4 单列一行
  `scope-excluded | 5 | editor_simulate_key … | H7`，**不与 `unreachable` 相加**。

---

## D. 3 条 Android：实测本机能力（任务书 D 段）

### D1. 实测命令与逐字结果

```
where adb
  -> INFO: Could not find files for the given pattern(s).   (exit 1)
set | findstr /i android
  -> JAVA_HOME=C:\Program Files (x86)\Android\openjdk\jdk-17.0.12
     （ANDROID_HOME / ANDROID_SDK_ROOT 未设）
dir /b "C:\Program Files (x86)\Android\android-sdk"
  -> build-tools  cmdline-tools  platform-tools  platforms
"C:\Program Files (x86)\Android\android-sdk\platform-tools\adb.exe" version
  -> Android Debug Bridge version 1.0.41
     Version 36.0.0-13206524
     Installed as C:\Program Files (x86)\Android\android-sdk\platform-tools\adb.exe
     Running on Windows 10.0.26100
"C:\Program Files (x86)\Android\android-sdk\platform-tools\adb.exe" devices -l
  -> List of devices attached
     (空列表；adb daemon 由该命令启动)
grep platform=  projects/**/export_presets.cfg
  -> 只有 Windows Desktop（ex_export 另有 Web）；**没有任何 **platform="Android"**
```

**这推翻了 TASK-114/115 的「本机没有 Android SDK」**：SDK 在，只是不在 PATH、
`ADB_PRESENT` 只看 EditorSettings 里配置的绝对路径 + PATH 解析，所以工具自报 `adb_present:false`。

### D2. 调用证据（`runs/_exercises/ex_grid/c7-task118`）

```
c7-001-os_list_android_devices-ok   (×5, 全部 ok)
{"adb_path":"adb","adb_present":false,"count":0,"devices":[],
 "message":"adb ran and reported no connected device (connect a device, or start an emulator, and make sure
            adb debugging is enabled)","source":"adb devices -l","states":[],"usable_count":0}
c7-006-os_list_android_devices-probe  -> -32602 Unknown parameter 'unexpected'（契约是空 schema）
c7-007-project_get_android_preset_info-ok (×5, 全部 -32000)
{"code":-32000,"data":{"preset_count":1,"presets_file":"res://export_presets.cfg","presets_file_present":true,
 "suggestion":"Add an Android preset in the editor (Project > Export > Add... > Android); this project has 1
 preset(s) and none of them is an Android preset"},"message":"No Android export preset is configured in this project"}
c7-012-project_get_android_preset_info-probe  -> -32001 Export preset 'NoSuchAndroidPreset' not found
c7-013..017-os_deploy_to_android_device-probe (×5, 全部 -32001，skip_export=true 不让导出子进程起来)
c7-018-os_deploy_to_android_device-probe      -> -32602（参数规则：'Windows Desktop' 不是本工具的参数）
```

### D3. 登记结论

| tool | 本次实测 | 声明通道 | 台账状态 |
|---|---|---|---|
| `os_list_android_devices` | 真跑 adb、真空设备表（5 ok + 1 边界） | `payload` | **达标** |
| `project_get_android_preset_info` | 6 次全拒绝（无 Android 预设） | `payload` | 计数达标缺证据（needs-an-external-device） |
| `os_deploy_to_android_device` | 6 次全拒绝（无预设/无设备） | `payload` | 计数达标缺证据（needs-an-external-device） |

登记表 `categories.H8.external_device` 已改写成**实测版**（`measured_on_this_machine` +
`run_evidence` + `measurable_when`），顶层新增 `needs_an_external_device` 分栏；
台账 §4 单列一行 `needs-an-external-device | 3 | …`，**不混进 `unreachable`**。
三条同时加入 `reclassified`（**只加不删**，66 → 69），所以 §4 的「待复核漂移」现在是 **0**。

---

## E. 最终计数（`python tools/tool_coverage.py` 的真实输出）

```
tool_coverage: mode=all-runs runs=111 trace_files=180 calls=8712 distinct=172
  buckets: 0=5 1-4=0 >=5=172 | status: 达标=152 计数达标缺证据=20 未达1-4=0 未达0=5
  registry: 74 members, 69 drift
```

| 指标 | TASK-115（基线） | TASK-118（本轮） | 增量 |
|---|---|---|---|
| run 目录 / trace / `tools/call` | 109 / 177 / 8665 | **111 / 180 / 8712** | +2 / +3 / **+47** |
| 出现过的工具名 | 169 | **172** | **+3** |
| `0` 次 | 8 | **5** | **−3**（只剩 5 条 scope-excluded） |
| **达标** | 106 | **152** | **+46**（新口径新达标 44 + 两条本轮才被调到 ≥5 并达标的 `os_list_android_devices` / `running_game_find_node_when_available`） |
| 计数达标缺证据 | 63 | **20** | **−43** |
| 证据档位 | pixel 34 / file 24 / readback 106 / count_only 5 / no_calls 8 | **pixel 34 / file 24 / readback 111 / count_only 3 / no_calls 5** | readback **+5**、count_only **−2**、no_calls **−3** |
| 内容级声明 | 声明 50 / 通过 48 / 逐字 48 / 被拒 2 | **声明 51 / 通过 51 / 逐字 51 / 被拒 0** | 被拒 **−2** |
| 登记表 `reclassified` | 66 | **69** | +3（成员仍 74，**一条没删**） |
| 登记表 `scope_excluded` / `needs_an_external_device` | ——（混在 H7/H8 里） | **5 / 3** | 新增两个分栏 |

**177 = 152 + 20 + 5**（达标 + 计数达标缺证据 + 未达(0)），逐条可查：
`TOOL-COVERAGE.md` §0.0（声明与通道计数）、§0.2（逐档清单）、§1（177 行总表，
每行带 `声明通道` 与 `通道证据`）、`coverage.json` 的 `channel_delta`（新达标逐条、仍不达标逐条原因）。

---

## F. 本轮**没有**做的事（如实清单）

1. **没有改边界门槛**：17 条「通道证据充足、缺边界调用」的工具没有被推成达标（§A4 第一行）。
   这是**刻意的**——任务书只授权改证据通道。
2. **没有构造 Android 预设**来让 `project_get_android_preset_info` / `os_deploy_to_android_device`
   拿到 ok 回包：它们在 `needs-an-external-device` 栏里如实报「只有拒绝分支」。
3. **没有安装/下载任何东西**：没装 Android 平台组件、没下载导出模板、没改用户 PATH 或环境变量
   （adb 只在 c7 会话进程内 prepend 进 PATH，进程结束即消失）。
4. **没有改引擎**（`godot/modules/mcp_server/` 零字节），故未重建两变体、未跑十道门、未 push。
5. **`editor_set_auto_dismiss_dialogs` 仍是 `count_only`**：设计性的 `-32000`，不是缺陷。
6. **没有清理运行产物**：`runs/_exercises/ex_grid/{c6,c7}-task118/`（含截图，不入库）留在原地，
   两个会话的 `import` 与 `project_build_csharp` 产物写进了 `projects/_exercises/ex_grid/.godot/`
   （既有忽略范围）。需要时整体删除 `runs\_exercises\ex_grid\{c6,c7}-task118\` 即可。

**下一批建议（按价值排序）**

1. **给「边界」单独立法**：若用户接受「通道证据充足即可达标」，20 条工具立刻达标；否则应给它们
   各补 1 次有意义的拒绝/失败调用（多数是「传一个不存在的路径/名字」这类边界）。
2. **Android 那一栏只差外部条件**：接一台设备或起一个模拟器 + 给一个练习工程加 Android 预设，
   就能把 `os_deploy_to_android_device` 的 export→install→launch 全路径与
   `project_get_android_preset_info` 的 ok 分支补成实测。
3. 若用户要动 `editor_simulate_*`：按登记表的 `measurable_when` 设计「编辑器侧输入观测」批次，
   并同步决定 ledger 是否给它一个档位。

---

## G. 提交

```
$ cd F:\moonbit-hof-rs && git log --oneline -4      （只列消息，不写哈希：见下）
chore(godot-mcp): TASK-118 - refresh the ledger once more after the decision record (timestamp only)
docs(godot-mcp):  TASK-118 - the report and the D163 decision record
feat(godot-mcp):  TASK-118 (D163) - judge coverage on each tool's declared evidence channel, drain
                  four count_only tools, and register the simulate/Android families by measurement
docs(godot-mcp):  TASK-117 - the report, the D162 decision record, and the game-loop log note
```

三个提交、顺序与 TASK-114/115 同构（**正文只按消息引用、不写死哈希**：本报告自己就在其中一次提交里，
任何写进正文的哈希都会被「写哈希」这个动作本身改掉；准确哈希请用 `git log --oneline`）：

1. **功能提交** —— `tools/tool_coverage.py`（通道口径）、`tools/tool_channels.json`、
   `tools/tool_coverage_unreachable.json`（scope-excluded / external_device 实测 / 三条 reclassified）、
   两个会话与清单、台账两件、派生脚本；
2. **报告与决策** —— `recovery/reports/TASK-118-REPORT.md` + `DECISIONS.md` D163；
3. **再刷一次台账** —— 台账的 `generated_utc` 每跑一次都会变，所以重跑一次留下时间戳；
   **实测数字逐字不变**（`runs=111 trace_files=180 calls=8712 distinct=172 ;
   buckets: 0=5 1-4=0 >=5=172 ; status: 达标=152 计数达标缺证据=20 未达0=5 ; registry: 74 members, 69 drift`）。

* 显式入库：`TOOL-COVERAGE.md` / `coverage.json`、`tools/tool_channels.json`、
  `tools/sessions/_exercises/ex_close/`、`tools/sessions/_exercises/{ex_grid/h3,ex_write/c4}-manifest.json`
  （两条声明被移进 `readback_superseded`）、`recovery/work/task118/`、本报告、`DECISIONS.md`。
* **没有**入库：`runs/`（既有约定）、`projects/_exercises/ex_grid/.godot/`（既有忽略）、`dist/`、
  以及主仓里 TASK-104 遗留的 `recovery/work/task104/logs/git-housekeeping.{out,err}.txt`
  （不是本任务产物，**未删未提交**）。
* **引擎仓（`F:\moonbit-hof-rs\godot-mcp\godot`）本轮无提交、无 push**：
  `godot/modules/mcp_server/` 一个字节未改。
