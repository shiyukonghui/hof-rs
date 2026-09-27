# TASK-138 — 修掉独立验收（ACCEPTANCE-TASK-137）点名的 7 条 defect + 3 条加固，并重跑受影响判定

> 子代理**只读本文件**执行；报告写到 `recovery\reports\TASK-138-REPORT.md`，**返回值只给该路径 + 一行状态**。
> **严格单线程**：本任务期间**不得**再派子代理。
> **独占文件**：`tools/playtest_player.py`、`tools/playability_gate.py`、`tools/playability_controls.json`、`tools/tests/**`、
> `tools/playtest_artifact_index.py`（你新建，若需要）、`runs/model-player/**`、`runs/accept-137/**`（**只读参考，勿改**）、
> `recovery/reports/TASK-136-REPORT.md`（**仅新增"勘误"小节**）、`recovery/reports/ERRATA.md`（若你决定集中放勘误）、
> `recovery/tasks/TEMPLATE-logic-feedback.md`、`DECISIONS.md`、`recovery/tasks/TASK-138.md`。
> **禁止触碰**：20 款正式工程的**逻辑**（本批**只测不改**，除非某改动是"为了修正测量"且**必须**在游戏侧——若真需要，**先说明**）、
> `projects/_exercises/neg_*` 与 `prefix_*`、`F:\models\**`、`/opt/jev-venv`、`/opt/playjev-venv`、8080/8081 服务、`.gitignore`、`recovery/tasks/README.md`。

---

## 0. 验收结论（一手）：`verdict = pass`，但有 7 条 defect 与 2 条风险

**已独立的核验（**不要重做**，直接引用）**：strict 真为默认（`playability_controls.json:312`、`playtest_player.py:211-214`、`playability_gate.py:2550-2578`）；
`PASS(baseline only)` 真被排除计数（`playtest_player.py:785-793`、`gate:2797-2828`）；ack 用游戏自己的 `Input.is_action_pressed`、变化用对照窗；
6 组反例 + 2304 格穷举通过；**两条臂分布：模型 1 PASS/1 baseline-only/3 FAIL/15 INCONCLUSIVE，脚本 9/1/4/6**；
独立重跑 snake/tetris 一致（pong 9 vs 10 步抖动）；11 张图实读；台账重扫 111/3 命中；复现 3 项游戏侧阻塞；`3ede4f2..HEAD` 只改 platformer。

### 要修的 7 条 defect（报告中编号为它的 ①②③④⑤⑥⑦）
1. **platformer 帧描述错误（major）**：报告 §7 第 9 行实际是 `TILE 3,27`，报告写 `TILE 4,27` 且称"右移两格"。→ **勘误**，并**在模板里加"读图描述必须带可机检锚点"**（见 §1.C）。
2. **`t136_redirect_scan.json` 的 sha256 与磁盘不符**（报告写 `42bbab3f…`，实测 `3ac18ad7…`）→ 更正为实测值，并写明**它是哪个时刻的产物**。
3. **台账拆分 16/95 实为 17/94**（包装器上线前后）→ 更正并给可复算口径。
4. **"截至 111 条"的台账哈希不可核**、截点后还含 `pytest`/`selftest` → 给出**可复算的定界方式**（例如：提交台账文件本身 + 行数与末行时间戳 + 全文件 sha256）。
5. **首版报告哈希自指不可核** → 改为**提交报告本身**（已提交）并给出"内容哈希在写入后不可自指"的说明，不再声称可核。
6. **§4.1 platformer 的 strict 列填错**（顶层 verdict 实为 INCONCLUSIVE）→ 更正该单元格。
7. **§1.2 举例错**：把 platformer 当 `PASS(baseline only)` 的例子，真正的例子是 **pong / asteroids** → 更正。

### 要处理的 2 条风险（我（决策者）判定其中第 1 条**必须修**）
8. **两窗帧数不相等（必须修）**：动作窗实测比对照窗多 **2.5–3.7×** 帧（`achieved` 中位 `138 vs 51`、`119 vs 33`；`target_delta` 都是 30）。
   工具里"两窗同帧长"的注释**实测不成立**。→ **把两窗做成真正同帧数**（按**实际达成的帧数**对齐：取两窗较小者，或补采/裁到相等），
   并**重跑受影响的判定**（至少所有 PASS / `PASS(baseline only)` 的：`tetris`、`pong`、`asteroids` + 脚本臂 PASS 的那些），
   **报告有没有 verdict 翻转**（翻转就如实报，**不许**为了保绿调参）。
9. **`ack` 静默回退（必须修）**：`inj.ack_result` 缺失时回退到注入前的 `pre_ack` → 改为**缺失即判该步 INCONCLUSIVE**，并给测试。

---

## 1. 目标

