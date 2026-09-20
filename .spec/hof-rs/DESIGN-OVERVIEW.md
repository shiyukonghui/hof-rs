# DESIGN-OVERVIEW — hof-rs 概要设计

- 状态：**评审稿 v0.1，待用户确认**（未确认不得进入详细设计）
- 输入：`.spec/hof-rs/REQUIREMENTS.md` v0.2（已确认）、`.spec/hof-rs/PRD-mario.md` v1（已确认）
- 输出目标：`.spec/hof-rs/DESIGN-DETAIL.md`（模块级签名与行为契约）

---

## 1. 设计主张（一句话）

**HoH = 一个确定性的 Runtime，把「一次角色调用」包装成「输入冻结 + 权限强制 + 产物校验 + 证据绑定」的事务；
角色本身是 mini harness 的一次完整调用，模型推理与工作流完全自由。**

展开成三条不可动摇的分层原则：

| 原则 | 含义 | 对应需求 |
|---|---|---|
| P-1 契约在 Runtime，不在 prompt | 权限、冻结、schema、证据绑定全部由代码强制；prompt 只写职责与产物要求 | R2 R3 R4 R6 |
| P-2 角色 = harness 调用 | 每个角色是同一固定 harness–model 配置的一次独立调用，不共享上下文 | R1 R13 |
| P-3 状态只走两条通道 | `A_t` 传下一轮 Developer，`E_t` 传下一轮 Planner；`D_t` 仅本轮共享 | R5 R9 R10 |

## 2. 架构分层

```text
┌──────────────────────────────────────────────────────────────────────┐
│ CLI (hoh)                                                            │
│   run / status / rollback / tools call|list|describe / doctor        │
└───────────────┬──────────────────────────────────────────────────────┘
                │
┌───────────────▼──────────────────────────────────────────────────────┐
│ Orchestrator（HoH 主循环，本文简称 Loop）                              │
│   for t in 1..=T:  plan → develop → test → record                     │
│   消融开关 Ablation{plan_update, evidence_feedback, warm_start}        │
│   负责：轮次编排、状态推进、失败决策、run 元数据                        │
└───────────────┬──────────────────────────────────────────────────────┘
                │  RoleInvocation
┌───────────────▼──────────────────────────────────────────────────────┐
│ Role Runtime（契约执行者，事务化）                                     │
│   ├─ ViewPlanner   为角色准备「视图目录」（cwd）与冻结输入             │
│   ├─ Policy        权限矩阵：单写者 / 只读 / 冻结 + 工具白名单         │
│   ├─ SchemaGate    产物 schema 校验 + 有界重试                        │
│   ├─ EvidenceBinder 候选身份（candidate_id）盖章与校验                │
│   ├─ Recorder      落盘 D_t / E_t / 轨迹 / 日志 / usage / 快照        │
│   └─ VersionStore  内容寻址快照 + 版本索引 + 回滚                     │
└───────────────┬──────────────────────────────────────────────────────┘
                │
     ┌──────────┴───────────┬────────────────────────┐
     ▼                      ▼                        ▼
┌─────────────┐   ┌──────────────────┐   ┌──────────────────────┐
│ Harness     │   │ ToolChannel      │   │ ProjectAdapter       │
│ (trait)     │   │ (trait)          │   │ (trait)              │
├─────────────┤   ├──────────────────┤   ├──────────────────────┤
│ MiniHarness │   │ McpCliChannel    │   │ GodotAdapter         │
│ = mini 的   │   │ = hoh tools call │   │ = Godot MCP 工具映射 │
│ DefaultAgent│   │   → HTTP JSON-RPC│   │   + 构建/启动/证据   │
│ + Model     │   │   → 127.0.0.1:9877   │                      │
│ + LocalEnv  │   │ ShellOnlyChannel │   │ TestAdapter(测试用)  │
└─────────────┘   └──────────────────┘   └──────────────────────┘
     │
     ▼  外部（用户负责在线）：LM Studio :1234 · Godot 编辑器 + godot_mcp_rs :9877
```

**为什么 harness / toolchannel / adapter 三者分离**：
- `Harness` 只管「把一段 prompt 变成一次 agent 执行」，与项目类型无关 → 满足 A2（mini 只是第一个实现）与未来换 harness（Codex 式 CLI）。
- `ToolChannel` 只管「角色能用哪些工具、如何调用、被拒绝时如何报错」→ 权限强制的**唯一收口**，与 Godot 无关。
- `ProjectAdapter` 只管「这个项目类型的 A₀ 长什么样、如何确定性构建/启动、如何采集证据」→ 满足 A3 与未来 Rust/其他项目目标。

