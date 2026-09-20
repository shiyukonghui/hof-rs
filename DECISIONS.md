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
