#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""TASK-103: the two documentation writers (GAME-LOOP-LOG.md and DECISIONS.md).

Written as a Python writer, never by a shell redirect (iron rule 1). It edits by
exact anchor and refuses when an anchor is not found exactly once, so a silent
miss cannot turn into a silent no-op.
"""

import io
import os
import sys

ROOT = r"F:\moonbit-hof-rs"
LOG = os.path.join(ROOT, "godot-mcp", "GAME-LOOP-LOG.md")
DECISIONS = os.path.join(ROOT, "DECISIONS.md")

ROW_16 = (
    "| 16 | Tower Defense | C# | 145（编辑器 14 / 游戏 131） | **145/145（100%）** | "
    "编辑器：`failed=1`（**声明的同名拒绝**，D-3）、`ok_effect_observed=1`、`ok_file_effect_observed=4`、`ok_no_effect_observed=8`；"
    "游戏：`failed=1`（**声明的边界调用**，`-32001`）、`ok_effect_observed=26`、`ok_file_effect_observed=78`、`ok_no_effect_observed=26` | "
    "**0 / 1**（**TD-1 会话**：全程对局那一段**漏了 `ForceTestState`** —— 三座塔建在上一段钉住的 `gold=0` 状态上、全部被 `no_gold` 拒绝，"
    "`StepFrames(4000)` 于是在无塔的场地上让 5 个敌人漏到终点、5 条命耗尽（`g53` 期望 3 实得 0、`g55` 期望 true 实得 false 等 **11 条同时 FAIL**）；"
    "另外**取证工具**自身 1 条（`R-1`，见下），**不算模块缺陷**） | `runs\\towerdefense\\td-task103-r3`（首轮 `-r1`，中间 `-r2` 未从模板重开） | "
    "第 16 个游戏。16×12 的 50 px 格点、**101 格无分支蛇形走廊**（路径由「从 S 出发、按右/下/左/上取第一个不是来路的路径格」的**确定性走法**从 ASCII 地图导出，"
    "Python 用同一走法重算 `PathHash`）、**整数行进**（每个敌人 `accum++`，攒满 `speed` 才进一格）、放塔（`-32000` 之外还有 `not_buildable`/`occupied`/`no_gold`/`out_of_bounds` 四种具名拒绝）、"
    "**切比雪夫射程 3 + 冷却 3 的塔**（取射程内**路径下标最大**的敌人）、三波（4/5/6 个，血 30/45/60）、生命与胜负。"
    "**像素差 31/145 非零**（编辑器 1/14、游戏 30/131），`user://` 五帧逐对 **185084 / 8356 / 3376 / 8133 px**、五个 sha **5/5 互不相同**；"
    "独立复算（`task102\\pixel_recompute.py` 逐调用对 + `task102\\frames_recompute.py` 保存帧 + 本轮 `recompute_readbacks.py`）**0 处不符**。"
    "断言 **77 PASS + 1 条声明的边界失败**（`-32001`）= 77 通过 / 0 失败。**Python 第二实现**（`make_session_towerdefense.py` 的 `TSim`）独立算出并作为断言字面量的有："
    "`MapHash=26299736`（由打印出来的 ASCII 重推）、`PathHash=-577587427` / `PathLength=101`（**重新走一遍**打印出来的地图）、"
    "逐步损伤后的 `EnemyList`、击杀后的 `Score`/`Gold`、漏掉后 `Wave` 与 `WaveLeftToSpawn` 的推进、"
    "以及**一整局**（三座塔、306 步、15 杀、0 漏、剩 5 条命、150 分、Wave=3）的每一步结果。"
    "与帧率无关的增量 `LastHookSteps`（`StepFrames(3)`→3）在十二帧之后仍是 3，而 `LastAutoSteps` 归 0；"
    "时钟是浮点累加器 `_autoAccum += delta*AutoClock`，`Elapsed` 是每帧 `+= delta` 的浮点秒表。"
    "多帧采样：冻结基线 12 帧（`Steps`/`EnemiesAlive`/`Gold`/`Lives`/`Won` 各只有 1 个值，`Elapsed`/`Ticks` 各 12 个不同值）对自动时钟 30 帧，"
    "并带**会 FAIL 的硬断言**（`Steps gt 0`、`EnemiesSpawned gt 0`、`AutoTicks gte 1` —— M3-4 的教训写进断言本身）。"
    "`e06` 同名批量被 `-32000` 拒绝（3 条 `conflicts`），`e05`/`e09` 的 sha `41de249a…`（860 B）**逐字节相同**；"
    "`project_build_csharp` exit 0（3796 ms）、`invalid_count=0`、`editor_get_errors count=0`；树里 279 个节点名 **0 个 `@` 开头**；"
    "声明的 `td_auto_step` 动作真的让 `Steps` 前进（`InputSteps=1`） |"
)

ROW_17 = (
    "| 17 | Missile Command | C# | 127（编辑器 14 / 游戏 113） | **127/127（100%）** | "
    "编辑器：`failed=1`（**声明的同名拒绝**，D-3）、`ok_effect_observed=1`、`ok_file_effect_observed=4`、`ok_no_effect_observed=8`；"
    "游戏：`failed=1`（**声明的边界调用**，`-32001`）、`ok_effect_observed=17`、`ok_file_effect_observed=74`、`ok_no_effect_observed=21` | "
    "**0 / 3**（**MC-1 载荷**：`PosAt` 是实例方法却被 `static AddMissiles` 调用 → `CS0120` → **C# 编译失败、脚本没挂上**，游戏退化成裸 `Node2D`；"
    "**MC-2 会话**：三条 `ProbeState` 断言写在探针循环**之后**，读到的是**最后**那次探针的状态（`g18b` 期望 `city` 实得 `ground`、`g19b` 期望 `battery` 实得 `ground`）；"
    "**TD-2 会话/证据**：TD 的 r2 **没有从模板重新实例化**，工程里已有三个静态节点 → 编辑器相首次同名批量被拒、像素列变 0/14。三条都已修并重跑） | "
    "`runs\\missilecommand\\mc-task103-r3`（首轮 `-r1`，`-r2` 已修 `PosAt` 但会话仍有 MC-2） | "
    "第 17 个游戏。800×600 场地、**6 座城市 + 3 个炮台（每台 10 发、每波补满）**、LCG 生成来袭弹（`seed=(seed*1103515245+12345) mod 2^31`，"
    "`x0=20+((seed>>16)%760)`、目标 6 城或地面）、**整数 floor 插值轨迹**（`x0 + DivFloor((tx-x0)*k, dur)`，C# 侧把 floor 显式写出来以便与 Python 的 `//` 逐位一致）、"
    "拦截弹从 x 最近的**有弹**炮台发射、爆炸半径 34 / 存在 8 步、**爆炸按下标顺序清掉半径内的来袭弹**、来袭弹落地按其目标点 28 px 摧毁城市、波次与得分（25/杀、每存活城市 100）。"
    "**像素差 21/127 非零**（编辑器 1/14、游戏 20/113），`user://` 五帧逐对 **15823 / 13578 / 4370 / 346 px**、五个 sha **5/5 互不相同**；"
    "独立复算（`task102\\pixel_recompute.py` + `task102\\frames_recompute.py` + 本轮 `recompute_readbacks.py`）**0 处不符**。"
    "断言 **73 PASS + 1 条声明的边界失败**（`-32001`）= 73 通过 / 0 失败。**Python 第二实现**（`make_session_missilecommand.py` 的 `MSim`）独立算出并作为断言字面量的有："
    "初始 `CityList`/`AmmoList`/`CityHash=29583456`/`WorldHash=852442047`、定盘天幕逐步的 `IncomingList` 与 `ExplosionList`、"
    "**一次爆炸的覆盖判定**（半径内的被打掉、半径外的活下来，`Destroyed`/`Score` 同步）、"
    "**带提前量的拦截**（在 Python 里把「拦截弹到达所需步数」与「来袭弹走到该点所需步数」迭代到不动点，"
    "得到 `InterceptorList=400,586,312,542,0,8,400,586`、8 步后爆炸点与来袭弹位置**逐位相同**→ 命中、`Leaked=0`、随后该波清算 `Wave` 推进并补满弹药）、"
    "一城被毁的 `CityList=1,1,0,1,1,1`、六城尽失的败局、以及**末波清空即胜**（`maxwave=1`，`Score=500`、`Won`/`GameOver`=true）。"
    "与帧率无关的增量 `LastHookSteps` 在十二帧之后仍是 3，而 `LastAutoSteps` 归 0；时钟是浮点累加器；`Elapsed` 是浮点秒表。"
    "多帧采样：冻结基线 12 帧对自动时钟 30 帧，带**会 FAIL 的硬断言**（`Steps gt 0`、`Spawned gt 0`、`AutoTicks gte 1`）。"
    "`e06` 同名批量被 `-32000` 拒绝，`project_build_csharp` exit 0（3815 ms）、`invalid_count=0`、`editor_get_errors count=0`；"
    "树里 270 个节点名 **0 个 `@` 开头**；声明的 `mc_auto_fire` 动作真的发了一发（`InputShots=1`、`Fired=1`、`Ammo` 29） |"
)

TASK103_SECTION = """
### TASK-103 记录（2026-09-27）

