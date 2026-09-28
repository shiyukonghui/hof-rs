# TASK-140 报告 —— 判据可靠性（报告档位 + `UNSTABLE`）与 4 款游戏侧缺陷修复

> 任务书：`F:\moonbit-hof-rs\godot-mcp\recovery\tasks\TASK-140.md`
> 执行方式：**严格单线程**，本任务期间**没有派任何子代理**（没有 `subagent` / `workflow` / `ralph` 调用）。
> 报告落点：`F:\moonbit-hof-rs\godot-mcp\recovery\reports\TASK-140-REPORT.md`
> 铁律 ①：本批**禁止一切 shell 重定向** ⇒ 自查数字见 §I（命令台账 + 扫描器，逐条原文）。
> 本报告每个数字都能用下文给出的**绝对路径 + sha256**或生成脚本复算；**判据一条没有放宽**。
> 可提交工件见 §J 的提交号。

---

## 0. 一句话结论

**A（判据可靠性，最高优先）**：
`tools/playability_controls.json -> model_player_window.reporting_frames = 90` 已声明（依据 = TASK-139
§A.4 的实测：w30 跨轮不可复现、w90 两轮逐款一致）。标称窗低于 90 的 run 照样测量、照样记录、照样打印，
但写 `BELOW_REPORTING_WINDOW` / `at_reporting_window: false` / **`counts_as_pass: false`**，并在
`qualified_verdict` 上标 `[reference only: ...]`——**只能拿走 PASS，永不补上**（§A.1）。
每个 verdict 现在都带**档位 + 轮次**（`--round` / `verdict_context` / `qualified_verdict` / gate 侧同字段，§A.3）。
新增 **`UNSTABLE`**：同款同档 **≥2 轮独立完整运行**，verdict **类别**不一致即标 `UNSTABLE`、
**列出分歧轮次与分歧点**（哪一步、哪个判据项）、**不计入 PASS**（§A.2）。
在报告档位下重跑 **脚本臂 20×2、模型臂 jev 20×2、playjev 10×2**，逐款两轮对照表 + `UNSTABLE` 名单 +
新分布见 §C，`SENSITIVE`（同轮两档）与 `UNSTABLE`（同档两轮）**并列**给出，谁也不替谁开脱。

**B（4 款游戏侧缺陷）**：`asteroids` 死亡后**自动重生**（+重生无敌）、`frogger` **一次按键=一步/≤1 命**
（边沿触发 + `RepeatHold` + `DeathGrace`，并挪开出生格正上方那辆车）、`bomberman` **炸弹可见**
（导出 `BombsVisible` / `BombMinContrast`；并把被规则拒绝的投放**写进导出计数器** `RejectedPlaces`，
修掉"拒绝了却什么都不写"）、`flappy` **两窗都在"世界在跑"下成立**（`AutoRun=true` + READY 相位**停在触地条上**
+ 触地是着陆）。4 款 `dotnet build` **0 失败 0 警告**，修前→修后证据逐款给出（§B）。
`flappy` 的脚本臂仍**不是** PASS，确切原因见 §B.4 与 D208（**结构性**的：横向滚动的世界被声明为玩法观测量时，
strict 的 2× 余量对一次 flap 不可达）——如实报，未调参凑绿。

**没有为了保绿调过判据**：两把尺子的公式一字未动、`min_frames` / `--window-frames` 语义未动、
`reporting_frames` 与 `UNSTABLE` **只能把 PASS 拿掉**；两侧翻转（有游戏变好、也有游戏变差）**逐款如实报**。

---

## A. 目标 A —— 判据可靠性

### A.1 `reporting_frames` 声明与 `BELOW_REPORTING_WINDOW`（Y1）

* **声明落点**：`tools\playability_controls.json -> model_player_window`（新增字段，并同步
  `_model_player_window_comment` 与新块 `_model_player_stability_comment`）：

  | 字段 | 值 |
  |---|---|
  | `min_frames` | 20（TASK-139 §1.A，未动） |
  | **`reporting_frames`** | **90** |
  | `reporting_state` | `BELOW_REPORTING_WINDOW` |
  | `reporting_counts_as_pass` | `false` |
  | `reporting_basis` | 见下（实测依据，逐字写进声明） |

* **取值依据（实测，不是猜）**：TASK-139 §A.4 用**三轮完整的 w30 探针**（5 款、专用端口、同命令同代码）
  测得 **5 款里 4 款跨轮翻档**（`asteroids` PASS/INCONCLUSIVE/FAIL、`tetris` PASS/FAIL/INCONCLUSIVE、
  `pong` `PASS` vs `PASS(baseline only)`、`breakout` INCONCLUSIVE/FAIL），机制逐 step 定位到
  `Engine.get_frames_drawn()` 跨度抖动 + `ack_result` 偶发缺失；而 **w90 两轮完整运行在同样 5 款上逐款一致**。
  90 因此不是"更大就更好"，它是**当前证据里唯一被证明可复现的档位**。
* **强制方式（Y1 的机器部分）**：`tools\playtest_player.py -> load_window_declaration`（读同一块，含
  `reporting_frames` / `reporting_basis`）与 `summarise(..., nominal_frames=)`：写
  `player.json -> reporting_window`（`required_frames` / `nominal_frames` / `at_reporting_window` / `state` /
  `basis` / `rule` / `not_a_loosening`）、`verdict_before_reporting_check`、`reporting_why`，
  并把 `counts_as_pass` / `pass` 强制为 `false`；`qualified_verdict` 追加
  `[reference only: window 30 < reporting 90]`。
  `tools\playability_gate.py -> evaluate_model_player_steps(..., run_context=)` 做**同样的收口**，
  写 `gate.json -> model_player_criterion.evidence.reporting_window`。
* **未记录标称窗 ⇒ 不判**：`nominal_frames is None` 时写 `state: unrecorded`，**既不加也不减** PASS
  （工具不许发明它没有的测量；这条在 `resummarise` 的旧 run 上尤其重要）。
* **断言**：`tools\tests\test_playability_model_player.py -> task140_cases`（**41 条**），其中 reporting 段
  **14 条**：声明存在且 ≥ `min_frames`、有 `basis`、模块常量等于声明值、`AT` 报告窗仍是 `PASS` 且
  `counts_as_pass=True`、`BELOW` 保留原 verdict 但 `counts_as_pass=False` 且标签带 `reference only`、
  **只能拿掉不能补上**（一个本来不 PASS 的 run 在 30 帧下也不 PASS）、gate 侧同口径、
  无 context 时不发明档位。
* **本批的实测触发（不是只有单测）**：§C.6 的 `t140-w30-demo` —— 同一款在 30 帧下的真实 run
  `verdict=PASS` 而 `counts_as_pass=False`、`reporting_window.state=BELOW_REPORTING_WINDOW`。

### A.2 `UNSTABLE`：同款同档 ≥2 轮不一致 ⇒ 不进 PASS（Y2）

* **声明**：`tools\playability_controls.json -> model_player_stability`（`min_rounds: 2`、
  `state: UNSTABLE`、`state_counts_as_pass: false`、`comparable_classes`、`rule`、`basis`、`not_a_loosening`）。
* **实现**：`tools\playtest_player.py`
  * `verdict_class()`：把 verdict 归到**类别**（`PASS` / `PASS(baseline only)` / `FAIL` /
    `INCONCLUSIVE` / `WINDOW_TOO_SHORT ...` / `MODEL_FIXED_POINT` / `MODEL_NO_PROGRESS`）。
    `PASS` 与 `PASS(baseline only)` 是**两个类别**——TASK-139 里 `pong` 正是在这两个字符串之间翻转。
  * `divergence_between(a, b)`：逐 step 比**可归因的判据项**（`injected` / `accepted` / `ack_missing` /
    `changed` / `changed_strict` / `step_verdict`），像素计数只作 `context` 记录（两轮本来就会不同）。
  * `stability_summary(runs)` / `stability_from_paths(paths)`：< `min_rounds` ⇒ `INSUFFICIENT_ROUNDS`
    （不是判断，也不是通过）；类别全同 ⇒ `STABLE`，且**只有每一轮都是字面 `PASS`** 才
    `counts_as_pass: true`；任一不同 ⇒ **`UNSTABLE`** + `divergent_rounds` + `divergence_points` +
    `counts_as_pass: false`。
  * CLI：`playtest_player.py stability --run <player.json> --run <player.json> [--out FILE]
    [--require-engine-state]`（`--require-engine-state` 在 `UNSTABLE` 时退出码 1，供"不许把不稳定当通过"的调用方）。
* **断言**：`task140_cases` 的 unstable 段 **22 条**：一轮 ⇒ `INSUFFICIENT_ROUNDS`；两轮同类别 ⇒ `STABLE`
  且 all-PASS 才通过；两轮不同 ⇒ `UNSTABLE` 且**不进 PASS**、轮次与类别列出、分歧**点名到步与判据项**；
  `PASS` vs `PASS(baseline only)` 算不一致；`WINDOW_TOO_SHORT` vs `PASS` 算不一致；
  稳定的全 FAIL 对**不通过**；一个 PASS + 一个 INCONCLUSIVE ⇒ `UNSTABLE` 且 `counts_as_pass=false`；
  `ack_missing` 消失被点名成 `accepted` / `ack_missing` 两项。
* **本批的实测触发**：§C 的 20 款 ×2 轮（脚本 + jev）与 10 款 ×2 轮（playjev）——`UNSTABLE` 名单与
  分歧点全部来自真实 run，见 §C.3。

### A.3 每处 verdict 带「档位 + 轮次」（Y3）

