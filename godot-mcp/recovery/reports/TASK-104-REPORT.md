# TASK-104 — 第 18、19、20 款 C# 小游戏（R-Type / Puzzle Bobble / Lunar Lander）交付，D138 的「至少 20 款」收口；一条会话缺陷 RT-1 在首轮被照出来并重跑；模块零改动，收尾走免跑判定

* 执行者：游戏/工具工程师（本会话，**有写权限，按用户指令不再委派**）
* 主仓：`F:\moonbit-hof-rs`（分支 `master`）
* 引擎仓：`F:\moonbit-hof-rs\godot-mcp\godot`（分支 `feature/mcp-server-module-rebuild`）
  * **本轮没有改动引擎仓任何一个字节**：HEAD 仍是 TASK-103 的 `1f9d0cb1c9`，工作树**空**，
    且与 `refs/remotes/origin/feature/mcp-server-module-rebuild` **同级**（fork 已在 `1f9d0cb1c9`，无需 push）
* 脚本 / 会话 / 证据：`godot-mcp\recovery\work\task104\`、`godot-mcp\runs\`、`godot-mcp\tools\sessions\{rtype,puzzlebobble,lunarlander}\`
* 报告：本文件。返回值 ≤ 10 行见文末 §G。

---

## 0. 结论表（每行一句话）

| 段 | 要求 | 结论 | 关键证据 |
|---|---|---|---|
| **A①** | **#18 R-Type 横版射击**（C#，只用 MCP 调用开发）：玩家移动、子弹、敌机波次与**编队**、敌弹、生命与得分 | **做完，首轮照出 1 条会话缺陷（RT-1）并重跑 r2 后全绿。** 223 次调用（编辑器 14 / 游戏 209），`facts_complete` **223/223（100%）**；断言 **101 PASS / 0 FAIL** = 99 条带属性的 node-state ＋ 1 条屏幕文本 ＋ 1 条场景自带断言，**另有 1 条声明的边界失败**（`-32001`，不计入 PASS）；像素差 **87/223 非零**（编辑器 1/14、游戏 86/209），`user://` 四帧逐对 **2069 / 7095 / 7547 px**、**4/4 互不相同**；独立复算 **0 处不符**；`project_build_csharp` exit 0（4266 ms）、`invalid_count=0`；三次场景树读取共 **214 个节点名 0 个 `@` 开头** | `runs\rtype\rt-task104-r2`（首轮 `rt-task104-r1`）、`logs\assert-rtype.txt`、`logs\pixel-rtype.txt`、`logs\frames-rtype.txt`、`logs\recompute-rtype.txt`、`logs\facts-rtype.txt` |
| **A②** | **#19 Puzzle Bobble**：方形泡泡网格、发射与吸附、同色三连消除、悬空掉落、连锁、失败线 | **做完，首轮一次通过，零缺陷。** 157 次调用（14 / 143），`facts_complete` **157/157（100%）**；断言 **87 PASS / 0 FAIL** = 85 条带属性的 node-state ＋ 1 条屏幕文本 ＋ 1 条场景自带断言，**另有 1 条声明的边界失败**（`-32001`，不计入 PASS）；像素差 **29/157 非零**（1/14、28/143），四帧逐对 **53444 / 18251 / 2929 px**、**4/4 互不相同**；独立复算 **0 处不符**（含**初始棋盘本身**由 LCG + 稳定循环重算）；`project_build_csharp` exit 0（2489 ms）、`invalid_count=0`；三次场景树读取共 **214 个节点名 0 个 `@` 开头** | `runs\puzzlebobble\pb-task104-r1`、`logs\assert-puzzlebobble.txt`、`logs\pixel-puzzlebobble.txt`、`logs\frames-puzzlebobble.txt`、`logs\recompute-puzzlebobble.txt`、`logs\facts-puzzlebobble.txt` |
| **A③** | **#20 Lunar Lander**：重力与推力、燃料、旋转、着陆台判定（速度/角度）、剩余燃料得分 | **做完，首轮一次通过，零缺陷。** 230 次调用（14 / 216），`facts_complete` **230/230（100%）**；断言 **150 PASS / 0 FAIL** = 148 条带属性的 node-state ＋ 1 条屏幕文本 ＋ 1 条场景自带断言，**另有 1 条声明的边界失败**（`-32001`，不计入 PASS）；像素差 **41/230 非零**（1/14、40/216），四帧逐对 **6798 / 1117 / 6885 px**、**4/4 互不相同**；独立复算 **0 处不符**，含**整条 35 步积分轨迹按 `call-index.txt` 顺序重放、17 个检查点**；`project_build_csharp` exit 0（3782 ms）、`invalid_count=0`；三次场景树读取共 **136 个节点名 0 个 `@` 开头** | `runs\lunarlander\ll-task104-r1`、`logs\assert-lunarlander.txt`、`logs\pixel-lunarlander.txt`、`logs\frames-lunarlander.txt`、`logs\recompute-lunarlander.txt`、`logs\facts-lunarlander.txt` |
| **B** | 达 20 款后在台账里做**里程碑小结**（每款一行、20 款一览、工具缺陷累计清单与修复轮次、像素证据与独立复算覆盖率、`--import` 累计），并**为独立验收准备入口** | **做完。** `GAME-LOOP-LOG.md` 新增 `## 里程碑：20 款（TASK-104 收口）`：20 款一览表（含第 18/19/20 行）、合计 **2 554 次调用**（编辑器 303 / 游戏 2 251，两列分别逐行相加得出）、`facts_complete` **20/20 款 100%**、**像素证据 20/20 可得且非零**、**独立复算 20/20、合计 0 处不符**、工具缺陷累计清单（D-3/D-1/D-2/G-1/X-1/X-2）与修复轮次、`--import` 累计、以及**验收要读的 9 类文件 + 10 条只读命令 + 4 条应当主动构造的反例** | `GAME-LOOP-LOG.md` 的 `### TASK-104 记录` 与 `## 里程碑：20 款（TASK-104 收口）` |
| **C** | 改模块 → 重建两变体 + 十道门全绿 + `accept_m1` 22/22 + push 到 fork；**未改模块则用免跑判定并如实说明**；主仓提交；报告含两仓 `git log --oneline -8` 与 `git status --short` | **未改模块，走免跑判定，如实说明：十道门与 `accept_m1` 本轮未重跑。** 引擎仓工作树**空**、HEAD 未移动；`tools\run_gates.ps1 -Tag task104` 自判 **`ANCHOR_STRUCTURAL_EQUIVALENT` + `SKIP_REBUILD` + `GATES_SKIPPED=1`**（理由：锚点与 HEAD 之间那 1 个文件是非编译的 `.md`）。主仓提交见 §F；两仓日志与状态逐字见 §F（取自 `logs\final-snapshot.txt`）。**没有 push**：fork 上已是 `1f9d0cb1c9`，本地与之同级 | `runs\gates\task104\summary.txt`、`logs\final-snapshot.txt`、§C、§F |

