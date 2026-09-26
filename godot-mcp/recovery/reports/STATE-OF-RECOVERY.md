# 恢复状态（TASK-080 / 2b 之后）— 一句话：**引擎补丁已完整复原；模块可跑但不可完全逐字复原**

> 本文件在 C:（**F: 仍处写入冻结**）。前序：`RECOVERY-PLAN.md`、`EXTRACTION-MANIFEST.md`、`REBUILD-2A-MANIFEST.md`、
> `REBUILD-2A-REPORT.md`、`REBUILD-2B-REPORT.md`。重建树：`C:\Users\wyl\AppData\Local\Temp\mcp-recovery\rebuild\godot\`。

## 1. 已复原（有证据）

| 项 | 状态 | 证据 |
|---|---|---|
| **引擎基线** | 完整可用、**确认未预先打补丁** | `SConstruct`/`core`/`editor`/`modules/mono`/`modules/gdscript`/`platform/windows`(69) 齐全；补丁符号出现 0 次 |
| **三个引擎补丁** | ★ **已真打上** | `git apply` **exit 0/0/0**；五个后状态文件的 **bytes/sha 与补丁套件记录值逐项一致**（`project_settings.{cpp,h}`、`editor_node.cpp`、`csharp_script.{cpp,h}`） |
| **模块源码/脚本/文档** | 661 个高/中置信载荷已落树；低置信 41 个另置 | `REBUILD-2A-MANIFEST.md`（逐文件来源与置信度） |
| **六个门纪律脚本** | **全部完整且解析干净** | `check_engine_anchor.ps1`(21,235B)、`mcp_evidence_guard.ps1`(44,890B)、`mcp_watch_run.ps1`(15,879B)、`check_exit_propagation.py`(16,260B)、`check_tautologies.py`(12,880B)、`check_hardcoded_counts.py`(10,174B) |
| **契约** | **形状正确**：`count=177`、`added_count=6`、`generator_version=1.22.0`、编辑器 **154** / 游戏 **73**、**幂等**（连跑两次同 sha） | 生成器重跑输出 |
| **`tools/registration.cpp`** | 从 `_low-confidence` 提升（17,014B/294 行；64 include ↔ 63 register 双射，63 组头文件齐全） | 化石已备份 `rebuild\work2b\registration.cpp.fossil-2a` |

## 2. 不可完全复原（边界确定，**不得伪造**）

| 项 | 差距 | 原因 |
|---|---|---|
| **契约 sha** | 重建值 `078433de…`（129,016 B）≠ 原值 `a5c59853…`（163,520 B），差 **34,504 B** | 重建出的 `gen_renamed_contract.py` 是**残缺件**（overrides 21/36 且含重复块，缺 TASK-076A 三条 append-only 记录）；115 个读窗合并仍拼不出单版本 |
| **`scripts/accept_m1.ps1`** | 10 处解析错误未修 | **终版 240–689 行区段在全部 179 份记录里从未被读取**，且现有文本含**整块三重复**；两次修复尝试**测完即回滚**（未为过解析而删功能） |
| **`tests/test_mcp_server.h`** | 树上是 09-22 化石（66,392 B） | 终版 29,110 行、读覆盖 72.6%、456/793 次 edit 重放失败 |
| **`docs/DESIGN-DETAIL.md`** | 化石 31,531 B vs 终版 84,486 B | 50 次 edit 全失败且**无 read** |
| **`.git` 历史 / 全部分支提交** | **永久丢失** | 记录里只有 sha 与 diff 文本；从未 push，上游只有 `master=57277407` |
| **`bin/` 二进制** | 丢失 | 零载荷（`%TEMP%` 里的 09-22…09-24 旧构建属另一来源，不含最后补丁） |
| ≥516 个从未被读写的文件 | 缺失 | 其中 **511 个是 `docs/reports/evidence/**` 的 request/response JSON → 可由证据脚本重跑再生** |

## 3. 结论与三条出路

**从会话记录重建的上限到此为止**：能恢复到「**引擎补丁正确 + 模块大体可编译 + 契约形状正确**」，
但**无法逐字复原**契约、`accept_m1.ps1`、`test_mcp_server.h`、`DESIGN-DETAIL.md`，也**无法恢复 git 历史与二进制**。
按本项目纪律，**不得**把这种降级状态当作原目标完成。

1. **A（最优，需你操作）**：**管理员权限反删除** `F:\RustProjects\godot-mcp-pro\code\godot`
   —— 可**一次性**恢复全部本地提交、契约、测试、证据与 `bin/`；**务必先于任何安装/拷贝**。
   （反删除成功则 C: 的重建成果可整目录丢弃。）
2. **B（你的备份）**：若有其它机器/网盘/外置盘副本，给路径即可。
3. **C（授权降级重建，需你明确同意）**：接受「契约 sha 不同 + `accept_m1.ps1` 缺失区段 + `test_mcp_server.h` 需重写」
   这一现实，由我继续 2c：修/重写缺口 → 构建 → **重跑六道门并重新验收**（`test_mcp_server.h` 重写后门③的断言数必然变化，
   需以「重新建立基线」的方式记录，而不是假装等价）。

**在得到你的选择前**：F: 保持冻结；C: 的重建树保持现状（可随时删）。
