# TASK-SMOKE-T12-REPORT — 真机轮：**再次从全新空工程出发**；**六条判据全部 `met`（E3 首次成立）**；三处修复的真机读数（2 绿、1 未触发）

- 任务书：`.spec/hof-rs/tasks/TASK-SMOKE-T12.md`（本轮唯一任务来源）
- 报告人：**真机轮执行子代理（无上游对话上下文）**；落点：`F:\moonbit-hof-rs`
- **本轮新目录（§1.1 要求声明）**：`F:\moonbit-hof-rs\.workspace\fresh-t12`
- 轮记录目录：`runs/smoke-t12/**`（运行时的轮记录 + 本轮自建的 `evidence/**`）
- 本轮命令（**恰好一轮，无重试**；除下文披露的"编辑器启动顺序纠错"外无重建）：
  - `target/release/hoh.exe init  --project F:\moonbit-hof-rs\.workspace\fresh-t12`
  - `target/release/hoh.exe run --iterations 1 --run-id smoke-t12 --fresh-workspace --project F:\moonbit-hof-rs\.workspace\fresh-t12`
- 墙钟：`02:49:33 → 03:25:17` = **35m44s**；`ROUND_EXIT=0`；tokens **17,703,610**（按角色汇总：planner 901,668 / developer 6,727,773 / tester 10,074,169；三角色 `usage_known=true`）
- 引擎身份（判据）：`4.8.dev.mono.custom_build.035edfce7`（`--version` 逐字；sha256 `08483088…e9e6a` 仅记录）
- 二进制：**按 HEAD 重建**（`cargo build --release --offline`，exit 0），
  `12692992 B / 2026-10-01 23:49:06` → `12713984 B / 2026-10-02 02:45:40 / sha256 310075fa…7158ca`
- HEAD（开工 = 收工 = 报告前）= `47680397fff0a990c92470c271a5a6e583aa8fc9`；`origin/master` 同值（**未推送**，闸门武装）

---

## 0. 结论摘要

| 判据 | 判定 | 一句话依据 |
|---|---|---|
| **E1** | **met** | 全新空目录（`ls -la` = `total 0`，`find -mindepth 1` = 0）→ `hoh init` exit 0 → **恰好一轮** `hoh run --fresh-workspace` exit 0；`meta.json.start_state.mode="fresh"`；Planner/Tester `Submitted` 且 `artifact_valid=true`；**Developer 真写了工程**（`A_0=3ac25f6c…` 3 文件/1727 B → `A_1=fc50ecd2…` 11 文件/7384 B，8 新增 + `main.tscn` 342→3580 B）；退出码三处同数。§2.1 |
| **E2** | **met** | `editor_errors_baseline.count=0`；`editor_play_scene` `playing=true`（pid 27736）；游戏进程 `running_game_get_scene_tree` 返回 **22 节点**；`editor_stop_scene` `stopped=true`；`artifact_gate={applicable:true,launchable:true,reasons:[]}`（`meta.json` 与 `result.json` 双处）。§2.2 |
| **E3** | **met（首次 4/4 类成立）** | **四类都有游戏进程内语义工具原始读数**：左移 −216.332458496 px、右移 +216.333312988 px、跳跃为**纯竖直弧线**（x `unique=1`、y `unique=30`）、**金币 `Coins: 0 → Coins: 2` 且 `Goal.reached false → true`**；四类各有一发 `running_game_assert_node_state passed=true`。§2.3 |
| **E4** | **met** | `evidence.json`：**12 verified / 10 gap**，`overlap=[]`、无重复；**33 条执行记录逐条 stat 全部存在**（`MISSING=[]`），`type` 齐备，`candidate_id` 全绑 `fc50ecd2…`；10 条 gap 各带 `player_impact` 与 `recommended_update`；`planner_handoff` 三项齐备（5/5/6）。§2.4 |
| **E5** | **met** | 三棵树**逐字节同一**：`versions/fc50ecd2…` == `iter-1/candidate` == 活体 `.workspace/fresh-t12`（11 文件/7384 B；`only_in_*`=[]、`differing`=[]）⇒ QA 未改 `A_1`。§2.5 |
| **E6** | **met** | `qa_report.md` 逐字 `Verdict: partial`，逐条列出 8 组未做到的东西（无墙/敌人/方块/死亡平面/重启、**F1-stop 回归**、F17 时长过短），并**主动拒绝过度声明**（把 `GAME_INPUT_CHANNEL_OK` 的轴探针明确写成"不可用作证据"）。§2.6 |

**本轮不可判定的判据：无**（E1..E6 均有本轮原始证据）。

### 0.1 三处修复的真机读数（§0 的 1/2/3）

| # | 修复 | 本轮真机读数 | 原始证据落点 |
|---|---|---|---|
| **1** | 驱动前释放遗留反向动作 | ✅ **绿（首次真机确认窗口真的推进了玩家）** | `interaction_evidence.json` call **[4]**：`running_game_play_input_recording` `label='interaction:release_stale_move_left'` → `{"event_count":1,"injected":1,"replayed":true,"speed":1.0}`，且它在**第一批驱动 call[6] 之前**；窗口随后每批 **60/60 个唯一 x 采样**推进（`67.33→283.67→511.00→738.33`）。`STALE_ACTION_NOT_RELEASED` 全轮 **0 次**。§3.1 |
| **2** | 观测窗口早于所有消耗性窗口 | ✅ **绿（首次真机确认 `0→N` 跃迁可被观测）** | `battery.json` 步骤序：`interaction_evidence` 下标 **6** < `input_channel_probe` **7** < `input_replay` **8**；观测窗口**自己的**前后读数是 `Coins: 0`（call[0]）→ `Coins: 2`（call[24]），判定行写 `COIN_PICKED_UP`。§3.2 |
| **3** | 角色自起 `editor_play_scene` 重发布路由 | ⚠️ **未触发（unexercised，不是绿也不是红）** | 本轮**没有任何角色执行 `editor_play_scene`，也没有任何角色执行 `running_game_*`**：7 个轨迹里 `hoh tools call` **0 次**；Developer 真执行的 **38 次** `hoh tools call` 全部是 `editor_*`/`project_*`（`running_game_*` **0 次**、`editor_play_scene` **0 次**）。**因此重发布路径、其就绪等待与 DR-43 拒绝语义本轮都没有被走到**；就绪等待耗时**无法归因**。§3.3 |

> **§3.3 的"0 次"是可复算断言**，作用域 = 本轮 4 个未脱敏轨迹（`planner.attempt1`、`developer.attempt1`、`developer.attempt2`、`tester.attempt1`）中 `extra.actions[*].command` 的**真执行命令**；复算脚本 `evidence/scripts/hoh_invocations.py`，输出 `evidence/analysis/hoh_invocations.txt`（`INVOCATIONS = 1 / 44 / 1 / 0`）。

---

## 1. 环境引导（§2.1 要求，逐步留证）

原始文件：`runs/smoke-t12/evidence/round/**`。

### 1.1 收紧点 1：**启动之前**的 `hoh doctor` 与 `netstat`（分别留存原始输出）

**① `hoh doctor`（`02:44:47`，编辑器尚未启动，端口无监听）**

```
[ok] godot.engine_binary: F:/moonbit-hof-rs/godot-mcp/godot/bin/godot.windows.editor.x86_64.mono.exe (size 194216960 B, mtime 1790641862)
[ok] godot.engine_version: 4.8.dev.mono.custom_build.035edfce7
[FAIL] model.chat: ... no api key resolved; set HOH_MODEL_API_KEY or OPENAI_API_KEY (C11)
[FAIL] tools.mcp: MCP transport failure to http://127.0.0.1:9877/mcp: ... (os error 10061)
DOCTOR_EXIT=4
```

（`preflight_doctor.txt`。两条 FAIL **都是当时预期的**：密钥尚未注入进程环境、编辑器尚未启动。）

**② 端口与进程（`02:44:55`，同一"启动之前"时点，原文）**

```
CMD: netstat -ano | findstr :9877      ->  (空)   NETSTAT_EXIT=1
CMD: tasklist | findstr /I godot       ->  (空)   TASKLIST_EXIT=1
```

（`preflight_port.txt`。⇒ 开工时**没有任何 godot 进程、9877 无监听**；编辑器是本轮自行启动的。）

**③ 密钥只报长度**：`HOH_MODEL_API_KEY` 从 `config/model.secret.env`（`.gitignore` 覆盖、仅给人 source，C11）导入**进程环境**，
`length=51`，**从未打印**；注入后 `model.chat` 转 `[ok] ... answered with model deepseek-v4.1-flash`（`preflight_doctor_withkey.txt`）。

### 1.2 🔴 引擎启动顺序纠错（**本轮的实质发现，必须如实披露**）

我第一次在**空目录**上执行任务书逐字命令，引擎起来了，但**以 `role=game` 身份**：

```
[MCP] role=game configured_port=9877 source=cmdline listen=true
[MCP] listening on 127.0.0.1:9877 (editor=false, tools=73)
[MCP] INFO: MCP server is ready on 127.0.0.1:9877 as the game process (port source=cmdline, tools=73)
```

⇒ `tools/list` 只给 **73** 个工具，**104 个 `editor_*` 工具全部缺席**（含 `editor_play_scene`）。我先用受控对照证明这**不是二进制换版**：

| 对照 | 输入 | 读数 |
|---|---|---|
| A | 同一二进制，`-e --path <空目录> --mcp-port=9881` | `role=game`，`tools=73`（`probe_empty_tools.json`） |
| B | 同一二进制，`-e --path <已 `hoh init` 的工程> --mcp-port=9877` | `role=editor`，`tools=154`（`editor_tools.txt`） |