---

## A. 三款游戏的形态与开发方式

三款都从**模板实例化**（`tools\new_game.ps1`），**游戏内容全部由 MCP 调用写成**：
`project_edit_script`（C# 载荷替换模板桩）、`editor_add_nodes_batch`（三个静态节点一次建好）、
`editor_add_input_action`（声明一个动作）、`editor_save_scene`、`project_build_csharp`、`project_validate_scripts`；
游戏相全部是 `running_game_*`。场景里**只有** `Background` / `Hud` / `Status`，其余全部**运行期新建**。

| 游戏 | 场景里的静态节点 | 运行期新建的东西 | 声明并验证的动作 |
|---|---|---|---|
| R-Type | `Background` / `Hud` / `Status` | 48 颗星 + 飞船 + 16 个敌机池 + 12 个玩家弹池 + 24 个敌弹池 = **101 个节点** | `rt_fire`（Space，按**按下沿**只发一发，`InputShots=1`） |
| Puzzle Bobble | `Background` / `Hud` / `Status` | **96 个格位** + 失败线 + 发射台 + 下一颗 + 弹丸 + 发射条 = **101 个节点** | `pb_shoot`（Space，按按下沿只发一发，`InputShots=1`） |
| Lunar Lander | `Background` / `Hud` / `Status` | 56 颗星 + 地面 + 3 个着陆台 + 着陆器 + 火焰 = **62 个节点** | `ll_thrust`（Space，按按下沿只点一次火，`InputThrusts=1`） |

三款都**故意重跑同名批量**（`e06`）：`-32000` + `data.conflicts` **3 条**（`Background`/`Hud`/`Status`），
且 `e05` 与 `e09` 读回的 `.tscn` **逐字节相同**：

| 游戏 | `e05`/`e09` sha256[0:16] | 大小 | `conflicts` |
|---|---|---|---|
| R-Type | `0494b8a022a3c3aa` | 850 B | 3（`Background`/`Hud`/`Status`） |
| Puzzle Bobble | `3723211c1a40e605` | 868 B | 3 |
| Lunar Lander | `50ec3aba6522a795` | 844 B | 3 |

**这三条 sha 同时是工程文件的可核对性**：`projects\{rtype,puzzlebobble,lunarlander}\scenes\main.tscn`
的 sha256 与上表逐位一致；`projects\<game>\src\<Class>.cs` 与
`tools\sessions\<game>\payload\<Class>.cs` **逐字节相同**（39713 / 37614 / 28822 B）。

### A1 三款的规则（每款都是从规则重写、可复算的整数/离散模型）

* **R-Type**（第 18 款）：800×600、HUD 到 y=64。船 `MovePlayer(dx,dy)` 每次 8 px，四处钳位；
  玩家子弹 16 px/步向右、出右边界消失；**编队入场**：一波的第 k 个出生点 = `(830 + (k/3)*40, 120 + (k%3)*70)`，
  敌机整体 3 px/步左移；敌机 **45 步固定冷却**，开火枪口 `(x-8, y+6)`、敌弹 6 px/步；
  玩家子弹取**出生顺序里第一个**重叠的敌机（一击必杀、+100 分）；**越过整场的敌机扣一条命**，
  中弹也扣命；三波 4/5/6 个。**一整局**（三波 15 个敌人、960 步、6 杀 9 漏、剩 49 命、600 分、Wave=3、24 次开火）
  由 Python 第二实现逐步算出，再原样作为调用序列发出。
