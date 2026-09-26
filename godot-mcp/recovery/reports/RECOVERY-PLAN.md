# 事故与恢复方案 — `F:\RustProjects\godot-mcp-pro\code\godot` 工作树被删除

> 由决策代理（D136 待落账）于事故当日编写。**本文件在 C:**，因为**对 F: 的一切写入已被冻结**。
> 冻结原因：被删数据仍在 F: 卷上，任何写入都可能覆盖可恢复簇。

## 1. 事件（已只读复核）

| 项 | 事实 |
|---|---|
| 对象 | `F:\RustProjects\godot-mcp-pro\code\godot`（引擎 fork 克隆 + 其 `.git` + `modules/mcp_server/**` + 引擎补丁 + `bin/`） |
| 现状 | **目录存在但完全为空**（实测：子项 0、递归 0） |
| 机制 | 子代理在 **cmd** 下执行 `powershell -File mcp077_live_evidence.ps1 -Phase before *> file`；**cmd 不认识 `*>`**，游离的 `*` 被绑定为脚本参数 `$OutRoot`，脚本随后 `Remove-Item -Recurse -Force $OutRoot` **清空了 CWD（仓库根）** |
| 回收站 | 无关（`F:\$Recycle.Bin` 仅 9 项 / 1441 B）→ **不是回收站删除** |
| 影子副本 | `vssadmin list shadows` 需管理员，当前会话**无权限** |
| 事故后 F: 写入 | **零**（仅只读检查：`Get-ChildItem`/`Select-String`/`git log|config|ls-files`）；`DECISIONS.md` 的 D136 **刻意未落账**，以保住恢复窗口 |
| 外层仓库 `godot-mcp-pro` | **完好**（自带 `.git`，remote `git@github.com:shiyukonghui/godot-mcp-pro.git`）；`ls-files code/godot` = **0**、无 `.gitmodules` → 引擎 fork 是**独立克隆**，外层救不了 |
| 上游 remote | `git@github.com:shiyukonghui/godot.git` 只有 `master=57277407`，**无模块分支** |
| `F:\moonbit-hof-rs\DECISIONS.md` | **完好**（537 KB，D1–D135）→ 全部决策与裁决、以及每批的实测数字都在 |
| **会话记录** | `C:\Users\wyl\.dsh\sessions\--F-moonbit-hof-rs--`：178 个 `session.v3.jsonl.zstd` / 122 MB；**已解压到 C:**（566.7 MB，178 个 `.jsonl`） |

## 2. 可恢复源清点（含能力边界）

