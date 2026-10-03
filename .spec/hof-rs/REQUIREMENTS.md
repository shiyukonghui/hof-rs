# REQUIREMENTS — hof-rs（Harness-of-Harness 的 Rust 复刻）

- 状态：**v0.3（2026-09-28，引擎换代，D216；v0.2 正文除 §3 硬约束与下列条目外不变）**
- 变更：v0.2 关闭全部 OPEN 项（用户已确认 OPEN-1/6/7，OPEN-2/3/4/5/8 按建议采纳并实测验证）
- 变更（v0.3）：**C3/C4/C5 重写**（引擎改为我们的 MCP 原生构建、通道去掉 GDExtension 插件、模型改为配置声明的 OpenAI 兼容端点）；
  A4、OPEN-4、§1、§7 前置说明、§9 术语 H 同步修订；新增 §10 修订记录。
  **`PRD-mario.md`（冻结的 S）一字未改**，其 P1「Godot 4.7.x」由 C3 取代（见 §10）。
- 依据：`2609.01481v1.pdf_by_PaddleOCR-VL-1.6.md`（HoH 论文 1126 行全文）
- 落点：`F:\moonbit-hof-rs`
- Agent 核心：`F:\RustProjects\mini-swe-agent-rust-mini\rust`（crate `mini_swe_agent`，本文件简称 mini）

---

## 1. 目标（自上而下）

**根本目的**：把论文的 Harness-of-Harness **运行时语义**在 Rust 里落地成可运行、可验证、可演化的工程系统，
使一个固定的 harness–model 配置（mini + 配置声明的模型端点）能被组织进「规划–开发–测试」循环，跨轮携带
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
| C3 | **Godot 引擎使用我们自己的 MCP 原生构建**（不是官方发行版）：`F:\moonbit-hof-rs\godot-mcp\godot\bin\godot.windows.editor.x86_64.mono.exe`，实测版本串 `4.8.dev.mono.custom_build.ba1587c71`（构建于 anchor `ba1587c71`）。编辑器端点固定 9877，**启动时必须显式传 `--mcp-port=9877`**。<br>历史（D216 取代）：C3 原钉官方 `Godot_v4.7.1-stable_mono_win64`。**版本串只记录、不写进代码、不作为判据**（C12：换版本不得要求改 `src/**`） |
| C4 | Godot 工具通道 = **引擎内置的 `modules/mcp_server` 原生模块**（四通道前缀契约，177 工具），`POST http://127.0.0.1:9877/mcp`，JSON-RPC 2.0；**需用户保持该编辑器打开**。<br>**不再使用** GDExtension 插件 `addons/godot_mcp_rs`（它与原生模块争同一端口 9877，且 `.godot/extension_list.cfg` 缓存会让它即使未启用也加载）。<br>**游戏进程是独立端点**：`running_game_*` 类工具只在游戏端点（`editor_play_scene` 注入的 `--mcp-port`）上可达，编辑器端点不提供 |
| C5 | 模型：**配置声明的 OpenAI 兼容端点**（`model.base_url` / `model.model_name` / `model.wire_model_name`）。当前配置＝远端 `http://100.105.152.101:18080/v1`，模型 `deepseek-v4.1-flash`，实测 `finish_reason=tool_calls` 正常、`usage` 完整。<br>密钥经环境变量 `HOH_MODEL_API_KEY`（其次 `OPENAI_API_KEY`）提供（C11）；**端点可用性与密钥均属配置面**。<br>本地 LM Studio（`http://127.0.0.1:1234/v1`，`qwen/qwen3.8-27b`）仍为受支持备选，换回只改配置 |
| C6 | 文档中文、代码与标识符英文；每个阶段结束 `git commit`，提交信息对应 `DECISIONS.md` 条目 |
| C7 | 证据只来自**公开**信息：spec S、D_t、A_t、公开执行记录；私有评分永不进入 prompt 或 E_t |
| C8 | token 统计必须从 `Message.extra["response"]["usage"]` 提取（mini 已持久化完整 ChatResponse）；不得依赖 `cost` 字段（本地模型无单价，cost 恒为 0） |
| C9 | **上线模型标识由配置显式声明（`model.wire_model_name`），且必须有双重锁定**：① 离线测试用假 HTTP 服务断言上线请求体里的 `model` 字段**逐字等于**它；② `hoh doctor` 的 chat 探测断言**响应里的 `model` 字段**等于它。**禁止**在代码里硬编码某个具体模型 id（换模型必须只改配置）。<br>历史教训（D6）：mini 的 `effective_model_name` 会按前缀表剥掉 `qwen/`，若上线 id 被悄悄改写，LM Studio 会额外加载第二个实例（显存翻倍）。该风险由上述双重锁定覆盖 |
| C10 | `model.provider` 必须**显式**写 `openai_compatible`；否则 `infer_provider()` 可能误判（例如 `qwen/...` 被判成 `aliyun`），请求不会打到目标端点 |
| C11 | **密钥不得入库**。`config/hoh.yaml` 中 `model.api_key` 必须为空；密钥通过进程环境变量提供（优先 `HOH_MODEL_API_KEY`，其次 `OPENAI_API_KEY`），由 Runtime 在加载配置时回填进传给 mini 的 model JSON 与 doctor 探测。<br>`.gitignore` 必须覆盖 `.env` / `*.env` / `config/*.secret*`。日志、轨迹、`meta.json`、`evidence.json` 与任何 prompt 中**禁止**出现密钥明文 |
| C12 | 换模型/换端点属**配置变更**，不得要求改 `src/**`：凡与具体模型或厂商绑定的检查（如 LM Studio 专有的 `/api/v0/models` 常驻实例检查）必须**按端点能力条件化**，不适用时报告为 `skipped`（`ok=true` + detail 说明），**不得**阻断 run |