* **Puzzle Bobble**（第 19 款）：8×12 方格、40 px/格、六色。
  **初始棋盘** = `seed=(seed*1103515245+12345) mod 2^31`、`(seed>>16)%6`、行优先填 4 行，
  再用同一套「去掉横/竖三连」的稳定循环修到无三连。
  **五种整数发射方向** `(-2,-1) (-1,-1) (0,-1) (1,-1) (2,-1)`，一格一步，**撞两侧墙反弹**；
  飞行中下一格越界或已占 → **吸附**在当前格（贴天花板也是一次吸附）。
  **同色四连通 ≥3 消除** → **悬空掉落**：与顶行不连通者掉出场地并计分 →
  **连锁**：掉落按**代**推进（只有正下方为空的浮空泡泡先落，一层一代，第 n 代倍率 n）。
  **失败线** row ≥ 10 判负；清空棋盘判胜。得分 = `消除数×10×代` + `掉落数×20×代`。
* **Lunar Lander**（第 20 款）：800×600、地面 y=560、三个着陆台（120–200 / 360–440 / 600–680，倍率 **1/2/1**）。
  **十二档整数姿态**（30° 一档）与**整数推力表**（正立 `(0,-4)`，顺时针 30° 递增）；
  每步 `vy += 1`（重力）；一次点火把推力对加到速度上并扣 1 燃料；
  积分 `x += vx; y += vy`。**着陆判定** = 触地时在着陆台上 ∧ `|Vx| ≤ 2` ∧ `|Vy| ≤ 6` ∧ 距正立 ≤ 1 档；
  满足则 `Landed` 且 **得分 = 剩余燃料 × 台倍率**，否则 `Crashed`；`Lx` 出场地也是坠毁。
  **下降方案由生成器先在 Python 里搜出来**（滑行到 `y ≥ 430` → 连续点火 8 步 → 滑行触地）：
  35 步、触地 `y=554`、`Vy=3`、剩 492 燃料、**台 1 → 984 分**。

### A2 调用数、判定分布、`facts_complete`（取自各自那一轮的 `ledger-*.txt`）

| 游戏 | 相 | 调用 | 判定分布 | `facts_complete` |
|---|---|---|---|---|
| R-Type | 编辑器 | 14 | `failed=1`（声明的同名拒绝，D-3）、`ok_effect_observed=1`、`ok_file_effect_observed=4`、`ok_no_effect_observed=8` | **14/14** |
| R-Type | 游戏 | 209 | `failed=1`（声明的边界调用 `-32001`）、`ok_effect_observed=83`、`ok_file_effect_observed=101`、`ok_no_effect_observed=24` | **209/209** |
| Puzzle Bobble | 编辑器 | 14 | 同上 | **14/14** |
| Puzzle Bobble | 游戏 | 143 | `failed=1`（`-32001`）、`ok_effect_observed=27`、`ok_file_effect_observed=91`、`ok_no_effect_observed=24` | **143/143** |
| Lunar Lander | 编辑器 | 14 | 同上 | **14/14** |
| Lunar Lander | 游戏 | 216 | `failed=1`（`-32001`）、`ok_effect_observed=39`、`ok_file_effect_observed=154`、`ok_no_effect_observed=22` | **216/216** |

三款每一轮的非 `ok` 判定都是**声明过的**：编辑器相那一次同名批量（D-3 的证据）与一条故意打在不存在属性上的边界断言（`-32001`）。

### A3 断言与「独立复算」（三款各自的真实数值）

* **断言**（分解逐款用脚本核对过：`assert_summary.py` 的每一处 PASS 都归到它自己那一类）：
  R-Type **101 PASS / 0 FAIL** = 99 条带属性的 `running_game_assert_node_state` ＋ 1 条屏幕文本（`WAVE CLEARED`）
  ＋ 1 条 `running_game_run_test_scenario` 自带的断言；**另有 1 条声明的边界失败**（`-32001`，不计入 PASS）。
  Puzzle Bobble **87 PASS / 0 FAIL** = 85 + 1 条屏幕文本（`BOARD CLEARED`）+ 1 条场景断言，另有 1 条边界失败。
  Lunar Lander **150 PASS / 0 FAIL** = 148 + 1 条屏幕文本（`THE EAGLE HAS LANDED`）+ 1 条场景断言，另有 1 条边界失败。
  逐属性分栏见 `logs\assert-*.txt`。
* **Python 第二实现**：三款各一份**从规则重写**的模拟器
  （`make_session_rtype.py` 的 `RSim`、`make_session_puzzlebobble.py` 的 `BSim`、`make_session_lunarlander.py` 的 `LSim`）。
  会话里每一个 `expected` 都取自它们；生成器同时导出 `expectations-*.json`，事后复算脚本把清单与响应里**实际回报的 `expected`** 逐条对齐：
  R-Type **99/99 + 1 条声明边界**、Puzzle Bobble **85/85 + 1**、Lunar Lander **148/148 + 1**，合计 **0 处不符**。
