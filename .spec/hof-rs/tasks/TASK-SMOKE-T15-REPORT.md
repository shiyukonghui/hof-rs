# TASK-SMOKE-T15-REPORT — **稳定性轮**：在含 DR-81 的修订上再跑一次同一命令序列；**产品自己的启动门转绿（`launchable=true`、`reasons=[]`、退出码 0、电池 12/12）**，我**独立复现了脱敏修复的真机效果**（每族 `raw=0`），但 **E3 not met**（跳跃类是单调自由落体，不是上抛弧线），故**六条判据并未全 met**

- 任务书：**`.spec/hof-rs/tasks/TASK-SMOKE-T12.md` 与 `TASK-SMOKE-T13.md` 全部条款继续有效**，外加调度者派发本轮时给出的 **5 条增量**（重建优先、脱敏真机复检、门必须转绿、不使用 `fresh-t14` 作基线、报告纪律）；**仓库里没有 `TASK-SMOKE-T15.md`**（本轮未新写任务书），本报告按前两本书的申报节 + 那 5 条增量撰写，并如实登记这一事实
- 报告人：**真机轮执行子代理（无上游对话上下文）**；落点：`F:\moonbit-hof-rs`
- **本轮新工程目录**：`F:\moonbit-hof-rs\.workspace\fresh-t15`（开工时**不存在**，见 §1.5）
- 轮记录：`runs/smoke-t15/**`；仓外暂存：`F:\moonbit-hof-rs-t15-staging/**`
- 本轮命令（**恰好一轮**；无被拒的启动）：
  - `F:\moonbit-hof-rs\target\release\hoh.exe init --project F:\moonbit-hof-rs\.workspace\fresh-t15`
  - `F:\moonbit-hof-rs\target\release\hoh.exe run --iterations 1 --run-id smoke-t15 --fresh-workspace --project F:\moonbit-hof-rs\.workspace\fresh-t15`
- 墙钟：`13:52:16 → 14:30:51` = **2314.110 s（38m34s）**；**`ROUND_EXIT=0`**；`meta.json.exit_code=0`
- 引擎（判据）：`4.8.dev.mono.custom_build.035edfce7`（`--version` 逐字）；二进制 sha256 `08483088…e9e6a`（与 T11–T14 记录逐字相同，仅记录）；**本轮编辑器 pid 30348**
- 二进制（**本轮按 HEAD 重建**）：`12746752 B / mtime 1790920275 / sha256 3bc1657b144e9c2ddd7262296428762814875d1d535692ae9f8da8b010d43f0b`（旧值 `12727808 / mtime 1790905290 / 3b97e4a0…`，早于 DR-81 的 `cb507e8`(13:20) ⇒ 陈旧，必须重建，见 §1.1）
- HEAD（开工 = 收工 = 报告前）= `c4a30fae620b65db4035368b20cb12853ff918d0`；开工时 `origin/master` 同值；**未 push**
- 总 tokens（`result.json.usage` 三角色之和 = 控制台 `total tokens`）= **20,641,602**

---

## 0. 结论摘要

| 判据 | 判定 | 一句话依据（本轮原始证据） |
|---|---|---|
| **E1** | **met** | 目录**可证为空**（0 条目 / 0 递归条目）→ `init` exit 0 → **恰好一轮** `run`；`start_state.mode="fresh"`；`A_0=3ac25f6c…`（3 文件/1727 B）→ `A_1=cde233b9…`（13 文件/11095 B；10 新增 + `main.tscn` 修改 + 0 删除）；Planner `D_1` 三节齐备、QA `E_1` 合法。§2.1 |
| **E2** | **met（本轮头条）** | **产品自己的门说 yes**：`artifact_gate={"applicable":true,"launchable":true,"reasons":[]}`，退出码 **0**；电池**唯一一次 pass 12/12 全 ok**，含 `editor_errors_baseline`（`count=0`）、`play_scene_ready`（`playing=true`，`:57609` pid 20720，`running_game_get_scene_tree` 28 节点）、`engine_identity`。§2.2 |
| **E3** | **not met** | 四类里**三类成立**：左移 Δ**−216.33813476563**（60/60 唯一 x）、右移 Δ**+216.33813476562**（60/60 唯一 x）、**`Coins: 0 → 1`**（引擎断言 `text:neq passed=true`）、**`Goal.reached false → true`**（`reached:neq passed=true`）。**跳跃类不成立**：被跳跃记录驱动的窗口（`raw/input_replay.json` call 31，30 采样）x 恒定（`unique=1`），**y 从 1492.81433105469 单调升到 2552.92553710938，最小值在 index 0，rise=0.0** ⇒ 是**自由落体**，不是上抛弧线；引擎的 `position:neq` 之所以 `passed=true`，只因"位置变了"。QA 自己把同一读数记为 gap `F2`。§2.3 |
| **E4** | **met** | `evidence.json`：**8 verified / 14 gap**，`overlap=[]`；**30** 条执行记录（verified 身上 **19** / gap 身上 **11**，两个作用域分开写）逐条 stat 存在（`MISSING=[]`），`candidate_id` 单一（`cde233b9…`）；14 条 gap 各带 `player_impact`/`recommended_update`；`planner_handoff` 3/6/3。§2.4 |
| **E5** | **met** | 三棵树**逐字节同一**：`versions/cde233b9…` == `iter-1/candidate` == 活体 `.workspace/fresh-t15`（13 文件/11095 B；`only_in_*=[]`、`differing=[]`、`ALL_IDENTICAL=True`）。§2.5 |
| **E6** | **met** | `qa_report.md` 逐字 `qa_status = partial`，逐条列出未做到的东西（F2/F1R/F4/F6/F7/F8/F9/F11/F12/F14/F15/F17/F10D/N3），把 `input_axis` 断言明确登记为 harness 自身设计（DR-58）而**不当作判据**，**没有**把未达成写成 verified。§2.6 |

**本轮不可判定的判据：无。**

### 0.1 本轮真正的两件头条

**(a) 上一轮失败的那道门，这一轮在真机上转绿了。** 判据与原始件：`artifact_gate.launchable=true`、`reasons=[]`、`exit_code=0`（四处同数）、电池 pass **12/12**。这不是"报告解释"，是产品自己的操作定义。原因有二，两者都被本轮原始件支持：① 本轮编辑器**在 `--fresh-workspace` 清空工作区后真的重建了 `.godot/**`**（11 个文件，mtime `14:05–14:30`，含 `filesystem_cache10` 911 B，均在 13:52:17 的清空之后），所以那条缓存写失败**根本没出现**（锚 `anchor_line_count=0`、判定 `count=0`）；② 即使出现，DR-81 ① 的具名豁免也已把它与工程缺陷分开（本轮**未触发**该分支，见 §4.3 的反例检验）。

**(b) 六条判据并没有全 met：失败的是 E3 的跳跃类，而且原因是产品侧的。** 本轮的产出关卡**没有地板**覆盖跳跃窗口所在的区域：交互窗口结束时玩家仍在 `y=263.925` 的干地上（x 走到 3257），随后 `input_replay` 的 move_right 窗口里玩家**跑出地面右缘并开始下坠**（y 263.9 → 929.3，x 3411→3627），此后每一个窗口玩家都在自由落体中，**跳跃窗口本质上是在半空中按跳跃键**。所以 `jump:replay_assert_moved` 的 `passed=true` **不能**被读成"跳起来了"——这正是两本书反复要求的"送达了输入 ≠ 真的动了"的实例，只不过这次"动了"的是重力。

---

## 1. 环境引导（**从第一秒写入文件**）

原始件：`runs/smoke-t15/evidence/round/**`、`evidence/gatecheck/**`。

### 1.1 二进制重建（任务书增量 1）

```text
$ cargo build --release --offline        (stderr) Compiling hof-rs v0.1.0 (F:\moonbit-hof-rs)
                                          Finished `release` profile [optimized] target(s) in 16.96s
BUILD_EXIT=0                             ELAPSED 17.090 s
pre-rebuild  size=12727808 mtime_unix=1790905290 sha256=3b97e4a02436bac781a41e3675ac7c4cb341c44d1682c297c3911d5d0cb80ba3
post-rebuild size=12746752 mtime_unix=1790920275 sha256=3bc1657b144e9c2ddd7262296428762814875d1d535692ae9f8da8b010d43f0b
```

**为什么必须重建**：开工时二进制 mtime `1790905290`（09:41:30），而 DR-81 的实现提交 `cb507e8` 在 **13:20:19** 改了 `src/adapter/godot.rs`、`src/runtime/secrets.rs`、`src/runtime/hygiene.rs` 与 `tests/**` ⇒ 旧二进制**不含**门的基础设施/时间窗判定与脱敏重叠修复，**陈旧二进制会使整轮作废**。本轮**没有**为了让日志出现 `Compiling` 行而 touch 任何文件：源文件在 `cb507e8` 之后本来就比二进制新。

标记核对（`evidence/round/binary_markers.txt`，逐字；直接扫二进制字节，不用 `strings`）：

```text
res://.godot/                                occurrences=3
cannot create file                           occurrences=1
check user write permissions                 occurrences=1
editor_infrastructure_failures               occurrences=3
project_defects_new                          occurrences=3
editor_error_window                          occurrences=1
window anchored with max_lines               occurrences=1
DSH_TERM_CMD                                 occurrences=1
HOH_GAME_ROUTE                               occurrences=5
STALE_ACTION_NOT_RELEASED                    occurrences=1
```

### 1.2 收紧点 1：**启动之前**的 `hoh doctor` 与端口/进程（并且发现一个占端口的遗留编辑器）

**(a) 开工读数（13:50:18，**我启动任何引擎之前**）** — `evidence/round/preflight_facts.txt`

```text
HEAD                        c4a30fae620b65db4035368b20cb12853ff918d0
ORIGIN_MASTER               c4a30fae620b65db4035368b20cb12853ff918d0
GIT_STATUS                  M src/adapter/godot.rs   ?? l.json ?? p2.json ?? pv.json ?? r.json
NETSTAT :9877               TCP 127.0.0.1:9877 LISTENING 26716      ← 不是我的进程
TASKLIST godot              godot.windows.editor.x86_64.mono.exe 26716
FROZEN_PRD_SHA              4c81c3a9995f0b3afdf01421a0c3be88573cceefc284ce9bafbfda141f0f5c3a
DECISIONS_SHA               245befb7af292c379c161ddc917e996a54a4dceea5e93c5d0226816efbae4a76
REQUIREMENTS_SHA            298a948929a434a91b9088f4d566b7e387d0cfeb270f86a79d88b006821e0e54
ENGINE_BIN_SHA              08483088a4a2772841cd3b4c916b2d45b3cb6255656cf3951598a86fce7e9e6a
```

**(b) `hoh doctor`（13:50:36，**我启动任何引擎之前**）** — `evidence/round/preflight_doctor.txt`，`EXIT_CODE: 4`

```text
[ok] spec / model.identity / model.resident / godot.project_file / godot.bundled_addon
[FAIL] model.chat: … no api key resolved; set HOH_MODEL_API_KEY or OPENAI_API_KEY (C11)
[ok] godot.engine_version: 4.8.dev.mono.custom_build.035edfce7
[ok] tools.mcp: 154 tools available at http://127.0.0.1:9877/mcp          ← 是由 26716 应答的
```

`model.chat` 的 FAIL 是**当时预期**：密钥只经 `config/model.secret.env` 注入子进程环境（`run_stream.py --env-from-secret`），doctor 自身不读该文件（C11）。直接探针 `…mono.exe --version` ⇒ `4.8.dev.mono.custom_build.035edfce7`，exit 0（`evidence/round/preflight_doctor.txt`）。

### 1.3 占端口的**遗留编辑器**：识别、判定与处置（诚实披露）

```text
ProcessId       : 26716        ParentProcessId : 36808        CreationDate : 2026/10/2 13:00:30
CommandLine     : F:\moonbit-hof-rs\godot-mcp\godot\bin\godot.windows.editor.x86_64.mono.exe --path F:/moonbit-hof-rs/.workspace/fresh-t14 -e res://scenes/main.tscn
```

- 它是**孤儿**：父进程 `36808`（`smoke-t14` 的编辑器）已不存在；它的 `--path` 是 `.workspace/fresh-t14`（`DECISIONS.md` **D294** 与 DR-81 验收记录的那个"未署名引擎进程"）。
- **它挡住的正是任务书的硬顺序**：Godot 在启动时固定编辑器工程、177 个工具无一能切换 ⇒ 只要 9877 被一个指向 `fresh-t14` 的编辑器占着，本轮**不可能**让编辑器指向 `fresh-t15`；继续跑就会变成"**MCP 观测 fresh-t14、磁盘写 fresh-t15**"的假轮。
- **处置（记录逐字）**：`taskkill /PID 26716 /T /F` ⇒ `exit 0`，`SUCCESS: The process with PID 26716 (child process of PID 36808) has been terminated.`；随后 `netstat :9877` 无 LISTENING、`tasklist` 无 godot 进程。
- 这不是"静默降级"：我**先**留了原始身份与端口证据（`preflight_facts.txt`），**再**停它，**再**记它已停，**然后**才起本轮自己的编辑器。`.workspace/fresh-t14` 按任务书增量 4 **不是基线**，故停它不触碰任何只读基线。

### 1.4 引擎启动捕获（**控制台句柄在 spawn 之前打开**）

`evidence/scripts/launch_engine.py` 在 `Popen` **之前**就以二进制追加方式打开控制台文件并把 stdout+stderr 都接上去，所以第一秒输出在文件里。

| 启动 | 命令（逐字） | pid | 控制台文件 | 就绪行 |
|---|---|---|---|---|
| ① 本轮编辑器（**init 之后**） | `…mono.exe -e --path F:\moonbit-hof-rs\.workspace\fresh-t15 --mcp-port=9877` | 30348 | `evidence/round/editor_console.txt` | `role=editor`，`tools=154`，2.06 s |
| ② 角色门复现（**空目录**，收工后，端口 9879） | `…mono.exe -e --path F:\moonbit-hof-rs-t15-staging\empty-probe-dir --mcp-port=9879` | 26032 | `evidence/gatecheck/gate_game_role_console.txt` | `role=game`，`tools=73` |

