# TASK-SMOKE-T11-REPORT — 真机轮：**在真正全新的空工程上 `hoh init` + `hoh run`**，六条判据逐条判定；四项新机制首次真机读数（三项绿、一项红）

- 任务书：`.spec/hof-rs/tasks/TASK-SMOKE-T11.md`（本轮）+ `TASK-SMOKE-T8.md`（基准任务书，仍全效）
- 报告人：**真机轮执行子代理（无上游对话上下文）**；落点：`F:\moonbit-hof-rs`
- 本轮命令（**恰好一轮，无重试**）：
  - `target/release/hoh.exe init  --project F:\moonbit-hof-rs\.workspace\fresh-t11`
  - `target/release/hoh.exe init --fresh-workspace --project F:\moonbit-hof-rs\.workspace\fresh-t11`
  - `target/release/hoh.exe run --iterations 1 --run-id smoke-t11 --fresh-workspace --project F:\moonbit-hof-rs\.workspace\fresh-t11`
- **本轮选定的新目录**（§1.1 要求声明）：**`F:\moonbit-hof-rs\.workspace\fresh-t11`**（工程根）
- 轮记录目录：`runs/smoke-t11/**` —— 运行时自己写出的轮记录为 **124 文件**（newest `2026-10-02 00:29:22`，即 `postrun_state.txt` 的 `RUN_DIR_FILE_COUNT=124`）；本轮另在其中自建 `evidence/**` 后，整个目录为 **186 文件**（`2026-10-02 00:37:24` 实测）。原始取证放在 `runs/smoke-t11/evidence/**`（见 §10）
- 墙钟：`23:50:36 → 00:29:22` = **38m46s**；`ROUND_EXIT=0`；tokens **17,876,780**（三方 `usage_known=true`）
- 引擎身份（**判据**）：`4.8.dev.mono.custom_build.035edfce7`（`--version` 逐字；sha256 `08483088…e9e6a` 仅记录）
- **测量期**（`postrun_state.txt`，00:29:34）HEAD = 收工 HEAD = `4558ba60ab88b607c36aecb58a3530654344584e`；`origin/master` = `47eee038…ab0b`（**ahead，未 push**，闸门武装且未尝试推送）。
  本报告自身的提交落在此之后（`docs(smoke-t11): … (SMOKE-T11)`，只新增本报告文件）⇒ **最终 HEAD = 本报告的那个提交**（位于 `4558ba6` 之上；其 sha 会随本报告本身的 amend 而变，故此处**不引用**其哈希，只引用提交信息与 `git log -1` 的标题）

---

## 0. 结论摘要

| 判据 | 判定 | 一句话依据 |
|---|---|---|
| **E1** | **met** | 全新空目录（原始清单为空）→ `hoh init`（exit 0）→ `hoh run --fresh-workspace`（`meta.json.start_state.mode="fresh"`）；Planner `Submitted`/`artifact_valid=true`；**Developer 在空脚手架上真写了工程**（`A_0=3ac25f6c…` 3 文件/1727 B → `A_1=04d8ba5a…` 11 文件/8830 B，8 新增 + `main.tscn` 342→4358 B）；Tester `Submitted`/`artifact_valid=true`，合法 `E_1`（7 verified + 14 gap）；退出码 0 **四处**一致。§2 |
| **E2** | **met** | `editor_errors_baseline.count=0`（0 条编译/脚本错误）；`editor_play_scene` `playing=true`，主场景起到 **31 节点**；`editor_stop_scene` `stopped=true`；`artifact_gate={applicable:true,launchable:true,reasons:[]}`（`meta.json` 与 `result.json` 双处一致）。§2.2 |
| **E3** | **not_met（4 类里 2 类成立）** | 左右移动、跳跃**成立**（游戏进程内 4/4 `position:neq` 断言 `passed=true`，逐帧数字自洽）；**"至少 1 个可交互对象"与"终点/胜负"未成立**：`interaction_evidence` 步 `ok=false`（`COIN_NOT_PICKED_UP`、`WIN_BLOCKED_UNDER_MOVE_RIGHT`）。§2.3、§3 |
| **E4** | **met** | `E_1` 7 条 verified，18 条执行记录**逐条 stat 全部存在**（`MISSING=[]`）、记录 `type` 齐备、`candidate_id` 全绑 `04d8ba5a…`；verified∩gap=∅、无重复；14 条 gap 各带 `player_impact`。§2.4 |
| **E5** | **met** | 三棵树**逐字节同一**：`iter-1/candidate` == `versions/04d8ba5a…` == 活体 `.workspace/fresh-t11`（两套口径都给 `04d8ba5a…` / `b33cf818…`）⇒ QA 未改 `A_1`。§2.5 |
| **E6** | **met** | `qa_report.md` 明写 `Status: **partial** - 7 verified claims, 14 gaps`，逐条列出未做到的东西（无墙/敌人/方块/死亡平面；金币 0→1 未观测；胜利未驱动），且**主动拒绝过度声明**（"A supporting observation exists but is not sufficient"）。§2.6 |

**本轮不可判定的判据：无**（E1..E6 均有本轮原始证据）。

### 0.1 §1.4 四项新机制的首次真机读数（速览）

| # | 机制 | 首次真机读数 |
|---|---|---|
| 1 | HUD `Coins:` 经属性工具读到（DR-76 ①） | ✅ **绿**：`interaction:read_/root/Main/HUD/Coins_text` → `{"node_path":"/root/Main/HUD/Coins","properties":{"text":"Coins: 1"},"type":"Label"}`；候选由场景树 `name`/`path` **枚举**、`text` **另经** `running_game_get_node_properties` 读；**0 次** `COIN_COUNTER_UNREADABLE`。§3.1 |
| 2 | `coverage_shortfall_px` 与两类胜负结论**出现在判定行** | ⚠️ **半绿**：判定行 `WIN_BLOCKED_UNDER_MOVE_RIGHT (…) coverage_shortfall_px=Some(6374.999954223633) — the bound is the level or the game logic, not the window's coverage; this conclusion is bounded by the movement direction: the window only holds `move_right` and never jumps …`——**数值确在判定行本身**，且旧名 `WIN_UNREACHABLE_GEOMETRICALLY` **0 次**；但**本轮只走到"仅 `move_right` 下被阻"这一类**，"预算耗尽未到达"（`WIN_UNREACHED_WITHIN_BUDGET`）**本轮没有出现**。§3.2 |
| 3 | 三处退出码读数**同数** | ✅ **绿**：`runs/smoke-t11/exit_code` = 字节 `30 0A`；`meta.json.exit_code` = `0`；`runs/smoke-t11/process_exit_code` = 字节 `30 0A`（**三处全部是落盘工件**，t10 的 T10A-4 缺口已闭合）。§3.3 |
| 4 | 角色 CLI **仍能到达游戏端点**（0 次 `game_endpoint_unavailable`） | ❌ **红**：Tester 真执行 9 条 `hoh tools call`，其中 **3 条 `running_game_get_node_properties` 全部被拒**——`the game process the record names is not running (pid 33536), so the route belongs to an earlier round`。**运行时的拒绝行为本身是正确设计（路由不撒谎、不静默回退）**；缺陷是**发布的游戏路由对"自己 play 场景的角色"是陈旧的**。§3.4、F-T11-1 |

> 六条判据中 E1 这次**不再带 T10A-1 那种限定**：`start_state.mode = "fresh"`，`A_0` 就是**空脚手架**（3 文件/1727 B），与 `.workspace/mario` 的 17 文件/18397 B 无关。判据(1)/C1 的"全新空白工程"条款**本轮成立**。

---

## 1. 环境引导（§2.1 要求，逐步留证）

原始输出：`runs/smoke-t11/evidence/round/prerun_state.txt`、`editor_bootstrap.txt`、`editor_scope.txt`、`editor_console.txt`。
（可复跑脚本：`runs/smoke-t11/evidence/scripts/prerun.sh`、`editor_bootstrap.sh`、`editor_scope.sh`。）

### 1.1 前置三步（顺序执行）

**① `hoh doctor`（打印 `godot.engine_binary` 路径 + size + mtime）**

```
[ok] godot.engine_binary: F:/moonbit-hof-rs/godot-mcp/godot/bin/godot.windows.editor.x86_64.mono.exe (size 194216960 B, mtime 1790641862)
[ok] godot.engine_version: 4.8.dev.mono.custom_build.035edfce7
[ok] tools.mcp: 154 tools available at http://127.0.0.1:9877/mcp
DOCTOR_EXIT=0
```

**② 端口是否已有监听（开工时，原文）**

```
NETSTAT_9877:
  (no listener)
GODOT_PROCS:
  (no godot process)
```

**③ 与任务书预期的差异（必须如实报告）**：任务书/parent 说"预期有活着的编辑器（pid 75204）"。**实测它已经不在**——端口 9877 无监听、全机没有任何 godot 进程。**我没有杀掉它**（我没有对 75204 采取任何动作；它在我开工前就已消失）。⇒ 依 §2.1"若未在跑 ⇒ 必须自己启动"，我自行启动，并**把它指向本轮那个全新工程**（见 §1.3 的 `--path` 说明与 §1.4 的"编辑器工程绑定"证据）。

### 1.2 引擎身份与二进制（记录 vs 判据）

| 项 | 值 | 性质 |
|---|---|---|
| `--version` | `4.8.dev.mono.custom_build.035edfce7` | **判据**（逐字相符；`meta.json.engine.version_string` 同值） |
| path / size / mtime | `…/godot.windows.editor.x86_64.mono.exe` / 194216960 / 1790641862 | 与任务书逐字相同 |
| sha256 | `08483088a4a2772841cd3b4c916b2d45b3cb6255656cf3951598a86fce7e9e6a` | **仅记录**（构建非逐位可复现） |