* **独立复算（后验，不 import 生成器、不看 `report.json`、不看 C#）**：`recompute_readbacks.py` 只吃运行自己写的
  `<tag>.json` 与 `call-index.txt`：
  * **R-Type**：由打印出来的 `player`/`lives`/`score`/`wave`/`wave_left` 与三张列表（`enemy_list`/`bullet_list`/`ebullet_list`）
    用**自己的** multiply-31 链重推 `StateHash` —— 2 个 `Dump()` 读数全部参与，**0 处不符**。
  * **Puzzle Bobble**：由打印出来的 `board=` 重推 `BoardHash`；**并由同一条 LCG + 同一个稳定循环重算初始棋盘本身**，
    与 `g13-readback-t0` 的 `board`/`board_hash`/`bubbles` **三项全 OK**；**0 处不符**。
  * **Lunar Lander**：由打印出来的 `pos`/`vel`/`angle_index`/`fuel`/`steps` 重推 `StateHash`；
    **并按 `call-index.txt` 的调用顺序独立重放整条轨迹**（自己的「点火/重力/积分/触地」）——
    **17 个检查点、0 处不符**。这就是任务点名要的「LL 的积分轨迹」。
* **像素差 + 帧链**：`pixel_recompute.py`（逐调用前后 PNG 对，两套阈值）与 `frames_recompute.py`（`user://` 保存帧链）
  对三款各 **0 处与 `report.json` 分歧**；三款保存帧 **4/4 sha 互不相同**。

### A4 帧率无关的步进与「一个属性一个写者」

三款都是**浮点累加器**（`_autoAccum += delta * AutoClock`），`Elapsed` 是每帧 `+= delta` 的浮点秒表；
每款各有**两个生产者、两个属性**：`LastHookSteps`（`StepFrames` 钩子这次调用做了多少）与 `LastAutoSteps`（这一帧的时钟走了多少）。
三款都在时钟跑过 12 帧之后断言 `LastHookSteps` **仍是钩子写下的那个值**。
**M3-4 的教训被写进断言本身**：三款的采样后面都跟着**会 FAIL 的硬断言** ——
`Steps gt 0`、`AutoTicks gte 1`，外加**一条 `neq` 窗口起始哈希**
（R-Type `StateHash neq H0`、PB `BoardHash neq H0`、LL `StateHash neq H0` 且 `Ly gt 起始值`）——
「时钟在走而世界冻住」不再是一串常数，而是一条红。
**PB 的采样板特意「先发射、再开钟」**：不先发一颗弹，棋盘在时钟下无事可做，采样窗口里一切恒定。

### A5 边界与反例（主动构造的「会 FAIL 的检查」）

* **每条容差都测两侧**（LL）：`|Vy|` **6 存活 / 7 坠毁**、`|Vx|` 4 坠毁、90° 坠毁、
  **330° 存活**（这条是「容差是两侧的」唯一证据 —— 只测 90° 会让人以为规则要求恰好正立）、
  错过所有着陆台坠毁、左右台各按自己倍率给分、飞出场地即坠毁。
* **PB 的越界侧**：`Aim(9)` 被钳到最后方向（不是拒绝）、`Aim` 同向重设被拒并计数；
  `Shoot` 在弹道中/结束后被拒；失败线那一发恰好停在 `(4,10)`。
* **R-Type 的原地拒绝**：钳到边界之后再来一次同向 `MovePlayer` 会**真的被记进 `RejectedMoves`**（不是静默）。

---

## B. 缺陷清单（分两栏）

### B1 工具缺陷（`modules\mcp_server`）：**0 条**

本轮**没有改动模块任何一个字节**（引擎仓工作树空、HEAD 仍是 `1f9d0cb1c9`），因此没有新的工具缺陷，
也没有为修任何东西而重建变体。

**一行诚实记录（不是缺陷）**：`project_validate_scripts` 在 rtype r2 上回 `not_compiled_count=1`
（`category=not_compiled`，理由写得很清楚：「构建产物里没有这个源文件的记录，所以没有发布 `valid`」），
而同一条工具在 pb r1 上回 `valid=true`。**TD/MC（TASK-103）当时也是 `not_compiled=1`。**
三次的 `invalid_count` 都是 0、`project_build_csharp` 都是 exit 0，所以这是**判定类别随时序变化的既有边界**
（工具自己把理由说出来了），**不是回归**。修它要动模块 → 重建两变体 + 十道门，不在本任务范围（登记为 X-2）。

### B2 游戏或驱动缺陷：**1 条**

| id | 层 | 现象（证据） | 根因 | 处置 → 重跑结果 |
|---|---|---|---|---|
| **RT-1** | R-Type **会话** | r1 的 `g114-assert-rejected` 期望 `RejectedMoves=0` 实得 **1**（同段 `g112-assert-shots-zero` 期望 `BulletsFired=0` 恰好也是 0，所以它没照出另一半） | 生成器**只把调用发出去，没有让自己那份 `RSim` 跟着走同一步**：游戏结束后的 `FireBullet()` / `MovePlayer()` 在载荷里被正确拒绝并计数，而在 `RSim` 里这两次调用根本没发生 —— 与 K-1 / TD-1 / M1 同源：**期望值必须来自它所断言的那一刻的状态** | 补 `lose.fire()` 与 `lose.move(8, 0)`；并按 **TD-2 的教训从模板重新实例化**（先写 sha256 清单再 `Move-Item`，全程零删除）后重跑 r2 → **101 PASS / 0 FAIL** |

