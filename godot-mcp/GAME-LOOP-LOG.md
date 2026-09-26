# GAME-LOOP-LOG — 跨轮进度台账（每轮更新）

* 目标口径：**D138** —— 轮次不设限，**至少 20 个经典小游戏、全部 C#**，每款都要有可复算的
  「操作有效性」证据（像素差 / 文件 sha / 断言 / 场景树快照），不接受「应该动了」。
* 证据根：`godot-mcp\runs\<game>\<run-tag>\`（`trace-*.jsonl` / `ledger-*.{txt,json}` /
  `report.{md,json}` / `shots-*/` / `engine-*.stdout.txt`）。
* 缺陷分两栏：**工具缺陷** = `modules\mcp_server` 的行为 / 日志 / 错误信息问题；
  **游戏或驱动缺陷** = 工程、脚本、会话、`tools\` 下的驱动问题。根因不清楚的只记录、不猜改。
* **本表的数字全部取自当轮产物**（`report.json` / `ledger-*.txt` / TASK-091 报告），不是凭印象。

---

## 台账

| # | 游戏 | 语言 | 会话调用数（编辑器 / 游戏） | `facts_complete` | 判定分布摘要 | 缺陷数（工具 / 游戏或驱动） | 证据路径 | 备注 |
|---|---|---|---|---|---|---|---|---|
| 1 | Pong | C# | 23 / 29（52） | run-4 **44/52**（编辑器 21/23、游戏 23/29）；TASK-092 重跑 **52/52（100%）** | run-4：`ok_effect=9, ok_effect_unavailable=7, ok_file_effect=18, ok_no_effect=18`（两相合计）；重跑：`ok_effect=9, ok_file=23, ok_no_effect=20`，`unavailable` 归零 | **0 / 6**（P-1..P-6；模块字节未改，故无工具缺陷） | `runs\pong\pong-run{1..4}\`、`runs\pong\pong-task092\` | 第 1 个游戏。像素差在 TASK-092 重跑里 **10/29 组非零**（当轮文件今天仍能复算出同一批数）；「注定失败的断言」2 条（run-4 的 `seq=12` 场景断言 + `seq=27` 屏幕文本）。**像素差 = 已回填（TASK-097 清理后重放）**：`runs\pong\pong-clean-task097` 的 74 个可比 capture pair 里 **14 个非零**（编辑器 3/45、游戏 11/29），`user://` 五帧逐对：`pong-t0`→`t1` **512 px**、`t1`→`t2` **512 px**、`t2`→`final` **7175 px**；`tools\game_report.py` 与 `recovery\work\task097\pixel_recompute.py`（独立复算）**逐对一致、0 处不符**。清理前的历史值（TASK-092 的 **10/29 非零**、副本写入后同一会话只剩 1/52）保留为「D-1 时期」对照，见 D-1 |
| 2 | Breakout | C# | 21 / 34（55） | **55/55（100%）**（编辑器 21/21、游戏 34/34） | `ok_file_effect=15`（编辑器 3 + 游戏 12）、`ok_no_effect=38`（17 + 21）、`failed=2`（每相各 1 条声明失败） | **0 / 5**（B-1 侧壁抹平水平速度、B-2 `HitsPaddle` 跨坐标系比较、B-3 HUD 两个写者、会话坐标约定误用、目标砖一格的会话缺陷） | `runs\breakout\breakout-task093-r7\`（最终）；r2/r3/r4/r5/r6 是逐步修复的中间轮 | 挡板/球/15 砖/碰撞消砖/计分/胜负全部由断言钉住（`PaddleBounces=7`、`Brick_r2_c0.Alive=false`、`Score=10`、`BricksRemaining=14`、`HUD="SCORE 10"`、胜负未达成的断言按设计失败、边界调用 `-32000/timeout_ms=1000`）；**像素差 = 已回填（TASK-097 清理后重放）**：`runs\breakout\breakout-clean-task097` 的 89 个可比 pair 里 **14 个非零**（编辑器 2/55、游戏 12/34），`user://` 逐对：`breakout-t0`→`t1` **3072 px**、`t1`→`t2` **3464 px**、`t2`→`t3` **2529 px**、`t3`→`final` **2169 px**；独立复算（`pixel_recompute.py`）与报告逐对一致。TASK-093 记的 0/55 是「副本层挡住真实节点」时期的值（`shots-game\` 68 个 PNG 逐字节相同），见 D-1 |
| 3 | Snake | C# | 20 / 31（51） | **51/51（100%）**（编辑器 20/20、游戏 31/31） | `ok_file_effect=14`（3 + 11）、`ok_no_effect=36`（17 + 19）、`failed=2`（编辑器相 1 条声明失败 + 游戏相 1 条声明失败） | **0 / 4**（S-1 `ForceTestState` 不清胜负、S-2 `Score`/`FoodsEaten` 跨测不归零、S-3 场景注入动作被当成「按住」、S-4 会话把墙测瞄在最后一格） | `runs\snake\snake-task093-r6\`（最终）；r1..r5 是逐步修复的中间轮 | 网格移动/食物增长/自撞/撞墙/计分全部由断言钉住（30 帧冻结采样只有 1 个位置、45 帧移动采样出现 2 个位置、`Length=4`/`segments_in_use=4`、`LoseReason=self`、`LoseReason=wall`）；命中 `sidecar_verified=2`（编辑器相的 C# 载荷超限走旁路证据）；**像素差 = 已回填（TASK-097 清理后重放）**：`runs\snake\snake-clean-task097` 的 102 个可比 pair 里 **13 个非零**（编辑器 0/71、游戏 13/31），`user://` 逐对：`snake-t0`→`t1` **480000 px**、`t1`→`t2` **4032 px**、`t2`→`final` **480000 px**（480000 = 整个 800×600 帧都不同）；独立复算（`pixel_recompute.py`）与报告逐对一致。TASK-093 记的 0/51 是「副本层挡住真实节点」时期的值（`shots-game\` 62 个 PNG 逐字节相同），见 D-1 |
| 4 | Tetris | C# | 42（编辑器 6 / 游戏 36）；首轮 53（17 + 36） | **42/42（100%）**（编辑器 6/6、游戏 36/36） | `ok_file_effect_observed=15`（2 + 13）、`ok_effect_observed=8`（全部在游戏相）、`ok_no_effect_observed=18`（4 + 14）、`failed=1`（声明的边界调用：断言一个不存在的属性，`-32001`） | **0 / 3**（T-1 `WriteBoard` 只按 `/` 分行而会话用竖线、T-2 `HardDrop` 返回落锁前的状态、T-3 GameOver 用例填满整行导致「消行」先于「出生检查」；三条均已修并重跑同批对比） | `runs\tetris\tetris-task096-r2\`（最终）；首轮 `runs\tetris\tetris-task096\` | 第 4 个游戏。**像素差 11/42 非零**（`tetris-t0`→`t1` 3174 px、`t1`→`t2` 4232 px、`t2`→`t3` 8503 px）—— 这款游戏的场景是**干净**的（`r06-scene-still-clean` 里没有 `@ColorRect@` 副本），所以像素证据在这里**可得**，见 D-1 再定域；下落/消行/得分/GameOver 另有逐帧采样与断言钉住（`PieceY` 0→11、`Lines=1`、`Score=100`、`FilledCells` 8→4→6、`GameOver` false→true）；`sidecar_verified=1`；只用 MCP 调用开发（`project_create_script` / `project_edit_script` / `editor_add_nodes_batch` / `editor_save_scene` / `project_build_csharp`），五个输入动作由 `editor_add_input_action` 声明，**场景只建一次** |
| 5 | Space Invaders | C# | 59（编辑器 15 / 游戏 44，另 2 条 `sleep`） | **59/59（100%）**（编辑器 15/15、游戏 44/44） | 编辑器：`failed=1`（**声明的边界调用**：同名批量被 D-3 策略拒绝）、`ok_effect=1`、`ok_file_effect=6`、`ok_no_effect=7`；游戏：`ok_effect=9`、`ok_file_effect=22`、`ok_no_effect=13` | **0 / 0**（首轮一次通过，没有发现工具缺陷或游戏/驱动缺陷） | `runs\spaceinvaders\si-task097-r1\` | 第 5 个游戏。**像素差 12/59 非零**（编辑器 1/15、游戏 11/44），`user://` 逐对：`si-t0`→`t1` **1576 px**、`t1`→`t2` **38127 px**、`t2`→`t3` **16990 px**、`t3`→`t4` **4800 px**；独立复算逐对一致。场景只建一次：`e03` 批量加 5 个静态节点，`e06` **同一批再跑一次被 `-32000` 拒绝**（`data.conflicts` 列出 5 条路径），前后文件 sha `db5939a5…` **一字未变**；40 个入侵者是**运行期新建**的节点（`g46` 树里 `Invader_*` 恰好 40 个），另加一个运行期 `ProbeOverlay` 做视觉对照。断言：`Score` 0→10、`InvadersRemaining` 40→39→1→0、`InvadersKilled` 1、`WaveSteps` 0→11、`Won` true、`GameOver` true（胜）/ true（负）、屏幕文本 `WAVE CLEARED` 与 `GAME OVER`；`g07` 冻结基线（12 帧 `WaveX` 恒 140）对 `g09` 移动采样（`WaveX` 152→260，10 个不同值）。`project_build_csharp` exit 0（3533 ms）、`project_validate_scripts` `invalid_count=0`。**声明的一处采样局限**：`g14` 的子弹飞行采样开始得太晚（0.09 s 的飞行在两帧之间就结束了），它记到的是击杀后的状态；子弹确实飞过由 `t0`→`t1` 的 1576 px 与 `g13`/`g15`/`g16`/`g17` 的断言共同钉住 |
| 6 | Asteroids | C# | 71（编辑器 16 / 游戏 55） | **71/71（100%）**（编辑器 16/16、游戏 55/55） | 编辑器：`failed=1`（**声明的同名拒绝**）、`ok_effect=1`、`ok_file_effect=7`、`ok_no_effect=7`；游戏：`failed=1`（**声明的边界调用**：断言一个不存在的属性，`-32001`）、`ok_effect=14`、`ok_file_effect=32`、`ok_no_effect=8` | **0 / 1**（**A-1**：会话把 `ForceTestState` 会归零的计数器当成会保留，`g36` 期望 120 实得 100；已修期望并重跑 r2） | `runs\asteroids\ast-task098-r2\`（首轮 `ast-task098-r1`） | 第 6 个游戏。**像素差 16/71 非零**（编辑器 1/16、游戏 15/55），`user://` 六帧逐对：`ast-t0`→`t1` **14774 px**、`t1`→`t2` **996 px**、`t2`→`t3` **6346 px**、`t3`→`t4` **7072 px**、`t4`→`t5` **8960 px**；独立复算（`pixel_recompute.py` 的逐调用对 + `frames_recompute.py` 的保存帧）与 `report.json` **0 处不符**。场景只有 3 个静态节点（`Background`/`Hud`/`Status`），飞船、子弹与**每一颗岩石**都是 `_Ready()` 里**运行期新建**的 `ColorRect`；`e03` 批量加静态节点，`e06` **同一批再跑一次被 `-32000` 拒绝**，保存后的文件与拒绝前**逐字节相同**。飞船旋转/推进由固定步长钩子钉住（`ShipAngle` 0→-45、`ShipX` 400→**452**、`ShipVelX`=**104**）；小行星分裂四路同时成立（`AsteroidsSplit=1`、`AsteroidsRemaining` 1→2、`FirstRockSize`=2、`RockList()`=`0:s2@200,150\|1:s2@200,150`）；计分 20（大）→ 100（小，清场）、生命 `Lives` 3→**2**→**0**、`Won` true（清场）/ false（阵亡）。**多帧采样改正了 TASK-097 的采样时机局限**：`g15` 先把子弹放在 150 px 之外再采 40 帧，`BulletActive` 在前 14 帧为 true、**第 14 帧**同时发生 `Score` 0→20 与 `AsteroidsRemaining` 1→2 —— 飞行与击杀落在同一采样窗口内 |
| 7 | Pac-Man | C# | 80（编辑器 16 / 游戏 64） | **80/80（100%）**（编辑器 16/16、游戏 64/64） | 编辑器：`failed=1`（**声明的同名拒绝**）、`ok_effect=1`、`ok_file_effect=7`、`ok_no_effect=7`；游戏：`failed=1`（**声明的边界调用**，`-32001`）、`ok_effect=13`、`ok_file_effect=32`、`ok_no_effect=18` | **0 / 1**（**P-1**：会话把 `GhostSteps` 的**累计总数**当成一次 `StepGhosts` 的**增量**，`g15` 期望 12 实得 16；已把增量做成真导出属性 `LastPatrolSteps` 并重跑 r2） | `runs\pacman\pac-task098-r2\`（首轮 `pac-task098-r1`） | 第 7 个游戏。**像素差 15/80 非零**（编辑器 1/16、游戏 14/64），`user://` 五帧逐对：`pac-t0`→`t1` **18888 px**、`t1`→`t2` **1853 px**、`t2`→`t3` **18546 px**、`t3`→`t4` **9586 px**；独立复算与 `report.json` **0 处不符**。19×13 的网格迷宫、**125 颗豆子**、4 个幽灵与吃豆人**全部运行期新建**（`e06` 同名批量被 `-32000` 拒绝）。断言把规则逐条钉住：`TotalPellets=125`、`PelletsRemaining` 125→2→1→0、`PelletsEaten` 0→1、`Score` 0→10、`PacCol` 9→10、撞墙**不移动**（`blocked at=9,8 from=9,9`）、幽灵抓捕 `Lives` 3→**2**→**0**、`Won` true（豆子清空）/ false（被抓）；幽灵巡逻由 `LastPatrolSteps` 的**增量**（末轮 =5）与 30 帧移动采样两路钉住（`Ghost0Col` 30 个不同值）；`running_game_run_test_scenario` 用声明的 `pac_right` 动作真的把 `PacCol` 推过 9（`all_passed=true`、`passed=1`）。**一处游戏侧的自保**：重建棋盘时先 `RemoveChild` 再 `QueueFree`，否则同一帧里重建的 `Wall_r2_c3` 会因为名字还被占着而被引擎改名成 `@ColorRect@N` —— 与 D-3 同一个陷阱；`g64` 的 248 个节点里 **0 个 `@` 开头的名字** |
| 8 | Frogger | C# | 90（编辑器 16 / 游戏 74） | **90/90（100%）**（编辑器 16/16、游戏 74/74） | 编辑器：`failed=1`（**声明的同名拒绝**）、`ok_effect=1`、`ok_file_effect=7`、`ok_no_effect=7`；游戏：`failed=1`（**声明的边界调用**，`-32001`）、`ok_effect=16`、`ok_file_effect=42`、`ok_no_effect=15` | **0 / 0**（首轮一次通过，没有发现工具缺陷或游戏/驱动缺陷） | `runs\frogger\frog-task099-r1\` | 第 8 个游戏。**像素差 17/90 非零**（编辑器 1/16、游戏 16/74），`user://` 五帧逐对：`frog-t0`→`t1` **8864 px**、`t1`→`t2` **9178 px**、`t2`→`t3` **9291 px**、`t3`→`t4` **9943 px**，五个帧 sha 互不相同；独立复算（`pixel_recompute.py` 逐调用对 + `frames_recompute.py` 保存帧）与 `report.json` **0 处不符**。13×15 的格点：5 条车道（row 9–13）各一辆车、row 8 是隔离带、5 行河（row 3–7）各一根两格浮木、row 0 是终点线、row 14 是出发点；**地形条、5 辆车、5 根浮木与青蛙全部运行期新建**，场景只有 3 个静态节点（`Background`/`Hud`/`Status`）。断言把规则逐条钉住：`FrogCol`/`FrogRow`（起点 6,14）、出界**不移动**（`blocked at=-1,14`）、空车道可走（13→12）、车撞 `Lives` 3→2 并回到起点、落水 `Lives` 3→2、浮木**载着青蛙走**（`FrogCol` 6→5 且仍在 row 4）、第五个家 `HomesReached` 4→5 + `Score`=50 + `Won`/`GameOver`=true、最后一命被撞后 `Lives`=0 + `Won`=false、屏幕文本 `ALL HOMES FILLED` / `GAME OVER`。确定性：`CarSpeed` 默认 0、`PollInput` 默认 false，运动只经固定步长钩子（`StepTraffic(5)` 的**增量** `LastTrafficSteps=5`，总数 `TrafficSteps=9` 含 30 帧巡逻采样让时钟推进的 4 步 —— 与 P-1 同一条教训，本轮一开始就用增量断言）；冻结基线（12 帧 `FrogCol`/`FrogRow`/`Car0Col`/`Log0Col` 各 1 个值、`Ticks` 12 个不同值）对移动采样（30 帧 `Car0Col`/`Log0Col` 逐帧变化）。`e06` 的**同名批量被 `-32000` 拒绝**且 `e05`/`e09` 文件 sha 一字未变；声明的 `frog_up` 动作真的把 `FrogRow` 推过 14（`all_passed=true`） |
| 9 | Flappy Bird | C# | 92（编辑器 14 / 游戏 78） | **92/92（100%）**（编辑器 14/14、游戏 78/78） | 编辑器：`failed=1`（**声明的同名拒绝**）、`ok_effect=1`、`ok_file_effect=5`、`ok_no_effect=7`；游戏：`failed=1`（**声明的边界调用**，`-32001`）、`ok_effect=21`、`ok_file_effect=41`、`ok_no_effect=15` | **0 / 1**（**F-1**：`AutoRun` 把 `delta*60` 截断成 0，高帧率下自重跑时钟一格都不走；`g44` 的 30 帧采样抓到 —— `Ticks` 在走而 `Pipe0X` 恒定；已改成累加器并重跑 r2） | `runs\flappy\flappy-task099-r2\`（首轮 `runs\flappy\flappy-task099-r1\`） | 第 9 个游戏。**像素差 22/92 非零**（编辑器 1/14、游戏 21/78），`user://` 五帧逐对：`flappy-t0`→`t1` **34326 px**、`t1`→`t2` **98611 px**、`t2`→`t3` **1699 px**、`t3`→`t4` **99094 px**，五个帧 sha 互不相同；独立复算与 `report.json` **0 处不符**。r2 的五个帧与 r1 **逐字节相同**（同一条会话、同一台机器、确定性状态机 —— 「同一个被钉住的状态画出同一张图」）。**一个固定帧 = 1/60 s**：`AutoRun` 默认 false，世界只经 `Flap()` / `StepFrames(n)` / `StepUntilPass(n)` 前进，于是「一帧重力 = 23.33 px/s」「天花板钳到 y=0 且速度归零」「落地停在 y=564」都是确切值；通过管子是最强的一条确定性证据：`StepUntilPass(400)` 依次给出 **164 / 100 / 100 / 100 / 100 帧**、`LastPassDelta=1`、`Score` 10/20/…/50，第五根通过时 `Won`/`GameOver`=true（`PipesToClear=5`），期间 `PipesRecycled>0` 证明管子真的回到右边缘。多帧采样：冻结基线（12 帧 `BirdY`/`Pipe0X` 各 1 个值、`Ticks` 12 个不同值）对滚动采样（`SetAutoRun(true)` + 30 帧，**r2 里 `Pipe0X` 17 个不同值 576→492** 而 `BirdY` 恒定）；另有 `StepFrames(5)` 使 `Pipe0X` 600→**585**（180 px/s × 5/60 s = 15 px）。失败路径也被钉住：撞管 `GameOver`=true 且 `Score`=0、落地 `GameOver`=true + `BirdY`=564、屏幕文本 `COURSE CLEARED` / `GAME OVER`。`e06` 同名批量被 `-32000` 拒绝且文件 sha 未变；两个声明动作 `flap` / `flappy_restart` 都接到载荷的真路径上（后者触发 `BuildWorld()` 重开） |
| 10 | 2048 | C# | 129（编辑器 16 / 游戏 113） | **129/129（100%）**（编辑器 16/16、游戏 113/113） | 编辑器：`failed=1`（**声明的同名拒绝**）、`ok_effect_observed=1`、`ok_file_effect_observed=7`、`ok_no_effect_observed=7`；游戏：`failed=1`（**声明的边界调用**，`-32001`）、`ok_effect_observed=22`、`ok_file_effect_observed=74`、`ok_no_effect_observed=16` | **0 / 1**（**G1**：`LastAutoSteps` 一个属性两个写者 —— `AutoStep` 钩子刚写完，下一帧的时钟又把它写回 0；r1 的两条增量断言实得 0。已拆成 `LastHookSteps`（钩子）与 `LastAutoSteps`（每帧时钟）两个属性并重跑 r2） | `runs\game2048\2048-task100-r2`（首轮 `runs\game2048\2048-task100-r1`） | 第 10 个游戏。4×4 未知数网格、四向滑动合并、计分、2048 取胜、无路可走判负、**非法移动被拒**（棋盘一字不变 + `MovesRejected` 计数）。**像素差 26/129 非零**（编辑器 1/16、游戏 25/113），`user://` 六帧逐对 **13055 / 15543 / 171792 / 148841 / 26181 px**，六个 sha 互不相同；独立复算（`pixel_recompute.py` 逐调用对 + `frames_recompute.py` 保存帧）与 `report.json` **0 处不符**。断言 **70 PASS + 1 条声明的边界失败**（node-state）＋ **2 条屏幕文本 PASS** ＋ **1 条场景断言 PASS** = **73 PASS**。四向都钉过确切棋盘（左 `2,2,4,0`→`4,4,0,0`、右 →`0,0,4,4`、上 →`4,4`、下 →底两格），合并得分 4→12→2048；赢局 `MaxTile=2048`、`Won=true`、`GameOver=false`；满盘无解 `CanMoveAny=false`、`GameOver=true`、`Won=false`、一动手即被拒；满盘但有一对相等**不算输**。**与帧率无关的增量属性**：`AutoStep(2)`→`LastHookSteps=2`、`AutoStep(3)`→3，而 `LastAutoSteps` 在时钟关闭时为 0；时钟用浮点累加器 `_autoAccum += delta*rate`，`Elapsed` 是每帧 `+= delta` 的浮点秒表（无截断）。多帧采样：冻结基线 12 帧（`GridHash`/`TilesInUse`/`MoveCount` 各 1 个值，`Elapsed`/`Ticks` 各 12 个不同值）对自动时钟 30 帧（`MoveCount` **30 个不同值 6→65**、`AutoSteps` 30 个、`GridHash` 4 个、`LastAutoSteps` {0,1}、`Elapsed`/`Ticks` 各 30 个）。`e06` 同名批量被 `-32000` 拒绝（`conflicts` 3 条），`e05`/`e09` 的 sha `7e7fb1d9…`（813 B）**逐字节相同**；`project_build_csharp` exit 0（3732 ms）、`invalid_count=0`、`editor_get_errors count=0`；三次 `running_game_get_scene_tree` 共 75 个节点名 **0 个 `@` 开头**。声明的 `m2048_left` 动作**按按下沿**只走一步（`InputMoves=1`） |
| 11 | Minesweeper | C# | 155（编辑器 14 / 游戏 141） | **155/155（100%）**（编辑器 14/14、游戏 141/141） | 编辑器：`failed=1`（**声明的同名拒绝**）、`ok_effect_observed=1`、`ok_file_effect_observed=5`、`ok_no_effect_observed=7`；游戏：`failed=1`（**声明的边界调用**，`-32001`）、`ok_effect_observed=19`、`ok_file_effect_observed=96`、`ok_no_effect_observed=25` | **0 / 1**（**M1**：会话把 `ForceTestState` 会归零的计数器当成会保留 —— r1 的收尾断言 `LastHookSteps eq 2` 实得 0；已改成「钩子、时钟、两条增量断言落在同一块被钉住的盘面上」并加一条显式断言，重跑 r2） | `runs\minesweeper\mine-task100-r2`（首轮 `runs\minesweeper\mine-task100-r1`） | 第 11 个游戏。9×9、10 雷、布雷（种子 LCG，**Python 用同一规则独立复算**出 `0,4\|0,5\|1,6\|2,4\|4,0\|6,0\|7,4\|7,7\|7,8\|8,0` 并作为断言字面量）、翻开、数字提示、标旗、首翻安全、失败与胜利判定、**非法操作被拒**。**像素差 21/155 非零**（编辑器 1/14、游戏 20/141），`user://` 五帧逐对 **194130 / 196947 / 196939 / 195563 px**，五个 sha 互不相同；独立复算 **0 处不符**；r2 的五个帧与 r1 **逐字节相同**（同一个被钉住的状态画出同一张图）。断言 **93 PASS + 1 条声明的边界失败** ＋ **2 条屏幕文本 PASS** ＋ **1 条场景断言 PASS** = **96 PASS**。规则逐条钉住：`MineList` 与复算一致、`SafeCells=71`；**首翻安全**（唯一那颗雷正在点击处 → `MinesRelocated=1`、`Exploded=false`、`MineList` 变成 `0,1`、点中的格子 `ProbeHint=1`）；数字提示（3 雷邻域 `ProbeHint=3`，雷自己 `hint=2`）；标旗与取消（`FlaggedCount` 1→0、`ProbeState` flagged→mine）；三种非法操作（翻已开的、标已开的、翻被标的）全部被拒且盘面不变（`Moves` 不动、`RejectedMoves` 1→2→3、`LastEvent` 含 `reason=already_revealed` / `reason=flagged`）；一次零提示翻开的**泛洪**开出 71 格 → `Won=true`、`GameOver=true`、`Exploded=false`；踩雷 `Exploded=true`、`ExplodedRow/Col=4,4`、`RevealedCount=0`、`Won=false`。与帧率无关的增量 `LastHookSteps`（`AutoStep(2)`→2）在时钟跑过 30 帧后仍是 2，而 `LastAutoSteps` 归 0；`ForceTestState` 把两条都归零（也是一条显式断言）。多帧采样：冻结基线 12 帧（`RevealHash`/`RevealedCount`/`FlaggedCount` 各 1 个值，`Elapsed`/`Ticks` 12 个不同值）对自动扫雷 30 帧（`RevealedCount` **7 个不同值 16→71**、`RevealHash` 7 个、`AutoSteps` 7 个、`Elapsed`/`Ticks` 各 30 个）。`e06` 同名批量被 `-32000` 拒绝，`e05`/`e09` 的 sha `1fcc873e…`（826 B）**逐字节相同**；`project_build_csharp` exit 0（3678 ms）、`invalid_count=0`、`errors count=0`；树里 333 个节点名 **0 个 `@` 开头**；声明的 `mine_reveal_next` 动作按按下沿只翻一格（`InputReveals=1`） |
| 12 | Sokoban | C# | 190（编辑器 14 / 游戏 176） | **190/190（100%）**（编辑器 14/14、游戏 176/176） | 编辑器：`failed=1`（**声明的同名拒绝**）、`ok_effect_observed=1`、`ok_file_effect_observed=5`、`ok_no_effect_observed=7`；游戏：`failed=1`（**声明的边界调用**，`-32001`）、`ok_effect_observed=24`、`ok_file_effect_observed=128`、`ok_no_effect_observed=23` | **0 / 1**（**K-1**：会话在**第一次** `AutoStep` 之后断言了仿真器**两次调用之后**的状态（`Steps` 期望 5 实得 2、`PlayerCol` 期望 3 实得 4）；C# 是对的，是会话读错了时刻 —— 已改成对第一次调用后的状态显式快照并重跑 r2） | `runs\sokoban\soko-task101-r2`（首轮 `runs\sokoban\soko-task101-r1`） | 第 12 个游戏。网格推箱、箱子与目标计数、**简单死锁判定**（角点 + 2×2 墙/箱方块，两条规则都在）、关卡完成与**撤销**（把玩家与被推的箱子一起回滚）。**像素差 29/190 非零**（编辑器 1/14、游戏 28/176），`user://` 六帧逐对 **0 / 61371 / 95473 / 90574 / 9796 px**（`t0`→`t1` 是 **0**：`t1` 拍在撤销之后，盘面逐字节回到起点 —— 这是「确定性」而不是缺陷）；六个 sha 里 5 个互不相同（`t0`==`t1` 正是那 0 px）；独立复算（`pixel_recompute.py` 逐调用对 + `frames_recompute.py` 保存帧 + `recompute_readbacks.py`）**0 处不符**。断言 **124 PASS + 1 条声明的边界失败**（ERROR）＋ **2 条屏幕文本 PASS** ＋ **1 条场景断言 PASS** = **127 PASS**。**Python 第二实现**（`recovery\work\task101\make_session_sokoban.py` 的 `Sim`）独立算出并作为断言字面量的有：四个关卡各自的 `BoardHash`、`BoxList`、`GoalList`、玩家坐标、`DeadlockList`（`2,1`）、每次推箱后的箱位与玩家位、`Undo` 之后恢复的盘面与哈希。规则逐条钉住：一次左推把箱子推上目标 → `Won=true`/`GameOver=true`/`Pushes=1`/`CanMoveAny=false`；赢后再动被拒（`reason=game_over`）；`Undo` 把 `Steps` 1→0、`Pushes` 1→0、`BoxList` 回到 `2,3`、`BoardHash` **逐位回到起点**；空栈撤销被拒（`reason=nothing_to_undo`）；走廊关 5 步 3 推通关（`BoxList=1,3\|3,1`），撤销一步后 `BoardHash` 等于复算的撤销值，再推一次又**逐位回到同一个通关哈希**；把箱子推进角落 → `Deadlocked=true`、`DeadlockList=2,1`、`GameOver=true`、`Won=false`；把箱子推向墙 → `reason=blocked_box` 且 `BoardHash` 不变；非法方向 → `reason=bad_dir`。与帧率无关的增量 `LastHookSteps`（`AutoStep(2)`→2、`AutoStep(3)`→3）在时钟跑过 30 帧后仍是 3，而 `LastAutoSteps` 归 0。多帧采样：冻结基线 12 帧（`BoardHash`/`BoxesOnGoal`/`Steps` 各 1 个值，`Elapsed`/`Ticks` 12 个不同值）对自动巡逻 30 帧（`Steps` **30 个不同值 15→59**、`AutoSteps` 30 个、`PlayerRow`/`PlayerCol` 各 2 个、`Elapsed`/`Ticks` 各 30 个）。`e06` 同名批量被 `-32000` 拒绝（3 条 `conflicts`），`e05`/`e09` 的 sha `d5c22b0d…`（831 B）**逐字节相同**；`project_build_csharp` exit 0（3692 ms）、`invalid_count=0`、`errors count=0`；两次 `running_game_get_scene_tree` 共 75/76 个节点名 **0 个 `@` 开头**；声明的 `soko_right` 动作按按下沿只走一格（`InputMoves=1`，`PlayerCol` 3→4） |
| 13 | Bomberman | C# | 233（编辑器 14 / 游戏 219） | **233/233（100%）**（编辑器 14/14、游戏 219/219） | 编辑器：`failed=1`（**声明的同名拒绝**）、`ok_effect_observed=1`、`ok_file_effect_observed=6`、`ok_no_effect_observed=6`；游戏：`failed=1`（**声明的边界调用**，`-32001`）、`ok_effect_observed=42`、`ok_file_effect_observed=147`、`ok_no_effect_observed=29` | **0 / 3**（**B-1 载荷**：走进敌人时把敌人一起删掉了，`EnemiesAlive` 与 `UnitHash` 因此和规则不符（r1：`g127` 期望 1 实得 0、`g129` 哈希不符）—— 改成「玩家掉一条命、敌人留下」；**B-2 会话**：`g90` 断言 `ProbeRow` 却没在那块盘面上探过格子（实得 -1）；**B-3 会话**：自动时钟采样的钉板**已经分出胜负**——r2 把炸弹钉在砖块格上（`PlaceBomb` 永远到不了的状态，爆炸把炸弹脚下那块砖也炸了 → 直接通关），r3 把引信定得太短（两次断言调用的时间里就烧完了）→ 采样看到的是冻住的盘面。改成「炸弹钉在**地板**格、引信 24，按**实测**时钟速率定尺」，r4 的采样里 `BombList` 17 个不同值、第 16 帧同时 `BombsActive` 1→0、`Detonations` 0→1、`BricksRemaining` 3→1、`GridHash` 变、`LastBlastCount` 0→7） | `runs\bomberman\bomb-task101-r4`（首轮 `r1`，中间 `r2`/`r3`） | 第 13 个游戏。13×9 的经典场地（硬墙 / 地板 / 10 块可炸砖 / 2 个敌人 / 3 条命）、网格移动、放炸弹与固定引信、**爆炸向四方扩散且被硬墙挡住、被第一块砖吃下并停住**、**连锁引爆**、敌人确定性追击、被抓与掉命重生、胜负判定。**像素差 45/233 非零**（编辑器 1/14、游戏 44/219），`user://` 六帧逐对 **7541 / 176025 / 168478 / 74786 / 114995 px**，六个 sha **6/6 互不相同**；独立复算（`pixel_recompute.py` + `frames_recompute.py` + `recompute_readbacks.py`）**0 处不符**。断言 **143 PASS + 1 条声明的边界失败**（ERROR）＋ **2 条屏幕文本 PASS** ＋ **2 条场景断言 PASS** = **147 PASS**。**Python 第二实现**（`make_session_bomberman.py` 的 `BSim`）独立计算并把结果作为断言字面量的有：五次爆炸的**逐格坐标序列**（`LastBlast`）、`LastBlastCount`、炸后 `GridHash`、敌人追击 3 步与 4 步后的 `EnemyList` 与 `UnitHash`、被抓后的玩家位与 `UnitHash`、`BombList` 引信。规则逐条钉住：撞墙 / 撞砖 / 走上活炸弹三种走法全被拒（`reason=wall` / `brick` / `bomb`）且 `Moves` 不动；同一格放第二颗炸弹被拒（`reason=bomb_already_here`）；引信 3→2→1→**引爆**（`StepFuse(2)` 后 `BombList=3,1,1`、`Detonations=0`；再 `StepFuse(1)` → `LastBlast=3,1\|2,1\|1,1\|4,1\|5,1\|3,2`、1 块砖被炸、`Score=10`）；走廊钉板证明**墙停、第一块砖吃下并停住**（`LastBlast=1,3\|2,3\|1,2\|1,1\|1,4`，3 块砖 2 块被炸）；玩家被自己炸到 → `Exploded=true`、`Lives` 3→2、`Respawn` 回出生格；**连锁**（两颗炸弹，一颗 1 引信一颗 3 引信）→ `StepFuse(1)` 后两颗都没了、`Detonations=1`、`LastBlast` 是两次爆炸的并集 8 格；敌人**确定性追击**（`StepEnemies(3)` → `4,1\|7,8`、`StepEnemies(1)` → `3,1\|7,7`，玩家一步没动）；走进敌人 → `DeadByEnemy=true`、`Exploded=false`、`Lives` 3→2、重生、**敌人仍在**（B-1 的修法）；最后一条命被抓 → `GameOver=true`、`Won=false`、再动被拒（`reason=game_over`）；**一次爆炸通关**（`LastBlast=4,6\|3,6\|5,6\|6,6\|4,5\|4,4\|4,7\|4,8`：北面炸掉最后一块砖、南面把最后一个敌人炸死）→ `Won=true`、`Score=110`、`Lives=3`、`Exploded=false`。与帧率无关的增量 `StepTick(2)` → `LastHookSteps=2`、`BombList=4,4,22`，时钟跑过 30 帧后仍是 2，而 `LastAutoSteps` 归 0。多帧采样：冻结基线 12 帧（`GridHash`/`BricksRemaining`/`PlayerRow` 各 1 个值，`Elapsed`/`Ticks` 12 个不同值）对自动时钟 30 帧（**`BombList` 17 个不同值 `4,4,16`→`''`**，第 16 帧同时 `BombsActive` 1→0、`Detonations` 0→1、`BricksRemaining` 3→1、`GridHash` 变、`LastBlastCount` 0→7，`AutoTicks` 29 个、`Elapsed`/`Ticks` 各 30 个）。`e06` 同名批量被 `-32000` 拒绝（3 条 `conflicts`），`e05`/`e09` 的 sha `05672aed…`（844 B）**逐字节相同**；`project_build_csharp` exit 0、`invalid_count=0`；两次 `running_game_get_scene_tree` 共 127/128 个节点名 **0 个 `@` 开头**；声明的 `bomb_right` / `bomb_place` 动作各按按下沿只做一次（`InputMoves=1`、`InputBombs=1`） |
| 14 | Platformer | C# | 228（编辑器 14 / 游戏 214） | **228/228（100%）** | 编辑器：`failed=1`（**声明的同名拒绝**）、`ok_effect_observed=1`、`ok_file_effect_observed=6`、`ok_no_effect_observed=6`；游戏：`failed=1`（**声明的边界调用**，`-32001`）、`ok_effect_observed=32`、`ok_file_effect_observed=147`、`ok_no_effect_observed=34` | **0 / 2**（**PL-1 载荷**：世界左/右/顶边用「格子相对」公式解算，而 C# 除法向零截断，越过 x=0 两像素的盒子被推到 x=20 而不是 x=0（`g48` 期望 0 实得 20）；**PL-2 载荷**：`Jump()` 没有清 `OnGround`（`g61` 期望 False 实得 True）。两条都由 Python 第二实现照出来、修好并重跑 r2） | `runs\platformer\plat-task102-r2`（首轮 `runs\platformer\plat-task102-r1`） | 第 14 个游戏。40×30 的 20 px 格子课程、**整数运动学**（`x+=vx` → 解横 → `vy+=1`（≤16）→ `y+=vy` → 解纵）、左右移动 / 重力 / 落地 / **可选二段跳** / 平台碰撞 / 收集物计分 / 掉坑与终点判定。**像素差 40/228 非零**（编辑器 1/14、游戏 39/214），`user://` 七帧逐对 **631 / 22530 / 24437 / 2445 / 24178 / 4349 px**，七个 sha **7/7 互不相同**；独立复算（`pixel_recompute.py` + `frames_recompute.py` + `recompute_readbacks.py`）**0 处不符**。断言 **139 PASS + 1 条声明的边界失败**（`-32001`）＋ **2 条屏幕文本 PASS** ＋ **2 条场景断言 PASS** = **143 PASS**。**Python 第二实现**（`recovery\work\task102\make_session_platformer.py` 的 `PSim`）独立算出并作为断言字面量的有：`MapHash`（由**打印出来的 ASCII 地图**重推：实心 1 / 终点 5 / 收集物 3 / 空 2，32 位 multiply-31 链）、`StateHash`、出生落地的 `PlayerY`/`Landings`、撞左墙后的 `PlayerX=0`、**逐帧抛物线**（`vy=-12` → 顶点 `y=478` 连续两帧 → 第 23 帧 `y=544` 但**仍在空中** → 第 24 帧落地并清零 `VelY`）、二段跳三条分支（地面跳 / 空中跳 / 第三次被拒）、收集物三拍（1 颗 10 分、2 颗 20 分、再走不重复计数）、终点胜利、掉坑两拍（第 10 帧 `y=599` 未掉、第 11 帧掉坑回出生点、最后一条命 → `GameOver`）。与帧率无关的增量 `LastHookSteps`（`StepFrames(3)`→3）在时钟跑过 30 帧后仍是 3，而 `LastAutoSteps` 归 0；时钟用浮点累加器 `_autoAccum += delta*60`，`Elapsed` 是 `+= delta` 的浮点秒表；`Ticks` 只由 `_Process` 写、`Frames` 只由固定帧写（一个属性一个写者）。多帧采样：冻结基线 12 帧（`MapHash`/`GemsRemaining`/`PlayerX`/`PlayerY`/`OnGround` 各 1 个值，`Elapsed`/`Ticks` 各 12 个不同值）对自动疾跑 30 帧（`PlayerX` **29 个不同值 140→252**、`Landings` 29 个、`AutoTicks` 29 个、`Elapsed`/`Ticks` 各 30 个）。`e06` 同名批量被 `-32000` 拒绝（3 条 `conflicts`），`e05`/`e09` 的 sha `0dd8bf57…`（834 B）**逐字节相同**；`project_build_csharp` exit 0（4761 ms）、`invalid_count=0`；树里 114/115 个节点名 **0 个 `@` 开头**；声明的 `plat_right` / `plat_jump` 动作按按下沿各只触发一次 |
| 15 | Match-3 | C# | 145（编辑器 14 / 游戏 131） | **145/145（100%）** | 编辑器：`failed=1`（**声明的同名拒绝**）、`ok_effect_observed=1`、`ok_file_effect_observed=6`、`ok_no_effect_observed=6`；游戏：`failed=1`（**声明的边界调用**，`-32001`）、`ok_effect_observed=17`、`ok_file_effect_observed=89`、`ok_no_effect_observed=24` | **1 / 4**（工具 **X-1**（只记录、未改模块）：`running_game_execute_gdscript` 的脚本**运行期报错**时工具回 `ok` + `result: null`，诊断只落在引擎 stderr 里；**M3-1 会话**：默认棋盘的 `ProbeValue` 是**猜**的（`g11` 期望 5 实得 1），改成用 Python 复算 `BuildBoard()` 的 LCG + 消稳循环并断言整盘 / 哈希 / Seed；**M3-2 会话**：三种非法交换的期望计数各自建在**新副本**上（1/1/1），而会话在同一块盘上累计（1/2/3）；**M3-3 会话**：正控 overlay 的 GDScript 写成了 C# 的 `addChild`；**M3-4 会话 / 测试设计**：自动时钟采样的钉板只**一个合法交换**，时钟在第一个采样帧之前就把它吃掉，30 帧采样全程看着**冻住的盘面**（`AutoTicks` 4→33 而 `Moves`/`Score`/`BoardHash`/`Refills` 一动不动）而断言照样全 PASS —— 四周都修好并重跑 r3） | `runs\match3\m3-task102-r3`（首轮 `r1`，中间 `r2`） | 第 15 个游戏。8×8 六色、网格交换、三连检测与消除、下落补充、**连锁得分**（第 n 链 ×n）、非法交换拒绝（盘面逐字节不变）。**像素差 22/145 非零**（编辑器 1/14、游戏 21/131），`user://` 七帧逐对 **140015 / 17813 / 24265 / 6892 / 132911 / 135425 px**，七个 sha **7/7 互不相同**；独立复算 （`pixel_recompute.py` + `frames_recompute.py` + `recompute_readbacks.py`）**0 处不符**。断言 **85 PASS + 1 条声明的边界失败**（`-32001`）＋ **2 条屏幕文本 PASS** ＋ **1 条场景断言 PASS** = **88 PASS**。**Python 第二实现**（`recovery\work\task102\make_session_match3.py` 的 `MSim`）独立算出并作为断言字面量的有：默认棋盘（同一条 LCG `seed=(seed*1103515245+12345) mod 2^31`、`(seed>>16)%6`、行优先填充 + 消稳循环）与它的 `BoardHash`/`Seed`、安静棋盘（**没有任何合法交换**）与 `AutoStep(3)` 的 `LastHookSteps=0`、指定交换后的**整盘 / 哈希 / Seed / Refills / 连锁长度 / 消除数 / 得分**、`AutoStep(1)` 选中的**行优先第一个合法交换**、两波连锁的整盘与 90 分、胜利（490→520 越过 500 线）与失败（`move_limit=1`）。规则逐条钉住：非法交换被拒且 `Board`/`BoardHash` 一字不变；非相邻与越界各按名字拒绝；连锁 `LastChain=2`、`LastCleared=6`、`Score=90`；胜利 `Won`/`GameOver`=true；再交换 `reason=game_over`。与帧率无关的增量 `LastHookSteps`；时钟浮点累加器；**`BoardHash neq H0` 把「盘面冻住」变成一条会 FAIL 的断言**（M3-4 的教训写进断言本身）。多帧采样：冻结基线 12 帧对自动对局 30 帧（`BoardHash` **26 个不同值**、`Moves` 3→32、`Score` 150→1270、`TotalCleared` 12→112、`Refills` 12→112、`Elapsed`/`Ticks` 各 30 个）。`e06` 同名批量被 `-32000` 拒绝（3 条 `conflicts`），`e05`/`e09` 的 sha `7772574a…`（842 B）**逐字节相同**；`project_build_csharp` exit 0（3725 ms）、`invalid_count=0`；树里 68/69 个节点名 **0 个 `@` 开头** |
| 16 | Tower Defense | C# | 145（编辑器 14 / 游戏 131） | **145/145（100%）** | 编辑器：`failed=1`（**声明的同名拒绝**，D-3）、`ok_effect_observed=1`、`ok_file_effect_observed=4`、`ok_no_effect_observed=8`；游戏：`failed=1`（**声明的边界调用**，`-32001`）、`ok_effect_observed=26`、`ok_file_effect_observed=78`、`ok_no_effect_observed=26` | **0 / 1**（**TD-1 会话**：全程对局那一段**漏了 `ForceTestState`** —— 三座塔建在上一段钉住的 `gold=0` 状态上、全部被 `no_gold` 拒绝，`StepFrames(4000)` 于是在无塔的场地上让 5 个敌人漏到终点、5 条命耗尽（`g53` 期望 3 实得 0、`g55` 期望 true 实得 false 等 **11 条同时 FAIL**）；另外**取证工具**自身 1 条（`R-1`，见下），**不算模块缺陷**） | `runs\towerdefense\td-task103-r3`（首轮 `-r1`，中间 `-r2` 未从模板重开） | 第 16 个游戏。16×12 的 50 px 格点、**101 格无分支蛇形走廊**（路径由「从 S 出发、按右/下/左/上取第一个不是来路的路径格」的**确定性走法**从 ASCII 地图导出，Python 用同一走法重算 `PathHash`）、**整数行进**（每个敌人 `accum++`，攒满 `speed` 才进一格）、放塔（`-32000` 之外还有 `not_buildable`/`occupied`/`no_gold`/`out_of_bounds` 四种具名拒绝）、**切比雪夫射程 3 + 冷却 3 的塔**（取射程内**路径下标最大**的敌人）、三波（4/5/6 个，血 30/45/60）、生命与胜负。**像素差 31/145 非零**（编辑器 1/14、游戏 30/131），`user://` 五帧逐对 **185084 / 8356 / 3376 / 8133 px**、五个 sha **5/5 互不相同**；独立复算（`task102\pixel_recompute.py` 逐调用对 + `task102\frames_recompute.py` 保存帧 + 本轮 `recompute_readbacks.py`）**0 处不符**。断言 **77 PASS + 1 条声明的边界失败**（`-32001`）= 77 通过 / 0 失败。**Python 第二实现**（`make_session_towerdefense.py` 的 `TSim`）独立算出并作为断言字面量的有：`MapHash=26299736`（由打印出来的 ASCII 重推）、`PathHash=-577587427` / `PathLength=101`（**重新走一遍**打印出来的地图）、逐步损伤后的 `EnemyList`、击杀后的 `Score`/`Gold`、漏掉后 `Wave` 与 `WaveLeftToSpawn` 的推进、以及**一整局**（三座塔、306 步、15 杀、0 漏、剩 5 条命、150 分、Wave=3）的每一步结果。与帧率无关的增量 `LastHookSteps`（`StepFrames(3)`→3）在十二帧之后仍是 3，而 `LastAutoSteps` 归 0；时钟是浮点累加器 `_autoAccum += delta*AutoClock`，`Elapsed` 是每帧 `+= delta` 的浮点秒表。多帧采样：冻结基线 12 帧（`Steps`/`EnemiesAlive`/`Gold`/`Lives`/`Won` 各只有 1 个值，`Elapsed`/`Ticks` 各 12 个不同值）对自动时钟 30 帧，并带**会 FAIL 的硬断言**（`Steps gt 0`、`EnemiesSpawned gt 0`、`AutoTicks gte 1` —— M3-4 的教训写进断言本身）。`e06` 同名批量被 `-32000` 拒绝（3 条 `conflicts`），`e05`/`e09` 的 sha `41de249a…`（860 B）**逐字节相同**；`project_build_csharp` exit 0（3796 ms）、`invalid_count=0`、`editor_get_errors count=0`；树里 279 个节点名 **0 个 `@` 开头**；声明的 `td_auto_step` 动作真的让 `Steps` 前进（`InputSteps=1`） |
| 17 | Missile Command | C# | 127（编辑器 14 / 游戏 113） | **127/127（100%）** | 编辑器：`failed=1`（**声明的同名拒绝**，D-3）、`ok_effect_observed=1`、`ok_file_effect_observed=4`、`ok_no_effect_observed=8`；游戏：`failed=1`（**声明的边界调用**，`-32001`）、`ok_effect_observed=17`、`ok_file_effect_observed=74`、`ok_no_effect_observed=21` | **0 / 3**（**MC-1 载荷**：`PosAt` 是实例方法却被 `static AddMissiles` 调用 → `CS0120` → **C# 编译失败、脚本没挂上**，游戏退化成裸 `Node2D`；**MC-2 会话**：三条 `ProbeState` 断言写在探针循环**之后**，读到的是**最后**那次探针的状态（`g18b` 期望 `city` 实得 `ground`、`g19b` 期望 `battery` 实得 `ground`）；**TD-2 会话/证据**：TD 的 r2 **没有从模板重新实例化**，工程里已有三个静态节点 → 编辑器相首次同名批量被拒、像素列变 0/14。三条都已修并重跑） | `runs\missilecommand\mc-task103-r3`（首轮 `-r1`，`-r2` 已修 `PosAt` 但会话仍有 MC-2） | 第 17 个游戏。800×600 场地、**6 座城市 + 3 个炮台（每台 10 发、每波补满）**、LCG 生成来袭弹（`seed=(seed*1103515245+12345) mod 2^31`，`x0=20+((seed>>16)%760)`、目标 6 城或地面）、**整数 floor 插值轨迹**（`x0 + DivFloor((tx-x0)*k, dur)`，C# 侧把 floor 显式写出来以便与 Python 的 `//` 逐位一致）、拦截弹从 x 最近的**有弹**炮台发射、爆炸半径 34 / 存在 8 步、**爆炸按下标顺序清掉半径内的来袭弹**、来袭弹落地按其目标点 28 px 摧毁城市、波次与得分（25/杀、每存活城市 100）。**像素差 21/127 非零**（编辑器 1/14、游戏 20/113），`user://` 五帧逐对 **15823 / 13578 / 4370 / 346 px**、五个 sha **5/5 互不相同**；独立复算（`task102\pixel_recompute.py` + `task102\frames_recompute.py` + 本轮 `recompute_readbacks.py`）**0 处不符**。断言 **73 PASS + 1 条声明的边界失败**（`-32001`）= 73 通过 / 0 失败。**Python 第二实现**（`make_session_missilecommand.py` 的 `MSim`）独立算出并作为断言字面量的有：初始 `CityList`/`AmmoList`/`CityHash=29583456`/`WorldHash=852442047`、定盘天幕逐步的 `IncomingList` 与 `ExplosionList`、**一次爆炸的覆盖判定**（半径内的被打掉、半径外的活下来，`Destroyed`/`Score` 同步）、**带提前量的拦截**（在 Python 里把「拦截弹到达所需步数」与「来袭弹走到该点所需步数」迭代到不动点，得到 `InterceptorList=400,586,312,542,0,8,400,586`、8 步后爆炸点与来袭弹位置**逐位相同**→ 命中、`Leaked=0`、随后该波清算 `Wave` 推进并补满弹药）、一城被毁的 `CityList=1,1,0,1,1,1`、六城尽失的败局、以及**末波清空即胜**（`maxwave=1`，`Score=500`、`Won`/`GameOver`=true）。与帧率无关的增量 `LastHookSteps` 在十二帧之后仍是 3，而 `LastAutoSteps` 归 0；时钟是浮点累加器；`Elapsed` 是浮点秒表。多帧采样：冻结基线 12 帧对自动时钟 30 帧，带**会 FAIL 的硬断言**（`Steps gt 0`、`Spawned gt 0`、`AutoTicks gte 1`）。`e06` 同名批量被 `-32000` 拒绝，`project_build_csharp` exit 0（3815 ms）、`invalid_count=0`、`editor_get_errors count=0`；树里 270 个节点名 **0 个 `@` 开头**；声明的 `mc_auto_fire` 动作真的发了一发（`InputShots=1`、`Fired=1`、`Ammo` 29） |
| 18 | R-Type | C# | 223（编辑器 14 / 游戏 209） | **223/223（100%）**（编辑器 14/14、游戏 209/209） | 编辑器：`failed=1`（**声明的同名拒绝**，D-3）、`ok_effect_observed=1`、`ok_file_effect_observed=4`、`ok_no_effect_observed=8`；游戏：`failed=1`（**声明的边界调用**，`-32001`）、`ok_effect_observed=83`、`ok_file_effect_observed=101`、`ok_no_effect_observed=24` | **0 / 1**（**RT-1 会话**：r1 的 `g114-assert-rejected` 期望 `RejectedMoves=0` 实得 **1** —— 游戏结束后那次 `MovePlayer` 确实被拒并计数，而生成器只发了调用、没有让自己那份 Python 第二实现跟着走同一步（与 K-1/TD-1 同一类：期望值必须来自它所断言的那一刻）；补上 `lose.fire()` / `lose.move(8, 0)`，从模板重新实例化后重跑 r2） | `runs\rtype\rt-task104-r2`（首轮 `runs\rtype\rt-task104-r1`） | 第 18 个游戏。800×600 场地、**整数运动学**（船 8 px/次调用，玩家子弹 16、敌机 3、敌弹 6 px/步），**编队入场**（第 k 个出生点 = `(830 + (k/3)*40, 120 + (k%3)*70)`，一边入场一边整体左移）、三波 4/5/6 个敌人、敌机 45 步固定冷却的射击、子弹取**出生顺序里第一个**重叠的敌机、越界敌机扣命、生命与得分。**像素差 87/223 非零**（编辑器 1/14、游戏 86/209），`user://` 四帧逐对 **2069 / 7095 / 7547 px**、四个 sha **4/4 互不相同**；独立复算（`task104\pixel_recompute.py` 逐调用对 + `task104\frames_recompute.py` 保存帧 + 本轮 `recompute_readbacks.py`）**0 处不符**。断言 **101 PASS / 0 FAIL** = 99 条带属性的 node-state ＋ **1 条屏幕文本 PASS**（`WAVE CLEARED`）＋ 1 条 `run_test_scenario` 自带的断言，**另有 1 条声明的边界失败**（`-32001`，不计入 PASS）。**Python 第二实现**（`recovery\work\task104\make_session_rtype.py` 的 `RSim`）独立算出并作为断言字面量的有：编队逐帧的 `EnemyList`、子弹与敌弹的 `BulletList`/`EnemyBulletList`、每一次碰撞后的 `StateHash`、以及**一整局**（三波 15 个敌人、6 杀 9 漏、剩 49 命、600 分、960 步、Wave=3）的每一步结果。规则逐条钉住：四个方向的移动与四处边界钳位（含两条会被记进 `RejectedMoves` 的“原地不动”拒绝）、子弹出右边界消失（104+44×16 ≥ 800）、一次击杀 = 100 分、敌机 45 步冷却后开火（枪口 = `(x-8, y+6)`）、中弹扣命、敌机穿越整场扣命、最后一命耗尽即败（钩子停在 1/3 步）、三波清空即胜。与帧率无关的增量 `LastHookSteps`（`StepFrames(3)`→3）在时钟跑过 12 帧之后仍是 3，而 `LastAutoSteps` 归 0；时钟是浮点累加器 `_autoAccum += delta*AutoClock`，`Elapsed` 是每帧 `+= delta` 的浮点秒表。多帧采样：冻结基线 12 帧（`Steps`/`EnemiesAlive`/`BulletsActive`/`StateHash` 各 1 个值，`Elapsed`/`Ticks` 各 12 个不同值）对自动时钟 30 帧，并带三条**会 FAIL 的硬断言**（`Steps gt 0`、`EnemiesSpawned gt 0`、`StateHash neq H0` —— M3-4 的教训写进断言本身）。`e06` 同名批量被 `-32000` 拒绝（`conflicts` 3 条：`Background`/`Hud`/`Status`），`e05`/`e09` 的 sha `0494b8a0…`（850 B）**逐字节相同**；`project_build_csharp` exit 0（4266 ms）、`editor_get_errors count=0`；三次场景树读取（编辑器相 1 + 游戏相 2）共 **214 个节点名 0 个 `@` 开头**；声明的 `rt_fire` 动作**按按下沿**只发一发（`InputShots=1`） |
| 19 | Puzzle Bobble | C# | 157（编辑器 14 / 游戏 143） | **157/157（100%）**（编辑器 14/14、游戏 143/143） | 编辑器：`failed=1`（**声明的同名拒绝**，D-3）、`ok_effect_observed=1`、`ok_file_effect_observed=4`、`ok_no_effect_observed=8`；游戏：`failed=1`（**声明的边界调用**，`-32001`）、`ok_effect_observed=27`、`ok_file_effect_observed=91`、`ok_no_effect_observed=24` | **0 / 0**（首轮一次通过，没有发现工具缺陷或游戏/驱动缺陷） | `runs\puzzlebobble\pb-task104-r1` | 第 19 个游戏。8×12 的方形泡泡网格（40 px/格）、**六色**、底部中央的发射器、**五种整数发射方向** `(±2,-1) (±1,-1) (0,-1)`（一格一步，两侧墙反弹）、**同色四连通三连消除**、**悬空掉落**（与顶行不连通的泡泡落下并计分）、**连锁**（掉落按“代”推进：只有正下方为空的浮空泡泡先落，一层一代，每一代提升链倍率）、**失败线**（结算后任何停在 row ≥ 10 的泡泡判负）、清空棋盘判胜。**像素差 29/157 非零**（编辑器 1/14、游戏 28/143），`user://` 四帧逐对 **53444 / 18251 / 2929 px**、四个 sha **4/4 互不相同**；独立复算（`pixel_recompute.py` + `frames_recompute.py` + `recompute_readbacks.py`）**0 处不符**。断言 **87 PASS / 0 FAIL** = 85 条带属性的 node-state ＋ **1 条屏幕文本 PASS**（`BOARD CLEARED`）＋ 1 条场景断言，**另有 1 条声明的边界失败**（`-32001`）。**Python 第二实现**（`make_session_puzzlebobble.py` 的 `BSim`）独立算出并作为断言字面量的有：**初始棋盘**（同一条 LCG `seed=(seed*1103515245+12345) mod 2^31`、`(seed>>16)%6`、行优先填 4 行 + 同一套“去掉三连”的稳定循环）、它的 `Board`/`BoardHash`/`BubblesInUse`、五种方向的飞行与**第 3 步的墙面反弹**、一发命中的**落点**与**消除/掉落/连锁/得分**（三连：`attach=(4,3)`、chain 2、cleared 3、dropped 1、70 分；两格浮空塔：`attach=(4,6)`、**chain 4**、cleared 3、dropped 3、**210 分**）、失败线那一发的落点与判负、以及清空棋盘的那一发（30 分、`Won`）。规则逐条钉住：`Probe` 的 outside/empty/occupied/shooter/projectile 五种命名与颜色值、`Aim` 的五档与两端钳位（同向重设被拒）、同色重设后 `ShooterColor` 前进到 `NextColor`、每发之后 `Shots` 递增、结束后 `Shoot`/`Aim` 被拒。与帧率无关的增量 `LastHookSteps`（`StepFrames(3)`→3）在时钟跑过 12 帧之后仍是 3，而 `LastAutoSteps` 归 0；时钟是浮点累加器。多帧采样：冻结基线 12 帧（`Steps`/`BubblesInUse`/`BoardHash` 各 1 个值，`Elapsed`/`Ticks` 各 12 个不同值）对自动时钟 30 帧（**先发射再开钟**，否则棋盘无事可做），带三条**会 FAIL 的硬断言**（`Steps gt 0`、`BoardHash neq H0`、`AutoTicks gte 1`）。`e06` 同名批量被 `-32000` 拒绝（`conflicts` 3 条），`e05`/`e09` 的 sha `3723211c…`（868 B）**逐字节相同**；`project_build_csharp` exit 0（2489 ms）、`e13` 回 `invalid_count=0`（本轮它是 `valid=true`）、`editor_get_errors count=0`；三次场景树读取共 **214 个节点名 0 个 `@` 开头**；声明的 `pb_shoot` 动作按按下沿只发一发（`InputShots=1`） |
| 20 | Lunar Lander | C# | 230（编辑器 14 / 游戏 216） | **230/230（100%）**（编辑器 14/14、游戏 216/216） | 编辑器：`failed=1`（**声明的同名拒绝**，D-3）、`ok_effect_observed=1`、`ok_file_effect_observed=4`、`ok_no_effect_observed=8`；游戏：`failed=1`（**声明的边界调用**，`-32001`）、`ok_effect_observed=39`、`ok_file_effect_observed=154`、`ok_no_effect_observed=22` | **0 / 0**（首轮一次通过，没有发现工具缺陷或游戏/驱动缺陷） | `runs\lunarlander\ll-task104-r1` | 第 20 个游戏，也是 D138「至少 20 款」的收口款。800×600 月面、地面线 y=560、**三个着陆台**（120–200 / 360–440 / 600–680，倍率 1/2/1）；**十二档整数姿态**（30° 一档）与**整数推力表**（正立 (0,-4)）、重力每步 +1、每次点火消耗 1 燃料、**整数积分** `vy += 重力; x += vx; y += vy`；着陆判定 = 在着陆台上 且 `|Vx| ≤ 2` 且 `|Vy| ≤ 6` 且距正立 ≤ 1 档，存活则得分 = **剩余燃料 × 台倍率**，否则坠毁；飞出场地也是坠毁。**像素差 41/230 非零**（编辑器 1/14、游戏 40/216），`user://` 四帧逐对 **6798 / 1117 / 6885 px**、四个 sha **4/4 互不相同**；独立复算（`pixel_recompute.py` + `frames_recompute.py` + `recompute_readbacks.py`）**0 处不符**。断言 **150 PASS / 0 FAIL** = 148 条带属性的 node-state ＋ **1 条屏幕文本 PASS**（`THE EAGLE HAS LANDED`）＋ 1 条场景断言，**另有 1 条声明的边界失败**（`-32001`）。**Python 第二实现**（`make_session_lunarlander.py` 的 `LSim`）独立算出并作为断言字面量的有：三座台与倍率、每一项容差、十二档推力表、以及**一条真实的整数下降轨迹** —— 生成器先在 Python 里**搜**出「自由落体到 y≥430 → 连续点火 8 步 → 滑行」的方案，再按搜出来的相位驱动载荷，逐相位断言 `Lx`/`Ly`/`Vx`/`Vy`/`Fuel`/`Steps`/`StateHash`/`LastHookSteps`（35 步、右脚在 554、`Vy=3`、剩 492 燃料、**台 1 → 984 分**）。**事后复算独立重放整条轨迹**：`recompute_readbacks.py` 只吃运行自己写的响应文件与 `call-index.txt` 的调用顺序，在**自己的**代码里重做「点火/重力/积分/触地」并逐检查点比对 —— **17 个检查点、0 处不符**。规则逐条钉住：`Thrust()` 的脉冲与 `SetThrust` 的持续点火分开、空箱点火被拒、**每一条容差的边界两侧**（`|Vy|` 6 存活 / 7 坠毁、`|Vx|` 4 坠毁、90° 坠毁、**330° 存活**证明容差是两侧的、错过所有着陆台坠毁、左右台各按自己倍率给分）、飞出场地即坠毁、结束后点火被拒。与帧率无关的增量 `LastHookSteps`（`StepFrames(3)`→3）在时钟跑过 12 帧之后仍是 3，而 `LastAutoSteps` 归 0；时钟是浮点累加器。多帧采样：冻结基线 12 帧（`Lx`/`Ly`/`Vx`/`Vy`/`Fuel`/`StateHash` 各 1 个值，`Elapsed`/`Ticks` 各 12 个不同值）对自动时钟 30 帧，带四条**会 FAIL 的硬断言**（`Steps gt 0`、`Ly gt 起始值`、`StateHash neq H0`、`AutoTicks gte 1`）。`e06` 同名批量被 `-32000` 拒绝（`conflicts` 3 条），`e05`/`e09` 的 sha `50ec3aba…`（844 B）**逐字节相同**；`project_build_csharp` exit 0（3782 ms）、`e13` 回 `invalid_count=0`、`editor_get_errors count=0`；三次场景树读取共 **136 个节点名 0 个 `@` 开头**；声明的 `ll_thrust` 动作按按下沿只点一次火（`InputThrusts=1`） |

