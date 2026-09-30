# TASK-SMOKE-T10-REPORT — 真机 T=1 整轮（引擎 `035edfce7`）：**E1 首次 `met`**、Tester 证据形状首次在真机被走到并被接受、E3 证据形态轮内成形且引擎接受 `position:neq`；**但发现一个新的 major 缺陷：DR-69 的密钥赋值脱敏把 Tester 轨迹 JSON 写坏**

- 任务书：`.spec/hof-rs/tasks/TASK-SMOKE-T10.md`（本轮）+ `.spec/hof-rs/tasks/TASK-SMOKE-T8.md`（**基准任务书，仍全效**）
- 落点：`F:\moonbit-hof-rs`（外层仓），报告人：**真机执行子代理（无上游对话上下文）**
- 本轮命令：`target/release/hoh.exe run --iterations 1 --run-id smoke-t10`
- **只跑了这一轮**（无重试、无 attempt-A/B，见 §16）
- 本轮轮目录：`runs/smoke-t10/**`（**232 文件 / `319555896964ce1526f72a33cb239bf389fe29bcde23841764d13c57dfb38b8b`**，newest `2026-09-30 18:23:08`）
- 只读基线（开工/收工逐字未变，§11.2）：`runs/smoke-t6`（135 / `c144ef32…7a9c03`）、`smoke-t7`（115 / `6e4c1595…20fb7`）、
  `smoke-t8`（358 / `6d11b2c6…bdf5a7`）、`smoke-t9`（83 / `541e2d81…36ca9d`）
- 开工=收工 HEAD **`c932fcb38343b1e66604acc6e7bbfbbf5f15b37b`**；`origin/master` == HEAD（**ahead 0，未 push 任何东西**）
- 我**未改**任何受控文件：`godot-mcp/**` 零改动（嵌套仓 0 行）、`PRD-mario.md` sha 未变、`DECISIONS.md` 我全程只读
  （它在报告提交后由**调度者的并发提交 `87adbea`/D276** 改动，见 §11.3 与 §16.11）、
  `.workspace/mario/**` 只被**本轮 Developer 按角色权限**改（那是剧本内的写，不是我），我全程只读它

---

## 0. 结论摘要

| 编号 | 判定 | 一句话依据 |
|---|---|---|
| **E1** | **met** | Planner `artifact_valid=true`；**Developer 真的写了工程文件**（`A_0=1f3d20ed…` 17 文件/18397 B → `A_1=ed98d1b8…` 17 文件/21679 B，**7 个脚本被改**）；Tester `Submitted`/`artifact_valid=true`，**合法 `E_1` 被接受**（9 verified + 11 gap）；整轮跑完，退出码 **0** 三方一致。§2 |
| **E2** | **met** | 电池 `project_reload_and_open` / `play_scene_ready` / `editor_errors_baseline` 全 `ok=true`；`launchable=true`、`reasons=[]`；主场景起到 **53 节点**；编辑器日志只 1 条信息性 MCP banner（0 编译/脚本错误）。§4.6 |
| **E3** | **not_met（部分：4 类行为里 2 类成立）** | **证据形态首次轮内成形且引擎接受**：每窗口 **before/after PNG**（8 张）+ `running_game_assert_node_state{Player,position,neq,期望=窗口首样本}` **4/4 `passed=true`**（无 `POSITION_ASSERTION_UNAVAILABLE`）。**左右移动、跳跃成立**；**"至少 1 个可交互对象"不成立**（金币未被拾取，`Coins: 0` 全程不变；F6–F12 全 gap）；**"终点/胜负条件"只成立失败半边**（GAME OVER+跳跃重开，F14/F15），**胜利从未被驱动**（F13 gap，`Goal.reached=false`）。§4 |
| **E4** | **met** | `E_1` 9 条 verified **逐条**指向存在的执行记录（我逐条 stat：`MISSING: []`），11 条 gap 互斥（`overlap: set()`），运行时把候选身份绑进记录（`candidate_id=ed98d1b8…`）。§2.4 |
| **E5** | **met** | 我自算三棵树**逐字节同一**：`candidate` == `versions/ed98d1b8…` == 活体 `.workspace/mario`（17 文件/21679 B/`c781cf81…034a`）⇒ QA 未改 `A_1`；`candidate_id == version_id == ed98d1b8…`。§2.3 |
| **E6** | **met** | `qa_report.md` 明写 `qa_status: partial`，11 条 gap 每条带 `player_impact`；**主动声明未达成**（金币、敌人、方块、胜利、时长、60s 稳定性）。§2.5 |

**本轮不可判定的判据：无**（E1..E6 全部有本轮证据）。

### 0.1 六个核心问题速答（原始证据见对应节）

| # | 问题 | 答案 |
|---|---|---|
| 1 | **E1 是否终于 met？** | **是**。Developer 真写了文件（7 个脚本，`A_0≠A_1`）；整轮跑完（Planner→Developer(×2)→电池→冻结→Tester，**54m14s，exit 0**）；`E_1` 被接受。**三方一致**：`exit_code` 字节 `30 0A`（`"0\n"`）、`meta.json.exit_code=0`、控制台 `ROUND_EXIT=0`。**无新失败原因**——但见**新缺陷 F-T10-1**（脱敏把 Tester 轨迹 JSON 写坏）。 |
| 2 | **Tester 证据形状是否终于被走到？** | **是，且一次就过**：`iter-1/traj/` 里**只有 `tester.attempt1.json`**（无 attempt2），`exit_status=Submitted`、`artifact_valid=true`；全轮 **0** 处 `schema_failure`、**0** 处 `RepeatedFormatError`。（`No tool calls found` 的格式提醒仍在，但**没有升级**：planner 6、developer.attempt1 23、developer.attempt2 0、tester 5，四个 attempt 里**没有一个**以 `RepeatedFormatError` 收场。）DR-68 的修复**首次获得真机证据**。 |
| 3 | **E3 是否补齐？** | **证据形态补齐，行为只补齐一半**。电池轮内产出 **8 张 before/after PNG** 与每窗口 1 次 `position:neq` 断言；**引擎接受**（4/4 `passed:true`，`resolved_node_path=/root/Main/Player`）。我逐帧抽取：右移 `+216.3330`（恒 `3.6667 px/帧` = 220 px/s）、左移 `−216.3329`、跳跃 y `269.981→214.259（f17）→242.592`。**可交互对象：不成立**；**终点/胜负：只失败半边成立**。§4 |
| 4 | **降噪与门** | **无任何 DR-24 定向修复 attempt**（`repair_retry_used=false`；无 `developer.attempt3`；`warnings.log` 无 `launch_gate_repair`；`battery_passes` 仅 1 遍；`quarantine/` 无 `deterministic-pass-*.stale-*`）。门被评估且**打开**（`applicable=true, launchable=true, reasons=[]`）；**无过期编辑器日志关门**（`editor_errors_baseline.count=1`，内容是信息性 banner）。`wrap_up_retry_used=true`（Developer 步数用尽的 wrap-up，`reason=artifact_missing`）——**不是修复尝试**，且它**确实写了工程**（`player.gd` mtime 18:09:43 落在 wrap-up 窗口 18:05:37–18:10:11）。§5 |
| 5 | **64 KiB 上限是否生效** | **生效，两次**。(a) Developer 读 `res://scripts/main.gd`：`hoh_output_original_bytes=80800 → 65536`；(b) Tester 读 `input_replay.json`：`147809 → 65536`。两次输出都带显式截断标注并写进 `extra`；**两个角色轨迹里最大单条消息 = 65886 B** ⇒ **没有超长结果被回放**（t9 的 15,570,803 B 事故未复现）。§6 |
| 6 | **是否发生零增量** | **没有**。`warnings.log` **只有 2 行**，**不含** `Zero-increment shape: …`、`no_progress`、`no_engineering_write`。⇒ 无需报告其形状；工程树确实有变更（§2.2）。§7 |

---

## 1. 执行流水

### 1.1 前置（开工前，全部只读/构建）

