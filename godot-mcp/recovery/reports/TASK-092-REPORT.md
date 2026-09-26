# TASK-092 — 恢复档案迁回本项目 + 三条溯源缺口收口（args 旁路证据 / 延迟调用的文件与画面证据 / 两个缺失的 doctest / 帧代价稳定化）

* 执行者：工具/迁移工程师（本会话，**有写权限，未再委派**）
* 主仓：`F:\moonbit-hof-rs`（分支 `master`，无远程）
* 引擎仓：`F:\moonbit-hof-rs\godot-mcp\godot`（分支 `feature/mcp-server-module-rebuild`，
  remote `git@github.com:shiyukonghui/godot.git`）
* 脚本 / 日志 / 中间产物：`godot-mcp\recovery\work\task092\`
* 时间：2026-09-26 / 09-27

---

## 0. 逐条结论

| 段 | 要求 | 结论 | 证据 |
|---|---|---|---|
| **A①** | 恢复档案迁回 `godot-mcp\recovery\`，先复制 → 逐文件 sha → 才删 C: 源 | **达成** | 33,433 文件 / 2,520,301,348 B，`compared=33433 mismatched=0 size_mismatch=0 missing=0 extra=0`，两侧字节数**精确相等** → `VERIFY_RECOVERY=PASS`（`work\task092\logs\verify.txt`） |
| **A②** | 主仓 .gitignore 忽略体量大者、保留并提交小而有价值者 | **达成** | 入库 **2,436 文件 / 75.6 MB**；忽略 26 个入口（≈31,020 文件 / 2.33 GB）：`transcripts\ staging\ logs\ tmp\ backup\ rebuild\godot\`、`work\events-*.jsonl`、三个嵌套 `.git` 与两个含它的目录 |
| **A③** | README 增补 recovery 一节 | **达成** | `godot-mcp\README.md` §8（内容清单 + 分界线 + 为什么忽略 `rebuild\godot`） |
| **A④** | 主仓提交、`git status` 干净 | **达成** | `d043fd3`；收尾时只剩本次任务的新增证据与报告（随 `C` 段提交） |
| **B①** | `args_truncated` 要有可核的旁路证据，台账据此判 `args_complete`，判据写进 MCP-TRACEABILITY.md | **达成** | 超限载荷整份写入 `<trace 名>.sidecar/`，行上给 `path`/`relative_path`/`bytes`/`sha256`；台账**读盘重算**后判 `sidecar_verified`；文档 §2.6 / §3.1（+§6） |
| **B②** | 延迟调用在完成时带上文件副作用 + 完成时刻截图与像素差；做不到要写明为什么并给明确状态名 | **达成** | 文件侧在 `Queue::tick()` 跨窗口累计（`observed_changed` / `no_mutation` / `not_tracked_deferred`）；画面侧 `before` 在请求帧、`after` 在完成帧之后（`frames_waited` 6–51）。**实测 `not_tracked_deferred` 已从两侧台账消失** |
| **B③** | 补两个缺失的 doctest（`in_input_map` 两种；`_tick_pending` 的 `result_json`） | **达成**，并多补 3 条 | `in_input_map`（已声明/未声明，走导出的 `create_test_scenario_task`）、`_tick_pending` 的 `result_json`（**真实环回 socket 驱动运输层**）；另加 sidecar、延迟窗口、帧代价三条 |
| **B④** | `_frame_cost_ms` 改用稳定估计并写明取值规则 | **达成** | 新增 `mcp_frame_clock.{h,cpp}`：最近 15 帧**中位数**、截断到整毫秒、夹 [16,1000]，采样点 `MCPServer::pump_frame`；规则表见 MCP-TRACEABILITY.md §6 |
| **B⑤** | 重建 mono + 非 mono，重跑九道门 + accept_m1（真实输出） | **达成** | 两变体 build exit 0，自报 `cf554ef58` == HEAD；**g01–g10 全部 exit 0**，`accept_m1 22/22`，门 9 `ANCHOR_EQUAL diff_count=0` |
| **B⑥** | 重跑 Pong 会话，`facts_complete` 达 100%，给改进前后对比 | **达成** | 编辑器 **23/23**、游戏 **29/29**（前：21/23、23/29）；报告缺陷清单 **0 条**；52/52 像素对独立复算一致 |
| **C** | 每步提交（引擎 push）、报告含两仓 log/status、如实报告 | **达成** | 引擎 2 次提交并 push（`87fbf82f4b..cf554ef58c`）；主仓 2 次提交；见 §C |

---

## A. 恢复档案迁回本项目

### A1 方法与校验（铁律 1/2/3/4 全程）

| 步骤 | 做法 | 结果 |
|---|---|---|
| 复制 | `robocopy /E /COPY:DAT /DCOPY:DAT /R:1 /W:1 /MT:8`，**从 cmd 启动**，输出走 `Start-Process -RedirectStandardOutput <绝对路径>`（无任何 shell 重定向） | 8 段 robocopy 全部 exit 1（= 有文件被复制，成功），≥8 才 `throw` |
| 目标结构 | 顶层 23 个 `.md` → `recovery\reports\`；其余顶层目录**原样保留**（`logs\ work\ staging\ transcripts\ rebuild\ backup\ scripts\ tmp\`） | 与任务书要求一致 |
| 校验 | 两侧都用 `Directory::EnumerateFiles` + `\\?\` 长路径前缀 + .NET 直读（`Get-ChildItem` 会**静默漏掉** >260 字符的路径），逐文件 SHA-256 | 见下 |
| 删源 | 校验**全过之后**才删；白名单前缀 `C:\...\mcp-recovery`、先打印清单（22 项 / 20,254 B）、无通配符、`-LiteralPath`、`-Recurse -Force` 前先断言目标绝对等于白名单 | 源已清空 |

```
### VERIFY recovery migration
src=C:\Users\wyl\AppData\Local\Temp\mcp-recovery
dst=F:\moonbit-hof-rs\godot-mcp\recovery
src_files=33433 expected_dst_files=33433 dst_files=33433
compared=33433 mismatched=0 size_mismatch=0 missing_in_dst=0 extra_in_dst=0
src_total_bytes=2520301348 dst_matched_total_bytes=2520301348
VERIFY_RECOVERY=PASS
```

（`work\task092\logs\verify.txt` + `inventory.txt` + 8 份 robocopy 日志；`copy_recovery.ps1` /
`verify_recovery.ps1` 也留在 `work\task092\`。）

### A2 入库分界线（`.gitignore` 的 TASK-092 段，README §8 是同一份清单）

盘上总量 **33,456 文件 / 2,520,551,255 B（2,404 MB）**；其中

* **入库**：迁移那一刻测得 **2,436 文件 / 79,318,459 B（75.6 MB）**；收尾时（含 TASK-092 自己的
  迁移脚本、校验输出、构建/门/版本日志与 before 基线）**2,456 文件 / ≈75.9 MB**。
  内容是 `reports\`（RECOVERY-PLAN、STATE-OF-RECOVERY、TASK-078..092 报告、EXTRACTION/REBUILD
  manifest）、`scripts\`、`rebuild\` 的补丁与清单（`patches\ work2b\ _low-confidence\ _refs\`）、
  `work\task*` 的脚本与实测产物（trace / ledger / PNG / 分析输出）。
  **单个最大**的入库文件是 `rebuild\work2b\gen-hits.txt`（21.06 MB 文本，契约重建生成器的命中
  清单，REBUILD-2B manifest 的原始证据）—— 它是文本证据不是原始料，所以留下；若日后要瘦身，
  这是第一个候选（本报告点名它，而不是让它在数字里隐形成分）。
* **忽略 ≈31,020 文件 / ≈2.33 GB**（26 个忽略入口）：`transcripts\`（566 MB）、`staging\`（344 MB）、
  `logs\`（2.4 MB 原始流）、`tmp\`、`backup\`（193 MB 引擎二进制备份）、
  `rebuild\godot\`（**重建期的引擎树旧副本**，19,238 文件 / 1.18 GB —— 与铁律 4 同性质）、
  `work\events-*.jsonl`（106 MB，transcripts 的加工中间物）、工作区里的 `.godot/bin/obj/__pycache__/*.dll`。

**两个必须说明的例外**（都是 git 的硬约束，不是偷懒）：

1. `work\gitapply-probe\`、`rebuild\_excluded\`、`staging\modules\mcp_server\` 里各有一个**嵌套 `.git`**；
   git **拒绝进入**含 `.git` 的目录（`error: ... does not have a commit checked out`），
   单独忽略 `**/.git/` 无效。前者是 5 个 `git apply` 演练用的**引擎源文件**（585 KB，派生自引擎树），
   后者只有一个 `.git` 目录 —— 两个目录整体忽略。
2. 后者里那份**重建时被排除的 T026 提交信息**已原样复制到
   `rebuild\_excluded-T026COMMITMSG.kept.txt`（sha256 `2D7C8613…` 两侧相同）后入库，
   所以内容没有丢，只是不能放在嵌套 `.git` 里面。

**忽略 ≠ 丢失**：文件在盘上原样保留（迁移后仍是完整的一份），只是不进 git 历史。

---

## B. 三条溯源缺口的收口

### B1 `args_truncated` → sidecar + 台账重算（`args_complete`）

**改了什么**：`mcp_trace.cpp` 的 `Recorder` 新增 `_sidecar_dir()` / `_write_sidecar()` /
`_emit_sidecar()`。**三个有界载荷同一套机制**（`args` / `result_json` / `error_data_json`）：

| 情形 | 行上 | 文件 |
|---|---|---|
| 未超限 | 完整载荷，`*_truncated:false` | 无（不产生任何 I/O） |
| 超限 | 仍是裁断前缀 + 真实字节数，另加 `*_sidecar = {path, relative_path, bytes, sha256}` | `<trace 名>.sidecar/<行号>-<种类>.json`，内容是**整份**规范化载荷 |
| 写不出来 | `*_sidecar_error: "<原因>"` | 无 |

写文件用的是和 trace 本身同一套「绕过引擎 safe-save」的处理（否则编辑器进程里 sidecar 在进程结束前
根本不存在）；`bytes` 是**把文件读回来量出来的**、`sha256` 是 `FileAccess::get_sha256()`
（与 `file_effects` 同一个函数，同为小写十六进制）；写失败**绝不打断它描述的那次调用**。
sidecar 在调用行**之前**写，所以读到行的观察者一定能打开它指的文件。

**台账怎么判**（`mcp_trace_ledger.py` 的 `sidecar_of()`）：**自己打开文件、重算 sha256、重量大小**，
只有三者全对才是 `sidecar_verified`；否则是 `sidecar_missing` / `sidecar_mismatch`（并给出实际值）/
`truncated_no_sidecar` / `sidecar_not_recorded_in_trace`（旧 trace）。`facts.args` 由
`args_complete` 决定，**不再**照抄行上的 `args_truncated`。文档：MCP-TRACEABILITY.md §2.6 / §3.1。

**实测（Pong 本次会话，编辑器 trace `seq=4 project_edit_script`，args 9464 B）**：

```
行：  args_truncated=true, args_bytes=9464, inline args=4096 B
      args_sidecar={"path":"F:\\...\\pong-task092/trace-editor.sidecar/0004-args.json",
                    "relative_path":"trace-editor.sidecar/0004-args.json",
                    "bytes":9464,"sha256":"168da6eea2c21e28b33288c82406deae784cbcd3c236cf7acfdd098fd9f4b3ce"}
