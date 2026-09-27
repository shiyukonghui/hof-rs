# TASK-115 — H7 的 15 条按实测一分为二 · H1 的 5 条与 TASK-113 的 3 条见证升档 · SAC 导出探针三问

> **本报告的每一个数字与每一段报错都来自本机真实命令的逐字输出**，没有从任何报告表格转抄。
> 「已经通过 / 应该可以」这类转述一律不写；没做到的写在 §E。
>
> **引擎侧零改动**（`godot/modules/mcp_server/` 一个字节未动），因此按铁律 7 **未触发**
> 两变体重建、未跑十道门、未跑 accept_m1、未 push 引擎仓。
> `projects/` 下 **20 款正式工程**与它们的历史 `runs/` **只读未动**。

---

## 0. 一句话结论与如实边界

**A 段（H7 15 条的分类与练习）、B 段（H1 5 条 + TASK-113 3 条见证恢复）、
C 段（SAC 导出探针三问）、D 段（台账重算 / 登记表改判 / 决策 / 提交 / 本报告）全部完成。**

1. **H7 是一个混合家族，任务书的分类有一半不成立**，这是本轮最重要的更正：
   * 任务书把 `editor_get_test_report` 与 `editor_analyze_screenshot_diff` 归到「不可达」，
     理由是需要「编辑器侧测试运行」。**实测两者都可达**：前者读游戏进程持久化的
     `user://mcp_test_report.json`、没有文件就从本进程累加器诚实回答；后者是**纯 CPU 侧**
     的 `Image::load` / `load_png_from_buffer`，源码自己写着 *no display server is needed …
     also works in a `--headless` process*。两条**都练到「达标」**。
   * 15 条的实测分类：**10 条可达**（已全部练到 ≥5 次）、**5 条按 D59 / GDR-21 的范围决定留在登记表**。
2. **H7 的 7 条写工具够不到「达标」，这是实测结论不是借口**：`runs/_exercises/ex_editor/h7-task115`
   82 次调用里 **0 次**像素变化、**0 次**文件变化
   （`verdicts: failed=19, ok_effect_unavailable=1, ok_no_effect_observed=62`；
   `file_effects: none=82`）。编辑器自己的 GUI 状态**不在**截图与文件效果这两个证据通道里，
   所以它们的最高诚实档位是**同 run 内容级读回**（`readback`），状态仍是 `计数达标缺证据`。
3. **B 段全部成功**：H1 的 5 条 `count_only` 与 TASK-113 被降级的 3 条**全部升到 `readback`**，
   且每条的 `expect` 都是本轮真写进去的值。顺带测出 TASK-113 那条见证**根本写不出 `expect`** 的根因：
   `editor_get_node_properties` 对 `script` 这个名字直接 `-32001`（`c4-v5-task111` seq 141）。
4. **C 段推翻了一个既有说法**：以前的口径是「导出的 exe = 导出模板的拷贝」。
   **实测不是**：默认预设（`embed_pck=false` + Godot 默认 `application/modify_resources=true`）
   导出的 exe 比模板**少 140800 字节**、sha256 不同；关掉 `modify_resources` 之后才**逐字节相同**。
   即 **「模板签名能否带进导出物」取决于 `modify_resources=false`，`embed_pck=false` 不够。**
   这一格**只在未签名的 `4.8.dev` 模板上验证过**；**官方 4.7.1 mono 模板本机没装，
   按任务书要求没有下载，所以「官方签名模板」那一格未测**。

**必须同时说清的边界**：