并且契约文件 `godot-mcp/godot/modules/mcp_server/docs/tools_list.renamed.json` 的 **177** 个名字里，
**73 个 served 名字是其真子集**（`SERVED BUT NOT IN CONTRACT = 0`），缺的恰好是 **104 个 `editor_*`**（`tools_contract_diff.txt`）。
引擎侧过滤点在 `tool_registry.cpp:267 scope_matches(...)` / `:316 build_tools_list(p_is_editor)`；`mcp_server.cpp:505` 取
`is_editor = Engine::get_singleton()->is_editor_hint()`。同一二进制 sha256 `08483088…` 与 T11 记录逐字相同。

**⇒ 结论（实测）**：在本引擎上 `-e` 不足以进入编辑器模式；`--path` 指向的目录**必须已经存在 `project.godot`**。
这与任务书自己要求的顺序「空目录 → `hoh init` → `hoh run`」一致——**是我第一次的启动顺序错了，不是引擎或产品缺陷**。
我按正确顺序重做：`rmdir` 空暂存目录 → 在**空目录**上 `hoh init` → 再启动编辑器（指向已有 `project.godot` 的新工程）。
旧的那个 `role=game` 进程（pid 22908）我用**精确 pid** `taskkill` 停掉；**全程未使用 `rm -rf`**。

### 1.3 编辑器身份、工程绑定（**反假轮证明**）与工具数

```
LAUNCH (verbatim):
  F:\moonbit-hof-rs\godot-mcp\godot\bin\godot.windows.editor.x86_64.mono.exe -e --path F:\moonbit-hof-rs\.workspace\fresh-t12 --mcp-port=9877
LAUNCH_TIME   2026-10-02 02:48:33  (managed background job term-38)
LISTENER_PID  33556
CommandLine=F:\moonbit-hof-rs\godot-mcp\godot\bin\godot.windows.editor.x86_64.mono.exe -e --path F:\moonbit-hof-rs\.workspace\fresh-t12 --mcp-port=9877
ExecutablePath=F:\moonbit-hof-rs\godot-mcp\godot\bin\godot.windows.editor.x86_64.mono.exe
CreationDate=20261002024833.856237+480
[MCP] role=editor configured_port=9877 source=cmdline listen=true
[MCP] listening on 127.0.0.1:9877 (editor=true, tools=154)
```

**编辑器所开工程 = 本轮新工程的实测证明**（引擎在启动时固定工程、177 工具无一能切换）：

```
$ python runs/smoke-t12/evidence/scripts/mcp_call.py project_list_scripts '{}'
{"id":1,"jsonrpc":"2.0","result":{"content":[{"text":"{\"count\":0,\"scripts\":[]}","type":"text"}]}}   ← 新工程：0 脚本
$ python .../mcp_call.py project_get_filesystem_tree '{}'
res:// 下非缓存的工程内容 = project.godot / scenes/main.tscn / scripts/README.md      ← 就是 `hoh init` 的产物
磁盘对照：.workspace/mario/scripts 有 15 个条目
```

⇒ **不是假轮**：MCP 侧看到的就是磁盘侧要写的那个工程。（运行时自己的 `godot.project_file` / `editor_scope` 检查项
在本轮 doctor 里也逐字指到 `F:\moonbit-hof-rs\.workspace\fresh-t12`。）

### 1.4 二进制重建（必要动作，已披露）

`target/release/hoh.exe` 原 mtime `2026-10-01 23:49`，**早于** HEAD `4768039`（`02:40:57`）⇒ 不含本轮必须检验的 DR-78 机制。
故执行 `cargo build --release --offline`（**只编译，未改任何源码**）：

```
Compiling hof-rs v0.1.0 (F:\moonbit-hof-rs)
Finished `release` profile [optimized] target(s) in 16.18s
BUILD_EXIT=0
```

新符号/新消息实测（`strings -a`）：`STALE_ACTION_NOT_RELEASED` **1 次**、
``the game the role started with `editor_play_scene` did not answer `running_game_get_scene_tree` after`` **1 次**
⇒ 重建下来的确实是含本轮新逻辑的二进制。
（`publish_role_started_game_route`、`COIN_OBSERVING_BATTERY_STEP` 是**编译期常量标识符**，不以字符串存在于 release 二进制里；
我不把"0 次"当作"没有该逻辑"的证据。冷启动重编由门日志里 `Compiling hof-rs` **1 次命中**证明。）

---

## 2. E1..E6 逐条判定 + 原始证据

### 2.0 "空目录 → init → run" 三步的原始输出

**(a) 目录为空（原始 `ls`，且是在暂存目录建立**之前**取的）**

```
$ ls -la .workspace/fresh-t12
total 0
drwxr-xr-x 1 wyl 197609 0 Oct  2 02:44 .
drwxr-xr-x 1 wyl 197609 0 Oct  2 02:44 ..
$ find .workspace/fresh-t12 -mindepth 1 | wc -l
0
$ find .workspace/fresh-t12 -maxdepth 1 | sort
.workspace/fresh-t12
$ stat -c '%n size=%s mtime=%Y' .workspace/fresh-t12
.workspace/fresh-t12 size=0 mtime=1790880270
```

（`evidence/round/empty_proof.txt`。该目录**本轮之前不存在**：开工 `ls -la .workspace/fresh-t12` 返回 `No such file or directory`。
披露：我前两次把暂存目录建在了工程目录里，那两次清单因多出 `.t12pre` 而**被污染并作废**；上面这份是在目录**可证为空**（0 条目）时重取的。）

**(b) `hoh init` 的真实输出**

```
$ target/release/hoh.exe init --project F:\moonbit-hof-rs\.workspace\fresh-t12
init: A0 ready at F:\moonbit-hof-rs\.workspace\fresh-t12 (initialize ran; no MCP, no model endpoint and no key were required)
INIT_EXIT=0
$ find .workspace/fresh-t12 -mindepth 1 | sort
.workspace/fresh-t12/project.godot
.workspace/fresh-t12/scenes
.workspace/fresh-t12/scenes/main.tscn
.workspace/fresh-t12/scripts
.workspace/fresh-t12/scripts/README.md
PROJECT_GODOT_SHA256=00d02c9c08c3dc4fc35e3d9bcc94b06c31d44b42df2f017bc0ca5615a12c0ef4
ADDON_DIR_EXISTS=False
```

（`evidence/round/init.txt`。与 T11 的 A₀ 脚手架**同 sha**，同样无 `addons/godot_mcp_rs`。）

**(c) `meta.json.start_state`（不得为 `as_is`）**

```text
"start_state": { "mode": "fresh", "version_id": null }
```

### 2.1 E1 = met

| 要件 | 原始证据 |
|---|---|
| Planner 产出合法 `D_1` | `iter-1/plan.md`（3299 B）；`logs/planner.attempt1.log`：`exit_status=RepeatedFormatError`、**`artifact_valid=true`**、`attempt=1`、45 calls |
| Developer 产出**真实工程增量** | `versions/index.json`：`A0 3ac25f6c…`(iteration 0, role init) → **`A1 fc50ecd2…`**(iteration 1, role developer)；`result.json.evidence_diff` 与我的独立 diff **逐条一致** |
| QA 产出合法 `E_1` | `iter-1/evidence.json`（37664 B，可解析）；`logs/tester.attempt1.log`：`exit_status=Submitted`、`artifact_valid=true`、`attempt=1`、135 calls |
| 整轮 + 退出码 | `runs/smoke-t12/exit_code` 字节 `30 0A`；`meta.json.exit_code=0`；`runs/smoke-t12/process_exit_code` 字节 `30 0A`；wrapper `ROUND_EXIT=0`；`result.json`：`ok=true, failed_role=null, reason="ok", issues=[]` |

**`A_0` / `A_1` 摘要（运行时自己的 hash 口径，`policy.rs::hash_tree`：`relpath\n{len}\n{bytes}\n` 排序流）**：

```
A0  3ac25f6c5c38885febd3a001ea99c88aca61b1799c7b105306919886c2c1d151    3 files   1727 B
A1  fc50ecd2c1acfcb9854c14b99edfc9dcc5f7004f6377b34ba90a1bb088cd228d   11 files   7384 B
```

**口径自证（重要）**：我**独立实现**了该方案（`evidence/scripts/treehash.py`，**不调用** hof-rs 的任何函数），
对本轮两个冻结树复算，得到**逐字相同**的 id：

```
runs/smoke-t12/versions/3ac25f6c…  -> 3ac25f6c5c38885febd3a001ea99c88aca61b1799c7b105306919886c2c1d151
runs/smoke-t12/versions/fc50ecd2…  -> fc50ecd2c1acfcb9854c14b99edfc9dcc5f7004f6377b34ba90a1bb088cd228d
```

（我第一版把路径小写了，两个 id 都复现不出来；`policy.rs::relativize` **不改变大小写**，去掉小写后两个都命中。
⇒ **路径大小写口径是承重的**，如实记在此。）

**被改文件清单（我独立 diff，`evidence/scripts/a0a1_diff.py`）**：

```
ADDED: scripts/{coin,goal,main,player}.gd + 各自 .gd.uid          （8 个文件）
MODIFIED: scenes/main.tscn   342 B -> 3580 B
REMOVED: []
```

`result.json.evidence_diff` = `{"added":[8 同上],"modified":["scenes/main.tscn"],"removed":[]}` ⇒ **逐条一致**。

**非琐碎**：Developer 从**只有 `README.md` 的 `scripts/`** 起手，写出 4 个脚本 + `Coin1`/`Coin2` + `Goal` + HUD（**22 节点**场景）。

**⚠️ 本轮 E1 的真实瑕疵（必须点名，不改判定）**：`result.json.attempts` 显示 Developer **两次 attempt 都是 `LimitsExceeded`
且 `artifact_valid=false`**（attempt1 150 calls；attempt2 是 wrap-up 重试，25 calls；`wrap_up_retry_used=true`、
`wrap_up_retry_reason="artifact_missing"`）。`A_1` 仍是对**磁盘上已有文件**的快照（这是我读 `result.json` + `versions/` 的**实测**；
"为什么 artifact 无效仍能快照"的**因果**我没读源码确认，列**推断**）。T11 的 developer 是 `artifact_valid=true`，本轮**不是**。