工具外复算（独立于台账）：文件 sha256 = 168DA6EE...（同一值，仅大小写）
                        文件 9464 B == 行上的 9464 B == 真实 args_bytes
                        文件尾 = 被 inline 裁掉的那半段 C#（"...\"path\":\"res://src/PongGame.cs\"}"）
台账：  args_evidence=sidecar_verified   args_complete=True
```

同一次会话里 `seq=6` 的 **`result_json` 也超限**（5232 B），拿到 `result_json_sidecar`
—— 说明机制不只为参数工作。本次 Pong 会话共产生 2 个 sidecar（`0004-args.json`、`0006-result.json`）。

### B2 延迟调用的文件侧与画面侧证据

**文件侧**：记录器（TASK-089 的 `MutationScope`）开在**任务真正运行的那一处** ——
`MCPDeferred::Queue::tick()` 在 `entry.task->tick()` 前后各开/收一次，把每一帧的行**跨整个延迟窗口
累计**到 pending 条目上，完成时随 `Completion` 交回运输层写进调用行（`_tick_pending`）。
状态取值：至少观测到一帧且真有落盘 → `observed_changed/mixed`；观测到但没落盘 → **`no_mutation`（是事实）**；
**一帧都没观测到**（deadline 先到）→ `not_tracked_deferred`（命名的边界）；trace 关 → 空串（与立即调用一致）。

**画面侧**：延迟调用的 `before` 帧在**请求被读到的帧**取（`Engine::arm()`，与立即调用同一处），
`finish()` 从「应答时」移到「完成时」（新增 `MCPHttpRequestSink::finish_deferred_capture()`，
由运输层在写出调用行之前调用，`seq` 用完成时才知道的那个行号），`after` 帧在完成帧之后
至少一个渲染帧取 —— 编码、PNG、像素比对、capture 行全部复用立即调用的同一套代码。
连接在完成前断开时由新增的 `Engine::discard()` 显式释放槽位（不留内存、不写行）。

**实测（Pong 本次会话，游戏 trace）**：

```
调用行（延迟）：capture.status="pending"（TASK-090 之前这里是 "unavailable"）
                file_effect_status= observed_changed（4 条场景）/ no_mutation（压力、逐帧采样）