* **官方 4.7.1-stable mono 导出模板没有安装**（`%APPDATA%\Godot\export_templates\` 下只有 `4.8.dev`）。
  因此探针 ① 的后半问（官方模板 exe 是否 `Valid`）**未测**；任务书要求「模板缺失先报告、
  不要擅自长时间下载」，**本轮没有下载任何东西**。
* **H7 的 7 条写工具到不了「达标」**（见 §0.2）。要改变这一点需要给 ledger 增加第三个证据通道
  （编辑器自身状态的读回），那是口径变更，超出本轮范围，**本轮只如实登记**。
* **`editor_set_auto_dismiss_dialogs` 永远没有成功分支**：它的 provider 是刻意的
  `-32000 Not implemented`（引擎没有进程级 auto-dismiss 开关）。7 次调用全是边界，档位停在
  `count_only`，**这是设计使然，不是缺陷**。
* **3 份 TASK-113 的声明被「移出」而不是「删除」**：它们在原地被移进
  `readback_superseded` 数组（带 `superseded_by` + `superseded_reason`），
  理由是同一个工具同时出现在「已核实」表和「被拒」表里读起来自相矛盾（§B4）。
* **一次失误（如实披露）**：探针第一次跑在「不带 `.pck` 运行」这一步**挂住** ——
  导出的游戏找不到 pck 时弹**模态对话框**等人工点击，`Start-Process -Wait` 永不返回。
  发现后杀掉该进程、改成**有界等待**（超时即 `taskkill /T /F`），重跑完成。
  这是本轮唯一一次杀进程，全部发生在我自己的 `recovery/work/task115/export_probe/` 下。

---

## 1. 交付物与证据路径

| 交付物 | 路径 | 说明 |
|---|---|---|
| H7 练习工程 | `projects\_exercises\ex_editor\` | **无 C#、无业务 GDScript** 的最小工程；场景 4 个可寻址节点、2 张 8×8 PNG + 1 张 16×16、一个空 `EditorPlugin`、3 个导出预设 |
| H7 会话与声明 | `tools\sessions\_exercises\ex_editor\{h7-session.json,h7-manifest.json}` | 82 次调用；**7 条**内容级读回声明 |
| H1 会话与声明 | `tools\sessions\_exercises\ex_3d\{h1b-session.json,h1b-manifest.json}` | 39 次调用；**5 条**声明 |
| c4b 会话与声明 | `tools\sessions\_exercises\ex_write5\{c4b-session.json,c4b-manifest.json}` | 19 次调用；**2 条**声明 |
| h2c 会话与声明 | `tools\sessions\_exercises\ex_anim2\{h2c-session.json,h2c-manifest.json}` | 15 次调用；**1 条**声明 |
| 探针脚本 | `recovery\work\task115\probe_export.ps1` | 有界等待；`Start-Process -RedirectStandardOutput/Error`，**无 shell 重定向** |
| 探针逐字输出 | `recovery\work\task115\logs\probe-report.txt` + `logs\*.stdout/stderr.txt` | §C 的每一行都来自这里 |
| PNG fixture 生成器 | `recovery\work\task115\mk_png_fixtures.py` | 手写 PNG 编码器，无第三方依赖 |
| 台账（重算） | `TOOL-COVERAGE.md` / `coverage.json` | 109 run / 177 trace / 8665 调用 / 169 出现过 |
| 登记表改判 | `tools\tool_coverage_unreachable.json` | `reclassified` 56 → **66**（只加不删）；新增 `categories.H7.still_out` 与 `categories.H8.external_device` |
| 派生脚本 | `recovery\work\task115\{mk_manifests,reclassify_h7,report_numbers}.py` | 全部可重跑；`reclassify_h7.py` **幂等**（第二遍输出 `added 0, refreshed 10`） |
| 决策 | `F:\moonbit-hof-rs\DECISIONS.md` **D160** | 选项、否决理由、更正、回滚点 |
| 会话账 | `runs\_exercises\{ex_editor\h7-task115, ex_3d\h1b2-task115, ex_write5\c4b-task115, ex_anim2\h2c-task115}\` | trace + ledger + report（`runs/` 不入库） |

---

## A. H7 的 15 条：分类 + 练习

### A1. 分类（实测，不是猜）

| # | tool | 分类 | 依据 |
|---|---|---|---|
| 1 | `editor_play_scene` | **可达** | `tools/editor_playback.cpp:294-472`；编辑器运行条 `EditorRunBar::play_*` 是可调用的 |
| 2 | `editor_stop_scene` | **可达** | 同文件 :493-522 |
| 3 | `editor_set_node_selection` | **可达** | `tools/editor_write_scene_editor.cpp:524-604`；`EditorSelection` 由 `EditorNode` 持有 |
| 4 | `editor_remove_node_selection` | **可达** | 同文件 :612-641 |
| 5 | `editor_remove_output_log` | **可达** | 同文件 :1009-1042；走的是面板 *Clear* 按钮自己的 `EditorLog::clear()` |
| 6 | `editor_reload_plugin` | **可达** | 同文件 :395-446；把 `editor_plugins/enabled` 里的每个 addon 禁用再启用 |
| 7 | `editor_rescan_project_filesystem` | **可达** | 同文件 :455-476；`EditorFileSystem::scan()`（异步，效果要另读） |
| 8 | `editor_get_test_report` | **可达（任务书猜错了）** | `tools/editor_testing_read.cpp:151-229`：读**游戏进程**持久化的桥接文件，没有就从本进程累加器诚实回答；**不需要任何编辑器侧测试运行** |
| 9 | `editor_analyze_screenshot_diff` | **可达（任务书猜错了）** | 同文件 :261-265 源码原话：*no display server is needed … `Image::load` and `Image::load_png_from_buffer` are CPU-side, so this tool also works in a `--headless` process* |
| 10 | `editor_set_auto_dismiss_dialogs` | **可达，但只有边界** | `tools/editor_node_write.cpp:1037-1063`：provider 永远是 `-32000 Not implemented` |
| 11-15 | `editor_simulate_key` / `mouse_click` / `mouse_move` / `input_action` / `input_sequence` | **范围排除（D59 / GDR-21）** | `tools/editor_input_simulation.cpp:53-112`（头注释）+ `:121-144`（前置条件） |

**第 11-15 条为什么是「范围排除」而不是「不可达」**（登记表里逐字写明）：
它们**编译进了这个构建**、**在编辑器端点是注册过的**，而且真编辑器里它们需要的东西一定存在 ——
源码原话：*`Input` is created by `Main::setup2` in every engine process, so in a real editor these
never fail*。它们做不到的是**驱动游戏**：它们调 `Input::get_singleton()->parse_input_event()`
注入的是**编辑器进程自己**的输入队列。本循环刻意用游戏端点的 `running_game_*` 输入工具验证游戏行为。
**可测条件**（写进登记表）：出现一个「在编辑器侧观测输入」的批次 —— 用 Editorial 侧插件或
`editor_execute_gdscript` 数 `Input` 事件、并在批次自述里写明「游戏端点不该看到任何东西」。
在现有 ledger 规则下这样的批次最多到 `ok_no_effect_observed`，只买到计数与边界，买不到档位。

### A2. 练习结果（`runs/_exercises/ex_editor/h7-task115`，82 次调用 / 正确 63 / 边界 19）

```
calls=82 malformed_lines=0
verdicts: failed=19, ok_effect_unavailable=1, ok_no_effect_observed=62
file_effects: none=82
```

| tool | 累计 | 有效 | 边界 | 档位 | 状态 | 见证读（同 run，内容级） |
|---|---|---|---|---|---|---|
| `editor_play_scene` | 7 | 0 | 2 | `readback` | 计数达标缺证据 | `editor_execute_gdscript`@59 `"result":true` |
| `editor_stop_scene` | 7 | 0 | 1 | `readback` | 计数达标缺证据 | `editor_execute_gdscript`@61 `"result":false` |
| `editor_set_node_selection` | 9 | 0 | 1 | `readback` | 计数达标缺证据 | `editor_get_selection`@13 `"name":"Box"` + `"type":"ColorRect"` |
| `editor_remove_node_selection` | 6 | 0 | 1 | `readback` | 计数达标缺证据 | `editor_get_selection`@22 `"count":0` + `"nodes":[]` |
| `editor_remove_output_log` | 6 | 0 | 1 | `readback` | 计数达标缺证据 | `editor_get_output_log`@6 `"in_process":true` + `expect_absent "Godot Engine v4.8.dev"` |
| `editor_reload_plugin` | 6 | 0 | 1 | `readback` | 计数达标缺证据 | `project_get_settings`@37 `res://addons/probe_plugin/plugin.cfg` |
| `editor_rescan_project_filesystem` | 6 | 0 | 1 | `readback` | 计数达标缺证据 | `project_get_filesystem_tree`@82 `editor_probe.tscn` |
| `editor_get_test_report` | 6 | **5** | 1 | `readback` | **达标** | own_payload（读类回包即证据） |
| `editor_analyze_screenshot_diff` | 8 | **5** | 3 | `readback` | **达标** | own_payload |
| `editor_set_auto_dismiss_dialogs` | 7 | 0 | **7** | `count_only` | 计数达标缺证据 | ——（没有成功分支，没有可读回的东西） |