### B3 取证工具自身：**2 条（`E-1`，明确不是模块缺陷、也不是游戏缺陷）**

都在本轮新写的 `recovery\work\task104\recompute_readbacks.py` 里：

| id | 现象 | 根因 | 处置 |
|---|---|---|---|
| **E-1a** | 哈希复算分支恒不执行：三款各只算到 **2 个哈希**却仍报 `0 处不符` | 判据写成 `"state_hash=" in fields`，而 `fields` 是**字典**（键不含 `=`）→ 条件恒假 —— **静默少算**，比报错更危险 | 改成 `"state_hash" in fields`；修后三款各自全部 `Dump()` 读数参与复算 |
| **E-1b** | Lunar Lander 的独立重放**从头到尾没开过火**，报 **10 处不符**（`g115`/`g125` 的 `steps`/`y`/`vy`/`fuel`/`max_vy`） | `SetThrust` 的回读按 `text.split("=",1)[1].strip()=="True"` 解析，实得 `"True fuel=500"` → 恒假 | 改成 `grab(text, "thrust_on") == "True"`；修后 **17 个检查点 0 处不符** |

**E-1b 的意义在它「响了」**：这条复算脚本没有和载荷互相迁就地静默同意，而是把 10 条不一致摆出来，
才让人去分清「是载荷错了」还是「是复算脚本错了」。上一轮 R-1 的教训（取证脚本自己也要能读错）在这里第二次应验。

---

## C. 收尾：免跑判定（未改模块）与如实说明

### C1 判定依据（三层，逐层都查过）

1. **引擎仓工作树空**：`git -C godot-mcp\godot status --short` → **空**；`git rev-parse HEAD` = `1f9d0cb1c983301d4efa575c16986c551df23600`
   （TASK-103 的模块提交之后的那个 commit，与 fork 同级）。**本条比「没有编译输入」更强：整棵树一个字节都没动。**
2. **门跑器自己的纯文档预检**（`tools\run_gates.ps1 -Tag task104`，不加 `-RunGates`）：

```
GATES_PREFLIGHT VERSION_TEXT=4.8.dev.mono.custom_build.1c7f5c07a
GATES_PREFLIGHT ANCHOR=1c7f5c07a HEAD=1f9d0cb1c ANCHOR_REPORTED=1c7f5c07a
GATES_PREFLIGHT WORKING_TREE_RED=0 WORKING_TREE_SAFE=0 COMMITTED_DIFF_SAFE=1
GATES_PREFLIGHT VERDICT=ANCHOR_STRUCTURAL_EQUIVALENT
GATES_PREFLIGHT REASON="1c7f5c07a is an ancestor of 1f9d0cb1c and all 1 file(s) in the diff are non-compiling; the binary is NOT equal to HEAD, it is structurally equivalent to it"
GATES_PREFLIGHT NONCOMPILING_COUNT=1
GATES_PREFLIGHT NONCOMPILING modules/mcp_server/docs/reports/REBUILT-2C-MANIFEST.md
GATES_PREFLIGHT RESULT=SKIP_REBUILD
GATES_SKIPPED=1
GATES_PREFLIGHT EXPLAIN=the diff between the built binary anchor and HEAD contains no compile input, so no compiled behaviour can have changed; the ten gates would report on the same binary that already passed
```

   逐字存放于 `runs\gates\task104\summary.txt`。
