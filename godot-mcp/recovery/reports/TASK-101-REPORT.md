# TASK-101 — 第 12、13 个游戏（Sokoban / Bomberman）交付；四条缺陷（载荷 1 / 会话 3）在各自首轮被「断言 + 多帧采样 + Python 第二实现」照出来、修好并重跑（Sokoban r1→r2、Bomberman r1→r4）；模块字节未动，门跑器判 `SKIP_REBUILD`（如实说明：十道门一门未跑）

* 执行者：工具工程师（本会话，**有写权限，不再委派**）
* 主仓：`F:\moonbit-hof-rs`（分支 `master`，无远端，本轮提交 `26553df`）
* 引擎仓：`F:\moonbit-hof-rs\godot-mcp\godot`（分支 `feature/mcp-server-module-rebuild`，`HEAD = origin = e041cae270`，**本轮一个字节未动**）
* 脚本 / 会话 / 证据：`godot-mcp\recovery\work\task101\`
* 时间：2026-09-27（本会话）

---

## 0. 结论表（每行一句话）

| 段 | 要求 | 结论 | 关键证据 |
|---|---|---|---|
| **A①** | **Sokoban**（C#，只用 MCP 调用开发）：网格推箱、箱子与目标计数、死锁判定（简单）、关卡完成与撤销 | **做完，首轮照出 1 条会话缺陷（K-1）、修好并重跑 r2 后全绿。** 190 次调用（编辑器 14 / 游戏 176），`facts_complete` **190/190（100%）**，判定分布 `failed=2`（**两条都是声明的**：`e06` 同名批量 `-32000`、`g170` 不存在属性 `-32001`）+ `ok_effect_observed=25` + `ok_file_effect_observed=133` + `ok_no_effect_observed=30`；断言 **124 PASS + 1 条声明的边界失败** ＋ **2 条屏幕文本 PASS** ＋ **1 条场景断言 PASS** = **127 PASS**；像素差 **29/190 非零**（编辑器 1/14、游戏 28/176），`user://` 六帧逐对 **0 / 61371 / 95473 / 90574 / 9796 px**（`t0`→`t1` 的 0 px 是**撤销把盘面逐字节还原**，不是缺陷），六个 sha 里 5 个互不相同；独立复算 **0 处不符**；`project_build_csharp` exit 0（3692 ms）、`invalid_count=0`、`errors count=0`；树里 75/76 个节点名 **0 个 `@` 开头** | `runs\sokoban\soko-task101-r2`（首轮 `-r1`）、`logs\summary-soko-r2.txt`、`logs\assert-soko-r2.txt`、`logs\samples-soko-r2.txt`、`logs\pixel-soko.txt`、`logs\frames-soko-r2.txt`、`logs\recompute-soko-r2.txt`、`logs\editor-soko-r2.txt` |
| **A②** | **Bomberman**（C#，只用 MCP 调用开发）：网格移动、放炸弹与爆炸扩散、破坏砖块、敌人、胜负与生命 | **做完，首轮照出 3 条缺陷（B-1 载荷、B-2 / B-3 会话）、逐条修好并重跑到 r4 后全绿。** 233 次调用（编辑器 14 / 游戏 219），`facts_complete` **233/233（100%）**，判定分布 `failed=2`（同样两条声明的）+ `ok_effect_observed=43` + `ok_file_effect_observed=153` + `ok_no_effect_observed=35`；断言 **143 PASS + 1 条声明的边界失败** ＋ **2 条屏幕文本 PASS** ＋ **2 条场景断言 PASS** = **147 PASS**；像素差 **45/233 非零**（编辑器 1/14、游戏 44/219），六帧逐对 **7541 / 176025 / 168478 / 74786 / 114995 px**，六个 sha **6/6 互不相同**；独立复算 **0 处不符**；`project_build_csharp` exit 0、`invalid_count=0`；树里 127/128 个节点名 **0 个 `@` 开头** | `runs\bomberman\bomb-task101-r4`（首轮 `-r1`，中间 `r2`/`r3`）、`logs\summary-bomb-r4.txt`、`logs\assert-bomb-r4.txt`、`logs\samples-bomb-r4.txt`、`logs\pixel-bomb-r4.txt`、`logs\frames-bomb-r4.txt`、`logs\recompute-bomb-r4.txt`、`logs\editor-bomb-r4.txt` |
| **A③** | 跑完给：调用数、判定分布、`facts_complete`、缺陷清单（分「工具缺陷」「游戏或驱动缺陷」）；两行加进 `GAME-LOOP-LOG.md` | **做完。** 台账续到第 12、13 行；**工具缺陷 0 条**；**游戏或驱动缺陷 4 条**（**K-1** 会话取值时机、**B-1** 载荷接触规则、**B-2** 会话断言无探测、**B-3** 会话/测试设计钉板已分出胜负）；`GAME-LOOP-LOG.md` 新增「TASK-101 记录」节与四条缺陷行 | `GAME-LOOP-LOG.md` 台账第 12/13 行、缺陷表 K-1 / B-1 / B-2 / B-3、TASK-101 记录节；`recovery\work\task101\decisions-d149.md`；`DECISIONS.md` 的 D149 |
| **B** | 若改了模块 → 重建两变体 + 十道门全绿（真实退出码）+ `accept_m1` 22/22 + push 到 fork；未改模块则用 `run_gates.ps1` 的纯文档/免跑判定并**如实说明**；主仓提交；报告含两仓 `git log --oneline -8` 与 `git status --short`；时间不够如实报告 | **未改模块，如实免跑。** `modules\mcp_server` 本轮**零字节改动**（引擎仓 `git status --short` 空、`git diff 2385fe2fb..HEAD` 仍只有两份 `.md`），预检判 `VERDICT=ANCHOR_STRUCTURAL_EQUIVALENT` + `RESULT=SKIP_REBUILD` + `GATES_SKIPPED=1`，**exit 0**，非编译清单两份 `.md`——**十道门本轮一门未跑，未重建、未 push 代码**。主仓提交 `26553df`（173 个文件，26899 行增 1 行删） | `runs\gates\task101-doconly\summary.txt`、`logs\gates-task101-doconly.txt`；§B、§F |