---

## 缺陷登记（跨轮累计）

### 工具缺陷（`modules\mcp_server`）

| id | 层 | 现象（证据） | 根因 | 状态 |
|---|---|---|---|---|
| — | — | TASK-091..093 期间**没有发现新的工具缺陷**；TASK-092 的三条溯源缺口已在上一轮关闭 | — | — |
| **D-1** | 运行期 / 画面侧（**TASK-094 定位：机器画面管线；TASK-095 更正为「加载期画布项不再重录」；TASK-096 再定域：上面两条都不成立，真因是场景文件里的 `@ColorRect@*` 副本层 —— 见下表后的三节**） | 进程的视口回读**恒返回本进程渲染的第一帧**：TASK-093 现场 62/40（snake）、68/42（breakout）个 PNG 各 1 个 sha；`running_game_capture_frames` 12 帧同一 sha；`user://` 截图跨 8 秒同 sha `D5C3A72ABA6F525C`。**TASK-094 的最小反例**：把 `Background.color` 依次设成蓝→红→绿（同一调用内读回 `background_color=(0.0,1.0,0.0,1.0)`，确实变绿），三次 `running_game_capture_screenshot` 得到**三张逐字节相同、且都还是最初深色背景**的 PNG；`--mcp-capture=off`（进程里根本没有 capture engine）同样复现。**同一时刻**蛇的 `SnakeSeg00.position` 从 `(144,240)` 走到 `(384,240)`（240 px），回读指纹恒为 `558211402` | **机器画面管线**，不是模块：①同一份二进制字节、同一个 `tools\sessions\pong\session.json`，00:14:53 得 **10/29 非零**（`pong-task092`，16 个不同 sha），01:18:26 重放得 **0/29**（`task094-pong-ab`，1 个 sha）；②渲染器本身在动——加 100 个 `ColorRect` 后 `Performance.RENDER_TOTAL_OBJECTS_IN_FRAME` **57 → 157**、prims 114 → 314，`Engine.get_frames_drawn()` 以 ≈144/s 递增；③窗口未最小化（`IsIconic=False`、`window_get_mode()=0`），故 `Main::iteration` 确实调用 `RenderingServer::draw()`；④读的 RID 就是渲染目标当前纹理（`RenderingServer.viewport_get_texture(vp_rid)` 与缓存值同 RID、同字节）；⑤vulkan / opengl3 / d3d12 **三者同样冻结**；⑥`RenderingServer.force_sync()` + `force_draw(true, 0.0)` 无效；⑦GPU 无 TDR/掉卡（`nvidia-smi` 正常、System 日志 8 小时内无 `nvlddmkm`）。**TASK-093 那条复现脚本本身有陷阱**：它拍的是**已经死了的蛇**（`SNAKE_WALL ... ticks=19`，1.5 秒就撞墙），所以「两张同 sha」在那条脚本里本来就该出现；TASK-094 的最小反例改用不被游戏脚本写、且不依赖存活的对象 | **TASK-097 已结案：真因 D-3 已修（同名默认拒绝）、副本层已删、像素差列已回填真实数值 —— 见本表后的「D-1 结案与副本层清理存证（TASK-097）」。** TASK-096 再定域（见「D-1 再定域（TASK-096）」）：引擎无辜（同一批操作在两个引擎上都正常）、回读无辜、机器画面管线无辜；真因是三个老游戏的场景文件里被写进了整份节点副本，副本绘制在上层，屏幕上是**副本的初值**。三个场景当时仍带着副本（**TASK-097 已用 `editor_delete_node` 删除并复核，见「D-1 结案」节**）**。复现（TASK-095 的更强反例，两条一起看才有判别力）：`powershell -File tools\run_game_session.ps1 -Game snake -Session recovery\work\task095\sessions\loadednode\session.json -RunTag x -GamePort 9892 -SkipReport`；**TASK-096 的判别证据**：`recovery\work\task096\sessions\occ\session.json`（`runs\snake\task096-occ`，隐藏 `@ColorRect@20995` 后同一像素立刻跟着 `Background.color` 走）、探针工程 A/B（`recovery\work\task096\probe`，我方引擎与 stock 4.7.1 逐行相同，加载期 Background 改色立刻上屏）、第 4 个游戏 Tetris（场景干净 → 像素差 11/42 非零，`runs\tetris\tetris-task096-r2`）；TASK-094 当时的证据仍在盘上（`recovery\work\task094\diag_freshness.ps1` + `sessions\repro2\session.json`（`D1_VERDICT=PRESENT`）、`runs\snake\task094-probe3/4/5`、`runs\snake\task094-probe9`；A/B `runs\pong\pong-task092` vs `runs\pong\task094-pong-ab`），当时**已试无效的绕过**（opengl3 / d3d12 / `force_draw` / 进程外窗口抓取 `CopyFromScreen`、`PrintWindow`）在「画面本来是静止的副本层」这条真因下不再需要别的解释 | |
| **D-2** | 运行期 / 主循环健康度（**TASK-094 已修：测试判据对负载敏感**） | `accept_m1.ps1` 在 `task093` / `task093b` 两轮里失败（`5/22`）：输出头部 `WARNING: the pump never looked steady, running the cases anyway`，随后 `case1_GET_mcp_200 status=0`、`case2..11/15..20` 抛 `Wait` 异常；同一脚本在同一台机器、同一引擎字节上单独重跑（`task093c`，wall=50.7s）→ `22/22`、`GATE_EXIT=0` | **判据是吞吐而不是就绪**：`Wait-ForStablePump` 原来要求「相隔 1000 ms 的两次采样之间 `frame_count` 至少 +20，连续 3 次」——即**至少 20 fps**。有负载时主循环活着但慢于 20 fps，判据永不成立，函数耗尽 180 s 死线后打印 WARNING 继续跑，用例于是在尚未稳定的泵上执行 → `status=0` / `Wait` 异常。绑定与端口逻辑无辜（`case12/13/14`、`guard_user_port_9877` 在失败轮里也全 PASS） | **改**（`modules\mcp_server\scripts\accept_m1.ps1`）：判据改为「`frame_count` 连续 6 次严格递增，采样间隔 250 ms」＝**约 1.5 秒不间断推进，与帧率无关**（1 fps 也能满足），死线仍 180 s，未满足时仍照旧响亮报警。实测：**单跑 wall=50.8s → 22/22、`GATE_EXIT=0`**（`runs\gates\task094-alone\`）；**同机 8 个 CPU 烧机进程（16 逻辑核）并跑 wall=55.3s → 22/22、`GATE_EXIT=0`**（`runs\gates\task094-load2\`）；另有一次短重叠负载（`dotnet build`）wall=41.5s → 22/22（`runs\gates\task094-load\`）。三次都没有出现 WARNING 行 |
| **G-1** | 门跑器 / 参数（**已定位，TASK-099 已修**） | `run_gates.ps1` 的 `-VersionText` 默认值是 `4.8.dev.mono.custom_build.8604fcf9e`（TASK-090 的锚点），对当前 HEAD `cf554ef58` 判 `ANCHOR_STALE_COMPILED`（`diff_count=22 safe_count=3 red_count=19`）→ 门 9 FAIL | 参数默认值落后于引擎仓 HEAD；**不是模块回归** | TASK-093 用 `-VersionText 4.8.dev.mono.custom_build.cf554ef58` 重跑（`runs\gates\task093c\`）；TASK-094 沿用同一锚点（`runs\gates\task094\`）；TASK-096 同样用它（`runs\gates\task096\`）。**TASK-099 修在根上**：`-VersionText` 默认改为空，锚点默认取**磁盘上那个二进制自己的 `--version`**（`-Anchor` / `-VersionText` 仍可显式覆盖），并新增**纯文档预检**：committed diff 与工作树里都没有编译输入时直接判 `ANCHOR_STRUCTURAL_EQUIVALENT` + `SKIP_REBUILD`、打印非编译文件清单、不跑十道门（`-RunGates` 可强制）；有编译输入时照常跑门。实测两情形：纯文档提交（anchor `2385fe2fb` → HEAD `0fbd5ec4c`，diff 两份 `.md`）`exit 0` + `GATES_SKIPPED=1`（`runs\gates\task099-doconly\`）；工作树里放一个未跟踪 `.cpp` 时 `VERDICT=RUN_GATES` 且 **`g01`..`g10` 全部 `exit=0`**（`runs\gates\task099-compileinput\summary.txt`） |
| **D-3** | 编辑器 / 场景写入（**TASK-096 发现，根因明确，未修：属画布项缺陷，按 §C 口径先只记录**） | 把 `editor_open_scene` + `editor_add_nodes_batch` + `editor_save_scene` 这一套在一个**已经有这些名字的节点**的场景上再跑一遍，会得到**整份副本**：pong 5、breakout 18、snake 37 个自动名节点（`@ColorRect@20995`…、`@Label@21000`…），它们排在场景树最后、**绘制在最上层**。提交级证据：`projects\pong\scenes\main.tscn` 在 `df02ccb`（TASK-092 之前）**0** 个副本，在 `97167e4`（TASK-093）**5** 个；`runs\pong\pong-run1..run4` 的 `e20-scene-tree` 都没有副本，`runs\pong\pong-control-task093` 的**有**。**数字口径（TASK-098 复核时补注）**：这里的 5 / 18 / 37 是**只数 `@ColorRect@*`** 的结果（当时的现场照片就是那一类）；把 `@Label@*` 也算进来是 **8 / 20 / 37**（Pong 5+3、Breakout 18+2、Snake 37+0）。两个数都对，差别只在口径；`recovery\work\task098\copy_count_evidence.py` 从清理会话自己读回来的清理前场景原文重新数过（`@...@` 逐个列出），与 TASK-097 删掉的 8 / 20 / 37 一致 | `editor_add_nodes_batch` 对「同名节点已存在」既不拒绝也不报告，Godot 按既有规则把新节点自动改名（`@ColorRect@NNNN`）；`editor_save_scene` 随后把**两份**都写进 `.tscn`。TASK-093 的编辑器相被重跑过（pong 的 control 轮、breakout/snake 的 r2..r7），污染就是这样进去的 | **已修（TASK-097，两半都做）**。①**根因动作**：`editor_add_nodes_batch` 新增 `on_name_conflict`（默认 `"refuse"`），目标父节点下已有同名子节点（或本批内同父同名）时**整批拒绝、一个节点都不写**，回 `-32000` + `data.conflicts`（含 `node_path` 与 `existing_node_path`）+ `data.suggestion`；显式开关 `"rename"` 保留引擎改名并在 `renamed_count` / `renamed[]` / `created[i].name_conflict` 里说明。②`editor_save_scene` 侧：对**本模块批量添加产生的同名重复**给出 `duplicates` / `duplicates_count` / `note`，不再静默保存。③**三个场景的副本层已按最小动作删除**（用 `editor_delete_node` 逐个删，存证与复核见下），像素差列已回填。**最小同批复现修前/修后**：`runs\pong\d3-before`（旧二进制：第二次同名批量返回 `ok` 并造出 `@ColorRect@20956`，文件 sha `851ff76b…`(240 B) → `166e0221…`(388 B)，副本进了 `.tscn`）对 `runs\pong\d3-after-r2`（新二进制：同一步 `-32000`，文件 sha `8f7d1768…`(241 B) **前后一字未变**）。**真项目里的复核**：三款游戏与 Space Invaders 重放时，会话里那一次 `editor_add_nodes_batch` 全部被判 `-32000`，重放后的场景树**没有任何 `@Type@N` 自动名节点**。**D-1 的真因就是本条** |
| **X-1** | 运行期 / 错误信息（`running_game_execute_gdscript`） | `runs\match3\m3-task102-r1\g115-runtime-overlay.json` 回的是 `ok`（ledger 记 `ok_no_effect_observed`）+ `{"result": null, "result_type": "Nil"}`，**没有任何错误码或错误消息**；同一刻引擎 stderr 里躺着 `SCRIPT ERROR: Invalid call. Nonexistent function 'addChild' in base 'Node2D (Match3Game.cs)'.`（`runs\match3\m3-task102-r1\engine-game.stderr.txt`，270 B）。同一会话里同一段代码在 platformer 上（`add_child`，拼写正确）回 `"overlay added"`，所以这不是工具坏了，而是**脚本运行期报错不被回进工具自己的答复** | 未定域（未改模块）：错误由 GDScript 运行期抛出、只有引擎进程的 stderr 承接；`running_game_execute_gdscript` 把脚本的返回值原样回传，脚本没返回值就是 `null`。**根因未查**，按台账口径「根因不清楚的只记录、不猜改」，且改它要动 `modules\mcp_server` → 必须重建两变体 + 重跑十道门，本轮不做 | **已修（TASK-103，见「TASK-103 记录」第 1 条）。** 原状态与可复现配方：把 `tools\sessions\match3\session.json` 里 `g115-runtime-overlay` 的 `add_child` 改回 `addChild` 再跑一次，或直接对任一运行中的游戏端点发 `running_game_execute_gdscript` + `{"code": "var m = get_parent()\nreturn m.NoSuchMethod()"}`。**对证据链的实际影响**：本轮 M3-3 就是被这条**半掩**住的 —— 工具答复是 `ok`，把 `addChild` 改成静默无效果；真正把它抓出来的是**像素差 0** 与**场景树里没有那个节点**。也就是说：`execute_gdscript` 的 `ok` 不能单独当「脚本执行成功」读，必须配效果证据 |

### D-1 定域更正（TASK-095，2026-09-27）

TASK-094 写的根因「进程的视口回读**恒返回本进程渲染的第一帧**」**已被现场实验否证**。更正如下。

1. **不是回读通道坏了。** 同一次进程内、同一时刻，根视口的回读会跟着画面变：
   在根画布上**运行期新建**一个 `ColorRect C4` 并改色，`ROOT px(750,550)` 由**红 `(1,0,0,1)` 变黄 `(1,1,0,1)`**（`runs\snake\task095-discriminate` z02/z04）。
2. **也不是"离屏 SubViewport 不可用"。** 一个**自有** SubViewport 的回读完全新鲜：红→绿→蓝→黄四张不同画面，缓存 RID 与现场 `RenderingServer.viewport_get_texture` 两种路径答案一致（`runs\snake\task095-offscreen` o03/o05/o07/o10）。
3. **真正被冻结的是「加载期画布项」。** 判据（`runs\snake\task095-loadednode` p01–p07）：
   采样像素 `P1(10,580)` 只被 `Background` 覆盖。
   * 改**加载期**节点 `Background.color` → 品红：`P1` **一字未变**（仍 `(0.051,0.0902,0.0706)`），而属性读回是 `(1,0,1,1)`；
     对同一节点连做 `queue_redraw()` + `hide()` + `show()` + 重设 `size` + 改绿，`P1` **仍然一字未变**。
   * 用**运行期新建**、铺满全屏的 `ColorRect` 盖住同一像素：`P1` 立刻变黄。改它的色，`P1` 跟着变。
   → **加载期入树的 `CanvasItem` 不再重录绘制命令；运行期新建的项正常重录。** 与视口、与世界（共享/自有）、与渲染驱动、与 capture engine 都无关。
   snake 上场内容几乎全是加载期节点（`main.tscn` 里 `Background`、16 条 `GridLine`、**`SnakeSeg00..19`**、`Food`、`Status` 全是声明节点），所以"蛇走 240 px 画面不动"是**这条规律的必然结果**。
4. **把目标场景搬进自有 SubViewport 也不解决**（两条搬法都实测）：
   镜像 `world_2d`（`task095-mirror2`）与把 `current_scene` 搬进 `/root/CaptureHost`（`task095-rehost`，且 `world_shared=false`）**都仍然冻结**，且搬迁会把 `SceneTree.current_scene` 变成 `null`。
5. **A/B 时间戳更正**：不是 `00:14:47` vs `02:00`，而是 **`00:14:53`**（`runs\pong\pong-task092\trace-game.jsonl`）vs **`01:18:26`**（`runs\pong\task094-pong-ab\trace-game.jsonl`），相隔约 **1 小时 3 分**。同一二进制字节前后答案不同这个事实不受影响。
6. **TASK-094 的探针之所以"没跑起来"，不是 PowerShell 的限制**：`recovery\work\task094\sessions\probe10\session.json` 是**语法非法的 JSON**（每个 call 对象少一个 `}`，只闭合了 `arguments`），Python 与 PS 5.1 报的**位置几乎相同**（char 493/494）。
7. **桌面侧**：本会话是 session 1、console、Active、未锁屏、非 RDP 的真实桌面；但 **`nvidia-smi --query-gpu=display_active` = `Disabled`**（`display_attached=Yes`），两条 `Win32_DesktopMonitor` 与 GameViewer 虚拟显示器适配器都 off-line。**共存，未证明因果**；要判因果必须改变机器状态后重测（接上物理输出 / 暂停 GameViewer），本轮未做。
8. **本轮未改 `modules\mcp_server` 一个字节**，因此未重建、未跑门、未 push；理由见 `recovery\reports\TASK-095-REPORT.md` §C/§F1。

### D-1 再定域（TASK-096，2026-09-27）

TASK-095 写的「加载期入树的 `CanvasItem` 不再重录绘制命令」**也被现场实验否证**。真因见工具缺陷 **D-3**：场景文件里有整份节点副本，副本绘制在上层。三条判别证据：

1. **同一批操作、两个引擎、一个干净场景 → 全部正常。** 探针工程 `recovery\work\task096\probe`（一个加载期 `Background` + 一条网格线，加 TASK-095 `loadednode` 会话的同一段 p01–p10 序列）在**我方引擎**（`4.8-dev custom_build`，带 `--mcp-*`）与 **stock Godot 4.7.1 mono 官方构建**（`D:\Program Files\Godot_v4.7.1-stable_mono_win64\...`）上**逐行相同**：`p03` 的 `P1(10,580)` 由底色变成品红、`p07` 变成绿。→ 引擎、回读通道、capture engine 全部无辜（证据：`runs\ours-8b9dd9a72b`、`runs\ours-mcp-flags`、`runs\stock-471`）。
2. **snake 上「冻的」那个像素本来就被副本占着。** `runs\snake\task096-occ` 的 `o03` 直接列出覆盖 `P1(10,580)` 的节点（按绘制顺序）：`0:Background`、`36:Status`、`37:@ColorRect@20995`（最后一个不透明、在最上层）。把它 `visible=false` 之后，`o06` 的同一像素立刻变成 `(0.949,0.0353,0.6863)` = 品红叠上 `Status` 的 0.35 红（`0.85*0.35+1*0.65=0.9475`、`0.1*0.35=0.035`、`1*0.65+0.1*0.35=0.685`，逐位吻合）；`o10` 把 `SnakeSeg00.position` 移到 `(300,300)`，该像素随即变成蛇身绿（同法可复算）。→ **画面没冻、属性没冻，冻的是采样点被别人占着**。
3. **一个新游戏、同一个引擎、同一套工具 → 像素证据当场回得来。** 第 4 个游戏 Tetris 的场景是干净的（`r06-scene-still-clean` 里没有自动名副本），`runs\tetris\tetris-task096-r2` 的像素差 **11/42 非零**、`user://` 四张截图两两不同（3174 / 4232 / 8503 px）。→ 只要场景没有副本层，像素差就可得。

