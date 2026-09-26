# TASK-102 — 第 14、15 个游戏（Platformer / Match-3）交付；七条缺陷（载荷 2 / 会话 5）在各自首轮被「断言 + 多帧采样 + Python 第二实现」照出来、修好并重跑（Platformer r1→r2、Match-3 r1→r2→r3）；一条工具错误信息缺口（X-1）只记录未修；模块字节未动，门跑器判 `SKIP_REBUILD`（如实说明：十道门一门未跑）

* 执行者：工具工程师（本会话，**有写权限，不再委派**）
* 主仓：`F:\moonbit-hof-rs`（分支 `master`，无远端，本轮提交 `3b9d55c`，**202 个文件 / 21862 行增**）
* 引擎仓：`F:\moonbit-hof-rs\godot-mcp\godot`（分支 `feature/mcp-server-module-rebuild`，`HEAD = origin = e041cae270`，**本轮一个字节未动**）
* 脚本 / 会话 / 证据：`godot-mcp\recovery\work\task102\`
* 时间：2026-09-27（本会话）

---

## 0. 结论表（每行一句话）

| 段 | 要求 | 结论 | 关键证据 |
|---|---|---|---|
| **A①** | **Platformer**（C#，只用 MCP 调用开发）：左右移动与跳（重力/落地/二段跳可选）、平台碰撞、收集物计分、掉坑或到达终点判定 | **做完，首轮照出 2 条载荷缺陷（PL-1 / PL-2）与 1 条会话缺陷（PL-3），逐条修好并重跑 r2 后全绿。** 228 次调用（编辑器 14 / 游戏 214），`facts_complete` **228/228（100%）**，判定分布 `failed=2`（**两条都是声明的**：`e06` 同名批量 `-32000`、`g208` 不存在属性 `-32001`）+ `ok_effect_observed=33` + `ok_file_effect_observed=153` + `ok_no_effect_observed=40`；断言 **139 PASS + 1 条声明的边界失败** ＋ **2 条屏幕文本 PASS** ＋ **2 条场景断言 PASS** = **143 PASS**；像素差 **40/228 非零**（编辑器 1/14、游戏 39/214），`user://` 七帧逐对 **631 / 22530 / 24437 / 2445 / 24178 / 4349 px**，七个 sha **7/7 互不相同**；独立复算 **0 处不符**；`project_build_csharp` exit 0（4761 ms）、`invalid_count=0`；树里 114/115 个节点名 **0 个 `@` 开头** | `runs\platformer\plat-task102-r2`（首轮 `-r1`）、`logs\summary-plat-r2.txt`、`logs\assert-plat-r2.txt`、`logs\samples-plat-r2.txt`、`logs\pixel-r2.txt`、`logs\frames-plat-r2.txt`、`logs\recompute-plat-r2.txt`、`logs\editor-plat-r2.txt` |
| **A②** | **Match-3**（C#，只用 MCP 调用开发）：网格交换、三连检测与消除、下落补充、连锁得分、非法交换拒绝 | **做完，首轮照出 3 条会话缺陷（M3-1 / M3-2 / M3-3），r2 又照出 1 条会话/测试设计缺陷（M3-4），逐条修好并重跑到 r3 后全绿。** 145 次调用（编辑器 14 / 游戏 131），`facts_complete` **145/145（100%）**，判定分布 `failed=2`（同样两条声明的）+ `ok_effect_observed=18` + `ok_file_effect_observed=95` + `ok_no_effect_observed=30`；断言 **85 PASS + 1 条声明的边界失败** ＋ **2 条屏幕文本 PASS** ＋ **1 条场景断言 PASS** = **88 PASS**；像素差 **22/145 非零**（编辑器 1/14、游戏 21/131），七帧逐对 **140015 / 17813 / 24265 / 6892 / 132911 / 135425 px**，**7/7 互不相同**；独立复算 **0 处不符**；`project_build_csharp` exit 0（3725 ms）、`invalid_count=0`；树里 68/69 个节点名 **0 个 `@` 开头** | `runs\match3\m3-task102-r3`（首轮 `-r1`，中间 `-r2`）、`logs\summary-m3-r3.txt`、`logs\assert-m3-r3.txt`、`logs\samples-m3-r3.txt`、`logs\pixel-m3-r3.txt`、`logs\frames-m3-r3.txt`、`logs\recompute-m3-r3.txt`、`logs\editor-m3-r3.txt` |
| **A③** | 跑完给：调用数、判定分布、`facts_complete`、缺陷清单（分「工具缺陷」「游戏或驱动缺陷」）；两行加进 `GAME-LOOP-LOG.md` | **做完。** 台账续到第 14、15 行；**工具缺陷 1 条（X-1，只记录、未修）**；**游戏或驱动缺陷 7 条**（**PL-1** 世界边界、**PL-2** 起跳不清 `OnGround`、**PL-3** 会话期望值引用错状态、**M3-1** 默认棋盘靠猜、**M3-2** 拒绝计数建在新副本上、**M3-3** GDScript 写了 C# 方法名、**M3-4** 采样钉板只剩一个合法交换）；`GAME-LOOP-LOG.md` 新增「TASK-102 记录」节与缺陷行 | `GAME-LOOP-LOG.md` 台账第 14/15 行、缺陷表 PL-1/PL-2/PL-3/M3-1..M3-4 与工具表 X-1、TASK-102 记录节；`recovery\work\task102\decisions-d150.md`；`DECISIONS.md` 的 D150 |
| **B** | 若改了模块 → 重建两变体 + 十道门全绿（真实退出码）+ `accept_m1` 22/22 + push 到 fork；未改模块则用 `run_gates.ps1` 的纯文档/免跑判定并**如实说明**；主仓提交；报告含两仓 `git log --oneline -8` 与 `git status --short`；时间不够如实报告 | **未改模块，如实免跑。** `modules\mcp_server` 本轮**零字节改动**（引擎仓 `git status --short` 空、`git diff --name-only 2385fe2fb..HEAD` 仍只有两份 `.md`），预检判 `VERDICT=ANCHOR_STRUCTURAL_EQUIVALENT` + `RESULT=SKIP_REBUILD` + `GATES_SKIPPED=1`，**exit 0**——**十道门本轮一门未跑，未重建、未 push 代码、未跑 `accept_m1`**。主仓提交 `3b9d55c`（202 个文件，21862 行增） | `runs\gates\task102-doconly\summary.txt`、`logs\gates-task102-doconly.txt`；§B、§F |

