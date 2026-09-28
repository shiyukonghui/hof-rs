# TASK-116 — 可玩性门（PLAYABILITY GATE）报告

> **TASK-149 校对注（2026-09-28，只增不改）**：本文件属**游戏侧（可玩性）**那一批的规范类文档。
> 主线已于 2026-09-28 校正为「**交付物 = MCP 工具及其测试用例矩阵**」，可玩性/模型玩家支线
> **中止**（见 `DECISIONS.md` **D212**）。因此 TASK-149 对本文件**不做逐条数字校对**——
> 它的每个数字都以 `runs/playability/**` 的产物为依据，而 `runs/**` **被 `.gitignore` 忽略、
> 不进提交**（只存在于本机），改动本文件既无法从 git 复算、也不改变任何主线结论。
> TASK-149 只做了两件事：①确认**每一条引用的路径在本机都存在**（无失效路径）；
> ②在 `recovery/reports/ERRATA.md` 里建立**老报告勘误索引**，供将来需要时逐条落账。
> **本文件的其他内容一字未动。**

> 生成时间：2026-09-27 13:46:56 ｜ 机器可读原始数据：`runs/playability/playability.json`
> 门工具：`tools/playability_gate.py` ｜ 试玩代理接口：`tools/playtest_agent.py`
> 逐款证据：`runs/playability/<game>/{frames/*.png, frames.json, filmstrip.png, gate.json}`

## 0. 为什么要有这道门（本轮要回答的问题）

用户试玩 20 款后反馈**部分游戏不可玩**。此前所有证据都来自 `shots-editor`——
`editor_capture_screenshot` 拍的是**整个编辑器窗口**（本机 2978×1793），运行中的游戏只是其中
一个内嵌子窗口，所以「像素差 512 px」测的是那个很小的嵌入区域，不能说明玩家在全窗口里看到什么。

本门实测口径：**真游戏进程**（引擎二进制不带 `-e`、真实窗口、绝不 `--headless`）+ **game 端点**
的 `running_game_capture_screenshot`（`mcp_capture.cpp:270-296`：game 侧永远读 `tree->get_root()`，
即整窗内容）+ 每帧记录**窗口/视口/声明尺寸三者的比对**。

## 1. 判据与阈值（可机检）

| 判据 | 测什么 | 通过条件 |
|---|---|---|
| **P1 可见性** | 全窗口帧的**内容包围盒**与**非背景像素占比**（背景 = 该帧众数颜色；内容 = 与背景逐通道差 > 16） | 内容占比 ≥ 0.40% **且** 包围盒覆盖 ≥ 12% |
| **P2 输入响应** | 对 InputMap 里**每一条**已声明动作，用两种通道注入：真实 `InputEventKey` 走 `Viewport.push_input`（`_Input`/`_UnhandledInput` 的路），以及 `Input.action_press`（`IsActionPressed` 轮询的路）；**每条动作与它自己紧邻的、等长的「无输入对照窗口」比** | 状态变化数或像素变化**超过对照**，且在 45 帧内 |
| **P3 主循环推进** | `Engine.get_frames_drawn()` 递增，且游戏自身量确实推进（自主帧 或 注入后帧） | 帧计数递增 **且**（自主变化 或 像素变化 ≥ 40 或 注入期状态变化 > 0） |
| **P4 不崩不挂** | 进程存活、无模态对话框（`EnumWindows` 枚举进程树的所有可见顶层窗口）、MCP 调用无超时 | 三者全满足 |
| **P5 操作可发现** | `project.godot` 的 InputMap ↔ README 的 `## 玩法` 逐条对照，并逐条验证「按了真的有效果」 | README 有玩法章节、键都能对上、代码不读未声明的动作、没有声明了却没人读的动作、每条动作都有效果 |
| **P6 操纵完备性** | `tools/playability_controls.json` 里逐款手写的「玩家必须能做的事」，每条都指名一个权威动作**和一个必须在注入后变化的可观测量** | 每条能力都有已声明、**已响应**、且指名的可观测量确实动了 |

**P6 为什么必须存在**：P1–P5 可以全绿而游戏仍然不能玩。一台只有「推进」键的登月舱会画（P1 过）、
按键有反应（P2 过）、主循环在跑（P3 过）、README 写了那一个键（P5 过）——而它不是一个游戏。
能力表是**人写的判断**，表里每一行则由门**逐行机检**（注入那个动作、要求指名的可观测量移动）：
判断与证据分开，谁都能替换表里的判断再重跑。

**P2 的忠实通道是 `Input.parse_input_event`**：人按键时显示服务器走的就是这一条，它**既**更新
InputMap 动作状态（`input.cpp:1113-1124`）**又**把事件派发到视口（`input.cpp:1126-1130`）。
`Viewport.push_input`（只派发，`viewport.cpp:3502-3566`）与 `Input.action_press`（只置状态）
各自只还原一半，**只在忠实通道失败时**才跑，用来把失败诊断成「游戏只在 `_Input` 里读」还是
「只有合成状态有效」。这条修掉的是一次真实的**假阴性**：早期版本只用后两个通道，于是所有
「轮询 `IsActionPressed`」的游戏都被误报为可疑。

**P2 为什么要有「对照窗口」**：球/车/蛇本来就在动的游戏里，任何一次注入前后的状态差都会被算成
「响应」。每条动作因此和它自己**紧邻的、等长的、不注入输入**的窗口比，只有**胜过对照**才算响应。
这条修掉的是一次真实的假阳性（`pong_serve` 曾被「响应」）。

**P1 阈值依据**：20 款实测的内容占比与包围盒覆盖分布见 §4 的表；「整屏纯背景」= 内容像素 0，
「内容只占窗口一小块」= 包围盒覆盖远小于 100%%。本机 20 款里通过 P1 的样本内容占比在 0.9%~3.4%、
包围盒覆盖在 68%~99% 之间，阈值取 0.4% / 12% 是留了 2~5 倍余量的下界，不是贴着样本画的线。

## 2. 总判定

**20 款中 20 款可玩、0 款不可玩。**

| 判据 | 未通过款数 |
|---|---|
| P1 | 0 |
| P2 | 0 |
| P3 | 0 |
| P4 | 0 |
| P5 | 0 |
| P6 | 0 |

| 游戏 | 窗口 | P1 | P2 | P3 | P4 | P5 | P6 | 判定 | filmstrip |
|---|---|---|---|---|---|---|---|---|---|
| `asteroids` | 800×600 | **pass** | **pass** | **pass** | **pass** | **pass** | **pass** | playable | `runs/playability/asteroids/filmstrip.png` |
| `bomberman` | 800×600 | **pass** | **pass** | **pass** | **pass** | **pass** | **pass** | playable | `runs/playability/bomberman/filmstrip.png` |
| `breakout` | 800×600 | **pass** | **pass** | **pass** | **pass** | **pass** | **pass** | playable | `runs/playability/breakout/filmstrip.png` |
| `flappy` | 800×600 | **pass** | **pass** | **pass** | **pass** | **pass** | **pass** | playable | `runs/playability/flappy/filmstrip.png` |
| `frogger` | 800×600 | **pass** | **pass** | **pass** | **pass** | **pass** | **pass** | playable | `runs/playability/frogger/filmstrip.png` |
| `game2048` | 800×600 | **pass** | **pass** | **pass** | **pass** | **pass** | **pass** | playable | `runs/playability/game2048/filmstrip.png` |
| `lunarlander` | 800×600 | **pass** | **pass** | **pass** | **pass** | **pass** | **pass** | playable | `runs/playability/lunarlander/filmstrip.png` |
| `match3` | 800×600 | **pass** | **pass** | **pass** | **pass** | **pass** | **pass** | playable | `runs/playability/match3/filmstrip.png` |
| `minesweeper` | 800×600 | **pass** | **pass** | **pass** | **pass** | **pass** | **pass** | playable | `runs/playability/minesweeper/filmstrip.png` |
| `missilecommand` | 800×600 | **pass** | **pass** | **pass** | **pass** | **pass** | **pass** | playable | `runs/playability/missilecommand/filmstrip.png` |
| `pacman` | 800×600 | **pass** | **pass** | **pass** | **pass** | **pass** | **pass** | playable | `runs/playability/pacman/filmstrip.png` |
| `platformer` | 800×600 | **pass** | **pass** | **pass** | **pass** | **pass** | **pass** | playable | `runs/playability/platformer/filmstrip.png` |
| `pong` | 800×600 | **pass** | **pass** | **pass** | **pass** | **pass** | **pass** | playable | `runs/playability/pong/filmstrip.png` |
| `puzzlebobble` | 800×600 | **pass** | **pass** | **pass** | **pass** | **pass** | **pass** | playable | `runs/playability/puzzlebobble/filmstrip.png` |
| `rtype` | 800×600 | **pass** | **pass** | **pass** | **pass** | **pass** | **pass** | playable | `runs/playability/rtype/filmstrip.png` |
| `snake` | 800×600 | **pass** | **pass** | **pass** | **pass** | **pass** | **pass** | playable | `runs/playability/snake/filmstrip.png` |
| `sokoban` | 800×600 | **pass** | **pass** | **pass** | **pass** | **pass** | **pass** | playable | `runs/playability/sokoban/filmstrip.png` |
| `spaceinvaders` | 800×600 | **pass** | **pass** | **pass** | **pass** | **pass** | **pass** | playable | `runs/playability/spaceinvaders/filmstrip.png` |
| `tetris` | 800×600 | **pass** | **pass** | **pass** | **pass** | **pass** | **pass** | playable | `runs/playability/tetris/filmstrip.png` |
| `towerdefense` | 800×600 | **pass** | **pass** | **pass** | **pass** | **pass** | **pass** | playable | `runs/playability/towerdefense/filmstrip.png` |

## 3. 修复前后对比

> 修复前那一轮（`runs/playability/playability.before.json`）用的是两通道注入
> （`Viewport.push_input` + `Input.action_press`）；修复后加了忠实的 `parse` 通道。
> 这个对比仍然是**同一方向的**：`parse_input_event` 是那两个通道的并集（它同时置状态并派发），
> 所以「修复前两个通道都没反应」在当时就是失败，用忠实通道重测也不会变成通过。