## 3. 数据模型（跨模块契约）

```rust
Spec            { path, sha256 }                       // S，冻结后只读（记录 hash 进 run 元数据）
ArtifactState   { workspace: PathBuf, version_id, candidate_id }
DevelopmentDoc  { iteration, path, priorities[], preservation_gate, acceptance_gate }   // D_t
EvidenceBundle  { iteration, qa_status, verified: [Record], gap: [Record],
                  planner_handoff { preservation_constraints[], update_targets[], validation_requirements[] } }  // E_t
Record          { claim_id, claim, execution_records: [ExecRecord], status,
                  player_impact?, recommended_update? }
ExecRecord      { kind: screenshot|replay|runtime_trace|assert|build|log,
                  path, observation, candidate_id }
Usage           { role, iteration, calls, prompt_tokens, completion_tokens, total_tokens,
                  cache_hit_tokens, cache_miss_tokens, usage_known: bool }
RoleOutcome     { role, exit_status, submission, trajectory_path, usage, duration, written_paths[], view_dir }
```

不变式（SchemaGate 强制）：
1. `verified` 与 `gap` 的 `claim_id` 集合互斥（R7）；
2. 每条 `ExecRecord.candidate_id` 必须等于本轮 `ArtifactState.candidate_id`（R4）；
3. `Usage.usage_known == false` 时 token 字段必须为 `null` 而非 0（R12）；
4. 有 `status == gap` 的记录必须含 `player_impact` 与 `recommended_update`。

## 4. 关键机制的设计（论文机制 → 实现手段）

### 4.1 角色调用事务（R1）
`RoleInvocation { role, system_prompt, task_prompt, view_dir, env_vars, tool_policy, limits }`
→ `Harness::invoke()` → `RoleOutcome`。每次调用**新建** `DefaultAgent`（新 messages、新 cost 计数），
不同角色之间不传递任何 messages。测试用 FakeHarness 记录调用序列，断言「三次调用、零状态共享」。

### 4.2 权限强制：位置隔离 + 哈希校验 + 工具白名单（R2 R3 R4 R13）

| 角色 | cwd（视图目录） | 写权限 | 事后校验 |
|---|---|---|---|
| Planner | `runs/<id>/iter-<t>/planner-view/`＝ A_{t-1} 的副本 + S + `E_{t-1}` + 脚手架 | 可写**副本**；真实 A 天然不可达 | 真实 A 的树哈希前后必须相等 |
| Developer | **真实 workspace**（warm-start 于 A_{t-1}） | 唯一写者 | 记录前后哈希差 → 生成 `A_t` 与 `candidate_id` |
| Tester | `runs/<id>/iter-<t>/candidate/`＝ A_t 的**冻结副本** + S + D_t | 可写副本但**禁止**（哈希须不变） | 副本哈希必须不变，否则标记 QA 被污染 → 本轮判失败 |

为什么不用 OS 只读权限：Windows ACL 需要管理员/全局副作用，且不可移植、不可测。
**位置隔离是「预防」，哈希校验是「检测」**，两者都给，才既安全又可测。
代价：每轮两个副本（Godot 工程去掉 `.godot/`/`.import/` 缓存）。已知限制，写入详细设计作为可优化项。

工具白名单在 `ToolChannel` 内按角色强制：`hoh tools call --role`（或 `HOH_ROLE` 环境变量）
命中拒绝表即返回结构化错误，**不依赖 prompt 自律**。Planner：只读类工具 + 无 MCP 写工具；
Developer：全部项目/编辑/执行工具；Tester：只读 + 执行 + 证据采集工具，禁写类 MCP 工具。

### 4.3 产物校验与有界重试（R6）——双闸门
1. **内层（廉价自愈）**：提供 `hoh submit --role <role> --file <path>`，当场校验并返回精确错误
   （缺哪个 heading / 哪个字段非法），角色可在**同一次调用内**修好。角色 prompt 要求用它提交。
2. **外层（论文口径的有界重试）**：调用结束后 SchemaGate 再校验落盘产物；失败则把
   format-error 追加进消息并**重新发起该角色调用**，重试上限默认 2；耗尽则本轮标记失败并落盘原因，
   **绝不静默降级为「通过」**。

