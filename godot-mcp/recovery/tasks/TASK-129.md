# TASK-129 — PlayJev 视觉判定接进试玩门 + 真负面样本标定（并修 Jev 侧的 token 估计与采样缺陷）

> 子代理**只读本文件**执行；报告写到
> `F:\moonbit-hof-rs\godot-mcp\recovery\reports\TASK-129-REPORT.md`，**返回值只给该路径 + 一行状态**。
> **本任务独占以下文件**（其他人不得改）：`tools/playability_gate.py`、`tools/playability_controls.json`、
> `tools/tools/`（如有）、`tools/playtest_agent.py`（仅在其内新增 playjev 相关行）、
> `projects/_exercises/neg_*`（你新建的负面变体目录）、`recovery/tasks/TASK-129.md`。
> **禁止触碰**：20 款正式工程 `projects/<game>/`、`F:\models\**`、`/opt/jev-venv`、`/opt/playjev-venv`、
> 8080/8081 上的服务进程、`recovery/reports/TASK-12{4..8}-REPORT.md`。
> 另：把 `recovery/tasks/TASK-12{4..9}.md` 一并提交（任务书要入库）。

---

## 0. 已核实事实（一手；不必再查）

### 0.1 服务（都在本机，均可直接用）
* **NeoHorse-Jev-4B**：`http://127.0.0.1:8080`，`/health` ready，文本强/视觉弱（`vision_finetuning:false`），**图像请求硬限制 1 图 1 问**；常驻显存约 13.3 GB。权重 `F:\models\NeoHorse-Jev-4B`（70/70 SHA256 全绿）。
* **PlayJev-0.8B**：`http://127.0.0.1:8081`，`/health` = `{"ok": true, "model": "playjev-0.8b", "two_frame": false}`，加载 14.0 s、显存 +3.6 GB；权重 `F:\models\PlayJev-0.8B`（2.08 GiB；`model.safetensors` sha256 `efe4d2c5…`、`tokenizer.json` `06b95093…`，与 HF LFS oid 逐字符相同）；Apache-2.0；基座 `Qwen/Qwen3.5-0.8B-Base`；`playjev_train.json` 里 **`freeze_vision:false`**（视觉塔确证参与训练）。
* 两台服务**共用一块 RTX 4090（24564 MiB）**；并行峰值实测 20493 MiB 无 OOM；Jev 延迟中位 0.909 s（冷启动最大 8.357 s）。**串行调用**（无动态批处理）。

### 0.2 已完成的实现
* `--agent=jev`（TASK-124，见 `TASK-124-REPORT.md`）：typed questions（动作 `choice`/不变量 `noul`/损坏度 `score`）、概率与 confidence 入证据、429/529 退避、未配置降级 wait。
* `--agent=playjev`（TASK-127，见 `TASK-127-REPORT.md`）：支持 **1 图 + N 问**；**自建六条 abstain 规则**（因为 `serve.py` **没有 `abstain` 字段**，且 `model.py:102` 的 `allowed_mass` 被 serve.py 丢弃）；`--abstain-min-confidence` 可在真实服务上构造出真 abstain。
* 门侧真实服务入口 `--base-url`、`--agent-state-budget`（TASK-128）。
* **TASK-127/128 实测纠正了任务书的两处二手事实**：`serve.py` 无 `abstain`；`state.frames` 的说法亦不成立——**以代码为准**。

