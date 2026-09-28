# TASK-DR41（批次一）— hof-rs 引擎换代：拆除 GDExtension 通道 + 工具契约迁移 + 双端点 + 引擎身份入库

> 你是一个**没有上游对话上下文**的实现子代理。本文件是你的**唯一任务来源**；
> 需要的事实、路径、判据都在这里。凡本文件未授权的事，一律不做。
> **本批次是纯离线批次：不启动 Godot、不碰端口、不联网、不调模型。**

---

## 0. 一句话目标

把 hof-rs 的工具层从**旧的 GDExtension 插件契约（174 条无前缀名）**迁移到**我们自建引擎的原生模块契约
（177 条四通道前缀名）**，并拆除旧插件通道、补上引擎身份取证。**判据是 `cargo test` 全绿**，
不是"看起来改完了"。

---

## 1. 必须先用只读方式读的文件（按顺序）

| 顺序 | 路径 | 看什么 |
|---|---|---|
| 1 | `.spec/hof-rs/DESIGN-DETAIL.md` **§13（文件末尾）** | **本次的权威设计条款 DR-41..DR-46**。与 §1–§12 冲突处以 §13 为准 |
| 2 | `.spec/hof-rs/REQUIREMENTS.md` **§3 C3/C4/C5 + §10** | 需求侧的新硬约束与"契约断层"的事实列账 |
| 3 | `DECISIONS.md` **文件末尾 D216** | 决策与两条硬约束（PRD 不改、旧词汇归零） |
| 4 | `godot-mcp/godot/modules/mcp_server/docs/tool-rename-map.json` | **改名唯一事实源**（174 条） |
| 5 | `godot-mcp/godot/modules/mcp_server/docs/tools_list.renamed.json` | **新的线上契约**（177 条，含 `inputSchema`） |
| 6 | `godot-mcp/recovery/TEST-CASES.md` | 177 条 `TC-TOOL-*`：逐工具的输入/输出形式与反例（查语义变化时用） |
| 7 | `src/adapter/godot.rs`（全文，约 3186 行） | 主战场：`PROJECT_GODOT`、`initialize`、`ensure_plugin_enabled`、`doctor`、证据电池全套 `step_*`、角色工具作用域 |
| 8 | `src/tools/{index,policy,mcp,reliable}.rs`、`src/runtime/policy.rs` | 工具索引/作用域/调用/就绪轮询 |
| 9 | `config/hoh.yaml`、`src/config.rs` | 配置面（`adapter.godot.*`、`tools.*`） |

**只读**：以上文件除第 7/8/9 项中本任务明确要改的部分外，一概只读。

---

## 2. 已给定的环境事实（不要再花时间重新发现）

- 引擎二进制（mono 构建）：`F:\moonbit-hof-rs\godot-mcp\godot\bin\godot.windows.editor.x86_64.mono.exe`
  （另有非 mono 版 `godot.windows.editor.x86_64.exe` 与各自 `.console.exe`；本次只用 **mono**）。
- 实测版本串：`4.8.dev.mono.custom_build.ba1587c71`（构建于 anchor `ba1587c71`）。
- 旧契约 = 当前 `tests/fixtures/mcp/tools_list.json`：**174 条**、无前缀（`play_scene`、`get_editor_errors`…）。
- 新契约 = `tools_list.renamed.json`：**177 条**、前缀 ∈ {`editor_`, `project_`, `running_game_`, `os_`}。
  旧名在新契约里**全部不存在**（已双向核对）。
- 引擎默认编辑器端口 9877（在 `modules/mcp_server/mcp_server.cpp:53`）；
  **游戏进程是独立端点**，由 `editor_play_scene` 注入 `--mcp-port` 决定。
- M 线实测端点切分：「editor 148 / game 69，game-only 23」——即**有 23 个工具只在游戏端点可达**。
- 仓内旧词汇耦合规模（实测）：`src/adapter/godot.rs` 97 处、`tests/evidence_battery.rs` 40 处，全仓约 270 行 / 24 文件。
- 外层仓的 `python/` 与 `tools/` 是**空目录**；`godot-mcp/**` 是**嵌套仓库**（本次禁改）。

---

## 3. 硬约束与禁项（违反任一条即任务失败）