* **TASK-096 的更正**：`@ColorRect@*` 副本的存在**不代表**「加载期项不重录」——探针工程里会正常改色的 `Background` 正是加载期节点；副本一旦让开，加载期项的改色/`queue_redraw()`/`hide()+show()`/改 `size` 都会上屏。
* TASK-095 的判别实验（运行期新建项活、改加载期项不动）**仍然成立**，但解释换了：**动的那个是加在最上层的新项，不动的那个是被副本挡住的旧项**——与「加载期 / 运行期」这条分类无关。
* TASK-095 §C 的三个前置选项因此**作废**：机器状态无需改动，影子渲染无需立项。只剩一件事：把副本从三个场景里删掉（属画布项缺陷，本轮按 §C 口径只记录，等决策）。
* 像素差列因此**不是**「永远不可得」：它只在那三个场景被清理之前不可得。列上写「**不可得（D-1）**」而不是 `0`，读法与替代证据链见 `modules\mcp_server\docs\reports\MCP-TRACEABILITY.md` §7 与 `tools\game_report.py`。
* **（TASK-097 结案）**：三个场景的副本层已删除，列上现在写的是**真实数值**（Pong 14/74、Breakout 14/89、Snake 13/102，独立复算一致）——见下一节「D-1 结案与副本层清理存证（TASK-097）」。本段以上保留为**当时的定域记录**，「不可得」只对清理之前的旧运行成立。

