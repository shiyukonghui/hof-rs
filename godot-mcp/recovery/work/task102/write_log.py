# -*- coding: utf-8 -*-
"""TASK-102: write the two game rows, the seven defect rows, the TASK-102 record
section and the next-step note into GAME-LOOP-LOG.md.

Written by a Python writer rather than a shell redirection (iron rule 1) and with an
explicit UTF-8 encoding (the file is Chinese).  Every anchor is checked to occur
exactly once before anything is written, so a wrong insertion point fails loudly
instead of mangling the ledger.
"""
import io
import os

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.abspath(os.path.join(HERE, "..", "..", ".."))
LOG = os.path.join(ROOT, "GAME-LOOP-LOG.md")

ROW_14 = (
    "| 14 | Platformer | C# | 228（编辑器 14 / 游戏 214） | **228/228（100%）** | "
    "编辑器：`failed=1`（**声明的同名拒绝**）、`ok_effect_observed=1`、"
    "`ok_file_effect_observed=6`、`ok_no_effect_observed=6`；游戏：`failed=1`"
    "（**声明的边界调用**，`-32001`）、`ok_effect_observed=32`、`ok_file_effect_observed=147`、"
    "`ok_no_effect_observed=34` | **0 / 2**（**PL-1 载荷**：世界左/右/顶边用「格子相对」公式解算，"
    "而 C# 除法向零截断，越过 x=0 两像素的盒子被推到 x=20 而不是 x=0（`g48` 期望 0 实得 20）；"
    "**PL-2 载荷**：`Jump()` 没有清 `OnGround`（`g61` 期望 False 实得 True）。两条都由 Python "
    "第二实现照出来、修好并重跑 r2） | `runs\\platformer\\plat-task102-r2`"
    "（首轮 `runs\\platformer\\plat-task102-r1`） | 第 14 个游戏。40×30 的 20 px 格子课程、"
    "**整数运动学**（`x+=vx` → 解横 → `vy+=1`（≤16）→ `y+=vy` → 解纵）、左右移动 / 重力 / 落地 / "
    "**可选二段跳** / 平台碰撞 / 收集物计分 / 掉坑与终点判定。**像素差 40/228 非零**"
    "（编辑器 1/14、游戏 39/214），`user://` 七帧逐对 **631 / 22530 / 24437 / 2445 / 24178 / 4349 px**，"
    "七个 sha **7/7 互不相同**；独立复算（`pixel_recompute.py` + `frames_recompute.py` + "
    "`recompute_readbacks.py`）**0 处不符**。断言 **139 PASS + 1 条声明的边界失败**（`-32001`）＋ "
    "**2 条屏幕文本 PASS** ＋ **2 条场景断言 PASS** = **143 PASS**。**Python 第二实现**"
    "（`recovery\\work\\task102\\make_session_platformer.py` 的 `PSim`）独立算出并作为断言字面量的有："
    "`MapHash`（由**打印出来的 ASCII 地图**重推：实心 1 / 终点 5 / 收集物 3 / 空 2，32 位 multiply-31 链）、"
    "`StateHash`、出生落地的 `PlayerY`/`Landings`、撞左墙后的 `PlayerX=0`、**逐帧抛物线**"
    "（`vy=-12` → 顶点 `y=478` 连续两帧 → 第 23 帧 `y=544` 但**仍在空中** → 第 24 帧落地并清零 `VelY`）、"
    "二段跳三条分支（地面跳 / 空中跳 / 第三次被拒）、收集物三拍（1 颗 10 分、2 颗 20 分、再走不重复计数）、"
    "终点胜利、掉坑两拍（第 10 帧 `y=599` 未掉、第 11 帧掉坑回出生点、最后一条命 → `GameOver`）。"
    "与帧率无关的增量 `LastHookSteps`（`StepFrames(3)`→3）在时钟跑过 30 帧后仍是 3，而 `LastAutoSteps` 归 0；"
    "时钟用浮点累加器 `_autoAccum += delta*60`，`Elapsed` 是 `+= delta` 的浮点秒表；`Ticks` 只由 `_Process` 写、"
    "`Frames` 只由固定帧写（一个属性一个写者）。多帧采样：冻结基线 12 帧（`MapHash`/`GemsRemaining`/`PlayerX`/"
    "`PlayerY`/`OnGround` 各 1 个值，`Elapsed`/`Ticks` 各 12 个不同值）对自动疾跑 30 帧"
    "（`PlayerX` **29 个不同值 140→252**、`Landings` 29 个、`AutoTicks` 29 个、`Elapsed`/`Ticks` 各 30 个）。"
    "`e06` 同名批量被 `-32000` 拒绝（3 条 `conflicts`），`e05`/`e09` 的 sha `0dd8bf57…`（834 B）"
    "**逐字节相同**；`project_build_csharp` exit 0（4761 ms）、`invalid_count=0`；树里 114/115 个节点名 "
    "**0 个 `@` 开头**；声明的 `plat_right` / `plat_jump` 动作按按下沿各只触发一次 |\n"
)