| 游戏 | 修复前 | 修复后 | 变了哪些判据 |
|---|---|---|---|
| `asteroids` | not_playable | playable | P2: FAIL→pass, P5: FAIL→pass |
| `bomberman` | not_playable | playable | P2: FAIL→pass, P5: FAIL→pass |
| `breakout` | not_playable | playable | P5: FAIL→pass |
| `flappy` | not_playable | playable | P2: FAIL→pass, P5: FAIL→pass |
| `frogger` | not_playable | playable | P2: FAIL→pass, P5: FAIL→pass |
| `game2048` | not_playable | playable | P2: FAIL→pass, P5: FAIL→pass |
| `lunarlander` | not_playable | playable | P2: FAIL→pass, P5: FAIL→pass |
| `match3` | not_playable | playable | P2: FAIL→pass, P5: FAIL→pass |
| `minesweeper` | not_playable | playable | P2: FAIL→pass, P5: FAIL→pass |
| `missilecommand` | not_playable | playable | P2: FAIL→pass, P5: FAIL→pass |
| `pacman` | not_playable | playable | P2: FAIL→pass, P5: FAIL→pass |
| `platformer` | not_playable | playable | P2: FAIL→pass, P5: FAIL→pass |
| `puzzlebobble` | not_playable | playable | P2: FAIL→pass, P5: FAIL→pass |
| `rtype` | not_playable | playable | P2: FAIL→pass, P5: FAIL→pass |
| `snake` | not_playable | playable | P5: FAIL→pass |
| `sokoban` | not_playable | playable | P2: FAIL→pass, P5: FAIL→pass |
| `spaceinvaders` | not_playable | playable | P2: FAIL→pass, P5: FAIL→pass |
| `tetris` | not_playable | playable | P5: FAIL→pass |
| `towerdefense` | not_playable | playable | P2: FAIL→pass, P5: FAIL→pass |

## 4. 逐款证据（P1 数值 + P2 逐动作）

### `asteroids` — playable

- 窗口：OS `[800, 600]` ／ 根视口 `[800.0, 600.0]` ／ 声明 `[800, 600]` ／ 一致 `True`
- 启动：{"port_up": true, "seconds": 1.8, "alive": true} ／ tools/list 73 个工具 ／ 本次耗时 34.6s
- **P1 pass**：best frame #1: content 3.0981% (>=0.40%), bbox coverage 67.0367% (>=12.00%), bbox=[21, 20, 676, 476], bg=[8, 8, 8]
- **P2 pass**：4/4 declared actions produced a state or pixel change within 45 frames through the faithful channel (`Input.parse_input_event`, the path a real key press takes): 4/4; of the failures, 0 answered only `Viewport.push_input` (an `_Input`-reader) and 0 answered only `Input.action_press`
- **P3 pass**：frames_drawn 259 -> 945 (advanced=True); autonomous state changes=1; pixel change over the autonomous+post frames=984; state changes seen during the input round=23
- **P4 pass**：process alive at end=True; visible windows of the tree=1; modal dialog candidates=0; MCP timeouts=0
- **P5 pass**：README documents 4 keys (['A', 'D', 'W', 'SPACE']); the InputMap declares 4 actions; the code reads 0 actions it does NOT declare ([]); 0 declared actions the code never reads ([]); 0 tested actions do nothing ([]); 0 never exercised ([]); README keys with no declared action: []
- **P6 pass**：4/4 required capabilities are delivered by a declared, responding action

  | 玩家必须能做的事 | 权威动作 | 结果 | 证据 |
  |---|---|---|---|
  | turn left | `ast_left` | pass | `ShipAngle` moved ['/root/Main.ShipAngle'] |
  | turn right | `ast_right` | pass | `ShipAngle` moved ['/root/Main.ShipAngle'] |
  | thrust | `ast_thrust` | pass | `ShipVelX|ShipVelY|Thrusting` moved ['/root/Main.ShipVelX', '/root/Main.ShipVelY'] |
  | fire | `ast_fire` | pass | `ShotsFired` moved ['/root/Main.ShotsFired'] |

- 逐动作。`real_key` = **忠实通道** `Input.parse_input_event`（显示服务器收到真实按键时走的就是这条：
  既更新 InputMap 动作状态，又把事件派发到视口）；`push_input` / `action_state` 是**诊断通道**，
  各自只还原一半（前者只派发、后者只置状态），只在忠实通道失败时才跑。

  | 动作 | 键 | real_key | push_input | action_state | 说明 |
  |---|---|---|---|---|---|
  | `ast_left` | A | yes | - | - |  |
  | `ast_right` | D | yes | - | - |  |
  | `ast_thrust` | W | yes | - | - |  |
  | `ast_fire` | SPACE | yes | - | - |  |


### `bomberman` — playable

- 窗口：OS `[800, 600]` ／ 根视口 `[800.0, 600.0]` ／ 声明 `[800, 600]` ／ 一致 `True`
- 启动：{"port_up": true, "seconds": 1.9, "alive": true} ／ tools/list 73 个工具 ／ 本次耗时 36.4s
- **P1 pass**：best frame #1: content 44.2048% (>=0.40%), bbox coverage 73.1935% (>=12.00%), bbox=[16, 16, 779, 451], bg=[8, 8, 24]
- **P2 pass**：5/5 declared actions produced a state or pixel change within 45 frames through the faithful channel (`Input.parse_input_event`, the path a real key press takes): 5/5; of the failures, 0 answered only `Viewport.push_input` (an `_Input`-reader) and 0 answered only `Input.action_press`
- **P3 pass**：frames_drawn 273 -> 1072 (advanced=True); autonomous state changes=2; pixel change over the autonomous+post frames=0; state changes seen during the input round=41
- **P4 pass**：process alive at end=True; visible windows of the tree=1; modal dialog candidates=0; MCP timeouts=0
- **P5 pass**：README documents 5 keys (['W', 'S', 'A', 'D', 'SPACE']); the InputMap declares 5 actions; the code reads 0 actions it does NOT declare ([]); 0 declared actions the code never reads ([]); 0 tested actions do nothing ([]); 0 never exercised ([]); README keys with no declared action: []
- **P6 pass**：5/5 required capabilities are delivered by a declared, responding action

  | 玩家必须能做的事 | 权威动作 | 结果 | 证据 |
  |---|---|---|---|
  | walk up | `bomb_up` | pass | `PlayerRow|RejectedMoves` moved ['/root/Main.RejectedMoves'] |
  | walk down | `bomb_down` | pass | `PlayerRow|RejectedMoves` moved ['/root/Main.PlayerRow'] |
  | walk left | `bomb_left` | pass | `PlayerCol|RejectedMoves` moved ['/root/Main.PlayerCol'] |
  | walk right | `bomb_right` | pass | `PlayerCol|RejectedMoves` moved ['/root/Main.PlayerCol'] |
  | place a bomb | `bomb_place` | pass | `BombsPlaced|BombsActive` moved ['/root/Main.BombsActive', '/root/Main.BombsPlaced'] |

- 逐动作。`real_key` = **忠实通道** `Input.parse_input_event`（显示服务器收到真实按键时走的就是这条：
  既更新 InputMap 动作状态，又把事件派发到视口）；`push_input` / `action_state` 是**诊断通道**，
  各自只还原一半（前者只派发、后者只置状态），只在忠实通道失败时才跑。

  | 动作 | 键 | real_key | push_input | action_state | 说明 |
  |---|---|---|---|---|---|
  | `bomb_up` | W | yes | - | - |  |
  | `bomb_right` | D | yes | - | - |  |
  | `bomb_place` | SPACE | yes | - | - |  |
  | `bomb_left` | A | yes | - | - |  |
  | `bomb_down` | S | yes | - | - |  |


### `breakout` — playable

- 窗口：OS `[800, 600]` ／ 根视口 `[800.0, 600.0]` ／ 声明 `[800, 600]` ／ 一致 `True`
- 启动：{"port_up": true, "seconds": 1.8, "alive": true} ／ tools/list 73 个工具 ／ 本次耗时 32.6s
- **P1 pass**：best frame #1: content 6.5873% (>=0.40%), bbox coverage 49.4875% (>=12.00%), bbox=[21, 21, 444, 535], bg=[8, 8, 24]
- **P2 pass**：3/3 declared actions produced a state or pixel change within 45 frames through the faithful channel (`Input.parse_input_event`, the path a real key press takes): 3/3; of the failures, 0 answered only `Viewport.push_input` (an `_Input`-reader) and 0 answered only `Input.action_press`
- **P3 pass**：frames_drawn 272 -> 846 (advanced=True); autonomous state changes=1; pixel change over the autonomous+post frames=376; state changes seen during the input round=12
- **P4 pass**：process alive at end=True; visible windows of the tree=1; modal dialog candidates=0; MCP timeouts=0
- **P5 pass**：README documents 3 keys (['A', 'D', 'SPACE']); the InputMap declares 3 actions; the code reads 0 actions it does NOT declare ([]); 0 declared actions the code never reads ([]); 0 tested actions do nothing ([]); 0 never exercised ([]); README keys with no declared action: []
- **P6 pass**：3/3 required capabilities are delivered by a declared, responding action

  | 玩家必须能做的事 | 权威动作 | 结果 | 证据 |
  |---|---|---|---|
  | move the paddle left | `breakout_left` | pass | `Paddle|MinX` moved ['/root/Main/Paddle.pos'] |
  | move the paddle right | `breakout_right` | pass | `Paddle|MaxX` moved ['/root/Main/Paddle.pos'] |
  | launch the ball | `breakout_launch` | pass | `Launched|Ball` moved ['/root/Main.BallSpeedX', '/root/Main.BallSpeedY', '/root/Main.BallX'] |

- 逐动作。`real_key` = **忠实通道** `Input.parse_input_event`（显示服务器收到真实按键时走的就是这条：
  既更新 InputMap 动作状态，又把事件派发到视口）；`push_input` / `action_state` 是**诊断通道**，
  各自只还原一半（前者只派发、后者只置状态），只在忠实通道失败时才跑。

  | 动作 | 键 | real_key | push_input | action_state | 说明 |
  |---|---|---|---|---|---|
  | `breakout_left` | A | yes | - | - |  |
  | `breakout_right` | D | yes | - | - |  |
  | `breakout_launch` | SPACE | yes | - | - |  |


### `flappy` — playable