seq=6  run_test_scenario          status=done frames_waited=51 changed=True  px=512
seq=11 run_test_scenario          status=done frames_waited=20 changed=True  px=3200
seq=12 run_test_scenario          status=done frames_waited=15 changed=False px=0
seq=13 run_test_scenario          status=done frames_waited=21 changed=True  px=3200
seq=28 run_stress_test            status=done frames_waited=6  changed=True  px=3200
seq=29 get_node_property_samples  status=done frames_waited=31 changed=False px=0
```

`frames_waited` 6–51（远大于 1）本身就是「after 帧确实在完成之后」的证据；`changed=False / px=0`
的两条是**诚实地报没动**（球已停、采样只读）。

### B3 两个缺失的 doctest（+3 条）

| 新用例 | 钉住什么 | 怎么做到 |
|---|---|---|
| `a scenario input step answers in_input_map for a declared and for an undeclared action` | 动作**已声明** → `in_input_map:true` 且状态真的动；**未声明** → `false`，而 `injected:1` 仍为真（投递与激活是两件事）；并与 `InputMap::has_action` 逐条一致 | TASK-090 声明过「测不了」：工具在无 `SceneTree` 的进程里 `-32000`。本次把**内核**导出为 `MCPTools::create_test_scenario_task(args, now_ms, require_scene_tree, err)`（`SceneTree` 检查留在工具侧、**位置不变**：先校验参数再判环境），doctest 用 `require_scene_tree=false` 驱动 |
| `a deferred completion carries its own body and its file effects on the trace line` | `_tick_pending` 写出的**调用行**带 `result_json`（工具自己的 body）与延迟窗口的真实 `file_effect_status` | 造一个 `MCPHttpRequestSink` + 真实 `MCPHttpServer`，**开环回 socket**（端口 12741）走一遍真实的 HTTP/JSON-RPC/pending 推进（与 `tests/core/io/test_tcp_server.cpp` 同一套等待惯用法），再读 trace 文件断言行 |
| `an over-bound argument list is written whole to a sidecar the line names` | 未超限 → 无 sidecar；超限 → 行上名字、文件里是**整份**载荷、`sha256` 与文件一致 | 把 `max_args_bytes` 调小、发两条真实 `project_write_text_file` 调用，读回 sidecar 文件自算 hash |
| `a deferred call's file effects are observed across its window and its boundaries are named` | `observed_changed` / `no_mutation` / `not_tracked_deferred` / trace 关 四种状态 | 在 `MCPDeferred::Queue` 的接缝上用手工帧钟驱动（不依赖墙钟），任务用本文件内的探针类 |
| `the frame-cost estimate is a clamped median of a window, not a moment reading` | 离群值不动中位数、真的慢会动、截断到 16、上下限、0/超长间隔不算样本 | 直接喂 `MCPFrameClock::note_frame(usec)` |

