# TASK-153-ACCEPT — TASK-153（生成器去跨仓耦合）独立验收

> 你是**独立验收子代理**。不得继承实现者或调度者的结论。
> 实现者报告：`godot-mcp/recovery/reports/TASK-153-REPORT.md`（**线索，非证据**）。
> 产物：`godot-mcp/recovery/reports/TASK-153-ACCEPTANCE.md`。
> **落点**：引擎仓 `godot-mcp/godot`（分支 `feature/mcp-server-module-rebuild`，被测 HEAD **`28432f859f`**，
> 基线 `bef4be0407`）+ 外层仓 `godot-mcp/recovery/**`。

## 1. 先读
`godot-mcp/recovery/tasks/TASK-153.md` → `reports/TASK-153-REPORT.md` → `DECISIONS.md` **D227/D228/D229**
→ `modules/mcp_server/scripts/gen_renamed_contract.py`（`:1764`、`:1801-1834`）→ 同族样板
`modules/mcp_server/scripts/check_rename_map.py:102`。

## 2. 核心复核项（逐条自己复现，给命令 + 原始输出 + 文件:行）

1. **去耦是否真成立**：`DEFAULT_OLD_CONTRACT` 是否指向**引擎内**基准；**非注释**处是否**不再出现**
   hof-rs 的任何路径/字面量（自己 grep + AST 扫描，并**从 `C:\` 跑一次**证明无 CWD 依赖）。
2. **行为保持（头号反直觉项）**：自己复算"改前生成器 + `--old-contract` 指向引擎基准"与"改后生成器默认"
   两者输出是否**逐字节相同**（实现者称 154311 B / `8461b6ee…e5373`）。
   **若不同 ⇒ 判 fail**（那就不是"只改来源"，而是偷改了行为）。
3. **非空洞性（自己设计植入，不要照抄）**：在**引擎内基准**上植入一个真实差异 ⇒ 生成器**必须失败**
   （非零退出，**不是**警告）；再在**改名表**上植入一条错映射 ⇒ 也**必须失败**。
   两处都要**逐字节恢复**：`git status --porcelain` 与 `git diff --stat` 双空 + `git hash-object` == HEAD blob
   （四文件；仓库对 CRLF 敏感）。
4. **十道门**：用**外层仓** `godot-mcp/tools/run_gates.ps1 -RunGates`（**注意：它在外层仓，不在引擎仓**）
   自己跑；应 **10/10 exit 0**；`g05` **30 PASS / 0 FAIL**；`g01` 160/160、`g02` 1586/1586、
   `g04` 3/3（应 154/73/177）、`g07` 10/10、`g08` UNCLASSIFIED=0、`g10` 22/22。
5. **`g09` 三道护栏（现行判据）**：`ANCHOR_EQUAL` 或 `ANCHOR_STRUCTURAL_EQUIVALENT` 且 `RED_COUNT=0`；
   且必须 ①逐条列出区间 diff 文件并证明**全是 docs/scripts、无编译输入**；②`git diff bef4be0407..HEAD -- <编译输入>` 为空；
   ③`check_engine_anchor.ps1`、`check_hardcoded_counts.py`、`run_gates.ps1` **零 diff**。任一不成立 ⇒ fail。
6. **溯源真实性**：新增注释里的路径/字节/条数/sha256/日期是否**可核**；实现者称它**沿用了 TASK-152 已提交的日期**
   并注明"本任务未采集"——请核实**没有编造**（这是上一批出现过的前科）。
7. **D229 第 1 条的独立复核**：确认**未**重生成 `docs/tools_list.renamed.json`
   （其 sha256/字节数应与 `bef4be0407` 时相同），并确认 `_meta.generated_from` 确为 hof-rs 路径且**早于本任务**
   （`git log -p` 追它最后一次被写入的提交）。⇒ 判定"历史事实、非本次引入"是否成立。
8. **D229 第 2 条的独立复核**：核实 `mcp029_clear_default_evidence.ps1:62` 与
   `mcp032_d3_d4_d6_evidence.ps1:63` 确含跨仓可执行引用、且后者确含 `$UserPort=9877`；确认二者**不在十门路径上**。
9. **禁区自查**：`9877/9888/9889` 前后均无监听；未 `push`（`origin` 应仍为 `bef4be0407`）；
   hof-rs 侧零改动（夹具 sha 仍 `50c5fb42…`、mtime 未变）；无新依赖；无既有检查被删/放宽。

## 3. 纪律
只读为主；**唯一**允许的改动是 §2.3 的植入（必须逐字节恢复并三法证明）。
**绝不占用/探测 9877**（含"不要运行 `mcp032…`"，因为它用 9877）；自用端口只用 9888/9889 并收尾复核释放。
串行构建、不抑制输出；不改 hof-rs 侧；不 `push`、不 stage；不联网（回环除外）。**不要修任何你发现的问题。**

## 4. 结构化结论（写进报告 §1）
```json
{ "verdict": "pass" | "fail",
  "criteria": [ { "id": "DECOUPLED|BEHAVIOUR_IDENTICAL|NON_VACUITY|GATES.10|G09.GUARDRAILS|PROVENANCE|ARTIFACT.UNTOUCHED|SCRIPTS.SCOPE|GUARDS",
                  "pass": true, "evidence": "命令 + 真实输出 + 文件:行" } ],
  "defects": [ { "id": "DEF-x", "severity": "blocker|major|minor|info", "what": "...", "reproduction": "..." } ],
  "risks": [ "..." ], "unverified": [ "..." ] }
```
`verdict=fail` 门槛：去耦不成立、**行为不一致**、某门红、任一植入不红、§2.5 三条件任一不成立、
工件被重生成、或原始工件被动过。

## 5. 报告必含小节
1. 结构化结论 + 真实命令与退出码；2. 逐项核对表；3. **反例清单**；4. 对"行为逐字节相同"的独立结论；
5. 未验证项与理由；6. 你没有独立复核的部分；7. 给下一批的建议（**不要**自己改代码）。

**回报给父代理只有一行：报告文件路径。**
