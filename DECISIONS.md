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