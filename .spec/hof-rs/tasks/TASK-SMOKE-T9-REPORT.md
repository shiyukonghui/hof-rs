# TASK-SMOKE-T9-REPORT — 真机 T=1 整轮（引擎 `035edfce7`；**E1 仍 not_met，但障碍又换位**：Developer 零工程增量 → `NoEngineeringWrite` 契约类退出码 **2**；E3 的**四类行为全部**在我的独立真机实验中被语义工具观测到）

- 任务书：`.spec/hof-rs/tasks/TASK-SMOKE-T8.md`（**唯一任务来源**，本轮沿用）+ 调度者本轮追加的五条
- 落点：`F:\moonbit-hof-rs`（外层仓），报告人：**真机执行子代理（无上游上下文）**
- 本轮命令：`target/release/hoh.exe run --iterations 1 --run-id smoke-t9`
- **本轮实际跑了两次**：attempt-A（**环境自修前的失败**，10:49:20 → 11:07:13，退出码 5）与 attempt-B
  （**重试即本轮正式轮**，11:08:44 → 11:27:29，**18 分 45 秒**，退出码 **2**）。两次都如实留档（§13）。
- 本轮基线：`runs/smoke-t9/**`（**83 文件** `/ 541e2d81…36ca9d`，全新目录）
- 只读基线（开工/收工逐字未变，§9）：`runs/smoke-t6`（135 `c144ef32…7a9c03`）、`runs/smoke-t7`（115 `6e4c1595…20fb7`）、
  `runs/smoke-t8`（358 `6d11b2c6…bdf5a7`）
- 开工 HEAD **`509ec0c`**（构建用）；我工作期间**调度者**又提交了 `a9e050c`（D268 修正 + 摘要尾串更正），收工 HEAD `a9e050c`；
  `origin/master` 全程 `fe129a1`（**ahead，未 push**）
- 我**未改**任何受控文件：`git status --porcelain -uall` 中**没有**任何被跟踪文件被改（唯一 `M` 项 `TASK-DR68-ACCEPTANCE.md` 在**我开工前**就已是 `M`，随后被调度者的 `a9e050c` 收编）；
  `godot-mcp/**` 零改动；`PRD-mario.md` sha256 仍 `4c81c3a9…5c3a`；`DECISIONS.md` 未由我编辑；未 push。

---

## 0. 结论摘要（E1..E6）

| 编号 | 判定 | 一句话依据 |
|---|---|---|
| **E1** | **not_met（障碍换位：Developer 零工程增量）** | Planner 产出合法 `D_1`（`artifact_valid=true`），**Developer 在 175 次调用 / 150+25 步里没有写任何一个工程文件**（工程树最后一次写入仍是 t8 的 `player.gd 07:19:25`）⇒ `no_progress` + **`NoEngineeringWrite`** ⇒ `ok=false`/`failed_role=developer`/退出码 **2**。**没有** `E_1`、**没有** Tester 阶段（因此 t8 的 schema 根因本轮**根本没有被走到**，不能沿用）。§2 |
| **E2** | **本轮不可判定（无证据）** | 失败发生在**冻结与电池之前**：`runs/smoke-t9/iter-1/` 下**没有** `candidate/`、**没有** `.hoh/deterministic/**`、没有 `battery.json`/`deterministic.log`。不以 t8 或我的实验替代本轮判据。§4.1 |
| **E3** | **本轮不可判定（无证据）**；**但四类行为在我的独立真机实验中被语义工具观测到** | 轮内**没有** `input_replay.json`（电池未跑）。我的独立实验（release-first，语义工具直读游戏进程）：**右移** 60 帧 `+216.333`（恒 `+3.6667 px/帧`）、**左移** 60 帧 **`−216.333`**（恒 `−3.6667 px/帧`）、**跳跃** y `221.09→峰 214.26→283.98`、**金币** `coins 0→1` 且 `Coin1` 从场景树消失、**终点** `Main.state = "won"`。**仍不判 met**：任务书的证据形态含**前后截图**与 `assert_node_state`，我的实验两者都没有，且这不是轮内证据。§3 |
| **E4** | **本轮不可判定（前提缺失）** | `E_1` 不存在（Tester 未运行），"每个 verified claim…"无从核起。§4.2 |
| **E5** | **本轮不可判定（无快照）** | 没有冻结：`versions/index.json` 只有 `A0`（`role=init`），**没有 `A_1`**、没有候选树。§4.3 |
| **E6** | **本轮不可判定（无工件）** | 同上，没有 QA 工件。§4.4 |

**与 `smoke-t7`/`smoke-t8` 相比的净变化**：**E1 的失败点第三次换位**——t7 是"Developer 零增量"，
t8 是"Developer 有增量、Tester 形状被拒"，**t9 又回到"Developer 零增量"，但机制完全不同**（t7 是 shell 方言烧预算；
t9 是**角色 CLI 结构上到不了游戏端点** ⇒ Developer 把整个预算花在 `.hoh/scratch` 里自造 MCP 客户端）。
**退出码 0 → 3 → 2**：本轮**首次在真机上走到契约类 `NoEngineeringWrite ⇒ 2`**（这正是 DR-68 验收 §7.6 点名未闭合的缺口）。
**电池/门/证据全链条本轮一次都没跑到**，所以 E2..E6 全部不可判定——**不以红灯冒充绿灯**。

**调度者本轮五条追加，逐条对应**：

| # | 追加问题 | 本轮答案 | 位置 |
|---|---|---|---|
| 1 | E1 是否到达 `met`？合法证据束是否被接受、整轮能否跑完？ | **否**。**但失败原因与上一轮不同**：Tester **根本没运行**，schema 未被触及。新原因 = `NoEngineeringWrite`（契约类，退出码 2）。 | §2 |
| 2 | 启动闸门双向行为；过期行不得关门、真实当前错误仍关门；有无修复尝试及其是否写工程树 | 本轮**门一次都没被评估**（无电池）。离线对拍 **14/14 通过**，含 stale 不关门与真实错误关门两个方向。本轮**没有任何修复尝试**（`repair_retry_used=false`，无 `developer.attempt3`）⇒ 无"修了但零写入"的缺陷。 | §5 |
| 3 | E3 左移：诚实说明能/不能确立什么（自抽逐帧数字） | **左移确实有效**：release-first 后 60 帧 `x 283.667→67.333`，恒 `−3.6667 px/帧`。**轴值断言在真机不触发**（`input_axis` 恒 `null`，已实测），承重的是**按轴的位置**。 | §3 |
| 4 | 失败路径是否写出真实电池与候选身份 | 本轮失败在**冻结之前**，三个字段**如实为空**：无 `A_1`、无电池。可自证（`versions/index.json` 只有 `A0`；无 `candidate/`；无 `deterministic/`）。 | §6 |
| 5 | 先构建再跑；离线门新增格式检查；编辑器存活；孤儿游戏进程 | 先 `touch`+`cargo build --release --offline`（exit 0）后跑；`cargo fmt --check` **exit 0**；编辑器 pid **75204 全程存活**；**发现并清理 1 个孤儿游戏进程 pid 77708**（§10）。 | §9/§10 |

---

## 1. 本轮执行流水（含一次环境自修）

### 1.1 前置（开工前，全部为只读/构建）

