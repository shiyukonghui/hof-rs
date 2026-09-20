# REQUIREMENTS — hof-rs（Harness-of-Harness 的 Rust 复刻）

- 状态：**v0.2 评审稿，待用户最终确认**（未确认不得进入概要设计）
- 变更：v0.2 关闭全部 OPEN 项（用户已确认 OPEN-1/6/7，OPEN-2/3/4/5/8 按建议采纳并实测验证）
- 依据：`2609.01481v1.pdf_by_PaddleOCR-VL-1.6.md`（HoH 论文 1126 行全文）
- 落点：`F:\moonbit-hof-rs`
- Agent 核心：`F:\RustProjects\mini-swe-agent-rust-mini\rust`（crate `mini_swe_agent`，本文件简称 mini）

---

## 1. 目标（自上而下）

**根本目的**：把论文的 Harness-of-Harness **运行时语义**在 Rust 里落地成可运行、可验证、可演化的工程系统，
使一个固定的 harness–model 配置（mini + 本地 qwen）能被组织进「规划–开发–测试」循环，跨轮携带
**产物状态 A_t** 与 **证据状态 E_t**，最终在 Godot 里自主开发出一个马里奥式平台游戏。

**两层目标（用户给定，顺序不可颠倒）**：

| 阶段 | 目标 | 可判定的东西 |
|---|---|---|
| 一 | **Runtime 语义正确** | 权限边界、冻结候选、schema 违约重试、双通道状态、证据 verified/gap 划分、消融开关——全部由离线确定性测试证明 |
| 二 | **跑出好软件** | 真实运行（本地 qwen + Godot MCP）产出一个可启动、可玩的马里奥式关卡，并留下可复核的证据包 |

**成功标准**：

阶段一（Runtime 语义正确）：
1. R1–R13 每条语义都有离线测试（含反例）且全绿；
2. **附加要求（用户确认）**：至少一次 T=1 的真实 smoke run 跑通全链路
   （mini → LM Studio qwen → MCP → Godot），证明「测试全绿」与「真能跑」不是一回事。

阶段二（跑出好软件）：至少完成一轮真实 `Planner→Developer→QA` 循环，产出 `D_1`、Godot 工程增量、
`E_1` 证据包（含截图/回放/运行时节点证据），且每个 verified claim 都指向可复现的公共执行记录。

---

## 2. 非目标（明确不做）

1. **不复现论文分数**（GameCraft-Bench / FrontierSWE / ProgramBench 的数值与 Dominance 计算）。
2. **不实现 benchmark adapter**（神谕评分、隐藏测试、私有 rubric 一律不接入）。
3. **不实现 PXI 玩家体验问卷聚合**（论文附录 B.8）。
4. **首版不做 70 轮多日无人值守长跑**（论文案例规模）；T 可配置，首版 T=1~3。
5. **不做 Docker-in-Docker / GPU 直通**（论文附录 B.3 的 FrontierSWE 执行形态）。
6. **不修改 mini**（论文主张 HoH 建立在既有 harness 之上，不改其实现）。
7. **不做 3D FPS**（论文的 Fusepoint 案例）；首版目标是 2D 平台游戏。
8. 不做多租户、抗恶意代码级别的沙箱（单机单用户研究者工具）。

---

## 3. 硬约束（不可协商）

| 编号 | 约束 |
|---|---|
| C1 | Rust 实现，Windows 本机可编译可运行（`LocalEnvironment` 在 Windows 走 `cmd.exe`，命令需跨平台或显式 Windows 优先） |
| C2 | mini 作为 **Cargo path 依赖**复用其 library API（`Model`/`Environment`/`DefaultAgent`/`AgentConfig`/`config`），**零改动** |
| C3 | Godot 4.7.1 mono：`D:\Program Files\Godot_v4.7.1-stable_mono_win64\Godot_v4.7.1-stable_mono_win64` |
| C4 | Godot 工具通道：Godot MCP Pro（GDExtension），`POST http://127.0.0.1:9877/mcp`，JSON-RPC 2.0；**需用户保持编辑器打开且插件已启用** |
| C5 | 模型：LM Studio，`http://127.0.0.1:1234`，模型 `qwen/qwen3.8-27b`；无云端 API key |
| C6 | 文档中文、代码与标识符英文；每个阶段结束 `git commit`，提交信息对应 `DECISIONS.md` 条目 |
| C7 | 证据只来自**公开**信息：spec S、D_t、A_t、公开执行记录；私有评分永不进入 prompt 或 E_t |
| C8 | token 统计必须从 `Message.extra["response"]["usage"]` 提取（mini 已持久化完整 ChatResponse）；不得依赖 `cost` 字段（本地模型无单价，cost 恒为 0） |

