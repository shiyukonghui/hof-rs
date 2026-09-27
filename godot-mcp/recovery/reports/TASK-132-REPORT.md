# TASK-132 报告 —— 「Jev 当模拟真人玩家」作为新的通关判据（模型看图出操作 → 游戏接受 → 画面必须动态变化）

* 任务书：`recovery/tasks/TASK-132.md`（2026-09-27，用户裁定）
* 基线提交：`a511087`（TASK-131 的 docs 收尾）；本任务的交付提交见 §J
* 报告：**本文件**。证据根：`runs/model-player/**`（本任务新目录）、
  `runs/playability/**`、`runs/realinput/**`（TASK-131，只读引用）
* **严格单线程**：本任务期间**没有派发任何子代理**（任务书 §0 硬约束），全部在本会话串行完成
* 回路工具：`tools/playtest_player.py`（新建）；门侧判据：`tools/playability_gate.py`
  （只新增「模型玩家」判据相关行）；Jev 图像通路：`tools/playtest_agent.py`（1 处 hook）

---

## 一句话结论

**回路建成、判据落地、3 款 × 2 后端全部跑完**，并按用户口径给出三态：
**`tetris × jev` = PASS**（8/8 步：`Input.is_action_pressed` 为真 + 画面相对同帧预算的
无输入对照窗真的变了，且读图确认"硬降/下落"就是 Tetris 的规则）；
**`pong × jev` = FAIL**（10 步里 9 步：模型出操作、游戏的 InputMap 确认按下、但画面相对
对照窗**没有**动态变化）；
**`snake × 两个后端` = INCONCLUSIVE**，原因是**游戏在第一帧之前就已经 GameOver**
（TASK-131 判出的真缺陷，本任务不修，只如实遇见）；
`tetris × playjev`、`pong × playjev` = **INCONCLUSIVE**，原因是**模型锁死在同一个动作、
拿到的是逐字节相同的帧**（同一动作 + 同帧 → 无法与"游戏忽略输入"区分）。
**Jev（视觉弱）与 PlayJev（视觉微调）的差异如实报在 §F**：Jev 的答案会随图片改变
（§D.3 的三图对照），但更容易在冻结画面上陷入 `wait`/`done`；PlayJev 会锁死在
一个动作上（同一帧 → 同一答案）。

---

## A. 用户判据与实现（本任务的全部依据）

| 用户口径（任务书 §0） | 实现落点 | 证据 |
|---|---|---|
| 检查 Jev 部署 | `playtest_player.py prep` | `runs/model-player/_env/prep.json`：8080 `{"status":"ready","model":"NeoHorse-Jev-4B","input_modalities":["text","image"]}`、8081 `{"ok":true,"model":"playjev-0.8b","two_frame":false}` |
| 模型看图出操作 | `Player.make_agent` + `choice_criteria`：**恰好 1 图 + 1 个 `choice` 问**，criteria = 游戏自己 `project.godot` 的 InputMap 动作集 | §E.1 的逐字请求/响应；每步 `NN/request.json`、`NN/response.json` |
| 注入并记录画面变化 | `inject_action`（`Input.parse_input_event`）/ `inject_real_key`（Win32 `SendInput`） | 每步 `injection` 字段 + `frames/*.png` |
| FAIL = 出了操作 ∧ 接受 ∧ 画面没变 | `step_verdict` + `summarise`（纯函数，`selftest` 覆盖） | `player.json -> verdict/why/fail_steps` |
| PASS = 能成功游玩并达成动态变化，且读图判断变化符合游戏逻辑 | `summarise`（机器半）+ **本报告 §G 读图表**（读图半） | 见 §G |
| demo = 左游戏图 / 右 Jev 操作 | `build_demo`（`demo.png`） | 每款每后端 `demo.png`；§H |

### A.1 回路六步 → 每一步的证据字段

`runs/model-player/<game>/<backend>/steps.jsonl` 每行都带任务书 §1.1 step 6 要求的名：
`step`、`frame_before_sha`、`frame_after_sha`、`pixel_diff`、`control_diff`、`state_before_sha`、
`state_after_sha`、`action`、`probs`、`confidence`、`channel`、`ack_evidence`、`changed_bool`，
另加本任务为了排掉伪影而必须记录的：`control_diff.frame_budget`（两侧**同游戏帧预算**）、
`gameplay_change_labels`（字段级："哪个字段从多少变到多少"）、`markers`、`step_verdict`。

### A.2 三个必须写清的取数口径

1. **动作集来源**：`playability_gate.parse_project(game)["actions"]` → `project/` 的
   `project.godot` `[input]` 段。**不用** README 的按键表，也**不把
   `playtest_agent.action_criteria` 默认追加的 `key_W` 一类按键选项留给玩家**
   （理由与实测见 §B.3）。`session.json -> action_set_source` 记了这条。
2. **对照窗**：**同帧预算（`Engine.get_frames_drawn()` 差 = 30 帧）、零输入**，
   并且**在注入之前测**（对照窗结束的时刻 = 注入的时刻）。
   `session.json -> measurement_window` 记了预算与理由。
3. **"变化"判定**（`decide_changed`，纯函数）：`changed = 玩法移动量 > 对照窗移动量`
   **或** `像素差 > max(2.5 × 对照窗像素, 40)`。
   移动量 = 声明可观测的位置向量位移欧氏距离 / 标量差 的**总和**。

---

## B. 回路实现中量到的四个"必须先修掉"的判据伪影（全部留有前后对照）

这四条都是**先做错、被数字抓住、再改对**的，留着是为了让后来者不要重犯。

### B.1 用墙钟做"等长对照窗" ⇒ 两侧帧数不同，真实输入被当成没变化

第一版 `--control-ms 350`（墙钟）。pong/jev 第 2–6 步的动作窗与对照窗
**都报 1100 像素**——因为 MCP 往返本身会改变窗口内的帧数，两侧根本不是同一长度。
证据留在 `runs/model-player/_prefix-abandoned/pong-wallclock-and-done/`。
修法：`wait_frames()` 按 `drawn` 对齐，`frame_budget` 逐步记录
（tetris/jev 第 1 步：`start_drawn 26 → end_drawn 56, achieved_delta 30, timed_out false`）。

### B.2 只用"变化的键个数"比较 ⇒ 自己会动的游戏骗过判据

pong 的球一直在飞，两个窗口里 `Ball.pos` 都"变了"，计数相等 → 输入被当成有效果。
第 2 步实测：动作窗球走 **128.278**，对照窗球走 **141.444** → 没有赢过对照。
修法：比**移动量**而不是变化键个数（`movement_magnitude`），并用 `selftest` 钉住这条：
`ball moved 1.7 px in both windows -> NOT changed` / `paddle moved 202 px vs ball's 1.7 -> changed`。

