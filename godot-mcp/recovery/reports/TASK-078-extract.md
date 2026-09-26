# TASK-078 — **恢复·提取阶段**：从会话记录抽取全部文件载荷到 **C: 暂存区**（**绝不写 F:**）

> 背景：`F:\RustProjects\godot-mcp-pro\code\godot` 被误删（详见 `C:\Users\wyl\AppData\Local\Temp\mcp-recovery\RECOVERY-PLAN.md`）。
> **F: 处于写入冻结**：本任务**只允许**在 `C:\Users\wyl\AppData\Local\Temp\mcp-recovery\` 下读写。
> 报告（**绝对路径**）`C:\Users\wyl\AppData\Local\Temp\mcp-recovery\EXTRACTION-REPORT.md`。返回值 **≤10 行**。

## 0. 硬性安全规则（**违反即任务失败**）

1. **绝不在 F: 上创建/修改/删除任何文件**（包括 `F:\moonbit-hof-rs`、包括"顺手提交"）。开工前 `Test-Path F:\` 之后**只读**；收尾核对 F: 未被触碰。
2. **禁止一切 shell 重定向**：不得使用 `>`、`>>`、`*>`、`2>&1`、`|`（管道用于**只读筛选**可，但**写文件一律**用 `Set-Content`/`Out-File -FilePath`/`[IO.File]::WriteAllBytes`/Python 的 `open(...,'wb')`）。
3. **破坏性命令安全**：任何 `Remove-Item`/`Move-Item`/`del` **必须**：目标**非空、绝对路径、以 `C:\Users\wyl\AppData\Local\Temp\mcp-recovery\` 开头**；**先打印将删清单**；参数含通配符或 `..` 或为空 → **直接 `throw`**。**默认拒绝**。
4. 全部路径**绝对**；脚本 `.ps1` 纯 ASCII；不联网。

## 1. 输入

- 已解压记录：`C:\Users\wyl\AppData\Local\Temp\mcp-recovery\transcripts\*.jsonl`（**178 份 / 566.7 MB**，来源 `.dsh` 会话的 `session.v3.jsonl.zstd`）。
- 同步事实源（**用于对照与验证，不要照抄结论**）：`F:\moonbit-hof-rs\DECISIONS.md`（D1–D135，**只读**）——里面有每批的契约 sha、门计数、探针数等**确切数字**。

## 2. 要做的事

1. **先探明记录格式**（先读 1–2 份 `.jsonl` 的少量行）：确认工具调用记录的字段结构（工具名、参数、结果、时间戳/序号、会话/代理标识）。
2. **抽取三类载荷**到 `C:\Users\wyl\AppData\Local\Temp\mcp-recovery\staging\`（**保持原目录结构**）：
   - **写类**：`write`/`edit`（含 `create`）的**目标路径 + 内容**（`edit` 需把 patch 应用到该路径**该时刻**的版本上）；
   - **读类**：`read` 的**行号内容**（去行号还原原文）；
   - **差异类**：`git diff` / `git show` / `git status` 的输出（用于重放**三个引擎补丁**）。
3. **定序与冲突解决**：同一路径多次出现时，**按时间戳/序号取最后版本**，并把**所有版本**存进
   `staging\__history\<path>\<序号>.bak`（便于回溯）。**不得**静默丢弃旧版本。
4. **产出清单**（这是本阶段最重要的产物）`C:\...\mcp-recovery\EXTRACTION-MANIFEST.md`：
   每个路径一行：`path | 来源(记录文件 + 序号/时间) | 置信度(高=直接 write | 中=从 read 还原 | 低=仅 diff/片段) | 字节数 | 是否缺尾部`；
   并按目录汇总（`modules/mcp_server/tools`、`scripts`、`tests`、`docs/reports`、`docs/reports/evidence`、契约三件套、引擎补丁文件）。
5. **与历史数字对账**（**不得采信记录中的叙述，只看载荷**）：
   ①`tools_list.renamed.json` 的最后一次生成是否出现在记录里？其 `_meta.count` 是 **177**、`added_count` **6** 吗？
   ②`gen_renamed_contract.py` 的最终版本能否还原（检查是否含 `ADDED_TOOLS` / `ADDED_VERB_EXTENSIONS` / 版本常量 **1.22.0** 或更高）？
   ③三个引擎补丁的改动点是否都能从 diff 类载荷中定位（`core/config/project_settings.{h,cpp}` 的 `save_custom_section`/`save_preserving_text`、
      `editor/editor_node.cpp` 的调用点、`modules/mono/csharp_script.{h,cpp}` 的 `is_source_newer_than_assembly`）？
   ④`check_engine_anchor.ps1`、`mcp_evidence_guard.ps1`、`mcp_watch_run.ps1`、`check_exit_propagation.py`、`check_tautologies.py`、
      `check_hardcoded_counts.py` 这六个**工具脚本**能否还原？
6. **明确写出不可恢复项**（例如：`.git` 历史、`bin/` 二进制、只在命令+退出码里出现的中间态、被 edit 前的原始大文件若从未被 read 过）。

## 3. 完成标准

- `staging\` 有结构化的文件树；`EXTRACTION-MANIFEST.md` 有每文件来源与置信度；`EXTRACTION-REPORT.md` 逐条回答 §2.5 的四个问题与 §2.6 的缺口清单。
- **F: 零写入**（给收尾核对证据）；不留任何未声明的一次性垃圾（要留就写清单）。
- **不要**尝试重建/编译/跑门——那是下一阶段的事；本阶段只做**抽取与对账**。
