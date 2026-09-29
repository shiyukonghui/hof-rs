# TASK-154 — 引擎侧收尾：两个历史取证脚本去跨仓引用 + `_meta` 历史说明（+ 可选：`g09` 护栏机器化）

> 你是**实现子代理**，无上游对话上下文；本文件是你的唯一任务来源。
> 落点：引擎仓 `F:\moonbit-hof-rs\godot-mcp\godot`（分支 `feature/mcp-server-module-rebuild`，
> 起始 HEAD `28432f859f`，工作树干净）。**已获授权改动 `modules/mcp_server/**`。**
> 门运行器在**外层仓**：`F:\moonbit-hof-rs\godot-mcp\tools\run_gates.ps1`（**不在引擎仓内**）。

---

## 0. 目标

TASK-153 之后，"**生成器 / `g05` 门**这一线"已不依赖 hof-rs。**剩下三处**收尾，做完后
"契约生成、自检、取证脚本均自包含"才可作为**事实**写入（**在此之前的任何更宽带说法都禁止**）。

## 1. 已核实的事实（别重新发现；行号已由独立验收者更正）

| 位置 | 事实 |
|---|---|
| `modules/mcp_server/scripts/mcp029_clear_default_evidence.ps1:62` | `$OldFixture` 指向 hof-rs 的 `tests/fixtures/mcp/tools_list.json` |
| `modules/mcp_server/scripts/mcp032_d3_d4_d6_evidence.ps1:63` | 同上（`$OldFixture`） |
| `modules/mcp_server/scripts/mcp032_d3_d4_d6_evidence.ps1:69` | **`$UserPort = 9877`**（硬编码；⚠ 这是决策者机器的编辑器端口） |
| 引擎内基准（**唯一正确来源**） | `modules/mcp_server/docs/rename-baseline-tools-list.json`（48749 B、174 条、sha256 `8f8051c4…`、blob `543b49b2…`） |
| 样板 | `scripts/gen_renamed_contract.py:1764/1801-1834`（TASK-153）与 `scripts/check_rename_map.py:102`（TASK-152） |
| 两个脚本**不在十门路径上** | 实测：`run_gates.ps1` 与 `accept_m1.ps1` 对它们 grep 均无命中；十门实际执行文件的"可执行跨仓引用"扫描 = **0** |
| 冻结工件 | `docs/tools_list.renamed.json` 的 `_meta.generated_from` 写 hof-rs 路径，由提交 `54200f0d77`（2026-09-26）引入 ⇒ **历史事实**，非本次引入 |

## 2. 要做什么

### 2.1 两个脚本去跨仓（必修）
- 把 `$OldFixture` 改为**引擎内**基准（用与 `gen_renamed_contract.py` / `check_rename_map.py` **一致**的
  `$PSScriptRoot`/`DOCS` 派生写法），**不得**再出现 `moonbit-hof-rs` / hof-rs 相对路径。
- **不得改变脚本"取证什么"的语义**（它们产出的证据含义必须与改前一致）。
- 若某脚本**无法**用引擎内基准等价替换（例如它取证的就是 hof-rs 侧的字面事实），**停下并在报告里说明**，
  给出你的判据与建议方案，**不要**硬改成语义不同的东西。

### 2.2 `$UserPort = 9877` 的处置（必修，二选一，说明理由）
- **(a) 参数化**：默认改为**测试端口**（如 9888），并把 9877 列为"必须显式传入才可用"的值；**或**
- **(b) 显式拒绝守卫**：脚本开头加硬守卫——若端口解析为 9877 则**立即退出并报错**，提示改用测试端口。
- 无论哪种：**不得**让该脚本存在"静默使用 9877"的路径。

### 2.3 `_meta.generated_from` 的历史说明（必修，**仅改文档**）
- 在合适位置（`MCP-SERVER-HANDOVER`、或 `docs/` 下贴近契约的说明、或已冻结工件的**旁注文档**——
  **不得**修改 `docs/tools_list.renamed.json` 本身）加一句：
  "`docs/tools_list.renamed.json` 的 `_meta.generated_from` 记录的是**生成当时**的来源（hof-rs 夹具），
  自 TASK-153 起生成器已改读引擎内基准；该字段为**历史溯源**，不代表当前输入。"
- **绝对禁止**重生成 `docs/tools_list.renamed.json`（D229 第 1 条已裁决；它的 blob/sha/字节必须与 `28432f859f` 时**完全相同**）。

### 2.4 可选（**明确可选**）：`g09` 三道护栏机器化
现判据是 `ANCHOR_EQUAL` 或 `ANCHOR_STRUCTURAL_EQUIVALENT` 且 `RED_COUNT=0`，**外加人工核验的三条**：
①区间 diff 全为 docs/scripts 且无编译输入；②编译输入区间 diff 为空；③
`check_engine_anchor.ps1` / `check_hardcoded_counts.py` / `run_gates.ps1` 零 diff。
- 若你有把握：把这三条做成判据脚本内**可复算**的规则。**必须**等价或**更严**，
  且**必须证明非空洞**（构造一个会触发它的反例并展示它变红）。
- **若做不到或会让判据变弱 ⇒ 不做**，在报告里说明并保持人工护栏。**本项不做不影响验收。**

## 3. 非空洞性与门

- **门**：用外层仓 `godot-mcp\tools\run_gates.ps1 -RunGates` 跑**十道门**，应 **10/10 exit 0**
  （`g05` 应 30 PASS/0 FAIL、`g01` 160/160、`g02` 1586/1586、`g04` 3/3=154/73/177、`g07` 10/10、
  `g08` UNCLASSIFIED=0、`g10` 22/22）；`g09` 按上述判据，并附三道护栏的核验证据。
- **若你做了 §2.4**：给它的反例证据（红→恢复）。
- **脚本改动的验证**：对 §2.1/§2.2 的每个脚本，给出"改前语义 vs 改后语义"的对照。
  **只有在不碰 9877、且能用测试端口安全运行时**才允许实际运行它们；否则**静态验证 + 明确说明未运行**。

## 4. 硬约束

- **绝不占用/探测 9877**（含：**不要**以原样运行 `mcp032…`）；自用端口只用 **9888/9889**，收尾复核已释放。
- 不改 hof-rs 侧任何文件（尤其 `tests/fixtures/mcp/tools_list.json`）；**不重生成** `docs/tools_list.renamed.json`。
- 不 `push`；逐条提交、英文信息带 `(TASK-154)`；串行构建、不抑制输出；无新依赖；
  不删/不放宽既有检查换绿；**不编造**任何日期或溯源（上一批有前科，现已列为独立验收必查项）。

## 5. 回报（**只回报报告文件路径**）

报告写到 `F:\moonbit-hof-rs\godot-mcp\recovery\reports\TASK-154-REPORT.md`，必含：
1. 结论 + 真实命令与退出码；2. 改动清单（文件:行）+ 每个脚本的"改前/改后语义"对照；
3. §2.2 你选了 (a) 还是 (b) 及理由；4. 十道门真实结果 + `g09` 三道护栏核验；
5. **若做了 §2.4**：它的非空洞反例证据；6. 禁区自查真实输出；7. 遗留风险与未验证项（区分实测/推断）；8. 诚实披露。