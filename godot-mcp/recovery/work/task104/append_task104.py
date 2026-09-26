#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""TASK-104: append the ledger rows, the task record, the twenty-game milestone and
the independent-acceptance entry point to GAME-LOOP-LOG.md, and decision D152 to
DECISIONS.md.

Written by a Python writer, never by a shell redirect (iron rule 1), and in UTF-8
so the Chinese text cannot be mangled by a PowerShell 5.1 ANSI round trip.
"""

import io
import os
import sys

ROOT = r"F:\moonbit-hof-rs"
LOG = os.path.join(ROOT, "godot-mcp", "GAME-LOOP-LOG.md")
DECISIONS = os.path.join(ROOT, "DECISIONS.md")

ROWS = [
    u"| 18 | R-Type | C# | 223（编辑器 14 / 游戏 209） | **223/223（100%）**（编辑器 14/14、游戏 209/209） | "
    u"编辑器：`failed=1`（**声明的同名拒绝**，D-3）、`ok_effect_observed=1`、`ok_file_effect_observed=4`、`ok_no_effect_observed=8`；"
    u"游戏：`failed=1`（**声明的边界调用**，`-32001`）、`ok_effect_observed=83`、`ok_file_effect_observed=101`、`ok_no_effect_observed=24` | "
    u"**0 / 1**（**RT-1 会话**：r1 的 `g114-assert-rejected` 期望 `RejectedMoves=0` 实得 **1** —— 游戏结束后那次 `MovePlayer` 确实被拒并计数，"
    u"而生成器只发了调用、没有让自己那份 Python 第二实现跟着走同一步（与 K-1/TD-1 同一类：期望值必须来自它所断言的那一刻）；"
    u"补上 `lose.fire()` / `lose.move(8, 0)`，从模板重新实例化后重跑 r2） | `runs\\rtype\\rt-task104-r2`（首轮 `runs\\rtype\\rt-task104-r1`） | "
    u"第 18 个游戏。800×600 场地、**整数运动学**（船 8 px/次调用，玩家子弹 16、敌机 3、敌弹 6 px/步），"
    u"**编队入场**（第 k 个出生点 = `(830 + (k/3)*40, 120 + (k%3)*70)`，一边入场一边整体左移）、三波 4/5/6 个敌人、"
    u"敌机 45 步固定冷却的射击、子弹取**出生顺序里第一个**重叠的敌机、越界敌机扣命、生命与得分。"
    u"**像素差 87/223 非零**（编辑器 1/14、游戏 86/209），`user://` 四帧逐对 **2069 / 7095 / 7547 px**、四个 sha **4/4 互不相同**；"
    u"独立复算（`task104\\pixel_recompute.py` 逐调用对 + `task104\\frames_recompute.py` 保存帧 + 本轮 `recompute_readbacks.py`）**0 处不符**。"
    u"断言 **99 PASS + 1 条声明的边界失败**（`-32001`）＋ **1 条屏幕文本 PASS**（`WAVE CLEARED`）= **101 PASS / 0 FAIL**。"
    u"**Python 第二实现**（`recovery\\work\\task104\\make_session_rtype.py` 的 `RSim`）独立算出并作为断言字面量的有："
    u"编队逐帧的 `EnemyList`、子弹与敌弹的 `BulletList`/`EnemyBulletList`、每一次碰撞后的 `StateHash`、"
    u"以及**一整局**（三波 15 个敌人、6 杀 9 漏、剩 49 命、600 分、960 步、Wave=3）的每一步结果。"
    u"规则逐条钉住：四个方向的移动与四处边界钳位（含两条会被记进 `RejectedMoves` 的“原地不动”拒绝）、"
    u"子弹出右边界消失（104+44×16 ≥ 800）、一次击杀 = 100 分、敌机 45 步冷却后开火（枪口 = `(x-8, y+6)`）、"
    u"中弹扣命、敌机穿越整场扣命、最后一命耗尽即败（钩子停在 1/3 步）、三波清空即胜。"
    u"与帧率无关的增量 `LastHookSteps`（`StepFrames(3)`→3）在时钟跑过 12 帧之后仍是 3，而 `LastAutoSteps` 归 0；"
    u"时钟是浮点累加器 `_autoAccum += delta*AutoClock`，`Elapsed` 是每帧 `+= delta` 的浮点秒表。"
    u"多帧采样：冻结基线 12 帧（`Steps`/`EnemiesAlive`/`BulletsActive`/`StateHash` 各 1 个值，`Elapsed`/`Ticks` 各 12 个不同值）"
    u"对自动时钟 30 帧，并带三条**会 FAIL 的硬断言**（`Steps gt 0`、`EnemiesSpawned gt 0`、`StateHash neq H0` —— M3-4 的教训写进断言本身）。"
    u"`e06` 同名批量被 `-32000` 拒绝（`conflicts` 3 条：`Background`/`Hud`/`Status`），`e05`/`e09` 的 sha `0494b8a0…`（850 B）**逐字节相同**；"
    u"`project_build_csharp` exit 0（4266 ms）、`editor_get_errors count=0`；三次 `running_game_get_scene_tree` 共 **214 个节点名 0 个 `@` 开头**；"
    u"声明的 `rt_fire` 动作**按按下沿**只发一发（`InputShots=1`） |",

    u"| 19 | Puzzle Bobble | C# | 157（编辑器 14 / 游戏 143） | **157/157（100%）**（编辑器 14/14、游戏 143/143） | "
    u"编辑器：`failed=1`（**声明的同名拒绝**，D-3）、`ok_effect_observed=1`、`ok_file_effect_observed=4`、`ok_no_effect_observed=8`；"
    u"游戏：`failed=1`（**声明的边界调用**，`-32001`）、`ok_effect_observed=27`、`ok_file_effect_observed=91`、`ok_no_effect_observed=24` | "
    u"**0 / 0**（首轮一次通过，没有发现工具缺陷或游戏/驱动缺陷） | `runs\\puzzlebobble\\pb-task104-r1` | "
    u"第 19 个游戏。8×12 的方形泡泡网格（40 px/格）、**六色**、底部中央的发射器、"
    u"**五种整数发射方向** `(±2,-1) (±1,-1) (0,-1)`（一格一步，两侧墙反弹）、"
    u"**同色四连通三连消除**、**悬空掉落**（与顶行不连通的泡泡落下并计分）、"
    u"**连锁**（掉落按“代”推进：只有正下方为空的浮空泡泡先落，一层一代，每一代提升链倍率）、"
    u"**失败线**（结算后任何停在 row ≥ 10 的泡泡判负）、清空棋盘判胜。"
    u"**像素差 29/157 非零**（编辑器 1/14、游戏 28/143），`user://` 四帧逐对 **53444 / 18251 / 2929 px**、四个 sha **4/4 互不相同**；"
    u"独立复算（`pixel_recompute.py` + `frames_recompute.py` + `recompute_readbacks.py`）**0 处不符**。"
    u"断言 **85 PASS + 1 条声明的边界失败**（`-32001`）＋ **1 条屏幕文本 PASS**（`BOARD CLEARED`）= **87 PASS / 0 FAIL**。"
    u"**Python 第二实现**（`make_session_puzzlebobble.py` 的 `BSim`）独立算出并作为断言字面量的有："
    u"**初始棋盘**（同一条 LCG `seed=(seed*1103515245+12345) mod 2^31`、`(seed>>16)%6`、行优先填 4 行 + 同一套“去掉三连”的稳定循环）、"
    u"它的 `Board`/`BoardHash`/`BubblesInUse`、五种方向的飞行与**第 3 步的墙面反弹**、"
    u"一发命中的**落点**与**消除/掉落/连锁/得分**（三连：`attach=(4,3)`、chain 2、cleared 3、dropped 1、70 分；"
    u"两格浮空塔：`attach=(4,6)`、**chain 4**、cleared 3、dropped 3、**210 分**）、失败线那一发的落点与判负、以及清空棋盘的那一发（30 分、`Won`）。"
    u"规则逐条钉住：`Probe` 的 outside/empty/occupied/shooter/projectile 五种命名与颜色值、`Aim` 的五档与两端钳位（同向重设被拒）、"
    u"同色重设后 `ShooterColor` 前进到 `NextColor`、每发之后 `Shots` 递增、结束后 `Shoot`/`Aim` 被拒。"
    u"与帧率无关的增量 `LastHookSteps`（`StepFrames(3)`→3）在时钟跑过 12 帧之后仍是 3，而 `LastAutoSteps` 归 0；时钟是浮点累加器。"
    u"多帧采样：冻结基线 12 帧（`Steps`/`BubblesInUse`/`BoardHash` 各 1 个值，`Elapsed`/`Ticks` 各 12 个不同值）"
    u"对自动时钟 30 帧（**先发射再开钟**，否则棋盘无事可做），带三条**会 FAIL 的硬断言**（`Steps gt 0`、`BoardHash neq H0`、`AutoTicks gte 1`）。"
    u"`e06` 同名批量被 `-32000` 拒绝（`conflicts` 3 条），`e05`/`e09` 的 sha `3723211c…`（868 B）**逐字节相同**；"
    u"`project_build_csharp` exit 0（2489 ms）、`e13` 回 `invalid_count=0`（本轮它是 `valid=true`）、`editor_get_errors count=0`；"
    u"树里 **214 个节点名 0 个 `@` 开头**；声明的 `pb_shoot` 动作按按下沿只发一发（`InputShots=1`） |",

    u"| 20 | Lunar Lander | C# | 230（编辑器 14 / 游戏 216） | **230/230（100%）**（编辑器 14/14、游戏 216/216） | "
    u"编辑器：`failed=1`（**声明的同名拒绝**，D-3）、`ok_effect_observed=1`、`ok_file_effect_observed=4`、`ok_no_effect_observed=8`；"
    u"游戏：`failed=1`（**声明的边界调用**，`-32001`）、`ok_effect_observed=39`、`ok_file_effect_observed=154`、`ok_no_effect_observed=22` | "
    u"**0 / 0**（首轮一次通过，没有发现工具缺陷或游戏/驱动缺陷） | `runs\\lunarlander\\ll-task104-r1` | "
    u"第 20 个游戏，也是 D138「至少 20 款」的收口款。800×600 月面、地面线 y=560、**三个着陆台**（120–200 / 360–440 / 600–680，倍率 1/2/1）；"
    u"**十二档整数姿态**（30° 一档）与**整数推力表**（正立 (0,-4)）、重力每步 +1、每次点火消耗 1 燃料、"
    u"**整数积分** `vy += 重力; x += vx; y += vy`；着陆判定 = 在着陆台上 且 `|Vx| ≤ 2` 且 `|Vy| ≤ 6` 且距正立 ≤ 1 档，"
    u"存活则得分 = **剩余燃料 × 台倍率**，否则坠毁；飞出场地也是坠毁。"
    u"**像素差 41/230 非零**（编辑器 1/14、游戏 40/216），`user://` 四帧逐对 **6798 / 1117 / 6885 px**、四个 sha **4/4 互不相同**；"
    u"独立复算（`pixel_recompute.py` + `frames_recompute.py` + `recompute_readbacks.py`）**0 处不符**。"
    u"断言 **148 PASS + 1 条声明的边界失败**（`-32001`）＋ **1 条屏幕文本 PASS**（`THE EAGLE HAS LANDED`）= **150 PASS / 0 FAIL**。"
    u"**Python 第二实现**（`make_session_lunarlander.py` 的 `LSim`）独立算出并作为断言字面量的有："
    u"三座台与倍率、每一项容差、十二档推力表、以及**一条真实的整数下降轨迹** —— 生成器先在 Python 里**搜**出「自由落体到 y≥430 → 连续点火 8 步 → 滑行」的方案，"
    u"再按搜出来的相位驱动载荷，逐相位断言 `Lx`/`Ly`/`Vx`/`Vy`/`Fuel`/`Steps`/`StateHash`/`LastHookSteps`（35 步、右脚在 554、`Vy=3`、剩 492 燃料、**台 1 → 984 分**）。"
    u"**事后复算独立重放整条轨迹**：`recompute_readbacks.py` 只吃运行自己写的响应文件与 `call-index.txt` 的调用顺序，"
    u"在**自己的**代码里重做「点火/重力/积分/触地」并逐检查点比对 —— **17 个检查点、0 处不符**。"
    u"规则逐条钉住：`Thrust()` 的脉冲与 `SetThrust` 的持续点火分开、空箱点火被拒、"
    u"**每一条容差的边界两侧**（`|Vy|` 6 存活 / 7 坠毁、`|Vx|` 4 坠毁、90° 坠毁、**330° 存活**证明容差是两侧的、"
    u"错过所有着陆台坠毁、左右台各按自己倍率给分）、飞出场地即坠毁、结束后点火被拒。"
    u"与帧率无关的增量 `LastHookSteps`（`StepFrames(3)`→3）在时钟跑过 12 帧之后仍是 3，而 `LastAutoSteps` 归 0；时钟是浮点累加器。"
    u"多帧采样：冻结基线 12 帧（`Lx`/`Ly`/`Vx`/`Vy`/`Fuel`/`StateHash` 各 1 个值，`Elapsed`/`Ticks` 各 12 个不同值）"
    u"对自动时钟 30 帧，带四条**会 FAIL 的硬断言**（`Steps gt 0`、`Ly gt 起始值`、`StateHash neq H0`、`AutoTicks gte 1`）。"
    u"`e06` 同名批量被 `-32000` 拒绝（`conflicts` 3 条），`e05`/`e09` 的 sha `50ec3aba…`（844 B）**逐字节相同**；"
    u"`project_build_csharp` exit 0（3782 ms）、`e13` 回 `invalid_count=0`、`editor_get_errors count=0`；"
    u"树里 **136 个节点名 0 个 `@` 开头**；声明的 `ll_thrust` 动作按按下沿只点一次火（`InputThrusts=1`） |",
]

RECORD = u"""
---