1. **工具缺陷 X-1 修在根上并重建两变体**（本轮唯一一次动 `modules\\mcp_server`）。现场是 TASK-102 的 `m3-task102-r1/g115-runtime-overlay`：
   脚本能编译、执行时调了 C# 拼写的 `addChild`，VM 中止该帧、只把 `SCRIPT ERROR` 打到引擎 stderr，而工具回
   `ok` + `{"result":null,"result_type":"Nil"}` —— 没有错误码、没有消息、没有建议，「脚本炸了」与「脚本跑了但没有可见副作用」在答复里无法区分。
   修法用的是**引擎自己的错误处理器**（解析捕获已经在用的那个钩子）：`GDScriptFunction::call()` 把中止的帧
   经 `_err_print_error(..., ERR_HANDLER_SCRIPT)` 报出来（`gdscript_vm.cpp:3988`，在 `#ifdef DEBUG_ENABLED` 里，而本模块所有门跑的都是
   `target=editor` → 该宏生效）。窗口恰好是一次 `Callable::callp`，所以窗口里每一条 `ERR_HANDLER_SCRIPT` 都是这次调用造成的；
   用 `ERR_HANDLER_SCRIPT`（而不是 `ERR_HANDLER_ERROR`）正是为了不把脚本自己的 `push_error()` 算成失败。
   * 错误码 **`-32000`（`tool_state`）**，不是 `-32602`（脚本**编译通过**了，语法没问题）也不是 `-32603`（不是本模块坏了）；
     `data.script_error` 带引擎原文、`code` 的行号、生成源行号、脚本路径、被点名的 GDScript 函数、错误条数与全部消息，`data.suggestion` 给出改法；
     **列号如实报为 `null`** —— 引擎给处理器的只有行号。
   * 生成脚本的身份**按 GDScript 自己的造法重建**（`gdscript://<instance id>.gd`，`gdscript.cpp:1337`），而不是读
     `Script::get_path()`：那是 `Resource::get_path()`，答的是**路径缓存**、对未从资源加载的脚本恒为空 —— 实测运行时错误点名
     `gdscript://-9223371484028730203.gd` 而 `get_path()` 答 `""`。答复里两个字符串都给，比较可审计。
   * 成功路径：`result` 为 `null`/`Nil` 时带 `note`（没有 `return` 的脚本与全是空操作的脚本答的都是 null）。
   * 描述与 C++ 注册字面量走生成器的 **append-only override**（键 `execute_game_script`）重新生成；契约**六项形状量一字未变**
     （`count=177`、`added_count=6`、`generator_version=1.22.0`、编辑器可见 154、游戏可见 73、**幂等**：连续两次生成同为
     sha256 `bd68e8047…`），契约文件 151 367 B / `64ddce9f…` → 153 330 B / `bd68e804…`，`_meta.overrides` 仍 34（改的是既有条目，不是新增）。
   * doctest：新增一例把三种情形分开钉住（解析失败 `-32602`；运行期错误 `-32000` + `data.script_error` 与它的行映射；成功有值 / 成功无值后者带 `note`），
     外加一条 `push_error()` 控制（**不得**变成拒绝）；TASK-090 的挂载用例在自己的失败路径上改为断言结构化拒绝。模块用例 **156 → 157**。
   * **最小同批复现（修前 / 修后并列）**：同一份六调用会话**逐字不改**跑两次 ——
     `runs\\match3\\task103-x1-before` 的 `g01` 回 `ok` + `{"result":null,"result_type":"Nil"}`（无码无消息）；
     `runs\\match3\\task103-x1-after` 的 `g01` 回 **`-32000`** + `data.script_error`（`line=7`、`generated_line=10`、`function=_mcp_execute`、
     `script_path=gdscript://-9223371989626911104.gd`、`in_generated_body=true`、`error_count=1`）+ `data.suggestion`。
     同一批里的正控 `g03`（把 `addChild` 改成 `add_child`）两次都回 `"overlay added"`（**没有过度报错**）；`g05`（无 `return` 的脚本）修后带 `note`；
     `g06`（解析失败）两次都是 `-32602` 且 `parse_error` 逐字未变；引擎 stderr 里那条 `SCRIPT ERROR` **仍然在**（处理器是纯追加的）。
   * **错误也进 trace**：`task103-x1-after` 的调用行（`seq=1`）带 `error_code=-32000`、`error_message` 与整段 `error_data_json`。
