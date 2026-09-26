
---

## D136 — **事故与恢复**：cmd 下 `*>` 被当字面参数污染脚本参数 + 脚本未校验目标根即 `Remove-Item -Recurse -Force` → 引擎工作树被清空；四次反删除只救回 MFT 驻留小文件；最终以「fork 基线 + 会话记录重放」重建

**事故**（发生于 TASK-077 会话，现场记录 `INCIDENT-077-workspace-deletion.md`）：
一条更新记录的命令行在 **cmd** 里执行 —— `*>` 是 **PowerShell** 的重定向算符，cmd 只把 `*` 当**多余的位置参数**、
把 `>` 当自己的 stdout 重定向。PowerShell `-File` 模式按**位置**绑定未命名实参，于是脚本的第二个参数
（`$OutRoot`）变成了字面量 `'*'`。脚本随后照原样执行了自己的清理行
`Remove-Item -Recurse -Force $OutRoot`（**未校验目标根**），`'*'` 在当前目录展开 —— 当前目录正是
`F:\RustProjects\godot-mcp-pro\code\godot`，于是**该目录下每一项**（含 `.git`）被删。

**损失**：`modules/mcp_server/**` 全部源码/测试/文档/证据、三个引擎补丁、`bin/` 二进制，以及
`feature/mcp-server-module` 的**全部本地提交**（从未 push；远端只有 `master = 57277407a…`）。

**恢复的四次尝试**（现场处置由用户在本会话族之外执行；口径由 TASK-091 任务书给定，本文照此记录，不另编数字）：
① 第三方反删除工具；② `winfr /regular`；③ `winfr /extensive`；④ `winfr /extensive` 复跑。
**四次结果一致且都不够**：只救回 **MFT 驻留**的小文件 —— **< 1 KB 的内容可用，≥ 1 KB 的全部为 0**。
关键文件（`test_mcp_server.h`、`accept_m1.ps1`、`docs/DESIGN-DETAIL.md`、契约 `tools_list.renamed.json`）
与 **`.git` 对象库**（packfile 都是 MB 级）**全部不可用**。

**重建路径**（TASK-078…090）：fork 基线 `57277407e77e61b161f35dbd7aeb510f7a9e26a6` 重新克隆 →
新分支 `feature/mcp-server-module-rebuild` → 从 **178 份 / 566.7 MB 会话记录**抽取载荷重放
（661 个高/中置信载荷）→ 三个引擎补丁按记录值的 bytes/sha **逐项一致** → 之后每一批都重建、重跑九门、重新验收。
**已知不可复原**（如实声明，不假装等价）：契约 sha 与原值不同（重建 `078433de…` vs 原 `a5c59853…`）、
`accept_m1.ps1` 缺失区段未修、`test_mcp_server.h` 是 09-22 化石、`docs/DESIGN-DETAIL.md` 是化石、
`.git` 历史与 `bin/` 永久丢失。

**三条防复发纪律**（此后写进每一份任务书的「铁律」）：
1. **禁止一切 shell 重定向** —— 输出一律 `Start-Process -RedirectStandardOutput <绝对路径>` 或 `-OutFile`；
   脚本参数**一律显式命名传递**，绝不依赖位置绑定。
2. **破坏性命令默认拒绝** —— `Remove-Item`/`Move-Item`/`del` 必须：目标**非空、绝对、在显式白名单前缀之下**，
   **先打印将删清单**，参数含**通配符**或 `..` 或为空 → **直接 throw**；且**一律用 `-LiteralPath`**。
   迁移类操作走「**先复制 → 逐文件 sha 校验 → 才删源**」，校验不过则**保留源并报告**。
3. **每个里程碑 push** —— 本地提交不再等于「已保存」；引擎仓每个里程碑推到 fork，主仓每段可提交改动即提交。

---

## D137 — **迁移与嵌套 git 处理**：引擎克隆与试测工程迁入 `F:\moonbit-hof-rs\godot-mcp\`，独立 `.git` 保留、主仓只忽略不并入

**背景**：`H:\rebuild` 是重建期的临时落脚点。TASK-091 把它迁进正式项目根，并要求**妥善处理两个 git 仓库的关系**。

### 迁移（先复制、逐文件校验、才删源）

| 源 | 目标 |
|---|---|
| `H:\rebuild\godot` | `F:\moonbit-hof-rs\godot-mcp\godot` |
| `H:\rebuild\projects` | `F:\moonbit-hof-rs\godot-mcp\projects` |

- 复制用 `robocopy /E /COPY:DAT /DCOPY:DAT /MT:8`（**cmd 启动**，`Start-Process -RedirectStandardOutput` 收集输出）：
  引擎 **2322 目录 / 21793 文件 / 4.708 GB，FAILED=0 / Mismatch=0**；工程 **303 文件 / 6,029,718 B**。