### D-1 结案与副本层清理存证（TASK-097，2026-09-27）

TASK-096 的三条判别证据把 D-1 定域到 D-3（场景文件里的整份副本层）。TASK-097 做了两件事，**D-1 结案**：

1. **根因动作已落进模块**（见工具缺陷 D-3 的「已修」格）：同名不再是引擎改名，而是默认拒绝；显式 `"rename"` 才会产生副本，且 `editor_save_scene` 会报告它。三款老游戏与 Space Invaders 的重放里，那一次 `editor_add_nodes_batch` 全部被拒（`-32000`），场景树里**没有任何自动名节点**回来。
2. **三个场景的副本层已用 MCP 工具删除并复核**（每个游戏一次会话：`editor_open_scene` → 读树/读文件/属性采样 → `editor_delete_node` × N → 读树 → `editor_save_scene` → 读文件/属性采样 → **原样重放该游戏原来的整份会话**）：

| 游戏 | 副本（ColorRect / Label） | 场景 sha256 清理前 → 后 | 具名节点块逐字节相同 | 属性采样 | 重放里的同名批量 | 像素差列 |
|---|---|---|---|---|---|---|
| Pong | 8（5 / 3） | `EACAF41B…`(3391 B) → `BD5E740C…`(1989 B) | **9/9 相同** | 4/4 相同 | `-32000` 拒绝 | **14/74 非零** |
| Breakout | 20（18 / 2） | `2EE4A2B5…`(8553 B) → `DB616EB2…`(4731 B) | **21/21 相同** | 4/4 相同 | `-32000` 拒绝 | **14/89 非零** |
| Snake | 37（37 / 0） | `653A3541…`(13284 B) → `47D8BB7E…`(7075 B) | **38/38 相同** | 4/4 相同 | `-32000` 拒绝 | **13/102 非零** |

* **「游戏逻辑未变」的证据不止一类**：①「清理前文件**去掉副本块**后与清理后文件**逐字节相同**」（除场景自身 `uid` 一行，见下）——`recovery\work\task097\check_cleanup.py` 对三款逐一实测；②具名节点的序列化块逐字节相同；③属性采样（位置/尺寸/颜色/文本/可见）前后相同；④**重放里原来的每一条断言仍然通过**（Pong 的 `g05/g18/g21/g22/g26/g27`、Breakout 的 `g05/g12d/g18/g20/g21/g22/g24`、Snake 的 `g04/g06/g08/g13/g14/g15/g17/g18/g19/g22/g25/g26`，含两条「按设计失败」的断言）；⑤运行期新建节点的对照（Snake 的移动采样仍出现两个位置、Space Invaders 的 `ProbeOverlay`）。
* **顺手实测到的一条副作用（不是本任务的改动）**：`editor_save_scene` 每**编辑器会话**第一次保存会给场景**重新分配 `uid`**（`.tscn` 头 `uid="uid://…"` 变化，文件其余字节不变）。项目里没有任何引用按 uid 指向这三份场景，游戏按路径加载，因此不影响本轮的结论；登记在此以免下游把「sha 变了」误读成内容变了（`check_cleanup.py` 的比较里把这一行归一化后才是「逐字节相同」）。**本任务未改这条行为，也未在本轮修复它。**

