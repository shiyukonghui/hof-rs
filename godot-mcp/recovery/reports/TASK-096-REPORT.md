# TASK-096 — D-1 归属判定：**三选一之外，第四条** —— 重跑的编辑器相把整份节点副本写进场景（工具缺陷 D-3）；像素列改标「不可得（D-1）」；第 4 个游戏 Tetris 交付

* 执行者：工具工程师（本会话，**有写权限，不再委派**）
* 主仓：`F:\moonbit-hof-rs`（分支 `master`，无远端）
* 引擎仓：`F:\moonbit-hof-rs\godot-mcp\godot`（分支 `feature/mcp-server-module-rebuild`，remote `git@github.com:shiyukonghui/godot.git`）
* 脚本 / 会话 / 探针 / 证据：`godot-mcp\recovery\work\task096\`
* 时间：2026-09-27（本会话）

---

## 0. 结论表（每行一句话）

| 段 | 要求 | 结论 | 关键证据 |
|---|---|---|---|
| **A** | 用同一场景、同一批调用在我方引擎与 stock 4.7.1 mono 上做 A/B，判 (a) 我们的回归 / (b) 上游既有行为 / (c) 纯呈现层 | **做完，但结论是三选一之外的第四条（项目侧缺陷）。** 同一批操作在**我方引擎**（含全部 `--mcp-*` 开关）与 **stock 4.7.1 官方构建**上**逐行相同且全部正常**；snake 上的「冻结」是**采样像素被一层同名副本挡住**——副本来自「重跑编辑器相」写进场景文件的整份节点副本 | 探针工程 `recovery\work\task096\probe` → `runs\ours-8b9dd9a72b` / `runs\ours-mcp-flags` / `runs\stock-471`；遮挡证明 `runs\snake\task096-occ`（o03/o06/o10） |
| **B** | 像素差列由 `0` 改为「不可得（D-1）」，并补替代证据链 | **做完。** `GAME-LOOP-LOG.md` 三行改标（根因按 TASK-096 的定域写，不是 TASK-095 的旧表述）；`tools\game_report.py` 内置该标注（`--pixel-evidence=auto|available|unavailable`，`report.md`/`report.json` 都带结论与理由）；`MCP-TRACEABILITY.md` 新增 **§7**（替代证据链 + 台账读法） | `runs\tetris\tetris-task096-r2\report.md`、`recovery\work\task096\reporttest-pong\report.md`（0/52 → 标注）、引擎仓 `95aa1d8984` |
| **C** | 第 4 个游戏 Tetris（C#），只用 MCP 调用开发 | **做完。** 两轮共 95 次调用（首轮 53、终轮 42）；终轮 `facts_complete` **42/42（100%）**；**像素差 11/42 非零**（场景干净）；下落/消行/得分/GameOver 由逐帧采样与断言钉住；3 条缺陷已修并重跑同批对比 | `runs\tetris\tetris-task096-r2\`、`tools\sessions\tetris\session.json` / `session-r2.json`、`projects\tetris\` |
| **D** | 改了模块就重建两变体 + 十道门 + `accept_m1` 22/22 + push；主仓提交；给两仓 log/status | **十道门全绿（真实退出码）、`accept_m1` 22/22；未重建（唯一改动是非编译的文档，理由见 §D2）；引擎仓已 push**；两仓 log/status 在 §D3 | `runs\gates\task096\summary.txt`；主仓 `1b5b108`；引擎仓 `95aa1d8984` |

---

## A. 归属判定：A/B 做完了，答案是「都不是」

### A1 实验设计：为什么必须造一个探针工程

任务书要求「用**同一个场景与同一批调用**」在两个引擎上跑，并「可直接复用 `sessions\loadednode\session.json` 的操作序列」。**这里有一个硬约束**：stock Godot 4.7.1 官方构建里**没有 `mcp_server` 模块**，会话文件里的 `running_game_execute_gdscript` 在它上面**不可能存在**。所以：

* 会话文件**逐字复用**在我方引擎上跑了一遍（`runs\snake\task096-loadednode-replay`，端口 9896）：现象**今天仍然复现**（`p03`/`p07` 的 `P1(10,580)` 与 `p01` 一字不差）；
* 同时把这批操作**重编码成一段 GDScript**（`recovery\work\task096\probe\probe.gd`，p01–p10 与 `loadednode` 的每一步一一对应，另加 p08–p10 三个运行期新建项的对照），放进一个**只用 GDScript 的探针工程**（`probe\project.godot` + `main.tscn`：一个加载期全屏 `Background` + 一条加载期网格线）。**同一份字节**分别交给两个引擎运行 —— 这是让「两个引擎、同一批操作」这句话为真的唯一形态，而且比复用 snake 更强：连场景文件都是同一份。

运行器 `recovery\work\task096\run_probe_ab.ps1`（铁律 1：`Start-Process -RedirectStandardOutput`；铁律 3：引擎由生成的 `.cmd` 从 `cmd.exe` 启动）。

### A2 结果：三个运行逐行相同，全部正常

| 运行 | 引擎 | 关键行 |
|---|---|---|
| `runs\ours-8b9dd9a72b` | `F:\...\godot\bin\godot.windows.editor.x86_64.mono.console.exe`（`4.8-dev (custom_build)`，**无** MCP 开关） | `p03` `P1(10,580)=(1.0, 0.0, 1.0, 1.0)`（品红）；`p07` `(0.0, 1.0, 0.0, 1.0)`（绿） |
| `runs\ours-mcp-flags` | 同一二进制，**带** `--mcp-port --mcp-trace --mcp-capture=every_call --mcp-capture-dir --mcp-capture-viewport=2d` | `p03` 品红；`p07` 绿（与上面逐行相同） |
| `runs\stock-471` | `D:\Program Files\Godot_v4.7.1-stable_mono_win64\...\Godot_v4.7.1-stable_mono_win64_console.exe`（`4.7.1-stable (official)`） | `p03` 品红；`p07` 绿（与上面逐行相同） |

三份 stdout 里 `p01` 的 `P1`/`P2` 都是 `(0.0,0.0,0.0,1.0)`（探针场景没有全屏底色，只有 `Background` 那块 800×600 的 ColorRect），`p03` 起随 `Background.color` 走；`p05`（运行期新建全屏 `C9`）三份都变黄；`p08`/`p09`/`p10`（运行期红→蓝→移除）三份都跟着变。

**结论：加载期入树的 `CanvasItem` 在两个引擎上都正常重录绘制命令。** TASK-095 的「加载期项不再重录」这条定域，在我方引擎自己的实测面前不成立。

### A3 真因：场景文件里的**副本层**

探针正常、snake 冻结，差异只能来自项目侧。读 `projects\snake\scenes\main.tscn`：它在具名节点（`Background`、14 条 `GridLine*`、20 个 `SnakeSeg*`、`Food`、`Status`）之后，还有 **37 个自动名节点** `@ColorRect@20995` … `@ColorRect@21031` —— 颜色与尺寸与具名节点**一一对应**（1+14+20+1+1 = 37），而且**排在树最后**，Godot 在同一父节点下按树序绘制，所以它们**绘制在最上层**。

**遮挡证明**（`recovery\work\task096\sessions\occ\session.json` → `runs\snake\task096-occ`，端口 9898）：

| 调用 | 输出（真实） | 说明 |
|---|---|---|
| `o03-who-covers-p1` | `covering P1 in draw order (last is on top): 0:Background color=(0.05, 0.09, 0.07, 1.0) \| 36:Status color=(0.85, 0.1, 0.1, 0.35) \| 37:@ColorRect@20995 color=(0.05, 0.09, 0.07, 1.0)` | 采样像素上压着**三层**，最上层是不透明的副本 |
| `o04-loaded-magenta-again` | `P1(10,580)=(0.051, 0.0902, 0.0706, 1.0) bg=(1.0, 0.0, 1.0, 1.0)` | 改加载期 `Background`：**像素不动**（=TASK-095 的现象） |
| `o05-hide-covers` / `o06-read-after-hide` | `hidden=["@ColorRect@20995"]` → `P1(10,580)=(0.949, 0.0353, 0.6863, 1.0)` | **隐藏那一个副本后同一像素立刻跟着 `Background.color` 走** |
| `o10-read-moved-segment` | `px(300,300)=(0.5255, 0.651, 0.3294, 1.0)`（其间 `SnakeSeg00.position` 被移到 `(300,300)`） | 加载期**蛇身**也正常上屏 |

`(0.949, 0.0353, 0.6863)` 可以**逐位复算**：品红 `(1,0,1)` 叠上 `Status` 的 `(0.85,0.1,0.1,α=0.35)` → `R=0.85*0.35+1*0.65=0.9475`、`G=0.1*0.35=0.035`、`B=0.1*0.35+1*0.65=0.685`。蛇身绿 `(0.35,0.95,0.45)` 同法得 `(0.525,0.6525,0.3275)`，与实测 `(0.5255,0.651,0.3294)` 同。**这两条把「像素确实在跟着属性走」钉死，不需要相信任何一句转述。**

**副本是怎么进去的（提交级与运行级证据）**：

| 证据 | 值 |
|---|---|
| `git show df02ccb:godot-mcp/projects/pong/scenes/main.tscn` 中 `@ColorRect@` 节点数（TASK-092 之前的 pong） | **0** |
| `git show 97167e4:...pong/scenes/main.tscn`（TASK-093）与 `HEAD` | **5** |
| `runs\pong\pong-run1 … pong-run4\e20-scene-tree.json` 里的 `@ColorRect@` | 无 |
| `runs\pong\pong-control-task093\e20-scene-tree.json` 里的 `@ColorRect@` | **有** |
| breakout / snake 场景里的副本数 | 18 / 37 |

`e20-scene-tree` 是 `editor_open_scene` + `editor_add_nodes_batch` + `editor_save_scene` 之后读回的树。**把这一套在已经有这些名字的节点上再跑一遍**，Godot 把新节点自动改名成 `@ColorRect@NNNN`，`editor_save_scene` 把**两份**都写进 `.tscn`。pong 的 control 轮就是这么被污染的；breakout/snake 的 r2..r7 同理。

**同一二进制、同一会话、前后答案不同（TASK-094 之谜）也就此解释**：`00:14:53` 的 `10/29` 非零发生在**场景还没有副本**的时候；`01:18:26` 的 `0/29` 发生在 pong 的场景已经被 control 轮写过副本之后。**与机器画面管线、GPU 扫描输出、GameViewer、`display_active=Disabled` 全都无关。** TASK-094 那次「两个不同引擎给出同一份窗口抓取字节」也因此不必再用「桌面合成面冻结」解释：两个引擎算出来的画面本来就都是**静止的副本层**。

### A4 对三选一的逐条回答

| 选项 | 判定 | 依据 |
|---|---|---|
| **(a) 我们引擎的改动引入的回归** | **不成立** | 同一份探针字节在我方引擎上正常（§A2）；若是我方回归，探针里加载期的 `Background` 也不会动。**没有补丁/提交需要定位，也没有修复方向要给** |
| **(b) Godot 上游在输出侧关闭时的既有行为** | **不成立** | stock 4.7.1 官方构建（`4.7.1-stable (official)`）在**同一批操作**上表现与 §A2 逐行相同。上游在干净场景里没有这个行为 |
| **(c) 纯呈现层（画面不合成）而渲染侧正常** | **不成立（但「画面确实没变」这半句是对的）** | 画面是真的静止的，而且静止的原因**不在渲染/合成侧，在场景文件里**：同样的引擎、同样的渲染路径、干净场景下像素差是**非零**的（Tetris 11/42，§C）。如果只是「画面不合成」，干净场景也不会动 |
| **(d) 第四条：项目侧 —— 场景被写入整份副本层** | **成立** | §A3 的三条证据 |

### A5 最小复现与修复方向（**本轮不改引擎**）

**最小复现（两条一起看才有判别力）**

```cmd
:: ① 现象：snake 上改加载期 Background，像素不动
powershell -File tools\run_game_session.ps1 -Game snake ^
  -Session recovery\work\task095\sessions\loadednode\session.json -RunTag x -GamePort 9892 -SkipReport

