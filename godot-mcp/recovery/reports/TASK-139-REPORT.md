# TASK-139 报告 —— 判据加固：窗口长度敏感性 + 合法拒绝识别，并在新口径下重跑 20×2

> 任务书：`F:\moonbit-hof-rs\godot-mcp\recovery\tasks\TASK-139.md`
> 执行方式：**严格单线程**，本任务期间**没有派任何子代理**（没有 `subagent` / `workflow` / `ralph` 调用）。
> 报告落点：`F:\moonbit-hof-rs\godot-mcp\recovery\reports\TASK-139-REPORT.md`
> 铁律 ①：本批**禁止一切 shell 重定向** ⇒ 自查数字见 §I（**299 条命令、0 命中**）。
> 本报告每个数字都能用下文给出的**绝对路径 + sha256**或生成脚本复算；**判据一条没有放宽**。
> 可提交工件已入库：**`455626c`**（`git log --oneline` 见 §J）。

---

## 0. 一句话结论

**A（窗口长度）**：`tools/playability_controls.json -> model_player_window.min_frames = 20` 已声明（含**实测依据**），
低于该值即 **`WINDOW_TOO_SHORT`**（与 FAIL / `MODEL_*` 分开，`counts_as_pass=false`，只能收紧）。
两档窗口（30 / 90）逐款重算 + 6 处 **`SENSITIVE`** 翻转并**点名受影响步**；
**`asteroids` 的专项结论是"不是仍然 PASS"**——脚本臂两档 PASS，**模型臂 w30 PASS → w90 FAIL**，
且原因是**长窗口揭出的真实游戏侧缺陷**（飞船死后不重生，连续 7 步 `pixel_diff=0`、两帧字节相同）。

**B（合法拒绝）**：5 款游戏的 `refusal_evidence` 已**逐字点名游戏侧计数器**（含"怎么取到"）；
边界写成声明式 `min_real_progress_steps = 4`：拒绝步**不判 FAIL、不进分母，但永不算推进**；
**"全拒绝零推进"必不得 PASS**——有断言，且**在真实数据上被触发过一次**（见 §B.5）。

**C（重跑）**：脚本臂 20/20 ×2 档、模型臂 jev 20/20 ×2 档、playjev **10 款**（≥8）全部在新口径下重跑完，
旧/新分布对照 + 逐款翻转如实报；100 个 run 的关键产物清单**已 `git add -f` 入库**；8 张全尺寸 800×600 帧实看，
**每条描述附可机检锚点**。

**另有一条比窗口长度更重要的实测结论（本批新发现）**：**w30 的逐款 verdict 不可复现**——
把本批**三轮完整的 w30 重复性探针**并排后，5 款里 **4 款在不同轮次之间翻过档**（同一命令、同一代码）；
**w90 的两轮完整运行**在同样 5 款上逐款一致。因此本报告**不把 w30 的一次抽样当成可复现读数**，
也不把"抖动翻档"记到窗口长度的账上（§A.4）。

**没有为了保绿调过任何一个参数**：两把尺子的公式一字未动、`--window-frames` 的语义未动、
`min_frames` **只能把 PASS 拿掉**；两档窗口各有游戏因此掉出 PASS，**如实报，未掩盖**。

---

## A. 目标 A —— 窗口长度敏感性

### A.1 声明式最小窗口长度（X1）

* **声明落点**：`tools\playability_controls.json -> model_player_window`（顶层块，含 `_model_player_window_comment`）：

  | 字段 | 值 |
  |---|---|
  | `min_frames` | **20** |
  | `applies_to` | `["control_window", "action_window"]`（**两侧都判**） |
  | `state` | `WINDOW_TOO_SHORT` |
  | `state_counts_as_pass` | `false` |
  | `declared_by` | `TASK-139 §1.A` |

* **取值依据（实测，不是猜）**：TASK-138 的 20 款共记录 **61 步**，两窗达成跨度落在 **29..34 帧**，
  **没有任何一窗低于 29**；20 因此在**全部已有证据的地板之下**（本批 100 个 run 的**全部窗口命中 0**，见 §A.6），
  同时高于一次 MCP 往返（**30..120 帧**，TASK-138 defect ⑧ 实测）这一分辨率下限；
  在 ~60 Hz 下约 1/3 秒，比变化测试比较的 1.0 s 短一档。短于 20 帧的窗口装不下
  "松键 → 游戏主循环 → 观测值回读"这一整拍——这正是该状态拒绝下判断的场合。

* **强制方式（X1 的机器部分）**：
  * `tools\playtest_player.py`：`load_window_declaration()` / `window_frames_of()` / `summarise()`。
    `player.json -> window_frames` **逐步**给出两侧实测跨度、`measured` / `short_windows` / `too_short` / `state`，
    并把**原判定保留**在 `verdict_before_window_check`；任一窗低于阈值时
    `verdict = "WINDOW_TOO_SHORT <原 verdict>"`、`counts_as_pass = false`、`pass = false`。
  * `tools\playability_gate.py -> evaluate_model_player_steps()` 读**同一块声明**并做同样的收口，
    写 `gate.json -> model_player_criterion.window_frames`。
  * **未记录跨度 ⇒ `unmeasured`，不判太短**（工具不许发明它没有的测量）。
* **与 FAIL / `MODEL_*` 分开**：它是关于**测量**的状态；与 `MODEL_FIXED_POINT` / `MODEL_NO_PROGRESS` 一样
  **永不是 PASS**，且不参与游戏判决的任何分支。
* **断言**：`tools\tests\test_playability_model_player.py` 的 TASK-139 段（`task139_cases`，**67 条**），
  含"29 帧不算太短 / 19 帧算 / 只动作窗短也判 / `None` 是 unmeasured 不是太短 /
  **同一局 30 帧是 PASS、3 帧变 WINDOW_TOO_SHORT 且 `counts_as_pass=false` 且原判定保留在旁** /
  gate 侧同口径"（**67** 条）。

### A.2 两档窗口的敏感性矩阵（X2）—— 逐款 verdict + 翻转项 + 受影响步

**同一份代码修订**（`runs\model-player\_scripts\t139_code_revision.json`）下，仅 `--window-frames` 不同：

**脚本臂（20 款）**

| 游戏 | w30 | w90 | 翻转 | 受影响步 |
|---|---|---|---|---|
| asteroids | PASS | PASS | | |
| bomberman | INCONCLUSIVE | INCONCLUSIVE | | |
| **breakout** | INCONCLUSIVE | **FAIL** | **SENSITIVE** | 1, 2, 3, 4 |
| flappy | INCONCLUSIVE | INCONCLUSIVE | | |
| frogger | INCONCLUSIVE | INCONCLUSIVE | | |
| game2048 | PASS | PASS | | |
| lunarlander | PASS | PASS | | |
| match3 | PASS | PASS | | |
| minesweeper | PASS | PASS | | |
| missilecommand | PASS | PASS | | |
| pacman | PASS | PASS | | |
| **platformer** | PASS | **INCONCLUSIVE** | **SENSITIVE** | 1–8 |
| **pong** | PASS(baseline only) | **PASS** | **SENSITIVE** | 1–12 |
| puzzlebobble | PASS | PASS | | |
| rtype | PASS | PASS | | |
| snake | PASS | PASS | | |
| sokoban | PASS | PASS | | |
| spaceinvaders | PASS | PASS | | |
| tetris | PASS | PASS | | |
| towerdefense | PASS | PASS | | |

**模型臂 jev（20 款）**

