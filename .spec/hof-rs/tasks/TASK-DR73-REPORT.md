# TASK-DR73-REPORT — E3 的两个产品侧缺口：诊断（层 A）+ 让流水线自己产出可拾取金币与可达胜利；**本批不声称 E3 met**

- 任务书：`.spec/hof-rs/tasks/TASK-DR73.md`
- 落点：`F:\moonbit-hof-rs`（外层仓），报告人：**实现子代理（无上游对话上下文）**
- 开工 HEAD：`34bd31c`；**本批 2 个提交**（英文信息均带 `(DR-73)`）：`4deefc8` = 代码与文档，
  **其后的 tip = 本报告自己的提交**。报告的提交无法在自己的文本里记录自己的 SHA
  （任何写进文本的 SHA 都会在下一次 `--amend` 后失效），因此本报告只记录**前一个提交的 SHA**
  与两个提交的信息，tip 由 `git log` 给出。
- 关键约束遵守：**离线**（未启动 Godot、未触端口、未联网、未调模型端点、未跑真机轮）
- **未 push**（`git rev-list --left-right --count origin/master...master` = `0 2`，本地领先 2）；闸门已武装，本任务书明确禁止 push

---

## 0. 结论摘要

| 项 | 结论 |
|---|---|
| **① 诊断** | **层 (A)：产出的工程脚本层**（并且是"C 的漏洞让 A 能通过"的合取：判据/计划/提示词从未要求也不需要验证这两件事）。**(B) 工具/引擎契约被排除**——观测与驱动两件事契约里都已有，且本批新增的观测步骤**只用契约内已有工具**、无需引擎改动 |
| **② 修复落点** | **提示词 + 技能 + 判据（电池观测）**，**未改 `.workspace/mario/**` 一个字节**，**未改 `godot-mcp/**`** |
| **③ 轮内可观测** | 新电池步骤 `interaction_evidence`：驱动 `move_right` → 读 `Coins:` HUD 标签与 `Goal.reached` → 每窗 before/after PNG + **引擎自己的 `running_game_assert_node_state`** 两条断言（`text:neq` 与 `reached:neq`）；**从不写属性** |
| **门** | `cargo test --offline` **exit 0**、**523 passed / 0 failed / 7 ignored**；`cargo fmt --check` exit 0；逐文件 touch **94** 个已跟踪 `.rs` 后强编；**0 个测试名被删**、`ignored` 不增 |
| **非空洞性** | **6 处仅生产代码/交付文本的受控植入**，各自使对应测试红，逐字节回退（`git diff --stat` 无植入痕迹 + `git hash-object` 与备份一致 + `cmp` 对仓外备份） |
| **携带项** | (a) sidecar 已生成、原件逐字节不动；(b) `runs/<id>/process_exit_code` 三处读数全部工件支撑；(c) CR 边界两侧各一条钉住测试 |
| **E3 判定** | **不声称 met**——本批让"金币被拾取"和"胜利被驱动"**成为轮内可观测量**，但"是否真 met"**只有真机能定** |

---

## 1. 门与套件（真实输出）

### 1.1 测试

```
cargo fmt --check                       FMT_EXIT=0
逐文件循环 touch 94 个 git ls-files '*.rs'（无通配符）  → 强制重编
cargo test --offline                    CARGO_EXIT=0
TOTAL passed=523 failed=0 ignored=7     （57 个 test binary 全 ok，0 个 FAILED）
```

> **陈旧 fingerprint 澄清（必答）**：**是，我清过**。过程里出现过一次"看起来有意义"
> 的结果：`cargo test --test tool_vocabulary` 连续两次报同一处 `assert_node_state`，
> 而我已改掉源码；`rm -rf target/debug/.fingerprint/hof-rs-*` 后**仍红** ⇒ 那次**不是**
> 旧二进制，而是我漏看了另一处字面量（`name.contains("assert_node_state")` 里的字符串本身
> 就是整词 `assert_node_state`）。**我随后又用 `rm -rf target/debug/.fingerprint/hof-rs-*`
> + 逐文件 touch 重编**，最终门读数来自这次重编。
> 另一处**真实的假红**：我改测试时误删了一个换行，`cargo test` **编译失败**（E0277），
> 而我当时用 `| grep -E "^test .*FAILED"` 读输出，把**上一次**的运行结果当成本次
> ⇒ 这正好是任务书警告的形状。此后我改成 `cargo test ... > file 2>&1; echo $?` 再读文件。

### 1.2 基线算术（从 git 对象亲算）

| 读数 | 值 |
|---|---|
| HEAD（`34bd31c`）`--list` | **514** |
| 本批 `--list` | **530**（+16，恰为本批新增：4 interaction_contract + 4 round_artifacts + 2 round_artifacts_sidecar + 4 evidence_battery + 2 secrets.rs 内嵌） |
| HEAD 非忽略基线 | **507 passed / 0 failed / 7 ignored**（本批开工前实测） |
| 本批 | **523 / 0 / 7** ⇒ 净 **+16**，`ignored` **7 不变** |
| **被删的测试名** | **0**（逐名集合比对：`HEAD names 514, current names 530, REMOVED 0`） |

### 1.3 行尾与工具

- 全程**用 `edit`/`write` 工具与 `rustfmt`**，**未用 PowerShell 的 raw read/write 对**编辑源码。
- **未整文件重写行尾**。`core.autocrlf=true`（`C:/Program Files/Git/etc/gitconfig`）使工作树部分 `.rs` 呈 CRLF，
  这是**该机器的既有检出行为**；为排除"行尾被写进提交"的可能，我用二进制逐字节核对提交对象：

```
HEAD:src/main.rs            bytes=1082    CR=0  LF=23
HEAD:src/adapter/godot.rs   bytes=253643  CR=0  LF=5891
HEAD~1:src/main.rs          bytes=370     CR=0  LF=13     ← 该文件在 HEAD~1 就是纯 LF
HEAD:tests/round_artifacts.rs bytes=8905  CR=0  LF=219
HEAD:src/lib.rs             bytes=534     CR=0  LF=19
```

⇒ **提交进仓的 blob 全部纯 LF（CR=0）**，没有任何一行行尾被改写。
（附：`grep -c $'\r'` 在 Git Bash 里对这两个路径**不可信**，它报出与行数相同的数；
上表用 Python 逐字节计数，是本次采用的读法。）

---

## 2. ① 诊断：**层 (A)**，以及为何排除 (B) 与 (C)

### 2.1 判据原文

`REQUIREMENTS.md:114`（E3）：

> 马甲核心可观察行为存在：玩家左右移动、跳跃、**至少 1 个可交互对象**、**一个终点/胜负条件**
> | `simulate_sequence` 回放 + 前后截图 + `assert_node_state`