### 4.4 证据绑定（R4 R7 R11）
- `candidate_id = sha256(排序后的 (相对路径, 内容) 对)`，排除缓存目录。
- Runtime 在 Tester 调用后给每条 ExecRecord 盖章；Tester 自填的 candidate_id 不符 → 判失败。
- Tester 的视图里**不存在**任何私有评分/隐藏测试文件；prompt 与视图目录同时受 R11 约束（双保险）。

### 4.5 跨轮状态与消融（R5 R8）

| 开关 | 关闭时的行为 | 只影响 |
|---|---|---|
| `plan_update` | `D_t := D_1`（t>1） | Planner 输出 |
| `evidence_feedback` | Planner 收到空证据 | Planner 输入 |
| `warm_start` | Developer cwd = A₀ 的副本而非 A_{t-1} | Developer 起点 |

每个开关只改一个输入；离线测试逐一断言「除此之外其余输入逐字节相同」，防止把消融做成模糊开关。

### 4.6 版本化与回滚（R10）
`runs/<id>/versions/index.json`（版本链：iteration / role / version_id / candidate_id / 是否已验证 / 父版本）
+ `versions/<version_id>/`（内容寻址快照）。`hoh rollback --to <version_id>` 把 workspace 还原到该快照。
不依赖 git（用户确认产物不进 git）。已知限制：全量快照，非增量（可后续换硬链接/增量）。

### 4.7 用量统计（R12，不改 mini）
从每次角色调用的轨迹 JSON 中提取 `messages[*].extra.response.usage`，累加
prompt/completion/total/cache_hit/cache_miss，按角色与轮次落盘。usage 缺失 → `usage_known=false`。
注意：qwen3.8 是推理模型，`completion_tokens` 已包含 `reasoning_tokens`，全额计。

### 4.8 剧本式渐进披露 + 最小技能（论文 §3.2 / §5）
角色视图目录内含 `TOOLS.md`（按类别浓缩的工具索引 + 一例用法）与 `skills/*.md`
（`godot-dev.md`、`godot-testing.md` 两份最小技能）；工具细节用 `hoh tools describe <name>` 按需取。
不在 prompt 里塞 175 个工具定义（也避免把工具定义塞进 mini 的 tool schema 导致上下文爆炸）。

## 5. 技术选型

| 项 | 选择 | 理由 / 否决者 |
|---|---|---|
| 语言/版本 | Rust 2021 | 与 mini 一致 |
| 异步 | tokio（mini 已用） | 与 mini 同源；角色串行，无需并发框架 |
| Agent 核心 | `mini_swe_agent` path 依赖，`DefaultAgent` + `LlmConnectorModel` + `LocalEnvironment` | D1 |
| 模板 | **复用** `mini_swe_agent::template::render`（minijinja） | 零新增模板依赖，行为与 harness 一致 |
| CLI | clap derive | 与 mini 一致 |
| HTTP（MCP 客户端） | `ureq`（阻塞、轻量） | 工具桥是短命进程，阻塞最简；否决 `reqwest`（异步重、非必要） |
| 哈希 | `sha2` | 成熟、标准 |
| 目录遍历 | `walkdir` | 成熟、标准 |
| run-id | `uuid` v4 | 已在 mini 依赖图中，几乎零成本 |
| 错误 | `anyhow`（边界）+ `thiserror`（类型化错误） | 与 mini 一致 |
| 测试 | mini 既有 `MockModel`/`MockEnvironment` 范式 + `tempfile` | 复用已验证的测试基础设施 |
| JSON schema 校验 | 手写类型化校验（serde + 不变式代码） | 否决 `jsonschema` 库：本项目的 schema 小且需自定义不变式，引库是过度设计 |

配置：`config/hoh.yaml`（模型/端点/上限/角色模板路径/工具端点）经 mini 的 `get_config_from_spec` + `recursive_merge` 加载，可被 CLI `-c key=value` 覆盖。

**模型配置（已实测核对，必须在设计里写死）**：
```yaml
model:
  model_name: qwen/qwen3.8-27b
  provider: openai_compatible      # 不写会被推断为 aliyun（DashScope）→ 打不到 LM Studio
  service_name: openai_compatible
  base_url: http://127.0.0.1:1234/v1   # 客户端直接拼 {base}/chat/completions
  api_key: lm-studio               # 非空即可
  use_tool_calls: true
```
（`effective_model_name` 会把 `qwen/` 剥成 `qwen3.8-27b`；已实测 LM Studio 接受该裸 id 并归一化。）

