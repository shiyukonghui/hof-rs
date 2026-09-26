# TASK-098 — 第 6、7 个游戏（Asteroids / Pac-Man）交付；`MCP-TRACEABILITY.md` §7 与 D-1 结案对齐；136 条未跟踪遗留按 TASK-096 已声明的口径落成规则并清空；副本数「5/18/37 对 8/20/37」查清是口径差；`--import` 访问违例 64 次受控复现失败

* 执行者：工具工程师（本会话，**有写权限，不再委派**）
* 主仓：`F:\moonbit-hof-rs`（分支 `master`，无远端）
* 引擎仓：`F:\moonbit-hof-rs\godot-mcp\godot`（分支 `feature/mcp-server-module-rebuild`，remote `git@github.com:shiyukonghui/godot.git`）
* 脚本 / 会话 / 证据：`godot-mcp\recovery\work\task098\`
* 时间：2026-09-27（本会话）

---

## 0. 结论表（每行一句话）

| 段 | 要求 | 结论 | 关键证据 |
|---|---|---|---|
| **A①** | **Asteroids**（C#，只用 MCP 调用开发）：飞船旋转/推进、子弹、小行星分裂、计分与生命；像素列必须真实非零；多帧采样**先采样再改变状态**；证据：采样 + 断言 + 文件 sha + 像素差 + 独立复算 | **做完。** 71 次调用（编辑器 16 / 游戏 55），`facts_complete` **71/71（100%）**，判定分布 `failed=2`（**两条都是声明的**：`e06` 同名批量被 `-32000` 拒绝、`g53` 断言不存在的属性 `-32001`）+ `ok_effect=15` + `ok_file_effect=39` + `ok_no_effect=15`；断言 **24 PASS + 1 条声明的边界失败**；像素差 **16/71 非零**（编辑器 1/16、游戏 15/55），`user://` 六帧逐对 **14774 / 996 / 6346 / 7072 / 8960 px**；独立复算（逐调用对 + 保存帧）与 `report.json` **0 处不符**；`project_build_csharp` **exit 0**、`invalid_count=0`。**TASK-097 的采样时机局限已改正**：`g15` 先把子弹放在 150 px 之外再采 40 帧，`BulletActive` 前 14 帧为 true、**第 14 帧**同时发生 `Score` 0→20 与 `AsteroidsRemaining` 1→2 | `runs\asteroids\ast-task098-r2`、`logs\summary-asteroids-r2.txt`、`logs\samples-asteroids-r2.txt`、`logs\frames-recompute-asteroids.txt` |
| **A②** | **Pac-Man**（C#，只用 MCP 调用开发）：网格迷宫、豆子计数、幽灵巡逻、吃豆得分、胜负 | **做完。** 80 次调用（编辑器 16 / 游戏 64），`facts_complete` **80/80（100%）**，判定分布 `failed=2`（同样两条声明的）+ `ok_effect=14` + `ok_file_effect=39` + `ok_no_effect=25`；断言 **29 PASS + 1 条声明的边界失败**；像素差 **15/80 非零**（编辑器 1/16、游戏 14/64），五帧逐对 **18888 / 1853 / 18546 / 9586 px**；19×13 迷宫、**125 颗豆子**、4 个幽灵与吃豆人全部运行期新建；`g64` 最终树 248 个节点里 **0 个 `@` 名**；声明的 `pac_right` 动作真的把 `PacCol` 推过 9（`all_passed=true`） | `runs\pacman\pac-task098-r2`、`logs\summary-pacman-r2.txt`、`logs\samples-pacman-r2.txt`、`logs\frames-recompute-pacman.txt` |
| **A③** | 跑完给：调用数、判定分布、`facts_complete`、缺陷清单（分「工具缺陷」「游戏或驱动缺陷」）；两行加进 `GAME-LOOP-LOG.md` | **做完。** 台账续到第 6、7 行；**工具缺陷 0 条**；**游戏或驱动缺陷 2 条**（A-1 Asteroids 会话把会被归零的计数器当成会保留，`g36` 期望 120 实得 100；P-1 Pac-Man 把 `GhostSteps` 的累计总数当成一次钩子的增量，`g15` 期望 12 实得 16）——**两条都已修并重跑同批，前后对照列入 §A2** | `GAME-LOOP-LOG.md` 台账第 6/7 行与「游戏或驱动缺陷」表 A-1/P-1 |
| **A④** | 若发现工具缺陷且根因明确 → 修掉 → 重建两变体 → 重跑同一批 → 十门全绿 + `accept_m1` 22/22 + push 到 fork | **不适用，并显式说明。** 本轮**没有发现根因明确的工具缺陷**：唯一的新现象是 `--import` 的间歇性访问违例，根因**不明确**（64 次受控复现全 0），按台账「根因不清楚的只记录、不猜改」处置。因此 `modules\mcp_server` 的**代码一个字节没动**，两变体仍是 TASK-097 在 `2385fe2fb5` 之后重建的那两份 → **未重建、未跑十道门**。引擎仓只有一份**文档**提交并已 push | §C、§D2；`logs\importprobe\` |
| **B①** | 主仓 136 条未跟踪文件逐类判定；最终 `git status --short` 干净 | **做完。** 判定**不是本轮新做的**：`TASK-096-REPORT.md` §D4 早已写下「不入库」。本轮把那条只停在报告措辞里的判定落成机器可执行的 `.gitignore` 规则（原始运行产物随 `godot-mcp/runs/` 一类；结论两份 `report.json`/`report.md` 早已入库、不受影响），并把同一批里 **4 个 0 字节 `tmp_*.tscn`**（§E 的两处重定向滑手的空文件）**先打印清单再删除**。收尾时主仓 `git status --short` **为空** | `cleanup_task096_leftovers.ps1`、`.gitignore`、§B1 |
| **B②** | `MCP-TRACEABILITY.md` §7 的措辞与结案状态对齐（写清 D-1 已结案与像素证据恢复的条件/边界），纯文档提交 | **做完。** 加**结案横幅**（D-3 已在 TASK-097 修在根上、「不可得（D-1）」从此只是清理之前那些运行的**历史记录**）；副本表改成 **8/20/37** 并注明 `5/18/37` 是**只数 `@ColorRect@`** 的口径；**新增 §7.3**：结案后本节仍生效的**四条条件**与**三条边界** | §B2、引擎提交 `0fbd5ec4cb` |
| **B③** | 核对 `GAME-LOOP-LOG.md` 与各报告的数字一致性；冲突以证据为准更新并注明历史口径 | **做完。7 行全部一致**（调用数 / `facts_complete` / 像素列 / 帧链，逐项从各自引用的产物重读）。唯一的差别是**副本数的口径**而不是数字冲突：**5/18/37**（只数 `@ColorRect@`）对 **8/20/37**（含 `@Label@`），从清理会话读回来的**清理前场景原文**逐个数后两处都加了注 | `logs\log-consistency.txt`、`logs\copy-count-evidence*.txt`、§B3 |
| **C** | 留意 `--import` 是否复现 `exit=-1073741819`；复现给最小复现与定位方向，不复现记录本轮次数与结论 | **复现了 1 次**（`ast-task098-r1`，症状与 TASK-097 一字不差），另外 3 次会话导入 `exit=0`；**受控复现 64 次全部 `exit=0`**。因为**导入本身已经跑完**（日志到 `[ DONE ]`），这是**关机期崩溃、不是导入失败**。定位方向已给（`is_cmdline_mode` 在引擎里只有一个调用者，是 `call_deferred` 排上来的脚本类更新）。**不改模块、不做结论** | §C、`logs\importprobe\probe-all.txt` + 三份 `probe-results*.json` |
| **D** | 主仓提交（含 `GAME-LOOP-LOG.md` 与两款游戏工程）；报告含两仓 `git log --oneline -8` 与 `git status --short`；时间不够如实报告 | **做完。** 主仓 `fdbbed6`（90 个文件）；引擎仓 `0fbd5ec4cb` 已 push（`094b071f9b..0fbd5ec4cb`）且与远端同级。两仓 `git status --short` 均为**空**；跑完后无 `Godot*` 进程、`9877 / 9930–9933 / 9950–9999` 无监听 | §D2、§D3 |

---

## A. 第 6、7 个游戏（C#，只用 MCP 调用开发）

### A1 形态与开发方式（两款同一套脚手架）

两款都从模板实例化（`tools\new_game.ps1 -Name asteroids -Class AsteroidsGame` / `-Name pacman -Class PacManGame`），**游戏内容全部由 MCP 调用写成**：`project_edit_script`（C# 载荷替换模板桩）、`editor_add_nodes_batch`（3 个静态节点）、`editor_add_input_action`、`editor_save_scene`、`project_build_csharp`、`project_validate_scripts`。

**场景各只有 3 个静态节点**（`Background` / `Hud` / `Status`），主体全部在 `_Ready()` 里**运行期新建**：

| 游戏 | 运行期新建的东西 | 为什么这样分 |
|---|---|---|
| Asteroids | 飞船 1、子弹 1、岩石 4→2 | 场景保持干净（编辑相 16 次调用），不会被 D-3 的同名陷阱咬到；「运行期新建的节点确实被画出来」成为这款游戏自己的证据 |
| Pac-Man | 墙壁（迷宫 `#`）、**125 颗豆子**、4 个幽灵、吃豆人 1 | 同上；最终树 248 个节点，全部是 `Wall_r{r}_c{c}` / `Pellet_r{r}_c{c}` / `Ghost_n` / `Pac` 这些**自己起的名字** |

