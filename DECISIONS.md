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