---

## 4. 用户未明说但默认成立的假设（需逐条确认）

| 编号 | 假设 | 若假设不成立的影响 |
|---|---|---|
| A1 | 「复刻 HoH 架构」= 复刻 **Runtime 语义与三角色循环**，不是复现论文数值 | 若要求复现数值，则需接入 benchmark 与云端强模型，本项目范围完全改变 |
| A2 | mini 是**被包裹的 harness**，HoH 不改它（论文 3.2/3.4 的核心主张） | 若可改，架构耦合方式与可验证性都变 |
| A3 | 开发能力走**可插拔 project adapter**；Godot 只是第一个 adapter | 若硬编码 Godot，则阶段一可用，长期演化性丧失 |
| A4 | 真实运行前，用户保证 Godot 编辑器 + MCP 插件在线、LM Studio 在线 | 否则阶段二无法执行，只能停在阶段一 |
| A5 | S（马里奥 PRD）是**权威需求源**，其质量直接决定 QA claim 的质量；S 要么用户提供、要么我们起草后经用户确认冻结 | 若 S 模糊，QA 只能产出低价值证据，HoH 退化为普通的「多轮写代码」 |
| A6 | 单用户、单机、串行运行；不做并发多项目调度 | 若需并发，Runtime 的 workspace/快照/端口策略需重设计 |
| A7 | 「集成到 Godot 中的 MCP」指的是 **godot-mcp-pro 本身**（已存在的开发者工具），HoH 通过它操作 Godot；**不是**要求把 HoH 做成 Godot 内的 MCP | ✅ **用户已确认**：HoH 是独立编排器，MCP 是它使用的工具通道 |
| A8 | 被开发产物的版本化由 **HoH 自己实现**（内容寻址快照 + 版本索引 + 回滚），不外包给 git | ✅ 用户已确认「Godot workspace 不进 git」；这也更贴论文「versioned project histories」的语义 |

---

## 5. 必须实现的 Runtime 语义（阶段一的可验收清单）

每条都是离线确定性测试的对象（FakeModel/FakeEnvironment，不联网）。

