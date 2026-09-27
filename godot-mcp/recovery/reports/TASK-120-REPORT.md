# TASK-120 — 按 TASK-119 独立验收的 fail 修证据机制

> **本文每个数字都来自本机本轮真实命令的输出**（台账 `python tools/tool_coverage.py`、
> 反例自证脚本、`git show HEAD:godot-mcp/coverage.json` 的前后对照、c8 会话的引擎输出）。
> 「应该可以 / 大概通过」这类转述一律不写；没做到的写在 §E5。
>
> **引擎侧零改动**（`godot/modules/mcp_server/` 一个字节未改，`git status` 可查），因此按铁律 7
> **未触发**两变体重建、未跑十道门、未跑 accept_m1、未 push 引擎仓。
> `projects/` 下的 20 款正式工程只读未动；本轮只往 `runs/_exercises/ex_grid/c8-task120`（既有忽略范围）
> 与 `projects/_exercises/ex_grid/.godot/`（既有忽略）写运行产物。

---

## 0. 一句话结论与修正后的最终口径

**TASK-119 判 fail 的两条 HIGH、一条 MEDIUM、四条 LOW 全部处理完毕。**

1. **见证机制不再是「那次读调用发生过」**：`verify_readback()` 增加四条硬规则 ——
   **A1** 见证工具必须是读类动词（写工具自己的回包不算）、**A2** 被采用的见证调用必须**晚于**
   被见证工具的至少一次调用（同 run、seq 更大）、**A3** `expect` 至少一条**带值**（拒裸键名）、
   **A4** 不得**只**声明 `expect_absent`。违背即拒签、理由进 rejected 列表。
2. **51 条声明全部按新规则重判**：14 条不合格，逐条用**见证回包里真实存在的值**补强，
   **0 条降级**；其中 3 条 input recording 改用**真读调用 + 写后值**重建见证。
3. **通道↔verb 交叉校验**进了 `load_channels()`，违规**加载期硬失败**；两条误声明修正：
   `os_deploy_to_android_device` → `file_effect`、`editor_capture_screenshot` → `payload`。
4. **17 条补边界用真调用**：新批次 `c8-task120` 给每条注入一次
   `-32602 Unknown parameter 'undeclared_probe'`（注册器门先于 handler），**没有动门槛**。
5. **四处标签修正**：distinct **172**（不是 171）现在由台账表头自己打印；
   `needs_an_external_device` 逐条状态；新增 `engine_not_implemented` 类；`basis` 标明是通道级模板。

```
$ cd F:\moonbit-hof-rs\godot-mcp && python tools\tool_coverage.py          （真实输出）
tool_coverage: mode=all-runs runs=112 trace_files=182 calls=8729 distinct=172
  buckets: 0=5 1-4=0 >=5=172 | status: 达标=169 计数达标缺证据=3 未达1-4=0 未达0=5
  registry: 74 members, 69 drift
```

| 指标 | TASK-118（被验收基线） | TASK-120（本轮） | 变化 | 原因 |
|---|---|---|---|---|
| run / trace / `tools/call` | 111 / 180 / 8712 | **112 / 182 / 8729** | +1 / +2 / **+17** | c8 批次 17 次被拒调用 |
| 出现过的工具名 | 172 | **172** | 0 | c8 只调用已出现过的工具 |
| **达标** | 152 | **169** | **+17** | 17 条边界**补上了**（不是放宽门槛） |
| **计数达标缺证据** | 20 | **3** | **−17** | 同上 |
| **未达(0)** | 5 | **5** | 0 | scope-excluded 5 条不变 |
| 档位 pixel/file/readback/count_only/no_calls | 34/24/111/3/5 | **34/24/111/3/5** | 0 | 档位是另一把尺子，本轮没动它 |
| 声明 / 复核通过 / 被拒 | 51 / 51 / 0 | **51 / 51 / 0** | 0 | 14 条被**补强**而非删除 |
| 登记表 members/drift/reclassified | 74 / 69 / 69 | 74 / 69 / 69 | 0 | 一条没删 |