---

## 4. 用户未明说但默认成立的假设（需逐条确认）

| 编号 | 假设 | 若假设不成立的影响 |
|---|---|---|
| A1 | 「复刻 HoH 架构」= 复刻 **Runtime 语义与三角色循环**，不是复现论文数值 | 若要求复现数值，则需接入 benchmark 与云端强模型，本项目范围完全改变 |
| A2 | mini 是**被包裹的 harness**，HoH 不改它（论文 3.2/3.4 的核心主张） | 若可改，架构耦合方式与可验证性都变 |
| A3 | 开发能力走**可插拔 project adapter**；Godot 只是第一个 adapter | 若硬编码 Godot，则阶段一可用，长期演化性丧失 |
| A4 | 真实运行前，用户保证：①**我们的 mono 构建编辑器**已在 `F:\moonbit-hof-rs\.workspace\mario` 打开并监听 9877；②模型端点在线且密钥已在环境变量里 | 否则阶段二无法执行，只能停在阶段一。**引擎身份由 DR-44 的闸门自动核对**，不再靠人工保证 |
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
| OPEN-4 | Godot 工程落点 `F:\moonbit-hof-rs\.workspace\mario`（`.gitignore` 排除）；`A_0` = 空 Godot 工程（`config/features=("4.8")`），**不含 `addons/godot_mcp_rs`**——MCP 由引擎自带的原生模块提供（C4，D216 修订） | 建议采纳 |
| OPEN-5 | **tool-calls 模式**。实测 `qwen/qwen3.8-27b`：`finish_reason=tool_calls`，正确产出 `bash` 调用；`usage` 完整回传（327/60/387）且含 `reasoning_tokens`；单次延迟约 2s。无需退化到 text-based | 2026-09 实测 |
| OPEN-6 | 阶段一验收**必须含 T=1 真实 smoke run** | 用户确认 |
| OPEN-7 | **HoH 代码单独建仓**（`F:\moonbit-hof-rs`，`git init`，按阶段 commit）；**Godot workspace 不进 git** | 用户确认 |
| OPEN-8 | 离线测试**主用 FakeModel/FakeEnvironment**；另留 2~3 个「带真实依赖」的标记测试（真 Godot MCP / 真 LM Studio）；**v1 不自建 mock MCP 服务器**，避免 mock 与 175 个真实工具行为漂移导致假阳性 | 建议采纳 |