```
HEAD / origin/master                c932fcb38343b1e66604acc6e7bbfbbf5f15b37b   (ahead 0)
git status --porcelain -uall        （空）
engine --version                    4.8.dev.mono.custom_build.035edfce7         （判据，逐字相符）
engine sha256 / size / mtime        08483088…e9e6a / 194216960 / 2026-09-29 08:31:02（仅记录）
editor                              127.0.0.1:9877 LISTENING pid 75204；GET /mcp → tools=154
godot processes                     仅 75204（**开局无孤儿游戏进程**）
runs/smoke-t10 存在？                False
cargo fmt --check                   FMT_EXIT=0
cargo build --release --offline     逐文件 touch 89 个 git ls-files '*.rs' 后编译：Compiling hof-rs ×1 → Finished 19.26s，BUILD_EXIT=0
target/release/hoh.exe              sha256 ada849581536837f47d49b1cd1f85ceab0e78bbc16455c878ace9f8d5d753e4f  mtime 2026-09-30 17:28:01
hoh doctor                          DOCTOR_EXIT=0（spec sha 命中 / model.chat 命中 / engine_version 命中 / tools.mcp 154）
密钥                                HOH_MODEL_API_KEY 自 config/model.secret.env 导入，**只报长度 51，不打印**
```

原文：`TASK-SMOKE-T10-evidence/round/prerun_state.txt`、`console.txt`。

### 1.2 正式轮（**唯一一轮**）

```
START 2026-09-30 17:28:54   END 2026-09-30 18:23:08   ELAPSED 3254 s = 54m14s
ROUND_EXIT=0
阶段时序（traj mtime / result.json durations）：
  planner            17:29:01→17:30:23     79,221 ms   21 calls / 139,523 tok    Submitted, artifact_valid=true
  developer#1        17:30:25→18:05:34   2,107,594 ms 150 calls /17,437,436 tok   LimitsExceeded
  developer#2(wrap)  18:05:37→18:10:11     273,954 ms   25 calls /  784,435 tok   LimitsExceeded   (wrap_up_retry_used=true, reason=artifact_missing)
  candidate 冻结      18:10:14
  电池               18:10:09→18:10:12    （1 遍，11/11 ok）
  tester             18:10:15→18:23:08     770,826 ms   94 calls / 7,255,119 tok   Submitted, artifact_valid=true
```

**退出码三方一致（原文）**：

```
runs/smoke-t10/exit_code        字节 30 0A           → "0\n"
runs/smoke-t10/meta.json        "exit_code": 0
console.txt                     ROUND_EXIT=0
runs/smoke-t10/iter-1/result.json  "ok": true, "failed_role": null, "reason": "ok", "issues": []
```

**tokens 合计 25,616,513**（planner 139,523 + developer 17,437,436+784,435=18,221,871 + tester 7,255,119）；
**`usage_known=true` 三条**，无 unknown。

---

## 2. Q1 专项 —— **E1 = met**（三个要件逐条成立）

### 2.1 要件 1：Planner 产出合法 `D_1`

`runs/smoke-t10/iter-1/plan.md`（2549 B）；`logs/planner.attempt1.log` → `"artifact_valid": true`、`exit_status:"Submitted"`。
（t9 的 `RepeatedFormatError` **本轮未复现**：planner 轨迹里 `RepeatedFormatError` = **0** 处。）

### 2.2 要件 2：Developer 真的写了工程文件 —— **`A_1 ≠ A_0`**

**两个树的摘要（我自己重算，口径见 §11.1）**：

```
A_0  versions/1f3d20ed50b472e422832c4fa2c8d7b72ae04ee11fa4c5ace65fb20a43997fd8   17 files  18397 B
A_1  versions/ed98d1b80be945c6d8e8a40fc3b5114dd9e1d33b1c29d576d050255a7fa1a1e1   17 files  21679 B
```

**树根相对、排除 `{.hoh,.godot,.import,.git}`、`rel\t{len}\tsha256`、序数排序、整体 sha256（我的口径，`scripts/hashtree2.py`）**：

```
planner-view（=A_0 副本）  5971b4843a75633dc7a0d88d0dee6d181e9e61848ef09638a210146caf53e463
versions/1f3d20ed…（A_0）  5971b4843a75633dc7a0d88d0dee6d181e9e61848ef09638a210146caf53e463   SAME
versions/ed98d1b8…（A_1）  c781cf81a8df99078591fe644d37ee34c576bc2d89f17141c9ee6fbc67c8034a   DIFFERS
iter-1/candidate（冻结）    c781cf81a8df99078591fe644d37ee34c576bc2d89f17141c9ee6fbc67c8034a   SAME
.workspace/mario（活体）    c781cf81a8df99078591fe644d37ee34c576bc2d89f17141c9ee6fbc67c8034a   SAME
```

> **跨轮自洽**：`A_0` 的 `5971b484…e463` 与 `TASK-SMOKE-T9-REPORT.md` §9.2 记录的工程树值**逐字相同** ⇒ 本轮起点正是 t9 的终点（同一张 A0），
> 而 `A_1` 是一个**新的**摘要 ⇒ 增量是真的、可比的。

**变更文件（`scripts/treediff.py`，逐文件）**：

```
ADDED: []   REMOVED: []
MODIFIED (7):
  scripts/brick.gd           171 B 64073c5ee2c7 ->  265 B f7a0474e9fe9
  scripts/coin.gd            430 B 470e38da53f1 ->  975 B b310d631e54d
  scripts/enemy.gd          1419 B ff8201d4f8a9 -> 1748 B a1406b9c6a76
  scripts/goal.gd            275 B 8c221d236e5f ->  440 B c88a3fb3b6e2
  scripts/main.gd           2344 B 26bd5ea69cd7 -> 3368 B ec95dc0e1794
  scripts/player.gd         2231 B b2936105212e -> 3216 B 6cb2c76cb878
  scripts/question_block.gd  510 B fc21a7dbec69 ->  650 B c927efb199bf
```

**哪些 attempt 写的（mtime 交叉核对）**：attempt#1 写了 6 个（17:44:06–17:51:16）；**wrap-up attempt#2 写了 `player.gd`**
（`iter-1/candidate/scripts/player.gd` mtime **18:09:43**，落在 wrap-up 窗口内）。
`scenes/main.tscn` 与 `project.godot` **本轮未被改**（mtime 仍是 t8/更早），与「只改 7 个脚本」一致。

**Developer 没有绕道（与 t9 的决定性差别）**：轨迹命令级统计（`scripts/counts.py`，原文 `analysis/trajectory_analysis.txt`）：

```
developer.attempt1.json : n_messages 349, assistant 127, bash 196
    cmd 'running_game_' = 0        cmd 'editor_' = 135      %HOH_ = 418
    'game_endpoint_unavailable' = 0     'JSON-RPC error' = 14     '-32602' = 4
    largest message = 65886 B（即被 64 KiB 截断的那条）
developer.attempt2.json : assistant 25, bash 40 ；cmd 'editor_' = 5 ；'JSON-RPC error' = 2
```

⇒ **t9 的"在 `.hoh/scratch` 里自造 MCP 客户端 + 裸 HTTP 探端口"没有重演**：没有任何 `running_game_*` CLI 调用、
没有裸 HTTP、`game_endpoint_unavailable` **0** 次。Developer 把力气放在读工程 + `editor_*` 自检 + **写工程**上。

### 2.3 要件 3：QA 产出**合法** `E_1` —— 与 E5 同一组证据

```
iter-1/evidence.json            14,567 B   {iteration:1, qa_status:"partial", verified_records:9, gap_records:11, planner_handoff:{3 数组}}
iter-1/candidate/.hoh/evidence.json 13,592 B （Tester 自己写的原件；记录里 candidate_id 为 ""）
iter-1/qa_report.md              2,624 B
iter-1/traj/tester.attempt1.json 834,125 B  （**这一个文件被脱敏写坏，见 F-T10-1**）
tester.attempt1.log              artifact_valid=true, exit_status=Submitted, attempt=1
```

**E5 的独立证明**：`candidate`（冻结视图）与 `versions/ed98d1b8…`（`A_1` 快照）与活体 `.workspace/mario`
**三棵树的根相对摘要完全相同** `c781cf81…034a`（17 文件 / 21679 B）⇒ **QA 没有改动 `A_1`**；
`result.json.candidate_id == version_id == ed98d1b80be945c6d8e8a40fc3b5114dd9e1d33b1c29d576d050255a7fa1a1e1`。