:: ② 判别：把最上层那一个副本隐藏掉，同一像素立刻跟着背景色走
powershell -File tools\run_game_session.ps1 -Game snake ^
  -Session recovery\work\task096\sessions\occ\session.json -RunTag x -GamePort 9898 -SkipReport

:: ③ 反证：干净场景里同一批操作在两个引擎上都正常
powershell -File recovery\work\task096\run_probe_ab.ps1 ^
  -Exe F:\moonbit-hof-rs\godot-mcp\godot\bin\godot.windows.editor.x86_64.mono.console.exe -Tag ours
powershell -File recovery\work\task096\run_probe_ab.ps1 ^
  -Exe "D:\Program Files\Godot_v4.7.1-stable_mono_win64\Godot_v4.7.1-stable_mono_win64\Godot_v4.7.1-stable_mono_win64_console.exe" -Tag stock
```

**修复方向（三层，任决策者取）**

1. **最小动作（项目侧，1 个文件 1 次编辑 × 3）**：把 `@ColorRect@*` / `@Label@*` 副本节点从 `projects\pong|breakout|snake\scenes\main.tscn` 删掉。画面会立刻恢复真实节点的运动，像素差列可回填。**风险 = 0**：副本没有任何脚本、没有任何一处代码引用它们（`SnakeGame._Ready()` 只收集带 `SnakeSegment` 脚本的子节点，副本是裸 `ColorRect`）。
2. **根因动作（模块侧，会触发重建 + 十门 + `accept_m1`）**：`editor_add_nodes_batch` 在目标父节点下发现**同名节点已存在**时**拒绝并报告**（或新增 `on_conflict=refuse|rename` 语义），`editor_save_scene` 在树里出现自动名副本时**警告**。这是让「下一个游戏不会被无声污染」的那一步。
3. **不推荐**：把副本当作预期行为。它让 `GAME-LOOP-LOG.md` 的像素差列在**每一款**用这套会话建出来的游戏上永久不可得。

**本轮按任务书 §C 的口径只记录、不改动**（D-3 已登记进 `GAME-LOOP-LOG.md` 的工具缺陷表）。

### A6 顺带更正的两条

1. TASK-095 的**判别实验**（运行期新建项活、改加载期项不动）**结论成立但解释错了**：动的那个是**加在最上层的新项**，不动的那个是**被副本挡住的旧项**——与「加载期 / 运行期」这条分类无关。探针工程里正常改色的 `Background` 正是加载期节点。
2. TASK-094/095 留下的三条出路（改机器状态重测 / 影子渲染立项 / 永久接受像素不可得）**全部作废**：不需要动那台机器的任何状态，不需要影子渲染，像素证据**今天就拿得回来**（Tetris 已经拿到）。

---

## B. 像素列改为诚实的「不可得」

### B1 `GAME-LOOP-LOG.md`

* 三行（Pong / Breakout / Snake）的像素差列由 `0/55`、`0/51`、`1/52` 改为 **`不可得（D-1）`**，并各带一句为什么；Pong 那行保留 TASK-092 当轮 **10/29 非零** 这个历史事实。
* D-1 行的**层级标签**、**根因**、**状态**三格重写：三次定域（TASK-094 / TASK-095 / TASK-096）逐条列出，TASK-096 的判据统计与复现命令写进状态格；TASK-094 的 A/B 时间戳在正文里用 `00:14:53` / `01:18:26`。
* 新增 **「D-1 再定域（TASK-096）」** 一节（三条判别证据 + 对 TASK-095 的更正 + 三条旧出路的作废声明）。
* 新增工具缺陷 **D-3**（副本是怎么被写进去的、提交级证据、最小动作与根因动作、为什么本轮只记录）。
* 新增第 4 行 **Tetris**（调用数、`facts_complete`、判定分布、像素差 11/42、缺陷、证据路径）。
* 缺陷登记新增 **T-1 / T-2 / T-3**（Tetris 的三条，含前后对比）。
* 待办三条重写（第 1 条变成「照 D-3 的两层动作走」，并写明三条旧出路作废）。

### B2 `tools\game_report.py`（报告工具）

* 新增 `--pixel-evidence=auto|available|unavailable`；`auto` 的规则是：一次运行里**所有**可复算的像素差都是 0 → 判 **unavailable**。
* 判 unavailable 时：表里的 `0` 打成 **`不可得（D-1）`**（捕获行表格与 `user://` 截图表格两处），汇总行带 `— 不可得（D-1）`，并追加一段明确读法（「本表的 0 **不是**『画面确实没有变化』」+ 替代证据链指针）。
* `report.json` 新增 `pixel_evidence = {verdict, reason, note, capture_pairs, comparable_pairs, non_zero_pairs}`，使这个结论**可机读、可核对**，而不是一句形容词。
* 实测：`recovery\work\task096\reporttest-pong\report.md`（TASK-094 的 pong 重放，0/52）→