3. **本任务的范围**：TASK-104 的全部改动都在**主仓**（三个游戏工程、三份会话与载荷、生成器、
   `recovery\work\task104\`、`GAME-LOOP-LOG.md`、`DECISIONS.md`），**没有一个字节落在 `modules\mcp_server`**。

### C2 因此（如实说明，不做「应该可以」的转述）

* **十道门（`run_gates.ps1 -RunGates`）本轮未重跑**；最后一次真实十道门全绿是 **TASK-103**，
  在那次重建的两个变体上（`4.8.dev.mono.custom_build.1c7f5c07a` / `4.8.dev.custom_build.1c7f5c07a`），
  逐门真实退出码见 `recovery\reports\TASK-103-REPORT.md` §C2 与 `runs\gates\task103\summary.txt`。
* **`accept_m1.ps1` 本轮未重跑**；最后一次 **22/22 cases passed / `GATE_EXIT=0`** 也是 TASK-103（同上）。
* **两个变体没有重建**（每次 ~16 分钟），因为没有任何编译输入变化。
* **引擎仓没有新提交、也没有 push**：`git rev-parse HEAD` = `git rev-parse refs/remotes/origin/feature/mcp-server-module-rebuild`
  = `1f9d0cb1c983301d4efa575c16986c551df23600`，fork 上已经是这个提交，**无可推送的新内容**。

---

## D. 铁律执行记录

| 铁律 | 本轮做法 |
|---|---|
| 1 **禁止一切 shell 重定向** | 所有日志由 `Start-Process -RedirectStandardOutput/-RedirectStandardError` 拥有（`capture.ps1` / `run_one.ps1` / `new_game_run.ps1` / `reset_game_project.ps1` / `git_commit.ps1` / `final_snapshot.ps1` / `evidence.ps1`）；所有文本文件由 **Python 写入器**（`make_session_*.py`、`append_task104.py`）或 write 工具写；**没有一处 `>` 或 `\|`-into-file** |
| 2 **破坏性命令默认拒绝** | 唯一的删除是 `recovery\work\task104\logs\` 下**具名绝对路径**的日志覆盖（每个助手自己那一份，且都在 `task104\logs\` 前缀内）；**rtype 工程是移动不是删除** —— `reset_game_project.ps1` 先写完整 sha256 清单（`archive\rtype-20260927-072931.manifest.json`）再 `Move-Item` 到 `archive\rtype-20260927-072931\`；**没有删除任何一个游戏工程、任何一次运行产物** |
| 3 **构建与运行必须从 cmd 启动** | 四次会话（rt r1、rt r2、pb r1、ll r1）、四次 `--import`、四次 `project_build_csharp`、十道门预检、两次快照、一次提交全部经 `cmd.exe` |
| 4 **唯一端口 + 跑前查进程与端口** | 每轮运行前 `tasklist` + `netstat` 清点；R-Type 用 **9964/9965**、Puzzle Bobble 用 **9966/9967**、Lunar Lander 用 **9968/9969**，各组不重叠；**收尾快照**：无 `Godot*` 进程、9958–9975 无 `LISTENING` |
| 5 **会话文件先 Python + PS 5.1 双解析** | `check_session.py` 与 `check_session_ps.ps1` 在**起引擎之前**对三份会话各跑一次（rk 223/157/230 calls、tag 唯一、`content_file` 可达、`code` 非空），日志 `logs\checksession-py-*.txt`；PS 侧输出 `PS_PARSE OK ... unique_tags=` 与 calls 数**逐一相等** |
| 6 **迁移与删除先写 sha 清单存证** | rtype 归档前由 `hash_tree.py` 写出逐文件 size + sha256 的 `archive\rtype-20260927-072931.manifest.json`，然后才 `Move-Item`（全程零删除） |

---

## E. 遗留（不阻塞）

1. **`--import` 的关机期消息**：本轮 4 次导入全部 `IMPORT_EXIT=0`。
   **非崩溃形态**出现 **1 次**（`runs\rtype\rt-task104-r1\import.stderr.txt`，307 B：同样的
   `Parameter "singleton" is null.` 加一条 `Thread::~Thread` 警告），其余 3 次 stderr **0 字节**。
   这印证 TASK-099 的定位：这条消息是**关机期**的，导入本身已跑完（`IMPORT_EXIT=0`），
   `IMPORT_EXIT` 仍然**不能**当健康信号用。**崩溃形态台账口径**：TASK-099 留档 **3/23**，此后按轮推进 3/28（TASK-102）→ 3/34（TASK-103）→
   **本轮 3/38**（本轮 4 次导入全部 `IMPORT_EXIT=0`）；即 3/23 这个标记之后共 **15 次导入、0 次复现**。
2. 三款都是各自经典规则的**最小完整子集**：R-Type 没有道具/地形/母舰，Puzzle Bobble 没有顶部下压与瞄准线，
   Lunar Lander 没有地形起伏与侧风。
3. `ForceTestState` 仍允许钉出游戏本身到不了的状态（B-3 的成因），本轮以「会话不这么钉」处置，未在载荷里加防护。
4. **X-2**（`project_validate_scripts` 的 `valid` 有时缺席）**只登记未修**；修它要动模块 → 重建两变体 + 十道门。
5. 引擎仓**无新提交、无 push**（无内容可推）。

---

## F. 两仓 `git log --oneline -8` 与 `git status --short`（逐字取自 `logs\final-snapshot.txt`）

### F1 主仓 `F:\moonbit-hof-rs`（分支 `master`）

`git rev-parse HEAD`：

```
a8e0e564de6e76e059f4ad2e84f55027087d952e
```

```
a8e0e56 feat(godot-mcp): TASK-104 (D152) - the 18th, 19th and 20th C# games are delivered through MCP calls only, which closes D138's twenty-game target
4e88119 docs(godot-mcp): TASK-103 - the report's F4 states the closing boundary the way it was measured: the helper's post-commit log/status lines go into the same handle, so a pair stays modified
9dc688c docs(godot-mcp): TASK-103 - F4 says exactly which file a commit helper leaves behind: one .err.txt, because the .out.txt it just wrote is taken into the commit itself
da9edda docs(godot-mcp): TASK-103 - the report's F4 states the closing boundary exactly instead of claiming a clean tree the last commit cannot produce
85fe8ca docs(godot-mcp): TASK-103 - the helper-owned logs of the commit and snapshot scripts are committed after the fact so the working tree is clean, and the report's closing section is filled from that snapshot verbatim
5a36457 feat(godot-mcp): TASK-103 (D151) - tool defect X-1 is fixed at its root and both engine variants are rebuilt at the module commit, and the 16th and 17th C# games are delivered through MCP calls only
9733cae docs(godot-mcp): TASK-102 - the report's closing boundary is restated so it cannot be made stale by the task's own doc-only follow-ups: the snapshot right after the report commit still has the six helper-owned log entries, they are committed by the report commit itself, the housekeeping commit that follows cleans the two lines the commit helper writes after its own commit, and the working tree is empty from then on
b365654 docs(godot-mcp): TASK-102 - the helper-owned logs of the commit and two-repo capture scripts are committed after the fact so the working tree is clean; no content change
```

`git status --short`（取快照那一刻）：

```
 M godot-mcp/recovery/work/task104/logs/git-main.err.txt
 M godot-mcp/recovery/work/task104/logs/git-main.out.txt
