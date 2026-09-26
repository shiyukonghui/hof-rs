# TASK-100 — 第 10、11 个游戏（2048 / Minesweeper）交付；「一个属性一个写者」（G1）与「`ForceTestState` 会归零」（M1）两条缺陷在 r1 被照出来、在 r2 修好；模块字节未动，门跑器判 `SKIP_REBUILD`（如实说明：十道门一门未跑）

* 执行者：工具工程师（本会话，**有写权限，不再委派**）
* 主仓：`F:\moonbit-hof-rs`（分支 `master`，无远端，本轮提交 `67bcbb0`）
* 引擎仓：`F:\moonbit-hof-rs\godot-mcp\godot`（分支 `feature/mcp-server-module-rebuild`，`HEAD = origin = e041cae270`，**本轮一个字节未动**）
* 脚本 / 会话 / 证据：`godot-mcp\recovery\work\task100\`
* 时间：2026-09-27（本会话）

---

## 0. 结论表（每行一句话）

| 段 | 要求 | 结论 | 关键证据 |
|---|---|---|---|
| **A①** | **2048**（C#，只用 MCP 调用开发）：4×4 未知数网格、四向合并、得分、胜负与禁止非法移动 | **做完，首轮照出 1 条载荷缺陷、修好并重跑 r2 后全绿。** 129 次调用（编辑器 16 / 游戏 113），`facts_complete` **129/129（100%）**，判定分布 `failed=2`（**两条都是声明的**：`e06` 同名批量 `-32000`、`g106` 不存在属性 `-32001`）+ `ok_effect_observed=23` + `ok_file_effect_observed=81` + `ok_no_effect_observed=23`；断言 **70 PASS + 1 条声明的边界失败** ＋ **2 条屏幕文本 PASS** ＋ **1 条场景断言 PASS** = **73 PASS**；像素差 **26/129 非零**（编辑器 1/16、游戏 25/113），`user://` 六帧逐对 **13055 / 15543 / 171792 / 148841 / 26181 px**；独立复算 **0 处不符**；`project_build_csharp` exit 0（3732 ms）、`invalid_count=0`、`errors count=0`；树里 75 个节点名 **0 个 `@` 开头** | `runs\game2048\2048-task100-r2`（首轮 `-r1`）、`logs\summary-2048-r2.txt`、`logs\assert-2048-r2.txt`、`logs\samples-2048-r2.txt`、`logs\pixel-2048-r2.txt`、`logs\frames-2048-r2.txt` |
| **A②** | **Minesweeper**（C#，只用 MCP 调用开发）：布雷、翻开、数字提示、标旗、失败与胜利判定（首翻安全） | **做完，首轮照出 1 条会话缺陷、修好并重跑 r2 后全绿。** 155 次调用（编辑器 14 / 游戏 141），`facts_complete` **155/155（100%）**，判定分布 `failed=2`（同样两条声明的）+ `ok_effect_observed=20` + `ok_file_effect_observed=101` + `ok_no_effect_observed=32`；断言 **93 PASS + 1 条声明的边界失败** ＋ **2 条屏幕文本 PASS** ＋ **1 条场景断言 PASS** = **96 PASS**；像素差 **21/155 非零**（编辑器 1/14、游戏 20/141），五帧逐对 **194130 / 196947 / 196939 / 195563 px**；独立复算 **0 处不符**；`project_build_csharp` exit 0（3678 ms）、`invalid_count=0`、`errors count=0`；树里 333 个节点名 **0 个 `@` 开头** | `runs\minesweeper\mine-task100-r2`（首轮 `-r1`）、`logs\summary-mine-r2.txt`、`logs\assert-mine-r2.txt`、`logs\samples-mine-r2.txt`、`logs\pixel-mine-r2.txt`、`logs\frames-mine-r2.txt` |
| **A③** | 跑完给：调用数、判定分布、`facts_complete`、缺陷清单（分「工具缺陷」「游戏或驱动缺陷」）；两行加进 `GAME-LOOP-LOG.md` | **做完。** 台账续到第 10、11 行；**工具缺陷 0 条**；**游戏或驱动缺陷 2 条**（**G1** 载荷：`LastAutoSteps` 一个属性两个写者，r1 的两条增量断言实得 0，已拆成 `LastHookSteps`/`LastAutoSteps`；**M1** 会话：把 `ForceTestState` 会归零的计数器当成会保留，r1 的收尾断言实得 0，已改成同一块钉住的盘面并新增一条显式断言）；`GAME-LOOP-LOG.md` 新增「TASK-100 记录」节与两条缺陷行 | `GAME-LOOP-LOG.md` 台账第 10/11 行、缺陷表 G1/M1、TASK-100 记录节；`recovery\work\task100\decisions-d148.md`；`DECISIONS.md` 的 D148 |
| **B** | 若改了模块 → 重建两变体 + 十道门全绿（真实退出码）+ `accept_m1` 22/22 + push 到 fork；未改模块则用 `run_gates.ps1` 的纯文档/免跑判定并**如实说明**；主仓提交；报告含两仓 `git log --oneline -8` 与 `git status --short`；时间不够如实报告 | **未改模块，如实免跑。** `modules\mcp_server` 本轮**零字节改动**（引擎仓 `git status --short` 空、`git diff 2385fe2fb..HEAD` 仍只有两份 `.md`），预检判 `VERDICT=ANCHOR_STRUCTURAL_EQUIVALENT` + `RESULT=SKIP_REBUILD` + `GATES_SKIPPED=1`，**exit 0**，非编译清单两份 `.md`——**十道门本轮一门未跑，未重建、未 push 代码**。主仓提交 `67bcbb0`（139 个文件，14831 行增 1 行删），提交后 `git status --short` **空** | `runs\gates\task100-doconly\summary.txt`、`logs\gates-task100-doconly.txt`；§B、§F |