---

## A. 第 14、15 个游戏（C#，只用 MCP 调用开发）

### A1 形态与开发方式（两款同一套脚手架，固化的模板照用）

两款都从模板实例化（`tools\new_game.ps1 -Name platformer -Class PlatformerGame` / `-Name match3 -Class Match3Game`），**游戏内容全部由 MCP 调用写成**：`project_edit_script`（C# 载荷替换模板桩）、`editor_add_nodes_batch`（3 个静态节点一次建好）、`editor_add_input_action`、`editor_save_scene`、`project_build_csharp`、`project_validate_scripts`；游戏相全部是 `running_game_*`。

| 游戏 | 场景里的静态节点 | 运行期新建的东西 |
|---|---|---|
| Platformer | `Background` / `Hud` / `Status` | 每个实心格 1 个 `Tile_r_c`（约 100 个）+ 每个收集物 1 个 `Gem_r_c`（14 个）+ `Goal` + 移动的 `PlayerSprite` |
| Match-3 | `Background` / `Hud` / `Status` | 每格 1 个 `Gem_r_c`（64 个） |

**确定性规则（继承前十三款）**：①静态节点一次批量建好；②动态对象运行期新建；③`ForceTestState` 一个调用钉死整盘状态；④**多帧采样先于会改变状态的那一步**；⑤每个「钩子做了多少」都是**与帧率无关的增量属性**（`LastHookSteps`），每帧时钟另一个属性（`LastAutoSteps`）——**一个属性只能有一个写者**（Platformer 的 `Ticks` 只由 `_Process` 写、`Frames` 只由固定帧写）；⑥建场景那一步**故意再跑一次同名批量**，让 D-3 的拒绝出现在每一轮证据里；⑦任何时钟都用**浮点累加器**（`_autoAccum += delta * rate`，不用 `(int)(delta * rate)`），`Elapsed` 是每帧 `+= delta` 的浮点秒表。

**两款各自的新形态**：

* **Platformer 是整数运动学**。地图是 40×30 的 20 px 格子（`'#'` 实心 / `'.'` 空 / `'C'` 收集物 / `'G'` 终点 / `'@'` 出生），一个固定帧是 `x += vx` → 解横 → `vy += 1`（钳到 16）→ `y += vy` → 解纵；**位置、速度、跳跃数、落地数全是 `int`**，所以一条跳跃弧是确切的整数序列，Python 可以逐帧复算（这正是本任务 A 段要求的「Platformer 的抛物落点独立复算」）。
* **Match-3 是种子线性同余**。补充宝石来自 `seed = (seed * 1103515245 + 12345) mod 2^31`、颜色 `= (seed >> 16) % 6`，按列自下而上填补、每列从最低空位向上取新宝石；连锁是「消除 → 下落 → 补充 → 再判」的循环，第 n 链计 `10 × 消除数 × n` 分。所以「一次交换之后的整块盘面」是一个可复算的确定值。

**「全新」的含义**：每次重跑之前，先把上一轮工程按「**先写 sha256 清单再移动**」归档，再用模板重新实例化，使新一轮与上一轮从同一个起点出发：

| 归档 | 文件数 | 字节数 |
|---|---|---|
| `archive\platformer-plat-r1`（清单 `platformer-plat-r1.manifest.json`） | 129 | 8 458 315 |
| `archive\match3-m3-r1`（清单 `match3-m3-r1.manifest.json`） | 131 | 8 396 788 |
| `archive\match3-m3-r2`（清单 `match3-m3-r2.manifest.json`） | 129 | 8 396 754 |

**全程零删除**：只移动，不删除。

### A2 终轮真实输出

| | Platformer r1 | Platformer **r2** | Match-3 r1 | Match-3 r2 | Match-3 **r3** |
|---|---|---|---|---|---|
| 调用数（编辑器 / 游戏） | 228（14 / 214） | **228（14 / 214）** | 136（14 / 122） | 139（14 / 125） | **145（14 / 131）** |
| `facts_complete` | 228/228 | **228/228（100%）** | 136/136 | 139/139 | **145/145（100%）** |
| 断言（node-state） | 136 PASS + 3 FAIL + 1 声明 ERROR | **139 PASS + 1 声明 ERROR** | 73 PASS + 3 FAIL + 1 声明 ERROR | 79 PASS + 1 声明 ERROR | **85 PASS + 1 声明 ERROR** |
| 断言（另两个工具） | — | **4 PASS** | — | — | **3 PASS** |
| 像素差非零 | 39/228（1/14、38/214） | **40/228（1/14、39/214）** | 16/136（1/14、15/122） | 17/139 | **22/145（1/14、21/131）** |
| 判定分布 | `failed=2` + 32 + 156 + 38 | **`failed=2` + 33 + 153 + 40** | `failed=2` + 15 + 92 + 27 | `failed=2` + 16 + 89 + 32 | **`failed=2` + 18 + 95 + 30** |
| 缺陷（工具 / 游戏或驱动） | 0 / 3 | **0 / 0（r1 三条已修）** | 0 / 3 | 0 / 1（M3-4 仍在） | **1（X-1，只记录） / 0（四条都已修）** |