### 1.3 我启动的编辑器（受管后台任务，记录 pid/cmdline/时间/首次可用证据）

```
LAUNCH (verbatim):
  F:\moonbit-hof-rs\godot-mcp\godot\bin\godot.windows.editor.x86_64.mono.exe -e \
    --path F:\moonbit-hof-rs\.workspace\fresh-t11 --mcp-port=9877
LAUNCH_TIME  2026-10-01 23:49:5x  (managed background job term-28)
LISTENER_PID 22876
$ cmd /c wmic process where processid=22876 get commandline,executablepath /format:list
CommandLine=F:\moonbit-hof-rs\godot-mcp\godot\bin\godot.windows.editor.x86_64.mono.exe -e --path F:\moonbit-hof-rs\.workspace\fresh-t11 --mcp-port=9877
ExecutablePath=F:\moonbit-hof-rs\godot-mcp\godot\bin\godot.windows.editor.x86_64.mono.exe
FIRST_USABLE_EVIDENCE (poll t=3s): [ok] tools.mcp: 154 tools available at http://127.0.0.1:9877/mcp
```

编辑器自身控制台（原始，`editor_console.txt`）：

```
Godot Engine v4.8.dev.mono.custom_build.035edfce7 (2026-09-29 00:01:57 UTC) - https://godotengine.org
OpenGL API 3.3.0 NVIDIA 616.56 - Compatibility - Using Device: NVIDIA - NVIDIA GeForce RTX 4090
[MCP] role=editor configured_port=9877 source=cmdline listen=true
[MCP] listening on 127.0.0.1:9877 (editor=true, tools=154)
[MCP] INFO: MCP server is ready on 127.0.0.1:9877 as the editor process (port source=cmdline, tools=154)
```

监听者镜像路径与 `hoh doctor` 报的路径**一致**（`meta.json.engine.listener = {pid:22876, matches_binary:true}`）。

### 1.4 为什么必须**重新**启动一个编辑器（关键判断，必须记录）

Godot 的编辑器工程由 `--path` **在启动时固定**；177 条契约里**没有任何**"切换编辑器所开工程"的工具（`project_*` 全是读写 *当前* 工程的 `res://`）。
而运行时自己的 `godot.editor_scope` 检查项逐字写着：

```
Confirm manually that the project currently open in the editor is exactly this workspace
(F:\moonbit-hof-rs\.workspace\fresh-t11); the runtime cannot verify it.
```

⇒ 若沿用"开着 `.workspace/mario` 的编辑器"来跑全新工程，则 **MCP 侧观测的是 mario、磁盘侧写的是 fresh-t11**，本轮会变成一场**假轮**。因此本轮的自启动把编辑器**指向新工程**，并**实测证明**编辑器开的确实是新工程：

```
$ python mcp_call.py project_list_scripts '{}'
{"count":0,"scripts":[]}                      ← 新脚手架（0 脚本）
$ python mcp_call.py project_get_filesystem_tree '{}'
res:// 下的非缓存内容 = project.godot / scenes/main.tscn / scripts/README.md  ← 就是 `hoh init` 的产物
（对照：磁盘 .workspace/mario/scripts 有 15 个条目）
```

### 1.5 二进制重建（必要动作，已披露）

`target/release/hoh.exe` 原 mtime `2026-09-30 17:28`，**早于** DR-76/DR-77 的源码提交 ⇒ 它不含本轮必须检验的新机制。故执行
`cargo build --release --offline`（**只编译，未改任何源码**）：

```
Compiling hof-rs v0.1.0 (F:\moonbit-hof-rs)
Finished `release` profile [optimized] target(s) in 16.85s
BUILD_EXIT=0
sha256 d0292a06b19c6dc4ab00bb916ad642ee077161d59882109c44ab986b7a6b4b40  size 12692992
```

---

## 2. E1..E6 逐条判定 + 原始证据

### 2.0 "空目录 → init → run" 三步的原始输出（§1.1 硬性要求）

原始文件：`runs/smoke-t11/evidence/round/fresh_init.txt`、`fresh_init2.txt`。

**(a) 该目录为空（原始 `ls` 输出）**

```
$ ls -la .workspace/fresh-t11
total 0
drwxr-xr-x 1 wyl 197609 0 Oct  1 23:49 .
drwxr-xr-x 1 wyl 197609 0 Oct  1 23:49 ..
$ find .workspace/fresh-t11 -mindepth 1 | wc -l
0
EMPTY_ASSERTION: [ 0 -eq 0 ] => the directory is empty (no files, no dotfiles, no subdirectories)
（prerun_state.txt：WORKSPACE_FRESH_T11_EXISTS=False —— 本轮之前它根本不存在）
```

**(b) `hoh init` 的真实输出**

```
$ target/release/hoh.exe init --project F:\moonbit-hof-rs\.workspace\fresh-t11
init: A0 ready at F:\moonbit-hof-rs\.workspace\fresh-t11 (initialize ran; no MCP, no model endpoint and no key were required)
INIT_EXIT=0
$ find .workspace/fresh-t11 -mindepth 1 | sort
.workspace/fresh-t11/project.godot
.workspace/fresh-t11/scenes
.workspace/fresh-t11/scenes/main.tscn
.workspace/fresh-t11/scripts
.workspace/fresh-t11/scripts/README.md
PROJECT_GODOT_SHA256=00d02c9c08c3dc4fc35e3d9bcc94b06c31d44b42df2f017bc0ca5615a12c0ef4
ADDON_DIR_EXISTS=False
```

（另跑 `hoh init --fresh-workspace`：`init: A0 ready … (workspace emptied, initialize ran; …)`，`INIT_FRESH_EXIT=0`，`project.godot` sha 不变；`.workspace/mario/scripts` 条目数仍 15 ⇒ purge 只作用于配置的工作区。）

**(c) `meta.json.start_state`（不得为 `as_is`）**

```text
"start_state": { "mode": "fresh", "version_id": null }
```

⇒ 运行时的**自己记录的**起点就是 `fresh`；`A_0` 快照 = 上面那份 3 文件脚手架。**T10A-1 的限定在本轮不再适用。**

### 2.1 E1 = met（三个要件 + 整轮）

| 要件 | 原始证据 |
|---|---|
| Planner 产出合法 `D_1` | `iter-1/plan.md`（2879 B）；`logs/planner.attempt1.log`：`exit_status=Submitted`、`artifact_valid=true`、`attempt=1`、`28 calls`；轨迹里 `RepeatedFormatError`=0 |
| Developer 产出**真实工程增量** | `versions/index.json`：`A0 3ac25f6c…`(iteration 0, role init) → `A1 04d8ba5a…`(iteration 1, role developer)；`logs/developer.attempt1.log`：`artifact_valid=true`、`attempt=1`、`142 calls` |
| QA 产出合法 `E_1` | `iter-1/evidence.json`（24822 B，可解析）、`qa_report.md`（3769 B）；`logs/tester.attempt1.log`：`exit_status=Submitted`、`artifact_valid=true`、`attempt=1`（`traj/` 下**只有 `tester.attempt1.json`**，无 attempt2） |
| 整轮 + 退出码 | `runs/smoke-t11/exit_code` 字节 `30 0A`；`meta.json.exit_code=0`；`runs/smoke-t11/process_exit_code` 字节 `30 0A`；wrapper `ROUND_EXIT=0`；`result.json`：`ok=true, failed_role=null, reason="ok", issues=[]` |

**`A_0` 与 `A_1` 的目录名级摘要（运行时自己的 hash 口径，`rel\n{len}\n{bytes}\n`、排除 `{.hoh,.git,.godot,.import}`）**：

```
A0  3ac25f6c5c38885febd3a001ea99c88aca61b1799c7b105306919886c2c1d151   3 files   1727 B
A1  04d8ba5a12899ed8bfc2c04113932983e5db03e8d471717fc3da8b5db9a585c1  11 files   8830 B
```

（自证口径：我这支 `treehash.py` 对 t10 的冻结树复现出 `1f3d20ed…`(17/18397) 与 `ed98d1b8…`(17/21679)，与 `runs/smoke-t10/versions/` 的目录名逐字相同。）

**被改文件清单（我独立 diff）**：

```
ADDED: scripts/{coin,goal,main,player}.gd + 各自的 .uid      （8 个文件）
MODIFIED: scenes/main.tscn   342 B 3c65f6ec5a85 -> 4358 B 813c145720d6
REMOVED: []
```

**非琐碎**：Developer 从**只有 `README.md` 的 `scripts/`** 起手，写出 4 个脚本 + 5 枚金币 + Goal + HUD（31 节点场景），`main.tscn` 从 342 B 长到 4358 B。`result.json.evidence_diff` 与我的 diff **逐条一致**（added 8 / modified 1 / removed 0）。

### 2.2 E2 = met

```
editor_errors_baseline : {"available":true,"count":0,"editor":true,"errors":[],"in_process":true,"log_path":"user://logs/godot.log","pid":22876,"port":9877,"process":"editor","source":"editor_log"}
play_scene_ready       : {"args_injected":["--mcp-port=56727"],"endpoint":"http://127.0.0.1:56727/mcp","mcp_port_source":"auto_free_port","mode":"main","pid":31528,"playing":true}
                         + running_game_get_scene_tree → 31 个节点（Main/Ground/Player/Camera2D/Coin1..Coin5/Goal/HUD{Coins,Lives,Time,Victory}）
editor_stop_scene      : {"message":"Playback stopped","stopped":true}
artifact_gate          : meta.json 与 result.json 两处均为 {"applicable":true,"launchable":true,"reasons":[]}
battery                : 12 步 / 11 ok（唯一 false = interaction_evidence）
```

