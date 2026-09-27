# TASK-139 — 判据加固：窗口长度敏感性 + 合法拒绝识别，并在新口径下重跑 20×2

> 子代理**只读本文件**执行；报告写到 `recovery\reports\TASK-139-REPORT.md`，**返回值只给该路径 + 一行状态**。
> **严格单线程**：本任务期间**不得**再派子代理。
> **独占文件**：`tools/playtest_player.py`、`tools/playability_gate.py`、`tools/playability_controls.json`、`tools/tests/**`、
> `tools/playtest_artifact_index.py`、`runs/model-player/**`、`recovery/tasks/TEMPLATE-logic-feedback.md`、`DECISIONS.md`、`recovery/tasks/TASK-139.md`。
> **禁止触碰**：20 款正式工程的**逻辑**（本批**只测不改**；游戏侧阻塞留到下一批）、`projects/_exercises/neg_*` 与 `prefix_*`、
> `recovery/reports/TASK-136-REPORT.md` 的历史内容（**只可追加勘误**）、`F:\models\**`、两个 venv、8080/8081 服务、`.gitignore`、`recovery/tasks/README.md`。

---

## 0. 现状（一手，来自 TASK-138 与 ACCEPTANCE-TASK-137）

* **两窗已按实际达成帧数对齐**（TASK-138，defect ⑧）：残差从 `+87 / 3.61×` 降到 **脚本臂中位 +1（最大 6 帧）、模型臂 +1（最大 4 帧）**；
  `--window-frames` 仍 30，两尺子公式与 `playability_controls.json` 未改。
* **新口径下的分布（TASK-138 实测）**：
  * **脚本臂 20/20：`10 PASS / 0 baseline-only / 4 FAIL / 6 INCONCLUSIVE`**（旧 `9/1/4/6`）；
    翻转：`asteroids` baseline-only → PASS；`flappy`、`minesweeper` FAIL → INCONCLUSIVE。
  * **模型臂只复核了 3 款**（tetris/pong/asteroids）：`1/1/1` → **`1 PASS / 0 / 2 FAIL`**，**`pong` baseline-only → FAIL**（新 baseline 在步 8、11 失败）。
* **已独立验收**（`ACCEPTANCE-TASK-137.md`，`verdict = pass`，无 blocker）。
* **TASK-138 登记的遗留风险**：① **`asteroids` 的 verdict 对窗口长度敏感**（0–6 帧残差来自客户端轮询，无法把游戏钉在某一帧）；
  ② 其余 **17 款模型臂未在新口径下复核**；③ 3 款游戏侧硬阻塞仍未修（frogger / bomberman / flappy）。
* **另有一条已知判据缺陷**（TASK-136 §4.3/§12 登记）：**5 款游戏的"合法拒绝"未被判据识别**
  （`match3` / `minesweeper` / `pacman` / `sokoban` / `towerdefense`）——这会把"游戏按规则拒绝"错判成 FAIL。

---

## 1. 目标

### A. 窗口长度敏感性（针对遗留风险 ①，我判定必须做）
1. **声明式最小窗口长度**：在 `tools/playability_controls.json` 增加声明（例如 `model_player_window.min_frames`，给出取值依据），
   并在工具里**强制**：达成帧数低于该值 ⇒ 该判定标 **`WINDOW_TOO_SHORT`**（与 FAIL / `MODEL_*` 分开，不进 PASS）。
2. **敏感性矩阵**：对**同一份证据**用**至少两档窗口**（例如 `--window-frames 30` 与更长的另一档）重算，
   逐款给**两档下的 verdict**；任何**因窗口长度而翻转**的款标 **`SENSITIVE`**，并**点名具体是哪几步**受影响。
3. **`asteroids` 单独给出**：它在 TASK-138 里从 baseline-only 翻成 PASS —— 在更长窗口下**是否仍然 PASS**？给逐帧证据。

### B. 合法拒绝识别（针对已登记的判据缺陷）
4. 为那 5 款（`match3`/`minesweeper`/`pacman`/`sokoban`/`towerdefense`）**声明 `refusal_evidence`**（指名**游戏侧计数器/状态字段**，
   例如 `RejectedMoves`/`InvalidDir`/等价物；**必须从游戏自己导出的状态里读**，不许用模型自述）。
