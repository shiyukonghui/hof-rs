# TASK-SMOKE-T10 — 真机 T=1 整轮（在 DR-69 之后：通道已通、证据形态已成形）

> **基准任务书 = `.spec/hof-rs/tasks/TASK-SMOKE-T8.md`**（环境/身份规则、六条判据口径、两条风险旗、证据要求、报告格式**全部沿用**）。
> **本文件只列 T8 之后的变化与必须回答的问题。** 冲突时以本文件为准（它是后来的）。
> 先读：T8 书 → `REQUIREMENTS.md`（E1..E6 原文）→ `TASK-SMOKE-T9-REPORT.md` 与其 **`TASK-SMOKE-T9-ACCEPTANCE.md`** →
> `TASK-DR69-REPORT.md` 与其 **`TASK-DR69-ACCEPTANCE.md`** → `DECISIONS.md` **D265..D272**。
> **轮目录：`runs/smoke-t10/**`（全新）。`runs/smoke-t6|t7|t8|t9` 一律只读。**

## 0. 本轮为何不同（DR-69 已改了什么）

1. **游戏路由现在跨进程发布**：运行在注册端点时写 `<run dir>/game_endpoint.json`，并经 `HOH_GAME_ROUTE` 交给每个角色；
   新进程 `hoh tools call running_game_*` **应当成功**；**无记录时仍硬失败**（DR-43 未放宽）；
   `editor_stop_scene` 撤该文件。**离线只证到"环回替身上可达"** ⇒ **本轮是它的第一次真机检验**。
2. **Developer 提示词已改**：先改工程代码；**轮内游戏观测不是你的前置**（归 Tester/电池）；**禁止自造 MCP 客户端/手写 JSON-RPC/裸探端口**；
   完成定义第 4 条**不再**要求用不可达通道自证。
3. **单条工具结果上限 64 KiB**（超限截断 + 显式标注 + 记 `original_bytes`）；**被中止的电池 pass 先保存后清理**
   （`quarantine/deterministic-pass-<n>.stale-<ts>`）。
4. **E3 的证据形态现在轮内可产出**：每个回放窗口的 **before/after PNG**（`.hoh/evidence/replay-<action>-{before,after}.png`）
   + **`running_game_assert_node_state{node_path=Player, property=position, operator=neq, expected=<窗口首样本>}`**。
   **期望值与观测取自同一采样窗** ⇒ **~14 帧采样滞后被消掉**；**没有任何"按总位移"的断言**。
5. **卫生检查现在覆盖目录**（`artifact_hygiene.suspicious_directories`）；密钥**赋值**（不只密钥值）会被脱敏。

## 1. 必须回答的核心问题（逐条给原始证据）

1. **E1 是否终于 `met`？** 具体：Developer 是否**真的写了工程文件**（`A_1 != A_0`，给出两树摘要与变更文件）、
   整轮是否**跑完**（Planner→Developer→Tester→电池）、是否产出**被接受的 `E_1`**。
   **若仍失败，必须报出新的真实原因**（不得沿用旧原因），并给出 `result.json`/`meta.json` 两个退出码位置与进程退出码的三方一致性。
   **注意**：DR-69 的**角色 CLI 可达**只在离线验证过 ⇒ 若 Developer 仍绕道，**报出 `hoh tools call running_game_*` 在真机上的原始回包**（成功还是 `game_endpoint_unavailable`），这是本轮最有价值的单条诊断。
2. **Tester 的证据形状是否终于被走到**（DR-68 的修复**至今未在真机上执行过**）⇒ 合法证据束是否被接受。
3. **E3 是否补齐**：电池是否在轮内产出 **before/after PNG + `position neq` 断言**；
   **引擎是否接受了该断言**（若报 `POSITION_ASSERTION_UNAVAILABLE`，如实说明并给原始回包）；
   左右移动、跳跃、可交互对象、终点/胜负各自可否被证实。
   **不得**用探针的 `GAME_INPUT_CHANNEL_OK` 当行为证据（风险旗 1 仍在）；**`input_axis` 在真机恒为 `null`** ⇒ 承重的是**按位置**的证据。
4. **降噪与门**：本轮是否有 **DR-24 定向修复 attempt**？若有，**它是否改动了工程树**（零写入的修复尝试是缺陷）；
   是否出现**过期编辑器日志关门**（F1 类）；`battery_passes`（第一遍 vs 第二遍）是否正常。
5. **64 KiB 上限是否真的生效**：轨迹里是否出现被截断+标注的工具结果；**是否再有超长结果被回放进后续请求**（上轮因此死过一次）。
6. **"零增量"是否发生**：若发生，报 `warnings.log` 的 `Zero-increment shape: …` 原文，
   并说明是**"Developer 什么都没写"**还是**"写了但全在排除路径"**。

## 2. 不要读作 met 的清单（DR-69 明确未验证）
- 真机上 `hoh tools call running_game_*` 是否成功；
- **引擎是否接受 `position:neq` 断言**；
- **DR-68 的 Tester 证据形状修复从未在真机执行过**；
- 闸门**仍无法区分**"工程无需改动"与"Developer 没改"（它只**测量**"是否在任何地方写过"）。

## 3. 纪律（与 T8 相同，并强调）
- 只跑**一轮**；**`runs/**` 除自己的 `runs/smoke-t10/**` 外零写入**（**连"写过再删"都不允许**）；
  分析产物放仓外或 `.spec/hof-rs/tasks/TASK-SMOKE-T10-evidence/`。
- **不改** `godot-mcp/**`、`.spec/hof-rs/PRD-mario.md`、`DECISIONS.md`、`.workspace/mario/**`。
- 密钥从 `config/model.secret.env` 导入，**绝不打印**（只报长度）；**证据里不得出现环境转储**（上轮的教训）。
- 编辑器应在 `127.0.0.1:9877`（pid 75204）；若需启动则记录 pid 并**收工后保持存活**；**清理任何孤儿游戏进程并上报**。
- 引擎身份以 **`--version` 字符串**为准（sha256 仅记录）；"引擎未改"用**嵌套仓**或 mtime/摘要证明；
  目录摘要口径**写明并自证**；三个假绿陷阱各实测。
- 本地提交英文信息带 `(SMOKE-T10)`，**不 push**；**不得**声称 E1/E3 met 除非有任务书要求的证据。

## 4. 报告
`.spec/hof-rs/tasks/TASK-SMOKE-T10-REPORT.md`：T8 书要求的各节 + §1 六个核心问题的逐一回答（原始证据）
+ "本轮不可判定的判据"（若有）与理由 + 诚实披露。**回报父代理只给报告文件路径。**