# DESIGN-DETAIL — hof-rs 的 Bevy 0.19.1 适配器（详细设计工件）

- 状态 / Status: **草稿，标注"待确认"处均取推荐默认值**；用户确认 `DESIGN-OVERVIEW` 与 `PRD` 的 6 点后定稿
- 上游 / Upstream: `REQUIREMENTS.md`（§9 确认、§10 SPIKE-2 裁决）、`DESIGN-OVERVIEW.md`、`PRD.md`、`SPIKE-1/2-REPORT.md`、`DECISIONS.md` D296
- 目标精度：**另一个工程师照此实现，无需再做设计决策**

---

## 1. `GameAdapter` trait（定稿签名）

```rust
pub trait GameAdapter {
    fn engine(&self) -> EngineId;                                  // Bevy0191 / Godot48Legacy
    fn prepare(&mut self, p: &Project) -> Result<Prepared>;         // 构建 + 契约校验
    fn start(&mut self, p: &Prepared) -> Result<RunningGame>;       // 启动 + 等到可观测
    fn stop(&mut self, g: RunningGame) -> Result<StopReport>;       // 收尾、保留证据
    fn read(&mut self, kind: SemanticKind) -> Result<Reading>;      // 逐调用读语义（禁 batch）
    fn inject(&mut self, intent: &Intent, level: bool) -> Result<InjectionReport>;
    fn wait_frames(&mut self, n: u32) -> Result<FrameMark>;         // [待确认①] 是否并入 read()
    fn health(&mut self) -> Result<Health>;
    fn validate_artifact(&self, p: &Project) -> Result<GateVerdict>;// 复用既有门分类
}
```

**失败语义**：全部返回 `Result`；**不得 panic**；任务级失败 → `Err`，证据级失败 → `Reading{failed:true, reason}`（供电池判定"未观测"）。
**[待确认①]** `wait_frames` 作为独立方法（推荐，见 §4 时序），还是并入 `read()` 的 `settle` 参数。

## 2. 两层工具面（MCP 工具清单，逐字冻结）

### 2.1 通用层（23 个 BRP 动词的 1:1 pass-through）
工具名 = 动词原名（**不做旧 Godot 名字映射**）；参数/返回 schema **机械生成**；只做 schema 校验、policy 白名单、脱敏挂钩、证据绑定，**不加语义**。

### 2.2 语义层（8 个，绑定冻结契约）

| 工具名 | 参数 | 返回 | 冻结依据 |
|---|---|---|---|
| `bevy_player_transform` | `{}` | `{x:f64,y:f64,frame:u64}` | `Transform` 的 `translation.x/.y`（**点号路径，禁数组下标**） |
| `bevy_grounded` | `{}` | `{grounded:bool,frame:u64}` | 接地组件 |
| `bevy_coin_counter` | `{}` | `{coins:i64,frame:u64}` | 金币计数资源 |
| `bevy_win_flag` | `{}` | `{won:bool,frame:u64}` | 胜利位资源 |
| `bevy_inject_move` | `{dir:-1\|0\|1, level:true}` | `{accepted:bool}` | 注入意图事件（**命名字段**） |
| `bevy_inject_jump` | `{press:bool}` | `{accepted:bool}` | 同上 |
| `bevy_wait_frames` | `{n:u32}` | `{frame_after:u64}` | 帧推进 |
| `bevy_health` | `{}` | `{alive:bool,stderr_tail:string}` | 进程存活与错误面 |

**一致性硬规则**：**每次读都必须逐调用**；**禁止 batch**（非帧原子，会产生假一致快照）。
**[待确认②]** 8 个动词是否定稿（是否需要额外的只读量，如 `gravity`/`max_coins`）。

## 3. 类型路径清单（`contract.rs`，冻结哈希入证据）

语义层每个动词绑定下列**全限定类型路径（含 crate 名）**，写入 `contract.rs` 的 `CONTRACT: &[ContractEntry]`，并计算
`contract_sha256 = sha256(canonical_json(CONTRACT))`，随每轮证据落盘；**路径变更 = 契约变更**，走决策流程。

| 语义 | 形态要求 |
|---|---|
| 玩家标记 | `#[reflect(Component)]` + `register_type` |
| `Transform` | 只读 `translation.x/.y` |
| 接地状态 | `#[reflect(Component)]`，布尔 |
| 金币计数 | `#[reflect(Resource)]`，整型 |
| 胜利位 | `#[reflect(Resource)]`，布尔 |
| 注入意图 | `#[reflect(Event)]`（或 Resource），**必须带命名字段** |