### B.3 把 `done`（"停止探测"）留给玩家 ⇒ 模型连选 9 步 `done`

`playtest_agent.action_criteria` 默认追加 `done: "stop probing: no further action is likely
to help"`。第一次全跑（`_prefix-abandoned/pong-wallclock-and-done/`）：第 4–12 步
**请求体逐字节相同（`request_sha 22b6a951d5ddf64d`）**、模型答案 `done` P=0.61。
修法：`Player.choice_criteria` 重建 criteria（去掉 `done`，保留 `wait`），
并把它挂到 `agent.build_action_criteria` 上；为此在
`playtest_agent.PlayJevAgent.build_questions` 里**把直接调用 `action_criteria(goal)`
改成走 `self.build_action_criteria(goal)`（默认实现逐字不变）**——这是本任务对
`playtest_agent.py` 的唯一改动（1 处，7 行含注释）。

### B.4 在"开局就已结束"的游戏上照走回路 ⇒ 造出假的 FAIL

第一版 snake：模型答 `snake_right`、`Input.is_action_pressed` 报 True、画面 0 像素 →
一条看似"游戏接受输入却没反应"的 FAIL，而它测的是**一局早在第一帧之前就结束的游戏**。
修法：settle 后立刻求值 `liveness.terminal`，成立则**不发任何模型请求**，
记 `terminal_at_settle_before_the_first_model_call`（snake 两个后端都是）。

**另外两条与真实键有关的修正**（写在 §D）。

---

## C. 3 款 × 2 后端：结论速览

| 游戏 | 后端 | 步数 | 注入 | 接受 | 接受∧变化 | 比例 | **结论** | FAIL 步 |
|---|---|---|---|---|---|---|---|---|
| tetris | jev | 8 | 8 | 8 | 8 | **1.0000** | **PASS** | — |
| tetris | playjev | 12 | 12 | 12 | 3 | 0.2500 | **INCONCLUSIVE** | 4–12（同动作+同帧固定点） |
| pong | jev | 10 | 10 | 10 | 1 | 0.1000 | **FAIL** | 1,2,3,4,5,6,8,9,10 |
| pong | playjev | 10 | 10 | 10 | 1 | 0.1000 | **INCONCLUSIVE** | 2–10（同动作+同帧固定点） |
| snake | jev | 0 | 0 | 0 | 0 | — | **INCONCLUSIVE** | —（第一帧前已终止） |
| snake | playjev | 0 | 0 | 0 | 0 | — | **INCONCLUSIVE** | —（第一帧前已终止） |
| pong（真实键臂） | jev | 10 | 5 | 5 | 2 | 0.4000 | **FAIL** | 1,2,3 |

`runs/model-player/_resummary.json` 是本表的机器可读版；
每款的判词原文在 `<game>/<backend>/player.json -> why`。

---

## D. ack 证据（Y3）：每一处都指名用了哪一条

`ack_evidence` 的取值只有四种，全部来自**游戏自己的话**（模型的回答一概不算证据）：

| 取值 | 含义 | 读的是什么 |
|---|---|---|
| `action_pressed` | 最强：注入瞬间/按住期间，游戏自己的 InputMap 认为该 action 按下 | `Input.is_action_pressed("%s")`（`probe_action_state`，在游戏进程内执行） |
| `state_moved` | 声明的玩法可观测在该窗口内移动了 | `state_delta` ∩ `gameplay_observables.items` |
| `refused_recorded` | 游戏自己记录了**蓄意拒绝**（它看见了输入，并说"不行"：墙/边界） | `LastRefusedInput`/`Rejected*`（`refusal_evidence` 声明） |
| `nothing` | 上述都没有 ⇒ **不接受**，该步不计入比例 | — |

**模型没出可注入动作的步**（空 choice / `wait` / 传输错误）被显式标为
`injected=false` 并**排除在比例之外**，同时抑制 `state_moved` 这条捷径——
否则一个自己会动的游戏会被记成"接受了一个从没发出的输入"（`selftest` 覆盖：
`8 steps but the model never acted -> INCONCLUSIVE`）。

### D.1 真实 OS 键臂（`--channel real`，TASK-131 配方，未重新发明）

`runs/model-player/realkey/pong/jev/`。逐步 `injection` 里保存了完整证据：

| step | action | VK | SendInput 下行/上行 | 焦点 | `GetForegroundWindow` 后 | 按住时 `Input.is_action_pressed` | 逐帧 |
|---|---|---|---|---|---|---|---|
| 1 | `pong_serve` | 0x20 SPACE | **1 / 1** | **ok** | `hwnd 10358590 / pid 109632 / class Engine / "pong (DEBUG)"` | **true (strength 1.0)** | §G.2 |
| 2 | `pong_serve` | 0x20 | 1 / 1 | ok | 同上（同一 hwnd） | true | — |
| 3 | `pong_serve` | 0x20 | 1 / 1 | ok | 同上 | true | — |
| 4 | `pong_serve` | 0x20 | 1 / 1 | ok | 同上 | true | — |
| 5 | `pong_serve` | 0x20 | 1 / 1 | ok | 同上 | true | §G.2 |

**两条与真实键有关的修正（都实测过）**：

1. **必须在 `SendInput` 之后留 settle 才能读 ack**：OS 键先到窗口消息队列，再由
   DisplayServer 变成 `InputEventKey`；同毫秒读会读到**处理之前**的状态。
   第一版真实键回路因此只报出 `state_moved`，看起来像"真实键没进 InputMap"。
   修法：`--ack-read-delay-ms 60`（默认），并记录 `injection.ack_after_keydown`。
2. **ack 判定要同时认 `is_action_pressed` 与 `pressed`**：门的 `probe_action_state`
   返回的字段名是 `pressed`（`{"pressed": Input.is_action_pressed(...)}`），
   而合成臂自己的探针返回 `is_action_pressed`。只认一个字段会把真实的
   `pressed: true` 读成 None。

**结论（真实键臂）**：真实 OS 键在本机**确实送达游戏进程并触发了 InputMap**
（焦点落在游戏自己的窗口、`SendInput` 1/1、按住时 `is_action_pressed==true`），
与 TASK-131 §A 的结论一致；本任务的真实键臂只跑 pong（任务书 §1.1 step 3 的"至少 1 款"要求）。

---

## E. 变化证据（Y4）：逐步表 + 对照窗

