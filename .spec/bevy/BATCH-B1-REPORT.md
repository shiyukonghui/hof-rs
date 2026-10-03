# BATCH-B1 REPORT — the engine-neutral runtime surface, the frozen contract, the BRP client, the two-layer tool surface, the evidence layout

- 日期 / Date: 2026-10-04
- 执行者 / Executor: implementation subagent (no prior context; followed the task书 as authoritative)
- 上游 / Upstream, read in order and treated as binding: `.spec/bevy/REQUIREMENTS.md`,
  `.spec/bevy/DESIGN-OVERVIEW.md`, `.spec/bevy/DESIGN-DETAIL.md`, `.spec/bevy/PRD.md`,
  `.spec/bevy/SPIKE-1-REPORT.md`, `.spec/bevy/SPIKE-2-REPORT.md`, `DECISIONS.md` **D296**,
  plus the existing conventions in `src/adapter/godot.rs` and `src/runtime/run_loop.rs`.
- 范围 / Scope: exactly the five tasks in the batch order. The Bevy adapter itself
  (`BevyAdapter`, real build/launch orchestration, battery wiring) is **not** in this batch and is
  named explicitly in §9.
- 交付物 / Deliverable: **this file** (`BATCH-B1-REPORT.md`, the name the batch order specifies;
  a status check referenced it as `TASK-B1-REPORT.md` — that is the same report, this one).
  **`DECISIONS.md` was not touched** (forbidden): the decision entry for this
  batch (D297) is the parent's to write — see §9.

> **中文 TL;DR**
> 1. 五个任务全部落地：`GameAdapter` trait（含两级失败语义）+ Godot 对齐、冻结的 `contract.rs`
>    （6 个语义面 + 规范 JSON sha256）、`brp.rs`（15702、恒 200 解 body、就绪轮询、禁 batch）+
>    进程内假 BRP 服务、两层 MCP 工具面（23 通用 + 8 语义，工具清单哈希已钉死）、
>    `runs/bevy-<round>/` 证据布局。
> 2. **Godot 行为零改动**：只改了该文件顶部的 `use` 列表并追加一个 `impl GameAdapter` 块（+116/−2），
>    原有任何一行逻辑、常量、测试都没动；`read`/`inject` 用「未观测/被拒」的证据级失败作答，
>    `prepare`/`start`/`stop`/`wait_frames`/`health` 是任务级 `Err(Unsupported)`，
>    `validate_artifact` 复用既有 DR-37/DR-86 判定。
> 3. 三个哈希已冻结并钉在测试里：contract `4af153e7…`、feature set `d6a90ba3…`、
>    tool list `e177325f…`。
> 4. 门禁：`cargo test --offline` **literal exit code 0**，基线自己复现为 653 passed / 0 failed /
>    7 ignored / 660 listed，本批为 **751 passed / 0 failed / 8 ignored / 759 listed**（新增 98 个
>    通过、1 个故意 `#[ignore]` 的真机 smoke）；`cargo fmt --all --check` exit 0；
>    强制重建（Python glob + remove-tree 清 fingerprint，再按 `git ls-files` 逐个 touch 101 个
>    `.rs`）后重跑通过。
> 5. 5 个受控植物，每个都「绿—红—恢复后绿」，且恢复经 sha256 断言逐字节相同。
> 6. `runs/**` 零写入；`godot-mcp/**`、`DECISIONS.md`、`PRD.md`、引擎树、`Cargo.toml`/`Cargo.lock`
>    零改动；未 push；未用 `rm -rf`；未用 `git checkout --`。

---

## 1. 任务一：`GameAdapter` trait 及其失败语义

**交付**：`src/adapter/mod.rs`（+514 行，纯追加；模块声明 `pub mod bevy; pub mod mcp;` 两行）。
`DESIGN-DETAIL.md` §1 的九个方法**逐字**落地，全部 `Result`；**本批新增的生产代码里 0 处
`unwrap()/expect/panic!/todo!/unimplemented!`**（`F:\b1-scratch\py\panic_probe.py` 机械核对，
逐个模块列出生产段的行号；`godot.rs`/`mod.rs` 命中的是**既有**代码的下标索引，本批未触碰）：

| 方法 | 语义（本批实现） | 失败级别 |
|---|---|---|
| `engine()` | `EngineId::Bevy0191` / `Godot48Legacy`，`as_str()` 给出 `bevy-0.19.1` / `godot-4.8-legacy` | 不失败 |
| `prepare(&Project)` | 构建产物 + 校验构建契约（落在下一批的 `build.rs`） | 任务级 `Err` |
| `start(&Prepared)` | 启动并等到可观测（下一批：轮询 15702 ≤30 s） | 任务级 `Err` |
| `stop(RunningGame)` | 收尾、保留 stdout/stderr | 任务级 `Err` |
| `read(SemanticKind)` | 逐调用读语义（禁 batch） | **证据级**：`Reading::not_observed(kind, frame, reason)` |
| `inject(&Intent, level)` | 电平触发注入 | **证据级**：`InjectionReport::refused(frame, reason)` |
| `wait_frames(n)` | 帧推进（设计待确认①：保持独立方法，不并入 `read`） | 任务级 `Err` |
| `health()` | 进程存活 + stderr 尾部 | 任务级 `Err`（进程不存在时不得报 `alive:false` 为“已知死”） |
| `validate_artifact(&Project)` | `GateVerdict` = **复用** `crate::model::ArtifactGate`（设计要求复用既有门分类） | 任务级 `Err` |

**失败语义的三条硬规则**（写在模块文档里，并有测试钉住）：

