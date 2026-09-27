# TASK-131 报告 —— 真实输入通路验证 + 取证对应关系核对 + 强制读图

* 任务书：`recovery/tasks/TASK-131.md`（2026-09-27）
* 基线提交：`8cd0127`（P7 + 输入形态研究，TASK-130），其上 `ebab184` / `14c2564`（docs）
* 报告：本文件。**证据目录**：`runs/realinput/**`（新）、`runs/playability/**`（既有 + `t131-before` / `t131-after` / `t131-smoke`）
* 严格单线程：本任务期间**没有派发任何子代理**（任务书 §0 硬约束），全部工作在本会话串行完成。

**一句话结论**：真实 OS 键在本机**能送达游戏窗口**（结论三选一取 **①**），所以"用户按键没反应"**不是输入通路缺陷**；
`Input.parse_input_event` 只是 **DisplayServer 之内**的忠实通道（原文那句 "the path a real key press takes" 是过度声称，已改正）。
"画面没有变化"的真相是**判据问题 + 两个真实游戏缺陷**：`snake` 在**第一帧之前就已经 GameOver**（1.52 秒游戏时间自撞墙、
InputMap 里没有重开键），`game2048` 的棋盘**从来没被种下任何棋子**（`GridString` 全 0），
而旧 P1/P2/P3 分别用"0.4% 非背景像素""任意状态变化""`frames_drawn` 递增"把它们判成了 PASS。

---

## 0. 结论速览（对应验收判据 X1–X14）

| 编号 | 结论 | 一句话证据 |
|---|---|---|
| X1 | **完成** | `runs/realinput/_env/env.json`：session 1 / `Default` 输入桌面 / 1 台 2560×1440 / `display_active=Enabled` / `SendInput` 返回 1 且 `GetAsyncKeyState=-32767` / `SetForegroundWindow` **换窗口成功** |
| X2 | **完成** | `pong`、`tetris`、`snake` 三款发布版 exe 实测，前后状态与像素对比见 §A.3 |
| X3 | **完成** | §A.4 两条通路对照表（同实例、同动作、各自带无输入对照窗） |
| X4 | **完成，取 ①** | 真实键有效；本机限制不再是默认解释；替代证据强度上限写在 §A.5 |
| X5 | **完成** | §B.1 逐步对应表（seq → 状态 sha → 帧 sha/像素差 → `ts_ms`/`frame_count`）+ §B.2 四处对齐（pid/端口/trace/版本） |
| X6 | **完成** | 采集视口 = 整窗 `800×600` = 工程声明 `[800,600]`（`out_window` 与 `window_conformance` 两处都记） |
| X7 | **完成** | §C 逐帧读图描述表（`read_image` 实看：两张 23 格 filmstrip + 三张 filmstrip + 3 张 800×600 全尺寸） |
| X8 | **完成** | `recovery/tasks/TEMPLATE-logic-feedback.md`（双通路 / 同实例核对 / 读图表 / 三态结论 + 8 条真实反例） |
| X9 | **完成** | §F 可重跑命令逐条 + 铁律自查 + 两仓 `git log/status` |
| X10 | **完成** | §D.1：**判据问题 (i)**（并额外发现"第一帧前就已结束"这个更根本的原因）；不是实例不一致 |
| X11 | **完成** | §A.1：环境结论已更新为 `display_active=Enabled`、单显示器、前台可用 → 真实键验收在本机**可行** |
| X12 | **完成** | §D.2：收紧 P2/P3 + 25 个目标前后对比；翻红 3 款正向 + 2 个负变体被抓住 |
| X13 | **完成** | §D.3：`snake_pause` 留激活态被**恢复**并读回；每帧带 `Paused`/时钟/`Ticks`/`Score` marker |
| X14 | **完成** | §D.4：P1 阈值从 0.004 重推为 0.008（推导依据 + 新值对比）；snake 帧逐项清单；P7 交叉核对 |

---

## A. 真实输入通路（OS 级）

### A.1 本机是否具备"把键送到窗口"的条件（X1 / X11）

工具：`tools/real_input_probe.py env` → `runs/realinput/_env/env.json`（只读，逐条原始读数）。

| 探测项 | 实测值 | 出处字段 |
|---|---|---|
| GPU `display_active` | **`Enabled`**（RTX 4090，驱动 616.56） | `nvidia_smi[0].stdout` |
| 显示器数 / 分辨率 | **1 台**，`\\.\DISPLAY1` `0,0,2560×1440`（primary） | `monitors`, `monitor_metrics.SM_CMONITORS` |
| 是否远程会话 | `SM_REMOTESESSION = 0` | `monitor_metrics` |
| 交互式桌面 | `OpenInputDesktop` 成功，名字 **`Default`** | `input_desktop` |
| 本进程会话 | `ProcessIdToSessionId = 1`；`query session` 显示 `console  wyl  1  Active` | `this_process` |
| 前台锁超时 | `SPI_GETFOREGROUNDLOCKTIMEOUT = 2147483647 ms` | `foreground_lock_timeout` |
| 置前台（同窗口） | `SetForegroundWindow` 返回 **1**、`GetLastError=0` | `foreground_attempt` |
| **置前台（换一个窗口）** | 目标 `hwnd=132032 / pid=17392 / Windows.UI.Core.CoreWindow`，前=`hwnd 1050864`（Firefox）→ **后 = 目标**，`ok=true` | `foreground_change_attempt` |
| 还原原前台 | **失败**（`ok=false`）——只读探测顺手换过前台，没换回 Firefox；这是探测的副作用，已如实记录，对后续实测无影响（每次实测都自己强制焦点） | `foreground_restore_attempt` |
| `SendInput` | F24 `keydown returned 1 / GetLastError 0` → `GetAsyncKeyState = -32767`(0x8001) → `keyup returned 1` → 读回 0 | `sendinput_selftest` |

**X11 的结论**：旧记录"本机没有活动显示"**不成立**（`display_active=Enabled`），
且**换一个窗口的前台切换真的成功**——"对已经是前台的窗口返回 1"什么也证明不了，所以这一条是单独测的。
因此 **A 段不得再以"本机限制"作为默认解释**，实测结论必须归因到游戏侧或通路侧。

### A.2 协议：为什么不是"先真键臂再合成臂"

第一版协议（真实键臂 → 合成键臂，同一动作）在 `snake` 上给出**假阴性**：`snake_left` 的合成臂报"无反应"，
原因是许多动作在它写的状态上**幂等**（连按两次 LEFT，`DirectionX` 第二次不变）。
这份被推翻的取数留在 `runs/realinput/snake`（早期）与 `runs/realinput/pong-hold0.5-confounded/`。

第二版协议（当前实现，`real_input_probe.py run`）：对**互逆动作对** `(X, Y)` 走循环
`REAL X → PARSE Y → PARSE X → REAL Y`，每个臂都从**相反的值**出发，
于是同一个动作在两条通道上各被测一次且都不是第二次写同一个值；
每个循环前跑一个**等长无输入对照窗**，臂只在**赢过对照**时才算数。

第三处修正（本轮实测抓到）：**prep 动作（真实 SPACE 发球）之前没有强制焦点**，
于是那一发 SPACE 送到了别的窗口，`pong_serve` 没触发——**而状态 sha256 照样变了**
（变的是 `_logTimer`）。这正是本任务的主题"变了哈希 ≠ 键生效"的又一次现形，证据留在
`runs/realinput/pong-prep-without-focus/`（该次 `engine-game.stdout.txt` **没有** `PONG_SERVE` 行）。
修正后 `runs/realinput/pong/engine-game.stdout.txt` 出现 `PONG_SERVE ball=(392, 268) v=(280, 180)`，球真的飞了。

### A.3 真实键实测（X2）

三款都用**发布版 exe**（`dist/exe/<game>/<game>.exe`），`SendInput` 打**该游戏自己 `project.godot` 里声明的键码**。