| 编号 | 语义 | 反例（必须被拒绝或显式记录） |
|---|---|---|
| R1 | **三次独立调用**：每轮 Planner→Developer→QA 顺序固定，每次是**全新 agent 实例**，不共享对话上下文 | 复用上一角色的 messages 即违约 |
| R2 | **Planner 只读**：Planner 阶段对 A 无写权限，产物只有 `D_t` | Planner 修改 artifact 文件 → 检测到并判失败 |
| R3 | **Developer 单写者**：只有 Developer 阶段可写 artifact；warm-start 从 `A_{t-1}` 而非 `A_0` | 其他角色写 artifact → 拒绝 |
| R4 | **QA 冻结候选**：QA 在 `A_t` 的只读快照上运行，快照身份（candidate id/hash）与证据绑定 | QA 修改快照 → 拒绝；证据归属错误候选人 → 判失败 |
| R5 | **双通道状态**：`A_t` 只流向下一轮 Developer，`E_t` 只流向下一轮 Planner；`D_t` 是**本轮共享**，不作为第三持久通道 | 下一轮 Planner 读到 `D_{t-1}` → 违约 |
| R6 | **schema 校验 + 有界重试**：Planner 输出必须含 `### Priority Order` / `### Preservation Gate` / `### Acceptance Gate`；QA 输出必须是合法 claim–evidence JSON | 违约 → 重试；重试耗尽 → 记为失败而非静默通过 |
| R7 | **证据模型**：`E_t = {verified[], gap[]}` 互斥划分；每条含 claim_id/claim/execution_records/status；gap 额外含 player_impact/recommended_update；handoff 含 preservation_constraints/update_targets/validation_requirements | 同一 claim 同时进两子集 → 违约 |
| R8 | **消融开关**：`w/o Plan Update`、`w/o Evidence Feedback`、`w/o Warm-Start` 各自只改一个跨轮输入 | 开关同时影响多处 → 不可解释 |
| R9 | **迭代预算与记录**：参数化 T；每轮落盘 `D_t`、harness 命令与过程日志、QA 报告、`A_t` 快照、用量统计 | 缺任一记录 → 不可审计 |
| R10 | **版本化与回滚**：HoH 自己实现被开发产物的版本库——每轮对 `A_t` 做内容寻址快照 + 版本索引，可回滚到上一个已验证状态（不依赖 git、不要求产物目录是 git 仓库）；HoH 自身代码则按阶段 git commit | 无历史 → 无法从大回归中恢复 |
| R11 | **公开性边界**：Planner/QA 的 prompt 与文件访问都不含私有评分、隐藏测试 | 注入私有信息 → 违约 |
| R12 | **用量统计**：按角色/轮次汇总 prompt/completion/total tokens（含 cache hit/miss） | usage 缺失时必须显式标 unknown，不得填 0 冒充 |
| R13 | **角色化工具边界**：Developer 具备写与执行；QA 具备执行与检查但不得改 A；工具集按角色裁剪 | QA 调用写工具 → 拒绝 |

---

## 6. 阶段二验收标准（真实运行）

| 编号 | 标准 | 证据形式 |
|---|---|---|
| E1 | 一轮完整循环真实跑通：Planner 产出合法 `D_1`；Developer 产出 Godot 工程增量；QA 产出合法 `E_1` | `runs/<run-id>/` 下全部工件 + 轨迹 JSON |
| E2 | 产出的 Godot 工程**可启动**（无编译/脚本错误） | MCP `play_scene` + `get_editor_errors` 输出 |
| E3 | 马甲核心可观察行为存在：玩家左右移动、跳跃、至少 1 个可交互对象、一个终点/胜负条件 | `simulate_sequence` 回放 + 前后截图 + `assert_node_state` |
| E4 | `E_1` 中每个 verified claim 都指向可复现的公共执行记录；无证据的 claim 必须落在 gap | 逐条对照报告 |
| E5 | QA 未修改 A_1（快照 hash 前后一致） | 快照 hash 对比 |
| E6 | 明确声明**未达成**的部分即视为诚实结论，不算失败；把未达成谎报为 verified 才算失败 | 人工复核 + 反例构造 |

> 说明：本地 27B 模型的能力不足以保证「像论文一样好」。阶段二的判据是**链路可用 + 证据可信 + 不自欺**，不是分数。

---

## 7. 已确认结论（原 OPEN 项，全部关闭）

