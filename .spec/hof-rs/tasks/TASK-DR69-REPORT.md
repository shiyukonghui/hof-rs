# TASK-DR69-REPORT — 打通"角色 CLI 够不到游戏端点"（选路 **A**，端点随 run 目录跨进程发布），把 E3 的证据形态做成轮内可达，并收掉工具输出上限/证据保全与携带项

- 任务书：`.spec/hof-rs/tasks/TASK-DR69.md`（**唯一任务来源**）+ 调度者本轮追加的两组事实（验收确认的代码级根因、`-p`、环境转储、采样滞后、以及"零增量 vs 无需改动"的区分要求）
- 落点：`F:\moonbit-hof-rs`（外层仓），报告人：**实现子代理（无上游对话上下文）**
- 开工 HEAD `b25fc4e`；收工 HEAD `03b35dd`（本批 7 个提交，**未 push**）
- 基线：`414 passed / 0 failed / 7 ignored`（开工自测）；门：`436 passed / 0 failed / 7 ignored`，`cargo fmt --check` exit 0
- 仓外工作目录：`C:\Users\wyl\AppData\Local\Temp\dr69\**`（脚本、备份、原始输出）；**`runs/**` 零写入**（连临时文件都没有）

---

## 0. 结论摘要

| 项 | 结果 | 一句话 |
|---|---|---|
| **①（一级）端点跨进程可达** | **选路 (A) 并实现** | 真因是**路由只活在 harness 进程内存里**，而角色的每条 `hoh tools call` 都是新进程。现在 run 在注册端点时把记录**发布**到 `<run dir>/game_endpoint.json`，并把它交给每个角色（`HOH_GAME_ROUTE`）；新进程 `hoh tools call running_game_*` **成功**（循环替身），无记录时**仍然硬失败**（DR-43 未放宽） |
| **② Developer 顺序** | **已改** | `developer.md` 明写"先改工程代码"、"轮内游戏观测不是你的前置（归 Tester/电池）"，并**禁止**自造客户端/裸探端口；旧定义 of done 第 4 条点名 `running_game_get_node_property_samples`（正是够不到的那条通道）已移除——这就是调度者点名的**矛盾**，本轮消除 |
| **③ 输出上限 + 证据保全** | **已做** | 单条工具结果上限 **64 KiB**，超限**截断 + 显式标注**并记入 `Output.extra`（进轨迹）；电池第二遍**先保存后清理**（`runs/<id>/quarantine/deterministic-pass-<n>.stale-<ts>`） |
| **④ E3 证据形态轮内可达** | **已做** | `input_replay` 每个窗口产出 **before/after 截图**（`.hoh/evidence/replay-<action>-{before,after}.png`，进候选视图）与 **`running_game_assert_node_state`** 位置断言（`position` + `neq` + 窗口首样本）——**不依赖** `input_axis` |
| **⑤ 携带项** | **逐条处置** | DEF-1 补覆盖（真实会红）；DR-67 **DEF-A 闭合**（失败定稿变成可执行函数 + 端到端测试）；DEF-C 修；DEF-D 复核（fmt 干净）；DEF-E 用命令生成清单；DEF-B 明确记录不静默改写；DR-65 抽共享助手并给出**可触发**的确定性反例 |
| **E1 / E3** | **不声称 met** | 本批**离线**，不跑真机轮。E3 的"证据形态可达"是**产物侧可离线钉住**的部分；真机是否 met 仍需一轮真机 |

---

## 1. 门与套件（真实尾部）

**强制重编**：`git ls-files '*.rs'` → **83 个已存在文件**逐个 `LastWriteTime = Get-Date`（**逐文件循环，非通配符**；`cargo test` 输出里 `Compiling hof-rs` 出现 **1** 次，证明真的重编）。

```
cargo fmt --check                      FMT_EXIT=0
cargo test --offline --no-fail-fast    EXIT=0
目标数 46；test result 行：436 passed / 0 failed / 7 ignored（`test result: FAILED` = 0 行）
```

对照开工自测（同一命令、同一口径）：**414 / 0 / 7**（714 行输出）。⇒ **+22 passed**，`ignored` **未增长**（7 → 7），无既有测试被删除或加 `#[ignore]`。

**两处"既有测试"的改动，逐条声明（都不是"改测试换绿"）**：

1. `tests/e1_increment.rs` `the_completion_definition_keeps_the_increment_and_drops_the_battery_ownership`：把断言
   `assert!(prompt.contains("running_game_get_node_property_samples"))` 改成
   **`assert!(!prompt.contains(...))`**。这是 DR-69 ② 明确要求的**需求变更**（旧断言要求的正是 Phase-1 诊断出的"结构性够不到的通道"，也是调度者点名的矛盾）。
   **不是放宽**：它把断言从"必须点名 X"改成"必须不点名 X"，并在 `tests/developer_contract.rs` 新增正向断言（顺序指令 + 禁止的绕道表述）。
2. `tests/evidence_battery.rs` `a_stale_png_does_not_suppress_the_frames_fallback`：
   原先断言**全电池范围**的 `running_game_capture_frames` 调用数 == 1；DR-69 ④ 让 `input_replay` 也拍帧（也会走 fallback），于是这个**全局计数**不再指向它要测的那一步。改为在**该步自己的 raw 记录**（`raw/screenshot.json`）里数，**要求仍是"恰好 1 次"**。
   ⇒ 范围收窄到被测对象，**断言没有变松**；若 `screenshot` 步真的多打一次 fallback，它照样红。
