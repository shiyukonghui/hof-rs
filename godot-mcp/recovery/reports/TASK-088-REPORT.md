# TASK-088 (2c-7) — mono 轴、验收电池、契约缺的 override 记录、以及溯源能力

* Repository: `H:\rebuild\godot`, branch `feature/mcp-server-module-rebuild`
* Start HEAD: `675df5ef27` → End HEAD: **`6b4c29dc81`**, **pushed**, `git status --short` **empty**, 与 origin 同步
* Scratch/tooling: `C:\Users\wyl\AppData\Local\Temp\mcp-recovery\work\task088\`
* Logs: `C:\Users\wyl\AppData\Local\Temp\mcp-recovery\logs\task088_*`
* Manifest: `modules/mcp_server/docs/reports/REBUILT-2C-MANIFEST.md` § 2c-7（G-1..G-7）
* 新文档: `modules/mcp_server/docs/reports/MCP-TRACEABILITY.md`

---

## 0. 六件事，逐条结论

| # | 要求 | 结论 |
|---|---|---|
| ① | mono 构建 + 锚点门 → 9/9 全绿 | **达成**。mono 构建 `scons platform=windows target=editor tests=yes module_mono_enabled=yes -j8 -k` exit 0（96 s + 两轮增量 53/51/50/35 s）；`--version` = `4.8.dev.mono.custom_build.<HEAD>`；`--generate-mono-glue` exit 0（1220 文件，"The Godot API sources were successfully generated"）；`build_assemblies.py` exit 0（`bin\GodotSharp\Api\{Debug,Release}\GodotSharp.dll` + 4 个本地 nupkg）；**最小 C# 工程实测**：离线 `dotnet build -c Debug` exit 0（0 警告 0 错误，3.05 s），引擎跑起来打出 `MCP088_CSHARP_READY version=4.8-dev (custom_build) answer=42`。锚点门 `ANCHOR_EQUAL` PASS。**9/9 门全绿** |
| ② | `accept_m1.ps1` 四处过时期望 + 重建 case0/case20 → 20/20 | **达成，且超过目标：22/22（exit 0）**。case1/case3/case12 的 `tools==2` → **契约派生**（实测打印 `implemented union=177, editor=154, game=73`）；`guard_user_port_9877` 改为「本脚本从不碰 9877」的不变量；case0/case20 按录制文本重放 → 20/20 后加两个用例 → 22/22。**没有删任何断言**：比较面从「2 个工具」扩到「该端点的全部 154/73 个，逐字节 name+description」 |
| ③ | `check_hardcoded_counts.py` 那一行 | **达成**。`docs\scripts\_tmp_gen_b3_b5.py:282` 的字面量 171 改为运行时派生（`% len(contract_names)`），并把同文件 284 行的同一陈旧字面量一并处理；`UNCLASSIFIED = 0`、`RESULT: PASS`。两行表达式单独做了单元测试（`verify_gen_expr.txt` RESULT: PASS，实测求值得 177） |
| ④ | 取回/重建剩余 override + `_meta.map_path` 对齐 + 六项 + sha 差值原因 | **部分达成，差值原因已定量分解**。实测取回**7 条 description 不一致的工具**（6 条全新记录 + `play_scene` 的 value 是同一改写的更早一版）；`_meta.map_path` 已对齐到**证据里的记录值**（`events-termdump.jsonl` 九处逐字 + 同一个 `map_sha256`）。六项：count 177 / added_count 6 / generator 1.22.0 / editor 154 / game 73 / **幂等**（连跑两次同 sha `724f03b8…`）。差值与 pinned 的差值原因见 §4。**3 条 inputSchema 不是缺记录**（生成器已声明为 SCHEMA_OVERRIDES，见 §4.3） |
| ⑤ | 溯源能力核实+补齐 + MCP-TRACEABILITY.md + 实测演示 | **达成**。核实：捕获/取景/原图不截断/像素差自动入日志全部实测在册。**补齐了一处真缺陷**：调用行此前**不带请求身份**（`method` 空、`id` null、无 `tool`/`args`），本轮补上并重建。产出 `MCP-TRACEABILITY.md`（字段/判定规则/失败分类）与 `scripts/mcp_trace_ledger.py`（每次调用一行台账）。**实测演示**：窗口化真实会话（编辑器 9888 + 游戏 9889），编辑器侧 `calls=4`、`ok_effect_observed=1 / ok_no_effect_observed=3`、`facts_complete 4/4`，截图 8+6 个 PNG，路径与摘要见 §5 |
| ⑥ | 时间不够如实报告 | 见 §7「没做到的」 |

---

## 1. ① mono 轴

| 步骤 | 命令 | 结果 |
|---|---|---|
| mono 引擎 | `scons platform=windows target=editor tests=yes module_mono_enabled=yes -j8 -k` | exit **0**；`bin\godot.windows.editor.x86_64.mono.exe` 193 983 488 B |
| 变体陈旧对象 | tracked 的 `mcp057_build_mono.cmd` 要求先删 4 个对象（mono/plain 共用 `bin\obj`，`version_generated.gen.h` 无依赖边） | 用受保护的 `del_stale_objs.py`（绝对路径 / 白名单前缀 / 先打印清单 / 无通配符 / 先 dry run）删除 3 个，再构建 |
| `--version` | mono console exe | `4.8.dev.mono.custom_build.675df5ef2` → 提交后重建为 `…e4b025519`（= HEAD） |
| glue | `--headless --generate-mono-glue modules/mono/glue` | exit **0**，`The Godot API sources were successfully generated`，1220 文件 |
| GodotSharp | `python modules\mono\build_scripts\build_assemblies.py --godot-output-dir=bin --godot-platform=windows` | exit **0**（50.7 s）；`Api\{Debug,Release}\GodotSharp.dll`（6 471 168 / 6 030 848 B）、`Tools\nupkgs\` 4 个 `4.8.0-dev` 包 |
| 最小 C# 工程 | 自己写 `project.godot` + `Main.cs` + `main.tscn` + `NuGet.config`（`<clear/>` + 本地 nupkgs） | `dotnet build -c Debug` exit 0，`0 个警告 0 个错误`，产物 `.godot\mono\temp\bin\Debug\Mcp088Csharp.dll`（7 680 B）；**引擎实跑**打出 `MCP088_CSHARP_READY version=4.8-dev (custom_build) answer=42` |
| 锚点门 | `check_engine_anchor.ps1 -VersionText '4.8.dev.mono.custom_build.e4b025519'` | `VERDICT=ANCHOR_EQUAL ANCHOR=e4b025519 HEAD=e4b025519 RESULT PASS`（提交后在 `6b4c29dc81` 上再判为 `ANCHOR_STRUCTURAL_EQUIVALENT`，diff=1 个 `.md`，RED_COUNT=0，仍 PASS） |

**如实说明两处**：
1. `build_assemblies.py` 第一次跑完后**看起来像卡死**（0 CPU、日志不再增长 13 分钟），我据此把它停了；随后查明原因是 `Start-Process -Wait` 会等**整个后代进程树**，而 MSBuild 的 reuse 节点在构建成功后仍存活 15 分钟。重跑 exit 0。所有 task-088 启动器已改为 `WaitForExit()`。
2. 未重跑 `build_assemblies.py` 里 GodotTools 的 bin 拷贝之外的官方 M3 证据脚本（`mcp014_m3_evidence.ps1`，已知它自身在第 183 行有 `Write-Utf8NoBom` 缺陷）。C# 轴的**可用性**是由「glue 生成 + Api/nupkg 产出 + 最小工程离线 build + 引擎实跑」四条独立实测支持的。

---

## 2. ② `accept_m1.ps1` → 22/22

### 2.1 四处过时期望，逐条

| 用例 | 原期望（M1 代） | 现在 | 依据 |
|---|---|---|---|
| `case1_GET_mcp_200` | `tools == 2` | `tools == $ExpectedEditorTools.Count` | 派生：6 份组清单的 implemented 并集 + rename map/added manifest 的 scope（与 `check_contract_subset.ps1` 同源），并与契约条数交叉校验 |
| `case3_tools_list_fixture` | 2 个 M1 工具 | 该端点全部工具逐字节比对 | 同上 |
| `case12_game_process_endpoint` | M1 游戏子集 | **派生 game 集**（旧函数表达不了 editor/game 之别） | 同上 |
| `guard_user_port_9877` | `pid_before > 0`（要求 9877 有监听） | 「本脚本从不碰 9877」：pid 前后相同 ∧ 若原本有监听则仍在且同 pid ∧ 9877 上的 pid 不是本脚本起的 | 实测 `listening_before=false pid_before=-1 pid_after=-1 same_pid=True survived=True touched_by_this_run=False`（9877 监听已退役） |

派生实测打印：`expectation : derived from 6 manifest(s) + rename map: implemented union=177, editor=154, game=73 (contract=177)`。

### 2.2 case0 / case20 重建，以及 TASK-087 的一个**证据错误**

`events-edit` 的 `seq` **只在单个 session 文件内唯一**。`seq=1030` 有两行：

| seq | time | path | 是什么 |
|---|---|---|---|
| 1030 | 1790155671555 | `tools/editor_shader_write.h` | C++ 注释重写 |
| 1030 | 1790321324515 | `scripts/accept_m1.ps1` | 加入 `case0_repo_exit_code_propagation` 的那一块 |

TASK-087 取到了**前一行**（一段 C++ banner）塞进 `.ps1`，所以才 17 个解析错误、才让全窗口并集里出现 `editor_shader_write.cpp` 的 banner。按 `(path, seq, time)` 选行后**逐字重放**：case0 `old 77 B → new 1998 B`，case20 `old 240 B → new 3061 B`（case20 的 `old` 是含 `Stop-Engine` 的那 6 行，`new` 把用例插在它**之前**——TASK-087 的嫁接把用例放在了 `Stop-Engine` 之后，于是 case20 在死掉的编辑器上跑，`Open-Connection` 抛 AggregateException；本次修正）。另外 case20 里对 `$ToolNames.Count` 的旧字面量也换成了派生值。

### 2.3 结果

`22/22 cases passed`，`[exitcode]=0`。
`case3` 证据行：`tools=154; editor verbatim 154/154 (declared schema deviations that really differ: 3 [editor_simulate_input_sequence, editor_list_signal_connections, editor_get_test_report])`。

**没有删断言**：`case3`/`case12` 的比对从「2 个工具」扩到「该端点全部工具，逐字节 name+description」，并加了**集合双向**检查（多一个、少一个都红）。唯一被「豁免」的是 `inputSchema` 差异，且只在**契约自己声明了 `inputSchema` override** 时才豁免，豁免名单**从 `_meta.overrides` 读**（不是手写清单），并打印实际豁免数。

---

## 3. ③ 硬编码计数

`docs\scripts\_tmp_gen_b3_b5.py` 的 `source.names` 与 `source.excluded` 里的 `171` 改为 `% (len(contract_names),)`。该文件今天本身跑不完（它的 SPEC 早于 6 个 ADDED_TOOLS，自检 `FATAL: unimplemented tool(s) missing`——**预先存在**，与本改动无关），所以改为**直接单元测试那两行表达式**：绑定真契约求值 → `177`，且两行上再无任何被扫描的数字化字面量。`check_hardcoded_counts.py`：`UNCLASSIFIED = 0`，`RESULT: PASS`（原来是唯一红门）。

---

## 4. ④ 契约

### 4.1 方法：拿实测发布文本当证据

窗口化真实会话抓到编辑器端点**完整的 154 条 `tools/list` 身体**（`live/editor-tools-list.json`，46 810 B），与 `docs/tools_list.renamed.json` 逐工具比对（`cmp_editor.txt`）：**恰好 10 个工具不一致** —— 7 条 description、3 条 inputSchema。

### 4.2 7 条 description 的处置

| 工具（fixture 名） | 方向 | 依据 |
|---|---|---|
| `set_project_setting` / `add_autoload` / `remove_autoload` / `set_input_action` / `reload_plugin` | append | 都是「原文 + `" "` + TASK-043 整文件写入诚实声明」；该句逐字取自录制 `scripts/mcp043_description_evidence.ps1:50` 的 `$Sentence`，且这 5 个工具的 C++ 字面量里确实逐字带着它（`editor_input_simulation.cpp:1244`、`editor_write_scene_editor.cpp:1026`、`project_autoload_write.cpp:256/263`、`project_setting_write.cpp:293`） |
| `validate_script` | append | 追加的是 TASK-055 的 `.cs` 裁决说明（1318 B） |
| `play_scene` | 已有记录，**value 换成实测文本** | 录制里这条改写是同一改写的更早一版；契约指纹 §2.3 没有它 |

实现：全部以 `json.dumps(实测字符串)` 写进生成器，并加 `# [REBUILT-2C low-confidence: verify]` 标记与逐条 `reason`（含被替换原文 + 证据路径）。