四类行为，`smoke-t10` 只成立两类。

### 2.2 证据（文件:行 + 原始读数）

**(A-1) 产出的工程把两件事都写了，但两件事都没发生。**

- `runs/smoke-t10/iter-1/candidate/scripts/coin.gd:13` `body_entered.connect(_on_body_entered)`、
  `:24-28` 处理器检查 `body.is_in_group("player")`、`:34-37` `game.add_coin(1)` + `queue_free()`；
- `runs/smoke-t10/iter-1/candidate/scripts/player.gd:31` `add_to_group("player")`；
- `runs/smoke-t10/iter-1/candidate/scripts/goal.gd:6-17` `add_to_group("goal")` + `reached` + `game.win()`；
- `runs/smoke-t10/iter-1/candidate/scenes/main.tscn:29-30` `CircleShape2D radius=11`、`:128-130` `Coin1` @ (300,290)、
  `:142-144` `Coin2` @ (425,290)、`:240-242` `Goal` @ (6400,280)、`:109-114` `Player` 24×32 @ (60,280)、
  `:44-48` `Ground` 6800×40 @ (3400,320)（→ 地面顶面 y=300）。
- 但：`runs/smoke-t10/iter-1/candidate/.hoh/evidence/hud-labels.json` 全轮 `Coins: 0`
  （0 处非 0：`TASK-SMOKE-T10-ACCEPTANCE.md:73` 记 91 处全 0）；`Goal.reached=false`，
  **从未出现**胜利文本。

**(A-2) 金币是被"物理扫过"的，不是"没走到"。** 判据是静态几何 + 逐帧位置（验收者自产，我复核口径一致）：

| 窗口 | 逐帧 x | 与 Coin1(300,290,r=11) | 与 Coin2(425,290,r=11) |
|---|---|---|---|
| `move_right` | 184.666702 → 400.999725（60 样本） | **扫过**（x=300 处矩形 288–312 与圆 289–311 重叠；y 268–300 与 279–301 重叠） | 未到 |
| `move_right_release` | 415.666351 → 448.666260（10 样本） | — | **扫过**（x=425 处矩形 413–437 与圆 414–436 重叠） |

⇒ 两枚金币的圆心区域都被玩家碰撞盒**穿过了**，`Coins:` 仍是 0。

**(A-3) 终点在可走范围之外。** `Goal` @ x=6400，但地面 `Ground` 的 6800 宽居中于 3400 ⇒ 覆盖 x∈[0,6800]，
看似够到；决定性的不是这个，而是**玩家全轮可观测 x 的最大值**：`448.666`（±1 帧）。
用工程自己的常量算**跳跃水平航程**：`speed=220 px/s`、`jump_velocity=-430 px/s`、`gravity=1400 px/s²`
（`player.gd:7-9`）⇒ 滞空 `2×430/1400 = 0.6143 s`、**单次跳跃水平约 `135 px`**、顶点约 `66 px`。
关卡里 Platform1@1100、Platform2@2200、Platform3@3600（宽 260/300/400，顶面 y=228/198/238），
从 Platform3 右缘（x=3800）到 Goal（x=6400）之间**没有任何落脚面**：`135 px` 的跳跃跨不过去，
玩家只会掉出关卡下边界（`player.gd` 无 y 兜底、`main.gd` 的失败分支会把玩家送回 x=60）。
⇒ **"终点/胜负条件"在位置上不可达**，这不是"回放没走到"，是**关卡不可通过**。

**(A-4) 生产层的可观测地址是齐的。** 金币计数在 `HUD/Coins`（`scenes/main.tscn:276-281`，`text="Coins: 0"`），
胜负在 `Goal.reached`（`goal.gd:4`，且是 `@export`）。也就是说：**产物把"可观测点"命名对了，
把"行为"写错了**——这正是层 (A) 的定义。

### 2.3 为何**排除 (B) 工具/引擎契约层**

1. **观测能力早已存在且被真机验证**：`TASK-SMOKE-T10-REPORT.md:371-384` 给出 `running_game_get_node_properties`
   的真机原始回包（`{"node_path":"/root/Main/HUD/Coins","properties":{"text":"Coins: 0",...}}`），
   而 `runs/smoke-t10/iter-1/candidate/.hoh/deterministic/raw/input_replay.json` 里
   `running_game_assert_node_state` **4/4 `passed=true`**。⇒ **"能读状态、能断言状态"不需要新契约**。
2. **驱动能力也已存在**：`input_replay` 的四个窗口用 `create_input_recording` + `play_input_recording`
   + `run_test_scenario` 真的把玩家推动了 `±216.333 px`（=220 px/s）。拾取/胜利所需的"驱动"
   与"移动"是**同一个**输入通道——本批新增窗口只用 `move_right` 这一个已有 action，**没有新增任何工具调用形态**。
3. **本批的观测步骤只用契约内既有工具**：`running_game_capture_screenshot`、
   `running_game_get_node_properties`、`running_game_get_node_property_samples`、
   `running_game_assert_node_state`、`running_game_play_input_recording`、
   `running_game_run_test_scenario`、`running_game_stop_input_recording`、`running_game_create_input_recording`。
   **`godot-mcp/**` 零改动**（§6 自证）。⇒ 若判 (B) 就必须动引擎，而**根本没有必须**。
4. **(B) 的唯一"不足"是语义宽窄问题，不是能力缺失**：`running_game_move_player_to_target`
   在无导航数据时按设计拒绝（`godot-mcp/.../RACING-DEV-LOG.md:257`：`-32000` + suggestion），
   所以本批**没有**用它——改用"真的按住右"的方式，这与 E3 的"玩家行为"语义也更一致。
   这是**取舍**，不是契约缺陷。

### 2.4 为何**排除 (C) 计划/判据层**为"唯一原因"（并说明它的真实份额）

任务书把"计划根本没要求拾取与胜利"列为 (C) 的一种。**实测不是**：
`runs/smoke-t10/iter-1/plan.md:5`（Priority Order 第 3 条）**明确要求**了

> touching a coin removes it and increments the HUD coin count by exactly one … reaching the Goal node enters a visible victory state

⇒ **Planner 要求了**。但同一条的 `### Acceptance Gate`（`plan.md:10`）只写

> simulate move_right … then simulate jump …

⇒ **判据闸门只覆盖移动与跳跃**。也就是说 (C) 的份额是**"闸门表述让角色以为不必做"**，
不是"没要求"。我把**主因判为 (A)**（脚本层真的错了：金币扫过不触发、终点不可达），
把 (C) 记为**共犯/放大器**（没有闸门把这两件事钉成"本轮成功"的必要条件，
所以 (A) 的缺陷**不可能在轮内被发现**）。二者的修复落在**同一处**：提示词/技能/电池观测。