### 台账数字一致性复核（TASK-098，2026-09-27）

TASK-098 把台账每一行引用的数字**从它自己引用的那份产物里**重读了一遍，而不是照旧报告抄：
`recovery\work\task098\log_consistency.py` 读每轮的 `report.json`，打印调用数、`facts_complete`、
判定分布、像素列（可比对 / 非零 / 每相拆分）与 `user://` 帧链。结果：

| 行 | 台账写的 | 产物复查 | 结论 |
|---|---|---|---|
| Pong | 52/52；像素 14/74（编辑器 3/45、游戏 11/29）；帧 512 / 512 / 7175 | 同 | **一致** |
| Breakout | 55/55；像素 14/89（2/55、12/34）；帧 3072 / 3464 / 2529 / 2169 | 同 | **一致** |
| Snake | 51/51；像素 13/102（0/71、13/31）；帧 480000 / 4032 / 480000 | 同 | **一致** |
| Tetris | 42/42；像素 11/42；帧 3174 / 4232 / 8503；首轮 53 次 | 同 | **一致** |
| Space Invaders | 59/59；像素 12/59（1/15、11/44）；帧 1576 / 38127 / 16990 / 4800 | 同 | **一致** |
| Asteroids | 71/71；像素 16/71（1/16、15/55）；帧 14774 / 996 / 6346 / 7072 / 8960 | 同 | **一致** |
| Pac-Man | 80/80；像素 15/80（1/16、14/64）；帧 18888 / 1853 / 18546 / 9586 | 同 | **一致** |

**唯一一处要更新的是副本数的口径，不是数字本身**：D-3 的「pong 5 / breakout 18 / snake 37」
是**只数 `@ColorRect@*`**；把 `@Label@*` 一并算进来是 **8 / 20 / 37**（5+3、18+2、37+0）。
证据是清理会话自己从盘上读回来的**清理前场景原文**
（`runs\<game>\<game>-clean-task097\c03-read-before.json`，场景字节 3391 / 8553 / 13284 B，
与 TASK-097 报告的清理前尺寸逐一吻合），由 `recovery\work\task098\copy_count_evidence.py`
逐个列出 `@...@` 名字重新数过。已在 D-3 行与 `MCP-TRACEABILITY.md` §7.1 两处加注「历史口径」。

**帧链容易被读错的地方（也已核过）**：`report.json` 的 `diff_vs_prev` 记在**目标帧**上，配对是
「与上一个**同尺寸**帧」，而 `user://` 目录里会留着更早实验的 PNG。所以台账写
「`snake-t2`→`final` 480000」时，读法必须是**帧链**（t0→t1→t2→final），不是「名字里带 `t2` 的那一行」。
`recovery\work\task098\frames_recompute.py` 独立按 mtime 重算三个老游戏的帧链，与 `report.json`
**0 处不符**（`snake`：t0→t1 480000、t1→t2 4032、t2→final 480000）。

### TASK-099 记录（2026-09-27）

1. **第 8、9 款（Frogger / Flappy Bird）交付**：台账第 8、9 行来自它们自己那一轮的产物
   （`runs\frogger\frog-task099-r1\report.json`、`runs\flappy\flappy-task099-r2\report.json`）。
   **工具缺陷 0 条**（上面「游戏或驱动缺陷」表新增的一条 **F-1** 是载荷缺陷：Flappy 的自重跑时钟
   把 `delta*60` 截断成 0，高帧率下一格都不走 —— 由 `g44` 的 30 帧采样照出来，改成累加器后重跑 r2）。
   Frogger 首轮零缺陷。两条非 `ok` 判定在每一轮里都是**声明过的**：`e06` 的同名批量拒绝
   （`-32000`，D-3 的证据）与一条故意打在不存在属性上的边界断言（`-32001`）。
   像素差 17/90（Frogger，首轮）与 22/92（Flappy，r2）逐对独立复算，**0 处不符**；
   `user://` 五帧的 sha 全部互不相同，帧链与 `report.json` 逐值一致；Flappy 的 r2 五个帧与 r1
   **逐字节相同**（同一个被钉住的状态画出同一张图）。
   两款都把「多帧采样先于会改变状态的那一步」与「先钉状态再断言」照做：Frogger 的冻结基线
   （12 帧 4 个属性各 1 个值）对 30 帧交通采样；Flappy 的冻结基线对 `SetAutoRun(true)` + 30 帧滚动采样
   （r2 里 `Pipe0X` 17 个不同值 576→492、`BirdY` 恒定）。两款都新增了**与帧率无关的增量属性**
   （Frogger 的 `LastTrafficSteps`、Flappy 的 `LastPassFrames` / `LastPassDelta`），P-1 的教训被写进载荷本身。
2. **门跑器 G-1 已修**（见工具缺陷表）：`run_gates.ps1` 现在默认读二进制的 `--version` 当锚点，
   并在 committed diff 与工作树都没有编译输入时判 `ANCHOR_STRUCTURAL_EQUIVALENT` + 跳过十道门
   （打印非编译文件清单）；有编译输入仍照常跑门。两情形实测见
   `runs\gates\task099-doconly\summary.txt` 与 `runs\gates\task099-compileinput\summary.txt`
   （后者 `g01`..`g10` 全 `exit=0`、`accept_m1 22/22`）。**该脚本在主仓 `tools\` 下，不在引擎仓里，
   因此不改变两个变体的任何一个字节**（引擎仓 `git status` 前后均为空）。
3. **`--import` 的关机期访问违例第 3 次现场复现**：`runs\frogger\frog-task099-r1\import.stderr.txt`
   与 TASK-097/098 一字不差（`0xC0000005`、`Parameter "singleton" is null.` @ `editor_node.cpp:6750`、
   日志已到 `[ DONE ] loading_editor_layout`）；同轮 `flappy` 的首次导入 `exit=0`（对照组，同样是全新工程）。
   受控探针 `recovery\work\task099\import_crash_probe2.ps1`（fresh/warm × 默认端口 9877 × 是否加压）
   的结果记在 `recovery\work\task099\logs\importprobe*`。**本轮未改引擎、未加埋点**：台账自己的口径是
   「根因不清楚的只记录、不猜改」，而三个判别器都要动引擎源码 + 重建两变体 —— 在一个探针无法按需
   复现的假设上重建，不符合这条口径。**对跑测试的实际影响不变**：它不影响导入结果，`IMPORT_EXIT`
   不能当健康信号（`run_game_session.ps1` 只记一行、不据此判失败）。
4. **十道门与验收**：本轮**没有模块字节改动**（引擎仓 diff 只有文档），因此没重建、没 push 代码；
   但预检的「有编译输入」那一情形把十道门**真实跑完**（全 `exit=0`，`accept_m1 22/22`），
   作为「跳过逻辑没有把门跑坏」的证据。

### TASK-100 记录（2026-09-27）

1. **第 10、11 款（2048 / Minesweeper）交付**：台账第 10、11 行来自它们自己那一轮的产物
   （`runs\game2048\2048-task100-r2\report.json`、`runs\minesweeper\mine-task100-r2\report.json`）。
   **工具缺陷 0 条**；「游戏或驱动缺陷」新增两条 **G1**（载荷：一个属性两个写者，r1 照出来、r2 修好）
   与 **M1**（会话：把 `ForceTestState` 会归零的计数器当成会保留，r1 照出来、r2 修好）。
   每一轮的两条非 `ok` 判定都是**声明过的**：`e06` 的同名批量拒绝（`-32000`）与一条故意打在不存在
   属性上的边界断言（`-32001`）。
   像素差 26/129（2048 r2）与 21/155（Minesweeper r2）逐对独立复算，**0 处不符**；
   `user://` 帧链（2048 六帧、Minesweeper 五帧）与 `report.json` 逐值一致、每个 sha 互不相同；
   Minesweeper r2 的五个帧与 r1 **逐字节相同**（同一个被钉住的状态画出同一张图），
   2048 r2 的 t0/t1/t2/t3/t5 也与 r1 逐字节相同、只有 t4 不同（自动时钟的帧时序）。
2. **「会动的证据」两路都有**：①**多帧属性采样**（先冻结基线、再自动时钟 30 帧）——
   2048 的 `MoveCount` 30 个不同值 6→65、`AutoSteps` 30 个、`Elapsed`/`Ticks` 各 30 个；
   Minesweeper 的 `RevealedCount` 7 个不同值 16→71、`RevealHash` 7 个、`Elapsed`/`Ticks` 各 30 个。
   ②**像素差 + 独立复算**（逐调用对 + 保存帧），两款的 `recomputed-vs-trace mismatches = none`。
3. **时钟全部与帧率无关**：两款都是浮点累加器 `_autoAccum += delta*rate`（不用 `(int)(delta*rate)`，
   即 F-1 的修法），`Elapsed` 是每帧 `+= delta` 的浮点秒表；每款另有**两个**独立增量属性
   （`LastHookSteps` = 钩子这次调用走了几步、`LastAutoSteps` = 这一帧的时钟走了几步）。
   **G1 就是这条纪律的产物**：两个生产者共用一个属性时，采样/断言读到的不再是它要证的那个事实。
4. **D-3 的拒绝在每一轮证据里**：两款都在建场景那一步**故意再跑一次同名批量**，`e06` 被判 `-32000`
   并给出 3 条 `conflicts`；`e05`/`e09` 的 `project_read_text_file` sha **逐字节相同**
   （2048 `7e7fb1d9…`/813 B，Minesweeper `1fcc873e…`/826 B）；两次运行的 `running_game_get_scene_tree`
   共 75 / 333 个节点名里 **0 个 `@` 开头**。
5. **确定性布雷可独立复算**：Minesweeper 的默认雷区是种子 LCG 的纯函数，会话生成器**用同一条规则
   在 Python 里重算**出 `0,4|0,5|1,6|2,4|4,0|6,0|7,4|7,7|7,8|8,0` 并把它作为断言字面量 ——
   `g07` 与收尾的 `g136` 两条 PASS 都是「实现与独立复算相符」，不是转述。
6. **`--import` 的关机期访问违例本轮 0 次**：四次导入（2048 r1/r2、Minesweeper r1/r2）全部
   `IMPORT_EXIT=0`、`import.stderr.txt` 0 字节。累计口径由 3/13 变成 **3/17**（待办 2 不变）。
7. **门跑器**：本轮**没有模块字节改动**（引擎仓 `git status` 空、`git diff 2385fe2fb..HEAD` 只有两份
   `.md`），因此按 TASK-099 的预检直接判 `ANCHOR_STRUCTURAL_EQUIVALENT` + `RESULT=SKIP_REBUILD` +
   `GATES_SKIPPED=1`（exit 0，`runs\gates\task100-doconly\summary.txt`）—— **如实说明：十道门本轮
   一门未跑**，没有重建、没有 push 代码。理由与 TASK-099 相同：没有编译输入，跑门只会把同一份
   已经通过的二进制再跑一遍。

### TASK-101 记录（2026-09-27）

1. **第 12、13 款（Sokoban / Bomberman）交付**：台账第 12、13 行来自它们自己那一轮的产物
   （`runs\sokoban\soko-task101-r2\report.json`、`runs\bomberman\bomb-task101-r4\report.json`）。
   **工具缺陷 0 条**（`modules\mcp_server` 本轮零字节改动）；「游戏或驱动缺陷」新增四条：
   **K-1**（Sokoban 会话：在第一次 `AutoStep` 之后断言了两次调用之后的状态）、**B-1**（Bomberman
   载荷：走进敌人时把敌人一起删了，与规则不符）、**B-2**（Bomberman 会话：断言 `ProbeRow` 却没
   探过格子）、**B-3**（Bomberman 会话/测试设计：自动时钟采样的钉板已经分出胜负 —— r2 把炸弹钉在
   砖块格上、r3 引信太短，两次的采样都看着冻住的盘面，而断言照样全 PASS）。四条都修好并在
   r2 / r4 复核。
2. **每一轮的两条非 `ok` 判定都是声明过的**：`e06` 的同名批量拒绝（`-32000`，D-3 的证据）与一条
   故意打在不存在属性上的边界断言（`-32001`）。`e05`/`e09` 的 `project_read_text_file` sha
   **逐字节相同**（Sokoban `d5c22b0d…`/831 B，Bomberman `05672aed…`/844 B），即被拒的批量
   **什么都没写**；两次运行的 `running_game_get_scene_tree` 共 75/76 与 127/128 个节点名里
   **0 个 `@` 开头**。
3. **独立复算不是转述**：`recovery\work\task101\recompute_readbacks.py` 不看 `report.json`、
   不看断言助手、也不看 C# —— 它把载荷**打印出来的** `Dump()` 一行行拆开，用**自己**的规则重算：
   Sokoban 的 `BoardHash` 由**打印出来的 ASCII 盘面**重新推（墙 2 / 地板 1 / 目标 3 / 箱 4 /
   箱在目标 5 / 玩家 6 / 玩家在目标 7），Bomberman 的 `GridHash` 由**打印出来的 ASCII 场地**重新推
   （硬墙 1 / 地板 2 / 砖 3），两者都是 32 位 multiply-31 链；再把会话里那些**由 Python 第二实现
   算出来的字面量**（四次爆炸的逐格坐标序列、炸后网格哈希、两步/三步追击后的敌人表与单位哈希、
   被抓后的玩家位与哈希）与载荷在**本轮的响应文件里实际回报的 `actual`** 逐条对齐。
   **Sokoban 0 处不符、Bomberman 0 处不符**（`logs\recompute-soko-r2.txt`、
   `logs\recompute-bomb-r4.txt`）。
4. **「会动的证据」两路都有**：①**多帧属性采样**（先冻结基线、再自动时钟 30 帧）——
   Sokoban 的 `Steps` **30 个不同值 15→59**、`AutoSteps` 30 个、`PlayerRow`/`PlayerCol` 各 2 个、
   `Elapsed`/`Ticks` 各 30 个；Bomberman 的 **`BombList` 17 个不同值 `4,4,16`→`''`**，且**第 16 帧
   同时**发生 `BombsActive` 1→0、`Detonations` 0→1、`BricksRemaining` 3→1、`GridHash` 变、
   `LastBlastCount` 0→7。②**像素差 + 独立复算**（逐调用对 + 保存帧）：Sokoban **29/190**（编辑器
   1/14、游戏 28/176）、Bomberman **45/233**（1/14、44/219），两款的 `recomputed-vs-trace
   mismatches` 都是 `none`，保存帧的 sha 与 `report.json` 逐值一致。
5. **时钟全部与帧率无关**：两款都是浮点累加器（`_autoAccum += delta * rate`，不用
   `(int)(delta*rate)`，即 F-1 的修法），`Elapsed` 是每帧 `+= delta` 的浮点秒表；每款另有**两个**
   独立增量属性（`LastHookSteps` = 钩子这次调用做了多少、`LastAutoSteps` = 这一帧的时钟做了多少）。
   两款都在时钟跑过 30 帧之后断言 `LastHookSteps` **仍是钩子写下的那个值**。
6. **确定性观察（如实记录，不是缺陷）**：Sokoban 的 `soko-t1` 拍在 `Undo()` 之后，而撤销把玩家与
   箱子一起回滚到起点 —— `soko-t0` 与 `soko-t1` 因此**逐字节相同**（`px_vs_prev=0`），六个帧里
   5 个互不相同。Bomberman 的六个帧 **6/6 互不相同**。Sokoban r2 的 `t0`/`t1`/`t2`/`t3`/`t5` 与
   r1 **逐字节相同**，只有 `t4`（自动巡逻采样之后那一帧）不同 —— 与 2048 的 t4 同一种现象（帧时序
   无法逐字节复现）。Bomberman r1→r2 之后 `t2`/`t3`/`t4` 变了，因为 B-1 改了「接触后敌人是否留下」，
   盘面本来就不同。
7. **`--import` 的关机期访问违例本轮到 r4 为止 0 次**：Sokoban 两次（r1、r2）、Bomberman 四次
   （r1..r4）共 **6 次导入全部 `IMPORT_EXIT=0`**、`import.stderr.txt` 0 字节。累计口径由 3/17 变成
   **3/23**（待办 2 不变）。
8. **门跑器**：本轮**没有模块字节改动**（引擎仓 `git status` 空、`git diff 2385fe2fb..HEAD` 只有两份
   `.md`），因此按 TASK-099 的预检直接判 `ANCHOR_STRUCTURAL_EQUIVALENT` + `RESULT=SKIP_REBUILD` +
   `GATES_SKIPPED=1`（exit 0，`runs\gates\task101-doconly\summary.txt`）—— **如实说明：十道门本轮
   一门未跑**，没有重建、没有 push 代码。