**逐字回包（节选，全部来自本 run 的 trace）**：

```
[h7-019-editor_get_selection-ok]            {"count":1,"nodes":[{"name":"Panel","path":"Panel","type":"Control"}],"top_only":false}
[h7-021-editor_remove_node_selection-ok]    {"cleared":1,"count":0,"selected":[]}
[h7-028-editor_remove_node_selection-ok]    {"cleared":3,"count":0,"selected":[]}
[h7-029-editor_remove_node_selection-ok]    {"cleared":0,"count":0,"selected":[]}     ← 空选中是合法答案
[h7-005-editor_remove_output_log-ok]        {"cleared":true,"log_is_empty":true,"log_was_empty":false}
[h7-004-editor_get_output_log-ok]           {"available":true,"count":10,"..."in_process":true,"lines":["Godot Engine v4.8.dev.custom_build ..."]}
[h7-006-editor_get_output_log-ok]           {"available":true,"count":1,"..."lines":[""]}
[h7-031-editor_reload_plugin-ok]            {"message":"编辑器插件已禁用并重新启用","plugins":["res://addons/probe_plugin/plugin.cfg"],"reloading":true}
[h7-037-project_get_settings-ok]            {"count":1,"settings":{"editor_plugins/enabled":"[\"res://addons/probe_plugin/plugin.cfg\"]"}}
[h7-059-editor_execute_gdscript-playing]    {"result":true,"result_type":"bool"}
[h7-061-editor_execute_gdscript-stopped]    {"result":false,"result_type":"bool"}
[h7-070-editor_stop_scene-probe-nothing]    {"message":"No scene playing","stopped":false}   ← 无物可停是信息不是失败
[h7-058-editor_play_scene-ok]               {"args_injected":["--mcp-port=61849","--headless"],"endpoint":"http://...","pid":...}
[h7-068-editor_play_scene-ok]               {"args_injected":["--mcp-port=9899","--headless"],...}
[h7-044-editor_get_test_report-ok]          {"all_passed":false,"cleared":[],"details":[],"failed":0,"no_results":true,"pass_rate":"N/A",...}
[h7-050-editor_analyze_screenshot_diff-ok]  {"changed_pixels":0,...,"identical":true,...}          ← a vs a
[h7-051-editor_analyze_screenshot_diff-ok]  {"changed_pixels":32,...}                             ← a vs b
[h7-074-editor_set_auto_dismiss_dialogs-probe-1]
      {"error":{"code":-32000,...":'This engine has no process-wide auto-dismiss setting for editor dialogs; ...
```

**边界（19 次 `ok=false`，全部在会话 note 里声明过）**：8 条「契约不接受该参数」的 `-32602`、
6 条 `-32001`（节点/场景/图片不存在）、2 条 `-32602`（类型/取值范围）、
5 条 `-32000`（auto-dismiss 的设计性 not_implemented）+ 2 条 `-32000`（auto-dismiss 的缺参/错类型
其实是 `-32602`；合计见下表）。