> 每一轮都是 `failed=2`，且**两条都是声明的**：编辑器相那一次同名拒绝（`-32000`）+ 一条故意打在不存在属性上的边界断言（`-32001`）。`report.json` 的自动缺陷清单只有这两条。

### A3 证据形态（任务书要求的四类都用上了）

**① 多帧属性采样（先采样、后改变）**

| 采样 | 帧数 | 结果 |
|---|---|---|
| Platformer `g36-samples-frozen` | 12 | 冻结基线：`MapHash` / `GemsRemaining` / `PlayerX` / `PlayerY` / `OnGround` **各只有 1 个值**，`Elapsed` / `Ticks` **各 12 个不同值** |
| Platformer `g188-samples-clock` | 30 | `PlayerX` **29 个不同值（140→252）**、`Landings` 29 个、`AutoTicks` 29 个、`Elapsed` / `Ticks` 各 30 个；`PlayerY`/`VelY`/`OnGround` 恒定（平坦地面直线疾跑） |
| Match-3 `g13-samples-frozen` | 12 | 冻结基线：`BoardHash` / `Moves` / `Score` / `TotalCleared` **各只有 1 个值**，`Elapsed` / `Ticks` **各 12 个不同值** |
| Match-3 `g101-samples-clock`（r2，**缺陷现场**） | 30 | `AutoTicks` 4→33，而 `Moves` 恒定 1、`Score` 恒定 30、`BoardHash` 恒定、`Refills` 恒定 3 —— 时钟在走、**盘面一格没动**（M3-4） |
| Match-3 `g101-samples-clock`（**r3，修好之后**） | 30 | **`BoardHash` 26 个不同值**、`Moves` 3→32、`Score` 150→1270、`TotalCleared` 12→112、`Refills` 12→112、`AutoTicks` 3→32、`MaxChain=2`、`Elapsed`/`Ticks` 各 30 个 |

**② 断言** —— **Platformer**：整张地图的 `MapHash`/`StateHash` 与 Python 复算一致；出生落地 4 帧（`y=544`、`OnGround=true`、`Landings=3`）；撞左墙 30 帧（`PlayerX=0`、`WallHits=1`、`VelX=0`、`Facing=-1`）；**跳跃抛物线的 8 个检查点逐帧钉住**（第 1 帧 `y=533`、第 6 帧 `y=493`、第 11/12 帧顶点 `y=478`、第 13 帧 `y=479`、第 18 帧 `y=499`、**第 23 帧 `y=544` 但 `OnGround=false`**、**第 24 帧落地 `y=544`/`OnGround=true`/`VelY=0`**）；二段跳三分支（地面跳 `vy=-12` → 空中跳 `vy=-10`/`AirJumps=1`/`Jumps=2` → 第三次被拒 `JumpsRejected=1` 且速度不变）与「关掉二段跳」分支；收集物三拍（1 颗 10 分 → 2 颗 20 分 → 再走不重复计数、`MapHash` 变成复算值）；终点胜利 + 胜利后再动被拒（`reason=game_over`）+ **`StepFrames(3)` 之后 `LastHookSteps=0`**；掉坑两拍（10 帧 `y=599` 未掉 → 第 11 帧 `Falls=1`/`Lives=2`/回出生点）+ 最后一条命 → `Lives=0`/`GameOver=true`。屏幕文本 `GOAL REACHED` / `ALL LIVES LOST`。**Match-3**：默认棋盘整盘/哈希/Seed 与 Python 复算一致；安静盘**没有任何合法交换**（`AutoStep(3)` → `LastHookSteps=0`）；三种非法交换（`no_match`/`not_adjacent`/`out_of_bounds`）被拒且盘面逐字节不变、`RejectedMoves` 累计 1/2/3；指定交换后的整盘/哈希/Seed/Refills/连锁/消除数/得分与复算一致（`chain=1`、3 颗、30 分）；`AutoStep(1)` 选中**行优先第一个合法交换** `0,4>0,5`；两波连锁（`LastChain=2`、6 颗、**90 分**）与最终整盘；胜利（490 → 520 越过 500）与再交换被拒（`reason=game_over`）；失败（`movelimit=1`）；**采样窗口首尾的 `BoardHash` 不相等**（`neq`）。屏幕文本 `TARGET REACHED` / `OUT OF MOVES`。

**③ 文件 sha** —— 两款各自 `e05` / `e09` 的 `project_read_text_file` sha **逐字节相同**（Platformer `0dd8bf57022b7967…` / 834 B；Match-3 `7772574ad82a8a09…` / 842 B），即被拒的同名批量**什么都没写**；`e06` 的 `-32000` 各列 3 条 `conflicts`（Background / Hud / Status）；编辑器相各 `sidecar_verified=1`（C# 载荷超限走旁路证据）。

**④ 像素差 + 独立复算** —— 见 A4。

### A4 独立复算（不是转述）

三层，互相独立：