（**像素**：该窗口 `PNG` 变化像素数；**移动**：声明可观测的移动量总和；
`ctl` 列 = 同帧预算的零输入对照窗。）

### E.1 tetris × jev —— **PASS**

| step | action | conf | http | ack（证据） | px / ctl px | 玩法移动 / ctl | 帧 before → after | 判词 |
|---|---|---|---|---|---|---|---|---|
| 1 | `tetris_drop` | 0.1053 | 200 | True (`action_pressed`) | 5290 / 0 | 6.0 / 0.0 | `d0b29873ef` → `6b4c6bfc86` | ok_ack_and_changed |
| 2 | `tetris_down` | 0.1632 | 200 | True (`action_pressed`) | 2116 / 0 | 1.0 / 0.0 | `6b4c6bfc86` → `1f173cff90` | ok_ack_and_changed |
| 3 | `tetris_drop` | 0.1615 | 200 | True (`action_pressed`) | 5290 / 0 | 7.0 / 0.0 | `1f173cff90` → `a14befbaef` | ok_ack_and_changed |
| 4 | `tetris_down` | 0.0805 | 200 | True (`action_pressed`) | 3174 / 0 | 1.0 / 0.0 | `a14befbaef` → `31d66cc9c8` | ok_ack_and_changed |
| 5 | `tetris_down` | 0.1017 | 200 | True (`action_pressed`) | 3174 / 0 | 1.0 / 0.0 | `31d66cc9c8` → `bb17fe8380` | ok_ack_and_changed |
| 6 | `tetris_down` | 0.1308 | 200 | True (`action_pressed`) | 3174 / 0 | 1.0 / 0.0 | `bb17fe8380` → `0ad9f35ef9` | ok_ack_and_changed |
| 7 | `tetris_down` | 0.1177 | 200 | True (`action_pressed`) | 3174 / 0 | 1.0 / 0.0 | `0ad9f35ef9` → `ffac6cf04f` | ok_ack_and_changed |
| 8 | `tetris_down` | 0.0984 | 200 | True (`action_pressed`) | 3174 / 0 | 1.0 / 0.0 | `ffac6cf04f` → `a5b7e5c4a5` | ok_ack_and_changed |

字段级玩法变化（`gameplay_change_labels`，摘）：step1
`FilledCells 0→4; NextKind 1→2; PieceKind 0→1`；step2 `PieceY 0→1`；
step3 `FilledCells 4→8; NextKind 2→3; PieceKind 1→2; PieceY 1→0`；
step4–8 `PieceY 1→2→3→4→5`。
`frame_budget`（step1）：`start_drawn 26 → end_drawn 56`，`achieved_delta 30`，未超时。

### E.2 pong × jev —— **FAIL**（用户点名的"问题"实例之一）

| step | action | conf | ack | px / ctl | 玩法移动 / ctl | 判词 |
|---|---|---|---|---|---|---|
| 1 | `pong_serve` | 0.2948 | True (`action_pressed`) | 1100 / 512 | 114.413 / 293.791 | **FAIL_no_change_after_accepted_input** |
| 2 | `pong_serve` | 0.2265 | True | 512 / 512 | 128.278 / 141.444 | FAIL |
| 3 | `pong_serve` | 0.2427 | True | 512 / 512 | 128.753 / 151.639 | FAIL |
| 4 | `pong_serve` | 0.2427 | True | 512 / 512 | 109.041 / 129.778 | FAIL |
| 5 | `pong_serve` | 0.2306 | True | 973 / 432 | 149.758 / 311.767 | FAIL |
| 6 | `pong_serve` | 0.2615 | True | 512 / 512 | 129.434 / 145.638 | FAIL |
| 7 | `pong_serve` | 0.2603 | True | 512 / 512 | 138.204 / 137.657 | ok_ack_and_changed |
| 8 | `pong_serve` | 0.2474 | True | 512 / 512 | 135.367 / 136.947 | FAIL |
| 9 | `pong_serve` | 0.1997 | True | 512 / 512 | 131.255 / 138.665 | FAIL |
| 10 | `pong_serve` | 0.2729 | True | 512 / 512 | 127.154 / 140.624 | FAIL |

**必须点名这条 FAIL 的性质**（否则容易被误读成"画面是死的"）：
**pong 的画面对照窗一直在动**（球自己飞，对照窗 432–512 像素），
FAIL 的意思是"**这个输入没有造成可分辨的动态变化**"——球的位置变化只由它自己的
弹道决定（`Ball.pos` 在**两个窗口**里都变了，移动量还常常**小于**对照窗）。
这正是用户判据里"接受了却没变化"的那一类，因为判据的比较基准是
**同帧预算的零输入对照**，不是"画面是不是全静止"。

### E.3 snake × jev（与 × playjev 相同）—— **INCONCLUSIVE**

| 项 | 值 | 证据 |
|---|---|---|
| settle 状态 | `GameOver=true`, `LoseReason="wall"`, `Ticks=19`, `Score=10` | `states/00_settle.json`、`states/00_live_check.json` |
| 模型调用次数 | **0**（在第一次调用前就中止） | `player.json -> terminal_at_settle_before_the_first_model_call` |
| 游戏自己的 stdout | `SNAKE_WALL head=25,10 cols=25 rows=21 score=10 ticks=19` | `engine-game.stdout.txt` |
| 输入映射里有没有重开键 | **没有**（只有 `snake_up/down/left/right/pause`） | `session.json -> actions_offered` |

### E.4 neg_frozen × jev —— Y5 的**受控 FAIL 实例**（6/6 步）

`projects/_exercises/neg_frozen`（breakout 的副本，`Main.process_mode = 4`）**只读**使用，
声明取自其源工程（`--controls-game breakout`，记录在 `session.json.controls_game`）。

| step | action | ack | px / ctl | 玩法移动 | 帧 before → after | 判词 |
|---|---|---|---|---|---|---|
| 1–6 | `breakout_launch` | True (`action_pressed`) | 0 / 0 | 0.0 / 0.0 | `c8df2c551a` → `c8df2c551a`（**同一哈希**） | **FAIL_no_change_after_accepted_input** |

`gate.json` 侧（`runs/model-player/_gatecheck/pong/gate.json`）对 pong 的
`model_player_criterion.evidence.pass=false` 也是同一条规则的可核对实例。

---

## F. Jev 与 PlayJev 对照（Y8，如实报差异）

