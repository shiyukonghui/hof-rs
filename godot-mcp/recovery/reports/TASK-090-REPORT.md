# TASK-090 (2c-9) — 失败应答的 data 入日志 + D-3 场景树裁决 + 第 8 轮试测

* Repository: `H:\rebuild\godot`, branch `feature/mcp-server-module-rebuild`
* Start HEAD: **`b8e0142b81`** → End HEAD: **`382549f63e`**，**pushed**
  （`b8e0142b81..382549f63e feature/mcp-server-module-rebuild -> feature/mcp-server-module-rebuild`），
  `git status --short` **空**，与 origin 同步
* 试测工程: `H:\rebuild\projects\mcpplay8`（**新建，不在 F: 上**；`H:\rebuild\projects\mcpplay` 原封未动）
* Scratch/tooling: `C:\Users\wyl\AppData\Local\Temp\mcp-recovery\work\task090\`
* Logs: `C:\Users\wyl\AppData\Local\Temp\mcp-recovery\logs\task090_*`
* Manifest: `modules/mcp_server/docs/reports/REBUILT-2C-MANIFEST.md` § 2c-9（J-1..J-3）
* 文档: `modules/mcp_server/docs/reports/MCP-TRACEABILITY.md`（§0 / §2.1 / §3.1 / §3.2 / §4.3 / §5 已改写）

---

## 0. 四件事，逐条结论

| # | 要求 | 结论 |
|---|---|---|
| A | 失败应答的 `data` 纳入 trace（补完溯源模型最后一个洞） | **达成**。调用行新增 `error_data_json` / `error_data_json_bytes` / `error_data_json_truncated`，与成功分支的 `result_json` **同收口、同上限策略、同命名族**；写入点覆盖立即分支、延迟拒绝分支与延迟完成分支。实测：编辑器 3 条失败行逐字带 `suggestion`；游戏 `seq=14` 带完整 `parse_error`（`line=1` + 引擎消息）。落盘证据见 §1.3 |
| B | D-3 设计裁决：游戏侧执行器必须能触达运行中的场景树 | **达成**。执行体在**有场景树时编译成 `extends Node` 并挂到当前场景根节点下**，返回前必定移除（成功/失败同一路径）；无场景树时保持原 `RefCounted` 语义。实测 `get_parent().name -> "Main"`、`get_path() -> /root/Main/@Node@8`、节点读写产生像素差，且三次场景树快照**完全相同**。契约描述同步、生成器以 **append-only override** 声明、形状六项保持（177/6/1.22.0/154/73/幂等） |
| C | 第 8 轮试测（多步编排） | **达成**，并产出 **4 个根因明确的缺陷**，全部修掉后重跑同一批：①注入的 action 没进游戏（`in_input_map` 缺失）；②场景编排的断言对台账不可见；③两个驱动器的 deadline 用硬编码帧时间；④延迟应答的调用行**从不带 `result_json``。改进前后对比见 §3.4 |
| D | 九道门 + accept_m1 + 提交 + F: | 九门全绿、accept_m1 22/22、5 次提交全部 push、F: 未触碰（逐字节核验）。**因契约描述变更，非 mono 二进制也必须重建**（`accept_m1` 跑的是它），这一点单独说明（§5.3） |

---

## 1. A) 失败应答的 `data` 入 trace

### 1.1 设计：一处收口，两条通道

| 位置 | 覆盖 |
|---|---|
| `mcp_jsonrpc.cpp` → `_record_error_data()`（新） | 立即工具错误分支 + 延迟拒绝分支 |
| `mcp_http_server.cpp` → `_tick_pending()` | 延迟通道的**完成**处（`completion.error.data`：`timeout_ms` / suggestion） |
| `mcp_trace.cpp` → `_build_line()` | 在既有 `method == "tools/call"` 块里，**每一次失败都写**（工具没带载荷就写 `""`） |

字段名与成功的 `result_json` 同族：`error_data_json` / `error_data_json_bytes` /
`error_data_json_truncated`；上限沿用 `max_args_bytes`（真实字节数另给）。
**「字段存在」因此可以与「这条 trace 出自旧版本」区分开**——这一点是刻意设计的，不是副产品。