### 4.3 3 条 inputSchema **不是缺记录**

生成器**本来就声明**了 `simulate_sequence` / `find_signal_connections` / `get_test_report` 三个 `SCHEMA_OVERRIDES`，即契约**故意**比实现富。C++ 侧证实：`editor_simulate_input_sequence` 的富 schema 不在任何 `.cpp` 里（`grep 可粘贴样例 tools/*.cpp` = 0 命中）。因此契约比实现「富」是**契约自己声明的偏离**，本轮**未**把它降级、也**未**去改实现。

### 4.4 `_meta.map_path` 对齐到记录值

证据：`staging/__payload-index/events-termdump.jsonl` 有九处逐字写着
`"map_path": "F:\\RustProjects\\godot-mcp-pro\\code\\godot\\modules\\mcp_server\\docs\\tool-rename-map.json"`，且都与 `map_sha256 = 2f552719…`（本树 rename map 的同一个 sha）相邻（抽取见 `work/task088/map_path2.txt`）。
生成器新增 `RECORDED_MAP_PATH` 常量并让 `_meta.map_path` 用它，**不再**写本机构建根
（`os.path.abspath`）。这样 sha 差异只反映内容，不再被构建根路径污染。

### 4.5 六项 + 差值原因

| 项 | 值 |
|---|---|
| `count` | **177** |
| `added_count` | **6** |
| `generator_version` | **1.22.0** |
| editor / game | **154 / 73** |
| 幂等 | 连跑两次 `python gen_renamed_contract.py`，两次都 exit 0、都是 **146 595 B**、sha 都是 `724f03b851695e71692b76b6d5049a2f53e425d9f0b67a88f85a9d6098ccfa5b` |
| 生成器自检 | `OK (lint 177/177, unique 177/177, disposition enum OK)`；`old contract sha256 = 8f8051c4…`、`rename map sha256 = 2f552719…`（与 pinned 指纹**逐字相同**） |