### TASK-104 记录（2026-09-27）

1. **第 18、19、20 款交付**，D138 的「至少 20 个经典小游戏、全部 C#」到此收口。三款都从**模板实例化**
   （`tools\\new_game.ps1`），**游戏内容全部由 MCP 调用写成**：`project_edit_script` 写 C# 载荷、
   `editor_add_nodes_batch` 一次建好三个静态节点（`Background`/`Hud`/`Status`，其后再不许静态节点）、
   `editor_add_input_action` 声明一个动作、`editor_save_scene`、`project_build_csharp`、`project_validate_scripts`；
   游戏相全部是 `running_game_*`。三款的调用数、判定分布与 `facts_complete` 见上面第 18/19/20 行，
   全部取自各自那一轮的 `report.json` / `ledger-*.txt`。
2. **固化模板照用并再添两条**：
   * 既有：批量建静态节点 → 运行期创建动态对象 → 只钉游戏本身可达的状态 → 先采样、后改变 → 故意重跑同名批量 →
     帧率无关步进 → 一个属性一个写者 → 采样带「必须动」硬断言 → 像素差 + Python 第二实现独立复算；
     以及 TASK-103 的「每段测试从自己的 `ForceTestState` 开始」「重跑从模板重新实例化」「`static` 只能调 `static`」
     「断言紧挨它引用的那一刻」「取证脚本自己也要能读错」。
   * **新增（写给第 21 款起）**：①**两态动作要成对测**（本题连发/脉冲、发射/瞄准，`Thrust()` 与 `SetThrust()` 是两种写者，
     各有断言）；②**每一条容差的边界两侧都要测**，而且**越界的“存活侧”也要测**—— LL 的 330° 存活证明容差是两侧的，
     只测 90° 坠毁会让人误以为“必须恰好正立”。