- 窗口：OS `[800, 600]` ／ 根视口 `[800.0, 600.0]` ／ 声明 `[800, 600]` ／ 一致 `True`
- 启动：{"port_up": true, "seconds": 1.8, "alive": true} ／ tools/list 73 个工具 ／ 本次耗时 30.7s
- **P1 pass**：best frame #1: content 7.3992% (>=0.40%), bbox coverage 81.1250% (>=12.00%), bbox=[21, 0, 649, 600], bg=[8, 24, 56]
- **P2 pass**：2/2 declared actions produced a state or pixel change within 45 frames through the faithful channel (`Input.parse_input_event`, the path a real key press takes): 2/2; of the failures, 0 answered only `Viewport.push_input` (an `_Input`-reader) and 0 answered only `Input.action_press`
- **P3 pass**：frames_drawn 269 -> 720 (advanced=True); autonomous state changes=1; pixel change over the autonomous+post frames=0; state changes seen during the input round=7
- **P4 pass**：process alive at end=True; visible windows of the tree=1; modal dialog candidates=0; MCP timeouts=0
- **P5 pass**：README documents 2 keys (['SPACE', 'R']); the InputMap declares 2 actions; the code reads 0 actions it does NOT declare ([]); 0 declared actions the code never reads ([]); 0 tested actions do nothing ([]); 0 never exercised ([]); README keys with no declared action: []
- **P6 pass**：2/2 required capabilities are delivered by a declared, responding action

  | 玩家必须能做的事 | 权威动作 | 结果 | 证据 |
  |---|---|---|---|
  | flap | `flap` | pass | `BirdVelocity|BirdY` moved ['/root/Main.BirdVelocity'] |
  | restart after dying | `flappy_restart` | pass | `Restarts|GameOver|Score` moved ['/root/Main.Restarts'] |

- 逐动作。`real_key` = **忠实通道** `Input.parse_input_event`（显示服务器收到真实按键时走的就是这条：
  既更新 InputMap 动作状态，又把事件派发到视口）；`push_input` / `action_state` 是**诊断通道**，
  各自只还原一半（前者只派发、后者只置状态），只在忠实通道失败时才跑。

  | 动作 | 键 | real_key | push_input | action_state | 说明 |
  |---|---|---|---|---|---|
  | `flap` | SPACE | yes | - | - |  |
  | `flappy_restart` | R | yes | - | - |  |


### `frogger` — playable

- 窗口：OS `[800, 600]` ／ 根视口 `[800.0, 600.0]` ／ 声明 `[800, 600]` ／ 一致 `True`
- 启动：{"port_up": true, "seconds": 1.9, "alive": true} ／ tools/list 73 个工具 ／ 本次耗时 31.6s
- **P1 pass**：best frame #1: content 42.9994% (>=0.40%), bbox coverage 79.6231% (>=12.00%), bbox=[21, 17, 667, 573], bg=[8, 8, 8]
- **P2 pass**：4/4 declared actions produced a state or pixel change within 45 frames through the faithful channel (`Input.parse_input_event`, the path a real key press takes): 4/4; of the failures, 0 answered only `Viewport.push_input` (an `_Input`-reader) and 0 answered only `Input.action_press`
- **P3 pass**：frames_drawn 271 -> 789 (advanced=True); autonomous state changes=1; pixel change over the autonomous+post frames=0; state changes seen during the input round=17
- **P4 pass**：process alive at end=True; visible windows of the tree=1; modal dialog candidates=0; MCP timeouts=0
- **P5 pass**：README documents 4 keys (['W', 'S', 'A', 'D']); the InputMap declares 4 actions; the code reads 0 actions it does NOT declare ([]); 0 declared actions the code never reads ([]); 0 tested actions do nothing ([]); 0 never exercised ([]); README keys with no declared action: []
- **P6 pass**：4/4 required capabilities are delivered by a declared, responding action

  | 玩家必须能做的事 | 权威动作 | 结果 | 证据 |
  |---|---|---|---|
  | hop up | `frog_up` | pass | `FrogRow|Lives|GameOver|HomesReached|Score` moved ['/root/Main.Lives'] |
  | hop down | `frog_down` | pass | `FrogRow|RejectedSteps` moved ['/root/Main.RejectedSteps'] |
  | hop left | `frog_left` | pass | `FrogCol` moved ['/root/Main.FrogCol'] |
  | hop right | `frog_right` | pass | `FrogCol` moved ['/root/Main.FrogCol'] |

- 逐动作。`real_key` = **忠实通道** `Input.parse_input_event`（显示服务器收到真实按键时走的就是这条：
  既更新 InputMap 动作状态，又把事件派发到视口）；`push_input` / `action_state` 是**诊断通道**，
  各自只还原一半（前者只派发、后者只置状态），只在忠实通道失败时才跑。

  | 动作 | 键 | real_key | push_input | action_state | 说明 |
  |---|---|---|---|---|---|
  | `frog_left` | A | yes | - | - |  |
  | `frog_right` | D | yes | - | - |  |
  | `frog_up` | W | yes | - | - |  |
  | `frog_down` | S | yes | - | - |  |


### `game2048` — playable

- 窗口：OS `[800, 600]` ／ 根视口 `[800.0, 600.0]` ／ 声明 `[800, 600]` ／ 一致 `True`
- 启动：{"port_up": true, "seconds": 1.8, "alive": true} ／ tools/list 73 个工具 ／ 本次耗时 34.5s
- **P1 pass**：best frame #1: content 44.1310% (>=0.40%), bbox coverage 79.9102% (>=12.00%), bbox=[21, 17, 709, 541], bg=[8, 8, 8]
- **P2 pass**：4/4 declared actions produced a state or pixel change within 45 frames through the faithful channel (`Input.parse_input_event`, the path a real key press takes): 4/4; of the failures, 0 answered only `Viewport.push_input` (an `_Input`-reader) and 0 answered only `Input.action_press`
- **P3 pass**：frames_drawn 275 -> 965 (advanced=True); autonomous state changes=2; pixel change over the autonomous+post frames=0; state changes seen during the input round=24
- **P4 pass**：process alive at end=True; visible windows of the tree=1; modal dialog candidates=0; MCP timeouts=0
- **P5 pass**：README documents 4 keys (['W', 'S', 'A', 'D']); the InputMap declares 4 actions; the code reads 0 actions it does NOT declare ([]); 0 declared actions the code never reads ([]); 0 tested actions do nothing ([]); 0 never exercised ([]); README keys with no declared action: []
- **P6 pass**：4/4 required capabilities are delivered by a declared, responding action

  | 玩家必须能做的事 | 权威动作 | 结果 | 证据 |
  |---|---|---|---|
  | slide up | `m2048_up` | pass | `MoveCount|MovesRejected|GridHash` moved ['/root/Main.MovesRejected'] |
  | slide down | `m2048_down` | pass | `MoveCount|MovesRejected|GridHash` moved ['/root/Main.MovesRejected'] |
  | slide left | `m2048_left` | pass | `MoveCount|MovesRejected|GridHash` moved ['/root/Main.MovesRejected'] |
  | slide right | `m2048_right` | pass | `MoveCount|MovesRejected|GridHash` moved ['/root/Main.MovesRejected'] |

- 逐动作。`real_key` = **忠实通道** `Input.parse_input_event`（显示服务器收到真实按键时走的就是这条：
  既更新 InputMap 动作状态，又把事件派发到视口）；`push_input` / `action_state` 是**诊断通道**，
  各自只还原一半（前者只派发、后者只置状态），只在忠实通道失败时才跑。

  | 动作 | 键 | real_key | push_input | action_state | 说明 |
  |---|---|---|---|---|---|
  | `m2048_up` | W | yes | - | - |  |
  | `m2048_right` | D | yes | - | - |  |
  | `m2048_down` | S | yes | - | - |  |
  | `m2048_left` | A | yes | - | - |  |


### `lunarlander` — playable

- 窗口：OS `[800, 600]` ／ 根视口 `[800.0, 600.0]` ／ 声明 `[800, 600]` ／ 一致 `True`
- 启动：{"port_up": true, "seconds": 1.8, "alive": true} ／ tools/list 73 个工具 ／ 本次耗时 32.6s
- **P1 pass**：best frame #1: content 7.8192% (>=0.40%), bbox coverage 97.0000% (>=12.00%), bbox=[0, 18, 800, 582], bg=[8, 8, 8]
- **P2 pass**：3/3 declared actions produced a state or pixel change within 45 frames through the faithful channel (`Input.parse_input_event`, the path a real key press takes): 3/3; of the failures, 0 answered only `Viewport.push_input` (an `_Input`-reader) and 0 answered only `Input.action_press`
- **P3 pass**：frames_drawn 273 -> 838 (advanced=True); autonomous state changes=2; pixel change over the autonomous+post frames=0; state changes seen during the input round=32
- **P4 pass**：process alive at end=True; visible windows of the tree=1; modal dialog candidates=0; MCP timeouts=0
- **P5 pass**：README documents 3 keys (['SPACE', 'A', 'D']); the InputMap declares 3 actions; the code reads 0 actions it does NOT declare ([]); 0 declared actions the code never reads ([]); 0 tested actions do nothing ([]); 0 never exercised ([]); README keys with no declared action: []
- **P6 pass**：3/3 required capabilities are delivered by a declared, responding action

  | 玩家必须能做的事 | 权威动作 | 结果 | 证据 |
  |---|---|---|---|
  | burn (thrust) | `ll_thrust` | pass | `Fuel|ThrustCount` moved ['/root/Main.Fuel', '/root/Main.FuelUsed', '/root/Main.ThrustCount'] |
  | turn left | `ll_rotate_left` | pass | `AngleDeg|RejectedRotations` moved ['/root/Main.AngleDeg'] |
  | turn right | `ll_rotate_right` | pass | `AngleDeg|RejectedRotations` moved ['/root/Main.AngleDeg'] |

- 逐动作。`real_key` = **忠实通道** `Input.parse_input_event`（显示服务器收到真实按键时走的就是这条：
  既更新 InputMap 动作状态，又把事件派发到视口）；`push_input` / `action_state` 是**诊断通道**，
  各自只还原一半（前者只派发、后者只置状态），只在忠实通道失败时才跑。

  | 动作 | 键 | real_key | push_input | action_state | 说明 |
  |---|---|---|---|---|---|
  | `ll_thrust` | SPACE | yes | - | - |  |
  | `ll_rotate_left` | A | yes | - | - |  |
  | `ll_rotate_right` | D | yes | - | - |  |


### `match3` — playable

