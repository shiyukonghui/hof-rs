# TASK-DR48-FIX — 批次二缺陷修复包（DR-48..DR-53）

> 你是**实现子代理**，没有上游对话上下文；本文件是你的唯一任务来源。
> 落点：`F:\moonbit-hof-rs`（外层仓 `master`）。
> **本批是纯离线批**：不启动 Godot、不碰任何端口（9877 上正跑着我们的编辑器，PID 108432，**绝不许动**）、
> 不联网、不调用任何模型端点。

---

## 1. 必读（按顺序）

| # | 路径 | 读什么 |
|---|---|---|
| 1 | `.spec/hof-rs/DESIGN-DETAIL.md` **§14（文件末尾前）** | **本批的权威设计条款 DR-48..DR-53**（与 §13 冲突处以 §14 为准） |
| 2 | `DECISIONS.md` 末尾 **D220**、**D221** | 裁决与修复包定义；D221 是权威裁决表 |
| 3 | `.spec/hof-rs/tasks/TASK-DR47-ACCEPTANCE.md` | **逐条取证（文件:行 + 原始输出）**，尤其在 `godot.rs`/`engine_identity.rs`/`run_loop.rs` 的定位 |
| 4 | `.spec/hof-rs/tasks/TASK-DR47-SMOKE-REPORT.md` | 执行者视角的 6 条缺陷描述（含复现步骤） |
| 5 | `runs/smoke-t6/**` | 真机原始证据（**只读**；`result.json` / `battery*` / `deterministic*` / `raw/**` / `meta.json`） |
| 6 | `godot-mcp/recovery/TEST-CASES.md` | 177 条 `TC-TOOL-*`：逐工具**输入/输出形式**（DR-52 的参数形状核对基准） |

> `godot-mcp/**` **只读**；`runs/smoke-t6/**` **只读且不得改写**（换代后基线）。

---

## 2. 要做的事

### DR-48 —— 可启动闸门假阴性（major，决定 E2）
现况：引擎的**信息横幅** `[MCP] capture=off (default; use --mcp-capture=on_error|every_call …)` 出现在
`editor_get_errors.errors` 里（引擎侧 `editor_read_scene_inspector.cpp:249` 用
`to_upper().contains("ERROR")` 过滤日志行 ⇒ 只有含 `on_error` 的这行命中），hof-rs 的
`editor_errors_baseline`（`src/adapter/godot.rs:783-796`）见非空 `errors` 即判"编辑器不干净"
⇒ 闸门假阴性、exit 6、白烧 60 步修复重试。

**要求（硬）**：
1. 只豁免**引擎信息横幅的确切形态**；把它做成**常量数据 + 一个具名匹配函数**，不得散落特例 `if`。
2. **禁止**按 `[MCP]` 前缀豁免 —— 引擎也会打印
   `ERROR: [MCP] SceneTree never became available; MCP server disabled.`（真错误）。
3. **未命中即按原语义**判"不干净"（保守）。
4. **必须**有反例测试：注入真实 `ERROR:` / `SCRIPT ERROR` 行后闸门**仍失败**；
   并有一条测试证明"恰好那两类横幅被豁免"。

### DR-49 —— 截图证据必须"本轮真实"（major，DEF-B + DEF-F）
现况：`running_game_capture_screenshot` 的 `save_path` 只收 `res://`/`user://`
（引擎 `running_game_capture.cpp:62-63`），而 hof-rs 传**文件系统绝对路径**（`godot.rs:1042-1048`）
⇒ 三次 `-32602`；该步仍被判 `ok=true`，**只因为**该路径上早躺着一张 2026-09-21 的旧 PNG
（`godot.rs:1109-1124` 用 `is_file()`）；且该旧文件**还压制了 `capture_frames` 回退**（`godot.rs:1081`）。

**要求（硬）**：
1. 调用形态改为契约允许的 `user://`（或把内联图像落地），**不得**传文件系统绝对路径。
2. **调用前作废目标路径上的既有文件**（删除或改名到 `*.stale-<ts>`），使"存在即 ok"**无法伪造**。
3. 步骤 `ok` 必须基于**新鲜度**（本次调用后新生成 / hash 变化 / mtime ≥ 调用前），**不得**仅 `is_file()`。
4. 修掉"旧文件压制 `capture_frames` 回退"。
5. **必须**有反例测试：放一张旧文件在目标路径上，断言步骤**不会**因此判成功。

### DR-50 —— 游戏端点挂死：**先定性，后修复**（major，决定 E3）
现况：`editor_play_scene` 成功、首个 `running_game_get_scene_tree` 成功（50 节点），随后
`running_game_execute_gdscript` **第 5 次**挂死（一次逻辑调用 ×3 重试 ⇒ `os 10060`）→ 之后 `os 10061`；
**两轮可复现**（65333/109964、63698/101872）。根因**未定**。