2. **第 16、17 款交付**：台账第 16、17 行来自它们自己那一轮的产物（`runs\\towerdefense\\td-task103-r3\\report.json`、
   `runs\\missilecommand\\mc-task103-r3\\report.json`）。两款 `facts_complete` 都是 **100%**（145/145、127/127）。
   两款每一轮的非 `ok` 判定都是**声明过的**：编辑器相那一次同名批量（`-32000`）与一条故意打在不存在属性上的边界断言（`-32001`）。
3. **缺陷清单（分两栏）**：
   * **工具缺陷（`modules\\mcp_server`）：0 条**。本轮唯一的模块改动是 A 段**主动**修 X-1（不是新发现），修完两变体重建、十道门重跑。
   * **游戏或驱动缺陷：4 条**
     | id | 层 | 现象（证据） | 根因 | 处置 → 重跑结果 |
     |---|---|---|---|---|
     | **MC-1** | Missile Command **载荷** | r1 的 `g02-assert-field-w` 回 `-32001`（`Property 'FieldW' on node '/root/Main' not found`），`g12-readback-t0` 回 `-32000`「`Nonexistent function 'Dump' in base 'Node2D'`」 | `PosAt` 是实例方法，却被 `static AddMissiles` 调用 → `CS0120`；`project_build_csharp` exit 1、`project_validate_scripts invalid_count=1`，**脚本没挂上**，根节点退化成裸 `Node2D` | `PosAt` 改 `static`（它本来就不碰实例状态）；r2/r3 编译 exit 0、脚本挂上、全部断言通过。**这条正是 X-1 修好之后第一次受益**：旧行为下 `Dump` 会静默回 `ok`+`null`，人只会看到「断言全不对」而不知道脚本根本没挂上 |
     | **MC-2** | Missile Command **会话** | r2 的 `g18b-assert-probe-state` 期望 `city` 实得 `ground`、`g19b` 期望 `battery` 实得 `ground`，而同刻 `g18a`/`g19a`（`ProbeValue`）全 PASS | 三条 `ProbeState` 断言写在探针循环**之后**，读到的是**最后**那次探针（(400,300)）的状态 —— 与 PL-3 / K-1 / M1 同一类：期望值必须引用它所断言的那**一刻** | 每次探针后立刻断言它的两个属性；r3 全 PASS |
     | **TD-1** | Tower Defense **会话** | r1 的 `g53-assert-towers` 期望 3 实得 0、`g53a-assert-gold` 期望 850 实得 0、`g55-assert-won` 期望 true 实得 false …… **11 条同时 FAIL**，`Steps` 实得 544、`Lives` 实得 0 | 「一整局」那一段**漏了 `ForceTestState` 调用**：三座塔建在上一段钉住的 `gold=0` 状态上，全被 `no_gold` 拒绝，`StepFrames(4000)` 于是在无塔场地上把 5 条命跑光 | 补上 `g49-play-setup` 的 force 调用；r2/r3 全 PASS（`TowersPlaced=3`、`Gold=850`、`Won=true`、`Steps=306`、`Killed=15`、`Leaked=0`） |
     | **TD-2** | Tower Defense **会话 / 证据设计** | r2 的编辑器相像素列 **0/14 非零**，而 r1 是 1/14（`editor_add_nodes_batch` 213 012 px） | r2 **没有从模板重新实例化**：工程里已有上一轮建的三个静态节点，首次同名批量被 `-32000` 拒绝，于是「一次批量建好三个静态节点」这一步在本轮**根本没有发生** | 归档 + 重新实例化后重跑（先写 sha256 清单再 `Move-Item`，全程零删除）；r3 编辑器相像素 1/14 非零（213 012 px） |
   * **取证工具自身 1 条（`R-1`，**不是**模块缺陷、也不是游戏缺陷）**：`recompute_readbacks.py` 第一版把 `Dump()` 行里 `last=<LastEvent>` 的片段也当成了字段，
     而 `StepFrames` 的 readback 恰好含 `incoming=0` —— 它覆盖了真正的 `incoming=<列表>`，解析器随后在 `m[1]` 上抛 `IndexError`。
     修法：只取 `last=` 之前的部分（`dump_fields`），并让列表解析对字段数做断言；修后两款各 **0 处不符**。