### 2.4 E4 的独立证明（逐条 stat，不看运行时自报）

`scripts/e4check.py`：对 9 条 verified 的**每一条** `execution_records[*].path` 在冻结候选视图里做存在性检查 ⇒
**`MISSING: []`**；`verified_ids = [F1,F2,F4,F5,F14,F15,F16,N1,N2]`、`gap_ids = [F3,F6,F7,F8,F9,F10,F11,F12,F13,F17,N3]`、
**`overlap: set()`（互斥）**；`planner_handoff` 三数组齐（4/6/6）。
`iter-1/evidence.json` 里每条记录的 `candidate_id` 已被运行时绑成 `ed98d1b8…`（Tester 原件里是空串）⇒ R4 的身份绑定**可见**。

### 2.5 E6：诚实性（不是"自我声明"，是可核对的内容）

`iter-1/qa_report.md`（我逐字读过）明写 `qa_status: partial`，并把**没做到的**摆出来：
金币未拾取（`Coins: 0` 全程不变）、facing 左向不翻、敌人/方块机制无执行记录、**胜利从未出现**（只有 GAME OVER）、
时长与 60s 稳定性未测。`gap_records` 每条带 `player_impact`（如 F13「the player can never win」）。
⇒ **未达成被声明，未谎报为 verified**。

### 2.6 E1 相关的**新缺陷**（不影响 E1 的三要件，但影响可审计性）

**F-T10-1（major，新）**：`runs/smoke-t10/iter-1/traj/tester.attempt1.json` **不是合法 JSON**。
`json.loads(..., strict=False)` 报 `Expecting ',' delimiter: line 2205 column 8 (char 412870)`；
破点正是 `HOH_MODEL_API_KEY=<redacted>` 之后的那个物理换行——**闭引号与逗号被删掉了**。
同轮另外 3 个轨迹文件都合法。根因与复现见 §9。

---

## 3. Q2 专项 —— Tester 证据形状**首次在真机被走到，并且一次通过**

```
runs/smoke-t10/iter-1/traj/   planner.attempt1.json
                              developer.attempt1.json
                              developer.attempt2.json
                              tester.attempt1.json      ← 只有 attempt1，**没有 attempt2**
```

| 判据 | 原始值 | 位置 |
|---|---|---|
| Tester 是否一次过 | `attempt=1`、`exit_status=Submitted`、`exit_was_limits=false` | `logs/tester.attempt1.log`、`result.json.attempts[3]` |
| 证据是否"合法" | `artifact_valid=true`；`E_1` 9 verified + 11 gap，结构、互斥、路径全部成立 | `evidence.json`、§2.4 |
| 是否发生过 schema 重试 | 全轮 `schema_failure` = **0**、`RepeatedFormatError` = **0**（四条轨迹**逐文件** 0） | `grep -ril` 全轮 + 逐文件 `grep -c` |
| 是否还被格式提醒打扰 | `No tool calls found` 仍出现（planner 6 / developer.attempt1 23 / developer.attempt2 0 / tester 5），但**没有一次升级**为 `RepeatedFormatError`；planner 与 tester 都以 `Submitted` 收场 | `grep -c` 逐文件 |
| 是否触及过 DR-68 的三要素 | 证据含 `type`/`claim_id`（`verified_records[0]` 有 `claim_id:"F1"`、`execution_records[*].type:"replay"`） | `iter-1/evidence.json` |

⇒ **t8 的 `schema_failure` 根因（证据缺 `type`/`claim_id`）在真机上不再复现**，与 DR-68 验收 R-1 的"未验证"项**就此闭合**。

---

## 4. Q3 专项 —— E3：证据形态轮内成形、引擎接受断言；行为只补齐一半

> 纪律：**我不把探针的 `GAME_INPUT_CHANNEL_OK` 当行为证据**（§13.1 给出它本轮的实测值，说明它为什么不可用）。
> 下面每条都来自**游戏进程端点上的语义工具**（`running_game_*`），来源见 §4.5。

### 4.1 轮内证据形态（DR-69 ④ 的目标形态）

`iter-1/candidate/.hoh/deterministic/raw/input_replay.json` = 48 次调用，`ok=true`，`supports=[F1,F2,F3]`，结构为**四个窗口**：

```
每个窗口：running_game_capture_screenshot(label=<action>:replay_frame_before)
        → create_input_recording → play_input_recording
        → run_test_scenario（轴断言）→ stop_input_recording
        → editor_simulate_input_action(label=<action>:EDITOR_SIDE_INJECTION)
        → running_game_get_node_property_samples（逐帧）
        → running_game_capture_screenshot(label=<action>:replay_frame_after)
        → running_game_assert_node_state(label=<action>:replay_assert_moved)
        → running_game_get_node_property_samples(properties=input_axis)
```

**PNG（轮内、在冻结候选视图里）**：`iter-1/candidate/.hoh/evidence/`
`replay-move_right-{before,after}.png`、`replay-move_left-{before,after}.png`、`replay-jump-{before,after}.png`、
`replay-move_right_release-{before,after}.png`，另有 `frame-00.png`（共 9 张）。

### 4.2 位置断言：**引擎接受了 `position:neq`**（DR-69 的 0.6 概率推断在此变实测）

四条的原始回包（`payload.content[0].text` 解出的 JSON，逐字）：

```json
{"actual":{"x":400.999725341797,"y":283.998992919922},"assertion":"node_state",
 "expected":{"x":184.666702270508,"y":283.998992919922},"node_path":"/root/Main/Player",
 "operator":"neq","passed":true,"property":"position","resolved_node_path":"/root/Main/Player"}    ← move_right
{"actual":{"x":448.666259765625,"y":283.998992919922},"expected":{"x":415.666351318359,"y":283.998992919922}, … "passed":true}  ← move_right_release
{"actual":{"x":455.999572753906,"y":242.59196472168},"expected":{"x":455.999572753906,"y":269.980834960938}, … "passed":true}   ← jump
{"actual":{"x":232.333389282227,"y":283.925262451172},"expected":{"x":448.666259765625,"y":277.758636474609}, … "passed":true}  ← move_left
```

⇒ **4/4 `passed=true`**，**没有** `POSITION_ASSERTION_UNAVAILABLE`（也没有 `POSITION_UNCHANGED`、`REPLAY_FRAME_MISSING`）。
**期望值逐条等于该窗口的第一个采样** ⇒ 采样滞后被消掉（DR-69 的校准设计**在真机成立**）。

### 4.3 我逐帧抽取的数字（不看运行时自报）

| 窗口 | 样本 | 首 → 末 | Δ | 每帧 | 对照 |
|---|---|---|---|---|---|
| `move_right` | 60 | x 184.666702270508 → 400.999725341797 | **+216.333023** | `216.333023/59 = 3.6666614` | ×60 = **220.0 px/s** |
| `move_right_release` | 10 | x 415.666351318359 → 448.666259765625 | +32.999908 | 3.6667 | 同向再确认 |
| `jump` | 30 | y 269.980834960938 → **214.258605957031（f17 峰）** → 242.59196472168 | 起升 **55.722229**、窗内下行 28.333359 | x 恒定 455.999572753906 | 抛物线上开下落，落回地面 |
| `move_left` | 60 | x 448.666259765625 → 232.333389282227 | **−216.332870** | `−216.332870/59 = −3.6666588` | ×60 = **−220.0 px/s** |

- **右移成立**：恒 `+3.6667 px/帧`；**左移成立**：恒 `−3.6667 px/帧`；两者对称（216.333 与 216.333），
  且 `3.6667×60 = 220.0 px/s` 与 `scripts/player.gd` 的 `speed`、`velocity.x = dir*speed` 自洽。
- **跳跃成立**：`y` 从 269.981 升到 214.259（f17 峰）再回落到 242.592，窗内 x 恒定 ⇒ 竖直位移来自跳跃，不是走路。
  （窗首 `y=269.981` 已高于地面 283.999 ⇒ 窗首已在空中，与 t9 验收记录的采样滞后同族；本报告**不使用总位移**做判定，
  只用**逐帧趋势 + 引擎自己接受的位置断言**。）