| 维度 | jev（8080，`NeoHorse-Jev-4B`，视觉**未**微调） | playjev（8081，`playjev-0.8b`，视觉**微调过**） |
|---|---|---|
| 图像通路 | `image` 顶层 data URL，**恰好 1 问**（`image_tokens 475`） | `state.frames[0]` data URL；**1 图 + N 问**，本回路只问动作时答案里仍带 `playable`/`no_render_failure`/`responds_to_input`/`brokenness` |
| 是否真的随图片变化 | **是**（§F.1 三图对照：同一 criteria、无文本 state，`pong_serve` 概率 0.429 → 0.148，答案从 `pong_serve` → `done` → `wait`） | 是（同帧同答；不同帧答案不同——见 §G 的逐步读图） |
| tetris 结果 | **PASS**（8/8，动作 `drop`/`down` 都是推动玩法的） | INCONCLUSIVE（连选 `tetris_left` 直到左墙，之后同帧同答） |
| pong 结果 | FAIL（9/10 步输入无差异） | INCONCLUSIVE（连选 `pong_right_down`，挡板到底后同帧同答） |
| 失效模式 | 画面"看起来静止/结束"时倾向 `wait`/`done`（`done` 已从候选移除后，改为 `wait` P=0.61 连选） | 锁死在一个动作上：同一帧 → 同一动作（`tetris_left` P≈0.58 连选 9 步） |
| 置信度 | 0.08–0.34（未校准，厂商未报告 NLL/Brier/ECE） | 0.34–0.66（同样未校准；`x-neohorse-confidence` 头只在 jev 侧出现，值是 `local-distribution-statistic-v1`） |
| 响应时延（本机实测） | 数秒/次（4B + 与 PlayJev 共用一块 4090，串行） | ~0.77 s/次（8B 侧 `timing.total_ms 766.7`） |

### F.1 证明"Jev 真的在读那张图"（三图对照，`runs/model-player/_probe/jev_image_sensitivity.json`）

同一 criteria 集、**不送任何文本 state**，只换图片：

| 图片 | 答案 | `pong_serve` | `done` | `wait` |
|---|---|---|---|---|
| `pong/jev/frames/001_settle.png`（球停中线） | `pong_serve` | **0.4290** | 0.0653 | 0.2401 |
| `pong/jev/frames/013_04_after.png`（比赛结束画面） | `done` | 0.1481 | **0.4616** | 0.3103 |
| `playability/snake/frames/01_settle.png`（snake 结束遮罩） | `wait` | 0.1481* | 0.1481* | **0.0848** |

（\*第三张的完整概率向量与第二张不同；本表只摘了三个键。两个向量
**不是**逐一相等，脚本自己打印 `probability vectors identical: False` 并列出每个键的两侧值。）
**结论**：Jev 的图像通路**是活的**，答案会随画面改变；但**未微调**这一点是真实的——
它的答案常常只反映"画面像不像结束/静止"这种整体判断，而不是位置级的战术意图
（3 款里没有一次选出左右挡板/方向的战术动作）。

---

## G. 强制读图（Y6）—— 我实际用 `read_image` 看过什么，以及看到了什么

### G.1 读图清单（分辨率 / 用途，逐张）

| # | 文件 | 尺寸 | 用途 |
|---|---|---|---|
| 1 | `runs/model-player/tetris/jev/demo.png` | 884×2070（8 行） | tetris/jev 的整体读图：左帧右操作 |
| 2 | `runs/model-player/tetris/jev/frames/002_01_before.png` | **800×600 全尺寸** | step1 注入前：空场 + 顶部青色 I 型 4 格 + 左侧 HUD |
| 3 | `runs/model-player/tetris/jev/frames/004_01_after.png` | **800×600 全尺寸** | step1 注入后：I 型已落在底部 + 顶部出现黄色 O 型（下一块） |
| 4 | `runs/model-player/tetris/jev/filmstrip.png` | 1086×1042（27 格） | 全部 27 帧逐格：确认 step1/step3 的"落下"与 step2、4–8 的"下移一格" |
| 5 | `runs/model-player/tetris/playjev/demo.png` | 884×2572（12 行） | tetris/playjev：左移 3 次到墙、之后 9 帧同一哈希 |
| 6 | `runs/model-player/pong/jev/demo.png` | 884×2572（10 行） | pong/jev：FAIL 逐步读图 |
| 7 | `runs/model-player/realkey/pong/jev/demo.png` | 884×2572（10 行） | 真实键臂：比分 0-0 → 5-0 GAME OVER 遮罩 |
| 8 | `runs/model-player/realkey/pong/jev/filmstrip.png` | 1086×1438（33 格） | 真实键臂全部帧：确认比分推进与结束遮罩 |
| 9 | `runs/model-player/pong/playjev/demo.png` | 884×2572（10 行） | pong/playjev：右挡板从中位到底部、之后同一哈希 |
| 10 | `runs/model-player/neg_frozen/jev/demo.png` | 884×1568（6 行） | Y5：6 步全同哈希的受控 FAIL |
| 11 | `runs/model-player/neg_frozen/jev/frames/002_01_before.png` | **800×600 全尺寸** | 冻结的画是什么样（SCORE 0 + 三排砖 + 挡板） |
| 12 | `runs/playability/snake/frames/01_settle.png` | **800×600 全尺寸** | snake 第一帧就是结束画面 |
| 13 | （TASK-131 遗留，只读引用）`runs/playability/snake/filmstrip.png` | 1086×1042 | 交叉核对"23 帧全同" |

**读图边界（照实声明）**：上述 13 张**都真的用 `read_image` 看过**；其中
**5 张 800×600 全尺寸原图**、其余是 demo/filmstrip（缩略）。
**HUD 小字类结论一律以状态字段为准**（例如 tetris 的 `Score/Lines/Level` 在
缩略图里读不出，就以 `markers` 字段为准），**没有**用像素差或 sha256 冒充"看过图"。

### G.2 逐帧描述表（"看到了什么 → 变了什么 → 是否与该步操作相符"）

#### G.2.1 `neg_frozen × jev`（Y5 受控实例，我给的是同一张哈希的 6 步）

| 帧 | 我看到了什么 | 与上一帧相比 | 与操作相符？ | 结论 |
|---|---|---|---|---|
| step1 before `c8df2c551a` | 黑底；左上 `SCORE 0`；顶部三排砖（红/橙/绿各 5 格，第 3 排缺 1 格填了深色）；中场偏下一颗黄色小子弹、最下方一条青色挡板 | — | 无操作 | 冻结局的开局画面 |
| step1 after `c8df2c551a` | **与 before 完全一样**（同一 sha256） | **无任何变化** | **不相符**：按了 `breakout_launch`（SPACE）却什么都没有发生 | **FAIL**（接受∧没变化） |
| step2–6 before/after | 同上，**6 步全部同一哈希** | 无变化 | 不相符（每次都是发球键） | 受控 FAIL 复现成立 |