| 游戏 | w30 | w90 | 翻转 | 受影响步 |
|---|---|---|---|---|
| **asteroids** | PASS | **FAIL** | **SENSITIVE** | 1–12 |
| bomberman | INCONCLUSIVE | INCONCLUSIVE | | |
| breakout | FAIL | FAIL | | |
| flappy | INCONCLUSIVE | INCONCLUSIVE | | |
| frogger | INCONCLUSIVE | INCONCLUSIVE | | |
| game2048 | INCONCLUSIVE | INCONCLUSIVE | | |
| lunarlander | INCONCLUSIVE | INCONCLUSIVE | | |
| match3 | INCONCLUSIVE | INCONCLUSIVE | | |
| minesweeper | INCONCLUSIVE | INCONCLUSIVE | | |
| missilecommand | INCONCLUSIVE | INCONCLUSIVE | | |
| pacman | INCONCLUSIVE | INCONCLUSIVE | | |
| platformer | INCONCLUSIVE | INCONCLUSIVE | | |
| **pong** | FAIL | **PASS(baseline only)** | **SENSITIVE** | 1–12 |
| puzzlebobble | INCONCLUSIVE | INCONCLUSIVE | | |
| rtype | INCONCLUSIVE | INCONCLUSIVE | | |
| snake | INCONCLUSIVE | INCONCLUSIVE | | |
| sokoban | INCONCLUSIVE | INCONCLUSIVE | | |
| **spaceinvaders** | FAIL | **INCONCLUSIVE** | **SENSITIVE** | 2–12 |
| tetris | PASS | PASS | | |
| towerdefense | INCONCLUSIVE | INCONCLUSIVE | | |

**playjev（10 款，只跑预算允许的一档）**：`game2048` PASS、`rtype` PASS、`sokoban` PASS、`pacman` FAIL、
其余 6 款 INCONCLUSIVE（`asteroids`/`match3`/`minesweeper`/`pong`/`snake`/`tetris`）。

**三个翻转的机制（点名到步）**

1. **脚本 `breakout`（w30 INCONCLUSIVE → w90 FAIL）**：`real_progress` 3 → 2、`rated` 3 → 3，
   两个判定都不是 PASS；**更长的窗口让自走的球在对照窗里也走得更远**，控制项上升，
   于是第 2/3/4 步的"动作窗赢过对照窗"不再成立 → 比率 1.0 → 0.6667 < 0.75 → FAIL。
   受影响步 `[1, 2, 3, 4]`（逐 step 定义见 `t139_sensitivity.json`）。
2. **脚本 `platformer`（w30 PASS → w90 INCONCLUSIVE）**：这两个读数的**档位损失原因不同**：
   w30 `8/8 changed`、无拒绝；w90 该局被游戏自己的拒绝计数器记下 **3 步合法拒绝**（步 4/6/8），
   于是 `rated_step_count = 5 < PASS_MIN_STEPS(8)` → INCONCLUSIVE。也就是说：
   **更长的窗口让"一次跳跃被判为无进展"的合法拒绝出现**（`Lives` 掉了一格、落点改变等），
   `game_side_verdict` 在 w90 仍是 PASS，但模型判决因分母不足而**降级**。
3. **脚本 `pong` / 模型 `pong`（反向翻转）**：更长的窗口让**对照窗**装进更多自走运动，
   严格尺子（`mv ≥ 2×control` 且 `mv ≥ 1.0`）在一部分步上不再满足 → 模型臂 w30 FAIL → w90 baseline-only（**放宽了**）、
   脚本臂 w30 baseline-only → w90 PASS（**也放宽了**）。**这两个方向都如实报**：
   窗口加长**不是单调收紧**——它同时让"响应是否超过自走对照"这一比较更公平、也让某些步的比值下降。

### A.3 `asteroids` 专项（X2 的加粗要求）—— **不是"仍然 PASS"**

| 臂 | w30 | w90 | 结论 |
|---|---|---|---|
| 脚本 | PASS（`real=8`, `rate=1.0`, `align=3`） | PASS（`real=8`, `rate=1.0`, `align=3`） | 两档稳定 PASS |
| **模型 jev** | **PASS**（8 步，`rate 1.0`） | **FAIL**（12 步，`rate 0.25`，`fail_steps=[3,5,6,7,8,9,10,11,12]`） | **SENSITIVE，且方向是变严** |

**逐帧证据（模型臂 w90，绝对路径 + sha256）**

| 步骤 | action | pixel_diff | gameplay_movement | 关键状态 |
|---|---|---|---|---|
| 4（`013_04_after.png`） | `ast_*` | 964 | 237.8 | `Lives=3`，飞船可见（青方块在 x≈157） |
| **5**（`016_05_after.png`） | `ast_fire` | 607 | 779.4 | **`Lives 3 → 2`**，`Ship.vis` 消失（被撞毁） |
| 6–12（`022_07_after.png` … `037_12_after.png`） | `ast_thrust` | **0** ×7 | **0.0** ×7 | **飞船未重生、岩石不再移动、画面完全冻结** |

* **两帧字节相同**：`...\t139-jev-v3-w90\asteroids\jev\frames\022_07_after.png` 与
  `...\frames\037_12_after.png` 的 `sha256` **都是**
  `c09b58739e8d3094b081f997554e29ca6e602b55d2acdc757664aaa92ddefe4d`（均 10111 B）。
* **它不是"游戏结束了"**：同两帧的 `markers` 为 `{"GameOver": false, "Lives": 2, "Score": 0}`，
  `Ticks` 仍在推进——**游戏没声明终局，但玩家已经没有可见飞船、世界不再更新**。
* **判定**：这是**长窗口揭出的真实游戏侧缺陷**（飞船被撞毁后不重生），不是测量噪声：
  w30 的窗口在撞毁之前就结束了，所以 w30 看不到它。TASK-139 **只测不改**，故**登记不修**，
  留给下一批（与 frogger / bomberman / flappy 同一张登记表的口径）。
* **对 TASK-138 遗留风险 ① 的正面回答**：`asteroids` 的 verdict **对窗口长度敏感，且这一点被证实**
  ——但敏感的原因**不是**"0–6 帧客户端轮询残差"，而是**窗口是否长到让撞击发生**。
  因此 TASK-138 里那个 `PASS` 是**窗口太短导致的假绿**，更长窗口的 `FAIL` 是**更公平的读数**。

### A.4 重复性探针 —— 比窗口长度更重要的实测结论

敏感性矩阵比较的是"只差一档窗口"的两次 run；这只有在**同一档内可复现**时才能把差异归因给窗口。
于是本批做了重复性探针（同一条命令跑两遍、5 款、**专用端口**），并在过程中**跑了三轮 w30**
（前两轮各有事故，见下），最终得到：

**（i）每一轮内部**（`t139_determinism_t139-determinism-w30.json` / `-w90.json`，各 5 款 × 2 遍）：

| 游戏 | w30 两遍（端口 9967） | w90 两遍（端口 9968） |
|---|---|---|
| asteroids | PASS vs PASS | PASS vs PASS |
| pacman | PASS vs PASS | PASS vs PASS |
| tetris | PASS vs PASS | PASS vs PASS |
| pong | PASS(baseline only) vs PASS(baseline only) | PASS vs PASS |
| breakout | INCONCLUSIVE vs INCONCLUSIVE | FAIL vs FAIL |

⇒ **两档的"轮内"一致**（`all_rc_zero=true`、`all_verdicts_stable=true`），
但 `step_diffs` 仍是 6–12 处（窗口跨度、`pixel_diff`、`gameplay_movement` 每次都不同）
——**测量有噪声，判决在轮内稳定**。

**（ii）跨轮**（这是关键，只做一轮会看不到）：把本批**三轮完整的 w30 探针**并排放：

| 游戏 | 第 1 轮（05:42，`rc` 全 0） | 第 2 轮（05:37，与 w90 共用端口，`rc` 含 1） | 第 3 轮（06:39，`rc` 全 0） | 读法 |
|---|---|---|---|---|
| asteroids | **PASS vs INCONCLUSIVE** | PASS vs FAIL | PASS vs PASS | **轮间翻档** |
| tetris | PASS vs PASS | **FAIL vs INCONCLUSIVE** | PASS vs PASS | **轮间翻档** |
| pong | **PASS(baseline only) vs PASS** | PASS(baseline only) vs PASS(baseline only) | PASS(baseline only) vs PASS(baseline only) | **轮间档位文字翻转** |
| pacman | PASS vs PASS | PASS vs PASS | PASS vs PASS | 稳定 |
| breakout | **INCONCLUSIVE vs FAIL** | FAIL vs FAIL | INCONCLUSIVE vs INCONCLUSIVE | **轮间翻档** |