**[待确认③]** 采用"清单常量 + 规范 JSON 哈希"（推荐）。SPIKE-1 实测：**单元结构体事件经 `observe+watch` 收不到帧** ⇒ 契约定为**命名字段**。

## 4. 时序与读一致性

```
wait_ready: 轮询 15702 rpc.discover，间隔 500ms，超时 30s（实测就绪 620ms headless）
每次观测: wait_frames(k) → read(...)   // k 由电池给出，保证读到稳定态
注入:    inject(intent, level=true) → 游戏每帧自清边沿（实测 2px vs 92px）
```
**禁止**：把"读基线 + 注入 + 读结果"塞进一个 batch（非帧原子）。

## 5. 构建契约（写入适配器契约，`prepare()` 校验）

| 项 | 规则 |
|---|---|
| 工具链 | `rustc ≥ 1.95`（实测 1.98）；Bevy **0.19.1 钉死** |
| feature 集 | **冻结**（漂移使暖增量 18s → 236s）；清单哈希入证据 |
| 锁文件 | `Cargo.lock` 哈希入证据；**不得在轮内变更** |
| target 目录 | **共享持久 target**（提升暖增量）；每轮记录命中率 |
| 预热 | 轮 0 预热；预算：**冷 ≤600s（实测 251s）/ 暖 ≤120s（实测 12s）/ 单轮 ≤300s** |
| 运行模式 | **headless 开关**（环境变量）——**每轮与 CI 一律 headless**（窗口模式实测 4 FPS 无法观测） |
| 端点 | **只依赖 15702**；15703 仅在存在渲染世界时存在，**不得依赖** |
| 传输 | HTTP/1.1 JSON-RPC 2.0；**HTTP 恒 200 ⇒ 必须解析 body 判成败**；仅回环；无认证/TLS |

## 6. 证据布局（每轮）

```
runs/bevy-<round>/
  meta.json                 # 退出码、分量、contract_sha256、feature_sha256、lock_sha256
  build.log                 # 构建耗时与 Compiling 证据
  launch.json               # headless 开关、端口、启动→就绪耗时
  calls/<seq>-<tool>.json   # 每次 MCP→BRP 调用的原始请求/响应（含时间戳与序号）
  readings/<semantic>.json  # 五条判据的读数与结论
  gate.json                 # 门裁定与 reasons
  qa/                       # Tester 的 QA 报告与快照哈希
```
**每次调用落一份原始 JSON**是判据(3)的证据基础（**禁止**由模型自撰脚本产生证据）。

## 7. 错误码与超时

| 情形 | 处理 |
|---|---|
| 端点未就绪 | 轮询至 30s，超时 → `Err(EndpointTimeout)`，门记 `infrastructure_failure`（**不**算项目缺陷） |
| body 内 JSON-RPC error | 解析 body → 映射为工具错误；**不得**因 HTTP 200 视为成功 |
| 进程退出 | `health()` → `alive:false`；读 stderr 尾部入证据 |
| 构建超预算 | 门记 `build_budget_exceeded`（**不**算项目缺陷） |
| 类型路径缺失 | `Err(ContractViolation)`，门关（**算**项目缺陷，因 PRD 要求该契约） |

## 8. 测试策略（TDD）

**必须有测试的行为**：
1. **纯函数**：工具名/schema 冻结哈希；`contract.rs` 规范 JSON 哈希；body-错误映射；超时计算。
2. **替身（fake BRP server）**：用本地假 HTTP 服务模拟 23 动词与错误，测 `brp.rs` 全部路径（含 **HTTP 200 + body 错误**、乱序响应、慢响应）。
3. **`GameAdapter` 契约测试**：对**假实现**与（可选、标记 `#[ignore]` 的）真实现各跑一遍，验证 §1 失败语义。
4. **电池级**：注入→等待→读的五条断言，使用**录制的 BRP 转录**（真实 SPIKE 数据）作为输入，**保证"单调下落不算"这类判据被真红覆盖**。
5. **集成（`#[ignore]`，需 GPU/引擎）**：真机 smoke——**这些测试不进默认门**，但必须存在并可在有环境时运行。

**验收标准如何被逐条验证**：E1..E6 各对应 §6 中的具体文件与字段；**验证脚本必须能对同一份 `runs/` 重算结论**（可复现性的机械保证）。

## 9. 待确认清单（阻塞定稿的两组）

**概要设计**：① `wait_frames` 是否独立方法 ② 语义层 8 动词是否定稿 ③ 契约冻结方式（`contract.rs` + 规范 JSON 哈希）
**PRD**：④ 玩法规模（单关卡/几何图元/无美术音频）是否够 ⑤ 六项语义面是否即契约全部 ⑥ 金币可否多次收集、有无上限