---

## A. 第 10、11 个游戏（C#，只用 MCP 调用开发）

### A1 形态与开发方式（两款同一套脚手架，TASK-099 结尾的模板照用 + 一条新增）

两款都从模板实例化（`tools\new_game.ps1 -Name game2048 -Class Game2048Game` / `-Name minesweeper -Class MinesweeperGame`），**游戏内容全部由 MCP 调用写成**：`project_edit_script`（C# 载荷替换模板桩）、`editor_add_nodes_batch`（3 个静态节点一次建好）、`editor_add_input_action`、`editor_save_scene`、`project_build_csharp`、`project_validate_scripts`、`editor_get_errors`；游戏相全部是 `running_game_*`。

| 游戏 | 场景里的静态节点 | 运行期新建的东西 |
|---|---|---|
| 2048 | `Background` / `Hud` / `Status` | 棋盘框 1 + 16 个 `Tile_r_c` + 16 个 `Val_r_c` |
| Minesweeper | `Background` / `Hud` / `Status` | 81 个 `Cell_r_c` + 81 个 `Num_r_c` |

**确定性规则（继承前九款，并新增第 ⑦ 条）**：①静态节点一次批量建好；②动态对象运行期新建；③`ForceTestState` 一个调用钉死整盘状态；④**多帧采样先于会改变状态的那一步**；⑤每个「钩子做了多少」都是**与帧率无关的增量属性**；⑥建场景那一步**故意再跑一次同名批量**，让 D-3 的拒绝出现在每一轮证据里；⑦**（本轮新增）一个属性只能有一个写者** —— 见 A5 的 G1。任何时钟都用**浮点累加器**（`_autoAccum += delta * rate`，不用 `(int)(delta * rate)`），`Elapsed` 是每帧 `+= delta` 的浮点秒表。

**「全新」的含义**：两次重跑之前，都先把 r1 工程按「**先写 sha256 清单再移动**」归档（`recovery\work\task100\archive\game2048-r1`，清单 129 文件 / 8 399 363 B；`minesweeper-r1`，清单 129 文件 / 8 417 591 B），再用模板重新实例化，使 r2 与 r1 从同一个起点出发。

### A2 终轮真实输出

| | 2048 r1 | 2048 **r2** | Minesweeper r1 | Minesweeper **r2** |
|---|---|---|---|---|
| 调用数（编辑器 / 游戏） | 128（16 / 112） | **129（16 / 113）** | 154（14 / 140） | **155（14 / 141）** |
| `facts_complete` | 128/128 | **129/129（100%）** | 154/154 | **155/155（100%）** |
| 断言（node-state） | 67 PASS + 2 FAIL + 1 声明 ERROR | **70 PASS + 1 声明 ERROR** | 90 PASS + 1 FAIL + 1 声明 ERROR | **93 PASS + 1 声明 ERROR** |
| 断言（另两个工具） | — | **2 屏幕文本 + 1 场景 = 3 PASS** | — | **2 屏幕文本 + 1 场景 = 3 PASS** |
| 像素差非零 | 25/128（1/16、24/112） | **26/129（1/16、25/113）** | 21/154（1/14、20/140） | **21/155（1/14、20/141）** |
| 判定分布 | `failed=2` + ok_effect 22 + ok_file 85 + ok_no 19 | **`failed=2` + 23 + 81 + 23** | `failed=2` + 20 + 104 + 28 | **`failed=2` + 20 + 101 + 32** |
| `user://` 帧链 | 13055 / 15543 / 171792 / 148841 / 26181 | **同上（六帧）**；t4 的 sha 与 r1 不同 | 194130 / 196947 / 196939 / 195563 | **与 r1 逐字节相同** |
| 缺陷（工具 / 游戏或驱动） | 0 / 1 | **0 / 0（r1 那条已修）** | 0 / 1 | **0 / 0（r1 那条已修）** |

