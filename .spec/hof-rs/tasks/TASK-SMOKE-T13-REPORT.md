# TASK-SMOKE-T13-REPORT — 复现轮：逐字重跑 T12 的同一命令序列；**结果类别与全部不变量再次成立**，逐轮差异已量化

- 任务书：`.spec/hof-rs/tasks/TASK-SMOKE-T13.md`（本轮唯一任务来源；`TASK-SMOKE-T12.md` 全部条款继续有效）
- 报告人：**真机轮执行子代理（无上游对话上下文）**；落点：`F:\moonbit-hof-rs`
- **本轮新目录**：`F:\moonbit-hof-rs\.workspace\fresh-t13`（开工不存在）；轮记录 `runs/smoke-t13/**`
- 本轮命令（**恰好一轮真的跑起来**；另有一次 0.4 秒即被拒绝的启动，原因与披露见 §1.4）：
  - `target/release/hoh.exe init --project F:\moonbit-hof-rs\.workspace\fresh-t13`
  - `target/release/hoh.exe run --iterations 1 --run-id smoke-t13 --fresh-workspace --project F:\moonbit-hof-rs\.workspace\fresh-t13`
- 墙钟：`04:17:42 → 05:04:02` = **46m20s（2780.2 s）**；`ROUND_EXIT=0`；`meta.json.exit_code=0`
- 引擎：`4.8.dev.mono.custom_build.035edfce7`；binary sha256 `08483088…e9e6a`（与 T12 记录**逐字相同**）；本轮启动，收工时仍存活（pid 948）
- HEAD（开工 = 收工 = 报告前）= `8ddbad3f4db43c28be158c17ad0678fe4d77857c`；**未 push**
- 二进制：`cargo build --release --offline` exit 0，**无重编**，产物 mtime `02:45:40`、sha256 `310075fa…7158ca` 与 T12 记录逐字相同（该 sha 在 HEAD 里未变 ⇒ 非陈旧）

---

## 0. 结论摘要

| 判据 | 判定 | 一句话依据（本轮原始证据） |
|---|---|---|
| **E1** | **met（复现）** | 空目录（`ENTRY_COUNT = 0`）→ `init` exit 0 → **恰好一轮** `run` exit 0；`start_state.mode="fresh"`；`A_0=3ac25f6c…`（3 文件/1727 B）→ `A_1=a54179ce…`（13 文件/9610 B；10 新增 + `main.tscn` 342→4335 B）；三处退出码同数（`0\n`/`0\n`/`0`）；`artifact_gate={applicable:true,launchable:true,reasons:[]}`。§2.1 |
| **E2** | **met（复现）** | `editor_errors_baseline.count=0`；`editor_play_scene` `playing=true`（pid 30728, :51223）；`running_game_get_scene_tree` 返回 **28 节点**；`editor_stop_scene` `stopped=true`；`screenshot` 落盘 6240 B PNG；电池 12/12 步 `ok=true`。§2.2 |
| **E3** | **met（复现）** | 四类**全部**有游戏端点语义工具原始读数：左移 −216.330933 px、右移 +21.082520 px（**26/60 唯一**，被 `Wall` 挡住）、跳跃为纯竖直弧线（x `unique=1`、y `unique=30`）、金币 `Coins: 0 → Coins: 2`、胜利 `Goal.reached false → true`；四发 `POSITION_ASSERT_PASSED` + 两发 `running_game_assert_node_state passed=true`。§2.3 |
| **E4** | **met（复现）** | `evidence.json`：**10 verified / 13 gap**，`overlap=[]`；**31** 条执行记录（verified-only **10** / gap-only **13**）逐条 stat 存在（`MISSING=[]`），`candidate_id` 全为 `a54179ce…`；13 条 gap 各带 `player_impact`/`recommended_update`；`planner_handoff` 4/9/3。§2.4 |
| **E5** | **met（复现）** | 三棵树**逐字节同一**：`versions/a54179ce…` == `iter-1/candidate` == 活体 `.workspace/fresh-t13`（13 文件/9610 B；`only_in_*=[]`、`differing=[]`）。§2.5 |
| **E6** | **met（复现）** | `qa_report.md` 逐字 `Verdict: partial`，13 个 gap 家族被点名，并**主动拒绝**把 `input_axis` 探针当作可观测（DR-58）。§2.6 |

**本轮不可判定的判据：无。**

### 0.1 对"判据(4) 可重跑"的**明确回答**（§1.4 要求）

**成立（结果类别与全部声明的不变量都再次成立），但不是"字节复现"，也不应期望字节复现。**

- **复现了的（本轮实测）**：六条判据判定类别（t12 全 met → t13 全 met）；`start_state=fresh`；门因正确原因打开（`launchable=true, reasons=[]`）；四类行为**各有**引擎侧 `passed=true` 断言；退出码四处一致；`A_1 ≠ A_0` 且改动只落在工程文件；10 条只读基线**逐字节未变**（两种独立口径，§6）；`A_0` 逐字节相同（`3ac25f6c…`、`project.godot` sha `00d02c9c…`）。
- **没有复现、也不该期望的（本轮实测）**：`A_1` 身份与全部字节；`A_1` = `fc50ecd2…`(11 文件/7384 B) vs `a54179ce…`(13 文件/9610 B)；tokens 17,703,610 vs 15,123,294；墙钟 35m44s vs 46m20s；场景节点 22 vs 28；`move_right` 位移 +216.33 vs +21.08（t13 的关卡多了一堵 `Wall`）；gap 家族集合不同。
- **新增的"运行间翻转"（诚实披露，见 §5.3）**：t13 的**轮内游戏会话启动失败**（DR-70，`warnings.log` 逐字），t12 没有；t13 的 developer 用**修复重试**（`repair_retry_used=true`）而 t12 用 **wrap-up 重试**；`artifact_valid` t13 两次都 `true`、t12 两次都 `false`。
- **一句话**：命令是"同一条"（§1.1 并排逐字对照），**结果类别可复现**，**字节不可复现且这是设计使然**（流水线由随机性模型驱动）。

### 0.2 四类行为的原始回包摘要（§2.3 全量）

```
interaction_evidence[  0] running_game_get_node_properties  interaction:read_/root/Main/HUD/Coins_text
      {"node_path":"/root/Main/HUD/Coins","properties":{"text":"Coins: 0"},"type":"Label"}
interaction_evidence[ 24] running_game_get_node_properties  → {"text":"Coins: 2"}
interaction_evidence[ 26] running_game_assert_node_state  interaction:replay_assert_picked_up
      {"actual":"Coins: 2","expected":"Coins: 0","operator":"neq","property":"text","passed":true}
interaction_evidence[ 27] running_game_assert_node_state  interaction:replay_assert_won
      {"actual":true,"expected":false,"operator":"neq","property":"reached","passed":true}
input_replay  move_left        x 1786.76892089844 → 1570.43798828125  Δ=-216.330933  60/60 唯一
input_replay  move_right       x 1773.99353027344 → 1795.07604980469  Δ=+21.082520   26/60 唯一（被 Wall 挡）
input_replay  move_right_release x 1794.15942382812 → 1795.07604980469 Δ=+0.916626     2/10 唯一（已静止）
input_replay  jump             x 恒 1794.10217285156（unique=1）；y 279.979614257812 → min 224.257385253906 → 252.590744018555（unique=30）
```

### 0.3 三处行为/修复的真机读数（对 T12 §0 的续判）

| # | 行为 | 本轮读数 | 决定性原始证据 |
|---|---|---|---|
| **1** | 驱动前释放遗留反向动作 | ✅ **绿（复现）** | `interaction_evidence` call[4] `interaction:release_stale_move_left` → `{"event_count":1,"injected":1,"replayed":true,"speed":1.0}`，**早于**首批驱动 call[6]；随后 7 批各 **60/60 唯一 x** |
| **2** | 观测窗口早于消耗性窗口 | ✅ **绿（复现）** | 电池步骤序 6(`interaction_evidence`) < 7(`input_channel_probe`) < 8(`input_replay`)；观测窗口**自己的**读数 `Coins: 0`(call 0) → `Coins: 2`(call 24)，判定行含 `COIN_PICKED_UP`/`WIN_DRIVEN` |
| **3** | 角色自起 `editor_play_scene` 重发布路由 | ⚠️ **该分支仍未触发；但角色侧 live 游戏路由调用本轮真的发生了 5 次（4 成功 / 1 被拒）** | `tester.attempt1` **4 次** `running_game_get_node_properties` **全部 exit 0 且回包是真实节点属性**（§3.3a）；`developer.attempt2` 1 次 `running_game_get_scene_tree` 被 **DR-43** 拒绝（exit 5，回包逐字 §3.3b）；**0 次** `editor_play_scene` ⇒ DR-78 的"角色自起场景→重发布"分支本身仍未被走到 |

---

## 1. 环境引导与命令对照

### 1.1 命令并排逐字对照（t12 vs t13）

| 步骤 | T12（`TASK-SMOKE-T12-REPORT.md` 第 8–9 行逐字） | T13（本轮 `evidence/round/init.txt`、`round_console2.txt` 逐字） | 差异 |
|---|---|---|---|
| init | `target/release/hoh.exe init  --project F:\moonbit-hof-rs\.workspace\fresh-t12` | `target/release/hoh.exe init --project F:\moonbit-hof-rs\.workspace\fresh-t13` | 仅 run id/工程目录名 |
| run | `target/release/hoh.exe run --iterations 1 --run-id smoke-t12 --fresh-workspace --project F:\moonbit-hof-rs\.workspace\fresh-t12` | `target/release/hoh.exe run --iterations 1 --run-id smoke-t13 --fresh-workspace --project F:\moonbit-hof-rs\.workspace\fresh-t13` | 仅 run id/工程目录名 |
| 引擎 | `…godot.windows.editor.x86_64.mono.exe -e --path <fresh-t12> --mcp-port=9877` | `…godot.windows.editor.x86_64.mono.exe -e --path F:\moonbit-hof-rs\.workspace\fresh-t13 --mcp-port=9877` | 仅 `--path` |

> 口径说明：T12 的 init 行有**两个空格**（原文如此）；本轮为单空格。除上表列出的差异外，参数、顺序、开关**逐字相同**。两轮的引擎路径逐字相同（`--version` 同为 `4.8.dev.mono.custom_build.035edfce7`，binary sha256 同为 `08483088…e9e6a`）。

### 1.2 收紧点 1：**启动之前**的 `hoh doctor` 与端口/进程读数

**(a) `hoh doctor`（`04:10:05`，编辑器尚未启动，路由指向本轮新目录）** — 原始件 `evidence/round/preflight_doctor.txt`

```
[ok] model.chat: ... answered with model `deepseek-v4.1-flash`
[FAIL] godot.project_file: F:\moonbit-hof-rs\.workspace\fresh-t13\project.godot
[ok] godot.engine_binary: F:/moonbit-hof-rs/godot-mcp/godot/bin/godot.windows.editor.x86_64.mono.exe (size 194216960 B, mtime 1790641862)
[ok] godot.engine_version: 4.8.dev.mono.custom_build.035edfce7
[FAIL] tools.mcp: MCP transport failure to http://127.0.0.1:9877/mcp: ... (os error 10061)
EXIT_CODE: 4
```

> 与 T12 的差异（如实）：T12 那次 doctor **无 key**（`model.chat` FAIL）；本轮把 key 注入进程环境后运行，`model.chat` 为 ok，`godot.project_file` FAIL 是因为当时目录还没有 `project.godot`（`hoh init` 尚未跑）。两条 FAIL 都是**当时点的预期**。

**(b) 端口与进程（`04:10:21`，同一"启动之前"时点）** — 原始件 `evidence/round/preflight_port.txt`

```
$ netstat -ano            (exit=0)   -> lines containing ':9877' = 0  (223 行里 0 行)
$ tasklist /FI IMAGENAME eq godot.windows.editor.x86_64.mono.exe   -> INFO: No tasks are running...
⇒ 开工时 9877 无监听、无任何 godot 进程；编辑器是本轮自行启动的
```

### 1.3 引擎启动证据（**从第一秒重定向到文件**，T12A-1 的直接修补）

T12A-1 的缺陷是："报告的启动控制台输出根本不存在"。本轮的做法：启动命令**从一开始**就把 stdout+stderr 接进文件，并对两次启动都留存：

| 启动 | 命令（逐字） | pid | 控制台捕获（**文件真的存在**） | 首条 MCP 就绪行 |
|---|---|---|---|---|
| ① 门复现（空目录） | `… -e --path F:\moonbit-hof-rs\.workspace\fresh-t13 --mcp-port=9877` | 25344 | `evidence/gatecheck/game-role-console.txt` | `role=game`，`tools=73` |
| ② 本轮编辑器 | 同上（此时目录已有 `project.godot`） | 948 | `evidence/round/editor_console_launch.txt` | `role=editor`，`tools=154` |

启动 ② 的完整控制台（逐字，`evidence/round/editor_console_launch.txt`）：

```
Godot Engine v4.8.dev.mono.custom_build.035edfce7 (2026-09-29 00:01:57 UTC) - https://godotengine.org
OpenGL API 3.3.0 NVIDIA 616.56 - Compatibility - Using Device: NVIDIA - NVIDIA GeForce RTX 4090

[MCP] pending_timeout_ms=30000 (configured=30000) pending_ticks_per_frame=8
[MCP] trace=off (default; use --mcp-trace=<path> or godot_mcp/trace_file to enable)
[MCP] capture=off (default; use --mcp-capture=on_error|every_call together with --mcp-trace=<path>)
[MCP] role=editor configured_port=9877 source=cmdline listen=true
[MCP] listening on 127.0.0.1:9877 (editor=true, tools=154)
[MCP] INFO: MCP server is ready on 127.0.0.1:9877 as the editor process (port source=cmdline, tools=154)
```

进程身份与工程绑定（**反假轮证明**，`evidence/round/editor_launch_meta.txt` 与 `scope_project_list_scripts.json`）：

```
ProcessId      : 948
CommandLine    : F:\moonbit-hof-rs\godot-mcp\godot\bin\godot.windows.editor.x86_64.mono.exe -e --path F:\moonbit-hof-rs\.workspace\fresh-t13 --mcp-port=9877
ExecutablePath : F:\moonbit-hof-rs\godot-mcp\godot\bin\godot.windows.editor.x86_64.mono.exe
CreationDate   : 2026/10/2 4:12:48
$ project_list_scripts -> {"count":0,"scripts":[]}     ← 本轮新工程
  磁盘对照：.workspace/mario/scripts 有 15 个条目
```

⇒ MCP 侧看到的**就是**磁盘侧要写的那个工程；引擎在启动时固定工程、177 个工具无一能切换，故这是"不是假轮"的实测证明。

### 1.4 **本次实际发生的一次"启动被拒"（必须披露）**

我在开工时把**开工前取证**放进了 `runs/smoke-t13/evidence/**`，于是 `hoh run` 在 `04:14:36` 被立即拒绝：

