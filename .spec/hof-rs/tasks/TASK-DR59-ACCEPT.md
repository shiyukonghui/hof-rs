# TASK-DR59-ACCEPT — DR-59（确定性证据按轮次隔离）独立验收

> 你是**独立验收子代理**。不得继承实现者或调度者的结论。
> 判据：`.spec/hof-rs/tasks/TASK-DR59.md`（任务书）、`DECISIONS.md` **D240/D244/D245/D246**。
> 实现者报告（**线索，非证据**）：`.spec/hof-rs/tasks/TASK-DR59-REPORT.md`。
> 批次提交（起点 `ea1cf07`）：`91a28f8`（红测试）、`db145b5`（quarantine）、`7fab86b`（两轮复现）。
> **离线批次**。产物：`.spec/hof-rs/tasks/TASK-DR59-ACCEPTANCE.md`。

## 1. 核心复核（逐条自己复现，给命令 + 原始输出 + 文件:行）

1. **套件**：`cargo test --offline` 应 **exit 0**；与当前基线对照（**353 passed / 0 failed / 7 ignored**），
   核对新增测试条数、**`ignored` 未增**、**无测试被删/放宽/加入 `#[ignore]`**（`git diff ea1cf07..HEAD --numstat` 逐条判）。
2. **隔离是否真的成立**：读实现，回答"新一轮的**读取路径**凭什么看不到上一轮证据"；
   并**自己**构造一轮"上一轮残留 + 新开轮"，断言**读不到**。
3. **必须是"移开/隔离"，不是"删除"（硬要求）**：确认实现把旧证据**移到可寻址的位置**（如 `.stale-`/quarantine 目录）
   且**字节仍在**；**若实现等价于删除用户数据 ⇒ 判 fail**。测试断言里**必须**能证明"旧字节仍存在且可定位"。
4. **非空洞性（自己设计植入）**：把隔离**关闭/改成恒不触发**（**只改生产代码，不改测试**）⇒ 目标测试**必须变红**；
   逐字节回退并用三法证明（`git status --porcelain` 与 `git diff --stat` 双空 + `git hash-object` == HEAD blob）。
5. **两轮复现件（`7fab86b`）**：核实它**确实**跑了两轮并复现 `smoke-t6 → smoke-t7` 的污染形态；
   确认它**不依赖** `.workspace/mario`（必须在 scratch/临时工作区，且报告该路径与清理情况）。
6. **禁区**：`.workspace/mario/**` 未改；`runs/**` **只读未动**（两轮基线文件数与最新 mtime 不变，**摘要口径写清**）；
   `PRD-mario.md` sha256 仍 `4c81c3a9…5c3a`；Cargo 零 diff；未 push（`origin/master` 应为 `ea1cf07`）、未 stage。
   **引擎树"未改"必须用嵌套仓** `git -C godot-mcp/godot …` 或 mtime/摘要（外层**不跟踪**引擎树，D242），
   并**证明 pathspec 真能命中**。两个假绿陷阱（不存在 pathspec；`cmd` 的 `^`）各实测。
7. **它的诚实声明**：逐条核实（例如它自报的未验证项/假设），**不得**让"假设"混成"实测"。

## 2. 纪律
只读为主；**唯一**允许的改动是 §1.4 的受控植入（逐字节恢复 + 三法证明）。
**离线**：不启动 Godot、不碰任何端口、不联网、不调模型端点。
不改 `.workspace/mario/**`、`runs/**`、`PRD-mario.md`、`DECISIONS.md`、`godot-mcp/**`。
**不 push、不 stage、不改写历史**（分支上有未推送提交等你判决）。**不要修任何你发现的问题。**

## 3. 结构化结论（写进报告 §1）
```json
{ "verdict": "pass" | "fail",
  "criteria": [ { "id": "SUITE|ISOLATION_REAL|QUARANTINE_NOT_DELETE|NON_VACUITY|TWO_ROUND_REPLAY|GUARDS|HONESTY",
                  "pass": true, "evidence": "命令 + 真实输出 + 文件:行" } ],
  "defects": [ { "id": "DEF-x", "severity": "blocker|major|minor|info", "what": "...", "reproduction": "..." } ],
  "risks": [ "..." ], "unverified": [ "..." ] }
```
`verdict=fail` 门槛：套件不绿或 ignored 增、隔离不成立、**实为删除**、植入不变红、两轮复现件不成立、或禁区被动过。

## 4. 报告必含小节
1. 结构化结论 + 真实命令与退出码；2. 逐项核对表；3. **反例清单**；4. 对"隔离真实且非删除"的独立判定；
5. 两轮复现件的独立判定；6. 未验证项与理由；7. 你没有独立复核的部分；8. 给下一批的建议（**不要**自己改代码）。

**回报给父代理只有一行：报告文件路径。**