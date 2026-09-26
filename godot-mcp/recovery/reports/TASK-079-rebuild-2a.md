# TASK-079 — **重建阶段 2a**：在 C: 上组装可用的重建树 + 逐文件缺口清单（**F: 仍冻结**）

> 前序：TASK-078 已把会话记录抽取到 `C:\Users\wyl\AppData\Local\Temp\mcp-recovery\staging\`（10,861 文件 / 344 MB，
> 含 `__history` 4,543 版本、`__diffs` 3,733 份、`EXTRACTION-MANIFEST.md`）。方案见 `...\mcp-recovery\RECOVERY-PLAN.md`。
> 报告 `C:\Users\wyl\AppData\Local\Temp\mcp-recovery\REBUILD-2A-REPORT.md`。返回值 **≤10 行**。

## 0. 硬性安全规则（**违反即失败**）

1. **绝不在 F: 上创建/修改/删除任何文件**；**F: 只读**。开工与收尾各核对一次 F: 未被触碰并给证据。
   本任务**只允许**在 `C:\Users\wyl\AppData\Local\Temp\mcp-recovery\` 下读写（可读 `%TEMP%` 其它目录作为素材源）。
2. **禁止一切 shell 重定向**（`>`、`>>`、`*>`、`2>&1`）：写文件只用 `Set-Content`/`Out-File -FilePath`/`[IO.File]::WriteAllBytes`/Python `open(...,'wb')`。
3. **破坏性命令默认拒绝**：目标须非空、绝对、**以 `C:\Users\wyl\AppData\Local\Temp\mcp-recovery\` 开头**，**先打印将删清单**；含通配符/`..`/为空 → `throw`。
4. 绝对路径；`.ps1` 纯 ASCII；不联网。

## 1. 目标（本阶段**只组装 + 清点**，不跑门）

在 **`C:\Users\wyl\AppData\Local\Temp\mcp-recovery\rebuild\godot\`** 组装出一棵可用的重建树：

1. **引擎基线**：用 `%TEMP%\audit002\tree\`（09-22 的全引擎树快照，**无 `.git`**）作基线**拷入** rebuild。
   **先验证它可用**：`SConstruct`、`core/config/project_settings.cpp`、`editor/editor_node.cpp`、`modules/mono/csharp_script.cpp`、
   `modules/gdscript/gdscript.cpp`、`platform/windows/**` 是否齐全；给**文件计数**与**关键文件存在性表**；
   若发现它其实是同一 fork 的**已被打过补丁**的版本 → **明确指出**（用 `save_custom_section` 等符号是否存在判定）。
2. **模块**：把 `staging\modules\mcp_server\**` 的**高/中置信**载荷按**原仓库相对路径**落到 rebuild
   （**低置信**的先落到 `rebuild\_low-confidence\`，**不要**混进正式树）。保留 `__history` 于 staging（不拷入正式树）。
3. **引擎三补丁的改动点**：从 `staging\__diffs\**` 里找出补丁 1/2/3 的 hunk（`git show 96f631addb`、`2f85141a74`、`5f3e7fb441` 等），
   **把每个改动点的“原始上下文 + 目标内容”整理成一份可执行清单** `rebuild\ENGINE-PATCHES-TO-REAPPLY.md`
   （文件 / 符号 / 该 patch 的 hunk 原文 / 依赖的邻接代码）。**本阶段先不真打补丁**，但必须给出**能照着打的清单**。
4. **其它仓库资产**：`modules/mcp_server/docs/tools_list.*.json`（**legacy 174 条输入**与 `tool-rename-map.json` 等）
   先从 staging 落；若 staging 缺，则从 `%TEMP%` 的已知副本（如 `audit003\gt\docs\tool-rename-map.json`、`task031-before\...`）补齐并**注明来源**。

## 2. 必须产出的清单（本阶段最重要的产物）

`C:\Users\wyl\AppData\Local\Temp\mcp-recovery\REBUILD-2A-MANIFEST.md`：
- **组装结果**：rebuild 下按目录的**文件数/字节数**；
- **缺口表**（逐文件）：`path | 状态(已落/低置信/缺失) | 来源 | 影响(能否编译/能否跑门) | 建议恢复方式`；
  必须显式覆盖已知硬缺口：`tests\test_mcp_server.h`（29,110 行、读 72.6%）、`docs\DESIGN-DETAIL.md`（50 edit 全失败且无 read）、
  `tools\registration.cpp`（42 全失败）、`scripts\accept_m1.ps1`（10 处 PS 解析错误）、`scripts\gen_renamed_contract.py`（版本常量停在 1.3.0）；
- **可解析性抽检**：对 rebuild 里**全部** `.py` 跑 `ast.parse`、**全部** `.ps1` 跑 PowerShell 解析（`[System.Management.Automation.Language.Parser]::ParseFile`），
  报告**失败清单**（文件 + 错误行），并与 TASK-078 的数字对照（`.py` 453 通过/3 失败；`.ps1` 433 解析/10 报错）；
- **未落地清单**：staging 里存在但**未**进入 rebuild 的低置信文件（数量 + 原因）。

## 3. 完成标准

- `rebuild\godot\` 存在且结构完整（引擎 + 模块 + docs 资产）；四份产物齐
  （`REBUILD-2A-REPORT.md`、`REBUILD-2A-MANIFEST.md`、`ENGINE-PATCHES-TO-REAPPLY.md`、可解析性清单）；
- **F: 零写入**（给两次核对证据）；不留未声明垃圾；
- **不要**尝试 scons 构建、不要跑门、不要重写任何模块源码（**只搬运 + 清点**）。