```
**capture pairs with a recomputed non-zero pixel diff: 0/52 — 不可得（D-1）**

> **PIXEL EVIDENCE UNAVAILABLE (D-1).** 不可得（D-1）: 像素证据链当时不可用 -- 场景文件里多出一整份节点副本 …
```

  Tetris 终轮（11/42 非零）则**不带**该标注，正常给出数字 —— 同一条规则在两个方向都被实测过。

### B3 `MCP-TRACEABILITY.md` §7（引擎仓）

新增 **§7 当像素证据不可得时的替代证据链（TASK-096）**：

* **§7.0 为什么这一节存在**：`0` 会被读成「画面确实没有变化」＝「操作没起作用」；`不可得` 与 `0` 是两个不同的断言。
* **§7.1 D-1 是什么**：副本层表（场景 / 具名节点 / 副本数 / 首行）+ 三条判别证据 + 副本来源的提交级证据。
* **§7.2 替代证据链（按强度排序）**：文件 sha（`file_effect_status`）> 多帧属性采样 > 断言（`result_flags=assertion_failed`）> 场景树快照 > 运行期新建画布项；每条都写明**它证明什么 / 不证明什么**，以及四条读法（其中最重要的一条：`scene_effect=unchanged` 在 D-1 存在期间**不构成「操作无效」的证据**；反过来一条带数字的像素差必须同时给出 sha、重算值与运行期新建项的对照）。