读取侧（`scripts/mcp_trace_ledger.py`）：每行新增 `error_data` / `error_data_evidence`
（`not_applicable` / `recorded_in_trace` / `recorded_in_trace_no_payload` / `not_recorded_in_trace` …）、
`error_flags`（`error_suggestion` / `error_parse_error`），文本报告新增 **failure payloads** 一段；
`error_data` 进入可重建性 `FACTS`。

### 1.2 实测（①② 两条都落盘）

编辑器（`live-after3/ledger-editor.txt` 第 38–41 行）：

```
failure payloads (`error_data_json`) present on 3/27 call(s)
  seq=12 req_id=112 project_create_resource err=-32000 | {"suggestion":"Set overwrite=true to replace the existing file"}
  seq=13 req_id=113 project_create_scene_file err=-32000 | {"suggestion":"Delete it first with project_delete_scene_file, or choose another path"}
  seq=15 req_id=115 project_delete_scene_file err=-32001 | {"suggestion":"Use project_get_filesystem_tree to list the .tscn files of the project"}
error_data_evidence: not_applicable=24, recorded_in_trace=3
```

游戏（`live-after3/ledger-game.txt`）`seq=14 req_id=314`：

```
{"parse_error":{"generated_line":4,"in_caller_code":true,"line":1,
 "message":"Parse Error: Expected grouping expression.","messages":["Parse Error: Expected grouping expression."]},
 "parse_error_column":null,
 "suggestion":"Parameter 'code' accepts a string (required); Accepted parameters of running_game_execute_gdscript: code"}
```

「行列与消息」：**行与消息原文都在 trace 上**；**列如实写 `null`**，理由与 TASK-063(d) 相同
（`ParserError` 带 `start_column`/`end_column`，但调用点在任何 handler 之前就丢掉了它，
`gdscript.cpp:828`）——不发明一个数字。

### 1.3 落盘证据路径

* trace：`…\work\task090\live-after3\trace-editor.jsonl`（行 23/25/29）、`trace-game.jsonl`（行 28）
* 台账：`…\live-after3\ledger-editor.txt` / `ledger-game.txt`（+ `.json`）
* doctest：`tests/test_mcp_server.h` 的
  `[MCPServer] a failed tools/call carries its data payload on the trace line`（三种形状：
  带 suggestion 的 -32602、带 parse_error 的 -32602、成功行没有任何 error_data 字段）
* 文档：`MCP-TRACEABILITY.md` §2.1 / §3.1 / §3.2 / §5

---

## 2. B) D-3 裁决：游戏侧执行器触达运行中的场景树

### 2.1 选定的实现（以及被否决的另外两条）

**选定**：有可达场景树时，执行体编译成 **`extends Node`**，实例被 `add_child` 到**当前场景根节点**
（没有 current scene 时挂到 tree root）下，调用结束（成功或失败）**在同一个函数里**移除并释放。

被否决的两条，理由写在 `tools/running_game_script_execution.h` 与 manifest J-2：

* **「把场景根注入成可访问上下文」**——做不到。`get_node()` 是 `Node` 的方法，`RefCounted` 上根本不存在；
  注入只会多出一套 `root.get_node(...)` 的写法，而引擎已经把它拼作 `get_node(...)`。
* **「把执行脚本 `set_script()` 挂到既有场景根上」**——真污染。恢复原脚本要重建脚本实例，
  场景根自己脚本的 `_init`/`_ready` 状态会丢；这不是「临时挂载」。
* **自己的挂载点、返回前移除**——唯一有**确定性收尾**的一条：一次 `add_child`、一次 `remove_child`、
  一次释放，成功路径和两条失败路径都走同一段清理。

**声明的边界**（写进契约描述与头文件）：节点存活不足一帧 ⇒ `_process`/`_physics_process` **不会 tick**
（body 里定义 `_ready` 会照常运行，那是普通 Godot 语义）；`$Path`/`get_node()` 以临时节点为基准
（父节点是场景根，绝对路径与 `get_tree().current_scene` 可达任意节点）；无场景树的进程保持原
`extends RefCounted` 语义**逐字节不变**。

### 2.2 契约同步（含生成器声明，不只是改一行 JSON）