1. **会话里的字面量来自 Python 第二实现**。`recovery\work\task102\make_session_platformer.py` 的 `PSim` 与 `make_session_match3.py` 的 `MSim` 各自从**规则**重写一遍载荷的逻辑（40×30 地图解析、一格 20 px 的整数运动学与轴分离解算、收集物/终点/掉坑；8×8 棋盘的行列 run 扫描、消除、逐列重力与补充顺序、LCG、连锁计分、交换合法性）。会话里每一处关键断言的期望值都取自它们。
2. **事后复算不看 `report.json`、不看断言助手、不看 C#**。`recompute_readbacks.py` 把载荷**打印出来的** `Dump()` 一行行拆开，用**自己的**代码重算哈希：Platformer 的 `MapHash` 由**打印出来的 ASCII 地图**重推（实心 1 / 终点 5 / 收集物 3 / 空 2），`StateHash` 由同一行上的 `player=` / `vel=` / `on_ground=` 重推；Match-3 的 `BoardHash` 由**打印出来的数字棋盘**重推（`h = h*31 + (value+1)`，行优先），都是 32 位 multiply-31 链。再把第二实现算出的字面量与载荷在**本轮响应文件里实际回报的 `actual`** 逐条对齐（Platformer 24 条、Match-3 25 条）。
3. **像素与帧**：`pixel_recompute.py`（逐调用 capture 对，自己解码 PNG、两条规则各算一遍）与 `frames_recompute.py`（`user://` 保存帧，自己按 mtime 排序、自己 sha256、自己对 `report.json`）。

| 运行 | `Dump()` 打印的盘面/棋盘 | 字面量逐条对齐 | 逐调用对 非零（引擎规则 >10） | 与 `report.json` 不符的对 | `user://` 帧链（复算） |
|---|---|---|---|---|---|
| Platformer **r2** | **2/2 OK**（从打印的 ASCII 重推 `MapHash` 与 `StateHash`） | **24/24 OK** | **40/228**（编辑器 1/14、游戏 39/214） | **0** | **631 / 22530 / 24437 / 2445 / 24178 / 4349**（7 帧 7 个不同 sha） |
| Match-3 **r3** | **3/3 OK** | **25/25 OK** | **22/145**（编辑器 1/14、游戏 21/131） | **0** | **140015 / 17813 / 24265 / 6892 / 132911 / 135425**（7 帧 7 个不同 sha） |

两款的保存帧 sha256 与 `report.json` 记录的**逐一相同**，帧链逐对独立复算 **0 处分歧**，`TOTAL RECOMPUTATION MISMATCHES: 0`（两款）。

**一条如实记录的采样相位现象（不是缺陷）**：Platformer 的 30 帧时钟采样里 `LastAutoSteps` 只有 `{1, 0}` 两个值、第 1 帧之后恒为 0，而 `AutoTicks` 同期涨了 28。原因是这台机器上引擎帧率远高于 60（采样点之间的实际间隔约 2.4 帧），浮点累加器每 2.4 帧才凑满 1 tick，采样点恰好总落在「还没凑满」的那一帧上。`LastAutoSteps` 写的是它自己那一帧的事实，累计量 `AutoTicks` 才是「时钟真的走了多少」；读采样时必须把两者分开读。

### A5 七条缺陷与一条工具缺口（各自首轮照出来、修好并重跑）