**与 pinned `a5c59853…` 的差值，定量分解**：

| | pinned (`contract_fingerprint.txt`) | 现在 | 差 |
|---|---|---|---|
| bytes | 163 520 | **146 595** | **−16 925** |
| `_meta.overrides` | 36 | **32**（description 20 + inputSchema 12） | **−4** |
| 其余 meta 标量 | count 177 / added 6 / genver 1.22.0 / tool_count_in 174 / excluded / merged | **全等** | 0 |
| `_meta.map_path` | 记录根 `F:\RustProjects\…` | **同一值（已对齐）** | 0 |

差值原因（三项，逐条可核）：
1. **少了 4 条 override 记录**（36 vs 32）。我能用证据定位的是 **10 个不一致工具**，其中 7 条是 description（6 新 + 1 改值）、3 条是**已存在**的 schema 声明；所以新增记录是 6 条，不是 10 条。剩下 4 条**在证据里找不到**：契约没有整文件写入录制（`events-write` 对 `docs/tools_list.renamed.json` 为 0 行），指纹只钉了数组**长度**。**没有编造**。
2. **约 16.9 KB 的体积差**。每条新记录的 value 都是几百字节（7 条合计约 3.3 KB）。剩余约 13.6 KB 无法由我找到的 10 处差异解释——最可能的一项是**序列化形式**：pinned 那份 163 520 B 很可能是缩进后的 JSON（本树是紧凑形式）。**这是一个假设，不是结论**，未据此改动任何东西。
3. 差值的第三项已被消除：`map_path` 现在是记录值，不再引入 24 B 的构建根差。