### 2.2 E2 = met

```
editor_errors_baseline : {"available":true,"count":0,"editor":true,"errors":[],"in_process":true,"log_path":"user://logs/godot.log","pid":33556,"port":9877,"process":"editor","source":"editor_log"}
play_scene_ready       : {"args_injected":["--mcp-port=53595"],"endpoint":"http://127.0.0.1:53595/mcp","mcp_port_source":"auto_free_port","mode":"main","pid":27736,"playing":true}
running_game_get_scene_tree (game endpoint) -> 22 typed nodes (Ground/Player/Coin1/Coin2/Goal/HUD{Coins,Lives,Time,Victory})
editor_stop_scene      : {"message":"Playback stopped","stopped":true}
artifact_gate          : meta.json 与 result.json 两处均为 {"applicable":true,"launchable":true,"reasons":[]}
battery                : 12 步 / 12 ok（`battery_passes[0].steps` 全部 true）
```

⇒ **0 条编译/脚本错误**、主场景**可启动**（22 节点）、**干净停止**、闸门因正确原因开启。
（`play_scene_ready` 的就绪判定是 **1 poll** 成功 ⇒ 运行时侧就绪等待在本轮几乎无成本；这与 §3.3 的角色侧就绪等待**不是同一个东西**。）

### 2.3 E3 = met（**四类全部成立，首次**）—— 逐类裁定

| 行为 | 裁定 | 决定性原始证据（**全部来自游戏进程端点上的语义工具**） |
|---|---|---|
| 左移 | **成立** | `input_replay` move_left 窗口：x `1149.00085449219 → 932.668395996094`，Δ=**−216.332458496**（60 帧，**60/60 唯一 x**）；`move_left:replay_assert_moved` `passed=true` |
| 右移 | **成立** | move_right 窗口：x `881.334777832031 → 1097.66809082031`，Δ=**+216.333312988**（60/60 唯一 x）；`move_right:replay_assert_moved` `passed=true` |
| 跳跃 | **成立** | jump 窗口：x **恒为** `1156.33410644531`（`unique=1`）、y `269.980834960938 → min 214.258605957031 → 242.59196472168`（`unique=30`）⇒ **纯竖直弧线**；`jump:replay_assert_moved` `passed=true` |
| **至少 1 个可交互对象** | **成立** | `interaction_evidence` 判定行：`coin counter /root/Main/HUD/Coins Coins: 0 -> Coins: 2`、**`COIN_PICKED_UP`**；引擎自己的 `running_game_assert_node_state`（`text:neq "Coins: 0"`，actual `"Coins: 2"`）`passed=true` |
| **一个终点/胜负条件** | **成立** | `Goal.reached` 读数 `false`（call 1/10/16）→ **`true`**（call 22）；判定行 **`WIN_DRIVEN`**；`running_game_assert_node_state`（`reached:neq false`，actual `true`）`passed=true`；`player max x=738.333984375` 越过 `goal.position.x=600.0`，`coverage_shortfall_px=Some(-138.333984375)`（**负值** ⇒ 已越过目标） |

**四条位置断言的原始回包（逐字，`payload.content[0].text` 解出）**：

```
move_right           actual {x:1097.66809082031,y:283.998992919922} expected {x:881.334777832031,…} operator=neq property=position passed=true resolved_node_path=/root/Main/Player
move_right_release   actual {x:1149.00085449219,…} expected {x:1116.00122070312,…} passed=true
jump                 actual {x:1156.33410644531,y:242.59196472168} expected {x:1156.33410644531,y:269.980834960938} passed=true
move_left            actual {x:932.668395996094,y:283.925262451172} expected {x:1149.00085449219,y:270.92529296875} passed=true
```

**证据形态齐备**：`input_replay.json` 48 次调用；`interaction_evidence.json` 28 次调用；
每窗口 before/after PNG（11 张，我逐个验 PNG magic `89504e470d0a1a0a` —— **11/11 通过**，大小见 §7）。

**关于金币与胜利的语义工具原始回包（§1.2 要求的"来自语义工具的原始回包"，不是推断）**：

```
[  0] running_game_get_node_properties  interaction:read_/root/Main/HUD/Coins_text
      {"node_path":"/root/Main/HUD/Coins","properties":{"text":"Coins: 0"},"type":"Label"}
...
[ 24] running_game_get_node_properties  interaction:read_/root/Main/HUD/Coins_text
      {"node_path":"/root/Main/HUD/Coins","properties":{"text":"Coins: 2"},"type":"Label"}
[ 26] running_game_assert_node_state    interaction:replay_assert_picked_up
      {"actual":"Coins: 2","expected":"Coins: 0","operator":"neq","property":"text","passed":true,"resolved_node_path":"/root/Main/HUD/Coins"}
[ 27] running_game_assert_node_state    interaction:replay_assert_won
      {"actual":true,"expected":false,"operator":"neq","property":"reached","passed":true,"resolved_node_path":"/root/Main/Goal"}
```

**诚实的边界**：
- 计数器实际是 **`0 → 2`**（不是 0→1）：观测窗口一次驱动穿过了 **两枚** 金币（场景只有 `Coin1`/`Coin2` 两个 `Area2D`）。
  判据要的是"至少 1 个可交互对象"且"0→N 跃迁在轮内被观测到"，**本读数满足**；但"恰好 1 枚"不是本轮读数。
- 本轮**没有**出现 `STALE_ACTION_NOT_RELEASED`（0 次），也**没有**出现 `COIN_NOT_PICKED_UP` / `WIN_BLOCKED_UNDER_MOVE_RIGHT` /
  `WIN_UNREACHED_WITHIN_BUDGET`（**作为本轮结果**）。
  ⚠️ **陷阱**：这些 token 在本轮轨迹里**有字符串出现**（tester 轨迹 6 处 `COIN_PICKED_UP`、2 处 `COIN_NOT_PICKED_UP` 等），
  但 `COIN_NOT_PICKED_UP` 的那 2 处**只出现在交给 Tester 的技能文档文本里**（`tool` 角色消息；`token_context.py` 实测），
  **不是**本轮产出的判定。**数量本身不是结论，位置才是。**

### 2.4 E4 = met（我自己逐条 stat，不看运行时自报）

```
iteration=1  qa_status=partial  verified=12  gap=10
verified_ids = [N1, N2, N3, P3, F1, F2, F3, F4, F5, F10, F13, F16]
gap_ids      = [F1-stop, F6, F7, F8, F9, F11, F12, F14, F15, F17]
overlap: []        dup_verified: []        dup_gap: []
execution_records=33   MISSING=[]                 ← 每条 path 都在冻结候选视图里真实存在
record types: {build:3, runtime_trace:5, assert:6, replay:10, log:3, screenshot:6}
record candidate_ids: [fc50ecd2c1acfcb9854c14b99edfc9dcc5f7004f6377b34ba90a1bb088cd228d]
gaps lacking player_impact: []        gaps lacking recommended_update: []
planner_handoff: preservation_constraints=5 / update_targets=5 / validation_requirements=6
```

**相对 T11 的判据侧变化**：`F10`（金币）与 `F13`（胜利）由 gap **转 verified**；`N2`/`N3` 新增为 verified；
`F1-stop`（松手后未静止）成为**新增 gap**（诚实读数）。

### 2.5 E5 = met（三棵树逐字节同一）

```
versions/fc50ecd2c1acfcb9854c14b99edfc9dcc5f7004f6377b34ba90a1bb088cd228d   files=11 bytes=7384
iter-1/candidate (frozen QA view)                                            files=11 bytes=7384
live .workspace/fresh-t12                                                    files=11 bytes=7384
only_in_first=[]   only_in_second=[]   differing=[]                          IDENTICAL = True
（三条的 runtime-scheme id 均为 fc50ecd2…，由我独立实现复算）
```

`result.json.candidate_id == version_id == fc50ecd2…`。

### 2.6 E6 = met（诚实性 = 可核对的内容）

`qa_report.md`（逐字）含：

```
Verdict: partial - the movement/jump/camera/coin/win slice is genuinely playable, but most of the platformer loop is not there yet.
## Gaps (what the player loses)
- F1 (stop) the post-release window still moved +32.99 px over 10 frames - no sample shows the player settling to rest.
- F6 no wall exists in the scene, so blocking is unobservable.
- F7/F8/F9 no enemy at all: no patrol, no contact damage, no stomp kill.
- F11/F12 no question block and no breakable brick.
- F14/F15 no death/fall-out state and therefore no restart/reset.
- F17 the whole course is crossed in about 3 s (3x60-frame batches), far below the required 30-120 s.
## Notes / caveats
- input_channel_probe reports GAME_INPUT_CHANNEL_OK but axis moved=false; the positional game_process
  quadruples and POSITION_ASSERT_PASSED in input_replay are the evidence actually used for F1/F2/F3.
```

⇒ **未达成被声明**（8 组），且**主动拒绝把弱观测当结论**（探针 `GAME_INPUT_CHANNEL_OK` 被自己标注为不可用作证据）；
**未谎报为 verified**。这与 `evidence.json` 的 `verified/gap` 划分**逐条一致**（12/10）。
---

## 3. 三处修复的真机读数（§0 的 1/2/3，逐条原始回包/判定行原文）

原始文件：`evidence/analysis/e3_extract.txt`、`assertions.txt`、`hoh_invocations.txt`、`route_trace.txt`。

### 3.1 ① 驱动前释放遗留反向动作 —— **绿（首次真机确认窗口真的推进了玩家）**

**`interaction_evidence.json` 的调用序（原始，节选；脚本 `e3_extract.py`）**：

