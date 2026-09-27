# TEMPLATE — 游戏逻辑反馈机制（game-logic feedback）

> **可复用模板。** 凡是"某个游戏/引擎改动是否让游戏真的能玩、逻辑是否正确"的验收，
> 都按本模板走。它是 TASK-131 的产物：TASK-131 之前，"能跑"被当成了"能玩"——
> `snake` 的 23 帧逐字节相同、`game2048` 的棋盘全空，而门报 P1..P7 全 PASS。
>
> 本模板的每一条都对应一个**被测到过的真实失效**，括号里写出证据落点。
> 模板里没有"模型看起来没问题"这种句子：要么有可复现的证据，要么明确写"证据不足"。

---

## 0. 前置：三态结论（只有这三种，不许写"应该可以"）

| 结论 | 含义 | 必要条件 |
|---|---|---|
| **逻辑正确** | 声明的玩法可观测**确实**被玩家的动作推动 | 双通路之一成立 + 逐帧读图与状态一致 + 无未声明的状态变更 |
| **逻辑错误** | 动作到达了游戏，但世界没有按声明的方式改变 | 焦点与送达成立，注入方式有效，而声明的可观测不变 |
| **证据不足** | 无法把上面两条分开 | 必须列出**缺哪一条证据**，以及它为什么缺（环境限制 / 通道缺失 / 图不可读） |

**不得**把"证据不足"写成"逻辑正确"，也**不得**用"本机环境限制"去解释一个
"焦点与送达都已成立"的失败（TASK-131 §A：本机 `display_active=Enabled`、
`SetForegroundWindow` 可切换前台、`SendInput` 返回 1/1，
证据 `runs/realinput/_env/env.json`）。

---

## 1. 双通路：真实键 + 合成键，两条都要测

### 1.1 真实 OS 键（不可省）
* 工具的权威实现：`tools/real_input_probe.py`（`env` 子命令 = 只读能力探测；
  `run` 子命令 = 实测）。**不要**在别处复制它的 SendInput 结构体——
  x64 下 `sizeof(INPUT) != 40` 会静默地什么都不发（工具里有断言）。
* 必测项（每条留原始读数）：
  1. 会话是否**交互式桌面**（`OpenInputDesktop` + `GetUserObjectInformationW`）；
  2. 显示器数/分辨率（`GetSystemMetrics`、`EnumDisplayMonitors`）；
  3. `GetForegroundWindow` 前后值 + `SetForegroundWindow` 返回值 + `GetLastError`
     ——并且要**换一个窗口**去试（对已经是前台的窗口返回 1 什么也证明不了）；
  4. `SendInput` 的返回计数（`requested=1, returned=1`）与 `GetAsyncKeyState` 的确认；
  5. 游戏窗口的 hwnd / pid / rect（焦点必须落在**游戏进程**的窗口上）。
* 键码来源：游戏 `project.godot` 的 InputMap `keycode`（Godot Key 枚举），
  经 `tools/real_input_probe.py` 的 `GODOT_TO_VK` 反查 Windows VK。
  转换表里没有的键必须**报错拒绝**，不许猜。
* `SendInput` 的按键在下行后必须有**上行**（`KEYEVENTF_KEYUP`），否则游戏会一直
  认为键被按住。

### 1.2 合成键（门的忠实通道）
`Input.parse_input_event(ev)`：它既置 InputMap action 状态又派发事件，
是 **DisplayServer 之内**的忠实通道。它证明不了 OS 事件能不能送到窗口，
所以它只能作为**对照臂**，不能单独作为"真人按键可以"的证据。

### 1.3 顺序陷阱（量到过，必须按此设计）
许多动作在它写的状态上是**幂等**的：连按两次 LEFT，`DirectionX` 第二次不变。
若"真实键臂"之后紧跟"合成键臂"打同一个动作，第二臂会报"没反应"——
那是协议假象，不是通路缺陷（证据：`runs/realinput/snake` 的第一版，见
`runs/realinput/pong-hold0.5-confounded/`）。

**正确协议（本模板采用，`real_input_probe.py run` 已实现）**：对一组**互逆动作对**
`(X, Y)` 按 `REAL X → PARSE Y → PARSE X → REAL Y` 循环，每个臂都从**相反的值**出发，
于是每个臂都有东西可变，且同一个动作在两条通道上各被测一次。
每个循环前跑一个**等长、无输入**的对照窗口；一个臂只有在**赢过自己的对照窗**时才算数。