### A. 修 defect ①–⑦（报告勘误，不改历史提交，新增勘误小节/文件）
* 在 `recovery/reports/TASK-136-REPORT.md` **新增"## 勘误（TASK-138）"小节**（或在 `ERRATA.md` 集中列，二者都要给**路径 + 行号**），逐条给出
  **原文 / 更正 / 更正依据（一手证据路径 + sha256）**。**不得**直接改写已完成的历史证据文件（只加勘误），除非某处是**纯笔误且你给出前后对照**。

### B. 修 defect ⑧（两窗同帧数）并重跑
* 实现"按**实际达成帧数**对齐"的两窗比较；把**目标帧数、达成帧数、对齐方式**逐步落盘。
* **重跑**：至少 `tetris`、`pong`、`asteroids`（模型臂）+ 脚本臂中所有 PASS 的款；逐款给**新旧 verdict 对照**与**是否翻转**。
* 若翻转 ⇒ **以新结论为准**并解释原因（新口径更严/更公平）。

### C. 修 defect ⑨（ack 回退）+ 读图锚点 + 产物清单
1. `ack`：`inj.ack_result` 缺失 ⇒ 该步 **INCONCLUSIVE**；补测试（含"缺失时不得用 pre_ack"的反例）。
2. **读图锚点（针对 defect ①）**：模板新增硬要求——**每一条逐帧读图描述必须附一个可机检锚点**
   （例如该步 `steps.jsonl` 里的 `TILE`/`Lives`/`Score`/`HeadX` 等**声明字段的实测值**），
   使"散文描述"能被**机器与状态逐字对照**；并在 `TASK-136-REPORT.md` 的 platformer 那一行补锚点。
3. **产物清单（针对 `runs/**` 被忽略）**：新增 `tools/playtest_artifact_index.py`（或等价），
   对**关键产物**（`player.json`、`steps.jsonl`、`gate.json`、`demo.png`、`filmstrip.png`）生成
   **路径 + sha256 + 大小 + 生成命令**的清单一**提交进仓**（例如 `runs/model-player/_index/ARTIFACTS-<批号>.json` + md），
   使结论在 `runs/**` 不入库的前提下**仍可事后核验**。

### D. 记录
* `DECISIONS.md` 追加本批条目（编号顺延）：两窗对齐口径、ack 回退禁止、读图锚点、产物清单机制、勘误清单。

---

## 2. 硬性约束（铁律）

1. **禁止一切 shell 重定向**（含 `> nul`、`1>NUL`、`2>&1`、`2>/dev/null`）；用 `-o`/`-OutFile`/Python 句柄；
   **沿用 TASK-136 的命令台账+扫描器**（`_scripts/t136_cmd.py` 等）并**在报告里给本批的自查数字**。
2. **破坏性命令默认拒绝**；**只测不改** 20 款游戏逻辑。
3. 命令尽量**从 cmd 启动**；中文写盘乱码用 cmd/bash 或 Python UTF-8。
4. **禁止任何第三方端点**；只用 8080/8081；**串行**调用；`429/529` 按 `Retry-After` 退避。
5. **不得**杀服务、不得动两个 venv、不得动 `F:\models\**`、不得动 `_exercises/` 既有变体。
6. 端口：唯一高位端口（避开 9877/9888/9889/8080/8081）。
7. **不许放宽判据**：两窗对齐只许让判定**更公平**（不得使 PASS 更容易）；若新口径让某款掉出 PASS，**如实报**。
8. 改引擎模块才触发两变体重建 + 十道门 + `accept_m1` + push；未改就写明"未触发"及依据。
9. 提交前 `git status --short` 只暂存自己独占清单里的文件。
10. **必须 `read_image` 实看关键帧**（含全尺寸 800×600），且**每条描述附可机检锚点**（见 §1.C.2）。

---

## 3. 验收判据

| 编号 | 判据 |
|---|---|
| W1 | defect ①–⑦ 逐条给出「原文 / 更正 / 依据（路径 + sha256）」；platformer 那一行已补锚点 |
| W2 | 两窗按**实际达成帧数**对齐，达成帧数逐步落盘；给出对齐方式与目标/达成对照 |
| W3 | 重跑 `tetris`/`pong`/`asteroids` + 脚本臂 PASS 款的**新旧 verdict 对照**与**是否翻转**（翻转如实报） |
| W4 | `ack` 缺失 ⇒ INCONCLUSIVE；测试覆盖"不得回退 pre_ack" |
| W5 | 模板新增"读图锚点"硬要求；并已用于修正后的 platformer 那行 |
| W6 | 产物清单（路径 + sha256 + 大小 + 生成命令）**已提交进仓**，可据以复核结论 |
| W7 | 本批重定向自查数字（台账条数 + 命中条数 + 逐条原文） |
| W8 | `DECISIONS.md` 本批条目已加 |
| W9 | 铁律逐条 + 文件所有权自查 + 两仓 `git log --oneline -5` 与 `git status --short` |
| W10 | 未达标项如实报告 |

---

## 4. 报告落点与返回值

* 报告：`F:\moonbit-hof-rs\godot-mcp\recovery\reports\TASK-138-REPORT.md`
* **返回值只给报告路径 + 一行状态**。