| id | 游戏 | 现象（证据） | 根因 | 处置 → 重跑结果 |
|---|---|---|---|---|
| **B-1** | Breakout | 球被瞄准在侧壁正上方时「贴墙直下」，`runs\breakout\breakout-task093-r3\engine-game.stdout.txt` 里 `speed=0,276` 一路到底，最后 `GAMEOVER reason=lost` | 侧壁分支写 `BallSpeedX = Mathf.Abs(BallSpeedX)`，水平分量为 0 时 `Abs(0)=0`，球失去横向分量 | **改**：水平分量为 0 时额外给 96 px/s 的内向偏折。r7 里 `BREAKOUT_BOUNCE` 正常出现、`PaddleBounces=7` |
| **B-2** | Breakout | `g12d` 断言「球被挡板弹回」失败：`BallSpeedY=276`（仍在向下），球落到场外；`g29` 里 `over=true` | `HitsPaddle()` 把**场坐标**的球位置与**绝对坐标**的挡板 `position` 直接比较（挡板绝对值 540，场坐标里那是 40），实际要求的矩形是 `y[540,556]`（场空间里在场地下方 500 px） | **改**：`HitsPaddle` 先把挡板位置减去 `ParkX/ParkY` 换成同一坐标系。诊断探针（`recovery\work\task093\diag-breakout.ps1`）实测 `BREAKOUT_BOUNCE` 出现、`PaddleTest()` 从 `hits=False` 变为命中 |
| **B-3** | Breakout | `HudScore.text` 断言失败：点数读回 10，屏幕文本是 `"10"` 而不是 `"SCORE 10"` | `BreakBrick` 直接写 `_scoreLabel.Text = Score.ToString()`，而 `_Ready`/`WriteHud` 写 `"SCORE {Score}"`；HUD 有两个写者、两种格式 | **改**：`BreakBrick` 改走 `WriteHud`。r7：`text eq "SCORE 10"` 通过，屏幕文本断言也通过 |
| **B-4** | Breakout（会话） | `g16-aim-at-brick` 的 `AimBall(35,160,...)` 把球放到**离砖 500 px** 的位置；`g18`「砖没了」却仍通过（球自由飞行时撞掉了别的砖） | 会话把**绝对屏幕坐标**传给了吃**场坐标**的测试钩子；断言与瞄准不是同一件事，测试因此**恰好**通过 | **改**：`AimBall` 文档写明坐标约定；会话改用 `35-ParkX, 160-ParkY`。r7：`Brick_r2_c0.Alive=false`、`BricksRemaining=14`、`Score=10` 三条同时成立 |
| **B-5** | Breakout（会话） | 早期几轮 `g20-assert-score-label-10` 的期望值写成 `"SCORE 10"` 但当时 HUD 写 `"10"`（与 B-3 同源），另有一条 `g25` 边界调用未落到端口上 | 会话期望值在代码改完之前先写死了 / 边界调用工具选错 | **改**：随 B-3 一并修正；边界调用改为 `running_game_find_node_when_available`（1 s 最短合法超时），实测 `-32000` + `timeout_ms:1000` |
| **S-1** | Snake | 第一条会话里「增长」断言读到 `len=3` 而同刻 `score=10`：`runs\snake\snake-task093\g12-readback-growth.json` | `ForceTestState` 摆了新棋盘却**没清 `GameOver`**——蛇在被测之前已经撞墙结束，`_Process` 提前返回，瞄准与观测互相打架 | **改**：`ForceTestState` 先 `Resume()`。r6：`Length=4`、`Score=10`、`FoodsEaten=1`、`segments_in_use=4` 四条同刻成立 |
| **S-2** | Snake | `g14-growth` 读回 `Score=20, FoodsEaten=2` 而测试期望 10 / 1 | 计数器跨测**不归零**，断言读到的是整场会话的累计值而不是这一次步进的增量 | **改**：`ForceTestState` 把 `Score`/`FoodsEaten`/`Ticks` 归零 |
| **S-3** | Snake | `g24b-dump-wall-board` 显示瞄准写入 `dir=1,0`、下一调用读回 `dir=-1,0`，`held=[l=True r=False u=True d=True]`（**没有任何场景在跑**）；墙测因此变成自撞（`SNAKE_SELF head=23,5`） | 场景步骤（`running_game_test_execution.cpp` 的 `_build_scenario_events`）只注入 `pressed=true` 的 `InputEventAction`、**从不注入配对的释放**，Godot 于是把该动作永久保持在按下态；蛇每帧采样 `Input.IsActionPressed`，把注入过的动作全都当成「玩家一直按着」，覆盖掉测试自己写的方向 | **改**：动作一旦以事件形式到达就记入 `_eventDriven`，此后不再采样它的按住态（真人连续按住的路径不受影响）。r6：墙测 `LoseReason=wall`、自撞测 `LoseReason=self`，两条同时成立 |
| **S-4** | Snake（会话） | 墙测瞄在 `24,5`（最后一格），第一步就是「头部进入颈部刚离开的格子」，被自身的自撞检查正确地判成 `self` | 会话把「离墙一格」误当成「离墙两格」 | **改**：瞄到 `23,5`，并加 `g24b-dump-wall-board` 把棋盘原样打出来（`segs=23,5\|22,5\|21,5 ... dir=1,0`） |
| **T-1** | Tetris（会话 / 载荷） | 首轮 `g20-assert-filled` 期望 `FilledCells=8` 实得 **0**，随后 `g22`（`Lines=1`）与 `g23`（`Score=100`）双双失败；引擎 stdout 的 `TETRIS_FORCE` 明写 `board=.../.......... filled=0`，而同一行的 `LastEvent` 又回显了完整 spec | 会话的 `board=` 用竖线分隔行，而 `WriteBoard` 只按 `/` 分行 → 整块 20 行落进第 0 行，第 0 行只取前 10 个字符（全是点）。**调用本身诚实报成功**，是断言把它抓出来的 | **改**：`WriteBoard` 同时接受 `/` 与竖线（`rows.Replace('|','/').Split('/')`）。r2：`g20` 实得 **8**、`g22` 实得 **1**、`g23` 实得 **100**，三条同刻成立 |
| **T-2** | Tetris（载荷） | 首轮 `g21-harddrop-clear` 返回 `score=0 lines=0`，而落锁后 `g29` 读回 `score=100 lines=1`——**同一个 `HardDrop` 的返回值与它自己的效果不一致**，`g22`/`g23` 因此在效果发生前后各读到一次不同状态 | `HardDrop()` 的 `LastEvent` 在 `LockPiece()` **之前**拼好，返回的是上一步的状态 | **改**：先 `LockPiece()` 再拼 `LastEvent`。r2：`g21` 直接返回 `harddrop dropped=0 piece=O score=100 lines=1 over=False` |
| **T-3** | Tetris（会话 / 测试设计） | 首轮 `g26` 用「出生行整行填满」造 GameOver，结果 `g28`（`GameOver=true`）失败，而同刻 `Lines=1`、`Score=100` —— 消行反而发生了 | `LockPiece()` 的顺序是「落锁 → 消行 → 出生」，整行会在出生检查之前被消掉，棋盘因此永远不满足结束条件。**游戏是对的，测试设计错了** | **改**：改用「出生格 `(4,0)`、`(5,0)` 被占、而这一行不是满行」（`....##....`）。r2：`g27` 返回 `over=True`、`g28` 实得 **true**、`g29` `filled=6` |
| **A-1** | Asteroids（会话） | 首轮 `g36-assert-score-120` 期望 `Score=120`、**实得 100**（`runs\asteroids\ast-task098-r1`）；`assertions.py` 把它列为 PASS 之外的唯一非声明失败 | 会话假设 `ForceTestState` 只换棋盘、**保留**计数器；而它按前五款游戏的确定性规则把**整个状态**钉死（`Score=0`、`AsteroidsSplit=0`、`AsteroidsDestroyed=0`），所以赢局那 100 分**只属于最后一颗小行星**，分列那一步的 20 分已经被重置 | **改**：期望值改成 **100**，并把「20 分钉在 `g19`」写进 `g36` 的注。r2：`g36` PASS（`actual=100`）；`runs\asteroids\ast-task098-r2` 的 25 条断言 = **24 PASS + 1 条声明的边界失败（`-32001`）** |
| **P-1** | Pac-Man（会话 / 载荷） | 首轮 `g15-assert-patrol-12` 期望 `GhostSteps=12`、**实得 16**（`runs\pacman\pac-task098-r1`） | 会话把 `GhostSteps`（**累计总数**）当成一次 `StepGhosts(12)` 的**增量**；前面那次 30 帧巡逻采样在 `GhostSpeed=8` 下已经让时钟推进了 **4** 步，而**帧率决定它是 3 还是 5** —— 也就是说这条断言就算写对总数也会抖 | **改**：载荷新增真导出属性 **`LastPatrolSteps`**（一次 `StepGhosts` 的增量，被 `GameOver` 截断时也如实记），会话改成「增量 `eq 12`」+「总数 `gt 12`」，断言因此与帧率无关。r2：`g15`/`g16` 双双 PASS；`runs\pacman\pac-task098-r2` 的 30 条断言 = **29 PASS + 1 条声明的边界失败（`-32001`）** |
| **F-1** | Flappy Bird（载荷） | 首轮 `runs\flappy\flappy-task099-r1` 的 `g44-samples-scroll`：30 帧采样里 `Ticks` 从 31 走到 101（引擎在跑），而 `Pipe0X` **恒定 582**、`BirdY` 恒定 300 —— 「自重跑时钟」一格都没推进世界。**所有断言仍然 PASS**（没有一条断言要求它动），是**多帧采样**把这条缺陷照出来的 | `FlappyBirdGame._Process` 写的是 `frames = (int)((float)delta * FixedFps)`：这台机器上窗口游戏进程跑在 60 fps 以上（采样显示约 144 fps），单帧 `delta*60 < 1`，截断成 0，于是 `StepFrames(0)` 永远不发生。会话里 `SetAutoRun(true)` 的响应本身诚实（`auto_run=True`），**缺陷在载荷的时钟，不在工具** | **改**：改成**累加器** `_autoAccum += delta * FixedFps; frames = (int)_autoAccum; _autoAccum -= frames;`（`SetAutoRun` / `ForceTestState` / 声明动作的重开路径都清零），并在源码注释里写明是这次采样发现的。**重跑 r2**：`g44` 的 `Pipe0X` 变成 **17 个不同值（576→492）**，`BirdY` 仍恒定；`g13` 冻结基线不变（`Pipe0X` 仍 1 个值）；断言仍 **38 PASS + 1 条声明的边界失败**；像素差 21/92 → **22/92**（多出来的那一对正是滚动采样后的那一帧） |
| **G1** | 2048（载荷） | 首轮 `runs\game2048\2048-task100-r1` 的 `g88-assert-last-auto-2` 期望 `LastAutoSteps=2` 实得 **0**、`g110-assert-last-3` 期望 3 实得 **0**；而同一刻 `AutoSteps=2`、`MoveCount=2` 双双 PASS —— 钩子确实走了两步，只是**读到的是别人写的值** | `LastAutoSteps` 有**两个写者**：`AutoStep(n)` 钩子写「这次调用走了几步」，`_Process` 每帧结尾写「这一帧的时钟走了几步」（时钟关闭时写 0）。断言在钩子返回之后、下一帧之后才执行，于是读到 0。**这是 P-1 的同一条教训换了个形态**：一个属性两个生产者，读回就不再是那个生产者的事实 | **改**：拆成两个属性 —— `LastHookSteps`（只有 `AutoStep` 写，时钟一个字节都不碰）与 `LastAutoSteps`（只有每帧时钟写）。r2：`g88-assert-last-hook-2`=2、`g88b-assert-last-auto-0`=0、`g110-assert-last-hook-3`=3 **三条同时 PASS**；r1 的两条失败帧保留为对照 |
| **M1** | Minesweeper（会话） | 首轮 `runs\minesweeper\mine-task100-r1` 的 `g124b-assert-hook-intact` 期望 `LastHookSteps=2` 实得 **0**，而 `g113-assert-last-hook-2`（同一事实、早 11 次调用）**PASS** | 会话在这两条断言之间插了一次 `ForceTestState`，而它按前 11 款游戏的确定性规则把**整个状态**钉死 —— 包括这条增量。**载荷是对的，是会话的假设错了**，与 A-1 / T-3 同一类 | **改**：让「钩子 → 开时钟 → 30 帧采样 → 关时钟 → 两条增量断言」落在**同一块被钉住的盘面**上（删掉中间那次 `ForceTestState`），并**新增一条显式断言** `ForceTestState` 之后 `LastHookSteps=0`（把 A-1 的教训写成断言而不是假设）。r2：`g113`/`g113b`/`g118b`/`g124`/`g126b` 全 PASS；r1 的失败帧保留为对照 |
| **K-1（TASK-101）** | Sokoban（会话） | 首轮 `runs\sokoban\soko-task101-r1` 的 `g145-assert-steps` 期望 5 **实得 2**、`g146-assert-player` 期望 `PlayerCol=3` **实得 4**（`runs\sokoban\soko-task101-r1\g141-autostep-2.json` 诚实回报 `autostep requested=2 attempts=2 accepted=2 total=2 steps=2`；`g148` 回报 `accepted=3 total=5 steps=5`） | 会话生成器把仿真实例**连用了两次** `auto_step`，而第一次调用之后的断言引用的是**两次调用之后**的快照（`AUTO2.steps`=5、`AUTO2.pc`=3）。**C# 是对的，是会话读错了时刻** —— 与 P-1 / A-1 / T-3 同一类，但这次错在**取值时机**而不是属性的语义 | **改**：`make_session_sokoban.py` 在第一次 `auto_step(2)` 之后显式快照 `AUTO2_STEPS2` / `AUTO2_PC2` / `AUTO2_PR2`，三条断言改用快照。r2：`g145`=2、`g146`=4、`g147`=2 三条同时 PASS，且 `g140`..`g152` 全部 PASS |
| **B-1（TASK-101）** | Bomberman（载荷） | 首轮 `runs\bomberman\bomb-task101-r1` 的 `g127-assert-alive` 期望 `EnemiesAlive=1` **实得 0**、`g129-assert-unit-hash` 期望 `1287431919` **实得 2024506202**，而同一刻 `g123`（`DeadByEnemy=true`）、`g125`（`Lives=2`）、`g126`（重生）全部 PASS —— 「玩家被抓」这件事**发生了**，只是敌人也没了 | `Move` 走进敌人格时先 `_enemyRow.RemoveAt(caught)` 再 `KillPlayer("enemy")`。经典规则是「接触即掉命、敌人**存活**」；第一版把敌人当成消耗品，`EnemiesAlive` 与 `UnitHash` 因此和证据所引用的规则不符。**这是 Python 第二实现（`BSim`）算出来的**：它在同名断言里给出的是「敌人留下」 | **改**：删掉那两行 `RemoveAt`，并补一条 `alive={EnemiesAlive}` 到 `LastEvent`。r2 起重跑：`g123`/`g125`/`g126`/`g127`/`g129` 五条同时 PASS |
| **B-2（TASK-101）** | Bomberman（会话） | 首轮 `g90-assert-probe-brick` 期望 `ProbeRow=2` **实得 -1** | 会话在那条断言之前**没有在那块盘面上探过任何格子**：`g81` 的 `ForceTestState` 按确定性规则把 `Probe*` 一并归零 (`ProbeRow=-1`)，会话却把上一段（不同的关卡）留下的探测结果当了真。注释与断言名（`probe-brick`）也都与实际不符 | **改**：改成显式 `ProbeCell(1, 3)`（炸弹原来的格子）+ 断言 `ProbeRow=1` 与 `ProbeState=floor`，再 `ProbeCell(2, 4)` 看幸存的那块砖。r4：`g90`/`g90b`/`g90c`/`g91`/`g92` 全部 PASS |
| **B-3（TASK-101）** | Bomberman（会话 / 测试设计） | r2 的 `g178-samples-clock` 30 帧采样里 **`AutoTicks` 恒定 4、`BombsActive` 恒定 0、`BricksRemaining` 恒定 0、`Elapsed`/`Ticks` 在走** —— 「炸弹爆炸」的采样看着一块**已经分出胜负的盘面**；r3 同样（`AutoTicks` 恒定 6、`BombsActive` 恒定 0）。两次的断言都**照样全 PASS**，是多帧采样把它照出来的 —— 与 F-1 一模一样的照法 | 两处叠加：①钉板把炸弹放在 `(3,4)`，而那是**砖块格** —— `PlaceBomb` 永远到不了的状态（它只在玩家脚下放炸弹，而玩家永远站不到砖上），爆炸于是把**炸弹自己脚下那块砖**也炸了，两块砖一起没 → `Won=true` → `GameOver` → 时钟停机；②r3 把引信定成 8，而 `SetAutoClock` 与 `samples` 之间那两三次调用的时间里时钟已经烧掉了 6 格，采样开始时炸弹已经不在 | **改**：钉板改成「炸弹在**地板** `(4,4)`、三块砖里只有两块在爆炸范围内、剩下的那块保证**永远赢不了**」，并且**按实测时钟速率给引信定尺**：累加器是墙钟驱动的，30 帧采样 ≈ `60 × 0.478 s ≈ 29` 个 tick，与帧率无关，所以引信 24 保证它**必然**在采样窗口内烧完、又**必然**活过采样开始前那几次调用。r4 的采样：`BombList` **17 个不同值** `4,4,16`→`''`，**第 16 帧**同时 `BombsActive` 1→0、`Detonations` 0→1、`BricksRemaining` 3→1、`GridHash` 变、`LastBlastCount` 0→7；`AutoTicks` 29 个不同值、`Elapsed`/`Ticks` 各 30 个。r2/r3 的冻帧保留为对照 |
| **PL-1** | Platformer（**载荷**） | 首轮 `runs\platformer\plat-task102-r1` 的 `g48-assert-x` 期望 `PlayerX=0` **实得 20**；而同刻 `g49-assert-wall-hits=1`、`g50-assert-vx-0=0`、`g51-assert-facing=-1`、`g52-assert-ground=True` 全 PASS —— 「撞墙停下」发生了，只是停的像素不对 | `ResolveHorizontal()` 用「盒子前缘所在格子 + 1」的格子相对公式解算碰撞，而 C# 的整数除法**向零截断**：盒子被推到 x=-2 时 `-2/20 = 0`，公式给出 `(0+1)*20 = 20`，把玩家从墙上弹回两格。Python 第二实现用**向下取整**的除法，`-2//20 = -1`，公式给出 `0` —— 两边对「世界左边缘」的答案不同，断言把 C# 的那一侧照了出来 | **改**：左/右/顶三条世界边界的解算改成**显式像素钳位**（`x<0→0`、`x+PW>Cols*Tile→Cols*Tile-PW`、`y<0→0`），格子相对公式只用于地图内部的实心格。r2：`g48` 实得 **0**、`g49`～`g52` 同刻成立 |
| **PL-2** | Platformer（**载荷**） | 首轮 `g61-assert-not-ground` 期望 `OnGround=False` **实得 True**：`Jump()` 刚被调用、速度已经是 `-12`，而「是否站在地上」还是起跳前的值 | `Jump()` 只设 `VelY`，没有清 `OnGround`；起跳语义上就是离地，第二实现 `PSim.jump()` 会清、载荷不清 | **改**：地面跳与空中跳两条分支都置 `OnGround=false`。r2：`g61` 实得 **False**，且抛物线 24 帧的每个检查点（含第 23 帧 `y=544` 但**仍在空中**）都与第二实现一致 |
| **PL-3** | Platformer（**会话**） | 首轮 `g144-assert-gem-hash` 期望 `MapHash=-1950852335` **实得 -1674907474** | 会话生成器给 LEVEL1 的四个场景都写了 `goal=0,0`（地图里多了一个终点格），而 `PSim` 是按 `goal=None`（无终点）构造的 —— **期望值与它引用的那个状态不是同一个状态** | **改**：四个 LEVEL1 场景改为不传 `goal=`（LEVEL1 本来就没有终点格），`PSim` 与规范因此一致。r2：`g144` 实得 **-1950852335** |
| **M3-1** | Match-3（**会话**） | 首轮 `runs\match3\m3-task102-r1` 的 `g11-assert-probe-value` 期望 `ProbeValue=5` **实得 1** | 会话对 `_Ready()` 里由 LCG 生成的默认棋盘**只能猜**：「(3,5) 应该是 5」是写死的字面量，没有任何复算支撑。**载荷是对的** | **改**：在生成器里用同一条 LCG 与同一个消稳循环复算 `BuildBoard()`，把默认棋盘、`BoardHash` 与生成后的 `Seed` 都做成断言，`ProbeValue` 取自复算结果。r2/r3：`g07a`/`g07b`/`g07c`/`g11` 全 PASS，`Seed=749508457` 与载荷 `MATCH3_READY` 打印的完全一致 |
| **M3-2** | Match-3（**会话**） | 首轮 `g35-assert-rejected-2` 期望 1 **实得 2**、`g38-assert-rejected-3` 期望 1 **实得 3** | 会话生成器给每种非法交换都新建了一个仿真对象，每个都只记 1 次拒绝；而会话是在**同一块盘面**上连做三次非法交换，`RejectedMoves` 是累计的 | **改**：三种拒绝改成建在**同一个**累计对象上（1/2/3）。r2/r3：`g29`/`g35`/`g38` 三条同时 PASS |
| **M3-3** | Match-3（**会话**） | 首轮 `g115-runtime-overlay` 回 `{"result": null, "result_type": "Nil"}`，`g117-shot-t6` 与 `g116` 的帧**逐字节相同**（`px_vs_prev=0`），最终场景树里**没有 `ProbeOverlay`**（68 个节点，与开头的 `g01` 一样多） | 正控代码写成了 GDScript 里的 `main.addChild(c)` —— **C# 的方法名**。GDScript 在 `add_child` 上不认 `addChild`，脚本在那一行报错，`return "overlay added"` 从未执行。引擎 stderr 里有 `SCRIPT ERROR: Invalid call. Nonexistent function 'addChild' in base 'Node2D (Match3Game.cs)'.` | **改**：改成 `main.add_child(c)`。r3：`g115` 回 `"overlay added"`、树上 69 个节点（含 `ProbeOverlay`）、`m3-t6` 与 `m3-t5` 相差 **135425 px** |
| **M3-4** | Match-3（**会话 / 测试设计**） | r2 的 `runs\match3\m3-task102-r2` 的 `g101-samples-clock` 30 帧采样里 **`AutoTicks` 从 4 一路涨到 33**，而 `Moves` 恒定 1、`Score` 恒定 30、`BoardHash` 恒定、`Refills` 恒定 3 —— 时钟在走，**盘面一格都没动**；而同一轮的 `g102`（`Moves gt 0`）、`g103`（`TotalCleared gt 0`）、`g104`（`AutoTicks gt 2`）**全部 PASS**。是**多帧采样**把它照出来的 —— 与 F-1 / B-3 一模一样的照法 | 钉板选的是 Q 盘，而 Q 上**只有一个合法交换**。`SetAutoClock(60.0)` 与第一个采样帧之间隔着两三次 MCP 调用，这段时间足够时钟把它吃掉；此后 `AutoStep` 每次都找不到合法交换，返回 0，盘面永远冻住。`AutoTicks` 是**时钟应用于多少步**，与「步有没有真的发生」无关，所以它照样在涨 —— 这正是 B-3 的教训换了个形态：**采样钉板必须是游戏能一直玩下去的状态** | **改**：①改成钉默认棋盘（LCG 生成的那一块），生成器先**在 Python 里实测**它能连做 40 次自动交换（40/40 applied、盘面确实在变）才允许写进会话；②把 `g102` 的阈值从 `gt 0` 提到 `gt 1`；③**新增断言** `g104a`（`BoardHash neq <窗口开始时的哈希>`）—— 盘面冻住从此是一条会 FAIL 的断言，而不只是采样里的一串常数。r3：`BoardHash` **26 个不同值**、`Moves` 3→32、`Score` 150→1270、`TotalCleared` 12→112、`Refills` 12→112，`g102`/`g103`/`g104`/`g104a`/`g104b`/`g105` 全 PASS |

---

### TASK-102 记录（2026-09-27）

1. **第 14、15 款（Platformer / Match-3）交付**：台账第 14、15 行来自它们自己那一轮的产物
   （`runs\platformer\plat-task102-r2\report.json`、`runs\match3\m3-task102-r3\report.json`）。
   **工具缺陷 1 条（X-1，只记录、未改模块）**（工具缺陷表新增）；「游戏或驱动缺陷」新增
   **PL-1**（载荷：世界左/右/顶边用格子相对公式解算，C# 向零截断把越界 2 px 的盒子推到 20 而不是 0）、
   **PL-2**（载荷：`Jump()` 不清 `OnGround`）、**PL-3**（会话：LEVEL1 场景的 `goal=0,0` 与
   `PSim` 的无终点状态不一致）、**M3-1**（会话：默认棋盘的探测值靠猜）、**M3-2**（会话：三种非法交换的
   计数建在新副本上而不是累计）、**M3-3**（会话：正控 GDScript 写了 C# 的 `addChild`）、
   **M3-4**（会话/测试设计：自动时钟采样的钉板只剩一个合法交换，时钟在第一个采样帧前就吃掉它，
   30 帧采样看着冻住的盘面而断言全 PASS）—— 七条都修好并在 r2 / r3 复核。
2. **每一轮的两条非 `ok` 判定都是声明过的**：`e06` 的同名批量拒绝（`-32000`，D-3 的证据）与一条
   故意打在不存在属性上的边界断言（`-32001`）。`e05`/`e09` 的 `project_read_text_file` sha
   **逐字节相同**（Platformer `0dd8bf57…`/834 B，Match-3 `7772574a…`/842 B），即被拒的批量
   **什么都没写**；两次运行的 `running_game_get_scene_tree` 共 114/115 与 68/69 个节点名里
   **0 个 `@` 开头**。
3. **独立复算不是转述**：`recovery\work\task102\recompute_readbacks.py` 不看 `report.json`、
   不看断言助手，也不看 C# —— 它把载荷**打印出来的** `Dump()` 一行行拆开，用**自己**的规则重算：
   Platformer 的 `MapHash` 由**打印出来的 ASCII 地图**重推（实心 1 / 终点 5 / 收集物 3 / 空 2）、
   `StateHash` 由同一行上的 `player=`/`vel=`/`on_ground=` 重推，Match-3 的 `BoardHash` 由**打印出来的
   数字棋盘**重推（`h = h*31 + (value+1)`，行优先），三者都是 32 位 multiply-31 链；再把会话里那些
   **由 Python 第二实现算出来的字面量**（抛物线逐帧高度与落地帧、撞墙像素、收集物三拍、掉坑两拍、
   指定交换后的整盘与哈希、连锁长度与得分、两波连锁的整盘）与载荷在**本轮响应文件里实际回报的
   `actual`** 逐条对齐。**Platformer 0 处不符、Match-3 0 处不符**（`logs\recompute-plat-r2.txt`、
   `logs\recompute-m3-r3.txt`）。