`docs/tools_list.renamed.json` 是**生成物**（`_meta.generated_from` = F: 的只读 fixture，
`generated_from_sha256 = 8f8051c4…`）。所以描述不是手改一行就完事：

* `scripts/gen_renamed_contract.py` 新增 `DESCRIPTION_OVERRIDES["execute_game_script"]`
  （**append-only**，默认模式），原文 `在运行中的游戏内执行 GDScript 代码` 逐字保留在句首，追加段说明
  场景树可达、路径基准、生命周期；
* 重跑生成器（两次）→ **幂等**，输出 sha256 = `4BE4285CD221A877712370E6A4C73426E0CC7B94C2B6E32D59B3AED69760ED3A`；
* 形状六项：**177** 条 / **added_count 6** / 生成器 **1.22.0**（按任务要求不升版）/ 编辑器端 **154** /
  游戏端 **73**（门 4 复证）/ **幂等**；
* `F:` fixture **只读**：生成器打印的 `old contract sha256 = 8f8051c4c0f8941089f0b21a193cef7c51fa7c41d7e312b1463ea8593f313c54`
  与 TASK-089 记录逐字节相同；
* `scripts/gen_b2_game_schema.py --group running_game_script_execution --in-place` 重出 C++ 生成段
  （第二次运行是 no-op），doctest 里钉住的字面量与契约**程序化比对为真**。

### 2.3 doctest（钉住新能力）

`[MCPServer] running_game_execute_gdscript reaches a live scene tree and leaves it alone`：
doctest 进程没有 `SceneTree`，所以核心被导出为
`execute_gdscript_code(code, tool_script, mount_point, error)`，由测试自己搭一棵真实的节点树：

1. `return get_parent().get_node("Player").name` → `"Player"`（读到调用前就存在的节点属性）；
2. 通过同一条路径 `set_name("Moved")` 真的写到了游戏自己的节点，且**从内部看挂载点是 2 个子节点**
   （`Player` + 自己），**返回后回到 1**；
3. 编译失败：`-32602`；运行期失败（`get_node("NoSuchChild")`）后挂载点同样干净；
4. 无挂载点时是改造前的 `RefCounted` 语义（引擎单例可用）。

`tests/test_mcp_server.h` 的用例数 **148 → 150**（门 1 复证）。

### 2.4 实测（live-after3）

见 `MCP-TRACEABILITY.md` §4.3 的表格：`get_parent().name = "Main"`、`Player.get_path() = /root/Main/Player`、
`get_path() = /root/Main/@Node@8`（执行体自己在树里、父节点是场景根）、
`get_tree().current_scene.name = "Main"`；移动/改色/改 HUD 文本分别产生
12 800 / 12 800 / 6 400 / 1 363 px 的**独立复算**像素差；同参数重复调用 0 px。

**「不污染」的直接证据**：`live-after3/analysis.json` 里 `g01`（执行器批量之前）、`g13`（之后）、
`g30`（会话末尾）三份场景树快照各 5 个节点、`path+type` 序列**完全一致**
（`identical_before_after: true`、`identical_before_final: true`）。

---

## 3. C) 第 8 轮试测

### 3.1 会话设计与覆盖

`…\work\task090\mcp090_live_evidence.ps1`：每次会话先把工程重置到同一份
`project.godot` / `main.tscn` / `main.gd`（+ 删掉上一轮的产物），再 import，再跑 **27 次编辑器调用
（id 101–128）+ 30 次游戏调用（id 301–330）**，全程 `--mcp-trace` + `--mcp-capture=every_call`
（`--mcp-capture-viewport=2d`，窗口化非 headless）。

* ①**驱动游戏循环**：执行体读写运行中场景状态（位置/颜色/HUD 文本）→ 截图 + 像素差（§2.4）。
* ②**批量节点树改动**：同一会话里 6 次节点写（执行体 4 次 + `running_game_set_node_property` 2 次），
  每次都有像素与/或文件证据；`seq=16/17` 是「同值再写 → 0 px」的对照。
* ③**输入模拟 + 断言编排**：Button 文本点击（+1 600 px）→ `assert_node_state` 通过；
  带错值的断言 → `assertion_failed`；deferred 场景 `input → wait → assert` 两条（一条该通过、一条该失败）。
