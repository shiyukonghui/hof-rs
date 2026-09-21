# DESIGN-DETAIL — hof-rs 详细设计

- 状态：**v0.4（真实冒烟后修订，见 §12 DR-17..DR-23；用户已知悉并同意继续）**
- 输入：`REQUIREMENTS.md` v0.2（C1–C10 / R1–R13 / E1–E6）、`PRD-mario.md` v1、`DESIGN-OVERVIEW.md` v0.1（+D6 修订）
- 纪律：本文精确到「实现者不需要再做任何设计决策」。凡本文未定之处，实现者应按本文的**裁决原则**就近推导，并在回报中列出，不得自行改变接口。

---

## 0. 裁决原则（实现者遇到歧义时的取舍顺序）

1. **契约强制优先于便利**：任何「靠 prompt 约定」能实现的东西，必须有代码层强制或检测。
2. **沉默即失败**：无法断言成功的一律记为失败/未知，禁止静默降级为「通过」。
3. **接口按本文，内部可自由**：模块内部实现自由，但 `pub` 签名与错误类型必须逐字一致。
4. **不碰外部仓库**：不得修改 `F:\RustProjects\mini-swe-agent-rust-mini`、`F:\RustProjects\godot-mcp-pro`、`.spec/` 下任何文档。
5. **离线可测优先**：任何新逻辑都必须能在无网络、无 Godot、无 LM Studio 的条件下被测试。

---

## 1. 工程骨架

### 1.1 Cargo 清单

`F:\moonbit-hof-rs\Cargo.toml`：

```toml
[package]
name = "hof-rs"
version = "0.1.0"
edition = "2021"
description = "Harness-of-Harness runtime for autonomous software development (Rust)"
license = "MIT"

[lib]
name = "hof_rs"
path = "src/lib.rs"

[[bin]]
name = "hoh"
path = "src/main.rs"

[dependencies]
mini-swe-agent = { path = "F:/RustProjects/mini-swe-agent-rust-mini/rust" }
anyhow = "1.0"
thiserror = "2.0"
async-trait = "0.1"
clap = { version = "4.6", features = ["derive", "env"] }
serde = { version = "1.0", features = ["derive"] }
serde_json = "1.0"
serde_yaml = "0.9"
tokio = { version = "1.53", features = ["fs", "macros", "rt-multi-thread", "time", "process"] }
tracing = "0.1"
tracing-subscriber = { version = "0.3", features = ["env-filter"] }
ureq = { version = "2", default-features = false, features = ["json"] }   # 仅本地环回 HTTP，无需 TLS
sha2 = "0.10"
walkdir = "2"
uuid = { version = "1", features = ["v4"] }

[dev-dependencies]
tempfile = "3.27"
```

> 若 `ureq` 的 `default-features=false` 组合在实现时无法编译，允许就近改用 `ureq = "2"`（带默认 TLS）或 `reqwest` blocking；该改动必须记入回报与 DECISIONS，不得改变 `mcp.rs` 的对外签名。

### 1.2 目录与文件落点

```text
F:\moonbit-hof-rs\
  Cargo.toml
  config\hoh.yaml
  src\
    main.rs                 仅 tokio::main + cli::dispatch
    lib.rs                  pub mod 导出
    cli.rs                  clap 定义 + 子命令实现
    config.rs               HohConfig 加载（复用 mini config 模块）
    errors.rs               HofError 与错误码映射
    model.rs                §2 全部数据模型 + 不变式校验
    runtime\{mod,run_loop,role,invoke,view,policy,schema,evidence,snapshot,usage,record}.rs
    harness\{mod,mini}.rs
    tools\{mod,mcp,bridge}.rs
    adapter\{mod,godot}.rs
    prompts\{planner.md,developer.md,tester.md,skills\godot-dev.md,skills\godot-testing.md}
  tests\
    runtime_semantics.rs  ablation.rs  schema_gate.rs  evidence_binding.rs
    snapshot_rollback.rs  usage_extraction.rs  tools_policy.rs  mini_wire_model.rs
    fixtures\traj_with_usage.json  fixtures\plan_ok.md  fixtures\plan_missing_gate.md
    fixtures\evidence_ok.json     fixtures\evidence_dup_claim.json  fixtures\evidence_dangling.json
    godot_smoke.rs        （全部 #[ignore]）
  .workspace\mario\        （gitignore；A₀ 起点）
  runs\<run-id>\           （gitignore）
```

---

## 2. 数据模型（`src/model.rs`）

所有类型 `pub`，`serde` 字段名**逐字**如下（JSON 落盘即此形）。

```rust
#[derive(Clone, Copy, Debug, PartialEq, Eq, Hash, Serialize, Deserialize)]
#[serde(rename_all = "lowercase")]
pub enum Role { Planner, Developer, Tester }

impl Role {
    pub fn as_str(self) -> &'static str;                 // "planner" | "developer" | "tester"
    pub fn artifact_rel_path(self) -> &'static str;
    // Planner => ".hoh/plan.md"; Tester => ".hoh/evidence.json"; Developer => "" （不可提交产物）
}

#[derive(Clone, Debug, PartialEq, Eq, Serialize, Deserialize)]
pub struct Spec { pub path: PathBuf, pub sha256: String }

#[derive(Clone, Copy, Debug, Serialize, Deserialize)]
pub struct Ablation { pub plan_update: bool, pub evidence_feedback: bool, pub warm_start: bool }
impl Default for Ablation { fn default() -> Self { Self { plan_update: true, evidence_feedback: true, warm_start: true } } }

#[derive(Clone, Copy, Debug, PartialEq, Eq, Serialize, Deserialize)]
#[serde(rename_all = "snake_case")]
pub enum ExecKind { Screenshot, Replay, RuntimeTrace, Assert, Build, Log }

#[derive(Clone, Debug, Serialize, Deserialize)]
pub struct ExecRecord {
    #[serde(rename = "type")] pub kind: ExecKind,
    pub path: Option<String>,          // 相对候选视图根（POSIX 风格分隔符）；Build/Log 可为 null
    pub observation: String,
    #[serde(default)] pub candidate_id: String,   // Runtime 盖章；Tester 填写时必须相符
}

#[derive(Clone, Copy, Debug, PartialEq, Eq, Serialize, Deserialize)]
#[serde(rename_all = "snake_case")]
pub enum ClaimStatus { Verified, Gap }

#[derive(Clone, Debug, Serialize, Deserialize)]
pub struct ClaimRecord {
    pub claim_id: String,
    pub claim: String,
    pub execution_records: Vec<ExecRecord>,
    pub status: ClaimStatus,
    #[serde(default, skip_serializing_if = "Option::is_none")] pub player_impact: Option<String>,
    #[serde(default, skip_serializing_if = "Option::is_none")] pub recommended_update: Option<String>,
}

#[derive(Clone, Copy, Debug, PartialEq, Eq, Serialize, Deserialize)]
#[serde(rename_all = "snake_case")]
pub enum QaStatus { Pass, Partial, Fail }

#[derive(Clone, Debug, Serialize, Deserialize, Default)]
pub struct PlannerHandoff {
    pub preservation_constraints: Vec<String>,
    pub update_targets: Vec<String>,
    pub validation_requirements: Vec<String>,
}

#[derive(Clone, Debug, Serialize, Deserialize)]
pub struct EvidenceBundle {
    pub iteration: u32,
    pub qa_status: QaStatus,
    pub verified_records: Vec<ClaimRecord>,        // 与论文 Listing 1 同名，勿改
    pub gap_records: Vec<ClaimRecord>,
    pub planner_handoff: PlannerHandoff,
}

#[derive(Clone, Debug)]
pub struct DevelopmentDoc {
    pub iteration: u32,
    pub path: PathBuf,
    pub raw: String,
    pub priorities: Vec<String>,
    pub preservation_gate: Vec<String>,
    pub acceptance_gate: Vec<String>,
}

#[derive(Clone, Debug, Default, Serialize, Deserialize)]
pub struct Usage {
    pub role: String,
    pub iteration: u32,
    pub calls: u64,
    pub prompt_tokens: Option<u64>,
    pub completion_tokens: Option<u64>,
    pub total_tokens: Option<u64>,
    pub cache_hit_tokens: Option<u64>,
    pub cache_miss_tokens: Option<u64>,
    pub usage_known: bool,
}

#[derive(Clone, Debug, Serialize, Deserialize)]
pub struct ArtifactState {
    pub workspace: PathBuf,
    pub version_id: String,      // == candidate_id，内容寻址
    pub candidate_id: String,
    pub parent_version_id: Option<String>,
}

#[derive(Clone, Copy, Debug, PartialEq, Eq)]
pub enum ContractViolation {
    ReadOnlyRoleWroteArtifact,   // Planner/Tester 改动了真实 A
    QaContaminatedCandidate,     // Tester 改动了冻结副本
    WorkspaceDriftBeforeQa,      // QA 开始前 真实 A 与 A_t.candidate_id 不一致
    CandidateIdMismatch,         // 证据自称的候选身份不符
    PlanUpdateForbidden,         // 本轮不允许更新 D（消融）
    NoProgress,                  // 仅告警，不作为失败
}
```

### 2.1 不变式（`model.rs` 提供纯函数，供 SchemaGate/测试共用）

```rust
pub fn validate_evidence(b: &EvidenceBundle, candidate_id: &str) -> Result<(), Vec<SchemaIssue>>;
pub fn validate_plan(doc: &DevelopmentDoc) -> Result<(), Vec<SchemaIssue>>;

pub struct SchemaIssue { pub code: IssueCode, pub message: String }
pub enum IssueCode {
    Json,                    // 反序列化失败
    MissingField,
    MissingSection,          // plan 缺 required heading
    EmptyGate,
    DuplicateClaimId,
    EmptyClaimList,
    UnsupportedVerified,     // verified 但 execution_records 为空
    GapMissingGuidance,      // gap 缺 player_impact 或 recommended_update
    DanglingEvidence,        // execution_records.path 指向不存在的文件
    CandidateMismatch,
}
```

校验规则（逐条）：

| 规则 | 级别 |
|---|---|
| `verified_records` 与 `gap_records` 的 `claim_id` 集合互斥，且各自内部唯一 | err `DuplicateClaimId` |
| 两条列表均为空 → `EmptyClaimList` | err |
| `status` 与所属列表一致（`verified_records` 内必须 `Verified`，`gap_records` 内必须 `Gap`） | err |
| `verified` 的 `execution_records` 非空 | err `UnsupportedVerified` |
| `gap` 必须含 `player_impact` 与 `recommended_update`（非空字符串） | err `GapMissingGuidance` |
| `execution_records[*].path` 为 `Some` 时，文件必须存在于候选视图根之下 | err `DanglingEvidence` |
| `execution_records[*].candidate_id` 非空时必须等于 `candidate_id` | err `CandidateMismatch` |
| `planner_handoff` 三个列表允许为空，但字段必须存在 | err `MissingField` |

plan 校验规则：

| 规则 | 级别 |
|---|---|
| 必须含二级标题 `## Project Planner Priorities` | err `MissingSection` |
| 必须含三级标题 `### Priority Order` 且其后至少 1 条编号项 | err `MissingSection` / `EmptyGate` |
| 必须含 `### Preservation Gate` 且至少 1 条 `- ` 项 | err |
| 必须含 `### Acceptance Gate` 且至少 1 条 `- ` 项 | err |
| 优先级条目数 ≤ 3 | err `EmptyGate`（消息：超出 planning-policy 上限） |