| 游戏 | 动作 | 键 / VK | 焦点 | 下行/上行返回 | 对照窗 状态/像素 | 真实键臂 状态/像素 | 游戏世界的变化 |
|---|---|---|---|---|---|---|---|
| pong | `pong_serve`（prep） | SPACE / 0x20 | ok | 1 / 1 | — / — | — | `PONG_SERVE ball=(392,268) v=(280,180)`（游戏 stdout） |
| pong | `pong_left_up` | W / 0x57 | ok | 1 / 1 | 0 变更 / 0 px | 5 变更 / **4300 px** | `PaddleLeft.pos` y 226→26.67；`Ball.pos` (704,469)→(560,376)；`_leftScore` 0→1 |
| pong | `pong_left_down` | S / 0x53 | ok | 1 / 1 | 0 / 0 | 5 / **4049 px** | `PaddleLeft.pos` y 26.72→226.06；`Ball.pos`→(397,271)；`_leftScore` 2→3 |
| tetris | `tetris_left` | A / 0x41 | ok | 1 / 1 | 0 / 0 | 2 / **1058 px** | `PieceX` 3→2 |
| tetris | `tetris_right` | D / 0x44 | ok | 1 / 1 | 0 / 0 | 2 / **1058 px** | `PieceX` 2→3 |
| snake | `snake_left` | A / 0x41 | ok | 1 / 1 | 0 / 0 | 1 / 0 px | `LastRefusedInput` `""`→`"-1,0"`（**事件到达了**，但游戏在 GameOver 下拒绝一切） |
| snake | `snake_right` | D / 0x44 | ok | 1 / 1 | 0 / 0 | 1 / 0 px | `LastRefusedInput` 变为 `"1,0"` |

（三款都是**互逆动作对循环 + 各自无输入对照窗**的协议，证据 `runs/realinput/{pong,tetris,snake}/real_input.json`。）

### A.4 两条通路对照表（X3）

同一实例、同一动作、各自带无输入对照窗（`runs/realinput/pong/real_input.json -> comparison_table`）：

| 动作 | 通道 | 注入调用 | 状态变更 | 像素差 | 赢过对照 | 逐帧图 |
|---|---|---|---|---|---|---|
| `pong_left_up` | **OS_SendInput** | `user32!SendInput`（VK 0x57） | 5（含 `PaddleLeft.pos`、`Ball.pos`、`_leftScore`） | 4300 | **是** | #05→#06 |
| `pong_left_up` | `Input.parse_input_event` | `running_game_execute_gdscript` seq 19/20 | 5（同上，含 `PaddleLeft.pos` 26.67→8） | 4173 | **是** | #07→#08 |
| `pong_left_down` | `Input.parse_input_event` | seq 15/16 | 3 | 3712 | **是** | #08→#09 |
| `pong_left_down` | **OS_SendInput** | VK 0x53 | 5 | 4049 | **是** | #09→#10 |
| `tetris_left` | **OS_SendInput** | `user32!SendInput`（VK 0x41） | 2（`PieceX` 3→2） | **1058** | 是 | `runs/realinput/tetris` #03→#04 |
| `tetris_left` | `Input.parse_input_event` | seq 15/16 | 2（`PieceX` 3→2） | **1058** | 是 | #06→#07 |
| `tetris_right` | `Input.parse_input_event` | seq 11/12 | 2（`PieceX` 2→3） | **1058** | 是 | #07→#08 |
| `tetris_right` | **OS_SendInput** | VK 0x44 | 2（`PieceX` 2→3） | **1058** | 是 | #09→#10 |

**对照臂的真实价值**：`Input.parse_input_event` 既置 InputMap 状态又派发事件，是 **DisplayServer 之内**的忠实通道；
它**证明不了** OS 事件能不能落到窗口，所以它只能当对照臂。两条通路在 pong/tetris 上结果一致，
说明**门里的注入在"送达之后"的行为是忠实的**；而这正是原来那句过度声称**唯一**成立的那一半。

### A.5 结论（X4，三选一）+ 替代证据的强度上限

**取 ①：真实键有效。** 依据：
1. 能力层：交互式桌面、单显示器、`display_active=Enabled`、前台可**真的切换**（§A.1）；
2. 送达层：`SendInput` 1/1 返回 + `GetAsyncKeyState` 按下确认；
3. 效果层：`pong` 真实 W/S 让挡板与世界变化（4300/4049 px，且赢过各自的 0/0 对照窗）、
   `tetris` 真实 A/D 与合成臂**同值**、`snake` 真实键改写了游戏自己的拒绝日志；
4. 游戏自己的 stdout（`PONG_SERVE` / `PONG_NUDGE` / `PONG_TICK`）把"我按的那一下"与"游戏内部事件"对上了。

**替代证据（当没有真实键能力时）与其强度上限**（照实写）：
* 机器侧的**最强组合** = 状态快照 sha256 + 整窗帧 sha256 + 逐帧像素差 + **游戏自身 stdout 事件** + pid/端口/trace/版本四处对齐；
* 上限一：它证明的是"**这一条注入**改变了**这一个实例**"，**不**证明"人坐在键盘前会看到什么"——那一条只能靠 §C 的读图补；
* 上限二：注入点若只能放在 **DisplayServer 边界之上**（门里的三种注入都是），
  它最多证明 `Input::parse_input_event` **之后**的行为，**不**能证明 OS 事件能到达窗口；
  本机这一条已经被 §A 的真实键实验**补上**了，但在别的机器上仍需重测；
* 上限三：`--mcp-trace` 默认 `off`（stdout 里 `[MCP] trace=off`），逐调用 trace 是**门自己**写的
  `calls/NNN_<tool>.response.json`，不是引擎侧 trace；引用时不要混淆。

---

## B. 取证对应关系核对

### B.1 逐步对应表（X5）

完整表：`runs/realinput/<game>/steps.json`（本工具直接产出，13–16 步）；渲染脚本 `runs/realinput/_scripts/b_table.py`。
pong 的样例（节选，`runs/realinput/pong/steps.json`）：

| step | phase | 注入（seq / 工具） | 状态 sha256(12) | drawn | 帧文件 | 帧 sha256(12) | px vs prev | ts_ms |
|---|---|---|---|---|---|---|---|---|
| 1 | settle | — | d3672100502b | 350 | 01_settle.png | 7b516a5ca402 | None | 7064 |
| 2 | prep | `[1,1]` user32!SendInput | 79ec16f15c05 | 360 | 02_prep_pong_serve_pre.png | 7b516a5ca402 | 0 | 7227 |
| 3 | prep | — | 46c2c9a75903 | 375 | 03_prep_pong_serve_post.png | 7b516a5ca402 | 0 | 7477 |
| 5 | real_key | `[1,1]` user32!SendInput | c724160575b3 | 430 | 05_…_ctl_end.png | 7b516a5ca402 | 0 | 8393 |
| 6 | real_key | — | e912ac91a822 | 487 | 06_…_real_post.png | 9c5e4b2521e6 | **3200** | 9344 |
| 8 | synthetic | `[19,20]` running_game_execute_gdscript | cb382f163c0d | 561 | 09_…_parse_post.png | 6ebf46020bf8 | **608** | 10577 |

（上表是 **prep-无焦点**那一版 pong 的编号；当前 `runs/realinput/pong/` 是修好焦点后的版本，
帧号与值以 `steps.json` 为准。两种版本都保留在盘上。）

### B.2 "取证与输入属于同一实例"：四处对齐（X5）

`runs/realinput/pong/session.json`：

| # | 对齐项 | 值 | 结论 |
|---|---|---|---|
| 1 | 游戏进程 pid | `game_pid = 76552`；窗口 pid `100428`；两者同在 `process_tree` 内（cmd → godot engine → pong.exe） | ✅ 同一进程树 |
| 2 | MCP 端口 | `mcp_port = 9931`、`mcp_endpoint = http://127.0.0.1:9931/mcp`、命令行含 `--mcp-port=9931`；跑前 `kill_what_holds(9931)` 证明端口独占 | ✅ 唯一端口 |
| 3 | trace 文件名 | `calls/NNN_<tool>.response.json`（逐调用落盘，`003_running_game_execute_gdscript.response.json` 等） | ✅ 每次状态/帧读都有对应 trace |
| 4 | 引擎版本串 | `4.8.dev.mono.custom_build.3fdabe2d9`（`<engine> --version`），引擎二进制 sha256 `27f5ce45…` | ✅ 与 `session.json.engine_version_string` 一致 |