---

## A. 第 12、13 个游戏（C#，只用 MCP 调用开发）

### A1 形态与开发方式（两款同一套脚手架，固化的模板照用）

两款都从模板实例化（`tools\new_game.ps1 -Name sokoban -Class SokobanGame` / `-Name bomberman -Class BombermanGame`），**游戏内容全部由 MCP 调用写成**：`project_edit_script`（C# 载荷替换模板桩）、`editor_add_nodes_batch`（3 个静态节点一次建好）、`editor_add_input_action`、`editor_save_scene`、`project_build_csharp`、`project_validate_scripts`、`editor_get_errors`；游戏相全部是 `running_game_*`。

| 游戏 | 场景里的静态节点 | 运行期新建的东西 |
|---|---|---|
| Sokoban | `Background` / `Hud` / `Status` | 每格 1 个 `Cell_r_c` + 1 个 `Mark_r_c` + 1 个移动的 `PlayerSprite` |
| Bomberman | `Background` / `Hud` / `Status` | 每格 1 个 `Cell_r_c` + 每个敌人 1 个 `Enemy_i` + 3 个 `Bomb_i` + 1 个 `PlayerSprite` |

**确定性规则（继承前十一款）**：①静态节点一次批量建好；②动态对象运行期新建；③`ForceTestState` 一个调用钉死整盘状态；④**多帧采样先于会改变状态的那一步**；⑤每个「钩子做了多少」都是**与帧率无关的增量属性**（`LastHookSteps`），每帧时钟另一个属性（`LastAutoSteps`）——**一个属性只能有一个写者**；⑥建场景那一步**故意再跑一次同名批量**，让 D-3 的拒绝出现在每一轮证据里；⑦任何时钟都用**浮点累加器**（`_autoAccum += delta * rate`，不用 `(int)(delta * rate)`），`Elapsed` 是每帧 `+= delta` 的浮点秒表。

**「全新」的含义**：每次重跑之前，都先把上一轮工程按「**先写 sha256 清单再移动**」归档，再用模板重新实例化，使新一轮与上一轮从同一个起点出发：

| 归档 | 文件数 | 字节数 |
|---|---|---|
| `archive\sokoban-r1`（清单 `sokoban-r1.manifest.json`） | 129 | 8 429 528 |
| `archive\bomberman-r1`（清单 `bomberman-r1.manifest.json`） | 129 | 8 473 434 |
| `archive\bomberman-r2`（清单 `bomberman-r2.manifest.json`） | 129 | 8 473 646 |
| `archive\bomberman-r3`（清单 `bomberman-r3.manifest.json`） | 129 | 8 473 644 |

**全程零删除**：只移动，不删除。

### A2 终轮真实输出

| | Sokoban r1 | Sokoban **r2** | Bomb r1 | Bomb r2 | Bomb r3 | Bomb **r4** |
|---|---|---|---|---|---|---|
| 调用数（编辑器 / 游戏） | 190（14 / 176） | **190（14 / 176）** | 224（14 / 210） | 226（14 / 212） | 231（14 / 217） | **233（14 / 219）** |
| `facts_complete` | 190/190 | **190/190（100%）** | 224/224 | 226/226 | 231/231 | **233/233（100%）** |
| 断言（node-state） | 122 PASS + 2 FAIL + 1 声明 ERROR | **124 PASS + 1 声明 ERROR** | 132 PASS + 3 FAIL + 1 声明 ERROR | 136 PASS + 1 声明 ERROR | 141 PASS + 1 声明 ERROR | **143 PASS + 1 声明 ERROR** |
| 断言（另两个工具） | — | **2 屏幕文本 + 1 场景 = 3 PASS** | — | — | — | **2 屏幕文本 + 2 场景 = 4 PASS** |
| 像素差非零 | 29/190（1/14、28/176） | **29/190（1/14、28/176）** | 45/224（1/14、44/210） | 44/226 | 45/231 | **45/233（1/14、44/219）** |
| 判定分布 | `failed=2` + 25 + 138 + 25 | **`failed=2` + 25 + 133 + 30** | `failed=2` + 42 + 151 + 29 | `failed=2` + 42 + 147 + 35 | `failed=2` + 43 + 152 + 34 | **`failed=2` + 43 + 153 + 35** |
| 缺陷（工具 / 游戏或驱动） | 0 / 1 | **0 / 0（r1 那条已修）** | 0 / 3 | 0 / 1（B-3 仍在） | 0 / 1（B-3 仍在） | **0 / 0（三条都已修）** |

> 每一轮都是 `failed=2`，且**两条都是声明的**：编辑器相那一次同名拒绝（`-32000`）+ 一条故意打在不存在属性上的边界断言（`-32001`）。`report.json` 的自动缺陷清单只有这两条。

