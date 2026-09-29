# TASK-DR62-ACCEPT — DR-62（三处"靠约定"缺口）独立验收

> 你是**独立验收子代理**。不得继承实现者或调度者的结论。
> 判据：`.spec/hof-rs/tasks/TASK-DR62.md`、`DECISIONS.md` **D249/D250**。
> 实现者报告（**线索，非证据**）：`.spec/hof-rs/tasks/TASK-DR62-REPORT.md`。
> 批次提交（起点 `6a0c9a9`）：`d338459`(红) → `6dc12b5`(修①②) → `49b9417`(固定作用域③)。
> **离线批次**。产物：`.spec/hof-rs/tasks/TASK-DR62-ACCEPTANCE.md`。

## 1. 核心复核（自己复现，给命令 + 原始输出 + 文件:行）

1. **套件**：`cargo test --offline` 应 **exit 0**；与 **366 passed / 0 failed / 7 ignored** 对照；
   `ignored` **未增**；**无既有测试被删/放宽/加 `#[ignore]`**（`git diff 6a0c9a9..HEAD --numstat` 逐条判，
   包括"改名/重写"是否只是**加强**）。
2. **判据是否真的不靠名字（头号目标）**：读实现，指出"是否被取代"的**判定源**是什么（manifest 记录？）；
   然后**你自己构造**一个**本轮**产物、把它命名为 `*.stale-*`，断言它**仍出现在**候选视图里
   （即**不再被误隐藏**）。**若它仍被隐藏 ⇒ 判 fail**。
3. **`copy_tree` 缺口**：确认 `run_loop.rs:991` 那条路径**应用了同一判据**（不只是 `view.rs`）。
   自己构造"上一轮在 `.hoh/deterministic` 留一个可识别件 + 新开轮"，断言它**不进**候选。
4. **遍历作用域被永久固定（DEF-1）**：读新自检，确认它有**埋在 `.hoh` 之外**的标记；
   然后**把 `walk` 收窄回 `.hoh`**（**只改生产代码**）⇒ **新自检与既有的 `.hoh` 外种子测试都必须红**。
   **若收窄后仍绿 ⇒ 判 fail**（作用域仍未被固定）。
5. **非空洞性**：**三处**仅生产代码的植入（①判据改回按文件名；②关掉 `copy_tree` 过滤；③`walk` 收窄回 `.hoh`）
   各自使**对应**测试红；逐字节回退（`git status --porcelain` 与 `git diff --stat` 双空 + `git hash-object` == HEAD blob；
   仓库 CRLF 敏感）。
6. **引擎 mtime 差异复核（D250 的 R-F）**：独立核对引擎树——嵌套仓 `status --porcelain`、
   关键 `.cpp` 的 sha256、以及 `mcp_server` 最新 mtime；**明确回答** `10:58:15` 与 `10:37:38` 的差异
   是否可解释（并写清你的依据）。**不得**把"没查出来"写成"确认未改"。
7. **禁区**：`.workspace/mario` 与 `runs/**` 未动（**写明摘要口径**，口径含 PowerShell `Sort-Object` 文化排序；
   并自证口径：`runs/smoke-t6` 应等于 `c144ef32…7a9c03`）；`PRD-mario.md` sha 未变；Cargo 零 diff；
   **未 push**（`origin/master` 应为 `6a0c9a9`）、未 stage。
   **引擎树"未改"必须用嵌套仓**（D242），并证明 pathspec 真能命中。两个假绿陷阱各实测
   （含 `git cat-file -e HEAD^:…` 在 cmd 与 bash 行为不同）。
8. **它的诚实声明**：逐条核实，不得把假设混成实测。

## 2. 纪律
只读为主；**唯一**改动是 §1.2/§1.4/§1.5 的植入（逐字节恢复 + 三法证明）。
**离线**：不启动 Godot、不碰外部端口、不联网、不调模型。
不改 `.workspace/mario/**`、`runs/**`、`PRD-mario.md`、`DECISIONS.md`、`godot-mcp/**`。
**不 push、不 stage、不改写历史**。**不要修任何你发现的问题。**

## 3. 结构化结论（写进报告 §1）
```json
{ "verdict": "pass" | "fail",
  "criteria": [ { "id": "SUITE|NOT_NAME_BASED|COPY_TREE|WALK_SCOPE_PINNED|NON_VACUITY|ENGINE_MTIME|GUARDS|HONESTY",
                  "pass": true, "evidence": "命令 + 真实输出 + 文件:行" } ],
  "defects": [ { "id": "DEF-x", "severity": "blocker|major|minor|info", "what": "...", "reproduction": "..." } ],
  "risks": [ "..." ], "unverified": [ "..." ] }
```
`verdict=fail` 门槛：套件不绿/ignored 增、**判据仍靠名字**、带 `.stale-` 的本轮产物仍被隐藏、
`copy_tree` 未覆盖、**收窄 `walk` 后仍绿**、或禁区被动过。

## 4. 报告必含小节
1. 结构化结论 + 真实命令与退出码；2. 逐项核对表；3. **反例清单**（你的植入位置与观测）；
4. 对"判据不靠名字"的独立判定；5. 对"作用域被永久固定"的独立判定；6. **引擎 mtime 差异的独立结论**；
7. 未验证项与理由；8. 你没有独立复核的部分；9. 给下一批的建议（**不要**自己改代码）。

**回报给父代理只有一行：报告文件路径。**