1. 任务级失败 → `Err(AdapterError::…)`，且 `AdapterError` 是**分类的**，因为门要按类判：
   `EndpointTimeout` = `infrastructure_failure`（不算项目缺陷）；`ContractViolation` = 项目缺陷
   （PRD §3-C2 要求该语义面存在）。
2. 证据级失败 → 一个**说明原因的读数**。`Reading::not_observed` 强制 `value = Null` 且
   `failed = true`，所以忽略 `failed` 的电池不可能把“没观测到”当成数据；`InjectionReport::refused`
   同理。这正是 E6（裁决诚实）可机械检查的前提。
3. 不得 panic。`Reading`/`InjectionReport`/`Health`/`StopReport`/`FrameMark` 都是可序列化的值，
   证据直接落盘。

**钉住它的测试**：
`adapter::game_adapter_tests::{the_capability_surface_is_object_safe, an_unobserved_read_says_why_and_never_carries_a_value, a_refused_injection_says_why_and_is_not_accepted, the_move_direction_is_validated_once_for_every_adapter, an_intent_names_the_contract_field_it_writes, the_semantic_kinds_are_the_designs_four_reads, a_task_level_failure_is_typed_not_a_string}`
（含一个完整 `FakeGameAdapter` 实现——设计 §8-3 要求「对假实现也跑一遍」），
以及集成测试 `tests/bevy_adapter_b1.rs::the_legacy_godot_adapter_implements_the_capability_surface_without_panicking`。

**边界**：`Intent::move_dir(i8)` 是唯一的范围校验点（`-1|0|1`），抛 `anyhow` 错误而非 panic；
`Intent` 自带 `field()`/`value()`/`tool()`，把「写哪个契约字段」与契约绑在一起。

---

## 2. 任务一（后半）：对 legacy Godot 适配器的**确切**改动

`git diff --numstat src/adapter/godot.rs` → **+116 / −2**，且只有两处：

1. 顶部两行 `use`：
   - `use crate::adapter::{…ProjectAdapter}` → 增补本 trait 的类型名（`AdapterError, EngineId, FrameMark, GameAdapter, GateVerdict, Health, InjectionReport, Intent, Prepared, Project, Reading, RunningGame, SemanticKind, StopReport`）；
   - `use crate::model::{ExecKind, ExecRecord, Role}` → 增补 `ArtifactGate`。
   这就是那 2 行删除的**全部**内容。
2. 文件末尾追加一个 `impl GameAdapter for GodotAdapter` 块（+116 行，含文档注释与两个 `const` 原因串）。

**没有任何既有行为被改动**：没有改任何既有方法的签名/实现、没有改常量、没有改测试；Godot 路径
的全部既有测试在最终门里原样通过（既有 **660** 个测试 = 653 passed + 7 ignored，一个不少、
一个未改）。新 trait 的方法**当前没有任何既有调用方**（`runtime/**` 尚未改用它），所以也不存在
运行时行为差异。

**每个方法的失败语义（老实版）**：

| 方法 | Godot 实现 | 为什么 |
|---|---|---|
| `engine()` | `EngineId::Godot48Legacy` | 真实值 |
| `validate_artifact()` | **真实实现**：`developer_artifact_valid_in` + `developer_artifact_defects_in` → `ArtifactGate{applicable:true, launchable, reasons}`；缺陷列表为空时补一条显式说明，绝不给出“不可启动但无理由” | 复用 DR-37/DR-86 既有判定，不新增行为 |
| `read(kind)` | `Ok(Reading::not_observed(kind, 0, 原因))` | Godot 的观测通道是异步 MCP（`running_game_*`），这条同步面上**没有**观测；老实答“未观测”而不是 Err，好让电池记 gap |
| `inject(..)` | `Ok(InjectionReport::refused(0, 原因))` | 同上：输入没有被投递 |
| `prepare/start/stop/wait_frames` | `Err(AdapterError::Unsupported{capability, reason})` | 游戏生命周期在异步 `ProjectAdapter::start_round_game`/`stop_round_game`（`ToolChannel`）上，同步桥接就等于新造行为，而 D296 冻结了 Godot 侧 |
| `health()` | `Err(AdapterError::Unsupported{…})`，理由：Godot 适配器从不拥有游戏进程（进程归编辑器的 MCP server），没有 pid/stderr 可报 | 报 `alive:false` 会是一条假知识 |

---

## 3. 任务二：冻结的可反射契约 `contract.rs`

**交付**：`src/adapter/bevy/contract.rs`（402 行）。`CONTRACT: &[ContractEntry]` 是 6 个语义面
（与 `DESIGN-DETAIL.md` §3 的表格逐行对应），每个条目携带 `surface / type_path / reflect /
semantic_tool / shape`：

| surface | 全限定类型路径 | reflect | 绑定工具 |
|---|---|---|---|
| `player_marker` | `hof_game::contract::Player` | Component | `bevy_player_transform`（定位实体） |
| `player_transform` | `bevy_transform::components::transform::Transform` | Component | `bevy_player_transform` |
| `grounded` | `hof_game::contract::Grounded` | Component | `bevy_grounded` |
| `coin_counter` | `hof_game::contract::CoinCounter` | Resource | `bevy_coin_counter` |
| `win_flag` | `hof_game::contract::WinFlag` | Resource | `bevy_win_flag` |
| `input_intent` | `hof_game::contract::InputIntent` | Resource | `bevy_inject_move`, `bevy_inject_jump` |

- `contract_sha256 = sha256(canonical_json(contract_value))`，**`CONTRACT_SHA256 =
  4af153e77af87ceddb162c4b782701ee0b6c066a651d4e4b5d1e71f329649c69`**（测试里钉死）。