**跑前/跑后检查（铁律 4）**：

```
pre-h7   netstat LISTENING 9877/9888/9889/9890/9891/9899 -> NONE ; tasklist godot -> NONE
post-h7  netstat LISTENING 9890/9891/9899/61849/61856/61861/61865 -> NONE ; tasklist godot -> NONE
         （5 个游戏子进程全部被 editor_stop_scene 收掉，没有孤儿）
```

### A3. 为什么 7 条写工具够不到「达标」—— 这是结论，不是掩饰

ledger 的「有效调用」只有两条通道：**像素真的变了**（`ok_effect_observed`）或**文件真的变了**
（`ok_file_effect_observed`）。本 run 里：

* 82 次调用的 `file_effects: none=82` —— 没有一次写盘（编辑器写工具都写内存里的活场景，
  没有 `editor_save_scene`）；
* 82 次调用里截图对比 `changed=False`（`report.md` 的 Pixel proof 表逐行 `False`），
  且该表同时报了 **`PIXEL EVIDENCE UNAVAILABLE (D-1)`** —— 本工程的 2D 视口在这个编辑器进程里
  本来就取不到可用的像素证据链（这是 ledger 的已知边界，见 `MCP-TRACEABILITY.md` §7）。

所以这 7 条工具**在那个像素/文件意义下永远不「生效」**。它们真做的改变（选中、面板清空、
运行条状态、插件禁用再启用、文件系统重扫）只能通过**读回来**证明 —— 这正是 TASK-113 引入的
`witness_read` + 内容级 `expect` 通道。**要把它们推上「达标」，需要给 ledger 增加第三个证据通道
（「编辑器自身状态的读回」）**，那是契约口径变更，本轮不做，只登记。

---

## B. H1 的 5 条 + TASK-113 的 3 条见证

### B1. 三个批次与真实回包

```
runs/_exercises/ex_3d/h1b2-task115     calls=39 malformed_lines=0
    verdicts: failed=6, ok_no_effect_observed=33        file_effects: none=39
runs/_exercises/ex_write5/c4b-task115  calls=19 malformed_lines=0
    verdicts: failed=2, ok_file_effect_observed=2, ok_no_effect_observed=15
    file_effects: changed=2, none=17
runs/_exercises/ex_anim2/h2c-task115   calls=15 malformed_lines=0
    verdicts: failed=1, ok_no_effect_observed=14        file_effects: none=15
```

**见证读的逐字回包（这就是 `expect` 的来源）**：

```
[h1b-018-editor_execute_gdscript-material]  {"result":"M:res://assets/mat3d_b.tres","result_type":"String"}
[h1b-025-editor_execute_gdscript-camera]    {"result":"C:Camera3D","result_type":"String"}
[h1b-032-editor_execute_gdscript-light]     {"result":"L:DirectionalLight3D","result_type":"String"}
[h1b-039-editor_execute_gdscript-environment]{"result":"E:WorldEnvironment","result_type":"String"}
[h1b-011-editor_get_scene_tree-ok]          {"scene_path":"res://scenes/probe3d.tscn","tree":{...,"name":"N1",...,"type":"MeshInstance3D",...}}
[c4b-012-editor_execute_gdscript-script]    {"result":"S:res://src/exc4b.gd","result_type":"String"}
[c4b-019-editor_execute_gdscript-theme]     {"result":"T:res://themes/c4b.tres","result_type":"String"}
[h2c-007-editor_list_animations-before]     {"animations":["Anim1","Anim2","Anim3","DelA","DelB",... ],"count":...,"node_path":"Player"}
[h2c-014-editor_list_animations-after]      {"animations":["Anim1","Anim2","Anim3"],"count":3,...,"node_path":"Player"}
[h2c-013-editor_remove_animation-probe]     {"error":{"code":-32001,"message":"...","suggestion":"The default library holds: Anim1, Anim2, Anim3..."}}
```

### B2. 升档结果

| tool | 之前 | 之后 | 见证 | `expect`（逐字） |
|---|---|---|---|---|
| `editor_add_mesh_instance` | `count_only` | `readback` | `editor_get_scene_tree`@11 | `"name":"N1"` ; `"type":"MeshInstance3D"` |
| `editor_setup_camera_3d` | `count_only` | `readback` | `editor_execute_gdscript`@25 | `C:Camera3D` |
| `editor_setup_lighting` | `count_only` | `readback` | `editor_execute_gdscript`@32 | `L:DirectionalLight3D` |
| `editor_set_material_3d` | `count_only` | `readback` | `editor_execute_gdscript`@18 | `M:res://assets/mat3d_b.tres` |
| `editor_setup_world_environment` | `count_only` | `readback` | `editor_execute_gdscript`@39 | `E:WorldEnvironment` |
| `editor_set_node_script` | `count_only` | `readback` | `editor_execute_gdscript`@12 | `S:res://src/exc4b.gd` |
| `editor_set_control_theme` | `count_only` | `readback` | `editor_execute_gdscript`@19 | `T:res://themes/c4b.tres` |
| `editor_remove_animation` | `count_only` | `readback` | `editor_list_animations`@14 | `"node_path":"Player"` + `expect_absent [DelA,DelB,DelC,DelD,DelE]` |