?? godot-mcp/recovery/work/task104/final_snapshot.ps1
?? godot-mcp/recovery/work/task104/logs/final-snapshot.cmd
?? godot-mcp/recovery/work/task104/logs/final-snapshot.err.txt
?? godot-mcp/recovery/work/task104/logs/final-snapshot.txt
```

那 6 条**全是收尾助手自己写的**：`git_commit.ps1` 在提交之后又往同一个 stdout/stderr 句柄里写
`GIT_EXIT` / `git log` / `git status`（于是那一对被报成 ` M`），`final_snapshot.ps1` 写自己的脚本与输出。
这与 TASK-102/103 记的是同一个边界：**`git_commit.ps1` 按铁律 1 拥有自己的输出，所以它写的每个日志都必然落在
它所属的那次提交之后**；再做一次 housekeeping 只会换出下一批同名新文件。**故到此为止，不再提交。**
本报告所在的**报告提交**会把上面这 6 条收进仓（快照取在作品提交之后、报告提交之前）。

### F2 引擎仓 `F:\moonbit-hof-rs\godot-mcp\godot`（分支 `feature/mcp-server-module-rebuild`）

```
===ENG rev-parse HEAD===
1f9d0cb1c983301d4efa575c16986c551df23600
===ENG rev-parse origin ref===
1f9d0cb1c983301d4efa575c16986c551df23600
```

`git log --oneline -8`（引擎仓，**与 TASK-103 结束时逐字相同，本轮未移动**）：

```
1f9d0cb1c9 modules/mcp_server: task103 - REBUILT-2C-MANIFEST gains the 2c-12 section: ...
1c7f5c07a1 modules/mcp_server: task103 (X-1) - a GDScript body that compiles and then fails while it runs is a structured refusal now (-32000 + data.script_error + data.suggestion) instead of an ok with a null result, and a successful body that returned no value carries a note, so "ok" can no longer be read as "the script ran"
e041cae270 modules/mcp_server: task099 - REBUILT-2C-MANIFEST gains the 2c-11 section: ...
0fbd5ec4cb modules/mcp_server: task098 - MCP-TRACEABILITY section 7 is aligned with the D-1 closure
094b071f9b modules/mcp_server: task097 - REBUILT-2C-MANIFEST gains the 2c-10 section: ...
2385fe2fb5 modules/mcp_server: task097 (D-3) - a requested node name the target parent already carries is now refused instead of silently renamed, ...
95aa1d8984 modules/mcp_server: task096 - MCP-TRACEABILITY gains section 7: ...
8b9dd9a72b modules/mcp_server: task094 - D-2 is a load-sensitive readiness predicate, not a defect: ...
```

`git status --short`（引擎仓）：**空**。

### F3 收尾后的进程与端口

```
===PROCESSES===
INFO: No tasks are running which match the specified criteria.
===PORTS 9958-9975===
===PORTS_DONE===
```

（`SNAPSHOT_EXIT=1` 是那条 `findstr` 无匹配的退出码，不是错误。）**未改变机器显示或串流状态。**

### F4 报告写完之后的三次自查提交（收尾时的最终状态）

本报告的第一版（提交 `60bc9fb`）里有两处数字**没有经得起复查**，都当场改掉并各留一个提交，
而不是留在报告里等人替我发现：

| 提交 | 改了什么 | 为什么 |
|---|---|---|
| `4ea0da5` | 断言分解与 20 款调用合计 | ①把「101 PASS」写成「99 + 1 条边界 + 1 条屏幕文本」，**分类差一格**：`assert_summary.py` 逐 tag 输出显示 101 里 99 条带 `property`，另两条是屏幕文本与 `run_test_scenario` 自带的断言，而那条声明的 `-32001` **不进任何一栏**；②把 20 行两列相加应是 **2 554**（303 / 2 251），原写 2 441（300 / 2 141） |
| `8cf0227` | `--import` 累计口径 | 原写 **3/48**（把 TASK-099 自己的 `3/23` 当成 TASK-100 之前的基数）。台账里的链是 `3/13 → 3/17 → 3/23 → 3/28`（TASK-102）`→ 3/34`（TASK-103），所以本轮是 **3/38**，`3/23` 之后共 **15 次导入、0 次复现** |
| `e3b8b57` | 最终审计脚本 | `audit_report_claims.py` 从运行产物与 20 行台账**重新推导**每一个头条数字并打印出来对账，输出存 `logs\audit-claims.txt`，与报告逐项一致；同一次顺带修掉行 20 的一个用词 |

三处修订都用**Python 写入器 + 逐条「恰好匹配一次」断言**做的，所以不可能静默改不动。
**这句话本身是留档：本报告的数字是我在写完之后又验过一遍的，不是初稿。**

收尾时的最终状态（逐字取自 `logs\closing.txt`）：

主仓 `F:\moonbit-hof-rs`（`master`），`rev-parse HEAD` = `e3b8b57894eb77888502cb9d5eb940be886c3289`：

```
e3b8b57 docs(godot-mcp): TASK-104 - the final audit script re-derives every headline number from the run products and the ledger, and one wording fix
8cf0227 docs(godot-mcp): TASK-104 - the --import cumulative denominator is corrected to 3/38 (it was written as 3/48 from a mis-read base)
4ea0da5 docs(godot-mcp): TASK-104 - the assertion tallies and the twenty-game call total are corrected against the run products instead of left as first written
60bc9fb docs(godot-mcp): TASK-104 - the report: the three new C# games with their real call counts, verdict distributions, assertion tallies and independently recomputed pixel columns, the one session defect their first runs caught, the two defects of the evidence tool itself, the twenty-game milestone, and the honest statement that no module byte changed so the ten gates and accept_m1 were NOT re-run
a8e0e56 feat(godot-mcp): TASK-104 (D152) - the 18th, 19th and 20th C# games are delivered through MCP calls only, which closes D138's twenty-game target
4e88119 docs(godot-mcp): TASK-103 - the report's F4 states the closing boundary the way it was measured: the helper's post-commit log/status lines go into the same handle, so a pair stays modified
9dc688c docs(godot-mcp): TASK-103 - F4 says exactly which file a commit helper leaves behind: one .err.txt, because the .out.txt it just wrote is taken into the commit itself
da9edda docs(godot-mcp): TASK-103 - the report's F4 states the closing boundary exactly instead of claiming a clean tree the last commit cannot produce
```

`git status --short`（主仓，取 `closing.txt` 那一刻）：

```
 M godot-mcp/recovery/work/task104/final_snapshot.ps1
 M godot-mcp/recovery/work/task104/logs/git-audit.err.txt
 M godot-mcp/recovery/work/task104/logs/git-audit.out.txt
