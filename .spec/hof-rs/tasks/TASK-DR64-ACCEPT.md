# TASK-DR64-ACCEPT — E1 根因离线诊断的独立验收

> 你是**独立验收子代理**。不得继承实现者或调度者的结论。
> 判据：`.spec/hof-rs/tasks/TASK-DR64.md`、`REQUIREMENTS.md`（E1 口径）、`DECISIONS.md` **D243/D257**。
> 实现者报告（**线索，非证据**）：`.spec/hof-rs/tasks/TASK-DR64-REPORT.md`。
> **离线、只读诊断批**（无源码改动，0 提交）。产物：`.spec/hof-rs/tasks/TASK-DR64-ACCEPTANCE.md`。

## 1. 核心复核（自己复现，给命令 + 原始输出 + 文件:行）

1. **头号命题：测量**能否**看见 Developer 的工程写入？**
   请**你自己**按 `src/runtime/policy.rs` 的 `hash_tree` 口径（**不得照抄它的实现**）在 `runs/smoke-t7` 的工作区上复算 `A_0`，
   并做**对照实验**：**新增 1 个工程文件**（如 `scripts/` 下）后再算 ⇒ **必须与 `A_0` 不同**。
   **若加了工程文件摘要仍不变 ⇒ 说明 E1 判据不可达 ⇒ 判 fail（并给出你的证据）。**
   同时核实排除集是否确为 `{.hoh,.git,.godot,.import}`，以及 `HOH_SCRATCH_DIR` 是否落在其中。
2. **`LimitsExceeded` 归因**：核实是 **step_limit=150**（三角色皆然）而非墙钟；核实墙钟超限走的是**另一个**中断种类
   （`TimeExceeded`），故与实测 `LimitsExceeded` 不冲突。给出 `result.json` 与轨迹里的**原始指针**。
3. **`no_progress` 的因果地位**：核实它**只是 warning**（`run_loop.rs:798-807` + `model.rs:345/:356` 的 `code()`），
   且该轮 **`ok=true`、`failed_role=null`、`exit_code=0`**。⇒ 判定"**因/果/描述**"。
4. **假绿指控**：核实"`ok=true` + 退出码 0 而 E1 not_met"**成立**，并判断这是否意味着
   **自动化层面会漏报 E1 失败**（这对目标判据至关重要）。**若指控不成立 ⇒ 明确反驳。**
5. **它点的测试级假绿**：核实 `tests/artifact_hygiene.rs:112-115` 与 `tests/developer_contract.rs:57-74`
   是否**只做字符串包含断言**（⇒ 结构上永远绿）。**给出你的判断**，并判断这是否与 E1 的失败**有因果贡献**（还是仅相关）。
6. **两条候选修法**是否**可执行、最小、风险已列**；**§5 的两个最小测试**（`e1_reachability.rs` / `role_shell_contract.rs`）
   设计是否**真能钉死**对应结论（先红后绿是否成立）。**若设计空洞 ⇒ 指出并给替代。**
7. **禁区与陷阱**：`runs/**` 未动（**摘要口径须写明**，含 PS `Sort-Object` 文化排序；并自证 `runs/smoke-t6` = `c144ef32…`）；
   PRD sha 未变；**引擎树必须用嵌套仓证明**，并**核实它对 D242 表述的收窄**：
   外层 `git ls-files godot-mcp` = 6484 而 `git ls-files godot-mcp/godot` = **0**（`.gitignore:33`）——
   **若数字不符 ⇒ 记缺陷**。仓内无临时物、仓外临时物已删（**核实它自报的删除**）。
   三个假绿陷阱各实测（含 `cmd` 的 `^`）。
8. **诚实性**：逐条核实其"实测/推断"标注；**不得**让推断混成实测。

## 2. 纪律
**只读**：不改任何文件（本批**无植入**——诊断批只有报告）。
**离线**：不启动 Godot、不碰外部端口、不联网、不调模型。
不改 `runs/**`、`.workspace/mario/**`、`PRD-mario.md`、`DECISIONS.md`、`godot-mcp/**`；临时物**仓外**。
**不 push、不 stage**；**报告写完后不要再改**（我在你的完成消息之后才提交）。**不要修任何你发现的问题。**

## 3. 结构化结论（写进报告 §1）
```json
{ "verdict": "pass" | "fail",
  "criteria": [ { "id": "MEASUREMENT_REACHES_ENGINEERING_WRITES|LIMIT_ATTRIBUTION|NO_PROGRESS_IS_DESCRIPTION|FALSE_GREEN_CLAIM|TEST_LEVEL_FALSE_GREEN|REPAIRS_AND_TESTS_ACTIONABLE|GUARDS|HONESTY", "pass": true, "evidence": "命令 + 真实输出 + 文件:行" } ],
  "defects": [ { "id": "DEF-x", "severity": "blocker|major|minor|info", "what": "...", "reproduction": "..." } ],
  "risks": [ "..." ], "unverified": [ "..." ] }
```
`verdict=fail` 门槛：**加工程文件后摘要仍不变**（判据不可达）、归因错误、`no_progress` 因果判定错误、
假绿指控不成立、修法/测试空洞、或禁区被动过。

## 4. 报告必含小节
1. 结构化结论 + 命令与输出；2. 逐项核对表；3. **你自己的对照实验**（加文件 ⇒ 摘要变的真实输出）；
4. 对"测量可达"的独立判定；5. 对"自动化假绿"的独立判定；6. 未验证项与理由；
7. 你没有独立复核的部分；8. 给下一批的建议（**不要**自己改代码）。

**回报给父代理只有一行：报告文件路径。**