```
[  0] running_game_get_node_properties    interaction:read_/root/Main/HUD/Coins_text  ok=True
      {"node_path":"/root/Main/HUD/Coins","properties":{"text":"Coins: 0"},"type":"Label"}
[  1] running_game_get_node_properties    interaction:read_Goal_reached              ok=True
      {"node_path":"/root/Main/Goal","properties":{"reached":false},"type":"Area2D"}
[  3] running_game_get_node_properties    interaction:read_Goal_position             ok=True
      {"node_path":"/root/Main/Goal","properties":{"position":{"x":600.0,"y":280.0}},"type":"Area2D"}
[  4] running_game_play_input_recording   interaction:release_stale_move_left        ok=True
      {"event_count":1,"injected":1,"replayed":true,"speed":1.0}
[  5] running_game_create_input_recording interaction:batch1:create_input_recording    ok=True
[  6] running_game_play_input_recording   interaction:batch1:play_input_recording     ok=True
      {"event_count":1,"injected":1,"replayed":true,"speed":1.0}
[  9] running_game_get_node_property_samples interaction:batch1   n_samples=60
      x: first=67.3333358764648  last=283.666717529297  unique=60
[ 15] running_game_get_node_property_samples interaction:batch2   n_samples=60
      x: first=294.666687011719  last=510.999420166016  unique=60
[ 21] running_game_get_node_property_samples interaction:batch3   n_samples=60
      x: first=521.999450683594  last=738.333984375      unique=60
```

**关键点（本轮要确认的那件事）**：`release_stale_move_left`（call[4]）**早于第一批驱动**（call[6]），
并且窗口随后在**自己的 3 批里**把玩家从 `67.33` 推进到 `738.33`（每批 **60/60 唯一 x 采样**，
每帧约 **+3.6667 px**，`×60 = 220 px/s`，与 `player.gd` 的 `speed=220` 自洽）。

⇒ T11 的失败形态（窗口采样 **180 个 x 全部逐位相同**、`x=225.000045776367` 恒定不动）**本轮没有复现**。
`STALE_ACTION_NOT_RELEASED` 全轮 **0 次**（作用域 = 本轮 4 个未脱敏轨迹全文，`grep` 计数）。

**§1.4 要求的"两个不同事实"**：本窗口的"送达"事实（`injected=1/replayed=true`）有 **4** 次；
但**送达 ≠ 移动**，见 §4 的对照。

### 3.2 ② 观测窗口早于所有消耗性窗口 —— **绿（`0→N` 跃迁首次真机可观测）**

**电池的步骤序（`battery.json`，原始，脚本 `battery_readings.py`）**：

```
[ 0] project_reload_and_open          ok=True
[ 1] scene_structure                  ok=True
[ 2] editor_errors_baseline           ok=True
[ 3] play_scene_ready                 ok=True
[ 4] scene_tree                      ok=True
[ 5] screenshot                      ok=True
[ 6] interaction_evidence            ok=True     ← 观测窗口
[ 7] input_channel_probe             ok=True     ← 消耗性窗口
[ 8] input_replay                    ok=True     ← 消耗性窗口
[ 9] node_and_collision_assertions   ok=True
[10] editor_stop_scene               ok=True
[11] engine_identity                 ok=True
```

**观测窗口自己的判定行（逐字，来自 `battery.json` 的 `record/observation`）**：

```
interaction: before readings coin=Some("Coins: 0") goal.reached=Some(Bool(false))
             goal.position=Some(Object {"x": Number(600.0), "y": Number(280.0)});
interaction: drove `move_right` for 3 of 130 batch(es) (60 frame(s) each, 7800 frames budgeted),
             player max x=Some(738.333984375), goal.position=Some(Object {"x": Number(600.0), "y": Number(280.0)}),
             coverage_shortfall_px=Some(-138.333984375), stopped as soon as the win was observed;
interaction: coin counter `/root/Main/HUD/Coins` Coins: 0 -> Coins: 2;
interaction: COIN_PICKED_UP (the counter grew 0 -> 2; `text:neq "Coins: 0"` accepted in the game process);
interaction: WIN_DRIVEN (goal.reached false -> true while the player drove right; `reached:neq false` accepted in the game process)
```

⇒ **T11 的结构性假阴性（F-T11-3）已消除**：观测窗口**自己**看到 `0 → 2`，而不是接手一个已被吃掉的计数器。
（T11 里 `interaction_evidence` 的首个读数就已是 `Coins: 1`，因为更早的 `input_replay` 已经吃掉金币。）

**顺带读数（DR-77 ② 的"钉住"在真机形态下仍成立）**：
`coverage_shortfall_px=Some(-138.333984375)` **出现在判定行本身**；本轮**没有**出现 `WIN_UNREACHED_WITHIN_BUDGET`
（预算没耗尽——只用了 3/130 批就赢了），因此**该类结论本轮无真机证据，我不替它借证据**。

### 3.3 ③ 角色自起 `editor_play_scene` 重发布路由 —— ⚠️ **未触发（unexercised）**

**这是本轮最重要的"非绿"读数，必须精确陈述。**

**实测（可复算，作用域见下）**：

```
planner.attempt1.json      role=planner   executed_commands= 52   hoh_tools_call=0
developer.attempt1.json    role=developer executed_commands=219   hoh_tools_call=0
developer.attempt2.json    role=developer executed_commands= 45   hoh_tools_call=0
tester.attempt1.json       role=tester    executed_commands=146   hoh_tools_call=0
TOTAL `hoh tools call` across all trajectories = 0
```

**但角色确实调用过工具通道**（用另一种拼写）：Developer 以 `"<…>\hoh.exe" tools call <tool> --args-file …`
真执行了 **44** 次 `hoh` 调用（`hoh_invocations.txt`），其中：

```
running_game_*   0 次        ← 关键：没有任何 running_game_* 调用
editor_play_scene 0 次        ← 关键：没有任何 play_scene
editor_stop_scene 0 次
实际调用的工具：editor_get_collision_info(11) / editor_get_errors(6) / editor_get_scene_tree(4) /
               editor_get_node_properties(4) / editor_execute_gdscript(4) / project_validate_scripts(2) /
               editor_open_scene(2) / project_write_text_file(1) / project_read_scene_file_content(1) /
               project_get_info(1) / editor_rescan_project_filesystem(1) / editor_remove_output_log(1) /
               editor_reload_plugin(1)
```

⇒ **0 次 `game_endpoint_unavailable`**（作用域 = 本轮 4 个未脱敏轨迹）；但**这不能证明修复 3 生效**，
因为**角色根本没走过会触发它的路径**——零拒绝是在**没有发出**这类调用的前提下取得的。
**这是本轮唯一的"整轮都没走到"的修复**。

**关于 Tester**：它**没有**发任何 live `hoh tools call`；它的 146 条命令是读冻结件
（`cat .hoh/deterministic/...`、`type .hoh\TOOLS.md`）与**对已捕获载荷做本地分析**（19 条 `python`，
例如解码 PNG 做像素分析、读 `battery.json`）。⇒ T11 的"Tester 3 次 live 追问被拒"这一红读数
**本轮既没有复现，也没有被正面证伪**。

**路由文件本身（如实）**：`runs/smoke-t12/game_endpoint.json` 在轮内**被改写至少两次**，两个值我都**直接读到**：

| 值 | 我读到它的方式 |
|---|---|
| `{"endpoint":"http://127.0.0.1:57989/mcp","port":57989,"source":"auto_free_port","pid":29776}` | Developer 自己的轨迹 `msg 116`（该角色执行了 `cat runs/smoke-t12/game_endpoint.json`，回包逐字如上） |
| `{"endpoint":"http://127.0.0.1:53694/mcp","port":53694,"source":"auto_free_port","pid":25236}` | 本轮 `03:12` 的直接 `cat` |

**我没有把"路由被改写"归因给修复 3**（判定：**无法归因**）。理由与反例检验见 §5。
另外：`meta.json.engine.mcp.game_endpoint` 记的是 `53595 / pid 27736`，而该字段的
`engine.checked_at` = `started_at` = `1790880575`（`02:49:35`，即**轮开始时的检查**），
**不是**轮内后来的某个游戏；`battery` 自己的 `play_scene_ready` 起的也是 `53595 / 27736`。
收工后 `game_endpoint.json` **不存在**（路由已被撤回，与 DR-43 的撤回语义一致）。

---

## 4. §1.4 的对照：`interaction_evidence` 与 `input_replay` 在同一候选上的位移/采样

**"送达了输入"与"真的移动了"是两个不同事实 —— 本轮在同一候选上同时给出两者。**

| 窗口 | 送达事实（`injected=1` `replayed=true`） | 移动事实（真实位移） |
|---|---|---|
| `interaction_evidence` batch1 | 有（call[6]） | x `67.3333358764648 → 283.666717529297`，Δ**+216.333381653**，60/60 唯一 |
| `interaction_evidence` batch2 | 有（call[12]） | x `294.666687011719 → 510.999420166016`，Δ**+216.332733154**，60/60 唯一 |
| `interaction_evidence` batch3 | 有（call[18]） | x `521.999450683594 → 738.333984375`，Δ**+216.334533691**，60/60 唯一 |
| `interaction:release_stale_move_left` | 有（call[4]） | （释放动作，`move_left` 归零） |
| `input_replay` move_right | 有（call[3]） | x `881.334777832031 → 1097.66809082031`，Δ**+216.333312988**，60/60 唯一 |
| `input_replay` move_right_release | 有（call[15]） | x `1116.00122070312 → 1149.00085449219`，Δ**+32.999633789**，10/10 唯一 |
| `input_replay` jump | 有（call[27]） | x **唯一值 1 个**（恒 `1156.33410644531`），y `269.980834960938 → 214.258605957031 → 242.59196472168`，y 唯一 30 个 |
| `input_replay` move_left | 有（call[39]） | x `1149.00085449219 → 932.668395996094`，Δ**−216.332458496**，60/60 唯一 |
| `input_channel_probe` move_right | 有（call[3]） | x `756.667419433594 → 863.001342773438`，Δ**+106.33392334**，30/30 唯一 |