ROW_15 = (
    "| 15 | Match-3 | C# | 145（编辑器 14 / 游戏 131） | **145/145（100%）** | "
    "编辑器：`failed=1`（**声明的同名拒绝**）、`ok_effect_observed=1`、`ok_file_effect_observed=6`、"
    "`ok_no_effect_observed=6`；游戏：`failed=1`（**声明的边界调用**，`-32001`）、"
    "`ok_effect_observed=17`、`ok_file_effect_observed=89`、`ok_no_effect_observed=24` | "
    "**1 / 4**（工具 **T-1**（只记录、未改模块）：`running_game_execute_gdscript` 的脚本**运行期报错**时"
    "工具回 `ok` + `result: null`，诊断只落在引擎 stderr 里；**M3-1 会话**：默认棋盘的 `ProbeValue` 是**猜**的"
    "（`g11` 期望 5 实得 1），改成用 Python 复算 `BuildBoard()` 的 LCG + 消稳循环并断言整盘 / 哈希 / Seed；"
    "**M3-2 会话**：三种非法交换的期望计数各自建在**新副本**上（1/1/1），而会话在同一块盘上累计（1/2/3）；"
    "**M3-3 会话**：正控 overlay 的 GDScript 写成了 C# 的 `addChild`；**M3-4 会话 / 测试设计**：自动时钟采样的钉板"
    "只**一个合法交换**，时钟在第一个采样帧之前就把它吃掉，30 帧采样全程看着**冻住的盘面**"
    "（`AutoTicks` 4→33 而 `Moves`/`Score`/`BoardHash`/`Refills` 一动不动）而断言照样全 PASS —— "
    "四周都修好并重跑 r3） | `runs\\match3\\m3-task102-r3`（首轮 `r1`，中间 `r2`） | 第 15 个游戏。"
    "8×8 六色、网格交换、三连检测与消除、下落补充、**连锁得分**（第 n 链 ×n）、非法交换拒绝"
    "（盘面逐字节不变）。**像素差 22/145 非零**（编辑器 1/14、游戏 21/131），`user://` 七帧逐对 "
    "**140015 / 17813 / 24265 / 6892 / 132911 / 135425 px**，七个 sha **7/7 互不相同**；独立复算 "
    "（`pixel_recompute.py` + `frames_recompute.py` + `recompute_readbacks.py`）**0 处不符**。断言 "
    "**85 PASS + 1 条声明的边界失败**（`-32001`）＋ **2 条屏幕文本 PASS** ＋ **1 条场景断言 PASS** = "
    "**88 PASS**。**Python 第二实现**（`recovery\\work\\task102\\make_session_match3.py` 的 `MSim`）"
    "独立算出并作为断言字面量的有：默认棋盘（同一条 LCG `seed=(seed*1103515245+12345) mod 2^31`、"
    "`(seed>>16)%6`、行优先填充 + 消稳循环）与它的 `BoardHash`/`Seed`、安静棋盘（**没有任何合法交换**）"
    "与 `AutoStep(3)` 的 `LastHookSteps=0`、指定交换后的**整盘 / 哈希 / Seed / Refills / 连锁长度 / 消除数 / "
    "得分**、`AutoStep(1)` 选中的**行优先第一个合法交换**、两波连锁的整盘与 90 分、胜利（490→520 越过 500 线）"
    "与失败（`move_limit=1`）。规则逐条钉住：非法交换被拒且 `Board`/`BoardHash` 一字不变；非相邻与越界各按名字拒绝；"
    "连锁 `LastChain=2`、`LastCleared=6`、`Score=90`；胜利 `Won`/`GameOver`=true；再交换 `reason=game_over`。"
    "与帧率无关的增量 `LastHookSteps`；时钟浮点累加器；**`BoardHash neq H0` 把「盘面冻住」变成一条会 FAIL 的断言**"
    "（M3-4 的教训写进断言本身）。多帧采样：冻结基线 12 帧对自动对局 30 帧（`BoardHash` **26 个不同值**、"
    "`Moves` 3→32、`Score` 150→1270、`TotalCleared` 12→112、`Refills` 12→112、`Elapsed`/`Ticks` 各 30 个）。"
    "`e06` 同名批量被 `-32000` 拒绝（3 条 `conflicts`），`e05`/`e09` 的 sha `7772574a…`（842 B）"
    "**逐字节相同**；`project_build_csharp` exit 0（3725 ms）、`invalid_count=0`；树里 68/69 个节点名 "
    "**0 个 `@` 开头** |\n"
)