**确定性规则（继承前五款）**：三件事默认关闭，只有测试显式开启 —— 岩石不漂移（`DriftSpeed=0`）、幽灵不自动巡逻（`GhostSpeed=0`）、不吃输入（`PollInput=false`）；每一个积分 `delta` 的运动都有**固定步长钩子**（`RotateShip` / `ThrustStep` / `StepRocks` / `StepPac` / `StepGhosts`），所以「飞船动了」「幽灵巡逻了」不可能是帧率噪声；`ForceTestState(spec)` 一个调用钉死整盘状态。**所有事实都是根节点上的真 Godot 属性**，断言用 `running_game_assert_node_state`，不解析任何日志行。

**两款都在建场景的那一步故意把同一批节点再跑一次**（`e06`），让 D-3 的拒绝在每一轮证据里都留下一条：

```
{"error":{"code":-32000,"message":"Refused: 3 node(s) of this batch would duplicate a name that
 already exists under the target parent (Background, Hud, Status)", …}}
```

`e05` / `e09` 的 `project_read_text_file` sha **逐字节相同** —— 被拒的那一批一个字节都没写。

### A2 终轮真实输出（首轮 / 重跑对照）

**A-1（Asteroids 会话缺陷）：** 首轮 `runs\asteroids\ast-task098-r1` 的 `g36-assert-score-120` **FAIL（actual=100）**。会话假设 `ForceTestState` 只换棋盘、保留计数器，而它按确定性规则把**整个状态**钉死（`Score=0`）。**改**：期望值改成 **100**，并把「那 20 分钉在 `g19`」写进注。重跑前先把旧工程**移动归档**（先写 sha 清单再 move，不删除）并重新实例化。

