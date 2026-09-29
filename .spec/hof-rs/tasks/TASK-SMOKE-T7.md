# TASK-SMOKE-T7 — 真机 T=1 复测（引擎 `035edfce7`，含 TASK-151 修复；验证 §15 后的 E2/E3）

> 你是**执行子代理**，无上游对话上下文；**本文件是你的唯一任务来源**。
> 先读：`.spec/hof-rs/REQUIREMENTS.md`（v0.3，看 C3/C4/C5 与 E1..E6 的口径）→
> `DESIGN-DETAIL.md` **§15**（v0.10）→ `ACCEPTANCE.md`（v2）→ `DECISIONS.md` **D216..D239**
> （尤其 D220/D223：上一轮真机 `smoke-t6` 的结论与缺陷）→ `.spec/hof-rs/tasks/TASK-DR54-REPORT.md`（本批改了什么）。
> **落点**：`F:\moonbit-hof-rs`。**这是真机批次**（允许启动 Godot、允许调模型端点）。

---

## 0. 目标

跑**一轮**真实 T=1，回答一个具体问题：**在引擎 `4.8.dev.mono.custom_build.035edfce7`（含 TASK-151 修复）
+ §15 改造（DR-54/55/56）之后，E2/E3 是否从 `not_met` 转为 `met`**。
上一轮（`smoke-t6`）的结论是 **E1/E2/E3 not_met，E4/E5/E6 met**，其中 **E2 是集成假阴性**（DR-48 已修）、
**E3 是游戏端点被调试器冻结**（引擎侧 TASK-151 已修，并已由 §15 把关键路径移到语义工具上）。

## 1. 前置（**由决策者已准备，你只需核对**）

- 编辑器**已在 9877 上运行**（决策者启动，mono 二进制，`--mcp-port=9877`）。
  你**必须**先核对：`GET http://127.0.0.1:9877/mcp` 返回 `status=ok` 且 `is_editor=true`，
  并记录**监听者 pid 与可执行体路径**、以及 `--version` 字符串（`godot.windows.editor.x86_64.mono.console.exe --version`）。
- **9877 只归编辑器用**；**不得**另起同类实例占它。
- 模型端点已在 `config/hoh.yaml`（`http://100.105.152.101:18080/v1`，`deepseek-v4.1-flash`）。
  **密钥不自动加载**：在 **bash** 里用
  `export HOH_MODEL_API_KEY=$(grep '^HOH_MODEL_API_KEY=' config/model.secret.env | cut -d= -f2- | tr -d '\r\n')`
  （**绝不打印密钥**，只可报**长度**）。
- 先做一次**连通性前置**：`hoh doctor`；确认模型端点可达（不要贴密钥）。

## 2. 要做什么

1. **先确保 `hoh` 是新鲜的（硬要求）**：仓库里现存的 `target/release/hoh.exe` 构建于 **2026-09-29 00:40:12**，
   **早于 §15 的全部提交**（`513069c`/`df95339`/`6329e5c`/`b3ccef9`/`9ff9cd2`）⇒ **它不含 DR-54/55/56**。
   你**必须**先**串行**跑 `cargo build --release --offline`（**不得**并发构建），
   并**用证据证明新鲜**：记录 `target/release/hoh.exe` 的 **mtime 与 sha256**，
   且 mtime **必须晚于** `git log -1 --format=%ci 9ff9cd2`。**若 mtime 仍早于该提交 ⇒ 停下上报**，
   **不得**用一个不含本批代码的二进制去跑真机（那会让结论无效）。
2. **再跑一轮**：`target/release/hoh.exe run --iterations 1 --run-id smoke-t7`。
2. **留全证据**：`runs/smoke-t7/**`（这是本轮基线，**不得**覆盖 `runs/smoke-t6/**`）。
   至少要有：退出码、`meta.json`（含 `engine` 块）、`iter-1/{result.json,evidence.json,qa_report.md,candidate/,traj/,logs/}`、
   usage/tokens、以及**所有 attempt 的真实现状**。
