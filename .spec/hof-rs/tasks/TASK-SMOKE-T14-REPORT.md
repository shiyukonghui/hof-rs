# TASK-SMOKE-T14-REPORT — **最终修订版真机轮**：在含最后两批修复的 HEAD 上重跑同一命令序列；**E1/E3/E4/E5/E6 met，E2 not met（退出码 6）**；角色自起场景重发布分支**首次被走到**

- 任务书：**`.spec/hof-rs/tasks/TASK-SMOKE-T12.md` 与 `TASK-SMOKE-T13.md` 全部条款继续有效**，外加**调度者派发本轮时给出的 5 条增量**（重建优先、角色自起场景探针、启动门复现、报告纪律、时间戳与端口精确）；**仓库里没有 `TASK-SMOKE-T14.md`**（本轮未新写任务书），本报告按前两本书的申报节 + 那 5 条增量撰写，并如实登记这一事实
- 报告人：**真机轮执行子代理（无上游对话上下文）**；落点：`F:\moonbit-hof-rs`
- **本轮新工程目录**：`F:\moonbit-hof-rs\.workspace\fresh-t14`（开工时**不存在**，见 §1.4）
- 轮记录：`runs/smoke-t14/**`；仓外暂存：`F:\moonbit-hof-rs-t14-staging/**`
- 本轮命令（**恰好一轮**；无被拒的启动）：
  - `target/release/hoh.exe init --project F:\moonbit-hof-rs\.workspace\fresh-t14`
  - `target/release/hoh.exe run --iterations 1 --run-id smoke-t14 --fresh-workspace --project F:\moonbit-hof-rs\.workspace\fresh-t14`
- 墙钟：`09:45:13 → 10:21:20` = **36m07s（2166.928 s）**；**`ROUND_EXIT=6`**；`meta.json.exit_code=6`
- 引擎（判据）：`4.8.dev.mono.custom_build.035edfce7`（`--version` 逐字）；二进制 sha256 `08483088…e9e6a`（与 T11/T12/T13 记录逐字相同，仅记录）
- 二进制（**本轮按 HEAD 重建**）：`12727808 B / mtime 1790905290 / sha256 3b97e4a02436bac781a41e3675ac7c4cb341c44d1682c297c3911d5d0cb80ba3`（旧值 `12713984 / 310075fa…` ⇒ 陈旧，必须重建，见 §1.1）
- HEAD（开工 = 收工 = 报告前）= `44131d983ed100a65775d5dfa865bcc6ed7fa4a4`；`origin/master` 同值（**未 push**）
- 总 tokens（`result.json.usage` 三角色之和 = 控制台 `total tokens`）= **16,346,289**

---

## 0. 结论摘要

| 判据 | 判定 | 一句话依据（本轮原始证据） |
|---|---|---|
| **E1** | **met** | 目录**可证为空**（0 条目）→ `init` exit 0 → **恰好一轮** `run`；`start_state.mode="fresh"`；`A_0=3ac25f6c…`（3 文件/1727 B）→ `A_1=3d18b24d…`（13 文件/8254 B；10 新增 + `main.tscn` 修改）；Planner `D_1` 三节齐备、QA `E_1` 合法。**但整轮退出码是 6，不是 0**（见 E2 与 §0.1）。§2.1 |
| **E2** | **not met** | 运行时的**自家可启动闸门**给出 `artifact_gate={applicable:true,launchable:false,reasons:[…]}`，退出码 6；`editor_get_errors` 在冻结点是 `count=1`（`ERROR: Cannot create file 'res://.godot/editor/filesystem_cache10'`）。**同一门的另一半是绿的**：`editor_play_scene playing=true`、`running_game_get_scene_tree` 返回 22 节点、电池 12 步里 10 步 ok。**这条红不是项目脚本错误**：pass 1 曾有真正的 `res://scripts/main.gd:8 - Parse Error`（6 条里的 1 条），修复重试后 pass 2 只剩那条编辑器缓存写失败 ⇒ 判据的"无编译/脚本错误"字面上成立、"可启动"字面上成立，**但产品自己的判据说不**。我按产品自己的门判 **not met**，理由与反例检验见 §2.2。§2.2 |
| **E3** | **met（四类全齐，本轮形态最强）** | 四类**全部**有游戏端点语义工具原始回包：左移 Δ**−216.33215332031**（60/60 唯一 x）、右移 Δ**+216.33093261719**（60/60 唯一 x）、跳跃**纯竖直**（x `unique=1`、y `unique=30`）、**金币 `Coins: 0 → Coins: 1`**（**首次真机 0→1**，不再是 0→2）、**`Goal.reached false → true`**；四发 `POSITION_ASSERT_PASSED` + 两发 `running_game_assert_node_state passed=true`。§2.3 |
| **E4** | **met** | `evidence.json`：**11 verified / 10 gap**，`overlap=[]`；**41** 条执行记录（verified 身上 **24** / gap 身上 **17**，两个作用域分开写）逐条 stat 存在（`MISSING=[]`），`candidate_id` 单一（`3d18b24d…`）；10 条 gap 各带 `player_impact`/`recommended_update`；`planner_handoff` 3/4/5。§2.4 |
| **E5** | **met** | 三棵树**逐字节同一**：`versions/3d18b24d…` == `iter-1/candidate` == 活体 `.workspace/fresh-t14`（13 文件/8254 B；`only_in_*=[]`、`differing=[]`）。§2.5 |
| **E6** | **met** | `qa_report.md` 逐字 `"Status: **partial**."`，逐条列出未做到的东西（F6/F8/F9/F11/F12/F14/F15/F17/N3/F5-COLL），并把编辑器错误登记为 gap `N3`；**没有**把未达成写成 verified。§2.6 |

**本轮不可判定的判据：无。**

### 0.1 本轮真正的头条：**退出码 6，成因不是项目**

这是四轮真机里第一次 `hoh run` 以**非 0** 退出（T12 = 0、T13 = 0）。`warnings.log` 里运行时的自述逐字为：

```text
iteration 1: the artifact is not launchable after the one allowed repair retry; freezing A1 anyway (artifact_gate.launchable=false)
```

原因链（全部有原始件，见 §2.2 与 §5）：

1. 轮次**开始时**那一次 `start_round_game` **成功**并发布了 `http://127.0.0.1:64097/mcp`（我在 09:46 从盘上读到并留档，`evidence/raw/live_snapshot_early.txt`）——**不是**"轮内起游戏失败"；
2. 电池 **pass 1**（09:58）`editor_errors_baseline` 报 **6** 条错误，其中**真的有** `res://scripts/main.gd:8 - Parse Error: Expected new line after "\".` 与 `Failed to load script "res://scripts/main.gd" with error "Parse error"`；同时 `play_scene_ready` 连不上 `:64145` ⇒ pass 1 门失败；
3. 运行时的**一次启动门修复重试**（`developer.attempt2`，日志 notes 逐字 `launch_gate_repair: the pre-freeze launchable gate failed`）把 `main.gd` 修好；
4. 电池 **pass 2**（10:06）`editor_errors_baseline` 只剩 **1** 条：`ERROR: Cannot create file 'res://.godot/editor/filesystem_cache10'. Check user write permissions.`；
5. 这条**既不是编译错误也不是脚本错误**，而是**编辑器自己的缓存目录写失败**：`--fresh-workspace` 会**清空工作区的每一个条目**（`src/runtime/start_state.rs:126`），包括 `.godot/editor/**`，而编辑器在轮开始前就已经指向该工程（任务书要求的顺序）⇒ 目录被从编辑器脚下删掉；
6. 门把"任何一条 editor 日志行"当作"工程不可用"⇒ `launchable=false` ⇒ exit 6。

**反例检验（把"我们没看到"与"不可能"分开）**：

- **不是权限**：`icacls` 对 `.workspace/fresh-t14\.godot` 与 `.workspace/fresh-t13\.godot` **逐行相同**（`Authenticated Users:(I)(M)`）；报错文本里的 "Check user write permissions" 是引擎的通用文案。
- **不是所有工程都这样**：`.godot/editor/filesystem_cache10` 在 `mario`(1241 B)、`fresh-t11`(673 B)、`fresh-t12`(805 B)、`fresh-t13`(789 B) **都存在**，**只有 fresh-t14 没有整个 `.godot/editor/` 目录**（`evidence/analysis/godot_editor_dir_check.txt`）。⇒ fresh-t13 在 04:54 重建过它，fresh-t14 没有。
- **不是"编辑器永远不报错"**：我在轮后**自己**再调一次 `editor_get_errors`，同一个编辑器（pid 36808）返回的是**另一条**、且**不是错误**的行：`[MCP] capture=off (default; …)`（`evidence/round/live_editor_get_errors.json`）。⇒ 该字段是**编辑器日志尾的读数**，不是稳定的项目诊断。
- **未定因**：我**没有**插桩编辑器的缓存落盘时刻，因此"为什么 t14 没有重建 `.godot/editor/` 而 t13 重建了"**没有确定**；我只给出了它现在的形状与四个反例。这是本轮最重要的未闭合项。

### 0.2 三处"最后修正批"的真机读数（本轮的增量要求）

| # | 要求核对的标记 | 本轮读数 | 决定性原始件 |
|---|---|---|---|
| **1** | 陈旧动作 token `STALE_ACTION_NOT_RELEASED` | 二进制里 **1** 处（重建后）；电池判定文本里 **0** 次（因为没触发失败）；行为侧：`interaction_evidence` call[4] `release_stale_move_left` **早于** call[6] 首批驱动，随后 7 批各 **60/60 唯一 x** | `evidence/round/binary_markers.txt`、`evidence/analysis/e3_extract.txt` |
| **2** | 路由发布就绪消息（角色侧） | 二进制里 **1** 处（`the game the role started with \`editor_play_scene\` did not answer…`）；**并且本轮首次由我本人真的走到该分支**：`hoh tools call editor_play_scene`（role=developer）→ exit 0，**路由文件被重发布**（§3.4） | `evidence/round/binary_markers.txt`、`evidence/probe/role_play_probe3.txt` |
| **3** | harness 命令行脱敏（`DSH_TERM_CMD`） | 二进制里 **1** 处（`HARNESS_ENV_VARS` / `COMMAND_LINE_VARS` 的字符串常量）；**但真机脱敏没有生效**：`DSH_TERM_CMD=<我的整条命令行>` 在 `.redacted.json` 旁路副本里**逐字存活**（4/2 处）——见 §7.4 的缺陷 **F-T14-2** | `evidence/analysis/redaction_check.txt`、`evidence/analysis/dsh_context.txt` |

---

## 1. 环境引导（**从第一秒写入文件**，T12A-1 的直接延续）

原始件：`runs/smoke-t14/evidence/round/**`、`evidence/gatecheck/**`。

### 1.1 二进制重建（任务书增量 1）

```text
$ cargo build --release --offline        (stderr) Compiling hof-rs v0.1.0 (F:\moonbit-hof-rs)
                                         Finished `release` profile [optimized] target(s) in 6.12s
BUILD_EXIT=0                             ELAPSED 6.240 s
$ stat  target/release/hoh.exe           size=12727808 mtime=1790905290
$ sha256sum target/release/hoh.exe       3b97e4a02436bac781a41e3675ac7c4cb341c44d1682c297c3911d5d0cb80ba3
```

**为什么必须重建**：开工时二进制是 `12713984 B / mtime 1790880340 / sha256 310075fa…7158ca`，而 `8ddbad3..HEAD`（`44131d9`）改了 `src/runtime/{hygiene,run_loop,secrets,usage}.rs` 与 `tests/**`（`git diff --name-status 8ddbad3..HEAD` 逐字）⇒ 旧二进制**不含** DR-79/DR-80 的四项卫生修复，**陈旧二进制会使整轮作废**。
**披露**：为了让构建日志有一个可复现的、真的 `Compiling` 行，我先 `touch src/main.rs` 再构建（**只改 mtime，不改内容**；`git status --porcelain` 至今为空，除 4 个越界 `.json`）。

标记核对（`evidence/round/binary_markers.txt`，逐字；直接扫二进制字节，不用 `strings`）：

```text
stale_action_token                             occurrences=1
route_publish_readiness_message                occurrences=1
harness_command_line_redaction_env_name        occurrences=1
route_publish_readiness_battery_side           occurrences=1
role_started_route_error_prefix                occurrences=3
```

### 1.2 收紧点 1：**启动之前**的 `hoh doctor` 与端口/进程

**(a) `hoh doctor`（09:41:54，编辑器尚未启动）** — `evidence/round/preflight_doctor.txt`，`EXIT_CODE: 4`

```text
[ok] spec: .spec/hof-rs/PRD-mario.md (sha256 4c81c3a9…5c3a)
[ok] model.identity / model.chat: … answered with model `deepseek-v4.1-flash`
[ok] model.resident: skipped: host `100.105.152.101` is not loopback …
[FAIL] godot.project_file: F:\moonbit-hof-rs\.workspace\fresh-t14\project.godot
[ok] godot.bundled_addon / godot.extension_cache
[ok] godot.editor_scope: … Confirm manually that the project currently open in the editor is exactly this workspace
[ok] godot.engine_binary: … (size 194216960 B, mtime 1790641862)
[FAIL] godot.engine_version: `"…mono.exe" --version` exited -1: 
[FAIL] tools.mcp: MCP transport failure to http://127.0.0.1:9877/mcp … (os error 10061)
```

**`godot.engine_version` 这次 FAIL 了，而与 T12/T13 不同——我查清了原因并留了对照**：
`doctor` 用**工程目录**当探针进程的 cwd（`src/cli_impl.rs:213 env_config.cwd = workspace`），而此时 `fresh-t14` **还不存在** ⇒ 子进程起不来 ⇒ `exited -1`。
对照（唯一翻转的变量是目录是否存在）：

```text
$ target/release/hoh.exe doctor --project .workspace/mario        # 目录存在
[ok] godot.engine_version: 4.8.dev.mono.custom_build.035edfce7
$ "…godot.windows.editor.x86_64.mono.exe" --version               # 直接探针，0.101 s
4.8.dev.mono.custom_build.035edfce7
```

⇒ **引擎身份判据本身是逐字命中的**（`evidence/round/engine_version_probe.txt`、`evidence/round/doctor_diag_existing_project.txt`）；那条 FAIL 是"目录还不存在"的**当时预期**，不是引擎问题。任务书增量 5 要求的"读原始记录、不假设"，这就是一例。