DEFECTS = (
    "| **PL-1** | Platformer（**载荷**） | 首轮 `runs\\platformer\\plat-task102-r1` 的 `g48-assert-x` "
    "期望 `PlayerX=0` **实得 20**；而同刻 `g49-assert-wall-hits=1`、`g50-assert-vx-0=0`、"
    "`g51-assert-facing=-1`、`g52-assert-ground=True` 全 PASS —— 「撞墙停下」发生了，"
    "只是停的像素不对 | `ResolveHorizontal()` 用「盒子前缘所在格子 + 1」的格子相对公式解算碰撞，"
    "而 C# 的整数除法**向零截断**：盒子被推到 x=-2 时 `-2/20 = 0`，公式给出 `(0+1)*20 = 20`，"
    "把玩家从墙上弹回两格。Python 第二实现用**向下取整**的除法，`-2//20 = -1`，公式给出 `0` —— "
    "两边对「世界左边缘」的答案不同，断言把 C# 的那一侧照了出来 | **改**：左/右/顶三条世界边界的解算"
    "改成**显式像素钳位**（`x<0→0`、`x+PW>Cols*Tile→Cols*Tile-PW`、`y<0→0`），格子相对公式只用于"
    "地图内部的实心格。r2：`g48` 实得 **0**、`g49`～`g52` 同刻成立 |\n"
    "| **PL-2** | Platformer（**载荷**） | 首轮 `g61-assert-not-ground` 期望 `OnGround=False` "
    "**实得 True**：`Jump()` 刚被调用、速度已经是 `-12`，而「是否站在地上」还是起跳前的值 | "
    "`Jump()` 只设 `VelY`，没有清 `OnGround`；起跳语义上就是离地，第二实现 `PSim.jump()` 会清、"
    "载荷不清 | **改**：地面跳与空中跳两条分支都置 `OnGround=false`。r2：`g61` 实得 **False**，"
    "且抛物线 24 帧的每个检查点（含第 23 帧 `y=544` 但**仍在空中**）都与第二实现一致 |\n"
    "| **PL-3** | Platformer（**会话**） | 首轮 `g144-assert-gem-hash` 期望 `MapHash=-1950852335` "
    "**实得 -1674907474** | 会话生成器给 LEVEL1 的四个场景都写了 `goal=0,0`（地图里多了一个终点格），"
    "而 `PSim` 是按 `goal=None`（无终点）构造的 —— **期望值与它引用的那个状态不是同一个状态** | "
    "**改**：四个 LEVEL1 场景改为不传 `goal=`（LEVEL1 本来就没有终点格），`PSim` 与规范因此一致。"
    "r2：`g144` 实得 **-1950852335** |\n"
    "| **M3-1** | Match-3（**会话**） | 首轮 `runs\\match3\\m3-task102-r1` 的 `g11-assert-probe-value` "
    "期望 `ProbeValue=5` **实得 1** | 会话对 `_Ready()` 里由 LCG 生成的默认棋盘**只能猜**："
    "「(3,5) 应该是 5」是写死的字面量，没有任何复算支撑。**载荷是对的** | **改**：在生成器里"
    "用同一条 LCG 与同一个消稳循环复算 `BuildBoard()`，把默认棋盘、`BoardHash` 与生成后的 `Seed` "
    "都做成断言，`ProbeValue` 取自复算结果。r2/r3：`g07a`/`g07b`/`g07c`/`g11` 全 PASS，"
    "`Seed=749508457` 与载荷 `MATCH3_READY` 打印的完全一致 |\n"
    "| **M3-2** | Match-3（**会话**） | 首轮 `g35-assert-rejected-2` 期望 1 **实得 2**、"
    "`g38-assert-rejected-3` 期望 1 **实得 3** | 会话生成器给每种非法交换都新建了一个仿真对象，"
    "每个都只记 1 次拒绝；而会话是在**同一块盘面**上连做三次非法交换，`RejectedMoves` 是累计的 | "
    "**改**：三种拒绝改成建在**同一个**累计对象上（1/2/3）。r2/r3：`g29`/`g35`/`g38` 三条同时 PASS |\n"
    "| **M3-3** | Match-3（**会话**） | 首轮 `g115-runtime-overlay` 回 `{\"result\": null, "
    "\"result_type\": \"Nil\"}`，`g117-shot-t6` 与 `g116` 的帧**逐字节相同**（`px_vs_prev=0`），"
    "最终场景树里**没有 `ProbeOverlay`**（68 个节点，与开头的 `g01` 一样多） | 正控代码写成了 GDScript 里的 "
    "`main.addChild(c)` —— **C# 的方法名**。GDScript 在 `add_child` 上不认 `addChild`，脚本在那一行报错，"
    "`return \"overlay added\"` 从未执行。引擎 stderr 里有 `SCRIPT ERROR: Invalid call. Nonexistent "
    "function 'addChild' in base 'Node2D (Match3Game.cs)'.` | **改**：改成 `main.add_child(c)`。"
    "r3：`g115` 回 `\"overlay added\"`、树上 69 个节点（含 `ProbeOverlay`）、`m3-t6` 与 `m3-t5` 相差 "
    "**135425 px** |\n"
    "| **M3-4** | Match-3（**会话 / 测试设计**） | r2 的 `runs\\match3\\m3-task102-r2` 的 "
    "`g101-samples-clock` 30 帧采样里 **`AutoTicks` 从 4 一路涨到 33**，而 `Moves` 恒定 1、`Score` 恒定 30、"
    "`BoardHash` 恒定、`Refills` 恒定 3 —— 时钟在走，**盘面一格都没动**；而同一轮的 "
    "`g102`（`Moves gt 0`）、`g103`（`TotalCleared gt 0`）、`g104`（`AutoTicks gt 2`）**全部 PASS**。"
    "是**多帧采样**把它照出来的 —— 与 F-1 / B-3 一模一样的照法 | 钉板选的是 Q 盘，而 Q 上"
    "**只有一个合法交换**。`SetAutoClock(60.0)` 与第一个采样帧之间隔着两三次 MCP 调用，"
    "这段时间足够时钟把它吃掉；此后 `AutoStep` 每次都找不到合法交换，返回 0，盘面永远冻住。"
    "`AutoTicks` 是**时钟应用于多少步**，与「步有没有真的发生」无关，所以它照样在涨 —— "
    "这正是 B-3 的教训换了个形态：**采样钉板必须是游戏能一直玩下去的状态** | **改**：①改成钉默认棋盘"
    "（LCG 生成的那一块），生成器先**在 Python 里实测**它能连做 40 次自动交换（40/40 applied、"
    "盘面确实在变）才允许写进会话；②把 `g102` 的阈值从 `gt 0` 提到 `gt 1`；③**新增断言** "
    "`g104a`（`BoardHash neq <窗口开始时的哈希>`）—— 盘面冻住从此是一条会 FAIL 的断言，"
    "而不只是采样里的一串常数。r3：`BoardHash` **26 个不同值**、`Moves` 3→32、`Score` 150→1270、"
    "`TotalCleared` 12→112、`Refills` 12→112，`g102`/`g103`/`g104`/`g104a`/`g104b`/`g105` 全 PASS |\n"
)

