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