3. **缺陷清单（分栏）**：
   * **工具缺陷（`modules\\mcp_server`）：0 条。** 本轮**没有改动模块任何一个字节**，因此 §C 的收尾走的是
     **免跑判定**（`run_gates.ps1` 纯文档预检 → `ANCHOR_STRUCTURAL_EQUIVALENT` + `SKIP_REBUILD`），
     十道门与 `accept_m1` **未重跑**，原因与判定见 `recovery\\reports\\TASK-104-REPORT.md` §C 与本文件末尾。
   * **一行诚实记录（不是缺陷）**：`project_validate_scripts` 在 rtype r2 上回 `not_compiled_count=1`
     （`category=not_compiled`，理由是「构建产物里没有这个源文件的记录」）；同一条工具在 pb r1 上回 `valid=true`。
     TD/MC（TASK-103）当时也是 `not_compiled=1`。三次的 `invalid_count` 都是 0、`project_build_csharp` 都是 exit 0，
     所以这是**判定类别随时序变化的既有边界**（工具自己把理由写清楚了），不是回归，也不构成本轮的游戏缺陷。
   * **游戏或驱动缺陷：1 条**
     | id | 层 | 现象（证据） | 根因 | 处置 → 重跑结果 |
     |---|---|---|---|---|
     | **RT-1** | R-Type **会话** | r1 的 `g114-assert-rejected` 期望 `RejectedMoves=0` 实得 **1**（同段 `g112` 期望 `BulletsFired=0` 恰好也是 0，所以没照出另一半） | 生成器只把调用发出去、**没有让自己那份 `RSim` 跟着走同一步**：游戏结束后的 `FireBullet()` / `MovePlayer()` 在载荷里被拒并计数，而在 `RSim` 里这两次调用根本没发生 | 补 `lose.fire()` 与 `lose.move(8, 0)`；按 TD-2 的教训**从模板重新实例化**（先写 sha256 清单再 `Move-Item`）后重跑 r2 → `101 PASS / 0 FAIL` |
   * **取证工具自身 2 条（`E-1`，明确**不是**模块缺陷、也不是游戏缺陷）**：都在本轮新写的
     `recovery\\work\\task104\\recompute_readbacks.py` 里。
     ①哈希复算分支写成了 `"state_hash=" in fields`，而 `fields` 是**字典**（键不含 `=`）→ 条件恒假 →
     两款各只算到 **2 个哈希**（本该更多）却仍报 `0 处不符` —— **静默少算**，比报错更危险；
     改成 `"state_hash" in fields` 后 R-Type/PB/LL 各 2 个 `Dump()` 读数全部参与复算。
     ②`SetThrust` 的回读按 `text.split("=",1)[1].strip()=="True"` 解析，实得 `"True fuel=500"` → 恒假 →
     LL 的独立重放**从头到尾没开过火**，报了 **10 处不符**（`g115`/`g125` 的 `steps`/`y`/`vy`/`fuel`）；
     改成 `grab(text, "thrust_on") == "True"` 后 **17 个检查点 0 处不符**。
     ②的意义在**它响了**：这条复算脚本没有和载荷“互相迁就”地静默同意，而是把 10 条不一致摆出来，
     才让人去分清「是载荷错了」还是「是复算脚本错了」—— 上一轮 R-1 的教训（取证脚本自己也要能读错）在这里第二次应验。