`count_only` **12 → 5**（另加 `editor_set_auto_dismiss_dialogs` 由 `no_calls` 进 `count_only`，故净值 −7）。

### B3. 为什么 TASK-113 那三条「写不出 `expect`」——本轮找到了根因

`c4-v5-task111` 里那条被拒的声明想让 `editor_get_node_properties{"path":"C4Node1",
"properties":["script"]}` 当见证。**实测它根本不回包**：

```
c4-141-editor_get_node_properties-ok.json:
{"error":{"code":-32001,"data":{"suggestion":"editor_get_node_properties never answers with an empty
 map for a property it was asked for by name. Names starting with '_' and the 'script' property are
 kept out of the property listing (the migration source's rule); ask for the properties you need by
 their public names instead"},
 "message":"Property 'script' on node 'C4Node1' is not readable by name not found"}}
```

源码规则：`tools/editor_node_read.cpp:206-208` 把 `_` 开头与 `script` 从**任何**列表/按名读取里排除。
所以「补一个 `expect` 就行」是不成立的 —— 见证工具本身选错了，本轮换成
`editor_execute_gdscript` 读 `Node.get_script().resource_path`。

### B4. 三份 TASK-113 声明「移出」而非「删除」

`ex_write/c4-manifest.json` 与 `ex_anim/h2-manifest.json` 里那三条被拒声明被移到同文件新增的
`readback_superseded` 数组（带 `superseded_by` + `superseded_reason`），原 `why` 逐字保留。
理由：留着它们会让同一个工具**同时**出现在 `TOOL-COVERAGE.md` §0.1 的「已核实见证」表与
「被拒声明」表里，读起来自相矛盾。**没有删除任何一条**，改判理由写在数组里、也写在本报告与 D160。

内容级复核总数：声明 38→**50**、经 trace 复核通过 33→**48**、逐字命中 33→**48**、
**被拒 5→2**（剩下两条是 TASK-115 未碰的既有缺口 `editor_add_gridmap` / `editor_connect_signal`）。

### B5. h1b2 的 6 条失败里有一条是「第二次跑」的正常现象（如实说明）

`h1b-002-project_create_resource` 在**第二次**（权威）运行里答 `-32000 Resource already exists:
res://assets/mat3d_b.tres` —— 第一次 h1b 运行已经把这个 `.tres` 写进磁盘（场景没存，但资源文件存了）。
材料本身内容一致，`h1b-018` 也读回了同一个路径。所以 6 条失败 = 5 条声明过的探针 + 这 1 条
幂等冲突；**它不影响任何一条见证的正确性**，但如实记在这里。

---

## C. SAC 友好导出可行性探针 —— 三问的逐条答案

**脚本**：`recovery/work/task115/probe_export.ps1`；**逐字输出**：
`recovery/work/task115/logs/probe-report.txt`。**没有联网、没有下载任何东西。**
所有引擎调用都通过生成的 `.cmd` 由 `cmd.exe` 启动（铁律 3），日志由
`Start-Process -RedirectStandardOutput/Error` 产生（铁律 1）。

### ① 官方 4.7.1 mono 导出模板是否已安装？模板 exe 是否 `Valid`？

**答案：没有安装。** 所以「官方模板 exe 是否 Valid」**未测**。

```
template root                : C:\Users\wyl\AppData\Roaming\Godot\export_templates
template root exists         : True
  version dir                : 4.8.dev
      version.txt                                              37 bytes
      windows_release_x86_64.exe                         82198528 bytes
      windows_release_x86_64_console.exe                   292352 bytes
4.7.1.stable.mono dir        : C:\Users\wyl\AppData\Roaming\Godot\export_templates\4.7.1.stable.mono
4.7.1.stable.mono exists     : False
4.7.1 template exe exists    : False
```

**顺带测到的（本机唯一可用的那一份）**：

```
official 4.7.1 mono editor   : Valid :: CN=Prehensile Tales B.V., O=..., L=Uitgeest, S=Noord Holland, C=NL
4.8.dev template exe         : NotSigned ::
  size / sha256              : 82198528 / AA883610178DC5322DFFA8111DEB0C2CC610364FDBFB557995B319B39785471E
```

→ 与本机编辑器签名状态一致（TASK-114 已测过官方编辑器 exe 是 `Valid`）。
官方模板缺失，需要约 1 GB 下载；**按任务书要求：先报告，不擅自下载。**

### ② `embed_pck=false` 之后，导出的 `game.exe` 与模板 exe 是否逐字节相同？

**答案：`embed_pck=false` 不够；要 `modify_resources=false` 才逐字节相同。**