⇒ **0 条编译/脚本错误**、主场景**可启动**（31 节点）并**干净停止**、闸门因正确原因开启。

### 2.3 E3 = not_met（四类里 2 类成立）—— 逐类裁定

| 行为 | 裁定 | 决定性原始证据（**全部来自游戏进程端点上的语义工具**） |
|---|---|---|
| 左移 | **成立** | `input_replay` move_left 窗口：x `455.999542236328 → 239.666732788086`，Δ=**−216.332809**（59 间隔 ⇒ **−3.6666578 px/帧**）；`running_game_assert_node_state` `passed=true` |
| 右移 | **成立** | move_right 窗口：x `192.000045776367 → 408.333038330078`，Δ=**+216.332993** ⇒ **+3.6666609 px/帧**（×60 = 219.9997 px/s，与 `player.gd` 的 220 自洽）；断言 `passed=true` |
| 跳跃 | **成立** | jump 窗口：y `283.590729 → 234.257355(第 16 帧峰) → 267.479584`，x 恒定 `466.999542236328` ⇒ 纯竖直弧线；断言 `passed=true` |
| **至少 1 个可交互对象** | **不成立** | `interaction_evidence` 步 `ok=false`；判定行 `COIN_NOT_PICKED_UP`（`Coins: 1 -> Coins: 1`），**引擎自己的** `text:neq "Coins: 1"` 断言 `passed=false`（`"reason":"expected text neq Coins: 1, found Coins: 1"`）⇒ `F10` 落 gap |
| **一个终点/胜负条件** | **不成立** | `Goal.reached` 4 次读全为 `false`；Goal 在 `x=6600.0`，判定行记录的 `player max x=225.000045776367`（`coverage_shortfall_px=Some(6374.999954223633)`）；轨迹树里**没有**敌人/方块/死亡平面 ⇒ `F13/F14/F15` 全 gap |

**四条位置断言的原始回包（逐字，`payload.content[0].text` 解出）**：

```
move_right           actual {x:408.333038330078,y:303.925201416016} expected {x:192.000045776367,…} operator=neq property=position passed=true resolved_node_path=/root/Main/Player
move_right_release   actual {x:459.666229248047,…} expected {x:426.666320800781,…} passed=true
jump                 actual {x:466.999542236328,y:267.479583740234} expected {x:466.999542236328,y:283.590728759766} passed=true
move_left            actual {x:239.666732788086,…} expected {x:455.999542236328,…} passed=true
```

**证据形态齐备**：`input_replay.json` 48 次调用（`running_game_*` 39 + `editor_*` 9），每窗口 before/after PNG（8 张，我逐个验 PNG magic `89504e470d0a1a0a`）+ 1 次引擎位置断言；另有 `replay-interaction-{before,after}.png`（共 11 张 PNG，含 `frame-00.png`）。

**关于金币的重要上下文（既不改写判定，也不替产物辩护）**：
- 运行时对计数的**唯一**读数就是 `Coins: 1`；全候选树里 `Coins: 0` **只出现在 `scenes/main.tscn` 的静态默认文本**（`scene_structure` 步其实是 `project_read_scene_file_content`，**不是**运行时读数）。
- 而 `main.gd` 从 `@export var coins: int = 0` 起手，`_ready()` 立即 `update_hud()` 写 "Coins: 0"，**只有** `coin.gd::collect()`（Area2D `body_entered` 且 body 属 "player" 组）才 `add_coin(1)`。
  ⇒ **运行时读到 `Coins: 1`，在代码上意味着本轮的某个窗口确实吃到了一枚金币**；但**本轮没有任何"0→1 的语义工具观测"**（窗口跑的时候计数已经是 1，因为更早的 `input_replay` 窗口已经把它吃掉了）。
- ⇒ 判定仍为 **E3 not_met**（判据要的是**在轮内被观测到**的可交互行为），但"游戏完全不能拾取"这一误读应予排除。

### 2.4 E4 = met（我自己逐条 stat，不看运行时自报）

```
iteration=1  qa_status=partial  verified=7  gap=14
verified_ids = [N1, F1, F2, F3, F4, F5, F16]
gap_ids      = [F1b, F2b, F6, F7, F8, F9, F10, F13, F17, N3, F11, F12, F14, F15]
overlap: []        dup_verified: []
execution_records=18   MISSING=[]            ← 每条 path 都在冻结候选视图里真实存在
record types: [assert, build, replay, runtime_trace, screenshot]     ← 无缺 type
record candidate_ids: [04d8ba5a12899ed8bfc2c04113932983e5db03e8d471717fc3da8b5db9a585c1]  ← 运行时绑定可见
gaps lacking player_impact: []
planner_handoff: preservation_constraints=4 / update_targets=5 / validation_requirements=6
```

### 2.5 E5 = met（三棵树逐字节同一）

```
A1 (versions dir)                 runtime_id=04d8ba5a12899ed8bfc2c04113932983e5db03e8d471717fc3da8b5db9a585c1  files=11 bytes=8830
iter-1/candidate (frozen QA view) runtime_id=04d8ba5a12899ed8bfc2c04113932983e5db03e8d471717fc3da8b5db9a585c1  files=11 bytes=8830
live .workspace/fresh-t11         runtime_id=04d8ba5a12899ed8bfc2c04113932983e5db03e8d471717fc3da8b5db9a585c1  files=11 bytes=8830
（第二口径 report_id 三处同为 b33cf818e41654e24d83e47025cc6a128da816de1fa5c1ac7b00c07a0031f23c）
```

`result.json.candidate_id == version_id == 04d8ba5a…`；剪影 diff `only-in-game [] / only-in-candidate [] / differing []`。

### 2.6 E6 = met（诚实性 = 可核对的内容）

`qa_report.md`（逐字）含：

```
- Status: **partial** - 7 verified claims, 14 gaps.
## What remains open (gaps)
Battery step interaction_evidence is **ok=false (UNAVAILABLE)**, so every claim that depends on it is a gap: …
F6 wall blocking, F7 patrol, F8 contact damage, F9 stomp, F11 question block, F12 breakable brick, F14 failure, F15 restart:
  … the scene file and running tree contain no wall, enemy, block or kill plane at all, so these behaviours are absent rather than merely unobserved.
```

并且**主动拒绝把弱观测当结论**："A supporting observation exists but is not sufficient … The 0 -> 1 transition and the coin leaving the tree still need a clean observation."
⇒ **未达成被声明，未谎报为 verified**。

---

## 3. §1.4 四项新机制的首次真机读数（逐条，含原始回包/判定行原文）

原始文件：`evidence/analysis/interaction_detail.txt`、`interaction_verdict_line.txt`、`interaction_summary.txt`、`endpoint_refusals.txt`、`timeline_tester.txt`。

### 3.1 ① HUD `Coins:` 经属性工具读到 —— **绿（DR-76 ① 在真机成立）**

`interaction_evidence.json` 的调用序列（原始）：

```
[ 0] running_game_get_node_properties  label=interaction:read_/root/Main/HUD/Coins_text  ok=True
     {"node_path": "/root/Main/HUD/Coins", "properties": {"text": "Coins: 1"}, "type": "Label"}
[ 1] running_game_get_node_properties  label=interaction:read_Goal_reached     ok=True
     {"node_path": "/root/Main/Goal", "properties": {"reached": false}, "type": "Area2D"}
[ 3] running_game_get_node_properties  label=interaction:read_Goal_position   ok=True
     {"node_path": "/root/Main/Goal", "properties": {"position": {"x": 6600.0, "y": 280.0}}, "type": "Area2D"}
```

判定行里运行时自己写下了发现路径（逐字）：

```
interaction: HUD counter candidates (from the scene tree's `name`/`path` only; each text read through
`running_game_get_node_properties`) = ["/root/Main/HUD/Coins", "/root/Main/HUD/Lives", "/root/Main/HUD/Time", "/root/Main/HUD/Victory"];
interaction: before readings coin=Some("Coins: 1") goal.reached=Some(Bool(false)) goal.position=Some(Object {"x": Number(6600.0), "y": Number(280.0)});
```

计数（我数）：本窗口 `running_game_get_node_properties` **7 次**、`capture_screenshot` 2 次、create/play/stop 各 3 次、`get_node_property_samples` 3 次、`run_test_scenario` 3 次、`assert_node_state` 1 次 = **25 次调用**。
**`COIN_COUNTER_UNREADABLE` 出现 0 次** ⇒ DR-76 ① 修的正是"真引擎只发 `name`/`path`/`type`"这条，**真机已验证可读**。

### 3.2 ② `coverage_shortfall_px` 与两类胜负结论出现在判定行 —— **半绿**

**判定行原文**（`record-08.json` / `battery.json`，我按 `verdict_line` 的形态区分；这里给出**判定行本身**）：

```
interaction: WIN_BLOCKED_UNDER_MOVE_RIGHT (goal.reached stayed false and the sampled player x did not advance
over 2 consecutive batch(es) of `move_right` while 127 batch(es) of the 130-batch budget were still unspent;
player max x=Some(225.000045776367), goal.position=Some(Object {"x": Number(6600.0), "y": Number(280.0)}),
coverage_shortfall_px=Some(6374.999954223633) — the bound is the level or the game logic, not the window's
coverage; this conclusion is bounded by the movement direction: the window only holds `move_right` and never
jumps, so it says nothing about whether a jump or another input could pass)
```