> 每一轮都是 `failed=2`，且**两条都是声明的**：编辑器相那一次同名拒绝（`-32000`）+ 一条故意打在不存在属性上的边界断言（`-32001`）。`report.json` 的自动缺陷清单只有这两条。

### A3 证据形态（任务书要求的四类都用上了）

**① 多帧属性采样（先采样、后改变）**

| 采样 | 帧数 | 结果 |
|---|---|---|
| 2048 `g15-samples-frozen` | 12 | 冻结基线：`GridHash` / `TilesInUse` / `MoveCount` **各只有 1 个值**，`Elapsed` / `Ticks` **各 12 个不同值** |
| 2048 `g94-samples-autoplay` | 30 | `MoveCount` **30 个不同值（6→65）**、`AutoSteps` 30 个（6→65）、`GridHash` 4 个、`LastAutoSteps` {0,1}、`Elapsed` 30 个、`Ticks` 30 个 |
| Minesweeper `g18-samples-frozen` | 12 | 冻结基线：`RevealHash` / `RevealedCount` / `FlaggedCount` **各只有 1 个值**，`Elapsed` / `Ticks` **各 12 个不同值** |
| Minesweeper `g119-samples-autoreveal` | 30 | `RevealedCount` **7 个不同值（16→71）**、`RevealHash` 7 个、`AutoSteps` 7 个（16→27）、`LastAutoSteps` {0,1}、`Elapsed` 30 个、`Ticks` 30 个 |

**② 断言** —— 2048：四向都钉过确切棋盘（左 `2,2,4,0`→`4,4,0,0`、右 →`0,0,4,4`、上 →`4,4,0,0` 上半、下 →底两格），合并得分 4→12→2048、`LastMoveGain`/`LastMoveMerges` 逐次精确；非法移动（已靠左再左、已靠上再上）**棋盘一字不变**且 `MovesRejected` 1→2、`LastEvent contains "rejected reason=no_change"`；赢局 `MaxTile=2048`/`Won=true`/`GameOver=false`；满盘无解 `CanMoveAny=false`/`GameOver=true`/`Won=false`/一动即被拒（`reason=game_over`）；**满盘但有一对相等不算输**；`LastHookSteps` 2 与 3、`LastAutoSteps` 0。屏幕文本 `2048 REACHED` / `NO MOVES LEFT`。Minesweeper：`MineList` 与独立复算一致、`SafeCells=71`；首翻安全三个数（`MinesRelocated=1`、`MineList` `0,0`→`0,1`、点中格 `ProbeHint=1`）；提示数 3 与 2；标旗/取消的四条状态；三种非法操作（翻已开、标已开、翻被标）全部被拒且 `Moves` 不动、`RejectedMoves` 1→2→3；泛洪一次开出 71 格 → `Won=true`/`GameOver=true`/`Exploded=false`；踩雷 `Exploded=true`/`ExplodedRow,Col=4,4`/`RevealedCount=0`；`LastHookSteps` 在时钟跑过 30 帧后仍是 2，`ForceTestState` 之后归零。屏幕文本 `CLEARED` / `BOOM - GAME OVER`。

**③ 文件 sha** —— 两款各自 `e05` / `e09` 的 `project_read_text_file` sha **逐字节相同**（2048 `7e7fb1d9d985f68074ca6923af07364dc8eb412a4d50aa19479eb2c9bae9c8e2e9` / 813 B；Minesweeper `1fcc873e8ce5b7f66ee13c09a8c18bb7f24098d6a5556bd88dd3e115e34b3845` / 826 B），即被拒的同名批量**什么都没写**；`e06` 的 `-32000` 各列 3 条 `conflicts`（Background / Hud / Status）；编辑器相各 `sidecar_verified=1`（C# 载荷超限走旁路证据）。

