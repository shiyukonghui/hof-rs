# TASK-152-ACCEPT — TASK-152（g05 自包含）独立验收

> 你是**独立验收子代理**。不得继承实现者或调度者的结论。
> 实现者报告：`godot-mcp/recovery/reports/TASK-152-REPORT.md`（**线索，非证据**）。
> 产物：`godot-mcp/recovery/reports/TASK-152-ACCEPTANCE.md`。
> **落点**：引擎仓 `godot-mcp/godot`（分支 `feature/mcp-server-module-rebuild`，被测 HEAD **`bef4be0407`**，
> 基线 `035edfce7f`）+ 外层仓 `godot-mcp/recovery/**`。

---

## 1. 先读

`godot-mcp/recovery/tasks/TASK-152.md`（判据）→ `reports/TASK-152-REPORT.md`（自述）
→ `DECISIONS.md` **D225/D226/D227** → `modules/mcp_server/scripts/check_rename_map.py`
→ `modules/mcp_server/docs/rename-baseline-tools-list.json` → `tools/run_gates.ps1:214-225`
→ `scripts/check_engine_anchor.ps1`。

## 2. 核心复核项（逐条自己复现，给命令 + 原始输出 + 文件:行）

1. **自包含是否真的成立（头号目标）**：`check_rename_map.py` 的 `DEFAULT_OLD_CONTRACT` 是否已指向
   **引擎仓内**路径；全脚本与 `g05` 的**执行路径**上是否**不再出现** hof-rs 的任何路径
   （自己 grep：`moonbit-hof-rs`、`hof-rs`、以及 hof-rs 内相对路径）。
2. **基准件字节一致**：`docs/rename-baseline-tools-list.json` 的 **sha256 是否仍为 `8f8051c4…`**、
   条数 **174**、**且引擎 blob id 是否为 `543b49b2583bf06c3aba2a320649a31eda272e3e`**
   （= hof-rs `db2eed7^` 的那个 blob）。请**自己**用 `git cat-file blob` 或等价方式核对
   （hof-rs 侧对象库只读；**不得**改 hof-rs 任何文件）。
3. **十道门**：自己跑全部十道（用与 `tools/run_gates.ps1:214-225` **逐字相同**的命令集）。
   应 **10/10 exit 0**；`g05` 应 `30/30 PASS`（B0 sha `8f8051c4…`、B1 len=174、B2 两个集合为空）；
   `g01` 160/160、`g02` 1586/1586、`g04` 3/3（**应报告 editor 154 / game 73 / contract 177**）、
   `g07` 10/10、`g08` UNCLASSIFIED=0、`g10` 22/22。**抽验至少两道你没有亲手跑过的门。**
4. **非空洞性（两处植入，必须都压红）**：
   ①往**引擎内基准件**植入一个名字 ⇒ `g05` 必须在 **B2** 上红、且**点名**该名字；
   ②往**改名表**植入一条错映射 ⇒ 必须红在**恰好一条**检查（实现者称是 D1）。
   之后**逐字节恢复**：`git status --porcelain` 与 `git diff --stat` **双空** +
   `git hash-object` == `HEAD` blob（**四个文件**都要；仓库对 CRLF 敏感）。
   **若任一植入不红 ⇒ 判 fail**（门被改成了永绿）。
5. **`g09` 判据变更的护栏（**我采纳了实现者的建议，但必须你替我把关**）**：
   实现者报告 `g09` 为 **`ANCHOR_STRUCTURAL_EQUIVALENT`**（ANCHOR=`035edfce7`、HEAD=`bef4be040`、
   `DIFF_COUNT=3 SAFE_COUNT=3 RED_COUNT=0`、RESULT PASS），并**未改** `check_engine_anchor.ps1` 一个字节。
   我已把本线判据改为：**`ANCHOR_EQUAL` 或 `ANCHOR_STRUCTURAL_EQUIVALENT` 且 `RED_COUNT=0`**，**但附加三个条件**：
   - (a) **逐条列出那 3 个 diff 文件**，并证明**每一个都是 docs/scripts**（**不得**含任何
     `modules/mcp_server/**/*.cpp` / `*.h` 等**编译输入**）；
   - (b) `git diff 035edfce7f..HEAD -- <编译输入>` **必须为空**；
   - (c) `git diff 035edfce7f..HEAD -- scripts/check_engine_anchor.ps1 tools/run_gates.ps1` **必须为空**
     （即判据脚本本身未被松动）。
   **任一条件不成立 ⇒ 判 fail。** 并请明确指出：该 3 个 diff 是否**只是**本文档/脚本。
6. **诚实范围（必须独立判定）**：实现者承认 `modules/mcp_server/scripts/gen_renamed_contract.py`
   （约 `:1800/:1804`）**仍**指向 hof-rs 的夹具并冻结同一 sha256，虽然**不在 `g05` 的执行路径上**。
   请核实该说法（行号 + 实际读到的内容），并明确回答：**"模块不再依赖跨仓输入"这句话是否成立**
   （我的判断是**不成立**，已另立 TASK-153；若你同意，请在报告里确认这句不许被写成完成态）。
7. **它自曝的两处**：①`g08` 曾因它自己新增的注释续行（裸 `152`）产生两个 UNCLASSIFIED、它改为不间断注释行后转绿，
   且**未**改 `check_hardcoded_counts.py` 任何模式；②一处**编造的溯源日期**（2026-02-15）被它自己发现并改正。
   请核实：`check_hardcoded_counts.py` 在 `035edfce7f..HEAD` **零 diff**；`g08` 现真为 UNCLASSIFIED=0；
   当前溯源日期与采集事实一致。
8. **禁区自查**：`9877` 从未被绑定/探测（`g04`/`g10` 的 `guard_user_port_9877` 应 `pid_before=-1 pid_after=-1`）；
   `9888/9889` 前后空闲；未 `push`；**hof-rs 侧零改动**（其夹具 sha 仍 `50c5fb42…`/177、mtime 未变）；
   无新依赖；无既有检查被删/放宽。

## 3. 纪律

只读为主；**唯一**允许的改动是 §2.4 的两处植入（必须逐字节恢复并三法证明）。
**绝不占用/探测 9877**；自用端口只用 **9888/9889** 并收尾复核释放。串行构建、不抑制输出；
不改 hof-rs 侧；不 `push`、不 stage；不联网（回环端口除外）。**不要修任何你发现的问题。**

## 4. 结构化结论（写进报告 §1）

```json
{ "verdict": "pass" | "fail",
  "criteria": [ { "id": "SELF_CONTAINED|BASELINE.BYTES|GATES.10|NON_VACUITY|G09.GUARDRAILS|SCOPE.HONESTY|SELF_REPORTED|GUARDS",
                  "pass": true, "evidence": "命令 + 真实输出 + 文件:行" } ],
  "defects": [ { "id": "DEF-x", "severity": "blocker|major|minor|info", "what": "...", "reproduction": "..." } ],
  "risks": [ "..." ], "unverified": [ "..." ] }
```

`verdict=fail` 门槛：自包含不成立、基准字节不符、某道门红、**任一植入不红**、§2.5 三条件任一不成立、
或原始工件被动过。

## 5. 报告必含小节

1. 结构化结论 + 真实命令与退出码；2. 逐项核对表；3. **反例清单**（你植入/改动了什么、观测到什么、是否推翻）；
4. 对 `g09` 判据变更的**独立把关结论**（含那 3 个 diff 的完整清单）；5. 未验证项与理由；
6. 你没有独立复核的部分；7. 给下一批的建议（**不要**自己改代码）。

**回报给父代理只有一行：报告文件路径。**