1. **不保留兼容别名层**：全仓只允许存在一套工具词汇（四通道前缀）。禁止"旧名仍可用"、禁止映射垫片。
2. **`PRD-mario.md` 一字不改**。它是冻结的规格 S；改它会使 `meta.json.spec.sha256` 变化（违约）。
   跑完必须核对：`sha256(.spec/hof-rs/PRD-mario.md) == 4c81c3a9995f0b3afdf01421a0c3be88573cceefc284ce9bafbfda141f0f5c3a`。
3. **不改 `godot-mcp/**`**（引擎侧已冻结；其中 `godot/` 还是独立仓库）。只**读**它的 `docs/`。
4. **不启动 Godot、不占用/探测 9877 或任何端口、不访问网络、不调用模型端点**（本批次纯离线）。
5. **不引入新依赖**（不得改 `Cargo.toml` 的 `[dependencies]`）。
6. **不得臆造能力**：若 hof-rs 用到的某项能力在新契约里**没有**对应工具，**停下并在报告里列为 BLOCKER**
   （`旧名 / 无对应 / 影响哪条判据`），不要用别的工具"凑一个近似行为"。
7. **不得删除或放宽既有测试来换绿**。允许改工具名、改夹具、改断言文本以匹配新契约，
   但每个被改的断言必须在报告里说明"为什么语义等价"。
8. 不 `push`；只在外层仓提交。

---

## 4. 要做的事（六块，逐块给判据）

### 4.1 DR-41 —— 拆除 GDExtension 通道

1. `PROJECT_GODOT` 模板：删掉 `[editor_plugins]` 段（含其下 `enabled=PackedStringArray(...)` 行）；
   `config/features` 由 `PackedStringArray("4.7")` 改为 `PackedStringArray("4.8")`。
2. `initialize()` 新工作区分支：**不再**复制 `addon_source`；**不再**写 `ADDON_MISSING.txt`。
3. `initialize()` **既有**工作区分支（当前 `.workspace/mario` 就是这种）：必须反向清理，且**幂等**：
   - 删 `<ws>/addons/godot_mcp_rs/`（仅此精确路径；不存在则跳过）；
   - 若 `<ws>/.godot/extension_list.cfg` 含 `res://addons/godot_mcp_rs/godot_mcp_rs.gdextension`，
     移除该行、其余行**逐字保留**；若因此变空则删掉该文件；
   - 从 `project.godot` 的 `[editor_plugins] → enabled=PackedStringArray(...)` 中移除
     `res://addons/godot_mcp_rs/plugin.cfg`，**列表中其它插件名逐字不变**；列表变空则整段移除；
     无该段/无该项时文件**逐字节不改**。
4. `ensure_plugin_enabled`（现 2438–2490 行）反转为 `ensure_bundled_addon_disabled`，保留"已满足即不触碰文件"的幂等性质。
5. 配置：删除 `adapter.godot.addon_source`（结构体字段 + `config/hoh.yaml` 行）；
   `grep -rn addon_source src tests config` 必须 **0 命中**。

**判据**：①新工程模板不含 `[editor_plugins]`；②既有工程的清理幂等（连跑两次第二次不改文件，用字节比较断言）；
③`addon_source` 0 命中；④`cargo test` 中与 `PROJECT_GODOT`/`initialize` 相关的既有测试全部按新语义更新并绿。

### 4.2 DR-42 —— 契约换代与夹具重采

1. 重采 `tests/fixtures/mcp/tools_list.json`：内容 = 177 条新契约（UTF-8 **无 BOM**）。
   批次一以**仓库内** `godot-mcp/godot/modules/mcp_server/docs/tools_list.renamed.json` 为源
   （活体核对留给批次二）。**注意**：源文件是 `tools/list` 的**结果对象**还是完整 JSON-RPC 响应，
   要看清结构后决定落盘形态——但**外层 `tools_list.json` 的既有结构（被现有代码解析的形态）必须被保持**，
   只换工具名与 schema。若两者结构不同，以**现有代码能解析**为准，并在报告里写明你怎么对齐的。
2. 新增 `tests/fixtures/mcp/PROVENANCE.md`：记录来源路径、源文件 sha256、落盘后 sha256、条数（177）、
   以及一句"**活体 `tools/list` 逐字核对留给批次二**"。