### 1.4 对照表（报告的固定表格）
| 动作 | 通道 | 焦点 | 键下行/上行返回 | 对照窗状态变更/像素 | 动作后状态变更/像素 | 是否赢过对照 | 逐帧图 |
|---|---|---|---|---|---|---|---|
| ... | OS_SendInput / parse_input_event | hwnd+pid | 1/1 | 0 / 0 | n / m | 是/否 | 见 §3 |

---

## 2. 取证—输入同一实例的核对项（四处对齐，缺一判 FAIL）

一旦发现帧来自编辑器进程 / 内嵌小窗 / 另一个进程，**判 FAIL 并点名**。

| # | 对齐项 | 从哪里取 | 判 FAIL 的样子 |
|---|---|---|---|
| 1 | 游戏进程 pid | `playability_gate.process_tree()`；`real_input_probe` 的 `session.json.identity` | 窗口 pid ∉ 游戏进程树 |
| 2 | MCP 端口 | 启动命令行 `--mcp-port=N`；`session.json.mcp_endpoint` | 端口不是本次唯一的那个；或端点上答复的不是这个 pid |
| 3 | trace 文件名 | `<out>/calls/NNN_<tool>.response.json`（每次调用一个） | 状态/帧读不出来自同一次调用序列 |
| 4 | 引擎版本串 | `godot\bin\...console.exe --version` | 版本与 `session.json.engine_version_string` 不一致 |

**加分证据（强烈建议）**：游戏自己的 stdout（`<out>/engine-game.stdout.txt`）。
它带时间戳地打印游戏内部事件（`PONG_TICK`、`SNAKE_WALL`、`SNAKE_REFUSED`…），
是把"我注入的那一下"与"游戏真的收到了"对上的最硬的一条。

**逐步对应表（报告必含）**：
步骤号 → 注入的调用（`seq`、工具名、参数）→ 同一时刻的状态快照（字段值 + sha256）
→ 该次采集的帧（帧 id、文件、sha256、与前一帧的像素差）→ 时间戳（`ts_ms`/`frame_count`）。
`tools/real_input_probe.py run` 直接产出这张表：`runs/realinput/<game>/steps.json`。

**视口与分辨率也要声明**：整窗？游戏视口？裁剪？分辨率是否等于工程声明值
（`gate.json -> window_conformance`）。TASK-117 的 exe 扫描与工程扫描要分别写清。

---

## 3. 逐帧读图（硬判据，不许用数字冒充看图）

1. 对**每一帧**与 filmstrip，用 `read_image` **实际查看**。
   最低标准：整张 filmstrip 逐格看（它含全部帧），并对每个**注入前后的关键帧**
   看全尺寸原图。报告里要写明"哪张图在什么分辨率下被看过"。
2. 逐帧写下来：**看到了什么**（画面内容、HUD 数值、玩家物体位置）、
   **与上一帧相比变了什么**、**这个变化与该次操作是否相符**。
3. 报告必须含**逐帧描述表**：
   | 帧 id | 文件 | 我看到了什么 | 与上一帧的变化 | 是否与操作相符 | 结论 |
4. **图不可读 / 无 `read_image` 能力时必须显式声明**"未能读图"并说明原因，
   **不得**用像素差、sha256、bbox 等数字充当"看图结论"。

**为什么这条是硬判据**：TASK-131 用 `read_image` 看到 snake 的每一格都是
"35% 透明度的红色结束遮罩 + 一条 96×24 的暗绿色蛇身 + 左上角一颗 24×24 的红食物"，
才判定它"只有一个绿色方块"是**渲染的是结束画面**，而不是渲染缺陷或相机错误。

---

## 4. 状态判据要问对问题（"有变化" ≠ "玩起来了"）

* **元状态不算数**：时钟（`Ticks`/`Elapsed`/`frames_drawn`）、输入计数（`Input*`）、
  拒绝日志（`LastRefusedInput`/`Rejected*`）、意图索引（`DirectionX/Y`/`Facing`/
  `AngleIndex`）、摘要（`*Hash`）、UI 文本（`*.text`）、模式标志（`Paused`/`GameOver`）
  ——它们的变化只说明**管道通了**。