---

## C. 第 4 个游戏：Tetris（C#，只用 MCP 调用开发）

### C1 开发方式与调用数

* 工程由 `tools\new_game.ps1 -Name tetris` 从模板实例化（与前三款同一脚手架）；**游戏内容全部由 MCP 调用写成**：`project_create_script`（形状表）、`project_edit_script`（主脚本）、`editor_add_nodes_batch`（4 个场景节点）、`editor_set_node_property`（HUD 文本）、`editor_add_input_action`×5（A/D/W/S/E）、`editor_save_scene`、`project_build_csharp`、`project_validate_scripts`。
* **两轮**：首轮 `tetris-task096`（编辑器 17 + 游戏 36 = 53 次调用）建工程并暴露 3 条缺陷；终轮 `tetris-task096-r2`（编辑器 6 + 游戏 36 = **42 次调用**）**只重写脚本并重建**，**场景不再重跑**——这正是 D-3 的教训，也是 Tetris 像素证据可得的原因。
* 每轮都先过 `recovery\work\task096\check_session.py`（JSON + 每个 `board=` 的形状：20 行 × 10 列），避免 TASK-095 那种「文件本身坏掉」的会话。

### C2 调用数、判定分布、`facts_complete`（终轮，真实输出）

| | 调用数 | 判定分布 | `facts_complete` | `args_evidence` |
|---|---|---|---|---|
| 编辑器相 | **6** | `ok_file_effect_observed=2`、`ok_no_effect_observed=4` | **6/6** | `sidecar_verified=1`、`inline_complete=5` |
| 游戏相 | **36** | `failed=1`、`ok_effect_observed=8`、`ok_file_effect_observed=13`、`ok_no_effect_observed=14` | **36/36** | `inline_complete=36` |
| 合计 | **42** | `failed=1`（**声明的边界调用**：断言一个不存在的属性 → `-32001` + `suggestion`）、`ok_effect_observed=8`、`ok_file_effect_observed=15`、`ok_no_effect_observed=18` | **42/42（100%）** | — |

首轮对照：编辑器 17/17 + 游戏 36/36 = **53/53**，判定分布 `ok_effect_observed=2+8`、`ok_file_effect_observed=10+15`、`ok_no_effect_observed=5+12`、`failed=1`。两轮的 `facts_complete` 都是 100%。

### C3 证据形态（任务书 §C 要求的四类都用了）