**177 = 达标 169 + 计数达标缺证据 3 + 未达(0) 5。** 仍缺证据的 3 条是：
`editor_set_auto_dismiss_dialogs`（**引擎未实现**）、`project_get_android_preset_info` 与
`os_deploy_to_android_device`（缺 Android 预设/设备）。

---

## 1. 交付物与证据路径

| 交付物 | 路径 | 说明 |
|---|---|---|
| 台账读者（改规则） | `tools/tool_coverage.py` | A1–A4 四条规则、通道↔verb 校验、标签渲染 |
| 通道声明表 | `tools/tool_channels.json` | 两条通道修正 + `basis_scope: channel_template` |
| 登记表 | `tools/tool_coverage_unreachable.json` | `needs_an_external_device.items`、新增 `engine_not_implemented` |
| 见证修复 | `tools/sessions/_exercises/{ex_anim/h2,ex_audio/h5,ex_nav/h4,ex_particles/h6,ex_rec/h9,ex_write/c4}-manifest.json` | 14 条 `expect` 带值（+3 条改见证工具） |
| c8 批次 | `tools/sessions/_exercises/ex_bound/{c8-session.json,c8-manifest.json}` | 17 条同形状被拒调用 |
| c8 run 产物（不入库） | `runs/_exercises/ex_grid/c8-task120/` | editor 10 次 / game 7 次，malformed=0，verdicts 全 `failed` |
| 反例自证 | `recovery/work/task120/witness_rules_selftest.py` | 20 项 A1–A4 + M1/M2/M2b/M3/M4，全过 |
| 前后对照 | `recovery/work/task120/report_numbers.py` | 用 `git show HEAD:…coverage.json` 对拍，无转抄 |
| 现场重算 | `recovery/tmp/task120/{recon.txt,dossier.txt,selftest.txt,numbers.txt,m4-excluded.*}`（不入库） | 逐条证据 |
| 决策 | `F:\moonbit-hof-rs\DECISIONS.md` **D164** | 六个选项的取舍与否决理由、影响面、回滚点 |

---

## A. 见证规则（TASK-119 的 D2 / D3 / R1 / R3）

### A1. 四条规则与落点

`tool_coverage.py::verify_readback()`（调用点 `build_payload`）：

| 规则 | 代码 | 判据 | 违背时的行为 |
|---|---|---|---|
| **A1** | `witness_verb = verb_of(witness, verbs)` | 见证工具的 verb 必须 ∈ `READ_VERBS`；且不能是被见证工具自己 | 拒签，理由 `TASK-120 A1: … is not a read call (verb=stop)` |
| **A2** | `run_index[run][tool]["seqs"]` | 被采用的见证调用必须晚于被见证工具的**至少一次**调用（同 run、`seq` 更大） | 拒签，理由含 `TASK-120 A2` 与被见证工具的 seq 列表 |
| **A3** | `literal_is_key_only()` = `^"[A-Za-z_][A-Za-z0-9_]*"$` | `expect` 至少一条**带值** | 拒签，理由 `TASK-120 A3` |
| **A4** | `forbidden_literals()` 非空且 `expected_literals()` 为空 | 不得只声明 `expect_absent` | 拒签，理由 `TASK-120 A4` |

**A3 的边界（写清楚，便于复核）**：规则拒的是「裸 JSON 键名 / 裸名字」这一可判形式
（`"position"`、`"damping_min"`、`"Music"`、`"RegionA"`）。**不拒**「本身就是值」的字面量：
`T:res://themes/c4b.tres`、`C:Camera3D`、`L:DirectionalLight3D`、`"baked":true`、`"volume_db":-6`
（`editor_execute_gdscript` 的结果就是那个值）。这条边界写进了台账 §0.1。

