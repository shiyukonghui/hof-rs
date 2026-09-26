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
| **D-1** | 运行期 / 画面侧（**TASK-094 定位：机器画面管线，不是 `modules\mcp_server`；TASK-095 更正根因表述与 A/B 时间戳 —— 见下表后的「D-1 定域更正」**） | 进程的视口回读**恒返回本进程渲染的第一帧**：TASK-093 现场 62/40（snake）、68/42（breakout）个 PNG 各 1 个 sha；`running_game_capture_frames` 12 帧同一 sha；`user://` 截图跨 8 秒同 sha `D5C3A72ABA6F525C`。**TASK-094 的最小反例**：把 `Background.color` 依次设成蓝→红→绿（同一调用内读回 `background_color=(0.0,1.0,0.0,1.0)`，确实变绿），三次 `running_game_capture_screenshot` 得到**三张逐字节相同、且都还是最初深色背景**的 PNG；`--mcp-capture=off`（进程里根本没有 capture engine）同样复现。**同一时刻**蛇的 `SnakeSeg00.position` 从 `(144,240)` 走到 `(384,240)`（240 px），回读指纹恒为 `558211402` | **机器画面管线**，不是模块：①同一份二进制字节、同一个 `tools\sessions\pong\session.json`，00:14:47 得 **10/29 非零**（`pong-task092`，16 个不同 sha），02:00 重放得 **0/29**（`task094-pong-ab`，1 个 sha）；②渲染器本身在动——加 100 个 `ColorRect` 后 `Performance.RENDER_TOTAL_OBJECTS_IN_FRAME` **57 → 157**、prims 114 → 314，`Engine.get_frames_drawn()` 以 ≈144/s 递增；③窗口未最小化（`IsIconic=False`、`window_get_mode()=0`），故 `Main::iteration` 确实调用 `RenderingServer::draw()`；④读的 RID 就是渲染目标当前纹理（`RenderingServer.viewport_get_texture(vp_rid)` 与缓存值同 RID、同字节）；⑤vulkan / opengl3 / d3d12 **三者同样冻结**；⑥`RenderingServer.force_sync()` + `force_draw(true, 0.0)` 无效；⑦GPU 无 TDR/掉卡（`nvidia-smi` 正常、System 日志 8 小时内无 `nvlddmkm`）。**TASK-093 那条复现脚本本身有陷阱**：它拍的是**已经死了的蛇**（`SNAKE_WALL ... ticks=19`，1.5 秒就撞墙），所以「两张同 sha」在那条脚本里本来就该出现；TASK-094 的最小反例改用不被游戏脚本写、且不依赖存活的对象 | **未修（不在本模块内，本模块改不动）**。复现：`recovery\work\task094\diag_freshness.ps1` + `recovery\work\task094\sessions\repro2\session.json`（`D1_VERDICT=PRESENT`）；同刻证据：`runs\snake\task094-probe3/4/5`、`runs\snake\task094-probe9`；A/B：`runs\pong\pong-task092` vs `runs\pong\task094-pong-ab`。**已试无效的绕过**：opengl3 / d3d12 / `force_draw` / 进程外窗口抓取（`CopyFromScreen`、`PrintWindow` —— 两个不同引擎给出同一份抓取字节，说明会话的桌面合成面本身是冻结的，进程外抓取在本机不可信） |
| **D-2** | 运行期 / 主循环健康度（**TASK-094 已修：测试判据对负载敏感**） | `accept_m1.ps1` 在 `task093` / `task093b` 两轮里失败（`5/22`）：输出头部 `WARNING: the pump never looked steady, running the cases anyway`，随后 `case1_GET_mcp_200 status=0`、`case2..11/15..20` 抛 `Wait` 异常；同一脚本在同一台机器、同一引擎字节上单独重跑（`task093c`，wall=50.7s）→ `22/22`、`GATE_EXIT=0` | **判据是吞吐而不是就绪**：`Wait-ForStablePump` 原来要求「相隔 1000 ms 的两次采样之间 `frame_count` 至少 +20，连续 3 次」——即**至少 20 fps**。有负载时主循环活着但慢于 20 fps，判据永不成立，函数耗尽 180 s 死线后打印 WARNING 继续跑，用例于是在尚未稳定的泵上执行 → `status=0` / `Wait` 异常。绑定与端口逻辑无辜（`case12/13/14`、`guard_user_port_9877` 在失败轮里也全 PASS） | **改**（`modules\mcp_server\scripts\accept_m1.ps1`）：判据改为「`frame_count` 连续 6 次严格递增，采样间隔 250 ms」＝**约 1.5 秒不间断推进，与帧率无关**（1 fps 也能满足），死线仍 180 s，未满足时仍照旧响亮报警。实测：**单跑 wall=50.8s → 22/22、`GATE_EXIT=0`**（`runs\gates\task094-alone\`）；**同机 8 个 CPU 烧机进程（16 逻辑核）并跑 wall=55.3s → 22/22、`GATE_EXIT=0`**（`runs\gates\task094-load2\`）；另有一次短重叠负载（`dotnet build`）wall=41.5s → 22/22（`runs\gates\task094-load\`）。三次都没有出现 WARNING 行 |
| **G-1** | 门跑器 / 参数（**已定位，未改**） | `run_gates.ps1` 的 `-VersionText` 默认值是 `4.8.dev.mono.custom_build.8604fcf9e`（TASK-090 的锚点），对当前 HEAD `cf554ef58` 判 `ANCHOR_STALE_COMPILED`（`diff_count=22 safe_count=3 red_count=19`）→ 门 9 FAIL | 参数默认值落后于引擎仓 HEAD；**不是模块回归** | TASK-093 用 `-VersionText 4.8.dev.mono.custom_build.cf554ef58` 重跑（`runs\gates\task093c\`）；TASK-094 沿用同一锚点（`runs\gates\task094\`） |

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
   复现（TASK-095 的更强反例，两条一起看才有判别力）：`powershell -File tools\run_game_session.ps1 -Game snake -Session recovery\work\task095\sessions\loadednode\session.json -RunTag x -GamePort 9892 -SkipReport`
   → `p03` 的 `P1(10,580)` 与 `p01` 一字不差（加载期项冻结），`p05` 的 `P1` 变黄（运行期项正常）；`p07` 在 `queue_redraw()+hide()+show()` 之后仍然一字不差。
   **下一步（需要用户授权，属于机器状态变更）**：接上/唤醒一个物理输出，或暂停/断开 `GameViewer`（网易远程串流，正在 session 1 运行且其虚拟显示器适配器 off-line），然后重跑上面这条会话。若 `p03`/`p07` 开始跟着变，则 D-1 判**机器画面管线**，像素差列自然回填；若不变，则 §C 的选项 2（影子渲染）才需要立项。
2. D-1 解决后重跑 Breakout / Snake / Pong 三段会话，把像素差列补齐（引擎侧零改动，会话与工程可直接重放）。
3. 台账每轮续行；下一款建议在 Breakout/Snake 的会话模板上直接复制。