### 7.1 由 OPEN 结论派生的布局约定

**当前固定配置 H（2026-09 变更，见 DECISIONS D15）**：

| 项 | 值 |
|---|---|
| 端点 | `http://100.105.152.101:18080/v1`（OpenAI 兼容） |
| 上线 model 字段 | `deepseek-v4.1-flash` |
| `provider` | `openai_compatible`（显式） |
| 密钥 | `HOH_MODEL_API_KEY` 环境变量（**不写入仓库**，C11） |
| 实测 | tool calls 正常（`finish_reason=tool_calls`）；`usage` 完整（292/52/344，含 `reasoning_tokens`）；单次约 0.9s |

> 本地 LM Studio（`qwen/qwen3.8-27b`）仍为受支持的备选配置（`model_name: openai/qwen/qwen3.8-27b` +
> `wire_model_name: qwen/qwen3.8-27b` + `base_url: http://127.0.0.1:1234/v1`），换回只需改配置（C12）。

```text
F:\moonbit-hof-rs\            <- HoH 代码仓（git；每阶段 commit 对应 DECISIONS.md 条目）
  .spec\hof-rs\               <- 需求/设计/验收工件
  .workspace\mario\           <- A_0 起点（gitignore，不进版本控制）
  runs\<run-id>\              <- 运行记录（gitignore）
    iter-1\{plan.md, evidence.json, traj\*.json, logs\*, snapshot\}
    versions\index.json       <- R10 的版本索引
  src\ ...                    <- Runtime 实现
```

> 阶段二真实运行的前置外部条件（用户负责，D216 修订）：**我们的 mono 构建编辑器**打开 `.workspace\mario` 并监听 9877
> （`godot.windows.editor.x86_64.mono.exe --path <ws> --mcp-port=9877`）；模型端点在线且 `HOH_MODEL_API_KEY` 已在环境变量中。
> 该编辑器**同时**是 MCP 通道提供者与游戏端点的父进程（`editor_play_scene` 为子进程注入 `--mcp-port`）。
> 备注：本地 LM Studio 已不再是必需品（C5）。

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
| H | 固定 harness–model 配置 | mini + 配置声明的模型端点（当前远端 `deepseek-v4.1-flash`）（配置冻结，不随轮次改变） |
| Runtime | 确定性契约执行者 | 本仓库 Rust 代码：权限、冻结、快照、schema、记录 |

---

## 10. 修订 v0.3（D216）：引擎换代与工具契约断层

**触发**：用户裁决改用「我们自己加了 MCP 模块的构建版本」（D216），并要求模型走远端
`http://100.105.152.101:18080/v1` 的 `deepseek-v4.1-flash`。

**模型半边：本就已就绪，无需改动**（实测取证）：`config/hoh.yaml` 的
`base_url`/`model_name`/`wire_model_name` 与要求逐字一致；`GET /v1/models` 返回唯一模型
`deepseek-v4.1-flash`；带 `tools` 的 `POST /v1/chat/completions` 返回
`finish_reason=tool_calls` 且参数正确。**注意**：密钥只经**环境变量**注入
（`API_KEY_ENV_VARS = ["HOH_MODEL_API_KEY","OPENAI_API_KEY"]`），hof-rs **不自动读**
`config/model.secret.env`（该文件只是给人 source 的，已被 `.gitignore` 覆盖）。

**引擎半边：实测到一个必须先解决的契约断层（本次真正的工程量）**：