**④ 像素差 + 独立复算** —— 见 A4。

### A4 独立复算（不是转述）

`recovery\work\task100\pixel_recompute.py`（逐调用 capture 对，**自己**解码 PNG、用自己的两条规则各算一遍）与 `frames_recompute.py`（`user://` 保存帧，**自己**按 mtime 排序、自己 sha256、自己对 `report.json` 的数字）：

| 运行 | 逐调用对 非零（引擎规则 >10） | 任一字节差异规则 | 与 `report.json` 不符的对 | `user://` 帧链（复算） |
|---|---|---|---|---|
| 2048 **r2** | **26/129**（编辑器 1/16、游戏 25/113） | 同样 26/129 | **0** | **13055 / 15543 / 171792 / 148841 / 26181** |
| Minesweeper **r2** | **21/155**（编辑器 1/14、游戏 20/141） | 同样 21/155 | **0** | **194130 / 196947 / 196939 / 195563** |

两款的保存帧 sha256 与 `report.json` 记录的**逐一相同**，每个游戏的**全部帧 sha 互不相同**（2048 6/6、Minesweeper 5/5）——「画面确实在变」不是形容词。**附带的确定性观察**：Minesweeper r2 的五帧与 r1 **逐字节相同**；2048 r2 的 t0/t1/t2/t3/t5 也与 r1 逐字节相同，只有 t4 不同（那是自动时钟采样之后的那一张，帧时序无法逐字节复现）。

### A5 两条缺陷（r1 照出来、r2 修好）

| id | 层 | 现象（证据） | 根因 | 处置 → 重跑结果 |
|---|---|---|---|---|
| **G1** | 2048（载荷） | 首轮 `runs\game2048\2048-task100-r1` 的 `g88-assert-last-auto-2` 期望 2 **实得 0**、`g110-assert-last-3` 期望 3 **实得 0**；而同一刻 `AutoSteps=2`、`MoveCount=2` 双双 PASS —— 钩子确实走了两步，只是**读到的是别人写的值** | `LastAutoSteps` 有**两个写者**：`AutoStep(n)` 钩子写「这次调用走了几步」，`_Process` 每帧结尾写「这一帧的时钟走了几步」（时钟关闭时写 0）。断言在钩子返回、又过了一帧之后才执行，于是读到 0。**是 P-1 的同一条教训换了个形态**：一个属性两个生产者，读回就不再是那个生产者的事实 | **改**：拆成 `LastHookSteps`（只有 `AutoStep` 写）与 `LastAutoSteps`（只有每帧时钟写）两个属性，并在源码注释里写明是这次运行发现的。r2：`g88-assert-last-hook-2`=2、`g88b-assert-last-auto-0`=0、`g110-assert-last-hook-3`=3 **三条同时 PASS** |
| **M1** | Minesweeper（会话） | 首轮 `runs\minesweeper\mine-task100-r1` 的 `g124b-assert-hook-intact` 期望 `LastHookSteps=2` **实得 0**，而 `g113-assert-last-hook-2`（同一事实、早 11 次调用）**PASS** | 会话在这两条断言之间插了一次 `ForceTestState`，而它按前 11 款游戏的确定性规则把**整个状态**钉死 —— 包括这条增量。**载荷是对的，是会话的假设错了**（与 A-1 / T-3 同一类） | **改**：让「钩子 → 开时钟 → 30 帧采样 → 关时钟 → 两条增量断言」落在**同一块被钉住的盘面**上（删掉中间那次 `ForceTestState`），并**新增一条显式断言**「`ForceTestState` 之后 `LastHookSteps=0`」，把 A-1 的教训写成断言而不是假设。r2：`g113`/`g113b`/`g118b`/`g124`/`g126b` 五条全 PASS |

**这两条的方法论价值**：G1 是「一条断言 + 一个采样」照出来的**载荷**缺陷；M1 是同一批断言照出来的**会话**缺陷。两条都不是工具缺陷，`modules\mcp_server` 本轮零字节改动。

### A6 缺陷清单

**工具缺陷（`modules\mcp_server`）：0 条。** 四轮共 566 条调用里没有一条是「工具做错了事」；唯一的非 `ok` 判定是每条运行里两条**声明的**边界调用（同名拒绝 `-32000`、不存在的属性 `-32001`）。

**游戏或驱动缺陷：2 条（G1 载荷、M1 会话，均已修并在 r2 复核）。**

---

## B. 收尾

### B1「模块字节未动 → 免跑十门」这个判定

