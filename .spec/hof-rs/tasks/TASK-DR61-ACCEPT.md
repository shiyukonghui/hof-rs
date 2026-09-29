# TASK-DR61-ACCEPT — DR-61（上一轮证据结构上不可达）独立验收

> 你是**独立验收子代理**。不得继承实现者或调度者的结论。
> 判据：`.spec/hof-rs/tasks/TASK-DR61.md`、`DECISIONS.md` **D247/D248**。
> 实现者报告（**线索，非证据**）：`.spec/hof-rs/tasks/TASK-DR61-REPORT.md`。
> 批次提交（起点 `5abddbd`）：`c139194`、`ab869e5`、`0d0f391`、`92e4aff`、`be8d115`（+ 报告）。
> **离线批次**。产物：`.spec/hof-rs/tasks/TASK-DR61-ACCEPTANCE.md`。

## 1. 核心复核（自己复现，给命令 + 原始输出 + 文件:行）

1. **套件**：`cargo test --offline` 应 **exit 0**；与 **359 passed / 0 failed / 7 ignored** 对照；
   `ignored` **未增**；**无既有测试被删/放宽/加入 `#[ignore]`**（`git diff 5abddbd..HEAD --numstat` 逐条判）。
2. **结构不可达（头号目标）**：不变量现在应当**遍历整个角色 cwd**。
   请**自设**至少两个位置各植入一份"上一轮证据"：①在 `.hoh` 下；②**在 cwd 内但 `.hoh` 之外**
   （例如 `cwd/somedir/` 或 `cwd/.hoh2/`）。**两处都必须让不变量红**。
   **若只有 `.hoh` 内的能红 ⇒ 判 fail**（说明仍是"针对已知位置的约定"，不是结构）。
3. **隔离物落点**：确认它**在角色 cwd 之外**；并自己走一遍 cwd 全树，**不得**出现上一轮字节。
4. **是移开不是删除**：旧字节仍**可寻址**；名字耗尽**不删除**（应失败）。
5. **非空洞性（自设两处植入，只改生产代码）**：①关掉隔离；②把隔离物**放回 cwd 内**。两者都必须让不变量红；
   逐字节回退（三法 + 你自选的第四法亦可）。
6. **`copy_evidence`**：被取代/隔离件**不得**进入 Tester 候选视图。自己构造"上一轮在 `.hoh/evidence` 留可识别文件 + 新开轮"，
   断言候选视图**不含**它。
7. **不得过度隔离（我特别关心这条）**：把隔离扩到**整棵 `.hoh`** 之后，**同一轮内**迭代 t≥2 的 Developer
   是否**仍能**看到 t-1 的轮内反馈（DR-59 的 R-2 是**刻意保留**的语义）？
   **若整树隔离把轮内状态也清掉了 ⇒ 这是回归，判 fail 或列为 blocker 级缺陷。**
8. **禁区**：`.workspace/mario` 未改；`runs/**` 只读未动（**写明摘要口径**，注意 PowerShell `Sort-Object` 的文化排序是口径的一部分）；
   `PRD-mario.md` sha 未变；Cargo 零 diff；**未 push**（`origin/master` 应仍 `5abddbd`）、未 stage。
   **引擎树"未改"必须用嵌套仓**（D242），并证明 pathspec 真能命中。两个假绿陷阱各实测。
9. **它的诚实声明**：逐条核实，不得把假设混成实测。

## 2. 纪律
只读为主；**唯一**改动是 §1.2/§1.5 的植入（逐字节恢复 + 三法证明）。
**离线**：不启动 Godot、不碰外部端口、不联网、不调模型。
不改 `.workspace/mario/**`、`runs/**`、`PRD-mario.md`、`DECISIONS.md`、`godot-mcp/**`。
**不 push、不 stage、不改写历史**（分支上有未推送提交等你判决）。**不要修任何你发现的问题。**

## 3. 结构化结论（写进报告 §1）
```json
{ "verdict": "pass" | "fail",
  "criteria": [ { "id": "SUITE|UNREACHABLE_STRUCTURAL|QUARANTINE_LOCATION|NOT_DELETE|NON_VACUITY|COPY_EVIDENCE|NO_OVER_QUARANTINE|GUARDS|HONESTY",
                  "pass": true, "evidence": "命令 + 真实输出 + 文件:行" } ],
  "defects": [ { "id": "DEF-x", "severity": "blocker|major|minor|info", "what": "...", "reproduction": "..." } ],
  "risks": [ "..." ], "unverified": [ "..." ] }
```
`verdict=fail` 门槛：套件不绿/ignored 增、**只有 `.hoh` 内的植入能红**、隔离物仍在 cwd 内、实为删除、
候选视图仍含上一轮 evidence、**整树隔离破坏了轮内反馈**、或禁区被动过。

## 4. 报告必含小节
1. 结构化结论 + 真实命令与退出码；2. 逐项核对表；3. **反例清单**（你植入的位置与观测）；
4. 对"结构不可达"的独立判定；5. 对"未过度隔离"的独立判定；6. 未验证项与理由；
7. 你没有独立复核的部分；8. 给下一批的建议（**不要**自己改代码）。

**回报给父代理只有一行：报告文件路径。**