* ④**资源/场景文件建删 + 工程设置**：`project_create_scene_file` / `project_create_resource` /
  `project_delete_scene_file` / `project_edit_script` / `project_set_setting` / `editor_save_scene` /
  `editor_capture_screenshot`，含 **6 次必须失败**的调用（编辑器 3 + 游戏 3），用来验证失败应答的 `data` 可溯源。

### 3.2 台账（最终会话；命令与产物路径见 §1.3）

```
编辑器 calls=27  facts_complete 27/27
  verdicts: failed=3, ok_effect_observed=1, ok_file_effect_observed=10, ok_no_effect_observed=13
游戏   calls=30  facts_complete 28/30
  verdicts: failed=3, ok_effect_observed=6, ok_effect_unavailable=2, ok_file_effect_observed=5, ok_no_effect_observed=14
```

**判定分布**：`failed=3+3` 全部是**刻意构造**的失败（2 个已存在/不存在 → -32000/-32001，
1 个 parse error，1 个找不到的节点，1 个找不到的 Button，1 个只读读工具类的正常失败）。
`ok_file_effect_observed` 里包含 5 条断言调用——它们写测试报告桥文件，因此**文件侧**可观测（TASK-089 D-5
的已知口径，不是缺陷）。

**`facts_complete` = 28/30（游戏）**：两行不完整都是 deferred 场景调用，缺的是 `file_effect`
（`not_tracked_deferred`）与 `scene_evidence`（引擎自己写明
`"the call is answered across frames (deferred), which the capture does not cover"`）——
**声明的边界**，不是丢失的证据。编辑器端 27/27。

### 3.3 缺陷清单（工具名 + trace 行号/请求 id + 证据 + 根因判断）

| # | 工具 · trace 位置 | 现象 | 截图/像素差 | 文件 sha | 根因判断 → 处置 |
|---|---|---|---|---|---|
| **E-1** | `running_game_run_test_scenario` · 游戏 `seq=25/26`（行 51/53，id 325/326） | 注入 `mcp_right` 后玩家**没动**（actual x=70，expected 95），步骤却回 `injected:1`；`all_passed:false` | capture `unavailable`（deferred 覆盖不到，引擎给的 reason 在行里） | 无（未碰盘） | **不是工具 bug，是契约空隙**：事件确实送到了 `_input`（before-run 的 stderr 带 `main.gd:24 _input` 的 GDScript backtrace），但 `InputEvent::is_action_pressed` 走 `InputMap::event_get_action_status`，后者对**未声明的 action** 直接返回 false（`core/input/input_map.cpp:291-292`）。探针 `probe_action.ps1` 实测 `InputMap.has_action("mcp_right") = false`，连**直接注入**也不动 → 修：项目侧声明 action（工程修复），模块侧按同一字段名补 `in_input_map`（与 `editor_simulate_input_action` 一致） |
| **E-2** | 台账 `result_flags` | 场景编排的结论（`all_passed` / `failed` / `errors`）**进不了 flags**，台账无法回答「断言成立吗」 | — | — | 读取侧只认顶层 `passed:false`/`created_conflict`，而场景把判定嵌在 `results[]` 并用 `all_passed` 汇总 → 修 `mcp_trace_ledger.py`，新增 `scenario_passed` / `scenario_assertion_failed` / `scenario_errors` / `scenario_asserted_nothing` |
| **E-3** | `running_game_run_test_scenario` / `running_game_run_stress_test` · 游戏 `seq=25`（行 51）`timeout_ms=1150` | 一次**每调用 250–530 ms** 的运行里，一个 0.4 s、3 步的场景**做对了全部动作**却被自己的 1150 ms 估计杀掉（`-32000`，`data.timeout_ms: 1150`，`completed_steps` 丢失） | capture `unavailable` | 无 | 两个驱动器都**按帧推进**（一帧一步/一次迭代），deadline 却按硬编码帧时间算（每步 250 ms / 每迭代 16 ms）→ 修：`_frame_cost_ms()` 读**本进程自身帧率**（下限保持旧常量，60 fps 时 deadline 与从前完全一样）；实测修复后同一场景 `timeout_ms=4396`，`duration_ms=474` 正常结束 |
| **E-4** | 延迟通道的调用行 · 游戏 `seq=25/26`（行 51/53） | 场景**答了** `all_passed:true/false`，但调用行**没有 `result_json`**（只有 `result_bytes`） | — | — | TASK-089 的 `result_json` 只在**立即**成功分支写；延迟完成处（`_tick_pending`）只写了 `ok/error_*`。而场景/压力工具**整个答案就是判定** → 修：`_tick_pending` 从 `completion.result` 写同族字段（与 `build_deferred_body` 包的是**同一个 Variant**） |

