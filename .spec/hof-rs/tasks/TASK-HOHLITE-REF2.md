# TASK-HOHLITE-REF2 — 按收窄范围重榨参考：**排除一切 godot-mcp**，聚焦 hoh-lite 的 core/harnesses/policies/benchmarks/templates

> 你是**侦察/参考子代理**，无上游对话上下文；**本文件是你的唯一任务来源**。
> **只读**对象：`F:\HarnessOfHarness`（HEAD `ae7cc6f`）。**不得修改、不得运行、不得联网。**
> 产物：`F:\moonbit-hof-rs\.spec\hof-rs\tasks\TASK-HOHLITE-REF2-REPORT.md`。

---

## 1. 范围裁决（**硬性，来自决策者 D237**）

- 参考范围**只**包括 hoh-lite 的 **`core` / `harnesses` / `policies` / `benchmarks` / `templates` / `adapters`**
  等**非 godot-mcp** 部分。
- **Godot MCP 部分整体排除**：vendored `satelliteoflove/godot-mcp`（v4.1.0、Node/TS、stdio、
  `ws://127.0.0.1:6550` addon、21 个 `godot_*` 工具）、`tools/godot-mcp`、以及**所有在其 MCP server 内实现的
  overlay patch 机制** —— **一律不作为参考来源，连概念也不借**。
- **我方引擎集成方式为准**：引擎内 `modules/mcp_server`、**HTTP POST `127.0.0.1:9877/mcp` JSON-RPC 2.0**、
  **177 条四前缀**契约（**冻结、逐字受门保护**）。
  **任何建议都不得**要求改引擎、换协议、动契约或新增工具。
- 若某条洞见**只能**通过其 godot-mcp 代码说明，**就丢弃它**（不要变相引入）。

## 2. 背景（必须先读）

`F:\moonbit-hof-rs` 是 Rust 实现（`hof-rs`）：三角色 Planner → Developer → Tester、证据分区
（`D_n`/`E_n`、verified/gap、candidate 绑定）、确定性证据电池与可启动闸门、退出码 `0/2/3/4/5/6`。
必读：`.spec/hof-rs/REQUIREMENTS.md`（v0.3）→ `DESIGN-OVERVIEW.md` → `DESIGN-DETAIL.md`（**§15 最新，v0.10**）
→ `ACCEPTANCE.md`（v2）→ `DECISIONS.md`（**D216..D237**，其中 **D236/D237** 是本线的裁决）。
**已有线索**（上一轮报告 `.spec/hof-rs/tasks/TASK-HOHLITE-REPORT.md` 是**线索，非证据**；
且其中 **godot-mcp 相关章节按本条已作废**）：其 `policies`/`benchmarks`/`templates` 是我们**完全没有**的概念。

## 3. 要产出什么（**证据优先**：逐条给 `路径:行` + 原文引用；推断与证据分栏）

1. **一次完整迭代的时序**：从入口到结束的阶段/产物/判定，**用其非 godot-mcp 代码**说明。
2. **`core`**：循环骨架、状态机、终止条件、预算与重试语义、错误处理与恢复（含"保留最后有效候选"一类）。
3. **`harnesses`**：抽象是什么、有哪些实现、如何插入（**与我们 Planner/Developer/Tester 的结构对照**）。
4. **`policies`（我们完全没有）**：定义、种类、在何处生效、**它与 harness 的边界**；
   给最小落地设想（Rust 侧要落在哪个模块、与现有闸门/电池如何共存）。
5. **`benchmarks`（我们完全没有）**：它如何定义/运行/汇总基准；**是否与我们的"证据电池"概念重叠或互补**；
   最小落地设想与其**风险**（尤其"神谕评分"的诱惑——我们是否需要）。
6. **`templates`（我们完全没有）**：模板管什么（提示？工程骨架？策略文件？）、如何版本化与校验。
7. **`adapters`**：适配器契约（它如何把"某个游戏/任务"接进来）；与我们的 `ProjectAdapter` 对照。
8. **`resources`/`configs`/`scripts`**：配置与资源的组织方式；值得借鉴的**约定**（不借代码）。
9. **可采纳清单**（编号表）：**what / why / 证据(file:line) / 成本 / 风险 /
   是否与 §1 硬约束冲突 / 建议优先级 P0..P3**。**每条必须与 godot-mcp 无关。**
10. **不建议采纳清单**：逐条给理由（避免照搬）。
11. **我们完全缺失的能力**：按价值排序 + 最小落地设想。
12. **未读到/无法判定**：如实列出（不得把推断写成实测）。

## 4. 纪律（硬性）

- **只读**：不改 `F:\HarnessOfHarness` 任何文件；**不运行**其任何脚本/入口（需 `GAMELOOP_HOME`/凭据）；
  **不联网**（含 pip/模型端点）。
- **不改 hof-rs 任何代码/测试/既有 `.spec/**`/`godot-mcp/**`**；唯一写入是 §5 的报告文件。
- 不 `git commit`/`push`/stage。不新增依赖。
- **不得编造**；读不到就写"未读到/无法判定"。
- **严禁**把 `assets/`（182 MB）或任何 godot-mcp 材料当作参考来源。

## 5. 报告结构

1. 结论摘要（≤15 行，含"最值得采纳的 3 条"，**且必须无一条与 godot-mcp 相关**）；
2. §3.1 一次迭代时序；3. §3.2–3.8 逐项（证据/解读分栏）；4. §3.9 **可采纳清单**；
5. §3.10 不建议采纳；6. §3.11 缺失能力；7. §3.12 未读到/无法判定；8. **我给决策者的建议排序**（P0..P3 + 理由）。

**回报给父代理只有一行：报告文件路径。**