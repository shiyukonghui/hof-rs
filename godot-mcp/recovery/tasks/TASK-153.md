# TASK-153 — 契约生成器去跨仓耦合：`gen_renamed_contract.py` 改用引擎内基准

> 你是**实现子代理**，无上游对话上下文；本文件是你的唯一任务来源。
> 落点：引擎仓 `F:\moonbit-hof-rs\godot-mcp\godot`（分支 `feature/mcp-server-module-rebuild`，
> 起始 HEAD `bef4be0407`，工作树干净）。**已获授权改动 `modules/mcp_server/**`。**

---

## 0. 一句话目标

`modules/mcp_server/scripts/gen_renamed_contract.py` **仍然**从 **hof-rs 仓**读取旧契约基准，
并在**同一文件**里冻结了它的 sha256。**TASK-152 已让 `g05` 自包含**，但**契约生成器还没有**。
本任务把它也指到**引擎内**基准，使 **契约生成与契约自检共用同一个引擎内基准**。

> **动机（必须写进代码注释）**：一道引擎脚本**跨仓依赖另一个仓库的工作文件**，会导致该仓库**任何合法演进**
> 都让引擎侧无缘由变红——这会训练人忽略红色。TASK-152 已在 `check_rename_map.py` 上修好这一点。

---

## 1. 已核实的事实（我已独立验过，别重新发现）

- `modules/mcp_server/scripts/gen_renamed_contract.py`：
  - **`:1800`** 仍写死 `r"F:\moonbit-hof-rs\tests\fixtures\mcp\tools_list.json"`；
  - **`:1804`** 仍冻结同一个 sha256（`8f8051c4…`）。
- 引擎内已有等价基准：`modules/mcp_server/docs/rename-baseline-tools-list.json`
  （48749 B、174 条、sha256 `8f8051c4c0f8941089f0b21a193cef7c51fa7c41d7e312b1463ea8593f313c54`、
  引擎 blob `543b49b2583bf06c3aba2a320649a31eda272e3e`，与 hof-rs `db2eed7^` 的 blob **逐字节相同**）。
- 参照实现（同一次修复的**样板**）：`modules/mcp_server/scripts/check_rename_map.py:102` 起——
  它已用 `os.path.join(DOCS, "rename-baseline-tools-list.json")` 并加了 **26 行溯源注释**；
  `TASK-152` 的提交 `069a2e2ea8` / `e1fbc8ec7f` 是**可以直接照抄的范式**。
- 验收依据：`recovery/reports/TASK-152-ACCEPTANCE.md` 的 `SCOPE.HONESTY` 一节。

---

## 2. 要做什么

1. 把 `:1800` 的基准路径改为**引擎内** `docs/rename-baseline-tools-list.json`（用与
   `check_rename_map.py` **同样**的 `DOCS` 派生写法，**不得**再出现 `moonbit-hof-rs` / `hof-rs` /
   任何 hof-rs 相对路径）。
2. 在常量旁写**溯源**：路径、字节数、条数、sha256、来源（hof-rs `db2eed7^` 的 blob id）、
   采集命令、日期。**溯源必须真实**——上一批有人写了一个**编造的日期**（2026-02-15）后被自己发现改正；
   你若不确定就**别写**或写"见 commit"，**绝不许编造**。
3. **保留原有能力**：生成器对"基准与产物不一致"必须**仍然失败**。**不得**把它改成永绿或降级为警告。
4. 若生成器有 `--help`/docstring 提到那个 hof-rs 路径，一并更新（**但不得**改动它的行为契约）。

## 3. 非空洞性（硬要求）

受控实验，做完**逐字节恢复**并证明：
- 在**引擎内基准件**上植入一个真实差异（例如改掉某个 `name`，或改掉一条映射）⇒ 生成器**必须失败**
  （非零退出码或明确的失败信息，**不是**警告）；
- 恢复：`git status --porcelain` 与 `git diff --stat` **双空** + `git hash-object` == `HEAD` blob
  （仓库对 CRLF 敏感）。**若植入后仍成功 ⇒ 判 fail。**

## 4. 门与回归

- **十道门必须仍全绿**（`tools/run_gates.ps1`）。重点：`g05` 仍 **exit 0 / 30 PASS**；
  `g01` 160/160、`g02` 1586/1586、`g04` 3/3（应 154/73/177）、`g07` 10/10、`g08` UNCLASSIFIED=0、`g10` 22/22。
- **`g09` 判据（本线现行）**：`ANCHOR_EQUAL` **或** `ANCHOR_STRUCTURAL_EQUIVALENT` 且 `RED_COUNT=0`；
  且必须同时：①区间内 3 个 diff **全是 docs/scripts、无编译输入**；②`git diff <起始 HEAD>..HEAD -- <编译输入>` 为空；
  ③`check_engine_anchor.ps1` / `run_gates.ps1` / `check_hardcoded_counts.py` **零 diff**。
- **注意**：引擎构建**不是位级可复现的**，**不得**用二进制 sha 当新鲜/一致判据（用 `--version` + 测试条数 + 探针）。

## 5. 硬约束

- **绝不占用/探测 9877**；自用端口只用 **9888/9889**，收尾复核已释放。
- 不改 hof-rs 侧任何文件（尤其 `tests/fixtures/mcp/tools_list.json`）；不 `push`；逐条提交、英文信息带 `(TASK-153)`；
  串行构建、不抑制输出；不删/不放宽既有检查换绿；不新增依赖；不把"未复现"写成"已修复"。

## 6. 回报（**只回报报告文件路径**）

报告写到 `recovery/reports/TASK-153-REPORT.md`，必含：
1. 结论 + 真实命令与退出码；2. 改动清单（文件:行）+ 溯源；3. **非空洞性三步原始输出**；
4. 十道门真实结果（含 `g05` 与 `g09` 的完整判定）；5. 禁区自查真实输出；6. 遗留风险与未验证项（区分实测/推断）；
7. 诚实披露。