* **结论**：**w30 下 5 款里 4 款的 verdict 在不同轮次之间翻过档**；同一份命令、同一份代码。
  而 **w90 的两轮完整运行**（05:55 的干净轮 + 05:37 事故轮之后重跑的 06:04 轮）
  在同样 5 款上**逐款一致**（`asteroids` PASS、`pacman` PASS、`tetris` PASS、`pong` PASS、`breakout` FAIL）。
* **机制**（两条，都有逐 step 证据）：
  1. `Engine.get_frames_drawn()` 的**实际跨度**逐次不同（同一步 w30 的 `control_frames` 在 30–41 之间跳），
     于是"动作窗是否赢过对照窗"在边缘步上可能翻面；
  2. **`ack_result` 偶发缺失**——`step_verdict = changed_but_ack_missing` / `no_ack_no_change`
     （TASK-138 defect ⑨ 规定缺失即该步 INCONCLUSIVE）。第 2 轮 w30/w90 **共用端口互杀**
     放大了这条（`rc=1`、游戏被中途杀掉 ⇒ 大面积 `ack_missing`），第 1、3 轮没有这种事故，
     但第 1 轮仍出现 `changed_but_ack_missing`（asteroids 第 1 遍）与 `no_ack_no_change`（tetris）——
     所以**这条机制不是端口事故的产物**，*事故只是把它放大*。
* **本批的处理**：**如实登记，不擅自改判据**。`min_frames=20` 拦的是"太短"，拦不住"抖动"；
  报告里引用某款 verdict 时**同时写明档位与轮次**；
  模板 §1.2c 已把这条写成硬要求（引用 w30 的逐款 verdict 必须声明它是哪一轮的抽样）。
* **本报告的口径声明**：§A.2/§C 里 **w30 的逐款 verdict 是"一次抽样"**，
  跨轮翻过档的 4 款（`asteroids`/`tetris`/`pong`/`breakout`）**不得被读成可复现读数**；
  **w90 的脚本臂**在本批的两轮完整运行中逐款一致（§A.6 对照），故 §A.2 的 w90 列按可复现读法引用。
* **三轮的原始证据都保留**：第 2 轮（事故轮）的结果文件已被第 3 轮覆盖，但它的读数完整保留在
  `t139_determinism.log`（`rc=1`、`verdict=…` 逐行）与 `t139_sweep.log` 的时间线上，
  **是本报告"跨轮不一致"这一结论的证据来源之一**，故不删。


### A.5 敏感性矩阵的复算入口

* 生成：`D:\Anaconda\python.exe runs\model-player\_scripts\t139_sensitivity.py`
* 数据：`...\runs\model-player\_scripts\t139_sensitivity.json`
  `sha256 = 33cb91ea7c9054f7a6ceb5bf7d81d6b74ee376b4e060f9240718f05bff70ee6d`（313904 B）
* 单款逐 step 翻转明细：`t139_flip.py <arm> <game>`（例如 `t139_flip.py model asteroids`）
* 重复性：`t139_determinism.py`；数据
  `t139_determinism_t139-determinism-w30.json`（`1c949789…`，84845 B）与
  `...-w90.json`（`8f3d3439…`，78204 B）

### A.6 `WINDOW_TOO_SHORT` 命中数（本批）

**0 次**。100 个 run 的**每一步**都记录了控制窗与动作窗的实测跨度，**没有任何一窗低于 20 帧**；
两档中位数约 **31 帧（w30）/ 92 帧（w90）**（逐 step 值见 `player.json -> window_frames.steps`）。
这与"20 选在实测地板 29 之下"的依据一致——**阈值不是为了在本批制造命中，而是为了在未来的短窗口上拒绝下判断**。

---

## B. 目标 B —— 合法拒绝识别

### B.1 5 款的 `refusal_evidence` 声明（X3）

**落点**：`tools\playability_controls.json -> games.<game>.refusal_evidence`（新增
`game_side_fields` / `action_that_refuses` / `identifies` / `how_read` / `step_rule` /
`min_real_progress_steps` / `keys` / `value_words` / `keys_before_task139`）。

| 游戏 | `game_side_fields`（**逐字，来自游戏导出状态**） | 拒绝的动作 | 实测命中步（本批脚本臂 w30） |
|---|---|---|---|
| `match3` | `RejectedMoves`, `InputRejectedSwaps` | `m3_swap` | 2, 4, 6, 10 |
| `minesweeper` | `RejectedMoves`, `InputRejectedCursorActions` | `mine_reveal` | 3, 5, 7, 9, 11 |
| `pacman` | `RejectedSteps` | `pac_up/down/left/right` | 3, 6, 8, 10, 12 |
| `sokoban` | `RejectedMoves` | `soko_up/down/left/right` | 3, 5, 11 |
| `towerdefense` | `InputRejectedPlaces` | `td_place` | 6, 9, 12 |

**"如何取到"（写进声明的 `how_read`，逐字）**：

> 游戏自己的导出属性，由 `tools/playability_gate.probe_state_source()` 在**游戏进程内**读取
> （经 MCP 工具 `running_game_execute_gdscript` 执行），在每次注入前后各采样一次并差分进
> `steps.jsonl -> state_delta`；本工具把差分出的 key 与 `game_side_fields` 比对。
> **模型自述从不作为证据。**

**证据来源是游戏源码，不是模型**：`RejectedMoves++` / `InputRejectedSwaps++` /
`InputRejectedCursorActions++` / `RejectedSteps++` / `InputRejectedPlaces++` 逐处可在
`projects\<game>\src\*Game.cs` 找到（例如 `Match3Game.cs:701`、`PacManGame.cs:567,579`、
`TowerDefenseGame.cs:915`、`MinesweeperGame.cs:627,639`、`SokobanGame.cs:744-805`）。

**本批**顺手修正了一个会造成**误豁免**的判据缺陷（如实报）：TASK-131 的宽泛模式
`["LastRefusedInput", "Rejected"]` + `value_words` 会对**任意值变化**误报（`LastRefusedInput`
只要出现就匹配，不看值）。对这 5 款已**收窄为精确字段名**并**清空 `value_words`**，
原值保留在 `keys_before_task139` 便于对照。**运行时的证据串也改成点名计数器**
（例如 `match3` 第 2 步：`/root/Main.InputRejectedSwaps: 0 -> 1`，而不是
`/root/Main.LastEvent: 'reset' -> 'rejected reason=no_match ...'`）。

### B.2 规则边界（X4）

**落点**：`tools\playability_controls.json -> model_player_refusal`；`playtest_player.py -> step_refusal_record()` / `_summarise_core()`。

1. **只许移掉对游戏不利的部分**：拒绝步
   ①不进 FAIL 集（`fail_steps` 去掉它，原集合保留在 `fail_steps_before_refusal_carve_out`）；
   ②不进接受率的分母（`rated_step_count` = accepted − refused）；
   ③**永不算推进**（同时不进 `real_progress_steps`）。豁免**不能**把"没变"变成"变了"。
2. **必须有真实推进的地板**：`min_real_progress_steps = 4`，依据：PASS 需要 ≥8 注入步、
   接受即变化率 ≥0.75，`8 × 0.75 = 6` ⇒ **没有任何拒绝**的 run 天然带 ≥6 步真实推进，
   4 够不到它——该下限**只可能在豁免拿掉了分母时生效**。
3. **"全拒绝零推进"必不得 PASS（有断言）**：新增 `refusal_only_run`，是**显式 FAIL 分支**，
   位于"模型固定点"之后、"真实推进地板"之前（这样它同时覆盖"模型换着动作全被拒"与"模型卡死全被拒"两种）。