```
template exe                           :     82198528 bytes  sha256 AA883610178DC5322DFFA8111DEB0C2CC610364FDBFB557995B319B39785471E
exported exe (embed_pck=false)         :     82057728 bytes  sha256 9A64C8433B12ACDB1374F95240524FEEB96DC114E704FD3810E381E499E6A9AD
exported exe (embed_pck=true)          :     82062160 bytes  sha256 27AE0FEB8758CFA87F10F16AED06D7F03C80C88FE7E713E69C9D8A8B47571DC9
exported exe (embed_pck=false + modify_resources=false)
                                       :     82198528 bytes  sha256 AA883610178DC5322DFFA8111DEB0C2CC610364FDBFB557995B319B39785471E
sidecar pck (embed_pck=false)          :         4416 bytes  sha256 DEA655179EA3A3B70EA91C07BB4B81E384E4220C2EEE8CA3E125E1ACA74F2DD0

sha256(template) -eq sha256(export, embed_pck=false)                              : False
sha256(template) -eq sha256(export, embed_pck=true)                               : False
sha256(template) -eq sha256(export, embed_pck=false + modify_resources=false)     : True
byte delta (embed_pck=false)                                                      : -140800
byte delta (embed_pck=false + modify_resources=false)                             : 0
```

**读法**：
* 默认预设（`binary_format/embed_pck=false` + Godot 默认 `application/modify_resources=true`）
  导出的 exe **不是**模板的拷贝：少了 **140800 字节**（Godot 会改写 PE 的版本信息/图标资源）。
  **一个带 `Valid` 签名的模板，这样导出之后签名必然失效。**
* 把 `application/modify_resources` 也设成 `false`，导出的 exe 与模板 **sha256 完全相同**
  → **签名按构造被保留**（Authenticode 覆盖整个文件，字节相同即签名有效）。
* **签名状态本身**：本机唯一模板是 `NotSigned`，所以「签名被保留」这一格在本机是**平凡成立**的；
  可迁移的是**机制**（字节同一性）。**官方 4.7.1 签名模板那一格未测。**

**这一条改变了 SAC 建议**：以前的说法是「导出物 = 模板拷贝 + 追加 PCK」。正确说法是
「默认设置下导出物会被改写；要保住模板字节（进而是签名）必须同时
`embed_pck=false` **且** `modify_resources=false`」。

### ③ 导出的 exe 真能运行吗？真的加载同目录 `.pck` 吗？

**答案：能，而且真的读同目录 `.pck`。** headless 与带窗口各一次，退出码 0。

```
# 不带 .pck（把 exe 单独拷到 alone\ 下）—— 这是「它真的读 pck」的证明
run WITHOUT the sidecar .pck, headless --quit-after 30 : exit TIMEOUT(45s)
    ! ERROR: Error: Couldn't load project data at path
    !   "F:/moonbit-hof-rs/godot-mcp/recovery/work/task115/export_probe/alone".
    !   Is the .pck file missing?
    ! If you've renamed the executable, the associated .pck file should also be renamed to match
    ! the executable's name (without the extension).
    !    at: Main::setup (main\main.cpp:2094)
    | RUN_EXIT=1

# 带同目录 .pck，headless
run WITH the sidecar .pck, headless --quit-after 60 : exit []
    | Godot Engine v4.8.dev.mono.custom_build.1f9d0cb1c (2026-09-26 23:05:35 UTC) - https://godotengine.org
    | [MCP] role=game configured_port=0 source=default listen=false
    | RUN_EXIT=0

# 带同目录 .pck，带窗口（真的开了窗口）
run WITH the sidecar .pck, windowed --quit-after 120 : exit []
    | Vulkan 1.4.351 - Forward+ - Using Device #0: NVIDIA - NVIDIA GeForce RTX 4090
    | RUN_EXIT=0

# 与模板逐字节相同的那份 exe（配同目录 pck）
purecopy\ex_editor.exe sha256 : AA883610178DC5322DFFA8111DEB0C2CC610364FDBFB557995B319B39785471E  (== template)
run byte-identical-to-template exe, headless --quit-after 60 : exit []
    | RUN_EXIT=0

post-run process check (no ex_editor.exe may be left behind):  none
```

**一个附带发现（写下来免得下次再踩）**：不带 `.pck` 时引擎**弹模态对话框**、`--headless` 也拦不住，
`Start-Process -Wait` 永不返回。`probe_export.ps1` 因此把游戏运行改成**有界等待**
（`Wait-Process -Timeout`，超时即 `taskkill /T /F` 并记 `TIMEOUT(ns)`）。**报告 ② 与 ③ 的其它行
不受影响**（`Run-CmdFileBounded` 的 `Exit` 字段在成功路径上取不到对象值，但**每行日志里的
`echo RUN_EXIT=<n>` 是引擎自己退出后的真实 `%ERRORLEVEL%`**，本报告引用的是它）。

**另注**：导出物自报的引擎版本是 `4.8.dev.mono.custom_build.1f9d0cb1c`，
而本机编辑器/模板是 `3fdabe2d9` 时代的自建二进制 —— 已装的 `4.8.dev` 模板与当前编辑器**不是同一个 commit**。
这不影响本段的机制结论（都是同一条导出代码路径），但说明「本机导出物」与「本机编辑器」严格来说不同源。

---

## D. 收尾

### D1. 引擎改动判定 → 未重建、未跑十道门

* `godot/modules/mcp_server/` **一个字节未改**（本轮没有发现需要修的缺陷，也没有为了「顺手」而改）。
* 因此按铁律 7 **未触发**两变体重建、未重跑十道门、未跑 accept_m1、未 push 引擎仓。
* 会话全部跑在既有的 `4.8.dev.mono.custom_build` 二进制上。

### D2. 台账增量（`python tools/tool_coverage.py`，非手算）