3. 逐条迁移旧名：先输出**映射表**（`旧名 → 新名 → 作用域 → 语义是否变化 → 依据`），
   再按表改 `src/**`、`tests/**`、`src/prompts/**`。
   **必须查表，禁止正则批量替换**（GDR-17 取消 2 对合并产生拆分、`update_` 被禁改名）。
   映射表必须进报告。
4. 角色工具作用域（`src/runtime/policy.rs`、`src/tools/policy.rs`、`src/adapter/godot.rs` 约 2690–2730 行）
   按四通道 + 只读动词集重写：
   - Planner：**只读**（仅允许只读类动词通道）；
   - Developer：写 + 执行（含 `editor_*`/`project_*` 写工具）；
   - Tester/QA：只读 + 执行/断言，**不得**有任何改产物的工具（R13）。

**判据**：①夹具 177 条且每条匹配 `^(editor|project|running_game|os)_[a-z0-9_]+$`；
②`tool_allowed(Planner, <任何写工具>) == false` 有测试；③`tool_allowed(QA, <任何写工具>) == false` 有测试。

### 4.3 DR-43 —— 双端点路由

新契约下 `running_game_*` **只在游戏端点**可达，编辑器端点（9877）不提供它们。

1. `src/tools/` 支持**按工具作用域路由端点**：`editor_*`/`project_*`/`os_*` → 编辑器端点；
   `running_game_*` → 游戏端点。
2. `step_play_scene` 必须从 `editor_play_scene` 的响应里解析并登记游戏端点
   （优先 `endpoint` 字段；否则由 `mcp_port` 拼 `http://127.0.0.1:<port>/mcp`），并记录其来源
   （`mcp_port_source` ∈ `argument`/`auto_free_port`）。**登记失败 ⇒ 该步失败**，
   **禁止**静默回退到编辑器端点。
3. `stop_scene` 之后游戏端点失效：后续 `running_game_*` 调用必须**报错**，不得打到旧端口。
4. 端点信息要能进 `meta.json`（见 4.4 的字段契约）。

**判据（离线，用假 MCP）**：①构造**双端点假 MCP**，断言 `running_game_*` 只出现在游戏端点收到的请求里，
且编辑器端点**从未**收到任何 `running_game_*`；②`editor_play_scene` 未返回端口时该步判定失败；
③`stop_scene` 后 `running_game_*` 报错（不是发出请求）。

### 4.4 DR-44 —— 引擎身份入库

1. 配置新增 `adapter.godot.editor_binary`（绝对路径）；`config/hoh.yaml` 填 mono 构建路径（见 §2）。
2. `hof doctor` 两项：
   - `godot.engine_binary`：`ok` = 路径存在；`detail` = 路径 + size + mtime；
   - `godot.engine_version`：`ok` = `<binary> --version` 退出码 0；`detail` = **版本串逐字**。
   **版本串不得写成代码常量、不得作为判据**（C12：换版本不许要求改 `src/**`）。
3. `meta.json` 新增 `engine` 块，字段契约**固定**：

```json
"engine": {
  "kind": "godot",
  "binary": { "path": "...", "size_bytes": 0, "mtime_unix": 0, "sha256": "..." },
  "version_string": "4.8.dev.mono.custom_build.ba1587c71",
  "mcp": { "editor_endpoint": "http://127.0.0.1:9877/mcp", "game_endpoint": null,
           "editor_status": { } },
  "listener": { "pid": 0, "path": "...", "matches_binary": true, "reason": null },
  "checked_at": 0
}
```

   取不到的值必须显式 `null` **并**在同级给 `reason`（参照 R12 的 usage-unknown 纪律）；
   **不得省略字段、不得编造**。
4. `listener.matches_binary`：经**既有 `Environment` 抽象**跑一条 Windows 探针（端口 → PID → 可执行体路径），
   与 `editor_binary`（规范化绝对路径、大小写不敏感）比较。**不新增 crate 依赖**。
5. 可启动闸门（现 `GATE_STEP_IDS` 附近）新增步骤 id `engine_identity`：
   `matches_binary == false` ⇒ 闸门失败，错误信息必须同列「配置的二进制 / 实际监听者路径 / PID」。