| 编号 | 结论 | 来源 |
|---|---|---|
| OPEN-1 | **HoH 是独立 Rust 编排器**，在任意项目上运行；Godot 只是第一个 project adapter；godot-mcp-pro 作为它使用的工具通道 | 用户原话：「godot-mcp-pro 存在 mcp 工具可以用来给 hoh 使用，以便进行游戏开发」 |
| OPEN-2 | **瘦 CLI 桥**：HoH 提供 `call` 型命令（一条命令 = 一次 JSON-RPC 工具调用到 `127.0.0.1:9877`），Developer/QA 通过 mini 的 shell 动作使用；工具清单按角色裁剪；原生 tool-call 化列为演进项 | 建议采纳 |
| OPEN-3 | **由我起草马里奥 PRD v1**，交用户确认后冻结为 S；冻结后只读，轮次间不得修改 | 建议采纳 |
| OPEN-4 | Godot 工程落点 `F:\moonbit-hof-rs\.workspace\mario`（`.gitignore` 排除）；`A_0` = 空 Godot 4.7 工程 + `addons/godot_mcp_rs` 插件骨架 | 建议采纳 |
| OPEN-5 | **tool-calls 模式**。实测 `qwen/qwen3.8-27b`：`finish_reason=tool_calls`，正确产出 `bash` 调用；`usage` 完整回传（327/60/387）且含 `reasoning_tokens`；单次延迟约 2s。无需退化到 text-based | 2026-09 实测 |
| OPEN-6 | 阶段一验收**必须含 T=1 真实 smoke run** | 用户确认 |
| OPEN-7 | **HoH 代码单独建仓**（`F:\moonbit-hof-rs`，`git init`，按阶段 commit）；**Godot workspace 不进 git** | 用户确认 |
| OPEN-8 | 离线测试**主用 FakeModel/FakeEnvironment**；另留 2~3 个「带真实依赖」的标记测试（真 Godot MCP / 真 LM Studio）；**v1 不自建 mock MCP 服务器**，避免 mock 与 175 个真实工具行为漂移导致假阳性 | 建议采纳 |

### 7.1 由 OPEN 结论派生的布局约定

```text
F:\moonbit-hof-rs\            <- HoH 代码仓（git；每阶段 commit 对应 DECISIONS.md 条目）
  .spec\hof-rs\               <- 需求/设计/验收工件
  .workspace\mario\           <- A_0 起点（gitignore，不进版本控制）
  runs\<run-id>\              <- 运行记录（gitignore）
    iter-1\{plan.md, evidence.json, traj\*.json, logs\*, snapshot\}
    versions\index.json       <- R10 的版本索引
  src\ ...                    <- Runtime 实现
```

> 阶段二真实运行的前置外部条件（用户负责）：Godot 编辑器打开该项目且已启用 `godot_mcp_rs` 插件（9877 监听）；
> LM Studio 在 `127.0.0.1:1234` 提供 `qwen/qwen3.8-27b`。当前实测：LM Studio ✅ 在线；9877 ❌ 未监听（编辑器未开）。

---

## 8. 复盘：处理这类问题时最常犯的错误

**把 HoH 做成「三个 prompt 串一圈的多智能体聊天」**。具体表现为：
1. 三角色共用一个对话/上下文（丢掉 R1、R4 的独立性前提）；
2. QA 直接读 Developer 的自我陈述当证据（丢掉「实现者不能证明自己」这一核心，论文 3.4.3）；
3. 只在最后一轮跑一次测试，而不是每轮都产出可审计的证据包（丢掉 R7、R9）；
4. 把 `D_t` 当持久状态往下传（丢掉 R5，且等于退化成论文消融里最差的一档）；
5. 只看「模型说完成了」而不做 schema 强制（丢掉 R6，HoH 的可验证性直接消失）；
6. 为了「快点跑起来」把 Godot 硬编码进 Runtime（丢掉 A3，阶段一通过后无法演化）。

第二个错误：**没有离线确定性测试路径**。整个系统依赖活着的 Godot 编辑器 + 本地模型，
若不能用 FakeModel/FakeEnvironment 复现循环语义，任何 bug 都无法定位，阶段一根本无法验收。

---

## 9. 术语表

| 记号 | 含义 | 本项目落点 |
|---|---|---|
| S | 公开规格（马里奥 PRD） | `spec/PRD.md`（冻结后只读） |
| A_t | 第 t 轮后的产物状态 | `workspace/mario/`（Godot 工程） |
| E_t | 第 t 轮的证据包 | `runs/<run>/iter-<t>/evidence.json` + QA 报告 |
| D_t | 第 t 轮的开发文档 | `runs/<run>/iter-<t>/plan.md` |
| H | 固定 harness–model 配置 | mini + LM Studio qwen（配置冻结，不随轮次改变） |
| Runtime | 确定性契约执行者 | 本仓库 Rust 代码：权限、冻结、快照、schema、记录 |