* 新增 `run --round N`；`player.json -> verdict_context` =
  `{verdict, window_frames, round, reporting_frames, at_reporting_window, backend, player, game,
  change_margin, counts_as_pass, what}`；`player.json -> qualified_verdict` = `PASS @w90 r2`
  （低于报告档时追加 `[reference only: ...]`）。
* **工具输出**：`run` 结束打两行——`VERDICT <game>/<backend>: <qualified_verdict> -- <why>` 与
  `verdict_context: {...}`；`session.json -> measurement_window` 同时记录 `reporting_frames` 与 `round`。
* **`resummarise` 不丢档位**：从旧 `player.json -> verdict_context` 继承 `window_frames` / `round`
  传给 `summarise`，否则一次重算会把"参考读数"悄悄升格成通过。
* **gate.json**：`record_model_player_criterion` 从 `steps.jsonl` **旁边**的 `player.json -> verdict_context`
  读回（文件不存在则 `unrecorded` 且不做任何 remove），写
  `gate.json -> model_player_criterion.evidence.verdict_context` 与 `... -> qualified_verdict`。
* **模板**：`recovery\tasks\TEMPLATE-logic-feedback.md` 新增 **§1.2d**（三条硬要求 + `SENSITIVE`≠`UNSTABLE`）
  与反例 **26–31**。

### A.4 报告档位下 ≥2 轮重跑（Y4）与 `SENSITIVE` 并列（Y5）

见 §C（逐款两轮对照表、`UNSTABLE` 名单、`SENSITIVE` 名单、新旧分布）。**两件事分开写**：
`UNSTABLE` = 同一档的两轮；`SENSITIVE` = 同一轮的两档（TASK-139 的 w30 记录 + 本批的 w90 两轮）。

---

## B. 目标 B —— 4 款游戏侧缺陷的修复（修前 → 修后证据）

