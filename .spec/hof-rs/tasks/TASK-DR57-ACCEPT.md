# TASK-DR57-ACCEPT — DR-57（零请求计数测试 + 报告更正 + DEF-2）独立验收

> 你是**独立验收子代理**。不得继承实现者或调度者的结论。
> 判据来源：`.spec/hof-rs/tasks/TASK-DR57.md`（任务书）、`.spec/hof-rs/tasks/TASK-DR54-ACCEPTANCE.md`（**首次发现该缺陷的验收报告**）、
> `DECISIONS.md` **D238/D239/D242/D244**、`DESIGN-DETAIL.md` **§15**（DR-55）。
> 实现者报告（**线索，非证据**）：`.spec/hof-rs/tasks/TASK-DR57-REPORT.md`。
> 批次提交（起点 `ba32de6`）：`440fc89`、`05efd7f`、`580b86c`、`ae7a45e`、`23304a1`、`c1586e1`、`f4f18cb`、`29fc265`。
> **离线批次**。产物：`.spec/hof-rs/tasks/TASK-DR57-ACCEPTANCE.md`。

## 1. 核心复核（逐条自己复现，给命令 + 原始输出 + 文件:行）

1. **套件**：自己跑 `cargo test --offline`；应 **exit 0 / 353 passed / 0 failed / 7 ignored**（37 targets）；
   核对 `ignored` **未增加**、**无测试被删/放宽/加进 `#[ignore]`**（`git diff ba32de6..HEAD --stat/-numstat` 逐条判）。
2. **头号反例目标：新测试真的"数在不会循环的那一层"吗？**
   自己读 `tests/endpoint_request_count.rs`：计数器是否确实在 **`call_with_meta` 之下、DR-55 早退之下、`McpClient::post` 之下**
   （即**只有真实 HTTP 尝试到达**才会产生连接）？**若计数器挂在任何会被判死逻辑拦掉的路径上 ⇒ 判 fail**。
   并核对它的自证：判死时 `accepted==2`、判死后 3 次调用计数**不动**、**重注册后能再动（+1）**。
3. **非空洞性（自己设计）**：任务书要求"植入 ⇒ 新测试必红"。**你至少自己做 2 处植入**（可参考但不要照抄
   `dr57-plants.ps1`）：①"判死前仍发一次请求"；②删除整个判死守卫。两次都**必须**让目标测试红，
   且**植入必须落在生产代码**（不得改测试）。每次逐字节回退并三法证明
   （`git status --porcelain` 与 `git diff --stat` 双空 + `git hash-object` == HEAD blob；仓库 CRLF 敏感）。
   **若新测试对某类植入仍是绿的 ⇒ 判 fail。**
4. **报告更正是否**真是更正**：`TASK-DR54-REPORT.md` §3.2 是否**引述了原文**、给出新文、
   **明确写出原推理为何无效**（关键：判死后 `observe()` 直接返回、`call_with_meta` 不再到达它，
   故 `consecutive_transport_failures` 是**结构性恒等**），并**指向新测试**。
   确认它**没有**删改其它结论、**没有**把报告粉饰成"原本就对"。核对报告 §6 那份"以观测充因果"的清单是否可信。
5. **DEF-2 处置**：`InputChannelProbe.has_action` 是否**被删**（含其唯一写入方），
   文档注释是否解释清楚"无读者却会被序列化进已发布证据，null 会被读成'动作不存在'"；
   确认**没有任何有读者的字段**被改动。并核实它自报的**同形残留** `is_pressed_before`（恒 None、无读者）**确实存在**。
6. **flake（独立判定）**：它报告 `tests/endpoint_liveness.rs::the_editor_endpoint_state_is_separate`
   在一次全量运行中 panic（`:435:10`，os error **10053**），并称该文件**字节未改**。
   请**多跑几次全量**（≥4 次）如实报告是否复现；核对 `endpoint_liveness.rs` 在区间内**零 diff**；
   并判定这是**既有问题**还是**本批引入**。**若本批引入 ⇒ 判 fail。**
7. **禁区与陷阱**：`.workspace/mario/**` 未被改；`runs/**` **只读且未动**（两轮基线文件数与最新 mtime 不变，
   并**自算摘要口径写清**）；`PRD-mario.md` sha256 仍 `4c81c3a9…5c3a`；`Cargo.toml`/`lock` 零 diff；
   **未 push**（`origin/master` 应为 `afb649a`）；未 stage。
   **引擎树"未改"必须用嵌套仓证明**（`git -C godot-mcp/godot status --porcelain -uno` 等，见 D242）——
   **不得**用外层 `git diff`（外层**不跟踪**引擎树）；并证明你的 pathspec 真能命中。
8. **两个假绿陷阱**（`git diff` 对不存在 pathspec 不报错；`cmd` 里 `^` 是转义符）各实测一次并给正确读法。

## 2. 纪律

只读为主；**唯一**允许的改动是 §1.3 的受控植入（逐字节恢复 + 三法证明）。
**离线**：不启动 Godot、不碰任何端口、不联网、不调模型端点。
不改 `.workspace/mario/**`、`runs/**`、`.spec/hof-rs/PRD-mario.md`、`DECISIONS.md`、`godot-mcp/**`。
**不 push、不 stage、不改写历史**（分支上有未推送提交等你判决）。**不要修任何你发现的问题。**

## 3. 结构化结论（写进报告 §1）

```json
{ "verdict": "pass" | "fail",
  "criteria": [ { "id": "SUITE|COUNTER_LAYER|NON_VACUITY|REPORT_CORRECTION|DEF2|FLAKE|GUARDS|TRAPS",
                  "pass": true, "evidence": "命令 + 真实输出 + 文件:行" } ],
  "defects": [ { "id": "DEF-x", "severity": "blocker|major|minor|info", "what": "...", "reproduction": "..." } ],
  "risks": [ "..." ], "unverified": [ "..." ] }
```

`verdict=fail` 门槛：套件不绿或 ignored 增加、**计数器层可被门冻住**、**任一类植入不红**、
报告"更正"实为粉饰、DEF-2 改动有读者的字段、flake 被判定为**本批引入**、或禁区被动过。

## 4. 报告必含小节

1. 结构化结论 + 真实命令与退出码；2. 逐项核对表；3. **反例清单**（你自己的植入 + 观测 + 是否推翻）；
4. 对"计数器层不可循环"的独立判定；5. **flake 的独立判定与复现次数统计**；
6. 未验证项与理由；7. 你没有独立复核的部分；8. 给下一批的建议（**不要**自己改代码）。

**回报给父代理只有一行：报告文件路径。**