```
HEAD                                  509ec0cd3093215fba35816e5b072d408f3f2e20
git status --porcelain -uall          " M .spec/hof-rs/tasks/TASK-DR68-ACCEPTANCE.md"   (非我所为)
origin/master                         fe129a163d6ca22e5e4b48b81e7229c4260b1291   ahead=1
git ls-files '*.rs' | wc -l           78   → xargs touch（只 touch 已存在文件，未造出 build.rs）
cargo fmt --check                     FMT_EXIT=0
cargo build --release --offline       Compiling hof-rs v0.1.0 → Finished in 17.99s   BUILD_EXIT=0
target/release/hoh.exe                mtime 2026-09-30 10:48:17 · sha256 2825bda9e809c2d928618efae06ffb8483ebae979d804b24ab8c60927f74623d
engine --version                      4.8.dev.mono.custom_build.035edfce7
hoh doctor                            DOCTOR_EXIT=0（spec sha 命中、model.chat 命中、godot.engine_version 命中、tools.mcp 154）
editor                                127.0.0.1:9877 LISTENING pid 75204；GET /mcp → tools=154
```

原文：`.spec/hof-rs/tasks/TASK-SMOKE-T9-evidence/experiment/{prerun_state.txt,doctor.txt,postrun_state.txt}`。

### 1.2 attempt-A（10:49:20 → 11:07:13，**退出码 5**）

```
hoh: harness failed for role developer iteration 1: llm-connector chat request failed
```

**这是环境/通道失败，不是产品判定**。我先做环境自修（重试），并把 attempt-A 的证据搬到仓外受控目录
（`.../TASK-SMOKE-T9-evidence/attempt1-aborted/**`），随后删除 `runs/smoke-t9` 重跑（§13 有完整披露）。

### 1.3 attempt-B（10:49 之后重试；11:08:44 → 11:27:29，**18 分 45 秒**，**退出码 2**）

```
hoh: contract violation: NoEngineeringWrite (no_engineering_write)
```

`runs/smoke-t9/exit_code` = `32 0a`（`"2\n"`）、`meta.json.exit_code = 2`、进程退出码 **2** ⇒ **三方一致**。

---

## 2. E1 专项 —— **not_met**，根因**不是** Tester schema（本轮没跑到那里）

### 2.1 三个要件逐条

| 要件 | 结果 | 证据 |
|---|---|---|
| Planner 产出合法 `D_1` | **成立** | `runs/smoke-t9/iter-1/plan.md`（2738 B）含 `### Priority Order`/`### Preservation Gate`/`### Acceptance Gate`；`logs/planner.attempt1.log` → `"artifact_valid": true` |
| Developer 产出 Godot 工程增量 | **不成立（零工程增量）** | `warnings.log`：`iteration 1: no_progress (the developer stage produced no change)` + `contract violation no_engineering_write (… every write went to an excluded path such as .hoh/scratch, .godot/** or .import/**)`；`result.json`：`failed_role="developer"`、`reason="contract_violation"` |
| QA 产出合法 `E_1` | **不成立（Tester 从未运行）** | `iter-1/traj/` 只有 `planner.attempt1.json` / `developer.attempt1.json` / `developer.attempt2.json`；**没有** `tester.*`、`evidence.json`、`qa_report.md` |

**"零工程增量"的硬证据（我自己算，不看运行时自报）**：

```
$ find .workspace/mario -type f -newermt "2026-09-30 11:08" -not -path "*/.hoh/*" -not -path "*/.godot/*" | wc -l
0
工程源文件最后的 mtime（全部早于本轮）：
  scripts/main.gd    2026-09-30 07:16:30     ← t8
  scenes/main.tscn   2026-09-30 07:17:58     ← t8
  scripts/player.gd  2026-09-30 07:19:25     ← t8
本轮窗口内有写入的文件共 45 个，全部落在 .hoh/**（运行时排除）与 .godot/**（缓存排除）。
我的工程树摘要（口径见 §9.2）：17 文件 / 18397 B / 5971b484…e463 —— 轮前轮后**同一个值**。
versions/index.json 只有 A0(init)=1f3d20ed…fd8，没有 A1。
```

⇒ `result.json.candidate_id=null`、`version_id=null`、`battery_passes=[]` **不是**失败存根的偷懒，而是**如实的空**：
本轮**确实没有** `A_1`、**确实没跑**电池（§6）。

### 2.2 为什么 Developer 一步工程写入都没有 —— **机制链（全部实测，可指文件:行与原始输出）**

**实测 1：Developer 全程只"读"过一次工程文件，之后再没碰过工程树。**

命令级扫描（脚本 `find_writes.py`，输出 `experiment/dev1_project_write_scan.txt`）：184 条命令中，只有 **4 条**提到工程源文件，
**全部是只读**（`type project.godot` / `type scenes\main.tscn` / `type scripts\main.gd` / `dir /s /b scenes scripts addons`），
出现在第 4–6 步；**没有任何一条写入/重定向到 `scripts/**`、`scenes/**`、`project.godot`**。

**实测 2：它把 150 步全部花在 `.hoh/scratch` 里自造 MCP 客户端。**
`dev1_commands.txt` 显示：第 9–145 步在处理 `%HOH_SCRATCH_DIR%` 下的 `mkdir`/`echo`/`python -c`/`printf` 脚手架，
反复试错 heredoc（`<< was unexpected at this time.`）、`python -c` 拼行、`from mcp import call` 导入失败等；
它最终自造了 `call.py`/`mcp.py`/`drv.py`，用**裸 HTTP**打游戏端点（端口 `57529 → 65009 → 55087 → 61245`，逐个试）。

**实测 3：它为什么绕道 —— 角色 CLI 结构上到不了游戏端点（本轮最重要的新发现，F-T9-1）。**

原始回包（`developer.attempt1.json`，第 27/32 步）：

```
$ %HOH_HOH_BIN% tools call running_game_get_scene_tree --args-file %HOH_SCRATCH_DIR%\args\tree.json
hoh: game_endpoint_unavailable: `running_game_get_scene_tree` runs in the game process and only the game
endpoint serves it; no game endpoint is registered yet (`editor_play_scene` must have answered with
`endpoint` or `mcp_port`). Falling back to the editor endpoint is not allowed (DR-43).
```

我在**本轮之外**做了受控复现（游戏确实在跑、端点确实已公布）：

```
$ hoh tools call editor_play_scene --role tester --args '{}'
{"args_injected":["--mcp-port=61183"],"endpoint":"http://127.0.0.1:61183/mcp","mcp_port":61183,"pid":106368,"playing":true}
$ hoh tools call running_game_get_scene_tree --role tester --args '{}'      # 另一个进程
hoh: game_endpoint_unavailable: … no game endpoint is registered yet …
EXIT=5
```

**代码层根因（文件:行）**：

| 落点 | 事实 |
|---|---|
| `src/tools/mod.rs:138` | 游戏路由是 **进程内**状态：`game: Arc<Mutex<Option<GameRoute>>>` |
| `src/tools/mod.rs:186-205` | `client_for()` 对 `running_game_*` 找不到路由即 `bail!`（硬错误，**不允许**回落编辑器端点，DR-43） |
| `src/tools/bridge.rs:227-234` | `channel_for(config)` 每次都 `McpChannel::new(...)` —— **新建，空路由** |
| `src/cli_impl.rs:53` | `hoh tools call` 每次调用都 `let channel = bridge::channel_for(&config);` 然后进程退出 |
| `src/tools/mod.rs:312` | `register_game_endpoint` 只写**本进程**内存 |

