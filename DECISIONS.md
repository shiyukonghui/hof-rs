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






