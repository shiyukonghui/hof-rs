# TASK-154-ACCEPT — TASK-154（引擎侧收尾：脚本去跨仓 + 端口守卫 + 历史说明）独立验收

> 你是**独立验收子代理**。不得继承实现者或调度者的结论。
> 实现者报告：`godot-mcp/recovery/reports/TASK-154-REPORT.md`（**线索，非证据**）。
> 产物：`godot-mcp/recovery/reports/TASK-154-ACCEPTANCE.md`；自产证据放 `godot-mcp/recovery/work/task154-acc/`。
> 被测：引擎仓 `godot-mcp/godot` HEAD **`fc63af77c3`**（4 提交，基线 `28432f859f`）；外层仓 `godot-mcp/**`。

## 1. 先读
`recovery/tasks/TASK-154.md` → `reports/TASK-154-REPORT.md` → `DECISIONS.md` **D230/D232/D233**
→ 两个被改脚本（`modules/mcp_server/scripts/mcp029_clear_default_evidence.ps1`、`mcp032_d3_d4_d6_evidence.ps1`）
→ `docs/MCP-SERVER-HANDOVER.md` §3.10。

## 2. 核心复核项（逐条自己复现，给命令 + 原始输出 + 文件:行）

1. **去跨仓是否真成立**：两个脚本的**非注释**处是否**不再指向 hof-rs**（自己 grep + 判读逻辑分支；
   唯一允许的是两处**拒绝 9877** 的正则字面量 `[regex]::Escape('9877')`，请确认它们只用于**拒绝**）。
   并核实 `mcp032` 已**不再** dot-source `mcp_port_guard.ps1`，而该模块**本身未被改动**且仍被其它脚本引用。
2. **端口守卫（§2.2 选 b）**：自己跑 `-EditorPort 9877` 与 `-GamePort 9877` ⇒ 应 **exit 4**、
   **在任何进程/网络动作之前**、且 **OutRoot 未被创建**。并抽查 `9870..9889` 收尾**无 LISTENING**。
   **绝不允许**你自己去绑定/探测 9877（脚本的拒绝路径不算探测，但请以证据表明"零网络调用"）。
3. **§2.3**：`docs/tools_list.renamed.json` 是否**未被重生成**（blob `3b1b191d`、154272 B、
   sha256 `fd00c75e…`，且与 `28432f859f` 时相同）；HANDOVER 的历史说明是否**只改文档**、措辞是否**不把未发生的事写成事实**。
4. **十道门**：用外层仓 `godot-mcp/tools/run_gates.ps1 -RunGates` 自跑（CWD 外层仓；
   **注意**：对 `git -C F:\moonbit-hof-rs` 传 `tools/run_gates.ps1` 会**静默匹配不到**——那是假绿陷阱）。
   应 **10/10 exit 0**、`g05` **30 PASS / 0 FAIL**、`g04` 3/3（154/73/177）、`g08` UNCLASSIFIED=0、
   `g10` 22/22；`g09` 按现行判据（`RED_COUNT=0`）。
   `g08` 计数面变到 126→130 请**自行判定**是否只是"新注释含 TASK 编号字面量"而无分类漏网。
5. **两个 pre-existing 红点的归因（必须独立判定，别照抄）**：
   ①`mcp032` 的 `-f` 花括号崩溃（`{'Material','material'}` 等，共 6 处）是否**真早于本批**
   （查区间 hunk、`git log`/`git log -S`）；②`mcp029` 的两处内容级红（活体报 `clear.default=true` + 8 字符描述）
   与 `mcp032` 的 D6 两处红，是否**确实不是本批引入**、且**冻结契约从未携带**相应文本。
   **若你判定其中任一为本批引入 ⇒ 判 fail。**
6. **`g09` 护栏 3 现在仍是人工项**：请给出那三个文件的**有效** `git diff` 为空的证据
   （注意上面那个 pathspec 陷阱：先证明 pathspec 能命中，例如用绝对路径或 `--stat` 出现文件名）。
7. **复核纪律（两个陷阱，务必在报告里给结论）**：
   ①`cmd /c git cat-file blob db2eed7^:…` 的 `^` 被 cmd 转义 ⇒ **静默解析成 HEAD**；
   ②`git diff` 对**不存在的 pathspec 不报错** ⇒ 假绿。请各自**实测复现**并说明正确读法。
8. **编码安全**：两个被改脚本是否仍 **0 个非 ASCII 字节、无 BOM**（PS 5.1 按 gb2312 读它们）；
   `mcp029` 的 `[char]0x5171` 转义是否仍在**注释行内**、脚本回放是否正常。
9. **禁区自查**：未 `push`（`origin` 应仍 `28432f859f`）；hof-rs 追踪文件零改动、夹具仍 `50c5fb42…`/71481 B；
   无新依赖；无既有检查被删/放宽；**未编造**任何日期或溯源。

## 3. 纪律
只读为主；**唯一**允许的改动是 §2.2/§2.7 的**受控实验**（若你为复现陷阱而临时改动，必须逐字节恢复并三法证明）。
**绝不占用/探测 9877**；只用测试端口 9888/9889 并收尾复核释放。串行构建、不抑制输出；不改 hof-rs 侧；
不 `push`、不 stage；不联网（回环除外）。**不要修任何你发现的问题。**

## 4. 结构化结论（写进报告 §1）
```json
{ "verdict": "pass" | "fail",
  "criteria": [ { "id": "DECOUPLED|PORT_GUARD|ARTIFACT_UNTOUCHED|GATES.10|PREEXISTING_ATTRIBUTION|G09.HUMAN_GUARDRAIL|TRAPS|ENCODING|GUARDS",
                  "pass": true, "evidence": "..." } ],
  "defects": [ { "id": "DEF-x", "severity": "blocker|major|minor|info", "what": "...", "reproduction": "..." } ],
  "risks": [ "..." ], "unverified": [ "..." ] }
```
`verdict=fail` 门槛：去跨仓不成立、端口守卫可被绕过（或实际碰了 9877）、工件被重生成、某门红、
**任一 pre-existing 红点被判定为本批引入**、或原始工件被动过。

## 5. 报告必含小节
1. 结构化结论 + 真实命令与退出码；2. 逐项核对表；3. **反例清单**；4. 两个陷阱的实测复现与正确读法；
5. 两个 pre-existing 红点的**独立归因结论**；6. 未验证项与理由；7. 你没有独立复核的部分；8. 给下一批的建议（**不要**自己改代码）。

**回报给父代理只有一行：报告文件路径。**