```
tool_coverage: mode=all-runs runs=109 trace_files=177 calls=8665 distinct=169
  buckets: 0=8 1-4=0 >=5=169 | status: 达标=106 缺证据=63 未达1-4=0 未达0=8
  registry: 74 members, 66 drift
```

| 指标 | TASK-114（基线） | TASK-115（本轮） | 增量 |
|---|---|---|---|
| run 目录 / trace / `tools/call` | 104 / 172 / 8471 | **109 / 177 / 8665** | +5 / +5 / **+194** |
| 出现过的工具名 | 159 | **169** | **+10** |
| `0` 次 | 18 | **8** | **−10** |
| 达标 | 104 | **106** | **+2** |
| 证据档位 | pixel 34 / file 24 / readback 89 / count_only 12 / no_calls 18 | **pixel 34 / file 24 / readback 106 / count_only 5 / no_calls 8** | readback **+17**、count_only **−7**、no_calls **−10** |
| 内容级声明 | 声明 38 / 通过 33 / 被拒 5 | **声明 50 / 通过 48 / 逐字命中 48 / 被拒 2** | 通过 **+15**、被拒 **−3** |
| 登记表 `reclassified` | 56 | **66** | +10（成员仍 74，**一条没删**） |

### D3. 登记表更新

* 新增 **10** 条 `reclassified`（H7 可达者，逐条带 why + 证据 run）。
* `categories.H7.why_unreachable` 与 `supporting_evidence` 改成「**SUPERSEDED BY MEASUREMENT**」
  并把**原文逐字附在后面**（不删除）。
* 新增 `categories.H7.still_out`：5 条 `editor_simulate_*` 的 why / evidence / `measurable_when`。
* 新增 `categories.H8.external_device`：3 条 Android 工具按「需要外部设备」登记（不是「不可达」）。
* `reclassify_h7.py` 跑第二遍输出 `added 0, refreshed 10` —— `reclassified` 数组**幂等**。
* **一处本轮自己踩到并修掉的缺陷（如实披露）**：该脚本的第一版只让 `reclassified` 数组幂等，
  **分类正文不是** —— 它每次运行都往 `categories.H7.why_unreachable` 前面再贴一遍
  「SUPERSEDED BY MEASUREMENT …」。跑第二遍之后那一格变成
  `… SUPERSEDED … ORIGINAL TEXT: … SUPERSEDED … ORIGINAL TEXT: <原文>`（重复两遍）。
  发现方式是**重刷台账后读 §4 的 H7 正文**（不是靠「应该不会重复」）。
  修法：把原文存进独立的 `why_unreachable_original` / `supporting_evidence_original`，
  每次运行**从原文重新合成**；并且能从一个已经被重复贴过的值里按**最后一个** `ORIGINAL TEXT:`
  标记恢复出真原文（所以它能自愈，不需要手工回滚）。修完实测：
  `SUPERSEDED BY MEASUREMENT` 出现 **1** 次、`ORIGINAL TEXT` 出现 **1** 次、原文 225 字逐字保留。

### D4. 跑前/跑后检查（铁律 4）

```
before-run-check  netstat LISTENING 9892/9893/9896/9897 -> NONE ; tasklist godot -> NONE
post-run-check    9890/9891/9892/9893/9894/9895/9896/9897/9899 + 5 个动态游戏端口 -> NONE ; tasklist godot -> NONE
post-probe-check  ex_editor.exe -> none
```

每次会话**之前**都先查进程与端口；4 个会话分别用 **(9890/9891)、(9892/9894)、(9893/9895)、
(9896/9897)**，互不重叠，且都不占用用户端口 **9877**。

### D5. 提交

见 §F。

---

## E. 本轮**没有**做的事（如实清单 + 下一批建议）

1. **官方 4.7.1 mono 导出模板那一格没测**：模板没装，需要约 1 GB 下载，按任务书要求**没有下载**。
   因此「官方签名模板的签名能否被 `modify_resources=false` 保住」是**推断（机制）**，
   不是**实测（那个模板）**。
2. **H7 的 7 条写工具到不了「达标」**：见 §A3。需要一个 ledger 口径变更（编辑器状态的读回通道），
   本轮只登记，未改口径。**`editor_set_auto_dismiss_dialogs` 是设计性的 `count_only`**，不要当成缺陷。
3. **剩余 8 条 0 次工具**：
   * `editor_simulate_*` 5 条 —— 登记表 `H7.still_out`，等一个「编辑器侧输入观测」批次；
   * `os_list_android_devices` / `os_deploy_to_android_device` / `project_get_android_preset_info` ——
     登记表 `H8.external_device`，等 Android 预设 + 真机/模拟器。
4. **`editor_add_gridmap` 与 `editor_connect_signal` 这两条被拒声明仍未修**
   （TASK-113/TASK-114 的既有缺口，理由都是「该 run 里找不到合格的见证调用」）。
   本轮没碰它们 —— 要修得各重跑一个小批次，成本很低。
5. **`count_only` 还剩 5 条**：`editor_connect_signal`、`running_game_find_node_when_available`、
   `editor_add_gridmap`、`editor_set_node_script_batch`、`editor_set_auto_dismiss_dialogs`
   （最后一条是设计性的）。前 4 条都要重跑一个带正确见证的小批次。