启动 ① 的完整控制台逐字（`evidence/round/editor_console.txt`）：

```text
==== CONSOLE OPENED BEFORE SPAWN (t=1790920309.749) ====
Godot Engine v4.8.dev.mono.custom_build.035edfce7 (2026-09-29 00:01:57 UTC) - https://godotengine.org
OpenGL API 3.3.0 NVIDIA 616.56 - Compatibility - Using Device: NVIDIA - NVIDIA GeForce RTX 4090
[MCP] role=editor configured_port=9877 source=cmdline listen=true
[MCP] listening on 127.0.0.1:9877 (editor=true, tools=154)
[MCP] INFO: MCP server is ready on 127.0.0.1:9877 as the editor process (port source=cmdline, tools=154)
```

进程身份与工程绑定（**反假轮**）— `evidence/round/editor_listener.txt`、`evidence/round/scope_project_list_scripts.json`、`evidence/round/editor_tools_list.json`：

```text
ProcessId      : 30348
CommandLine    : F:\moonbit-hof-rs\godot-mcp\godot\bin\godot.windows.editor.x86_64.mono.exe -e --path F:\moonbit-hof-rs\.workspace\fresh-t15 --mcp-port=9877
ExecutablePath : F:\moonbit-hof-rs\godot-mcp\godot\bin\godot.windows.editor.x86_64.mono.exe
CreationDate   : 2026/10/2 13:51:49
netstat        : TCP 127.0.0.1:9877 LISTENING 30348
$ project_list_scripts -> {"count":0,"scripts":[]}      ← 本轮新工程
  磁盘对照：.workspace/mario/scripts 有 15 个条目
editor tools/list -> 154 = {editor_ 104, project_ 48, os_ 2, running_ 0}
```

⇒ MCP 侧看到的**就是**磁盘侧要写的那个工程。**运行期的 inline doctor 也逐字命中引擎串**（`evidence/round/round_console.txt`：`[ok] godot.engine_version: 4.8.dev.mono.custom_build.035edfce7`）。

### 1.5 "空目录 → init → run" 三步原始输出

**(a) 目录为空**（`evidence/round/empty_proof.txt`：先证明**不存在**，再 `mkdir`，再证明 0 条目）

```text
EXISTS_BEFORE: False        ISDIR_BEFORE: False
$ cmd /c mkdir F:\moonbit-hof-rs\.workspace\fresh-t15   exit=0
ENTRY_COUNT: 0              ENTRIES: []      RECURSIVE_ENTRY_COUNT: 0
$ cmd /c dir /a …           0 File(s)              0 bytes      2 Dir(s)
```

**(b) `hoh init`**（`evidence/round/init.txt`）：`init: A0 ready at F:\moonbit-hof-rs\.workspace\fresh-t15 (initialize ran; no MCP, no model endpoint and no key were required)` / `EXIT_CODE: 0`。
`A_0` 树（`evidence/round/init_tree.txt`）：`project.godot` / `scenes/main.tscn` / `scripts/README.md` = **3 文件 / 1727 B**，运行时 id **`3ac25f6c…`**（与 T11–T14 的 A₀ 同 id；我的独立实现复算逐字命中）。

**(c) `start_state`**：`{"mode": "fresh", "version_id": null}`（不是 `as_is`）。

**(d) `hoh run` 的启动与结束**（`evidence/round/round_console.txt`，流式写入）

```text
STARTED: 2026-10-02 13:52:16 (1790920336.985)
…（runtime doctor 全 ok，含 model.chat 与 godot.engine_version 与 tools.mcp 154）
run smoke-t15 finished: 1 iteration(s), final version Some("cde233b96c5b0a7bfd22a31078897231d0595cee6dd40ab9fe9df017d8fc8c37"), total tokens Some(20641602)
prd coverage: 8/17 verified (harness/gate describe the runtime contract, not the product)
ENDED:   2026-10-02 14:30:51 (1790922651.095)
ELAPSED_SECONDS: 2314.110
ROUND_EXIT: 0
```

---

## 2. E1..E6 逐条判定 + 原始证据

### 2.1 E1 = met

| 要件 | 本轮原始证据 |
|---|---|
| Planner 产出合法 `D_1` | `iter-1/plan.md`（2159 B）含 `### Priority Order` / `### Preservation Gate` / `### Acceptance Gate`；`logs/planner.attempt1.log`：`exit_status=RepeatedFormatError`、**`artifact_valid=true`**、15 calls |
| Developer 产出**真实工程增量** | `versions/index.json`（`schema`+`versions` 两条）：`3ac25f6c…`(iter 0, role init) → `cde233b9…`(iter 1, role developer)；`result.json.evidence_diff` = 10 新增 + `scenes/main.tscn` 修改 + 0 删除 |
| QA 产出合法 `E_1` | `iter-1/evidence.json`（20546 B，可解析）；`logs/tester.attempt1.log`：`exit_status=RepeatedFormatError`、`artifact_valid=true`、141 calls |
| 整轮 | `result.json`：`ok=true, failed_role=null, reason="ok", issues=[]`；`versions/index.json` 只有 2 条（iteration 0/1）；`iter-1/` 只有一个迭代目录；`result.json.attempts` 只有 4 条（planner×1、developer×**2**、tester×1） |

**退出码（四处）**：`exit_code` 字节 `30 0A`、`process_exit_code` 字节 `30 0A`、`meta.json.exit_code=0`、wrapper `ROUND_EXIT=0` ⇒ **四处同数，值 0**。

**`A_0`/`A_1` 摘要（运行时口径；我用独立实现复算，两个 id 都逐字命中）**：

```text
A0  3ac25f6c5c38885febd3a001ea99c88aca61b1799c7b105306919886c2c1d151    3 files   1727 B
A1  cde233b96c5b0a7bfd22a31078897231d0595cee6dd40ab9fe9df017d8fc8c37   13 files  11095 B
```

**被改文件清单**：ADDED 10（`scripts/{coin,enemy,goal,main,player}.gd` + 各自 `.gd.uid`）；MODIFIED 1（`scenes/main.tscn`）；REMOVED 0。差异**全部落在 Developer 产出的工程文件**上，没有落在 `.hoh/**`、`runs/**` 等被排除路径。

**非琐碎**：Developer 从只有 `README.md` 的 `scripts/` 起手，写出 5 个脚本并把 `main.tscn` 从 342 B 扩到 5144 B（28 节点），且**有真正的修复动作**（attempt1 触发 `artifact_missing` 的 wrap-up retry，attempt2 补完）。

**机制读数（`result.json`/`warnings.log`，可复算）**：`repair_retry_used=false`、`wrap_up_retry_used=true`、`wrap_up_retry_reason="artifact_missing"`；`warnings.log` 637 B / 4 个换行结尾行，其中 `launch_gate_repair` **0** 次 ⇒ **attempt2 不是门的修复重试**（与 T14 不同）。

### 2.2 E2 = **met**（本轮头条）

**判据原文**：「产出的 Godot 工程**可启动**（无编译/脚本错误）」；证据形式：MCP `play_scene` + `get_editor_errors`。
**口径（D294 已裁定）**：E2 以产品的操作定义 `artifact_gate.launchable=true, reasons=[]` 读。

```text
artifact_gate            = {"applicable": true, "launchable": true, "reasons": []}
exit_code                = 0（exit_code / process_exit_code / meta.json / ROUND_EXIT 四处同数）
battery pass             = 1 次，12/12 ok=True
  project_reload_and_open / scene_structure / editor_errors_baseline / play_scene_ready /
  scene_tree / screenshot / interaction_evidence / input_channel_probe / input_replay /
  node_and_collision_assertions / editor_stop_scene / engine_identity   —— 全部 true
editor_errors_baseline   = {"available":true,"count":0,"errors":[],"pid":30348,"port":9877,"source":"editor_log"}  ok=True
play_scene_ready         = editor_play_scene -> {"endpoint":"http://127.0.0.1:57609/mcp","mcp_port":57609,"pid":20720,"playing":true}
                           running_game_get_scene_tree -> 28 nodes（带 path 与 type）
editor_stop_scene        = {"message":"Playback stopped","stopped":true}
```

**与上一轮的差别是可复算的**：T14 的 `editor_errors_baseline` 是 `count=1`（`res://.godot/editor/filesystem_cache10` 写失败）⇒ `launchable=false` ⇒ exit 6；本轮 `count=0` ⇒ `launchable=true` ⇒ exit 0。

### 2.3 E3 = **not met**（四类里三类成立；失败的是**跳跃**）

| 行为 | 裁定 | 决定性原始证据（**全部来自游戏进程端点**） |
|---|---|---|
| 左移 | **成立** | `input_replay` move_left：x `3679.02709960938 → 3462.68896484375`，Δ=**−216.33813476563**（60 帧，**60/60 唯一 x**）；`move_left:replay_assert_moved` `passed=true` |
| 右移 | **成立** | move_right：x `3411.3544921875 → 3627.69262695312`，Δ=**+216.33813476562**（60 帧，**60/60 唯一 x**）；`move_right:replay_assert_moved` `passed=true`；（补充窗口）move_right_release Δ**+33.00073242187**（10 帧，10/10 唯一） |
| **跳跃** | **不成立** | 被 `jump` 记录驱动的窗口（call 31，30 帧）：x **恒为** `3690.02734375`（`unique=1`）；y **单调递增** `1492.81433105469 … 2552.92553710938`，**最小值在 index 0，rise=0.0**，`y_nondecreasing=True`（`evidence/analysis/e3_jump_t15.txt`）⇒ **纯竖直自由落体，没有任何上抛**；`jump:replay_assert_moved` 的 `passed=true` 只证明"位置变了"。QA 的同一读数见 gap `F2`：「the recorded jump window starts mid-air (velocity y = +42, y rising) and never shows an upward arc or a landing/re-jump」 |
| **至少 1 个可交互对象** | **成立** | `interaction_evidence` 的 `running_game_get_node_properties`：`Coins: 0`（call 0）→ **`Coins: 1`**（call 90）；`running_game_assert_node_state`（`text:neq "Coins: 0"`，actual `"Coins: 1"`）`passed=true`；判定行 `COIN_PICKED_UP` |
| **一个终点/胜负条件** | **成立** | `Goal.reached`：`false`（call 1/10/16/22/28/34/40/46/52/58/64/70/76/82）→ **`true`**（call 88/91）；`running_game_assert_node_state`（`reached:neq false`，actual `true`）`passed=true`；判定行 `WIN_DRIVEN` |

**"金币跃迁来自语义工具原始回包"（不得推断）——逐字**：

```text
[  0] running_game_get_node_properties interaction:read_/root/Main/HUD/Coins_text
      {"node_path":"/root/Main/HUD/Coins","properties":{"text":"Coins: 0"},"type":"Label"}
[ 90] running_game_get_node_properties interaction:read_/root/Main/HUD/Coins_text
      {"node_path":"/root/Main/HUD/Coins","properties":{"text":"Coins: 1"},"type":"Label"}
[ 92] running_game_assert_node_state   interaction:replay_assert_picked_up
      {"actual":"Coins: 1","expected":"Coins: 0","operator":"neq","property":"text","passed":true,"resolved_node_path":"/root/Main/HUD/Coins"}
[ 93] running_game_assert_node_state   interaction:replay_assert_won
      {"actual":true,"expected":false,"operator":"neq","property":"reached","passed":true,"resolved_node_path":"/root/Main/Goal"}
```

（原始件 `iter-1/candidate/.hoh/deterministic/raw/interaction_evidence.json`；提取件 `evidence/analysis/e3_extract.txt`。）

**跳跃窗口的 y 序列逐字（决定性）**：

```text
window 2 (call 31, frame_count=30)  x first=3690.02734375 last=3690.02734375 unique=1
y = [1492.81433105469, 1523.92541503906, 1555.42541503906, 1587.31433105469, 1619.59216308594,
     1652.25891113281, 1685.314453125, 1718.75891113281, 1752.59228515625, 1786.81457519531,
     1821.42565917969, 1856.42565917969, 1891.81457519531, 1927.59240722656, 1963.75903320312,
     2000.31457519531, 2037.25903320312, 2074.59228515625, 2112.314453125, 2150.42553710938,
     2188.92553710938, 2227.814453125, 2267.09228515625, 2306.75903320312, 2346.81469726562,
     2387.25903320312, 2428.09228515625, 2469.314453125, 2510.92553710938, 2552.92553710938]
y first=1492.81433105469 min=1492.81433105469 (index 0) last=2552.92553710938 nondecreasing=True rise=0.0
```

**为什么是自由落体（反例检验：把"我们没看到 X"与"X 不可能"分开）**

| 检验 | 读数 | 结论 |
|---|---|---|
| 是不是"采样只覆盖了下坠的后半段"？ | 该窗口**起点已在地面高度之上**：窗口开始 `y=1492.81`，而交互窗口结束时玩家还在 `y=263.925`；且窗口内 `min == first`（index 0） | **否**；窗口内**从未上升**，上抛若发生必然出现 `min < first` |
| 是不是"玩家在空中但确实跳了"？ | 该窗口的驱动事件是 `jump`（`event_types.action=2`、`pressed=true`、`injected=1`），而 y 的增量从 ~31 逐步增大（重力加速） | **否**；输入被送达、玩家只在被重力拉下去 |
| 是不是"地面存在但玩家站在别处"？ | 同一 `input_replay` 的 move_right 窗口起点仍在 `y=263.925`（地面），60 帧内 y 升到 929.3（跑出地面右缘）；此后三个窗口 y 单调升 | **是**：地面在 `x≈3411` 之后不存在，跳跃窗口（x≈3690）**没有地板** |
| 是不是"引擎断言否证了它"？ | `position:neq` 只看"位置变了" | **否**；断言**不能**区分"起跳"与"坠落"——这是断言口径的已知上限，本轮把它写实 |

⇒ **E3 判 not met**。范围精确表述：**"左右移动 / 可交互对象 / 终点胜负"三类本轮成立；"跳跃"类本轮不成立，因为产出关卡在跳跃窗口所在区域没有地板，玩家处于自由落体，引擎的 `position:neq` 通过不能作为跳跃证据。**