**加分证据**：游戏自己的 stdout `<out>/engine-game.stdout.txt` 里有带时间戳的内部事件
（`PONG_TICK ball=(392, 268) v=(0, 0) left=226 right=226 score=0-0`、`PONG_NUDGE who=left_up y=96`、
`SNAKE_WALL head=25,10 cols=25 rows=21 score=10 ticks=19`），这是"注入的那一下"与"游戏真的收到"最硬的一条对齐。

**没有发现**帧来自编辑器进程 / 内嵌小窗 / 另一个进程的情形（窗口 pid ∈ 游戏进程树，
窗口 rect 与 `DisplayServer.window_get_size()` 的 `800×600` 一致）。

### B.3 采集视口与分辨率（X6）

| 项 | 值 | 出处 |
|---|---|---|
| 帧尺寸 | `800×600` | `analyse_frame` 对每帧算出的 `width/height` |
| 采集通道 | `running_game_capture_screenshot`（**game 端点**、**整窗**） | 门 1205 行；`real_input_probe` 同样只用这个工具 |
| OS 窗口尺寸 | `[800, 600]` | `PROBE_WINDOW.display_window_size` |
| root viewport | `[800.0, 600.0]` | `PROBE_WINDOW.root_viewport_size` |
| 工程声明 | `[800, 600]`（无 `window_width_override`） | `parse_project` |
| 判定 | **MATCH**（filmstrip 头部自注 `OS window [800,600] root viewport [800.0, 600.0] declared [800,600] (MATCH)`） | `gate.json -> window_conformance` |

即：**整窗 = 游戏 root viewport = 工程声明**，三者一致；不是编辑器截图、不是裁剪、不是桌面截图。

---

## C. 强制读图（X7）

**实际读过的图（`read_image`，写清分辨率与用途）**

| # | 文件 | 分辨率 | 用途 |
|---|---|---|---|
| 1 | `runs/playability/snake/filmstrip.png` | 1086×1042（23 格，每格 210px 宽） | X10/X14 主证据：**逐格**确认 23 帧全同 |
| 2 | `runs/playability/snake/frames/01_settle.png` | **800×600 全尺寸原图** | X14 逐项清单：认出结束遮罩/蛇身/食物/网格线 |
| 3 | `runs/playability/pong/filmstrip.png` | 1086×1042（23 格） | 对照：pong 前 6 帧静止但随后确实动 |
| 4 | `runs/realinput/pong/filmstrip.png` | 1086×448（13 格） | A/B 主证据：真实键与合成键都推动了挡板与世界 |
| 5 | `runs/realinput/pong/frames/06_a00_pong_left_up_real_post.png` | **800×600 全尺寸** | 真实 W 之后左挡板到顶、球在中线 |
| 6 | `runs/realinput/pong/frames/15_a01_pong_left_down_parse_post.png` | **800×600 全尺寸** | 合成 S 之后左挡板到底 |
| 7 | `runs/realinput/tetris/filmstrip.png` | 1086×646（14 格） | 第二款：左→左→右→右 的循环协议肉眼可核 |
| 8 | `runs/realinput/snake/filmstrip.png` | 1086×448（8 格） | snake 8 帧全同（真实键也没能救活已结束的局） |

### C.1 `runs/playability/snake` 23 帧逐帧描述表（X10/X14 核心）

所有 23 帧 `sha256 = b74c75d6cdb2…`、`changed vs prev: 0`，画面内容相同。我**看到的**是：
一整块 **35% 透明度的红色遮罩**（`/root/Main/Status`，`Color(0.85,0.1,0.1,0.35)`，`visible=true`）
盖住 800×600 全场；中间偏上有一条 **96×24 的暗绿色横条**（4 格蛇身，`x=504…600, y=240…264`，
`Color(0.24,0.68,0.33)` 被红罩压成暗橄榄绿）；**左上角有一颗 24×24 的红方块**（`Food`，
被 `RespawnFoodAwayFromSnake()` 扫到 `(0,0)`，`Color(0.98,0.3,0.3)` 被压成亮红）；
网格线在遮罩下**肉眼勉强可见但低于 PIXEL_DELTA=16**；**没有分数、没有 HUD、没有任何文字**。

| 帧 | 文件 | 我看到了什么 | 与上一帧相比 | 与操作相符？ | 结论 |
|---|---|---|---|---|---|
| #01 | `01_settle.png` | 红罩 + 4 格蛇身 + 左上角食物；无 HUD | — | 无操作 | **已经是结束画面** |
| #02 | `02_auto1.png` | 同上 | **无变化（px 0）** | 无操作 | 静止 |
| #03 | `03_auto2.png` | 同上 | 无变化（px 0） | 无操作 | 静止 |
| #04 | `04_auto3.png` | 同上 | 无变化（px 0） | 无操作 | 静止 |
| #05 | `05_a00_snake_up_parse_pre.png` | 同上 | 无变化 | 对照窗 | 静止 |
| #06 | `06_a00_snake_up_parse_ctl.png` | 同上 | 无变化 | 对照窗 | 静止 |
| #07 | `07_a00_snake_up_parse_act.png` | 同上 | 无变化 | **按 W 后**：**不相符**（应左转/上转） | 见 §D.1：被拒 |
| #08 | `08_a01_snake_down_parse_pre.png` | 同上 | 无变化 | 对照窗 | 静止 |
| #09 | `09_a01_snake_down_parse_ctl.png` | 同上 | 无变化 | 对照窗 | 静止 |
| #10 | `10_a01_snake_down_parse_act.png` | 同上 | 无变化 | **按 S 后**：不相符 | 静止 |
| #11-13 | `11/12/13_a02_snake_left_*` | 同上 | 全部无变化 | **按 A 后**：不相符 | 静止 |
| #14-16 | `14/15/16_a03_snake_right_*` | 同上 | 全部无变化 | **按 D 后**：不相符 | 静止 |
| #17-19 | `17/18/19_a04_snake_pause_*` | 同上 | 全部无变化 | **按 P 后**：遮罩不变（本来就在结束态） | 静止 |
| #20-21 | `20/21_post*` | 同上 | 全部无变化 | 输入轮之后 | 静止 |
| #22-23 | `22/23_agent*` | 同上 | 全部无变化 | 代理动作后 | 静止 |

**读图给出的、数字给不出的三条**：
(1) 那层红色是**结束遮罩**（`Status` 节点 + 场景文件颜色 + 与背景按 0.35 alpha 复合后
    `0.35×217+0.65×13 ≈ 84`，与实测 `bg=[88,24,24]` 吻合），不是背景色也不是渲染缺陷；
(2) 绿色是 **4 格蛇身**而不是"一个方块"——它已经吃了一个食物（`Length=4`）；
(3) 左上角那颗红点是 `Food` 被重生成到 `(0,0)` 的结果——**它同时把 P1 的 bbox 撑到 33%**（见 §D.4）。

### C.2 `runs/playability/pong` 23 帧逐帧描述表（对照）

