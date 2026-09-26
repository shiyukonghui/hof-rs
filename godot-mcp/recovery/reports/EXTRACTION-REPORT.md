# EXTRACTION-REPORT — TASK-078：从会话记录抽取全部文件载荷到 C: 暂存区

> 报告绝对路径：`C:\Users\wyl\AppData\Local\Temp\mcp-recovery\EXTRACTION-REPORT.md`
> 清单：`C:\Users\wyl\AppData\Local\Temp\mcp-recovery\EXTRACTION-MANIFEST.md`
> 暂存区：`C:\Users\wyl\AppData\Local\Temp\mcp-recovery\staging\`
> 本阶段**只做抽取与对账**：没有重建、没有编译、没有跑门、没有在 F: 上做任何写入。

---

## 0. 结论摘要（TL;DR）

1. **三件套 / 六个工具脚本 / 引擎补丁的改动点都有载荷**；其中五个工具脚本可完整还原、一个（`check_hardcoded_counts.py`）为 read 重建但 100% 行覆盖。
2. **契约 `tools_list.renamed.json` 的最后一次生成在记录里**（`exit=0`，`output tools = 177`，`added = 6` 且给出六个名字），且**最终版本 `_meta` 的两行被 read 直接命中**：`"count": 177` / `"added_count": 6`。但契约本身从未被 `write`/`edit`，读覆盖只有 20.3% → **必须按 RECOVERY-PLAN §4.2 用生成器重跑**。
3. **生成器 `gen_renamed_contract.py` 的最终版逐字还原失败**：机制（`ADDED_TOOLS` / `ADDED_VERB_EXTENSIONS`）都在，23 次版本 bump 也全在记录里（`1.0.0 → 1.22.0`），但 125 次 `edit` 重放有 **47 次 old-not-found**（多次 bump 走了 term 一次性脚本，没有 write/edit 载荷）→ 重放文件里 `GENERATOR_VERSION` 停在 `"1.3.0"`。**最终值 `1.22.0` 有直接证据，但文件要重写。**
4. **三个引擎补丁的每一个改动点都能定位**（`edit` 的 old/new 逐字 + `git show <sha> -- <文件>` 的 diff 载荷），但**改后的引擎文件本体不可还原**：5 个引擎文件 **0 个 write 载荷**（它们来自 git clone），read 覆盖 7.6%–51.3%。
5. **不可恢复**：`.git` 全部对象/历史、`bin/` 二进制、只以"命令+退出码"出现的中间态、以及至少 **516 个曾在树里出现过但从未被 read/write 的文件**（其中 511 个是 `docs/reports/evidence/**` 的请求/响应 JSON）。
6. **F: 零写入**：开工与收尾两次只读核对完全一致（见 §6）。

---

## 1. 输入与记录格式（先探明格式，再动手）

| 项 | 值 |
|---|---|
| 记录目录 | `C:\Users\wyl\AppData\Local\Temp\mcp-recovery\transcripts\*.jsonl` |
| 文件数 / 字节 | **178 份 / 594,263,811 B**（任务书写的 566.7 MB 是 MiB 口径） |
| 记录条数 | 145,614 行 JSON |
| 会话数 | 178（全部 `cwd = F:\moonbit-hof-rs`，含主会话与子代理会话，`origin` 有 `subagent`） |

**格式**：每行一个 JSON 对象，`{type, seq, time, data}`。

* `session`：`{id, createdAt, cwd, parentSession, origin, delegationDepth, agentPreset}`。
* `tool/call`：`data = {turn, step, callId, name, arguments(JSON 字符串)}`；`seq` 单调、`time` 为 epoch ms。
* `tool/result`：`data.message.source.callId` 反查调用；文本在 `data.message.content[0].content[0].text`。
  * `read` 的结果**带结构化 `meta`**：`{path, offset, totalLines, lang?, lines:[{number,text}]}` → 还原无需解析 `N: 文本` 前缀，且能精确知道**缺哪些行**。
  * 行文本**不含 CR**（抽样 2001 条 read 全为 LF）→ 统一按 `\n` 拼行。
* 工具调用计数（全量）：`term` 11865、`read` 6118、`edit` 5601、`grep` 2550、`write` 1742、`job_output` 1379、`glob` 233、`workflow` 131、其余零星。

---

## 2. 抽取方法（可复算）

流水线（脚本全部在 `scripts\`，可重跑；均为**只读 transcripts + 只写 C: 恢复目录**）：

| 阶段 | 脚本 | 产物 |
|---|---|---|
| 探明格式 | `recon.py`、`probe_format.py`、`probe_read.py`、`probe_cr.py` | 控制台证据 |
| ① 分门别类落盘 | `extract_pass1.py` | `work\events-{write,edit,read,diff,termfile,termdump,termlog,misc}.jsonl` |
| ② 重建文件版本 | `extract_pass2_v3.py` | `staging\**`、`staging\__history\**`、`staging\__candidates\**`、`work\reconstruction.jsonl` |
| ③ 差异类 | `extract_pass2b_diffs_v2.py` | `staging\__diffs\**`（每个命令一份 `.diff` + `.cmd.txt`，含 `INDEX.md`） |
| ④ 客观校验并换候选 | `fix_candidates.py`、`check_py_syntax.py`、`parse_check_ps1.ps1` | `work\swaps.json`、`work\ps1-parse.json` |
| ⑤ 清单 | `build_manifest.py` | `EXTRACTION-MANIFEST.md` |
| ⑥ 对账 | `reconcile.py`、`find_tokens.py`、`probe_genruns.py`、`probe_genver.py`、`compare_module_listing.py` | 本报告 §5、§7 |

**两个候选，一个裁判：**

* **候选 A `write-chain`**：按 `(time, seq, transcript)` 全局定序，`write` 载荷作基、`edit` 的 old→new 逐条前向重放。
* **候选 E `read-epoch`**：把该路径的全部 read 窗口**从新到旧贪心接受**，与已接受内容**冲突的旧窗口整条丢弃**（不按行号硬拼）→ 得到"版本自洽"的快照；再把**该快照最新一次读之后**发生的 edit 前向应用。
* **选择规则**：A 零失败 → 用 A（高）；A 有失败且 E 覆盖 ≥60% → 用 E（中）；否则 A（低）。若存在**更晚的一次完整 read**，以它为准或用作 A 的验证。
* **客观裁判**：`.py` 用 `ast.parse`（staged 失败而候选能解析 → 换），`.ps1` 用 `[Parser]::ParseFile`（只解析、不执行）。两处依此换了候选：`gen_renamed_contract.py`、`check_narrowing_points.py` 从 `read-epoch` 换成 `write-chain`（其余 Python 453 份解析通过）。
* **不静默丢弃**：每个被覆盖的历史版本进 `__history\<path>\<NNNN>_<来源>_seq<S>_<sha8>.bak`；两个候选不一致时，落选那份进 `__candidates\<path>.{write-chain,read-epoch}.txt`。

**去重**：read 事件按 `(记录文件, seq, callId, offset)` 去重，删掉 305 条重复行（同一结果的重复落盘）。

---

## 3. 暂存区结构与体量

```
staging\
  modules\mcp_server\**            703 路径 / 699 已落盘 / 12,295,107 B（高353 中309 低41）
  core\ editor\ modules\mono\ …    引擎与其它仓库内文件（按 F:\…\code\godot\ 相对结构镜像）
  __history\<path>\<NNNN>_…bak     4,543 份 / 203,569,900 B   ← 所有被取代的历史版本
  __candidates\<path>.*.txt        296 份 / 5,746,569 B       ← 落选候选
  __diffs\<target>\<NNNN>_….diff   3,733 份 / 4,209,631 B     ← 差异类（含 INDEX.md）
  __payload-index\                 13 份 / 109,952,083 B      ← 机器可读原始 spool + README
  __external\<盘><绝对路径>         1,371 份 / 7,218,375 B     ← 仓库外载荷（%TEMP% 一次性脚本、hof-rs 等）
  （staging 顶层还有 14 个仓库根文件：SConstruct、build-m0.cmd、version.py …）
  合计 10,861 文件 / 344,073,509 B
```

| 指标 | 值 |
|---|---|
| 有载荷的不同路径 | **2,315** |
| 已落盘文件 | **2,276** |
| 仓库内路径（相对被删树） | 909 |
| 仓库外路径 | 1,406 |
| 置信度 高 / 中 / 低 | **1,278 / 940 / 97** |
| 完全无载荷 | 39 |
| 缺尾部（`tail=yes`）/ 只缺中段 | 192 / 56 |
| `.ps1` 解析出错 | 10（其中 8 在 `modules\mcp_server` 内：`scripts\` 7 份 + `docs\reports\evidence\task060\trace-recovered\scripts\mcp060_lib.ps1`） |
| `.py` 解析失败 | 3 |

---

## 4. 逐条回答 §2.5

### ① `tools_list.renamed.json` 的最后一次生成 + `_meta.count` / `added_count`

**最后生成：在记录里。** 记录 `time=1790346784653, seq=267`（transcript `7ceecdb8-…` / `bd7065ac-…` 期间）：

```
mkdir "%TEMP%\t076" 2>nul & python scripts\gen_renamed_contract.py > "%TEMP%\t076\gen.txt" 2>&1 & echo EXIT=%ERRORLEVEL% & type "%TEMP%\t076\gen.txt"
--- 输出（原文照录）---
EXIT=0
gen_renamed_contract: input tools = 174
gen_renamed_contract: output tools = 177
gen_renamed_contract: order_normative = false (order is not part of the contract)
gen_renamed_contract: merged = 1 (get_editor_performance -> get_performance_monitors)
gen_renamed_contract: unregister = 2 (navigate_to, export_project)
gen_renamed_contract: added = 6 (project_build_csharp, project_write_text_file, project_validate_scripts, editor_set_node_script_batch, editor_set_node_property_updates, project_read_text_file)
```

**`_meta.count = 177`、`added_count = 6`：有直接载荷证据**（不是叙述，是对**最终 4174 行版本**的 read）：

```
time=1790348432461 seq=295  offset=3864 totalLines=4174  （同一份 4174 行契约的最后几次读取之一）
  3930:     "tool_count_in": 174,
  3931:     "count": 177,
  3932:     "added_count": 6,
  3933:     "added_tools": [
```

旁证（同一批，均为被测工具自身输出）：

* `time=1790347606822`：`contract entries = 177 / _meta.count = 177 / _meta.added_count = 6 / _meta.generator_ver…`
* `time=1790348191550`：`contract: entries=177  _meta.count=177  added_count=6  overrides=36  generator_version=1.22.0`
* `time=1790349141268`：`python -c "...len(d['result']['tools'])..."` → `177`（删除前最后一次直接读契约）。

**结论**：177 / 6 两个数字成立，且**证据是载荷与本机命令输出**，与 `DECISIONS.md` 的 `177 = 171 + 6` 一致（171 是移植条目数，未在本任务核对范围内）。
**注意**：契约文件**没有任何 write/edit 载荷**（`n_write=0, n_edit=0`），read 覆盖仅 **20.3%**（`staging\modules\mcp_server\docs\tools_list.renamed.json` 是片段）。所以**契约正文必须重跑生成器**，不能用暂存副本冒充。

### ② `gen_renamed_contract.py` 最终版能否还原

| 检查项 | 结果 | 证据 |
|---|---|---|
| 含 `ADDED_TOOLS` | **是**（重放文件内 9 处） | `staging\modules\mcp_server\scripts\gen_renamed_contract.py:1238` |
| 含 `ADDED_VERB_EXTENSIONS` | **是**（6 处，含定义 + 校验） | 同上 `:1535` |
| 版本常量 ≥ `1.22.0` | **记录里有最终值，但重放文件里没有** | 最后一条 bump：`time=1790346756470 seq=236` `GENERATOR_VERSION = "1.21.0"` → `"1.22.0"`；另有 `git show e8c2ed5993` 的 diff 载荷 `time=1790348580744` 逐字出现 `-GENERATOR_VERSION = "1.21.0"` / `+GENERATOR_VERSION = "1.22.0"`。重放文件里是 `GENERATOR_VERSION = "1.3.0"`（`:500`）。 |
| 逐字还原最终文件 | **不能** | 125 次 edit 中 **47 次 old-not-found**；23 次 bump 在记录里连续无缺口（`1.0.0→…→1.22.0`，`work\` 证据见 `reconcile.py` Q2），说明**中间多次修改走了 term 一次性脚本**（无 write/edit 载荷）→ 链断。read-epoch 候选覆盖 75% 但按行号拼接会重复整块（`def main` 出现 3 次），`ast.parse` 失败。 |

**结论**：**机制结构可还原（据此可重写），最终文件不可逐字还原**。落盘的是 `write-chain` 候选（`ast.parse` 通过、含两个机制、122 KB 级），置信度**低**，已在清单 §7 风险表登记；`read-epoch` 候选留在 `__candidates\`。

### ③ 三个引擎补丁的改动点能否从差异类载荷定位

**能——五处改动点全部可定位（逐字），但文件本体不可还原。**

| 文件 | 改动点 | `edit` 载荷 | `diff` 载荷 |
|---|---|---|---|
| `core/config/project_settings.cpp` | `save_custom_section` / `_save_custom_section_bnd` / ClassDB 绑定 / `update_settings_section_text` / `publish_settings_sections_text` / `_collect_settings_for_save` | **10 条**：`t=1790271677977 s393`、`t=1790271681378 s398`、`t=1790271691076 s415`、`t=1790271928080 s574`、`t=1790274812723 s1019`、`t=1790308408468 s414`、`t=1790308412442 s419`、`t=1790308455650 s424`、`t=1790308492323 s449`、`t=1790308496680 s454` | `__diffs\__root__\godot\core\config\project_settings.cpp\0442_t1790307850505_seq92.diff`（`git show 96f631addb`，第 389/486/491/503 行给出完整 `+save_custom_section` 实现与绑定）；`_unparsed\godot\0267_t1790323626145_seq98.diff` 给出补丁 3 的 hunk 头 `@@ -1714,24 +1740,14 @@ Error ProjectSettings::save_custom_section…` |
| `core/config/project_settings.h` | 三个新方法声明 | **5 条**：`s383 / s388 / s404 / s409 / s444`（`save_custom_section`、`save_preserving_text`、`publish_settings_sections_text`） | `__diffs\__root__\godot\core\config\project_settings.h\1269_t1790277003381_seq58.diff`（`git show 96f631addb`，第 23/59/60 行给出 `+Error _save_custom_section_bnd(…)`、`+Error save_custom_section(…)`） |
| `editor/editor_node.cpp` | 开窗保存调用点 | **3 条**：`s429`（`!cmdline_mode` 注释块）、`s434`（`project_settings_path` 存在性判断）、`s439`（`save_preserving_text()` 分支） | `_unparsed\godot\0071_t1790325442684_seq403.diff`（`git show 2f85141a74 -- editor/editor_node.cpp`，含 `+ ProjectSettings::get_singleton()->save_preserving_text();`）；`_unparsed\godot\0069_t1790324845152_seq185.diff` 给出 `:1071 → :1085-1088` 的行号定位 |
| `modules/mono/csharp_script.h` | 只读访问器声明 | **1 条**：`t=1790262732846 s215` | `__diffs\__root__\godot\modules\mono\csharp_script.cpp\__root__\godot\modules\mono\csharp_script.h\0266_t1790323617976_seq93.diff`（`git show 5f3e7fb441`，`+ bool is_source_newer_than_assembly() const;`） |
| `modules/mono/csharp_script.cpp` | 函数体 + 调用点 | **2 条**：`t=1790262732882 s217`（`+bool CSharpScript::is_source_newer_than_assembly() const {`）、`t=1790262736791 s222`（`if (is_source_newer_than_assembly()) {`） | 同上 `0266_…diff`：`+bool CSharpScript::is_source_newer_than_assembly() const {`、`+ if (is_source_newer_than_assembly()) {` |

**但**（这是本阶段必须说清的坏消息）：这 5 个文件**一个 write 载荷都没有**（引擎树来自 `git clone`，从未由 write 工具创建），read 覆盖 `project_settings.cpp 32.6%`、`project_settings.h 48.6%`、`editor_node.cpp 7.6%`、`csharp_script.cpp 17.2%`、`csharp_script.h 51.3%` → 暂存区里的这几个文件是**碎片拼块**（置信度 中/低，`tail=yes`），**不能当基线用**。重放补丁的正确做法的下一步：先用 `%TEMP%\audit002\tree\` 之类的**引擎旧树**做基线（RECOVERY-PLAN §2 已列），再按上表的 old/new 前向重放。

### ④ 六个工具脚本能否还原

**能。六个全部落盘、`tail=no`（完整）、语法校验干净。**

| 脚本 | 落盘大小 | 行数 | 候选 | 置信度 | 校验 |
|---|---|---|---|---|---|
| `scripts\check_engine_anchor.ps1` | 21,235 B | 431 | read-complete | 中 | PS 解析错误 **0** |
| `scripts\mcp_evidence_guard.ps1` | 44,890 B | 878 | write-chain | **高** | PS 解析错误 **0**（26 次 edit 全部应用成功） |
| `scripts\mcp_watch_run.ps1` | 15,879 B | 407 | read-complete | 中 | PS 解析错误 **0** |
| `scripts\check_exit_propagation.py` | 16,260 B | 374 | write-chain | **高** | `ast.parse` **OK** |
| `scripts\check_tautologies.py` | 12,880 B | 303 | read-complete | 中 | `ast.parse` **OK** |
| `scripts\check_hardcoded_counts.py` | 10,174 B | 257 | read-epoch（读覆盖 **100%**） | 中 | `ast.parse` **OK** |

旁证：`check_exit_propagation.py` 另有 `%TEMP%\mcp069\draft\` 的草稿双胞胎（已落 `staging\__external\…\mcp069\draft\check_exit_propagation.py`，16,423 B），两份可互校。

---

## 5. §2.6 不可恢复项（明确写出）

1. **`.git` 全部历史**：分支、对象、`git log` 实体、提交树都不可还原。记录里只有 `git show <sha>` / `git log --oneline` 的**文本输出**与 sha（如 `96f631addb`、`2f85141a74`、`5f3e7fb441`、`e8c2ed5993`、`d652a43a35`），**没有对象**。`feature/mcp-server-module` 分支与各 sha 只能作为重放后的校验目标。
2. **`bin\` 二进制**：`godot.windows.editor.x86_64[.mono].exe`（186/187 MB）等无任何载荷。（`%TEMP%` 里有 09-22…09-24 的旧构建，但那是**另一来源**，不是本次记录抽取的产物。）
3. **只以"命令 + 退出码"出现的中间态**：例如把输出重定向到 `%TEMP%\t076_meta.txt` 后再没回显的那些命令（`t=1790346669465 s131`、`t=1790346673530 s141`）；这类输出只留下"命令 + `(no output)`"。`work\events-termlog.jsonl`（11,925 条）登记了全部命令与其输出长度，可用于核对哪些输出缺失。
4. **从未被 read/write/edit 触及的文件（至少 516 个）**：以 TASK-068 时点的一次 `Get-ChildItem modules\mcp_server -Recurse -File` 清单（819 条）与被抽取集合比对，**516 条完全没有载荷**：
   * **511 条**是 `docs\reports\evidence\**` 的请求/响应 JSON（`racing\0012-*` 之类，成对的 `.request.json` / `.response.json`）；
   * 3 条 `scripts\__pycache__\*`、1 条 `__pycache__\config.cpython-39.pyc`、1 条被截断的路径名。
   * 明细：`work\module-listing-missing.txt`。**该清单本身可能被截断（822 行 vs 解析 819 条），所以 516 是下界。**
   * 反向：暂存区有 400 个 `modules\mcp_server` 路径不在这份清单里 → 它们是 TASK-068 之后才产生的（说明证据区在事故前仍在增长）。
5. **引擎基线**：见 §4③ —— 5 个引擎文件只有改动点，没有可用的完整文件。
6. **读覆盖不足的"热文件"**（重放失败率高的）：`tests\test_mcp_server.h`（29,110 行、读覆盖 72.6%、**793 次 edit 中 456 次重放失败**）、`docs\DESIGN-DETAIL.md`（50 次 edit 全失败且无 read）、`tools\registration.cpp`（42 次 edit 全失败）、`scripts\accept_m1.ps1`（10 处 PS 解析错误，已从 write-chain 换到 read-epoch）、`tools\tool_helpers.cpp`（135 次 edit 3 次失败）、`scripts\mcp066b_run.ps1`（1 次失败 → 低）。**这些是"碎片可用、整文件不可信"。**
7. **被 term 一次性脚本改写过的文件**：任何没有 write/edit 载荷却内容变了的文件（典型是版本 bump、批量替换）→ 重放链断裂。清单 §7 与 `reconstruction.jsonl` 的 `n_failed` 字段可筛。
8. **三个 `.py` 重建后无法解析**（无候选可换）：`modules\mono\build_scripts\build_assemblies.py`、`platform\windows\detect.py`、`methods.py`（低置信）。
9. **进程态**：编辑器运行状态、MCP 会话、门运行时的实时输出（只有被捕获成文本的日志；日志文件本身若在 `docs/reports/evidence/**` 且未被 write/read，见第 4 条）。
10. **本任务之外但相关**：`F:\moonbit-hof-rs\DECISIONS.md` 的 **D136 未落账**（事故方刻意为之以保恢复窗口）；本任务**没有**替它落账（F: 写入冻结）。建议条目文本见 §9。

---

## 6. 安全合规与 **F: 零写入** 证据

### 6.1 只读核对（开工 vs 收尾，两次完全一致）

| 对象 | 开工（首次只读核对） | 收尾（本次） | 判定 |
|---|---|---|---|
| `F:\moonbit-hof-rs` 文件数 | 11,653 | **11,653** | 一致 |
| `F:\moonbit-hof-rs` 总字节 | 7,251,171,328 | **7,251,171,328** | 一致 |
| `F:\moonbit-hof-rs` 最新 LastWriteTime | 2026-09-25 23:11:19 | **2026-09-25 23:11:19** | 一致 |
| `F:\moonbit-hof-rs\DECISIONS.md` | — | 537,251 B / mtime **2026-09-25 23:11:18** | 与仓库最新写入时间同刻，未被本任务触碰 |
| `F:\RustProjects\godot-mcp-pro\code\godot` | 存在、子项 0、递归 0、mtime 2026-09-25 23:19:49 | **存在、子项 0、递归 0、mtime 2026-09-25 23:19:49** | 一致（未新增任何文件，连探针文件也没有） |

本任务对 F: 的**全部**访问都是 `Test-Path` / `Get-Item` / `Get-ChildItem` / `Sort-Object`，**没有一次写、删、改、`git` 命令**；`git` 相关的一切都来自记录文本，没有在 F: 上执行。

### 6.2 三条硬性纪律的执行情况

1. **禁止 shell 重定向**：全流程零 `>`、`>>`、`*>`、`2>&1`。写文件只用工具自身（`write`/`edit`）、Python `open(...,'w')`/`[IO.File]::WriteAllText`/`Out-File -FilePath`/`Set-Content`。已对 `scripts\*.ps1` 静态复核：**non-ASCII = 0、重定向 = 0**。（工作记录里出现过 `>` 字符的 8 个文件全在**原记录的命令文本**里，不是本任务执行的命令。）
2. **破坏性命令默认拒绝**：全程只执行过 **2 次** `Remove-Item`，都在 `scripts\reset_staging.ps1` 里，且该脚本先断言：目标非空、绝对路径、**以 `C:\Users\wyl\AppData\Local\Temp\mcp-recovery\` 开头**、无通配符、无 `..`、非盘根/用户根；**先打印完整清单**再删。
   * 第 1 次：`staging\` 10,581 文件 / 228,940,865 B（v1 产物，被 v2 取代）。
   * 第 2 次：`staging\` 11,935 文件 / 235,272,168 B（v2 产物，被 v3 取代）。
   * 没有删过 `transcripts\`、`work\`、`scripts\`、`staging\__diffs` 之外的东西。
3. **路径全绝对、脚本纯 ASCII、不联网**：`scripts\*.ps1` 三份均纯 ASCII；Python 脚本不回显中文以外的内容；未使用 web 工具。

---

## 7. 与历史数字对账（只看载荷）与偏差登记

| 历史说法（`DECISIONS.md`，只读参考） | 载荷侧结果 | 判定 |
|---|---|---|
| 契约 `_meta.count = 177`、`added_count = 6`（D134/D135 一带） | read 直接命中最终版 4174 行的 3931/3932 行 | **一致** |
| 生成器 `1.21.0`（D134）→ `1.22.0`（D135） | 最后 bump `t=1790346756470 s236`；`git show e8c2ed5993` diff 逐字 | **一致** |
| 177 = 171 移植 + 6 新增（六个名字） | 生成器 stdout `added = 6 (六个名字)`；契约 `_meta.added_count = 6` | **一致** |
| `editor/editor_node.cpp` 调用点 `:1085-1088` | `edit` 载荷 `s429/s434/s439` + `git show 2f85141a74` diff | **一致** |
| `check_engine_anchor.ps1` / 六个脚本存在且纯 ASCII | 六份全部落盘、PS/Python 解析干净 | **一致** |
| `tools_list.renamed.json` 应当由生成器重跑得到 | 载荷里**没有** write/edit，read 覆盖 20.3% | **一致（必须重跑）** |
| 各批"门计数 / doctest 数 / 探针数" | 本阶段**不采信**、也不核对（那些是运行期数字，只有命令+输出文本） | 未核 |

**新发现的两处需要下一阶段注意的偏差：**

* `test_mcp_server.h` 在记录里有 793 次 `edit`，其中 **456 次无法重放**（多会话并行编辑 + 被 term 脚本改写），read 覆盖 72.6% → 落盘 431,976 B 的文件**不足以作为最终版本**，需要用可运行门重建。
* `docs\reports\evidence\**` 的 511 个请求/响应 JSON **从未被 read**，但其中很多原本由"证据当场复制进仓库"的脚本生成 → 需要重跑生成它们的证据脚本（那些脚本本身**在**载荷里，见 `staging\modules\mcp_server\scripts\mcp0*_evidence.ps1`）。

---

## 8. 交付物与"一次性垃圾"声明

**必需交付物**

* `C:\Users\wyl\AppData\Local\Temp\mcp-recovery\EXTRACTION-MANIFEST.md`（2,898 行 / 441,297 B；每路径一行 + 按目录汇总 + 5 个专题表 + 风险表）
* `C:\Users\wyl\AppData\Local\Temp\mcp-recovery\EXTRACTION-REPORT.md`（本文件）
* `staging\`（§3 结构；10,861 文件 / 344,073,509 B）

**中间产物（声明保留，供复算与下一阶段复用，均在 C:）**

* `work\`：8 个 spool（`events-*.jsonl`）、`reconstruction.jsonl`、`gen-runs.jsonl`、`ps1-parse.json`、`swaps.json`、`module-listing-raw.txt`、`module-listing-missing.txt`、`tree-listing.txt`。
* `scripts\`：28 份脚本（`extract_pass1.py`、`extract_pass2.py`、`extract_pass2_v2.py`、`extract_pass2_v3.py`、`extract_pass2b_diffs.py`、`extract_pass2b_diffs_v2.py`、`fix_candidates.py`、`build_manifest.py`、`reconcile.py`、`check_py_syntax.py`、`parse_check_ps1.ps1`、`reset_staging.ps1`、`copy_payload_index.ps1`、`compare_module_listing.py`、`find_tokens.py`、`inventory.py`、`audit_records.py`、`recon.py`、`probe_*.py` 等）。
  **其中 `extract_pass2.py`/`extract_pass2_v2.py`/`extract_pass2b_diffs.py` 是 v1/v2 代脚本，已被 v3 取代，保留仅为可追溯，勿再运行。**
* `staging\__candidates\`、`staging\__payload-index\`（已在清单 §10 声明）。

**没有留下未声明的东西**：除以上之外，`mcp-recovery\` 下只有原有的 `transcripts\`、`RECOVERY-PLAN.md`、`TASK-078-extract.md` 三份输入。

---

## 9. 给下一阶段（不是本阶段执行）

1. **基线优先**：引擎三种补丁先用 `%TEMP%\audit002\tree\`（早期全树、无 `.git`）与 `%TEMP%\mcp044-module-backup\`（模块旧快照）做基线，再按 §4③ 的 old/new 前向重放；**不要**用本暂存区里那 5 个碎片引擎文件当基线。
2. **契约重跑**：`gen_renamed_contract.py` 需按记录重写（机制 + 1.22.0 + 三个 v1.22 override），再跑生成器产出契约，并核对 `_meta.count=177 / added_count=6 / generator_version=1.22.0`（本报告已给出这三个期望值的载荷证据）。
3. **热文件重建**：`test_mcp_server.h`、`DESIGN-DETAIL.md`、`registration.cpp`、`accept_m1.ps1` 等按"碎片 + 门"重建，不要直接采信暂存字节。
4. **证据区**：`docs/reports/evidence/**` 的 511 个 JSON 需要由载荷里已有的证据脚本重跑生成。
5. **`.git`**：只能 `git init` 重新开始（`DECISIONS.md` D136 起继续记账）。

**建议的决策日志条目（因 F: 写入冻结，本任务未落账，供恢复后抄录）：**

> **D136 — TASK-078 提取阶段完成：载荷三条通道全部落袋 / 契约 177+6 有直接载荷证据 / 生成器与引擎文件只有改动点、无本体 / 至少 516 个证据 JSON 从未被 read**
> ① 178 份 / 594,263,811 B 记录 → 2,315 路径、2,276 落盘（高 1,278 / 中 940 / 低 97）、4,543 个历史版本、3,733 份 diff 载荷、296 份落选候选；
> ② `tools_list.renamed.json` 最后生成 `seq=267 EXIT=0 output tools=177 added=6`，最终版 `_meta.count=177/added_count=6` 由 read 直接命中（第 3931/3932 行）；契约本体仍需重跑；
> ③ `gen_renamed_contract.py` 23 次 bump 记录在案（`1.0.0→1.22.0`），但 125 次 edit 中 47 次无法重放（中间修改走 term 一次性脚本）→ 机制可还原、最终文件不可逐字还原；
> ④ 三个引擎补丁的 5 个文件 **0 个 write 载荷**、read 覆盖 7.6%–51.3% → 改动点可逐字定位、文件本体必须用引擎旧树作基线重放；
> ⑤ 六个工具脚本全部完整落盘、PS/Python 解析干净；
> ⑥ 不可恢复：`.git` 全部、`bin/` 二进制、命令+退出码式中间态、至少 516 个从未被 read 的文件（511 个是 evidence JSON）；
> ⑦ **F: 零写入**（收尾核对与开工完全一致：11,653 文件 / 7,251,171,328 B / 最新 mtime 2026-09-25 23:11:19；被删树仍 0 子项）；
> ⑧ 纪律：零 shell 重定向；2 次 `Remove-Item` 均为带前缀断言 + 先打印清单的暂存区重置。

---

## 10. 一句话回答任务书的四条"返回值"

* **状态**：完成（抽取 + 对账），只在 C: 写入，F: 零写入。
* **staging 汇总**：2,276 个文件落盘 / 2,315 路径 / 高 1,278·中 940·低 97；`__history` 4,543、`__diffs` 3,733、`__candidates` 296、`__payload-index` 13。
* **契约**：最后生成在记录里（`EXIT=0`，`output tools=177`，`added=6`），最终版 `_meta.count=177`、`added_count=6` 有 read 直证；正文需重跑。
* **生成器**：`ADDED_TOOLS`/`ADDED_VERB_EXTENSIONS` 可还原；`1.22.0` 在记录里；**最终文件不可逐字还原**（47/125 重放失败，常量停在 1.3.0）。
* **引擎补丁**：5 个文件 5 处改动点全部可定位（edit + git show 载荷）；文件本体不可还原（0 write、读覆盖 7.6%–51.3%）。
* **工具脚本**：六个全部完整、解析干净。
* **不可恢复**：`.git`、`bin/`、命令+退出码中间态、≥516 个未被 read 的文件、引擎基线、若干热文件整版。
* **F: 证据**：开工/收尾两次只读核对逐项一致（见 §6.1）。