### A2. 51 条声明的重判结果

* **14 条不合格 → 全部补强（0 条降级）**，逐条的「旧 expect → 新 expect → 见证 seq/verb」见
  `recovery/tmp/task120/numbers.txt`。摘录：

| tool | 旧 `expect`（裸键名） | 新 `expect`（带值，逐字来自见证回包） | 见证 |
|---|---|---|---|
| `editor_add_audio_bus` | `"Music"` | `"name":"Music"` ; `"index":2` | `editor_get_audio_bus_layout`@22 verb=get |
| `editor_add_scene_instance` | `"Sub1"` | `/Main/Sub1/C4Node2` ; `"name":"Sub1"` | `editor_get_scene_tree`@132 verb=get |
| `editor_add_state_machine_state` | `"Walk"` | `"name":"Walk"` ; `"animation":"Anim2"` | `editor_get_animation_tree_structure`@88 verb=get |
| `editor_add_state_machine_transition` | `"Idle"` | `"from":"Jump"` ; `"to":"Walk"` | 同上 @88 |
| `editor_create_animation` | `"Anim5"` | `"animations":["Anim1","Anim2","Anim3","Anim4","Anim5"` | `editor_list_animations`@23 verb=list |
| `editor_set_node_groups` | `"ex_host"` | `"node_path":"Host"` ; `"groups":["ex_host"]` | `editor_get_node_groups`@143 verb=get |
| `editor_set_particle_material` | `"damping_min"` | `"node_path":"P1"` ; `"initial_velocity_min":40.0` ; `"initial_velocity_max":90.0` | `editor_get_particle_info`@34 verb=get |
| `editor_setup_navigation_agent` | `"max_speed"` | `"path":"Player/NA3"` ; `"max_speed":320.0` | `editor_get_navigation_info`@27 verb=get |
| `editor_setup_navigation_region` | `"RegionA"` | `"path":"RegionA"` ; `"type":"NavigationRegion2D"` | 同上 @27 |
| `editor_setup_physics_body` | `"PB1"` | `/Main/PB1/CollisionShape2D` ; `"name":"PB1"` | `editor_get_scene_tree`@132 verb=get |
| `running_game_move_player_to_target` | `"position"` | `"x":220.86` ; `"y":394.86` | `running_game_get_node_properties`@7 verb=get |

* **37 条原样通过**（含 `editor_bake_navigation_mesh`、`editor_connect_signal`、
  `editor_set_viewport_3d_camera`、`editor_stop_scene` 等，逐条 VERDICT=OK 见 `recon.txt`）。
* **一处必须点名的诚实发现**：`editor_set_particle_material` 原来那条 `expect: ["damping_min"]`
  就算补成「读回 `"damping_min":1.0`」也是**假的证据** —— 那个 1.0 出现在 P2 的回包里，而
  P2 在**写之前**（seq=18 的响应）就已经是 1.0（种子场景自带）；写落在 P4，而 P4 根本没有被读。
  本轮改用 P1 自己的记录（seq=17 的写报告 stored 40.0/90.0，seq=34 的读回同一对值）。
  这条写进了 manifest 的 `why`，正是 A2/A3 要防的东西。

### A3. 三条 input recording 用真读调用 + 写后值重建

| tool | 旧见证（被拒原因） | 新见证 |
|---|---|---|
| `running_game_create_input_recording` | `running_game_stop_input_recording`（verb=**stop**，写工具自己的回包）→ A1 | `running_game_get_node_properties`@18（**写后**读回 `"x":346.0`） |
| `running_game_play_input_recording` | `running_game_get_node_properties`@2 + `expect ["position"]` → A3（且旧口径会取到写前那次） | `…get_node_properties`@22（紧接 replay@21 之后的读回 `"x":151.0`，而 seq=20 是 reset 后的 100.0） |
| `running_game_stop_input_recording` | `…get_node_properties`@2 + `expect ["position"]` → A3 | `…get_node_properties`@18（stop@17 之后的读回 `"x":346.0`，而 seq=2 是 100.0） |