4. **「像素差 + 独立复算」三款的真实数值**：R-Type **87/223**（编辑器 1/14、游戏 86/209），
   `user://` 四帧 **2069 / 7095 / 7547 px**；Puzzle Bobble **29/157**（1/14、28/143），四帧 **53444 / 18251 / 2929 px**；
   Lunar Lander **41/230**（1/14、40/216），四帧 **6798 / 1117 / 6885 px**。
   三款的 `recomputed-vs-trace mismatches` 都是 **0**，保存帧 sha 与 `report.json` 逐值一致、**4/4 互不相同**，
   帧链逐对独立复算 **0 处分歧**；`recompute_readbacks.py` 还独立重算了
   R-Type 的 `StateHash`（由打印出来的 `player`/`enemies`/两张子弹表重推）、
   Puzzle Bobble 的 `BoardHash`（由打印出来的棋盘重推）**与初始棋盘本身**（同一条 LCG + 同一个稳定循环）、
   Lunar Lander 的 `StateHash` **与整条积分轨迹**（按 `call-index.txt` 的调用顺序重放，17 个检查点）。
5. **时钟与单写者（继承 G1/F-1/M3-4）**：三款都是浮点累加器（`_autoAccum += delta * rate`），
   `Elapsed` 是每帧 `+= delta` 的浮点秒表；三款各有 `LastHookSteps`（钩子）与 `LastAutoSteps`（每帧时钟）**两个**属性，
   且都在采样里出现过；三款都在时钟跑过 12 帧之后断言 `LastHookSteps` **仍是钩子写下的那个值**。
   **M3-4 的教训写进断言本身**：三款的采样后面都跟着会 FAIL 的硬断言（`Steps gt 0` 与一个 `neq 窗口起始哈希`），
   所以「时钟在走而世界冻住」不再是采样里的一串常数，而是一条红。
"""

MILESTONE = u"""
---

## 里程碑：20 款（TASK-104 收口）

* **口径**：D138 —— 轮次不设限，至少 20 个经典小游戏、**全部 C#**，每款都要有可复算的「操作有效性」证据。
  TASK-104 交付第 18/19/20 款，口径达成。

### 20 款一览（每行一款；调用数 = 编辑器 / 游戏，`facts` = 可重建事实齐全的调用占比）

| # | 游戏 | 会话调用数 | `facts_complete` | 像素差（非零 / 可比） | 独立复算 | 缺陷（工具 / 游戏或驱动） | 证据路径 |
|---|---|---|---|---|---|---|---|
| 1 | Pong | 23 / 29（52） | 52/52（100%） | 14/74 | 0 处不符 | 0 / 6 | `runs\\pong\\pong-clean-task097` |
| 2 | Breakout | 21 / 34（55） | 55/55（100%） | 14/89 | 0 处不符 | 0 / 5 | `runs\\breakout\\breakout-clean-task097` |
| 3 | Snake | 20 / 31（51） | 51/51（100%） | 13/102 | 0 处不符 | 0 / 4 | `runs\\snake\\snake-clean-task097` |
| 4 | Tetris | 6 / 36（42） | 42/42（100%） | 11/42 | 0 处不符 | 0 / 3 | `runs\\tetris\\tetris-task096-r2` |
| 5 | Space Invaders | 15 / 44（59） | 59/59（100%） | 12/59 | 0 处不符 | 0 / 0 | `runs\\spaceinvaders\\si-task097-r1` |
| 6 | Asteroids | 16 / 55（71） | 71/71（100%） | 16/71 | 0 处不符 | 0 / 1 | `runs\\asteroids\\ast-task098-r2` |
| 7 | Pac-Man | 16 / 64（80） | 80/80（100%） | 15/80 | 0 处不符 | 0 / 1 | `runs\\pacman\\pac-task098-r2` |
| 8 | Frogger | 16 / 74（90） | 90/90（100%） | 17/90 | 0 处不符 | 0 / 0 | `runs\\frogger\\frog-task099-r1` |
| 9 | Flappy Bird | 14 / 78（92） | 92/92（100%） | 22/92 | 0 处不符 | 0 / 1 | `runs\\flappy\\flappy-task099-r2` |
| 10 | 2048 | 16 / 113（129） | 129/129（100%） | 26/129 | 0 处不符 | 0 / 1 | `runs\\game2048\\2048-task100-r2` |
| 11 | Minesweeper | 14 / 141（155） | 155/155（100%） | 21/155 | 0 处不符 | 0 / 1 | `runs\\minesweeper\\mine-task100-r2` |
| 12 | Sokoban | 14 / 176（190） | 190/190（100%） | 29/190 | 0 处不符 | 0 / 1 | `runs\\sokoban\\soko-task101-r2` |
| 13 | Bomberman | 14 / 219（233） | 233/233（100%） | 45/233 | 0 处不符 | 0 / 3 | `runs\\bomberman\\bomb-task101-r4` |
| 14 | Platformer | 14 / 214（228） | 228/228（100%） | 40/228 | 0 处不符 | 0 / 2 | `runs\\platformer\\plat-task102-r2` |
| 15 | Match-3 | 14 / 131（145） | 145/145（100%） | 22/145 | 0 处不符 | 1 / 4（X-1 已于 TASK-103 修） | `runs\\match3\\m3-task102-r3` |
| 16 | Tower Defense | 14 / 131（145） | 145/145（100%） | 31/145 | 0 处不符 | 0 / 1 | `runs\\towerdefense\\td-task103-r3` |
| 17 | Missile Command | 14 / 113（127） | 127/127（100%） | 21/127 | 0 处不符 | 0 / 3 | `runs\\missilecommand\\mc-task103-r3` |
| 18 | **R-Type** | 14 / 209（223） | 223/223（100%） | **87/223** | **0 处不符** | **0 / 1** | `runs\\rtype\\rt-task104-r2` |
| 19 | **Puzzle Bobble** | 14 / 143（157） | 157/157（100%） | **29/157** | **0 处不符** | **0 / 0** | `runs\\puzzlebobble\\pb-task104-r1` |
| 20 | **Lunar Lander** | 14 / 216（230） | 230/230（100%） | **41/230** | **0 处不符** | **0 / 0** | `runs\\lunarlander\\ll-task104-r1` |