| 帧 | 我看到了什么 | 与上一帧相比 | 与操作相符？ |
|---|---|---|---|
| #01-#04 `settle`/`auto1-3` | 深蓝黑场地、蓝色左挡板在中、红色右挡板在中、黄色小球静止在中线、顶上一个白 `0` 与一个白 `0` | 全同（px 0，`sha=7b516a5ca402`） | 无操作 → **合法静止**（`AutoServe` 未发球，`Ball.Velocity=[0,0]`） |
| #05-#07 `a00_pong_left_up_*` | 左挡板**上移到接近顶端**、球仍在中间 | pre→ctl 0；ctl→act 有变化 | **相符**：按上键左挡板上移 |
| #08-#10 `a01_pong_left_down_*` | 左挡板**下移**、球仍在中间 | 同上 | **相符** |
| #11-#13 `a02_pong_right_up_*` | **右挡板**上移、球仍在中间 | 同上 | **相符** |
| #14-#16 `a03_pong_right_down_*` | 右挡板下移 | 同上 | **相符** |
| #17-#18 `a04_pong_serve_pre/ctl` | 球仍在中线、`0 0` | 无变化 | 对照窗 |
| #19 `a04_pong_serve_act` | 球开始离开中线（黄点在中线右侧） | 有变化 | **相符**：发球 |
| #20-#23 `post1/post2/agent00/agent01` | 球继续右移（到 546→…）、挡板仍在上/下位 | 每帧都有变化（512 等） | **相符** |

### C.3 `runs/realinput/pong` 13 帧逐帧描述表（A 段主证据）

| 帧 | 我看到了什么 | 与上一帧相比 | 与操作相符？ |
|---|---|---|---|
| #01 `01_settle` | 双方挡板居中、球停在中线、`0  0` | — | 初始（球未发） |
| #02 `02_prep_pong_serve_pre` | 同上 | 0 px | 对照 |
| #03 `03_prep_pong_serve_post` | **球右移并下落**（约 (445,302)）、`0  0` | 有变化 | **相符**：真实 SPACE 发球（stdout `PONG_SERVE`） |
| #04 `04_p00_ctl_end` | 球继续到右下 (704,469)、`0  0` | 有变化（球自主运动） | 对照窗（**球自己在动**，所以判据必须要求臂赢过对照） |
| #05 `05_p00_arm1_real_post`（同 #04 帧） | 记录注入前状态 | — | 真实 W 之前 |
| #06 arm1 real post | **左挡板到顶**、球回到 (560,376)、分数变成 **`1  0`** | 4300 px | **相符**：真实 W 让挡板上移，且球出界给左边得 1 分 |
| #07 arm2 parse post | 球到 (756,502)、`1  0`、左挡板仍高 | 3712 px | 相符（合成 S 下移前的状态） |
| #08 arm3 parse post | 球到 (541,364)、左挡板到顶、分数 **`2  0`** | 4173 px | **相符**：合成 W 让挡板上移 |
| #09 arm4 real post | 球到 (397,271)、左挡板到中位 (226)、分数 **`3  0`** | 4049 px | **相符**：真实 S 让挡板下移 |
| #10 `zz_tail` | 球到 (728,484)、`3  0` | 有变化 | 相符 |

### C.4 `runs/realinput/tetris` / `runs/realinput/snake` 逐帧描述表（节选）

| 帧 | 我看到了什么 | 与上一帧相比 | 与操作相符？ |
|---|---|---|---|
| tetris #01-#03 | 深色场地 + 左上 `TETRIS HUD` + 右上浅蓝方块（当前块）+ 右侧 Next 面板 | 全同（px 0） | 对照 |
| tetris #04 | **浅蓝方块左移一格** | 1058 px | **相符**：真实 A |
| tetris #06-#07 | 方块再左移一格 | 1058 px | **相符**：合成 A（与真实臂同值） |
| tetris #09-#10 | **方块右移一格** | 1058 px | **相符**：真实 D |
| tetris #12-#13 | 方块再右移一格 | 1058 px | **相符**：合成 D |
| snake #01-#08 | 红罩 + 4 格蛇身 + 左上角食物，**8 帧全同** | 全部 px 0 | **不相符**：真实键与合成键都没能让画面动（因为局已经结束） |

**读图边界（照实声明）**：本轮 `read_image` 能力正常，全部上述图片**都真的看过了**。
但**不是**每一张 800×600 单帧都单独看过全尺寸原图——23 格 filmstrip 是逐格看的（每格 210px 宽），
另有 3 张关键帧看了全尺寸。**我没有**用像素差或 sha256 冒充"看过图"；
filmstrip 缩略图看小字（如 HUD 数值）能力有限，所以 HUD 数值类结论一律以状态字段为准并在表里标注来源。

---

## D. 判据：解释矛盾 + 收紧 P1/P2/P3

### D.1 X10 —— 为什么 snake 23 帧全同、pong 前 6 帧全同，而门报 P2/P3 pass

**二选一：取 (i) 判据问题**，并额外发现一个更根本的原因。**不是**实例不一致。

**(i-a) 判据问题（旧门的确切来源）**

* 旧 `P2` 判的是 `a["responds"] = parse/push/action 任一 changed`，而 `changed = state_wins or pixel_wins`，
  `state_wins = len(act_delta) > len(ctl_delta)` ——**任何**状态变化都算。snake 的 5 个动作全绿，
  靠的是 `DirectionX 1→-1`、`DirectionY 0→1`、`LastRefusedInput ""→"1,0"`、`Paused false→true`，
  **全是元状态**（输入意图、拒绝日志、模式标志），画面 23 帧逐字节相同。
* 旧 `P3` 判的是 `loop_advanced and (len(auto_delta)>0 or len(post_delta)>0 or pixel_auto>=40 or input_delta_count>0)`。
  snake 的 `frames_drawn 271→1084` 让 `loop_advanced=True`，`input_delta_count=8` 让它 pass；
  它自己的 `why` 就写着 `pixel change over the autonomous+post frames=0`。
  **`frames_drawn` 递增只证明渲染循环在跑，不证明游戏在推进。**
* `P6` 没拦住的原因：snake 的 P6 能力表里 "turn up/down/left/right" 的 observable 是
  `DirectionX|DirectionY|LastRefusedInput`（**元状态**），"pause" 的 observable 是 `Paused`——**声明本身就在放水**。

**(i-b) 更根本的原因（旧判据完全看不见的那一半）：采集实例在**第一帧之前**就已经结束**

| 证据 | 出处 | 值 |
|---|---|---|
| settle 状态快照 | `runs/playability/snake/states/00_settle.json` | `GameOver=true, LoseReason="wall", HeadX=25, HeadY=10, Ticks=19, Score=10, Length=4, FoodsEaten=1, Paused=false` |
| 游戏自己的 stdout | `runs/playability/snake/engine-game.stdout.txt` | `SNAKE_READY head=5,10 dir=1,0` → `SNAKE_ATE head=12,10 len=4 score=10` → `SNAKE_FOOD cell=0,0` → `SNAKE_TICK head=24,10 ticks=19` → **`SNAKE_WALL head=25,10 cols=25 rows=21 score=10 ticks=19`** |
| 之后的注入 | 同上 | `SNAKE_DIR dir=0,-1` / `SNAKE_REFUSED input=0,1` / `SNAKE_DIR dir=-1,0` / `SNAKE_REFUSED input=1,0` / `SNAKE_PAUSE paused=True` |

即：`SnakeGame._Ready()` 里 `ResetSnake()` 把方向设为 `(1,0)`，`_Process` **立刻开始步进**
（类注释里那句 "The snake starts parked" 与实现不符），19 步 × `StepSeconds=0.08` = **1.52 秒游戏时间**就撞右墙；
门的 `--settle 4.0` 让第一帧出现在约 4 秒之后——**玩家看到的第一帧就是结束画面**
（`Status` 遮罩 `visible=true`）。此后 `_Process` 第 159 行 `if (GameOver || Paused) return;` 直接返回，
**棋盘再也不会变**。而 snake 的 InputMap 只有 `W/A/S/D/P`，**没有重开键**（重开只有 `Resume()`/`ForceTestState()` 这些 MCP 方法）。

**(i-c) §0.5 猜对了一半**：门自己的 `snake_pause` 把 `Paused` 从 false 翻成 true 且**没有恢复**，
所以它之后的帧**必然**静止；但静止**从第 1 帧就开始了**，`Paused` 只是雪上加霜。两件事都要修：
前者 → §D.3（副作用恢复 + 每帧 marker）；后者 → §D.2（P2/P3 收紧 + settle 活性检查）。