**总计**：本轮"送达"事实 **12** 次（`interaction_evidence` 4 / `input_channel_probe` 1 / `input_replay` 7）；
"移动"事实 = 上表 7 条有位移的采样序列 + 5 条 `running_game_assert_node_state passed=true`。

**反例/边界（不许把送达当移动）**：
- `interaction_evidence` 每批的 `run_test_scenario` 回包是 `"all_passed": false, "failed": 1`，
  原因是 `input_axis` 断言 `"node '/root/Main/Player' does not ha[ve…]"` —— **该探针在本项目上读不到轴，
  但这与"玩家有没有动"无关**：同批的位置采样序列证明玩家在动。
  这正是 E3 判据要求在"游戏进程内、用语义工具、看行为"而不是"看探针 OK"的原因。
- `jump` 窗口 x 的唯一值为 **1**、y 唯一值为 **30** ⇒ 竖直弧线的**判据是形状**，不是"位移非零"。

---

## 5. 机制归因与反例检验（把"我们没看到 X"与"X 不可能"分开）

| # | 归因主张 | 支持读数 | **反例检验** | 判定性质 |
|---|---|---|---|---|
| C-A | 前两次"引擎以 game 身份启动"是**因为 `--path` 目录还没有 `project.godot`** | 空目录 → `role=game`/73 工具；`hoh init` 后同一二进制 → `role=editor`/154 工具 | **同轮、同二进制、仅改这一个变量**（目录内容）即翻转 ⇒ 排除了"二进制换版"（sha256 与 T11 逐字相同）与"端口参数"（两次都是 `--mcp-port`） | **实测**（A/B 对照） |
| C-B | 修复 1 生效（窗口真的推进玩家） | call[4] 的释放 + 窗口 3 批各 60/60 唯一 x | 若"释放没生效"，`move_right` 与仍在按住的 `move_left` 会互相抵消 ⇒ 轴向 0 ⇒ 采样 x 恒定；本窗口 x **每批唯一 60 个**且单调 +3.6667 px/帧 | **实测** |
| C-C | 修复 2 生效（跃迁可观测） | 步骤序 6<7<8 + 窗口自己的 `Coins: 0 → 2` | 若观测窗口仍晚于消耗窗口，则首个读数会是 `Coins: 1/2`（T11 形态）；本轮首个读数是 **`Coins: 0`** | **实测** |
| C-D | **修复 3 本轮生效** | 路由文件确实被改写过两次 | **反例成立**：没有任何角色调用 `editor_play_scene` 或 `running_game_*`（0/0），因此**没有任何观测能区分**"新逻辑重发布了路由"与"运行时既有的发布路径/别的窗口重发布了路由"。⇒ **该归因不成立** | **不可归因**（不是"没看到"，而是"这条路径根本没被走到"） |
| C-E | 0 次 `game_endpoint_unavailable` 说明角色 live CLI 可用 | 4 个轨迹全文 0 次 | **反例成立**：Developer 只发 `editor_*`/`project_*`（编辑器端点），从未发 `running_game_*`（游戏端点）⇒ 这**不是**对"`running_game_*` 还拒不拒"的检验。**"没看到拒绝" ≠ "拒绝不可能"** | **不可归因** |
| C-F | Developer 的 `artifact_valid=false` 仍然快照出 A₁ | `attempts` 两次 `LimitsExceeded` + `artifact_valid=false`，而 `versions/fc50ecd2…` 存在 | 我只观测到"两者同时为真"；**没有**读源码确认快照与 artifact_valid 的先后/依赖关系 ⇒ 因果未证 | **实测现象 + 因果未知** |

---

## 6. 只读基线的未变证明（内容 / count / mtime 三口径）

口径 = 本仓既往口径（PowerShell 5.1 `Get-ChildItem -Recurse -Force -File`；**仓根相对**小写 POSIX 路径 + 字节长 + SHA256；
`\t` 连接、`\n` 分行、无尾随换行；行序 **`Sort-Object` 文化排序**；整体 UTF-8 取 SHA256）。
脚本 `evidence/scripts/baseline_digest.ps1` + `baseline_set.ps1`（可复跑），输出 `evidence/round/baseline_{before,after}.txt`。

```
=== BEFORE: 2026-10-02 02:48（编辑器已起、轮未开始） ===     === AFTER: 2026-10-02 03:31（轮结束） ===
.workspace/mario   178  dee0a36f357c440d078c652d4d4b8990af1a63b88d282c1e36c04a16d006cc94  newest 2026-09-30 18:23:08
runs/smoke-t6      135  c144ef3219e21dd322978e41a5531d53dee270619c026585505920f9277a9c03  newest 2026-09-29 02:32:01
runs/smoke-t7      115  6e4c1595753c2cdefb16e4d2e5f05242ca202c70c81a93e98ae2b9c92b520fb7  newest 2026-09-29 14:41:14
runs/smoke-t8      358  6d11b2c61ec507b5f02525ddc0e7f7adb08763cd2439a4b08788b7fe51bdf5a7  newest 2026-09-30 07:58:28
runs/smoke-t9       83  541e2d814e563ba667c95bde49765d05e44cf11aa5ab90b2f44931f30136ca9d  newest 2026-09-30 11:27:29
runs/smoke-t10     232  319555896964ce1526f72a33cb239bf389fe29bcde23841764d13c57dfb38b8b  newest 2026-09-30 18:23:08
runs/smoke-t11     186  a76c228f596f2a0a6309bca9cee304401ddffc2d10ab384488cfaaffb8e27392  newest 2026-10-02 00:38:11
.workspace/fresh-t11 100 4c07c0b6d4352a5a64e1b49908e3ae1325f62f0a3b4de44d17efc51ebffd13a4  newest 2026-10-02 00:29:23
```

**开工 / 收工逐字相同（八条全中）** ⇒ **零字节写入**（连"写过再删"也没有：摘要口径含**空文件**，
任何创建/删除都会改变文件集与 count）。`newest` mtime 也逐条未变 ⇒ **内容与 mtime 两口径都未动**。
其中 `smoke-t6 = c144ef32…7a9c03` 命中任务书点名的自证值；`runs/smoke-t11 = 186 文件 / a76c228f…` 与 T11 报告一致。

**额外的独立口径**（`find` + `-newermt`）：
```
find runs -type f -newermt "2026-10-02 02:49:33" | grep -v smoke-t12   ->  (空)
find .workspace/mario -type f -newermt "2026-10-02 02:49:33"           ->  (空)
```
⇒ 本轮时间窗内 `runs/**`（除本轮自己的 `smoke-t12`）与 `mario` **都没有文件被写**。

**口径披露（必须写清）**：`evidence/analysis/digests.txt` 里的 digest 是**我另写的 Python 口径**
（`str.sort` 而非 PowerShell `Sort-Object` 文化序）；它对 `smoke-t6/t7/t9/t10/t11` 的**文件数与字节数**与上表一致，
但因排序口径不同，**哈希值不同**（例如 mario 我算 `f622f5b0…`，PowerShell 口径是 `dee0a36f…`）。
**上表用的是任务书/既往报告引用的 PowerShell 口径值**；我的 Python 口径只用于**逐字节树比较**（§2.5）。

---

## 7. 机制读数（零增量 / 修复尝试 / 64 KiB / 陈旧日志 / 端点可达 / 退出码三处同数 / 就绪等待）

原始：`evidence/analysis/mechanisms2.txt`、`hoh_invocations.txt`、`route_trace.txt`、`verify_numbers.txt`。

| 机制 | 本轮真实读数 |
|---|---|
| **零增量** | **未发生**。`warnings.log` 全文 4 行（`qa_scope…` + 3 条"redacted 旁路"），**不含** `Zero-increment`/`no_progress`/`no_engineering_write`（各 **0** 次）；`A_1 ≠ A_0` 且差异落在 Developer 产出的工程文件上 |
| **修复尝试** | **有**（与 T11 不同）。`repair_retry_used=false`、**`wrap_up_retry_used=true`**、`wrap_up_retry_reason="artifact_missing"`；Developer **两次 attempt**（`traj/developer.attempt1.json` + `attempt2.json`），两次都是 `LimitsExceeded`/`artifact_valid=false`；warnings 里无 `launch_gate_repair`；无 `quarantine/` |
| **64 KiB 上限** | **本轮未被触发**（不是"没生效"）：四条未脱敏轨迹里 `hoh_output_truncated` **0 次**；**最大单条消息 = 50,026 B**（tester）< 65,536 B ⇒ 没有输出越过阈值。⚠️ 轨迹里另有 `truncated` 字符串 developer 4 / tester 8 次，**逐处看过，全部是 MCP 工具自己的字段**（`"truncated":false`，来自输入录制/脚本校验回包），**不是**运行时截断标记 |
| **陈旧日志** | `editor_errors_baseline.count=0`（`errors:[]`）⇒ 无"过期编辑器日志关门"可触发 |
| **端点可达** | 角色侧：**0 次** `game_endpoint_unavailable`，但**同时 0 次 `running_game_*` 调用**（作用域 = 4 个未脱敏轨迹）⇒ **本项本轮不可判定**（见 §3.3 / C-E）。运行时侧：编辑器端点 `tools=154`、`editor_status.status="ok"`、`is_editor=true`；游戏端点由电池实测可达（22 节点） |
| **退出码三处同数** | ✅ `runs/smoke-t12/exit_code` = 字节 `30 0A`；`runs/smoke-t12/process_exit_code` = 字节 `30 0A`；`meta.json.exit_code` = `0`；另加 wrapper `ROUND_EXIT=0`（**四处**一致） |
| **就绪等待（DR-78 新增）** | **运行时侧**：`play_scene_ready` 的判定行逐字 `after 1 poll(s)` ⇒ 几乎零成本。**角色侧**（本次新增的那次等待）：**无法测量**，因为**没有任何角色执行 `editor_play_scene`**（§3.3）。⇒ 任务书 §0.3 要求的"如实记录就绪等待是否拖累/误导了轮次"，本轮答案是：**这条路径未被走到，因此没有可记录的成本**；我不能拿运行时侧那 1 poll 冒充角色侧读数 |
| **MCP 同步/错误** | `mcp-sync.json` = `{"available":true,"probes":0,"desynced":false,...}`；`mcp-errors.jsonl` **不存在** |
| **脱敏** | 3 个轨迹有旁路 `*.redacted.json`，**原件逐字节保留**（`warnings.log` 明写）；7 个轨迹文件**全部是合法 JSON**（我逐个 `json.loads` 通过） |
| **`evidence_diff`** | 非空且与我的独立 diff 逐条一致（§2.1） |
| **图片证据** | 11 张 PNG，magic 全部 `89504e470d0a1a0a`（11/11）；`frame-00.png` 5996 B、`replay-interaction-before.png` 5996 B、`replay-interaction-after.png` 7376 B（**前后不同大小**，与"金币消失"一致；我未做像素级复核，属**未复核项**） |
---