合计 **2 441 次调用**（编辑器 300 / 游戏 2 141），`facts_complete` **20 款全部 100%**。

### 证据覆盖率

* **像素证据：20/20 款可得且非零。** 每一款都有「逐调用捕获对里非零的组数」与「`user://` 保存帧链」两路；
  帧链逐对（engine 规则 >10 与 any-difference 两套）**都由 `pixel_recompute.py` / `frames_recompute.py` 独立重算**，
  与 `report.json` **逐对一致（0 处分歧）**。第 1–3 款的像素列是 TASK-097 清理副本层后**回填**的（见 D-1 结案节）。
* **独立复算：20/20 款。** 每一款都有「从规则重写的 Python 第二实现」产出会话里的断言字面量
  （`recovery\\work\\task{task}\\make_session_<game>.py`），并且事后有一支**不 import 生成器、不看 `report.json`、不看 C#**
  的复算脚本（`recompute_readbacks.py` 等）把打印出来的状态重算一遍：哈希、地图/路径/棋盘、整数轨迹、逐格爆炸范围、
  消除与掉落结果。**20 款合计 0 处不符。**
* **事后复算的能力清单（截至 TASK-104）**：R-Type `StateHash`（由打印列表重推）、
  Puzzle Bobble `BoardHash` **与初始棋盘本身**（LCG + 稳定循环重算）、
  Lunar Lander `StateHash` **与整条 35 步积分轨迹**（按 `call-index.txt` 顺序重放，17 个检查点）、
  Tower Defense `MapHash`/`PathHash`（重走一遍路径）、Missile Command `CityHash`/`WorldHash`、
  Platformer `MapHash`/抛物线、Match-3 整盘与连锁、Sokoban/Bomberman/2048/Minesweeper 的哈希与逐格结果。

### 工具缺陷累计清单与修复轮次

| id | 现象 | 修复轮次 | 状态 |
|---|---|---|---|
| **D-3** | `editor_add_nodes_batch` 对同名节点既不拒绝也不报告 → `.tscn` 里进整份副本层（也是 D-1 的真因） | **TASK-097** | 已修；20 款每一轮的编辑器相都**故意重跑同名批量**，`-32000` + `data.conflicts` 成为常态化证据 |
| **D-1** | 像素回读恒返回第一帧 | **TASK-097（D-3 的副产物）** | 已结案；三个老场景的副本层已删，像素列已回填 |
| **D-2** | `accept_m1.ps1` 的就绪判据是吞吐（≥20 fps）而不是就绪 | **TASK-094** | 已修（改为 `frame_count` 连续 6 次严格递增） |
| **G-1** | `run_gates.ps1` 的锚点默认值落后于引擎仓 HEAD | **TASK-099** | 已修（锚点取二进制自己的 `--version` + 纯文档预检跳过） |
| **X-1** | `running_game_execute_gdscript` 的脚本**运行期报错**回 `ok` + `null`，诊断只落引擎 stderr | **TASK-103** | 已修（`-32000` + `data.script_error` + `data.suggestion`；成功但无返回值带 `note`；错误进 trace），修后两变体重建、十道门全绿 |
| **X-2（观察，未修）** | `project_validate_scripts` 的 `valid` 有时缺席（`not_compiled_count=1`，工具自己写明理由），同一命令在另一轮回 `valid=true`；三次的 `invalid_count` 都是 0 | —— | **只记录**：它是工具自己说清楚的判定类别，不是回归；修它要动模块 → 重建两变体 + 十道门，本任务的范围与 C) 分支都不含此改动 |
| **R-1 / E-1** | **取证脚本自身**的两类读错（`last=` 之后的片段覆盖真字段；字典成员判断写成带 `=` 的字符串；`True fuel=500` 当成 `True`） | TASK-103 / TASK-104 | 已修；另一件**证据**：E-1 的第二个 bug 是**响亮地**报出 10 处不符才被发现的 —— 复算脚本必须能喊 |

### `--import` 累计口径

* **崩溃形态（`exit=-1073741819` / `0xC0000005`，stderr 只有 `Parameter "singleton" is null.`）**：
  TASK-099 留档时是 **3/23**；TASK-100 的 4 次、TASK-101 的 6 次、TASK-102 的 5 次、TASK-103 的 6 次、
  TASK-104 的 **4 次**全部 `IMPORT_EXIT=0`。**累计 3/48，TASK-099 之后 25 次导入 0 次复现。**