| id | 层 | 现象（证据） | 根因 | 处置 → 重跑结果 |
|---|---|---|---|---|
| **PL-1** | Platformer（**载荷**） | 首轮 `g48-assert-x` 期望 `PlayerX=0` **实得 20**；而同刻 `g49`（`WallHits=1`）、`g50`（`VelX=0`）、`g51`（`Facing=-1`）、`g52`（`OnGround=true`）全 PASS——「撞墙停下」发生了，只是停的像素不对 | `ResolveHorizontal()` 用「盒子前缘所在格子 + 1」的格子相对公式解算碰撞，而 C# 的整数除法**向零截断**：盒子被推到 `x=-2` 时 `-2/20 = 0`，公式给出 `(0+1)*20 = 20`，把玩家从墙上弹回两格。**Python 第二实现用向下取整**（`-2//20 = -1` → `0`），两边对「世界左边缘」的答案不同 | **改**：左/右/顶三条世界边界改成**显式像素钳位**（`x<0→0`、`x+PW>Cols*Tile→Cols*Tile-PW`、`y<0→0`），格子相对公式只用于地图内部的实心格。r2：`g48` 实得 **0**，`g49`～`g52` 同刻成立 |
| **PL-2** | Platformer（**载荷**） | 首轮 `g61-assert-not-ground` 期望 `OnGround=False` **实得 True**：`Jump()` 刚被调用、速度已经是 `-12`，而「是否站在地上」还是起跳前的值 | `Jump()` 只设 `VelY`，没有清 `OnGround`；起跳语义上就是离地，`PSim.jump()` 会清、载荷不清 | **改**：地面跳与空中跳两条分支都置 `OnGround=false`。r2：`g61` 实得 **False**，且抛物线的 8 个检查点（含第 23 帧 `y=544` 但**仍在空中**）全与第二实现一致 |
| **PL-3** | Platformer（**会话**） | 首轮 `g144-assert-gem-hash` 期望 `MapHash=-1950852335` **实得 -1674907474** | 生成器给四个 LEVEL1 场景都写了 `goal=0,0`（地图里多了一个终点格），而 `PSim` 是按 `goal=None`（无终点）构造的——**期望值与它引用的那个状态不是同一个状态** | **改**：四个 LEVEL1 场景不再传 `goal=`。r2：`g144` 实得 **-1950852335** |
| **M3-1** | Match-3（**会话**） | 首轮 `g11-assert-probe-value` 期望 `ProbeValue=5` **实得 1** | 会话对 `_Ready()` 里由 LCG 生成的默认棋盘**只能猜**：「(3,5) 应该是 5」是写死的字面量，没有任何复算支撑。**载荷是对的** | **改**：在生成器里用同一条 LCG 与同一个消稳循环复算 `BuildBoard()`，把默认棋盘、`BoardHash` 与生成后的 `Seed` 都做成断言，`ProbeValue` 取自复算结果。r2/r3：`g07a`/`g07b`/`g07c`/`g11` 全 PASS，`Seed=749508457` 与载荷 `MATCH3_READY` 打印的**完全一致** |
| **M3-2** | Match-3（**会话**） | 首轮 `g35-assert-rejected-2` 期望 1 **实得 2**、`g38-assert-rejected-3` 期望 1 **实得 3** | 生成器给每种非法交换都新建了一个仿真对象，每个只记 1 次拒绝；而会话是在**同一块盘面**上连做三次非法交换，`RejectedMoves` 是累计的 | **改**：三种拒绝改成建在**同一个**累计对象上（1/2/3）。r2/r3：`g29`/`g35`/`g38` 三条同时 PASS |
| **M3-3** | Match-3（**会话**） | 首轮 `g115-runtime-overlay` 回 `{"result": null, "result_type": "Nil"}`，`g117-shot-t6` 与前一帧**逐字节相同**（`px_vs_prev=0`），最终场景树里**没有 `ProbeOverlay`**（68 个节点，与开头 `g01` 一样多） | 正控代码写成了 GDScript 里的 `main.addChild(c)`——**C# 的方法名**。GDScript 不认 `addChild`，脚本在那一行报错，`return "overlay added"` 从未执行。引擎 stderr 有 `SCRIPT ERROR: Invalid call. Nonexistent function 'addChild' in base 'Node2D (Match3Game.cs)'.` | **改**：改成 `main.add_child(c)`。r3：`g115` 回 `"overlay added"`、树上 **69** 个节点（含 `ProbeOverlay`）、`m3-t6` 与 `m3-t5` 相差 **135425 px** |
| **M3-4** | Match-3（**会话 / 测试设计**） | r2 的 `g101-samples-clock` 30 帧采样里 **`AutoTicks` 4→33**，而 `Moves` 恒定 1、`Score` 恒定 30、`BoardHash` 恒定、`Refills` 恒定 3——时钟在走，**盘面一格没动**；而同一轮 `g102`（`Moves gt 0`）、`g103`（`TotalCleared gt 0`）、`g104`（`AutoTicks gt 2`）**全部 PASS**。是**多帧采样**把它照出来的——与 F-1 / B-3 一模一样的照法 | 钉板选的是 Q 盘，而 Q 上**只有一个合法交换**。`SetAutoClock(60.0)` 与第一个采样帧之间隔着两三次 MCP 调用，这段时间足够时钟把它吃掉；此后 `AutoStep` 每次都找不到合法交换、返回 0，盘面永远冻住。`AutoTicks` 是**时钟应用了多少步**，与「步有没有真的发生」无关，所以它照样在涨——B-3 的教训换了个形态：**采样钉板必须是游戏能一直玩下去的状态** | **改**：①改成钉默认棋盘，生成器先**在 Python 里实测**它能连做 40 次自动交换（40/40 applied、盘面确实在变）才允许写进会话；②`g102` 阈值从 `gt 0` 提到 `gt 1`；③**新增断言 `g104a`（`BoardHash neq` 窗口开始时的哈希）**——盘面冻住从此是一条会 **FAIL** 的断言，而不只是采样里的一串常数。r3：`BoardHash` **26 个不同值**、`Moves` 3→32、`Score` 150→1270、`TotalCleared` 12→112、`Refills` 12→112，六条断言全 PASS |
| **X-1**（**工具**，只记录未修） | `running_game_execute_gdscript` 的错误信息 | `runs\match3\m3-task102-r1\g115-runtime-overlay.json` 回的是 `ok`（ledger 记 `ok_no_effect_observed`）+ `{"result": null, "result_type": "Nil"}`，**没有任何错误码或错误消息**；同一刻引擎 stderr 里躺着完整的 `SCRIPT ERROR` 行。同一会话里同一段代码（拼写正确的 `add_child`）在 platformer 上回 `"overlay added"` | 未定域（未改模块）：错误由 GDScript 运行期抛出、只有引擎进程的 stderr 承接；工具把脚本返回值原样回传，脚本没返回值就是 `null`。**根因未查**，按台账口径「根因不清楚的只记录、不猜改」；改它要动 `modules\mcp_server` → 必须重建两变体 + 重跑十道门，本轮不做 | **只记录，未修。** 可复现配方：把 `tools\sessions\match3\session.json` 的 `add_child` 改回 `addChild` 再跑一次。**对证据链的实际影响**：M3-3 就是被这条**半掩**住的——工具答复是 `ok`，把 `addChild` 改成静默无效果；真正把它抓出来的是**像素差 0** 与**场景树里没有那个节点**。结论：`execute_gdscript` 的 `ok` 不能单独当「脚本执行成功」读，必须配效果证据 |

**这八条的方法论价值**：PL-1 是「世界边界不能复用地图内部的格子相对公式（C# 除法向零截断）」、PL-2 是「起跳就是离地，状态要跟着改」、PL-3 是「期望值必须与它引用的那个状态同源」、M3-1 是「第二实现要覆盖**生成出来的**默认状态」、M3-2 是「累计量要在同一个对象上累计」、M3-3 是「脚本语言别写成宿主语言的方法名」、M3-4 是「采样钉板必须先证明它能一直动，并把『没动』做成会失败的断言」、X-1 是「`ok` 不等于脚本执行成功」。八条都**不是模板用错工具**，`modules\mcp_server` 本轮零字节改动。

### A6 缺陷清单

**工具缺陷（`modules\mcp_server`）：1 条（X-1，只记录、未修、未改模块）。** 五轮共 876 条调用里没有第二类「工具做错了事」；其余非 `ok` 判定是每条运行里两条**声明的**边界调用（同名拒绝 `-32000`、不存在的属性 `-32001`）。

