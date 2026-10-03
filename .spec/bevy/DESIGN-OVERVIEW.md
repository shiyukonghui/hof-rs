# DESIGN-OVERVIEW — hof-rs 的 Bevy 0.19.1 适配器（概要设计工件）

- 状态 / Status: **待用户确认**（确认后进入详细设计）
- 上游 / Upstream: `.spec/bevy/REQUIREMENTS.md`（含 §9 用户确认、§10 SPIKE-2 裁决）、`.spec/bevy/SPIKE-1-REPORT.md`、`.spec/bevy/SPIKE-2-REPORT.md`、`DECISIONS.md` **D296**
- 原则 / Principle: **适配器只做"引擎相关"的事**；流水线、门、电池、证据、完整性审计、冻结视图全部**引擎无关、原样复用**。

---

## 1. 架构分层与模块划分

```
runtime/            （既有，引擎无关，不改语义）
  run_loop · role · model · schema · secrets · evidence · hygiene · policy · frozen_view · integrity
adapter/            （新增 trait 边界）
  mod.rs            trait GameAdapter —— 引擎中立的能力面
  godot.rs          Godot 实现（legacy：保留、仍可编译、不再演进）
  bevy/             Bevy 0.19.1 实现（本批新增）
    mod.rs          BevyAdapter（实现 GameAdapter）
    build.rs        cargo 构建、预算、共享 target、冻结 feature 集、锁文件哈希、轮 0 预热
    launch.rs       同一二进制 + 运行时 headless 开关、端点发现与钉死 15702、就绪轮询
    brp.rs          JSON-RPC 2.0 over HTTP/1.1 客户端（恒 200 ⇒ 解析 body 判成败；禁止 batch）
    contract.rs     可反射语义契约（类型路径清单）与其冻结哈希校验
  mcp/              （新增）薄层 MCP 服务
    generic.rs      通用层：23 个 BRP 动词的 1:1 pass-through
    semantic.rs     语义层：<10 个绑定冻结契约的动词
    server.rs       MCP 传输与 schema 校验、policy 白名单、脱敏挂钩、证据绑定
```

**职责边界（硬性）**：
- `adapter/bevy/**` **不得**包含玩法逻辑；游戏的实现永远是 **Developer 角色**的产出。
- `runtime/**` **不得**出现 `bevy` 或 `godot` 字样；全部经 `GameAdapter` trait 间接调用。
- `adapter/godot.rs` 只允许**编译性适配**（trait 改动引起的签名对齐），**功能冻结**。

## 2. `GameAdapter` trait（引擎中立能力面）

按"能力"而非"引擎"命名，使 Godot/Bevy 都能实现：

| 能力 | 语义 | Bevy 侧实现要点 |
|---|---|---|
| `prepare(project) -> Prepared` | 构建产物、校验构建契约 | 冻结 feature 集 + 锁文件哈希 + 共享 target + 预算检查 |
| `start(prepared) -> RunningGame` | 启动并**等到可观测** | headless 运行开关；轮询 **15702** 直到 `rpc.discover` 成功或 30 s 超时 |
| `stop(game)` | 收尾、保留证据 | 释放端口、保留进程 stdout/err |
| `read_semantic(kind) -> Value` | 读**契约语义** | 逐调用（**不 batch**）读反射组件/资源 |
| `inject(intent, level)` | 注入**电平触发**意图 | 写反射资源或触发**带命名字段**的反射事件；边沿由游戏自清 |
| `frame_marker() -> FrameId` | 帧推进/等待 | 等待 N 帧后再读，避免读到中间态 |
| `health()` | 错误/日志/存活 | 读进程 stdout/err 与引擎侧错误面 |
| `validate_artifact(project) -> Gate` | 产物可交付性判定 | 复用既有门分类（真实项目缺陷 vs 基础设施） |

**不放入 trait 的**：截图（用户已决定不纳入判据）、玩法断言（属电池与判据层）。

## 3. 两层工具面（关键设计）

**通用层（1:1 pass-through）**：把 BRP 的 **23 个动词**按**原名词**映射为 MCP 工具，参数/返回 schema 由本层机械生成。
**语义层（<10 条，绑定冻结契约）**：只暴露与判据直接相关的最小面，例如
`bevy_player_transform` · `bevy_grounded` · `bevy_coin_counter` · `bevy_win_flag` · `bevy_inject_move` · `bevy_inject_jump` · `bevy_health` · `bevy_wait_frames`。

**两条硬性规则**：
1. **不做名字映射**：绝不把旧 177 条 Godot 工具名映射到 BRP 动词（语义面完全不同）。
2. **类型路径就是契约**：语义层动词背后绑定的**全限定类型路径**（含 crate 名）写入 `contract.rs` 的清单并**冻结其哈希**；类型路径变更 = 契约变更，须显式走决策流程。

## 4. 关键数据流（一轮的形状）

```
hoh init(空工程) → prepare(cargo build, 预算/feature/lock 校验)
  → start(headless, 等 15702 就绪 ≤30 s)
  → 逐调用读基线(coins/win/transform/grounded)         ← 禁止 batch
  → inject 电平意图 → wait_frames → 读观测
  → 断言五条：位移改变 / coins 0→N / win false→true / 跳跃 rise>0 且 fall>0 / 起跳前 grounded=true
  → validate_artifact(门) → Tester(QA 冻结候选，禁改) → 证据落 runs/<round>/**
```