**只记录、不猜改的两条（不是缺陷，口径写进文档）**：

* **capture 的 `changed_pixels` 不按「任意差异」算**：`seq=8`（改 HUD 文本）trace 报 1 363，
  按「任意差异 > 0」重算是 1 464，差的 101 个像素全在阈值以下。按引擎自己的规则
  （`max(|dr|,|dg|,|db|) > 10`，`mcp_capture.cpp:68` + `tool_helpers.cpp:1223`）重算 =
  **1 363，28/28 逐对相等**。这是我方读数口径问题，不是 trace 的错——已把这个规则写进
  `analyse_round8.py` 并留在报告里。
* **deferred 的 `scene_effect=unavailable` / `file_effect=not_tracked`**：引擎逐帧 tick 才做实际工作，
  同步的每调用缓冲看不到画面与磁盘。声明的边界（也正是 `facts_complete 28/30` 的原因）。

### 3.4 改进前后对比（**同一批调用**，同一工程，同一种开关）

四轮跑下来，每一轮暴露下一个缺陷，最后一轮全绿。bat.: editor / game：

| 轮次 | 二进制（构建时 HEAD + 已含修复） | 编辑器台账 | 游戏台账 | 场景编排两行 |
|---|---|---|---|---|
| `live-before` | `b8e0142b81` + A/B | failed=3 / ok_effect=1 / ok_file=10 / ok_no_effect=13；facts 27/27 | failed=3 / ok_effect=6 / ok_unavail=2 / ok_file=6 / ok_no_effect=13；facts **28/30** | **没有 `in_input_map`**，事件不动玩家，`all_passed:false`；**没有 `result_json`** → flags 空 |
| `live-after` | + E-1/E-2 | 同上（不变） | failed=**5**（多 2 条 deferred 超时） | 被自己的 1150 ms deadline 杀掉 |
| `live-after2` | + E-3 | 同上 | failed=3 | `all_passed` 有值但**调用行仍无 `result_json`** |
| `live-after3` | + E-4 | **failed=3 / ok_effect=1 / ok_file=10 / ok_no_effect=13；facts 27/27**（与 before 逐项相同） | failed=3 / ok_effect=6 / ok_unavail=2 / ok_file=5 / ok_no_effect=14；facts 28/30 | **`scenario_passed` / `scenario_assertion_failed`**；`in_input_map:true`；玩家 x 95.0 与实际一致 |

**编辑器端逐项相同**是「这一批修复没有改变工具行为」的证据；游戏端唯一移动的一行是
`seq=29 running_game_capture_screenshot`：`changed` → `unchanged`，因为 `user://round8-game.png`
在 `user://` 里**跨轮留存**，而同一批调用产生的最终画面逐字节相同（这一条如实记录，不算回归）。

**会话内 `MCP090_MOVE` 输出**（游戏 stdout，最直观的因果链）：

```
before ：MCP090_MINIGAME_READY name=Main player=(100.0, 220.0)          （没有 mcp_right_in_map）
         MCP090_MOVE moves=1 x=70.0                                     （只有 Button 点击）
after3 ：MCP090_MINIGAME_READY name=Main player=(100.0, 220.0) mcp_right_in_map=true
         MCP090_MOVE moves=1 x=70.0   ← Button 点击（seq=22）
         MCP090_MOVE moves=2 x=95.0   ← 场景注入的 mcp_right（seq=25）  ← 修好了
         MCP090_MOVE moves=3 x=120.0  ← 第二条场景（seq=26）
```