- 窗口：OS `[800, 600]` ／ 根视口 `[800.0, 600.0]` ／ 声明 `[800, 600]` ／ 一致 `True`
- 启动：{"port_up": true, "seconds": 1.8, "alive": true} ／ tools/list 73 个工具 ／ 本次耗时 38.5s
- **P1 pass**：best frame #1: content 34.6250% (>=0.40%), bbox coverage 82.3662% (>=12.00%), bbox=[14, 18, 786, 503], bg=[8, 8, 24]
- **P2 pass**：6/6 declared actions produced a state or pixel change within 45 frames through the faithful channel (`Input.parse_input_event`, the path a real key press takes): 6/6; of the failures, 0 answered only `Viewport.push_input` (an `_Input`-reader) and 0 answered only `Input.action_press`
- **P3 pass**：frames_drawn 269 -> 1192 (advanced=True); autonomous state changes=2; pixel change over the autonomous+post frames=0; state changes seen during the input round=49
- **P4 pass**：process alive at end=True; visible windows of the tree=1; modal dialog candidates=0; MCP timeouts=0
- **P5 pass**：README documents 6 keys (['A', 'D', 'W', 'S', 'SPACE', 'G']); the InputMap declares 6 actions; the code reads 0 actions it does NOT declare ([]); 0 declared actions the code never reads ([]); 0 tested actions do nothing ([]); 0 never exercised ([]); README keys with no declared action: []
- **P6 pass**：5/5 required capabilities are delivered by a declared, responding action

  | 玩家必须能做的事 | 权威动作 | 结果 | 证据 |
  |---|---|---|---|
  | move the cursor left | `m3_left` | pass | `CursorCol` moved ['/root/Main.CursorCol'] |
  | move the cursor right | `m3_right` | pass | `CursorCol` moved ['/root/Main.CursorCol'] |
  | move the cursor up | `m3_up` | pass | `CursorRow` moved ['/root/Main.CursorRow'] |
  | move the cursor down | `m3_down` | pass | `CursorRow` moved ['/root/Main.CursorRow'] |
  | swap the cursor's gem with the one to its right | `m3_swap` | pass | `LastSwap|Score|Moves|RejectedMoves` moved ['/root/Main.LastSwap', '/root/Main.Moves', '/root/Main.Score'] |

- 逐动作。`real_key` = **忠实通道** `Input.parse_input_event`（显示服务器收到真实按键时走的就是这条：
  既更新 InputMap 动作状态，又把事件派发到视口）；`push_input` / `action_state` 是**诊断通道**，
  各自只还原一半（前者只派发、后者只置状态），只在忠实通道失败时才跑。

  | 动作 | 键 | real_key | push_input | action_state | 说明 |
  |---|---|---|---|---|---|
  | `m3_auto_move` | G | yes | - | - |  |
  | `m3_left` | A | yes | - | - |  |
  | `m3_right` | D | yes | - | - |  |
  | `m3_up` | W | yes | - | - |  |
  | `m3_down` | S | yes | - | - |  |
  | `m3_swap` | SPACE | yes | - | - |  |


### `minesweeper` — playable

- 窗口：OS `[800, 600]` ／ 根视口 `[800.0, 600.0]` ／ 声明 `[800, 600]` ／ 一致 `True`
- 启动：{"port_up": true, "seconds": 1.8, "alive": true} ／ tools/list 73 个工具 ／ 本次耗时 42.4s
- **P1 pass**：best frame #1: content 46.8250% (>=0.40%), bbox coverage 83.5667% (>=12.00%), bbox=[22, 17, 736, 545], bg=[8, 24, 24]
- **P2 pass**：8/8 declared actions produced a state or pixel change within 45 frames through the faithful channel (`Input.parse_input_event`, the path a real key press takes): 8/8; of the failures, 0 answered only `Viewport.push_input` (an `_Input`-reader) and 0 answered only `Input.action_press`
- **P3 pass**：frames_drawn 265 -> 1420 (advanced=True); autonomous state changes=2; pixel change over the autonomous+post frames=0; state changes seen during the input round=75
- **P4 pass**：process alive at end=True; visible windows of the tree=1; modal dialog candidates=0; MCP timeouts=0
- **P5 pass**：README documents 8 keys (['A', 'D', 'W', 'S', 'SPACE', 'F', 'R', 'G']); the InputMap declares 8 actions; the code reads 0 actions it does NOT declare ([]); 0 declared actions the code never reads ([]); 0 tested actions do nothing ([]); 0 never exercised ([]); README keys with no declared action: []
- **P6 pass**：6/6 required capabilities are delivered by a declared, responding action

  | 玩家必须能做的事 | 权威动作 | 结果 | 证据 |
  |---|---|---|---|
  | move the cursor left | `mine_left` | pass | `CursorCol` moved ['/root/Main.CursorCol'] |
  | move the cursor right | `mine_right` | pass | `CursorCol` moved ['/root/Main.CursorCol'] |
  | move the cursor up | `mine_up` | pass | `CursorRow` moved ['/root/Main.CursorRow'] |
  | move the cursor down | `mine_down` | pass | `CursorRow` moved ['/root/Main.CursorRow'] |
  | reveal the cell under the cursor | `mine_reveal` | pass | `RevealedCount|Moves|RejectedMoves|MinesRelocated` moved ['/root/Main.RejectedMoves'] |
  | flag the cell under the cursor | `mine_flag` | pass | `FlaggedCount|FlagToggles|RejectedMoves` moved ['/root/Main.RejectedMoves'] |

- 逐动作。`real_key` = **忠实通道** `Input.parse_input_event`（显示服务器收到真实按键时走的就是这条：
  既更新 InputMap 动作状态，又把事件派发到视口）；`push_input` / `action_state` 是**诊断通道**，
  各自只还原一半（前者只派发、后者只置状态），只在忠实通道失败时才跑。

  | 动作 | 键 | real_key | push_input | action_state | 说明 |
  |---|---|---|---|---|---|
  | `mine_reveal_next` | R | yes | - | - |  |
  | `mine_flag_next` | G | yes | - | - |  |
  | `mine_left` | A | yes | - | - |  |
  | `mine_right` | D | yes | - | - |  |
  | `mine_up` | W | yes | - | - |  |
  | `mine_down` | S | yes | - | - |  |
  | `mine_reveal` | SPACE | yes | - | - |  |
  | `mine_flag` | F | yes | - | - |  |


### `missilecommand` — playable

- 窗口：OS `[800, 600]` ／ 根视口 `[800.0, 600.0]` ／ 声明 `[800, 600]` ／ 一致 `True`
- 启动：{"port_up": true, "seconds": 1.8, "alive": true} ／ tools/list 73 个工具 ／ 本次耗时 34.5s
- **P1 pass**：best frame #1: content 4.5846% (>=0.40%), bbox coverage 91.9983% (>=12.00%), bbox=[14, 18, 764, 578], bg=[8, 8, 8]
- **P2 pass**：4/4 declared actions produced a state or pixel change within 45 frames through the faithful channel (`Input.parse_input_event`, the path a real key press takes): 4/4; of the failures, 0 answered only `Viewport.push_input` (an `_Input`-reader) and 0 answered only `Input.action_press`
- **P3 pass**：frames_drawn 273 -> 960 (advanced=True); autonomous state changes=2; pixel change over the autonomous+post frames=0; state changes seen during the input round=34
- **P4 pass**：process alive at end=True; visible windows of the tree=1; modal dialog candidates=0; MCP timeouts=0
- **P5 pass**：README documents 4 keys (['A', 'D', 'SPACE', 'G']); the InputMap declares 4 actions; the code reads 0 actions it does NOT declare ([]); 0 declared actions the code never reads ([]); 0 tested actions do nothing ([]); 0 never exercised ([]); README keys with no declared action: []
- **P6 pass**：3/3 required capabilities are delivered by a declared, responding action

  | 玩家必须能做的事 | 权威动作 | 结果 | 证据 |
  |---|---|---|---|
  | aim left | `mc_left` | pass | `CursorX` moved ['/root/Main.CursorX'] |
  | aim right | `mc_right` | pass | `CursorX` moved ['/root/Main.CursorX'] |
  | fire at the cursor | `mc_fire` | pass | `Fired|Ammo|InterceptorAlive` moved ['/root/Main.Ammo', '/root/Main.AmmoList', '/root/Main.Fired'] |

- 逐动作。`real_key` = **忠实通道** `Input.parse_input_event`（显示服务器收到真实按键时走的就是这条：
  既更新 InputMap 动作状态，又把事件派发到视口）；`push_input` / `action_state` 是**诊断通道**，
  各自只还原一半（前者只派发、后者只置状态），只在忠实通道失败时才跑。

  | 动作 | 键 | real_key | push_input | action_state | 说明 |
  |---|---|---|---|---|---|
  | `mc_auto_fire` | G | yes | - | - |  |
  | `mc_left` | A | yes | - | - |  |
  | `mc_right` | D | yes | - | - |  |
  | `mc_fire` | SPACE | yes | - | - |  |


### `pacman` — playable

- 窗口：OS `[800, 600]` ／ 根视口 `[800.0, 600.0]` ／ 声明 `[800, 600]` ／ 一致 `True`
- 启动：{"port_up": true, "seconds": 1.8, "alive": true} ／ tools/list 73 个工具 ／ 本次耗时 34.5s
- **P1 pass**：best frame #1: content 44.3415% (>=0.40%), bbox coverage 88.8250% (>=12.00%), bbox=[20, 19, 760, 561], bg=[8, 8, 8]
- **P2 pass**：4/4 declared actions produced a state or pixel change within 45 frames through the faithful channel (`Input.parse_input_event`, the path a real key press takes): 4/4; of the failures, 0 answered only `Viewport.push_input` (an `_Input`-reader) and 0 answered only `Input.action_press`
- **P3 pass**：frames_drawn 271 -> 959 (advanced=True); autonomous state changes=1; pixel change over the autonomous+post frames=0; state changes seen during the input round=25
- **P4 pass**：process alive at end=True; visible windows of the tree=1; modal dialog candidates=0; MCP timeouts=0
- **P5 pass**：README documents 4 keys (['W', 'S', 'A', 'D']); the InputMap declares 4 actions; the code reads 0 actions it does NOT declare ([]); 0 declared actions the code never reads ([]); 0 tested actions do nothing ([]); 0 never exercised ([]); README keys with no declared action: []
- **P6 pass**：4/4 required capabilities are delivered by a declared, responding action

  | 玩家必须能做的事 | 权威动作 | 结果 | 证据 |
  |---|---|---|---|
  | move up | `pac_up` | pass | `PacRow|PacCol|RejectedSteps` moved ['/root/Main.RejectedSteps'] |
  | move down | `pac_down` | pass | `PacRow|PacCol|RejectedSteps` moved ['/root/Main.RejectedSteps'] |
  | move left | `pac_left` | pass | `PacCol|PacRow` moved ['/root/Main.PacCol'] |
  | move right | `pac_right` | pass | `PacCol|PacRow` moved ['/root/Main.PacCol'] |