**修前证据**：`runs\model-player\t140-prefix4-w90-r1\<game>\scripted\`（4 款，报告档位 w90 r1，
**HEAD 代码**，2026-09-28 07:03–07:07 跑）；`asteroids` 的"死亡不重生"另有 TASK-139 的**模型臂 w90**
（`runs\model-player\t139-jev-v3-w90\asteroids\jev\`）。
**修后证据**：`runs\model-player\t140-postfix4-w90-r2\`（r2，见 §B.4）、`t140-postfix4-w90-r3\`（bomberman，
含拒绝计数器修复）与 **§C 的两轮全量 sweep**（`t140-scripted-w90-r1/-r2`，含 `--round`）。
修前副本/哈希：`runs\model-player\t140-build\{game}.txt` 与 §F 的源码 sha256。

### B.1 `asteroids`：死亡后必须重生（Y6）

* **修前（一等证据，TASK-139 §A.3 的模型臂 w90，本批**重新读图复核**）**：步骤 5 `Lives 3 → 2` 之后
  连续 **7 步** `pixel_diff = 0` / `gameplay_movement = 0`，而 `GameOver=false`、`Lives=2`；
  两帧 **sha256 完全相同**：
  `frames\016_05_after.png` 与 `frames\037_12_after.png` 都是
  `c09b58739e8d3094b081f997554e29ca6e602b55d2acdc757664aaa92ddefe4d`（10111 B，800×600）。
  本批 `read_image` **实看**这两张：HUD 都是 `SCORE 0  LIVES 2  ROCKS 4`，四角四块米色岩石，
  **画面里没有任何飞船**（视觉逐像素相同）。
* **代码成因**：`CheckShipHits()` 里只写 `ShipAlive = false`（飞船节点 `Visible=false`），
  而 `RespawnShip()` **只有会话钩子会调**；`DriftSpeed` 默认 0（岩石不动），于是"船没了 = 世界停了"。
* **修法（可开关）**：新增导出 `RespawnDelay`（默认 **1.0 s**，`0` = 回到修前"永不重生"）、
  `RespawnInvuln`（默认 **1.5 s**）、`RespawnTimer` / `InvulnTimer` / `ShipInvulnerable` /
  `ShipVisible` / `Respawns`；`_Process` 里跑重生倒计时（**世界照常更新**：子弹、漂移的岩石、
  命中判定都在），重生落点仍是场地中心 + 无敌闪烁（`ApplyShip` 里按 `_shieldPhase` 闪烁，
  `ShipVisible` 记录**实际画了什么**）；`CheckShipHits` 在无敌期直接返回（否则静态场上"同一块岩石"
  会在重生那一帧立刻再撞一次）；`RespawnShip()` 公开钩子与自动重生共用**同一个** `RespawnNow()`。
* **修后证据**：脚本臂 w90 两次（`t140-postfix4-w90-r2`、`t140-scripted-w90-r1/-r2`）都是 8 步全变化
  （`real=8`、`rate=1.0`）。**"撞击 → 重生"的模型臂 w90 实证**见 §C.5（本批重跑后补：同一款、同窗，
  修前是 §B.1 的 7 步零变化）。

### B.2 `frogger`：出生格不被车压住，一次按键 = 一步 / ≤1 命（Y7）

* **修前（一等证据，`t140-prefix4-w90-r1/frogger/scripted`）**：run **只有 1 个注入步**
  （`injected_steps=1`），该步 `LastEvent: '' → 'lives lost reason=hit by car at=6,13 lives=0 game over'`、
  **`Lives 3 → 0`**、`GameOver false → true`，青蛙**没离开出生格**。
  读图 `frames\004_01_after.png`（sha256 `bf3db4758b74fcaf7af2f6a2feab3eeaa90a84497831a6b07112cd0c311cd13a`）：
  HUD `SCORE 0  LIVES 0  HOMES 0/5` + 右上 `GAME OVER`，绿青蛙仍在**最底部出生带** col 6。
* **成因（逐字）**：出生点 `(6,14)` 的**正上方** `(6,13)` 停着第 5 辆车（`CarStart = {... {6,13,1}}`），
  而 `InputRepeat = 0.12 s` + "按住即重复迈步"把**一次 350 ms 注入**变成 3 步：
  迈上去被撞（3→2）→ `ResetFrog` 回出生格 → 键还按着 → 再迈（2→1）→ 再迈（1→0）。
* **修法（三件，全部可开关）**：
  1. **车不再压在出生列正上方**：`CarStart` 第 5 项 `{6,13,1}` → `{1,13,1}`（该车道仍有车）；
     新增导出 `StartCellClear`（出生格与正上方是否**没有**车），`UpdateHud()` 每次重绘都重算。
  2. **按键边沿触发**：`KeyHeld` / `PressConsumed` / `HopsThisPress` / `LivesLostThisPress`；
     一次按下**只**迈一步，按住要**自动重复**必须再连续按住 `RepeatHold = 0.5 s`
     （长于任何一次注入的 350 ms）；`RepeatHold = 0` 关闭自动重复。
  3. **掉命冷却**：`DeathGrace = 0.6 s`（`GraceTimer`）期间不移动、不再掉命，
     `CheckFrogSafety()` 在冷却期直接返回（重置到出生格也安全）。
* **修后证据（一等证据，`t140-postfix4-w90-r2/frogger/scripted`）**：
  * **单次注入只走 1 步**：8 个注入步，每步**恰好一格**、`px=1152`（= 24×24 青蛙 + 一格位移），
    例如步 1 `FrogRow 14 → 13`、`LastEvent: '' → 'moved to=6,13 score=0 lives=3'`，
    步 2 `FrogRow 13 → 12`；`HopsThisPress`/`LivesLostThisPress` 在松键时归零（故不出现在差分里），
    "一步"由**格数**直接证明。run 结果：8/8 变化、`real=8`、`rate=1.0`、
    `verdict=PASS`（修前 `INCONCLUSIVE` 且只有 1 步）。
  * **≤1 命**：该修后 run **一次命都没掉**（`Lives 3` 全程不变），与修前"一次注入掉 3 命"形成对照；
    机制上是"按下边沿只迈一步 + 掉命即 0.6 s 冷却"两道锁，任一道都保证单次注入 ≤1 命。
  * 读图 `frames\004_01_after.png`（sha256 `fa3cc225e8b609e874a2177fca8d2efa8e60cb9d2890ba794c6cdc3d1525363e`）：
    HUD `SCORE 0  LIVES 3  HOMES 0/5` + `HOMES 0/5`，青蛙已**上移一格**（y≈536），
    同一车道里那辆黄车在 col 1（**不在出生列**）。

### B.3 `bomberman`：已放置的炸弹必须可见；`AutoClock` 取舍写明（Y7）

* **修前（一等证据，`t140-prefix4-w90-r1/bomberman/scripted`）**：步 1/3 都 `bomb_place`，
  `BombsActive 0→1→2`、HUD `BOMBS 2`，**盘面上看不到任何炸弹**；
  两帧字节相同：`frames\010_03_after.png` 与 `frames\013_04_after.png` 同为
  `865e926f74e1d88f7f6bff479c406c18ce81ca1dc3ebf16fb536c6593931fc8c`（9654 B，800×600）。
  读图 `frames\007_02_after.png`（`a18448cdbe95a7ed9a0eea54cc779d8c1d95c636d7a35315332784919162fcf1`）：
  HUD `BOMBS 1`，蓝玩家在 (1,2)，**它上一格 (1,1) 是空地板**——那里正放着一颗炸弹。
  成因：炸弹矩形颜色 `(0.15,0.15,0.20)` 画在空地板格 `(0.15,0.17,0.21)` 上（单通道差 0.02）。
* **第二条（本批新发现，同一处）**：`HandleInput` 的守卫
  `place && !_prevBomb && BombsActive < MaxBombs && BombAt(...) < 0` 在"上限已满 / 格上已有炸弹"时
  **静默丢弃**该次按键：修前步 5/7/9 是 `accepted and nothing changed` 且**状态差分为空**
  （只有 `Elapsed`/`Ticks`），与"这个键根本没接上"完全无法区分。
* **修法**：①声明色 `BombColor=(0.95,0.35,0.10)` / `BombColorDue=(1.0,0.94,0.25)` 取代原暗色；
  ②新增导出 `BombsVisible`（可见炸弹矩形数）与 `BombMinContrast`（炸弹与其所压格子的**逐通道最小差**），
  在 `ApplyBoard()` 里每次重绘实测；③守卫删掉，把决定交回 `PlaceBomb()`——它本来就把
  `game_over` / `bomb_already_here` / `max_bombs` 三种拒绝写进 `RejectedMoves`，
  本批再新增 **`RejectedPlaces`** 精确计数器；④`tools/playability_controls.json ->
  games.bomberman.refusal_evidence` 收窄成**两个精确计数器**
  （`game_side_fields = ["RejectedMoves","RejectedPlaces"]`，旧宽泛模式留在 `keys_before_task140`、
  `value_words` 清空）。**这不放宽判据**：被拒绝的投放现在有游戏自己的记录，
  正是 TASK-116 约定 #1 与 TASK-139 §1.B 的拒绝边界要处理的情形。
* **修后证据（一等证据，`t140-postfix4-w90-r3/bomberman/scripted`）**：
  * 步 1 `bomb_place`：`BombList '' → '1,1,3'`、`BombsVisible 0 → 1`、
    **`BombMinContrast 0.0 → 0.79999995`**、`Bomb_0.vis False → True`、
    `Bomb_0.pos [0,0,26,26] → [178,126,26,26]`、**`pixel_diff 0 → 138`**（= 炸弹矩形露在玩家 sprite
    之外的像素）。
  * 读图 `frames\007_02_after.png`（sha256 `bf25a2a153d9096a84f2f6691b20a6bde3ed23995dd9ef42d0d98803e944641b`）：
    HUD `BOMBS 1`，蓝玩家在 (1,2)，**上一格 (1,1) 有一颗看得见的橙红炸弹**——
    与修前同一步同位置的空地板形成逐像素对照。
  * 拒绝不再静默：步 4/6/8（撞墙/砖的移动）与 **步 5/7/9（上限已满的投放）** 现在都写
    `RejectedMoves`/`RejectedPlaces` ⇒ 被识别为**合法拒绝**（`refused_steps=[4,5,6,7,8,9]`），
    rated 6 步全变化、`real=6`、`rate=1.0`、**`verdict=PASS`**（修前 `INCONCLUSIVE`、rate 0.6667）。
* **`AutoClock` 取舍（写明）**：**保持 0**。理由：本工程的确定性规则要求"世界是状态字符串的纯函数"
  （爆破格可被独立重算），而 TASK-136 §6.2 实测把时钟打开是**更差**的——炸弹在玩家旁边炸、
  一次输入就掉命、整局 3 步结束（"一按就死"）。**代价照写**：playtest run 里 `Detonations` 仍恒为 0，
  只有显式调 `StepFuse`（或驱动自己打开时钟）才有爆破；**可见性与引信无关**——炸弹在放下的那一帧就在画面上。

### B.4 `flappy`：对照窗与动作窗都在"世界在跑"下成立（Y7）

* **修前（一等证据，`t140-prefix4-w90-r1/flappy/scripted`）**：`AutoRun=false` ⇒ 世界不自走，
  12 步 `real=1`、`rate=0.0833`，除步 1（`BirdVelocity 0 → -420`）外每步 `px=0 mv=0`；
  读图 `frames\002_01_before.png`（sha256 `0f53a0d32ceb9ad239a7cbe2e7cfebbcc347dbcf466d7da96a0ace51ad185523`）：
  HUD `SCORE 0  PASSED 0/5  FRAME 0`，黄鸟悬在中左 `(x≈195,y≈313)`——**`FRAME 0` 就是"世界没在跑"**。
  （该 sha256 与 TASK-136 §7 记录的第 5/6 行**逐字相同**，是跨批次复现。）
* **TASK-136 试过 `AutoRun=true` 并回退的原因**：鸟在**对照窗内**就落地死亡（`GameOver`），
  随后注入的 `flap` 打在已结束的局面上；本批**实测复现**了这一条，并定位得更精确：
  鸟悬在 `y=300`（盒子 300..336）时，gap 为 130..290 的那根管子满足 `top >= gapBottom`（300 ≥ 290）
  ⇒ **撞管**，一两个窗口内世界就结束。
* **修法（全部可开关）**：
  1. `AutoRun = true`（默认；`SetAutoRun` 仍可关）；
  2. **`IdleHover = true`：READY 相位停在"触地条"上**（不是悬在半空）——新增 `GroundHeight=84`，
     管子下半截止于 `GroundTop()`，`HitsPipe()` 对"顶边已到触地条"的鸟直接判否，
     于是**停在地上的鸟不会被管子撞到**，世界可以一直跑；
  3. **`GroundIsFatal = false`：触地是着陆**（回到 READY、`Landings++`），只有撞管才结束；
  4. 重开局不再把时钟关掉（删掉 `AutoRun = false;`），并重置 `BirdReady` / `Landings`；
     导出 `BirdReady` / `Landings` / `GroundTop()` 进 `Dump()`。
  （`IdleHover=false` + `GroundIsFatal=true` 即修前行为，是"可开关变体"的另一半。）
* **修后证据（`t140-postfix4-w90-r2/flappy/scripted`，9 步）**：
  * **两窗都在世界运行下成立**：动作步的**对照窗** `ctl_px = 45590..74290`、`cmv = 2476..2494`
    （管子真的在滚，`FrameCount`/`Pipe0X`/`Pipe_*.pos` 在**两个窗口**里都在变），
    而同一窗口里**鸟的 `BirdY`/`BirdVelocity` 完全静止**（READY 停在地面）；
    动作窗 `px = 109135..128294`、鸟真的起飞（`BirdReady false→true`、`BirdY`/`BirdVelocity` 变化）。
  * 读图 `frames\002_01_before.png`（sha256 `9082895f8df88d99b7077913fae0f6d734b59d94ea8aa7a9338fd420910b906b`）：
    HUD `SCORE 20  PASSED 2/5  FRAME 291`（**世界在跑**），黄鸟**停在底部深绿色触地条上**，
    三组管子分布在不同位置——与修前的 `FRAME 0` 悬空鸟形成对照。
  * run 结果：**三次修后 run 同类**——`t140-postfix4-w90-r2` 9 步 `real=8`、`rate=0.8889`；
    报告档位两轮 `t140-scripted-w90-r1/r2` 各 12 步 `real=7`、`rate=0.5833`；都是
    `PASS(baseline only)`、`counts_as_pass=false`（**不是 PASS**；确切原因见下）。
* **为什么仍不是 PASS（确切原因，D208）**：`flappy` 的玩法观测量声明里含 `/root/Main/Pipe`，
  于是三根管子六个矩形每窗各移动约 270 px，`mv`/`cmv` 里各占约 **2446**；strict 要求
  `mv ≥ 2×cmv`，而一次 flap 的贡献 **< 1000**（鸟的 `|Δy| + 节点位移 + |Δv|`）。
  步 3/5/7/9 之所以在 strict 下"变化"，是**靠像素项以 2.5002×（114087 vs 2.5×45590=113975）**擦线通过，
  步 1 差 0.5%（128294 < 185725）⇒ 整局只能算 baseline 通过。
  **本批没有为此调参**（不改声明、不调 `PipeSpeed`、不改尺子）：这是"世界自走量 > 玩家动作量"的
  横向卷轴游戏在 strict 下的结构性边界，已登记为 D208 并列入 §G 遗留风险。
* **`AutoRun=true` 的一条副作用（如实报）**：世界一跑起来，**管子会自己越过鸟的 x**，于是
  `PipesPassed`/`Score` 在鸟落在地面不动时也会增长（post-fix 第 1 步的 `PASSED 2/5`，
  更晚的步到 `PASSED 5/5` ⇒ `Won=true`、`GameOver=true`，run 因此只有 9 步）。
  这是该游戏**原有的计分规则**（`pipe.X + PipeWidth < BirdX` ⇒ 记一分），修前因为世界不走所以看不见；
  本批**没有改计分**，只登记（§G 遗留风险 ④）。

---

## C. 目标 C —— 报告档位下重跑（≥2 轮）与产物

> 生成器：`runs\model-player\_scripts\t140_runall.py`（链式，**串行**，每段独立端口）→
> `t140_sweep.py`（逐款，命令经 `t140_cmd.py` 入台账）→ 分析 `t140_stability.py`。
> 三个臂、每个臂两轮，全部 `--window-frames 90 --round {1,2} --change-margin strict`。

### C.1 覆盖自证

| run 前缀 | 后端目录 | 轮次 | 覆盖 | 结果文件 |
|---|---|---|---|---|
| `t140-scripted-w90-r1` | `scripted` | 1 | **20/20** | `_scripts\t140_results_t140-scripted-w90-r1.json` |
| `t140-scripted-w90-r2` | `scripted` | 2 | **20/20** | `...-r2.json` |
| `t140-jev-v3-w90-r1` | `jev` | 1 | **20/20** | `_scripts\t140_results_t140-jev-v3-w90-r1.json` |
| `t140-jev-v3-w90-r2` | `jev` | 2 | **20/20** | `...-r2.json` |
| `t140-playjev-v3-w90-r1` | `playjev` | 1 | **10/10** | `_scripts\t140_results_t140-playjev-v3-w90-r1.json` |
| `t140-playjev-v3-w90-r2` | `playjev` | 2 | **10/10** | `...-r2.json` |

每款每轮一个 `player.json` + `steps.jsonl` + `frames/*.png` + `demo.png`。
**playjev 覆盖 10 款**（与 TASK-139 同一集合，如实报；预算未允许 20 款 ×2 轮）。

### C.2 脚本臂：两轮对照表 + `UNSTABLE`（`UNSTABLE: (none)`）

（由 `t140_stability.py --arm scripted` 生成，原文 `_scripts\t140_stability_scripted.md`；
`*` = `counts_as_pass: true`）

| game | T140 w90 r1 | T140 w90 r2 | T139 w30（记录） | T139 w90（记录） | UNSTABLE | SENSITIVE | CROSS-BATCH |
|---|---|---|---|---|---|---|---|
| `asteroids` | `PASS`* | `PASS`* | `PASS`* | `PASS`* | | | |
| `bomberman` | `PASS`* | `PASS`* | `INCONCLUSIVE` | `INCONCLUSIVE` | | **SENSITIVE** | **DIFFERS** |
| `breakout` | `INCONCLUSIVE` | `INCONCLUSIVE` | `INCONCLUSIVE` | `FAIL` | | | **DIFFERS** |
| `flappy` | `PASS(baseline only)` | `PASS(baseline only)` | `INCONCLUSIVE` | `INCONCLUSIVE` | | **SENSITIVE** | **DIFFERS** |
| `frogger` | `PASS`* | `PASS`* | `INCONCLUSIVE` | `INCONCLUSIVE` | | **SENSITIVE** | **DIFFERS** |
| `game2048` | `PASS`* | `PASS`* | `PASS`* | `PASS`* | | | |
| `lunarlander` | `PASS`* | `PASS`* | `PASS`* | `PASS`* | | | |
| `match3` | `PASS`* | `PASS`* | `PASS`* | `PASS`* | | | |
| `minesweeper` | `PASS`* | `PASS`* | `PASS`* | `PASS`* | | | |
| `missilecommand` | `PASS`* | `PASS`* | `PASS`* | `PASS`* | | | |
| `pacman` | `PASS`* | `PASS`* | `PASS`* | `PASS`* | | | |
| `platformer` | `INCONCLUSIVE` | `INCONCLUSIVE` | `PASS`* | `INCONCLUSIVE` | | **SENSITIVE** | |
| `pong` | `PASS`* | `PASS`* | `PASS(baseline only)` | `PASS`* | | **SENSITIVE** | |
| `puzzlebobble` | `PASS`* | `PASS`* | `PASS`* | `PASS`* | | | |
| `rtype` | `PASS`* | `PASS`* | `PASS`* | `PASS`* | | | |
| `snake` | `PASS`* | `PASS`* | `PASS`* | `PASS`* | | | |
| `sokoban` | `PASS`* | `PASS`* | `PASS`* | `PASS`* | | | |
| `spaceinvaders` | `PASS`* | `PASS`* | `PASS`* | `PASS`* | | | |
| `tetris` | `PASS`* | `PASS`* | `PASS`* | `PASS`* | | | |
| `towerdefense` | `PASS`* | `PASS`* | `PASS`* | `PASS`* | | | |

* **`UNSTABLE` 名单（脚本臂，本批两轮）**：**空**。20 款在报告档位的两轮独立完整运行上逐款类别一致。
* **`SENSITIVE`（同一轮的不同档）**：`bomberman` / `flappy` / `frogger` / `platformer` / `pong`。
  TASK-139 自己标过的 `breakout`/`platformer`/`pong` 里，`breakout` 在本批两轮与 TASK-139 的 w30
  同类别故不在本列；`bomberman`/`flappy`/`frogger` 的差异**主因是修游戏**（见下一行的归因）。
  **没有被"两轮一致"掩盖**：它与 `UNSTABLE` 并列在同一张表里。
* **`CROSS-BATCH`（本批 w90 vs TASK-139 的 w90，同档的第三次独立读数）**：
  `bomberman` / `breakout` / `flappy` / `frogger` 与前两次不一致，**逐款归因**：
  * `bomberman` / `flappy` / `frogger`：本批修了这 3 款（§B 有修前→修后证据）⇒ 差异来自修法本身。
  * **`breakout`：本批没有碰它**（`projects/breakout/**` 未改）。TASK-139 的 w90 读 `FAIL`，
    本批 w90 两轮都读 `INCONCLUSIVE` ⇒ **同一档的第三次独立完整运行与前两次不一致**。
* **这条的机器证据（Y2 的"实测触发"）**：三次独立完整运行并排交给 `stability`：
  ```
  playtest_player.py stability --run <r1>/breakout/scripted/player.json \
      --run <r2>/breakout/scripted/player.json --run t139-scripted-w90/breakout/scripted/player.json
  => STABILITY breakout/90: UNSTABLE -- 1=INCONCLUSIVE, 2=INCONCLUSIVE, None=FAIL
     分歧点：step 2/3/4 的 injected / accepted / changed / changed_strict / step_verdict
             （`ok_ack_and_changed` vs `no_ack_no_change`）
  ```
  产物：`_scripts\t140_unstable_breakout.json`。分歧点是 **`ack` 丢失**（TASK-138 defect ⑨ 的
  `no_ack_no_change`）——TASK-139 定位过的机制**在 w90 上同样会发生**。
* **结论（本批新增的判据认识）**：`reporting_frames=90` 是**必要**的纪律（裸 verdict 不是类别证据），
  但不是"这一档可复现"的充分保证；`UNSTABLE` 应在**所有可得的同档独立完整运行**上计算（跨批计入），
  报告写"**这两轮一致**"，不写"这一档可复现"。已写进模板反例 32 与 D209。

### C.3 模型臂（jev）与 playjev 臂

**模型臂（`--backend jev --variant V3 --change-margin strict`，20/20 ×2）**
（原文 `_scripts\t140_stability_model.md`；`*` = `counts_as_pass: true`）

| game | T140 w90 r1 | T140 w90 r2 | T139 w30（记录） | T139 w90（记录） | UNSTABLE | SENSITIVE | CROSS-BATCH |
|---|---|---|---|---|---|---|---|
| **`asteroids`** | `PASS`* | `PASS(baseline only)` | `PASS`* | `FAIL` | **UNSTABLE** | **SENSITIVE** | **DIFFERS** |
| `bomberman` | `INCONCLUSIVE` | `INCONCLUSIVE` | `INCONCLUSIVE` | `INCONCLUSIVE` | | | |
| `breakout` | `FAIL` | `FAIL` | `FAIL` | `FAIL` | | | |
| `flappy` | `FAIL` | `FAIL` | `INCONCLUSIVE` | `INCONCLUSIVE` | | **SENSITIVE** | **DIFFERS** |
| `frogger` | `INCONCLUSIVE` | `INCONCLUSIVE` | `INCONCLUSIVE` | `INCONCLUSIVE` | | | |
| `game2048` | `INCONCLUSIVE` | `INCONCLUSIVE` | `INCONCLUSIVE` | `INCONCLUSIVE` | | | |
| `lunarlander` | `INCONCLUSIVE` | `INCONCLUSIVE` | `INCONCLUSIVE` | `INCONCLUSIVE` | | | |
| `match3` | `INCONCLUSIVE` | `INCONCLUSIVE` | `INCONCLUSIVE` | `INCONCLUSIVE` | | | |
| `minesweeper` | `INCONCLUSIVE` | `INCONCLUSIVE` | `INCONCLUSIVE` | `INCONCLUSIVE` | | | |
| `missilecommand` | `INCONCLUSIVE` | `INCONCLUSIVE` | `INCONCLUSIVE` | `INCONCLUSIVE` | | | |
| `pacman` | `INCONCLUSIVE` | `INCONCLUSIVE` | `INCONCLUSIVE` | `INCONCLUSIVE` | | | |
| `platformer` | `INCONCLUSIVE` | `INCONCLUSIVE` | `INCONCLUSIVE` | `INCONCLUSIVE` | | | |
| `pong` | `PASS(baseline only)` | `PASS(baseline only)` | `FAIL` | `PASS(baseline only)` | | **SENSITIVE** | |
| `puzzlebobble` | `INCONCLUSIVE` | `INCONCLUSIVE` | `INCONCLUSIVE` | `INCONCLUSIVE` | | | |
| `rtype` | `INCONCLUSIVE` | `INCONCLUSIVE` | `INCONCLUSIVE` | `INCONCLUSIVE` | | | |
| `snake` | `INCONCLUSIVE` | `INCONCLUSIVE` | `INCONCLUSIVE` | `INCONCLUSIVE` | | | |
| `sokoban` | `INCONCLUSIVE` | `INCONCLUSIVE` | `INCONCLUSIVE` | `INCONCLUSIVE` | | | |
| `spaceinvaders` | `INCONCLUSIVE` | `INCONCLUSIVE` | `FAIL` | `INCONCLUSIVE` | | **SENSITIVE** | |
| `tetris` | `PASS`* | `PASS`* | `PASS`* | `PASS`* | | | |
| `towerdefense` | `INCONCLUSIVE` | `INCONCLUSIVE` | `INCONCLUSIVE` | `INCONCLUSIVE` | | | |

* **`UNSTABLE` 名单（模型臂）**：**`asteroids`** —— r1 `PASS @w90 r1`、r2 `PASS(baseline only) @w90 r2`。
  这是 **`UNSTABLE` 的第一等实测触发**（不是构造的）：同款、同档、同命令、同代码，两轮之间从
  `PASS` 掉到 `PASS(baseline only)`。
  **分歧点（机器给出，`_scripts\t140_stability_model.json` / `t140_divergence.py model`）**：
  * `step 6  changed_strict  round1=True  round2=False  （pixel_diff 965 vs 968，差 3 个像素）`
  * `step 9/10/11/12  step_present  round1=False round2=True`（r1 在 8 步后触发"连续 8 步 distinct
    actions 且全变化"的**耐心提前停止**，r2 跑了 12 步 —— 这条是**运行长度差异**，不是判据分歧，
    工具如实把它单列成 `step_present`，没有混进 `changed`）。
  * 逐轮读数：r1 `real=8 rate=1.0`；r2 `real=10 rate=0.8333`（**一次 3 像素的 strict 余量差异**改变了类别）。
  这直接说明 §C.2 的 `reporting_frames=90` 纪律是**必要**的：一个 `PASS` 与一个
  `PASS(baseline only)` 之间可以只差 3 个像素。
* **模型臂分布**：r1 `PASS 2 / baseline-only 1 / FAIL 2 / INCONCLUSIVE 15`；
  r2 `1 / 2 / 2 / 15`（`asteroids` 与 `pong` 的类别在两轮之间互换，`asteroids` 因此进 `UNSTABLE`）。

**playjev 臂（`--backend playjev --variant V3`，10/10 ×2）**
（原文 `_scripts\t140_stability_playjev.md`；TASK-139 只跑过 w30，故 "other-window" 列是 w30）

| game | T140 w90 r1 | T140 w90 r2 | T139 w30（记录） | UNSTABLE | SENSITIVE |
|---|---|---|---|---|---|
| `asteroids` | `PASS`* | `PASS`* | `INCONCLUSIVE` | | **SENSITIVE** |
| `game2048` | `PASS`* | `PASS`* | `PASS`* | | |
| `match3` | `INCONCLUSIVE` | `INCONCLUSIVE` | `INCONCLUSIVE` | | |
| `minesweeper` | `INCONCLUSIVE` | `INCONCLUSIVE` | `INCONCLUSIVE` | | |
| `pacman` | `FAIL` | `FAIL` | `FAIL` | | |
| `pong` | `INCONCLUSIVE` | `INCONCLUSIVE` | `INCONCLUSIVE` | | |
| `rtype` | `PASS`* | `PASS`* | `PASS`* | | |
| `snake` | `INCONCLUSIVE` | `INCONCLUSIVE` | `INCONCLUSIVE` | | |
| `sokoban` | `PASS`* | `PASS`* | `PASS`* | | |
| `tetris` | `INCONCLUSIVE` | `INCONCLUSIVE` | `INCONCLUSIVE` | | |

* playjev `UNSTABLE: (none)`；两轮分布都是 `PASS 4 / baseline-only 0 / FAIL 1 / INCONCLUSIVE 5`
  （TASK-139 w30 是 `3 / 0 / 1 / 6`）；`asteroids` 因为**修了游戏**而从 INCONCLUSIVE 变 PASS
  （w30 vs w90 的两档对照里因此标 `SENSITIVE`，归因是修法本身）。

### C.4 新分布

| 臂 / 档 | 分布（PASS / baseline-only / FAIL / INCONCLUSIVE） | 备注 |
|---|---|---|
| 脚本 · TASK-136 记录 | `9 / 1 / 4 / 6` | 旧基准 |
| 脚本 · TASK-139 w30 | `15 / 1 / 0 / 4` | TASK-139（**本批工具会把它们读成"低于报告档位的参考读数"**，见 §G.7） |
| 脚本 · TASK-139 w90 | `15 / 0 / 1 / 4` | TASK-139 |
| **脚本 · TASK-140 w90 r1** | **`17 / 1 / 0 / 2`** | 本批（§C.2） |
| **脚本 · TASK-140 w90 r2** | **`17 / 1 / 0 / 2`** | 本批（§C.2） |
| 模型 · TASK-139 w90 | `1 / 1 / 2 / 16` | TASK-139 |
| **模型 · TASK-140 w90 r1** | **`2 / 1 / 2 / 15`** | 本批（§C.3） |
| **模型 · TASK-140 w90 r2** | **`1 / 2 / 2 / 15`** | 本批（§C.3）；与 r1 的差额就是 `asteroids` 的 `UNSTABLE` |
| playjev · TASK-139 w30 | `3 / 0 / 1 / 6` | 10 款 |
| **playjev · TASK-140 w90 r1/r2** | **`4 / 0 / 1 / 5`** | 10 款，两轮相同 |

脚本臂 15→17 的差额来自**修游戏**（`frogger`、`bomberman` 从 INCONCLUSIVE 变 PASS），不是判据变化；
模型臂 r1→r2 的差额来自**不可复现**（`asteroids`），不是代码变化。

### C.5 `asteroids` 修后：撞击 → 重生（Y6 的修后一侧）

本批的定向探针（`_scripts\t140_respawn_probe.py`，用游戏**自己的** `ForceTestState("ship=650,130")`
把飞船放到岩石上，再用游戏**自己的**导出属性逐样本读回；端口 9989，一次游戏进程、两个对照case）：

| case | `RespawnDelay` / `RespawnInvuln` | 撞击后 `ShipAlive` 序列（前 12 个样本） | `Respawns` | 最长连续 `pixel_diff=0` | 结论 |
|---|---|---|---|---|---|
| 可开关变体（= 修前行为） | `0 / 0` | `F,F,F,F,F,F,F,F,F,F,F,F` | `0`（24 样本全是 0） | **23** | 修前的"死亡即冻结"被**按需复现** |
| 出厂默认 | `1.0 / 1.5` | `F,F,F,F,T,T,T,T,T,T,T,T` | `0→1`（第 5 样本起） | 15（到重生为止） | **撞 → 掉一命 → 1.0 s 后重生，画面重新变化** |

* 默认 case 的逐样本（`probe.json`）：`RespawnTimer 0.95 → 0.93 → 0.72 → 0.41 → 0.12` ⇒ 第 5 样本
  `LastEvent = 'respawned at=400,300 lives=2 invuln=1.50 respawns=1'`、`ShipAlive=True`、
  `InvulnTimer 1.32 → 1.02 → 0.74 → 0.44 → 0.12 → 0`，且 `ShipVisible` 在
  `True/False/True/True` 之间闪 ⇒ 该样本 `pixel_diff=484`（**护盾可见**），无敌结束后回 `0`
  （场上无输入、`DriftSpeed=0`，这是**应有的**静止）。
* **修后死亡窗口那一帧与 TASK-139 的冻结帧逐字节相同**：
  `028_default_respawn_1s_01.png`、`031_default_respawn_1s_04.png`、
  `003_variant_respawn_delay_0_01.png` 的 sha256 都是
  `c09b58739e8d3094b081f997554e29ca6e602b55d2acdc757664aaa92ddefe4d`
  ——**与 TASK-139 `016_05_after.png` / `037_12_after.png` 完全相同**；改变的是**下一帧**：
  重生帧 `032_default_respawn_1s_05.png` = `d60ff4811ea97444acbca36a3b9ff4ba6d6914a54480dda48769d8f0d16c3d03`。
* 读图另见 §C.7 第 9/10 行（全尺寸 800×600 实看）。
* 模型臂 w90 的类别变化也与此一致：TASK-139 w90 的 `asteroids` 因"撞后 7 步零变化"读 `FAIL`，
  本批两轮读 `PASS` / `PASS(baseline only)`（**两轮不一致**，见 §C.3 的 `UNSTABLE`）。

### C.6 真实 w30 run 触发 `BELOW_REPORTING_WINDOW`（Y1 的实测触发）

`runs\model-player\t140-w30-demo\asteroids\scripted\player.json`（`--window-frames 30 --round 1`，
端口 9987，2026-09-28 09:30）：

* `verdict = "PASS"`（测量照旧），`verdict_context = {"window_frames": 30, "round": 1,
  "reporting_frames": 90, "at_reporting_window": false, ...}`
* `reporting_window.state = "BELOW_REPORTING_WINDOW"`、`counts_as_pass = false`、
  `qualified_verdict = "PASS @w30 r1 [reference only: window 30 < reporting 90]"`
* 同一款在同一档 90 帧下（`t140-scripted-w90-r1/r2`）`counts_as_pass = true`。

### C.7 关键帧实看（Y9）

全部用 `read_image` **实看全尺寸 800×600 原图**（下表"尺寸"一列即工具回报的镜像尺寸），
每条描述附**可机检锚点**（完整 sha256 + 该步的声明字段实测值）。

| # | 帧（仓库相对路径，`godot-mcp/` 起） | 尺寸 | 我看到了什么（锚点） | 结论 |
|---|---|---|---|---|
| 1 | `runs/model-player/t140-prefix4-w90-r1/frogger/scripted/frames/004_01_after.png` | 800×600 | HUD `SCORE 0  LIVES 0  HOMES 0/5` + `GAME OVER`；绿青蛙仍在**最底部出生带 col 6**；`sha256=bf3db475…cd13a`；该步 `Lives 3→0`、`LastEvent='lives lost reason=hit by car at=6,13 lives=0 game over'` | **修前**：一次注入 = 三条命 |
| 2 | `runs/model-player/t140-postfix4-w90-r2/frogger/scripted/frames/004_01_after.png` | 800×600 | HUD `SCORE 0  LIVES 3  HOMES 0/5`；青蛙**上移一格**（y≈536）；同车道黄车在 col 1；`sha256=fa3cc225…25363e`；`FrogRow 14→13` | **修后**：一次注入 = 一格、0 命 |
| 3 | `runs/model-player/t140-prefix4-w90-r1/bomberman/scripted/frames/007_02_after.png` | 800×600 | HUD `BOMBS 1`；蓝玩家在 (1,2)，**它上一格 (1,1) 是空地板**；`sha256=a18448cd…162fcf1` | **修前**：炸弹不可见 |
| 4 | `runs/model-player/t140-postfix4-w90-r3/bomberman/scripted/frames/007_02_after.png` | 800×600 | 同一 HUD `BOMBS 1`、同一玩家位置，**上一格是一颗橙红炸弹**；`sha256=bf25a2a1…e944641b`；另一步 `BombMinContrast 0→0.79999995`、`BombsVisible 0→1`、`pixel_diff 0→138` | **修后**：炸弹可见 |
| 5 | `runs/model-player/t140-prefix4-w90-r1/flappy/scripted/frames/002_01_before.png` | 800×600 | HUD `SCORE 0  PASSED 0/5  FRAME 0`；黄鸟悬在中左 `(x≈195,y≈313)`；`sha256=0f53a0d3…185523`（**与 TASK-136 §7 记录的 `0f53a0d3…` 逐字相同**） | **修前**：世界不自走（`FRAME 0`） |
| 6 | `runs/model-player/t140-postfix4-w90-r2/flappy/scripted/frames/002_01_before.png` | 800×600 | HUD `SCORE 20  PASSED 2/5  FRAME 291`；黄鸟**停在底部深绿触地条上**，三组管子分布不同；`sha256=9082895f…10b906b` | **修后**：世界在跑 + 鸟栖地 |
| 7 | `runs/model-player/t139-jev-v3-w90/asteroids/jev/frames/016_05_after.png` | 800×600 | HUD `SCORE 0  LIVES 2  ROCKS 4`；四角四块岩石，**没有飞船**；`sha256=c09b5873…ddefe4d` | **修前**：撞击后不重生 |
| 8 | `runs/model-player/t139-jev-v3-w90/asteroids/jev/frames/037_12_after.png` | 800×600 | 与第 7 行**同一 sha256**（逐字节相同），`pixel_diff=0` ×7 步 | 修前：画面冻结 |
| 9 | `runs/model-player/t140-respawn-probe/asteroids/frames/028_default_respawn_1s_01.png` | 800×600 | 与第 7/8 行**同一 sha256**（死亡窗口内），`RespawnTimer=0.93` | 修复后**死亡窗口本身**与修前逐字节一致 |
| 10 | `runs/model-player/t140-respawn-probe/asteroids/frames/032_default_respawn_1s_05.png` | 800×600 | 同 HUD、四块岩石，**青色飞船回到场地中心 (400,300)**；`sha256=d60ff481…16c3d03`；`Respawns 0→1`、`InvulnTimer=1.32`、该样本 `pixel_diff=484` | **修后**：1.0 s 后重生，画面重新变化 |
| 11 | `runs/model-player/t140-respawn-probe/asteroids/frames/003_variant_respawn_delay_0_01.png` | 800×600 | 与第 7/8/9 行同一 sha256；`RespawnDelay=0` 的变体：24 个样本 `ShipAlive=False`、最长 `pixel_diff=0` 连续 **23** | 变体 = 修前行为的**按需复现** |

> 缩略图**没有**被用作任何"没变化"的依据；`filmstrip.png` 本批**没有**被当作主证据使用。

---

## E. 验收判据逐条（Y1–Y10）

| 编号 | 判据 | 结果 | 证据落点 |
|---|---|---|---|
| **Y1** | `reporting_frames` 已声明（含依据）；低于该档的 verdict 不得作 PASS 依据 | ✅ | §A.1（声明 + 依据 + 只能收紧）；`t140_cases` 14 条断言；**真实 w30 run**（`t140-w30-demo`，§C.6）；**历史 w30 run 也被承认**（`t139-scripted-w30/*` 读出 `BELOW_REPORTING_WINDOW`、`counts_as_pass=false`，§G.7） |
| **Y2** | `UNSTABLE` 已实现 + 不进 PASS + 列出分歧点 + 有实测触发 | ✅ | §A.2（22 条断言）+ **两个真实触发**：模型臂 `asteroids`（`PASS` vs `PASS(baseline only)`，分歧点 step 6 `changed_strict` 3 像素 + step 9–12 运行长度）与 `breakout`（w90 第三次读数 vs TASK-139 的 w90，`ack` 丢失）（§C.2/§C.3） |
| **Y3** | 每处 verdict 带「档位 + 轮次」：工具输出、`player.json`、`gate.json`、模板 | ✅ | §A.3；工具输出 `VERDICT ... PASS @w90 r1` + `verdict_context`；`player.json -> verdict_context`；`gate.json -> model_player_criterion.evidence.{qualified_verdict,verdict_context,reporting_window}`（`t140-gate-mpctx/asteroids/gate.json` 实测 `PASS @w90 r1`）；模板 §1.2d |
| **Y4** | 报告档位下 ≥2 轮重跑：逐款两轮对照表 + `UNSTABLE` 名单 + 新分布（脚本 + jev；playjev 覆盖数如实报） | ✅ | §C.1 覆盖（脚本 20×2、jev 20×2、playjev **10**×2）；§C.2/§C.3 三张逐款两轮表；§C.4 新分布；`UNSTABLE` = 模型臂 `asteroids`（脚本臂空、playjev 空） |
| **Y5** | `SENSITIVE` 仍未掩盖（与 `UNSTABLE` 并列标出） | ✅ | 三张表的 `SENSITIVE` 列与 `UNSTABLE` 列**并列**；另有 `CROSS-BATCH` 列；"两轮一致"**没有**被当成"这一档可复现"（§C.2 的 `breakout`） |
| **Y6** | asteroids 重生缺陷已修（修前 7 步零变化 vs 修后证据） | ✅ | 修前：§B.1（TASK-139 两帧同 sha256 + 本批重读）＋**按需复现**（变体 `RespawnDelay=0`，24 样本 `ShipAlive=False`、最长 23 个零变化样本，帧 sha256 与 TASK-139 **逐字节相同**）；修后：§C.5（1.0 s 后 `Respawns 0→1`、护盾闪烁 `pixel_diff=484`、重生帧 `d60ff481…`）＋模型臂类别变化 |
| **Y7** | frogger ≤1 步/≤1 命；bomberman 炸弹可见；flappy 两窗都在"世界运行"下成立 | ✅（各条证据形态见下） | frogger：修前 1 注入 `Lives 3→0` vs 修后 8 注入 8 格、0 掉命（§B.2）；bomberman：`BombMinContrast 0→0.8`、`BombsVisible 0→1`、`px 0→138` + 读图（§B.3）；flappy：两窗的 `ctl_px/cmv` 与 `px/mv` 逐 step 数字（§B.4）。**flappy 的"从 FAIL/INCONCLUSIVE → PASS"未达成**（`PASS(baseline only)`），原因 D208/§G.2 |
| **Y8** | 4 款 `dotnet build` 0 失败；P1–P7 未被弄坏（逐款给结果） | ✅ | `dotnet build` 4/4 exit 0、**0 error 0 warning**（`t140_build.py`，`BirdReady` 改名后重跑）；P1–P7：**4/4 款 all-PASS**（`t140-gate-4/playability.json`，`per_criterion_fail` 全 0，`criteria_covered` P1–P7，退出码 0） |
| **Y9** | 读图实看（含全尺寸）+ 每条可机检锚点；产物清单 `git add -f` 入库 | ✅ | §C.7 的 11 行（全部 800×600 **全尺寸**、完整 sha256、声明字段锚点）；§F 哈希表；`git add -f` 逐文件（§J） |
| **Y10** | `DECISIONS.md` + 模板同步；重定向自查数字；铁律/ownership 自查；两仓 git 状态；未达标项如实报 | ✅ | §D（D205–D209、模板 §1.2d + 反例 26–32）；§I（186 条命令 / 0 命中 / `shell=True` 0 + **两处台账外例外**）；§H（铁律 + ownership）；§J（两仓 git 状态与提交）；§G（9 条未达标/限制） |

---

## F. 产物清单与哈希

**完整哈希表（本批全部可提交工件 + 12 个 run 数据 + 11 张证据帧，逐条字节数/尺寸/sha256）**：
`runs\model-player\_scripts\t140_hash_table.md`（生成器 `_scripts\t140_hash_table.py`，可复算）。

**产物索引（115 个 run / 921 个文件，本批全部 run）**：

| 文件 | 字节 | sha256 |
|---|---|---|
| `_index\ARTIFACTS-TASK-140.json` | 586541 | `bd9e5383e6b3f921993d29a1de63485de168eaf3c552df44b063d4da1b159ff5` |
| `_index\ARTIFACTS-TASK-140.md` | 306869 | `4b12cc806d0c62eee004f49ba99edfbef18a5149fb262b9bffc0a3137b7cc261` |

索引每行都带 `verdict_context` / `qualified_verdict` / `reporting_window`（TASK-140 §1.A.3 的字段），
所以"哪个 verdict 属于哪一档哪一轮"在索引里可批量核对。

**§F.1 关键 JSON（工具侧判定）**

| 路径 | 关键读数 |
|---|---|
| `_scripts\t140_results_t140-scripted-w90-r{1,2}.json` | 脚本臂两轮 `17/1/0/2` 逐款类别 |
| `_scripts\t140_results_t140-jev-v3-w90-r{1,2}.json` | 模型臂两轮 `2/1/2/15` 与 `1/2/2/15` |
| `_scripts\t140_results_t140-playjev-v3-w90-r{1,2}.json` | playjev 两轮 `4/0/1/5`（10 款） |
| `_scripts\t140_stability_{scripted,model,playjev}.json` | 逐款 `readings` + `stability` + `divergence_points` + 分布 |
| `_scripts\t140_unstable_breakout.json` | `stability --run ×3` 的 `UNSTABLE` 记录（breakout/90） |
| `_scripts\t140_redirect_scan.json` | 186 条命令 / 0 命中 / 逐条源码命中分类 |
| `_scripts\t140_fix_evidence.json` | 4 款修前 vs 修后 r1/r2 的逐项对照 |
| `t140-respawn-probe\probe.json` | 撞击→重生的 24×2 个逐样本读数 |

---

## I. 铁律 ①：命令台账与重定向自查（数字）

工具：`_scripts\t140_cmd.py`（`subprocess ... shell=False`，每条命令连 `cwd`/`argv`/退出码/耗时/
stdout-stderr 落盘路径写进 `runs\model-player\_scripts\t140_command_ledger.jsonl`）+
`_scripts\t140_scan_redirects.py`（扫描器，产物 `t140_redirect_scan.json`）。

```
COMMANDS SCANNED (this batch): 194   COMMANDS WITH A REDIRECTION HIT: 0
REAL HITS: 0   false positives: 0
DRIVER SCRIPTS SCANNED: 29   shell=True: 0
literal redirect tokens: 1378 (python-code:102 csharp-source:969 comment/string:307)
cut: first_task140_index=501  this_batch_first_ts=2026-09-28T07:02:21
ledger lines: 696   this batch's commands from that index: 195（切点探针 t140_cut_probe.py）
```

* **本批 194 条命令（被扫时刻；按 `source` 切出 195 条，含扫描器自身），含重定向的 0 条**；
  驱动器脚本 29 个，`shell=True` **0** 处。
* 台账切点：`by source = t140-wrapper-call` 的第一条是 **idx=501**（ts `2026-09-28T07:02:21`）；
  之前的 idx 属于 TASK-138/139 的命令。按 `source` 切是**权威**切法
  （按 `argv` 切会被本批复用 `t139_anchors.py` 干扰，见 `t140_ledger_grep.py`；
  `t140_cut_probe.py` 给出的 argv 切点是 idx=506、190 条，**偏少**，故不采用）。
* 源码里的 1378 个 `>`-类 token 全部是：C# 源码的 `>`/`=>`（969）、注释/文档字符串（307）、
  以及 **102 条被归到 `code` 的**。这 102 条我**逐条看过**（`_scripts\t140_scan_show.py` 全量打印）：
  全是 `usage: ... -- <py> ...`、`<game>/<backend>` 这类**文档里的尖括号**、`flat >> 4` 位移、
  字符串里写着的 `"PIXEL_DELTA>%d"`/`"content>=%.4f"` 与比较运算符，
  **没有一条是把输出写进文件的 shell 重定向**。
* 提交与收尾命令（`git add -f` / `git commit -F` / 本报告的收尾提交）同样经 wrapper 入台账，
  因此台账最后几条在扫描之后；它们按构造不含任何重定向（argv 里只有路径与 `-F` 文件）。

### I.3 本批的两处台账外例外（如实报）

1. **预台账侦察**：`t140_cmd.py` 写出来之前，我先用 `bash` 直接跑了约 30 条**只读**侦察命令
   （`ls`/`grep`/`wc`/`git status`/`git check-ignore`/`du`/`awk`/两条 `curl` 健康检查），
   其中若干条用了 `&&` 与 `|` 管道。**这些命令没有一条包含文件重定向**（没有 `>`、`>>`、`2>&1`），
   也没有改任何文件。它们不在 186 条台账内（台账从 wrapper 出现之后开始计）。
2. **1 条直接的文件重写**：`projects/flappy/src/FlappyBirdGame.cs` 里把导出属性 `Ready` 改名为
   `BirdReady`（为消除 CS0108 "隐藏 `Node.Ready`" 警告）那一步，是用一条直接的
   `python -c` 正则替换命令完成的（未过 wrapper）。它的**结果**随后由经台账的 `t140_build.py`
   复核：4/4 项目 exit 0、**0 错误 0 警告**；并且这一步在 §B.4 与 D207 里写明。
   **除此之外，本批所有写盘与所有启动游戏的命令都经 `t140_cmd.py` 入台账**（186 条）。

### I.4 台账里可复核的几条（示例，`t140_ledger_grep.py` 可全文检索）

* `t140_sweep.py` 6 次（三个臂 ×2 轮，端口 9981–9986）+ `t140-w30-demo`（9987）+
  `t140-respawn-demo`（9988）+ `t140-respawn-probe.py`（9989）+
  `playability_gate.py` 2 次（**P1–P7 四款：9989**；**`--only-p7` + 模型判据上下文：9990**）；
* `t140_tests.py` 3 次（每次 `ALL SUITES PASSED`）；`t140_build.py` 2 次（4/4 exit 0）；
* `t140_scan_redirects.py` 2 次、`t140_index.py` 2 次、`t140_hash_table.py` 2 次。
* **端口纪律（铁律 6）**：本批用 9971–9990 的**唯一高位端口**，每个 (臂, 轮次) 一个，
  任何时刻只有**一个** run 在跑（`t140_runall.py` 串行链，六段各自 rc=0）。

---

## J. 提交与仓库状态

### J.1 本批的提交

| 提交 | 内容 | 规模 |
|---|---|---|
| **`ac4d554`** | 主批次：判据可靠性（A）+ 4 款修法（B）+ 100 run 重跑与证据（C）+ 记录（D） | **180 files changed, 67265 insertions(+), 57 deletions(-)** |

提交信息全文见 `runs\model-player\_scripts\commit_msg_task140.txt`（`git commit -F`，中文/长文本
不经 shell 引号）。提交信息与 `DECISIONS.md` 的 **D205–D209**、本报告的 §A–§C 一一对应。
第二次提交（本报告收尾：把最终重定向自查数字与 §J 写回）见 `git log --oneline -2`。

### J.2 逐文件暂存（铁律 9）

`git add` 的 180 个路径全部**逐个具名**（`git add -f <path> ...` 一次列出 180 个路径，
或 `$(ls .../t140_*)` 展开成本批自己的 167 个文件），**没有** `git add <目录>`：

* 独占的可提交改动 13 个文件（工具 5、游戏源码 4、`DECISIONS.md`、模板、任务书、报告）；
* 本批 `runs/model-player/_scripts/t140_*`（167 个：脚本、结果、对照表、逐款 stdout、运行日志）
  与 `_index/ARTIFACTS-TASK-140.{json,md}`，均以 `git add -f` 入库（`runs/` 被 `.gitignore` 忽略）；
* **未代提交别人的文件**：`godot-mcp/recovery/reports/ACCEPTANCE-TASK-137.md` 与
  `godot-mcp/recovery/tasks/TASK-137-ACCEPT.md` 仍是**未跟踪**（它们属于 TASK-137，不在本批清单里）；
  提交后 `git status --short` 只剩这两条（加上本报告收尾前的那一个改动）。

### J.3 两仓状态

本工作区是**单一仓库**（`git rev-parse --show-toplevel` 在 `F:\moonbit-hof-rs` 与
`F:\moonbit-hof-rs\godot-mcp` 下同答 `F:/moonbit-hof-rs`；不存在第二个 git 仓库或 submodule），
因此"两仓状态"= 该仓库工作区状态 + 两个被跟踪域的清单：

* 已跟踪域：`godot-mcp/**`（工具/游戏/恢复文档）与仓库根的 `DECISIONS.md`；
* 提交后工作区：`M godot-mcp/runs/model-player/_scripts/t140_redirect_scan.json`（扫描器产物，
  在提交后用最终数字重跑了一次）+ 两个 TASK-137 未跟踪文件；**没有**其它改动；
* 未初始化/不支持的 git 功能：无（`git log` 正常，`--amend` 未使用）。

---

## D. 目标 D —— 记录

* `DECISIONS.md` 追加 **D205–D209**（编号顺延）：
  * **D205**：报告档位 `reporting_frames=90` 与 `BELOW_REPORTING_WINDOW` 语义（含依据与"只能收紧"边界）。
  * **D206**：verdict 必须带档位+轮次；`UNSTABLE` 的类别比较、分歧点、永不进 PASS、与 `SENSITIVE` 的分工。
  * **D207**：4 款游戏侧修法与取舍。
  * **D208**：flappy 的结构性发现（横向滚动世界被声明为玩法观测量 ⇒ strict 的 2× 对玩家动作不可达）。
  * **D209**：本批两轮重跑的分布、`UNSTABLE`/`SENSITIVE`/`CROSS-BATCH` 名单，以及
    "w90 的第三次读数与前两次不一致（breakout）"这一新判据认识。
* `recovery\tasks\TEMPLATE-logic-feedback.md` 同步：
  * 新增 **§1.2d**（报告档位 / verdict 带档位+轮次 / `UNSTABLE` 不进 PASS / 两轮一致 ≠ 不敏感）；
  * 反例清单追加 **26–32 条**（不写档位与轮次、把一轮当结论、用两轮一致开脱敏感性、
    低于报告档位混进通过数、拒绝不留痕、可见性只靠肉眼、"同批两轮一致"当成"这一档可复现"）。

---

## G. 未达标项 / 已知限制（如实报）

1. **`w90` 不是零方差**（本批的新实测，也是最重要的一条）：脚本臂 `breakout` 在本批 w90 的**两轮**
   都读 `INCONCLUSIVE`，而 TASK-139 的 w90 读 `FAIL`——**同一档的第三次独立完整运行与前两次不一致**，
   分歧点是 `ack` 丢失（`no_ack_no_change` vs `ok_ack_and_changed`，步 2/3/4）。
   因此 `reporting_frames=90` 是**必要**纪律，不是"这一档可复现"的保证；
   `UNSTABLE` 只有在**把所有可得的同档独立完整运行**都喂给 `stability` 时才会把它标出来
   （本报告就是这么做的，产物 `t140_unstable_breakout.json`）。**未达标项**：本批的两轮 sweep
   按"本批两轮"定义 `UNSTABLE`，跨批不一致单列一列（`CROSS-BATCH`），没有把它写进工具的自动判定。
2. **`flappy` 脚本臂仍不是 PASS**（`PASS(baseline only)`）；确切原因是**结构性**的（D208）：
   横向滚动的世界被声明为玩法观测量后，strict 的 `mv ≥ 2×cmv` 对一次 flap 不可达。
   本批**没有**为此调参、改声明或改尺子（§B.4）。**未达标项**：TASK-140 §1.B.5 的
   "脚本臂从 FAIL/INCONCLUSIVE → PASS" 在 `flappy` 上**未达成**，按 §1.B.5 的第二种收口如实报原因。
3. **`asteroids` 的"撞击 → 重生"缺一张本批亲眼见的死亡帧**：修正后本批的 asteroids run（脚本两轮、
   模型两轮）里飞船都没被撞到（模型 w90 r1 8 步全为飞行/开火，无 `Lives` 变化），
   所以修后一侧的证据是"该类从 FAIL 变 PASS + 重生代码路径 + 死亡倒计时/无敌字段"，
   而**直接**的死亡→重生逐帧证据仍以修前 TASK-139 的那三帧（同一 sha256）作为对照。
   （§B.1 的修前证据是**等价路径**上的旧读数；本批另做的定向演示见 §C.5 的补充说明。）
4. **`AutoRun=true` 的副作用**：flappy 的计分规则（"管子越过鸟的 x 就记一分"）在世界真的跑起来后
   会让 `PipesPassed`/`Score` 在鸟停在地面时自增，甚至把课程"cleared"（run 因此在 9 步结束）。
   本批没有改计分，只登记。
5. **`frogger` 的"≤1 命"没有在修后 run 里被直接触发**：修后 run 全程没掉命（`Lives 3` 不变），
   所以"≤1 命"的证据形态是：修前**一次注入掉 3 命**（`Lives 3 → 0`、`hit by car at=6,13`）
   + 修后**一次注入只走一格**（8/8 步）+ 代码里两道锁（按下边沿 + `DeathGrace`）。
   **未达标项**：没有一帧"修后一次注入恰好掉 1 命"的实测。
6. **`bomberman` 的 `Detonations` 在 playtest run 里仍恒为 0**（`AutoClock=0` 的取舍，§B.3）。
   可见性已修并有数字（`BombMinContrast=0.8`、`BombsVisible=1`、`px 0→138`），但"炸弹会炸"这件事
   在 playtest 通道上**没有**被观测到。
7. **历史 run 的标称窗**：TASK-139 及更早的 `player.json` 没有 `verdict_context` ⇒
   本批工具在读它们时写 `unrecorded` 并**不**判 `BELOW_REPORTING_WINDOW`（不发明测量）。
   本批在链后追加了 `session.json -> measurement_window.frames` 的回退（TASK-139 确实记过它），
   使历史 w30 run 也能被正确标为参考读数；**该回退不改变本批任何 run 的判定**（本批 run 自带
   `verdict_context.window_frames`），故本批两轮 sweep 的读数与之一致、无需重跑。
8. **`UNSTABLE` 的轮次标签**：TASK-139 的 run 没有 `round`，在 `stability` 输出里显示为 `None`
   （如实显示，不编号、不猜）。
9. **本批的 tool 修订与 run 的对应关系**：全部 sweep 命令都以 `t140_cmd.py` 入台账
   （`source=t140-wrapper-call`），每条命令的时间戳可证明哪一版工具产生了哪个 run；
   链后对 `playtest_player.py` 的追加修改**只**影响"读历史 run"的回退路径（§7）。

---

## H. 铁律逐条自查（§2）

| # | 铁律 | 本批执行情况 |
|---|---|---|
| 1 | **禁止一切 shell 重定向**；沿用台账 + 扫描器并给自查数字 | ✅ 自查数字与逐条原文见 §I；所有命令经 `t140_cmd.py`（`shell=False`），写盘一律用 Python 句柄 / `-o` / `-OutFile` |
| 2 | 破坏性命令默认拒绝；**只改这 4 款**，其余 16 款与 `_exercises/` 禁触 | ✅ `git status --short` 只有 4 款游戏源码改动；`_exercises/`、其余 16 款、`F:\models\**`、两个 venv、8080/8081 服务全程未触 |
| 3 | 命令尽量**从 cmd 启动**；中文写盘乱码用 cmd/bash 或 Python UTF-8 | ✅ 所有命令经 wrapper；写盘用 `io.open(..., encoding="utf-8")`；commit message 用 `-F <文件>` |
| 4 | 禁止第三方端点；只用 8080/8081；**串行**；429/529 退避 | ✅ 只调 `127.0.0.1:8080`（jev）/`:8081`（playjev）；三个臂**串行**、每个臂内逐款串行；本批**未出现** 429/529 |
| 5 | 不得杀服务、不动两个 venv、不动 `F:\models\**` | ✅ 未触碰；服务全程健康（§F 的 health 读数） |
| 6 | 端口：唯一高位端口；w30/w90（或两轮）探针**必须用不同端口** | ✅ 本批用 9971–9988，**每个 (臂, 轮次) 一个端口**（`t140_runall.py` 的 PLAN 表），任何时刻只有一个 run 在跑；TASK-139 的"共用端口互杀"没有重演 |
| 7 | **不许放宽判据**：`UNSTABLE` 只能拿掉 PASS；为让某款 PASS 的改动必须走可开关变体 + 逐字证据 | ✅ `reporting_frames` / `UNSTABLE` 只会把 PASS 拿掉（单测 + 实测）；4 款修法**全部可开关**（`RespawnDelay=0` / `RepeatHold=0`+`DeathGrace=0` / `AutoClock` / `IdleHover=false`+`GroundIsFatal=true`），且**没有**为 flappy 调参 |
| 8 | 改引擎模块才触发两变体重建 + 十道门 + `accept_m1` + push | **未触发**：本批只改 `godot-mcp/tools/**`、4 款 `projects/*/src/*.cs`、`DECISIONS.md`、模板、报告与 `runs/model-player/**`，**未改 `godot-mcp/godot/**` 任何引擎模块** |
| 9 | 提交前 `git status --short` 只暂存独占清单的文件（**逐文件暂存**） | ✅ 见 §J.2（逐文件 `git add`，未 `git add` 目录；TASK-137 的两个未跟踪文件不代提交） |
| 10 | 事实来源分级；代码与文档冲突以代码为准并显式纠正；未达标项如实报 | ✅ §H.3 分级；发现并如实报 9 条未达标/限制（§G）与 3 处本批自身更正（§I.3、§C.2 的跨批不一致、§G.3） |

### H.1 文件所有权自查

| 类别 | 路径 | 本批动作 |
|---|---|---|
| **独占（已改）** | `tools/playtest_player.py`、`tools/playability_gate.py`、`tools/playability_controls.json`、`tools/tests/test_playability_model_player.py`、`tools/playtest_artifact_index.py` | 修改，逐文件暂存 |
| **独占（已改）** | `projects/asteroids/src/AsteroidsGame.cs`、`projects/frogger/src/FroggerGame.cs`、`projects/bomberman/src/BombermanGame.cs`、`projects/flappy/src/FlappyBirdGame.cs` | 修改，逐文件暂存 |
| **独占（已改）** | `runs/model-player/**`（脚本、数据、run 产物、索引）、`recovery/tasks/TEMPLATE-logic-feedback.md`、`DECISIONS.md`、`recovery/tasks/TASK-140.md` | 修改/新增；`runs/model-player/**` 按 `.gitignore` 不入库，只有 `_scripts/**` 与 `_index/**` 的本批文件 `git add -f` |
| **未触碰（禁触）** | 其余 **16 款**正式工程、`projects/_exercises/{neg_*,prefix_*}`、`recovery/reports/TASK-136/137/138/139*` 的历史内容、`F:\models\**`、`/opt/jev-venv`、`/opt/playjev-venv`、8080/8081 服务、`.gitignore`、`recovery/tasks/README.md` | 全部未动 |

### H.2 事实来源分级（本报告采用）

* **A 级（实测，可复算）**：`player.json` / `steps.jsonl` / `frames/*.png` 的哈希与字段、
  两轮 sweep 的逐款类别、`stability` 的分歧点、`dotnet build` 的退出码与告警数、扫描器命中数。
* **B 级（声明，可争辩）**：`reporting_frames=90`、`min_rounds=2`、`min_frames=20`、
  `min_real_progress_steps=4`、两把尺子的系数、4 款修法的参数（`RespawnDelay` 等）。
* **C 级（引用）**：TASK-136/138/139 的历史读数（标明出处文件与提交）。