---

## 4. D) 收尾

（九门与 accept_m1 的真实输出见 §5；本节先给方法与产物路径。）

* 门 1/2/9 与九门总跑：`…\work\task089\run_gates.ps1`（每个门一个 `cmd.exe` 子进程，
  `Start-Process -RedirectStandardOutput`，退出码在子进程内部回显后解析）。
* 9 个门的命令与 TASK-089 完全一致（含 `-VersionText 4.8.dev.mono.custom_build.<HEAD>`）。
* `accept_m1`：`powershell -NoProfile -ExecutionPolicy Bypass -File modules\mcp_server\scripts\accept_m1.ps1`。
* 提交：5 次（step1..step5），每次 `git push`。
* F: 未触碰：开工/收尾两次 `Get-FileHash`，见 §5.4。

---

## 5. 门与收尾的真实输出

### 5.1 九道门（真实输出）

二进制：`bin\godot.windows.editor.x86_64.mono.console.exe`，构建于 HEAD `8604fcf9e`
并自报 `4.8.dev.mono.custom_build.8604fcf9e`；非 mono 变体同源重建，自报 `4.8.dev.custom_build.8604fcf9e`。
九门串行跑（`work/task089/run_gates.ps1 -Tag task090_final3`），每个门一个 `cmd.exe` 子进程、
各自的 stdout/stderr、退出码在子进程内部回显后解析。日志 `logs/task090_final3_g0*.{stdout,stderr}.txt`，
汇总 `logs/task090_final3.summary.txt`。

| # | gate | 命令 | 结果 |
|---|---|---|---|
| 1 | module doctest | `--headless --test --test-case=[MCPServer]*` | **exit 0** — `150/150 passed`、`6510/6510` assertions、`SUCCESS!`（2c-8 是 148，本批 +2） |
| 2 | full doctest | `--headless --test` | **exit 0** — `1576/1576 passed / 3 skipped`、`430823/430823` assertions、`SUCCESS!` |
| 3 | group manifests | `python modules\mcp_server\docs\scripts\check_tool_groups.py` | **exit 0** — `TOOL-GROUPS CHECK PASS`，`BYTES 5681`，`SHA256 b83d79d3…`（与 2c-8 逐字节相同） |
| 4 | contract subset (live) | `scripts\check_contract_subset.ps1` | **exit 0** — `3/3 checks passed`；`editor port=9888 tools=154`、`game port=9889 tools=73`、`guard_user_port_9877` PASS |
| 5 | rename map | `python modules\mcp_server\docs\scripts\check_rename_map.py` | **exit 0** — `RESULT: PASS (all checks green)` |
| 6 | tautologies | `python scripts\check_tautologies.py` | **exit 0** — `TAUTOLOGY CHECK PASS`（scanned 2 root(s)） |
| 7 | exit-code propagation | `python scripts\check_exit_propagation.py --probes` | **exit 0** — `PROBES: 10/10` |
| 8 | hardcoded counts | `python scripts\check_hardcoded_counts.py` | **exit 0** — `RESULT: PASS (every occurrence of 171/173/175/176/152/72/153 is classified; none is UNCLASSIFIED)` |
| 9 | engine anchor | `check_engine_anchor.ps1 -VersionText 4.8.dev.mono.custom_build.8604fcf9e` | **exit 0** — `ANCHOR_JUDGE VERDICT=ANCHOR_EQUAL`，`diff_count=0`，`RESULT PASS` |
| + | M1 acceptance | `powershell -NoProfile -ExecutionPolicy Bypass -File modules\mcp_server\scripts\accept_m1.ps1` | **exit 0** — **`22/22 cases passed`**（`logs/task090_accept_m1.stdout.txt`） |

**门 9 的一次真实失败记录（有价值，保留）**：本任务中段我先用构建期 HEAD 的 `-VersionText`
跑门 9，judge 给出 `ANCHOR_STALE_COMPILED`：

```
ANCHOR_JUDGE REASON=cac01b5f9 is an ancestor of eee58538a but the diff contains 1 file(s)
   that can change the compiled binary: COMPILE_INPUT:modules/mcp_server/mcp_http_server.cpp
```

