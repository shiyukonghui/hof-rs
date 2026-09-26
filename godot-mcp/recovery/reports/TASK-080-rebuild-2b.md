# TASK-080 — **重建阶段 2b**：打上三个引擎补丁 + 重建 177 条契约 + 攻两个硬缺口（**F: 仍冻结**）

> 前序：`rebuild\godot`（19,238 文件 / 1.185 GB）已组装；补丁可行性已在沙箱证明（`patch1→patch2→patch3` 全序 exit 0/0/0）。
> 方案 `RECOVERY-PLAN.md`；清单 `REBUILD-2A-MANIFEST.md`；补丁套件 `rebuild\ENGINE-PATCHES-TO-REAPPLY.md` + `rebuild\patches\*.diff`。
> 报告 `C:\Users\wyl\AppData\Local\Temp\mcp-recovery\REBUILD-2B-REPORT.md`。返回值 **≤10 行**。

## 0. 硬性安全规则（**违反即失败**，与 TASK-078/079 相同）

1. **绝不在 F: 上创建/修改/删除任何文件**（F: 只读）；开工与收尾各核对一次并给证据。
2. **禁止一切 shell 重定向**（`>`/`>>`/`*>`/`2>&1`）。
3. **破坏性命令默认拒绝**：目标须非空、绝对、以 `C:\Users\wyl\AppData\Local\Temp\mcp-recovery\` 开头，先打印将删清单；含通配符/`..`/为空 → `throw`。
4. 只在 `C:\Users\wyl\AppData\Local\Temp\mcp-recovery\` 内写；绝对路径；`.ps1` 纯 ASCII；不联网。

## 1. 三件事（按序）

1. **打补丁**：在 `rebuild\godot` 上按 `patch1→patch2→patch3` 用 `git apply`（先用 `--check`）真打；
   **验证**：三个补丁的符号真的出现（`is_source_newer_than_assembly`、`update_settings_section_text`/`save_custom_section`、`save_preserving_text`），
   并与 `ENGINE-PATCHES-TO-REAPPLY.md` 里记录的**后状态**逐项对照（行数/sha）；若有偏差异常 → 如实报告。
2. **重建契约（目标 177 条）**：①先用记录中的 `1.21.0→1.22.0` 逐字 diff **修正 `scripts\gen_renamed_contract.py` 的版本常量**；
   ②重跑生成器（它需要 legacy 174 条输入与 override/added 表；**只读**从 `F:\moonbit-hof-rs\tests\fixtures\mcp\tools_list.json` 或
   `rebuild\godot\modules\mcp_server\docs\` 下已有资产取）；
   ③**验证**：`_meta.count == 177`、`added_count == 6`、`generator_version == 1.22.0`、
   编辑器可视图 **154** / 游戏 **73**（与 TASK-076A 记录一致），并给生成器**幂等**证据（连跑两次同 sha）。
   **对照目标**：TASK-076A 的契约 sha 为 `a5c59853…`（SHA 全值见 `F:\moonbit-hof-rs\DECISIONS.md` D134/D135，**只读**）——
   若能逐字复现最好；**不能则如实报告差异**（不得伪造）。
3. **攻两个硬缺口**（能做到哪一步就做到哪一步，**如实报告**）：
   - **`tools\registration.cpp`**（`_low-confidence` 里 17,014 B，疑似完整 ↔ 树上是 2,580 B 化石）：**判定它是否完整**
     （是否覆盖契约全部 177 条的注册字面量；可与契约文件逐名对比），能提升就从 `_low-confidence` 提升并**替换化石**；
   - **`scripts\accept_m1.ps1`**（已落 MID 但 **10 处解析错误**）：定位并修到**语法干净**（`[Parser]::ParseFile` 无错）；
     **不得**为了让解析通过而删功能——**如实标注**哪些断言无法从载荷恢复。

## 2. 完成标准

- `rebuild\godot` 已**打好三个补丁**且有后状态证据；
- **契约重建到 177 条**（或给出明确差异与原因）+ 幂等证据；
- 两个硬缺口**状态推进**（或明确说明为何不能）；
- **可解析性复核**：`rebuild\godot` 全量 `.py` / `.ps1` 再次抽检，与 2a 数字对照；
- **不要**跑 scons 构建（那是 2c）；**不要**改任何模块源码的语义（只做补丁应用、版本常量修正、缺口修复）。
- 产物：`REBUILD-2B-REPORT.md`（真实输出/退出码/sha256/结论锚点）。