3. `tests/e1_increment.rs` `the_prompt_names_every_excluded_path_not_just_the_scratch_dir`：把排除集从 `{.hoh,.godot,.import}` 扩到 `{.hoh,.git,.godot,.import}`（DEF-C 的修法；**加强**，且让测试名与断言一致）。

---

## 2. ① 诊断 + 选路 + 测试钉法

### 2.1 诊断（文件:行 + 可复现命令）

**"端点为何只在内存里、谁发布它、为什么 `hoh tools call` 走另一条路、编辑器是否已知道端口"**：

| 事实 | 落点 |
|---|---|
| 游戏路由是**进程内**状态 | `src/tools/mod.rs:138` `game: Arc<Mutex<Option<GameRoute>>>`（新行号同义） |
| 没有注册就**硬失败**（禁止回落编辑器端点） | `src/tools/mod.rs` `client_for()` 的 `ToolScope::Game` 分支：`anyhow::bail!("game_endpoint_unavailable: … Falling back to the editor endpoint is not allowed (DR-43).")` |
| 谁发布：只有**运行时自己**，且在 `editor_play_scene` 回包里 | `src/runtime/run_loop.rs` 电池注册处 → `src/adapter/godot.rs` 的 `parse_game_endpoint` + `register_game_endpoint` |
| 每条 `hoh tools call` 都是**新进程**，其路由永远为空 | `src/cli_impl.rs:53` `let channel = bridge::channel_for(&config);`（每次新建）→ `src/tools/bridge.rs:227-234` `McpChannel::new(...)`（`game` 初值 `None`）→ 进程退出 |
| 编辑器**确实**知道端口 | `editor_play_scene` 的回包 `{"endpoint":"http://127.0.0.1:61183/mcp","mcp_port":61183,"pid":…,"playing":true}`（`smoke-t9` 冻结证据 `…/experiment/play_scene.json`）。**但编辑器端点不提供任何 `running_game_*` 工具**（同一轮实测：编辑器端点 `GET /mcp` → 154 个工具，`running_game_* = 0`） |

**可复现命令（本批新增的离线测试就是它的可执行版本）**：

```
# 红（改前）：游戏端点已在跑（这里是回环替身），角色进程仍拒绝
cargo test --offline --test game_route_across_processes -- a_role_shell_reaches
  → stderr: hoh: game_endpoint_unavailable: `running_game_get_scene_tree` runs in the game
    process and only the game endpoint serves it; no game endpoint is registered yet …
  → left: Some(5)  right: Some(0)      （EXIT=101）

# 绿（改后）：同一断言通过，且游戏替身收到调用、编辑器替身没收到任何 running_game_*
cargo test --offline --test game_route_across_processes
  → 3 passed; 0 failed
```

### 2.2 选路：**选 (A)**，理由与 (B) 的取舍

**选 (A)：让游戏路由可跨进程解析。** 因为它是**根因**而非症状：

- (B)（在流程上禁止"轮内游戏观测"，归 Tester/电池）**只堵住一种表现**。同一个结构缺陷在 t8 让 Developer 撞了 20 次却仍写了代码，在 t9 让它把 175 次调用烧光——**它是放大器，不是唯一原因**（TASK-SMOKE-T9 §2.2 实测）。若只选 (B)，任何**未来**想把 `running_game_*` 用于轮内自检的角色/计划都会被同一条硬 bail 挡住，缺陷只是被文档掩盖。
- (B) 还有一处**内在矛盾**：`developer.md` 的定义 of done 当时正要求 Developer 自己用 `running_game_get_node_property_samples` 证明可观测性。选 (B) 必须同时接受"角色不许直连游戏"这条**设计裁决**，而那会与已冻结的编辑器工具面（`editor_simulate_input_action` 等）形成新的边界争论。
- (A) 的**次选**——经编辑器中转——**不可行**：`running_game_*` 在编辑器端点上是 **0 条**（实测），要中转就得改引擎模块 `godot-mcp/**`，而本批**禁止**改它。故 (A) 取"run 发布、角色进程采纳"这一形态。

**(A) 的具体形态（本批实现）**：

1. `src/tools/endpoint.rs`：`GAME_ROUTE_FILE = "game_endpoint.json"`、`GAME_ROUTE_ENV = "HOH_GAME_ROUTE"`、`game_route_path`、`publish_game_route`（临时文件 + rename，原子）、`load_game_route`（读不出/坏 JSON ⇒ `None`，**绝不猜端口**）、`withdraw_game_route`。
2. `src/tools/mod.rs`：新增 `ToolChannel::use_game_route_file(path)`（默认空实现，单端点替身不受影响）；`McpChannel` 存该路径，`register_game_endpoint` **先发布再返回**，`clear_game_endpoint` **撤下文件**（`editor_stop_scene` 之后不可能再解析到一个死端口）。
3. `src/tools/bridge.rs`：`adopt_published_game_route(channel, path)`（`None` 读环境变量；参数化以便测试）。
4. `src/cli_impl.rs`：`tools call` 在调用前采纳已发布的 route。
5. `src/runtime/invoke.rs`：`role_env` 给每个角色 `HOH_GAME_ROUTE=<绝对路径>`；`src/runtime/shell.rs` 把它纳入 `COMMAND_VARS`（模板写 `{{HOH_GAME_ROUTE}}`，按平台渲染）。
6. `src/runtime/run_loop.rs`：`run` 一开始就把 `<run dir>/game_endpoint.json` 绑给通道。