---

## 3. 配置（`src/config.rs` + `config/hoh.yaml`）

### 3.1 `config/hoh.yaml`（逐字）

```yaml
model:
  model_name: deepseek-v4.1-flash         # DR-14 取代此前的 qwen 配置；见 §12
  provider: openai_compatible             # C10：必须显式
  service_name: openai_compatible
  wire_model_name: deepseek-v4.1-flash    # DR-14 新增：上线必须逐字等于它（双重锁定）
  base_url: http://100.105.152.101:18080/v1
  # api_key 必须为空（C11）：密钥由环境变量 HOH_MODEL_API_KEY 提供，不入库
  use_tool_calls: true
  request_timeout_secs: 900
  max_retries: 3

agent:
  step_limit: 150                         # DR-18：60 已被证明不够（5/5 次调用 LimitsExceeded）
  wrap_up_steps: 25                       # DR-18：剩余步数进入该阈值时必须先写出产物骨架
  cost_limit: 0.0
  wall_time_limit_seconds: 3600
  max_consecutive_format_errors: 3
  command_timeout_seconds: 180            # LocalEnvironment.timeout

runtime:
  iterations: 3
  max_schema_retries: 2
  workspace: .workspace/mario
  runs_dir: runs
  spec: .spec/hof-rs/PRD-mario.md

adapter:
  kind: godot                             # godot | test
  godot:
    addon_source: F:/RustProjects/godot-mcp-pro/addons/godot_mcp_rs
    cache_excludes: [".godot", ".import"]
    main_scene: res://scenes/main.tscn

tools:
  endpoint: http://127.0.0.1:9877/mcp
  timeout_seconds: 120
  max_retries: 2
  ready_timeout_seconds: 30               # DR-20：play_scene 后轮询游戏就绪的上限
```

### 3.2 加载契约

```rust
pub struct HohConfig {
    pub model: serde_json::Value,          // 原样传给 mini（不得在此层改写任何字段）
    pub agent: AgentLimits,
    pub runtime: RuntimeConfig,
    pub adapter: AdapterConfig,
    pub tools: ToolsConfig,
}
pub struct AgentLimits { pub step_limit: u64, pub cost_limit: f64, pub wall_time_limit_seconds: u64,
                         pub max_consecutive_format_errors: u64, pub command_timeout_seconds: u64 }
pub struct RuntimeConfig { pub iterations: u32, pub max_schema_retries: u32,
                           pub workspace: PathBuf, pub runs_dir: PathBuf, pub spec: PathBuf }
pub struct AdapterConfig { pub kind: String, pub godot: GodotConfig }
pub struct ToolsConfig { pub endpoint: String, pub timeout_seconds: u64, pub max_retries: u32 }

pub fn load_config(specs: &[String]) -> anyhow::Result<HohConfig>;
// 实现：mini_swe_agent::config::get_config_from_spec 逐项加载 + recursive_merge；
// 首个 spec 默认 "config/hoh.yaml"；CLI -c key=value 追加在末尾（后者覆盖前者）。
// 解析后必须断言：model.model_name == "openai/qwen/qwen3.8-27b" 且 model.provider == "openai_compatible"，
// 否则返回 ConfigError::ModelIdentityViolation（C9/C10）。
```

**新增配置项的上线 id 断言必须同时有测试**（`tests/mini_wire_model.rs`）：用 `LlmConnectorModel::from_value_with_mode(model_json, ApiMode::ToolCalls)` 构造模型，断言 `model.model_name()` 与内部上线名一致；上线名通过反射不可得，因此改为：断言 `mini_swe_agent::models::llm_connector` 暴露的纯函数 `effective_model_name`（若 `pub`）……

> **实现注意**：`effective_model_name` 是 `pub(crate)` 的，测试无法直接调用。因此采用**间接断言**：在 `tests/mini_wire_model.rs` 中用 `ureq` 起一个本地 `TcpListener` 假 HTTP 服务，返回固定 chat 响应，把 `base_url` 指向它，运行一次 `DefaultAgent::run`，从**服务端收到的请求体**里解析 `model` 字段，断言等于 `qwen/qwen3.8-27b`。这是唯一可信的锁定方式，必须实现。
> 该测试若因 `ureq` 依赖不可用，则用 `std::net::TcpListener` 手写最小 HTTP 服务（只支持单次请求，读取到 `\r\n\r\n` 后的 body 长度即可），不得跳过。

---

## 4. 运行时（`src/runtime/`）

### 4.1 角色与调用

```rust
pub struct RoleInvocation {
    pub role: Role,
    pub iteration: u32,
    pub system_prompt: String,                // 已完全渲染，无 jinja 语法
    pub task_prompt: String,                  // 已完全渲染
    pub cwd: PathBuf,                         // 角色视图根
    pub env: std::collections::BTreeMap<String, String>,
    pub limits: AgentLimits,
    pub model: serde_json::Value,
    pub trajectory_path: PathBuf,
    pub retry_context: Option<String>,        // 第 2/3 次尝试时的 schema 错误文本
}

pub struct RoleOutcome {
    pub role: Role,
    pub iteration: u32,
    pub attempts: u32,
    pub exit_status: String,
    pub submission: String,
    pub trajectory_path: PathBuf,
    pub usage: Usage,
    pub duration_ms: u64,
}

#[async_trait::async_trait]
pub trait Harness: Send + Sync {
    async fn invoke(&self, inv: &RoleInvocation) -> anyhow::Result<RoleOutcome>;
}
```

### 4.2 `MiniHarness`（`src/harness/mini.rs`）——必须用 mini 的哪几个 API

```rust
use mini_swe_agent::{
    models::{ApiMode, LlmConnectorModel},
    environments::{LocalEnvironment, LocalEnvironmentConfig},
    Agent, AgentConfig, AgentMode, DefaultAgent, Message, Model, Environment,
};

impl Harness for MiniHarness {
    async fn invoke(&self, inv: &RoleInvocation) -> anyhow::Result<RoleOutcome> {
        // 1) 每次调用都全新构造（R1：零状态共享）
        let model = LlmConnectorModel::from_value_with_mode(inv.model.clone(), ApiMode::ToolCalls)?;
        let mut env_cfg = LocalEnvironmentConfig::default();
        env_cfg.cwd = inv.cwd.to_string_lossy().into_owned();
        env_cfg.timeout = inv.limits.command_timeout_seconds;
        env_cfg.env = inv.env.iter().map(|(k,v)| (k.clone(), Value::String(v.clone()))).collect();
        let env = LocalEnvironment::new(env_cfg);

        let cfg = AgentConfig {
            system_template: "{{hoh_system_prompt}}".to_string(),
            instance_template: "{{task}}".to_string(),
            step_limit: inv.limits.step_limit,
            cost_limit: inv.limits.cost_limit,
            wall_time_limit_seconds: inv.limits.wall_time_limit_seconds,
            max_consecutive_format_errors: inv.limits.max_consecutive_format_errors,
            output_path: Some(inv.trajectory_path.clone()),
            mode: AgentMode::Yolo,          // DefaultAgent 不读 mode，写入仅为轨迹可读
            confirm_exit: false,
            whitelist_actions: vec![],
        };

        let mut agent = DefaultAgent::new(Box::new(model), Box::new(env), cfg);
        let task_text = match &inv.retry_context {
            Some(ctx) => format!("{task}\n\n---\n\n{ctx}", task = inv.task_prompt),
            None => inv.task_prompt.clone(),
        };
        let kwargs = serde_json::json!({ "hoh_system_prompt": inv.system_prompt });
        let _extra = agent.run(&task_text, Some(kwargs)).await;   // 返回值是 exit 的 extra，不作为成功判据
        // 2) usage 从轨迹提取（D2）
        let usage = crate::runtime::usage::extract_usage(&inv.trajectory_path, inv.role, inv.iteration)?;
        // 3) exit_status/submission 也从 agent.messages 末条取（比 extra 更可靠）
        ...
    }
}
```

**必须遵守的实现细节（否则会踩坑）**：

1. **不能用 `agent.run(task)` 直接塞角色正文**：`run()` 会用 minijinja 渲染 `system_template` 与 `instance_template`，
   若把含 `{{` / `{%`（例如证据 JSON 或 Godot GDScript）的正文放进**模板**，会被误解析。
   因此固定 `system_template = "{{hoh_system_prompt}}"`、`instance_template = "{{task}}"`，
   正文只作为**模板变量的值**传入（值不会被二次解析）。任何情况下不得把正文拼进模板字符串。
2. `agent.run()` 的 `Result` 为 `AgentError`：`Err(AgentError::Interrupt(_))` 表示正常收尾路径之一（如提交/超限），
   **不是** harness 失败；`Err(AgentError::Other(_))` 才是失败。`cost_limit` 必须给 0.0（本地模型无成本），
   否则 mini 会用默认 3.0 触发 `LimitsExceeded`。
3. `DefaultAgent::run` 会在每步后把轨迹写到 `output_path`，因此 `runs/<id>/iter-<t>/traj/<role>.json` 必须
   **先创建父目录**（`run()` 只在 `save()` 内 `create_dir_all`，MiniHarness 自行提前创建以免首步丢轨迹）。
4. `LocalEnvironment` 在 Windows 用 `cmd.exe /C`，命令需 Windows 兼容；`env` 值必须是字符串。
5. `inv.env` 必须包含（供 `hoh` 工具桥与 `hoh submit` 定位上下文）：

   | 变量 | 值 |
   |---|---|
   | `HOH_ROLE` | `inv.role.as_str()` |
   | `HOH_RUN_ID` | run id |
   | `HOH_ITERATION` | `inv.iteration` |
   | `HOH_ARTIFACT_DIR` | `<cwd>/.hoh` |
   | `HOH_TOOLS_ENDPOINT` | `tools.endpoint` |
   | `HOH_TOOLS_POLICY` | 角色策略名（= `HOH_ROLE`） |
   | `HOH_HOH_BIN` | 当前可执行文件绝对路径（`std::env::current_exe()`），供 agent 直接调用 |

### 4.3 视图构建（`src/runtime/view.rs`）

```rust
pub struct ViewSpec {
    pub root: PathBuf,                 // 视图根
    pub source: Option<PathBuf>,       // 从哪个目录复制（None = 空目录）
    pub excludes: Vec<String>,         // 复制时排除的顶层目录名（相对路径前缀匹配）
    pub inputs: Vec<(String, String)>, // (相对路径, 内容) 写到 root 下
}
pub fn build_view(spec: &ViewSpec) -> anyhow::Result<()>;   // 幂等：已存在则先清空（保留 root）
pub fn copy_tree(src: &Path, dst: &Path, excludes: &[String]) -> anyhow::Result<()>;
```

三类视图（每轮 `t`）：