- `canonical_json` 自己实现（不依赖 serde 的 map 顺序）：递归、键字典序、无空白、字符串按 JSON 转义。
- `check_registered_type_paths(&[String]) -> Err(ContractViolation)`：给一组运行时已注册类型路径，
  缺任何一条契约路径即报错并逐条列出（`-23402/-23403/-23501/-23502` 也被登记为
  `CONTRACT_VIOLATION_CODES`，供 router 分类）。
- `check_game_crate_name` / `game_crate_name_of`：契约路径含 crate 名，所以**游戏 crate 必须叫
  `hof_game`**，否则报 `ContractViolation`。
- `SEMANTIC_TOOLS`（8 个名字）与 `TOOLS_WITHOUT_TYPE_PATH`（`bevy_wait_frames`, `bevy_health`）
  使「8 个语义工具 = 6 条契约绑定 + 2 条无类型面」可机械核对。

**钉住它的测试**：`canonical_json_is_whitespace_free_and_key_sorted`、
`canonical_json_is_stable_under_key_reordering`（键重排不变）、
`canonical_json_escapes_strings_like_json_does`、
`the_contract_hash_is_the_pinned_literal`、
`the_contract_hash_changes_when_any_entry_changes`（路径或 `shape` 任一改动都会移动哈希）、
`the_contract_is_six_surfaces_and_the_semantic_tools_are_fully_accounted_for`、
`every_game_declared_path_is_under_the_frozen_crate_and_module`、
`a_missing_type_path_is_a_contract_violation`、`the_game_crate_name_is_part_of_the_contract`、
`brp_contract_violation_codes_are_pinned`，外加集成测试
`the_frozen_contract_hash_and_crate_name_are_pinned`。

> **这是一个刻意冻结的选择，不是测量结果**：本批开始时没有游戏，`hof_game` 这个 crate 名与
> `contract` 模块名是**本批替 PRD/模板先定下来**的（PRD §3-C2 要求「路径须写入 `contract.rs` 并冻结」）。
> 若后续决定改名，那就是契约变更：`CONTRACT_SHA256` 会移动、测试先红、必须走决策流程重新钉。

---

## 4. 任务三：BRP 客户端 `brp.rs` + 进程内假 BRP 服务

**交付**：`src/adapter/bevy/brp.rs`（789 行，含测试与假服务）。落地 `DESIGN-DETAIL.md` §5/§7：

- **只依赖 15702**：`BRP_PORT = 15702`、`BRP_HOST = "127.0.0.1"`、`endpoint()` 恒为
  `http://127.0.0.1:15702/`；没有任何 API 默认指向 15703（要别的端口只能显式构造 client）。
- **恒 200 ⇒ 解析 body 判成败**：`read_document` 把非 null 的 `error` 映射为
  `BrpError::Rpc{code,message}`；`{"error":null,"result":…}` 才算成功；反过来，非 2xx 的 HTTP
  状态是 `HttpStatus` 错误（BRP 自己不会这样答，答了就是代理或另一个服务）。
- **就绪轮询 30 s**：`wait_ready(budget, interval)` 反复 `rpc.discover`，任何非就绪答复都重试，
  预算用尽 → `BrpError::EndpointTimeout{budget_millis}`（`is_infrastructure() == true`，门须记
  `infrastructure_failure`）。常量 `READY_POLL_INTERVAL = 500 ms`、`ENDPOINT_READY_BUDGET = 30 s`
  （设计 §4）。
- **绝不 batch**：`call(method, params)` 只收一个方法名；`request_body(id, method, params)` 只能
  产出**对象**；params 若给成数组直接 `InvalidRequest`；`read_document` 收到**数组**答复也拒绝
  （「本客户端从不 batch」）。没有批量 API 可写。
- **失败分类**：`BrpError::{Transport, Timeout, HttpStatus, Rpc, Malformed, EndpointTimeout,
  InvalidRequest}`，并给出三个判定：
  `is_method_not_found()`（`-32601` = 适配器 bug，SPIKE-1 §6.3）、
  `is_infrastructure()`、`is_contract_violation()`（`-23502` 等 = 项目缺陷）。
- **原始证据可用**：`call_document(id, method, params)` 返回**整个 JSON-RPC 文档**，
  `next_id()` 让每个请求有自己的 id，证据里落的就是引擎真正答的那份文档。
- 超时分类的一个实测细节：`ureq 2.12` 的 `ErrorKind` **没有** Timeout 变体，读超时是
  `Transport` 且 `message()` 为 `None`（实测打印：`kind=ConnectionFailed message="Connect error"
  waited=2.04s` 是**被拒连接**，而读超时是 IO 类）。因此分类顺序是：先看 kind
  （`ConnectionFailed`/`Dns` 一律 Transport，因为 Windows 上到已关闭回环端口的 connect 本身实测
  花了 **2.04 s**，仅凭「等了很久」会误判），再看消息与实测等待是否达到 timeout。

**假 BRP 服务**（`#[cfg(test)] mod fake`，进程内、离线、绑 `127.0.0.1:0`，`Drop` 时停线程并 join）：

- `FakeBrp::spawn(script)` + `Reply::{Json, Raw200, Status, DelayThen}`，脚本用尽后重复最后一条
  （所以就绪轮询不会“没脚本可答”）；`requests()` 暴露**原始请求体**，`refused_port()` 给出一个
  确定无人监听的回环端口。
- HTTP 逐字节自己实现（解析 `Content-Length`、回 `Connection: close`），因此 `ureq` 面对的是一个
  真客户端会面对的真协议。

**任务要求的五个 case，全部覆盖**（外加 9 个）：