**为什么不是"任意文件都能被信任"**：route 文件落在 **run 目录**（`runs/<id>/game_endpoint.json`）——不在工程树、不在任何角色视图、不在 Developer 的可写目录；只有运行时写它；`editor_stop_scene` 撤它。**没有文件 ⇒ 行为与今天完全一致**（硬 bail、EXIT≠0）。

### 2.3 该路怎么被测试钉住（3 个断言，其中 1 个是"红过"的）

`tests/game_route_across_processes.rs`：

| 测试 | 断言 | 红过吗 |
|---|---|---|
| `a_role_shell_reaches_the_published_game_endpoint_across_processes` | 用**真实二进制**、真实子进程、`HOH_GAME_ROUTE` + `-c tools.endpoint=<编辑器替身>`；要求 **exit 0**、游戏替身**收到** `running_game_get_scene_tree`、编辑器替身**一个 `running_game_*` 都没收到**、stdout 不含 `game_endpoint_unavailable` | **是**（改前 `Some(5)` vs `Some(0)`） |
| `without_a_published_route_the_game_call_still_fails_loudly` | 没有 route 时 exit≠0 + 文本含 `game_endpoint_unavailable` + 编辑器替身**零请求**（DR-43 未放宽） | 否（改前也绿——它是**反向守卫**） |
| `registering_publishes_the_route_and_stopping_withdraws_it` | 运行时路径：注册 ⇒ 文件出现且 JSON 与记录逐字段相等；**另一个通道**（= 另一个进程）能采纳；`clear_game_endpoint` 后文件消失且采纳为空 | 否**但承重**：植入 `P1`（删掉发布调用）让它**红** |

---

## 3. ②③④ 的落点与红→绿；⑤ 每项处置

### 3.1 ② Developer 顺序（`src/prompts/developer.md`）

**红**（`cargo test --offline --test developer_contract -- the_developer_changes_the_code_first`）：

```
panicked at tests\developer_contract.rs:72:9:
developer.md must tell the Developer its order of work; missing `change the project code first`
```

**改**：`[policy]` 加三条（"**Change the project code first.**" 的顺序规定；"**Observing the running game in this round is NOT your prerequisite**"；禁止自造 MCP 客户端/手写 JSON-RPC/裸探端口）；`[separation of duties]` 加"**Your order of work**"；`[self-test]` 把可自证通道限定为**编辑器侧**（`editor_get_errors`/`editor_play_scene`/`editor_simulate_input_action`/`editor_get_collision_info`）；`[definition-of-done]` 第 4 条改成**结构性**要求（命名节点 + 会变的属性），删掉对游戏端点的自证指令；`.git/**` 补进两处排除集说明（DEF-C）。

**绿**：`developer_contract` 5 passed；`e1_increment` 13→14 passed；`prompt_shell_contract`/`role_shell_contract` 仍绿（`{{HOH_GAME_ROUTE}}` 走既有渲染管线）。

**测试**：`the_developer_changes_the_code_first_and_leaves_observation_to_the_tester` —— 正向断言 4 个 needle，**反向**断言不得出现 `running_game_get_node_property_samples`、`python -c`、`invoke-restmethod`、`netstat`、`curl `、`raw http`、`build/write your own mcp client`。

### 3.2 ③ 工具输出上限 + 被中止尝试的证据保全

**红（本项的红是"能力不存在"的编译级红，明确标注）**：

```
cargo test --offline --test tool_output_ceiling
error[E0432]: unresolved import `hof_rs::harness::cap`
error: could not compile `hof-rs` (test "tool_output_ceiling") due to 1 previous error   EXIT=101
```

（**诚实标注**：这一步是"接口还不存在"，不是运行时断言失败。该项的**运行时**非空洞性由植入 `P2` 提供：把上限短路后 `an_oversized_tool_result_is_truncated_and_annotated` 立刻 exit 101。）

**实现**：`src/harness/cap.rs`（`DEFAULT_MAX_TOOL_OUTPUT_BYTES = 64 KiB`、`TRUNCATION_MARKER`、`cap_tool_output`（保留**头部**、按 UTF-8 边界切、附带 `N of M bytes` 与"剩余已丢弃"的说明）、`CappedEnvironment`（包装任意 `Environment`，超限时改写 `output.output` 并把 `hoh_output_truncated/…_original_bytes/…_limit_bytes` 写进 `Output::extra` ⇒ 随轨迹落盘））；`src/harness/mini.rs` 用它包住 mini 的 `LocalEnvironment`；`AgentLimits::max_tool_output_bytes` 配置化（默认 64 KiB）。

**测试**（consuming 15,570,803 字节——**真机事故的字节数**）：截断、标注、`original_bytes` 精确、carried 文本 bounded、**不含**超限的连续字节串；再加一条**真环境**测试（`LocalEnvironment` + `type big.txt` 生成 2 MiB，断言被截断且 `extra` 标记）——证明改的是"harness 真正用的那个环境边界"。

