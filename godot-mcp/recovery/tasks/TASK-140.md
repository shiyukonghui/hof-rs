# TASK-140 — 判据可靠性（跨轮可复现 + `UNSTABLE`）与 4 款游戏侧缺陷修复

> 子代理**只读本文件**执行；报告写到 `recovery\reports\TASK-140-REPORT.md`，**返回值只给该路径 + 一行状态**。
> **严格单线程**：本任务期间**不得**再派子代理。
> **独占文件**：`tools/playtest_player.py`、`tools/playability_gate.py`、`tools/playability_controls.json`、`tools/tests/**`、
> `tools/playtest_artifact_index.py`、`runs/model-player/**`、`recovery/tasks/TEMPLATE-logic-feedback.md`、`DECISIONS.md`、
> **`projects/asteroids/**`、`projects/frogger/**`、`projects/bomberman/**`、`projects/flappy/**`（**仅这 4 款的游戏逻辑**）**、`recovery/tasks/TASK-140.md`。
> **禁止触碰**：其余 **16 款**正式工程、`projects/_exercises/neg_*` 与 `prefix_*`、`recovery/reports/TASK-136/137/138/139*` 的历史内容（只可追加勘误）、
> `F:\models\**`、`/opt/jev-venv`、`/opt/playjev-venv`、8080/8081 服务、`.gitignore`、`recovery/tasks/README.md`。

---

## 0. 现状（一手，来自 TASK-139 + ACCEPTANCE-TASK-137）

* 判据：用户口径「**Jev 当模拟真人玩家**：看图出操作 → 游戏接受 → **画面必须动态变化**；"出了操作+接受输入+画面不动"= **FAIL**」；
  **strict 余量是 PASS 默认**；仅 baseline 通过者写 `PASS(baseline only)` 且不计入；`MODEL_FIXED_POINT`/`MODEL_NO_PROGRESS`/`WINDOW_TOO_SHORT` 均**不进 PASS**；
  脚本臂（`--player scripted`）与模型臂并列，用来把"游戏问题"与"模型问题"分开。
* TASK-139 实测分布（两档窗口、je v 20×2、playjev 10 款，报告 `TASK-139-REPORT.md`）：
  脚本 **w30 `15/1/0/4`、w90 `15/0/1/4`**；模型 **w30 `2/0/3/15`、w90 `1/1/2/16`**；playjev `3/0/1/6`。
  敏感性：脚本 3 款（breakout/platformer/pong）、模型 3 款（asteroids/pong/spaceinvaders）标 `SENSITIVE`。
* **TASK-139 的两条关键发现（本任务的直接依据）**：
  1. **`w30` 的 verdict 跨轮不可复现**：三轮完整 w30 探针里 5 款有 **4 款翻档**（同命令、同代码；机制 = 实测帧跨度抖动 + `ack_result` 偶发缺失）。
     **`w90` 两轮在同样 5 款上逐款一致**。→ 报告 §A.4 / DECISIONS D204 / 模板 §1.2c 要求"引用 verdict 必须同时说明档位与轮次"。
  2. **`asteroids` 真实游戏缺陷**：长窗口下撞击后**飞船不重生**，连续 7 步 `pixel_diff=0`，
     `016_05_after`/`022_07_after`/`037_12_after` 三帧 **sha256 完全相同**（`certutil` 独立复核）。→ 登记未修，交本批。
* 其它登记未修的游戏侧缺陷：**frogger**（出生点上方有车 + 按住重复迈步 ⇒ **一次注入连丢三条命**）、
  **bomberman**（`AutoClock=0` ⇒ `Detonations` 恒 0；**已放置的炸弹在画面上不可见**）、
  **flappy**（`AutoRun=false` ⇒ `FrameCount 0`；`AutoRun=true` 实测更差，因对照窗在注入前采）。
* 已登记的判据加固：`refusal_evidence` 5 款已声明（`RejectedMoves`/`InputRejectedSwaps`/`InputRejectedCursorActions`/`RejectedSteps`/`InputRejectedPlaces`），
  边界 `min_real_progress_steps=4`，"全拒绝零推进必不得 PASS" 已在真实数据上触发过一次。

---

## 1. 目标

### A. 判据可靠性：把"跨轮可复现"变成 PASS 的必要条件（**最高优先**）
1. **声明报告档位**：在 `tools/playability_controls.json` 声明 **`model_player_window.reporting_frames`**（给依据；建议 **90**，理由：w30 跨轮不稳、w90 两轮一致），
   低于该档的 verdict **不得**作为 PASS 依据（可报告为参考）。
2. **新增 `UNSTABLE` 判决**：同一款、同一档位、**≥2 轮独立完整运行**，若 verdict（含 PASS/baseline-only/FAIL/`MODEL_*`/`WINDOW_TOO_SHORT`）**不一致** ⇒ 标 **`UNSTABLE`**，
   **不计入 PASS**，并**列出不一致的轮次与分歧点**（哪一步、哪个判据项）。
3. **每处引用的 verdict 必须带「档位 + 轮次」**（写进工具输出、`player.json`、`gate.json` 与模板）。
4. **在报告档位下重跑 ≥2 轮**：脚本臂 20×2、模型臂 jev 20×2（playjev 预算允许就 ≥10 款），
   给**逐款两轮对照表** + `UNSTABLE` 名单 + 新分布。