* **非崩溃形态（同样的 `singleton` 行 + `Thread::~Thread` 警告，但 `IMPORT_EXIT=0` 且导入已跑完）**：
  TASK-104 出现 **1 次**（`runs\\rtype\\rt-task104-r1`，stderr 307 B）。它印证 TASK-099 的定位：
  这条消息是**关机期**的，不是导入失败；`IMPORT_EXIT` 仍然不能当健康信号用。

### 下一步：独立验收入口（TASK-105）

验收子代理应当**只**读下列文件与命令，不读本轮的总结文字：

**要读的工件（按顺序）**

1. `recovery\\reports\\TASK-104-REPORT.md` —— 本轮结论、逐条证据与遗留。
2. `godot-mcp\\GAME-LOOP-LOG.md` —— 台账第 18/19/20 行、`### TASK-104 记录`、本节（里程碑）。
3. `F:\\moonbit-hof-rs\\DECISIONS.md` 的 **D152** —— 本轮的决策与被否决选项。
4. 三份载荷（**唯一**的游戏实现）：
   `godot-mcp\\tools\\sessions\\rtype\\payload\\RTypeGame.cs`、
   `...\\puzzlebobble\\payload\\PuzzleBobbleGame.cs`、
   `...\\lunarlander\\payload\\LunarLanderGame.cs`。
5. 三份会话（**唯一的调用序列**）：`tools\\sessions\\{rtype,puzzlebobble,lunarlander}\\session.json`。
6. 三份生成器 + Python 第二实现：`recovery\\work\\task104\\make_session_{rtype,puzzlebobble,lunarlander}.py`。
7. 三份期望清单：`recovery\\work\\task104\\expectations-{rtype,puzzlebobble,lunarlander}.json`。
8. 三份运行产物：`runs\\rtype\\rt-task104-r2\\`、`runs\\puzzlebobble\\pb-task104-r1\\`、`runs\\lunarlander\\ll-task104-r1\\`
   （`trace-*.jsonl` / `ledger-*.{txt,json}` / `report.{md,json}` / 每调用一个 `<tag>.json` / `call-index.txt` / `shots-*/`）。
9. 本轮自己的证据日志：`recovery\\work\\task104\\logs\\{assert,recompute,pixel,frames,facts,pixelpairs,checksession-py}-<game>.txt`。

**可以自己跑的命令（都是只读）**

```
python tools\\game_report.py  <run-dir> --game=<game> --run-tag=<tag>          # 重算台账/像素/帧链
python recovery\\work\\task104\\assert_summary.py <run-dir>                     # 逐属性断言分栏
python recovery\\work\\task104\\recompute_readbacks.py <run-dir> recovery\\work\\task104\\expectations-<game>.json <game>
python recovery\\work\\task104\\pixel_recompute.py   <run-dir>                  # 逐调用捕获对，两套阈值
python recovery\\work\\task104\\frames_recompute.py  <game> <prefix>-t <run-dir> # 保存帧链 + 与 report.json 对账
python recovery\\work\\task104\\game_facts.py        <run-dir>                  # 构建/校验/@-名/台账事实
python recovery\\work\\task104\\check_session.py     tools\\sessions\\<game>\\session.json
powershell -File recovery\\work\\task104\\check_session_ps.ps1 -Session tools\\sessions\\<game>\\session.json -Label <game>
```

**应当主动构造的反例**

* 把 `expectations-<game>.json` 里任意一条 `expected` 改掉，重跑 `recompute_readbacks.py` —— 它必须报 `LITERAL`/`FAILED`，
  否则「字面量对齐」不是一条真检查。
* 用 `python make_session_<game>.py` 重新生成会话，与仓里的 `session.json` 逐字节比对 —— 生成器必须是**确定性**的。
* 对三款各挑一条**越界的存活侧**断言（LL 的 330°、PB 的 `|Vy|` 边界、R-Type 的钳位）核对它真的在容差之内。
* **不重跑十道门**：本轮**没有改动 `modules\\mcp_server` 任何一个字节**，所以 §C 走的是免跑判定；
  验收若要跑门，请先自己确认引擎仓的工作树与 TASK-103 的 `1f9d0cb1c9` 之间没有编译输入差异
  （`git -C godot-mcp\\godot status --short` 与 `git diff --stat 1f9d0cb1c9..HEAD -- modules\\mcp_server`）。
"""

TODO_ITEM = u"""7. **（TASK-104 续）第 21 款起，模板再加两条**：①**两态动作要成对测** —— 同一个量若既能被「一次调用」写、
   又能被「每帧时钟」写（LL 的 `Thrust()` 对 `SetThrust()`），就必须是**两个属性**、各有自己的断言；
   ②**每条容差的边界两侧都要测，而且越界的「存活侧」也要测** —— LL 的 330° 存活才说明容差是两侧的，
   只测 90° 坠毁会让人误以为规则要求恰好正立。
   台账已到第 20 行，D138 的口径达成；后续轮次若继续加游戏，沿用同一套模板（静态节点一次批量建好、
   动态对象运行期新建、`ForceTestState` 一次钉死、**多帧采样先于会改变状态的那一步**、
   **增量属性与帧率无关且单一写者**、建场景那一步故意重跑同名批量、任何时钟都用浮点累加器、
   采样窗口内状态必然改变的断言、Python 第二实现 + 事后独立复算）。
"""

D152 = u"""
## D152 — TASK-104：第 18、19、20 款 C# 小游戏（R-Type / Puzzle Bobble / Lunar Lander）交付，D138 的「至少 20 款」收口；一条会话缺陷（RT-1）在首轮被照出来并重跑；模块零改动，故收尾走免跑判定

* **日期**：2026-09-27
* **触发问题**：D138 的「至少 20 个经典小游戏、全部 C#」推进到第 18、19、20 款，同时也是对固化模板的第三次压力测试 ——
  这三是三种此前没做过的**时间/空间结构**：①横版卷轴射击（**编队入场**：一波敌人按固定槽位从右侧整体进入并左移、
  两种子弹、两侧碰撞）；②**下落式解谜**（格子棋盘、离散发射角、同色三连、**与顶行不连通的泡泡掉落**、**连锁**、失败线）；
  ③**连续积分物理**（重力、燃料、旋转、以及一个由三项容差共同决定的着陆判定）。要检验的是：
  「可独立复算」这条口径在**整数化的物理积分**上是否仍然成立，以及在**多代级联**（PB 的连锁）上是否还能被 Python 复算。