**(b) 端口与进程（09:43:03，同一"启动之前"时点）** — `evidence/round/preflight_port.txt`

```text
$ netstat -ano                     exit=0 total_lines=552
  lines containing ':9877' = 0
$ tasklist /FI "IMAGENAME eq godot.windows.editor.x86_64.mono.exe"   exit=0
  INFO: No tasks are running which match the specified criteria.
```

⇒ 开工时**9877 无监听、无任何 godot 进程**；本轮两个引擎进程都是我自己起的。密钥只报长度（`HOH_MODEL_API_KEY` 51 B，从不打印）。

### 1.3 引擎启动捕获（**控制台句柄在 spawn 之前打开**）

`evidence/scripts/launch_engine.py` 在 `Popen` **之前**就以二进制追加方式打开一个控制台文件并把 stdout+stderr 都接上去，所以**第一秒的输出在文件里**（T12A-1 的"启动控制台不存在"结构上不可能再发生）。

| 启动 | 命令（逐字） | pid | 控制台文件 | 就绪行 |
|---|---|---|---|---|
| ① 门复现（**空目录**） | `…mono.exe -e --path F:\moonbit-hof-rs\.workspace\fresh-t14 --mcp-port=9877` | 34448 | `evidence/gatecheck/gate_game_role_console.txt` | `role=game`，`tools=73` |
| ② 本轮编辑器（**init 之后**） | 同上（此时目录已有 `project.godot`） | 36808 | `evidence/round/editor_console.txt` | `role=editor`，`tools=154` |

启动 ② 的完整控制台逐字（`evidence/round/editor_console.txt`）：

```text
==== CONSOLE OPENED BEFORE SPAWN (t=1790905468.167) ====
Godot Engine v4.8.dev.mono.custom_build.035edfce7 (2026-09-29 00:01:57 UTC) - https://godotengine.org
OpenGL API 3.3.0 NVIDIA 616.56 - Compatibility - Using Device: NVIDIA - NVIDIA GeForce RTX 4090

[MCP] pending_timeout_ms=30000 (configured=30000) pending_ticks_per_frame=8
[MCP] trace=off (default; …)
[MCP] capture=off (default; …)
[MCP] role=editor configured_port=9877 source=cmdline listen=true
[MCP] listening on 127.0.0.1:9877 (editor=true, tools=154)
[MCP] INFO: MCP server is ready on 127.0.0.1:9877 as the editor process (port source=cmdline, tools=154)
```

进程身份与工程绑定（**反假轮**）— `evidence/round/editor_launch_meta.txt`、`evidence/round/scope_project_list_scripts.json`、`evidence/round/editor_listener.txt`：

```text
ProcessId      : 36808
CommandLine    : F:\moonbit-hof-rs\godot-mcp\godot\bin\godot.windows.editor.x86_64.mono.exe -e --path F:\moonbit-hof-rs\.workspace\fresh-t14 --mcp-port=9877
ExecutablePath : F:\moonbit-hof-rs\godot-mcp\godot\bin\godot.windows.editor.x86_64.mono.exe
CreationDate   : 2026/10/2 9:44:28
netstat        : TCP 127.0.0.1:9877 LISTENING 36808
$ project_list_scripts -> {"count":0,"scripts":[]}      ← 本轮新工程
  磁盘对照：.workspace/mario/scripts 有 15 个条目
editor tools/list -> 154 = {editor_ 104, project_ 48, os_ 2, running_ 0}
```

⇒ MCP 侧看到的**就是**磁盘侧要写的那个工程。**运行期的 inline doctor 也逐字命中引擎串**（`evidence/round/round_console.txt`：`[ok] godot.engine_version: 4.8.dev.mono.custom_build.035edfce7`）。

### 1.4 "空目录 → init → run" 三步原始输出

**(a) 目录为空**（`evidence/round/empty_proof.txt`：先证明**不存在**，再 `mkdir`，再证明 0 条目）

```text
EXISTS_BEFORE: False        ISDIR_BEFORE: False
$ cmd /c mkdir F:\moonbit-hof-rs\.workspace\fresh-t14   exit=0
ENTRY_COUNT: 0              ENTRIES: []      RECURSIVE_ENTRY_COUNT: 0
$ cmd /c dir /a …           0 File(s)              0 bytes      2 Dir(s)
```

**(b) `hoh init`**（`evidence/round/init.txt`）：

```text
init: A0 ready at F:\moonbit-hof-rs\.workspace\fresh-t14 (initialize ran; no MCP, no model endpoint and no key were required)
EXIT_CODE: 0
```

`A_0` 树（`evidence/round/init_tree.txt`）：`project.godot` / `scenes/main.tscn` / `scripts/README.md` = **3 文件 / 1727 B**，运行时 id **`3ac25f6c…`**（与 T11/T12/T13 的 A₀ **同 id**；我的独立实现复算逐字命中）。

**(c) `start_state`**：`{"mode": "fresh", "version_id": null}`（`meta.json`；**不是** `as_is`）。

**(d) `hoh run` 的启动与结束**（`evidence/round/round_console.txt`，流式写入）：

```text
STARTED: 2026-10-02 09:45:13 (1790905513.791)
…（runtime doctor 全 ok，含 godot.engine_version 与 tools.mcp 154）
ENDED:   2026-10-02 10:21:20 (1790907680.719)
ELAPSED_SECONDS: 2166.928
ROUND_EXIT: 6
```

---

## 2. E1..E6 逐条判定 + 原始证据

### 2.1 E1 = met（**并附退出码的实情**）

| 要件 | 本轮原始证据 |
|---|---|
| Planner 产出合法 `D_1` | `iter-1/plan.md`（2648 B）含 `### Priority Order` / `### Preservation Gate` / `### Acceptance Gate`（三项 `True`）；`logs/planner.attempt1.log`：`exit_status=RepeatedFormatError`、**`artifact_valid=true`**、15 calls |
| Developer 产出**真实工程增量** | `versions/index.json`：`3ac25f6c…`(iter 0, role init) → `3d18b24d…`(iter 1, role developer)；`result.json.evidence_diff` = 10 新增 + `scenes/main.tscn` 修改 + 0 删除 |
| QA 产出合法 `E_1` | `iter-1/evidence.json`（42161 B，可解析）；`logs/tester.attempt1.log`：`exit_status=RepeatedFormatError`、`artifact_valid=true`、101 calls |
| 整轮 | `result.json`：`ok=true, failed_role=null, reason="ok", issues=[]`；`versions/index.json` 只有 2 条（iteration 0 / 1）；`iter-1/` 只有一个迭代目录；`result.json.attempts` 只有 4 条（planner×1、developer×**2**、tester×1，其中 developer 的 2 条是**同一次迭代内的两条 attempt**，不是两轮） |

**退出码（四处）**：`exit_code` 字节 `36 0A`、`process_exit_code` 字节 `36 0A`、`meta.json.exit_code=6`、wrapper `ROUND_EXIT=6` ⇒ **四处同数，但值是 6 不是 0**。
退出码语义（源码）：`exit_code=0` 只在"循环跑完**且**冻结产物 `launchable`"时给出；`launchable=false` ⇒ 6。本轮 `artifact_gate.launchable=false` ⇒ 6。

**`A_0`/`A_1` 摘要（运行时口径；我用独立实现复算，两个 id 都逐字命中）**：

```text
A0  3ac25f6c5c38885febd3a001ea99c88aca61b1799c7b105306919886c2c1d151    3 files   1727 B
A1  3d18b24d2432fa5eddf8b14c37bcdc4a3b739b4b4013556a0a769d77d147a26a   13 files   8254 B
```

**被改文件清单**：ADDED 10（`scripts/{coin,enemy,goal,main,player}.gd` + 各自 `.gd.uid`）；MODIFIED 1（`scenes/main.tscn`）；REMOVED 0。差异**全部落在 Developer 产出的工程文件**上，没有落在 `.hoh/**`、`runs/**` 等被排除路径。

**非琐碎**：Developer 从只有 `README.md` 的 `scripts/` 起手，写出 5 个脚本 + `Ground/Player/Coin1/Coin2/Goal/Enemy1/HUD/Wall` 的 **22 节点**场景，且**有真正的修复动作**（pass 1 的 `main.gd` 解析错误被 attempt2 修掉，见 §2.2）。

⇒ **E1 的四个要件都成立**；我把"退出码 6"作为**不改变本条判定、但必须点名**的事实写在这里，并把它的成因归到 E2。

### 2.2 E2 = **not met**（范围的精确表述）

**判据原文**：「产出的 Godot 工程**可启动**（无编译/脚本错误）」；证据形式：MCP `play_scene` + `get_editor_errors` 输出。

**绿的一半（实测）**：

```text
play_scene_ready : editor_play_scene → {"args_injected":["--mcp-port=63860"],"endpoint":"http://127.0.0.1:63860/mcp",
                   "mcp_port":63860,"mode":"main","pid":7740,"playing":true}
                   running_game_get_scene_tree → 22 nodes（带 path 与 type）
editor_stop_scene: {"message":"Playback stopped","stopped":true}
battery          : 12 步；10 步 ok=true
```

**红的一半（实测，且它是本轮退出的原因）**：

```text
editor_errors_baseline (pass 2, 冻结件) ok=False
{"available":true,"count":1,"editor":true,
 "errors":["  ERROR: Cannot create file 'res://.godot/editor/filesystem_cache10'. Check user write permissions."],
 "in_process":true,"log_path":"user://logs/godot.log","pid":36808,"port":9877,"process":"editor","source":"editor_log"}
artifact_gate = {"applicable":true,"launchable":false,"reasons":["editor_errors_baseline: editor reported 1 error(s): … (UNAVAILABLE: the editor is not clean; 1 line(s) still reproducible)"]}
exit_code = 6
```

**为什么我判 not met（而不是替产品说话）**：E2 的标题就是"**可启动**"，而**产品自己对这一轮的操作性定义**（`artifact_gate.launchable`）在本轮是 `false`。我不拿我自己的推理去覆盖产品自己的闸门。**同时**我把这条红的确切性质写清（下一条），让下一批能据此决定是修门还是修缓存。

**这条红的确切性质（反例检验）**：

| 检验 | 读数 | 结论 |
|---|---|---|
| 是权限问题吗？ | `icacls .workspace\fresh-t14\.godot` 与 `.workspace\fresh-t13\.godot` **逐行相同**（`Authenticated Users:(I)(M)`、`BUILTIN\Users:(I)(RX)`） | **否**；引擎文案 "Check user write permissions" 是通用串 |
| 是所有工程都这样吗？ | `.godot/editor/filesystem_cache10` 在 `mario`/`fresh-t11`/`fresh-t12`/`fresh-t13` **都存在**（1241/673/805/789 B），**只有 fresh-t14 没有整个 `.godot/editor/`** | **否**；不是引擎的普遍行为 |
| 是项目脚本错误吗？ | pass 2 的 `errors` 里**没有**任何 `Parse Error` / `Failed to load script`；pass 1 里**有**（6 条含 `res://scripts/main.gd:8 - Parse Error`），而 attempt2 修好了它 | **否**；残留那条属编辑器缓存，不属编译/脚本 |
| 该字段稳定吗？ | 轮后我**自己**再调 `editor_get_errors`，同一 pid 36808 返回 `count=1` 且内容是 `[MCP] capture=off (default; …)`——**一条根本不是错误的日志行** | **否**；它是编辑器日志尾的读数 |
| 那目录是谁删的？ | `--fresh-workspace` 逐字清空工作区的**每一个条目**（`src/runtime/start_state.rs:100 purge_contents` / `:126 fresh_workspace`）；编辑器在 09:44:28 就已指向该工程（任务书要求的顺序），清空发生在 09:45:13 | **是本轮命令序列的必然副作用**；但**为什么 t14 没有像 t13 那样重建 `.godot/editor/`，我未插桩，未定因** |

⇒ 一句话：**E2 按产品自己的门判 not met；红来自"编辑器缓存目录被 `--fresh-workspace` 清掉后没有重建"，不是产出的工程写坏了。** 我把"判据字面读法下 E2 会是 met"这一读法也明写在此，供验收者独立裁断。

### 2.3 E3 = met（四类全齐；**本轮首次拿到真正的 0→1**）

| 行为 | 裁定 | 决定性原始证据（**全部来自游戏进程端点**） |
|---|---|---|
| 左移 | **成立** | `input_replay` move_left：x `2085.65844726562 → 1869.32629394531`，Δ=**−216.33215332031**（60 帧，**60/60 唯一 x**）；`move_left:replay_assert_moved` `passed=true` |
| 右移 | **成立** | move_right：x `1817.99340820312 → 2034.32434082031`，Δ=**+216.33093261719**（60 帧，**60/60 唯一 x**）；`move_right:replay_assert_moved` `passed=true`；（补充窗口）move_right_release Δ**+33.00073242188**（10 帧，10/10 唯一） |
| 跳跃 | **成立** | jump：x **恒为** `2096.65869140625`（`unique=1`）、y `283.591979980469 → min 234.258605957031 → 267.480834960938`（`unique=30`）⇒ **纯竖直弧线**；`jump:replay_assert_moved` `passed=true` |
| **至少 1 个可交互对象** | **成立** | `interaction_evidence` 的 `running_game_get_node_properties`：`Coins: 0`（call 0）→ **`Coins: 1`**（call 48）；引擎自己的 `running_game_assert_node_state`（`text:neq "Coins: 0"`，actual `"Coins: 1"`）`passed=true`；判定行 `COIN_PICKED_UP` |
| **一个终点/胜负条件** | **成立** | `Goal.reached`：`false`（call 1/10/16/22/28/34/40）→ **`true`**（call 46/49）；`running_game_assert_node_state`（`reached:neq false`，actual `true`）`passed=true`；判定行 `WIN_DRIVEN`；`player max x=1671.32836914062` 越过 `goal.position.x=1600.0`，`coverage_shortfall_px=Some(-71.32836914062)`（**负值**） |

**"金币跃迁来自语义工具原始回包"（不得推断）——逐字**：