3. **逐条判定 E1..E6**（判据以 `REQUIREMENTS.md` 为准；**逐条给原始证据**，不要只给结论）：
   - **E2**（可启动闸门）：`artifact_gate.launchable` 是否已不再被引擎信息横幅误判为失败；
     **注意**：引擎**真错误**行（如 `ERROR: [MCP] SceneTree never became available…`）**必须**仍能让闸门失败——
     请**构造反例**确认豁免不是"一刀切变绿"。
   - **E3**（游戏内行为可判定）：**这是本轮的核心**。请给出：①`editor_play_scene` 是否仍正常返回端点/pid；
     ②`running_game_*` **语义工具**（`create_input_recording`/`play_input_recording`/`run_test_scenario`/
     `get_node_property_samples`/`get_node_properties`）**是否真的被调用并成功**；
     ③**游戏端点在被拒绝/编译不过的调用之后是否仍然存活**（TASK-151 的验收点；
     可主动构造一次"编译不过的 `code`"或一次语义拒绝来检验）；
     ④关键断言是否由**语义工具**产出，`execute_gdscript` 是否**只**做只读探针。
   - **E1/E4/E5/E6** 按原口径判定（E5 的哈希口径请**自己重实现**核对，别复用工具自报）。
4. **记录引擎身份**（判据 ≠ 判据混用）：`meta.json.engine` 的 `version_string` **应**以
   `4.8.dev.mono.custom_build.035edfce7` 开头（**这是判据**）；`binary.sha256` 只作**记录**
   （引擎构建**非位级可复现**，同源码重建会得到不同 sha256）。
5. **观察运行时成本**：本轮 tokens/耗时；**特别记录**"判死前的重试乘法"是否出现
   （已知残留：判死前最多约 6 次 HTTP 尝试、按 120s 估算可烧约 12 分钟，见 D239）。

## 3. 硬约束

- **不得**改 `godot-mcp/**`（引擎侧仍由引擎仓那条线管）；**不得**改 `.spec/hof-rs/PRD-mario.md`；
  **不得**写/覆盖 `runs/smoke-t6/**`。
- **不得**为"让指标好看"而改判据、改断言、改配置里的阈值；**不得**把推断写成实测。
- **不得**因为一次 `LimitsExceeded` 就宣称 E 项结论——`smoke-t6` 四次 attempt 全 `LimitsExceeded` 仍给出了有效结论；
  你只需**如实**汇报本轮的 attempt 结果。
- **不 push**；**不改** `src/**`/`tests/**`（本批只跑与取证；若你发现必须改代码，**停下上报**）。
- 收尾：**不要杀掉编辑器**（决策者管理它）；但请**记录**它的 pid/路径与你观测到的状态；
  释放你自己起的任何进程与端口，并复核没有遗留监听。

## 4. 完成后回报（**只回报报告文件路径**）

报告：`.spec/hof-rs/tasks/TASK-SMOKE-T7-REPORT.md`。必含：

1. **结论**：E1..E6 逐条的 **met / not_met / 不可判定** + 每条**原始证据**（文件:行或命令输出）；
2. **E3 专项**：§2.3 的四问逐条回答，**含游戏端点存活性实验的原始输出**；
3. **退出码与 tokens/耗时**；`artifact_gate.launchable` 的值与理由；
4. **引擎身份**：`version_string`（判据）与 `sha256`（记录）、监听者 pid/路径；
5. **反例**：你为 E2 的豁免非空洞性所构造的实验与其结果；
6. **与 `smoke-t6` 的逐项对照**（哪些变了、哪些没变、为什么）；
7. **仍未验证/不可判定项**（严格区分实测与推断）；
8. **诚实披露**（失败、重试、你自己搞错又改的地方）。

**回报给父代理只有一行：报告文件路径。**