**证据保全**：`src/runtime/run_loop.rs` 新增 `preserve_then_clear(dir, preserve_root, label)`（有内容 ⇒ **rename 到** `<run dir>/quarantine/<label>.stale-<ts>`；rename 失败才退化为递归复制后删除；空/不存在 ⇒ 直接清掉且**不创建** quarantine），`run_battery_pass` 在 `create_dir_all` **之前**调用它，并写一条 `DR-69: battery pass N replaced pass N-1's evidence; those bytes were preserved at …` 的 warning。
**测试**：`tests/aborted_attempt_evidence.rs`（单元：内容逐字节存活、目录被清、空/缺失不产生 quarantine）+ `tests/evidence_battery.rs::an_aborted_battery_pass_is_preserved_before_its_directory_is_cleared`（**端到端**：一个真的花了那一次修复重试的轮次，断言 `quarantine/deterministic-pass-1.stale-*` 恰好一个、`raw/play_scene_ready.json`+`raw/input_replay.json`+`mcp-errors.jsonl` 都在、且候选视图里仍是**第二遍**的电池）。

### 3.3 ④ E3 证据形态轮内可达（`src/adapter/godot.rs`）

**红**（`the_input_replay_produces_before_and_after_frames_and_a_positional_assertion`）：

```
the replay of `move_right` must capture a BEFORE frame: ["editor_side_injection",
"move_right:create_input_recording", …, "move_left:EDITOR_SIDE_INJECTION:release"]
   （完全没有 replay_frame_*，也没有 assert 调用）
```

**实现**：`BatterySession::capture_replay_frame(label, phase, calls)`（沿用 DR-49：**不带** `save_path`、先失效旧文件、内联 base64 落盘、`running_game_capture_frames` 兜底）+ `assert_replay_moved(label, expected, calls)`（`running_game_assert_node_state`，`node_path=Player`、`property=position`、`operator=neq`）。每个窗口：**注入前**拍 before → 采样 → 判断本轴位移（DR-68 ⑧ 未回退）→ 拍 after → 位置断言。三种诚实失败：`REPLAY_FRAME_MISSING`、`POSITION_UNCHANGED`、`POSITION_ASSERTION_UNAVAILABLE`（结构性失败与"没变"分开）。
**期望值 = 该窗口的 `before_position`（第一个样本）**，不是注入前读数 ⇒ **不受 ~14 帧采样滞后影响**（见 §6-校准）。图片落在 `.hoh/evidence/replay-<action>-{before,after}.png` ⇒ 由 DR-36 的候选复制进入冻结视图。EVIDENCE_PLAYBOOK 的 `input_replay` 行同步更新。

**绿**：`evidence_battery` 44 passed（含新 2 条）；新增断言逐条核对：三窗口各有 before/after label、PNG 与工具产出**逐字节相等**、**候选视图里也在**、断言参数是引擎自己的名字、`passed:true`、每次截图都不带 `save_path`；死轴反例（`MovementMode::None`）里位置断言 `passed:false` ≥3 且观测点名失败。

### 3.4 ⑤ 每项处置