**(i-d) pong 前 6 帧全同是合法的**，不是判据问题：`PongGame` 的确定性规则明确"新进程把球停在中间零速度，等显式发球"
（`PongGame.cs:13-16`、`ParkBall()`），`Ball.Velocity=[0,0]`、两块挡板无人按 → 前 6 帧必然相同。
旧 `P3` 对 pong 的 pass 是**有效证据**（它记录了 `Ball.Velocity [0,0]→[-285.6,-320]` 与真实位移、`pixel change=512`）；
**同一个 P2/P3 对 pong 有效、对 snake 被元状态蒙混** —— 这正是 §D.2 要修的缺口。

### D.2 X12 —— 收紧 P2/P3（声明驱动），修在根上

**新声明**（`tools/playability_controls.json`，25 个目标每个都有，共 5 个新键）：

| 键 | 作用 |
|---|---|
| `gameplay_observables.items` | 该游戏**算作"世界在动"**的 state key 清单（位置/速度/得分/棋盘推进…） |
| `refusal_evidence` | 游戏**自己记录蓄意拒绝**的键名与词（`LastRefusedInput`/`Rejected*`；值里含 `rejected`/`blocked`/…）——**唯一豁免** |
| `liveness.terminal` | 什么叫"这局已经结束"（如 `/root/Main.GameOver == true`），**在 settle 帧上求值** |
| `state_markers` | 每帧要记录的 marker 字段（`Paused`/`GameOver`/`Ticks`/`Score`/…） |
| `mode_actions` | 会留下**持久模式**的动作 + 怎么恢复（当前只有 `snake_pause`） |

**均匀 META 黑名单**（`playability_gate.META_KEY_PATTERNS`，**META 优先于 `items`**，声明不能把元状态写回来）：
时钟（`Ticks`/`Elapsed`/`_logTimer`）、输入计数（`Input*`）、输入描述（`LastEvent`）、拒绝日志（`LastRefusedInput`/`Rejected*`）、
意图索引（`DirectionX/Y`/`Facing`/`AngleIndex`）、摘要（`*Hash`）、UI 文本（`*.text`）、模式标志（`Paused`/`GameOver`/`LoseReason`）、`Seed`、`Moved`。

**新 P2** = 每个声明动作必须**在该游戏声明的玩法可观测上赢过自己的无输入对照窗**（或像素赢过对照），
**或**是游戏自己记录的蓄意拒绝；**并且**至少有一个动作真的推动了玩法。
（最后半句是关键：没有它，"全都拒绝了，因为局已经死了"——snake 与 game2048——会靠拒绝豁免蒙过去。）

**新 P3** = `loop_advanced` **且** 有玩法推进证据（输入的某个臂推动了玩法/像素，**或** `auto`/`post` 帧出现玩法变化或像素差 ≥ 40）
**且** `settle` 帧上**没有**声明的终止条件成立。`frames_drawn` 递增**不再充分**。

**新 P1** = `content_fraction >= 0.008`（推导见 §D.4）+ `bbox_coverage >= 0.12`（保留但**降级为诊断**）。

#### D.2.1 收紧前 / 收紧后：25 个目标从**同一份记录证据**重算

工具 `tools/playability_rescore.py`（新）：它读旧的 `gate.json` + `states/00_settle.json`，
把**冻结的旧规则**和**新规则**各算一遍。**自校验：旧规则逐字复现了全部 24 份记录的 P2/P3 判定（0 处不复现）**，
所以"前后"两列确实来自同一份证据。完整表：`runs/realinput/t131-rescore-from-recorded.json`。

| 目标 | 记录 P2/P3 | 旧规则（复现） | **新 P2/P3** | 变化 | 原因 |
|---|---|---|---|---|---|
| asteroids / breakout / flappy / frogger / lunarlander / match3 / minesweeper / missilecommand / pacman / platformer / pong / rtype / sokoban / spaceinvaders / tetris / towerdefense / bomberman / neg_hud_missing / neg_ui_offscreen | pass/pass | pass/pass | **pass/pass** | — | 动作推动了声明的可观测（或像素），或拒绝有游戏自己的记录且同局另有动作真的推动了玩法 |
| `snake` | pass/pass | pass/pass | **FAIL/FAIL** | **▼▼** | P2：0/5 动作推动玩法（3 个是拒绝豁免、2 个 intent-only），且**没有任何动作推动过玩法**；P3：`settle` 帧 `GameOver=true` + 无玩法推进 + 像素 0 |
| `game2048` | pass/pass | pass/pass | **FAIL/FAIL** | **▼▼** | 4 个方向全部被游戏自己判为 `no_change`（`MovesRejected` 1→4、`GridHash` 恒为 1531428369）；**棋盘 `GridString` 全 0、`TilesInUse=0`**，即从来没种下棋子；P3 无任何玩法推进 |
| `puzzlebobble` | pass/pass | pass/pass | **FAIL/pass** | **▼** | `pb_left`/`pb_right` 只改 `AngleIndex`（意图索引，**0 像素变化**）→ intent-only；`pb_shoot` 正常（`ProjActive`/`ProjRow`） |
| `neg_black_screen` | **pass/pass** | pass/pass | **FAIL/FAIL** | **✔ 抓住** | snake 的副本：负变体第一次被 P2/P3 抓住（原来只有 P1 抓） |
| `neg_input_dead` | FAIL/pass | FAIL/pass | **FAIL/FAIL** | **✔ 抓住** | mine sweeper 副本的 `PollInput=false`：只有 `Elapsed`/`Ticks` 变化 → P3 也翻了 |
| `neg_frozen` | FAIL/FAIL | FAIL/FAIL | FAIL/FAIL | — | `process_mode=4`，无任何变化 |
| `neg_hud_missing` | pass/pass | pass/pass | pass/pass | — | UI 缺失由 P7 负责（已 FAIL），游戏逻辑本身正常 |
| `neg_ui_offscreen` | pass/pass | pass/pass | pass/pass | — | 同上 |

**因此翻红的 3 款正向游戏，逐个定性**：

1. **`snake` = 真游戏缺陷**（不是判据假阳性）。证据链完整：内部状态 + 游戏自己的 stdout + 读图 + 场景/源码。
   1.52 秒自撞、无重开键、第一帧即结束画面。**判红是对的。**
2. **`game2048` = 真游戏缺陷**。`states/00_settle.json` 的 `GridString = "0,0,0,0/0,0,0,0/0,0,0,0/0,0,0,0"`、
   `TilesInUse=0`、`MaxTile=0`、`EmptyCells=16`；四个方向都被 `Move()` 判 `reason=no_change`。
   即：**开局没有生成初始棋子**，玩家无论按什么都不会动。旧门报 P1..P7 全 PASS。**判红是对的。**
3. **`puzzlebobble` = 判据边界情况，我判"留下红"，并接受它可能是声明问题**。
   `pb_left/right` 只改 `AngleIndex`，**像素差 0**——按 X12 的口径（"仅 Direction 这类元状态"不算），
   瞄准指数与"方向"同族，故不计；两条出路写明：
   (a) 游戏侧把瞄准指示器画出来（那就是真实缺陷：**玩家按左右看不到任何东西**）；
   (b) 声明侧把 `AngleIndex` 明确列为玩法可观测并给出理由。
   任务书要求"给出收紧前后的对比并说明哪些款翻红、原因是什么"，这条按原样留着，不偷偷放宽。

**收紧后的 5 个负变体**（`--only-p7` 之外的全量口径）：
`neg_black_screen`（P1/P2/P3/P7 全 FAIL）、`neg_input_dead`（P2/P3/P5/P6 FAIL）、
`neg_frozen`（P2/P3/P5/P6 FAIL）、`neg_hud_missing`（P7 FAIL）、`neg_ui_offscreen`（P7 FAIL）。
**两个原来会溜过去的负变体（`neg_black_screen`、`neg_input_dead`）现在被抓住**——这是收紧带来的直接收益。

#### D.2.2 收紧后的**真重跑**（20 款 + 5 个负变体，不是重算）