**游戏或驱动缺陷：7 条（PL-1、PL-2、PL-3、M3-1、M3-2、M3-3、M3-4，均已修并在 r2 / r3 复核）。**

**与固化模板的一处如实偏差**：本轮的编辑器相是 **14 次调用**，没有 `editor_get_errors`（TASK-099..101 的编辑器相都带了它）。因此本轮的编译健康证据只有 `project_build_csharp` exit 0（Platformer 4761 ms / Match-3 3725 ms）与 `project_validate_scripts invalid_count=0` 两条，没有 `editor_get_errors count=0` 那一条。这一点如实记在这里，不补跑、不转述。

---

## B. 收尾

### B1「模块字节未动 → 免跑十门」这个判定

`modules\mcp_server` 本轮**代码一个字节没动**：引擎仓 `git status --short` 为空，`git diff --name-only --no-renames 2385fe2fb..HEAD` 仍只有 `MCP-TRACEABILITY.md` 与 `REBUILT-2C-MANIFEST.md` 两份 `.md`。两个变体仍是 TASK-097 在模块提交 `2385fe2fb5` 之后重建的那两份（自报 `4.8.dev.mono.custom_build.2385fe2fb`）。

`tools\run_gates.ps1 -Tag task102-doconly` 的真实输出（`runs\gates\task102-doconly\summary.txt`、逐字见 `logs\gates-task102-doconly.txt`）：

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
GATES_PREFLIGHT EXPLAIN=the diff between the built binary anchor and HEAD contains no compile input, so no compiled behaviour can have changed; the ten gates would report on the same binary that already passed
```

**如实说明**：本轮**没有重建两个变体、没有跑十道门、没有跑 `accept_m1`、没有 push 代码**，判定的依据是「引擎仓没有任何编译输入」。任何「门应该是绿的」的说法本轮**都不成立**，因为没有跑。（X-1 只是一条记录，没有动模块。）

### B2 提交与两个仓库

**主仓**（分支 `master`，无远端）：`3b9d55c`，**202 个文件，21862 行增 / 0 行删**。提交信息对应 `DECISIONS.md` 的 D150。

**引擎仓**（分支 `feature/mcp-server-module-rebuild`）：**本轮没有任何提交，也没有 push**——`git status --short` 空，`git rev-parse HEAD` = `git rev-parse refs/remotes/origin/feature/mcp-server-module-rebuild` = `e041cae270487d5c910f1e7ebe0e13982886d602`。两仓的 `git log --oneline -8` 与 `git status --short` 见 §F。

### B3 `--import` 的关机期访问违例

本轮**五次导入全部 `IMPORT_EXIT=0`、`import.stderr.txt` 0 字节**（Platformer r1/r2、Match-3 r1/r2/r3）。累计口径因此从 **3 次 / 23 次会话导入** 变成 **3 次 / 28 次**。台账待办 2 的判定不变：**不改引擎、不重建**，等可复现配方或用户授权。

### B4 收尾后的进程与端口

最后一轮之后：无 `Godot*` 进程；会话端口 `9940/9941`、`9942/9943` 无 **LISTENING**；门预检没有跑门、没有占用 9888/9889。**未改变机器显示或串流状态**（未停 `GameViewer`、未动设备/注册表/电源/显示拓扑）。

---

## C. 铁律遵守（逐条对照）

| 铁律 | 遵守情况 |
|---|---|
| ① 禁止一切 shell 重定向 | **基本遵守，有一处违例已记录**：所有 python / powershell / cmd 调用一律 `Start-Process -RedirectStandardOutput/-RedirectStandardError <绝对路径>` 拥有 stdout/stderr（`capture.ps1` / `run_one.ps1` / `commit.ps1` / `run_gates_task102.ps1` / `git_status.ps1` / `git_two_repos.ps1` / `commit_stat.ps1`）；所有文本文件由 Python 写入器或 `write`/`edit` 工具写。**违例一处**：本会话第一次跑 `recovery\work\task102\check_session.py`（Platformer 会话的预检）时用了 cmd 的 `> nul 2>&1`；发现后立刻改为 `capture.ps1`（`Start-Process` 拥有输出），该次检查也随即补跑进 `logs\check-session-platformer.txt`。**此后本任务再没有出现过 `>` 或 `>>`。** |
| ② 破坏性命令默认拒绝 | **遵守，且本轮零删除**：唯一的「移动」是三次归档工程——先写 129/131/129 个文件的 sha256 清单、目标不存在才 `Move-Item`，**自始至终没有删除任何文件**；没有杀任何非本任务进程。 |
| ③ 构建与运行从 cmd 启动 | **遵守**：五次会话运行、两次 `new_game`（经 `reset_game_project.ps1` 生成的 `.cmd`）、门预检、两仓 git 查询全部是 `Start-Process cmd.exe /c …`；`dotnet build` 由会话内的 `project_build_csharp` 触发。 |
| ④ 唯一端口 + 跑前查进程与端口 | **遵守**：`9940/9941`（Platformer r1、r2）、`9942/9943`（Match-3 r1、r2、r3）；每轮开跑前 `netstat` + `tasklist` 确认无残留，收尾后再查一次（无 `Godot*`、无 LISTENING）。 |
| ⑤ 会话文件先双解析后才执行 | **遵守，且对最终版会话补做了一次**：两个会话在**开引擎之前**都过 `check_session.py`（Python JSON + 形状 + `content_file` 可达）与 `check_session_ps.ps1`（PS 5.1 `ConvertFrom-Json`）。中途重新生成过会话（Platformer 一次、Match-3 两次），因此**收尾时对盘上最终的会话文件又做了一遍双解析**：`logs\check-session-platformer-final.txt`、`logs\check-session-match3-final.txt`、`logs\check-session-ps-platformer-final.txt`、`logs\check-session-ps-match3-final.txt` —— Python 侧 exit 0，PS 侧 `PS_PARSE OK`（228 = 14 + 214；145 = 14 + 131）。 |
| ⑥ 迁移与删除先存证 sha | **遵守**：三次 `Move-Item` 之前各写出一份该工程全部文件的 sha256 清单（`archive\*.manifest.json`，已入库）；本轮没有删除操作。 |
| ⑦ 不改变机器显示或串流状态 | **遵守**：未停 `GameViewer`、未改设备/注册表/电源、未接触显示拓扑。 |

---

## D. 本任务产出的文件

```
recovery\work\task102\
  make_session_platformer.py                            Platformer 会话生成器 + Python 第二实现（PSim），并把两张地图写进载荷
  make_session_match3.py                                Match-3 会话生成器 + Python 第二实现（MSim），并实测采样钉板能一直动
  recompute_readbacks.py                                事后复算：从打印的 ASCII 地图/棋盘重算哈希 + 字面量逐条对齐
  probe_clock_board.py                                  采样钉板的耐力搜索（M3-4 的修法）
  decisions-d150.md + append_decisions.py               写入 DECISIONS.md 的正文（Python 写入器，非 shell 重定向）
  write_log.py + fix_defect_id.py                       写入 GAME-LOOP-LOG.md（含把工具缺陷 id 从 T-1 改成 X-1）
  capture.ps1 / run_one.ps1 / commit.ps1                三件套：拥有输出、唯一端口、从 cmd 提交
  run_gates_task102.ps1 / git_status.ps1 / git_two_repos.ps1 / commit_stat.ps1   只读与收尾的取数脚本
  check_session.py / check_session_ps.ps1               铁律 5 的双解析（Python + PS 5.1）
  reset_game_project.ps1                                先写 sha 清单再移动 + 重新实例化
  assertions.py / extra_assertions.py / samples.py / run_summary.py / build_facts.py
  pixel_recompute.py / frames_recompute.py / editor_facts.py / trace_lookup.py / callread.py / peek.py / scaffold.py
  commit-message.txt                                    主仓提交信息原文
  archive\platformer-plat-r1 / match3-m3-r1 / match3-m3-r2（各含 .manifest.json）
  logs\                                                 70+ 份证据日志（五轮会话、断言、采样、复算、门预检、归档、两仓 git）