| 视图 | root | source | 注入 inputs |
|---|---|---|---|
| Planner | `runs/<id>/iter-<t>/planner-view/` | `A_{t-1}` 的 workspace（t=1 时为空目录内容） | `.hoh/TASK.md`(S 原文)、`.hoh/evidence.json`(E_{t-1} 或空)、`.hoh/TOOLS.md`、`.hoh/skills/*.md`、`.hoh/SCAFFOLD.md` |
| Developer | **真实 workspace**（不复制） | — | `.hoh/TASK.md`、`.hoh/plan.md`(D_t)、`.hoh/TOOLS.md`、`.hoh/skills/*.md`、`.hoh/EVIDENCE_HISTORY.md`(最近一轮 verified 摘要) |
| Tester | `runs/<id>/iter-<t>/candidate/` | `A_t` 的 workspace | `.hoh/TASK.md`、`.hoh/plan.md`、`.hoh/TOOLS.md`、`.hoh/skills/*.md`、`.hoh/deterministic/*.json`、`.hoh/evidence.json`(**空**，由 Tester 写) |

固定排除项（始终排除，与 adapter 的 `cache_excludes` 合并）：`.hoh`, `.git`。
Developer 视图无需复制，但**必须**在本阶段开始前确保 `.hoh/` 内容为最新（覆盖写）。

`.hoh/SCAFFOLD.md` = 空模板（仅含三个 required heading 与占位说明），对应论文的 document scaffold。

### 4.4 权限强制（`src/runtime/policy.rs`）

```rust
pub struct HashExcludes(pub Vec<String>);
pub fn hash_tree(root: &Path, excludes: &[String]) -> anyhow::Result<String>;
pub fn assert_unchanged(label: &str, before: &str, after: &str) -> Result<(), ContractViolation>;
pub fn tool_allowed(role: Role, tool: &str) -> bool;
pub const PLANNER_DENY_PREFIXES: &[&str];  // 见 §6.3
```

执行顺序（`run_loop.rs` 严格按此）：

```text
t=1..=T:
  h_pre   = hash_tree(workspace)                       # 进入 Planner 前的真实 A
  [Planner]  build planner-view (副本 of workspace) -> MiniHarness::invoke -> SchemaGate(plan) 
             h_post = hash_tree(workspace)
             assert_unchanged("planner", h_pre, h_post) == Ok 否则 fail(ReadOnlyRoleWroteArtifact)
             把 planner-view/.hoh/plan.md 物化为 iter-<t>/plan.md；解析为 DevelopmentDoc
  [Developer] 写 .hoh/{TASK.md,plan.md,TOOLS.md,...} 到真实 workspace（.hoh 不参与哈希）
             h_dev_before = hash_tree(workspace)
             MiniHarness::invoke (cwd = workspace)
             h_dev_after  = hash_tree(workspace)
             若 h_dev_before == h_dev_after -> 记 NoProgress 告警（不失败）
  [Deterministic]  # v0.2 修订 DR-1：确定性阶段提前到 A_t 冻结之前，且作用于【真实 workspace】
             adapter.build_check(workspace) 产出 ExecRecord（含构建/启动/报错）
             h_det = hash_tree(workspace)          # 确定性阶段允许改动工程（编辑器副产物）
  [Freeze]   A_t.candidate_id = h_det
             snapshot(workspace) -> version_id == candidate_id
  [Tester]  build candidate view (副本 of workspace/快照) -> 注入 .hoh/deterministic/*
             # 前置断言（安全网，正常情况下必然成立）
             assert hash_tree(workspace) == A_t.candidate_id 否则 fail(WorkspaceDriftBeforeQa)
             h_cand_before = hash_tree(candidate); h_ws_before = hash_tree(workspace)
             MiniHarness::invoke (cwd = candidate)
             h_cand_after = hash_tree(candidate); h_ws_after = hash_tree(workspace)
             assert_unchanged("tester/candidate", h_cand_before, h_cand_after) 否则 fail(QaContaminatedCandidate)
             assert_unchanged("tester/workspace", h_ws_before, h_ws_after)     否则 fail(ReadOnlyRoleWroteArtifact)
             SchemaGate(evidence, candidate_id) + EvidenceBinder
             物化为 iter-<t>/evidence.json 与 qa_report.md
  [Record]  iter-<t>/usage.json, result.json, versions/index.json 追加
```

**检测与预防的分工（必须同时存在，缺一不可）**：副本隔离只能防止「相对路径写入」，无法防止 agent 用绝对路径写到真实工程；因此真实 A 的前后哈希断言是**强制项**，不是可选优化。

**QA 阶段的额外约束（关键，勿省）**：由于 MCP 工具作用于「编辑器当前打开的工程」（=真实 workspace），
Tester 能通过 MCP/shell 触达真实 A，**不只是副本**。因此 Tester 阶段必须做**三件**事：
1. 调用前断言 `hash_tree(workspace) == A_t.candidate_id`（否则本轮 QA 作废，报 `WorkspaceDriftBeforeQa`）；
2. 调用前后同时对**副本**与**真实 workspace** 做哈希断言，任一变化即判失败；
3. 工具白名单禁掉全部 Tester 写类 MCP 工具（§5.4），作为第一道闸。

新增错误变体：`ContractViolation::WorkspaceDriftBeforeQa`。

### 4.5 SchemaGate（`src/runtime/schema.rs`）

```rust
pub struct GateOutcome { pub attempts: u32, pub issues: Vec<Vec<SchemaIssue>> }  // 每次尝试的问题
pub async fn gate_plan(harness:&dyn Harness, base: &RoleInvocation, max_retries: u32) -> Result<DevelopmentDoc>;
pub async fn gate_evidence(harness:&dyn Harness, base: &RoleInvocation, candidate_id:&str, max_retries: u32)
    -> Result<EvidenceBundle>;
```

行为契约：
1. 调用 `harness.invoke(base)` → 读取角色产物路径（`base.cwd/.hoh/plan.md` / `.hoh/evidence.json`）。**产物不存在**也计入一次失败尝试（issue `Json`，消息含期望路径）。
2. 校验失败 → 构造 `retry_context`（包含：失败的 issue 列表 + 必须的产物骨架 + 期望路径），
   `base.retry_context = Some(...)`，重新调用。总尝试次数 = `1 + max_schema_retries`。
3. 全部失败 → 返回 `Err(HofError::SchemaFailure { role, attempts, issues })`；`run_loop` 把该轮 `result.json`
   写为 `{"ok":false,"failed_role":"planner|tester","reason":"schema_failure","issues":[...]}` 并**终止本次 run**
   （退出码 3）。**不得**继续下一轮，也不得用上一轮的 D/E 顶替。
4. 每次尝试都必须落盘轨迹到 `traj/<role>.attempt<N>.json`，usage 累加。

### 4.6 EvidenceBinder（`src/runtime/evidence.rs`）

```rust
pub fn bind(bundle: &mut EvidenceBundle, candidate_id: &str, view_root: &Path) -> Result<(), Vec<SchemaIssue>>;
```
1. 对每条 `ExecRecord`：`path` 为 `Some(p)` 且 `p` 不以 `/` 或盘符开头时，解析为 `view_root.join(p)` 并断言存在；
2. 盖章：`candidate_id` 为空 → 写入 `candidate_id`；非空且不等 → `CandidateMismatch`；
3. 不修改 Tester 的 `status`、`observation`、`claim` 文本（禁止 Runtime 替 Tester 判定）；
4. 落盘 `iter-<t>/evidence.json`（pretty JSON，UTF-8，LF）。

### 4.7 VersionStore（`src/runtime/snapshot.rs`）

```rust
pub struct VersionStore { pub root: PathBuf }   // = runs/<id>/versions
pub struct VersionEntry { pub version_id: String, pub candidate_id: String, pub iteration: u32,
                          pub role: String, pub verified: bool, pub parent: Option<String>,
                          pub created_at: u64, pub note: String }
pub fn snapshot(&self, workspace:&Path, excludes:&[String], iteration:u32, note:&str) -> anyhow::Result<VersionEntry>;
pub fn append_index(&self, entry:&VersionEntry) -> anyhow::Result<()>;
pub fn read_index(&self) -> anyhow::Result<Vec<VersionEntry>>;
pub fn rollback(&self, workspace:&Path, excludes:&[String], version_id:&str) -> anyhow::Result<()>;
```
- `version_id == candidate_id == sha256(排序后的 "relpath\n{len}\n{bytes}")`，排除项与 `hash_tree` 完全一致（必须复用同一函数，禁止两套实现）。
- `snapshot` 把树复制到 `versions/<version_id>/`（已存在则跳过复制，只追加索引）。
- `rollback`：删除 workspace 下**所有被哈希覆盖的条目**（保留 `.hoh` 与排除项），再从快照复制回来；随后重算哈希并断言等于 `version_id`，不等则报错。
- `index.json` 结构：`{ "schema": 1, "versions": [VersionEntry...] }`；写入用「临时文件 + rename」。

### 4.8 Usage 提取（`src/runtime/usage.rs`）

```rust
pub fn extract_usage(trajectory: &Path, role: Role, iteration: u32) -> anyhow::Result<Usage>;
pub fn merge_usage(a: &mut Usage, b: &Usage);
```
- 轨迹 = mini 的 JSON：顶层 `messages` 数组（每项含 `role`、`content`、`extra`）。
- 遍历 `messages[*].extra.response.usage`，累加四个字段；`calls` = 具有 `extra.response` 的条数。
- 若一条 usage 都没有 → `usage_known = false`，五个 token 字段为 `None`，`calls` 仍照实计数（R12）。
- 部分条目有 usage 时：`usage_known = true`，缺失字段按 `None` 处理并在 `total_tokens` 缺失时用 `prompt+completion` 补齐（仅当两者都存在）。

### 4.9 每轮与 run 元数据（`src/runtime/record.rs`）

```rust
pub fn write_run_meta(run_dir:&Path, meta:&RunMeta) -> anyhow::Result<()>;
pub struct RunMeta { pub run_id: String, pub spec: Spec, pub ablation: Ablation, pub iterations: u32,
                     pub model_identity: String, pub started_at: u64, pub hoh_version: String,
                     pub config: serde_json::Value }
pub fn write_iter_result(run_dir:&Path, iteration:u32, r:&IterResult) -> anyhow::Result<()>;
pub struct IterResult { pub ok: bool, pub failed_role: Option<Role>, pub reason: String,
                        pub issues: Vec<SchemaIssue>, pub warnings: Vec<String>,
                        pub candidate_id: Option<String>, pub version_id: Option<String>,
                        pub usage: Vec<Usage>, pub durations_ms: Vec<(String,u64)> }
```

### 4.10 主循环（`src/runtime/run_loop.rs`）

```rust
pub struct Orchestrator { pub harness: Box<dyn Harness>, pub adapter: Box<dyn ProjectAdapter>,
                          pub tools: std::sync::Arc<dyn ToolChannel>, pub cfg: HohConfig,
                          pub ablation: Ablation }
pub async fn run(orchestrator:&Orchestrator, spec:&Spec, run_id:&str) -> anyhow::Result<RunSummary>;
pub struct RunSummary { pub run_id: String, pub iterations_completed: u32, pub final_version_id: Option<String>,
                        pub total_usage: Usage, pub ok: bool }
```
消融接线（**只改一处输入**，逐条）：