TOOL_DEFECT = (
    "| **T-1** | 运行期 / 错误信息（`running_game_execute_gdscript`） | "
    "`runs\\match3\\m3-task102-r1\\g115-runtime-overlay.json` 回的是 `ok`（ledger 记 "
    "`ok_no_effect_observed`）+ `{\"result\": null, \"result_type\": \"Nil\"}`，"
    "**没有任何错误码或错误消息**；同一刻引擎 stderr 里躺着 "
    "`SCRIPT ERROR: Invalid call. Nonexistent function 'addChild' in base 'Node2D (Match3Game.cs)'.`"
    "（`runs\\match3\\m3-task102-r1\\engine-game.stderr.txt`，270 B）。"
    "同一会话里同一段代码在 platformer 上（`add_child`，拼写正确）回 `\"overlay added\"`，"
    "所以这不是工具坏了，而是**脚本运行期报错不被回进工具自己的答复** | 未定域（未改模块）："
    "错误由 GDScript 运行期抛出、只有引擎进程的 stderr 承接；`running_game_execute_gdscript` "
    "把脚本的返回值原样回传，脚本没返回值就是 `null`。**根因未查**，按台账口径「根因不清楚的"
    "只记录、不猜改」，且改它要动 `modules\\mcp_server` → 必须重建两变体 + 重跑十道门，"
    "本轮不做 | **只记录，未修**。可复现配方：把 `tools\\sessions\\match3\\session.json` 里 "
    "`g115-runtime-overlay` 的 `add_child` 改回 `addChild` 再跑一次，或直接对任一运行中的游戏端点发 "
    "`running_game_execute_gdscript` + `{\"code\": \"var m = get_parent()\\nreturn m.NoSuchMethod()\"}`。"
    "**对证据链的实际影响**：本轮 M3-3 就是被这条**半掩**住的 —— 工具答复是 `ok`，"
    "把 `addChild` 改成静默无效果；真正把它抓出来的是**像素差 0** 与**场景树里没有那个节点**。"
    "也就是说：`execute_gdscript` 的 `ok` 不能单独当「脚本执行成功」读，必须配效果证据 |\n"
)