即「二进制自报的提交不是 HEAD，且两者之间的差异里有**会改变二进制**的文件」——脚本自身退出码仍是 0，
判 FAIL 的是 judge。处置：在最终 HEAD 重建两个变体后重跑，才得到上面的 `ANCHOR_EQUAL`。
这条正好说明门 9 是**真的在看**，而不是在复读退出码。

### 5.2 accept_m1 的失败与修复（真实过程）

中途一次 `accept_m1` 得到 **21/22**，唯一失败项：

```
[FAIL] case12_game_process_endpoint
       ... running_game_execute_gdscript: description differs | game verbatim 72/73
```

根因：`scripts/accept_m1.ps1:53` 写死跑**非 mono** 二进制，而 item B 改了该工具的契约描述，
非 mono 变体自 TASK-089 起从未重建 → 它服务旧描述。**重建非 mono 变体后 22/22**（§5.1 末行）。
这也是本任务比任务书多出来的一步：**改了契约就要把两个变体都重建**。

### 5.3 一个必须说清的环境事实：`accept_m1` 跑的是**非 mono** 二进制

`scripts/accept_m1.ps1:53` 写死 `bin\godot.windows.editor.x86_64.console.exe`（**非 mono**），
而 TASK-090 的 item B 改了 `running_game_execute_gdscript` 的**契约描述**，`case12` 会把
游戏端 `tools/list` 逐字与 `docs/tools_list.renamed.json` 比。非 mono 二进制自 TASK-089 起就没重建过
（TASK-089 报告已声明），它服务的是**旧描述**，于是 case12 报
`running_game_execute_gdscript: description differs | game verbatim 72/73` → 21/22。
这不是代码回归，而是「改了契约就必须把两个变体都重建」——本任务把 **mono 与非 mono 两个变体
都在最终 HEAD 重建**，见 §5.1/§5.2。

### 5.4 F: 未触碰的证据

| 文件 | 字节 | sha256（开工 = 收尾，逐字节相同） |
|---|---|---|
| `F:\moonbit-hof-rs\DECISIONS.md` | 537 251 | `114B2A8218E35DF8E998FA4329D99F97D6037987E19FBA4A324B567C009CF323` |
| `F:\moonbit-hof-rs\tests\fixtures\mcp\tools_list.json` | 48 749 | `8F8051C4C0F8941089F0B21A193CEF7C51FA7C41D7E312B1463EA8593F313C54` |

生成器打印的 `old contract sha256 = 8f8051c4c0f8941089f0b21a193cef7c51fa7c41d7e312b1463ea8593f313c54`
是**同一次读取**的独立复算。

### 5.5 未做到 / 遗留（如实）

1. **`in_input_map` 没有 doctest 钉住**：这条代码路径在 `TestScenarioTask::tick()` 里，而 doctest
   进程的 Input 单例只在 `[SceneTree]`/`[Editor]` 用例里存在，本模块的用例都是 `[MCPServer]`。
   同一字段在 **编辑器侧** `editor_simulate_input_action` 上已有 doctest
   （`tests/test_mcp_server.h` 的 `CHECK_FALSE((bool)not_in_map["in_input_map"])`），
   游戏侧由第 8 轮 trace 实测钉住（`"in_input_map":true`）。**声明这个缺口，不假装覆盖。**
2. **`_tick_pending` 的 `result_json` 也没有 doctest**：它需要构造一个带 recorder 的
   `MCPHttpServer` 并推进 pending 完成，现有用例只测到 HTTP 报文层。由第 8 轮 trace 实测钉住
   （`seq=25` 的 `result_json` 与 wire body 同源）。
3. **`_frame_cost_ms()` 读的是瞬时帧率**：`seq=25` 的 `timeout_ms=4396` 而一秒后 `seq=26` 是 `1150`
   ——说明采用时刻的 fps 读数可能继承一次瞬时卡顿。影响是**放宽** deadline（上限被框架的 30 s 夹住），
   不会误杀；但「同一会话两条相同场景拿到不同 deadline」这件事本身记在这里。