```text
[  0] running_game_get_node_properties interaction:read_/root/Main/HUD/Coins_text
      {"node_path":"/root/Main/HUD/Coins","properties":{"text":"Coins: 0"},"type":"Label"}
[ 48] running_game_get_node_properties interaction:read_/root/Main/HUD/Coins_text
      {"node_path":"/root/Main/HUD/Coins","properties":{"text":"Coins: 1"},"type":"Label"}
[ 50] running_game_assert_node_state   interaction:replay_assert_picked_up
      {"actual":"Coins: 1","expected":"Coins: 0","operator":"neq","property":"text","passed":true,"resolved_node_path":"/root/Main/HUD/Coins"}
[ 51] running_game_assert_node_state   interaction:replay_assert_won
      {"actual":true,"expected":false,"operator":"neq","property":"reached","passed":true,"resolved_node_path":"/root/Main/Goal"}
```

（`evidence/analysis/e3_extract.txt`；原始件 `iter-1/candidate/.hoh/deterministic/raw/interaction_evidence.json`。）

**诚实的边界**：计数器是 **`0 → 1`**（T12/T13 都是 `0 → 2`）——本轮的场景只有一枚被扫到，**恰好 1 枚**这一次是真的。`input_axis` 探针**仍然**读不到轴（`running_game_run_test_scenario` 的 `input_axis` 断言报 `node '/root/Main/Player' does not have the property 'input_axis'`，`all_passed=false`）——E3 的依据是**位置采样 + 引擎断言**，不是探针；`qa_report` 也明说了这一点（§2.6）。

**计数（作用域 = `iter-1/candidate/.hoh/deterministic/battery.json` 全部 `record.observation` 文本，5654 B）**：`POSITION_ASSERT_PASSED` **4**、`COIN_PICKED_UP` **1**、`WIN_DRIVEN` **1**、`COIN_NOT_PICKED_UP` **0**、`WIN_BLOCKED_UNDER_MOVE_RIGHT` **0**、`WIN_UNREACHED_WITHIN_BUDGET` **0**、`WIN_UNREACHABLE_GEOMETRICALLY` **0**、`STALE_ACTION_NOT_RELEASED` **0**、`COIN_COUNTER_UNREADABLE` **0**（`evidence/analysis/final_counts.txt`）。

### 2.4 E4 = met

```text
iteration=1  qa_status=partial  verified=11  gap=10
verified_ids = [F1,F2,F3,F4,F5,F7,F10,F13,F16,N1,N2]
gap_ids      = [F6,F8,F9,F11,F12,F14,F15,F17,N3,F5-COLL]
overlap: []        dup ids: []
execution_records: verified 身上=24, gap 身上=17, verified+gap=41   ← 两个作用域分别写清
MISSING=[]         record types {assert:23, build:2, replay:10, runtime_trace:6}
record candidate_ids = ["3d18b24d2432fa5eddf8b14c37bcdc4a3b739b4b4013556a0a769d77d147a26a"]
gaps lacking player_impact: []     gaps lacking recommended_update: []
planner_handoff: preservation_constraints=3 / update_targets=4 / validation_requirements=5
```

（`evidence/analysis/round_facts.txt`。**注**：T13 的验收 T13A-4 指出"verified-only/gap-only"曾被写成 10/13；本轮我按**记录挂在谁身上**统计，得到 **24/17**，总 41 不变。）

**与 T13 的判据侧变化（诚实读数）**：`N3`（编辑器错误）本轮**新成为 gap**；`F5-COLL`（Player/Goal 碰撞形状读不到，`shape_count=0`）也是新的；`F1`/`F2`/`F3`/`F4`/`F5`/`F7`/`F10`/`F13`/`F16`/`N1`/`N2` 继续 verified。

### 2.5 E5 = met（三棵树逐字节同一）

```text
versions/3d18b24d…   13 files / 8254 bytes
iter-1/candidate     13 files / 8254 bytes
live .workspace/fresh-t14  13 files / 8254 bytes
only_in_first=[]  only_in_second=[]  differing=[]   ALL_IDENTICAL = True
（三者 runtime-scheme id 均由我的独立实现复算为 3d18b24d…）
result.json.candidate_id == version_id == 3d18b24d…
```

⇒ **QA 未修改 `A_1`**。

### 2.6 E6 = met

`qa_report.md`（1813 B）逐字包含：

```text
# QA report - iteration 1 
"Status: **partial**. The bootable player-controller path plus the coin and win loop from this iteration's plan are working and were re-observed in one uninterrupted game-process run; the wider PRD (enemies, blocks, fail/restart, level scale, minor editor warnings) is not implemented or not observable." 
## What I checked 
"- Battery: read .hoh/deterministic/battery.json and every raw payload. All steps are ok except editor_errors_baseline (1 reproducible editor error) and node_and_collision_assertions (shape_count 0 for Player/Goal). Those two are recorded as gaps, and no claim depending on them is verified." 
## What remains open (gaps) 
"- F6 no wall exists … F8/F9 no contact damage and no stomp; F11/F12 no question block or breakable brick; F14/F15 only a silent life decrement + teleport, no observable fail/restart; F17 the level clears in ~7 s vs the 30-120 s target; N3 the editor error above; F5-COLL Player/Goal collision shapes unreadable in the assertion step." 
```

⇒ 未达成被**逐条声明**，编辑器错误被登记为 gap `N3`，**并且明确写"no claim depending on them is verified"**；与 `evidence.json` 的 11/10 划分逐条一致，**没有**把未达成写成 verified。
**口径说明**：本轮 QA 报告用的是 `"Status: **partial**."`，**不是** T12/T13 的 `Verdict: partial`；判据要的是诚实声明，不是那四个字母，但两个 token 的差异在此写明以免误读。

---

## 3. 角色侧 live 游戏路由与本轮新增的**探针**

### 3.1 普查（作用域写清，可复算）

**口径 A**：`runs/smoke-t14/iter-1/traj/*.json`（排除 `*.redacted.json`）的 `extra.actions[*].command`，**按命令行**计数：

```text
planner.attempt1     executed_commands= 16  tools_call= 0  running_game_*=0  editor_play_scene=0
developer.attempt1   executed_commands=211  tools_call=10  running_game_*=0  editor_play_scene=0
developer.attempt2   executed_commands= 89  tools_call=37  running_game_*=0  editor_play_scene=0
tester.attempt1      executed_commands=123  tools_call=64  running_game_*=75  editor_play_scene=0
TOTAL                executed_commands=439  tools_call=111 running_game_*=75  editor_play_scene=0
```

**口径 B**（同一语料，**按含该字符串的命令数**，并把每条命令与它的回包配对）：`running_game_*` 命令 **33** 条：**32 条 `returncode=0`**、**1 条 `returncode=1`**（一个多行 heredoc 命令自身失败，**不是** DR-43 拒绝）、**`game_endpoint_unavailable` 拒绝 0 条**。

**负控**：探测器对合成的 `tools call running_game_get_scene_tree` / `tools call editor_play_scene` 命中；对"分析命令里只提到 `running_game_`"不命中。

⇒ **两个口径都真，数字不同（75 vs 33），因为它们数的东西不同**（字符串出现次数 vs 命令条数）；本报告的每个数字都写明它属于哪个口径。

### 3.2 Tester 的 33 条 live 调用（原始回包节选）

T13 的"角色侧 live 游戏路由"结论在本轮**再次成立，而且规模大得多**——Tester 在电池 pass 2 发布路由之后跑了 **33** 条 `running_game_*` 命令，**0 条被 DR-43 拒绝**：

```text
msg 76  running_game_get_node_properties  returncode=0
        reply: {"node_path":"/root/Main/HUD/Result", …}
msg 76  running_game_get_scene_tree       returncode=0
msg 82  running_game_get_node_properties  returncode=0  (HUD/Victory, Lives, Enemy1, Coin1 …)
msg 88  running_game_run_test_scenario    returncode=0
msg 90  running_game_capture_screenshot   returncode=0   → res://.hoh/evidence/qa-victory.png（7640 B）
msg 157 running_game_get_node_properties  returncode=1   ← 该命令自身失败（heredoc/`/tmp` 形状），非拒绝
```

（`evidence/analysis/role_game_calls.txt`。）

### 3.3 三种命运同一个机制

| 观察 | 原始读数 | 归因性质 |
|---|---|---|
| 轮次开始那一次起游戏 | **成功**：`game_endpoint.json` = `{"endpoint":"http://127.0.0.1:64097/mcp","port":64097,"source":"auto_free_port","pid":35444}`，mtime `09:45:19`（我在 09:46 从盘上读到并留档） | **实测**（live 盘上捕获，`evidence/raw/live_snapshot_early.txt`） |
| 电池 pass 1 的起游戏 | `editor_play_scene` 应答 `:64145`（pid 32116，`playing=true`），随后 3 次轮询在 `1790906296/…6303/…6304`（09:58:16–24）全部连接被拒 ⇒ 端点被标 unavailable | **实测**（`quarantine/…/raw/play_scene_ready.json` + `mcp-errors.jsonl`） |
| **修复期**那一次起游戏 | 应答 `:64294`（pid 32536，CreationDate `09:58:24`，cmdline 逐字含 `"--mcp-port=64294"`），就绪轮询失败 ⇒ **DR-70**；`warnings.log` mtime `09:58:38`、那时 1110 B | **实测**（pid/CreationDate 来自 Win32_Process；DR-70 逐字在 `warnings.log`） |
| 电池 pass 2 的起游戏 | 应答 `:63860`（pid 7740），`running_game_get_scene_tree` **1 poll** 成功、22 节点 | **实测** |
| Tester 的 33 条 live 调用 | 32 成功 / 0 拒绝 | **实测** |

⇒ **四种命运（成功、就绪失败、就绪失败、成功）都在同一轮、同一二进制、同一工程上出现** ⇒ "角色侧 live 路由能不能用"**不是 CLI 的属性，而是"调用时刻有没有已发布且可用的路由"的属性**——这正是 T13 的 C-D，本轮把它从 2 个样本扩到 5 个。

**反例检验（T13A-1 的教训，我提前做了）**：我**没有**把 DR-70 归因到"轮次开始那次起游戏"。证据是三条独立读数同向：① 09:45:19 的盘上路由内容是 `:64097` 且**成功应答**；② DR-70 文本里点名的端点是 **`:64294`**，不是 `:64097`；③ `warnings.log` 的 mtime 是 `09:58:38`，而轮次开始是 `09:45:13`。

### 3.4 **我本人**对"角色自起场景 → 重发布路由"分支的探针（任务书增量 2）

**声明**：这不是角色行为，是**轮次作者**在轮次结束后用 harness 自己的工具调用命令走的一次**授权探针**。命令逐字：

```text
HOH_ROLE=developer
HOH_GAME_ROUTE=F:\moonbit-hof-rs\runs\smoke-t14\game_endpoint.json
HOH_HOH_BIN=F:\moonbit-hof-rs\target\release\hoh.exe
F:\moonbit-hof-rs\target\release\hoh.exe tools call editor_play_scene --args-file …\play_args.json --role developer
（args = {"mode": "main"}）
```

**第一次尝试失败（披露）**：我把 `scene_path` 当参数传了，引擎回 `-32602 Unknown parameter 'scene_path'`；`editor_play_scene` 只接受 `extra_args`/`headless`/`mcp_port`/`mode`（`evidence/probe/role_play_probe.txt`）。这正是 T12 §1.4 说过的"省略 `scene_path` 由引擎源码证明"的工程形态——**我按引擎回包改了参数，没有放宽任何策略**。

**第二次（`evidence/probe/role_play_probe3.txt`，逐字）**：

```text
ROUTE_BEFORE: exists=True  {"endpoint":"http://127.0.0.1:59429/mcp","port":59429,"source":"auto_free_port","pid":25424}  ← 陈旧（该游戏已停）
GODOT_BEFORE: [36808 编辑器]
CLI_START 10:27:43.271
NEW_GODOT_PROCESS first seen 10:27:43.270: pid=28892 … "--mcp-port=59546" --scene res://scenes/main.tscn …
ROUTE_FILE changed again at 10:27:44.399: {"endpoint":"http://127.0.0.1:59546/mcp","port":59546,"source":"auto_free_port","pid":28892}
CLI_END 10:27:44.401  elapsed=1.129s  exit=0
stdout（原始回包）:
{
  "content": [
    { "text": "{\"args_deduplicated\":[],\"args_injected\":[\"--mcp-port=59546\"],\"endpoint\":\"http://127.0.0.1:59546/mcp\",
              \"headless\":false,\"mcp_port\":59546,\"mcp_port_source\":\"auto_free_port\",\"mode\":\"main\",\"pid\":28892,\"playing\":true}", "type": "text" }
  ]
}
ROUTE_AFTER: exists=True  {"endpoint":"http://127.0.0.1:59546/mcp","port":59546,"source":"auto_free_port","pid":28892}  mtime=1790908064
```

**裁定**：

- **分支被走到了**：`hoh tools call editor_play_scene`（role 侧 CLI，`cli_impl.rs:74-89` 的 `GAME_START_TOOL` 分支）**成功重发布了 `runs/smoke-t14/game_endpoint.json`**，把陈旧路由（pid 25424）**换成了新游戏**（pid 28892, `:59546`）——**没有**保留旧路由，**没有**回落到编辑器端点；exit 0。
- **就绪等待的成本**：整条命令 **1.129 s**；新游戏进程在 CLI 启动后**同一轮询间隔内**出现；路由文件被改写发生在 **+1.128 s**。⇒ 就绪等待 ≈ **1.1 s**（`tools.ready_timeout_seconds = 30` 一次都没用满，第一次轮询就成功）。这**推翻**了"这条等待会拖累轮次"的担心（至少在这一轮的这个时刻）。
- **第一次探针**（`role_play_probe.txt`）也留档：那次失败是**参数错误**，路由未变。
- **收尾**：两次探针各起了一个游戏，我都用 `editor_stop_scene` 停掉并留原始回包 `{"message":"Playback stopped","stopped":true}`；收工时 `tasklist` 只剩编辑器 pid 36808（`evidence/probe/post_probe_processes.txt`）。

---

## 4. 任务书增量 3：启动门的**独立复现**（空目录 ⇒ role=game/73 工具）

**方法**：在**可证为空**的目录上启动引擎，控制台句柄在 spawn 前打开。