4. **无拒绝的 run 逐位不变**：拒绝集为空时 `rated == accepted`，每个数字与 TASK-139 之前相同；
   而且**地板在无拒绝时根本不参与**（见 B.4 的自查缺陷）。

### B.3 反向测试（X4 的断言部分）

`tools\tests\test_playability_model_player.py` 的 TASK-139 段（原文见文件）：

| 序列 | 断言 | 结果 |
|---|---|---|
| **拒绝 + 真实推进**（4 拒绝 + 4 推进，`match3`） | `verdict == "PASS"`、`counts_as_pass`、`refused_steps == [2,4,6,8]`、`fail_steps == []`、`fail_steps_before… == [2,4,6,8]`、`rated_step_count == 4`、`real_progress_steps == [1,3,5,7]`、`refusal_only_run == False`；**gate 侧同口径** | 全部 OK |
| **全在拒绝、零推进**（8 步全拒绝，动作与帧都不同，避开固定点条款） | `verdict != "PASS"`、`verdict == "FAIL"`、`counts_as_pass == False`、`refused_steps == 1..8`、`rated_step_count == 0`、`real_progress_step_count == 0`、`refusal_only_run == True`；**gate 侧同口径** | 全部 OK |
| **拒绝多、推进少**（6 拒绝 + 2 推进） | `verdict == "INCONCLUSIVE"`（不是 PASS） | OK |
| **无拒绝**（8 步全推进） | `refused_step_count == 0`、FAIL 集等于原始集、分母 8、`PASS` | OK |
| **无拒绝但推进 < 4**（新增自查） | 地板**不参与**，`verdict == "FAIL"`（比率 0.25），gate 同 | OK |
| **拒绝检测本身** | 计数器动了才算（`from == to` 不算）；证据串点名**声明过的计数器**；无 `game_side_fields` 时宽泛模式仍可用 | OK |

测试总数：该文件 **108 条断言全过**（其中 TASK-139 段 **67 条**）；`
playtest_player.py selftest` 亦全过（`selftest PASSED`）。两次最终运行都经台账执行，
命令与输出见 `t139_sweep.log` 之后的台账条目。

### B.4 我在实现中发现并修掉的**两个自己的缺陷**（如实报）

1. **地板一度对"零拒绝"的 run 也生效**（会导致无关的老 PASS 被收紧，违反"不许放宽/也不许无关收紧"）。
   **更正**：地板的触发条件加 `and refused_steps`（有拒绝才判地板），并补两条断言
   （"零拒绝 + 真实推进 2 < 4 ⇒ 仍是 FAIL，不是 INCONCLUSIVE"）。
   证据：`playtest_player.py:1345`（core）与 `:1408`（game-side）、gate `:2839`。
2. **`from == to` 的字段被当成"动过"**（状态 dump 列出每个导出属性，按它判拒绝会对任意步误豁免）。
   **更正**：`step_refusal_record` 先过滤 `from != to` 再匹配；并补断言
   "`RejectedMoves 1 -> 1` 不是拒绝"。

### B.5 边界在**真实数据**上被触发过一次（不是只有单测）

playjev 臂的 `pacman`（`...\t139-playjev-v3-w30\pacman\playjev\player.json`）：

* `refused_steps = [1,2,3,4,5,6,7,8,9,10,11,12]`（**全部 12 步都是游戏自己记录的拒绝**）、
  `rated_step_count = 0`、`real_progress_step_count = 0`、`refusal_only_run = true`。
* `verdict = **FAIL**`、`counts_as_pass = false`。
* **这正是"全拒绝零推进必不得 PASS"的现场证据**：如果按"拒绝就算合规"，这一款会变成"拒绝 12/12 ⇒ 100% 合规 ⇒ PASS"，
  而实际上**它一步也没推动世界**。

---

## C. 目标 C —— 在新口径下重跑 20×2（X5）

### C.1 覆盖（先证明覆盖，再谈分布）

`...\runs\model-player\_scripts\t139_coverage.py` 的输出（**每个 arm 的证据目录与结果文件都数**）：

| run 前缀 | 后端目录 | 证据 run | 结果文件行数 | 结论 |
|---|---|---|---|---|
| `t139-scripted-w30` | `scripted` | **20/20** | 20 | complete |
| `t139-scripted-w90` | `scripted` | **20/20** | 20 | complete |
| `t139-jev-v3-w30` | `jev` | **20/20** | 20 | complete |
| `t139-jev-v3-w90` | `jev` | **20/20** | 20 | complete |
| `t139-playjev-v3-w30` | `playjev` | **10/10** | 10 | complete |
| `t139-determinism-w30` | `scripted` | 5/5 | — | complete |
| `t139-determinism-w90` | `scripted` | 5/5 | — | complete |

**合计 100 个 run**，全部在**同一份冻结修订**下产生（`t139_code_revision.json` 的
`frozen-before-sweeps` 与 `frozen-after-evidence-ordering-fix` 两个快照，逐文件 sha256）。

**这一节为什么要单独写**：过程中发生过两次"**部分重跑覆盖了整臂结果文件**"
（5 款重跑把 20 行写成 5 行），以及一次**共用端口的两进程互杀**（确定性探针的 w30/w90 第一版）。
两类事故都被上面的覆盖检查与 `rc` 检查抓出来，并**重跑到完整**；
`t139_sweep.py --results-suffix` 与 `t139_merge.py` 是为此新增的。
**如实报**：`t139_results_t139-scripted-w30-counterev.json`（5 行）保留在库，是"部分重跑"的原始证据。

### C.2 旧 / 新分布对照（X5）

| 臂 / 档 | 分布 | 备注 |
|---|---|---|
| 脚本 · TASK-136 记录 | `9 PASS / 1 baseline-only / 4 FAIL / 6 INCONCLUSIVE` | 旧基准 |
| 脚本 · TASK-139 **w30** | **`15 PASS / 1 baseline-only / 0 FAIL / 4 INCONCLUSIVE`** | 本批 |
| 脚本 · TASK-139 **w90** | **`15 PASS / 0 / 1 FAIL / 4 INCONCLUSIVE`** | 本批 |
| 模型 jev · TASK-136 记录 | `1 PASS / 1 baseline-only / 3 FAIL / 15 INCONCLUSIVE` | 旧基准 |
| 模型 jev · TASK-139 **w30** | **`2 PASS / 0 / 3 FAIL / 15 INCONCLUSIVE`** | 本批（20/20，**遗留风险 ② 已闭合**） |
| 模型 jev · TASK-139 **w90** | **`1 PASS / 1 baseline-only / 2 FAIL / 16 INCONCLUSIVE`** | 本批 |
| playjev · 本批 **w30** | **`3 PASS / 0 / 1 FAIL / 6 INCONCLUSIVE`** | **10 款（≥8）**，如实报覆盖数 |

**脚本臂逐款翻转（TASK-136 → 本批 w30）**：

| 游戏 | 旧 | 新 | 原因（一句话） |
|---|---|---|---|
| asteroids | PASS(baseline only) | **PASS** | TASK-138 的两窗对齐（旧口径遗留） |
| bomberman | FAIL | **INCONCLUSIVE** | 3 步为游戏记录的合法拒绝 |
| match3 | FAIL | **PASS** | 4 步合法拒绝（B 的作用） |
| minesweeper | INCONCLUSIVE | **PASS** | 5 步合法拒绝 |
| pacman | FAIL | **PASS** | 5 步合法拒绝 |
| platformer | INCONCLUSIVE | **PASS** | 本批该 run 无拒绝、8/8 推进 |
| pong | PASS | **PASS(baseline only)** | 严格尺子在本批的抽样的边缘步上不满足（§A.4 口径） |
| sokoban | FAIL | **PASS** | 3 步合法拒绝 |
| towerdefense | INCONCLUSIVE | **PASS** | 3 步合法拒绝 |

**模型臂逐款翻转（TASK-136 → 本批 w30）**：`asteroids` FAIL → **PASS**；`pong` baseline-only → **FAIL**；
其余 18 款档位不变（其中 15 款仍 INCONCLUSIVE、`breakout` 仍 FAIL）。**17 款首次在新口径下复核**。

