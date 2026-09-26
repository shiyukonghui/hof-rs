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

### 游戏或驱动缺陷

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

---

## 待办

1. **D-1 结案（TASK-097）**：D-3 的根因动作已落进模块（`editor_add_nodes_batch` 默认拒绝同名，`on_name_conflict: "rename"` 才改名且 `editor_save_scene` 会报告），三个老游戏的副本层已用 `editor_delete_node` 逐个删除并复核，像素差列已回填真实数值（Pong 14/74、Breakout 14/89、Snake 13/102，逐对独立复算一致）。复现命令：`powershell -File tools\run_game_session.ps1 -Game pong -Session tools\sessions\pong\session-clean-task097.json -RunTag x -EditorPort 9916 -GamePort 9917`（breakout / snake 同理，会话名同款）。
   最小同批复现的修前/修后：`runs\pong\d3-before`（副本进 `.tscn`）对 `runs\pong\d3-after-r2`（`-32000` + 文件 sha 不变）。
2. **`--import` 的间歇性退出码（TASK-099 仍**未**结案，如实留档）**：`--import` 偶发以 `exit=-1073741819`（`0xC0000005`）退出，stderr 只有
   `ERROR: Parameter "singleton" is null.` / `at: EditorNode::is_cmdline_mode (editor\editor_node.cpp:6750)`，
   而且**导入本身已经跑完**（日志已到 `[ DONE ] loading_editor_layout`，23 行 stdout），即**关机期崩溃、不是导入失败**。
   累计 **3 次 / 13 次会话导入**（TASK-097 的 `d3-after` 首轮、TASK-098 的 `ast-task098-r1`、TASK-099 的 `frog-task099-r1` 首轮）；
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
5. **门跑器 G-1 已修（TASK-099）**：`tools\run_gates.ps1` 的锚点默认取二进制自己的 `--version`，
   纯非编译（文档）提交直接判 `ANCHOR_STRUCTURAL_EQUIVALENT` + 跳过十道门并打印非编译文件清单；
   有编译输入（committed 或工作树）仍照常跑门。复现两情形：
   `powershell -File tools\run_gates.ps1 -Tag x`（跳过）与在引擎工作树放一个未跟踪 `.cpp` 后再跑（照常跑门）；
   `-RunGates` 强制跑门，`-PreflightOnly` 只看判定。
