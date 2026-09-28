# TASK-150 — ① 忽略/停止跟踪导出中间产物；② 从历史中清除它们（**破坏性，用户已授权**）

> 子代理**只读本文件**执行；报告 `recovery\reports\TASK-150-REPORT.md`，**只返回路径 + 一行状态**。
> **严格单线程**：不得再派子代理。**禁止 shell 重定向**（`>`/`>>`/`2>&1`/`2>nul`/`1>NUL`/`2>/dev/null`）。
> **用户已明确授权**：可以 `git rm --cached`、`git filter-branch`、`git gc --prune=now`、`git push --force-with-lease`（**仅限外层仓 `F:\moonbit-hof-rs` 的 `master`**）。

---

## 0. 背景（一手）

* 外层仓 `F:\moonbit-hof-rs`（`origin` = `https://github.com/shiyukonghui/hof-rs.git`，分支 `master`）已推到 `8f48c93`（与远端同步）。
* 本次推送时 GitHub 逐条告警：**20 个游戏 exe 各 78.26 MB**，路径为
  `godot-mcp/recovery/work/task148/exe/<game>/<game>.exe`，另有 `GH001: Large files detected`。
  即 TASK-148 的**导出中间产物整棵树**（exe/pck 等，~1.5 GB+）**已进入已推送的历史**。
* 根因：TASK-149 任务书 §A.1 写了"提交整个 `work/task148`"（**口径偏宽**），实施方照做并已把该点登记为未达标项 U2。
* **用户裁定**：执行 **① 忽略 + 停止跟踪**（非破坏）**和 ② 重写历史清除**（破坏性）**两步**。

---

## 1. 执行顺序（**必须按此顺序，禁止跳步**）

### A. 先备份（**任何破坏性动作之前**）
1. 记录 `git rev-parse HEAD`（`<OLD_HEAD>`）与 `git status --short`（应为空）。
2. 备份到**仓库之外**：`F:\moonbit-hof-rs-backup\hof-rs-pre-purge-<YYYYMMDD-HHMM>.bundle`，命令 `git bundle create <path> --all`；
   记录 bundle 的**路径 / 字节数 / sha256**，并**验证** `git bundle verify <path>` 通过。
3. 报告必须包含上述 4 个值 + 验证输出。**没有备份证据就不得进入 §C。**

### B. 盘点要清理的对象（**用数字决定，不要凭猜**）
4. 列出历史中**最大的 30 个 blob**（对象类型/大小/路径），方法任选其一并写清命令：
   `git rev-list --objects --all` 配合 `git cat-file --batch-check='%(objecttype) %(objectname) %(objectsize) %(rest)'`。
5. 产出**清理清单**（路径前缀），至少覆盖：
   * `godot-mcp/recovery/work/task148/exe/`（20 个 exe + pck 等）；
   * `godot-mcp/recovery/work/task148/unzip-test/`；
   * 盘点中发现的**其它生成物/二进制大树**（例如历史里的 `emsdk/`、`dist/` 下意外入库的大文件）——**逐个列出并给出大小依据**。
6. **不要**把源码、报告、文档、测试、`TEST-CASES.md`、`DECISIONS.md`、`ERRATA.md` 等文本资产放进清理清单。
   清单要在报告里**逐条给理由**。

### C. 第 ① 步：忽略 + 停止跟踪（非破坏，先提交）
7. 在**外层仓根 `.gitignore`** 追加规则（**只在文件末尾追加，不改既有规则**）：
   `godot-mcp/recovery/work/task148/exe/`、`godot-mcp/recovery/work/task148/unzip-test/`、以及 §B 发现的同类生成物模式。
8. `git rm -r --cached --ignore-unmatch <清理清单>`（**只动索引，磁盘文件必须仍在**）。
9. 提交（一个提交）：信息写清"停止跟踪导出中间产物（磁盘保留）+ gitignore 规则"。
10. **验证**：`git status --short` 中这些路径应显示为**未跟踪/被忽略**；磁盘上**文件仍存在**（给 `Test-Path`/大小抽查证据）。
    这一步之后 `git ls-files <path>` 必须为空。

### D. 第 ② 步：历史重写（破坏性）
11. **优先检查 `git filter-repo` 是否已安装**（`git filter-repo --version`）。**只可使用已安装的工具，禁止联网安装**。
    * 已安装 ⇒ 用它（`--path`/`--invert-paths` 精确指定清理清单）。
    * 未安装 ⇒ 用内置 `git filter-branch`：
      `git filter-branch --force --index-filter "git rm -r --cached --ignore-unmatch <清单>" --prune-empty --tag-name-filter cat -- --all`
      （本仓仅 ~57 提交 / ~7k 对象，可行；**原样记录命令**。）