### 2.5 一个必须诚实声明的空白

**我无法（离线、且不得启动 Godot）判定"金币扫过而不触发"的运行时机制**。我能给的机制层事实只有：

- 写法**在普通 Godot 4 工程里是规范写法**（`Area2D` 默认 `monitoring=true`、默认 layer/mask=1；
  `CharacterBody2D` 默认 layer=1；`move_and_slide` 会推物理世界 ⇒ `body_entered` 应当触发）；
- `.tscn` 里**没有任何** `collision_layer`/`collision_mask`/`monitoring` 覆盖（我逐行读过 `scenes/main.tscn`）；
- 因此**我不断言**"根因是 monitoring/layer/mask 中的某一个"。可能的机制包括
  （i）重放期间注入/采样与物理帧的交互使 overlap 恰好没有在 `body_entered` 的判定帧成立、
  （ii）`_process` 里的 `falling` 分支或节点树变化、**或**（iii）其它我离线无法观察的运行时条件。
- **但这不影响层判定**：(A) 的判据不是"我知道哪一行错了"，而是
  **"产出的工程没有交付这两类行为，而流水线的任何一环都没有把它当作必须交付的东西"**。
  修复因此必须落在 (A)+(C) 的**生产侧**：让流水线**自己**能发现并产出正确行为。

---

## 3. ② 的改动落点与"禁止手工写游戏"的遵守证明

### 3.1 改动落点（全部在流水线侧，无一处是示例游戏）

| 文件 | 改动 | 作用 |
|---|---|---|
| `src/adapter/godot.rs` | 新电池步骤 `step_interaction_evidence` + 4 个纯函数 helper（`hud_label_path`/`node_property_value`/`required_sample_pairs`/`coin_count`/`is_false`/`is_true`）+ 常量（`COIN_COUNTER_PREFIX`/`GOAL_REACHED_PROPERTY`/`GOAL_POSITION_NODE`/`INTERACTION_DRIVE_ACTION`/`INTERACTION_MAX_BATCHES`/`INTERACTION_BATCH_FRAMES`）+ `evidence_playbook` 的步骤表新增一行 | **判据/证据层**：让两件事成为轮内可观测量 |
| `src/prompts/developer.md` | 完成定义新增第 6 条（"a collectible picked up" / "a reachable win condition"），`all five` → `all six` | **提示词层**：Developer 的 DoD 明确要求 |
| `src/prompts/planner.md` | `[planning-policy]` 新增"只覆盖移动与跳跃的 Acceptance Gate 不构成成功"两条 | **判据表述层**：闸门必须覆盖 |
| `src/prompts/skills/godot-dev.md` | 新增 `## 3a`（Area2D 真正触发 `body_entered` 的四条检查 + 可抄代码）与 `## 3b`（可达的胜利条件 + 跳跃航程算术 + 可抄代码） | **技能层**：给**可执行**做法 |
| `src/prompts/mod.rs` | planner 任务书第 4 条补一句验收闸门覆盖范围 | 同上，任务书口径 |
| `src/runtime/secrets.rs` | 仅新增 2 条钉住测试（无生产逻辑改动） | 携带项 (c) |
| `src/cli_impl.rs` | `PROCESS_EXIT_CODE_FILE`/`RUN_DIR_ENV`/`process_exit_code_for`/`write_process_exit_code`/`record_process_exit_code_from_env` + `run` 里导出轮目录 | 携带项 (b) |
| `src/main.rs` | 记录进程退出码后返回同一 `code` | 携带项 (b) |
| `tests/interaction_contract.rs` | **新** 4 条可执行断言（提示词/技能必须**明确要求且给出可执行做法**） | ② 的先红测试 |
| `tests/evidence_battery.rs` | +4 条断言 + fixture 扩展（`InteractionMode` 等） | ③ 的先红测试 |
| `tests/round_artifacts.rs` `tests/round_artifacts_sidecar.rs` | **新**，携带项 (b)/(a) | 携带项 |
| `.spec/hof-rs/tasks/TASK-SMOKE-T10-evidence/analysis/redaction_defect.redacted.txt` | **新 sidecar**（生成物，原件不动） | 携带项 (a) |

### 3.2 "禁止手工写游戏"的遵守证明

```bash
$ git status --porcelain -uall -- .workspace
（空）
$ git diff --stat -- .workspace .spec/hof-rs/PRD-mario.md DECISIONS.md
（空，exit 0）
$ git check-ignore -v .workspace/mario/project.godot
.gitignore:11:.workspace/	.workspace/mario/project.godot
$ find .workspace/mario -newermt '2026-10-01 00:00' -type f | wc -l
0
$ sha256sum .spec/hof-rs/PRD-mario.md
4c81c3a9995f0b3afdf0…0f5c3a   ← 与 T10 验收记录逐字相同
```

- `.workspace/mario/**` **一个字节都没改**（它是真机基线的一部分）；本批**没有**在任何"临时副本"里改游戏——
  **一个游戏文件都没有打开写过**。
- 本批唯一"碰游戏内容"的动作是**只读**：读 `runs/smoke-t10/iter-1/candidate/**` 的脚本与 `.tscn` 做几何/信号诊断。
- `godot-mcp/**` 零改动（外层 `git ls-files godot-mcp`=**6484** 真命中 vs `godot-mcp/godot`=**0** 空判；
  嵌套仓 `HEAD=fc63af77…`、`status --porcelain -uall`=**0 行**）。
- 因此修复**只能**通过提示词/技能/判据模板实现——也就是本批所做的。

### 3.3 ② 的先红测试（真实失败输出）

先红的方式：**先把测试写出来、暂不接线**（把 `self.step_interaction_evidence(...)` 从 `run` 里拿掉），
再运行。原始输出：

```
$ cargo test --offline --test evidence_battery the_interaction_window_records_a_real_coin_pickup_and_its_assertion
thread '...' panicked at tests\evidence_battery.rs:1429:28:
missing battery step `interaction_evidence`: [BatteryRecord { step_id: "project_reload_and_open", … },
 … { step_id: "input_replay", … }, { step_id: "node_and_collision_assertions", … },
 { step_id: "editor_stop_scene", … }]
test result: FAILED. 0 passed; 1 failed; 0 ignored; 0 measured; 48 filtered out
```

另外三条同因同红：