`modules\mcp_server` 本轮**代码一个字节没动**：引擎仓 `git status --short` 为空，`git diff --name-only --no-renames 2385fe2fb..HEAD` 仍只有 `MCP-TRACEABILITY.md` 与 `REBUILT-2C-MANIFEST.md` 两份 `.md`。两个变体仍是 TASK-097 在模块提交 `2385fe2fb5` 之后重建的那两份（自报 `4.8.dev.mono.custom_build.2385fe2fb`）。

按 TASK-099 修好的预检，`tools\run_gates.ps1 -Tag task100-doconly` 的真实输出（`runs\gates\task100-doconly\summary.txt`、逐字见 `logs\gates-task100-doconly.txt`）：

```
GATES_PREFLIGHT VERSION_TEXT=4.8.dev.mono.custom_build.2385fe2fb
GATES_PREFLIGHT ANCHOR=2385fe2fb HEAD=e041cae27 ANCHOR_REPORTED=2385fe2fb
GATES_PREFLIGHT WORKING_TREE_RED=0 WORKING_TREE_SAFE=0 COMMITTED_DIFF_SAFE=2
GATES_PREFLIGHT VERDICT=ANCHOR_STRUCTURAL_EQUIVALENT
GATES_PREFLIGHT REASON="2385fe2fb is an ancestor of e041cae27 and all 2 file(s) in the diff are non-compiling; the binary is NOT equal to HEAD, it is structurally equivalent to it"
GATES_PREFLIGHT NONCOMPILING_COUNT=2
GATES_PREFLIGHT NONCOMPILING modules/mcp_server/docs/reports/MCP-TRACEABILITY.md
GATES_PREFLIGHT NONCOMPILING modules/mcp_server/docs/reports/REBUILT-2C-MANIFEST.md
GATES_PREFLIGHT RESULT=SKIP_REBUILD
GATES_SKIPPED=1
```

**如实说明**：本轮**没有重建两个变体、没有跑十道门、没有跑 `accept_m1`、没有 push 代码**，判定的依据是「引擎仓没有任何编译输入」。这与 TASK-099 的情形一致（那一轮为验证预检本身刻意跑过一次编译输入情形；本轮没有新增预检逻辑，所以没有可验证的新门账）。任何「门应该是绿的」的说法本轮**都不成立**，因为没有跑。

### B2 提交与两个仓库

**主仓**（分支 `master`，无远端）：`67bcbb0`，**139 个文件，14831 行增 / 1 行删**（`git status --short` 提交后为空）。提交信息对应 `DECISIONS.md` 的 D148。

**引擎仓**（分支 `feature/mcp-server-module-rebuild`）：**本轮没有任何提交，也没有 push** —— `git status --short` 空，`git rev-parse HEAD` = `git rev-parse refs/remotes/origin/feature/mcp-server-module-rebuild` = `e041cae270487d5c910f1e7ebe0e13982886d602`（与远端同级）。两仓的 `git log --oneline -8` 与 `git status --short` 见 §F。

### B3 `--import` 的关机期访问违例

本轮**四次导入全部 `IMPORT_EXIT=0`、`import.stderr.txt` 0 字节**（2048 r1/r2、Minesweeper r1/r2）。累计口径因此从 **3 次 / 13 次会话导入** 变成 **3 次 / 17 次**。台账待办 2 的判定不变：**不改引擎、不重建**，等可复现配方或用户授权。

### B4 收尾后的进程与端口

最后一轮之后：无 `Godot*` 进程；会话端口 `9940/9941`、`9942/9943` 无 **LISTENING**；门预检没有跑门、没有占用 9888/9889。**未改变机器显示或串流状态**（未停 `GameViewer`、未动设备/注册表/电源/显示拓扑）。

---

## C. 铁律遵守（逐条对照）