1. **多帧属性采样**（方块下落）：`g06` 重力关闭 10 帧 → `PieceY` 恒定（确定性规则的可证伪基线）；`g07` `SetGravity(0.05)`；`g08` 30 帧 → `PieceY` 从 1 递增、`Ticks` 同步递增；`g09` 断言 `PieceY > 0` 实得 **11**。
2. **断言**（得分 / 行数 / GameOver）：`g20` `FilledCells=8`、`g22` `Lines=1`、`g23` `Score=100`、`g28` `GameOver=true`，另有 `g12/g13/g14`（右移一列 / 左移回来 / 旋转到 `PieceRot=1`）与一条**声明失败**的边界断言（`-32001`）。
3. **文件 sha**：编辑器相 6 次调用里 2 次 `file_effect=changed`（两个 `.cs`）、1 次 `unchanged`（重建后 `.cs` 内容未变的那个）、`sidecar_verified=1`（超限载荷走旁路证据并可被读侧重算）。
4. **像素差 + 运行期新建画布项**：**11/42 非零**；`user://` 四张截图两两不同 —— `tetris-t0`→`t1` **3174 px**、`t1`→`t2` **4232 px**、`t2`→`t3` **8503 px**；`g30` 在运行期 `ColorRect.new()` 造了一个 `ProbeOverlay`（`(20,540) 120×40`，青色）并截图对比，`g32` 逐帧采样确认它在树里。**这条是「回读通道当时活着」的正向对照**，也是为什么 Tetris 这一行的像素列**不需要**写「不可得」。

### C4 缺陷清单（分两栏）

**工具缺陷（`modules\mcp_server`）**

| id | 现象 | 根因 | 状态 |
|---|---|---|---|
| **D-3** | 重跑编辑器相会在场景里留下整份 `@ColorRect@*` / `@Label@*` 副本（pong 5 / breakout 18 / snake 37），它们绘制在最上层，**这就是 D-1** | `editor_add_nodes_batch` 对同名节点不拒绝也不报告；`editor_save_scene` 把自动改名的副本一并写入 | **未修（记录）**：与画布项缺陷相关，按 §C 口径等决策。最小动作与根因动作见 §A5 |
| — | Tetris 本轮**没有**发现新的工具缺陷（42/42 facts，唯一 `failed` 是声明的边界调用） | — | — |

**游戏或驱动缺陷（Tetris 首轮，三条全部已修并重跑同批对比）**

| id | 现象（首轮真实输出） | 根因 | 处置 → 终轮结果 |
|---|---|---|---|
| **T-1** | `g20-assert-filled` 期望 8 实得 **0**，`g22`/`g23` 连带失败；引擎 stdout 的 `TETRIS_FORCE` 写着 `board=…/.......... filled=0`，而同一行的 `LastEvent` 又回显了完整 spec | 会话用竖线分行，`WriteBoard` 只按 `/` 分行 → 20 行落进第 0 行、只取前 10 个字符 | **改**（`rows.Replace('|','/').Split('/')`）→ `g20` 实得 **8**、`g22` 实得 **1**、`g23` 实得 **100** |
| **T-2** | `g21-harddrop-clear` 返回 `score=0 lines=0`，而落锁后 `g29` 读回 `score=100 lines=1` —— 同一次调用的返回值与它自己的效果矛盾 | `HardDrop()` 的 `LastEvent` 在 `LockPiece()` **之前**拼好 | **改**（先落锁再拼）→ `g21` 直接返回 `harddrop … score=100 lines=1` |
| **T-3** | `g26` 用「出生行整行填满」造 GameOver，`g28` 失败；同刻却出现 `Lines=1 Score=100`（消行反发生了） | `LockPiece()` 顺序是「落锁 → 消行 → 出生」，整行会先被消掉。**游戏是对的，测试设计错了** | **改**（占住出生格 `(4,0)(5,0)` 而该行不满：`....##....`）→ `g27` 返回 `over=True`、`g28` 实得 **true**、`g29` `filled=6` |

### C5 台账新行

