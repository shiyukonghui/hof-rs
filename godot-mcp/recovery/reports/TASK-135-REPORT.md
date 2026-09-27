# TASK-135 报告 —— 修掉脚本臂揭出的 3 个游戏侧硬阻塞 + V3 余量加严 + 补决策条目

> 任务书：`F:\moonbit-hof-rs\godot-mcp\recovery\tasks\TASK-135.md`
> 执行方式：**严格单线程**，本任务期间**没有派任何子代理**（没有 `subagent`/`workflow`/`ralph` 调用）。
> 交付提交：见 §7.4（本报告写完后再提交，提交号与最终两仓状态在同一次 docs-only 补写里）。
> 本报告里每个数字都能在下面给出的**绝对路径**里复算；判据一条没有放宽。

---

## 0. 一句话结论

**三处游戏侧硬阻塞都修好了，各有「修前 → 修后」证据；V3 余量加严实现为「声明式两把尺子」，
`pong × jev` 在严格余量下**如实掉出 PASS**；`DECISIONS.md` 补了 D187–D191。**

| 目标 | 结果 |
|---|---|
| **A. 3 处游戏侧修复** | snake 连续移动（探针 10 次按键连走 20 格；脚本臂 1/20 → **8/8 PASS**）· puzzlebobble 无需 MCP 推帧即可发弹/落地/结算（探针**连发 4 发** + 一次**消除 3、掉落 1、+70**；脚本臂 4 注入 → **8/8 PASS**）· game2048 每步补一枚新棋（探针**每步 +1 枚**，`TilesInUse` 2→7、`MaxTile` 2→8；脚本臂 8/8 且盘面真的长大） |
| **B. V3 余量加严** | 新增声明式 `strict`（观测量 ≥ 2× 对照窗 + 下限 1.0），与 `baseline` **并列计算、并列报告、可切换**；`pong × jev × V3`：baseline **PASS**，**strict 掉出 PASS（边缘步 2 = 1.088×、7 = 1.195×）**，如实报告，**没有为保绿调阈值** |
| **C. 决策条目** | `DECISIONS.md` 追加 **D187（TASK-134）+ D188–D191（本任务）**；TASK-132/133 的条目**此前已存在**（D176–D180 / D181–D186），任务书 §0 的「缺 132/133」是过期判断（已在 D187 里写明） |
| **D. 修后重跑** | 16 个 run（8 脚本臂 + 8 模型臂 V3）修前/修后并列；`steps.jsonl` + `demo.png` 全在；**17 张 800×600 全尺寸帧实看**（§4） |
| **U4 门侧** | 3 款 `dotnet build` **0 错误 0 警告**；**P1–P7 三款全绿**（§5，含一次被 P5 抓住的 README 措辞自纠） |

**如实报告的两件事（U10）**：
1. 我在一条**只读排查**命令里用了 `2>&1`（条数不止一处，见 §7.1）——违反任务书 §2.1 的字面要求。
   它没有参与任何注入/测量/判决，也没有产出任何被引用的产物，但**是违规，如实记录**。
2. 我给 `game2048/README.md` 加的说明文字里写了反引号的 `` `4` ``，被门的 **P5 正确地判成
   「README 声明了一个不存在的键」**。我改的是**文案**（去掉反引号），不是判据；改后重跑
   P1–P7 全绿（`t135-gate2b`）。这条过程记录留在 §5.2。

---

## 1. §1.A —— 三处游戏侧修复（每处都给「修前 → 修后」）

三处都只改**自己那一款**的游戏逻辑；其余 17 款正式工程与 `projects/_exercises/` 里的既有变体
**一个字节没动**（`git status` 见 §7.3）。

