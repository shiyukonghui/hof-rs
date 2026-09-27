# TASK-128 — 用已部署的 NeoHorse-Jev 跑模型判定基线并标定阈值（20 款正样本 vs 修复前负样本）

> 子代理**只读本文件**执行；完成后报告写到
> `F:\moonbit-hof-rs\godot-mcp\recovery\reports\TASK-128-REPORT.md`，**返回值只给该路径 + 一行状态**。
> 自包含。**全程本地调用已部署的服务；禁止把截图发往任何第三方端点。**
> 同期另有子代理在部署 PlayJev（TASK-127，独立 venv `/opt/playjev-venv`、端口 8081）——
> **不要碰它的 venv/端口/文件**；两边会共用同一块 GPU，注意显存与延迟影响（见 §4.5）。

---

## 0. 已核实事实（不必再查，直接用）

* **Jev 服务正在运行**（detached，WSL 内 PID 730）：`http://127.0.0.1:8080`，
  `GET /health` → `{"status":"ready","model":"NeoHorse-Jev-4B","input_modalities":["text","image"]}`，
  WSL 内与 Windows 宿主都通；日志 `runs/playability/jev-serve-detached-*.log`；**常驻显存约 13.3 GB / 24 GB**。
* 权重：`F:\models\NeoHorse-Jev-4B`（73 文件 / 9,145,375,991 B，**70/70 SHA256 全绿**）。
* 环境：WSL2 Ubuntu 26.04、venv `/opt/jev-venv`（Python 3.12.13）、`torch 2.8.0+cu128`（GPU 实测可用）、
  `transformers 5.17.0`、`triton 3.7.1`、`flash-linear-attention 0.5.2`。
* **模型协议（关键）**：Jev **不是 chat LM、无 OpenAI 端点**。可用端点只有
  `POST /v1/decision`、`POST /v1/systemone`、`GET /health`（**`/v1/models` 不提供**）。
* **我们已实现 `--agent=jev`**（TASK-124，见 `recovery/reports/TASK-124-REPORT.md`）：typed questions
  （动作=`choice`、不变量=`noul`、损坏度=`score` 有序 5 级）、`answers.*` 映射回动作、probabilities/confidence/usage 入证据、
  `429/529` 按 `Retry-After` 退避、未配置/不通则降级 `wait`。
  **⚠️ 重要更正（TASK-125 实测）**：`--agent=jev --probe` **不是有效调用**；`--probe` / `--probe-jev`
  **只打内置哑服务，不会访问真实服务**。要打真实服务必须用**有文档的**路径（见 §2.1）。
* 阈值文件 `tools/playability_controls.json` 已有 `agent_thresholds`
  （`noul_min_p_true=0.5`、`score_max_expected=2.5`、`uncalibrated:true`），门侧 `load_agent_thresholds()`
  会把 `threshold_verdict` 记进 `gate["agent"]`。
* 厂商明确：概率**未校准**（NLL/Brier/ECE 未报告）→ **阈值必须由我们自己的正负样本得出**，这正是本任务的核心。
* 网络现实：Windows 侧 GitHub 可达、**HuggingFace 不可达**；**WSL 内 GitHub 不可达**。

---

## 1. 目标

1. 让门能用**有文档的命令**真正打到本地 Jev 服务（补上真实服务入口，别只靠内置哑服务）。
2. 在**正样本**（20 款修好版）与**负样本**（修复前版本）上采集**模型原始信号**。
3. 据此**标定可玩性阈值**并更新 `agent_thresholds`；给出**分离度分析**与**未校准声明**。
4. 产出可重跑的命令与证据；把"模型判定"与既有 **P1–P6 机检判据**并列对照（谁抓到、谁漏掉）。

---

## 2. 步骤

### 2.1 打通真实服务入口（先做，且要留证）
* 查 `tools/playtest_agent.py --help` 与 `tools/playability_gate.py --help` 现状；
  若**没有**"用 `--agent=jev` 打真实服务"的文档化入口，就**补一个小改动**：
  例如 `--agent=jev` 配合 `PLAYTEST_BASE_URL=http://127.0.0.1:8080` 时走真实服务，
  **`--probe*` 保持只打内置哑服务的语义不变**（不要破坏 TASK-124 的自测）。
* **留证**：给出一次真实调用（游戏或样例状态）的**请求与响应逐字记录**，以及服务端日志对应行；
  明确写出"这次确实打到了 8080，而不是哑服务"（例如响应里的 `model`/`usage`/`X-NeoHorse-*` 头）。

### 2.2 正样本（20 款修好版）
* 运行 `tools/playability_gate.py` 带 `--agent=jev`（按 §2.1 的真实服务入口），覆盖**全部 20 款**
  （`projects/` 或 `dist/exe/` 均可，**以你能稳定驱动的那套为准并写明**）。
* 每款保留：每个问题的**原始概率/confidence/abstain**、所用 `state` 文本（或哈希+样例）、截图指针、
  以及门的 P1–P6 结论，落 `runs/playability/agent-jev/<game>/…`（`runs/` 不入库但要给盘上路径）。