### A3 证据形态（任务书要求的四类都用上了）

**① 多帧属性采样（先采样、后改变）**

| 采样 | 帧数 | 结果 |
|---|---|---|
| Sokoban `g34-samples-frozen` | 12 | 冻结基线：`BoardHash` / `BoxesOnGoal` / `Steps` **各只有 1 个值**，`Elapsed` / `Ticks` **各 12 个不同值** |
| Sokoban `g155-samples-autopush` | 30 | `Steps` **30 个不同值（15→59）**、`AutoSteps` 30 个、`PlayerRow` / `PlayerCol` 各 2 个、`LastAutoSteps` 2 个、`Elapsed` / `Ticks` 各 30 个 |
| Bomb `g37-samples-frozen` | 12 | 冻结基线：`GridHash` / `BricksRemaining` / `PlayerRow` **各只有 1 个值**，`Elapsed` / `Ticks` **各 12 个不同值** |
| Bomb `g178-samples-clock` | 30 | **`BombList` 17 个不同值（`4,4,16`→`''`）**；**第 16 帧同时**：`BombsActive` 1→0、`Detonations` 0→1、`BricksRemaining` 3→1、`GridHash` 变、`LastBlastCount` 0→7；`AutoTicks` 29 个、`LastAutoSteps` 2 个、`Elapsed` / `Ticks` 各 30 个 |

**② 断言** —— **Sokoban**：四个关卡各自的 `BoardHash` / `BoxList` / `GoalList` / 玩家坐标与 Python 第二实现一致；一次左推上目标 → `Won`/`GameOver`，赢后再动被拒（`reason=game_over`），`Undo` 把 `Steps` 1→0、`Pushes` 1→0、`BoxList` 回到 `2,3`、**`BoardHash` 逐位回到起点**，空栈撤销被拒（`reason=nothing_to_undo`）；走廊关 5 步 3 推通关（`BoxList=1,3|3,1`），撤销一步后哈希等于复算的撤销值、再推一次**逐位回到同一个通关哈希**；把箱子推进角落 → `Deadlocked=true` / `DeadlockList=2,1` / `GameOver=true` / `Won=false`；把箱子推向墙 → `reason=blocked_box` 且 `BoardHash` 一字不变；非法方向 → `reason=bad_dir`；`AutoStep(2)`→`LastHookSteps=2`、`AutoStep(3)`→3，时钟跑过 30 帧后仍是 3 而 `LastAutoSteps` 归 0；`ForceTestState` 把 `LastHookSteps` 归零（显式断言）。屏幕文本 `LEVEL CLEARED` / `STUCK - DEADLOCK`。**Bomberman**：撞墙 / 撞砖 / 走上活炸弹三种走法全被拒（`reason=wall` / `brick` / `bomb`）且 `Moves` 不动；同格放第二颗炸弹被拒（`reason=bomb_already_here`）；引信 `3→2→1→引爆`（`BombList=3,1,1` 时 `Detonations=0`；再一步 → `LastBlast=3,1|2,1|1,1|4,1|5,1|3,2`、1 块砖被炸、`Score=10`）；走廊钉板证明**硬墙停、第一块砖吃下并停住**（`LastBlast=1,3|2,3|1,2|1,1|1,4`，3 块砖 2 块被炸、第 3 块仍立着）；玩家被自己炸到 → `Exploded=true` / `Lives` 3→2 / 重生回出生格；**连锁**（1 引信 + 3 引信两颗炸弹）→ `StepFuse(1)` 后两颗都没了、`Detonations=1`、`LastBlast` 是两次爆炸的并集 8 格；**确定性追击**（`StepEnemies(3)`→`4,1|7,8`、`StepEnemies(1)`→`3,1|7,7`，玩家一步没动）；走进敌人 → `DeadByEnemy=true` / `Exploded=false` / `Lives` 3→2 / 重生 / **敌人仍在**；最后一条命被抓 → `GameOver=true` / `Won=false` / 再动被拒；**一次爆炸通关**（北面炸掉最后一块砖 + 南面炸死最后一个敌人 → `Won=true` / `Score=110` / `Lives=3` / `Exploded=false`）；`StepTick(2)`→`LastHookSteps=2` / `BombList=4,4,22`，时钟跑过 30 帧后仍是 2 而 `LastAutoSteps` 归 0。屏幕文本 `FIELD CLEARED` / `GAME OVER`。

**③ 文件 sha** —— 两款各自 `e05` / `e09` 的 `project_read_text_file` sha **逐字节相同**（Sokoban `d5c22b0d3f88c6a505e18508988f3dc288ff461f5d8bba4c139971c00b04fbbe` / 831 B；Bomberman `05672aed6e7c6e3e22aeb500a58de8b85dcaa19486733ccf059f26e8dd75cb1c` / 844 B），即被拒的同名批量**什么都没写**；`e06` 的 `-32000` 各列 3 条 `conflicts`（Background / Hud / Status）；编辑器相各 `sidecar_verified=1`（C# 载荷超限走旁路证据）。

**④ 像素差 + 独立复算** —— 见 A4。

### A4 独立复算（不是转述）

三层，互相独立：