RECORD = """### TASK-102 记录（2026-09-27）

1. **第 14、15 款（Platformer / Match-3）交付**：台账第 14、15 行来自它们自己那一轮的产物
   （`runs\\platformer\\plat-task102-r2\\report.json`、`runs\\match3\\m3-task102-r3\\report.json`）。
   **工具缺陷 1 条（T-1，只记录、未改模块）**（工具缺陷表新增）；「游戏或驱动缺陷」新增
   **PL-1**（载荷：世界左/右/顶边用格子相对公式解算，C# 向零截断把越界 2 px 的盒子推到 20 而不是 0）、
   **PL-2**（载荷：`Jump()` 不清 `OnGround`）、**PL-3**（会话：LEVEL1 场景的 `goal=0,0` 与
   `PSim` 的无终点状态不一致）、**M3-1**（会话：默认棋盘的探测值靠猜）、**M3-2**（会话：三种非法交换的
   计数建在新副本上而不是累计）、**M3-3**（会话：正控 GDScript 写了 C# 的 `addChild`）、
   **M3-4**（会话/测试设计：自动时钟采样的钉板只剩一个合法交换，时钟在第一个采样帧前就吃掉它，
   30 帧采样看着冻住的盘面而断言全 PASS）—— 七条都修好并在 r2 / r3 复核。
2. **每一轮的两条非 `ok` 判定都是声明过的**：`e06` 的同名批量拒绝（`-32000`，D-3 的证据）与一条
   故意打在不存在属性上的边界断言（`-32001`）。`e05`/`e09` 的 `project_read_text_file` sha
   **逐字节相同**（Platformer `0dd8bf57…`/834 B，Match-3 `7772574a…`/842 B），即被拒的批量
   **什么都没写**；两次运行的 `running_game_get_scene_tree` 共 114/115 与 68/69 个节点名里
   **0 个 `@` 开头**。
3. **独立复算不是转述**：`recovery\\work\\task102\\recompute_readbacks.py` 不看 `report.json`、
   不看断言助手，也不看 C# —— 它把载荷**打印出来的** `Dump()` 一行行拆开，用**自己**的规则重算：
   Platformer 的 `MapHash` 由**打印出来的 ASCII 地图**重推（实心 1 / 终点 5 / 收集物 3 / 空 2）、
   `StateHash` 由同一行上的 `player=`/`vel=`/`on_ground=` 重推，Match-3 的 `BoardHash` 由**打印出来的
   数字棋盘**重推（`h = h*31 + (value+1)`，行优先），三者都是 32 位 multiply-31 链；再把会话里那些
   **由 Python 第二实现算出来的字面量**（抛物线逐帧高度与落地帧、撞墙像素、收集物三拍、掉坑两拍、
   指定交换后的整盘与哈希、连锁长度与得分、两波连锁的整盘）与载荷在**本轮响应文件里实际回报的
   `actual`** 逐条对齐。**Platformer 0 处不符、Match-3 0 处不符**（`logs\\recompute-plat-r2.txt`、
   `logs\\recompute-m3-r3.txt`）。
4. **「会动的证据」两路都有**：①**多帧属性采样**（先冻结基线、再自动时钟 30 帧）——
   Platformer 的冻结基线 5 个属性各 1 个值、自动疾跑 30 帧里 `PlayerX` **29 个不同值 140→252**；
   Match-3 的冻结基线 4 个属性各 1 个值、自动对局 30 帧里 `BoardHash` **26 个不同值**、
   `Moves` 3→32、`Score` 150→1270。②**像素差 + 独立复算**（逐调用对 + 保存帧）：
   Platformer **40/228**（编辑器 1/14、游戏 39/214）、Match-3 **22/145**（1/14、21/131），
   两款的 `recomputed-vs-trace mismatches` 都是 `none`，`user://` 七帧的 sha 与 `report.json`
   逐值一致、**7/7 互不相同**，帧链逐对独立复算 **0 处分歧**。
5. **时钟全部与帧率无关**：两款都是浮点累加器（`_autoAccum += delta * rate`，不用
   `(int)(delta*rate)`，即 F-1 的修法），`Elapsed` 是每帧 `+= delta` 的浮点秒表；每款另有**两个**
   独立增量属性（`LastHookSteps` = 钩子这次调用做了多少、`LastAutoSteps` = 这一帧的时钟走了多少），
   且 Platformer 的 `Ticks` 只由 `_Process` 写、`Frames` 只由固定帧写 —— **一个属性一个写者**。
   两款都在时钟跑过 30 帧之后断言 `LastHookSteps` **仍是钩子写下的那个值**。
6. **一条如实记录的采样相位现象（不是缺陷）**：Platformer 的 30 帧时钟采样里 `LastAutoSteps`
   只有 `{1, 0}` 两个值、且第 1 帧之后恒为 0，而 `AutoTicks` 同期涨了 28 —— 因为这台机器上
   引擎帧率远高于 60（采样点之间的实际间隔约 2.4 帧），累加器每 2.4 帧才凑满 1 tick，
   采样点恰好总是落在「还没凑满」的那一帧上。`LastAutoSteps` 写的是它自己那一帧的事实，
   累计量 `AutoTicks` 才是「时钟真的走了多少」。读采样时必须把两者分开读。
7. **`--import` 的关机期访问违例本轮 0 次**：五次导入（Platformer r1/r2、Match-3 r1/r2/r3）
   全部 `IMPORT_EXIT=0`、`import.stderr.txt` 0 字节。累计口径由 3/23 变成 **3/28**（待办 2 不变）。
8. **门跑器**：本轮**没有模块字节改动**（引擎仓 `git status` 空、`git diff --name-only 2385fe2fb..HEAD`
   仍只有两份 `.md`），因此按 TASK-099 的预检直接判 `ANCHOR_STRUCTURAL_EQUIVALENT` +
   `RESULT=SKIP_REBUILD` + `GATES_SKIPPED=1`（exit 0，`runs\\gates\\task102-doconly\\summary.txt`）——
   **如实说明：十道门本轮一门未跑**，没有重建、没有 push 代码（T-1 只是记录，没有动模块）。
9. **模板增补（写给下一款）**：①**第二实现要覆盖「生成出来的」默认状态**，不只是被钉住的盘面 ——
   M3-1 的猜测字面量只有复算 `BuildBoard()` 才能消掉；②**采样钉板必须先证明它能一直动** ——
   M3-4 的教训，生成器应先在 Python 里实测「这段窗口它能动多少次」再写进会话；
   ③**把「采样期间状态没变」做成会 FAIL 的断言**（`neq` 一个窗口开始时的哈希），
   而不是只靠采样里的一串常数；④**世界边界的碰撞解算不要复用地图内部的格子相对公式** ——
   C# 的整数除法向零截断，负方向的世界边界会给出反直觉的答案（PL-1）；
   ⑤半掩的错误最危险：`execute_gdscript` 的 `ok` 不等于脚本执行成功，必须配像素差与场景树证据（T-1）。

"""