4. **「像素差 + 独立复算」两款的真实数值**：Tower Defense **31/145**（编辑器 1/14、游戏 30/131），
   `user://` 五帧 **185084 / 8356 / 3376 / 8133 px**；Missile Command **21/127**（1/14、20/113），五帧 **15823 / 13578 / 4370 / 346 px**。
   两款的 `recomputed-vs-trace mismatches` 都是 `none`，保存帧 sha 与 `report.json` 逐值一致、**5/5 互不相同**，
   帧链逐对独立复算 **0 处分歧**；`recompute_readbacks.py` 还**只从打印出来的** `Dump()` 重算哈希
   （TD 的 `MapHash` 由 ASCII 重推、`PathHash` 由**重新走一遍**导出的路径重推；MC 的 `CityHash`/`WorldHash` 由打印出来的城市位、两张导弹表、爆炸表与 `score`/`wave`/`steps` 重推），
   并把生成器记录的每一条期望字面量与响应里**实际回报的 `expected`** 逐条对齐：TD **75/75 + 1 条声明边界**、MC **71/71 + 1 条声明边界**，合计 **0 处不符**。
5. **时钟与单写者（继承 G1/F-1/M3-4）**：两款都是浮点累加器（`_autoAccum += delta * rate`），`Elapsed` 是每帧 `+= delta` 的浮点秒表；
   每款各有 `LastHookSteps`（钩子）与 `LastAutoSteps`（每帧时钟）**两个**属性，且都在采样里出现过；
   两款都在时钟跑过 12 帧之后断言 `LastHookSteps` **仍是钩子写下的那个值**。
   **M3-4 的教训写进了断言本身**：两款的采样后面都跟着 `Steps gt 0` / `EnemiesSpawned(Spawned) gt 0` / `AutoTicks gte 1` 三条**会 FAIL 的硬断言**，
   所以「时钟在走而世界冻住」不再是采样里的一串常数，而是一条红。