1. **会话里的字面量来自 Python 第二实现**。`recovery\work\task101\make_session_sokoban.py` 的 `Sim` 与 `make_session_bomberman.py` 的 `BSim` 各自从**规则**重写一遍载荷的逻辑（关卡解析、走法与推箱合法性、撤销栈、角点 + 2×2 死锁、爆炸扩散与「第一块砖吃下并停住」、链式引爆、敌人追击优先级、三种哈希），会话里每一处关键断言的期望值都取自它们。
2. **事后复算不看 `report.json`、不看断言助手、不看 C#**。`recompute_readbacks.py` 把载荷**打印出来的** `Dump()` 一行行拆开，用**自己的**代码从**打印出来的 ASCII 盘面**重算哈希（Sokoban 墙 2 / 地板 1 / 目标 3 / 箱 4 / 箱在目标 5 / 玩家 6 / 玩家在目标 7；Bomberman 硬墙 1 / 地板 2 / 砖 3，都是 32 位 multiply-31 链），再把第二实现算出的字面量与载荷在本轮响应文件里**实际回报的 `actual`** 逐条对齐。
3. **像素与帧**：`pixel_recompute.py`（逐调用 capture 对，自己解码 PNG、两条规则各算一遍）与 `frames_recompute.py`（`user://` 保存帧，自己按 mtime 排序、自己 sha256、自己对 `report.json`）。

| 运行 | `Dump()` 盘面哈希 | 字面量逐条对齐 | 逐调用对 非零（引擎规则 >10） | 与 `report.json` 不符的对 | `user://` 帧链（复算） |
|---|---|---|---|---|---|
| Sokoban **r2** | **2/2 OK**（从打印的 ASCII 重推） | **12/12 OK** | **29/190**（编辑器 1/14、游戏 28/176） | **0** | **0 / 61371 / 95473 / 90574 / 9796** |
| Bomberman **r4** | **2/2 OK** | **14/14 OK** | **45/233**（编辑器 1/14、游戏 44/219） | **0** | **7541 / 176025 / 168478 / 74786 / 114995** |

两款的保存帧 sha256 与 `report.json` 记录的**逐一相同**；Sokoban 六帧里 **5 个 sha 互不相同**（`t0` == `t1` 正是那 0 px：`t1` 拍在撤销之后）、Bomberman **6/6 互不相同**。`TOTAL RECOMPUTATION MISMATCHES: 0`（两款）。

**跨轮一致性观察（如实记录）**：Sokoban r2 的 `t0`/`t1`/`t2`/`t3`/`t5` 与 r1 **逐字节相同**，只有 `t4`（自动巡逻采样之后那一帧）不同——与 2048 的 t4 同一种现象（帧时序无法逐字节复现）。Bomberman 从 r1 到 r2 之后 `t2`/`t3`/`t4` 变了，因为 B-1 改了「接触后敌人是否留下」，盘面本来就不同。

### A5 四条缺陷（各自首轮照出来、修好并重跑）

| id | 层 | 现象（证据） | 根因 | 处置 → 重跑结果 |
|---|---|---|---|---|
| **K-1** | Sokoban（会话） | 首轮 `runs\sokoban\soko-task101-r1` 的 `g145-assert-steps` 期望 5 **实得 2**、`g146-assert-player` 期望 `PlayerCol=3` **实得 4**；而同刻 `g142`（`LastHookSteps=2`）、`g144`（`AutoSteps=2`）、`g147`（`PlayerRow=2`）都 PASS。载荷自己的回报是诚实的：`g141` 返回 `autostep requested=2 attempts=2 accepted=2 total=2 steps=2`、`g148` 返回 `accepted=3 total=5 steps=5` | 会话生成器把同一个仿真实例**连用了两次** `auto_step`，而第一次调用之后的断言引用的是**两次调用之后**的快照（`AUTO2.steps`=5、`AUTO2.pc`=3）。**C# 是对的，是会话读错了时刻**——与 P-1 / A-1 / T-3 同一类，但这次错在**取值时机** | **改**：在第一次 `auto_step(2)` 之后显式快照 `AUTO2_STEPS2` / `AUTO2_PC2` / `AUTO2_PR2`，三条断言改用快照。r2：`g145`=2、`g146`=4、`g147`=2 **三条同时 PASS**，`g140`..`g152` 全绿 |
| **B-1** | Bomberman（**载荷**） | 首轮 `runs\bomberman\bomb-task101-r1` 的 `g127-assert-alive` 期望 `EnemiesAlive=1` **实得 0**、`g129-assert-unit-hash` 期望 `1287431919` **实得 2024506202**；而同一刻 `g123`（`DeadByEnemy=true`）、`g125`（`Lives=2`）、`g126`（重生）全 PASS——「玩家被抓」确实发生了，只是敌人也没了 | `Move` 走进敌人格时先 `_enemyRow.RemoveAt(caught)` 再 `KillPlayer("enemy")`。经典规则是「接触即掉命、敌人**存活**」；第一版把敌人当消耗品，`EnemiesAlive` 与 `UnitHash` 因此和证据所引用的规则不符。**这是 Python 第二实现 `BSim` 算出来的** | **改**：删掉那两行 `RemoveAt`，并把 `alive={EnemiesAlive}` 补进 `LastEvent`。r2 起：`g123`/`g125`/`g126`/`g127`/`g129` **五条同时 PASS** |
| **B-2** | Bomberman（会话） | 首轮 `g90-assert-probe-brick` 期望 `ProbeRow=2` **实得 -1** | 会话在那条断言之前**没有在那块盘面上探过任何格子**：`g81` 的 `ForceTestState` 按确定性规则把 `Probe*` 一并归零。注释与断言名（`probe-brick`）也都与实际不符 | **改**：改成显式 `ProbeCell(1,3)` + 断言 `ProbeRow=1` 与 `ProbeState=floor`，再 `ProbeCell(2,4)` 看幸存的那块砖。r4：`g90`/`g90b`/`g90c`/`g91`/`g92` 全 PASS |
| **B-3** | Bomberman（会话 / 测试设计） | r2 的 `g178-samples-clock` 30 帧采样里 **`AutoTicks` 恒定 4、`BombsActive` 恒定 0、`BricksRemaining` 恒定 0、`Elapsed`/`Ticks` 在走**；r3 同样（`AutoTicks` 恒定 6、`BombsActive` 恒定 0）。**两次的断言都照样全 PASS**，是多帧采样把它照出来的——与 F-1 一模一样的照法 | 两处叠加：①钉板把炸弹放在 `(3,4)`，而那是**砖块格**——`PlaceBomb` 永远到不了的状态（它只在玩家脚下放炸弹，而玩家永远站不到砖上），爆炸于是把**炸弹自己脚下那块砖**也炸了，两块砖一起没 → `Won` → `GameOver` → 时钟停机；②r3 把引信定成 8，而 `SetAutoClock` 与 `samples` 之间那两三次调用的时间里时钟已经烧掉 6 格 | **改**：钉板改成「炸弹在**地板** `(4,4)`、三块砖里只有两块在爆炸范围内、剩下的那块保证**永远赢不了**」，并**按实测时钟速率给引信定尺**（累加器是墙钟驱动的，30 帧采样 ≈ `60 × 0.478 s ≈ 29` tick，与帧率无关，故引信 24 **必然**在窗口内烧完、又**必然**活过采样开始前那几次调用）。r4 采样：`BombList` **17 个不同值**、**第 16 帧**五条属性同时跳变 |