| 开关 | 关闭时的精确行为 | 禁止的行为 |
|---|---|---|
| `plan_update=false` | t>1 时不调用 Planner，直接复用 `D_1`（把 `iter-1/plan.md` 复制为 `iter-<t>/plan.md`） | 不得同时跳过证据收集 |
| `evidence_feedback=false` | Planner 视图的 `.hoh/evidence.json` 写 `{"iteration": t-1, "qa_status":"partial", "verified_records":[], "gap_records":[], "planner_handoff":{"preservation_constraints":[],"update_targets":[],"validation_requirements":[]}}`（空证据，**不是**删除文件） | 不得影响 Tester 是否运行、不得影响 warm-start |
| `warm_start=false` | Planner 与 Developer 的 source 都取初始 `A₀` 的副本（Planner 视图仍从 A₀ 构建；Developer 先在 workspace 上执行 `rollback` 到 `A₀` 快照） | 不得影响证据是否传递 |
| 三个开关都开启 | 全 HoH 行为 | — |

`warm_start=false` 的实现要求：A₀ 必须在 run 开始时打一个快照（`versions/<a0_id>`，`iteration=0, role="init"`），
后续靠 `rollback` 回到它。

---

## 5. 工具通道（`src/tools/`）

### 5.1 Trait

```rust
pub struct ToolResult { pub ok: bool, pub payload: serde_json::Value }
#[async_trait::async_trait]
pub trait ToolChannel: Send + Sync {
    fn allowed(&self, role: Role, tool: &str) -> bool;
    fn index_markdown(&self, role: Role) -> String;                       // 生成 TOOLS.md
    async fn call(&self, role: Role, tool: &str, args: serde_json::Value) -> anyhow::Result<ToolResult>;
}
```

### 5.2 MCP 客户端（`src/tools/mcp.rs`）

```rust
pub struct McpClient { pub endpoint: String, pub timeout_seconds: u64, pub max_retries: u32 }
impl McpClient {
    pub fn list_tools(&self) -> anyhow::Result<Vec<String>>;
    pub fn describe(&self, tool: &str) -> anyhow::Result<serde_json::Value>;
    pub fn call(&self, tool: &str, args: serde_json::Value) -> anyhow::Result<serde_json::Value>;
}
```
- 请求体：`{"jsonrpc":"2.0","id":<递增>,"method":"tools/call","params":{"name":<tool>,"arguments":<args>}}`，
  `tools/list` 无 params。
- 响应：取 `result`；若 `error` 非空 → `Err`，错误信息含 `code`/`message`。
- 重试：仅对「连接失败/超时」重试（`max_retries`），不对 JSON-RPC 业务错误重试。
- 全部为**阻塞**调用（`ureq`）；`ToolChannel::call` 内部用 `tokio::task::spawn_blocking` 包裹以避免阻塞运行时。

### 5.3 CLI 桥（`src/tools/bridge.rs` + `cli.rs`）

```
hoh tools call <tool> [--args '<json>'] [--args-file <path>]
hoh tools list [--role <role>]
hoh tools describe <tool>
hoh submit --role <role> --file <path>
```
- `tools call`：从 `HOH_ROLE`（或 `--role`）取角色；若 `!channel.allowed(role, tool)` → 打印
  ```json
  {"ok":false,"error":"tool_not_permitted","role":"tester","tool":"add_node","hint":"This role may not mutate the artifact."}
  ```
  并 **exit 2**。成功则打印 MCP 的 `result` JSON（原样，UTF-8）并 exit 0。
- `--args` 为 JSON 时直接解析；`--args-file` 读 UTF-8 文件（**首选**，规避 Windows 引号问题，见 RK-6）。
- `hoh submit`：`role` 为 planner/tester；读取 `--file`；按 §2.1 校验；通过则原子写入
  `HOH_ARTIFACT_DIR` 下的规范路径（planner→`plan.md`，tester→`evidence.json`）并打印
  `{"ok":true,"written":"..."}`；失败则打印 `{"ok":false,"issues":[...]}` 并 **exit 3**。
  `hoh submit --role developer` 一律拒绝（exit 2）——Developer 无「提交产物」，它的产物就是工程本身。

### 5.4 工具策略表（`src/tools/policy.rs`，逐字实现）

| 角色 | 允许 | 拒绝（显式名单，命中即拒） |
|---|---|---|
| Planner | 无 MCP 工具（仅 shell 只读自查可用：`ls`/`cat`/`findstr` 等由 shell 自身提供，不在本层管辖） | 全部 MCP 工具 |
| Developer | MCP 全部 175 工具 | 无 |
| Tester | 只读/执行/证据类：`get_*`, `list_*`, `read_*`, `search_*`, `find_*`, `analyze_*`, `detect_*`, `play_scene`, `stop_scene`, `simulate_*`, `capture_frames`, `monitor_properties`, `start_recording`, `stop_recording`, `replay_recording`, `assert_*`, `compare_screenshots`, `run_test_scenario`, `run_stress_test`, `get_test_report`, `wait_for_node`, `click_button_by_text`, `navigate_to`, `move_to`, `cross_scene_set_property`(只读语义例外见下) | 写/删/改类：`add_*`, `create_*`, `delete_*`, `remove_*`, `set_*`, `update_*`, `move_node`, `rename_node`, `duplicate_node`, `edit_*`, `attach_script`, `connect_signal`, `disconnect_signal`, `tilemap_set_cell`, `tilemap_fill_rect`, `tilemap_clear`, `batch_set_property`, `cross_scene_set_property`, `export_project`, `execute_editor_script`, `execute_game_script`, `reload_plugin`, `reload_project`, `set_game_node_property`, `set_project_setting`, `set_input_action`, `bake_navigation_mesh`, `clear_output`, `clear_editor_selection` |

> 例外说明：`set_game_node_property` 与 `execute_game_script` 即便「只是调试」也**必须**拒绝，
> 否则 Tester 能改变被评估对象的状态（违反 R4）。Tester 需要构造被测状态时，只能通过 `simulate_*` 输入。

列表未覆盖的工具名一律 **default-deny**（对 Planner/Tester），并在拒绝信息里说明「未在允许名单内」。

---

## 6. 项目适配器（`src/adapter/`）

```rust
pub struct BuildRecord { pub kind: ExecKind, pub path: Option<String>, pub observation: String }

#[async_trait::async_trait]
pub trait ProjectAdapter: Send + Sync {
    fn initialize(&self, workspace: &Path) -> anyhow::Result<()>;
    fn cache_excludes(&self) -> Vec<String>;
    async fn build_check(&self, candidate_view: &Path, tools: &dyn ToolChannel) -> anyhow::Result<Vec<ExecRecord>>;
    fn evidence_playbook(&self) -> String;                 // 注入 Tester 的采集指引（Markdown）
    fn tool_policy(&self, role: Role) -> Vec<String>;      // 角色可见工具清单（用于 TOOLS.md 索引）
    fn doctor(&self, workspace: &Path) -> anyhow::Result<Vec<DoctorItem>>;
}
pub struct DoctorItem { pub name: String, pub ok: bool, pub detail: String }
```

### 6.1 `GodotAdapter`（`src/adapter/godot.rs`）

- `initialize`：幂等。若 `workspace/project.godot` 不存在 → 建最小 Godot 4 工程（`project.godot` +
  `scenes/main.tscn` + `scripts/`），并把 `godot.addon_source` 复制到 `workspace/addons/godot_mcp_rs`。
  若目录已存在且非空 → 返回 `Err(AdapterError::WorkspaceNotEmpty)`（除非 CLI 传 `--force-init`）。
- `cache_excludes`：`[".godot", ".import", ".hoh", ".git"]`（`.hoh`/`.git` 由 Runtime 强制合并，adapter 可省略但重复无害）。
- `build_check`（**只用 MCP 只读/执行工具**，Tester 走同一通道）：
  1. `reload_project`（**Runtime 代执行**，因为 Tester 被禁；作为确定性阶段的一部分，允许在 candidate 视图上调用）→ 忽略结果，仅记录；
  2. `get_editor_errors` → 若无错误：`BuildRecord{Build, None, "editor has no errors"}`；有错误：observation 内含错误原文（仍记为 Build 记录，Tester 据此判 gap）；
  3. `play_scene`（main scene）→ `get_game_scene_tree` 成功返回 → `stop_scene`；任一失败 → observation 记录失败详情。
  每步失败重试至多 `tools.max_retries`，超时 `tools.timeout_seconds`。
- `evidence_playbook`：Markdown，必须包含四类证据的可执行示例（`simulate_sequence` 驱动左右移动/跳跃、
  `capture_frames` 或 `get_game_screenshot` 截图、`monitor_properties` 记录位置随时间变化、
  `assert_node_state` 断言节点属性），并明确「截图/回放文件必须落在 `.hoh/evidence/` 下并在
  `execution_records.path` 里以相对路径引用」。
- `doctor`：检查 `project.godot` 存在、`addons/godot_mcp_rs` 存在、MCP `tools/list` 可通（要求 ≥1 个工具）。

> **实现注意**：candidate 视图是 A_t 的**副本**，其 `res://` 根即视图根，但 MCP 只作用于「编辑器当前打开的项目」。
> 因此 Tester 阶段的截图/回放**实际来自编辑器当前项目**。设计裁决：v1 接受该限制，
> 但必须在 `evidence.json` 里由 Runtime 盖章 `candidate_id`，并在 `doctor` 与 `run` 启动时**断言
> `workspace` 就是编辑器当前打开的项目**（通过 `get_project_info` 的路径信息比对，若 MCP 不返回路径，
> 则以 `hoh doctor` 的人工确认项呈现，并把该限制写入 run 元数据的 `warnings`）。
> 这一限制必须作为已知风险在回报中提出，不得默认为「已解决」。

### 6.2 `TestAdapter`（测试用，位于 `src/adapter/test_adapter.rs`，`pub`）

- `initialize`：写 `marker.txt`。
- `cache_excludes`：`["cache"]`。
- `build_check`：返回 1 条固定 `Build` 记录（observation 含固定字符串，测试断言用）。
- `evidence_playbook`：返回常量。
- `doctor`：全绿。

---

## 7. 角色 prompt（`src/prompts/*.md`，英文；由 `include_str!` 嵌入）

三个文件都必须含 `[role] / [source-of-truth] / [output-contract]` 三段结构（与论文附录 A.2 对应），
并显式声明「不得自行改写产物路径」。差异如下。

### 7.1 `planner.md`

必需内容：
1. 身份与边界：iteration 号；**planning-only**；`Do not implement, edit, test, or inspect production code.`
2. source of truth：`The public specification at .hoh/TASK.md is the complete product source of truth.`
   `Do not use benchmark scores, hidden tests, private rubrics, evaluator feedback, or other non-public information.`
3. 证据段：`EVIDENCE` 从 `.hoh/evidence.json` 读取；`For iteration 1 there is no previous evidence.`
   `Do not request or reconstruct the previous development document.`（**R5 的 prompt 侧保障**）
4. planning policy：`Prioritize blockers and regressions before product extensions. Select at most three achievable priorities.`
   `Convert each priority into a concrete implementation target and an observable validation requirement.`
5. 输出契约：只写 `.hoh/plan.md`，结构**逐字**为：
   ```markdown
   ## Project Planner Priorities
   ### Priority Order
   1. **<name>** - <action and observable outcome>
   ### Preservation Gate
   - <working functionality / evidence that must not regress>
   ### Acceptance Gate
   - <smallest end-to-end validation>
   ```
