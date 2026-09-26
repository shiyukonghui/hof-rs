# TASK-081 — 在 H: 克隆 fork 并**在基线之上重建**（新分支；**F: 仍冻结**）

> 背景：`F:\RustProjects\godot-mcp-pro\code\godot` 被误删（见 `C:\...\mcp-recovery\RECOVERY-PLAN.md`）。
> C: 已有 TASK-078/079/080 的重建树与补丁套件。**本任务在 H: 上做，绝不动 F:**。
> 报告 `C:\Users\wyl\AppData\Local\Temp\mcp-recovery\TASK-081-CLONE-REBUILD-REPORT.md`。返回值 **≤10 行**。

## 0. 硬性安全规则（**违反即失败**）

1. **绝不在 F: 上创建/修改/删除任何文件**（F: 只读；开工/收尾各核对一次并给证据）。
   本任务只在 **`H:\`**（重建）与 **`C:\Users\wyl\AppData\Local\Temp\mcp-recovery\`**（报告/脚本）下写。
2. **禁止一切 shell 重定向**（`>`/`>>`/`*>`/`2>&1`）：写文件用 `Set-Content`/`Out-File -FilePath`/`[IO.File]::WriteAll*`/Python `open(...,'wb')`。
3. **破坏性命令默认拒绝**：非空、绝对、以 `H:\` 或该 C: 前缀开头，**先打印将删清单**；含通配符/`..`/为空 → `throw`。
4. 绝对路径；`.ps1` 纯 ASCII；**不 push**（只本地提交）；不联网除克隆本身。

## 1. 步骤

1. **连通性**：先 `git ls-remote git@github.com:shiyukonghui/godot.git`（只读）。若 SSH 失败 → 用
   `https://github.com/shiyukonghui/godot.git`。**把实际用了哪个 URL 记下来**。
2. **克隆到 `H:\rebuild\godot`**（若 `H:\rebuild` 不存在则创建）。克隆完成后：
   `git -C H:\rebuild\godot rev-parse HEAD`、`git log --oneline -1`、`git branch -a`，
   **确认远端 `master` == `57277407e77e61b161f35dbd7aeb510f7a9e26a6`**（这是我们的事故前 pre-patch 基线）。
3. **建新分支**：`git switch -c feature/mcp-server-module-rebuild 57277407`（或等价的 checkout -b）；记录新分支名。
4. **叠加模块**：把 C: 重建树里的模块拷进来：
   `C:\Users\wyl\AppData\Local\Temp\mcp-recovery\rebuild\godot\modules\mcp_server\**` → `H:\rebuild\godot\modules\mcp_server\**`
   （**只叠加 `modules\mcp_server`**，**不要**覆盖引擎目录；`_low-confidence` 里的东西**不要**混入，
   但把仍缺的关键文件清单列出来：契约正文、`tests\test_mcp_server.h`、`scripts\accept_m1.ps1`、`docs\DESIGN-DETAIL.md` 等）。
   同时把 `docs\tool-rename-map.json` 等**已有且 sha 可验**的契约资产一并放入。
5. **打三个引擎补丁**：按 `patch1→patch2→patch3`，用 `H:\rebuild\godot\`（或 C: 套件目录）里的 `.diff`：
   先 `git apply --check`，再 `git apply`。**逐条验证后状态**：下面五个文件的 sha256 **必须逐字等于**记录值：
   ```
   core/config/project_settings.cpp  e9c4f6fb143afcdd63939574e0067a4aff929ff47d2893b996da218415d05f68
   core/config/project_settings.h    b8491ca81d1a8f8cdb986325812948e74406904614a0503704184452e19b7d79
   editor/editor_node.cpp            699bfc817f99ce25cd45678cb3213dea203b49e1a85c4f4f54f7d1b597647ec8
   modules/mono/csharp_script.cpp    7fef858f8f51a177390f1a878591a4567943ce2b78965b599e47b04b85975eb8
   modules/mono/csharp_script.h      499bdbc4e2e8340125bc88e79065826da5753ee07da7070bf4ba58952ae16f0b
   ```
   → 这一步是**最强证据**：证明引擎侧已**逐字回到事故前状态**。
6. **提交**（**不 push**）：在新分支上分两次提交更清晰：①`engine: reapply the three MCP patches (verified by sha)` ②`modules/mcp_server: rebuild from session transcripts (fidelity noted in report)`。
7. **健康检查**：`git status --short`（哪些文件缺/未跟踪）、`git log --oneline -3`；
   对 `modules/mcp_server` 里全部 `.py`/`.ps1` 做解析抽检（同 TASK-079 方法），给失败清单；
   **并明确列出与事故前相比仍缺什么**（附"事故前应有"的依据来源：`F:\moonbit-hof-rs\DECISIONS.md` 只读 + C: 的 EXTRACTION/REBUILD 清单）。

## 2. 完成标准

- `H:\rebuild\godot` 是一个**真 git 仓库**，位于新分支，基线 `57277407`，**三个补丁已打且五个 sha 全 MATCH**；
- 模块已叠加并提交，健康检查与**缺口清单**齐备；
- **F: 零写入**（两次核对证据）；报告含：URL 使用、分支名、五个 sha 的 MATCH/DIFF 表、模块文件数、解析失败清单、缺口清单、两次提交的 sha。