### 4.4 四类行为逐条裁定

| 行为 | 本轮可否确立 | 依据 |
|---|---|---|
| **左移** | **成立** | `input_replay` move_left 窗口 `Δx=−216.333`；`F1` verified |
| **右移** | **成立** | `Δx=+216.333`（另有 release 窗口 +32.9999 复核）；`F1` verified |
| **跳跃** | **成立** | 上开下落抛物线；`F2` verified |
| **至少 1 个可交互对象** | **不成立** | 金币未被拾取：`hud-labels.json` 的 `HUD/Coins` 在被驱动穿过整关后**仍是 `Coins: 0`**；`F10` 在 gap，`F6/F7/F8/F9/F11/F12` 也在 gap（无公共执行记录） |
| **一个终点/胜负条件** | **只失败半边成立** | 失败：`HUD/Result='GAME OVER - press Jump to restart'`（`failure-state.json`），跳跃后重开（`restart-state.json`：`x=60.0`、Result 清空）⇒ `F14/F15` verified。胜利：`Goal.reached=false`、**从未观测到胜利文本**（`F13` gap，`player_impact:"the player can never win"`） |

⇒ **E3 = not_met**：四类里**只明确成立 2 类（左右移动、跳跃）**，可交互对象不成立，终点/胜负只完成了失败半边。
**但判据要求的形式（回放 + 前后截图 + `assert_node_state`）本轮第一次在轮内齐备**，这是本批最大的方法学进展。

### 4.5 来源确实是**游戏进程端点上的语义工具**

- `iter-1/candidate/.hoh/deterministic/raw/play_scene_ready.json`：`editor_play_scene(mode=main)` →
  `{"endpoint":"http://127.0.0.1:65144/mcp","mcp_port":65144,"mcp_port_source":"auto_free_port", …}`；
  `editor_stop_scene` 记录 `game_endpoint_invalidated:{endpoint:…65144…,pid:109040,port:65144}`。
- 轨迹里 48 次 replay 调用的工具名**全部**是 `running_game_*`（`capture_screenshot`/`create_input_recording`/
  `play_input_recording`/`get_node_property_samples`/`assert_node_state`/`run_test_scenario`/`stop_input_recording`）；
  注入走 `editor_simulate_input_action`（harness 自己的分工），但**读数与断言**都在游戏端点。
- **`input_axis` 在真机恒为 `null`（实测）**：`{"frame_count":1,…, "samples":[{"frame":0,"input_axis":null}]}`
  且 `run_test_scenario` 的轴断言原始回包：
  `{"all_passed":false,…,"reason":"node '/root/Main/Player' does not have the property 'input_axis'",…}`
  ⇒ **承重的确实是按位置的证据**（与调度者判断一致）。

### 4.6 E2 的原始依据（顺带）

- `raw/editor_errors_baseline.json`：`{"available":true,"count":1,"editor":true,"errors":["[MCP] capture=off (default; …)"], …}`
  ⇒ **0 条编译/脚本错误**，只有 1 条信息性 MCP banner。
- `E_1` 的 `N1` 记录：主场景 boot 起 **53 节点**，`editor_stop_scene` → `{"stopped":true}`。
- `result.json.artifact_gate = {applicable:true, launchable:true, reasons:[]}`；`meta.json` 同值 ⇒ **双处自洽**。

---

## 5. Q4 专项 —— 降噪、门、修复尝试

1. **DR-24 定向修复 attempt：没有。**
   `result.json.repair_retry_used = false`；`iter-1/traj/` 无 `developer.attempt3`；`warnings.log` 无 `launch_gate_repair`；
   `quarantine/` 只有 `.hoh.stale-1790760534`（DR-61 的上一轮 `.hoh` 隔离），**没有** `deterministic-pass-*.stale-*`
   ⇒ **电池只跑了 1 遍**（`result.json.battery_passes` 长度为 1，`pass:1`，11 步全 `true`）。
   ⇒ **不存在"零写入的修复尝试"这一类缺陷**，也无需比较第一遍 vs 第二遍。
2. **门被评估且因正确原因打开**：`applicable=true`、`launchable=true`、`reasons=[]`；
   失败路径的"如实空"本轮**没有被走到**（本轮成功）。
3. **无过期编辑器日志关门（F1 类）**：`editor_errors_baseline.count=1` 且内容是 `[MCP] capture=off …` 的**信息性**行，
   不是 `res://…:line … Function "X()" not found` 那种形状 ⇒ 不触发 DR-68 ② 的窄规则，也不需触发。
4. **`wrap_up_retry_used=true` 的性质**：`wrap_up_retry_reason="artifact_missing"`，是**步数用尽后的 wrap-up**
   （Developer 两条 attempt 都是 `LimitsExceeded`），**不是修复重试**。它**确实动了工程**（`player.gd` 18:09:43）
   ⇒ 若把"wrap-up"误读成"修复"，会得出错误结论；这里明确区分。
5. **降噪读数**：全轮 **0** 处 `game_endpoint_unavailable`；**无** `mcp-errors.jsonl`（⇒ 运行时层面 0 次 MCP 传输错误）；
   `-32602` 只有 **6** 次（developer 4 + tester 2），且**全部是角色自己参数写错**，例如
   `hoh: JSON-RPC error -32602: Unknown parameter 'node_path' for tool 'editor_get_node_properties'`（returncode 5）——
   是模型自纠过程，不是 harness 缺陷。

---

## 6. Q5 专项 —— 64 KiB 上限确实生效、无超长结果被回放

**两次真实截断（`Output.extra`，随轨迹落盘）**：

```
(a) Developer 读 res://scripts/main.gd（project_read_script）
    [hoh: tool output truncated — the bytes above are only the head of the result]
    [hoh: 65536 of 80800 bytes were carried; the remaining 15264 bytes were dropped and are NOT part of this result.
     Re-run the command narrower, or write its output to a file under the scratch directory and read a slice of it.]
    extra: {hoh_output_limit_bytes:65536, hoh_output_original_bytes:80800, hoh_output_truncated:true}
    traj: developer.attempt1.json，1 处

(b) Tester 读 .hoh/deterministic/raw/input_replay.json（147,809 B）
    [hoh: 65536 of 147809 bytes were carried; the remaining 82273 bytes were dropped …]
    extra: {hoh_output_limit_bytes:65536, hoh_output_original_bytes:147809, hoh_output_truncated:true}
    traj: tester.attempt1.json，1 处
```

**没有超长结果被回放**（t9 的致命事故不复现）：
四条轨迹里**最大单条消息 = 65,886 B**（developer），tester 最大 52,270 B；
**全轮不存在任何 MB 级消息**；attempt-A/整轮失败（exit 5 `llm-connector chat request failed`）**未发生**。
⇒ 截断后的文本（head）才是进入后续请求的内容，`original_bytes` 精确记录被丢弃的字节数。

---

## 7. Q6 专项 —— "零增量"没有发生

`runs/smoke-t10/warnings.log` **全文只有两行**（逐字）：

```
DR-61: moved the previous round's .hoh out of this round's read path to runs\smoke-t10\quarantine\.hoh.stale-1790760534; no role's working directory can reach those bytes (they are kept, not deleted)
qa_scope: MCP acts on the project open in the editor (the real workspace) while the Tester evaluates a frozen copy; the runtime binds both to one candidate identity with pre-QA and around-QA hash assertions (D7).
```

**没有** `Zero-increment shape: …`、**没有** `no_progress`、**没有** `no_engineering_write`。
且 `result.json.ok=true`、退出码 0、`A_1` 是一个新摘要 ⇒ **"Developer 什么都没写"与"全写在排除路径"两个形状本轮都不成立**。
（t9 的 `-p` 目录也顺带被本轮 Developer 清掉了，见 §11.4。）

---

## 8. 通道诊断（调度者点名"本轮最有价值的单条诊断"）：**角色 CLI 在真机上成功到达游戏端点**

**这是 DR-69/70/71 三轮修改后的第一次真机检验，结果是绿的。**