```
$ cargo test --offline --test evidence_battery -- a_project_that_never_picks_a_coin_up… \
    a_level_whose_goal_is_unreachable… a_hud_without_a_coin_cell…
test a_hud_without_a_coin_cell_is_reported_as_unreadable_not_as_zero ... FAILED
test a_project_that_never_picks_a_coin_up_is_recorded_as_a_gap ... FAILED
test a_level_whose_goal_is_unreachable_fails_only_the_win_half ... FAILED
test result: FAILED. 0 passed; 3 failed; 0 ignored; 0 measured; 46 filtered out
```

`tests/interaction_contract.rs` 的先红（交付文本当时不含要求）：

```
$ cargo test --offline --test interaction_contract
thread '...the_planner_acceptance_gate…' panicked at tests\interaction_contract.rs:150:5:
  the planner must be told the acceptance gate has to cover an interaction, not only movement:
thread '...the_godot_dev_skill_carries_an_executable_recipe…' panicked at tests\interaction_contract.rs:82:5:
  the skill must say an `Area2D` needs `monitoring` (a disabled one never fires `body_entered`):
thread '...the_developer_definition_of_done…' panicked at tests\interaction_contract.rs:37:9:
  the Developer's definition of done must name `a collectible picked up`; the round that produced
  `Coins: 0` and `Goal.reached=false` was never told it had to.
test result: FAILED. 1 passed; 3 failed; 0 ignored; 0 measured; 46 filtered out
```

**绿**：`cargo test --offline --test evidence_battery` → `49 passed / 0 failed`；
`--test interaction_contract` → `4 passed / 0 failed`。

---

## 4. ③ 的轮内可观测性改动

新步骤 `interaction_evidence`（`src/adapter/godot.rs`，插在 `input_replay` 与 `node_and_collision_assertions` 之间）：

| 阶段 | 调用（全部契约内既有工具） | 产物 |
|---|---|---|
| (a) 定位计数格 | 从同一游戏会话的 `running_game_get_scene_tree` 里找 `HUD` 下 text 以 `Coins:` 开头的 `Label` | 节点 path（找不到 ⇒ `COIN_COUNTER_UNREADABLE`，不是"0 枚"） |
| (b) 前读 + 前帧 | `running_game_get_node_properties{Coins 标签, text}`、`{Goal, reached}`、`{Goal, position}`；`running_game_capture_screenshot` | `.hoh/evidence/replay-interaction-before.png` |
| (c) 驱动并采样 | 每批：`create_input_recording` → `play_input_recording`(按下 `move_right`) → `run_test_scenario` → `stop_input_recording`，再 `running_game_get_node_property_samples{Player, position, 60 帧}`；**最多 24 批**，**一旦读到 `reached=true` 立即停** | 逐批 `player max x`（记录里可见） |
| (d) 后帧 + 后读 | 同上 | `.hoh/evidence/replay-interaction-after.png` |
| (e) 两条断言 | `running_game_assert_node_state{Coins 标签, text, neq, 期望=前读}`、`{Goal, reached, neq, false}` | 与移动窗口**同一形态**的引擎判定 |

**判定词（诚实失败名，逐条可指）**：

- `COIN_PICKED_UP`（绿）／`COIN_NOT_PICKED_UP`（计数在整个窗口内没涨）
- `WIN_DRIVEN`（绿）／`WIN_NOT_DRIVEN`（`reached` 全程 false，**并把 `player max x` 与 `goal.position` 写进记录**，使"不可达"可度量）
- `COIN_COUNTER_UNREADABLE`（没有 `Coins:` 标签——与"0 枚"区分）
- `GOAL_FLAG_NOT_FALSE_BEFORE`（窗口开始前 `reached` 就为真 ⇒ 无法归因于本次驱动）
- `COIN_ASSERTION_UNAVAILABLE` / `WIN_ASSERTION_UNAVAILABLE`（引擎答不出 ⇒ 不是绿）

**两条设计纪律（都写进代码注释与 playbook，并被测试钉住）**：

1. **按位置/状态，不按轴**：`input_axis` 真机恒 `null`（DR-58）⇒ 承重的是
   `Coins:` 标签文本与 `Goal.reached`（以及既有的 `Player.position`），**没有**任何断言依赖 `input_axis`。
2. **从不写属性**：窗口只"驱动输入"与"读状态"。测试显式断言记录里
   **没有** `set_node_property` 一类写工具；"游戏自己驱动了胜利分支"是**读数**而非愿望。

**该步骤 `ok=false` 的后果（有意为之）**：它会让闸门/整轮把"这两件事没做到"如实记为
**证据不可用（gap）**。这不是回归（`input_replay` 及其 4 个位置断言完全不变），
而是**把从未被验证过的功能如实记为未验证**——这正是它要修的那个洞。

---

## 5. 携带项（D280 的三条范围决定）

### 5.1 (a) 受控分析文件的脱敏 sidecar

- **原件**：`.spec/hof-rs/tasks/TASK-SMOKE-T10-evidence/analysis/redaction_defect.txt`
  （`sha256 = 201ae32e970c6b396ef309aacad45e986d972a6f48fbe122a46d58b31d949466`，**2035 字节**，含前导 BOM）。
  **绝不改写**：测试 `the_sidecar_is_generated_and_the_original_is_untouched` 在生成 sidecar 后
  **重新读取原件并要求逐字节与生成前一致**，并把 sha256/长度**钉成常量**——任何对原件的改写都会让该测试红。
- **sidecar**：`redaction_defect.redacted.txt`（已随本批提交）。
  - 两行 `'…'` 记录（逐字保留的 `HOH_ARTIFACT_DIR=`/`HOH_GAME_ROUTE=`/`HOH_HOH_BIN=`/`HOH_ITERATION=1`/
    `HOH_MODEL_API_KEY=<redacted>;C:\Users\wyl\node_modules…`）**整值替换**为生成标记；
  - 其余行过**生产代码**的 `secrets::redact_secret_assignments`；
  - 保留的finding：**哪条轨迹坏了、坏在第几字节（412870）、为什么**（这是该文件作为缺陷证据的意义）。