**残留边界（如实写）**：契约里**没有**任何能读回录制器状态的读工具（本机扫描契约：名字含 record/input
的只有这 3 条写工具与 `editor_*` 输入模拟），所以对这三条，**读调用只能证明「被录下来的那段输入真的
驱动了游戏」**（位置从 100.0 变成 346.0/151.0），**不能**证明「录制器的内部状态」。
`expect` 是写后值、见证晚于写，这两条硬规则满足；但「create/stop 本身的效果」仍然只能由
**写工具自己的回包**（`event_count:2` / `recording:false`）说明 —— 而那是被规则明文排除的证据来源。
这条写进了 manifest 的 `why` 与台账 §0.1，请复核者按此判断它的强度。

### A6. 反例自证（`recovery/work/task120/witness_rules_selftest.py`，**20/20 PASS**）

```
$ python recovery/work/task120/witness_rules_selftest.py
PASS  positive control: repaired stop_input_recording signs      seq=18 expect=['"x":346.0']
PASS  A1 non-read witness (audit's D2) is refused                TASK-120 A1: … is not a read call (verb=stop) …
PASS  A1 self-witness is refused                                 TASK-120 A1: …
PASS  witness tool renamed (read verb, wrong payload) -> refused  none of the 1 substantive … payload(s) satisfies …
PASS  witness tool renamed to a never-called read tool -> refused  no `ok=true` substantive call of `editor_get_selection` …
PASS  A2 pre-write witness is refused                            TASK-120 A2: … not later than any of the 2 call(s) of `writer` …
PASS  A2 post-write witness signs (not a blanket reject)         seq=11
PASS  A3 bare-key expect (audit's D3) is refused                 TASK-120 A3: …
PASS  A4 expect_absent without expect is refused                 TASK-120 A4: …
PASS  M2 key renamed -> OLD rule refuses (content gate was live) old: None
PASS  M2 key renamed -> NEW rule refuses                         TASK-120 A3: …
PASS  M2b the value 346.0 -> 0.0 is refused (value-level expect)  none of the 5 … satisfies expect '"x":346.0'
PASS  M3 start-value mutation: OLD rule still signs (the defect)  old signed at seq=2 both before and after the mutation
PASS  M3 start-value mutation: NEW rule refuses (chev 0)         none of the 5 … satisfies expect '"x":346.0'
PASS  M3 mutation demotes the tool off the pass status           status=计数达标缺证据
PASS  un-mutated corpus: NEW rule signs at the post-write read   seq=18 expect=['"x":346.0']
PASS  M1 blanked read payload is not effective evidence          classify(blank)=(False, False)
PASS  M1 substantive read payload IS evidence                    classify(real)=(True, False)
PASS  M4 boundary call present -> 达标                            boundary=1 status=达标
PASS  M4 boundary call removed -> back to 计数达标缺证据          status=计数达标缺证据
checks=20 failures=0
```

* **M2（改见证 payload 里的字面量）**：改名键 → 拒签；把被引用的**值** 346.0 改成 0.0 → 拒签。
* **M3（把写后的读强改回起始值 100.0）——本轮的关键自证**：在**同一份被篡改的语料**上
  同时跑旧规则与新规则 —— **旧规则照签**（`witness_seq=2`，写之前那次读，篡改前后完全一致，
  即「玩家一步没动」也看不出来），**新规则拒签**并让该工具退回 `计数达标缺证据`。
  这就是 TASK-119 判 fail 的那个口子，现在会报警。
* **M1/M4（另两条门）**：空回包不是有效载荷证据；c8 给的那次边界调用一旦拿掉，
  状态立刻退回 `计数达标缺证据`。

**语料级 M4 复核**（真跑台账，把 c8 整批排除）：