`GAME-LOOP-LOG.md` 第 4 行已加（调用数 42、判定分布、`facts_complete` 42/42、像素差 11/42、0/3 缺陷、证据路径 `runs\tetris\tetris-task096-r2\`）。

---

## D. 收尾

### D1 十道门（`runs\gates\task096\summary.txt`，真实退出码）

| # | 门 | 结果 |
|---|---|---|
| g01 | 模块 doctests `--test-case=[MCPServer]*` | **exit=0**（`155/155 passed`、`6613/6613 assertions`、`SUCCESS!`，8.7 s） |
| g02 | 全量 doctests `--headless --test` | **exit=0**（`1581/1581 passed / 3 skipped`、`430926/430926 assertions`，31.5 s） |
| g03 | 组 manifest | **exit=0**（`TOOL-GROUPS CHECK PASS`） |
| g04 | 契约子集（活体） | **exit=0**（`3/3 checks passed`，编辑器 9888 / 游戏 9889 / `guard_user_port_9877`） |
| g05 | 改名映射 | **exit=0**（`RESULT: PASS`） |
| g06 | 恒真断言 | **exit=0**（`TAUTOLOGY CHECK PASS`） |
| g07 | 退出码传播 | **exit=0**（`PROBES: 10/10`） |
| g08 | 硬编码计数 | **exit=0**（`UNCLASSIFIED = 0`，`RESULT: PASS`） |
| g09 | 引擎锚点 | **exit=0**（`ANCHOR_JUDGE VERDICT=ANCHOR_STRUCTURAL_EQUIVALENT`；`anchor=cf554ef58 head=8b9dd9a72 diff_count=1 safe_count=1 red_count=0`；`RESULT PASS`） |
| g10 | `accept_m1` | **exit=0**（**`22/22 cases passed`**，46.5 s） |

门 9 用真实的编译锚点 `4.8.dev.mono.custom_build.cf554ef58`（引擎二进制 `--version` 的逐字输出）；差集只有 `accept_m1.ps1` 一个非编译文件，所以是 `STRUCTURAL_EQUIVALENT` 而不是 `STALE_COMPILED`。

### D2 为什么没有重建两个变体

本轮引擎仓的**唯一**改动是 `modules/mcp_server/docs/reports/MCP-TRACEABILITY.md`（一份**纯文档**，66 行新增，零编译输入）。TASK-094 已就同一问题立过口径：**没有编译输入变化的重建会逐字节复现同一份二进制，证明不了任何事**。所以我：

* 跑了十道门与 `accept_m1`（因为它们会扫描模块目录，文档就在扫描面里）——**全部真绿**；
* **没有**重建变体，并把这条决定写在这里而不是伪装成「重建过了」；
* 后果（已知且自陈）：编译进二进制的版本字符串仍是 `cf554ef58`，而引擎仓 HEAD 现在是 `95aa1d8984`；门 9 因此判 `ANCHOR_STRUCTURAL_EQUIVALENT`（锚点 `cf554ef58` 与 `95aa1d8984` 之间的差集**全是**声明过的非编译文件）。这与 TASK-092/094 记录的自我更正同族。

### D3 提交与两个仓库

**引擎仓 `F:\moonbit-hof-rs\godot-mcp\godot`（分支 `feature/mcp-server-module-rebuild`）** — `git log --oneline -4`（提交并 push 之后）：

```
95aa1d8984 modules/mcp_server: task096 - MCP-TRACEABILITY gains section 7: what the evidence chain is when the pixel diff is unavailable, and how the ledger is to be read then; the section also carries the re-localisation of D-1 (the duplicate node layer a replayed editor phase writes into a scene), which is why the three older games' pixel column says unavailable rather than 0
8b9dd9a72b modules/mcp_server: task094 - D-2 is a load-sensitive readiness predicate, not a defect: the accept_m1 wait now asks the main loop to advance (frame_count strictly increasing six samples in a row) instead of asking it to be faster than 20 fps, so the suite is 22/22 solo and 22/22 under eight CPU burners
cf554ef58c modules/mcp_server: task092 (B2/B3/B4) step2 - a deferred call's file effects and its capture are collected at completion, the two missing doctests exist, and the frame cost is a clamped median of a window
87fbf82f4b modules/mcp_server: task092 (B1) step1 - an over-bound payload is written whole to a sidecar the line can be checked against, and the ledger re-hashes it
```

`git status --short`：**空**。`git push origin feature/mcp-server-module-rebuild` 的真实输出：

```
To github.com:shiyukonghui/godot.git
   8b9dd9a72b..95aa1d8984  feature/mcp-server-module-rebuild -> feature/mcp-server-module-rebuild