6. 提交方式：`Write the file, then run: $HOH_HOH_BIN submit --role planner --file .hoh/plan.md`
   `If it reports issues, fix the file and submit again before you finish.`

### 7.2 `developer.md`

必需内容：
1. 身份：iteration 号；`Build or improve the complete project in the current working directory.`
2. 输入：`.hoh/TASK.md`（PRD）、`.hoh/plan.md`（本轮实现与验证简报）、`.hoh/EVIDENCE_HISTORY.md`（上轮已验证/未解决摘要）。
3. warm-start 指令：`Continue from the artifact already present. Preserve verified functionality and repair the
   next observable gap rather than replacing a working project with a smaller reset.`
4. policy：先修 build/runtime blocker，再按 plan 的优先级顺序实现；`Keep the project launchable at all times.`
   `Use $HOH_HOH_BIN tools call <tool> --args-file <path> for Godot editor operations.`
5. 自测（shift-left）：`Before editing, establish a baseline for the target behavior. After each meaningful change,
   re-run the corresponding path and inspect the affected implementation and adjacent regression surface.`
   `Your self-tests do not establish that the requirements are satisfied; independent QA will decide that.`
6. 输出契约：**不得**调用 `submit`；产物就是工程本身；结束时用 `COMPLETE_TASK_AND_SUBMIT_FINAL_OUTPUT`
   机制（mini 的退出协议）提交一句话总结。

### 7.3 `tester.md`

必需内容：
1. 身份：iteration 号；`Review the updated artifact as a player-facing product`；`Do not modify production code.`
2. 输入：`.hoh/TASK.md`、`.hoh/plan.md`、`.hoh/deterministic/*.json`（确定性构建/启动记录）、
   `.hoh/TOOLS.md`（只读/执行类工具）。
3. assessment policy（论文 A.2 逐条）：从公共需求与验证目标推导 checkable claims；
   只有被引用的执行记录**可见地支持**时才给 `verified`；失败/回归/未满足/证据不足一律记 `gap`；
   不得读或推断 `/tests`、benchmark 分数、私有评测文件。
4. 证据要求：每个 claim 必须引用 `execution_records`，`path` 为**相对路径**且文件真实存在；
   截图/回放必须写入 `.hoh/evidence/`。
5. 输出契约：写 `.hoh/evidence.json`，字段逐字为论文 Listing 1 结构（含 `iteration`、`qa_status`、
   `verified_records`、`gap_records`、`planner_handoff`），并另写人类可读的 `.hoh/qa_report.md`。
6. 提交方式：`$HOH_HOH_BIN submit --role tester --file .hoh/evidence.json`，失败即按 issues 修复重提。

### 7.4 skills（各 ≤ 60 行）

- `godot-dev.md`：GDScript 4.7 要点、InputMap 命名 action（`move_left`/`move_right`/`jump`）、
  节点命名约定（`Player`、`Enemy*`、`Coin*`、`HUD`、`Goal`）、`hoh tools call` 的常用调用示例（3~5 条）。
- `godot-testing.md`：`simulate_sequence` → 截图 → `assert_node_state` 的证据采集范式、
  「同一候选身份下的记录才可互相引用」、以及「源码存在 ≠ 行为验证」的判定纪律。

---

## 8. CLI（`src/cli.rs`）

```rust
#[derive(clap::Parser)]
pub struct Cli { #[command(subcommand)] pub command: Command }

pub enum Command {
    Run(RunArgs), Doctor(DoctorArgs), Status(StatusArgs), Rollback(RollbackArgs),
    Tools(ToolsArgs), Submit(SubmitArgs), SpecHash(SpecHashArgs),
}
pub struct RunArgs {
    #[arg(long)] spec: Option<PathBuf>,
    #[arg(long)] project: Option<PathBuf>,
    #[arg(long, default_value_t = 3)] iterations: u32,
    #[arg(long)] run_id: Option<String>,
    #[arg(long, default_value = "godot")] adapter: String,
    #[arg(short='c', long="config")] config_spec: Vec<String>,
    #[arg(long, default_value_t = 2)] max_schema_retries: u32,
    #[arg(long)] ablate: Vec<String>,          // plan_update=false / evidence_feedback=false / warm_start=false
    #[arg(long)] force_init: bool,
}
```

行为契约：
- `run`：`hoh doctor` 等价预检 **必须**先执行；任一项失败 → 打印逐项体检表并 exit 4（**不启动**）。
- `run_id` 默认 `<UTC yyyymmdd-HHMMSS>-<uuid4 前 8 位>`；同 id 目录已存在 → 报错退出，除非 `--resume`（v1 允许不实现 resume，但必须明确报 `resume_not_implemented` 并 exit 2）。
- 退出码：`0` 成功；`2` 契约违约/用法错误（含 resume 未实现）；`3` schema 重试耗尽；`4` 外部依赖不可用；`5` harness/模型错误。
- `status`：打印每轮 `ok/reason/candidate_id/usage` 表格 + 汇总 tokens；无需网络。
- `rollback`：调用 `VersionStore::rollback` 并打印新哈希。
- `spec-hash`：打印 S 的 sha256（用于人工核对冻结）。

`doctor` 检查项（逐项 ok/detail，全部 ok 才放行）：
1. `spec` 文件存在且非空；打印其 sha256。
2. 模型配置通过 C9/C10 断言。
3. `GET {model.base_url 去掉尾部 /v1}/../` 不用；改为直接 `POST {base_url}/chat/completions` 发一条
   `max_tokens=1` 的最小请求（`model` 字段用**上线名**）→ 必须 200 且响应 `model` 字段等于 `qwen/qwen3.8-27b`。
4. `GET http://127.0.0.1:1234/api/v0/models` → 列出 `state=loaded` 且 id 含 `qwen3.8` 的条目；
   若存在裸 id `qwen3.8-27b` 的已加载条目 → **ok=false**，提示「存在重复常驻实例，会占用额外显存，请在 LM Studio 卸载」（对应 D6）。
5. `adapter.doctor(workspace)` 的每一项。
6. `tools.list_tools()` 非空（即 9877 可达、编辑器已开、插件已启用）。

---

## 9. 测试策略（离线为主）

### 9.1 测试替身（全部放在 `tests/` 下的公共模块 `tests/common/mod.rs`）

```rust
pub struct FakeHarness { pub script: Vec<FakeStep>, pub log: Mutex<Vec<RoleInvocationRecord>> }
pub struct FakeStep {
    pub role: Role,
    pub writes: Vec<(String, String)>,   // (相对 view 根的路径, 内容)
    pub exit_status: String,
    pub usage: Option<UsageFixture>,
    pub write_outside_view: Option<(PathBuf, String)>,   // 用于制造越权写入反例
    pub sleep_ms: u64,
}
pub struct FakeAdapter { pub build_records: Vec<ExecRecord>, pub excludes: Vec<String> }
pub struct FakeToolChannel { pub calls: Mutex<Vec<(Role,String,Value)>> }
```
`FakeHarness::invoke` 行为契约：
1. 记录 `RoleInvocation` 的**全部字段**（role、iteration、cwd、env、system_prompt、task_prompt、
   retry_context、model JSON 的规范化串、limits）——消融测试靠逐字节比较这些记录；
2. 按 `script` 顺序取下一步（角色必须匹配，否则 panic 并打印实际调用序列）；
3. 写 `writes` 到 `inv.cwd`；若 `write_outside_view` 有值则写到该绝对路径（越权反例）；
4. 生成 `inv.trajectory_path`（父目录先建），内容为含 `usage` 的合法 mini 轨迹 JSON；
5. 返回 `RoleOutcome`。

### 9.2 逐条验收映射（R1–R13 / E1–E6）

| 需求 | 测试文件::用例 | 断言要点 |
|---|---|---|
| R1 | `runtime_semantics.rs::three_independent_invocations` | 恰好 3 次调用、顺序 planner→developer→tester、每次 `RoleInvocation.env` 含正确 role、FakeHarness 记录中无跨角色 messages 传递（不同 cwd） |
| R2 | `runtime_semantics.rs::planner_cannot_write_artifact` | 让 FakeHarness 在 planner 步用 `write_outside_view` 改真实 workspace → `run` 返回 `ReadOnlyRoleWroteArtifact`，且 `result.json.ok=false`、`failed_role=planner` |
| R3 | `runtime_semantics.rs::developer_is_only_writer` | developer 步后 workspace 哈希变化被记为 `A_t`；planner/tester 步后哈希必须不变 |
| R4 | `evidence_binding.rs::{rejects_contaminated_candidate, rejects_workspace_drift, rejects_direct_real_workspace_write}` | tester 步内改 candidate 视图 → `QaContaminatedCandidate`；改**真实 workspace（绝对路径）** → `ReadOnlyRoleWroteArtifact`；QA 前 workspace 被外部改动 → `WorkspaceDriftBeforeQa`；`candidate_id` 不符 → `CandidateIdMismatch` |
| R5 | `runtime_semantics.rs::no_third_state_channel` | 生成的第 2 轮 planner `task_prompt` 与 `planner-view` 中**不含** `D_1` 文本；且 `system_prompt` 含 `Do not request or reconstruct the previous development document` |
| R6 | `schema_gate.rs::plan_retry_then_success` / `evidence_retry_exhausted` / `missing_artifact_counts_as_attempt` | 首次写非法 plan → 第二次合法 → `attempts==2`；两次非法 → `SchemaFailure` 且退出码 3；产物缺失也计入尝试 |
| R7 | `evidence_binding.rs::verified_gap_partition` | verified∩gap 的 claim_id 交集为空；gap 缺 guidance → issue；verified 空 records → issue |
| R8 | `ablation.rs::{plan_update_off_only_changes_plan, evidence_off_only_changes_evidence, warm_start_off_only_changes_source}` | 逐字节比较 FakeHarness 记录：关闭某开关后，**除该输入外**其余字段完全相同 |
| R9 | `runtime_semantics.rs::records_all_artifacts` | 每轮目录含 `plan.md`/`evidence.json`/`qa_report.md`/`traj/*.json`/`logs/*`/`usage.json`/`result.json`；`meta.json` 含 spec.sha256 |
| R10 | `snapshot_rollback.rs::{snapshot_is_content_addressed, rollback_restores_exact_tree, rollback_detects_corruption}` | 相同内容 → 相同 version_id；改动一个字节 → 不同；rollback 后哈希等于目标；篡改快照 → 报错 |
| R11 | `runtime_semantics.rs::no_private_information_in_views` | 在 workspace 里放 `tests/secret.json` 与 `runs/` 同名敏感文件，断言描述不进入任何视图、证据、prompt；且 tester 工具策略拒绝写工具 |
| R12 | `usage_extraction.rs::{sums_usage_across_messages, unknown_when_absent, merges_partial}` | 夹具 `traj_with_usage.json` → 精确数值；无 usage → `usage_known=false` 且 token 为 `None`；`merge_usage` 累加正确 |
| R13 | `tools_policy.rs::{tester_denied_mutating_tools, developer_allowed_all, planner_denied_all_mcp, default_deny_unknown}` | 逐条对照 §5.4 名单；未知工具 default-deny；`hoh tools call` 命中拒绝时退出码 2 且输出 `tool_not_permitted` |
| C9/C10 | `mini_wire_model.rs::wire_model_id_is_exact` + `cli.rs::doctor_rejects_stripped_id` | 假 HTTP 服务收到的 `model` 字段 == `qwen/qwen3.8-27b`；配置被篡改（去掉 `openai/` 前缀）→ `load_config` 返回 `ModelIdentityViolation` |
| E1–E6 | `godot_smoke.rs`（`#[ignore]`） | 真实 T=1：跑通一类；断言 `play_scene` 成功、`get_editor_errors` 空、至少 3 条证据记录、QA 视图哈希不变、`/api/v0/models` 的 loaded 条目数不增加 |