- **短额数值确在判定行本身**（不是只在"驱动行"里）：驱动行同样带 `coverage_shortfall_px=Some(6374.999954223633)`，两处同值 ⇒ DR-77 ② 的"钉住"在真机形态下成立。
- **DR-77 ③ 的改名生效**：`WIN_BLOCKED_UNDER_MOVE_RIGHT` 出现，旧名 `WIN_UNREACHABLE_GEOMETRICALLY` **0 次**，且判定行自带限定语（"the window only holds `move_right` and never jumps"）。
- **两类结论本轮只走到一类**：`WIN_BLOCKED_UNDER_MOVE_RIGHT`（3/130 批、127 批未花）。**`WIN_UNREACHED_WITHIN_BUDGET` 本轮没有出现**（预算根本没被耗尽）⇒ 该类结论在本轮**没有真机证据**，我不替它借证据。
- **一项来自我的独立读数（本次轮的重要副作用）**：该窗口三个批次的采样 **x 全部是 `225.000045776367`**（3×60 帧**逐位相同**），而同轮 `input_replay` 的四个窗口在同一候选上分别移动了 216.33/33.00/0/216.33 px。判定行自己也写"stopped after 2 batch(es) without forward progress"。⇒ **`WIN_BLOCKED_UNDER_MOVE_RIGHT` 是对"当前这一次驱动没有推进"的诚实读数**，但**它在这一轮里不能区分"关卡挡路"与"驱动没生效"**（该窗口里 `editor_simulate_input_action` 调用数 = **0**，而 `input_replay` 里有 **8** 次；注入记录只有 `pressed` 事件、时长 ~40 ms）。这一条我**只作为读数与推断分开列**（见 F-T11-2 与 §7）。

### 3.3 ③ 三处退出码读数同数 —— **绿**

```
$ xxd runs/smoke-t11/exit_code
00000000: 300a                                     0.
meta.json                : "exit_code": 0
$ xxd runs/smoke-t11/process_exit_code
00000000: 300a                                     0.
wrapper                  : ROUND_EXIT=0
result.json              : "ok": true, "failed_role": null, "reason": "ok", "issues": []
写盘次序（mtime）：result.json 00:29:22.569 < exit_code .6289 < process_exit_code/meta.json .6305
```

⇒ **三处落盘工件全部存在且同数（0）**，另有 wrapper 的第四处一致 ⇒ T10A-4（第三处不在冻结件里）**已闭合**。

### 3.4 ④ 角色 CLI 仍能到达游戏端点 —— **红：3 次 `game_endpoint_unavailable`**

我按"**真正执行的命令** × 其 tool result"配对（脚本 `cli_pair.py`，用 `assistant.extra.actions[*].command` + `tool_call_id`）：

```
planner : executed bash 29,  hoh tools call 0
developer: executed bash 201, hoh tools call 98   (editor_*/project_* 全部；running_game_* = 0)
           → PAYLOAD 91 / ENDPOINT_REFUSED 0 / other 7
tester   : executed bash 125, hoh tools call 9    (editor_play_scene 3, editor_get_scene_tree 2, editor_stop_scene 1,
                                                    running_game_get_node_properties 3)
           → PAYLOAD 6 / ENDPOINT_REFUSED 3 / other 0
```

三次拒绝的**原始回包**（逐字）：

```
hoh: game_endpoint_unavailable: `running_game_get_node_properties` runs in the game process and only the game
endpoint serves it; the published route was found and **refused**: the game process the record names is not
running (pid 33536), so the route belongs to an earlier round. No request was sent, so this is an explicit
refusal, not a transport failure. Falling back to the editor endpoint is not allowed (DR-43).
```

时间线（我自轨迹 `extra.timestamp` 重建，`analysis/timeline_tester.txt`）：

```
00:12:40 tester  editor_play_scene                  → "hoh: could not find config file for config/hoh.yaml"（cwd 不对，非路由问题）
00:13:37 tester  editor_play_scene                  → {"mcp_port":57449,"pid":4508,"playing":true}
00:13:40 tester  running_game_get_node_properties   → REFUSED (route names pid 33536)
00:13:42 tester  type runs\smoke-t11\game_endpoint.json → {"endpoint":"http://127.0.0.1:56821/mcp","port":56821,"pid":33536}
00:16:35 tester  running_game_get_node_properties   → REFUSED
00:17:06 tester  editor_stop_scene
00:18:10 tester  editor_play_scene                  → {"mcp_port":57902,"pid":4784,"playing":true}
                    同一行 type 仍显示 route = 56821/33536       ← 路由**没有**随 play_scene 刷新
00:18:12 tester  running_game_get_node_properties   → REFUSED
```

- **运行时侧行为是正确的**：路由"发现但被拒 + 不静默回退编辑端点"（DR-43/DR-71 的"路由永不撒谎"）；它**没有**撒谎，也**没有**降级。
- **缺陷在别处**：角色自己 `editor_play_scene` 起的新游戏（57449/4508、57902/4784）**不会**更新 `runs/<id>/game_endpoint.json`，而 `meta.json.engine.mcp.game_endpoint` 记录的仍是**电池那一次**的游戏（**56727 / pid 31528**）。⇒ 任何"自己 play 场景再读数"的角色都会撞上陈旧路由。
- 影响面：**电池**的游戏端点读数不受影响（其 raw 载荷都是活游戏进程里的语义工具回包，`channel=game_process`）；受影响的只是 **Tester 的现场 CLI 追问**（它的 3 次 live 追问全部被拒，于是只能引用电池 raw）。⇒ 这也解释了 §1.4-4 的"红"。

---

## 4. 产出工程的身份（A_0 / A_1 摘要、文件数/字节数、被改文件）

见 §2.1。汇总：

| 记号 | 运行时 id（= versions 目录名） | 我的 report 口径 id | 文件数 | 字节数 |
|---|---|---|---|---|
| **A_0**（`hoh init` 的空脚手架） | `3ac25f6c5c38885febd3a001ea99c88aca61b1799c7b105306919886c2c1d151` | `ef369f272a4ceab0130bb00682caaf1acaed4043d72abe227fc0b27193545e01` | 3 | 1727 |
| **A_1**（Developer + 电池后的冻结候选） | `04d8ba5a12899ed8bfc2c04113932983e5db03e8d471717fc3da8b5db9a585c1` | `b33cf818e41654e24d83e47025cc6a128da816de1fa5c1ac7b00c07a0031f23c` | 11 | 8830 |
| `iter-1/candidate` = 活体工作区 | 同上 `04d8ba5a…` | 同上 `b33cf818…` | 11 | 8830 |

`A_1 != A_0`（摘要不同、文件集不同、非琐碎，见 §2.1 的 8 新增 + 1 修改）；差异**全部落在 Developer 产出的工程文件**上（`scripts/**`、`scenes/main.tscn`），**没有**落在 `.hoh/**`、`runs/**` 这类被排除路径。

---

## 5. 只读基线的未变证明（内容 / count / mtime 三口径自证）

口径 = 本仓既往口径（PowerShell 5.1 `Get-ChildItem -Recurse -Force -File`；仓根相对**小写**路径 + 字节长 + SHA256；`\t` 连接、`\n` 分行、无尾随换行；行序 **`Sort-Object` 文化排序**；整体 UTF-8 取 SHA256）。脚本：`evidence/scripts/baseline_digest.ps1`（可复跑）。

```
=== BASELINE DIGESTS (before) : 2026-10-01 23:48:43 ===        === BASELINE DIGESTS (after) : 2026-10-02 00:29:42 ===
.workspace\mario 178  dee0a36f357c440d078c652d4d4b8990af1a63b88d282c1e36c04a16d006cc94  newest 2026-09-30 18:23:08
runs\smoke-t6    135  c144ef3219e21dd322978e41a5531d53dee270619c026585505920f9277a9c03  newest 2026-09-29 02:32:01
runs\smoke-t7    115  6e4c1595753c2cdefb16e4d2e5f05242ca202c70c81a93e98ae2b9c92b520fb7  newest 2026-09-29 14:41:14
runs\smoke-t8    358  6d11b2c61ec507b5f02525ddc0e7f7adb08763cd2439a4b08788b7fe51bdf5a7  newest 2026-09-30 07:58:28
runs\smoke-t9     83  541e2d814e563ba667c95bde49765d05e44cf11aa5ab90b2f44931f30136ca9d  newest 2026-09-30 11:27:29
runs\smoke-t10   232  319555896964ce1526f72a33cb239bf389fe29bcde23841764d13c57dfb38b8b  newest 2026-09-30 18:23:08
```

**开工 / 收工逐字相同（六条全中，含任务书要求的自证值 `smoke-t6 = c144ef32…7a9c03`）**，且 `newest` mtime 也未变 ⇒ 内容与 mtime 两口径都未动。
`mario` 这份摘要是**含 `.godot` 缓存的整树**（178 文件）——**我的编辑器从未打开过 mario**，所以连缓存都没被碰。
`.workspace/fresh-t11` 是本轮**新目录**（开工不存在），它与 t6..t10 都在只读清单之外。

---

## 6. 机制读数（零增量 / 崩溃 / 修复尝试 / 64 KiB / 闸门 / 陈旧日志 / 端点 / 脱敏 / evidence_diff）

原始：`evidence/analysis/mechanisms.txt`、`traj_scan.txt`、`cli_*.txt`、`postrun_state.txt`。