**这四条的方法论价值**：K-1 是「断言取值时机」、B-1 是「第二实现照出载荷规则错」、B-2 是「断言与前提不符」、B-3 是「钉板必须是游戏真能到达的状态 / 采样窗口要按实测速率定尺」。四条都**不是工具缺陷**，`modules\mcp_server` 本轮零字节改动。

### A6 缺陷清单

**工具缺陷（`modules\mcp_server`）：0 条。** 六轮共 1334 条调用里没有一条是「工具做错了事」；唯一的非 `ok` 判定是每条运行里两条**声明的**边界调用（同名拒绝 `-32000`、不存在的属性 `-32001`）。

**游戏或驱动缺陷：4 条（K-1、B-1、B-2、B-3，均已修并在 r2 / r4 复核）。**

---

## B. 收尾

### B1「模块字节未动 → 免跑十门」这个判定

`modules\mcp_server` 本轮**代码一个字节没动**：引擎仓 `git status --short` 为空，`git diff --name-only --no-renames 2385fe2fb..HEAD` 仍只有 `MCP-TRACEABILITY.md` 与 `REBUILT-2C-MANIFEST.md` 两份 `.md`。两个变体仍是 TASK-097 在模块提交 `2385fe2fb5` 之后重建的那两份（自报 `4.8.dev.mono.custom_build.2385fe2fb`）。

`tools\run_gates.ps1 -Tag task101-doconly` 的真实输出（`runs\gates\task101-doconly\summary.txt`、逐字见 `logs\gates-task101-doconly.txt`）：

```
GATES_PREFLIGHT VERSION_TEXT=4.8.dev.mono.custom_build.2385fe2fb
GATES_PREFLIGHT ANCHOR=2385fe2fb HEAD=e041cae27 ANCHOR_REPORTED=2385fe2fb
GATES_PREFLIGHT WORKING_TREE_RED=0 WORKING_TREE_SAFE=0 COMMITTED_DIFF_SAFE=2
GATES_PREFLIGHT VERDICT=ANCHOR_STRUCTURAL_EQUIVALENT
GATES_PREFLIGHT REASON="2385fe2fb is an ancestor of e041cae27 and all 2 file(s) in the diff are non-compiling; the binary is NOT equal to HEAD, it is structurally equivalent to it"
GATES_PREFLIGHT NONCOMPILING_COUNT=2
GATES_PREFLIGHT NONCOMPILING modules/mcp_server/docs/reports/MCP-TRACEABILITY.md
GATES_PREFLIGHT NONCOMPILING modules/mcp_server/docs/reports/REBUILT-2C-MANIFEST.md
GATES_PREFLIGHT RESULT=SKIP_REBUILD
GATES_SKIPPED=1
```

**如实说明**：本轮**没有重建两个变体、没有跑十道门、没有跑 `accept_m1`、没有 push 代码**，判定的依据是「引擎仓没有任何编译输入」。任何「门应该是绿的」的说法本轮**都不成立**，因为没有跑。

### B2 提交与两个仓库

**主仓**（分支 `master`，无远端）：`26553df`，**173 个文件，26899 行增 / 1 行删**。提交信息对应 `DECISIONS.md` 的 D149。

**引擎仓**（分支 `feature/mcp-server-module-rebuild`）：**本轮没有任何提交，也没有 push** —— `git status --short` 空，`git rev-parse HEAD` = `git rev-parse refs/remotes/origin/feature/mcp-server-module-rebuild` = `e041cae270487d5c910f1e7ebe0e13982886d602`。两仓的 `git log --oneline -8` 与 `git status --short` 见 §F。