1. **轮次级路由在第一个角色之前就存在**：`runs/smoke-t10/game_endpoint.json` mtime **17:29:01**，
   planner 轨迹写出于 **17:30:23**；我在轮中（~17:47）读到的内容逐字为
   `{"endpoint":"http://127.0.0.1:61826/mcp","port":61826,"source":"auto_free_port","pid":109308}`，
   且 `pid 109308` 实测存活（`Get-Process`，StartTime 17:28:59）。原文：`analysis/midrun_game_endpoint.txt`。
2. **每个角色都拿到 `HOH_GAME_ROUTE`**：Tester 的环境读取回包里有
   `HOH_GAME_ROUTE=F:\moonbit-hof-rs\runs\smoke-t10\game_endpoint.json`（值本身不是密钥，见 §13.2 的脱敏说明）。
3. **角色**真的用**契约内的 CLI** 打通了游戏端点（**原始回包逐字**）：
   ```
   $ cd /d F:\moonbit-hof-rs & "%HOH_HOH_BIN%" tools call running_game_get_node_properties \
       --args-file "...\candidate\.hoh\scratch\hud_Coins.json"
   <returncode>0</returncode>
   <output>
   {
     "content": [
       { "text": "{\"node_path\":\"/root/Main/HUD/Coins\",\"properties\":{\"text\":\"Coins: 0\",\"visible\":true},\"type\":\"Label\"}",
         "type": "text" }
     ]
   }
   </output>
   ```
   计数（精确，`scripts/tester_execcount2.py`：按每条工具结果的 `extra.actions[0].command` 取**真正执行**的命令，避免把同一命令在
   assistant 参数与 `extra.actions` 里的两份文本重复计数）：Tester **执行了 89 条 bash 命令**，其中 **23 条**是
   `hoh tools call running_game_*`（`get_node_properties` 11、`run_test_scenario` 10、`get_node_property_samples` 4、
   `create/play/stop_input_recording` 各 2），命令文本里 `game_endpoint_unavailable` **0** 次。
   `.hoh/evidence/{hud-labels,camera-node,failure-state,restart-state,facing-scenario}.json` 的内容
   （`/root/Main/HUD/Lives`、`anchor_mode:1`、`GLOBAL_POSITION` 浮点、`GAME OVER - press Jump to restart`、spawn `x=60.0`）
   **只可能来自活着的游戏进程**。原文：`analysis/tester_live_cli_payload.txt`、`analysis/tester_cli.txt`。
4. **轮末撤下**：`runs/smoke-t10/game_endpoint.json` **收工时不存在**（`Test-Path` False）；
   `editor_stop_scene` 记录 `game_endpoint_invalidated:{65144/pid 109040}`；收工全机**无游戏进程**（只剩编辑器 75204）。
   ⇒ **发布-就绪-撤下**的生命周期在本轮走全。
5. **Developer 本轮根本没试** `running_game_*`（0 次），只用了 `editor_*`（135 次）⇒ 新提示词的分工约束**起了作用**，
   同时也意味着"Developer 也能到达"这一条**本轮没有被它亲自验证**（Tester 验证了同一条通道）。

---

## 9. 新发现清单（本轮，全部可指到 文件:行 / 原始输出）