| case | 测试 | 断言 |
|---|---|---|
| 正常答复 | `a_normal_reply_comes_back_as_its_result` | 返回 `result` |
| HTTP 200 + body 错误 | `an_error_body_under_http_200_is_a_tool_error` | `Rpc{-32601}`，`is_method_not_found()`，**不是** infrastructure |
| 慢答复超过超时 | `a_slow_reply_that_exceeds_the_timeout_is_a_timeout` | `Timeout{millis}`，`is_infrastructure()` |
| 连接被拒 | `a_refused_connection_is_a_transport_failure` | `Transport`，`is_infrastructure()` |
| 答复 JSON 非法 | `a_malformed_body_is_a_malformed_reply` | `Malformed`，且**不**算 infrastructure |
| 附加 | `a_null_error_with_a_result_is_a_success`、`a_resource_that_is_not_present_is_a_contract_violation`、`a_batch_reply_is_refused_rather_than_read`、`a_non_200_status_is_an_error_even_though_brp_always_answers_200`、`readiness_polls_until_discover_answers`、`readiness_gives_up_with_the_budget_it_was_given`、`the_request_body_is_one_object_with_one_method`、`the_client_puts_exactly_that_object_on_the_wire`、`the_client_refuses_a_list_valued_params_payload`、`every_request_carries_its_own_id_and_the_raw_document_is_available`、`the_pinned_endpoint_is_15702` | — |

---

## 5. 任务四：两层 MCP 工具面（23 通用 + 8 语义）

**交付**：`src/adapter/mcp/{mod.rs, generic.rs, semantic.rs, server.rs}`（+ `evidence.rs`，见 §6）。

### 5.1 通用层（1:1 pass-through，**零改名**）

- 23 个动词的权威来源：`bevy_remote-0.19.1/src/builtin_methods.rs` 的 `add_default_methods`
  （仓外解包源码，只读复核）+ SPIKE-1 §1.2 的活体 `rpc.discover`（`methodCount: 23`）。
  表在 `generic.rs::BRP_VERBS`，顺序与 SPIKE-1 表格**逐个一致**：
  `rpc.discover, world.get_components, world.query, world.list_components,
  world.get_components+watch, world.list_components+watch, world.get_resources,
  world.list_resources, world.insert_resources, world.mutate_resources, world.remove_resources,
  world.insert_components, world.remove_components, world.mutate_components, world.spawn_entity,
  world.despawn_entity, world.reparent_entities, world.trigger_event, world.write_message,
  world.observe+watch, registry.schema, schedule.list, schedule.graph`。
- **工具名 = 动词原名**（含 `+watch` 与点号，逐字不改）；参数表声明一次，schema 由
  `ToolSpec::input_schema()` 机械生成（`additionalProperties:false`，所以拼错参数是被拒而不是被忽略）；
  `streaming`（3 条 `+watch`）与 `mutating` 也都从同一张表导出。
- **不做旧 Godot 名字映射**的机械证据：`no_generic_tool_reuses_an_old_godot_tool_name` 与集成测试
  `the_generic_layer_keeps_the_verb_names_and_the_old_vocabulary_out` 用仓库自带的
  `tools::index::embedded_tool_schemas()`（177 条 Godot 工具快照）做交集断言——交集为空。
- **pass-through 的一条机械规则**：`arguments == {}` 时**不发 `params`**。理由是 BRP 用
  `Option<Params>` 区分「无参数」（`world.list_components` = 列全部已注册组件）与「空对象」
  （缺必填 `entity` ⇒ 报错）。非空则**逐字照发**（`the_client_puts_exactly_that_object_on_the_wire`
  与 `a_generic_call_passes_the_arguments_through_verbatim` 钉住）。

### 5.2 语义层（8 条，绑定冻结契约）

`semantic.rs::SEMANTIC_TOOL_SPECS` 的顺序与名字与 `contract::SEMANTIC_TOOLS` 完全一致：
`bevy_player_transform, bevy_grounded, bevy_coin_counter, bevy_win_flag, bevy_inject_move,
bevy_inject_jump, bevy_wait_frames, bevy_health`。

- 每个只读工具**恰好一次 BRP 调用**（`each_read_is_one_call_and_never_a_batch`）：组件读走
  `world.query`，`data.components=[路径]`、`filter.with=[玩家标记]`、`strict:true`；资源读走
  `world.get_resources`。
- 注入走 `world.mutate_resources` 写 `InputIntent` 的**命名字段**：`move_dir` ← `dir`（`-1|0|1`），
  `jump_pressed` ← `press`；电平语义由游戏每帧自清（PRD §3-C3）。
- `bevy_wait_frames` / `bevy_health` 不产生 BRP 调用（SPIKE-1 §6.3：帧推进不是 BRP 动词；
  进程健康不在 ECS 里）。
- **缺失即契约违反，绝不静默为 0**：`project` 对空结果集、缺组件、`errors` 非空、
  字段类型不对分别给 `ContractViolation` / `Malformed`；`classify_brp_error` 把 `-23502` 之类
  映射为 `ContractViolation`。返回形状（`{x,y,frame}` / `{grounded,frame}` / `{coins,frame}` /
  `{won,frame}` / `{accepted}` / `{frame_after}` / `{alive,stderr_tail}`）逐条有测试。

### 5.3 服务层（薄，且只做四件事）

`server.rs::BevyMcpServer`：

- **白名单**：只有 31 个冻结名字可调用；其它一律 `unknown_tool`（别名如 `entity_query` 被拒——
  这正是「不做名字映射」的行为证据）。
- **先校验后发送**：`resolve()` 用生成的 schema 校验（必填、类型、`enum`、`const`、未知参数），
  失败即 `invalid_arguments` **且不触网**（`a_typo_in_a_parameter_is_refused_before_the_wire`
  断言假服务收到 0 个请求）。
- **绝不 batch**：语义读按 `plan()` 逐条 `call_document`（`a_batch_is_never_sent_even_for_a_multi_step_future`
  检查线上每个 body 都是对象）。