命令见 §F.1 第 5 条，输出根 `runs/playability/t131-after/`（总表 `playability.json`）。

```
totals: {"games": 25, "playable": 17, "not_playable": 8,
         "per_criterion_fail": {"P1": 2, "P2": 6, "P3": 5, "P4": 0, "P5": 2, "P6": 2, "P7": 3},
         "per_criterion_measured": {"P1": 25, "P2": 25, "P3": 25, "P4": 25, "P5": 25, "P6": 25, "P7": 25}}
```

| 目标 | 收紧前（记录的旧运行） | **收紧后（真重跑）** | 与 §D.2.1 的重算一致？ |
|---|---|---|---|
| 17 款正向：asteroids, bomberman, breakout, flappy, frogger, lunarlander, match3, minesweeper, missilecommand, pacman, platformer, pong, rtype, sokoban, spaceinvaders, tetris, towerdefense | P1..P7 全 pass | **P1..P7 全 pass** | ✅ |
| `snake` | P1..P7 全 pass | **P1=FAIL P2=FAIL P3=FAIL**，P4..P7=PASS | ✅ |
| `game2048` | P1..P7 全 pass | **P2=FAIL P3=FAIL**，P1/P4..P7=PASS | ✅ |
| `puzzlebobble` | P1..P7 全 pass | **P2=FAIL**，P1/P3..P7=PASS | ✅ |
| `neg_black_screen` | P1=FAIL，P2..P6=PASS（P7 未跑） | **P1=FAIL P2=FAIL P3=FAIL P7=FAIL** | ✅（负变体第一次被 P2/P3 抓住） |
| `neg_input_dead` | P2=FAIL P5=FAIL P6=FAIL，**P3=PASS** | **P2=FAIL P3=FAIL P5=FAIL P6=FAIL** | ✅（P3 现在也翻） |
| `neg_frozen` | P2=FAIL P3=FAIL P5=FAIL P6=FAIL | P2=FAIL P3=FAIL P5=FAIL P6=FAIL | ✅ |
| `neg_hud_missing` | P1..P6=PASS（P7 未跑） | P1..P6=PASS，**P7=FAIL** | ✅ |
| `neg_ui_offscreen` | P1..P6=PASS，P7=FAIL | P1..P6=PASS，**P7=FAIL** | ✅ |

重跑给出的 `why` 是**可核对的一句话**，例如 snake 的 P3：

> `frames_drawn 258 -> 1130 (advanced=True); gameplay progress: autonomous=False (from [] / pixel 0),
> input-round=False (from []); declared terminal at settle=True; state changes seen during the input round=8
> (of which gameplay=0); the game is ALREADY in a declared terminal state at the settle frame
> ([{"field": "GameOver", ...}]), so nothing it draws afterwards can be progress; ...`

以及 `action side effects: left_in_mode=['snake_pause'] restored=['snake_pause'] not_restorable=[]`
—— **副作用恢复在真跑里生效**（X13）。

**顺带观察到的既存缺陷（不在本任务范围，未修，点名留给决策者）**：
每一次门运行都会走到 `agent` 段并抛
`EXCEPTION: AttributeError: 'ScriptedAgent' object has no attribute 'last_evidence'`。
它**不是本轮引入**：旧代码的 `runs/playability/t131-before/neg_ui_offscreen/summary.txt` 里就有同一行；
P1..P7 在它之前就已算完（本次 25 款全部拿到完整判据），受影响的只有 `--agent` / `--visual-agent` 段。

#### D.2.3 交叉自校验（两份产物互相钉住）

* 对 **旧的** 20+5 份记录跑重算：新规则翻红集合 = {snake, game2048, puzzlebobble(P2), neg_black_screen, neg_input_dead(P3)}；
* 对 **新重跑的** 25 份产物再跑一次重算（`--runs-root runs\playability\t131-after`，输出
  `runs/realinput/t131-rescore-after-live.json`）：**新规则逐款复现了重跑自己的 P2/P3（25/25 一致）**，
  而"冻结的旧规则"**恰好只在那 5 个翻转款上不一致**——这是对"翻转来自新规则而不是来自运行抖动"最直接的证明。

### D.3 X13 —— 动作副作用的恢复与声明 + 每帧 marker

* **恢复**：`games.*.mode_actions` 声明"哪个动作会留下持久模式 / 用什么恢复 / 哪个 marker 能证明"。
  当前只有 `snake_pause`（`Paused` 为 true 时 `_Process` 直接返回）。
  门在输入轮之后、后置帧之前执行：读 marker → 若处于激活态则按声明的恢复动作**再按一次** →
  **读回 marker** → 记录。冒烟运行的日志：
  `action side effects: left_in_mode=['snake_pause'] restored=['snake_pause'] not_restorable=[]`
  证据：`runs/playability/t131-smoke/snake/gate.json -> action_side_effects` 与
  `criteria.P3.action_side_effects`。
  若某动作**没有**声明恢复，门会把它记进 `not_restorable` 并写明"游戏被留在这个模式里，
  之后每一帧的 marker 都带着它"——**不允许静默**。
* **每帧 marker**：`capture()` 把与该帧同一次状态读取的 marker 写进帧记录，
  `criteria.P3.marker_timeline` 给出全帧时间线。snake 的前 8 帧样例：

| 帧 | label | px vs prev | `Paused` | `GameOver` | `LoseReason` | `Ticks` | `Score` | `ms` | `drawn` | `physics` |
|---|---|---|---|---|---|---|---|---|---|---|
| 1 | settle | None | false | **true** | **wall** | 19 | 10 | 6218 | 22 | 158 |
| 2 | auto1 | 0 | false | true | wall | 19 | 10 | 8015 | 29 | 206 |
| 3 | auto2 | 0 | false | true | wall | 19 | 10 | 9524 | 35 | 247 |
| 4 | auto3 | 0 | false | true | wall | 19 | 10 | 11075 | 41 | 288 |
| 5 | a00_snake_up_parse_pre | 0 | false | true | wall | 19 | 10 | 12121 | 45 | 313 |
| 6 | a00_snake_up_parse_ctl | 0 | false | true | wall | 19 | 10 | 13660 | 51 | 354 |
| 7 | a00_snake_up_parse_act | 0 | false | true | wall | 19 | 10 | 15471 | 58 | 402 |
| 8 | a01_snake_down_parse_pre | 0 | false | true | wall | 19 | 10 | 16757 | 63 | 435 |

  **"静止帧是否合法"现在可以从 artifact 直接判**：时钟在走（`ms`/`drawn`/`physics` 递增）、
  而 `GameOver=true` 且 `Ticks=19` 冻结 → **静止是必然的，且原因可指认**；
  `snake_pause` 之后 `Paused` 会被恢复成 false（恢复点在后置帧之前），不再污染后置帧。

### D.4 X14 —— 重推 P1 阈值 + snake 帧逐项清单 + P7 交叉核对

**(a) 旧阈值的问题（两个，都被实测打穿）**

1. `min_content_fraction = 0.004`（0.4%）**低于任何真实游戏的 settle 帧**，从来就没有依据。
   实测分布（`runs/realinput/_scripts/p1_metrics.py` 打印全表，25 个目标）：

| game | 旧 P1 | content% | bboxcov% | **bbox_fill%** | content px | bbox |
|---|---|---|---|---|---|---|
| `snake` | pass | **0.6000** | 33.0000 | **1.818** | 2880 | `[0,0,600,264]` |
| `rtype` | pass | **1.0988** | 95.6400 | **1.149** | 5274 | `[0,18,797,576]` |
| `pong` | pass | 1.8196 | 86.4800 | 2.104 | 8734 | `[24,0,752,552]` |
| `asteroids` | pass | 3.0981 | 67.0367 | 4.622 | 14871 | `[21,20,676,476]` |
| `missilecommand` | pass | 4.5846 | 91.9983 | 4.983 | 22006 | `[14,18,764,578]` |
| `breakout`/`neg_frozen` | pass | 6.5873 | 49.4875 | 13.311 | 31619 | `[21,21,444,535]` |
| …（中段略）… | pass | … | … | … | … | … |
| `tetris` | pass | 48.5983 | 50.6183 | 96.009 | 233272 | `[20,38,502,484]` |
| `neg_black_screen` | **FAIL** | 0.0000 | 0.0000 | 0.000 | 0 | `[0,0,0,0]` |