* **玩法可观测才算数**：物体的位置/速度、得分、棋盘/关卡推进、被消耗物的计数。
  每个游戏必须在 `tools/playability_controls.json -> games.<game>.gameplay_observables.items`
  里**声明**自己的清单，判据由声明驱动（`playability_gate.is_gameplay_key`）。
* **允许的唯一豁免**：游戏自己记录了**蓄意拒绝**（墙、边界、非法方向）。
  豁免生效还要求**同一局里至少有一个动作真的推动了玩法**——否则
  "全部都拒绝了，因为游戏已经死了"（snake / game2048）仍然判红。
* **先判"开局是不是已经结束"**：在 settle 帧上求值
  `games.<game>.liveness.terminal`（例如 `/root/Main.GameOver == true`）。
  一个在第一帧就已经结束的游戏，其后的静止画面**必然**合法，
  不能用"后来的画面有变化"来证明它可玩（snake：`GameOver=true`、
  `SNAKE_WALL head=25,10 ticks=19`，1.52 秒游戏时间即死亡，且 InputMap 里没有重开键）。
* **动作副作用必须恢复或声明**：动作序列不得把游戏留在"暂停/冻结/停止"态之后
  继续采集后置帧。要么按 `games.<game>.mode_actions[].restore` **测完恢复**
  （`snake_pause` 再按一次；门会读回 marker 并记录），要么**在每一帧上显式声明**
  当时状态。**每帧都要带 marker**：`Paused`、时钟参数、`Ticks`、`Score`
  （`gate.json -> criteria.P3.marker_timeline`）。
* **阈值要能说出依据**：`P1_MIN_CONTENT_FRACTION` 之类必须给出推导
  （哪几款样本、去掉哪几种伪影、新旧值对比、余量多大），并注明
  "fitted for separation, not calibrated"。
  同时注意**伪影指标**：`bbox_coverage` 是**跨度**不是**填充**——
  snake 靠"左上角一颗食物 + 右下角一条蛇"刷出 33% 的 bbox 覆盖率。
  凡是被证伪过的指标，要么降级为诊断值（只记录不判定），要么给出反例。

---

## 5. 交付与回报格式

* 证据目录：`runs/<topic>/<game>/`（JSON + PNG + filmstrip + 游戏 stdout + MCP trace）。
  报告里每个数字都要能追到文件路径。
* 报告章节：① 环境能力（本机能否送键）② 双通路对照表 ③ 逐步对应表 + 同实例四处对齐
  ④ 逐帧读图描述表 ⑤ 门判据前后对比（哪些款翻红、为什么）
  ⑥ "本机限制 vs 游戏缺陷"的明确区分 ⑦ 可重跑命令逐条 ⑧ 遗留风险。
* 结论必须落在 §0 的三态之一，并写出**替代证据的强度上限**：
  例如"注入点只能放在 DisplayServer 边界之上，因此它最多证明
  `Input::parse_input_event` 之后的行为，不能证明 OS 事件能到达窗口"。
* 报告落点与返回值：只回**报告绝对路径 + 一行状态**（done / partial / failed）。

---

## 6. 反例清单（每条都真实发生过，用来防止模板被"优化"掉）

1. `frames_drawn` 递增 ⇒ 判 P3 pass（snake：渲染循环在跑，棋盘冻死）。
2. 任意状态变化 ⇒ 判 P2 "responds"（snake：`Paused`/`LastRefusedInput`/`DirectionX`）。
3. 0.4% 非背景像素 ⇒ 判 P1 "可见"（snake：结束遮罩上的 4 格蛇身）。
4. bbox 跨度 ⇒ 当作"内容铺满画面"（snake：两个对角小物刷出 33%）。
5. 动作序列把游戏暂停后不恢复 ⇒ 后置帧必然静止，却被记成"状态有变化"。
6. 对幂等动作连测两次同一通道 ⇒ 第二臂假报"无反应"。
7. 单用 `Input.parse_input_event` ⇒ 声称覆盖了"真人按键的路径"（它只覆盖
   DisplayServer 之内那一半）。
8. 只看像素差/哈希 ⇒ 冒充"读过图"。