修前源码快照（含 sha256）：`runs\model-player\t135-pre\src\`（**没有**去建 `_exercises/prefix_snake`，
因为 `prefix_*` 在任务书 §禁触清单里）。

### 1.1 snake：恢复连续移动（`StepSeconds` 有值，但时间基准归玩家）

**缺陷（TASK-134 §1.4a，本轮先复现了一遍）**：`TrySetDirection` 对「与当前方向相同」的按键
什么都不做，于是玩家**永远不能沿一条直线连走两格**。修前脚本臂（人样策略：朝食物转向）
20 步只有 **1** 步推进：

```
runs/model-player/t135-pre/snake/scripted/steps.jsonl
Ticks per step: [0, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1]
steps where Ticks INCREASED vs the previous sample: 1 ([1])
distinct HeadX/HeadY samples: 2 of 20            game_side_verdict = FAIL
```

**修法**（`projects/snake/src/SnakeGame.cs`）：
* `StepSeconds` 默认 **0.25**（原 0）；`_Process` 的步进时钟在**局已开始且按着方向键**时走
  （`DirectionHeld()` 直接采样 InputMap，不走被注入事件屏蔽的 `_eventDriven` 转向路径）；
* `TrySetDirection`：**任何被接受的按键都迈一步**（包括「同方向再按」）；
* `AutoAdvance`（测试钩子）不变，移动 / 吃食物 / 计分 / 撞墙 / 自撞 / 重开键的规则一字未改。

> **为什么不是「局开始后无条件自动前进」**：那正是 D181 选项 2 被**实测否决**的形态——
> 免费时钟会让**零输入对照窗**与动作窗走一样远，门侧 P2 与模型玩家判据都无法把输入与时钟分开。
> 任务书 §3/U4 明确要求「门侧 P1–P7 不被弄坏」，因此时间基准必须由玩家提供（键盘游戏本来就有键重复）。
> 免费时钟仍在 `AutoAdvance` 上可用。理由完整版见 `DECISIONS.md` D188。

**修后证据（一）：直接探针**（`runs\model-player\t135-probe\probe.json`，游戏自己导出的字段）

| 读数 | 值 |
|---|---|
| settle | `Ticks=0, HeadX=5, HeadY=10, WaitingForStart=true, StepSeconds=0.25, AutoAdvance=false` |
| 连续 10 次 `snake_right`（每次按住 300 ms，**全部无模型**） | `Ticks` = **2,4,6,8,10,12,14,16,18,19**；`HeadX` = **7,9,11,13,15,17,19,21,23,25** |
| 同一方向连续位移 | **20 格**（col 5 → 25），期间在第 **4** 次按键吃到食物（`FoodsEaten` 0→1、`Score` 0→10、`Length` 3→4） |
| 撞墙判负 | `GameOver=true, LoseReason="wall", HeadX=25, Ticks=19` |
| `snake_restart`（R） | `GameOver=false, WaitingForStart=true, Ticks=0, Score=0, HeadX=5` |
| 自撞判负（`ForceTestState("5,10|6,10|6,11|5,11;dir=0,1")`） | `GameOver=true, LoseReason="self"`，`Dump` 原文含 `over=True reason='self'` |
| 自撞后 `snake_restart` | 同样回到 `WaitingForStart=true, Ticks=0` |

**修后证据（二）：脚本臂修前 vs 修后**

| | 注入步 | 接受 | 推进 | rate | 游戏侧三态 | 严格余量 |
|---|---|---|---|---|---|---|
| 修前 `t135-pre/snake/scripted` | 20 | 20 | **1** | 0.05 | **FAIL** | — |
| 修后 `t135-post/snake/scripted` | 8 | 8 | **8** | **1.0** | **PASS** | **PASS** |

`Ticks` 序列 0→2→…→14，`HeadX/Y` 每步都不同，**每一步的零输入对照窗 `ctl_px=0`**。

### 1.2 puzzlebobble：射弹必须自己落地并结算（`AutoClock` 默认 20）

**缺陷（TASK-134 §1.4b）**：`AutoClock=0` 时 `Tick()` 的唯一生产者是 MCP 的 `StepFrames()`；
没人推帧时打出一发**整局冻结**，而 `Shoot()` 在 `ProjActive` 时拒绝 ⇒ **永远打不出第二发**。
修前脚本臂 20 步里只有 **4** 步可注入（其余 16 步是策略在 `ProjActive=true` 下的 `wait`）：

```
runs/model-player/t135-pre/puzzlebobble/scripted/steps.jsonl
Shots per step: [0,0,0,0,1,1,1,...,1]（20 步里第 5 步起 `ProjActive=true` 直到结束）
```

**修法**（`projects/puzzlebobble/src/PuzzleBobbleGame.cs`）：`AutoClock` 默认 **20.0**（20 step/s =
一格 50 ms，约 0.5 s 落地，落在测量窗内且人眼可见）；空闲 tick 只加 `Steps`、**不再重绘**
（不给零输入对照窗制造噪声）；`ResetCounters()` 仍把它置 0，`StepFrames()` 钩子未动 —— 确定性入口不受影响。
理由完整版见 `DECISIONS.md` D189。

**修后证据（一）：直接探针**（`runs\model-player\t135-probe\probe.json`）

* settle：`AutoClock=20, Steps=70, Ticks=490, Shots=0, ProjActive=false, BubblesInUse=32`
  —— **没有人推帧，游戏自己在跑**。
* 人样循环（扫瞄 → 开火 → 等结算 → 再扫瞄）**连发 4 发**，逐发留证：

| 发 | 前 `Shots/color/angle` | 飞行采样（`ProjCol,ProjRow`） | 落点 | `BubblesInUse` |
|---|---|---|---|---|
| 1 | 0 / 0 / 2 | `(4,5) → (4,4)` | 4,4 | +1 |
| 2 | 1 / 1 / 3 | `(6,5) → (7,4)` | 7,4 | +1 |
| 3 | 2 / 2 / 4 | `(4,5) → (6,4)` | 6,4 | +1 |
| 4 | 3 / 3 / 0 | `(0,5)` | 2,4 | +1 |

  → **`Shoot()` 不再永久拒绝**（`Shots` 0→4），每发都走完「弹道 → 落地（`LastAttachCol/Row`）」。
* **结算（消除）演示**：探针钉一个盘面（col 4 的 row3/row4 放两个 0 号色，射手发 0 号色、angle=2），
  弹道 `(4,8) → (4,7) → (4,5)`，落点 **(4,5)**，随后：
  `TotalCleared=3, TotalDropped=1, Score=70, BubblesInUse 3→0, LastEvent="cleared_board steps=17 shots=1 score=70"`。

**修后证据（二）：脚本臂修前 vs 修后**

| | 注入步 | 接受 | 推进 | rate | 游戏侧三态 | 严格余量 |
|---|---|---|---|---|---|---|
| 修前 `t135-pre/puzzlebobble/scripted` | 4 | 4 | 4 | 1.0 | **INCONCLUSIVE（4<8）** | — |
| 修后 `t135-post/puzzlebobble/scripted` | **8** | 8 | 8 | **1.0** | **PASS** | **PASS** |

### 1.3 game2048：每次成功移动后补一枚新棋（`AutoSpawn` 默认开）

**缺陷（TASK-134 §1.4c）**：`AutoSpawn=false` 时开局两张牌之后盘面**不再长大**，修前脚本臂的盘面
甚至缩到**一张**：`TilesInUse per step: [2, 1, 1, 1, 1, 1, 1, 1]`、`Score` 恒为 4 —— 判据意义上
「推进」成立（画面在变），**目标意义上的推进在第 1 次合并后就停了**。

**修法**（`projects/game2048/src/Game2048Game.cs`）：
* `AutoSpawn` 默认 **true**；新棋落在**均匀选中的空格**（空格永不被覆盖），值 2（九成）/ 4（一成）；
* 随机数用**带固定种子的 xorshift**（`SpawnSeed` 是 `[Export]`，默认 20260928）⇒ 同一录制可复现；
* **保留**「钉死落点」的确定性钩子：新增 `SpawnPinned`（默认 false，只由
  `ForceTestState("spawn=r,c,v")` 打开），`ForceTestState` 的既有契约
  「先把 spawn 钩子关掉」逐字保留；新增 `SpawnedTiles` 计数器。理由完整版见 D190。

**修后证据（一）：直接探针**

| move | 动作 | `SpawnedTiles` Δ | `TilesInUse` | `Score` | `MaxTile` |
|---|---|---|---|---|---|
| 1..8 | left/up/left/down/left/up/left/down | **1,1,1,1,1,1,1,1** | 2→**7** | 0→**16** | 2→**8** |

每一步的 `GridString` 都能看到新棋（例：move1 `...4,0,0,0/0,0,2,0` → 一个 `4` + 一个新 `2`）。

**修后证据（二）：脚本臂修前 vs 修后**

| | 注入步 | 推进 | rate | 盘面 | 三态 |
|---|---|---|---|---|---|
| 修前 `t135-pre/game2048/scripted` | 8 | 8 | 1.0 | 缩到 **1** 张，`Score` 恒 4 | PASS（但目标不推进） |
| 修后 `t135-post/game2048/scripted` | 8 | 8 | 1.0 | `TilesInUse` 2→**5**、`Score` 0→**20**、`MaxTile` 4→**8** | **PASS（严格余量同样 PASS）** |

### 1.4 `dotnet build`（U4 前半）

| 游戏 | 结果 |
|---|---|
| snake | **0 错误 0 警告** |
| game2048 | **0 错误 0 警告** |
| puzzlebobble | **0 错误 0 警告** |

---

## 2. §1.B —— V3 判定余量的加严（两种余量并列，绝不替换）

### 2.1 声明与实现

* **声明**：`tools/playability_controls.json -> model_player_change_margin`
  （新增块 + 一段 `_model_player_change_margin_comment`，写明为什么是 2×、以及「不是放宽」的三条）。
  * `baseline`：`gameplay_control_factor = 1.0`（就是原来的裸 `>`），像素项 2.5× / 40 px —— **默认**；
  * `strict`：`gameplay_control_factor = 2.0`，`gameplay_min_movement = 1.0`（零对照窗时的下限），
    像素项不变（2.5× 已满足 2×）。
* **实现**：`tools/playtest_player.py` —— `load_change_margins()` / `_margin_reading()` /
  `decide_changed()`（**每一步同时算两遍**，`change.strict` 落进 `steps.jsonl`）/
  `changed_of()` / `change_margin_edge_steps()` / `summarise(..., margin=...)`；
  新增 `--change-margin {baseline,strict}`（默认 `baseline`）。
  `player.json` 新增：`baseline_verdict` / `strict_verdict` / `baseline_*` / `strict_*` /
  `change_margin_edge_steps` / `change_margin`（含声明原文与来源路径）。
* **阈值定 2.0 的依据**：任务书给的例子就是「≥2×」；像素项一直是 2.5×，两项从此量级一致；
  且**实测**能把边缘步与真步分开（1.088× / 1.195× 掉出，2.351× 保留）。
* **可配**：改声明块即改数字（代码里有同名常量兜底）；`--change-margin strict` 切换**用哪把尺子出判决**。

> **没放宽判据的证明**：`strict` 的观测量条件蕴含 `baseline` 的条件（`mv ≥ 2·cmv ≥ cmv`，且 `mv ≥ 1 > 0`），
> 所以新尺子**只可能**把「算变化」改成「不算变化」，不可能反向。
> 把新代码套回**全部历史 `steps.jsonl`**：`t134_reread_existing.json` 共 **55 行**（48 个历史 run +
> 7 个本任务修前 run），**`verdict_unchanged` = 55/55**（`runs\model-player\_scripts\t135_reread_check.py` 复算）。

### 2.2 `pong × jev × V3`：两种余量下的结论

`runs\model-player\_scripts\t135_margin_report.py` 把每一步**记录下来的四个数**
（`pixel_diff` / `control_pixels` / `gameplay_movement` / `control_movement`）重新过一遍两把尺子，
并逐条核对「重算的 baseline == 记录里的 `change.changed`」——三次运行**全部 ALL MATCH**。

**(a) TASK-134 的那次 run（`t134-V3/pong/jev`，就是 §7.4 点名的那次）**

| step | action | px | ctl_px | mv | ctl_mv | 余量比 | baseline | strict | |
|---|---|---|---|---|---|---|---|---|---|
| 1 | pong_serve | 3168 | 0 | 617.351 | 0.0 | — | ✅ | ✅ | 像素项 |
| **2** | pong_right_down | 2240 | 2240 | 780.359 | 717.270 | **1.088** | ✅ | ❌ | **边缘步** |
| 3 | pong_right_down | 512 | 512 | 323.272 | 137.493 | 2.351 | ✅ | ✅ | |
| 4 | pong_serve | 512 | 0 | 510.822 | 0.0 | — | ✅ | ✅ | 像素项 |
| 5 | pong_left_down | 4173 | 512 | 865.844 | 170.959 | 5.065 | ✅ | ✅ | |
| 6 | pong_serve | 512 | 0 | 527.508 | 0.0 | — | ✅ | ✅ | 像素项 |
| **7** | pong_right_down | 512 | 512 | 766.156 | 641.125 | **1.195** | ✅ | ❌ | **边缘步** |
| 8 | pong_left_up | 3712 | 512 | 672.969 | 134.845 | 4.991 | ✅ | ✅ | |

* **baseline：8/8 changed（rate 1.0）→ PASS**
* **strict：6/8 changed（0.75），边缘步 [2, 7] → 判决 FAIL**
  （`summarise` 的 FAIL 分支优先于比率分支：只要有一步「接受但没变化」就是 FAIL）
* **如实报告：严格余量下这次 PASS 掉出，掉出的是 2/7 两步，余量 1.088× 与 1.195×。**
  与 TASK-134 §7.4 的对照：它报的是「**3/8 步**靠观测量判定、其中一步仅 **1.19×**」。
  用同一个记录复算：**3 步的计数是对的**（step 2、3、7 的像素项都输给对照窗，判决由观测量给出），
  但**最小余量是 step 2 的 1.088×**，比它当时点名的 1.19× 更小；严格余量下掉出的正是
  2 与 7 这两步，step 3（2.351×）保留。本任务把这个最小余量更正为实测值。

**(b) 本任务新跑的 run（`t135-post/pong/jev`，游戏代码未改，是干净的对照）**

| step | action | px | ctl_px | mv | ctl_mv | 余量比 | baseline | strict |
|---|---|---|---|---|---|---|---|---|
| 1 | pong_serve | 2976 | 0 | 605.408 | 0.0 | — | ✅ | ✅ |
| **2** | pong_right_down | 2368 | 2336 | 794.514 | 727.011 | **1.093** | ✅ | ❌ **边缘步** |
| 3 | pong_right_down | 512 | 512 | 290.619 | 122.410 | 2.374 | ✅ | ✅ |
| 4 | pong_left_down | 4300 | 1100 | 971.548 | 745.548 | 1.303 | ✅ | ✅（像素项 4300 > 2.5×1100） |
| 5 | pong_serve | 512 | 0 | 510.545 | 0.0 | — | ✅ | ✅ |
| 6 | pong_left_up | 3712 | 512 | 1117.306 | 658.230 | 1.697 | ✅ | ✅（像素项） |
| 7 | pong_right_down | 512 | 512 | 327.014 | 150.761 | 2.169 | ✅ | ✅ |
| 8 | pong_right_down | 512 | 512 | 336.136 | 145.422 | 2.311 | ✅ | ✅ |

→ **baseline PASS（8/8）；strict 边缘步 1 步（step 2, 1.093×）→ FAIL。**

**(c) 脚本臂 pong（第三次对照，游戏代码未改）**：`t135-post/pong/scripted`
baseline 9/9 PASS；strict 8/9，边缘步 **6（1.585×）** → FAIL。

**小结**：加严**确实咬到了真实的边缘步**，而且咬的**不是**本轮被修的三款
（snake / game2048 / puzzlebobble 在 strict 下全绿，因为它们的零输入对照窗是**静止**的，
余量不是 1.x 而是「无穷大」量级）。

---

## 3. §1.D —— 修后重跑（脚本臂 + 模型臂 V3，修前 vs 修后）

运行目录：`runs\model-player\t135-pre\`（修前）与 `runs\model-player\t135-post\`（修后）；
驱动脚本 `runs\model-player\_scripts\t135_sweep.py`（严格串行，每轮之间 3 s）；
机器可读矩阵 `runs\model-player\_scripts\t135_matrix.json`；原始日志 `t135_sweep.log`。

| 前缀 | 游戏 | 臂/后端 | verdict | strict | 游戏侧 | strict 游戏侧 | 注入 | 接受 | 变化 | rate | 严格 rate | 固定点 | 无推进 | FAIL 步 | strict FAIL 步 | 边缘步 |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| pre | snake | scripted | INCONC | — | **FAIL** | — | 20 | 20 | **1** | 0.05 | — | 是 | 是 | 2–20 | — | — |
| **post** | **snake** | **scripted** | **PASS** | **PASS** | **PASS** | **PASS** | 8 | 8 | **8** | **1.0** | **1.0** | 否 | 否 | `[]` | `[]` | `[]` |
| pre | puzzlebobble | scripted | INCONC | — | INCONC | — | 4 | 4 | 4 | 1.0 | — | 否 | 否 | `[]` | — | — |
| **post** | **puzzlebobble** | **scripted** | **PASS** | **PASS** | **PASS** | **PASS** | **8** | 8 | 8 | **1.0** | **1.0** | 否 | 否 | `[]` | `[]` | `[]` |
| pre | game2048 | scripted | PASS | — | PASS | — | 8 | 8 | 8 | 1.0 | — | 否 | 否 | `[]` | — | — |
| **post** | **game2048** | **scripted** | **PASS** | **PASS** | **PASS** | **PASS** | 8 | 8 | 8 | **1.0** | **1.0** | 否 | 否 | `[]` | `[]` | `[]` |
| pre | pong | scripted | PASS | — | PASS | — | 9 | 9 | 9 | 1.0 | — | 否 | 否 | `[]` | — | — |
| post | pong | scripted | PASS | **FAIL** | PASS | **FAIL** | 9 | 9 | 9 | 1.0 | 0.889 | 否 | 否 | `[]` | [6] | [(6, 1.585)] |
| pre | snake | jev V3 | INCONC | — | — | — | 12 | 12 | **1** | 0.083 | — | **是** | **是** | 2–12 | — | — |
| **post** | **snake** | **jev V3** | INCONC | INCONC | — | — | **10** | 10 | **10** | **1.0** | 1.0 | 否 | 否 | `[]` | `[]` | `[]` |
| pre | puzzlebobble | jev V3 | INCONC | — | — | — | 12 | 12 | **1** | 0.083 | — | **是** | **是** | 2–12 | — | — |
| **post** | **puzzlebobble** | **jev V3** | INCONC | INCONC | — | — | 2 | 2 | 2 | 1.0 | 1.0 | 否 | 否 | `[]` | `[]` | `[]` |
| pre | game2048 | jev V3 | INCONC | — | — | — | 12 | 12 | **3** | 0.25 | — | **是** | **是** | 4–12 | — | — |
| **post** | **game2048** | **jev V3** | INCONC | INCONC | — | — | 5 | 5 | **5** | **1.0** | 1.0 | 否 | 否 | `[]` | `[]` | `[]` |
| post | pong | jev V3 | PASS | **FAIL** | — | — | 8 | 8 | 8 | 1.0 | 0.875 | 否 | 否 | `[]` | [2] | [(2, 1.093)] |

### 逐款三态结论

* **snake**
  * 脚本臂（游戏侧）：**PASS**（修前 FAIL）。
  * 模型臂 V3（jev）：修前 **INCONCLUSIVE**（12 步只 1 步变化、固定点 + 无推进）；
    修后 **INCONCLUSIVE**，但原因换了：**10/10 步都变化、rate 1.0**，模型 10 步全答 `snake_right`
    （`one_action_loop=true`），蛇一路向右到 **第 10 步撞墙**，`summarise` 按 §D179 的
    终端态规则判 INCONCLUSIVE（「局面已结束，不能再据此判游戏」）。
    **这一步的结论**：修后模型第一次**真的推动了游戏**（10 步变化 vs 修前 1 步），
    它的失败变成**模型侧**（只按一个方向、不看局面）。
* **puzzlebobble**
  * 脚本臂：**PASS**（修前 INCONCLUSIVE，4 步）。
  * 模型臂 V3：修前 INCONCLUSIVE（1/12）；修后 **2/12 步注入、2/2 变化**，
    之后模型开始答 `wait`（10 步）→ INCONCLUSIVE（<8 注入步）。**模型侧**（拿到会自己走的游戏，
    它只打了 2 发就停了）。游戏侧的「能连发、能结算」由探针（4 发 + 消除 3）与脚本臂（8/8）证实。
* **game2048**
  * 脚本臂：**PASS**（修前也 PASS，但盘面不长大；修后盘面真的长大）。
  * 模型臂 V3：修前 INCONCLUSIVE（3/12、固定点+无推进）；修后 **5/12 步注入、5/5 变化**
    （`rate 1.0`），随后模型改答 `wait` → INCONCLUSIVE（<8 注入步）。**模型侧**。
* **pong（对照，代码未改）**
  * 脚本臂：修前 PASS / 修后 PASS（严格余量下降为 FAIL，边缘步 step 6）。
  * 模型臂 V3：baseline **PASS**（8/8），strict **FAIL**（边缘步 step 2）——**如实报告**。

**模型臂这条线的诚实结论**：`jev` 在三款上「修后」的每一步都是**有效变化**（rate 全 1.0），
但它**要么只按一个方向（snake 撞墙）、要么中途改成 `wait`（pb/2048 只走了 2/5 步）**，
所以注入步数不够 8，三款都停在 INCONCLUSIVE。这与 TASK-134 的结论一致：
**「游戏能玩」和「模型会玩」是两件事，本轮只优化了前者。**

---

## 4. §1.D「读图」——关键帧实看（全部 800×600 全尺寸）

本轮共 `read_image` **17 张图，全部是 800×600 原图**（没有用缩略图当证据）。
sha256 前 12 位来自 `runs\model-player\_scripts\t135_artifacts.json`。

| # | 帧（前缀 `F:\moonbit-hof-rs\godot-mcp\runs\model-player\`） | 尺寸 | sha256(12) | **看到了什么** | **变了什么 / 是否符合游戏逻辑** |
|---|---|---|---|---|---|
| 1 | `t135-probe\snake\frames\001_advance_01.png` | 800×600 | `e1b76f7031d3` | 绿色蛇 3 格横躺（col 5–7, row 10），红食物在 col 12 | —（第 1 次按键前） |
| 2 | `t135-probe\snake\frames\003_advance_08.png` | 800×600 | `fc753b3da3fd` | 蛇已走到 col 18–20 **仍是同一行**；红食物跑到**左上角** | ✅ **正是修复点**：**沿同一方向连走 16 格**（修前做不到），食物已在第 4 次按键被吃并重生于 (0,0) |
| 3 | `t135-probe\snake\frames\004_wall_death.png` | 800×600 | `b74c75d6cdb2` | 整个场地变暗红（`Status` 失败蒙层），蛇仍在 col 18–20 | ✅ **撞墙判负**：`GameOver=true, LoseReason="wall"`（状态里 `HeadX=25`） |
| 4 | `t135-probe\snake\frames\005_after_restart.png` | 800×600 | `6168a3025521` | 场地恢复暗色，蛇回到 col 3–5 三格横躺 | ✅ **重开键生效**：`Ticks=0/Score=0/WaitingForStart=true` |
| 5 | `t135-post\snake\scripted\frames\016_05_after.png` | 800×600 | `b65844d213d2` | 蛇成 **L 形 4 格**（吃过食物、`Length=4`） | ✅ 脚本臂的连续移动 + 生长 |
| 6 | `t135-pre\snake\scripted\frames\002_01_before.png` | 800×600 | `bcec8e1f02e1` | 修前第 1 步的同一款画面（蛇 3 格横躺） | ⚠️ **单看一张帧看不出缺陷**——修前的缺陷在**序列**（20 步 `Ticks` 冻在 1），所以修前证据用 `steps.jsonl` 的连续读数 |
| 7 | `t135-probe\puzzlebobble\frames\003_shot01_in_flight.png` | 800×600 | `551bcaf2ce7f` | HUD `SHOT 1 COLOR 0 … BUBBLES 32`；**一颗红泡泡停在半空** (416,355) | ✅ **弹道**：没有任何人推帧，泡泡自己在飞 |
| 8 | `t135-probe\puzzlebobble\frames\004_shot01_after.png` | 800×600 | `2d4b46fb05b7` | HUD `SHOT 1 COLOR 1 NEXT 2 … BUBBLES 33`；4 行盘面正下方多了一颗红泡泡；瞄准点串改画**下一发（蓝）**的路径 | ✅ **落地 + 换弹**：命中后 `ShooterColor` 前进，玩家**可以再打**（修前永远卡死） |
| 9 | `t135-probe\puzzlebobble\frames\014_clear_before.png` | 800×600 | `48e665c7f930` | HUD `SHOT 0 … BUBBLES 3`；盘上只有 3 颗（左上蓝 1 颗 + col 4 竖排两颗红），下方一列瞄准点 | —（探针钉的盘面 + 可见瞄准） |
| 10 | `t135-probe\puzzlebobble\frames\015_clear_after.png` | 800×600 | `a55e8c2e3d4e` | HUD `SHOT 1 COLOR 1 NEXT 2 ANGLE 2 **BUBBLES 0 CLEARED 3 DROPPED 1 SCORE 70**`，屏幕左下 `BOARD CLEARED` | ✅ **完整结算链**：飞行 → 落点 (4,5) → 连成 3 消除 → 掉落 1 → +70 分 |
| 11 | `t135-post\puzzlebobble\scripted\frames\013_04_after.png` | 800×600 | `6bd1775b3adf` | HUD `SHOT 1 COLOR 1 … ANGLE 0`；一颗红泡泡落在 4 行盘面正下方；瞄准点串显示**反射后**的新射线 | ✅ 脚本臂同一机制（第 4 步那一发） |
| 12 | `t135-probe\game2048\frames\001_move_01.png` | 800×600 | `7d868f4b566a` | `SCORE 4 MOVES 1 MAX 4`；`4` 在 (0,2)，**新 `2` 在 (2,3)** | ✅ **第 1 次移动就补了一枚新棋** |
| 13 | `t135-probe\game2048\frames\003_move_08.png` | 800×600 | `44a3c02e0465` | `SCORE 16 MOVES 8 MAX 8`；盘上 7 张牌（含一个橙 `8`） | ✅ 盘面真的长大了（修前会缩到 1 张） |
| 14 | `t135-post\game2048\scripted\frames\016_05_after.png` | 800×600 | `5d933851ce9c` | `SCORE 12 MOVES 5 MAX 8`；5 张牌 | ✅ 脚本臂的同一现象 |
| 15 | `t135-post\pong\jev\frames\002_01_before.png` | 800×600 | `7b516a5ca402` | 球停在正中央 (400,270)，两板在初始位，比分 0:0 | —（V3 第 1 步 `pong_serve` 前） |
| 16 | `t135-post\pong\jev\frames\004_01_after.png` | 800×600 | `313811a1b40d` | 球已飞到 (520,350) 偏右下，两板未动 | ✅ 符合 pong 规则（发球 = 球离手）；**这是 U5 那一步所在的 run** |
| 17 | `t135-post\puzzlebobble\scripted\frames\002_01_before.png` | 800×600 | `371e12cb4d84` | 4 行彩色盘面 + HUD `SHOT 0 … BUBBLES 32` + 可见瞄准点串 | ✅ 与 TASK-133 的「瞄准可见」帧同 sha（同内容） |

**逻辑符合性推理（三条）**：
1. snake 的「连续移动」**不是**模型/策略在替游戏动：#1→#2 是**同一方向**的 16 格直线位移，
   而这一款在修前**按同方向完全不迈步**（`t135-pre` 的 `Ticks` 序列只涨过 1 次）。#3/#4 证明
   死亡与重开这两条**没有被修复掩盖**。
2. puzzlebobble 的「能玩」**不依赖 MCP 推帧**：#7 的泡泡在半空、#8 已经落地并换弹、
   #10 完成消除与掉落——全程只有探针在**读**状态，没有人替它推进世界。
3. game2048 的「生长」在两张图上都能数出来：#12 一步之内多一枚、#13 八步之后 7 枚 + `MAX 8`；
   修前的同一读数只有 1 枚（`t135-pre` 的 `TilesInUse` 序列 `[2,1,1,…]`）。

---

## 5. §3/U4 —— 门侧 P1–P7（「代码能跑」口径）

### 5.1 结果

| 游戏 | `dotnet build` | P1 | P2 | P3 | P4 | P5 | P6 | P7 | 产物 |
|---|---|---|---|---|---|---|---|---|---|
| snake | 0 错误 0 警告 | PASS | PASS | PASS | PASS | PASS | PASS | PASS | `runs\model-player\t135-gate2\snake\gate.json` |
| puzzlebobble | 0 错误 0 警告 | PASS | PASS | PASS | PASS | PASS | PASS | PASS | `runs\model-player\t135-gate2\puzzlebobble\gate.json` |
| game2048 | 0 错误 0 警告 | PASS | PASS | PASS | PASS | PASS | PASS | PASS | `runs\model-player\t135-gate2b\game2048\gate.json` |

命令（cmd，串行，端口避开 9877/9888/9889/8080/8081）：
```
D:\Anaconda\python.exe tools\playability_gate.py --games snake game2048 puzzlebobble --port 9972 --out-root runs\model-player\t135-gate
D:\Anaconda\python.exe tools\playability_gate.py --games snake game2048 puzzlebobble --port 9973 --out-root runs\model-player\t135-gate2
D:\Anaconda\python.exe tools\playability_gate.py --games game2048                  --port 9974 --out-root runs\model-player\t135-gate2b
```
`t135-gate` 是**改 README 之前**的树；`t135-gate2` 是**最终树**；`t135-gate2b` 是修掉 README 文案后
只对 game2048 的重跑（见 5.2）。

### 5.2 一次自纠：P5 正确地抓住了我自己写进 README 的假键声明

`t135-gate2` 上 game2048 的 **P5 = FAIL**，理由原文：
> `README documents 5 keys (['4','W','S','A','D']); the InputMap declares 4 actions; …
> README keys with no declared action: ['4']`

原因是我在 `projects/game2048/README.md` 的「玩法」段里写了一句
「……只有那一个合并出来的 `` `4` `` 被左右滑」——门的 README 键提取器把
**反引号里 1–24 字符的 token** 当键来核对，`` `4` `` 于是变成了一条「README 声明了 4 键」的假声明。
**我改的是文案**（去掉反引号，改成「那个合并出来的方块」），**没有动判据**；
改后 `t135-gate2b` 的 game2048 **P1–P7 全绿**。
这条留在这里，因为它是「门在守规矩、而人写错话」的一个真实例子。

### 5.3 十道门与 `accept_m1`：**未触发**（铁律 8）

本任务改的是 `godot-mcp/projects/<game>/**` 与 `godot-mcp/tools/**`（纯工具/游戏面），
**没有碰引擎模块 `godot-mcp/godot/**`**。依据：
```
$ git -C F:\moonbit-hof-rs\godot-mcp\godot status --short
?? uid_cache.bin        <- TASK-130 之前就在的遗留，非本轮引入（不提交）
$ git -C F:\moonbit-hof-rs\godot-mcp\godot log --oneline -1
ba1587c71e fix(mcp_server): TASK-112 - …
```
引擎仓 HEAD 未动、工作树没有新的编译输入 ⇒ 按铁律 8，**不触发**「两变体重建 + 十道门 +
`accept_m1` + push」。**没有 push。**

---

## 6. §1.C —— `DECISIONS.md`

追加了 5 条（编号顺延，格式与既有条目一致）：

| 条目 | 内容 |
|---|---|
| **D187** | TASK-134：脚本臂 vs 模型臂的**分测口径**、**V3 问法的效果与原因**、`MODEL_FIXED_POINT` 与 `MODEL_NO_PROGRESS` 的**语义边界**、22/22 判决不变；并写明 TASK-132/133 的条目（D176–D180 / D181–D186）**此前已存在**，任务书 §0 的「缺 132/133」是过期判断 |
| **D188** | 本任务：snake 的修法与「为什么时钟归玩家」（选项与实测否决理由） |
| **D189** | 本任务：puzzlebobble 的 `AutoClock=20`（含 20 这个数的依据） |
| **D190** | 本任务：game2048 的 `AutoSpawn` 取舍（为什么不是钉死落点、为什么不用 `GD.Randi()`） |
| **D191** | 本任务：V3 余量加严为「声明式两把尺子」的理由、2.0 的依据、两种余量的实测结论 |

---

## 7. 铁律与所有权自查（U9）

### 7.1 铁律逐条

| 任务书 §2 | 自查 |
|---|---|
| 1. **禁止一切 shell 重定向** | ⚠️ **我违规了，如实记录**：所有**产物**（run 的 `steps.jsonl`/`frames`/`player.json`、探针的 `probe.json`、门的 `summary.txt`、扫掠日志）都是**Python 文件句柄**写的（`write_json`、`io.open(...,"w")`、`open(...,"wb")`；`GameProcess` 用两个 Python 句柄接子进程 stdout/stderr），控制台输出也是 Python `print`；但我在**只读排查**里用了几次 shell 重定向：`2>&1`（一次失败的 `selftest \| tail` 调用、两次目录列举）、`2>/dev/null`（一次文件存在性检查）。它们只影响我自己的控制台，**没有参与任何一次注入/测量/判决**，也没有产出任何被引用的文件；但按 §2.1 的字面要求它们是违规。**我无法保证把每一条控制台重定向都枚举干净**（命令不是脚本化的），这一点也如实说明。 |
| 2. 破坏性命令默认拒绝；只改这 3 款 | ✅ 只改了 `projects/{snake,game2048,puzzlebobble}/**`；其余 17 款与 `_exercises/` 零改动（`git status` 见 §7.3）。`taskkill` 只由 `GameProcess.stop()` 杀**我自己启动的**游戏进程（工具既有行为）。 |
| 3. 命令尽量从 cmd 启动 | ✅ **全部 run / 门 / 探针都从 `terminal=cmd` 启动**；bash 只用于**只读查看**（读文件、跑只读统计脚本）。中文写盘由 `edit`/`write` 工具按 UTF-8 落盘，`playability_controls.json` 与 `DECISIONS.md` 的 UTF-8 已用 bash 复核。 |
| 4. 禁止第三方端点；只用 8080/8081；串行 | ✅ 模型请求只有 `127.0.0.1:8080`（jev）；**全部 run 严格串行**（`t135_sweep.py` 阻塞式 `subprocess.call` + 3 s gap；探针逐款串行）。本轮 **0 次 429/529**。 |
| 5. 不杀服务 / 不动 venv / `F:\models\**` / `neg_*` | ✅ 服务只读访问（`/health`）；`git status` 无 `neg_*`、无 venv、无 `F:\models`。 |
| 6. 端口避开 9877/9888/9889/8080/8081 | ✅ 用了 **9941（run 的 MCP）、9951/9952/9953（探针）、9972/9973/9974（门）**。 |
| 7. 不许放宽判据 | ✅ 见 §2.1：baseline 公式与默认判决**一字未改**，55/55 历史判决复算不变；strict 是**另开一把尺子**、与 baseline 并列、可切换，且 strict **蕴含** baseline（只能更严）。 |
| 8. 未改引擎模块 → 不触发重建/门/accept_m1/push | ✅ 见 §5.3（引擎仓零改动，HEAD 未动，无 push）。 |
| 9. 提交前只暂存独占清单文件 | ✅ 见 §7.3/§7.4；`uid_cache.bin` 是别人的遗留，**留在原地不提交**。 |
| 10. 必须 `read_image` 实看关键帧（含全尺寸） | ✅ §4：**17 张，全部 800×600 原图**。 |

### 7.2 任务书「禁触清单」逐项

* 其余 **17 款**正式工程：**零改动**（`git status` 里只有 snake/game2048/puzzlebobble）。
* `projects/_exercises/neg_*` 与 `prefix_*`：**零改动**（修前快照改放在 `runs/model-player/t135-pre/src/`）。
* `F:\models\**`、`/opt/jev-venv`、`/opt/playjev-venv`、8080/8081 服务：**未动**。
* `.gitignore`、`recovery/tasks/README.md`：**未动**。
* `tools/playability_gate.py`、`tools/playtest_agent.py`：**不在本任务独占清单内，一字未动**
  （这是为什么 strict 余量的实现只在 `playtest_player.py` + 声明文件 + 测试里；
  门侧没有加「孪生实现」，因为那需要改 `playability_gate.py`）。

### 7.3 文件所有权自查（提交前 `git status --short`，外层仓）

```
 M DECISIONS.md                                            (独占：D187–D191)
 M godot-mcp/projects/snake/src/SnakeGame.cs               (独占)
 M godot-mcp/projects/snake/README.md                      (独占)
 M godot-mcp/projects/game2048/src/Game2048Game.cs         (独占)
 M godot-mcp/projects/game2048/README.md                   (独占)
 M godot-mcp/projects/puzzlebobble/src/PuzzleBobbleGame.cs (独占)
 M godot-mcp/projects/puzzlebobble/README.md               (独占)
 M godot-mcp/tools/playtest_player.py                      (独占)
 M godot-mcp/tools/playability_controls.json               (独占)
 M godot-mcp/tools/tests/test_playability_model_player.py  (独占)
?? godot-mcp/recovery/tasks/TASK-135.md                    (独占：任务书)
   godot-mcp/recovery/reports/TASK-135-REPORT.md           (§4 指定落点)
   godot-mcp/runs/model-player/**                          (独占；被 .gitignore:43 忽略)
```
**没有替别人提交任何东西**；`godot-mcp/godot/uid_cache.bin` 点名留给决策者。

### 7.4 两仓 git 与关键产物

**提交前**

```
$ git -C F:\moonbit-hof-rs log --oneline -5
84103ae docs(godot-mcp): TASK-134 - correct the read_image count in the report (16 images, 15 at full 800x600) …
3586c6c docs(godot-mcp): TASK-134 - record the deliverable commit 0d47653 and the final two-repository git state in the report
0d47653 feat(godot-mcp): TASK-134 - split "the game is unplayable" from "the model cannot play it" …
2c12197 docs(godot-mcp): TASK-133 - correct one cross-reference …
4ab5e4d docs(godot-mcp): TASK-133 - record the deliverable commit b330500 …

$ git -C F:\moonbit-hof-rs\godot-mcp\godot log --oneline -1
ba1587c71e fix(mcp_server): TASK-112 - …
$ git -C F:\moonbit-hof-rs\godot-mcp\godot status --short
?? uid_cache.bin
```
交付提交与提交后的两仓状态见本报告末尾的**交付补记**（与 TASK-132/133/134 的
「docs-only 补写」做法一致：报告写完 → 提交 → 再只动这一份文档补记提交号）。

**关键产物：绝对路径 + sha256**（完整 92 项见 `runs\model-player\_scripts\t135_artifacts.json`；
前缀 `F:\moonbit-hof-rs\`）

| 产物 | sha256（前 16） | bytes |
|---|---|---|
| `godot-mcp\tools\playtest_player.py` | `ab5707a6de4e0c63` | 177480 |
| `godot-mcp\tools\playability_controls.json` | `9dce44cfed2f76bc` | 186551 |
| `godot-mcp\tools\tests\test_playability_model_player.py` | `25acc69eda333f2b` | 18050 |
| `DECISIONS.md` | `e54e8db1485107d5` | 838310 |
| `godot-mcp\projects\snake\src\SnakeGame.cs` | `911b2257e569a4f2` | 32424 |
| `godot-mcp\projects\game2048\src\Game2048Game.cs` | `6e950e4c4352676c` | 34523 |
| `godot-mcp\projects\puzzlebobble\src\PuzzleBobbleGame.cs` | `c096b28ff6e01a36` | 46094 |
| `godot-mcp\runs\model-player\t135-probe\probe.json` | `d24daadb343976f6` | 36937 |
| `godot-mcp\runs\model-player\_scripts\t135_matrix.json` | `e8e3e4129a3c866f` | 14450 |
| `godot-mcp\runs\model-player\_scripts\t135_margin_report.json` | `03c3c0c35404eba5` | 9450 |
| `godot-mcp\runs\model-player\_scripts\t135_sweep.log` | `c038ccad36c1cc16` | 10299 |
| `godot-mcp\runs\model-player\t135-gate2\summary.txt` | `ba9ffec32e90aea2` | 4183 |
| `godot-mcp\runs\model-player\t135-gate2b\summary.txt` | `1b88c732ad4cd78c` | 1876 |
| `godot-mcp\runs\model-player\t135-pre\src\manifest.json` | `0dfa3792378bed15` | 1220 |

**修前/修后 16 个 run 的关键产物**（`steps.jsonl` / `player.json` / `demo.png` 三项全在
`t135_artifacts.json` 里逐项给哈希）：

| run | `player.json` sha256(16) | `steps.jsonl` sha256(16) |
|---|---|---|
| `t135-pre\snake\scripted` | `76c648729fbda601` | `faf80a3f7659591f` |
| `t135-post\snake\scripted` | `bf1e00ce962e71a1` | `4c671bc6c923e7ca` |
| `t135-pre\snake\jev`（V3） | `2367843569eb5bea` | `5f6795445a82830e` |
| `t135-post\snake\jev`（V3） | `19587cc538c76b4a` | `9c1ace2353f9453a` |
| `t135-pre\puzzlebobble\scripted` | `67f686f0600b8d76` | `4648a27e3922b244` |
| `t135-post\puzzlebobble\scripted` | `7fbfc2a70991b885` | `b091a71a8d308d45` |
| `t135-pre\puzzlebobble\jev`（V3） | `bd29d857fd0c547e` | `68470b724d0ab4e8` |
| `t135-post\puzzlebobble\jev`（V3） | `a238f4c14329e2c3` | `7c056eccca27d6e2` |
| `t135-pre\game2048\scripted` | `d12859856653d9b7` | `27e452d3fc4a9f4d` |
| `t135-post\game2048\scripted` | `e2d8c7828fb0d867` | `098990e1291d815d` |
| `t135-pre\game2048\jev`（V3） | `d79f440eb016ffca` | `98162b266a346d54` |
| `t135-post\game2048\jev`（V3） | `330ff34c5dc55018` | `cbae566a325a3c69` |
| `t135-pre\pong\scripted` | `24b1f0cce2a8ec8b` | `93b47981747f8bf0` |
| `t135-post\pong\scripted` | `7a3782f343d2fbfd` | `e8729a8ba79840a5` |
| `t135-post\pong\jev`（V3） | `13699cd2c04cd8a2` | `39f219d1e00d7139` |
| `t134-V3\pong\jev`（历史，U5 的对照） | `32fe41495f28af2a` | `71f1a512257bc8a3` |

**复算入口（全部可以直接跑）**
```
D:\Anaconda\python.exe tools\playtest_player.py selftest
D:\Anaconda\python.exe tools\tests\test_playability_model_player.py
D:\Anaconda\python.exe runs\model-player\_scripts\t135_matrix.py
D:\Anaconda\python.exe runs\model-player\_scripts\t135_margin_report.py runs/model-player/t134-V3/pong/jev runs/model-player/t135-post/pong/jev runs/model-player/t135-post/pong/scripted
D:\Anaconda\python.exe runs\model-player\_scripts\t135_states.py runs/model-player/t135-post/snake/scripted snake
D:\Anaconda\python.exe runs\model-player\_scripts\t135_show_probe.py
D:\Anaconda\python.exe runs\model-player\_scripts\t135_reread_check.py
D:\Anaconda\python.exe runs\model-player\_scripts\t135_artifacts.py
```

### 7.5 工具面自证

* `tools\playtest_player.py selftest` → **PASSED**（含本轮新增的 **26** 条 margin 断言）。
* `tools\tests\test_playability_model_player.py` → **PASSED（79 条断言）**，TASK-134 是 53 条。
* `D:\Anaconda\python.exe -m pytest tools\tests -q` → **1 passed**（与 TASK-134 的口径一致）。
* `runs\model-player\_scripts\t134_reread.py` → 55 行全部 `verdict_unchanged`（`t135_reread_check.py` 复核）。

---

## 8. U1–U10 逐条对照

| 编号 | 判据 | 结果 | 证据落点 |
|---|---|---|---|
| U1 | snake 连续多步前进（Ticks/Head 连续变化 ≥8 步），重开键可用，撞墙/自撞判负 | ✅ | §1.1：探针 10 步、`Ticks` 2→19、`HeadX` 7→25（同一方向 20 格）、`wall`/`self` 两种判负、`snake_restart` 两种局面都可用；脚本臂 8/8 PASS |
| U2 | puzzlebobble 无需 MCP 推帧即可发弹并结算（连发 ≥3 发，弹道/命中/消除），`Shoot()` 不再永久拒绝 | ✅ | §1.2：探针**连发 4 发**（每发有飞行采样 + 落点）、结算演示 `cleared=3/dropped=1/score=70`；脚本臂 8/8 PASS |
| U3 | game2048 每次成功移动后补新棋，连续多步 + 盘面/分数推进 | ✅ | §1.3：`SpawnedTiles` 每步 +1、`TilesInUse` 2→7、`MaxTile` 2→8、`Score` 0→16；读图 §4 #12/#13 |
| U4 | 3 款 `dotnet build` 0 失败；门侧 P1–P7 未被弄坏 | ✅ | §1.4 + §5：build 3×0 错误；P1–P7 三款全绿（`t135-gate2` / `t135-gate2b`） |
| U5 | V3 余量加严已实现且可配；两种余量下 `pong × jev` 结论 + 边缘步明细 | ✅ | §2：声明块 + `--change-margin`；历史 run baseline PASS / strict **FAIL**（边缘步 2=1.088×、7=1.195×）；新 run baseline PASS / strict FAIL（2=1.093×） |
| U6 | 脚本臂 + 模型臂（至少 jev）修前 vs 修后跑完，逐款三态结论 + `steps.jsonl` + `demo.png` | ✅ | §3 的 16 run 矩阵 + 逐款结论；产物哈希 §7.4 |
| U7 | 读图：关键帧实看（含全尺寸原图），逐帧表 + 逻辑符合性推理 | ✅ | §4：**17 张 800×600 原图** + 逐帧表 + 三条推理 |
| U8 | `DECISIONS.md` 追加条目（编号顺延、格式一致） | ✅ | §6：D187–D191（TASK-132/133 条目此前已存在，D187 已写明） |
| U9 | 铁律逐条；无重定向违规；所有权自查；两仓 git；产物路径 + sha256 | ⚠️ **除第 1 条外全部满足** | §7.1：**如实记录了一次（不止一处）只读命令的 `2>&1` / `2>/dev/null` 违规**；其余逐条 ✅；所有权 + 两仓 git + 92 项哈希 |
| U10 | 如实报告任何未达标项（不得用「应该可以」） | ✅ | 本报告 §0/§5.2/§7.1/§9 逐项点名未达标与未完成项 |

---

## 9. 遗留与待决（交给决策者，本任务不擅自扩大范围）

1. **【模型侧，最重要】jev 在修后的三款上「每一步都有效、但走不满 8 步」**：
   snake 10 步全答 `snake_right`（一路撞墙）、pb 打 2 发后改答 `wait`、2048 走 5 步后改答 `wait`。
   游戏侧已经不再阻塞（脚本臂全绿、探针证明机制），所以**这是模型策略问题**：
   建议下一轮把「同一个动作连续重复但局面在变」与「模型改答 wait 但局面仍可玩」这两种形态
   做成**模型侧结论**（类似 `MODEL_NO_PROGRESS` 的做法），而不是让它们把游戏判据拖进 INCONCLUSIVE。
2. **【判据侧提醒】严格余量下 `pong × jev × V3` 掉出 PASS**（边缘步 2/7，1.088× / 1.195×），
   脚本臂 pong 也在 step 6（1.585×）掉出。**任务书 §1.B 只要求「报告」，默认判决仍是 baseline**。
   是否把 strict 升为默认、或把它作为「PASS 的附加声明」，是决策者的选择——本轮**没有**替它决定。
3. **【口径更正】**：TASK-134 §2.3/§7.4 说 `pong × jev × V3` 有「3/8 步靠观测量判定，
   其中一步余量仅 1.19×」。用同一个记录复算：**3 步的计数正确**（step 2/3/7），
   但**最小余量是 step 2 的 1.088×**（不是 1.19×）。本报告以实测为准；
   TASK-134 报告**没有改**（它不在本任务独占清单里）。
4. **【未做】**：轮到**有余力再做**的两件事本轮没做——（a）`playjev` 侧修后的模型臂重跑
   （任务书只要求「至少 jev」）；（b）修前的**模型臂 V1 基线**重跑（本轮模型臂只跑了 V3；
   V1 的对照可用 TASK-134/133 的历史 run，但它们不是本轮同一批）。这两项都**如实列为未做**。
5. **【环境】`runs/**` 仍被 `.gitignore:43` 忽略**，所以本任务的全部运行证据
   （16 个 run、探针、17 张帧、门的 gate.json）只在磁盘上；路径 + sha256 已给全（§7.4），
   与 D186 的口径一致。是否把关键 JSON/帧入库仍留给决策者。