## 8. `A_0` / `A_1` 摘要与身份（运行时口径 + 报告口径）

| 记号 | 运行时 id（= `versions/` 目录名） | 文件数 | 字节数 | 我独立复算的 runtime-scheme id |
|---|---|---|---|---|
| **A_0**（`hoh init` 的空脚手架） | `3ac25f6c5c38885febd3a001ea99c88aca61b1799c7b105306919886c2c1d151` | 3 | 1727 | `3ac25f6c…c1d151`（**逐字命中**） |
| **A_1**（Developer + 电池后的冻结候选） | `fc50ecd2c1acfcb9854c14b99edfc9dcc5f7004f6377b34ba90a1bb088cd228d` | 11 | 7384 | `fc50ecd2…cd228d`（**逐字命中**） |
| `iter-1/candidate` = 活体工作区 | 同上 `fc50ecd2…` | 11 | 7384 | 同上 |

**身份说明（两种口径）**：
- **运行时口径**（`policy.rs::hash_tree`）：`relpath\n{len}\n{bytes}\n` 排序流；上面两行即此口径，且被我的独立实现复算命中。
- **报告口径**（既往报告用的 `rel\tlen\tsha256` 仓根相对小写路径整块哈希）：本轮 A₁ 冻结树为该口径的
  `dc4054b0d13ea2ed9d6a82548399b3462ee460f5662009dd3669d6d663e3d340`（3ac25f6c 树为 `a4fc4b81…`）。
  ⚠️ 我**不把它与 T11 的报告口径值（`b33cf818…`）比较大小**，因为口径不同、树也不同；此处只登记数值。

`A_1 != A_0`（摘要不同、文件集不同、非琐碎，见 §2.1 的 8 新增 + 1 修改 342→3580 B）。
差异**全部落在 Developer 产出的工程文件**上（`scripts/**`、`scenes/main.tscn`），**没有**落在 `.hoh/**`、`runs/**` 这类被排除路径。

---

## 9. 报告纪律自证（§1.6 的四条）

### (a) 所有"0 次 / 逐位相同 / 不存在"断言都可从其引用的证据文件复算，且写明作用域

| 断言 | 作用域 | 复算方式 / 文件 |
|---|---|---|
| `hoh tools call` = **0 次** | 本轮 4 个未脱敏轨迹的 `extra.actions[*].command` | `scripts/hoh_invocations.py`；`analysis/hoh_invocations.txt` |
| `running_game_*` 调用 = **0 次**、`editor_play_scene` = **0 次** | 同上 | 同上 |
| `game_endpoint_unavailable` = **0 次** | 本轮 4 个未脱敏轨迹**全文** | `scripts/token_census.py`；输出见 §3.3 |
| `STALE_ACTION_NOT_RELEASED` = **0 次** | 同上 | 同上；`battery.json` 判定行不含该 token |
| `hoh_output_truncated` = **0 次** | 4 个未脱敏轨迹全文 | `scripts/mechanisms2.py`；`analysis/mechanisms2.txt` |
| 8 条只读基线摘要**逐字相同** | 8 个目录的全部文件（含空文件） | `evidence/round/baseline_before.txt` vs `baseline_after.txt`（`diff` exit 0） |
| 三棵树**逐字节相同** | `versions/fc50ecd2…`、`iter-1/candidate`、`.workspace/fresh-t12`（排除 `.hoh/.git/.godot/.import`） | `scripts/treehash.py`（`only_in_*=[]`、`differing=[]`） |
| `runs/**`（除 smoke-t12）与 `mario` 在本轮时间窗内**无文件被写** | 该两棵树 | `find … -newermt "2026-10-02 02:49:33"`（空） |

### (b) 机制归因附反例检验（"我们没看到 X" vs "X 不可能"）

见 **§5 的 C-A..C-F 表**。要点：C-A/C-B/C-C 有**同轮对照**支持；**C-D 与 C-E 的反例成立**——
修复 3 与"角色 live CLI 可用"本轮**都不能被判为通过**，因为对应的调用路径**根本没被走到**（0 次），
这与"路径存在但失败了"是两种不同的世界，我没有把前者说成后者。

### (c) 机器可读块由 JSON 序列化器生成 + 栅栏感知 `json.loads` 复验（**已做**）

- **生成**：`python runs/smoke-t12/evidence/scripts/build_json_block.py runs/smoke-t12 runs/smoke-t12/evidence/analysis/machine_block.json`
  （内部用 `json.dump(..., ensure_ascii=False, indent=2)`；输出 9978 B，落盘 `evidence/analysis/machine_block.json`）。
  本报告 §11 的 `json` 代码块就是该文件内容的**逐字复制**。