| 铁律 | 遵守情况 |
|---|---|
| ① 禁止一切 shell 重定向 | **遵守**：所有 python / powershell / cmd 调用一律 `Start-Process -RedirectStandardOutput/-RedirectStandardError <绝对路径>` 拥有 stdout/stderr；所有文本文件由 Python 写入器、`write`/`edit` 工具或 `[System.IO.File]::WriteAllText` 写。**一处需要说清**：为过滤输出用了 PowerShell 的**管道**（`Get-Content … \| Select-String`、`… \| Measure-Object`），管道不是重定向；没有出现过一个 `>` / `>>`。 |
| ② 破坏性命令默认拒绝 | **遵守，且本轮零删除**：唯一的「移动」是两次 `reset_game_project.ps1` 归档工程 —— 先写 129 文件的 sha256 清单、目标不存在才 `Move-Item`，**自始至终没有删除任何文件**；没有杀任何非本任务进程。 |
| ③ 构建与运行从 cmd 启动 | **遵守**：四次会话运行、两次 `new_game`（经 `reset_game_project.ps1` 生成的 `.cmd`）、门预检全部是 `Start-Process cmd.exe /c …`；`dotnet build` 由会话内的 `project_build_csharp` 触发。 |
| ④ 唯一端口 + 跑前查进程与端口 | **遵守**：`9940/9941`（2048 r1、r2）、`9942/9943`（Minesweeper r1、r2）；每次开跑前 `netstat` + `Get-Process` 确认无残留，收尾后再查一次（无 `Godot*`、无 LISTENING）。 |
| ⑤ 会话文件先双解析后才执行 | **遵守**：四个会话（2048 r1、2048 r2、Minesweeper r1、Minesweeper r2）在开引擎之前都过 `check_session.py`（Python JSON + 形状 + `content_file` 可达）与 `check_session_ps.ps1`（PS 5.1 `ConvertFrom-Json`），两侧都 PASS（129 / 129 / 154 / 155 次调用）。 |
| ⑥ 迁移与删除先存证 sha | **遵守**：两次 `Move-Item` 之前各写出一份该工程 129 个文件的 sha256 清单（`archive\game2048-r1.manifest.json`、`archive\minesweeper-r1.manifest.json`，已入库）；本轮没有删除操作。 |
| ⑦ 不改变机器显示或串流状态 | **遵守**：未停 `GameViewer`、未改设备/注册表/电源、未接触显示拓扑。 |

---

## D. 本任务产出的文件

```
recovery\work\task100\
  make_session_game2048.py / make_session_minesweeper.py   两款游戏的会话生成器（可逐字重生成；后者内含 LCG 的 Python 独立复算）
  append_decisions.py + decisions-d148.md                  写入 DECISIONS.md 的正文（Python 写入器，非 shell 重定向）
  check_session_ps.ps1                                      PS 5.1 那一半的双解析（Python 侧沿用 TASK-098 的）
  reset_game_project.ps1                                    先写 sha 清单再移动 + 重新实例化（TASK-099 的同一份，路径改成 task100）
  assertions.py / extra_assertions.py                       断言逐条读出（后者补屏幕文本与场景断言）
  samples.py / run_summary.py / pixel_recompute.py / frames_recompute.py / extract_editor.py / callread.py / check_session.py
  commit-message.txt                                        主仓提交信息原文
  archive\game2048-r1(.manifest.json) / minesweeper-r1(.manifest.json)   两份 r1 工程的 sha 清单与源码（先存证再移动）
  logs\                                                     60+ 份证据日志（会话逐字输出、断言、采样、复算、门预检、归档）
tools\sessions\{game2048,minesweeper}\session.json + payload\*.cs
projects\game2048\ / projects\minesweeper\                 由模板实例化、随后全部由 MCP 调用写成
runs\game2048\2048-task100-{r1,r2}\、runs\minesweeper\mine-task100-{r1,r2}\   （盘上路径；runs\ 按 .gitignore 不入库）
runs\gates\task100-doconly\                                （同上，不入库）
GAME-LOOP-LOG.md                                           第 10/11 行 + G1/M1 两条缺陷行 + TASK-100 记录节 + 待办续写
DECISIONS.md                                               D148
```