```
$ python tools\tool_coverage.py --exclude c8-task120 --md …m4-excluded.md --json …m4-excluded.json
tool_coverage: mode=all-runs runs=111 trace_files=180 calls=8712 distinct=172
  buckets: 0=5 1-4=0 >=5=172 | status: 达标=152 计数达标缺证据=20 未达1-4=0 未达0=5
```

即 **+17 完全来自 c8 注入的那 17 次被拒调用**，不是口径松动。

---

## B. 通道与 verb 一致性（TASK-119 的 D1 / D5 / D6）

* `load_channels()`（现签名 `load_channels(root, names, verbs)`）在原有的「覆盖契约 / 通道名合法」
  之上新增**通道↔verb 一致**校验：
  * **动作动词不得声明 `payload`** —— `read_payload` 只对 `READ_VERBS` 累加（`build_rows`），
    那样的证据门**结构性恒为 0**；
  * **读类动词不得声明** `file_effect` / `pixel_effect` / `editor_state` —— 读类调用的回包**就是**
    测量结果，要求它交画面/文件/内存态增量会把正常读者判成无效。
  * 违规**拒绝运行**（`SystemExit`，逐条打印工具、verb 与通道）。校验后实测：
    `read-verb tools=76 declared payload=76`，**违规 0 条**。
* 两条误声明修正（`tools/tool_channels.json`，`basis` 逐条重写、写明依据）：

| tool | 旧通道 | 新通道 | 依据 | 对判定的影响 |
|---|---|---|---|---|
| `os_deploy_to_android_device` | `payload` | **`file_effect`** | `deploy` 是动作动词，回包不是测量结果；它真正可观测的产物是导出/部署写出的 APK | 仍是 `计数达标缺证据`（本机无预设无设备，`chev=0`），但证据门**不再是结构性不可满足** |
| `editor_capture_screenshot` | `file_effect` | **`payload`** | `capture` ∈ READ_VERBS；契约允许内联 base64 **或**落盘，25 次里只有 15 次有文件效果 | `chev` 15 → **25**，加上 c8 的 1 次边界 → **达标** |

* **D6**：`tool_channels.json` 顶层新增 `basis_scope: "channel_template"` 与 `basis_scope_note`
  （同通道 22/28/51/76 条的 `basis` 逐字相同，只有 `subject` 逐条不同），台账 §0.0 把它作为引用块打印。

---

## C. 17 条补边界（TASK-119 的 D4）

### C1. 跑前检查（铁律 4/5）

```
$ netstat -ano | findstr /c:"9905"      （空）
$ netstat -ano | findstr /c:"9906"      （空）
$ tasklist | findstr /i godot           （空）
$ python recovery\work\task104\check_session.py tools\sessions\_exercises\ex_bound\c8-session.json
  calls : 17 (editor 10 / game 7)   utf8 json : OK   CHECK_SESSION OK
$ powershell -File recovery\work\task104\check_session_ps.ps1 … -Label c8
  PS_PARSE OK c8 calls=17 editor=10 game=7 unique_tags=17
```

（铁律 5 的**双解析**：Python 与 PowerShell 5.1 各自解析同一份会话文件，两者都通过；
会话/清单文件都是 `json.dumps(indent=2)` 的 UTF-8 + LF，可被两侧解析器逐字接受。）

### C2. 注入的调用（不改门槛）

会话 `tools/sessions/_exercises/ex_bound/c8-session.json`：10 条 editor 端、7 条 game 端，
每条**只带一个未声明参数** `undeclared_probe`，由
`tool_registry.cpp:812-855` 的未声明参数门在 **handler 之前**拒绝。引擎逐字回答（17/17）：