**计数（作用域 = `iter-1/candidate/.hoh/deterministic/battery.json` 全部 `record.observation` 文本，5403 B）**：`POSITION_ASSERT_PASSED` **4**、`COIN_PICKED_UP` **1**、`WIN_DRIVEN` **1**、`GAME_INPUT_CHANNEL_OK` **2**、`COIN_NOT_PICKED_UP` **0**、`WIN_BLOCKED_UNDER_MOVE_RIGHT` **0**、`WIN_UNREACHED_WITHIN_BUDGET` **0**、`WIN_UNREACHABLE_GEOMETRICALLY` **0**、`STALE_ACTION_NOT_RELEASED` **0**、`COIN_COUNTER_UNREADABLE` **0**（`evidence/analysis/final_counts.txt`）。

**`interaction_evidence` 与 `input_replay` 的对照（T12 §1.4）**：`interaction_evidence` call[4] 是陈旧动作释放探针（`event_count=1, injected=1`），随后 14 批各 **60/60 唯一 x**；`input_replay` 的五个窗口里，**送达输入**（`injected=1`）与**真的发生对应动作**是两件事——跳跃窗口把这一点变成可复算的反例（`injected=1` 而 `rise=0.0`）。

### 2.4 E4 = met

```text
iteration=1  qa_status=partial  verified=8  gap=14
verified_ids = [N1,N2,F1,F3,F5,F10,F13,F16]
gap_ids      = [F2,F1R,F4,F6,F7,F8,F9,F11,F12,F14,F17,F15,F10D,N3]
overlap: []        dup ids: []
execution_records: verified 身上=19, gap 身上=11, verified+gap=30   ← 两个作用域分别写清
MISSING=[]         record types {assert:6, build:3, replay:9, runtime_trace:9, screenshot:3}
record candidate_ids = ["cde233b96c5b0a7bfd22a31078897231d0595cee6dd40ab9fe9df017d8fc8c37"]
gaps lacking player_impact: []     gaps lacking recommended_update: []
planner_handoff: preservation_constraints=3 / update_targets=6 / validation_requirements=3
```

（`evidence/analysis/round_facts.txt`。）

### 2.5 E5 = met（三棵树逐字节同一）

```text
versions/cde233b9…          13 files / 11095 bytes
iter-1/candidate            13 files / 11095 bytes
live .workspace/fresh-t15   13 files / 11095 bytes
only_in_first=[]  only_in_second=[]  differing=[]   ALL_IDENTICAL = True
（三者 runtime-scheme id 均由我的独立实现复算为 cde233b96c5b0a7bfd22a31078897231d0595cee6dd40ab9fe9df017d8fc8c37）
result.json.candidate_id == version_id == cde233b9…
```

⇒ **QA 未修改 `A_1`**。

### 2.6 E6 = met

`qa_report.md`（2807 B）逐字要点：

```text
## Verdict
`qa_status = partial`: the launchable core plus movement/ground/coin/goal/HUD work is verified,
but the majority of the game verbs (jump, enemies, blocks, fail/restart, level length, target
length) are unobservable and recorded as gaps with player impact and a smallest next step.
- **F2 jump**: the recorded jump window starts mid-air (velocity y = +42, y rising) and never
  shows an upward arc or a landing/re-jump. The core jump verb is unproven.
- … F6 wall / F7,F8,F9 enemy / F11,F12 blocks / F14,F15 fail & restart / F17 level length /
  N3 stability
No production file was modified; every probe was read-only and written under `.hoh/`.
```

⇒ 未达成被**逐条声明**并带 player impact；`input_axis` 断言被明确登记为 harness 自身设计（DR-58）而**不当作判据**；与 `evidence.json` 的 8/14 划分逐条一致，**没有**把未达成写成 verified。
**口径说明**：本轮 QA 用的是 `qa_status = partial`（T14 是 `Status: **partial**.`、T12/T13 是 `Verdict: partial`）；判据要的是诚实声明，不是那几个字母，差异在此写明以免误读。

---

## 3. 增量 2：**脱敏修复的真机复检**（不看单测断言，只看本轮自己的旁路副本）

**方法**：对 `runs/smoke-t15/iter-1/traj/` 下**全部 7 个** JSON（3 个原件 + 3 个旁路 + developer.attempt2 无旁路）**逐字节扫描**，对 `src/runtime/secrets.rs:53 SECRET_ENV_VARS` 与 `:84 HARNESS_ENV_VARS` 的**每一个名字**分别数：
`NAME=` 出现次数、`NAME=<redacted>` 次数、以及**未被替换的原文**（`raw = total − marked`）；另数 JSON 键形 `"NAME":` 的取值是否被替换。扫描器**不是正则**：环境转储在 JSON 串里以 `\n`（反斜杠+n）分隔赋值，`NAME=` 前的字符是字母 `n`，所以 `(?<![A-Za-z0-9_])` 会**拒绝每一个真实出现**（本脚本第一版正是这样，得到全 0 的假读数；错误与更正都留在 `evidence/analysis/redaction_counts_t15.txt` 的说明里与 §10.5）。

**赋值形（修复声称覆盖的形状）——本轮实测数**

| 文件（作用域=该文件全文） | `<redacted>` 标记 | 有赋值的族 | `NAME=` 出现总数 | 其中已标记 | **原文存活（raw）** |
|---|---|---|---|---|---|
| `planner.attempt1.json`（原件，76353 B） | 0 | 12 | 24 | 0 | **24** |
| `planner.attempt1.redacted.json` | **24** | 12 | 24 | **24** | **0** |
| `developer.attempt1.json`（原件，994873 B） | 0 | 11 | 22 | 0 | **22** |
| `developer.attempt1.redacted.json` | **22** | 11 | 22 | **22** | **0** |
| `developer.attempt2.json`（235198 B，无旁路） | 0 | **0** | 0 | 0 | **0** |
| `tester.attempt1.json`（原件，1080415 B） | 0 | 3 | 15 | 0 | **15** |
| `tester.attempt1.redacted.json` | **15** | 3 | 15 | **15** | **0** |

- 逐族读数（每族 `total` / `marked` / `raw`）在 `evidence/analysis/redaction_counts_t15.txt`；机器可读形式在 `redaction_counts_t15.json`。
- 覆盖到的族：`planner` 12 族 × 2 次 = 24（含 `DSH_TERM_CMD`、`HOH_ARTIFACT_DIR`、`HOH_GAME_ROUTE`、`HOH_HOH_BIN`、`HOH_ITERATION`、`HOH_MODEL_API_KEY`、`HOH_ROLE`、`HOH_RUN_DIR`、`HOH_RUN_ID`、`HOH_SCRATCH_DIR`、`HOH_TOOLS_ENDPOINT`、`HOH_VIEW_DIR`）；`developer.attempt1` 11 族 × 2 = 22（无 `DSH_TERM_CMD`，其转储以 `HOH_ARTIFACT_DIR` 起头）；`tester.attempt1` 3 族 × 5 = 15（`HOH_HOH_BIN`/`HOH_SCRATCH_DIR`/`HOH_ARTIFACT_DIR`）。
- **原件仍有原文、旁路 `raw=0`** ⇒ 这个对照是**有意义**的（不是"两边都空"）。
- `developer.attempt2.json` 的转储**没有重复出现**（0 处赋值）⇒ 对它而言该形状不存在，**不能**拿它当"修复生效"的证据。

⇒ **上一轮那个"整族在重复转储下存活"的缺陷，在本轮真机上不复现。**（这是**实测**：raw=0 在三个旁路里逐族成立。）

**密钥值本身**：`HOH_MODEL_API_KEY` 长度 **51**（来源 `config/model.secret.env`，只报长度）；对 `runs/smoke-t15/**` 与 `.workspace/fresh-t15/**` 共 **250** 个文件逐字节扫描 ⇒ **0** 个文件含该值。

**但是——同一族还有第二种形状，修复不覆盖它（本轮新发现，`F-T15-1`）**：
harness 自己的 role-config 转储把**同一批名字**写成 JSON 键值，取值**非空且未被替换**，在**原件与旁路副本里都逐字存活**：

```text
"HOH_GAME_ROUTE": "F:\\moonbit-hof-rs\\runs\\smoke-t15\\game_endpoint.json"
"HOH_HOH_BIN": "F:\\moonbit-hof-rs\\target\\release\\hoh.exe"
"HOH_ARTIFACT_DIR": "F:\\moonbit-hof-rs\\.workspace\\fresh-t15\\.hoh"
"HOH_SCRATCH_DIR": "F:\\moonbit-hof-rs\\.workspace\\fresh-t15\\.hoh\\scratch"
"HOH_RUN_DIR": "F:\\moonbit-hof-rs\\runs\\smoke-t15"
"HOH_RUN_ID": "smoke-t15"        "HOH_ROLE": "developer"      "HOH_ITERATION": "1"
"HOH_VIEW_DIR": "F:\\…\\fresh-t15"   "HOH_TOOLS_ENDPOINT": "http://127.0.0.1:9877/mcp"
（另有两个未列入 HARNESS_ENV_VARS 的名字： "HOH_TOOLS_POLICY": "developer" / "HOH_WORKSPACE": "F:\\…\\fresh-t15"）
四个凭据名（HOH_MODEL_API_KEY / OPENAI_API_KEY / LITELLM_API_KEY / MSWEA_MODEL_API_KEY）在该转储里取值均为空串
```

**计数（作用域 = `evidence/analysis/redaction_jsonkey_t15.txt`，同样的 7 个文件）**：上述 11 个已声明族**每个文件各 1 处、取值非空、`marked=0`**；`HOH_TOOLS_POLICY`/`HOH_WORKSPACE` 各 1 处。⇒ 这是**与赋值形不同的披露向量**（路径、角色、迭代号、run id、回环端点 URL；**不含任何凭据值**），**既不是**修复声称覆盖的形状，**也不是**修复造成的回归（T14 的冻结件里同形读数同样存在，见 §3.1）。

### 3.1 反例检验（把"我们没看到"与"不可能"分开）

| 检验 | 读数 | 结论 |
|---|---|---|
| 会不会是"本轮根本没有环境转储"？ | 原件里 12 族 × 2、11 族 × 2、3 族 × 5 的**赋值形出现**都在，旁路里同一位置全部变成 `<redacted>` | **否**；正是"重复转储"的形状 |
| 会不会是"放宽了脱敏器/改动被做掉"？ | 二进制里 `DSH_TERM_CMD` 1 处、`HOH_GAME_ROUTE` 5 处；`src/runtime/secrets.rs` 的区间相交+吞并代码在 `cb507e8` 内 | **否**；是修复后的二进制 |
| 会不会是"旁路副本其实是原件改名"？ | 6 个 JSON 全部 `json.loads` 通过；旁路与原件**字节不同**（994873→994449、76353→75017、1080415→1080298），且 `warnings.log` 逐条记 "frozen evidence kept in place; the redacted form was generated as …" | **否** |
| 会不会"原件的族集合与旁路不同"？ | 两侧 `NAME=` 总数**逐族相等**（名字保留，只有取值被换） | **否** |
| JSON 键形是本轮新增的回归吗？ | 对 `runs/smoke-t14`（只读）做同一扫描：`"HOH_GAME_ROUTE": "F:…"` 等键形在 T14 的旁路里**同样 raw** | **否**；**既存向量**，非本轮引入 |

（最后一条的读数：`evidence/analysis/redaction_jsonkey_t14_crosscheck.txt`。）

---

## 4. 增量 3：启动门的裁决、理由、时间窗锚与计数

### 4.1 裁决（`runs/smoke-t15/iter-1/result.json` 逐字）

```text
"artifact_gate": { "applicable": true, "launchable": true, "reasons": [] }
```

⇒ **门是绿的，`reasons` 为空**。四处退出码同为 `0`（`30 0a` / `30 0a` / `meta 0` / `ROUND_EXIT: 0`）。

### 4.2 原始文档里的窗口锚与计数（`iter-1/candidate/.hoh/deterministic/raw/editor_errors_baseline.json`）

```text
"criterion": "an editor log line closes the gate only when it is not an exact DR-48 engine banner,
              not stale by DR-68, not editor infrastructure by DR-81 ①, and its number of occurrences
              grew between the pre-reload anchor reading and the judged reading",
"anchor": "editor_get_errors max_lines=2000 taken immediately before `project_reload_and_open`;
           the judged reading is max_lines=50 taken after it",
"anchor_line_count": 0,
"anchor_request_and_answer": {"args": {"max_lines": 2000}, "ok": true,
   "payload": {"content":[{"text":"{\"available\":true,\"count\":0,…,\"errors\":[],\"pid\":30348,\"port\":9877,…}"}]},
   "request_id": 8, "response_id": 8, "tool": "editor_get_errors"},
"banners": 0, "stale": 0, "editor_infrastructure_failures": 0,
"pre_existing_lines": 0, "project_defects_new": 0
```

判定读数（同文件 `calls[0].payload`）：`{"available":true,"count":0,"errors":[],"pid":30348,"port":9877,"source":"editor_log"}`，`ok=true`。
电池只有**一次** pass（`quarantine/` **不存在**），12 步全 ok。

### 4.3 有没有"基础设施类"的行？——**没有出现**，且这必须与"不可能出现"分开