> `runs\` 按 `.gitignore` 不入库（盘上真实存在）；本报告所有 `runs\...` 引用都是盘上路径。
> `recovery\work\task100\`（含两份归档工程）、两款游戏工程与会话均已入库。

---

## E. 真实跑出来的数字速查（都可在盘上复算）

| 项 | 2048 | Minesweeper |
|---|---|---|
| 运行目录 | `runs\game2048\2048-task100-r2`（首轮 `-r1` 对照） | `runs\minesweeper\mine-task100-r2`（首轮 `-r1` 对照） |
| 调用数（编辑器 / 游戏） | 129（16 / 113） | 155（14 / 141） |
| `facts_complete` | 129/129（100%） | 155/155（100%） |
| `args_evidence` | 编辑器 `sidecar_verified=1` + `inline_complete=15`；游戏 `inline_complete=113` | 编辑器 `sidecar_verified=1` + `inline_complete=13`；游戏 `inline_complete=141` |
| 判定分布 | `failed=2` / `ok_effect_observed=23` / `ok_file_effect_observed=81` / `ok_no_effect_observed=23` | `failed=2` / `20` / `101` / `32` |
| 断言 | 70 PASS + 1 声明 ERROR（node-state）＋ 3 PASS（屏幕文本 + 场景）= **73 PASS** | 93 PASS + 1 声明 ERROR ＋ 3 PASS = **96 PASS** |
| 像素差非零 | 26/129（1/16、25/113） | 21/155（1/14、20/141） |
| `user://` 帧链 | 13055 / 15543 / 171792 / 148841 / 26181（六帧 6/6 不同 sha） | 194130 / 196947 / 196939 / 195563（五帧 5/5 不同 sha） |
| 场景 sha（`e05`=`e09`） | `7e7fb1d9…`（813 B） | `1fcc873e…`（826 B） |
| `project_build_csharp` | exit 0（3732 ms） | exit 0（3678 ms） |
| `project_validate_scripts` / `editor_get_errors` | `invalid_count=0` / `count=0` | `invalid_count=0` / `count=0` |
| 树里 `@` 自动名 | 0（75 个节点名） | 0（333 个节点名） |
| `--import` | exit 0（r1、r2 各一次） | exit 0（r1、r2 各一次） |
| 缺陷（工具 / 游戏或驱动） | 0 / 0（r1 有 G1，已修） | 0 / 0（r1 有 M1，已修） |
| 独立复算不符数 | 0 | 0 |
| 门跑器（本轮） | — | 纯文档：`SKIP_REBUILD` + `GATES_SKIPPED=1` + exit 0（**十道门一门未跑**） |

---

## F. 提交后的逐字复核（本报告自身的提交之前）

**边界说明**：本节的两段帐是**主仓 `67bcbb0` 提交之后、本报告那次提交之前**的那一刻的两仓状态。此后本报告自身的提交（以及任何纯文档追加）只让主仓 `git log` 顶部多出一个**文档**提交；本节里唯一会变旧的是 `git log` 的顶部行与 `git status --short` 的输出，而**「主仓新增 139 个文件、两仓 `git status --short` 均为空、引擎仓与远端同级」**这三点不会因此改变。

### F1 主仓 `F:\moonbit-hof-rs`（分支 `master`，无远端）

`git log --oneline -8`：

```
67bcbb0 feat(godot-mcp): TASK-100 (D148) - the 10th and 11th C# games are delivered through MCP calls only (2048: a 4x4 unknown-number grid with four-direction slide-and-merge, scoring, the 2048 win, the no-legal-move loss and illegal moves refused with a byte-identical board; Minesweeper: a 9x9 ten-mine field from a seeded LCG whose layout the session generator recomputes independently in Python, flood reveal, number hints, flags, first-click safety, win and loss, and illegal operations refused), both with a float-accumulator clock, both with two single-writer increment properties after the G1 defect (one property with two writers read 0 by the time the assertion ran), both replaying the D-3 duplicate-name batch for its -32000 refusal, and the gate runner's doc-only preflight reporting ANCHOR_STRUCTURAL_EQUIVALENT plus SKIP_REBUILD because not one module byte changed
fbf4bf1 docs(godot-mcp): TASK-099 - the report: the two new C# games with their real call counts, verdict distributions, assertion tallies and independently recomputed pixel columns, the Flappy payload defect the multi-frame sample caught with its fix and re-run, the gate runner's doc-only preflight with both measured cases and why it cannot reach either variant, and the third live --import shutdown access violation recorded with 24 more controlled probes at zero crashes and no engine edit
7b5fa56 feat(godot-mcp): TASK-099 - the 8th and 9th C# games are delivered through MCP calls only (Frogger: a 13x15 grid crossing with traffic, logs, homes and lives; Flappy Bird: one fixed 1/60 s frame of gravity, gaps, scoring and collisions, with the Flappy payload defect a 30-frame sample caught fixed and re-run), the gate runner learns to recognise a purely non-compiling submission and skip the ten gates for it while still running them the moment anything can change the compiled binary, the third live --import shutdown access violation is recorded with 24 more controlled probes at zero crashes and no engine edit, and ledger G-1 is closed at the root
5c83668 docs(godot-mcp): TASK-098 - the report: the two new C# games with their before/after runs, the section 7 alignment, the leftover accounting reconciled from a git-status entry count to a file count, the seven-row number re-read, and the import access violation recorded as unreproducible in 64 controlled runs with its static localisation
fdbbed6 feat(godot-mcp): TASK-098 - the 6th and 7th C# games are delivered through MCP calls only, MCP-TRACEABILITY section 7 is aligned with the D-1 closure, and the TASK-096 leftovers are resolved by enforcing the verdict TASK-096 had already recorded
ddc0dbb docs(godot-mcp): TASK-097 - the report's closing boundary is restated so it cannot be made stale by the task's own doc-only follow-ups: the snapshot is the state right after the report commit, and the two follow-ups that exist are listed verbatim
fc54163 docs(godot-mcp): TASK-097 - GAME-LOOP-LOG's TASK-096 re-localisation section gains the one-line closure note, so its "unavailable (D-1)" wording is read as the historical record of the runs before the cleanup rather than as the current state of the pixel column
d1ac6e6 docs(godot-mcp): TASK-097 - the report's closing section: both repositories' real git logs and status lines, the tracked-versus-untracked accounting (0 tracked changes, 136 untracked entries all left over from TASK-096), the engine branch being level with its remote at 094b071f9b, and the post-run process/port check
```