用例数 150 → **155**（模块），断言 6,510 → **6,613**；全量 1,576 → **1,581**，断言 430,823 → **430,926**。

### B4 帧代价的稳定估计

新增 `modules/mcp_server/mcp_frame_clock.{h,cpp}`：`MCPServer::pump_frame()` 每帧一次
`OS::get_ticks_usec()`（无分配、无锁、无 I/O），差值即「一帧的代价」；丢弃 0 µs 与 >2000 ms 的样本；
**最近 15 帧的中位数**，**截断**到整毫秒，夹在 **[16, 1000] ms**；无样本 → 16 ms。

**为什么不再退回 `Engine::get_frames_per_second()`**（这是实现期发现的一个真缺陷）：
`Engine::_fps` 的默认值是 **1**（`core/config/engine.h:67`），无样本时它会给出
`1000/1 = 1000 ms/帧` —— 一个由占位值造出来的 60 倍放大 deadline。任何能算出 deadline 的进程
都已经 pump 过帧（采样在请求被服务之前），所以这个分支只有 doctest 与单帧进程会走到，
两者要的正是旧常量 16。取值规则表写进 MCP-TRACEABILITY.md **§6**（含读数侧含义：
两条相同场景的 `timeout_ms` 不同只说明取值时刻不同）。

