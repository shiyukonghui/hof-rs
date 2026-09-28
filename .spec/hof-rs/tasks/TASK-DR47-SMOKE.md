# TASK-DR47-SMOKE — 批次二：真机 T=1 冒烟（在我们的 MCP 原生构建上）

> 你是**批次二的执行子代理**。你**没有**上游对话上下文；本文件是你唯一任务来源。
> 落点：`F:\moonbit-hof-rs`（外层仓，分支 `master`）。设计依据：`.spec/hof-rs/DESIGN-DETAIL.md` **§13（DR-43/DR-47）**。
> 前置：**编辑器已由调度者启动**（见 §1）。你不是启动者，**不得**重启、杀死或抢占它。

---

## 0. 一句话目标

在**我们自建的 mono 引擎构建**上（编辑器端点 9877）跑通一轮真实 **T=1** 的
`Planner → Developer → QA` 循环，并留下**可复核**的证据包；同时完成批次一遗留的
**活体 `tools/list` 与夹具逐字核对**。

---

## 1. 已给定的前置事实（**先核对，不要假设**）

| 项 | 值 |
|---|---|
| 引擎二进制（mono） | `F:\moonbit-hof-rs\godot-mcp\godot\bin\godot.windows.editor.x86_64.mono.exe` |
| 期望版本串 | 以 **`4.8.dev.mono`** 开头（实测为 `4.8.dev.mono.custom_build.ba1587c71`） |
| 编辑器端点 | `http://127.0.0.1:9877/mcp`（调度者以 `--path F:\moonbit-hof-rs\.workspace\mario --mcp-port=9877` 启动） |
| 工作区 | `F:\moonbit-hof-rs\.workspace\mario` |
| 模型端点 | `http://100.105.152.101:18080/v1`，模型 `deepseek-v4.1-flash`（见 `config/hoh.yaml`） |
| 密钥 | 经环境变量 `HOH_MODEL_API_KEY` 提供。**不准把密钥打进任何输出、日志或报告**（只可打印其长度） |
| 配置 | `config/hoh.yaml`（`runtime.workspace` / `spec` / `runs_dir` 均已就位，`agent.step_limit=150`） |

**必须先做的前置核对（任一项不符 ⇒ 停止并报告，不要开跑）**：
1. `GET http://127.0.0.1:9877/mcp` 返回 200，且 JSON 里 `is_editor == true`；
2. 9877 的**监听者 PID** 的可执行体路径 == 上面那个 mono 二进制（用 `Get-NetTCPConnection` + `Get-Process`，
   或 `hof doctor` 的 `godot.engine_binary` / `godot.engine_version` 两项——两项都要贴原始输出）；
3. `<binary> --version` 的输出以 `4.8.dev.mono` 开头（贴原文）；
4. `.workspace/mario/project.godot` **不含** `[editor_plugins]`，且 `.workspace/mario/addons/godot_mcp_rs` **不存在**
   （若存在 ⇒ 端口双绑定风险，停止并报告，不要自己删——那是批次一的职责）。

---

## 2. 第一件事：活体契约逐字核对（**准入门**）

批次一（离线）无法证明"活体 `tools/list` 与夹具一致"，这一条由你现在补上：

1. 对 9877 发 `tools/list`（`initialize` 后），把**原始响应字节**落盘到临时目录（不要写进 `runs/**`）。
2. 与 `tests/fixtures/mcp/tools_list.json` 做**名字集合**与**逐字（name/description/inputSchema）**比对；
   同时与 `godot-mcp/godot/modules/mcp_server/docs/tools_list.renamed.json` 比对。
3. **规则**（D217 裁决第 3 条，必须照此判定）：
   - **名字集合**必须**严格相等**（多一条或少一条都算不一致 ⇒ **停止，不要开跑**，把差集按"活体多出 / 夹具多出"两列列出）；
   - **`name` / `description` / `inputSchema`** 逐条**逐字**比较；有差异 ⇒ 允许开跑，但必须**逐条列出**差异
     （这是"离线源 vs 活体"的已知风险面）；
   - **夹具专用字段必须被点名**：批次一的夹具是据引擎侧文档 `tools_list.renamed.json` **重新序列化**的产物
     （**不是**活体捕获），可能带有活体没有的键。你必须查明并写出：夹具相对活体/相对 `renamed.json`
     **多哪些键、少哪些键**；这些**夹具专用键不参与逐字比较**，但**必须在报告里点名**，不得含糊带过。
4. 记录：工具条数、编辑器作用域可见条数、以及 `GET /mcp` 里的 `tools` 计数字段。

---

## 3. 跑真实 T=1 冒烟

1. 设好环境变量（从 `config/model.secret.env` 取值即可；**不要 echo 它**）。
2. 用 `hoh` 二进制（`$HOH_HOH_BIN` 或 `target\release\hoh.exe`）执行一轮：
   `hoh run --iterations 1 --run-id smoke-t6`
   （不要带 `--fresh-workspace`，当前工作区是 A_0 起点；若你必须改参数，在报告里说明为什么。）