### 2.3 负样本（修复前版本）
* 先确认 `F:\moonbit-hof-rs\godot-mcp\dist\exe-task109-pre-fix\exe\<game>\<game>.exe` **是否存在**
  （那是 TASK-109 导出的修复前版本：`PollInput=false` → **按键无反应**，天然负样本）。
* 若存在：用同一套门与同样的 `state` 构造跑**同一批游戏**（至少 8–10 款，覆盖不同玩法）；
  **必须记录**"这批负样本的失效方式是输入无响应"，并说明哪些判据（P2 vs 模型 noul/score）分别抓到它。
* 若**不存在或驱动不起来**：**如实报告并停下该分支**，改用你能构造的负样本（例如人为把已修好版本
  的 `PollInput` 改回 false 的**副本**，副本放 `projects/_exercises/`，**不要改原件**），并在报告里声明构造方式。

### 2.4 分离度与阈值标定
* 对每个问题（动作/noul/score）给出正负两类的分布：`n`、`min`、`max`、`median`、简单的可分性指标
  （如"正类 min 与负类 max 是否重叠"、阈值扫描下的错分计数）。**不需要**实现完整 ROC/AUC 框架，但**不许只给平均值**。
* 提出阈值并与现有默认（`0.5` / `2.5`）对比：**说明选了哪个、为什么、错分会落在哪**；
  在报告与 `tools/playability_controls.json` 的注释里**保留"未校准"声明**并注明**样本量很小（20 正 / N 负）**这一局限。
* 明确写下**模型判定的语义边界**：它判的是"**这个 state/画面是否像可玩**"，**不等于**"游戏逻辑正确"或"好玩"；
  厂商亦警告概率未校准、多问题不共享前向。

### 2.5 一致性与冲突分析
* 逐款对照：**模型判定** vs **P1–P6 机检** vs **人类复核已知结论**
  （TASK-116 的修复前 1/20、修复后 20/20；`PLAYABILITY-REPORT.md`、`PLAYABILITY-DEFECTS.md`）。
* **冲突项逐条登记**：谁抓到谁漏掉、可能原因（例如模型只看 state 文本、机检看像素/进程）、
  以及"模型判定为不可玩"的每一款是否真有问题。**不得**把冲突抹平。

---

## 3. 硬性约束（铁律）

1. **禁止一切 shell 重定向**（`>`、`>>`、`*>`、`2>&1`、`> nul`）；用 `-o` / `-OutFile` / Python。
2. **破坏性命令默认拒绝**；**不得改 `projects/` 里 20 款正式工程的逻辑**（要构造负样本就复制到 `_exercises/`）。
3. 命令尽量**从 cmd 启动**；中文写盘乱码用 cmd/bash 或 Python UTF-8。
4. **不得**杀 Jev 服务、不得动 `/opt/jev-venv`、不得动 `F:\models\NeoHorse-Jev-4B`、不得动 TASK-127 的 venv/端口。
5. **禁止任何第三方端点**（图像或状态都不外发）。
6. 端口：门的会话用唯一高位端口，跑前查占用；**避开 9877/9888/9889、避开 8080/8081（模型服务）**。
7. 串行调用模型（服务**无动态批处理**）；对 `429/529` 按 `Retry-After` 退避并记数。
8. 改引擎模块才触发两变体重建 + 十道门 + `accept_m1` + push；**未改就写明"未触发"及依据**。

---

## 4. 验收判据（报告逐条给证据）

| 编号 | 判据 |
|---|---|
| A1 | 有**文档化**的真实服务入口，且给出"确实打到 8080"的逐字证据 |
| A2 | 20 款正样本全部跑完，逐款逐问原始概率/abstain/confidence 落盘（给路径与计数） |
| A3 | 负样本跑完（或如实报告为何跑不了 + 构造的替代负样本） |
| A4 | 分离度分析含 `n/min/max/median` 与阈值扫描错分，**不是只给平均值** |
| A5 | 阈值已更新进 `tools/playability_controls.json`，理由与局限写明，**"未校准"声明保留** |
| A6 | 模型判定 vs 机检 vs 已知结论的**冲突项逐条登记**（含"模型漏掉/误报"的具体案例） |
| A7 | 给出**可重跑命令**（逐条，含环境变量与端口） |
| A8 | 明写铁律：无重定向、无破坏性命令、未改正式工程逻辑、未动模型服务/venv/权重；两仓 `git log --oneline -5` 与 `status` |
| A9 | 显存/延迟观察（与 TASK-127 并行时是否互相影响；有无 OOM 或明显变慢） |

---

## 5. 报告落点与返回值

* 报告：`F:\moonbit-hof-rs\godot-mcp\recovery\reports\TASK-128-REPORT.md`
  （含：真实服务入口的改动与留证、正负样本清单与原始信号路径、分离度与阈值标定、
  一致性/冲突分析、A1–A9 逐条证据、遗留与待决项）。
* **返回值只给报告路径 + 一行状态**。
* 跑不完就**如实报告跑到哪一款**，不要写"应该可以"。