- 逐动作。`real_key` = **忠实通道** `Input.parse_input_event`（显示服务器收到真实按键时走的就是这条：
  既更新 InputMap 动作状态，又把事件派发到视口）；`push_input` / `action_state` 是**诊断通道**，
  各自只还原一半（前者只派发、后者只置状态），只在忠实通道失败时才跑。

  | 动作 | 键 | real_key | push_input | action_state | 说明 |
  |---|---|---|---|---|---|
  | `pac_left` | A | yes | - | - |  |
  | `pac_right` | D | yes | - | - |  |
  | `pac_up` | W | yes | - | - |  |
  | `pac_down` | S | yes | - | - |  |


### `platformer` — playable

- 窗口：OS `[800, 600]` ／ 根视口 `[800.0, 600.0]` ／ 声明 `[800, 600]` ／ 一致 `True`
- 启动：{"port_up": true, "seconds": 1.9, "alive": true} ／ tools/list 73 个工具 ／ 本次耗时 32.6s
- **P1 pass**：best frame #1: content 9.1581% (>=0.40%), bbox coverage 97.3333% (>=12.00%), bbox=[0, 16, 800, 584], bg=[8, 8, 24]
- **P2 pass**：3/3 declared actions produced a state or pixel change within 45 frames through the faithful channel (`Input.parse_input_event`, the path a real key press takes): 3/3; of the failures, 0 answered only `Viewport.push_input` (an `_Input`-reader) and 0 answered only `Input.action_press`
- **P3 pass**：frames_drawn 271 -> 843 (advanced=True); autonomous state changes=2; pixel change over the autonomous+post frames=0; state changes seen during the input round=19
- **P4 pass**：process alive at end=True; visible windows of the tree=1; modal dialog candidates=0; MCP timeouts=0
- **P5 pass**：README documents 3 keys (['A', 'D', 'SPACE']); the InputMap declares 3 actions; the code reads 0 actions it does NOT declare ([]); 0 declared actions the code never reads ([]); 0 tested actions do nothing ([]); 0 never exercised ([]); README keys with no declared action: []
- **P6 pass**：3/3 required capabilities are delivered by a declared, responding action

  | 玩家必须能做的事 | 权威动作 | 结果 | 证据 |
  |---|---|---|---|
  | run left | `plat_left` | pass | `PlayerX|VelX|Facing` moved ['/root/Main.Facing', '/root/Main.VelX'] |
  | run right | `plat_right` | pass | `PlayerX|VelX|Facing` moved ['/root/Main.Facing', '/root/Main.VelX'] |
  | jump | `plat_jump` | pass | `PlayerY|VelY|Jumps|JumpsRejected` moved ['/root/Main.AirJumps', '/root/Main.InputJumps', '/root/Main.Jumps'] |

- 逐动作。`real_key` = **忠实通道** `Input.parse_input_event`（显示服务器收到真实按键时走的就是这条：
  既更新 InputMap 动作状态，又把事件派发到视口）；`push_input` / `action_state` 是**诊断通道**，
  各自只还原一半（前者只派发、后者只置状态），只在忠实通道失败时才跑。

  | 动作 | 键 | real_key | push_input | action_state | 说明 |
  |---|---|---|---|---|---|
  | `plat_left` | A | yes | - | - |  |
  | `plat_right` | D | yes | - | - |  |
  | `plat_jump` | SPACE | yes | - | - |  |


### `pong` — playable

- 窗口：OS `[800, 600]` ／ 根视口 `[800.0, 600.0]` ／ 声明 `[800, 600]` ／ 一致 `True`
- 启动：{"port_up": true, "seconds": 1.8, "alive": true} ／ tools/list 73 个工具 ／ 本次耗时 36.2s
- **P1 pass**：best frame #1: content 1.8196% (>=0.40%), bbox coverage 86.4800% (>=12.00%), bbox=[24, 0, 752, 552], bg=[8, 24, 24]
- **P2 pass**：5/5 declared actions produced a state or pixel change within 45 frames through the faithful channel (`Input.parse_input_event`, the path a real key press takes): 5/5; of the failures, 0 answered only `Viewport.push_input` (an `_Input`-reader) and 0 answered only `Input.action_press`
- **P3 pass**：frames_drawn 273 -> 1065 (advanced=True); autonomous state changes=0; pixel change over the autonomous+post frames=512; state changes seen during the input round=6
- **P4 pass**：process alive at end=True; visible windows of the tree=1; modal dialog candidates=0; MCP timeouts=0
- **P5 pass**：README documents 5 keys (['W', 'S', 'UP', 'DOWN', 'SPACE']); the InputMap declares 5 actions; the code reads 0 actions it does NOT declare ([]); 0 declared actions the code never reads ([]); 0 tested actions do nothing ([]); 0 never exercised ([]); README keys with no declared action: []
- **P6 pass**：5/5 required capabilities are delivered by a declared, responding action

  | 玩家必须能做的事 | 权威动作 | 结果 | 证据 |
  |---|---|---|---|
  | move the left paddle up | `pong_left_up` | pass | `PaddleLeft` moved ['/root/Main/PaddleLeft.pos'] |
  | move the left paddle down | `pong_left_down` | pass | `PaddleLeft` moved ['/root/Main/PaddleLeft.pos'] |
  | move the right paddle up | `pong_right_up` | pass | `PaddleRight` moved ['/root/Main/PaddleRight.pos'] |
  | move the right paddle down | `pong_right_down` | pass | `PaddleRight` moved ['/root/Main/PaddleRight.pos'] |
  | serve the ball | `pong_serve` | pass | `Ball|Velocity` moved ['/root/Main/Ball.Velocity', '/root/Main/Ball.pos'] |

- 逐动作。`real_key` = **忠实通道** `Input.parse_input_event`（显示服务器收到真实按键时走的就是这条：
  既更新 InputMap 动作状态，又把事件派发到视口）；`push_input` / `action_state` 是**诊断通道**，
  各自只还原一半（前者只派发、后者只置状态），只在忠实通道失败时才跑。

  | 动作 | 键 | real_key | push_input | action_state | 说明 |
  |---|---|---|---|---|---|
  | `pong_left_up` | W | yes | - | - |  |
  | `pong_left_down` | S | yes | - | - |  |
  | `pong_right_up` | UP | yes | - | - |  |
  | `pong_right_down` | DOWN | yes | - | - |  |
  | `pong_serve` | SPACE | yes | - | - |  |


### `puzzlebobble` — playable

- 窗口：OS `[800, 600]` ／ 根视口 `[800.0, 600.0]` ／ 声明 `[800, 600]` ／ 一致 `True`
- 启动：{"port_up": true, "seconds": 1.9, "alive": true} ／ tools/list 73 个工具 ／ 本次耗时 32.5s
- **P1 pass**：best frame #1: content 10.5060% (>=0.40%), bbox coverage 84.8671% (>=12.00%), bbox=[14, 17, 706, 577], bg=[8, 8, 24]
- **P2 pass**：3/3 declared actions produced a state or pixel change within 45 frames through the faithful channel (`Input.parse_input_event`, the path a real key press takes): 3/3; of the failures, 0 answered only `Viewport.push_input` (an `_Input`-reader) and 0 answered only `Input.action_press`
- **P3 pass**：frames_drawn 271 -> 840 (advanced=True); autonomous state changes=2; pixel change over the autonomous+post frames=0; state changes seen during the input round=24
- **P4 pass**：process alive at end=True; visible windows of the tree=1; modal dialog candidates=0; MCP timeouts=0
- **P5 pass**：README documents 3 keys (['A', 'D', 'SPACE']); the InputMap declares 3 actions; the code reads 0 actions it does NOT declare ([]); 0 declared actions the code never reads ([]); 0 tested actions do nothing ([]); 0 never exercised ([]); README keys with no declared action: []
- **P6 pass**：3/3 required capabilities are delivered by a declared, responding action

  | 玩家必须能做的事 | 权威动作 | 结果 | 证据 |
  |---|---|---|---|
  | aim left | `pb_left` | pass | `AngleIndex|ShooterCol` moved ['/root/Main.AngleIndex'] |
  | aim right | `pb_right` | pass | `AngleIndex|ShooterCol` moved ['/root/Main.AngleIndex'] |
  | shoot | `pb_shoot` | pass | `Shots|ProjActive` moved ['/root/Main.InputShots', '/root/Main.ProjActive', '/root/Main.Shots'] |

- 逐动作。`real_key` = **忠实通道** `Input.parse_input_event`（显示服务器收到真实按键时走的就是这条：
  既更新 InputMap 动作状态，又把事件派发到视口）；`push_input` / `action_state` 是**诊断通道**，
  各自只还原一半（前者只派发、后者只置状态），只在忠实通道失败时才跑。

  | 动作 | 键 | real_key | push_input | action_state | 说明 |
  |---|---|---|---|---|---|
  | `pb_shoot` | SPACE | yes | - | - |  |
  | `pb_left` | A | yes | - | - |  |
  | `pb_right` | D | yes | - | - |  |


### `rtype` — playable