**分布变化的原因（逐条）**：
1. **B 的合法拒绝豁免**：直接解释 5 款（match3/minesweeper/pacman/sokoban/towerdefense）从 FAIL/INCONCLUSIVE 变 PASS，
   以及 bomberman 从 FAIL 变 INCONCLUSIVE。全部有 `refused_steps` 逐步证据。
2. **A 的窗口声明**：本批 `min_frames=20` **命中 0**，所以它对分布**没有**贡献；它的作用是防止未来短窗口下判断。
3. **两档窗口**：贡献 6 处 `SENSITIVE`（§A.2），其中 2 处让游戏**掉出 PASS**（脚本 `platformer`、模型 `asteroids`），**如实报**。
4. **重复性**：w30 与 w90 在 `pong`/`breakout` 上给出不同档位，**其中至少一部分是抖动而非窗口长度**
   （§A.4 的两遍探针已证明 w30 上这两款两遍不等）；本报告按"抖动不可归因"处理并逐条标注。

### C.3 产物清单入库（X6）

* 生成：
  `D:\Anaconda\python.exe tools\playtest_artifact_index.py --task TASK-139 --roots t139-scripted-w30 t139-scripted-w90 t139-jev-v3-w30 t139-jev-v3-w90 t139-playjev-v3-w30 t139-determinism-w30 t139-determinism-w90 --results-glob runs\model-player\_scripts\t139_results_*.json`
* 入库（`git add -f`，因为 `.gitignore` 第 12 行 `runs/`、第 43 行 `godot-mcp/runs/`）：

| 文件 | sha256 | 大小(B) |
|---|---|---|
| `godot-mcp/runs/model-player/_index/ARTIFACTS-TASK-139.json` | `d6d4685ce678ad5f8d5b88b3e6f1132bb28346f2ef4363c2ae98f5a1357bc69b` | 755515 |
| `godot-mcp/runs/model-player/_index/ARTIFACTS-TASK-139.md` | `558913c3056a4e0af19508592e131e4d2c148a4bf486610c29795794b71e3e05` | 364279 |

* 内容：**100 个 run / 800 个文件**，每个 run 带 `player.json` 的 verdict、`counts_as_pass`、
  `rated_step_count`、`refused_steps`、`real_progress_step_count`、`window_min_frames`、`window_state`、
  `frame_alignment` 读数与 `ack_missing_count`，每个关键文件带**路径 + sha256 + 大小**，
  每个 run 带**产生它的命令**（来自 `t139_results_*.json` 的 `cmd` 与共享台账）。
* **`.gitignore` 未改**；`runs/**` 依旧不入库，只有这一份清单入库。

### C.4 读图实看 + 可机检锚点（X7）

以下 **8 张帧全部用 `read_image` 实看**（渲染尺寸与源尺寸一致，均为 **800×600**），
每条描述同行给出**可机检锚点**（帧路径 + 完整 sha256 + 该步 `steps.jsonl` 的声明字段实测值）：

| # | 帧（绝对路径省略 `...\runs\model-player\`） | 源尺寸 | sha256（完整） | 实看描述 | 可机检锚点 |
|---|---|---|---|---|---|
| 1 | `t139-jev-v3-w30\asteroids\jev\frames\002_01_before.png` | 800×600 | `f1f195814a5c7d843d9d96aad75c23fde0a4afb06caf723499982fad432bc14a` | HUD 逐字 `SCORE 0  LIVES 3  ROCKS 4` / `ASTEROIDS 4`；**青色飞船在正中（约 x=400,y=300）**；四个米色岩石在四角 | 步 1 `ShipX=400.0 ShipY=300.0 ShipVelX=0.0 Lives=3 Score=0 BulletActive=false Ticks=638` |
| 2 | `…w30\asteroids\jev\frames\004_01_after.png` | 800×600 | `0c185ef8490ad7ac2463fed6ad4fb6ce9ab1346c0a865dcd2195f71b71287c6d` | **飞船明显右移**（青方块中心从约 x=400 移到 x≈458），岩石与 HUD 不变 | 步 1 `ShipX 400.0 → 457.611267089844`、`ShipVelX 0.0 → 90.599494934082`、`px=968 ctl=0 mv=205.822`、`Ticks→887` |
| 3 | `…w30\asteroids\jev\frames\005_02_before.png` | 800×600 | `3af88066de10f9cceff6c0e485779332a702d2ec65b8ed3059426dc4c91851a2` | 飞船已到约 x=490，其余同上 | 步 2 `ShipX=490.192108154297` |
| 4 | `…w30\asteroids\jev\frames\007_02_after.png` | 800×600 | `6fd4af3488d017cf3071d8b8c8e540e2cd9f516652fd59a6bcf164049f0a83bf` | 飞船继续右移到约 x=626 | 步 2 `ShipX 490.19→626.18`、`ShipVelX 77.53→134.82`、`mv=329.275 ctl=105.624` |
| 5 | `t139-jev-v3-w90\asteroids\jev\frames\013_04_after.png` | 800×600 | `683fbc883fddc6f89294f49d12a5e1bcf854109e43040a1e0959ba4901bf750d` | HUD `LIVES 3`；**飞船可见**且已下移到约 x=157,y=382 | 步 4 `Lives=3`、`px=964` |
| 6 | `…w90\asteroids\jev\frames\016_05_after.png` | 800×600 | `c09b58739e8d3094b081f997554e29ca6e602b55d2acdc757664aaa92ddefe4d` | **HUD 变成 `LIVES 2`；画面里已经没有飞船** | 步 5 `Lives 3 → 2`（`markers.Lives=2`）、`px=607`、`mv=779.428` |
| 7 | `…w90\asteroids\jev\frames\022_07_after.png` | 800×600 | `c09b58739e8d3094b081f997554e29ca6e602b55d2acdc757664aaa92ddefe4d`（**与 #6 字节相同**） | `SCORE 0  LIVES 2  ROCKS 4`，四岩石仍在原位、**无飞船** | 步 7 `pixel_diff=0 gameplay_movement=0.0 GameOver=false` |
| 8 | `…w90\asteroids\jev\frames\037_12_after.png` | 800×600 | `c09b58739e8d3094b081f997554e29ca6e602b55d2acdc757664aaa92ddefe4d`（**与 #6/#7 字节相同**） | **与 #6/#7 视觉完全一致**（像素级相同） | 步 12 `pixel_diff=0 mv=0.0`；三帧 sha256 相同 |

* **一致的结论**：#5→#6→#7→#8 串起来证明"**Lives 掉一格后飞船再没出现、世界冻结**"，
  而 `GameOver` 始终 `false`——**不是终局，是卡死**。
  三条帧 `016_05_after` / `022_07_after` / `037_12_after` 的 sha256 **完全相同**，是"此后 7 步零变化"的机器证据。
* **锚点怎么机检**：帧 sha256 用 `certutil -hashfile <路径> SHA256`；
  声明字段用 `t139_anchors.py <prefix> <game> <backend> <step...>`（逐字打印
  `steps.jsonl` 的 `markers` / `readable_state.values` / `state_delta` / 两窗跨度）。

---

## D. 目标 D —— 记录（X8）

* `DECISIONS.md` 追加 **D202 / D203 / D204**（编号顺延）：
  * **D202**：声明式最小窗口长度 + `WINDOW_TOO_SHORT` 语义（含取值依据与"只能收紧"的边界）。
  * **D203**：合法拒绝的规则边界（含 `min_real_progress_steps=4` 的依据、字段来源、`refusal_only_run`）。
  * **D204**：新口径下的分布变化及原因 + 两档窗口的 `SENSITIVE` 清单 + **重复性实测**。