6. **H7 的 `readback` 档位有一处要留意**：`editor_play_scene` / `editor_stop_scene` 的见证是
   `editor_execute_gdscript`（`EditorInterface.is_playing_scene()`）。它是**独立读调用**、
   内容级可核（`"result":true` / `"result":false`），但它是**通用求值器**而不是专门的运行条读工具。
   登记表与 D160 都写明了这一点，供验收者判断是否够强。
7. **没有消除本轮产生的构建/运行产物**：`recovery/work/task115/export_probe/`（约 250 MB：
   3 份导出的 exe + pck）与 `runs/_exercises/**` 留在原地 —— 前者由
   `recovery/work/task115/.gitignore` 挡掉，后者本来就不入库。需要时整体删除
   `recovery\work\task115\export_probe\` 即可。

**下一批建议（按价值排序）**

1. **给 ledger 加第三个证据通道**（编辑器自身状态的读回），
   把 `editor_set_node_groups`、`editor_setup_camera_3d` 这类「有见证但永远 eff=0」的工具
   从 `计数达标缺证据` 里解放出来 —— 这是**口径决策**，需要用户拍板，且会一次性影响
   现在 63 条 `计数达标缺证据` 里的相当一部分。
2. 修 `editor_add_gridmap` / `editor_connect_signal` 两条被拒声明（各一个小批次即可）。
3. 若用户愿意付那 1 GB 下载：装上官方 4.7.1-stable mono 模板，把 §C① 与 §C② 的
   官方签名那一格补成实测；否则**不要**把本报告的机制结论说成「官方模板已验证」。

---

## F. 提交

```
$ cd F:\moonbit-hof-rs && git log --oneline -3
<HEAD~2>  feat(godot-mcp): TASK-115 (D160) - split H7 by measurement, restore eight witnesses,
          and the export/signature probe
<HEAD~1>  docs(godot-mcp): TASK-115 - the report and the D160 decision record
<HEAD>    chore(godot-mcp): TASK-115 - refresh the ledger once more, and record the three-commit
          order in the report
```

三个提交、顺序与 TASK-114 同构（**正文只按消息引用、不写哈希**：本报告自己就在其中一次提交里，
任何写进正文的哈希都会被「写哈希」这个动作本身改掉；准确哈希请用 `git log --oneline`）：

1. **功能提交**（`HEAD~2`）—— 工程 / 会话 / 清单 / 台账 / 登记表 / 派生脚本；
2. **报告与决策**（`HEAD~1`）—— 本报告 + `DECISIONS.md` D160；
3. **再刷一次台账**（`HEAD`）—— 原因是 `tool_coverage.py` 把登记表的 `reclassified` 当**输入**：
   第一次刷新跑在 `reclassify_h7.py` 之前，所以 `TOOL-COVERAGE.md` §4 里那 10 条新漂移还标着
   「待复核」。重刷后是 **74 成员 / 66 漂移 / 66 已改判 / 0 条未改判漂移**，语料数字不变
   （109 run / 177 trace / 8665 调用 / 169 工具）。

这样「改动 → 提交 → 决策日志」三者可互查。
* 显式入库的东西：`projects/_exercises/ex_editor/`（含 `export_presets.cfg` —— 该工程自己的
  `.gitignore` **没有**忽略它）、四个会话与清单、`TOOL-COVERAGE.md` / `coverage.json`、
  `tools/tool_coverage_unreachable.json`、`recovery/work/task115/`（脚本 + README +
  `logs/probe-report.txt`）、`recovery/reports/TASK-115-REPORT.md`、`DECISIONS.md`。
* **没有**入库：`recovery/work/task115/export_probe/` 与 `logs/*.stdout.txt` / `*.stderr.txt`
  （由 `recovery/work/task115/.gitignore` 挡掉；`logs/probe-report.txt` 是显式例外，
  因为它是探针三问唯一自包含的逐字证据）、`runs/`（既有约定）、`dist/`（TASK-107/109 的既有未跟踪状态）。
* 本轮生成的工程产物按既有惯例入库了：`projects/_exercises/ex_3d/assets/mat3d_b.tres`、
  `projects/_exercises/ex_write5/{src/exc4b.gd,src/exc4b.gd.uid,themes/c4b.tres}`
  （它们的同类如 `ExC4.cs` / `c4.tres` 在 TASK-111 时也是入库的）。

**引擎仓（`F:\moonbit-hof-rs\godot-mcp\godot`）本轮无提交、无 push**：
`godot/modules/mcp_server/` 一个字节未改，因此按铁律 7 **不重建、不跑十道门、不 push**。

**未纳入工作树的主仓条目（都不是本任务的产物，一律未删除）**：
`godot-mcp/dist/` 里的既有打包产物（TASK-107/109）、
`godot-mcp/projects/_exercises/{ex_write2,ex_write3,ex_write4,ex_audio,ex_nav,ex_particles,ex_rec,ex_export,ex_export_np}/`
（沿用既有未跟踪状态）、`godot-mcp/tools/__pycache__/`、
`godot-mcp/recovery/reports/ACCEPTANCE-TASK-107.md`、
`godot-mcp/recovery/work/task104/logs/git-housekeeping.{out,err}.txt`（TASK-104 的既有改动）。