- **错误分类进门的词汇表**：`classify()` 产出 `kind ∈ {contract_violation, infrastructure_failure,
  transport, adapter_bug(-32601), brp_error, malformed_reply, unsupported, unknown_tool,
  invalid_arguments, no_game_process}`；`bevy_health` 在**没有注册进程**时是 `no_game_process`
  错误，绝不报 `alive:false` 当事实。
- **脱敏挂钩**：`trait Redactor` + `NoRedaction`（默认，逐字保留）+ `SecretRedaction`（调用既有
  `runtime::secrets::redact_secret_assignments`）；`redact_value` 递归作用在证据的字符串上。
- **帧等待可注入**：`trait FrameWaiter` + `WallClockWaiter{16 ms}`（SPIKE-2 headless 实测 60.3 FPS）；
  测试用记录型 waiter 断言「要了多少帧」，不花墙钟。
- **证据绑定**：`call_with_evidence` 每次调用产出一份 `CallEvidence`（seq 从 1 起、时间戳、
  layer、brp_methods、原始 request/response、result、error）。

### 5.4 冻结哈希与名字（钉在测试里）

- **`TOOL_LIST_SHA256 = e177325fe8b2036c355d37b9373b85b524f4a7f0d999e087711366bca661ae97`**
  （= `sha256(canonical_json(tools/list))`，`TOOL_COUNT = 31`）。
- 钉住它的测试：`adapter::mcp::tests::the_tool_list_hash_is_pinned_and_the_list_has_the_frozen_size`
  与集成测试 `the_tool_list_hash_and_the_eight_semantic_names_are_pinned`（后者把 8 个语义名字
  逐字列出）。另有 `generic_tool_names_are_the_verb_names_verbatim`、
  `the_verb_list_is_the_measured_23_in_order`、`the_eight_semantic_tools_are_the_frozen_names_in_order`、
  `every_semantic_tool_is_bound_to_a_contract_entry_or_explicitly_path_free`、
  `the_tool_list_is_the_frozen_surface`。

> **一句诚实的话**：「工具清单」在 MCP 的 `tools/list` 里是 `name + description + inputSchema`；
> 23 条通用工具的**返回**是 BRP 原样透传（由 BRP 自己的 schema 决定），8 条语义工具的**返回**形状
> 由 §5.2 的投影测试逐条钉住，而不是塞进 `tools/list`。若验收要求把返回形状也写进哈希，
> 那需要在 `tools/list` 里增加 `outputSchema` 并重钉哈希——这是**下一批的一个决定**，见 §9。

---

## 6. 任务五：证据布局 `runs/bevy-<round>/`

**交付**：`src/adapter/mcp/evidence.rs`（563 行）。`DESIGN-DETAIL.md` §6 的七项逐项落地：

```
runs/bevy-<round>/
  meta.json                 # round, exit_code, segments, contract_sha256, feature_sha256, lock_sha256
  build.log                 # 构建日志（逐字）
  launch.json               # headless 开关 / 端口 / 启动→就绪耗时
  calls/<seq:04>-<tool>.json# 每次 MCP→BRP 调用的原始请求/响应 + 序号 + 时间戳 + ok/error
  readings/<surface>.json   # 每条判据的读数
  gate.json                 # 门裁定与 reasons（缺省写 not-applicable/false）
  qa/                       # Tester 的报告与快照哈希（本批只建目录）
```

- `LAYOUT` 常量把七个名字冻结，测试 `the_layout_is_the_designs_six_names` 钉住它。
- `RoundHashes::measure(lockfile)` 现算三个哈希（契约、feature set、锁文件），
  `meta_json` 把三者与退出码、分量一起写进 `meta.json`。
- `CallEvidence` 每次调用一个文件：`rel_path()` = `calls/0001-<tool>.json`；工具名经
  `sanitize_tool_name`（保留 `. - _ +`，其余 `_`）**保证只是 `calls/` 下的一个文件名**。
- `round_name` 校验轮名（拒绝空、`.`、`..`、分隔符、空白等），`round_dir(root, round)` 是模块里
  **唯一**一处 `join("runs")`。
- `write_round(root, &RoundEvidence)` 把一轮全部写出，并返回轮目录。

**这一条最重要的性质（禁止区自检，不只是声明）**：

- `a_round_written_into_temporary_space_never_touches_the_repository_runs_directory`：写前写后
  **逐项对比仓库 `runs/` 的目录清单**（含大小），必须完全相同，且写出的目录必须落在传入的临时
  root 之下。
- `the_evidence_module_only_ever_writes_below_the_root_it_is_given`：对模块源码做自检——
  **生产代码**里 `join("runs")` 只能出现 1 次（就是 `round_dir`），且不得硬编码任何绝对路径。
- `a_round_name_cannot_escape_the_runs_directory`、`tool_names_are_sanitized_into_one_path_component`
  分别挡住「轮名逃逸」与「工具名逃逸」。
- 本批**没有**往仓库 `runs/**` 写任何东西（见 §9 的自检）。

---

## 7. 门禁数字（literal exit codes，无第二个测试进程）

所有测量都在**独立构建目录**里做：基线用 `F:\b1-scratch\target-base`，本批用
`F:\b1-scratch\target-b1`（SPIKE 的教训：共享 target 目录产生过旧二进制读数）。