?? godot-mcp/recovery/work/task104/logs/closing.cmd
?? godot-mcp/recovery/work/task104/logs/closing.err.txt
?? godot-mcp/recovery/work/task104/logs/closing.txt
```

同样**全是收尾助手自己写的**（`git-audit.*` 是 `git_commit.ps1` 在提交之后写回去的那一对；
`final_snapshot.ps1` 这次为了不覆盖 F1 引用的那一份而被加上了 `-Tag`，于是它自己也成了待提交项；
`closing.*` 是刚写出来的快照）。收尾时的引擎仓仍然是 **`1f9d0cb1c9`、工作树空、无 push**。
本报告所在的这一次提交会把上面这 6 项收进仓 —— 这正是 TASK-102/103 记下的那条**收尾自身的边界**
（按铁律 1 拥有自己输出的助手，其日志必然落在它所属的提交之后），**到此为止，不再提交**。

---

## G. 返回值（≤ 10 行）

1. TASK-104 完成：第 18/19/20 款 C# 小游戏交付，**D138 的「至少 20 款」收口**（台账 20 行齐全，20 款 `facts_complete` 全 100%）。
2. R-Type `rt-task104-r2`：223 调用（14/209）、101 PASS/0 FAIL、像素 87/223、复算 0 处不符；首轮缺陷 **RT-1**（会话）已修并重跑。
3. Puzzle Bobble `pb-task104-r1`：157 调用（14/143）、87 PASS/0 FAIL、像素 29/157、复算 0 处不符（含初始棋盘由 LCG 重算）；零缺陷。
4. Lunar Lander `ll-task104-r1`：230 调用（14/216）、150 PASS/0 FAIL、像素 41/230、复算 0 处不符（含 **35 步积分轨迹 17 个检查点独立重放**）；零缺陷。
5. 缺陷分栏：**工具缺陷 0 条**（未改模块一个字节）+ **游戏或驱动缺陷 1 条**（RT-1）+ 取证工具自身 2 条（E-1a/1b，均已修）；X-2 只登记。
6. 里程碑小结（20 款一览、**合计 2 554 次调用 = 编辑器 303 / 游戏 2 251**、工具缺陷累计与修复轮次、像素/复算覆盖率 20/20、`--import` 累计 3/38）与**独立验收入口**已写进 `GAME-LOOP-LOG.md`。
7. 收尾：**未改模块 → 走免跑判定**，`run_gates.ps1` 自判 `ANCHOR_STRUCTURAL_EQUIVALENT` + `SKIP_REBUILD`；**十道门与 `accept_m1` 本轮未重跑（如实说明，不做「应该可以」的转述）**。
8. 主仓提交 `a8e0e56`（139 文件 / 24 875 增）+ 报告 `60bc9fb` + **四次自查修订** `4ea0da5`/`8cf0227`/`e3b8b57`/`e5caf63`（断言分解、20 款合计 2 554、`--import` 3/38、最终审计脚本、F4 收尾节），**收尾时 HEAD `e5caf63`**（它自己的哈希写在提交之后，逐字见 `logs\git-f4.out.txt`）；引擎仓**工作树空、HEAD 未动、无 push**（fork 已是 `1f9d0cb1c9`）。
9. 报告：`F:\moonbit-hof-rs\godot-mcp\recovery\reports\TASK-104-REPORT.md`；决策 **D152** 已入 `DECISIONS.md`。
10. 遗留：`--import` 关机期消息本轮**非崩溃形态**出现 1 次（`IMPORT_EXIT=0`）；三款均为经典规则的最小完整子集；X-2 未修。