---

## 5. ⑤ 溯源能力（本轮重点）

### 5.1 核实到的能力（全部实测在册）

| 能力 | 实测/依据 |
|---|---|
| `--mcp-capture=off\|on_error\|every_call`（默认 off） | 启动行 `[MCP] capture=enabled: mode=every_call viewport=2d dir=…` |
| `--mcp-capture-viewport=editor\|2d\|3d`（默认 editor） | 本轮用 `2d`；游戏侧恒 `game`（只有一个窗口） |
| 原图不截断保存 | 8 个编辑器 PNG 各 78 036 B、**2978×1793**（`scale=1` 即不缩放不拷贝）；启动行逐字 "capture keeps every PNG it writes (no size limit, nothing is ever deleted)"，只有 1 GiB 阈值 WARN，从不删除 |
| 像素差自动写入日志 | 捕获行带 `changed` / `changed_pixels` / `total_pixels` / `changed_pixel_ratio`，以及 before/after 的 `path/sha256/bytes/width/height` |

### 5.2 补齐的一处真缺陷：调用行没有请求身份

修复前的真实 trace（`live/trace-editor.jsonl` 旧版）里调用行是
`{"id":null,…,"method":""…,"capture":{…}}` —— **没有 `tool`、没有 `args`**，而紧邻的捕获行却写着 `"tool":"editor_open_scene"`。
即 JSON-RPC 层只把捕获态挂上了记录，请求身份从未填。本轮在 `mcp_jsonrpc.cpp` 补四处（全部包在
`// [REBUILT-2C low-confidence: verify] … // [/REBUILT-2C]` 里并登记 manifest G-2#1）：