| | 旧（hof-rs 现用） | 新（我们的构建） |
|---|---|---|
| 契约源 | `tests/fixtures/mcp/tools_list.json`（48,749 B） | `godot/modules/mcp_server/docs/tools_list.renamed.json` |
| 工具数 | 174 | **177** |
| 命名 | 无前缀（`play_scene`、`get_editor_errors`、`capture_frames`…） | 四通道前缀（`editor_play_scene`、`project_get_info`…） |

双向核对结论：hof-rs 现行使用的工具名在**新契约里全部不存在**；且 174→177 含 GDR-17
取消合并产生的**拆分**与 `update_` 禁用改名，**不是纯改名**。仓内耦合实测约 **270 行 / 24 个文件**
（`src/adapter/godot.rs` 97、`tests/evidence_battery.rs` 40、其余分散）。

**附加条款（用户裁决）**：
1. **不保留旧名兼容层**——全仓只保留一套词汇（四通道前缀）；禁止别名映射。
2. **`PRD-mario.md` 一字不改**——它是冻结的 S；其 P1「Godot 4.7.x」由 C3 **取代**（引擎版本是硬约束，不是产品需求）。
   因此 `meta.json.spec.sha256` 必须仍为 `4c81c3a9…5c3a`，改动 PRD 即违约（并会使历史轮次证据不可比）。
3. 批次落地：**批次一 = 纯离线迁移**（`cargo test` 为判据）；**批次二 = 真机 T=1 冒烟**，两批各自独立验收。
   设计条款见 `DESIGN-DETAIL.md` §13（DR-41..DR-47）。

**尚未关闭的风险（诚实列账）**：
- 新契约里 23 个工具是**游戏端点独有**，编辑器端点不可达 ⇒ hof-rs 的输入回放/监控设计必须改为双端点（DR-43）；
- `.workspace/mario` 里残留的 addon 与 `.godot/extension_list.cfg` 缓存必须先清理，否则仍是双绑定（DR-41）；
- 「活体 `tools/list` 与夹具逐字一致」这一条**离线批次无法证明**，留给批次二。

---

# DR-80 注（追加式，2026-10-02）

> **规则**（`DECISIONS.md` **D289**）：对冻结文档的更正**只能追加**——**只追加、不改原文、不改证据字符串**，
> 被取代的原句**逐字保留并标注** `superseded` / `incorrect`。本节因此**不动 C3 原句一字**（第 58 行原样），
> 只在此处给出正确读数、证据与判据口径。触发：目标级验收 `tasks/OBJECTIVE-ACCEPTANCE.md` 的 **OA-4**
> 与本批任务书 `tasks/TASK-DR80.md` ②。口径：本节数字全部来自 `runs/**` 与 `.spec/**` 的**只读复算**。

## 1. 被取代的原句（C3，第 58 行；逐字保留，标注 `superseded`）

```text
实测版本串 `4.8.dev.mono.custom_build.ba1587c71`（构建于 anchor `ba1587c71`）
```

就**当前安装的那支引擎二进制**而言，这半句已**不成立**（`incorrect`）；完整 C3 行仍在第 58 行**一字未改**。

## 2. 差异不是笔误，而是引擎被换过一次

| 构建 | 版本串 | 二进制 sha256 | size |
|---|---|---|---|
| `smoke-t6` 及更早（旧构建） | `4.8.dev.mono.custom_build.ba1587c71` | `25d29eb4…` | 194,207,744 |
| `smoke-t7` 起至今（**现行**） | `4.8.dev.mono.custom_build.035edfce7` | `08483088…` | 194,216,960 |

出处（逐字）：`tasks/TASK-SMOKE-T7-REPORT.md` 第 387 行「引擎 | `4.8.dev.mono.custom_build.ba1587c71`，
sha256 `25d29eb4…`，size 194,207,744 | **`4.8.dev.mono.custom_build.035edfce7`**，sha256 `08483088…`，
size 194,216,960 | 变了：换到含 TASK-151 修复的构建」。