**符合游戏逻辑吗**：不适用——这是一个**故意做坏**的受控变体
（`Main.process_mode = 4`，`_Process`/输入处理整棵子树关闭），
它的用途就是证明"模型出操作 + ack 成立 + 画面不动 ⇒ 判 FAIL"这条规则**会响**。

#### G.2.2 `tetris × jev`（PASS 的读图半）

| 帧 | 我看到了什么 | 与上一帧相比 | 与操作相符？ | 结论 |
|---|---|---|---|---|
| step1 before | 左面板写 `TETRIS 10x20`；右面板（10×20 场地）**顶部正中一条青色 4 格 I 型**；场地内其它位置全空 | — | — | 开局 |
| step1 after | **顶部 I 型消失**，**底部中央出现一条灰色 4 格**（已落地的方块被画成灰），**顶部出现一个黄色 2×2 O 型** | 场地上多了 4 格落地块 + 顶部换了新块 | **相符**：模型选了 `tetris_drop`（硬降 E），`state_delta` 里
`/root/Main.LastEvent: "" → "harddrop dropped=18 piece=I score=0 lines=0 over=False"`、`FilledCells 0→4`、`PieceKind 0→1`、`NextKind 1→2` | ✅ |
| step2 before→after | 顶部黄色 O 型**整体下移一格**（第二行） | 只差一行 | **相符**：`tetris_down`（S，软降）→ `PieceY 0→1`；读数 2116 px | ✅ |
| step3 before→after | 顶部换回**紫色 T/S 型**；底部灰色堆从 4 格增加到 8 格（第二块已落地） | 又落了一块 + 换新块 | **相符**：`tetris_drop` → `LastEvent "harddrop dropped=18 piece=O"`、`FilledCells 4→8`、`PieceKind 1→2`、`NextKind 2→3`；5290 px | ✅ |
| step4–8 before→after | 紫色块逐帧**下移一格**（`PieceY 1→2→3→4→5`），每帧 3174 px | 每帧一行 | **相符**：`tetris_down` → `PieceY n→n+1` | ✅ |

**"符合游戏逻辑"的推理依据**：Tetris 的规则是"方块受控下落/转向、落地后固定并生成新块、
填满整行才消行加分"。这 8 步里每一次都同时满足三件事：
(a) 模型选的键就是该动作声明的键（`tetris_drop`=`E`、`tetris_down`=`S`，来自 InputMap）；
(b) 游戏自己的 `LastEvent`/`PieceX/PieceY`/`FilledCells`/`NextKind` 的变化**恰好是该动作的定义**
（硬降 ⇒ 直接落地 + 生成新块；软降 ⇒ `PieceY+1`）；
(c) 我**看图**确认了"块确实在场地里多了一行/落了地"，
像素差 2116–5290 **稳定地赢过**同帧预算的零输入对照窗（对照窗 0 像素 ——
因为 tetris 的重力间隔长于 30 帧，零输入窗口里块本来就不会动）。
**没有**出现"画面变了但状态没变"或"状态变了但画面没变"的不一致。

#### G.2.3 `pong × jev`（FAIL 的读图半）

| 帧 | 我看到了什么 | 与上一帧相比 | 与操作相符？ | 结论 |
|---|---|---|---|---|
| step1 before | 深蓝场地；左侧竖条（青，偏上）、右侧竖条（红，居中）；右半场一颗黄球；顶部两个白色 `0` `0` | — | — | 球在飞行中 |
| step1 after | 同场地；**球移到左半场**（`Ball.pos [639.1,426.9]→[542.9,365.0]`）；两块挡板**完全没动**；比分仍 `0 0` | 球移动 | **不相符**：按的是 `pong_serve`（SPACE），而球**本来就在飞**（prep 阶段已发过球），SPACE 在这局里是幂等的 | **FAIL**（接受∧无差异） |
| step2–6 before→after | 每帧球都在**自己的弹道**上（`[651.9,435.1]→[544.0,365.7]` 等），挡板不动、比分不变 | 球在动，但**动作窗与对照窗的球移动量分别 128.3 vs 141.4、128.8 vs 151.6、109.0 vs 129.8、149.8 vs 311.8、129.4 vs 145.6** —— 都**没赢过对照** | 不相符 | FAIL |
| step7 before→after | 球 `[653.7,436.2]→[537.5,361.5]`，移动量 138.204 vs 对照 137.657（**刚好赢过**） | 赢过对照窗 | 勉强相符 | 唯一 `ok_ack_and_changed`（说明阈值不是"永远判 FAIL"） |
| step8–10 | 同 step2–6 | 没赢过对照 | 不相符 | FAIL |

**符合游戏逻辑吗**：**这条 FAIL 不是"游戏坏了"**。
读图 + 状态一起给出的结论是：**pong 的球在 Prep 之后一直在自己飞，模型反复按发球键，
而发球在球已飞行时是幂等的**——所以"输入没有造成可分辨的变化"。
判据要求"相对同帧预算的零输入对照窗出现动态变化"，而这 9 步没有。
（另一条独立证据：`engine-game.stdout.txt` 显示整局是 `PONG_SCORE scored_by=LEFT` ×5 →
`PONG_OVER winner=LEFT left=5 right=0`，左侧**在模型有机会干预前**就以 5:0 结束了比赛，
时间约在 settle 后 12 秒内。）

#### G.2.4 `snake × jev / playjev`（INCONCLUSIVE 的读图半）

`runs/playability/snake/frames/01_settle.png`（800×600 全尺寸，只读引用 TASK-131 的产物；
本任务的 snake 运行在 sleep 4 s 后采的 settle 帧与它同源同义）：

**我看到的**：整屏是一层**暗红**（`bg=[88,24,24]`：35% 透明度的红遮罩压在深绿背景上）；
画面被**淡淡的网格线**分成 25×21 格；第 10 行靠右有一条**暗绿色 4 格横条**
（`x≈504…600`，即格子 21–24 → 蛇身 `Length=4`）；**左上角一颗红色 24×24 方块**
（`Food` 被重生到 `(0,0)`，全屏唯一亮红点）；**没有任何分数/HUD/文字**。
**与上一帧相比**：这就是第一帧（本任务没有更早的帧）；TASK-131 记录了它之后 23 帧
逐字节相同（`--settle 4.0` 让第一帧出现在约 4 秒之后）。
**与操作相符吗**：**不适用**——这是 `GameOver=true` 的**结束画面**；
游戏自己的 stdout 写着 `SNAKE_WALL head=25,10 cols=25 rows=21 score=10 ticks=19`
（`StepSeconds=0.08`×19 ≈ **1.52 秒游戏时间**），而 InputMap 里**没有重开键**。
因此：**模型连不上"可玩"这件事**，判 INCONCLUSIVE（缺的是"一个还没结束的局面"）。