```text
LAUNCH_CMD: F:\moonbit-hof-rs\godot-mcp\godot\bin\godot.windows.editor.x86_64.mono.exe -e --path F:\moonbit-hof-rs\.workspace\fresh-t14 --mcp-port=9877
PROJECT_PATH_ENTRIES: []            PROJECT_GODOT_EXISTS: False
pid: 34448                          CreationDate: 2026/10/2 9:43:28
[MCP] role=game configured_port=9877 source=cmdline listen=true
[MCP] listening on 127.0.0.1:9877 (editor=false, tools=73)
[MCP] INFO: MCP server is ready on 127.0.0.1:9877 as the game process (port source=cmdline, tools=73)
```

**工具集普查（我直接向该端点发 `tools/list`，原始回包 `evidence/gatecheck/game_role_tools_list.json`）**：

```text
served_total = 73      duplicate_served_names = []
served_by_prefix = {"editor_": 0, "os_": 2, "project_": 48, "running_": 23}
契约 177 名（tools_list.renamed.json）：{"editor_": 104, "os_": 2, "project_": 48, "running_": 23}
SERVED BUT NOT IN CONTRACT = 0
IN CONTRACT BUT NOT SERVED = 104        not_served_by_prefix = {"editor_": 104}
editor_* served = 0 / 104               running_game_* served = 23 / 23
editor_play_scene served = False        running_game_get_scene_tree served = True
```

该端点上 `editor_status` 被引擎**拒绝**：`{"error":{"code":-32601,"message":"Method not found: editor_status"}}`（`evidence/gatecheck/game_role_editor_status.json`）。

**对照（唯一被翻转的变量是"目录里有没有 `project.godot`"）**：**同一二进制**（sha256 `08483088…`）在 init 之后的同一目录上启动 ⇒ `role=editor`、`tools=154`（`{editor_:104, project_:48, os_:2}`、`running_game_* served = 0`、`editor_play_scene served = True`）。

**收尾**：门进程用**精确 pid** `taskkill /PID 34448 /T /F` 停掉；随后 9877 只剩 `TIME_WAIT`（无 LISTENING）、无 godot 进程（`evidence/gatecheck/after_gate_kill_port.txt`）。**未使用 `rm -rf`；路径全部是字面量，没有从未展开的变量构造路径。**

⇒ **顺序必须是"先建空目录 → `hoh init` → 再由编辑器指向它"**（本轮第四次独立复现）。

---

## 5. 只读基线的未变证明（三口径）

**基线集合（11 条）**：`runs/smoke-t6..t13`（8）+ `.workspace/{mario,fresh-t11,fresh-t12}`（3）。

