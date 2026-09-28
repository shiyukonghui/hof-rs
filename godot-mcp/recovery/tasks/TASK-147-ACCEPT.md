# TASK-147-ACCEPT — 独立复验：`TEST-CASES.md` 自洽性修复（blocker 是否真清）

> **你是独立验收方**：不得继承实施者/决策者结论；只看 §0 判据、**代码/矩阵实物**、**可复现证据**。**必须自己跑、自己重算**。
> 报告 `recovery\reports\ACCEPTANCE-TASK-147.md`，**只返回该路径 + 一行 verdict**。
> **只读验收**（可写 `recovery/work/accept-147/**` 与报告）。**严格单线程**：不得再派子代理。

---

## 0. 背景与验收基准

上一轮独立验收（TASK-145）判 **fail**，blocker = `recovery/TEST-CASES.md` **§1.1 声明与正文不符**
（声明 `TC-PY=404/合计785` vs 正文 `400/781`；**4 条 TASK-144 新增 pytest 用例无编号行**；**2 行指向已改名/不存在的测试**）、
major = **23 处 stale "23 passed"**、口径偏宽（**"强反例 177/177"** 应为 **175/177 + 2 弱**）。

实施方（TASK-146，提交 `03839a5`）声称：**修后 `TC-PY=407、合计=788`**（六族逐族相等）；补齐 4 条编号行；
替换 2 条失效行名为真实测试；全篇 25 处 stale → **30 passed**；口径收紧为 **175/177 + 2 弱**；
新增 `tools/tests/test_matrix_self_consistency.py`（3 条）并经**三种故意破坏**真判红、恢复后 `TEST-CASES.md` sha256 逐位未变；
`pytest tools\tests` = **30 passed / 0 failed / 0 skipped**。

**判据**：矩阵与实物必须严格一致；数字必须可复现；口径不得偏宽；未达标项必须如实登记。

---

## 1. 要独立核验的事项（**全部自己重算，不信转述**）

### A. blocker 是否真清
1. **统计 == 正文**：**自己**从 `TEST-CASES.md` 正文**重算**六族计数与合计（别用它的脚本；如用，须另写一个独立实现对照），
   核对是否等于 §1.1 声明（报告称 `177/10/22/159/407/13 = 788`）。**逐族**给数字。
2. **TASK-144 的 4 条新用例**：在矩阵里**逐条找到**编号行（报告称指针 286/299/337/361），核字段是否齐全（输入形式/输出形式/反例/证据指针/现状）。
3. **2 条替换后的行名**（报告称 `test_the_batch_gate_judges_the_declared_channel`(:254)、`test_every_fail_is_a_real_shortage_on_its_own_channel`(:272)）：
   **自己确认这些测试真实存在**（文件+行号+名字一致），并**全篇扫描**是否还有指向不存在对象的引用（`pytest=def` / `script_check` / 行号指针）。
4. **stale 是否清干**：全篇搜 `23 passed` 与其它数字；核 §8.1 的实测数（报告称 30）是否与**你自己跑的**结果一致，且**全篇只有一个来源**。

### B. 口径与反例强度
5. 核 §1.2/§1.4 是否已是 **175/177 强 + 2 弱**；§2 那两条 `editor_simulate_*` 是否标 `weak`；
   核报告新增的对抗性结论是否与**代码**一致：**121 `missing_required` + 21 `wrong_type` 由 handler 侧 `tool_builder.cpp:207-232` 的 `require_string/require_int` 发出**、
   **2 条只到 `tool_registry.cpp:864`**（`editor_simulate_*`）。**逐处引用文件:行**。

### C. 自洽校验测试是否真的有效（**对抗性**）
6. 读 `tools/tests/test_matrix_self_consistency.py`，**自己故意破坏**至少两种（例如：改一份**副本**的 §1.1 合计；或把一行指向不存在的测试名）
   ⇒ 确认**真的判红**；**恢复**后证明被跟踪文件 **sha256 逐位未变**（给出前后 sha256）。
7. 检查它**是否可能被绕过**（例如只比对一个家族、把 `printed` 类测试漏掉、只校验合计不校验逐族）——有则点名。

### D. 全局回归与诚实性
8. 自己跑 `pytest tools\tests`（给通过/失败/跳过 + 原始命令）；核对报告称的 **30 passed**。
9. **抽样 ≥6 条 TC-TOOL 行**重新核对（schema/通道/台账/反例指针）是否仍与实物一致（防修复过程改动它处）。
10. 核对报告 §F/§H 的**未达标/遗留**与它自认的 2 条重定向违规是否属实、是否影响产物。
11. 核对提交 `03839a5` 的**文件清单**是否只有它独占的那些（**没有**替他人提交 `DECISIONS.md`/`TASK-140-REPORT.md`/`playability_*` 等）。

---

## 2. 约束

1. **禁止一切 shell 重定向**；用 `-o`/`-OutFile`/Python 句柄。
2. **只读验收**；破坏性命令默认拒绝；**不碰产品/引擎代码与游戏工程**；不改 `.gitignore`。
3. 唯一高位端口；禁止第三方端点；串行；不用 8080/8081。
4. **区分"证据支持"与"推断"**；不成立的**明说**；发现造假一律 blocker。

---

## 3. 结构化输出（报告末尾必须有）

```json
{ "verdict": "pass | fail",
  "criteria": [{"id":"A1","pass":true,"evidence":"我重算的数字 / 文件:行 / 产物路径"}],
  "defects": [{"what":"...","severity":"blocker|major|minor","evidence":"..."}],
  "risks": ["..."], "unverifiable": ["..."] }
```

任一 `blocker`（统计仍与正文不符、引用仍失效、数字不可复现、自洽测试形同虚设）⇒ **`verdict: "fail"`**。

---

## 4. 报告落点

* `F:\moonbit-hof-rs\godot-mcp\recovery\reports\ACCEPTANCE-TASK-147.md`；**只返回路径 + 一行 verdict**。