### B3 `--import` 的关机期访问违例

本轮**六次导入全部 `IMPORT_EXIT=0`、`import.stderr.txt` 0 字节**（Sokoban r1/r2、Bomberman r1/r2/r3/r4）。累计口径因此从 **3 次 / 17 次会话导入** 变成 **3 次 / 23 次**。台账待办 2 的判定不变：**不改引擎、不重建**，等可复现配方或用户授权。

### B4 收尾后的进程与端口

最后一轮之后：无 `Godot*` 进程；会话端口 `9944/9945`、`9946/9947` 无 **LISTENING**；门预检没有跑门、没有占用 9888/9889。**未改变机器显示或串流状态**（未停 `GameViewer`、未动设备/注册表/电源/显示拓扑）。

---

## C. 铁律遵守（逐条对照）

| 铁律 | 遵守情况 |
|---|---|
| ① 禁止一切 shell 重定向 | **基本遵守，有一处违例已记录**：所有 python / powershell / cmd 调用一律 `Start-Process -RedirectStandardOutput/-RedirectStandardError <绝对路径>` 拥有 stdout/stderr（`capture.ps1` / `run_one.ps1` / `commit.ps1`）；所有文本文件由 Python 写入器或 `write`/`edit` 工具写。**违例一处**：本会话第一次跑 `assertions.py` 时用了 PowerShell 的 `>` 把输出写进 `logs\assert-soko-r1.txt`；发现后立刻改为 `capture.ps1`（`Start-Process` 拥有输出），该文件随后被同一条 `Start-Process` 重写。**此后本任务再没有出现过 `>` 或 `>>`。** |
| ② 破坏性命令默认拒绝 | **遵守，且本轮零删除**：唯一的「移动」是四次归档工程——先写 129 文件的 sha256 清单、目标不存在才 `Move-Item`，**自始至终没有删除任何文件**；没有杀任何非本任务进程。 |
| ③ 构建与运行从 cmd 启动 | **遵守**：六次会话运行、两次 `new_game`（经 `reset_game_project.ps1` 生成的 `.cmd` 与直接调用）、门预检全部是 `Start-Process cmd.exe /c …`；`dotnet build` 由会话内的 `project_build_csharp` 触发。 |
| ④ 唯一端口 + 跑前查进程与端口 | **遵守**：`9944/9945`（Sokoban r1、r2）、`9946/9947`（Bomberman r1..r4）；每次开跑前 `netstat` + `Get-Process` 确认无残留，收尾后再查一次（无 `Godot*`、无 LISTENING）。 |
| ⑤ 会话文件先双解析后才执行 | **遵守**：六个会话在开引擎之前都过 `check_session.py`（Python JSON + 形状 + `content_file` 可达）与 `check_session_ps.ps1`（PS 5.1 `ConvertFrom-Json`），两侧都 PASS。 |
| ⑥ 迁移与删除先存证 sha | **遵守**：四次 `Move-Item` 之前各写出一份该工程 129 个文件的 sha256 清单（`archive\*.manifest.json`，已入库）；本轮没有删除操作。 |
| ⑦ 不改变机器显示或串流状态 | **遵守**：未停 `GameViewer`、未改设备/注册表/电源、未接触显示拓扑。 |

---

## D. 本任务产出的文件

```
recovery\work\task101\
  make_session_sokoban.py / make_session_bomberman.py   两款游戏的会话生成器 + Python 第二实现（Sim / BSim）
  recompute_readbacks.py                                事后复算：从打印的 ASCII 盘面重算哈希 + 字面量逐条对齐
  append_decisions.py + decisions-d149.md               写入 DECISIONS.md 的正文（Python 写入器，非 shell 重定向）
  capture.ps1 / run_one.ps1 / commit.ps1                三件套：拥有输出、唯一端口、从 cmd 提交
  check_session.py / check_session_ps.ps1               铁律 5 的双解析（Python + PS 5.1）
  reset_game_project.ps1                                先写 sha 清单再移动 + 重新实例化
  assertions.py / extra_assertions.py / samples.py / run_summary.py
  pixel_recompute.py / frames_recompute.py / editor_facts.py / recompute_readbacks.py / peek.py / callread.py
  commit-message.txt                                    主仓提交信息原文
  archive\sokoban-r1 / bomberman-r1 / bomberman-r2 / bomberman-r3（各含 .manifest.json）
  logs\                                                 40+ 份证据日志（六轮会话、断言、采样、复算、门预检、归档）
tools\sessions\sokoban\session.json + payload\SokobanGame.cs
tools\sessions\bomberman\session.json + payload\BombermanGame.cs
projects\sokoban\ / projects\bomberman\                 由模板实例化、随后全部由 MCP 调用写成
runs\sokoban\soko-task101-{r1,r2}\、runs\bomberman\bomb-task101-{r1,r2,r3,r4}\   （盘上路径；runs\ 按 .gitignore 不入库）
runs\gates\task101-doconly\                            （同上，不入库）
GAME-LOOP-LOG.md                                       第 12/13 行 + K-1/B-1/B-2/B-3 四条缺陷行 + TASK-101 记录节 + 待办续写
DECISIONS.md                                           D149
```