2. `bbox_coverage` 是**跨度**不是**填充**：snake 用"左上角一颗 24×24 食物 + (504,240) 的 96×24 蛇身"
   刷出 **33% 覆盖率**（`bbox=[0,0,600,264]`），而它的 bbox 填充率只有 **1.818%**。
   反过来 `rtype` 是**合法的稀疏射击游戏**（1.099% 内容、95.6% 跨度、1.149% 填充）——
   所以**填充率也不能当阈值**，否则会误杀 rtype。

**(b) 选定值与推导依据（对比旧值）**

| 指标 | 旧值 | **新值** | 推导依据 |
|---|---|---|---|
| `P1_MIN_CONTENT_FRACTION` | 0.004 | **0.008** | 取"能保住 20 款正向、卡住 snake"的最大整数百分位：20 款 settle 帧的**最低健康值 = rtype 1.099%**，病态样本 = snake 0.600%。0.8% 在两者之间：距 snake **1.33×**、距 rtype **1.37×**，且正好是旧值的 **2×**。**如实标注：这是在 1 个病态样本上"为分离而拟合"，不是标定**（n=1 无法谈概率标定） |
| `P1_MIN_BBOX_COVERAGE` | 0.12 | **0.12（保留，但降级为诊断）** | 保留它作"内容没有挤在一个角"的粗守卫（全部真实样本都远高于 0.12）；**不再作为"内容铺满画面"的证据**，因为 snake 的反例（两个对角小物 → 33%）证明跨度阈值做不到这件事。新增 `bbox_fill` 只**记录不判定** |
| `P1` 判定 | 老两条 | 老两条（新值）+ 记录 `bbox_fill` | 每条 `why` 现在自带 `bbox_fill … (recorded, NOT a threshold)` |

**新 P1 的效果**：25 个目标里**只有 snake 翻红**（0.600% < 0.8%），
`neg_black_screen` 本来就是 FAIL（0.000%），其余全部保持原判定——包括最低的 `rtype`（1.099%）。

**(c) snake 这一帧里到底有什么（读图 + 场景树/状态交叉核对）**

| 项 | 内容 | 来源 |
|---|---|---|
| 整窗遮罩 | `/root/Main/Status`：`ColorRect` `800×600`，`color=Color(0.85,0.1,0.1,0.35)`，`visible=true`（`GameOver` 时被置 true） | `scenes/main.tscn:231-235`、`SnakeGame.cs:430/477` |
| 复合结果 | 遮罩下背景 `Color(0.05,0.09,0.07)` → `0.35×217+0.65×13≈84`，实测 `bg=[88,24,24]` | 场景文件 + `analyse_frame` |
| 蛇身 | 4 段 `SnakeSeg00..03` `ColorRect 24×24`，`Color(0.24,0.68,0.33)`，位于 `x=504..600, y=240`（= 格 21..24, 行 10） | `states/00_settle.json` 的 `pos=[576,240,24,24]` 等 |
| 食物 | `/root/Main/Food` `24×24` `Color(0.98,0.3,0.3)`，**位于 (0,0)**（左上角） | 同上 + `SNAKE_FOOD cell=0,0` |
| 网格线 | 7 条竖 + 6 条横，`Color(0.1,0.17,0.14)`；遮罩下与背景差 ≈5 < `PIXEL_DELTA=16` → **不计入 content** | 场景文件 + 复合计算 |
| HUD / 分数 / 文字 | **不存在**（snake 的场景里没有任何 `Label`，全场景只有 `Background`/`GridLine*`/`SnakeSeg*`/`Food`/`Status`） | `scenes/main.tscn` 全文 |
| 相机/缩放 | 正常：OS 窗口 `800×600` = root viewport `800.0×600.0` = 声明 `[800,600]`，`stretch mode="canvas_items"` | `gate.json -> window_conformance` |

**判定**：**不是渲染缺陷、不是相机/缩放错误，而是"渲染的本来就是结束画面"**——
真正的缺陷在游戏逻辑（自撞 + 无重开），P1 旧阈值只是**把这个结束画面误报成"可见性合格"**。
另外顺手发现一条设计缺口：**snake 没有任何 HUD/分数显示**（TASK-116 的 P7 声明只检查
`Background`/`Food`/`SnakeSeg00`，所以 P7 看不到这一点）。

**(d) P7 交叉核对**

`runs/playability/t130-p7-summary.json`：**20 款正向的 P7 全部 PASS**，其中
`snake: pass, why="all 3 declared UI item(s) are present, visible and on screen: field, food, head"`。

**所以 P1 与 P7 对 snake 的判定并不相反（都 PASS）——而两个 PASS 都是盲的，必须点名：**

* P7 检查的是**声明的节点在不在、可不可见、有没有面积**。snake 的 `Background`/`Food`/`SnakeSeg00`
  确实存在、`visible_in_tree=true`、面积达标 —— 所以 P7 pass **在它自己的问题范围内是正确的**；
* 但 P7 无法表达"这块棋盘上盖着一个结束遮罩、游戏已经死了"，也不检查"应该有分数/HUD 却一个都没有"；
* 结论：**P7 与 P1 不是互相矛盾，而是互补地都没覆盖这个失效形态**。
  真正抓住它的是**新的 P2/P3（玩法推进 + settle 活性）**与**新的 P1 阈值（0.6% < 0.8%）**，
  三者一起才把 snake 判红（冒烟运行：`P1=FAIL P2=FAIL P3=FAIL P4..P7=PASS`）。
* P7 侧的可改进点（**只提，不在本任务实现**）：给 snake 声明一个"必须存在的分数 `Label`"，
  那么"没有 HUD"这件事就会有一条机器判据 —— 也就是说 P7 的声明面本身还可以收紧。

---

## E. "本机限制 vs 游戏缺陷"的明确区分

| 现象 | 归类 | 依据 |
|---|---|---|
| 真人按键无反应 | **不是本机限制** | `display_active=Enabled`；`SetForegroundWindow` 可**换**窗口；`SendInput` 1/1；真实键确实改变了 pong/tetris/snake 的状态与世界（§A.3） |
| snake 画面无变化 | **游戏缺陷 + 判据缺陷** | 第一帧前 `GameOver=true`（自撞 1.52 s）；无重开键；旧 P1/P2/P3 用元状态与 `frames_drawn` 放行 |
| game2048 画面无变化 | **游戏缺陷** | `GridString` 全 0、`TilesInUse=0`，四个方向均 `reason=no_change` |
| puzzlebobble 瞄准无变化 | **判据边界（可能是游戏侧可见性缺陷）** | `AngleIndex` 变、像素差 0；两条出路见 §D.2 |
| 门把游戏留在暂停态 | **门侧伪影（已修）** | `snake_pause` 留 `Paused=true` 未恢复；现在恢复并读回（§D.3） |
| 注入 SPACE 没触发发球 | **探针侧（已修）** | prep 动作前没有强制焦点；修正后 stdout 出现 `PONG_SERVE`（§A.2） |
| 真实键**无效**的情形 | 本轮**没有出现**；一旦出现，焦点与送达成立即判"游戏侧输入未被 OS 事件驱动" | 结论三选一的第 ③ 支（本轮不适用） |

---

## F. 可重跑命令（逐条，X9）+ 自查

### F.1 命令

（全部从 `F:\moonbit-hof-rs\godot-mcp` 出发，`cmd` / `pwsh` 均可；**无 shell 重定向**）