6. **模板增补（写给第 18 款）**：①**每一段测试都必须从它自己的 `ForceTestState` 开始** —— TD-1 的成因是「上一段钉住的状态」被下一段继承；
   ②**重跑必须从模板重新实例化**（先写 sha256 清单再移动工程），否则编辑器相的第一步会在上一轮的工程上被同名拒绝（TD-2）；
   ③**载荷里的 `static` 方法只能调 `static` 方法** —— MC-1 的 `CS0120` 让整份脚本没挂上，而这类失败在修好 X-1 之后**第一次**由工具自己说了出来；
   ④**断言要紧挨着它引用的那一刻**（MC-2，与 PL-3/K-1/M1 同源）；⑤**取证脚本自己也要能读错**：`last=` 之后的 `key=value` 片段会覆盖真字段（R-1）。
7. **门跑器**：本轮**改了模块**（X-1），因此**重建两个变体 + 十道门全绿 + `accept_m1` 22/22**都跑了，真实退出码与逐门结果见
   `recovery\\reports\\TASK-103-REPORT.md` §C 与 `runs\\gates\\task103\\summary.txt`。引擎仓提交 `1c7f5c07a1`（模块提交），
   两变体都在该提交之后重建，锚点自报 `4.8.dev.mono.custom_build.1c7f5c07a` / `4.8.dev.custom_build.1c7f5c07a`。
8. **`--import` 的关机期访问违例本轮 0 次**：TD 的 r1/r2/r3 与 MC 的 r1/r2/r3 六次导入全部 `IMPORT_EXIT=0`、`import.stderr.txt` 0 字节。累计口径 **3/34**（待办 2 不变）。

"""

DECISION_151 = """
## D151 — TASK-103：工具缺陷 X-1（GDScript 运行期错误没有结构化错误）修在根上并重建两变体；第 16、17 款 C# 小游戏（Tower Defense / Missile Command）交付；四条缺陷（工具 0 / 游戏或驱动 4）在各自首轮被照出来并重跑

* **日期**：2026-09-27
* **触发问题**：两件事。①TASK-102 只记录未修的 **X-1**：`running_game_execute_gdscript` 在**脚本运行期报错**时回 `ok` + `{"result":null}`，没有错误码、没有消息，真 `SCRIPT ERROR` 只在引擎 stderr —— 那一轮 M3-3 就是被这条**半掩**住的（工具说成功，真正抓到它的是像素差 0 与场景树里没有那个节点）。②D138 的「至少 20 个经典小游戏、全部 C#」推进到第 16、17 款，并要检验固化模板在**两种新形态**上是否仍然够用：网格塔防（放塔 / 射程 / 冷却 / 波次）与弹幕拦截（来袭弹 / 拦截弹 / 爆炸覆盖 / 城市存活）。