| 项 | 基线（HEAD `d0a4805`，我自己复现） | 本批 |
|---|---|---|
| `cargo test --offline` **literal exit code** | **0** | **0** |
| passed / failed / ignored / listed | 653 / 0 / 7 / 660 | **751 / 0 / 8 / 759** |
| 其中 lib 单元测试 | 188 passed | **281 passed**（+93） |
| 集成测试套件数（`test result:` 行数） | 62 | 63（新增 `bevy_adapter_b1`） |
| 新增通过测试 | — | **+98**（93 lib + 5 集成） |
| 删除/削弱测试 | — | **0**（无删除、无跳过、无 `#[ignore]` 新增于既有测试） |
| 新增 `#[ignore]` | — | **+1，且是我故意标的**：`tests/bevy_adapter_b1.rs::the_pinned_endpoint_answers_discover_with_the_23_methods_of_bevy_0191`（真机 smoke，需 15702 上有真 Bevy，设计 §8-5 要求它存在但不得进默认门；本批**从未运行**它） |
| `cargo fmt --all --check` exit code | **0** | **0** |
| 强制重建 | — | 先 `git ls-files '*.rs'` 得 **101** 个文件；用 Python 先打印再逐条 remove-tree 掉 `target-b1\debug\.fingerprint` 下的 `hof-rs-*`（第一次 4 个、第二次 64 个）；再**逐个** touch 这 101 个 `.rs`；然后重跑全量门禁 → exit **0**，751/0/8/759 |

补充事实（可复核）：

- 基线日志 `F:\b1-scratch\out\baseline.log`（`CARGO_TEST_EXIT=0`），本批日志
  `F:\b1-scratch\out\final-gate2.log`（`CARGO_TEST_EXIT=0`）；计数由
  `F:\b1-scratch\py\sum_tests.py` 从日志逐行求和得出。
- 门禁在**同一个修订**上跑了两次（第二次是加入那个 `#[ignore]` 真机 smoke 之后）：
  第一次 `out\final-gate.log` = **751 / 0 / 7 / 758**、exit 0；第二次（发布的数）`out\final-gate2.log`
  = **751 / 0 / 8 / 759**、exit 0。两次都在强制重建之后。
- 中途的绿对照：`out\plant-control.log`（281 lib + 5 集成，exit 0）。

---

## 8. 受控植物（5 个，每个「绿—红—恢复后绿」+ 逐字节还原）

恢复纪律：每个植物前先把目标文件快照进 `F:\b1-scratch\backup\b1`（`snap.py` 记 sha256、
`setstamp.py` 显式设 mtime、`verify.py` 断言工作副本等于备份）；植物用编辑工具施加；恢复用
`restore.py`（逐文件 copyfile + 重新 setstamp + **打印并断言 sha256 等于清单**）；恢复后再跑一次
绿对照。所有删除都用 `py/rmtree.py`（先打印、且必须严格位于 `F:\b1-scratch` 之内）、
`force_rebuild.py`（同上约束），**全程没有 `rm -rf`，没有 `git checkout --`**。

| # | 文件 | 植物内容 | 变红的测试（字面 exit 101） | 恢复后 sha256（等于快照） |
|---|---|---|---|---|
| P1 | `src/adapter/bevy/contract.rs` | `Grounded` → `GroundedOnFloor`（类型路径漂移） | `adapter::bevy::contract::tests::the_contract_hash_is_the_pinned_literal` | `bbac5b3b405cfeb9…` |
| P2 | `src/adapter/mcp/generic.rs` | 把工具名 `world.query` 改成 `entity_query`（旧 Godot 风格改名） | `adapter::mcp::tests::the_tool_list_hash_is_pinned_and_the_list_has_the_frozen_size` **且** `adapter::mcp::generic::tests::generic_tool_names_are_the_verb_names_verbatim` | `26fe9714b2408fd6…` |
| P3 | `src/adapter/bevy/brp.rs` | 删掉 `read_document` 里对 HTTP 200 body 内 `error` 的检查 | `adapter::bevy::brp::tests::an_error_body_under_http_200_is_a_tool_error` | `5f5c34a49475a967…` |
| P4 | `src/adapter/mcp/evidence.rs` | 去掉轮名校验（轮名直接进路径） | `adapter::mcp::evidence::tests::a_round_name_cannot_escape_the_runs_directory` | `6f21477d07b6b3c3…` |
| P5 | `src/adapter/godot.rs` | `read()` 改成返回 `Reading::observed(kind, 0, {"coins":0})`（把未观测说成观测） | 集成 `the_legacy_godot_adapter_implements_the_capability_surface_without_panicking` | `0ffc52dd73c19cf0…` |

**P2 附带一条真发现**：`the_verb_list_is_the_measured_23_in_order` 在改名后**仍然是绿的**，因为它
比对的是 BRP 的 `method` 字段（契约的动词），而不是 MCP 的 `name`。也就是说「动词清单」与
「工具名清单」是两条不同的钉子，前者管协议覆盖面，后者（工具清单哈希 + name==method 断言）管
**改名**——这正是设计要求把工具清单逐字冻结的意义。P4 第一次施加时留下了语法错误（编译红），
我重做成「能编译但行为错」的植物，因为编译失败不算「自己的测试变红」。

---

## 9. 禁止区自检 / Forbidden-zone self-check

- **`git status --porcelain`**：在父代理提交 `f100e2f` 之后、本报告修订之前是
  ```
  ?? l.json
  ?? p2.json
  ?? pv.json
  ?? r.json
  ```
  本报告随后被修订（数字与提交状态），因此**现在**还会多一行
  ` M .spec/bevy/BATCH-B1-REPORT.md`（就是本文件）。
  那 4 个未追踪 JSON 在**我开工前就已存在**（SPIKE-1 §C.0 记录了同样四个），不是我产生的，
  我也没有删改它们。
- **提交状态**：父代理在本批执行期间把全部改动提交为 **`f100e2f`**
  （`feat(bevy): add the engine-neutral adapter trait, the frozen reflectable contract, the remote
  protocol client and the two-layer tool surface`，13 files changed, 5857 insertions(+), 2
  deletions(-)）。**我本人没有执行 `git commit`，也从未执行 `git push`**（闸门已武装，本批未推送）。
  本报告在该提交之后又做了一次数字/状态修订，因此报告文件本身目前是一个**新的未提交改动**，
  请父代理随 D297 一起追加提交（或 amend）。