**P-1（Pac-Man 会话/载荷缺陷）：** 首轮 `runs\pacman\pac-task098-r1` 的 `g15-assert-patrol-12` **FAIL（actual=16）**。会话把 `GhostSteps`（累计总数）当成一次 `StepGhosts(12)` 的增量；前面 30 帧采样在 `GhostSpeed=8` 下已经让时钟推进了 4 步，而**帧率决定它是 3 还是 5**（写对总数也仍会抖）。**改**：载荷新增真导出属性 **`LastPatrolSteps`**（一次钩子调用的增量），会话改成断言增量 `eq 12` + 总数 `gt 12` —— 与帧率无关。

| | Asteroids r1 | Asteroids **r2** | Pac-Man r1 | Pac-Man **r2** |
|---|---|---|---|---|
| 调用数 | 71（16 / 55） | **71（16 / 55）** | 79（16 / 63） | **80（16 / 64）** |
| `facts_complete` | 71/71 | **71/71** | 79/79 | **80/80** |
| 断言 | 23 PASS + **1 FAIL** + 1 声明 ERROR | **24 PASS + 1 声明 ERROR** | 27 PASS + **1 FAIL** + 1 声明 ERROR | **29 PASS + 1 声明 ERROR** |
| 像素差非零 | 15/71 | **16/71** | 15/79 | **15/80** |
| 判定分布 | `failed=2` + `ok_effect=15` + `ok_file_effect=33` + `ok_no_effect=21` | **`failed=2` + `ok_effect=15` + `ok_file_effect=39` + `ok_no_effect=15`** | `failed=2` + `ok_effect=14` + `ok_file_effect=43` + `ok_no_effect=20` | **`failed=2` + `ok_effect=14` + `ok_file_effect=39` + `ok_no_effect=25`** |
| `user://` 帧链 | — | **14774 / 996 / 6346 / 7072 / 8960** | 18888 / 1853 / 18546 / 9586 | **18888 / 1853 / 18546 / 9586** |
| 缺陷（工具 / 游戏或驱动） | 0 / 1 | **0 / 0** | 0 / 1 | **0 / 0** |

> 两轮都是 `failed=2`，且**两条都是声明的**：编辑器相那一次同名拒绝（`-32000`）+ 一条故意打在不存在属性上的边界断言（`-32001`）。`report.json` 的自动缺陷清单只有这两条。

### A3 证据形态（任务书要求的四类都用上了）

**① 多帧属性采样（先采样再改变状态）**

| 采样 | 帧数 | 结果 |
|---|---|---|
| Asteroids `g08-samples-frozen` | 12 | 冻结基线：`ShipX` / `ShipY` / `FirstRockX` **各只有 1 个值**，`Ticks` 12 个不同值（时钟在走、画面不动） |
| Asteroids `g10-samples-drift` | 30 | `FirstRockX` **30 个不同值**（156.10→199.71）、`FirstRockY` 30 个不同值 |
| Asteroids `g15-samples-flight` | 40 | `BulletY` 15 个不同值；`BulletActive` 前 14 帧 `true`；**第 14 帧**同时 `Score` 0→20、`AsteroidsRemaining` 1→2 —— **飞行与击杀落在同一窗口内**（TASK-097 的采样时机局限就此改正） |
| Pac-Man `g10-samples-frozen` | 12 | `Ghost0Col` / `Ghost0Row` / `PacCol` 各 1 个值，`Ticks` 12 个不同值 |
| Pac-Man `g12-samples-patrol` | 30 | `Ghost0Col` / `Ghost0Row` 各 **30 个不同值**，`GhostSteps` 递增 |

**② 断言** —— Asteroids：`Score` 0→20→100、`AsteroidsRemaining` 4→1→2、`AsteroidsSplit=1`、`AsteroidsDestroyed=1`、`FirstRockSize=2`、`ShipX` 400→**452**、`ShipVelX`=**104**、`ShipAngle`=**-45**、`Lives` 3→**2**→**0**、`ShipAlive=false`、`Won` true（清场）/ false（阵亡）、`GameOver` true（胜）与 true（负）、屏幕文本 `FIELD CLEARED` / `GAME OVER`。Pac-Man：`TotalPellets=125`、`PelletsRemaining` 125→2→1→0、`PelletsEaten` 0→1、`Score` 0→10、`PacCol` 9→**10**、撞墙**不移动**（`blocked at=9,8 from=9,9`）、`Lives` 3→**2**→**0**、`Won` true（豆子清空）/ false（被抓）、`LastPatrolSteps` 5、`GhostSteps` gt 12、屏幕文本 `MAZE CLEARED` / `GAME OVER`。

**③ 文件 sha** —— 两款各自的 `e05` / `e09` `project_read_text_file` sha 与拒绝前**逐字节相同**；`editor_add_nodes_batch` 的 `file_effect=changed` 各 1 次；编辑器相各 `sidecar_verified=1`（C# 载荷超限走旁路证据）。

**④ 像素差 + 独立复算** —— 见 A4。

### A4 独立复算（不是转述）

`recovery\work\task098\pixel_recompute.py`（逐调用 capture 对，**自己**解码 PNG、用自己的两条规则各算一遍）与 `frames_recompute.py`（`user://` 保存帧，**自己**按 mtime 排序、自己 sha256、自己对 `report.json` 的数字）：**逐对一致、0 处不符**。

| 运行 | 逐调用对 非零（引擎规则 >10） | 任一字节差异规则 | trace 记录的数与复算不符的对 | 帧链（复算） |
|---|---|---|---|---|
| Asteroids | **16/71**（编辑器 1/16、游戏 15/55） | 同样 16/71 | **0** | 14774 / 996 / 6346 / 7072 / 8960 |
| Pac-Man | **15/80**（编辑器 1/16、游戏 14/64） | 同样 15/80 | **0** | 18888 / 1853 / 18546 / 9586 |

`user://` 帧的 sha256 与 `report.json` 记录的**逐一相同**（磁盘上的文件没有被后续运行覆盖），Asteroids 的六个帧是**六个不同的 sha** —— 「画面确实在变」不是一句形容词。