```
hoh: configuration error: run directory runs\smoke-t13 already exists; pass --resume (not implemented in v1)
EXIT_CODE: 2   ELAPSED_SECONDS: 0.412
```

→ **没有角色运行、没有写任何工程字节**；我把取证搬出仓外（`F:\moonbit-hof-rs-t13-staging`，用 `os.rename`/`copytree`，**全程未用 `rm -rf`**），随后 `04:17:42` 起**恰好跑了一轮**（全程 `04:17:42 → 05:04:02`）。证据：`evidence/round/round_console.txt`（被拒的这次）与 `evidence/round/round_console2.txt`（真的那次）。

**"恰好一轮"的可复算证据**：`versions/index.json` 只有 2 条（`iteration 0 role=init`、`iteration 1 role=developer`）；`iter-1/` 只有一个迭代目录；`result.json.attempts` 只有 4 条（planner×1、developer×2、tester×1），其中 developer 的 2 条是**同一次迭代内的两条 attempt**，不是两轮。

### 1.5 二进制

```
$ cargo build --release --offline        Finished `release` profile in 0.68s   BUILD_EXIT=0
$ stat  target/release/hoh.exe           size=12713984 mtime=2026-10-02 02:45:40
$ sha256sum target/release/hoh.exe       310075faea14317af48a9602f7baedb1fc1e0d2af8bb4a057f3f00cb4f7158ca
```

**无重编**（cargo 无 `Compiling` 行）：现有二进制的 sha256 与 mtime 与 T12 记录**逐字相同**，而 HEAD(`8ddbad3f`, `04:08:30`) 相对 T12 轮内 HEAD(`47680397`) 只改了 3 个文档文件（`.spec/hof-rs/tasks/TASK-SMOKE-T12-{REPORT,ACCEPTANCE}.md`、`TASK-SMOKE-T13.md`）⇒ 二进制**非陈旧**。**本轮未改任何 `src/**`**（`git status` 可证）。

### 1.6 role 门的**独立复现**（任务书 §1.6 新增条款）

复现方法：在**可证为空**的目录上启动引擎，并把控制台从第一秒接进文件。

```
LAUNCH_CMD: …godot.windows.editor.x86_64.mono.exe -e --path F:\moonbit-hof-rs\.workspace\fresh-t13 --mcp-port=9877
path_dir_entries: []            path_dir_project_godot_exists: False
pid: 25344                      CreationDate: 2026/10/2 4:10:41
[MCP] role=game configured_port=9877 source=cmdline listen=true
[MCP] listening on 127.0.0.1:9877 (editor=false, tools=73)
[MCP] INFO: MCP server is ready on 127.0.0.1:9877 as the game process (port source=cmdline, tools=73)
netstat: TCP 127.0.0.1:9877 LISTENING 25344
```

**实测的工具集（本轮直接向该端点发 `tools/list`，原始回包 `evidence/gatecheck/game-role-tools_list.json`）**：

```
served_total = 73      duplicate_served_names = []
served_by_prefix = {"project_": 48, "running_": 23, "os_": 2}
契约 177 名（godot-mcp/godot/modules/mcp_server/docs/tools_list.renamed.json）：
  {"editor_": 104, "project_": 48, "running_": 23, "os_": 2}
SERVED BUT NOT IN CONTRACT = 0
IN CONTRACT BUT NOT SERVED = 104   not_served_by_prefix = {"editor_": 104}
editor_* served = 0 / 104          running_game_* served = 23 / 23
editor_play_scene served = False   running_game_get_scene_tree served = True
```

同一端点上 `editor_status` 被引擎**拒绝**（`{"error":{"code":-32601,"message":"Method not found: editor_status"}}`，`evidence/gatecheck/game-role-editor_status.json`）。

**对照（唯一被翻转的变量是目录内容）**：同一二进制（sha256 `08483088…`）在**已有 `project.godot`** 的同一目录上启动 → `role=editor`、`tools=154`（`{"editor_":104,"project_":48,"os_":2}`、`running_game_* served = 0`、`editor_play_scene served = True`；`evidence/round/editor_tools_list.json`、`evidence/analysis/tool_census_editor_role.txt`）。

⇒ **本轮独立复现了 T12 的发现**，且这次**两侧都带自己的启动控制台 / cmdline / pid**（T12A-2 的"A 侧无原始件"由此闭合）。**顺序必须**是"先建空目录 → `hoh init` → 再由编辑器指向它"。

---

## 2. E1..E6 逐条判定 + 原始证据

### 2.0 "空目录 → init → run" 三步原始输出

**(a) 目录为空**（`evidence/round/empty_proof.txt`；先证明**不存在**，再 `mkdir`，再证明 `ENTRY_COUNT = 0`）

```
$ cmd /c dir /a F:\moonbit-hof-rs\.workspace\fresh-t13      -> exit=1  "File Not Found"
$ cmd /c mkdir  F:\moonbit-hof-rs\.workspace\fresh-t13      -> exit=0
$ dir /a …                                                   -> 0 File(s) 0 bytes   (仅 . 与 ..)
os.listdir(...) -> []       ENTRY_COUNT = 0      递归遍历 = 0 条目
```

**(b) `hoh init`（`evidence/round/init.txt`）**

```
init: A0 ready at F:\moonbit-hof-rs\.workspace\fresh-t13 (initialize ran; no MCP, no model endpoint and no key were required)
EXIT_CODE: 0
```

`A_0` 树（`evidence/round/init_tree.txt`）：`project.godot` / `scenes/main.tscn` / `scripts/README.md` = 3 文件 / 1727 B；`project.godot` sha256 `00d02c9c…c0ef4` **与 T12/T11 的 A₀ 逐字相同**（确定性脚手架，不是手写）。

**(c) `start_state`**：`{"mode": "fresh", "version_id": null}`（`meta.json`；**不是 `as_is`**）。

### 2.1 E1 = met

| 要件 | 本轮原始证据 |
|---|---|
| Planner 产出合法 `D_1` | `iter-1/plan.md`（2448 B，含 `### Priority Order` / `### Preservation Gate` / `### Acceptance Gate`）；`logs/planner.attempt1.log`：`exit_status=RepeatedFormatError`、`artifact_valid=true`、27 calls |
| Developer 产出**真实工程增量** | `versions/index.json`：`3ac25f6c…`(iter 0, role init) → `a54179ce…`(iter 1, role developer)；`result.json.evidence_diff` 与我的独立 diff **逐条一致** |
| QA 产出合法 `E_1` | `iter-1/evidence.json`（21656 B，可解析）；`logs/tester.attempt1.log`：`Submitted`、`artifact_valid=true`、105 calls |
| 整轮 + 退出码 | `runs/smoke-t13/exit_code` 字节 `30 0A`；`meta.json.exit_code=0`；`runs/smoke-t13/process_exit_code` 字节 `30 0A`；wrapper `ROUND_EXIT=0`；`result.json`：`ok=true, failed_role=null, reason="ok", issues=[]` |

**退出码语义**（比 T12 更精确）：`exit_code=0` 由 `cli_impl::run_exit_code` 计算 ⇒ "循环跑完**且**冻结产物可用"（若 `launchable=false` 会是 6，若失败会是其错误类）。本轮 `artifact_gate={applicable:true,launchable:true,reasons:[]}`。

**`A_0`/`A_1` 摘要（运行时口径；我用独立实现复算，两个 id 都逐字命中）**：

```
A0  3ac25f6c5c38885febd3a001ea99c88aca61b1799c7b105306919886c2c1d151    3 files   1727 B   recomputed MATCH=True
A1  a54179ceb11b9fb6477f66b05c6e0f9ced812423eee5d4b000fa9f0a680edfc4   13 files   9610 B   recomputed MATCH=True
```

**被改文件清单（我独立 diff，`evidence/analysis/a0a1_diff.txt`）**：

```
ADDED (10): scripts/{coin,enemy,goal,main,player}.gd + 各自 .gd.uid
MODIFIED (1): scenes/main.tscn   342 B -> 4335 B
REMOVED (0)
```

`result.json.evidence_diff` = 同一份 10 新增 + 1 修改 + 0 删除 ⇒ **逐条一致**。

**非琐碎**：developer 从只有 `README.md` 的 `scripts/` 起手，写出 5 个脚本 + `Coin1/Coin2/Goal/Enemy1/HUD/Wall` 的 **28 节点**场景。

**⚠️ 本轮 E1 的真实形态（必须点名，不改判定）**：developer **两次 attempt 都 `LimitsExceeded`**，但**两次 `artifact_valid=true`**，`wrap_up_retry_used=false`、`repair_retry_used=true`，且 **attempt2 是"启动门修复重试"**而不是 wrap-up（`logs/developer.attempt2.log` 的 `notes` = `launch_gate_repair: the pre-freeze launchable gate failed`）。这**与 T10/T12 的形态不同**（那两轮 `artifact_valid=false` + wrap-up 重试）。机制审读见 §5.1。

### 2.2 E2 = met

```
editor_errors_baseline : {"available":true,"count":0,"editor":true,"errors":[],"in_process":true,"pid":948,"port":9877,"process":"editor","source":"editor_log"}
play_scene_ready       : {"args_injected":["--mcp-port=51223"],"endpoint":"http://127.0.0.1:51223/mcp","mode":"main","pid":30728,"playing":true}
                         + running_game_get_scene_tree -> 28 typed nodes
screenshot             : .hoh/evidence/frame-00.png (6240 byte(s))
battery                : 12 steps, all ok=true
editor_stop_scene      : {"message":"Playback stopped","stopped":true}
artifact_gate          : meta.json 与 result.json 两处 {"applicable":true,"launchable":true,"reasons":[]}
```

（`evidence/analysis/battery_reads.txt` 逐字。）⚠️ 但 `play_scene_ready` 的 `after 1 poll(s)` 是**电池 pass 2** 的读数；**pass 1 与轮内会话启动都想同一条路失败了**，见 §3.3 / §5。

### 2.3 E3 = met（四类全部成立，**复现**）

| 行为 | 裁定 | 决定性原始证据（全部来自**游戏进程端点**的语义工具） |
|---|---|---|
| 左移 | **成立** | `input_replay`：x `1786.76892089844 → 1570.43798828125`，Δ=**−216.330933**（60 帧，**60/60 唯一 x**）；`move_left: POSITION_ASSERT_PASSED` |
| 右移 | **成立** | `input_replay`：x `1773.99353027344 → 1795.07604980469`，Δ=**+21.082520**（60 帧，**26/60 唯一**）；`move_right: POSITION_ASSERT_PASSED`。**位移小是关卡造成的**：`Wall` 在 x=1900，玩家在 1795 处被挡（`input_replay` 判定行逐字含 `F6 wall blocking` 未被触及，Q/A 记为 gap） |
| 跳跃 | **成立** | `input_replay`：x **恒为** `1794.10217285156`（`unique=1`）、y `279.979614257812 → min 224.257385253906 → 252.590744018555`（`unique=30`）⇒ **纯竖直弧线**；`jump: POSITION_ASSERT_PASSED` |
| **至少 1 个可交互对象** | **成立** | `interaction_evidence` 的 `running_game_get_node_properties`：`Coins: 0`(call 0) → `Coins: 2`(call 24)；引擎自己的 `running_game_assert_node_state`（`text:neq "Coins: 0"`，actual `"Coins: 2"`）`passed=true`；判定行 `COIN_PICKED_UP` |
| **一个终点/胜负条件** | **成立** | `Goal.reached`：`false`(call 1/10/16) → **`true`**；`running_game_assert_node_state`（`reached:neq false`，actual `true`）`passed=true`；判定行 `WIN_DRIVEN`；`player max x=1667.66174316406` 越过 `goal.position.x=1500.0`，`coverage_shortfall_px=Some(-167.66174316406)`（**负值**） |

**"金币跃迁来自语义工具原始回包"（不得推断）**——逐字：

```
[  0] running_game_get_node_properties  interaction:read_/root/Main/HUD/Coins_text
      {"node_path":"/root/Main/HUD/Coins","properties":{"text":"Coins: 0"},"type":"Label"}
[ 24] running_game_get_node_properties  interaction:read_/root/Main/HUD/Coins_text
      {"node_path":"/root/Main/HUD/Coins","properties":{"text":"Coins: 2"},"type":"Label"}
[ 26] running_game_assert_node_state    interaction:replay_assert_picked_up
      {"actual":"Coins: 2","expected":"Coins: 0","operator":"neq","property":"text","passed":true,"resolved_node_path":"/root/Main/HUD/Coins"}
[ 27] running_game_assert_node_state    interaction:replay_assert_won
      {"actual":true,"expected":false,"operator":"neq","property":"reached","passed":true,"resolved_node_path":"/root/Main/Goal"}
```

**诚实的边界**：计数器是 **`0 → 2`**（两枚 `Coin1`/`Coin2` 被同一次驱动扫过）；判据要的是"至少 1 个可交互对象"+"跃迁在轮内被观测到"，**本读数满足**；"恰好 1 枚"不是本轮读数。`input_axis` 探针仍然 `null`（`running_game_run_test_scenario` 的 `input_axis` 断言报 `node '/root/Main/Player' does not have the property 'input_axis'`）——E3 的依据是**位置采样 + 引擎断言**，不是探针。

### 2.4 E4 = met（我自己逐条 stat）

```
iteration=1  qa_status=partial  verified=10  gap=13
verified_ids = [F1, F2, F3, F5, F10, F13, F16, N1, N2, N3]
gap_ids      = [F2b, F4, F6, F7, F8, F9, F11, F12, F13b, F14, F15, F17, N3b]
overlap: []        dup ids: []
execution_records: verified-only=10, gap-only=13, verified+gap=31   ← 作用域分别写清
MISSING=[]         record types {replay:11, runtime_trace:10, build:5, assert:3, screenshot:2}
record candidate_ids = {a54179ce…: 31}（单一）
gaps lacking player_impact: []     gaps lacking recommended_update: []
planner_handoff: preservation_constraints=4 / update_targets=9 / validation_requirements=3
```

**相对 T12 的判据侧变化（诚实读数）**：`F1`(移动) 回 verified；`F10`(金币)/`F13`(胜利) 继续 verified；**新增 gap 家族 `F2b`（跳跃可重复性）`F13b`（可见胜利结果）`N3b`（60 s 稳定性）**，而 T12 的 `F1-stop` 不复现（T13 的 `move_right_release` 10 帧里 x 只变 0.9166 px，接近静止，Q/A 未把它列为 gap——**这是两次采样窗口长度不同造成的判定差异，如实记录**）。

### 2.5 E5 = met（三棵树逐字节同一）

```
versions/a54179ce…   13 files / 9610 bytes
iter-1/candidate     13 files / 9610 bytes
live .workspace/fresh-t13  13 files / 9610 bytes
only_in_first=[]  only_in_second=[]  differing=[]   ALL_IDENTICAL = True
（三者的 runtime-scheme id 均为 a54179ce…，由我独立实现复算）
result.json.candidate_id == version_id == a54179ce…
```

⇒ **QA 未修改 `A_1`**。