替换掉的是 TASK-090 的**一秒一次更新的一秒读数**：一次卡顿会被之后整整一秒的 deadline 继承
（实测同一场景两个实例 `4396` / `1150`）。中位数让单个离群值不再移动答案。

### B5 重建两个变体（真实输出）

```
START mono  00:07:43  END mono  exit=0 00:09:36
START nomon 00:09:36  END nomon exit=0 00:11:30
```

| 变体 | 可执行文件 | 字节 | sha256 | `--version` 自报 |
|---|---|---|---|---|
| mono | `bin\godot.windows.editor.x86_64.mono.exe` | 194,109,952 | `7301EDF8F0727CBD3BB61FFCCE9AAC7A8EB76DD65238D5ED41C0F2ACB5595000` | `4.8.dev.mono.custom_build.cf554ef58` |
| 非 mono | `bin\godot.windows.editor.x86_64.exe` | 193,525,248 | `6332D486B410463627739C667CD307D81B38793E99CDFDEA5EB626E9798658A2` | `4.8.dev.custom_build.cf554ef58` |

**构建脚本本身踩到一个坑并修掉（如实记录）**：`Start-Process -Wait` 在 scons 已经打印
`done building targets`、所有编译器进程都已退出之后**永远不返回**（它的行为是等所有共享重定向
句柄的进程）；第一版脚本因此挂住。改为轮询直接子进程 `HasExited`，退出码从日志尾部的
`TASK092_BUILD_EXIT=!ERRORLEVEL!` 标记读（`-PassThru` 的 `ExitCode` 对一个真失败的构建返回过空值）。
两个构建脚本与全部日志留在 `recovery\work\task092\`。

### B6 九道门 + accept_m1（`runs\gates\task092\`，全部真实输出）

| # | gate | 结论（exit 0） |
|---|---|---|
| 1 | 模块 doctest `--test-case=[MCPServer]*` | `155/155 passed`、`6613/6613 assertions`、`SUCCESS!` |
| 2 | 全量 doctest `--headless --test` | `1581/1581 passed / 3 skipped`、`430926/430926 assertions`、`SUCCESS!` |
| 3 | 组清单 | `TOOL-GROUPS CHECK PASS` |
| 4 | 契约子集（活链） | `3/3 checks passed` |
| 5 | 改名映射 | `RESULT: PASS (all checks green)` |
| 6 | 同义反复 | `TAUTOLOGY CHECK PASS`（scanned=2 file kind(s) under 2 root(s)） |
| 7 | 退出码传播 | `PROBES: 10/10` |
| 8 | 硬编码计数 | `RESULT: PASS … none is UNCLASSIFIED`（BUCKET UNCLASSIFIED=0, total=116） |
| 9 | 引擎锚点 | `ANCHOR_JUDGE VERDICT=ANCHOR_EQUAL`；`anchor=cf554ef58 head=cf554ef58 diff_count=0 red_count=0`；`ANCHOR_JUDGE RESULT PASS`（**报告落地后重跑一次仍为 `ANCHOR_EQUAL`**，见 §D3） |
| +10 | `accept_m1.ps1` | **`22/22 cases passed`** |

**顺带修掉门跑器的一个真缺陷**：`run_gates.ps1` 原来用 `%ERRORLEVEL%` 作退出码标记，
而 `%VAR%` 是在 cmd **解析整行时**展开的 —— 也就是在命令运行**之前**，所以那个标记报的是进入时的
error level，**报不出失败**。本次改为 `cmd /v:on` + `!ERRORLEVEL!`（并同样把 `-Wait` 改成轮询）。
命令集合、顺序、输出布局都没变；TASK-089..091 的**门结论本身**仍成立，因为它们引用的都是
各门输出正文里的判定行（`150/150 passed`、`RESULT: PASS`、`22/22` 等），不是那个标记。

### B7 Pong 会话重跑（同一批调用、同一开关，工程先 `reset_game.ps1` 复位）

```
reset_game.ps1 -Name pong -Confirm   →  REMOVED + RESET（133 文件 / 7.96 MB → 模板态）
run_game_session.ps1 -Game pong -RunTag pong-task092  →  编辑器 24 条请求（1 条 tools/list +
                                                        23 条 tools/call）+ 游戏 29 条 tools/call，
                                                        ledger/report 全部 exit 0
