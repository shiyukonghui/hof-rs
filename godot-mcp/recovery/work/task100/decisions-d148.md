## D148 — TASK-100：第 10、11 款 C# 游戏（2048 / Minesweeper）交付；「一个属性一个写者」（G1）与会话对 `ForceTestState` 的假设（M1）

**日期**：2026-09-27　**触发问题**：D147 留下两件事 —— ①台账只到第 9 行，D138 的目标是至少 20 款 C# 游戏；②D147 把「任何『钩子做了多少』都做成与帧率无关的增量属性」写进模板（P-1 的教训），但**没有规定这个属性只能有一个写者**。本轮交付第 10、11 款时，这条缺口当场以两种形态出现：**G1**（载荷：`LastAutoSteps` 既被 `AutoStep` 钩子写、又被每帧时钟写，r1 两条断言实得 0）与 **M1**（会话：把 `ForceTestState` 会归零的计数器当成会保留，r1 收尾断言实得 0）。

**考虑过的选项**

| 决策点 | 选项 | 选择 | 理由 |
|---|---|---|---|
| ① 两款游戏的场景怎么建 | (a) 把静态棋盘铺进 `.tscn`；(b) **继续只摆 3 个静态节点（`Background`/`Hud`/`Status`），棋盘全部 `_Ready()` 运行期新建** | **(b)** | 沿用第 4..9 款的形态：场景小而干净（编辑器相 16 / 14 次调用），不会被 D-3 的同名陷阱咬到，而且「运行期新建的节点确实被画出来」本身就是证据（2048 的 16 个格子、Minesweeper 的 81 个格子） |
| ② 2048 的「未知数」怎么保证确定性 | (a) 真随机 spawn；(b) **随机落子做成声明的固定钩子 `SpawnTile(r,c,v)` / `AutoSpawn`，棋盘由一次 `ForceTestState` 钉死** | **(b)** | 「合并出的 8」必须是单元格的性质，不能是时间/随机数的性质；与本系列前十款同一条确定性规则 |
| ③ Minesweeper 的雷区怎么保证确定性 | (a) 每次运行随机布雷；(b) **种子 + 固定 LCG（`MineSeed=12345`），并让会话生成器用同一条规则在 Python 里独立复算出 `MineList` 字面量** | **(b)** | 布雷是纯函数 → 断言的期望值可以**独立复算**而不是从实现抄。`g07`/`g136` 两条 PASS 就是「实现与独立复算相符」 |
| ④ 首翻安全怎么做成可断言的事实 | (a) 只保证不炸；(b) **把那颗雷按行优先移到第一个无雷格，并导出 `MinesRelocated` / `MineList` / `ProbeMine` / `ProbeHint`** | **(b)** | 「唯一一颗雷正在点击处」→ `MinesRelocated=1`、`MineList` 由 `0,0` 变成 `0,1`、点中的格子 `ProbeHint=1`：三个数把规则钉死，而不是「没炸就算对」 |
| ⑤ 增量属性几个写者 | (a) 沿用「`LastAutoSteps` 一个属性，钩子和时钟都写」；(b) **拆成 `LastHookSteps`（只有 `AutoStep` 写）与 `LastAutoSteps`（只有每帧时钟写）** | **(b)** | **G1 实测**：r1 里 `AutoSteps=2`、`MoveCount=2` 双双 PASS 而 `LastAutoSteps=0` —— 钩子确实走了两步，只是断言读到的是下一帧时钟写进去的 0。一个属性两个写者，读回就不再是那个生产者的事实；这是 P-1 的同一条教训换了形态 |
| ⑥ 时钟形态 | (a) `frames = (int)(delta * rate)`；(b) **浮点累加器 `_autoAccum += delta * rate` + 每帧 `Elapsed += delta` 的浮点秒表** | **(b)** | F-1 的根因（144 fps 下单帧 `delta*rate < 1` 被截断成 0）。两款都按 (b) 写，且 `Elapsed` 在采样里 30/30 帧各不相同 |
| ⑦ 声明动作怎么触发 | (a) 直接轮询 `Input.IsActionPressed` 并按帧重复；(b) **按「按下沿」触发，一次注入只算一次操作** | **(b)** | 场景步骤注入的按键**永不释放**；按沿触发让「一次注入 = 一次操作」成为确定事实（实测 `InputMoves=1`、`InputReveals=1`），也避免 S-3 那类「被当成一直按住」的陷阱 |
| ⑧ M1 怎么修 | (a) 把会话期望值改成 0；(b) **让「钩子 → 开时钟 → 30 帧采样 → 关时钟 → 两条增量断言」落在同一块被钉住的盘面上，并新增一条显式断言「`ForceTestState` 之后两条增量都归零」** | **(b)** | (a) 会让「时钟不写钩子的属性」这条事实从证据里消失。载荷是对的、会话的假设错了（A-1/T-3 同类）：把 A-1 的教训**写成断言**，下次同类假设会在同一处失败 |

