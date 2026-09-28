# TASK-149 — 仓库清理（含已中止支线入库）+ 规范类文档校对

> 子代理**只读本文件**执行；报告 `recovery\reports\TASK-149-REPORT.md`，**只返回路径 + 一行状态**。
> **严格单线程**：不得再派子代理。**禁止 shell 重定向**（`>`/`>>`/`2>&1`/`2>nul`/`1>NUL`/`2>/dev/null`）。
> **独占**：`DECISIONS.md`、`recovery/tasks/**.md`、`recovery/reports/*.md`、`recovery/work/**`、`recovery/TEST-CASES.md`、
> `TOOL-COVERAGE.md`、`PLAYABILITY-REPORT.md`、`PLAYABILITY-DEFECTS.md`、`GAME-LOOP-LOG.md`、`recovery/reports/ERRATA.md`（新建）、`recovery/tasks/TASK-149.md`。
> **禁触**：`projects/**`（游戏工程）、`tools/**`（产品代码与测试代码）、引擎仓 `godot/**`（**唯一例外**：`godot/.gitignore` 加一行，见 §C）、`dist/**`、`F:\models\**`、两个 venv、8080/8081。

---

## 0. 依据（用户裁定）

* 主线 = **好用的 MCP 工具**；游戏/可玩性那套**已中止**（TASK-142 被中断）。
* 用户裁定：**① 把已中止支线的改动作为「已中止支线」独立提交（保留、非破坏）；② 文档校对范围为「规范类 + 最新报告」，老报告只做勘误索引。**

**当前残留（实测）**：
* 已修改：`DECISIONS.md`、`recovery/reports/TASK-140-REPORT.md`、`recovery/tasks/TEMPLATE-logic-feedback.md`、
  `tools/playability_controls.json`、`tools/playtest_player.py`、`tools/tests/test_playability_model_player.py`；
* 未跟踪：`recovery/reports/{ACCEPTANCE-TASK-137,ACCEPTANCE-TASK-141,ACCEPTANCE-TASK-145,ACCEPTANCE-TASK-147,TASK-142-REPORT}.md`、
  `recovery/tasks/{TASK-137-ACCEPT,TASK-141-ACCEPT,TASK-142,TASK-143,TASK-144,TASK-145-ACCEPT,TASK-146,TASK-147-ACCEPT,TASK-148,TASK-149}.md`、
  `recovery/work/accept-145/`、`recovery/work/accept-147/`、`tools/playtest_player_t142_prefix.py`。
* **批次产出未入库**：`recovery/work/task144/`、`recovery/work/task148/`（TASK-143/146 的 work 已入库）。

---

## 1. 目标

### A. 审计轨迹入库（**逐文件暂存**，一个提交）
1. 提交：`recovery/reports/ACCEPTANCE-TASK-{137,141,145,147}.md`、`TASK-142-REPORT.md`、
   各 `recovery/tasks/TASK-13x/14x*.md`（含各 `*-ACCEPT.md`）、`recovery/work/accept-{145,147}/`、`recovery/work/task144/`、`recovery/work/task148/`。
2. 提交信息写清**本批入库的是哪些证据**与它们对应的交付提交（`8c562d4`/`e9d17f9`/`03839a5`/`91783eb`）。

### B. 已中止支线（TASK-142）独立提交（**保留、非破坏**）
3. 把 §0 列出的**已修改**文件与 `tools/playtest_player_t142_prefix.py` 作为**一个独立提交**：
   * 提交信息**必须**注明：**来自已中止的支线 TASK-142（主线已于 2026-09-28 校正为"MCP 工具测试用例"）**、**保留仅作参考**、
     **不属于本主线交付**、以及**它的被测状态**（TASK-143 记录：`task142_cases` 52 断言 PASSED，未让任何测试变红）。
   * **不得**把 `DECISIONS.md` 拆成两半提交——见 §D。
4. **不得 revert / 丢弃**任何内容（用户选了"保留"）。若发现某文件与主线冲突（例如会改产品行为），**只报告不处置**。

### C. 引擎仓 `uid_cache.bin`
5. 在 **`godot-mcp/godot/.gitignore`** 追加忽略 `uid_cache.bin`（**非破坏**：不删文件），提交到引擎仓（分支 `feature/mcp-server-module-rebuild`，**不 force**）。
6. 复跑 `run_gates` 的 **preflight**（或等价检查），确认 `WORKING_TREE_RED` **不再**由该文件引起；给原始输出要点。若仍红，**逐条说明剩下的是什么**。

### D. `DECISIONS.md`
7. 追加条目（编号顺延；**沿用文件既有格式**）：① **主线校正**（2026-09-28，用户裁定：交付物是 MCP 工具，非小游戏）与**中止 TASK-142** 的原因/影响；
   ② TASK-143（781→788 用例矩阵口径）、TASK-144（U4 规则对齐 + g09 锚点复位 `ba1587c71`）、TASK-146（矩阵自洽守护 + 口径收紧 175/177）、
   ③ TASK-148 **打包偏离**（单卷 vs 两卷的口径澄清、MANIFEST 增列、`UseSharedCompilation=false` 根因）。
