# DECISIONS — hof-rs

> 「代码为什么长这样」的权威来源。每个决策点追加一条：日期 / 触发问题 / 考虑的选项 / 最终选择 / 理由 / 预期影响与回滚点。
> 提交信息应对应本文件的决策编号（如 `feat(runtime): ... (D7)`）。

---

## D1 — 用 Cargo path 依赖复用 mini，不改其源码

- 日期：2026-09（阶段一需求分析期间）
- 触发问题：HoH 的 agent 核心如何接入 `F:\RustProjects\mini-swe-agent-rust-mini\rust`？
- 选项：
  1. **Cargo path 依赖 + 直接用 library API**（选中）
  2. 子进程调用 `mini` 二进制（CLI 协议）
  3. 把 mini 源码 vendor 进本仓库
- 选择：选项 1。
- 理由：mini 暴露了 `Model`/`Environment`/`DefaultAgent`/`AgentConfig`/`config` 全部所需边界，且
  `AgentConfig` 支持自定义 `system_template` + `instance_template`（minijinja），足以装配角色化 prompt；
  `tests/core.rs` 已有 `MockModel`/`MockEnvironment` 范式可直接复用做离线确定性测试。子进程方案会让
  「角色权限」「冻结候选」的执行证据难以精确绑定（无法拿到每轮 messages/usage），调试成本也高。
  vendor 会失去「harness 未被修改」这一论文关键性质与上游可同步性。
- 影响与回滚点：`Cargo.toml` 单一 `path = "F:/RustProjects/mini-swe-agent-rust-mini/rust"` 依赖行；
  若上游 API 变动导致集成失败，回退到选项 2（子进程），Runtime 的角色/冻结/schema 逻辑不受影响。

## D2 — 不新增 mini 侧 patch：token 用量从轨迹中提取

- 日期：2026-09
- 触发问题：用户问「token 消耗值修复过一次，判断是否完善，未完善可安排修复」。
- 核查事实：
  - `llm_connector.rs:214-229` 把完整 `ChatResponse` 写入 `Message.extra["response"]`；
  - `llm-connector 1.4.0` `Usage{prompt_tokens, completion_tokens, total_tokens,
    prompt_cache_hit_tokens, prompt_cache_miss_tokens}` 派生 `Serialize/Deserialize`；
  - `calculate_cost()` 在未配置 `input_cost_per_million`/`output_cost_per_million` 时返回 `0.0`
    （本地 qwen 无单价 → cost 恒 0）；
  - `GlobalModelStats` 只累计 cost，无 token 字段；`ModelConfig` 无默认单价表。
- 选择：**不修改 mini**。HoH 侧自建 usage 汇总器，从 agent messages 的
  `extra.response.usage`（含 format-error 路径写入的 `response`）按角色/轮次累计 tokens。
- 理由：论文主张 HoH 不修改底层 harness；token 数据事实上已无损持久化，改 mini 属于不必要的侵入。
- 未完善之处（已知限制，记录在案）：
  1. provider 不返回 `usage` 时无从补救 → HoH 必须显式标 `unknown`，禁止填 0 冒充；
  2. `global_model_stats` 无 token 维度（HoH 不依赖它）；
  3. cost 对本地模型无意义，HoH 一律以 token 为口径。
- 回滚点：若某 provider 只在响应头/流式增量里给 usage，届时再评估是否向 mini 提极小增补（需用户批准）。

## D3 — Godot 通过 Godot MCP Pro 的 HTTP JSON-RPC 触达

- 日期：2026-09
- 触发问题：Developer/QA 如何操作 Godot（论文用 Godot MCP + 资产/UI/测试技能）？
- 核查事实：`godot-mcp-pro` 是注入编辑器的 GDExtension，内置 HTTP 服务器
  `POST http://127.0.0.1:9877/mcp`（JSON-RPC 2.0，175 工具），另有 stdio↔TCP 的 `mcp_bridge`（端口 9876）。
  「Testing & QA」「Runtime」「Input」「Editor」四类工具恰好提供 HoH 需要的黑盒证据：
  `simulate_sequence`、`capture_frames`、`get_game_screenshot`、`assert_node_state`、
  `run_test_scenario`、`start/stop/replay_recording`、`get_editor_errors`、`get_output_log`。
- 选择：以 HTTP JSON-RPC 为工具通道；HoH 侧提供瘦 CLI 封装（一个命令 = 一次工具调用），
  供 mini 的 agent 通过 shell 动作调用；工具清单按角色裁剪（R13）。
- 理由：零中介、无需 Node 运行时、协议标准；与 mini「动作=shell 命令」的模型天然契合；
  Runtime 可在工具层做角色权限强制（QA 禁写工具）。
- 影响与回滚点：真实运行依赖「Godot 编辑器打开 + 插件启用 + 9877 监听」这一外部前置条件；
  若不稳定，回退到 `mcp_bridge` stdio，或直连 GDExtension TCP 9876。工具封装层是唯一改动面。

## D4 — 仓库边界：HoH 代码单仓 + 产物不进 git + 论文只留 OCR 文本

- 日期：2026-09
- 触发问题：什么进版本控制？（用户已确认「HoH 代码单独建仓，Godot workspace 不进 git」）
- 选择：
  1. `F:\moonbit-hof-rs` 作为 HoH 代码仓（`git init`，按阶段 commit，提交信息带决策编号）；
  2. `.workspace/`（Godot 工程）与 `runs/`（运行记录、快照、轨迹）**gitignore**；
  3. 被开发产物的版本化由 HoH 自己实现（R10），不依赖 git；
  4. 16MB 原版 PDF 不入库，只提交 OCR 文本 `2609.01481v1.pdf_by_PaddleOCR-VL-1.6.md` 作为权威参考。
- 理由：代码与产物分离，避免「产物污染代码历史」；论文 PDF 是二进制外部出版物，文本足够支撑设计与追溯。
- 回滚点：若后续需要把产物版本与代码版本关联，可在 `runs/<id>/meta.json` 记录 HoH 的 commit hash（单向引用，不反向入库）。

## D5 — tool-calls 模式（实测确认）

- 日期：2026-09
- 触发问题：本地 `qwen/qwen3.8-27b` 是否支持 OpenAI tool calls？（决定 Developer 走 tool-calls 还是 text-based）
- 核查事实：对 LM Studio `127.0.0.1:1234/v1/chat/completions` 发携带 `bash` 工具定义的请求，得到
  `finish_reason=tool_calls`、`tool_calls[0].function.name="bash"`、`arguments={"command":"ls -la"}`；
  `usage={prompt:327, completion:60, total:387}` 且含 `completion_tokens_details.reasoning_tokens=30`；单次约 2s。
- 选择：**tool-calls 模式**（mini 的 `ApiMode::ToolCalls`，即 `LlmConnectorModel` 默认路径）。
- 理由：原生工具调用比正则解析更稳；qwen3.8 是推理模型，`reasoning_tokens` 会推高 completion 成本，
  统计时必须按 `completion_tokens` 全额计（不得只算可见输出）。
- 回滚点：若某轮发现 tool call 解析频繁失败（`max_consecutive_format_errors` 触发），切
  `mini_textbased.yaml` + `action_regex`，无需改动 Runtime。

## D6 — 上线模型标识用「自剥前缀」写法锁定为 `qwen/qwen3.8-27b`（用户指出 + 实测确认）

- 日期：2026-09
- 触发问题：用户指出「不要让 `effective_model_name` 剥掉 `qwen/` 前缀成 `qwen3.8-27b`，LM Studio 会重新启动模型，多占用显存」。
- 实测证据（`GET /api/v0/models` 前后对比，请求 `/v1/chat/completions`）：

  | 上线 model 字段 | 响应 `model` | 加载状态 |
  |---|---|---|
  | `qwen/qwen3.8-27b` | `qwen/qwen3.8-27b` | 1 个已加载实例 |
  | `qwen3.8-27b`（剥后裸 id） | `qwen3.8-27b` | **新增第二条 `state=loaded`** → 显存翻倍且常驻 |
  | `Qwen/qwen3.8-27b` | 归一化为 `qwen/qwen3.8-27b` | 未新增 |

- 选项：
  1. **`model_name: openai/qwen/qwen3.8-27b` + 显式 `provider: openai_compatible`**（选中）
     —— mini 剥掉 `openai/` 后上线恰好是规范 id；
  2. 大小写变体 `Qwen/...`（依赖 LM Studio 归一化，语义晦涩）；
  3. 让用户在 LM Studio 把模型 id 改成裸 id（把架构约束转嫁给外部配置，脆弱）；
  4. 给 mini 加 `wire_model_name` 配置项（需改 harness，D2 反对）。
- 选择：选项 1。
- 理由：零改动 mini、上线字符串精确等于规范 id、不触发二次加载；`provider` 显式指定同时绕开
  `infer_provider("qwen/...") → aliyun` 的误判（若不显式指定，请求会走 DashScope 语义打不到 LM Studio）。
- 影响与回滚点：`config/hoh.yaml` 的 `model_name` 与 `provider` 成为**不可随意改动**的两个字段（C9/C10）；
  必须有离线测试断言「解析后送往线路的 model 字符串 == `qwen/qwen3.8-27b`」。
  若上游 mini 改了前缀剥离表，该写法会失效 → 届时回退到选项 2 或选项 4。
- 附带事项：本次实验在用户机器上留下了一个多余的常驻实例 `qwen3.8-27b`（`state=loaded`），
  建议在 LM Studio 中手动卸载该条目以释放显存。

## D7 — v1 接受 MCP 作用域限制，用「同一候选两种访问路径 + 双哈希断言」缓解

- 日期：2026-09（阶段三详细设计）
- 触发问题：MCP 只能操作「编辑器当前打开的工程」（= 真实 workspace），无法直接作用于 Tester 的 `A_t` 副本。
  论文要求 QA 在**冻结只读候选**上取证，两者存在张力。
- 选项：
  1. **v1 接受限制 + 双哈希断言**（选中）：副本负责「读输入、写证据」，编辑器工程负责「执行与截图」；
     QA 前断言 `hash_tree(workspace) == A_t.candidate_id`，QA 前后对**副本与真实 workspace 同时**做哈希断言；
     限制显式写入 `meta.json.warnings` 与验收报告。
  2. v1 即为 QA 起第二个 Godot 编辑器实例（打开 candidate 副本，`godot_mcp/port=9878`）→ 冻结语义端到端成立，
     代价是多一个实例的启动时间与内存。
  3. 只在文档里留接口位，真实运行后再定。
- 选择：选项 1（用户确认）。选项 2 列为 v1.1 首选项。
- 理由：v1 的验收对象是「Runtime 语义正确」，选项 1 已把「Tester 不能改动被评估对象」变成**可检测的强制断言**，
  且不引入跨进程端口编排的复杂度；同时把「限制」而非「假设」写进产物，符合本项目「不静默降级」的纪律。
- 实现要点（已写入 DESIGN-DETAIL §4.4/§4.5/§6.1/§9.2/§11）：
  ① 新增 `ContractViolation::WorkspaceDriftBeforeQa`；② Tester 阶段的 workspace 哈希断言为强制项；
  ③ R4 的测试必须包含「Tester 用绝对路径直写真实 workspace」这条反例。

## D8 — 阶段四单实现子代理顺序完成（不并行拆流）

- 日期：2026-09
- 触发问题：详细设计 §10.1 提出 WS-A/WS-B 可并行（WS-A 先交接口冻结提交），用户选择如何派发。
- 选择：**单个实现子代理顺序完成全部**（用户确认）。不并行拆流。
- 理由：本项目的模块共享同一个状态机（视图/权限/schema/证据/记录/主循环），接口漂移是首要风险；
  单一责任主体 + 详细设计作为唯一契约，比两个子代理抢接口更可靠。
- 风险与回滚点：单次实现周期长，若中途上下文耗尽或阻塞，则**另派全新子代理**，以
  `DESIGN-DETAIL.md` + git 历史 + `DECISIONS.md` 为恢复依据继续（不得让同一子代理带着未验证结论续写）。

## D9 — 实现期对详细设计「未定之处」的就近裁决（接口零偏离）

- 日期：2026-09（阶段四编码实现）
- 触发问题：DESIGN-DETAIL 有几处契约与实现细节之间存在空隙（§0 授权实现者就近推导并回报）。逐条裁决如下，
  **未改变任何 §2/§3/§4/§5/§6 的 pub 签名**。
- 裁决：
  1. **悬空证据（DanglingEvidence）归属**：`validate_evidence(b, candidate_id)` 没有视图根参数，无法判存在性；
     按 §2.1 表格语义与 §4.6 职责划分，**文件存在性检查落在 `EvidenceBinder::bind`**（含“绝对路径不被解析”
     这条反例），`validate_evidence` 只做纯不变式。新增 `validate_evidence_shape(&Value)` 承担 `MissingField`
     （否则缺 `planner_handoff` 只能报 Json），它仍是纯函数、签名未动。
  2. **status 与所属列表不一致**：§2.1 表格要求 err 但未指定 `IssueCode`。为不新增 enum 变体（保持 §2 冻结），
     复用 `IssueCode::Json` 并给出明确 message。测试 `evidence_rejects_status_mismatch` 锁定该行为。
  3. **`VersionStore::snapshot` 无 role 参数**：§4.7 签名保持不变，另加 `snapshot_role(..., role, note)`；
     主循环用后者写 `role="init"` / `role="developer"`，`snapshot` 委托之（role 为空），两条路径共用同一哈希。
  4. **Tester 视图注入项**：§4.3 表格未列 `evidence_playbook()` 的落点，按 §6.1「注入 Tester 的采集指引」，
     落为 `.hoh/EVIDENCE_PLAYBOOK.md`（附加输入，不改任何既有输入）。
  5. **`.hoh/evidence.json` 占位**：Tester 视图写入**零字节**占位文件。理由：既满足 §4.3「注入空 evidence.json」，
     又保证「Tester 未产出」时 gate 仍按失败计（Json issue，消息含期望路径），不会与「合法空证据」混淆。
  6. **工具策略单一真源**：§5.4 要求表在 `src/tools/policy.rs`，§4.4 要求 `runtime/policy.rs` 暴露
     `tool_allowed`/`PLANNER_DENY_PREFIXES`。为避免两套表漂移，**规范表实现在 `runtime::policy::tool_matrix`**，
     `tools::policy` 仅 re-export + 提供 `denial_payload`（CLI 结构化拒绝体）。
- 影响与回滚点：以上均为附加函数或既有签名的实现选择，回滚只需删除附加函数；测试
  （`evidence_binding.rs` / `tools_policy.rs` / `snapshot_rollback.rs`）是这些裁决的可执行依据。

## D10 — 离线锁定上线 model id 用 std::net 假 HTTP 服务；MCP 作用域限制的落地方式

- 日期：2026-09（阶段四编码实现）
- 触发问题：§3.2 要求「用假 HTTP 服务断言上线 model 字段 == `qwen/qwen3.8-27b`」，首选 `ureq`；`ureq` 是
  HTTP **客户端**，无法作服务端，且标准的 `std::net::TcpListener` 无依赖、永远可用（§3.2 已允许该回退）。
- 选择：`tests/mini_wire_model.rs` 用 `std::net::TcpListener` 手写最小 HTTP/1.1 服务（读取 header +
  Content-Length body，回固定 chat completion，body 经 mpsc 回传），真实跑一次
  `DefaultAgent::run`，断言服务端收到的 `model` 字段与两条 messages 内容。回退方案已获 §3.2 许可。
- 附带：同一测试断言 `system_template`/`instance_template` 的变量值语义（收到的是正文本身，不是模板源），
  这是 §4.2 陷阱 1 的可执行证据。
- MCP 作用域（D7）的实际落地：`GodotAdapter::doctor` 只返回**客观可判定项**（project.godot、addon 目录），
  「编辑器当前打开的工程 == 真实 workspace」这一不可自动判定的事实作为 `meta.json.warnings` +
  `warnings.log` 的固定条目（`run_loop::MCP_SCOPE_WARNING`）写入每次 run，并在 `hoh doctor` 报告之外由
  文档与回报显式声明；不把它伪装成「已解决」。
- 回滚点：若日后要求端到端严格冻结，按 D7 选项 2 起第二个编辑器实例（9878）打开 candidate 副本，届时只需替换
  `GodotAdapter` 的通道端点，Runtime 契约不变。

## D11 — 阶段五第一次独立验收 verdict=fail，进入修复轮（不自行修复）

- 日期：2026-09（阶段五）
- 触发问题：独立验收子代理（工作流 `hof-rs-acceptance`）自跑全部命令并构造文档外反例后，判 `fail`。
- 验收事实（由验收方独立复现，非实现者自报）：
  - **通过**：R1–R13 与 C9/C10 全部成立（82 passed / 0 failed / 7 ignored；clippy `-D warnings` 在
    `cargo clean -p hof-rs` 后 exit 0 且 0 warning；fmt --check exit 0）；两个外部仓库与 `.spec`
    相对冻结提交零改动；工作树干净、未新增提交。
  - **不通过**：`A1`(blocker) 证据路径 `../` 逃逸未被强制；`A2`(major) `godot_smoke.rs` E2–E6 为
    「零断言 + 绿色」伪测试；`A3`–`A5`(minor) 拒绝文案/doctor 人工确认项缺失/CLI 出口与 unknown 展示；
    `A6`(nit) 一处恒真断言。另 9 条风险，其中「确定性阶段自伤」与「R11 残留暴露面」需设计层裁决。
  - **不可验证**：E1–E6 全部（9877 实测 Connection refused）。
- 选择：**不自行修复**（遵守角色边界），把缺陷整理为决策后回到阶段四，派发**又一批全新**实现子代理；
  随后再派**又一批全新**验收子代理复验。设计层问题按阶段关卡显式回到阶段三修正工件（见 D12）。
- 理由：验收方与实现方独立是本项目的核心价值；blocker 必须由新的实现主体修复并由新的验收主体复验，
  否则「独立」沦为空话。
- 回滚点：若修复轮引入新的 blocker，回滚到 `45b5ff4`（全部 R1–R13 通过的那个状态）重新规划修复。

## D12 — 详细设计升版 v0.2：验收驱动的设计修订（DR-1..DR-13）

- 日期：2026-09（阶段三回炉）
- 触发问题：验收暴露的两条风险触到设计层，不能在实现层偷偷打补丁。
- 选项：
  1. **回阶段三显式修订 DESIGN-DETAIL（选中）**，把修订写成规范性 DR 条目，再交实现者落地；
  2. 只在修复任务书里口头要求，`DESIGN-DETAIL.md` 不动；
  3. 先照旧实现，等真实运行暴露问题再说。
- 选择：选项 1。已在 `DESIGN-DETAIL.md` 追加 §12（DR-1..DR-13）并同步改写 §4.4 执行顺序，版本升 v0.2。
- 关键设计修订：
  - **DR-1（设计性）**：确定性构建/执行阶段**提前到 A_t 冻结之前**，且 `build_check` 的入参由
    `candidate_view` 改为**真实 workspace**。理由：MCP 只能作用于编辑器当前打开的工程（= workspace，D7），
    让确定性阶段也作用于 workspace 可**根除**「工具自身改写工程 → QA 前 `WorkspaceDriftBeforeQa` 误报」
    这一整类问题，并让确定性记录与候选身份天然一致；构建/执行属「产出候选」而非「评估候选」，语义更准。
    QA 前的漂移断言保留为安全网。
  - **DR-3（硬性补强 R11）**：新增 `runtime.private_excludes`，只影响视图构建、不扩大 `hash_tree` 排除集
    （避免削弱 R2/R3 的越权检测）。
  - **DR-4**：`GodotAdapter::initialize` 幂等写入 `project.godot` 的 `[editor_plugins] enabled`，把
    「手工启用插件」从用户前置条件中移除，使 A₀ 打开即可用 MCP。
  - **DR-10**：拒绝 `..` 逃逸 + canonicalize 前缀断言（blocker A1 的根因修复）。
  - **DR-9**：`godot_smoke` 前置缺失必须失败；**DR-11**：`cache_excludes` 防误用约束。
- 影响与回滚点：`ProjectAdapter::build_check` 签名变更（唯一接口变更），`run_loop` 顺序变更；
  回滚只需还原 §4.4 顺序与签名（本轮无生产运行，回滚无损）。

## D13 — 修复轮完成（DR-1..DR-11 落地），进入第二轮独立验收

- 日期：2026-09（阶段四修复轮 → 阶段五复验）
- 触发问题：D11 判 fail 后派发**全新**实现子代理执行修复（工作流 `hof-rs-fix-round`）。
- 修复轮结果（已由我方只读核查确认）：
  - 离线套件 **100 passed / 0 failed / 7 ignored**（基线 82，新增 18 条）；`clippy --all-targets -- -D warnings`
    与 `fmt --check` 均 exit 0。
  - **DR-9 生效证据**：`cargo test --test godot_smoke -- --ignored` 现在 **0 passed / 7 failed**（此前是
    「5 passed 且零断言」的伪测试），panic 文本含缺失路径与 `HOH_SMOKE=1` 提示。
  - **A1 blocker 已修**：`check_paths` 三道闸（绝对路径 / `ParentDir` 组件 / canonicalize 前缀断言），
    新增 `evidence_binding.rs::rejects_parent_dir_traversal` 与 `tools_policy` 的 submit 逃逸用例。
  - **DR-1 已落地**：顺序改为 `Developer → Deterministic(workspace) → Freeze A_t → candidate 副本 → Tester`；
    `build_check(&self, workspace, tools)` 签名变更；新增用例证明「确定性阶段改动被计入 candidate_id 而非触发漂移」。
  - **DR-4 已落地**：`.workspace/mario/project.godot` 现含
    `[editor_plugins] enabled=PackedStringArray("res://addons/godot_mcp_rs/plugin.gd")` 同义条目
    （实测第 37/39 行），「手工启用插件」不再是用户前置步骤。
  - 4 次提交（`971882b` / `74b2d67` / `1033aaf` / `a351817`）；工作树干净；`.spec` 相对 v0.2 冻结零改动；
    两个外部仓库零改动。
- 两处既有断言的调整（属 DR-1/DR-7 的语义变更，非放宽）：
  1. `rejects_workspace_drift` 的注入点从「确定性阶段」后移到「冻结之后」（`evidence_playbook` 钩子），
     原注入点在新语义下是合法改动；反例本身保留；
  2. `default_deny_unknown` 的期望文案改为 DR-7 规定的 `Tool not in this role's allowlist.`。
- 选择：**进入第二轮独立验收**，派发又一批全新验收子代理（不得复用第一次验收者的结论），
  重点复验 A1/A2 是否真修、DR-1 是否引入新回归、以及是否有新的逃逸路径。
- 回滚点：若第二轮验收仍 fail 且属 blocker，回滚到 `9f3598e`（v0.2 设计冻结点）或 `45b5ff4`（R1–R13 全通过点）重新规划。
- 遗留（属 DR-13，需真实运行定论，不阻塞离线验收）：E1–E6、编辑器副产物对候选身份的影响、
  真实 27B 的 schema 遵从率、副本耗时与快照体积。

## D14 — 第二轮独立验收 pass（离线范围），阶段一整体仍以「真实冒烟」为闸

- 日期：2026-09（阶段五复验）
- 触发问题：D13 后派发**又一批全新**验收子代理复验（工作流 `hof-rs-acceptance-2`）。
- 结果：**verdict = pass**，零缺陷。验收方自建反例（不复用第一次验收的任何结论）：
  - A1/DR-10：构造 **18 种逃逸形态**（`..\` 反斜杠、`C:foo` 驱动相对、UNC、设备路径、**`mklink /J` junction**、
    symlink、`cand` vs `cand2` 前缀相似目录等）全部被拒为 `DanglingEvidence`；阳性对照被接受；
  - A2/DR-9：`cargo test --test godot_smoke -- --ignored` → **0 passed / 7 failed**（exit 101），
    设 `HOH_SMOKE=1` 亦 panic 并打印缺失路径；
  - DR-1：读码确认顺序与 `build_check(workspace)` 签名，并判定**未削弱** R2/R3/R4（Planner 断言在确定性阶段之前、
    Developer 的 NoProgress 判定在其之前、Tester 的双哈希在其之后；确定性阶段由 Runtime/adapter 触发，角色无法注入写）；
  - 4 项既有断言调整全部判为可接受（其中 2 项为收紧）。
  - 套件 **100 passed / 0 failed / 7 ignored**；clippy（clean 后重建）与 fmt 均 exit 0；工作树与 `.spec`、两个外部仓库零改动。
- 关键发现：仓库遗留一个**不完整的 `runs/godot-smoke/`**（planner 轨迹以 `LimitsExceeded` 收尾、123 条消息；
  developer 无 exit 条目；缺 `evidence.json`/`result.json`/`candidate`），说明曾有一次真实冒烟在 Developer 阶段中断。
  该遗留目录会使 `e1` 的 `assert!(!run_dir.exists())` 直接失败，真实冒烟前必须清理。
- 选择：**离线范围接受 pass；但阶段一整体不判完成**。依据 `REQUIREMENTS.md` §1（用户确认的附加要求：
  阶段一必须含至少一次 T=1 真实 smoke run），E1–E6 未执行即阶段一未完成。
- 理由：不把「离线测试全绿」冒充为「系统真能跑」；这正是本项目「沉默即失败、不静默降级」纪律的体现。
- 回滚点：真实冒烟若暴露设计问题，按阶段关卡回到阶段三修订 `DESIGN-DETAIL`（升 v0.3）后再修实现。
- 下一步（阻塞于外部前置条件）：用户打开 Godot 编辑器于 `.workspace/mario`（插件现已自动启用）、
  LM Studio 保持 `qwen/qwen3.8-27b` 在线（并卸载实验期残留的裸实例）；我方清理遗留 run 后派发 T=1 真实冒烟。
  > **已被 D15 取代**：模型改为远端 `deepseek-v4.1-flash`。

## D15 — 真实冒烟改用远端 `deepseek-v4.1-flash`（取代本地 qwen）

- 日期：2026-09（阶段五真实冒烟前置期）
- 触发问题：用户取消本地 LM Studio 冒烟，给出远端 OpenAI 兼容端点与凭据，要求用它测试。
- 实测（决策者亲自探测，未经任何子代理转述）：
  - `GET /v1/models` 返回 `deepseek-v4.1-flash`（单模型）；
  - `POST /v1/chat/completions` 携带 `bash` 工具定义 → `finish_reason=tool_calls`，
    参数 `{"command": "ls -la"}` 正确；`usage = {prompt:292, completion:52, total:344}` 且含
    `completion_tokens_details.reasoning_tokens=12`；单次约 **0.9s**（本地 27B 约 2s）。
  - 端点需 `Authorization: Bearer <key>`（与本地 LM Studio 不同——旧 `chat_probe` 不带鉴权头，必须修）。
- 选项：
  1. **以配置方式切换到远端模型，并把「模型身份」从硬编码泛化为配置驱动**（选中）；
  2. 保持本地 qwen 不变，拒绝切换（用户已明确要求切换）；
  3. 改代码硬编码新模型名（换模型就要改码，违反 C12 精神，否决）。
- 选择：选项 1。同步在 REQUIREMENTS 把 C9 泛化为「配置声明 `wire_model_name` + 离线/在线双重锁定」，
  新增 C11（密钥不得入库）与 C12（换模型不得要求改码）。
- 密钥处理：`config/hoh.yaml` 的 `api_key` 必须为空；密钥经环境变量 `HOH_MODEL_API_KEY`（其次 `OPENAI_API_KEY`）
  注入；`.gitignore` 覆盖 `.env` / `*.env` / `config/*.secret*`；`meta.json`、轨迹、日志、doctor 输出禁止出现明文。
  **本决策日志与本仓库任何文件均不得写入该密钥。**
- 影响与回滚点：`src/config.rs`（身份断言泛化）、`src/cli_impl.rs`（chat 探测带鉴权、LM Studio 专有检查条件化）、
  `src/errors.rs`（错误文案去具体模型名）、`config/hoh.yaml`、`tests/mini_wire_model.rs` 与 `src/cli.rs` 相关测试。
  回滚：把 `model` 段换回 D6 的 qwen 配置即可（`wire_model_name: qwen/qwen3.8-27b`），代码无需再改——这正是 C12 的价值。

## D16 — 详细设计升版 v0.3（DR-14..DR-16，模型无关化）

- 日期：2026-09（阶段三回炉，第二次）
- 触发问题：D15 的模型切换暴露了「设计把具体模型名写进了规范性要求」这一缺陷。
- 选择：回阶段三显式修订，追加 §12 的 DR-14..DR-16 并改写 §3.1 的 model 段，版本升 v0.3（用户已知悉并同意继续）。
- 修订要点：
  - **DR-14**：新增必填配置 `model.wire_model_name`；删除代码中的模型常量；身份断言只校验通用不变式
    （provider 显式、两个名字非空、api_key 必须为空）；离线测试改为**从配置读** `wire_model_name`（换模型自动跟随）。
  - **DR-15**：doctor 的 `model.chat` 必须带鉴权头；`model.resident` 是 LM Studio 专有检查，必须条件化，
    不适用时报 `skipped`（`ok=true`）而**不得**阻断 run（C12）。
  - **DR-16**：密钥卫生——配置留空、环境注入、落盘 redaction、并有测试断言仓库/产物中无 `sk-` 明文。
- 理由：把「某个具体模型」从规范里彻底移除，才能让「换模型」回到配置层；这正是 D15 选项目标的制度化。
- 回滚点：`DESIGN-DETAIL.md` 回退到 `4dd1bd9` 版本即可（代码回退到 `4dd1bd9` 或 `a351817`）。

## D17 — 第一次真实 T=1 冒烟：negative baseline（阶段一仍未完成）

- 日期：2026-09（阶段五真实冒烟）
- 触发问题：在 Godot 编辑器在线、远端 `deepseek-v4.1-flash` 在线、`hoh doctor` 8/8 全绿的前提下，
  派发全新子代理执行真实 T=1 冒烟（工作流 `hof-rs-real-smoke-t1`）。
- 实测事实（子代理逐条取证，已由我方复核关键结论）：
  - 真实跑了 **22.8 分钟**，`exit 3`（schema 重试耗尽）。
  - Planner ✅ 一次通过 schema，产出 2.4KB 合法 `D_1`；Developer 冻结出 `A_1`（`candidate_id=18b39995…`）。
  - **QA 三次尝试全部失败**（attempt1/2 证据为空文件、attempt3 产物缺失）→ **`E_1` 不存在**。
  - **5/5 次角色调用全部 `LimitsExceeded`**（`step_limit=60`），submission 全为空——没有任何角色正常收尾。
  - **A_0→A_1 净增量为零**：唯一新脚本 `scripts/player.gd` 为 **0 字节**；按住 `move_right` 120 帧
    玩家 `position` 恒为 `(0,0)`；截图 320×180 整幅纯灰；`Goal` 为 `shape_count=0` 的 Area2D；HUD 无 Label。
  - Runtime 确定性阶段 **2/2 记录失败**：`get_editor_errors` → `-32603 无法打开日志文件`；
    `get_game_scene_tree` → `等待游戏响应超时 (5秒)`。
  - **E5 ✅ met**（独立复核：快照 27 文件与 workspace 逐个 SHA256 全等、QA 窗口内零写入、无契约违约）。
  - 用量合计 **8.50M tokens**（planner 0.44M / developer 1.59M / tester 6.47M），cost=0（端点无单价，符合 C8）。
  - **C11 违规（安全）**：`HOH_MODEL_API_KEY` 经**父进程环境继承**进入角色子 shell，Tester 执行 `cmd /c set HOH`
    使密钥明文落入 `tester.attempt1.json` 与 `tester.attempt3.json`，并回灌进模型上下文（已发往远端端点）。
    决策者已就地擦除这 2 个文件（复扫 0 命中），并确认全树仅此 2 处。
- 结论：**阶段一未完成**；本轮只能作为「链路可用性 + 证据可信度」的负面基准。E1/E3 not_met，E4/E6 not_reached。
- 选择：把缺陷整理为 DR-17..DR-23（设计 v0.4，D18），派**全新**实现子代理执行修复包，随后**又一批全新**验收子代理复核。

## D18 — 详细设计升版 v0.4（DR-17..DR-23，修复包）

- 日期：2026-09（阶段三回炉，第三次）
- 触发问题：D17 的真实冒烟暴露 7 类问题（结构性冲突、安全、健壮性、起点污染、记录不对称、产出定义缺失）。
- 用户已确认的取舍：
  1. **证据采集归属**：改为「**Runtime/adapter 拥有证据采集，Tester 只做判定**」（DR-17）——这是论文的原始分工，
     并直接消除「60 步被采集吃掉」的结构性冲突；
  2. **修复范围**：**完整修复包**（DR-17..DR-23）；
  3. **Developer 产出为零**：同时强化 prompt/skills 与明确「完成的定义」（DR-23）。
- 修订要点：DR-17 确定性证据电池（含 `supports` 需求映射与失败如实记录）、DR-18 步数预算（150/25）与
  「先收口」纪律 + 每轮每角色至多一次 wrap-up retry、DR-19 密钥不得进子进程环境 + 运行后扫描擦除、
  DR-20 MCP 就绪等待/重试/错误原文、DR-21 `--fresh-workspace`/`--reset-workspace` 与 `start_state` 记录、
  DR-22 traj/log 逐次尝试对称 + usage 明细、DR-23 developer 完成定义与 godot skills 配方。
- 回滚点：`DESIGN-DETAIL.md` 回退到 `7846b54`；代码回退到 `77e2e7e`。

## D19 — 已接受风险：当前模型密钥不轮换（用户判定）

- 日期：2026-09
- 触发问题：D17 发现密钥经子进程环境进入轨迹与模型上下文，决策者建议轮换。
- 用户判定：**该密钥是局域网本地服务的凭据，目前看没有泄漏，继续测试、不轮换**。
- 记录为**已接受风险**（由用户承担），但同时保留 DR-19 的实现要求：
  密钥不得进入角色子进程环境、运行后必须扫描擦除——因为「密钥进入模型上下文」本身违反 C11 纪律，
  且该通道在下一次换用真实云端凭据时会立刻成为真实风险。
- 回滚点：任何时候用户决定轮换，只需更新 gitignore 覆盖的 `config/model.secret.env` 即可，无需改码。

## D20 — 修复包 v0.4 的实现期裁决（DR-17..DR-23）

- 日期：2026-09（阶段四实现）
- 触发问题：DR-17..DR-23 在下发到实现时仍有若干「设计未细分」的取舍点，需在不动设计决策的前提下定案。
- 考虑的选项与最终选择：
  1. **`usage.json` 结构**：保留裸数组 vs 改为 `{schema, summary, attempts}`。
     **选择后者**（DR-22 明确要求「增加 attempts 并保留原有汇总字段」）；代价是 1 条既有断言
     （`runtime_semantics.rs::records_all_artifacts`）必须从「数组长度 3」改为「summary 长度 3 + attempts 非空」，
     并让 `hoh status` 同时兼容两种形态（旧 run 的产物仍可读）。已在回报 regressions 中逐条登记。
  2. **`mcp-errors.jsonl` 的写入范围**：仅电池调用 vs 所有 `hoh tools call`。
     **选择电池（runtime 拥有的确定性阶段）**。理由：角色自身发起的调用会把失败写入角色视图的 `.hoh`，
     而 Tester 阶段的视图是冻结候选副本——让工具桥在那里写文件会把「被评估对象」变成「可写对象」，
     违反 R4；冒烟暴露的三类失败（编辑器日志 `-32603`、就绪超时、截图 `-32603`）全部发生在确定性阶段，
     电池覆盖即是根因覆盖。记为**范围解释**，非偏离。
  3. **`--args-file` 的绝对化**：`canonicalize` vs 手工绝对化。
     **选择手工绝对化**（`current_dir().join(path)`）：文件不存在时 `canonicalize` 必然失败，
     而 DR-20 恰恰要求「不存在时错误信息含期望的绝对路径」。
  4. **traj 的字段承载方式**：把 `exit_status/duration_ms/usage/artifact_path` 提升到 traj 顶层 vs 放入 `hoh` 子块。
     **选择 `hoh` 子块**：mini 的轨迹格式（`info`/`messages`/`trajectory_format`）不得被改写，
     顶层新增键会被未知字段策略吞掉或与之冲突的风险最小；日志侧则为平铺字段。两者信息等价且一一对应。
  5. **Developer 的 wrap-up retry 触发条件**：DR-18 的「产物缺失/不合法」对 Developer 无定义。
     **选择以 `LimitsExceeded` 为触发**（其产物即工程本身）；与 Planner/Tester 一样每轮至多一次。
  6. **`--fresh-workspace` 对不存在路径的处理**：自动创建 vs 报错。
     **选择报错**（DR-21 明示「实现前必须断言该路径存在且是目录」），避免把「拼错路径」变成「静默创建」。
- 新增依赖：无（复用已有 `thiserror`/`tokio`/`serde_json`）。
- 预期影响：7 条 DR 全部落地，离线测试 122 → 160 条；真实 T=1 冒烟尚未重跑（见回报 open_items）。
- 回滚点：本次实现对应提交 `9876574`、`0060147`、`fb3a06f`、`4b3f0f6`、`d87a852`；
  `DECISIONS.md` 回退到 `2a64277`。

## D21 — 第二轮真实 T=1 冒烟（smoke-t2）：E1/E4/E5/E6 met，E2/E3 not_met

- 日期：2026-09（阶段五真实冒烟，第二轮）
- 触发问题：D18 修复包（DR-17..DR-23）落地后，派全新子代理重跑真实 T=1（工作流 `hof-rs-real-smoke-t2`）。
- 实测事实（72.5 分钟；子代理逐条取证）：
  - **全循环跑通**：Planner 一次通过 schema（`D_1` 3179 B）；Developer 产出**真实增量**
    （A0 27 文件 → A1 48 文件；`player.gd` **0 B → 2076 B**；7 个新 GDScript；`main.tscn` 342 → 7369 B）；
    证据电池 **7/7 步产出**；QA 产出合法 `E_1`（24981 B，19 条 gap、**0 条 verified**、`qa_status=fail`）并通过 `hoh submit`。
  - `result.json`: `ok=true`、`candidate_id == version_id == 40fb64…`。
  - **E1 met**（保留：三角色均**非干净收尾**——planner/developer ×2 为 `LimitsExceeded`、tester 为 `RepeatedFormatError`；
    循环完成是因为产物合法，不是因为角色正常结束）。
  - **E2 not_met**：`scenes/main.tscn` **没有根节点**（首个节点声明即 `parent="."`）→
    `Invalid scene: root node Ground cannot specify a parent node` + `Failed loading scene`；
    `play_scene` 谎报 `playing:true`。
  - **E3 not_met**：`monitor_properties` 全部 `-32603`（游戏未运行）→ **0 个位置采样**；**0 张截图**；
    Player/Goal `shape_count=0`；HUD 可见文本节点 0。
  - **E4 met（空洞地）**：`verified_records` 为空，故无「verified 指向不可复现记录」的可能；19 条 gap 的
    `execution_records` 均为候选根下的**相对路径**且盖章 `candidate_id`。
  - **E5 met**：三方哈希逐字节一致（workspace == A1 快照 == 候选视图，均 `26eae9eb…`），QA 未改 A_1。
  - **E6 met**：`qa_report.md` 以 `## Verdict: **fail**` 开头，明确「candidate is not launchable」，
    gap 均带 `player_impact` 与 `recommended_update`。
  - **DR 效果**：DR-17 yes / DR-18 partial（150 步**仍然** LimitsExceeded，但角色已能留下合法产物；
    wrap-up retry 确实触发）/ **DR-19 yes（密钥零泄漏：4 个密钥变量在角色环境全为空串，257 文件扫描 0 命中，
    Developer 实际执行了 `set | findstr /i hoh` 也没拿到值）** / DR-20 partial（重试与就绪等待生效、
    `mcp-errors.jsonl` 77 条原文；但相对路径 `--args-file` 仍报 `os error 3`）/ DR-21 yes（`as_is` 如实记录）/
    DR-22 yes（traj 与 logs 逐尝试 4↔4 对称，usage 有 attempts 明细）/ DR-23 partial（脚本非空、磁盘 `.tscn`
    含 Label 与 CollisionShape2D，但因场景非法而 0/7 可观察）。
  - 用量：**11.27M tokens**（developer attempt1 单次 16.06M prompt tokens、56.5 分钟）——预算被大量重复读文件吃掉。
- 新发现的缺陷（全部记入 DR-24..DR-28）：
  F-2 场景无根节点（根因：Developer 用旁路 Python 脚本 `gen_scene.py` 生成 `.tscn`，与编辑器实时场景分歧）；
  F-5 `HOH_ARTIFACT_DIR` 传**相对路径** → `hoh submit` 写到嵌套假路径；
  F-6 Developer 2/3 预算用于阅读 HoH 自身与 godot-mcp-pro 源码（工具 schema 不可发现）；
  F-7 A_1 混入 `_probe.gd`/`_t.txt`/`tmp_args.json` 等垃圾并被计入候选身份；
  F-8 Developer 在**仓库根**建 `.hoh_live_args/`（越界、哈希不可见，已由决策者清理）；
  F-1 `Start-Process -PassThru` + 重定向下 `$p.ExitCode` 返回 `$null`（环境怪癖，退出码只能推导）；
  另有「编辑器内存场景与磁盘 `.tscn` 不一致」的实测证据。
- 选择：**判定 E2/E3 未通过 → 阶段一仍未完成**；把缺陷整理为 DR-24..DR-28（设计 v0.5，D22），
  派全新实现子代理修复，再派又一批全新验收子代理。
- 本轮的一处显式偏离（决策者裁决）：DR-21 要求真实冒烟用 `--fresh-workspace`，
  但**清空 `.workspace/mario` 会删除正在被编辑器加载的插件 DLL**（可能搞崩编辑器与 MCP），
  故本轮改用 `as_is` 并在 `meta.json.start_state` 如实记录。**干净 A₀ 冒烟留到编辑器可安全关闭时执行。**

## D22 — 详细设计升版 v0.5（DR-24..DR-28，第二轮修复包）

- 日期：2026-09（阶段三回炉，第四次）
- 触发问题：D21 暴露「跑通但做不出可启动的东西」——缺一道**被检查的**可启动闸门，以及工具可发现性、
  路径与卫生三类工程缺陷。
- 修订要点：
  - **DR-24（最高优先级）**：冻结前 `launchable` 闸门（`editor_errors_baseline.ok && play_scene_ready.ok`）；
    不通过则**不冻结**，用电池失败原文对 Developer 发起**一次**定向修复（`agent.repair_steps=60`）；
    电池在取编辑器错误前必须 `reload_project` + `open_scene(main)`；adapter 提供**场景结构校验**
    （恰好一个无 `parent` 的根节点）并给出可执行提示。
  - **DR-25**：角色环境全部路径型变量改**绝对路径**；`hoh submit` 只许写规范产物路径（否则 exit 2）；
    `--args-file` 相对路径以 `HOH_ARTIFACT_DIR` 为基准；新增**越界写检测** `out_of_tree_writes`。
  - **DR-26**：`TOOLS.md` 由真实 `tools/list` schema 生成（含参数名/类型）；新增 `PROJECT_MAP.md`；
    `godot-dev.md` 必须含**已知良好的最小平台游戏骨架**（含唯一根节点、碰撞体、Label）；
    prompt 禁止读取 harness 与外部仓库源码；一次成功 `submit` 即结束。
  - **DR-27**：`result.json.artifact_gate` + 退出码 **6**（循环完成但产物不可启动）+ `status` 双列 +
    写 `runs/<id>/exit_code` 文件。
  - **DR-28**：产物卫生——临时文件只许写 `HOH_SCRATCH_DIR`（`.hoh` 下，不参与哈希）；
    `result.json.artifact_hygiene.suspicious_files` 留痕不自动删除。
- 回滚点：`DESIGN-DETAIL.md` 回退到 `2a64277`；代码回退到 `11ef9b6`。

## D23 — 修复包 v0.5 的实现期裁决（DR-24..DR-28）

- 日期：2026-09（阶段四，修复包 v0.5 实现）
- 触发问题：DR-24..DR-28 已冻结，但若干处「设计未细分」的实现取舍会改变既有契约，
  必须显式记录而不是悄悄选一个。

### 裁决 1：`ArtifactGate.applicable` 第三态（DR-24/DR-27）
- 问题：`launchable := editor_errors_baseline.ok && play_scene_ready.ok` 对**没有这两个步骤**的适配器
  （`TestAdapter`/`FakeAdapter`，其电池由 trait 默认实现派生）意味着 `launchable=false`，
  会触发一次定向修复调用，进而打断既有 60+ 个离线场景（FakeHarness 脚本耗尽而 panic）。
- 选择：`ArtifactGate` 增加 `applicable` 字段。电池未声明两个门步骤时
  `{applicable:false, launchable:true, reasons:["gate_not_applicable: ..."]}`，既不触发修复也不返回 6；
  只有 Godot 电池（声明了两个步骤）才是真门。
- 理由：**「没检查」不允许伪装成「通过」**——用显式第三态表示，而不是把缺失当失败或当成功。
- 影响：`hoh run` 对 `--adapter test` 永远返回 0；`result.json.artifact_gate.applicable=false` 可审计。

### 裁决 2：`hoh submit` 的路径语义（DR-25）
- 问题：DR-25 要求「相对 `--file` 以 `HOH_ARTIFACT_DIR` 为基准」且「写入前断言目标绝对路径逐字
  等于规范产物路径」。字面最严读法（任何 `--file` 必须等于 `<view>/.hoh/<name>`）会让既有
  `submit_validates_and_writes_the_canonical_artifact`（用 `tests/fixtures/plan_ok.md` 作为只读来源、
  期望写入规范路径、exit 0）失效。
- 选择：
  1. 写入目标恒为规范路径 `<artifact_dir>/plan.md|evidence.json`；
  2. `HOH_ARTIFACT_DIR` 必须是绝对路径，否则 `exit 2` 并报 expected/actual（这正是 smoke-t2 的嵌套 bug）；
  3. 相对 `--file` 先按 `HOH_ARTIFACT_DIR` 解析，解析结果**必须逐字等于**规范路径，否则 `exit 2`
     并报 expected/actual（`--file other.md` 被拒）；
  4. 绝对 `--file` 保留既有「读取来源 → 校验 → 写规范路径」语义（测试与人工工具依赖它）。
- 配套：三个 prompt 与 skills 里的提交命令由 `--file .hoh/plan.md` 改为 `--file plan.md`
  （相对基准是 `HOH_ARTIFACT_DIR` 本身）。
- 理由：真正的生产故障模式是「相对 artifact dir + 相对文件名」的笛卡尔积；绝对来源是人工/测试通道，
  与角色运行时的失败模式无关。把两者区分开，既关掉 bug 又不误伤既有契约。

### 裁决 3：电池以 `Role::Developer` 调用工具（DR-24）
- 问题：新增的 `reload_project` 属于 `MUTATING_EXACT`，`open_scene` 也不在 Tester 允许名单里；
  而电池此前用 `Role::Tester` 调用。
- 选择：`BatterySession` 的 `call`/`ready` 改用 `Role::Developer`（唯一写者角色，全量工具）。
- 理由：电池是 **runtime 的确定性阶段**（DR-1），不是 Tester；它必须能强制编辑器反映磁盘真值。
  Tester 的写工具禁令（R13）不变。
- 回滚点：若未来给电池单独的角色策略，只需改 `BatterySession::call`。

### 裁决 4：`scene_structure` 步骤位置（DR-24）
- 选择：顺序为 `project_reload_and_open` → `scene_structure` → `editor_errors_baseline` → `play_scene_ready`
  → …（共 9 步）。门定义仍严格等于 `editor_errors_baseline.ok && play_scene_ready.ok`。
- 理由：`scene_structure` 的可执行提示是定向修复的第一手材料，越早产出越好；把它纳入门会偏离冻结定义。

### 裁决 5：越界写扫描用元数据而非内容哈希（DR-25）
- 选择：`(len, mtime_nanos)` + `WalkDir::filter_entry` 跳过 `.git/.workspace/runs/target/node_modules/.hoh*`
  与 `--project` 子树；上限 50，相对扫描根、排序、只报不删。
- 新增配置键 `runtime.out_of_tree_root`（serde default 为 `None` → 进程 cwd），使离线测试可指向临时目录。
- 理由：扫描发生在每次角色调用后，内容哈希代价不必要；`(len, mtime)` 足以回答「新增/修改」。

### 裁决 6：两遍电池的落盘（DR-24）
- 选择：第 2 遍电池**重建** `.hoh/deterministic`（不留第 1 遍的原始 payload 冒充最终证据）；
  两遍的 `ok` 摘要都写入 `result.json.battery_passes`（pass/launchable/steps）。

### 裁决 7：既有测试的必要调整（DR-24 引入的新步骤）
- `tests/evidence_battery.rs`：
  - 步骤顺序断言由 7 步改为 9 步（新增前两步）——**必须改**，因为电池步骤顺序是 DR-24 的规范行为；
  - `FixtureChannel` 增加 `reload_project`/`open_scene`/`get_scene_file_content` 三个答复——**必须改**，
    否则夹具对未知工具 panic；
  - `editor_error_failure_is_recorded_verbatim` 与 `readiness_timeout_fails_the_step_and_is_journalled`
    改用 `repairing_script()`（多一个 Developer 步骤）——**必须改**，因为这两例门为 false，
    DR-24 必然发起一次定向修复。
- 其余 160 条断言未改。

### 裁决 8：DR-27 退出码 6 的离线可测边界
- 事实：`hoh run` 的 doctor 预检需要模型端点与 MCP（离线必失败 → exit 4），因此**无法**在离线套件里
  端到端跑出 6。
- 选择：把退出码派生与落盘抽成纯函数 `run_exit_code(&ArtifactGate)` 与
  `finalize_run(run_dir, &RunSummary)`，并另加一个真实 `run_loop` 回合（GodotAdapter + 全失败工具通道）
  证明 `summary.artifact_gate.launchable=false` 且 `run_exit_code → 6`。
- 遗留：真实 CLI 路径（doctor 通过 → 6）留待真实冒烟验证，记入 known_risks。
- **该遗留已由 D24 关闭**：`smoke-t3` 真实 CLI 路径实测 `exit_code=6`，且与 `meta.json.exit_code`、
  `hoh status` 的 `gate=fail` 三方一致。

## D24 — 第三轮真实 T=1 冒烟（smoke-t3）：exit 6；MCP 响应错位导致闸门假阴性

- 日期：2026-09（阶段五真实冒烟，第三轮）
- 触发问题：v0.5 修复包（DR-24..DR-28）落地后，派全新子代理重跑真实 T=1（工作流 `hof-rs-real-smoke-t3`），
  起点 `as_is`（已知 `main.tscn` 无根节点，专门用来验证可启动闸门与定向修复）。
- 实测事实（48.3 分钟，**exit 6**；退出码取自 `runs/smoke-t3/exit_code` 并与 `meta.json.exit_code`、
  `hoh status` 的 `harness=ok gate=fail` 三方交叉核对一致——DR-27 生效）：
  - **实际缺陷被真的修好了**：冻结场景含 **50 条 `[node]` 行、恰好一个根节点**
    `[node name="Main" type="Node2D"]`（第 41 行，无 `parent=`）、0 条缺 `parent` 的非根、0 条悬空 parent、
    7 个 `res://` 引用全部存在。
  - **DR-24 机制按设计工作**：电池顺序正确（`project_reload_and_open` → `scene_structure` → `editor_errors_baseline`
    → `play_scene_ready` → …）；闸门判 `false` → **恰好一次** Developer 定向修复
    （`repair_retry_used=true`、`battery_passes=2`、限额 60、`retry_context` 含逐字失败原文）→ 第二次仍 `false`
    → **诚实冻结**并写 `artifact_gate.launchable=false` + 原文。
  - **但闸门是假阴性，根因是环境缺陷**：9877 上的 MCP 服务**永远慢一拍且回带上一会话陈旧 id**。
    决策者用原始 HTTP 客户端复核（发 id=1 → 收 resp.id=704；发 id=2 → 收 id=1 的响应；
    发 id=3 → 收 id=2 的响应即 `{"count":0,"errors":[]}`）。因此 `get_scene_file_content` 收到 `open_scene` 的回复、
    `get_editor_errors` 收到场景文本，电池全部 payload 被错标。
    代价：那次「定向修复」在追不存在的缺陷，白烧 **13.4 分钟 / 4.35M tokens**，且承诺的可执行提示无法产出。
  - **E5 ✅**：版本快照、冻结候选、真实 workspace 三方 26 个文件逐字节相同（树哈希 `bbcebb91…`）。
  - **E6 ✅**（`qa_status=fail` 诚实收口）；**E1 ✅**；**E2 未能判定**（被错位污染）；
    **E3 not_met 但结论不可信**——补偿错位后 `Player.position` 在 `move_right`/`jump` 下 60 帧恒为
    `(60.0, 283.999)`、velocity 恒 `(0,0)`，而 `Enemy1` 在巡逻（`735.50→733.16`, vx=-70）、HUD 在倒数（120→87）；
    但若 `simulate_action` 自身响应错位，就无法区分「输入没送达」与「控制器没读输入」。
  - 密钥扫描：373 文件 **0 命中**（DR-19 持续有效）。
  - 新发现缺陷：①`developer` **attempt1 的 7,134,952 tokens / 799.8s 被覆盖**（汇总 25,839,490，真实 32,974,442）；
    ②`input_replay` 在 `0 frame(s), position unknown` 时仍 `ok=true`；③`screenshot` 在 PNG 不存在时仍写 `path`；
    ④`play_scene_ready` 接受了 `play_scene` 自己的回复；⑤`harness_source_read` **无条件误报**
    （它把系统提示里的禁止路径清单本身当证据）；⑥`os error 3` 仍出现 4 次。
- 选择：**判定阶段一仍未完成**（E2 无法判定、E3 不可信）；把缺陷整理为 DR-29..DR-33（设计 v0.6，D25），
  派全新实现子代理修复，再派又一批全新验收子代理 + 第四轮冒烟。
- 关键判断：**错位响应绝不能被「补偿后就当正常」**——它必须先被**检测**（`resp.id != req.id`）并**修复**，
  修不好就如实报错。这正是 DR-29 的规范。

## D25 — 详细设计升版 v0.6（DR-29..DR-33）

- 日期：2026-09（阶段三回炉，第五次）
- 触发问题：D24 暴露「环境缺陷 + 客户端不设防」共同制造假阴性，并连带污染结论、浪费预算。
- 修订要点：
  - **DR-29（最高优先级）**：`McpClient` 必须按 `id` 关联响应；错位时不得使用 payload，改为按 `resp.id`
    存入短生命周期待取响应表 + 只读探针（上限 `tools.max_sync_retries=4`）取回本请求响应；
    超限返回 `HofError::McpResponseDesync`；raw payload 头记录 `request_id/response_id/sync_probes`；
    会话起始做同步探针并在错位时留痕 `mcp_desync_detected`。
  - **DR-30**：电池步骤必须校验 payload 形状（就绪须由场景树确认、`editor_errors` 须有 `errors` 数组、
    `input_replay` 须有 ≥1 帧位置样本、`screenshot` 须 PNG 真实存在、`scene_tree` 须含路径与类型）。
  - **DR-31**：逐次尝试 usage/duration 立即入列，`summary` 必须逐字等于 `Σ attempts`。
  - **DR-32**：`harness_source_read` 只扫工具命令与参数，不扫 prompt。
  - **DR-33**：输入证据可判定化——记录动作可用性（InputMap 绑定）+ `(action, before, after, velocity)` 四元组，
    区分 `ACTION_NOT_BOUND` / `INPUT_HAD_NO_EFFECT` / 成功三态。
- 回滚点：`DESIGN-DETAIL.md` 回退到 `b83245a`；代码回退到 `f373dba`。

## D26 — 修复包 v0.6（DR-29..DR-34）的实现期裁决

- 日期：2026-09（阶段四，修复包 v0.6 实现）
- 触发问题：DR-29..DR-34 已冻结，但「错位修复的具体机制」「形状校验之外的第三态」「base64 落盘」
  等实现取舍会改变既有契约或往代码里引入新依赖，必须显式记录。
- 提交对应：`509fbfc`(DR-34) / `f3bb83d`(DR-32) / `1f36d1e`(DR-31) / `7e85f7b`(DR-30,DR-33) / `c1d94e6`(DR-29)。

### 裁决 1：错位修复的机制（DR-29）
- 选择：`McpClient::rpc` 对**所有** JSON-RPC 请求（含 `tools/list`）统一做 id 关联：
  1. `resp.id == req.id` → 使用其 `result`（若是 `error` 仍按业务错误返回）；
  2. 不等 → 把该响应按其自身 id 存入 `pending`（`Arc<Mutex<BTreeMap<u64,Value>>`，容量 32，超出丢最旧），
     **绝不读取其 payload**；随后每轮：先查 `pending` 里是否有本请求的 id，再发**一个**只读探针
     （`tools/call get_project_info`，id 自增），本轮响应同样按上述规则处理；
  3. 探针数达到 `tools.max_sync_retries`（默认 4）仍无匹配 → `HofError::McpResponseDesync{expected_id,got_ids,sync_probes}`。
- 迭代而非递归：整段是一个 `loop`，每轮最多一个探针，无栈增长。
- 「探针自身也走同一套校验」的落实：探针的响应若不带**本请求**的 id，也不得被当作结果使用（只会被入表）。
- 退出码：`McpResponseDesync` 归入 `External`（4）——错位的端点是「外部依赖不可用」，不是 harness 缺陷。
- 严格性取舍：响应**没有 id** 视为错位（而不是宽容地当作匹配），因为无法归属的 payload 正是本缺陷的根源；
  代价是「不返回 id 的非合规服务器」会得到 4 而不是静默成功，记入 known_risks。
- 回滚点：`McpClient::rpc`/`matched`/`stash`/`claim` 四个函数。

### 裁决 2：会话同步探针的介质与偏移语义（DR-29）
- 选择：`BatterySession::run` 的**第一步**调用 `ToolChannel::session_sync_probe()`（默认实现返回
  `available:false`，由 `McpChannel` 覆盖为两次连续 `get_project_info`）；报告落
  `<workspace>/.hoh/deterministic/mcp-sync.json`，`run_loop` 在每次电池 pass 之后读它，
  错位时把 `mcp_desync_detected: id_offset=<n> probes=<n> (...)` 追加进 `result.json.warnings`。
- 理由：`result.json` 由 run_loop 写、探针由 adapter 执行，两者之间已有的通道就是 `.hoh/deterministic/**`
  下的文件（`battery.json`/`mcp-errors.jsonl` 同例）；不引入新的 trait 返回值改造。
- 偏移语义：取**首个**观测到的 `resp.id - req.id`。注意它不一定是 `smoke-t3` 的 `+703`：
  `run_loop` 在电池之前会调 `index_markdown`（一次 `tools/list`），它可能已经消耗掉那条陈旧响应，
  此时探针看到的是普通的「慢一拍」`-1`。报告同时给出 `probes`，测试按实际值断言。
- 每次电池 pass 会重建 `.hoh/deterministic`，所以第 2 遍（定向修复后）的探针结论会覆盖第 1 遍，
  与 D23 裁决 6 的「不留第 1 遍 payload 冒充最终证据」一致。

### 裁决 3：内联 base64 PNG 的手写解码（DR-30）
- 事实：`smoke-t3` 的 `capture_frames` 回包是 `frames[*].image_base64`（真实 base64 PNG），
  而当时 Runtime 既不落盘也不校验，仍写了 `path`。
- 选择：在 `src/adapter/godot.rs` 内实现最小标准字母表 base64 解码（约 30 行，带单元测试），
  只接受解码结果以 PNG 签名 `\x89PNG\r\n\x1a\n` 开头；解码器内置在 adapter，不新增 crate。
- 理由：仓库当前依赖树里没有 base64 实现，本机按「离线优先」构建（§9.3 要求断网可全绿），
  引入新依赖需要联网拉取；而这里需要的只是「把服务器给的 PNG 变成字节」这一件事。
- screenshot 的判定被收敛成**一个**判据：`fs::metadata(<workspace>/.hoh/evidence/frame-00.png)`。
  主工具失败 → 回落 `capture_frames`；两者都拿不到真实 PNG → `ok=false` 且 `path=None`。

### 裁决 4：`ACTION_BINDING_UNKNOWN` 第三态（DR-33）
- 问题：DR-33 只定义了三态（不存在 / 存在但无效果 / 有效），但没规定 `get_input_actions`
  **调用失败或 payload 形状不可识别**时的行为。
- 选择：
  - 可用性**已知**且动作缺失 → `ACTION_NOT_BOUND`，`ok=false`，`supports` 追加 `P3`（DR-33 明确要求）；
  - 可用性**已知**且动作存在、已送达、位置不变 → `INPUT_HAD_NO_EFFECT`，`ok=false`，`supports` 含 F1/F2；
  - 可用性**未知**但位置发生了变化 → 记录 `ACTION_BINDING_UNKNOWN` 于 observation，**不**判失败
    （正向证据成立，输入确实送达且有效）；
  - 可用性**未知**且位置不变 → 同时标 `ACTION_BINDING_UNKNOWN` 与 `INPUT_HAD_NO_EFFECT`，`ok=false`，
    `supports` 追加 `P3`——不假装能区分两种失败模式。
- 理由：诚实性优先；把「不知道」写成第三态，而不是塞进已有的两个状态里。

### 裁决 5：`supports` 词表扩展到 P1..P6（DR-33）
- 事实：`BatteryRecord.supports` 此前只用 `F1..F17`/`N1..N4`；DR-33 要求 `ACTION_NOT_BOUND` 的
  `supports` 含 `P3`（PRD 第 2 节的工程约束「输入全部使用 InputMap 命名 action」）。
- 选择：按 DR-33 输出 `P3`；`evidence_playbook` 的步骤表同步说明；`tests/evidence_battery.rs::valid_supports`
  的白名单扩展为 `F1..F17 ∪ N1..N4 ∪ P1..P6`。
- 理由：DR-33 是规范性条款，词表必须跟上，否则「动作不存在」无法被映射到 P3 这条约束。

### 裁决 6：`harness_source_read` 的标记集与轨迹夹具（DR-32）
- 选择：扫描范围限定 `messages[*].extra.actions[*]` 的**全部字符串值**（命令、内联参数、嵌套对象）；
  标记集由「具体文件路径」放宽为目录级前缀 `src/`、`src\`、`.spec/`、`.spec\`、`.git/`、`.git\`、
  `tests/fixtures`、`tests/common`、`tests\common`、`RustProjects`。
- 理由：DR-32 的验收例子是 `cat src/config.rs`，原标记集（`src/runtime` 等）抓不到；
  而 Godot 工程惯例用 `scripts/`/`scenes/`，`src/` 前缀不会误报正常开发命令。
- 夹具配套：`FakeStep::trajectory_mentioning` 改为把文本写进 `extra.actions[*].command`
  （原实现写在 exit 消息里，那是 prompt 侧文本，DR-32 后不该再触发）；新增
  `trajectory_prompt_containing` 专门构造「只在 prompt 里出现」的反例。

### 裁决 7：既有测试的必要调整（逐条）
1. `tests/common/mod.rs::FakeStep::trajectory_mentioning` —— **必须改**：夹具把探针文本从
   exit 消息移到 `extra.actions`，因为 DR-32 规定只有工具命令是证据。
2. `tests/tool_discovery.rs::reading_harness_sources_is_recorded_as_a_warning` —— 断言不变
   （仍要求出现 `harness_source_read`），夹具命令由 `grep -n play_scene src/runtime/run_loop.rs`
   改为 DR-32 的验收例子 `cat src/config.rs`；同时新增 ①（prompt 含禁止清单 → 不产生留痕）
   与 ②（工具命令 cat src/config.rs → 产生留痕）两例。
3. `tests/evidence_battery.rs::green_battery_records_every_step_and_copies_into_the_candidate`
   —— 原断言 `replay.observation.contains("120")`（真实 120 帧采样）改为
   `contains("60 frame(s)")` + `before_position/after_position`。**必须改**：`smoke-t3` 的真实
   hold-right 记录是**恒定坐标**（`(60.0, 283.999)` 全程不变），DR-30/DR-33 之后它必须判
   `INPUT_HAD_NO_EFFECT`（该反例已另立新测试），因此不能再充当绿色夹具；绿路径改用
   `FixtureChannel::with_moving(true)` 合成的、真正响应动作的记录。
   同一用例的截图断言由「path 存在」**加强**为「文件真实存在且字节等于工具产出的 PNG」。
4. `tests/evidence_battery.rs::FixtureChannel` —— **必须改**：新增
   `with_moving` / `with_screenshot` / `with_input_actions` / `with_reply` 四个夹具开关，
   `get_input_actions` 与 `monitor_properties`（按最后一次 `simulate_action` 合成）必须有答复，
   否则 DR-33/DR-30 的用例无法构造；`green()` 默认 moving+bound+写文件。
5. `tests/evidence_battery.rs::valid_supports` —— **必须改**：白名单加 `P1..P6`（见裁决 5）。
6. `tests/role_paths.rs::submit` —— **必须改**：拆成 `submit`/`submit_in`，后者显式设置
   `HOH_VIEW_DIR`（DR-34 的第三个基准）并对未设置的用例 `env_remove`，避免环境泄漏影响断言。
7. `tests/record_symmetry.rs`、`tests/mcp_desync.rs` —— 仅新增用例，未改既有断言。
- 结论：**没有任何断言被放宽**；除上述 2 处夹具驱动表达式外，既有断言逐字保留。

### 裁决 8：`McpFailure.correlation` 装箱
- 问题：加入 `RpcCorrelation` 后 `McpFailure` 超过 clippy `result_large_err` 阈值（>128B）。
- 选择：`pub correlation: Box<RpcCorrelation>`；`&failure.correlation` 处由 deref 强制转换保持不变。
- 理由：保持 `Result<_, McpFailure>` 的签名（`call_with_retries*` 的调用方不受影响）并让 clippy 全绿。

- 回滚点：本包整体回退到 `f373dba`；Doc 回退到 `b83245a`。

## D27 — 第四次真实 T=1 冒烟（smoke-t5）：exit 0；E2 首次无污染判定通过，E3 证明非 A_1 缺陷

- 日期：2026-09（阶段五真实冒烟，第四轮；run-id `smoke-t5`）
- 触发问题：v0.6 修复包（DR-29..DR-34）落地后，派全新子代理重跑真实 T=1（工作流 `hof-rs-real-smoke-t5`）。
  注：`smoke-t4` 曾被外部信号中止（只到 Planner 起步，65 文件），保留作审计，未复用该 run-id。
- 实测事实（**50.3 分钟，50,147,756 tokens，exit_code=0**；`exit_code` 文件 / `meta.json` / `hoh status`
  三方一致：`iter-1 harness=ok gate=ok ok=true candidate=ea897618…`）：
  - **DR-29 完全生效**：24 次 MCP 调用**全部**拿到自己的响应（每次先停放 1 条陈旧响应再发只读探针），
    19 次步骤探针 + 2 次会话探针，**零 `McpResponseDesync`**；每个 raw 头都满足 `request_id == response_id`。
    `editor_errors_baseline` 终于拿到真实 `{"count":0,"errors":[]}`——**smoke-t3 的假阴性消失**。
  - **E2 = met（首个无污染判定）**：`artifact_gate.launchable=true`、`repair_retry_used=false`（闸门一次通过）、
    就绪由场景树形状确认（`main scene booted; 50 node(s) carrying a path and a type`）、截图产出真实 PNG（4246 B，签名正确）。
  - **E1/E4/E5/E6 = met**：8 条 verified claim 全部限定在结构与可启动性、均引用候选内相对路径；
    22 条 gap 均带 `player_impact`/`recommended_update`；`qa_report.md` 明确 `Result: FAIL`；
    验收方**独立重算**三方哈希：workspace == A_1 快照 == 候选副本 == `ea897618…`（26 文件）。
  - **E3 = not_met，但已证明不是 `A_1` 的缺陷**：电池报 `ACTION_NOT_BOUND`，而 `A_1` 的 `project.godot`
    明确声明 `move_left/move_right/jump`。根因是**工具链**：addon 的 `get_input_actions`（`InputMap::singleton()`）与
    `simulate_action`（`Input::parse_input_event`）都在**编辑器进程**内，而游戏是**独立进程**（`user://` 文件 IPC），
    `runtime.rs` 的游戏侧转发工具列表里没有这两个工具——编辑器侧注入**永远打不到游戏进程**。
    Developer 自己也独立得到同一结论（它给游戏侧 agent 打了 `simulate_action` 补丁并用 `execute_game_script` 验证方法存在，
    玩家仍恒为 `(60.0, 283.999)`、velocity `(0,0)`）。
  - **危险后果**：该假阴性已渗入 `qa_report` 的 Blocking finding、gap G1 与 `planner_handoff.update_targets[0]`
    → **下一轮会去修一个不存在的缺陷**（约 50M tokens）。这正是 HoH 最怕的「错误根因进入下一轮」。
  - DR 效果：DR-24 yes / **DR-29 yes** / DR-30 yes / **DR-31 yes（逐字段核对 summary == Σ attempts）** /
    DR-32 partial（假阳性消失，但两个越界动作未命中：`dir` 列 harness 根、`dir /b /s *.yaml | findstr hoh` 命中 `config/hoh.yaml`）/
    DR-33 partial（三态与四元组齐备，但可用性探针读的是**编辑器** InputMap → 假阴性）/
    **DR-34 yes（`os error 3` 归零）**。
  - 其它缺陷：**Tester 看不到真实 PNG**（`.hoh/evidence` 未复制进冻结候选 → 误报「文件不存在」gap G19）；
    **DR-18 wrap-up retry 在 `artifact_valid=true` 时仍触发**（白烧 0.94M tokens / 3.1 分钟且未改变增量）；
    `exit 0 + gate ok` 与「F1..F17 全 gap、产品不可玩」并存容易被误读为成功；
    `as_is` 起点是前几轮遗留的完整马里奥工程，本轮净增量只有 +624 B 的 addon 补丁。
  - 密钥扫描：350 文件（文本 + 原始字节两种方式）**0 命中**。
- 选择：**判定阶段一仍未完成**（E3 未达成）；把缺陷整理为 DR-35..DR-40（设计 v0.7，D28），
  派全新实现子代理修复，再派又一批全新验收子代理，最后在**重启编辑器 + 干净 A₀** 下做收口冒烟。
- 关键判断：E3 的失败不是「模型不行」，而是**证据通道错了**——必须把输入注入与观测都放到**游戏进程内**
  （优先 `execute_game_script` 等 game-forwarded 工具），否则无论模型多强都测不出可玩性。

## D28 — 详细设计升版 v0.7（DR-35..DR-40）

- 日期：2026-09（阶段三回炉，第六次）
- 触发问题：D27 暴露「证据通道错进程」与「证据可见性/触发条件/留痕/gate 语义」四类缺陷。
- 修订要点：
  - **DR-35**：输入证据必须走**游戏进程内**通道（`execute_game_script` 等）；先做**通道能力探针**
    （游戏进程内读 `InputMap.has_action`/`Input.get_axis`，按下后等待若干帧复读）；三态判定；
    编辑器侧 `simulate_action` 只作补充并标注 `EDITOR_SIDE_INJECTION`；四元组标注 `channel`。
  - **DR-36**：候选视图必须复制 `.hoh/evidence/**`（截图/回放），否则真实证据被判缺失；新增 `runtime.max_evidence_bytes`。
  - **DR-37**：wrap-up retry 收紧为 `LimitsExceeded && artifact_valid == false`，并记录 `wrap_up_retry_reason`。
  - **DR-38**：留痕补齐 `config/**`、`DECISIONS.md`、`Cargo.toml` 与 harness 仓库根路径。
  - **DR-39**：`result.json.prd_coverage` + `hoh status` 三列（`harness=/gate=/prd=`）+ 结束摘要；
    **不改变退出码语义**（退出码反映运行时契约，不反映模型产出质量）。
  - **DR-40**：新增 `hoh init`（不依赖 MCP/模型）解决 `--fresh-workspace` 与 doctor 预检的循环依赖。
- 回滚点：`DESIGN-DETAIL.md` 回退到 `294c35f`；代码回退到 `d7da254`。

## D29 — 修复包 v0.7（DR-35..DR-40）的实现期裁决

- 日期：2026-09（阶段四，修复包 v0.7 实现）
- 触发问题：DR-35..DR-40 已冻结，但「Expression 能触达什么」「artifact_valid 怎么判定」「prd 总数怎么来」
  「init 的退出码怎么映射」等取舍会改变既有契约或决定 DR 能否在真实运行中生效，必须显式记录。
- 提交对应：见本包各提交信息（`(DR-38)` / `(DR-39)` / `(DR-36)` / `(DR-37)` / `(DR-40)` / `(DR-35)`）。

### 裁决 1：DR-38 的命中规则分三层，且必须排除 `.hoh`
- 事实（`smoke-t5`）：两个越界动作分别是 `dir`（cwd = harness 仓库根）与
  `dir /b /s *.yaml | findstr hoh`；后者**不含任何路径**，只靠「按名字搜索整个树」这一语义构成越界。
- 选择：命中判定拆成三个**纯函数**，任一为真即产生 `harness_source_read`：
  1. `mentions_forbidden_source(text)`：标记集在 `src/`、`.spec/`、`tests/fixtures`、`tests/common`、
     `RustProjects`、`.git/` 之外补齐 `config/`、`config\`、`DECISIONS.md`、`Cargo.toml`；
  2. `enumerates_harness_tree(text)`：出现列举/搜索动词（`dir`/`ls`/`find`/`findstr`/`grep`/
     `get-childitem`/`gci`/`tree`/`select-string`）**且**出现整树模式（`*.`、`**` 或 `/s`/`-r`/
     `-recurse`）**且**出现 harness 自指词（`hoh`/`harness`/`hof-rs`/`decisions.md`/`cargo.toml`）；
  3. `mentions_harness_root(text, root)`：命令文本（两种分隔符归一化后）包含**运行期注入**的
     harness 仓库根路径（`runtime.out_of_tree_root`，默认进程 cwd），`src/**` 内不写死任何盘符。
- 关键取舍：判定 2 之前先**剔除 `.hoh`**。`.hoh` 是运行期自己的产物目录，Tester/Developer 列举
  `.hoh/deterministic/*.json` 是正常工作；不剔除就会把「hoh」当成 harness 自指词而误报。
- 理由：三个判据各自独立可测（单元测试覆盖「命中/不命中」两侧），且 `dir F:/moonbit-hof-rs`
  与 `dir /b /s *.yaml | findstr hoh` 两条真实越界都有唯一对应的判据。
- 回滚点：`hygiene.rs` 的四个函数与 `run_loop::note_source_reads` 的签名。

### 裁决 2：DR-36 的证据复制与体积阈值
- 选择：`build_view` 之后，除 `.hoh/deterministic/**` 外再复制 `<workspace>/.hoh/evidence/**` 到
  `<candidate>/.hoh/evidence/**`（`.hoh` 不参与 `hash_tree`/快照，因此不改变 `candidate_id`）。
- 超限语义按 DR 字面：**仍复制**并记录体积，在 `result.json.warnings` 追加
  `evidence_too_large: <相对路径> (<n> byte(s) > <limit>)`；绝不静默跳过、绝不改成「不复制只告警」。
- 新配置键 `runtime.max_evidence_bytes`（默认 8388608 = 8 MiB），`serde(default)`，`config/hoh.yaml`
  同步写入；除该键外未改任何配置。
- 回滚点：`run_loop` 中 `copy_evidence` 调用点与 `RuntimeConfig::max_evidence_bytes`。

### 裁决 3：DR-37 的 `artifact_valid` 与理由字段
- 问题：实现里 Developer 的 `artifact_valid` 恒为 `workspace.is_dir()`（恒真），所以「收紧触发条件」
  若不真正实现判定就等于没收紧。
- 选择：
  - `ProjectAdapter` 新增 `fn developer_artifact_valid(&self, workspace: &Path) -> bool`，**默认返回
    `false`**（DR-37「无法判定则视为 false，保守」）；因此未实现该判定的 adapter 保持 DR-18 的既有行为。
  - `GodotAdapter` 的实现 = 「主场景 `.tscn` 可被 `validate_scene_structure_in` 校验」**且**「主场景确实
    引用了至少一个存在且非空的 GDScript 入口脚本」。
  - 触发条件收紧为 `exit_status == LimitsExceeded && artifact_valid == false`。
  - `result.json.wrap_up_retry_reason ∈ {artifact_missing, not_triggered}`：**任何**角色用了 wrap-up
    重试（Planner/Tester 的 schema 路径与 Developer 的预算路径）都记 `artifact_missing`，否则
    `not_triggered`。这就是 DR-37 测试③「正常收尾 + 产物缺失 → 触发（保持既有行为）」的落地口径：
    「正常收尾但产物缺失」走的是既有的 **schema 重试**路径（`schema_gate.rs::missing_artifact_counts_as_attempt`），
    该路径行为不变，并在结果里得到同一个 `artifact_missing` 理由。
- 回滚点：`ProjectAdapter::developer_artifact_valid`、`GodotAdapter` 的实现、`run_loop` 开发者段落。

### 裁决 4：DR-39 的 `prd_coverage` 与 total
- 选择：`prd_coverage: {verified, gap, verified_ids[], gap_ids[]}` **逐字**按 DR 落地，不额外加 `total`
  字段（避免与冻结文本不一致）；总数由推导函数给出：
  - 若 `verified_ids ∪ gap_ids` 中出现任何 `F1..F17` 形态的 id → `total = 17`（PRD 的 F 需求总数）；
  - 否则 `total = verified + gap`，并在 `status` 行尾标注 `(total=derived)`。
- `status` 每轮打印 `harness=`、`gate=`、`prd=<verified>/<total>`；`hoh run` 结束打印
  `prd coverage: <v>/<total> verified`。**退出码语义完全不变**（`run_exit_code` 只看 `artifact_gate`）。
- Runtime 只做**派生**：`verified`/`gap` 直接来自 E_t 的 `verified_records`/`gap_records`，不判定 claim。
- 代价：`RunSummary` 增加一个字段，`tests/result_semantics.rs` 的结构体字面量必须同步（已记入 regressions）。
- 回滚点：`model::PrdCoverage`、`record::IterResult::prd_coverage`、`cli_impl::status`/`run`。

### 裁决 5：DR-40 的退出码映射与执行顺序
- 选择：`hoh init` 只做「（可选）清空 + `ProjectAdapter::initialize`」，不构造 harness、不建 MCP 通道、
  不解析密钥；适配器失败统一映射为 `HofError::External` → 退出码 **4**（「适配器不可用」，符合 §8 的
  「外部依赖不可用」）。`clap` 的用法错误本身就是退出码 2。
- `hoh run --fresh-workspace` 改为「先 init/清空重建 A₀ → 再 doctor 预检 → 再跑」；doctor 失败时
  **保留**已重建的 A₀ 直接返回 4，不回滚、不删除（DR-40 明确要求）。
- 回滚点：`cli::Command::Init`、`cli_impl::init`、`cli_impl::run` 中 start_state 计算的位置。

### 裁决 6（重要）：DR-35 的工具能力事实与实现口径
- **实测事实（本机 Godot 4.7.1-stable-mono，`--headless --script`，`Expression.execute([], base, false)`）**：
  `Expression` 在带 base instance 时**只能解析 base 的成员**，引擎单例与全局类**一律不可达**：
  ```
  Input.is_action_pressed("move_right") => failed=true | err=Invalid named index 'Input' for base type Object
  InputMap.has_action("move_right")     => failed=true | err=Invalid named index 'InputMap' for base type Object
  Input.action_press("move_right")      => failed=true | err=Invalid named index 'Input' for base type Object
  Engine.get_singleton("Input")         => failed=true | err=Invalid named index 'Engine' for base type Object
  InputEventAction.new()                => failed=true | err=Invalid named index 'InputEventAction' for base type Object
  JSON.stringify(...) / OS.get_name()   => failed=true | err=Invalid named index '...' for base type Object
  get_class() / get_tree() != null / str({...}) => failed=false（base 成员与全局工具函数可用）
  ```
  这把 `smoke-t5` 里 Developer 看到的
  `hoh: JSON-RPC error -32603: Internal error: Execute error: Invalid named index 'Input' for base type Object`
  从「偶发」确认为**工具通道的硬性限制**：`execute_game_script` 走的是
  `addons/godot_mcp_rs/mcp_runtime_agent.gd` 的 `Expression`（base = 该 autoload 节点），
  因此 DR-35 字面要求的裸 `Input`/`InputMap` 脚本**在任何项目里都不可能执行成功**。
  另经实测：`root.push_input(str_to_var('Object(InputEventAction,...)'))` 可构造事件但**不会**更新
  `Input.is_action_pressed`/`get_axis`；能更新 Input 状态的只有 `Input.parse_input_event`，而它必须先拿到
  `Input` 单例（不可达）。A_0 的 addon 里唯一调用 `Input.parse_input_event` 的方法是
  `_cmd_replay_recording`，其 action 被硬编码为 `"replay_event"`（不可参数化）。
- 选择（**不越权改设计**，只把 DR-35 落到可实现的最大诚实范围）：
  1. 仍然按 DR-35 的机制发**设计字面脚本**（`str(InputMap.has_action("move_right"))`、
     `str(Input.is_action_pressed("move_right"))`、`str(Input.get_axis("move_left","move_right"))`、
     `str(Input.action_press(..))` + 若干帧后复读），原始返回原样落
     `.hoh/deterministic/raw/input_channel_probe.json`；**形状不可识别或调用失败 → `ACTION_BINDING_UNKNOWN`，
     绝不降级为 `ACTION_NOT_BOUND`**（DR-35 的第三态正是为此存在）。
  2. 同时用**可达**的表达式读游戏进程内的 `Player.position`（`get_tree().current_scene.get_node_or_null(
     "Player").position`，`smoke-t5` 的 Developer 轨迹已证明该形态可用），把「游戏进程可达」与
     「Input 单例不可达」两类事实分开落在 raw 里，供 Tester 与人工区分「工具不行」与「游戏不行」。
  3. 「press 后等待→帧再复读」由**游戏进程内**的 `monitor_properties`（game-forwarded，按帧采样
     Player.position）承担：`Expression` 无法 `await`，脚本内等待不可实现，这是对 DR 字面的最小偏离。
  4. `input_replay` 的最终判定只看**游戏进程内观测到的位置变化**；编辑器侧 `simulate_action` 仅作补充记录
     并标注 `EDITOR_SIDE_INJECTION`，四元组一律带 `channel: game_process|editor_process`。
- 结论/风险：本机与当前 addon 下，探针会得到 `ACTION_BINDING_UNKNOWN`（而不是假阴性的
  `ACTION_NOT_BOUND`）——这消除了 D27 里「假阴性渗入下一轮」的危险，但**E3 仍不可判定**。
  要让 E3 真正可判定，必须给游戏进程装一个可参数化的输入桥（例如由 harness 在 `A₀` 注入一个 autoload
  帮助脚本，或修 addon 的 `execute_game_script` 改成能访问引擎单例的 GDScript 执行方式）。
  这两条都**超出 DR-35 授权**且会改动「被评估对象」（A_t 会多出 harness 自己的 autoload），
  因此不在本包内擅自实施，作为 `known_risks` / `open_items` 上报，交决策者裁决。
- 回滚点：`godot.rs` 的 `input_channel_probe` 步骤、`step_input_replay`、`replay_quadruple`。

## D30 — 方向变更：把 MCP 工具逻辑集成进 Godot 本体（内置模块 `mcp_server`），以解锁 E3

- 日期：2026-09（阶段三回炉后的**架构级方向决策**，由用户提出并批准计划）
- 触发问题：D27/D29 已把 E3 失败的根因锁定在**工具链的进程边界**：
  GDExtension 只存在于编辑器进程，`simulate_action`/`get_input_actions` 作用于**编辑器**的输入系统；
  游戏是独立子进程，靠 `user://` 文件 IPC 转发；而 `execute_game_script` 走
  `Expression.execute`，**访问不到任何引擎单例**（`Input`/`InputMap`/`Engine`/`OS` 全部
  `Invalid named index`，D29 裁决 6 实测）。结论：**在现有 addon 架构下，无论模型多强，E3 都不可判定。**
- 用户裁决（4 项，已确认）：
  1. **基线** = 用户 fork 的 master（`code/godot`，`4.8.0.dev`，HEAD `57277407`，remote 是
     `git@github.com:shiyukonghui/godot.git`），**不切 4.7.1-stable**；
  2. **覆盖策略** = **分类分批 + 每批对等门**（不追求一次性 174 工具全量对等）；
  3. **游戏进程归属** = **hof-rs Runtime 自己拉起游戏进程**（`--mcp-port=N`，捕获 stdout、掌控退出码与清理），
     不打补丁让编辑器 run bar 代传端口；
  4. **游戏开发语言** = 用户要求**使用 C#** → 因此引擎必须 **mono 构建**（`module_mono_enabled=yes`），
     工程侧 `.csproj` 的目标框架是 `net8.0`；本机已具备 .NET SDK 9.0.100/9.0.300 + .NET 8 运行时。
- 决策者补充的架构判断（写入计划）：
  - 模块形态：**内置 module `modules/mcp_server/`**（非 GDExtension）。单例在
    `MODULE_INITIALIZATION_LEVEL_SCENE` 注册 → 编辑器与游戏进程**同一份代码都可用**；
    `Engine::is_editor_hint()` 决定暴露哪些工具；编辑器侧可选 `EditorPlugins::add_by_type<T>()`（EDITOR 级）。
  - 传输与并发：**`TCPServer` + 主线程逐帧泵（`SceneTree::process_frame`）+ 按 JSON-RPC `id` 关联**。
    **全程无跨线程队列**——这同时从构造上消灭了 D24 的「响应慢一拍/错位」缺陷类别
    （其根因已定位为 `transport_http.rs` 用单一 FIFO `try_recv` 取响应、不按 id 关联）。
  - 端口：`--mcp-port=N` > `ProjectSettings: godot_mcp/port` > 默认（编辑器 9877 / 游戏 9878）；
    **游戏侧默认不开启**，必须显式传参，避免发行版开端口。
  - 被否决的备选：①继续用 GDExtension 只修 `execute_game_script`（治标，不解决进程边界）；
    ②给编辑器 run bar 传端口（生命周期/输出不可控）；③SSE/WebSocket 传输（hof-rs 只需 `POST /mcp`）；
    ④编辑器↔游戏双端点 IPC（被「两进程各自独立端点」取代）。
- 分两步构建以隔离最高风险：**先非 mono** 打通「SCons + 模块 + HTTP」，**再 mono 收口**并让 C# 版 Mario 跑起来。
- 里程碑：M0 工具链与非 mono 基线构建 / M1 模块骨架+HTTP+JSON-RPC / M2 B1+B2 批次（**E3 解锁点**）/
  M3 mono 构建 + C# 工程可跑 / M4 B3+B4 批次 / M5 B5 批次 + hof-rs 切端点 + 真实 T=1 冒烟收口。
- 连带的需求变更（必须按阶段关卡显式回到阶段一更新，不得在实现里回填）：
  `PRD-mario.md` 增加 **P7「全部游戏逻辑使用 C#」**、**P8「C# 编译零错误」**；
  `skills/godot-dev.md` 重写为 C# 版；Tester 的编译证据改为 `dotnet build` 输出 + `get_editor_errors`；
  `A₀` 脚手架需含 mono 生成的 `.csproj`；`hoh doctor` 增加「引擎是否 mono / dotnet 可用性 / 双端点探活」预检。
- 本轮规划产生的分析产物（**非交付物，可删**）：
  `F:\RustProjects\godot-mcp-pro\code\godot\.graphifyignore` 与 `graphify-out\`
  （**131,616 节点 / 297,366 边 / 2,074 社区**，`--code-only` 纯本地 AST、**0 token**；含 `GRAPH_REPORT.md`）；
  代码变更后用 `graphify update` 增量重建（无 API 成本）。
- 回滚点：hof-rs 本仓库**未被本次规划修改**（仍为 v0.7 冻结态 `4b3e06f`）；引擎侧改动全部在 fork 的
  本地分支 `feature/mcp-server-module` 上，**只本地提交、不推送**（除非用户明确要求）。

## D31 — 工具命名审计：改名是契约变更，先审计再动手（用户指令）

- 日期：2026-09（M0 通过、M1 动工前）
- 触发问题（用户）：历史运行中出现「**工具名与功能不够对应，导致智能体选错工具**」。
  工具的唯一消费者是 AI 智能体，因此**名字可以更长、更直白**，目标是「看名字就秒懂功能、且不会与邻近工具混淆」。
- 已识别的真实痛点（决策者的初步判断，待审计确认）：
  1. **作用域不可见**：成对工具「编辑器进程 vs 游戏运行进程」在名字上没有区分，
     例如 `get_scene_tree` / `get_game_scene_tree`、`get_node_properties` / `get_game_node_properties`、
     `execute_editor_script` / `execute_game_script`、`set_game_node_property` / `update_property`、`move_node` / `move_to`。
     这正是 `smoke-t5` 里 QA 误判「`ACTION_NOT_BOUND`」的同源风险——智能体分不清工具作用于哪个进程。
  2. **动词不统一**：`update_*` / `set_*` / `edit_*`；`get_*` / `read_*` / `list_*`；`run_*` / `play_*` / `execute_*`。
- 选择：**先派全新子代理做完整审计**（174 个工具逐个对照实现语义），产出
  ①面向智能体的命名规范 ②逐个审计表 ③**易混淆分组分析** ④`old→new` 迁移映射与影响面 ⑤兼容/别名策略 ⑥分阶段落地顺序；
  决策者据此决定「采纳/部分采纳」，再落到契约变更。
- 关键约束：**只改真正会误导的**——改名是契约变更，成本必须小于收益；已清晰的工具明确标注「不改」。
- 预期影响面（审计需逐项确认）：`config/hoh.yaml` 工具策略、`src/tools/policy.rs`、`src/runtime/evidence.rs` 的电池步骤名、
  `src/prompts/*.md`、`src/skills/*.md`、`tests/**`、Rust addon 的 `commands/**`、以及新的引擎模块的 `tools/list` 契约源。
- 回滚点：审计结论只是提案，未落地前不影响任何既有代码。

## D32 — M1 传输层不造轮子：先调研现有 C++ MCP 库（用户指令）

- 日期：2026-09（M0 通过、M1 动工前；M1 工作流已因此中止，未产生任何代码）
- 触发问题（用户）：**「M1 的工作在自己造轮子支持 mcp 服务，这完全没有必要，调研使用现有的 C++ mcp 库」**。
- 决策者对该指令的判断：此前 DESIGN-DETAIL 的 GDR-5/GDR-6 让实现者**手写 HTTP/1.1 子集 + JSON-RPC 信封**，
  这是把「协议实现」当成核心工作，而它并非本项目的差异化价值；协议 bug（分块传输、keep-alive、半包、并发、id 关联）
  恰恰是最容易出错且最难验收的部分——`D24` 的响应错位事故已经证明这类错误代价极高。
- 选择：**暂停 M1 实现**，先派全新子代理调研候选库并给出决策矩阵与推荐（含 vendor 落地步骤），
  同时把「完全不引入第三方、用 Godot `TCPServer`+`JSON` 自造」作为**对照项**诚实评估。
- 调研必须核实的本地事实：Godot 该分支的 **C++ 标准**、`thirdparty/` 的 vendor 与 SCsub 集成做法、
  `TCPServer`/`StreamPeerTCP`/`JSON` 的实际接口能力。
- 硬性约束：库的许可证须与 MIT 兼容；**不得强制线程模型**（工具必须在主线程执行，Godot API 非线程安全）；
  只需 **HTTP `POST /mcp` 的 JSON-RPC**（不需要 SSE/WebSocket/stdio，但可注明是否顺带支持）；
  响应必须能按 `id` 关联。
- 预期影响：**DESIGN-DETAIL 将新增 GDR-12+**（传输层选型与 vendor 方案），GDR-5/GDR-6 相应修订或废止；
  M1 的范围与验收脚本随之调整（验收用例不变，只是实现载体变）。
- 回滚点：调研结论未落地前，引擎源码零改动（M0 的非 mono 基线构建产物可用）。

## D33 — M1 传输层选型结论：**保留自研**（无合适的 C++ MCP 库），加固项按需触发（D32 的裁决）

- 日期：2026-09（D32 调研回收后的裁决）
- 调研结论（全部附来源并实测抓取，非搜索引擎摘要）：
  1. **不存在官方 C++ MCP SDK**：`modelcontextprotocol` org 官方 SDK 只有
     TS/Python/Kotlin/Java/Swift/Rust/Ruby/C#/Go/PHP；`anthropics` org 只有 python/ts/go/java/ruby/php/csharp。
  2. 第三方 C++ MCP SDK 中可用的三个——**cpp-mcp**（325★, MIT, C++17, 2025-03-26 Streamable HTTP）、
     **cxxmcp**（24★, MIT, 自称 RC）、**gopher-mcp**（147★, Apache-2.0, 80 open issues）——**全部与核心约束正面冲突**：
     都自带 HTTP 服务器 + 自带线程模型 + 自带 nlohmann/json，而我们需要「单客户端 / 主线程执行工具 /
     Godot `Variant` JSON / 单头文件级依赖」。
  3. **最强否决性约束（实测）**：Godot 默认 `disable_exceptions=yes`（`SConstruct:277`），
     MSVC 下定义 `_HAS_EXCEPTIONS=0` 且**不加 `/EHsc`**（`SConstruct:934-940`）；C++ 标准为 **C++17 + `/permissive-`**
     （`SConstruct:924,928`）；`dev_mode` 下 `warnings=extra` + `werror=yes`（`/W4+/WX`）。
     `cpp-mcp` 自有源码 27 处 `throw` + nlohmann 48 处 `throw`；nlohmann 的 `JSON_NOEXCEPTION` 走 **`std::abort()`**
     ——在游戏引擎里对畸形客户端输入 abort 属崩溃风险。
  4. **既成事实**：被中止的 M1 工作流已在 fork 里写出 `modules/mcp_server/{mcp_http_server,mcp_jsonrpc,tool_registry,
     mcp_server,tools/project}.*` + 27 条 doctest + `scripts/accept_m1.ps1`，并已用它成功构建（20:55 的二进制）。
     实测其设计已**结构性排除** D24 的 FIFO 错位（`mcp_http_server.h` 注释明写 no shared arrival-ordered queue，
     响应写回发起它的连接）。
  5. 已识别的真实缺口（实测逐行核对）：①**不支持 `Transfer-Encoding: chunked` 请求体**（只认 `Content-Length`，会 400）；
     ②不处理 `Expect: 100-continue`（curl >1024B 会白等约 1s）；③`Request` 不暴露 header map
     （未来若要 `Mcp-Session-Id` 才需要）；④`String::utf8()` 对非法 UTF-8 行为不明确。
- 选择：**不引入任何 MCP SDK**；HTTP 传输保留 Godot `TCPServer`+`StreamPeerTCP` 自研子集，JSON 用引擎自带
  `core/io/json.h`（`Variant`/`Dictionary` 零桥接）。**理由**：本场景被明确限定为「只服务我们自己的 harness、
  单客户端、顺序请求、`POST /mcp` + `Content-Length`」，引入 SDK 是净负收益（线程模型冲突、异常体系冲突、
  双层 JSON、且 SDK 的 SSE/`Mcp-Session-Id` 会强制 hof-rs 增加会话状态）。
- **加固项按需触发**（不现在做）：
  - 触发条件 A：harness 出现 chunked body（例如改用第三方 HTTP 客户端或流式 body）→
    vendor **`picohttpparser`**（2 文件 32 KB，MIT/Perl 双许可取 MIT，无状态/无分配/无线程/无异常），
    用它替换手写 framing 中「body 分帧」那一小块（`phr_parse_request` + `phr_decode_chunked`）。
    vendor 步骤已核实（本 checkout 的 `thirdparty/` **没有** `SCsub`，须照 `modules/enet/SCsub` 模板：
    `env_thirdparty.disable_warnings()` + `add_source_files(..., "#thirdparty/picohttpparser/picohttpparser.c")`），
    且**必须**登记 `thirdparty/README.md`（字母序 + 前后各两空行）与 `COPYRIGHT.txt`
    （`core/SCsub:270-272` 会把 `COPYRIGHT.txt` 编进 `core/license.gen.h`，出现在编辑器 License 界面）。
    **【D39 更正】本条原文写的「无 `Content-Length` 时会 400」是错的：实测为 `411 Length Required`**
    （TE 完全未被解析，落入 `MISSING_CONTENT_LENGTH`）。411 才是语义正确的状态码，已由独立验收确认并写进单测。
  - 触发条件 B：需要规范级 Streamable HTTP 会话（`Mcp-Session-Id`/GET SSE/DELETE）→ 重新评估（届时备选是
    `cpp-httplib` 单头 + `CPPHTTPLIB_NO_EXCEPTIONS`，代价是后台线程 + 主线程任务队列）。
  - **小加固（建议随 M1 收尾做）**：处理 `Expect: 100-continue`（20~30 LOC），避免 curl 调试与严格客户端异常。
- 契约固定：**hof-rs 只发带 `Content-Length` 的 `POST /mcp`**（写入 REQUIREMENTS 作为当前契约）；
  任何引入 chunked 的改动必须先触发加固项 A。
- 回滚点：不改任何既有代码；结论只影响后续选型。

## D34 — 工具命名审计结论：**部分采纳 P0（48 项）+ 单向标记规范 + 先止血后改名**

- 日期：2026-09（D31 调研回收后的裁决）
- 调研结论（174/174 逐个对照实现，每条都有 `file:line` 依据）：
  - **改名不是审美问题，是三类可复现事故源**：
    ① **作用域不可见**：真正作用于运行中游戏的只有 **24 个**（19 个 runtime + 4 个 test + `get_game_screenshot`），
       其中 20 个名字未说明进程；反向地，**`simulate_*`(5) 与 `get_input_actions`/`set_input_action` 注入的是
       编辑器进程的 `Input`/`InputMap` 单例，根本到不了游戏**——这**独立复现了 D27 的 E3 根因**。
    ② **谎报能力（6 个）**：`export_project`（TODO，硬编码 `export_started:true`）、`bake_navigation_mesh`（恒真）、
       `get_test_report`（固定文案）、`clear_output`（只打换行）、`set_auto_dismiss`（写无人读取的 static）、
       `navigate_to`（直接回「请自行实现」）；另 `tilemap_set_cell`/`tilemap_fill_rect` 用单参 `set_cell`
       **把格子擦掉却报 set:true/filled:N**。
    ③ **近重名语义相反/重复实现**：`search_files`(文件名) vs `search_in_files`(内容)；
       `find_node_references` 与 `search_in_files` 是同一操作的两份实现；`move_node`(reparent) vs `move_to`(改坐标)；
       `batch_get_properties`(GAME) vs `batch_set_property`(ED)。
  - 规模：建议改名 **86 个（49%）**，其中**高风险 48 个**；明确不改 88 个。
- 选择：**部分采纳**，具体：
  1. **采纳命名规范**：`<verb>_<object>[_<qualifier>]`，动词闭集，**废除 `update_`**（单属性一律 `set_`），
     `get_`/`read_`/`list_` 按「内存对象/文件内容/集合」切分。
  2. **采纳「单向标记 + 单例强制」**（这是决策者初判的修正）：唯一后缀方向 = 游戏侧 `_in_running_game`（24 个），
     **不带标记 = 编辑器/项目磁盘/OS 上下文**；只有「每进程各有一份实例的全局单例」的编辑器侧才加 `_in_editor`
     （`simulate_*`、`*input_action*`、`*audio_server*`、`*performance_monitors`，约 12 个）。
     理由：标记少数派比给 150 个编辑器工具都加标记便宜 7 倍，且能写成**注册期可机械校验的后缀谓词**。
  3. **采纳 P0 的 48 项改名** + **5 项「未实现前不注册」**（`clear_output`/`set_auto_dismiss`/`export_project`/
     `bake_navigation_mesh`/`get_test_report`）+ **4 项「不改名但必修实现」**（`disconnect_signal`、
     Expression 多语句路径、`add_state_machine_transition` 枚举错位、`tilemap_*` 先修实现）。
  4. **P1 的 38 项只做与 P0 同族的 9 项**，其余记为技术债（等引擎模块移植时顺手改）。
  5. **不保留可见别名**：`MCPToolRegistry` 的 `tools` map（可调用）与 `order` Vector（决定 `tools/list`）天然分离，
     旧名不 push 进 `order` 即可；保留别名会与「前缀式授权」叠加出绕过面。
- **最高严重度的安全发现（必须写进实现任务书）**：hof-rs 的工具策略是**前缀匹配 + 精确名单**
  （`src/runtime/policy.rs:184-245`：`MUTATING_PREFIXES` = add_/create_/delete_/remove_/set_/update_/edit_；
  `MUTATING_EXACT` 含 `move_node`、`set_game_node_property`、`bake_navigation_mesh`）。
  因此 **`move_node` → `reparent_node` 会掉出 `MUTATING_EXACT` 且不以任何 mutating 前缀开头
  → Tester 会静默获得改名权**（`policy.rs:223`）。**必须加不变量测试 `is_mutating(new) == is_mutating(old)`**，
  对该项显式豁免并另立安全断言。
- 对 D31 假设的两处更正（审计实测）：工具名**不在** `config/hoh.yaml`（只有端点/超时/重试等），
  也**不在** `src/runtime/evidence.rs`；真实落点是 `src/runtime/policy.rs`、`src/adapter/godot.rs`（含
  `GAME_PROCESS_CHANNEL`/`EDITOR_PROCESS_CHANNEL` 两个既有通道常量，新名字应与它们对齐）、
  `src/adapter/mod.rs`（电池步骤名）、`src/prompts/**`、`tests/**`、addon 的 `commands/**`。
- **两个前置阻塞项（必须先做，否则改名没有验收闸门）**：
  A. **复核 `MCPScreenshot` 机制**：`get_game_screenshot` 依赖游戏侧预写 `user://mcp_screenshot.png`，
     但审计在 `addons/` 下**未找到生成该文件的 autoload**；若确实不存在，hof-rs 电池的 `play_scene_ready`
     会稳定失败——这是独立缺陷，须优先确认（与 E2/E3 证据链直接相关）。
  B. **把 `tools/list` 逐字一致性从 2 个工具扩展到全量 174**（当前只有 2 个工具受契约约束，
     改名后契约源将没有验收闸门）。同时决定是否顺手修 `tools_list.json` 描述的双重编码
     （`accept_m1.ps1` 已有「接受原始或还原值」的兜底，不修则该兜底会永久化）。
- 落地顺序（采纳）：**Phase 0 止血（零改名）→ Phase 1 冻结规范 + registry lint 闸门 → Phase 2 P0 原子切换
  （单提交全绿，含 `is_mutating` 不变式）→ Phase 3 P1 同族 9 项 → Phase 4 addon 按新名逐个移植（未移植即不注册）
  → Phase 5 清理兜底**。
- 回滚点：改名未落地前不影响任何既有代码；Phase 0 止血的每一项都是可单独回滚的小改动。

## D35 — M1 中断工作树的 triage：前任在途改动是**真实缺陷修复**，不是半成品

- 日期：2026-09（M1 收尾）
- 触发问题：D32 时我中止了 M1 工作流，但那个子代理**在取消前已把模块写进 fork**（4 个提交 + 27 条 doctest +
  `accept_m1.ps1`），并留下**未提交的在途改动**（`mcp_http_server.{h,cpp}`、`mcp_server.cpp`）与一个
  `m1-concurrency-repro.ps1`。必须由**全新子代理**独立 triage，不得采信前任结论。
- 实测结论：
  - 在途改动是**缺陷追查的中途**，不是半成品：其中 `_read()` 里新增的 `connection.peer->poll();` 是**真实修复**——
    `StreamPeerSocket::get_status()` 只返回缓存状态，不调 `poll()` 就永远不会把对端 FIN 转成断开，
    于是死连接会一直占到 30 s idle 超时，**永久吃掉 16 条连接预算**。
  - **A/B 实测**（同一二进制路径，只回退这三个文件后重建，52 s）：无 `poll()` 时「fresh request served = False after 8517 ms」；
    有它时「fresh request served = True after 30 ms」。**端点确实会在 16 条短连接后彻底不可用。**
  - 另两处（`close_reason` + 两条 `print_verbose`）是**诊断**，被有意保留（verbose-only、有界，
    且正是它们把下面那个缺陷从猜测变成一行日志可查）。
  - `bin/` 里的二进制相对工作树是**陈旧**的（前任改完没重建）。前任留下的 `m1-concurrency-repro.ps1` 被**删除**
    （它是**假阴性制造器**：读取循环非阻塞、会在服务端仍按每帧 8 条排水时提前放弃；实测同一二进制报 104/104、8/104、再崩溃），
    其诊断意图转为**提交进仓库的确定性用例** `case15_connection_reaping`，并且它崩溃时泄漏的编辑器 PID 已被清理。
- 选择：采纳该修复并继续收尾；不重复造轮子（模块的 HTTP/JSON-RPC 已可用，与 D33 的选型结论一致）。
- 回滚点：`_read()` 的 `peer->poll()` 一行；诊断字段可独立移除。

## D36 — M1 的里程碑门曾失败：**idle 超时的 uint64 下溢**把活连接当空闲掐断

- 日期：2026-09（M1 收尾）
- 触发问题：`case8_concurrent_100`（G4 的关键门）**先失败**：
  `Unable to write data to the transport connection: An existing connection was forcibly closed by the remote host`。
- 根因（由 verbose 日志定位，非猜测）：`poll()` 每帧只取一次 `now`，而 `_read()` 用
  `OS::get_singleton()->get_ticks_msec()` **另取一次更晚的时间**打 `last_activity_ms`；
  `now - last_activity_ms` 在 uint64 上**回绕成约 1.8e19 ms**，于是 idle 判定对**刚收到 1320 字节流水线请求的活连接**命中，
  连接被以 `reason=5` 掐断、其输入缓冲未解析。这正是前任那个 repro 一直在撞的形状（它追对了子系统，但没走到算术）。
- 选择：修复为 `_read(connection, now)` 使用**帧时钟**，并抽出带守卫的 `MCPHttp::is_idle_timeout()` 辅助函数，
  用单测把边界钉住。修复后两次完整验收运行的日志里：43 次 `read_failed=true/reason=0` 的正常排水、
  1 次刻意的 `reason=3`（413）、**0 次「有未解析数据的 idle 丢弃」**。
- 影响：G4（并发 100 零错位）从失败转为通过，并额外跑 6 轮×100 = 600/600 id 全匹配。
- 回滚点：`mcp_http_server.cpp` 的 `_read(Connection&, uint64_t)` 签名与 `is_idle_timeout()`。

## D37 — M1 收尾的三项实现裁决（Expect:100-continue / chunked 状态码 / 孤儿节点）

- 日期：2026-09（M1 收尾）
- 1. **`Expect: 100-continue` 已按 D33 的小加固实现**（TDD：先有**行为级原生红**——发头不带 body 时 3 s 内收不到
  `HTTP/1.1 100 Continue`；再有**编译级红**；实现后中间响应 22 ms 内到达、恰好一次、最终 200）。
  实现要点：`ParseOutcome` 增 `expect_continue`（仅当头块完整、`Content-Length>0` 且存在该头时置位）；
  `build_continue_response()` 返回逐字的 `HTTP/1.1 100 Continue\r\n\r\n`（1xx **不得**带 Content-Length/Content-Type，有单测钉住）；
  中间响应排进**该连接自己的** out_buffer 以保序，且每请求恰好一次。
- 2. **更正 D33 的措辞**：chunked-only 请求实际返回 **411 Length Required**（而非 D33 写的 400）。
  411 才是「有 body 却无 Content-Length」的语义正确状态码；**采纳实现的真实行为并把它写进单测固定**，
  不为了对齐我写错的一句话去改行为。
- 3. **孤儿节点退场**：`bootstrap()` 在 SceneTree 始终不出现时（600 次后）**销毁实例并注销单例**
  （新增 `_retire_unattached()`）。原因：不销毁会让**一条无关的引擎测试**失败——
  `modules/gdscript/tests/.../call_native_static_method.out` 的期望输出里多出一行
  `1526726744 - Stray Node: (Type: MCPServer) (Source:)`。修好后全引擎 `--test` 1456/1456 全绿。
  这是对 GDR-3「报错并禁用」的补全（真正禁用），未改变注册时机（仍为 SCENE 级）。
- 其它登记为**偏差**（不改行为）：`/mcp` 状态体新增 `connections` 字段（验收用例的可观测点，附加字段）；
  `accept_m1.ps1` 由 14 行增至 17 行（新增连接回收与 Expect 两例 + 端口守卫，原行未改）；
  继承来的诊断字段保留。
- 回滚点：`mcp_http_server.cpp` 的 `expect_continue`/`_queue_continue`；`mcp_server.cpp` 的 `_retire_unattached()`。

## D38 — 工具命名最终决定：**一次做全 + 名字更长更直观 + 通道前缀**，并因此**重做授权判定**（用户指令）

- 日期：2026-09（D34 的用户裁决，覆盖 D34 的「部分采纳」）
- 用户指令：**① 改名一次做全（不再分 P0/P1）；② 名字可以更长更直观——智能体调错一次工具浪费的 token 远超过名字本身的 token，不要怕长，区分度要更高。**
- 由此对 D34 结论的三处**覆盖**：
  1. **范围**：不再是「P0 48 项」或「P1 只做同族 9 项」，而是**对全部 174 个工具逐个给最终名**（含明确的「保留原名」判定）。
     审计中标记的重复实现（`find_node_references` ≈ `search_in_files`、`analyze_signal_flow` ≈ `find_signal_connections`）
     与谎报工具（`export_project`/`bake_navigation_mesh`/`get_test_report`/`clear_output`/`set_auto_dismiss`/`navigate_to`）
     必须在最终表里给出处置（合并 / 下架 / 实现后再注册），不得继续以现在这种名字+行为存在。
  2. **命名形态**：D34 的「单向标记」（只给 24 个游戏侧加 `_in_running_game` 后缀，150 个编辑器侧不加）**被取代**。
     既然长度不是约束，采用**通道前缀**，让**每一个**工具都自证其作用进程/介质，使「这个工具作用在哪」在名字首段即可判定：
     `editor_*`（编辑器进程/编辑场景）、`running_game_*`（运行中游戏进程，经 IPC/端口）、
     `project_*`（项目磁盘：文件、资源、设置）、`os_*`（外部进程/设备）。
     规范形态：**`<channel>_<verb>_<object>[_<qualifier>]`**，先通道后动词；动词取闭集并**废除 `update_`**
     （单属性一律 `set_`；磁盘文件读改写才用 `edit_`）。名字长度以「不看文档即可确定通道+动词+对象」为准，不设软上限。
     例：`simulate_action` → `editor_simulate_action`（因为它在编辑器进程注入，到不了游戏——这正是 D27 的 E3 根因）；
     `monitor_properties` → `running_game_monitor_node_properties`；`search_files` → `project_search_file_names`；
     `search_in_files` → `project_search_file_contents`；`move_node` → `editor_reparent_node`。
  3. **代价必须显式承担——授权判定不能再靠名字前缀猜**（本次改名最重要的架构后果）：
     hof-rs 现在用**名字前缀**判 `MUTATING_PREFIXES` = add_/create_/delete_/remove_/set_/update_/edit_（`src/runtime/policy.rs:184-245`）。
     **一旦名字变成 `editor_add_node` 这种形态，前缀匹配会全面失效** → Tester 会在**大批工具**上静默获得写权限
     （D34 只识别出 `move_node`→`reparent_node` 一个陷阱，通道前缀会让它变成系统性问题）。
     选择（三层防御）：
     - **单一事实源**：最终对照表以机器可读形式落盘（`.spec/godot-mcp-engine/tool-rename-map.json`），
       每个工具带 `channel / verb / mutating / scope / intent / old_name / new_name`；
       策略允许名单**由该表生成**，而不是从名字现场猜。
     - **注册期 lint**（引擎模块 `tool_registry.cpp`）：名字必须匹配 `<channel>_<verb>_<object>...`，
       且声明的 `mutating`/`channel` 必须与名字解析结果一致；不合规即注册失败（构建期就能发现）。
     - **运行期不变式测试**（hof-rs）：对全部工具断言 `is_mutating(new) == declared_mutating`、
       `channel(new) == declared_channel`；并保留 `is_mutating(old) == is_mutating(new)` 的迁移期断言，
       任何权限边界变化必须显式豁免并给出理由（安全断言，不得静默通过）。
- 交付物（缺一不可，落盘在 `.spec/godot-mcp-engine/`）：
  - **`TOOL-NAMING.md`**：最终命名规范（通道/动词/对象/限定词、动词闭集、禁止项、lint 规则、长度判据与例子）
    + **174 行完整对照表**（`old_name | channel | verb | object | new_name | mutating | scope | 处置(改名/保留/合并/下架) | 理由`）
    + 易混淆分组在新名下的消歧说明 + 迁移与影响面清单。
  - **`tool-rename-map.json`**：机器可读，供实现者机械改名与 hof-rs 生成策略使用。
- 回答用户提问：**此前不存在「工具名称对照文档」工件**——174 项审计结果只存在于子代理回报文本中（含其 `rename_map`），
  且其提案形态（单向标记、P0/P1 分批）已被本决策覆盖。因此必须**新产出**上述两个工件，并由决策者冻结后
  才进入 Phase 2 的原子切换。
- 回滚点：两个工件冻结前，任何仓库代码都不动；改名落地时按 D34 的顺序（Phase 0 止血 → Phase 1 规范+lint →
  Phase 2 原子切换）执行，只是范围改为全量。

## D39 — M1 独立验收：**PASS**；缺陷处置与 M1 修正加固包

- 日期：2026-09（阶段五，M1 独立验收）
- 验收方：全新独立子代理 `78058364-2395-453d-a3cc-60fffc69c65b`（未参与实施、未采信数字、自建 PowerShell+Python 客户端、
  产物在 `%TEMP%\m1acc`、**未修改任何文件**）。
- 结论：**pass**。14/14 验收行通过；**实施者可复跑的数字逐个精确复现**（模块 doctest 30/30=172 断言；
  全引擎 `--test` **1456/1456=424453 断言**；`accept_m1.ps1` **17/17 连跑两次**）；未发现伪造。
  独立反例全部通过：D24 响应归属（交错字符串/数字 id、12 个响应值与 JSON 类型全对、零跨连接泄漏）、
  D35 死连接回收（16 条后新请求 28/29 ms）、D36 活连接未被误判 idle（相隔 4 s 的两批流水线 16/16）、
  G4（100 流水线 100/100、mismatches 0）、游戏进程 9889 同一份工具、不带 `--mcp-port` 不监听、
  `Expect: 100-continue` 87 ms 恰好一次、**9877/PID 36392 全程不变**。
- **它抓出我方两个「测试放水」缺陷（产品行为正确）**：
  - **D-1（major）**：`accept_m1.ps1` 的「413 后连接已关闭」断言**恒真**（把读超时当关闭）。它把该惯用法套在一条
    **确定还活着**的 keep-alive 连接上得到 `closed=True`，而同一 socket 18 ms 后仍成功服务请求 → **可复制粘贴的假阴性制造器**。
  - **D-2（major，影响所有后续批次的对等门）**：description 相等性**无法强制**——fixture 双重编码属实
    （独立复核：326390 字节、含 BOM、174/174 复原且反向重编码逐字节相等），而「原始值或还原值任一命中」的兜底
    **会放行一个输出乱码的实现**。
- 其它发现：D-3 未知工具名返回 `-32601`（GDR-6 表述需澄清）；D-4 `HEADER_TOO_LARGE` 应为 **431**（当前 400、431 是死代码）；
  D-5 非法 UTF-8 body 被静默替换并**接受**（边界此前未定义）；D-6 裸 LF 会让客户端静默 30 s；D-7 `id: true` 原样回显；
  D-8「工作树干净」表述不准确（4 个 M0 期未跟踪物、无被跟踪改动）。
  未验证项 U-1..U-5（含：D35/D36 的**反事实** A/B 需回退代码才能复现，已如实保留；「并发 100」实际是
  **≤8 连接上的 100 条流水线**，因 `SocketServer::MAX_PENDING_CONNECTIONS = 8`）。
- 处置（已写入 `DESIGN-DETAIL.md` §14 的 GDR-12..GDR-15）：
  - **GDR-12**：①413 后的关闭必须**正向证明**（不接受读超时当关闭）；②`HEADER_TOO_LARGE → 431`；
    ③裸 LF → **400**；④非法 UTF-8 保留宽松但**写入规范**并加 verbose 警告；`id` 非规范类型宽松回显也写入规范。
  - **GDR-13**：**重采 fixture 为干净 UTF-8**（从 9877 取原始响应字节、正确 UTF-8 写盘、无 BOM），
    对等门**去掉兜底、改为逐字相等**；重采后跑 hof-rs 离线测试确认无回归，并记录新 sha256。
  - **GDR-14**：未知工具名 = `-32601`（与参照实现一致）；`-32001` 专用于**工具内部资源未找到**。GDR-6 表述据此澄清，**不改代码**。
  - **GDR-15**：合入门措辞重述为「≤8 连接上 100 条流水线请求」；`max_requests_per_frame`（默认 8）是**全局每帧预算**，
    **hof-rs 不得假设一请求一帧**；是否改为每连接预算列为 M2 开工前的开放项。
- 选择：**接受 M1**，并在开启 B1/M2 之前派一个**小修正加固包**（范围见下），然后才进入 B1：
  ①修 `case11` 的关闭断言为正向证明；②`HEADER_TOO_LARGE → 431`；③裸 LF → 400；④非法 UTF-8 的 verbose 警告；
  ⑤`accept_m1.ps1` 去掉 description 兜底改为逐字相等；⑥重采 `F:\moonbit-hof-rs\tests\fixtures\mcp\tools_list.json` 为干净 UTF-8
  （该项**授权**该包修改这一个 hof-rs 文件，其余 hof-rs 内容保持只读）。
- 回滚点：修正包只动 `modules/mcp_server/**` 与上述**一个** fixture 文件；两者都可单独回退。
- **修正包已完成（引擎侧 `7d90ae32f4`、`455a08cc13`）**，关键结果：
  - `case11` 的关闭断言改为**正向证明**（`Test-PeerClosed`：优先 FIN/reset，退化为「探针无响应」）；
    修前在**确定活着**的连接上也返回 `closed=True`（原生复现），修后在活连接上 `False`、413/431/裸 LF 后 `TRUE(FIN)`。
  - **431** 落地（含 reason phrase，不再是死代码）；**裸 LF → 400**（新增 `ParseStatus::BARE_LF_LINE_ENDING`，27 ms 内响应，旧行为是静默 30 s）；
    **非法 UTF-8** 保留宽松但新增 `is_valid_utf8` 严格校验 + `print_verbose` 警告（带原始字节长度）。
  - 对等门**删除 Latin-1 兜底**，并改用**大小写敏感**的逐字比较（PowerShell `-eq` 对字符串不区分大小写，原先的"逐字"其实没强制）；
    脚本增至 20 用例（新增 431/裸 LF/非 UTF-8 三例），**连跑两次 20/20 exit 0**。
  - 单测 **33/33（204 断言）**；全引擎 **1459/1459（424485 断言）0 failed**。
  - **fixture 已重采**（GDR-13）：`326390 B / 含 BOM / sha256 be6e0526690cc2460a45b3623cea61667fddbb16d25778e0b85882261a8da6ba`
    → **`48749 B / 无 BOM / sha256 8f8051c4c0f8941089f0b21a193cef7c51fa7c41d7e312b1463ea8593f313c54`**（取 9877 的原始 `tools/list` 响应字节）；
    校验脚本 21 项全过（174 工具、名字与顺序不变、描述为干净 UTF-8、无 U+FFFD、无 Latin-1 残留、191 条嵌套 inputSchema 描述一并修复）。
    hof-rs 离线测试 **261 passed / 0 failed / 7 ignored**（与改动前逐字相同，**无断言被放宽**）。

## D40 — 引擎侧规范工件迁入 Godot fork（用户裁决：文档与代码同居）

- 日期：2026-09
- 用户指令：**「文档放到 godot 目录更合适」**（原位置是 hof-rs 的 `.spec/godot-mcp-engine/`）。
- 先回答用户的核对问题：**M1 的提交确实在 `F:\RustProjects\godot-mcp-pro\code\godot`**——
  分支 `feature/mcp-server-module`，`57277407e7..HEAD` 共 **10 个提交**，改动 **17 个文件且全部在 `modules/mcp_server/` 下（零越界）**，
  工作区仅剩 4 个既有未跟踪物（`.graphifyignore`、`build-m0.cmd`、`graphify-out/`、`install-deps-m0.cmd`）。
- 选择（新的文档归属约定）：
  | 内容 | 位置 | 理由 |
  |---|---|---|
  | 引擎模块的规范与验收工件（需求/概要/详细设计/验收） | **fork `modules/mcp_server/docs/`** | 与代码同居，fork 内自洽；改码与改规范在同一提交里可见 |
  | 跨项目决策日志 `DECISIONS.md` | **hof-rs 仓库** | 记录的是 hof-rs 与引擎模块**共同**的决策树（D30 起为引擎方向、D35–D39 为 M1 实现/验收裁决）；拆开会让「为什么长这样」失去单一来源 |
  | 命名工件（`tool-rename-map.json`、`TOOL-NAMING.md`） | **fork `modules/mcp_server/docs/`** | 与工具实现同居，生成与消费都在引擎侧 |
- 执行：
  - fork 侧提交 `9b6ca0d314`：新增 `modules/mcp_server/docs/{REQUIREMENTS,DESIGN-OVERVIEW,DESIGN-DETAIL,ACCEPTANCE}.md`（逐字节相同，SHA256 已核对）
    与 `modules/mcp_server/README.md`（模块说明、架构要点、构建/测试命令、文档索引、指向 hof-rs `DECISIONS.md` 的说明、当前状态）。
  - hof-rs 侧：`git rm` 上述 4 个文件，`.spec/godot-mcp-engine/README.md` 改为**指针存根**（保留历史路径引用可解析）。
  - fork 内 `__pycache__/` 已被 Godot 自身 `.gitignore:77` 覆盖，无需处理；模块受跟踪文件共 22 个。
- 回滚点：文档搬迁只涉及文档路径；代码与构建不受影响。若要回退，把 4 个文件移回 `.spec/godot-mcp-engine/` 即可。

## D41 — 174 项命名映射产出（数据层）；并纠正「30 条权限漏判」的说法

- 日期：2026-09
- 触发：D38 决定「一次做全 + 通道前缀」，需先产出机器可读映射（数据），再渲染规范文档（表述）。
  D38 的第一次尝试因单代理上下文耗尽失败，**拆解为两步**后第一步完成。
- 交付物：`modules/mcp_server/docs/tool-rename-map.json`（fork 提交 `906b23f16a`）
  - `67826` 字节，sha256 `9f5a57e9201b5f7b0b4929c7562eca3345cc8fa280d63fe1079d4bfae302b91b`，174 条，每条 9 字段
    （`old_name/new_name/channel/verb/object/mutating/scope/disposition/reason`），按 fixture 原始顺序排列。
  - `disposition`：`rename 162 / fix_implementation_first 7 / merge_into 3 / unregister_until_implemented 2 / keep 0`；
    `channel`：`editor 103 / project 45 / running_game 24 / os 2`；`scope`：`editor 103 / both 47 / game 24`。
  - 5 项自检全 PASS（174 计数、与 fixture **双向差集为空**、未合并项名字唯一、lint 谓词、disposition 合法且 reason 非空）。
  - 样例（可读性检验）：`simulate_action` → **`editor_simulate_input_action`**（把「它在编辑器进程注入」写进名字，正是 E3 根因）；
    `monitor_properties` → `running_game_get_node_property_samples`；`move_node` → `editor_reparent_node`；
    `search_files` → `project_search_file_names` vs `search_in_files` → `project_search_file_contents`；
    `find_node_references` → 并入同一新名（merge）；`tilemap_set_cell` → `editor_set_tilemap_cell`（fix_implementation_first）；
    `export_project` → `project_export_game`（unregister_until_implemented）。
  - 语义来源全部为实现（`unconfirmed` 为空）；「24 个走游戏进程」被**精确证实**（19 runtime + 4 test + `get_game_screenshot`）。
- **纠正一个我差点采信的错误说法**：映射生成方报告「现有 `is_mutating()` 漏判 30 条（语义=写但被判只读）」，
  听上去像权限漏洞。决策者用**交集**复核后结论相反：
  - 表结构实为四张：`TESTER_ALLOW_PREFIXES`（9 个前缀）、**`TESTER_ALLOW_EXACT`（16 个精确名，我先前漏看）**、
    `MUTATING_PREFIXES`（7 个）、`MUTATING_EXACT`（22 个）；Tester 权限 = `(allow_prefix ∪ allow_exact) − mutating`。
  - Tester 实际可调用的旧工具 **80 个**；其中「语义可写」的 **15 个**全部是
    `play_scene`/`stop_scene`/`start_recording`/`stop_recording`/`replay_recording`/`click_button_by_text`/`navigate_to`/
    `move_to`/`simulate_{key,mouse_click,mouse_move,action,sequence}`/`run_test_scenario`/`run_stress_test`——
    **它们作用于运行中的游戏或编辑器输入状态，不修改产物**，且 `TESTER_ALLOW_EXACT` 的存在正是为了允许它们取证。
  - 唯一会写 `.tscn` 的 `cross_scene_set_property` **已在 `MUTATING_EXACT` 中**，被拒。
  - 结论：**当前不存在 Tester 权限缺口**。「30 条」是「命名分类器」的统计，不是可达权限；
    `is_mutating` 的语义是「是否修改产物」（`policy.rs:280` 的文案即此），比映射里的 `mutating`（含游戏/编辑器状态）更窄，两者口径不同属正常。
- **真正的风险是改名的后果，方向与「漏洞」相反**：新名字以通道前缀开头（`editor_*`/`running_game_*`/`project_*`/`os_*`），
  `get_/list_/read_/search_/find_/analyze_/detect_/simulate_/assert_` 与 `add_/create_/delete_/remove_/set_/update_/edit_`
  **都不会出现在首段** → 两张表**同时失效**。后果是：
  ①若只更新 mutating 表而不更新 allow 表 → **Tester 被锁死（fail-closed，功能故障而非越权）**；
  ②若为了让 Tester 能用而把 `editor_`/`running_game_` 加进 allow 前缀，而 mutating 侧没有同步改为「按 verb 段判定」，
     **才会**变成真实越权（`editor_set_*` 不以 `set_` 开头）。
  因此 D38 的三层防御必须**同时**落地（JSON 为唯一事实源 + 注册期 lint + 运行期不变式测试），
  且**禁止**用「给 allow 表加通道前缀」这种局部补丁过桥。
- 采纳映射生成方提出的开放项判定（写入本节，实现时照此执行）：
  1. `project_` 与 `editor_` 的边界判据 = **「是否作用于编辑器实时状态」**（`save_scene`→editor；
     `create_scene`/`delete_scene`/`get_scene_file_content`/`cross_scene_set_property`→project；`analyze_scene_complexity`
     主契约是磁盘路径故→project，其「path 为空回退当前编辑场景」写入 reason）。
  2. **merge 必须吸收被合并方的参数**（`find_signal_connections` 的 `signal_name` 过滤、
     `find_node_references` 的扩展名白名单与 addons 跳过策略需被 `search_in_files` 参数化），否则是行为回退。
  3. **7 个 `fix_implementation_first` 在修好前不得以新名注册**；其中 `tilemap_set_cell`/`tilemap_fill_rect`
     **会擦除既有格子却报成功**（数据破坏），优先级最高，必须先写成红测试。
  4. `simulate_*` 的 `mutating=true` 保留（非幂等副作用）；截图类带可选 `save_path` 的条件写保留 `false`，在 reason 中说明。
- 回滚点：映射文件与文档同处 `docs/`，删除即回退；未改动任何代码或策略。

## D42 — 引擎侧后续工件落点与命名工作的拆解教训

- 日期：2026-09
- 落点（承 D40）：`tool-rename-map.json` 已在 `fork modules/mcp_server/docs/`；下一步的 `TOOL-NAMING.md` 同样写进该目录。
- 教训：**「174 项语义重推导 + 写两份大文档」超出单个子代理容量**（第一次尝试上下文耗尽、零产出）。
  拆解为「①只产出 JSON 数据 ②据 JSON 渲染文档」后，第一步一次成功。
  后续同类任务（全量契约变更）一律按「数据 → 表述」拆两步，且要求代理**分批落盘**而非把全表留在自己上下文里。

## D43 — 优先级变更：**优先完成 Godot 侧 MCP 工具集成与测试；hof-rs 暂停**（用户指令）

- 日期：2026-09
- 用户指令：**「优先完成 godot 的 mcp 工具集成和测试，hoh 先暂停」**。
- 含义界定（决策者的解释，供用户纠正）：
  - **暂停**：不再推进 hof-rs 的实现/验收/真实冒烟（`hoh run` 全部停），不改 hof-rs 的代码与测试。
  - **不暂停**：hof-rs 仓库继续作为**决策日志**（本文件）与**契约源**（`tests/fixtures/mcp/tools_list.json`）的宿主——
    两者都是**只读输入**或文档，不算「推进 hof-rs 工作」。引擎侧工件仍按 D40 落在 fork。
- **执行顺序随之简化**（D34 的 Phase 0–5 是为「hof-rs 在线、两侧名字需原子切换」设计的；hof-rs 暂停后该约束消失）：
  1. **引擎内先立规矩**：在 `tool_registry.cpp` 实现命名规范 lint（D38 的谓词：通道前缀正则、verb 闭集、
     声明与名字一致、禁 `update_`），并把 `tool-rename-map.json` 冻结为**唯一事实源**。
  2. **生成「重命名后的期望契约」**：用 `tool-rename-map.json` 机械变换
     `tests/fixtures/mcp/tools_list.json`（旧名 174 条）→ `docs/tools_list.renamed.json`（新名，
     含 merge 项去重、2 个 unregister 项剔除）。这就是**每批对等门的参照物**，且不依赖 hof-rs 运行时。
  3. **按批次移植 + 测试**：B1(42) → B2(25) → B3 → B4 → B5；每批做到
     ①`tools/list` 与期望契约**逐字相等**；②每个工具有成功/缺参/底层失败三类证据；③引擎 doctest 全绿；
     ④全引擎 `--test` 不回归。
  4. **处置项必须落地**：3 对 merge 由保留方**吸收被合并方参数**；2 个 `unregister_until_implemented` **不移植**；
     7 个 `fix_implementation_first` **先修实现（写红测试）再以新名注册**，其中 `tilemap_set_cell`/`tilemap_fill_rect`
     会擦除既有格子却报成功（**数据破坏**）——最高优先级。
  5. **hof-rs 侧的策略重构（授权判定改由表驱动）与产品级验收（E1–E6 真实冒烟）推迟到用户解除暂停之后**；
     届时再做「通道前缀使两张权限表同时失效」的重构（D41 的三层防御）。**在解除暂停前，不得改 hof-rs 的 policy/adapter**。
- 对既定决策的影响：D38（命名一次做全）与 D41（映射）**继续有效且是当前工作的输入**；
  D34 的「Phase 2 原子切换」被本条的引擎优先顺序取代（hof-rs 侧切换合并进将来的解除暂停时刻）。
- 回滚点：本条只是**顺序与优先级**决定，不改任何代码；引擎侧仍只动 `modules/mcp_server/**`。

## D44 — 协作协议变更：**文件化任务书 + 文件化报告**（用户指令）

- 日期：2026-09
- 用户指令：**「后续你与子代理之间的任务下发通过任务书（我给任务书地址）；子代理强制通过任务报告汇报，简洁总结 + 报告地址」**。
- 规定：
  1. **任务书是文件**：决策者把任务书写成 markdown 落到固定路径，**在委派提示里只给路径**（不再把长任务书塞进提示）；
     子代理必须先读该文件再动手。
  2. **报告是文件**：子代理**必须**把完整报告（含真实命令输出与证据）写到指定报告路径；
     返回给决策者的内容**只允许**是「简洁总结（≤15 行）+ 报告路径」。
  3. **落点**（承 D40：引擎侧工件与代码同居）：
     - 引擎侧任务书 → fork `modules/mcp_server/docs/tasks/TASK-<编号>-<slug>.md`
     - 引擎侧报告 → fork `modules/mcp_server/docs/reports/REPORT-<编号>-<slug>.md`
     - 跨项目决策日志 → 仍是 hof-rs `DECISIONS.md`（本文件）
  4. **理由**：①上下文卫生（长任务书与长报告不再占用对话上下文）；②审计链持久（报告随代码入库，可 git 追溯）；
     ③「改动 → 提交 → 决策日志」三者可互查。
- 回滚点：协议本身不涉及代码；若某次委派确实不适合落盘（例如极短的只读核对），可临时口头委派，但**报告仍须落盘**。

## D45 — 命名映射 v1.1 修复决定（采纳独立审计的 D-1..D-8）

- 日期：2026-09（独立审计判定 `fail`：机械层 178 项断言全过，缺陷集中在数据字段）
- 背景：独立审计（全新子代理，自写脚本、未采信生成方结论）结论为
  **机械层全对**（字节/sha256/条数/字段/双向差集/命名谓词/四组计数逐项精确复现，39 个函数体行号与映射引用全吻合），
  但**数据正确性有 3 类缺陷**（2 major + 1 minor）+ 5 个 minor/nit。
- 逐条裁决：
  - **D-1（major，权限相关）采纳并取保守解**：`editor_capture_screenshot`（旧 `get_editor_screenshot`）与
    `running_game_capture_screenshot`（旧 `get_game_screenshot`）声明 `mutating=false`，但 `save_path` 非空时**真的写 PNG 落盘**
    （`editor.rs:327-343` / `:395-402`，schema 文案明确允许 `res://`）→ **两行改为 `mutating=true`**，
    并在 `reason` 写明「条件写：save_path 非空即落盘」；`convention` 增加**条件写**条款
    （凡「默认只读、参数可触发落盘」的工具一律按最保守语义记 `mutating=true`）。
  - **D-2 / D-3（major，能力丢失）采纳其事实，但结论改为「取消这两对合并」**：
    审计实测两对 merge **都不无损**——
    `search_in_files ⇐ find_node_references`：输出形状（逐行 `{file,line,text}` vs 按文件聚合 `{file,lines[]}`）、
    上限 **50 vs 100**、**大小写不敏感 vs 敏感** 三项不等价；且 D41 原先声称要吸收的「扩展名白名单/跳过 addons」**指错了**
    （保留方扩展名是超集，两者都已跳过 addons）。
    `analyze_signal_flow ⇐ find_signal_connections`：除已知的 `signal_name` 外，还差**4 项**——
    返回形状（按节点嵌套 vs 扁平 `connections[]`）、**非持久连接过滤**（`flags & 1`）、
    **编辑场景之外的 target**、`node_path` **子串 vs 精确**匹配。
    → **决定取消这两对合并，两两保留为独立工具并给可区分的名字**（用户的诉求是**区分度**而非工具数少；
    名字变长不是约束，能力丢失才是代价）。保留的唯一无损合并是
    `get_performance_monitors ⇐ get_editor_performance`（审计逐字段核验其为子集，**成立**），
    该对仍合并，但 reason 必须写明「形状由平铺改嵌套」。
  - **D-4（minor）采纳**：`disposition` 改为**枚举**（`rename | keep | merge_into | unregister_until_implemented |
    fix_implementation_first`），合并目标新增独立字段 **`merge_target`**（= 保留方的 `old_name`），
    使「精确匹配」的消费者可判定。
  - **D-5（minor）采纳**：`convention` 补齐值域声明 `disposition_enum`、`scope_enum`，并显式写明
    **`mutating` 的口径**（含游戏/编辑器状态副作用，共 101 条）与 hof-rs `is_mutating`（仅「是否改产物」，`policy.rs:280`）
    **不是同一谓词**——**禁止把前者直接灌进 `MUTATING_EXACT`**（会把 15 个合法取证工具一起拒掉，fail-closed 回归）。
  - **D-6 / D-7 / D-8（nit）采纳**：修正三处引文失真（`navigate_to` 的 gd 实际文案、
    `get_project_info` 的 reason 误提 DirAccess、`move_node` 未体现可选 `new_name` 副作用）。
- **工具数变化**：`174 − 2（unregister） − 1（保留的无损合并） = **171**`；
  因此 B0 生成的 `docs/tools_list.renamed.json`（原 169）与 `docs/TOOL-NAMING.md`（其头部硬编码了 JSON 的字节数与 sha256）
  **必须一并重生成**，否则契约与文档失效。
- 另记两条口径提醒（不属缺陷但必须在实现期遵守）：
  1. `convention.verb_closed_set` 的 37 项**只有内部一致性**（上游 D38/D41 只点名 16 个），
     其中 `evaluate` 用量为 0 → 下一版 convention 决定「移除」或「保留并说明」。
  2. 若注册期 lint 用「verb 段推 mutating」，审计实测 **3 处误判**
     （`project_convert_uid_to_path`/`project_convert_path_to_uid` 的 `convert` 非写、`editor_open_scene` 的 `open` 属写）
     → 需要**对象/scope 感知的豁免表**，不能只靠动词闭集。
- 回滚点：映射与契约都是数据文件，恢复旧版即回退；本条不改任何引擎源码。

## D46 — 映射 v1.1 通过独立验收；B1 采用「框架先行 + 按组并行」结构

- 日期：2026-09
- **验收结果（全新子代理，独立复算 + 自读源码 + 对抗性反例）：`pass`**
  - D-1..D-8 **8/8 闭合**；**无新缺陷**（仅 2 个 nit）；
  - 三件工件指纹自行重算全部相符（`70917 / 2f552719…`、`95060 / 96495bad…`、`98381 / 078b94e5…`）；
  - 计数独立复算全对：`disposition` `rename 164 / fix 7 / merge_into 1 / unregister 2`、通道 `103/45/24/2`、
    `mutating=true` **103**；契约 171 条；两个取消合并的新名各 1 条且不泄漏；
  - 生成器**幂等**且逐字节复现落库件；`TOOL-NAMING.md` 174 行逐字段对账 **0 不一致**，无 v1.0 残留；
  - 工程门自跑：doctest **39/39**、全引擎 **1465/1465（0 failed）**、`accept_m1.ps1` **连跑两次 20/20**；9877 全程 PID 36392 未受影响；
  - 抽样 26 条（4/4 通道、7/7 fix、2/2 unregister）对回源码 **0 处失真**。
- **纠正我自己的一处笔误（nit N-2）**：D45 里写 `mutating` 「共 101 条」是**改动前基线**，v1.1 实为 **103**
  （101 + 两个截图工具按 GDR-18 改保守值）。
- 处置验收提出的 2 个 nit 与 6 条风险：
  - **N-1**：`TOOL-NAMING.md` 的 `disposition` 单元格被生成器渲染成「`merge_into`→目标」而非纯枚举值 →
    改 `docs/scripts/gen_table.py` 输出纯枚举（或加列说明），重渲染并更新文档指纹。**归入 TASK-002**。
  - **N-2**：本节已纠正。
  - **R-1/R-2/R-3（消歧仍需一句话）**：`editor_analyze_signal_flow` ⇄ `editor_list_signal_connections`、
    `project_search_file_names` ⇄ `project_search_file_contents`、`project_convert_uid_to_path` ⇄ `project_convert_path_to_uid`
    这三对**光看名字仍不足以可靠二选一** → 必须在各自 **`description` 内联一句判别点**
    （返回值形状 / 上限 / 大小写 / 过滤规则）。**归入 TASK-002（映射 v1.2）**。
  - **R-4（全量门缺口）**：`accept_m1.ps1` 的逐字对等门**只比较已实现的 2 个工具**（`$ToolNames`），不是 171 条全量。
    → ①立即在 SUMMARY 打印「已实现 N / 契约 171」并标 `known_deviation`，避免把批次门误读为全量门；
      ②**171 条全量逐字对等门排进 B5 收口**（编辑器与游戏两端点各跑一次全量集合相等 + 逐工具逐字相等 + 无多余工具）。
  - **R-5**：映射 `reason` 里的源码引用指向**迁移源**（`godot_mcp_gdext`/`addons/godot_mcp_rs`），随 C++ 重写会过期 →
    每批移植时**同步刷新该批的 reason 引用为 `as-built` 位置**。
  - **R-6**：映射 `mutating`（103，含状态副作用）与 hof-rs `is_mutating`（仅产物）口径不同，
    hof-rs 侧的不变式测试**随暂停推迟**（解除暂停时按 D41 三层防御落地）。
- **B1 架构决定（本条的实质内容）**：B1 = **42 个旧工具 → 41 个注册**
  （`get_editor_performance` 已被无损合并进 `editor_get_performance_monitors`，不单独注册）。
  41 个 C++ 实现超出单个子代理容量（且 TASK-001 已证明单代理做「大批量 + 多文档」会上下文耗尽），
  因此 B1 采用**两阶段结构**：
  1. **框架先行（TASK-002）**：①registry 按组分文件 + 每组一个 `register_<group>_tools(registry)`，
     共享注册表只按组调用（消除并行改同一文件的冲突）；②统一的工具编写助手
     （`ToolDef` 构建、参数校验、成功/缺参/底层失败三类错误封装、`scope` 过滤）；③移植**模板组**证明模式可行。
  2. **按组并行（TASK-003a/b/c…）**：每个子代理只拥有自己的 `tools/<group>.{h,cpp}` 与**一行**注册调用。
  - **模板组定义（机器可派生，避免歧义）**：`B1 ∩ channel=project ∩ mutating=false`（工程只读族）。
  - **每批/每组对等门（四道，逐字）**：①该组的 `tools/list` 与该组在 `tools_list.renamed.json` 中的子集
    **逐字相等**（name/description/inputSchema）；②每个工具**成功 / 缺参 / 底层失败**三类证据；
    ③引擎 doctest 全绿；④全引擎 `--test` 零回归（基线 1465，仅允许因新测试而增加）。
  - **禁令**：不得为让门变绿而提前注册未实现工具；不得注册 2 个 `unregister_until_implemented`；
    7 个 `fix_implementation_first` 必须**先写红测试再修实现**（B1 内的 `clear_output` 适用此条）。
- 回滚点：框架改动限于 `modules/mcp_server/tools/**` 与 `tool_registry.*`；模板组可单独回退。

## D47 — TASK-002 交付（B1 框架 + 模板组 + 全 B1 分组 + 映射 v1.2）与 9 条偏差裁决

- 日期：2026-09
- **交付（4 部分全部完成，4 个引擎侧提交）**：
  1. **预备**：映射 **v1.2** —— 为 R-1/R-2/R-3 的 7 个易混工具在契约 `description` 里**内联判别点**
     （逐条从迁移源码读出，登记在 `gen_renamed_contract.py` 的 `DESCRIPTION_OVERRIDES`，`_meta.overrides` 可查）；
     修掉生成器「一填 override 就 FATAL」的既有缺陷并加 append-only 自检；
     **nit N-1**（`disposition` 改纯枚举 + 174 行回归护栏）、**nit R-4**（`accept_m1.ps1` SUMMARY 打印
     「已实现 6 / 契约 171」并标 `known_deviation`）。
  2. **框架**（已写入 `DESIGN-DETAIL.md` **§17 / GDR-19**）：`tools/` 按组分文件，共享入口只剩
     `register_all_tools()`（每组一行）；`MCPTools::ToolBuilder` **强制显式声明** `channel/verb/scope/mutating`；
     参数校验 `require_*`/`optional_*` → `-32602`；结构化 `MCPToolError`
     （`-32602` / `-32001`（带 `data.suggestion`）/ `-32000` / `-32603`）；磁盘助手 `normalize_project_path`
     （只允许 `res://`、禁 `..` 与空段）等。
  3. **模板组（决策者指定的 6 个工具）**：`project_get_info`/`project_get_settings`（迁移，`tools/list` 逐字不变）
     + `project_get_filesystem_tree`/`project_search_file_names`/`project_search_file_contents`/
     `project_find_files_referencing_symbol`（新实现）。后两者是**取消合并后的两个不同实现**——
     同一工程同一输入实测 **3 命中 vs 0 命中**，GDR-17 得到直接检验。
  4. **全 B1 组清单** `docs/tool-groups.json`：**41 个工具 / 7 组**，机器校验「恰好各出现一次」PASS；
     7 组是「一组一通道一读写 + 组 ≤10」约束下的算术下界（B1 = 23 project + 17 editor + 1 running_game）。
- **工程门（实现方自跑，待 TASK-AUDIT-002 独立复核）**：doctest **53/53（410 断言）**（红阶段抓到 2 个真实缺陷）；
  全引擎 **1479 passed / 0 failed / 3 skipped**（基线 1465 + 14）；
  `accept_m1.ps1` **21/21 连跑两次**；`check_contract_subset.ps1 -Group project_read_template` 在
  **9888 与 9889** 逐字 **6/6**；9877 全程 PID 36392 未受影响。
- **9 条偏差的裁决（全部接受，理由如下）**：
  1. path 不存在返回 **`-32001` 带 `data.suggestion`**（参照实现是**静默空结果**）→ 接受：
     静默空结果会让智能体把「路径写错」误判为「没有命中」，符合 GDR-14 的语义。
  2. `optional_*` 对「存在但类型错」返回 **`-32602`**（参照实现静默忽略）→ 接受：
     静默忽略参数是误配置的主要来源。
  3. `TOOL_ENABLED` → **`MCP_EDITOR_TOOLS_ENABLED`**（经全树 grep 确认本 fork 只有 `TOOLS_ENABLED`）→ 接受：
     **是我任务书写错了宏名**，实现方的等价替换正确。
  4. 新增 **GDR-19/§17** 到 `DESIGN-DETAIL.md` → 接受（框架落点需要成为规范，否则下一批会照着过期规范写）。
  5. 组数 **7**（我建议 4–6）→ 接受：算术下界，非风格问题。
  6. 三个工具「三类证据」中有一类**不可构造**（`project_get_info` 无参数、部分工具无底层失败路径）→ 接受，
     但要求后续每组在报告里**显式声明哪一类不可构造及原因**（不得用「已覆盖」含糊过去）。
  7. `DESIGN-DETAIL.md` 的 §1 布局与 §7 `ToolDef` 片段同步更新 → 接受。
  8. 工作树里 `TASK-002` 任务书处于 modified（我在派发后又收窄了模板组）→ 由决策者提交（已提交 `74d565f24d`）。
  9. 证据脚本首版因「JSON body 作为 Windows 命令行参数丢引号」全返回 `-32700`，改用 `--data-binary @file` →
     接受，并作为**后续任务书的强制写法**（D48 起写入模板）。
- 回滚点：框架与模板组可整组回退；`docs/tool-groups.json` 是数据文件。

## D48 — 并行纪律修正：**实现组必须串行**（子代理共享同一工作树）

- 日期：2026-09
- 触发：D46 我曾写「按组并行（TASK-003a/b/c…）」。但本会话的子代理**共享同一个工作树**（无隔离），
  而所有组都必须修改 **同一处** `tools/registration.cpp` 的 `register_all_tools()`；
  两个子代理同时「读-改-写」同一文件会产生**丢失更新**，且中途不可编译的工作树会让任何一方的门失败。
- 决定：**实现批次一律串行**（一次只有一个实现子代理在改树）。
  - 「分组」的真正价值不变：它让**每个任务的范围明确、可独立验收、失败可精确回退**，
    并让未来的真并行（独立工作树/分支）成为可能；
  - 顺序按 `docs/tool-groups.json` 的风险与依赖排序（先只读、后写；`editor_write_scene_editor` 因含
    `fix_implementation_first` 的 `editor_remove_output_log` 而必须**先写红测试**，排在最后处理）；
  - 每组的收口固定为：`check_contract_subset.ps1 -Group <组名>`（9888+9889 逐字）→ doctest → 全引擎 → 三类证据。
- 附：**任务书模板**新增两条强制项（源自本轮经验）：①证据采集一律用 `--data-binary @file`；
  ②报告里必须显式声明「三类证据中哪一类不可构造及原因」。
- 回滚点：纯流程决定，不涉代码。

## D49 — TASK-AUDIT-002 通过；5 个缺陷裁决 + 框架加固

- 日期：2026-09
- **验收结果：`pass`**（四维分开判定全过；基准 HEAD `74d565f24d`，工作树无 modified）
  - 独立复现 15 项：4 个指纹相符；174 行表逐字段 0 不一致；41 工具双向差集为空且**等价于「§10 的 42 旧 − `get_editor_performance`」**
    （验收方自行从设计文档抽 42 token 再经映射换算，集合完全相等）；
  - **`ToolBuilder` 违规实测**：自造 16 组合探针 → **15/15 缺项组合被拒**、缺项名逐项入 reason、完整声明通过；
  - **`normalize_project_path` 22 条自造反例无逃逸**（项目外文件从 `res://` 搜不到）；
  - 两个取消合并工具的差异**独立复现**（形状、大小写、上限 50 vs 100、每文件 ≤5 行）；
  - 7 条判别点逐条对回源码为真；四对二选一裁决**全部「够」**；
  - 四道门自跑一致：doctest 53/53（410）、全引擎 1479/0/3、accept 21/21 ×2、subset 在 9888+9889 各 6/6；9877 PID 36392 未变。
- **D-1 裁决：`tools/list` 的**顺序不是契约语义**（MCP 客户端不得依赖顺序）。**
  - 契约 `_meta` 增 `order_normative: false`；`DESIGN-DETAIL` 写明「顺序非规范，但引擎必须**确定性**（同一次构建内重复调用逐字节相同）」；
  - B5 的**全量门**定为「**集合相等 + 逐工具逐字相等（name/description/inputSchema）+ 无多余工具**」，**不含顺序**；
  - 加一条 doctest 证明 `tools/list` 的输出**确定性**（连续两次调用逐字节相同）。
- 其余 4 个缺陷的裁决：
  | 缺陷 | 裁决 |
  |---|---|
  | **D-2**（实现方报告称「同一输入 3 vs 0 命中」，实测为 **3 vs 1**；机制对、叙述错） | 接受为**叙述错误**，不涉代码；在 `REPORT-002` 追加**勘误段**（保留原文以免掩盖），并在本日志记录 |
  | **D-3**（`accept_m1.ps1` 的 SUMMARY 因 `+` 与 `-f` 优先级打印字面 `{0}/{1}`） | **修**（加括号）；修后须实测打印 `6` 与 `171` |
  | **D-4**（`normalize_project_path` 不折叠 `.` 段：`res://.`、`res:// `、`res://src/.` 均通过；无安全影响） | **修**（折叠 `.` 与单空格段），加 doctest |
  | **D-5**（`TOOL-NAMING.md` 有 1 行 reason 含未转义 `\|`，使该行按 `\|` 切列得 10 列） | **修生成器**（渲染前转义 `\|`），重渲染并对**全部 174 行**断言「恰好 9 列」 |
- **框架加固（采纳验收方的两条机制性建议）**：
  1. `MCPToolRegistry::register_tool` 目前 **public**，可绕过 `ToolBuilder` 的命名 lint / `mutating` 声明 / 编辑器守卫 →
     改为**只能经 `ToolBuilder` 注册**（私有化或等价的编译期/运行期强制），并加一条测试证明「绕过路径不可用」。
  2. **所有组必须经 `ToolBuilder` 注册**写入任务书模板（`DESIGN-DETAIL` §17.2 同步）。
- **并行安全的实证（强化 D48）**：验收方在 `%TEMP%` 用 `git merge-file` 模拟两个子代理各加一行注册 →
  **exit=2、4 个冲突标记**。故 D48 的「实现批次串行」得到直接证据支持；任务书模板再加一条：
  **注册行由该批实现者单独追加，且一批只有一个实现者在改树**。
- 其余风险（记录不修）：真实游戏进程下 `scope=EDITOR` 的端到端不可见性**本轮无法验证**
  （B1 无 EDITOR 工具，9889 过滤平凡成立）→ 留到 B3（`editor_write_scene_editor` 组）落地时补端到端证据；
  `editor_screen_size` 在游戏进程走 `SceneTree` 回退（64×64）而非参照的 `{0,0}`——**早于 TASK-002 存在**（M1 同段代码），非本轮回归。
- 回滚点：本节只裁决与排期；实际改动由 TASK-003 承担。

## D50 — TASK-003 通过独立验收；落地「组移植手册」+ 3 条口径裁决

- 日期：2026-09
- **TASK-AUDIT-003：`pass`**（机械/行为/工程三向全绿），关键实测：
  - **绕过路径确实不可用**：模块内 `.register_tool(` 唯一调用点 `tools/tool_builder.cpp:143`；
    把声明**改回 public 后重新编译失败**（`error C2338: static_assert ... register_tool is public again`，exit 2），
    并已**逐字节还原**（7662 B / `2a55e68d…` 与变异前相同，`git status` 干净，重建 exit 0）。
  - `normalize_project_path`：**30 条自造反例**在线实测，16 条 `-32602`（7 条含 `..`、9 条缺 `res://`），
    14 条折叠，**逃逸/格式违规 0**；`res://a/./../b` 仍在折叠前被拒。
  - D-1 落地：`_meta.order_normative=false`；**跨进程重启**两次 `tools/list` 逐字节相同（sha `a726b11a…`）。
  - D-3：accept ×2 各 21/21，SUMMARY 实测打印 6/171，`{0}`/`{1}` 字面量 0。
  - D-5：验收方独立核实——`\|` 转义在 HEAD~2 **早已存在**，**我的任务书诊断确已过时**；
    实现方的正确读法是「按**未转义** `|` 切分」并断言「裸 `|` 只出现在 `get_project_info` 的 reason 里、共 1 处」。
  - 新缺陷 4 条全为 low/info：`REPORT-002:194` 注释过期（已排入 TASK-004）、
    `static_assert` 绊线只在 `tests=yes` 构建里（**可接受**：语言级 private 在任何构建都挡得住）、
    空段折叠属已批准的行为放宽、D-5 诊断过时。
- **签字（决策者裁决，采纳）**：
  1. **D-A-4 空段折叠**：`res://a//b` 由 `-32602` 改为折叠 → **接受**（安全边界不变，`..` 仍拒）。
  2. **D-A-2 D-5 读法**：按「未转义 `|`」切分 + 断言裸 `|` 归属唯一 → **接受**；
     **不**改写映射 reason（否则映射 sha → 文档指纹 → 契约 `_meta.map_sha256` 全线漂移，收益不抵成本）。
  3. **D-A-3**：`static_assert` 绊线只在测试构建 → **接受**（可选增强，不阻塞）。
- **新增流程工件：`docs/tasks/PLAYBOOK-group-port.md`（组移植手册）**——把 B1→B5 每一组的共同规范
  （8 步工作流、**五道门**、报告格式、硬性约束、6 条已知偏差）固化一次；此后每组任务书只写「组名 + 成员 + 组特有注意」。
  这样做的直接收益：①决策者不再为 5 个剩余组重复长篇任务书；②组与组之间**门与偏差口径一致**，
  不会出现「这组按旧口径、那组按新口径」；③把「已知偏差」从散落的裁决变成执行者**必须沿用**的输入。
  手册的门④新增「`accept_m1.ps1` 连跑两次」，并把审计建议的「`tools/list` **跨进程重启**一致」并入。
- **三条口径裁决（写入手册 §6，避免后续组重复争论）**：
  1. 映射 `reason` 的源码引用**指向迁移源**（`godot_mcp_gdext`/`addons`），**不因 C++ 重写而改写**；
     **as-built 位置写进各组报告**即可（R-5 由此闭合，且避免 sha 漂移）。
  2. 因无法在 9877（用户正在使用的编辑器）上驱动迁移源做**在线 golden 对比**，
     每组的「响应形状对等」以「**逐工具写出迁移源的可观察契约 + C++ 落点 + 差异声明**」代替在线对比，
     差异必须显式列出（这是诚实的替代证据，不是省略）。
  3. `tools/list` **顺序非规范**、内容逐字是规范；游戏端点 9889 只暴露该组中 `scope` 允许的工具。
- 回滚点：手册与裁决均为文档；TASK-003 的代码改动可整提交回退。

## D51 — TASK-004 交付与裁决；**验收粒度改为里程碑级**

- 日期：2026-09
- **TASK-004（组 `project_read_analysis`，7 个只读工具）交付**，五道门全绿：
  门① 契约子集（编辑器 9888 + 游戏 9889）**7/7 逐字**；门② 24 例 `curl --data-binary` 真实证据（双端点）；
  门③ doctest **65/65·607**（TDD 红阶段 11 failed 有据）；门④ 全引擎 **1491/1491·0 failed**；
  门⑤ `accept_m1.ps1` **22/22 连跑两次**（新增 `case20` 跨进程重启一致性，**四次独立进程 sha 恒为 `94ea9978…`**）。
  TDD 顺序正确（先红后绿），只读性由 doctest 固定（7 个工具调完后 fixture 文件列表逐字节不变）。
- **三条实测偏差的裁决（全部接受，均为「迁移源本身有缺陷」）**：
  1. **`project_get_scene_exports` 的导出过滤被重写**：迁移源用**字面量 1024** 判导出，
     而本 fork 的该位是 `PROPERTY_USAGE_NO_INSTANCE_STATE`（`PROPERTY_USAGE_SCRIPT_VARIABLE` 是 `1<<12`），
     **恒返回 `count:0`**；且编辑器进程里节点的合并属性列表**不带** `SCRIPT_VARIABLE`（实测 `usage=6`）。
     → C++ 版改读 `Script::get_script_property_list()` 并以 `PROPERTY_USAGE_EDITOR` 判定，两进程结果一致。
     **接受**：这与 D45 对「谎报工具」的立场一致——**工具必须真的能用**，不得为「与参照逐字一致」而复刻坏行为。
  2. **`project_analyze_scene_complexity` 的编辑场景回退改用 `SceneTree::get_edited_scene_root()`**：
     `EditorInterface` 版本**无 null 检查、在 doctest 进程实测 SIGSEGV** → **接受**（消除崩溃路径），
     编辑器专有性仍由 `MCP_EDITOR_TOOLS_ENABLED` + `is_editor_process()` 双层守卫；游戏进程无 `path` 时返回 `-32000`+建议。
  3. **`check_contract_subset.ps1` 语义被修正**：原版要求实况 `tools/list` 等于**单个组**的集合，
     在第二个组落地后必然失败（实测 actual=13 vs expected=7）→ 改为对照 `tool-groups.json` 中
     **所有 `implemented=true` 组的并集**（并保留「未实现却已注册即失败」的额外检查）。
     **接受**，并已写入 `PLAYBOOK-group-port.md` §3 门① 的新语义（后续每组共用）。
- **其余 10 条偏差**：路径归一后回显、`-32001`/`-32602` 口径、确定序替代 `HashMap` 迭代序、
  保留迁移源怪癖（`get_scene_dependencies` 的 `type` 恒空串）——均**接受**，
  其中前两类已进手册 §6，后两类新增为手册 §6 第 7/8 条。
- **手册与规范更新**（本回合已落盘）：
  1. `PLAYBOOK` §3 门① 改为**并集语义**；
  2. `PLAYBOOK` §6 新增第 6/7/8 条：**迁移源有缺陷时以「工具真的能用」为准并显式记录**（含上述两个具体案例）、
     路径归一后回显、非确定行为改确定序但保留怪癖；
  3. 编辑器进程「合并属性列表不带 `SCRIPT_VARIABLE`」这一**陷阱**写入手册（`editor_*` 组会再遇到）。
- **框架清理排期**：TASK-004 在组文件里重复实现了 4 个小助手（`_split_lines`/`_serialize_variant`/`_join_path`/扩展名遍历），
  原因是组文件内部链接的助手无法跨文件复用。→ 排入 **TASK-005 第一部分**：上提到 `tools/tool_builder.h`，
  两个已有组改用共享助手，并**证明重构前后响应逐字节相同**（否则后续 4 个组会把重复成倍放大）。
- **⭐ 验收粒度改为里程碑级（重要流程裁决）**：
  - 原因：TASK-001/002/003 每个小任务都派了独立验收（各占一个完整子代理周期）。
    在「剩余 5 个 B1 组 + B2（25 工具）+ M3/M4/M5」的体量下，逐任务验收会把周期耗尽在验证上；
    而**方法论基础（映射 v1.1/v1.2、框架、路径安全、单注册路径）已被三轮独立验收覆盖**，风险已从「基础错」转为「组实现错」。
  - 新规则：**每组仍必须自己跑五道门**（这是硬性交付条件），但**独立验收改为里程碑粒度**——
    即 **M2（B1+B2 全部落地）后派一个全新子代理做里程碑级独立验收**，
    覆盖：全量 171 条契约中「已实现并集」的逐字对等、跨组一致性、响应形状与迁移源可观察契约的对照抽样、
    五道门复跑、以及随机/边界反例。若里程碑验收判 fail，按缺陷清单回到实现方修，再派**又一批全新**验收。
  - 保留例外：**涉及安全边界或基础契约的改动**（如 `register_tool` 可见性、路径归一、契约/映射本身）仍走即时独立验收。
- 回滚点：D51 只改流程与手册；TASK-004/005 的代码改动各自可整提交回退。

## D52 — TASK-005 交付；两起真实事故转化为纪律；`size` 单位裁决

- 日期：2026-09
- **TASK-005 交付**（第一部分框架清理 + 第二部分组 `project_read_files` 6 工具）：
  - **助手去重**：4 个重复助手（`join_path`/`split_lines`/`serialize_variant`/`collect_files_by_extension`）
    上提到新共享头 `tools/tool_helpers.{h,cpp}`，两个已有组改用共享实现；
    **重构等价性有据**：验收方独立重建重构前后两个提交，13 条 `tools/list` 响应**逐字节相等**（sha `d94a75f3…`）。
  - 五道门：门① 契约子集（`implemented_union=19`）**6/6 逐字**；门② 编辑器 21 例 + 游戏 21 例**逐字节相同**；
    门③ doctest **73/73·726**（基线 65/607）；门④ 全引擎 **1499/1499·0 failed**（基线 1491/424888）；
    门⑤ `accept_m1.ps1` **22/22 连跑两次**（`case20` tools=19 逐字节一致）。
  - 该实现者**自带了一轮嵌套独立验收**：首轮判 `fail`（证据管道缺陷），勘误后第二轮 `pass`、defects 为空。
- **两起真实事故 → 已写入 `PLAYBOOK` §7（纪律补强）**：
  1. **证据采集禁止用 `Out-File`/管道承载响应体**：一版 `tools/list` 证据经 `Out-File -Encoding ascii` 被污染
     （每个非 ASCII 字符塌成 `?`、字节数记为错值 3411），**直接导致独立验收判 fail**。
     → 一律 `curl.exe -s -o <file>` 或用 `[IO.File]::WriteAllBytes`，比较前先算 sha256。
  2. **实现者不得创建竞争性规范文档**：`docs/spec/TASK-005/`（37 KB 的 REQUIREMENTS/DESIGN-OVERVIEW/DESIGN-DETAIL）
     与规范 `docs/DESIGN-DETAIL.md` 重复，**已删除**；规则入库：**规范由决策者维护，实现者只写报告**，
     认为规范有误就在报告里报缺陷。
  3. 附：**证据被证伪要显式撤回**（该实现者撤回了不可复现的「`--import` 崩溃」主张）——append-only 勘误是允许且被鼓励的。
- **`size` 单位裁决（手册 §6 新增第 9 条）**：迁移源（Rust）用**字节数**（`String::len()`），
  C++ 版用 `String::length()` 会得到**字符数** —— 属不必要的偏离。
  → **除契约明确写字符数，一律返回 UTF-8 字节数**；已实现的 `project_read_script` /
  `project_read_scene_file_content` 的 `size` 排行入 **TASK-006 顺带修**。
- 其余偏差裁决（接受）：`$ToolNames` 13→19 同步、`tool-groups.json` 的 `implemented` 置位、
  `project_validate_script` 增加 `ScriptServer::are_languages_initialized()` 守卫
  （迁移源无守卫、实测对好脚本给**假阴性** `err 36`；doctest 退化为结构检查并**明确声明「未编译」**，
  而非假通过）、`_error_identifier` 手写映射、`project_get_resource_preview` 三条语义收紧、
  `project_list_scripts` 两类证据语义上不可构造（已显式声明）、红阶段临时 SPIKE 探针在绿阶段删除。
- **B1 进度**：`project_read_template`(6) ✅ / `project_read_analysis`(7) ✅ / `project_read_files`(6) ✅ →
  已实现 **19 / 41**；剩余 `editor_read_scene_inspector`(7)、`project_write_resource_scene`(4)、
  `editor_write_scene_editor`(10)、`running_game_read_scene`(1)。
- **TASK-006 的关键价值**：它是**第一个 `scope=editor` 的组**，因此可以补上一直被记为 unverifiable 的
  「游戏进程不暴露编辑器工具」**端到端**证据（9889 的 `tools/list` 必须不含本组工具；
  并构造一次「游戏进程调用编辑器工具」的请求，必须被拒且不执行）。
- 回滚点：TASK-005 的代码改动可整提交回退；手册/裁决为文档。

## D53 — TASK-006 交付（首个 editor-scope 组，补上端到端守卫证据）；契约描述缺陷裁决

- 日期：2026-09
- **TASK-006 交付**（组 `editor_read_scene_inspector`，7 个编辑器专有只读工具；B1 进度 **26/41**）：
  - 五道门：门① **3/3**；门③ doctest **78/78·995**（红阶段 7 failed/62 断言有据）；门④ 全引擎
    **1504/1504·0 failed**；门⑤ `accept_m1.ps1` **22/22 连跑两次**（PASS 清单逐字节相同）；
    门② 双端点真实证据（4 个不可构造类已显式声明）。
  - **补上了一路被记为 unverifiable 的端到端守卫证据**（本组是第一个 `scope=editor` 组）：
    编辑器 9888 = **26** 个工具（本组 7 个逐字 True）；游戏 9889 = **19** 个工具且本组 7 个**全部缺席**；
    **游戏进程调用 `editor_get_errors` → `-32601 Method not found` 且未执行**；
    编译期守卫（所有编辑器 API 调用点都在 `MCP_EDITOR_TOOLS_ENABLED` 区间内）与
    运行期守卫（`hint=true` 但无 `EditorNode` 时返回 `-32000` 而非 SIGSEGV）均有证据。
  - 门脚本按端点语义修正（第二个组落地后原「单并集」语义必然误报）→ **接受**，并排入 TASK-007 §2 写进 `DESIGN-DETAIL` §17.3。
  - 其余偏差接受：`inputSchema` 从契约字面量解析（Godot JSON 只有一种数字类型，整型默认值解析后需折回 `INT`——
    **门① 真的抓到了这一点**，报告附录保留了抓到的过程）、红阶段退出码未采（用 `Status: FAILURE!` + 62 断言失败作证，
    **不为凑数字重跑红树**——这是好习惯）、`editor_get_selection` 非空选区样本推迟到 B3、
    `editor_get_scene_tree` 保留迁移源的编辑器内部路径怪癖（手册 §6.8）。
- **⭐ 契约描述缺陷裁决（用户最在意的「描述必须与功能对应」）**：
  - 问题：`editor_analyze_signal_flow` 的契约描述写「按 `flags & 1` 判持久连接」，
    但 **Godot 4 里 `CONNECT_DEFERRED = 1`、`CONNECT_PERSIST = 2`** → 照字面实现会让普通场景**恒返回 `nodes: []`**。
    TASK-006 的实现按**意图**用了 `CONNECT_PERSIST`，但**没有自行改契约**（正确做法），只报缺陷请决策者裁定。
  - 裁决：**描述必须改对**（这正是 D38/D45 那条「名字与描述必须与功能对应」的延续）。
    做法：走 `gen_renamed_contract.py` 的 **`DESCRIPTION_OVERRIDES`**（理由入 `_meta.overrides`），
    **不改 `tool-rename-map.json`**（避免映射 sha 漂移），并**同步 C++ 侧描述字面量**（否则门①会失败——这正是门①的价值）。
    排入 **TASK-007 第一部分**。
  - 附注：这是**第 2 例**「迁移源本身有缺陷、必须偏离参照」的案例（第 1 例是 `project_get_scene_exports` 的恒 `count:0`），
    手册 §6.6 的规则（以「工具真的能用」为准并显式记录）已被两次实证验证。
- 回滚点：契约描述改动可由生成器 revert（`DESCRIPTION_OVERRIDES` 单条）；组实现可整提交回退。

## D54 — TASK-007 交付（首个写组）；契约描述已改对；第 3 例迁移源缺陷

- 日期：2026-09（B1 进度 **30/41**；剩余 `editor_write_scene_editor`(10)、`running_game_read_scene`(1)）
- **TASK-007 三部分全部完成**，五道门全绿（冻结 commit `7cb87e78cb`，引擎 console.exe sha `32436f6b…`）：
  - 门① **3/3**（编辑器 30 / 游戏 23）；门③ doctest **89/89·1213**（红阶段 11/11 新用例全红）；
    门④ 全引擎 **1515/1515·0 failed**；门⑤ `accept_m1.ps1` **22/22 连跑两次**（PASS 清单逐条一致）。
  - **契约描述已改对**（用户最在意的一条）：生成器新增向后兼容的 **`mode="replace"`**
    （默认仍是 append；replace 必须**在 reason 里逐字引用被替换文本**，未知 mode 报错），
    `editor_analyze_signal_flow` 的描述改为「只收集持久连接（`CONNECT_PERSIST`，值为 2；注意 Godot 4 中
    `flags & 1` 是 `CONNECT_DEFERRED`，不是持久连接）…」；契约仍 **171 条**、仅该行变化、`inputSchema` 与
    `map_sha256` 不变；**C++ 字面量逐字同步**；`TOOL-NAMING.md` 重渲染字节相同。
  - **第一个写组**（4 个 `mutating=true`）落地：写路径为「**临时文件 + 备份 + rename 发布**」，
    失败不触碰目标文件；真实编辑器进程 + `%TEMP%` scratch 副本给出 before/after **逐文件 size+sha256**；
    以**损坏 `.tres`** 为反例证明四次失败调用后该文件**逐字节不变**（`2800faaa…` 前后一致）；
    工程内（`.godot/` 之外）残留临时文件 **0**。
- **偏差裁决（全部接受）**：
  1. 生成器新增 `mode="replace"` → 接受（append-only 会让描述里留下互相矛盾的两句）。
  2. **`project_create_scene_file` 拒绝覆盖既有文件**（`-32000`+建议），迁移源会**静默覆盖**且契约无 `overwrite` 参数 →
     接受（「不得破坏既有文件」优先；属第 4 例「迁移源行为不可取」）。
  3. 临时文件命名为确定性的 `<base>.mcp-tmp.<ext>`（扩展名必须在最后一段——**实现者踩过这个坑并记录**）。
  4. 新增共享工厂 `MCPToolError::tool_state(...)` → 接受（避免同一种错误长出两种形状）。
  5. `accept_m1.ps1` 的 `$ToolNames` 追加 4 个写工具；**逐端点 scope 推导逻辑未动**。
  6. `project_edit_resource` 对「存在但不可加载」返回 `-32001`（沿用「找不到具体东西」语义）→ 接受。
  7. 报告 §8 的三条**自我纠错**（临时名 bug、`ResourceLoader` 缓存造成的「覆盖无效」假象已用
     `CACHE_MODE_IGNORE` 推翻、`.import` sidecar 可观察性主张撤回）→ **接受并赞赏**：这正是手册 §7.3 要的行为。
- **第 3 例迁移源缺陷写入 `PLAYBOOK` §6.6**：`editor_analyze_signal_flow` 的 `flags & 1` 在 Godot 4 是
  `CONNECT_DEFERRED`（`CONNECT_PERSIST = 2`）。**映射 `reason` 里残留的措辞不再作为行为依据**——
  行为以「工具真的能用」为准、描述以**契约（经 override 纠正）**为准、映射 reason 仅供参考。
  这是对「映射 sha 不漂移」与我此前「reason 引用不改写」裁决的**收口**：不改映射，但明确其权威边界。
- 未采纳（暂缓）：`find_signal_connections` 的 `_meta.overrides` 理由里仍引用旧描述措辞 —— 纯元数据文案，
  与 TASK-008 一起顺手清理即可，不值得单独一轮。
- 回滚点：写组实现可整提交回退；描述改动可由 `DESCRIPTION_OVERRIDES` 单条 revert。

## D55 — TASK-008 交付（B1 达 40/41）；fix-first 首次见效；第 5 例迁移源缺陷

- 日期：2026-09（B1 = **40/41**；仅剩 `running_game_read_scene` 的 1 个 `scope=game` 工具）
- **TASK-008 交付**（组 `editor_write_scene_editor`，10 个编辑器写工具；冻结 `7292af5930`，
  引擎 sha `557a31da…`）：
  - 门① **3/3**（编辑器 40 逐字 / 游戏 23 且十个工具**全部正确缺席**）；门③ doctest **94/94·1728**；
    门④ 全引擎 **1520/1520·0 failed**；门⑤ `accept_m1.ps1` **22/22 连跑两次**；
    门② 新建证据驱动器：主 41/41、GUI 7/7（**真实 3840×2054 PNG**）、无插件 3/3、游戏调用 14/14，**65/65**。
  - **fix-first 首次见效（D45 的 7 个 `fix_implementation_first` 中第一个被真正修掉）**：
    红阶段**线上实测**迁移源行为返回 `{"cleared":true,"log_was_empty":false,"log_is_empty":false}`
    （面板实测**并未清空**），doctest 在 `CHECK_FALSE(result.cleared)` 上失败；
    修法走 (a)：接 **`EditorNode::get_log()->clear()`**（正是 Output 面板 Clear 按钮的处理函数），
    绿阶段返回 `{"cleared":true,"log_was_empty":false,"log_is_empty":true}`，
    且**第二次调用**报 `log_was_empty:true`（只有第一次真清空才可能如此）；
    外部对照：引擎日志文件里 3 条标记仍在 → 证明不是靠截断日志文件冒充清屏。
  - **助手去重第二次**：原子发布助手上提到 `tools/tool_helpers.*`，等价性证明 **36/36 响应文件逐字节相同**（`85f4ca55…`）。
  - 状态变化**证据链**（用另一个读工具观察）：`scene_path` main→second.tscn；选区 0→1→2→1→0；
    相机位置 (1,2,3) 调用后可读；原子发布的反例（只读目标）保持**逐字节不变**且 `bad.txt` 未被创建、
    无 `.mcp-tmp` 残留。
- **偏差裁决（全部接受）**：
  1. **`editor_reload_plugin` 被重新瞄准**：迁移源**硬编码 `godot_mcp` 插件名**并 disable+enable，
     而我们的 MCP 服务是**内置模块、没有插件** → 照抄会变成**空操作却返回 `{"reloading":true}`**（又是一次谎报）。
     实现者改为作用于**项目里真实启用的插件**，空列表则**诚实地**返回 `-32000`+建议。**接受**——
     这是**第 5 例**「迁移源本身会谎报、必须偏离」。
  2. `editor_open_scene` 校验「编辑器真的打开了该文件」，存在但不可加载 → `-32001`+建议（不返回假的 `opened:true`）→ 接受。
  3. `editor_save_scene` 用 `PackedScene::pack` + `ResourceSaver::save(temp)` + 原子改名，而**不用**
     `EditorInterface::save_scene_as`（后者会把编辑场景**重定向**到它写入的路径）→ 接受；
     **但记录风险**：因此**不复制**编辑器保存管线的额外副作用（editor states、外部资源、folding、
     PRE/POST_SAVE 通知）——这是一个**已知功能缺口**，留待后续需要时补。
  4. `editor_capture_screenshot` 把 `save_path` 写入失败当**错误**（迁移源吞掉失败仍报成功）→ 接受。
  5/6. 属性值强制转换的局部子集、`_require_editor_ui` 的第二份副本（组间不得互改文件所致）
     → 接受，并排入 **TASK-009 §2 去重批次**（带同样的逐字节等价证明）。
  7. 红阶段用「迁移源行为 + 只读测量仪」构造，因为**不这样谎言在线级根本不可观察** → 接受（这是必要手段）。
- **环境陷阱已记录并要固化**（TASK-009 §3）：仓库根 `build-m0.cmd`（未跟踪）**没有 `tests=yes`**
  → 容易在**无测试的二进制**上跑门；且**修改 `tests/test_mcp_server.h` 后不删过期 obj 不会重新编译测试 TU**。
  → 在模块内提交**受跟踪**的 `scripts/build_local.cmd`，把这些写进脚本注释。
- 回滚点：TASK-008 的代码改动可整提交回退。

## D56 — **B1 收官（41/41）**；B2 规划与 E3 解锁路径；4 项裁决

- 日期：2026-09（head `bc34e66029`；引擎 `0f7c0752…`，version `4.8.dev.custom_build.54a21edb3`）
- **B1 = 41/41 全部落地**（7 组：6+7+6+4+7+10+1），`check_tool_groups.py` 报告 `distinct=41 == 42-1`。
  按映射 `scope` 推导的端点数：**editor-only 17 / game-only 1 / both 23 → 编辑器端点 40、游戏端点 24**，
  实况 `tools/list` 与推导**完全一致**——**「双向缺席」都拿到了端到端证据**（此前记为 unverifiable 的一项现已闭合）。
  门：doctest **96/96·1844**、全引擎 **1522/1522·0 failed**、`accept_m1.ps1` **22/22 连跑两次**、契约子集 3/3、
  `check_tool_groups` PASS、`build_local.cmd`（含 `tests=yes`）exit 0。
- **助手去重第三批**：`require_editor_ui` / `property_value_from_json` / `coerce_to_property_type` / `property_type_of`
  上提到 `tool_helpers.*`，各**恰好一处定义**；等价性用**线上逐字节**证明（35/38 行相同，
  差异仅 `g01_tools_list`（新增工具，23→24）与两个含易变 `frame_count` 的状态快照）。
- **裁决（4 项）**：
  1. **`max_results` 语义 = 「最近的 k 个」**（实现方 collect→按距离排序→截断），
     迁移源是「前序遍历发现的前 N 个」。**接受实现方的语义**——工具名是
     `running_game_find_nearby_nodes`（**nearby**），「最近的 k 个」才与名字相符；
     这是**第 6 例**「迁移源行为不可取」，记入 `PLAYBOOK` §6.6 的案例族。
  2. **`MCPToolError::no_scene()` 的 `data.suggestion` 措辞**（从 game-only 工具里说「请先用 `editor_open_scene`」，
     而游戏进程根本不提供该工具）→ **修**：措辞改为按 `scope` 自适应（或中立），
     排入 **TASK-010** 的小修项。
  3. **`--import` 会尝试绑定 9877**（今天只因用户编辑器占着端口而失败）→ **保持默认端口不变**
     （GDR-4 的默认值是与 hof-rs 的集成契约），但要求**绑定成功时打印一条 INFO（端口 + 进程类型）**，
     使意外绑定**可见**；排入 TASK-010。
  4. **两处已存在的无守卫 `double→int64` 强转**（`tool_builder.cpp` 的 `_integral_value`、
     以及 `coerce_to_property_type` 把越界 double 交给 `type_convert`；实测 `1e20` 静默变 `0`）
     → **修**（越界拒绝并给出 `-32602`），排入 TASK-010。
- **门脚本又需语义修正**（第二次）：`accept_m1.ps1` 现按
  「union 减去 game-only」推导编辑器的期望集合并断言 `game_scope_leaked=[]`；
  `check_contract_subset.ps1` 不再拿整个并集当编辑器端点的期望。**接受**——这正说明
  「逐端点 scope 语义」不是可选的装饰，而是门脚本正确性的前提（已在 D53 写入 `DESIGN-DETAIL` §17.3）。
- **B2 规划（M2 的 E3 解锁点）**：
  - B2 = **25 个工具**（`DESIGN-DETAIL` §10），是**混合批次**：既有 `scope=game` 的观测/驱动类，
    也有 `channel=editor` 的输入/编辑器播放类（`editor_play_scene`、`editor_simulate_*`、`editor_add_input_action` 等）。
  - **E3 解锁的杠杆点识别**：内置模块**同时存在于游戏进程**，
    因此 `scope=game` 的工具是**在游戏进程内直接执行**的（不再需要 GDExtension 时代的 `user://` 文件 IPC），
    其中 **`running_game_execute_gdscript`（旧 `execute_game_script`）** 是在游戏进程内跑任意脚本的能力——
    **它取代了迁移源里受 `Expression.execute([], base, false)` 限制的那条路径**（旧路径连 `Input` 单例都够不到），
    从而让「在游戏内注入输入 + 读取观测」成为可能。**这就是 E3 的解锁点**，必须在报告中以证据钉死
    （例：在游戏进程内通过该工具注入输入并观察到节点状态变化）。
  - **注意映射的既有裁定**：`editor_simulate_*` 按**迁移源行为**被定为 `channel=editor`（它们当年注入的是
    **编辑器进程**的 `Input`，正是 E3 根因）。因此**不得**把「驱动游戏」的希望寄托在它们身上；
    游戏侧驱动必须走 `scope=game` 的工具（`running_game_execute_gdscript`、
    `running_game_simulate_button_click_by_text`、`running_game_move_player_to_target` 等）。
    **本批必须在报告里显式回答：在不启动编辑器的情况下，一条从 9889 发起的调用序列能否让游戏产生可观测的状态变化。**
  - B2 需要**自己的组清单**（B1 的 `tool-groups.json` 只覆盖 B1）→ TASK-010 产出 B2 manifest 并移植第一组。
- 回滚点：B1 各组实现均可整提交回退；本节的裁决为文档。

## D57 — B2 第一刀：**E3 解锁点已钉死**；裁决新增「延迟响应通道」（GDR-20）

- 日期：2026-09（B2 进度 **7/25**；head `56ca32d735`）
- **`docs/tool-groups-b2.json` 产出**：B2 = 25 工具 / **9 组**，`check_tool_groups.py --batch B2` PASS
  （每个恰好一次、无重复无遗漏、名字都在 171 契约内、每组单一 channel/scope/mutating）；
  **跨 manifest 校验**：与 B1 无重叠、已实现并集 **48 = 17 editor-scope + 23 both + 8 game-scope**
  → 编辑器端点 40、**游戏端点 31**；B1 的 manifest 字节未变。
  组划分：`running_game_observation`(6,已实现)、`running_game_script_execution`(1,已实现)、
  `running_game_frame_observation`(3)、`running_game_input`(4)、`running_game_node_write`(1)、
  `running_game_capture`(1)、`editor_playback`(2)、`editor_input_simulation`(6)、`editor_input_read`(1)。
- **⭐ E3 解锁点已用证据钉死（29/29 PASS，全部在 9889，无编辑器进程参与）**：
  1. 从运行中的游戏读到场景树与属性（`Main` → `Player`+`Hud/Score`+`Start`，`baseline position.x=0`）；
  2. `running_game_execute_gdscript` 在**游戏进程内**够到引擎单例：`OS.get_process_id()=50156`
     （确实是引擎进程，而非控制台包装进程 53140）、`Engine.get_main_loop()` 拿到 `SceneTree`；
     **并在同一调用里现场复现旧路径的失败**：`Expression.execute([], RefCounted.new(), false)`
     → `has_execute_failed()=true`、`get_error_text()="Invalid named index 'Input' for base type Object"`；
  3. **在游戏进程内注入输入**：`InputEventAction(mcp_test_jump)` 经 `Input.parse_input_event`
     （`InputMap.has_action=true`，事件当帧入队、下一帧被 `DisplayServerHeadless` 冲刷）；
  4. **可观测状态变化**：约 3 秒后 `position.x 0→445`、`moved_frames 0→445`、`injected_events=1`；
  5. **因果性**：投递 `pressed=false` 后，间隔两秒的两次读取都停在 `position.x=451.0`。
  → 这正好闭合了 E3 的原始根因（旧路径连 `Input` 单例都够不到；且旧 `simulate_*` 注入的是**编辑器**的 `Input`）。
- **裁决 1：批准新增「延迟响应通道」（GDR-20）**——3 个跨帧工具在当前模型下**无法实现**（已给最小证明：
  同一帧取 N 次样本得到 N 个相同的值），且 B4 的 `assert_*`/`run_test_scenario`/`watch_signals`
  与 B5 的录制族同样需要跨帧。设计要求（写进 `DESIGN-DETAIL` GDR-20）：
  1. **保持「无 FIFO」原则**：pending 请求按 **(连接, 请求 id)** 关联，响应仍写回发起它的那条连接；
  2. **状态机归框架**：工具返回「已完成结果」或「pending 句柄（含 `tick()`）」，
     由 `MCPHttpServer`/`MCPJsonRpc` 驱动逐帧推进，**工具实现本身保持简单**；
  3. **不阻塞主线程**（禁止 sleep/等待）；每帧推进 pending 的预算要有上限（不得饿死常规请求）；
  4. **超时**：默认 30 s 后以 **`-32000` + `data.suggestion` + `data.timeout_ms`** 收尾（不得静默丢弃）；
  5. **连接断开要清理** pending，不得泄漏；
  6. 帧时钟用 `SceneTree` 的帧计数；
  7. 必须能用**受控的假 pending 工具**（doctest）证明状态机正确（含超时、断连、多 pending 交错），
     再用真实跨帧工具端到端验证。
- **裁决 2：把「活证据链」升级为每组强制**。本任务正是靠线上证据抓到**doctest 抓不到的真缺陷**
  （属性过滤器只用 `PROPERTY_USAGE_EDITOR` 会**静默丢掉脚本变量**）→
  `PLAYBOOK` §3 门② 升级为：「除每工具三类证据外，**每组必须给出一条跨工具的端到端活证据链**」。
- **裁决 3：接受两处自我纠正**（延续手册 §7.3）：
  ①我 Ruling 中的前提「越界 `1e20` 静默变 `0`」**不成立**——实现者实测该构建下 `_integral_value`
  在修复前就已拒绝（UB 强转得到 `INT64_MIN`），**只保留「静默接受并写入错误整数」这半句**成立
  （`coerce_to_property_type` 路径：`Curve.bake_resolution=1e20` 修复前会写出错误整数，现在返回 `-32602` 且不写文件）；
  ②实现者自己的第一版生成器**不幂等**（第二次 `--in-place` 会重复生成块），已修并**重跑全部门**。
- **其他偏差裁决（接受）**：实现两组而非一组（`execute_gdscript` 是 `mutating=true`，不能与只读组同组）；
  观测组 6 个而非 7 个（2 个跨帧工具移入 frame 组）；`get_node_properties` 用嵌套形状而非迁移源的扁平 `_safe_get`
  （避免属性键与 `node_path`/`type`/`name` 冲突）；`find_nodes_by_script` 用**精确**脚本路径匹配；
  `execute_gdscript` 接受**函数体**而非单个表达式、返回值结构化 `{result, result_type}`、
  并新增 `ScriptServer::are_languages_initialized()==false → -32000` 的守卫；
  `script_filter`/`type_filter`/`named_only` **按其契约实现**而非像迁移源那样静默忽略（第 6 条手册 §6.6 精神）；
  门脚本以最小改动支持 B2 manifest（**未削弱任何既有断言**，B1 断言逐字节不变）。
- 回滚点：延迟响应通道与新组实现均可整提交回退；manifest 是数据文件。

## D58 — TASK-011 交付（延迟通道 GDR-20）；B2 进度 11/25；两条强化建议入库

- 日期：2026-09（B2 进度 **11/25**；已实现并集 48→**52**，编辑器端点 40 / 游戏端点 **35**）
- **TASK-011 交付**（延迟响应通道 + 4 个跨帧工具），门全绿：
  - 框架：`mcp_deferred.{h,cpp}` 的 `Task`/`Queue` 按 **(连接, 请求 id)** 关联、**无 FIFO**；
    `MCPHttpServer` 逐帧推进（**每帧预算 8**）；超时以 `-32000`+`data.suggestion`+`data.timeout_ms` 收尾；
    `drop_connection()` 是**唯一清理点**；帧时钟 `SceneTree::get_frame()`。
  - **5 类状态机**：doctest 6 用例 + 线上 21 项检查；多 pending 交错 `crossed=False`；断连后 pending `1→0`；
    超时实测 **2046 ms**（自报 2000 ms，只能收紧）。
    **红阶段抓到真缺陷**：`Queue::tick` 轮转扫描完成项时索引非升序 → `remove_at` 越界
    （`FATAL: Index p_index = 2 is out of bounds (size() = 1)`），改为按 sequence 删除后全绿。
  - **跨帧证据**：headless 采样 `moved_frames=[406,408,410,413,415,418]` **严格递增**；
    窗口化 `capture_frames` 帧号 169/173/177、三个 **互不相同**的 PNG sha256；截图落盘 **4890 B 真 PNG**。
  - **无回归证据（本批最重要）**：`accept_m1.ps1` ×2 各 22/22 且两次 PASS 清单**逐字节相同**
    （并发 100 / keep-alive / 413 / 431 / 裸 LF / `Expect: 100-continue` 全过）；全引擎 **1538/1538·427192 断言 0 failed**。
    两处新行为（空闲回收豁免有 pending 的连接、同连接响应顺序背压）**只在存在 pending 时生效**。
- **两条强化建议已写入 `DESIGN-DETAIL` §18 / GDR-20 第 8、9 条**：每连接**请求背压**（HTTP/1.1 响应顺序）、
  有 pending 的连接**豁免空闲回收**（否则 30 s 空闲回收会抢在框架超时前斩断连接）。
  另记录第 10 条**能力不满足时诚实拒绝**（headless dummy renderer 无纹理存储 → 捕获类工具先判能力后拒绝，
  成功证据改在窗口化进程采集，**不得把空白帧当成功**）。
- **偏差裁决（全部接受）**：`capture_screenshot` 实现为即时而非 deferred（其跨帧依赖来自旧文件 IPC，
  进程内消失）；`find_node_when_available` 超时返回 `-32000`（**不再出现 `{found:false}` 的假成功形态**）；
  `count`/`frame_count`/`frame_interval` 为 0 时 `-32602`（0 会退回同帧重复观测，正是本任务要消灭的缺陷）；
  **跨帧持 `ObjectID` 而非裸 `Node*`**（避免悬垂指针——这是 C++ 侧的硬性正确性要求）；
  `capture_frames` 新增 `frame` 与 `sha256` 键（仅有 index 无法证明「多帧可区分」）；
  `capture_screenshot` 的 `save_path` **只接受 `res://`/`user://`**（迁移源 `globalize_path` 接受任意绝对路径，
  属**安全收紧**）；`get_status_body()` 新增 `pending`/`pending_connections`；hoist 三处既有助手（verbatim 移动）。
- 未做的可选项（记录）：`Queue::add()` 的**每连接 pending 上限**加固——当前靠每帧预算与超时；
  若后续出现「单连接提交大量 pending」的现实风险再加。
- 回滚点：延迟通道可整提交回退（但它已是 B4/B5 的前置依赖）；manifest 是数据文件。

## D59 — TASK-012 交付（B2 19/25）；活证据链再抓 3 个真缺陷；输入边界条款入库

- 日期：2026-09（B2 进度 **19/25**；已实现并集 52→**60**）
- **TASK-012 交付**（8 工具：`running_game_input`(4) / `running_game_node_write`(1) /
  `editor_playback`(2) / `editor_input_read`(1)）——该子代理**完成了全部工作与报告**，
  但**未能返回结构化回报**（工作流返回 `null`）；决策者直接读报告取证，故本条的结论来自报告原文而非转述。
  - 门：门① **四组各跑两次共 24/24**；门② 游戏相 **32/32** + 播放相 **18/18**；
    门③ doctest **118/118·3288**；门④ 全引擎 **1544/1544·427570 断言 0 failed**；
    门⑤ `accept_m1.ps1` **22/22 连跑两次**（PASS 清单 IDENTICAL）。
  - **活证据链又抓到 3 个真缺陷（全部红→绿修好，且都是 doctest 抓不到的形态）**：
    - **CR-1**：`running_game_set_node_property` 对「未给组件名的 JSON 对象」**静默写成零向量**；
    - **CR-2**：录制把 `Vector2` **序列化成字符串**，导致**录完不能回放**（往返缺陷）；
    - **CR-3**：**第二次 stop 把上一次的事件又发一遍**。
  - **进程级证据**：`editor_play_scene` 拉起的游戏子进程在 `editor_stop_scene` 后**确已消失**
    （`p08`–`p15`：9889 可连→不可连、pid 追踪其子树、`netstat` 无 LISTENING、脚本启动的 pid 全部退出）。
    这是「不制造孤儿进程」的正面证明。
- **裁决与处置**：
  1. **`running_game_play_input_recording` 的 `events` 由 `required` 放宽为可缺省**（缺省时回退到本进程刚停止的录制）→
     **接受**：`create → stop → play` 是该族的主用法，强制抄回事件既无益又易错（且正是 CR-2 那类往返缺陷的温床）；
     这是一处**契约文本的放宽**（消费者按 `required` 用法仍然可用），须在 M2 验收时复核。
  2. 新增 `tools/input_recorder.{h,cpp}` + `MCPInputRecorderNode`，**用引擎内 C++ 子类覆写的 `Node::input()`**
     而非 `_input` GDVIRTUAL —— **接受，且这是重要技术发现**：GDVIRTUAL 只经 `ScriptInstance`/GDExtension 解析，
     **引擎内的 C++ 子类永远收不到**。已写入 `DESIGN-DETAIL` §19.4。
  3. `editor_stop_scene` 回读 `is_playing_scene()`（子进程拒绝退出 → `stopped:false`，不再无条件 `stopped:true`）→ 接受。
  4. `editor_play_scene` 的 `mode` 走 `normalize_project_path`（只接受项目内路径，迁移源接受绝对路径）→ 接受（安全收紧）。
  5. `vector_from_dictionary` 声明在头文件以便 doctest 断言**真函数** → 接受（CR-1 是静默错值，只有直接断言钉得住）。
  6. `stop_input_recording` 新增 `event_types`/`duration_ms`（答案超集）、`actions` 升序（确定化）→ 接受。
- **新规范条款 `DESIGN-DETAIL` §19 / GDR-21「输入通道边界」**（本模块存在的首要理由之一）：
  ①`editor_*` 输入工具作用于编辑器进程、**永远不能驱动游戏**；②驱动游戏必须走 `scope=game` 工具且只在游戏端点可见
  （双向缺席都有线上证据）；③**游戏子进程的端口来源**：harness 启动时传 `--mcp-port`，
  而**编辑器经 `editor_play_scene` 启动时不会转发 `--mcp-port`**（`editor_run.cpp` 无端口参数），
  此时端口来自 `ProjectSettings: godot_mcp/port`——**模块不为「别人启动的游戏」发明端口**，
  这条写进规范以免后续被误判为缺陷；④录制用 `Node::input()` 而非 `_input` GDVIRTUAL；
  ⑤录制必须有**长度上限**并报 `truncated: true`。
- **两条引擎事实登记（不绕过、不伪装，记入报告与规范）**：编辑器不转发端口（上条③）；
  编辑器**会另起自己的辅助子进程**，故「编辑器无子进程」**不是**无孤儿的判据
  → 本批改为按游戏 child 的 pid **追踪其子树**。
- **4 条勘误（全部接受）**，其中值得记住的是：
  ①D56 的证据脚本第一版用了 DDScript 里不存在的常量（`DEVICE_ID_INTERNAL` 未 BIND）导致**看起来像工具全坏**
     → 修法：改用 `DEVICE_ID_EMULATION` 并**新增前置检查断言游戏脚本确已加载**
     （教训：**证据挂了先怀疑证据，而不是先怀疑被测物**）；
  ②请求体由字符串拼接构造 → 含引号的坐标破坏 JSON，表现为 `-32700`/`-32602`（**看起来像被测工具的缺陷**）
     → 一律用 `ConvertTo-Json` 生成（与 D52 的 `Out-File` 事故同类，手册 §7.1 的又一实例）；
  ③一次被抑制输出的构建造成**构建竞态残留**（SCons `CommandNoCache` 生成 `modules_tests.gen.h` 失败，
     该次构建**没真正进行**），日志里的编译错误**不是本批引入的缺陷**——教训：**不要抑制 scons 输出**；
  ④门②的游戏相前三次运行失败，是 3 个真缺陷 + 2 个宿主问题共同所致，**失败记录全部保留**（append-only）。
- 回滚点：本批实现可整提交回退；规范条款为文档。

## D60 — **B2 收官 25/25**（B1+B2 = 66 工具）；CR-4/CR-5；派 M2 里程碑验收

- 日期：2026-09（已实现并集 60→**66**；编辑器端点 **49** / 游戏端点 **40**；引擎 `46e92359…`）
- **TASK-013 交付**（B2 最后一组 `editor_input_simulation` 6 工具 + 录制上限 + GDR-21 边界实测）：
  - 门：门① 3/3 ×2；门② 边界 **24/24**、上限 **11/11**、反例 **15/15**（50 组真实请求/响应，全部落盘 + sha256）；
    门③ doctest **122/122·3618**；门④ 全引擎 **1548/1548·427900 断言 0 failed**；门⑤ `accept_m1.ps1` **22/22 ×2**（清单一致）；
    `check_tool_groups.py --batch B2` → **25/25 PASS**（`implemented=true` 组 9 个、25 工具）。
  - **GDR-21 边界实测（双进程同一次运行对照）**：编辑器侧 `editor_simulate_key` 后**编辑器进程自己**的
    EditorPlugin 计数 `key=1`，而**游戏自己的计数保持 0**；点/移/加动作后编辑器 `mouse_button=1/mouse_motion=1/action=1`，
    游戏仍 `0/0`；编辑器 `InputMap` 含新 action（count=90）而游戏 `InputMap.has_action=false`；
    **对照**：同一按键**在游戏进程内**注入时游戏计数 `0→1`；9889 调用编辑器工具 → `-32601`；`tools/list` **49 vs 40**。
    → 「为什么编辑器注入驱动不了游戏」现在**钉在实测上**。
  - **录制上限**：事件数/时长双上限（默认 `100000` / `600000 ms`，可经 `godot_mcp/recording_max_events|recording_max_duration_ms`
    或 `set_limits()` 覆盖，`<=0` = 无界）；达上限**停止采集**、计数丢弃并在结果里**无条件**报 `truncated/dropped/limits`；
    实测：上限 3 录 5 → `event_count=3 dropped=2 truncated=true`；时长上限 500 ms → `event_count=1 dropped=1`。
    `truncated` 的语义被钉死为「**至少真丢了一个事件**」（时钟越过上限但没有后续事件时**不**声称截断）。
  - **又抓到两个真缺陷（红→绿）**：**CR-4** 鼠标事件未设 `global_position` → **鼠标实际没动**；
    **CR-5** `button` 未做范围校验 → `mouse_button_to_mask()` 移位触发**引擎 UB**（现校验 1..9）。
- **偏差裁决（全部接受）**：`editor_simulate_input_sequence` 注册为 deferred（`frame_delay` 是帧时钟，
  其首个事件在请求的**下一帧**落地——延迟通道从不在到达帧内 tick）；
  单个鼠标工具**只注入一个事件**（addon 的 `auto_release` 参数不在冻结契约里，映射引用的 `input.rs` 也是单事件）；
  未知按键名 → `-32602`（而不是注入 `KEY_NONE`）；六个工具的答案新增透明键（`target:"editor"`、
  `in_input_map`、`persisted:false`、`time_ms_ignored`）；上限走 `ProjectSettings` + `set_limits()`
  （契约没有该参数、**不得改契约**）；`stop_input_recording` 增加三个无条件键；
  三个旧 doctest 的编辑器表计数随工具数变化（`60→66`、`43→49`，**未削弱任何断言**）；
  本 fork 的 `REQUIRE` **不回卷**（`tests/test_macros.h:44`）→ 新用例对每次读取都加守卫。
- **两条引擎事实入库（供后续批次）**：①`InputEventMouse::set_position()` **不**派发 `global_position`
  （`input_event.cpp:689` vs `input.cpp:926`）——这正是 CR-4 的成因；
  ②`InputMap::action_add_event()` **会去重**（`input_map.cpp:205`）。
- **已知未修（记录，不掩盖）**：`tools/editor_input_read.cpp` 解引用 `InputMap::get_singleton()` **无 null 检查**
  （在活的编辑器端点上不可达，doctest 中可达）——按「不得改别组文件」纪律留给后续清理批次。
  另记风险：**录制上限只约束采集，不约束随后交给 play/save 的快照**（可选加固）。
- **⭐ M2 里程碑独立验收已派发**（任务书 `TASK-AUDIT-M2`）：覆盖 **B1+B2 全部 66 个工具**，
  分五类判定（全量对等 / 诚实性 / 行为一致 / 安全边界 / 工程门），
  并要求验收方**自己**复跑边界与上限相、自己核对「7 个 fix 中只有 1 个已修、其余 6 个必须未注册」、
  自己构造路径逃逸与参数滥用反例、自己证明**9877 未被占用**且无孤儿进程。
- 回滚点：本批实现可整提交回退；manifest 与规范为文档/数据。

## D61 — **M2 里程碑独立验收：`pass`**；3 缺陷裁决；进入 M3（mono + C#）

- 日期：2026-09（66 工具；验收基准 HEAD `e843f46668`）
- **M2 独立验收（全新子代理，六类判定全 pass）**：
  - **全量对等 = pass**：验收方**自己**抓两端点，期望集合**只**由两个 manifest + 映射的 `scope` 推导
    （`editor 26 / game 17 / both 23` ⇒ 编辑器 **49**、游戏 **40**）；并集**恰为 66**（missing 0 / extra 0）；
    **89 个端点-工具对**的 `name`/`description`/`inputSchema` **0 不一致**；双向 scope 泄漏均为空，
    跨端点调用 `-32601` 且**无 content 信封**（并用已知工具做对照，证明不是「注册表一律 `-32601`」）；
    `tools/list` 同 id 三次 + **跨进程重启** sha 一致。
  - **诚实性 = pass**：**6 个未修的 `fix_implementation_first`**（`editor_disconnect_signal`/`editor_set_auto_dismiss_dialogs`/
    `editor_set_tilemap_cell`/`editor_set_tilemap_cells_in_rect`/`editor_bake_navigation_mesh`/`editor_get_test_report`）
    与 **2 个 `unregister`** **全部未注册**（两 manifest 不含、两端点 16 次调用全 `-32601`、源码全文检索 0 命中）；
    `editor_remove_output_log` 走 `EditorLog::clear()`（面板 Clear 同路径），**不写/不截断任何日志文件**，
    无 `EditorLog` 时 `-32000` 且**绝不报 `cleared:true`**。
  - **行为一致 = pass**：42 条抽样（跨 4 通道、含写工具与 deferred）最终 40 条为契约形状；
    首版 8 条红**全为审计自身的期望错误**（同一参数名撞 PowerShell 自动变量等），已 append-only 更正；
    唯一实质分歧为 D-1。跨工具落地性有独立读回（`set_node_property` 写入由 `execute_gdscript` 独立确认）。
  - **安全边界 = pass**：写侧 8 种逃逸拼写 × 2 工具、读侧 5 种 × 4 工具**全 `-32602`**，
    前后快照证明**工程外零文件落盘**；`1e20`/`NaN`(→`-32700`)/类型错/缺参全被拒；
    deferred **9/9**：工具自报 2 s → `-32000`+`data.timeout_ms=2000`（证明只能**收紧** 30 s 上限）、
    pending 期间 `ping` 35 ms、**两条连接同发 `id=5555` 各自收到自己的超时**（证明键是 `(连接, id)`、无全局 FIFO）、
    硬断连后 pending 归零不崩、同连接响应保序。
  - **工程门 = pass**：验收方**先重建**与 HEAD 一致的二进制（`--version` = `4.8.dev.custom_build.e843f4666`）才验收 →
    doctest 122/122·3618、全引擎 1548/1548·427900 断言 0 failed、`accept_m1.ps1` 两次 22/22（清单 IDENTICAL）、
    两个 manifest PASS；**9877 全程 PID 36392 未被触碰**、9888/9889 无 LISTENING、无孤儿进程。
- **3 个缺陷 + 1 条加固的裁决**：
  1. **D-1（minor）采纳**：`running_game_set_node_property` 对**不存在的属性**返回成功形状（`new_value:null`）→
     改为 **`-32001`+`data.suggestion`**。**注意**：迁移源（`mcp_runtime_agent.gd:159-160`）同样无条件 `set:true`，
     故这不是「与参照不一致」而是「工具真的能用」标准下的**诚实性缺口** → **手册 §6.6 的第 7 例**。
  2. **D-2（nit）采纳**：headless 截图用 `-32603` → 统一为 GDR-20 第 10 条的 **`-32000`+建议**，
     `-32603` 只留给真正的内部错误。
  3. **D-3（nit）裁决：契约改成与行为一致**（而非把行为改回必填）。理由：契约的 `inputSchema` 是**智能体读取的**，
     它必须描述真实可接受集（否则「描述与功能不对应」这一被用户反复强调的问题会重现）；
     用 `SCHEMA_OVERRIDES` 把 `events` 移出 `required`，并把**回退规则写进 description**
     （缺省 = 回放本进程最近一次 `stop_input_recording`；无可用录制 → `-32602`），
     然后**重跑生成器 + 重渲染 `TOOL-NAMING.md` + 更新全部指纹 + 同步 C++ 字面量**。
  4. **R-3 加固采纳**：`mcp_server/pending_timeout_ms` 配 `0` 会**关闭延迟任务的唯一兜底** →
     改为「`<=0` 视为默认上限」或显式拒绝 + 启动警告。
- **唯一流程风险 R-1 已写入 `PLAYBOOK` §3（重要）**：`bin/` 不受版本控制
  （`.gitignore` 忽略 `[Bb]in/`）→ 门会在**陈旧二进制**上跑出**假红**（验收方开工时二进制落后 HEAD 一个任务，
  会把 B2 误判为 **19/25**）。新增强制步骤：**门之前必须重建**，
  并**校验 `--version` 的 hash 前缀 == `git rev-parse --short HEAD`**。
- **U-1/U-2 未闭合但有据**：`editor_remove_output_log` 的**肉眼级**面板清空（U-1）与截图**成功路径**（U-2）
  本环境未直接观测（U-2 的窗口化成功证据已在 TASK-008 的 gui 相拿到真实 PNG）；
  当前证据水平足以判 pass，若需正式闭合，可在**不占用 9877** 的前提下开一次短命窗口化进程补证。
- **下一步：M3**（TASK-014）——mono 构建 + **C# 工程真的能跑**，并把上述 3 缺陷 + R-3 一并修掉。
  为什么现在做 M3 而不是继续 B3：用户要求 **C# 作为游戏开发语言**，mono 与内置模块是否冲突**越早验证越便宜**；
  若等到 B3–B5 之后再发现冲突，返工面会大得多。
- 回滚点：M2 判决为文档；3 项修复由 TASK-014 承担，可整提交回退。

## D62 — **M3 交付：mono 构建 + C# 工程真的能跑**；3 缺陷已修；C# 事实与并发构建隐患入库

- 日期：2026-09（同一 commit 两个构建：非 mono `4.8.dev.custom_build.eb05a50ed` /
  mono `4.8.dev.mono.custom_build.eb05a50ed`）
- **mono 构建（M3 主体）**：
  - `scons platform=windows target=editor module_mono_enabled=yes -j8` → exit 0，**112.8 s**，
    产物 `bin\godot.windows.editor.x86_64.mono.exe`（178 MB）+ `.mono.console.exe`；
    **因为 mono 用不同的文件名，非 mono（`tests=yes`）二进制不被覆盖**——两者并存在 `bin\`，
    故无需备份/还原（仍另存了一份到 `%TEMP%`）。这正是后续批次要的行为（doctest 仍由非 mono 承担）。
  - glue 生成：`--headless --generate-mono-glue modules/mono/glue` → exit 0（2.7 s，"The Godot API sources were successfully generated"）；
    装配：`build_assemblies.py --godot-output-dir=bin --godot-platform=windows` → exit 0（80.7 s），
    产出 `bin\GodotSharp\{Api\{Debug,Release},Tools}` 与 4 个 `4.8.0-dev` nupkg。
  - **mono 构建不带 `tests=yes`**（任务书允许）→ **「mono 下的 doctest」未被测量，也不作任何声称**（诚实边界）。
- **C# 工程真的能跑（M3 验收核心）**：
  - 最小 C# 工程（`%TEMP%\mcp014-scratch\m3-csharp-proj`）：`project.godot` + `.csproj`（`Godot.NET.Sdk 4.8.0-dev`, `net8.0`）+ `Main.cs`；
    **离线**构建（本机 `nuget.org` 不可达属正常，`NuGet.config` 只指向引擎自带的 `bin\GodotSharp\Tools\nupkgs`）
    → `dotnet build -c Debug` **0 警告 0 错误**，产物落在 GodotSharpDirs 期望的位置。
  - 直接证据（不是「文件存在」这类间接证据）：引擎 stdout `[MCP014-CS] Main._Ready ran; state=csharp-ready`；
    从 **9889** 用 `running_game_execute_gdscript` 调 C# 方法得 `csharp: ticks=1423 state=csharp-ready`；
    `[Export] CsharpTicks` 经 `get_node_properties` 两次读到 **1428 → 1564**；
    **C++ 写入 `CsharpState` 后 C# 读回 `state=written-from-mcp`**（跨语言双向可见）。
  - **模块共存**：mono 下编辑器端点 9888 = **49**、游戏端点 9889 = **40**，与非 mono 完全一致；
    四项修复在 mono 下同样成立。
- **M2 三项修复 + R-3 全部落地**：
  - **D-1**：`write_node_property` 先**查属性表**再写（`property_type_of` 返回 `NIL` 也意味着「声明为 `Variant`」，
    故以属性表判定）→ 未知属性 `-32001`+建议，**任何错误路径都产生不出成功形状**。
  - **D-2**：`editor_capture_screenshot` 先判能力 → `-32000`+建议；`-32603` 只留给唯一的真内部错误。
  - **D-3**：生成器 v1.5.0 引入 **`SCHEMA_OVERRIDES`**（首条：`events` 移出 `required` → `"required": []`），
    配套 `DESCRIPTION_OVERRIDES` 写明**回退规则**；schema override 必须 `mode=replace` 且**理由里逐字引用被移除的 required**；
    契约重生成、`TOOL-NAMING.md` 重渲染（逐字节相同）、C++ 字面量同步（再跑一次是 no-op）。
  - **R-3**：`pending_timeout_ms<=0` → 落回 30000；启动日志同时报**配置值与生效值**；
    实测工具自报 600 s 时 **30.0 s** 后以 `-32000`+`data.timeout_ms=30000` 收尾。
  - 门（实现方自跑）：doctest 红 2 例/10 断言 → 绿 **124/124·3653**；全引擎 **1550/1550·427935 断言 0 failed**；
    门① **3/3** 两端点；`accept_m1.ps1` **22/22 ×2**（PASS 清单逐字节相同）；
    且**全部在 `--version == git rev-parse --short HEAD` 的重建二进制上**。
- **两条 C# 实测事实入库（`PLAYBOOK` §3 与后续任务书）**：①`running_game_execute_gdscript` 编译到**裸 `RefCounted`**，
  **没有 `get_node()`** → 要用 `Engine.get_main_loop()`；②**C# 的 `public` 字段不是 Godot 属性**，
  只有 `[Export]` 成员在「游戏侧节点工具」的属性面里。**B3 的任务书必须带上这两条**，否则会在 C# 工程上踩坑。
- **并发构建隐患入库（`PLAYBOOK` §3，与 R-1 同类）**：实现方自报**短暂并发跑了两个 scons**
  （「杀死后台任务」**不保证**其 scons 子进程也停），两者同时重写生成头 `modules/modules_tests.gen.h`
  → **一批与本批无关的假编译错误**；单进程重建后全部消失、源码未变。
  → 规则：**构建一律串行**，且**不要抑制 scons 输出**。
- **为 hof-rs 的 `hoh doctor` 预检准备（记录；hof-rs 仍暂停）**：需检查 `Microsoft.NETCore.App 8.x`、
  `<engine>/GodotSharp/Api/{Debug,Release}`、`<engine>/GodotSharp/Tools/nupkgs` 下的 `Godot.NET.Sdk.<version>`，
  以及**离线解析本地源**（本机无外网应当被视为**正常**而不是异常）。
- 偏差裁决（接受）：未重建「修复前」的二进制（before 侧用 M2 验收**自己测到的**响应 + 修复前源码 + 本轮 doctest 红阶段）；
  红阶段日志早于一次测试文本编辑（两处头条断言与最终版逐字节相同）；
  `Variant::NIL` 类型的属性在本环境**不可构造**（`set_meta(name, Variant())` 会抹掉条目）→ 该分支以代码论证 + 两侧可构造子例夹逼，
  **明确声明为覆盖缺口**；`write_node_property` 先判 `is_inside_tree()` 再 `get_path()`（孤儿节点返回 `""` 且不触发引擎错误）；
  门②首轮跑在代码提交前的二进制上（`--version ca053e552`），提交后**重建并重跑全部门与门②**（报告只引用重绑后的结果）。
- **下一步：M3 独立验收（TASK-AUDIT-M3）**，然后 **M4 = B3+B4**（B3 就是节点写族，`running_game_set_node_property`
  已确立「先查属性表再写」的形状，本族应照此办理），最后 **M5 = B5 + hof-rs 切端点 + 真实 T=1 冒烟**。
  注意 **hof-rs 仍处用户指令的暂停状态（D43）**：M5 里「hof-rs 切端点 + 真实冒烟」需在解除暂停后进行；
  我会在推进到 M5 时就此向用户确认，而**不擅自恢复 hof-rs 的工作**。
- 回滚点：mono 构建产物与 C# 工程都在 `bin/` 与 `%TEMP%`（不受版本控制）；3 项修复可整提交回退。

## D63 — **M3 独立验收：`pass`**；一处措辞被纠正；进入 M4（B3/B4/B5 分类 + B3 首组）

- 日期：2026-09（验收方自建 HEAD 绑定二进制：mono `4.8.dev.mono.custom_build.6ea5de6e0` / 非 mono 同前缀）
- **M3 独立验收（六类全 pass）**：
  - **mono 构建 pass**：验收方**自己重建**两个构建（mono 113 s / 非 mono 45.8 s，exit 0）；
    glue 重生成到 `%TEMP%` 与仓内 **1110 个 generated 文件逐字节相同**；
    4 个 `4.8.0-dev` nupkg 被**离线 `dotnet build` 端到端消费**（未重跑 `build_assemblies.py`，**已显式声明取舍**）。
  - **C# 可跑 pass**：验收方**自建工程副本**（robocopy 排除 `.godot`，另加 `public int PlainField` 与抛异常的 `Boom()`）→
    离线 `dotnet build` exit 0、**0 警告 0 错误**；mono 引擎起游戏后 C# **真的在跑**（ticks 递增），
    从 9889 读到 `csharp: ticks=944 state=written-from-mcp`；C++ 写 `CsharpState` 后 C# 读回（**反向也验证了**）。
  - **模块共存 pass**：mono 下 9888=**49** / 9889=**40**，验收方**自己逐字比对零失配、零 scope 泄漏**。
  - **三项修复 pass**：D-3 的**结构化 diff 自证**（171→171、名字集合不变、**只**动该工具 `description`+`required`、
    `properties` 一字未改、`_meta` 仅 `generator_version 1.4.0→1.5.0` 与 2 条 override、`map_sha256` 与实际相符）；
    D-1 → `-32001`+建议且真实写入由**另一工具独立读回**；D-2 → `-32000`+建议（参数错仍 `-32602`）；
    R-3 配 `0` 时启动日志报 `pending_timeout_ms=30000 (configured=0)` + WARNING，**实测 30.022 s** 以
    `-32000`+`data.timeout_ms=30000` 收尾（另补测配置 5000 保留为 5000）。
  - **工程门 pass**（全在重绑定二进制上）：doctest 124/124·3653、全引擎 1550/1550·427935 断言 0 failed、
    门① 3/3、`accept_m1.ps1` 22/22 ×2（PASS 清单逐字节相同）；**mono 与非 mono 同一请求 6/6 payload 逐字节相同**。
  - **端口纪律 pass**：9877 全程 PID 36392 未被触碰；9888/9889 收尾无 LISTENING；无孤儿；无 git 写操作。
- **缺陷 1 条（minor/文档）已采纳并已在手册修正**：我在 `PLAYBOOK` 里写的
  「C# 的 `public` 字段**不是** Godot 属性，只有 `[Export]` 在属性面里」**措辞过强**——
  准确事实是：**非 `[Export]` 的 `public` 字段不进 `get_property_list()`，但 `Object::get/set` 仍可按名读写**
  （`csharp_script.cpp:1487-1521`；实测全量列举 29 键不含 `PlainField`，但按名 `set` 成功 `4242→7`）。
  → **B3 的节点写族不得据「不可达」做设计**：属性表用于**校验/类型判定**，
  「按名可写」这一事实要么显式允许、要么显式拒绝并在报告说明。手册 §3 已按此修正。
- **另两条已入手册的隐性风险**：①**首次导入且 `.tscn` 带 BOM** 的 scratch 工程 `--import` 会以 `0xC0000005` 退出
  （门脚本用 `Set-Content -Encoding UTF8` 容易引入 BOM）→ **门脚本必须显式校验 `--import` 退出码**、
  scratch 的 `.tscn` **不要写 BOM**；②`godot_mcp` 启用但未传 `--mcp-port` 时会尝试 bind **9877**，
  实测被 OS 拒绝并**优雅自禁**（`WARNING: [MCP] bind failed on 127.0.0.1:9877; MCP server disabled`），
  用户进程未受影响（与 §19.3/GDR-4 的裁决一致）。
  另记：`REPORT-014` §6 里 4 个二进制 sha256 **已因验收方重绑定 HEAD 而失效**（`bin/` 不受版本控制）——
  下游引用这些指纹的证据需重取。
- **进入 M4**（TASK-015）：
  - **第一部分**：把剩余 **103** 个工具（171 契约 − 2 个 `unregister` − 已实现 66）**完整分类**成
    `docs/tool-groups-b3.json` / `-b4.json` / `-b5.json`，要求**完备性可机器校验**
    （三 manifest 并集恰为 103、恰好各一次、与 B1/B2 无交集、名字都在契约、channel/scope/mutating 与映射逐条一致），
    且**不得削弱既有 manifest 检查**。
  - **第二部分**：移植 B3 首组（编辑器节点写族，8–10 个），**含 2 个 `fix_implementation_first` 必须先红后修**：
    **`editor_disconnect_signal`**（迁移源**忽略 `target_path`**、固定用场景根作 `Callable` → 断的可能不是目标那条却报成功）
    与 **`editor_set_auto_dismiss_dialogs`**（只写**无人读取的 static** → 纯谎报，必须真实现或诚实 `-32000`，
    **禁止假成功**）。节点写族照 TASK-014 确立的「**先查属性表再写**」形状做。
- 回滚点：M3 判决为文档；TASK-015 的实现可整提交回退。

## D64 — TASK-015：B3/B4/B5 分类完备（**105 而非 103**，我的算术错误被纠正）；两个 fix-first 真修

- 日期：2026-09（已实现 **76/171**；`editor_node_write` 组 10 个工具落地）
- **⭐ 决策者的算术错误被实现方纠正（记录在案）**：我在 D63/TASK-015 里写「剩余待移植 = 171 − 2 unregister − 66 = **103**」，
  但**那 2 个 `unregister_until_implemented` 的名字并不在 171 条契约里**（它们已被剔除），
  所以不能二次扣减 → **真实待移植 = 171 − 66 = 105**。实现方按真实集合分类并做成**机器断言**。
  教训：**「契约条数」与「待移植集合」必须分别实时推导**，不要用过去某一步的残差做算术。
- **B3/B4/B5 分类完备（可机器校验）**：`b3`(40 工具/12 组，sha `25a2d784…`) / `b4`(7/3，`21a5dd5e…`) / `b5`(58/26，`09dc64da…`)；
  并集**恰好 105、各一次**、彼此及与 B1/B2 **无交集**；`check_tool_groups.py --check-completeness` 与
  `--batch B3|B4|B5` 全部 exit 0，且 **B1/B2 旧路径输出 SHA 逐字节不变**（`0cfcac80…`/`14eba000…`）。
- **B3 首组 `editor_node_write`（10 个工具）**：门① **3/3**；门② **43/43**；门③ doctest **130/130·4383**
  （红阶段 128/130、14 断言失败、exit 1）；门④ 全引擎 **1556/1556·428665 断言 0 failed**；
  门⑤ `accept_m1.ps1` **22/22 ×2**；全部在 `--version == HEAD`（`41267a006`）的绑定二进制上。
- **两个 `fix_implementation_first` 真修（红→绿）**：
  1. **`editor_disconnect_signal`**：红版忠实移植迁移源（**忽略 `target_path`**、用场景根构造 `Callable`、**无条件报成功**）
     → 恰好在该用例上 **14 条断言失败**、exit 1，引擎日志留下 `Attempt to disconnect a nonexistent connection`；
     修后**按调用者指定的 target 解析**，先 `has_signal` 再 `is_connected` 精确匹配才断开，否则 `-32001`+建议。
     线上证明：`connect=0 / first disconnect=0(target=Renamed) / second disconnect=-32001`。
  2. **`editor_set_auto_dismiss_dialogs`**：红版写**无人读取的 static** 并返回成功字典 → 修后**恒为
     `-32000 Not implemented` + `data.suggestion`**，因为**已证明本引擎没有进程级弹窗自动关闭开关**
     （29 处 `set_hide_on_ok` 都是**逐对话框硬编码**；唯一的编辑器级对话框设置 `accept_dialog_cancel_ok_buttons`
     属顺序选择）。**该工具没有可构造的成功类，已显式声明**。
     → 这是 D45 的 7 个 fix-first 中**第 3 个**被真正修掉（`editor_remove_output_log`、`editor_disconnect_signal`、
     `editor_set_auto_dismiss_dialogs`）；剩余 4 个在 B4（`editor_get_test_report`）与 B5（tilemap×2、`bake_navigation_mesh`）。
- 偏差裁决（接受）：`editor_set_node_property` 返回键集改 TASK-014 形状（去掉迁移源恒真的 `updated:true`）；
  `editor_delete_node` **拒绝删除编辑场景根**（迁移源会把整棵打开场景 `queue_free`）并报 `deferred:true`；
  `editor_rename_node` 报引擎**实际采用**的名字（`set_name` 是消毒而非失败）并加 `requested_name`/`name_sanitized`；
  `editor_reparent_node` 新增「移到自己后代下」「移动编辑根」两条前置拒绝；`editor_connect_signal` 未知信号 `-32001`、
  重复连接幂等成功并标 `already_connected`；`editor_set_node_groups` 非字符串元素 `-32602`、`removed` 排序 `added` 去重（确定性）；
  `editor_add_node` 的属性走同一份 `write_node_property`，**未知属性时销毁半成品节点**；
  证据脚本的 `--import` 传 `--mcp-port=0` 且**校验 `$LASTEXITCODE`**（`Start-Process` 的 `ExitCode` 在本机返回空，
  前两次运行曾误报失败——与 D63 的「门必须校验 import 退出码」同源）。
- **已知瑕疵（记录不改）**：未知属性的错误消息里节点名是**引擎绝对路径且含每次运行不同的节点 id**（非确定）；
  改它会波及 B2 已验收的线上消息 → 留待有需要时统一。
- **下一步（TASK-016）**：先**上提 `_find_node`**（TASK-015 因纪律在组内复制了一份；不清理会让每个编辑器写组再复制一遍）
  并给出**逐字节等价证明**；再移植 B3 接下来 **2 组（≤20 个工具）**，优先 `editor_node_read`，
  并要求**写族→读族互验的活证据链**（用写族改、用读族读回）。
- 回滚点：本批可整提交回退；manifest 为数据文件。

## D65 — TASK-016 交付（86/171）；手册的悬空引用已修正；再次清理竞争性文档

- 日期：2026-09（已实现 **86/171**；剩余 B3 20 / B4 7 / B5 58；编辑器端点 69 / 游戏端点 40）
- **TASK-016 交付**（助手上提 + B3 两组 10 工具），独立验收 verdict = `pass`（0 blocker/major、1 minor 文案）：
  - **助手上提**：`edited_scene_root()`（3 份副本）与 `find_node()`（2 份副本）上提到 `tools/tool_helpers.*`，
    模块内各只剩 **1 处定义**；**逐字节等价证明**：真重建 PRE=`c26516becc` 的 before 二进制，
    同 20 例序列 **20/20 响应 sha256 全等（diff=0）**，且引擎 banner 证实两侧构建**确实不同**（防「拿同一二进制比同一二进制」的假证明）。
  - **两组 10 工具**：`editor_node_read`(6) + `editor_node_instantiate`(4)，契约逐字（双端），
    9889 **全缺席**、10/10 回 `-32601` 不执行。
  - **两处行为纠正**：`properties` 点名**不存在属性** → `-32001`（**手册 §6.6 第 8 例**）；
    `editor_add_gridmap` 的库加载失败 → `-32001` 而**不**再假报 `created:true`。
  - **写族→读族互验活链（本批最有价值的证据）**：`editor_add_node` → 设属性 → 读族读回 `{7,9}` →
    设组 → 读组 → 按组找到 → 连信号 → 读信号/信号连接表 → 断开 → **连接数归零** → 删节点；
    另一条链由实例化族 → 读族读回 `RayCast2D/RayCast3D/MeshInstance3D/GridMap(mesh_library_set=true)/Node3D`。
    两条链**由独立验收子代理自行重跑复现**（非抄报告）。
  - 门：① 两组各 3/3；② **86/86**；③ doctest **139/139·5185**；④ 全引擎 **1565/1565·429467 断言 0 failed**；
    ⑤ `accept_m1.ps1` **22/22 ×2**（PASS 集合相同）；交付后重建复核 `--version == HEAD`（`b5999d447`）仍全绿。
- **缺陷 1 条（minor/文案）**：`MCPToolError::not_found()` 在「被列举规则隐藏但被点名」的属性上**重复追加后缀**
  （出现 `... is not readable by name not found`；行为正确、仅文案）→ 排入 **TASK-017 顺带修** 并补 doctest。
- **⚠️ 手册缺陷已修正（决策者的责任）**：`PLAYBOOK` 开头引用 `DECISIONS.md` 时**未写全路径**，
  而该文件在 **hof-rs**（对执行者只读）、fork 内并不存在 → 执行者搜索无果后**自造了**
  `docs/spec/TASK-016/DECISIONS.md`（这已是**第二次**自造竞争性文档，第一次是 `docs/spec/TASK-005/`）。
  → 处置：①**删除**该目录；②手册改为**绝对路径** `F:\moonbit-hof-rs\DECISIONS.md`，
  并**显式写明**「**本 fork 内不得新建** `DECISIONS.md` / `docs/spec/**` 之类的竞争性规范或日志文档；
  执行者只写报告；认为规范有误就在报告里报缺陷」。
  教训：**路径引用不写全，等价于给下游发出错误指令**——与「任务书必须自包含」是同一条纪律。
- **风险 R1（接受并记录）**：全量 doctest 进程里**真 `GridMap` 会 SIGSEGV**（二分证明：仅排除该用例即 1564/1564 全绿），
  根因未定位、且 `modules/gridmap` 超出本模块范围。实现方把该 doctest 的接收者改为裸 `Node`，
  **工具侧真 `GridMap` 路径由线上证据覆盖**。→ 接受该处置；**不**为它单开 spike
  （除非 M5 的真实冒烟需要 `editor_add_gridmap`）；作为已知覆盖缺口记录。
- 下一批（TASK-017）：B3 接下来 **3 组 10 个工具**（`editor_node_batch_write`(2)、`editor_control_layout_write`(1)、
  `editor_node_setup`(7)），要求**批量写的事务语义显式化**（含故意坏的中间元素反例，禁止「报成功但只做一半」）
  与 **7 个 setup 族的读回证据**；顺带修上面的文案缺陷。
- 回滚点：本批可整提交回退；manifest 为数据文件。

## D66 — TASK-017 交付（96/171）；批准实施者的 3 项自决；**静默错值必须修**

- 日期：2026-09（已实现 **96/171**；编辑器端点 79 / 游戏端点 40；B3 剩 10、B4 7、B5 58）
- **TASK-017 交付**（3 组 10 工具），独立验收 pass：
  - 门① 三组各 **3/3**；门② **88/88**；门③ doctest **157/157·5875**；门④ 全引擎 **1583/1583·430157 断言 0 failed**；
    门⑤ `accept_m1.ps1` **22/22 ×2**；全在 `--version == HEAD`（`612d1e544`）的绑定二进制上。
  - **批量写事务语义（本批最有价值的决定）**：`editor_add_nodes_batch` **全成功或全回滚**——
    prepare 阶段校验每个元素却**什么都不实例化**，全部合法才 commit；任一步失败则**逆序释放**并返回带
    `data.batch = {status:"rolled_back", on_error:"all_or_nothing", …}` 的**单个错误**。
    反例证据：`[合法, {父路径缺失}, 合法]` → `-32001`，读族证明**零新增路径**。
  - **7 个 setup 族各有「用另一个读工具」的读回证据**；**`shape_params` 真的落地**
    （`RectangleShape2D (32,32)`、`BoxShape3D (1,2,3)`，经保存 + 读 `.tscn` 验证）——**迁移源静默忽略它**。
  - **`not_found` 文案修复其实是承重的**：实施者起初声称「无活调用者」，**被独立验收推翻**——
    批量工具把已带后缀的消息再送进 `not_found`，线上真出现 `... not found not found`；修好并**撤回**原主张，
    同时把门脚本里**空转的行内 grep** 换成**基于响应的精确消息 + 计数断言**。
- **批准实施者自行做出的 3 项决策**（其无法联系到人，报告里记录了被否决的替代方案）：
  D1 批量新增**全成功/全回滚**（**否决**迁移源的部分成功：会让「报成功但只做一半」可表示）；**批准**。
  D2 属性批量写作用集 = 所有 `get_class()==type || is_class(type)` 的节点（自然前序、确定），
  **任何写入之前**校验匹配与属性存在，否则 `-32001`，并保存旧值以便中途失败回滚；**批准**。
  D3 单个串行实现者；**批准**（与 D48 一致）。
- **⚠️ 新发现的诚实性缺口：静默写入错误的值**。`editor_set_node_property_batch`、`editor_add_nodes_batch`
  与**既有** `editor_set_node_property`（共享强转路径）对布局不兼容的值（如给 `position` 传 `1e20`）
  **返回 `status: ok` 却静默写入 `Vector2(0,0)`**。实施方正确地上报而未自行改动。
  - **裁决：必须修**（与 M2 的 D-1 同类：「**静默写错值并报成功**」）。口径沿用 `PLAYBOOK` §6.2 / TASK-010：
    **越界/不兼容一律 `-32602`**；批量路径须在**任何写入之前**捕获（保持全成功/回滚）；须有
    「线上 `-32602` + 读回证明未被改动」的证据。属**对已验收工具的行为变更**，报告须显式列影响面。
  - 排入 **TASK-018 第一部分**。
- **门脚本去硬编码（采纳实施方建议）**：`accept_m1.ps1` 的 `$ToolNames` 是硬编码并集，每批手工追加（已改 4 次）→
  改为**从 manifest 的 `implemented=true` 组派生**（必要时按映射 `scope` 逐端点过滤），
  并要求「派生结果与硬编码清单**逐名 diff 为空**」的证明。排入 TASK-018 第二部分。
- **接受为已知覆盖缺口（不修）**：导航/光照/物理的**正例**只有线上证据（doctest 进程无物理服务器/导航全局，
  某些正向构造会崩）→ 仅跑 doctest 的 CI **抓不到**这类回归，已显式声明；`REPORT-017` 三处纯文案精度问题不返工。
- **下一批（TASK-018）**：B3 收官 **10 个工具**（6 组）+ 静默错值修复 + 门脚本去硬编码。
  其中 **UID 方向对**（`convert_path_to_uid` ⇄ `convert_uid_to_path`，token 集合相同仅次序相反）要求演示
  「按契约描述能否可靠二选一」，并给出「方向搞反会**静默返回错映射**」的对照证据。
- 回滚点：本批可整提交回退；manifest 为数据文件。

## D67 — **B3 收官 40/40（已实现 106/171）**；门脚本去硬编码成功；P-1..P-4 裁决

- 日期：2026-09（已实现 **106/171**；编辑器端点 89 / 游戏端点 48；剩 B4 7、B5 58）
- **TASK-018 交付**（B3 最后 10 工具 + 静默错值修复 + 门脚本去硬编码），门在代码冻结 `37f8bcb0e1` 上全绿：
  门① 六组各 **3/3**；门② **104/104**；门③ doctest **168/168·6610**；门④ 全引擎 **1594/1594·430892 断言 0 failed**；
  门⑤ `accept_m1.ps1` **22/22 ×2**（PASS 清单 diff=0）。
  - **静默错值已修**（D66 裁决落地）：`coerce_to_property_type` 增加 **`Variant::can_convert` 门**
    （唯一一处、位于 `Object::set()` 之前）→ 布局不兼容值一律 `-32602`（消息含目标类型、值拼写、
    以及**引擎本会写入的值**）；`write_node_property` 拆成**校验 + 写入 + 回读**；批量路径**在任何写入前**逐节点预校验。
    线上证明：**场景 `.tscn` 前后 sha256 相同**；合法值回归覆盖 `Vector2`/`Vector3`/`float`/`int`/`Color`/`String`。
    **受影响（行为被改变的既有已验收工具）**：`editor_set_node_property`、`editor_set_node_property_batch`、
    `editor_add_nodes_batch`、`running_game_set_node_property`、`editor_add_resource_to_node_property`、
    `project_create_resource`、`project_edit_resource` —— 全部由「静默错值」变为「`-32602`」。
  - **门脚本去硬编码成功**：`$ToolNames` 从**5 个 manifest 的 `implemented=true` 组**派生；
    证明用 `git show ddb585d888:` 取**基线提交**（不用工作树副本，避免自证）：基线字面量 96 与基线 manifest 派生 96
    **逐名 diff 为空**，工作树派生 106 = 旧集 + 本任务 10 个；新脚本**引号工具名计数 0**（旧 96）；未削弱任何断言。
    → **后续批次不再需要改门脚本**。
  - **B3 = 40/40**：12/12 组 implemented、40/40 在线于 9888；9889 按 `scope` 恰好 8/8 且 **32 个 editor-scope 工具一个不漏**；
    `check_tool_groups.py --batch B3` 与 `--check-completeness` 均 exit 0。
  - **线上实测又抓到两个真问题**：①编辑器侧 `editor_execute_gdscript` **全部** `-32602 "does not compile: OK"`，
    根因 `GDScript::can_instantiate()` 在编辑器运行时**拒绝非 `@tool` 脚本** → 生成源改带 `@tool`
    （**游戏侧逐字节不变**），并把「编译失败」与「不可实例化」拆成两种诚实消息；
    ②本 fork 的 **`Variant::construct_from_string` 是空壳** → `"Vector2(…)"` 字符串语法**从未生效**
    （旧实现把它**静默写成零向量**，现为 `-32602`）。
- **P-1..P-4 裁决**：
  1. **P-1**：**不修引擎核心**（超范围且会让 fork 分叉）→ **删除** `property_value_from_json` 里**已死的字符串语法分支与注释**，
     注明「字符串→Vector/Color 在此 fork 不可用，请传结构化对象」，补 doctest 断言其 `-32602`。排入 TASK-019 §2。
  2. **P-2**：`project_set_setting` **允许新建键并报 `created:true`** —— 该报告是**诚实的**（确实创建了）；不视为缺陷。
  3. **P-3**：代码上限保留；**无超时是已知限制** —— 模块单线程运行在主线程、**无法在主线程内中断 GDScript**，
     **不引入伪超时**。记录为已知限制，不假装有超时。
  4. **P-4**：`editor_set_node_script` **不需要 UndoRedo**（编辑器 UX 增强，非正确性；记为非目标）。
- **下一步：TASK-019 = B4 全部 7 个工具 + P-1 清理** → 完成后 **M4 = B3+B4 = 47/47**。
  B4 是「**游戏可玩性自动判定**」工具族（`assert_node_state`/`assert_screen_text`/`run_test_scenario`/`run_stress_test`/
  `watch_signals`/`compare_screenshots`/`editor_get_test_report`）——**M2 解锁的 E3 在此完整**：
  要求「从 9889 发起：启动 → 注入输入/等待 → 断言状态与屏幕文本 → 结构化 pass/fail 结论」，
  且**必须含一个故意失败的场景**以证明它真会报 fail。`editor_get_test_report` 是 D45 fix-first 中**第 4 个**。
- 回滚点：本批可整提交回退；manifest 为数据文件。

## D68 — **M4 收官（B3+B4 = 47/47，已实现 113/171）**；门脚本陷阱入库；派 M4 独立验收

- 日期：2026-09（已实现 **113/171**；剩 **B5 58**）
- **TASK-019 交付**（B4 全部 7 个工具），三组门① 3/3；门② **66/66**；门③ doctest **175/175·7122**；
  门④ 全引擎 **1601/1601·431404 断言 0 failed**；门⑤ `accept_m1.ps1` **22/22 ×2**（PASS 清单相同）；
  9877 PID 36392 未动；`--version == HEAD`（`a63583c6a`）已校验。**B4 = 7/7、M4 = 47/47 机器校验通过。**
- **第 4 个 `fix_implementation_first` 修掉（`editor_get_test_report`）**：迁移源**从未收集任何结果**、
  恒返回固定文案 + `available_commands` + `note`。现在返回**真实累加器**
  （`total/passed/failed/pass_rate/all_passed/no_results/details`），由两个断言工具与场景运行器**写入**；
  `clear` 拼错 → `-32602`。红证据：空累加器契约 + 线上 `C1`（`no_results:true`）与 `C2`
  （`message=False available_commands=False note=False`）；并证明**四个游戏进程的断言不会泄漏进编辑器进程的累加器**。
- **场景运行器（E3 的自动化判定载体）**：从 **9889** 发起 →
  ①应通过场景 `all_passed=true`、`total_steps=4`；②**故意失败场景** `all_passed=false`、`failed=2`，
  **每个失败步骤带 `expected`/`actual`/`reason`/`resolved_node_path`**（这就是「判定是**算出来的**而非编造的」的线上证明）；
  ③空步骤/未知步骤类型/`scene_path` 前置拒绝为 `-32602`。`run_stress_test` **刻意没有 `passed` 字段**（不给假判定）。
- **又修了一个实测缺陷**：期望值归一化——`{"x":3,"y":4}` 与 `Vector2` 属性比较时**报 `passed=false` 却打印两个相同的值**。
  另：`assert_screen_text` 现在读**真实 Control 树文本**（迁移源读的是它自己的收集器**从未写入过**的键）并支持 `case_sensitive`。
- **两条门脚本陷阱写入 `PLAYBOOK` §7**（都造成过假 PASS/假红）：
  1. **「工具是否在线」不得用 `-match`/文本包含判断** —— 契约 `description` **会互相按名引用**
     （如「要扁平形态请用 `editor_list_signal_connections`」），必须**解析 `tools/list` 的 `name` 字段**做集合判断；
  2. **断言/期望值必须先与引擎实际语义对齐**（上述 `Vector2` 表示形式缺陷）。
- **三条引擎事实（待后续批次共用；暂记在报告与代码注释）**：
  ①`Node::has_method("get_signal_list")` 为 `false`，而 `Object::get_signal_list()` 是**私有**；
  ②`CallableCustom` 由 `Callable` 的引用计数持有；③`Array` 赋值是**引用**而非快照。
- **计数订正（不是新增，而是修掉上一批的陈旧值）**：编辑器端点可见数 `97 → 91`、游戏进程的编辑器视图 `45 → 31`；
  本批实测注册表总数 **113**（editor 60 / both 31 / game 22），游戏进程注册表 53。
- **M4 独立验收已派发**（`TASK-AUDIT-M4`）：覆盖 B3+B4 共 **47** 个工具，分七类判定，
  要求验收方**自己解析 `tools/list` 的 `name` 字段**（明令禁止 `-match`）、
  自己核实「4 个已修 fix-first 真的做到、剩余 3 个 + 2 个 unregister 仍未注册」、
  自己构造静默错值/批量事务/多场景/UUID 方向的反例，并证明 **9877 未被占用、门脚本确实已无需手工改**。
- **下一步（M5 = B5 58 个工具 + hof-rs 切端点 + 真实 T=1 冒烟）**：B5 是最后一批（26 组/58 工具），
  按 ~10 工具一批推进（约 5–6 批）。**注意：hof-rs 仍处用户指令的暂停状态（D43）** ——
  「hof-rs 切端点 + 真实 T=1 冒烟」须在**解除暂停后**进行；我推进到该步时会**先向用户确认**，不擅自恢复。
- 回滚点：本批可整提交回退；manifest 为数据文件。

## D69 — **M4 独立验收判 `fail`**：我 D67 的闸门设错了层级；回到阶段四修

- 日期：2026-09（验收基准：验收方**自己重建**的 HEAD 绑定二进制 `5ece15100`）
- **M4 验收结论**：`verdict = fail`。**六类 pass**（全量对等 / 安全与事务 / 延迟通道 / 工程门 / 端口纪律 / fix-first 现状），
  **三类 fail**（诚实性 / 行为一致 / 工程门中的部分项）。这**再次证明里程碑级独立验收的价值**：
  它自己解析 `tools/list` 的 `name` 字段（明令禁止 `-match`）、自构造反例，抓到了我自检**结构上无法覆盖**的缺口。
- **缺陷 D-1（high）：复合属性的「分量」绕过静默错值闸门。**
  `position`（`Vector2`）传 `{"x":"abc"|"NaN"|null|{"z":9}|[1,2]}` → **`code=0`（成功）**，`position.x` 被**静默写成 `0.0`**。
  根因：`tool_helpers.cpp:599-607` 的 `property_value_from_json` 在 DICTIONARY 分支**递归时传 `Variant::NIL`**，
  分量**从未经过** `can_convert` 门；而门只作用于 **dict→Vector2 整体**（该整体转换在引擎里**是允许的**）。
  → **我 D67 的修复只做了「整值级」，漏了「分量级」**：这是**闸门设错了层级**，不是小疏忽。
- **缺陷 D-2（high）：`STRING→FLOAT/INT` 放行无法解析的字符串。**
  `rotation="abc"` → `code=0`、读回 `0.0`（`can_convert(STRING,FLOAT)=true` 但 `type_convert("abc",FLOAT)=0.0`）；
  该缺口**同时使 FLOAT 分支的 NaN/Inf 守卫对字符串输入失效**。
- **缺陷 D-3（medium）**：两个独立断言工具（`running_game_assert_node_state` / `assert_screen_text`）失败时**不带 `reason`**，
  而**场景运行器内同一断言有 `reason`** → 两入口字段集不一致。
- **⭐ 最重要的一条教训（已写入 `PLAYBOOK` §3）**：**自检的证据形态必须能区分「拒绝」与「按引擎语义写默认值」。**
  D67 的自检用的是「读回值 vs 请求值 + 场景 sha256 不变」，而
  「引擎按语义写入默认值」**同样**让读回值 ≠ 请求值 —— 于是同一方法**结构上不可能**发现 D-1/D-2。
  新证据形态硬要求：**错误码 + 前后 sha256 相同 + 旧值仍为旧值**（用另一个读工具明确断言「未被改动」），
  且每个反例要覆盖 **整数/浮点/字符串/复合/数组/dictionary/null 六类 + 批量路径**。
- **另一条门配置教训**：验收方开工时 `--version` 校验**通过**（因为用仓库根的未跟踪 `build-m0.cmd` 建出的二进制版本串也是 HEAD），
  但该脚本**不传 `tests=yes`**，导致 `--test` **直接 abort** → 门必须一律用
  **`modules/mcp_server/scripts/build_local.cmd`**。已写入 `PLAYBOOK` §3。
- **其他已记录的验收发现（接受）**：`--import` 首次导入**偶发** `0xC0000005`（脚本 3 次重试，第 2 次成功）→
  可能污染「只导入一次」的自动化，记为风险；`editor_list_signal_connections` 的 `count` **包含编辑器自身内部连接**
  （契约明文如此）→ 极易造成「连接数为 0 才算过」的**假红**，正确判据是**按 source/signal/target/method 精确计数**；
  `DESIGN-DETAIL` §17.3 措辞与实况的**对称 scope 规则**不相容（判为**文档措辞**问题，非实现缺陷）。
- **处置：回到阶段四**（TASK-020），派**全新**实现子代理修 D-1/D-2/D-3，并：
  ①补出新的**证据形态**；②**显式列出**受 D-2 行为变更影响的工具清单；
  ③修正 §17.3 措辞（只改措辞、不改规则）；④补跑验收方未能完成的两项
  （跨场景**坏文件**事务跑透、`editor_analyze_screenshot_diff` 的真实 PNG 对）。
  修完**必须由另一个全新验收子代理按同样的对抗性反例复核**（尤其那五种分量值）。
- **对总进度的判断**：已实现 **113/171** 的机械层（对等/scope/契约逐字）是**坚实的**（本验收与 M2 都独立证实），
  fail 集中在**值转换的诚实性**这一条线上；因此**不推倒重来**，只修这条线并让 B5 沿用新的证据形态。
- 回滚点：修复本身可整提交回退；§17.3 为文档。

## D70 — TASK-020 交付（D-1/D-2/D-3 已修 + 新证据形态）；同类残留面先补齐再复核

- 日期：2026-09（已实现仍 **113/171**；本任务是**修复**而非新增）
- **TASK-020 交付**，五道门在源码提交 `576e19c3fc` 绑定的二进制上全绿：
  - ①契约子集 3/3；②证据 **67/67**（**修前同一脚本 29 pass / 32 fail**，对比强烈）；③doctest **179/179·7312**；
    ④全引擎 **1605/1605·431594 断言 0 failed**；⑤`accept_m1.ps1` **22/22 ×2**（PASS 清单 diff=0）。
- **三缺陷修法**：
  - **D-1**：闸门落在**真正折叠分量**的 `shape_vector_from_json` —— 新增**分量表**
    （`Vector2/3` 分量为 `FLOAT`、`Vector2i/3i` 为 `INT`、`Color.r/g/b/a` 为 `FLOAT`），
    每个分量**先经同一道 `coerce` 判定**再折叠（参数名带 `value.x`），不合规 `-32602` **且写前拒绝**。
    > **实现方纠正了我在任务书里写的根因**：我把它归到 `property_value_from_json` 的 DICTIONARY 递归，
    > 但实测 **`can_convert(DICTIONARY, VECTOR2)` 是 `false`** —— 真正的折叠点在 `shape_vector_from_json`。
    > 这是**第二次**由执行者纠正我的技术判断（第一次是 105 vs 103 的算术），记在案。
  - **D-2**：`STRING→FLOAT/INT` 增加「**整串可解析 + 有限 + `int64` 范围**」判定；`#rrggbb` 的 `Color` 特例保留。
    实现方**比字面更严**：`INT` 目标拒绝小数拼写 `"1.5"`（修前经 `String::to_int` 得 `1`）。
  - **D-3**：整份断言 verdict 下沉为**共享字段集**（`node_state_assertion_fields` / `screen_text_assertion_fields`），
    工具入口与场景运行器**共用**，失败字段集**逐键相同、`reason` 逐字节相同**。
- **证据形态（新硬要求）已落地**：每个反例**三条同时**覆盖 —— ①`-32602` 且 `result` 为 null；
  ②反例前后 `scenes/main.tscn` **sha256 相同**；③**另一个读工具**断言旧值未变（`9888` 与 `9889` 各一）。
  批量路径另加 `batch.status=rolled_back`、节点未泄漏、sha 相同。
- **两项补验通过**（M4 验收未能完成者）：①跨场景「**好文件 + 坏文件**」全或无 —— 坏文件在场时
  `code=-32000`、`data.scenes.errors=[{scene, reason:"not a loadable PackedScene"}]`、
  suggestion 含 `Nothing was written`、两个好文件 sha 前后相同；移除坏文件后两文件都写入并可读回；
  ②`editor_analyze_screenshot_diff` —— 引擎自写 4×4 PNG：相同图 `identical=true/diff_percentage=0`、
  不同图 `identical=false/changed=1/diff_percentage=6.25`、`threshold=255` 掩蔽、`=0` 保留、
  `300`/`-1` → `-32602`、缺 `image_a` → `-32602`。
- **`DESIGN-DETAIL` §17.3 措辞已修正**（只改措辞、不改规则；门脚本 sha256 未变）。
- **受影响工具清单（9 个，行为从「静默错值」变为 `-32602`）**：`editor_set_node_property`、
  `editor_set_node_property_batch`、`editor_add_nodes_batch`、`running_game_set_node_property`、
  `editor_add_resource_to_node_property`、`project_create_resource`、`project_edit_resource`、`project_set_setting`
  （以上 8 个**线上实测**）、`project_set_node_property_across_scenes`（共享点**推导**）。
- **决策者裁决：同类残留面先补齐，再让全新子代理复核。**
  实现方主动列出**同一缺陷类的残留面**：`STRING→BOOL` 的可解析性、**容器元素位宽**
  （`PackedByteArray`/`PackedInt32Array` 等）、`PackedVector4Array` 的元素整形。
  → 若直接派复核，复核只会把它们当**新缺陷**再报一遍、多花一轮；**先补齐同类面**（**TASK-021**）更省，也更彻底。
  TASK-021 另要求：**通读并列出所有「转换失败 → 退化成默认值 → 报成功」的路径清单**，逐条判定修/不修 + 理由，
  并断言「同类面已清零（含自查范围说明）」。
  修完后**由全新的验收子代理按 M4 的同样对抗性反例复核**（尤其五种分量值与字符串值）。
- `--import` 首次导入**偶发** `0xC0000005`（3 次重试、第 2 次成功）仍作为**风险**记录，
  并要求证据脚本保留重试与退出码校验。
- 回滚点：TASK-020/021 的改动各自可整提交回退。

## D71 — TASK-021：静默错值**同类面已清零（在自查范围内）**；两条原则入规范；派 M4 复核

- 日期：2026-09（已实现仍 **113/171**；本任务是修复）
- **TASK-021 交付**（5 个同类面全部「修前红 + 修后绿」），门在源码提交 `de04c86f4c` 绑定的二进制上全绿：
  门① 3/3；门② **74/74**（**修前同一脚本 40 pass / 34 fail**）；门③ doctest **184/184·7509**
  （红：184/179、5 失败、123 断言失败）；门④ 全引擎 **1610/1610·431791 断言 0 failed**；
  门⑤ `accept_m1.ps1` **22/22 ×2**（PASS 清单 diff=0）。9877 全程 PID 36392 未动。
- **闭合的 5 个面**：
  1. **`STRING→BOOL`**：`booleanize` 语义下**非空串即 `true`** → `"abc"`/`"false"`/`"0"` 曾**静默写 `true`**；
     现只接受 `"true"/"false"/"1"/"0"` 并**写拼写所指的值**。
     > **有意偏离引擎语义**：`"0"` 映射为 `false`（引擎 `booleanize("0")` 是 `true`）——
     > 理由是「把 `"0"` 写成 `true`」**本身就是**我们要消灭的静默错值；已用 doctest 与线上双重钉住。
  2. **packed 元素位宽**：`Byte 300→44`、`-1→255`、`Int32 3e9` 截断、`Float32 1e300→inf`、`1e-300→0` → **越界一律 `-32602`**。
  3. **`Vector4` 补进分量表**（`PackedVector4Array` 与其他向量数组同机制）。
  4. **分量槽位宽**（同族**下层**）：`real_t`（单精度构建的 `float`）槽与 `Vector2i/3i` 的 `int32` 槽，
     `{"x":1e300}`、`{"x":3000000000}` 曾**静默收窄** → 现按槽位宽判定。
  5. **通读代码新发现 `STRING→COLOR`**：`Color(String)` 对读不出的串**回黑**，`"notacolor"` 曾写黑 →
     现按 `html_is_valid`/`find_named_color` 判定。
- **完整路径清单（18 行）**：报告 §3 逐条给出「修 / 不修 + 理由」。
  **不修**的是**声明的确定性转换**（写入 `String` 目标时的字符串化、未知向量成员被忽略、整值 `FLOAT→INT` 截断、
  `INT→COLOR` 的 `Color::hex`、`property_value_from_json` 的 NIL 递归、读方向 `serialize_variant`）——
  它们**不是**「失败 → 默认值」这一类。**自查范围**（JSON 可达的源类型只有 `NIL/BOOL/INT/FLOAT/STRING/ARRAY/DICTIONARY`）
  已在报告中显式声明；`OBJECT/RID/CALLABLE` 的算子分支**不可达**。
- **两条原则入 `PLAYBOOK` §7**：
  1. **「失败 → 默认值 → 报成功」分两层判定**：「**声明的确定性转换**」不算该类但**必须逐条声明**；
     「**槽位宽**」（`uint8`/`int32`/`float`/`real_t`）**必须与「转换关系」分开判定** ——
     `can_convert` 为真**不代表**值能落进槽位（已实证六种收窄/截断）。
  2. **本 harness 的 doctest `REQUIRE` 不会中止用例**（`tests/test_macros.h:44`）→
     `REQUIRE` 之后的**每次读取/索引都必须自己守卫**，否则会以「读到空值」产生**假绿**。
- **待记录（不阻塞）的读数形状不一致 O-1**：`Vector4`/packed 向量的**读回形状是 `String`**，而 `Vector2` 是**对象** →
  这是**读数形状**不一致（不是静默值），但会让消费者困惑。**裁决**：**记入规范并排在 B5 之后统一**，
  不在本轮修（避免在 B5 前扰动已验收的读数形状）；若 B5 之后仍有预算则做一次统一。
- **O-3 裁决**：整值 `FLOAT→INT` 截断**保持**（属声明的确定性转换）。
- **处置：派全新的验收子代理复核 M4**（第二次验收），并把首轮判 `fail` 的三个缺陷与 TASK-021 的五个面
  **显式列入其对抗性范围**（要求用**同样的**五种分量值/字符串值复核，并**自己再找同族新面**）。
- 回滚点：TASK-021 改动可整提交回退；两条原则为文档。

## D72 — M4 复核**仍 fail**：「槽位宽」已被漏三次 → 改为**统一收窄闸门**；D-5/D-6 裁决

- 日期：2026-09（复核基准：验收方**自己重建**的 HEAD 绑定二进制 `08f0bd529`）
- **M4 第二次验收结论**：`verdict = fail`，**六类中 pass**（全量对等 / 安全与事务 / 延迟通道 / 工程门 / 端口纪律 / 首轮三缺陷已闭合），
  **诚实性与行为一致 fail**。**首轮 3 缺陷 + TASK-021 的 5 个面经对抗性复核确认闭合**（含五种分量值与字符串值，
  用两个独立读工具 + sha 相同判定），且验收方**自建了全新 harness**（未复用首轮脚本，197 条检查）。
- **⭐ D-4（high）：标量 `real_t` 槽位宽未判定 —— 「槽位宽」这一类已被漏了三次。**
  `rotation=1e300`/`3.5e38`/`"1e300"` → `code=0` 写 **`inf`**；`1e-300`/`1e-46` → 写 **`0.0`**；
  **5 条写路径复现**，其中 `project_set_node_property_across_scenes` **真的把 `rotation = inf` 落进 `.tscn` 并回 `Applied`**。
  漏的三次是：①容器元素位宽（A-2）→ ②分量槽位宽（A-4）→ ③**标量槽**（D-4）。
  → **裁决：停止逐类打补丁**，改为**一处统一的「收窄闸门」**：判定「这个 Variant 能否无损落进目标成员」，
  覆盖 `double→float`（溢出为 `inf`、非零下溢为 `0`）、`int64→int32/uint8`、容器元素、向量分量、packed 元素，
  并把它与既有 `can_convert`/可解析性/有限性**串成同一条链**；**5 条写路径必须复用同一处**、**任何写入之前**判定。
  这条**教训本身**比缺陷更重要：**逐类枚举的补丁策略在结构上注定继续漏**。
- **⭐ 证据形态再次升级（旧形态对 D-4 结构性假绿）**：M4b 实测证明旧形态看不见 D-4 ——
  未 save 时 sha 恒同、值真被改时无旧值可读、读工具对 `inf` 返回 `null`。
  → 新形态**四条同时**满足：①`-32602`；②**响应回显值必须有限**（不得用 `inf`/`nan`/`null` 掩盖）；
  ③**显式保存后扫描文件字节**，`.tscn`/`.tres`/`project.godot` **不得含 `inf`/`nan`**；
  ④另一读工具读到旧值未变，**并说明该工具对本例为何有效**（对 `inf` 返回 `null` 的工具**不能**单独作证）。
- **D-5（medium）裁决：修。** `project_create_resource` 的 `properties_set` **未回读校验** ——
  `Curve.min_value=5.0` 与 `1e300` 都返回 `code=0` + `properties_set:["min_value"]`，而文件里 `_limits` 仍是 `[0.99, 1.0, …]`
  （引擎 setter 在 `min_value > max_value` 时**静默忽略**）；同族的 `project_edit_resource` **反而真回读**（`changed:{old,new}`）。
  → 统一为**回读形状**：「报成功必须以回读为据」，被引擎静默忽略的属性要**如实报告**（不列为已设置，或标 `ignored`）。
- **D-6（medium）裁决：采用「文件桥接」，不改契约。** `editor_get_test_report` 是 editor-only，
  而 `record_test_result` 的**三个调用点全在 `scope=game` 工具**里 → 客户端在任何可达端点**恒见 `total=0`**，能力不可达。
  → **游戏进程把断言报告原子持久化到 `user://`**，由**编辑器侧的 `editor_get_test_report` 读该文件**
  （正是迁移源当年的文件 IPC 做法）：既让能力**真的可达**，又**不动契约/映射/不新增工具**；
  文件缺失/为空必须**诚实**返回，**不得伪造 `total`**；返回需带 `source` 与文件路径/时间戳。
- **另一条工具改进（采纳验收方建议）**：`scripts/build_local.cmd` 增加 **`-Force`**（删陈旧 `test_*` 对象后重建），
  并在注释里写明「改 `tests/*.h` 后不加 `-Force` 可能跑旧用例产生**假绿**」。
- **处置：TASK-022**（全新实现子代理）——统一收窄闸门 + 四条证据形态 + D-5 回读形状 + D-6 文件桥接 +
  `DESIGN-DETAIL` 新增 **GDR-22**（槽位宽覆盖标量成员 / 统一收窄闸门 / 声明的确定性转换不属该类）+
  `build_local.cmd -Force`。修完**再由全新验收子代理复核**（第三次），并要求其：
  用**同样的**反例矩阵、把**落盘文件不含 `inf`/`nan`** 作为显式条款、并**自己再找**同族新面。
- **对总进度的判断（保持不变）**：机械层（对等/scope/契约逐字）稳定；
  fail 仍集中在**值转换的诚实性**这一条线上，故继续**只修这条线**，B5 开工时**必须沿用最新证据形态**。
- 回滚点：TASK-022 改动可整提交回退；GDR-22 为文档。

## D73 — TASK-022 交付：**统一收窄闸门**（D-4）+ D-5 回读 + D-6 文件桥接；待第三次复核

- 日期：2026-09（已实现仍 **113/171**；本任务是修复）
- **交付**（3 个提交；门在 HEAD 绑定二进制 `bb82ecc0…` 上全绿）：
  - **D-4 统一收窄闸门**：`MCPTools::ValueSlot{ WIDE, REAL_T, INT32, UINT8 }` +
    **唯一判定** `value_fits_slot(...)`；`coerce_to_property_type` 在**类型转换成功后、任何 `Object::set()` 之前**判定；
    **TASK-021 的两处分散判定（元素、分量）函数体已删除、改为调用同一处**；5 条写路径全部复用。
    覆盖 `double→float32` **溢出与非零下溢**、`int64→int32/uint8`、容器元素、向量/颜色分量、packed 元素、标量成员。
    **诚实边界（GDR-22 §20.3，显式声明）**：标量 **INT 成员**的 C++ 宽度**在 `PropertyInfo` 里不可见**，
    故保持 `WIDE`，由**写后读回真值**保诚实（不靠猜宽度）；这是**唯一未判的收窄面**。
  - **D-5**：`project_create_resource` 改为**真回读** —— `changed:{<prop>:{old,new}}`，
    `properties_set` **只含「回读值 = 请求值」**的属性，其余进 **`ignored`**（`requested`/`stored`/`reason`）。
    实测 `Curve.min_value=5.0` → `properties_set=[]` + `ignored` 齐全；正例 `0.25/0.75` → 两项入 `properties_set`。
  - **D-6 文件桥接**：`record_test_result` 每次更新后**原子写** `user://mcp_test_report.json`；
    `editor_get_test_report` **优先读该文件**并回 `source=game_process_file` + 路径 + 写入时间戳；
    缺失/空/坏 JSON → `source=editor_process`、`report_file_present=false`、`report_unavailable_reason`、
    `no_results=true`（**绝不伪造 `total`**）；`clear` 同时清编辑器累加器并删除桥接文件，`cleared` 说明**真实范围**
    （**不声称**清了游戏进程内存）。线上实测：游戏侧两个断言（一过一失败）→ **9888 读到 `total=2/passed=1/failed=1` 与明细**。
  - **GDR-22** 写入 `DESIGN-DETAIL` §20（判据 / 落点与调用点 / 覆盖清单 + 诚实边界 / **不属该类的确定性转换** /
    **四条证据形态** / 资源写后回读 / 跨进程可达性）；`build_local.cmd` 增加 **`-Force`**
    （注释写明「改 `tests/*.h` 后不加 `-Force` 会跑旧用例产生**假绿**」）。
- **证据形态四条（新）已落地并自证**：①`-32602`；②**拒绝响应无值回显**（旧缺陷形状 `code=0 + new_value=1e99999` 被明确排除；
  诊断文本里点名「引擎实写 `inf`/`0`」**不算**回显）；③**显式保存后扫 `.tscn` 字节**：无 `inf`/`nan`/`1e99999` 且 sha256 相同；
  ④**另一读工具双读**（模块读 + GDScript 求值）旧值未变。**89/89** 覆盖 **5 条写路径 × 反例矩阵**。
- 门：①契约子集 3/3（9888=91 / 9889=53 / 契约 171 逐字）；②**89/89**；③doctest **190/190·7716**（红阶段 3 用例 71/103 断言失败）；
  ④全引擎 **1616/1616·431998 断言 0 failed**；⑤`accept_m1.ps1` **22/22 ×2**（PASS 清单 diff=0）；
  9877 全程 PID 36392 未触碰；未 push。
- **接受的关键偏差**：跨场景路径 `project_set_node_property_across_scenes` 的**值级拒绝外层是 `-32000`**
  （该工具契约的全成功/全回滚信封），`-32602` 语义在 `data.scenes.errors[].reason` 内 —— **四条证据形态仍成立**；
  `project_set_setting` **显式传 `WIDE`**（`ProjectSettings` 以 `Variant` 存储，按成员规则会**误拒**可存储的大浮点）。
- **下一步：第三次 M4 复核**（全新子代理），要求：用**同样的** 5 路径反例矩阵、
  把「**落盘文件不得含 `inf`/`nan`**」作为**显式条款**、复核 D-5 的 `ignored` 判据与 D-6 的跨进程数字与诚实空，
  并**自己再找**同族新面（尤其 `Vector4i`/`Rect2`/`Transform2D` 的分量宽度、窗口化截图分支）。
  另建议下轮抽样**资源类型的 setter 归一化**（`Environment`/`CameraAttributes` 等），
  检验 `ignored` 判据是否会把「故意归一化的 setter」误标。
- 回滚点：TASK-022 改动可整提交回退；GDR-22 为文档。

## D74 — ⭐ 参考源层级更正（用户指令）：**引擎源码是第一参考源**；迁移源只是「类别与用途」参考

- 日期：2026-09
- **用户指令**：「迁移源**不是完美预言机**，只是一个**工具类别**和**工具有哪些功能**的参考；
  **工具怎么使用顺手**是要**根据引擎源码**作为**第一参考源**。」
- **这条推翻了本项目此前的一条隐含前提**：我们一直把迁移源当作**行为预言机**
  （手册原文：《读迁移源：写出该工具的可观察契约》，把「与参照不同」当作**需要记录理由的偏差**）。
  代价是**系统性**的两类：
  1. **它的缺陷被当成规范**（已实证 7 例，见 `PLAYBOOK` §6.6）；
  2. **它的怪癖被当成要保留的行为** —— 手册原 §6.8 甚至**明文要求保留怪癖**（「不得顺手修好」）。**现推翻该条。**
- **新规范（已落地）**：
  1. **`DESIGN-DETAIL` 新增 §21 / GDR-23**：引擎源码（`core/**`、`scene/**`、`editor/**`）为**第一参考源**；
     迁移源只回答「**有哪些类别的工具**」「**大致干什么**」；**与迁移源不同是常态**
     （只需①有引擎依据②报告记录）；**「与参照一致」不是优点，「照抄参照的怪癖」是缺陷**；
     **怪癖不再默认保留**（只有引擎只能如此时才保留）；契约仍是名字/描述/schema 的对等门，
     需改参数形态就**走既有 override 机制并重生成指纹**。
  2. **`PLAYBOOK` §1/§2**：必读表把「**引擎源码**」列为**第一参考源**、迁移源降为「**仅类别参考**」；
     工作流第 2 步改为「**先读引擎**设计顺手的调用形态，**再读迁移源**只为确认类别与用途」；
     报告格式新增「**引擎依据**」列。
  3. **`PLAYBOOK` §6 总纲 + §6.10**：**顺手性（ergonomics）正式成为验收条款** ——
     工具必须让调用方**一趟做完引擎一趟能做的事**、参数取引擎自然形态、返回字段**可链式喂回**；
     要求调用方做「多步舞蹈」换取引擎一次调用即可给出的结果，**算缺陷**（minor 起），
     并须附「引擎本来能做到什么」的证据。
- **⭐ 由此产生的「顺手性清账清单」（此前被当成可接受，现按 GDR-23 重新排队）**：
  | # | 项 | 现状问题（引擎明明能更好） | 优先级 |
  |---|---|---|---|
  | E-1 | `project_get_scene_dependencies` 的 `type` **恒为空串** | 迁移源怪癖被**明文保留**；引擎可直接给出资源类型 | 高 |
  | E-2 | `editor_get_scene_tree` 路径含**每次运行都变的编辑器内部节点 id**（`@EditorNode@<id>`） | 非确定、不可复现、不可跨调用链式使用 | 高 |
  | E-3 | `Vector4`/packed 向量**读回形状是 `String`**，而 `Vector2` 是**对象**（M4b 的 O-1） | 同一类值两种形状，消费者要分支处理 | 高 |
  | E-4 | `assign_shader_material` **忽略 `material_slot`** | 引擎有槽位概念，工具却永远写节点 `material` | 高 |
  | E-5 | `set_shader_param` 用**复合属性路径** `material:shader_parameter/x` 直写 | 引擎有 `ShaderMaterial::set_shader_parameter`；直写是否静默失效**尚未证实** | 高 |
  | E-6 | `editor_get_errors` / `editor_get_output_log` 只读 `user://logs/godot.log` **文件** | 编辑器进程内**有 `EditorLog` 缓冲**，更即时、不依赖落盘时机 | 中 |
  | E-7 | `attach_script` 用 `node.set("script", …)` **泛写** | 引擎有脚本属性与 usage 语义 | 中 |
  | E-8 | 错误消息里**带不稳定节点 id**（`@Node@123`） | 不可复现，难以断言 | 中 |
  | E-9 | `project_read_resource` 只回 `{path,type,loaded}`（**无属性**） | 引擎能列属性；读资源却不给内容，调用方还要再走一趟 | 中 |
  | E-10 | `editor_play_scene` 不把 `--mcp-port` 传给游戏子进程 | **引擎事实**（`editor_run.cpp` 参数构造无端口），模块内**无法**修；已记入 §19.3 | 记（非缺陷） |
- **执行顺序（我的决定）**：
  1. **把「顺手性」并进第三次 M4 复核**：同一轮审计产出两份结果 —— ①D-4/D-5/D-6 是否闭合；
     ②**按 GDR-23 的顺手性清单**（E-1..E-9）逐条给**引擎源码证据**与严重度。
     这不是凑数：这些项大多落在**已验收的 B1–B4 工具**上，独立审计方按引擎源码逐条取证比我自己列更可靠。
  2. **然后开 B5（58 工具）**：每批任务书改为**引擎优先**设计（GDR-23），报告必须给「引擎依据」列与「顺手性自评」。
  3. **顺手性修复批次**按审计排序穿插在 B5 之间，优先 E-1..E-5。
- **对已完成工作的影响（诚实说明）**：GDR-23 **不否定**已交付的机械层与诚实性成果
  （对等/scope/契约逐字/静默错值闸门/断言字段统一等仍然成立），
  但它**降低了「与迁移源一致」的价值权重**：凡此前以「保留迁移源行为」为理由的裁决都要**重审**，
  上面的 E-1..E-9 就是**第一遍清账**。
- 回滚点：GDR-23 与手册改动为文档；清账项分批修复，各自可回退。

## D75 — M4 第三次验收仍 `fail`：**闸门未覆盖专用 setter 路径**（第 4 种形态）→ 转「结构性护栏」；E-10 推翻我的结论

- 日期：2026-09（验收基准：验收方用 `build_local.cmd -Force` 自建的 HEAD 绑定二进制 `50aadecca`）
- **结论**：`verdict = fail`。**六类中 pass**：全量对等（union 113 == manifest；9888=91/9889=53 与对称推导一致；
  description+inputSchema+键集**逐字 0 差异**）、行为一致（抽样 25+；**4 个 fix-first 复验确认真做到**）、
  安全与事务、延迟通道、工程门（doctest 190/190·7716；全引擎 1616/1616·431998；`accept_m1` 22/22 ×2；
  `check_tool_groups` 四项 PASS）、端口纪律（9877 全程 PID 36392）。
  **首轮/次轮的缺陷**：D-1/D-2/D-3（**真闭合**，6 反例 × 5 路径 × 四条证据形态全成立）、D-5（**真闭合**，
  与独立 GDScript 回读逐条一致）、D-6（**真闭合**，含缺失/空/坏 JSON 三种诚实空）——**均已验证闭合**。
- **⭐ D-7（high）：统一收窄闸门「覆盖全部写路径」的声明不成立 —— 同一类缺陷的第 4 种形态。**
  闸门挂在 `coerce_to_property_type` 上，因此**只覆盖走 `Object::set()` 的属性写**；
  凡「**先算出值、再调用专用 setter**」的路径**全部绕过**：
  - `editor_set_viewport_3d_camera` 的 `position`/`rotation_degrees`（`editor_write_scene_editor.cpp:149`）→
    `code=0`、回显 `"x":1e99999`、独立 GDScript 读到 `camera.global_position=(inf,0,0)`；
  - `editor_setup_world_environment` 的 `bg_color`（`editor_node_setup.cpp:128` → `:339`）→ `code=0`（`setup:true`），
    且 **`background_color = Color(inf, 0, 0, 1)` 已被 `editor_save_scene` 写进 `.tscn`**。
  - 形态变迁史：**容器元素（A-2）→ 复合值分量（A-4）→ 标量成员（D-4）→ 专用 setter 路径（D-7）**。
- **⭐ 因此本轮的处置不只是修实例，而是修「方法论」**：加**结构性护栏**（TASK-023 §3）——
  ①**收窄点清单**（全模块 `(real_t)`/`(float)`/`Color(`/`Vector2(`/`Vector3(`/`Vector4(` 逐条标注是否经闸门）；
  ②做成**可重复执行的检查脚本**（`check_narrowing_points.py`）→ **新增未标注的收窄点即失败**；
  ③写入 `DESIGN-DETAIL`（**GDR-24**：槽位判定必须覆盖不经 `Object::set()` 的专用 setter 路径）；
  ④**纳入门禁**（`PLAYBOOK` §3 新增**门⑥**），使后续批次自动生效。
  **理由**：这个类已经证明「按形状/按工具名补丁」在结构上不可持续 —— 每次补完就换个形态再来一次。
- **D-15（medium, latent）**：`value_fits_slot` 的 `REAL_T` 分支在 `#ifdef REAL_T_IS_DOUBLE` 下**无条件 `return true`**，
  而 **`Color` 分量恒为 `float32`**、**`PackedFloat32Array` 元素恒为 `float32`** → **双精度构建下同类缺陷复活**。
  → 裁决：**拆开 `FLOAT32` 与 `REAL_T` 两个槽位**（`Color` 分量与 `PackedFloat32Array` 元素恒按 32 位判）；
  本机**无法**构造双精度二进制做端到端验证 → **必须显式声明为风险登记**，**不得**声称已验证。
- **⭐ E-10：我的「模块内不可修」结论被推翻（第三次技术判断被纠正）。**
  我此前判定 `editor_play_scene` 不转发 `--mcp-port` 属**引擎事实、模块内不可修**（D62 记录、§19.3）。
  审计方找到反证：**`editor_run_bar.h:123-125`** 的 `play_*_scene(..., const Vector<String> &p_play_args)`
  与 **`editor_plugin.h:218`** 的 `virtual void run_scene(const String&, Vector<String>&)` 钩子 ——
  **编辑器启动的游戏子进程可以被注入 `--mcp-port`**。
  → **E-10 从"记录"提升为"高优先级修复"**：它使 E3 的关键流程（**从编辑器起游戏并立刻用 MCP 观察**）
  不再需要修改被测工程的 `godot_mcp/port` 设置，**直接改善 M5 的可用性**。
- **顺手性审计结果（GDR-23 首次执行）**：E-1/E-2+E-8/E-3/E-6/E-9/E-10 **六项确认为缺陷**；
  E-4/E-5 **判 N/A**（shader 工具属 B5，尚未上架；但**迁移源确有 E-4 描述的缺陷**——读了 `material_slot` 却不用、
  硬编码 `set_surface_override_material(0, mat)` → **保留为 B5 的实现约束**）；
  **E-7 前提不成立**（实现本来就用 `set_script()`，不存在泛写）。
  审计方另**自找 G-1..G-4**：**G-1** 不支持子属性路径 `position:y`/`v4:x`（引擎有 `Object::set_indexed`，编辑器
  Inspector 正用）→ medium；**G-2** `project_get_scene_dependencies` 的 `path` 是 `uid://` 而非 `res://`，
  调用方必须多走一趟转换 → medium；G-3 `editor_get_test_report` 的 `clear` 默认删共享桥接文件（多客户端）；G-4 日志工具形状不一致。
  审计方还给出**每条引擎正解 API 与行号**（`resource_format_text.cpp:919/960-968`、`node.h:573 get_path_to(root,true)`、
  `object.h:697-698 set_indexed`、`editor_log.h:182` …）—— 这正是 GDR-23 要的证据形态。
- **一条方法学建议（采纳）**：顺手性验收用「**一条链零字符串手术**」作为可执行判据 ——
  即「从起游戏到断言」的整条链中，**调用方不需要做字符串手工处理**（不需要手动拼 `uid://`→`res://`、
  不需要把 `Vector4` 字符串再解析、不需要在路径里剔 `@EditorNode@…`）。
- **执行计划（我的安排）**：
  1. **TASK-023**：D-7 + D-15 + **结构性护栏**（收窄点清单 + 检查脚本 + GDR-24 + 门⑥）+ 回归矩阵。
  2. **TASK-024**：顺手性批次 1（**E-10 优先**，因为它改善 M5 流程；随后 E-1、E-3、E-9、E-6）。
  3. **TASK-025**：顺手性批次 2（E-2/E-8、G-1、G-2、G-4、G-3）。
  4. **第四次 M4 复核**（全新子代理）：用「零字符串手术链」+ 四条证据形态 + 收窄点清单检查。
  5. 通过后开 **B5（58 工具）**，每批**引擎优先**设计；B5 里的 shader/material 族必须带上 E-4/E-5 的引擎约束。
- 回滚点：TASK-023..025 各自可整提交回退；GDR-24 与门⑥ 为文档/脚本。

## D76 — TASK-023 交付：闸门铺到专用 setter 路径 + **结构性护栏上线**（门⑥）

- 日期：2026-09（已实现仍 **113/171**；本任务是修复）
- **D-7 闭合**（且**比我的任务书更宽**）：
  - 指定点：`editor_set_viewport_3d_camera`（`position`/`rotation_degrees`/`look_at` 的每个分量、
    以及 **`fov`** —— 我把它列为「仅登记」，实现方判定它**同属收窄类**故一并挡住）与
    `editor_setup_world_environment`（`bg_color` + `ambient_color`）。
  - **实现方自己的全模块扫描又找出 11 个收窄点并全部挡住**：编辑器输入模拟的 x/y/strength 与序列、
    游戏重放向量/强度、`run_test_scenario` 的 step strength（**整场景任何注入之前**校验）、
    以及 **`running_game_find_nearby_nodes` 的 `position`/`radius`** ——
    **这是一个读工具**：`radius=1e300` → `inf` 会让「距离 ≤ inf」**匹配所有节点**，即**读的答案本身是错的**
    → 判为缺陷而非登记。这个发现**不在我的任务书里**，是执行者按「引擎优先」原则推出来的。
  - **D-7 的第二半由证据跑出来**：第一版虽然会 `-32602`，但**已经 `memnew` 了一个 `WorldEnvironment`**（场景被改动）；
    修成**先解析再创建**，并新增 doctest 断言「拒绝后 `child_count()==0`」。**这是"拒绝也要无副作用"的范例。**
- **D-15**：`ValueSlot` 拆出 **`FLOAT32`**，`judge_32_bit = (slot==FLOAT32) || (slot==REAL_T && !REAL_T_IS_DOUBLE)` ——
  **正确性与构建配置无关**；`PackedFloat32Array` 元素与 `Color` 分量改用 `FLOAT32`。
  **明确声明：本机只建了单精度二进制，D-15 未做端到端验证**（证据为源码级 + 两条「在任何构建下都必须成立」的 doctest），
  并**登记为风险**（不声称已验证）。
- **★ 结构性护栏（本任务最重要的产出）**：
  - `modules/mcp_server/scripts/check_narrowing_points.py`：扫描 `tools/**` 的
    `(real_t)`/`(float)`/`Color(`/`Vector2(`/`Vector3(`/`Vector4(`，**29 个点 / 11 个文件全部标注**，
    分类为 `gated`(14) / `pregated`(5) / `safe`(9) / `gate`(1)，**每个都带理由**；
    **新增未标注点 → FAIL / exit 1**（**红演示已在报告里记录并回退**）。
  - 钉法是 **`(文件, 标记 id, 文件内出现序)`** 而非绝对行号（第一版按行号，加一个空行就产生**假红**）。
  - **`DESIGN-DETAIL` §22 / GDR-24**：槽位判定必须覆盖**不经 `Object::set()` 的专用 setter 路径**；
    任何新增收窄点必须在清单中显式标注经过的闸门。
  - **`PLAYBOOK` §3 新增门⑥**：后续批次自动执行。
- 门：契约子集 3/3；**证据 216/0 失败**；doctest **195/195·7817**；全引擎 **1621/1621·432099 断言 0 failed**；
  `accept_m1.ps1` **22/22 ×2**；**门⑥ PASS**；**M4c 的 6 反例 × 5 路径矩阵与 D-5/D-6 段重跑无回退**。
- **接受的关键偏差（其中一条是方法论级别的）**：
  1. **保存文件的断言改用「归一化内容指纹」而非原始 sha256** —— 一旦场景含 `ext_resource`/`sub_resource`，
     引擎文本保存器**每次保存都会铸新的随机后缀**（连存 12 次 sha 从不重复），
     因此对 `WorldEnvironment` 这类用例**逐字节 sha 在结构上不可能相同**。
     字节级判据（无 `inf`/`nan`/`Color(inf`）与独立 GDScript 读回保留；**5 条 D-4 写路径仍比较真实 sha256**。
  2. **门⑥ 不覆盖 `(int)`/`(uint8_t)`**（40+ 处，绝大多数是枚举/错误码格式化）——
     其真正的值面（`PackedInt32Array`/`PackedByteArray` 元素、`Vector2i/3i` 分量）已在 GDR-22 的 `INT32`/`UINT8` 槽内，
     并在回归矩阵里重跑过。**范围声明写在报告里，不是遗漏。**
- **下一步**：`TASK-024` = **顺手性批次 1**（**E-10 优先** —— 用 `run_scene(scene, args)` 钩子转发 `--mcp-port`，
  让「从编辑器起游戏并立刻观察」不再需要改被测工程设置；随后 E-1、E-3、E-9、E-6），
  然后 `TASK-025` = 批次 2（E-2/E-8、G-1、G-2、G-4、G-3），再做**第四次 M4 复核**
  （用「**一条链零字符串手术**」作可执行判据），最后开 B5。
- 回滚点：TASK-023 改动可整提交回退；护栏脚本与 GDR-24 为新增件。

## D77 — TASK-024 **中途失败**（执行者耗尽上下文）→ 回退半成品、**拆分为单点任务**；委派完成判定的纪律强化

- 日期：2026-09
- **事件**：TASK-024（顺手性批次 1，含 E-10/E-1/E-3/E-9/E-6 五项 + 契约 schema override + 重生成指纹）
  的 workflow **返回 `report: null`**（子代理未把 schema 对象带回），且**报告文件不存在、没有任何提交**。
  检查工作树发现它**停在中途**：`tools_list.renamed.json` **已重生成**（含 `play_scene.mcp_port`）、
  `gen_renamed_contract.py` 已加 override、399 行 doctest 已加、`DESIGN-DETAIL` 已加 53 行，
  但 **`tools/**` 一行未改** → **工作树处于「契约宣告了参数、代码不接受参数」的不一致状态**（门① 必红）。
- **处置**：
  1. **先存档**半成品补丁（`%TEMP%\task024-partial.patch`，36186 B），**再把工作树回退到干净的 HEAD**
     （决策者绝不留不一致的树）。
  2. **拆成单点任务**：`TASK-024a` = **E-10 only**（含 schema override + 重生成 + 证据）；
     其余 E-1/E-3/E-9/E-6 留给 `TASK-024b`。
     判据：含「契约 override + 重生成指纹 + 引擎新行为 + 证据链」的**一项**就已接近一个执行者的上下文上限。
  3. 半成品补丁**交给新执行者当起点**，但**明确告知它是未验证的**、且**必须自己复核**
     （采纳/丢弃都要逐项说明）——**不因省事而放弃复核责任**。
- **纪律强化（两次同类事件：TASK-012 与本次）**：
  - **委派的「完成」不能只看 workflow 返回值**。`report: null` **不等于**「没干活」，
    也**不等于**「干完了」→ 必须**独立核对三件事**：①报告文件是否存在；②**是否有提交**；
    ③**工作树是否干净/一致**。三者缺一，就当**未完成**处理。
  - **绝不留下不一致的工作树**：发现半成品立即**存档 + 回退**，再派新子代理。
- **教训**：任务粒度要**按「一个上下文能装下」**来切，而不是按「功能上相关」来切。
  重组任务时的经验值：**一个契约 schema override + 重生成 + 引擎新行为 + 证据，就应独占一个任务**。
- 回滚点：本决策为流程；TASK-024a 的实现可整提交回退。

## D78 — TASK-024a 交付（E-10）：**编辑器起的游戏现在可被 MCP 直接观察**（零字符串手术）

- 日期：2026-09（已实现仍 **113/171**；本任务是顺手性改造）
- **交付**（提交 `485353e8a8`/`76f78f82b9`/`a5d15f7464`，门在 `--version == HEAD`（`76f78f82b`）的绑定二进制上）：
  - **实现**：`play_args = {"--mcp-port=" + itos(game_port)}` 交给
    `EditorRunBar::play_main_scene(false, args)` / `play_current_scene(false, args)` / `play_custom_scene(path, args)`；
    `EditorRun::run()` 原样附加到子进程命令行（`editor_run.cpp:157-161`）。
    **关键引擎事实**：**`EditorInterface::play_*` 无法携带 run args**（`editor_interface.cpp:815-825`），
    这正是原实现做不到的原因 —— 工具改为直接走 `EditorRunBar`。
  - **端口选择（顺手且不冲突）**：`mcp_port` 指定 → 范围/占用/「等于编辑器自身端口」三重前置检查
    （占用或等于编辑器端口 → `-32000` + 建议，**不做静默回退**，因为「`playing:true` 配一个连不上的端口」正是要消灭的假成功）；
    缺省 → `TCPServer::listen(0)` 取空闲端口并排除编辑器端口（8 次尝试）。
    Windows 上该探测可信，因为 `NetSocketWinSock::set_reuse_address_enabled()` 是**刻意的 no-op**（`net_socket_winsock.cpp:549-554`）。
  - **响应**：`mcp_port` / `mcp_port_source`(`argument`|`auto_free_port`) / `endpoint` / `pid`；
    且 `playing:true` 被**收紧**为「**读回** `is_playing()` 且**子进程 pid 变化**」，而不是「调用过 `play_*`」。
- **⭐ 实测证据（不是推断）**：
  - 子进程 cmdline 实测含 `--mcp-port=19890`（附完整命令行文本）；
  - **该端口真的接上并跑了游戏侧工具**（`running_game_get_scene_tree` → `{"tree":{"name":"Main","path":"/root/Main"}}`）；
  - 缺省自动端口 `57389 ≠ 9888` 同样闭环；`19891` 被真实 listener 占住 → `-32000` 且**游戏未启动**；`9888` → `-32000`；
  - **零字符串手术链（4 步，调用方字符串操作 0 次）**：`editor_open_scene` → `editor_play_scene(mode=res://scenes/other.tscn, mcp_port=19893)`
    → `running_game_get_scene_tree` → `running_game_get_node_properties(node_path=tree.path)`；
  - 三种 `mode`（main/current/路径）各一次回归；`editor_stop_scene` 后子进程消失、**无孤儿**。
- **契约只经 override**：生成器 **1.5.0 → 1.6.0**；`DESCRIPTION_OVERRIDES["play_scene"]`（**append**，原文「运行场景」在首，
  生成器有前缀守卫）+ `SCHEMA_OVERRIDES["play_scene"]`（`mode=replace`，理由**逐字引用被移除的 `required` 成员 `[]`**）；
  契约 diff **只有 `play_scene`（18+/2−）** + `_meta.generator_version` + 2 条 override（`overrides=11`）；
  `TOOL-NAMING.md` **无需重渲染**（它由未变的映射渲染，用 `gen_table.py --check-only`（exit 0 + 两次渲染逐字节相同）**证明**而非断言）。
- 门：①`editor_playback` 逐字 **3/3**；②**31/31**；③doctest **197/197·7861**；④全引擎 **1623/1623·432143 断言 0 failed**；
  ⑤`accept_m1.ps1` **22/22 ×2**（PASS 清单一致）；⑥**门⑥ exit 0**；9877 全程 PID 36392 未动。
- **半成品补丁的处置（逐项复核，纪律的执行）**：**采纳** override 机制/版本号/两条 doctest/`tcp_server.h` include；
  **丢弃** 补丁里的 `DESIGN-DETAIL` GDR-25+§23（属整批且**执行者不写规范**）、`check_narrowing_points.py` 的
  `851→1000` 重钉（本树里 851 是对的，门⑥ 通过）、以及 E-1/E-3/E-6/E-9 的全部 doctest。
  并**改写了**补丁的契约文字：补丁声称响应「在游戏真的起来后给出」（**过度承诺**，工具并不等待子进程 bind），
  且其理由引用了一个**不存在的 GDR-25 小节**。
  → **注意**：补丁里的 `mcp_port:0` 校验 doctest **抓到了新实现的一个真缺陷**（显式 `mcp_port:0` 被静默接受）。
  **这印证了「把半成品交给新人但要求复核」比「直接丢掉」更有价值。**
- **诚实边界（登记，不声称）**：「**子进程没起来 → `-32000`**」这条分支**没有线上证据**（只能经恢复模式或缺失
  `project.godot` 构造）→ 报告标为**推断**；一个**不可复现**的首次 `--import` 观察
  （`ERROR: Parameter "singleton" is null`）按手册 §7.3 登记为**观察**，**不算缺陷**。
- **待决策者执行的规范落笔（行动项）**：E-10 需要一个设计条款（「**编辑器起的游戏由工具注入端口；
  契约必须说明端口来源**」）与「顺手性可执行判据（零字符串手术）」——
  执行者**正确地拒绝**写规范（职责边界），所以这条由**我**在下一次 `DESIGN-DETAIL` 编辑中落笔（GDR-25）。
- 下一步：`TASK-024b`（E-1/G-2、E-3、E-9、E-6/G-4 —— **继续拆小**，本单点任务已证明一项就能占满一个执行者）、
  `TASK-025`（E-2/E-8、G-1、G-3），然后**第四次 M4 复核**，再开 B5。
- 回滚点：TASK-024a 改动可整提交回退；契约 override 可移除并重生成。

## D79 — TASK-024b 交付（E-1/G-2 + E-3 读侧）+ **勘误：门⑥ 声称与实现不符**（已查证）

TASK-024b 交付(E-1/G-2 + E-3 读侧) + 勘误: 门⑥ 声称与实现不符(已查证)

TASK-024b(提交 2a1cb4a4e8/928af5d3d8/abffba1cc5/4e910f7c4d): 六门全绿
  ① 契约子集 3/3(编辑器 91/游戏 53/本组 7 逐字 True); ② 证据 68/68; ③ doctest 201/201 (8021 断言, 基线 197/7861);
  ④ 全引擎 1627/1627 (432303 断言); ⑤ accept 22/22 x2(PASS 清单逐字相同); ⑥ 29 点全部登记 PASS
E-1+G-2: get_dependencies(p_add_types=true) + 按引擎布局 path::type[::fallback] 切分(resource_format_text.cpp:960-968);
  type 为真实类型(loader 类优先、标签类型兜底, 因导入资源如 .png 的 get_resource_type 为空串),
  path 恒为 res://, 另给 uid/declared_type/path_source; 改前 3 趟 -> 改后 2 趟, path 直接喂 project_read_resource 实测 code=0
E-3 读侧: Vector4/Vector4i/Rect2i 加对象分支 + 全部 10 个 packed 加元素形状数组分支
  (PackedByteArray=整数数组, 即写侧可接受的形态); 编辑器 9888 与游戏 9889 读回逐字一致
零字符串手术链(六步, 逐步 string ops = 0): deps->path -> project_read_resource -> convert_path_to_uid ->
  editor_get_node_properties(.v4/.pv4/.bytes) -> editor_set_node_property(value=读回 .v4, new_value 相同) ->
  running_game_get_node_properties 两端一致

【勘误】门⑥ 声称与实现不符(决策者已自行只读查证):
  REPORT-023 声称 PINNED 按 (文件,标记 id,文件内出现序) 索引、行号只作说明;
  实际脚本 PINNED 是 {file:{line:pin}} 按行号做键, 且'陈旧条目'是失败条件 ->
  任何代码位移都会假红, 每批必须手工重钉(TASK-024b 把 851 改成 986)
  影响: 假红是响亮失败不是静默错误, 但违反 GDR-24 的意图(位移不该导致失败), 且制造每批摩擦
  处置: TASK-025 §1 真正改为按 (文件,标记id,出现序) 索引, 行号仅作注释/报告信息;
  失败条件必须保留(未标注点/标记不在清单/陈旧条目)并用三组实验证明(位移不假红 + 新增未标注点仍 exit 1 +
  陈旧条目仍 exit 1); 并要求执行者在报告里显式更正 REPORT-023 的该条声称(对已验收报告的勘误, 不得悄悄改代码了事)

新残留缺口(实测披露, 非本批回归): E-3 写侧无 Vector4i/Rect2i 分量表 -> 读回对象原样写回被 -32602 拒绝,
  违反 GDR-25 §23.1(1)/(4)(返回的标识不必转形就能喂回) -> TASK-025 §2 修复:
  对读回形状矩阵每一项做写回测试, 不能写回的补齐写侧(经已有闸门, 不得新开绕过分支),
  引擎本身不可写的逐项列引擎依据并给可读原因; 边界: 若引擎语义确为不可写, 按 GDR-23 以引擎为准
下一步: TASK-025(门⑥索引 + E-3 写侧) -> TASK-026(E-9 + E-6/G-4) -> TASK-027(E-2/E-8 + G-1 + G-3)
  -> 第四次 M4 复核 -> B5(58 工具)

## D80 — TASK-025 交付（门⑥ 索引真修 + E-3 写侧闭合）+ GDR-25 §23.4 双向闭合规则落笔

TASK-025 交付(门⑥索引真修 + E-3 写侧闭合) + GDR-25 §23.4 双向闭合规则落笔

TASK-025(提交 f9c0510194/a95b824053/6f77e987ad/dfda642459/1486febf8a): 门①-⑥ 全绿, --version == HEAD(dfda64245)
  ① 契约子集 3/3(编辑器 91/游戏 53 不变, 本组逐字 True); ② 证据 110/110; ③ doctest 205/205 (8102 断言, 基线 201/8021);
  ④ 全引擎 1631/1631 (432384 断言); ⑤ accept 22/22 x2(PASS 清单 identical); ⑥ 30 点/30 pins/0 moved + 三组实验 22/22
门⑥ 索引真修: PINNED 由 {file:{line:pin}} 改为 {file:{marker id:[pins 按出现序]}}, 查表按 (file, marker id, occurrence),
  line 仅作注释; 失败条件三条一字未减(unannotated/unlisted/stale); moved 从死代码变成可达真提示
  四组实验: E1 位移不假红(插入 20 行注释不重钉 -> exit 0 且只报 moved 提示);
  E2 新增未标注 -> exit 1; E3 陈旧条目(标记改名) -> exit 1; E4 还原后 sha 逐字节相同;
  E0 新旧对照用 TASK-025 起点提交 0b120996ff 的 git archive 副本(不碰仓库): 改前脚本同一位移 exit 1(假红),
  新脚本 exit 0 —— 两侧对照点是'同一个改动下的各自判定'
  勘误(append-only, 未改 REPORT-023 原文): REPORT-023 §5 与 §11 deviations 第 4 条声称 pin 按
  (文件,marker id,出现序) 索引、位移只产生 moved 提示且不 fail; 实际改前实现是 PINNED[file][point.line] 行号键、
  moved 分支构造上恒不可达(死代码); TASK-024b 因此手工把 851 改成 986
  结论: 核心不变式'新增未标注收窄点即 fail'仍然成立(那次红演示观测有效); 被否定的是'位移不失败'这条设计声称
E-3 写侧闭合: vector_from_dictionary/vector_component_hint/_vector_components 各补 VECTOR4I/RECT2/RECT2I
  (Rect2 分量 real_t -> REAL_T; Rect2i/Vector4i -> INT32; 分量名与读侧逐字一致); 每分量先经 _check_components ->
  coerce_to_property_type + _component_fits_slot, 未新开绕过分支
  读回->写回矩阵 19 项 x 两端点 = 19/19 全部往返(code=0 + new_value 结构化相等 + 再读相等), 证据 110/110;
  矩阵内无引擎不可写项; 三条拒绝的可读消息实测(1e300 点名 value.x 与 32-bit float 槽并给出引擎会写的 inf 等)
  回归: TASK-024b 证据脚本原文重跑 66/68, 2 条失败恰为被本批闭合的 GAP_v4i_*/GAP_rect_i_*(现 code=0),
  其余 66 条不变 —— 未改历史证据脚本、未放宽断言(以'失败恰为被闭合项'作等价判据)
  零字符串手术链扩展为读->写->再读 6 步两端点各一遍, 逐步 0 次字符串处理;
  且'零'不是声称: 脚本读取自身源码在 # CHAIN-BEGIN/# CHAIN-END 区间检索 10 个禁用记号(Split/Replace/Substring/Trim/
  -match/-replace/[double]/[int]/[regex]/ConvertTo-Json), 实测 <none>
  如实登记 3 个脚手架自身缺陷(doctest 字面量+GodotString 无 operator+ 编译失败; 颜色形状判据误用 .x;
  门⑥ E0 误从 HEAD 取旧脚本) 并已修

GDR-25 §23.4 双向闭合规则落笔(决策者): '读侧能答出对象形态的类型集合'必须等于'写侧能接受对象形态的类型集合';
  登记 19 项读回->写回形状表; 写侧分量表规则 = 读侧能答出对象的类型集合(新增读回类型必须同时加写侧, 否则算缺陷);
  分量槽位(Rect2=REAL_T / Rect2i,Vector4i=INT32 / Color=FLOAT32)每分量必经 value_fits_slot;
  已知残留欠账: Transform2D/3D, Basis, Quaternion, Plane, Projection, AABB 当前无工具读回,
  一旦有工具要读回必须对象形态读写, 不得用 stringify() 字符串形态;
  证据形态三层等价: code=0 + new_value 与读回值结构化相等(不是拼字符串比较) + 再读仍相等, 两端点各一遍
下一步: TASK-026(E-9 + E-6/G-4) -> TASK-027(E-2/E-8 + G-1 + G-3) -> 第四次 M4 复核 -> B5(58 工具)

## D81 — TASK-026 交付（E-9 + E-6/G-4）+ D-8 裁决与 §23.5 落笔 + 其余上报项裁决

TASK-026 交付(E-9 + E-6/G-4) + D-8 裁决落笔(GDR-25 §23.5 OBJECT 形状) + 其余上报项裁决

TASK-026(提交 48474b5a8d/d9db6a8a55): 未新增工具、未改名字、未动契约(契约/映射/组清单零改动)
  ① 契约子集 3/3; ② 证据 37/37 + OBJECT 探针 11/11; ③ doctest 209/209 (8228 断言, 基线 205/8102);
  ④ 全引擎 1635/1635 (432510 断言); ⑤ accept 22/22 x2; ⑥ exit 0; 9877(PID 36392) 全程未动
E-9: project_read_resource 给 STORAGE 属性值(既有 serialize_variant, 形状按 §23.4) + total_properties/truncated/
  dropped/limits{max_properties:64}/message; 实测 Gradient 7 条与引擎 GDScript STORAGE 列表逐项相等;
  Environment 101 -> 64 返回/37 丢弃; 缺参 -32602、文件缺失 -32001+suggestion 未变
E-6+G-4: 两个日志工具改为'本进程 EditorLog 优先、文件仅后备'(与 editor_remove_output_log 同侧),
  共用 9 键来源块(source/in_process/available/editor/process/pid/port/log_path/note), 形状分裂消除;
  不可用一律诚实空(source:none + available:false + note), 绝不 -32603
  实测红: 旧码在编辑器端点 source=log_file 读到游戏进程的行; 游戏持有时两工具双双 -32603
  实测绿: source=editor_log、in_process=true、本进程标记可见、游戏标记不可见、文件被独占时仍 code=0
  D-7 边界已就地写明: editor_log_lines() 读的是面板渲染文本(含 ERROR:/WARNING: 前缀; 用户关掉的类型过滤器、
  搜索框内容、进入树前的消息不在内; 面板 10000 行上限); 要全量需引擎公开 EditorLog 读取口

D-8 裁决(新规范 GDR-25 §23.5, 决策者落笔): OBJECT 属性双向不闭合(读 {} / 写侧拒 {} / 写 null 读回仍 {}) 属缺陷
  读回形状: 未设置 -> null(不得答 {}, 因为 {} 语义上是'有个对象但无信息'= 假信息);
    已设置资源 -> {type,path}; 无路径资源 -> {type,path:""}(可加 local_to_scene); 非资源对象 -> {type,path} 不泄露指针/地址
  写回形状: 必须接受读回形状本身(null / res:// 字符串 / 对象 {type,path}); {} -> -32602(信息不足, 不得当成清除);
    加载失败 -32001+建议; type 不符 -32602(消息给期望与实际); 写回后必须读回验证且 null 写回后读回必须是 null
  这正是'引擎为第一参考源'落到形状契约上的例子: 语义以引擎为准, JSON 形状由本规范定义, 目标是'读到的值能原样喂回'

其余上报项裁决:
  D-1(Curve.min_value 不是 STORAGE, 任务书示例有误): 保持 STORAGE-only —— 它才是引擎持久化的权威内容,
    且可写回(§23.4 往返成立); EDITOR-usage 的派生视图(min_value/max_value 等)是 _limits 的视图,
    不纳入读回往返契约; 任务书示例的错由我承担
  D-2(为满足链式喂回而改 project_edit_resource/project_create_resource 补 shape_vector_from_json 分量整形步):
    接受(同一模块、无契约变更; 不接受则分量形状读回值喂不回去)
  D-3(source 取值改为 editor_log/log_file/none, 替代迁移源的 log_file/no_log_file): 接受(§23.3 指定的拼写;
    none+available:false+note 是诚实空; 旧拼写不再保留)
  D-4(二进制自报父提交 hash): 接受(git status 证明内容一致); 第四次 M4 复核会重建使二进制==HEAD
  D-6(新 _editor_log_view() 与 editor_write_scene_editor.cpp 的文件私有 walker 重复): 登记为 hoist 候选, 后续批次清理
  D-5(门⑥ pin 行号按提示更新): 接受(不更新也 exit 0, 仅留 drifted 提示)
  裁决'不加 source 参数让编辑器端点读别的进程日志': 不加 —— 那正是 M4c 抓到的混淆源(把别的进程日志当自己的);
    诚实行为就是读本进程日志, 跨进程需求由 hof-rs 侧自建通道解决
下一步: TASK-027(D-8 闭合 + E-2/E-8 稳定路径) -> TASK-028(G-1 子属性路径 + G-3 clear 语义) -> 第四次 M4 复核

## D82 — TASK-027 交付（D-8 OBJECT 双向闭合 + E-2/E-8 稳定路径）+ 上报项裁决 + 最后一批顺手性项

TASK-027 交付(D-8 OBJECT 双向闭合 + E-2/E-8 稳定路径) + 上报项裁决 + 最后一批顺手性项

TASK-027(提交 925fc9d607/45b962d046, 全部在提交后于 HEAD 重建的二进制上跑, --version=925fc9d60 == HEAD)
  ① 契约子集 3/3; ② 证据 61/61(红相位同脚本 32/61 exit 1); ③ doctest 213/213 (8309 断言, 基线 209/8228);
  ④ 全引擎 1639/1639 (432591 断言); ⑤ accept 22/22 x2(PASS 清单 identical); ⑥ exit 0;
  回归: mcp016 86/86、mcp017 88/88(逐字消息断言仍成立)、mcp026 37/37(其旧缺陷探针 8/11, 3 条失败即被修掉的旧行为, append-only)
D-8 OBJECT 双向闭合: 读 null 指针->null(不再 {}); 有路径 Resource->{type,path}; 无路径->{type,path:"",local_to_scene};
  非 Resource 对象->{type,path:wire_node_path} 不泄露指针; 写侧接受 null / res:// 字符串 / 同形对象, {} -> -32602,
  加载失败 -32001+建议, type 不符 -32602(期望与实际); 另加'属性声明类别'校验(PropertyInfo::class_name, 含逗号表与 - 排除)
  —— 不加则新字符串写形态会把静默默认值带回模块(setter 存 null 报成功)
E-2/E-8 稳定路径: editor_get_scene_tree 的 path 改为相对编辑场景根('.'/'Actor'/'Actor/Sprite2D'), 绝对路径另给 absolute_path;
  新增 MCPTools::wire_node_path 供写族拒答使用, 消息不再含 @EditorNode@
  可复现性: 两个独立编辑器进程的整包响应逐字节相同(sha bdebaef0…), 证据脚本两次运行日志 sha 也相同
  零字符串手术链 8 步 0 次字符串处理(树->读属性(material=null)->写 res:// 字符串->读 {type,path}->原样喂回->再读->写 null->再读)
  受影响工具清单分 A/B/C/D 四类逐条给证据, 且这些都属输出形状/消息, inputSchema 未动(门① 证明契约逐字未变)

裁决:
  D-2 属性声明类别校验(超出 §23.5 字面): 接受(防止新的静默默认值)
  D-3 非资源对象(Node 引用)读回 {type,path} 暂不能写回(-32602, 缺'谁把节点路径解析成对象'的上下文): 登记为已知边界;
    当前无工具读回 Node 型 Object 属性 -> latent; 将来需要时单独裁决
  D-4 local_to_scene 只读不写: 接受(§23.5 表格'若适用'的直译)
  D-8 游戏侧仍答 /root/Main/...: 接受(它是游戏自己场景树的稳定路径, 不含编辑器内部装饰, 可复现可链式);
    若要游戏侧也相对当前场景根, 属另一项(会动 53 个游戏工具与契约描述), 暂不立项
  D-9 门跑在提交后 HEAD 重建的二进制上: 接受(两轮数字一致)
  D-1 新发现: 全新工程 + 含 .tscn 时首次 --import 必崩 0xC0000005, 第二次 exit 0(不含 .tscn 的工程首次即 0)
    -> 影响所有新建骨架工程的门脚本(PLAYBOOK §3 要求校验 --import 退出码) -> TASK-028 §3:
    界定最小复现与根因(排除 BOM/.godot 缺失/--mcp-port/文件内容), 若无法归因到模块就明说引擎侧缺陷并给上游材料;
    脚本加固(不写 BOM + 校验退出码 + 有界重试 + 可诊断输出); 并把该纪律补进 PLAYBOOK §3(运维纪律, 允许执行者直接改手册)
下一步 TASK-028(三项收尾: G-1 子属性路径 / G-3 clear 破坏性 / D-1 import 加固) -> 第四次 M4 复核 -> B5(58 工具)

## D83 — TASK-028 交付（G-1/G-3/D-1）+ 我的 BOM 归因被推翻 + clear.default 裁决（方案 A）

TASK-028 交付(G-1/G-3/D-1) + 我的 BOM 归因被推翻 + clear.default 裁决(方案A)

TASK-028(提交 bf051fc1a6/ba719d483d/dca9c82bcf): 门全绿, --version == HEAD(dca9c82bc)
  ① 契约子集 3/3; ② 证据 27/27 + TASK-027 重跑 61/61 未回退; ③ doctest 217/217 (8415 断言);
  ④ 全引擎 1643/1643 (432697 断言); ⑤ accept 22/22 x2(PASS 清单 IDENTICAL); ⑥ 30 点/30 pins exit 0;
  9877 全程 PID 36392 未动; 未 push; 工作树干净

G-1 子属性路径: 编辑器与游戏节点写族(含 add_node.properties、add_nodes_batch、set_property_batch、跨场景事务)
  接受引擎语法 position:y / v4:x / material:shader_parameter/uv1_scale, 写动作是引擎 Object::set_indexed,
  值仍走 property_value_from_json -> shape_vector_from_json -> coerce_to_property_type 同一道闸门(未新增收窄点, 门⑥ 30/30)
  语义按引擎: 不存在子段 -32001 且消息指名哪一段 + 给该类型成员清单; 不可 index -32602; 写后读回(带 parent_property/
  parent_old_value/parent_new_value, 仅多段路径); 前导冒号 ':y' 按畸形 -32602 拒绝(NodePath 会静默重解释为裸路径 y);
  Dictionary 新键 d:new_key 拒绝为 -32001(引擎允许加键但无声明类型可过闸门), 已存在键可写
  读侧结论(不越权): 不支持子路径 —— 一次读整属性就拿到全部分量, 信息更多、调用次数相同、零字符串手术;
  加它要改契约描述而无收益(已用 doctest 钉住)
G-3: clear 改为显式 opt-in(缺省/false = 纯读不删, 显式 clear:true 才清), 响应 cleared 列出真实范围;
  双客户端实测两次纯读响应体 sha256 完全相同且桥接文件仍在; 显式清后为诚实空
  待决策项: 已注册 inputSchema 仍写 "clear":{"default":true} 与实现不一致 —— 执行者按纪律未自行 override, 上报;
  裁决: 方案 A —— default 改 false + 描述写明'显式 true 会删除共享桥接文件、影响其它客户端'
  -> 需 SCHEMA_OVERRIDES(mode=replace, 理由逐字引用被替换的 "default": true) + 可能加 DESCRIPTION_OVERRIDES +
  重生成契约与全部指纹 + 门① 重跑 -> 独占一个任务(TASK-029)

D-1 --import 首次崩溃: 【推翻我此前的 BOM 归因】
  84 次受控全新工程首导(7 变体 x 6, 首导+二导)全部 exit 0, Parse Error 0 次: 含/不含 .tscn、.tscn 带 BOM、
  project.godot 带 BOM、.tscn 含 ext_resource、--mcp-port 缺省(=9877 已被占)/=0/=9888 均无差异;
  另加 relink 后 32 次、TASK-027 复刻 16 次同样全 0(累计 132 次)
  -> 「含 .tscn 首次必崩」「BOM 必崩」两条断言均不成立, 执行者按 PLAYBOOK §7.3 显式撤回并就地改写 PLAYBOOK §3 判据
  -> 根因判定: 引擎侧间歇性进程级访问违例(0xC0000005 / exit -1073741819), 当前不可复现, 无法归因到本模块;
     唯一可复现的引擎侧痕迹是 stderr 的 Parameter "singleton" is null. at: EditorNode::is_cmdline_mode
     (editor_node.cpp:6732, 调用点 editor_file_system.cpp:2301, 模块里无调用者), 且它自身也是间歇的(84 次 0 次)
  -> 上游最小复现材料已写进报告 §3.4(命令/最小工程/退出码/stderr/可跑探针 scripts/mcp028_import_crash_probe.ps1)
  这一条是我第二次被纠正的技术判断(BOM 归因源自更早一轮的观察, 我把它写成了 PLAYBOOK 判据) —— 教训同 D74:
  观察要被复现实验检验后才能成为规律; 单次观察不得升级为规范
脚本加固(与根因无关但必要): 新增 scripts/mcp_import_guard.ps1 作为唯一实现
  (无 BOM 且机器校验 first3 非 EF BB BF + 校验退出码 + 默认 3 次有界重试 + 每次失败打印命令行/退出码十进制与 0x/
  工程路径/日志路径/日志尾部); accept_m1、check_contract_subset、mcp009–mcp027 全部改用; 失败路径用 stub 引擎真实演示;
  scratch 不写 BOM 仍作为零成本纪律保留
  PLAYBOOK §3 就地改写为四条纪律并撤回旧的 BOM 判据(运维纪律, 允许执行者直接改手册)

下一步: TASK-029(clear.default override + 重生成指纹) -> 第四次 M4 独立复核(覆盖 D-1..D-15、E-1..E-10、G-1/G-3/G-4
  的闭合 + 零字符串手术链 + 门①-⑥) -> B5(58 工具, 每批引擎优先)

## D84 — 第四次 M4 复核仍 fail：D1 活动场景静默丢失写入（high）+ D2 门⑥ 拼写可绕过（high）

第四次 M4 复核仍 fail —— D1 活动场景静默丢失写入(high) + D2 门⑥拼写可绕过(high)

M4d(验收方自建证据, 基准 HEAD ac06a1cade): verdict=fail
  pass: 全量对等(自解析 name, 编辑器 91/91、游戏 53/53 逐字相等; 13 条 override; 用生成器重生成契约与
    被跟踪文件逐字节相同 = 证明无手改); 静默错值五形态(30+ 例全 -32602 + 无值回显 + 保存后文件无 inf/nan +
    另一读工具读回旧值; 新增 10 条同族面全拒; FLOAT32/REAL_T 已分离且欠账登记诚实);
    门⑥ 静止/插入/删标记/位移四类行为正确(证明索引是标记身份而非行号, 实验后逐字节还原);
    顺手性八项(含 E-10 子进程 cmdline 真含 --mcp-port=9897 且响应 pid 即该进程; E-3 编辑器 12 项 + 游戏 4 项
    三层往返; §23.5 OBJECT; E-9 截断; E-6 日志归属; E-2 两独立进程路径逐字一致; G-1 子属性; G-3 clear 缺省纯读);
    零字符串手术链 2 条跨 6/5 工具调用方字符串处理 0 次(源码区间扫描证实);
    六道门全绿(①5 组 15 例、③219/219、④1645/1645、⑤accept ×2 各 22/22 清单一致、⑥ exit0); 端口纪律 pass

D1(high) project_set_node_property_across_scenes 对活动编辑场景报成功但未写入:
  force=true -> code:0 + mode:"live_open_scene" + message "active open scene was edited in memory",
  但另一工具读回旧值 {"x":1.0,"y":2.0}, 随后 editor_save_scene 落盘仍是旧值; 同一次调用里关闭的 side.tscn 确实写成 Vector2(3,4)
  根因(验收方定位, 待复核): project_cross_scene_write.cpp:309-317 对活动场景也用 CACHE_MODE_IGNORE 加载并 instantiate 出
  游离副本(匹配/校验都作用在副本上); :451-455 对 live_open_scene 跳过落盘只调 _mark_active_scene_unsaved();
  :81-86 注释却声称 edits the live nodes
  危险性: 报成功 + 什么都没发生, 而且把场景标为'已修改' -> 调用方按报告继续 editor_save_scene 会把旧值当成
  '已保存的新值' 写下去 = 静默数据丢失。这正是本项目要消灭的那一类
  裁决: TASK-030 —— 二选一(推荐真的写活节点并读回验证, 保留 mark_scene_as_unsaved; 或诚实拒绝并去掉'已写入'措辞),
  无论哪种 scenes_affected[].mode 必须让调用方一眼看出'写没写', 不得出现'成功+未写入'组合;
  必须新增端到端回归链: 写活动场景 -> 另一工具读回新值 -> editor_save_scene -> 文件含新值; 并覆盖活动+关闭混合时关闭者仍真落盘

D2(high, 护栏强度) 门⑥ 可被常见拼写绕过: 扫描器只认 (real_t)/(float)/Color(/Vector2(/Vector3(/Vector4( 六种字面拼写;
  const real_t x=1.0e300(隐式收窄)、static_cast<float>(1e300)、::Color(1e300,0,0,1)、Vector3{1e300,0,0}、
  Color 与 ( 跨行 —— 五个探针插入后门⑥仍 exit0(扫描器 0 命中), 同一数值写成 (real_t) 则 exit1
  -> DESIGN-DETAIL §22.3 与脚本 docstring 的'每个收窄点都必须标注'在拼写层面不成立;
     R1: 门绿不等于覆盖面完整, 后续批次可用最常见写法静默引入第 5 种静默错值形态
  裁决: TASK-031 —— 扩展扫描覆盖(static_cast/隐式初始化/限定构造/花括号/跨行)或改用编译器级检查(-Wconversion);
  并把 §22.3 的'每个收窄点'表述收窄为'已覆盖的拼写集合'(若选扫描)或改为'由编译器保证'(若选 -Wconversion);
  用这 5 个探针做回归(应 exit1)

D3(medium) editor_get_node_properties 不带 properties 时把检查器分组/类别标签当属性输出:
  12 个不存在的 null 属性(Node/Node2D/Material/Transform/Visibility/Ordering/Texture/Process/Thread Group/
  Auto Translate/Editor Description/Physics Interpolation/CanvasItem), 且 Material 与真实属性 material 大小写冲突
  -> 本机 PowerShell 5.1 直接报 duplicated keys 导致整包无法解析(大小写不敏感字典的客户端同样受影响)
  位置 tools/editor_node_read.cpp:192-205(只跳过 _ 前缀与 script, 未按 PROPERTY_USAGE_GROUP/CATEGORY 过滤)
  R3: 容易被误判为偶发坏响应 -> TASK-032 优先修
D4(minor) 未知/多余参数名被静默忽略: project_get_settings 契约参数是 prefix, 用 filter 调用 code0 并返回 981 条
  (既不拒绝也不过滤), 拼错的参数名得到'像样的错答案'; 对比 project_set_setting 用 name 时诚实 -32602
  裁决: TASK-032 —— 未知参数名返回 -32602(可回显已忽略参数名)
D5(minor) 零命中仍宣称已应用: path_filter 指文件而非目录 -> total_scenes=0/scenes_affected=[] 但 message 仍 'Applied'
  裁决: TASK-030 —— total_scenes==0 时消息显式说明无匹配 或 -32001+建议(说明理由)
D6(minor) 游戏侧路径形态与描述不一致: running_game_get_scene_tree 返回 /root/Main/Actor,
  而同族 running_game_get_node_properties 描述写'node_path(相对于场景根节点)'; 实测两种写法都能喂回
  裁决: TASK-032 —— 用 DESCRIPTION_OVERRIDES 说明实际返回形态并声明两种写法都接受(走 override + 重生成指纹)
未确认: 符号链接逃逸(本机无开发者模式, 其余 8 读侧 + 3 写侧已实测拒绝); 双精度端到端(已声明欠账);
  absolute_path 跨机器/跨编辑器布局的稳定性(内嵌 @EditorNode@<layout id>)
风险: R1 门⑥ 假绿(已裁决修); R2 D1 静默数据丢失(已裁决修); R3 D3 大小写冲突致整包解析失败;
  R4 absolute_path 含布局 id; R5 Camera3D.rotation_degrees 派生属性有 1 ulp 漂移(将来若把三层等价做成严格位相等门会假红)
下一步: TASK-030(D1+D5) -> TASK-031(D2 护栏) -> TASK-032(D3+D4+D6) -> 第五次 M4 复核 -> B5(58 工具)

## D85 — TASK-030 交付：D1 改为真的写活节点（含 mode 语义表）+ D5 显式无匹配；mcp018 历史不变式过期

TASK-030 交付 —— D1 改为真的写活节点(含 mode 语义表) + D5 显式无匹配; mcp018 历史不变式过期

TASK-030(提交 545060f25e/b6203ba2b7/e7d0d218f1/9ef9c8f0fb): 门①3/3; ②22/22(红阶段 22 checks/7 failed);
  ③220/220 (8481 断言); ④1646/1646 (432763 断言); ⑤accept 22/22 x2(清单逐条一致); ⑥30/30 exit0;
  重跑 mcp028 27/0、mcp029 20/0; 9877 全程未动; 未 push; 最终 HEAD 9ef9c8f0fb, 二进制 --version == HEAD

D1 裁决落地=方案①「真的写活节点」(理由: force=true 的契约语义本来就是允许改活动编辑场景;
  本 fork 有唯一顺手答案 = edited_scene_root() 的编辑器同步活树 + mark_scene_as_unsaved();
  方案②会让'整工程一次改完'主用例永久残废、把一次调用变成多步舞蹈; 且活节点写入可验证 -> 能验证就不该退化成拒绝)
  根因复核: 验收方行号全为真(:309-317 加载游离副本 / :451-455 跳过落盘只标 unsaved / :81-86 注释自相矛盾);
  执行方补充两条决定修法的事实: ①mode 在计划阶段 :361 已定死(工具自己也不知道改的是哪棵树) ->
  修法必须把'写哪棵树'变成计划阶段的事实(plan.instance + plan.owns_instance);
  ②instance 原来无条件释放(六处 memdelete), 若只把 instance 换成活树会删掉用户正在编辑的场景 ->
  新增 owns_instance 与唯一释放入口 _release_planned_scenes()
  写后逐节点读回验证, 不一致则整段回退并 -32000 + data.live_nodes_restored; 活节点排在所有文件之后提交, 保住 all-or-nothing
  mode 语义表(三行穷尽互斥 + written/persisted 两布尔): dry_run(false/false) / offline_saved(true/true) /
  live_open_scene_written(true/false); 不存在 written=true 而其实没写的组合(该值只有两条产生路径:
  文件原子发布成功, 或活节点写后每节点读回都与写入值一致)
  端到端链绿: 写活动场景 -> 另一工具读回 {3,4}(sha 7ae14eaf -> edd2622c) -> editor_save_scene ->
  good.tscn 含 Vector2(3,4); 同一次调用里关闭的 side.tscn 真落盘含 Vector2(3,4)
  红阶段字节级铁证: '调用后读回'与'调用前基线'响应 sha256 完全相同(7ae14eaf…, 166 字节); save 后文件仍是 Vector2(1, 2)
D5 选择'显式说明没有场景匹配'而非 -32001(理由: 零命中是合法查询结果, dry_run 预览/按目录扫零命中很常见,
  改错误会打断'先探测再决定'的正常流程; 且 total_scenes==0 与 scenes_affected==[] 本身是机器可判字段);
  message 分四情形, 非 dry_run 零命中句明确提示 path_filter 是目录不是单个场景文件
偏差接受: mode 词表变化(live_open_scene -> live_open_scene_written + written/persisted 两布尔) —— 响应形状不在契约文件里,
  门① 逐字通过证明契约面零偏离, offline_saved/dry_run 未改名;
  editor_rescan_triggered 语义收窄为'只在真的替换过文件时为 true'(活节点编辑不触碰资源文件系统);
  新增公开函数 MCPTools::write_live_scene_property()(doctest 进程无 SceneTree, 与 prepare_node_property_value 公开同理);
  doctest 第(4)段的红阶段用 #if 0 临时屏蔽(旧实现无该入口会整个 TU 编译失败), 最终提交无 #if 0(已核验 if0_count=0),
  但该段因此没有'先红'执行记录 —— 如实声明

mcp018 历史不变式过期(如实上报未自改): 该脚本断言 derivation_new_union_is_old_plus_exactly_ten(old=96 new=113),
  随工具数增长必然失效; 输入只有 manifests 与冻结旧脚本、本次一字未改 -> 判定与 TASK-030 无关
  裁决: 由后续批次收口(把该断言改成'相对当时清单'或标记为已被后续批次超越), 否则该脚本会持续红
下一步: TASK-031(D2 门⑥ 拼写覆盖: static_cast/隐式初始化/限定构造/花括号/跨行, 或改编译器级 -Wconversion,
  并用 5 个探针回归) -> TASK-032(D3 分组标签当属性 + Material/material 大小写冲突; D4 未知参数名 -32602;
  D6 游戏侧路径描述 override; mcp018 断言收口) -> 第五次 M4 复核 -> B5(58 工具)

## D86 — **M4 里程碑独立验收通过**（第五次 pass）；报告陈旧结论的纪律；B5 开工

**M4 里程碑独立验收通过**(第五次 pass); 报告陈旧结论的纪律; B5 开工

M4e 第五次独立验收(验收方自建证据, 基准 HEAD 9f2b2e484e): **verdict = pass**
  D1-D6 全部闭合(每条均为验收方自跑证据): D1 写活动场景 -> 另一工具读回新值(7,8) -> save -> 文件含 Vector2(7,8)
    且不变量检查 0 条 code=0∧written=false; D2 门⑥ 三段 exit 0/0/85-85 + 自造 M4d 五探针全红 + 位移不假红 + 逐字节还原;
    D3 编辑器 42 键==引擎值集/13 标签 0 泄漏/0 大小写冲突/ConvertFrom-Json 解析成功; D4 immediate 与 deferred 双入口 -32602
    且已声明参数不被误拒; D5 零命中无 Applied 且文件 sha 不变; D6 描述与线上形态一致 + 原样喂回成功
  **报告矛盾裁决**: REPORT-025 成立, REPORT-032 的'Vector4i/Rect2i 写侧缺口仍未修'为假(照抄 REPORT-024b 未经复测的陈旧结论,
    且与它自己 §3 的 GAP_* 以 code=0 失败的观测自相矛盾); 三条证据(源码/线上 19x2 往返/doctest 断言)一致; 无并行分发表; 实现不需修
  契约与 override: 14 条(11 description + 3 inputSchema)与生成器声明逐对相等; 用生成器重生成与跟踪文件逐字节相同 = 无手改;
    清空 override 后的基线结构化 diff 只差这 14 对与 _meta.overrides
  顺手性 pass(含 E-10 自抓 cmdline + 注入端口跑游戏工具; §23.4 19x2; §23.5 三形态; E-9/E-6/E-2/G-1/G-3 全复现; 自写零手术链 4 步 0 次);
  静态错值 pass(mcp021/022/023 自跑 74/90/218 全 PASS; 抽 ≥25 例具四条件; 五形态全覆盖);
  门 pass(①4 组、③222/222、④1648/1648、⑤22/22 x2 清单 diff=0、⑥三段); 9877 PID 36392 不变; 无孤儿; 无 git 写操作

M4e 遗留(4 条, 均不阻塞收口):
  D-M4e-1(medium, 覆盖缺口): 又找到 5 种可绕过门⑥ 的拼写(-1.0e300 / (1.0e300) / 0x1p1000f / typedef 别名 / 数组初始化),
    均 exit 0 且不在 --coverage 已打印边界里(违 §22.3b 规则 6); 当前 tools/** 无此类拼写
  D-M4e-2(low): running_game_get_node_properties 描述写'不传返回所有属性', 实现只答 EDITOR|SCRIPT_VARIABLE 子集(27/42)
  D-M4e-3(low): 跨场景写工具在'单文件过滤 + 该类型零节点'时建议句不成立
  D-M4e-4(documentation): REPORT-032 的陈旧结论 -> **已由我 append-only 勘误**(作废其 next_step 第 2 条 + 三条事实 + 教训)
  -> D-M4e-1/2/3 并入 TASK-033 的三条小收口

R1 风险登记(持续): 门⑥ 是**有限集合**保证且集合仍在被绕过(M4d 找到 5 种, M4e 又找到 5 种) ->
  必须坚持 §22.3b 规则 2 的**三腿**(机器检查 + 代码审查 + 行为证据), 不得只靠门⑥ 变绿判定'没有新收窄'

★ 新增纪律(D86, 本批起强制, 写入 TASK-033 §2 与后续任务书):
  **任何从别的报告/任务书引用的结论, 必须①标明它测自哪个提交 ②在参考它开工前复测 ③发现过期就在报告里显式指出并 append-only 勘误**
  背景: REPORT-032 的错误结论进入了'下一步建议', 若照它开工会做一批无用功(TASK-025 已修);
  这是'报结论'与'报证据'之间的区别 —— 结论会随代码漂移, 证据不会(只要有提交锚点)
  同时: 报告一旦有结论被推翻, 必须 append-only 勘误, 不得只在新报告里悄悄改口径

B5 开工: TASK-033 = B5 批次 1(动画族 14 工具: animation_write 4 + animation_tree_write 7 + animation_read 3)
  + 三条小收口; 引擎优先设计(GDR-23) + 每工具'引擎依据'列 + 零字符串手术链 + 门⑥ 三段 + §22.3b 规则 4
B5 余下三批已规划: 批次 2(audio 6 + particle 5 + theme 2 + profiling 1 + scene_3d 1 = 15);
  批次 3(tilemap 6 + shader 4 + physics 3 + project_shader 2 = 15, 含 2 个 fix-first);
  批次 4(navigation 3 + running_game_navigation 1 + project_theme_write 5 + export 2 + android 2 = 13-14, 含 bake_navigation_mesh fix-first)

## D87 — TASK-033 交付（B5 动画族 14 工具）+ 批准 4 个 schema 缺口 + 规范更新；B5 批次 2 派发

TASK-033 交付(B5 动画族 14 工具) + 批准 4 个 schema 缺口 + 规范更新; B5 批次2 派发

TASK-033(提交 613df1eda9/36510a32b7/c5bc94ac5d/7e9d00ddf2/4e71becf2d/355bff9538): 六门全绿
  ① 3/3 x3 组(implemented_union 105 editor / 53 game, contract 171); ② 线上 75/75;
  ③ 红 225/9 失败 -> 绿 229/229 (10714 断言); ④ 1655/1655 (434996 断言); ⑤ accept 22/22 x2 逐字节一致;
  ⑥ 扫描 34/34 无漂移 + --coverage 17 拼写 + 探针 101/101; 回归 mcp030 22 / mcp032 39 全绿
  14 工具全部 scope=editor, 9889 上 -32601; 21 步零字符串手术链每步字符串操作 0 次;
  自捉并修掉三处自身缺陷(14 处 handler 成功响应**双层信封**、整数 default 被引擎 JSON 往返拉平为 0.0、
  两处 doctest 期望与引擎语义不符[StateMachine 自带 Start/End、BlendTree 自带小写 output])
  进度: B5 14/58; 模块 127 注册 / 105 编辑器可见 / 53 游戏可见

★ 新纪律当场生效(TASK-033 主动对 REPORT-AUDIT-M4e 出勘误):
  它指出 M4e 的 D-M4e-3 因果前提为假 —— 单个 .tscn 作 path_filter 之所以零命中, 不是因为'它匹配上了但类型零节点',
  而是因为 walker 的 DirAccess::open 对**文件**失败; 并给出锚点(TASK-030 的 doctest 已钉)与 append-only 勘误
  -> 说明 D86 的'结论须带提交锚点 + 引用前复测'这条纪律是有用的(第一轮就抓到一条错误的缺陷归因)

裁决: 批准 4 个 schema 缺口走 override(TASK-033 上报, 已备好可直接粘贴的 SCHEMA_OVERRIDES):
  editor_add_state_machine_state.animation / editor_set_blend_tree_node.animation /
  editor_add_state_machine_transition 的 xfade_time / priority / advance_condition
  理由: 这是'**工具真需要却没声明**'导致**能力结构性不可达**(与 D-6 同类) —— 不加 animation 就无法给新建状态指定动画,
  动画链的一部分不可达; 契约是逐字门对象, 唯一合规出路就是 override + 重生成 + 更新指纹
  -> 并入 TASK-034 §0(附'不可达 → 可达'的前后对照作为价值证明)

规范更新(决策者落笔, 因执行者无权改 DESIGN-DETAIL):
  §22.3b 第 6 条: 覆盖集合 16 -> **17 种拼写**(TASK-033 补入同文件别名类), 探针 101/101
  §23.4 残留清单: **Quaternion 已由 TASK-033 补齐读/写对, 不再是残留**
  (仍为残留: Transform2D/Transform3D, Basis, Plane, Projection, AABB)

B5 剩余三批(44 工具)已按 manifest 精确切分并在 TASK-034/后续任务书中固定:
  批次 2 (15): audio_write 4 + audio_read 2 + particle_write 4 + particle_read 1 + theme_write 1 + scene_3d_write 1
    + profiling_read 1 + navigation_read 1, **外加 §0 的 4 个 schema override**;
    注意引擎槽位约束(E-4): set_particle_material/set_material_3d 必须真正尊重 material_slot(迁移源读了却硬编码 0)
  批次 3 (15): tilemap_write 3 + tilemap_read 3 + shader_write 2 + project_shader_write 2 + project_shader_read 2
    + physics_write 1 + physics_read 2 (**含 2 个 fix-first**: tilemap 数据破坏族; 另 E-5: set_shader_param 必须用
    ShaderMaterial::set_shader_parameter 而非复合属性路径直写)
  批次 4 (14): navigation_write 2 (**含 bake_navigation_mesh 这个 fix-first**) + running_game_navigation_write 1
    + project_theme_write 5 + project_theme_read 1 + project_export_read 2 + project_android_read 1
    + os_android_read 1 + os_android_write 1

## D88 — TASK-034 交付（B5 批次 2，15 工具 + 4 个 schema override）+ 三项裁决；派批次 3（含 2 个 fix-first + E-5）

TASK-034 交付(B5 批次2 15 工具 + 4 个 schema override) + 三项裁决; 派批次3(含 2 fix-first + E-5)

TASK-034(提交 d744a100bc/f9a8797a1f/0eada018d6, 引擎锚点 fc724ce49a): 六门全绿
  ① 8/8 组(每组 3/3); ② 线上 114/114; ③ 239/239 (12198 断言); ④ 1665/1665 (436480 断言);
  ⑤ accept 22/22 x2(派生并集 142, editor 120 / game 53); ⑥ 38/38 pins + --coverage 17 拼写 + 探针 101/101;
  回归 mcp030 22 / mcp032 39 / mcp033 75 全绿; 9877 PID 36392 未动; 未 push
  §0 四个 schema 缺口经 3 条 mode=replace override 收口(生成器 1.8.0 -> 1.9.0, overrides 14 -> 17):
    add_state_machine_state.animation / set_blend_tree_node.animation / add_state_machine_transition 的
    xfade_time + priority + advance_condition; 重生成契约(sha bc8c37a0…) 且 _meta.map_sha256 未变;
    结构化 diff 证明只有 3 个工具的 inputSchema 变化
    **不可达 → 可达**双重证明: 结构性(HEAD 契约缺该成员 / 线上调用答 animation='')+ 线上(声明后写入、读回、
    并把 transition 自己的 advance_condition_parameter 原样喂进 editor_set_animation_tree_parameter)
  §1 15 工具(8 组) + **E-4 槽位证据**(真实双面 MeshInstance3D: surface_material_override/0 = a.tres, /1 = b.tres
    分别正确 —— 迁移源硬编码槽 0 会在这里失败; 槽 2 -> -32001 建议 0..1; 非数字拼写 -> -32602)
  自捉并修的一处真缺陷: advance condition 必须在 AnimationNodeStateMachine::add_transition **之后**设置
    (animation_node_state_machine.cpp:1581 的连接才让 AnimationTree 刷新其缓存的 parameters/... 列表) ——
    修复前工具会答出一个它自己都喂不回去的参数名(零字符串手术链当场抓到)
  两条零字符串手术链(audio 5 工具 / particles 5 工具), 脚本自断言 0 次字符串操作
  进度: B5 29/58, 11/26 组

裁决(三项):
  (a) **批准** editor_set_material_3d.material_slot 由 string 改为 **integer**(SCHEMA_OVERRIDES + 重生成 + 指纹):
      引擎 API 取 int 表面索引, 把索引声明成字符串是迁移源 GDScript `str()` 的历史包袱, 属 GDR-23 意义上的不顺手;
      并要求顺带普查「其它把索引/序号声明成字符串」的参数(已实现 + 未实现 171 条), 列清单, 本批只修这一个
  (b) **批准** editor_add_audio_bus.after_bus_index 越界 -> -32602(不做静默 append/clamp): 与'不得静默重解释'一致, 无需改动
  (c) **门⑥ 的 PINNED.line 只是文档**: 位移不失败 -> **后续批次无需为对齐行号去改它**;
      批次义务 = 新增收窄点必须标注 + 跑门⑥ 三段式(这条纠正了 TASK-034 每批手动重钉 34->38 的惯例, 属无谓工作)

批次 3(TASK-035, 15 工具)含**两个 fix-first**(editor_set_tilemap_cell / editor_set_tilemap_cells_in_rect:
迁移源未正确校验/使用 source/atlas 坐标 = **数据破坏类**; 批量必须全成功或全回滚, remove_all 给真实删除计数,
读族必须能读回写族的内容)与 **E-5**(editor_set_shader_param: 实测'复合属性路径直写'是否真的生效;
若静默失效即为第三类'报成功但没发生'; 仍应改用 ShaderMaterial::set_shader_parameter)
批次 4(剩余 14 工具)含第 3 个 fix-first(editor_bake_navigation_mesh)与 Android/export 组;
  Android/export 组需要 Android 导出环境 -> **预授权**: 无设备/无 SDK 时, 诚实的**能力感知拒绝**(-32000 + 建议)
  与「能力缺失」证据即为正确结果, **不得**伪造成功; 由 M5 验收决定该类是否记为已声明不可验证能力

## D89 — TASK-035 交付（B5 批次 3，15 工具）：两个 fix-first 是数据破坏级；E-5 结论=拼写问题；派最后一批

TASK-035 交付(B5 批次3 15 工具) —— 两个 fix-first 是数据破坏级; E-5 结论=拼写问题; 派最后一批

TASK-035(提交 1e8b4075ee/de96b61b18/1ce26e58d0, 门时 --version de96b61b1 == HEAD): 六门全绿
  ① 7/7 组 x 3/3(两端点); ② 线上 67/67; ③ 251/251 (13978 断言); ④ 1677/1677 (438260 断言);
  ⑤ accept 22/22 x2(implemented 135 editor / 57 game); ⑥ 38/38 pins + coverage + 探针 101/101;
  回归 mcp030 22/0、mcp032 39/0、mcp033 75/75、mcp034 109/114(5 条失败是该冻结脚本的 HEAD 相对 before 断言,
    已核对 fc724ce49a 无 advance_condition/xfade_time 而 e6b50d9884 已含); 9877 未动; 未 push
  进度: B5 44/58, 18/26 组

★ 两个 fix-first 都是**数据破坏级**(红阶段 7 用例/53 断言失败):
  editor_set_tilemap_cell: 迁移源调用单参 TileMapLayer::set_cell(coords) —— 那实际是**擦除**形状
    (source 默认 TileSet::INVALID_SOURCE), 即**把格子清掉却回 set:true**;
    修后按 (source_id, atlas_coords) 对 TileSet 解析校验, 未知 source/atlas 在碰格子之前 -32602,
    写后读回核对(不一致报内部错)
  editor_set_tilemap_cells_in_rect: 迁移源**完全丢弃 source_id/atlas_coords**; 修后先整体预校验(上限 65536)、
    快照 get_used_cells()、写后逐个核对、任一步不符则**整块恢复**(restored)
  editor_remove_all_tilemap_cells: 由**常量 0** 改为真实 removed/remaining/cell_count_before

★ E-5 实测结论(三条可验证事实): 迁移源的裸 Object::set("slot:shader_parameter/<name>") 是**静默空操作**
  (Object::set 不切 ':' , 落到 _setv 后参数仍为 NIL); 而引擎的 set_indexed 路径**是通的**
  (本模块自己的 editor_set_node_property 走它, 线上把 albedo 真的改动了并被读回);
  → 迁移源的缺陷是**那种单次 set 的拼写**(第三类: 报成功但没发生), **不是引擎能力缺失**
  工具改用 ShaderMaterial::set_shader_parameter + 用 Shader::get_shader_uniform_list 校验名字 + 读回 +
  在响应里给 write_path; 未知名字 -32001; editor_set_shader_material 真正替换指定槽(含 previous_material/material_slots)

其余: material_slot 经 override 由 string 改 **integer**(生成器 1.10.0, overrides 17->18; 旧十进制字符串仍接受;
  「索引声明成字符串」全量普查 = 171 条 / 255 个字符串参数中**恰好 1 例**, 已修);
  门② 抓到并修掉两处 doctest 漏掉的缺陷(嵌套 JSON 整数以 double 到达 -> 统一走 integral_value;
  vec3 uniform 需先 shape_vector_from_json 再过槽位闸门)

裁决(两项, 执行方上报):
  (a) docs/tool-groups-b5.json 中 editor_set_physics_layers 的注记与 schema/映射不一致 -> 修正注记文本(不改 schema/映射)
  (b) 两个'枚举/索引声明成字符串'候选 -> **都保持 string**: editor_set_shader_material.material_slot 主要是**槽位名**
      (引擎里材质槽就是属性名), 接受十进制索引是便利; editor_simulate_key.keycode 是**枚举名**(KEY_A 之类),
      让智能体写名字比写魔法整数更顺手(GDR-23) -> 报告给理由 + 实测名字写法可用, 不改契约

最后一批 TASK-036(14 工具): navigation_write 2(含**第 3 个 fix-first** editor_bake_navigation_mesh ——
  迁移源未真正烘焙/未回读核实却可能报成功; 引擎侧 bake 是**异步**的, 必须走 GDR-20 延迟通道并用另一工具证明
  真的产出; 不得因'异步难等'退化成假成功) + navigation_read 1 + running_game_navigation_write 1 +
  project_theme_write 5 + project_theme_read 1 + project_export_read 2 + project_android_read 1 +
  os_android_read 1 + os_android_write 1
  **Android/export 预授权诚实边界**: 无 SDK/设备/预设时仍要实现工具, 但要检测'能力缺失'并**诚实拒绝**
  (-32000 + 建议缺什么/怎么装), **不得伪造成功或回显假设备**; 能力缺失本身即有效证据; 报告必须把
  '只拿到能力缺失证据'与'拿到真实成功证据'**分列**, 不得混为一谈
  running_game_move_player_to_target: **不得**只是 position = target 的瞬移, 要按引擎语义(导航代理/寻路)实现,
  并给'真的沿路径移动'的可观察证据(位置随帧变化)

## D90 — **B5 收官 58/58，契约 171/171 全部 implemented**；派 B5/M5 引擎侧独立验收；待用户裁决 hof-rs 暂停

**B5 收官 58/58, 契约 171/171 全部 implemented**; 派 B5/M5 引擎侧独立验收; 待用户裁决 hof-rs 暂停

TASK-036(提交 6e18a00400/05d9bbce37/9d941492b5): 六门全绿(最终二进制 --version == HEAD b547d1a1df)
  ① 9/9 组 x 3/3(implemented_union 148 editor / 69 game); ② 活证据 59/59; ③ 259/259 (15605 断言);
  ④ 1685/1685 (439887 断言); ⑤ accept 22/22 x2(逐字节相同); ⑥ 三段 scanned==pinned==69 + 101/101 探针;
  回归 mcp030 22/22、mcp032 39/39、mcp033 75/75、mcp034 109/114、mcp035 66/67
  (6 条失败全为历史脚本 before 侧锚点随 HEAD 前进失效, 已逐条对齐并证明 TASK-036 未触碰契约文件)

★ B5 收口机器校验: check_tool_groups.py --batch B5 exit 0(distinct 58, 每工具恰一次, 名字都在 171 契约内,
  name 派生 channel/verb 与映射一致, 每组单渠道/单作用域/单 mutating, 组大小<=10, 26 组携带 58 工具);
  --check-completeness exit 0(契约 171 = B1/B2 66 + B3+B4+B5 105, 两两不相交, missing=0, foreign=0)
  -> **171/171 全部 implemented**

第 3 个 fix-first 交付(editor_bake_navigation_mesh): 迁移源把烘焙当**可写属性** ->
  实测 -32602 'value 不能写入 Callable 属性'(名字解析到引擎绑定方法), **零状态改变**;
  修法: GDR-20 延迟通道 + 每帧轮询 is_baking()(上限 1800 帧/25000ms, 只压低框架上限)+ 进入前检查 map 有 region,
  否则 -32000+建议(能力感知); 并用**另一工具** editor_get_navigation_info 复核 0->2 多边形;
  0 多边形时回答带 message 说明'烘焙跑了但没有多边形', 不算成功
running_game_move_player_to_target: **不是瞬移** —— 按引擎语义(NavigationAgent set_target_position/
  get_next_path_position/is_navigation_finished; 否则 NavigationServer map_get_path; CharacterBody 走 velocity+
  move_and_slide)逐帧采样; 实测 22 个互异采样点, 脚本用另一工具跨帧独立看到 5 个位置 92.9->177.4->258.5->343.0->356.2,
  末值与工具自报 final_position 完全相同; 无导航 region 时 -32000 诚实拒绝(绝不退化成直线行走)
主题 6 工具零字符串手术链(create->color->constant->font_size->stylebox->get_info, StringOps=0), 写入全部回读;
  <=0 字号按 §20.6 进 ignored 并标 font_size_readable:false
Android/export: 真实预设 + **引擎自己的 EditorExportPlatform::can_export** 作能力证据; 本机无 SDK/adb/设备/模板
  -> -32000 并列出缺什么; os_list_android_devices 报 'Could not run adb' + missing[](不是 count:0);
  「能力缺失」与「真实成功」分支在报告 §3.1/§3.2 **分列互不混同**; 实现期还修掉一个**假空**缺陷
  (EditorExport 只在 NOTIFICATION_ENTER_TREE 读一次配置 -> 文件后写会被答成'0 个预设', 改为引擎列表非空才用它)
§0 两项收口: editor_physics_write 注记修正(只改文本); material_slot 与 keycode **保持 string** 且名字写法实测可用

待用户裁决(见 D43): M5 的另一半 = **hof-rs 切端点 + 真实 T=1 冒烟**, 而 hof-rs 仍处用户指令的**暂停**状态。
  我已派 B5/M5 引擎侧独立验收(TASK-AUDIT-B5, 覆盖 171/171 对等、契约纪律(18 条 override 可核对)、
  7 个 fix-first + 2 个 unregister、顺手性、门⑥ 对抗、工程门与端口、能力缺失声明),
  并在本轮结束时就「是否解除 hof-rs 暂停」向用户提问; 未获答复前不恢复 hof-rs 侧工作

## D91 — **B5/171 独立验收通过（pass，八类全过）**：Godot 侧全部完成；M5 的 hof-rs 一半待用户解除暂停

**B5/171 独立验收通过(pass, 八类全过)** —— Godot 侧全部完成; M5 的 hof-rs 一半待用户解除暂停

TASK-AUDIT-B5(验收方自建证据, 基准 HEAD c7bb936e00): **verdict = pass**, 八类全过
  ① 171/171 对等: 自解析 tools/list 的 name 字段(禁止文本包含判断) —— 9888=148(43186B)、9889=69(23359B),
     并集**恰为 171**(missing 0/extra 0); 217 组 (name,description,inputSchema) 逐字比对 0 不符;
     scope 双向差集空(editor 148/148、game 69/69; 共享 46/仅 editor 102/仅 game 23);
     125 条跨端点调用全 -32601 且响应无 result; check_tool_groups 无参数/B2..B5/--check-completeness 全 exit 0
  ② 契约纪律: AST 读生成器声明 11+7=18, 与 _meta.overrides 18 逐对相等; 生成器重生成 110770B **逐字节相同** = 无手改;
     清空 override 后结构化 diff 仅差那 18 对字段 + _meta.overrides
  ③ 诚实性: **7 个 fix-first 全部自建证据复验** ——
     tilemap 写 (2,3) 被 editor_get_tilemap_cell/used_cells/info **三个读者读回**, 负坐标往返, source_id=-1 才是显式清除,
     未知 source/atlas 各 -32602 且拒绝后计数不变; 矩形 3x4 filled=12/verified=12, 坏元素整调用拒绝且 used 仍 14;
     烘焙 0->2 多边形由**另一工具**+**直问引擎**双见证, 非 region -32602/未知节点 -32001/无源几何时不认成功;
     早期四个也各自复验(输出面板真清、只断命名目标、auto_dismiss 诚实 -32000、跨进程报告桥接 total=2/passed=1 且
     clear 真的清两侧); **2 个 unregister 未注册**; 30 条探针覆盖 29 个不同 B5 工具全明确报错+建议
  ④ 顺手性: 自跑主题链 6 步 + 移动链 3 步, 对其 22 个工具调用实参做 AST 遍历(禁止嵌套调用/f-string/BinOp/推导式)
     -> offenders=0, STRING_OPS=0; 移动**跨帧 24 个互异位置, 最大单步 20.69 vs 总位移 426.17**(瞬移会是一次等于全程的跳变),
     终点被独立读确认; 无导航 region 时 -32000 拒绝而非直线行走; §23.4 抽样 10/10 三层等价; §23.5 三形态
  ⑤ 门⑥: 三段 + 自造对抗(插入 (real_t)/static_cast<float>/Color{...} 各 exit 1; 只插空行/空白/注释 exit 0 不假红;
     标注未登记仍 exit 1; 逐字节还原且 git status 不变)
  ⑥ 工程门: 门①5 组 x3/3; 门③ 259/259(15605 断言); 门④ 1685/1685(439887 断言); 门⑤ 22/22 x2 且 PASS 清单逐项同序一致;
     门② mcp033/mcp036 exit 0, mcp034(109/114)+mcp035(66/67) 的 6 条失败经只读 git show 独立裁决为**脚本 before 锚点陈旧**
     (HEAD 契约与工作树逐字节相同) 非实现回归
  ⑦ 能力缺失声明: 真实成功分支(真预设/引擎 can_export 原文/export_platform_count=7)与能力缺失分支
     (adb 不在 PATH、SDK 目录不存在 -> -32000 + 建议, **不是 count:0**, 无 APK 产出)分列互不混同, 原始响应均落盘+sha256
  ⑧ 端口: 9877 前后同 PID 36392; 测试仅 9888/9889(另 9890 已释放); 收尾无监听残留、无孤儿; 未改被跟踪文件、无 git 写操作

★ 结论: **Godot 侧 M0-M4 + B5 全部完成且独立验收通过; 契约 171/171 全部 implemented**
  验收方明确声明: 本次 pass **只覆盖引擎侧 B5/171 收口, 不构成对 hof-rs(M5 另一半: 切端点 + 真实 T=1 冒烟)的背书**

遗留(3 条, 均不阻塞收口):
  D1(low): check_tool_groups.py 的 usage 写 [--batch B1|B2|...] 但 --batch B1 被判 unknown batch 并 exit 1
    (B1 的不变式实际由无参数路径执行) -> 修 usage 措辞或让 --batch B1 等价于无参数路径
  D2(low): project_edit_resource(非 B5 工具, 既有实现) 未按 §20.6 落地 ignored 语义: Curve.min_value=5.0 被引擎夹成
    0.99 后列进 changed 而无 ignored 条目; **完全未知的属性名**回成功形状 {changed:{}, message:'No properties were changed'}
    -> 调用方无法区分'没动这个参数'与'这个参数不存在'; 建议未知键 -32602 或进 ignored, 夹取值进 ignored{requested,stored,reason}
  R4(medium, 历史脚本): mcp034/mcp035 各若干条 s0_head_* 断言读 git show HEAD: 并断言**旧形状** ->
    随 HEAD 前进反转; 建议这类脚本**钉显式提交锚点**而不是 HEAD (这正是 D86 纪律的脚本实现)
  风险登记继承: R3 门⑥ 仍是**有限拼写集合**保证(未覆盖边界已打印) -> 必须坚持 §22.3b 规则 2 的三腿;
    R1 editor_set_shader_material 默认 material_slot='material' 依赖节点类型(3D mesh 上省略会 -32602, 属诚实可诊断);
    R2 project_set_theme_font_size(size<=0) 的'写入器说读不回来'与'读者眼中 16 是被设置的'分散在两个工具里
  未确认(继承): 双精度端到端(已登记欠账)、Android 成功分支(本机无 SDK/设备)、§23.4 完整 19x2、
    B5 其余 29 个工具的不存在目标、editor_get_test_report 的编辑器内存累加器成功路径

★ M5 的另一半(**hof-rs 切端点 + 真实 T=1 冒烟**)仍处**用户指令的暂停状态(D43)** ->
  已在本轮向用户提问是否解除暂停; 未获答复前**不恢复 hof-rs 侧工作**(不碰 hof-rs 的 policy/adapter)

## D92 — 用户裁决（hof-rs 保持暂停／只收口 Godot 侧；Android 记为已声明不可验证能力）+ 授权实机游戏开发试测

用户裁决(hof-rs 保持暂停/只收口 Godot 侧; Android 记为已声明不可验证能力) + 授权实机游戏开发试测

用户两项裁决(本轮提问答复):
  ① **hof-rs 保持暂停, 只收口 Godot 侧** -> 我**不碰 hof-rs**(不改其 policy/adapter, 不做切端点与 T=1 冒烟);
     目标里的 hof-rs 一半**因用户指令而不可推进**, 直到用户解除暂停
  ② **Android/export 记为「已声明的不可验证能力」, 不阻塞** -> 与「双精度构建未端到端验证」同性质:
     已在 DECISIONS(D91)、REPORT-036 §3.1/§3.2 与 REPORT-AUDIT-B5 中显式声明;
     有 SDK/设备/模板的机器上按现成脚本(scripts/mcp036_*)重跑即可闭合

用户的**新指令**: 目标收口后授权一个 agent 组织**实机游戏开发试测** ——
  组织者生成**赛车游戏方案** -> 交给开发子代理**真的做出来**; 组织者**不阻塞流程**,
  观察开发子代理的操作并**记录**, 判断**异常情况**与**可优化点**(例: 某工具要多次调用才摸清正确用法 /
  缺少某些工具 / 若干操作本可合并成一个 等等需要发掘的改进)

据此我确立三步(新增工作流, 不在原目标内的编码阶段一/二/三, 而是新的**试测阶段**):
  step 1 (**TASK-037**, 已派): Godot 侧收口残留 —— B5 验收的 3 条遗留(D2 project_edit_resource 的
    成功形状与 §20.6 ignored 语义[**又落回本项目核心命题**: 未知属性被回成成功形状];
    D1 check_tool_groups 的 --batch B1 说法; R4 历史脚本 before 锚点用 HEAD -> 钉显式提交)
    + 2 条 low 风险(R1 shader material 默认槽依赖节点类型; R2 theme 字号 <=0 的写者/读者说法不一致)
  step 2 (**TASK-038**, 已写任务书): **MCP 调用追踪** —— 观察者的**诚实证据源**。
    理由: 若只让开发者自己写日志, 观察者看到的只是**被观察者的自述**(掐掉的摩擦看不见);
    故由模块自己记录每次工具调用的真实事实(seq/连接/id/工具/参数/错误码/耗时/pending/响应大小),
    **可选、默认关闭、零行为变化**(关闭时 tools/list 逐字节相同; 开启时 171 工具响应逐字节相同),
    并配 scripts/analyze_mcp_trace.py 产出摩擦信号(连续失败后成功=多次调用才摸清用法)、
    缺失工具线索(-32601/被反复试探的参数名)、可合并线索(高频 2-3 步 n-gram)、异常(超时/超大响应/单一工具占比>30%)
  step 3 (**试测工作流**, 待 step 1/2 完成后派):
    组织者(Agent A)生成赛车游戏方案 + 观察规则; 开发者(Agent B)用 **MCP 工具**在 **C# 工程**里真的做出赛车游戏
      (M3 已交付 mono 构建与 C# 可跑; 用 C# 同时压测 C# 轴); 观察者(Agent C)与开发者**并行**且**只读**
      (读追踪 + 自己用第二连接探测), **不阻塞**开发者;
      org 最后汇总: 异常清单 + 可优化点清单(附证据: 调用序列/耗时/错误码) + 缺失工具清单 + 可合并操作清单
    试测的产物: 一份赛车游戏(可跑) + 一份**基于真实操作证据的工具改进清单** —— 后者才是这次试测的主要产出

纪律不变: 实现与验收一律委派全新子代理; 我不亲自写业务代码; 每个改动经门①-⑥; 9877 绝不占用;
  hof-rs 侧在用户解除暂停前**不动**

## D93 — TASK-037 交付（Godot 侧收口，遗留为零）+ TASK-038 交付（可选调用追踪）+ 启动实机赛车试测

TASK-037 交付(Godot 侧收口, 遗留为零) + TASK-038 交付(可选调用追踪) + 启动实机赛车试测

TASK-037(提交 a8210611cf 实现 + b6476fc48d 文档; **workflow 返回 null 但实际完成** —— 按 D77 独立核对报告/提交/工作树):
  D2 已修: `project_edit_resource` 的**未知属性**不再回成功形状, 引擎**夹取**值进 ignored(§20.6);
    并同类自查 project_create_resource 与 editor_set_node_property 家族同口径修
  D1(check_tool_groups --batch B1 说法) / R1(shader material 默认槽) / R2(theme 字号 <=0 写者读者不一致) / R4(历史脚本钉显式提交锚点) 全修
  门: ①3/3 x3 组; ②探针 40/40; ③262/262 (15676 断言); ④1688/1688 (439958 断言); ⑤22/22 x2(PASS 清单 diff=0);
    ⑥ 71/71 + 101/101; 回归 6 脚本全绿(mcp036 59/59, mcp035 67/67, mcp034 114/114, mcp033 75/75, mcp032 39/0, mcp030 22/0)
  报告 §10「Godot 侧遗留为零」逐项表 + **如实列出 5 条不可修/超范围残余**(Android 成功分支=已声明不可验证能力;
    门⑥ 有限拼写集合; §23.4 无读者类型; 双精度未端到端; 专用 setter 的'被拒绝'实例未逐一构造)
  过程教训(再次命中 D77): workflow 返回 report:null **不等于没干活** —— 本批实际完成且工作树干净;
    仍按三件事核对(报告文件 46208B / 2 个提交 / git status 干净)

TASK-038(提交 39a4e59b54 实现 + 05054426d4 报告): **可选服务端调用追踪**(观察者的诚实证据源)
  开关: --mcp-trace=<path> > ProjectSettings godot_mcp/trace_file > **默认关闭**(不写文件/不序列化参数/不读时钟);
    启动日志报 trace=off 或 trace enabled + '参数可能含工程内容'
  产物: JSON Lines, 每行 seq/ts_ms/connection/id(原样 token)/method/ok/error_code/error_message/duration_ms/result_bytes
    + tools/call 加 tool/args(规范化 JSON 键排序)/args_bytes/args_truncated + tools/list 加条数 + 延迟调用加 pending_ms/timeout_ms
  零行为变化三条对照(含**与任务前二进制的逐条 sha256 比对**: 22 探针 identical, 含 148 条全量 tools/list;
    关/关/开三跑 stable=22 unstable=0; 门① 逐字通过)
  健壮性: 写失败 WARN 一次并自禁, 只追加, 每行+退出 flush, 不走 safe save, 主线程单帧保证行不撕裂
  分析脚本 scripts/analyze_mcp_trace.py: 四类信号(摩擦=连续失败后成功/同参重复/错误码分布; 缺失工具=-32601 与反复试探的参数名;
    可合并=高频 2-3 步 n-gram; 异常=超时/pending 超上限/响应>1MiB/单工具占比>30%)
  真实样例: 自驱 10 次调用(含 2 条刻意构造的'先失败后成功'、-32601 缺失工具、重复同参、单工具占比 42.9%), 分析器全部抓到
  门: ①3/3; ③272/272 (15831 断言); ④1698/1698 (440113 断言); ⑤22/22 x2(diff=0); ⑥71/71 + 101/101; 契约一字未改
  顺带修 PLAYBOOK: Import-McpProject -NoPort **不等于** --mcp-port=0(前者会让编辑器导入尝试绑定 9877 —— 已实测日志)

规范落笔(决策者, 依 TASK-038 §11 草稿): `DESIGN-DETAIL` 新增 **§24 / GDR-26「可选的服务端调用追踪」** ——
  开关与优先级、JSON Lines 产物契约与字段表、**零行为变化为硬条款**(含'关-关-开'对照组与'与改动前二进制逐条 sha256'证据模板)、
  健壮性、隐私与边界(含参数/默认关闭/不进契约/连接先消失的延迟请求不产生行)、分析脚本的启发式**不是**契约

★ 用户新指令落地: 启动**实机赛车游戏开发试测**(TASK-039, 四角色共用一份任务书: §A 组织者/§B 开发者/§C 观察者/§D 汇总者)
  组织者生成**赛车游戏方案**(车+赛道+检查点圈计时+最小 HUD, 必须用到相当多样的工具)+**观察规则**;
  开发子代理用 **MCP 工具**在 **C# 工程**里真的做出来, **必须逐条记录**: 用了哪个工具/结果/学到什么,
  以及**凡回退到工具之外手段**的'想做什么/试过什么/为什么不行'(=缺失工具的证据源);
  观察者**只读、并行、不阻塞**(以服务端追踪为主, 因为那是真实事实而非被观察者自述; 可用第二连接做只读探测),
  每 30-60s 轮询 seq 断段增量, 直到 DEV-DONE.marker 或 45 分钟预算; 至少给 ≥3 条'多次调用才摸清用法'、
  ≥2 条缺失工具、≥2 条可合并、≥2 条异常/矛盾 —— **没有就如实说没有, 不得凑数**;
  汇总者**自己回追踪原文复算**每条结论(标注实测/推断), 产出四张表(异常/缺失工具/可合并/可优化, 每张都要证据)
  并按证据强度 x 影响面排序, 另单列**疑似缺陷**(最小复现 + 期望/实际 + 证据 sha256 + 严重度)
  四角色**都不得修改模块**(只记录发现; 修复是后续批次), 模块侧不因试测改变(以 git status + 契约 sha256 证明)

## D94 — 实机赛车试测完成：抓到 3 条真缺陷（2 high）+ 缺失工具/可合并/可优化清单；派修复批次

实机赛车试测完成 —— 抓到 3 条真缺陷(2 high) + 缺失工具/可合并/可优化清单; 派修复批次

TASK-039 实机赛车游戏开发试测(4 子代理: 组织者 -> 开发者 ∥ 观察者 -> 汇总者; 观察者不阻塞开发者) **完成**
  产物: docs/reports/RACING-TEST-PLAN.md(414 行, 12 条验收判据 AC-1..AC-12, 16 个工具族约 80 工具, rubric 阈值对齐
    analyze_mcp_trace.py 的 1MiB/30%/12/2 与 mcp_server.h 的 30000ms/8MiB) / RACING-DEV-LOG.md / RACING-OBSERVATIONS.md /
    RACING-FINDINGS.md(68 KB) ; 原始追踪 trace-editor.jsonl / trace-game.jsonl(%TEMP%)
  游戏: 2D C# 赛车工程(%TEMP%/mcp-racing-test), 车/赛道/检查点/圈计时/HUD; AC 逐条有实测响应与 sha256
  ★ 开发者发现**交付的 mono 二进制落后 137 个提交且没有 --mcp-trace** -> 自己串行重建(94s, exit 0)后才等于 HEAD
    -> **教训(交付卫生)**: bin/ 不受版本控制 -> **每次试测/验收前必须重建对应构建**(R-1 的又一次实证;
      且 mono 与 non-mono 是两个不同产物, 不能只重建其一)
  ★ 汇总者**纠正了两份报告的错**(这正是试测该有的产出):
    对开发者日志 7 处纠错(例: '20 次失败是给未挂脚本节点写脚本属性'错, 实际全是 Node 'X' not found;
    §2 B 段行号错; trace sha 是过期快照; project_validate_script 的坏信号名反例不成立; 同时确认其 D-1/D-2 根因与行号逐字正确)
    对观察者多处纠错(它自己的 205 行/28 失败是**窗口快照**, 全量为 298/37; OBS-009 证伪; OBS-018① 在窗口外找到了真 A5)
    对方案 §A 的判据缺陷(AC-6'三工具答案一致'不可满足; 3.1 清单里的 running_game_get_test_report 不存在; A4/A8 用 result_bytes 会假阳性)

★★ 3 条**真缺陷**(不是手感, 是正确性/诚实性; 每条都有可粘贴最小复现 + 源码行号 + 追踪行号 + 响应 sha256):
  D-1(high) editor_add_resource_to_node_property 对**不存在的属性**报 ok 而什么都没发生:
    editor_write_scene_editor.cpp:697 的 node->set(...) **无** object_has_property 检查 + :699-703 **无条件回显**;
    对照 editor_set_node_property 写 no_such_property_zzq 正确回 -32001
    -> 与 TASK-014 D-1 在 running_game_set_node_property 上修掉的是**同一类**, **编辑器写侧漏了**
  D-2(high) editor_connect_signal **不持久化**: editor_node_write.cpp:257 的 connect() **未传 CONNECT_PERSIST**,
    而 packed_scene.cpp:1238 **只序列化带该位的连接**(恢复侧 :760 正是用 CONNECT_PERSIST);
    实测: 连接后 save_scene -> 读盘 .tscn **`[connection]` 块数 = 0**, 重开即消失; 响应里**连 persisted 字段都没有**
    (对照 editor_add_input_action 老实回 persisted:false); grep CONNECT_PERSIST modules/mcp_server/tools/** = **0 命中** -> 系统性遗漏
    **试测的真实后果: 一台不会开始计时的车**(脚本被迫自己 Connect) —— 这条正是'真实使用'才能撞出来的
  D-3(medium) running_game_get_node_properties 对**根本不存在**的属性静默回 null, 而同端点写工具回 -32001 ->
    **一个端点内自相矛盾**, 且契约未记载该 null 语义(running_game_observation.cpp:167-168 注释明文承认该行为)
  另有一条**诚实性澄清**(汇总者主动排除误报): OBS-022 怀疑的'报成功后游戏读到旧值'**不成立** —— 那之间**没有任何 save_scene**,
    游戏读的是未含这些写入的磁盘场景; **不要**把它当 A5 证据

四张表(每张都在 RACING-FINDINGS.md, 带证据并已排序):
  异常 10 条; **缺失工具 6 条**(建工程 / 编译 C# / headless 起游戏 / trace 路径 / 采样原子化 / InputMap 持久化,
    每条都给建议的工具名与签名草案); 可合并 4 条建议 + **3 条明确不建议**(附理由); 可优化 13 条(含分析器与追踪本身的两条取证修复)

裁决:
  (a) **立即修 3 条缺陷**(TASK-040, 红先行 + **同类系统排查**): D-1 还要求**扫遍全部写工具**列出
      '先 set() 再无条件回显成功'的模式并逐条修; D-2 还要求连信号带 CONNECT_PERSIST + 响应给 persisted 布尔 +
      disconnect 能断持久连接 + 排查'其它应为持久/应落盘的写操作'; D-3 二选一(推荐与写侧一致回 -32001)并保证同端点口径一致
  (b) **缺失工具/可合并/可优化不擅自实现**: 新增或合并工具会**改变契约面**(171 条是逐字对等门) ->
      属**治理决策** -> 我把清单与推荐交给用户定夺, **不自行扩张契约**; 用户点头后再按 override/新条目机制立项

## D95 — TASK-040 交付（3 条试测缺陷已修，含 20 处 set() 全排查与赛车下游回归）+ 授权释放我方遗留端口 + M-6 立项

TASK-040 交付(3 条试测缺陷已修, 含 20 处 set() 全排查与赛车下游回归) + 授权释放我方遗留端口 + M-6 立项

TASK-040(提交 8e35a95b94/67e7dbe7c6/b416588b8a/eb28f1fa1a): 三条缺陷红→绿修好, 只改 modules/mcp_server/**
  D-1: editor_add_resource_to_node_property 的裸 Object::set + 无条件回显 -> MCPTools::assign_resource_to_property
    (存在性 -> -32001+建议; 声明类别不符 -> -32602; 写后读回不符 -> -32000);
    **全模块 20 处直接 Object::set()/set_deferred() 逐条排查 -> 恰好 1 处缺口(就是它), 其余 19 处都有前置检查
    或写后归类(changed/ignored)或属性名来自模块自有表** -> 编辑器写族无同类缺口
  D-2: 连接一律带 CONNECT_PERSIST(已存在的非持久连接会被重建), 响应给**从活对象读回的 persisted**,
    editor_disconnect_signal 给 was_persistent; **持久化排查表**证明这是唯一未声明缺口
    (editor_add_input_action 的 persisted:false 是**诚实**的, 行为未改)
  D-3: 选「与写侧一致」(-32001 + 建议), **契约未动**(sha C844EC8A… 未变), 并扩大到 filter/batch 兄弟工具(逐项错误条目)
  ★ **赛车下游回归 35/35**(对试测工程做副本, 源保持只读): 工具建的连接**真的写进 main.tscn**([connection] 计数 0->2)、
    **跨编辑器重启仍在**(工具侧 + 文件内容双向确认)、并且**在运行的游戏里真的被触发**(fired=21) -> 那台车本来会自己计时;
    **反事实结论**: 2026 那版之所以还能计时, 是因为 Main.cs **自己连了按钮**(正是缺陷逼出的 workaround) -> **把 D-2 掩盖了**;
    真正的受害者是没有脚本兜底的那条连接(CP1.body_entered -> LapTimer.OnCheckpointOnEntered)
  门: ①3/3 x3 组; ②47/47; ③276/276 (15875 断言, 红时 272/4 失败); ④1702/1702 (440157 断言); ⑥71/71 + 101/101;
    ⑤两种 accept_m1 各 20 PASS / 2 FAIL, 两次 PASS 与 FAIL 清单完全一致 —— **两条失败都是环境项**:
      (a) 断言'9877 有监听者'失败(用户 Godot 当前未运行) (b) case13 因 9889 被遗留赛车游戏占用
    回归 409/416, 7 条失败全部是同一条环境断言

裁决/授权(本批下发):
  (a) **授权终止我方遗留进程**: TASK-039 试测遗留的游戏 PID 73176(mono 构建, %TEMP%/mcp-racing-test, 占 9889)
      是我方启动的, TASK-040 出于纪律没杀 -> 本批允许终止, **但必须先核实 PID 与命令行确实指向该 scratch 工程与 --mcp-port=9889**;
      **绝不允许碰 9877 的任何进程**; 终止后确认 9889 空闲并复跑门⑤与游戏端口相关回归, 给干净结果
  (b) **M-6 立项**(editor_add_input_action 真的持久化): 目前只改编辑器进程内 InputMap 并诚实回 persisted:false;
      从游戏开发角度**输入动作必须能被游戏看到** -> 让它同时**原子写进 project.godot 的 [input]**、幂等、回读核实,
      persisted 改为**从磁盘回读的真实结果**(失败要诚实 false + 原因); 这是**行为增强、不新增参数**
      (若要动 inputSchema 必须停下来报我, 不得自行改契约); 并同类排查其兄弟工具是否也应能读写工程级输入映射
  (c) O-2 **暂不实现**(editor_add_resource_to_node_property 的 old_value/new_value: editor 侧资源写是另一种形状,
      加它会造出**第二个序列化器**, 违反 GDR-25 单一形状规则) -> 报告确认即可
  (d) O-3 **确认不加 persist 参数**(会动 inputSchema 与 171 条逐字门) -> 日后若要'可选不持久', 作为独立契约变更立项
  (e) 门⑤ 的 9877 环境断言: **不得改成恒真**, 但要能区分'9877 没人在用(环境事实)'与'9877 被我们占了(违规)';

环境事实(记录): **用户当前未运行 Godot(9877 无监听)**; 试测遗留游戏仍在 9889(待 TASK-041 释放)

★ 试测发现但**未擅自实施**的改进(交用户定夺, 因为会**改变契约面**): 6 条缺失工具(建工程/编译 C#/headless 起游戏/
  trace 路径/采样原子化/InputMap 持久化[M-6 已立项])、4 条建议合并 + 3 条明确不建议、13 条可优化
  理由: 新增或合并工具会改变 171 条**逐字对等门** -> 属治理决策; 用户点头后再走 override/新条目机制

## D96 — TASK-041 交付（**门⑤ 首次全绿**）：释放我方遗留端口 + InputMap 真持久化；派最后小批次

TASK-041 交付(**门⑤ 首次全绿**) —— 释放我方遗留端口 + InputMap 真持久化; 派最后小批次

TASK-041(提交 36c485834e/49a99fdf1a/96a2dc3331/6f5b981ac2/100d230673/9f99733f69): 只改 modules/mcp_server/**
  ① **释放我方遗留端口**(核验后终止): 终止前用 netstat+wmic 核实 127.0.0.1:9889 pid 73176 的
     ExecutablePath=...mono.exe、CommandLine=`--headless --path %TEMP%/mcp-racing-test --mcp-port=9889 --mcp-trace=...`
     (与 TASK-039 遗留物逐字一致) -> taskkill 成功; 收尾 **9877/9888/9889 全无监听、零残留 godot 进程**;
     **9877 全程从未被 bind/杀/重启**(机器可核对: guard 报 ours=False asked_by_us=False)
  ② **门⑤ 首次全绿**: accept_m1 x2 各 **22/22**, PASS 清单逐项一致;
     guard_user_port_9877 由 FAIL->PASS 靠新**六分类**(environment_fact_no_listener_before_or_after), **不是恒真**
     (守卫反而更强: 用'自启 pid + 自启命令行'证明**我们**没占 9877); case13 因 9889 空闲而真过
  ③ **M-6 落地**: editor_add_input_action 现在真的持久化 —— 把动作真实状态(deadzone+events)**原子写进
     project.godot 的 [input]**(用引擎自己的 save_custom + rename), 幂等, `persisted` 改为**从磁盘回读**的结论,
     失败诚实 false + persisted_reason; **inputSchema 零改动、契约 sha 未变**;
     线上: 无 [input] 的 scratch 工程写后出现 `mcp041_drive_forward={...}` 且**两个独立游戏进程** InputMap.has_action=True;
     含 `.`/`/` 的名字诚实 false+原因且**不落盘**
  ④ **门⑥ 对作者自己生效**(重要: 门真的会红): 本批新增 2 个 deadzone 比较收窄点未标注 -> 第一次跑
     scanned 73 / pinned 71 **真的红了** -> 标注 + PINNED 登记(safe: 比较自身宽度) + 探针基线 71->73 -> 101/101
  门: ①3/3; ②32/32; ③277/277 (15919 断言); ④1703/1703 (440201 断言); ⑤22/22 x2 全绿; ⑥三段全 0 (73/73 + 17 拼写 + 101/101)
  回归 8 脚本逐条归因: mcp032 38/39、mcp033 74/75、mcp034 113/114、mcp035 66/67、mcp036 58/59、probe037 39/40
    —— **每条唯一失败都是'断言 9877 有监听者'的环境前置**(用户 Godot 当前未运行), 非回归;
    mcp040 两脚本 47/47 与 35/35 **0 失败**

裁决(三项, 见 TASK-042):
  (a) **授权对齐 6 个回归脚本的 9877 环境前置断言**到门⑤ 的六分类形式(不得放松'我们没占用 9877'这个真不变式),
      对齐后复跑并逐条归因
  (b) **授权实测 project.godot 重写影响**(带注释的真实工程): save_custom 会重写整个文件(project_set_setting 的既有行为),
      但 M-6 之后'加一个输入动作'也会带出该副作用(注释丢失等) -> 要么给出'不可避免, 必须记载'(我落规范与工具描述),
      要么给出可行方案(例如只改 [input] 段的局部发布是否可行)
  (c) **O-6 诚实化**: 内置动作名(ui_accept 等)写入后会被镜像进 [input] -> 以诚实为先: 目标动作**已存在**(含内置)时,
      响应必须能区分'**新建**'与'**已存在并被我改动**', persisted 仍从磁盘回读得出(磁盘没变必须 false); 不新增参数
  (d) **O-4 只报告不实现**: 目前唯一输入映射读者只显示**编辑器进程**的映射, 看不到**工程级**真相;
      '新增读工程级输入映射的工具'属**扩张契约**(171 条逐字门) -> 本批只写待立项说明(能力缺口/建议名与签名草案/影响面),
      交用户定夺

## D97 — TASK-042 交付（端口守卫七分类 + project.godot 重写实测 + O-6 诚实化）+ 三项裁决 + 待用户定夺的契约扩张清单

TASK-042 交付(端口守卫七分类 + project.godot 重写实测 + O-6 诚实化) + 三项裁决 + 待用户定夺的契约扩张清单

TASK-042(提交 b72c09a3ea/d5b98df19a/3b7a3c19b1/10dfe36a69/a502516976/8fb95f4208/fee8745aa9): 门批次 19 步全 exit 0
  ① **端口守卫统一**: 抽出 scripts/mcp_port_guard.ps1(**七分类** = 门⑤ 的六类 + 更严的 user_editor_vanished_during_the_run)
     + 探针脚本 21/21(证明每类可达、三类违规必 FAIL, 含 98770-vs-9877 前缀陷阱与 --import 命令行);
     6 个回归脚本 + accept_m1.ps1 全部改用;**复跑** mcp032 38/0、mcp033 74/0、mcp034 113/0、mcp035 66/0、mcp036 58/0、
     probe037 39/0、mcp040 两脚本 47/0 与 35/0 —— **全 exit 0, 旧失败类消失且无新失败**
     (值得记: 只照抄六分类会**放松**旧断言, 故必须加第七类 —— 执行者主动指出并修, 判断正确)
  ② **project.godot 重写影响实测**(带注释真实工程 modules/gdscript/tests/scripts/project.godot 的逐字节副本):
     加一个动作后 407B -> 869B、sha 变; **整文件被 ProjectSettings::save_custom() 重写**, **4/4 手写注释丢失**,
     引擎写入自己的固定 7 行头, 其余行逐字保留; 二次相同调用**逐字节相同**(幂等); 编辑器退出不再改文件;
     源码结论: save_custom -> _save_settings_text 写头 + 所有已存设置(project_settings.cpp:1162-1210/1234-1341),
     ConfigFile::save 也是整文件 -> **引擎写出口无局部发布 API => 重写不可避免**
     **但**: spike 证实可行方案 —— 把引擎自己序列化的那一条 [input] 条目**纯文本拼进原文件**(原 407 字节是**精确前缀**),
     真实游戏进程启动后 InputMap.has_action=true、事件 1 个、既有动作仍在、**注释与手写格式全保留**、游戏不改文件
     -> 实现**故意未做**(绕过引擎写出口的风险面另议, 属用户裁决项)
  ③ **O-6 诚实化已实现**(不新增参数, inputSchema/description **逐字未动**): 响应新增两个正交字段
     action_state = created | pre_existing_modified | pre_existing_unchanged(按**写入前后事件数**判定, 因为
       InputMap::_find_event 会去重同一事件) 与 project_entry = created | replaced | unchanged | none | unknown
       (发布前用引擎 ConfigFile 读磁盘旧状态); persisted 仍严格来自**磁盘回读**
     线上: 新动作 -> created/created; 再调一次 -> pre_existing_unchanged/unchanged; **内置名 ui_accept** ->
       created=false + pre_existing_unchanged + event_count=3 + project_entry=created + persisted=true; 文件里确有 ui_accept=
  ④ **O-4 只报告未实现**: 唯一输入映射读者 editor_get_input_actions 读的是**编辑器进程**的 InputMap
     (main.cpp:2330-2333: 编辑器 load_default(), 只有游戏 load_from_project_settings()) -> 新编辑器进程看不到工程 [input]
     (TASK-041 实测 count=89 且不含刚持久化的动作); 草案名 project_get_input_map, 契约 171 -> **172**
  门: ①3/3; ②30/30 + 21/21 + 32/32; ③277/277 (15948 断言); ④1703/1703 (440230 断言); ⑤22/22 x2(清单一致);
     ⑥ 73/73 + 17 拼写 + 101/101(11 个 pinned 行号漂移: 脚本自身声明非失败 -> 本批**不刷新**,
     因为在门批次跑完后改门脚本会使'绑定的提交'失效 —— 判断正确)
  契约/组清单/DESIGN-DETAIL **未动**(契约 sha C844EC8A… 与 REPORT-041 逐字相同); 9877 全程只观察; 收尾三端口全空

裁决(本批我直接落):
  (a) **副作用不得沉默 -> TASK-043**: 把「整文件重写 + 手写注释丢失 + 其余逐字保留 + 幂等 + 需要就自行备份」
      写进**受影响的每个工具的描述**(DESCRIPTION_OVERRIDES append + 重生成 + 指纹), 并先**逐个从源码确认**哪些工具
      真的会经引擎写出口保存 project.godot(不许猜); **不改实现**; 拼接方案**本批不实现**
  (b) **O-6 接受现状**: 内置动作可被显式覆盖(引擎允许), 且已有 action_state/project_entry 两个诚实字段使之可见 ->
      不改为拒绝; 记录
  (c) **O-4/O-5 待用户定夺**(它们**扩张契约** 171 -> 172+): project_get_input_map(读工程级输入映射)与
      '删除动作工具必须同时清除 input/<action>' 一起立项 —— 属治理决策, 我不自行扩张

★ 交用户定夺的**契约扩张清单**(全部是'新增/合并工具会改变 171 条逐字对等门'):
  A. 6 条缺失工具(试测发现): ①建工程 ②编译 C# ③headless 起游戏 ④trace 路径查询 ⑤采样原子化 ⑥InputMap 持久化[已做 M-6]
     + O-4 project_get_input_map + O-5 删除动作清除磁盘条目
  B. 4 条建议合并 + 3 条明确不建议(附理由) —— 见 RACING-FINDINGS §2.3/§3.2
  C. 13 条可优化(参数/返回形状/错误消息/往返次数; 含分析器与追踪自身两条取证修复) —— 见 §2.4
  D. 拼接发布方案(保住 project.godot 手写注释) —— 绕过引擎写出口, 风险面另议
  另: 试测的**交付卫生**教训 —— bin/ 不受版本控制, mono 二进制曾落后 137 个提交且缺 --mcp-trace ->
    每次试测/验收前**必须重建对应构建**(mono 与 non-mono 是两个产物)

## D98 — TASK-043 交付（5 个工具的「整文件重写」已入描述）+ 四项裁决（含我任务书措辞错误的自纠）

TASK-043 交付(5 个工具的'整文件重写'已入描述) + 四项裁决(含我任务书措辞错误的自纠)

TASK-043(提交 47b5008bac 描述+生成器 / d748214ffc 门批次 / 45076b352b+4b581c782c+82d1b53e6c 报告): 门批次 27 步全 exit 0
  普查(**从源码逐个确认, 不猜**): **恰好 5 个**工具经引擎写出口保存 project.godot ——
    project_set_setting(project_setting_write.cpp:217-218 -> tool_helpers.cpp:571-573 -> :558-566 save_custom 回调
      -> project_settings.cpp:1234-1341 -> :1162-1210)
    project_add_autoload / project_remove_autoload(project_autoload_write.cpp:149-150 / :180-181 -> 同一链)
    editor_add_input_action(editor_input_simulation.cpp:665 -> tool_helpers.cpp:842-863 -> :788-838 -> :815 publish)
    **外加未点名的第 5 个 editor_reload_plugin**(editor_write_scene_editor.cpp:396-397 -> editor_node.cpp:4543-4549/
      :4623-4627 -> :4512-4531 _update_addon_config -> :4530 queue_save -> project_settings_editor.cpp:97-100
      (**1.5s 一次性 Timer**) -> :102-106 save() -> save_custom; **不受 p_config_changed 门控**)
    排除项逐条给理由(rescan/场景/脚本/主题/材质/音频/动画/文本资源写者/cross_scene/export 族/AutoloadSettings UI 等)
  描述: DESCRIPTION_OVERRIDES mode=append 5 条(set_project_setting/add_autoload/remove_autoload/set_input_action/
    reload_plugin), 原文逐字保留在句首, 句尾同一句英文事实; **用条件句 'when this call saves'**,
    因为其中 3 个工具有'成功但不写文件'的路径(名字不存在/无 project.godot/已存在且相同)
  生成器 1.10.0 -> 1.11.0; 契约 110770B c844ec8a… -> 118032B 443f1df2…, _meta.overrides 18 -> 23;
    结构化 diff problems=0(只动这 5 条 description + _meta); 生成器两次同 sha(幂等); **未手改契约**
  行为零改动; 线上核实 16/16(9888 tools/list 45186B sha 23f3bd6b…, 5 条 -ceq 相等且以新句结尾, 其余 143 条逐字未动)
  第 5 个工具独立实测 14/14(带注释工程 + 已启用 addon: 编辑器启动与 --import **都不动文件**(对照),
    一次 reload 后 504B -> 585B、注释 3/3 丢失、引擎固定头出现、其余逐字保留、二次字节不变)
  门: ①x4 3/3(每归属组一次, 否则单跑只覆盖 5 个被改工具中的 1 个); ③277/277 (15948 断言); ④1703/1703 (440230 断言);
    ⑤22/22 x2(清单一致); ⑥73/73 + 17 拼写 + 101/101 + 源码字节还原; 回归 mcp032 38/0、mcp033 74/0、mcp034 113/0、
    mcp035 66/0、mcp036 58/0、mcp040 47/0 + 35/0、probe037 39/39、mcp042 30/0、mcp041 32/0、9877 探针 21/0
  9877 全程 classification=environment_fact_no_listener_before_or_after

★ 执行者指出**我的任务书措辞错误**(自纠): TASK-043 §1.4「实现文件 diff 为空」与 §1.3「只改描述与生成器」
  **不可能同时字面成立** —— **线上描述本身就是 tools/*.cpp 里的注册字面量**, 契约改了字面量必须同步, 否则门①必红。
  它守住'行为零改动', 把 diff 收成 4 文件 5 删 5 增并给机器形状断言(每条增删行都是
  ToolBuilder builder('<5 个之一>', String::utf8(...) 且增行去掉新句后与删行逐字相同, problems=0), tests/ 零改动
  -> 我的措辞错误, 不是它的偏差; 记此自纠以便后继任务书写得更准

裁决(四项):
  (a) **确认'描述字面量属于描述、允许改'**: 保持'契约与线上逐字同步'这一硬要求就必须改该字面量;
      后继任务书不再写「实现文件 diff 为空」, 改写「**行为零改动 + 描述字面量 diff 须有机器形状断言**」
  (b) **语言口径修正(小批次)**: 契约其余描述是中文, 本批 append 的是英文 -> 按'与该工具原描述同语种'改为中文,
      语义不变, 重生成 + 指纹, 门① 逐字通过; 避免同一描述中英混杂
  (c) **editor_reload_plugin 的 1.5s 延迟保存不改为可观测**(行为变更, 需单独立项); 已在描述里用条件句如实覆盖
      'when this call saves' -> 记为**已知限制**
  (d) 继承 D88: 门⑥ 的 11 条 pinned 行号漂移**只是文档**, 不刷新(改门脚本会使'绑定的提交'失效)

## D99 — 用户要求「操作前后截图 + 与操作日志同行记录」：需求确认与设计定型（§25/GDR-27 + TASK-044）

docs(decisions): D99 用户要求「操作前后截图 + 与操作日志同行记录」—— 需求确认与设计定型(§25/GDR-27 + TASK-044)

用户提问/要求: MCP 有截图工具吗? 能否在一次操作时做操作前后的截图, 并与操作日志一起记录, 便于排查问题

事实核查(只读调查, 决策者):
  现有契约里**已有 6 个**相关工具: editor_capture_screenshot{save_path} / running_game_capture_screenshot{save_path} /
    editor_analyze_screenshot_diff{image_a,image_b,threshold}(像素级 a->b 差异图) / running_game_capture_frames /
    running_game_assert_screen_text / project_get_resource_preview
  -> 手工链路今天已能拼出来(截图->操作->截图->diff); 缺的正是**自动化 + 与操作日志绑定**
  editor_capture_screenshot 实现事实(e 1908-1911 行区间读过): 抓 get_base_control()->get_viewport()(**整个编辑器窗口**),
    save_path 支持 res://|user:// 且拒绝 ..; 与 running_game_capture_screenshot 共用
    normalize_screenshot_path / screenshot_png_writer / game_framebuffer_available(均在 tool_helpers);
    **headless 是诚实拒绝**: 先问 display server, 无纹理存储 -> -32000 + 建议(不回空白图); 视口未绘制过帧同 -32000 + 建议
  2D/3D 视口可用性: editor/editor_interface.h:130 get_editor_viewport_2d() 与 :131 get_editor_viewport_3d(int p_idx=0)
    **都存在**(模块里 editor_read_scene_inspector.cpp:492 与 editor_write_scene_editor.cpp:762 已在用 3D 那个)
  -> viewport=editor|2d|3d 可实现

用户四项选择(已答, 必须照办):
  ① 三档开关 --mcp-capture=off|on_error|every_call(**默认 off**)
  ② 取景 viewport=editor|2d|3d(默认 editor)
  ③ **存原图且不设上限**
  ④ 自动跑像素 diff, 把 changed / changed_pixel_ratio 写进日志行

设计定型(决策者, 已写入 DESIGN-DETAIL §25/GDR-27 与 TASK-044):
  **形态 = §24/GDR-26 追踪的可选扩展 => 零契约变更**(不新增工具、不改任何 inputSchema/description, 171 条逐字门不动;
    截图与结论**只进日志与文件, 绝不进响应**)
  时序(诚实 + 零延迟): 收到请求只做**一次 framebuffer 图像拷贝**, **随后照常应答(不等帧)**;
    编码/落盘/diff 全在**应答之后**执行 -> 不改变任何工具的响应内容与时序;
    「前」= 请求到达时最近渲染的帧; 「后」= 生效并**再渲染至少 1 帧**之后(用既有帧计数 + 延迟通道, 与 bake 轮询同法),
    日志带 frames_waited 自证; 应答后**追加一行** {"event":"capture","seq":<同一 seq>,...} 与调用行**同 seq 关联**
  headless 不得静默: status:"unavailable" + reason(不写空白图); 写失败 status:"failed" + reason 且**绝不影响**工具调用
  **不设上限但必须可见**(对用户选择③的保护, 不是偷偷限额): 不设上限、**绝不自动删除任何文件**;
    每行带 total_bytes(累计); 启动日志打印捕获目录与模式; 累计超 1 GB **只 WARN 一次**
  复用而非重写(GDR-25): 把 editor_analyze_screenshot_diff 的像素比对算法从 tools/editor_testing_read.cpp
    **提升到 tool_helpers**, 使捕获与该工具**共用同一实现**(与 TASK-011 提升 PNG 写入器同法), 并证明后者行为不变
  零行为变化: off 时与改动前二进制响应逐字节相同; on 时 171 工具响应逐字节相同(沿用 §24 三条对照模板)
  验收的**存在理由**: 必须构造一个'报成功但什么都没发生'的实验得到 changed:false, 以及一个真实改变得到
    changed:true + changed_pixel_ratio>0 —— 这正是本功能存在的意义(D-1/D-2 家族会被它一眼照出来)

阶段纪律: 需求(用户四项选择)已确认 -> 详细设计已落 §25/GDR-27 + TASK-044; **待用户确认设计后**再派实现子代理(阶段四)

## D100 — TASK-044 交付（操作前后捕获，零契约变更）+ 规范补实测事实与边界 + 批准代价优化（TASK-045）

docs(decisions): D100 TASK-044 交付(操作前后捕获, 零契约变更) + 规范补实测事实与边界 + 批准代价优化(TASK-045)

TASK-044(提交 39fc7179e7 实现 / 57d19f084a 测试与证据 / 0d405fa2a9 + 1dd26a37f8 报告; 最终锚点重建后 --version == HEAD):
  形态: **§24/GDR-26 追踪的可选扩展, 零契约变更**(未新增工具、未改任何 inputSchema/description; DESIGN-DETAIL 一字未改);
    新增 mcp_capture.{h,cpp}(配置解析/三视口取景/帧状态机/落盘/判定/事件行); mcp_trace 增 capture 字段与
    **不占请求 seq 的事件行**; MCPServer 在 poll 之前 begin_frame、之后 tick;
    GDR-25: 把像素比对从 editor_testing_read.cpp 提升到 tool_helpers 供两者共用
  用户四项选择照办: 三档开关(默认 off) / viewport=editor|2d|3d(默认 editor, 游戏侧 viewport=game) /
    **存原图不设上限且绝不删文件** / 自动 diff 出 changed + changed_pixel_ratio
  ★ **存在理由实验当场成立**: 同一 editor_set_node_property 同参调用两次, **两次 error_code 都为 0**,
    而日志第一次 changed:true ratio 0.0200016705515105(106800/5339554)、第二次 **changed:false 且前后 sha256 相同**;
    游戏端点同型(true 0.321502057613169 -> false) -> **'报成功但什么都没发生'从推断变成机器可判事实**
    (这正是 D-1/D-2 家族缺陷的照妖镜)
  视口实测: 2d 2978x1793 / 3d 2978x1790 / editor 3840x2054(整窗) / game 1152x648; 引擎依据 editor_interface.h:125/130/131
  零行为变化: pre(on=改动前二进制重建)/off/on 三跑 22/22 探针(含**全量 tools/list**)逐字节相同, 0 不稳定
  headless: status:unavailable + reason(与既有报错逐字相同), **零文件**, 调用本身不受影响(编辑器调用仍 0/-32001)
  可见性: 15 次捕获后**恰好 30 张图、一张没删**; total_bytes 严格递增; 超阈值**只 WARN 一次**
    (真实 1GB 阈值未活测, 由 doctest 在生产路径上压低阈值验证 —— 如实声明)
  门: ①3/3; ②62/62(editor 40/headless 8/game 9/diff-image 5); ③285/285 (16187 断言); ④1711/1711 (440469 断言);
    ⑤22/22 x2(清单逐行相同); ⑥73/73 + 17 拼写 + 101/101(字节还原)
  回归: mcp043 28 步 / mcp042 19 步 / mcp041 17 步全 EXIT 0, mcp038 zero_change 7/7 + trace_evidence 12/12
  偏差(已报, 诚实): D1 延迟通道的 tools/call 记 unavailable+reason(不静默 skip);
    D3 捕获依赖 --mcp-trace(无追踪时给一次 WARN); D6 真实 1GB 阈值未活测; D8 mcp_capture.cpp 在门⑥ 扫描范围之外

★ D4(**必须记入规范的实测代价**): 响应路径只多**一次 framebuffer 拷贝**(同调用服务端 off 中位 0-1ms ->
  every_call 中位 7-8ms), **但**应答之后的 PNG 编码 + 533 万像素比对占住主线程 ~400ms ->
  **背靠背**往返 18.5ms -> 453.6ms(请求间有空隙时 30.7ms, 说明代价集中在读回来那一刻)
  -> 裁决: 规范**不得**写成'无代价'; 已落 DESIGN-DETAIL §25 第 12 条为**已知代价**

规范落笔(决策者, 依 TASK-044 §16 的 5 项请求): DESIGN-DETAIL §25 增第 11-13 条 ——
  实测事实(三视口尺寸 + 存在理由实验数字) / '零延迟'的准确含义=响应路径 + 背靠背排队代价 /
  边界(捕获依赖 --mcp-trace; 延迟通道记 unavailable; headless 目录空建; **mcp_capture.cpp 在门⑥ 声明范围之外
    => 扫描数不变不能当作'未引入新收窄拼写'的证据**, 该文件须走代码审查 + 行为证据两腿)

裁决: **批准代价优化 TASK-045** —— 把 MCPTools::compare_screenshot_pixels 的 Image::get_pixel() 逐像素读
  改为 Image::get_data() 原始字节遍历(先读引擎源码确认格式/行距/通道语义), 要求**行为逐位等价**
  (threshold 语义/每通道比较/两种差异色/snapped 0.01/尺寸不一致的报错顺序都不变),
  **两个调用方都复测**(editor_analyze_screenshot_diff 的 doctest 与线上证据不变; 捕获对同一对 PNG 给同样的
  106800/5339554), 并给**优化前后耗时与新的背靠背往返数字**; 完成后由**独立验收**覆盖捕获特性整体(TASK-044+045)

## D101 — TASK-045 交付（像素比对 5.7×）+ 规范按实测拆开代价 + 派最后一跳编码代价（TASK-046）

docs(decisions): D101 TASK-045 交付(像素比对 5.7x) + 规范按实测拆开代价 + 派最后一跳编码代价(TASK-046)

TASK-045(提交 46d85b2e1d 实现 / 548a1e2131 测试与证据 / 07d886438a + 9efa1c9ae2 报告): 门全绿
  做法: MCPTools::compare_screenshot_pixels 改用 Image::get_data() 原始字节遍历;
    同尺寸+同格式且属 6 种 byte/255.0 格式走快路径, 否则**逐字回退**原逐像素循环(保留引擎对压缩格式的拒绝行为);
    格式不同**不用 convert()**(理由: 会引入第二套取整且两个调用方都不是该形状, 附 file:line 证据)
  引擎依据: image.h:392(get_data() 返回 const 引用, 零拷贝), image.cpp:3816(get_pixel 的 ofs=y*width+x -> 行距=width*pixel_size 无填充),
    image.cpp:137/3558-3693(各格式每像素字节与解码), color.h:233(get_r8=clamp(round(c*255),0,255))
  **逐位等价三层证明**: (a)穷举 6 格式 x 3 通道 x 256 字节值 -> get_r8/g8/b8 恒等于存储字节;
    (b)A/B 差分: 同图下原始路径 vs 强制逐像素路径, 在 width/height/changed_pixels/total_pixels/identical/
      diff_percentage **以及差异图的原始 get_data() 字节**上全同(含非覆盖格式与混合格式的参考循环);
    (c)线上 pre/post 两二进制: 捕获仍 106800/5339554 与 ratio 0.0200016705515105, 第二次仍 changed:false/0,
      两张 PNG sha 不变, editor_analyze_screenshot_diff 仍 identical=false 106800/5339554,
      **该工具的整包 payload sha256 前后完全相同**(51c69777…, 33405B)
  耗时(进程内 A/B, 同图交替, 打印不断言): 只判 changed 92.15ms -> 16.05ms(**5.7x**); 含差异图 135.03 -> 54.40ms(2.5x);
    同尺寸 PNG 编码实测 177.0 + 179.0ms(**本任务未触及**)
  **如实报未达预期**: 背靠背往返 458.6 -> 386.6ms(**仅 -17%**, 不是数量级) —— 归因**实测而非推断**:
    ~450ms 里比对只占 ~89ms, 剩下 ~357ms 是两张 PNG 编码(实测 356.0ms)
  门: ①3/3x4; ②mcp045 15/15 + mcp044 62/62; ③289/289 (+4 用例/+5125 断言); ④1715/1715 (445594 断言);
    ⑤22/22 x2; ⑥三段 scanned 75/pinned 75 + 101/101; 回归 mcp043 28/28 + mcp042 19/19 + mcp041 17/17 + mcp038 7/7+12/12
  新收窄点 2 处已登记并更新 PINNED(73->75); 诚实项: 红阶段是**实现后受控回退**(非严格测试先行), 但有真红(37 断言失败);
    首轮 gate6c 因探针脚本硬编码 scanned==73 而红, 已改为 75 并整条复跑(记账, 非放松门)

规范落笔(决策者): DESIGN-DETAIL §25 第 12 条**按实测拆开代价** ——
  应答后 = 像素比对 ~89ms -> **~14ms**(TASK-045) + **两张 PNG 编码 ~356ms**(各 ~177ms, 未触及);
  背靠背 18.5ms(off) -> 453.6/458.6(TASK-044) -> **377.6/386.6ms**(TASK-045); 有空隙时 ~30ms;
  **主因是 PNG 编码**; 不得写成'无代价'

裁决: **派 TASK-046(最后一跳, 只动捕获旁路、零契约变更)**:
  (a) **快速压缩**: 捕获落盘走 p_fast=true(引擎 image_to_png 已有该形参 -> PNG_IMAGE_FLAG_FAST);
      **既有截图工具的默认行为不得变**(改压缩级别会改变用户拿到的字节), 只用于捕获旁路; 体积变化要如实报
  (b) **可选缩放** --mcp-capture-scale=1|2|4(默认 1; running_game_capture_frames 的 half_resolution 是先例);
      **关键一致性**: 缩放必须发生在**比对之前**, 使日志的 changed_pixel_ratio 与**文件**永远自洽
      (否则日志数字与拿文件调 editor_analyze_screenshot_diff 的数字会对不上 —— 那是陷阱, 不允许);
      scale=1 时行为必须与 TASK-045 **逐字节相同**
  (c) 实测前后三段耗时 + 新的背靠背(scale=1/2 各给); **没降就如实报**
  (d) 若认为'挪到非主线程'更根本: **先别做**, 给可行性评估(引擎线程模型/资源读回限制/与 GDR-20 的关系)与代价估计, 报我裁决

## D102 — TASK-046 交付（编码 5×，背靠背 −73%）+ 规范收口（§25 第 14–15 条）+ 派捕获特性的独立验收

docs(decisions): D102 TASK-046 交付(编码 5x, 背靠背 -73%) + 规范收口(§25 第14-15条) + 派捕获特性的独立验收

TASK-046(提交 a7b8b5322f 代码 / 5a5fe039f2 测试与脚本 / 264f9564c5 报告(FINAL-ANCHOR) / db12480616 仅文档):
  ★ fast PNG: 捕获落盘走 Image::_save_png_to_buffer(true) -> image_to_png(..., p_fast) -> PNG_IMAGE_FLAG_FAST
    (NO_FILTERS + level3; 引擎锚点 png_driver_common.cpp:128/142-144, pngwrite.c:2172-2184);
    **screenshot_png_writer 一字未改** -> 两个既有截图工具的字节**构造性不变**(p_fast=false 就是原来的 save_png()),
    并有单元证明; 实测编码 **174.1 -> 34.7 ms/帧(5.0x)**, 两帧 354 -> 69.4ms; **体积约 4.5x**(如实报, 诊断产物可接受)
  ★ --mcp-capture-scale=1|2|4(默认 1): 在比对**之前**缩放两帧并在日志行记 scale ->
    **日志数字 == 拿落盘文件调 editor_analyze_screenshot_diff 的数字**(单元 + 线上双证),
    并明确堵住'只缩放落盘图'那个陷阱; 插值用 BILINEAR(LANCZOS 实测 77-83ms/对会让 scale=2 **比 scale=1 更慢**),
    scale=4 会欠采样(已声明)
  ★ 背靠背往返: 458.6(TASK-044) -> 386.6(TASK-045) -> **99.0-101.4ms(TASK-046, -73%)**; 有空隙时 ~30ms 不变;
    管线归因闭合: scale=1 = 69.8(编码) + 14.4(比对) = 84.2ms, 与线上忙时 ~81ms 吻合;
    服务端 duration_ms 仍 off 0 / every_call 7-7.5ms(=一次 framebuffer 拷贝)
  等价性: 同对 PNG 仍 106800/5339554 + ratio 0.0200016705515105; editor_analyze_screenshot_diff 整包 payload
    sha256 仍 51c69777…; pre=off=on 22/22 逐字节相同; mcp044 62/62 与 REPORT-045 一致
  门: ①3/3x5; ②23/23 + 62/62; ③293/293 (21431 断言); ④1719/1719 (445713 断言); ⑤22/22 x2; ⑥75/75 + 101/101
    (本批**零新增收窄点**); 回归 mcp043 28/28 等全 exit 0
  非主线程化(**评估后不做, 我采纳**): ViewportTexture::get_image -> RS::texture_2d_get 在主线程**同步等待渲染线程**
    (server_wrap_mt_common.h:153-165), 那 7-8ms 移不走; 可移的是编码/缩放/比对/写文件, 但 FileAccess::backup_save 是
    **进程级静态**、追踪器 Recorder **无锁**(其行完整性明确依赖'全在主线程', mcp_trace.cpp:230-235) ->
    需要**先在规范里定义有界队列/丢弃语义**; 收益已从 ~357ms 降到 ~84ms => **架构选择而非性能必需** -> 暂缓;
    若将来要做, **先改规范再动人**
  发现并修掉一个**既有假红**: mcp044_capture_evidence.ps1 的 headless 相不等捕获行就读 trace(捕获行晚一帧追加)

★ 我任务书的**措辞/前提错误(自纠)**: TASK-046 说 'screenshot_png_writer 已有 p_fast 形参' —— **它没有**
  (只有 PNGDriverCommon::image_to_png 有; Image::save_png 也没有); 执行者实现了实质并给完整 file:line 链;
  另 'scale=1 逐字节相同' 不可能指 PNG 字节(杠杆① 就是要改它们) -> 已按任务书自身的 §1.4 清单裁定为
  **像素/判定/两个调用方 payload/响应**不变; PNG 字节**故意变**(865c2f93…/87731a87… -> c2d7a1bf…/4516082843…, 五轮可复现)
  -> 教训(本任务第二次犯同类): 任务书提到**既有符号**时, 必须写**确切符号 + 签名 + 它存在的证据**, 否则就写
  '先核实该签名'; 不得凭印象描述既有 API

规范收口(决策者落笔): DESIGN-DETAIL §25 增 **第 14 条**(编码代价已收: fast PNG + 4.5x 体积 + scale 开关与比对前缩放
  的一致性要求 + BILINEAR 选择与 scale=4 欠采样 + 背靠背 99.0-101.4ms + 管线归因 69.8+14.4=84.2ms
  + **捕获行新增 scale 字段**/启动行追加 scale=<n>)与 **第 15 条**(非主线程化: 评估后不做 + 原因 + 若做的前置条件)

裁决: 采纳执行者 5 项建议 —— (1)规范已收口(上条); (2)D-2 的读法如上(像素/判定/payload/响应, 非 PNG 字节);
  (3)保持 BILINEAR(成本导向; LANCZOS 会让 scale=2 比 scale=1 更慢); (4)非主线程**暂缓**(先改规范再动人);
  (5)接受 D-10 的脚本修正(修的是**假红**, 断言未削弱)

阶段五: 派**独立验收子代理**(TASK-AUDIT-CAPTURE)覆盖捕获特性整体(存在理由 / 三档开关与三视口 / 诚实性与边界 /
  零行为变化 / 缩放一致性与代价 / 工程门与端口), 并要求它**自己**用同一对文件复核日志里的比率

## D103 — **捕获特性独立验收通过（pass，零缺陷）**：用户要求的「操作前后截图 + 与操作日志同行记录」已交付

docs(decisions): D103 **捕获特性独立验收通过(pass, 零缺陷)** —— 用户要求的'操作前后截图 + 与操作日志同行记录'已交付

TASK-AUDIT-CAPTURE(独立验收, 基准 1c1895353f): **verdict = pass, defects = []**
  验证方没有采信任何报告: 自己写了**纯 Python PNG 解码器**(zlib+filter 链+max(|dr|,|dg|,|db|)>10)作第三把尺子
  ① **存在理由三路对齐**(自造同参同值重放): 编辑器与游戏端点两次同参写都 error_code=0,
     第一次 changed:true(编辑器 106800/5339554 ratio 0.0200016705515105; 游戏 240000/746496 ratio 0.321502057613169),
     第二次 changed:false/ratio 0; **日志 -> 模块 diff 工具 -> 独立解码器三路逐个整数相同**
  ② 三档开关: off **连目录都不建**; on_error 只对失败调用产 1 对图; every_call 每次 done 恰好 2 个 .png(frames_waited 全 >=1)
  ③ 三视口: 2d 2978x1793(113929B, 2 色, mean_luma 76.18) / 3d 2978x1790(1149064B, 2925 色) / editor 3840x2054(294280B, 432 色),
     像素多样性合格(非 1x1 非全黑), 三者 sha 互异且都能被 diff 工具自比对解码
  ④ 诚实性与边界: headless 3/3 status=unavailable + reason 与既有 -32000 消息**逐字相同** + **零文件** + total_bytes=0,
     调用本身照常; 捕获**绝不进响应**(判定性写入响应体 255B x2 不含 capture/shots; 且 22 探针 on 与 pre 逐字节相同);
     deferred 调用记 unavailable + reason='the call is answered across frames (deferred)...' 不静默 skip;
     **无删除路径**(代码腿: mcp_capture.{h,cpp} 只有 make_dir_recursive_absolute, 无任何 remove*; 实跑腿: total_bytes 15 段严格递增),
     阈值 WARN 的 doctest 19/19 并证明触发后两对 PNG 仍在盘上
  ⑤ 零行为变化: 22 探针(initialize/全量 tools/list/ping/18 条 tools/call)在 pre(2f520cf90, 其父提交即引入捕获的父)/
     off/on 三跑 deterministic=22 unstable=0 changed=0; tools/list 三跑同 sha 4f26919e… 同 45186B;
     契约 sha 443f1df2… 与 git cat-file blob HEAD 同值且最后改动仍是 TASK-043 的 47b500bac
  ⑥ 缩放一致性与代价: scale=2 日志(1489x896/26800/1334144/ratio 0.0200877866257316) == 喂落盘文件给 diff 工具 == Python 解码器, 三者逐值同;
     scale=1 锚点仍 106800/5339554, 整包 payload sha 仍 51c69777…(33405B); 服务端 duration_ms off 中位 0 -> every_call 中位 8ms;
     客户端背靠背 off 中位 18.3ms / every_call 中位 **99.2ms**(min 87.7 max 99.9), 间隔 2.5s 中位 33.5ms -> 与 §25 第14条同量级几乎逐值相同
  门: ①3 组各 3/3; ②mcp010 28/29、mcp019 65/66、mcp027 59/61(**唯一失败类是 9877 环境门**); ③293/293 (21431 断言);
    ④1719/1719 (445713 断言); ⑤22/22 x2(清单 diff 为空); ⑥三段 75/75 + 101/101
  未确认 5 条(诚实): 未自己重建 pre 二进制(用的是既有产物, 仅核验 --version 与父提交等价); mcp027 D8 未在 pre 上复跑(故'无关'是推断);
    自己的脚本缺陷改用直接清点复核; 最后一次调用因进程被杀而无捕获行(设计上晚一帧追加, 未验证优雅退出 flush); '写图失败只 WARN' 未构造真实写失败
  风险 5 条: 捕获**硬依赖 --mcp-trace**(单独给 --mcp-capture 只在 stderr WARN, 客户端看不到 -> 使用方可能误以为'什么都没发生');
    背靠背 ~99ms/次已如实记录; scale=4 欠采样; mcp_capture 不在门⑥ 扫描范围; **9877 无监听者时所有把'pid 不变且不为 -1'当断言的门脚本必然报红**
    (mcp010/mcp019/mcp027 各有 1 条) -> '六道门字面全绿'在用户编辑器未运行时不可达

★ 结论: 用户本次要求(**操作前后截图 + 与操作日志同行记录, 便于排查问题**)已交付且**独立验收通过**;
  它把本项目核心命题('报成功但什么都没发生')从推断变成**机器可判事实**(changed:false)

遗留(小, 后续批次): 把 mcp010/mcp019/mcp027 的 9877 前置断言也按 TASK-042 的七分类对齐(现在只有 7 个脚本对齐了);
  以及若要'退出前 flush', 用优雅退出后再读 trace 验证

## D104 — TASK-047 交付（M0–M5 里程碑闭合清单，当前 HEAD 可复现）+ 3 脚本 9877 对齐 + 优雅退出 flush 收口 + 四项裁决

docs(decisions): D104 TASK-047 交付(M0-M5 里程碑闭合清单, 当前 HEAD 可复现) + 3 脚本 9877 对齐 + 优雅退出 flush 收口 + 四项裁决

TASK-047(提交 05f8713a5d 脚本 / 019c4b0198 文档; 只改 scripts 与 docs/reports, 未动任何 .cpp/.h/契约):
  ① **3 脚本 9877 前置对齐**(mcp010 4 处 / mcp019 3 处 / mcp027 3 处): 旧谓词
     (( -eq ) -and ( -ne -1)) 在本环境(9877 无监听, pid=-1)下**机器求值为 False** =>
     **必然假红并掩盖真回归**; 改走 mcp_port_guard.ps1 七分类并登记自己启动的 pid+命令行;
     真不变式'我们没占用 9877'**保留且加强**(新增 our_pids/our_ports/asked_by_us 三条事实);
     复跑: mcp010 -Phase game **29/29** exit0、mcp019 **66/66** exit0、mcp027 **59/60** exit1(port guard PASS)
     剩余红逐条归因: mcp010 scope/count 的 4 条是 TASK-010 期**硬编码不变式**(48 union / 17-23-8 split / 编辑器端点 40 /
       editor-only 17 game-only 8), 而 accept_m1 独立给出正确的 148/69 与 102/23, completeness 给出 171=66+105;
       mcp027 唯一红 D8 = REPORT-AUDIT-CAPTURE §9.1 已登记的**预先存在** TASK-027 缺陷
  ② **优雅退出 flush 收口**(12/12 PASS): 优雅退出(退出码 0, 非 kill)**不丢已写下的行**(trace 1223B 以 LF 收尾、3 行全可解析),
     **但在飞的捕获行确实被丢弃**(在第 2 次调用内 quit 使'下一帧'永不发生 -> 在飞边界是确定事件而非竞态);
     代码依据: mcp_trace.cpp:235/240-247/194-203 vs mcp_server.cpp:259-283(先 trace close 再 capture stop)
     与 mcp_capture.cpp:406-416(显式 drop)/721-723(_complete 是唯一写入者)/726-755(tick 需 frame>=finish+1)
     => CAPTURE 验收的未确认项收口为'**确认丢弃, 与 kill 无关**'
  ③ **MILESTONES-CLOSURE.md**(主要产出, 全部在当前 HEAD 595607336d 重跑): M0 build_local -Force exit0 + --version==HEAD;
     M1 accept_m1 x2 22/22 且清单逐行相同 + 契约子集 3/3 x2(171/171, editor 148 / game 69);
     M2 groups 无参数(B1, 41 工具)+B2(9 组 25 工具) exit0 + mcp010 game 29/29;
     **M3 重建 mono 构建**(唯一允许的第二次构建, 串行无并发, exit0, mono --version==HEAD) + C# 工程检查 11/11
       (程序集 9728B、游戏端点 tools/list=69 由契约 171-102 机器推导、[MCP014-CS] Main._Ready ran、
        CsharpReport()='csharp: ticks=352 state=csharp-ready'、**C++ 写 CsharpState 后 C# 读回**),
       随后 build_local -Force **恢复非 mono**(1m46s)并复验 --version==HEAD;
     M4 B3(12 组 40 工具)+B4(3 组 7 工具) exit0 + mcp019 66/66;
     M5 B5(26 组 58 工具) exit0 + --check-completeness exit0(**171 = 66 + 105 恰好各一次, missing=0 foreign=0**)
  门: ①3/3 x2; ②29/29 + 66/66 + 59/60; ③293/293 (21431 断言); ④1719/1719 (445713 断言, 0 failed, 3 skipped);
    ⑤22/22 x2(清单一致); ⑥75/75 + 101/101(**探针 log sha 与 REPORT-046 同一 sha = 跨批次可复现**)
  诚实登记: mcp041/042/043 三个门批次聚合器与 mcp044/045/046 证据脚本**本批未跑**, 已在闭合清单 §4 与报告 §4
    **显式写成未跑(不写成通过)**; 未跑就留位置待补

裁决(四项):
  (a) **mcp010 的 4 条 TASK-010 期硬编码不变式**: 不'更新数字'了事, 而是**改为派生**(与 accept_m1 同法:
      从 manifest/契约推导 union 与 scope 集合) -> 这样它随时间自动正确; 若某条在历史上**有意**是快照,
      则在脚本头部**显式标注为历史视角**并**移出 exit 判据**(不得让它持续红而掩盖真回归)
  (b) **mcp014_m3_evidence.ps1:183 的一行缺陷**(Write-Utf8NoBom 未定义, 应为 Write-McpUtf8NoBom): 一行修掉,
      修后在 mono 二进制上完整复跑 -Phase m3(现在只有新增的 mcp047_m3_mono_check.ps1 的 11/11 接续证据)
  (c) **mcp027 D8**(glow_levels/1 is not a settable property name, -32602): 属 TASK-027 议题的**真缺陷** ->
      单独立项修复(OBJECT/数组**子路径**写侧与读侧形状不一致; 与本项目'读回必须能写回'的 GDR-25 直接相关)
  (d) **补跑三个门批次聚合器**(mcp041/042/043)与 mcp044/045/046 证据脚本, 使闭合清单的'逐批次门证据'一栏不留空

目标状态: 目标里的 **Godot 侧(M0-M5 除 hof-rs 外)已完成且当前 HEAD 可复现**; **hof-rs 一半仍按用户指令(D43/D92)暂停**
  -> **目标保持 active**(未完成), 不标 blocked(那是用户明确的范围决定, 不是我被卡住), 继续做 Godot 侧收尾

## D105 — 试测改进清单**独立确认**完成（19 确认／5 部分／3 未确认）+ 排期四档 + 第一批（A 档）开工

docs(decisions): D105 试测改进清单**独立确认**完成(19 确认/5 部分/3 未确认) + 排期四档 + 第一批(A档)开工

TASK-048(提交 cef846a418/f07352c9d1): ①mcp010 的 4 条硬编码不变式**改为派生**(五 manifest implemented 并集 +
  rename map scope + 活端点集合相等) -> -Phase scope 12/13→15/15、count 4/7→12/12 均 exit0
  (union 171 = 102 editor + 46 both + 23 game, 与 accept_m1 独立一致); ②mcp014:183 一行修好
  (Write-McpUtf8NoBom), 按纪律串行重建 mono 后复跑 -Phase m3 -> 现在跑到底 18/20;
  **新暴露两条红(旧缺陷被隐藏, 非回归)**: m09 冻结字面量 49/40(实测 148/69 恰等于该 HEAD 的派生期望)、
  m23 的 pid -gt 0 环境前提(9877 无监听), 同源还有 gate2 的 g06/g26 -> 已登记待处置;
  ③三个门批次聚合器全部 exit0(mcp041 17/17, mcp042 19/19, mcp043 28/28 步);
  ④捕获/成本脚本全 exit0(mcp044 62/62, mcp045 15/15, mcp046 23/23); 五道门 + 门⑥ 三段全 EXIT 0;
  MILESTONES-CLOSURE §4 的'未跑'已替换为真实结果
TASK-049(提交 3193981897283b85a5b8851ff40548d32cdf85a0/5ee2c596a8) —— **mcp027 D8 真缺陷已修**:
  根因: tools/project_write_resource_scene.cpp:147-149 的 _is_settable_property_name() =
  String::is_valid_identifier()(:534-539) **先于**对象属性表判定, 于是把**读侧自己刚产出的**名字
  (Environment.glow_levels/1..7 由 ADD_PROPERTYI 注册为字面属性名, environment.cpp:1464-1470) 拒掉 = -32602
  => 直接违反 GDR-25 §23.4(读到的值必须能原样写回)
  修法(选项 a): **让对象自己的属性表说话**, is_valid_identifier 降为表外名字的回退;
  拒绝语义保留(空名/检查器标签/:路径/a.b/a[0]/空格 -> -32602; 未知标识符 -> -32001);
  写后仍由**读回真值**决定(changed/properties_set/ignored); 红先行(3 用例 0 过/6 断言失败) -> 绿(4 用例 53/53)
  同类普查(活体 ClassDB): **984 个非标识符属性名** / 189 标签, 形状 100% 为 /, 跨 9 个类; 逐形状处置已给
  门: ①3/3; ②35/35; ③297/297 (+4 用例/+53 断言); ④1723/1723 (0 failed); ⑤22 PASS/0 FAIL x2;
    ⑥75/75 + 101/101; 回归 mcp027 **60/60(D8 FAIL->PASS)**、mcp019 66/66、mcp010 29/15/12、mcp041/042/043 全 EXIT 0;
    契约 sha 443f1df2… 未变
  报了一条**相邻缺陷 F-1 未修**(需决策): 未设置的 shader uniform 读回 null(headless RenderingServer 无默认,
  material.cpp:342-347), 而 null 对非 Object 属性被正确拒绝 -> 该对仍不可闭合; 已钉成机器可查边界, 建议
  '读侧答声明默认值 + 显式 unset_properties 字段'(REPORT-049 §8.1)

★ 用户授权: **先独立确认**试测改进清单, **确认存在的再安排开发与修复**
TASK-AUDIT-RACING-BACKLOG(独立验证, 只读, 锚点 5ee2c596a; 对照试测锚点 f34ee937f 工具名集合逐字相同 171/171):
  **30 个判定点: confirmed 19 / partially 5 / not confirmed 3 / 无需动作 3**
  ★ **未确认(纠正清单)**: M-4 给工具起的游戏指定 trace 文件 -> project_set_setting{godot_mcp/trace_file} **已能覆盖**
    (实测子进程写出 trace 并被分析器解析); M-6 InputMap 持久化 -> **TASK-041 已实现**(persisted/persisted_reason/
    action_state/project_entry, 游戏进程 has_action=true); O-3 加 persist 参数 -> **TASK-040 已修行为**, 加开关反制造歧义
  ★ **证伪/伪影**: O-6(a) 的'prefix 尾随斜杠改变结果集'是**测量伪影**(真实语义 begins_with:
    godot_mcp ≡ godot_mcp/ ≡ godot_mcp/tr 逐字相同 234B, od_mcp=0); C-4① 的 editor_set_node_property_batch
    **在试测锚点就已注册**(type-scoped); M-1 的'鸡生蛋'**证伪** —— 无 project.godot 时端点以 **game 角色**起(69 工具),
    project_set_setting 能写出第一份 project.godot, 重启即得 148 条编辑器工具
  ★ **project.godot 专项 4 点全 confirmed**: 整文件重写 + 注释 4/4 丢失**逐字节复现**; 拼接**确实可行**
    (真游戏读到 has_action=true、注释保留、--import 与运行后 sha 不变、幂等);
    **但构造出可复现静默失败 R1**: 当 [input] **不是最后一个节**时朴素追加会把键落进别的节 -> has_action=false;
    另有 R2-R9(重复键/override 段/BOM-CRLF/转义与多行/并发写/与 project_set_setting 行为不一致/引擎格式漂移/无法安全处理须拒绝)
  ★ **最该先做 3 条**: O-1(缺必填参数补 data.suggestion, 横切 171 条, 零契约成本, 集中在注册表两个入口);
    C-3(editor_add_nodes_batch 同批父子: 源码 :251-258 父路径在构造前解析 + 失败全批回滚, 线上 -32001 全批回滚);
    O-9(editor_list_signal_connections 加 scope: 5 节点小场景实测 **60/60 条编辑器内部连接、12659 B**, 按 source 过滤无效)
  ★ **新发现 N-1..N-8**: N-1 无 project.godot 时的引导路径无任何 description 记载;
    **N-2 非 Mono 构建下 project_validate_script 对合法 .cs 报 valid:false/ERR_PARSE_ERROR**(get_language_for_extension
    为 null 时回退 GDScript, project_read_files.cpp:302-305) = **把'语言不可用'冒充'编译失败'**的诚实性缺口;
    **N-3 没有任何工具能写 .csproj/NuGet.config/.cfg**(project_create_script 只收 .gd/.cs) = M-1 残余的最具体边界;
    **N-4 editor_setup_collision_shape 不幂等**(对已有 CollisionShape2D 再调用会造出嵌套形状);
    N-5 O-6 的斜杠归因是伪影; **N-6 试测原始 trace 根本不在仓库**(所以 C-1/C-2/C-6 的频次不可复测, 建议今后当场复制证据进仓库);
    N-7 -32602 应一律附 accepted-parameters(含**嵌套路径**定位); N-8 trace 纯追加(3 个进程追加出 3 个 seq==1 且无代次标记)

裁决: **排期四档**(用户已授权'确认存在则开发修复'):
  **A 档·零契约成本(先做)**: O-1 + N-7 + N-2 + O-11/O-12 + O-7/O-8(仅描述指路)/O-10/O-13
  **B 档·改 inputSchema、条目数不变**: C-3 + O-9 + O-2 + O-4 + O-5 + M-3
  **C 档·新增工具(171 -> 172+, 需新契约条目, 由我方撰写条目)**: M-2 project_build_csharp(唯一'无工具也无组合'的真缺口)
    + N-3 的工程文本写能力 + C-4③ project_validate_scripts + C-4④ editor_set_node_script_batch + M-5 采样步
  **D 档·非契约**: O-11 分析器三处 + O-12 trace_opened 一行
  **明确不做(9 条)**: M-4/M-6/O-3(已覆盖或已修)、C-5/C-6/C-7、激进版 O-8、C-2 合并、max_depth 默认值(归因错误已撤回)、
    **现在做拼接器**(R1 未解决前不做; 仅当'保留注释'成为硬需求时立项, 且必须先解决 R1-R9)
  **契约机制(需明确)**: C 档新增工具 = **在契约里新增我方撰写条目**(名/描述/inputSchema 由我定, 走生成器),
    于是对等门的表述从'171 逐字'变为'**171 逐字 + N 条新增自撰条目**'; 我会在批次任务书里把这一点写清
  立即开工: **TASK-050 = A 档**(O-1 横切 + N-7 含嵌套路径 + N-2 诚实性), 要求**错误码与既有消息文本不得变**
    (只增补 data.suggestion), 并逐条归因受影响的证据脚本(不得为让脚本变绿而放宽断言)

## D106 — A 档交付（O-1 横切 171 条补建议 + N-7 可接受参数含嵌套路径 + N-2 跨语言诚实性）+ 采纳其 -32000 选择

docs(decisions): D106 A 档交付(O-1 横切 171 条补建议 + N-7 可接受参数含嵌套路径 + N-2 跨语言诚实性) + 采纳其 -32000 选择

TASK-050(提交 b8b6553d90 实现+测试+生成器+契约+3 新脚本 / a95c0bf1e8 报告+证据 / 及 5 条仅文档跟进; 最终 HEAD 588f74994 重建后 --version == HEAD):
  **O-1(横切 171 条, 零契约成本)**: 两个注册表入口(call_tool / call_deferred_tool)**统一**补 data.suggestion ->
    点名缺失参数 + **按契约 inputSchema 键序**列出可接受参数名(与 TASK-032 的未知参数门共用同一 helper, 二者不会漂移);
    覆盖 immediate + deferred 两条入口 x 必填「省略」与「为空」两种情形;
    实测 e06/e08/e09(immediate)、e10/e11(deferred)、e16(必填为空)、g01-g03(游戏侧): **96-100 B -> 219-367 B, 消息文本逐字节不变**
  **N-7**: **任何** -32602 都附可接受形态(schema 驱动): 嵌套路径可定位(events[0].type / events[0].keycode / steps[0].type,
    含步解析器的 Parameter 'steps[0]'.type 拼法重组), 形态含 type/enum/requiredness/default;
    契约无法确定性生成时(裸 array 无 items)**说明原因且仍打印可接受清单**; **从不为空**(151 次调用扫描两端口清单 + 活探针证明)
  **N-2(诚实性缺口已修)**: 删除 GDScript 回退; classify_validate_script_mode() 分三态 —— STRUCTURAL(无语言服务器, 语义未变) /
    LANGUAGE_UNAVAILABLE(**-32000 + data.suggestion, 不给 valid 字段**) / COMPILE(该文件自己的语言); 2x2 判定表有单元测试;
    实测合法 res://scripts/legit.cs 由 {valid:false, error_text:ERR_PARSE_ERROR, message:'Compilation failed...'} 变为
    -32000 'this build has no script backend for .cs, so the file was not parsed or compiled' + 指向 module_mono_enabled=yes 的建议;
    valid 语义写进契约描述(DESCRIPTION_OVERRIDES append, 生成器 1.11.0 -> 1.12.0; 契约 118032B/443f1df2 -> 119598B/713d486a), 门① 逐字 True(双端点)
  **横切纪律遵守**: 错误码与既有消息文本**冻结**, 只增补 data 且**不覆盖已有建议**;
    实测 e06 消息仍逐字 'Missing required parameter: path'(96->219B), e15 既有建议 215->215B, e17b 批量信封 582->582B,
    e07 -32001 207->207B, e04/e05 真 .gd 编译 173/230B 不变, e19 transport -32601 102B 不变, 成功链调用逐字节相同
  受影响脚本(逐条归因, **未放松任何断言**): (1)tests/test_mcp_server.h 的 expect_invalid lambda —— 旧行断言
    '-32602 不带 data'(**它把 O-1 缺陷编码成了断言**), 已加强为要求非空建议且含工具名, 其 code+message 检查未动;
    (2)mcp043_gates.ps1 的 gate2g **只挪调用点**(右侧改为与自己同一修订对+sha 钉住, 因为原来指向**活契约**并硬编码生成器 1.11.0),
    mcp043_contract_diff.py 逐字节未动, 复跑 problems=0; (3)mcp044_zero_change.ps1 需要 TASK-044 之前的二进制(本修订无法重建)
    -> **明说未跑**而非用替身; (4)scripts/** 里 250+ 条既有 -32602 断言只查 code + 消息片段(已核对只有那一条查 data 缺失)
  门: ①3/3(双端点逐字, project_validate_script description=True); ②29 条真实请求 + 跨工具链; ③**301/301 (22367 断言)**;
    ④**1727/1727 (446649 断言, 0 failed, 3 skipped)**; ⑤22/22 x2(清单逐字节相同); ⑥75/75 + 101/101(**探针 log sha 与 REPORT-049 同一 sha**);
    契约 diff mcp050 problems=0、mcp043 钉住对 problems=0; 回归 mcp010/019/027 + mcp044 62/62 + mcp045 15/15 + mcp046 23/23 全 exit0
  一处如实归因: mcp041 首跑 gate4 出现引擎侧 [Image] SIGSEGV 但 0 断言失败 -> 用 6 次 A/B 复跑归因并全绿

裁决: **采纳执行者对 N-2 的选择** —— 用 **-32000 + data.suggestion**(而非审计建议的 valid:null):
  null 对客户端是 falsy(易被当成'通过'或'未执行'), 而'**能力缺失 -> -32000**'是 DESIGN-DETAIL §16-10 已确立的规则;
  执行者给了选项与理由(报告 §5.2 / D3) -> 以项目既有规则为准

A 档完成; **B 档(C-3 editor_add_nodes_batch 同批父子 + O-9 editor_list_signal_connections 加 scope + O-2/O-4/O-5 + M-3)为下一批**;
C 档(新增工具 171->172+, 含 M-2 project_build_csharp 与 N-3 的工程文本写能力)与 D 档(O-11/O-12)排队;
目标仍保持 active(hof-rs 一半按用户指令暂停)

## D107 — B 档交付（C-3 同批父子 / O-9 连接 scope / O-4+O-5 schema 补全 / M-3 play 参数）+ 采纳 signal_name 解读 + 措辞教训

docs(decisions): D107 B 档交付(C-3 同批父子 / O-9 连接 scope / O-4+O-5 schema 补全 / M-3 play 参数) + 采纳 signal_name 解读 + 措辞教训

TASK-051(提交 d652a43a35 契约+生成器 / 8b4a65a54f 实现 / 0408da76a9 测试 / b34169d634 证据 / 06abd44ce4 + 9d5e409ae0 报告):
  五项全部落地(红/绿各 25 真实请求 + 8 facts), **契约条目数不变、只改 inputSchema**
  **C-3**: editor_add_nodes_batch 新增可选布尔 resolve_within_batch(**默认 false = 旧语义逐字保留**:
    默认模式拒绝响应与改动前**逐字相同, -32001 / 588 B**); 为真时父路径可引用**本批更早元素**创建的节点
    (e09 单请求建成 P1 与 P1/C1, created[] 给 parent_source=scene/batch, 跨工具链读回属性成功);
    **三类明确拒绝**: 前向引用(e12, -32001 'is created later in this batch (nodes[1])' + 重排建议)、
    同批重名(e13, -32602 + 歧义说明)、无人提供的父(e14, 原文不变) —— **三条都仍整批回滚**
  **O-9**: editor_list_signal_connections 新增 scope=all|user|internal(默认 all = 旧答案);
    判别口径是 callable 方法拼写(含 :: 为引擎/编辑器绑定); 同一 5 节点场景 默认 **59 条 12 412 B** ->
    scope=user **0 条 178 B**、scope=internal 59 条 12 486 B; signal_name=script_changed 两相位同为 15 条(子串语义未改);
    **机器检查证明 connections 数组红绿逐元素相同**(收窄只加过滤, 不改内容)
  **O-4/O-5**(纯声明补全, 行为未改): editor_simulate_input_sequence 补 events[].items(17 成员 + required + enum + 可粘贴样例),
    实测收益当场可见: 同一请求的建议文本由 'the schema declares events as an array with no item shape' 变为
    '(a string, one of: key|mouse_click|mouse_button|mouse_move|mouse_motion|action)';
    running_game_run_test_scenario 的 steps[].properties 由 9 增至 11(+pressed/+strength), 响应逐字相同(行为一直在, 缺的只是声明)
  **M-3**: editor_play_scene 新增 headless(bool, 默认 false)与 extra_args(string 数组, 默认 []);
    默认行为不变(纯函数 build_play_args(p,false,[]) 恰好返回 ['--mcp-port=<p>'], doctest 钉死);
    实测 headless 启动成功 + 子进程命令行 mcp_port_occurrences=1 / headless_occurrences=1 + 游戏端点 9889 直连可用(is_editor=false, tools=69);
    extra_args 里重复的 --headless **去重并在 args_deduplicated 回报**; extra_args 含 --mcp-port(两种拼写) -> **-32602 + 理由**
    (引擎取最后一次出现, 会让 endpoint 说谎)
  契约: 5 条 SCHEMA_OVERRIDES(全 mode=replace, 理由**逐字引用被替换的 required 成员**) + 生成器 1.12.0 -> 1.13.0
    -> 132 684 B / 171 条 / **28 overrides**; 重生成**幂等**(连跑两次同 sha c92b9fd2…); **契约从未手改**;
    mcp051_contract_diff.py 断言 problems=0(只动这 5 条 inputSchema、每条**纯新增**成员 +3/+6/+7/+53/+6、旧成员逐字保留、
    _meta 只动 generator_version 与 overrides、map_sha256/generated_from_sha256 未动); 门① 5 组各 3/3 逐字 True
  门: ①6 次 exit0; ②红绿各 25 请求 + 8 facts(含子进程命令行取证); ③**307/307 (22536 断言)**;
    ④**1733/1733 (446818 断言, 0 failed, 3 skipped)**; ⑤22/22 x2(清单逐行一致); ⑥75/75 + 101/101;
    回归三批全 exit0(mcp010/019/027、mcp041/042/043 398/427/504s、mcp044x4/045/046、TASK-050 证据与 diff problems=0);
    副作用已回滚(task050 历史证据先复制留档再 git checkout 还原)

裁决: **采纳执行者对 O-9 'signal_name' 的解读** —— **保留该过滤能力、不改子串语义**
  (理由: 冻结契约描述 + GDR-17/R-1 判别点; 改成精确匹配属**行为变更**, 不在本批授权内)
★ **我的措辞教训(同类第三次)**: 任务书写 '保留 signal_name 的精确过滤' 容易读成'把它改成精确匹配' ->
  今后写这类要求必须写成 '**行为不变; 该参数的现有语义(子串匹配)保持现状**', 而不是用一个可能被读作变更的动词短语;
  三次同类(D-1 前提错、D-2 scale=1 措辞、本条的'保留…精确匹配')都源于**用简短描述代替确切规格** ->
  规则: 涉及既有行为的要求, 一律写'**现状是什么 + 必须保持什么**, 附现状证据(文件:行或实测)' 

进度: A 档(O-1/N-7/N-2 等)与 B 档(C-3/O-9/O-4/O-5/M-3)已交付;
  下一批 = **C 档**(新增工具, 契约 171 -> 172+ 且条目由我撰写): M-2 project_build_csharp(唯一'无工具也无组合'的真缺口)
  + N-3 的工程文本写能力(.csproj/NuGet.config) + C-4③ project_validate_scripts + C-4④ editor_set_node_script_batch + M-5 采样步;
  之后 D 档(O-11 分析器三处 + O-12 trace_opened 一行); 明确不做 9 条见 D105
目标仍 active(hof-rs 一半按用户指令暂停)

## D108 — 契约扩张机制立法（§26/GDR-28）+ C 档第一批（TASK-052：project_build_csharp + project_write_text_file，171→173）

docs(decisions): D108 契约扩张机制立法(§26/GDR-28) + C 档第一批(TASK-052: project_build_csharp + project_write_text_file, 171->173)

背景: A/B 档已交付; C 档需要**新增工具**, 而此前生成器只做'重命名 + override 既有 174 条'(契约恰好 171 条移植工具) ->
  必须先把**新增机制**写成规范, 否则无法诚实扩张

规范落笔(决策者): DESIGN-DETAIL 新增 **§26 / GDR-28「契约扩张: 新增工具」**:
  1 新增条目**由决策者撰写**(名/描述/inputSchema), 落在生成器 **ADDED_TOOLS** 列表(与两张 override 表**分离**),
    在重命名+override 之后**确定性追加**; _meta 增 added_tools(有序) + added_count; **幂等**
  2 对等门表述随之改变: 门① = '**171 条移植工具逐字 + N 条新增自撰条目逐字**';
    check_tool_groups.py --check-completeness 由 '171 = 66+105' 改为 '**171+N = 66+105+N**', 新增**恰好一次**
    (missing=0 / foreign=0 / duplicated=0)
  3 新增工具也必须进组清单: 落在**新的** docs/tool-groups-added.json(**不改**既有批次清单), 受**同样的组规则**
    (单渠道/单作用域/单 mutating/组大小<=10/名字派生一致); check_tool_groups.py 增 --added 并计入完备性
  4 命名同规(GDR-16/D38): <channel>_<verb>_<object>[_<qualifier>], 渠道限 4 个, 不用 update_, 可判别性优先
  5 新增工具与移植工具**同标准**(三类证据/错误码与建议/写后读回/scope 隔离/门① 逐字/组规则/契约指纹) —— 新增**不是降级通道**
  6 **capability-aware 拒绝**: 依赖外部能力(如 .NET SDK/MSBuild)时缺能力必须 -32000 + data.suggestion(说缺什么怎么装),
    **不得**伪造成功或回显假数据
  7 **不可手改契约**: 一切改动经生成器 + 结构化 diff(只动新增条目与 _meta) + 幂等证明

TASK-052(本批): ①机制(上条) ②两个新增工具, **条目原文由我给定**(见任务书 §1, 实现须与契约字面一致):
  **project_build_csharp**(project/build/csharp; timeout_ms 默认 120000/范围 1000..600000, configuration Debug|Release,
    extra_args[], rescan 默认 true): 跨进程跑 .NET SDK 构建 .csproj, **超时必须真的杀子进程**并如实报 timed_out,
    捕获 stdout/stderr(**截断要标明**), 返回 exit_code/stdout/stderr/duration_ms/command(真实命令行)/project_files/rescanned;
    **失败不得伪造成 exit_code:0**; 无 C# 支持或无 SDK -> **-32000 + 建议**(缺什么/怎么装)
  **project_write_text_file**(project/write/text_file; path/content 必填, overwrite 默认 false):
    **拒绝** project.godot(指向 project_set_setting)与 .tscn/.tres/.gd/.cs(指向专用工具)与 res:// 外/..;
    **没有任何删除路径**; overwrite:false 且已存在 -> 拒绝(不得静默覆盖); 写后**读回核实**返回 path/bytes/sha256/created;
    **原子发布**并说明依据
  价值证明(闭环): **从零只用工具**建最小 C# 工程(project_set_setting 写工程名 -> project_write_text_file 写 .csproj/NuGet.config
    -> project_create_script 写 .cs -> project_build_csharp 构建成功), 逐步给响应与 sha256
  证据要求: 成功构建 + 故意写错 .cs 的非零退出 + 无 SDK/无 C# 的诚实拒绝 + 超时杀子进程;
    四类拒绝 + overwrite:false 命中已存在且**文件字节未变** + 写后另一工具读回
  门: 五道门 + 门⑥ 三段式 + --check-completeness/--added exit0; 回归 mcp041/042/043 + mcp010/019/027 + mcp044/045/046
    + TASK-050/051 证据脚本逐条归因; 不可构造项显式声明

C 档余下(下一批): C-4③ project_validate_scripts、C-4④ editor_set_node_script_batch、M-5 采样步; A/B 档已完成
目标仍 active(hof-rs 一半按用户指令暂停)

## D109 — C 档 1 交付（**契约 171→173** + 只用工具的 C# 工程闭环成立）+ 错误码改判 + 派 C 档 2（TASK-053）

docs(decisions): D109 C 档 1 交付(**契约 171->173** + 只用工具的 C# 工程闭环成立) + 错误码改判 + 派 C 档 2(TASK-053)

TASK-052(提交 c1f3385daf 机制 / 2b2cbdeec2 两工具 / f38d240abb doctest / 2218613a33 证据与报告; 两个二进制自报 f38d240ab):
  **① 机制落地**: 生成器 v1.14.0 新增 **ADDED_TOOLS**(与两张 override 表**分离**), 在 rename+override 之后确定性追加;
    _meta 加 added_tools/added_count; 契约 **171 -> 173**, 连跑两次同 sha(1cb68de8…); 结构化 diff **34 checks/0 problems**
    (171 条移植条目**逐字不变**、新增恰为末两条、_meta 只动 count/generator_version/added_tools/added_count、map_sha256 未动);
    --check-completeness 证 **171+2 = 66+105+2**(四桶互斥); --added 校验**新**清单 docs/tool-groups-added.json(3467B),
    **既有五份批次清单与 tool-rename-map.json 一个字节都没变**;
    注册表为新增动词保留**一个显式扩展**(MCP_ADDED_TOOL_VERBS = {build, write}), **与映射自带的 37 词表分开**, 使后者逐字不变
  **② project_build_csharp**: 跨进程 dotnet build(**可轮询 pid + PIPE_NOWAIT, tick 不阻塞**); 一次调用处理找到的每个 .csproj;
    **超时真的杀子进程**(把传输层上限算进去: effective=min(requested, pending_timeout_ms), 提前 400ms, OS::kill),
    如实回 timed_out/killed/exit_code:-1; **失败绝不伪造成 0**(实测 exit_code=1 + 1729B stdout);
    输出按流按项目 64KiB 上限 + **显式 truncated 标记**; 能力缺失 -> -32000 + 建议(装 SDK/用 C# 构建)
  **③ project_write_text_file**: 经既有 publish_text_atomically 原子发布 + **写后从盘上读回**(返回 sha 与 Get-FileHash 相符);
    拒 project.godot(大小写不敏感, 指向 project_set_setting)与 .tscn/.tres/.gd/.cs 家族(各指向专用工具)与
    res:// 外/含 .. 段/只给目录 -> -32602 + data.suggestion; **完全没有删除路径**(schema 恰三个成员, 删除形状的参数被注册表当未知参数拒绝);
    overwrite:false 命中已存在 -> 拒绝且**文件 sha 未变**(绝不静默覆盖)
  **④ 闭环(本批价值证明)**: **只用工具从零**建最小 C# 工程 ——
    c1 project_set_setting{application/config/name} -> saved=true; c2/c3 project_write_text_file 写 .csproj/NuGet.config(sha 与盘上相符);
    c4 project_create_script 写 .cs; c5 project_build_csharp -> **exit_code=0, duration_ms=2505,
    command='...dotnet.exe build ...Mcp052Loop.csproj -c Debug', dll 4096B sha256 707db412…**;
    c6/c7 故意写错的 .cs -> exit_code=1(**失败没被伪装**); c9/c10 挂住的 MSBuild + timeout_ms=2000 ->
    **timed_out=true/exit_code=-1/killed=true/duration_ms=1600**(正是 2000-400); c11 事后无遗留 dotnet pid;
    c12/c13 工具写的 .cfg 被**另一个工具**读回(零字符串手术链)
  线上: 契约 173; **9888=150 / 9889=71**(由映射 + 新增清单**派生**, 非硬编码); 两个新增条目在**两端点逐字 True**
  门: ①3/3 x2 组; ②53/53; ③**315/315 (22935 断言)**; ④**1741/1741 (447217 断言, 0 failed)**; ⑤22/22 x2(清单一致);
    ⑥75/75 + 101/101; 回归 mcp041/042/043 + mcp010/019/027 + mcp044/045/046 + mcp047(mono 11/11, 独立确认游戏端点 71)
    + mcp050/051/052 全 exit0(逐条归因); 9877 未占用; 未 push

裁决(错误码改判, 已落 §26/GDR-28 第 10 条): project_write_text_file 在'**目标已存在且 overwrite:false**'时
  **不用 -32001**(GDR-14 的 -32001 = **你要找的东西不存在**, 此处它**存在**), 也**不用 -32602**
  (该参数**已声明且取值合法**) -> 用 **-32000 + data.suggestion**(点名 overwrite:true), 因为**是状态**不允许该调用;
  并**必须**同时证明拒绝后**文件字节未变**。执行者按我任务书字面用了 -32001 并**主动指出该冲突** -> 我改判, 它没错

★ 又一次措辞教训的印证(D107 立的规则生效): 执行者在我没写清'错误码语义'的地方**主动上报冲突**而不是硬套,
  这正是'涉及既有语义的要求要写现状 + 必须保持什么'的价值

TASK-053(C 档 2, 已派): ①错误码改判落地 + 更新受影响的 doctest/证据期望; ②新增三个:
  **project_validate_scripts**(批量校验, **语言不可用必须与校验失败区分**, 沿用 TASK-050 的 -32000 口径);
  **editor_set_node_script_batch**(批量挂脚本, **全成功或全回滚**, keep_existing 跳过并计入 skipped, 逐节点读回核实);
  **M-5 采样步**(给既有采样读取工具加步长参数, **默认保持现语义** + 逐字节对照)
  契约 173 -> **176**; 机制沿用 ADDED_TOOLS; 回归逐条归因
C 档之后: D 档(O-11 分析器三处 + O-12 trace_opened 一行); A/B/C 档完成后可考虑对新增工具做一次独立验收
目标仍 active(hof-rs 一半按用户指令暂停)

## D110 — C 档 2 交付（**契约 173→175**）+ 两处我的任务书纠错 + 发现引擎级诚实性缺陷（D-053-3）+ 派 TASK-054

docs(decisions): D110 C 档 2 交付(**契约 173->175**) + 两处我的任务书纠错 + 发现引擎级诚实性缺陷(D-053-3) + 派 TASK-054

TASK-053(提交 96c1693d3d/db0566242b/e33c5b4dc9; plain 与 mono 二进制均自报基准 c4823798a):
  §1 错误码改判**已落地**: 占用目标 + overwrite:false -> **-32000 + data.suggestion 点名 overwrite:true**,
    且**拒绝前后文件逐字节相同**(a07); 受影响的 doctest/证据期望已同步更新(未只改实现尺寸)
  新增 **project_validate_scripts**(both/只读): 逐文件 path/language/valid/分类(ok|invalid|language_unavailable)/error_text(截断标明),
    **语言不可用与校验失败分开**(沿用 TASK-050 口径), 返回 count/valid_count/invalid_count/unavailable_count
  新增 **editor_set_node_script_batch**(editor/写): **全成功或全回滚**; keep_existing:true 时已挂脚本的节点
    **跳过并计入 skipped[] + 原因**(不静默覆盖); 逐节点**读回核实**; 失败给 rolled_back:true + 失败项
  **M-5**: 目标工具 = **running_game_get_node_property_samples**(它原本已有管时间的 frame_interval, 新参数是**载荷网格**);
    定名 **sample_stride**(integer, 默认 1, >=1), 走 SCHEMA_OVERRIDES[mode=replace] + 重生成注册段;
    **默认路径逐字节不变**: 295 B sha eef36e62… == 改动前在 c4823798a 上的基线(连跑 3 次同 sha);
    **显式步长**: 180 点 6147 B >> sample_stride=10 得 18 帧/observed 180/**781 B**(-87%);
    sample_stride=0 -> -32602 'must be at least 1'; 规则导出为 MCPTools::sample_is_returned(index, stride) 便于无 SceneTree 单测
  契约: **175 条**(137749 B, sha 65c83ab8…, 生成器 **1.15.0**, added_count **4**), 幂等两次同 sha;
    tool-groups-added.json **4 组**; 线上 **9888=152 / 9889=72**; --check-completeness 打印 **171+4 = 66+105+4**; --added exit0
  门: ①3/3(152/72 逐字); ②**72/72**; ③**325/325 (23430 断言)**; ④**1751/1751 (447653 断言, 0 failed)**; ⑤22/22 x2;
    ⑥ 75/75 + --coverage + **探针 101/101**; 回归 **21 步全 exit0**(含 mcp041 电池内部重跑门①③④⑤x2⑥);
    9877 全程未被占用; 未 push

★ **它纠了我两处(都是我的错)**:
  (1) 我在 §3 写'契约 173 -> **176**', 而 §2 只给出**两条**新增条目、§2.3 又明写 M-5 不改数量 -> 实际 **175**;
      它**没有替我编第三条条目**(按 GDR-28 第 1 条, 条目须由决策者撰写) —— 这是**正确**的做法
      -> 教训: **手写条数 = 又一次'用简短描述代替确切规格'**; 已落 §26 第 11 条: 条数必须从清单**派生**
  (2) 我写'**不改已有条目**'与 M-5'给既有工具加参数'**字面互斥** -> 它按既有 SCHEMA_OVERRIDES(有 _meta.overrides 留痕)处理,
      **其余 172 条逐字不变** -> 已落 §26 第 12 条: 给既有工具加参数走 SCHEMA_OVERRIDES, 新增条目走 ADDED_TOOLS, **两条通道不得混用**

★ **新发现的引擎级诚实性缺陷(D-053-3, 已落 §26 第 13 条)**: CSharpScript::reload() **恒返回 OK**
  (modules/mono/csharp_script.cpp:2593-2620) -> **mono 构建里语法错误的 .cs 也报 valid:true**,
  **单数与批量校验工具都受影响**(同一共享判定); 它**没有单方面改**, 建议单独立项 -> 我立 TASK-054 §1

TASK-054(已派, 三块): ①**C# 校验不得说谎**(二选一: 找到真能区分的引擎信号并给'语法错误 .cs -> valid:false'的线上证据;
  找不到就**下调声明**为 unverifiable + reason + 引擎依据(文件:行), **两个工具口径必须一致**, 描述同步澄清);
  ②**O-12** 追踪**代次标记**(打开文件时写一行 trace_opened: pid/启动时刻/--mcp-port/--version/role, **不占请求 seq**;
  analyze_mcp_trace.py 按它**切段**, 跨运行不再拼接; 不改既有请求行字段);
  ③**O-11** 分析器三处取证修复(摩擦窗口排除'两次之间夹了别的调用'的伪摩擦; n-gram 不跨连接/代次混统计;
  单工具占比/超大响应**排除捕获事件行与 tools/list**, 否则诊断旁路污染自己的统计) 各给修复前后同一份追踪的对照
  **契约条数不变**(本批不新增条目); 回归逐条归因

进度: A 档(O-1/N-7/N-2) + B 档(C-3/O-9/O-4/O-5/M-3) + C 档(新增 4 工具, 契约 171->175) 已交付;
  TASK-054(D 档 + C# 诚实性)在跑; 之后可对**新增的 4 个工具**做一次独立验收, 并复核 §26/GDR-28 的落地
目标仍 active(hof-rs 一半按用户指令暂停)

## D111 — TASK-054 交付（C# 校验下调为不可验证 + 追踪代次标记 + 分析器三处修复）+ 构建依赖缺陷登记

docs(decisions): D111 TASK-054 交付(C# 校验下调为不可验证 + 追踪代次标记 + 分析器三处修复) + 构建依赖缺陷登记

TASK-054(提交 7cafa46e05 实现 / 04d609f9c7 报告注记; 门跑在父树 bd88b1b41 上并注明):
  ① **C# 校验诚实化(引擎级缺陷 D-053-3 收口)**: 读源码后判定方案 (a) **不成立** —— CSharpScript::reload() 恒 OK
     (csharp_script.cpp:2588-2621), 而唯一的'真信号' valid 是**私有**(csharp_script.h:137)且语义是
     '**这个类之前建过吗**'(ScriptManagerBridge.cs:436-463), 根本不是编译结论 => 按 (b) **下调声明**:
     单数工具 -32000 'no compile verdict' + 建议(引 csharp_script.cpp:2588-2621 与 ScriptManagerBridge.cs:436-463);
     批量工具该项 {category:'unverifiable', valid:null, reason, suggestion} + **unverifiable_count**;
     **两个工具的 message+suggestion 逐字一致**(m07 True/True); **.gd 判定与非 mono 的 -32000 口径逐字节未动**
     实测(mono 9888): broken.cs 由 valid:true/category=ok -> unverifiable; legit.cs 同形; valid.gd 仍 ok;
     broken.gd 仍 invalid/ERR_PARSE_ERROR; 非 mono 路径 sha 与红相位相等(1cc98e60…/ba0bc23e…)
  ② **O-12 代次标记**: 新增 MCPTrace::build_trace_opened_fields() + record_event_line(), 在端口解析后写一行
     trace_opened(event,pid,ts_ms,uptime_ms,started_ts_ms,mcp_port,listen,version,role), **不占 seq、不改既有请求行字段**;
     同一 --mcp-trace 文件跨 3 个进程实测: 红 9 行/0 标记/**3x seq==1** -> 绿 12 行/3 标记(pid 77376/81940/83236,
     editor x3, 9888 x3, version==mono --version), 标记不带 seq, 每代仍从 seq==1 开始; 分析器按它切段
  ③ **O-11 分析器三处修复(同迹前后对照)**: (1)摩擦需**同一会话且中间无其它工具调用** -> 编辑器迹 13->12 对
     (被删那对中间夹了 5 个别的调用)、合成 3->2, 两段真摩擦保留; (2)n-gram **按代次分桶**(unigram 把 [gram]
     拆成 21 个字符 -> 1 个名字; 编辑器 bigram 0 -> 10); (3)超大响应**排除 event:'capture' 与 tools/list**
     -> 合成 2->1 + large_responses_excluded=1; 并显式声明'每请求一连接'的退化(<session_keys.degenerate_generations>)
  契约: **175 条不变**(171 移植 + 4 新增); _meta.generator_version 1.15.0 -> **1.16.0**, overrides 29, added_count 4,
    map_sha256 未动; 契约 sha 460004da…; **git diff 只有 4 行**(单数 description+reason、批量 description、generator_version);
    生成器幂等; C++ 注册字面量与契约**程序化核对相等**
  门: ①exit0(9888=152/9889=72, 契约 175, 两组逐字 True); ③**327/327 (23480 断言, 0 failed)**;
    ④**1753/1753 (447703 断言, 0 failed)**; ⑤accept_m1 x2 22/22; ⑥三段 exit0(scanned 75==pinned 75 + 覆盖声明 + 101/101);
    完备性 '171 + 4 = 66 + 105 + 4: PASS' + --added PASS; 门② 红 **44/44** + 绿 **53/53**;
    plain 与 mono 二进制均自报 bd88b1b41; 9877 未占用; 未 push

★ 登记一条**构建正确性**问题(执行者上报, 值得单独处理): **scons 不跟踪'生成的版本头'对 mcp_trace.o 的依赖**
  -> 在 build_local.cmd -Force 里规避(它始终全量重建), 但 **mono 侧须手删该目标文件**;
  这是 R-5('陈旧对象导致假绿')的一个**具体实例** -> 后续应把'生成头 -> 对象依赖'补进构建脚本,
  或让门在跑之前校验'二进制 --version == HEAD'(已有该纪律, 但依赖人工) -> **待排期**

进度: **A 档**(O-1/N-7/N-2) + **B 档**(C-3/O-9/O-4/O-5/M-3) + **C 档**(+4 工具, 契约 171->175) + **D 档**(O-11/O-12) 已交付;
  引擎级 C# 诚实性缺陷已收口(下调声明而非假装能判定)
下一步候选: (i)**对新增的 4 个工具做一次独立验收**(与移植批次同标准, 这是 §26/GDR-28 第 5 条的要求);
  (ii) scons 生成头依赖修复; (iii) 试测清单里明确不做的 9 条保持不做
目标仍 active(hof-rs 一半按用户指令暂停)

## D112 — **授权引擎打补丁**（我决策并执行，用户睡眠中授权自行决策）+ 补丁纪律 + 新增工具独立验收 + 游戏测试循环章程

docs(decisions): D112 **授权引擎打补丁**(我决策并执行, 用户睡眠中授权自行决策) + 补丁纪律 + 新增工具独立验收 + 游戏测试循环章程

用户指令(逐字要点): ①'某些工具拿不到具体的成功和失败响应, 可以考虑给 godot 源码打补丁'; 
  ②'接下来是我的睡眠时间, 你自行决策即可, 不用寻求我审批, 将决策记录即可';
  ③'工具完善后, 继续之前的使用工具进行具体的小游戏开发测试--发现问题改进--继续测试的循环'

★ 决策 1(**给引擎打补丁: 做**)。已确认的'拿不到具体成功/失败响应'有两处**根因在引擎 API**, 而非我们的工具:
  (a) **CSharpScript::reload() 恒返回 OK**(modules/mono/csharp_script.cpp:2588-2621), 唯一看似可用的 alid 是
      **私有**且语义是'**这个类之前建过吗**'(csharp_script.h:137 + ScriptManagerBridge.cs:436-463) ->
      **引擎根本没有对外提供'这个 .cs 编译过吗'的结论** -> 我们的工具只能诚实答 unverifiable
  (b) **project.godot 没有局部发布 API**(save_custom -> _save_settings_text 写头 + 所有设置;
      ConfigFile::save 同样整文件) -> '保住手写注释'只能靠**文本拼接**, 而拼接有 R1 可复现静默失败([input] 非末节时键落错节)
  裁决: 两处都**在引擎侧补最小、只读、朝上游形状的 API**, 而不是在工具里假装能判

★ 决策 2(**补丁纪律**, 新立, 本批起对一切引擎补丁生效):
  1 **最小**: 只加必要接口/字段, **不改**既有 API 签名与语义; 既有 175 条工具行为**必须逐字节不变**
  2 **朝上游形状**: 命名/放置/注释风格与所在文件一致; ClassDB/_bind_methods 按既有写法
  3 **附'为什么需要'**: 源码注释写明'为让上层区分编译失败与没结论'; 报告给**完整补丁清单**(文件/行/新增符号/为什么),
    由我落进 DESIGN-DETAIL
  4 **可被门覆盖**: 新行为必须有 doctest(门③) + 线上证据(门②), 门④ 全量不回归
  5 **不可构造就如实声明**: 若只能做到项目/程序集级真值, 工具回答必须**如实表述为项目级**, 不得冒充文件级

★ 决策 3(**游戏测试循环章程**, 用户要求的循环, 记为长期机制):
  循环 = ①用**当前工具集**做一次**具体小游戏开发试测**(组织者出方案 -> 开发者**只用工具**实现 -> 观察者**非阻塞**记录 ->
  汇总者回追踪原文复算) ②把发现**独立确认**(确认存在才做) ③按确认结果**改进工具/引擎** ④改进经独立验收后**回到 ①**
  每轮试测**必须**: 用 --mcp-trace + --mcp-capture(on_error 或 every_call) 取证;
  组织者/开发者/观察者/汇总者**都不得修改模块实现**(只记录); **证据当场复制进仓库**(N-6 教训: 上一轮原始 trace 没进仓库,
  导致频次类结论不可复测); 每轮的产物是'**一份能跑的小游戏 + 一份基于真实操作证据的改进清单**'
  上一轮(RACING)已产出 26 条清单并完成 A/B/C/D 四档改进(契约 171 -> 175) -> **下一轮试测应在 175 条 + 引擎补丁之上重跑**

本批派发: ①**TASK-AUDIT-ADDED**(独立验收新增 4 工具 + 机制自洽 + 对等门 175, 与移植批次**同标准**, GDR-28 第 5 条);
  ②**TASK-055**(引擎补丁 1: 让 C# 拿到**真正的编译结论** —— 先调研'编译结论落在哪'并给 file:line,
  再按优先级选最小可行补丁面: 文件级真值 > 程序集级真值(如实表述为项目级) > 让 reload() 不再对'源文件与已加载程序集不一致'报 OK;
  然后让两个校验工具用上真值; 证据含语法错误->明确失败 / 合法->明确通过 / '改过但未编译'与'编译失败'区分 /
  非 mono 口径不变 / 既有 175 工具响应逐字节不变(描述变更单独列出))
  下一批: project.godot **局部发布**引擎 API(补丁 2, 一次解决 R1-R9), 随后进入**游戏测试循环第 2 轮**
目标仍 active(hof-rs 一半仍按用户此前指令暂停; 用户本次未解除该暂停)

## D113 — 新增工具验收 fail（D1 阻断）+ **引擎补丁 1 成功（C# 拿到真结论）** + 派修复与重验（TASK-056）

docs(decisions): D113 新增工具验收 fail(D1 阻断) + **引擎补丁 1 成功(C# 拿到真结论)** + 派修复与重验(TASK-056)

★ TASK-AUDIT-ADDED(**verdict = fail**, 唯一阻断项 D1; 锚点 da657ea1f, 验收方自跑 181 断言/349 证据):
  通过项: 机制自洽(重生成逐字节=跟踪文件、幂等、171 条移植逐字未变、新增恰 4 条、_meta 只动预期字段、
    171+4=66+105+4 四桶互斥、--added exit0、五份批次清单 sha 未变);
    对等门(实时 tools/list 解析 9888=152/9889=72、并集=175、逐条逐字相等、scope 双向零泄漏、跨端点 -32601);
    四个新工具 3/4 pass(从零只用工具构建 C# 成功 exit_code=0 + DLL sha; 错 .cs exit_code=1 + CS1002/CS1513;
      超时 1601ms 杀 dotnet:85220 且无孤儿; 无 C# 后端/无 SDK 均 -32000+建议; 写文件读回 sha 一致 + 四类拒绝 +
      overwrite:false 字节未变 + 无删除路径; 批量全成功/keep_existing 跳过+skipped[]/tscn 读回/拒绝信封 rolled_back 且 tscn sha 未变);
    M-5(默认==stride:1 逐字节、stride 语义与点数正确、0/负数/非整数 -32602);
    顺手性(10 工具链、字符串手术 0 次、含建工程→写文件→写脚本→构建闭环); 工程门(13 步全 0; 门③327/0 门④1753/0
      门⑤两跑一致 门⑥三腿 101/101); 端口(9877 全程 pid=-1、只用 9888/9889 并释放、无孤儿、无 git 写)
  **D1(阻断)**: project_validate_scripts 对 category=language_unavailable 条目**发布了 'valid': false**
    (project_read_files.cpp:364 + project_validate_scripts.cpp:168; 只有 unverifiable 走 null) ->
    **违反 TASK-053 §2.1 与诚实性口径**, 且与 TASK-054 的处理**不对称**
  D2(minor 文档漂移): docs/tool-groups-added.json 的 source.entries 仍写生成器 v1.15.0(实际 1.16.0)
  D3(cosmetic): project_build_csharp 的 command 分隔符混用('C:\Program Files\dotnet\/dotnet.exe')
  未确认 3 条(诚实): U1 批量挂脚本的取回腿线上不可达(Object::set_script 唯一拒绝是 is_abstract(), 取回代码已代码审查);
    U2 M-5'默认与改动前逐字节相同'无法独立复现(盘上无改动前二进制, bin/ 不受版本控制) -> 已给同构建等价证明;
    U4 9877 全程无监听 -> '未占用'是真空成立

★ TASK-055(**引擎补丁 1 成功**, commit 5f3e7fb441; scons 严格串行; 9877 全程 guard PASS):
  **调研结论(重要)**: **文件级编译诊断在引擎里根本不存在** —— 只活在 GodotTools 的 MSBuild 管道里
    (GodotBuildLogger.cs:82,89 -> msbuild_issues.csv), 引擎侧从未持有
  **补丁面选择 (c)+(b)**: 引擎侧只加**一个只读访问器** CSharpScript::is_source_newer_than_assembly()
    (csharp_script.h:276-294, cpp:2621, **复用 _update_exports() 已有的比较** at cpp:2174);
    **reload() 的签名与返回值逐字节未动**(D-2) -> 补丁满足'最小/朝上游形状/单一真值来源'
  模块侧: 新增 tools/csharp_verdict.{h,cpp}; project_build_csharp 记下**逐文件诊断 + 构建时 mtime**
    (user://mcp_csharp_build_state.json, **响应字段不变**); 两个校验工具回答
    **ok / invalid + 编译器原文 / not_compiled**(绝不对'没人编译过'答 invalid)
  **真真值证据**: 真 Godot.NET.Sdk 构建 -> 语法错误 = invalid + **CS1519/CS1002 文本**; 合法 = ok;
    **改过未编译 = not_compiled, 且与'编译失败'在同一份响应里区分**; 非 mono 的 -32000 逐字节不变;
    pre/post 35 探针 = 23 相同 + **12 处已声明差异**(10 个 C# 探针 + 2 个 tools/list), 移动条目**恰好是两个校验工具**
  门: ①x2 exit0(9888=152/9889=72/契约 175 逐字); ③**327/327 (23521 断言)**; ④**1753/1753 (447744 断言)**;
    ⑥x3(101/101); 完备性 171+4=66+105+4 exit0; 回归 mcp053 73/73 + mcp054 green 53/53
  **声明未跑(D-1)**: accept_m1 x2 与 mcp041/042/043、mcp010/019/027、mcp044/045/046、mcp050/051/052 ->
    我派 TASK-056 补跑
  残余(已声明): 单数 error_text 无上限 vs 批量 400B 标记; MSBuild 诊断可能重复; mtime 守卫是秒级分辨率

裁决: ①D1 必修(语言不可用**不得**声称 valid:false; 与 unverifiable 一致用 null + category + reason; 两工具口径一致);
  ②D2/D3 顺手修; ③TASK-055 未跑的电池**补跑**; ④修完**再派全新验收子代理**复核(D112 循环: fail -> 新实现批次 -> 新验收)
引擎补丁 2(project.godot 局部发布, 一次解决 R1-R9)排在其后; 之后进入**游戏测试循环第 2 轮**(章程见 D112)
目标仍 active

## D114 — D1 修复 + 新增工具**重验 pass**（新抓三条：mono 脏树锚点／版本漂移无机器校验／证据被静默覆写）+ 派 TASK-057

docs(decisions): D114 D1 修复 + 新增工具**重验 pass**(新抓三条: mono 脏树锚点/版本漂移无机器校验/证据被静默覆写) + 派 TASK-057

TASK-056(实现提交 75adcdcce8 / 报告提交 427fc79da2): D1/D2/D3 全修 + 补跑 15/15 exit0; 门 9 步全绿; **契约 175 与 sha 9c706054 未动**
  D1: 批量工具三个'无结论'分类统一 **valid:null + reason**, 单数仍 -32000 **不声称**(响应 sha 62c37e40 与 TASK-055 同值);
    前后对照 PRE_POST_COMPARE=PASS; 契约描述本就正确故未改契约/生成器
  D2: source.entries v1.15.0 -> **v1.17.0**(偏离我任务书字面的 1.16.0, 理由: TASK-055 已升到 1.17.0, 写 1.16.0 会再造漂移) -> **判断正确**
  D3: 新增可测纯函数 csharp_executable_path, command 由 C:\Program Files\dotnet\/dotnet.exe 变为 ...\dotnet.exe; 真实构建前后 exit_code 均 0
  补跑: accept_m1 x2 22/22(清单 differ=0) + mcp041/042/043_gates + mcp010 29/29 + mcp019 + mcp027 60/60 + mcp044 40/40 +
    mcp045 15/15 + mcp046 23/23 + mcp050 + mcp051 + mcp052 53/53 + mcp053 73/73 -> **15/15 exit0**
  门: ③328/328(+1 用例) ④1754/1754 ⑥75/75 + 101/101 --check-completeness/--added exit0(175=171+4) ①editor152/game72

TASK-AUDIT-ADDED **重验(全新验收子代理) = pass**(锚点 427fc79da):
  自己重跑: 机制幂等 + 与跟踪契约**逐字节相同**(9c706054…); 171->175 且 4 条为**有序尾**;
  实时 tools/list 9888=152 / 9889=72 **名字完全由契约派生、0 处 name/description/inputSchema 不符**; scope 双向零泄漏 + 跨端点 -32601;
  门 328/328、1754/1754、①4 组、⑥三段 + 101/101、⑤22/22 x2 清单 0 差异; 四个新工具**成功/拒绝/回滚/能力缺失/超时杀进程/无孤儿全部复现**;
  M-5 默认与**改动前基线逐字节相同**且与显式 stride=1 相同; 自造探针 62/62 pass;
  **9877 全程未被监听或请求**; 无孤儿; 跟踪文件逐字节还原(git diff HEAD = 0)
  **D1 复核(逐字节)**: "valid":false 在整个响应里**只出现一次** —— 在 res://scripts/broken.gd(category=invalid);
    两个 language_unavailable 条目(legit.cs / note.gdshader)都带 **valid: null + category + reason + suggestion**;
    **单数与批量对全部 5 个文件结论一致**; 代码腿 project_validate_scripts.cpp:154-176 强制 Variant(),
    doctest test_mcp_server.h:25863-25890 钉 Variant::NIL; tool-groups-added.json 版本三处一致 1.17.0;
    command 只有一种分隔符(PATH 条目带尾反斜杠正是 D3 的触发源)

★ 新抓三条(全部值得修, 已派 TASK-057):
  **D-B1(medium, 构建锚点)**: bin 里的 **mono 二进制是脏树构建**(自报 4e3de1090 != HEAD 427fc79da, mtime 早于提交)
    -> 这正是 mcp052(52/53)与 mcp053(72/73)**唯一**失败项 engines_match_head;
    **上一轮的'15/15 exit 0'在本树上不可复现** -> 修法: 在 HEAD **串行重建 mono** 并复跑到 53/53 与 73/73
    (**又一次 R-5'陈旧二进制/对象导致假绿'的实例**; 这条与构建依赖缺陷同源)
  **R-B2(low-medium, 潜在)**: tool-groups-added.json 的生成器版本是**自由文本**, check_tool_groups.py **完全不校验**
    -> 漂移会**静默复发**(本类已复发两次) -> 加**机器断言**(三处必须相等) + **造一次失败演示**
  **R-B3(low)**: 15 步回归里 **13 步会静默覆写被跟踪的证据文件**(mcp051 还会新建 task051/red/e20_child_status.json)
    -> 重跑会改写历史取证(人工 git checkout 才补得回) -> 电池默认写 %TEMP% 或结束时自动还原并打印清单,
    并给'重跑前后 git status/diff 为空'证据 (**N-6 的近亲: 证据完整性**)

决策(我): 三条**都修**(D-B1 必做, 因为它使'跑过'不可复现; R-B2 把人工纪律变成机器约束; R-B3 保证据完整性);
  并派 **引擎补丁 2**: ProjectSettings **局部发布** —— 现状 save_custom/_save_settings_text 只能整文件重写
  (project_settings.cpp:1162-1210/1234-1341), 而文本拼接有 R1-R9 九条风险 ->
  优先级: ①引擎侧提供'只更新某节/某组键'的写出口(**由引擎序列化目标节, 不让上层做文本手术**);
  ②次优: 暴露分节序列化文本; ③保底: 都不行就**明确不做**并把整文件重写保持为**已声明行为**(现状), **不退回文本拼接**;
  硬要求: 既有 175 工具行为**逐字节不变**(project_set_setting 等默认仍整文件重写),
  注释与其余文本**逐字保留**的字节级证据(含 [input] **非末节**反例/幂等/--import 与运行后不变/BOM-CRLF/并发),
  若要让 editor_add_input_action 用新路径, **必须单列'行为变更'一节**并说明安全性(否则本批只提供 API, 由我另批切换)
之后: **游戏测试循环第 2 轮**(在 175 条 + 两个引擎补丁之上重跑; 章程见 D112)
目标仍 active

## D115 — TASK-057 真相（引擎补丁 2 = **最优面：按节发布，注释/BOM/CRLF 逐字保留**）+ TASK-058 恢复报告 + 派 TASK-059

docs(decisions): D115 TASK-057 真相(引擎补丁 2 = **最优面:按节发布, 注释/BOM/CRLF 逐字保留**) + TASK-058 恢复报告 + 派 TASK-059

TASK-057/TASK-058: TASK-057 **实现已提交但报告缺失**(写完代码即中断) -> 按 D77 独立核对(提交+二进制+工作树)后
  派 TASK-058 **恢复报告并补跑缺项(成功)**
  96f631addb 实际只做了: 引擎 ProjectSettings API(**纯增量 +448/-35**) + R-B2 三处一致的生成器版本断言
    + source.generator_version 字段 + 失败演示 + R-B3 mcp_evidence_guard.ps1(电池默认写 %TEMP% + 自动还原)
    + D-B1 的 mcp057_build_mono.cmd + 门/探针脚本 + 4 个 doctest;
    **没有触碰任何工具源码/注册/契约**
  ★ **引擎补丁 2 走了最优面(面 1)**: update_settings_section_text()(project_settings.cpp:1537, 头 :230) +
    save_custom_section()(cpp:1682, 头 :229), ClassDB 绑定 :2104; 目标节由**同一个 VariantWriter** 序列化(:1551-1559),
    **其余字节全部原样搬过去** —— 注释、键序、**BOM(显式重加 EF BB BF :1712-1721)**、**CRLF(:1631-1637)** 都在;
    LF 与独立构造的期望**逐字节相同 409/409 B**, sha256 5453ba95…
  门: ①3/3 x5 组(contract=175, union 152/72) ③332/332 ④1758/1758 (447860 断言, 0 failed, 3 skipped)
    ⑤accept_m1 x2 22/22 清单一致 ⑥75/75 + 101/101 + --coverage; --check-completeness/--added/--generator-version PASS
    (sha 3bb522d9…); **R-B2 失败演示通过**(3 处漂移被抓 + 3 次逐字节还原); patch2 证据 24/0;
    **回归 15/15 exit0 且 mcp052 53/53、mcp053 73/73**(D-B1 关闭); **R-B3 还原 66/1/0 且 git diff --stat 为空**;
    提交后 build_local -Force 与 mcp057_build_mono.cmd 均 exit0, 两二进制自报 612829827

★ TASK-058 揪出的缺陷(我裁决如下):
  **D-4(medium, 必修, 我批)**: **5 条契约描述仍写'引擎没有局部发布 API / 整文件重写会丢注释'(行 93/787/1572/2201/2220)**,
    已被补丁 2 **证伪** -> **我们自己的描述在说谎** -> 必须**行为切换与描述同批**改:
    把真正**节内写**的工具改用新 API(逐工具判定并列表; **哪些场景必须回退整文件重写**要明写),
    新描述必须说明'按节写入会保留注释与其余文本 / 何时仍整文件重写 / 现在不再丢注释(行为改善)';
    证据: 带注释 project.godot 改前改后**注释 4/4 保留**(逐字节 diff 只动目标节) + 幂等 + **[input] 非末节反例** +
    --import 与游戏运行后不变 + 回退路径如实表现 + 既有 175 工具响应**只允许**'描述变更'与'场景①文件内容变更', 其余逐字节不变
  **D-2(必修, 讽刺但重要)**: 我们**自己的门里有一条恒真断言** —— mcp057_settings_publish_evidence.ps1 约 :364
    的 (.Count -eq 0 -or True) **永远为真 = 什么都没查**; -> 改成真断言 + **造一次失败演示**,
    并**普查 scripts/** 里所有恒真模式**(-or True / if (False) / 恒真比较)**逐条列出并修(或说明为何保留)
  D-1 重复 Check(:319/:332) -> 去重; D-5 mcp057_build_mono.cmd 硬编码 D:\Anaconda\Scripts\scons.exe -> 改为探测 + 可读报错;
  D-7 save_custom_section 用 remove-then-rename(非 POSIX 原子, 小窗口, 有 backup+rollback 兜底) -> **保留现状并如实登记**(我接受);
  D-3 4 个新 doctest **无红相位输出**(无法重建) -> 报告已如实声明并给独立进程外证据替代 -> **接受**,
    教训写入报告: **红相位输出必须当场保存**, 不得事后补造
  D-6 我任务书的报告文件名自相矛盾(标题 vs 正文) -> **我的错**, 已在 D114 记录该班次; 本次以 TASK-058 指定路径为准

派 TASK-059: D-4(行为+描述同批切换) + D-2(恒真断言普查) + D-1/D-5 顺手 + D-7/D-3 如实登记
之后: **游戏测试循环第 2 轮**(在 175 条工具 + 两个引擎补丁 + 按节发布之上重跑; 章程见 D112)
目标仍 active(hof-rs 一半按用户指令暂停; 用户本轮未解除)

## D116 — TASK-059 交付（**按节发布已切换上线**：注释不再丢）+ 恒真断言固化为守卫 + 三项裁决 + 派发纪律

docs(decisions): D116 TASK-059 交付(**按节发布已切换上线**: 注释不再丢) + 恒真断言固化为守卫 + 三项裁决 + 派发纪律

TASK-059(提交 d569b58d28 D-4 实现+契约 v1.18.0+测试 / 60584b317e D-2/D-1/D-5+新证据与门脚本 /
  739e0bb555 判定包原样保留 / cd7224274 D-8 / 4f99a4e37 报告(仅文档, 零编译字节); 二进制自报 cd7224274 == HEAD):
  **D-4 行为与描述同批切换(已上线)**: 切到 save_custom_section() 的三个工具 —— project_set_setting(节=key 首个 '/' 之前)、
    editor_add_input_action([input])、project_add_autoload([autoload]);
    **保留整文件重写**并如实说明: project_remove_autoload(**节写只替换值、永不删键** project_settings.h:226-227)、
    editor_reload_plugin(保存属编辑器自己的 ProjectSettingsEditor 定时器, 不在本模块)
    **四条回退路径在 tools/tool_helpers.h 命名并逐条实现**: (1)键不归任何节(无 '/' 或前导 '/');
    (2)目标文件不存在(save_custom_section 不创建文件 :1685-1689, 回退保持 TASK-059 之前'会创建'的行为);
    (3)引擎拒绝节写; (4)名字已在无头全局块(ConfigFile 的空节) -> 节写会留陈旧重复
  **证据**: 注释 4/4 保留 + 前缀/后缀逐字节相同 + 新键落进正确节 + **幂等** + **R1 场景 [input] 非末节正确** +
    引擎侧 InputMap.has_action=True + --import 与游戏运行后 sha 不变 + 回退路径如实表现(注释丢/引擎头写入/error_code=0);
    **契约 v1.18.0 仍 175 条, 名字与全部 175 个 inputSchema 逐字节不变**(只有 5 条描述移动);
    红相位**当场保存**(3 用例 3 失败 20 断言 -> 绿 3/3 89 断言; 模块 335/335)
  **D-2 恒真断言收口**(重要): 改成真检查(**真的 bind 那两个端口**, 不解析本地化 netstat 文本) +
    **三态失败演示**(基线 exit0 -> 造真残留(复制 cmd.exe 为假 godot 并让命令行命中 scratch 根) -> 未改动的脚本 exit1 +
    [FAIL] p2_no_scratch_engine_process_left :: swept 1 pid -> 清理 -> 还原 exit0) +
    **新增 scripts/check_tautologies.py(门⑥ 形状)**: 14 种声明拼写(9 PS + 5 py)、18/18 探针(14 插入必命中 + 4 近似必不命中)、
    --coverage 打印覆盖与未覆盖、一条钉住的引用 -> **让这一类无法静默复发**; 普查确认全库**仅此一处**
  D-1 去重(删 :319 保留 :332 **未丢 survivor 断言**); D-5 scons 探测(%SCONS% -> PATH -> 已知绝对路径, 打印来源,
    完全不可用时给可执行消息 + exit 3, 另有 --probe-only; **同一缺陷在 build_local.cmd 里也有, 一并修**) + 演示 9/9;
  D-7 remove-then-rename 非原子: **接受现状并登记**(有 backup+rollback); D-3 无红相位: **接受声明**并把
    '红相位输出必须当场保存、不得事后补造'写进报告
  **新发现并修掉 D-8**: 三处把生成器版本钉成字面量 1.17.0 -> 本批升 1.18.0 后**假红**(其中一处正是 R-B2 的失败演示 ->
    等于演示失效) -> 三处改为**运行时读** gen_renamed_contract.py; 另修一处自伤(--rev 默认 HEAD 会使'前'变成'后')
  门(22 步全 exit 0, 二进制自报 cd7224274 == HEAD): ③**335/335 (23714 断言)** ④**1761/1761 (447949 断言, 0 failed)**
    ⑥75/75 + 101/101 + --coverage; 恒真扫描 18/18; --check-completeness/--added **字节与 sha 一致**(33880d5c…);
    --generator-version PASS(1.18.0); 契约 pre/post PASS; R-B2 失败演示 PASS; D-5 演示 9/9;
    ①逐字 x5(默认 + 4 组)各 3/3(契约 175, union 152/72); section-switch 证据 **30/30**; patch2 23/23; D-2 演示三态
  回归电池 **全 exit 0**: accept_m1 x2 22/22(differing_lines=0)、mcp041/042/043、mcp010 29/29、mcp019、mcp027 60/60、
    mcp044 40/40、mcp045 15/15、mcp046 23/23、mcp052 53/53、mcp053 73/73、**66 个被跟踪证据文件已还原且 git diff --stat 为 0**;
    另跑 mcp054 53/53 与 mcp056 -Phase both 22/22; mcp057_gates.ps1 **未跑**(其步骤是 mcp059_gates.ps1 的真子集,
    每一步都已跑到) -> **声明而非冒充**
  端口: 9877 全程未起/未杀/未重启(前后无监听, 每次 9877 guard pass=True); 只用 9888/9889; 未 push;
    **模块外无引擎文件改动**(git diff 在 modules/mcp_server 之外为空); hof-rs 只读; DESIGN-DETAIL 未改

裁决(三项, 执行者上报):
  (a) **D-7 原子替换(remove-then-rename -> MoveFileEx(MOVEFILE_REPLACE_EXISTING)): 暂缓** —— 窗口极小且有 backup+rollback 兜底,
      收益低于风险(改 core/io 或 core/config 需重跑并发矩阵)
  (b) **project_remove_autoload 的注释丢失: 批准后续引擎补丁** —— 需要'枚举命名空间到 CustomMap + 删键'的节级能力
      (与本轮同一类: 文本保全), 排在游戏试测轮之后或并行
  (c) **editor_reload_plugin 的节级化: 暂缓** —— 其保存属 editor/settings/project_settingseditor.cpp 的定时器,
      改动面更大且节奏由编辑器决定
★ **派发纪律(本次真实教训)**: 第一次派 TASK-059 时, 子代理**把自己误判为'调度/决策'角色而拒绝执行**
  (声称其范围不得亲自写实现), 于是**零改动 + 零门**但交出一份**高质量判定包**(全部源码调研);
  我在重发时明写'**你就是实现会话, 有写权限, 现在就动手, 不要把活再委派出去**'后一次成功
  -> **今后每次派发实现任务必须显式声明该会话的实现权限**, 不得依赖默认理解;
  判定包也已按纪律**原样保留**为 REPORT-059-JUDGEMENT-PACK.md(并纠正其中两处猜测: 行 787 的工具是 editor_reload_plugin;
  API 读法逐行复核) —— '不做但把调研做透'也是可用的产出

进度: A/B/C/D 四档 + 两个引擎补丁(按节发布、C# 判定前置)已交付; 契约 175 条; 恒真断言已固化为守卫;
  下一步 = **游戏测试循环第 2 轮**(在 175 工具 + 按节发布 + 更诚实的 C# 判定之上重跑; 章程 D112),
  预期能暴露上一轮被掩盖的新问题(注释保全、C# 校验、批量工具、scope 收窄等新能力都值得被真实使用检验)
目标仍 active(hof-rs 一半按用户指令暂停)

## D117 — **修「观察者提前结束」**：缺陷定位为协议设计缺陷 + 裁决：把等待交给确定性 watcher，停止理由必须机器可读

docs(decisions): D117 **修「观察者提前结束」** —— 缺陷定位为协议设计缺陷 + 裁决: 把等待交给确定性 watcher, 停止理由必须机器可读

★ 用户报告: 第 2 轮试测中**观察者在开发尚未结束时就结束了**。我定位为**协议设计缺陷, 不是偶发**:
  1 **预算比工作短**: 我给观察者 25 分钟预算, 而完整开发必然更久 -> **到点必退(必然)**
  2 **停止条件交给智能体判断**: '轮询直到 marker 或预算到顶' **没有机器可核对的停止理由**;
     LLM 在长轮询里容易'觉得看够了'就收尾
  3 **等待没有交给确定性进程**: 真正该做等待与记录的是**脚本**, 不是智能体的意志力
  (另: 本轮 workflow 被 cancelled, 未产出任何试测产物 -> 无脏状态需要清理)

★ 裁决(三条, 写入 TASK-061 与 TASK-060 修订):
  (a) **把等待与记录交给确定性进程**: 新增 scripts/mcp_watch_run.ps1(纯 ASCII) ——
      阻塞等待 -Marker, 每 -IntervalSec(默认 30)检查 marker 与**每个追踪文件的新增行数/最后 seq**(按行道数, 不解析本地化文本),
      每次检查往 -OutDir\watch.log **追加**一行状态;
      **停止并给出机器可读的理由**: marker(exit 0) / 	imeout(exit 0 但 reason=timeout) / stale(StaleSec 内无新行 -> reason=stale);
      结束时打印并写文件: stop_reason / 耗时 / 最后 seq / 追踪总行数 / 轮询次数;
      **不得**依赖 netstat/本地化输出; **不得**杀任何进程; **绝不**碰 9877
  (b) **预算必须严格对齐**: 开发者 **45 分钟**; 观察者/watcher **75 分钟(严格大于开发者)** ->
      '开发者还没完而观察者已退'在**构造上不可能**; 观察者**禁止**用自己的 sleep 循环决定何时收工,
      必须**先跑一次阻塞调用**等 watcher 返回, 再基于**完整**记录分析; 产物与返回值**必须**含
      stop_reason/polls/last_seq/trace_lines/watch 日志路径; **reason != marker 时必须显式声明'观察在开发结束前停止'**
  (c) **开发者必须有心跳**: 每个里程碑往 %TEMP%/mcp-breakout/PROGRESS.md 追加一行 ->
      给 stale 判据**第二个信号**(追踪之外); 汇总者**必须核对 stop_reason**, 非 marker 时报告须**明确标注'本轮观察不完整'**

★ 证据要求(硬): 三种停止各演示一次(marker/timeout/stale, 各贴 watch.log 与结论行) +
  **反例演示**(用旧口径模拟'开发进行中' -> watcher 明确报 reason=timeout 而非静默结束) +
  -TimeoutSec 取值依据(观察者 > 开发者) + 改后**逐条自查** TASK-060 §C 不再有'由智能体自行决定结束'的措辞(贴前后对照)

★ 一般化(这条不止用于试测): **凡是'等待某个外部事件'的委派, 都不得把停止条件留给智能体的判断** ——
  必须(a)交给确定性进程; (b)给出机器可读的停止理由; (c)让预算严格覆盖被等待对象的预算。
  这条与'恒真断言'同族: **看起来在等的检查, 可能什么都没等** -> 已与 D116 的 check_tautologies.py 一起构成'门不能是摆设'的两条纪律

执行: TASK-061(实现 watcher + 改写 TASK-060 协议 + 三种停止演示 + 反例演示), 完成后**重发 TASK-060 第 2 轮**
目标仍 active(hof-rs 一半按用户指令暂停)

## D118 — TASK-061 交付（确定性 watcher + 协议修订）：观察者早退已从协议层修掉；重发第 2 轮试测

docs(decisions): D118 TASK-061 交付(确定性 watcher + 协议修订) —— 观察者早退已从协议层修掉; 重发第 2 轮试测

TASK-061(提交 A=ea345b51df 实现 / B=fcbeb90840 回填锚点; 基线 0a9fc1d466):
  新增 **scripts/mcp_watch_run.ps1**(15880B, sha 9e1d595c…, 纯 ASCII, parse-errors=0):
    阻塞等待; 每 -IntervalSec(默认30) 检查 marker 与**每个追踪文件的新增行数 + 最后 seq**(**按行道数**, 不解析本地化文本);
    每次检查往 -OutDir/watch.log **追加**一行; **机器可读 stop_reason**(优先级 marker>timeout>stale, 三者均 exit 0, usage 错 exit 2);
    结束打印并写 stop_reason/耗时/最后 seq/追踪总行数/轮询次数(watch-summary.json/.txt + 一行 WATCH_STOP);
    **不含 netstat、不杀进程、只读输入、只写 OutDir**; 另支持 -f 心跳(PROGRESS.md)
  **三种停止实测**: marker(10s/6 polls/exit0) / timeout(12s/7 polls/exit0) / stale(10s/6 polls/exit0); 证据生成器一条命令可复跑(EVIDENCE_OK scenarios=5)
  **反例演示(关键)**: S4 = marker 缺失且追踪持续增长(l=2->8, seq=2->8) + 预算耗尽 ->
    新 watcher 明确 **reason=timeout + observation_stopped_before_development_ended=1**;
    S5 = 旧协议脚本同状态 -> 末行仅 **BUDGET_REACHED**, stdout 1 字节, **全文无 stop_reason(静默结束)**, 改动逐行留档
  **取值依据**: 开发者 **2700s** < 观察者 **4500s**(余量 1800s, 最迟 4530s 返回);
    -StaleSec **300** = 第 1 轮 400 条调用中**最大运行内间隔 92.235s 的 3.2 倍**
  **TASK-060 协议改写**(+56/-15): §0 第 8 条(观测者预算严格大于开发者; 观察者**必须阻塞在 watcher 上**, **禁止**自己 sleep 轮询决定收工;
    产物与返回值必须含 stop_reason/polls/last_seq/trace_lines/watch 日志路径; reason != marker 必须显式声明'观察在开发结束前停止'),
    §0 第 9 条 + §B(开发者每里程碑追加 PROGRESS.md = stale 的第二信号),
    §C(完整命令行 + *.log 陷阱注记), §D(**逐项对账**: 缺字段或提前收尾 = 观察环节**不合格**)
    **机器自查**: 改后关键词命中全是否定/禁止句式, 不存在'由智能体自行决定结束'的许可措辞
  顺手修/报: 它自己的 **seek 缺陷**(增量读未定位偏移 -> last_seq 恒为首行值, 已修+前后证据);
    根 docs/ 是第 2 轮**未跟踪遗留**(无锚点); .gitignore *.log + .gitattributes eol=lf 会**静默让证据进不了提交**
    (已 git add -f 且证据改 LF, work==blob 33/33) —— 又一条'证据完整性'陷阱, 已登记
  纪律: git diff --stat -- tools tests **为空**(工作区与提交 A 均空); 契约零改动; 未起引擎; 9877 未碰; 未 push

★ 一般化(已入 D117): **凡'等待某外部事件'的委派, 停止条件不得留给智能体判断** -> 必须(a)交给确定性进程;
  (b)给出机器可读停止理由; (c)预算严格覆盖被等待对象。与 D116 的 check_tautologies.py 一起构成'**门/等待不能是摆设**'两条纪律

执行: **重发 TASK-060 第 2 轮**(打砖块 C#, 六条新能力专项压测), 协议已按上条修订
目标仍 active(hof-rs 一半按用户指令暂停)

## D119 — **第 2 轮产物其实存在但落错目录**（我的任务书用了相对路径）→ 改为回收+补汇总（TASK-062）

docs(decisions): D119 **第 2 轮产物其实存在但落错目录**(我的任务书用了相对路径) -> 改为回收+补汇总(TASK-062)

★ 重大发现(决策者核对): 引擎仓根的**未跟踪 docs/**(445 个文件)**不是遗留垃圾**, 而是
  **第 2 轮试测(TASK-060)的真实产物** —— 含 BREAKOUT-TEST-PLAN.md / BREAKOUT-DEV-LOG.md / BREAKOUT-OBSERVATIONS.md,
  以及按 **c1(注释保全)/c2(C# 真结论)/c3(批量父子)/c4(批量挂脚本)** 分组的完整取证与 probe-{cs2,cs3,gdscript,paths} 探针
  -> 即: **workflow 虽被取消(我没拿到结构化返回), 但开发者实际做了大量工作**(含打砖块工程与六条新能力取证)
  三条偏差: ①**产物落错目录**(引擎仓根 docs/ 而非 modules/mcp_server/docs/); ②**§D 汇总从未生成**(工作流被取消);
  ③**观察者确实提前结束**(c-obs 里只有零星快照 + 旧 watch.ps1 —— 正是用户报告的那个问题)
★ **根因是我的任务书的错**: TASK-060 写'产物一律写到 docs/reports/' —— **相对路径**, 而子代理 cwd 是**引擎仓根**
  -> 今后**所有任务书必须用绝对路径**(或明确写 modules/mcp_server/docs/...); 这条并入'确切的规格'纪律
  (同类第 4 次: D-1 前提错 / D-2 scale=1 措辞 / O-9 '保留精确匹配' / 本次相对路径)

裁决: **不重跑**(避免重复浪费与证据污染), 改为 **TASK-062 回收 + 补汇总**:
  ①把根 docs/reports/** **整体搬进** modules/mcp_server/docs/reports/**(含 evidence/task060)**, 修正被搬文件内的路径引用,
    删除空根 docs/, 给'搬前/搬后文件计数 + 内容 sha256 对照'(证明没丢内容);
  ②在三份产物头部**诚实标注**: workflow 被取消=中断快照; 观察者用**旧协议**=**观察在开发结束前停止(覆盖不完整)**;
    不得当完整记录用;
  ③**补做 §D 汇总** BREAKOUT-FINDINGS.md, **以 evidence/task060/** 原文为准(不凭报告叙述)**专答六条新能力判据**
    (注释保全 / C# 真结论 invalid+编译器原文+ok+not_compiled / 批量父子 / 批量挂脚本含 keep_existing /
    scope 收窄 / 捕获 changed:false) 逐条给 通过|不通过|不可构造 + 证据路径与 sha256;
    四张表(异常/缺失/可合并/可优化) + 疑似缺陷单列 + **明确写清哪些结论受'观察不完整'影响**
  ④本批只动 docs/** 与(必要时)scripts/**; tools/tests diff 必须为空; 契约不动; .gitignore *.log 要 git add -f

★ 教训(已入 D117/D119 两条纪律): ①等待外部事件的委派不得把停止条件留给智能体判断(D117);
  ②**委派必须给绝对路径**(D119) —— 否则产物会落在错误的仓/目录, 而且**取消的工作流仍可能在后台留下产物**,
  所以'取消'之后**必须核对工作树**(本次正是靠 git status 才发现 445 个文件)

目标仍 active(hof-rs 一半按用户指令暂停)

## D120 — 第 2 轮回收+汇总完成（六判据：②③通过，①④不通过，⑤⑥未构造）+ 抓到产品缺陷（含**端点静默失能**）+ 观察者问题已量化

docs(decisions): D120 第 2 轮回收+汇总完成(六判据: ②③通过, ①④不通过, ⑤⑥未构造) + 抓到产品缺陷(含**端点静默失能**) + 观察者问题已量化

TASK-062(提交 f6f2ff3376 + 文档收尾; 只动 modules/mcp_server/docs/** 537 文件):
  回收: 根 docs/reports/** 445 文件/658190 B 搬入模块目录, **搬前搬后 sha256 逐字节相同(Compare-Object 0 差异)**,
    空根 docs/ 已删; 路径引用修正 6 文件(每处恰 +19 字节 = modules/mcp_server/, JSON 重新校验, 一次 JSON 转义写坏当场修复并记录);
    三份产物头部**前插状态声明**(原正文一字未改);
    **额外只读回收 78 个从未入库的原始追踪/日志/脚本**(含 §B 承诺却没入库的 run.log) -> '以原文为准'的前提
  **六条新能力判据**(以 evidence/task060/** 原文为准, 每条带证据路径+sha256):
    ② **C# 真结论 = 通过**: ok(c2_v5 sha b18ac829…) / invalid(c2_v2 sha c088002b…, error_text 含 **Broken.cs(5,5) CS1519** 与 (5,23) CS1002) /
      **not_compiled(c2_v1 与 c2_v3 响应 sha 同为 a631ecb2…, valid=null)** -> '改过未构建'与'编译失败'**被区分**;
      同一响应并存(c2_v4 count=2: CS0103 的 invalid + valid=null 的 not_compiled); 单数拒绝明说'not compiled != does not compile'
    ③ **批量父子 = 通过**: 单次调用 count=26(c3_a1 sha c841696c…), parent_source scene=5/batch=21/missing=0,
      **另一工具读回 18/18 砖**(c3_a2 sha 8de6cff3…), 前向引用 -32001 + **整批回滚**(c3_d1), 同批重名 -32602 + 回滚(c3_e1),
      默认 false 回归 -32001(c3_f1), errors[].index 可定位
    ① 注释保全 = **不通过**: P1a/b/d/e/g 通过(**注释 4/4 逐字保留**, 三探针键均落 [input] 内, S2==S1,
      对照组 project_remove_autoload 丢注释并出现引擎 7 行头), **但** P1c 判据**自相矛盾**(要求 [input] 之外逐字节不变,
      同时方案又要求写 physics/...(必然新增 [physics] 46B)) = **判据无解**; **P1f 断言与其引用证据相反**
      (称 InputMap 有 mcp060_probe_action, 而其引用的 c1_a6 响应 sha 1a5da0e4… 里没有该键)
    ④ 批量挂脚本 = **不通过**: P4a/P4c/P4e/P4g/P4h 通过(count=18 attached=18; skipped=18 每项带 reason 与 previous_script_path;
      rolled_back:true 且 Ball.cs 出现 0 次; 9889 上 editor_* 0 条且 -32601), **但 P4b 不可归因** ——
      main.tscn.before_attach 与 after_attach **同 sha a423d468…**(before 已含 18 行 script = ExtResource) -> **快照时序错误**;
      P4d 退化(5 份快照同 sha); P4f 未构造
    ⑤ scope 收窄 = **未构造**: **对该工具调用数 0**; 追踪里 6 次命中**全在 SignalRegistry.cs 的源码注释里**(正是我们禁止的文本包含式判断)
    ⑥ 捕获 changed:false = **未构造**: **307/307 捕获行 status=unavailable**(全程 headless, 无窗口化追踪, 游戏侧 --mcp-capture=off);
      §A 明令不得用 headless 边界顶替 ⑥ 的通过
  四张表: 异常 7 / 缺失工具 5 / 可合并 5 / 可优化 6 + **疑似缺陷 10 条**(分[产品]与[试测产物/流程]) + 对 §A/§B/§C 的纠错 10 条
  ★ **产品侧真缺陷(下一批要修)**:
    (i) **游戏端点静默失能**(major): bind failed on 127.0.0.1:9889 (error=22) -> get_port()=0(MCP server disabled),
        **响应里没有任何迹象** -> 又是'报成功但什么都没发生'家族, 且发生在**端点本身**
    (ii) **node_path 参数面不一致**(minor-major): editor_set_node_property/editor_get_node_properties 用 **path**,
        editor_set_node_script_batch 用 **node_paths**; 三者都要求**场景根相对**路径但**描述未声明**、-32001 **不指路**
        -> 第 1 轮 DEV-LOG 报的那条'缺陷'实为**误报**, 根因即此
    (iii) editor_set_node_property_batch 无法按路径列表**批量写不同值**(updates -> -32602; 几何只能 20 次单点写)
    (iv) editor_execute_gdscript 的 parse 错误**不带行列**(26 次调用, 7 对失败->成功)
  ★ 试测产物/流程缺陷: 证据文件**同名复用被覆盖**(run.log 里 c2_b0_build 复用 4 次; 磁盘可比的 200 条中 163 相符 **37 不符**);
    P1c 判据无解; P4d 退化对照
  ★ 观察者问题**已量化**(用户报告的那条): 观察窗口 05:34:40-06:00:25 由**自建 watchdog**以 **BUDGET_REACHED** 收口
    (无 watch-summary.json, watch.log sha a584bc61…), 而 §B 首次工具调用在 06:26:28、开发最后证据 08:01:15 ->
    **观察在开发开始调用前 26 分钟结束、距开发结束约 2 小时**; §C 的四类计数(0/0/0/2)全是**时间错位产物**,
    '单工具占比 100%'等分母=1 无统计意义 -> 汇总者**逐条列清**: 受影响 / 不受影响 / 仍空白 三类
    (不受影响: ①②③④ 判据结论与四张表; 仍空白: ⑤⑥ 之外还有**游戏侧活链**(输入->位置回读/砖块消失/计分)
     与'打砖块工程本身是否真能跑')
  untouched: git diff --stat -- tools tests = 空(提交前后各一次); 更强口径 97144b5afb..HEAD 中
    tools/tests/scripts/契约/modules/mono 零改动, 537 个入库文件全在 modules/mcp_server/docs/**;
    8 个被 .gitignore 挡住的 *.log 已 git add -f; 未 push; 未启动任何 Godot 进程

裁决(下一批 = TASK-063):
  (a) 修 (i) 端点静默失能:**bind 失败必须可见** —— 至少启动日志 ERROR + 一个可查询的状态/工具字段;
      并查 error=22(EINVAL) 的成因(可能与 headless/监听参数有关)并给最小复现; **不得**静默 get_port()=0
  (b) 修 (ii) 参数面一致性: **统一或至少描述声明 + -32001 指路**(走 override 描述 + 错误建议; 是否改参数名需我另裁)
  (c) (iii)(iv) 排入同一批(批量写不同值 = 新参数或新工具; parse 错误补行列)
  (d) **重测 ⑤/⑥**(必须): 窗口化进程 + 真实调用 editor_list_signal_connections{scope:user} + 至少一次 changed:false;
      **并用 TASK-061 的 watcher 保证观察覆盖完整**(stop_reason 必须是 marker)
  (e) 试测流程修复: 证据文件**按 id 唯一命名**(禁同名复用) + 快照时序(**先写 before 再写 after** 且断言 sha 不同)
目标仍 active(hof-rs 一半按用户指令暂停)

## D121 — TASK-063 交付（4 条产品缺陷全修，契约 175→176）+ 新工具不是后门 + 下一轮重测计划

docs(decisions): D121 TASK-063 交付(4 条产品缺陷全修, 契约 175->176) + 新工具不是后门 + 下一轮重测计划

TASK-063(提交 92a260b682 实现 / 4e31df769d + c589eae24e 报告与证据; 二进制 --version = 92a260b68 == 实现提交):
  **(a) 端点静默失能(修)**: **根因 = error=22 实为 ERR_ALREADY_IN_USE** ——
    SocketServer::_listen 把**所有** bind 失败压成同一个码(core/io/socket_server.cpp:47-52), 不是 EINVAL;
    修: **ERROR 级日志**(请求端口 / 诊断原因 / **端点已禁用**) + **进程内可查状态**(3 态枚举 + 5 访问器 +
    debug_endpoint_state) + **端到端可机器读的 endpoint_disabled 追踪事件**; 空闲端口实测绑上且 tools/list=72;
    53/53 活检查;**未改引擎文件**(候选引擎改动已上报我)
  **(b) 参数面(修, 契约条数不变)**: 参数名**保留**(改名会破坏既有调用方与证据);
    2 条 DESCRIPTION_OVERRIDES + 1 条 ADDED_TOOLS 描述**共用同一条规则句**(声明'场景根相对 + 单数 vs 复数'), 不会漂移;
    -32001 与 -32602 的 data.suggestion 指路(显式工具表驱动的 MCPTools::node_path_guidance(); **res:// 类工具不收场景根建议**)
  **(c) 新增工具 editor_set_node_property_updates**(ADDED_TOOLS, 契约 **175 -> 176 = 171 + 5**):
    一次调用给 4 节点写 **4 个不同值**; 越界那条 -32602 **其余成功**; **逐条读回 old/new/changed**;
    stop_on_error=false 逐条报告 / true 首错即停且**真实回滚**;
    ★ **写入全程走 MCPTools::write_node_property** -> **同一道 ValueSlot 闸门 + 同一道属性存在性拒绝**
      => **新工具不是绕过 §20/§22 收窄闸门的后门**(这条是我在任务书里点名的硬要求, 已达成)
  **(d) parse 行列(部分修)**: **行可得**(临时引擎错误处理器 + 生成源的 body offset 映射回**调用方自己的行序**);
    **列不可得**(调用点丢弃 ParserError.start_column) -> **如实发布 data.parse_error_column = null 且键存在**,
    边界声明 + 实测对照; 两个 execute 工具共用
  线上: 契约 **176**; **9888 = 153 / 9889 = 72**; 9889 **不含** editor_set_node_property_updates 且对它回 -32601
  门: ①3/3; ②53/53; ③**342/342**; ④**1768/1768 (448171 断言)**; ⑤22/22 x2 清单一致;
    ⑥三段 exit0 + 101/101; --check-completeness/--added/--generator-version(1.19.0) exit0; 构建从 cmd 串行
  偏差(如实上报): **4 个他任务的证据脚本把契约条数钉成旧值(152/175)** -> 红; 因本会话无 HEAD 锚点的 mono 二进制未重跑;
    已逐条点名并给最小修法 -> 下一批修
  纪律: 9877 未占用/杀/重启; 未 push; **未改引擎文件**; 102 文件证据树 SHA256SUMS 复核 exit0

裁决: ①(d) 的列缺失**接受为已声明边界**(引擎调用点丢弃, 要让列可得须改引擎 -> 价值低, 暂不做);
  ②(b) 的**参数名不改**为最终口径(改名属破坏性变更, 收益低于成本); 若将来要统一, 必须**新增别名并保留旧名**;
  ③下一批(**TASK-064**): (i)修那 4 个钉旧契约条数的证据脚本(**只更新期望值, 不得放松断言**);
    (ii)**重测第 2 轮未构造的 ⑤⑥**(窗口化进程 + **真实调用** editor_list_signal_connections{scope:user} + 至少一次 changed:false),
    并且**必须用 TASK-061 的 watcher 保证 stop_reason=marker**(否则观察环节不合格);
    (iii)补测**游戏侧活链**(第 2 轮仍空白: 输入->位置回读 / 砖块消失 / 计分变化);
    (iv)试测流程修复: 证据文件**按 id 唯一命名**(禁同名复用) + 快照**先 before 后 after 且断言 sha 不同**

进度: Godot 侧 176 条工具; 两条引擎补丁(按节发布 / C# 判定) + 4 条第 2 轮产品缺陷全部交付;
  下一轮是**第 3 轮试测**(打砖块或新的小游戏), 必须把 ⑤⑥ 与游戏侧活链**真正跑到**
目标仍 active(hof-rs 一半按用户指令暂停)

## D122 — TASK-064 交付（6 处陈旧期望值改为派生且未放松断言 + 取证唯一命名/快照时序变成无法表达的缺陷）

docs(decisions): D122 TASK-064 交付(6 处陈旧期望值改为派生且未放松断言 + 取证唯一命名/快照时序变成无法表达的缺陷)

TASK-064: ①**6 处陈旧契约条数期望**(我点名的 4 个 + 它自己多查出的 mcp053_added:327 四名字面量 + mcp054:307 added_count==4)
  改为**从 '171 ported + _meta.added_count' 与第六份清单派生**; **171 仍是被检查的字面量**;
  **没有任何断言被放松**(逐条 diff §1.3/§3): 派生读独立声明源 + _meta.added_tools 与清单**逐元素双向相等** +
  线上 9888/9889 仍单独要求等于派生视图 + mcp059 的 after 只能按声明的 added_tools **有序尾**增长且 no-growth 轮不许移动;
  **反向探针 13/13**: 同一输入上**每个旧表达式为假、每个新表达式为真** -> 给出精确的前后退出码对照
  两处**故意不改**且论证充分: mcp063:374 是 TASK-063 自己的 175->176 **过渡证据**(176 是其主题, 不可变成移动派生);
  mcp052_contract_diff.py 是**冻结的一次性对照**(输入对已不存在)
  给后续批次的提醒: 派生检查对'追加'永远绿, 但对**改名/删除/重排/丢条目**会**正确地变红**
 ②**取证缺陷变成'无法表达'**(mcp_evidence_guard.ps1 +351 行): <leaf>__<id>__<seq>__<sha8> 唯一命名;
  **一个路径只允许一种内容**(同名不同 sha -> 抛错并报出两个摘要; 运行内/盘上预存/事后全树审计三处);
  同内容重复**标记 SameContentSeen 而非静默重写**; Write-McpEvidenceSnapshotPair 固定 before->between->after
  **并断言两 sha 不同**(除非显式 -ExpectedIdentical -Reason, 且声明相同却不能移动);
  探针 **20 例/0 失败**, 含 **6 个刻意反例**(旧固定名写出器/同路径不同 sha/冻结对/未声明'预期相同'); 连续两跑自清理后 exit 0
  纪律: git diff --stat -- tools tests **为空**(工作区与 HEAD~1..HEAD 均空); 契约/清单/映射/DESIGN-DETAIL 未动;
    **未起引擎**(scons 从未跑); 9877 未碰; 未 push; 全部 .ps1/.py 非 ASCII 字节 = 0
  **声明覆盖缺口(诚实)**: 三个引擎驱动脚本 mcp052/mcp053/mcp054 **未能端到端重跑** —— 本工作树 mono 二进制锚在 cd7224274 != HEAD,
    而它**刻意没有重建 mono**; 覆盖率由反向探针替代, **不冒充完整回归**

裁决: ①**重建 mono 并复跑那三个脚本**并入下一批(与第 3 轮试测同一批做, 既补这个缺口又给试测提供 HEAD 锚定的 mono 二进制);
  ②TASK-064 的两处'故意不改'**批准**(过渡证据与冻结对照都不该变成移动派生);
  ③'派生会让改名/删除/重排变红'这条**写成规范提醒**(已由它给出, 我落进下一批任务书)
下一批 = **TASK-065 第 3 轮试测**(在 176 条工具 + 两条引擎补丁 + 4 条缺陷修复之上):
  (i)**先重建 mono 并复跑 mcp052/053/054**(补 TASK-064 的覆盖缺口)
  (ii)**把第 2 轮未构造的 ⑤⑥ 真正跑到**: ⑤ 真实调用 editor_list_signal_connections{scope:'user'} + 相邻 c5 取证;
    ⑥ **窗口化**进程下至少一次 changed:false(headless 永远是 unavailable, 不得顶替)
  (iii)**补测游戏侧活链**(第 2 轮仍空白): 输入->位置回读 / 砖块消失 / 计分变化
  (iv)**观察必须用 TASK-061 的 watcher**, stop_reason 必须是 marker, 否则该轮观察环节**判不合格**
  (v)试测脚本必须用 TASK-064 的 mcp_evidence_guard.ps1(唯一命名 + 快照时序断言)
目标仍 active(hof-rs 一半按用户指令暂停)

## D123 — TASK-065 交付：**mono 锚点缺口关闭** + **缺口专项第 3 轮：⑤⑥ 与游戏侧活链全部构造成功**（stop_reason=marker）

docs(decisions): D123 TASK-065 交付 —— **mono 锚点缺口关闭** + **缺口专项第 3 轮: ⑤⑥ 与游戏侧活链全部构造成功**(stop_reason=marker)

TASK-065A(提交 6b46ff363e 报告+197 证据文件 / 3daa41591a / 08691fd21e; 未 push; 9877 全程无监听):
  **串行重建两个引擎到 HEAD 770872998**(mono 与 plain **都必须**, 因 engines_match_head 要求二者同时含 HEAD 短 sha):
    mono=4.8.dev.mono.custom_build.770872998 (10:05:05, exit0, 1:42.06); plain=4.8.dev.custom_build.770872998 (10:07:03, exit0, 1:38.76);
    修复前 mono=cd7224274 / plain=92a260b68
  **三个脚本复跑到 exit 0**: mcp052 **53/53**(log sha 931d5db2…) / mcp053 **73/73**(c6f7bb5a…) / mcp054 **53/53**(882cf084…);
    修复前的红有**两条独立原因**且逐条归因: (A)陈旧字面期望 152/175/4(TASK-064 ea05a19d4b 修, 本批重跑 mcp064 反例探针 13/13 佐证);
    (B)**陈旧二进制锚点**(本批修, 锚点谓词 PRE=False -> POST=True); 受版本控制证据就地更新 40 文件, 最强单点 task054/green/status.json "tools":152->153
  门全 exit0: ①契约 5 步(实况并集 153/72, 契约 176, 逐字 True); ③**342/342 (23924 断言)**; ④**1768/1768 (448171, 与 REPORT-063 逐字一致, 0 failed)**;
    ⑤accept_m1 x2 22/22 清单 Compare-Object 为空; ⑥三段式 75==75 + 17 拼写 + 101/101 且字节还原;
    --check-completeness("171 + 5 = 66 + 105 + 5" PASS)/--added(双向 missing=0 foreign=0)/--generator-version(1.19.0) PASS;
    tools/tests/契约空 diff, 契约 sha d4e53b43… 未变
TASK-065B(**缺口专项第 3 轮, 71/71 判据 PASS, exit0; 证据 127 文件 collisions=0; 未改实现; 契约 sha 未变; 9877 无监听; 端口已释放; 未 push**):
  **⑤ scope 收窄(第 2 轮'未构造') -> 构造成功**: 编辑器端点真实调用 editor_list_signal_connections **20 次**;
    默认 **47 条/9756 B**、scope:"user" **2 条/371 B**、scope:"internal" **45 条/9565 B**;
    user 的 method **只含** _on_timer_timeout/_on_timer_two_timeout(**无 "::"**), internal 45 条**全含 "::"**;
    **user 并 internal = default 且 user 交 internal = 空**(default-user=45=internal, default-internal=2=那两条 fixture 连接) —— **集合代数逐项核对**;
    signal_name x scope 组合正确(timeout: default 2 = user 2 并 internal 0); 显式 scope:"all" 结果体 sha256 与默认**逐字节相同**(249ea832…);
    scope:"bogus" -> -32602 且**列出枚举**
  **⑥ 窗口化 changed:false(第 2 轮'未构造') -> 构造成功**: **窗口化进程**(无 --headless, --mcp-capture=every_call viewport=2d scale=2, **status=done 而非 unavailable**);
    真实变化 editor_set_node_property(Box.position->200,120) -> **changed:true** 10232/1334144 px ratio 0.00766933704307781 frames_waited=1;
    **同参同值重放**(参数 sha 257fbd0b…, 工具仍报成功 old/new 都=200,120) -> **changed:false** 0 px ratio 0.0; 只读重放同样 false;
    **三路一致**: 日志 10232/1334144 = 工具 editor_analyze_screenshot_diff 10232/1334144(响应 sha 3995d85a…) = **PIL 独立复算** 10232/1334144(all_three_routes_agree=true);
    幂等对三路都 0/1334144 且 identical=true; 证据守卫快照 main.tscn before 3cad0f2d… -> after 36af27ad…(不同, between=改属性+editor_save_scene)
  **游戏侧活链(第 2 轮仍空白) -> 全部构造**: 9889/headless/15 次调用 **0 错误**:
    ①输入注入 paddle_right -> **另一工具**读回 **24 帧 x=321->482**(24 个不同值, **逐帧单调 +7.0 px/帧, 非瞬移**), 另一读回 300->496 moves=28;
      球 launch 后 18 帧 y=312->244(每帧 -4 px); ②running_game_find_nodes_by_script{brick.gd} **3->2**(Brick0 从解析后的场景树消失);
    ③HUD/ScoreLabel.text **"Score: 0" -> "Score: 10"** + 进程内断言 Main.score>0 通过(actual=10)
  ★ **stop_reason = marker** —— **TASK-061 的 watcher 生效, 观察完整覆盖整轮运行**(用户报告的'观察者提前结束'现已有机械闸门)
  仍空白 8 条(如实列出, 未含糊): B1 游戏端窗口化捕获族 / B2 --mcp-capture=on_error 与 diff_image / B3 scale 1/4 /
    B4 scope x node_path 组合 / B5 连接来源(场景文件 [connection] vs 运行期 connect())区分 /
    B6 editor_analyze_screenshot_diff 的拒绝路径 / **B7 C# 工程上的同一套活链**(第 2 轮 C# 工程缺脚本/碰撞/分数 Label, 见报告 F1) /
    B8 多进程多会话的 scope 稳定性

★ 里程碑意义: 第 2 轮的三处缺口(⑤⑥ 与游戏侧活链)**这一轮全部变成有证据的事实** ——
  scope 收窄的集合代数(并=默认, 交=空)是**最强形式**的收窄证明; 捕获的 changed:false 有**三路一致**的像素账;
  游戏侧活链证明**输入->世界状态->UI** 三段都能被工具读到。**工具在真实游戏开发上的可用性已被闭环验证**

裁决/下一步: ①8 条空白中 **B7(C# 工程活链)** 优先(第 2 轮的 C# 工程本身不完整, 需先补齐工程);
  ②B6(diff 工具拒绝路径)与 B1/B2/B3 属取证面, 排其后; ③B4/B5/B8 属组合面, 可并入下一轮;
  ④hof-rs 一半仍按用户指令暂停 -> 目标**保持 active**, 不标完成

## D124 — TASK-066 交付：**C# 打砖块补齐 + B7 收口 + 前 8 条空白 8/8 全收**（六判据全通过，stop_reason=marker）+ 抓到两条新缺陷

docs(decisions): D124 TASK-066 交付 —— **C# 打砖块补齐 + B7 收口 + 前 8 条空白 8/8 全收**(六判据全通过, stop_reason=marker) + 抓到两条新缺陷

TASK-066A(开发者; 证据 40dad5a6df / 报告 a27d7d7ba1; 二进制 7708729982; **未改模块实现**; 9877 无监听):
  C# 打砖块**补成完整可跑**(16 节点 / 5 个 _Process 驱动的 C# 脚本 / 4 个 [input] 动作 / project_build_csharp exit 0),
    全部**经 9888/9889 MCP 端点**建成; 活链在**窗口化**游戏进程跑通; **146/146 断言**(session1 59/session2 41/session3 46);
    MCP 请求 **99 次**(tools/call 97 + tools/list 2); **回退 9 条**
  **六条新能力判据全部通过**:
    ①注释保全: 分段写 **4/4 注释逐字存活**(E0->E1), 对照组 project_remove_autoload 整文件写**抹光 4/4**
    ②C# 真结论: ok(valid=true) / 不构建->**not_compiled**(-32000) / 构建失败->**invalid + error CS1040,CS1002 带(行,列)**,
      且**同响应内 invalid + not_compiled 并存**
    ③批量父子: 一次 editor_add_nodes_batch(resolve_within_batch) 建 16 节点(scene=8/batch=8/missing=0)
    ④批量挂脚本: 一次把 Brick.cs 挂到 3 砖(count=3 errors=[] previous_script_path 全空), .tscn 落盘可回读
    ⑤scope: all=207 / **user=1** / internal=206, 交集 0, 并集=default, 每 scope 3 次响应体**逐字节稳定**
    ⑥changed: **窗口化**编辑器 changed:true 2660px / 同参重放 changed:false; 游戏进程同样 true 4544px / false;
      两路与工具 diff **逐位一致**
  **7 条新发现**, 最重两条: (i) **project_list_scripts 对 .cs 失明**(C# 工程的脚本列不出来; **一条调用即可复现**);
    (ii) **窗口化编辑器启动会重写 project.godot 并丢掉注释**(与已知'ProjectSettingsEditor 定时器保存'同源 ->
    若确属**引擎自身**行为, 则**启动时**就会吃掉用户注释, 比工具误用更严重 -> 需确认后考虑**第三个引擎补丁**)
TASK-066B(验证者; 88/88 运行判据 + 8/8 收尾判据, **B066 RESULT checks_passed=88 checks_failed=0 exit0**;
  证据树 358 文件 collisions=0; **未改实现/契约**, 契约 sha d4e53b43… 前后同值; 9877 无监听; 端口已释放; 未 push; 未跑 scons):
  **活链(C# 工程, mono 窗口化游戏进程 9889, 5 个 .cs)**:
    ①paddle_right -> **另一工具**读回挡板 **24 帧 24 个不同 x, 严格单调 313.98->475.03(+7.0 px/帧 = 420/60)**,
      Paddle.position.x 300.0->487.98, Moves=1325, LastDir=right, 进程内断言 Moves gt 0 actual=1434 passed;
      球 18 帧 18 个不同 y 严格递减 311.38->237.74(每帧 -4.3 px = 260/60)
    ②running_game_find_nodes_by_script{res://scripts/Brick.cs} **3->2**(存活 Brick1,Brick2; 解析后整棵树 Brick0 前 true 后 false)
    ③HUD/ScoreLabel.properties.text **"Score: 0" -> "Score: 10"**, Main{Score=10,BricksHit=1,State=playing,Lives=3},
      进程内断言 Main.Score gt 0 actual=10 passed; 三步对的两步响应 sha256 **两两不同**
  **⑤(4 个独立进程)**: 默认 207/44751 B, user **1 条/275 B**, internal **206/44658 B**;
    **user 并 internal = default(双向差集皆 0)**、**user 交 internal = 空(0)**、default-user=206=internal、
    default-internal=1(正是场景文件第 89 行那条 ProbeTimer|timeout|.|OnTimerTimeout);
    同 scope 三次逐字节相同(all f21a9805/user b96f6af2/internal 95487469); 显式 all == 默认;
    user 的 method 全不含 "::", internal 206/206 全含 "::"; bogus -> -32602 并列全三种口径;
    B4: node_path ProbeTimer x scope -> 11/1/10 仍划分; **B8: 4 进程 internal 全 206/user 全 1/default 全 207**(与 A 逐项相同)
  **⑥(窗口化, status=done, viewport=2d/game, scale=2)**: 编辑器只读重放两次 false/0px; 真实变化
    editor_set_node_property{WallTop.position -> (0,60)} -> changed:true 2660/1334144 ratio 0.00199378777703156;
    同参同值(arguments_sha256 两次相同)重放 -> 工具仍报成功但 **changed:false/0px**, before==after sha 37062f00;
    **三路一致**: trace 2660/1334144 == editor_analyze_screenshot_diff 2660/1334144 == **PIL 独立复算** 2660/1334144
    (all_three_routes_agree=true, 4 对, 含游戏侧 4224/186624); 游戏侧同样 true 4224/186624 / 重放 false 0px;
    证据守卫快照 p1_main_tscn: before d33b8931…(2890 B) -> between(set+save) -> after ec0b9826…(2910 B), **两 sha 断言不同**
  **前 8 条空白 8/8 全部收口**: B1 游戏端窗口化捕获族(screenshot 1152x648 PNG 8107 B, save_path,
    capture_frames 半分辨率 3x576x324 engine frames 592/602/612 间隔 10, 全分辨率 2x1152x648, 移动可见节点后帧 sha 3aaa17cb->8f0a0546);
    B2 on_error 成功调用 0 条捕获行/失败调用 1 条且全会话捕获行数=失败数, diff_image=on 的 diff.path/bytes/sha256 齐备 118122 B;
    B3 scale1 2978x1793=5339554, scale2 1489x896=1334144=逐轴 floor/2, scale4 744x448=333312=逐轴 floor/4;
    B4 scope x node_path 11/1/10 仍划分; B5 运行期 connect() 的 ProbeTimer|timeout|Ball|queue_free 进 user(1->2)、
      **不在 .tscn 里**, 但两种来源键集相同 -> **工具不暴露 provenance**(如实的边界);
    B6 四拒绝路径 -32001/-32602/-32602/-32602; B7 C# 活链主目标全通过; B8 四进程 206/1/207 稳定
  对 A 的纠错 2 条(waited_seconds 系回显名; dll 19968 B 已过期应为 20992 B), 独立确认其 3 条主张;
  **如实声明 4 条不可构造**(含'on_error 与 diff_image 同时生效'为何构造不出的完整推理 + 已分别构造两个开关)
  ★ **stop_reason = marker**(连续第二轮观察完整覆盖)

裁决/下一步(下一批 = TASK-067):
  (a) **project_list_scripts 对 .cs 失明**: 先**独立复核**(一条调用即可), 确认后修(应能列出 C# 脚本; 若属引擎 API 边界则如实声明);
  (b) **窗口化编辑器启动重写 project.godot 丢注释**: **优先确认根因**(是否引擎自身的 ProjectSettingsEditor 定时器保存);
      若确认 -> **第三个引擎补丁**: 让编辑器自己的保存也走**按节发布**(与补丁 2 同一能力), 使**启动/保存都不再吃注释**;
      必要时在报告里区分'工具写入'与'编辑器自身写入'两条路径
  (c) 其余 6 条发现(见 REPORT-066)按证据强度排序, 择要修
  (d) B5 的 provenance 边界(两种来源键集相同)记为**已声明能力边界**, 不修(除非有低成本办法)
目标仍 active(hof-rs 一半按用户指令暂停)

## D125 — TASK-067 交付：**.cs 失明已修** + **窗口化编辑器启动吃注释的根因定位到行** + **第三个引擎补丁（save_preserving_text）**

docs(decisions): D125 TASK-067 交付 —— **.cs 失明已修** + **窗口化编辑器启动吃注释的根因定位到行** + **第三个引擎补丁(save_preserving_text)**

TASK-067(提交 2f85141a74 实现 / 82c8313a5e 报告+证据 / adf87b7090 / eff591a140; 未 push; 9877 全程无监听; 收尾无残留进程):
 ① **project_list_scripts 对 .cs 失明 -> 已修**(**独立复核成立**): 改动前二进制 count=2, 而同进程
    project_read_script{res://scripts/Main.cs} 返回 size=2389、fs_tree 17 条含 Main.cs、磁盘 res://scripts 有 6 个 .cs;
    修法: **扩展名集合改由 ScriptServer 派生**(GDScript->gd, **mono 编译进来时**->cs; script_language.cpp:239/:221/:227,
    gdscript.cpp:2215-2217, register_types.cpp:57 -> csharp_script.cpp:98) + 保留 .gdshader(**它是 Shader 不是 ScriptLanguage**);
    **walk 一字未改**; 改动后 **count=10**(6 .cs + 2 .gd + 2 生成 .cs), 10/10 都是路径字符串、**两种语言形状一致**;
    契约 **176 / sha d4e53b43… 前后同值**, 未加 override
    **如实声明副作用**: walk 仍下探 .godot, 故真实 Mono 工程里 2 个生成 .cs(res://.godot/mono/temp/obj/Debug/)也会被列出;
    收窄 walk 会撞到钉住的 .hiddendir/secret.gd 断言 -> **需我另裁**
 ② **窗口化编辑器启动吃注释 -> 根因定位到行**: editor/editor_node.cpp:**1062-1072** 的 **!cmdline_mode** 分支在 **:1071**
    调 ProjectSettings::save()(core/config/project_settings.cpp:1086 -> _save_settings_text :1162 整文件重写);
    而 **cmdline_mode 由 editor_node.cpp:8479 从 headless 得出** -> **这就是 '--import/--headless 从不丢注释、
    窗口化启动必丢' 的全部原因**; 最小复现(改动前 mono 二进制): 541 B / 4 条探针注释 / sha cca8e45d… ->
    --import **逐字节不变** -> 窗口化启动 sha cd4ebe43…, **4 条探针注释全丢**(只剩引擎 7 行头注释);
    **工具写入路径**(editor_add_input_action/project_set_setting, TASK-059 按节发布)**一条注释行都没动** -> 两条路径分开陈述
 ③ **引擎第三个补丁**: 新增 **ProjectSettings::save_preserving_text()** + public static publish_settings_sections_text();
    把三段**抽出共享**(save_custom 的'收集设置'半 = _collect_settings_for_save; save_custom_section 的读半/写半 =
    _read_settings_text_file / _publish_settings_text_file), **只切换 editor_node.cpp:1071 一个调用点**;
    save_preserving_text 发布的**正是 save() 会发布的那一组**(逐节走补丁 2 的 update_settings_section_text),
    **其余字节原样搬**, 且**总是写**(该调用点的既定用途是把工程标为最近修改: project_list.cpp:866-869 读该 mtime),
    并刷新 last_save_time 以免 editor_node.cpp:1627 的外部变更检查被自己的写触发;
    project.godot **不存在**时仍调 save()(创建工程靠它);
    **save()/save_custom()/save_custom_section() 可观测行为逐字不变**; 另外 27 个编辑器 save() 调用点未动;
    **D112 纪律全都满足**(最小/朝上游形状/可被门覆盖: 17 断言模块 doctest + 窗口化实测; 零新增收窄点, 门⑥ scanned==pinned==75)
    修后证据: 带注释 project.godot 经窗口化启动 **cca8e45d… -> dcc50cbd…**, **4 条注释逐字保留、顺序不变、
    [input] 里那条仍在 [input] 内**; 工具写入路径 D=4->F=4(一条注释行都没动)
 ④ 红/绿: mono 红 3 条(含 has(probe.cs) false==true) / plain 红 2 条, **均当场落盘入库**; 两变体最终全绿;
    ★ 它留了一条重要观察: **mono 绿与 plain 绿的文本 sha8 相同 -> 绿灯不能证明是哪个变体**(已留档)
 ⑤ 门: mcp059_gates.ps1 **21/21 步 exit0**; ③**344/23953**; ④**1770/448200**;
    ⑥三段式 scanned==pinned==75 + **101/101** + --coverage; --check-completeness/--added/--generator-version(1.19.0) PASS;
    契约前后同 sha; 门① -Group project_read_files **3/3**(9888+9889 各 6 条 name/description/inputSchema=True, 并集 153/72);
    门⑤ accept_m1 x2 **22/22 且 differing_lines=0**; 构建 plain/mono 严格串行, 两二进制 == HEAD 716957c26
 ⑥ 15 步回归电池 **14/15 exit0**(mcp010 29/29, mcp027 60/60, mcp044 40/40, mcp045 15/15, mcp046 23/23,
    mcp052 53/53, mcp053 73/73, mcp041/042/043 各含 5 回归); 唯一非零是**电池自检'工作树必须干净'**
    (manifest 证明 newly modified=0/newly untracked=0/restore failures=0, 5 个源文件 KEPT-DIRTY-BEFORE-THE-RUN -> **非回归**)
 ⑦ 其余 5 条发现**不修且各有依据**: F-066-3 单复数校验形状(契约已逐字声明两种读法, 统一是**破坏性 API 变更**);
    F-066-4 游戏视口恒为 game(mcp_capture.cpp:375-376 声明游戏进程只有一个窗口 -> 该字段是**有效值**而非被忽略的请求);
    **F-066-5 all_passed:false 且无断言 —— 刻意如此**(running_game_test_execution.cpp:596-599/:243-246:
    '什么都没断言就不该被报成全部通过' —— **我完全同意**); F-066-6 .tscn 字面量计数(判据设计缺陷, 模块不依赖);
    F-066-7 already_connected:true(已声明为正向); 另登记: R4 的 waited_seconds 入/出参命名(修它要动契约 sha,
    而本批整条证据链锚在该 sha 上) + R4 的 .dll 字节数陈旧(报告引用缺陷, 应 append-only 勘误到 R4)

裁决/下一步候选(均已登记, 择要排期):
  (a) **.godot walk 是否收窄**(现会把 res://.godot/mono/temp/obj/Debug/ 下 2 个生成 .cs 列出) -> 我倾向**不收窄但声明**
      (收窄会撞钉住断言, 且'列出生成文件'对使用者是**诚实**的; 若要收窄须同时更新那条断言并说明)
  (b) waited_seconds 命名统一 -> 走 override, **单独一批**(避免与证据链 sha 冲突)
  (c) **check_rename_map.py 仍硬编码 171**(既有陈旧期望) -> 与 TASK-064 同类, 改为派生
  (d) R4 的 .dll 字节数勘误 -> append-only 修 R4
目标仍 active(hof-rs 一半按用户指令暂停)

累计: Godot 侧 176 条工具; **三个引擎补丁**(C# 判定前置 / 按节发布 / 编辑器自身保存保全文本); 试测 4 轮;
  第 4 轮六判据全通过 + 8 条空白全收; 观察连续两轮 stop_reason=marker

## D126 — TASK-068 交付（陈旧期望派生／描述澄清一次移动 sha／append-only 勘误）+ 又抓到两条「门/取证是摆设」缺陷

docs(decisions): D126 TASK-068 交付(陈旧期望派生/描述澄清一次移动 sha/append-only 勘误) + 又抓到两条'门/取证是摆设'缺陷

TASK-068(HEAD eff591a14; plain+mono 二进制均 == HEAD; 报告时**未提交**, 我随后提交):
 ① **check_rename_map.py 陈旧 171 -> 已派生**: ported 从 dropped 集合数出、added 读契约 _meta, **171 保留为被检查字面量**;
    修复前 exit 1(恰好 G1/G5 两条 FAIL) -> 修复后 **exit 0**; **反向探针 7/7**(旧表达式同输入为假/新为真/**喂坏输入为假 = 非恒真式**)
    新增普查工具 **check_hardcoded_counts.py**(221 行, 纯 ASCII): 144 个脚本逐行扫 7 个数(171/173/175/176/152/72/153),
    **147 处 / 6 桶 / 0 UNCLASSIFIED**; 逐条清单入 evidence\task068\logs\census_hardcoded_counts_verbose.txt;
    显式登记本批不动者(5 处 PINNED 属各批次取证脚本, 改它们会动已提交证据树的重跑结果; CHECKED 4 行是要求保留的被检查字面量)
 ② **两处描述澄清(契约 sha 只移动一次)**: 均 mode=append + reason 逐字引用被替换成员;
    (i) **project_list_scripts 如实声明**会列出 .godot 下生成脚本(walk 从 res:// 递归只跳 . 与 ..,
       mono 工程会出现 res://.godot/mono/temp/obj/Debug/*.AssemblyInfo.cs, 调用方自行过滤)
       —— 依据 project_read_files.cpp:215-239 + D125 裁决(b) + REPORT-067 §1.4 的 2 条实测; 参数面零变化
    (ii) **waited_seconds 经核实不是同名异义**(入参 seconds @:316-317; 出参 waited_seconds @:440/:459; 不同对象;
       找到节点时不回显 @:461-465) -> **只改描述、不改名、不加别名**(加契约未声明入参会破坏门① 逐字);
       实测旧调用仍可用(seconds 成功回显 1.5; waited_seconds 当入参仍 -32602; 错类型仍 -32602)
    C++ 侧手工同步 + 生成器重跑相结合; mcp068_contract_cpp_diff.py 逐字比对 PASS(373/373、571/571 字节);
    **契约 176 条不变, sha d4e53b43… -> 70153982…(155872 B), overrides 31->33, generator 1.20.0**;
    inputSchema 一条未动; tool-rename-map.json 逐字未变; 五份批次清单逐字未变
 ③ **R4 追加'附录 A'(append-only, +48 行全在文档末尾, §8.3 原文一字节未改)**:
    被勘误对象 = §8.3 正文引用的 19968 B; 追加实测(工作树 eff591a14) **20992 B / sha 2e1ff3dd…**(本批**独立复算成功**);
    **不改原文的三条理由**(①19968 是 A 原叙述的逐字引用, 改了读者无法再核对 REPORT-066:39; ②历史报告按 PLAYBOOK §7.3 走追加勘误不回填;
    ③两个数字同时在场才构成'同一工程两次构建程序集变大'的时间线); 并写明诚实边界(20992 的正确读法是'TASK-068 实测时刻盘上的值')
 门: ①逐字 3/3(153/72/contract 176, guard 9877 pid_before=-1/after=-1); ②**45/45**;
    ③**345/23971**(基线 344/23953, +1 用例 +18 断言); ④**1771/448218**(+1/+18); ⑤accept_m1 x2 22/22 differing_lines=0;
    ⑥三段式 scanned==pinned==75 + 101/101 + --coverage, **本批新增收窄点=0**;
    --check-completeness(171+5=66+105+5 PASS)/--added(三方版本同串)/--generator-version 全 exit0;
    红相位(18 断言中 14 失败)与绿相位(18/18)**当场落盘**; 构建严格串行 4 次

★ **又抓到两条'门/取证是摆设'缺陷(与 D116 恒真断言、D117 观察者假等待同族, 已登记)**:
  (i) **回归电池会删除它见过的未跟踪报告** —— 本批报告被电池删掉后被迫重建
    -> 比'覆写'更糟(**删证据**); 必须改为: 电池只允许**改它自己声明的产物**, 对**未跟踪的新文件**要么避开要么备份后还原并打印清单
  (ii) **mcp041/042/043_gates 返回 exit 0 却掩盖 3 个内部红色步骤**(A22/A23/A26b、L21x5, 全是 TASK-057/059 的陈旧期望)
    -> **一个'看起来在检查、实际放行'的门**; 必须改为: **内红则整体非零**(或至少把内红汇总进退出码), 并修那 3 处陈旧期望

累计: Godot 侧 **176 条工具 / 契约 sha 70153982…**; **三个引擎补丁**(C# 判定前置 / 按节发布 / 编辑器自身保存保全文本);
  试测 4 轮(六判据全通过 + 8 条空白全收 + 观察连续两轮 stop_reason=marker);
  已系统化四条'不能是摆设'纪律: 恒真断言(D116) / 假等待(D117) / 静默覆写证据(D122) / **删证据与内红放行(D126)**
下一步候选: ①修 (i)(ii) 两条门缺陷(优先, 因为它们会污染**所有**后续批次的判断);
  ②对**三个引擎补丁 + 新增 5 个工具**做一次**独立验收**(GDR-28 第 5 条; 目前只有实现方自证的门);
  ③hof-rs 一半仍按用户指令暂停
目标仍 active

## D127 — TASK-069 交付：两条门缺陷已修（电池删证据／内红被吞两层）+ 新增 check_exit_propagation.py 并入 accept_m1 case0

docs(decisions): D127 TASK-069 交付 —— 两条门缺陷已修(电池删证据 / 内红被吞两层) + 新增 check_exit_propagation.py 并入 accept_m1 case0

TASK-069(HEAD 48a3c2e33; 契约 **176 条未动**, sha 70153982… 与 TASK-068 逐字节相同; 未 push; 未碰 9877; 未改引擎/DESIGN-DETAIL):
 ① **电池删证据 -> 复现并修复**: 改动前清单逐字自相矛盾(REMOVED …REPORT-069-planted-untracked-during-PRE.md
    而收口宣布 
ewly untracked=0), 运行后植入文件 Test-Path False;
    修法 = -AllowedPaths/-AllowedRoots **路径白名单 + 默认拒绝**(空串/'.'/'/' 归一为空 -> throw 'would declare every path';
    两列表皆空 = 默认拒绝); tracked 还原与 untracked 删除**两半都过判定**; 未声明一律 UNTOUCHED/UNTOUCHED-MODIFIED 原样保留;
    清单细分为 RESTORED/RESTORED-NEW/UNTOUCHED/UNTOUCHED-MODIFIED/KEPT-DIRTY-BEFORE-THE-RUN/RESTORE-FAILED/SUMMARY;
    判定改为'**声明范围内** leftover 必须 0'
    修后: battery_post 清单 RESTORED-NEW 1 / REMOVED 0 / UNTOUCHED 1, 植入件 Test-Path=True 且 sha256 **与植入值逐字相同**;
    探针 mcp069_guard_whitelist_probe.ps1 **19/19**(临时 git 仓库四路径: 声明内两半被还原/删除, 声明外两半原样;
    默认拒绝场景四项零改动; -AllowedRoots ./ 抛错; 
ot-evidence/a.json 不被认成已声明)
 ② **门内红却 exit 0 -> 复现两层并修复**: 改动前 mcp042_gates|0/mcp043_gates|0, 而其 summary 内写着
    STEP gate2_rewrite_and_honesty_evidence EXIT 1 等; 更底层 **mcp040_defect_probes / mcp040_racing_regression
    打印 FAIL 却不设退出码**(红被吞**两层**);
    修法 = 三个 mcp*_gates.ps1 末尾**同一段收口**(把 summary 打印移到收口之前使其成为最后语句):
    Select-String -Pattern 'EXIT [1-9]' -> 非空则逐条打印并 **exit 1**, 否则打印 ALL STEPS EXIT 0
    验证: 人为制造一红 -> FAILED STEPS: 1 / GATES_EXIT=1 -> 删除注入并 **sha256 证明逐字节还原**;
    机制级演示 mcp069_exit_propagation_demo.ps1 **10/10**(逐字抽取真实驱动的 Invoke-Step 与收口, 断言是真实文件 byte-exact 后缀)
    **普查**: scripts/** 与 docs/scripts/** 中 14 个'能报红'脚本 -> **12 个此前会吞红(全部已修)** + 2 个 dot-source 库(pin 带理由);
    已修含 7 个 step 电池 + 4 个 check 聚合器(mcp022/mcp023 写 failed 数却无 exit; mcp040 两个打印 FAIL 后无 exit;
    **docs/scripts/selfcheck.py 打印 FAIL 后 sys.exit(0)**)
    ★ **新增 scripts/check_exit_propagation.py(门⑥ 形状)**: 3 种已声明形状 + 16 种已声明 guard 拼写 + SHAPE_GUARDS 映射 +
    **双向核对 PINNED**(未 pin 而命中=失败; pin 了不命中=STALE PIN) + --probes **10/10** + --coverage
    (诚实声明不保证的部分: sys.exit(main()) 不跟踪返回值 / 拼写对但不可达的 guard / .cmd 不扫)
    **并接进 accept_m1.ps1 的 case0_repo_exit_code_propagation** -> **每批必跑两次, 无法静默复发**(例数 22->23)
  陈旧期望改派生: A22/A23/A26b 从'整文件重写'改为**由标本字节算出**的前导/节边界断言;
    L21x5 从钉死一句改为**按 DESCRIPTION_OVERRIDES 声明的 mode 派生**(replace=逐字节相等); **反向探针 44/44**
  门: 最终锚点电池 **17/17 步 exit 0**(ALL REGRESSION STEPS EXIT 0); 三个 gates 全部 ALL STEPS EXIT 0;
    ⑤ accept_m1 x2 **23/23 differing_lines=0**; ③**345/23971**; ④**1771/448218**; ⑥ 75/75 + 101/101 + §22.3b 规则4 新增收窄点 0;
    --check-completeness/--added/--generator-version/check_rename_map/check_tautologies 全 exit 0;
    端口收尾无 LISTENING(仅 TIME_WAIT); 工作树 17 个 M(+499/-42) + 5 新脚本 + 报告 + evidence/task069(46 文件)

★ 纪律沉淀(第五条, 与 D116/D117/D122/D126 同族): **'能报红的脚本必须在红时真的非零'** ——
  红被吞有两层(聚合器 + 底层脚本), 所以既要**修个案**又要**仓库内断言 + 每批必跑**(内置进 accept_m1 case0)。
  这条与'恒真断言/假等待/静默覆写/删证据+内红放行'共同构成**门不能是摆设**的一族。
  一般化: 任何'多层封装的门', 其**退出码必须逐层向上传播并且有机器断言在核**
下一步: ①对**三个引擎补丁 + 5 个新增工具**做**独立验收**(GDR-28 第 5 条; 目前只有实现方自证的门);
  ②此后可回到试测循环或按用户指令收口; ③hof-rs 一半仍按用户指令**暂停**
目标仍 active

## D128 — **独立验收 pass（零阻塞缺陷）**：三个引擎补丁非侵入性 + 5 个新增工具拒绝面 + **门完整性五条绕过尝试全部失败**

docs(decisions): D128 **独立验收 pass(零阻塞缺陷)** —— 三个引擎补丁非侵入性 + 5 个新增工具拒绝面 + **门完整性五条绕过尝试全部失败**

TASK-AUDIT-ENGINE(**verdict = pass**; 全新验收子代理, **未采信任何 REPORT-* 与我的摘要**; 锚点 e45ad638e6):
  开工: build_local.cmd -Force exit0; 模块 doctest **345/23971/0**; 全引擎 **1771/448218/0**; accept_m1 **23/23 x2 清单逐字节一致**
 ① **补丁非侵入性 = pass**: 净改动仅 **5 个引擎文件 752+/7-**;
    **把 7 行被删既有行逐行列出并判定**(project_settings.cpp save_custom 头行+ERR_FAIL+空行=**纯搬家**;
    editor_node.cpp:1071 save() 改为 :1085-1088 的 if/else=**有意改进调用点**; csharp_script.cpp:2174-2176 三行 ->
    :2174 if(is_source_newer_than_assembly()) 且**对任意 mtime 等价**(空路径/mtime==0 旧式也是 0>x=false));
    **reload()(csharp_script.cpp:2586)/save()(project_settings.cpp:1085) 完全未动**; save_custom 签名/Error 返回未变;
    save_custom_section 补丁②与③签名逐字相同; **editor/ 下 26 处 save() 调用点字节不变**(第 27 处是注释);
    新 API 仅 save_preserving_text(editor_node.cpp:1088)/publish_settings_sections_text(project_settings.cpp:1922)/
    save_custom_section(tool_helpers.cpp:651) 被用
    **行为实测(自造工程 3 行手写注释)**: add_autoload 节写入 sha 32209af4->8b92f419 **注释 3->3**, 重复调用 sha 不变;
    **反向探测** remove_autoload(声明整文件) sha->a7d9e7ff **注释 3->0** 且换成引擎 7 行抬头;
    project_set_setting 无节名->整文件(3->0), 有节名->只多 [audit_probe]/value=5.0 三行(**3->3**)
 ② **5 个新增工具拒绝面 = pass**: **20 条反例**(glow_levels/1 非标识符、未知属性、越界路径、project.godot、.tscn/.gd/.cs 覆盖)
    **全部同族拒绝 -32602/-32001/-32000 + data.suggestion, 无悄悄成功**;
    **stop_on_error 两种语义含回滚后读回证明**(先写 position 11.5 读回 11.5; 再以 99.5+坏条目在 true 下批量 ->
    rolled_back + **读回仍是 11.5** = 真的取回);
    ★ **代码腿 ValueSlot 链条**: editor_set_node_property_updates -> write_node_property(editor_node_property_updates.cpp:276)
      -> prepare_node_property_value(running_game_node_write.cpp:1009) -> **value_fits_slot(tool_helpers.cpp:2410, 实现 :1789)**
      => **收窄闸门没有被绕**; 其余 4 个工具无 Variant->类型化槽写入, 故闸门命题**不适用而非被绕过**(区分得很清楚)
 ③ **契约对等 = pass**: 实时 tools/list(落盘后 ConvertFrom-Json **非文本包含判断**): 9888=153 / 9889=72, **并集=176**,
    missing=0 foreign=0; 153+72 条 canonical **逐字**(mismatches=0); scope **双向零泄漏**; 跨端点 -32601;
    唯一差异 = 1 条 inputSchema 的**成员顺序**(order_normative=false) -> **判为非缺陷并给引证**
 ④ ★ **门完整性五条绕过尝试全部失败(本次最重要产物, 证明门不是摆设)**:
    (i) 植入 -or True -> **exit 1 并点名** scripts\zz_audit_tautology_probe.ps1 第 3 行;
    (ii) 植入'有打印器但无 guard' -> **exit 1 点名**; 自带演示 unguarded exit0 且 summary 带 EXIT 3 / guarded_red exit1 / guarded_green exit0;
    (iii) 假等待: 开发进行中->**timeout**、卡住->**stale**、marker 叶子存在->marker、
      **marker 路径为目录 -> timeout 且 marker_seen=False**(**冒充被挡**), 未结束时**永不为 marker**;
    (iv) 删证据/静默覆写: 未声明 REPORT-planted.md **原样存活**、声明外已跟踪文件不 revert、**默认拒绝 restored=0 removed=0 untouched=3**、
      **blanket './' 声明抛异常**、子串 not-evidence 不误判;
    (v) accept_m1 case0_repo_exit_code_propagation **两次 PASS**
    它同时给出**门调用事实**与**边界**(恒真/退出传播检查是**拼写可见的有限集合**——集合外写法实测能逃, docstring 已声明;
      marker 不校验写入者) -> **诚实标注保证范围**
  defects: **无阻塞项**!
  unconfirmed(诚实列 5 条): mono/C# 成功腿未独立复测(mono 二进制 48a3c2e33=HEAD~1, 但 diff 只含 scripts/** 与 docs/** ->
    结构性等同; 未重建也未实测); editor_node.cpp:1071 的开窗保存带 !cmdline_mode 守卫, save_preserving_text()
    只做了源码级核对(**未在窗口化编辑器里真跑并比对 project.godot**); mcp059_gates/mcp056_regression_battery
    未整脚本重跑(以 git grep 行号 + 单独执行被调命令证明); 双精度 precision=double 构建未验; 证据守卫**只约束自身还原函数**
  clean: 审计后 git diff 空; 只剩 4 个既有未跟踪物 + 任务书 + 报告; 9877/9888/9889 无 LISTENING; 无孤儿; 未 push; HEAD 未变

★ 结论: **Godot 侧至此完整闭环** —— 176 条工具 + 三个引擎补丁 + 试测 4 轮 + 门完整性五条纪律,
  且**关键部分已被一个不继承任何结论的独立验收方复核为 pass**(含对门的**主动绕过尝试全部失败**)
目标: **仍 active** —— 唯一未完成的原始目标是 hof-rs 切换端点与真实 T=1 冒烟, 而用户明确指令**暂停**该半;
  Godot 侧已交付完毕, 不应在用户未解除暂停前推进 hof-rs

## D129 — TASK-070 交付：独立验收的 5 条未确认**全部关闭**（含**窗口化实测补丁 3**）+ 三条新发现

docs(decisions): D129 TASK-070 交付 —— 独立验收的 5 条未确认**全部关闭**(含**窗口化实测补丁 3**) + 三条新发现(F-1 测试缺配置独立性 / 守卫盲区已构造 / 本地化假 FAIL)

TASK-070(锚点 3cbaacd6b; 契约 **176 未变**; 已跟踪文件 0 改动; 未 push; 9877 全程无监听且**从未被请求**):
 ① **mono/C# 成功腿(关闭)**: mono 串行重建到 HEAD(108 s, --version == HEAD) ->
    成功腿 exit0 + 产物 **sha cf88da4f…(5632 B)**; 非 mono 能力缺失腿 **-32000 + 建议**;
    **三态在 mono 构建上实测**(ok / **invalid + 编译器自己的 CS1519/CS1002/CS1040** / not_compiled),
    且**同一 payload 内 count=3=sum**; 失败构建后产物 sha 未变
    副产品(如实登记): (a) **.NET SDK 输出是本地化的** -> 'Build succeeded' 曾是**假 FAIL**,
      判据改为'退出码 + SDK 自己的 <Asm> -> <path> 行 + 产物指纹'; (b) 首次 --import 出现**一次间歇性 0xC0000005**
      (第二次成功, 日志尾部指向 EditorNode::is_cmdline_mode) -> **只登记、不归因**
 ② ★ **窗口化补丁 3 实测(关闭, 且补上了上游缺的维度)**: **真的开窗口**(-e --path <proj> --mcp-port=9888, **无 --headless**),
    其自身日志: 'OpenGL API 3.3.0 NVIDIA 616.56 … Using Device: **NVIDIA GeForce RTX 4090**' +
    '[MCP] listening on 127.0.0.1:9888 (editor=true, tools=153)';
    fixture: **5 条手写注释(2 条在 [input] 内)**、[input] **非末节**、含引擎从未听过的键、无 BOM;
    **实测结果**: 开窗后文件**逐字节不变**(sha b6a07dc1…)而 **mtime 前进**(639259222579937631 -> 639259222967615149)
      -> **证明'真的写了、且写出来一模一样'** —— **字节相同本身无法区分'写了没变'与'根本没写'**,
      这正是上游源码级核对**缺的维度**(只有 !cmdline_mode 分支会写);
    幂等: 第二次开窗 sha 不变 + mtime 再前进(与声明的'总是写'一致);
    对照: --import 与 --headless 均 sha **且 mtime** 不变;
    **反向**: ProjectSettings.save() 经 --script 探针**仍整文件重写**(5 条注释消失 + 引擎头);
    ★ 调用点集合与补丁前修订**逐文件逐数一致**(28 行/16 文件, added=∅ removed=∅);
    ★ 它**纠正了自己一个判断错误**: 比较 file:LINE 是错的, 因为补丁 3 让 6 个调用点行号移位(应比 file:count 集合)
 ③ **两个门驱动器整脚本重跑(关闭)**: mcp059_gates **21 步全 0**(ALL GATE STEPS EXIT 0); mcp056 电池 **15 步全 0** +
    accept_m1 x2 **23/23 differing_lines=0** + 还原清单 RESTORED 56 / RESTORED-NEW 1 / UNTOUCHED 1 / git diff --stat 0 行
    ★ **纠正了一个流传的认知**: 电池**根本不会**因'工作树脏'而非零 —— 它只是**打印**(实测: mcp041/042/043 用 Add-Content 记录,
      rb2 打印); 本轮活证: 运行中写入的报告以 **UNTOUCHED** 出现而电池仍 exit 0 -> 任何此类失败都只是自检读数, 不是回归
 ④ **双精度(关闭, 本机能构建就真建了)**: precision=double 冷构建 **14 min 51 s exit 0**,
    独立变体 bin\godot.windows.editor.double.x86_64.console.exe(sha ab4835e8…), **与 plain/mono 并存不需回建**;
    探针证明真是双精度(Vector2(1e300,0).x 打印 301 位小数且有限 vs 单精度 'x=inf is_finite=false');
    ★ **ValueSlot::FLOAT32 在真双精度二进制上实测 2/2 PASS**(其 FLOAT32 半段无条件编译 tool_helpers.cpp:1801-1807,
      若 FLOAT32 委托给 REAL_T 则任何构建都会失败) -> **主张从'源码级+单测级'升为'真机实测'**
    ★ **新发现 F-1(非阻塞)**: 同一套 345 用例在双精度二进制上是 **338 过 / 7 红**, 7 条全是
      '标量 real_t 成员 / Vector2/Rect2/Vector4/Quaternion 分量拒绝 1e300' 这类**单精度期望**
      (失败输出里 **0 条断言涉及 FLOAT32**、20 条涉及 REAL_T) -> **是测试缺配置独立性, 不是门错**;
      正确写法已存在于 test_mcp_server.h:15043(if (sizeof(real_t) == 4));
      **不影响今天的单精度交付(门③ 345/345), 但若哪天把双精度纳入门, 门③会红**
 ⑤ ★ **守卫盲区被构造并承认(关闭)**: (A) **快照前就存在的未跟踪文件**被别处删除 -> **manifest 零行**且文件真没了;
    (B) **未跟踪目录内部**的活动(改写+新建) -> 零行;
    机制: Get-McpEvidenceState 只产生 Modified(tracked) 与 Untracked(**目录级**), Restore-McpEvidence 只遍历
      '新出现的 modified / 新出现的 untracked' -> **没有'existed before, gone now'这一支**
    **更糟**: 电池**自己的裁决也瞎** —— 重算的 declared-leftover 会是 0, 即真实静默删除后仍会打印 	racked_evidence_restored
    **建议(带可工作原型 + 实测成本)**: 用 git status --porcelain -uall 的**文件级清单**(path -> length:mtime ticks)
      替换目录级 Untracked, 新增 MISSING-UNTRACKED / APPEARED-UNTRACKED / CHANGED-UNTRACKED 三类 manifest 行;
      实测本仓 4029 个未跟踪文件: **2304 ms/次(不哈希)**, 6445 ms 含 sha256; 原型**三类差异全抓到**(10/10),
      且哈希模式**没有多抓到**长度+mtime 能抓的
    **三条边界**: 只能**发现**不能还原被删的未跟踪文件(价值是把静默成功换成显式告警); 受 git status 视野限制(ignored 仍在视野外);
      长度+mtime 可被**同秒等长改写**绕过 -> -HashUntracked 作为可选
    探针离开时仓库逐字节不变(porcelain -uall 前后各 4026 行, 0 差异)
 门: ①逐字 5 个调用点各 3/3(contract=176, union 153/72); ③**345/23971/0**; ④**1771/448218/0**; ⑤accept_m1 x2 **23/23**;
    ⑥三段式 exit0 + 探针 **101/101** + 本批新增收窄点 0; --check-completeness/--added/--generator-version exit0(1.20.0);
    构建严格串行且 START-END 互不重叠(plain 51 s / mono 108 s / double 14m51s); 6 个新脚本纯 ASCII; 三次红相位原样保存

裁决/下一步: ①**采纳守卫的文件级清单改进**(原型已可用, 成本可接受) -> 排为下一批(A 项);
  ②**F-1 修测试的配置独立性**(照 test_mcp_server.h:15043 的 if (sizeof(real_t) == 4) 写法包住 7 条) -> 同批(B 项),
    并在报告里写明'门③是单精度门'这一**已声明口径**;
  ③0xC0000005 保留为**已登记的未归因间歇**(下次窗口化运行前留意, 若复现则立项);
  ④hof-rs 一半仍按用户指令**暂停**
目标仍 active

## D130 — TASK-071 交付（守卫文件级清单：盲区被点名／F-1 修好：单精度 345、双精度 345／**声明门③是单精度门**）+ 发现「锚点假红」流程缺口

docs(decisions): D130 TASK-071 交付(守卫文件级清单: 盲区被点名 / F-1 修好: 单精度345 双精度345 / **声明门③是单精度门**) + 发现'锚点假红'流程缺口

TASK-071(提交 4c2532c178 实现/测试/证据 + 7b8478a7da 报告; 锚点 4512d14c7e; 契约 **176 未变**; 未 push; 9877 全程 pid=-1 且从未请求):
 A **守卫改文件级清单(盲区消除)**: Get-McpEvidenceState 改用 git status --porcelain -uall -> **文件级** UntrackedInventory
   (path -> 'length:mtime_ticks', -HashUntracked 时追加 ':sha256'); 新增 Get-McpUntrackedInventory / Compare-McpUntrackedInventory;
   Restore-McpEvidence 新增 **MISSING-UNTRACKED / APPEARED-UNTRACKED / CHANGED-UNTRACKED**(未声明时为 UNTOUCHED-*)、PRUNED-EMPTY-DIR;
   SUMMARY 旧四字段**逐字保留**、尾部追加 missing/changed/appeared/pruned/inventory-hashed;
   **mcp056 电池裁决把 Missing+Changed 并入 leftoverCandidates**;
   加固: 哈希模式对锁定文件记 'unreadable' 而非中止; 快照/还原哈希模式不一致时抛错
   证据: ①盲区A(快照前已存在的未跟踪文件被别处删除): **第一版 0 行 -> 现 1 行 UNTOUCHED-MISSING-UNTRACKED 且无任何 RESTORED***;
     ②盲区B(已存在未跟踪目录内改写+新建): 第一版 0 行 -> 新建 2 行 + 改写 1 行;
     ③**电池裁决**: 同场景声明后 declared-leftover **由 0 变 4** -> 真删除**不再被报成 tracked_evidence_restored**;
     ④**明确声明并实测'只发现不还原'**(文件仍不在/仍是新字节); ⑤porcelain -uall 前后**逐字节(sha256)相同**;
     ⑥成本 **2336 ms / 6587 ms**(4026 文件, 复测 REPORT-070 的 2304/6445)
 B **F-1 修好(测试配置独立性)**: 按**已存在的** D-15 写法 if (sizeof(real_t) == 4) 给 7 条加配置条件 ——
   **单精度分支原断言逐字保留**(345/23971 与 TASK-070 基线一致, **未减少**);
   64 位分支改为'**real_t 槽能表示 1e300 就应当接受**'这一等价且更贴命题的断言, **并追加 ValueSlot::FLOAT32 的拒绝断言**
   (Color 分量 / PackedFloat32Array 元素; tool_helpers.cpp:1801-1807 的 FLOAT32 半段无条件编译)
   -> 使'**32 位收窄必须被拒**'在**两种构建下都存在**
   理由(它讲清了): 这 7 条的命题是'**同一闸门按槽位宽度判定**', 1e300 是否被拒是**该构建下槽位的取值**, 不是命题本身;
   没有整体改指 FLOAT32 槽, 因为那会**删掉标量 real_t 与 Vector2/Rect2/Vector4/Quaternion 分量这些真实写路径的覆盖**
   证据: 红相位当场保存(double 345|**338|7 failed**, 23961|99 failed, 失败断言点名 FLOAT32 = **0 条**、REAL_T 文本 22 处);
   **单精度 345|345 passed, 23971 断言(= 基线)**; **双精度 345|345 passed, 23956 断言**(差 15 是 if/else 分支固有差异, 改前差 10)
 ★ **口径声明**: **门③(--test-case=[MCPServer]*) 是单精度门**(跑 bin\godot.windows.editor.x86_64.console.exe, precision 缺省 float);
   **双精度当前未被任何门覆盖** —— 门①②④⑤⑥ 全是单精度/脚本级门, **'未纳入门'**明说;
   本批双精度 345/345 是**手工构建+手工跑**的证据, **不是门③的一部分**; 建议把 precision=double 做成门③**可选变体**(命令已固化)
 门: ①3/3(176/153/72, 9877 pid_before=pid_after=-1); ②**14/14**(为**非工具批次**新增了活证据脚本 mcp071_gate2_live_evidence.ps1:
   编辑器 tools/list 61863B/153、游戏 32973B/72、并集=176; 成功类/缺参类 -32602 'Missing required parameter: path'/底层失败类 -32001+建议/
   跨工具链 create->read->validate 闭合); ③**345/23971/0**; ④**1771/448218/0**(=基线); ⑤accept_m1 x2 **23/23 differing_lines=0**;
   ⑥三段 exit0(scanned=pinned=75, 18 条行号漂移提示为既有且全在 tools/**, 本批零改) + 探针 **101/101**;
   check_tool_groups 三模式 exit0(1.20.0); 另 mcp069 白名单 13/13、mcp070 第二版 10/10、mcp071 17/17;
   三次构建 START/END 互不重叠(单精度 17:50:22-17:52:07; 双精度 17:53:58-17:54:51)

★ **唯一非零(它如实归因, 且暴露一个流程缺口)**: 回归电池 exit 1, FAILED STEPS: 2 —— **只有 mcp052/mcp053 的 engines_match_head**,
  原因: **mono 二进制自报 3cbaacd6b 而 HEAD = 4512d14c7**(TASK-070 的提交只增 docs/scripts、**无引擎 C++**),
  REPORT-070 §4.2 在锚点 3cbaacd6b 上这两步是 **53/53 与 73/73**; 本批未重建 mono(范围外) -> 建议下一步重建
  **我的判读**: 这不是回归, 而是**'锚点假红'** —— **每次提交都会移动 HEAD, 从而让二进制锚点检查失效**;
  若照此下去**每批都会假红**, 而**假红会腐蚀对门的信任**(正是我们一直在消灭的那类问题)
  -> 下一批必须把它**机械化**, 而不是靠'记得重建 mono':
  改法(择一或并用): (a) engines_match_head 从'**精确 sha 相等**'升级为'**结构性等价证明**'
     —— 二进制锚点是 HEAD 的**祖先**, 且 git diff --name-only <anchor>..HEAD **不含编译输入**
     (即只含 *.md/*.json/*.ps1/*.py/*.txt 之类; 任何 *.cpp/*.h/*.cs/*.tscn 出现则**仍然红**);
   (b) 或者在门里**显式区分两种红**: BINARY_STALE_DOCS_ONLY(警告, 非零与否按口径) vs BINARY_STALE_COMPILED(真红)
   **必须**同时保留'真陈旧必须红'的能力(反例演示: 改一个 .cpp 但不重建 -> 必须红)
下一步: ①修上述'锚点假红'(A 项, 优先) + 重建 mono 并复跑到 53/53、73/73; ②可选把双精度纳入门③变体;
  ③hof-rs 一半仍按用户指令**暂停**
目标仍 active

## D131 — TASK-072 交付：**「锚点假红」机械化消除**（结构性等价证明，保留真陈旧必红）+ mono 重建复跑 53/53、73/73

docs(decisions): D131 TASK-072 交付 —— **「锚点假红」机械化消除**(结构性等价证明, 保留真陈旧必红) + mono 重建复跑 53/53、73/73

TASK-072(提交 e0534f5b59 / ff796dbf9 / 1cd6408403 / 37cc835898 / 8ffb92b4b2; 锚点 ff796dbf9; 契约 **176 不变**;
  未 push; 9877 全程未占用未杀 pid_before=pid_after=-1 asked_by_us=False; 工作树只剩 4 个既有未跟踪物):
 ① **单一判据**: modules/mcp_server/scripts/check_engine_anchor.ps1(sha 94cd937a…)
    Get-McpEngineAnchorVerdict 返回 {Verdict,Ok,Anchor,AnchorReported,Head,Ancestor,DiffCount,SafeFiles,RedFiles,Criterion,Reason,Summary};
    命令模式 -VersionText/-Anchor/-HeadSha/-RepoRoot/-Json, exit 0=PASS / 1=FAIL / 3=usage
    **四种可区分结论**: A==H -> **ANCHOR_EQUAL**; merge-base --is-ancestor 失败 -> **ANCHOR_NOT_ANCESTOR**;
    git diff --name-only --no-renames A..H 全落在非编译白名单 -> **ANCHOR_STRUCTURAL_EQUIVALENT**(打印安全差异清单与计数);
    出现任何编译输入或 **UNCLASSIFIED** -> **ANCHOR_STALE_COMPILED**(红)
    **fail-closed 细节(值得记)**: SAFE 白名单显式枚举(.md/.json/.txt/.ps1/.py/.cmd/.sh/.bat/.psm1/.psd1/.yml/.yaml/.toml/.cfg/.ini/
      .csv/.rst/.adoc/.html/.css/.svg/图片/.log + .gitignore/.gitattributes/.gitmodules/.editorconfig/LICENSE/COPYING/AUTHORS/NOTICE);
      **config.py 被显式从 .py 白名单挖出**判红; **--no-renames** 使重命名藏不住编译输入; A 不可解析/无 token/非祖先一律红
    **15 个锚点脚本 + 2 个探针统一 dot-source 调用**(mcp016/024b/025/026/047/052/053/057_gates/057_settings/059_gates/
      059_section/063/070_double/070_mono/070_windowed), **无第二份判据**; mcp052/053 检查条数仍 53/73
    探针: mcp072_anchor_judge_probe.ps1(**13/13**, A1-A10 决策表 + B1 26 行分类表 + C 真实二进制) +
      mcp072_anchor_counterexample_probe.ps1(**10/10**); 探针自带还原断言 S0 PASS(HEAD 回位/porcelain -uno 空/两文件 sha 逐字节相同)
 ② ★ **四个反例在真实仓库上演示**(临时提交 + finally reset --hard, 全部回位):
    ①只改 .md 不重建 -> plain 与 mono 均 **ANCHOR_STRUCTURAL_EQUIVALENT**, diff=1 safe=1 red=0, 清单 [S:...PLAYBOOK-group-port.md], **exit 0 不红**;
    ②改 .cpp 不重建 -> 均 **ANCHOR_STALE_COMPILED**, red=1, 清单 [R:modules/mcp_server/tools/registration.cpp(COMPILE_INPUT)], **exit 1 红**;
    ③非祖先: (a) 真实但不在历史的 commit -> ANCHOR_NOT_ANCESTOR ancestor=no; (b) **伪造 4.8.dev.custom_build.deadbeefc** ->
      'does not resolve to a commit'; (c) 无 hex token 的 4.8.dev -> 非祖先; **均红**;
    ④真重建 -> 两二进制 **ANCHOR_EQUAL**, diff=0, exit 0
    另 1b: 命令行入口在同一 docs-only 情形返回 ANCHOR_JUDGE VERDICT=ANCHOR_STRUCTURAL_EQUIVALENT / RESULT PASS exit 0(**库模式与命令模式一致**)
 ③ **没有削弱**: 输出里逐字写 '**the binary is NOT equal to HEAD, it is structurally equivalent to it**';
    每份证据保留 anchor/anchor_reported/head/verdict/ancestor/diff_count/safe_count/red_count/criterion 原文/完整差异清单/reason;
    mcp052/053 的 Check 证据行同时保留**两个 --version 原文(含 .mono. 变体标记)**与两个 verdict 摘要 -> 后来者可自行判断
 ④ **重建 mono(4 段严格串行, START-END 不重叠)**: plain@H1 18:41:46-18:42:37 / mono@H1 18:42:44-18:44:38 /
    plain@H2 18:49:37-18:51:29 / mono@H2 18:51:40-18:53:32, 全 exit0;
    --version = 4.8.dev[.mono].custom_build.ff796dbf9 与 git rev-parse --short=9 HEAD 逐字一致;
    二进制 sha: plain 4b269370… / mono 225198b3…
    复跑: **mcp052 53/53 exit0**(engines_match_head [PASS], verdict=ANCHOR_EQUAL, diff=0); **mcp053 73/73 exit0**;
    **回归电池 ALL REGRESSION STEPS EXIT 0**(REPORT-071 的 FAILED STEPS: 2 **消失**; accept_m1 x2 23/23 differing_lines=0;
      mcp041/042/043 gates 17/19/29 步全 0; mcp010 29/29、mcp019、mcp027 60/60、mcp044 40/40、mcp045 15/15、mcp046 23/23;
      tracked_evidence_restored declared leftovers=0)
    ★ **追加端到端证明**: **报告提交 1cd6408403 之后不重建**(二进制仍 ff796dbf9) -> mcp052 53/53 与 mcp053 73/73 **仍 exit 0**,
      判据 **ANCHOR_STRUCTURAL_EQUIVALENT**(diff=23 safe=23 red=0) => **'只改文档/脚本的提交不再造成假红'已闭环**
 ⑤ 门(锚点 ff796dbf9): ①3/3(176, 153/72, 9877 pid_before=pid_after=-1); ②**14/14**(mcp071_gate2_live_evidence.ps1:
    编辑器 153/61863B sha 333b4a68…、游戏 72/32973B sha 0ed732af…、并集 176、三类 + 跨工具链 create->read->validate、
    porcelain -uall 前后 sha 相同); ③**345/345 (23971)**; ④**1771/1771 (448218)**; ⑤accept_m1 x2 **23/23 differing_lines=0**;
    ⑥三段 exit0(**101/101** 探针后逐字节还原, tools/** 零改动); check_tool_groups 三连 exit0(1.20.0);
    **check_exit_propagation.py exit0**(它自己的探针曾出现 UNDISCHARGED **当场发现并修**: 失败计数改名为扫描器声明的
      $script:Failures, **未改扫描器**)

★ 纪律累计(第六条, 与五条同族): **门不得因'与判断无关的变化'而假红** ——
  判据要区分'**结构性等价**'与'**真的陈旧**', 且必须**同时证明两条腿**(docs-only 不红 / .cpp 变更仍红),
  否则就会用'放宽'换'不吵', 那是另一个方向的失败。
  另: 本次**修复方式**本身值得记 —— 单一判据 + 15 个调用方统一 dot-source, **杜绝判据复制带来的漂移**
下一步: Godot 侧已达'可移交'状态; 剩余可选项 = 把 **precision=double** 纳入门③的**可选变体**(命令已固化, 本机 345/345);
  以及 hof-rs 一半(**用户明确指令暂停**) -> 故**目标仍 active**, 不标完成
目标仍 active

## D132 — TASK-073 交付：双精度成为门③**可选变体**（默认不变，四种方式证明）+ **移交文档 578 行/21 条已知边界**

docs(decisions): D132 TASK-073 交付 —— 双精度成为门③**可选变体**(默认不变, 四种方式证明) + **移交文档 578 行/21 条已知边界**

TASK-073A(提交 9c12c23834 / 1ab3c14831 / b6fbb917b8; 锚点 9c12c2383; 契约 176 不变; tools/** 未动;
  DESIGN-DETAIL **未改**(提案文本在报告 §6); 9877 从未碰 pid=-1; 未 push):
  precision=double 现为门③**显式可选变体**: mcp059_gates.ps1 新增 -PrecisionVariant single|double(默认 single) +
  -WithDouble 别名 + 矛盾时 exit 3; 唯一新增步骤(标记 MCP073-ONLY-IN-DOUBLE-MODE)跑 scripts/mcp073_gate3_double.ps1:
  拒绝在 scons 存活时构建 -> 经 mcp070_build_double.cmd **串行**构建 -> 用 **TASK-072 的 check_engine_anchor.ps1** 判锚点
  (EQUAL/STRUCTURAL_EQUIVALENT 通过, **STALE_COMPILED 必须红**) -> 在 .double 二进制上跑**同一套** [MCPServer]* 并要求全绿
  ★ **默认不变四种证明**: ①mcp073_default_plan_compare.ps1 6/6 —— 在**完整 Invoke-Step 行**(参数/引擎 flag/用例集)上
    基线(git show 8ffb92b4b)22 步 == 工作树 22 步, 双精度模式 = 那 22 步 + gate3_double_variant;
    ②插入探针 4/4(插一步->exit1; 删标记步->exit1; 真实驱动保持字节不变);
    ③两次完整电池(锚点 9c12c2383): 默认 **22 步 ALL GATE STEPS EXIT 0** vs 开关 **23 步 ALL GATE STEPS EXIT 0**,
      22 个共享步骤的 name/exit 差异 **0**; 22 条尾巴 17 条字节相同, 5 条差异仅在 %TEMP% 证据根戳(逐行记录);
      gate3 单精度 345|345 与 gate4 1771|1771/448218 两边一致;
    ④**最强对照**: 5 个双精度产物(exe + 3 个 .double.obj)在默认运行前后 **LastWriteTimeUtc/Length identical(differing=0)**,
      且默认运行**未创建** mcp070_build_double.log、**未创建** gate3_double 证据目录
    它**明确不主张**什么: 电池 stdout 逐字节相同(时间戳/日志路径必然不同)
  双精度(开关): 电池 23 步全 exit0, gate3_double_variant exit0(8/8); 单跑最终脚本 **9/9 PASS**:
    构建 exit0; 双精度 doctest **345|345 passed, 23956|23956 断言**; 锚点 **ANCHOR_EQUAL**;
    同用例单精度对照 345/345、23971|23971(差 15 = if/else 分支固有); **未放宽任何断言**(同一用例集/同一判据, 绿=0 failed 用例与断言)
  ★ **红相位是构造出来的**: 回放 4512d14c7e 的 F-1 前测试文件(raw blob, git hash-object 验证) ->
    **与记录完全一致的 345|338|7 与 23961|23862|99**(0 条 ERROR 点名 FLOAT32、0 条越类失败),
    再 git checkout **逐字节还原**(sha256/blob/porcelain 断言) -> 重建转绿 345/345、23956 断言(13/13)
  ★ **'必须红'那条腿在真实状态上演示**: 本任务开始时双精度二进制自报 **4512d14c7e** -> 判官返回
    **ANCHOR_STALE_COMPILED**, ancestor=yes, diff=79 safe=78 **red=1**, 红清单 = modules/mcp_server/tests/test_mcp_server.h,
    RESULT FAIL 非零退出; 单精度二进制 sha 4b269370… **与 REPORT-072 记录字节相同**(本批从未碰它)
  时长(4 次严格串行, START-END 不重叠, 从 cmd, 不抑制, 同时只有 1 个 scons): 63.6 s / 70.2 s / 65.4 s / 62.5 s;
    双精度 doctest 14.4-14.5 s; 单精度对照 14.1 s -> **冷构建 ~15 min(REPORT-071), 热缓存开关 +~77 s, 默认路径 +0 s**
TASK-073B(**只写文档, 0 处代码/脚本/契约改动**): 产出 modules/mcp_server/docs/MCP-SERVER-HANDOVER.md(**578 行**)
  六节齐: ①交付物清单 ②门与**门完整性六条纪律** ③**已知边界与已声明限制** ④复现步骤 ⑤仍未做/被否决项 ⑥自检
  **21 条已知边界**(任务书点名 10 条 + 补充 11 条) **每条带锚点**(提交 sha / 契约 sha / 证据路径), 含:
    门③默认单精度+双精度为可选变体 / 证据守卫**只发现不能还原** / 恒真与退出传播检查是**拼写可见有限集合**(集合外能逃) /
    watcher **不校验 marker 写入者** / unverifiable/language_unavailable/not_compiled 三类语义区别 /
    project_list_scripts 会列 .godot 生成脚本 / **一次未归因的间歇 0xC0000005**(首次 --import) / 双精度未被默认门覆盖 ...
  复现步骤**自洽**: 脚本逐条在仓库内存在; 不需端口/构建的 **10 组只读检查当场实跑**, 数字与文档逐条一致(门类数字均标采集锚点)
  未 push; 未启动引擎 -> 未占用 9888/9889、未碰 9877

★ 结论: **Godot 侧已到'可移交'状态** —— 工具/引擎补丁/试测/门纪律/口径声明/边界清单/**复现步骤**齐备,
  且'门③是单精度门'这一**已声明口径**现已**可强制执行**(可选变体), 默认行为分毫不改
目标: **仍 active** —— 唯一未完成的原始目标项 = **hof-rs 切端点 + 真实 T=1 冒烟**, 而用户明确指令**暂停**该半;
  Godot 侧无剩余必做项(可选: 第 5 轮试测以继续发掘改进点)

## D133 — **试测第 5 轮**（2D 平台跳跃，232 次调用）：观察完整（stop_reason=marker）+ 汇总者纠正 4 处主张 + 4 条真缺陷

docs(decisions): D133 **试测第 5 轮**(2D 平台跳跃, 232 次调用) —— 观察完整(stop_reason=marker) + 汇总者纠正 4 处主张 + 4 条真缺陷(D2 契约违约且静默 / D3 有写无读 / D4 实例子节点不可寻址 / D9 错误计数低估)

TASK-074(三角色: 开发者 232 次调用 ok202/非ok30 + 回退 33; 观察者 watcher; 汇总者自建 10 个只读复算脚本;
  HEAD 58becb2f33; 未改 modules/mcp_server/** 与 modules/mono/**; 9877 未动; 未 push):
  **观察覆盖完整**: stop_reason=**marker**, polls=29, last_seq=199, trace_lines=505, elapsed=841s(**预算 4800s 未到顶**)
    -> 用户在 D117 报的'观察者提前结束'**本轮未再发生**(watcher + 协议修订生效)
  §0.6 **十一条判据**: **8 通过 / 1 部分通过 / 2 偷换 / 0 不通过**
    通过: ①多场景+实例化 ③动画关键帧(12 帧) ④Theme+UI+override ⑥粒子+视差 ⑦C#/GDScript 混用(build exit0, 运行期两种同现)
      ⑨大批量(一次 100 节点 71ms; 一次 12 个不同值) ⑩用户信号 5 条(scope:user 只列这 5 条 vs all 1355) ⑪运行期注入(逐帧跳跃弧线, y 20 个不同值)
    **部分通过**: ②TileMapLayer —— **无任何入口能给 TileSet 加 source/atlas**(source_count 0), cell 写入**永不可达** -> 能力边界(不可构造)
    ★ **偷换(被点名)**: ⑤ 建的是 **AudioStreamPlayer2D** 而非任务书要求的 AudioStreamPlayer **且未声明**;
      ⑧ 声称'用工具读回'而 **project_read_file/_text_file 双 -32601** -> 只能用 OS 级 sha256 验证
  ★ **汇总者纠正 4 处**(自建 10 个只读复算脚本, 从 trace-editor.jsonl 398 行/247681B、5 份追踪、CALLS.jsonl 232 行、raw/** 232 目录独立复算):
    ①**证伪开发者的 D1**('批量挂脚本不落盘'): 磁盘 main.tscn sha f82264933b54… 里 **Coin000…Coin029 恰 30 个 script = ExtResource**,
      路径唯一性排除单点补救 -> 采纳观察者结论(三路证据)
    ②**纠错**: 游戏侧非 ok **实为 14 条**(A/B 均记 2; B 靠两个相反口径误差相抵才凑出 30)
    ③⑩ 的 4 vs 5 条是**时序**(M6 早于 Coin002 补连 seq156)
    ④**D6 补强**: 写入类响应也**不确定**(save_scene 9 次 **7 个 sha**)
    另 §C **自纠 1 处**(曾误把 body/envelope 双尺寸读成副本漂移)
  ★ **4 条真缺陷(下一批要修)**:
    **D2(S1, 契约违约 + 静默失败)**: editor_set_node_script(_batch) 在**根类型 <-> extends 不兼容**时回 **attached:true**,
      而引擎**静默丢弃**脚本; **契约明文承诺的 eadable 字段在响应全文不存在**(sha ef8db75df33ab89b);
      证据: 编辑器日志 Area2D **0** 次、游戏日志 **30** 次
    **D9(S1)**: 错误计数低估(见上 14 vs 2)
    **D3(S2, 有写无读)**: 契约 176 条**无'读工程文本文件'**, project_write_text_file 有写无读 -> 写读闭环无法用工具完成
    **D4(S2)**: **实例子场景内部节点在编辑器侧不可寻址**(属性写工具能到 Anim, **信号工具不能**, 且 editor_get_scene_tree 也看不到),
      而**运行期完全正常**(4 份转储 World/Player children=0 而运行期 Anim 齐全)
    D5(S2, 未定性): TileSet 无 atlas source 致 tile 写入不可达; 终态 has_tile_set:false, 需最小复现
    D6/D7/D8/D10/D11(S3): 同参同响应不成立(写入类也不稳) / body-envelope 双尺寸落盘 / D2 的运行时证据只在 %TEMP% 未进仓库 /
      _property_batch 与 _updates 难分辨且 -32601 无提示 / **analyze_mcp_trace.py 因 args 恒为 str 结构性漏报一整类信号**
  开发者如实声明的两个不可构造: 100 枚金币**运行期拾取不生效**(裸 Node2D 无碰撞体 + coin.gd extends Area2D 被静默丢弃;
    修它要实例化 100 个子场景, 与'一次 100 节点'判据冲突 -> 声明而非伪造); TileMapLayer 同上
  **汇总者的两条'最该先做'**: ①给脚本写族补**根类型<->extends 兼容性判定**并**真的回出契约已承诺的 readable 字段**
    (D2+E3+M3 三合一; 验收**必须含合法绑定对照以防假修复**; 且**切勿按已被证伪的 D1 开工**);
    ②补 **project_read_text_file**(有写无读的不对称; 纯函数/无编辑器状态/回归成本最低; 可直接复用本轮现成对账 d39c679f9561… 逐字相等)
 待复现声明: D5 需一次活体最小复现; R4 的 '--import 默认 9877 副作用'未能独立复核

裁决(下一批 = TASK-075): ①修 **D2**(含**真的回 eadable** + 兼容性判定 + 合法绑定对照);
  ②新增 **project_read_text_file**(走 ADDED_TOOLS, 契约 176 -> 177; 与 project_write_text_file 对称, 同样拒绝 project.godot/场景/脚本? **不** ——
    读是只读操作, 应允许读任意工程内文本但**必须**限制在 res:// 内、拒绝越界与 .., 并**如实声明**它不解析语义);
  ③修 **D9**(错误计数); ④**D4** 与 **D5** 先做**最小复现**再决定修法(可能涉及引擎侧寻址); ⑤S3 择要(尤其 analyze_mcp_trace.py 的 args 恒 str 结构性漏报)
目标仍 active(hof-rs 一半按用户指令暂停; 本轮用户指令='工具可用后继续进行试测--改进的循环' -> 循环继续)

## D134 — TASK-075 交付：D2 契约违约+静默已修（含防假修复对照）／**新增 project_read_text_file（契约 176→177）**／D9 根因修且**撤回上轮错误结论**／D4·D5 定性／分析器漏报修

docs(decisions): D134 TASK-075 交付 —— D2 契约违约+静默已修(含防假修复对照) / **新增 project_read_text_file(契约 176->177)** / D9 根因修且**撤回上轮错误结论** / D4·D5 定性 / 分析器漏报修

TASK-075(锚点 077694816 / 35ae10422; **契约 177 = 171 + 6**(generator 1.21.0); 线上 **9888=154 / 9889=73**;
  未 push; 9877 从未碰; **modules/mcp_server 之外零改动**):
 ① **D2(S1) 修好**: 改前(bf9518c2b3, sha 4cff9d54…) 四个节点全回 ttached:true 而引擎**丢了 3 个**(编辑器 err 0 / 游戏 err 3),
    且**逐节点 readable 字段到处都不存在**;
    改后(35ae10422/077694816, sha a788caa9…): 不兼容 -> **前置拒绝 -32000 + data.suggestion**(点名 GDScript::instance_create()/
    CSharpScript::instance_create() 与 Area2D vs Node2D), errors[0].readable=false, **rolled_back=true, 什么都没写**;
    **合法绑定对照** -> attached:true + **readable:true**(sha 618d3ba4…); **防假修复对照通过**(合法绑定在运行游戏里 Good.marker=75 可读,
    非法被拒, 两处日志引擎丢弃消息 **0**);
    红相位: 写回基线字节重放 -> 红 3 例|2 失败|54 断言 -> 绿 3/3|137 断言
 ② ★ **新增 project_read_text_file**(ADDED_TOOLS, **契约 177 = 171 + 6**): 描述与 inputSchema **逐字**; 只读; scope=both;
    **限制在 res://**(拒 user://、res://../、C:/Windows/、目录 -> -32602; 缺文件 -32001; max_bytes 边界 -32602);
    **每个响应都声明 parsed:false 与 'does not parse, validate or interpret'**;
    证据: (1)**写回执 sha = 读回 sha = 磁盘 sha = c824cf30d46289d3…**(size 20, text 相符);
      (2)四类拒绝各一条; (3)4096 B 文件上 max_bytes=16 -> 	ext_omitted:true + reason **而 size/sha256 仍描述整个文件**;
        max_bytes=8192 -> text_omitted:false; (4)非 UTF-8 -> -32000 + 建议;
    门① 逐字比对 name/description/inputSchema = True(它**先 FAIL 于 1048576.0 vs 1048576**, 靠'整数折叠回 INT'修好)
 ③ **D9 根因修好 + 撤回上轮错误结论**: 根因 = obs_digest.py:78 只在**编辑器**追踪列表上计数(:47 构造), 游戏侧段落**根本没有计数器**,
    且'按追踪计数只是下界'从未声明;
    修法: 从**权威 CALLS.jsonl(232 行)按端口计数** + 交叉核对 raw/**(30 条 error 响应 -> MATCH) + **无条件打印 COVERAGE 行**
    ★ **撤回**: 第 5 轮'游戏侧实为 14'**是错的** —— 权威记录/追踪/§C 自己的 aggregate 全说 **9889 非 ok = 2**(编辑器 28 / 游戏 2 / 合计 30);
      14 是两个端口的 **-32001 合计(12+2)被误归因**给游戏侧; 已用机器断言 D904 钉住这次撤回
 ④ **D4 定性(最小复现 9/9)**: **不是工具分裂**(三个工具共用 MCPTools::find_node, 彼此一致) —— 是**编辑器缓存了旧 PackedScene**:
    改完 player.tscn 并保存(磁盘已验证)后**活的实例仍 0 个子节点**、**同一会话新建实例也仍是旧的**、
    **游戏进程加载文件后有**该子节点; 会话内办法: 在**外层场景的实例下**加子节点 -> Player/Anim 可解析且连接(connected:true persisted:true);
    **声明边界**: editor_get_scene_tree 才是'可寻址性'的权威, 先改子场景
    (并查明第 5 轮那次属性写是在 **player.tscn 打开**时用 path 'Anim' 做的)
 ⑤ **D5 定性**: **能力缺口而非缺陷** —— project_create_resource{TileSet} 得 properties_set:[](无 atlas source);
    但 tile_set **赋值是生效的**(has_tile_set:true, source_count:0), 且 editor_set_tilemap_cell **明确拒绝** -32602
    'no source 0 … (add a TileSetAtlasSource first)' -> **推翻 E8 的'赋值未生效'**
 ⑥ **分析器结构性漏报修好**: missing_tools() 里 rgs = record.get('args') 后 isinstance(args, dict),
    而追踪在 **198/198** 行把 args 存成 **JSON 字符串** -> 整个'探过的参数'信号**结构性为空**('probed args none');
    修法: call_args() 接受两种拼写; '不可读(0)'与'录制截断(1: seq 128 editor_add_nodes_batch, args_truncated)'**分开计数**;
    新增 **--self-test**(合成用例 atlas_x/atlas_y/bogus 命中, node_path/source_id 从未探过, counts 2/0; exit 0/1) +
    **变异探针**(让 call_args() 恒返回 None -> 4 problems exit 1);
    同一份冻结追踪: probed args none -> **六个名字**(source_id x4, atlas_x x2, atlas_y x2, resource_properties x2, resource_type x2, atlas_coords x2);
    并**如实声明**该信号是'摩擦'而非判决(拼写正确但因别的原因失败的调用也会出现)
 门: ①3/3(project_text_read 组; 177 / 154 / 73 逐字 True); ②**26/26**(改前 18/18); ③**348/348 (24223)**; ④**1774/1774 (448470)**;
    ⑤accept_m1 x2 **23/23** 且 **177 名字清单逐字节相同**(names_sha256 276f162c…);
    ⑥三段全绿(scanned==pinned==75 + 101/101 且字节还原); --check-completeness/--added/--generator-version exit0(**171+6 = 66+105+6**);
    check_exit_propagation / check_tautologies / check_engine_anchor 均 exit0(ANCHOR_EQUAL 077694816;
    最后文档提交后 STRUCTURAL_EQUIVALENT **RED_COUNT=0**); §22.3b 规则4: 新增收窄点 0
 一处**预先存在**的非零(如实上报): check_hardcoded_counts.py 在 **未被他触碰**的 scripts/mcp071_gate2_live_evidence.ps1:192/:266
    报 2 行 UNCLASSIFIED; 已用'对该文件的基线树(git archive bf9518c2b3)跑同一检查器'证明**非本批引入** -> 留给后续
 契约数字同步: 49->50、152/153->154、72->73、35->36 全部重派生; 仍**故意不动**的他任务冻结证据脚本(mcp063/mcp066b/mcp071)已登记

裁决/下一步: ①Godot 侧工具数 177; 第 5 轮的 4 条真缺陷中 **D2/D9 已修、D3(有写无读)已消除、D4/D5 已定性为边界**;
  ②下一批可: (a)把 'editor_get_scene_tree 是可寻址性权威' 与 'TileSetAtlasSource 能力缺口' 写进**相关工具描述**(契约 sha 移动一次);
  (b)清掉那 2 行预先存在的 UNCLASSIFIED(mcp071 的 176 字面量改为派生);
  (c)进入**第 6 轮试测**(继续试测-改进循环) ③hof-rs 一半仍按用户指令**暂停**
目标仍 active

## D135 — **独立验收 fail**：抓到阻塞 D-B1（res 围栏被链接穿透，模块级）+ D-B2（编译不过仍报 readable）+ D-B3（分析器误报）+ 我的裁决

docs(decisions): D135 **独立验收 fail** —— 抓到阻塞 D-B1(res 围栏被链接穿透, 模块级) + D-B2(编译不过仍报 readable) + D-B3(分析器误报) + 我的裁决

TASK-076A(提交 e8c2ed5993 实现 / e83de65d98 报告+门证据 / b13f3197b5 锚点; **契约 177 不变**, sha 6f654b64… -> a5c59853…, overrides 33->36):
  ①**三条已定性边界写入契约描述**(append-only, 逐字门证明: 条数 177 不变/name 顺序不变/**每个 inputSchema 逐字节相同**/只有三条 description 变;
    git diff --stat 仅两个 tools/*.cpp 且只改 ToolBuilder 描述字面量):
    editor_get_scene_tree(编辑器侧可寻址性权威 + PackedScene 实例快照 + **先改子场景后改实例** + 明确'**不是各工具不一致, 差别在编辑器缓存**');
    editor_set_tilemap_cell / _cells_in_rect(TileSetAtlasSource 能力缺口, 如实声明)
  ②**清掉 2 行预先存在的 UNCLASSIFIED**: mcp071_gate2_live_evidence.ps1 :192/:266 的 176 字面量改为**派生**(.Count);
    新增反向探针(9/9: 旧字面量假/新派生真/变异输入假/检查器仍能抓裸字面量); check_hardcoded_counts exit 0(BUCKET UNCLASSIFIED = 0, total 157);
    红相位(改动前字节重放 -> :192 [176] / :266 [176] 两条 UNCLASSIFIED + RESULT FAIL)当场保存
  ③门全绿且**绑定最终二进制**(commit 后重做 build_local -Force 使 --version == HEAD e8c2ed599, **避免 D86 的 ANCHOR_STALE_COMPILED 假红**):
    ①两组各 3/3; ②26/26; ③348/348(24223); ④1774/1774(448470); ⑤accept_m1 x2 23/23 且 **177 名字清单 sha 276f162c… 逐字一致**;
    ⑥三段绿(75==75 + 101/101); 四检查脚本全 exit0; mcp068_contract_cpp_diff 5/5 MATCH
  它另登记(**未修**): mcp071 的 G204/G207 仍是 153/72(实测端点 154/73), 被普查归入 LIVE 桶故非本批 UNCLASSIFIED;
    **端点数无法从契约派生(需 scope)** -> 建议下一批一并派生

TASK-076B(**独立验收 = fail**; 锚点 b13f3197b; 提交 d1a2c031f5; 证据 62 份原始响应 + 6 个可重跑脚本 + MANIFEST):
  通过: **parsed:false 诚实性** / ★**D9 = 2(撤回成立)** / 分析器修复机制本身 / A 的两处描述改动与派生
  ★ **D9 撤回被三份互不相关的冻结记录证实**: CALLS.jsonl(sha 56d95094…, 232 行) -> 9888=28(-32602x9/-32001x12/-32000x4/-32601x3)、9889=2、合计 30;
    raw/**(232 目录)与 CALLS 按 response_file 1:1 关联 232/232 0 mismatch; traces(editor 28/game3 1/game4 1) -> 28/2;
    '14' = 两个端口 -32001 的总数(12+2) 被第 5 轮汇总**误当游戏侧数**(且与其自报'非 ok 30'自相矛盾);
    它还**逐字引用第 5 轮汇总者自己的产物** aggregate/c_calls2.stdout.txt 第 6 行: 'port 9889 calls 34 ok 32 non-ok 2'
  ★ **D-B1(阻塞, 围栏被链接穿透)**: **语法型越界 40 条探针全被拦住**(..、res:/..、a/../../、....//、%2e%2e/%2f/%5c、
    user://、C:/ 与 C:\、\\?\ 与 \\localhost\C$、F:、RES:///Res://、res://\\?\C:\、res://CON、NUL、目录、缺文件、
    非 UTF-8、max_bytes 0/-1/1.5/'abc'/16777217/16777216/1);
    但**链接穿透成立**: mklink /J proj\link <工程外目录> 后 project_read_text_file{res://link/secret.txt}
      **返回工程外文件全部字节**(响应 sha 8a60ea9d… == OS 哈希 a41903ea…), 9889 逐字节同结果;
      **project_read_script 与 project_get_filesystem_tree 同样穿透 -> 模块级洞**, 新工具继承
  ★ **D-B2(高)**: D2 只修了**根类型不兼容**; **编译不过的脚本** broken.gd(unc broken(:)仍被批量报
    **attached:true + readable:true**(响应 sha 609c6d82…)并写进 .tscn, 而**引擎载入场景时丢弃**
    (游戏侧 /root/Main/Sprite **无 script 字段**, H01 sha 791cb88c…; stderr 有 GDScript::reload(res://scripts/broken.gd:2) Parse Error),
    **同进程 project_validate_script 已答 valid:false/ERR_PARSE_ERROR**(sha c2f52f47…)
    -> **正是 D2 要关掉的那类谎报**(它据此判缺陷: 落在实现自己写下的承诺里)
    同时确认 D2 的四点要求实测通过: 不兼容必拒 + **盘上零写入**(main.tscn 前后逐字节相同) + 合法绑定 attached:true/readable:true;
    **防假修复通过**: 判据是引擎的 get_instance_base_type()+is_class(), 对基类方向/类不匹配/脚本继承脚本/RefCounted 全部正确, **非类型名硬编码**
  ★ **D-B3(中)**: probed_argument_names 不与'名字是否在该工具 inputSchema 里'挂钩 -> 冻结追踪上 6 条里
    **4 条**(source_id/resource_properties/resource_type/atlas_coords)是**契约确有且拼写正确**、只因**无 TileSet/枚举不认识 Vector2/类型不可写**
    而失败, 被读成'缺参数'; 真阳性只有 atlas_x/atlas_y
  它另如实声明 4 条 unconfirmed(其中: D-B1 是否按越界计**交由我裁决**; D-B2 是否属本轮范围;
    门③④ 只核对 0 failed 与 exit 0 **未与上轮 passed 基线逐一对比**(那需采信实现方历史数字);
    9877 未碰由'全程无 listener + 未发一字节'证明; **D-B1/D-B2 修复后本报告全部结论作废, 需新锚点 + 新验收会话**)

★ 我的裁决:
  (1) **D-B1 按缺陷修**(阻塞) —— **不是因为'提权'**(调用方本就能执行任意 GDScript, 那不成立),
      而是因为**工具描述承诺了 res:// 约束却返回工程外字节** = **声明与行为不一致**, 与前面七条纪律同族;
      修法: 解析真实路径(处理 ..、链接、junction、盘符、UNC)并校验在工程根内 -> 明确拒绝 + 建议; **一处修好覆盖三个工具**;
      若引擎 API 无法可靠判定 -> **如实声明 + 给出可被调用方自行校验的字段**(如 resolved_path), **不得保持沉默的穿透**
  (2) **D-B2 必修**: readable 必须意味着**引擎真的能载入/编译**(GDScript 走解析检查且与 project_validate_script **同源**;
      C# 走 invalid/not_compiled 口径); 不满足 -> 拒绝 + 回滚; **必须带合法对照**防过度拒绝
  (3) **D-B3**: 与契约 inputSchema **交叉核对**, **分两桶报告**(契约外参数 vs 拼写正确但别的原因失败), 命名不得暗示因果 + 加自测
  (4) 采纳验收方的纪律: **D-B1/D-B2 修复后必须派新的独立验收会话**(原结论作废)
下一批 = TASK-077(三条一起修); 之后 = 新的独立验收; hof-rs 一半仍按用户指令**暂停**
目标仍 active
---

## D136 — **事故与恢复**：cmd 下 `*>` 被当字面参数污染脚本参数 + 脚本未校验目标根即 `Remove-Item -Recurse -Force` → 引擎工作树被清空；四次反删除只救回 MFT 驻留小文件；最终以「fork 基线 + 会话记录重放」重建

**事故**（发生于 TASK-077 会话，现场记录 `INCIDENT-077-workspace-deletion.md`）：
一条更新记录的命令行在 **cmd** 里执行 —— `*>` 是 **PowerShell** 的重定向算符，cmd 只把 `*` 当**多余的位置参数**、
把 `>` 当自己的 stdout 重定向。PowerShell `-File` 模式按**位置**绑定未命名实参，于是脚本的第二个参数
（`$OutRoot`）变成了字面量 `'*'`。脚本随后照原样执行了自己的清理行
`Remove-Item -Recurse -Force $OutRoot`（**未校验目标根**），`'*'` 在当前目录展开 —— 当前目录正是
`F:\RustProjects\godot-mcp-pro\code\godot`，于是**该目录下每一项**（含 `.git`）被删。

**损失**：`modules/mcp_server/**` 全部源码/测试/文档/证据、三个引擎补丁、`bin/` 二进制，以及
`feature/mcp-server-module` 的**全部本地提交**（从未 push；远端只有 `master = 57277407a…`）。

**恢复的四次尝试**（现场处置由用户在本会话族之外执行；口径由 TASK-091 任务书给定，本文照此记录，不另编数字）：
① 第三方反删除工具；② `winfr /regular`；③ `winfr /extensive`；④ `winfr /extensive` 复跑。
**四次结果一致且都不够**：只救回 **MFT 驻留**的小文件 —— **< 1 KB 的内容可用，≥ 1 KB 的全部为 0**。
关键文件（`test_mcp_server.h`、`accept_m1.ps1`、`docs/DESIGN-DETAIL.md`、契约 `tools_list.renamed.json`）
与 **`.git` 对象库**（packfile 都是 MB 级）**全部不可用**。

**重建路径**（TASK-078…090）：fork 基线 `57277407e77e61b161f35dbd7aeb510f7a9e26a6` 重新克隆 →
新分支 `feature/mcp-server-module-rebuild` → 从 **178 份 / 566.7 MB 会话记录**抽取载荷重放
（661 个高/中置信载荷）→ 三个引擎补丁按记录值的 bytes/sha **逐项一致** → 之后每一批都重建、重跑九门、重新验收。
**已知不可复原**（如实声明，不假装等价）：契约 sha 与原值不同（重建 `078433de…` vs 原 `a5c59853…`）、
`accept_m1.ps1` 缺失区段未修、`test_mcp_server.h` 是 09-22 化石、`docs/DESIGN-DETAIL.md` 是化石、
`.git` 历史与 `bin/` 永久丢失。

**三条防复发纪律**（此后写进每一份任务书的「铁律」）：
1. **禁止一切 shell 重定向** —— 输出一律 `Start-Process -RedirectStandardOutput <绝对路径>` 或 `-OutFile`；
   脚本参数**一律显式命名传递**，绝不依赖位置绑定。
2. **破坏性命令默认拒绝** —— `Remove-Item`/`Move-Item`/`del` 必须：目标**非空、绝对、在显式白名单前缀之下**，
   **先打印将删清单**，参数含**通配符**或 `..` 或为空 → **直接 throw**；且**一律用 `-LiteralPath`**。
   迁移类操作走「**先复制 → 逐文件 sha 校验 → 才删源**」，校验不过则**保留源并报告**。
3. **每个里程碑 push** —— 本地提交不再等于「已保存」；引擎仓每个里程碑推到 fork，主仓每段可提交改动即提交。

---

## D137 — **迁移与嵌套 git 处理**：引擎克隆与试测工程迁入 `F:\moonbit-hof-rs\godot-mcp\`，独立 `.git` 保留、主仓只忽略不并入

**背景**：`H:\rebuild` 是重建期的临时落脚点。TASK-091 把它迁进正式项目根，并要求**妥善处理两个 git 仓库的关系**。

### 迁移（先复制、逐文件校验、才删源）

| 源 | 目标 |
|---|---|
| `H:\rebuild\godot` | `F:\moonbit-hof-rs\godot-mcp\godot` |
| `H:\rebuild\projects` | `F:\moonbit-hof-rs\godot-mcp\projects` |

- 复制用 `robocopy /E /COPY:DAT /DCOPY:DAT /MT:8`（**cmd 启动**，`Start-Process -RedirectStandardOutput` 收集输出）：
  引擎 **2322 目录 / 21793 文件 / 4.708 GB，FAILED=0 / Mismatch=0**；工程 **303 文件 / 6,029,718 B**。
- 校验由 `verify_tree.ps1` 做**逐文件 SHA-256**（`\\?\` 长路径前缀；树上最长路径 277/294 字符，
  > 260 的源 13 个、目标 80 个 —— `Get-ChildItem` 递归会静默漏掉，故用 `Directory::EnumerateFiles` + .NET 直读）：
  - 引擎：`src=21793 dst=21793 missing=0 extra=0 compared=21793 mismatched=0`，
    两侧总字节 **5,055,873,699 == 5,055,873,699** → `VERIFY_godot=PASS`；
  - 工程：`303/303, mismatched=0, 6,029,718 == 6,029,718` → `VERIFY_projects=PASS`。
- **校验全过之后才删源**，删源走 `safe_remove.ps1`：白名单前缀 `H:\rebuild`、先打印清单
  （`FILES 21793 / BYTES 5055873699`，与校验值一致）、无通配符、`-LiteralPath`、需显式 `-Confirm`。
  `H:\rebuild` 现为空。

### 迁移后 A③ 的校验

| 项 | 结果 |
|---|---|
| `git rev-parse HEAD` | `382549f63ead3d511c429b3e213d6ecb74986208` |
| 分支 / origin | `feature/mcp-server-module-rebuild`；`refs/remotes/origin/feature/mcp-server-module-rebuild` **同一 sha** |
| `git status --short` | **空（0 行）** |
| `git fsck --no-progress` | 两侧 **exit 0**，stdout/stderr **逐字节全等**（两边都是 0 字节输出，sha `E3B0C44298FC1C149AFBF4C8996FB92427AE41E4649B934CA495991B7852B855`） |
| 抽查 `modules\mcp_server\docs\tools_list.renamed.json` | 148,141 B，sha `4BE4285CD221A877712370E6A4C73426E0CC7B94C2B6E32D59B3AED69760ED3A`（与迁移前逐字节一致） |
| 抽查 `bin\*.exe` 四个变体 | 300,544 / 193,465,344 / 300,544 / 194,050,560 B，sha 与迁移前**逐个相同** |

### 嵌套 git 处理（本次的重点决策）

1. **引擎树保留自己的 `.git`**（独立克隆，**不并入**主仓、**不做 submodule**）。理由：它是 4.7 GB / 2.18 万文件的
   上游 fork 全历史；submodule 会把「模块补丁的版本」绑到一个仍需单独推送的第二仓库，主仓对它的每次引用都变脆；
   而内核补丁本来就是**引擎的**交付物，应由**引擎仓自己的分支**承担 —— 主仓只需要「知道它在哪、怎么构建」。
2. **主仓 `.gitignore` 忽略 `godot-mcp/godot/`**（整棵），以及各游戏工程的 `.godot/`、`bin/`、`obj/`、`.mono/`、
   `export_presets.cfg`、`godot-mcp/runs/`。
   **`*.import` 故意不忽略**：它是 Godot 的资源 UID 映射，属于工程源码，丢了工程打不开（任务书说「视情况」，这里结论是「不忽略」）。
3. **策略**：**引擎仓**以 fork 分支为准、**每个里程碑 push**；**主仓**只跟踪「模板 + 游戏源码 + 驱动脚本 + 文档」这些**小文件**，
   每段可提交改动即提交，保持 `git status` 干净。
4. `godot-mcp/README.md` 写清布局、两个仓库的关系、构建方式与如何跑试测。
5. TASK-085/086 期的重定向残留（`$null`、`$l`、`%DST%/`）**留档不删**（破坏性命令默认拒绝），
   在 `.gitignore` 里点名忽略，使主仓 `git status` 归零。

---

## D138 — **新目标口径**：轮次不设限、**至少 20 个经典小游戏、全部 C#**，以「可完整溯源操作有效性」为改进基础

用户在本任务（TASK-091）里把目标口径重新定死，取代「把某个游戏做到位就收」的旧读法：

1. **轮次不设限**：不预设「第 N 轮结束」。只要每轮的证据链完整、缺陷有根因、修复有前后对比，就一直做下去，
   直到 20 个游戏全部落地；中途不因「已经跑了很久」而降标准。
2. **至少 20 个经典小游戏**：Pong 是**第 1 个**，随后按同一套脚手架与同一套试测驱动继续
   （贪吃蛇、打砖块、扫雷、俄罗斯方块、2048、太空侵略者、Flappy、双人乒乓、青蛙过河、推箱子、连连看、
   数独、记忆翻牌、弹球、赛车、platformer、卡片配对……按可行性排序）。
3. **全部 C#**（Godot .NET），不再用 GDScript 写游戏逻辑；GDScript 只作为**测试执行器**
   （`running_game_execute_gdscript`）与试测断言语言使用。
4. **改进基础 = 「可完整溯源操作有效性」**：每一个游戏、每一次调用都必须能被台账（`mcp_trace_ledger.py`）判出
   「这次操作到底有没有产生效果」，且证据**可复现、可复算**（像素差、文件 sha、断言、场景树快照），
   **不接受「应该动了」「看起来对」**。判定分布（`verdicts`）与 `facts_complete` 是每款游戏的准入门槛。
5. 由此产生的**工程要求**：脚手架必须可复用（`godot-mcp/projects/_template`）、试测必须有统一驱动
   （`godot-mcp/tools/run_game_session.ps1`）、每款游戏必须产出**每游戏报告**（判定分布 + `facts_complete` + 缺陷清单），
   缺陷「**根因明确的才改，不清楚的只记录**」。

---

## D139 — TASK-091 D 段交付：**可复用 C# 游戏脚手架 + 统一试测驱动 + 第 1 个游戏 Pong**（6 条根因明确的缺陷，5 条修复 + 1 条同类复发，全部重跑对比）

**交付物**（都在 `F:\moonbit-hof-rs\godot-mcp\` 下，主仓跟踪）：

| 件 | 路径 | 说明 |
|---|---|---|
| 工程模板 | `projects\_template\` | Godot .NET 骨架（`Godot.NET.Sdk/4.8.0-dev`、`net8.0`），`NuGet.config` 清空包源只指向引擎自带的 `bin\GodotSharp\Tools\nupkgs` → **离线 `dotnet build` 成功**（`DOTNET_BUILD_EXIT=0`，输出 `.godot\mono\temp\bin\Debug\pong.dll`）；占位符 `__NAME__` / `__CLASS__` 由 `tools\new_game.ps1` 实例化 |
| 新建/重置 | `tools\new_game.ps1`、`tools\reset_game.ps1` | 前者只生成（目标已存在即拒）；后者是**唯一带删除**的工具：名字必须单段、目标必须恰好是 `<root>\projects\<name>`、先打印清单、需 `-Confirm`、**永不动 `runs\`** |
| 试测驱动 | `tools\run_game_session.ps1` | 起编辑器 9888 + 游戏 9889（`--mcp-trace` + `--mcp-capture=every_call` + `--mcp-capture-viewport=2d`）→ 重放会话（`:9888/:9889` 分相）→ 跑 `mcp_trace_ledger.py` → 跑 `game_report.py` |
| 每游戏报告 | `tools\game_report.py` | 判定分布 + `facts_complete` + **独立复算**的像素差（Pillow 重算每对 PNG，并与 trace 自己报的数逐对比对）+ 缺陷清单（每条给根因） |
| 门运行器 | `tools\run_gates.ps1` | 九道门 + `accept_m1`，每门一个 `cmd` 子进程、退出码在子进程内回显后解析 |
| 第 1 个游戏 | `projects\pong\` | C# Pong：`PongGame.cs` / `Ball.cs` / `Paddle.cs` + `scenes\main.tscn`（9 节点），**整份工程由 MCP 调用写成**（`project_create_script` / `project_edit_script` / `editor_add_nodes_batch` / `editor_set_node_script_batch` / `editor_set_node_property` / `editor_add_input_action` / `editor_save_scene` / `project_build_csharp`） |

会话与调用集：`tools\sessions\pong\session.json`（编辑器 24 条 + 游戏 29 条，C# 载荷在 `payload\`）。
四次运行的产物在 `runs\pong\pong-run{1..4}\`（trace / ledger / 截图 / `report.md` / `report.json`）。

**Pong 的「操作有效性」证据链**（全部可复算，见 `runs\pong\pong-run4\report.md`）：

* 球动了：`PONG_TICK` 球 (392,268) → (666.6,444.5)；`running_game_set_node_property` 各行的截图**独立复算**出 62 / 92 / 120 / 512 / 512 / 96 px 的像素差，且与 trace 自报的数**逐对相等**；
* 板动了：注入 `pong_left_up` ×2 再 `pong_left_down` ×1，`PONG_NUDGE y=96 → 8 → 138`（= `Speed 520 × InjectedStepSeconds 0.25`，两次都被 `MinY=8` 夹住的那次也如实反映）；
* 比分变了：`assert_node_state{ScoreRight.text == "1"} → "2"`，同刻 `PONG_SCORE scored_by=RIGHT … right=1/2`；
* 胜负判了：`WinLabel.text = "GAME OVER - RIGHT WINS 0:2"`，`PONG_OVER winner=RIGHT`，并按该**逐字字符串**断言通过；
* 断言不是橡皮图章：同一批里 **2 条注定失败**的断言（板位置 `eq` → `scenario_assertion_failed`、屏幕文本不存在 → `assertion_failed`）都被台账抓住，另有 3 条场景断言 `scenario_passed` 作正对照（更正：初稿写「3 条」把 run-1 里那两条因 P-1 而偶然失败的比分断言算了进来，run-4 它们是正确的正例）；
* 空转看得见：停球后 `PONG_TICK` 连续 6 次 `v=(0,0)` 位置不动，`running_game_get_node_property_samples` 的 30 帧同样不动。

### 缺陷清单（根因明确的才改）

| # | 层 | 现象与证据 | 根因 | 处置与重跑结果 |
|---|---|---|---|---|
| **P-1** | 游戏设计 | run-1：驱动起完端点还没发第一条调用，比赛已经自己打完 5 分（`PONG_SCORE` ×5）；`g17` 断言 `ScoreRight.text=="1"` 实得 `"3"`，`g20` 期望 `"2"` 实得 `"3"` | `_Ready` 直接发球，而驱动在端口就绪后固定等 6 s，这段无人值守的时间把比分推走了 | **改**：`_Ready` 把球停在中央且 `Velocity=Zero`，只有一条显式发球才开球（会话用注入的 `pong_serve` 发球，顺带把输入路径也走了一遍）。run-4：整个启动窗口 6 次 `PONG_TICK v=(0,0)` 比分 0-0，之后每条比分断言都成立 |
| **P-2** | 游戏逻辑 | run-1：`PONG_OVER winner=LEFT` 而同刻标签是 `GAME OVER - LEFT WINS 3:3` —— 刚得分的是 RIGHT | 胜负用 `_leftScore >= WinScore ? LEFT : RIGHT` 判，即「谁在目标之上」而不是「谁刚越线」；`WinScore` 被中途调小时两者不等价 | **改**：`Score(side)` 只看**刚得分那方**的总分是否达标。run-4：`PONG_OVER winner=RIGHT`、标签 `GAME OVER - RIGHT WINS 0:2`，且按该字符串的断言通过 |
| **P-3** | 驱动（阻塞报告） | run-1：`game_report.py` 退出 2，argparse 报 `unrecognized arguments: (cmd); Out=…; Err=…; Cmdline=…` —— 一个 PSCustomObject 被拼进了命令行 | **PowerShell 变量名大小写不敏感**：引擎句柄 `$script:game` 与参数 `$Game` 是同一个变量，启动游戏相时把 `-Game` 覆盖成了句柄对象 | **改**：句柄改名 `$script:GameProc` / `$script:EditorProc`，并加注释钉住 |
| **P-4** | 驱动生命周期 | `reset_game.ps1` 删 `projects\pong` 失败：`being used by another process`；`Get-Process` 里还留着 `godot.windows.editor.x86_64.mono.exe` | `Stop-Engine` 只杀 `cmd.exe` 的直接子进程（`.console.exe` 启动器），真正的引擎进程是孙进程 | **改**：`taskkill /PID <pid> /T /F` 杀整棵树。run-3/run-4 的重置全部成功，收尾无残留引擎进程 |
| **P-5** | 驱动（P-3 同类复发） | run-3：`report.cmd` 里是 `--game= --run-tag=pong-run3`，报告的「Saved frames」指向 `…\app_userdata\`（少了 `pong`） | P-3 只改了函数内的句柄名，**开头那两行 `$editor = $null` / `$game = $null` 没删**，`$game` 依旧把 `-Game` 清空 | **改**：删掉那两行并写明原因。run-4：`report.cmd` 是 `--game=pong`，user 目录正确 |
| **P-6** | 驱动引号 | run-3：`import: exit 1`，stderr 是 cmd 的 `The filename, directory name, or volume label syntax is incorrect.` —— 而三个路径都是对的 | `Start-Process` 把内层 `"` 转义成 `\"` 交给原生命令行，cmd 不按 PowerShell 的意思读它 | **改**：ledger / report / import 一律**生成 `.cmd` 文件再跑**（文件里没有引号游戏）。run-4：`import: exit 0`、`ledger exit 0`、`report: exit 0` |

**模块侧零缺陷**：编辑器端点在 run-1 / run-2 / run-4 的判定分布**逐项相同**
（`ok_effect_observed=3, ok_effect_unavailable=1, ok_file_effect_observed=10, ok_no_effect_observed=9`；
run-4 因 `user://pong-editor.png` 与上一轮逐字节相同而多一条 `unchanged`，见下），
游戏端的 `facts_complete` 缺口全部是引擎自己写明的 `not_tracked_deferred`（deferred / 压力 / 逐帧采样），
没有一条「丢失的证据」。**TASK-091 未改动 `modules/mcp_server` 的任何字节**，因此不需要重建引擎。

**两次独立的重跑证据**（同一批调用、同一开关、工程每次先 `reset_game.ps1` 复位）：

| 轮 | 二进制锚点 | 编辑器台账 | 游戏台账 | 关键差异 |
|---|---|---|---|---|
| run-1（修前） | 8604fcf9e | 23 调用，判定分布见上 | 28 调用；`ok_effect_observed=8` | 比分被启动窗口推走；`winner=LEFT 3:3`；报告工具退出 2 |
| run-2（P-1/P-2/P-3 修后） | 同上 | **与 run-1 逐项相同** | 29 调用；`ok_effect_observed=5, ok_file_effect_observed=10` | 比分 0:2 确定；`winner=RIGHT`；报告仍因 P-5 失败 |
| run-3（+P-4/P-6） | 同上 | 与 run-1 逐项相同 | 29 调用；`changed=6, **unchanged=4**` | 4 个截图与 run-2 **逐字节相同** → 会话可复现；报告因 P-5 空 `--game` |
| run-4（+P-5） | 同上 | `changed=9, unchanged=1` | 29 调用；`ok_effect_observed=6, ok_file_effect_observed=9` | `import/ledger/report` 全部 exit 0；`report.cmd` 里 `--game=pong` |

`unchanged` 不是「没写盘」，而是**写下去的字节与上一轮完全相同**——这本身是确定性会话的正面证据。

**九道门**（`runs\gates\task091\`，第 10 条为 `accept_m1`）：
g01 `150/150 passed / 6510 assertions`、g02 `1576/1576 passed / 3 skipped / 430823 assertions`、
g03 `TOOL-GROUPS CHECK PASS`、g04 `3/3 checks passed`（9888=154 工具、9889=73 工具、9877 守卫）、
g05 `RESULT: PASS`、g06 `TAUTOLOGY CHECK PASS`、g07 `PROBES: 10/10`、g08 `RESULT: PASS`、
g09 `ANCHOR_JUDGE RESULT PASS`（`ANCHOR_STRUCTURAL_EQUIVALENT`，二进制自报 `8604fcf9e`、HEAD `382549f63e`，
差异 2 个 `.md`、`RED_COUNT=0`）、g10 `accept_m1` **22/22**。**全部 exit 0**。

**遗留（如实）**：①Pong 只有一局、一次会话；20 个游戏的口径（D138）刚起步；
②`running_game_get_node_property_samples` 报 `scene_evidence=unavailable`，这是引擎声明的边界；
③`project_edit_script` 的 trace 行 `args_truncated=true`（9464 B），是 trace 自己的字节上限，不是丢证据；
④报告里的 `recomputed px` 用的是引擎的规则 `max(|dr|,|dg|,|db|) > 10`，与 trace 自报的数逐对相等，但「任意差异」口径会更大（TASK-090 已记录同一现象）。

## D140 — TASK-092（A 段）恢复档案迁回本项目 + 三条溯源缺口的处置决策（B 段设计）

TASK-092 A 段把 `C:\Users\wyl\AppData\Local\Temp\mcp-recovery\` 整体迁进
`godot-mcp\recovery\`；B 段把 MCP-TRACEABILITY 里剩下的三条缺口一次收口，决策在此落笔。

**A：迁移（先复制 → 逐文件 sha → 才删源）**

* 源 33,433 文件 / 2,520,301,348 B；目标同一批文件**逐文件 SHA-256 全等**：
  `compared=33433 mismatched=0 size_mismatch=0 missing_in_dst=0 extra_in_dst=0`，
  两侧字节数**精确相等**（`VERIFY_RECOVERY=PASS`，`recovery\work\task092\logs\verify.txt`）。
  路径最长超过 260 字符，所以两侧都用 `Directory::EnumerateFiles` + `\\?\` 前缀 + .NET 直读
  （`Get-ChildItem` 会静默漏掉长路径——TASK-091 已经踩过一次）。
  校验全过之后才删 C: 源（白名单前缀 + 先打印清单 + 无通配符 + `-LiteralPath`）。
* 目标结构：根级 23 个 `.md` → `recovery\reports\`，其余顶层目录原样保留
  （`logs\ work\ staging\ transcripts\ rebuild\ backup\ scripts\ tmp\`）。
* **入库分界线**（`.gitignore` 的 TASK-092 段，README §8 有同一份清单）：
  入库 = 2,436 文件 / 75.6 MB（报告、manifest、`work\` 下的脚本与实测产物、`rebuild\` 的补丁与
  低置信清单）；忽略 = 约 31,000 文件 / 2.44 GB（`transcripts\ staging\ logs\ tmp\ backup\`、
  `rebuild\godot\`（**重建期的引擎树旧副本**，与铁律 4 同性质）、`work\events-*.jsonl` 等原始料）。
  **忽略不等于丢失**：文件留在盘上，只是不进 git 历史。
* 迁移脚本、两侧清单与 robocopy 日志留在 `recovery\work\task092\`（证据随档案走）。

**B：三条缺口的处置（选型与否决理由）**

| 缺口 | 考虑过的选项 | 最终选择 | 理由 |
|---|---|---|---|
| **① `args_truncated`（9464 B 的参数无法复核）** | (a) 提高 `max_args_bytes` 上限；(b) 把参数整份入 trace、取消上限；(c) 超限载荷写**旁路文件**并在行上记路径 + sha256 + 字节数 | **(c)** | (a) 只是把墙往后挪，任何固定上限都会再被撞到，且大参数会把 trace 变成项目副本；(b) 去掉上限等于让一个调试旁路通道吃掉主路径的 I/O 与磁盘；(c) 把「裁断」变成**可核的事实**：行上仍有前缀与真实字节数（旧读者不受影响），完整载荷可读、可重算 hash。**同一机制覆盖三个有界载荷**（`args` / `result_json` / `error_data_json`），不另造第二套 |
| **① 的判据** | (a) 行上有 `args_sidecar` 就算完整；(b) 台账**读盘重算** sha256 与字节数 | **(b)** | (a) 是「它说写了就写了」，与 D94 抓到的「无条件回显」同类。台账 `sidecar_of()` 自己打开文件、重算 hash、重量大小，只有三者全对才是 `sidecar_verified`；`sidecar_mismatch` 给出实际值。`relative_path` 相对 trace 目录，所以 trace 换机器后仍可核 |
| **② `not_tracked_deferred`** | (a) 保持声明、只在文档写清；(b) 让延迟调用在**完成时**补齐文件侧与画面侧证据 | **(b)** | (a) 等于把「场景/压力这两个工具的答案就是判定」这句话的理解权交给读者；(b) 代码上**不是新机制**：文件侧复用 TASK-089 的 `MutationScope`（开在 `Queue::tick()` 这个任务真正运行的地方，跨帧累计），画面侧复用 TASK-044 的 `Engine::arm/finish`（`before` 在请求帧、`finish` 移到完成帧）。只剩一条**命名**边界：deadline 在第一次 tick 之前就到 → `not_tracked_deferred`；而「看过但没落盘」明确写 `no_mutation`，两者不再混同 |
| **② 的代价** | (a) 每帧开一次 scope；(b) 忽略 | **(a)** | trace 关时一个 scope 都不开（与立即调用同一条件）；trace 开时每次 tick 多一对方括号 + 每帧一次 `begin/end`，无分配。在飞的延迟调用会多持有一帧 framebuffer 拷贝（数量上界 = pending 表上界），连接断开时由 `Engine::discard()` 显式释放 |
| **③ 两个缺失的 doctest** | (a) 继续用「第 8 轮 trace 实测钉住」；(b) 补 doctest | **(b)** | `in_input_map`（动作已声明 / 未声明两种）由 `[MCPServer]` 用例自建 `InputMap` 驱动；`_tick_pending` 的 `result_json` 需要真实传输层，所以用例**开一个环回 socket**（与 `tests/core/io/test_tcp_server.cpp` 同一套等待惯用法）。另外把 B1/B2 的新契约也各补一条 doctest（sidecar 与延迟窗口），否则新能力只有文档没有回归网 |
| **④ `_frame_cost_ms` 用瞬时帧率** | (a) 保留 `Engine::get_frames_per_second()`；(b) 用 `Performance` 的最近一帧；(c) 自建**最近 N 帧中位数**窗口 | **(c)** | (a) 的读数**一秒才更新一次**，一次卡顿被接下来整整一秒的 deadline 继承（实测同一场景两个实例 `4396` / `1150`）；(b) 同样是瞬间值；(c) 采样点本来就有——`MCPServer::pump_frame` 每帧都跑，一次 `get_ticks_usec()`。窗口 15 帧、中位数、截断到整毫秒、夹 [16, 1000]，**60 fps 下与旧常量逐字相同**（16667 µs → 16 ms），行为对快进程零变化 |
| **⑤ 重建** | (a) 只重建 mono；(b) 两个变体都重建 | **(b)** | 契约描述与测试都改了，`accept_m1` 的 case12 会逐字比对 `tools_list.renamed.json`；TASK-090 已经证明只重建一个变体会得到 21/22 |

**读法落文档**：`modules/mcp_server/docs/reports/MCP-TRACEABILITY.md` 新增 §2.6（sidecar 字段与
成本）、§2.7（延迟调用的两侧证据与边界表）、§3.1（`args_evidence` 六种取值 → `args_complete`）、
§6（帧代价取值规则表）；`godot-mcp\README.md` §8 是恢复档案的内容与忽略策略，§4.3 指向上述读法。

**回滚点**：A 段是文件位移，回滚 = 反向复制（源已删，但目标是一份逐文件校验过的完整副本）；
B 段每个缺口一个提交，任一条都可单独 `git revert`，且都不改 `tools_list` 契约（`inputSchema`
与 description 一字未动）。

> 结果（门、Pong 重跑、facts_complete 前后对比、提交与 push）在 B 段实现与验收完成后追加为 D141。