**最终选择与理由**：交付 **2048**（第 10 款：4×4 未知数网格、四向滑动合并、计分、2048 取胜、无路可走判负、非法移动被拒）与 **Minesweeper**（第 11 款：9×9 / 10 雷、布雷、翻开与泛洪、数字提示、标旗、首翻安全、失败与胜利判定、非法操作被拒），两款全程只用 MCP 调用写成（`project_edit_script` / `editor_add_nodes_batch` / `editor_save_scene` / `editor_add_input_action` / `project_build_csharp` / `project_validate_scripts` / `editor_get_errors`，游戏相全部是 `running_game_*`）。两款都在建场景那一步**故意再跑一次同名批量**让 D-3 的 `-32000` 留在每一轮证据里（`conflicts` 各 3 条，`e05`/`e09` 文件 sha 逐字节相同），都有**冻结基线 + 自动时钟 30 帧**两段多帧采样、都有**两个单一写者的增量属性**、都把 `Elapsed` 做成不截断的浮点累加器。发现并修好两条缺陷（G1 载荷、M1 会话），各自重跑对照。

**预期影响与回滚点**：主仓新增 `projects\game2048\`、`projects\minesweeper\`、`tools\sessions\{game2048,minesweeper}\`、`recovery\work\task100\`（含两份归档工程的 sha256 清单与源码），并修改 `GAME-LOOP-LOG.md`。引擎仓 `git status` 前后均为空、`git diff 2385fe2fb..HEAD` 仍只有两份 `.md` → **两个变体一个字节都没动，未重建、未 push 代码**。回滚 = `git revert` 对应提交（纯新增 + 文档，无迁移）。风险敞口：①`--import` 的间歇性退出码仍在（本轮 4 次导入全 0，累计 3/17），`IMPORT_EXIT` 依旧**不能**当健康信号；②两款的自重跑时钟默认关闭（`AutoPlay`/`AutoReveal` = 0），只在测试显式打开时参与证据；③Minesweeper 的 `Probe*` 系列是**测试专用**的读回属性（会暴露隐藏格的信息），已在载荷注释里写明，不参与胜负判定。

**验证（真实输出）**：

* **2048**（`runs\game2048\2048-task100-r2`，首轮 r1 对照）：129 次调用（编辑器 16 / 游戏 113），`facts_complete` **129/129（100%）**，判定分布 `failed=2`（**两条都是声明的**：`e06` 同名批量 `-32000`、`g106` 不存在属性 `-32001`）+ `ok_effect_observed=23` + `ok_file_effect_observed=81` + `ok_no_effect_observed=23`；断言 **70 PASS + 1 条声明的边界失败**（`assertions.py`）＋ **2 条屏幕文本 PASS** ＋ **1 条场景断言 PASS**（`extra_assertions.py`）= **73 PASS**；像素差 **26/129 非零**（编辑器 1/16、游戏 25/113），`user://` 六帧逐对 **13055 / 15543 / 171792 / 148841 / 26181 px**，六个 sha 互不相同；独立复算（`pixel_recompute.py` + `frames_recompute.py`）与 `report.json` **0 处不符**；`project_build_csharp` exit 0（3732 ms）、`invalid_count=0`、`editor_get_errors count=0`；树里 75 个节点名 **0 个 `@` 开头**。
* **Minesweeper**（`runs\minesweeper\mine-task100-r2`，首轮 r1 对照）：155 次调用（编辑器 14 / 游戏 141），`facts_complete` **155/155（100%）**，判定分布 `failed=2`（同样两条声明的）+ `ok_effect_observed=20` + `ok_file_effect_observed=101` + `ok_no_effect_observed=32`；断言 **93 PASS + 1 条声明的边界失败** ＋ **2 条屏幕文本 PASS** ＋ **1 条场景断言 PASS** = **96 PASS**；像素差 **21/155 非零**（编辑器 1/14、游戏 20/141），`user://` 五帧逐对 **194130 / 196947 / 196939 / 195563 px**，五个 sha 互不相同；独立复算 **0 处不符**；`project_build_csharp` exit 0（3678 ms）、`invalid_count=0`、`errors count=0`；树里 333 个节点名 **0 个 `@` 开头**。
* **「会动的证据」**：2048 的自动时钟 30 帧采样里 `MoveCount` **30 个不同值 6→65**、`AutoSteps` 30 个、`Elapsed`/`Ticks` 各 30 个；Minesweeper 的 `RevealedCount` **7 个不同值 16→71**、`RevealHash` 7 个、`AutoSteps` 7 个、`Elapsed`/`Ticks` 各 30 个。冻结基线与自动时钟的对照就是「不动的那个不动、动的那个在动」。
* **两条缺陷的修前/修后**：`runs\game2048\2048-task100-r1` 的 `g88-assert-last-auto-2` **FAIL（actual=0）** 与 `g110-assert-last-3` **FAIL（actual=0）** → r2 的 `g88-assert-last-hook-2`/`g88b-assert-last-auto-0`/`g110-assert-last-hook-3` **三条同时 PASS**；`runs\minesweeper\mine-task100-r1` 的 `g124b-assert-hook-intact` **FAIL（actual=0）** → r2 的 `g113`/`g113b`/`g118b`/`g124`/`g126b` 五条 **全 PASS**。两次重跑都先把旧工程**先写 sha256 清单再移动归档**（`recovery\work\task100\archive\*-r1`，各 129 文件 / 8 399 363 B、8 417 591 B）并重新从模板实例化。
* **门跑器**：本轮无模块字节改动 → `run_gates.ps1` 预检判 `ANCHOR_STRUCTURAL_EQUIVALENT` + `RESULT=SKIP_REBUILD` + `GATES_SKIPPED=1`，exit 0，非编译文件清单两份 `.md`（`runs\gates\task100-doconly\summary.txt`）。**如实说明：十道门本轮一门未跑**，未重建、未 push 代码。
* **`--import`**：四次导入（2048 r1/r2、Minesweeper r1/r2）全部 `IMPORT_EXIT=0`、`import.stderr.txt` 0 字节；累计 **3 次 / 17 次会话导入**（待办 2 不变）。

**遗留（不阻塞）**：①`--import` 的关机期访问违例仍未结案（本轮 0 次，三个判别器都要动引擎源码 + 重建两变体，等可复现配方或用户授权）；②`editor_add_node`（单个）仍保留引擎改名语义、`editor_save_scene` 每会话重发场景 `uid` 的行为未修（沿用 TASK-097 的声明边界）；③Minesweeper 的 `AutoReveal` 策略只翻「行优先第一个隐藏安全未标旗格」，是一款游戏的测试策略而**不是通用求解器**；④2048 的 `AutoPlay` 策略是固定方向循环（左→上→右→下），同样只为可复算的证据服务。