- **未改动**：`DECISIONS.md`、`.spec/bevy/PRD.md`、`.spec/bevy/REQUIREMENTS.md`、
  `.spec/bevy/DESIGN-OVERVIEW.md`、`.spec/bevy/DESIGN-DETAIL.md`、`.spec/bevy/SPIKE-*.md`、
  `godot-mcp/**`、引擎树、`Cargo.toml`、`Cargo.lock`、`runtime/**`、`.spec/hof-rs/**`。可复核：
  `git diff --stat -- Cargo.toml Cargo.lock DECISIONS.md godot-mcp .spec/bevy/PRD.md
  .spec/bevy/REQUIREMENTS.md .spec/bevy/DESIGN-OVERVIEW.md .spec/bevy/DESIGN-DETAIL.md
  .spec/bevy/SPIKE-1-REPORT.md .spec/bevy/SPIKE-2-REPORT.md` 在提交后为空。
- **`runs/**` 零写入（有 mtime 证据）**：`runs/` 下共 7341 个文件，**最新的一个**是
  `runs\smoke-t16\evidence\round\evidence_refresh.txt`（2026-10-03T05:47:27），而本批结束时刻是
  2026-10-04T01:47 —— **全部早于本批开工**。证据布局只通过「调用方传入 root」的 `write_round`
  落盘，测试只写 `tempfile` 临时目录，并用目录清单前后比对断言仓库 `runs/` 未变。
- **未用 `rm -rf`**、**未用 `git checkout --`**；所有删除都经 Python remove-tree 且先打印路径、
  再校验路径严格位于 `F:\b1-scratch`。
- **时间戳纪律**：每个被植物/恢复的文件都在恢复后显式 `os.utime` 设成
  `2026-10-04T00:00:00Z` 并断言 sha256 等于快照；两个备份集
  （`backup/b1` 5 个文件、`backup/base` 2 个文件）与 `verify.py` 都可复核。
- **不引依赖**：本批**零新增依赖**。用到的都是仓库已有的 `serde_json`、`sha2`（经
  `runtime::policy::sha256_hex`）、`ureq 2.12`（`default-features = false`，纯回环明文）、
  `thiserror`、`tempfile`（dev）。假 BRP 服务用 `std::net` + 手写 HTTP/1.1，因此**没有引入任何
  HTTP server 依赖**。
- **无引擎、无游戏、无网络（产品口径）**：默认门内**没有任何真实网络或引擎**；唯一的 socket 是
  进程内假服务绑 `127.0.0.1:0`。唯一会真的连 15702 的测试是那个 `#[ignore]` 的真机 smoke。
- **无 panic 自检**：`F:\b1-scratch\py\panic_probe.py` 逐个新模块切出 `#[cfg(test)]` 之前的
  生产段，检查 `unwrap()/expect/panic!/todo!/unimplemented!/[0]` —— 新代码 0 命中（见 §1）。

---

## 10. 本批**故意留给下一批**的东西

1. **`BevyAdapter` 本身**（`adapter/bevy/mod.rs` 的 `GameAdapter` 实现）：本批只建了 `bevy/` 树；
   `DESIGN-OVERVIEW` 把 `mod.rs` 定位为 `BevyAdapter`，本批它只有模块声明。
2. **`build.rs` 的可执行部分**：本批只冻结了**契约数据**（`FROZEN_FEATURES`/`BEVY_VERSION`/
   四个预算常量/`feature_set_sha256`/`lockfile_sha256`/`lockfile_matches`/`BuildBudget`），
   **没有**跑 cargo、没有测量冷/暖增量、没有实现预算恢复与轮 0 预热（`FEATURE_SET_SHA256 =
   d6a90ba39e67b9e05fd28d97cc570dc989a03e8ec7a15ba93d077d5fe95d1f96` 已钉）。
3. **`launch.rs`**：headless 运行时开关、同一二进制的 C1/C3 分支、把 `BevyMcpServer` 接到真进程、
   进程句柄喂给 `bevy_health`、15702 就绪等待的端到端验证——都没有做（设计 §5 的端点规则与
   SPIKE-2 的 C6 形态留待使用）。
4. **电池与五条观测（E3）**：`readings/*.json` 的内容生产、`gate.json` 由真门填充、
   `qa/` 的 Tester 内容、`calls/` 由真游戏产生——本批只保证了**布局与哈希**。
5. **真机 smoke 的执行**：那个 `#[ignore]` 测试本批**从未跑过**（没有真引擎在跑），下一批必须在
   有 15702 的环境里 `--ignored` 跑一次并记录结果。
6. **三个待决策项（属于父代理/设计回合，不是实现）**：
   (a) `hof_game` 这个 crate 名与 `hof_game::contract` 模块名是否被 PRD/模板采纳（不采纳就改契约
   并重钉 `CONTRACT_SHA256`）；
   (b) `frame` 字段的语义——本批实现为**适配器的观测序号**（BRP 无帧动词、`Time` 不可反射，
   SPIKE-1 §0.4-3），若判据需要**真实游戏帧**，PRD 必须新增一个可反射的帧计数器资源（= 契约变更，
   第 7 个语义面）；
   (c) 是否把 8 条语义工具的**返回形状**也写进 `tools/list`（`outputSchema`）并入哈希。
7. **`DECISIONS.md` D297 条目**：按约束我**不得**改 `DECISIONS.md`，所以本批的决策（trait 形态、
   Godot 对齐方式、契约冻结值、`hof_game` 冻结、frame 语义、args 空则无 params）需要父代理补记。