### 9.3 测试纪律（TDD 硬要求，见 §10 任务书）

- 每个测试必须先写出「因缺行为而失败」的形态（红），再写最小实现（绿），再重构（保持全绿）。
- 不得为了让测试通过而放宽断言；不得用 `#[ignore]`/`--skip` 规避离线测试。
- 整个离线测试套件必须能在 **断网、无 Godot、无 LM Studio** 环境下 `cargo test` 全绿。
- `godot_smoke.rs` 中所有用例 `#[ignore]`，并在文件头注释里写明真实运行所需的三个外部前置条件。

---

## 10. 交给实现子代理的任务书草案

### 10.1 工作分解（两个可并行的工作流，文件边界互不重叠）

| 工作流 | 范围（独占文件） | 依赖 |
|---|---|---|
| **WS-A 核心 Runtime** | `Cargo.toml`, `config/hoh.yaml`, `src/{lib,main,cli,config,errors,model}.rs`, `src/runtime/**`, `src/harness/**`, `src/adapter/{mod,test_adapter}.rs`, `tests/{runtime_semantics,ablation,schema_gate,evidence_binding,snapshot_rollback,usage_extraction,mini_wire_model,common}.rs`, `tests/fixtures/**` | 仅本文档；Godot 相关一律用 `TestAdapter` |
| **WS-B 工具通道与 Godot 适配** | `src/tools/**`, `src/adapter/godot.rs`, `src/prompts/**`, `tests/{tools_policy,godot_smoke}.rs` | 仅本文档；依赖 `src/model.rs` 的 `Role`/`ExecRecord`/`ExecKind` 与 `src/tools/mod.rs` 的 trait（由 WS-A 提供**冻结签名**，WS-B 先按签名写桩不可行 → 因此 WS-B 必须等 WS-A 提交 `model.rs` 与 `tools/mod.rs` 的签名骨架后再开始） |

> **裁决**：允许并行，但要求 WS-A **先提交** `src/model.rs`、`src/errors.rs`、`src/tools/mod.rs`（仅 trait 与类型，不含实现）
> 作为「接口冻结提交」，之后 WS-B 才动工。若时序难以协调，则退化为**单工作流顺序实现**（本设计文档已足够自包含）。

### 10.2 任务书正文（逐字下发给子代理）

```
目标
在 F:\moonbit-hof-rs 实现 hof-rs（Harness-of-Harness 的 Rust 运行时），严格按
.spec/hof-rs/DESIGN-DETAIL.md 的接口与行为契约。工程落点见该文档 §1。

先读
1. .spec/hof-rs/DESIGN-DETAIL.md（唯一实现依据，逐条遵守）
2. .spec/hof-rs/REQUIREMENTS.md（R1-R13 是验收对象）
3. .spec/hof-rs/DESIGN-OVERVIEW.md（分层与选型背景）
4. .spec/hof-rs/PRD-mario.md（了解 S 的形态，实现不得改动它）

范围
按 DESIGN-DETAIL §10.1 分配给你的工作流的独占文件范围。
不在此范围内的文件一律不得改动。

硬性约束
- 不得修改 F:\RustProjects\mini-swe-agent-rust-mini\** 与 F:\RustProjects\godot-mcp-pro\**（只读参考）。
- 不得修改 .spec/** 下任何文档。
- 不得联网（cargo 拉取依赖除外）；不得依赖真实 Godot / LM Studio 才能通过测试。
- 模型配置逐字遵守 DESIGN-DETAIL §3.1（C9/C10：上线 model id 必须恰好是 qwen/qwen3.8-27b）。
- 不得引入 DESIGN-DETAIL §1.1 之外的依赖；若必须引入，先在回报中说明并给出理由。

严格 TDD（红-绿-重构）
1. 先写会失败的最小测试，运行并确认它因「缺少行为」而失败（贴出真实失败输出）。
2. 写最小实现让它通过（贴出通过输出）。
3. 在测试全绿下重构。
- 每完成一个测试-实现循环就运行一次 cargo test；不允许测试长期处于红色。
- 测试是需求的可执行文档：DESIGN-DETAIL §9.2 的映射表必须逐条落地，用例名一致。
- 禁止用 #[ignore]、--skip、放宽断言等方式规避离线测试。
- 每个模块完成后运行 cargo fmt 与 cargo clippy --all-targets -- -D warnings（若 clippy 不可用则说明）。

提交要求
- 每完成一个可提交单元就 git add -A && git commit，提交信息格式：
  <type>(<scope>): <中文简述> (D<n>|<R编号>)
  例：feat(runtime): 实现角色调用事务与 usage 提取 (R1,R12)
  决策编号引用 DECISIONS.md 中已有的 D1-D6；新增决策写进 DECISIONS.md 再提交。
- 不得提交 .workspace/、runs/、target/。

完成后的回报格式（必须逐项，禁止只说「已完成」）
1. 状态：完成的文件清单（相对路径）。
2. 测试证据：`cargo test` 的**真实输出尾部**（含 passed/failed 计数）；逐条列出 DESIGN-DETAIL
   §9.2 映射表中的 R 编号 → 测试用例名 → 通过/未通过。
3. 与设计的偏离：任何偏离本文档的地方，逐条说明「文档怎么写的 / 实际怎么做的 / 为什么」。
4. 未完成项与阻塞：明确列出，不得隐瞒。
5. 新增依赖：名称、版本、理由、评估（维护活跃度/许可证）。
6. 已知风险：尤其是 DESIGN-DETAIL §6.1 中「MCP 作用于编辑器当前项目，而 Tester 在副本上」这一限制，
   必须给出你的实际处理方式与残留风险。
7. 可复现命令：审阅者如何一键复跑你的测试。
```

### 10.3 我（决策者）在验收阶段的对应动作

- 派**全新**验收子代理，独立逐条核对 §9.2 映射表、跑测试、构造反例（越权写入、schema 违约、
  证据悬空、消融不纯），按结构化 schema 返回 verdict/criteria/defects/risks。
- 验收结论与证据写入 `.spec/hof-rs/ACCEPTANCE.md`。

---

## 11. 已知限制与必须在回报中提出的风险

1. **MCP 作用域限制**（§6.1 + §4.4）：Tester 在 `A_t` 副本上评估，但 MCP 只能操作编辑器当前打开的项目，
   而该项目在 v1 中就是真实 workspace。因此 v1 采用「**同一候选的两种访问路径**」：副本（读输入、写证据）
   + 编辑器工程（执行与截图），并用「QA 前 workspace 哈希 == candidate_id」+「QA 前后 workspace 与副本双哈希断言」
   把两者绑成同一候选身份。若运行时检测到不一致，必须把该事实写入 `meta.json.warnings` 并在 `result.json` 标 warning；
   不允许把它当成「已解决」。
   替代方案（更强但更重，v1 不采用）：为 QA 单独起第二个 Godot 编辑器实例并打开 candidate 副本、
   把 `godot_mcp/port` 设为另一个端口（如 9878），从而让 Tester 真正只作用于副本。若用户要求端到端严格冻结，
   这应作为 v1.1 的首选项。
2. **副本成本**：每轮两个工程副本（排除缓存）。若单轮耗时或磁盘超预期，实现者必须实测并回报数据，
   不得擅自改成哈希检测替代。
3. **快照为全量**（非增量）：大工程下会膨胀；实现者需回报实测体积。
4. **`ureq` 无 TLS**：v1 只访问本地环回，若后续接入远程 MCP 必须换实现（并记决策）。
5. **`resume` 未实现**：v1 明确报 `resume_not_implemented`（exit 2），不得假装支持。

---

## 12. 修订 v0.2（独立验收后，规范性；与本文件前文冲突处**以本节为准**）

来源：阶段五第一次独立验收 verdict = `fail`（blocker A1、major A2、minor A3–A5、nit A6）+ 9 条风险。
本节各项均为**规范性要求**，实现者必须逐条落地并给出测试证据。修订依据见 `DECISIONS.md` D11/D12。

### DR-1（设计性修订，最重要）确定性阶段提前到 A_t 冻结之前，且作用于真实 workspace

- 新顺序：`Developer → Deterministic(build/exec on workspace) → Freeze A_t(hash+snapshot) → candidate 副本 → Tester → Record`
  （已同步改写 §4.4 伪码）。
- `ProjectAdapter::build_check` 的入参由 `candidate_view` 改为 **`workspace`**（真实工程）。
  理由：MCP 只能作用于编辑器当前打开的工程（= workspace，D7），让确定性阶段作用于 workspace 可**根除**
  「工具自身改写工程 → QA 前漂移 `WorkspaceDriftBeforeQa`」这一整类误报；确定性记录与候选身份天然一致。
- 确定性阶段产生的 `ExecRecord` 与日志在冻结后复制进 candidate 视图的 `.hoh/deterministic/`。
- QA 前的 `hash_tree(workspace) == A_t.candidate_id` 断言**保留**，作为安全网（正常情况下必然成立）。
- 语义澄清：构建/执行属于「产出候选」的一部分，不属于「评估候选」；评估仍只发生在冻结之后。
- 接口签名相应改为 `async fn build_check(&self, workspace: &Path, tools: &dyn ToolChannel) -> Result<Vec<ExecRecord>>`。

### DR-2 契约违约必须附具体差异清单（可诊断）

任何 `ContractViolation` 判定失败时，`result.json` 必须新增 `evidence_diff` 字段：
`{"added":[相对路径...],"modified":[...],"removed":[...]}`（相对 workspace 根，POSIX 分隔符，排序，最多各 50 条）。
哈希比较必须能给出**具体差异**，不允许只报「哈希不同」。用途：把误报变成可定位事件、把越权变成可追责证据。
测试：构造只改一个深层文件的越权写入，断言 `evidence_diff.modified` 恰好含该相对路径。

### DR-3 新增 `runtime.private_excludes`（硬性补强 R11）

- `config/hoh.yaml` 新增 `runtime.private_excludes: []`（默认空数组）。
- 视图构建（`build_view`/`copy_tree`）在原排除项之外**再排除**这些相对路径/前缀；
  它们**不**影响 artifact 哈希与快照（即不扩大 `hash_tree` 的排除集，避免削弱 R2/R3 检测）。
- 测试：配置 `private_excludes: ["tests/secret.json"]` 后，断言该文件不出现于任何角色视图，
  且 `hash_tree(workspace)` 仍覆盖该文件（即它仍在 artifact 身份内）。

### DR-4 `GodotAdapter::initialize` 必须幂等写入插件启用段