### 2.6 E6 = met

`qa_report.md`（2114 B）逐字含：

```
Verdict: partial
- F2b jump repeatability (only one 30-frame window; no landing + second jump).
- F4 camera follow (no traversal long enough to observe the viewport).
- F6 wall blocking (longest run stops at x=1769.4; Wall at x=1900 never touched).
- F7/F8/F9 enemy patrol, contact damage, stomp (Enemy1 never observed moving or touched).
- F11/F12 question block and breakable brick (no such nodes exist).
- F13b visible victory result (Result label never read after the win).
- F14/F15 failure flow and restart reset (no observable failure path).
- F17 level length/pacing (no timed complete clear).
- N3b 60-second stability (only a load-time error check exists).
- input_axis is not a real observable (DR-58); assert on positions/properties.
- Enemy contact and the Wall were never reached, so danger and blocking remain unproven rather than proven absent.
```

⇒ 未达成被**逐条声明**，且**主动拒绝把弱观测当结论**（`input_axis` 探针被自己标注为不可用）；未谎报为 verified。与 `evidence.json` 的 10/13 划分**逐条一致**。

---

## 3. 三处行为/修复的真机读数

### 3.1 ① 驱动前释放遗留反向动作 —— **绿（复现）**

```
[  4] running_game_play_input_recording  interaction:release_stale_move_left   ok=True
      {"event_count":1,"injected":1,"replayed":true,"speed":1.0}
[  5] running_game_create_input_recording interaction:batch1:create_input_recording
[  6] running_game_play_input_recording   interaction:batch1:play_input_recording
[  9] running_game_get_node_property_samples interaction:batch1  n_samples=60  x: 87.3333282470703 → 303.666656494141  unique=60
[ 15] … batch2  x 314.666625976562 → 530.99951171875  unique=60
[ 21] … batch3  x 541.999572753906 → 758.334106445312 unique=60
[ 27] … batch4  x 769.334167480469 → 985.668701171875 unique=60
[ 33] … batch5  x 996.668762207031 → 1213.00012207031 unique=60
[ 39] … batch6  x 1224.0 → 1440.33093261719 unique=60
[ 45] … batch7  x 1451.33081054688 → 1667.66174316406 unique=60
```

⇒ 释放（call[4]）**早于**首批驱动（call[6]），且 7 批**各 60/60 唯一 x**、每帧约 +3.6667 px（= 220 px/s，与 `player.gd` 的 `speed` 自洽）。T11 的失败形态（180 个 x 全部逐位相同）**本轮不复现**。

### 3.2 ② 观测窗口早于所有消耗性窗口 —— **绿（复现）**

```
电池步骤序（battery.json，逐字）：
[ 0] project_reload_and_open  [ 1] scene_structure  [ 2] editor_errors_baseline
[ 3] play_scene_ready         [ 4] scene_tree       [ 5] screenshot
[ 6] interaction_evidence     ← 观测窗口
[ 7] input_channel_probe      ← 消耗性
[ 8] input_replay             ← 消耗性
[ 9] node_and_collision_assertions  [10] editor_stop_scene  [11] engine_identity
```

观测窗口**自己的**判定行（逐字）：

```
interaction: before readings coin=Some("Coins: 0") goal.reached=Some(Bool(false)) goal.position=Some(Object {"x": Number(1500.0), "y": Number(286.0)});
interaction: drove `move_right` for 7 of 130 batch(es) (60 frame(s) each, 7800 frames budgeted), player max x=Some(1667.66174316406), coverage_shortfall_px=Some(-167.66174316406), stopped as soon as the win was observed;
interaction: coin counter `/root/Main/HUD/Coins` Coins: 0 -> Coins: 2;
interaction: COIN_PICKED_UP (the counter grew 0 -> 2; `text:neq "Coins: 0"` accepted in the game process);
interaction: WIN_DRIVEN (goal.reached false -> true while the player drove right; `reached:neq false` accepted in the game process)
```

⇒ T11 的结构性假阴性（首个读数就已是 `Coins: 1`）**不复现**：本轮首个读数是 `Coins: 0`。

### 3.3 ③ 角色自起场景 / 角色侧 live 路由 —— **本轮首次拿到角色侧 live 游戏路由的原始回包：4 次成功、1 次被拒**

**(a) Tester 的 4 次 live 调用（全部成功，exit 0）** — 原始件 `evidence/analysis/tester_running_game_invocations.txt`

```
tester.attempt1 消息 151（一次派发里的两条命令，同一 tool_call 组）：
  cd /d F:\moonbit-hof-rs & python -c "…写入 a1.json（{'node_path':'HUD/Result','properties':['text']}）" &
      "%HOH_HOH_BIN%" tools call running_game_get_node_properties --args-file runs/smoke-t13/iter-1/candidate/.hoh/scratch/a1.json 2>&1 | more +0
  → 消息 152，returncode=0，原始回包：
    {"node_path":"/root/Main/HUD/Result","properties":{"text":""},"type":"Label"}

  cd /d F:\moonbit-hof-rs & python -c "…写入 a2.json（{'node_path':'Player','properties':['position','facing','velocity']}）" &
      "%HOH_HOH_BIN%" tools call running_game_get_node_properties --args-file runs/smoke-t13/iter-1/candidate/.hoh/scratch/a2.json 2>&1 | more +0
  → 消息 153，returncode=0，原始回包：
    {"node_path":"/root/Main/Player","properties":{"facing":1,"position":{"x":80.0,"y":293.998992919922},
     "velocity":{"x":0.0,"y":0.0}},"type":"CharacterBody2D"}

tester.attempt1 消息 154（两条命令）→ 消息 155，returncode=0

合计：Tester 的 running_game_* 调用 = 4，成功 = 4，被拒 = 0
```

⇒ **DR-69 的"角色侧 live CLI 采纳运行期发布的路由"这一条，本轮第一次被真机证明成立**（此前 T11 三次被拒、T12 零次调用）。这也是对 T12A / F-T12-1 的**正面回答**：角色 live 游戏路由**可以**工作——**前提是调用发生在运行期自己的游戏会话成功启动之后**（Tester 在电池 pass 2 之后跑，见 §3.3c）。

**(b) Developer 的 1 次 live 调用（被 DR-43 明确拒绝）** — developer attempt2，消息 137→139

```
命令（逐字）：
  cd /d F:\moonbit-hof-rs && echo {} > .tmp_probe.json && "%HOH_HOH_BIN%" tools call running_game_get_scene_tree --args-file .tmp_probe.json 2>&1

回包（逐字，returncode=5）：
  hoh: game_endpoint_unavailable: `running_game_get_scene_tree` runs in the game process and only the game
  endpoint serves it; no game endpoint is registered yet (`editor_play_scene` must have answered with
  `endpoint` or `mcp_port`). Falling back to the editor endpoint is not allowed (DR-43).
```

**(c) 普查（作用域写清，可复算）** — `evidence/analysis/game_route_calls.txt`、`called_tools_census.txt`、`recount_tools.txt`

```
corpus = runs/smoke-t13/iter-1/traj/*.json 的 extra.actions[*].command（排除 *.redacted.json；**最终工件**）
planner.attempt1     executed_commands= 29   tools_call= 0   running_game_*=0   editor_play_scene=0
developer.attempt1   executed_commands=187   tools_call=23   running_game_*=0   editor_play_scene=0
developer.attempt2   executed_commands= 98   tools_call=47   running_game_*=1   editor_play_scene=0
tester.attempt1      executed_commands=134   tools_call= 8   running_game_*=4   editor_play_scene=0
TOTAL                executed_commands=448   tools_call=78   running_game_*=5（4 成功 / 1 被拒）   editor_play_scene=0
探测器负控：合成的 `tools call running_game_get_scene_tree` / `editor_play_scene` 都能命中；
            而"分析命令里仅仅出现 running_game_ 字样"不命中（`recount_tools.py` 逐条列出）
```

**(d) 为什么两者命运不同（本轮最重要的机制读数）** — `warnings.log` 逐字：

```
DR-70: the round's game session could not be started (the round's game did not answer
`running_game_get_scene_tree` after 3 poll(s): … the endpoint http://127.0.0.1:55361/mcp was marked
unavailable after 2 consecutive transport failures; no request was sent and no retry was made …
endpoint_state={"endpoint":"http://127.0.0.1:55361/mcp","state":"unavailable","unavailable":true,
"consecutive_transport_failures":2,"transport_failures_at_mark":2} …); the game route stays withdrawn
until the battery starts its own game, so every `running_game_*` call from a role shell fails with
`game_endpoint_unavailable` (DR-43) for this window
```

时间线（epoch 换算见 `evidence/analysis/epochs.txt`）：

| 时刻 | 事件 |
|---|---|
| 04:17:44 | `start_round_game`：`editor_play_scene` 应答端点 `:55361`，随即 3 次轮询全部失败 ⇒ **路由被撤回**（DR-70） |
| 04:18 | Planner 运行（角色 shell 有 `HOH_GAME_ROUTE`，但**没有路由可采纳**） |
| 04:19–04:41 | Developer attempt1 运行（`running_game_*=0`） |
| 04:31:28 | **Developer 的 live `running_game_get_scene_tree` → exit 5（DR-43 明确拒绝）** |
| 04:41:30 / 04:41:37 | 电池 pass 1：`:55336` 两次传输失败（连接被拒） |
| 04:41:38 | 端点被标记 unavailable（`ENDPOINT_DEATH_THRESHOLD=2`），pass 1 的 `play_scene_ready.ok=false` |
| 04:41 | pass 1 门失败 ⇒ **修复重试**（developer attempt2） |
| 04:54:38 | 电池 pass 2 替换 pass 1（pass 1 原始件进 `quarantine/`） |
| 04:54:51 | pass 2：`:51223` **1 poll** 就绪 ⇒ **路由发布**、`A_1` 冻结（`created_at=1790888091`） |
| ≈05:00–05:02 | **Tester 的 4 次 `running_game_get_node_properties` 全部成功**（路由由运行期发布且可用） |
| 05:04:02 | 轮结束；`game_endpoint.json` 被撤回（收工时不存在） |

⇒ **"角色发过 live 游戏路由调用"这条本轮做到了，而且拿到了两种命运**；**但 DR-78 的"角色自起 `editor_play_scene` → 重发布"分支仍未被走到**（0 次），因为 **developer 提示词明确禁止角色自起场景**（`src/prompts/developer.md:112-113`、`:142-143`：`do not start a game of your own (editor_play_scene)`），而 Tester 的提示词把"自己采集"降为次要（`src/prompts/tester.md:7-18`）。**Tester 走了 DR-69 的采纳路径**（它照 `TOOLS.md` 里的 `running_game_*` 工具直接调用），**没有**走 DR-78 的发布路径。

---

## 4. "送达了输入"与"真的移动了"的对照（§1.4 要求，同一候选）

| 窗口 | 送达事实（`injected=1`/`replayed=true`） | 移动事实（真实采样） |
|---|---|---|
| `interaction_evidence` batch1..batch7 | 有（call 6/12/18/24/30/36/42） | 每批 60/60 唯一 x，7 批合计 `87.333… → 1667.662…` |
| `interaction:release_stale_move_left` | 有（call 4） | （释放动作） |
| `input_channel_probe` move_right | 有 | x `1685.99487304688 → 1769.41040039062`（30/30 唯一） |
| `input_replay` move_right | 有（call 3） | Δ+21.082520，**26/60 唯一**（被 Wall 挡） |
| `input_replay` move_right_release | 有（call 15） | Δ+0.916626，**2/10 唯一**（已静止） |
| `input_replay` jump | 有（call 27） | x 唯一 1、y 唯一 30（竖直弧线） |
| `input_replay` move_left | 有（call 39） | Δ−216.330933，60/60 唯一 |

**反例/边界（不许把送达当移动）**：
- `interaction_evidence` 每批的 `running_game_run_test_scenario` 回包是 `"all_passed": false, "failed": 1`，原因是 `input_axis` 断言 `node '/root/Main/Player' does not have the property 'input_axis'` —— **该探针读不到轴，但这与"玩家有没有动"无关**：同批的位置采样证明玩家在动。这正是 E3 要求"在游戏进程内、用语义工具、看行为"的原因。
- `move_right` 的 **26/60 唯一**说明"送达 ≠ 位移量"：位移量由关卡（墙）决定，不由注入是否成功决定。

---

## 5. 归因与两项指定调查（含反例检验）

### 5.1 调查 A：developer 两次触限、`artifact_valid=true`、修复重试——**不是 T10/T12 形态的复发**

**实测**：`result.json.attempts` = dev attempt1（150 calls，`LimitsExceeded`，`artifact_valid=true`）、dev attempt2（60 calls，`LimitsExceeded`，`artifact_valid=true`）；`wrap_up_retry_used=false`、`wrap_up_retry_reason="not_triggered"`、`repair_retry_used=true`。

**attempt2 到底是什么**（源码 + 日志双重证据）：
- `logs/developer.attempt2.log` 的 `notes` = `launch_gate_repair: the pre-freeze launchable gate failed`；
- `src/runtime/run_loop.rs:1342-1400`：只有当 **电池 pass 1 的 `launch_gate` 失败**时才发起"一次定向修复"，trajectory 名就是 `developer.attempt{n+1}`。
- ⇒ 本轮的 attempt2 **是修复重试**，不是 wrap-up。

**为什么 `artifact_valid=true`**（源码）：`src/adapter/godot.rs:306 developer_artifact_valid_in` 判的是"主场景存在、能解析（`validate_scene_structure_in`）、至少引用一个脚本资源、且每个被引用脚本文件存在且非空"。T13 的 `main.tscn` 在 attempt1 结束时**已满足**全部条件 ⇒ `true`。这也解释了**为什么没有 wrap-up 重试**（`run_loop.rs:1154` 的条件是 `developer_limits && !developer_artifact_valid`）。

**是否是"应该的行为"**：
- 该标志的**语义**与文档一致（"项目可用吗"，不是"这次尝试成功了吗"）；
- **但** attempt2 的 `artifact_valid` 用的是**attempt1 结束时**算出来的值（`run_loop.rs:1137` 只算一次，`1185` 直接复用），修复调用之后**没有重新判定** ⇒ 一行 `artifact_valid` 同时代表两条不同的尝试，**这是测量口径的松动**（`repair` 把项目改坏了也会显示 `true`）。
- **判定**：`artifact_valid=true` **本轮实测为真**、因果已定位到源码；与 T10/T12 的 `false` 形态**不同**（因为那两轮 attempt1 结束时场景不满足结构/脚本条件）。**本轮不修**（任务书 §1.4 明确：除非本轮本身需要，不修流水线）。

### 5.2 调查 B：planner 的 usage 恰好是单次 attempt 的 2 倍——**确认为真，机制已定位（且 T12 同样中招）**

**实测算术**（`evidence/analysis/usage_cmp.txt`、`token_totals.txt`）：