```
c8-001 editor_open_scene          -32602 Unknown parameter 'undeclared_probe' … suggestion: path
c8-002 editor_save_scene          -32602 … suggestion: path
c8-003 editor_delete_node         -32602 … suggestion: path
c8-004 editor_set_node_property   -32602 … suggestion: path, property, value
c8-005 editor_get_errors          -32602 … suggestion: max_lines
c8-006 editor_capture_screenshot  -32602 … suggestion: save_path
c8-007 project_edit_script        -32602 … suggestion: content, path, replace, search
c8-008 editor_add_input_action    -32602 … suggestion: action, key
c8-009 project_build_csharp       -32602 … suggestion: configuration, extra_args, rescan, timeout_ms
c8-010 project_validate_scripts   -32602 … suggestion: include_errors_only, paths
c8-011 running_game_capture_screenshot        -32602 … suggestion: save_path
c8-012 running_game_get_scene_tree            -32602 … suggestion: max_depth, named_only, script_filter, type_filter
c8-013 running_game_get_node_property_samples -32602 … suggestion: frame_count, … properties, …
c8-014 running_game_stop_input_recording      -32602 … suggestion: running_game_stop_input_recording accepts no parameters
c8-015 running_game_run_test_scenario         -32602 … suggestion: scene_path, steps
c8-016 running_game_assert_screen_text        -32602 … suggestion: case_sensitive, partial, text
c8-017 running_game_run_stress_test           -32602 … suggestion: action, count
```

台账：`editor: calls=10 malformed_lines=0 verdicts: failed=10`；
`game: calls=7 malformed_lines=0 verdicts: failed=7`。跑后 `tasklist` 无 godot、
`netstat` 9905/9906 无监听。

### C3. 前后对照（逐条，来自 `report_numbers.py` 对拍 `git show HEAD`）

| tool | 通道 | 边界 前→后 | 通道证据 前→后 | 状态 前→后 |
|---|---|---|---|---|
| `editor_add_input_action` | file_effect | 0 → 1 | 122 → 122 | 计数达标缺证据 → **达标** |
| `editor_capture_screenshot` | payload（B 段改的） | 0 → 1 | 15 → 25 | 计数达标缺证据 → **达标** |
| `editor_delete_node` | pixel_effect | 0 → 1 | 5 → 5 | 计数达标缺证据 → **达标** |
| `editor_get_errors` | payload | 0 → 1 | 50 → 50 | 计数达标缺证据 → **达标** |
| `editor_open_scene` | pixel_effect | 0 → 1 | 9 → 9 | 计数达标缺证据 → **达标** |
| `editor_save_scene` | file_effect | 0 → 1 | 77 → 77 | 计数达标缺证据 → **达标** |
| `editor_set_node_property` | pixel_effect | 0 → 1 | 12 → 12 | 计数达标缺证据 → **达标** |
| `project_build_csharp` | file_effect | 0 → 1 | 63 → 63 | 计数达标缺证据 → **达标** |
| `project_edit_script` | file_effect | 0 → 1 | 52 → 52 | 计数达标缺证据 → **达标** |
| `project_validate_scripts` | payload | 0 → 1 | 80 → 80 | 计数达标缺证据 → **达标** |
| `running_game_assert_screen_text` | payload | 0 → 1 | 65 → 65 | 计数达标缺证据 → **达标** |
| `running_game_capture_screenshot` | payload | 0 → 1 | 298 → 298 | 计数达标缺证据 → **达标** |
| `running_game_get_node_property_samples` | payload | 0 → 1 | 122 → 122 | 计数达标缺证据 → **达标** |
| `running_game_get_scene_tree` | payload | 0 → 1 | 123 → 123 | 计数达标缺证据 → **达标** |
| `running_game_run_stress_test` | pixel_effect | 0 → 1 | 5 → 5 | 计数达标缺证据 → **达标** |
| `running_game_run_test_scenario` | pixel_effect | 0 → 1 | 1 → 1 | 计数达标缺证据 → **达标** |
| `running_game_stop_input_recording` | editor_state | 0 → 1 | 1 → 1（见证已 A1/A3 修好） | 计数达标缺证据 → **达标** |