* `dispatch`：`trace.id_json = id_json; trace.method = method;`
* `_dispatch_tools_call`：`r_trace.tool = tool_name;`
* `dispatch` 的 `tools/list` 分支：`trace.is_tools_list = true; trace.tool_count = get_visible_tool_count(...)`

依据：TASK-085 裁决 (C) 已记录 `dispatch` 是写出来的（录制里唯一的定义早于 trace 参数），方向由
`mcp_trace.h:132-182` 的字段声明与 `mcp_trace.cpp:322-346` 的读取条件唯一确定。

### 5.3 判定模型

`scripts/mcp_trace_ledger.py` 把「调用行 + 同 `seq` 的捕获行」合成**每次调用一行**：

```
verdict = failed                  ok=false
          ok_effect_observed      ok 且像素 changed      ← 有效，效果有画面证据
          ok_no_effect_observed   ok 且像素不变          ← 「报成功但没动」
          ok_effect_unavailable   ok 但本进程无法取景（诚实边界）
          ok_effect_not_observed  ok 但没开捕获（无信息，不得读作无效）
```

同时给出 `facts_complete`（request_id / tool / args（未截断）/ times / result / capture /
scene_evidence 是否齐备），用来区分「证据支持」与「推断」。文件侧副作用**没有**写进运行期日志，
台账显式写 `file_effect_evidence: "not_recorded_in_trace"`（声明的缺口，不写空成功）。
完整模型见 `modules/mcp_server/docs/reports/MCP-TRACEABILITY.md`。

### 5.4 实测演示（真实会话，窗口化）

驱动 `work/task088/mcp088_live_evidence.ps1`；编辑器 9888 + 游戏 9889，两侧都开
`--mcp-trace` + `--mcp-capture=every_call` + `--mcp-capture-dir=<绝对路径>` + `viewport=2d`。

| 产物 | 路径 | 实测 |
|---|---|---|
| 编辑器 trace | `…\work\task088\live\trace-editor.jsonl` | 10 行 |
| 游戏 trace | `…\work\task088\live\trace-game.jsonl` | 7 行 |
| 编辑器截图 | `…\live\shots-editor\` | **8 个 PNG**，各 78 036 B，2978×1793 |
| 游戏截图 | `…\live\shots-game\` | **6 个 PNG**，各 12 266 B |
| 编辑器 `tools/list` 原文 | `…\live\editor-tools-list.json` | 46 810 B / 154 工具 |
| 台账（文本/JSON） | `…\live\ledger-editor.txt` / `.json` | 见下 |

台账**逐行实测输出**：

```
calls=4 malformed_lines=0
verdicts: ok_effect_observed=1, ok_no_effect_observed=3