4. **「会动的证据」两路都有**：①**多帧属性采样**（先冻结基线、再自动时钟 30 帧）——
   Platformer 的冻结基线 5 个属性各 1 个值、自动疾跑 30 帧里 `PlayerX` **29 个不同值 140→252**；
   Match-3 的冻结基线 4 个属性各 1 个值、自动对局 30 帧里 `BoardHash` **26 个不同值**、
   `Moves` 3→32、`Score` 150→1270。②**像素差 + 独立复算**（逐调用对 + 保存帧）：
   Platformer **40/228**（编辑器 1/14、游戏 39/214）、Match-3 **22/145**（1/14、21/131），
   两款的 `recomputed-vs-trace mismatches` 都是 `none`，`user://` 七帧的 sha 与 `report.json`
   逐值一致、**7/7 互不相同**，帧链逐对独立复算 **0 处分歧**。
5. **时钟全部与帧率无关**：两款都是浮点累加器（`_autoAccum += delta * rate`，不用
   `(int)(delta*rate)`，即 F-1 的修法），`Elapsed` 是每帧 `+= delta` 的浮点秒表；每款另有**两个**
   独立增量属性（`LastHookSteps` = 钩子这次调用做了多少、`LastAutoSteps` = 这一帧的时钟走了多少），
   且 Platformer 的 `Ticks` 只由 `_Process` 写、`Frames` 只由固定帧写 —— **一个属性一个写者**。
   两款都在时钟跑过 30 帧之后断言 `LastHookSteps` **仍是钩子写下的那个值**。
6. **一条如实记录的采样相位现象（不是缺陷）**：Platformer 的 30 帧时钟采样里 `LastAutoSteps`
   只有 `{1, 0}` 两个值、且第 1 帧之后恒为 0，而 `AutoTicks` 同期涨了 28 —— 因为这台机器上
   引擎帧率远高于 60（采样点之间的实际间隔约 2.4 帧），累加器每 2.4 帧才凑满 1 tick，
   采样点恰好总是落在「还没凑满」的那一帧上。`LastAutoSteps` 写的是它自己那一帧的事实，
   累计量 `AutoTicks` 才是「时钟真的走了多少」。读采样时必须把两者分开读。
7. **`--import` 的关机期访问违例本轮 0 次**：五次导入（Platformer r1/r2、Match-3 r1/r2/r3）
   全部 `IMPORT_EXIT=0`、`import.stderr.txt` 0 字节。累计口径由 3/23 变成 **3/28**（待办 2 不变）。
8. **门跑器**：本轮**没有模块字节改动**（引擎仓 `git status` 空、`git diff --name-only 2385fe2fb..HEAD`
   仍只有两份 `.md`），因此按 TASK-099 的预检直接判 `ANCHOR_STRUCTURAL_EQUIVALENT` +
   `RESULT=SKIP_REBUILD` + `GATES_SKIPPED=1`（exit 0，`runs\gates\task102-doconly\summary.txt`）——
   **如实说明：十道门本轮一门未跑**，没有重建、没有 push 代码（X-1 只是记录，没有动模块）。
9. **模板增补（写给下一款）**：①**第二实现要覆盖「生成出来的」默认状态**，不只是被钉住的盘面 ——
   M3-1 的猜测字面量只有复算 `BuildBoard()` 才能消掉；②**采样钉板必须先证明它能一直动** ——
   M3-4 的教训，生成器应先在 Python 里实测「这段窗口它能动多少次」再写进会话；
   ③**把「采样期间状态没变」做成会 FAIL 的断言**（`neq` 一个窗口开始时的哈希），
   而不是只靠采样里的一串常数；④**世界边界的碰撞解算不要复用地图内部的格子相对公式** ——
   C# 的整数除法向零截断，负方向的世界边界会给出反直觉的答案（PL-1）；
   ⑤半掩的错误最危险：`execute_gdscript` 的 `ok` 不等于脚本执行成功，必须配像素差与场景树证据（X-1）  **TASK-103 已修**：运行期错误回 `-32000` + `data.script_error` + `data.suggestion`，成功但无返回值带 `note`，错误同时进 trace 的调用行；两变体已在该提交后重建、十道门重跑。。


---

### TASK-103 记录（2026-09-27）

1. **工具缺陷 X-1 修在根上并重建两变体**（本轮唯一一次动 `modules\mcp_server`）。现场是 TASK-102 的 `m3-task102-r1/g115-runtime-overlay`：
   脚本能编译、执行时调了 C# 拼写的 `addChild`，VM 中止该帧、只把 `SCRIPT ERROR` 打到引擎 stderr，而工具回
   `ok` + `{"result":null,"result_type":"Nil"}` —— 没有错误码、没有消息、没有建议，「脚本炸了」与「脚本跑了但没有可见副作用」在答复里无法区分。
   修法用的是**引擎自己的错误处理器**（解析捕获已经在用的那个钩子）：`GDScriptFunction::call()` 把中止的帧
   经 `_err_print_error(..., ERR_HANDLER_SCRIPT)` 报出来（`gdscript_vm.cpp:3988`，在 `#ifdef DEBUG_ENABLED` 里，而本模块所有门跑的都是
   `target=editor` → 该宏生效）。窗口恰好是一次 `Callable::callp`，所以窗口里每一条 `ERR_HANDLER_SCRIPT` 都是这次调用造成的；
   用 `ERR_HANDLER_SCRIPT`（而不是 `ERR_HANDLER_ERROR`）正是为了不把脚本自己的 `push_error()` 算成失败。
   * 错误码 **`-32000`（`tool_state`）**，不是 `-32602`（脚本**编译通过**了，语法没问题）也不是 `-32603`（不是本模块坏了）；
     `data.script_error` 带引擎原文、`code` 的行号、生成源行号、脚本路径、被点名的 GDScript 函数、错误条数与全部消息，`data.suggestion` 给出改法；
     **列号如实报为 `null`** —— 引擎给处理器的只有行号。
   * 生成脚本的身份**按 GDScript 自己的造法重建**（`gdscript://<instance id>.gd`，`gdscript.cpp:1337`），而不是读
     `Script::get_path()`：那是 `Resource::get_path()`，答的是**路径缓存**、对未从资源加载的脚本恒为空 —— 实测运行时错误点名
     `gdscript://-9223371484028730203.gd` 而 `get_path()` 答 `""`。答复里两个字符串都给，比较可审计。
   * 成功路径：`result` 为 `null`/`Nil` 时带 `note`（没有 `return` 的脚本与全是空操作的脚本答的都是 null）。
   * 描述与 C++ 注册字面量走生成器的 **append-only override**（键 `execute_game_script`）重新生成；契约**六项形状量一字未变**
     （`count=177`、`added_count=6`、`generator_version=1.22.0`、编辑器可见 154、游戏可见 73、**幂等**：连续两次生成同为
     sha256 `bd68e8047…`），契约文件 151 367 B / `64ddce9f…` → 153 330 B / `bd68e804…`，`_meta.overrides` 仍 34（改的是既有条目，不是新增）。
   * doctest：新增一例把三种情形分开钉住（解析失败 `-32602`；运行期错误 `-32000` + `data.script_error` 与它的行映射；成功有值 / 成功无值后者带 `note`），
     外加一条 `push_error()` 控制（**不得**变成拒绝）；TASK-090 的挂载用例在自己的失败路径上改为断言结构化拒绝。模块用例 **156 → 157**。
   * **最小同批复现（修前 / 修后并列）**：同一份六调用会话**逐字不改**跑两次 ——
     `runs\match3\task103-x1-before` 的 `g01` 回 `ok` + `{"result":null,"result_type":"Nil"}`（无码无消息）；
     `runs\match3\task103-x1-after` 的 `g01` 回 **`-32000`** + `data.script_error`（`line=7`、`generated_line=10`、`function=_mcp_execute`、
     `script_path=gdscript://-9223371989626911104.gd`、`in_generated_body=true`、`error_count=1`）+ `data.suggestion`。
     同一批里的正控 `g03`（把 `addChild` 改成 `add_child`）两次都回 `"overlay added"`（**没有过度报错**）；`g05`（无 `return` 的脚本）修后带 `note`；
     `g06`（解析失败）两次都是 `-32602` 且 `parse_error` 逐字未变；引擎 stderr 里那条 `SCRIPT ERROR` **仍然在**（处理器是纯追加的）。
   * **错误也进 trace**：`task103-x1-after` 的调用行（`seq=1`）带 `error_code=-32000`、`error_message` 与整段 `error_data_json`。
2. **第 16、17 款交付**：台账第 16、17 行来自它们自己那一轮的产物（`runs\towerdefense\td-task103-r3\report.json`、
   `runs\missilecommand\mc-task103-r3\report.json`）。两款 `facts_complete` 都是 **100%**（145/145、127/127）。
   两款每一轮的非 `ok` 判定都是**声明过的**：编辑器相那一次同名批量（`-32000`）与一条故意打在不存在属性上的边界断言（`-32001`）。
3. **缺陷清单（分两栏）**：
   * **工具缺陷（`modules\mcp_server`）：0 条**。本轮唯一的模块改动是 A 段**主动**修 X-1（不是新发现），修完两变体重建、十道门重跑。
   * **游戏或驱动缺陷：4 条**
     | id | 层 | 现象（证据） | 根因 | 处置 → 重跑结果 |
     |---|---|---|---|---|
     | **MC-1** | Missile Command **载荷** | r1 的 `g02-assert-field-w` 回 `-32001`（`Property 'FieldW' on node '/root/Main' not found`），`g12-readback-t0` 回 `-32000`「`Nonexistent function 'Dump' in base 'Node2D'`」 | `PosAt` 是实例方法，却被 `static AddMissiles` 调用 → `CS0120`；`project_build_csharp` exit 1、`project_validate_scripts invalid_count=1`，**脚本没挂上**，根节点退化成裸 `Node2D` | `PosAt` 改 `static`（它本来就不碰实例状态）；r2/r3 编译 exit 0、脚本挂上、全部断言通过。**这条正是 X-1 修好之后第一次受益**：旧行为下 `Dump` 会静默回 `ok`+`null`，人只会看到「断言全不对」而不知道脚本根本没挂上 |
     | **MC-2** | Missile Command **会话** | r2 的 `g18b-assert-probe-state` 期望 `city` 实得 `ground`、`g19b` 期望 `battery` 实得 `ground`，而同刻 `g18a`/`g19a`（`ProbeValue`）全 PASS | 三条 `ProbeState` 断言写在探针循环**之后**，读到的是**最后**那次探针（(400,300)）的状态 —— 与 PL-3 / K-1 / M1 同一类：期望值必须引用它所断言的那**一刻** | 每次探针后立刻断言它的两个属性；r3 全 PASS |
     | **TD-1** | Tower Defense **会话** | r1 的 `g53-assert-towers` 期望 3 实得 0、`g53a-assert-gold` 期望 850 实得 0、`g55-assert-won` 期望 true 实得 false …… **11 条同时 FAIL**，`Steps` 实得 544、`Lives` 实得 0 | 「一整局」那一段**漏了 `ForceTestState` 调用**：三座塔建在上一段钉住的 `gold=0` 状态上，全被 `no_gold` 拒绝，`StepFrames(4000)` 于是在无塔场地上把 5 条命跑光 | 补上 `g49-play-setup` 的 force 调用；r2/r3 全 PASS（`TowersPlaced=3`、`Gold=850`、`Won=true`、`Steps=306`、`Killed=15`、`Leaked=0`） |
     | **TD-2** | Tower Defense **会话 / 证据设计** | r2 的编辑器相像素列 **0/14 非零**，而 r1 是 1/14（`editor_add_nodes_batch` 213 012 px） | r2 **没有从模板重新实例化**：工程里已有上一轮建的三个静态节点，首次同名批量被 `-32000` 拒绝，于是「一次批量建好三个静态节点」这一步在本轮**根本没有发生** | 归档 + 重新实例化后重跑（先写 sha256 清单再 `Move-Item`，全程零删除）；r3 编辑器相像素 1/14 非零（213 012 px） |
   * **取证工具自身 1 条（`R-1`，**不是**模块缺陷、也不是游戏缺陷）**：`recompute_readbacks.py` 第一版把 `Dump()` 行里 `last=<LastEvent>` 的片段也当成了字段，
     而 `StepFrames` 的 readback 恰好含 `incoming=0` —— 它覆盖了真正的 `incoming=<列表>`，解析器随后在 `m[1]` 上抛 `IndexError`。
     修法：只取 `last=` 之前的部分（`dump_fields`），并让列表解析对字段数做断言；修后两款各 **0 处不符**。
4. **「像素差 + 独立复算」两款的真实数值**：Tower Defense **31/145**（编辑器 1/14、游戏 30/131），
   `user://` 五帧 **185084 / 8356 / 3376 / 8133 px**；Missile Command **21/127**（1/14、20/113），五帧 **15823 / 13578 / 4370 / 346 px**。
   两款的 `recomputed-vs-trace mismatches` 都是 `none`，保存帧 sha 与 `report.json` 逐值一致、**5/5 互不相同**，
   帧链逐对独立复算 **0 处分歧**；`recompute_readbacks.py` 还**只从打印出来的** `Dump()` 重算哈希
   （TD 的 `MapHash` 由 ASCII 重推、`PathHash` 由**重新走一遍**导出的路径重推；MC 的 `CityHash`/`WorldHash` 由打印出来的城市位、两张导弹表、爆炸表与 `score`/`wave`/`steps` 重推），
   并把生成器记录的每一条期望字面量与响应里**实际回报的 `expected`** 逐条对齐：TD **75/75 + 1 条声明边界**、MC **71/71 + 1 条声明边界**，合计 **0 处不符**。
5. **时钟与单写者（继承 G1/F-1/M3-4）**：两款都是浮点累加器（`_autoAccum += delta * rate`），`Elapsed` 是每帧 `+= delta` 的浮点秒表；
   每款各有 `LastHookSteps`（钩子）与 `LastAutoSteps`（每帧时钟）**两个**属性，且都在采样里出现过；
   两款都在时钟跑过 12 帧之后断言 `LastHookSteps` **仍是钩子写下的那个值**。
   **M3-4 的教训写进了断言本身**：两款的采样后面都跟着 `Steps gt 0` / `EnemiesSpawned(Spawned) gt 0` / `AutoTicks gte 1` 三条**会 FAIL 的硬断言**，
   所以「时钟在走而世界冻住」不再是采样里的一串常数，而是一条红。
6. **模板增补（写给第 18 款）**：①**每一段测试都必须从它自己的 `ForceTestState` 开始** —— TD-1 的成因是「上一段钉住的状态」被下一段继承；
   ②**重跑必须从模板重新实例化**（先写 sha256 清单再移动工程），否则编辑器相的第一步会在上一轮的工程上被同名拒绝（TD-2）；
   ③**载荷里的 `static` 方法只能调 `static` 方法** —— MC-1 的 `CS0120` 让整份脚本没挂上，而这类失败在修好 X-1 之后**第一次**由工具自己说了出来；
   ④**断言要紧挨着它引用的那一刻**（MC-2，与 PL-3/K-1/M1 同源）；⑤**取证脚本自己也要能读错**：`last=` 之后的 `key=value` 片段会覆盖真字段（R-1）。
7. **门跑器**：本轮**改了模块**（X-1），因此**重建两个变体 + 十道门全绿 + `accept_m1` 22/22**都跑了，真实退出码与逐门结果见
   `recovery\reports\TASK-103-REPORT.md` §C 与 `runs\gates\task103\summary.txt`。引擎仓提交 `1c7f5c07a1`（模块提交），
   两变体都在该提交之后重建，锚点自报 `4.8.dev.mono.custom_build.1c7f5c07a` / `4.8.dev.custom_build.1c7f5c07a`。
8. **`--import` 的关机期访问违例本轮 0 次**：TD 的 r1/r2/r3 与 MC 的 r1/r2/r3 六次导入全部 `IMPORT_EXIT=0`、`import.stderr.txt` 0 字节。累计口径 **3/34**（待办 2 不变）。



---

### TASK-104 记录（2026-09-27）

1. **第 18、19、20 款交付**，D138 的「至少 20 个经典小游戏、全部 C#」到此收口。三款都从**模板实例化**
   （`tools\new_game.ps1`），**游戏内容全部由 MCP 调用写成**：`project_edit_script` 写 C# 载荷、
   `editor_add_nodes_batch` 一次建好三个静态节点（`Background`/`Hud`/`Status`，其后再不许静态节点）、
   `editor_add_input_action` 声明一个动作、`editor_save_scene`、`project_build_csharp`、`project_validate_scripts`；
   游戏相全部是 `running_game_*`。三款的调用数、判定分布与 `facts_complete` 见上面第 18/19/20 行，
   全部取自各自那一轮的 `report.json` / `ledger-*.txt`。
2. **固化模板照用并再添两条**：
   * 既有：批量建静态节点 → 运行期创建动态对象 → 只钉游戏本身可达的状态 → 先采样、后改变 → 故意重跑同名批量 →
     帧率无关步进 → 一个属性一个写者 → 采样带「必须动」硬断言 → 像素差 + Python 第二实现独立复算；
     以及 TASK-103 的「每段测试从自己的 `ForceTestState` 开始」「重跑从模板重新实例化」「`static` 只能调 `static`」
     「断言紧挨它引用的那一刻」「取证脚本自己也要能读错」。
   * **新增（写给第 21 款起）**：①**两态动作要成对测**（本题连发/脉冲、发射/瞄准，`Thrust()` 与 `SetThrust()` 是两种写者，
     各有断言）；②**每一条容差的边界两侧都要测**，而且**越界的“存活侧”也要测**—— LL 的 330° 存活证明容差是两侧的，
     只测 90° 坠毁会让人误以为“必须恰好正立”。
3. **缺陷清单（分栏）**：
   * **工具缺陷（`modules\mcp_server`）：0 条。** 本轮**没有改动模块任何一个字节**，因此 §C 的收尾走的是
     **免跑判定**（`run_gates.ps1` 纯文档预检 → `ANCHOR_STRUCTURAL_EQUIVALENT` + `SKIP_REBUILD`），
     十道门与 `accept_m1` **未重跑**，原因与判定见 `recovery\reports\TASK-104-REPORT.md` §C 与本文件末尾。
   * **一行诚实记录（不是缺陷）**：`project_validate_scripts` 在 rtype r2 上回 `not_compiled_count=1`
     （`category=not_compiled`，理由是「构建产物里没有这个源文件的记录」）；同一条工具在 pb r1 上回 `valid=true`。
     TD/MC（TASK-103）当时也是 `not_compiled=1`。三次的 `invalid_count` 都是 0、`project_build_csharp` 都是 exit 0，
     所以这是**判定类别随时序变化的既有边界**（工具自己把理由写清楚了），不是回归，也不构成本轮的游戏缺陷。
   * **游戏或驱动缺陷：1 条**
     | id | 层 | 现象（证据） | 根因 | 处置 → 重跑结果 |
     |---|---|---|---|---|
     | **RT-1** | R-Type **会话** | r1 的 `g114-assert-rejected` 期望 `RejectedMoves=0` 实得 **1**（同段 `g112` 期望 `BulletsFired=0` 恰好也是 0，所以没照出另一半） | 生成器只把调用发出去、**没有让自己那份 `RSim` 跟着走同一步**：游戏结束后的 `FireBullet()` / `MovePlayer()` 在载荷里被拒并计数，而在 `RSim` 里这两次调用根本没发生 | 补 `lose.fire()` 与 `lose.move(8, 0)`；按 TD-2 的教训**从模板重新实例化**（先写 sha256 清单再 `Move-Item`）后重跑 r2 → `101 PASS / 0 FAIL` |
   * **取证工具自身 2 条（`E-1`，明确**不是**模块缺陷、也不是游戏缺陷）**：都在本轮新写的
     `recovery\work\task104\recompute_readbacks.py` 里。
     ①哈希复算分支写成了 `"state_hash=" in fields`，而 `fields` 是**字典**（键不含 `=`）→ 条件恒假 →
     两款各只算到 **2 个哈希**（本该更多）却仍报 `0 处不符` —— **静默少算**，比报错更危险；
     改成 `"state_hash" in fields` 后 R-Type/PB/LL 各 2 个 `Dump()` 读数全部参与复算。
     ②`SetThrust` 的回读按 `text.split("=",1)[1].strip()=="True"` 解析，实得 `"True fuel=500"` → 恒假 →
     LL 的独立重放**从头到尾没开过火**，报了 **10 处不符**（`g115`/`g125` 的 `steps`/`y`/`vy`/`fuel`）；
     改成 `grab(text, "thrust_on") == "True"` 后 **17 个检查点 0 处不符**。
     ②的意义在**它响了**：这条复算脚本没有和载荷“互相迁就”地静默同意，而是把 10 条不一致摆出来，
     才让人去分清「是载荷错了」还是「是复算脚本错了」—— 上一轮 R-1 的教训（取证脚本自己也要能读错）在这里第二次应验。
4. **「像素差 + 独立复算」三款的真实数值**：R-Type **87/223**（编辑器 1/14、游戏 86/209），
   `user://` 四帧 **2069 / 7095 / 7547 px**；Puzzle Bobble **29/157**（1/14、28/143），四帧 **53444 / 18251 / 2929 px**；
   Lunar Lander **41/230**（1/14、40/216），四帧 **6798 / 1117 / 6885 px**。
   三款的 `recomputed-vs-trace mismatches` 都是 **0**，保存帧 sha 与 `report.json` 逐值一致、**4/4 互不相同**，
   帧链逐对独立复算 **0 处分歧**；`recompute_readbacks.py` 还独立重算了
   R-Type 的 `StateHash`（由打印出来的 `player`/`enemies`/两张子弹表重推）、
   Puzzle Bobble 的 `BoardHash`（由打印出来的棋盘重推）**与初始棋盘本身**（同一条 LCG + 同一个稳定循环）、
   Lunar Lander 的 `StateHash` **与整条积分轨迹**（按 `call-index.txt` 的调用顺序重放，17 个检查点）。