- 除创建 `project.godot` / `scenes/main.tscn` / `scripts/` 与拷贝 addon 外，还必须在 `project.godot` 中
  保证存在 `[editor_plugins]` 段且 `enabled` 数组**包含** `"res://addons/godot_mcp_rs/plugin.cfg"`。
- 幂等要求：重复调用不重复添加、**不得**覆盖其它已启用插件项；若 `enabled` 已含该项则完全不动文件内容。
- 目的：使 A₀「打开即可用 MCP」，把「手工启用插件」这一易错步骤从用户前置条件中移除。
- 测试：`initialize` 两次后 `project.godot` 中该条目恰好出现 1 次；预置 `enabled` 含另一插件时不丢失。

### DR-5 `get_editor_errors` 判定改为解析 JSON，禁止子串启发式

- 依据 `errors` 数组长度判断是否有错（兼容 `{"errors": []}` 带空格、以及 observation 内含 "error" 字样的合法字段）。
- 无法解析为 JSON 时按「有错」记录并把原文写入 observation（保守）。
- 测试：给假 MCP payload `{"errors": []}` 与 `{"errors":[{"message":"x"}]}` 分别断言无错/有错。

### DR-6 `hoh doctor` 增加 `godot.editor_scope` 人工确认项；每轮 result.json 也带该 warning

- `doctor` 输出新增一项 `godot.editor_scope`：`ok = true`，`detail` = `MCP_SCOPE_WARNING` 原文 +
  明确要求用户人工确认「编辑器当前打开的工程就是该 workspace」。**不改变** exit 4 的放行语义
  （即该项本身不会导致拒绝运行）。
- D7 的限制除写入 `meta.json.warnings` 与 `warnings.log` 外，还必须在**每轮** `result.json.warnings` 中出现。
- 测试：`doctor` 输出包含该行；成功轮的 `result.json.warnings` 含 `MCP_SCOPE_WARNING`。

### DR-7 拒绝文案必须区分「未在允许名单内」

- `runtime::policy` 的 `denial_reason` 必须对 Planner 与 Tester 都覆盖两种情况：
  ①角色禁止此类操作（写类工具）→「This role may not mutate the artifact.」；
  ②工具不在该角色允许名单内（含全部未知工具）→「Tool not in this role's allowlist.」。
- Planner 对**全部** MCP 工具都属情况②（其 allowlist 为空）。
- 测试：断言 Planner 调 `get_editor_errors` 的 hint 为情况②文案；Tester 调 `add_node` 为情况①文案。

### DR-8 CLI 出口与展示纪律

- `status` 的「runs 目录不存在 / run-id 不存在」与 `rollback` 的「版本不存在」必须返回类型化错误 → **exit 2**
  （不得落 anyhow 兜底 exit 5；exit 5 专指 harness/model 错误）。
- `status` 汇总 tokens 时：若存在 `usage_known == false` 的轮次，必须显示 `unknown`
  （例如 `total tokens: 120 (1 iteration unknown)`），**不得**把缺失值当 0 累加后打印 `total tokens: 0`。
- 新增 `tests/cli_status_rollback.rs`（tempfile 驱动、离线）：覆盖正常 status、run-id 不存在(exit 2)、
  rollback 缺版本(exit 2)、unknown usage 的展示。

### DR-9 `godot_smoke.rs` 前置条件缺失必须失败，且 e0 不得用 force_init

- E2–E6 在真实 run 产物缺失时**必须 panic 并给出缺失路径**，不得 `eprintln` 后 `return`（当前是「零断言 + 绿色」）。
  允许的替代：统一要求 `HOH_SMOKE=1` 环境变量，未设置时 panic（并同步修正文件头注释）。
- `e0_initialize_workspace` 不得传 `force_init=true`；必须断言 `initialize` 对已初始化工作区**幂等**
  （第二次调用为 no-op 且 `project.godot` 内容不变）。`force_init` 的破坏性语义需在 CLI 帮助文本中明确。
- 测试：以「runs/ 不存在」为前提运行 `cargo test --test godot_smoke -- --ignored`，断言结果为**失败**而不是 passed。

### DR-10 路径逃逸收紧（blocker A1）

- `EvidenceBinder::check_paths`（以及 `hoh submit` 复用的同一函数）必须：
  1. 拒绝任何含 `..`（`std::path::Component::ParentDir`）组件的 `path` → `DanglingEvidence`；
  2. 在存在性检查之外，对 `canonicalize(view_root)` 与解析后的 `canonicalize(resolved)` 做**前缀断言**
     （解析失败或不在前缀内 → `DanglingEvidence`）。
- 同步收紧 `godot_smoke.rs::e4` 的包含性判定（禁止用 `candidate.join(path)` 的朴素拼接）。
- 新增测试 `evidence_binding.rs::rejects_parent_dir_traversal`：
  `path = "../outside_secret.txt"`（文件真实存在于视图根之外）必须得到 `DanglingEvidence`，`bind` 返回 `Err`；
  绝对路径、符号链接逃逸（若可构造）同样必须被拒。

### DR-11 `cache_excludes` 的防误用约束

- `config/hoh.yaml` 中 `adapter.godot.cache_excludes` 必须带注释：**只允许缓存类目录**（如 `.godot`、`.import`）。
  把真实产物路径加入排除集会**同时关闭** R2/R3 的越权检测能力。
- `src/adapter/mod.rs` 的 `cache_excludes` trait 方法文档必须写明该约束；`GodotAdapter` 实现处同样注释。

### DR-12 未声明偏离的补记（文档侧）

以下实现期事实已被验收判为「可接受但未申报」，本修订一并承认并写入文档，后续不必再作为偏离申报：
- `MiniHarness` 把 `Err(AgentError::Format(_))` 与 `Ok`/`Interrupt` 一并视为正常收尾（格式错误的失败由 SchemaGate 兜住）；
- 新增 `src/cli_impl.rs`；`RunMeta` 新增 `warnings` 字段（§4.9 原缺，属设计缺口）；
- `VersionStore::snapshot_role` 为附加 API；`validate_evidence_shape` 为附加纯函数；
- 工具策略单一真源为 `runtime::policy::tool_matrix`，`src/tools/policy.rs` 仅 re-export。

### DR-13 验收后仍未解决、需真实运行才能定论的事项（不属本节修复范围）

- E1–E6 需 Godot 编辑器（9877）+ LM Studio 在线才能验证；
- 真实运行中编辑器副产物（`*.uid`、`uid_cache`、存档、导出产物）是否会造成假失败；
- 真实 27B 模型在 `1 + max_schema_retries` 次内产出合法 plan/evidence 的能力；
- 副本耗时与全量快照体积的实测数据。

### DR-14 模型身份「配置驱动 + 双重锁定」（取代 C9 的硬编码写法）

- `config/hoh.yaml` 的 `model` 段新增必填项 **`wire_model_name`**：声明「上线请求体里的 `model` 字段必须逐字等于」的字符串。
- **删除代码中的硬编码模型常量**：`config::REQUIRED_MODEL_NAME` / `config::WIRE_MODEL_NAME` 必须移除；
  `assert_model_identity` 改为校验下列通用不变式（不再认识任何具体模型名）：
  1. `model.provider` 显式存在且等于 `openai_compatible`（C10）；
  2. `model.model_name` 与 `model.wire_model_name` 均非空；
  3. `model.api_key` **必须为空**（C11）——密钥来自环境，不得写在配置里；
  4. `HofError::ModelIdentityViolation` 的文案与字段改为携带 `expected` / `actual` 或配置值，不得再出现具体模型名。
- **双重锁定（C9）**：
  1. 离线：`tests/mini_wire_model.rs` 改为**从配置读取 `wire_model_name`**，用假 HTTP 服务断言服务端收到的
     `model` 字段逐字等于它（换模型只改配置，测试自动跟随，无需改码）；
  2. 在线：`hoh doctor` 的 `model.chat` 探测断言**响应里的 `model` 字段**等于 `wire_model_name`。
- 配置解析后必须把 `wire_model_name` 保留在传给 mini 的 model JSON 中（mini 会忽略未知字段），
  但**不得**用它替换 `model_name`（C9 的风险正是「上线 id 被悄悄改写」）。

### DR-15 `hoh doctor` 的探测必须通用化（C12）

- `model.chat` 探测**必须携带 `Authorization: Bearer <resolved api_key>`**（当前实现不带任何鉴权头，对远端端点会 401）。
  api_key 的解析顺序（C11）：`model.api_key`（非空）→ `HOH_MODEL_API_KEY` → `OPENAI_API_KEY`；三者皆空时
  该探测项 `ok=false`，detail 明确「no api key resolved」。
- `model.resident` 探测是 **LM Studio 专有**（`/api/v0/models` + 裸 id 重复实例检查），必须条件化：
  - 仅当 `base_url` 的 host 为 `127.0.0.1` / `localhost`（或配置显式开启）时才执行；
  - 端点不提供该 API、或 host 为远端时，返回 `DoctorItem{ ok: true, detail: "skipped: ..." }`（**不得** `ok=false`，
    否则会阻断 run，违反 C12）；
  - 裸 id 检查改为通用规则：若存在 `state=loaded` 且 id 等于「`wire_model_name` 去掉厂商前缀后的形式」的条目，
    才报告重复实例（保留 D6 的教训，但不硬编码 `qwen3.8-27b`）。
- 端到端要求：**换模型/换端点后，`hoh doctor` 必须全绿，且不得需要改 `src/**`。**

### DR-16 密钥卫生（C11）

- `config/hoh.yaml`：`model.api_key` 留空（或整行不写）；文件中不得出现任何形如 `sk-...` 的字面量。
- `.gitignore` 追加：`.env`、`*.env`、`config/*.secret*`。
- 加载配置后把解析出的密钥回填到**内存中**传给 mini 的 model JSON；`meta.json`、轨迹、日志、
  `evidence.json`、role prompt、`doctor` 输出中**禁止**出现密钥明文：
  - `meta.json.config` 落盘前必须把 `model.api_key` 替换为 `null`（或 `"<redacted>"`）；
  - 轨迹由 mini 写入，其中 `info.config.model.api_key` 可能含密钥 → **运行结束后必须对 `runs/<id>/**/traj/*.json`
    做 redaction 后再视为验收产物**；更稳的做法是给 mini 传 `api_key` 为空并依赖其环境变量回退（若 mini 的
    `resolve_api_key` 能从 `OPENAI_API_KEY` 取到值），实现者必须在两者中选择并给出证据。
- 测试：①配置里出现 `api_key` 非空 → `ModelIdentityViolation`；②`meta.json` 与轨迹中不含 `sk-` 前缀串；
  ③密钥只来自环境时，`hoh doctor` 的 `model.chat` 探测仍能带鉴权成功（用假 HTTP 服务断言收到了
  `Authorization: Bearer <key>`）。

### DR-17 确定性证据电池：Runtime/adapter 拥有证据采集，Tester 只做判定（设计性修订）

来源：第一次真实 T=1 冒烟暴露的结构性冲突——Tester 三次尝试各 60 步**全部被证据采集吃掉**，
从未走到写 claims，`E_1` 始终不存在（run 以 exit 3 收尾）。论文原分工本就是「Tester 拿到**确定性构建/执行结果**」
后再判定，故把采集职责收回 Runtime/adapter。