```
planner  attempt: calls 27  total 272,378
planner  summary: calls 54  total 544,756   ← 恰为 2 倍
runtime summary 总计 = 15,123,294            (控制台打印同值)
attempts 求和        = 14,850,916
差额 = 272,378 = planner attempt 一次的量   ← 被算了两次
```

**机制（源码 + 复算，不是猜）**：`src/runtime/usage.rs:130`

```rust
if name.starts_with(&format!("{}.attempt", role.as_str())) && name.ends_with(".json") {
    paths.push(entry.path());
}
```

而 `runs/smoke-t13/iter-1/traj/` 里同时存在 `planner.attempt1.json` **和** `planner.attempt1.redacted.json`（DR-72 ② 的"冻结证据旁路副本"），二者都匹配该过滤条件；redacted 副本**保留了同样的 `extra.response.usage`**，于是被**合并两次**。

**反例/复算检验**：我用与运行时相同的 `extract_usage` + `merge_usage` 逻辑，只对"它的过滤器实际匹配到的文件"求和：

```
过滤到的文件（2 个）：['planner.attempt1.json', 'planner.attempt1.redacted.json']
  planner.attempt1.json            calls=27 total=272378
  planner.attempt1.redacted.json   calls=27 total=272378
MERGED calls=54 total=544756        ← 与运行时 summary 逐字相等
```

（`evidence/analysis/usage_attribution_t13.txt`；同法对 T12 复算见 `evidence/analysis/usage_attribution_t12.txt`。⇒ **不是"两次模型调用"导致**：如果真是两次调用，轨迹里会有两次不同 usage；这里是**同一份 usage 被读了两遍**。）

**历史**：T10 planner ratio=1.000、T11 planner ratio=1.000、**T12 planner ratio=2.000**（summary 90 calls/901,668 vs attempt 45/450,834）、**T13 planner ratio=2.000**。⇒ **T12A-5 说这是"本轮新异常"不完全对**：T12 已经中招，只是 T12 报告没查；T10/T11 干净是因为它们的 `traj/` 目录里当时**没有**该类旁路副本（T10 一个都没有；T11 只有 developer 的，而 developer 的 summary 走的是"合并 attempt usage"的另一条路径）。

**作用域**：任何"该角色在 summary 生成之前已有 `.redacted` 旁路副本"的轮次，其**轮级 token 数**会被抬高**恰好一次该角色尝试**的量；**逐 attempt 的行是准确的**。**本轮不修**（仅调查，任务书 §1.4）。

### 5.3 机制归因表（"我们没看到 X" ≠ "X 不可能"）

| # | 主张 | 支持读数 | **反例检验** | 性质 |
|---|---|---|---|---|
| C-A | 空 `--path`（无 `project.godot`）⇒ `role=game`/73 工具；`init` 后同一二进制 ⇒ `role=editor`/154 | 两侧各自的启动控制台 + cmdline + pid + 工具集普查 | **同一二进制（sha256 逐字相同）、同一端口、同一目录，只翻转"目录里有没有 project.godot"** ⇒ 排除换二进制与端口参数混淆 | **实测（A/B 对照，两侧都有原始件）** |
| C-B | E3 的"金币跃迁"是引擎侧观测，不是推断 | `running_game_get_node_properties` 原始回包 + `running_game_assert_node_state passed=true` | 编辑器端点**不提供** `running_game_*`（154 工具中 0 个）⇒ 该回包不可能来自编辑器端点 | **实测** |
| C-C | 本轮 developer 的 live 调用被拒是**因为当时没有路由**，不是因为"路由陈旧" | 角色 shell 的 env dump 逐字给出 `HOH_GAME_ROUTE=F:\moonbit-hof-rs\runs\smoke-t13\game_endpoint.json`（变量确实在）；`warnings.log` 的 DR-70 逐字说路由被撤回、"every running_game_* call from a role shell fails for this window"；回包文本是"no game endpoint is registered yet"（而非 `Expired`/`OwnerGone`/`Unreachable`） | **反例**：若路由文件当时存在且可采纳，回包会是其它形态或直接成功。我**没有**在同一时刻读过磁盘上是否存在该文件（运行时已把文件撤回），所以"文件不存在"这一点来自**运行时的自述 + 回包形态**，不是我的直接 stat；**我把它标为"强推断（证据一致）"而不是"实测"** | **实测（调用与回包）+ 强推断（文件当时不在）** |
| C-D | "0 次拒绝"或"1 次拒绝"能说明角色侧 live CLI 的状态 | Tester 的 4 次调用**全部成功**（同一轮、同一 `HOH_HOH_BIN`、同一 `HOH_GAME_ROUTE` 机制） | **反例成立**：同一轮里 Developer 的 1 次被拒、Tester 的 4 次成功 ⇒ **"被拒"与"可用"都不是 CLI 的属性，而是"调用时刻有没有可用路由"的属性**。T12 的"0 次拒绝"因此**什么都证明不了**（它 0 次调用），而本轮的"4 成功 + 1 被拒"才是这条通道的真机证据 | **实测（两侧原始回包）** |
| C-E | 轮内会话启动失败与电池 pass 1 失败是**同一原因** | pass 1 的 `mcp-errors.jsonl` 两次"connection refused"、pass 2 一次成功（同一二进制、同一编辑器、同一项目） | **不能证"必然"**：我没有对游戏进程的启动/绑定时刻做仪器化，也没有测 ready 超时与轮询间隔。**"三次里两次失败"只是读数，不能推断"每次都会失败"** | **实测现象 + 因果未定** |
| C-F | planner usage 2 倍是"两次调用" | —— | **反例成立**：用运行时的过滤器复算，两个文件承载**同一份** usage；若真是两次调用，两文件 usage 不会逐字相同 | **实测（算术 + 过滤复算）** |

---

## 6. 只读基线的未变证明（三口径 + 双独立口径）

**口径 A（内容）**：`Get-ChildItem -Recurse -Force -File`；仓根相对小写 POSIX 路径 + TAB + 字节 + TAB + sha256；LF 连接、无尾随换行；`Sort-Object` 文化序；整体 UTF-8 取 SHA-256。脚本 `evidence/scripts/baseline_digest_repo.ps1`（可复跑），输出 `evidence/round/baseline_{before,after}_repo.txt`、`baseline_after_evidence.txt`。

**口径标定（承重的一步）**：同一口径**逐字复现了 T12 公布的 8 个摘要**（含任务书点名的 `runs/smoke-t6 = 135 文件 / c144ef32…7a9c03`）⇒ 不是我另造了口径。**8/8 命中**（`evidence/analysis/anchor_check.txt`）。标定过程中我先用"子树相对路径"算，**8 个全不命中**；改成"仓根相对路径"后 8/8 命中 ⇒ **路径前缀是承重的**，如实记录。

```
=== BEFORE 04:11 / AFTER 05:04 / AFTER_EVIDENCE 05:1x —— 三次逐字相同 ===
.workspace/mario     178  dee0a36f357c440d078c652d4d4b8990af1a63b88d282c1e36c04a16d006cc94  2026-09-30 18:23:08
runs/smoke-t6        135  c144ef3219e21dd322978e41a5531d53dee270619c026585505920f9277a9c03  2026-09-29 02:32:01
runs/smoke-t7        115  6e4c1595753c2cdefb16e4d2e5f05242ca202c70c81a93e98ae2b9c92b520fb7  2026-09-29 14:41:14
runs/smoke-t8        358  6d11b2c61ec507b5f02525ddc0e7f7adb08763cd2439a4b08788b7fe51bdf5a7  2026-09-30 07:58:28
runs/smoke-t9         83  541e2d814e563ba667c95bde49765d05e44cf11aa5ab90b2f44931f30136ca9d  2026-09-30 11:27:29
runs/smoke-t10       232  319555896964ce1526f72a33cb239bf389fe29bcde23841764d13c57dfb38b8b  2026-09-30 18:23:08
runs/smoke-t11       186  a76c228f596f2a0a6309bca9cee304401ddffc2d10ab384488cfaaffb8e27392  2026-10-02 00:38:11
runs/smoke-t12       215  1d5889b7f371469459693f9904ba745ce805d571a8101afc6f6abba94aa53ea0  2026-10-02 03:37:43
.workspace/fresh-t11 100  4c07c0b6d4352a5a64e1b49908e3ae1325f62f0a3b4de44d17efc51ebffd13a4  2026-10-02 00:29:23
.workspace/fresh-t12 109  da56639bde817f5fddd0ef177543e587714418385cd57b4972ef17f63b3ce49c  2026-10-02 03:25:18
```

**口径 B（第二个独立口径，纯文本整块）**：把 T12 自己的 8 行基线表（`runs/smoke-t12/evidence/round/baseline_final.txt`）与**用同样格式重新测量得到的表**整体取 SHA-256：

```
T12 表文本 digest                     = 7cddc7e187394173502dcdeee21dbdf5426003a314c60141b1b24a82b5a3d490
本轮对同样 8 个目录重测的表文本 digest = 7cddc7e187394173502dcdeee21dbdf5426003a314c60141b1b24a82b5a3d490   ← 逐字相同
8/8 目录逐条 IDENTICAL（含 count 与 newest mtime）
```

（`evidence/analysis/text_digest_caliber.txt`。）

**口径 C（时间窗）**：

```
find runs -type f -newermt "2026-10-02 04:17:42" | grep -v smoke-t13   ->  空
find .workspace/mario / .workspace/fresh-t11 / .workspace/fresh-t12 -newermt "…"  ->  空
```

⇒ **10 条只读基线（`runs/smoke-t6..t12` + 三个既有工作区）在内容、文件数、mtime 三个口径上都未变**；本轮产出只落在 `.workspace/fresh-t13/**` 与 `runs/smoke-t13/**`。

**诚实披露（两处与 T12 报告表格的差异，且都不是本轮写的）**：
1. `runs/smoke-t12` 现在 **215 文件 / newest `03:37:43`**，而 T12 报告 §6 的表写 **215 / `03:31`**，且其 `closing_state.txt` 自记 `file count = 203`。差异与 T12 自己的收尾（`remaining` 与 `evidence/**`）一致，且**本轮在三个时点测得该目录摘要完全相同**；**但"03:31 → 03:37:43"这 6 分钟的成因我无法逐文件复算**（那是 T12 收尾窗口，缺逐文件清单）。
2. `.workspace/fresh-t12` 现在 **109 文件**，而 T12 报告 §6 的表写 **100**；其 `closing_state.txt` 自记 `.workspace/fresh-t12 file count (all) = 109`。差额 = **`.godot/**` 的编辑器缓存文件**（该目录被产物哈希排除）；**成因我不能复算**，只登记该目录的摘要在本轮三测中未变。

### 6.1 只读基线的**第三方对照**（T12A-2 后的补充）

- `PRD-mario.md` sha256 = `4c81c3a9…5c3a`（`meta.json.spec.sha256` 与 `hoh doctor` 双处一致）。
- 引擎二进制 sha256 = `08483088a4a2772841cd3b4c916b2d45b3cb6255656cf3951598a86fce7e9e6a`（**与 T12 记录逐字相同** ⇒ 引擎树未被本轮改动；本轮**未写** `godot-mcp/**`）。
- `DECISIONS.md` 本轮**未读改**（本轮只调查、只写报告与 `runs/smoke-t13/**`）；**本轮不新增 D 条目**（任务书要求：除非本轮需要，不修流水线、不改冻结规范）。

---

## 7. 机制读数表