- **本轮实测**：`editor_infrastructure_failures=0`、`project_defects_new=0`、锚 0 行、判定 0 行 ⇒ **本轮没有任何行需要被分类**，因此 **DR-81 ① 的分类分支本轮未被真机触发**；它只被二进制标记（`res://.godot/` 3、`cannot create file` 1、`check user write permissions` 1、`editor_infrastructure_failures` 3、`project_defects_new` 3）与源码阅读支持。
- **"不可能出现"是错的（反例）**：同一编辑器（pid 30348、:9877）在**轮后**再读一次 `editor_get_errors` 返回的是 `count=1` 且唯一一行是 `[MCP] capture=off (default; …)`——**一条根本不是错误的横幅行**（`evidence/round/closeout_t15.txt`）。⇒ 该字段是**编辑器日志尾的读数**，其内容随日志变化（T14 的 H7 在本轮独立复现）。
- **缓存目录这一半本轮的形状（可复算）**：`.workspace/fresh-t15/.godot/editor/filesystem_cache10` **存在**，911 B；该目录下 **11** 个文件的 mtime 全在 `14:05:10–14:30:51`，**全部晚于** `--fresh-workspace` 清空工作区的 `13:52:17`（`evidence/round/godot_cache_timeline.txt`）。对照 T14：`fresh-t14` 整目录缺失（`evidence` 冻结）、`fresh-t13` 在 04:54 重建过。
- **对 DR-81 ④ 机制结论的实测小修正（诚实登记）**：DR-81 的代码级结论是"**已在运行**的编辑器不会重新导入 ⇒ 不会重建 `.godot`"。本轮**同一形状**（编辑器先指向工程、随后 `--fresh-workspace` 清空）下，**运行中的编辑器在 14:05–14:30 逐步重建了 `.godot/**`**，包括 `filesystem_cache10`。⇒ "运行中的编辑器不会重建"**不是一条普遍律**，至少在本轮不成立；差别可能是"何时有写入需求"（本轮它在电池的 `project_reload_and_open`/场景打开时才写），但**我没有插桩**⇒ 归因标为**推断/未定**。

---

## 5. 命令并排对照与逐轮对照表

### 5.1 命令逐字并排（证明"同一条命令序列"）

| 步骤 | T14（上一轮，失败在门） | T15（本轮） |
|---|---|---|
| 空目录证明 | `cmd /c mkdir F:\moonbit-hof-rs\.workspace\fresh-t14`（先证不存在、再证 0 条目） | `cmd /c mkdir F:\moonbit-hof-rs\.workspace\fresh-t15`（同法） |
| 引擎 | `F:\moonbit-hof-rs\godot-mcp\godot\bin\godot.windows.editor.x86_64.mono.exe -e --path F:\moonbit-hof-rs\.workspace\fresh-t14 --mcp-port=9877` | `… -e --path F:\moonbit-hof-rs\.workspace\fresh-t15 --mcp-port=9877` |
| init | `target/release/hoh.exe init --project F:\moonbit-hof-rs\.workspace\fresh-t14` | `target/release/hoh.exe init --project F:\moonbit-hof-rs\.workspace\fresh-t15` |
| run | `target/release/hoh.exe run --iterations 1 --run-id smoke-t14 --fresh-workspace --project F:\moonbit-hof-rs\.workspace\fresh-t14` | `target/release/hoh.exe run --iterations 1 --run-id smoke-t15 --fresh-workspace --project F:\moonbit-hof-rs\.workspace\fresh-t15` |
| 差异 | — | **只有 run id 与工程目录**（与 T12/T13/T14 一致） |

### 5.2 逐轮对照表（判定 / 关键读数）

| 读数 | T12 | T13 | T14 | **T15（本轮）** |
|---|---|---|---|---|
| `ROUND_EXIT` | 0 | 0 | **6** | **0** |
| `artifact_gate.launchable` | true | true | **false** | **true**（`reasons=[]`） |
| 电池 pass | 2 次（pass2 10/12） | — | pass1 4/12、pass2 10/12 | **1 次，12/12** |
| E1 / E2 / E3 | met / met / met | met / met / met | met / **not_met** / met | met / **met** / **not_met** |
| E4 / E5 / E6 | met / met / met | met / met / met | met / met / met | met / met / met |
| `A_0` | `3ac25f6c…` 3/1727 | 同 | 同 | **`3ac25f6c…` 3/1727** |
| `A_1` | — | `a54179ce…` 13/9610 | `3d18b24d…` 13/8254 | **`cde233b9…` 13/11095** |
| 场景节点 | — | 28 | 22 | **28** |
| 金币 | `0→2` | `0→1`（结构不可达→修好） | `0→1` | **`0→1`** |
| 左移 / 右移 Δ | — | −216.33 / +216.33 | −216.332 / +216.331 | **−216.338 / +216.338** |
| 跳跃 | — | 成立 | 成立（`min<first`） | **不成立（单调下坠）** |
| 64 KiB 截断 | 1 次 | 1 次 | 1 次（79928） | **1 次（146150）** |
| tokens | — | — | 16,346,289 | **20,641,602** |
| 墙钟 | — | 46m20s | 36m07s | **38m34s** |
| Developer attempt 次数 | — | — | 2（第 2 次是**门修复**重试） | **2（第 2 次是 `artifact_missing` wrap-up 重试；`repair_retry_used=false`）** |
| 脱敏（赋值形） | 泄漏 | 泄漏（`DSH_TERM_CMD`） | **泄漏**（整族） | **raw=0（修复生效）** |
| 只读基线 | 10 条未变 | 10 条未变 | 11 条未变 | **12 条逐字节未变** |

⇒ **"同一条命令序列"成立**；**判定类别在本轮发生了变化**，而且变化的**方向相反于上一轮**：上一轮唯一红在 **E2（门）**，本轮唯一红在 **E3（跳跃）**。

---

## 6. 角色门复现、日志读数与其它机制读数

### 6.1 角色门独立复现（T13 §1.6，**第 5 次**）

**方法**：在**可证为空**的目录上启动引擎，控制台句柄在 spawn 之前打开。**端口说明**：任务书要求收工时保持本轮编辑器存活，而它占着 9877，故空目录这一腿用 **9879**；**角色判定取自引擎自己的控制台行与 `tools/list` 回包，与端口号无关**（这是唯一被翻转的变量，如实写明）。

```text
EMPTY_DIR: F:\moonbit-hof-rs-t15-staging\empty-probe-dir   ENTRIES: []   PROJECT_GODOT_EXISTS: False
pid 26032   LAUNCH_CMD: …mono.exe -e --path <empty> --mcp-port=9879
[MCP] role=game configured_port=9879 source=cmdline listen=true
[MCP] listening on 127.0.0.1:9879 (editor=false, tools=73)
SERVED_TOOLS: 73   SERVED_BY_PREFIX: {"editor_": 0, "os_": 2, "project_": 48, "running_": 23}
editor_play_scene_served: False        running_game_get_scene_tree_served: True
editor_status -> {"error":{"code":-32601,"message":"Method not found: editor_status"}}
$ taskkill /PID 26032 /T /F -> exit=0（精确 pid）
```

**对照（唯一被翻转的变量是"目录里有没有 `project.godot`"）**：**同一二进制**在 `hoh init` **之后**的同一新工程上启动 ⇒ `role=editor`、`tools=154`（`{editor_:104, project_:48, os_:2}`、`running_game_*` = **0**、`project_list_scripts` = **0**，而 `mario` 磁盘上有 15 个脚本）。
⇒ **顺序必须是"先建空目录 → `hoh init` → 再由编辑器指向它"**（第 5 次独立复现）。

### 6.2 机制读数（每项写明作用域）

| 机制 | 本轮真实读数 |
|---|---|
| **零增量** | **未发生**。`warnings.log`（637 B / 4 个换行结尾行）里 `Zero-increment`/`no_progress`/`no_engineering_write` 各 **0** 次；`A_1 ≠ A_0` 且差异落在工程文件 |
| **修复尝试** | `repair_retry_used=false`、`launch_gate_repair` 在 `warnings.log` **0** 次；`wrap_up_retry_used=true`、`reason="artifact_missing"`；developer 两次 attempt 都是 `LimitsExceeded`、`notes` 为空 |
| **可启动闸门** | **唯一 pass 12/12 `launchable=true`**；`editor_errors_baseline` `count=0`、锚 0 行；窗口计数全 0（§4.2） |
| **64 KiB 上限** | **触发 1 次**：`tester.attempt1.json` **msg 18**：`limit=65536 / original=146150`（从 `extra.hoh_output_truncated` 解析，**不是** grep 字节） |
| **陈旧日志** | 本轮**没有**"陈旧行关门"可触发（判定读数 0 行）；轮后同一 pid 的该字段返回 `[MCP] capture=off …` 这类**非错误横幅行** ⇒ 该字段不稳定的实测复现（§4.3） |
| **端点可达（角色侧）** | 口径 A（`extra.actions[*].command` 在 `messages[*]` 内，4 个未脱敏轨迹）：记录命令 **344** 条；含 `tools call running_game_*` **0** 条；含 `tools call editor_play_scene` **0** 条；文本含 `running_game_` **5** 条。口径 B：`game_endpoint_unavailable`（DR-43 拒绝文本）在 7 个轨迹文件里 **0** 次 |
| **路由就绪（起游戏）** | 轮开始 `:60538` pid 3176（13:52:22 盘上读到）；电池 pass 1 `editor_play_scene → :57609` pid 20720，`running_game_get_scene_tree` **成功**（28 节点）；收工时 `tasklist` 只剩编辑器 30348，`editor_stop_scene` 回 `{"message":"No scene playing","stopped":false}` |
| **退出码四处同数** | `exit_code` 字节 `30 0a`、`process_exit_code` 字节 `30 0a`、`meta.json.exit_code=0`、wrapper `ROUND_EXIT: 0` |
| **usage 归属（DR-79 ②）** | 三角色 **ratio 全部 = 1.000**（planner 15/84,180、developer 175/8,940,812、tester 141/11,616,610；summary == attempts 之和）。**本轮 planner 有 `.redacted.json` 旁路副本**（t12/t13 造成 2.0 倍的形状），而 ratio 仍是 1.000 ⇒ 这是 T14 缺的**区分性**样本。仍属**推断**（比值），不是插桩 |
| **脱敏** | 3 个轨迹各有 `.redacted.json`；`result.json.secret_redactions = 9`；赋值形**逐族 raw=0**（§3）；密钥值 0 命中；**JSON 键形未覆盖**（§3，F-T15-1） |
| **越界写入（DR-25）** | `out_of_tree_writes = []`；`warnings.log` 里 `out_of_tree_cleanup` **0** 行；仓根仍有 **T14 遗留**的 `l.json`/`p2.json`/`pv.json`/`r.json`（本轮**未新增**、也未删除） |
| **图片证据** | `iter-1/candidate/.hoh/evidence/*.png` 存在（含 `frame-00` 与 replay before/after） |
| **轨迹合法性** | 7 个 JSON（4 原件 + 3 旁路）全部 `json.loads` 通过 |

---

## 7. 只读基线的未变证明（三口径）

**基线集合（12 条）**：`runs/smoke-t6..t13`（8）+ `.workspace/{mario,fresh-t11,fresh-t12,fresh-t13}`（4）。**按任务书增量 4，`.workspace/fresh-t14` 不是基线**（被无署名编辑器改写过），我也**没有**把它计入。

**口径 A（内容）**：PowerShell 5.1 `Get-ChildItem -Recurse -Force -File`；**仓根相对**小写 POSIX 路径 + TAB + 字节 + TAB + sha256；LF 连接、无尾随换行；`Sort-Object` **文化序**；整体 UTF-8 取 SHA-256。两次测量（开工 `13:50`、轮结束 `14:33`）**逐字节相同**：

```text
runs/smoke-t6        135  c144ef3219e21dd322978e41a5531d53dee270619c026585505920f9277a9c03  2026-09-29 02:32:01
runs/smoke-t7        115  6e4c1595753c2cdefb16e4d2e5f05242ca202c70c81a93e98ae2b9c92b520fb7  2026-09-29 14:41:14
runs/smoke-t8        358  6d11b2c61ec507b5f02525ddc0e7f7adb08763cd2439a4b08788b7fe51bdf5a7  2026-09-30 07:58:28
runs/smoke-t9         83  541e2d814e563ba667c95bde49765d05e44cf11aa5ab90b2f44931f30136ca9d  2026-09-30 11:27:29
runs/smoke-t10       232  319555896964ce1526f72a33cb239bf389fe29bcde23841764d13c57dfb38b8b  2026-09-30 18:23:08
runs/smoke-t11       186  a76c228f596f2a0a6309bca9cee304401ddffc2d10ab384488cfaaffb8e27392  2026-10-02 00:38:11
runs/smoke-t12       215  1d5889b7f371469459693f9904ba745ce805d571a8101afc6f6abba94aa53ea0  2026-10-02 03:37:43
runs/smoke-t13       268  2d0ee05d8e6dcf4a384c7a1295fdb05f2b508631baa4e0eebdc6d11c9fdeb138  2026-10-02 05:23:00
.workspace/mario     178  dee0a36f357c440d078c652d4d4b8990af1a63b88d282c1e36c04a16d006cc94  2026-09-30 18:23:08
.workspace/fresh-t11 100  4c07c0b6d4352a5a64e1b49908e3ae1325f62f0a3b4de44d17efc51ebffd13a4  2026-10-02 00:29:23
.workspace/fresh-t12 109  da56639bde817f5fddd0ef177543e587714418385cd57b4972ef17f63b3ce49c  2026-10-02 03:25:18
.workspace/fresh-t13 105  d423f6bf254317f10c373d9f1b663a8f8924d0b00783100e01c4f0ed429f33e3  2026-10-02 05:04:03
```

**口径标定（承重的一步）**：同一口径**逐字复现了任务书点名的锚点** `runs/smoke-t6 = 135 / c144ef32…7a9c03 / newest 2026-09-29 02:32:01`，并逐条复现 T14 报告公布表里的全部 10 条（`evidence/analysis/baseline_check.txt`）。

**口径 B（第二个独立口径）**：把**整张基线表文本**取 SHA-256，两次时点相同：`5a0d24cf1814877cff223c7e9d0a206869c5f30e67cd6ed6b9ab848dbe3c3103`。

**口径 C（时间窗）**：以轮次开始 `1790920336.985` 为界，Python 递归遍历（**不用这个 shell 的 `bash`**——T14 已证明它解析到 WSL bash）：

```text
files under runs/** (excluding runs/smoke-t15) newer than the window  = 0 []
files under the four read-only workspace dirs newer than the window   = 0 []
```

⇒ **12 条只读基线在内容、文件数、mtime 三个口径上都未变**；本轮产出只落在 `.workspace/fresh-t15/**` 与 `runs/smoke-t15/**`。**没有一条基线"不再匹配"**。
**披露**：收尾时我又用同一口径测了一次（为了在提交报告前再确认一次基线的未变），它把 `evidence/round/baseline_before_repo.txt` 覆写成了**字节完全相同**的第三次读数（表 SHA-256 仍是 `5a0d24cf…3103`）⇒ 该文件现在**同时**是开工读数与最终读数，二者内容逐字节相同；开工那一次的"BEFORE == AFTER"比较由先写下的 `evidence/analysis/baseline_check.txt` 原样保留。