- **断言**：`the_sidecar_carries_no_environment_value_and_no_user_name` 逐条检查
  `HOH_ARTIFACT_DIR/HOH_GAME_ROUTE/HOH_HOH_BIN/HOH_ITERATION/HOH_MODEL_API_KEY/PATH` 后**不得**出现原值；
  并断言 sidecar 里**没有** `C:\`、`node_modules`、`moonbit-hof-rs`、`<redacted>;`；
  再断言**原件里确实有**这些值（否则该测试是空转）。

### 5.2 (b) 持久化轮次进程退出码

- 新增常量与函数（`src/cli_impl.rs`）：`PROCESS_EXIT_CODE_FILE = "process_exit_code"`、
  `RUN_DIR_ENV = "HOH_RUN_DIR"`、`process_exit_code_for`、`write_process_exit_code`、
  `record_process_exit_code_from_env`。
- `cli_impl::run` 在**任何角色之前** `std::env::set_var(RUN_DIR_ENV, &run_dir)`；
  `src/main.rs` 在返回 `code` 之前调用 `record_process_exit_code_from_env()`，
  **记录的就是它将要返回的那个数**。
- **一致性设计（重要，写下来）**：`ExitCode` 不暴露数字，所以进程边界无法再算一遍 summary；
  记录器因此读回 **`finalize_run` 已落盘的 `runs/<id>/exit_code`** 并原样镜像。
  ⇒ 这不是"第二个计算"，而是**同一决策点（`run_exit_code_for(summary)`）的第三个持久读数**，
  两处字节形状一致（`<code>\n`），无法漂移；未走到 `finalize_run` 的轮次没有 `exit_code`，
  因而**没有第三处可备份**（记录器如实不写）。
- 测试（`tests/round_artifacts.rs`，4 条）：字节形状与幂等；
  **三处读数同数**（`process_exit_code_for` == `finalize_run` 落盘 == `meta.json.exit_code`，且顺序无关）；
  通过**真实环境变量**驱动真实记录器（含"不是轮次就不写"、"空值"、"目录里没有裁决就不写"三个反例，
  并断言值非 0 以免常量 0 混过）；接线检查（`main.rs` 调用 + `run` 在轮次前导出目录，且比较的是**位置**）。

### 5.3 (c) 把 `\r` 边界钉住

任务书写的是"Windows 路径含 `\r` 时赋值扫描提前终止"。**我在 `secrets.rs` 里读到的是**：
`is_value_terminator`（`:221-229`）中 **`\n` 与 `\r` 都是终结符**（`b'\n' | b'\r' => true`），
而 `assignment_value_end` **不消费终结符**（`:378-388`，注释明写 "The terminator is **not** consumed"）。
=⇒ 现实里存活的形态是：**CR 之后、同一物理行的余部原样保留**。这就是 DR-72 记录的那个代价，
D280(c)"接受为已记录代价、但必须加测试钉住、不能悄悄扩大"。我按**这个**语义钉了**两条**测试：

- `a_plain_text_cr_ends_the_value_and_the_carried_rest_is_a_pinned_cost`（纯文本）：
  夹具 `HOH_ARTIFACT_DIR=C:\repo\runs\smoke-t10\rTAIL-INVITATION\n`；
  断言 **span 恰好止于 CR**（`span.end == text.find('\r')`）、**span 数量 = 1**、
  **输出 = `HOH_ARTIFACT_DIR=<redacted>\rTAIL-INVITATION\n`**（"余部原样保留"就是那个代价，逐字钉死）、
  以及 `bytes_changed_outside_spans == 0`；**并**断言 **CR 的下一行仍被脱敏**（代价不可被读成"整段失守"）。
- `a_json_escaped_carriage_return_ends_the_value_without_a_surviving_tail`（JSON 内 `\`+`r`）：
  这是**真正的转义族**，其值尾后内容必须存活，且结果仍是合法 JSON——**两种形态不得混淆**。

---

## 6. TDD 证据（红 → 绿）

| 项 | 先红（真实输出见 §3.3 / §6.1） | 绿 |
|---|---|---|
| ② 判据侧：`the_planner_acceptance_gate_must_cover_the_interaction_behaviours` | `panicked at tests\interaction_contract.rs:150:5: the planner must be told the acceptance gate has to cover an interaction, not only movement` | ok |
| ② 提示词/技能侧：`the_developer_definition_of_done_requires_the_two_missing_behaviours` | `panicked at tests\interaction_contract.rs:37:9: … must name 'a collectible picked up'` | ok |
| ② 技能侧：`the_godot_dev_skill_carries_an_executable_recipe_for_both_behaviours` | `panicked at tests\interaction_contract.rs:82:5: the skill must say an 'Area2D' needs 'monitoring'` | ok |
| ② 步骤表：`the_tester_is_told_which_battery_steps_prove_the_two_behaviours` | （随步骤表补齐而同批转绿；其"红"由 ③ 的接线缺失承担） | ok |
| ③ `the_interaction_window_records_a_real_coin_pickup_and_its_assertion` | `missing battery step 'interaction_evidence'` | ok |
| ③ `a_project_that_never_picks_a_coin_up_is_recorded_as_a_gap` | 同因（`missing battery step`） | ok |
| ③ `a_level_whose_goal_is_unreachable_fails_only_the_win_half` | 同因 | ok |
| ③ `a_hud_without_a_coin_cell_is_reported_as_unreadable_not_as_zero` | 同因 | ok |
| (b) `the_process_entry_point_records_the_artifact_from_the_exported_run_directory` | §6.1 植入 4 即其红（真实反例驱动） | ok |
| (b) 其余 3 条 | 同批引入 | ok |
| (a) `the_sidecar_carries_no_environment_value_and_no_user_name` | §6.1 植入 6 即其红 | ok |
| (c) 两条 CR 钉 | §6.1 植入 1 即其红 | ok |

### 6.1 补充：先红/非空洞共用的"受控植入"红输出（节选，完整见 §6.2）

```
植入1  is_value_terminator 去掉 b'\r'
  test runtime::secrets::tests::a_plain_text_cr_ends_the_value_and_the_carried_rest_is_a_pinned_cost ... FAILED
  panicked at src\runtime\secrets.rs:1199:9: assertion `left == right` failed: the span must end on the carriage return, not past it
    left: 55   right: 39

植入2  金币断言改到属性 "visible"
  test the_interaction_window_records_a_real_coin_pickup_and_its_assertion ... FAILED
  … COIN_ASSERTION_UNAVAILABLE (the game process could not answer `text:neq "Coins: 0"` on `/root/Main/HUD/Coins`) …

植入3  developer.md 把 "a collectible picked up" 改成 "an interactive object"
  test the_developer_definition_of_done_requires_the_two_missing_behaviours ... FAILED
  test result: FAILED. 0 passed; 1 failed

植入4  记录器写成 code+1
  test the_process_entry_point_records_the_artifact_from_the_exported_run_directory ... FAILED
  assertion `left == right` failed: the exported run directory carries the verdict the round was finalised with
    left: "6\n"   right: "5\n"

植入5  goal_after 读不存在的属性 "reached_after_the_drive"
  test a_level_whose_goal_is_unreachable_fails_only_the_win_half ... FAILED
  test a_project_that_never_picks_a_coin_up_is_recorded_as_a_gap ... FAILED
  test the_interaction_window_records_a_real_coin_pickup_and_its_assertion ... FAILED