| 机制 | 本轮真实读数（作用域已写清） |
|---|---|
| **零增量** | **未发生**。`warnings.log` 8 行里 `Zero-increment`/`no_progress`/`no_engineering_write` 各 **0** 次；`A_1 ≠ A_0` 且差异落在工程文件 |
| **修复尝试** | `wrap_up_retry_used=false`、`repair_retry_used=true`（**启动门修复**，见 §5.1）；`logs/developer.attempt2.log` 的 `notes` 逐字为 `launch_gate_repair: the pre-freeze launchable gate failed` |
| **64 KiB 上限** | **未被触发**（不是"没生效"）：四条未脱敏轨迹里 `hoh_output_truncated` **0** 次 |
| **陈旧日志** | `editor_errors_baseline.count=0`（`errors:[]`）⇒ 无"过期编辑器日志关门"可触发 |
| **轮内会话就绪（DR-70）** | **失败**：`:55361` 3 polls 全失败、路由撤回（`warnings.log` 逐字） |
| **电池 pass 1 就绪** | **失败**：`:55336` 两次 connection refused（`04:41:30`、`04:41:37`），`04:41:38` 被标记 unavailable；原始件在 `runs/smoke-t13/quarantine/deterministic-pass-1.stale-1790888078/` |
| **电池 pass 2 就绪** | **成功**：`:51223`，**1 poll** |
| **端点可达（角色侧）** | ✅ **首次有真机正面读数**：Tester 的 **4 次** `running_game_get_node_properties` **全部 exit 0**（真实节点属性回包）；Developer 的 **1 次** `running_game_get_scene_tree` **exit 5 被拒** ⇒ 同一条通道在同一轮内的两种命运，取决于**调用时刻有没有可用路由** |
| **退出码四处同数** | `exit_code` 字节 `30 0A`、`process_exit_code` 字节 `30 0A`、`meta.json.exit_code=0`、wrapper `ROUND_EXIT=0` |
| **MCP 同步** | `mcp-sync.json`（`evidence/round/…` 与冻结件内）可读；保留 pass 的 `mcp-errors.jsonl` **不存在**（pass 无传输失败）；pass 1 的有（在 quarantine） |
| **脱敏** | 4 个轨迹各有 `.redacted.json` 旁路，**原件逐字节保留**（`warnings.log` 明写）；`result.json.secret_redactions = 14` |
| **越界写入（DR-25）** | `out_of_tree_writes = [".tmp_coin.json", ".tmp_goal.json", ".tmp_hud.json"]`（**实测存在于仓根** `F:\moonbit-hof-rs\`，108/68/46 B，mtime `04:52:28–29`，`git status` 显示为未跟踪）；`artifact_hygiene = {"suspicious_files": [], "suspicious_directories": []}` |
| **图片证据** | 11 张 PNG（`frame-00` + 5 组 before/after）；`frame-00` 6240 B（大小与 T12 的 5996 B 不同，符合"场景不同"） |
| **轨迹合法性** | 4 个轨迹 + 4 个旁路 = 8 个 JSON，**全部 `json.loads` 通过**（`evidence/analysis/utf8_scan.txt` 顺带验证 UTF-8） |
| **派生物编码（T12A-3 修补）** | 本轮**所有**派生分析文件都由 Python 以 `encoding="utf-8"` 显式写盘（`capture.py`/`run_cmd.py`/各分析脚本），**没有一次控制台重定向**；扫描 = `81 文本文件 / NOT VALID UTF-8 = 0`（staging）与 `246 文本文件 / NOT VALID UTF-8 = 0`（`runs/smoke-t13`，含 11 个二进制被跳过），两处 `LEAK = 0` |

---

## 8. `A_0`/`A_1` 摘要与身份（两种口径）

| 记号 | 运行时 id（= `versions/` 目录名） | 文件数 | 字节 | 我独立复算 |
|---|---|---|---|---|
| **A_0**（`hoh init` 脚手架） | `3ac25f6c5c38885febd3a001ea99c88aca61b1799c7b105306919886c2c1d151` | 3 | 1727 | 逐字命中 |
| **A_1**（developer + 电池后的冻结候选） | `a54179ceb11b9fb6477f66b05c6e0f9ced812423eee5d4b000fa9f0a680edfc4` | 13 | 9610 | 逐字命中 |
| `iter-1/candidate` = 活体工作区 | 同上 | 13 | 9610 | 同上 |

**口径**：运行时口径 = `src/runtime/policy.rs::hash_tree`（`relpath\n{len}\n{bytes}\n` 排序流，**路径保持原大小写**）；我的独立实现 `evidence/scripts/treehash.py` **不调用** hof-rs 任何函数。

---

## 9. 报告纪律自证（§1.8 / T12 §6 四条）

### (a) 全部"0 次 / 逐位相同 / 不存在"断言都可从其引用的文件复算，且写明作用域

| 断言 | 作用域 | 复算方式 / 文件 |
|---|---|---|
| `editor_play_scene` 角色调用 = **0 次** | `runs/smoke-t13/iter-1/traj/*.json`（排除 `*.redacted.json`）的 `extra.actions[*].command` | `evidence/scripts/game_route_calls.py` → `evidence/analysis/game_route_calls.txt` |
| `running_game_*` 角色调用 = **1 次** | 同上 | 同上（并附原始命令行） |
| `tools call` 总计 = **78 次**（逐条可核对，`recount_tools.txt`） | 同上 | 同上 |
| 10 条只读基线**逐字未变** | 10 个目录的全部文件（含隐藏/系统） | 三份 `baseline_*_repo.txt` + `text_digest_caliber.txt` |
| 三棵树**逐字节相同** | `versions/a54179ce…`、`iter-1/candidate`、`.workspace/fresh-t13`（排除 `.hoh/.git/.godot/.import/node_modules/target`） | `evidence/scripts/treehash.py --compare` |
| 报告引用的**每个文件都存在** | 报告全文的反引号路径 token | `evidence/scripts/cite_check.py` → `evidence/analysis/cite_check.txt`（`MISSING = 0`） |
| **没有**任何派生物不是合法 UTF-8 | staging 81 个 + `runs/smoke-t13` 246 个文本文件 | `evidence/scripts/utf8_scan.py`（`NOT VALID UTF-8 = 0`，`LEAK = 0`） |
| 引擎树未被本轮改动 | 引擎二进制 sha256 与 T12 记录逐字相同 | §6.1 |

### (b) 机制归因附反例检验（"没看到 X" vs "X 不可能"）

见 §5.3 的 C-A..C-F。要点：**C-C 与 C-E 我明确降级**（前者是"强推断"、后者"因果未定"），**C-D 的反例成立**（1 次拒绝**不能**证明"角色 side CLI 不可用"，因为拒绝的原因是**当时没有路由**，同轮 pass 2 走通了同一条链）。

### (c) 机器可读块由 JSON 序列化器生成 + 栅栏感知 `json.loads` 回读（**已做**）

- **生成**：`evidence/scripts/build_json_block.py`（内部 `json.dump(..., ensure_ascii=False, indent=2)`，并在写盘前 `assert` 了本轮所有承重数字：`runtime_total == 15123294`、`attempt_total == 14850916`、`len(verified)==10`、`len(gap)==13`、`len(records)==31`、`start_state.mode=="fresh"`、`exit_code==0`）⇒ 输出 `evidence/analysis/machine_block.json`（31196 B）。
- **装配**：`evidence/scripts/assemble_report.py` 把该文件的**字节原样**插入 ```json 栅栏（不做字符串拼接）。
- **回读**：`evidence/scripts/json_block_check.py`（按 ``` 切块、只对 info string 为 `json` 的块 `json.loads`，核对 9 个必需顶层键，并与 `machine_block.json` 比字节）。转录见 `evidence/analysis/json_block_check.txt`。

### (d) 派生物数字与正文一致

正文所有数字都取自同一批脚本产物（`round_facts.txt`、`battery_reads.txt`、`game_route_calls.txt`、`usage_cmp.txt`、`token_totals.txt`、`a0a1_diff.txt`、`anchor_check.txt`、`epochs.txt`、`utf8_scan.txt`、`text_digest_caliber.txt`），且机器块由 `build_json_block.py` 从**同一批冻结件**重读生成、带 `assert` 把关。自查中我改过两处：JSON 里 `player x reached` 一条的引号（语法错误，已修）与一处中文被误写成 `-Term`（已修）——都发生在**报告落盘之前**。

---

## 10. 遗留风险与未验证项（严格区分实测 / 推断 / 未知）

**实测（本轮有原始证据）**

1. 空目录（0 条目）→ `hoh init` exit 0 → **恰好一轮** `hoh run` exit 0；`start_state=fresh`；`A_0` 3 文件/1727 B、与 T12/T11 的 A₀ **同 sha**。
2. **E1..E6 全部 met**（复现）；E3 四类齐备，金币 `0→2` 与 `Goal.reached false→true` 都来自**游戏端点语义工具原始回包**，且各有引擎侧 `passed=true`。
3. 行为 ①（遗留动作释放）与 ②（观测早于消耗）**复现为绿**。
4. **行为 ③：角色侧 live 路由调用本轮真的发生 1 次，被 DR-43 明确拒绝（回包逐字）**；DR-78 的"角色自起场景→重发布"分支仍 **0 次**。
5. **轮内会话启动（DR-70）失败**、电池 pass 1 就绪失败（`:55336` 两次 connection refused）、pass 2 成功（`:51223` 1 poll）——原始件分别在 `warnings.log` 与 `quarantine/`。
6. **planner token 双计确认为真**（2×），机制定位到 `usage_from_attempts` 把 `.redacted.json` 旁路当作第二个 attempt；**T12 同样中招**，T10/T11 没有。
7. developer 两次触限但 `artifact_valid=true`，且 **attempt2 是启动门修复重试**（不是 wrap-up）；原因与源码位置已给出（§5.1）。
8. 10 条只读基线**三测逐字未变**（两种独立口径）；`A_1` 三棵树逐字节同一；退出码四处一致。
9. `out_of_tree_writes` 的 3 个 `.tmp_*.json` **实测仍在仓根**、未跟踪。
10. 本轮所有派生文本**合法 UTF-8**，没有密钥泄漏（扫描 327 个文本文件（81 staging + 246 `runs/smoke-t13`）/ `LEAK = 0`）。

**推断（不得当作已测）**

1. **（≈0.8）** 轮到 :55361 与 pass 1 到 :55336 的失败，共同原因是"游戏进程在 `editor_play_scene` 应答后未在就绪窗口内绑定 MCP 端口"；支持：`ENDPOINT_DEATH_THRESHOLD=2` + 两次 connection refused + pass 2 成功。**我没有仪器化游戏进程、也没测 ready 超时与轮询间隔**，故不做"必然失败"的结论。
2. **（≈0.85）** 角色那次拒绝时 `game_endpoint.json` 确实不存在；支持：DR-70 逐字（路由被撤回）+ 回包形态（"no game endpoint is registered yet"，而非 `Expired`/`OwnerGone`/`Unreachable`）。**我没有在同一时刻直接 stat 过该文件**（运行时已撤回）。
3. **（≈0.6）** `.workspace/fresh-t12` 的 100→109 差额来自 `.godot/**` 编辑器缓存；**未逐文件复算**（缺 T12 的逐文件清单）。
4. **（≈0.5）** T12 的 `03:31 → 03:37:43` 是其收尾窗口的写入；**未复算**。

**未达到 / 未知（必须点名）**

1. **F-T13-1（major，机制侧）**：**轮内会话启动（DR-70）在本轮失败**，导致（a）角色提示词所作的承诺（"the runtime publishes that route for the whole round"）在整个窗口内为**假**；（b）角色侧 live 调用被拒；（c）电池 pass 1 白跑一次并触发一次修复重试。**根因未定**（是引擎绑定慢、还是运行时轮询/超时太紧，或两者都有）。
2. **F-T13-2（major，判据侧）**：**DR-78 的"角色自起 `editor_play_scene` → 重发布路由"仍未被任何角色走到**（0 次）。**本轮已定位到结构性原因**：`developer.md` 明令禁止角色自起场景（`:112-113`、`:142-143`），`tester.md` 把自采降为次要 ⇒ 角色**没有理由**走那条路；且角色自起场景会打断运行时自己的会话（提示词的理由仍然成立）。⇒ 该分支**不可能**在当前提示词下自然被走到，需要**显式授权或专用探针任务**才能在真机上检验。
   **但 T12A / F-T12-1 的实质问题（"角色侧 live 游戏路由到底能不能用"）本轮已由 Tester 的 4 次成功调用回答：能用**。只有"角色自己起游戏并重发布"这一条分支仍然悬空。
3. **F-T13-3（minor）**：轮级 token 数被 planner 双计抬高 272,378；下游任何基于 `result.json.usage` 的成本/消融比较都会受影响。
4. **F-T13-4（minor）**：64 KiB 截断路径仍未被真机触发（与 T11/T12 同）。
5. **F-T13-5（minor）**：developer 在仓根留下 3 个 `.tmp_*.json`（`out_of_tree_writes` 已记录）；我**按"不删"处理**（它们是本轮的取证对象），但它们会一直出现在 `git status`。
6. **F-T13-6（info）**：`result.json.warnings` 比 `warnings.log` **少** DR-69/DR-70 两条（`warnings.log` 多出的是运行级 sweep 警告）⇒ 只看 `result.json` 会**漏掉**最关键的 DR-70 警告。
7. **F-T13-7（info）**：`artifact_valid` 在修复 attempt 上复用 attempt1 的判定（§5.1）。

---

## 11. 诚实披露（含重试、意外写入）

1. **一次被拒的启动 + 恰好一轮真跑**（§1.4）：`04:14:36` 的 `hoh run` 因 `runs/smoke-t13` 已存在被立即拒绝（exit 2、0.4 s），**无角色运行、无工程写入**；把取证搬出仓外后 `04:17:42` 起**恰好一轮**。全程**未使用 `rm -rf`**、**从未从未展开变量构造路径**（所有删除都是 `rmdir` 删空目录或 `os.remove` 具名文件）。
2. **role note 注入器第一次崩了**：`%HOH_GAME_ROUTE%` 里的 `%H` 触发了 Python 的 `%` 格式化错误，留下一个 **0 字节**的 `.hoh/ROLE_NOTE-t13.md`；`04:19:09` 用修正后的脚本重写为 **1586 B**（`evidence/round/role_note_injection.txt`）。**该注入在计划上还有一处判断错**：角色视图由 `build_view` 构造（`.hoh` 被排除），所以**只有 live 工作区里的那一份**会被副本带进后续视图。
3. **引擎我启动了两次以上**：①空目录门复现（pid 25344，`taskkill /PID 25344 /T` 精确停掉，**未用 `rm -rf`**）；②本轮编辑器（pid 948，收工时仍存活）。**两个进程的控制台输出都在证据里**（T12A-1 的直接修补）。
4. **暂存目录**：`F:\moonbit-hof-rs-t13-staging`（**仓外**）；收工时其内容全部复制进 `runs/smoke-t13/evidence/**`（**106** 个文件：round 23 / analysis 28 / gatecheck 5 / scripts 50），暂存目录保留（未删）。
5. **我做的机器动作**：`mkdir`/`rmdir`（仅空目录）/`os.remove`（仅具名文件）/`copytree`/`os.rename`、`cargo build --release --offline`（**无重编**）、启动/精确 pid 停止 godot、只读的进程/端口/文件检查、**一轮** `hoh run`、以及本地只读分析脚本。**没有改 `src/**`、`tests/**`、`godot-mcp/**`、`.workspace/mario/**`、`.workspace/fresh-t11/**`、`.workspace/fresh-t12/**`、`PRD-mario.md`、`DECISIONS.md`、`REQUIREMENTS.md`，也没有改任何冻结任务书。**
5b. **我在轮次还在跑的时候做过一次普查，并因此把 Tester 数少了**：那一版快照显示 `tester.attempt1` 有 85 条执行命令、`running_game_*` **0** 次；**同一文件的最终工件**是 134 条执行命令、`running_game_*` **4** 次且全部成功（消息 151–155）。运行期会在角色返回之后**继续补写**轨迹（我后来用 `where_strings.py` 逐消息定位到这 4 次调用确实在 `extra.actions[*].command` 里）。**本报告中的所有计数都已改用最终工件重算**，这条错误在此如实登记。
6. **密钥卫生**：`HOH_MODEL_API_KEY` 只从 `config/model.secret.env` 注入**子进程环境**（`run_cmd.py`/`capture.py`），**只报长度 51，从不打印**；扫描 `219` 个文本文件（staging 74 + `runs/smoke-t13` 145）**0 处**含该值。
7. **未 push**：`origin/master == 8ddbad3f…`（与开工相同）；本轮唯一提交只含报告文件。
8. **本报告的证据全部来自本轮**（`runs/smoke-t13/**`、`.workspace/fresh-t13/**`、`F:\moonbit-hof-rs-t13-staging\**`）；对 T10/T11/T12 的引用只用于**口径自证**与**历史对照**，不冒充本轮读数。
9. **本轮不修任何发现的问题**（F-T13-1..F-T13-7）：任务书 §1.4 明确要求"除非本轮本身需要，不修流水线"。

---

## 12. 工件索引

| 类别 | 路径 |
|---|---|
| 轮记录（运行时） | `runs/smoke-t13/`：`exit_code`、`process_exit_code`、`meta.json`、`warnings.log`、`TOOLS.md`、`versions/{index.json,3ac25f6c…,a54179ce…}`、`quarantine/deterministic-pass-1.stale-1790888078/**`、`iter-1/{plan.md,result.json,usage.json,evidence.json,qa_report.md,logs/,traj/,planner-view/,candidate/}` |
| 被开发工程 | `.workspace/fresh-t13/**`（`project.godot`、`scenes/main.tscn`、`scripts/*.gd`） |
| 原始取证（本轮自建，已并入） | `runs/smoke-t13/evidence/round/**`（21 个）、`evidence/gatecheck/**`（5 个） |
| 可复跑脚本 | `runs/smoke-t13/evidence/scripts/**`（37 个：`capture.py`、`run_cmd.py`、`empty_proof.py`、`port_preflight.py`、`gate_launch.py`、`mcp_call.py`、`tool_census.py`、`baseline_digest_repo.ps1`、`anchor_hash.py`、`anchor_check.py`、`treehash.py`、`a0a1_diff.py`、`round_facts.py`、`battery_reads.py`、`game_route_calls.py`、`called_tools_census.py`、`usage_cmp.py`、`usage_from_traj.py`、`publish_readiness.py`、`text_digest_caliber.py`、`utf8_scan.py`、`cite_check.py`、`build_json_block.py`、`assemble_report.py`、`json_block_check.py` 等） |
| 分析输出 | `runs/smoke-t13/evidence/analysis/**`（14 个，全部显式 UTF-8） |
| 图片证据 | `runs/smoke-t13/iter-1/candidate/.hoh/evidence/*.png`（11 张） |
| 规范 / 任务书 | `.spec/hof-rs/REQUIREMENTS.md`（E1..E6 第 110-119 行）、`.spec/hof-rs/OBJECTIVE-COMPLETION.md`、`.spec/hof-rs/tasks/TASK-SMOKE-T13.md`、`TASK-SMOKE-T12.md` |
| 上轮对照 | `TASK-SMOKE-T12-REPORT.md`、`TASK-SMOKE-T12-ACCEPTANCE.md`、`TASK-SMOKE-T11-REPORT.md` |
| 相关决策（只读） | `DECISIONS.md` **D290 / D291 / D292** |
| 仓外暂存（未删） | `F:\moonbit-hof-rs-t13-staging/**` |

---

## 附：机器可读结论

（本块由 `evidence/scripts/build_json_block.py` 用 `json.dump(..., ensure_ascii=False, indent=2)` 序列化，
与 `evidence/analysis/machine_block.json` **逐字相同**；由 `evidence/scripts/assemble_report.py` 原样插入。
落盘后由 `evidence/scripts/json_block_check.py` 以栅栏感知方式 `json.loads` 回读并与该文件比字节，
转录见 `evidence/analysis/json_block_check.txt`。）

```json
{
  "task": "TASK-SMOKE-T13",
  "kind": "reproducibility round: rerun of the TASK-SMOKE-T12 command sequence in a new empty project",
  "round_id": "smoke-t13",
  "run_dir": "runs/smoke-t13",
  "project_dir": ".workspace/fresh-t13",
  "evidence_dir": "runs/smoke-t13/evidence",
  "head_at_start": "8ddbad3f4db43c28be158c17ad0678fe4d77857c",
  "head_at_report_time": "8ddbad3f4db43c28be158c17ad0678fe4d77857c",
  "previous_round": {
    "task": "TASK-SMOKE-T12",
    "run_dir": "runs/smoke-t12",
    "project_dir": ".workspace/fresh-t12"
  },
  "commands": {
    "t12_init": "target/release/hoh.exe init  --project F:\\moonbit-hof-rs\\.workspace\\fresh-t12",
    "t13_init": "target/release/hoh.exe init --project F:\\moonbit-hof-rs\\.workspace\\fresh-t13",
    "t12_run": "target/release/hoh.exe run --iterations 1 --run-id smoke-t12 --fresh-workspace --project F:\\moonbit-hof-rs\\.workspace\\fresh-t12",
    "t13_run": "target/release/hoh.exe run --iterations 1 --run-id smoke-t13 --fresh-workspace --project F:\\moonbit-hof-rs\\.workspace\\fresh-t13",
    "engine_launch": "F:\\moonbit-hof-rs\\godot-mcp\\godot\\bin\\godot.windows.editor.x86_64.mono.exe -e --path F:\\moonbit-hof-rs\\.workspace\\fresh-t13 --mcp-port=9877",
    "identical_apart_from": [
      "the run id (smoke-t12 / smoke-t13)",
      "the project directory (fresh-t12 / fresh-t13)"
    ],
    "same_command_evidence": "runs/smoke-t13/evidence/round/init.txt and round_console2.txt carry the verbatim command line of this round; TASK-SMOKE-T12-REPORT.md lines 8-9 carry T12's",
    "aborted_first_attempt": {
      "command": "same as t13_run, launched at 04:14:36",
      "exit_code": 2,
      "reason": "run directory runs/smoke-t13 already exists; pass --resume (not implemented in v1)",
      "cause": "the round author had staged pre-round evidence under runs/smoke-t13 before starting the round",
      "disclosure": "one aborted launch; no role ran, no project byte was written; the round was then run exactly once"
    }
  },
  "engine": {
    "version_string": "4.8.dev.mono.custom_build.035edfce7",
    "binary": "F:\\moonbit-hof-rs\\godot-mcp\\godot\\bin\\godot.windows.editor.x86_64.mono.exe",
    "size_bytes": 194216960,
    "mtime_unix": 1790641862,
    "sha256": "08483088a4a2772841cd3b4c916b2d45b3cb6255656cf3951598a86fce7e9e6a",
    "identical_to_t12_record": true,
    "listener_pid": 948,
    "cmdline_verbatim": "F:\\moonbit-hof-rs\\godot-mcp\\godot\\bin\\godot.windows.editor.x86_64.mono.exe -e --path F:\\moonbit-hof-rs\\.workspace\\fresh-t13 --mcp-port=9877",
    "creation_date_local": "2026-10-02 04:12:48",
    "role_at_listen": "editor",
    "tools_at_editor_endpoint": 154,
    "started_by_this_round": true,
    "console_capture_from_first_second": "runs/smoke-t13/evidence/round/editor_console_launch.txt",
    "alive_at_report_time": true
  },
  "role_gate_reproduction": {
    "claim": "with -e --path pointing at a directory that has no project.godot, the engine comes up as role=game with 73 tools and every editor_* tool missing",
    "independent_reproduction": true,
    "path_dir": "F:\\moonbit-hof-rs\\.workspace\\fresh-t13 (empty at the time of the launch)",
    "path_dir_entries_at_launch": [],
    "path_dir_project_godot_exists_at_launch": false,
    "pid": 25344,
    "cmdline_verbatim": "F:\\moonbit-hof-rs\\godot-mcp\\godot\\bin\\godot.windows.editor.x86_64.mono.exe -e --path F:\\moonbit-hof-rs\\.workspace\\fresh-t13 --mcp-port=9877",
    "first_mcp_ready_line": "[MCP] INFO: MCP server is ready on 127.0.0.1:9877 as the game process (port source=cmdline, tools=73)",
    "console_capture": "runs/smoke-t13/evidence/gatecheck/game-role-console.txt",
    "launch_meta": "runs/smoke-t13/evidence/gatecheck/game-role-launch_meta.txt",
    "live_tools_list_reply": "runs/smoke-t13/evidence/gatecheck/game-role-tools_list.json",
    "tools_served": 73,
    "tools_by_prefix": {
      "project_": 48,
      "running_": 23,
      "os_": 2
    },
    "editor_star_served": 0,
    "editor_star_in_contract": 104,
    "served_but_not_in_contract": 0,
    "editor_status_call_refused": "{\"error\":{\"code\":-32601,\"message\":\"Method not found: editor_status\"}}",
    "b_side": {
      "path_dir": "the same directory after `hoh init`",
      "pid": 948,
      "role": "editor",
      "tools_served": 154,
      "tools_by_prefix": {
        "editor_": 104,
        "project_": 48,
        "os_": 2
      },
      "running_game_star_served": 0,
      "same_binary_sha256": "08483088a4a2772841cd3b4c916b2d45b3cb6255656cf3951598a86fce7e9e6a"
    },
    "census_files": [
      "runs/smoke-t13/evidence/analysis/tool_census_game_role.txt",
      "runs/smoke-t13/evidence/analysis/tool_census_editor_role.txt"
    ],
    "conclusion": "reproduced, and both sides now carry their own launch console, cmdline and pid; the only variable flipped between the two launches was the presence of project.godot"
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
      "independent_recompute_matches": true,
      "project_godot_sha256": "00d02c9c08c3dc4fc35e3d9bcc94b06c31d44b42df2f017bc0ca5615a12c0ef4"
    },
    "A1": {
      "runtime_id": "a54179ceb11b9fb6477f66b05c6e0f9ced812423eee5d4b000fa9f0a680edfc4",
      "files": 13,
      "bytes": 9610,
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
      {
        "path": "scenes/main.tscn",
        "from_bytes": 342,
        "to_bytes": 4335
      }
    ],
    "removed": [],
    "runtime_evidence_diff_agrees": true
  },
  "timing": {
    "started_console": "2026-10-02 04:17:42",
    "ended_console": "2026-10-02 05:04:02",
    "elapsed_seconds": 2780.241,
    "t12_elapsed_seconds": 2144,
    "rounds_that_actually_started": 1,
    "started_at_epoch": 1790885864,
    "versions_a0_created_at": 1790885864,
    "versions_a1_created_at": 1790888091
  },
  "tokens": {
    "runtime_summary_total": 15123294,
    "sum_of_attempts": 14850916,
    "planner_summary": {
      "calls": 54,
      "total_tokens": 544756
    },
    "planner_attempt": {
      "calls": 27,
      "total_tokens": 272378
    },
    "planner_double_counted": true,
    "double_count_cause": "usage_from_attempts (src/runtime/usage.rs:130) matches every traj file whose name starts with '<role>.attempt' and ends with '.json'; the frozen-evidence redacted sidecar '<role>.attempt1.redacted.json' matches too, so the role is counted twice when a redaction copy exists at summary time",
    "t12_had_the_same_defect": true,
    "t10_t11_ratios": {
      "t10_planner": 1.0,
      "t11_planner": 1.0
    },
    "t12_planner_ratio": 2.0,
    "t13_planner_ratio": 2.0
  },
  "verdicts": {
    "E1": "met",
    "E2": "met",
    "E3": "met",
    "E4": "met",
    "E5": "met",
    "E6": "met"
  },
  "criteria": [
    {
      "id": "E1",
      "pass": true,
      "evidence": "empty directory proven (empty_proof.txt: dir did not exist, then ENTRY_COUNT=0) -> hoh init exit 0 -> exactly one hoh run exit 0; start_state {mode:fresh}; A0 3ac25f6c... 3 files/1727 B -> A1 a54179ce... 13 files/9610 B (10 added, main.tscn 342->4335 B, 0 removed); planner artifact_valid true, tester Submitted; exit_code bytes 0x30 0x0a, process_exit_code bytes 0x30 0x0a, meta.exit_code 0; artifact_gate launchable true"
    },
    {
      "id": "E2",
      "pass": true,
      "evidence": "editor_errors_baseline count=0 errors=[]; play_scene_ready editor_play_scene playing=true pid 30728 endpoint :51223 then running_game_get_scene_tree -> 28 typed nodes; screenshot written (6240 B PNG); editor_stop_scene stopped=true (battery step 10); artifact_gate {applicable:true, launchable:true, reasons:[]} in meta.json and result.json; battery 12/12 steps ok"
    },
    {
      "id": "E3",
      "pass": true,
      "evidence": "four classes, all from the game endpoint's semantic tools: move_left x 1786.76892089844 -> 1570.43798828125 (delta -216.330933, 60/60 unique); move_right x 1773.99353027344 -> 1795.07604980469 (delta +21.082520, 26/60 unique, stopped by the Wall at x=1900); jump a pure vertical arc (x unique=1 at 1794.10217285156, y 279.979614257812 -> min 224.257385253906 -> 252.590744018555, y unique=30); interactable object Coins: 0 -> Coins: 2 with running_game_assert_node_state text:neq passed=true; win condition Goal.reached false -> true with reached:neq passed=true. Four POSITION_ASSERT_PASSED lines in the game process"
    },
    {
      "id": "E4",
      "pass": true,
      "evidence": "evidence.json: 10 verified / 13 gap, overlap [], every record's candidate_id is A1, 31 execution records over verified+gap (10 verified-only / 13 gap-only - scopes stated), MISSING record paths [], every gap has player_impact and recommended_update; planner_handoff 4/9/3"
    },
    {
      "id": "E5",
      "pass": true,
      "evidence": "versions/A1 == iter-1/candidate == live .workspace/fresh-t13, byte-identical (13 files / 9610 B, only_in=[], differing=[])"
    },
    {
      "id": "E6",
      "pass": true,
      "evidence": "qa_report.md line 'Verdict: partial'; 13 gap families enumerated with player impact; it explicitly refuses to treat the input_axis probe as an observable (DR-58)"
    }
  ],
  "fixes_and_behaviours": {
    "1_stale_action_release": {
      "verdict": "green (reproduced)",
      "evidence": "interaction_evidence call[4] running_game_play_input_recording 'interaction:release_stale_move_left' -> {event_count:1, injected:1, replayed:true, speed:1.0}, before the first driven batch at call[6]; batches then advance 60/60 unique x each",
      "STALE_ACTION_NOT_RELEASED_count_in_battery_verdict_lines": 0
    },
    "2_observation_before_consumption": {
      "verdict": "green (reproduced)",
      "evidence": "battery step order: interaction_evidence at index 6, input_channel_probe at 7, input_replay at 8; the window's own readings are Coins: 0 (call[0]) -> Coins: 2 (call[24]) with COIN_PICKED_UP and WIN_DRIVEN in its verdict line",
      "coin_before": "Coins: 0",
      "coin_after": "Coins: 2"
    },
    "3_role_initiated_live_game_call": {
      "verdict": "EXERCISED BY TWO ROLES: the Tester's four live game-route calls all succeeded; the Developer's single one was refused, and the refusal is explained by the round's own earlier failure",
      "tester_success": {
        "role": "tester, attempt 1",
        "calls": 4,
        "tool": "running_game_get_node_properties",
        "refusals": 0,
        "raw_reply_1_verbatim": "{\"node_path\":\"/root/Main/HUD/Result\",\"properties\":{\"text\":\"\"},\"type\":\"Label\"}",
        "raw_reply_2_verbatim": "{\"node_path\":\"/root/Main/Player\",\"properties\":{\"facing\":1,\"position\":{\"x\":80.0,\"y\":293.998992919922},\"velocity\":{\"x\":0.0,\"y\":0.0}},\"type\":\"CharacterBody2D\"}",
        "exit_codes": [
          0,
          0,
          0,
          0
        ],
        "trajectory": "runs/smoke-t13/iter-1/traj/tester.attempt1.json",
        "messages": [
          151,
          152,
          153,
          154,
          155
        ],
        "why_they_succeeded": "the Tester ran after the deterministic battery had started its own game (:51223) and published the route, so HOH_GAME_ROUTE named a live endpoint; 0 of 4 refused",
        "evidence_file": "runs/smoke-t13/evidence/analysis/tester_running_game_invocations.txt"
      },
      "developer_refusal": {
        "role": "developer, attempt 2",
        "tool": "running_game_get_scene_tree",
        "raw_command": "cd /d F:\\moonbit-hof-rs && echo {} > .tmp_probe.json && \"%HOH_HOH_BIN%\" tools call running_game_get_scene_tree --args-file .tmp_probe.json 2>&1",
        "raw_reply_verbatim": "hoh: game_endpoint_unavailable: `running_game_get_scene_tree` runs in the game process and only the game endpoint serves it; no game endpoint is registered yet (`editor_play_scene` must have answered with `endpoint` or `mcp_port`). Falling back to the editor endpoint is not allowed (DR-43).",
        "exit_code": 5,
        "trajectory": "runs/smoke-t13/iter-1/traj/developer.attempt2.json",
        "request_message_index": 137,
        "reply_message_index": 139,
        "why_it_was_refused": "the runtime's own round-game start failed its readiness poll at 04:17:44 (warnings.log DR-70), so no route existed for the role to adopt; the same readiness failure then hit battery pass 1 (:55336, connection refused twice, endpoint marked unavailable) and only battery pass 2 (:51223) succeeded"
      },
      "hoh_role_initiated_editor_play_scene_calls": 0,
      "consequence_for_the_fixes": "the DR-69 adopt-published-route path IS now proven on real hardware (the Tester's four calls); the DR-78 republish path (which only fires on a role's own editor_play_scene) is still unexercised because no role called it"
    }
  },
  "role_live_call_census": {
    "corpus": "every extra.actions[*].command in runs/smoke-t13/iter-1/traj/*.json, excluding *.redacted.json (the FINAL artifacts, after the runtime's post-role enrichment; an in-flight snapshot taken while the round was still running undercounts the Tester, see honest_disclosure)",
    "per_trajectory": {
      "planner.attempt1": {
        "executed_commands": 29,
        "tools_call": 0,
        "running_game_star": 0,
        "editor_play_scene": 0
      },
      "developer.attempt1": {
        "executed_commands": 187,
        "tools_call": 23,
        "running_game_star": 0,
        "editor_play_scene": 0
      },
      "developer.attempt2": {
        "executed_commands": 98,
        "tools_call": 47,
        "running_game_star": 1,
        "editor_play_scene": 0
      },
      "tester.attempt1": {
        "executed_commands": 134,
        "tools_call": 8,
        "running_game_star": 4,
        "editor_play_scene": 0
      }
    },
    "total_tools_call": 78,
    "total_running_game_star": 5,
    "running_game_star_succeeded": 4,
    "running_game_star_refused": 1,
    "total_editor_play_scene": 0,
    "tools_call_scope_note": "78 counts `tools call` lines inside executed commands; a command may chain two of them, and `called_tools_census.py` counts per line-eight occurrences the same way",
    "negative_control": "the detector fires on synthetic `tools call running_game_get_scene_tree` / `editor_play_scene` and does not fire on a plain mention of running_game_ inside an analysis command",
    "census_files": [
      "runs/smoke-t13/evidence/analysis/game_route_calls.txt",
      "runs/smoke-t13/evidence/analysis/called_tools_census.txt",
      "runs/smoke-t13/evidence/analysis/recount_tools.txt",
      "runs/smoke-t13/evidence/analysis/tester_running_game_invocations.txt",
      "runs/smoke-t13/evidence/analysis/where_tester_rg.txt"
    ]
  },
  "reproducibility": {
    "question": "does criterion (4)'s 'the same command can be rerun in a clean environment' hold?",
    "answer": "yes for the outcome class and for every stated invariant; no for bytes, and byte equality was never expected (the pipeline is driven by a stochastic model)",
    "outcome_class_reproduced": [
      "E1..E6 all met in both rounds",
      "start_state mode=fresh in both rounds",
      "artifact_gate applicable+launchable with reasons=[] in both rounds",
      "exit codes agree in both rounds (t12: bytes 30 0a / 0 / 30 0a, wrapper 0; t13: bytes 30 0a / 0 / 30 0a, wrapper 0)",
      "A0 identical in both rounds (3ac25f6c..., 3 files/1727 B, same project.godot sha256)",
      "A1 != A0 in both rounds, with the change falling on engineering files",
      "four behaviour classes each carry an engine-side passed=true assertion in both rounds",
      "the read-only baselines are byte-identical in both rounds"
    ],
    "invariants_that_flipped": [
      "T13's round-game start failed readiness (40 consecutive real rounds would have hidden this); T12's did not",
      "T13's developer never hit the wrap-up retry but did use the launch-gate repair retry; T12's developer used the wrap-up retry and not the repair retry",
      "T13's developer-artifact_valid is true for both attempts; T12's was false for both"
    ],
    "bytes_not_reproduced": {
      "A1_id_t12": "fc50ecd2c1acfcb9854c14b99edfc9dcc5f7004f6377b34ba90a1bb088cd228d",
      "A1_id_t13": "a54179ceb11b9fb6477f66b05c6e0f9ced812423eee5d4b000fa9f0a680edfc4",
      "A1_files_t12": 11,
      "A1_files_t13": 13,
      "A1_bytes_t12": 7384,
      "A1_bytes_t13": 9610,
      "why": "the Developer is a language model; the plan it received, the level it built and therefore the tree hash are all different"
    },
    "deltas": [
      {
        "item": "wall clock",
        "t12": "35m44s (2144 s)",
        "t13": "46m20s (2780 s)"
      },
      {
        "item": "tokens (runtime summary total)",
        "t12": 17703610,
        "t13": 15123294
      },
      {
        "item": "tokens (attempt sum)",
        "t12": 17252776,
        "t13": 14850916
      },
      {
        "item": "A1",
        "t12": "fc50ecd2... 11 files/7384 B",
        "t13": "a54179ce... 13 files/9610 B"
      },
      {
        "item": "scene nodes",
        "t12": 22,
        "t13": 28
      },
      {
        "item": "developer attempts",
        "t12": "2 (both LimitsExceeded, artifact_valid=false, wrap_up_retry)",
        "t13": "2 (attempt1 LimitsExceeded, attempt2 = launch-gate repair, both artifact_valid=true, wrap_up_retry_used=false, repair_retry_used=true)"
      },
      {
        "item": "player x reached",
        "t12": "738.333984375 (starts near 67)",
        "t13": "1667.66174316406 (starts near 87); the level is longer and has a Wall at x=1900"
      },
      {
        "item": "coin counter transition",
        "t12": "Coins: 0 -> Coins: 2",
        "t13": "Coins: 0 -> Coins: 2"
      },
      {
        "item": "move_right delta in input_replay",
        "t12": "+216.333312988 px (60/60 unique)",
        "t13": "+21.082520 px (26/60 unique, blocked by the Wall)"
      },
      {
        "item": "move_left delta",
        "t12": "-216.332458496 px",
        "t13": "-216.330933 px"
      },
      {
        "item": "jump shape",
        "t12": "x unique=1, y unique=30",
        "t13": "x unique=1, y unique=30"
      },
      {
        "item": "gap ids",
        "t12": "[F1-stop, F6, F7, F8, F9, F11, F12, F14, F15, F17]",
        "t13": "[F2b, F4, F6, F7, F8, F9, F11, F12, F13b, F14, F15, F17, N3b]"
      },
      {
        "item": "verified count",
        "t12": 12,
        "t13": 10
      }
    ],
    "unstable_items_and_whether_they_change_the_verdict": [
      {
        "item": "the round-game readiness failure",
        "changes_verdict": false,
        "why": "it removed the role-visible route for one window and cost battery pass 1, but the artifact gate still passed and the battery's own pass 2 produced every reading E1..E6 needs"
      },
      {
        "item": "which retry the developer used",
        "changes_verdict": false,
        "why": "both rounds ended with a usable A1 and exit 0; the retry flavour is a mechanism reading, not a criterion"
      },
      {
        "item": "A1 identity and every movement magnitude",
        "changes_verdict": false,
        "why": "E3 asks for the existence of the four behaviour classes, which both rounds satisfy with engine-side assertions"
      }
    ]
  },
  "anomaly_investigations": {
    "a_developer_attempt_limit_and_artifact_valid": {
      "reported_shape": "the developer exhausted its attempt limit twice and its project was still snapshotted with artifact_valid=true",
      "was_it_true": {
        "attempts_that_hit_the_limit": 2,
        "artifact_valid_values": [
          true,
          true
        ],
        "wrap_up_retry_used": false,
        "repair_retry_used": true
      },
      "not_a_recurrence_of_the_t10_t12_shape": true,
      "what_the_second_call_actually_was": "the launch-gate repair retry (DR-24/DR-70): battery pass 1 failed the launchable gate, so the runtime made one targeted Developer call with budget repair_steps; its log note is 'launch_gate_repair: the pre-freeze launchable gate failed' (runs/smoke-t13/iter-1/logs/developer.attempt2.log)",
      "why_artifact_valid_is_true": "it is `developer_artifact_valid_in` (src/adapter/godot.rs:306): the configured main scene exists, parses (validate_scene_structure_in), references at least one script resource, and every referenced script file exists and is non-empty. The T13 scene satisfied all of that at the moment attempt 1 ended, which is also why the wrap-up retry did not fire. The value is NOT 'the attempt succeeded' and NOT re-evaluated after the repair call.",
      "is_this_intended": {
        "answer": "the flag and the retry gate are consistent with their documented meaning; what is loose is that the second attempt is stamped with the FIRST attempt's artifact check rather than a fresh one",
        "consequence": "attempt 2 in the attempts table shows artifact_valid=true even though the repair call itself was checked never; a round whose repair made the scene worse would carry the same value",
        "verified_by": "source reading of run_loop.rs:1137/1185; no test was run against this branch"
      },
      "fix_required_for_this_round": false
    },
    "b_planner_usage_double_count": {
      "was_it_true": true,
      "mechanism": "src/runtime/usage.rs:130 usage_from_attempts filters on `name.starts_with(\"<role>.attempt\") && name.ends_with(\".json\")`; the redaction sidecars `planner.attempt1.redacted.json` etc. match, and they carry the same `extra.response.usage` blocks, so the role is summed twice",
      "arithmetic": {
        "planner_attempt_calls": 27,
        "planner_attempt_tokens": 272378,
        "planner_summary_calls": 54,
        "planner_summary_tokens": 544756,
        "runtime_total": 15123294,
        "attempt_total": 14850916
      },
      "counterexample_check": "re-implemented the runtime's own extract+merge over exactly the files its filter matches: both the plain and the redacted planner trajectory contribute 27 calls / 272378 tokens, and the merged value equals the runtime's summary exactly (evidence/analysis/usage_attribution_t13.txt)",
      "scope_of_the_defect": "any role whose trajectory had a redaction sidecar written before the summary: planner in t12 and t13, developer in t13 (developer's own summary equals the sum of the attempt rows, so the developer's plain-attempt rows are the only ones present in its summary path)",
      "history": {
        "t10_planner_ratio": 1.0,
        "t11_planner_ratio": 1.0,
        "t12_planner_ratio": 2.0,
        "t13_planner_ratio": 2.0
      },
      "why_t10_t11_were_clean": "no redaction sidecar existed in those rounds' traj directories at summary time (t10 had none at all; t11 had only the developer's, and the developer entry is built by merging attempt usages rather than by re-walking the directory)",
      "fix_required_for_this_round": false,
      "impact": "the round's headline token number is inflated by exactly the planner's attempt; every per-attempt row is correct"
    }
  },
  "count_scopes": {
    "verified_records": {
      "value": 10,
      "scope": "iter-1/evidence.json verified_records list length"
    },
    "gap_records": {
      "value": 13,
      "scope": "iter-1/evidence.json gap_records list length"
    },
    "execution_records_verified_only": {
      "value": 10,
      "scope": "execution_records entries inside verified_records only"
    },
    "execution_records_gap_only": {
      "value": 13,
      "scope": "execution_records entries inside gap_records only"
    },
    "execution_records_verified_plus_gap": {
      "value": 31,
      "scope": "all execution_records entries in evidence.json"
    },
    "role_tools_call_invocations": {
      "value": 78,
      "scope": "extra.actions[*].command across the four unredacted FINAL trajectories; each `tools call <name>` occurrence counted once"
    },
    "role_running_game_invocations": {
      "value": 5,
      "scope": "same corpus (4 succeeded - Tester; 1 refused - Developer)"
    },
    "role_editor_play_scene_invocations": {
      "value": 0,
      "scope": "same corpus"
    },
    "round_dir_files": {
      "value": 264,
      "scope": "runs/smoke-t13 after evidence/ was copied in; 147 before"
    },
    "round_dir_files_before_evidence": {
      "value": 147,
      "scope": "runs/smoke-t13 excluding runs/smoke-t13/evidence/**"
    },
    "evidence_files_copied_in_after_close": {
      "value": 110,
      "scope": "runs/smoke-t13/evidence/** (23 round + 31 analysis + 5 gatecheck + 51 scripts)"
    },
    "read_only_baseline_dirs": {
      "value": 10,
      "scope": "runs/smoke-t6..t12 and .workspace/{mario,fresh-t11,fresh-t12}"
    }
  },
  "baselines": {
    "caliber": "Get-ChildItem -Recurse -Force -File; repo-root-relative lowercase POSIX path + TAB + bytes + TAB + sha256; LF-joined, no trailing newline; culture order; SHA-256 of those UTF-8 bytes",
    "caliber_is_anchored": "the same caliber reproduces all eight T12-published digests (including runs/smoke-t6 = c144ef32...7a9c03) exactly",
    "second_independent_caliber": {
      "what": "SHA-256 of the whole baseline TABLE text (T12's own table format)",
      "t12_table_text_digest": "7cddc7e187394173502dcdeee21dbdf5426003a314c60141b1b24a82b5a3d490",
      "t13_table_text_digest_over_the_same_eight_dirs": "7cddc7e187394173502dcdeee21dbdf5426003a314c60141b1b24a82b5a3d490",
      "identical": true,
      "file": "runs/smoke-t13/evidence/analysis/text_digest_caliber.txt"
    },
    "calibration_file": "runs/smoke-t13/evidence/analysis/anchor_calibration.txt",
    "read_only_dirs_unchanged_three_ways": true,
    "before_after_evidence_files": [
      "evidence/round/baseline_before_repo.txt",
      "evidence/round/baseline_after_repo.txt",
      "evidence/round/baseline_after_evidence.txt"
    ],
    "zero_byte_write_window": "find runs -newermt '2026-10-02 04:17:42' outside smoke-t13 -> empty; mario/fresh-t11/fresh-t12 -> empty"
  },
  "mechanisms": {
    "zero_increment": {
      "occurred": false,
      "evidence": "warnings.log carries neither Zero-increment, no_progress nor no_engineering_write; A1 != A0 with the change on engineering files"
    },
    "repair_attempts": {
      "wrap_up_retry_used": false,
      "wrap_up_retry_reason": "not_triggered",
      "repair_retry_used": true,
      "repair_note": "launch_gate_repair: the pre-freeze launchable gate failed"
    },
    "truncation_64kib": {
      "triggered": false
    },
    "editor_errors_baseline_count": 0,
    "round_game_readiness_failure": {
      "occurred": true,
      "endpoint": "http://127.0.0.1:55361/mcp",
      "polls": 3,
      "warning_source": "runs/smoke-t13/warnings.log (DR-70 line)",
      "consequence": "no published route for any role until battery pass 2"
    },
    "battery_pass_1_readiness_failure": {
      "occurred": true,
      "endpoint": "http://127.0.0.1:55336/mcp",
      "transport_failures": [
        1790887290,
        1790887297
      ],
      "marked_unavailable_at": 1790887298,
      "evidence": "runs/smoke-t13/quarantine/deterministic-pass-1.stale-1790888078/{raw/play_scene_ready.json,mcp-errors.jsonl}"
    },
    "battery_pass_2_readiness": {
      "ok": true,
      "endpoint": "http://127.0.0.1:51223/mcp",
      "polls": 1
    },
    "out_of_tree_writes": [
      ".tmp_coin.json",
      ".tmp_goal.json",
      ".tmp_hud.json"
    ],
    "secret_redactions": 14,
    "mcp_errors_kept_pass_present": false
  },
  "evidence_files_that_exist": {
    "note": "the report's appendix carries the full generated index with byte sizes and sha256 for 59 cited files; this list names the load-bearing ones. Counts: evidence/round 23, evidence/analysis 31, evidence/gatecheck 5, evidence/scripts 51, total 110.",
    "round": [
      "empty_proof.txt",
      "preflight_doctor.txt",
      "preflight_port.txt",
      "init.txt",
      "init_tree.txt",
      "editor_console_launch.txt",
      "editor_launch_meta.txt",
      "editor_tools_list.json",
      "scope_project_list_scripts.json",
      "scope_project_filesystem_tree.json",
      "round_console.txt",
      "round_console2.txt",
      "role_note_injection.txt",
      "inject_stdout.txt",
      "baseline_before_repo.txt",
      "baseline_before.txt",
      "baseline_before_legacy.txt",
      "baseline_after_repo.txt",
      "baseline_after_evidence.txt",
      "README_STAGING.txt",
      "game_endpoint_tools_list_round_author.json",
      "game_endpoint_scene_tree_round_author.json",
      "report_body.md"
    ],
    "gatecheck": [
      "game-role-console.txt",
      "game-role-launch_meta.txt",
      "game-role-tools_list.json",
      "game-role-editor_status.json",
      "game-role-pid.txt"
    ],
    "analysis": [
      "round_facts.txt",
      "battery_reads.txt",
      "game_route_calls.txt",
      "called_tools_census.txt",
      "recount_tools.txt",
      "tester_running_game_invocations.txt",
      "tester_play_scene.txt",
      "where_tester_rg.txt",
      "where_tester_play_scene.txt",
      "usage_cmp.txt",
      "usage_attribution_t12.txt",
      "usage_attribution_t13.txt",
      "publish_readiness.txt",
      "a0a1_diff.txt",
      "anchor_check.txt",
      "anchor_calibration.txt",
      "tool_census_game_role.txt",
      "tool_census_editor_role.txt",
      "token_totals.txt",
      "epochs.txt",
      "utf8_scan.txt",
      "utf8_scan_round.txt",
      "text_digest_caliber.txt",
      "file_inventory.txt",
      "machine_block.json",
      "json_block_check.txt",
      "cite_check.txt",
      "evidence_index.md",
      "game_route_calls_inflight.txt"
    ],
    "scripts": "51 files under evidence/scripts (see the generated index)"
  },
  "unverified": [
    "whether the engine always needs more than ~10 s to bind the game MCP port after editor_play_scene answers: three observations exist (two failures at :55361 and :55336, one success at :51223) but the readiness timeout and poll cadence were not measured directly",
    "the exact lifetime of the original round game process on :55361: it was not probed before the runtime marked it unavailable",
    "why the round-game start and battery pass 1 failed while battery pass 2 succeeded moments later: the port was different each time and the game process was not instrumented",
    "the DR-78 role-started-scene republish path: no role called editor_play_scene, so the branch, its readiness wait and its publish failure modes remain unexercised",
    "the semantics of `out_of_tree_writes` beyond the three paths it lists: the runtime recorded the writes but this round did not read the verification logic",
    "the redaction sidecars' content fidelity: they parse as JSON and the originals are byte-unchanged, but the deltas were not diffed",
    "the source-level meaning of artifact_valid for a repair attempt (only the co-occurrence is observed; the value is the pre-repair check)",
    "the 64 KiB truncation path is still untriggered"
  ],
  "risks": [
    "The runtime's round-game start (DR-70) failed in this round; when that happens the developer prompt still promises 'the runtime publishes that route for the whole round', so the promise and the behaviour disagree exactly when a role believes it",
    "The live route a role sees depends on WHEN in the round it runs: the Developer's call was refused at 04:31 and the Tester's four calls succeeded at 05:02, in the same round, for the same project",
    "A developer call that spends an entire 150-step budget without hitting the launch gate produces artifact_valid=true, so the gate cannot distinguish 'a usable project' from 'a project the model stopped improving'",
    "usage_from_attempts counts redaction sidecars, so any round-level cost or ablation comparison that uses result.json.usage is inflated for every role with a sidecar (measured for planner in t12 and t13)",
    "The role note this round injected under .hoh/ reached the live workspace, but the round-book text that promised the game route was already false for the whole window it was written in",
    "The evidence bundle (106 files) was copied into runs/smoke-t13/evidence after the round closed, so runs/smoke-t13's own digest necessarily changed; the ten read-only baselines are the ones with the three-way proof"
  ],
  "honest_disclosure": [
    "The first hoh run of this round aborted instantly (exit 2) because runs/smoke-t13 already existed from pre-round staging; nothing ran and no project byte was written. The round was then run exactly once.",
    "The role-note injector crashed on a %-format bug on its first attempt and left a 0-byte .hoh/ROLE_NOTE-t13.md in the live workspace; the note was rewritten as UTF-8 by a fixed script at 04:19.",
    "I censused the live game-route calls while the round was still running and therefore undercounted the Tester: the in-flight snapshot showed tester.attempt1 with 85 executed commands and 0 running_game_* calls, while the FINAL artifact of the same file shows 134 executed commands and 4 running_game_* calls, all successful. The runtime enriches a trajectory after the role returns, and my in-flight number was wrong. The numbers in this report are all recomputed from the final artifacts.",
    "The Developer's live running_game_get_scene_tree call was refused (exit 5, DR-43) because DR-70's round-game start had already failed; that refusal sits next to the Tester's four successes and the two together are the round's live-route evidence.",
    "Battery pass 1 was quarantined by pass 2; its raw payloads are kept under runs/smoke-t13/quarantine/ and were used here.",
    "Three .tmp_*.json files the developer left in the repository root (F:\\moonbit-hof-rs) are still there; they are untracked, listed by result.json.out_of_tree_writes, and were left in place rather than deleted.",
    "Fresh-t12 is 109 files now while the T12 report's baseline table recorded 100; smoke-t12's newest mtime is 03:37:43 while that table says 03:31. Both changes are consistent with T12's own round-end copy (nine files) and its post-report redaction copies, not with a write by this round - this round's three-way digest is identical.",
    "No push was attempted; origin/master is untouched. The only commit of this round carries the report."
  ]
}
```

SELF-CHECK: fences=64 json_block_count=1 FENCE_AWARE_JSON_LEGAL=PASS BYTE_IDENTICAL_TO_machine_block.json=True


## 附：证据索引（每个文件都在盘上，附字节数与 sha256；由脚本生成）

生成脚本 `runs/smoke-t13/evidence/scripts/build_evidence_block.py`；每条都给字节数与 SHA-256，
任何被引用的文件都可以按表核对存在性与内容。

**pre-round preflight and the empty-directory proof**

| 文件 | 字节 | sha256（前 16） |
|---|---|---|
| `runs/smoke-t13/evidence/round/empty_proof.txt` | 1192 | `160f6aae58f3cc64` |
| `runs/smoke-t13/evidence/round/preflight_doctor.txt` | 1895 | `4c4701682239a70e` |
| `runs/smoke-t13/evidence/round/preflight_port.txt` | 565 | `e871ea11dca52be4` |
| `runs/smoke-t13/evidence/round/README_STAGING.txt` | 888 | `14996f432b5b8339` |

**engine launch, role gate and editor identity**

| 文件 | 字节 | sha256（前 16） |
|---|---|---|
| `runs/smoke-t13/evidence/gatecheck/game-role-console.txt` | 878 | `0679c7c25f4caf8d` |
| `runs/smoke-t13/evidence/gatecheck/game-role-launch_meta.txt` | 695 | `b2cef72b9ceb7f68` |
| `runs/smoke-t13/evidence/gatecheck/game-role-tools_list.json` | 31359 | `7f13c01136acb4f1` |
| `runs/smoke-t13/evidence/gatecheck/game-role-editor_status.json` | 289 | `d695f3319eb47f23` |
| `runs/smoke-t13/evidence/round/editor_console_launch.txt` | 698 | `24e66eea13e1cab6` |
| `runs/smoke-t13/evidence/round/editor_launch_meta.txt` | 340 | `1b7c101a5076a32f` |
| `runs/smoke-t13/evidence/round/editor_tools_list.json` | 56691 | `081dccb4cce5398a` |
| `runs/smoke-t13/evidence/round/scope_project_list_scripts.json` | 305 | `edcaf882f57b44fc` |
| `runs/smoke-t13/evidence/round/scope_project_filesystem_tree.json` | 9892 | `4781303dd00b3bf6` |

**init, the single run, the aborted launch, note injection**

| 文件 | 字节 | sha256（前 16） |
|---|---|---|
| `runs/smoke-t13/evidence/round/init.txt` | 473 | `9c2f8bb98620f359` |
| `runs/smoke-t13/evidence/round/init_tree.txt` | 540 | `30bbe9477fa33e07` |
| `runs/smoke-t13/evidence/round/round_console.txt` | 1990 | `9866bcdae7678e38` |
| `runs/smoke-t13/evidence/round/round_console2.txt` | 2131 | `385e5e36356b530f` |
| `runs/smoke-t13/evidence/round/role_note_injection.txt` | 213 | `e44b8054135a1e80` |

**read-only baseline digests (three measurement times)**

| 文件 | 字节 | sha256（前 16） |
|---|---|---|
| `runs/smoke-t13/evidence/round/baseline_before_repo.txt` | 1048 | `6b3a91fcf8900cf6` |
| `runs/smoke-t13/evidence/round/baseline_before.txt` | 1048 | `7dd1d3eccd80e31c` |
| `runs/smoke-t13/evidence/round/baseline_before_legacy.txt` | 1048 | `fc87ec2726b10fdf` |
| `runs/smoke-t13/evidence/round/baseline_after_repo.txt` | 1048 | `6b3a91fcf8900cf6` |
| `runs/smoke-t13/evidence/round/baseline_after_evidence.txt` | 1048 | `6b3a91fcf8900cf6` |

**analysis outputs (all written as explicit UTF-8)**

| 文件 | 字节 | sha256（前 16） |
|---|---|---|
| `runs/smoke-t13/evidence/analysis/round_facts.txt` | 11457 | `4e9417167087b825` |
| `runs/smoke-t13/evidence/analysis/battery_reads.txt` | 52743 | `403b8b752e5a40d9` |
| `runs/smoke-t13/evidence/analysis/game_route_calls.txt` | 4204 | `1fa2c1fdcb9a5b19` |
| `runs/smoke-t13/evidence/analysis/called_tools_census.txt` | 4845 | `b1b6e26fc4622f60` |
| `runs/smoke-t13/evidence/analysis/usage_cmp.txt` | 3527 | `ad51fda9020da4d4` |
| `runs/smoke-t13/evidence/analysis/usage_attribution_t12.txt` | 545 | `12e243492623fd71` |
| `runs/smoke-t13/evidence/analysis/usage_attribution_t13.txt` | 544 | `382c728c958c768c` |
| `runs/smoke-t13/evidence/analysis/publish_readiness.txt` | 4672 | `58445e525ce94901` |
| `runs/smoke-t13/evidence/analysis/a0a1_diff.txt` | 925 | `4c567d43ddb5f92a` |
| `runs/smoke-t13/evidence/analysis/anchor_check.txt` | 1267 | `0c8ab2a30ace6a30` |
| `runs/smoke-t13/evidence/analysis/anchor_calibration.txt` | 17816 | `a1b0b06ebf216c4a` |
| `runs/smoke-t13/evidence/analysis/tool_census_game_role.txt` | 3700 | `b3fb92d02301453a` |
| `runs/smoke-t13/evidence/analysis/tool_census_editor_role.txt` | 1523 | `64f134c9a533b90a` |
| `runs/smoke-t13/evidence/analysis/token_totals.txt` | 370 | `94b34c092a8f4882` |
| `runs/smoke-t13/evidence/analysis/epochs.txt` | 2513 | `c16990eed6698c3f` |
| `runs/smoke-t13/evidence/analysis/utf8_scan.txt` | 213 | `7ce3eaac4ce47693` |
| `runs/smoke-t13/evidence/analysis/utf8_scan_round.txt` | 218 | `85d5af5f98761cf8` |
| `runs/smoke-t13/evidence/analysis/text_digest_caliber.txt` | 822 | `0ac7cd55a4659586` |
| `runs/smoke-t13/evidence/analysis/machine_block.json` | 34699 | `36e34d0d04369206` |
| `runs/smoke-t13/evidence/analysis/json_block_check.txt` | 333 | `939b414e14f36c0a` |
| `runs/smoke-t13/evidence/analysis/cite_check.txt` | 18189 | `4bbce1a00a26101c` |

**round artifacts produced by the runtime**

| 文件 | 字节 | sha256（前 16） |
|---|---|---|
| `runs/smoke-t13/meta.json` | 2438 | `cdc982baf42c2db8` |
| `runs/smoke-t13/warnings.log` | 1849 | `d8957bf3e09f34b4` |
| `runs/smoke-t13/versions/index.json` | 832 | `b60667bd39bce929` |
| `runs/smoke-t13/iter-1/result.json` | 7811 | `a7d5fa93e519e7b0` |
| `runs/smoke-t13/iter-1/usage.json` | 2696 | `2edfd39fd914c7c2` |
| `runs/smoke-t13/iter-1/evidence.json` | 21656 | `a2c6e5c42e55d058` |
| `runs/smoke-t13/iter-1/qa_report.md` | 2114 | `c84e0a92621386bf` |
| `runs/smoke-t13/iter-1/plan.md` | 2448 | `9c729ba725128e0b` |
| `runs/smoke-t13/quarantine/deterministic-pass-1.stale-1790888078/raw/play_scene_ready.json` | 1503 | `c6dffa3e74933904` |
| `runs/smoke-t13/quarantine/deterministic-pass-1.stale-1790888078/mcp-errors.jsonl` | 13353 | `2a794ce917c893b8` |
| `runs/smoke-t13/iter-1/candidate/.hoh/deterministic/battery.json` | 9029 | `d12a70c7120ea74c` |
| `runs/smoke-t13/iter-1/candidate/.hoh/deterministic/raw/interaction_evidence.json` | 85834 | `6f701a73fc31f930` |
| `runs/smoke-t13/iter-1/candidate/.hoh/deterministic/raw/input_replay.json` | 128012 | `7d5e171e455fac65` |
| `runs/smoke-t13/iter-1/traj/developer.attempt2.json` | 648164 | `6c072fcc423f149c` |
| `runs/smoke-t13/iter-1/logs/developer.attempt2.log` | 595 | `c27d299a764c4735` |

索引内文件总数 = **59**；表内列出但**不存在**的路径 = **0**（[]）