```

| | 编辑器（9888） | 游戏（9889） |
|---|---|---|
| 调用数 | 23 | 29 |
| **`facts_complete` 前（run-4，用新台账重读）** | **21/23** | **23/29** |
| **`facts_complete` 后（pong-task092）** | **23/23（100%）** | **29/29（100%）** |
| `args_evidence` 后 | `inline_complete=22, sidecar_verified=1` | `inline_complete=29` |
| 判定分布 前 | `ok_effect=3, ok_unavail=1, ok_file=9, ok_no_effect=10` | `ok_effect=6, ok_unavail=6, ok_file=9, ok_no_effect=8` |
| 判定分布 后 | `ok_effect=3, ok_file=10, ok_no_effect=10` | `ok_effect=6, ok_file=13, ok_no_effect=10` |
| `file_effects` 前 | `changed=9, none=12, not_tracked=1, unchanged=1` | `changed=9, none=13, not_tracked=6, unchanged=1` |
| `file_effects` 后 | `changed=10, none=12, unchanged=1` | `changed=13, none=15, unchanged=1` |

**前后的缺口逐条对照**（用同一份台账脚本读，所以是同类可比）：

| 端点 | seq | 工具 | 前（缺什么） | 后 |
|---|---|---|---|---|
| editor | 4 | `project_edit_script` | `args` 不可重建（`args_truncated=true`，9464 B，`sidecar_not_recorded_in_trace`） | `sidecar_verified` → `args_complete=true` |
| editor | 5 | `project_build_csharp` | `file_effect=not_tracked`（`not_tracked_deferred`） | `observed_changed`（dotnet 真的写了盘） |
| game | 6/11/12/13 | `running_game_run_test_scenario` | `file_effect=not_tracked` + 画面 `unavailable` | `observed_changed` + capture `pending`→`done`（px 512 / 3200 / 0 / 3200） |
| game | 28 | `running_game_run_stress_test` | 同上 | `no_mutation` + capture `done`（px 3200） |
| game | 29 | `running_game_get_node_property_samples` | 同上 | `no_mutation` + capture `done`（px 0） |

**`ok_effect_unavailable` 在两侧台账里都消失了**（前 1+6 条 → 后 0 条）：延迟调用从「无法观测」
变成「有文件侧与画面侧的实测证据」。**测试报告缺陷清单 0 条**（`report.json` 的 `defects` 为空，
`defects_manual` 也为空）—— TASK-091 那一批 `facts_incomplete` 低危缺陷全部消失。

**独立复算（不信任 trace 自报）**：`game_report.py` 把 capture 行指到的两份 PNG 读回来重算像素差，
**52/52 与 trace 自报逐对相等、0 处不一致**，其中 13 对非零。

---

## C. 收尾：提交、git 状态、遗留

### 引擎仓 `F:\moonbit-hof-rs\godot-mcp\godot`（每里程碑 push）

```
cf554ef58c modules/mcp_server: task092 (B2/B3/B4) step2 - a deferred call's file effects and its capture are collected at completion, the two missing doctests exist, and the frame cost is a clamped median of a window
87fbf82f4b modules/mcp_server: task092 (B1) step1 - an over-bound payload is written whole to a sidecar the line can be checked against, and the ledger re-hashes it
382549f63e modules/mcp_server: task090 (2c-9) step6 - the round-8 record: the traceability section and the gate ledger
8604fcf9e2 modules/mcp_server: task090 (2c-9) step5 - the description change is declared in the generator, so the contract stays reproducible
eee58538a1 modules/mcp_server: task090 (2c-9) step4 - a deferred call's own body reaches its trace line too
cac01b5f9f modules/mcp_server: task090 (2c-9) step3 - the round-8 fixes: the InputMap fact, the scenario flags, the frame-based deadline
a455a87bea modules/mcp_server: task090 (2c-9) step2 - D-3: the game executor reaches the running scene tree
4b8625bedc modules/mcp_server: task090 (2c-9) step1 - the failure answer's data payload reaches the call line
```

`git status --short`：**空**；`git push origin feature/mcp-server-module-rebuild` → **exit 0**，
`382549f63e..cf554ef58c`，本地与 `refs/remotes/origin/...` 同为 `cf554ef58c`。

> **为什么切成两次提交**：B1 只动 `mcp_trace.*` + 台账脚本，是一个自洽可编译的单元；
> B2/B3/B4 之间共享 `mcp_server.cpp` / `test_mcp_server.h` / 文档，按四条缺口硬切会造出
> **编译不过的中间提交**。所以按「可独立编译」的边界切，而不是按缺口的条数切。

### 主仓 `F:\moonbit-hof-rs`

`git log --oneline` 快照（**截至 `9a9b1f3`**；本报告的这一处收尾编辑是它之后的一个纯文档提交，
不会再改变下面任何一条结论）：

```
9a9b1f3 docs(godot-mcp): TASK-092 - the tracked/ignored numbers are stated for both measurement points, and the largest tracked artifact is named instead of hiding inside a total
0516f4c chore(godot-mcp): TASK-092 - the gate 9 re-run's stderr stub lands with its stdout
3e4aa99 docs(godot-mcp): TASK-092 report self-correction - gate 9 stays ANCHOR_EQUAL after the report commit (it judges the engine repo, which has not moved), and the editor phase is 24 requests of which 23 are tools/call
4e74537 docs(godot-mcp): TASK-092 B/C - the three traceability gaps are closed (args sidecar, deferred file+screen evidence, the two missing doctests, a stable frame-cost estimate), the gates and accept_m1 are green, and Pong reaches facts_complete 100%
d043fd3 chore(godot-mcp): TASK-092 A - the recovery archive moves into the project (per-file sha256 verified) and its ignore policy is split by size and reproducibility
f523904 docs(godot-mcp): 更正 Pong 缺陷记录里的一个数字 —— run-4 里「注定失败的断言」是 2 条不是 3 条
9f87061 docs(decisions): D139 TASK-091 D 段交付 —— 脚手架 + 试测驱动 + Pong + 6 条缺陷的重跑对比
df02ccb feat(godot-mcp): 可复用 C# 游戏模板 + 统一试测驱动 + 第 1 个游戏 Pong
```

三个逻辑步骤对应 **`d043fd3`（A）** 与 **`4e74537`（B+C）**；其余三条是**自我更正与数字澄清**
（门 9 判的是引擎仓、编辑器相是 24 条请求、两个测点的入库数字与最大单个文件），
按本项目的既有做法**另开提交而不是重写历史**。

`git status --short`：**空**（收尾核验）。本次主仓改动：`recovery\`（迁移 + task092 证据）、
`.gitignore`、`README.md`（§8 + §4.3）、`tools\run_gates.ps1`（退出码标记 + 轮询）、
`tools\game_report.py`（`args_evidence` 进报告）、`DECISIONS.md`（D140/D141）、
`projects\pong\scenes\main.tscn`（会话重放后的 engine `unique_id` 变化，语义相同）。

> `projects\pong\README.md` 被 `reset_game.ps1` 用模板文本覆盖过一次；它是**手写文档**
> （玩法、键位、Ball/Paddle 清单）而不是会话产物，所以已 `git checkout` 还原，没有把丢文档
> 当成「重置的副作用」提交。

---

## D. 遗留与如实声明

1. **Pong 仍然只有一局、一次会话**（本次是第 5 次运行：run-1..4 + task092）。D138 的
   「≥20 个游戏」还没开始推进。
2. **`user://` 跨轮留存**：同名截图会被下一轮覆盖，报告里的 sha/像素差都是**当轮文件**的复算值。
   本次 `changed=10/13`、`unchanged=1` 里的那条 `unchanged` 就是这种跨轮同字节。