8. **注明**：其中 TASK-142 相关条目**来自已中止支线**（若文件中确有），以免读者误以为它在主线内。

### E. 文档校对（**规范类 + 最新报告**）
9. **校对范围（以此为准）**：
   * 规范类：`DECISIONS.md`、`recovery/tasks/README.md`、`recovery/tasks/TEMPLATE-logic-feedback.md`、`recovery/TEST-CASES.md`、
     `TOOL-COVERAGE.md`（及同目录 `PLAYABILITY-*`、`GAME-LOOP-LOG.md`）；
   * 最新报告：`recovery/reports/TASK-{143,144,146,147,148}-REPORT.md`、`ACCEPTANCE-TASK-{137,141,145,147}.md`。
   * **老报告不改**，只进 §E.12 的勘误索引。
10. 校对内容：**失效交叉引用**、**陈旧/自相矛盾的数字**、**与代码冲突的说法**（**代码优先**）、**失效路径/行号**、**术语与命名不一致**（例如同一机制多个名字）。
11. **必须复跑验证**：改完 `recovery/TEST-CASES.md` 或任何被守护的东西后，跑
    `python -m pytest tools\tests -q --no-header -p no:cacheprovider`（当前基线 **30 passed**）与 `recovery/TEST-CASES.md` 自洽校验；
    **若你的文档改动让守护测试变红，必须修文档而不是改测试**。
12. 新建 `recovery/reports/ERRATA.md`：**老报告的勘误索引**，逐条给「文件 / 原说法 / 更正 / 依据」。
    至少收录已点名的这些（其余你自行补充）：
    * `TASK-140-REPORT.md` 同一报告内 **194 vs 186**（权威台账重算 = 194）；
    * `TEST-CASES.md` 的 "**121** 条 missing_required" **不可复现** ⇒ 实测 **142 = 119（`tool_builder.cpp:207-232`）+ 21（`Parameter '…' must be`）+ 2（无冒号，`editor_node_write.cpp:1040` / `editor_node_property_updates.cpp:435`）**；
    * `TASK-129` §9.4 的"**只有一个仓**"说法（本机实为**两个**：外层 + 嵌套引擎仓）；
    * `TASK-136` §7 第 9 行 platformer 帧描述（实为 `TILE 3,27`，原文 `4,27`）——并**附可机检锚点**；
    * `TASK-136` §4.1 platformer 的 strict 列、§1.2 的 `PASS(baseline only)` 举例（真例是 pong/asteroids）。

### F. 交付
13. 报告：逐项给**提交号**、**改了什么**（文件 + 关键 diff 摘要）、**复跑结果**（pytest 数字 + preflight）、**未达标项**、关键产物**路径 + sha256**。
14. **只提交你独占清单里的文件**；`dist/**` 大包不动；不代提交其它人/其它批的产物（除 §A 明确列出的审计轨迹）。

---

## 2. 硬性约束

1. **禁止一切 shell 重定向**；用 `-o`/`-OutFile`/Python 句柄；如可用台账机制则给自查数字。
2. **破坏性命令默认拒绝**；**不得** `git checkout --`/`restore` 丢弃他人改动；不删文件、不删旧包、不改 `.gitignore`（除 §C 的引擎仓一行）。
3. **不改产品/测试代码**（`tools/**` 只读）、不改游戏工程。
4. 命令尽量**从 cmd 启动**；唯一高位端口；禁止第三方端点。
5. **代码优先于文档**；冲突时改文档并显式记录。
6. **未达标项如实报**（不得"应该可以"）。

---

## 3. 验收判据

| 编号 | 判据 |
|---|---|
| Q1 | 审计轨迹（§A 列出的报告/任务书/work 目录）已入库，且提交信息写明对应交付提交 |
| Q2 | TASK-142 残留作为**一个独立提交**入库，提交信息注明"已中止支线/仅作参考/不属于主线交付/被测状态" |
| Q3 | **无任何丢弃/revert**；`git log` 可追；被跟踪文件内容与提交前一致（除有意修改的文档） |
| Q4 | 引擎仓 `.gitignore` 已加 `uid_cache.bin` 并提交；preflight 复跑结果给出（不再因它而红，或逐条说明剩余项） |
| Q5 | `DECISIONS.md` 已加本批条目（主线校正/143/144/146/148 偏离），并注明 TASK-142 条目的来源 |
| Q6 | 校对范围内的文档已逐份过一遍：列出**逐文件发现与修改**（含"无问题"的文件） |
| Q7 | `recovery/reports/ERRATA.md` 已建，至少收录 §E.12 点名的 5 类勘误，逐条「文件/原说法/更正/依据」 |
| Q8 | **改完复跑**：`pytest tools\tests` 数字给出（基线 30 passed）、`TEST-CASES.md` 自洽校验通过；若曾变红，说明如何处理 |
| Q9 | 铁律逐条 + 文件所有权自查 + 两仓 `git log --oneline -5` / `git status --short` + 关键产物路径与 sha256 |
| Q10 | 未达标项如实报 |

---

## 4. 报告落点

* `F:\moonbit-hof-rs\godot-mcp\recovery\reports\TASK-149-REPORT.md`；**只返回路径 + 一行状态**。