- `ProjectAdapter` 新增（或改写 `build_check` 为）**证据电池**：
  ```rust
  pub struct BatteryStep { pub id: String, pub supports: Vec<String>, pub timeout_secs: u64, pub retries: u32 }
  pub struct BatteryRecord { pub step_id: String, pub supports: Vec<String>, pub record: ExecRecord, pub ok: bool, pub raw_path: Option<String> }
  async fn evidence_battery(&self, workspace: &Path, tools: &dyn ToolChannel) -> Result<Vec<BatteryRecord>>;
  ```
- 电池在**冻结 A_t 之前**、作用于**真实 workspace**（与 DR-1 一致）；原始 payload 落
  `<workspace>/.hoh/deterministic/raw/<step>.json`，汇总落 `<workspace>/.hoh/deterministic/battery.json`，
  并整体复制进候选视图（`candidate/.hoh/deterministic/**`）。
- `BatteryRecord.supports` 必须声明该步能为哪些 PRD 需求提供证据（映射 `F1..F17` 与 `N1..N4`），
  使 Tester 的 claim 推导有可核对骨架。
- **Godot 最小电池（顺序固定）**：
  1. `get_editor_errors`（启动前基线）；
  2. `play_scene`（主场景）+ **就绪等待**（见 DR-20）；
  3. `get_game_scene_tree` → 节点树存在性；
  4. 截图（`get_game_screenshot` 或 `capture_frames`）→ 存 `evidence/*.png`，必须与节点树**同一时刻**；
  5. 输入回放：`simulate_action`/`simulate_sequence`（`move_right` 至少 1 秒）+ `monitor_properties` 记录
     `Player` 的 `position`（起点/终点）→ 供 E3「坐标发生变化」判定；同法覆盖 `jump`、`move_left`；
  6. 节点断言：对 PRD 点名的节点（`Player`、`Goal`、`HUD`、`Enemy*`、`Coin*`）取属性 +
     `Goal`/实体必须有碰撞体（`get_collision_info`，`shape_count > 0`）；HUD 必须有可见文本节点；
  7. `stop_scene`。
- **失败必须如实记录**：某步失败时 `ok=false` 且 `record.observation` 写明失败原因（含 JSON-RPC code/message 原文），
  并作为「证据不可用」交给 Tester——**不得**伪装成「无错误」或跳过。Tester 对该步所支撑的 claim 必须判 `gap`。
- **Tester prompt 改写**：主职责从「采集每项证据」改为「**判定**——读取电池记录与原始文件，推导 checkable claims，
  只把被可见证据支持的 claim 标 `verified`，其余标 `gap`」；仍可补充少量自己的只读/执行调用，但不得把证据采集
  当作主要工作。证据文件引用一律使用**相对路径**。

### DR-18 步数预算与「先收口」纪律

现行 `step_limit=60` 已被证明不够（5/5 次调用全部 `LimitsExceeded`）。规范：
- `agent.step_limit` 默认 **150**；`agent.wrap_up_steps` 默认 **25**。
- 角色 prompt 末尾必须追加硬性说明：「你最多有 `step_limit` 步；当剩余步数 ≤ `wrap_up_steps` 时，
  你必须**立即**写出符合契约的产物骨架，之后再补充完善。」
- **顺序纪律**：Tester 必须在最开始的几步内先写一个**最小合法 `evidence.json`**（可只含 1 条 gap 记录），
  再逐步充实；Planner/Developer 同理先保证「有可提交产物」。
- **收口重试（wrap-up retry）**：若某角色以 `LimitsExceeded` 收尾**且**其产物缺失/不合法，
  Runtime 允许**额外一次**该角色调用，预算较小（`min(wrap_up_steps, 30)` 步），
  `retry_context` 说明「上一次因步数耗尽未收口，本次只许写产物、不得再做探索」。每轮每角色**至多一次**。
- `result.json` 必须逐次记录 `exit_status`、`attempts`、`wrap_up_retry_used`。

### DR-19 密钥不得进入角色子进程环境（C11 修正，安全）

根因（第一次真跑实测）：mini 的 `LocalEnvironment` 把**父进程环境整体透传**给子 shell，而 Runtime 按 C11
把密钥装在自身进程环境里，于是 Tester 一条 `cmd /c set HOH` 就让密钥明文进入轨迹与模型上下文。

- 构造角色 `LocalEnvironmentConfig.env` 时，**必须显式覆盖**下列变量为空串，以阻断继承：
  `HOH_MODEL_API_KEY`、`OPENAI_API_KEY`、`LITELLM_API_KEY`、`MSWEA_MODEL_API_KEY`（不存在也写入空串，代价为零）。
- 运行结束时（以及每次角色调用结束后）对 `runs/<id>/**` 执行**已知密钥值扫描 + 擦除**：
  命中处替换为 `<redacted>`，命中文件数写入 `result.json.secret_redactions`（**不得**打印密钥内容）。
- `skills`/prompt 中明确禁止角色读取或回显环境变量中的密钥；`godot-dev.md` 的调用示例一律使用 `$HOH_ARTIFACT_DIR`。
- 测试：①断言 role env 中上述变量均为空串；②构造「工具输出包含密钥」的场景，断言落盘后已被擦除且计数正确；
  ③断言 meta.json 与全部 `traj/*.json` 中不含密钥字面量。
- 已知并接受：用户判定当前密钥为局域网本地服务凭据、暂不轮换（D19 记录为已接受风险）；但本隔离仍必须实现。

### DR-20 MCP 就绪等待、重试与错误诊断

实测失败：`get_editor_errors` → `-32603 无法打开日志文件`；`get_game_scene_tree` → `等待游戏响应超时 (5秒)`；
截图 → `-32603 截图文件不存在…MCPScreenshot autoload 未激活`；`--args-file` 相对路径解析失败。

- **就绪等待**：`play_scene` 之后必须轮询 `get_game_scene_tree` 直到成功或超时
  （间隔 500ms、上限 `tools.ready_timeout_seconds`，默认 30s），再做任何依赖运行时的调用。
- **重试**：`get_editor_errors` 与截图调用失败时按 `tools.max_retries` 重试（间隔 1s）。
- **错误原文**：所有 MCP 失败的 `code` 与 `message` 必须写入
  `<workspace>/.hoh/deterministic/mcp-errors.jsonl`，并在对应 `BatteryRecord.observation` 里带上原文。
- **`--args-file`**：工具桥必须接受绝对路径；文件不存在时错误信息必须含**期望的绝对路径**；
  `skills` 中的示例必须使用 `$HOH_ARTIFACT_DIR` 展开后的绝对路径写法。
- **不得**把失败静默当成「无错误」；失败步的观察文本必须显式含 `UNAVAILABLE`/`FAILED` 字样，供 Tester 判 gap。

### DR-21 干净 A₀ 与可复现起点

实测问题：`.workspace/mario` 已被前两次尝试污染（存在 Player/Goal/HUD 节点与 `mcp/` 临时文件），
不再是 `OPEN-4` 约定的「空 Godot 工程 + 插件骨架」，跨轮不可比。

- 新增 CLI 开关：`hoh run --fresh-workspace`：清空 workspace 内容并调用 `adapter.initialize` 重建 A₀；
  另有 `--reset-workspace`：回滚到本次 run 的 A₀ 快照。
- `meta.json` 必须新增 `start_state: { mode: "fresh" | "reset" | "as_is", version_id: Option<String> }`。
- **真实冒烟的任务书必须使用 `--fresh-workspace`**（除非明确要续跑）。
- 测试：①`--fresh-workspace` 后 workspace 等于 `initialize` 的产物（忽略 `.hoh`）；②A₀ 快照在任何角色调用前已存在。

### DR-22 记录与日志对称性

- 每个角色**每次尝试**都必须同时产出：`iter-<t>/traj/<role>.attempt<N>.json` 与
  `iter-<t>/logs/<role>.attempt<N>.log`；两者都必须含 `exit_status`、`duration_ms`、`usage`、`artifact_path`。
- 修复实测缺陷：`logs/planner.log` 缺失；developer 轨迹命名与其它角色不一致。
- `usage.json` 增加**逐角色逐次尝试**明细（`attempts: [{role, attempt, calls, tokens...}]`），并保留原有汇总。
- 测试：断言一轮 run 后 `traj/` 与 `logs/` 的文件名集合一一对应（attempt 级别）。

### DR-23 Developer 产出定义与 skills 强化

实测问题：本轮 A₀→A₁ 唯一新增脚本 `player.gd` 为 **0 字节**，玩家坐标恒 `(0,0)`、Goal 无碰撞体、HUD 无 Label。

- `developer.md` 必须新增「**完成的定义**」：
  - 本轮计划的每条可观察行为都必须能从**电池记录（回放/截图/节点属性）**中被观察到；
  - 严禁留下空文件；写入脚本后必须回读自校验（`read_script` 或 shell 读回非空）；
  - 必须保证 `N1`（任何轮次 A_t 可启动）与 `N2`（可观测性）。
- `skills/godot-dev.md` 必须给出**可复制、经真实运行验证**的最小配方（≥4 条）：
  ① `hoh tools call <tool> --args-file $HOH_ARTIFACT_DIR/args/<name>.json`（绝对路径）；
  ② 用 `create_script`/`edit_script` 写出**非空** GDScript，并立刻 `read_script` 验证；
  ③ 为 `CharacterBody2D`/`StaticBody2D` 添加 `CollisionShape2D` + `RectangleShape2D`（否则无碰撞）；
  ④ 为 `Area2D`（如 `Goal`）添加碰撞体（否则 `shape_count=0`，胜负条件不可能触发）；
  ⑤ HUD 使用 `Label` 并设置非空 `text`；
  ⑥ 用 `simulate_action` + `monitor_properties` 自测「坐标发生变化」。
- `skills/godot-testing.md` 必须说明：电池已提供哪些记录、如何在 `evidence.json` 中以相对路径引用、
  以及「源码存在 ≠ 行为验证」。

---
### 12.1 变更记录

| 版本 | 日期 | 变更 | 触发 |
|---|---|---|---|
| v0.1 | 2026-09 | 初版（阶段三冻结） | 概要设计确认 |
| v0.1a | 2026-09 | §4.4 补强 QA 三件套与 `WorkspaceDriftBeforeQa` | 自查发现绝对路径逃逸风险 |
| v0.2 | 2026-09 | 追加 §12（DR-1..DR-13）并改写 §4.4 执行顺序 | 阶段五第一次独立验收 verdict=fail |
| v0.3 | 2026-09 | 追加 §12（DR-14..DR-16）并改写 §3.1 的 model 段：模型身份改为配置驱动、doctor 探测通用化、密钥卫生 | 用户更换为远端 `deepseek-v4.1-flash`（D15） |
| v0.4 | 2026-09 | 追加 §12（DR-17..DR-23）：确定性证据电池、步数预算与先收口纪律、密钥不得进子进程环境、MCP 就绪等待与诊断、干净 A₀、记录对称性、Developer 产出定义与 skills 强化 | 第一次真实 T=1 冒烟（negative baseline：5/5 LimitsExceeded、QA 无 E_1、A_1 零功能增量、密钥经子进程环境泄漏）（D17/D18） |