3. **门 9 的锚点是 `ANCHOR_EQUAL`（diff_count=0），并且本报告提交之后仍然是**：
   它判的是**引擎仓**的 HEAD，而引擎仓自构建以来没有新提交（本报告与 D141 都在主仓里）。
   已实测复跑一次：`ANCHOR_JUDGE VERDICT=ANCHOR_EQUAL … RESULT PASS`
   （`work\task092\logs\gate9-after-report.log`）。**没有为此再重建**，因为不需要重建。
4. **延迟调用的画面侧代价**：每个在飞的延迟调用多持有一帧 framebuffer 拷贝，数量上界 = pending 表
   上界；连接断开由 `Engine::discard()` 释放。这是**声明的代价**，不是泄漏。
5. **仍然是纯截断的只有 `error_message`（512 B）**：它是给人看的一句话，机器可读的那一半在
   `error_data_json` 里从不丢；本次没有给它加 sidecar，属于刻意。
6. **`work\gitapply-probe\` / `rebuild\_excluded\` 整体未入库**（嵌套 `.git` 导致 git 拒收），
   内容仍在盘上；T026 提交信息另存了一份入库（见 A2）。
7. **旧 trace 的读法没变**：`sidecar_not_recorded_in_trace` / `file_effect_evidence=not_recorded_in_trace`
   只对**旧版本写出的** trace 成立 —— 本次「前」的基线就是用同一个新台账脚本读 run-4 得到的，
   两边的数字因此可比。
8. 本节所有数字都取自本任务的实际产物（`recovery\work\task092\`、`runs\gates\task092\`、
   `runs\pong\pong-task092\`、两份 `git log`/`git status`），没有凭印象编排；
   所有门与 accept_m1 都是**真实退出码**（`g01..g10 exit=0`）。