- 校验由 `verify_tree.ps1` 做**逐文件 SHA-256**（`\\?\` 长路径前缀；树上最长路径 277/294 字符，
  > 260 的源 13 个、目标 80 个 —— `Get-ChildItem` 递归会静默漏掉，故用 `Directory::EnumerateFiles` + .NET 直读）：
  - 引擎：`src=21793 dst=21793 missing=0 extra=0 compared=21793 mismatched=0`，
    两侧总字节 **5,055,873,699 == 5,055,873,699** → `VERIFY_godot=PASS`；
  - 工程：`303/303, mismatched=0, 6,029,718 == 6,029,718` → `VERIFY_projects=PASS`。
- **校验全过之后才删源**，删源走 `safe_remove.ps1`：白名单前缀 `H:\rebuild`、先打印清单
  （`FILES 21793 / BYTES 5055873699`，与校验值一致）、无通配符、`-LiteralPath`、需显式 `-Confirm`。
  `H:\rebuild` 现为空。

### 迁移后 A③ 的校验

| 项 | 结果 |
|---|---|
| `git rev-parse HEAD` | `382549f63ead3d511c429b3e213d6ecb74986208` |
| 分支 / origin | `feature/mcp-server-module-rebuild`；`refs/remotes/origin/feature/mcp-server-module-rebuild` **同一 sha** |
| `git status --short` | **空（0 行）** |
| `git fsck --no-progress` | 两侧 **exit 0**，stdout/stderr **逐字节全等**（两边都是 0 字节输出，sha `E3B0C44298FC1C149AFBF4C8996FB92427AE41E4649B934CA495991B7852B855`） |
| 抽查 `modules\mcp_server\docs\tools_list.renamed.json` | 148,141 B，sha `4BE4285CD221A877712370E6A4C73426E0CC7B94C2B6E32D59B3AED69760ED3A`（与迁移前逐字节一致） |
| 抽查 `bin\*.exe` 四个变体 | 300,544 / 193,465,344 / 300,544 / 194,050,560 B，sha 与迁移前**逐个相同** |

### 嵌套 git 处理（本次的重点决策）

1. **引擎树保留自己的 `.git`**（独立克隆，**不并入**主仓、**不做 submodule**）。理由：它是 4.7 GB / 2.18 万文件的
   上游 fork 全历史；submodule 会把「模块补丁的版本」绑到一个仍需单独推送的第二仓库，主仓对它的每次引用都变脆；
   而内核补丁本来就是**引擎的**交付物，应由**引擎仓自己的分支**承担 —— 主仓只需要「知道它在哪、怎么构建」。
2. **主仓 `.gitignore` 忽略 `godot-mcp/godot/`**（整棵），以及各游戏工程的 `.godot/`、`bin/`、`obj/`、`.mono/`、
   `export_presets.cfg`、`godot-mcp/runs/`。
   **`*.import` 故意不忽略**：它是 Godot 的资源 UID 映射，属于工程源码，丢了工程打不开（任务书说「视情况」，这里结论是「不忽略」）。
3. **策略**：**引擎仓**以 fork 分支为准、**每个里程碑 push**；**主仓**只跟踪「模板 + 游戏源码 + 驱动脚本 + 文档」这些**小文件**，
   每段可提交改动即提交，保持 `git status` 干净。
4. `godot-mcp/README.md` 写清布局、两个仓库的关系、构建方式与如何跑试测。
5. TASK-085/086 期的重定向残留（`$null`、`$l`、`%DST%/`）**留档不删**（破坏性命令默认拒绝），
   在 `.gitignore` 里点名忽略，使主仓 `git status` 归零。

---

## D138 — **新目标口径**：轮次不设限、**至少 20 个经典小游戏、全部 C#**，以「可完整溯源操作有效性」为改进基础

用户在本任务（TASK-091）里把目标口径重新定死，取代「把某个游戏做到位就收」的旧读法：

1. **轮次不设限**：不预设「第 N 轮结束」。只要每轮的证据链完整、缺陷有根因、修复有前后对比，就一直做下去，
   直到 20 个游戏全部落地；中途不因「已经跑了很久」而降标准。
2. **至少 20 个经典小游戏**：Pong 是**第 1 个**，随后按同一套脚手架与同一套试测驱动继续
   （贪吃蛇、打砖块、扫雷、俄罗斯方块、2048、太空侵略者、Flappy、双人乒乓、青蛙过河、推箱子、连连看、
   数独、记忆翻牌、弹球、赛车、platformer、卡片配对……按可行性排序）。
3. **全部 C#**（Godot .NET），不再用 GDScript 写游戏逻辑；GDScript 只作为**测试执行器**
   （`running_game_execute_gdscript`）与试测断言语言使用。
4. **改进基础 = 「可完整溯源操作有效性」**：每一个游戏、每一次调用都必须能被台账（`mcp_trace_ledger.py`）判出
   「这次操作到底有没有产生效果」，且证据**可复现、可复算**（像素差、文件 sha、断言、场景树快照），
   **不接受「应该动了」「看起来对」**。判定分布（`verdicts`）与 `facts_complete` 是每款游戏的准入门槛。
5. 由此产生的**工程要求**：脚手架必须可复用（`godot-mcp/projects/_template`）、试测必须有统一驱动
   （`godot-mcp/tools/run_game_session.ps1`）、每款游戏必须产出**每游戏报告**（判定分布 + `facts_complete` + 缺陷清单），
   缺陷「**根因明确的才改，不清楚的只记录**」。