```text
:: 0) 环境事实（只读）
nvidia-smi --query-gpu=name,display_active,display_mode --format=csv
query session

:: 1) X1 只读能力探测（写 runs\realinput\_env\env.json）
python tools\real_input_probe.py env

:: 2) SendInput 结构体自检（x64 sizeof(INPUT)==40）
python tools\real_input_probe.py selftest

:: 3) A 段实测：发布版 exe，真实键 vs 合成注入（互逆动作对循环 + 对照窗）
python tools\real_input_probe.py run --game pong --mode exe --actions pong_left_up pong_left_down --prep-actions pong_serve --hold 0.12 --control-seconds 0.24 --port 9931 --show-nodes /root/Main/Ball /root/Main/PaddleLeft /root/Main/PaddleRight /root/Main/ScoreLeft /root/Main/ScoreRight
python tools\real_input_probe.py run --game tetris --mode exe --actions tetris_left tetris_right --hold 0.12 --control-seconds 0.24 --port 9932
python tools\real_input_probe.py run --game snake --mode exe --actions snake_left snake_right --hold 0.12 --control-seconds 0.24 --port 9933 --show-nodes /root/Main /root/Main/SnakeSeg00 /root/Main/Food

:: 4) X12 收紧前后的同证据重算（含旧规则自校验）
python tools\playability_rescore.py --extra-roots runs\playability\t131-before --json runs\realinput\t131-rescore-from-recorded.json

:: 5) X12/X13/X14 收紧后的全量重跑：20 款 + 5 个负变体
python tools\playability_gate.py --all --exercise neg_input_dead neg_black_screen neg_frozen neg_hud_missing neg_ui_offscreen --agent scripted --out-root runs\playability\t131-after --port 9961

:: 6) P7 交叉核对（TASK-130 已有，直接复用）
python tools\playability_gate.py --all --exercise neg_input_dead neg_black_screen neg_frozen neg_hud_missing neg_ui_offscreen --only-p7 --out-root runs\playability\t130-p7 --port 9913

:: 7) 报告辅助脚本（都在 runs\realinput\_scripts\，只读证据）
python runs\realinput\_scripts\p1_metrics.py
python runs\realinput\_scripts\changed_keys.py
python runs\realinput\_scripts\per_action.py pong snake game2048
python runs\realinput\_scripts\b_table.py pong 20
python runs\realinput\_scripts\dump_real_input.py pong
python runs\realinput\_scripts\dump_steps.py pong
python runs\realinput\_scripts\env_values.py
python runs\realinput\_scripts\check_patch_scope.py
```

**未触发重建 / 十道门**（铁律 8）：本任务**没有改引擎模块**——
改动只在 `tools/*.py`、`tools/playability_controls.json`、`recovery/**` 与 `DECISIONS.md`；
`godot-mcp/godot/` 一个字节没动（`git -C godot status --short` 只有 TASK-130 之前就在的未跟踪 `uid_cache.bin`）。
依据：任务书 §3.8；且 `docs/reports` 之外没有触碰 `modules/mcp_server`。

### F.2 铁律与文件所有权自查

* 无 shell 重定向：全部输出走 `-o` / `--out-root` / `--json` / Python `io.open` / `subprocess` 管道；
  `git show` 也走 Python 采集（`runs/realinput/_scripts/check_patch_scope.py`），没有 `>`。
* 未改 20 款正式工程：`projects/<game>/` 未被写入（只读源码与场景）；
  新增声明写在 `tools/playability_controls.json`，负变体语义未改（TASK-130 的 `neg_*` 一个都没动，只重跑）。
* 未杀 8080/8081、未动两个 venv、未动 `F:\models\**`、未动 TASK-130 产物。
* 端口：`9931 / 9932 / 9933 / 9941 / 9951 / 9961`，跑前 `kill_what_holds` 查占用，全部与 9877/9888/9889/8080/8081 无关。
* 未为了"让真实键生效"去改游戏的输入映射或工程设置（**先测量**：结论是根本不需要改）。
* 独占清单以外的文件只新增（`tools/playability_rescore.py`、`runs/realinput/**`、`recovery/tasks/TEMPLATE-logic-feedback.md`、本报告）。

### F.3 两仓 git（提交后）

**外层仓 `F:\moonbit-hof-rs`（`master`）**：本任务提交 `03692fd`（8 files changed, 5763 insertions(+), 243 deletions(-)）

```text
03692fd feat(godot-mcp): TASK-131 (D173/D174/D175) - real OS-key delivery is proven on this machine ...
14c2564 docs(godot-mcp): TASK-130 - note the follow-up commit in the report so the recorded HEAD matches the real HEAD
ebab184 docs(godot-mcp): TASK-130 - record the final commit id and the post-commit git log/status ...
8cd0127 feat(godot-mcp): TASK-130 (D171/D172) - ...            <- 本任务的基线
f39d4e7 docs(godot-mcp): TASK-129 - record the final commit id ...

$ git status --short
?? godot-mcp/recovery/tasks/TASK-132.md
```

**嵌套引擎仓 `F:\moonbit-hof-rs\godot-mcp\godot`（自带 `.git`）**：本任务**零字节改动**

```text
ba1587c71e fix(mcp_server): TASK-112 - ...                      <- 与本任务无关，仍是 HEAD
3fdabe2d9a fix(godot-mcp): TASK-110 - ...
1f9d0cb1c9 modules/mcp_server: task103 - ...
1c7f5c07a1 modules/mcp_server: task103 (X-1) - ...
e041cae270 modules/mcp_server: task099 - ...

$ git status --short
?? uid_cache.bin                                                <- 本任务之前就在
```

**两点必须点名**（铁律 9：别人的遗留改动不要替他提交）：

1. `godot-mcp/recovery/tasks/TASK-132.md` 在本任务执行期间出现，**不是我的文件**，**没有被我提交**，留给决策者。
2. 引擎仓的未跟踪 `uid_cache.bin` 同理（TASK-130 之前就在）。

---

## G. 遗留风险与下一步建议（交给决策者裁决，本任务不擅自扩大范围）

1. **两个真游戏缺陷未修**（本任务只做"判定"，修游戏属于另一批工作）：
   * `snake`：`_Ready()` → `ResetSnake()` 把方向设为 `(1,0)` 且 `_Process` 立刻步进，1.52 秒自撞右墙；
     InputMap 无重开键；类注释 "The snake starts parked" 与实现不符。修法方向（供参考）：
     初始方向置零并等待第一个方向键（与 pong/breakout 的确定性规则一致）+ 加一个重开键。
   * `game2048`：开局没有生成初始棋子（`GridString` 全 0、`TilesInUse=0`）。修法方向：
     `_Ready()`（或首次 `Move` 之前）按设计生成 2 个随机/固定棋子。
2. **`puzzlebobble` 的瞄准可见性**：`pb_left/right` 只改 `AngleIndex` 且像素差 0。二选一（画出来 / 声明为可观测）。
3. **`P7` 对 snake 是 PASS**：P7 只检查声明节点；建议给它声明一个"必须存在的分数 `Label`"，
   这样"没有 HUD"就会有一条机器判据（这属于 P7 声明面的收紧，不在本任务内）。
4. **既存缺陷未修**：`--agent` 段的 `'ScriptedAgent' object has no attribute 'last_evidence'`
   （旧代码同样存在；不影响 P1..P7，但会让 `--agent` / `--visual-agent` 段静默失效）。
5. **读图的分辨率边界**：23 格 filmstrip 是逐格看的（每格 210px 宽），HUD 小字类结论一律以状态字段为准；
   若以后要求"每帧全尺寸原图"级别的读图证据，需要把 `--visual-frames` 类的机制推广到逐帧。
6. **真实键结论的可迁移性**：本结论只在**本机、本次会话**成立；别的机器/会话必须重跑
   `real_input_probe.py env`（`display_active`、前台可切换性、`SendInput` 返回）再引用。
7. **`refusal_evidence` 豁免是一个可被滥用的口子**：它要求"同局至少一个动作真的推动了玩法"，
   但一个**部分动作坏掉**的游戏仍可能靠它蒙过个别动作。建议下一批把"每个动作必须要有
   玩法证据**或**一个明确的、逐动作的拒绝声明"再收紧一档（本任务未做，避免一次改太多）。