* **考虑的选项**：
  1. **X-1 只改文档（把「`ok` 不等于脚本执行成功」写进描述）**：不改模块就不必重建两变体、不必跑十道门，成本最低。但下一轮的同款失败仍然只能靠**别的通道**（像素差 / 场景树）间接发现，而 X-1 的教训恰恰是「半掩的错误最危险」。**否**。
  2. **X-1 用 `-32602` 报告运行期错误**（与解析失败同一个码，消费者只需认一个码）：省一个分支，但会让调用者去修**语法**，而它的语法完全正确 —— 错因被指向错误的方向。**否**。
  3. **X-1 用 `-32603`（`internal`）**：语义是「本模块坏了」，而事实是**调用者的代码**失败、模块正确地观察到了它。**否**。
  4. **X-1 靠包裹脚本、把错误吞进 try 之类的宿主结构**：GDScript **没有异常**，而且任何「安装一个吞掉错误打印的处理」都会**削弱引擎自己的诊断**（stderr 上那条 `SCRIPT ERROR` 是排查时唯一的第一手材料）。**否** —— 只做**纯追加**的捕获（引擎照常打印，我们额外抄一份）。
  5. **弹幕拦截用浮点物理 / 用真随机**：省事，但「爆炸在半径内打掉了哪几发」「若干步之后来袭弹在哪」都会变成容差而不是确切值，D138 要的可复算证据会被降级成形容词。**否**。
  6. **把「一整局」交给自动时钟跑、不写脚本计划**：TD 的一整局是**确定性规则下的确定序列**（三座塔、306 步），用 `StepFrames(4000)` 一次调用跑完并把每一步的结果交给第二实现核对，比用钟表时间跑更精确也更快。**取此**。

* **最终选择**：
  * **X-1 修在根上，用引擎自己的错误处理器**（与解析捕获同一钩子）：`GDScriptFunction::call()` 把中止的帧经 `_err_print_error(..., ERR_HANDLER_SCRIPT)` 报出来（`gdscript_vm.cpp:3988`）；窗口恰好一次 `Callable::callp`，因此窗口里每条 `ERR_HANDLER_SCRIPT` 都是这次调用造成的；用 `ERR_HANDLER_SCRIPT` 而不是 `ERR_HANDLER_ERROR`，正是为了**不**把脚本自己的 `push_error()` 算成失败（doctest 里有一条控制专门钉这一点）。
  * **错误码取 `-32000`（`tool_state`）**：本模块既有的「调用形式没问题、是这次执行没成」的约定（`not_implemented` / `no_scene` 同为 `-32000`，且 GDR-14 要求它带 `data.suggestion`）。理由逐条写进了源码注释与描述：`-32602` 意味着**参数/语法**有问题（脚本编译通过了），`-32603` 意味着**模块**坏了（是调用者的代码失败了）。
  * `data.script_error` 带引擎原文、`code` 的行号、生成源行号、脚本路径、被点名的 GDScript 函数、错误条数与全部消息；**列号如实为 `null`**（引擎给处理器的只有行）；`data.suggestion` 给出改法；同一批事实随失败的 `data` 进 trace 的调用行（`error_data_json`）。
  * **生成脚本的身份按 GDScript 自己的造法重建**（`gdscript://<instance id>.gd`，`gdscript.cpp:1337`），不读 `Script::get_path()` —— 后者是 `Resource::get_path()`、答的是**路径缓存**、对未从资源加载的脚本恒为空（本轮实测：运行时错误点名 `gdscript://-9223371484028730203.gd` 而 `get_path()` 答 `""`）。答复里两个字符串都给，比较可审计。
  * **成功但无副作用要能被区分**：`result` 为 `null`/`Nil` 时响应带 `note`。摆在结果对象里而不是 `error.data` 里，因为成功路径**没有** JSON-RPC 的 `error.data`。
  * 契约改动走生成器的 **append-only override**（键 `execute_game_script`：TASK-090 的句子逐字保留在前，本轮句子追加在后），重新生成契约与 C++ 注册字面量；**六项形状量一字未变**（177/6/1.22.0/154/73/幂等），改动登记进 `REBUILT-2C-MANIFEST.md` 的 2c-12。
  * **两款游戏都从模板实例化、内容全部由 MCP 调用写成**；两款都带一份**从规则重写的 Python 第二实现**（`make_session_towerdefense.py` 的 `TSim`、`make_session_missilecommand.py` 的 `MSim`），会话里每一个期望字面量都取自它们。
  * **Tower Defense 是整数网格塔防**：40×30 换成 16×12 的 50 px 格点、**101 格无分支蛇形走廊**，路径由「从 S 出发按右/下/左/上取第一个不是来路的路径格」的确定性走法从 ASCII 地图导出（Python 用同一走法重算 `PathHash`）；塔取切比雪夫距离 ≤3 内**路径下标最大**的敌人、冷却 3；三波 4/5/6 个、血 30/45/60。
  * **Missile Command 是整数弹道拦截**：`x0 + DivFloor((tx-x0)*k, dur)`（C# 侧把 floor 明确写出来，与 Python 的 `//` 逐位一致）；拦截弹从 x 最近的**有弹**炮台发射；爆炸半径 34、存在 8 步、按下标顺序清掉半径内的来袭弹；来袭弹落地按其目标点 28 px 摧毁城市。**「带提前量的一发」在 Python 里迭代到不动点**（拦截弹到达所需步数 == 来袭弹走到该点所需步数），所以那一发命中是算出来的而不是碰出来的。