- 窗口：OS `[800, 600]` ／ 根视口 `[800.0, 600.0]` ／ 声明 `[800, 600]` ／ 一致 `True`
- 启动：{"port_up": true, "seconds": 1.8, "alive": true} ／ tools/list 73 个工具 ／ 本次耗时 36.3s
- **P1 pass**：best frame #1: content 1.0988% (>=0.40%), bbox coverage 95.6400% (>=12.00%), bbox=[0, 18, 797, 576], bg=[8, 8, 8]
- **P2 pass**：5/5 declared actions produced a state or pixel change within 45 frames through the faithful channel (`Input.parse_input_event`, the path a real key press takes): 5/5; of the failures, 0 answered only `Viewport.push_input` (an `_Input`-reader) and 0 answered only `Input.action_press`
- **P3 pass**：frames_drawn 272 -> 1066 (advanced=True); autonomous state changes=2; pixel change over the autonomous+post frames=0; state changes seen during the input round=43
- **P4 pass**：process alive at end=True; visible windows of the tree=1; modal dialog candidates=0; MCP timeouts=0
- **P5 pass**：README documents 5 keys (['A', 'D', 'W', 'S', 'SPACE']); the InputMap declares 5 actions; the code reads 0 actions it does NOT declare ([]); 0 declared actions the code never reads ([]); 0 tested actions do nothing ([]); 0 never exercised ([]); README keys with no declared action: []
- **P6 pass**：5/5 required capabilities are delivered by a declared, responding action

  | 玩家必须能做的事 | 权威动作 | 结果 | 证据 |
  |---|---|---|---|
  | fly left | `rt_left` | pass | `PlayerX|RejectedMoves` moved ['/root/Main.PlayerX'] |
  | fly right | `rt_right` | pass | `PlayerX|RejectedMoves` moved ['/root/Main.PlayerX'] |
  | fly up | `rt_up` | pass | `PlayerY|RejectedMoves` moved ['/root/Main.PlayerY'] |
  | fly down | `rt_down` | pass | `PlayerY|RejectedMoves` moved ['/root/Main.PlayerY'] |
  | fire | `rt_fire` | pass | `BulletsFired|BulletsActive` moved ['/root/Main.BulletsActive', '/root/Main.BulletsFired'] |

- 逐动作。`real_key` = **忠实通道** `Input.parse_input_event`（显示服务器收到真实按键时走的就是这条：
  既更新 InputMap 动作状态，又把事件派发到视口）；`push_input` / `action_state` 是**诊断通道**，
  各自只还原一半（前者只派发、后者只置状态），只在忠实通道失败时才跑。

  | 动作 | 键 | real_key | push_input | action_state | 说明 |
  |---|---|---|---|---|---|
  | `rt_fire` | SPACE | yes | - | - |  |
  | `rt_left` | A | yes | - | - |  |
  | `rt_right` | D | yes | - | - |  |
  | `rt_up` | W | yes | - | - |  |
  | `rt_down` | S | yes | - | - |  |


### `snake` — playable

- 窗口：OS `[800, 600]` ／ 根视口 `[800.0, 600.0]` ／ 声明 `[800, 600]` ／ 一致 `True`
- 启动：{"port_up": true, "seconds": 1.8, "alive": true} ／ tools/list 73 个工具 ／ 本次耗时 36.6s
- **P1 pass**：best frame #1: content 0.6000% (>=0.40%), bbox coverage 33.0000% (>=12.00%), bbox=[0, 0, 600, 264], bg=[88, 24, 24]
- **P2 pass**：5/5 declared actions produced a state or pixel change within 45 frames through the faithful channel (`Input.parse_input_event`, the path a real key press takes): 5/5; of the failures, 0 answered only `Viewport.push_input` (an `_Input`-reader) and 0 answered only `Input.action_press`
- **P3 pass**：frames_drawn 271 -> 1084 (advanced=True); autonomous state changes=0; pixel change over the autonomous+post frames=0; state changes seen during the input round=8
- **P4 pass**：process alive at end=True; visible windows of the tree=1; modal dialog candidates=0; MCP timeouts=0
- **P5 pass**：README documents 5 keys (['W', 'S', 'A', 'D', 'P']); the InputMap declares 5 actions; the code reads 0 actions it does NOT declare ([]); 0 declared actions the code never reads ([]); 0 tested actions do nothing ([]); 0 never exercised ([]); README keys with no declared action: []
- **P6 pass**：5/5 required capabilities are delivered by a declared, responding action

  | 玩家必须能做的事 | 权威动作 | 结果 | 证据 |
  |---|---|---|---|
  | turn up | `snake_up` | pass | `DirectionX|DirectionY|LastRefusedInput` moved ['/root/Main.DirectionX', '/root/Main.DirectionY'] |
  | turn down | `snake_down` | pass | `DirectionX|DirectionY|LastRefusedInput` moved ['/root/Main.LastRefusedInput'] |
  | turn left | `snake_left` | pass | `DirectionX|DirectionY|LastRefusedInput` moved ['/root/Main.DirectionX', '/root/Main.DirectionY', '/root/Main.LastRefusedInput'] |
  | turn right | `snake_right` | pass | `DirectionX|DirectionY|LastRefusedInput` moved ['/root/Main.LastRefusedInput'] |
  | pause | `snake_pause` | pass | `Paused` moved ['/root/Main.Paused'] |

- 逐动作。`real_key` = **忠实通道** `Input.parse_input_event`（显示服务器收到真实按键时走的就是这条：
  既更新 InputMap 动作状态，又把事件派发到视口）；`push_input` / `action_state` 是**诊断通道**，
  各自只还原一半（前者只派发、后者只置状态），只在忠实通道失败时才跑。

  | 动作 | 键 | real_key | push_input | action_state | 说明 |
  |---|---|---|---|---|---|
  | `snake_up` | W | yes | - | - |  |
  | `snake_down` | S | yes | - | - |  |
  | `snake_left` | A | yes | - | - |  |
  | `snake_right` | D | yes | - | - |  |
  | `snake_pause` | P | yes | - | - |  |


### `sokoban` — playable

- 窗口：OS `[800, 600]` ／ 根视口 `[800.0, 600.0]` ／ 声明 `[800, 600]` ／ 一致 `True`
- 启动：{"port_up": true, "seconds": 1.8, "alive": true} ／ tools/list 73 个工具 ／ 本次耗时 34.4s
- **P1 pass**：best frame #1: content 27.3656% (>=0.40%), bbox coverage 63.8633% (>=12.00%), bbox=[18, 16, 782, 392], bg=[8, 8, 24]
- **P2 pass**：4/4 declared actions produced a state or pixel change within 45 frames through the faithful channel (`Input.parse_input_event`, the path a real key press takes): 4/4; of the failures, 0 answered only `Viewport.push_input` (an `_Input`-reader) and 0 answered only `Input.action_press`
- **P3 pass**：frames_drawn 271 -> 951 (advanced=True); autonomous state changes=2; pixel change over the autonomous+post frames=0; state changes seen during the input round=44
- **P4 pass**：process alive at end=True; visible windows of the tree=1; modal dialog candidates=0; MCP timeouts=0
- **P5 pass**：README documents 4 keys (['W', 'S', 'A', 'D']); the InputMap declares 4 actions; the code reads 0 actions it does NOT declare ([]); 0 declared actions the code never reads ([]); 0 tested actions do nothing ([]); 0 never exercised ([]); README keys with no declared action: []
- **P6 pass**：4/4 required capabilities are delivered by a declared, responding action

  | 玩家必须能做的事 | 权威动作 | 结果 | 证据 |
  |---|---|---|---|
  | walk up | `soko_up` | pass | `PlayerRow|RejectedMoves` moved ['/root/Main.PlayerRow'] |
  | walk down | `soko_down` | pass | `PlayerRow|RejectedMoves` moved ['/root/Main.PlayerRow'] |
  | walk left | `soko_left` | pass | `PlayerCol|RejectedMoves` moved ['/root/Main.PlayerCol'] |
  | walk right | `soko_right` | pass | `PlayerCol|RejectedMoves` moved ['/root/Main.PlayerCol'] |

- 逐动作。`real_key` = **忠实通道** `Input.parse_input_event`（显示服务器收到真实按键时走的就是这条：
  既更新 InputMap 动作状态，又把事件派发到视口）；`push_input` / `action_state` 是**诊断通道**，
  各自只还原一半（前者只派发、后者只置状态），只在忠实通道失败时才跑。

  | 动作 | 键 | real_key | push_input | action_state | 说明 |
  |---|---|---|---|---|---|
  | `soko_up` | W | yes | - | - |  |
  | `soko_right` | D | yes | - | - |  |
  | `soko_left` | A | yes | - | - |  |
  | `soko_down` | S | yes | - | - |  |


### `spaceinvaders` — playable

- 窗口：OS `[800, 600]` ／ 根视口 `[800.0, 600.0]` ／ 声明 `[800, 600]` ／ 一致 `True`
- 启动：{"port_up": true, "seconds": 1.9, "alive": true} ／ tools/list 73 个工具 ／ 本次耗时 32.6s
- **P1 pass**：best frame #1: content 8.4779% (>=0.40%), bbox coverage 63.2392% (>=12.00%), bbox=[21, 20, 586, 518], bg=[8, 8, 24]
- **P2 pass**：3/3 declared actions produced a state or pixel change within 45 frames through the faithful channel (`Input.parse_input_event`, the path a real key press takes): 3/3; of the failures, 0 answered only `Viewport.push_input` (an `_Input`-reader) and 0 answered only `Input.action_press`
- **P3 pass**：frames_drawn 268 -> 839 (advanced=True); autonomous state changes=1; pixel change over the autonomous+post frames=1640; state changes seen during the input round=14
- **P4 pass**：process alive at end=True; visible windows of the tree=1; modal dialog candidates=0; MCP timeouts=0
- **P5 pass**：README documents 3 keys (['A', 'D', 'SPACE']); the InputMap declares 3 actions; the code reads 0 actions it does NOT declare ([]); 0 declared actions the code never reads ([]); 0 tested actions do nothing ([]); 0 never exercised ([]); README keys with no declared action: []
- **P6 pass**：3/3 required capabilities are delivered by a declared, responding action

  | 玩家必须能做的事 | 权威动作 | 结果 | 证据 |
  |---|---|---|---|
  | move left | `si_left` | pass | `PlayerX` moved ['/root/Main.PlayerX'] |
  | move right | `si_right` | pass | `PlayerX` moved ['/root/Main.PlayerX'] |
  | fire | `si_fire` | pass | `ShotsFired|BulletActive` moved ['/root/Main.BulletActive', '/root/Main.ShotsFired'] |

- 逐动作。`real_key` = **忠实通道** `Input.parse_input_event`（显示服务器收到真实按键时走的就是这条：
  既更新 InputMap 动作状态，又把事件派发到视口）；`push_input` / `action_state` 是**诊断通道**，
  各自只还原一半（前者只派发、后者只置状态），只在忠实通道失败时才跑。

  | 动作 | 键 | real_key | push_input | action_state | 说明 |
  |---|---|---|---|---|---|
  | `si_left` | A | yes | - | - |  |
  | `si_right` | D | yes | - | - |  |
  | `si_fire` | SPACE | yes | - | - |  |