| 机制 | 本轮真实读数 |
|---|---|
| **零增量** | **未发生**。`warnings.log` 全文 2 行（`qa_scope…`、`frozen evidence kept in place…`），**不含** `Zero-increment`、`no_progress`、`no_engineering_write`；`A_1≠A_0` |
| **崩溃** | **无**。exit 0；`out_of_tree_writes=[]`；`artifact_hygiene={suspicious_files:[],suspicious_directories:[]}`；工程里**没有** `-p` 之类残留目录（t10 的 F-T10-5 未复现） |
| **修复尝试** | **无**。`repair_retry_used=false`；`wrap_up_retry_used=false`（`reason="not_triggered"`）；三角色各 **1 次 attempt**（`traj/` 无 attempt2/3）；`battery_passes` 长度 **1**；warnings 无 `launch_gate_repair`；无 `quarantine/`（新目录本来就没有上一轮的 `.hoh` 可隔离） |
| **64 KiB 上限** | **本轮未被触发**（不是"没生效"）：四条轨迹 `hoh_output_truncated` **0 次**；最大单条 tool content = **45,486 B**（tester），最大整条消息序列化 = **102,475 B** ⇒ 无输出越过 65,536 B 阈值。⇒ **本轮不能给出"截断行为"的真机读数** |
| **闸门** | 被评估且**因正确原因开启**：`{applicable:true, launchable:true, reasons:[]}`（`meta.json` 与 `result.json` 双处）；电池 12 步 11 ok |
| **陈旧日志** | `editor_errors_baseline.count=0`（连 t10 那条信息性 banner 都没有）⇒ 无"过期编辑器日志关门"可触发，也无需触发 |
| **端点可达** | **3 次 `game_endpoint_unavailable`**（§3.4 / F-T11-1）——**这是本轮唯一的机制级红读数** |
| **脱敏（F-T10-1 家族）** | **不再复现**：4 个轨迹文件（含 `tester.attempt1.json`）**全部是合法 JSON**（`json.loads` 通过）；脱敏改为**旁路产物** `developer.attempt1.redacted.json`（8 处 `<redacted>`，1084030 B），**原件 `developer.attempt1.json` 逐字节保留**（1084125 B）；`warnings.log` 明写 `frozen evidence kept in place; the redacted form was generated as developer.attempt1.redacted.json (the original is byte-unchanged, DR-72 ②)` |
| **`evidence_diff`（t10 F-T10-3）** | **本轮非空且正确**：`{"added":["scripts/{coin,goal,main,player}.gd","….gd.uid"],"modified":["scenes/main.tscn"],"removed":[]}`，与我的独立 diff 一致 |
| **角色格式摩擦** | Developer 以 `exit_status=RepeatedFormatError` 收场（142 calls、`artifact_valid=true`、**无第二次 attempt**）；`No tool calls found` 出现 planner 2 / developer 9 / tester 9 次；**全轮 0 处 `schema_failure`**。⇒ "达到格式错误上限"本轮**被容忍**（因 `artifact_valid=true`），与 t8 的 tester 拒收形成对照（见 §7 推断） |

---

## 7. "判据观测到" vs "我们观测到"（严格区分，§1.5 要求）

| 事实 | 谁观测到 | 证据形态 |
|---|---|---|
| HUD 计数 1、Goal.reached=false、GOAL position x=6600 | **判据（运行时/电池）** | 游戏进程端点语义工具 `running_game_get_node_properties`，落在 `interaction_evidence.json` |
| 左右移动、跳跃（4 窗口、4/4 断言通过） | **判据** | `input_replay.json` + 8 张 PNG + 引擎 `assert_node_state` 回包 |
| `COIN_NOT_PICKED_UP` / `WIN_BLOCKED_UNDER_MOVE_RIGHT` / `coverage_shortfall_px` | **判据** | `battery.json` / `deterministic.json` / `record-08.json` 的判定行 |
| `Coins: 1` 意味着"确实吃到过一枚金币" | **我**（读 `main.gd`/`coin.gd` 的代码后推断 + 计数读数） | 代码 + 上方读数；**不是**判据的结论（判据只说"没观测到 0→1"） |
| 交互窗口 180 个采样 x 逐位相同 ⇒ 那一次驱动没有推进 | **我**（逐样本重算 + 调用清单对比） | `evidence/analysis/input_replay_frames.txt`、`interaction_detail.txt` |
| 路由陈旧（play_scene 不刷新 `game_endpoint.json`） | **我**（轨迹时间线 + 路由文件内容） | `evidence/analysis/timeline_tester.txt`、`endpoint_refusals.txt` |
| 编辑器开的是新工程 | **我**（MCP `project_list_scripts`/`project_get_filesystem_tree` + cmdline） | `evidence/round/editor_scope.txt` |

---

## 8. 遗留风险与未验证项（严格区分实测 / 推断）

**实测（本轮有原始证据）**

1. **全新空工程条款成立**：空目录清单 + `hoh init` exit 0 + `start_state.mode="fresh"` + `A_0` = 3 文件脚手架。
2. E1 met（`A_0≠A_1`、8 新增/1 修改、`E_1` 被接受、整轮 exit 0 四处一致）；E2/E4/E5/E6 met；E3 not_met（2/4 类）。
3. **§1.4 逐条**：①绿（计数经属性工具读到）；②半绿（数值在判定行、改名生效、只走到一类）；③绿（三处退出码同数且都落盘）；④**红**（3 次端点拒绝）。
4. developer 轨迹**合法 JSON** + 旁路 `*.redacted.json` + 原件逐字节保留 ⇒ F-T10-1 未复现。
5. `evidence_diff` 非空且与我的 diff 一致 ⇒ t10 的 F-T10-3 在本轮产物上闭合。
6. 六条只读基线（含 mario 含缓存的 178 文件整树）内容与 mtime **开工=收工**。
7. 无零增量、无修复尝试、无孤儿游戏进程；编辑器 22876 存活；PRD / DECISIONS / 嵌套引擎 / 外层 HEAD 均未变。
8. **64 KiB 上限本轮未被触发**（最大 tool content 45,486 B）。

**推断（不得当作已测）**

1. **（≈0.85）** `Coins: 1` 意味着本轮真的吃到了一枚金币——依据是 `main.gd` 的 `coins=0` 初值与唯一的 `add_coin(1)` 调用点；我**没有**在轮内观测到 `0→1`，也没有逐帧抓到金币节点消失。
2. **（≈0.75）** 交互窗口"零推进"很可能来自**驱动没生效**（该窗口 0 次 `editor_simulate_input_action`，而 `input_replay` 有 8 次；注入记录只有两次 `pressed` 事件、时长 ~40 ms），而**不是**关卡挡路。机制归因未做端到端复现。
3. **（≈0.7）** 路由陈旧的触发条件 = "角色自己 `editor_play_scene`" （该路径不 publish 路由），而运行时的轮级/电池级 publish 正常；我没有读 publish 代码逐行确认，只从 3 次拒绝 + 路由内容 + 时间线推断。
4. **（≈0.6）** Developer 的 `RepeatedFormatError` 被接受（因为它 `artifact_valid=true`）属"有意的宽松"还是"未覆盖分支"，我未从源码确认。

**未闭合（应回上游，本报告不修）**

1. **F-T11-1（major）**：游戏路由对"自己 play 场景的角色"陈旧 ⇒ 角色 live CLI 不可用（§3.4）。
2. **F-T11-2（major）**：`interaction_evidence` 窗口在真机上**可能根本没驱动**（180 样本逐位相同、无 editor 侧注入）⇒ 其 `COIN_NOT_PICKED_UP`/`WIN_BLOCKED_UNDER_MOVE_RIGHT` 目前**不能证明任何关于游戏的事**，只能证明"这一次没动"。
3. **F-T11-3（major，判据侧）**：`input_replay` 会先吃掉金币，导致后续 `interaction_evidence` **无法再看到 0→1** ⇒ F10 在本轮结构上**不可能成立**（窗口顺序决定的假阴性）。E3 的产品缺口与"证据形态的假阴性"应分开处理。
4. **F-T11-4（minor）**：`WIN_UNREACHED_WITHIN_BUDGET` 一类结论**本轮无真机证据**。
5. **F-T11-5（minor）**：64 KiB 截断路径本轮未被触发 ⇒ 仍然是"离线测试覆盖、真机未验"。
6. **F-T11-6（info）**：`scene_structure` 是静态 `project_read_scene_file_content`，F16 的 `Coins: 0` 因此是**场景默认文本**而非运行时读数（本轮 E4 不受影响，但容易被误读为"运行时读到 0"）。

---

## 9. 诚实披露