* `recovery\tasks\TEMPLATE-logic-feedback.md` 同步三项：
  * 新增 **§1.2c**：`model_player_window.min_frames` / `WINDOW_TOO_SHORT` / **短窗口与不可复现是两件事**；
  * 新增 **§4.1**：合法拒绝的六条边界（证据必须来自游戏导出状态、只许移掉对游戏不利的部分、
    真实推进地板、全拒绝零推进不得 PASS、无拒绝逐位不变、反向测试必须存在）；
  * 反例清单追加 **22–25 条**（标称窗口≠够长、用拒绝当 PASS 理由、`from==to` 误判拒绝、
    拒绝步混进模型固定点）。

---

## E. X1–X10 逐条

| 编号 | 判据 | 结果 | 落点 |
|---|---|---|---|
| **X1** | 最小窗口长度已声明（含依据）；低于阈值 ⇒ `WINDOW_TOO_SHORT`（与 FAIL/`MODEL_*` 分开、不进 PASS） | ✅ | §A.1；声明在 `playability_controls.json -> model_player_window`，强制在 `playtest_player.py` + `playability_gate.py`，断言 **67** 条 |
| **X2** | 敏感性矩阵：两档窗口下逐款 verdict + 翻转项 + 受影响步；`asteroids` 专项结论 | ✅ | §A.2（20×2 全表 + 6 处 SENSITIVE + 受影响步 + 三个翻转的机制）、§A.3（asteroids：**模型臂 PASS→FAIL，且是真实游戏缺陷**） |
| **X3** | 5 款 `refusal_evidence` 已声明（字段来自游戏导出状态），并给"如何取到" | ✅ | §B.1（逐字字段名 + `how_read` + 源码出处 + 实测命中步） |
| **X4** | 规则边界：全拒绝零推进必不得 PASS（有断言）；拒绝+真实推进可达 PASS | ✅ | §B.2/§B.3（双向断言全过）；§B.5（**真实数据上触发过一次**：playjev pacman 12/12 拒绝 ⇒ FAIL） |
| **X5** | 脚本臂 20/20 + 模型臂 jev 20/20 新口径重跑完；旧/新分布对照；playjev 覆盖数如实报 | ✅ | §C.1（覆盖自证：100 run）、§C.2（分布对照 + 逐款翻转 + 原因）；playjev **10 款**（≥8） |
| **X6** | 产物清单已生成并 `git add -f` 入库（路径 + sha256 + 大小 + 生成命令） | ✅ | §C.3（两个文件 + 生成命令逐字 + 800 文件条目）；§J（提交 `455626c`） |
| **X7** | 读图：关键帧实看（含全尺寸），每条附可机检锚点 | ✅ | §C.4（8 张 800×600 实看，逐条路径 + sha256 + 声明字段实测值） |
| **X8** | `DECISIONS.md` + 模板同步本批三项 | ✅ | §D（D202/D203/D204；模板 §1.2c / §4.1 / 反例 22–25） |
| **X9** | 本批重定向自查数字（台账条数 / 命中 / 逐条原文） | ✅ | §I：**299 条命令、0 命中、0 误报**；切点由 `t139_cut_probe.py` 实证（`first_task139_index = 201`） |
| **X10** | 铁律逐条 + 文件所有权自查 + 两仓 `git log --oneline -5` 与 `git status --short`；未达标项如实报 | ✅ | §H/§J；未达标项（无阻塞项）见 §G |

---

## F. 关键产物的绝对路径 + sha256（本批）

> **怎么复算**：`certutil -hashfile "<路径>" SHA256`，或
> `D:\Anaconda\python.exe runs\model-player\_scripts\t139_hashes.py`（本表由它生成）。

| 产物 | sha256 | 大小(B) | 绝对路径 |
|---|---|---|---|
| 判据工具（主） | `69e12c0e391a2faa9deddca46dcd6d9f720212fe9e9918b7fbf02bf29dac3c61` | 255302 | `F:\moonbit-hof-rs\godot-mcp\tools\playtest_player.py` |
| gate（同口径） | `80092a2e050a51c48c40dbd892b4ddc9db4376be6e7f4bb0a1d7cf740e5da04e` | 213493 | `F:\moonbit-hof-rs\godot-mcp\tools\playability_gate.py` |
| 声明文件 | `04e2b2a34f46bb23f5a0217534fd4c645d937c70b92c539a427892686e0ea905` | 198775 | `F:\moonbit-hof-rs\godot-mcp\tools\playability_controls.json` |
| 产物清单工具 | `5aebba0abe3e7aec8ce1b9605342a7b63dbb45f24a62a6d2d8a2728bbf043f7c` | 14830 | `F:\moonbit-hof-rs\godot-mcp\tools\playtest_artifact_index.py` |
| 断言（108 条，TASK-139 段 67 条） | `99b08506c64d68ae0c02715d0214a53c1b0fe6f92c9955fa6d9a7543a9401508` | 38980 | `F:\moonbit-hof-rs\godot-mcp\tools\tests\test_playability_model_player.py` |
| 决策日志 | `fbca22f683316f630841e78a7b254b5a81108719b01f0b262e59efd854ae05fd` | 871544 | `F:\moonbit-hof-rs\DECISIONS.md` |
| 模板 | `f41298669a595cafd845b27a8c0321c42da7c55c9b358d6bca8e2c9b3e47f947` | 37189 | `F:\moonbit-hof-rs\godot-mcp\recovery\tasks\TEMPLATE-logic-feedback.md` |
| 任务书 | `6d6df3cf40087ac24a3ad6303d6b851fceb558828617a64fe52d3dd5af749faf` | 7240 | `F:\moonbit-hof-rs\godot-mcp\recovery\tasks\TASK-139.md` |
| 敏感性矩阵数据 | `33cb91ea7c9054f7a6ceb5bf7d81d6b74ee376b4e060f9240718f05bff70ee6d` | 313904 | `...\runs\model-player\_scripts\t139_sensitivity.json` |
| 旧/新对照数据 | `7ab58431285915620fc35c11750e243a63b4b24e0859293db1628d0442681a14` | 630066 | `...\runs\model-player\_scripts\t139_compare.json` |
| 重复性 w30（第 3 轮，final） | `e4e5e849bad6215ebe49848c6fe0b23a53e590442affd6b8180192324a9e1c3f` | 82502 | `...\runs\model-player\_scripts\t139_determinism_t139-determinism-w30.json` |
| 重复性 w90 | `8f3d3439691ba7fecab72b4b57d4e86e5a0ef15eeaa4457444db4a94cde0d6f9` | 78204 | `...\runs\model-player\_scripts\t139_determinism_t139-determinism-w90.json` |
| 重复性日志（**含第 2 轮事故轮**） | `099655406fc44486a69121672d03312e566c81aee6bd59e9821cb75a04d385f4` | 8799 | `...\runs\model-player\_scripts\t139_determinism.log` |
| 重定向自查 | `d5c441e23426c8f4f2cded585f9818ae8de52bd6874f929f45e7878ecea551d9` | 153177 | `...\runs\model-player\_scripts\t139_redirect_scan.json` |
| 脚本臂 w30 | `9bfdc0cdb394d78b432f3ca7dcb8fda1b82ce2cd1eba9c78060e5a0520406d30` | 108716 | `...\runs\model-player\_scripts\t139_results_t139-scripted-w30.json` |
| 脚本臂 w90 | `96287c11e6e179f0db7da32c7ad1a41d2699a03b7a30a737af3d60b8233e491d` | 107286 | `...\runs\model-player\_scripts\t139_results_t139-scripted-w90.json` |
| 模型臂 w30 | `b1aeecee26e270e0a0529bd3f5eada418b19bcb33b4a0cebd7bef5474e9858f5` | 117275 | `...\runs\model-player\_scripts\t139_results_t139-jev-v3-w30.json` |
| 模型臂 w90 | `193b6ca255bb7b79d9427cac59fad1b256bfec881f7b8f4165abf8848fecf32e` | 118416 | `...\runs\model-player\_scripts\t139_results_t139-jev-v3-w90.json` |
| playjev w30 | `d8b3a89220744385b9bdeb0cc2b9d57bd294650bb92e5852a35a8649c6155949` | 62939 | `...\runs\model-player\_scripts\t139_results_t139-playjev-v3-w30.json` |
| 产物清单 JSON | `d6d4685ce678ad5f8d5b88b3e6f1132bb28346f2ef4363c2ae98f5a1357bc69b` | 755515 | `...\runs\model-player\_index\ARTIFACTS-TASK-139.json` |
| 产物清单 MD | `558913c3056a4e0af19508592e131e4d2c148a4bf486610c29795794b71e3e05` | 364279 | `...\runs\model-player\_index\ARTIFACTS-TASK-139.md` |
| 命令台账（本批读到时） | `afee865e2825b3cf17c5db581eff6ee00c555b58cc14576afe6d1ae72239d2ea` | 171668 | `...\runs\model-player\_scripts\t136_commands.jsonl` |
| asteroids 模型 w30 | `bf604b720a350200fb6e372a1c5bd9228a00730609fb5c6b686c425fe6e84fc1` | 169166 | `...\t139-jev-v3-w30\asteroids\jev\player.json` |
| asteroids 模型 w90 | `e6f4cc5104a13408b61152253b03b8cbc416672f101c20ec988673ceb2f5d0a7` | 245090 | `...\t139-jev-v3-w90\asteroids\jev\player.json` |
| 冻结的两帧（**同 sha**） | `c09b58739e8d3094b081f997554e29ca6e602b55d2acdc757664aaa92ddefe4d` | 10111 ×2 | `...\t139-jev-v3-w90\asteroids\jev\frames\{022_07_after,037_12_after}.png` |
| match3 合法拒绝步 2 | `bc93d0faf4af0bbdfb2395a6d4455ef7f610fa78d4c28d84ea842184106b85c7` | 141510 | `...\t139-scripted-w30\match3\scripted\steps.jsonl` |
| playjev pacman（全拒绝 FAIL） | `ff3d43344405baea5075002902a8906f8e3d84978d84463b51dbaf5817b7ac29` | 366834 | `...\t139-playjev-v3-w30\pacman\playjev\player.json` |
| **本报告** | 见 §J 的提交；**不写自身内容哈希**（写入动作会改变它，定义上不可核） | — | `F:\moonbit-hof-rs\godot-mcp\recovery\reports\TASK-139-REPORT.md` |