5. 若某款两轮一致但**仍受窗口长度影响**（TASK-139 的 `SENSITIVE`），**同时标出**，不要用"两轮一致"掩盖敏感性。

### B. 修 4 款游戏侧缺陷（**允许改这 4 款的逻辑**；每处给修前→修后证据 + `dotnet build` 0 失败 + P1–P7 未被弄坏）
1. **asteroids**：**死亡后必须重生**（或给明确的结束态 + 重开键，二者选一并写明理由），使"撞击后连续 7 步零变化"消失。
2. **frogger**：出生点不能被车压住；**一次按键不得连丢多条命**（按住重复步进要收敛到合理频率或加冷却）；给出"单次注入只走 1 步 / 只丢 ≤1 命"的实测证据。
3. **bomberman**：**已放置的炸弹必须可见**（画面元素或状态可归因）；`AutoClock` 取舍写明（修前状态：`Detonations` 恒 0）。
4. **flappy**：让**对照窗与动作窗都能在"游戏运行中"成立**（修前 `AutoRun=true` 失败的原因是**对照窗在注入前采** →
   应把**对照窗与动作窗都放在同一"世界运行"背景下**，而不是把游戏关掉）；给出修后两窗都有效的证据。
5. 每款修后：**脚本臂**（游戏侧）在该款上从 FAIL/INCONCLUSIVE → PASS 或给出**仍然不 PASS 的确切原因**。

### C. 重跑与证据
6. 报告档位下重跑受影响款 + （预算允许）全 20 款；逐款三态 + `steps.jsonl` + `demo.png`。
7. **必须 `read_image` 实看关键帧**（含全尺寸 800×600），**每条描述附可机检锚点**。
8. 产物清单用 `tools/playtest_artifact_index.py` 生成并 **`git add -f` 入库**。

### D. 记录
9. `DECISIONS.md` 追加（编号顺延）：报告档位与 `UNSTABLE` 语义、4 款修法与影响、任何翻转/敏感性。
10. `TEMPLATE-logic-feedback.md` 同步："verdict 必须带档位+轮次"、"`UNSTABLE` 不进 PASS"、"两轮一致不等于不敏感"。

---

## 2. 硬性约束（铁律）

1. **禁止一切 shell 重定向**（含 `> nul`、`1>NUL`、`2>&1`、`2>/dev/null`）；用 `-o`/`-OutFile`/Python 句柄；沿用命令台账 + 扫描器并给本批自查数字。
2. **破坏性命令默认拒绝**；**只改这 4 款**，其余 16 款与 `_exercises/` 既有变体禁触。
3. 命令尽量**从 cmd 启动**；中文写盘乱码用 cmd/bash 或 Python UTF-8。
4. **禁止任何第三方端点**；只用 8080/8081；**串行**调用；`429/529` 按 `Retry-After` 退避。
5. **不得**杀服务、不得动两个 venv、不得动 `F:\models\**`。
6. 端口：**唯一高位端口**；w30/w90（或两轮）探针**必须用不同端口**（TASK-139 曾因共用端口互杀）。
7. **不许放宽判据**：`UNSTABLE` 只能**拿掉** PASS；任何为让某款 PASS 的改动必须走可开关变体 + 逐字证据。
8. 改引擎模块才触发两变体重建 + 十道门 + `accept_m1` + push；未改就写明"未触发"及依据。
9. 提交前 `git status --short` 只暂存自己独占清单的文件（**逐文件暂存**，勿 `git add` 整个目录）；别人的未跟踪文件不代提交。
10. **事实来源分级**；代码与文档冲突以代码为准并显式纠正。**未达标项如实报**。

---

## 3. 验收判据

| 编号 | 判据 |
|---|---|
| Y1 | `reporting_frames` 已声明（含依据）；低于该档的 verdict 不得作 PASS 依据 |
| Y2 | `UNSTABLE` 已实现：两轮不一致 ⇒ 标 `UNSTABLE`、不进 PASS、列出分歧点；并有测试/实测触发 |
| Y3 | 每处 verdict 带「档位 + 轮次」（工具输出、`player.json`、`gate.json`、模板） |
| Y4 | 报告档位下 ≥2 轮重跑：逐款两轮对照表 + `UNSTABLE` 名单 + 新分布（脚本 + jev；playjev 覆盖数如实报） |
| Y5 | `SENSITIVE` 仍未掩盖（与 `UNSTABLE` 并列标出） |
| Y6 | asteroids 重生缺陷已修（给修前 7 步零变化 vs 修后证据） |
| Y7 | frogger 单次注入 ≤1 步/≤1 命（给证据）；bomberman 炸弹可见（给证据）；flappy 两窗都在"世界运行"下成立（给证据） |
| Y8 | 4 款 `dotnet build` 0 失败；P1–P7 未被弄坏（逐款给结果） |
| Y9 | 读图实看（含全尺寸）+ 每条附可机检锚点；产物清单已 `git add -f` 入库 |
| Y10 | `DECISIONS.md` + 模板同步；本批重定向自查数字；铁律/wonership 自查；两仓 git 状态；未达标项如实报 |

---

## 4. 报告落点与返回值

* 报告：`F:\moonbit-hof-rs\godot-mcp\recovery\reports\TASK-140-REPORT.md`
* **返回值只给报告路径 + 一行状态**。