> `runs\` 按 `.gitignore` 不入库（盘上真实存在）；本报告所有 `runs\...` 引用都是盘上路径。
> `recovery\work\task101\`（含四份归档工程）、两款游戏工程与会话均已入库。

---

## E. 真实跑出来的数字速查（都可在盘上复算）

| 项 | Sokoban | Bomberman |
|---|---|---|
| 运行目录 | `runs\sokoban\soko-task101-r2`（首轮 `-r1` 对照） | `runs\bomberman\bomb-task101-r4`（首轮 `-r1`，中间 `-r2` / `-r3`） |
| 调用数（编辑器 / 游戏） | 190（14 / 176） | 233（14 / 219） |
| `facts_complete` | 190/190（100%） | 233/233（100%） |
| `args_evidence` | 编辑器 `sidecar_verified=1` + `inline_complete=13`；游戏 `inline_complete=176` | 编辑器 `sidecar_verified=1` + `inline_complete=13`；游戏 `inline_complete=219` |
| 判定分布 | `failed=2` / `ok_effect_observed=25` / `ok_file_effect_observed=133` / `ok_no_effect_observed=30` | `failed=2` / `43` / `153` / `35` |
| 断言 | 124 PASS + 1 声明 ERROR（node-state）＋ 3 PASS（屏幕文本 + 场景）= **127 PASS** | 143 PASS + 1 声明 ERROR ＋ 4 PASS = **147 PASS** |
| 像素差非零 | 29/190（1/14、28/176） | 45/233（1/14、44/219） |
| `user://` 帧链 | 0 / 61371 / 95473 / 90574 / 9796（六帧 5/6 不同 sha） | 7541 / 176025 / 168478 / 74786 / 114995（六帧 6/6 不同 sha） |
| 场景 sha（`e05`=`e09`） | `d5c22b0d…`（831 B） | `05672aed…`（844 B） |
| `project_build_csharp` | exit 0（3692 ms） | exit 0 |
| `project_validate_scripts` / `editor_get_errors` | `invalid_count=0` / `count=0` | `invalid_count=0` |
| 树里 `@` 自动名 | 0（75 / 76 个节点名） | 0（127 / 128 个节点名） |
| `--import` | exit 0（r1、r2 各一次） | exit 0（r1..r4 各一次） |
| 缺陷（工具 / 游戏或驱动） | 0 / 0（r1 有 K-1，已修） | 0 / 0（r1 有 B-1/B-2、r2/r3 有 B-3，均已修） |
| 独立复算不符数 | 0 | 0 |
| 门跑器（本轮） | — | 纯文档：`SKIP_REBUILD` + `GATES_SKIPPED=1` + exit 0（**十道门一门未跑**） |

---

## F. 提交后的逐字复核（本报告自身的提交之前）

**边界说明**：本节的两段帐是**主仓 `26553df` 提交之后、本报告那次提交之前**的那一刻的两仓状态。此后本报告自身的提交（以及任何纯文档追加）只让主仓 `git log` 顶部多出一个**文档**提交；本节里唯一会变旧的是 `git log` 的顶部行与 `git status --short` 的输出，而**「主仓新增 173 个文件、引擎仓 `git status --short` 为空、引擎仓与远端同级」**这三点不会因此改变。

### F1 主仓 `F:\moonbit-hof-rs`（分支 `master`，无远端）

`git log --oneline -8`：

```
26553df feat(godot-mcp): TASK-101 (D149) - the 12th and 13th C# games are delivered through MCP calls only (Sokoban: a grid push game with box and goal counts, the classic corner plus 2x2 simple deadlock test, level completion and an undo that rolls the player and the box back together; Bomberman: a 13x9 field of hard walls, ten destructible bricks and two enemies, grid movement, a fixed-fuse bomb, a blast that is stopped by a wall and takes the FIRST brick each way, a chain reaction, a deterministic greedy enemy chase, lives and respawn, and a win that one blast can deliver), both with a float-accumulator clock, both with two single-writer increment properties, both replaying the D-3 duplicate-name batch for its -32000 refusal, both with a second Python implementation of their own rules whose outputs are the session's assertion literals, and both with a post-hoc recomputation that derives the printed board's hash and every blast cell from the printed ASCII alone
3f28def docs(godot-mcp): TASK-100 - the report: the two new C# games with their real call counts, verdict distributions, assertion tallies and independently recomputed pixel columns, the two defects the first runs caught (a payload property with two writers, read as 0 by the time the assertion ran, and a session that assumed ForceTestState preserves a counter) with their fixes and re-runs, and the gate runner's doc-only preflight that skipped the ten gates because not one module byte changed
67bcbb0 feat(godot-mcp): TASK-100 (D148) - the 10th and 11th C# games are delivered through MCP calls only (2048: a 4x4 unknown-number grid with four-direction slide-and-merge, scoring, the 2048 win, the no-legal-move loss and illegal moves refused with a byte-identical board; Minesweeper: a 9x9 ten-mine field from a seeded LCG whose layout the session generator recomputes independently in Python, flood reveal, number hints, flags, first-click safety, win and loss, and illegal operations refused), both with a float-accumulator clock, both with two single-writer increment properties after the G1 defect (one property with two writers read 0 by the time the assertion ran), both replaying the D-3 duplicate-name batch for its -32000 refusal, and the gate runner's doc-only preflight reporting ANCHOR_STRUCTURAL_EQUIVALENT plus SKIP_REBUILD because not one module byte changed
fbf4bf1 docs(godot-mcp): TASK-099 - the report: the two new C# games with their real call counts, verdict distributions, assertion tallies and independently recomputed pixel columns, the Flappy payload defect the multi-frame sample caught with its fix and re-run, the gate runner's doc-only preflight with both measured cases and why it cannot reach either variant, and the third live --import shutdown access violation recorded with 24 more controlled probes at zero crashes and no engine edit
7b5fa56 feat(godot-mcp): TASK-099 - the 8th and 9th C# games are delivered through MCP calls only (Frogger: a 13x15 grid crossing with traffic, logs, homes and lives; Flappy Bird: one fixed 1/60 s frame of gravity, gaps, scoring and collisions, with the Flappy payload defect a 30-frame sample caught fixed and re-run), the gate runner learns to recognise a purely non-compiling submission and skip the ten gates for it while still running them the moment anything can change the compiled binary, the third live --import shutdown access violation is recorded with 24 more controlled probes at zero crashes and no engine edit, and ledger G-1 is closed at the root
5c83668 docs(godot-mcp): TASK-098 - the report: the two new C# games with their before/after runs, the section 7 alignment, the leftover accounting reconciled from a git-status entry count to a file count, the seven-row number re-read, and the import access violation recorded as unreproducible in 64 controlled runs with its static localisation
fdbbed6 feat(godot-mcp): TASK-098 - the 6th and 7th C# games are delivered through MCP calls only, MCP-TRACEABILITY section 7 is aligned with the D-1 closure, and the TASK-096 leftovers are resolved by enforcing the verdict TASK-096 had already recorded
ddc0dbb docs(godot-mcp): TASK-097 - the report's closing boundary is restated so it cannot be made stale by the task's own doc-only follow-ups: the snapshot is the state right after the report commit, and the two follow-ups that exist are listed verbatim
```