12. 清理旧引用与对象：`rm -rf .git/refs/original`（若存在）、`git reflog expire --expire=now --all`、`git gc --prune=now --aggressive`。
    * 记录清理前后的 `git count-objects -vH` 与 `.git` 目录字节数。
13. **验证（必须全过，任一条不过就停手并如实报告）**：
    * **(a) 内容零差异**：`git diff <OLD_HEAD> HEAD --stat -- . ':(exclude)<清理清单各前缀>'` 输出**必须为空**
      （除被清理路径外，历史末态的树完全一致）。若 filter-branch 改了提交 ID，这条以**树内容**为准。
    * **(b) 大对象已消失**：重跑 §B 的盘点 ⇒ **不再有 >10 MB 的 blob**（或逐条列出仍然存在的、并说明为何保留）。
    * **(c) 提交数**：`git rev-list --count HEAD` 与清理前对照（`--prune-empty` 可能减少，**逐项说明**）。
    * **(d) 工作区文件仍在**：被清理路径的文件**仍在磁盘上**（抽查 ≥3 个，给路径+字节数）。
    * **(e) 文本资产未受损**：抽查 `DECISIONS.md`/`recovery/TEST-CASES.md`/`recovery/reports/ERRATA.md` 的 sha256 与清理前一致。

### E. 推送（`--force-with-lease`）
14. `git push --force-with-lease origin master`；记录完整输出与退出码；随后 `git status -sb` 确认 `## master...origin/master`（**无 ahead/behind**）且远端 HEAD == 本地 HEAD。
15. **不得**动引擎仓（`godot-mcp/godot`，已同步、无需推送）。

### F. 报告
16. 报告须含：备份证据（路径/字节/sha256/verify 输出）、盘点结论与清理清单（含理由）、第①步提交号、第②步完整命令、
    清理前后**体积对照**（`count-objects` + `.git` 字节）、§D.13 五条验证的**原始输出**、推送输出、
    **回滚配方**（`git bundle` 路径 + `<OLD_HEAD>` + `git reset --hard` + `push --force-with-lease`）、
    铁律逐条（含重定向自查）、两仓 `git log --oneline -3` / `git status --short`、以及**任何偏离/未达标项**。

---

## 2. 硬性约束

1. **禁止一切 shell 重定向**；用 `-o`/`-OutFile`/Python 句柄。
2. **磁盘文件一律不删**（只动 git 索引与历史）；不删旧包、不改 `dist/**`。
3. 命令尽量**从 cmd 启动**（`git filter-branch` 在 cmd/bash 下均可）；唯一高位端口（本任务不需要）。
4. **禁止联网安装**任何工具；不使用第三方端点。
5. **只重写外层仓 `master`**；**不 force 引擎仓**；不用 `--force`（用 `--force-with-lease`）。
6. **未达标项如实报**（不得"应该可以"）；若 §D.13 任一验证不过 ⇒ **停手、不推送**，并把状态与回滚点写进报告。

---

## 3. 验收判据

| 编号 | 判据 |
|---|---|
| R1 | 备份 bundle 已生成在**仓库外**，含路径/字节/sha256 + `bundle verify` 通过 |
| R2 | 历史最大 blob 盘点已给（前 30 + 清理清单逐条给理由） |
| R3 | 第①步：`.gitignore` 追加规则 + `git rm --cached` 一个提交；`git ls-files <清单>` 为空；磁盘文件仍在 |
| R4 | 第②步：重写命令原样记录；`.git` 体积**前后对照**（数字） |
| R5 | 验证 (a) 除清理路径外**树内容零差异**；(b) 无 >10 MB blob（或逐条说明）；(c) 提交数变化已解释；(d) 磁盘文件仍在（≥3 抽查）；(e) 文本资产 sha256 未变 |
| R6 | `push --force-with-lease` 成功；`git status -sb` 同步；远端 == 本地 HEAD |
| R7 | 报告含**回滚配方**；铁律与重定向自查；两仓 git 状态；未达标项如实报 |
| R8 | 引擎仓未被改动/未被 force 推送 |

---

## 4. 报告落点

* `F:\moonbit-hof-rs\godot-mcp\recovery\reports\TASK-150-REPORT.md`；**只返回路径 + 一行状态**。