| 编号 | 处置 | 证据 |
|---|---|---|
| **DEF-1**（`INPUT_AXIS_NOT_CHANGED` 无覆盖） | **补覆盖** | 新增 `AxisMode::WrongSign` 替身（引擎回报与所持方向相反的读数）+ `an_axis_reading_that_contradicts_the_held_direction_is_red`：**位移本身是对的**（断言不含 `INPUT_HAD_NO_EFFECT`），红只能来自轴交叉校验。植入 `P3` 让它红 |
| **DR-67 DEF-A**（`cli_impl.rs` 那 6 行调用点无可执行覆盖） | **结构性强制的可执行化** | 新增 `cli_impl::run_round_and_finalize(orchestrator, spec, run_id, run_dir)`，失败定稿分支**搬进它**；`run` 只调它。`tests/e1_increment.rs::the_real_round_path_persists_a_failing_rounds_verdict` 用**真实的失败轮次**驱动它，断言 `runs/run-1/exit_code == "2"`、`meta.json.exit_code == 2`、`meta.artifact_gate.applicable == false`。植入 `P4`（退回 `?` 形态）让它红 |
| **DR-67 DEF-B**（披露自述失准、附录标题被静默删除） | **明确记录，不静默改写** | 历史报告是证据。本报告 §7 逐条列出：`TASK-DR67-REPORT.md:96-99/:467` 对 diff 的描述与事实不符（第 8 条从未被删，被删的是 DR-66 报告的附录标题）、`TASK-DR66-REPORT.md:574`"一个字未改"不成立、DEF-4 两处旧误未标注。**建议下一批**（或调度者）在 DR-66/DR-67 报告里加标注块并恢复/标注附录标题——本批不动他人报告 |
| **DR-67 DEF-C**（`.git` 未点名、测试名言过其实） | **已修** | `developer.md` 两处排除集加 `.git/**`；`the_prompt_names_every_excluded_path_not_just_the_scratch_dir` 的两条循环都扩到 4 个（加强）；该测试名现在与断言一致 |
| **DR-67 DEF-D**（`run_loop.rs` 格式损坏） | **已由 DR-68 全树修正，本批复核** | `cargo fmt --check` exit 0（改前后各一次） |
| **DR-67 DEF-E**（受控清单须命令生成） | **用命令生成** | `git diff --name-status origin/master..HEAD`（29 项）与 `Get-ChildItem -Recurse %TEMP%\dr69`（25 项）**都来自命令输出**，逐字贴在 §5，不是手写 |
| **DR-65**（`dual_endpoint.rs`/`endpoint_request_count.rs` 同形非阻塞 accept 竞态） | **抽共享助手 + 给出可触发反例** | `tests/common/mod.rs::accept_blocking`（accept 后**显式** `set_nonblocking(false)`）成为**三个**替身（含已修的 `endpoint_liveness.rs`）唯一入口；新增 `tests/loopback_accept_blocking.rs`：客户端**先连接、延迟 250 ms 再写**，服务端阻塞读必须仍能应答。**实测可触发**（见 §4 的 `C1`：去掉 `set_nonblocking(false)` 后该测试 exit 101）⇒ 本轮**不是**"未实测的纵深防御" |
| **调度者：矛盾（定义 of done 指向够不到的通道）** | **已消除** | 见 3.1：第 4 条改为结构性要求；同时 (A) 让该通道**真的可达**（两件事都做，不互相掩盖） |
| **调度者：零增量 vs"无需改动"** | **区分了一半，另一半明确说不能区分** | 闸门现在**测**两个事实并在 `warnings.log` 里写明：`Zero-increment shape: <N> file(s) under .hoh/scratch at the gate, so <the Developer produced no write at all / the Developer wrote, but every write went to an excluded path>`，**并显式写**"This gate measures the artifact tree, so it cannot distinguish `the project needed no change` from `the Developer changed nothing`"。⇒ "它在别处写过吗"可测；"本来该不该改"**运行时没有 ground truth**，故声明不可区分，并说明 E1 的判据本身是针对**待开发工程**的 |
| **调度者：`.workspace/mario` 里的 `-p` 目录** | **未删除（硬约束冲突，如实上报）**；**hygiene 已扩到目录** | 任务书 §3 明写 **不改 `.workspace/mario/**`**，调度者要求删除它 —— **两者冲突，我服从任务书（"本文件是你的唯一任务来源"）并在本报告点名**。可做的一半已做：`hygiene::suspicious_directories`（`-p`/前导 `-`、前导 `_`、`tmp_*`、`*.bak/*.tmp`、含 `%VAR%`/`$VAR` 的名）写进 `result.json.artifact_hygiene.suspicious_directories`。单元测试自证**文件扫描对目录是盲的**（`suspicious_files(root).is_empty()` 而目录扫描命中 3 个）。建议：由拥有该工作区的批次清理 `-p`（它是空目录，删除不影响 `A_0` 内容哈希） |
| **调度者：环境转储入库** | **已处置** | 生产侧：`secrets::redact_secret_assignments`（把对已知密钥变量的**赋值**整体替换掉，并**不再**要求 `known_secrets` 非空才扫描）+ 单元测试；证据侧：`.spec/hof-rs/tasks/TASK-SMOKE-T9-evidence/experiment/dev1_commands.txt` 里那 53 字节的赋值被替换为 `<redacted-key-path-by-DR-69>`，并新增 `…/REDACTION.md` 说明改了什么、为什么、以及**未动**的两处披露（`TASK-SMOKE-T9-ACCEPTANCE/REPORT.md` 仍点名 key 文件路径——那是缺陷披露本身，改它等于销毁审计痕迹；由调度者裁量） |
| **调度者：采样滞后 ~14 帧校准** | **记录并规避** | 见 §6"校准"：本批**没有**引入任何"按总位移"的断言；位置断言的期望值取窗口**首样本**，因此与滞后无关；电池观测文本仍按窗口口径给出逐帧速率 |

---

## 4. 非空洞性：9 处**生产代码**植入 + 1 处**测试载体**植入

驱动脚本：`%TEMP%\dr69\plants.py`（可复跑）；原始输出：`%TEMP%\dr69\plants-output.txt`。每处都是**改一处 → 跑它对应的测试 → 还原**，还原的四重判据：`git status --porcelain` 空 + `git diff --stat` 空 + `git hash-object == HEAD:<path>` + **`cmp` 对仓外备份 `BYTE-IDENTICAL`**（**`cmp` 是强制项**：本仓 `core.autocrlf=true`，行尾改写对 git 不可见）。

```
=== P1-route-not-published: cargo exit=101 -> RED      (the endpoint is never published)
    restore: status='' diff='' hash=a6ad52a029==a6ad52a029 cmp=True(out='BYTE-IDENTICAL') -> OK
=== P2-no-output-ceiling: cargo exit=101 -> RED        (the 64 KiB ceiling is short-circuited)
    restore: status='' diff='' hash=7409c96425==7409c96425 cmp=True(out='BYTE-IDENTICAL') -> OK
=== P3-axis-branch-removed: cargo exit=101 -> RED      (the INPUT_AXIS_NOT_CHANGED branch is dead)
    restore: status='' diff='' hash=8e0968454e==8e0968454e cmp=True(out='BYTE-IDENTICAL') -> OK
=== P4-caller-glue-off: cargo exit=101 -> RED          (the failure finalisation is skipped = DR-67's caller-glue-off)
    restore: status='' diff='' hash=c8f5381fb9==c8f5381fb9 cmp=True(out='BYTE-IDENTICAL') -> OK
=== P5-replay-before-frame-removed: cargo exit=101 -> RED  (no before frame in the replay)
    restore: status='' diff='' hash=8e0968454e==8e0968454e cmp=True(out='BYTE-IDENTICAL') -> OK
=== P6-aborted-pass-not-preserved: cargo exit=101 -> RED   (the aborted pass is destroyed again)
    restore: status='' diff='' hash=d76252b600==d76252b600 cmp=True(out='BYTE-IDENTICAL') -> OK
=== P7-secret-assignment-kept: cargo exit=101 -> RED   (the assignment redactor is switched off)
    restore: status='' diff='' hash=b47845e4aa==b47845e4aa cmp=True(out='BYTE-IDENTICAL') -> OK
=== P8-directory-hygiene-blind: cargo exit=101 -> RED   (directory hygiene returns nothing)
    restore: status='' diff='' hash=ca7e6c7077==ca7e6c7077 cmp=True(out='BYTE-IDENTICAL') -> OK
=== P9-developer-order-removed: cargo exit=101 -> RED   (both ordering sentences replaced)
    restore: status='' diff='' hash=0e0025a406==0e0025a406 cmp=True(out='BYTE-IDENTICAL') -> OK

SUMMARY                     all_restored=True   all_red=True
```