* **选择理由**：
  * X-1 的修法**不削弱引擎诊断**（纯追加的 handler，stderr 那条 `SCRIPT ERROR` 一字不少），并且**立刻在下一款游戏上见效**：第 17 款的 MC-1（`static` 调实例方法导致 C# 编译失败、脚本根本没挂上）第一次由**工具自己**说出来（`Nonexistent function 'Dump' in base 'Node2D'` + 结构化 `-32000`），而旧行为下它只会是一串「断言全不对」。
  * 码的选择是**语义**而不是省事：`-32602`/`-32603` 都会把调用者指向错误的方向；`-32000` 是既有约定里唯一说「调用没问题、这次执行没成」的那个。
  * 两款的「可复算」不是声明：TD 的整局（306 步、15 杀、0 漏、5 命、150 分、Wave 3）与 MC 的每一次爆炸覆盖、每一发提前量拦截，都是**第二实现先算出来、再作为断言字面量**的；事后复算脚本**不看 `report.json`、不看断言助手、不看 C#**，只把载荷打印出来的 `Dump()` 拿来重算哈希（TD 的 `MapHash`/`PathHash`、MC 的 `CityHash`/`WorldHash`），两款 **0 处不符**。
  * 四条缺陷各自的**发现通道**互不重叠：TD-1 是**断言整片失败**（11 条同时红）、TD-2 是**像素列从 1/14 掉到 0/14**、MC-1 是**编辑器相的红**（`exit_code=1` + `invalid_count=1` → 游戏退化）、MC-2 是**两条同刻断言互相矛盾**（`ProbeValue` 对而 `ProbeState` 错）。没有一条能单独覆盖全部。

* **本轮缺陷（详见 `GAME-LOOP-LOG.md` 的 TASK-103 记录节）**：
  | id | 层 | 现象（证据） | 根因 | 处置 → 重跑结果 |
  |---|---|---|---|---|
  | **MC-1** | Missile Command 载荷 | r1 `g02` 回 `-32001`、`g12` 回 `-32000`「`Nonexistent function 'Dump' in base 'Node2D'`」 | `PosAt` 是实例方法却被 `static AddMissiles` 调用 → `CS0120` → `project_build_csharp` exit 1 → **脚本没挂上**、根节点退化成裸 `Node2D` | `PosAt` 改 `static`；r2/r3 编译 exit 0、全部断言通过 |
  | **MC-2** | Missile Command 会话 | r2 `g18b` 期望 `city` 实得 `ground`、`g19b` 期望 `battery` 实得 `ground`，同刻 `ProbeValue` 全 PASS | 三条 `ProbeState` 断言写在探针循环**之后**，读的是**最后**那次探针的状态（与 PL-3/K-1/M1 同源） | 每次探针后立刻断言它的两个属性；r3 全 PASS |
  | **TD-1** | Tower Defense 会话 | r1 的 11 条断言同时 FAIL（`TowersPlaced` 期望 3 实得 0、`Won` 期望 true 实得 false、`Steps` 实得 544、`Lives` 实得 0） | 「一整局」那一段**漏了 `ForceTestState`**：三座塔建在上一段钉住的 `gold=0` 上、全被 `no_gold` 拒绝 | 补上 force 调用；r2/r3 全 PASS |
  | **TD-2** | Tower Defense 会话 / 证据设计 | r2 编辑器相像素列 **0/14**，而 r1 是 1/14（213 012 px） | r2 **没有从模板重新实例化**，工程里已有上一轮的三个静态节点 → 首次同名批量被 `-32000` 拒绝 | 归档（先写 sha256 清单再移动）+ 重新实例化后重跑；r3 恢复 1/14 |
  | **R-1（取证工具，不算模块缺陷）** | `recovery\\work\\task103\\recompute_readbacks.py` | 复算脚本在 MC 上抛 `IndexError` | 它把 `Dump()` 行里 `last=<LastEvent>` 的片段也当字段，而 `StepFrames` 的 readback 含 `incoming=0`，覆盖了真正的列表 | 只取 `last=` 之前的部分并断言列表字段数；修后两款 0 处不符 |