**要求（硬）**：
1. **第一步只做定性**：只读、**可复现**地表征"**引擎侧挂死** vs **hof-rs 调用形态**"，
   产出**判据 + 原始输出**（不得只说结论）。可用 `runs/smoke-t6` 的原始记录；
   若需活体复现，**只能**经一次真实的 `editor_play_scene`（会占用编辑器），且必须记录并清理。
2. **禁止**修改 `godot-mcp/**`。
3. **若定性为引擎缺陷 ⇒ 停下并上报**（把它作为 BLOCKER 写进报告），并**只在 hof-rs 侧**给出
   **不改引擎**的绕行方案（例如改用逐帧采样类工具替代长时 `execute_gdscript`）。
   **定性未完成前不得"修"**。

### DR-51 —— 端点身份必须真正持久化（moderate，DEF-D）
现况：`engine.mcp.editor_status` 被**硬写** `Value::Null`（`src/adapter/engine_identity.rs` 附近）⇒ **永不填充**；
`game_endpoint` 的回写（`run_loop.rs:787-793`）发生在电池**之后**，而电池的 `editor_stop_scene`
已清掉注册（`godot.rs:1887-1888`），pass2 后无回写 ⇒ **两个字段结构性永远为空**。

**要求**：`editor_status` 用**真实 `GET /mcp` 响应体**填充；`game_endpoint` 在**登记当刻**回写；
缺值仍守 §13.4 的 `null` + `reason` 契约。**必须**有测试覆盖"有端点时字段被填上"。

### DR-52 —— 诊断自洽 + 参数形状核对（DEF-E + 漏迁面）
1. 诊断文本必须与**自己的原始记录**一致：`deterministic.json` 声称"编辑器 InputMap 不含
   move_left/move_right/jump"，而它自己记录的 `editor_get_input_actions` 返回 **92 个动作且前三正是它们**。
2. 以 `TEST-CASES.md` 的 177 条 `TC-TOOL-*` 为准，**逐工具核对 hof-rs 的调用参数形状**
   （必填/可选/默认/取值域）。逐条列出"工具 / 契约形状 / hof-rs 现状 / 是否一致 / 处理"，
   不一致的按契约改正并留测试。**这是 DR-42 只做改名所漏掉的迁移面。**

### DR-53 —— 批次一遗留 minor
1. 畸形 `enabled=`（无括号）：**不得改动文件**，须写 reason（现被解释为"列表变空 ⇒ 删整段"）。
2. 补两条回归测试：`mcp_port_source` 的 `undeclared` 分支、`engine_identity` 在 `None` 时关闸。
3. `the_snapshot_is_the_real_174_tool_list`（`src/tools/index.rs:260`）改名并收紧断言（夹具 177 条）。

---

## 3. TDD 与纪律

- 逐 DR 执行**红-绿-重构**：先写会失败的最小测试并**确认它因缺行为而失败**（记真实输出），
  再写最小实现，最后在全绿下重构。**不许**长期红，**不许**删/放宽既有测试换绿。
- `cargo test --offline` 必须全绿（列出 `#[ignore]`/环境门控项与其门控方式）。
- 不新增依赖；不改 `godot-mcp/**`、`.spec/hof-rs/PRD-mario.md`（跑完 `sha256` 必须仍是 `4c81c3a9…5c3a`）；
  不 `push`；不 stage `runs/**`、`.workspace/**`、`config/*.secret*`；逐条提交、信息带 DR 编号。
- **DR-42/DR-47 语义保持**：DR-45 的"旧词汇归零"守卫必须仍然全绿。

---

## 4. 回报（**只回报报告文件路径**）

报告写到 `.spec/hof-rs/tasks/TASK-DR48-REPORT.md`，必含：

1. **结论** + `cargo test --offline` 真实输出尾部与退出码；
2. 逐 DR 的判据对照（命令 → 真实输出 → 文件:行）；
3. **DR-52 的完整参数形状核对表**；
4. **DR-50 的定性结论**（判据 + 原始输出 + 你的定性与置信度；若为引擎缺陷则明确写出"BLOCKER + 上报"，
   并给出 hof-rs 侧绕行方案）；
5. 被修改的既有断言：逐条"原断言 / 新断言 / 为什么语义等价"；
6. 禁区自查（未启动 Godot、未碰端口、未联网、未改 `godot-mcp/**`、未改 PRD、无新依赖、未 push）真实输出；
7. 遗留风险与**未验证项**（区分「实测」与「推断」）；
8. 诚实披露（返工、猜错、绕过尝试）。

**回报给父代理只有一行：报告文件路径。**