NEXT = """6. **（TASK-102 续）** 台账已到第 15 行（第 14 款 Platformer `runs\\platformer\\plat-task102-r2`，
   228/228 facts、像素差 40/228 非零；第 15 款 Match-3 `runs\\match3\\m3-task102-r3`，145/145 facts、
   像素差 22/145 非零）。模板再添五条（见「TASK-102 记录」第 9 条）：**第二实现要覆盖生成出来的默认状态**、
   **采样钉板要先证明它能一直动**、**把「采样期间状态没变」做成会 FAIL 的断言**、
   **世界边界不要复用格子相对公式**、**`execute_gdscript` 的 `ok` 不等于脚本执行成功**。
   下一款（第 16 款）继续复制同一套模板：静态节点一次批量建好、动态对象运行期新建、
   `ForceTestState` 一次钉死、**多帧采样先于会改变状态的那一步**、
   **增量属性与帧率无关且单一写者**、建场景那一步故意重跑同名批量、任何时钟都用浮点累加器，
   并额外带上「采样窗口内状态必然改变」的断言。
"""

with io.open(LOG, "r", encoding="utf-8") as handle:
    text = handle.read()


def sub_once(haystack, needle, replacement, label):
    count = haystack.count(needle)
    if count != 1:
        raise SystemExit("FATAL: anchor %s occurs %d times" % (label, count))
    return haystack.replace(needle, replacement)


# 1. the two rows go directly above the separator that closes the ledger table
# (no leading newline: the row that is already there ends with one, and an extra
# blank line would break the markdown table)
anchor_rows = "\n---\n\n## 缺陷登记（跨轮累计）"
text = sub_once(text, anchor_rows, ROW_14 + ROW_15 + anchor_rows, "ledger-table-end")
# 2. T-1 goes at the end of the tool-defect table
anchor_tool = "\n### D-1 定域更正（TASK-095，2026-09-27）"
text = sub_once(text, anchor_tool, TOOL_DEFECT + anchor_tool, "tool-defect-table-end")
# 3. the seven game rows, the record section and the next-step note go just above 待办
anchor_next = "\n---\n\n## 待办"
text = sub_once(text, anchor_next,
                DEFECTS + "\n---\n\n" + RECORD + anchor_next, "todo-head")
# 4. the next-step note goes at the very end of the 待办 list
text = text.rstrip("\n") + "\n" + NEXT

with io.open(LOG, "w", encoding="utf-8", newline="\n") as handle:
    handle.write(text)
print("wrote %s (%d bytes)" % (LOG, len(text)))