⇒ 角色的每条 `hoh tools call` 都是**新进程**，其游戏路由**永远为空** ⇒ **角色 shell 永远无法用契约内的
`running_game_*` 工具**（除非它自己起游戏并**在同一次调用**里完成——不可能，因为 `hoh tools call` 一次只发一个工具）。
只有**运行时自己**（`src/adapter/godot.rs:901-911` 在 `editor_play_scene` 回包里 `register_game_endpoint`）与
**恰好同一次调用的那个进程**能看到游戏路由。

**现场对照**：t8 的 Developer 也撞过同一个错误（`game_endpoint_unavailable` 出现 **20 次** vs 本轮 **4 次**），但 t8 它继续写代码；
本轮它选择把预算全投进"把游戏跑起来看"的绕道。⇒ **同一个结构缺陷，两次真机得到两种后果**，说明它是**放大器**而非唯一原因。

**① 实测（有原始输出）**
1. 工程树零写入（45 个写入全在 `.hoh/**` + `.godot/**`；工程源文件 mtime 停在 t8）。
2. 184 条命令中只有 4 条提到工程源文件，且全是只读（第 4–6 步）。
3. `%HOH_HOH_BIN% tools call running_game_*` 在游戏运行时仍报 `game_endpoint_unavailable`（受控复现，EXIT=5）。
4. 契约闸门确实触发：`no_progress` + `no_engineering_write`，退出码 2 三方一致。
5. 本轮 `bash -c` 包裹 **0** 次、cmd 方言错误 **0** 次、`%HOH_*` 引用 175 次 ⇒ t7 的"shell 方言"机制**本轮不复现**。

6. t8 Developer 撞同一错误 20 次（t9 4 次），但 t8 写了代码。

**② 推断（明确标为推断，不得当实测）**
1. **（≈0.8）** t9 的 `plan.md` 把"可观测结果"钉在 `running_game_get_node_property_samples` /
   `GAME_INPUT_CHANNEL_OK` 上（第 3–5 行、第 12 行），而 A0 已是**功能完整**的 17 文件工程 ⇒ Developer 把任务理解为
   "先证明行为能观测"；一旦契约通道被堵，它转向绕道而不是改代码。
2. **（≈0.6）** 提示词层缺一条"**你先动手改，观测由 Tester/电池负责**"的分工约束；本轮 Developer 没有任何被告知
   "游戏通道对角色不可用，别在这上面花时间"。
3. **（≈0.5）** 若 `plan.md` 的第 1 优先级（可启动 + 无错）本就是"已满足"，模型缺少"本轮该改什么"的抓手，
   于是把预算花在探索上。**注意这三条都是推断；我只对"零写入"与"通道不可达"负责任**。

### 2.4 与 `smoke-t8` 的 E1 对照（同一判据，三个不同故障点）

| 轮 | `A_1 ≠ A_0` | 失败角色 | 失败原因 | 退出码 |
|---|---|---|---|---|
| t7 | **否**（`A_1 == A_0`） | developer | 零增量（提示词 shell 方言烧预算） | 0（当年未建闸门） |
| t8 | **是**（3 文件） | **tester** | `schema_failure`（证据缺 `type`/`claim_id`） | 3 |
| **t9** | **否**（`A_1` 不存在） | **developer** | **`contract_violation` / `no_engineering_write`** | **2** |

⇒ **t8 的 E1 障碍（Tester 证据形状）本轮根本没被走到**；DR-68 ① 的修复在**离线**上成立（`schema_gate` 6/6，§5.3），
但**真机是否自愈仍未验证**（与 DR-68 验收 R-1 一致）。

---

## 3. E3 专项 —— 轮内无证据；**独立真机实验：四类行为全部可观测**

> 纪律：**我不把任何探针结果当行为证据**；本轮连探针都没跑（无电池）。下面每一条都来自
> **语义工具直读运行中的游戏进程**，逐帧数字由我自己从原始回包抽出（脚本与原文见 §16）。

### 3.1 轮内：**没有 E3 证据**（如实）

`runs/smoke-t9` 下不存在 `.hoh/deterministic/raw/input_replay.json`、`input_channel_probe.json`、
`play_scene_ready.json` 等任何电池 raw —— 因为开发者阶段就违约退出，**电池从未运行**。
⇒ 按任务书口径，本轮 **E3 不可判定**，且**不得**用 t8 的 raw 或我的实验冒充轮内证据。

### 3.2 我的独立实验（release-first；语义工具；直读游戏进程）

方法（脚本 `experiment/e3_probe.py`）：先 `editor_play_scene`（`--role tester`）拿到 `mcp_port=61183 / pid=106368`；
每个方向测试前**先在游戏进程内释放全部动作**（`running_game_play_input_recording`，`pressed:false`），
再注入目标动作，再 `running_game_get_node_property_samples`（`frame_count=60/30`）逐帧读数。
原始输出：`experiment/e3_probe_output.txt`。

| 窗口 | 注入 | 帧 | 首/末 x | 首/末 y | 目标轴位移 | 逐帧 |
|---|---|---|---|---|---|---|
| BASELINE | 无（仅释放） | 30 | 恒定 | 恒定 | `dx=0 dy=0` | 静止 |
| **MOVE_RIGHT** | `move_right pressed=true` | 60 | 111.333305 → 327.666595 | 283.999 恒定 | **`dx=+216.333290`** | 恒 **+3.6667 px/帧** |
| **MOVE_LEFT** | `move_left pressed=true` | 60 | 283.666718 → **67.333321** | 283.999 恒定 | **`dx=−216.333397`** | 恒 **−3.6667 px/帧** |
| **JUMP** | `jump pressed=true` | 30 | 63.667 恒定 | 221.092 → **峰 214.259（f6）** → 283.979 | `dy=+62.887` | 先升后落回地面 |

- 每个窗口注入前 `running_game_get_node_properties` 都是 `controllable=true, velocity=(0,0), position.y=283.999`（地面、静止）
  ⇒ 排除了"角色不可控 / 残留速度"两种解释（对照 t8 的实验边界问题）。
- `3.6667 px/帧 × 60 帧/s = 220.0 px/s`，与 `scripts/player.gd` 的 `speed = 220.0` 数值自洽 ⇒ 位移来自游戏自己的移动代码路径。
- **左移结论（本追加的核心）**：**左移有效**——`dx=−216.333397`、逐帧恒 `−3.6667`，且释放上一输入后
  `get_axis` 不再被 `move_right` 抵消。t8 的"左移不产生位移"确实只是**注入时序假象**；DR-68 的正确读法
  "not established"在本轮被推进为 **established（有效）**。

**金币与终点（第二个独立实验，脚本 `experiment/e3_interact.py`，原文 `experiment/e3_interact_output.txt`）**：

```
start Main=  {"coins": 0, "lives": 3, "state": "playing", "time_left": 118.97}
场景树含 Coin1..Coin4 / Enemy1,Enemy2 / QuestionBlock / Brick1 / Goal / HUD(Score,Result,Lives,Coins,Time)
把 Player 置于 Coin1(300,290) →  Main.coins: 0 → 1 ；再读场景树：Coin1 已不在树中（present=False）
把 Player 置于 Goal(6400,280) →  Main.state = "won"
```

⇒ **"至少 1 个可交互对象"与"一个终点/胜负条件"也在游戏进程内被语义工具观测到**（金币被拾取并消失、计数 +1；到达终点进入 `won`）。