C3 的这半句记录的是**换引擎之前**那支构建的真机读数（同一串见 `tasks/TASK-DR41-IMPL.md`、
`tasks/TASK-DR47-SMOKE-REPORT.md`、`tasks/TASK-DR47-ACCEPTANCE.md`）；引擎在 T7 前被替换时，
`REQUIREMENTS.md` 没有回头更新，于是 C3 的"实测"停在旧构建上。**这是文档陈旧，不是代码缺陷**：
`src/**` 从不硬编码版本串（C12；`tasks/TASK-DR41-ACCEPTANCE.md` 的 R9 以 `rustc.exe` 替身实测过 0 命中）。

## 3. 实测值与其证据文件

| 事实 | 实测值 | 证据文件（只读） |
|---|---|---|
| 版本串（**身份判据**） | `4.8.dev.mono.custom_build.035edfce7` | `runs/smoke-t11/meta.json`、`runs/smoke-t12/meta.json`、`runs/smoke-t13/meta.json` 的 `.engine.version_string` |
| 同上（原始捕获，含 `--version` 语义） | 同值 | `runs/smoke-t11/evidence/round/prerun_state.txt` 第 24 行 `VERSION_STRING=…` |
| 二进制 sha256 | `08483088a4a2772841cd3b4c916b2d45b3cb6255656cf3951598a86fce7e9e6a` | 同上第 23 行 `SHA256=…` |
| 二进制 size（字节） | `194216960` | 同上第 20 行 `SIZE=…` |
| 二进制 mtime（unix） | `1790641862` | 同上第 21 行 `MTIME_UNIX=…` |
| 启动横幅 | `Godot Engine v4.8.dev.mono.custom_build.035edfce7 (2026-09-29 00:01:57 UTC)` | `tasks/TASK-SMOKE-T11-REPORT.md` 第 96 行、`tasks/TASK-SMOKE-T13-REPORT.md` 第 111 行 |
| 引擎源码锚点存在性 | 提交 `035edfce7f7a18cbd6d2ab79069151d798ce0d86` 是嵌套仓 `HEAD` 的祖先 | `git -C godot-mcp/godot merge-base --is-ancestor 035edfce7 HEAD` → exit 0 |

复现命令：

```bash
python -c "import json;print(json.load(open(r'runs/smoke-t13/meta.json',encoding='utf-8'))['engine']['version_string'])"
# -> 4.8.dev.mono.custom_build.035edfce7
python -c "import json;[print(r, json.load(open('runs/%s/meta.json'%r,encoding='utf-8'))['engine']['version_string']) for r in ('smoke-t11','smoke-t12','smoke-t13')]"
grep -n 'VERSION_STRING\|SHA256\|SIZE\|MTIME_UNIX' runs/smoke-t11/evidence/round/prerun_state.txt
git -C godot-mcp/godot merge-base --is-ancestor 035edfce7 HEAD ; echo $?     # 0
```

## 4. 判据口径：判据(1) 以**实测串** `035edfce7` 为准

**目标原文自己点的就是该串**——`OBJECTIVE-COMPLETION.md` 第 11 行：

```text
- **必须为真**：在引擎 `4.8.dev.mono.custom_build.035edfce7` 上，`hoh init` 一个**全新空白工程**后，
```

每一轮任务书（`TASK-SMOKE-T7/T8/T9/T10/T11/T12`）与每一轮报告也都把 `035edfce7` 写作**判据**、
把二进制 sha256 只作记录（例如 `tasks/TASK-SMOKE-T11.md` 第 35 行：「引擎身份 = `--version` 字符串
`4.8.dev.mono.custom_build.035edfce7`（**判据**；sha256 仅记录）」）。⇒ 本轮起，
**C3 的"实测版本串 `ba1587c71`"一律读作 `superseded`（就现行引擎而言亦 `incorrect`），
判据以 `035edfce7` 为准**。