## 6. 模块划分（概要级）

```text
src/
  main.rs            二进制入口
  cli.rs             子命令定义与分发（run/status/rollback/tools/doctor）
  config.rs          hoh.yaml 加载与 CLI 覆盖合并（复用 mini config）
  model.rs           数据模型 + 不变式校验（§3）
  runtime/
    loop.rs          Orchestrator：T 轮主循环与消融
    role.rs          Role / RoleInvocation / RoleOutcome
    invoke.rs        单次角色调用：建视图 → 建 agent → run → 收 usage/轨迹
    view.rs          视图目录构建（副本、排除缓存、注入 S/E/D/TOOLS/skills）
    policy.rs        权限矩阵与工具白名单裁决
    schema.rs        SchemaGate（外层校验 + 有界重试）
    evidence.rs      EvidenceBinder（candidate_id 盖章与校验）
    snapshot.rs      VersionStore（内容寻址快照、版本索引、回滚）
    usage.rs         usage 提取与汇总
    record.rs        每轮工件与 run 元数据落盘
  harness/
    mod.rs           trait Harness
    mini.rs          MiniHarness（唯一实现）
  tools/
    mod.rs           trait ToolChannel + 角色策略表
    mcp.rs           JSON-RPC over HTTP(ureq) 客户端
    cli.rs           `hoh tools call|list|describe` 实现
  adapter/
    mod.rs           trait ProjectAdapter
    godot.rs         GodotAdapter（MCP 工具 + 构建/启动/证据采集）
  prompts/
    planner.md developer.md tester.md
    skills/godot-dev.md skills/godot-testing.md
tests/               离线确定性测试（FakeHarness/FakeToolChannel/FakeAdapter）
tests/godot_smoke.rs 真实性依赖的标记测试（默认忽略，需显式开启）
```

## 7. 关键接口（概览级，详细设计给出完整签名）

```rust
#[async_trait] trait Harness: Send + Sync {
    async fn invoke(&self, inv: &RoleInvocation) -> Result<RoleOutcome>;
}

#[async_trait] trait ToolChannel: Send + Sync {
    fn allowed(&self, role: Role, tool: &str) -> bool;
    fn index_markdown(&self, role: Role) -> String;        // 生成 TOOLS.md
    async fn call(&self, role: Role, tool: &str, args: Value) -> Result<ToolResult>;
}

#[async_trait] trait ProjectAdapter: Send + Sync {
    fn initialize(&self, workspace: &Path) -> Result<()>;            // A₀ 骨架
    fn cache_excludes(&self) -> &[&str];                             // 副本排除项
    async fn build_check(&self, candidate: &Path) -> Result<Vec<ExecRecord>>;
    fn evidence_playbook(&self) -> &str;                             // 注入 Tester 的收集指引
    fn tool_policy(&self, role: Role) -> ToolPolicy;
}

struct Orchestrator { harness: Box<dyn Harness>, adapter: Box<dyn ProjectAdapter>,
                      tools: Arc<dyn ToolChannel>, store: VersionStore, cfg: HohConfig, /*
                      ablation: Ablation, spec: Spec, */ }
```

## 8. 备选方案与否决理由

| 编号 | 备选 | 否决理由 |
|---|---|---|
| ALT-1 | 三角色共享一个 agent/对话，靠角色切换 prompt | 破坏 R1/R4，直接丢掉论文的独立性前提（= 论文讨论的「实现者自我验证」缺陷） |
| ALT-2 | 权限靠 prompt 约定（「你不要修改代码」） | 不可强制、不可测试、不可追责；违反 P-1 |
| ALT-3 | 用 OS 只读权限/ACL 做冻结 | Windows 上需提权、不可移植、CI 不可测；改为位置隔离 + 哈希 |
| ALT-4 | Tester 直接在 A_t 上运行 | 违反冻结；观测可能跨版本混合，证据失效 |
| ALT-5 | 用 git commit/tag 做产物版本化 | 用户确认产物不进 git；且版本化应是 Runtime 职责（论文语义） |
| ALT-6 | 把 175 个 MCP 工具做成 mini 的原生 tool 定义 | tool schema 巨大且随插件漂移，上下文与 token 成本失控；瘦 CLI + 按需 describe 更经济 |
| ALT-7 | 自建 memory 模块/向量库 | 论文明确用文件系统渐进披露，无独立 memory 模块；引库违背设计意图 |
| ALT-8 | HoH 做成 Godot 内的 MCP 插件 | 用户已确认(A7)：HoH 是独立编排器；插件形态会让 Runtime 无法离线测试 |
| ALT-9 | 引入 `jsonschema` 做产物校验 | schema 小、需自定义不变式，引库是过度设计 |
| ALT-10 | 用 `reqwest` 做 MCP HTTP 客户端 | 异步重依赖，仅为短命 CLI 调用，不划算 |