**冻结件与仓库状态**：`PRD-mario.md` `4c81c3a9…5c3a`（逐字未变）；引擎二进制 `08483088…e9e6a`（与 T11–T14 记录逐字相同 ⇒ 本轮**未写** `godot-mcp/**`）；`DECISIONS.md` `245befb7…a76`、`.spec/hof-rs/REQUIREMENTS.md` `298a9489…`（记录，**本轮未改**）；`git status --porcelain` 只有 `M src/adapter/godot.rs`（**stat-cache 假象**：`git diff` 为空、`git hash-object` == `HEAD:src/adapter/godot.rs` == `05cc4fce…`，T14 验收已记录同一现象）与 4 个**上轮遗留**未跟踪 `*.json`（§10.7）；`HEAD == origin/master == c4a30fa`（**未 push**）。

---

## 8. 报告纪律自证

### (a) 全部"0 次 / 逐位相同 / 不存在"断言都可从其引用的文件复算，且写明作用域

| 断言 | 作用域 | 复算方式 / 文件 |
|---|---|---|
| 原始文档里 `editor_infrastructure_failures` = **0**、`project_defects_new` = **0** | 该轮的 `iter-1/candidate/.hoh/deterministic/raw/editor_errors_baseline.json` 的 `channel.editor_error_window` | `evidence/analysis/gate_t15.txt`（`json.load` 后逐字段打印） |
| 锚与判定各 **0** 行 | 同上（`anchor_line_count` 与 `calls[0].payload.count`） | 同上 |
| 赋值形原文存活 = **0** | 三个 `.redacted.json` 全文，逐族 | `evidence/analysis/redaction_counts_t15.txt` / `.json`（scanner，非正则） |
| 密钥值命中 = **0** | `runs/smoke-t15/**` + `.workspace/fresh-t15/**`，共 250 文件 | 同上（只报长度 51 与命中数） |
| 12 条基线**逐位未变** | 12 个目录的全部文件 | 两份 `baseline_*_repo.txt` + `baseline_check.py`（三口径） |
| 三棵树**逐字节相同** | 三个树（排除 `.hoh/.git/.godot/.import/node_modules/target`） | `evidence/analysis/e5_compare.txt` |
| 轮次窗口外**没有**文件被写 | `runs/**`（除 smoke-t15）与四个只读工作区 | `baseline_after.py`（口径 C） |
| `tools call running_game_*` 角色调用 = **0** | 4 个未脱敏轨迹的 `messages[*].extra.actions[*].command` | `evidence/analysis/caliber_audit_t15.txt` |
| `game_endpoint_unavailable` = **0** | 7 个轨迹文件全文 | 同上 |
| `quarantine/` 不存在 | `runs/smoke-t15/` | `ls` 与 `gate_t15.py` 的 quarantine 段 |

### (b) 机制归因附反例检验（"没看到 X" ≠ "X 不可能"）

见 §2.3 的四条跳跃反例、§3.1 的五条脱敏反例、§4.3 的门反例（本轮**没有**基础设施行 ≠ 它不可能出现：轮后同一字段就返回了另一条非错误行）、§6.1 的角色门对照。**明确标为推断/未定**的三处：① 为什么本轮编辑器重建了 `.godot` 而 T14 的没有（未插桩）；② DR-79 ② 的过滤只由 ratio 推断；③ 谁最初启动了 26716。

### (c) 机器可读块由 JSON 序列化器生成 + 栅栏感知 `json.loads` 回读（**已做**）

- **生成**：`evidence/scripts/build_json_block_t15.py`（内部 `json.dumps(..., ensure_ascii=False, indent=2)`，并在写盘前 `assert` 了本轮承重数字：`exit_code==0`、`artifact_gate=={"launchable":true,"reasons":[]}`、`start_state.mode=="fresh"`、`len(verified)==8`、`len(gap)==14`、`bat` 12/12、窗口三个计数为 0、每个旁路 `assignment_raw==0`、每个原件 `assignment_raw>0`）⇒ `evidence/analysis/machine_block.json`（36630 B，sha256 `d2f54a3e…ace0`）。
- **装配**：`evidence/scripts/assemble_report_t15.py` 把该文件的**字节原样**插入 ```json 栅栏。
- **回读**：`evidence/scripts/json_block_check_t15.py`（按行锚定 ``` 切块、只对 info string 为 `json` 的块 `json.loads`，并与 `machine_block.json` 比字节）⇒ `evidence/analysis/json_block_check.txt`。

### (d) 派生物数字与正文一致

正文所有数字都取自同一批脚本产物（`round_facts.txt`、`gate_t15.txt`、`battery_reads.txt`、`e3_extract.txt`、`e3_jump_t15.txt`、`caliber_audit_t15.txt`、`redaction_counts_t15.*`、`redaction_jsonkey_t15.txt`、`baseline_check.txt`、`mechanisms.txt`、`final_counts.txt`、`truncation_t15.txt`、`closeout_t15.txt`、`godot_cache_timeline.txt`），机器块由 `build_json_block_t15.py` 从**同一批冻结件**重读生成并带 `assert`。**所有派生文本都由 Python 以 `encoding="utf-8"` 显式写盘，没有一次控制台重定向**（`evidence/analysis/utf8_scan.txt`）。

---

## 9. 遗留风险与未验证项（严格区分实测 / 推断 / 未知）

**实测（本轮有原始证据）**

1. 空目录（0 条目）→ `hoh init` exit 0 → **恰好一轮** `hoh run`；`start_state=fresh`；`A_0` 3 文件/1727 B（与 T11–T14 同 id）→ `A_1` 13 文件/11095 B。
2. **门转绿**：`launchable=true`、`reasons=[]`、exit 0、电池 12/12；**E2 met**。
3. **E3 not met**：三类成立，**跳跃类是单调自由落体**（`rise=0.0`、`min` 在 index 0）。
4. **脱敏修复真机生效**：赋值形逐族 `raw=0`（24 / 22 / 15 处全被标记），原件仍有原文；密钥值 0 命中。
5. **同一族的 JSON 键形仍原文存活**（11 个已声明族 + 2 个未声明名，各文件 1 处，取值非空），成因未定、非本轮回归。
6. **12 条只读基线三口径未变**；三棵树逐字节同一；退出码四处同为 0。
7. 角色门第 5 次复现（空目录 73/role=game、init 后 154/role=editor）。
8. `.godot/editor/filesystem_cache10` 在本轮工作区存在（911 B），11 个 `.godot` 文件 mtime 全晚于清空时刻。
9. 64 KiB 截断触发 1 次（146150 → 65536）；`out_of_tree_writes=[]`；usage 三角色 ratio 1.000。
10. 轮末只剩编辑器 30348；无孤儿游戏进程；密钥值全轮 0 命中。

**推断（不得当作已测）**

1. **（≈0.8）** 本轮门红之所以消失，主要是编辑器**重建了 `.godot`**（所以缓存写失败没发生），而不是 DR-81 的豁免救了它——因为本轮**根本没有**基础设施行（两侧计数 0）；支持：11 个 `.godot` 文件的 mtime 全在清空之后、判定读数 `count=0`。**未插桩**。
2. **（≈0.7）** DR-79 ② 的过滤生效：planner 本轮有旁路副本而 ratio 仍 1.000。**没有**读过滤器的 span 报告。
3. **（≈0.6）** 跳跃类失败的直接原因是"地面在 x≈3411 之后不存在"（move_right 窗口起点仍在地面高度、60 帧内跑出去并下坠）；**我读的是位置采样**，没有读关卡的碰撞体范围来独立确认地面终点。
4. **（≈0.5）** 角色侧 live 路由本轮**没有被角色大量使用**（0 条 `tools call running_game_*`，5 条仅文本提及），所以本轮**不能**用来加强或削弱 T13/T14 的"角色侧 live 路由可用"结论。

**未达到 / 未知（必须点名）**

1. **F-T15-1（major，卫生）**：**同一批 `HOH_*` 变量族的 JSON 键形在冻结件与其脱敏副本里逐字存活**（路径/角色/迭代/run id/回环端点；无凭据）。DR-81 的修复只覆盖赋值形；此向量的成因与是否应纳入范围**未定**。
2. **F-T15-2（major，判据侧）**：**E3 not met**——产出关卡的跳跃窗口没有地板，跳跃不可观测；`position:neq` 断言无法区分"起跳"与"坠落"。**是否算产品缺陷还是判据/关卡生成的局限**，留给决策层（我按判据原文判 not met）。
3. **F-T15-3（minor，判据侧）**：`model.chat` 在 `hoh doctor`（无密钥环境）下 FAIL，属 C11 的**预期**行为，但会让"doctor 全绿"这类口径在无密钥的 shell 里误判；本轮按"直接 `--version` + doctor 运行期输出"两条独立读数绕过，未改动任何配置。
4. **F-T15-4（info）**：DR-81 ④ 的"运行中的编辑器不会重建 `.godot`"在本轮**被反例削弱**（见 §4.3）；机制归因未插桩。
5. **F-T15-5（info）**：`editor_get_errors` 的读数在轮内为 0 行、轮后为非错误横幅行 ⇒ 该字段不稳定，而门把它当硬判据（T14 的 F-T14-4 在本轮独立复现）。
6. **本轮未复现/未检验**：`zero-increment` 未发生；`repair_retry`（门修复）未触发；`wrap_up_retry` 触发了但原因是 `artifact_missing`；`out_of_tree_cleanup` 无产出。

---

## 10. 诚实披露（含重试、意外写入、别人的进程）

1. **二进制**：按 HEAD 重建，**没有**为制造 `Compiling` 行而 touch 任何文件（源文件本就比旧二进制新）；旧二进制确实陈旧（早于 DR-81 提交）。
2. **停掉了别人的进程（必须点名）**：开工时 9877 被**孤儿编辑器 PID 26716**（`--path .workspace/fresh-t14`，父进程 36808 已消失）占用。我留了原始身份与端口证据后，用 `taskkill /PID 26716 /T /F` 停它（原始输出在 `evidence/round/kill_and_build.txt`）。**原因**：Godot 启动时固定编辑器工程、没有任何工具能切换，留着它本轮无法让编辑器指向新工程，继续跑就是假轮。**它不是本轮的进程，也不是我启动的**；本轮编辑器 30348 是我随后启动的。
3. **`hoh doctor` 的 `model.chat` FAIL**：无密钥 shell 下的**预期**读数（C11）；我用 `--version` 直接探针与运行期 doctor 输出两条独立读数确认引擎身份，**没有**改配置、**没有**把 FAIL 说成 ok。
4. **`hoh run` 内的 attempt2 不是门修复**：`warnings.log` 里 `launch_gate_repair` 0 次、`repair_retry_used=false`、`wrap_up_retry_reason="artifact_missing"`；我不把它写成"门又红了一次"。
5. **我自己的分析脚本犯过一次会造假绿的错**：第一版脱敏计数用 `(?<![A-Za-z0-9_])` 左守卫，而 JSON 串里的环境转储由 `\n`（反斜杠+n）分隔，于是**每一个真实出现都被拒绝**、全族读数变成 0（看起来"干净"）。我把它改成接受 JSON 转义的扫描器，并把这次错误写进 `evidence/analysis/redaction_counts_t15.txt` 与本报告。**这也是本轮"派生物不得与正文矛盾"的实例**。
6. **口径 C 的遍历用 Python**（T14 已证明这个 shell 的 `bash` 解析到 WSL bash，`find -newermt` 语义不同）；本轮无失败重跑。
7. **`git status` 是脏的**：`M src/adapter/godot.rs` 是上批验收留下的 **stat-cache 假象**（`git diff` 空、`git hash-object` 与 `HEAD` 相同、文件纯 LF），4 个未跟踪 `*.json` 是 **T14 的越界写入遗留**；本轮 `out_of_tree_writes=[]`，我**未新增也未删除**它们。
8. **293 个外部写入与我无关**：`.workspace/fresh-t14` 的 107 文件/2,985,005 B（newest 13:00:40）由无署名编辑器 PID 26716 写成（D294 与 DR-81 验收已记录同一进程）；我**未**把它计入任何基线。
9. **密钥卫生**：`HOH_MODEL_API_KEY` 只从 `config/model.secret.env` 注入**子进程环境**（`run_stream.py --env-from-secret`），**只报长度 51、从不打印**；对整个 `runs/smoke-t15` 与本轮工作区的扫描 **0** 命中。
10. **未 push**：`origin/master == c4a30fa…`（与开工相同）；本轮提交只含报告文件。
11. **本报告的证据全部来自本轮**；对 T10–T14 的引用只用于**口径标定**、**历史对照**与**"是否为本轮回归"的反例检验**（§3.1 的 t14 交叉扫描），不冒充本轮读数。

---

## 11. **本轮是否说明"当前修订在真机上全绿"？**

**结论：不是全绿。六条判据里五条 met、一条（E3）not met；但上一轮把这一轮判红的那个原因（产品自己的启动门）本轮在真机上转绿了。**

**支持"绿"的一侧（均为本轮实测）**

1. **启动门绿**：`artifact_gate={"applicable":true,"launchable":true,"reasons":[]}`、`hoh run` **exit 0**（四处同数）、电池**唯一 pass 12/12 ok**。上一轮同一命令序列在这个门上是 `launchable=false` / exit 6。
2. **E1/E2/E4/E5/E6 met**：可空工程 → 合法 `D_1` → 真实工程增量（10 新增 + `main.tscn` 342→5144 B）→ 合法 `E_1`（8 verified / 14 gap、30 条记录、`MISSING=[]`）→ 三棵树逐字节同一 → QA 诚实。
3. **脱敏修复在真机上确实生效**：三个旁路副本里**逐族 `raw=0`**，而对应原件仍有原文；密钥值 0 命中。
4. **12 条只读基线三口径逐字节未变**；引擎二进制与 T11–T14 逐字相同（未写引擎树）。

**反对"绿"的一侧（均为本轮实测）**