#### G.2.5 真实键臂 `realkey/pong/jev`（33 帧全部看过）

| 帧 | 我看到了什么 | 变了什么 | 与操作相符？ |
|---|---|---|---|
| #01 settle / #02 prep_before | 比分 `0 0`，两块挡板居中，**球在中线**（未发球） | — | 初始 |
| #03 prep_after | 比分仍 `0 0`，**球离开中线向右下飞出** | 球动了（prep 用的是合成通道，非本臂动作） | 相符（发球生效） |
| #04–#06 step1（**真实 SPACE**） | `0 0` → `1 0`；球在其弹道上；挡板未动 | 球移动 + 比分 +1（球出界） | **不相符**：真实 SPACE 发出，InputMap 报 pressed，但球已飞 → 无差异（FAIL） |
| #07–#15 step2–5（**真实 SPACE**） | 比分 `1 0`→`2 0`→`3 0`→`4 0`→`5 0`；球持续移动 | 比分推进（球每次出界） | 其中 step4/#15 的 `1003 px > 512` 赢过对照 → `ok_ack_and_changed` |
| #16 之后（step6–10） | **`GAME OVER - LEFT WINS 5:0`** 白字出现在场地中线；比分固定 `5 0`；**球回到中线静止**；挡板不动 | 全静止（游戏已结束） | 不相符：模型此时改答 `wait`（无动作）→ `no_ack_no_change`，被排除在比例外 |

**这条臂读出的三件事**：(1) 真实 OS 键确实驱动了游戏（比分从 0-0 走到 5-0）；
(2) 左方在模型真正开始"玩"之前就赢了——**pong 与 snake 同型的结构性问题：
终局先于模型的决定到来**；(3) 游戏结束后模型不再出可注入动作（`wait` P=0.61）。

---

## H. demo 产物（Y7）

每款每后端一张 `demo.png`：**左列 = 该步模型看到的那一帧**（整窗 800×600 缩略），
**右列 = 该步模型输出的动作名 + 键盘 + 该动作的**概率条**（前 5 名，选中的那条高亮）
+ `ack/changed/判词` 三行 + 该步"玩法可观测移动了什么"（字段级）**，左右按步对齐。

| 产物 | 路径 | 尺寸 |
|---|---|---|
| tetris/jev | `runs/model-player/tetris/jev/demo.png` | 884×2070（8 行） |
| tetris/playjev | `runs/model-player/tetris/playjev/demo.png` | 884×2572（12 行） |
| pong/jev | `runs/model-player/pong/jev/demo.png` | 884×2572（10 行） |
| pong/playjev | `runs/model-player/pong/playjev/demo.png` | 884×2572（10 行） |
| 真实键臂 pong/jev | `runs/model-player/realkey/pong/jev/demo.png` | 884×2572（10 行） |
| Y5 受控 FAIL | `runs/model-player/neg_frozen/jev/demo.png` | 884×1568（6 行） |
| snake（两后端） | 无（0 步：中止于第一次模型调用前） | — |

Filmstrip（门的既有格式）：每个 run 目录下 `filmstrip.png`。
FAIL 专项图：`runs/model-player/_failcase/{pong-jev,pong-playjev,tetris-playjev,neg_frozen-jev}.png`
（由 `playtest_player.py failcase --path <run>` 生成，逐条列出三个子句的读数）。

---

## I. 门侧的判据落点（Y9 的"其他判据只列代码能跑"）

`tools/playability_gate.py` **只新增**了模型玩家判据相关的行（`git diff --stat`：146 行新增）：

* `MODEL_PLAYER_CRITERION_NOTE`：把用户口径写进门里 ——
  "P1..P7 回答的是'游戏代码能不能跑、能不能画'，**它们不是可玩性判据**"。
* `evaluate_model_player_steps(steps, game)`：把同一条规则（含固定点/终止态两个证据质量区分）
  作用在录制的 `steps.jsonl` 上 —— 与回路自己的 `summarise` **同一套判定**。
* `record_model_player_criterion(gate, args, game)`：**在完整跑与 `--only-p7` 两条路径上都调用**，
  把规则与数字记进 `gate.json -> model_player_criterion`。
* CLI：`--model-player-steps <steps.jsonl>`。

实测（`runs/model-player/_gatecheck/`）：

| 运行 | P1..P7 | `model_player_criterion.evidence.pass` |
|---|---|---|
| `--games pong --only-p7 --model-player-steps runs/model-player/pong/jev/steps.jsonl` | `P7=PASS` | **false**（"9 accepted input(s) left the viewport unchanged … steps [1,2,3,4,5,6,8,9,10]"） |
| `--games tetris --model-player-steps runs/model-player/tetris/jev/steps.jsonl` | `P1..P7 全 PASS` | **true**（8/8，rate 1.0000） |

**这就是"P1..P7 全绿 ≠ 可玩"的当场示范**：pong 的 `P7=PASS`（两个 `ScoreLeft/ScoreRight`
标签都在、可见、面积达标）而模型玩家判据 `pass=false`。
（既存缺陷照实点名：这一跑仍在 `--agent` 段抛
`EXCEPTION: AttributeError: 'ScriptedAgent' object has no attribute 'last_evidence'`——
TASK-131 已登记，**不是本轮引入**，P1..P7 与模型玩家判据都在它之前算完。）

---

## J. 验收判据 Y1–Y10 逐条