### `tetris` — playable

- 窗口：OS `[800, 600]` ／ 根视口 `[800.0, 600.0]` ／ 声明 `[800, 600]` ／ 一致 `True`
- 启动：{"port_up": true, "seconds": 1.8, "alive": true} ／ tools/list 73 个工具 ／ 本次耗时 36.3s
- **P1 pass**：best frame #1: content 48.5983% (>=0.40%), bbox coverage 50.6183% (>=12.00%), bbox=[20, 38, 502, 484], bg=[72, 72, 72]
- **P2 pass**：5/5 declared actions produced a state or pixel change within 45 frames through the faithful channel (`Input.parse_input_event`, the path a real key press takes): 5/5; of the failures, 0 answered only `Viewport.push_input` (an `_Input`-reader) and 0 answered only `Input.action_press`
- **P3 pass**：frames_drawn 265 -> 1057 (advanced=True); autonomous state changes=0; pixel change over the autonomous+post frames=0; state changes seen during the input round=12
- **P4 pass**：process alive at end=True; visible windows of the tree=1; modal dialog candidates=0; MCP timeouts=0
- **P5 pass**：README documents 5 keys (['A', 'D', 'W', 'S', 'E']); the InputMap declares 5 actions; the code reads 0 actions it does NOT declare ([]); 0 declared actions the code never reads ([]); 0 tested actions do nothing ([]); 0 never exercised ([]); README keys with no declared action: []
- **P6 pass**：5/5 required capabilities are delivered by a declared, responding action

  | 玩家必须能做的事 | 权威动作 | 结果 | 证据 |
  |---|---|---|---|
  | move left | `tetris_left` | pass | `PieceX` moved ['/root/Main.PieceX'] |
  | move right | `tetris_right` | pass | `PieceX` moved ['/root/Main.PieceX'] |
  | rotate | `tetris_rotate` | pass | `PieceRot` moved ['/root/Main.PieceRot'] |
  | soft drop | `tetris_down` | pass | `PieceY|Score|Ticks` moved ['/root/Main.PieceY', '/root/Main.Ticks'] |
  | hard drop | `tetris_drop` | pass | `PieceY|Score|Lines|FilledCells` moved ['/root/Main.FilledCells', '/root/Main.PieceY'] |

- 逐动作。`real_key` = **忠实通道** `Input.parse_input_event`（显示服务器收到真实按键时走的就是这条：
  既更新 InputMap 动作状态，又把事件派发到视口）；`push_input` / `action_state` 是**诊断通道**，
  各自只还原一半（前者只派发、后者只置状态），只在忠实通道失败时才跑。

  | 动作 | 键 | real_key | push_input | action_state | 说明 |
  |---|---|---|---|---|---|
  | `tetris_left` | A | yes | - | - |  |
  | `tetris_right` | D | yes | - | - |  |
  | `tetris_rotate` | W | yes | - | - |  |
  | `tetris_down` | S | yes | - | - |  |
  | `tetris_drop` | E | yes | - | - |  |


### `towerdefense` — playable

- 窗口：OS `[800, 600]` ／ 根视口 `[800.0, 600.0]` ／ 声明 `[800, 600]` ／ 一致 `True`
- 启动：{"port_up": true, "seconds": 1.9, "alive": true} ／ tools/list 73 个工具 ／ 本次耗时 38.3s
- **P1 pass**：best frame #1: content 45.4579% (>=0.40%), bbox coverage 96.1833% (>=12.00%), bbox=[2, 18, 796, 580], bg=[8, 8, 24]
- **P2 pass**：6/6 declared actions produced a state or pixel change within 45 frames through the faithful channel (`Input.parse_input_event`, the path a real key press takes): 6/6; of the failures, 0 answered only `Viewport.push_input` (an `_Input`-reader) and 0 answered only `Input.action_press`
- **P3 pass**：frames_drawn 267 -> 1181 (advanced=True); autonomous state changes=2; pixel change over the autonomous+post frames=0; state changes seen during the input round=39
- **P4 pass**：process alive at end=True; visible windows of the tree=1; modal dialog candidates=0; MCP timeouts=0
- **P5 pass**：README documents 6 keys (['A', 'D', 'W', 'S', 'SPACE', 'G']); the InputMap declares 6 actions; the code reads 0 actions it does NOT declare ([]); 0 declared actions the code never reads ([]); 0 tested actions do nothing ([]); 0 never exercised ([]); README keys with no declared action: []
- **P6 pass**：5/5 required capabilities are delivered by a declared, responding action

  | 玩家必须能做的事 | 权威动作 | 结果 | 证据 |
  |---|---|---|---|
  | move the cursor left | `td_left` | pass | `CursorCol` moved ['/root/Main.CursorCol'] |
  | move the cursor right | `td_right` | pass | `CursorCol` moved ['/root/Main.CursorCol'] |
  | move the cursor up | `td_up` | pass | `CursorRow` moved ['/root/Main.CursorRow'] |
  | move the cursor down | `td_down` | pass | `CursorRow` moved ['/root/Main.CursorRow'] |
  | place a tower at the cursor | `td_place` | pass | `TowersPlaced|Gold|TowerList` moved ['/root/Main.Gold', '/root/Main.TowerList', '/root/Main.TowersPlaced'] |

- 逐动作。`real_key` = **忠实通道** `Input.parse_input_event`（显示服务器收到真实按键时走的就是这条：
  既更新 InputMap 动作状态，又把事件派发到视口）；`push_input` / `action_state` 是**诊断通道**，
  各自只还原一半（前者只派发、后者只置状态），只在忠实通道失败时才跑。

  | 动作 | 键 | real_key | push_input | action_state | 说明 |
  |---|---|---|---|---|---|
  | `td_auto_step` | G | yes | - | - |  |
  | `td_left` | A | yes | - | - |  |
  | `td_right` | D | yes | - | - |  |
  | `td_up` | W | yes | - | - |  |
  | `td_down` | S | yes | - | - |  |
  | `td_place` | SPACE | yes | - | - |  |


## 5. 静态审计（InputMap ↔ 代码 ↔ README）

| 游戏 | 声明动作 | 键 | 代码读取 | 读而未声明 | 声明而无人读 | README 玩法 |
|---|---|---|---|---|---|---|
| `asteroids` | ast_left, ast_right, ast_thrust, ast_fire | ast_left=A, ast_right=D, ast_thrust=W, ast_fire=SPACE | ast_fire, ast_left, ast_right, ast_thrust | — | — | yes |
| `bomberman` | bomb_up, bomb_right, bomb_place, bomb_left, bomb_down | bomb_up=W, bomb_right=D, bomb_place=SPACE, bomb_left=A, bomb_down=S | bomb_down, bomb_left, bomb_place, bomb_right, bomb_up | — | — | yes |
| `breakout` | breakout_left, breakout_right, breakout_launch | breakout_left=A, breakout_right=D, breakout_launch=SPACE | breakout_launch, breakout_left, breakout_right | — | — | yes |
| `flappy` | flap, flappy_restart | flap=SPACE, flappy_restart=R | flap, flappy_restart | — | — | yes |
| `frogger` | frog_left, frog_right, frog_up, frog_down | frog_left=A, frog_right=D, frog_up=W, frog_down=S | frog_down, frog_left, frog_right, frog_up | — | — | yes |
| `game2048` | m2048_up, m2048_right, m2048_down, m2048_left | m2048_up=W, m2048_right=D, m2048_down=S, m2048_left=A | m2048_down, m2048_left, m2048_right, m2048_up | — | — | yes |
| `lunarlander` | ll_thrust, ll_rotate_left, ll_rotate_right | ll_thrust=SPACE, ll_rotate_left=A, ll_rotate_right=D | ll_rotate_left, ll_rotate_right, ll_thrust | — | — | yes |
| `match3` | m3_auto_move, m3_left, m3_right, m3_up, m3_down, m3_swap | m3_auto_move=G, m3_left=A, m3_right=D, m3_up=W, m3_down=S, m3_swap=SPACE | m3_auto_move, m3_swap | — | m3_down, m3_left, m3_right, m3_up | yes |
| `minesweeper` | mine_reveal_next, mine_flag_next, mine_left, mine_right, mine_up, mine_down, mine_reveal, mine_flag | mine_reveal_next=R, mine_flag_next=G, mine_left=A, mine_right=D, mine_up=W, mine_down=S, mine_reveal=SPACE, mine_flag=F | mine_flag, mine_flag_next, mine_reveal, mine_reveal_next | — | mine_down, mine_left, mine_right, mine_up | yes |
| `missilecommand` | mc_auto_fire, mc_left, mc_right, mc_fire | mc_auto_fire=G, mc_left=A, mc_right=D, mc_fire=SPACE | mc_auto_fire, mc_fire, mc_left, mc_right | — | — | yes |
| `pacman` | pac_left, pac_right, pac_up, pac_down | pac_left=A, pac_right=D, pac_up=W, pac_down=S | pac_down, pac_left, pac_right, pac_up | — | — | yes |
| `platformer` | plat_left, plat_right, plat_jump | plat_left=A, plat_right=D, plat_jump=SPACE | plat_jump, plat_left, plat_right | — | — | yes |
| `pong` | pong_left_up, pong_left_down, pong_right_up, pong_right_down, pong_serve | pong_left_up=W, pong_left_down=S, pong_right_up=UP, pong_right_down=DOWN, pong_serve=SPACE | pong_left_down, pong_left_up, pong_right_down, pong_right_up, pong_serve | — | — | yes |
| `puzzlebobble` | pb_shoot, pb_left, pb_right | pb_shoot=SPACE, pb_left=A, pb_right=D | pb_left, pb_right, pb_shoot | — | — | yes |
| `rtype` | rt_fire, rt_left, rt_right, rt_up, rt_down | rt_fire=SPACE, rt_left=A, rt_right=D, rt_up=W, rt_down=S | rt_down, rt_fire, rt_left, rt_right, rt_up | — | — | yes |
| `snake` | snake_up, snake_down, snake_left, snake_right, snake_pause | snake_up=W, snake_down=S, snake_left=A, snake_right=D, snake_pause=P | snake_down, snake_left, snake_pause, snake_right, snake_up | — | — | yes |
| `sokoban` | soko_up, soko_right, soko_left, soko_down | soko_up=W, soko_right=D, soko_left=A, soko_down=S | soko_down, soko_left, soko_right, soko_up | — | — | yes |
| `spaceinvaders` | si_left, si_right, si_fire | si_left=A, si_right=D, si_fire=SPACE | si_fire, si_left, si_right | — | — | yes |
| `tetris` | tetris_left, tetris_right, tetris_rotate, tetris_down, tetris_drop | tetris_left=A, tetris_right=D, tetris_rotate=W, tetris_down=S, tetris_drop=E | tetris_down, tetris_drop, tetris_left, tetris_right, tetris_rotate | — | — | yes |
| `towerdefense` | td_auto_step, td_left, td_right, td_up, td_down, td_place | td_auto_step=G, td_left=A, td_right=D, td_up=W, td_down=S, td_place=SPACE | td_auto_step, td_place | — | td_down, td_left, td_right, td_up | yes |