4. **非 mono 二进制本轮才重建**：TASK-089 声明它落后；本轮因契约变更必须重建（否则 `accept_m1`
   case12 必然失败），重建后自报 `4.8.dev.custom_build.8604fcf9e`，与 mono 变体同源。
5. **`user://round8-game.png` 跨轮留存**导致截图调用在重放时从 `changed` 变 `unchanged`
   （§3.4），不是缺陷但会影响「前后逐行对比」的读法。
6. **capture 对 deferred 一律 `unavailable`**：引擎自己给的 reason 已在行里，但「deferred 调用的
   画面效果」仍然无法从 trace 证明——声明的边界。

---

## 6. 提交、git 状态与门 9 的最终判定

6 次提交（每次 `git push`，最终 `382549f63e` 与 `origin/...` 一致）：

```
382549f63e modules/mcp_server: task090 (2c-9) step6 - the round-8 record: the traceability section and the gate ledger
8604fcf9e2 modules/mcp_server: task090 (2c-9) step5 - the description change is declared in the generator, so the contract stays reproducible
eee58538a1 modules/mcp_server: task090 (2c-9) step4 - a deferred call's own body reaches its trace line too
cac01b5f9f modules/mcp_server: task090 (2c-9) step3 - the round-8 fixes: the InputMap fact, the scenario flags, the frame-based deadline
a455a87bea modules/mcp_server: task090 (2c-9) step2 - D-3: the game executor reaches the running scene tree
4b8625bedc modules/mcp_server: task090 (2c-9) step1 - the failure answer's data payload reaches the call line
b8e0142b81 modules/mcp_server: task089 (2c-8) step3 - the gate ledger (9/9 + 22/22) and the iron-rule record
80035ed115 modules/mcp_server: task089 (2c-8) step2 - the round-7 test loop: three defects fixed, the trace now carries the tool's own answer
```

`git status --short` = **空**（提交后核验）；`git rev-parse --short HEAD` = `git rev-parse --short
origin/feature/mcp-server-module-rebuild` = `382549f63e`。

**门 9 在最终 HEAD 上复判**（step6 只改了两个 `.md`，非编译输入）：

```
ANCHOR_JUDGE SUMMARY anchor=8604fcf9e anchor_reported=8604fcf9e head=382549f63
  verdict=ANCHOR_STRUCTURAL_EQUIVALENT ancestor=yes diff_count=2 safe_count=2 red_count=0
  reason="8604fcf9e is an ancestor of 382549f63 and all 2 file(s) in the diff are non-compiling;
          the binary is NOT equal to HEAD, it is structurally equivalent to it"
  diff=[S:modules/mcp_server/docs/reports/MCP-TRACEABILITY.md S:modules/mcp_server/docs/reports/REBUILT-2C-MANIFEST.md]
ANCHOR_JUDGE RESULT PASS
```

即：二进制自报 `8604fcf9e`，最终 HEAD `382549f63e` 是它的后代且差异**全部非编译**——
门 9 如实给出 `ANCHOR_STRUCTURAL_EQUIVALENT`（与 TASK-089 在收尾提交后的同一种判定）。

---

## 7. 复现

```
# 1) 重生成契约（幂等）与生成段
python modules\mcp_server\scripts\gen_renamed_contract.py
python modules\mcp_server\scripts\gen_b2_game_schema.py --group running_game_script_execution --in-place tools/running_game_script_execution.cpp

# 2) 两个变体（bin\obj 共享，必须串行）
"C:\Users\wyl\AppData\Local\Temp\mcp-recovery\work\task090\task090_build_both.cmd"

# 3) 第 8 轮会话（前后对比：换 -Root 与 -RunTag 即可重放同一批调用）
powershell -NoProfile -ExecutionPolicy Bypass -File C:\Users\wyl\AppData\Local\Temp\mcp-recovery\work\task090\mcp090_live_evidence.ps1 -Root <dir> -RunTag <tag>

# 4) 台账 + 工具外像素/场景树复核
python modules\mcp_server\scripts\mcp_trace_ledger.py <dir>\trace-game.jsonl --text <dir>\ledger-game.txt --json <dir>\ledger-game.json
python C:\Users\wyl\AppData\Local\Temp\mcp-recovery\work\task090\analyse_round8.py <dir> --label <tag>
```