| 源 | 位置 | 内容 | 能恢复什么 / 不能恢复什么 |
|---|---|---|---|
| **会话记录（已解压）** | `C:\Users\wyl\AppData\Local\Temp\mcp-recovery\transcripts\*.jsonl` | 566.7 MB；探针命中：`tools_list.renamed.json` 129 份、`editor_set_node_property_updates` 25 份、`check_engine_anchor` 11 份、`project_read_text_file` 10 份、`save_preserving_text` 8 份、`MCP-SERVER-HANDOVER` 6 份 | **能**：重建源码/脚本/文档的**最新版本**（`read`/`write`/`edit` 的载荷都在记录里）；**不能**：`.git` 历史（需重新 `git init`）、`bin/` 二进制、部分只以“命令+退出码”形式出现的中间态 |
| 模块旧快照 | `%TEMP%\mcp044-module-backup\mcp_server\`（808 文件；`gen_renamed_contract.py` 64,767 B、`mcp_server.h` 8,394 B、`mcp_capture.cpp` 23,942 B；09-24） | TASK-044 时代 | **能**：作**对照/兜底**；**不能**：不是最新（缺补丁 1–3、后加工具、门完整性工作） |
| 全引擎旧树 | `%TEMP%\audit002\tree\`（含 `modules/`、`core/`、`editor/`、`bin/`；`modules/mcp_server` **仅 46 文件**，09-22；**无 `.git`**） | 早期全树 | **能**：引擎侧**基线文件**（便于重放三个补丁的上下文）；**不能**：模块本身太旧 |
| 编辑器二进制 | `%TEMP%\mcp055\pre\godot.windows.editor.x86_64[.mono].exe`（09-24 22:41/22:43，186/187 MB）、`mcp046-pre`、`mcp045-evidence\pre`、`mcp044-pretask`、`mcp014-bin-nonmono`、`audit002\tree\bin` | 09-22…09-24 构建 | **能**：立即有一个可跑的编辑器（用于对照/临时验证）；**不能**：不含最后的补丁 |
| `%TEMP%` 证据区 | 大量 `mcp00x…mcp076` 目录 | 各批次的响应、日志、追踪、脚本草稿 | **能**：**大部分 docs/reports/evidence 可直接回填**（原本就要求“证据当场复制进仓库”） |

## 3. 三条路线

1. **反删除（推荐，需你操作）**：管理员权限 + 反删除工具，范围限定 `F:\RustProjects\godot-mcp-pro\code\godot`。
   **能连 `.git` 一起回来 → 全部本地提交、证据链、二进制原样恢复**。**必须在任何安装/拷贝/写入 F: 之前做。**
2. **从会话记录重建（我可执行，需你授权）**：见 §4。**代价**：工期大（源码 ~150 文件 + 脚本 ~60 + 文档/报告/证据；部分需重跑）；**`.git` 历史不可还原**（重新 `git init` 并从 D136 起继续记）；三个引擎补丁需按 `DECISIONS.md` 记录**重放**并用门验证。
3. **你的备份**：若有其它机器/网盘/外置盘副本，给我路径即可。

## 4. 重建程序（路线 2 的步骤，供授权后执行）

1. **先做只读提取**：从 566.7 MB `.jsonl` 中按工具调用类型抽取
   ①`write`/`edit` 的**文件内容与目标路径**（取**最后一次**出现的版本，用时间戳/序号定序）；
   ②`read` 的结果（含行号，可去行号还原）；③`git diff`/`git show` 的输出（引擎补丁的精确差异）。
   产出**清单**：`path → 来源(记录/时间戳) → 置信度(高/中/低)`。
2. **重建顺序**：`modules/mcp_server/**`（源码 → 脚本 → 文档/报告/证据）→ 契约三件套
   （**`tools_list.renamed.json` 必须用生成器重跑得到，不以记录中的副本为准**，并核对 `_meta.count=177` / sha）
   → 引擎补丁（`core/config/project_settings.{h,cpp}`、`editor/editor_node.cpp`、`modules/mono/csharp_script.{h,cpp}`）。
3. **验证**：按 `MCP-SERVER-HANDOVER.md` 的「复现步骤」跑六道门 + 四个检查脚本 + `check_engine_anchor.ps1`；
   **每一项都必须与 `DECISIONS.md` 里记录的数字对照**（D110–D135 提供了各批的确切数字：契约 sha、门计数、探针数等）。
4. **落点**：先在 **C:** 重建并验证，最后一次性拷回 F:（拷贝前确认反删除已放弃）。

## 5. 根因与要立的三条纪律（防止复发）

1. **禁止 shell 重定向**：任何命令一律用工具自身的参数（`-OutFile`/`Out-File`/`--data-binary @file`），
   **绝不用 `>`/`>>`/`*>`/`2>&1` 重定向**（cmd 与 pwsh 语义不同，且本事故正是 `*>` 在 cmd 下被当成字面参数）。
2. **破坏性脚本必须默认拒绝**：任何含 `Remove-Item`/`rm`/`del`/`Move-Item` 的脚本，**运行前**必须
   ①校验目标根**非空、绝对、非仓根、非盘根**；②校验目标在**显式声明的白名单**内；③**打印将要删除的绝对路径清单与数量**；
   ④参数缺失/含通配符/含 `..` → **直接 throw**。把 `.ps1` 的静态检查加入仓库断言（扫危险 cmdlet + 未校验的 `-Path $X`）。
3. **任务书必须含「破坏性操作安全」条款**：每份给子代理的任务书都写明上述两条，并要求「首次运行破坏性脚本前先 `-WhatIf`/干跑」。

## 6. 请你决定

- **A（推荐）**：先跑反删除（管理员）→ 告诉我结果；成功则我仅需重建 `.git` 之外的东西为零，直接继续 TASK-077。
- **B**：授权我按 §4 从会话记录重建（我会先在 C: 做，再拷回）。
- **C**：给我备份路径。
- 在得到答复前，**我不写 F:**；（会话记录已解压到 C:，属准备工作，可随时使用/删除。）