tools\sessions\platformer\session.json + payload\PlatformerGame.cs
tools\sessions\match3\session.json + payload\Match3Game.cs
projects\platformer\ / projects\match3\                 由模板实例化、随后全部由 MCP 调用写成
runs\platformer\plat-task102-{r1,r2}\、runs\match3\m3-task102-{r1,r2,r3}\   （盘上路径；runs\ 按 .gitignore 不入库）
runs\gates\task102-doconly\                            （同上，不入库）
GAME-LOOP-LOG.md                                       第 14/15 行 + PL-1/PL-2/PL-3/M3-1..M3-4 与 X-1 缺陷行 + TASK-102 记录节 + 待办续写
DECISIONS.md                                           D150
```

> `runs\` 按 `.gitignore` 不入库（盘上真实存在）；本报告所有 `runs\...` 引用都是盘上路径。
> `recovery\work\task102\`（含三份归档工程）、两款游戏工程与会话均已入库。

---

## E. 真实跑出来的数字速查（都可在盘上复算）

| 项 | Platformer | Match-3 |
|---|---|---|
| 运行目录 | `runs\platformer\plat-task102-r2`（首轮 `-r1` 对照） | `runs\match3\m3-task102-r3`（首轮 `-r1`，中间 `-r2`） |
| 调用数（编辑器 / 游戏） | 228（14 / 214） | 145（14 / 131） |
| `facts_complete` | 228/228（100%） | 145/145（100%） |
| `args_evidence` | 编辑器 `sidecar_verified=1` + `inline_complete=13`；游戏 `inline_complete=214` | 编辑器 `sidecar_verified=1` + `inline_complete=13`；游戏 `inline_complete=131` |
| 判定分布 | `failed=2` / `ok_effect_observed=33` / `ok_file_effect_observed=153` / `ok_no_effect_observed=40` | `failed=2` / `18` / `95` / `30` |
| 断言 | 139 PASS + 1 声明 ERROR（node-state）＋ 4 PASS（屏幕文本 + 场景）= **143 PASS** | 85 PASS + 1 声明 ERROR ＋ 3 PASS = **88 PASS** |
| 像素差非零 | 40/228（1/14、39/214） | 22/145（1/14、21/131） |
| `user://` 帧链 | 631 / 22530 / 24437 / 2445 / 24178 / 4349（七帧 7/7 不同 sha） | 140015 / 17813 / 24265 / 6892 / 132911 / 135425（七帧 7/7 不同 sha） |
| 场景 sha（`e05`=`e09`） | `0dd8bf5702…`（834 B） | `7772574ad8…`（842 B） |
| `project_build_csharp` | exit 0（4761 ms） | exit 0（3725 ms） |
| `project_validate_scripts` | `invalid_count=0` | `invalid_count=0` |
| 树里 `@` 自动名 | 0（114 / 115 个节点名） | 0（68 / 69 个节点名） |
| `--import` | exit 0（r1、r2 各一次） | exit 0（r1、r2、r3 各一次） |
| 缺陷（工具 / 游戏或驱动） | 0 / 0（r1 有 PL-1/PL-2/PL-3，均已修） | 1（X-1，只记录）/ 0（r1 有 M3-1..M3-3、r2 有 M3-4，均已修） |
| 独立复算不符数 | 0 | 0 |
| 门跑器（本轮） | — | 纯文档：`SKIP_REBUILD` + `GATES_SKIPPED=1` + exit 0（**十道门一门未跑**） |