C3 自带的"版本串只记录、不写进代码、不作为判据"**仍然成立**：它的意思是**代码不得硬编码版本串**
（C12：换版本不得要求改 `src/**`），**不是**说轮次的引擎身份无需核对——轮次判据一贯是 `--version`
字符串逐字相符，这也正是本差异必须记下来的原因（否则"引擎身份与规格一致"这类论证会在文档层被削弱）。
C3 的其余内容（引擎是自建 MCP 原生构建、二进制路径、编辑器端点 9877、`--mcp-port=9877`、
非官方发行版、D216 取代史）**均不变**。

## 5. 同族未改的陈旧落点（只登记，本批按任务书**不改**）

- `DESIGN-DETAIL.md` 第 1508、1587 行同样记 `ba1587c71`；
- `tasks/TASK-DR41-IMPL.md` 第 39、140 行同样记 `ba1587c71`；
- `tasks/TASK-DR41-ACCEPTANCE.md`、`tasks/TASK-DR47-*` 是**当时的**历史记录（它们对**当时**的二进制为真），
  按追加式规则**不改**。

本批只处理 `REQUIREMENTS.md`；其余同族陈旧读数留待一次显式划定范围的清理，已作为遗留项登记在
`tasks/TASK-DR80-REPORT.md`。

# DR-89 注（追加式，2026-10-03）——E5 的读数已强于该行文本；追加不改封印前缀

上方 E5 行（`| E5 | QA 未修改 A_1（快照 hash 前后一致） | 快照 hash 对比 |`）的**文本**只主张
「快照 hash 前后一致」。自 DR-88 起，**代码强于该口径**（实现的逐条读数见 DR-89 报告）：

- **E5 的实际读数**：一轮通过 E5，当且仅当 `ok == true`，且 `qa_contaminated_*` 与 `qa_wrote_cache_*`
  两族警告**皆缺席**（`tests/godot_smoke.rs::e5_qa_did_not_modify_the_artifact`；离线同形读数
  `tests/evidence_binding.rs::qa_write_warnings`，与 E5 用同一条过滤规则）。哈希相等仍是必要条件，
  但不再是充分条件。
- **为什么**：适配器配置的被排除目录（`config/hoh.yaml` 的 `.godot`、`.import`；运行时恒定排除的
  `.hoh`/`.git` 不进观察）不在 `hash_tree` 的覆盖内——R10 要求 `version_id` 稳定，所以它们**不能**进哈希。
  运行时因此在 QA 窗口两侧各取一次这些目录的**非哈希清单**；候选视图内出现、改变或消失的缓存文件会被
  移出视图并留证，以 `qa_wrote_cache_candidate` 具名，并以
  `ContractViolation::QaContaminatedCandidate` **拒绝该轮**（`ok=false` / `reason=contract_violation` /
  `failed_role=tester`）。**保留拒绝、不放宽**（R4/R13 决定）。
- **本观察的边界，及其对判据的后果**：清单只覆盖**候选视图**——它是运行时为 QA 构建的、且是 Tester 的
  cwd、没有其他写者。**工作区**（`.workspace/**`）里同样被排除的缓存目录仍**不被观察**，因为那里的写者
  可能是用户的长期编辑器（D294）；把 watch 扩到工作区会用非角色的写制造假红，故**不扩**。
  **后果**：在工作区缓存目录里发生的写仍然读作 `ok=true` 且无 `qa_*` 警告。因此 E5 的合规读数始终是
  「就哈希所覆盖的集合、以及**候选视图内**的被排除目录而言」，**不是**「字节级不可能有写」。
- 封印：本文件 20,910 B / `7b551ca0…` 的封印前缀逐字未动，本注按 D289 **追加**在本文件末尾。
