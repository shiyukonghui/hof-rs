# TASK-144 — 收口工具测试的两个可修项：陈旧批校验脚本（U4）+ g09 锚点漂移（U1）

> 子代理**只读本文件**执行；报告 `recovery\reports\TASK-144-REPORT.md`，**只返回路径 + 一行状态**。
> **严格单线程**：不得再派子代理。**禁止 shell 重定向**（含 `> nul`/`1>NUL`/`2>&1`/`2>/dev/null`）。
> **禁触**：`projects/**`（游戏工程）、`projects/_exercises/**`、`F:\models\**`、两个 venv、8080/8081、`.gitignore`、`recovery/tasks/README.md`。
> **独占**：`tools/verify_coverage_batch.py`、`tools/tests/**`、`recovery/work/task144/**`、`recovery/TEST-CASES.md`（**只追加/更新 U4 行与统计**）、
> **引擎仓 `godot/`**（仅当为清 g09 必须重建时；见 §B）、`recovery/reports/TASK-144-REPORT.md`、`recovery/tasks/TASK-144.md`。
> **`DECISIONS.md` 已被中止批次（TASK-142）改脏**：**不要**把它整体 add。若需追加条目，**只能单独 `git add` 你自己新增的那一段**；
> 若无法干净分离 ⇒ **不改它**，把本该记录的内容写进报告，留给决策者。**不得** revert 他人改动。

---

## 0. 现状（一手，来自 TASK-143，提交 `8c562d4`）

* `recovery/TEST-CASES.md`：**781 条用例**（6 族：TC-TOOL 177 / TC-GATE 10 / TC-M1 22 / TC-ENG 159 / TC-PY 400 / TC-CONS 13）；
  **177 工具强反例 175/177**（trace 真实失败调用 172 + 活体探针 142 个真收到 `-32602`），弱反例 2，**完全无 0**。
* 新增测试 `tools/tests/test_contract_forms.py`（14）与 `test_coverage_batch_consistency.py`（5）：**pytest 23 passed**。
* `coverage.json` 重生成与已提交版**逐行一致**；自写 trace 读取器与 `tool_coverage.py` 在同一 182 文件语料上同得 `calls=8729` 互证。
* **十道门：9 绿 1 红**；`accept_m1 22/22`。
* **待决策三项**：U1 g09 红（锚点漂移）、U2 两条 simulate 工具无真实失败观察（0 调用、scope_excluded）、
  U4 `tools/verify_coverage_batch.py` **陈旧**（仍用 TASK-118 之前的 `effective>=1` 规则 ⇒ 对 `editor_state` 通道工具**系统性误红**：
  166 目标 **118 pass / 48 fail**，其中 **45 条误红 + 3 条真实缺证据**）。
* **F1（PIN，不擅改）**：3 条工具 schema 无 `required`（`editor_get_selection` / `editor_set_node_selection` / `editor_remove_node_selection`，
  其中 `set_node_selection` 是 one-of，方言表达不出）。

---

## 1. 目标

### A. 修 U4：把陈旧批校验脚本对齐现行规则
1. 读 `tools/verify_coverage_batch.py` 与 TASK-118 之后的现行规则（以 `tools/tool_coverage.py` + `tools/tool_channels.json` 为准；
   **代码优先于任何文档/报告**），**修掉 `effective>=1` 这类陈旧判据**，使 `editor_state` 通道工具不再被系统性误红。
2. **给出前后对照**：166 目标在修前 `118 pass / 48 fail` → 修后应为 **`163 pass / 3 fail`**（3 条为**真实缺证据**，逐条点名并说明缺什么）。
3. 为它补**反例判据**：一条**故意构造的错输入**（例如把某工具声明成错误通道）必须判红；并把该负例写成测试。
4. 更新 `TEST-CASES.md` 中 U4 相关行与统计（**只改这些行**）。

### B. 清 U1：g09 红 = **锚点记账漂移**，按既有流程收口
5. 你已给出一手证据（TASK-143）：二进制自报 `3fdabe2d9`、引擎 HEAD `ba1587c71`、A..H 有 5 个编译输入 ⇒ `ANCHOR_STALE_COMPILED`；
   且**二进制内含 159 个 `[MCPServer]` 用例**（HEAD 159、锚点版本仅 157）⇒ **二进制其实含着 TASK-112 的改动，只是版本串没换**。
6. 因此按既有流程执行：**两变体重建 → 十道门全绿 → `accept_m1 22/22` → push**（引擎仓 `git@github.com:shiyukonghui/godot.git`），
   然后**重记锚点**并复跑 g09 使其转绿。
   * 若重建后发现**确有**未包含的改动 ⇒ 如实报告"不是纯记账漂移"，**不要**只为让 g09 变绿而伪造锚点。
   * 重建/推送的每一步给**原始命令与输出要点**；push 前确认只在 `feature/mcp-server-module-rebuild` 上、且不 force。
7. 若因环境原因无法完成重建/推送 ⇒ **如实报告阻塞点**（已尝试什么、需要什么），**不要**绕过 g09。

### C. 记录与交付
8. 报告含：U4 修法 + 前后对照 + 新负例；U1 全流程证据（含两变体产物路径 + sha256、十道门逐门结果、`accept_m1` 结果、push 结果、新锚点）；
   U2/F1 的处置（保持"如实登记"或给出更强的反例尝试，说明为何做不到）；**未达标项如实报**。
9. 提交：**逐文件暂存**，只提交你独占清单里的文件；TASK-142 残留与既有未跟踪报告**一律不代提交**。

---

## 2. 硬性约束

1. **禁止一切 shell 重定向**；如台账机制存在则沿用并给自查数字。
2. **破坏性命令默认拒绝**；**不碰游戏工程**；不改 `.gitignore`。
3. 命令尽量**从 cmd 启动**；唯一高位端口；禁止第三方端点；模型调用（若用到）串行。
4. **不许放宽判据**：U4 修的是**误报**，不得顺手放宽真实缺口判据；g09 必须**真绿**。
5. 改引擎模块 ⇒ 必须走 §B 全流程（这本来就是本任务要求）。
6. **事实来源分级**；代码与文档冲突以代码为准。**未达标项如实报**。

---

## 3. 验收判据

| 编号 | 判据 |
|---|---|
| D1 | `verify_coverage_batch.py` 已对齐现行规则；前后对照 `118/48` → `163/3`（或给出不符的确切原因） |
| D2 | 该脚本有**会失败的负例**（构造错通道 ⇒ 判红），并写成测试 |
| D3 | `TEST-CASES.md` 的 U4 行与统计已更新（只改相关行） |
| D4 | g09：两变体重建 + **十道门逐门结果**（应 10 绿）+ `accept_m1 22/22` + push 证据 + 新锚点 |
| D5 | 若重建暴露"确非纯记账漂移"，如实报告并**不以伪锚点收口** |
| D6 | U2/F1 处置明确（保持登记 or 更强的反例尝试 + 为何做不到） |
| D7 | 铁律逐条 + 文件所有权自查 + 两仓 `git log --oneline -3` / `git status --short`；关键产物路径 + sha256 |
| D8 | 未达标项如实报（不得"应该可以"） |

---

## 4. 报告落点

* `F:\moonbit-hof-rs\godot-mcp\recovery\reports\TASK-144-REPORT.md`；**只返回路径 + 一行状态**。