```

`git rev-parse HEAD` == `refs/remotes/origin/feature/mcp-server-module-rebuild` == `95aa1d8984fc88aa0415a3b823811fd76d76a2ad`。

**主仓 `F:\moonbit-hof-rs`（分支 `master`，无远端）** — `git log --oneline -8`：

```
1b5b108 feat(godot-mcp): TASK-096 - D-1 is neither the machine picture pipeline nor the loaded canvas items: a replayed editor phase writes a whole duplicate node layer into the scene, drawn on top, so the screen really is still; the same batch of operations is normal on a clean probe project on both engines; the pixel column becomes 'unavailable (D-1)' with the replacement evidence chain in MCP-TRACEABILITY.md section 7; and the 4th C# game Tetris is delivered through MCP calls (42/42 facts, 11/42 non-zero pixel diffs on a clean scene), with three defects fixed and re-run
813f0d0 docs(godot-mcp): TASK-095 - the report's closing section carries both repositories' real git logs and status lines, the tracked-versus-ignored accounting of the evidence set, and the post-run process and port cleanup check
9fbe917 docs(godot-mcp): TASK-095 - D-1 re-localised: the canvas items the loaded scene brings in stop re-recording their draw commands
63e0749 docs(godot-mcp): TASK-094 - the report's closing section carries the real per-gate exit codes, both repositories' logs and the reason the rebuild was deliberately not run
b42e233 docs(godot-mcp): TASK-094 - D142 in the decision log (D-1 attributed to the machine's picture pipeline and the twelve hypotheses eliminated, D-2 judged as test brittleness and its readiness predicate fixed), with the ten gate exit codes and the three accept_m1 measurements
f65fe78 docs(godot-mcp): TASK-094 - D-1 is the machine's picture pipeline, not the module: the minimal counter-example (blue/red/green background, three identical PNGs that still show the dark background, with the property read back as green), the twelve eliminated hypotheses, the same-session A/B that answers 10/29 non-zero at 00:14 and 0/29 at 02:00 on unchanged binary bytes, and the four bypasses that all fail; the pixel-diff column stays at its real 0 because no fix can be produced from inside this process
5f47949 docs(godot-mcp): TASK-093 - the report carries the two commit ids of this task and the final gate ledger
ae0b791 docs(godot-mcp): TASK-093 - the report and its evidence: eight game-side defects with before/after runs, the ten gates green, and the one environment defect that blocks pixel evidence
```

`git status --short`：有输出，但**没有一行是「已跟踪文件被改」** —— 只有 `??`（未跟踪）。逐类列出见 §D4 的入库口径。`1b5b108` 携带 `DECISIONS.md`（D144）、`GAME-LOOP-LOG.md`、`tools\game_report.py`、`projects\tetris\`（10 个文件）、`tools\sessions\tetris\`（4 个文件）与 `recovery\work\task096\` 的证据集（含 A/B 的三份 probe stdout，用 `git add -f` 入库，因为它们落在被忽略的 `runs\` 规则下）。

### D4 入库口径与清理检查

| 位置 | 文件数 | 是否入库 |
|---|---|---|
| `recovery\work\task096\`（脚本 + 探针 + 会话 + 三份 probe stdout + reporttest 的两份报告） | 25 | **入库** |
| `recovery\work\task096\reporttest-pong\` 的其余部分（pong 重放目录的副本：PNG / trace / 逐调用 json）与 `tmp_*.tscn` | 237 | **不入库**：前者是 `runs\` 的临时副本（只为验证工具改动，已入库 `report.md`/`report.json` 两份结论）；后者是两处重定向滑手的空文件（见 §E） |
| `projects\tetris\`、`tools\sessions\tetris\` | 14 | **入库** |
| `runs\tetris\*`、`runs\snake\task096-*`、`runs\gates\task096\` | 大批 | **不入库**（`.gitignore` 明写 `runs/`），盘上真实存在，本报告所有 `runs\...` 引用都是盘上路径 |

**收尾检查（跑完后立刻测）**：`tasklist /FI "IMAGENAME eq Godot*"` → **无**；`netstat -ano | findstr LISTENING` 在 `9888–9899 / 9900–9903` → **无监听**。

### D5 端口纪律

每个会话一个唯一端口并跑前检查：`9895/9896`（loadednode 重放）、`9897`（带 MCP 开关的探针）、`9898/9899`（遮挡证明）、`9900/9901`（Tetris 首轮）、`9902/9903`（Tetris 终轮）；探针 A/B 不监听端口。门 4 与门 10 使用 `9888/9889`，跑之前确认无残留。

---

## E. 铁律遵守（含两处自陈滑手）

| 铁律 | 遵守情况 |
|---|---|
| ① 禁止一切 shell 重定向 | **主体遵守**：所有运行都由 `Start-Process -RedirectStandardOutput/-RedirectStandardError` 拥有 stdout/stderr（`run_game_session.ps1`、`run_probe_ab.ps1`、`run_gates.ps1`）；会话/报告文件由 `Set-Content -Encoding UTF8` 写。**两处滑手，如实登记**：(1) 验证副本层来源时用 `git show ... > recovery\work\task096\tmp_*.tscn` 写了 4 个文件（因为当时路径写错，4 个都是 **0 字节**，已不随之入库）；(2) 用 `python tools\game_report.py ... > recovery\work\task096\reporttest-pong-print.txt 2>&1` 落了一份工具打印（已入库，作为工具改动的旁证）。两处都只落在自己的工作目录、没有覆盖任何既有文件；此后全部改用 `-OutFile` 或不落盘 |
| ② 破坏性命令默认拒绝 | 未删除、未杀任何非本任务进程、未改设备/注册表/电源/显示拓扑。唯一的「删除」是 `run_game_session.ps1` 与 `run_probe_ab.ps1` 对**自己在本次 RunTag 目录内**的产物（有 `Assert-InOutRoot` 前缀校验），以及门跑器对上一轮门的同名输出 |
| ③ 构建与运行从 cmd 启动 | 引擎一律由生成的 `.cmd` 经 `Start-Process cmd.exe /c` 启动；`dotnet build` 由 `project_build_csharp` 触发；所有 `term` 调用都在 `cmd` 终端 |
| ④ 唯一端口 + 跑前查进程与端口 | 见 §D5 |
| ⑤ 不改变机器显示或串流状态 | 未停 `GameViewer`、未改设备/注册表/电源、未接触显示拓扑。**TASK-095 提出的「改机器状态重测」本轮被证明根本不需要**（§A6） |

---

## F. 本任务产出的文件

```
recovery\work\task096\
  check_session.py               会话文件预检（JSON + board 形状），TASK-095 那类坏文件不再进流水线
  show_results.py                从一次运行里解出指定调用的 result 载荷
  make_r2.py                     生成终轮会话（去掉场景构建调用，只重写脚本 + 重建）
  run_probe_ab.ps1               A/B 运行器（一个引擎、一个探针工程、-Extra 可挂 MCP 开关）
  probe\project.godot|main.tscn|probe.gd    探针工程：加载期 Background + 网格线 + p01–p10
  sessions\occ\session.json      遮挡证明（o01–o10）
  runs\ours-8b9dd9a72b|ours-mcp-flags|stock-471\stdout.txt   A2 的三份逐行证据
  reporttest-pong\report.md|report.json                      B2 的实测（0/52 → 不可得）
  occ-responses.txt              o01/o03/o08/o10 的完整响应体
tools\sessions\tetris\
  session.json                   首轮：建工程 + 建场景 + 全部游戏相（53 次调用）
  session-r2.json                终轮：只重写脚本 + 重建 + 全部游戏相（42 次调用）
  payload\TetrisGame.cs|Tetromino.cs
projects\tetris\                 由 new_game.ps1 实例化、随后全部由 MCP 调用写成的第 4 个游戏
runs\tetris\tetris-task096-r2\   report.md / report.json / ledger-*.{txt,json} / trace-*.jsonl / shots-*
runs\gates\task096\              summary.txt 与 g01..g10 的真实 stdout/stderr
```

**一句话收尾**：TASK-096 的产出是**一次归属判定 + 一条被登记的新缺陷 + 像素证据链的诚实化 + 第 4 个游戏**——不是一次引擎修复。引擎侧只多了一份说明「像素不可得时该拿什么当证据」的文档；真正要做的事（删副本、让同名节点别静默改名）写在 `GAME-LOOP-LOG.md` 的 D-3 与 §A5 里，等决策者开口。

---

## G. 提交后的逐字复核（本报告自身的提交之后）

上面 §D3 的两段 `git log` 是本报告**写下来那一刻**的快照；本报告自身是主仓的**下一个**提交。下面这一节是提交完成后重测的逐字输出，**使 §D3 的快照不可能被本报告自己的提交改旧**。

**主仓 `F:\moonbit-hof-rs`（分支 `master`）** — `git log --oneline -8`：

```
b84bc87 docs(godot-mcp): TASK-096 - the report: the ownership A/B (the same operation batch is normal on both engines and on a clean probe project, so the answer is neither our regression nor an upstream behaviour nor the presentation layer but the duplicate node layer a replayed editor phase writes into a scene), the occlusion proof with its recomputable colours, the pixel column becoming unavailable (D-1) with the replacement evidence chain, and the 4th C# game Tetris with its three fixed defects and their before/after runs
1b5b108 feat(godot-mcp): TASK-096 - D-1 is neither the machine picture pipeline nor the loaded canvas items: a replayed editor phase writes a whole duplicate node layer into the scene, drawn on top, so the screen really is still; the same batch of operations is normal on a clean probe project on both engines; the pixel column becomes 'unavailable (D-1)' with the replacement evidence chain in MCP-TRACEABILITY.md section 7; and the 4th C# game Tetris is delivered through MCP calls (42/42 facts, 11/42 non-zero pixel diffs on a clean scene), with three defects fixed and re-run
813f0d0 docs(godot-mcp): TASK-095 - the report's closing section carries both repositories' real git logs and status lines, the tracked-versus-ignored accounting of the evidence set, and the post-run process and port cleanup check
9fbe917 docs(godot-mcp): TASK-095 - D-1 re-localised: the canvas items the loaded scene brings in stop re-recording their draw commands
63e0749 docs(godot-mcp): TASK-094 - the report's closing section carries the real per-gate exit codes, both repositories' logs and the reason the rebuild was deliberately not run
b42e233 docs(godot-mcp): TASK-094 - D142 in the decision log (D-1 attributed to the machine's picture pipeline and the twelve hypotheses eliminated, D-2 judged as test brittleness and its readiness predicate fixed), with the ten gate exit codes and the three accept_m1 measurements
f65fe78 docs(godot-mcp): TASK-094 - D-1 is the machine's picture pipeline, not the module: the minimal counter-example (blue/red/green background, three identical PNGs that still show the dark background, with the property read back as green), the twelve eliminated hypotheses, the same-session A/B that answers 10/29 non-zero at 00:14 and 0/29 at 02:00 on unchanged binary bytes, and the four bypasses that all fail; the pixel-diff column stays at its real 0 because no fix can be produced from inside this process
5f47949 docs(godot-mcp): TASK-093 - the report carries the two commit ids of this task and the final gate ledger
```

`git status --short`（剔除未跟踪行后）：**空 —— 没有任何已跟踪文件处于被改状态**；未跟踪的只有 §D4 说明的那两类（`reporttest-pong\` 的临时副本、4 个 0 字节 `tmp_*.tscn`）。

**引擎仓 `F:\moonbit-hof-rs\godot-mcp\godot`（分支 `feature/mcp-server-module-rebuild`）** — `git log --oneline -4` 与 `git status --short`：

```
95aa1d8984 modules/mcp_server: task096 - MCP-TRACEABILITY gains section 7: what the evidence chain is when the pixel diff is unavailable, and how the ledger is to be read then; the section also carries the re-localisation of D-1 (the duplicate node layer a replayed editor phase writes into a scene), which is why the three older games' pixel column says unavailable rather than 0
8b9dd9a72b modules/mcp_server: task094 - D-2 is a load-sensitive readiness predicate, not a defect: the accept_m1 wait now asks the main loop to advance (frame_count strictly increasing six samples in a row) instead of asking it to be faster than 20 fps, so the suite is 22/22 solo and 22/22 under eight CPU burners
cf554ef58c modules/mcp_server: task092 (B2/B3/B4) step2 - a deferred call's file effects and its capture are collected at completion, the two missing doctests exist, and the frame cost is a clamped median of a window
87fbf82f4b modules/mcp_server: task092 (B1) step1 - an over-bound payload is written whole to a sidecar the line can be checked against, and the ledger re-hashes it
```

`git status --short`：**空**；`HEAD == origin/feature/mcp-server-module-rebuild == 95aa1d8984fc88aa0415a3b823811fd76d76a2ad`。

