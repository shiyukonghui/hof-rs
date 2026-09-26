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
| 1 | Pong | C# | 23 / 29（52） | run-4 **44/52**（编辑器 21/23、游戏 23/29）；TASK-092 重跑 **52/52（100%）** | run-4：`ok_effect=9, ok_effect_unavailable=7, ok_file_effect=18, ok_no_effect=18`（两相合计）；重跑：`ok_effect=9, ok_file=23, ok_no_effect=20`，`unavailable` 归零 | **0 / 6**（P-1..P-6；模块字节未改，故无工具缺陷） | `runs\pong\pong-run{1..4}\`、`runs\pong\pong-task092\` | 第 1 个游戏。像素差在 TASK-092 重跑里 **10/29 组非零**（当轮文件今天仍能复算出同一批数）；「注定失败的断言」2 条（run-4 的 `seq=12` 场景断言 + `seq=27` 屏幕文本）。**TASK-093 现场重跑同一会话只得到 1/52 且与帧陈旧同源 —— 见 D-1** |
| 2 | Breakout | C# | 21 / 34（55） | **55/55（100%）**（编辑器 21/21、游戏 34/34） | `ok_file_effect=15`（编辑器 3 + 游戏 12）、`ok_no_effect=38`（17 + 21）、`failed=2`（每相各 1 条声明失败） | **0 / 5**（B-1 侧壁抹平水平速度、B-2 `HitsPaddle` 跨坐标系比较、B-3 HUD 两个写者、会话坐标约定误用、目标砖一格的会话缺陷） | `runs\breakout\breakout-task093-r7\`（最终）；r2/r3/r4/r5/r6 是逐步修复的中间轮 | 挡板/球/15 砖/碰撞消砖/计分/胜负全部由断言钉住（`PaddleBounces=7`、`Brick_r2_c0.Alive=false`、`Score=10`、`BricksRemaining=14`、`HUD="SCORE 10"`、胜负未达成的断言按设计失败、边界调用 `-32000/timeout_ms=1000`）；**像素差 0/55，且 `shots-game\` 68 个 PNG 逐字节相同 —— 见 D-1** |
| 3 | Snake | C# | 20 / 31（51） | **51/51（100%）**（编辑器 20/20、游戏 31/31） | `ok_file_effect=14`（3 + 11）、`ok_no_effect=36`（17 + 19）、`failed=2`（编辑器相 1 条声明失败 + 游戏相 1 条声明失败） | **0 / 4**（S-1 `ForceTestState` 不清胜负、S-2 `Score`/`FoodsEaten` 跨测不归零、S-3 场景注入动作被当成「按住」、S-4 会话把墙测瞄在最后一格） | `runs\snake\snake-task093-r6\`（最终）；r1..r5 是逐步修复的中间轮 | 网格移动/食物增长/自撞/撞墙/计分全部由断言钉住（30 帧冻结采样只有 1 个位置、45 帧移动采样出现 2 个位置、`Length=4`/`segments_in_use=4`、`LoseReason=self`、`LoseReason=wall`）；命中 `sidecar_verified=2`（编辑器相的 C# 载荷超限走旁路证据）；**像素差 0/51，且 `shots-game\` 62 个 PNG 逐字节相同 —— 见 D-1** |

---

## 缺陷登记（跨轮累计）

### 工具缺陷（`modules\mcp_server`）

| id | 层 | 现象（证据） | 根因 | 状态 |
|---|---|---|---|---|
| — | — | TASK-091..093 期间**没有发现新的工具缺陷**；TASK-092 的三条溯源缺口已在上一轮关闭 | — | — |
| **D-1** | 运行期 / 画面侧（**待定：先按工具层登记**） | 进程的视口回读**恒返回同一帧**：`runs\snake\snake-task093-r6\shots-game\` 62 个 PNG、`shots-editor\` 40 个 PNG **逐字节相同**；`runs\breakout\breakout-task093-r7\` 同样（68 / 42 个各 1 个 sha）；`running_game_capture_frames` 12 帧（frame 652..1023）**同一 sha**；`user://` 截图跨 8 秒两次调用**同 sha** `D5C3A72ABA6F525C`。同一批代码在 TASK-092 的 Pong 会话里 **10/29 组非零**（今天用当轮 PNG 复算仍是 512/314/92/122/3200…），TASK-093 现场重跑同一会话只剩 1/52 | **根因未定**。已排除：窗口遮挡/最小化（`ShowWindow(9)`+`SetForegroundWindow` 无效）、渲染驱动（Vulkan 与 OpenGL3 同结论）、窗口尺寸（独占全屏 2880×2160 同结论）、游戏逻辑（同一时刻 `running_game_get_node_property_samples` 与 `execute_gdscript` 都报告球/蛇在动，`frames_waited` 单调递增到 73）、帧循环（`pending_ms`/`timeout_ms` 正常增长） | **未修**（阻塞像素证据）。复现脚本：`recovery\work\task093\diag_render.ps1`（自校验：`IDENTICAL_BYTES=True` → `DEFECT_D1=PRESENT`） |
| **D-2** | 运行期 / 主循环健康度（**已定性：资源争用下的假失败**） | `accept_m1.ps1` 在 `task093` / `task093b` 两轮里失败（`5/22`）：输出头部 `waiting for a steadily pumping main loop ... WARNING: the pump never looked steady, running the cases anyway`，随后 `case1_GET_mcp_200 status=0`、`case2..11/15..20` 抛 `Wait` 异常。**同一脚本在同一台机器、同一引擎字节上单独重跑（`task093c`，g10 wall=50.7s）→ `22/22 cases passed`、`GATE_EXIT=0`** | 与「同一时刻还有别的引擎在抢 CPU / 端口」有关：那两轮我正在后台跑会话与门跑器；`task093c` 是唯一一次单独跑的。判据：`case12/13/14` 与 `guard_user_port_9877` 在三轮里**都 PASS**（含 `case14_port_occupied` 期望的 `bind failed ... error=22`），说明绑定与端口逻辑本身正常，失败只落在「端点要在窗口内稳定作答」这一类 | **不修**（不是模块行为）；读法写进台账：**跑 `accept_m1` 时机器上不要并行跑会话/构建** |
| **G-1** | 门跑器 / 参数（**已定位，未改**） | `run_gates.ps1` 的 `-VersionText` 默认值是 `4.8.dev.mono.custom_build.8604fcf9e`（TASK-090 的锚点），对当前 HEAD `cf554ef58` 判 `ANCHOR_STALE_COMPILED`（`diff_count=22 safe_count=3 red_count=19`）→ 门 9 FAIL | 参数默认值落后于引擎仓 HEAD；**不是模块回归**（引擎仓 TASK-093 期间零改动，`git status --short` 空） | 用 `-VersionText 4.8.dev.mono.custom_build.cf554ef58` 重跑（`runs\gates\task093c\`），结论见 TASK-093 报告 §C |

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

---

## 待办

1. **D-1（像素回读陈旧）必须先解决**，否则 D138 的「像素差」这一条证据在本机持续不可得。
   复现：`powershell -File recovery\work\task093\diag_render.ps1` → 看 `IDENTICAL_BYTES`。
2. D-1 解决后重跑 Breakout / Snake / Pong 三段会话，把像素差列补齐（引擎侧零改动，会话与工程可直接重放）。
3. 台账每轮续行；下一款建议在 Breakout/Snake 的会话模板上直接复制。
