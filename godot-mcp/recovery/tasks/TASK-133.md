# TASK-133 — 修掉被新判据抓出的 4 个真缺陷，并用「模型玩家」判据给前后对比

> 子代理**只读本文件**执行；报告写到
> `F:\moonbit-hof-rs\godot-mcp\recovery\reports\TASK-133-REPORT.md`，**返回值只给该路径 + 一行状态**。
> **严格单线程**：本任务期间**不得**再派子代理。
> **独占文件**：`projects/snake/**`、`projects/game2048/**`、`projects/pong/**`、`projects/puzzlebobble/**` 的**游戏逻辑**（仅这 4 款）、
> `tools/playtest_player.py`、`tools/playability_gate.py`、`tools/playability_controls.json`、`runs/model-player/**`、`recovery/tasks/TASK-133.md`。
> **禁止触碰**：**其余 16 款正式工程**、`projects/_exercises/neg_*`、`F:\models\**`、`/opt/jev-venv`、`/opt/playjev-venv`、8080/8081 服务、`.gitignore`、`recovery/tasks/README.md`。

---

## 0. 已核实的缺陷（一手，来自 TASK-131 / TASK-132 的实测与证据）

| 游戏 | 缺陷（现象 → 根因 → 出处） |
|---|---|
| **snake** | **第一帧之前就 `GameOver`**：settle 快照 `GameOver=true / LoseReason=wall / Ticks=19`；游戏 stdout `SNAKE_WALL head=25,10 cols=25 rows=21 score=10 ticks=19`。根因：`ResetSnake` 把方向设 `(1,0)` 且 `_Process` 立刻步进 → **1.52 s（19×0.08s）自撞右墙**；且 **InputMap 无重开键**。→ TASK-132 的模型玩家回路在第一次模型调用前就被迫中止（INCONCLUSIVE）。 |
| **game2048** | **开局没种下棋子**：`GridString` 全 0、`TilesInUse=0`，四个方向均 `reason=no_change` → 不可玩（TASK-131 的新 P2/P3 翻红）。 |
| **pong** | **结构性问题**：`AutoServe` + **右挡板无人操作** → 约 **12 s 就以 5:0 结束**，模型可玩窗口只有 **1–5 步**；TASK-132 记 10 步里 **9 步"接受但相对零输入对照窗无差异"**（球自己在飞、球在飞时发球幂等）→ **FAIL**。 |
| **puzzlebobble** | **瞄准不可见**：`pb_left/right` 只改 `AngleIndex`，**像素差 0** → 玩家看不见自己在瞄准（TASK-131 仅 P2 翻红，当时**刻意未放宽判据**）。 |

**判据背景**：用户已把通关判据改为**「Jev 当模拟真人玩家」**（看图出操作 → 游戏接受输入 → **画面必须动态变化**；"出了操作 + 接受了输入 + 画面不动"即 **FAIL**），
子代理须**读前后图**判断动态变化**是否符合游戏逻辑**；**P1–P7 只用于"代码能跑"**。工具在 `tools/playtest_player.py`（TASK-132 交付，selftest 23 条全绿），
判定摘要进 `gate.json → model_player_criterion`。

---

## 1. 目标

### A. 修 4 款游戏的**真实缺陷**（只改这 4 款，改动必须有据可查）
1. **snake**：①起局**不再自动踩墙**（起局后无输入时应静止，或给一个明确的"等待开始"状态）；②**加重开键**（InputMap + 工程 README/`required_ui` 同步）；③保留原有可玩性（转向/吃食物/得分/自撞判负），且**不得**用"永远不死"之类方式掩盖。
2. **game2048**：起局**种下初始棋子**（至少 2 个），并保证四方向**确实可动**（给出移动证据）。
3. **pong**：让**模型有可玩的窗口**——例如改为**等玩家发球**（去掉/收敛 `AutoServe`）、或让对局在无人操作时不致 5:0 速死（**具体做法你定，但要写明理由与影响**）；球在飞时的 `serve` 幂等要么给可见反馈，要么从动作集里排除（并说明依据）。
4. **puzzlebobble**：加**可见的瞄准指示**（角度/方向可视化），使 `pb_left/right` 产生**可归因的像素变化**。

> **不得**为了让判据变绿而：放宽任何判据、伪造"玩法可观测"、把动作从动作集里偷偷删掉（除非按 §1.A.3 明写理由）。

### B. 用同一判据给**前后对比**（本任务的核心证据）
* 对上述 4 款 ×（`jev` 与 `playjev` 两后端）跑 `tools/playtest_player.py`，**修复前 vs 修复后**对照：
  * 修复前的判定直接引用 TASK-132 的 `runs/model-player/**` 结果（**不要重跑成"看起来更好"的版本**）；
  * 修复后写到 `runs/model-player/<game>/after-fix/`（你的证据根）；
  * 逐款给出**三态结论**（PASS / FAIL / INCONCLUSIVE）+ 逐步 `steps.jsonl` + `demo.png`；
  * **预期**：snake 从 INCONCLUSIVE 变为可评估（并按其真实表现给 PASS/FAIL）；game2048 / puzzlebobble / pong 的缺陷被消除后，**要么 PASS，要么给出仍然 FAIL 的确切原因**（不许含糊）。