* **考虑的选项**：
  1. **Lunar Lander 用 Godot 的 `RigidBody2D` / 浮点物理**：省事、像"真游戏"，但着陆速度、着陆点、剩余燃料都会变成
     依赖引擎内部积分顺序的浮点值 —— 「vy 恰好是 6 所以活下来、7 所以坠毁」这种**边界证据**就不再是可复算的确切值。**否**。
  2. **Lunar Lander 用浮点角度 + `Mathf.Sin/Cos` 生成推力**：可以写 360° 平滑旋转，但推力表就变成浮点数，
     C# 与 Python 的 `sin` 末位差异会让"逐检查点相等"变成"近似相等"。**否** —— 改成**十二档整数姿态 + 整数推力表**，
     30° 一档，表值直接写成整数常量，两端没有可分歧的自由度。
  3. **Puzzle Bobble 用真随机填充初始棋盘**：省一条 LCG，但初始棋盘、它的哈希、以及"第一发落点"都不再可复算。**否**。
  4. **Puzzle Bobble 的"连锁"定义成"消除后全局重扫 ≥3 的同色块"**：实现最短，但**它是拼出来的一条规则** ——
     正常局面下棋盘上不会存在没被消掉的 ≥3 同色块，那条分支永远跑不到，"连锁"就成了一条**没有证据支持的规则**。**否**。
  5. **Puzzle Bobble 的悬空泡泡"落到底部堆起来"而不是掉出场外**：能自然地造出新的三连，但落在 `FailRow` 以下会让
     每一次掉落都直接判负（或者要给"掉落的泡泡不触发失败线"打补丁）。**否**。
  6. **R-Type 的"一整局胜利"用 `ForceTestState` 直接钉一个"已经是最后一波且场上无敌人"的状态**：一次调用就能赢，
     但那不是"打完一整局"。**否** —— 生成器在 Python 里把整局（960 步、3 波 15 个敌人、24 次开火）**跑完**，
     再把这个方案原样作为调用序列发出去，胜负与每一步的战果都来自第二实现。
  7. **本轮顺手修 `project_validate_scripts` 的 `not_compiled` 类别**（X-2）：它要动 `modules\\mcp_server` →
     重建两个变体（每次 ~16 分钟）+ 十道门 + `accept_m1` + push；而它**不是回归**（工具自己写明了理由，
     TD/MC 当时也是这个值、`invalid_count` 恒 0）。**否** —— 只登记，按 C) 分支走免跑判定。
* **最终选择**：
  * 三款都从模板实例化（`tools\\new_game.ps1`），**游戏内容全部由 MCP 调用写成**；场景里只有三个静态节点
    （`Background`/`Hud`/`Status`），其余（R-Type 的星空/飞船/编队池/两个弹池 88 个、PB 的 96 个格位 + 失败线 + 发射器 + 弹丸、
    LL 的地面/三台/星空/着陆器/火焰）**全部运行期新建**；每款都**故意重跑同名批量**，`-32000` + `data.conflicts`
    （3 条）与 `e05`/`e09` 的**逐字节相同**成为常态证据。
  * **R-Type**：800×600、**整数运动学**、**编队槽位算术**（第 k 个出生点 = `(830 + (k/3)*40, 120 + (k%3)*70)`）、
    敌机 45 步固定冷却、子弹取**出生顺序里第一个**重叠的敌机、越界敌机扣命、三波 4/5/6。一整局（960 步、6 杀 9 漏、
    49 命、600 分）由 `RSim` 逐步算出并作为断言字面量。
  * **Puzzle Bobble**：8×12 方格、六色、**五种整数方向**（±2/±1/0 列，一格一步）与**两侧墙反弹**、
    **同色四连通三连消除**、**悬空掉落**（与顶行不连通者掉出场外）、**连锁 = 掉落按“代”推进**
    （只有正下方为空的浮空泡泡先落，一层一代，每代提升链倍率）、**失败线**（结算后停在 row ≥ 10 判负）、清空判胜。
    初始棋盘由**同一条 LCG + 同一套去三连的稳定循环**生成，Python 独立复算棋盘本身与它的哈希。
  * **Lunar Lander**：800×600、**十二档整数姿态 + 整数推力表**、重力每步 +1、每次点火 1 燃料、**整数积分**；
    着陆判定 = 在台上 ∧ `|Vx| ≤ 2` ∧ `|Vy| ≤ 6` ∧ 距正立 ≤ 1 档；**得分 = 剩余燃料 × 台倍率**。
    生成器先在 Python 里**搜**出一条安全的下降方案（滑行到 y ≥ 430 → 连续点火 8 步 → 滑行触地，35 步、`Vy=3`、984 分），
    再按搜出来的相位驱动载荷；事后复算脚本**按 `call-index.txt` 的调用顺序独立重放整条轨迹**（17 个检查点、0 处不符）。
  * 三款各有一份**从规则重写**的 Python 第二实现（`make_session_{rtype,puzzlebobble,lunarlander}.py` 的 `RSim`/`BSim`/`LSim`），
    会话里每一个期望字面量都取自它们；`recompute_readbacks.py` 事后**不 import 生成器、不看 `report.json`、不看 C#**，
    只把载荷**打印出来**的状态拿来重算并逐条对齐。
  * **证伪优先**：三款的采样后面都跟着**会 FAIL 的硬断言**（`Steps gt 0`、`neq 一个窗口起始的哈希`、`AutoTicks gte 1`）；
    LL 额外加 `Ly gt 起始值`。**每条容差都测两侧**：`|Vy|` 6 活 / 7 死、`|Vx|` 4 死、90° 死、**330° 活**（证明容差两侧）。
  * **模块零改动** → §C 收尾走**免跑判定**（`run_gates.ps1` 的纯文档预检 → `ANCHOR_STRUCTURAL_EQUIVALENT` + `SKIP_REBUILD`），
    十道门与 `accept_m1` 本任务**未重跑**，原因与判定逐条写进报告。