* **预期影响与回滚点**：
  * 模板再添五条（写给第 18 款）：**每段测试都从自己的 `ForceTestState` 开始**（TD-1）；**重跑必须从模板重新实例化**（TD-2）；**`static` 只能调 `static`**（MC-1）；**断言紧挨着它引用的那一刻**（MC-2，与 PL-3/K-1/M1 同源）；**取证脚本自己要能读错**（R-1）。
  * X-1 的接线只在 `running_game_execute_gdscript` 的**执行路径**上新增一段判定与两个响应字段：`ok` 的语义**没有放宽**（原先能读到 `result` 的调用仍然读到），新增的是**原先错报为 `ok` 的那一类失败**与**成功但无值时的 note**。回滚点是引擎仓提交 `1c7f5c07a1` 的前一个提交 `e041cae270`（重新 checkout 并重建两变体即可）。
  * 契约与注册字面量是**同一个生成器的同一份输出**（append-only override），回滚只需把 override 的 `value` 恢复并重跑两次生成器（幂等，第二次同 sha256）。
  * 两款的工程、C# 载荷、会话、会话生成器、Python 第二实现、复算脚本全部入库（`tools\\sessions\\{towerdefense,missilecommand}`、`recovery\\work\\task103\\`），任何一处都可逐字重生成；回滚点就是删掉这两款并把台账两行撤掉。
  * **遗留（不阻塞）**：①`--import` 的关机期访问违例仍未结案（本轮 6 次导入 0 次复现，累计 3/34）；②TD 的塔**没有升级/出售**、MC 的炮台**不能选择**，两款都是各自经典规则的最小完整子集；③`ForceTestState` 仍允许钉出游戏本身到不了的状态（B-3 的成因），本轮以「会话不这么钉」处置，未在载荷里加防护；④X-1 的运行期捕获在 `target=template_release` 下**看不到任何错误**（`gdscript_vm.cpp` 的报错块在 `#ifdef DEBUG_ENABLED` 里）—— 该边界写进了工具注释与描述，本模块所有门跑的都是 `target=editor`。
"""


def edit(path, replacements):
    with io.open(path, encoding="utf-8", newline="") as handle:
        text = handle.read()
    for anchor, replacement, count in replacements:
        found = text.count(anchor)
        if found != count:
            sys.exit("FATAL: anchor appears %d time(s), expected %d: %r" % (found, count, anchor[:80]))
        text = text.replace(anchor, replacement)
    with io.open(path, "w", encoding="utf-8", newline="") as handle:
        handle.write(text)
    print("rewrote %s (%d bytes)" % (path, len(text.encode("utf-8"))))


def main():
    # --- GAME-LOOP-LOG.md -----------------------------------------------------
    with io.open(LOG, encoding="utf-8", newline="") as handle:
        text = handle.read()
    marker = "\n\n---\n\n## 缺陷登记（跨轮累计）"
    if text.count(marker) != 1:
        sys.exit("FATAL: the ledger table's closing marker is not unique")
    text = text.replace(marker, "\n" + ROW_16 + "\n" + ROW_17 + marker)
    todo_marker = "\n## 待办\n"
    if text.count(todo_marker) != 1:
        sys.exit("FATAL: the '## 待办' marker is not unique")
    text = text.replace(todo_marker, TASK103_SECTION + todo_marker, 1)
    # X-1's own row in the tool-defect table: it now has a fix.
    old_status = "**只记录，未修**。可复现配方"
    if text.count(old_status) != 1:
        sys.exit("FATAL: the X-1 status cell is not unique")
    text = text.replace(old_status, "**已修（TASK-103，见「TASK-103 记录」第 1 条）。** 原状态与可复现配方")
    old_tail = "必须配像素差与场景树证据（X-1）"
    if text.count(old_tail) != 1:
        sys.exit("FATAL: the X-1 consequence sentence is not unique")
    text = text.replace(old_tail, old_tail + "  **TASK-103 已修**：运行期错误回 `-32000` + `data.script_error` + `data.suggestion`，"
                                             "成功但无返回值带 `note`，错误同时进 trace 的调用行；两变体已在该提交后重建、十道门重跑。")
    with io.open(LOG, "w", encoding="utf-8", newline="") as handle:
        handle.write(text)
    print("rewrote %s (%d bytes)" % (LOG, len(text.encode("utf-8"))))

    # --- DECISIONS.md ---------------------------------------------------------
    with io.open(DECISIONS, encoding="utf-8", newline="") as handle:
        decisions = handle.read()
    decisions = decisions.rstrip("\n") + "\n" + DECISION_151
    with io.open(DECISIONS, "w", encoding="utf-8", newline="") as handle:
        handle.write(decisions)
    print("appended D151 to %s (%d bytes)" % (DECISIONS, len(decisions.encode("utf-8"))))


if __name__ == "__main__":
    main()