### 3.3 我不能确立什么（诚实边界）

1. **不判 E3 met**：任务书要求 E3 的证据形态是 `simulate_sequence` 回放 + **前后截图** + `assert_node_state`；
   我的实验**没有截图**、`run_test_scenario` 只在轴探针里用过一次（且该断言因 `input_axis` 不存在而失败）。
   证据形态不达标 ⇒ **不声称 met**。
2. **终点是"瞬移到达"而非"走过去"**：我用 `running_game_set_node_property` 把 Player 放到 `Goal` 坐标；
   **没有**验证"从出生点一路走到终点"的可玩性（金币那一半我是**瞬移**到币位；但 `move_right` 窗口里
   Player 从 x=111 走到 x=327，**确实穿过了 Coin1(x=300)** ⇒ 拾取也与正常行走一致）。
3. **这些是我的实验，不是轮内证据**；它们证明"**产物侧四类行为都实现了**"，不证明"**流水线能自动证到**"。
4. **`input_axis` 断言的 caveat 已实测成立**（与调度者提醒一致）：
   ```
   samples: [{"frame":0,"input_axis":null},{"frame":1,"input_axis":null},{"frame":2,"input_axis":null}]
   run_test_scenario assert input_axis → passed=false,
     reason="node '/root/Main/Player' does not have the property 'input_axis'"
   ```
   ⇒ **DR-68 ③(a) 的"断言轴值确实改变"在真机上几乎不会触发**；真机承重的是
   `movement_on_intended_axis`（**按目标轴的位置断言**），这一点由上面的逐帧数字直接支撑。

---

## 4. E2 / E4 / E5 / E6 —— 本轮**不可判定**（无对应证据，不以红灯冒充）

### 4.1 E2：没有电池、没有候选

`runs/smoke-t9/iter-1/` 下没有 `candidate/`，也没有 `.hoh/deterministic/**`；
`find runs/smoke-t9 -name battery.json -o -name deterministic.log` 为空。
⇒ 本轮**没有** `launchable`、`editor_errors_baseline`、`play_scene_ready` 的任何读数。

### 4.2 E4：没有 `E_1`

没有 `tester.*` 轨迹、没有 `evidence.json`/`qa_report.md` 工件。
（`iter-1/planner-view/.hoh/evidence.json` 是 Planner 的**输入副本**：`iteration:0, verified_records:[], gap_records:[]`，
不是本轮 `E_1`，不得混用。）

### 4.3 E5：没有快照可对

`versions/index.json` 只有 `A0`（`role=init`、`created_at 1790737726`），**没有 `A_1`**
⇒ "QA 未修改 `A_1`"没有对象。可如实说的是：**本轮的运行树没有任何工程文件被写过**（§2.1），
这是比 E5 更强的静态事实，但它不构成 E5 的"前后快照 hash 一致"判据。

### 4.4 E6：没有 QA 工件 ⇒ 无从复核诚实性

（内容层无对象；不作任何"诚实/不诚实"的判定。）

---

## 5. 启动闸门（追加 2）—— 本轮未评估；离线对拍**双向**成立；**无任何修复尝试**

1. **轮内事实**：因为电池没跑，门**一次都没有被评估**：
   - `result.json.artifact_gate = {"applicable":false,"launchable":false,"reasons":["no launchable gate was evaluated for this iteration"]}`
   - `meta.json.artifact_gate  = {"applicable":false,"launchable":false,"reasons":["the round failed; no artifact gate was produced"]}`
   ⇒ **两处都自洽**（对比 t8 失败轮曾写 `launchable=true`；DR-68 ⑦ 的修正在本轮真机的失败路径上**成立**）。
2. **修复尝试：无。** `result.json.repair_retry_used = false`；`iter-1/traj/` 里**没有** `developer.attempt3`；
   `warnings.log` 无 `launch_gate_repair`。⇒ 本轮**不存在**"修复尝试但零写入"的情况（t8 的 F1 代价本轮未复现）。
3. **双向行为（离线对拍，非真机）**：`cargo test --offline --test launchable_gate` ⇒ **14 passed / 0 failed / exit 0**，
   其中直接对拍两向的是：
   ```
   a_stale_editor_log_line_does_not_close_the_gate ........... ok   ← 过期行不关门
   a_reproducible_parse_error_still_closes_the_gate ......... ok   ← 真实当前错误仍关门
   a_real_editor_error_still_closes_the_gate ................ ok   ← 真实错误仍关门（不同形状）
   a_launchable_project_never_invokes_a_repair .............. ok   ← 门开时不触发修复
   a_broken_scene_triggers_exactly_one_targeted_repair ...... ok   ← 真坏时**恰好一次**定向修复
   an_unknown_mcp_prefixed_line_still_closes_the_gate ....... ok   ← fail-closed 面
   ```
   **口径声明**：这是**离线测试**证据，证明"窄规则没有把门放宽成永不关门"；它**不能**替代真机上的门行为
   （本轮真机没走到门）。与 DR-68 验收 §2.4 的结论一致，且我**独立重跑**了一次。
4. **诚实边界**：DR-68 ② 的规则**故意很窄**（只处理 `res://<file>:<line> … Function "X()" not found in base self.`）；
   `an_unknown_mcp_prefixed_line_still_closes_the_gate` 表明**其它形状仍 fail-closed** ⇒ 下一轮若出现**另一种**陈旧形状，
   仍可能重演"白烧修复"（遗留风险 R-3，非本轮实测）。

---

## 6. 失败路径 `result.json` 的自证（追加 4）

本轮走的是**冻结之前**的失败点（Developer 违约），所以任务书"真实电池/候选身份"的检验方式是：
**三个字段是否如实指向"根本没有"**。

```
runs/smoke-t9/iter-1/result.json:
  "ok": false, "failed_role": "developer", "reason": "contract_violation",
  "candidate_id": null, "version_id": null, "battery_passes": [],
  "evidence_diff": {"added":[],"modified":[],"removed":[]},
  "repair_retry_used": false,
  "artifact_gate": {"applicable": false, "launchable": false, "reasons": ["no launchable gate was evaluated for this iteration"]},
  "warnings": ["qa_scope…","harness_source_read","no_progress","no_engineering_write"]
runs/smoke-t9/versions/index.json: 只有 A0(init) 一条，没有 A1
$ find runs/smoke-t9 -maxdepth 2 -name candidate -o -maxdepth 2 -name deterministic  → 空
```

判定：**如实，非存根**。三条独立证据（无 `A_1`、无候选树、无电池 raw）都指向"这三个字段本来就该是空"，
与 t8 的存根（真实有 `A_1` 与 11/11 电池却写成空）**性质不同**。
**残留（DR-68 R7 未闭合）**：`evidence_diff` 仍是空——本轮它**恰好也该是空**（零写入），所以本轮**无法**区分
"如实空"与"没实现"；该缺陷只能等一轮"有增量但后段失败"的失败轮来暴露。

---

## 7. 新发现清单（本轮，全部可指到 文件:行 / 原始输出）