## 5. 备选方案与否决理由

| 决策点 | 选择 | 被否决的选项与否决理由 |
|---|---|---|
| 运行期工具面 | **自建薄 MCP 包装 BRP** | ①依赖 `Nub/bevy_mcp`：工具集与演进不由我们控制，**冻结契约无从保证**；②harness 直连 BRP：丢掉可冻结契约、schema 校验、policy 白名单、脱敏与证据绑定 |
| 运行模式 | **同一二进制 + 运行时 headless 开关** | ①只用窗口模式：实测 **4.0 FPS**、弧线仅 6 点 ⇒ **无法观测**；②延后 headless：一旦游戏把语义放进渲染侧组件，切 `backends:None` **会丢渲染世界**，将来须重新设计 |
| 注入机制 | **电平触发 + 带命名字段事件** | ①每帧清零：实测 0.4 s 仅走 **2 px**（电平后 92 px）；②单元结构体事件：`observe+watch` **收不到帧**（根因未定位） |
| 一致性读取 | **逐调用** | **batch 非帧原子**：同一批 24 个相同调用返回中同时出现 coins:1 与 coins:2 ⇒ 会制造**假一致快照** |
| 截图证据 | **不纳入判据** | BRP 原生无截图动词；纳入则 PRD/模板/门都多一条可失败路径，而 ECS 语义证据更强 |
| Godot 处置 | **legacy 保留可编译** | 删除会摧毁已冻结契约与既有验收证据链 |

## 6. 非功能性要求与对策

- **性能/预算**：冷 ≤600 s（实测 headless 251 s）/ 暖 ≤120 s（实测 12 s）/ 单轮 ≤300 s / 端点等待 30 s（实测就绪 620 ms）。
  对策：共享持久 target、**冻结 feature 集**（漂移会把暖增量 18 s 变 236 s）、冻结 `Cargo.lock`、轮 0 预热。
- **安全**：BRP 无认证、无 TLS ⇒ **只绑回环**，适配器**不得**暴露非回环接口；证据中不得落环境变量转储（沿用既有脱敏）。
- **兼容性**：Bevy **0.19.1 钉死**；`rustc ≥1.95`（实测 1.98）；锁文件哈希入证据。
- **可维护性**：trait 化后新增引擎只需实现 trait；语义契约集中在 `contract.rs` 便于冻结与审计。
- **可观测性**：每轮落 `runs/<round>/**`：构建日志、启动耗时、**每次 BRP 调用的原始 JSON（含序号/时间戳）**、五条断言的读数、门读数。

## 7. 风险与回滚点

| 风险 | 影响 | 对策 | 回滚点 |
|---|---|---|---|
| feature 集漂移 | 暖增量 18 s → 236 s | 冻结 feature 集并校验哈希 | 恢复冻结清单 |
| `bevy_remote` 无条件拉 `bevy_dev_tools` | 仍编译 render/wgpu/naga/pbr（冷构建 −17% 有限） | 接受（已实测）；必要时评估裁剪 | 无关，纯成本 |
| `+watch` 用 `bounded(8)+try_send` | 慢消费者**静默关流** | 电池不依赖 watch；改逐调用轮询 | 弃用 watch |
| 无真·无桌面环境实测 | CI 可行性未证 | 记为未验证项；C4 证据是结构性的（winit 不在依赖图） | 补 spike |
| 软件适配器未测 | 无 GPU 机器行为未知 | headless 不依赖 GPU（已证明），故不受影响 | — |
| 类型路径变更 | 契约破坏 | 冻结哈希 + 决策流程 | 恢复清单版本 |

**整体回滚**：删除 `adapter/bevy/**` 与 `mcp/**` 即回到 Godot 时期状态（`origin/master` 的 `55a0751`）；Godot 路径始终可编译。

## 8. 与详细设计的接口（本工件的下游）

`DESIGN-DETAIL.md` 必须精确到"另一个工程师照着就能实现"：
1. **每个工具**：名称、参数 schema、返回 schema、错误码与超时、幂等性；
2. **类型路径清单**（`contract.rs` 冻结内容）与其哈希算法；
3. **`GameAdapter` 每个方法**的签名、前置/后置条件、失败语义；
4. **证据文件布局**与命名（含每次调用的原始 JSON）；
5. **构建契约**的具体落点（feature 清单、锁文件哈希位置、target 目录策略、轮 0 预热流程）；
6. **测试策略**：哪些行为必须有测试、如何用替身（fake BRP server）验证、验收标准如何逐条被验证。

---

## 9. 需要你确认的三点

1. **trait 形态**：能力面按上表（prepare/start/read_semantic/inject/frame_marker/health/validate_artifact）是否合适？是否需要把 `frame_marker` 并入 `read_semantic`？
2. **语义层动词集合**：`<10` 条是否按上表定稿（是否还要 `bevy_camera_*` 之类，虽然不取截图）？
3. **契约冻结方式**：类型路径清单集中在一个 `contract.rs` 并以哈希冻结（我倾向"清单文件 + 哈希入证据"），是否可以？