**测试载体植入（显式声明，参 D253）**：`C1-common-accept-nonblocking` —— 改的是 `tests/common/mod.rs`（**测试代码**，不是生产代码），去掉 `accept_blocking` 里的 `set_nonblocking(false)`：

```
=== C1-common-accept-nonblocking: cargo exit=101 -> RED
    thread 'a_delayed_request_is_still_answered' panicked at tests\loopback_accept_blocking.rs:163:10
    status: ''   diff: ''   hash: 1908c2e5af… == 1908c2e5af…   cmp: 'BYTE-IDENTICAL'
```

⇒ DR-65 的形状**可被确定性触发**（这正是 DR-65 要求的"使旧形状红、新形状绿的确定性触发"）。

---

## 5. 禁区自查（真实输出）

### 5.1 `runs/**` 逐字未变（同一脚本、同一口径：PowerShell 5.1 `Get-ChildItem -Recurse -Force -File`；仓根相对小写 POSIX 路径 + 字节数 + 小写 SHA256，`\t` 连接、`\n` 分行、**文化排序**、整体 UTF-8 sha256）

```
runs/smoke-t6  135 files  repo-relative c144ef3219e21dd322978e41a5531d53dee270619c026585505920f9277a9c03  newest 2026-09-29 02:32:01
runs/smoke-t7  115 files  repo-relative 6e4c1595753c2cdefb16e4d2e5f05242ca202c70c81a93e98ae2b9c92b520fb7  newest 2026-09-29 14:41:14
runs/smoke-t8  358 files  repo-relative 6d11b2c61ec507b5f02525ddc0e7f7adb08763cd2439a4b08788b7fe51bdf5a7  newest 2026-09-30 07:58:28
runs/smoke-t9   83 files  repo-relative 541e2d814e563ba667c95bde49765d05e44cf11aa5ab90b2f44931f30136ca9d  newest 2026-09-30 11:27:29
```