---

## G. 未达标项 / 已知限制（如实报）

1. **w30 的逐款 verdict 不可复现**（§A.4 的**跨轮**对照：三轮完整 w30 探针里 5 款有 4 款翻过档）。
   本报告不声称它是可复现读数；
   受影响的款（`asteroids`/`tetris`/`pong`/`breakout`）的**档位差异不能全部归因给窗口长度**。
   本批**没有**因此改判据（那属于设计变更，应另开任务）。
   另外：三轮中的第 2 轮曾因 **w30/w90 共用端口互杀**产生 `rc=1`，那一轮的读数**不作为常规证据**
   （只在 §A.4 的跨轮对照里出现，并已注明原因）。
2. **`asteroids` 的死亡不重生缺陷只登记未修**。TASK-139 明令"只测不改 20 款游戏逻辑"，
   故该缺陷留给下一批；它的证据（帧 sha、逐 step、状态）已在 §A.3 与产物中固定。
3. **`min_frames` 只拦"太短"，拦不住"抖动"**。这是刻意的分工（§A.4/§D）；
   抖动问题本批只测量与登记。
4. **playjev 只跑了 10 款（预算允许范围内）**，未做两档窗口（预算），故 playjev 只有单档敏感性数据。
5. **重复性探针只覆盖脚本臂 5 款**（w30/w90 各两遍）。模型臂的重复性未测（预算）；
   §A.4 的结论**只适用于被探针覆盖的那 5 款**，不外推。
6. **部分重跑覆盖过整臂结果文件**（§C.1）：已重跑到完整，但 `t139_results_t139-scripted-w30-counterev.json`
   这类中间产物保留在库，读者看到多份结果文件时应以 `t139_coverage.py` 的覆盖检查为准。
7. **同 sha 的两帧是"静止"的证据，不是"内容是游戏终局"的证据**：`GameOver` 为 `false`（§A.3），
   所以本报告只用它证明"世界不再更新"，不据此断言游戏自认为结束。

---

## H. X10 —— 铁律逐条、所有权自查

### H.1 铁律逐条（任务书 §2）

| # | 铁律 | 本批执行情况 |
|---|---|---|
| 1 | 禁止一切 shell 重定向；沿用台账+扫描器并给自查数字 | ✅ **299 条命令、0 命中、0 误报**（§I）；所有命令经 `t139_cmd.py`（`shell=False`）或已回填；写盘一律用 Python 句柄/`-F` 文件 |
| 2 | 破坏性命令默认拒绝；只测不改 20 款游戏逻辑 | ✅ 未改任何 `projects/**`；`git status` 的 20 款游戏目录无改动；本批删除只发生在**自己的 run 产物**（`counterev` 空目录、`_smoke139.*`） |
| 3 | 命令尽量从 cmd 启动；中文写盘用 UTF-8 | ✅ 运行命令经 `cmd /c`；写盘用 Python `io.open(encoding="utf-8")`；commit message 用 `-F <文件>`（非重定向） |
| 4 | 禁止第三方端点；只用 8080/8081；串行；429/529 退避 | ✅ 只调 `127.0.0.1:8080`（jev）/`:8081`（playjev）；模型臂**串行**（一个跑完再起下一个）；本批**未出现** 429/529，故无退避记录 |
| 5 | 不得杀服务/动 venv/动 `F:\models\**`/动 `_exercises` 既有变体 | ✅ 未触碰；两个服务全程健康（`t139_health.py`：`{"status":"ready"}` / `{"ok":true}`） |
| 6 | 端口：唯一高位端口（避开 9877/9888/9889/8080/8081） | ✅ 用了 9961–9973；**曾犯一次错**（确定性探针 w30/w90 共用 9967 导致互杀），已修成 `PORT_STEP` 并按端口重建，事故与更正见 §C.1 |
| 7 | 不许放宽判据；窗口加长/拒绝豁免只许更公平；翻转如实报 | ✅ 豁免只移 FAIL 与分母、**永不算推进**且带回退地板；`min_frames` 只能拿掉 PASS；6 处翻转如实报，其中 **2 处让游戏掉出 PASS** |
| 8 | 改引擎模块才触发重建/十道门/`accept_m1`/push | **未触发**：本批只改 `godot-mcp/tools/**`、`DECISIONS.md`、模板与 `runs/model-player/**`，**未改 `godot-mcp/godot/**` 的任何引擎模块**（依据：`git status --short` 的改动清单里没有任何 `godot/modules/**` 路径；提交 `455626c` 的文件清单同样只有上述路径） |
| 9 | 提交前 `git status --short` 只暂存独占清单内的文件 | ✅ 提交前逐条核对（§J.2）；`ACCEPTANCE-TASK-137.md` / `TASK-137-ACCEPT.md`（TASK-137 的未跟踪文件）**未暂存** |
| 10 | 事实来源分级；代码与文档冲突以代码为准并显式纠正 | ✅ 本报告区分"实测（代码/产物）/ 声明 / 引用"；发现三处**自己的**实现缺陷并更正（§B.4、§C.1、§I.3） |

### H.2 文件所有权自查

| 类别 | 路径 | 本批动作 |
|---|---|---|
| **独占（已改）** | `tools/playtest_player.py`、`tools/playability_gate.py`、`tools/playability_controls.json`、`tools/tests/test_playability_model_player.py`、`tools/playtest_artifact_index.py` | 修改，已入库 |
| **独占（已改）** | `runs/model-player/**`（脚本、数据、run 产物）、`recovery/tasks/TEMPLATE-logic-feedback.md`、`DECISIONS.md` | 修改/新增；`_index` 两条 `git add -f` 入库，其余按 `.gitignore` 不入库 |
| **独占（只读）** | `recovery/tasks/TASK-139.md` | 只读；随本批一并入库（任务书本身） |
| **未触碰（禁触）** | 20 款正式工程的**逻辑**（`projects/**/src/**`）、`projects/_exercises/{neg_*,prefix_*}`、`recovery/reports/TASK-136-REPORT.md`（**本批未追加勘误**——本批没有针对它的勘误项）、`F:\models\**`、两个 venv、8080/8081 服务、`.gitignore`、`recovery/tasks/README.md` | 全部未动（依据：`git status --short`） |