### A5 游戏侧的一处自保（与 D-3 同一个陷阱，在游戏里避开）

Pac-Man 每次 `ForceTestState` 都会**重建整个棋盘**。若直接 `QueueFree()`，节点要到**帧末**才真正离开场景树，同一帧里重建的 `Wall_r2_c3` 会发现名字还被占着 —— Godot 就把它改名成 `@ColorRect@N`。**这正是 D-3 的形状**，只是发生在运行期节点上。做法是先 `RemoveChild()`（立刻释放名字）再 `QueueFree()`。实测：`g64` 的 **248 个节点里 0 个 `@` 开头的名字**。（Asteroids 用单调递增的 `Rock_{seq}` 命名，天然避开，`g55` 最终树同样没有 `@` 名。）

### A6 缺陷清单

**工具缺陷（`modules\mcp_server`）：0 条。** 两款游戏 151 条调用里没有一条是「工具做错了事」；唯一的非 `ok` 判定是两条**声明的**边界调用（同名拒绝 `-32000`、不存在的属性 `-32001`），以及首轮两条**会话自己的**期望值错误（A-1 / P-1）。

**游戏或驱动缺陷：2 条，均已知根因、已修、已重跑同批对照。**

| id | 现象（证据） | 根因 | 处置 → 重跑结果 |
|---|---|---|---|
| **A-1** | Asteroids 首轮 `g36-assert-score-120` FAIL、actual=100（`runs\asteroids\ast-task098-r1`） | 会话假设 `ForceTestState` 保留计数器；它按确定性规则把整个状态钉死 | 期望改 **100**，注里说明 20 分钉在 `g19`；r2 `g36` PASS |
| **P-1** | Pac-Man 首轮 `g15-assert-patrol-12` FAIL、actual=16（`runs\pacman\pac-task098-r1`） | 会话把**累计总数**当成一次钩子的**增量**，而总数含帧率相关的时钟步数 | 载荷加 `LastPatrolSteps`，断言改成「增量 eq 12」+「总数 gt 12」；r2 两条 PASS |

---

## B. 清理遗留 + 文档对齐

### B1 136 条未跟踪文件：逐类判定与处置

**判定不是我做的。** `TASK-096-REPORT.md` §D4 早已写下：