`git status --short`：**空**（本任务的新增与改动全部随 `67bcbb0` 入库；`git show --stat` 给出 **139 files changed, 14831 insertions(+), 1 deletion(-)**，那 1 行删是 `GAME-LOOP-LOG.md` 待办第 4 条的续写替换）。

### F2 引擎仓 `F:\moonbit-hof-rs\godot-mcp\godot`（分支 `feature/mcp-server-module-rebuild`）

`git log --oneline -8`（**与本轮开始时逐字相同 —— 本轮没有提交**）：

```
e041cae270 modules/mcp_server: task099 - REBUILT-2C-MANIFEST gains the 2c-11 section: the gate runner's doc-only preflight (one classifier, dot-sourced from the module's own anchor judge, anchor taken from the built binary's --version, committed range plus working tree, and the two measured cases with all ten gates green in the compile-input one), the third live --import shutdown access violation with its 24 controlled probes at 0 crashes, and the explicit reason why the change to tools/run_gates.ps1 cannot reach either variant (it is a main-repository script, so the engine tree has no byte to rebuild)
0fbd5ec4cb modules/mcp_server: task098 - MCP-TRACEABILITY section 7 is aligned with the D-1 closure
094b071f9b modules/mcp_server: task097 - REBUILT-2C-MANIFEST gains the 2c-10 section: the name-conflict policy the section registers (the default refusal with its complete conflict list, its error code and its opt-in rename), the contract's six shape quantities after the append-only override (177/6/1.22.0/154/73/idempotent, sha 64ddce9f), the ten gates and accept_m1 22/22 with their real exit codes, and the three iron-rule deviations of this task recorded rather than hidden
2385fe2fb5 modules/mcp_server: task097 (D-3) - a requested node name the target parent already carries is now refused instead of silently renamed, so a replayed editor phase can no longer write a whole duplicate node layer into a scene; editor_save_scene reports the duplicates a batch made under an explicit rename instead of saving them silently
95aa1d8984 modules/mcp_server: task096 - MCP-TRACEABILITY gains section 7: what the evidence chain is when the pixel diff is unavailable, and how the ledger is to be read then; the section also carries the re-localisation of D-1 (the duplicate node layer a replayed editor phase writes into a scene), which is why the three older games' pixel column says unavailable rather than 0
8b9dd9a72b modules/mcp_server: task094 - D-2 is a load-sensitive readiness predicate, not a defect: the accept_m1 wait now asks the main loop to advance (frame_count strictly increasing six samples in a row) instead of asking it to be faster than 20 fps, so the suite is 22/22 solo and 22/22 under eight CPU burners
cf554ef58c modules/mcp_server: task092 (B2/B3/B4) step2 - a deferred call's file effects and its capture are collected at completion, the two missing doctests exist, and the frame cost is a clamped median of a window
87fbf82f4b modules/mcp_server: task092 (B1) step1 - an over-bound payload is written whole to a sidecar the line can be checked against, and the ledger re-hashes it
```

`git status --short`：**空**；`git rev-parse HEAD` = `git rev-parse refs/remotes/origin/feature/mcp-server-module-rebuild` = **`e041cae270487d5c910f1e7ebe0e13982886d602`**（与远端同级，本轮未 push 任何东西）。

### F3 收尾后的进程与端口

无残留 `Godot*` 进程；`9940/9941`、`9942/9943` 无 **LISTENING**。**未改变机器显示或串流状态。**