| 编号 | 结论 | 证据 |
|---|---|---|
| **Y1** | **完成** | `tools/playtest_player.py` 子命令 `run/prep/selftest/summary/demo/resummarise/failcase`；`--help` 可用；重跑命令见 §K.1；`python tools\playtest_player.py selftest` 全绿（22 条断言，纯函数、无游戏无模型） |
| **Y2** | **完成** | §E/§F.1 的逐字证据：`runs/model-player/pong/jev/01/request.json`（6690 B）里 `image = "data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAAAy…rkJggg=="`（长 5846）、`questions` 只有 `move` 一个 `choice`（`with_image true, question_count 1`）、`state {}`；响应 `usage {"input_tokens":650,"output_tokens":178,"image_tokens":475}`。PlayJev 的逐字证据同法（`tetris/playjev/01/`） |
| **Y3** | **完成** | §D 表 + 每步 `ack_evidence`；**实物**：`probe_action_state` 的返回被存进 `injection.ack_result`（合成）与 `injection.ack_after_keydown`（真实键），如 `{"action":"pong_serve","has_action":true,"pressed":true,"strength":1.0}` |
| **Y4** | **完成** | §E 逐步表（`frame_before_sha`/`frame_after_sha`/`pixel_diff`/`control_diff`/`frame_budget`/`changed_bool`），`steps.jsonl` 每行齐备 |
| **Y5** | **完成** | §E.4 + §G.2.1：`neg_frozen` **6/6 步** `FAIL_no_change_after_accepted_input`（同哈希 6 次），产物 `runs/model-player/_failcase/neg_frozen-jev.png`（另有 pong/tetris/playjev 三个真实实例的 failcase 图）。规则本身由 `selftest` 钉住：`accepted + 0 px vs 0 control -> FAIL_no_change_after_accepted_input` |
| **Y6** | **完成** | §G：**13 张图**真看过（5 张 800×600 全尺寸），逐帧描述表 + "是否符合游戏逻辑"的推理；读图边界照实声明 |
| **Y7** | **完成** | §H：6 张 `demo.png`（884×1568…2572），左帧右操作对齐，含概率条与字段级玩法变化；filmstrip 齐备 |
| **Y8** | **完成** | §C（3 款 × 2 后端齐全，snake 为 0 步但有明确理由）+ §F 对照表 + §F.1 的三图对照（"Jev 视觉弱"如实写：答案随图变，但从没选出位置级战术动作） |
| **Y9** | **完成** | §C 三态逐款（PASS 1 / FAIL 2 / INCONCLUSIVE 4，含真实键臂）+ §I（其他判据只列"代码能跑"：`--model-player-steps` 把规则记进 `gate.json`，实测 pong `P7=PASS` 而模型玩家 `pass=false`） |
| **Y10** | **完成** | §L 铁律与文件所有权自查 + 两仓 `git log/status`；`recovery/tasks/TEMPLATE-logic-feedback.md` 已更新为**含"模型玩家 + 读图 + demo 布局"**的模板（新增 §0.1 判据重心、§1 回路六步与三条取数口径、§5 demo 布局硬要求、§7 的反例 9–15） |

---

## K. 可重跑命令（逐条，无 shell 重定向）

### K.1 回路

```text
:: 0) 只读环境（服务/端口/引擎/exe）→ runs\model-player\_env\prep.json
python tools\playtest_player.py prep

:: 1) 纯函数自检（无游戏、无模型；判据规则本身）
python tools\playtest_player.py selftest

:: 2) 3 款 × 2 后端（串行；模型服务共用一块 4090）
python tools\playtest_player.py run --game tetris --backend jev     --steps 12 --port 9952
python tools\playtest_player.py run --game tetris --backend playjev --steps 12 --port 9952
python tools\playtest_player.py run --game pong   --backend jev     --steps 10 --prep-actions pong_serve --port 9951
python tools\playtest_player.py run --game pong   --backend playjev --steps 10 --port 9951
python tools\playtest_player.py run --game snake  --backend jev     --steps 12 --port 9953
python tools\playtest_player.py run --game snake  --backend playjev --steps 12 --port 9953

:: 3) 真实 OS 键对照臂（TASK-131 配方；至少 1 款）
python tools\playtest_player.py run --game pong --backend jev --steps 10 --prep-actions pong_serve --channel real --out-prefix realkey --port 9951

:: 4) Y5 受控 FAIL（只读使用 projects\_exercises\neg_frozen，声明取自其源工程 breakout）
python tools\playtest_player.py run --game neg_frozen --controls-game breakout --project-dir projects/_exercises/neg_frozen --steps 6 --port 9954

:: 5) 由已录制的证据重算结论 / 重建产物（不需要游戏与模型）
python tools\playtest_player.py resummarise
python tools\playtest_player.py summary  --path runs\model-player\tetris\jev
python tools\playtest_player.py demo     --path runs\model-player\tetris\jev
python tools\playtest_player.py failcase --path runs\model-player\pong\jev
python runs\model-player\_scripts\rebuild_all_demos.py

:: 6) 门侧：把模型玩家判据记进 gate.json
python tools\playability_gate.py --games pong   --only-p7 --out-root runs\model-player\_gatecheck --port 9961 --model-player-steps runs\model-player\pong\jev\steps.jsonl
python tools\playability_gate.py --games tetris --out-root runs\model-player\_gatecheck --port 9961 --model-player-steps runs\model-player\tetris\jev\steps.jsonl
```

### K.2 核验脚本（都在 `runs/model-player/_scripts/`，只读证据）

```text
python runs\model-player\_scripts\prep_probe.py            :: 服务/端口/引擎/exe
python runs\model-player\_scripts\dump_actions.py pong snake tetris breakout
python runs\model-player\_scripts\report_tables.py tetris/jev pong/jev realkey/pong/jev
python runs\model-player\_scripts\evidence_y2.py           :: Y2 逐字请求/响应
python runs\model-player\_scripts\dump_choices.py runs\model-player\pong\jev
python runs\model-player\_scripts\req_hash.py runs\model-player\tetris\playjev 01 02 03 04 05
python runs\model-player\_scripts\show_injection.py runs\model-player\realkey\pong\jev
python runs\model-player\_scripts\show_gate_criterion.py   :: gate.json 里的模型玩家判据
python runs\model-player\_scripts\check_gate_criterion.py  :: 门侧 vs 回路侧逐款一致性
python runs\model-player\_scripts\backfill_labels.py       :: 由 state_delta 重推字段级标签
python runs\model-player\_scripts\probe_jev_image.py <3 张图>   :: Jev 图像敏感性
```

---

## L. 铁律与文件所有权自查（Y10）

* **无 shell 重定向**：全部产物由 Python 句柄写盘（`io.open(...,"w")` / `open(...,"wb")` /
  门的 `write_json`）；`git show/status` 也走 Python 或直接读取。
* **未改 20 款正式工程的逻辑**：`projects/<game>/` 只读；`projects/_exercises/neg_*` 只读
  （`neg_frozen` 作为 **Y5 受控实例**被读取运行，输出写在 `runs/model-player/**`，
  **一个字节都没写回工程**；声明取自 `--controls-game breakout`，记录在 `session.json`）。
* **未杀服务、未动两个 venv、未动 `F:\models\**`**；只用 8080/8081 本机服务，**零第三方端点**。
* **端口**：`9951 / 9952 / 9953 / 9954 / 9961`，跑前 `kill_what_holds` 查占用；
  与 9877/9888/9889/8080/8081 无关。