> `recovery\work\task096\reporttest-pong\` 的其余部分（pong 重放目录的副本：PNG / trace / 逐调用 json）与 `tmp_*.tscn` … **不入库**：前者是 `runs\` 的临时副本（只为验证工具改动，已入库 `report.md`/`report.json` 两份结论）；后者是两处重定向滑手的空文件

挂着 136 条的唯一原因是：**那条判定只停在报告措辞里，从来没有变成机器可执行的规则**。本轮把它落成规则。

| 类别 | 数量 | 处置 | 理由 |
|---|---|---|---|
| `reporttest-pong\report.json` / `report.md` | 2 | **保持入库**（本来就已在库里） | 它们是那一轮的**结论** |
| `reporttest-pong\` 的其余部分（trace / 逐调用 json / `shots-*` PNG / ledger / 引擎日志） | 236（全部 238 减去两份结论） | **加 `.gitignore`**（`reporttest-pong/*` + 两条 `!` 例外） | 与 `godot-mcp/runs/` 同类：原始运行产物，盘上留着供复算与重放，不进历史（5.27 MB） |
| `tmp_{pong,breakout,snake}_*.tscn` | 4 | **先打印清单再删除**（`cleanup_task096_leftovers.ps1`；四个都是 **0 字节**） | §E 自陈的两处 `>` 重定向滑手的空文件，TASK-096 已判「不入库」；0 字节文件留着没有任何信息 |

`cleanup_task096_leftovers.ps1` 的守卫：目标一律**绝对路径**、禁通配符与 `..`、必须落在 `recovery\work\task096\` 白名单前缀内、**必须 0 字节**、**默认 dry-run**（`-Execute` 才动手）。

> **「136」是 git status 的条目数，不是文件数，这里把两个口径对齐**：`git status --short` 会把**整体未被跟踪的子目录折叠成一行**。
> 出发时的 136 条 = `reporttest-pong\` 顶层 131 个文件 − 已入库的 2 份结论 = **129 行**，加上
> `shots-editor\` / `shots-game\` / `trace-editor.sidecar\` 三个折叠目录行 = **132 行**，再加 4 个
> `tmp_*.tscn` = **136**。按**文件**数是 `reporttest-pong\` 的 **236** 个 + `tmp_*.tscn` **4** 个 = **240 个**。
> 上表按文件数登记（236 / 2 / 4），所以它加起来是 242 而不是 136 —— 两个数说的是不同的东西，
> 差别全部来自目录折叠，没有任何文件被漏掉。（折叠行为已用一个最小仓库实测确认：两个完全未跟踪的
> 子目录各占 **1 行**，`-uall` 才逐个列出文件。）

**结果**：收尾后主仓 `git status --short` **为空**。

### B2 `MCP-TRACEABILITY.md` §7 与结案状态对齐（纯文档提交 `0fbd5ec4cb`）

§7 是在 D-1 **尚未结案**时写的，条件式措辞会让一个已结案的缺陷读起来像当前状态。三处改动：

1. **结案横幅**（本节开头）：写清 D-1 的根因是工具缺陷 **D-3**、**TASK-097 已修在根上**（默认拒绝同名 + `data.conflicts`；显式 `"rename"` 才改名且保存侧报告 `duplicates`）、三个老场景的副本层已删、像素列已回填真实数值（14/74、14/89、13/102，独立复算一致）。结论句：**「不可得（D-1）」是历史记录，不是当前状态。**
2. **§7.1 的副本表**：`5 / 18 / 37` → **`8`（5+3）/ `20`（18+2）/ `37`（37+0）**，并加**口径注**说明旧数是**只数 `@ColorRect@*`**。
3. **新增 §7.3「结案之后这一节什么时候还适用」**：四条**条件**（场景干净 / 画面真的有东西在动 / 一条数字必须带自己的对照 / `--pixel-evidence` 选对档）+ 三条**边界**（不承诺任何场景都能拿到非零像素差；像素差不证明游戏逻辑正确；三个老游戏的「不可得」字样不再更新，它们是那段时间的忠实记录）。

### B3 `GAME-LOOP-LOG.md` 与各报告的数字一致性

`recovery\work\task098\log_consistency.py` **从每一行自己引用的那份产物里**重读数字（不照旧报告抄）：

| 行 | 台账写的 | 产物复查 |
|---|---|---|
| Pong | 52/52；像素 14/74（3/45、11/29）；帧 512 / 512 / 7175 | **一致** |
| Breakout | 55/55；像素 14/89（2/55、12/34）；帧 3072 / 3464 / 2529 / 2169 | **一致** |
| Snake | 51/51；像素 13/102（0/71、13/31）；帧 480000 / 4032 / 480000 | **一致** |
| Tetris | 42/42；像素 11/42；帧 3174 / 4232 / 8503；首轮 53 次 | **一致** |
| Space Invaders | 59/59；像素 12/59（1/15、11/44）；帧 1576 / 38127 / 16990 / 4800 | **一致** |
| Asteroids（新） | 71/71；像素 16/71（1/16、15/55）；帧 14774 / 996 / 6346 / 7072 / 8960 | **一致** |
| Pac-Man（新） | 80/80；像素 15/80（1/16、14/64）；帧 18888 / 1853 / 18546 / 9586 | **一致** |

**发现的唯一差别是口径，不是数字冲突**：D-3 / §7.1 的 **5 / 18 / 37** 是只数 `@ColorRect@*`；把 `@Label@*` 一并算进来是 **8 / 20 / 37**。证据是**清理会话自己从盘上读回来的清理前场景原文**（`runs\<game>\<game>-clean-task097\c03-read-before.json`）：

| 游戏 | `@ColorRect@` | `@Label@` | 自动名合计 | 具名节点 | 场景字节 | 与 TASK-097 报告的清理前尺寸 |
|---|---|---|---|---|---|---|
| Pong | 5 | 3 | **8** | 9 | 3391 | **吻合** |
| Breakout | 18 | 2 | **20** | 21 | 8553 | **吻合** |
| Snake | 37 | 0 | **37** | 38 | 13284 | **吻合** |

→ `copy_count_evidence.py` 逐个列出 `@...@` 名字重新数过；`GAME-LOOP-LOG.md` 的 D-3 行与 `MCP-TRACEABILITY.md` §7.1 **两处都加了「历史口径」注**。**没有改掉任何一个旧数字**，因为两个数都对。

**另外核过一处容易读错的地方**：`report.json` 的 `diff_vs_prev` 记在**目标帧**上，配对是「与上一个**同尺寸**帧」，而 `user://` 目录里会留着更早实验的 PNG。台账写「`snake-t2`→`final` 480000」时读法必须是**帧链**（t0→t1→t2→final）。`frames_recompute.py` 独立按 mtime 重算三个老游戏的帧链，与 `report.json` **0 处不符**。

台账还新增了一节「台账数字一致性复核（TASK-098）」把上面这张表写进文档，并更新了待办。

---

## C. `--import` 的间歇性访问违例（`exit=-1073741819`）

### C1 症状与出现次数（本轮真实输出）

| 来源 | 结果 |
|---|---|
| **本轮会话导入 4 次** | `ast-task098-r1` **崩溃**；`ast-task098-r2` / `pac-task098-r1` / `pac-task098-r2` `exit=0` |
| **TASK-097 的 7 次** | `d3-after` 首轮**崩溃**；其余 6 次 `exit=0` |
| **累计** | **2 次 / 11 次会话导入** |

崩溃时的真实输出（与 TASK-097 一字不差）：

```
IMPORT_EXIT=-1073741819

ERROR: Parameter "singleton" is null.
   at: EditorNode::is_cmdline_mode (editor\editor_node.cpp:6750)
```

**关键观察**：崩溃发生前，导入**已经跑完** —— stdout 里 `first_scan_filesystem` 与
`loading_editor_layout` 都已 `[ DONE ]`。所以这是**关机期的崩溃，不是导入失败**。

### C2 受控复现：64 次，全部 `exit=0`

`recovery\work\task098\import_crash_probe.ps1`（铁律 1：`Start-Process -RedirectStandardOutput/-RedirectStandardError` 拥有 stdout/stderr；铁律 3：子进程是 `cmd.exe`；铁律 4：每次唯一端口且**先确认该端口空闲**）。每一次导入都在自己的**新副本**上跑（不删除任何东西），并跑「冷（无 `.godot`）→ 热」两轮：

| 变体 | 次数 | 崩溃 |
|---|---|---|
| 我方引擎，**唯一端口**，C# 12 + GDScript 12 | **24** | **0** |
| 我方引擎，**默认端口 9877**（真实会话的做法），C# | **16** | **0** |
| **stock Godot 4.7.1 mono**，默认端口，C# 12 + GDScript 12 | **24** | **0** |
| 合计 | **64** | **0** |

**已排除的变量**：项目语言（C# 与 GDScript 各 12 次全 0）、冷热（首次全量扫描与热导入各 32 次全 0）、端口（唯一端口 24 次全 0）、引擎（stock 与我方各半，全 0）。**结论：无法按需复现**，它是低频环境/时序事件（观测频率约 2/11，但 64 次探针 0 次）。

### C3 定位方向（静态证据，不是猜测）

`EditorNode::is_cmdline_mode()`（`editor\editor_node.cpp:6749`）里 `ERR_FAIL_NULL_V(singleton, false)` 就是那行 stderr 的来源。全树搜索它在引擎里**只有一个调用者**：

```
editor\file_system\editor_file_system.cpp:2301:  if (!EditorNode::is_cmdline_mode()) {
```

那行在 `EditorFileSystem::_process_update_pending()` 里（`editor_file_system.cpp:2297`），而 `_process_update_pending` 是
`_queue_update_script_class()`（同文件 2307 行）排上来的**延迟调用**，触发条件是**某个脚本的类信息发生变化**。
→ **定位方向：一条延迟的脚本类更新回调在编辑器析构之后仍然执行，于是撞上 `singleton == null`。**

下一批该做的判别（已写进 `GAME-LOOP-LOG.md` 待办 2）：

1. 在 `EditorNode` 析构前后把 `_process_update_pending` 的调用点打桩，看它是否真的在 `singleton` 被清空之后被调用；
2. 用 `EditorNode::get_singleton()` 的空值检查替换掉这条路径上的 `ERR_FAIL_NULL_V`（或让 `is_cmdline_mode()` 在 `singleton == null` 时**不打印**），看崩溃是否随之消失 —— 这会把「只是打印了警告」与「同一帧里还有别的空指针解引用」分开；
3. 若 2 之后仍崩，崩溃就不在这条路径上，应改用 crash dump（`procdump -e`）拿真实栈。

**本轮的决定：不改模块。** 台账自己的口径是「根因不清楚的只记录、不猜改」；没有可证的根因就没有可回滚的改动。**对跑测试的实际影响**：它不影响导入结果，但 `IMPORT_EXIT` **不能当健康信号用**（`run_game_session.ps1` 现在只在日志里记一行，不据此判失败）。「不改模块」也意味着**本轮不重建、不跑十道门** —— 见 §D1。

---

## D. 收尾

### D1 「没有模块字节改动 → 不重建、不跑十道门」这个取舍

`modules\mcp_server` 本轮**代码一个字节没动**（引擎仓 `git diff` 只有
`docs\reports\MCP-TRACEABILITY.md` 一份文档，58 行增 4 行删）。两变体的二进制仍是 TASK-097 在模块提交
`2385fe2fb5` 之后重建的那两份（`4.8.dev.mono.custom_build.2385fe2fb` / `4.8.dev.custom_build.2385fe2fb`）。

因此：

* **未重建两变体**：没有源改动可重建；
* **未跑十道门**：门账的意义是「这次改动没有破坏什么」；源未变，跑门只会把锚点差集从「0」变成「1 个声明过的非编译文件」（TASK-097 §D1 已经预告过这一点），拿不到新信息；
* **未 push 代码**：没有代码可 push；引擎仓本次要 push 的是**文档提交**，已 push（§D3）。

**这是显式的取舍，不是遗漏。** 若下游认为「任何提交都必须带一次门账」，那么需要的改动是让门跑器把**纯文档提交**识别为 `ANCHOR_STRUCTURAL_EQUIVALENT` 并跳过重建，而不是每轮空跑一遍。

### D2 提交与两个仓库

**引擎仓**（分支 `feature/mcp-server-module-rebuild`）：

```
0fbd5ec4cb modules/mcp_server: task098 - MCP-TRACEABILITY section 7 is aligned with the D-1 closure
094b071f9b modules/mcp_server: task097 - REBUILT-2C-MANIFEST gains the 2c-10 section: …
2385fe2fb5 modules/mcp_server: task097 (D-3) - a requested node name the target parent already carries is now refused …
95aa1d8984 modules/mcp_server: task096 - MCP-TRACEABILITY gains section 7: …
```

push 的真实输出：

```
To github.com:shiyukonghui/godot.git
   094b071f9b..0fbd5ec4cb  feature/mcp-server-module-rebuild -> feature/mcp-server-module-rebuild
```

`git rev-parse HEAD` = `git rev-parse refs/remotes/origin/feature/mcp-server-module-rebuild` = **`0fbd5ec4cbdfe58e22fa21119575f24495460bd1`**；`git status --short` **空**。

**主仓**（分支 `master`，无远端）：`fdbbed6`（90 个文件，13393 行增 3 行删）。两仓的 `git log --oneline -8` 与 `git status --short` 见 §G。

### D3 收尾后的进程与端口

最后一轮（stock A/B 探针）之后：无 `Godot*` 进程；`9877`、`9930–9933`、`9950–9999` 均无 **LISTENING**。**未改变机器显示或串流状态**（未停 `GameViewer`、未动设备/注册表/电源/显示拓扑）。

### D4 铁律遵守（含三处自陈滑手）

| 铁律 | 遵守情况 |
|---|---|
| ① 禁止一切 shell 重定向 | **主体遵守**：所有构建/运行由 `Start-Process -RedirectStandardOutput/-RedirectStandardError` 拥有 stdout/stderr（`tools\run_game_session.ps1`、`recovery\work\task098\run_cmd.ps1`、`import_crash_probe.ps1`）；所有文本文件由 Python 写入器、`write`/`edit` 工具或 `Set-Content -LiteralPath` 写；`collect_evidence.py` 用的是 Python `subprocess` 的 `stdout=<file handle>`（进程 API，不是 shell 重定向）。**一处滑手，如实登记**：`git push … 2>&1`（把 git 的进度输出并进管道，**没有写任何文件**，输出已按原样记进 §D2）。 |
| ② 破坏性命令默认拒绝 | 唯一的两处破坏性动作都走了守卫脚本且**先打印清单**：删除 4 个 **0 字节** `tmp_*.tscn`（绝对路径、白名单前缀、禁通配符、默认 dry-run）；重置工程用 `Move-Item` **移动归档**（先写 sha 清单），**自始至终没有删除任何工程**。探针的每一次导入都在自己的**新副本**上跑。未杀任何非本任务进程，未改设备/注册表/电源/显示拓扑。 |
| ③ 构建与运行从 cmd 启动 | 全部由生成的 `.cmd` 经 `Start-Process cmd.exe /c` 启动（`run_game_session.ps1` 的 import/引擎/ledger/report、`run_cmd.ps1`、`import_crash_probe.ps1`）；`dotnet build` 由 `project_build_csharp` 触发。 |
| ④ 唯一端口 + 跑前查进程与端口 | 会话：`9930/9931`（asteroids r1、r2）、`9932/9933`（pacman r1、r2）；探针：`9950–9973`、`9980–9991`（每次唯一，且 `Assert-FreePort` 先查），默认端口变体先查 `9877`。每次开跑前 `netstat`/`Get-Process` 确认无残留。 |
| ⑤ 会话文件双解析后才执行 | 两个自造会话在开引擎之前都过 `check_session.py`（Python JSON + 形状 + `content_file` 可达；两次重生成都重跑）与 `check_session.ps1`（PS 5.1 `ConvertFrom-Json`），两侧都 PASS 才执行（各 74 / 80 次调用）。 |
| ⑥ 迁移/删除一律先复制或先存证 sha | `reset_game_project.ps1` 在 move **之前**写出该工程 8 个有意义文件的 sha256 清单（`archive\*.manifest.json`，已入库），再 `Move-Item`；归档的工程文件也已入库（`archive\` 18 个文件）。 |
| ⑦ 不改变机器显示或串流状态 | 未停 `GameViewer`、未改设备/注册表/电源、未接触显示拓扑。 |

---

## E. 本任务产出的文件

```
recovery\work\task098\
  check_session.py / check_session.ps1       会话双解析（Python + PS 5.1，从 TASK-097 沿用）
  run_cmd.ps1                                统一运行器（Start-Process，无 shell 重定向）
  make_session_asteroids.py                  两款游戏的会话生成器（可逐字重生成）
  make_session_pacman.py
  reset_game_project.ps1                     工程归档 + 重新实例化（先写 sha 清单再 move）
  cleanup_task096_leftovers.ps1              TASK-096 遗留的清单式删除（默认 dry-run）
  import_crash_probe.ps1                     --import 访问违例探针（唯一端口/默认端口/stock A/B）
  make_probe_log.py                          把 64 次探针日志折成一份逐字转录
  pixel_recompute.py                         独立像素复算（逐调用 capture 对）
  frames_recompute.py                        独立像素复算（user:// 保存帧 + 与 report.json 对照）
  samples.py / assertions.py / run_summary.py    采样摘要 / 全断言扫描 / 一轮的四个数字
  log_consistency.py                         从各行自己引用的产物里重读台账数字
  copy_count_evidence.py                     从清理前场景原文里数副本（逐个列出 @ 名）
  callread.py / inspect 读取器               （原名 inspect.py，因会遮蔽标准库而改名）
  collect_evidence.py                        把上面每一项的输出落成 logs\*.txt
  payload\{asteroids,pacman}\*.cs            载荷副本（与 tools\sessions\...\payload 同一份字节）
  archive\*.manifest.json + 归档工程         两个 r1 工程的 sha 清单与文件（先存证再移动）
  logs\                                      21 份证据日志 + logs\importprobe\（转录 + 3 份 JSON）
  commit-msg-main.txt / commit-msg-engine.txt
tools\sessions\{asteroids,pacman}\session.json + payload\*.cs
projects\asteroids\ / projects\pacman\      由模板实例化、随后全部由 MCP 调用写成
runs\asteroids\ast-task098-{r1,r2}\、runs\pacman\pac-task098-{r1,r2}\      （盘上路径；runs\ 按 .gitignore 不入库）
GAME-LOOP-LOG.md                            第 6/7 行 + 两条缺陷 + 一致性复核节 + 待办更新
DECISIONS.md                                D146
godot\modules\mcp_server\docs\reports\MCP-TRACEABILITY.md   §7 结案对齐 + 新增 §7.3
.gitignore                                  两条新规则（TASK-096 report-test 原始产物、TASK-098 探针工作区）
```

> `runs\` 与 `recovery\work\task098\importprobe\` 按 `.gitignore` 不入库（盘上真实存在）；本报告所有
> `runs\...` 引用都是盘上路径。`recovery\work\task098\` 的其余部分、两款游戏工程与引擎文档均已入库。

---

## F. 真实跑出来的数字速查（都可在盘上复算）

| 项 | Asteroids | Pac-Man |
|---|---|---|
| 调用数（编辑器 / 游戏） | 71（16 / 55） | 80（16 / 64） |
| `facts_complete` | 71/71（100%） | 80/80（100%） |
| `args_evidence` | 编辑器 `sidecar_verified=1` + `inline_complete=15`；游戏 `inline_complete=55` | 编辑器 `sidecar_verified=1` + `inline_complete=15`；游戏 `inline_complete=64` |
| 判定分布 | `failed=2` / `ok_effect=15` / `ok_file_effect=39` / `ok_no_effect=15` | `failed=2` / `ok_effect=14` / `ok_file_effect=39` / `ok_no_effect=25` |
| 断言 | 24 PASS + 1 声明 ERROR | 29 PASS + 1 声明 ERROR |
| 像素差非零 | 16/71（1/16、15/55） | 15/80（1/16、14/64） |
| `user://` 帧链 | 14774 / 996 / 6346 / 7072 / 8960 | 18888 / 1853 / 18546 / 9586 |
| `project_build_csharp` | exit 0（3808 ms） | exit 0 |
| `project_validate_scripts` | `invalid_count=0` | `invalid_count=0` |
| `editor_get_errors` | `count=0` | `count=0` |
| 缺陷（工具 / 游戏或驱动） | 0 / 0（r1 有 1 条已修） | 0 / 0（r1 有 1 条已修） |

---

## G. 提交后的逐字复核（本报告自身的提交之前）

**边界说明（把话说死）**：本节的两段帐是**主仓 `fdbbed6` 与引擎仓 `0fbd5ec4cb` 提交之后、本报告那次提交之前**的那一刻的两仓状态。此后本报告自身的提交（以及任何纯文档追加）只让主仓 `git log` 顶部多出一个**文档**提交；本节里唯一真正会变旧的事实是 `git log` 的顶部行与 `git status --short` 的输出，而**「主仓新增 90 个文件、两仓 `git status --short` 均为空、引擎仓与远端同级」**这三点不会因为多一个文档提交而改变。

### G1 主仓 `F:\moonbit-hof-rs`（分支 `master`，无远端）

`git log --oneline -8`：

```
fdbbed6 feat(godot-mcp): TASK-098 - the 6th and 7th C# games are delivered through MCP calls only, MCP-TRACEABILITY section 7 is aligned with the D-1 closure, and the TASK-096 leftovers are resolved by enforcing the verdict TASK-096 had already recorded
ddc0dbb docs(godot-mcp): TASK-097 - the report's closing boundary is restated so it cannot be made stale by the task's own doc-only follow-ups: the snapshot is the state right after the report commit, and the two follow-ups that exist are listed verbatim
fc54163 docs(godot-mcp): TASK-097 - GAME-LOOP-LOG's TASK-096 re-localisation section gains the one-line closure note, so its "unavailable (D-1)" wording is read as the historical record of the runs before the cleanup rather than as the current state of the pixel column
d1ac6e6 docs(godot-mcp): TASK-097 - the report's closing section: both repositories' real git logs and status lines, the tracked-versus-untracked accounting (0 tracked changes, 136 untracked entries all left over from TASK-096), the engine branch being level with its remote at 094b071f9b, and the post-run process/port check
4e2b85b feat(godot-mcp): TASK-097 - D-3 is fixed at the root: editor_add_nodes_batch refuses a requested name the target parent already carries instead of letting the engine rename it into a duplicate, editor_save_scene reports the duplicates an explicit rename leaves behind, the duplicate layer is removed from the three older scenes and their pixel-diff column is refilled with real numbers (Pong 14/74, Breakout 14/89, Snake 13/102, independently recomputed), and the fifth C# game Space Invaders is delivered through MCP calls only (59/59 facts, 12/59 non-zero pixel diffs, first-run green)
aa64293 docs(godot-mcp): TASK-096 - the report's boundary note: the closing snapshot describes the state before this doc-only follow-up, and the follow-up carries this very sentence
4173162 docs(godot-mcp): TASK-096 - the report's closing section carries the post-commit git logs of both repositories verbatim, so the snapshot in its body cannot be made stale by the report's own commit
b84bc87 docs(godot-mcp): TASK-096 - the report: the ownership A/B (the same operation batch is normal on both engines and on a clean probe project, so the answer is neither our regression nor an upstream behaviour nor the presentation layer but the duplicate node layer a replayed editor phase writes into a scene), the occlusion proof with its recomputable colours, the pixel column becoming unavailable (D-1) with the replacement evidence chain, and the 4th C# game Tetris with its three fixed defects and their before/after runs
```

`git status --short`：**空**（本项目出发时的 **136 条未跟踪**已按 §B1 清零；TASK-098 自己的新增全部随 `fdbbed6` 入库）。

### G2 引擎仓 `F:\moonbit-hof-rs\godot-mcp\godot`（分支 `feature/mcp-server-module-rebuild`）

`git log --oneline -6`：

```
0fbd5ec4cb modules/mcp_server: task098 - MCP-TRACEABILITY section 7 is aligned with the D-1 closure
094b071f9b modules/mcp_server: task097 - REBUILT-2C-MANIFEST gains the 2c-10 section: the name-conflict policy the section registers (the default refusal with its complete conflict list, its error code and its opt-in rename), the contract's six shape quantities after the append-only override (177/6/1.22.0/154/73/idempotent, sha 64ddce9f), the ten gates and accept_m1 22/22 with their real exit codes, and the three iron-rule deviations of this task recorded rather than hidden
2385fe2fb5 modules/mcp_server: task097 (D-3) - a requested node name the target parent already carries is now refused instead of silently renamed, so a replayed editor phase can no longer write a whole duplicate node layer into a scene; editor_save_scene reports the duplicates a batch made under an explicit rename instead of saving them silently
95aa1d8984 modules/mcp_server: task096 - MCP-TRACEABILITY gains section 7: what the evidence chain is when the pixel diff is unavailable, and how the ledger is to be read then; the section also carries the re-localisation of D-1 (the duplicate node layer a replayed editor phase writes into a scene), which is why the three older games' pixel column says unavailable rather than 0
8b9dd9a72b modules/mcp_server: task094 - D-2 is a load-sensitive readiness predicate, not a defect: the accept_m1 wait now asks the main loop to advance (frame_count strictly increasing six samples in a row) instead of asking it to be faster than 20 fps, so the suite is 22/22 solo and 22/22 under eight CPU burners
cf554ef58c modules/mcp_server: task092 (B2/B3/B4) step2 - a deferred call's file effects and its capture are collected at completion, the two missing doctests exist, and the frame cost is a clamped median of a window
```

`git status --short`：**空**；`git rev-parse HEAD` = `git rev-parse refs/remotes/origin/feature/mcp-server-module-rebuild` = **`0fbd5ec4cbdfe58e22fa21119575f24495460bd1`**。

### G3 收尾后的进程与端口

无残留 `Godot*` 进程；`9877`、`9930–9933`、`9950–9999` 无 **LISTENING**。**未改变机器显示或串流状态**。