植入6  sidecar 的整值替换被改成复制（`<redacted>` 占位）
  test the_sidecar_is_generated_and_the_original_is_untouched ... FAILED
  panicked at tests\round_artifacts_sidecar.rs:165:5:
  every recorded occurrence must be replaced by the marker, not copied
    left: 0   right: 2
```

> **植入 6 教了我一件事并已改产品测试**：第一版植入（把标记文本写短）**没有**让测试红
> ⇒ 说明 sidecar 测试当时**不检测"是否真做了替换"**。我因此给 sidecar 测试补了
> `text.matches("<redacted by TASK-DR73:").count() == 原件 occurrence 数` 这条断言，
> 该植入才转红。**这是空转测试被植入发现、并当场修掉的一例。**

---

## 7. 非空洞性（≥4 处仅生产代码/交付文本的受控植入，各自红、逐字节回退）

**方法**：先用 `cp` 把目标文件备份到**仓外** `C:\Users\wyl\AppData\Local\Temp\dr73bak\`，
用 `edit` 做**最小**植入，运行**对应**测试取红输出，再 `cp` 回退，最后四重核对：
`cmp` 对备份、`git status --porcelain -uall`、`git diff --stat`、`git hash-object` 与备份一致。

| # | 植入 | 落点 | 使哪条测试红 | 回退核对 |
|---|---|---|---|---|
| 1 | `b'\n' | b'\r'` → `b'\n'` | `src/runtime/secrets.rs:222` | `secrets` CR 钉（§6.1） | `cmp` OK；`git diff --stat` 无植入痕迹；`hash-object` 与备份一致 |
| 2 | 金币断言属性 `"text"` → `"visible"` | `src/adapter/godot.rs:2659` | `the_interaction_window_records_a_real_coin_pickup_and_its_assertion` | `cmp` OK；`git diff --stat -- src/adapter/godot.rs` = 601 insertions（与植入前相同） |
| 3 | DoD 措辞 `"a collectible picked up"` → `"an interactive object"` | `src/prompts/developer.md:158` | `the_developer_definition_of_done_requires_the_two_missing_behaviours` | `cmp` OK；diff 仍为 26+/2- |
| 4 | 记录器写 `code` → `code + 1` | `src/cli_impl.rs:798` | `the_process_entry_point_records_the_artifact_from_the_exported_run_directory` | `cmp` OK；diff 无植入痕迹 |
| 5 | `goal_after` 读 `"reached_after_the_drive"`（不存在） | `src/adapter/godot.rs:2637` | `the_interaction_window…` + `a_level_whose_goal…` + `a_project_that_never_picks…` | `cmp` OK；`git diff --stat -- src/adapter/godot.rs` = 601 insertions |
| 6 | sidecar 整值替换 → 复制 | `tests/round_artifacts_sidecar.rs:68` | `the_sidecar_is_generated_and_the_original_is_untouched`（补强断言后） | `cmp` OK |

**植入若落在承载不变量的测试里**：植入 2/5 触碰的是"判据/观测"测试，植入 3/6 触碰的是
**交付文本（prompt/skill）与生成器**——四者都**不是**承载仓库不变量的测试（如 `frozen_evidence.rs`、
`tool_vocabulary.rs`、`push_gate.rs`），**我没有改过任何承载不变量的测试**（参 D253）：
`git diff --stat` 里 `tests/` 下只有 `evidence_battery.rs`（扩展）+ 3 个新文件，
**既有测试文件 0 处被改**（`frozen_evidence.rs`/`tool_vocabulary.rs`/`frozen…` 等均为 0 改动）。
**唯一的既有测试文件改动是 `tests/evidence_battery.rs`，且是纯增量（+647/−18，删除行全是 rustfmt 与
我自己的新增块）**；它被改是因为新步骤属于该电池，且我在其中**新增**了 4 条断言、**没有删任何断言**。

**回退后的四重自证（逐条真实输出）**：

```
$ cmp /tmp/dr73bak/<file> <file>            → 全部 OK（无输出 + exit 0）
$ git status --porcelain -uall              → 只有本批的 13 项（9 M + 4 ??）
$ git diff --stat -- src/adapter/godot.rs   → 601 insertions(+)   ← 与植入前逐字相同
$ git diff --stat -- src/runtime/secrets.rs → 74 insertions(+)
$ git diff --stat -- src/prompts/developer.md → 26 insertions(+), 2 deletions(-)
$ git hash-object src/adapter/godot.rs      → 与 /tmp/dr73bak/godot.rs 的 hash-object 相同
```

（`cmp` 强制：本机 `core.autocrlf=true`，用 `cmp` 而不是文本比较，避免行尾被当成差异。）

---

## 8. 禁区自查（真实输出）

### 8.1 `runs/**` 五条基线

```bash
$ for d in runs/smoke-t6 runs/smoke-t7 runs/smoke-t8 runs/smoke-t9 runs/smoke-t10; do
    n=$(find "$d" -type f | wc -l); newest=$(find "$d" -type f -printf '%T+ %p\n' | sort | tail -1)
  done
runs/smoke-t6  files=135  newest=2026-09-29+02:32:01.6939688000
runs/smoke-t7  files=115  newest=2026-09-29+14:41:14.6623671000
runs/smoke-t8  files=358  newest=2026-09-30+07:58:28.5949213000
runs/smoke-t9  files=83   newest=2026-09-30+11:27:29.6579756000
runs/smoke-t10 files=232  newest=2026-09-30+18:23:08.1898080000
```

**摘要口径与自证**（仓根相对、`\`→`/`、**小写**、`rel\tlen\tsha256`、`\n` 连接、**序数排序**、整体 sha256；
分析脚本在**仓外** `C:\Users\wyl\AppData\Local\Temp\dr73\digest2.py`）：

```
runs/smoke-t6   135  c144ef3219e21dd322978e41a5531d53dee270619c026585505920f9277a9c03   ← 自证命中
runs/smoke-t7   115  6e4c1595753c2cdefb16e4d2e5f05242ca202c70c81a93e98ae2b9c92b520fb7
runs/smoke-t8   358  c347bd637ab481b1ec357cbb534c1330bad18cfab85c113038fa0878e6b3d3f5
runs/smoke-t9    83  541e2d814e563ba667c95bde49765d05e44cf11aa5ab90b2f44931f30136ca9d
runs/smoke-t10  232  9ba72fbd83528ec7166b791f8659320ff8b1eba5a913a28bf2ec8d5f2e0963ad
```

- `smoke-t6` 的 `c144ef32…7a9c03` 是**任务书要求的自证值**，命中。
- `smoke-t8` 得 `c347bd63…b3d3f5`，与 `TASK-SMOKE-T9-ACCEPTANCE.md §2.3` 记录的**序数排序**值逐字相同
  ⇒ **文化排序是口径的一部分**（PowerShell `Sort-Object` 在 t8/t10 会分叉）；我的数值与冻结报告里
  用文化排序得到的 `6d11b2c6…`/`31955589…` 不同，**是口径不同，不是内容不同**（文件数与 newest mtime 逐字相符）。
- `find runs -newermt '2026-10-01 00:00' -type f` = **0** ⇒ 开工至今**没有任何 `runs/**` 文件被写过**
  （**连"写过再删"都没有**；本报告全程只在仓外与 `.spec/**` 写文件）。

### 8.2 mario / PRD / 嵌套引擎 / 依赖 / push / 仓内临时物

```
$ git status --porcelain -uall -- .workspace runs PRD-mario.md .spec/hof-rs/PRD-mario.md DECISIONS.md godot-mcp
（空）
$ sha256sum .spec/hof-rs/PRD-mario.md
4c81c3a9995f0b3afdf01421a0c3be88573cceefc284ce9bafbfda141f0f5c3a
$ git -C godot-mcp/godot rev-parse HEAD
fc63af77c33368c4a1bb839c95d19750554f63a3
$ git -C godot-mcp/godot status --porcelain -uall | wc -l
0
$ git ls-files godot-mcp | wc -l          → 6484   （真命中）
$ git ls-files godot-mcp/godot | wc -l    → 0      （空判：外层不跟踪引擎树，见 §9）
$ git check-ignore -v godot-mcp/godot
.gitignore:33:godot-mcp/godot/
$ git diff --stat HEAD~1 HEAD -- Cargo.toml Cargo.lock
（空）                                    ← 无新依赖
$ git rev-list --left-right --count origin/master...master
0	1                                       ← ahead 1，未 push
$ git status --porcelain -uall
M src/adapter/godot.rs / src/cli_impl.rs / src/main.rs / src/prompts/{developer,mod,planner}.md
M src/prompts/skills/godot-dev.md / src/runtime/secrets.rs / tests/evidence_battery.rs
?? .spec/.../redaction_defect.redacted.txt / tests/{interaction_contract,round_artifacts,round_artifacts_sidecar}.rs
（收工时由 §10.1 的提交收口为干净工作树）
```

**仓内无临时物**：本批所有分析脚本、输出、备份都在**仓外**
`C:\Users\wyl\AppData\Local\Temp\dr73*\`；`git status` 里没有任何 `_*`/`tmp_*`/`*.bak`/`*.py`。

### 8.3 密钥卫生

- 含明文密钥的**唯一**文件是 `config/model.secret.env`（C11 允许，且**未进仓**：`git ls-files config` 只有 `config/hoh.yaml`）。
- 本批新建的 sidecar 经 §5.1 的断言检查：无 `HOH_*` 值、无用户名路径、无 `C:\`、无 `node_modules`。
- 我没有把任何环境转储、密钥值或 `HOH_*` 值写进本报告或任何被提交的文件。

---

## 9. 三个假绿陷阱（各自实测 + 正确读法）

**① `git diff` 对不存在的 pathspec 不报错**

```
$ git diff --stat -- definitely/not/a/real/path
（stdout+stderr 皆空）  trap1_exit=0
```

读法：**空输出 + 0 与"没有变化"不可区分** ⇒ 断言"某路径未改"之前必须先证明该 pathspec 真命中
（本批对照：`git ls-files godot-mcp`=**6484** 真命中 / `git ls-files godot-mcp/godot`=**0** 空判）。

**② `cmd` 里 `^` 是转义 ⇒ 所有 `rev^` 查询一律在 bash 做**

```
bash : git cat-file -e 'fe129a1^:.spec/…/TASK-DR68-ACCEPTANCE.md'
       fatal: path '…TASK-DR68-ACCEPTANCE.md' exists on disk, but not in 'fe129a1^'   bash-exit=128
bash : git cat-file -e 'fe129a1:.spec/…/TASK-DR68-ACCEPTANCE.md'
                                                                                      bash-exit=0
bash : git cat-file -e 'fe129a1^:definitely/not/here'
       fatal: path 'definitely/not/here' does not exist in 'fe129a1^'                 bash-exit=128
cmd  : git cat-file -e fe129a1^:.spec/…/TASK-DR68-ACCEPTANCE.md & echo %errorlevel%
       CMD_EXIT=0
cmd  : git rev-parse fe129a1^
       fe129a163d6ca22e5e4b48b81e7229c4260b1291        ← `^` 被吃掉，问的是另一个 revision
```

读法：**cmd 下的 0 不携带证据力**；有证据力的只有 bash（128 vs 0 才是判别）。

**③ 外层仓不跟踪引擎树（同族：也不跟踪 `runs/**` 与 `.workspace/**`）**

```
$ git ls-files godot-mcp | wc -l          → 6484
$ git ls-files godot-mcp/godot | wc -l    → 0
$ git check-ignore -v godot-mcp/godot runs/smoke-t10/meta.json .workspace/mario/project.godot
.gitignore:33:godot-mcp/godot/     godot-mcp/godot
.gitignore:12:runs/                runs/smoke-t10/meta.json
.gitignore:11:.workspace/          .workspace/mario/project.godot
$ git ls-files runs | wc -l → 0 ; git ls-files .workspace | wc -l → 0
```

读法：③′ 外层 `git status/diff` 对本批**全部真机证据都是空判** ⇒
"未变 / 已留证"只能靠**目录摘要 + 文件数 + newest mtime**（§8.1）；
引擎未改的判据是**嵌套仓** `fc63af77…` + `porcelain` 0 行。

---

## 10. 诚实披露

1. **我犯过一个错并已修好**：诊断早期我为了建临时目录，在一个 `%DST%` 字面量目录上执行了
   `rm -rf '%DST%'`，**误删了 7 个已跟踪文件**（`%DST%/red/*`）。我立刻用
   `git restore --source=HEAD -- '%DST%'` 恢复，并**逐个**核对
   `git hash-object <file>` == `git rev-parse HEAD:<file>`（7/7 OK），`git status --porcelain -uall` 空。
   **这 7 个文件在本批最终提交里零改动**（`git show --stat HEAD` 不含 `%DST%`）。
   我把这件事写下来，因为"误删再恢复"即使逐字节复原，也属于必须披露的动作。
2. **我没有声称 E3 met。** 本批交付的是"这两件事**轮内可观测**、且**流水线被要求**做到"，
   以及两条**会被引擎自己拒绝**的断言。是否真 met **只有真机能定**。
3. **我没有把 (A) 的运行时机制写成实测。** §2.5 明确：我**无法**离线判定"扫过不触发"的机制；
   我给的是"产物没交付行为 + 流水线没要求"这一层可核结论。
4. **我没有用诊断结论去改游戏。** `.workspace/mario/**` 零写入；本批对 `.spec/hof-rs/tasks/**` 的写入
   只有**新建**的 sidecar 与**本报告**；`DECISIONS.md` **只读、零编辑**（见 §10.3）。
5. **`scripts/run_round.ps1` 不存在**：`tests/round_artifacts.rs` 最初用源码检查断言它的 `ROUND_EXIT`，
   运行时 `os error 2`（文件不存在）⇒ 我删掉了那条源码检查（保留对 `main.rs`/`cli_impl.rs` 的接线检查）。
   这恰好说明 T10A-4 说的"第三处读数出自包装脚本"的**包装脚本本身已不在仓里**——本批的
   `process_exit_code` 因而更必要。
6. **我未做真机轮、未启动 Godot、未联网、未调用任何模型端点、未触碰任何端口。**
7. **`runs/**` 我零写入**（含"写过再删"）；分析产物与备份全部在仓外。
8. **`cargo test` 的最终读数来自"逐文件 touch 94 个已跟踪 `.rs` + 清 `target/debug/.fingerprint/hof-rs-*`"后的重编**；
   过程里我看到过两次**不可信的红/绿**（§1.1），都已定位原因并在重编后取数。
9. **sidecar 是生成物**：它由 `tests/round_artifacts_sidecar.rs` 的 `build_sidecar()` 生成，
   该测试同时钉住"原件逐字节不变"；因此 sidecar 的内容可被 CI 重新生成并逐字节复现。
10. **未验证/未闭合**见 §11。**本报告写完后不再修改。**

### 10.1 提交

```
$ git log --oneline -2
694deda docs(dr73): the DR-73 report - diagnosis of layer A, the battery window that makes pickup
        and win observable in-round, the prompt/skill/plan repairs, six plants, and the three
        carried items (DR-73)          ← tip（本报告自己的提交；SHA 以 `git log` 为准）
4deefc8 feat(dr73): observe E3's pickup and win in-round, and make the pipeline require them (DR-73)
$ git show --stat --oneline 4deefc8
 …13 files changed, 2256 insertions(+), 23 deletions(-)
$ git rev-list --left-right --count origin/master...master
0	2                                       ← 本地领先 2，未 push
$ git status --porcelain -uall
（空）
```

两个提交信息均含 `(DR-73)`、均为英文，逐条对应本报告 §3/§5。
**提交顺序**：先把代码/文档与报告提交，再做一次栅栏检查，然后**只**把"收工 HEAD 的表述"
改成上述不依赖自身 SHA 的写法并 `--amend`。此后**不再修改本报告**。

---

**本报告不含机器可读 JSON 结论块**（§0 是 markdown 表格，其余围栏均为 shell/测试输出）。
按任务书要求，我仍对本文**全部围栏代码块**做了"栅栏感知"检查：先用
`^\s*```(json)?\s*$` 切分栅栏，对**标记为 `json` 的块**逐一 `json.loads`；结果
**`json` 围栏数 = 0**（无可解析对象，因此也没有"块不合法"的风险）。检查脚本在仓外
`C:\Users\wyl\AppData\Local\Temp\dr73\fences.py`，输出：

```
json-fenced blocks = 0 ; all fenced blocks = 16 ; json.loads failures = 0
```

---

## 11. 遗留风险与未验证项（严格区分实测/推断）

**实测（本批有原始输出）**

1. 门：`cargo test --offline` exit 0、**523/0/7**、`--list` 530、**0 测试名被删**、`cargo fmt --check` 0。
2. 六处植入各自红、逐字节回退（`cmp`/`hash-object`/`git diff --stat`）。
3. 新电池步骤的四条判定在 fixture 下**可红可绿**，且其"绿"要求引擎自己的断言 `passed=true`。
4. 三处退出码读数同数（真实写入器 + 真实环境变量驱动）。
5. 原件 `redaction_defect.txt` sha256 未变、sidecar 无环境值。
6. 两条 CR 边界被钉（含"余部原样保留"这一代价本身）。
7. 五条 `runs/**` 基线的**文件数与 newest mtime** 与冻结记录逐字相符，且 `runs/**` 无 2026-10-01 之后写入。
8. 嵌套引擎 `fc63af77…`、`porcelain` 0 行；`PRD-mario.md` sha 未变；无新依赖；未 push。

**推断（不得当作已测）**

1. **（高把握）** 金币"扫过不触发"的机制在 monitoring/layer/mask 三者之外（三者在我读到的 `.tscn` 里都是默认值）
   ——我**没有**运行时证据，因此只把"产物没交付行为"写成实测。
2. **（中）** 关卡从 Platform3 右缘到 Goal 之间**没有任何落脚面**（我按 `.tscn` 的节点表逐条核对，
   但**没有**跑物理模拟验证"确实跳不过去"；`135 px` 的跳跃航程是公式推算 + 工程常量）。
3. **（中）** 新增步骤在**真机**上会把 `smoke-t10` 那类候选判为 **`ok=false`**（我在 fixture 上验证了该分支，
   真机上的采样时序、24 批是否足够、`reached` 的读取延迟等**未测**）。
4. **（低）** `HOH_RUN_DIR` 走环境变量：同一进程内多次 `run` 会互相覆盖该变量（生产里一次进程只跑一轮；
   我未构造"同一进程两轮"的场景）。

**未闭合（应回上游/回设计）**

1. **E3 是否 met**：只有真机能定。本批让它在**轮内可判**，但没有跑真机。
2. **金币为什么真的没被拾取**（运行时机制）：需要真机轮或一次受控真机实验才能定位；
   本批让下一轮**必然会观测到**它，并会让电池如实报 gap。
3. **T10A-2/F-T10-1 的脱敏器健壮性**（前导/BOM 的 JSON 识别、值内真实转义）：DR-74 已修并在
   DR-76 排队（`DECISIONS.md` D285 A-1/A-2）；本批**没有**动脱敏器的生产逻辑。
4. **`evidence_diff`（F-T10-3）仍空**：DR-68 R7 的状态由 DR-74 处理，本批未涉及。
5. **B 层的一个真实边界（记录，不修）**：`running_game_move_player_to_target` 需要导航数据
   （无数据时按设计 `-32000` 拒绝）⇒ 本批**没有**用它。若未来想让电池"通用地"把玩家送到任意目标，
   需要的是**关卡/导航设计**（Developer 侧）或**引擎侧导航支持**（TASK-15x），**不是本批的范围**。
   由于本批的观测不依赖它，**没有提出 TASK-15x 方案**（§2.3 已说明为何不需要）。