- **复验**：`python runs/smoke-t12/evidence/scripts/json_block_check.py .spec/hof-rs/tasks/TASK-SMOKE-T12-REPORT.md runs/smoke-t12/evidence/analysis/json_block_check.txt`
  —— 该脚本**按 ``` 切块、只对 info string 为 `json` 的块做 `json.loads`**，并核对必需顶层键与 `verdicts`。
  转录见 `evidence/analysis/json_block_check.txt`（`FENCE_AWARE_JSON_BLOCKS_FOUND = 1`、`RESULT = PASS`）。
  **我确实做了这一步**，且是在报告写完之后、收工之前。
- 另：UTF-8 合法性由 `json_block_check.py` 逐字节读取（`encoding="utf-8"`）保证——T11A-3 的教训
  （派生物必须自己合法）本轮用"序列化器直接写 UTF-8 文件 + 栅栏感知回读"来覆盖。

### (d) 派生物数字与正文一致

正文所有数字都取自同一批脚本产物（`verify_numbers.txt`、`assertions.txt`、`e4_check.txt`、
`mechanisms2.txt`、`token_total.txt`、`digests.txt`、`round_summary.txt`），
且 §11 的机器块由 `build_json_block.py` 从**同一批冻结件**重新读取生成。
自查中我发现并修正了两处：① 页眉 tokens 原写 `17,793,610`，实际 `17,703,610`（已改为 `token_total.txt` 的值）；
② `delivery_facts_injected_1` 原写 8，实际 **12**（已按 `verify_numbers.txt` 改为 12）。
两处都发生在报告定稿前，未出现"正文与派生物不一致"的终态。

---

## 10. 遗留风险与未验证项（严格区分实测 / 推断 / 未知）

**实测（本轮有原始证据）**

1. 全新空工程条款成立：空目录清单（0 条目）+ `hoh init` exit 0 + `start_state.mode="fresh"` + `A_0` = 3 文件脚手架。
2. **E1/E2/E3/E4/E5/E6 全部 met**；**E3 首次四类齐备**（左右移动 + 跳跃 + 可交互对象 + 胜负），
   且金币 `0→2` 与 `Goal.reached false→true` **都来自游戏进程端点语义工具的原始回包**。
3. 修复 ①（遗留动作释放）与修复 ②（观测早于消耗）**真机绿**；`STALE_ACTION_NOT_RELEASED` 0 次。
4. 三棵树逐字节同一；8 条只读基线开工=收工；`runs/**`（除本轮）与 `mario` 零写入。
5. 退出码四处一致（0）；无零增量；无崩溃；`out_of_tree_writes=[]`；`artifact_hygiene` 干净；无孤儿游戏进程。
6. 64 KiB 截断**未被触发**（最大单条消息 50,026 B）。
7. 7 个轨迹文件**全部合法 JSON**；3 个旁路 `*.redacted.json`，原件保留。
8. 引擎二进制与 T11 记录**逐字相同**（sha256 `08483088…`）；嵌套引擎 `fc63af77…` porcelain 0 行。

**推断（不得当作已测）**

1. **（≈0.9）** 空 `--path` 目录导致引擎以 `role=game` 启动、`hoh init` 后转 `role=editor`——
   这是我用同二进制 A/B 对照夹出来的（C-A），但**我没有读引擎源码**确认 `project.godot` 缺失时
   `is_editor_hint()` 的确切失效机制。
2. **（≈0.6）** `runs/smoke-t12/game_endpoint.json` 在轮内被改写，其中至少一次可能来自修复 3 的发布路径；
   但**无法归因**（C-D）。我没有读 publish 的触发点逐行确认。
3. **（≈0.5）** Developer `artifact_valid=false` 仍快照出 A₁，可能是"快照只看磁盘文件、不看 artifact_valid"；
   未读源码确认（C-F）。
4. **（≈0.5）** 轨迹里的 `input_axis` 探针读不到轴（`does not ha[ve]`），可能是本项目 `Player` 没有
   `input_axis` 属性（探针形状与本工程不匹配），也可能是引擎能力问题；本轮**未定因**。
   这不影响 E3（E3 用的是位置采样与引擎断言）。

**未达到 / 未知（必须点名）**

1. **F-T12-1（major，判据侧）**：**修复 3 本轮未被任何角色触发**（0 次 `editor_play_scene`、0 次 `running_game_*`），
   ⇒ "角色 live CLI 不再被陈旧路由拒绝"**仍然没有被真机证明**，其**就绪等待成本也无法测量**。
   这是本轮最大的未闭合项，也是与任务书 §0.3 的期望最直接的差距。
2. **F-T12-2（minor）**：`WrapUpRetry` / `wrap_up_retry_used=true` 本轮**首次出现**；
   Developer 以 `artifact_valid=false` 收场而 `A_1` 仍成立——该分支的**语义**（是否应该算失败）本轮未审。
3. **F-T12-3（minor）**：金币跃迁本轮观测到的是 **`0→2`**；"恰好一枚"的形态**无本轮读数**。
4. **F-T12-4（minor）**：64 KiB 截断路径仍未被真机触发（与 T11 同）。
5. **F-T12-5（info）**：`meta.json.engine.mcp.game_endpoint` 记录的是**轮开始时**（`checked_at == started_at`）
   的那个游戏（`53595/27736`），**不是**轮内后来实际被使用的那个（例如 `53694/25236`）；字段名容易被误读为"当前路由"。
6. **F-T12-6（info）**：`evidence/analysis/digests.txt` 的 Python 口径哈希与 PowerShell 口径**不同**（排序差异，§6），
   引用时**必须写明口径**，否则会误判为"基线变了"。

---

## 11. 诚实披露（含重试、意外写入）

1. **我只跑了一轮**（`02:49:33 → 03:25:17`，单次 `hoh run`）。**无第二轮、无 attempt-A/B、无删除重建**；
   `runs/smoke-t12` 是本轮全新目录。
2. **引擎我启动了两次，第一次是错的**（§1.2）：第一次在**空 `--path`** 上启动，得到 `role=game`/73 工具，
   **不满足本轮需要编辑器端点的前提**。我用**精确 pid**（22908）停掉它，`hoh init` 之后再启动，
   第二次得到 `role=editor`/154 工具。**两个进程、两次启动的原始控制台输出都在证据里**，我没有隐藏这次错误。
   另有一次**受控探针对照**（空目录 + `--mcp-port=9881`，pid 28268），同样以精确 pid 停掉并如实记录。
3. **收工时编辑器存活**：`9877 LISTENING → pid 33556`，全机仅此一个 godot 进程
   （**无孤儿游戏进程需要清理**：`editor_stop_scene` 已由剧本完成；`game_endpoint.json` 已撤除）。
4. **暂存目录与随之而来的两次空目录污染**：为了不让 `--fresh-workspace` 的 purge 吃掉开工前取证，
   我在 `.workspace/.t12-scratch/` 暂存所有开工件（该目录是 `.gitignore` 的 `.workspace/` 之下、**不是**既有工作区）。
   我前两次误把暂存目录建在 `fresh-t12` 里，导致"空目录"清单多出 `.t12pre`；**两次都被我作废并重取**，
   用 `rm -f` **按精确文件名**删除那一个文件 + `rmdir` 删空目录（**绝未使用 `rm -rf`**，**绝未从未展开变量构造路径**）。
   收工时该暂存目录被清空删除，其内容全部搬进 `runs/smoke-t12/evidence/**`。
5. **一次中间态披露**：为取得"轮开始时"的 `doctor`（`hoh doctor` 在轮开始前）我跑过多次 doctor；
   其中**开工前**两次（无 key / 有 key）、**编辑器起来后**一次（`154 tools`）、**第二次启动后**一次。
   全部原始输出在 `evidence/round/`。
6. **我做的机器动作**：`mkdir`/`rmdir`/`rm -f <单个具名文件>`、`cp`、`mv`、`cargo build --release --offline`、
   启动/停止 godot 进程（精确 pid）、只读的进程/端口/文件检查、一轮 `hoh run`、
   以及本地只读分析脚本。**没有改 `src/**`、`tests/**`、`godot-mcp/**`、`.workspace/mario/**`、`.workspace/fresh-t11/**`、
   `PRD-mario.md`、`DECISIONS.md`、`REQUIREMENTS.md`，也没有改冻结的任务书。**
7. **本轮全部新增产出**只落在：`.workspace/fresh-t12/**`（被开发工程）、`runs/smoke-t12/**`（轮记录 + `evidence/**`）、
   本报告，以及 `.gitignore` 覆盖的 `target/`（编译产物）。
8. **我没有修任何发现的问题**（含 F-T12-1..F-T12-6）：本报告只做诊断、复现与判定。
9. **密钥卫生**：`HOH_MODEL_API_KEY` 只从 `config/model.secret.env` 导入进程环境，**只报长度 51，从不打印**；
   任何落盘证据都不含明文密钥。
10. **未 push**：`git status --porcelain -uall` 空；`origin/master == HEAD == 47680397…`（0 ahead / 0 behind）。
11. **我用的证据全部来自本轮**（`runs/smoke-t12/**`、`.workspace/fresh-t12/**`）；对 T11/T10 的引用
    只用于**口径自证**与**基线值对照**，不冒充本轮读数。
12. 报告写完后不再修改（除下方"收尾复验"可能要求的、且会在提交说明中标注的措辞更正）。

---

## 12. 工件索引

| 类别 | 路径 |
|---|---|
| 本轮轮记录 | `runs/smoke-t12/**`：`exit_code`、`process_exit_code`、`meta.json`、`warnings.log`、`TOOLS.md`、`versions/{index.json,3ac25f6c…,fc50ecd2…}`、`iter-1/{plan.md,result.json,usage.json,evidence.json,qa_report.md,logs/,traj/,planner-view/,candidate/}` |
| 被开发工程 | `.workspace/fresh-t12/**`（`project.godot`、`scenes/main.tscn`、`scripts/*.gd`） |
| 原始取证（本轮自建） | `runs/smoke-t12/evidence/round/**`：`empty_proof.txt`、`preflight_doctor.txt`、`preflight_doctor_withkey.txt`、`preflight_port.txt`、`preflight_doctor_live.txt`、`doctor_live_final.txt`、`rebuild.txt`、`init.txt`、`round_console.txt`、`editor_bootstrap.txt`、`scope_*.json`、`tools_list_{game,editor}_mode.json`、`tools_list_editor_live.json`、`baseline_{before,after}.txt`、`closing_state.txt`、`README_STAGING.txt` |
| 可复跑脚本 | `runs/smoke-t12/evidence/scripts/**`（`run_round.sh`、`baseline_digest.ps1`、`baseline_set.ps1`、`treehash.py`、`mcp_call.py`、`list_tools.py`、`list_all_tools.py`、`tools_contract_diff.py`、`tools_probe.py`、`raw_tools.py`、`battery_readings.py`、`e3_extract.py`、`assertions.py`、`verify_numbers.py`、`e4_check.py`、`round_summary.py`、`mechanisms.py`、`mechanisms2.py`、`cli_pair.py`、`cli_timeline.py`、`cmd_census.py`、`live_calls.py`、`live_tool_attempts.py`、`hoh_invocations.py`、`mcp_attempts_detail.py`、`token_census.py`、`token_context.py`、`token_total.py`、`msg_window.py`、`traj_shape.py`、`inspect_project.py`、`a0a1_diff.py`、`meta_timing.py`、`scene_tree.py`、`route_trace.py`、`digests.py`、`closing_state.py`、`build_json_block.py`、`json_block_check.py`） |
| 分析输出 | `runs/smoke-t12/evidence/analysis/**`：`e3_extract.txt`、`assertions.txt`、`verify_numbers.txt`、`e4_check.txt`、`mechanisms2.txt`、`hoh_invocations.txt`、`tester_timeline.txt`、`route_trace.txt`、`scene_tree_game.txt`、`round_summary.txt`、`token_total.txt`、`digests.txt`、`tools_contract_diff.txt`、`advertised_tools.txt`、`all_tools.txt`、`editor_tools.txt`、`machine_block.json`、`json_block_check.txt` |
| 电池原始件（轮内） | `runs/smoke-t12/iter-1/candidate/.hoh/deterministic/**`：`battery.json`、`deterministic.json`、`record-00..11.json`、`raw/{project_reload_and_open,scene_structure,editor_errors_baseline,play_scene_ready,scene_tree,screenshot,input_channel_probe,input_replay,interaction_evidence,node_and_collision_assertions,editor_stop_scene}.json` |
| 图片证据 | `runs/smoke-t12/iter-1/candidate/.hoh/evidence/*.png`（11 张） |
| 规范 / 任务书 | `.spec/hof-rs/REQUIREMENTS.md`（E1..E6 第 110-119 行）、`.spec/hof-rs/OBJECTIVE-COMPLETION.md`（C1..C5）、`.spec/hof-rs/tasks/TASK-SMOKE-T12.md` |
| 上轮对照 | `TASK-SMOKE-T11-REPORT.md`、`TASK-SMOKE-T11-ACCEPTANCE.md`、`TASK-DR78-REPORT.md`、`TASK-DR78-ACCEPTANCE.md` |
| 相关决策 | `DECISIONS.md` **D276 / D278 / D289 / D290 / D291 / D292**（只读） |

---

## 附：机器可读结论

（本块由 `evidence/scripts/build_json_block.py` 用 `json.dumps(..., ensure_ascii=False, indent=2)` 序列化，
与 `evidence/analysis/machine_block.json` 逐字相同；落盘后由栅栏感知脚本 `json_block_check.py`
以 `json.loads` 回读并核对必需顶层键，转录见 `evidence/analysis/json_block_check.txt`。）
```json
{
  "task": "TASK-SMOKE-T12",
  "round_id": "smoke-t12",
  "round_dir": "runs/smoke-t12",
  "project_dir": ".workspace/fresh-t12",
  "head": "47680397fff0a990c92470c271a5a6e583aa8fc9",
  "started_at": "2026-10-02 02:49:33",
  "ended_at": "2026-10-02 03:25:17",
  "elapsed_seconds": 2144,
  "round_exit": 0,
  "engine": {
    "version_string": "4.8.dev.mono.custom_build.035edfce7",
    "binary": "F:\\moonbit-hof-rs\\godot-mcp\\godot\\bin\\godot.windows.editor.x86_64.mono.exe",
    "size_bytes": 194216960,
    "mtime_unix": 1790641862,
    "sha256_recorded_only": "08483088a4a2772841cd3b4c916b2d45b3cb6255656cf3951598a86fce7e9e6a",
    "listener_pid": 33556,
    "listener_matches_binary": true,
    "role_at_listen": "editor",
    "tools_at_editor_endpoint": 154,
    "started_by_this_round": true,
    "note": "No editor was running at round start (port 9877 had no listener). First launch was made with --path pointing at the still-empty project directory and the engine came up as role=game with 73 tools (all 104 editor_* tools absent); after `hoh init` created project.godot a relaunch reported role=editor with 154 tools."
  },
  "start_state": {
    "mode": "fresh",
    "version_id": null
  },
  "fresh_project_evidence": {
    "directory_absent_before": true,
    "empty_listing": "ls -la -> 'total 0' (only . and ..); find -mindepth 1 | wc -l -> 0",
    "init_command": "hoh init --project F:\\moonbit-hof-rs\\.workspace\\fresh-t12",
    "init_exit": 0,
    "run_command": "hoh run --iterations 1 --run-id smoke-t12 --fresh-workspace --project F:\\moonbit-hof-rs\\.workspace\\fresh-t12",
    "editor_scope_verified": "project_list_scripts -> {\"count\":0,\"scripts\":[]} and project_get_filesystem_tree lists exactly the init scaffold (project.godot, scenes/main.tscn, scripts/README.md)",
    "script_count_new_project": 0,
    "script_count_old_mario_project": 15
  },
  "binary_rebuild": {
    "command": "cargo build --release --offline",
    "exit": 0,
    "before": {
      "size_bytes": 12692992,
      "mtime": "2026-10-01 23:49:06"
    },
    "after": {
      "size_bytes": 12713984,
      "mtime": "2026-10-02 02:45:40",
      "sha256": "310075faea14317af48a9602f7baedb1fc1e0d2af8bb4a057f3f00cb4f7158ca"
    },
    "new_symbol_present": "STALE_ACTION_NOT_RELEASED",
    "new_message_present": "the game the role started with `editor_play_scene` did not answer"
  },
  "product_identity": {
    "A0": {
      "runtime_id": "3ac25f6c5c38885febd3a001ea99c88aca61b1799c7b105306919886c2c1d151",
      "files": 3,
      "bytes": 1727
    },
    "A1": {
      "runtime_id": "fc50ecd2c1acfcb9854c14b99edfc9dcc5f7004f6377b34ba90a1bb088cd228d",
      "files": 11,
      "bytes": 7384
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
          "to_bytes": 3580
        }
      ],
      "removed": []
    }
  },
  "verdicts": {
    "E1": "met",
    "E2": "met",
    "E3": "met",
    "E4": "met",
    "E5": "met",
    "E6": "met"
  },
  "unjudgeable": [],
  "e3_classes": {
    "move_left": {
      "observed": true,
      "delta_px": -216.332458496,
      "frames": 60,
      "source": "input_replay[43] 1149.00085449219 -> 932.668395996094, 60/60 unique x"
    },
    "move_right": {
      "observed": true,
      "delta_px": 216.333312988,
      "frames": 60,
      "source": "input_replay[7] 881.334777832031 -> 1097.66809082031, 60/60 unique x"
    },
    "jump": {
      "observed": true,
      "x_unique": 1,
      "x_value": 1156.33410644531,
      "y_first": 269.980834960938,
      "y_min": 214.258605957031,
      "y_last": 242.59196472168,
      "y_unique": 30,
      "source": "input_replay[31], a pure vertical arc (x held constant)"
    },
    "interactable_object": {
      "observed": true,
      "evidence": "interaction_evidence[0] Coins: 0 -> [24] Coins: 2; running_game_assert_node_state text:neq passed=true (actual 'Coins: 2', expected 'Coins: 0')"
    },
    "win_condition": {
      "observed": true,
      "evidence": "Goal.reached false at [1]/[10]/[16] -> true at [22]; running_game_assert_node_state reached:neq passed=true"
    }
  },
  "fixes": {
    "1_stale_action_release": {
      "verdict": "green",
      "evidence": "interaction_evidence call[4] running_game_play_input_recording label='interaction:release_stale_move_left' -> {\"event_count\":1,\"injected\":1,\"replayed\":true,\"speed\":1.0}, before the first driven batch at call[6]; the window then advanced the player 60/60 unique x samples per batch",
      "STALE_ACTION_NOT_RELEASED_count": 0
    },
    "2_observation_before_consumption": {
      "verdict": "green",
      "evidence": "battery step order: interaction_evidence at index 6, input_channel_probe at 7, input_replay at 8; the window's own before-reading is Coins: 0 and the after-reading is Coins: 2",
      "coin_before": "Coins: 0",
      "coin_after": "Coins: 2"
    },
    "3_role_started_route_republish": {
      "verdict": "unexercised",
      "evidence": "No role invoked editor_play_scene and no role invoked any running_game_* tool this round (0 hoh tools call in every trajectory; the developer's 38 live calls were all editor_*/project_*), so the role-side republish path and its refusal semantics were NOT exercised and no readiness-wait time can be attributed to it.",
      "role_editor_play_scene_calls": 0,
      "role_running_game_calls": 0,
      "endpoint_refusals": 0,
      "route_file_rewritten_during_round": true,
      "route_values_directly_observed": [
        {
          "value": "http://127.0.0.1:57989/mcp pid 29776",
          "seen": "developer trajectory msg 116 (the role ran cat on runs/smoke-t12/game_endpoint.json)"
        },
        {
          "value": "http://127.0.0.1:53694/mcp pid 25236",
          "seen": "this round's direct read at 03:12"
        }
      ]
    }
  },
  "delivery_vs_movement": {
    "delivery_facts_injected_1": 12,
    "delivery_facts_by_window": {
      "interaction_evidence": 4,
      "input_channel_probe": 1,
      "input_replay": 7
    },
    "movement_facts_unique_x_60_of_60": true,
    "note": "injected=1/replayed=true proves only that the game accepted an event; the movement evidence is the position sample series and the in-game assertions"
  },
  "mechanisms": {
    "zero_increment": false,
    "repair_attempts": {
      "repair_retry_used": false,
      "wrap_up_retry_used": true,
      "wrap_up_retry_reason": "artifact_missing"
    },
    "truncation_64kib_triggered": false,
    "largest_single_message_bytes": 50026,
    "editor_errors_baseline_count": 0,
    "mcp_sync_desynced": false,
    "mcp_errors_file_present": false,
    "exit_code_three_way": {
      "round_dir_exit_code": "0\\n",
      "process_exit_code": "0\\n",
      "meta_json_exit_code": 0
    },
    "ready_wait_battery_play_scene": "1 poll",
    "ready_wait_role_side": "not measured (path unexercised)"
  },
  "criteria": [
    {
      "id": "E1",
      "pass": true,
      "evidence": "fresh empty dir -> hoh init exit 0 -> one hoh run exit 0; start_state.mode=fresh; A0=3ac25f6c... 3 files/1727 B -> A1=fc50ecd2... 11 files/7384 B; plan.md + evidence.json accepted; exit codes agree three ways"
    },
    {
      "id": "E2",
      "pass": true,
      "evidence": "editor_errors_baseline count=0; play_scene_ready playing=true pid=27736; running_game_get_scene_tree returned 22 nodes; editor_stop_scene stopped=true; artifact_gate launchable=true reasons=[]"
    },
    {
      "id": "E3",
      "pass": true,
      "evidence": "all four classes observed on the game endpoint: move_left -216.33 px, move_right +216.33 px, jump pure vertical arc, Coin1/Coin2 Area2D picked up (Coins: 0 -> 2) and Goal reached (false -> true), each with a running_game_assert_node_state passed=true in the game process"
    },
    {
      "id": "E4",
      "pass": true,
      "evidence": "evidence.json: 12 verified / 10 gap, overlap empty, 33 execution records all present on disk, all candidate-bound to fc50ecd2..., all gaps carry player_impact and recommended_update"
    },
    {
      "id": "E5",
      "pass": true,
      "evidence": "versions/fc50ecd2... == iter-1/candidate == live .workspace/fresh-t12, byte-identical (11 files/7384 B, no only-in/differing entries)"
    },
    {
      "id": "E6",
      "pass": true,
      "evidence": "qa_report.md declares 'Verdict: partial' and enumerates 8 gap families explicitly, including the F1-stop regression; it refuses to overstate (the GAME_INPUT_CHANNEL_OK axis probe is called out as not usable)"
    }
  ],
  "honest_disclosure": [
    "I launched the engine once before hoh init on an empty --path; it came up role=game with 73 tools. I stopped it (pid 22908), ran hoh init, and relaunched; the editor then reported role=editor with 154 tools. Both launches are in the evidence.",
    "The staging directory .workspace/.t12-scratch was created to keep preflight evidence alive across --fresh-workspace's purge of the project directory; it is removed at the end.",
    "wrap_up_retry_used=true reason=artifact_missing: the developer exhausted its limits on both attempts (artifact_valid=false) and the run still snapshotted the on-disk files as A1.",
    "Fix 3 (role-side route republish) was NOT exercised by any role; I report it as unexercised rather than green.",
    "The route file was rewritten to two values I read directly; I could not attribute either rewrite to a specific call from the frozen evidence."
  ]
}
```