| 编号 | 级别 | 内容 | 证据 |
|---|---|---|---|
| **F-T9-1** | **major** | **角色 CLI 结构上到不了游戏端点**：`hoh tools call running_game_*` 每次都是新进程，而游戏路由是**进程内**内存 ⇒ 角色**永远**拿不到 `running_game_*`（游戏正在跑、端点已在 `editor_play_scene` 回包里公布的情况下仍然 `game_endpoint_unavailable`，EXIT=5） | `src/tools/mod.rs:138/186-205/312`、`src/tools/bridge.rs:227-234`、`src/cli_impl.rs:53`；原始复现 `experiment/game_endpoint_probe.txt` |
| **F-T9-2** | **major（本轮 E1 的直接因）** | Developer **零工程写入**：175 次调用全部用于 `.hoh/scratch` 自造 MCP 客户端与裸 HTTP 探游戏；184 条命令里只有 4 条提到工程源文件且全是读 | `experiment/dev1_commands.txt`、`experiment/dev1_project_write_scan.txt`、§2.1 的三个 `find` 事实 |
| **F-T9-3** | minor | **planner 仍 `RepeatedFormatError`**：DR-68 ⑥ 的终止符**确实已下发**（轨迹里 7 处 `COMPLETE_TASK_AND_SUBMIT_FINAL_OUTPUT`），但模型在 submit 之后连发 **3 次"无工具调用"的回复**（msg 97/98/99）⇒ mini 判 `FormatError`×3 → `RepeatedFormatError`。**改了提示词不等于模型会遵守**（DR-68 验收 R5 的担忧成立） | `traj/planner.attempt1.json` msg 95-100；`logs/planner.attempt1.log` |
| **F-T9-4** | minor | **工具输出无上限 ⇒ 可直接掐死整轮**（attempt-A 的因）：Developer 的 `dir /s /b /a "%TEMP%" | findstr …` 返回 **15,570,803 字节**，该结果被原样塞进下一次 chat 请求 ⇒ `llm-connector chat request failed`，整轮退出码 5 | `attempt1-aborted/developer_attempt1_summary.txt`（`largest messages: [(221, 15570803)…]`）、`attempt1-aborted/console.txt` |
| **F-T9-5** | info | **孤儿游戏进程机制仍在**：attempt-A 的 Developer 起过游戏（pid 77708，11:06:10，`--mcp-port=51911`），轮失败后**未被收尾**；我手工用 `editor_stop_scene` 清掉 | §10、`experiment/stop_orphan.txt` |
| **F-T9-6** | info | `input_axis` 探针确诊：`running_game_get_node_property_samples` 每帧 `null`，"assert input_axis" 直接报 `does not have the property 'input_axis'` ⇒ DR-68 的轴值断言在真机不触发 | `experiment/axis_caveat.txt` |

---

## 8. 与 `smoke-t7` / `smoke-t8` 的逐项对照

| 维度 | `smoke-t7` | `smoke-t8` | **`smoke-t9`（本轮）** |
|---|---|---|---|
| 引擎 | `4.8.dev.mono.custom_build.035edfce7` | 同 | **同**（`--version` 逐字） |
| `hoh` 二进制 | 建于 `9ff9cd2` | 建于 `0f37105` | **建于 `509ec0c`，sha `2825bda9…623d`（仅记录）** |
| **退出码** | 0 | 3 | **2**（首次真机走到契约类 `NoEngineeringWrite`） |
| `runs/<id>/exit_code` / `meta.exit_code` | `0` / 0 | `3` / 3 | **`"2\n"` / 2**（三方与进程退出码一致） |
| 持久化 `artifact_gate` | `launchable=true,reasons=[]` | `applicable=false,launchable=true`（假绿） | **`applicable=false,launchable=false`**（自洽，DR-68 ⑦ 生效） |
| 电池 | 11 步 / 9 ok | 11 步 / **11 ok**（pass 2） | **未运行**（无 candidate、无 deterministic） |
| `input_channel_probe` / `input_replay` | `EDITOR_SIDE_INJECTION`（不可归因） | `game_process` 四元组（右移/跳跃可归因，左移被时序污染） | **未运行**（轮内无证据）；我的独立实验四类行为全观测到（§3） |
| 工程增量 | `A_1 == A_0`（零） | `A_1=1f3d20ed…`（3 文件） | **`A_1` 不存在（零）** |
| `E_1` | 有（被接受，8 verified+20 gap） | 无（被 schema 拒） | **无**（Tester 未运行） |
| 失败角色 / 原因 | developer / `LimitsExceeded` | tester / `schema_failure` | **developer / `contract_violation`+`no_engineering_write`** |
| attempts | 3 | 6 | **3**：planner `RepeatedFormatError`(1) + developer `LimitsExceeded`(1+wrap-up 1) |
| MCP 错误日志 / 传输失败 / 运行时 `-32602` | 1 / 0 / 1 | 0 / 0 / 0 | **0 / 0 / 0**（无 `mcp-errors.jsonl`；run 内 18 处 `-32602` 字面串**全部**来自模型自己的裸 HTTP 回包，非运行时尝试） |
| `repair_retry_used` | false | `deterministic:true` / `result.json:false`（两层） | **false**（无修复尝试） |
| tokens | 22,424,721 | 24,462,425 | **8,094,119**（planner 561,394 + developer 7,532,725） |
| 墙钟 | 74:58 | 65:27 | **18:45**（早退，含 attempt-A 的 17:53 另计） |
| E1..E6 | `not_met/met/not_met/met/met/met` | `not_met/met/not_met(部分)/not_met/met/met` | **`not_met / 不可判定 / 不可判定 / 不可判定 / 不可判定 / 不可判定`** |

**回答调度者追加 1（核心问题）**：**E1 未达到 `met`，而且失败点不在 Tester**——
本轮 **Tester 从未运行**，所以 t8 的 schema 拒绝**没有被再次触发**（既没有"仍然失败"，也没有"自愈"）。
新原因是 **Developer 零工程增量 → `NoEngineeringWrite`**；其直接机制是 **F-T9-1（角色 CLI 到不了游戏端点）**
叠加 **F-T9-2（模型把全部预算投进绕道）**。

---

## 9. 工程身份、摘要口径与禁区自证

### 9.1 引擎身份（判据 / 记录严格分开）

| 项 | 值 | 性质 |
|---|---|---|
| **`--version`** | `4.8.dev.mono.custom_build.035edfce7` | **判据**（与任务书逐字相符；`meta.json.engine.version_string` 同值） |
| `binary.sha256` | `08483088a4a2772841cd3b4c916b2d45b3cb6255656cf3951598a86fce7e9e6a` | **仅记录**（引擎构建非逐位可复现） |
| `size_bytes` / `mtime` | 194,216,960 / 2026-09-29 08:31:02 | 记录 |
| 监听者 | `listener.pid = 75204`、`matches_binary = true` | `meta.json.engine.listener` |
| 端点 | `GET /mcp → {"status":"ok","is_editor":true,"listening":true,"tools":154,…}`；`running_game_*` 在编辑器端点 **0 条** | `experiment/probe_editor_prerun.txt`（临场输出） |

### 9.2 摘要口径（写明 + 对既有基线自证）