**口径 A（内容）**：PowerShell 5.1 `Get-ChildItem -Recurse -Force -File`；**仓根相对**小写 POSIX 路径 + TAB + 字节 + TAB + sha256；LF 连接、无尾随换行；`Sort-Object` **文化序**；整体 UTF-8 取 SHA-256。脚本 `evidence/scripts/baseline_digest.ps1`。三次测量（开工 `09:41`、轮结束 `10:21`、证据并入之后）**逐字节相同**：

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
```

**口径标定（承重的一步）**：同一口径**逐字复现了任务书点名的锚点** `runs/smoke-t6 = 135 文件 / c144ef32…7a9c03 / newest 2026-09-29 02:32:01`，且**逐条复现了 T13 报告公布表里的全部 10 条**（`evidence/analysis/baseline_check.txt`：`published lines reproduced = 10 / 10`）⇒ 不是我另造的口径。

**口径 B（第二个独立口径）**：把**整张基线表文本**取 SHA-256，三个时点相同：`6a36ffce9bedecfc733a60c01a63297f6503ea37cf05023e162e76826d33e844`。

**口径 C（时间窗）**：以轮次开始 `1790905513.791` 为界，Python 递归遍历（**不用这个 shell 的 `bash`：它解析到 WSL 的 bash，`find -newermt` 语义与 Git Bash 不同，第一次跑就报了 `WSL2 … ERROR_FILE_NOT_FOUND`，见 `evidence/analysis/baseline_check.txt` 的同段说明**）：

```text
files under runs/** newer than the window, excluding runs/smoke-t14 = 0 []
files under the three read-only workspace dirs newer than the window  = 0 []
```

⇒ **11 条只读基线在内容、文件数、mtime 三个口径上都未变**；本轮产出只落在 `.workspace/fresh-t14/**` 与 `runs/smoke-t14/**`。

**冻结件与仓库状态**：`PRD-mario.md` sha256 `4c81c3a9…5c3a`（逐字未变）；引擎二进制 sha256 `08483088…e9e6a`（**与 T11/T12/T13 记录逐字相同** ⇒ 本轮**未写** `godot-mcp/**`）；`DECISIONS.md` `5621b2ea…`、`.spec/hof-rs/REQUIREMENTS.md` `298a9489…`（记录，**本轮未改**）；`git status --porcelain` 只有 4 个未跟踪的仓根 `*.json`（§7.5）；`HEAD == origin/master == 44131d9`（**未 push**）。

---

## 6. `A_0`/`A_1` 摘要与身份（两种口径）

| 记号 | 运行时 id（= `versions/` 目录名） | 文件数 | 字节 | 我独立复算 |
|---|---|---|---|---|
| **A_0**（`hoh init` 脚手架） | `3ac25f6c5c38885febd3a001ea99c88aca61b1799c7b105306919886c2c1d151` | 3 | 1727 | 逐字命中 |
| **A_1**（developer + 电池后的冻结候选） | `3d18b24d2432fa5eddf8b14c37bcdc4a3b739b4b4013556a0a769d77d147a26a` | 13 | 8254 | 逐字命中 |
| `iter-1/candidate` = 活体工作区 | 同上 | 13 | 8254 | 同上 |

**口径**：运行时口径 = `src/runtime/policy.rs::hash_tree`（`relpath\n{len}\n{bytes}\n` 排序流，**路径保持原大小写**，排除 `.hoh/.git/.godot/.import/node_modules/target`）；我的独立实现 `evidence/scripts/tree_hash.py` **不调用** hof-rs 任何函数，并且**用 T13 的两个冻结树做过标定**（`3ac25f6c…` 3/1727 与 `a54179ce…` 13/9610 都逐字命中）。

---

## 7. 机制读数

原始：`evidence/analysis/{mechanisms,final_counts,redaction_check,dsh_context,godot_editor_dir_check}.txt`。

| 机制 | 本轮真实读数（作用域已写清） |
|---|---|
| **零增量** | **未发生**。`warnings.log`（1700 B / 6 个换行结尾的行）里 `Zero-increment`/`no_progress`/`no_engineering_write` 各 **0** 次；`A_1 ≠ A_0` 且差异落在工程文件 |
| **修复尝试** | `repair_retry_used=true`、`wrap_up_retry_used=false`、`wrap_up_retry_reason="not_triggered"`；`logs/developer.attempt2.log` 的 `notes` 逐字 `launch_gate_repair: the pre-freeze launchable gate failed`；**这一轮修复真的修好了东西**（pass 1 的 `main.gd` 解析错误在 pass 2 消失） |
| **可启动闸门** | **pass 1 `launchable=false`、pass 2 `launchable=false`**；最终 `artifact_gate.launchable=false`，`reasons` 只有一条（`editor_errors_baseline`）。pass 1 的步骤矩阵 12 步里 **4** 步 ok（`project_reload_and_open`/`scene_structure`/`editor_stop_scene`/`engine_identity`），`play_scene_ready` 起全 false；pass 2 **10/12** ok（`editor_errors_baseline` 与 `node_and_collision_assertions` 为 false） |
| **64 KiB 上限** | **触发 1 次**（**本路径的第二次真机触发**）：`tester.attempt1.json` **msg 29**：`hoh_output_truncated=true, limit=65536, original=79928`（解析 `extra` 字段，**不是** grep 字节——T13A-2 的教训） |
| **陈旧日志** | `editor_errors_baseline` 的 `source="editor_log"`、`in_process=true`；本轮**没有**"陈旧日志关门"可触发（它报的是当刻读到的日志尾） |
| **端点可达（角色侧）** | ✅ Tester **33** 条 `running_game_*` 命令：**32 exit 0 / 0 DR-43 拒绝**（1 条 exit 1 是该命令自身失败）；Developer/Planner **0** 条 |
| **路由就绪（三次起游戏）** | 轮开始 `:64097` **成功**；电池 pass 1 `:64145` **失败**（3 polls，两次 connection refused）；修复期 `:64294` **失败**（DR-70）；电池 pass 2 `:63860` **成功（1 poll）** |
| **退出码四处同数** | `exit_code` 字节 `36 0A`、`process_exit_code` 字节 `36 0A`、`meta.json.exit_code=6`、wrapper `ROUND_EXIT=6` |
| **usage 归属（DR-79 ②）** | 三角色 **ratio 全部 = 1.000**（planner 15/84,000、developer 210/7,242,788、tester 101/9,019,501；summary == attempts 之和）。**但我不把它当作"DR-79 ② 的确认"**：本轮 planner **没有** `.redacted` 旁路副本（T13 里造成 2.0 倍的那个形状本轮不存在），developer 的 summary 走的是"合并 attempt"的另一条路径 ⇒ 这是一次**阴性结果**，不是对修复的阳性检验。§7.3 |
| **脱敏** | 2 个轨迹各有 `.redacted.json` 旁路，**原件逐字节保留**；`result.json.secret_redactions = 7`；**但 `DSH_TERM_CMD` 与 `HOH_GAME_ROUTE` 的赋值在原件与旁路副本里都逐字存活** ⇒ **F-T14-2**，见 §7.4 |
| **越界写入（DR-25）** | `out_of_tree_writes = ["l.json","p2.json","pv.json","r.json"]`（**实测仍在仓根** `F:\moonbit-hof-rs\`，151/153/62/153 B，mtime `10:14:36–10:16:26`，`git status` 未跟踪）；`warnings.log` 里 `out_of_tree_cleanup` **0** 行（DR-79 ① 的清理只针对单分量的 `.tmp_*`/`tmp_*`/`*.tmp`/`*.bak`，这 4 个**不匹配**） |
| **图片证据** | `iter-1/candidate/.hoh/evidence/*.png` **11** 张（`frame-00` + 5 组 before/after + Tester 的 `qa-victory.png` 7640 B） |
| **轨迹合法性** | 6 个 JSON（4 原件 + 2 旁路）全部 `json.loads` 通过 |

### 7.3 usage 阴性结果的准确表述

```text
planner    summary calls=15  total=84000    | attempts calls=15  total=84000    | ratio=1.000
developer  summary calls=210 total=7242788  | attempts calls=210 total=7242788  | ratio=1.000
tester     summary calls=101 total=9019501  | attempts calls=101 total=9019501  | ratio=1.000
traj 文件：developer.attempt1.json / developer.attempt1.redacted.json / developer.attempt2.json /
          developer.attempt2.redacted.json / planner.attempt1.json / tester.attempt1.json
```

⇒ 本轮**没有**出现 T12/T13 的 2 倍；但**造成那个 2 倍的形状（planner 在 summary 生成前已有旁路副本）本轮不存在**，所以这**不能**证明 DR-79 ② 的过滤器生效。要证明它，需要一个 planner 旁路副本存在、且 summary 走 `usage_from_attempts` 的轮次。

### 7.4 缺陷 F-T14-2：`DSH_TERM_CMD` 脱敏在真机上**没有生效**

**读数（可复算）**：

```text
== developer.attempt1.json (原件) ==            DSH_TERM_CMD=cd 出现 4 次
== developer.attempt1.redacted.json (旁路副本) == DSH_TERM_CMD=cd 出现 4 次；DSH_TERM_CMD=<redacted> 出现 0 次
== developer.attempt2.json (原件) ==            DSH_TERM_CMD=cd 出现 2 次
== developer.attempt2.redacted.json ==           DSH_TERM_CMD=cd 出现 2 次；DSH_TERM_CMD=<redacted> 出现 0 次
（同一份副本里 HOH_MODEL_API_KEY=<redacted> 出现 4 次、<redacted> 共 7/10 次）
```

逐字存活的内容是**我自己的 harness 命令行**（含仓外暂存路径 `F:\moonbit-hof-rs-t14-staging` 与脚本名），例如（节选，逐字来自冻结件）：

```text
DSH_TERM_CMD=cd /f/moonbit-hof-rs && python \"F:/moonbit-hof-rs-t14-staging/scripts/run_stream.py\" --out \"F:/moonbit-hof-rs-t14-staging/round/round_console.txt\" …
```

**反例检验**：

- **不是"脱敏没运行"**：同一份副本里 `HOH_MODEL_API_KEY=<redacted>`（4 次）与 `<redacted>`（共 7 次）都在 ⇒ 脱敏管线跑了。
- **不是"这个变量名不在名单里"**：`src/runtime/secrets.rs:84-99` 的 `HARNESS_ENV_VARS` **逐字**含 `"DSH_TERM_CMD"`，且 `:198 COMMAND_LINE_VARS = &["DSH_TERM_CMD"]`；重建后的二进制里该串出现 **1** 次。
- **不是"值不敏感所以跳过"**：DR-79 ④ 的注释逐字写明它要被脱敏。
- **但是**：`HOH_GAME_ROUTE=F:` 也**同样**没有被脱敏（0 次 `<redacted>`，4 次原样），而 `HOH_ROLE`/`HOH_RUN_DIR`/`HOH_RUN_ID`/`HOH_SCRATCH_DIR`/`HOH_TOOLS_ENDPOINT`/`HOH_VIEW_DIR`/`PATH` **被脱敏了** ⇒ 同一份转储里名单上的名字**有的被处理有的没有**。
- **未定因**：我**没有**插桩脱敏器、也没有在轮内读它的 span 报告（`result.json` 里没有 refusal 列表）。⇒ 结论**只到"观察到的现象"**：**在含 DR-79 ④ 的修订上，一条真机轮的 harness 命令行仍然进入了冻结件与其旁路副本**。机理**未确定**。
- **安全影响的作用域**：泄漏的是**路径与命令行**，**不含**密钥值（`HOH_MODEL_API_KEY` 的值 0 命中；见 §9 的扫描）。这与 T13A-5 是同一类"披露等级"，但 T13A-5 的修复被宣称已关闭它 ⇒ 本轮证明**没有关闭**。

### 7.5 仓根 4 个越界文件的处置

`l.json` / `p2.json` / `pv.json` / `r.json` 是本轮 tester 在仓根写下的（`result.json.out_of_tree_writes` 逐字记录，DR-25 是"检出但不阻止"）。DR-79 ① 的有界清理**没有**它们，因为它们的名字不符合单分量临时形状（`.tmp_*`/`tmp_*`/`*.tmp`/`*.bak`）。**我按"不删"处理**（它们是本轮的取证对象，删掉就等于删证据），并在此点名它们会让 `git status` 一直有 4 个 `??`。我**没有**把它们提交。

---

## 8. 报告纪律自证

### (a) 全部"0 次 / 逐位相同 / 不存在"断言都可从其引用的文件复算，且写明作用域

| 断言 | 作用域 | 复算方式 / 文件 |
|---|---|---|
| `editor_play_scene` 角色调用 = **0 次** | 4 个未脱敏 `traj/*.json` 的 `extra.actions[*].command` | `evidence/scripts/traj_audit.py` → `evidence/analysis/traj_audit.txt` |
| `running_game_*` 命令 = **33** 条（口径 B）／字符串出现 **75** 次（口径 A） | 同上 | `evidence/scripts/role_game_calls.py`、`traj_audit.py` |
| `game_endpoint_unavailable` 角色侧拒绝 = **0** | 同上 | `role_game_calls.py` |
| 11 条只读基线**逐位未变** | 11 个目录的全部文件 | 三份 `baseline_*_repo.txt` + `baseline_check.txt`（三口径） |
| 三棵树**逐字节相同** | `versions/3d18b24d…`、`iter-1/candidate`、`.workspace/fresh-t14`（排除 `.hoh/.git/.godot/.import/node_modules/target`） | `evidence/scripts/tree_hash.py compare` |
| `out_of_tree_cleanup` 行 = **0** | `runs/smoke-t14/warnings.log` 全文（1700 B） | `evidence/analysis/mechanisms.txt` |
| 轮次窗口外**没有**文件被写 | `runs/**`（除 `runs/smoke-t14`）与三个只读工作区 | `baseline_check.txt` 口径 C |
| 二进制里三个标记**各 ≥1** | `target/release/hoh.exe` 的原始字节 | `evidence/scripts/binary_markers.py` |

### (b) 机制归因附反例检验（"没看到 X" ≠ "X 不可能"）

见 §0.1 的四条反例、§3.3 的 T13A-1 预防、§7.4 的四条反例。要点：**E2 的红我做了四条反例检验**（不是权限、不是普遍行为、不是脚本错误、字段不稳定），并把**未定因**（为什么 t14 没重建 `.godot/editor/`）明确标为未定；**F-T14-2 的机理我明确标为未定**，只给出可复算的现象。

### (c) 机器可读块由 JSON 序列化器生成 + 栅栏感知 `json.loads` 回读（**已做**）

- **生成**：`evidence/scripts/build_json_block.py`（内部 `json.dump(..., ensure_ascii=False, indent=2)`，并在写盘前 `assert` 了本轮承重数字：`exit_code==6`、`start_state.mode=="fresh"`、`len(verified)==11`、`len(gap)==10`、`records==41`、`A1=="3d18b24d…"`、`launchable==False`）⇒ `evidence/analysis/machine_block.json`。
- **装配**：`evidence/scripts/assemble_report.py` 把该文件的**字节原样**插入 ```json 栅栏。
- **回读**：`evidence/scripts/json_block_check.py`（按行锚定的 ``` 切块、只对 info string 为 `json` 的块 `json.loads`，并与 `machine_block.json` 比字节）⇒ `evidence/analysis/json_block_check.txt`。

### (d) 派生物数字与正文一致

正文所有数字都取自同一批脚本产物（`round_facts.txt`、`battery_reads.txt`、`e3_extract.txt`、`baseline_check.txt`、`traj_audit.txt`、`role_game_calls.txt`、`mechanisms.txt`、`final_counts.txt`、`sizes.txt`、`editor_errors_probe.txt`、`redaction_check.txt`、`godot_editor_dir_check.txt`、`project_inventory.txt`），机器块由 `build_json_block.py` 从**同一批冻结件**重读生成并带 `assert`。**所有派生文本都由 Python 以 `encoding="utf-8"` 显式写盘，没有一次控制台重定向**（`evidence/analysis/utf8_scan.txt`：`NOT VALID UTF-8 = 0`）。

---

## 9. 遗留风险与未验证项（严格区分实测 / 推断 / 未知）

**实测（本轮有原始证据）**

1. 空目录（0 条目）→ `hoh init` exit 0 → **恰好一轮** `hoh run`；`start_state=fresh`；`A_0` 3 文件/1727 B 与 T11/T12/T13 同 id。
2. **E1/E3/E4/E5/E6 met；E2 not met**（`artifact_gate.launchable=false`，exit 6）。
3. **E3 四类全齐**，且**金币 `0 → 1`** 与 `Goal.reached false → true` 都来自游戏端点语义工具的原始回包，各带引擎侧 `passed=true`。
4. **角色自起场景 → 重发布路由的分支被走到**（由我本人探针，非角色）：路由文件被换成新游戏，exit 0，就绪等待 ≈ **1.1 s**。
5. **角色侧 live 路由第三次被真机证明可用**：Tester 33 条命令，32 成功、0 拒绝。
6. 电池 pass 1 失败（含**真的** `main.gd` 解析错误 + `:64145` 就绪失败），修复重试把脚本修好，pass 2 只剩编辑器缓存写错误。
7. **64 KiB 截断触发 1 次**（79,928 → 65,536）。
8. **`DSH_TERM_CMD` 在原件与旁路副本里都未脱敏**（现象实测，机理未定）。
9. 11 条只读基线三口径未变；三棵树逐字节同一；退出码四处同为 6。
10. 三次起游戏的就绪命运（成功/失败/失败/成功）与 5 个观察点。
11. 本轮所有派生文本合法 UTF-8，**密钥值 0 命中**。

**推断（不得当作已测）**

1. **（≈0.8）** `.godot/editor/` 之所以缺失，是 `--fresh-workspace` 在编辑器已指向工程之后清空工作区、而编辑器这次没有重建该目录；支持：`purge_contents` 逐字清空每个条目、编辑器在 09:44:28 已指向、`.godot/uid_cache.bin` 在 09:57:41 被重建**但没有 `editor/` 子目录**、且四个别的工程都有该文件。**我没有插桩编辑器的缓存落盘时刻。**
2. **（≈0.6）** 轮开始那次起游戏（`:64097`）与 pass 1（`:64145`）之间的失败差异来自游戏进程绑定 MCP 端口的早晚；四轮里同一形态反复出现，但 ready 超时与轮询间隔我**没有**仪器化。
3. **（≈0.5）** tester 的 1 条 `returncode=1`（msg 157）是那条 heredoc/`/tmp` 命令自身在 `cmd.exe` 下的失败，不是工具通道问题；我只读了它的命令行与 returncode。

**未达到 / 未知（必须点名）**

1. **F-T14-1（major，判据侧）**：**E2 not met / 退出码 6**，门把"编辑器缓存写失败"当成"工程不可启动"。根因（为什么 t14 的 `.godot/editor/` 没被重建）**未定**。
2. **F-T14-2（major，卫生）**：**`DSH_TERM_CMD` 与 `HOH_GAME_ROUTE` 的赋值在冻结件与其脱敏副本里都原样存活**；DR-79 ④ 宣称关闭的披露类别**没有关闭**。机理未定。
3. **F-T14-3（minor）**：`out_of_tree_writes` 的 4 个仓根 `*.json` 仍在，DR-79 ① 的有界清理形状覆盖不到它们（它只清 `.tmp_*`/`tmp_*`/`*.tmp`/`*.bak`）。
4. **F-T14-4（minor）**：`editor_get_errors` 的读数**不稳定**（轮内是 `filesystem_cache10`，轮后是 `[MCP] capture=off…`），而门把它当硬判据。
5. **F-T14-5（info）**：DR-79 ② 的 usage 过滤器本轮**没有被区分性地检验**（没有 planner 旁路副本）。
6. **本轮未复现/未检验**：`usage` 双计（2.0 倍）没有出现；`wrap_up_retry` 没有触发；`out_of_tree_cleanup` 没有产出任何行。

---

## 10. 诚实披露（含重试、意外写入）

1. **二进制**：为了让构建日志有真的 `Compiling` 行，我先 `touch src/main.rs` 再 `cargo build --release --offline`；**只改 mtime 不改内容**（`git status` 直到报告前只有 4 个未跟踪 `*.json`）。旧二进制（`310075fa…`）确实陈旧，必须重建。
2. **`hoh doctor` 的 `godot.engine_version` FAIL**：我用"目录存在 vs 不存在"的对照与一次直接 `--version` 把它归因成"探针 cwd 不存在"，**没有**接受表面的 FAIL，也**没有**拿它当引擎问题。
3. **探针第一次失败**：我把 `scene_path` 当 `editor_play_scene` 的参数传了，引擎回 `-32602`；两份转录都留档（`role_play_probe.txt` / `role_play_probe3.txt`）。
4. **引擎我启动了 3 次**（门 pid 34448 精确停掉；编辑器 pid 36808 收工仍存活；探针各起一个游戏，各用 `editor_stop_scene` 停掉并留回包）。收工时 `tasklist` 只有编辑器。
5. **口径 C 第一次跑失败**：这个 shell 的 `bash` 解析到 WSL bash，`find -newermt` 报了 `WSL2 … ERROR_FILE_NOT_FOUND`；我改成 Python 递归遍历（`os.walk` + mtime 比较）并把这个改动的理由写进 `baseline_check.txt` 的同段，**没有**把失败的那次说成"空结果"。
6. **`git status` 是脏的**：仓根 4 个未跟踪 `*.json` 是本轮 tester 的越界写入，我按"不删、留证据"处理并点名。
7. **密钥卫生**：`HOH_MODEL_API_KEY` 只从 `config/model.secret.env` 注入**子进程环境**（`capture.py`/`run_stream.py` 的 `--env-from-secret`），**只报长度 51、从不打印**；对 `runs/smoke-t14/**` 与暂存目录的扫描 **0** 处含该值（§9 第 11 条）。
8. **未 push**：`origin/master == 44131d9…`（与开工相同）；本轮提交只含报告文件。
9. **本报告的证据全部来自本轮**；对 T10–T13 的引用只用于**口径标定**与**历史对照**，不冒充本轮读数。

---

## 11. 本轮是否闭合"**最终修订版只被离线验证过**"这个缺口？

**结论：部分闭合，且带一条新的、必须立刻进队列的红。**

**支持（本轮实测）**

1. **运行的是含最后两批修复的修订**：开工 `HEAD = 44131d9`，其祖先含 `ec90c19`(DR-79) 与 `3e727b9`(DR-80)；`git diff --name-status 8ddbad3..HEAD` 逐字显示 `src/runtime/{hygiene,run_loop,secrets,usage}.rs` 与 `tests/**` 被改。开工的二进制（`310075fa…`）**早于**这些改动 ⇒ **确实重建**成 `3b97e4a0…`，并在其字节里找到三处标记。
2. **同一条命令序列在这一修订上真的跑完了**：空目录 → `init` → **恰好一轮** `run`，36m07s，`start_state=fresh`，产出 `A_1 = 3d18b24d…`。
3. **六条判据里五条 met**（E1/E3/E4/E5/E6），且 E3 是本目标迄今**最强**的一次（四类齐备 + 真 0→1 + 四发位置断言）。
4. **三条悬挂的行为，两条继续为绿、第三条首次被走到**：陈旧动作释放（7 批 60/60 唯一 x）、观测早于消耗（`Coins: 0` 起点）、**角色自起场景重发布路由（我本人探针，exit 0 + 路由被换）**；角色侧 live 路由本身第三次被证明可用（33 条命令、0 拒绝）。
5. **11 条只读基线三口径未变**；引擎二进制与 T11–T13 记录逐字相同。

**反对（本轮实测）**

1. **`hoh run` 首次以非 0 退出（6）**，`artifact_gate.launchable=false` ⇒ **E2 not met**。这条红虽然来自编辑器缓存而不是项目，但它**恰恰只可能在真机上暴露**——离线测试一路是绿的，所以"离线验证过"这个缺口**没有被完全关上**，反而给出了一个它为什么会漏的真机反例。
2. **DR-79 ④ 的 harness 命令行脱敏在真机上没有生效**（`DSH_TERM_CMD` 与 `HOH_GAME_ROUTE` 的赋值原样进入冻结件与脱敏副本）。这是"离线测试绿、真机红"的**第二**个实例。
3. **`editor_get_errors` 的读数不稳定**，而闸门把它当硬判据 ⇒ 同一份工程可以在两分钟内被判"不可启动"与"可启动"，取决于日志尾里恰好有什么。

**一句话**：**本轮把"当前修订只被离线验证过"这个缺口从"完全未验证"推进到"已在一台真机、一条完整命令序列上验证过，并抓到两条只有真机能暴露的红"**；它**没有**给出"当前修订真机全绿"的结论——恰恰相反，它给出了两条应当立刻进队列的缺陷（F-T14-1、F-T14-2）。

---

## 12. 工件索引

| 类别 | 路径 |
|---|---|
| 轮记录（运行时） | `runs/smoke-t14/`：`exit_code`、`process_exit_code`、`meta.json`、`warnings.log`、`TOOLS.md`、`versions/{index.json,3ac25f6c…,3d18b24d…}`、`quarantine/deterministic-pass-1.stale-1790906763/**`、`iter-1/{plan.md,result.json,evidence.json,qa_report.md,logs/,traj/,planner-view/,candidate/}` |
| 被开发工程 | `.workspace/fresh-t14/**`（`project.godot`、`scenes/main.tscn`、`scripts/*.gd`） |
| 原始取证（本轮自建，已并入） | `runs/smoke-t14/evidence/**`：`round/**`、`analysis/**`、`gatecheck/**`、`probe/**`、`raw/**`、`scripts/**`，另有 `evidence/COPY_MANIFEST.txt`；**逐文件的字节数与 sha256 见文末自动生成的证据索引** |
| 可复跑脚本 | `runs/smoke-t14/evidence/scripts/**`（`capture.py`、`run_stream.py`、`launch_engine.py`、`empty_proof.py`、`port_preflight.py`、`tree_hash.py`、`tool_census.py`、`mcp_call.py`、`binary_markers.py`、`round_facts.py`、`battery.py`、`e3_extract.py`、`traj_audit.py`、`role_game_calls.py`、`probe_role_play.py`、`live_snapshot.py`、`live_timeline.py`、`snapshot_det.py`、`editor_errors_probe.py`、`godot_editor_dir_check.py`、`redaction_check.py`、`dsh_context.py`、`baseline_digest.ps1`、`baseline_check.py`、`mechanisms.py`、`final_counts.py`、`build_json_block.py`、`assemble_report.py`、`json_block_check.py` 等） |
| 分析输出 | `runs/smoke-t14/evidence/analysis/**`（全部由 Python 以 `encoding="utf-8"` 显式写盘；逐文件字节数见文末索引） |
| 规范 / 任务书 | `.spec/hof-rs/REQUIREMENTS.md`（E1..E6 第 110–119 行）、`.spec/hof-rs/OBJECTIVE-COMPLETION.md`、`tasks/TASK-SMOKE-T12.md`、`tasks/TASK-SMOKE-T13.md`（**无 `TASK-SMOKE-T14.md`**；本轮的增量条款来自调度者的派发指令） |
| 上轮对照 | `tasks/TASK-SMOKE-T12-REPORT.md`/`-ACCEPTANCE.md`、`TASK-SMOKE-T13-REPORT.md`（含 DR-79/DR-80 追加勘误）/`-ACCEPTANCE.md` |
| 相关决策（只读） | `DECISIONS.md` **D289–D293** |

---

## 附：机器可读结论

（本块由 `evidence/scripts/build_json_block.py` 用 `json.dump(..., ensure_ascii=False, indent=2)` 序列化，并在写盘前 `assert` 了本轮全部承重数字；与 `evidence/analysis/machine_block.json` **逐字相同**，由 `evidence/scripts/assemble_report.py` 以**字节原样**插入。落盘后由 `evidence/scripts/json_block_check.py` 以**行锚定、栅栏感知**的方式 `json.loads` 回读并比字节。）

```json
{
  "task": "TASK-SMOKE-T14",
  "kind": "final-revision real round: the T12/T13 command sequence rerun on the HEAD that carries the last corrective batches, plus the authorised role-started-scene probe",
  "round_id": "smoke-t14",
  "run_dir": "runs/smoke-t14",
  "project_dir": ".workspace/fresh-t14",
  "evidence_dir": "runs/smoke-t14/evidence",
  "head_at_start": "44131d983ed100a65775d5dfa865bcc6ed7fa4a4",
  "head_at_report_time": "44131d983ed100a65775d5dfa865bcc6ed7fa4a4",
  "last_corrective_commits_on_this_ancestry": {
    "DR-79": "ec90c19",
    "DR-80": "3e727b9",
    "src_files_changed_from_8ddbad3_to_HEAD": [
      "src/runtime/hygiene.rs",
      "src/runtime/run_loop.rs",
      "src/runtime/secrets.rs",
      "src/runtime/usage.rs",
      "tests/append_only_guard.rs",
      "tests/launchable_gate.rs",
      "tests/role_paths.rs",
      "tests/usage_extraction.rs"
    ]
  },
  "commands": {
    "init": "target/release/hoh.exe init --project F:\\moonbit-hof-rs\\.workspace\\fresh-t14",
    "run": "target/release/hoh.exe run --iterations 1 --run-id smoke-t14 --fresh-workspace --project F:\\moonbit-hof-rs\\.workspace\\fresh-t14",
    "engine_launch": "F:\\moonbit-hof-rs\\godot-mcp\\godot\\bin\\godot.windows.editor.x86_64.mono.exe -e --path F:\\moonbit-hof-rs\\.workspace\\fresh-t14 --mcp-port=9877",
    "identical_to_t12_t13_apart_from": [
      "the run id",
      "the project directory"
    ]
  },
  "binary": {
    "path": "target/release/hoh.exe",
    "size_bytes": 12727808,
    "mtime_unix": 1790905290,
    "sha256": "3b97e4a02436bac781a41e3675ac7c4cb341c44d1682c297c3911d5d0cb80ba3",
    "rebuilt_this_round": true,
    "stale_predecessor_sha256": "310075faea14317af48a9602f7baedb1fc1e0d2af8bb4a057f3f00cb4f7158ca",
    "marker_counts": {
      "STALE_ACTION_NOT_RELEASED": 1,
      "route_publish_readiness_message": 1,
      "DSH_TERM_CMD": 1
    },
    "marker_evidence": "runs/smoke-t14/evidence/round/binary_markers.txt"
  },
  "engine": {
    "version_string": "4.8.dev.mono.custom_build.035edfce7",
    "sha256": "08483088a4a2772841cd3b4c916b2d45b3cb6255656cf3951598a86fce7e9e6a",
    "size_bytes": 194216960,
    "listener_pid": 36808,
    "matches_binary": true,
    "started_by_this_round": true,
    "alive_at_report_time": true
  },
  "role_gate_reproduction": {
    "empty_dir_launch": {
      "pid": 34448,
      "project_godot_exists": false,
      "project_dir_entries": [],
      "role": "game",
      "tools_served": 73,
      "operator_prefix_counts": {
        "editor_": 0,
        "project_": 48,
        "running_": 23,
        "os_": 2
      },
      "in_contract_not_served": 104,
      "not_served_by_prefix": {
        "editor_": 104
      },
      "editor_status_refused": "{\"error\":{\"code\":-32601,\"message\":\"Method not found: editor_status\"}}",
      "console": "runs/smoke-t14/evidence/gatecheck/gate_game_role_console.txt",
      "tools_list": "runs/smoke-t14/evidence/gatecheck/game_role_tools_list.json"
    },
    "after_init_launch": {
      "pid": 36808,
      "role": "editor",
      "tools_served": 154,
      "operator_prefix_counts": {
        "editor_": 104,
        "project_": 48,
        "running_": 0,
        "os_": 2
      },
      "same_binary_sha256": "08483088a4a2772841cd3b4c916b2d45b3cb6255656cf3951598a86fce7e9e6a",
      "project_list_scripts_count": 0,
      "mario_scripts_on_disk": 15
    },
    "conclusion": "reproduced for the fourth time; the only variable flipped between the two launches was the presence of project.godot, so the order empty-dir -> hoh init -> point the editor is load-bearing"
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
      "runtime_id": "3d18b24d2432fa5eddf8b14c37bcdc4a3b739b4b4013556a0a769d77d147a26a",
      "files": 13,
      "bytes": 8254,
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
    "runtime_evidence_diff_agrees": true,
    "three_trees_byte_identical": true
  },
  "timing": {
    "started_console": "2026-10-02 09:45:13",
    "ended_console": "2026-10-02 10:21:20",
    "elapsed_seconds": 2166.928,
    "round_exit": 6,
    "rounds_that_actually_started": 1,
    "aborted_launches": 0
  },
  "exit_codes": {
    "exit_code_hex": "360a",
    "process_exit_code_hex": "360a",
    "meta_exit_code": 6,
    "wrapper_round_exit": 6,
    "all_four_agree": true,
    "value_is_not_zero_because": "artifact_gate.launchable=false"
  },
  "verdicts": {
    "E1": "met",
    "E2": "not_met",
    "E3": "met",
    "E4": "met",
    "E5": "met",
    "E6": "met"
  },
  "criteria": [
    {
      "id": "E1",
      "pass": true,
      "evidence": "empty directory proven (absent, then 0 entries) -> init exit 0 -> exactly one run; start_state fresh; A0 3ac25f6c 3 files/1727 B -> A1 3d18b24d 13 files/8254 B (10 added, main.tscn modified, 0 removed); plan.md carries all three required sections; evidence.json parses; attempts planner RepeatedFormatError artifact_valid=true, developer 1+2 LimitsExceeded artifact_valid=true (attempt2 = launch-gate repair), tester RepeatedFormatError artifact_valid=true; exit codes agree four ways at 6"
    },
    {
      "id": "E2",
      "pass": false,
      "evidence": "The product's own gate says no: artifact_gate {applicable:true, launchable:false}, reasons = one entry, editor_errors_baseline: editor reported 1 error(s) = \"Cannot create file 'res://.godot/editor/filesystem_cache10'. Check user write permissions.\"; exit_code 6. The other half of the gate is green: editor_play_scene answered playing=true (endpoint http://127.0.0.1:63860/mcp, pid 7740), running_game_get_scene_tree returned 22 nodes, 10 of 12 battery steps ok. Counterexamples: icacls identical to fresh-t13 (not permissions); four other projects carry .godot/editor/filesystem_cache10 and only fresh-t14 lacks the directory; pass 2 carries no Parse Error while pass 1 did (6 errors incl. res://scripts/main.gd:8), so the repair fixed the real script error; a later live editor_get_errors call returned a different, non-error line ([MCP] capture=off ...). Cause of the missing directory not instrumented -> undetermined."
    },
    {
      "id": "E3",
      "pass": true,
      "evidence": "All four classes from the game endpoint's semantic tools: move_left x 2085.65844726562 -> 1869.32629394531 (delta -216.33215332031, 60/60 unique); move_right x 1817.99340820312 -> 2034.32434082031 (delta +216.33093261719, 60/60 unique); jump a pure vertical arc (x unique=1 at 2096.65869140625, y 283.591979980469 -> min 234.258605957031 -> 267.480834960938, y unique=30); interactable object Coins: 0 (call 0) -> Coins: 1 (call 48) with running_game_assert_node_state text:neq passed=true; win Goal.reached false (calls 1/10/16/22/28/34/40) -> true (calls 46/49) with reached:neq passed=true. Four POSITION_ASSERT_PASSED lines and two passing assert_node_state replies in the battery observation text (5654 B), which carries COIN_PICKED_UP once and WIN_DRIVEN once"
    },
    {
      "id": "E4",
      "pass": true,
      "evidence": "11 verified [F1,F2,F3,F4,F5,F7,F10,F13,F16,N1,N2] / 10 gap [F6,F8,F9,F11,F12,F14,F15,F17,N3,F5-COLL], overlap [], no duplicate ids; 41 execution records, 24 attached to verified claims and 17 attached to gap claims (scopes stated), every path exists (MISSING=[]), every record candidate_id = A1; every gap carries player_impact and recommended_update; planner_handoff 3/4/5"
    },
    {
      "id": "E5",
      "pass": true,
      "evidence": "versions/3d18b24d, iter-1/candidate and live .workspace/fresh-t14 are byte-identical: 13 files / 8254 B each, only_in=[], differing=[], all three ids recomputed by an independent implementation"
    },
    {
      "id": "E6",
      "pass": true,
      "evidence": "qa_report.md opens 'Status: **partial**.' and enumerates the open items (F6/F8/F9/F11/F12/F14/F15/F17/N3/F5-COLL) with player impact; it records the editor error as gap N3 and writes 'no claim depending on them is verified'; no unmet item is reported as verified"
    }
  ],
  "criteria_note": "E2 is scored by the product's own operational definition of launchable, which is false for this run, even though the criterion's two literal clauses (bootable, no compile/script error) are satisfied by the raw evidence; the discrepancy is itself this round's headline finding.",
  "behaviours": {
    "stale_action_release": {
      "verdict": "green",
      "evidence": "interaction_evidence call[4] running_game_play_input_recording 'interaction:release_stale_move_left' -> {event_count:1, injected:1, replayed:true, speed:1.0}, before the first driven batch at call[6]; the seven batches then advance 60/60 unique x each"
    },
    "observe_before_consume": {
      "verdict": "green",
      "evidence": "battery step order: interaction_evidence (6) < input_channel_probe (7) < input_replay (8); the window's own readings start at Coins: 0 (call 0) and end at Coins: 1 (call 48), with COIN_PICKED_UP and WIN_DRIVEN",
      "coin_before": "Coins: 0",
      "coin_after": "Coins: 1"
    },
    "role_started_scene_route_republish": {
      "verdict": "EXERCISED BY A PROBE BY THE ROUND AUTHOR, NOT BY A ROLE",
      "role_calls_in_the_round": {
        "editor_play_scene": 0
      },
      "probe": {
        "role": "developer",
        "command": "F:\\moonbit-hof-rs\\target\\release\\hoh.exe tools call editor_play_scene --args-file <staging>\\play_args.json --role developer",
        "env": {
          "HOH_ROLE": "developer",
          "HOH_GAME_ROUTE": "F:\\moonbit-hof-rs\\runs\\smoke-t14\\game_endpoint.json"
        },
        "args": {
          "mode": "main"
        },
        "exit_code": 0,
        "raw_reply": "{\"args_deduplicated\":[],\"args_injected\":[\"--mcp-port=59546\"],\"endpoint\":\"http://127.0.0.1:59546/mcp\",\"headless\":false,\"mcp_port\":59546,\"mcp_port_source\":\"auto_free_port\",\"mode\":\"main\",\"pid\":28892,\"playing\":true}",
        "route_before": "{\"endpoint\":\"http://127.0.0.1:59429/mcp\",\"port\":59429,\"source\":\"auto_free_port\",\"pid\":25424}",
        "route_after": "{\"endpoint\":\"http://127.0.0.1:59546/mcp\",\"port\":59546,\"source\":\"auto_free_port\",\"pid\":28892}",
        "new_game_pid": 28892,
        "readiness_wait_seconds": 1.128,
        "whole_command_seconds": 1.129,
        "ready_timeout_seconds_configured": 30,
        "conclusion": "the branch publishes the route the role-started game announced instead of keeping the stale one; the readiness wait cost ~1.1 s and never approached the configured 30 s",
        "evidence": "runs/smoke-t14/evidence/probe/role_play_probe3.txt"
      },
      "first_probe_attempt_failed_on_args": "scene_path is not a parameter of editor_play_scene (-32602); disclosed, see probe/role_play_probe.txt",
      "cleanup": "both probe games were stopped with editor_stop_scene {\"message\":\"Playback stopped\",\"stopped\":true}; at close only the editor pid 36808 remained"
    }
  },
  "role_live_calls": {
    "caliber_a_scope": "extra.actions[*].command in the four unredacted final trajectories; counts occurrences of running_game_* per command line",
    "caliber_a_per_trajectory": {
      "planner.attempt1": {
        "executed_commands": 16,
        "tools_call": 0,
        "running_game_star_occurrences": 0,
        "editor_play_scene": 0
      },
      "developer.attempt1": {
        "executed_commands": 211,
        "tools_call": 10,
        "running_game_star_occurrences": 0,
        "editor_play_scene": 0
      },
      "developer.attempt2": {
        "executed_commands": 89,
        "tools_call": 37,
        "running_game_star_occurrences": 0,
        "editor_play_scene": 0
      },
      "tester.attempt1": {
        "executed_commands": 123,
        "tools_call": 64,
        "running_game_star_occurrences": 75,
        "editor_play_scene": 0
      }
    },
    "caliber_a_total": {
      "executed_commands": 439,
      "tools_call": 111,
      "running_game_star_occurrences": 75,
      "editor_play_scene": 0
    },
    "caliber_b_scope": "same corpus, commands containing running_game_, paired with the tool message that carries their output",
    "caliber_b_total": {
      "commands": 33,
      "exit_zero": 32,
      "exit_one": 1,
      "game_endpoint_unavailable_refusals": 0
    },
    "negative_control": "the detector fires on synthetic tools call running_game_get_scene_tree / editor_play_scene and does not fire on a bare mention of running_game_ inside an analysis command",
    "evidence": "runs/smoke-t14/evidence/analysis/role_game_calls.txt"
  },
  "start_round_game_attempts": [
    {
      "when": "2026-10-02 09:45:19",
      "endpoint": "http://127.0.0.1:64097/mcp",
      "pid": 35444,
      "outcome": "success",
      "evidence": "runs/smoke-t14/evidence/raw/live_snapshot_early.txt (read off disk at 09:46:19 while the route was live)"
    },
    {
      "when": "2026-10-02 09:58:16-24",
      "endpoint": "http://127.0.0.1:64145/mcp",
      "pid": 32116,
      "outcome": "readiness failed after 3 polls (2 connection refused)",
      "evidence": "runs/smoke-t14/quarantine/deterministic-pass-1.stale-1790906763/raw/play_scene_ready.json"
    },
    {
      "when": "2026-10-02 09:58:38 (warnings.log mtime)",
      "endpoint": "http://127.0.0.1:64294/mcp",
      "pid": 32536,
      "outcome": "readiness failed -> DR-70",
      "evidence": "runs/smoke-t14/warnings.log"
    },
    {
      "when": "2026-10-02 10:06:05",
      "endpoint": "http://127.0.0.1:63860/mcp",
      "pid": 7740,
      "outcome": "success after 1 poll, 22 nodes",
      "evidence": "runs/smoke-t14/iter-1/candidate/.hoh/deterministic/raw/play_scene_ready.json"
    }
  ],
  "editor_error_investigation": {
    "pass_1_count": 6,
    "pass_1_included": [
      "res://scripts/main.gd:8 - Parse Error: Expected new line after \"\\\".",
      "Failed to load script \"res://scripts/main.gd\" with error \"Parse error\"",
      "Cannot create file 'res://.godot/editor/filesystem_cache10'. Check user write permissions."
    ],
    "pass_2_count": 1,
    "pass_2_only": "Cannot create file 'res://.godot/editor/filesystem_cache10'. Check user write permissions.",
    "live_after_round_count": 1,
    "live_after_round_value": "[MCP] capture=off (default; use --mcp-capture=on_error|every_call together with --mcp-trace=<path>)",
    "acl_identical_to_fresh_t13": true,
    "godot_editor_dir_present": {
      "mario": true,
      "fresh-t11": true,
      "fresh-t12": true,
      "fresh-t13": true,
      "fresh-t14": false
    },
    "purge_source": "src/runtime/start_state.rs:100 purge_contents / :126 fresh_workspace removes every entry of the workspace, including .godot/editor/**",
    "cause": "undetermined; the round did not instrument the editor's cache flush"
  },
  "mechanisms": {
    "zero_increment": {
      "occurred": false,
      "evidence": "warnings.log (1700 B, 6 newline-terminated lines) carries none of Zero-increment/no_progress/no_engineering_write"
    },
    "repair_retry_used": true,
    "wrap_up_retry_used": false,
    "wrap_up_retry_reason": "not_triggered",
    "repair_note": "launch_gate_repair: the pre-freeze launchable gate failed",
    "artifact_gate": {
      "applicable": true,
      "launchable": false,
      "reasons": [
        "editor_errors_baseline: editor reported 1 error(s):\n{\"available\":true,\"count\":1,\"editor\":true,\"errors\":[\"  ERROR: Cannot create file 'res://.godot/editor/filesystem_cache10'. Check user write permissions.\"],\"in_process\":true,\"log_path\":\"user://logs/godot.log\",\"note\":\"\",\"pid\":36808,\"port\":9877,\"process\":\"editor\",\"source\":\"editor_log\"} (UNAVAILABLE: the editor is not clean; 1 line(s) still reproducible)"
      ]
    },
    "battery_passes": [
      {
        "pass": 1,
        "launchable": false,
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
            false
          ],
          [
            "play_scene_ready",
            false
          ],
          [
            "scene_tree",
            false
          ],
          [
            "screenshot",
            false
          ],
          [
            "interaction_evidence",
            false
          ],
          [
            "input_channel_probe",
            false
          ],
          [
            "input_replay",
            false
          ],
          [
            "node_and_collision_assertions",
            false
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
      },
      {
        "pass": 2,
        "launchable": false,
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
            false
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
            false
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
    "truncation_64kib": {
      "triggered": true,
      "count": 1,
      "where": "tester.attempt1.json message 29",
      "limit_bytes": 65536,
      "original_bytes": 79928
    },
    "editor_errors_baseline_count_pass2": 1,
    "secret_redactions": 7,
    "out_of_tree_writes": [
      "l.json",
      "p2.json",
      "pv.json",
      "r.json"
    ],
    "out_of_tree_cleanup_lines_in_warnings_log": 0,
    "out_of_tree_files_still_present": true,
    "usage_ratios": {
      "planner": 1.0,
      "developer": 1.0,
      "tester": 1.0
    },
    "usage_double_count_distinguishing_case_present": false,
    "usage_note": "all three roles' summary equals the sum of their attempts (ratio 1.000), but the planner has no redaction sidecar this round, so the shape that produced the 2x in t12/t13 is absent; this is a negative result, not a confirmation of the DR-79 filter",
    "dsH_term_cmd_redaction": {
      "expected": "DSH_TERM_CMD=<redacted>",
      "observed": "DSH_TERM_CMD=<raw harness command line>",
      "occurrences_raw_in_redacted_copy": {
        "developer.attempt1.redacted.json": 4,
        "developer.attempt2.redacted.json": 2
      },
      "occurrences_marker_in_redacted_copy": 0,
      "hoh_game_route_also_unredacted": true,
      "other_harness_names_redacted_in_the_same_dump": [
        "HOH_ROLE",
        "HOH_RUN_DIR",
        "HOH_RUN_ID",
        "HOH_SCRATCH_DIR",
        "HOH_TOOLS_ENDPOINT",
        "HOH_VIEW_DIR",
        "PATH",
        "HOH_MODEL_API_KEY"
      ],
      "api_key_value_hits": 0,
      "cause": "undetermined; the redactor was not instrumented"
    }
  },
  "count_scopes": {
    "verified_records": {
      "value": 11,
      "scope": "iter-1/evidence.json verified_records length"
    },
    "gap_records": {
      "value": 10,
      "scope": "iter-1/evidence.json gap_records length"
    },
    "execution_records_on_verified": {
      "value": 24,
      "scope": "execution_records inside verified_records"
    },
    "execution_records_on_gap": {
      "value": 17,
      "scope": "execution_records inside gap_records"
    },
    "execution_records_total": {
      "value": 41,
      "scope": "all execution_records in evidence.json"
    },
    "round_dir_files": {
      "value": 300,
      "scope": "runs/smoke-t14 after evidence/ was copied in"
    },
    "evidence_files": {
      "value": 121,
      "scope": "runs/smoke-t14/evidence/**"
    },
    "read_only_baseline_dirs": {
      "value": 11,
      "scope": "runs/smoke-t6..t13 and .workspace/{mario,fresh-t11,fresh-t12}"
    },
    "tokens_total": {
      "value": 16346289,
      "scope": "sum of the three role entries in result.json.usage, equal to the console 'total tokens'"
    }
  },
  "baselines": {
    "caliber": "Get-ChildItem -Recurse -Force -File; repo-root-relative lowercase POSIX path + TAB + bytes + TAB + sha256; LF-joined, no trailing newline; culture order; SHA-256 of those UTF-8 bytes",
    "caliber_is_anchored": "reproduces the task book anchor runs/smoke-t6 = 135 / c144ef32...7a9c03 / 2026-09-29 02:32:01 and every one of the ten T13-published rows (10/10)",
    "three_measurements_identical": [
      "before the round (09:41)",
      "after the round (10:21)",
      "after the evidence bundle"
    ],
    "table_text_digest": "6a36ffce9bedecfc733a60c01a63297f6503ea37cf05023e162e76826d33e844",
    "time_window": {
      "start_epoch": 1790905513.791,
      "files_outside_smoke_t14_newer": 0,
      "files_in_three_workspaces_newer": 0
    },
    "engine_binary_sha256": "08483088a4a2772841cd3b4c916b2d45b3cb6255656cf3951598a86fce7e9e6a",
    "prd_mario_sha256": "4c81c3a9995f0b3afdf01421a0c3be88573cceefc284ce9bafbfda141f0f5c3a",
    "evidence": "runs/smoke-t14/evidence/analysis/baseline_check.txt"
  },
  "final_revision_gap": {
    "question": "does this round close the gap that the current revision had only been verified offline?",
    "answer": "partially: the revision that carries DR-79/DR-80 was rebuilt and a full round really ran on it, five of six criteria are met and three previously-dangling behaviours were exercised - but the round also produced two reds that only a real machine could expose, so 'all green on real hardware' is NOT established",
    "for": [
      "HEAD 44131d9 has ec90c19 (DR-79) and 3e727b9 (DR-80) as ancestors and changes src/runtime/{hygiene,run_loop,secrets,usage}.rs",
      "the pre-existing binary (310075fa...) predated those changes, so it was rebuilt (3b97e4a0...) and the three new markers were found in its bytes",
      "the same command sequence ran once from a provably empty directory (36m07s, exactly one round)",
      "E1/E3/E4/E5/E6 met; the role-started-scene republish branch was walked for the first time",
      "the eleven read-only baselines are byte-identical under three calibers and the engine binary is unchanged"
    ],
    "against": [
      "hoh run exited 6 for the first time; artifact_gate.launchable=false; E2 is not met",
      "the round-book's DSH_TERM_CMD redaction did not take effect on real hardware (the harness command line survives in the frozen trajectories and their redacted copies)",
      "editor_get_errors is a log-tail reading and is not stable, yet the gate treats it as a hard verdict"
    ]
  },
  "unverified": [
    "why fresh-t14 has no .godot/editor directory while four other projects do: the editor's cache flush was not instrumented",
    "the exact lifetime of the game processes that failed readiness (:64145, :64294): they were not probed between the play reply and the failed polls",
    "why the code path that should redact DSH_TERM_CMD assignments left them intact while redacting other HARNESS_ENV_VARS names in the same dump",
    "whether the usage_from_attempts filter fix works: this round had no planner redaction sidecar, so the distinguishing case did not occur",
    "the semantics of out_of_tree_writes beyond the four paths it lists",
    "redaction sidecar fidelity beyond what was replaced: the originals are byte-unchanged and both forms parse, but the spans were not audited"
  ],
  "risks": [
    "The launch gate cannot tell an editor cache-write failure from a project defect, so a clean project can be frozen with launchable=false and exit 6 - exactly what happened here",
    "--fresh-workspace deletes .godot/editor while the editor is already pointed at the project, because the book's mandatory order starts the editor before the run; whether the editor recreates the directory is not deterministic across rounds",
    "The harness command line still reaches frozen trajectories through DSH_TERM_CMD; today it carries paths only, but the same vector would carry a credential if one ever appeared on the harness command line",
    "Four untracked *.json files keep the repository dirty and are outside every baseline",
    "The 64 KiB output cap fired again on a real 79,928-byte payload, so any analysis that trusts a role's in-context view silently loses the tail"
  ],
  "honest_disclosure": [
    "The release binary was rebuilt after touching src/main.rs so that the build transcript would contain a real 'Compiling' line; only the mtime changed.",
    "The pre-launch hoh doctor reported godot.engine_version as FAIL because the probe's cwd is the project directory, which did not exist yet; a direct --version and a doctor run against .workspace/mario both return 4.8.dev.mono.custom_build.035edfce7, so the judge criterion is met.",
    "The first probe of the role-started-scene branch failed with -32602 because scene_path is not a parameter of editor_play_scene; both transcripts are kept and the retry used the engine's own parameter list.",
    "The evidence bundle was copied into runs/smoke-t14/evidence after the round closed, so runs/smoke-t14's own digest necessarily changed; the eleven read-only baselines are the ones with the three-way proof.",
    "caliber C was first attempted with this shell's `bash`, which resolves to WSL bash and reported a WSL2 mount error; it was rewritten to walk the tree in Python and the reason is recorded in the artifact.",
    "Four untracked *.json files in the repository root were left in place rather than deleted, because they are this round's evidence of the tester's out-of-tree writes.",
    "No push was attempted; origin/master is untouched. The commit of this round carries the report only."
  ]
}
```

## 附：证据索引（`runs/smoke-t14/evidence/**`；每行给字节数与 sha256 前 16 位，按路径排序）

| 文件 | 字节 | sha256(16) |
|---|---|---|
| `runs/smoke-t14/evidence/COPY_MANIFEST.txt` | 4097 | `ef5b6eb2233ff27d` |
| `runs/smoke-t14/evidence/analysis/baseline_check.txt` | 6083 | `331e2aaaa429f090` |
| `runs/smoke-t14/evidence/analysis/battery_reads.txt` | 34948 | `bcb7fc2ca0cc3c3f` |
| `runs/smoke-t14/evidence/analysis/cite_check.txt` | 395 | `4d597e5c8cd2461e` |
| `runs/smoke-t14/evidence/analysis/dsh_context.txt` | 3060 | `72b386b0e511f33a` |
| `runs/smoke-t14/evidence/analysis/e3_extract.txt` | 18463 | `449ea4b3893b35ed` |
| `runs/smoke-t14/evidence/analysis/editor_errors_probe.txt` | 2380 | `263e3a1455dd5b9f` |
| `runs/smoke-t14/evidence/analysis/env_leak_probe.txt` | 6335 | `4cca0fd26465d4d4` |
| `runs/smoke-t14/evidence/analysis/final_counts.txt` | 2068 | `433903f6a6e3eff0` |
| `runs/smoke-t14/evidence/analysis/godot_editor_dir_check.txt` | 2499 | `0a7f5dbdcbaa6d62` |
| `runs/smoke-t14/evidence/analysis/json_block_check.txt` | 396 | `d3438a2d2e12c94f` |
| `runs/smoke-t14/evidence/analysis/machine_block.json` | 26693 | `78b2d6c950a72062` |
| `runs/smoke-t14/evidence/analysis/mechanisms.txt` | 3535 | `3261fa1db626e2e4` |
| `runs/smoke-t14/evidence/analysis/project_inventory.txt` | 5077 | `e7f09ad9a9dcd48a` |
| `runs/smoke-t14/evidence/analysis/redaction_check.txt` | 3614 | `0ab63922d6344862` |
| `runs/smoke-t14/evidence/analysis/redaction_pairs.txt` | 2465 | `5e632e93405230d9` |
| `runs/smoke-t14/evidence/analysis/role_game_calls.txt` | 12727 | `271216db5a7ccfc6` |
| `runs/smoke-t14/evidence/analysis/round_facts.txt` | 12463 | `486ef79177678d03` |
| `runs/smoke-t14/evidence/analysis/sizes.txt` | 908 | `66e4bd603f9db1d7` |
| `runs/smoke-t14/evidence/analysis/tool_census_editor_role.txt` | 1546 | `b15c4ffc4dcb2824` |
| `runs/smoke-t14/evidence/analysis/tool_census_game_role.txt` | 3746 | `ad9cbc94d4361aa1` |
| `runs/smoke-t14/evidence/analysis/traj_audit.txt` | 2421 | `aa7ddd5821df29c4` |
| `runs/smoke-t14/evidence/analysis/utf8_scan.txt` | 326 | `439e0d86fb7c9281` |
| `runs/smoke-t14/evidence/gatecheck/after_gate_kill_port.txt` | 512 | `302c6f9f5b29f76b` |
| `runs/smoke-t14/evidence/gatecheck/game_role_editor_status.json` | 386 | `094e9340fa96682e` |
| `runs/smoke-t14/evidence/gatecheck/game_role_tools_list.json` | 31444 | `57dcfd4965e52ba3` |
| `runs/smoke-t14/evidence/gatecheck/gate_game_role_console.txt` | 750 | `5345399d259fb9c7` |
| `runs/smoke-t14/evidence/gatecheck/gate_game_role_launch_meta.txt` | 854 | `3a25d341e1bc08ef` |
| `runs/smoke-t14/evidence/gatecheck/wait_ready_gate.txt` | 976 | `fcead0bfc0483464` |
| `runs/smoke-t14/evidence/probe/play_args.json` | 16 | `890b74bf18ed705b` |
| `runs/smoke-t14/evidence/probe/post_probe_processes.txt` | 987 | `ac9b80f9dc81de09` |
| `runs/smoke-t14/evidence/probe/pre_probe_state.txt` | 2768 | `d14ce2a7a1b291bb` |
| `runs/smoke-t14/evidence/probe/role_play_probe.txt` | 1408 | `c1f69440da4a05e6` |
| `runs/smoke-t14/evidence/probe/role_play_probe2.txt` | 2284 | `10153d49e0716ecc` |
| `runs/smoke-t14/evidence/probe/role_play_probe3.txt` | 2686 | `76235f0aa651139c` |
| `runs/smoke-t14/evidence/probe/stop_args.json` | 2 | `44136fa355b3678a` |
| `runs/smoke-t14/evidence/probe/stop_scene.txt` | 559 | `80997486ba80a266` |
| `runs/smoke-t14/evidence/probe/stop_scene2.txt` | 559 | `c70eec31bafa8427` |
| `runs/smoke-t14/evidence/raw/live_snapshot_early.txt` | 1570 | `6f9612865f61a767` |
| `runs/smoke-t14/evidence/raw/live_snapshot_mid.txt` | 2319 | `22a49dde2ecdb4c6` |
| `runs/smoke-t14/evidence/raw/live_timeline_mid.txt` | 781 | `7b560ed94e879dff` |
| `runs/smoke-t14/evidence/raw/live_timeline_mid2.txt` | 3125 | `3a66ab45fd810e2a` |
| `runs/smoke-t14/evidence/raw/pass1_live/SNAPSHOT_MANIFEST.txt` | 939 | `e62b4270a26cdf40` |
| `runs/smoke-t14/evidence/raw/pass1_live/mcp-errors.jsonl` | 13353 | `fdd5b2734c23318e` |
| `runs/smoke-t14/evidence/raw/pass1_live/mcp-sync.json` | 103 | `da705b09d14fc9b1` |
| `runs/smoke-t14/evidence/raw/pass1_live/raw/editor_errors_baseline.json` | 1396 | `fafd44c6fe9260f7` |
| `runs/smoke-t14/evidence/raw/pass1_live/raw/editor_stop_scene.json` | 521 | `e304efb1ad038b2a` |
| `runs/smoke-t14/evidence/raw/pass1_live/raw/input_channel_probe.json` | 7157 | `3d58a6c03084023f` |
| `runs/smoke-t14/evidence/raw/pass1_live/raw/input_replay.json` | 15244 | `c940eeb5a71db6b2` |
| `runs/smoke-t14/evidence/raw/pass1_live/raw/interaction_evidence.json` | 4844 | `99ee7056ed01652c` |
| `runs/smoke-t14/evidence/raw/pass1_live/raw/node_and_collision_assertions.json` | 4320 | `147339726c7e5823` |
| `runs/smoke-t14/evidence/raw/pass1_live/raw/play_scene_ready.json` | 1503 | `03e49180da1c7e3e` |
| `runs/smoke-t14/evidence/raw/pass1_live/raw/project_reload_and_open.json` | 939 | `80cdc23d93f5b79b` |
| `runs/smoke-t14/evidence/raw/pass1_live/raw/scene_structure.json` | 5218 | `e653ed29100f424a` |
| `runs/smoke-t14/evidence/raw/pass1_live/raw/scene_tree.json` | 769 | `de28a419f72af670` |
| `runs/smoke-t14/evidence/raw/pass1_live/raw/screenshot.json` | 1374 | `81cfe372a9f414ee` |
| `runs/smoke-t14/evidence/round/baseline_after_evidence.txt` | 1152 | `6a36ffce9bedecfc` |
| `runs/smoke-t14/evidence/round/baseline_after_repo.txt` | 1152 | `6a36ffce9bedecfc` |
| `runs/smoke-t14/evidence/round/baseline_before_repo.txt` | 1152 | `6a36ffce9bedecfc` |
| `runs/smoke-t14/evidence/round/binary_markers.txt` | 800 | `872959c08193a8c8` |
| `runs/smoke-t14/evidence/round/build_release.txt` | 537 | `f3b031d0c462f9c0` |
| `runs/smoke-t14/evidence/round/doctor_diag_existing_project.txt` | 2001 | `5d07c8c9d1e3aff4` |
| `runs/smoke-t14/evidence/round/editor_console.txt` | 2915 | `c4a2d6562e4d1603` |
| `runs/smoke-t14/evidence/round/editor_launch_meta.txt` | 869 | `c1c530c6a6302921` |
| `runs/smoke-t14/evidence/round/editor_listener.txt` | 972 | `23c46c80c19fa80c` |
| `runs/smoke-t14/evidence/round/editor_tools_list.json` | 56761 | `72b6f89534871980` |
| `runs/smoke-t14/evidence/round/empty_proof.txt` | 714 | `492734b4a02ac29d` |
| `runs/smoke-t14/evidence/round/engine_version_probe.txt` | 466 | `0d2953abe9399bda` |
| `runs/smoke-t14/evidence/round/init.txt` | 512 | `901740096c5daed7` |
| `runs/smoke-t14/evidence/round/init_tree.txt` | 413 | `9f287742db7d7e85` |
| `runs/smoke-t14/evidence/round/live_editor_get_errors.json` | 673 | `4c8c7910c43d7767` |
| `runs/smoke-t14/evidence/round/preflight_doctor.txt` | 2132 | `5ac0f6b76d5203e6` |
| `runs/smoke-t14/evidence/round/preflight_doctor_retry.txt` | 2103 | `f08ffdcac0af44c5` |
| `runs/smoke-t14/evidence/round/preflight_port.txt` | 371 | `67968171dd986ce0` |
| `runs/smoke-t14/evidence/round/report_body.md` | 63959 | `48e35ed396593209` |
| `runs/smoke-t14/evidence/round/round_console.txt` | 2206 | `6a293bb784f39037` |
| `runs/smoke-t14/evidence/round/round_window.json` | 440 | `6e1e8135524c6cb3` |
| `runs/smoke-t14/evidence/round/scope_project_list_scripts.json` | 385 | `7d03be933bf1b7d1` |
| `runs/smoke-t14/evidence/round/scope_project_tree.json` | 9806 | `63607a300d215853` |
| `runs/smoke-t14/evidence/round/wait_ready_editor.txt` | 969 | `1931ff543ed2e018` |
| `runs/smoke-t14/evidence/scripts/assemble_report.py` | 2464 | `e92fca10397feac7` |
| `runs/smoke-t14/evidence/scripts/baseline_check.py` | 5444 | `821abb55b0fc9807` |
| `runs/smoke-t14/evidence/scripts/baseline_digest.ps1` | 1958 | `6c0cd49c327f8f1b` |
| `runs/smoke-t14/evidence/scripts/battery.py` | 4979 | `68473fae1daf3e7b` |
| `runs/smoke-t14/evidence/scripts/binary_markers.py` | 1780 | `d9ec7402c4b83a5d` |
| `runs/smoke-t14/evidence/scripts/build_json_block.py` | 28556 | `4d593e607c464ec8` |
| `runs/smoke-t14/evidence/scripts/capture.py` | 4120 | `7b63baec5abe5172` |
| `runs/smoke-t14/evidence/scripts/cite_check.py` | 5756 | `3473e3cfd356cbb9` |
| `runs/smoke-t14/evidence/scripts/copy_evidence.py` | 1434 | `ab4e337f5218bea7` |
| `runs/smoke-t14/evidence/scripts/dsh_context.py` | 1139 | `14950f6b3e88306f` |
| `runs/smoke-t14/evidence/scripts/dump_struct.py` | 1037 | `219e5743b610eccb` |
| `runs/smoke-t14/evidence/scripts/e3_extract.py` | 5735 | `8e7e78577dbdef58` |
| `runs/smoke-t14/evidence/scripts/editor_errors_probe.py` | 2583 | `b64fa34654ca25ff` |
| `runs/smoke-t14/evidence/scripts/empty_proof.py` | 2097 | `998eaf51990b1c74` |
| `runs/smoke-t14/evidence/scripts/env_leak_probe.py` | 1802 | `3aec5d14be69104f` |
| `runs/smoke-t14/evidence/scripts/final_counts.py` | 2419 | `e6bcc426e1f048f4` |
| `runs/smoke-t14/evidence/scripts/godot_editor_dir_check.py` | 1436 | `62cbfd0be9c4a0a0` |
| `runs/smoke-t14/evidence/scripts/inner.py` | 1003 | `28ee61f30025f783` |
| `runs/smoke-t14/evidence/scripts/json_block_check.py` | 2592 | `377efa381591742c` |
| `runs/smoke-t14/evidence/scripts/launch_engine.py` | 3138 | `9b7f52eaa2b09565` |
| `runs/smoke-t14/evidence/scripts/live_snapshot.py` | 2142 | `59666614738764f5` |
| `runs/smoke-t14/evidence/scripts/live_timeline.py` | 2793 | `89ce59a4ca0f2f64` |
| `runs/smoke-t14/evidence/scripts/mcp_call.py` | 3197 | `f180de050fec7dde` |
| `runs/smoke-t14/evidence/scripts/mechanisms.py` | 4077 | `dec8df7b6e46acbe` |
| `runs/smoke-t14/evidence/scripts/port_preflight.py` | 1607 | `751233f6fb5e84c9` |
| `runs/smoke-t14/evidence/scripts/probe_role_play.py` | 6548 | `e2132eca0852082e` |
| `runs/smoke-t14/evidence/scripts/project_inventory.py` | 820 | `3397e43ed0af81b7` |
| `runs/smoke-t14/evidence/scripts/redaction_check.py` | 2345 | `dacbd578e27f3cc0` |
| `runs/smoke-t14/evidence/scripts/redaction_pairs.py` | 1565 | `c817bc576af9f55e` |
| `runs/smoke-t14/evidence/scripts/role_game_calls.py` | 3234 | `71cf51474c3f4493` |
| `runs/smoke-t14/evidence/scripts/round_facts.py` | 7253 | `1f9124af7bbeb121` |
| `runs/smoke-t14/evidence/scripts/round_window.py` | 855 | `45f0cab72dedfa3d` |
| `runs/smoke-t14/evidence/scripts/run_stream.py` | 3030 | `d6865f5cc056d21e` |
| `runs/smoke-t14/evidence/scripts/secret_env.py` | 987 | `1953985ede9e4912` |
| `runs/smoke-t14/evidence/scripts/sizes.py` | 1557 | `d606c079c956449b` |
| `runs/smoke-t14/evidence/scripts/snapshot_det.py` | 1176 | `9d55e51a352829cd` |
| `runs/smoke-t14/evidence/scripts/tool_census.py` | 4039 | `b116f79e8c699e58` |
| `runs/smoke-t14/evidence/scripts/traj_audit.py` | 5294 | `1eb3129c9a959930` |
| `runs/smoke-t14/evidence/scripts/tree_hash.py` | 4060 | `448cbab3f97478c2` |
| `runs/smoke-t14/evidence/scripts/utf8_scan.py` | 2466 | `5c980e11df6c947d` |
| `runs/smoke-t14/evidence/scripts/wait_ready.py` | 1457 | `1323f636d133abfa` |