* **串行调用**：一个 step 结束后才发下一个请求；PlayJev/jev 全跑期间没有并发请求
  （`playtest_agent` 各自带 `threading.Lock`，本回路单线程调用）。
  `429/529` 按 `Retry-After` 退避的代码在 `playtest_agent._post_decision` 内，本轮**未触发**。
* **事实来源分级**：本报告的一手来源 = 本机实测（`runs/model-player/**`、游戏 stdout、
  MCP trace）与仓库代码；二手来源 = TASK-131 报告与本任务书中的既有结论，引用时点明出处
  （如 snake 的自撞过程引用 `runs/playability/snake/`）。
  代码与文档冲突时以代码为准：本轮**没有**发现冲突，但**纠正了一处工具文档级误解**——
  任务书 §1.1 step 4 举例的 `Input.is_action_pressed` 与门的
  `probe_action_state` 返回字段名（`pressed`）不一致，实现里两者都认（§D）。
* **未触发两变体重建 / 十道门**（铁律 8）：本任务**没有改引擎模块**——
  改动只在 `tools/playtest_player.py`（新）、`tools/playability_gate.py`（只新增模型玩家判据）、
  `tools/playtest_agent.py`（1 处 hook，7 行，默认行为逐字不变）、
  `recovery/tasks/TEMPLATE-logic-feedback.md`、`recovery/reports/TASK-132-REPORT.md`、
  `DECISIONS.md`。依据：`godot-mcp/godot/` 一个字节没动
  （`git -C godot status --short` 只有 TASK-130 之前就在的未跟踪 `uid_cache.bin`）。

### L.1 两仓 git（提交后回填见 §M）

**外层仓 `F:\moonbit-hof-rs`（`master`）**：本任务交付提交见 §M；基线 `a511087`。

**嵌套引擎仓 `F:\moonbit-hof-rs\godot-mcp\godot`（自带 `.git`）**：本任务**零字节改动**

```text
ba1587c71e fix(mcp_server): TASK-112 - ...            <- 与本任务无关，仍是 HEAD
3fdabe2d9a fix(godot-mcp): TASK-110 - ...
1f9d0cb1c9 modules/mcp_server: task103 - ...
1c7f5c07a1 modules/mcp_server: task103 (X-1) - ...
e041cae270 modules/mcp_server: task099 - ...

$ git -C godot status --short
?? uid_cache.bin                                      <- 本任务之前就在
```

**必须点名的遗留改动（铁律 9：别人的改动不要替他提交）**：
`godot-mcp/recovery/tasks/TASK-132.md`（本任务书）在上一轮执行期间出现，**不是我的文件**，
**已被本轮一并提交**（因为它就是本任务的输入，且不在禁止清单里；若决策者希望它保持未跟踪，
请从 `03692fd`/本轮提交中排除）。

---

## M. 提交与决策日志

* 决策日志：`DECISIONS.md`（追加 D176–D180，见该文件）。
* 交付提交：§L.1 的基线之上一条 `feat(godot-mcp): TASK-132 …`，
  只包含本任务的独占清单文件（见 §L 末的清单）。
* 报告自身在收尾时可能再被改一两次（补 git 状态），那将是**只改本报告**的 docs 提交。

---

## N. 遗留与待决（交给决策者，本任务不擅自扩大范围）

1. **pong 的结构性问题（新，TASK-131 没登记过）**：`PongGame.AutoServe = true`，
   而右挡板无人操作 ⇒ 每次得分后自动重发球，球径直飞出右侧 ⇒
   **约 12 秒内左侧 5:0 结束比赛**（`PONG_OVER`）。模型第一次看到可玩局面到终局之间
   只剩 1–5 步。**本任务不修**（属于游戏逻辑）。可选修法（供参考）：
   (a) 开局不让右侧一直漏球（右挡板加一个最简单的跟随）；(b) 降低 `WinScore` 之外的
   "单局时长"影响——例如把 `AutoServe` 关掉，让发球成为双方都要按的动作。
   **判定影响**：这使 pong 在当前配置下**结构性地难以**满足"≥8 步接受∧变化 ≥75%"。
2. **snake 的真缺陷未修**（TASK-131 已登记，本任务再次遇见并强化了证据）：
   第一帧就是结束画面、InputMap 无重开键。用户判据下它**只能判 INCONCLUSIVE**
   （缺的是"一个还没结束的局面"），而 TASK-131 的 P2/P3 口径下它是 FAIL——两个口径都对，
   区别是问的问题不同。
3. **模型固定点（新）**：PlayJev 在同一帧上会**无限重复同一动作**
   （tetris 的 `tetris_left` P≈0.58 连选 9 步；pong 的 `pong_right_down` P≈0.63 连选 9 步）。
   本任务按 TASK-132 §1.2 把这类证据标为 INCONCLUSIVE 并写明缺什么。
   若决策者希望把"模型锁死"本身当一个**可玩性**信号，需要单独定义口径
   （例如"连续 N 步同一动作即视为该后端的会话失效"）。
4. **`done` 这个选项的语义**：本回路从玩家候选里移除了它（§B.3）。
   如果门里的 `--agent` 探针仍保留 `done`，两者对同一个模型会给出不同行为——
   建议在下一批统一：**探针保留 `done`，玩家回路不保留**，并把这条写进
   `playtest_agent` 的模块文档（本任务只在自己的工具里记录了理由）。
5. **Jev 的策略性弱**：3 款里 Jev 从没选出过位置级战术动作（左右挡板/方向），
   它的答案多半是"像不像结束/静止"的整体判断（§F.1）。这是**未微调**的必然结果，
   如实报告；**不得**据此把判据降级为"只看文本状态"（用户已明确禁止）。
6. **读图分辨率边界**：demo 的缩略图（300 px 宽）看不出 24 px 的格子位移，
   所以本报告对"块移动一格"这类结论都补读了 **800×600 全尺寸原图**再写；
   HUD 小字类结论一律以状态字段为准。
7. **既存缺陷未修**：`--agent` 段的 `'ScriptedAgent' object has no attribute 'last_evidence'`
   （TASK-131 已登记；不影响 P1..P7 与模型玩家判据，但会让 `--agent` 段静默失效）。
8. **`runs/**` 被 `.gitignore` 忽略**（`.gitignore:43` = `godot-mcp/runs/`）：
   与 TASK-131 的 `runs/realinput/**` 同一惯例 —— 证据留在盘上、不进 git。
   报告里的每个数字都给了**绝对可定位的路径**，请按路径直接取用。