### H.3 事实来源分级（本报告采用）

* **A 级（实测，可复算）**：`player.json` / `steps.jsonl` / `frames/*.png` 的哈希与字段、
  扫描器的命中计数、`t139_coverage.py` 的覆盖数、两遍重复性探针的读数。
* **B 级（声明，可争辩）**：`playability_controls.json` 里的 `min_frames=20`、
  `min_real_progress_steps=4`、两把尺子的系数；本报告给出各自的 `basis` 而不把它们说成事实。
* **C 级（引用）**：TASK-136/138 的历史读数（标明出处文件与来源），
  以及模板里既有的条款编号。

---

## I. X9 —— 本批重定向自查数字

* **自查数字（最终一次扫描）**：本批 **299 条命令**、**0 条命中**重定向、**0 条误报**。
  （同一次扫描之前的读数：280 条；差额是定稿阶段新增的验证/生成命令。）
* **扫描器**：`...\runs\model-player\_scripts\t139_scan_redirects.py`
  （由 `t139_cmd.py` 包一层执行，所以它自己也在台账里）
* **产物**：`...\runs\model-player\_scripts\t139_redirect_scan.json`
  `sha256 = d5c441e23426c8f4f2cded585f9818ae8de52bd6874f929f45e7878ecea551d9`（153177 B）

### I.1 命令侧

| 指标 | 值 |
|---|---|
| 台账总行数（扫描时） | **500**（`ledger_lines_total`；台账追加式，故此后还会增长） |
| 台账 sha256（扫描时） | `9be2999f6e58bb4e3a067ac07d86a0dcad36d5a7eb7d7103dff2570467ffed86`（171864 B） |
| 本批命令数（切点之后） | **299** |
| **命中重定向的命令数** | **0** |
| 误报 | **0** |
| 本批首条 ts | `2026-09-28T04:43:17`（`first_task139_index = 201`） |
| 本批末条 ts | 见 `t139_redirect_scan.json -> this_batch_last_ts` |

### I.2 切点（**实证，不是假设**）

* `t139_cut_probe.py` 输出：**第一条命名 `t139` 的台账条目 idx=201**、`ts=2026-09-28T04:43:17`、
  `source=t139-wrapper-call`，其前一条 idx=200 是 TASK-138 的收尾命令（`ts=2026-09-28T04:30:20`）。
* **如实报三次切点口径的自我更正**：第一版用"第一条 `manual-backfill`"⇒ 会把 TASK-138 自己的 16 条回填
  也算进来（多报 44 条、3 条命中）；第二版用"`t139_` 子串"⇒ 漏掉 argv 里不含 `t139_` 的
  wrapper 条目（例如直接跑 `tools/playtest_player.py` 的）；第三版以上述"`source` 或 argv 的 t139 命名空间"
  为准，并与 `t139_cut_probe.py` 的独立输出**对齐后**才定稿。

### I.3 脚本侧（源码里的字面 `>` 等）

* 扫描 31 个文件（本批 `t139_*.py` + `tools/playtest_player.py` + `tools/playability_gate.py` +
  `tools/playtest_artifact_index.py`），`shell=True`：**0**。
* 字面 token 命中 **396** 处（`code` 248 / 注释与字符串 148）。**逐条原文**在
  `t139_redirect_scan.json -> script_hits`（本报告不贴 396 行，链接足够）。
* **为何 248 处 `code` 不是"重定向"**：扫描器把"行首不是 `#`/引号/反引号"的一切都归为 `code`（已在脚本注释里
  声明这是近似），于是 `>=`、`->`、`>>`（位运算）、`>` 比较、以及**打印出来的**箭头
  （如 `print("   %-16s -> %-26s")`）都被计入。三条判据：(1) 这些行没有一个是 shell 命令行；
  (2) `t139_cmd.py` 用 `shell=False`，**即使**把 `>` 放进 argv 也没有 shell 去解释它；
  (3) 命令侧的 **299** 条**命中 0**，这才是"我实际运行的命令有没有重定向"的答案。
* **驱动脚本数**：32 个（本批 `t139_*.py` 33 个 + 3 个改过的 `tools/*.py`，去掉扫描器自己）。

---

## J. X10 —— 两仓状态与提交

### J.1 `git log --oneline -5`（`F:\moonbit-hof-rs`）

```
455626c TASK-139: declare a minimum measurement window, recognise legal refusals, and re-run 20x2
926ac5e docs(godot-mcp): TASK-138 - state that the report's own later revisions are located by commit id, not by an embedded hash (docs-only)
1f36fb4 docs(godot-mcp): TASK-138 - record that 417dbc9 is the docs-only write-back of the deliverable commit (docs-only)
417dbc9 docs(godot-mcp): TASK-138 - fill in the deliverable commit 648b94c and the blob-identity of the final report (docs-only)
648b94c TASK-138: align the two measurement windows on ACTUAL drawn frames, forbid the pre-injection ack fallback, require a machine-checkable anchor for every image read, and commit the run-artifact index
```

`F:\moonbit-hof-rs\godot-mcp` 是同一个仓库（`git rev-parse --show-toplevel` 在两个目录下都返回
`F:/moonbit-hof-rs`），故**只有一仓**——本批没有第二仓。

### J.2 `git status --short`（提交前）

```
M  DECISIONS.md
A  godot-mcp/recovery/tasks/TASK-139.md
M  godot-mcp/recovery/tasks/TEMPLATE-logic-feedback.md
A  godot-mcp/runs/model-player/_index/ARTIFACTS-TASK-139.{json,md}
A  godot-mcp/runs/model-player/_scripts/t139_*.py / t139_*.json / t139_*.log   (37 个)
M  godot-mcp/tools/{playtest_player,playability_gate,playtest_artifact_index}.py
M  godot-mcp/tools/playability_controls.json
M  godot-mcp/tools/tests/test_playability_model_player.py
?? godot-mcp/recovery/reports/ACCEPTANCE-TASK-137.md      <- TASK-137 的未跟踪文件，未暂存
?? godot-mcp/recovery/tasks/TASK-137-ACCEPT.md            <- 同上，未暂存
```

### J.3 提交

* 交付提交：**`455626c`**
  （`TASK-139: declare a minimum measurement window, recognise legal refusals, and re-run 20x2`）
* 提交信息文件：`...\runs\model-player\_scripts\t139_commit_msg.txt`（随提交入库，便于核对提交说了什么）
* **本报告本身**：以**另一次提交**入库；定位方式用**提交号**，**不写自身内容哈希**
  （写入动作会改变哈希，定义上不可核；与 TASK-138 勘误 ⑤ 的口径一致）。
* `git add -f` 的两个路径（`runs/**` 被忽略）：`ARTIFACTS-TASK-139.json` / `.md`，
  以及本批自己的 `_scripts/t139_*`（涉及台账可核性与结论复算，属"小而不可再生的判定依据"）。
* **`.gitignore` 未改**。

---

## K. 一句话给下一位读者

**要看结论**：§0 + §E；**要看证据**：§C.1（覆盖自证）/ §C.4（8 张实看帧 + 锚点）/ §F（哈希表，
用 `certutil` 复核）；**要复算**：`t139_sensitivity.py`、`t139_compare.py`、`t139_coverage.py`、
`t139_determinism.py`、`t139_scan_redirects.py`、`t139_hashes.py`；
**要读一条没解决的问题**：§G.1（w30 不可复现）与 §A.3（asteroids 死亡不重生，已登记未修）。