* **必须读图**：`read_image` 实看修复前后的关键帧（含**全尺寸 800×600** 原图，缩略图不得作为"没变化"的依据），写出"看到了什么/变了什么/是否符合游戏逻辑"。

### C. 三条判据细化（TASK-132 §N 的遗留，按下列裁决执行）
1. **模型固定点独立口径（§N.3）**：`playtest_player.py` 与门新增**独立**结论 **`MODEL_FIXED_POINT`**——当模型连续 ≥3 步给出**同一动作且帧哈希相同**时，报"模型卡死"（**不算游戏缺陷**，也不许据此判游戏 PASS），在报告与 `gate.json` 里与 FAIL 分开记；**selftest 增加对应断言**。
2. **移除 `done`（§N.4）**：探针/动作词表里**统一移除 `done`**（实时游戏里它无意义），保留 `wait`；说明改动面。
3. **证据落点声明（§N.8 裁决）**：`runs/**` **继续被忽略**（符合 D165"大块可再生产物不入库"），但**报告必须给出关键产物的完整路径 + sha256**，使结论可复核。

---

## 2. 硬性约束（铁律）

1. **禁止一切 shell 重定向**（`>`、`>>`、`*>`、`2>&1`、`> nul`、`1>NUL`）；用 `-o`/`-OutFile`/Python 句柄。
2. **破坏性命令默认拒绝**；**只改上述 4 款**，**不得**碰其余 16 款与 `_exercises/neg_*`。
3. 命令尽量**从 cmd 启动**；中文写盘乱码用 cmd/bash 或 Python UTF-8。
4. **禁止任何第三方端点**；只用 8080/8081 本机服务；**串行**调用；`429/529` 按 `Retry-After` 退避。
5. **不得**杀服务、不得动两个 venv、不得动 `F:\models\**`。
6. 端口：唯一高位端口（避开 9877/9888/9889/8080/8081）。
7. 改**游戏逻辑**不需要重建引擎；若确实改了 `godot/modules/mcp_server/` 则必须两变体重建 + 十道门全绿 + `accept_m1 22/22` + push（并写明依据）。
8. 提交前 `git status --short` 确认**只暂存自己独占清单里的文件**；别人的遗留改动**不要替他提交**，点名留给决策者。
9. 每款修完必须跑 **`dotnet build`** 确认 0 失败，并跑**TASK-116 的 P1–P7**（"代码能跑"口径）确认没有把别的东西弄坏。

---

## 3. 验收判据

| 编号 | 判据 |
|---|---|
| Z1 | snake：起局不再自动踩墙（给出起局 N 秒无输入的 `Ticks/GameOver` 证据）+ 重开键可用（InputMap ↔ README/`required_ui` 一致） |
| Z2 | game2048：起局有 ≥2 个棋子，四方向**确实可动**（给移动前后状态/像素证据） |
| Z3 | pong：模型可玩窗口显著变长（给出步数/时间证据），且 `serve` 不再是"无可见反馈"的死动作（或已按理由移出动作集） |
| Z4 | puzzlebobble：瞄准产生**可归因像素变化**（给前后帧 + 像素差） |
| Z5 | 4 款 × 2 后端 after-fix 跑完，**三态结论**逐款给全 + `steps.jsonl` + `demo.png` |
| Z6 | 修复前结果**引用 TASK-132 既有证据**（不是重跑出来的更好版本），前后对照逐项列清 |
| Z7 | 读图：修复前后关键帧用 `read_image` 实看（含全尺寸原图），逐帧表 + "是否符合游戏逻辑"的推理 |
| Z8 | `MODEL_FIXED_POINT` 已实现并与 FAIL 分开记；selftest 覆盖；`done` 已移除 |
| Z9 | 4 款 `dotnet build` 0 失败；P1–P7 未被弄坏（逐款给结果） |
| Z10 | 铁律 + 文件所有权自查 + 两仓 `git log --oneline -5` 与 `git status --short`；关键产物**路径 + sha256** 已列 |

---

## 4. 报告落点与返回值

* 报告：`F:\moonbit-hof-rs\godot-mcp\recovery\reports\TASK-133-REPORT.md`
  （含：4 款缺陷的根因与修法、前后对照表、逐帧读图表、"仍 FAIL 的确切原因"、判据细化、Z1–Z10 逐条证据、遗留与待决）。
* **返回值只给报告路径 + 一行状态**；跑不完就如实报告做到哪一款/哪一步，不要写"应该可以"。