**口径（本仓既往口径，逐字照任务书 §4）**：PowerShell 5.1（culture zh-CN）`Get-ChildItem -Recurse -Force -File`；
每文件取**仓根相对**路径（`\`→`/`、**转小写**）+ 字节长度 + 小写 SHA256；三列 `\t` 连接、`\n` 分行、无尾随换行；
行序 **`Sort-Object`（文化排序）**；整体 UTF-8 取 SHA256。脚本：`experiment/digest.ps1`（可复跑）。

**自证（三条已记录基线逐字命中）**：

```
runs/smoke-t6   135  c144ef3219e21dd322978e41a5531d53dee270619c026585505920f9277a9c03   <== 命中任务书自证值
runs/smoke-t7   115  6e4c1595753c2cdefb16e4d2e5f05242ca202c70c81a93e98ae2b9c92b520fb7   <== 命中 DR-66/67/68 记录
runs/smoke-t8   358  6d11b2c61ec507b5f02525ddc0e7f7adb08763cd2439a4b08788b7fe51bdf5a7   <== 命中 DR-68 记录（尾串 …bdf5a7）
```

**收工值**：`runs/smoke-t6` / `runs/smoke-t7` / `runs/smoke-t8` 与开工**逐字相同**（三棵均未被覆盖）；
**本轮新目录** `runs/smoke-t9` = **83 文件 / `541e2d81…36ca9d` / newest 2026-09-30 11:27:29**。

**工程树口径（我自己的口径，写明）**：递归、排除 `.godot/.import/.hoh/.git`、仓相对小写 POSIX 路径 + size + sha256、
`\t`/`\n` 连接、`sort()` 序数序、整体 sha256（`experiment/hashtree.py`）。本轮值：
`.workspace/mario` 工程树 **17 文件 / 18397 B / `5971b484…e463`**（轮前轮后同一值）；
运行时自己的内容寻址 `A0 = 1f3d20ed…fd8`（**口径不同，不是同一个实现**，不得互换引用）。
整目录摘要：`.workspace/mario` 85 文件 / `ece46412…2203`（含 `.hoh`/`.godot`，天然不稳定，仅作记录）。

### 9.3 禁区自证（开工 / 收工两点）

| 断言 | 证据 |
|---|---|
| 三条 `runs/**` 基线未被覆盖 | 摘要 + newest mtime 全部与记录逐字一致（§9.2） |
| `PRD-mario.md` 逐字节冻结 | sha256 `4c81c3a9995f0b3afdf01421a0c3be88573cceefc284ce9bafbfda141f0f5c3a`（开工/收工同值） |
| `DECISIONS.md` 未由我编辑 | 我全程只读；开工 `01b9f157…a18d`、收工 `cda4229b…a8d`（**变化来自调度者 `509ec0c`→`a9e050c` 的提交，不是我**） |
| `godot-mcp/**` 零改动 | 嵌套仓 `git -C godot-mcp/godot rev-parse HEAD = fc63af77…`、`status --porcelain -uall` **0 行**、`find … -newermt "2026-09-30 00:00" -type f` = **0**；外层 `git ls-files godot-mcp`=**6484**（真命中）而 `godot-mcp/godot`=**0**（外层空判） |
| 我未改任何被跟踪文件 | `git status --porcelain -uall` 中被跟踪文件零改动；我只新增报告 + 受控证据目录 |
| 无新依赖 / 未 stage / 未 push | `git diff --stat HEAD -- Cargo.toml Cargo.lock` 空；`origin/master = fe129a1…`（ahead=2，未 push） |
| `runs/**` 只写了我自己的新目录 | 本轮我对 `runs/**` 的写入**只**发生在 `runs/smoke-t9/**`（我的轮目录）。**没有**在 `runs/**` 其它任何路径建过临时文件（分析脚本与输出全在仓外 `%TEMP%\smoke-t9\` + 受控 `.spec/hof-rs/tasks/TASK-SMOKE-T9-evidence/`）。**附带说明**：attempt-A 被我删除重跑（属我自己的轮目录，非基线），删除前已把其证据搬出 `runs/**`（§13） |
| 密钥卫生 | 导出为 `HOH_MODEL_API_KEY`（**只报长度 51**）；`runs/smoke-t9` 命中 **0**、`.spec` 命中 **0**、`src/tests/config` 命中 **1（就是源文件 `config/model.secret.env` 本身）**；console 两份命中 **0**；唯一含明文副本的是仓外 `%TEMP%\smoke-t9\keyval.txt` |

---

## 10. 编辑器 pid 与进程清理（追加 5）

```
开工：127.0.0.1:9877 LISTENING pid 75204
      CMDLINE = F:\moonbit-hof-rs\godot-mcp\godot\bin\godot.windows.editor.x86_64.mono.exe
                -e --path .workspace/mario --mcp-port=9877
收工：Get-Process -Id 75204 → present=True（tasklist 仍列出）；9877 listener pid = 75204
      GET /mcp → {"status":"ok","is_editor":true,"listening":true,"tools":154,…}
⇒ 编辑器本体全程未被启动、未被杀、未被重启（开工时就在跑），收工后**仍存活**。
```

**孤儿游戏进程（任务书点名）**：

| 进程 | 来源 | 处置 | 结果 |
|---|---|---|---|
| **pid 77708**（parent 75204，start `11:06:10`，`--mcp-port=51911`） | **attempt-A 的 Developer** 起过游戏后轮失败，未收尾 ⇒ **孤儿** | `editor_stop_scene --role tester` | `{"message":"Playback stopped","stopped":true}`；pid 消失、51911 关闭（原文 `experiment/stop_orphan.txt`） |
| pid 106368（`--mcp-port=61183`） | 我的独立 E3 实验 #1 | 同一工具收尾 | 已停（`experiment/stop_after_probe.txt`） |
| pid 115160（`--mcp-port=62306`） | 我的独立 E3 实验 #2 | 同一工具收尾 | 已停（`experiment/stop_after_interact.txt`） |

**收工复核**：`tasklist | grep -i godot` 只有 **75204**；`netstat` 无任何游戏端口 LISTENING ⇒ **无孤儿残留**。

---

## 11. 两条风险旗的处置（逐条）

### 风险旗 1：不得把探针的 `GAME_INPUT_CHANNEL_OK` 当 E3 行为证据

- **处置：采信，且本轮它没有机会发生**——本轮**没有电池**，所以 `input_channel_probe` 与
  `GAME_INPUT_CHANNEL_OK` **一次都没出现**；我没有任何探针输出可用于（也不会用于）E3 判定。
- **代码层矛盾仍在（未被 DR-68 触碰）**：`src/adapter/godot.rs:1271-1272` 的文档说 `GAME_INPUT_CHANNEL_OK` 意味着
  "…input injection was accepted, **with a semantic reading arriving**"，而判定式
  `src/adapter/godot.rs:1422` 是 `match (pressed, axis_after.is_some() || game_process_reachable)` ——
  **可达性单独就能抬到 OK**（与 t8 §2.4 完全一致）。**遗留风险 R-2 未关闭**。
- 我的 E3 证据**只**引用 §3.2 的逐帧位置/状态读数（`running_game_get_node_property_samples` /
  `running_game_get_node_properties`），与探针无关。

### 风险旗 2：夹具刻意排除 `semantic_summary.json`，需要则停下上报

- **处置：我不需要它，也没有触碰守卫。** 我全程未读取/生成 `semantic_summary.json`；
  `git diff --stat HEAD -- src/adapter/tool_vocabulary.rs` **空**（零 diff）；夹具与守卫均未放宽。
- 我的 E3 证据全部来自**契约内**语义工具（`editor_play_scene` / `running_game_get_node_properties` /
  `running_game_get_node_property_samples` / `running_game_play_input_recording` /
  `running_game_set_node_property` / `running_game_get_scene_tree` / `running_game_run_test_scenario` /
  `editor_stop_scene`），无需该夹具。

---

## 12. 三个假绿陷阱的实测与正确读法

原始输出：`experiment/traps_output.txt`（脚本 `experiment/traps.sh`，可复跑）。

**① `git diff` 对不存在的 pathspec 不报错**

```
$ git diff --stat -- definitely/not/a/real/path
stdout+stderr=[]   exit=0
```

读法：**空输出 + 退出码 0** 与"没有变化"不可区分 ⇒ 用 `git diff` 证明"某路径未改"之前，
必须先证明该 pathspec **真的命中**（本轮用 `git ls-files godot-mcp | wc -l` = 6484 与
`git ls-files godot-mcp/godot | wc -l` = 0 作对照）。

**② `cmd` 里 `^` 是转义 ⇒ 所有 `rev^` 查询一律在 bash 做**

用 `fe129a1`（**新增** `.spec/hof-rs/tasks/TASK-DR68-ACCEPTANCE.md` 的提交）构造"两 revision 对同一路径存在性不同"：

```
bash : git cat-file -e fe129a1^:.spec/hof-rs/tasks/TASK-DR68-ACCEPTANCE.md  -> exit 128
bash : git cat-file -e fe129a1:.spec/hof-rs/tasks/TASK-DR68-ACCEPTANCE.md   -> exit 0
cmd  : git cat-file -e fe129a1^:<同一路径>                                   -> exit 0   ← 假绿
cmd  : git cat-file -e fe129a1:<同一路径>                                    -> exit 0
对照（两 revision 都有 DECISIONS.md）：bash HEAD^ = 0 / bash HEAD = 0 ⇒ 同号，不触发
对照（两 revision 都没有的路径）    ：bash = 128                        ⇒ 这个形状**不是**假绿
```

读法：真正有证据力的只有 **bash**；`cmd` 下的 `0` 不具备证据力（它实际问的是**另一个 revision**）。

**③ 外层仓不跟踪引擎树 ⇒ 引擎断言只能用嵌套仓或 mtime/摘要**

```
outer ls-files godot-mcp        = 6484   （真命中）
outer ls-files godot-mcp/godot  = 0      （空判）
git check-ignore -v godot-mcp/godot → .gitignore:33:godot-mcp/godot/
git diff --stat -- godot-mcp/godot/bin → 空 + exit 0（"什么都没说"）
nested: HEAD fc63af77… 、status --porcelain -uall = 0 行  ⇒ 引擎树未改（判据来源）
```

**③′（本轮附加）`runs/**` 同样被 gitignore**：`git check-ignore -v runs/smoke-t9/meta.json → .gitignore:12:runs/`
⇒ 外层 `git status/diff` 对本轮**全部证据**都是空判；"未变/已留证"只能靠**目录摘要**（§9.2）。

---

## 13. attempt-A（环境失败）的完整披露 + 诚实清单

1. **发生了什么**：attempt-A 于 `10:49:20` 启动，`11:07:13` 以 `hoh: harness failed for role developer iteration 1:
   llm-connector chat request failed`（**退出码 5**）结束，用时 **17 分 53 秒**。
2. **直接机制（实测）**：Developer 第 93 个 assistant 步发出
   `dir /s /b /a "%TEMP%" | findstr /i "hoh mcp endpoint"`，其工具结果 **15,570,803 字节**（msg 221），
   随后该结果被原样拼进下一次 chat 请求 ⇒ connector 失败。
   （脚本 `dump_traj.py` 的 `largest messages: [(221, 15570803), …]`；原文 `attempt1-aborted/developer_attempt1_summary.txt`。）
3. **attempt-A 没有污染产物**：它的工程树摘要与我开工前的值一致（`5971b484…e463`，17 文件/18397 B），
   所有写入同样落在 `.workspace/mario/.hoh/scratch/**`。它**留下了孤儿游戏进程 pid 77708**（§10，已清）。
4. **自修动作**：按"网络/通道类环境问题先自修"的纪律，我（a）确认端点健康（`/v1/chat/completions` 两次 PING 成功，
   0.2s 级、`model=deepseek-v4.1-flash`；原文在调度日志之外，见 §16 索引），（b）**重试一次**即 attempt-B。
   **重试即本轮正式轮**，不是"多跑几轮"。
5. **我搬出并保留了什么**：`attempt1-aborted/{console.txt,meta.json,exit_code,warnings.log,planner.attempt1.log,index.json,plan.md,developer_attempt1_summary.txt}`。
6. **我没有保留什么（如实）**：**attempt-A 的 16.4 MB `developer.attempt1.json` 全量轨迹未保留**
   （它随被我删除的 `runs/smoke-t9` 一起消失；我保留的是它的机器生成摘要 + 若干原始回包片段）。
   这是**我的处置取舍**（避免把 16 MB 塞进仓库），但它意味着 **attempt-A 的原始轨迹不可复核**。
   若调度者要求逐帧复核 attempt-A，这是**不可补**的损失。
7. **我删除了 `runs/smoke-t9` 一次并重建**（attempt-A 的轮目录，属**我自己的**轮目录，非任何基线）。
   删除前所有被引用证据已搬出 `runs/**`（第 5 条）。**对 `runs/**` 的其它任何路径我零写入。**
8. **我做过一次"改状态"的动作**：用 `editor_stop_scene` 停掉孤儿进程 77708（以及我自己实验起的 106368/115160）。
   编辑器本体 75204 未被触碰。这是本轮我唯一改变机器状态的工具动作。
9. **我没有改** `src/**`、`tests/**`、`godot-mcp/**`、`.workspace/mario/**` 的工程文件、`PRD-mario.md`、`DECISIONS.md`。

---

## 14. 遗留风险与未验证项（严格区分"实测"与"推断"）

**实测（本轮有证据）**

1. 本轮 E1 = not_met：Developer 零工程增量，契约闸门 `no_engineering_write` 触发，退出码 **2** 三方一致。
2. **角色 CLI 到不了游戏端点**：游戏在跑、端点已公布，新进程的 `hoh tools call running_game_*` 仍 `game_endpoint_unavailable`（EXIT=5）。
3. Developer 184 条命令里只有 4 条提到工程源文件（全读），零写入。
4. **四类 E3 行为在游戏进程内被语义工具观测到**：右移 `+3.6667 px/帧`、左移 `−3.6667 px/帧`、跳跃抛物线、金币 `0→1` 且 `Coin1` 消失、`state="won"`。
5. `input_axis` 恒 `null`，"assert input_axis" 直接失败 ⇒ 轴值断言真机不触发。
6. 门**本轮未被评估**；两处 gate 字段自洽；**无修复尝试**。
7. 失败路径三字段**如实为空**（无 `A_1`、无电池），与 t8 存根性质不同。
8. 三条 `runs/**` 基线未动；引擎树未改（嵌套仓 0 行 + 今日 0 文件）；编辑器 75204 存活；孤儿进程已清。
9. 三个假绿陷阱全部亲自复现并给出正确读法。
10. attempt-A 的因是**单条工具输出 15,570,803 字节**灌进 chat 请求导致 connector 失败（退出码 5）。

**推断（不得当作已证）**

1. **（≈0.8）** "Developer 把预算全投在绕道上"与 `plan.md` 把可观测结果钉在游戏内读数上、而 A0 已功能完整有关；
   我没有做提示词对照实验，故只是推断。
2. **（≈0.7）** F-T9-1 是**放大器而非唯一原因**：t8 的 Developer 撞同一错误 20 次仍写了代码；
   本轮 4 次却崩了 ⇒ 模型行为差异也是必要因子。
3. **（≈0.6）** F-T9-4（工具输出无上限）是**通用**的：任何角色只要 `dir /s /b` 到一个大目录树都可能重演退出码 5；
   我没有测试其它命令形状，故未证。
4. **（≈0.5）** F-T9-3（planner `RepeatedFormatError`）与 DR-68 ⑥ 只改了提示词文本有关；我无法证明
   "另一种提示词会让模型真的调用终止符"。
5. **DR-68 ①（Tester 证据形状自愈）的真机状态仍未知**：本轮 Tester 未运行 ⇒ 既未证实也未否证。

**未关闭（应回上游/回设计，本报告不修）**

1. **F-T9-1（major）**：角色 CLI 与游戏端点的**跨进程可达性**需要设计决定（持久化端点记录 / 或在 `hoh tools call` 里自动发现游戏端点 / 或明确禁止角色直连游戏并在提示词里说清）。
2. **F-T9-2 的组织问题**：Developer 的提示词缺少"**先改代码，观测交给 Tester/电池**"的分工约束，
   且在 A0 已完整时缺少"本轮改什么"的抓手。
3. **F-T9-4（major，可靠性）**：工具输出**无截断/无上限**，可单点掐死整轮（代价 17:53 + 退出码 5）。
4. **F-T9-5**：轮失败时**不收尾自己起的游戏进程**（孤儿 pid 77708）。
5. **F-T9-3**：planner/tester 的合法终止符只是**文本**，模型仍会发"无工具调用"回复。
6. **DR-68 R7（`evidence_diff`）**与**DR-68 R8（`GAME_INPUT_CHANNEL_OK` 代码/文档矛盾）**仍开放。
7. **E2..E6 的判据本轮完全没有被执行**——不是"未达标"，而是"没测到"；下一轮必须先让 Developer 产出增量，
   否则整条电池/QA 链永远不启动。

---

## 15. 诚实披露

1. **我跑了两次**（attempt-A 环境失败 + attempt-B 重试）。调度者的指示是"跑一轮"；我把 attempt-A 视为
   **环境自修前的失败**并保留了全部可得证据，把 attempt-B 作为正式轮。**两次都在报告里，未隐藏。**
2. **我删除了 `runs/smoke-t9` 一次并重建**（attempt-A 的目录，属我自己的轮目录）；删除前把被引用证据搬到了
   `.spec/hof-rs/tasks/TASK-SMOKE-T9-evidence/attempt1-aborted/**`。**attempt-A 的 16.4 MB 全量轨迹没有保留**
   （§13.6）——这是不可补的复核损失，我如实标注。
3. **我做了三次游戏进程的启动/停止**（孤儿清理 + 两个独立实验），每次都用契约内的 `editor_stop_scene` 收尾；
   收工时**无孤儿残留**。
4. **我没有声称 E1 或 E3 已 met**。E1 明确 not_met；E3 我给出的是"**不可判定（轮内无证据）** +
   **独立实验观测到全部四类行为**"，并明确说明证据形态不含截图、不达任务书的 E3 证据要求。
5. **我没有用 t8/t7 的 raw 冒充本轮证据**；所有轮内事实都指到 `runs/smoke-t9/**`，所有我的实验都标为"我的实验"。
6. **我没有改** `DECISIONS.md`（虽然环境自修按纪律应记入决策日志——我无权改它，故在本报告 §13 完整留证，
   请调度者决定是否补记 D269）。
7. **我对 `runs/**` 的写入只发生在 `runs/smoke-t9/**`**（连临时文件都没有在别处建过）；
   分析脚本与中间输出全在仓外 `%TEMP%\smoke-t9\`，被引用的关键证据另存于受控目录 `.spec/hof-rs/tasks/TASK-SMOKE-T9-evidence/`。
8. **attempt-A 的因（15.5 MB 工具输出）是我从被删轨迹的机器摘要里读到的，不是逐帧复核**（§13.6）。
9. **未 push**；我的提交只含本报告 + 受控证据目录。

---

## 16. 工件索引

| 类别 | 路径 |
|---|---|
| 本轮轮记录（**新目录**） | `runs/smoke-t9/**`（83 文件 `541e2d81…36ca9d`）：`exit_code`(`"2\n"`)、`meta.json`、`warnings.log`、`TOOLS.md`、`quarantine/.hoh.stale-1790737725/`、`versions/index.json`（**只有 A0**）、`iter-1/{plan.md,result.json,usage.json,logs/planner.attempt1.log,traj/{planner,developer.attempt1,developer.attempt2}.json,planner-view/}` |
| 本轮控制台原文 | `.spec/hof-rs/tasks/TASK-SMOKE-T9-evidence/round/console_retry.txt`；attempt-A 的 `…/attempt1-aborted/console.txt` |
| attempt-A（环境失败）证据 | `.spec/hof-rs/tasks/TASK-SMOKE-T9-evidence/attempt1-aborted/**`（console / meta / exit_code / warnings / planner log / index / plan / **developer 轨迹摘要**） |
| 本轮轮要点（仓外持久副本） | `…/TASK-SMOKE-T9-evidence/round/{result.json,meta.json,exit_code,warnings.log,usage.json,index.json,plan.md,planner.attempt1.log}` |
| 我的独立实验与检查 | `…/TASK-SMOKE-T9-evidence/experiment/**`：`e3_probe.py`/`e3_probe_output.txt`、`e3_interact.py`/`e3_interact_output.txt`、`axis_caveat.py`/`axis_caveat.txt`、`game_endpoint_probe.txt`、`play_scene.json`/`play_scene2.json`、`stop_orphan.txt`/`stop_after_probe.txt`/`stop_after_interact.txt`、`traps.sh`/`traps_output.txt`、`doctor.txt`、`prerun_state.txt`/`postrun_state.txt`、`dev1_commands.txt`/`dev1_project_write_scan.txt`、`traj_metrics.txt`、`digest.ps1`/`hashtree.py` |
| 离线对拍（补充，非真机） | `cargo test --offline --test launchable_gate` → **14/14 exit 0**；`--test schema_gate` → **6/6 exit 0**；`cargo fmt --check` → **exit 0** |
| 只读基线（未改动） | `runs/smoke-t6/**`（135 `c144ef32…`）、`runs/smoke-t7/**`（115 `6e4c1595…`）、`runs/smoke-t8/**`（358 `6d11b2c6…`） |
| 规范/需求 | `.spec/hof-rs/REQUIREMENTS.md`（E1..E6 在第 110-119 行）、`.spec/hof-rs/tasks/TASK-SMOKE-T8.md`（沿用任务书） |
| 上轮对照 | `.spec/hof-rs/tasks/TASK-SMOKE-T8-REPORT.md`、`TASK-SMOKE-T8-ACCEPTANCE.md`、`TASK-DR68-REPORT.md`、`TASK-DR68-ACCEPTANCE.md` |
| 相关决策 | `DECISIONS.md` **D265/D266/D267**（均已读） |

> 注：`runs/**` 与 `.workspace/**` 在 `.gitignore` 中（`.gitignore:12`、`:33`），故轮内证据留在工作区而不入库；
> 受控证据目录 `.spec/hof-rs/tasks/TASK-SMOKE-T9-evidence/**` 与本报告一起入库，以免重演 DR-68 验收 R-7
> 的"证据只活在会被清理的工作树里"。