| 编号 | 级别 | 内容 | 证据 |
|---|---|---|---|
| **F-T10-1** | **major** | **DR-69 的密钥赋值脱敏会把 JSON 轨迹写坏**：`redact_secret_assignments` 在不带引号的赋值里用 `[';','\n','\r']` 找值的末尾，**不认 JSON 里转义的 `\n`（`\`+`n`）**；当赋值出现在 JSON 字符串内部、且后面跟的是**物理换行**时，它就一路吃到物理行尾，**把字符串剩下的内容、闭引号与逗号一起删掉** ⇒ 文件不再是合法 JSON。本轮 `iter-1/traj/tester.attempt1.json` 因此损坏（`Expecting ',' delimiter … char 412870`，另 3 个轨迹文件合法）。 | 代码：`src/runtime/secrets.rs:70-98`（`find([';','\n','\r'])`，:88）；调用点 `src/runtime/run_loop.rs:866/1097/1287/1571/1674/1708`（**写盘后回写**）。原始：`analysis/redaction_defect.txt`（含我的**逐行仿真**，输入即"JSON 转义的环境转储"，输出与文件里观察到的损坏**同形**） |
| **F-T10-2** | info（**有利**） | `developer.attempt2.json` 的两处脱敏**没有**造成损坏：那里的值后面跟着字面 `;`（`HOH_MODEL_API_KEY=<redacted>;C:\Users\…`），扫描正确停在 `;`。⇒ 同一缺陷的**触发条件是"赋值后紧跟物理换行"**，可据此写反例测试。 | `analysis/redaction_defect.txt` 第一段 |
| **F-T10-3** | minor | **`evidence_diff` 仍是空**（`{"added":[],"modified":[],"removed":[]}`），而本轮**真实有 7 个文件被改** ⇒ **DR-68 R7 在本轮终于有条件被判为"未实现"而不是"恰好为空"**（t9 时它恰好也该为空，无法区分）。 | `iter-1/result.json`；§2.2 的 7 文件清单 |
| **F-T10-4** | info | **Developer 两次 attempt 都 `LimitsExceeded`，靠 wrap-up 收尾**；而 wrap-up **只写了 1 个文件**（`player.gd`），主增量来自 attempt#1。⇒ "步数用尽"不等于"没干活"，但**它离失败只差 1 个文件**：若 wrap-up 也没写，本轮就会落进 `NoEngineeringWrite`。 | `result.json.attempts`、`else` 见 §2.2 mtime |
| **F-T10-5** | info | **`-p` 目录被本轮 Developer 清掉**：`rmdir "-p"` 出现 2 次；收工 `.workspace/mario/-p` **不存在**，`A_1`/candidate 也不存在；而 **A_0 快照与 planner-view 里仍在**。 ⇒ D271/R3 的该项在本轮**被医生自己治好了一半**（活体工作区干净了；历史 A0 快照里那份仍在，且它**不进内容哈希**）。 | 轨迹命令；`Test-Path`；§11.4 |

---

## 10. 与 `smoke-t7` / `smoke-t8` / `smoke-t9` 的逐项对照

| 维度 | t7 | t8 | t9 | **t10（本轮）** |
|---|---|---|---|---|
| 引擎 | `035edfce7` | 同 | 同 | **同（`--version` 逐字）** |
| `hoh` 二进制 | 建于 `9ff9cd2` | `0f37105` | `509ec0c` | **建于 `c932fcb`，sha `ada84958…53e4f`（仅记录）** |
| **退出码** | 0 | 3 | 2 | **0** |
| `exit_code` / `meta.exit_code` / 进程码 | — | 3/3 | `"2\n"`/2 | **`"0\n"`/0/0（三方一致）** |
| 持久化 `artifact_gate` | `launchable=true,reasons=[]` | `applicable=false,launchable=true`（假绿） | `applicable=false,launchable=false` | **`applicable=true, launchable=true, reasons=[]`（成功轮，双处自洽）** |
| 电池 | 11 步 / 9 ok | 11 步 / 11 ok（pass 2） | 未运行 | **1 遍 / 11 步全 ok** |
| `input_channel_probe` | `EDITOR_SIDE_INJECTION` | `game_process` 四元组 | 未运行 | **`GAME_INPUT_CHANNEL_OK` 但 `axis_*=null`、`moved_while_pressed=false`（**不采信**，§13.1）** |
| `input_replay` 证据形态 | 无截图/无断言 | 无截图/无断言 | 未运行 | **8 张 before/after PNG + 4 次 `position:neq`（4/4 引擎接受）** |
| 工程增量 | `A_1==A_0`（零） | `A_1=1f3d20ed…`（3 文件） | 无 `A_1` | **`A_1=ed98d1b8…`，`A_0≠A_1`，7 文件（+3282 B）** |
| `E_1` | 有（8 verified+20 gap） | 无（被 schema 拒） | 无（Tester 未运行） | **有（9 verified + 11 gap，attempt1 一次过）** |
| 失败角色 / 原因 | developer / `LimitsExceeded` | tester / `schema_failure` | developer / `contract_violation` | **无失败（`ok=true`）** |
| attempts | 3 | 6 | 3 | **4**：planner1 + developer 1+wrap-up + tester1 |
| `repair_retry_used` | false | 两层不一致 | false | **false**；`wrap_up_retry_used=true`（性质见 §5.4） |
| MCP 传输错误 / `-32602` | 1 / 0 / 1 | 0/0/0 | 0/0/0（18 处是模型裸 HTTP） | **0（无 `mcp-errors.jsonl`）/ 6 次（全部角色自己参数写错）** |
| `game_endpoint_unavailable` | — | 20 次 | 4 次 | **0 次** |
| 单条工具输出上限 | 无（15.5 MB 事故） | 无 | 无（exit 5 事故） | **64 KiB 生效 ×2，最大消息 65,886 B** |
| tokens | 22,424,721 | 24,462,425 | 8,094,119 | **25,616,513** |
| 墙钟 | 74:58 | 65:27 | 18:45（+17:53） | **54:14（单轮，无重试）** |
| E1..E6 | `not_met/met/not_met/met/met/met` | `not_met/met/not_met/met/met/met` | `not_met/不可判×5` | **`met / met / not_met(部分) / met / met / met`** |

---

## 11. 引擎身份、摘要口径、禁区自证

### 11.1 引擎身份（判据 / 记录严格分开）

| 项 | 值 | 性质 |
|---|---|---|
| **`--version`** | `4.8.dev.mono.custom_build.035edfce7` | **判据**（与任务书逐字相符；`meta.json.engine.version_string` 同值） |
| `binary.sha256` | `08483088a4a2772841cd3b4c916b2d45b3cb6255656cf3951598a86fce7e9e6a` | **仅记录**（构建非逐位可复现） |
| `size_bytes` / `mtime_unix` | 194,216,960 / 1790641862（`2026-09-29 08:31:02`） | 记录（与 `meta.json` 逐字相同） |
| 监听者 | `listener.pid=75204`、`matches_binary=true`、`path` 指向同一 exe | `meta.json.engine.listener` |
| 编辑器端点 | `GET /mcp` → `{"is_editor":true,"listening":true,"tools":154,"transport":"streamable-http", …}` | 开场实测 |

### 11.2 摘要口径（写明 + 自证 + **文化排序是口径的一部分**）

**口径（本仓既往口径，逐字照 T8 §4）**：PowerShell 5.1（culture zh-CN）`Get-ChildItem -Recurse -Force -File`；
每文件取**仓根相对**路径（`\`→`/`、**转小写**）+ 字节长度 + 小写 SHA256；三列 `\t` 连接、`\n` 分行、**无尾随换行**；
行序 **`Sort-Object`（文化排序）**；整体 UTF-8 取 SHA256。脚本：`scripts/digest.ps1`（可复跑）。

**自证（四条既有基线逐字命中）**：

```
runs/smoke-t6   135  c144ef3219e21dd322978e41a5531d53dee270619c026585505920f9277a9c03   <== 命中任务书要求的自证值
runs/smoke-t7   115  6e4c1595753c2cdefb16e4d2e5f05242ca202c70c81a93e98ae2b9c92b520fb7
runs/smoke-t8   358  6d11b2c61ec507b5f02525ddc0e7f7adb08763cd2439a4b08788b7fe51bdf5a7
runs/smoke-t9    83  541e2d814e563ba667c95bde49765d05e44cf11aa5ab90b2f44931f30136ca9d
runs/smoke-t10  232  319555896964ce1526f72a33cb239bf389fe29bcde23841764d13c57dfb38b8b   newest 2026-09-30 18:23:08
```

**"文化排序是口径的一部分"我实测**：把 `Sort-Object` 换成 `StringComparer::Ordinal`，`runs/smoke-t8` 得
**`c347bd637ab481b1ec357cbb534c1330bad18cfab85c113038fa0878e6b3d3f5`**——与 `TASK-SMOKE-T9-ACCEPTANCE.md` §2.3 记录的序数值**逐字相同**
⇒ 该口径确实**同数不同摘要**，不能省。

**工程树口径（我自己的口径，写明）**：递归、排除 `{.hoh,.godot,.import,.git}`、**树根相对**小写 POSIX 路径 + size + sha256、
`\t`/`\n` 连接、`sort()` 序数序、整体 sha256（`scripts/hashtree2.py`）。
**注意**：这与运行时的内容寻址 `A_t` 口径**不同**（运行时是 `rel\n{len}\n{bytes}\n` 流），**两者不得互换引用**；
本文引用 `1f3d20ed…`/`ed98d1b8…` 时一律标明它是**运行时身份**，引用 `5971b484…`/`c781cf81…` 时标明是**我的口径**。

### 11.3 禁区自证（开工 / 收工两点）

| 断言 | 证据 |
|---|---|
| 四条 `runs/**` 基线未被覆盖 | 摘要 + newest mtime 与记录逐字一致（§11.2）；**我全程只在 `runs/smoke-t10/**` 写入**，连临时文件都没在别处建过 |
| `PRD-mario.md` 逐字节冻结 | sha256 `4c81c3a9995f0b3afdf01421a0c3be88573cceefc284ce9bafbfda141f0f5c3a`（开工=收工= `meta.json.spec.sha256`） |
| `DECISIONS.md` 未由我编辑 | 我全程只读、零 `git add` 该文件；**我最后一次测量（提交前）** 的 sha256 为 `024fb22d2bd0f3bb5b7a9b380a87dd1edf3c11d25b2900bc8217a4dbe4bb5ef0`，开工值同。**其后它变了**（现为 `4db9c006…64b6`）——变更是**调度者的并发提交 `87adbea`（D276，+30 行）**，不是本次真机轮所为（§16.11） |
| `godot-mcp/**` 零改动 | 嵌套仓 `git -C godot-mcp/godot rev-parse HEAD = fc63af77c33368c4a1bb839c95d19750554f63a3`、`status --porcelain -uall` **0 行**、引擎树内晚于 `2026-09-30 00:00` 的文件 **0**；外层 `git ls-files godot-mcp`=**6484**（真命中）vs `godot-mcp/godot`=**0**（空判） |
| `.workspace/mario` 我只读 | 工程树：开工 `5971b484…e463`（=A0）→ 收工 `c781cf81…034a`（=A1）；**变更是本轮 Developer 按角色的写**，不是我；我未写任何工程文件 |
| 无新依赖 / 未 stage / 未 push | HEAD == `origin/master` == `c932fcb…`（**ahead 0**）；`git status --porcelain -uall` 在我提交前为空 |
| 密钥卫生 | 用配置里的真值（51 字符串）在 `runs/smoke-t10` / `.spec` / `src` / `tests` 全树比对：**含明文密钥的文件 = 0**，唯一命中是 `config/model.secret.env` 本身（C11 允许）；受控证据目录 **0** 命中 |

### 11.4 `-p` 目录的处置（如实）

- **A_0 快照与 `planner-view` 里仍在**（`versions/1f3d20ed…/-p` True、`iter-1/planner-view/-p` True）；
- **活体 `.workspace/mario/-p` 与 `A_1`/`candidate` 里已不存在**（False）——是本轮 **Developer** 用
  `rmdir "-p"` 清掉的（轨迹里 2 条命令），**不是运行时**（运行时从不删工程内容）；
- `result.json.artifact_hygiene = {suspicious_files:[], suspicious_directories:[]}` —— 因为卫生检查看到的是**已经清掉的**候选树，
  所以它**没报**；这解释了"目录卫生生效但仍为空"的表面矛盾。**空目录依旧不进内容哈希**（D271/R3 的盲区本身未变）。

---

## 12. 编辑器、进程与孤儿清理

```
开工：127.0.0.1:9877 LISTENING pid 75204（StartTime 2026/9/29 13:20:54）
      cmdline: godot.windows.editor.x86_64.mono.exe -e --path .workspace/mario --mcp-port=9877
轮中：pid 75204 存活；游戏进程 pid 109308（17:28:59，轮级）与 pid 109040（电池 play，65144）先后出现
收工：Get-NetTCPConnection -LocalPort 9877 → OwningProcess = 75204
      Get-Process | ? ProcessName -like '*godot*' → **只有 75204**
      ⇒ 编辑器**未被我启动/重启/杀掉，收工仍存活**；**无孤儿游戏进程**（t9 的 77708 类问题本轮未发生）
```

我本轮**没有手工起过任何游戏进程**（唯一一次游戏是剧本自己起的）；**没有过任何需要清理的孤儿**。

---

## 13. 两条风险旗的处置（逐条）

### 风险旗 1：不得把探针的 `GAME_INPUT_CHANNEL_OK` 当 E3 行为证据

- **处置：采信，并且本轮它正好给出了反向证明。** 电池的 `raw/input_channel_probe.json` 实测为：

```
channel: {capability: "GAME_INPUT_CHANNEL_OK",
          game_process_reachable: true,
          axis_before: null, axis_after: null, moved_while_pressed: false, pressed: true,
          detail: "game process via semantic tools: reachable=true, axis_before=None, injection accepted=true,
                   axis_after=None, axis moved=false; …"}
```

⇒ **`GAME_INPUT_CHANNEL_OK` 在 `axis=null`、`moved_while_pressed=false` 的情况下照样成立**，
与 `src/adapter/godot.rs` 的 `match (pressed, axis_after.is_some() || game_process_reachable)` 判定式一致
⇒ **它至多证明"可达 + 注入被接受"，不能证明"行为发生"**。我**不使用**它作 E3 的任何一条证据；
E3 的每条都来自 §4.2/§4.3 的逐帧位置与**引擎接受的位置断言**。**遗留风险 R-2 未关闭**（代码/文档语义仍然过宽）。

### 风险旗 2：夹具刻意排除 `semantic_summary.json`，需要则停下上报

- **处置：我不需要它，也没有触碰守卫。** 全程未读取/生成 `semantic_summary.json`；
  `git diff --stat HEAD -- src/adapter/tool_vocabulary.rs` 为空（零 diff）；`git status` 里无 `src/**` 改动。
- 我的 E3 证据**全部**来自契约内语义工具（`editor_play_scene` / `running_game_capture_screenshot` /
  `running_game_get_node_property_samples` / `running_game_assert_node_state` / `running_game_run_test_scenario` /
  `running_game_play_input_recording` / `editor_stop_scene`），无需该夹具。

---

## 14. 三个假绿陷阱的实测与正确读法

原始输出：`TASK-SMOKE-T10-evidence/round/traps_output.txt`（脚本 `scripts/traps.sh`，可复跑）。

**① `git diff` 对不存在的 pathspec 不报错**

```
$ git diff --stat -- definitely/not/a/real/path
（stdout+stderr 皆空）  trap1 exit=0
读法：**空输出 + 0** 与"没有变化"不可区分 ⇒ 断言"某路径未改"之前必须先证明该 pathspec 真命中
      （本轮对照：git ls-files godot-mcp = 6484 真命中 / git ls-files godot-mcp/godot = 0 空判）
```

**② `cmd` 里 `^` 是转义 ⇒ 所有 `rev^` 查询一律在 bash 做**

```
bash : git cat-file -e 'fe129a1^:.spec/hof-rs/tasks/TASK-DR68-ACCEPTANCE.md'  → fatal … bash-exit=128
bash : git cat-file -e 'fe129a1:.spec/hof-rs/tasks/TASK-DR68-ACCEPTANCE.md'   → bash-exit=0
bash : git cat-file -e 'HEAD^:DECISIONS.md'  → 0 ；'HEAD:DECISIONS.md' → 0      （对照：两 revision 都有 ⇒ 同号，不触发）
bash : git cat-file -e 'fe129a1^:definitely/not/here' → bash-exit=128          （对照：都不存在 ⇒ 也不是假绿形状）
cmd  : git cat-file -e fe129a1^:.spec/…/TASK-DR68-ACCEPTANCE.md → 0（CMD_EXIT_ON_SUCCESS）
cmd  : git cat-file -e fe129a1^:definitely/not/here            → 0
cmd  : git rev-parse fe129a1^                                  → fe129a163d6ca22e5e4b48b81e7229c4260b1291（^ 被吃掉）
读法：**cmd 下的 0 不携带证据力**——它实际问的是另一个 revision；有证据力的只有 bash。
```

**③ 外层仓不跟踪引擎树（同族：也不跟踪 `runs/**` 与 `.workspace/**`）**

```
outer ls-files godot-mcp        = 6484   （真命中）
outer ls-files godot-mcp/godot  = 0      （空判）
git check-ignore -v godot-mcp/godot      → .gitignore:33:godot-mcp/godot/
git diff --stat -- godot-mcp/godot/bin   → 空 + exit 0（"什么都没说"）
nested engine: HEAD fc63af77…、status --porcelain -uall = 0 行 ⇒ **引擎树未改（判据来源）**
git check-ignore -v runs/smoke-t10/meta.json → .gitignore:12:runs/
读法：③′ 外层 `git status/diff` 对本轮**全部证据**都是空判 ⇒ "未变 / 已留证"只能靠**目录摘要**（§11.2）
```

---

## 15. 本轮未验证 / 未闭合（严格区分实测与推断）

**实测（本轮有证据）**

1. E1 met：`A_0≠A_1`（7 文件）、`E_1` 被接受、整轮跑完、退出码 0 三方一致。
2. **角色 CLI 在真机上成功到达游戏端点**（Tester 执行 23 条 `hoh tools call running_game_*`，回包是真游戏载荷；全轮 `game_endpoint_unavailable`=0）；
   轮级路由 17:29:01 发布（第一个角色之前）、轮末撤下。
3. **Tester 证据形状一次通过**（attempt1、Submitted、artifact_valid=true、0 schema 失败）。
4. **E3 证据形态轮内成形、引擎接受 `position:neq`（4/4 passed）**；左右移动与跳跃成立；可交互对象不成立；胜负只失败半边成立。
5. 64 KiB 上限生效 ×2（80800→65536、147809→65536），最大消息 65,886 B，无超长回放。
6. 无修复尝试、无过期日志关门、门因正确原因打开、电池仅 1 遍。
7. **F-T10-1 实测**：`tester.attempt1.json` 非合法 JSON，破点=脱敏位置；`redact_secret_assignments` 的终止符搜索不认 JSON 转义换行（含逐行仿真复现）。
8. 四条基线未动；PRD/DECISIONS sha 未变；引擎树未改；无孤儿；编辑器 75204 存活；密钥明文 0 泄漏。
9. 三个假绿陷阱全部亲自复现并给出读法。
10. `-p` 被本轮 Developer 清掉（A0 快照里仍在，哈希不可见）。

**推断（不得当作已测）**

1. **（≈0.8）** `player.gd` 的改动质量与 E3 的行为成败不必然相关：本轮 7 个脚本都被改，但金币/敌人/方块/胜利仍不可用
   ——我没有做"改了哪些行为"的语义 diff（只做了字节 diff），故这只是读数。
2. **（≈0.7）** F-T10-1 的触发条件是"赋值后紧跟**物理换行**"（attempt2 因后面跟 `;` 而幸免）——我已用仿真复现该机制，
   但**没有**用真实二进制做"注入含 key 的 JSON 内容"的端到端复现（那需要在真机上再造一次环境转储，代价过高）。
3. **（≈0.6）** 轮级游戏（61826/pid 109308）与电池 `editor_play_scene` 返回的游戏（65144/pid 109040）**是两个不同的进程**；
   我没有找到"轮级游戏被显式停止"的记录，只能确认**收工无任何游戏进程存活**（可能是电池的 `editor_stop_scene` 一并收尾）。
   两条端口的先后关系与 PID 大小不一致（Windows PID 可回收），故**不强断言时序**。
4. **（≈0.5）** 若把 `wrap_up_retry` 也算作"第二次尝试"，则 Developer 的"两次都 `LimitsExceeded` 却仍交付"是**脆的**
   ——本轮离 `NoEngineeringWrite` 只差 wrap-up 写的那 1 个文件（F-T10-4）。

**未闭合（应回上游/回设计，本报告不修）**

1. **F-T10-1（major）**：脱敏写入破坏 JSON 轨迹 ⇒ 建议（a）终止符集补上 JSON 转义的 `\n`/`\r`（即同时匹配 `\\n`、`\\r`），
   或（b）对 JSON 文件走"解析-改写-序列化"而不是文本替换，或（c）至少**在改写后校验 JSON 可解析**，不可解析则不改写。
   并补一条**反例测试**：输入是 JSON 转义的环境转储。
2. **E3 的两项内容缺口**：可交互对象（金币/敌人/方块）与**胜利条件**——这是**产物侧**的欠缺（`qa_report` 的 update_targets 已点名）。
3. **F-T10-3**：`evidence_diff` 仍空，而本轮真改了 7 个文件 ⇒ DR-68 R7 **应当被判 fail 一次**（t9 时无法区分，现在能）。
4. **F-T10-4**：Developer 步数用尽 + wrap-up 单文件兜底 ⇒ 预算/收尾策略仍有单点脆弱。
5. **`GAME_INPUT_CHANNEL_OK` 的语义过宽**（R-2）未关闭。
6. **`-p` 的历史 A0 快照仍在**（哈希不可见）；活体已清。
7. **`artifact_hygiene.suspicious_directories` 在本轮"看不出问题"是因为候选树已被清** ⇒ 它**不能**作为"工程树没有可疑目录"的正面证据。

---

## 16. 诚实披露

1. **我只跑了这一轮**（`17:28:54 → 18:23:08`，单次 `hoh run`，退出码 0）。**没有重试、没有删除重建、没有 attempt-A/B**；
   `runs/smoke-t10` 是本轮**全新**目录。**不存在被隐藏的失败尝试**。
2. **我对 `runs/**` 的写入只发生在 `runs/smoke-t10/**`**（外加运行时自己写的同一目录）；
   **没有**在 `runs/**` 其它任何路径建过文件（**连"写过再删"都没有**）。分析脚本、原始输出全在仓外 `%TEMP%\smoke-t10\`，
   被引用的关键证据另存于受控目录 `.spec/hof-rs/tasks/TASK-SMOKE-T10-evidence/`。
3. **我做过一次"改状态"之外的机器动作**：`cargo build`（构建）、只读的进程/端口/文件检查。**没有**手工启动或停止任何 Godot 进程。
4. **我没有改** `src/**`、`tests/**`、`godot-mcp/**`、`.workspace/mario/**`（工程文件）、`PRD-mario.md`、`DECISIONS.md`。
   本轮对 `.workspace/mario` 的唯一写入来自**剧本内的 Developer**。
5. **我发现的 F-T10-1 会牵涉一个已经入库的代码路径**（`src/runtime/secrets.rs`），但**我没有修它**——
   本报告只做诊断与复现，修复应由下一批实现者按 TDD 进行（含反例测试）。
6. **我没有把环境转储写进任何被提交的证据**：受控目录里**不含**原始 env dump（我删掉了那一段，只保留
   仿真与"字节位置/解析失败"这样的结论性描述），密钥明文在全仓 0 命中。
7. **我没有声称 E2/E4/E5/E6 的证据强度超过我实际核过的范围**：E2 我核的是电池 raw 与 gate 字段；
   E4 我核的是"记录指向的文件存在 + 集合互斥"；E5 我核的是三棵树逐字节同一；E6 我核的是 QA 文本与 gap 内容。
8. **我没有用 t7/t8/t9 的任何 raw 冒充本轮证据**；所有轮内事实都指到 `runs/smoke-t10/**`。
9. **`-p` 的清理者是本轮 Developer，不是运行时**——我没有把它算作"运行时卫生生效"的证据。
10. 报告写完后不再修改；**未 push**。
11. **并发活动（如实记账，非我所致）**：我提交报告时 HEAD 为 `c932fcb` + 我的两个提交（`15e071f` 证据、`224250b` 报告）；
    **随后调度者在同一工作区落了 `87adbea`（D276，只改 `DECISIONS.md` +30 行）**，我的更正提交落在它之上（`1345a33`）。
    ⇒ 收工 HEAD 为 **`1345a33`**、`origin/master` 仍是 **`c932fcb`（ahead 4，未 push）**；
    `DECISIONS.md` 的 sha 变化**来自 `87adbea`**。这一条与 T9 轮的 R8 同族：**决策日志在被验收之前就写下了结论**，
    若本报告被验收判 fail，`D276` 需要回改。**我只执行了"跑一轮 + 取证 + 报告"**，未参与该提交。

---

## 17. 工件索引

| 类别 | 路径 |
|---|---|
| 本轮轮记录（**新目录**） | `runs/smoke-t10/**`（232 文件 / `31955589…b38b8b` / newest `2026-09-30 18:23:08`）：`exit_code`(`"0\n"`)、`meta.json`、`warnings.log`、`TOOLS.md`、`quarantine/.hoh.stale-1790760534/`、`versions/{index.json,1f3d20ed…,ed98d1b8…}`、`iter-1/{plan.md,result.json,usage.json,evidence.json,qa_report.md,logs/,traj/,planner-view/,candidate/}` |
| 电池原始证据 | `runs/smoke-t10/iter-1/candidate/.hoh/deterministic/`：`battery.json`、`deterministic.json`、`deterministic.log`、`mcp-sync.json`、`record-00..10.json`、`raw/{project_reload_and_open,scene_structure,editor_errors_baseline,play_scene_ready,scene_tree,screenshot,input_channel_probe,**input_replay**,node_and_collision_assertions,editor_stop_scene}.json` |
| E3 图片证据 | `…/candidate/.hoh/evidence/replay-{move_right,move_left,jump,move_right_release}-{before,after}.png`、`frame-00.png`、`camera-node.json`、`hud-labels.json`、`failure-state.json`、`restart-state.json`、`facing-scenario.json` |
| 受控证据目录（入库） | `.spec/hof-rs/tasks/TASK-SMOKE-T10-evidence/round/**`（result/meta/exit_code/warnings/usage/plan/qa_report/evidence/battery/deterministic/4 份 role log/console/traps/prerun） |
| 受控分析（入库） | `…/analysis/**`：`replay_calls.txt`、`replay_frames.txt`、`evidence_records.txt`、`e4_check.txt`、`tree_digests.txt`、`trajectory_analysis.txt`、`tester_cli.txt`、`tester_live_cli_payload.txt`、`midrun_game_endpoint.txt`、`redaction_defect.txt`、`developer_attempt2_tail.txt` |
| 可复跑脚本（入库） | `…/scripts/**`：`digest.ps1`、`hashtree2.py`、`treediff.py`、`replay_frames.py`、`replay_calls.py`、`evall.py`、`e4check.py`、`counts.py`、`tester_cli.py`、`ctx.py`、`region.py`、`redcheck.py`、`simred.py`、`traps.sh`、`run_round.ps1`、`peek.py`、`rawfind.py`、`dev_scan.py`、`traj_tail.py`、`evdump.py`、`traj_find.py` |
| 只读基线（未改动） | `runs/smoke-t6/**`、`runs/smoke-t7/**`、`runs/smoke-t8/**`、`runs/smoke-t9/**` |
| 规范/任务书 | `.spec/hof-rs/REQUIREMENTS.md`（E1..E6 第 110-119 行）、`.spec/hof-rs/tasks/TASK-SMOKE-T10.md`、`TASK-SMOKE-T8.md` |
| 上轮对照 | `TASK-SMOKE-T9-REPORT.md`、`TASK-SMOKE-T9-ACCEPTANCE.md`、`TASK-DR69-REPORT.md`、`TASK-DR69-ACCEPTANCE.md`、`TASK-DR70-*.md`、`TASK-DR71-*.md` |
| 相关决策 | `DECISIONS.md` **D265..D275**（已读） |

> 注：`runs/**`、`.workspace/**` 在 `.gitignore` 中（`.gitignore:12`、`:11`/`:33`），故轮内证据留在工作区而不入库；
> 受控证据目录与本报告一起入库，以免重演"证据只活在会被清理的工作树里"。