1. **E3 not met**：跳跃类是**单调自由落体**（`x unique=1`、`y` 从 1492.81 单调升到 2552.93、`min` 在 index 0、`rise=0.0`），而 `jump:replay_assert_moved` 依然 `passed=true` ⇒ **不能**把"断言通过"读成"跳起来了"；QA 自己把同一读数记为 gap `F2`。**这一条是判据原文的硬性四类之一**，因此本轮**不是**"六条全 met 的一轮"。
2. **同一批变量族的 JSON 键形仍原文存活**（路径/角色/迭代/run id/回环端点；无凭据）——上一轮修的是赋值形，这个形状未被覆盖，也**不是**本轮引入的回归。
3. **`editor_get_errors` 仍是不稳定的日志尾读数**（轮内 0 行、轮后一条非错误横幅行），而门把它当硬判据。

**一句话**：**这一轮证明"上一轮的门红不是项目缺陷、并且在新修订上真的不再关门"，同时暴露了另一个只在真机上才看得见的红（跳跃不可观测 + JSON 键形披露）。因此"当前修订真机上全绿"仍未被建立，本轮给出的是一条更窄、更有用的结论：门与脱敏两项修复在真机上有效，六条判据仍差 E3 一条。**

---

## 12. 工件索引

| 类别 | 路径 |
|---|---|
| 轮记录（运行时） | `runs/smoke-t15/`：`exit_code`、`process_exit_code`、`meta.json`、`warnings.log`、`TOOLS.md`、`versions/{index.json,3ac25f6c…,cde233b9…}`、`iter-1/{plan.md,result.json,evidence.json,usage.json,qa_report.md,logs/,traj/,planner-view/,candidate/}`（**无 `quarantine/`**） |
| 被开发工程 | `.workspace/fresh-t15/**`（`project.godot`、`scenes/main.tscn`、`scripts/*.gd`） |
| 原始取证（本轮自建，已并入） | `runs/smoke-t15/evidence/**`：`round/**`、`analysis/**`、`gatecheck/**`、`scripts/**`，另有 `evidence/COPY_MANIFEST.txt`（作用域 = `{round,gatecheck,analysis}` 三个采集目录，**47 个文件**：round 22 + gatecheck 4 + analysis 21；**不含 `analysis/machine_block.json` 自身**，使计数稳定；`scripts/` 另有 **73** 个可跑脚本副本。**逐文件的字节数与 sha256 见该清单**） |
| 可复跑脚本 | `runs/smoke-t15/evidence/scripts/**`（`preflight.py`、`preflight_doctor.py`、`kill_and_build.py`、`binary_markers_t15.py`、`stage_workspace.py`、`launch_engine.py`、`wait_ready.py`、`editor_listener.py`、`run_stream.py`、`mcp_call.py`、`t15_analysis.py`、`tree_hash.py`、`gate_t15.py`、`redaction_counts_t15.py`、`redaction_jsonkey_t15.py`、`e3_extract.py`、`e3_jump_t15.py`、`battery.py`、`mechanisms.py`、`final_counts.py`、`truncation_t15.py`、`caliber_audit_t15.py`、`role_gate_t15.py`、`closeout_t15.py`、`godot_cache_timeline.py`、`baseline_digest.ps1`、`baseline_check.py`、`baseline_after.py`、`build_json_block_t15.py`、`assemble_report_t15.py`、`json_block_check_t15.py`、`copy_evidence_t15.py` 等） |
| 分析输出 | `runs/smoke-t15/evidence/analysis/**`（全部由 Python 以 `encoding="utf-8"` 显式写盘） |
| 规范 / 任务书 | `.spec/hof-rs/REQUIREMENTS.md`（E1..E6 第 110–119 行）、`.spec/hof-rs/OBJECTIVE-COMPLETION.md`、`tasks/TASK-SMOKE-T12.md`、`tasks/TASK-SMOKE-T13.md`（**无 `TASK-SMOKE-T15.md`**；本轮增量条款来自调度者的派发指令） |
| 上轮对照 | `tasks/TASK-SMOKE-T12-REPORT.md`/`-ACCEPTANCE.md`、`TASK-SMOKE-T13-REPORT.md`（含 DR-79 追加勘误）/`-ACCEPTANCE.md`、`TASK-SMOKE-T14-REPORT.md`/`-ACCEPTANCE.md`、`TASK-DR81-REPORT.md`/`-ACCEPTANCE.md` |
| 相关决策（只读） | `DECISIONS.md` **D289–D294** |

---

## 附：机器可读结论

（本块由 `evidence/scripts/build_json_block_t15.py` 用 `json.dumps(..., ensure_ascii=False, indent=2)` 序列化，并在写盘前 `assert` 了本轮全部承重数字；与 `evidence/analysis/machine_block.json` **逐字相同**，由 `evidence/scripts/assemble_report_t15.py` 以**字节原样**插入。落盘后由 `evidence/scripts/json_block_check_t15.py` 以**行锚定、栅栏感知**的方式 `json.loads` 回读并比字节。）