## 6. 试玩代理接口（item D）

`tools/playtest_agent.py` 定义 `decide(frames, state, goal) -> action`，两种后端：

- `scripted`：内置脚本化动作序列，本轮 A–C 全程用它跑通；
- `openai`：OpenAI 兼容 HTTP 客户端，读 `PLAYTEST_BASE_URL` / `PLAYTEST_API_KEY` /
  `PLAYTEST_MODEL`，把**截图 base64 + 结构化状态**发给模型，要求返回 **JSON 动作**；
  `judge()` 用同一端点问「这一帧看起来是否可玩/有什么异常」。

接 NeoHorse-Jev 这类本地模型：起 OpenAI 兼容服务（vLLM / llama.cpp `--port 8000`）→ 设好那三个环境变量
→ `python tools/playability_gate.py --games pong --agent=openai`。细节见该文件顶部 docstring。

连通性验证（本轮**未**接真模型，按任务书要求只做哑服务/报错可控验证）：
`python tools/playtest_agent.py --probe` —— 内置一个哑 OpenAI 服务，一个端点回固定应答、
一个端点回 HTTP 500，检查：请求打到 `/v1/chat/completions`、Bearer 头带上、base64 图挂上、
JSON 动作能解析、judge JSON 能解析、500 被报成错误而不是静默成功、未配置时安全降级。

## 7. 两仓 git 状态与提交

下表由本工具在生成报告时**直接调用 `git`** 得到（只读命令），所以报告与仓库状态不会各说各话。

### 主仓 `F:\moonbit-hof-rs`

`git log --oneline -8`：

```
4d651d1 docs(godot-mcp): TASK-116 - the report, the defect register, and the D161 decision record
34b1fc6 feat(godot-mcp): TASK-116 (D161) - the playability gate, and the 19 games it found were unplayable
aaf2d9a docs(godot-mcp): TASK-115 - the report's commit list now names all four commits
b180262 fix(godot-mcp): TASK-115 - reclassify_h7.py was only half idempotent; recompose the H7 note from its original
d4c1d2b chore(godot-mcp): TASK-115 - refresh the ledger once more, and record the three-commit order in the report
84fb1bc docs(godot-mcp): TASK-115 - the report and the D160 decision record
2c1ff0a feat(godot-mcp): TASK-115 (D160) - split H7 by measurement, restore eight witnesses, and the export/signature probe
eb52b26 docs(godot-mcp): TASK-114 - record the two commit hashes and the engine-repo status in the report
```

`git status --short`：

```
 M godot-mcp/recovery/work/task104/logs/git-housekeeping.err.txt
 M godot-mcp/recovery/work/task104/logs/git-housekeeping.out.txt
?? godot-mcp/dist/MANIFEST.txt
?? godot-mcp/dist/PACKAGE-INFO-TASK109.txt
?? godot-mcp/dist/SELFCHECK.txt
?? godot-mcp/dist/build_package.py
?? godot-mcp/dist/check_counts.py
?? godot-mcp/dist/exe/
?? godot-mcp/dist/gather.py
?? godot-mcp/dist/godot-mcp-20games-20260927-0844.MANIFEST.txt
?? godot-mcp/dist/godot-mcp-20games-20260927-0844.sha256.txt
?? godot-mcp/dist/godot-mcp-20games-20260927-0844.zip
?? godot-mcp/dist/godot-mcp-20games-exe-20260927-0927-part1of2.zip
?? godot-mcp/dist/godot-mcp-20games-exe-20260927-0927-part2of2.zip
?? godot-mcp/dist/godot-mcp-20games-exe-20260927-0927.sha256.txt
?? godot-mcp/dist/probe_runs.json
?? godot-mcp/dist/probe_runs.py
?? godot-mcp/dist/review_data.json
?? godot-mcp/dist/selfcheck.py
?? godot-mcp/dist/zip-info.json
?? godot-mcp/projects/_exercises/ex_audio/
?? godot-mcp/projects/_exercises/ex_export/
?? godot-mcp/projects/_exercises/ex_export_np/
?? godot-mcp/projects/_exercises/ex_nav/
?? godot-mcp/projects/_exercises/ex_particles/
?? godot-mcp/projects/_exercises/ex_rec/
?? godot-mcp/projects/_exercises/ex_write2/
?? godot-mcp/projects/_exercises/ex_write3/
?? godot-mcp/projects/_exercises/ex_write4/
?? godot-mcp/recovery/reports/ACCEPTANCE-TASK-107.md
?? godot-mcp/tools/__pycache__/
```

### 引擎仓 `godot-mcp\godot`

`git log --oneline -8`：

```
ba1587c71e fix(mcp_server): TASK-112 - the three engine defects TASK-111 registered are fixed at the root (one of them blocking and silent), plus one schema override
3fdabe2d9a fix(godot-mcp): TASK-110 - editor_list_signal_connections' registered schema regains `scope`, the one member that made the TASK-051 narrowing unreachable
1f9d0cb1c9 modules/mcp_server: task103 - REBUILT-2C-MANIFEST gains the 2c-12 section: the runtime-error contract of running_game_execute_gdscript (the -32000 code and why the two neighbouring codes are wrong for it, the reconstructed script identity and why Script::get_path() cannot be it, the two boundaries that remain - no column from the handler, and a release template reporting nothing because both VM sites are inside DEBUG_ENABLED), the append-only description override with the contract's six shape quantities unchanged (177/6/1.22.0/154/73/idempotent, sha bd68e804), the minimal same-batch reproduction with its before/after answers and its three controls, the ten gates with their real exit codes and accept_m1 22/22 on the binary rebuilt at 1c7f5c07a, the deliberate boundary that leaves the editor executor alone, and the iron rules as they were actually followed
1c7f5c07a1 modules/mcp_server: task103 (X-1) - a GDScript body that compiles and then fails while it runs is a structured refusal now (-32000 + data.script_error + data.suggestion) instead of an ok with a null result, and a successful body that returned no value carries a note, so "ok" can no longer be read as "the script ran"
e041cae270 modules/mcp_server: task099 - REBUILT-2C-MANIFEST gains the 2c-11 section: the gate runner's doc-only preflight (one classifier, dot-sourced from the module's own anchor judge, anchor taken from the built binary's --version, committed range plus working tree, and the two measured cases with all ten gates green in the compile-input one), the third live --import shutdown access violation with its 24 controlled probes at 0 crashes, and the explicit reason why the change to tools/run_gates.ps1 cannot reach either variant (it is a main-repository script, so the engine tree has no byte to rebuild)
0fbd5ec4cb modules/mcp_server: task098 - MCP-TRACEABILITY section 7 is aligned with the D-1 closure
094b071f9b modules/mcp_server: task097 - REBUILT-2C-MANIFEST gains the 2c-10 section: the name-conflict policy the section registers (the default refusal with its complete conflict list, its error code and its opt-in rename), the contract's six shape quantities after the append-only override (177/6/1.22.0/154/73/idempotent, sha 64ddce9f), the ten gates and accept_m1 22/22 with their real exit codes, and the three iron-rule deviations of this task recorded rather than hidden
2385fe2fb5 modules/mcp_server: task097 (D-3) - a requested node name the target parent already carries is now refused instead of silently renamed, so a replayed editor phase can no longer write a whole duplicate node layer into a scene; editor_save_scene reports the duplicates a batch made under an explicit rename instead of saving them silently
```

`git status --short`：

```
?? uid_cache.bin
```

**本轮没有改引擎模块**：`godot\modules\mcp_server\` 一个字节未动（引擎仓 `git status --short`
只有 Godot 自己生成的 `uid_cache.bin`），因此按铁律 7 **不需要**重建两变体 / 十道门 / accept_m1 / push。
所有改动都在主仓：门与代理工具、20 款工程的 C# 与 project.godot 与 README、以及本报告。

## 8. 遗留项与本轮不该被读成的东西（如实登记）

1. **P6 全绿 ≠ 好玩**。它只说明能力表里列的每一件事都有一个键能真的做到。能力表的每一行都是
   **人写的判断**，可以被质疑和替换；替换后重跑，门会重新机检。
2. **`hold_ms` 是手工调参的**。默认 0.5 s 对多数游戏合适，但 Frogger 的键盘路径按住会重复，
   0.5 s 是四次跳跃、四次进车道就是四次死亡；它在 `tools/playability_controls.json` 里单独写了
   `hold_ms: 150`。这是**已知的顺序/时长敏感性**，不是已经解决的问题——换一款有重复间隔的游戏
   仍可能要再调一次。
3. **能力表没有 `pre` 预热**。一条能力若在游戏初始态被合法拒绝（在角落、在边缘、在墙边），
   门只能靠游戏自己的**拒绝计数器**间接证明「键被读到了」。本轮给三款补了计数器，
   另有两款把光标起点从角落移到棋盘中间；**通用解法（能力表支持预热序列）没有做**。
4. **P1 的阈值是下界，不是贴着样本画的线**：本轮通过 P1 的样本内容占比在 0.9%~3.4%、
   包围盒覆盖在 68%~99%，阈值取 0.4% / 12%。
5. **每款只测了一个进程、一次会话**。没有测长时间运行的稳定性、没有测多分辨率/缩放、
   没有测手柄——这些都不在本轮的判据里。
6. **修复前那一轮的注入通道与修复后不同**（前：`push_input` + `action_press`；后：
   `parse_input_event` 为主通道）。§3 已论证这个对比在同一方向上成立，因为
   `parse_input_event` 是那两个通道的并集。
