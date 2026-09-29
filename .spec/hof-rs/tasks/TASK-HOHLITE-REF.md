# TASK-HOHLITE-REF — 以已发布的 `hoh-lite`（Python 包 `gameloop`）为 hof-rs 提供参考

> 你是**侦察/参考子代理**，无上游对话上下文；**本文件是你的唯一任务来源**。
> **只读**对象：`F:\HarnessOfHarness`（HEAD `ae7cc6f`，已克隆；**377 MB**，其中 `assets/` 182 MB、
> `hoh-lite/` 3.5 MB / 395 文件）。**不得修改、不得运行**其中任何东西。
> 你的产物：`F:\moonbit-hof-rs\.spec\hof-rs\tasks\TASK-HOHLITE-REPORT.md`。

---

## 1. 背景（我们的系统，你必须先读）

`F:\moonbit-hof-rs` 是 **Rust 实现** 的同概念系统（`hof-rs`）：三角色流水线 Planner → Developer → Tester、
证据分区（`D_n`/`E_n`、verified/gap、candidate 绑定）、MCP 工具作用域策略、`hoh` CLI
（`init`/`doctor`/`run`/`status`/`rollback`/`tools`/`submit`/`spec-hash`）、确定性证据电池与可启动闸门、
退出码 `0/2/3/4/5/6`、`DR-nn` 设计修订史。必读：
`.spec/hof-rs/REQUIREMENTS.md`（v0.3）→ `.spec/hof-rs/DESIGN-OVERVIEW.md` →
`.spec/hof-rs/DESIGN-DETAIL.md`（**§15 为最新，v0.10**）→ `.spec/hof-rs/ACCEPTANCE.md`（v2）→
`DECISIONS.md`（**D216..D234** 是最近的历史）。
**硬约束（任何建议都不得违反）**：`PRD-mario.md` 逐字节冻结；引擎工具契约 **177 条**（四通道前缀）冻结且逐字受门保护；
离线批次不得联网；不得依赖新引擎行为。

## 2. 对象（只读）

`F:\HarnessOfHarness\hoh-lite`：`pyproject.toml` 声明为包 **`gameloop` v0.1.0**
（"General iterative game-development loop with a GameCraft adapter"，Apache-2.0，Python ≥3.12，
**运行期零依赖**；可选 extras：`gamecraft-bench`=`harbor==0.23.0`、`deepseek-harness`=`deepseek-harness-sdk==0.1.0rc6`）。
分层：`src/gameloop/{core,harnesses,policies,adapters,benchmarks,tools,resources,templates}` + `_vendor`。
另有 `configs/`、`scripts/`、`tools/`（含 `tools/godot-mcp`）与 `assets/`。
入口：`gameloop`、`gameloop-gamecraft`、`gameloop-summarize` 等 console scripts。

## 3. 要产出什么（**证据优先**：每条断言给 `路径:行` 与原文引用）

1. **总览**：`gameloop` 是什么、怎么跑起来、它的**一次完整迭代**长什么样（时序/阶段/产物）。
2. **架构对照表**：`core`/`harnesses`/`policies`/`adapters`/`benchmarks`/`tools`/`templates`
   各自职责 ⇒ **与 hof-rs 的对应物或缺失项**（逐行对照，指出我们**没有**的概念）。
3. **角色与循环**：它的角色/回合/终止条件/预算与重试语义；与我们的 Planner/Developer/Tester、
   `step_limit`、wrap-up/repair 重试的**结构差异**。
4. **证据与验证**：它把什么当"证明"、怎么判定完成、有没有类似我们的证据分区/可启动闸门/QA 三件套。
5. **工具与 MCP 层**：`tools/godot-mcp`、`_vendor/godot_mcp` **到底是什么**——
   **重点核实它与我们引擎的 `modules/mcp_server` 是否同源/同契约**（工具名、前缀、scope、schema）；
   若同名同形，给出**版本/来源对照**（它是快照？旧版？分支？）。
6. **模型/提供方抽象**：怎么接模型、是否多提供方、超时/重试/密钥卫生；与我们的
   `openai_compatible` + `HOH_MODEL_API_KEY` 差异。
7. **配置、打包、可观测性**：`configs/`、日志/轨迹/指标、以及是否有我们没有的
   `benchmarks`/`policies`/`templates` 机制。
8. **许可与合规**：`LICENSE`(Apache-2.0)、`NOTICE`、`THIRD_PARTY_NOTICES.md` 与 `_vendor` 的条款；
   **明确区分**"可采用的**概念/设计**"与"需遵守许可的**代码**"（我们是 Rust，多数情况只借概念，但必须说清）。
9. **可采纳清单**：编号条目，每条给 **what / why / 证据(file:line) / 成本 / 风险 /
   是否与 §1 硬约束冲突 / 建议优先级(P0..P3)**。
10. **明确不建议采纳清单**：hof-lite 做了而我们**有意不做**的事，附理由（避免"照搬"）。
11. **我们完全缺失的能力**：按对 hof-rs 的价值排序，给出"若要引入"的最小落地设想。

## 4. 纪律（硬性）

- **只读**：不得修改 `F:\HarnessOfHarness` 任何文件；**不得运行**其任何脚本/入口
  （它需要 `GAMELOOP_HOME`/`BENCH`/凭据，且本任务**联网禁止**）。
- **不得修改 hof-rs 的任何代码、测试、`.spec/**` 既有文档、`godot-mcp/**`**；
  你的唯一写入是 §5 的报告文件。
- **不联网**（含 pip/模型端点）；不新增依赖；不 `git commit`/`push`/stage。
- **不得编造**：无法读到就写"未读到/无法判定"，**不要把推断写成实测**。
- 区分**证据**与**你的解读**，二者分栏或分标记。

## 5. 报告结构（写到 `.spec/hof-rs/tasks/TASK-HOHLITE-REPORT.md`）

1. 结论摘要（≤15 行，含"最值得采纳的 3 条"）；2. §3.1 总览 + 一次迭代时序；
3. §3.2 架构对照表；4. §3.3–3.7 逐项（证据 + 解读分离）；
5. §3.8 许可与合规；6. §3.9 **可采纳清单**（编号表）；7. §3.10 不建议采纳清单；
8. §3.11 缺失能力；9. **未读到/无法判定清单**；10. **我给决策者的建议排序**（P0..P3 及理由）。

**回报给父代理只有一行：报告文件路径。**