5. **时钟与单写者（继承 G1/F-1/M3-4）**：三款都是浮点累加器（`_autoAccum += delta * rate`），
   `Elapsed` 是每帧 `+= delta` 的浮点秒表；三款各有 `LastHookSteps`（钩子）与 `LastAutoSteps`（每帧时钟）**两个**属性，
   且都在采样里出现过；三款都在时钟跑过 12 帧之后断言 `LastHookSteps` **仍是钩子写下的那个值**。
   **M3-4 的教训写进断言本身**：三款的采样后面都跟着会 FAIL 的硬断言（`Steps gt 0` 与一个 `neq 窗口起始哈希`），
   所以「时钟在走而世界冻住」不再是采样里的一串常数，而是一条红。


---

## 里程碑：20 款（TASK-104 收口）

* **口径**：D138 —— 轮次不设限，至少 20 个经典小游戏、**全部 C#**，每款都要有可复算的「操作有效性」证据。
  TASK-104 交付第 18/19/20 款，口径达成。

### 20 款一览（每行一款；调用数 = 编辑器 / 游戏，`facts` = 可重建事实齐全的调用占比）

| # | 游戏 | 会话调用数 | `facts_complete` | 像素差（非零 / 可比） | 独立复算 | 缺陷（工具 / 游戏或驱动） | 证据路径 |
|---|---|---|---|---|---|---|---|
| 1 | Pong | 23 / 29（52） | 52/52（100%） | 14/74 | 0 处不符 | 0 / 6 | `runs\pong\pong-clean-task097` |
| 2 | Breakout | 21 / 34（55） | 55/55（100%） | 14/89 | 0 处不符 | 0 / 5 | `runs\breakout\breakout-clean-task097` |
| 3 | Snake | 20 / 31（51） | 51/51（100%） | 13/102 | 0 处不符 | 0 / 4 | `runs\snake\snake-clean-task097` |
| 4 | Tetris | 6 / 36（42） | 42/42（100%） | 11/42 | 0 处不符 | 0 / 3 | `runs\tetris\tetris-task096-r2` |
| 5 | Space Invaders | 15 / 44（59） | 59/59（100%） | 12/59 | 0 处不符 | 0 / 0 | `runs\spaceinvaders\si-task097-r1` |
| 6 | Asteroids | 16 / 55（71） | 71/71（100%） | 16/71 | 0 处不符 | 0 / 1 | `runs\asteroids\ast-task098-r2` |
| 7 | Pac-Man | 16 / 64（80） | 80/80（100%） | 15/80 | 0 处不符 | 0 / 1 | `runs\pacman\pac-task098-r2` |
| 8 | Frogger | 16 / 74（90） | 90/90（100%） | 17/90 | 0 处不符 | 0 / 0 | `runs\frogger\frog-task099-r1` |
| 9 | Flappy Bird | 14 / 78（92） | 92/92（100%） | 22/92 | 0 处不符 | 0 / 1 | `runs\flappy\flappy-task099-r2` |
| 10 | 2048 | 16 / 113（129） | 129/129（100%） | 26/129 | 0 处不符 | 0 / 1 | `runs\game2048\2048-task100-r2` |
| 11 | Minesweeper | 14 / 141（155） | 155/155（100%） | 21/155 | 0 处不符 | 0 / 1 | `runs\minesweeper\mine-task100-r2` |
| 12 | Sokoban | 14 / 176（190） | 190/190（100%） | 29/190 | 0 处不符 | 0 / 1 | `runs\sokoban\soko-task101-r2` |
| 13 | Bomberman | 14 / 219（233） | 233/233（100%） | 45/233 | 0 处不符 | 0 / 3 | `runs\bomberman\bomb-task101-r4` |
| 14 | Platformer | 14 / 214（228） | 228/228（100%） | 40/228 | 0 处不符 | 0 / 2 | `runs\platformer\plat-task102-r2` |
| 15 | Match-3 | 14 / 131（145） | 145/145（100%） | 22/145 | 0 处不符 | 1 / 4（X-1 已于 TASK-103 修） | `runs\match3\m3-task102-r3` |
| 16 | Tower Defense | 14 / 131（145） | 145/145（100%） | 31/145 | 0 处不符 | 0 / 1 | `runs\towerdefense\td-task103-r3` |
| 17 | Missile Command | 14 / 113（127） | 127/127（100%） | 21/127 | 0 处不符 | 0 / 3 | `runs\missilecommand\mc-task103-r3` |
| 18 | **R-Type** | 14 / 209（223） | 223/223（100%） | **87/223** | **0 处不符** | **0 / 1** | `runs\rtype\rt-task104-r2` |
| 19 | **Puzzle Bobble** | 14 / 143（157） | 157/157（100%） | **29/157** | **0 处不符** | **0 / 0** | `runs\puzzlebobble\pb-task104-r1` |
| 20 | **Lunar Lander** | 14 / 216（230） | 230/230（100%） | **41/230** | **0 处不符** | **0 / 0** | `runs\lunarlander\ll-task104-r1` |

合计 **2 554 次调用**（编辑器 303 / 游戏 2 251），`facts_complete` **20 款全部 100%**。
（这个和逐行重算过：把上面 20 行的「编辑器 / 游戏」两列分别相加得到 303 / 2 251。）

### 证据覆盖率

* **像素证据：20/20 款可得且非零。** 每一款都有「逐调用捕获对里非零的组数」与「`user://` 保存帧链」两路；
  帧链逐对（engine 规则 >10 与 any-difference 两套）**都由 `pixel_recompute.py` / `frames_recompute.py` 独立重算**，
  与 `report.json` **逐对一致（0 处分歧）**。第 1–3 款的像素列是 TASK-097 清理副本层后**回填**的（见 D-1 结案节）。
* **独立复算：20/20 款。** 每一款都有「从规则重写的 Python 第二实现」产出会话里的断言字面量
  （`recovery\work\task{task}\make_session_<game>.py`），并且事后有一支**不 import 生成器、不看 `report.json`、不看 C#**
  的复算脚本（`recompute_readbacks.py` 等）把打印出来的状态重算一遍：哈希、地图/路径/棋盘、整数轨迹、逐格爆炸范围、
  消除与掉落结果。**20 款合计 0 处不符。**
* **事后复算的能力清单（截至 TASK-104）**：R-Type `StateHash`（由打印列表重推）、
  Puzzle Bobble `BoardHash` **与初始棋盘本身**（LCG + 稳定循环重算）、
  Lunar Lander `StateHash` **与整条 35 步积分轨迹**（按 `call-index.txt` 顺序重放，17 个检查点）、
  Tower Defense `MapHash`/`PathHash`（重走一遍路径）、Missile Command `CityHash`/`WorldHash`、
  Platformer `MapHash`/抛物线、Match-3 整盘与连锁、Sokoban/Bomberman/2048/Minesweeper 的哈希与逐格结果。

### 工具缺陷累计清单与修复轮次

| id | 现象 | 修复轮次 | 状态 |
|---|---|---|---|
| **D-3** | `editor_add_nodes_batch` 对同名节点既不拒绝也不报告 → `.tscn` 里进整份副本层（也是 D-1 的真因） | **TASK-097** | 已修；20 款每一轮的编辑器相都**故意重跑同名批量**，`-32000` + `data.conflicts` 成为常态化证据 |
| **D-1** | 像素回读恒返回第一帧 | **TASK-097（D-3 的副产物）** | 已结案；三个老场景的副本层已删，像素列已回填 |
| **D-2** | `accept_m1.ps1` 的就绪判据是吞吐（≥20 fps）而不是就绪 | **TASK-094** | 已修（改为 `frame_count` 连续 6 次严格递增） |
| **G-1** | `run_gates.ps1` 的锚点默认值落后于引擎仓 HEAD | **TASK-099** | 已修（锚点取二进制自己的 `--version` + 纯文档预检跳过） |
| **X-1** | `running_game_execute_gdscript` 的脚本**运行期报错**回 `ok` + `null`，诊断只落引擎 stderr | **TASK-103** | 已修（`-32000` + `data.script_error` + `data.suggestion`；成功但无返回值带 `note`；错误进 trace），修后两变体重建、十道门全绿 |
| **X-2（观察，未修）** | `project_validate_scripts` 的 `valid` 有时缺席（`not_compiled_count=1`，工具自己写明理由），同一命令在另一轮回 `valid=true`；三次的 `invalid_count` 都是 0 | —— | **只记录**：它是工具自己说清楚的判定类别，不是回归；修它要动模块 → 重建两变体 + 十道门，本任务的范围与 C) 分支都不含此改动 |
| **R-1 / E-1** | **取证脚本自身**的两类读错（`last=` 之后的片段覆盖真字段；字典成员判断写成带 `=` 的字符串；`True fuel=500` 当成 `True`） | TASK-103 / TASK-104 | 已修；另一件**证据**：E-1 的第二个 bug 是**响亮地**报出 10 处不符才被发现的 —— 复算脚本必须能喊 |

### `--import` 累计口径

* **崩溃形态（`exit=-1073741819` / `0xC0000005`，stderr 只有 `Parameter "singleton" is null.`）**：
  TASK-099 留档时是 **3/23**，此后台账口径按轮推进 **3/28**（TASK-102）→ **3/34**（TASK-103）→
  **本轮 3/38**：TASK-104 的 **4 次导入全部 `IMPORT_EXIT=0`**、其中 3 次 `import.stderr.txt` 0 字节。
  也就是说：**3/23 这个标记之后，台账口径走过 23→28→34→38 共 15 次导入、0 次复现。**
  （不要把 TASK-099 的 3/23 当成 TASK-100 之前的基数 —— 它是那一轮**结束时**的标记，这才是台账里
  `3/13 → 3/17 → 3/23 → 3/28 → 3/34` 这条链的含义。）
* **非崩溃形态（同样的 `singleton` 行 + `Thread::~Thread` 警告，但 `IMPORT_EXIT=0` 且导入已跑完）**：
  TASK-104 出现 **1 次**（`runs\rtype\rt-task104-r1`，stderr 307 B）。它印证 TASK-099 的定位：
  这条消息是**关机期**的，不是导入失败；`IMPORT_EXIT` 仍然不能当健康信号用。

### 下一步：独立验收入口（TASK-105）

验收子代理应当**只**读下列文件与命令，不读本轮的总结文字：

**要读的工件（按顺序）**

1. `recovery\reports\TASK-104-REPORT.md` —— 本轮结论、逐条证据与遗留。
2. `godot-mcp\GAME-LOOP-LOG.md` —— 台账第 18/19/20 行、`### TASK-104 记录`、本节（里程碑）。
3. `F:\moonbit-hof-rs\DECISIONS.md` 的 **D152** —— 本轮的决策与被否决选项。
4. 三份载荷（**唯一**的游戏实现）：
   `godot-mcp\tools\sessions\rtype\payload\RTypeGame.cs`、
   `...\puzzlebobble\payload\PuzzleBobbleGame.cs`、
   `...\lunarlander\payload\LunarLanderGame.cs`。
5. 三份会话（**唯一的调用序列**）：`tools\sessions\{rtype,puzzlebobble,lunarlander}\session.json`。
6. 三份生成器 + Python 第二实现：`recovery\work\task104\make_session_{rtype,puzzlebobble,lunarlander}.py`。
7. 三份期望清单：`recovery\work\task104\expectations-{rtype,puzzlebobble,lunarlander}.json`。
8. 三份运行产物：`runs\rtype\rt-task104-r2\`、`runs\puzzlebobble\pb-task104-r1\`、`runs\lunarlander\ll-task104-r1\`
   （`trace-*.jsonl` / `ledger-*.{txt,json}` / `report.{md,json}` / 每调用一个 `<tag>.json` / `call-index.txt` / `shots-*/`）。
9. 本轮自己的证据日志：`recovery\work\task104\logs\{assert,recompute,pixel,frames,facts,pixelpairs,checksession-py}-<game>.txt`。

**可以自己跑的命令（都是只读）**

```
python tools\game_report.py  <run-dir> --game=<game> --run-tag=<tag>          # 重算台账/像素/帧链
python recovery\work\task104\assert_summary.py <run-dir>                     # 逐属性断言分栏
python recovery\work\task104\recompute_readbacks.py <run-dir> recovery\work\task104\expectations-<game>.json <game>
python recovery\work\task104\pixel_recompute.py   <run-dir>                  # 逐调用捕获对，两套阈值
python recovery\work\task104\frames_recompute.py  <game> <prefix>-t <run-dir> # 保存帧链 + 与 report.json 对账
python recovery\work\task104\game_facts.py        <run-dir>                  # 构建/校验/@-名/台账事实
python recovery\work\task104\check_session.py     tools\sessions\<game>\session.json
powershell -File recovery\work\task104\check_session_ps.ps1 -Session tools\sessions\<game>\session.json -Label <game>
```

**应当主动构造的反例**

* 把 `expectations-<game>.json` 里任意一条 `expected` 改掉，重跑 `recompute_readbacks.py` —— 它必须报 `LITERAL`/`FAILED`，
  否则「字面量对齐」不是一条真检查。
* 用 `python make_session_<game>.py` 重新生成会话，与仓里的 `session.json` 逐字节比对 —— 生成器必须是**确定性**的。
* 对三款各挑一条**越界的存活侧**断言（LL 的 330°、PB 的 `|Vy|` 边界、R-Type 的钳位）核对它真的在容差之内。
* **不重跑十道门**：本轮**没有改动 `modules\mcp_server` 任何一个字节**，所以 §C 走的是免跑判定；
  验收若要跑门，请先自己确认引擎仓的工作树与 TASK-103 的 `1f9d0cb1c9` 之间没有编译输入差异
  （`git -C godot-mcp\godot status --short` 与 `git diff --stat 1f9d0cb1c9..HEAD -- modules\mcp_server`）。

## 待办

1. **D-1 结案（TASK-097）**：D-3 的根因动作已落进模块（`editor_add_nodes_batch` 默认拒绝同名，`on_name_conflict: "rename"` 才改名且 `editor_save_scene` 会报告），三个老游戏的副本层已用 `editor_delete_node` 逐个删除并复核，像素差列已回填真实数值（Pong 14/74、Breakout 14/89、Snake 13/102，逐对独立复算一致）。复现命令：`powershell -File tools\run_game_session.ps1 -Game pong -Session tools\sessions\pong\session-clean-task097.json -RunTag x -EditorPort 9916 -GamePort 9917`（breakout / snake 同理，会话名同款）。
   最小同批复现的修前/修后：`runs\pong\d3-before`（副本进 `.tscn`）对 `runs\pong\d3-after-r2`（`-32000` + 文件 sha 不变）。
2. **`--import` 的间歇性退出码（TASK-099 仍**未**结案，如实留档）**：`--import` 偶发以 `exit=-1073741819`（`0xC0000005`）退出，stderr 只有
   `ERROR: Parameter "singleton" is null.` / `at: EditorNode::is_cmdline_mode (editor\editor_node.cpp:6750)`，
   而且**导入本身已经跑完**（日志已到 `[ DONE ] loading_editor_layout`，23 行 stdout），即**关机期崩溃、不是导入失败**。
   累计 **3 次 / 23 次会话导入**（TASK-097 的 `d3-after` 首轮、TASK-098 的 `ast-task098-r1`、TASK-099 的 `frog-task099-r1` 首轮；TASK-100 的 4 次与 TASK-101 的 6 次导入全部 `IMPORT_EXIT=0`）；
   同一轮的对照组 `flappy-task099-r1` 首次导入 `exit=0`（**同样是全新工程**，所以「全新工程」本身不是判别器）。
   已排除/未复现：项目语言（C# 与 GDScript 各 12 次全 0）、冷热（首次扫描与热导入各 12 次全 0）、唯一端口（24 次全 0）、
   stock 4.7.1 mono（24 次全 0）；TASK-099 又加上：**默认端口 9877**（真实会话的做法，TASK-098 16 次全 0）、
   全新副本的 fresh/warm（TASK-099 12 次全 0）、**8 个 CPU 烧机进程加压**（TASK-099 12 次全 0）—— 见
   `recovery\work\task099\logs\importprobe\probe2-frog-load0.json` 与 `probe2-frogload-load8.json`。
   静态定位方向：`EditorNode::is_cmdline_mode()` 在引擎里**只有一个调用者** ——
   `EditorFileSystem::_process_update_pending()`（`editor\file_system\editor_file_system.cpp:2301`），
   而它是 `call_deferred` 排上来的脚本类信息更新；这条路径在编辑器析构之后再跑就会撞上 `singleton == null`。
   **下一步该做的判别（TASK-099 未做，按要求留档不猜改）**：三个判别器（在该调用点埋点 / 把 `ERR_FAIL_NULL_V`
   换成静默空检查以区分「只是警告」与「同帧其它空解引用」/ 仍崩则用 procdump 拿真实栈）**都要动引擎源码并重建两变体**；
   本轮把「现场记录 + 受控统计」这两件不动引擎的事做完了（见上），而按需复现仍不成立，因此在拿到可复现配方之前
   **不改引擎、不重建**。探针：`recovery\work\task099\import_crash_probe2.ps1`。
   **对跑测试的实际影响**：它不影响导入结果，但意味着 `IMPORT_EXIT` **不能**当健康信号用
   （`run_game_session.ps1` 现在只在日志里记一行，不据此判失败）。
3. **残留（不阻塞）**：①`editor_add_node`（单个）仍保留引擎改名语义，但它在自己的响应里明确回报 `name`，TASK-097 **故意未改**（改动会再动一份契约）；②`editor_save_scene` 每编辑器会话重发场景 `uid` 的行为**未修**（已在 D-1 结案节登记，项目内无 uid 引用）；③TASK-097 记的「`g14` 那种飞行采样开始太晚」的会话设计局限**已在 TASK-098 改正**（Asteroids 的 `g15` 先布置 150 px 外的子弹再采 40 帧，飞行与击杀落在同一窗口内），本条可以关掉。
4. 台账已续到第 9 行（第 8 款 Frogger `runs\frogger\frog-task099-r1`，90/90 facts、像素差 17/90 非零；
   第 9 款 Flappy Bird `runs\flappy\flappy-task099-r1`，92/92 facts、像素差 21/92 非零；两款首轮零缺陷）；
   下一款建议继续复制同一套模板（静态节点用批量工具一次建好、动态对象在运行期新建、`ForceTestState` 一个调用
   钉死状态、**多帧采样先于会改变状态的那一步**、**任何「钩子做了多少」都做成与帧率无关的增量属性**），
   并在建场景的那一步**故意再跑一次同名批量**，让 D-3 的拒绝在每一轮的证据里都留下一条。
   **（TASK-100 续）** 台账已到第 11 行（第 10 款 2048 `runs\game2048\2048-task100-r2`，129/129 facts、
   像素差 26/129 非零；第 11 款 Minesweeper `runs\minesweeper\mine-task100-r2`，155/155 facts、
   像素差 21/155 非零）。模板再加一条：**一个属性只能有一个写者** —— 同一个「做了多少」的量若既被
   固定步长钩子写、又被每帧时钟写，断言读到的就不是它要证的那个生产者的事实（**G1**）；两款因此各有
   `LastHookSteps`（钩子）与 `LastAutoSteps`（每帧时钟）两个属性，且都在采样里出现过。
   下一款（第 12 款）继续复制同一套模板：静态节点一次批量建好、动态对象运行期新建、`ForceTestState`
   一次钉死、**多帧采样先于会改变状态的那一步**、**增量属性与帧率无关且单一写者**、建场景那一步故意
   重跑同名批量、任何时钟都用浮点累加器。
5. **门跑器 G-1 已修（TASK-099）**：`tools\run_gates.ps1` 的锚点默认取二进制自己的 `--version`，
   纯非编译（文档）提交直接判 `ANCHOR_STRUCTURAL_EQUIVALENT` + 跳过十道门并打印非编译文件清单；
   有编译输入（committed 或工作树）仍照常跑门。复现两情形：
   `powershell -File tools\run_gates.ps1 -Tag x`（跳过）与在引擎工作树放一个未跟踪 `.cpp` 后再跑（照常跑门）；
   `-RunGates` 强制跑门，`-PreflightOnly` 只看判定。
6. **（TASK-102 续）** 台账已到第 15 行（第 14 款 Platformer `runs\platformer\plat-task102-r2`，
   228/228 facts、像素差 40/228 非零；第 15 款 Match-3 `runs\match3\m3-task102-r3`，145/145 facts、
   像素差 22/145 非零）。模板再添五条（见「TASK-102 记录」第 9 条）：**第二实现要覆盖生成出来的默认状态**、
   **采样钉板要先证明它能一直动**、**把「采样期间状态没变」做成会 FAIL 的断言**、
   **世界边界不要复用格子相对公式**、**`execute_gdscript` 的 `ok` 不等于脚本执行成功**。
   下一款（第 16 款）继续复制同一套模板：静态节点一次批量建好、动态对象运行期新建、
   `ForceTestState` 一次钉死、**多帧采样先于会改变状态的那一步**、
   **增量属性与帧率无关且单一写者**、建场景那一步故意重跑同名批量、任何时钟都用浮点累加器，
   并额外带上「采样窗口内状态必然改变」的断言。
7. **（TASK-104 续）第 21 款起，模板再加两条**：①**两态动作要成对测** —— 同一个量若既能被「一次调用」写、
   又能被「每帧时钟」写（LL 的 `Thrust()` 对 `SetThrust()`），就必须是**两个属性**、各有自己的断言；
   ②**每条容差的边界两侧都要测，而且越界的「存活侧」也要测** —— LL 的 330° 存活才说明容差是两侧的，
   只测 90° 坠毁会让人误以为规则要求恰好正立。
   台账已到第 20 行，D138 的口径达成；后续轮次若继续加游戏，沿用同一套模板（静态节点一次批量建好、
   动态对象运行期新建、`ForceTestState` 一次钉死、**多帧采样先于会改变状态的那一步**、
   **增量属性与帧率无关且单一写者**、建场景那一步故意重跑同名批量、任何时钟都用浮点累加器、
   采样窗口内状态必然改变的断言、Python 第二实现 + 事后独立复算）。