* **选择理由**：
  * 「可复算」在**连续量**上仍然成立的关键不是"别做物理"，而是**把物理整数化**：姿态离散成 12 档、推力写成整数表、
    积分写成整数加法。于是 LL 的 `vy=6 活 / 7 死` 是一个**确切值**，而它恰好是最有说服力的那条边界证据。
  * 「可复算」在**级联**上仍然成立的关键是**把级联定义成可复算的形状**：PB 的连锁不是"重扫 ≥3"，
    而是"掉落按代推进" —— 每一代的集合都由棋盘上的**代数条件**唯一决定，因此 Python 能逐代复算，
    而且这条规则在正常局面里**真的会被走到**（两格浮空塔 → chain 4）。
  * 一条**会产生 10 条假不一致**的复算脚本比一条永远同意别人的脚本更有价值：E-1 的第二个 bug 正是被它自己"响"出来的。
* **本轮缺陷（详见 `GAME-LOOP-LOG.md` 的 `### TASK-104 记录`）**：
  | id | 层 | 现象（证据） | 根因 | 处置 → 重跑结果 |
  |---|---|---|---|---|
  | **RT-1** | R-Type **会话** | r1 `g114-assert-rejected` 期望 `RejectedMoves=0` 实得 1 | 生成器只发调用、没让自己那份 `RSim` 走同一步（游戏结束后的调用在载荷里被拒并计数） | 补 `lose.fire()`/`lose.move(8,0)`，从模板重新实例化后重跑 r2 → 101 PASS / 0 FAIL |
  | **X-2（观察）** | `project_validate_scripts` | rtype r2 回 `not_compiled_count=1`，pb r1 回 `valid=true`；TD/MC 当时也是 `not_compiled=1` | 判定类别随时序变化，工具自己写明理由 | 只记录；修它要动模块 → 重建两变体 + 十道门，不在本任务范围 |
  | **E-1（取证工具，不算模块缺陷）** | `recovery\\work\\task104\\recompute_readbacks.py` | ①`"state_hash=" in fields`（`fields` 是字典）恒假 → **静默少算**；②`SetThrust` 回读解析成 `"True fuel=500"` → LL 重放从头没开火，报 10 处不符 | 两处都是复算脚本自身的读错 | ①改 `"state_hash" in fields`；②改 `grab(text,"thrust_on")`；修后三款 0 处不符、LL 17 个检查点 0 处不符 |
* **预期影响与回滚点**：
  * 模板再加两条（写给第 21 款起）：**两态动作要成对测**（同一量若既能被一次调用写、又能被每帧时钟写，就必须是两个属性）；
    **每条容差的边界两侧都要测，越界的“存活侧”也要测**。
  * 本轮的工件全部是**新增文件**（三个游戏工程、三份 C# 载荷、三份会话、三份生成器、`recovery\\work\\task104\\` 的全部脚本与日志），
    任何一份都能单独删除而不影响前十七款；回滚点就是删掉这三款并把台账的第 18/19/20 行撤掉。
  * **遗留（不阻塞）**：①`--import` 的关机期消息本轮以**非崩溃**形态出现 1 次（`IMPORT_EXIT=0`），累计崩溃口径仍是 3/48；
    ②三款各自都是经典规则的**最小完整子集**（R-Type 没有道具与地形、PB 没有顶部下压与瞄准线、
    LL 没有地形起伏与风）；③`ForceTestState` 仍允许钉出游戏本身到不了的状态（B-3 的成因），本轮以「会话不这么钉」处置；
    ④X-2 只登记未修。
"""


def insert_after(lines, needle, new_lines):
    for index, line in enumerate(lines):
        if line.startswith(needle):
            return lines[:index + 1] + new_lines + lines[index + 1:]
    raise SystemExit("anchor not found: %r" % needle)


def insert_before(lines, needle, new_lines):
    for index, line in enumerate(lines):
        if line.startswith(needle):
            return lines[:index] + new_lines + lines[index:]
    raise SystemExit("anchor not found: %r" % needle)


def main():
    with io.open(LOG, "r", encoding="utf-8", newline="") as handle:
        log_lines = handle.read().splitlines(keepends=True)
    if any(line.startswith(u"| 20 | Lunar Lander ") for line in log_lines):
        raise SystemExit("REFUSED: the TASK-104 rows are already in GAME-LOOP-LOG.md")
    rows = [row + u"\n" for row in ROWS]
    log_lines = insert_after(log_lines, u"| 17 | Missile Command ", rows)

    record_lines = [line + u"\n" for line in RECORD.split(u"\n")]
    log_lines = insert_before(log_lines, u"## 待办", record_lines)

    milestone_lines = [line + u"\n" for line in MILESTONE.split(u"\n")]
    log_lines = insert_before(log_lines, u"## 待办", milestone_lines)

    # the 待办 list itself gains one item, at the very end of the file
    if log_lines and not log_lines[-1].endswith(u"\n"):
        log_lines[-1] = log_lines[-1] + u"\n"
    log_lines.extend(line + u"\n" for line in TODO_ITEM.split(u"\n"))

    with io.open(LOG, "w", encoding="utf-8", newline="") as handle:
        handle.write(u"".join(log_lines))
    print("updated %s (%d lines)" % (LOG, len(log_lines)))

    with io.open(DECISIONS, "r", encoding="utf-8", newline="") as handle:
        text = handle.read()
    if u"D152" in text:
        raise SystemExit("REFUSED: DECISIONS.md already carries D152")
    if not text.endswith(u"\n"):
        text += u"\n"
    text += D152
    with io.open(DECISIONS, "w", encoding="utf-8", newline="") as handle:
        handle.write(text)
    print("updated %s (+%d chars)" % (DECISIONS, len(D152)))
    return 0


if __name__ == "__main__":
    sys.exit(main())