6. `secret_hygiene` 类测试必须覆盖 `engine` 新键（不得出现密钥明文）。

**判据**：①用假 MCP/假 Environment 构造匹配与不匹配两种情形，断言闸门行为；
②`meta.json` 的 `engine` 块在字段缺失时写 `null` + `reason`（有测试）；
③现有 `meta.json` 相关测试全部按新结构更新并绿。

### 4.5 DR-45 —— 旧词汇归零（迁移完成的机器判据）

新增 `tests/tool_vocabulary.rs`，三条**必须同时绿**：
1. 夹具里每条 `name` 匹配 `^(editor|project|running_game|os)_[a-z0-9_]+$`；
2. `src/**`、`tests/**`、`src/prompts/**` 中**不存在任何不在夹具里的工具名**（旧词汇为 0）；
3. 反向：代码里被调用的**每个**工具名都**必须**在夹具里存在。

> 提示：第 2 条的"工具名"判定要写得稳（例如从夹具名集合反查 + 对 `"..."`/`tools call <name>` 等形态扫描），
> 并在报告里写明你如何避免误报（例如不要把函数名/变量名当成工具名）。**误报和漏报都要说明**。

### 4.6 DR-46 —— 批次禁项自查

提交前自证：没有启动 Godot、没有占用/探测端口、没有联网、没有改 `godot-mcp/**`、
没有改 `PRD-mario.md`、没有加依赖。自查方式要写进报告（例如 `git status`/`git diff --stat` 的真实输出）。

---

## 5. TDD 要求（强制，逐块执行）

对每一块（4.1–4.5）：

1. **红**：先写/改**最小**的失败测试，运行并**确认它是因为缺行为而失败**（把真实失败输出记进报告）。
2. **绿**：写**最小**实现让它通过。
3. **重构**：在全绿下整理代码（命名、提取函数），每步之间**都跑测试套件**。
4. **不许长期红**：任何时刻不得留下未跑或长期红色的套件。
5. 测试是**可执行的需求文档**：断言要写"为什么"（注释里引 DR 编号），不要写"实现恰好如此"。

命令：`cargo test`（离线）。若存在需要真实依赖、被 `#[ignore]` 或被环境变量门控的测试，
**如实列出**它们与其门控方式，不要偷偷删掉。至少必须做到：`cargo test` 全绿、
`cargo build` 无警告增量（或如实列出既有警告）。

---

## 6. 提交要求

- 只提交**外层仓**（`F:\moonbit-hof-rs`）。提交信息英文、形如
  `adapter: drop the bundled GDExtension addon and its stale extension cache (DR-41)`
  ——**每条提交信息必须带 DR 编号**，与 `DECISIONS.md` D216 互查。
- 建议按 DR 拆成 4–6 个提交（DR-41 / DR-42 / DR-43 / DR-44 / DR-45 / 文档），便于回滚。
- **不要**把 `runs/**`、`.workspace/**`、`config/*.secret*` 加进提交。
- **不要** `push`。

---

## 7. 完成后的回报格式（**只返回报告文件路径**）

把报告写到：`.spec/hof-rs/tasks/TASK-DR41-REPORT.md`

报告必须含以下小节（缺一节视为未完成）：

1. **结论**：做完了什么 / 未做什么 / 是否全绿（附 `cargo test` 的**真实输出尾部**与退出码）。
2. **逐条判据对照**：§4.1–4.5 每条判据 → 证据（命令 + 真实输出片段 + 文件:行号）。
3. **旧名→新名映射表**（§4.2 第 3 项要求）：完整 174/177 相关条目，含作用域与语义变化。
4. **BLOCKER 清单**：无对应工具的能力（若有），以及影响哪条判据。**没有就写"无"**，不要省略本节。
5. **被我修改的既有断言**：逐条列出"原断言 / 新断言 / 为什么语义等价"（§3.7 要求）。
6. **禁区自查**：§4.6 的真实输出。
7. **遗留风险与不确定项**：例如"夹具结构对齐方式""DP-45 扫描的误报边界""活体核对尚未做"。
8. **诚实披露**：过程中任何返工、猜错、绕过尝试都要写；**不许把推断写成实测**。

**回报给我（父代理）的内容只有一行：报告文件路径。** 不要粘贴大段输出。