`git status --short`：**只有两行**，都是本报告提交工具自己写的日志（`recovery/work/task101/logs/git-commit.txt` 与 `.err.txt`，在 `git add -A` 之后又被 `Start-Process` 的句柄追加过），会随本报告的提交一并入库；本任务的新增与改动全部随 `26553df` 入库（`git show --stat` 给出 **173 files changed, 26899 insertions(+), 1 deletion(-)**，那 1 行删是 `GAME-LOOP-LOG.md` 待办第 2 条的续写替换）。

### F2 引擎仓 `F:\moonbit-hof-rs\godot-mcp\godot`（分支 `feature/mcp-server-module-rebuild`）

`git log --oneline -8`（**与本轮开始时逐字相同 —— 本轮没有提交**）：

```
e041cae270 modules/mcp_server: task099 - REBUILT-2C-MANIFEST gains the 2c-11 section: the gate runner's doc-only preflight (one classifier, dot-sourced from the module's own anchor judge, anchor taken from the built binary's --version, committed range plus working tree, and the two measured cases with all ten gates green in the compile-input one), the third live --import shutdown access violation with its 24 controlled probes at 0 crashes, and the explicit reason why the change to tools/run_gates.ps1 cannot reach either variant (it is a main-repository script, so the engine tree has no byte to rebuild)
0fbd5ec4cb modules/mcp_server: task098 - MCP-TRACEABILITY section 7 is aligned with the D-1 closure
094b071f9b modules/mcp_server: task097 - REBUILT-2C-MANIFEST gains the 2c-10 section: the name-conflict policy the section registers (the default refusal with its complete conflict list, its error code and its opt-in rename), the contract's six shape quantities after the append-only override (177/6/1.22.0/154/73/idempotent, sha 64ddce9f), the ten gates and accept_m1 22/22 with their real exit codes, and the three iron-rule deviations of this task recorded rather than hidden
2385fe2fb5 modules/mcp_server: task097 (D-3) - a requested node name the target parent already carries is now refused instead of silently renamed, so a replayed editor phase can no longer write a whole duplicate node layer into a scene; editor_save_scene reports the duplicates a batch made under an explicit rename instead of saving them silently
95aa1d8984 modules/mcp_server: task096 - MCP-TRACEABILITY gains section 7: what the evidence chain is when the pixel diff is unavailable, and how the ledger is to be read then; the section also carries the re-localisation of D-1 (the duplicate node layer a replayed editor phase writes into a scene), which is why the three older games' pixel column says unavailable rather than 0
8b9dd9a72b modules/mcp_server: task094 - D-2 is a load-sensitive readiness predicate, not a defect: the accept_m1 wait now asks the main loop to advance (frame_count strictly increasing six samples in a row) instead of asking it to be faster than 20 fps, so the suite is 22/22 solo and 22/22 under eight CPU burners
cf554ef58c modules/mcp_server: task092 (B2/B3/B4) step2 - a deferred call's file effects and its capture are collected at completion, the two missing doctests exist, and the frame cost is a clamped median of a window
87fbf82f4b modules/mcp_server: task092 (B1) step1 - an over-bound payload is written whole to a sidecar the line can be checked against, and the ledger re-hashes it
```

`git status --short`：**空**；`git rev-parse HEAD` = `git rev-parse refs/remotes/origin/feature/mcp-server-module-rebuild` = **`e041cae270487d5c910f1e7ebe0e13982886d602`**（与远端同级，本轮未 push 任何东西）。

### F3 收尾后的进程与端口

无残留 `Godot*` 进程；`9944/9945`、`9946/9947` 无 **LISTENING**。**未改变机器显示或串流状态。**