### 0.3 TASK-128 的实测结论（本任务的前提）
* 正样本 20/20 款 P1–P6 全 PASS，58 次模型调用 0 错误；信号在 `runs\playability\agent-jev\<game>\agent.json`。
* **负样本**：修复前导出（路径实为 `dist\exe-task109-pre-fix\<game>\<game>.exe`，**不是** `…\exe-task109-pre-fix\exe\…`）20 款全跑完，**只有 16 款**门判 not_playable（P2/P5/P6 FAIL，失效方式确为 `PollInput=false`）；**breakout/snake/tetris 的修复前导出被判 playable**、pong 本就是例外 → 这 4 款**已从负类排除并逐条登记**。
* **标定结论：没有任何问句能干净分离**。`noul.responses_to_input` 是唯一有信号的维度（正中位 0.4555 / 负中位 0.1534，**有重叠**）；`playable_frame`/`no_render_failure` 几乎全重叠；**`score` 零分离度**（最优扫描仍 13/36 错）。联合最小 → `noul_min_p_true` 0.5→**0.25**、`score_max_expected` 维持 2.5，错分 3/36（先验 11/36）。`uncalibrated` 保持 true。
* **缺陷**：①门在 3 次调用里递**同一份 state** → 每款只有 **1 个独立模型观测**；②客户端 `jev_estimate_tokens` **低估服务侧 2.1–2.4 倍**（1018→2160、1791→4229），导致 15/20 款一开始被 HTTP 422 拒绝；③负类**只覆盖一种失效模式**（输入无响应）；④我们 836 张已捕获帧里**没有一张天然退化帧**（TASK-127 的负面帧是**派生**的）。
* PlayJev 侧初步锚点（TASK-127，6 样本）：**`playable` 有效**（黑屏/平色/内容缺失 P(yes)=0.202/0.200/0.203；真实帧 0.48–0.85），**`score` 方向反了**（黑屏 2.41 < 真实 snake 帧 3.97）。

---

## 1. 决策者已裁定（必须照此执行，不要另立方案）

* **D-A（Q1 权威度量）**：**"玩家拿到的产物"以导出 exe 为权威**；"我们修的代码"以工程树为准。二者冲突时**并列登记**，不得抹平。负类**只纳入导出产物确实失效的样本**（即那 16 款）。
* **D-B（Q2 采样）**：门必须**对同一款游戏采集 ≥3 个彼此独立的 state 观测**（例如：注入前 / 注入后 / 一段时间后的不同状态，且 state 必须哈希不同），否则**样本量按 1 计**并如实标注。
* **D-C（Q3 token 估计）**：修 `jev_estimate_tokens`——用**服务端 `usage` 实测**（已有 1334/648 等样本）标定一个**保守系数**，并在收到 `422` 时**自动减半预算重试**（有界次数、逐次留证）；**禁止静默截断**。
* **D-D（Q4 负类与真负面帧）**：在 `projects/_exercises/` 下**新建声明式负面变体**（复制现有工程，**绝不改 20 款正式工程**），覆盖**至少四种失效模式**，并为它们**采集真实退化帧**：
  1. **输入断开**（`PollInput=false`）——已可用（修复前导出）；
  2. **不渲染/黑屏**（例如主场景不实例化可视节点，或渲染目标不绘制）；
  3. **冻结**（帧不推进：时钟/`_Process` 被停）；
  4. **UI/控件缺失**（HUD 或关键控件被移走）。
  每种变体要写清**构造方式、期望被哪条判据抓到**，并在报告里给出真实帧的落盘路径与哈希。
* **D-E（score 维度）**：**`score` 撤出判定路径**，仅作**显式标注"未校准、本版方向可疑"的观察值**保留；可用**翻转图例顺序**做一个**声明式探针**（判断方向反转是否为措辞/图例顺序伪影），**该探针结果永不进判定**。

---

## 2. 交付物

### A. 修 Jev 侧两处缺陷（D-B、D-C）
* `--agent-state-budget` 之上的**多状态采样**：对每款至少 3 个 state（彼此不同、带 sha256 与来源说明），三次调用**必须都记录**（含 attempts/usage/概率）。
* `jev_estimate_tokens` 按实测标定 + `422` 自动减半重试（有界）。

### B. 声明式负面变体 + 真实退化帧（D-D）
* 至少四种失效模式的变体工程（`projects/_exercises/neg_*`），各自：
  * 能起（`--headless --quit-after` 退出码 0 或说明为何不能）；
  * 通过门的 MCP 端点采集**真实整窗帧**（复用既有采集路径），帧存 `runs/playability/negatives/<mode>/frames/*.png`；
  * 给出每张帧的**预期标签**（应由哪条判据/哪个模型维度抓到）。

### C. PlayJev 视觉判定接进试玩门（**本任务核心**）
* 门新增 `--agent=playjev`（或 `--visual-agent=playjev`）路径：**1 图 + N 问**，其中：
  * 动作 = `choice`；
  * **可玩性 = `noul`（`playable`）**；
  * **`score` 不进判定**（按 D-E：仅记录为观察值 + 标注"方向可疑"）。