seq    req_id   tool                        dur_ms  ok    err  scene_effect  verdict
2      102      editor_open_scene           18      True  0    unchanged     ok_no_effect_observed
3      103      editor_get_scene_tree       18      True  0    unchanged     ok_no_effect_observed
4      104      editor_set_node_property    18      True  0    changed       ok_effect_observed
5      105      editor_set_node_property    19      True  0    unchanged     ok_no_effect_observed

rows whose reconstructible facts are all present: 4/4
```

**第 4 行是「有效」**（颜色写真的上了屏），**第 5 行同参数再写一次**（`ok=true` 但画面没动）被判
`ok_no_effect_observed` —— 这正是本模型要机械钉住的形态。`req_id`（102–105）与 `tool` 两列能读出来，
就是 §5.2 那处补齐的直接结果（修复前这两列是 `null` 与空）。

---

## 6. 门清单账本（9/9 全绿，真实输出）

| # | 门 | 命令 | 结果 |
|---|---|---|---|
| 1 | 模块 doctest | mono console exe `--headless --test --test-case=[MCPServer]*` | **exit 0** `143/143 passed/0 failed`、`6396/6396` 断言、`SUCCESS!`，`[module_exit]=0` |
| 2 | 全量 doctest | 同二进制 `--headless --test` | **exit 0** `1569/1569/0 failed/3 skipped`、`430709/430709`、`SUCCESS!`，`[full_exit]=0` |
| 3 | 组清单 | `docs/scripts/check_tool_groups.py` | **exit 0** `TOOL-GROUPS CHECK PASS`，5681 B，sha `b83d79d3…` |
| 4 | 契约子集（活链） | `scripts/check_contract_subset.ps1` | **exit 0** `3/3 checks passed`；editor 9888 `tools=154`、game 9889 `tools=73`、`guard_user_port_9877` PASS |
| 5 | rename map | `docs/scripts/check_rename_map.py` | **exit 0** `RESULT: PASS`；`177 == 174 - 2 - 1 + 6` |
| 6 | 同义反复 | `scripts/check_tautologies.py` | **exit 0** `TAUTOLOGY CHECK PASS` |
| 7 | 退出码传播 | `scripts/check_exit_propagation.py --probes` | **exit 0** `PROBES: 10/10` |
| 8 | 硬编码计数 | `scripts/check_hardcoded_counts.py` | **exit 0** `UNCLASSIFIED = 0`（**原为唯一红门**） |
| 9 | 引擎锚点 | `check_engine_anchor.ps1 -VersionText '4.8.dev.mono.custom_build.e4b025519'` | **exit 0** `ANCHOR_EQUAL` PASS（在 `6b4c29dc81` 上再判 `ANCHOR_STRUCTURAL_EQUIVALENT`，RED_COUNT=0） |
| + | M1 验收 | `scripts/accept_m1.ps1` | **exit 0** `22/22 cases passed`（原 16/20） |
| + | 溯源演示 | `mcp088_live_evidence.ps1` + `mcp_trace_ledger.py` | `calls=4`，`ok_effect_observed=1 / ok_no_effect_observed=3`，`facts_complete 4/4` |

**诚实标注**：**非 mono 二进制不在 HEAD**。`-VersionText '4.8.dev.custom_build.75d86665e'` 判为
`ANCHOR_STALE_COMPILED`，唯一红文件是 `modules/mcp_server/tests/test_mcp_server.h`。我没有为它再跑一次
整机非 mono 构建；因此 **HEAD 的测试证据用的是 mono 二进制**（门 1/2），而 `accept_m1` 与契约子集的结论
描述的是 HEAD 所服务的注册表（两者差异中唯一的编译输入只是测试头）。

---

## 7. 没做到的 / 遗留风险（如实）

1. **契约 override 还差 4 条记录**（36 vs 32），且契约比 pinned 小 16 925 B。原因见 §4.5：4 条记录在树内
   证据里找不到；约 13.6 KB 的体积差最可能来自序列化形式（**假设，未据此改动任何东西**）。
   **没有编造任何 override。**
2. **3 条 `inputSchema` 契约比实现富**（契约自己声明的偏离）。未降级契约、也未改实现。`accept_m1`
   只在契约声明了对应 override 时豁免该差异，并打印豁免数。
3. **非 mono 二进制未在 HEAD 重建**（§6）。
4. **文件侧副作用没有写进运行期日志**——这是溯源模型里唯一的能力缺口，已在
   `MCP-TRACEABILITY.md` §3.2 与台账里显式声明（`file_effect_evidence: "not_recorded_in_trace"`），
   未用空成功掩盖。
5. **游戏侧 73 条工具的 description 我只从 case12 的日志身体比对**（4 处不一致，全部也在编辑器集合内，
   已修）；没有为游戏端点单独跑一轮全量比对脚本。
6. 演示会话里 `editor_open_scene` 与 `editor_get_scene_tree` 都是 `unchanged`（打开场景没有改变 2D 主界面的
   像素），这是**如实结果**，不是演示失败：判定规则在这份证据上正常工作。
7. `check_engine_anchor.ps1` 的 PASS 在提交后是 `STRUCTURAL_EQUIVALENT`（diff 只是一个 `.md`），
   不是 `ANCHOR_EQUAL`——这是「二进制早于一个纯文档提交」的正确读数。

---

## 8. 收尾

```
git log --oneline -8
6b4c29dc81 modules/mcp_server: task088 (2c-7) step2 - the gate ledger (9/9) and the live traceability ledger
e4b025519a modules/mcp_server: task088 (2c-7) step1 - record identity on the trace, the six missing contract overrides, accept_m1 22/22
675df5ef27 modules/mcp_server: task087 (2c-6) - gate ledger, and accept_m1.ps1's four remaining FAILs named
586cb5e010 modules/mcp_server: task087 (2c-6) step5a - recover the two missing group manifests; contract subset gate is 3/3
ab99c693cc modules/mcp_server: task087 (2c-6) step1 - step-5 boundary review + the three conflict cases, suite honestly green
75d86665e6 modules/mcp_server: task087 (2c-6) step4 - G5 contract shape gate verified, 10 overrides still missing
8bbd589e52 modules/mcp_server: task087 (2c-6) step2 - accept_m1.ps1 parses with 0 errors
96a7d69186 modules/mcp_server: task087 (2c-6) step3 - DESIGN-DETAIL.md restored byte-exact (84,486 B)
```

```
git status --short
(empty)
git rev-parse HEAD                        = 6b4c29dc814d890f52ced72fa3c96783dfdcc399
git rev-parse origin/feature/...          = 6b4c29dc814d890f52ced72fa3c96783dfdcc399   (同步)
```

`git push`：两次，都 fast-forward、无 force、无拒绝 —
`675df5ef27..e4b025519a`、`e4b025519a..6b4c29dc81`。

**F: 未触碰证据**（开工与收尾各测一次，六项完全一致）：
`F:\moonbit-hof-rs\DECISIONS.md` **537 251 B** sha
`114B2A8218E35DF8E998FA4329D99F97D6037987E19FBA4A324B567C009CF323`；
`F:\moonbit-hof-rs\tests\fixtures\mcp\tools_list.json` **48 749 B** sha
`8F8051C4C0F8941089F0B21A193CEF7C51FA7C41D7E312B1463EA8593F313C54`
（该 fixture 是生成器的输入，**只读**）。

**Manifest 更新摘要**（§ 2c-7，已提交）：
G-1 纠正 2c-6 的 `seq=1030` 选行错误；G-2 六处「写出来的」改动逐条给依据与行为风险；
G-3 说明 3 条 inputSchema 是契约自己声明的偏离、以及 `_meta.overrides` 26→32 的道理；
G-4 实测演示产物表；G-5 三条流程坑（`-Wait` 等后代树 / `%ERRORLEVEL%` 解析期展开 / PowerShell 引号）；
G-6 九门账本；G-7 铁律与 F: 证据。