3. **一轮就是一轮**：`--iterations 1`。它可能会跑很久（历史实测单轮 11M–50M tokens、数十分钟到数小时）。
   **不要**因为"看起来没动静"就中断它；只有确认死锁或已失去意义才允许停，且必须在报告里说明。
4. 记下**退出码**（预期 `0`；`6` = 循环完成但产物不可启动；`4` = 外部依赖不可用；`2` = 契约违约）。

---

## 4. 取证与逐条判定（E1..E6）

对 `runs/smoke-t6/` 逐个核对，**每条都要贴证据**：

| 编号 | 判据 | 你要给的证据 |
|---|---|---|
| E1 | 一轮完整循环跑通：Planner 产出合法 `D_1`；Developer 产出工程增量；QA 产出合法 `E_1` | `iter-1/plan.md`、`iter-1/evidence.json`、`iter-1/qa_report.md`、`versions/index.json` 的真实片段 |
| E2 | 产物**可启动**（无脚本/编译错误） | `iter-1/result.json` 的 `artifact_gate` + 活体 `GET /mcp` 与 `editor_get_errors`（新名以契约夹具为准）的真实输出 |
| E3 | 核心可观察行为存在（左右移动、跳跃、≥1 可交互对象、终点/胜负条件） | 回放/多帧采样的**真实 payload** + 前后截图；**逐项**说 met/not_met/unverifiable |
| E4 | `E_1` 每个 verified claim 都指向可复现的公共执行记录；无证据者落 gap | 逐条对照 |
| E5 | QA 未改 `A_1`（快照 hash 前后一致） | 两个 hash 的真实值 |
| E6 | 未达成就如实声明 = 诚实结论，**不算失败**；把未达成谎报成 verified 才算失败 | 人工复核 + **至少构造 1 个反例**（例如断言某条 claim 的证据是否真的支持它） |

> **E6 是本次最重要的判据**：宁可 E3 明确 `not_met`，也不要把它写成 met。历史上 `smoke-t5` 就是
> "exit 0 但 E3 不可判定"，如实记录是**正确的**交付。
>
> **特别注意**：新契约下 `running_game_*` 只存在于**游戏端点**（由 `editor_play_scene` 注入的 `--mcp-port` 决定），
> 编辑器端点不提供。若 E3 依赖游戏端点而端点未登记成功，那就是 `not_met`（或缺陷），**不是**"用编辑器端点凑一个近似"。

---

## 5. `meta.json` 的引擎身份（本批新增，必须核对）

`runs/smoke-t6/meta.json` 必须含 `engine` 块，且：
- `engine.binary.path` == mono 构建路径；`size_bytes`/`sha256` 与你自己算的一致；
- `engine.version_string` 以 `4.8.dev.mono` 开头；
- `engine.listener.matches_binary == true`；
- `engine.mcp.editor_endpoint` 是 9877；`game_endpoint` 若为 `null` 必须带 `reason`；
- **任何字段缺失或为 `null` 而无 `reason` ⇒ 缺陷。**

---

## 6. 硬禁项（违反任一条即任务失败）

1. **不杀死、不重启、不抢占**编辑器进程；不占用 9877 以外的任何端口去"试"；
2. **不修改** `godot-mcp/**`（只读；其中 `godot/` 还是独立仓库）；
3. **不修改** `.spec/hof-rs/PRD-mario.md`（冻结的 S；跑完 `sha256` 必须仍是 `4c81c3a9…5c3a`）；
4. **不修改** `src/**`、`tests/**`、`config/hoh.yaml` 来"让冒烟通过"。
   若发现代码缺陷导致冒烟失败 —— **不要自己修**，把它写成缺陷（含复现与影响）并报告，修复由另一批实现子代理做；
5. 不删除、不覆盖既有的 `runs/smoke-t1..t5`（它们是**旧契约时代**的证据，保留用于对照）；
6. 不 `git commit`、不 `git push`、不 stage 任何东西（本批是**执行与取证**，提交由调度者决定）；
7. 不把密钥写进任何输出、日志、报告或 `runs/**`；
8. 不新建仓库外的第三方端点调用；只打 `127.0.0.1:9877` 与配置里的模型端点。

---

## 7. 回报格式

报告写到 `.spec/hof-rs/tasks/TASK-DR47-SMOKE-REPORT.md`，必须含：

1. **前置核对**（§1 四项）的原始输出；
2. **活体契约核对**（§2）结论 + 差集/差异清单；
3. **冒烟命令原文**（不含密钥）+ **真实退出码** + 关键日志片段；
4. **E1..E6 逐条判定**（met / not_met / unverifiable + 证据）；
5. **`engine` 块**原文 + 你自己算的 sha256 对照；
6. **缺陷清单**（若有，含复现步骤与影响；没有写"无"，**不许省略本节**）；
7. **遗留风险与不确定项**（例如"游戏端点登记失败""E3 第 3 项无法构造"）；
8. **诚实披露**：任何中断、重跑、猜错、绕过尝试。

**回报给父代理只有一行：报告文件路径。**