8. **`PRD.sha256` 入证据**：设计 §6 的 `meta.json` 只列 contract/feature/lock 三个哈希，
   所以本批 `RoundHashes` 只有三个。是否把 PRD 冻结哈希也纳入是决定项。

---

## 11. 残余风险：**实测**与**推断**分开

**实测（本批有证据）**

- BRP 客户端的五类失败路径与就绪轮询，全部在进程内假服务上跑通（§4 表）。
- 契约/feature/工具清单三个哈希以及它们在内容变化时移动（P1/P2 植物实测）。
- Godot 侧：既有 660 个测试（653 passed / 7 ignored）一个不改地全绿；diff 只有 +116/−2（两行
  import + 一个 impl 块）。
- 门禁数字与 `cargo fmt --all --check`、强制重建后的复跑（§7），literal exit code 均为 0。
- 一个环境事实：`ureq 2.12` 的 `ErrorKind` 无 Timeout；对本机一个已关闭回环端口的 connect
  实测耗时 **2.04 s** 且 kind 为 `ConnectionFailed`（因此超时分类不能只看耗时）。

**推断（本批没有测量，必须在后续批次里证伪）**

1. 契约里的**游戏侧类型路径**（`hof_game::contract::{Player,Grounded,CoinCounter,WinFlag,InputIntent}`）
   是**刻意冻结的设计选择**，不是测量：现在还没有游戏。
2. 8 条语义工具的返回形状（例如 `world.query` 结果是数组、`world.get_resources` 返回 `{value:…}`）
   来自 SPIKE-1/SPIKE-2 的活体证据，本批**没有**再连真引擎复核一次。
3. 「args 为空 ⇒ 不发 params」这条规则来自对 `bevy_remote` 源码 `Option<Params>` 的阅读，
   本批用假服务验证了**发出/不发出**的行为，但没有在真 BRP 上验证 `world.list_components` 的
   两种行为差异。
4. `frame` = 适配器观测序号（见 §10-6b）；`bevy_wait_frames` 的 16 ms/帧来自 SPIKE-2 的
   headless 60.3 FPS 读数，不是本批实测。
5. `-32601 = 适配器 bug` 与 `CONTRACT_VIOLATION_CODES` 的取值来自 SPIKE-1 的错误码表
   （源码 + 活体负例），本批未重新实测。
6. 真机 smoke 测试**未运行**，因此它能否在真 Bevy 0.19.1 上通过仍是未知（它的期望值
   `methodCount=23 / version=0.19.1 / servers[0]=15702` 来自 SPIKE-1 §4.1）。
7. 「无第二测试进程」这一条我只能声明：门禁运行时我没有启动任何其它 cargo/测试进程，
   构建都用独立的 `CARGO_TARGET_DIR`（`target-base` 与 `target-b1`）。

---

## 12. 变更清单（供父代理提交与复核）

这些变更已在 **`f100e2f`** 中（父代理提交）；下表 sha256 是提交后、本报告修订时的字节
（`F:\b1-scratch\py\file_table.py` 可重算）。

新增（10 个文件）：

| 路径 | 行数 | sha256 |
|---|---|---|
| `src/adapter/bevy/mod.rs` | 12 | `806fefc60a83336cb05b8fc4795f745621350663ba5a2e073276cfac03083592` |
| `src/adapter/bevy/brp.rs` | 789 | `5f5c34a49475a9671ce26c1bc5fdf14244edcdc5306122b30fecda220923a50a` |
| `src/adapter/bevy/build.rs` | 177 | `945bd39f5961b74af09612a36b8bca6bc67c75e90c82cdc57e3278df957402b8` |
| `src/adapter/bevy/contract.rs` | 402 | `bbac5b3b405cfeb913c44cc139a05b6da3a2f4a54664d67c77ea64f8f07171ce` |
| `src/adapter/mcp/mod.rs` | 440 | `279d9c12b8d64d94d2b676c2af59bb69534ff2ae385afd3a73c8d237de08b74d` |
| `src/adapter/mcp/generic.rs` | 659 | `26fe9714b2408fd6f958365c63e391d9466894662b3ec12a50976d0e79263da0` |
| `src/adapter/mcp/semantic.rs` | 642 | `efd63ed1d8634f95e5825fb28406135c6aa20de6687179dd15fa8fc369e5cc86` |
| `src/adapter/mcp/server.rs` | 805 | `2998b00bfcc7d89da2eb043b71b4a50bae0166cc7b036a7b1e9cf973c399b49b` |
| `src/adapter/mcp/evidence.rs` | 563 | `6f21477d07b6b3c3a4726caf8dee5af9bd88644a99f1d4328e4b1c11df64b211` |
| `tests/bevy_adapter_b1.rs` | 248 | `d62773596922099e960c64b17c0bbcd74587d13a17ad80f546aa9856186ee5b7` |

修改（2 个文件）：

| 路径 | diff | 现在 sha256 |
|---|---|---|
| `src/adapter/mod.rs` | `+514 / −0`（两行模块声明 + `GameAdapter` 段） | `40a1d573d952298f7873710d2a6d854812d5dd30fba958e8885657ed964ced09` |
| `src/adapter/godot.rs` | `+116 / −2`（两行 `use` + 一个 `impl GameAdapter`） | `0ffc52dd73c19cf0c45e62ce414a91c799c4bd242820bc34a8f25c1c19f9b50e` |

回滚方式：整批改动已在 `f100e2f`，所以回滚是 `git revert f100e2f`（或 `git reset --hard d0a4805`
若允许丢历史）—— 回到 `d0a4805` 的状态；Godot 路径与既有 660 个测试不受影响。