**17/17 达标**，且剔除 c8 后精确退回 152/20（§A6）。

---

## D. 四处标签修正

| 项 | 问题 | 修法 | 落点 |
|---|---|---|---|
| **D7** 171/172 | 一处口述「出现过 171 条」与台账 172 不符 | 台账**表头自己打印** `出现过的工具名（distinct）= 172（= 契约 177 − 0 次 5）`，从生成器里算，不会再口述漂移 | `tool_coverage.py::render_md` + `TOOL-COVERAGE.md` 第 6 行 |
| **D8** 混栏 | `needs_an_external_device` 把**已达标**的 `os_list_android_devices` 与两条只有拒绝分支的同列 | 该栏改为**逐条**表格（tool / 台账状态 / 本机实测 / 证据）+ 逐条说明；`os_list_android_devices` 明确标 `达标`（5 ok + 1 边界） | 登记表 `needs_an_external_device.items` + 台账 §4 |
| **R5** 标签 | `editor_set_auto_dismiss_dialogs` 被混在「缺证据」里，读起来像没做完的测量 | 新增顶层 `engine_not_implemented` 类；台账 §4 单开一节，§0.0「仍不达标」表里理由改印 `引擎未实现：-32000 Not implemented…（不是缺证据）`；行上带 `ledger_class` | 登记表 + `tool_coverage.py` |
| **D6** basis | `basis` 看起来像逐条论证，其实是按通道套模板 | `basis_scope: channel_template` + 说明块打印进 §0.0 | `tools/tool_channels.json` + 台账 §0.0 |

**D3 的 `-32000` 计数要更正 TASK-119 的说法（如实）**：该工具 7 次调用**不是**「7/7 全是
`-32000 Not implemented`」——真实切分是 **5 次参数合法输入全部 `-32000 Not implemented`
（seq 74-78）**，另 **2 次是参数校验拒绝（`-32602` missing/mistyped `enabled`，seq 79-80）**。
结论不变（成功分支在本引擎构建里不存在），但数字按实测写。

---

## E. 收尾

### E1. 台账与前后口径

见 §0 的表。命令、逐条前后对照、`still_short` 逐条理由都在
`recovery/tmp/task120/{numbers.txt,recon.txt}`；`coverage.json` 的
`channel_delta.still_short` 现在只剩 8 条（3 条缺证据 + 5 条 0 次）。

### E2. 决策与提交

* `DECISIONS.md` **D164**：六个选项（含被否决者及理由：只降级不修规则 / 要求「同一次写」/
  强制键值对 / 降门槛 / 只论证不注入 / 校验只报警）与影响面、回滚点。
* 主仓提交（**只按消息引用，不写哈希**：本报告与决策自己就在其中一次提交里）：

```
1. feat(godot-mcp): TASK-120 (D164) - tighten the readback witness rules (read-verb only,
   after the write, value-carrying expect, no bare expect_absent), cross-check channel vs
   verb, and give the 17 boundary-less tools a real refused call (batch c8)
2. docs(godot-mcp): TASK-120 - the report and the D164 decision record
3. chore(godot-mcp): TASK-120 - refresh the ledger once more after the decision record
   (generated_utc only; every number identical to the one quoted in the report)
```

显式入库：`tools/tool_coverage.py`、`tools/tool_channels.json`、
`tools/tool_coverage_unreachable.json`、6 份 manifest、`tools/sessions/_exercises/ex_bound/`、
`TOOL-COVERAGE.md`、`coverage.json`、`recovery/work/task120/`、本报告、`DECISIONS.md`。
**不入库**：`runs/`（含 `c8-task120`）、`projects/_exercises/ex_grid/.godot/`、`dist/`、
`recovery/tmp/`（既有忽略）。

### E3. 铁律遵守情况（含**两处违例**，如实记录）