**四条与记录逐字相同**（t6 命中任务书自证值；t7/t8/t9 命中 DR-66/67/68/69 记录）。**写-删检查**：`runs/smoke-t6|t7|t8` 下晚于 `2026-09-30 12:00` 的文件/目录数 = **0 / 0 / 0**（目录 mtime 对"写过再删"最敏感）。
**我对 `runs/**` 的写入 = 0**：本批**所有**分析产物都在仓外 `%TEMP%\dr69\`；连一个临时文件都没有在 `runs/**` 建过。

### 5.2 其余禁区

```
PRD-mario.md sha256                     4c81c3a9995f0b3afdf01421a0c3be88573cceefc284ce9bafbfda141f0f5c3a   （未变）
DECISIONS.md                            git status/diff 空 —— 我全程未编辑
godot-mcp/**（嵌套仓）                   HEAD fc63af77c33368c4a1bb839c95d19750554f63a3；status --porcelain -uall = 0 行
pathspec 真命中对照                      外层 `git ls-files godot-mcp` = 6484（真命中） vs `git ls-files godot-mcp/godot` = 0（空判）
无新依赖                                 `git diff --stat HEAD -- Cargo.toml Cargo.lock` 空
未 push                                  `origin/master = 9aebbe15f13508d1ee5063505b2827ee59cc041a`，`rev-list --count origin/master..HEAD` = 7（本批 7 个提交）
仓内无临时物                              `git status --porcelain -uall` 空（除已提交内容）
`.workspace/mario` 未改                   工程文件最新 mtime 仍是 t8 的 `player.gd 07:19:25`；`-p` 目录仍在（**故意不删**，见 §3.4）
离线                                     未启动 Godot、未碰任何外部端口（测试内回环替身不计）、未联网、未调模型端点、未跑真机轮
```

### 5.3 三个假绿陷阱（本批亲自复现）

```
① git diff 对不存在的 pathspec 不报错
   $ bash -c 'git diff --stat -- definitely/not/a/real/path; echo exit=$?'   →  exit=0（输出空）
   读法：空 + 0 与"没变化"不可区分 ⇒ 必须先证明 pathspec 真命中（上面 6484 vs 0 的对照就是那一步）

② cmd 里 `^` 是转义 ⇒ 所有 `rev^` 查询一律在 bash 做
   bash : git cat-file -e fe129a1^:.spec/hof-rs/tasks/TASK-DR68-ACCEPTANCE.md → fatal …, bash-exit=128
   bash : git cat-file -e fe129a1:.spec/hof-rs/tasks/TASK-DR68-ACCEPTANCE.md  → bash-exit=0
   bash : git cat-file -e fe129a1^:definitely/not/here                        → bash-exit=128
   cmd  : fe129a1^:<同一路径> → cmd-exit=0 ；fe129a1^:definitely/not/here → cmd-exit=0 ；fe129a1:<同一路径> → 0
   读法：cmd 下三个都返回 0 ⇒ 该返回值**不携带信息**（它实际问的是另一个 revision）；有证据力的只有 bash

③ 外层仓不跟踪引擎树/工作区/轮目录 ⇒ 这些断言只能靠嵌套仓或摘要
   $ git check-ignore -v runs/smoke-t9/meta.json            → .gitignore:12:runs/
   $ git check-ignore -v .workspace/mario/project.godot     → .gitignore:11:.workspace/
   $ git ls-files godot-mcp = 6484（真命中）；git ls-files godot-mcp/godot = 0（空判）
```

### 5.4 受控清单（DEF-E：**命令生成**）

```
$ git diff --name-status origin/master..HEAD
A  .spec/hof-rs/tasks/TASK-SMOKE-T9-evidence/REDACTION.md
M  .spec/hof-rs/tasks/TASK-SMOKE-T9-evidence/experiment/dev1_commands.txt
M  src/adapter/godot.rs        M  src/cli_impl.rs        M  src/config.rs
A  src/harness/cap.rs          M  src/harness/mini.rs    M  src/harness/mod.rs
M  src/model.rs                M  src/prompts/developer.md
M  src/runtime/hygiene.rs      M  src/runtime/invoke.rs  M  src/runtime/run_loop.rs
M  src/runtime/secrets.rs      M  src/runtime/shell.rs
M  src/tools/bridge.rs         M  src/tools/endpoint.rs  M  src/tools/mod.rs
A  tests/aborted_attempt_evidence.rs   M  tests/common/mod.rs
M  tests/developer_contract.rs M  tests/dual_endpoint.rs  M  tests/e1_increment.rs
M  tests/endpoint_liveness.rs  M  tests/endpoint_request_count.rs  M  tests/evidence_battery.rs
A  tests/game_route_across_processes.rs  A  tests/loopback_accept_blocking.rs  A  tests/tool_output_ceiling.rs
（29 项；本批 7 个提交，均英文信息带 (DR-69)）

$ Get-ChildItem -Recurse -File "$env:TEMP\dr69"   → 25 项（apply4.py, apply5.py, apply5b.py, apply5c.py,
  apply5d.py, carrier.py, plants.py, probe4.py, redact_evidence.py, carrier-output.txt, plants-output.txt,
  suite-baseline.txt, suite-final.txt, battery.corrupt.rs, godot.corrupt.rs, bak\{C1,P1..P9}.bak）
  ⇒ 全部在仓外；**仓内零临时物**
```

---

## 6. 遗留风险与未验证项（严格区分实测 / 推断）

**实测（本批有证据）**

1. 改前：真实二进制、新进程、`HOH_GAME_ROUTE` 已就位且游戏替身在跑，`hoh tools call running_game_get_scene_tree` 仍 **exit 5 + `game_endpoint_unavailable`**（`left: Some(5) right: Some(0)`）。
2. 改后：同一路径 **exit 0**，游戏替身收到调用，编辑器替身**零** `running_game_*`；**无 route 时仍硬失败**（DR-43 保持）。
3. 工具结果上限 64 KiB：15,570,803 字节输入被截断 + 标注 + `original_bytes` 精确；**真** `LocalEnvironment` 的 2 MiB 输出同样被截断；未超限结果逐字节不变。
4. 被中止的电池 pass **先保存后清理**：`runs/run-1/quarantine/deterministic-pass-1.stale-*` 里的 `raw/*.json` 与 `mcp-errors.jsonl` 逐字节存活，候选视图仍是第二遍。
5. `input_replay` 产出 6+2 张 before/after PNG（与工具产出逐字节相等、且在候选视图内）与每窗口一次的 `running_game_assert_node_state(position:neq)`；死轴时断言 `passed:false`。
6. 9 处生产植入全部使**对应**测试转红，且 9/9 逐字节还原（四重判据）；1 处测试载体植入使 DR-65 触发测试转红。
7. 门：436/0/7、`cargo fmt --check` exit 0、强制重编（`Compiling hof-rs` × 1）。
8. 四条 `runs/**` 基线逐字未变；PRD sha 未变；嵌套引擎未变（0 行）；无新依赖；未 push；仓内无临时物。

**推断（不得当作已测）**

1. **（≈0.85）** 真机上的 `running_game_*` 会经由发布的路由成功：本批只在**回环替身**上证明了"跨进程解析 + 真的把请求送到游戏端点"这一段；真机还多一层（引擎的 JSON-RPC 与 DR-29 关联 id），未验。
2. **（≈0.7）** Developer 的零增量**不会**再因"够不到端点"而复现：提示词与通道两条都改了，但"模型会不会仍然选择绕道"只能由真机轮回答（t8/t9 表明同一障碍下模型反应可以不同）。
3. **（≈0.6）** `position` + `neq` 在真机的 `running_game_assert_node_state` 上会被接受：参数字名与类型已按引擎源码（`running_game_assertion.cpp:95-162`）核对，但**未**用真引擎跑过；`assertion_expectation_for` 对 `{"x","y"}` 字典 → `Vector2` 的归一化只在源码注释里读到。
4. **（≈0.5）** 64 KiB 足以容纳一切**合法**载荷：真机没有出现过被截断的合法工具结果，但也没有系统性统计。
5. **（≈0.4）** "scratch 文件数"确实能区分两种零增量形状：离线夹具里成立（写了 `.hoh/scratch/experiment.py`），真机上是否总有可观测的 scratch 写入未验。

**未验证 / 未闭合（明确留给下一批）**

1. **道路 (A) 的真机意义**：只有真机轮才能回答"游戏在跑时角色的 `hoh tools call running_game_*` 成功"——本批给出的是**结构级**等价物。
2. **E3 的 met**：本批只让**证据形态**轮内可达；是否 met 必须由真机轮判定。**本报告不声称 E1/E3 met。**
3. **DR-68 ①（Tester 证据形状自愈）从未在真机被走到**（`smoke-t9` 死在冻结之前）——调度者要求保持这一条为未验证项，本轮**保持**。
4. **`-p` 目录仍在 `.workspace/mario`**：需由拥有该工作区的批次清理；hygiene 现在会**报告**它（`artifact_hygiene.suspicious_directories`），但运行时不删任何东西。
5. **DR-67 DEF-B**：DR-66/DR-67 报告的自述失准与丢失的附录标题未修（只记录，§3.4）。
6. **两处披露仍含 key 文件路径**（`TASK-SMOKE-T9-{REPORT,ACCEPTANCE}.md`）：未改，等调度者裁量（见 `REDACTION.md`）。
7. **`runs/smoke-t9/**` 里的同类环境转储未清**：它是只读证据，本批不许动。
8. **E2/E4/E5/E6 本批完全没被触及**（无真机轮）。

**校准记录（采样滞后，调度者点名）**

`TASK-SMOKE-T9-ACCEPTANCE.md` §3.3 测出注入后前 ~14 帧（≈51 px）不在采样窗内。本批的**承重**断言因此是：① 逐帧**速率**（DR-68 ⑧ 的按轴位移，未回退），② `running_game_assert_node_state(position:neq <窗口首样本>)` —— 期望值与观测值取自**同一采样窗**，滞后被消掉。**本批没有引入任何"按总位移"的断言**；若下一批要用总量，必须先接受或校正该偏移。

**诚实补充：本批没有度量、也没有主张**"`hoh tools call running_game_*` 在**真机**上成功"。回到 §6 推断 1。

---

## 7. 诚实披露

1. **我犯过一次真实事故并已修复**：我用 PowerShell 5.1 的 `Get-Content -Raw` + `Set-Content` 去替换 `src/adapter/godot.rs` 与 `tests/evidence_battery.rs` 里的两条字符串，**把两个文件里全部非 ASCII 字符（破折号、圈码）打成了 `?`**（`—` 计数从 74/61 变成 0/0）。我立刻 `git checkout HEAD --` 还原，改用一个 **UTF-8 直写**的 Python 脚本重放全部改动，并在重放后**逐文件核对非 ASCII 计数**（`godot.rs` `—`=74、`⑧`=3；`battery.rs` `—`=61、`⑧`=4，与 HEAD 相同）。损坏的中间副本留在仓外的 `%TEMP%\dr69\{godot,battery}.corrupt.rs` 供核对。**教训**：本仓的文本文件不能用 PS 5.1 的文本重写路径处理。
2. **③ 的"红"是编译级**（`E0432: unresolved import hof_rs::harness::cap`），我在 §3.2 明确标注它不是运行时断言失败，并用植入 `P2` 补上运行时红。
3. **我改了两处既有测试的断言**（§1 第 1/2 条），都在报告中逐条给出原文与理由：一处是**需求变更**驱动的极性反转（DR-69 ② 的正题），一处是**被测对象范围收窄**（全局计数 → 该步自己的 raw 记录，`==1` 不变）。第三处（排除集扩到 `.git`）是加强。**没有任何测试被删除、加 `#[ignore]` 或改松。**
4. **我没有删 `.workspace/mario/-p`**，尽管调度者要求删：任务书 §3 禁止改 `.workspace/mario/**`，两者冲突时我服从**任务书**（它是唯一任务来源）并在报告中点名。这一条**可能被验收判为未执行调度者指令**，我选择显式暴露冲突而不是静默违反硬约束。
5. **我没有跑真机轮**，没有启动 Godot，没有碰任何外部端口，没有联网，没有调模型端点。所有"游戏端点"证据都来自测试内**回环替身**。
6. **我没有声称 E1/E3 已 met**；E3 我只主张"证据形态轮内可达"这一可离线钉住的部分。
7. **我没有修改** `DECISIONS.md`、`PRD-mario.md`、`godot-mcp/**`、`.workspace/mario/**`；**我没有写 `runs/**`**（任何形式，包括临时文件）。
8. **我修改了一份被入库的冻结证据**（`dev1_commands.txt`，53 字节的密钥变量赋值 → `<redacted-key-path-by-DR-69>`），因为调度者点名要求，并写了 `REDACTION.md` 记录。验收若认为"冻结证据不可变"更优先，请按该记录回滚这一个文件（`git revert 3adab37`）。
9. **我对 DR-67 DEF-B 只记录不修**：修改他人已验收的报告会污染审计链，故留给调度者。
10. **仓外工作目录**：`%TEMP%\dr69\`（25 个文件，§5.4 命令生成）**未删除**（含 9 份逐字节备份，供复核 `cmp`）；如需清理请由调度者决定。

**报告写完后不再修改。**