```json
{
  "task": "TASK-SMOKE-T15",
  "kind": "stability round: one more run of the T12/T13 command sequence on the revision that carries DR-81, with a real-hardware check of the redaction repair and of the launch gate",
  "round_id": "smoke-t15",
  "run_dir": "runs/smoke-t15",
  "project_dir": ".workspace/fresh-t15",
  "evidence_dir": "runs/smoke-t15/evidence",
  "head_at_start": "c4a30fae620b65db4035368b20cb12853ff918d0",
  "head_at_report_time": "c4a30fae620b65db4035368b20cb12853ff918d0",
  "origin_master_at_start": "c4a30fae620b65db4035368b20cb12853ff918d0",
  "dr81_commit": "cb507e8840daef3a7b0094712f8248c4c280adb7",
  "commands": {
    "empty_proof": "cmd /c mkdir F:\\moonbit-hof-rs\\.workspace\\fresh-t15 (proved absent, then 0 entries)",
    "init": "target/release/hoh.exe init --project F:\\moonbit-hof-rs\\.workspace\\fresh-t15",
    "run": "target/release/hoh.exe run --iterations 1 --run-id smoke-t15 --fresh-workspace --project F:\\moonbit-hof-rs\\.workspace\\fresh-t15",
    "engine_launch": "F:\\moonbit-hof-rs\\godot-mcp\\godot\\bin\\godot.windows.editor.x86_64.mono.exe -e --path F:\\moonbit-hof-rs\\.workspace\\fresh-t15 --mcp-port=9877",
    "identical_to_t14_apart_from": [
      "the run id",
      "the project directory"
    ]
  },
  "binary": {
    "path": "target/release/hoh.exe",
    "size_bytes": 12746752,
    "mtime_unix": 1790920275,
    "sha256": "3bc1657b144e9c2ddd7262296428762814875d1d535692ae9f8da8b010d43f0b",
    "rebuilt_this_round": true,
    "rebuilt_from": "HEAD c4a30fa (DR-81 is in cb507e8)",
    "forced_compile_line": "Compiling hof-rs v0.1.0 (F:\\moonbit-hof-rs)",
    "stale_predecessor": {
      "size_bytes": 12727808,
      "mtime_unix": 1790905290,
      "sha256": "3b97e4a02436bac781a41e3675ac7c4cb341c44d1682c297c3911d5d0cb80ba3",
      "why_stale": "built at 09:41, before the DR-81 commit cb507e8 at 13:20"
    },
    "markers": {
      "res://.godot/": 3,
      "cannot create file": 1,
      "check user write permissions": 1,
      "editor_infrastructure_failures": 3,
      "project_defects_new": 3,
      "editor_error_window": 1,
      "window anchored with max_lines": 1,
      "DSH_TERM_CMD": 1,
      "HOH_GAME_ROUTE": 5,
      "STALE_ACTION_NOT_RELEASED": 1
    },
    "marker_evidence": "runs/smoke-t15/evidence/round/binary_markers.txt"
  },
  "engine": {
    "version_string": "4.8.dev.mono.custom_build.035edfce7",
    "sha256": "08483088a4a2772841cd3b4c916b2d45b3cb6255656cf3951598a86fce7e9e6a",
    "size_bytes": 194216960,
    "listener_pid": 30348,
    "listener_command_line": "F:\\moonbit-hof-rs\\godot-mcp\\godot\\bin\\godot.windows.editor.x86_64.mono.exe -e --path F:\\moonbit-hof-rs\\.workspace\\fresh-t15 --mcp-port=9877",
    "started_by_this_round": true,
    "matches_binary": true,
    "alive_at_close": true,
    "editor_tools": 154,
    "project_list_scripts_count": 0,
    "mario_scripts_on_disk": 15
  },
  "foreign_process_reclaimed": {
    "pid": 26716,
    "command_line": "F:\\moonbit-hof-rs\\godot-mcp\\godot\\bin\\godot.windows.editor.x86_64.mono.exe --path F:/moonbit-hof-rs/.workspace/fresh-t14 -e res://scenes/main.tscn",
    "parent": 36808,
    "creation": "2026-10-02 13:00:30",
    "why": "Godot fixes the editor project at startup and no tool can switch it, so an editor pointed at fresh-t14 blocks this round's mandatory order (empty dir -> init -> point the editor at the new project).  It was an orphan (its parent, the smoke-t14 editor 36808, was gone) holding 9877.",
    "action": "taskkill /PID 26716 /T /F -> exit 0, 'SUCCESS: The process with PID 26716 ... has been terminated.'",
    "after": "netstat :9877 has no LISTENING row and tasklist has no godot process"
  },
  "start_state": {
    "mode": "fresh",
    "version_id": null
  },
  "project_identity": {
    "A0": {
      "runtime_id": "3ac25f6c5c38885febd3a001ea99c88aca61b1799c7b105306919886c2c1d151",
      "files": 3,
      "bytes": 1727,
      "independent_recompute_matches": true
    },
    "A1": {
      "runtime_id": "cde233b96c5b0a7bfd22a31078897231d0595cee6dd40ab9fe9df017d8fc8c37",
      "files": 13,
      "bytes": 11095,
      "independent_recompute_matches": true
    },
    "A1_neq_A0": true,
    "added": [
      "scripts/coin.gd",
      "scripts/coin.gd.uid",
      "scripts/enemy.gd",
      "scripts/enemy.gd.uid",
      "scripts/goal.gd",
      "scripts/goal.gd.uid",
      "scripts/main.gd",
      "scripts/main.gd.uid",
      "scripts/player.gd",
      "scripts/player.gd.uid"
    ],
    "modified": [
      "scenes/main.tscn"
    ],
    "removed": [],
    "three_trees_byte_identical": true
  },
  "timing": {
    "started_console": "2026-10-02 13:52:16",
    "ended_console": "2026-10-02 14:30:51",
    "elapsed_seconds": 2314.11,
    "round_exit": 0,
    "rounds_that_actually_started": 1,
    "aborted_launches": 0
  },
  "exit_codes": {
    "exit_code_hex": "300a",
    "process_exit_code_hex": "300a",
    "meta_exit_code": 0,
    "wrapper_round_exit": 0,
    "all_four_agree": true
  },
  "verdicts": {
    "E1": "met",
    "E2": "met",
    "E3": "not_met",
    "E4": "met",
    "E5": "met",
    "E6": "met"
  },
  "criteria": [
    {
      "id": "E1",
      "pass": true,
      "evidence": "directory proved absent then empty (0 entries, 0 recursive entries) -> hoh init exit 0 -> exactly one run; start_state.mode=fresh; A0 3ac25f6c 3 files/1727 B -> A1 cde233b9 13 files/11095 B (10 added, scenes/main.tscn modified, 0 removed); plan.md carries ### Priority Order / ### Preservation Gate / ### Acceptance Gate and artifact_valid=true; evidence.json parses with 8 verified / 14 gap; exit codes agree four ways at 0"
    },
    {
      "id": "E2",
      "pass": true,
      "evidence": "the product's own gate says yes: artifact_gate {applicable:true, launchable:true, reasons:[]} and hoh run exits 0; the frozen battery pass is 12/12 ok including editor_errors_baseline (count=0), play_scene_ready (playing=true, endpoint :57609 pid 20720, running_game_get_scene_tree returns 28 nodes) and engine_identity; the raw document carries the window anchor (max_lines=2000 before project_reload_and_open, anchor_line_count=0) and the counts (banners 0, stale 0, editor_infrastructure_failures 0, pre_existing 0, project_defects_new 0)"
    },
    {
      "id": "E3",
      "pass": false,
      "evidence": "three of the four classes are observed from game-endpoint semantic tools: move_right x 3411.3544921875 -> 3627.69262695312 (+216.33813476562, 60/60 unique x) and move_left x 3679.02709960938 -> 3462.68896484375 (-216.33813476563, 60/60 unique x), an interactable object (running_game_get_node_properties /root/Main/HUD/Coins text 'Coins: 0' at call 0 -> 'Coins: 1' at call 90, with running_game_assert_node_state text:neq passed=true), and a win condition (Goal.reached false -> true, assert reached:neq passed=true). The jump class fails: in the window driven by the jump recording (raw/input_replay.json call 31, 30 samples) x is constant (unique=1) and y is strictly increasing 1492.81433105469 .. 2552.92553710938 with the minimum at index 0 and rise=0.0 - it is a free fall, not an upward arc; the engine's own position:neq assertion passes only because the position changed. QA records the same reading as gap F2 ('never shows an upward arc')."
    },
    {
      "id": "E4",
      "pass": true,
      "evidence": "iter-1/evidence.json parses: qa_status partial, verified 8 [N1,N2,F1,F3,F5,F10,F13,F16], gap 14 [F2,F1R,F4,F6,F7,F8,F9,F11,F12,F14,F17,F15,F10D,N3], overlap [], no duplicate ids; 30 execution records, 19 attached to verified and 11 to gap claims (scopes stated), every record candidate_id = cde233b9, every path exists (MISSING=[]), every gap carries player_impact and recommended_update, planner_handoff 3/6/3"
    },
    {
      "id": "E5",
      "pass": true,
      "evidence": "versions/cde233b9, iter-1/candidate and live .workspace/fresh-t15 are byte-identical: the independent hash_tree port gives the same id cde233b96c5b0a7bfd22a31078897231d0595cee6dd40ab9fe9df017d8fc8c37, 13 files / 11095 B each, only_in=[], differing=[]; QA did not modify A1"
    },
    {
      "id": "E6",
      "pass": true,
      "evidence": "iter-1/qa_report.md states 'qa_status = partial' and enumerates the open items with player impact, including F2 jump ('unproven'), F6 wall, F7/F8/F9 enemy, F11/F12 blocks, F14/F15 fail/restart, F17 level length, N3 stability; it records the known input_axis assertion as the harness's own DR-58 design and never scores it as a claim; no unmet item is reported as verified"
    }
  ],
  "criteria_note": "E3 is scored as not met even though the round is otherwise the strongest one yet: the jump class is a core verb of the same criterion, and a monotone fall under the jump input is not a jump.  The engine-side position:neq assertion passing does not change that, which is exactly the 'injected != moved' distinction the task books require.",
  "gate": {
    "artifact_gate": {
      "applicable": true,
      "launchable": true,
      "reasons": []
    },
    "window": {
      "anchor": "editor_get_errors max_lines=2000 taken immediately before `project_reload_and_open`; the judged reading is max_lines=50 taken after it",
      "anchor_line_count": 0,
      "anchor_request_and_answer": {
        "args": {
          "max_lines": 2000
        },
        "ok": true,
        "payload": {
          "content": [
            {
              "text": "{\"available\":true,\"count\":0,\"editor\":true,\"errors\":[],\"in_process\":true,\"log_path\":\"user://logs/godot.log\",\"note\":\"\",\"pid\":30348,\"port\":9877,\"process\":\"editor\",\"source\":\"editor_log\"}",
              "type": "text"
            }
          ]
        },
        "request_id": 8,
        "response_id": 8,
        "sync_probes": 0,
        "tool": "editor_get_errors"
      },
      "banners": 0,
      "criterion": "an editor log line closes the gate only when it is not an exact DR-48 engine banner, not stale by DR-68, not editor infrastructure by DR-81 ①, and its number of occurrences grew between the pre-reload anchor reading and the judged reading",
      "editor_infrastructure_failures": 0,
      "pre_existing_lines": 0,
      "project_defects_new": 0,
      "stale": 0
    },
    "anchor_payload_count": 0,
    "battery_passes": [
      {
        "pass": 1,
        "launchable": true,
        "steps": [
          [
            "project_reload_and_open",
            true
          ],
          [
            "scene_structure",
            true
          ],
          [
            "editor_errors_baseline",
            true
          ],
          [
            "play_scene_ready",
            true
          ],
          [
            "scene_tree",
            true
          ],
          [
            "screenshot",
            true
          ],
          [
            "interaction_evidence",
            true
          ],
          [
            "input_channel_probe",
            true
          ],
          [
            "input_replay",
            true
          ],
          [
            "node_and_collision_assertions",
            true
          ],
          [
            "editor_stop_scene",
            true
          ],
          [
            "engine_identity",
            true
          ]
        ]
      }
    ],
    "infrastructure_line_observed": false,
    "infrastructure_line_note": "no line was classified as editor infrastructure because the judged reading and the anchor were both empty (count=0, anchor_line_count=0).  This is 'we did not see it', not 'it cannot happen': the same field returned '[MCP] capture=off (default; ...)' - a non-error banner line - when read live after the round (evidence/round/closeout_t15.txt), and .godot/editor/filesystem_cache10 exists in this workspace (911 B) with mtimes 14:05..14:30, after the --fresh-workspace purge at 13:52:17."
  },
  "behaviours": {
    "move_left": {
      "x_first": 3679.02709960938,
      "x_last": 3462.68896484375,
      "delta": -216.33813476563,
      "unique_x_over_60_samples": 60,
      "assertion": "move_left:replay_assert_moved passed=true"
    },
    "move_right": {
      "x_first": 3411.3544921875,
      "x_last": 3627.69262695312,
      "delta": 216.33813476562,
      "unique_x_over_60_samples": 60,
      "assertion": "move_right:replay_assert_moved passed=true"
    },
    "jump": {
      "verdict": "not demonstrated (free fall)",
      "x_unique": 1,
      "x_value": 3690.02734375,
      "y_first": 1492.81433105469,
      "y_min": 1492.81433105469,
      "y_min_index": 0,
      "y_last": 2552.92553710938,
      "y_unique": 30,
      "y_nondecreasing": true,
      "rise": 0.0,
      "assertion": "jump:replay_assert_moved passed=true (position:neq only proves the position changed)",
      "qa": "gap F2 jump: 'the recorded jump window starts mid-air ... never shows an upward arc'"
    },
    "interactable_object": {
      "coin_before": "Coins: 0",
      "coin_after": "Coins: 1",
      "assertion": "running_game_assert_node_state text:neq passed=true"
    },
    "win_condition": {
      "goal_reached_before": false,
      "goal_reached_after": true,
      "assertion": "running_game_assert_node_state reached:neq passed=true"
    },
    "injected_vs_moved": "interaction_evidence call[4] is the stale-release probe (event_count 1, injected 1) and each of the 14 driven batches reports injected=1 with 60/60 unique x; the jump window reports injected=1 (event action 'jump', pressed true) yet the player only falls, so 'the input was delivered' and 'the player jumped' are different facts and this round has a concrete instance of the gap."
  },
  "redaction": {
    "claim_under_test": "the DR-81 repair makes splice_assignments use a real interval overlap so a repeated environment dump can no longer leave whole variable families raw",
    "scope": "runs/smoke-t15/iter-1/traj/*.json",
    "assignment_form": {
      "runs/smoke-t15/iter-1/traj/developer.attempt1.json": {
        "assignment_occurrences": 22,
        "assignment_marked": 0,
        "assignment_raw": 22,
        "families_with_occurrences": {
          "HOH_ARTIFACT_DIR": {
            "family": "HARNESS",
            "marked": 0,
            "raw": 2,
            "total": 2
          },
          "HOH_GAME_ROUTE": {
            "family": "HARNESS",
            "marked": 0,
            "raw": 2,
            "total": 2
          },
          "HOH_HOH_BIN": {
            "family": "HARNESS",
            "marked": 0,
            "raw": 2,
            "total": 2
          },
          "HOH_ITERATION": {
            "family": "HARNESS",
            "marked": 0,
            "raw": 2,
            "total": 2
          },
          "HOH_MODEL_API_KEY": {
            "family": "SECRET",
            "marked": 0,
            "raw": 2,
            "total": 2
          },
          "HOH_ROLE": {
            "family": "HARNESS",
            "marked": 0,
            "raw": 2,
            "total": 2
          },
          "HOH_RUN_DIR": {
            "family": "HARNESS",
            "marked": 0,
            "raw": 2,
            "total": 2
          },
          "HOH_RUN_ID": {
            "family": "HARNESS",
            "marked": 0,
            "raw": 2,
            "total": 2
          },
          "HOH_SCRATCH_DIR": {
            "family": "HARNESS",
            "marked": 0,
            "raw": 2,
            "total": 2
          },
          "HOH_TOOLS_ENDPOINT": {
            "family": "HARNESS",
            "marked": 0,
            "raw": 2,
            "total": 2
          },
          "HOH_VIEW_DIR": {
            "family": "HARNESS",
            "marked": 0,
            "raw": 2,
            "total": 2
          }
        },
        "markers": 0
      },
      "runs/smoke-t15/iter-1/traj/developer.attempt1.redacted.json": {
        "assignment_occurrences": 22,
        "assignment_marked": 22,
        "assignment_raw": 0,
        "families_with_occurrences": {
          "HOH_ARTIFACT_DIR": {
            "family": "HARNESS",
            "marked": 2,
            "raw": 0,
            "total": 2
          },
          "HOH_GAME_ROUTE": {
            "family": "HARNESS",
            "marked": 2,
            "raw": 0,
            "total": 2
          },
          "HOH_HOH_BIN": {
            "family": "HARNESS",
            "marked": 2,
            "raw": 0,
            "total": 2
          },
          "HOH_ITERATION": {
            "family": "HARNESS",
            "marked": 2,
            "raw": 0,
            "total": 2
          },
          "HOH_MODEL_API_KEY": {
            "family": "SECRET",
            "marked": 2,
            "raw": 0,
            "total": 2
          },
          "HOH_ROLE": {
            "family": "HARNESS",
            "marked": 2,
            "raw": 0,
            "total": 2
          },
          "HOH_RUN_DIR": {
            "family": "HARNESS",
            "marked": 2,
            "raw": 0,
            "total": 2
          },
          "HOH_RUN_ID": {
            "family": "HARNESS",
            "marked": 2,
            "raw": 0,
            "total": 2
          },
          "HOH_SCRATCH_DIR": {
            "family": "HARNESS",
            "marked": 2,
            "raw": 0,
            "total": 2
          },
          "HOH_TOOLS_ENDPOINT": {
            "family": "HARNESS",
            "marked": 2,
            "raw": 0,
            "total": 2
          },
          "HOH_VIEW_DIR": {
            "family": "HARNESS",
            "marked": 2,
            "raw": 0,
            "total": 2
          }
        },
        "markers": 22
      },
      "runs/smoke-t15/iter-1/traj/developer.attempt2.json": {
        "assignment_occurrences": 0,
        "assignment_marked": 0,
        "assignment_raw": 0,
        "families_with_occurrences": {},
        "markers": 0
      },
      "runs/smoke-t15/iter-1/traj/planner.attempt1.json": {
        "assignment_occurrences": 24,
        "assignment_marked": 0,
        "assignment_raw": 24,
        "families_with_occurrences": {
          "DSH_TERM_CMD": {
            "family": "HARNESS",
            "marked": 0,
            "raw": 2,
            "total": 2
          },
          "HOH_ARTIFACT_DIR": {
            "family": "HARNESS",
            "marked": 0,
            "raw": 2,
            "total": 2
          },
          "HOH_GAME_ROUTE": {
            "family": "HARNESS",
            "marked": 0,
            "raw": 2,
            "total": 2
          },
          "HOH_HOH_BIN": {
            "family": "HARNESS",
            "marked": 0,
            "raw": 2,
            "total": 2
          },
          "HOH_ITERATION": {
            "family": "HARNESS",
            "marked": 0,
            "raw": 2,
            "total": 2
          },
          "HOH_MODEL_API_KEY": {
            "family": "SECRET",
            "marked": 0,
            "raw": 2,
            "total": 2
          },
          "HOH_ROLE": {
            "family": "HARNESS",
            "marked": 0,
            "raw": 2,
            "total": 2
          },
          "HOH_RUN_DIR": {
            "family": "HARNESS",
            "marked": 0,
            "raw": 2,
            "total": 2
          },
          "HOH_RUN_ID": {
            "family": "HARNESS",
            "marked": 0,
            "raw": 2,
            "total": 2
          },
          "HOH_SCRATCH_DIR": {
            "family": "HARNESS",
            "marked": 0,
            "raw": 2,
            "total": 2
          },
          "HOH_TOOLS_ENDPOINT": {
            "family": "HARNESS",
            "marked": 0,
            "raw": 2,
            "total": 2
          },
          "HOH_VIEW_DIR": {
            "family": "HARNESS",
            "marked": 0,
            "raw": 2,
            "total": 2
          }
        },
        "markers": 0
      },
      "runs/smoke-t15/iter-1/traj/planner.attempt1.redacted.json": {
        "assignment_occurrences": 24,
        "assignment_marked": 24,
        "assignment_raw": 0,
        "families_with_occurrences": {
          "DSH_TERM_CMD": {
            "family": "HARNESS",
            "marked": 2,
            "raw": 0,
            "total": 2
          },
          "HOH_ARTIFACT_DIR": {
            "family": "HARNESS",
            "marked": 2,
            "raw": 0,
            "total": 2
          },
          "HOH_GAME_ROUTE": {
            "family": "HARNESS",
            "marked": 2,
            "raw": 0,
            "total": 2
          },
          "HOH_HOH_BIN": {
            "family": "HARNESS",
            "marked": 2,
            "raw": 0,
            "total": 2
          },
          "HOH_ITERATION": {
            "family": "HARNESS",
            "marked": 2,
            "raw": 0,
            "total": 2
          },
          "HOH_MODEL_API_KEY": {
            "family": "SECRET",
            "marked": 2,
            "raw": 0,
            "total": 2
          },
          "HOH_ROLE": {
            "family": "HARNESS",
            "marked": 2,
            "raw": 0,
            "total": 2
          },
          "HOH_RUN_DIR": {
            "family": "HARNESS",
            "marked": 2,
            "raw": 0,
            "total": 2
          },
          "HOH_RUN_ID": {
            "family": "HARNESS",
            "marked": 2,
            "raw": 0,
            "total": 2
          },
          "HOH_SCRATCH_DIR": {
            "family": "HARNESS",
            "marked": 2,
            "raw": 0,
            "total": 2
          },
          "HOH_TOOLS_ENDPOINT": {
            "family": "HARNESS",
            "marked": 2,
            "raw": 0,
            "total": 2
          },
          "HOH_VIEW_DIR": {
            "family": "HARNESS",
            "marked": 2,
            "raw": 0,
            "total": 2
          }
        },
        "markers": 24
      },
      "runs/smoke-t15/iter-1/traj/tester.attempt1.json": {
        "assignment_occurrences": 15,
        "assignment_marked": 0,
        "assignment_raw": 15,
        "families_with_occurrences": {
          "HOH_ARTIFACT_DIR": {
            "family": "HARNESS",
            "marked": 0,
            "raw": 5,
            "total": 5
          },
          "HOH_HOH_BIN": {
            "family": "HARNESS",
            "marked": 0,
            "raw": 5,
            "total": 5
          },
          "HOH_SCRATCH_DIR": {
            "family": "HARNESS",
            "marked": 0,
            "raw": 5,
            "total": 5
          }
        },
        "markers": 0
      },
      "runs/smoke-t15/iter-1/traj/tester.attempt1.redacted.json": {
        "assignment_occurrences": 15,
        "assignment_marked": 15,
        "assignment_raw": 0,
        "families_with_occurrences": {
          "HOH_ARTIFACT_DIR": {
            "family": "HARNESS",
            "marked": 5,
            "raw": 0,
            "total": 5
          },
          "HOH_HOH_BIN": {
            "family": "HARNESS",
            "marked": 5,
            "raw": 0,
            "total": 5
          },
          "HOH_SCRATCH_DIR": {
            "family": "HARNESS",
            "marked": 5,
            "raw": 0,
            "total": 5
          }
        },
        "markers": 15
      }
    },
    "json_key_form_finding": {
      "what": "the harness's own role-config dump writes the same names as JSON keys with real values, and that shape is not covered by the repair: in every sidecar (and in every sealed original) `\"HOH_GAME_ROUTE\": \"F:...game_endpoint.json\"`, `\"HOH_HOH_BIN\"`, `\"HOH_ROLE\"`, `\"HOH_ITERATION\"`, `\"HOH_RUN_DIR\"`, `\"HOH_RUN_ID\"`, `\"HOH_SCRATCH_DIR\"`, `\"HOH_TOOLS_ENDPOINT\"`, `\"HOH_VIEW_DIR\"`, `\"HOH_ARTIFACT_DIR\"` (and the unclaimed `HOH_TOOLS_POLICY`, `HOH_WORKSPACE`) each survive with a non-empty raw value; the four credential names survive only as empty strings",
      "counts_scope": "analysis/redaction_jsonkey_t15.txt (same seven trajectory files)",
      "disclosure_level": "paths, role, iteration, run id and a loopback endpoint URL; no credential value"
    },
    "secret_value_scan": {
      "files_scanned": 250,
      "hits": [],
      "key_len": 51
    },
    "verdict": "the repaired assignment scan is effective on the real path (raw=0 in every sidecar; the sealed originals still carry the raw form, so the comparison is meaningful), and the secret value itself never appears.  The JSON-key shape of the same families remains raw and is a new, separately measured disclosure vector, not a regression of the repaired one."
  },
  "role_gate_reproduction": {
    "why_port_differs": "the round's editor must stay alive at close and holds 9877, so the empty-dir leg ran on 9879; the role decision comes from the engine's own console line and the tools/list reply, not from the port number",
    "empty_dir": {
      "dir": "F:\\moonbit-hof-rs-t15-staging\\empty-probe-dir",
      "entries": [],
      "project_godot_exists": false,
      "pid": 26032,
      "role": "game",
      "tools_served": 73,
      "served_by_prefix": {
        "editor_": 0,
        "os_": 2,
        "project_": 48,
        "running_": 23
      },
      "editor_play_scene_served": false,
      "editor_status": "{\"error\":{\"code\":-32601,\"message\":\"Method not found: editor_status\"}}"
    },
    "after_init": {
      "dir": ".workspace/fresh-t15",
      "pid": 30348,
      "role": "editor",
      "tools_served": 154,
      "served_by_prefix": {
        "editor_": 104,
        "os_": 2,
        "project_": 48,
        "running_": 0
      },
      "project_list_scripts_count": 0,
      "mario_scripts_on_disk": 15
    },
    "conclusion": "reproduced for the fifth time; the only variable flipped is project.godot's presence"
  },
  "baselines": {
    "caliber": "Get-ChildItem -Recurse -Force -File; repo-root-relative lowercase POSIX path + TAB + bytes + TAB + sha256; LF-joined, no trailing newline; culture order; SHA-256 of those UTF-8 bytes",
    "caliber_is_anchored": "reproduces the task-book anchor runs/smoke-t6 = 135 / c144ef32...7a9c03 / 2026-09-29 02:32:01 and the ten rows T14 published",
    "dirs": [
      "runs/smoke-t6",
      "runs/smoke-t7",
      "runs/smoke-t8",
      "runs/smoke-t9",
      "runs/smoke-t10",
      "runs/smoke-t11",
      "runs/smoke-t12",
      "runs/smoke-t13",
      ".workspace/mario",
      ".workspace/fresh-t11",
      ".workspace/fresh-t12",
      ".workspace/fresh-t13"
    ],
    "table_sha256_before": "5a0d24cf1814877cff223c7e9d0a206869c5f30e67cd6ed6b9ab848dbe3c3103",
    "table_sha256_after": "5a0d24cf1814877cff223c7e9d0a206869c5f30e67cd6ed6b9ab848dbe3c3103",
    "tables_byte_identical": true,
    "rows_that_no_longer_match": [],
    "time_window_start_epoch": 1790920336.985,
    "files_newer_than_the_window_outside_smoke_t15": 0,
    "excluded_by_the_task_book": {
      ".workspace/fresh-t14": "not a baseline; rewritten by the external editor"
    },
    "informational_not_baselines": {
      "runs/smoke-t14": {
        "files": 300,
        "bytes": 4564948,
        "newest": "2026-10-02 10:36:58"
      },
      ".workspace/fresh-t14": {
        "files": 107,
        "bytes": 2985005,
        "newest": "2026-10-02 13:00:40"
      }
    }
  },
  "mechanisms": {
    "zero_increment": {
      "occurred": false,
      "evidence": "warnings.log (637 B, 4 newline-terminated lines) carries 0 occurrences of Zero-increment / no_progress / no_engineering_write"
    },
    "repair_retry_used": false,
    "wrap_up_retry_used": true,
    "wrap_up_retry_reason": "artifact_missing",
    "wrap_up_note": "developer.attempt2 (25 calls, 124 s, notes empty, exit_status LimitsExceeded) is the artifact_missing wrap-up retry, not a launch-gate repair: warnings.log has 0 lines containing launch_gate_repair, and repair_retry_used=false",
    "truncation_64kib": {
      "triggered": true,
      "count": 1,
      "where": "tester.attempt1.json message 18",
      "limit_bytes": 65536,
      "original_bytes": 146150,
      "source": "extra.hoh_output_truncated parsed from the trajectory, not byte-grepped"
    },
    "editor_errors_live_after_round": {
      "count": 1,
      "line": "[MCP] capture=off (default; use --mcp-capture=on_error|every_call together with --mcp-trace=<path>)",
      "note": "a non-error banner line from the same editor pid 30348"
    },
    "role_side_live_calls": {
      "caliber_a_scope": "extra.actions[*].command inside messages[*], final unredacted trajectories",
      "commands_recorded": 344,
      "commands_containing_tools_call_running_game": 0,
      "commands_containing_tools_call_editor_play_scene": 0,
      "commands_containing_running_game_": 5,
      "game_endpoint_unavailable_occurrences": 0
    },
    "secret_redactions": 9,
    "out_of_tree_writes": [],
    "out_of_tree_cleanup_lines": 0,
    "usage_ratios": {
      "planner": 1.0,
      "developer": 1.0,
      "tester": 1.0
    },
    "usage_note": "all three roles' summary equals the sum of their attempts, and this round DOES have a planner *.redacted.json sidecar (the shape that produced the 2x in t12/t13), so ratio 1.000 is the distinguishing case T14 lacked.  Still an inference from the ratio, not an instrumented trace of DR-79 (2).",
    "tokens_total": 20641602,
    "quarantine_entries": 0,
    "battery_passes_count": 1
  },
  "count_scopes": {
    "verified_records": {
      "value": 8,
      "scope": "iter-1/evidence.json verified_records length"
    },
    "gap_records": {
      "value": 14,
      "scope": "iter-1/evidence.json gap_records length"
    },
    "execution_records_on_verified": {
      "value": 19,
      "scope": "execution_records inside verified_records"
    },
    "execution_records_on_gap": {
      "value": 11,
      "scope": "execution_records inside gap_records"
    },
    "execution_records_total": {
      "value": 30,
      "scope": "all execution_records in evidence.json"
    },
    "run_dir_files": {
      "value": 107,
      "scope": "runs/smoke-t15 before evidence/ was copied in"
    },
    "evidence_capture_files": {
      "value": 47,
      "scope": "runs/smoke-t15/evidence/{round,gatecheck,analysis}/** excluding analysis/machine_block.json -> round 22 + gatecheck 4 + analysis 21; the scripts/ subdirectory holds the runnable copies of the analysis scripts (73 files) and is counted separately so the number is stable against adding a script"
    },
    "evidence_script_files": {
      "value": 73,
      "scope": "runs/smoke-t15/evidence/scripts/**"
    },
    "evidence_manifest": {
      "path": "runs/smoke-t15/evidence/COPY_MANIFEST.txt",
      "scope": "per-file bytes and sha256 for everything in evidence/, written by evidence/scripts/copy_evidence_t15.py"
    },
    "read_only_baseline_dirs": {
      "value": 12,
      "scope": "runs/smoke-t6..t13 and .workspace/{mario,fresh-t11,fresh-t12,fresh-t13}"
    },
    "tokens_total": {
      "value": 20641602,
      "scope": "result.json.usage, equal to the console 'total tokens'"
    },
    "battery_steps": {
      "value": 12,
      "scope": "battery.json length, all ok"
    }
  },
  "stability_vs_previous_rounds": {
    "t13": {
      "exit": 0,
      "E1": "met",
      "E2": "met",
      "E3": "met",
      "E4": "met",
      "E5": "met",
      "E6": "met"
    },
    "t14": {
      "exit": 6,
      "E1": "met",
      "E2": "not_met",
      "E3": "met",
      "E4": "met",
      "E5": "met",
      "E6": "met",
      "gate": "launchable=false, reason = the editor cache-write line"
    },
    "t15": {
      "exit": 0,
      "E1": "met",
      "E2": "met",
      "E3": "not_met",
      "E4": "met",
      "E5": "met",
      "E6": "met",
      "gate": "launchable=true, reasons=[]"
    },
    "reading": "the same command sequence on this revision now opens the product's own launch gate and exits 0, which is what the previous round failed; the criterion that fails instead is E3, and for a different, product-side reason (the produced level has no floor under the jump window, so the player is in free fall and the jump verb is unobservable)."
  },
  "green_on_real_hardware": {
    "question": "does this round show the current revision green on real hardware?",
    "answer": "not fully.  Six criteria: E1/E2/E4/E5/E6 met, E3 not met.  The launch gate that failed the previous round is now green on hardware (launchable=true, reasons=[], exit 0, battery 12/12), and the redaction repair is effective on the real path, but the round still does not produce 'all six criteria met', so the dispatch objective of this stability round is only partly met.",
    "for": [
      "hoh run exits 0 on the rebuilt binary; artifact_gate launchable=true with reasons=[]",
      "battery pass 12/12 ok including editor_errors_baseline count=0 and engine_identity",
      "the DR-81 redaction repair is effective on the real path: every claimed family has raw=0 in every sidecar",
      "E1/E2/E4/E5/E6 met; the twelve read-only baselines are byte-identical byte-for-byte under the published caliber"
    ],
    "against": [
      "E3 is not met: the jump class is a monotone fall (rise=0.0, min at index 0), and QA records it as gap F2",
      "the JSON-key shape of the same HOH_* families still survives raw in the frozen sidecars",
      "the editor_errors reading is still a log-tail reading whose value changed after the round"
    ]
  },
  "unverified": [
    "why the same field returned count=0 during the battery and a [MCP] banner line live afterwards: the editor log is append-only and its tail was not instrumented",
    "whether an editor infrastructure line would have been recorded as infrastructure in this round's payload: the payload has no such line (both counts 0), so the DR-81 (1) classification is only verified by reading the code plus the binary markers, not by this round's data",
    "the mechanism behind the JSON-key disclosure shape: whether it is an intentional boundary of the assignment scan or an oversight (the repair's claim is about the assignment form only)",
    "which process/actor started PID 26716 originally: only its parent (36808, the smoke-t14 editor, now gone) and its command line are known",
    "the redactor's refusal list: result.json carries no refusal entries, so refused redactions cannot be counted"
  ],
  "risks": [
    "The launch gate's editor step is a log-tail reading: this round it read 0 during the battery and a non-error banner line afterwards, so a green gate is not evidence that the editor log is clean in principle",
    "The JSON-key environment dump reaches every frozen trajectory and its sidecar with paths, role, iteration, run id and a loopback endpoint URL; the same vector would carry a credential if one were ever put in those variables",
    "E3's jump class failed for a level-geometry reason (no floor under the jump window): the same failure can recur on any round whose produced level ends before the jump window starts",
    "The repaired assignment scan is verified here only through the shapes this round produced (up to 5 occurrences per family); a shape not present in this round (for example an assignment inside a JSON key) is untested by it",
    "The 64 KiB cap fired again on a 146150-byte payload, so any analysis trusting a role's in-context view silently loses the tail",
    "A foreign editor process held the fixed editor port and had to be terminated to satisfy the book's order; if that recurs the round must stop and report rather than point a stale editor at a new project"
  ],
  "honest_disclosure": [
    "The release binary was rebuilt from HEAD before the round; the stale predecessor (12727808 B, mtime 1790905290, sha 3b97e4a0...) predated the DR-81 commit and the build emitted a real 'Compiling hof-rs' line without any file being touched to force it.",
    "A pre-existing orphan editor (PID 26716, --path .workspace/fresh-t14, parent 36808) held port 9877 at start; I terminated it with taskkill /PID 26716 /T /F (exit 0, raw output kept) because Godot fixes the editor project at startup.  I started the round's own editor (pid 30348) afterwards.",
    "The empty-directory proof and every engine console are self-authored captures; the independent corroboration is the deterministic A0 identity, start_state=fresh and the live MCP scope probe (project_list_scripts 0 while mario has 15).",
    "The role-gate empty-dir leg ran on port 9879, not 9877, because the round's editor must stay alive at close; the role decision is taken from the engine's console line and the tools/list reply.",
    "The redaction measure first used a (?<![A-Za-z0-9_]) guard, which rejected every real occurrence in these files because an environment dump inside a JSON string is preceded by the letter n of the backslash-n escape; the script was rewritten as a scanner that accepts a preceding JSON escape and the mistake is disclosed in the artifact.",
    "runs/smoke-t15/evidence was copied into the run directory after the round closed, so runs/smoke-t15's own digest necessarily changed; the twelve read-only baselines are the ones with the three-way proof.",
    "No push was attempted; origin/master is unchanged at c4a30fa and the commit of this round carries the report only.",
    "All temporary material lives under F:\\moonbit-hof-rs-t15-staging (outside the repository); no rm -rf was used and no path was built from an unexpanded variable."
  ]
}
```