| 铁律 | 情况 |
|---|---|
| 1 禁止 shell 重定向 | **两处违例**：早期两条**诊断**命令用了 `2>&1`（把 stderr 并进管道）与一次 `> $null 2>&1`（丢弃输出），均在 `recovery/work/task120/inspect.py` 的侦察阶段，**未写任何工件**；发现后本轮其余命令一律只用管道/工具自带捕获，引擎 stdout/stderr 全程由 `run_game_session.ps1` 的 `Start-Process -RedirectStandardOutput/…` 拥有。 |
| 2 破坏性命令默认拒绝 | 未执行任何删除/覆盖；驱动脚本自身的 `Remove-InOutRoot` 只作用于 `runs/_exercises/ex_grid/c8-task120`（前缀断言）。 |
| 3 构建与运行从 cmd 启动 | c8 会话经 `cmd` 调用 `run_game_session.ps1`，引擎由该脚本经 `cmd.exe /c` 启动；台账重算也走 `cmd`。 |
| 4 唯一端口 + 跑前查进程与端口 | 9905/9906（c6/c7 用 9901-9904），跑前跑后都查了 `netstat` 与 `tasklist`，跑后无残留。 |
| 5 会话先 Python + PS 5.1 双解析 | c8-session 与 c8-manifest 都过了 `check_session.py` 与 `check_session_ps.ps1`。 |
| 6 改模块就重建两变体 + 十道门 + accept_m1 + push | **未触发**：`godot/modules/mcp_server/` 零字节改动（`git status -- godot-mcp/godot/modules` 为空）。 |
| 7 不改机器安全设置 | 未改 PATH/环境变量/证书/防火墙；c8 全部在本进程内起引擎，结束即回收。 |

### E4. 剩余项（**没有做完 / 做不到**的）

1. **三条 input recording 的见证强度上限**（§A3）：契约里没有能读回录制器状态的读工具，
   所以「create/stop 本身的效果」仍无法由**读调用**证明 —— 现在能证明的是「被录下的输入真的驱动了
   游戏（写后位置 ≠ 起始值）」。要真解决需要引擎新增一个读类工具（例如 `running_game_get_input_recording`），
   这是**引擎能力**问题，本轮无权也不应随手加。
2. **两条 Android 工具的达标仍只差外部条件**：`project_get_android_preset_info` 需要工程里的 Android
   预设，`os_deploy_to_android_device` 还需要真机/模拟器；本轮**没有**造假预设（登记表逐条写明）。
3. **c8 用 editor+game 两个端点各一批**：17 条被拒调用**没有**在同一 run 内同时覆盖两个端点
   （驱动脚本按 `port` 分相），所以 `boundary` 的证据来自同一 run 的两个 trace 文件；
   这与既有批次同构，但不是「一次进程内 17 条连续」。
4. **M1 的语料级复刻用 classify 级等价检查替代**（§A6）：TASK-119 的 M1 是在 `runs/` 副本上清空
   `project_get_info` 的载荷；本轮没有再造副本，改为直接验证读者判定（空回包 → 无效载荷 →
   `read_payload` 不累加）。M4 则做了**语料级**复核（`--exclude c8-task120`）。
5. `editor_set_auto_dismiss_dialogs` **仍不是达标**，只是标签正确了（引擎未实现，无成功分支可测）。

### E5. 复现指令（全部只读或只写 scratch）

```
cd F:\moonbit-hof-rs\godot-mcp
python tools\tool_coverage.py                                  # 重算台账（口径数字）
python recovery\work\task120\witness_rules_selftest.py         # 20 项反例自证
python recovery\work\task120\report_numbers.py                 # 前后对照（对拍 git HEAD）
python tools\tool_coverage.py --exclude c8-task120 --md recovery\tmp\task120\m4-excluded.md ^
                               --json recovery\tmp\task120\m4-excluded.json   # M4：退回 152/20
```