* `tools/playability_controls.json` 增加**独立于 Jev 的** `playjev_thresholds`（含 `uncalibrated:true`、样本量与局限说明），门把结果记进 `gate["playjev"]`（与 `gate["agent"]` 并列）。
* 在**20 款正样本**与**四种负样本（真实帧）**上跑，给出：
  * 每款的 PlayJev 逐问原始概率/confidence/abstain；
  * **真实负面帧**上的 `playable` 分布 → **用真负面标定阈值**（并与 TASK-127 的派生帧锚点对比）；
  * `score` 观察值与**翻转图例探针**结果（声明式，不进判定）。

### D. 一致性与冲突（沿用 TASK-128 的口径，不得抹平）
* 逐款对照：**PlayJev 视觉判定** vs **Jev 状态判定** vs **P1–P6 机检** vs **TASK-116 历史结论**；冲突项逐条登记（谁抓到、谁漏掉、可能原因）。
* 明确写出**模型判定的语义边界**：它判"这一帧/这一状态像不像可玩"，**不等于**游戏逻辑正确或好玩。

### E. 收尾
* 任务书入库：提交 `recovery/tasks/TASK-12{4..9}.md`（含本文件）。
* 报告含两仓 `git log --oneline -5` 与 `git status --short`；提交前用 `git status --short` 确认**只暂存自己独占清单里的文件**（**发现别人的改动不要替他提交**，点名留给对方）。
* `DECISIONS.md` 追加一条（记录 D-A..D-E 与本次实测结论）。

---

## 3. 硬性约束（铁律）

1. **禁止一切 shell 重定向**（`>`、`>>`、`*>`、`2>&1`、`> nul`、`1>NUL`）；用 `-o` / `-OutFile` / Python。
2. **破坏性命令默认拒绝**；**禁止改 20 款正式工程的逻辑**（负面变体只能复制到 `_exercises/`）。
3. 命令尽量**从 cmd 启动**；中文写盘乱码用 cmd/bash 或 Python UTF-8。
4. **禁止任何第三方端点**（截图/状态都不外发）；只用 8080/8081 本机服务。
5. **不得**杀 8080/8081 的服务、不得动 `/opt/jev-venv`、`/opt/playjev-venv`、`F:\models\**`。
6. 端口：会话用唯一高位端口（避开 9877/9888/9889/8080/8081），跑前查占用。
7. **串行**调用模型；`429/529` 按 `Retry-After` 退避并记数；注意显存（两台服务已占约 17 GB）。
8. 改引擎模块才触发两变体重建 + 十道门 + `accept_m1` + push；**未改就写明"未触发"及依据**。
9. 任务书里的事实**标来源等级**；**代码与任务书冲突时以代码为准并显式纠正**。

---

## 4. 验收判据（报告逐条给证据）

| 编号 | 判据 |
|---|---|
| V1 | 多状态采样：每款 ≥3 个**哈希不同**的 state，三次调用全留证（D-B） |
| V2 | token 估计按 `usage` 标定 + `422` 自动减半重试有界（给标定数据与一次真实重试记录）（D-C） |
| V3 | 四种失效模式的负面变体建好，且**采到真实整窗退化帧**（给路径、哈希、预期标签）（D-D） |
| V4 | 门的 PlayJev 路径可用（1 图 + N 问），`score` 不在判定路径；`playjev_thresholds` 有 `uncalibrated` 与局限说明（D-E） |
| V5 | 20 款正样本 + 四类负样本全部跑完（或如实说明跑不了的部分） |
| V6 | **用真负面帧标定** `playable` 阈值（给分布与阈值扫描错分，并与派生帧锚点对比） |
| V7 | 翻转图例探针有结果且**明确标注不进判定** |
| V8 | 冲突逐条登记（PlayJev vs Jev vs 机检 vs TASK-116），含"模型误报/漏报"具体案例 |
| V9 | 可重跑命令（逐条，含环境变量/端口/预算参数） |
| V10 | 铁律遵守 + 文件所有权核对（只暂存自己的文件）+ 任务书已入库 |

---

## 5. 报告落点与返回值

* 报告：`F:\moonbit-hof-rs\godot-mcp\recovery\reports\TASK-129-REPORT.md`
* **返回值只给报告路径 + 一行状态**；跑不完就**如实报告跑到哪一款**，不要写"应该可以"。