1. **只跑了这一轮**（`23:50:36 → 00:29:22`，单次 `hoh run`）。**无重试、无 attempt-A/B、无删除重建**；`runs/smoke-t11` 是本轮全新目录。
2. **编辑器是我启动的**（pid 22876，受管后台任务 `term-28`）：开工时**没有任何 godot 进程、9877 无监听**（任务书预期的 75204 已不在，**我没有杀它**）。**收工时我让它继续存活**（只读检查：`9877 LISTENING → 22876`；全机仅此一个 godot 进程）。
3. **我没有启动任何游戏进程**，也没有孤儿游戏进程需要清理（`editor_stop_scene` 已由剧本/角色完成；收工全机无游戏进程）。**因此没有 `editor_stop_scene` 原始回包需要我补记**——那是运行时的，本报告引用的是它的落盘件。
4. **我做过的机器动作**：`cargo build --release --offline`（重建 2 个二进制之一）、`mkdir`/`rmdir`、启动编辑器、只读进程/端口/文件检查、以及本轮的一轮 `hoh run`。
5. **一次意外写入，已清除并披露**：开工时我误在 `runs/smoke-t11/evidence/{scripts,round,analysis}` 下建了 3 个**空目录**，随即用 `rmdir` 删除（**只删空目录**，删完 `runs/` 下无 t11 条目），以保证 `hoh run` 的"run 目录必须不存在"前置成立。**基线零字节写入；全程绝未使用 `rm -rf`，绝未从未展开变量构造路径。**
6. **本轮全部新增产出**只落在：`.workspace/fresh-t11/**`（被开发工程）、`runs/smoke-t11/**`（轮记录 + `evidence/**`）、`F:\moonbit-hof-rs\.spec\hof-rs\tasks\TASK-SMOKE-T11-REPORT.md`（本报告），以及 `.gitignore` 覆盖的 `target/`（编译产物）。
7. **我没有改** `src/**`、`tests/**`、`godot-mcp/**`、`.workspace/mario/**`、`PRD-mario.md`、`DECISIONS.md`、`REQUIREMENTS.md`，也**没有改冻结的任务书**。`DECISIONS.md` 的 sha256 开工=收工=`5ca40958…868b2a`（我只读）。
8. **我没有修任何发现的问题**（含 F-T11-1/F-T11-2/F-T11-3）：本报告只做诊断、复现与判定。
9. **密钥卫生**：`HOH_MODEL_API_KEY` 只从 `config/model.secret.env` 导入进程环境，**只报长度 51，从不打印**；任何落盘证据都不含明文密钥。
10. **未 push**（闸门武装，未尝试）；提交用带 `(SMOKE-T11)` 的英文信息。本报告的提交是**本轮唯一一次提交**，只新增 `TASK-SMOKE-T11-REPORT.md`；因 Git 的 `eol` 提示，它在**下次 checkout 时**可能被写成 CRLF（工作区当前内容是 LF，`json.dumps` 产物原样）。
11. **我在报告写完后做了两处精度更正并 amend 了同一提交**（未 push、未新增提交）：(i) `runs/smoke-t11` 的文件数在加入 `evidence/**` 后由 124 变为 186，已改为两个数分别标明时点；(ii) 工作区 HEAD 在我提交报告后由 `4558ba6` 前移到"本报告的那个提交"，已改为分别标明（且**不再引用该提交自身的哈希**，因为它会随本次 amend 改变）。两者都由 `postrun_state.txt` / `RUN_T11_*` 实测读数支持。
12. **我用的证据全部来自本轮**（`runs/smoke-t11/**`、`.workspace/fresh-t11/**`）；对 t10 的引用**只**用于口径自证（`1f3d20ed…`/`ed98d1b8…` 与 t6 摘要），不冒充本轮读数。
13. 除第 11 条列出的两处精度更正外，报告写完后不再修改。

---

## 10. 工件索引

| 类别 | 路径 |
|---|---|
| 本轮轮记录（新目录） | `runs/smoke-t11/**` —— 运行时轮记录 **124 文件**（newest `2026-10-02 00:29:22`）；连同本轮自建的 `evidence/**` 共 **186 文件**：`exit_code`、`process_exit_code`、`meta.json`、`warnings.log`、`TOOLS.md`、`versions/{index.json,3ac25f6c…,04d8ba5a…}`、`iter-1/{plan.md,result.json,usage.json,evidence.json,qa_report.md,logs/,traj/,planner-view/,candidate/}` |
| 被开发工程 | `.workspace/fresh-t11/**`（`project.godot`、`scenes/main.tscn`、`scripts/*.gd`） |
| 原始取证（本轮自建） | `runs/smoke-t11/evidence/round/**`：`prerun_state.txt`、`fresh_init.txt`、`fresh_init2.txt`、`editor_bootstrap.txt`、`editor_scope.txt`、`editor_console.txt`、`console.txt`、`wrapper.txt`、`baseline_before.txt`、`baseline_after.txt`、`postrun_state.txt` |
| 可复跑脚本 | `runs/smoke-t11/evidence/scripts/**`（`prerun.sh`、`fresh_init.sh`、`fresh_init2.sh`、`editor_bootstrap.sh`、`editor_scope.sh`、`run_round_t11.sh`、`postrun.sh`、`consolidate.sh`、`baseline_digest.ps1`、`treehash.py`、`mcp_call.py`、`traj_scan.py`、`cli_pair.py`、`timeline.py`、`frames.py`、`interaction_detail.py`、`battery.py`、`evcheck.py`、`mechanisms.py`、`coins.py`、`sizes.py`、`ctx.py`、`dump_strings.py`、`full.py`、`cmds.py`、`traj_shape.py`） |
| 分析输出 | `runs/smoke-t11/evidence/analysis/**`：`traj_scan.txt`、`cli_{planner,developer,tester}.txt`、`timeline_tester.txt`、`message_sizes.txt`、`e4_check.txt`、`e1_verified_claims.txt`、`battery_raw.txt`、`input_replay_frames.txt`、`interaction_{detail,summary,verdict_line}.txt`、`mechanisms.txt`、`coin_readings.txt`、`endpoint_refusals.txt`、`tree_identities.txt`、`a0_to_a1_diff.txt`、`e5_candidate_vs_live.txt` |
| 电池原始件（轮内） | `runs/smoke-t11/iter-1/candidate/.hoh/deterministic/**`：`battery.json`、`deterministic.json`、`record-00..11.json`、`raw/{project_reload_and_open,scene_structure,editor_errors_baseline,play_scene_ready,scene_tree,screenshot,input_channel_probe,input_replay,interaction_evidence,node_and_collision_assertions,editor_stop_scene}.json` |
| 图片证据 | `runs/smoke-t11/iter-1/candidate/.hoh/evidence/*.png`（11 张，含 `replay-interaction-{before,after}.png`） |
| 规范 / 任务书 | `.spec/hof-rs/REQUIREMENTS.md`（E1..E6 第 110-119 行）、`.spec/hof-rs/OBJECTIVE-COMPLETION.md`（C1..C5）、`.spec/hof-rs/tasks/TASK-SMOKE-T11.md`、`TASK-SMOKE-T8.md` |
| 上轮对照 | `TASK-SMOKE-T10-REPORT.md`、`TASK-SMOKE-T10-ACCEPTANCE.md`、`TASK-DR76-*.md`、`TASK-DR77-*.md` |
| 相关决策 | `DECISIONS.md` **D276 / D278 / D288 / D289 / D290**（只读） |

---

## 附：机器可读结论