5. **规则边界**：合法拒绝**可以**让该步不算 FAIL，但**不得**让一款游戏凭"全在拒绝"拿到 PASS
   （必须有 ≥ 门槛的**真实推进**步；门槛写成声明式并给依据）。
6. **反向测试**：构造"**一边拒绝一边有真实推进**"与"**全在拒绝、零推进**"两种序列，
   前者应可 PASS（若推进达标），后者**必须**不是 PASS（给断言）。

### C. 在新口径下重跑 20×2（针对遗留风险 ②）
7. **脚本臂 20/20 + 模型臂 20/20**（`jev`；`playjev` 若预算允许就对 ≥8 款跑）全部在**新对齐口径**下重跑，
   逐款三态 + `steps.jsonl` + `demo.png`；并给**旧分布 vs 新分布**对照。
8. **产物清单**：用 `tools/playtest_artifact_index.py` 生成本批清单并 **`git add -f` 提交进仓**
   （`runs/**` 继续被忽略，`.gitignore` 不改）。
9. **必须 `read_image` 实看关键帧**（含全尺寸 800×600），**每条描述附可机检锚点**（TASK-138 新增的硬要求）。

### D. 记录
10. `DECISIONS.md` 追加本批条目（编号顺延）：最小窗口长度与 `SENSITIVE`/`WINDOW_TOO_SHORT` 的语义、合法拒绝的规则边界、
    新口径下的分布变化及原因。并在 `TEMPLATE-logic-feedback.md` 同步这三项。

---

## 2. 硬性约束（铁律）

1. **禁止一切 shell 重定向**（含 `> nul`、`1>NUL`、`2>&1`、`2>/dev/null`）；用 `-o`/`-OutFile`/Python 句柄；
   **沿用 TASK-136/138 的命令台账 + 扫描器**，报告里给本批自查数字。
2. **破坏性命令默认拒绝**；**只测不改** 20 款游戏逻辑。
3. 命令尽量**从 cmd 启动**；中文写盘乱码用 cmd/bash 或 Python UTF-8。
4. **禁止任何第三方端点**；只用 8080/8081；**串行**调用；`429/529` 按 `Retry-After` 退避。
5. **不得**杀服务、不得动两个 venv、不得动 `F:\models\**`、不得动 `_exercises/` 既有变体。
6. 端口：唯一高位端口（避开 9877/9888/9889/8080/8081）。
7. **不许放宽判据**：窗口加长、拒绝豁免都只许让判定**更公平**；任何因此掉出 PASS 的款**如实报**（翻转不许掩盖）。
8. 改引擎模块才触发两变体重建 + 十道门 + `accept_m1` + push；未改就写明"未触发"及依据。
9. 提交前 `git status --short` 只暂存自己独占清单里的文件。
10. **事实来源分级**；代码与文档冲突以代码为准并显式纠正。

---

## 3. 验收判据

| 编号 | 判据 |
|---|---|
| X1 | 最小窗口长度已声明（含依据）；低于阈值 ⇒ `WINDOW_TOO_SHORT`（与 FAIL/`MODEL_*` 分开、不进 PASS） |
| X2 | 敏感性矩阵：两档窗口下逐款 verdict + 翻转项 + 受影响步；`asteroids` 有专项结论 |
| X3 | 5 款 `refusal_evidence` 已声明（字段来自游戏导出状态），并给"如何取到" |
| X4 | 规则边界：全拒绝零推进**必不得 PASS**（有断言）；拒绝+真实推进可达 PASS |
| X5 | 脚本臂 20/20 + 模型臂 jev 20/20 新口径重跑完；旧/新分布对照；playjev 覆盖数如实报 |
| X6 | 产物清单已生成并 `git add -f` 入库（路径 + sha256 + 大小 + 生成命令） |
| X7 | 读图：关键帧实看（含全尺寸），**每条附可机检锚点** |
| X8 | `DECISIONS.md` + 模板同步本批三项 |
| X9 | 本批重定向自查数字（台账条数 / 命中 / 逐条原文） |
| X10 | 铁律逐条 + 文件所有权自查 + 两仓 `git log --oneline -5` 与 `git status --short`；未达标项如实报 |

---

## 4. 报告落点与返回值

* 报告：`F:\moonbit-hof-rs\godot-mcp\recovery\reports\TASK-139-REPORT.md`
* **返回值只给报告路径 + 一行状态**。