## 9. 非功能性策略

| 维度 | 策略 |
|---|---|
| 性能 | 角色串行、单进程内 3 次 harness 调用/轮；副本排除 `.godot/`/`.import/`；MCP 调用为阻塞 HTTP（本地环回） |
| 可测性 | Harness / ToolChannel / ProjectAdapter / 时钟 / 随机 id 全部 trait 化或可注入；离线测试零网络 |
| 可维护 | 契约与推理分离（prompt 是 Markdown 资产，可独立迭代）；模块边界 = trait |
| 可演化 | 换 harness、换 tool channel、换项目类型均为新增实现，不动 Loop |
| 可追溯 | 每轮 `runs/<id>/iter-<t>/` 落盘 D/E/轨迹/日志/usage/快照；版本索引可回滚 |
| 边界安全 | R11 双保险：视图目录不含私有信息 + prompt 不含；工具白名单按角色强制 |
| 兼容 | Windows 优先（`PathBuf` 统一、UTF-8 处理、避免中文路径依赖）；命令执行经 mini `LocalEnvironment`（Windows 走 `cmd.exe`） |
| 失败可解释 | 任何判失败都必须落盘原因（schema 违约原文 / 哈希不符 / 工具越权），不允许静默通过 |

## 10. 风险与回滚点

| 编号 | 风险 | 影响 | 缓解 | 回滚点 |
|---|---|---|---|---|
| RK-1 | Godot 编辑器必须开、插件必须启用（9877） | 阶段二无法运行 | `hoh doctor` 预检 9877 + 模型端点，失败即明确报错 | 无（外部前置条件，向用户明示） |
| RK-2 | 每轮两次工程副本，Godot 工程可能较大 | 时间/磁盘开销 | 排除缓存目录；记录耗时；未来可换硬链接/增量快照 | 若不可接受 → 降级为哈希检测 + 明确声明（需用户批准，记 DECISIONS） |
| RK-3 | MCP 黑盒证据（截图/回放）天然有时序抖动 | QA 证据不稳、误判 | adapter 内重试；证据原样落盘；不确定一律 gap | 回退 `mcp_bridge` stdio 或 TCP 9876 |
| RK-4 | 本地 27B 模型能力有限 | 增量质量低、schema 反复违约 | 小步增量（≤3 优先级）、有界重试、诚实 gap | 提高重试上限/换模型（配置层，无需改码） |
| RK-5 | 单个角色调用耗尽预算（step/cost/time） | 该轮不产出 | 每角色独立限额并在 RoleOutcome 记录 exit_status | 调整限额配置 |
| RK-6 | Windows `cmd.exe` 引号/编码问题 | 工具桥命令失败 | 工具桥参数走 JSON 文件或 base64 传参，避免引号地狱；输出 UTF-8 | 改走 stdio 桥 |
| RK-7 | `ureq`/`sha2`/`walkdir` 拉取失败（网络） | 无法构建 | rsproxy 镜像已验证可用；失败时按既定方法重试/换源并记录 DECISIONS | 退回 `reqwest` 或临时手写 HTTP |

## 11. 需要你质疑/确认的关键取舍（概要设计关卡）

1. **副本隔离 vs 哈希检测**：我选择了「两者都做」。代价是每轮两个工程副本。你是否接受？
2. **双闸门 schema 校验**（内层 `hoh submit` 自愈 + 外层有界重试）是否比论文更激进？我认为它更省预算且不削弱可验证性。
3. **工具通道用瘦 CLI**（而非原生 tool 定义）是否符合你的预期？它会成为 Developer/QA 的主要工作方式。
4. **`hoh doctor` 预检**把「Godot 未开/插件未启用」变成启动即失败——这会让你每次跑之前必须先开编辑器，可以接受吗？
5. **角色 prompt 用中文还是英文？**（当前设计：prompt 与 skills 用英文，文档与日志用中文——理由是本地模型对工具调用模板的英文指令更稳。请确认。）