---

## F. 提交后的逐字复核（本报告自身的提交之前）

**边界说明**：本节的两段帐是**主仓 `3b9d55c` 提交之后、本报告那次提交之前**的那一刻的两仓状态。此后本报告自身的提交（以及任何纯文档追加）只让主仓 `git log` 顶部多出一个**文档**提交；本节里唯一会变旧的是 `git log` 的顶部行与 `git status --short` 的输出，而**「主仓新增 202 个文件、引擎仓 `git status --short` 为空、引擎仓与远端同级」**这三点不会因此改变。

### F1 主仓 `F:\moonbit-hof-rs`（分支 `master`，无远端）

`git log --oneline -8`：

```
3b9d55c feat(godot-mcp): TASK-102 (D150) - the 14th and 15th C# games are delivered through MCP calls only (Platformer: a 40x30 course of 20-pixel tiles with integer kinematics -- x += vx, resolve the horizontal overlap, vy += 1 clamped to 16, y += vy, resolve the vertical overlap -- so a jump arc is an exact integer sequence, with left/right running, gravity, landing, an optional mid-air second jump, platform collision, collectibles that score, a pit that costs a life and respawns, and a goal tile that wins; Match-3: an 8x8 six-colour board with an orthogonal swap that a line of three or more accepts and a board-identical refusal otherwise, a run scan in both directions, per-column gravity, a linear congruential refill, chain-weighted scoring and a target/move-limit pair that ends the game either way), both with a float-accumulator clock, both with two single-writer increment properties, both replaying the D-3 duplicate-name batch for its -32000 refusal, both with a second Python implementation of their own rules whose outputs are the session's assertion literals, both with a post-hoc recomputation that derives the printed map's and the printed board's hash from the printed ASCII alone, and both with the frame-by-frame parabola (Platformer) and the exact post-cascade board (Match-3) recomputed independently
af12574 docs(godot-mcp): TASK-101 - the two run logs the commit helper itself owns are committed after the fact so the working tree is clean; no content change
5e43af0 docs(godot-mcp): TASK-101 - the report: the two new C# games with their real call counts, verdict distributions, assertion tallies and independently recomputed pixel columns, the four defects their first runs caught (a session that read a fact from the wrong moment, a payload that consumed the enemy it walked into, a session that asserted a probe it never made, and a pinned board whose fuse had already decided the level so the 30-frame sample watched a frozen board while every assertion still passed), each with its fix and re-run, and the gate runner's doc-only preflight that skipped the ten gates because not one module byte changed
26553df feat(godot-mcp): TASK-101 (D149) - the 12th and 13th C# games are delivered through MCP calls only (Sokoban: ...
3f28def docs(godot-mcp): TASK-100 - the report: ...
67bcbb0 feat(godot-mcp): TASK-100 (D148) - the 10th and 11th C# games are delivered through MCP calls only (2048: ...
fbf4bf1 docs(godot-mcp): TASK-099 - the report: ...
7b5fa56 feat(godot-mcp): TASK-099 - the 8th and 9th C# games are delivered through MCP calls only (Frogger: ...
```

`git status --short`（**本报告与随后那次 housekeeping 提交之后**）：

```
（空）
```

**边界与更正**：`3b9d55c` 提交之后、本报告提交之前，`git status --short` 有六条——都是本报告的取证工具自己写的（`commit.ps1` 与 `git_two_repos.ps1` 的日志，在 `git add -A` 之后又被 `Start-Process` 的句柄追加/新建过）。它们随**本报告的提交 `3b2958e`** 一并入库，再由 **`b365654`**（housekeeping，`3 files changed, 26 insertions(+)`）把提交助手自己最后写下的那两行日志收干净，此后工作树为空。因此**「主仓新增 202 个文件、引擎仓 `git status --short` 为空、引擎仓与远端同级」**三点不变，唯一变旧的是 `git log` 的顶部三行。

本报告自身提交之后紧随的两个提交（都在 TASK-102 名下，内容只是本报告的取证工具的日志）：

```
b365654 docs(godot-mcp): TASK-102 - the helper-owned logs of the commit and two-repo capture scripts are committed after the fact so the working tree is clean; no content change
3b2958e docs(godot-mcp): TASK-102 - the report: ...（本报告）
```

本任务的新增与改动全部随 `3b9d55c` 入库（`git show --stat` 给出 **202 files changed, 21862 insertions(+)**）。

### F2 引擎仓 `F:\moonbit-hof-rs\godot-mcp\godot`（分支 `feature/mcp-server-module-rebuild`）

`git log --oneline -8`（**与本轮开始时逐字相同——本轮没有提交**）：

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

`git status --short`：**空**；`git rev-parse HEAD` = `git rev-parse refs/remotes/origin/feature/mcp-server-module-rebuild` = **`e041cae270487d5c910f1e7ebe0e13982886d602`**（与远端同级，本轮未 push 任何东西）。`git diff --name-only --no-renames 2385fe2fb..HEAD` 仍只有 `modules/mcp_server/docs/reports/MCP-TRACEABILITY.md` 与 `modules/mcp_server/docs/reports/REBUILT-2C-MANIFEST.md`。

### F3 收尾后的进程与端口

无残留 `Godot*` 进程；`9940/9941`、`9942/9943` 无 **LISTENING**。**未改变机器显示或串流状态。**