```json
{
  "task": "TASK-SMOKE-T11",
  "round_id": "smoke-t11",
  "round_dir": "runs/smoke-t11",
  "project_dir": ".workspace/fresh-t11",
  "engine": {
    "version_string": "4.8.dev.mono.custom_build.035edfce7",
    "binary": "F:\\moonbit-hof-rs\\godot-mcp\\godot\\bin\\godot.windows.editor.x86_64.mono.exe",
    "size_bytes": 194216960,
    "mtime_unix": 1790641862,
    "sha256_recorded_only": "08483088a4a2772841cd3b4c916b2d45b3cb6255656cf3951598a86fce7e9e6a",
    "listener_pid": 22876,
    "listener_matches_binary": true,
    "started_by_this_round": true,
    "note": "No editor was running at round start (port 9877 had no listener, no godot process); the previously recorded pid 75204 was already gone and was not killed by this round."
  },
  "start_state": {
    "mode": "fresh",
    "version_id": null
  },
  "fresh_project_evidence": {
    "directory_absent_before": true,
    "empty_listing": "ls -la .workspace/fresh-t11 -> total 0 (only . and ..); find -mindepth 1 | wc -l -> 0",
    "init_command": "hoh init --project F:\\moonbit-hof-rs\\.workspace\\fresh-t11",
    "init_exit": 0,
    "init_output": "init: A0 ready at F:\\moonbit-hof-rs\\.workspace\\fresh-t11 (initialize ran; no MCP, no model endpoint and no key were required)",
    "run_command": "hoh run --iterations 1 --run-id smoke-t11 --fresh-workspace --project F:\\moonbit-hof-rs\\.workspace\\fresh-t11",
    "editor_scope_verified": "project_list_scripts -> {\"count\":0,\"scripts\":[]} and project_get_filesystem_tree shows exactly the init scaffold (project.godot, scenes/main.tscn, scripts/README.md)"
  },
  "round": {
    "start": "2026-10-01 23:50:36",
    "end": "2026-10-02 00:29:22",
    "elapsed_seconds": 2326,
    "round_exit": 0,
    "total_tokens": 17876780,
    "tokens_by_role": {
      "planner": 199008,
      "developer": 8354310,
      "tester": 9323462
    },
    "usage_known": true,
    "attempts": [
      {
        "role": "planner",
        "attempt": 1,
        "exit_status": "Submitted",
        "artifact_valid": true
      },
      {
        "role": "developer",
        "attempt": 1,
        "exit_status": "RepeatedFormatError",
        "artifact_valid": true
      },
      {
        "role": "tester",
        "attempt": 1,
        "exit_status": "Submitted",
        "artifact_valid": true
      }
    ],
    "retries": []
  },
  "product_identity": {
    "A0": {
      "runtime_id": "3ac25f6c5c38885febd3a001ea99c88aca61b1799c7b105306919886c2c1d151",
      "report_scheme_id": "ef369f272a4ceab0130bb00682caaf1acaed4043d72abe227fc0b27193545e01",
      "files": 3,
      "bytes": 1727,
      "is_empty_scaffold": true
    },
    "A1": {
      "runtime_id": "04d8ba5a12899ed8bfc2c04113932983e5db03e8d471717fc3da8b5db9a585c1",
      "report_scheme_id": "b33cf818e41654e24d83e47025cc6a128da816de1fa5c1ac7b00c07a0031f23c",
      "files": 11,
      "bytes": 8830
    },
    "A1_neq_A0": true,
    "changes": {
      "added": [
        "scripts/coin.gd",
        "scripts/coin.gd.uid",
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
          "to_bytes": 4358
        }
      ],
      "removed": []
    },
    "non_trivial": "The Developer started from a scaffold whose scripts/ held only README.md and produced 4 scripts plus a 31-node scene (Ground, Player, Camera2D, Coin1..Coin5, Goal, HUD{Coins,Lives,Time,Victory})."
  },
  "verdicts": {
    "E1": "met",
    "E2": "met",
    "E3": "not_met",
    "E4": "met",
    "E5": "met",
    "E6": "met"
  },
  "unjudgeable": [],
  "criteria": [
    {
      "id": "E1.planner-legal-D1",
      "pass": true,
      "evidence": "iter-1/plan.md (2879 B); logs/planner.attempt1.log -> exit_status=Submitted, artifact_valid=true, attempt=1, 28 calls; RepeatedFormatError=0 in the planner trajectory."
    },
    {
      "id": "E1.developer-real-increment",
      "pass": true,
      "evidence": "versions/index.json: A0=3ac25f6c...(iteration 0 role init, 3 files/1727 B) -> A1=04d8ba5a...(iteration 1 role developer, 11 files/8830 B); independent diff: ADDED 8, MODIFIED scenes/main.tscn 342->4358 B, REMOVED 0; logs/developer.attempt1.log: artifact_valid=true. Both runtime directory names reproduced by my own implementation of the runtime hash scheme."
    },
    {
      "id": "E1.tester-legal-E1",
      "pass": true,
      "evidence": "iter-1/evidence.json parses: iteration=1, qa_status=partial, verified=7, gap=14; logs/tester.attempt1.log -> exit_status=Submitted, artifact_valid=true, attempt=1; traj/ holds only tester.attempt1.json."
    },
    {
      "id": "E1.round-completed-exit0",
      "pass": true,
      "evidence": "runs/smoke-t11/exit_code bytes 30 0A; meta.json exit_code=0; runs/smoke-t11/process_exit_code bytes 30 0A; wrapper ROUND_EXIT=0; result.json ok=true failed_role=null reason=\"ok\" issues=[]."
    },
    {
      "id": "E1.fresh-empty-project-clause",
      "pass": true,
      "evidence": "Directory did not exist before the round; raw ls -la showed 'total 0' and find counted 0 entries; hoh init exit 0 rebuilt A0 there; meta.json start_state={\"mode\":\"fresh\",\"version_id\":null}; A0 is the 3-file/1727 B scaffold, not .workspace/mario (17 files/18397 B). The editor MCP scope was verified against the same directory (0 scripts)."
    },
    {
      "id": "E2.launchable-no-errors",
      "pass": true,
      "evidence": "raw/editor_errors_baseline.json count=0 errors=[] in_process=true pid=22876; raw/play_scene_ready.json playing=true mcp_port=56727 pid=31528 and running_game_get_scene_tree returned 31 nodes; raw/editor_stop_scene.json stopped=true; artifact_gate {applicable:true,launchable:true,reasons:[]} in both meta.json and result.json."
    },
    {
      "id": "E3.left-right-movement",
      "pass": true,
      "evidence": "input_replay.json (48 calls) game-process windows: move_right x 192.000045776367 -> 408.333038330078 (dx=+216.332993, 3.6666609 px/frame); move_left x 455.999542236328 -> 239.666732788086 (dx=-216.332809). All four running_game_assert_node_state replies passed=true with resolved_node_path=/root/Main/Player."
    },
    {
      "id": "E3.jump",
      "pass": true,
      "evidence": "jump window: y 283.590729 -> 234.257355 at frame 16 -> 267.479584 with x constant at 466.999542236328, i.e. a pure vertical arc; engine assertion passed=true."
    },
    {
      "id": "E3.at-least-one-interactive-object",
      "pass": false,
      "evidence": "interaction_evidence step ok=false; verdict COIN_NOT_PICKED_UP with the engine's own text:neq \"Coins: 1\" assertion returning passed=false (reason \"expected text neq Coins: 1, found Coins: 1\"). No runtime reading of 'Coins: 0' exists anywhere in the round (the only 'Coins: 0' is the static default text in scenes/main.tscn). Counter-reading nuance: the runtime did read Coins: 1 through the property tool while main.gd starts at 0 and only coin.gd::collect() increments it, which indicates a coin was collected earlier in the round - but no semantic-tool observation of the transition exists."
    },
    {
      "id": "E3.goal-or-win-condition",
      "pass": false,
      "evidence": "Goal.reached read false four times; Goal.position x=6600.0 while the interaction verdict records player max x=225.000045776367; the trajectory/scene tree contains no enemy, block or kill plane, so no failure/restart flow exists either. F13/F14/F15 are gaps."
    },
    {
      "id": "E4.verified-claims-backed",
      "pass": true,
      "evidence": "7 verified claims carry 18 execution_records; every record path exists under the frozen candidate (MISSING=[]); every record has a type (assert/build/replay/runtime_trace/screenshot) and candidate_id=04d8ba5a...; verified and gap sets are disjoint with no duplicates; all 14 gaps carry player_impact; planner_handoff has all three arrays."
    },
    {
      "id": "E5.qa-did-not-modify-A1",
      "pass": true,
      "evidence": "iter-1/candidate, versions/04d8ba5a... and live .workspace/fresh-t11 are byte-identical: same runtime_id 04d8ba5a..., same report-scheme id b33cf818..., 11 files/8830 B in all three; candidate_id == version_id == 04d8ba5a...."
    },
    {
      "id": "E6.honest-declaration",
      "pass": true,
      "evidence": "qa_report.md states 'Status: **partial** - 7 verified claims, 14 gaps' and enumerates the unmet items (no wall/enemy/block/kill plane, coin 0->1 transition unobserved, win never driven), explicitly refusing to overclaim: 'A supporting observation exists but is not sufficient ... The 0 -> 1 transition and the coin leaving the tree still need a clean observation.'"
    },
    {
      "id": "M1.coin-counter-readable-via-property-tool",
      "pass": true,
      "evidence": "interaction_evidence.json call[0] label 'interaction:read_/root/Main/HUD/Coins_text' -> {\"node_path\":\"/root/Main/HUD/Coins\",\"properties\":{\"text\":\"Coins: 1\"},\"type\":\"Label\"}; the verdict line records the discovery path: candidates enumerated from the scene tree's name/path only, each text read through running_game_get_node_properties; COIN_COUNTER_UNREADABLE occurred 0 times."
    },
    {
      "id": "M2.shortfall-on-verdict-line-and-two-class-split",
      "pass": false,
      "evidence": "The verdict line itself carries the figure: 'WIN_BLOCKED_UNDER_MOVE_RIGHT (... player max x=Some(225.000045776367), goal.position=Some(Object {\"x\": Number(6600.0), \"y\": Number(280.0)}), coverage_shortfall_px=Some(6374.999954223633) - the bound is the level or the game logic, not the window's coverage; this conclusion is bounded by the movement direction ...)'. The DR-77 rename is in force (WIN_UNREACHABLE_GEOMETRICALLY appears 0 times). However only ONE of the two classes was exercised: WIN_BLOCKED_UNDER_MOVE_RIGHT (3 of 130 batches, 127 unspent). WIN_UNREACHED_WITHIN_BUDGET did not occur this round, so the budget-exhaustion class has no real-machine evidence here."
    },
    {
      "id": "M3.three-exit-code-readings-equal",
      "pass": true,
      "evidence": "runs/smoke-t11/exit_code = bytes 30 0A; meta.json exit_code = 0; runs/smoke-t11/process_exit_code = bytes 30 0A; wrapper ROUND_EXIT=0. All three are persisted artifacts (the t10 T10A-4 gap is closed). Write order by mtime: result.json 00:29:22.569 < exit_code .6289 < process_exit_code/meta.json .6305."
    },
    {
      "id": "M4.character-cli-reaches-game-endpoint",
      "pass": false,
      "evidence": "The Tester executed 9 hoh tools call invocations; the 3 running_game_get_node_properties calls were ALL refused: 'hoh: game_endpoint_unavailable: ... the published route was found and **refused**: the game process the record names is not running (pid 33536), so the route belongs to an earlier round. No request was sent, so this is an explicit refusal, not a transport failure. Falling back to the editor endpoint is not allowed (DR-43).' The Developer made 0 running_game_* calls (98 CLI calls, all editor_*/project_*). The battery's own game-process payloads are unaffected."
    },
    {
      "id": "G1.read-only-baselines-unchanged",
      "pass": true,
      "evidence": "Repo-convention digests are byte-identical before (23:48:43) and after (00:29:42): .workspace/mario 178 files dee0a36f357c440d078c652d4d4b8990af1a63b88d282c1e36c04a16d006cc94 (newest 2026-09-30 18:23:08); runs/smoke-t6 135 c144ef32...7a9c03 (the required self-proof); smoke-t7 115 6e4c1595...20fb7; smoke-t8 358 6d11b2c6...bdf5a7; smoke-t9 83 541e2d81...36ca9d; smoke-t10 232 31955589...b38b8b. newest mtimes unchanged too."
    },
    {
      "id": "G2.frozen-files-and-engine-untouched",
      "pass": true,
      "evidence": "PRD-mario.md sha256 4c81c3a9995f0b3afdf01421a0c3be88573cceefc284ce9bafbfda141f0f5c3a (before = after = meta.json spec sha); DECISIONS.md sha256 5ca40958f6563223c3f1a223670b59478d272ed610e15f3da34f81276e868b2a before = after; nested engine repo HEAD fc63af77c33368c4a1bb839c95d19750554f63a3 with status --porcelain -uall = 0 lines; outer HEAD unchanged 4558ba60ab88b607c36aecb58a3530654344584e."
    },
    {
      "id": "G3.no-orphan-processes-editor-alive",
      "pass": true,
      "evidence": "After the round, port 9877 is LISTENING owned by pid 22876 and tasklist shows exactly one godot process (22876); runs/smoke-t11/game_endpoint.json no longer exists; the round started no game process of its own and needed no cleanup."
    },
    {
      "id": "G4.redaction-defect-did-not-recur",
      "pass": true,
      "evidence": "All four trajectory files parse as legal JSON (including tester.attempt1.json, corrupted in smoke-t10). The redaction is now a sidecar: developer.attempt1.redacted.json (8 <redacted>, 1084030 B) while developer.attempt1.json keeps its original 1084125 B; warnings.log records 'frozen evidence kept in place; the redacted form was generated as developer.attempt1.redacted.json (the original is byte-unchanged, DR-72 2)'."
    },
    {
      "id": "G5.evidence-diff-populated",
      "pass": true,
      "evidence": "result.json evidence_diff = {added: 8 scripts files, modified: [scenes/main.tscn], removed: []}, matching my independent diff; smoke-t10's empty evidence_diff (F-T10-3) is closed on this product."
    }
  ],
  "mechanism_readings": {
    "zero_increment": {
      "occurred": false,
      "evidence": "warnings.log (2 lines) has no Zero-increment/no_progress/no_engineering_write; A1 != A0."
    },
    "crash": {
      "occurred": false,
      "evidence": "exit 0; result.json out_of_tree_writes=[]; artifact_hygiene suspicious_files=[] suspicious_directories=[]; no stray '-p' directory in the project."
    },
    "repair_attempt": {
      "occurred": false,
      "evidence": "repair_retry_used=false; wrap_up_retry_used=false reason=not_triggered; one attempt per role; battery_passes length 1; no launch_gate_repair warning."
    },
    "output_cap_64KiB": {
      "exercised": false,
      "evidence": "0 hoh_output_truncated markers in any trajectory; max tool content 45486 B (tester); max serialized message 102475 B - no output crossed 65536 B.",
      "note": "No real-machine reading of the truncation path was produced this round."
    },
    "artifact_gate": {
      "applicable": true,
      "launchable": true,
      "reasons": [],
      "evidence": "identical in meta.json and result.json; battery 12 steps / 11 ok (only interaction_evidence false)."
    },
    "stale_editor_logs": {
      "count": 0,
      "evidence": "raw/editor_errors_baseline.json count=0 errors=[] pid=22876 process=editor."
    },
    "endpoint_reachability": {
      "game_endpoint_unavailable_count": 3,
      "evidence": "see criterion M4; three refused running_game_get_node_properties invocations by the Tester (each serialized twice, hence 6 string hits)."
    },
    "character_format_friction": {
      "developer_exit_status": "RepeatedFormatError",
      "developer_attempts": 1,
      "schema_failure_count": 0,
      "evidence": "'No tool calls found' appears planner 2 / developer 9 / tester 9 times; the developer still delivered artifact_valid=true and the round continued."
    }
  },
  "defects": [
    {
      "id": "F-T11-1",
      "severity": "major",
      "what": "The published game route is stale for a role that starts its own game: the Tester's editor_play_scene created fresh games (57449/pid 4508 at 00:13:37, 57902/pid 4784 at 00:18:10) while runs/smoke-t11/game_endpoint.json still named 56821/pid 33536, so all three live running_game_* CLI calls were refused. meta.json records the battery's game (56727/pid 31528). The runtime's refusal itself is correct and deliberate (route never lies, no silent fallback); the gap is that nothing republishes the route on a role-initiated play_scene.",
      "reproduction": "python runs/smoke-t11/evidence/scripts/cli_pair.py runs/smoke-t11/iter-1/traj/tester.attempt1.json ; python runs/smoke-t11/evidence/scripts/timeline.py runs/smoke-t11/iter-1/traj/tester.attempt1.json"
    },
    {
      "id": "F-T11-2",
      "severity": "major",
      "what": "The interaction_evidence window appears not to have driven the game at all this round: all 180 samples across its three batches are the single value x=225.000045776367, while input_replay on the same candidate moved the player 216.33/33.00/0/216.33 px. The window calls running_game_create/play_input_recording and run_test_scenario but makes 0 editor_simulate_input_action calls (input_replay makes 8), and the recordings carry only two pressed events over ~40 ms. Consequently COIN_NOT_PICKED_UP and WIN_BLOCKED_UNDER_MOVE_RIGHT in that step are honest readings of 'this attempt did not advance' and cannot yet be read as evidence about the game.",
      "reproduction": "python runs/smoke-t11/evidence/scripts/interaction_detail.py runs/smoke-t11/iter-1/candidate/.hoh/deterministic/raw/interaction_evidence.json ; python runs/smoke-t11/evidence/scripts/frames.py runs/smoke-t11/iter-1/candidate/.hoh/deterministic/raw/input_replay.json"
    },
    {
      "id": "F-T11-3",
      "severity": "major",
      "what": "Structural false negative for E3's coin-pickup class: the input_replay windows run BEFORE interaction_evidence and already consume a coin (the counter reads Coins: 1 at the start of the interaction window, and main.gd starts at 0), so the 0 -> 1 transition F10 demands can no longer be observed in that window on any candidate. The product gap and the evidence-shape false negative must be triaged separately.",
      "reproduction": "python runs/smoke-t11/evidence/scripts/coins.py runs/smoke-t11 ; read runs/smoke-t11/iter-1/candidate/scripts/{main,coin}.gd"
    },
    {
      "id": "F-T11-4",
      "severity": "minor",
      "what": "The WIN_UNREACHED_WITHIN_BUDGET class (budget exhausted) was not exercised on the real machine this round; only WIN_BLOCKED_UNDER_MOVE_RIGHT was. The split is therefore only half-verified in vivo.",
      "reproduction": "grep -o 'WIN_UNREACHED_WITHIN_BUDGET' runs/smoke-t11/iter-1/candidate/.hoh/deterministic/*.json -> 0 hits"
    },
    {
      "id": "F-T11-5",
      "severity": "minor",
      "what": "The 64 KiB output-cap path was not triggered (largest tool result 45486 B), so it remains covered only by offline tests; this round cannot speak to it.",
      "reproduction": "python runs/smoke-t11/evidence/scripts/sizes.py runs/smoke-t11"
    },
    {
      "id": "F-T11-6",
      "severity": "info",
      "what": "The battery's scene_structure step is a static project_read_scene_file_content read, so F16's 'HUD/Coins text=Coins: 0' is the scene file's default text, not a runtime reading. E4 is unaffected (the record is honestly typed 'assert' against the scene file), but the value is easy to misread as a runtime counter reading.",
      "reproduction": "cat runs/smoke-t11/iter-1/candidate/.hoh/deterministic/raw/scene_structure.json"
    }
  ],
  "risks": [
    "F-T11-2's root cause is inferred, not proven: I did not reproduce the interaction window's driving path end-to-end, so 'the drive did not take' is a probability (~0.75), not a measurement.",
    "F-T11-3 assumes the coin consumed before the interaction window was consumed by input_replay; the counter read 1 at window start and main.gd starts at 0, which makes a pickup certain, but which window did it is inferred from the screenshots the Tester describes.",
    "The battery's game endpoint (56727/31528) and the route file's last value (56821/33536) are different processes; which writer published 56821 was not determined from source.",
    "E3's two established behaviours were observed through windows that also inject via editor_simulate_input_action; the positional evidence is game-process, but the injection is editor-side by design (unchanged from smoke-t10).",
    "The round rebuilt target/release/hoh.exe from HEAD before running, because the pre-existing binary predated DR-76/DR-77; the run therefore exercised the current HEAD sources, which is what the new mechanisms require."
  ],
  "unverified": [
    "Whether the editor expected by the task (pid 75204) was terminated by something outside this round: it was already absent at 23:48 (no listener, no process); I did not kill it and cannot say who closed it.",
    "WIN_UNREACHED_WITHIN_BUDGET behaviour on real hardware (class not exercised).",
    "The 64 KiB truncation path on real hardware (not triggered).",
    "The exact author of the route value 56821/pid 33536 (no publish-path source read).",
    "Whether the Developer's RepeatedFormatError exit was tolerated deliberately or by an uncovered branch."
  ],
  "honest_disclosure": {
    "rounds_run": 1,
    "retries": 0,
    "editor_started_by_agent": true,
    "editor_pid": 22876,
    "editor_left_alive": true,
    "game_processes_started_by_agent": 0,
    "orphans_cleaned": 0,
    "accidental_write": "Three EMPTY directories were created under runs/smoke-t11/evidence/ before the round and removed with rmdir so that the run directory would not exist; zero bytes written to any baseline; no rm -rf was used and no path was built from an unexpanded variable.",
    "binary_rebuilt": "cargo build --release --offline (16.85 s) -> sha256 d0292a06b19c6dc4ab00bb916ad642ee077161d59882109c44ab986b7a6b4b40",
    "files_not_modified": [
      "src/**",
      "tests/**",
      "godot-mcp/**",
      ".workspace/mario/**",
      "PRD-mario.md",
      "DECISIONS.md",
      "REQUIREMENTS.md",
      "TASK-SMOKE-T11.md"
    ],
    "secrets": "HOH_MODEL_API_KEY imported from config/model.secret.env into the process environment; length 51 reported only; never printed and never written to any artifact.",
    "pushed": false,
    "git_commit_tag": "(SMOKE-T11)"
  }
}
```

