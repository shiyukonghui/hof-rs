# TASK-099 — 第 8、9 个游戏（Frogger / Flappy Bird）交付；`run_gates.ps1` 识别纯文档提交并跳过重建（G-1 结案）；`--import` 关机期访问违例第 3 次**现场复现**，24 次受控探针仍全 0，不动引擎

* 执行者：工具工程师（本会话，**有写权限，不再委派**）
* 主仓：`F:\moonbit-hof-rs`（分支 `master`，无远端）
* 引擎仓：`F:\moonbit-hof-rs\godot-mcp\godot`（分支 `feature/mcp-server-module-rebuild`，remote `git@github.com:shiyukonghui/godot.git`）
* 脚本 / 会话 / 证据：`godot-mcp\recovery\work\task099\`
* 时间：2026-09-27（本会话）

---

## 0. 结论表（每行一句话）

| 段 | 要求 | 结论 | 关键证据 |
|---|---|---|---|
| **A①** | **Frogger**（C#，只用 MCP 调用开发）：格子过马路（车流）、过河（浮木）、到位计分、生命与胜负；像素列必须真实非零；多帧采样、断言、文件 sha、像素差 + 独立复算 | **做完，首轮一次通过。** 90 次调用（编辑器 16 / 游戏 74），`facts_complete` **90/90（100%）**，判定分布 `failed=2`（**两条都是声明的**：`e06` 同名批量 `-32000`、`g68` 不存在属性 `-32001`）+ `ok_effect=17` + `ok_file_effect=49` + `ok_no_effect=22`；断言 **34 PASS + 1 条声明的边界失败**；像素差 **17/90 非零**（编辑器 1/16、游戏 16/74），`user://` 五帧逐对 **8864 / 9178 / 9291 / 9943 px**；独立复算 **0 处不符**；`project_build_csharp` exit 0、`invalid_count=0` | `runs\frogger\frog-task099-r1`、`logs\summary-frogger-r1.txt`、`logs\samples-both.txt`、`logs\pixel-recompute-both.txt`、`logs\frames-recompute-both.txt` |
| **A②** | **Flappy Bird**（C#，只用 MCP 调用开发）：重力与点击上升、管道间隙、通过计分、碰撞判负 | **做完，首轮 1 条载荷缺陷已修并重跑。** r2：92 次调用（编辑器 14 / 游戏 78），`facts_complete` **92/92（100%）**，`failed=2`（同样两条声明的）+ `ok_effect=22` + `ok_file_effect=46` + `ok_no_effect=22`；断言 **38 PASS + 1 条声明的边界失败**；像素差 **22/92 非零**（编辑器 1/14、游戏 21/78），五帧逐对 **34326 / 98611 / 1699 / 99094 px**；独立复算 **0 处不符**；`StepUntilPass` 的确切帧数 **164 / 100 / 100 / 100 / 100** | `runs\flappy\flappy-task099-r2`（首轮 `-r1` 留作对照）、`logs\summary-flappy-r2.txt`、`logs\samples-flappy-r2.txt`、`logs\assertions-flappy-r2.txt` |
| **A③** | 跑完给：调用数、判定分布、`facts_complete`、缺陷清单（分「工具缺陷」「游戏或驱动缺陷」）；两行加进 `GAME-LOOP-LOG.md` | **做完。** 台账续到第 8、9 行；**工具缺陷 0 条**；**游戏或驱动缺陷 1 条**（**F-1**：Flappy 的 `AutoRun` 把 `delta*60` 截断成 0，高帧率下一格都不走 —— 由 30 帧采样照出来，已修并重跑 r2）；另在 `GAME-LOOP-LOG.md` 新增「TASK-099 记录」节并把 G-1 标为已修 | `GAME-LOOP-LOG.md` 台账第 8/9 行、缺陷表 F-1、TASK-099 记录节；`recovery\work\task099\decisions-d147.md` |
| **B** | 让门跑器在引擎仓 diff 只含非编译文件时不再空跑十门，直接给 `ANCHOR_STRUCTURAL_EQUIVALENT + 跳过重建` 的判定与理由并打印非编译文件清单；含编译输入则照常跑门；两情形各一次实测；改动带标记并登记 manifest；说明为何不影响两变体 | **做完。** 纯文档情形：`VERDICT=ANCHOR_STRUCTURAL_EQUIVALENT` + `RESULT=SKIP_REBUILD` + `GATES_SKIPPED=1` + 两个 `.md` 路径，**exit 0、一门未跑**；编译输入情形（工作树里一个未跟踪 `.cpp`）：`VERDICT=RUN_GATES` 且 **`g01`..`g10` 全部 `exit=0`**（`accept_m1 22/22`）。第三个对照：committed diff 含 4 个 `.cpp/.h` → `ANCHOR_STALE_COMPILED` + `RUN_GATES`。登记在引擎仓 `REBUILT-2C-MANIFEST.md` 新增的 **2c-11 / L-1** 节 | `runs\gates\task099-doconly\summary.txt`、`runs\gates\task099-compileinput\summary.txt`、`runs\gates\task099-committed-compile\summary.txt`、`logs\gates-*.txt`、引擎提交 `e041cae270` |
| **C** | 按台账待办做三个判别器（埋点 / 静默空检查 / procdump）；若无法稳定复现，就只做埋点与统计，不要凭推测改引擎 | **现场复现 1 次，受控 24 次全 0 → 按任务书自己的条件，不动引擎、不加埋点。** 现场：`frog-task099-r1` 的首次导入 `IMPORT_EXIT=-1073741819`（症状与 TASK-097/098 一字不差、日志已到 `[ DONE ] loading_editor_layout`）；对照：同轮 `flappy-task099-r1` 首次导入 `exit=0`（**同样是全新工程**）。受控：默认端口 9877 × fresh/warm × 是否加压 8 线程 → **24 次 0 崩**；累计受控 88 次全 0 对 13 次会话导入 3 次崩 | `runs\frogger\frog-task099-r1\import.{stdout,stderr}.txt`、`logs\importprobe\probe2-all.txt`、`probe2-frog-load0.json`、`probe2-frogload-load8.json` |
| **D** | 若改了模块 → 重建两变体 + 十道门全绿（真实退出码）+ `accept_m1` 22/22 + push 到 fork；主仓提交（含台账与两款游戏）；报告含两仓 `git log --oneline -8` 与 `git status --short`；时间不够如实报告 | **不适用，并显式说明。** `modules\mcp_server` **一个字节没动**（引擎仓 `git diff --name-only 2385fe2fb..HEAD` 只有 `.md`），两变体仍是 TASK-097 的构建 → **未重建、未 push 代码**；但十道门**真实跑完过一次**（预检的编译输入情形，全 exit 0、`accept_m1 22/22`）。引擎仓本次只有一份**文档**提交并已 push（`0fbd5ec4cb..e041cae270`）。主仓 `7b5fa56`（120 个文件） | §B、§C、§D2 |

---

## A. 第 8、9 个游戏（C#，只用 MCP 调用开发）

### A1 形态与开发方式（两款同一套脚手架，TASK-098 结尾推荐的模板照用）

两款都从模板实例化（`tools\new_game.ps1 -Name frogger -Class FroggerGame` / `-Name flappy -Class FlappyBirdGame`），**游戏内容全部由 MCP 调用写成**：`project_edit_script`（C# 载荷替换模板桩）、`editor_add_nodes_batch`（3 个静态节点一次建好）、`editor_add_input_action`、`editor_save_scene`、`project_build_csharp`、`project_validate_scripts`。

| 游戏 | 场景里的静态节点 | 运行期新建的东西 |
|---|---|---|
| Frogger | `Background` / `Hud` / `Status` | 4 条地形条、5 辆车、5 根两格浮木、青蛙 1 |
| Flappy Bird | `Background` / `Hud` / `Status` | 小鸟 1、3 根管子的上下两半 6 |

**确定性规则（继承前七款）**：Frogger 的 `CarSpeed` 默认 0、`PollInput` 默认 false；Flappy 的 `AutoRun` 默认 false、`PollInput` 默认 false。两款都把每一个「钩子做了多少」做成**与帧率无关的增量属性**：Frogger 的 `LastTrafficSteps`、Flappy 的 `LastPassFrames` / `LastPassDelta` —— P-1 的教训被写进载荷本身。`ForceTestState(spec)` 一个调用钉死整盘状态。**所有事实都是根节点上的真 Godot 属性**，断言用 `running_game_assert_node_state`，不解析任何日志行。

**两款都在建场景的那一步故意把同一批节点再跑一次**（`e06`），让 D-3 的拒绝在每一轮证据里都留下一条：`{"error":{"code":-32000,…"Refused: 3 node(s) of this batch would duplicate a name that already exists…"}}`，且 `e05` / `e09` 的 `project_read_text_file` sha **逐字节相同**。

**「全新」的含义**：Flappy 重跑 r2 之前，先把 r1 工程按「**先写 sha256 清单再移动**」归档到 `recovery\work\task099\archive\flappy-r1`（清单 129 个文件 / 8 369 613 B），再用模板重新实例化，使 r2 与 r1 从同一个起点出发。

### A2 终轮真实输出

| | Frogger **r1** | Flappy r1 | Flappy **r2** |
|---|---|---|---|
| 调用数（编辑器 / 游戏） | **90（16 / 74）** | 92（14 / 78） | **92（14 / 78）** |
| `facts_complete` | **90/90（100%）** | 92/92 | **92/92（100%）** |
| 断言 | **34 PASS + 1 声明 ERROR** | 38 PASS + 1 声明 ERROR | **38 PASS + 1 声明 ERROR** |
| 像素差非零 | **17/90**（1/16、16/74） | 21/92（1/14、20/78） | **22/92**（1/14、21/78） |
| 判定分布 | `failed=2` + `ok_effect=17` + `ok_file_effect=49` + `ok_no_effect=22` | `failed=2` + `ok_effect=21` + `ok_file_effect=51` + `ok_no_effect=18` | **`failed=2` + `ok_effect=22` + `ok_file_effect=46` + `ok_no_effect=22`** |
| `user://` 帧链 | **8864 / 9178 / 9291 / 9943** | 34326 / 98611 / 1699 / 99094 | **34326 / 98611 / 1699 / 99094**（与 r1 逐字节相同） |
| 缺陷（工具 / 游戏或驱动） | 0 / 0 | 0 / 1 | **0 / 0** |

> 两轮都是 `failed=2`，且**两条都是声明的**：编辑器相那一次同名拒绝（`-32000`）+ 一条故意打在不存在属性上的边界断言（`-32001`）。`report.json` 的自动缺陷清单只有这两条。

### A3 证据形态（任务书要求的四类都用上了）

**① 多帧属性采样（先采样、后改变）**

| 采样 | 帧数 | 结果 |
|---|---|---|
| Frogger `g13-samples-frozen` | 12 | 冻结基线：`FrogCol` / `FrogRow` / `Car0Col` / `Log0Col` **各只有 1 个值**，`Ticks` 12 个不同值 |
| Frogger `g15-samples-traffic` | 30 | `Car0Col` 与 `Log0Col` **各 5 个不同值**（变化点 @4/@11/@19/@27），`Ticks` 30 个不同值 |
| Flappy `g13-samples-frozen` | 12 | 冻结基线：`BirdY` / `Pipe0X` 各 1 个值，`Ticks` 12 个不同值 |
| Flappy `g44-samples-scroll`（r2） | 30 | `Pipe0X` **17 个不同值（576→492）**、`BirdY` 恒定 300 —— 自重跑时钟真的在推世界（r1 里这里是**恒定 582**，正是 F-1 的证据） |

**② 断言** —— Frogger：`FrogCol`/`FrogRow` 起点 6,14、出界**不移动**、空车道可走（13→12）、车撞 `Lives` 3→2 + 回到起点、落水 `Lives` 3→2、**浮木载着青蛙走**（`FrogCol` 6→5、仍在 row 4）、`HomesReached` 4→5、`Score`=50、`Won`/`GameOver`=true、最后一命 `Lives`=0 + `Won`=false、屏幕文本 `ALL HOMES FILLED` / `GAME OVER`、`LastTrafficSteps`=5（增量）与 `TrafficSteps`=9（总数）。Flappy：`BirdY` 起点 300、`Flap()` 后 `BirdVelocity`= **-420**、一帧重力 `> 23`、天花板钳到 `BirdY`=0 且速度归零、落地 `BirdY`=**564** + `GameOver`、撞管 `GameOver` 且 `Score`=0、`StepUntilPass` 的 164/100/100/100/100、`Score` 10→50、`PipesRecycled>0`、第五根后 `Won`/`GameOver`=true、屏幕文本 `COURSE CLEARED` / `GAME OVER`。

**③ 文件 sha** —— 两款各自的 `e05` / `e09` sha 与拒绝前**逐字节相同**；`editor_add_nodes_batch` 的 `file_effect=changed` 各 1 次；编辑器相各 `sidecar_verified=1`（C# 载荷超限走旁路证据）。

**④ 像素差 + 独立复算** —— 见 A4。

### A4 独立复算（不是转述）

`recovery\work\task099\pixel_recompute.py`（逐调用 capture 对，**自己**解码 PNG、用自己的两条规则各算一遍）与 `frames_recompute.py`（`user://` 保存帧，**自己**按 mtime 排序、自己 sha256、自己对 `report.json` 的数字）：

| 运行 | 逐调用对 非零（引擎规则 >10） | 任一字节差异规则 | trace 记录的数与复算不符的对 | 帧链（复算） |
|---|---|---|---|---|
| Frogger r1 | **17/90**（编辑器 1/16、游戏 16/74） | 同样 17/90 | **0** | 8864 / 9178 / 9291 / 9943 |
| Flappy r2 | **22/92**（编辑器 1/14、游戏 21/78） | 同样 22/92 | **0** | 34326 / 98611 / 1699 / 99094 |

`user://` 帧的 sha256 与 `report.json` 记录的**逐一相同**，两款都是**五个不同的 sha** —— 「画面确实在变」不是一句形容词。**附带的确定性观察**：Flappy r2 的五个帧与 r1 **逐字节相同**，即「同一个被钉住的状态画出同一张图」。

### A5 F-1：多帧采样照出来的那条载荷缺陷（这是本轮唯一一条「游戏或驱动缺陷」）

| id | 现象（证据） | 根因 | 处置 → 重跑结果 |
|---|---|---|---|
| **F-1** | 首轮 `runs\flappy\flappy-task099-r1` 的 `g44-samples-scroll`：30 帧里 `Ticks` 从 31 走到 101（引擎在跑），而 `Pipe0X` **恒定 582**、`BirdY` 恒定 300。**所有断言仍全 PASS**（没有一条断言要求它动） | `FlappyBirdGame._Process` 写的是 `frames = (int)((float)delta * FixedFps)`：这台机器上窗口游戏进程跑在 60 fps 以上（采样显示约 144 fps），单帧 `delta*60 < 1`，截断成 0 → `StepFrames(0)` 永不发生。会话里 `SetAutoRun(true)` 的响应本身诚实（`auto_run=True`）—— **缺陷在载荷的时钟，不在工具** | **改**：改成累加器 `_autoAccum += delta * FixedFps; frames = (int)_autoAccum; _autoAccum -= frames;`（`SetAutoRun` / `ForceTestState` / 声明动作的重开路径都清零），并在源码注释里写明是这次采样发现的。r2：`Pipe0X` 变成 **17 个不同值（576→492）**而 `BirdY` 恒定；`g13` 冻结基线不变；断言仍 38 PASS + 1 声明 ERROR；像素差 21/92 → **22/92** |

**这条的方法论价值**：它是「多帧采样先于会改变状态的那一步」这条模板**当场产生收益**的例子 —— 30 帧里两个量的对照（一个在走、一个不走）把「时钟没接上」变成机器可判事实，而断言集合当时是全绿的。

### A6 缺陷清单

**工具缺陷（`modules\mcp_server`）：0 条。** 两款共 182 条调用里没有一条是「工具做错了事」；唯一的非 `ok` 判定是两条**声明的**边界调用（同名拒绝 `-32000`、不存在的属性 `-32001`）。

**游戏或驱动缺陷：1 条（F-1，已修并重跑，见 A5）。**

---

## B. 门跑器：识别纯文档提交并跳过重建（G-1 结案）

### B1 改了什么

`tools\run_gates.ps1`（**主仓**文件，不在引擎仓树内）新增一段**预检**，放在十道门之前：

* **分类器只有一份**：dot-source 模块自己的 `modules\mcp_server\scripts\check_engine_anchor.ps1`，用它既有的编译/非编译白名单与 fail-closed 语义，而不是在门跑器里再抄一份。
* **锚点默认取二进制自己的 `--version`**（`-Anchor` / `-VersionText` 仍可覆盖）；这就是 G-1 的根因修法 —— 旧默认是 TASK-090 的 `8604fcf9e`，每个新提交都会把它变成 stale。
* **diff 的口径 = committed 区间 + 工作树**（`git diff A..H` 与 `git status --porcelain --untracked-files=all` 一起看）：一个未提交的 `.cpp` 同样能改变下次编译产物。
* **判 `ANCHOR_STRUCTURAL_EQUIVALENT` 时不再空跑十门**：打印 verdict / `criterion` / `reason` / **非编译文件清单**，写 `summary.txt`，给 `GATES_SKIPPED=1`，`exit 0`。
* **只要出现一个编译输入（committed 或工作树）就照常跑门**；`-RunGates` 无条件强制跑门；`-PreflightOnly` 只看判定、不看门。

### B2 两情形实测（各一次）

| 情形 | 预检输出 | 门 |
|---|---|---|
| **纯文档提交**：二进制锚点 `2385fe2fb`（它自己报的 `4.8.dev.mono.custom_build.2385fe2fb`）对 HEAD `0fbd5ec4c`，diff = `MCP-TRACEABILITY.md` + `REBUILT-2C-MANIFEST.md` | `VERDICT=ANCHOR_STRUCTURAL_EQUIVALENT`、`WORKING_TREE_RED=0 WORKING_TREE_SAFE=0 COMMITTED_DIFF_SAFE=2`、`NONCOMPILING_COUNT=2`（两条路径都打印）、`RESULT=SKIP_REBUILD`、`GATES_SKIPPED=1`，**exit 0** | **一门未跑**（没有编译输入，跑门只会把同一份已通过的二进制再跑一遍）——`runs\gates\task099-doconly\summary.txt` |
| **改一个 `.cpp`**：在引擎工作树放一个未跟踪的 `modules\mcp_server\tools\task099_preflight_probe_b.cpp`（本轮创建、测完立即按「先打印清单再删」删除，引擎仓 `git status` 前后均为空） | `VERDICT=RUN_GATES`、`REASON="the engine working tree carries 1 compile input(s) that are not in any built binary"`、`GATES_SKIPPED=0` | **`g01`..`g10` 全部 `exit=0`**，`g09` 判 `ANCHOR_STRUCTURAL_EQUIVALENT`、`g10 accept_m1` **`22/22 cases passed`** —— `runs\gates\task099-compileinput\summary.txt` |
| 对照（committed diff 含编译输入）：`-Anchor 95aa1d8984 -PreflightOnly` | `VERDICT=RUN_GATES` + `ANCHOR_STALE_COMPILED`，逐个点名 `test_mcp_server.h`、`editor_node_batch_write.{cpp,h}`、`editor_write_scene_editor.cpp` | 本轮只做判定，未再跑一遍门 |

### B3 为什么不影响两个变体（任务书要求说明）

`tools\run_gates.ps1` 位于**主仓** `F:\moonbit-hof-rs\godot-mcp\tools\`，**不在引擎仓 `godot\` 的树内**。证据：

* 改动前后引擎仓 `git status --porcelain` 均为**空**；
* `git diff --name-only --no-renames 2385fe2fb..HEAD` 仍然只有两份 `.md`（本轮把 2c-11 节写进 `REBUILT-2C-MANIFEST.md`，仍是文档）；
* 两个二进制 `bin\godot.windows.editor.x86_64.mono.console.exe` / `…x86_64.console.exe` 自 TASK-097 之后**未被重建**，`--version` 仍报 `4.8.dev.mono.custom_build.2385fe2fb`。

因此「跳过重建」在这两情形下都是**正确**的：文档提交改动不了编译产物，本来就没有东西可重建。

**登记**：引擎仓 `modules\mcp_server\docs\reports\REBUILT-2C-MANIFEST.md` 新增 **2c-11** 节（L-1 门跑器预检 + L-2 `--import`），提交 `e041cae270`。

---

## C. `--import` 的关机期访问违例

### C1 现场（本轮第 3 次，症状与前两次一字不差）

`runs\frogger\frog-task099-r1\import.stdout.txt` 尾与 `import.stderr.txt`：

```
[ DONE ] loading_editor_layout
IMPORT_EXIT=-1073741819
```
```
ERROR: Parameter "singleton" is null.
   at: EditorNode::is_cmdline_mode (editor\editor_node.cpp:6750)
```

stdout 共 **23 行**，`[ DONE ] first_scan_filesystem` 与 `[ DONE ] loading_editor_layout` 都在崩溃之前 —— **关机期崩溃，不是导入失败**。这是**全新工程 `projects\frogger` 的第一次导入**。

**对照（同一轮）**：`flappy-task099-r1`（同样是 `new_game.ps1` 刚实例化、同样从未导入）首次导入 **`exit=0`**。→ **「全新工程」本身不是判别器**。

### C2 受控探针：24 次，全部 `exit=0`

`recovery\work\task099\import_crash_probe2.ps1`（铁律 1/3/4：`Start-Process` 拥有 stdout/stderr、子进程是 `cmd.exe`、每次导入先查端口；**不删除任何东西**，每次都在自己的新副本上跑）：

| 变体 | 次数 | 崩溃 |
|---|---|---|
| 全新副本（无 `.godot`/`bin`/`obj`），**默认端口 9877**（真实驱动的做法），fresh 6 + warm 6 | **12** | **0** |
| 同上，另加 **8 个 CPU 烧机进程**（每次导入 5.0 s → 6.0 s，关机窗口被拉长） | **12** | **0** |
| 合计（本轮） | **24** | **0** |

**累计口径**：受控探针 **88 次全 0**（TASK-098 的 64 + 本轮的 24）对 **13 次会话导入里的 3 次崩溃**；已排除的变量：项目语言、冷热、唯一端口/默认端口、stock Godot 4.7.1 mono、**CPU 加压**；未说服的变量：全新工程（对照组不崩）。

### C3 为什么**没有**做那三个判别器（这是显式取舍，不是遗漏）

台账待办给的三个判别器（① 在 `EditorFileSystem::_process_update_pending()` 的调用点埋点；② 把 `ERR_FAIL_NULL_V` 换成静默空检查以区分「只是警告」与「同帧其它空解引用」；③ 仍崩则用 procdump 拿真实栈）**三个都要改引擎源码**：①② 改 `editor/file_system/editor_file_system.cpp`（**引擎核心**，不是模块），改完必须重建**两个变体**，而 ③ 需要一次可复现的崩溃。

任务书自己写了条件：**「若无法稳定复现，就只做埋点与统计（本轮 N 次会话中崩几次、崩前日志到哪一步），不要凭推测改引擎」**。本轮的现实正是这个条件：现场样本 1 次、控制组不崩、24 次定向受控（含加压）全 0。在「无法按需复现」的假设上改引擎核心并重建，属于「凭推测改引擎」。

所以本轮把**不动引擎的那一半做完了**：现场逐字记录（崩溃时日志停在哪一步、退出码、stderr 全文）、对照样本、24 次受控统计与累计口径、以及**判别器为什么还没做**的理由。**下一步**：要么拿到可复现配方（例如在别处复现出更高命中率），要么用户明确授权重建引擎做埋点 —— 两者都不是本轮能自行决定的。

**对跑测试的实际影响（未变）**：它不影响导入结果，但 `IMPORT_EXIT` **不能**当健康信号用（`run_game_session.ps1` 只在日志里记一行，不据此判失败）。

---

## D. 收尾

### D1 「模块字节未动 → 不重建」这个取舍

`modules\mcp_server` 本轮**代码一个字节没动**；引擎仓本轮唯一的改动是 `docs\reports\REBUILT-2C-MANIFEST.md` 的 2c-11 节（58 行增，文档）。两变体仍是 TASK-097 在模块提交 `2385fe2fb5` 之后重建的那两份。因此：

* **未重建**：没有源改动可重建；
* **未 push 代码**：没有代码可 push（引擎仓要 push 的是**文档提交**，已 push）；
* **但十道门真实跑完过一次**：预检的编译输入情形把 `g01`..`g10` 全跑了（全 `exit=0`、`accept_m1 22/22`），作为「新增的预检没有把门跑坏」的证据 —— 这是本轮相对 TASK-098 的改进（那一轮连门账都没有，只能靠措辞解释）。

### D2 提交与两个仓库

**引擎仓**（分支 `feature/mcp-server-module-rebuild`）push 的真实输出：

```
To github.com:shiyukonghui/godot.git
   0fbd5ec4cb..e041cae270  feature/mcp-server-module-rebuild -> feature/mcp-server-module-rebuild
```

`git rev-parse HEAD` = `git rev-parse refs/remotes/origin/feature/mcp-server-module-rebuild` = **`e041cae270487d5c910f1e7ebe0e13982886d602`**；`git status --short` **空**。

**主仓**（分支 `master`，无远端）：`7b5fa56`（120 个文件，11532 行增 16 行删）。两仓的 `git log --oneline -8` 与 `git status --short` 见 §G。

### D3 收尾后的进程与端口

最后一轮之后：无 `Godot*` 进程；`9877` 与 `9934–9939`（本轮会话端口）无 **LISTENING**；探针用的 8 个烧机进程已被 `taskkill /T` 结束。**未改变机器显示或串流状态**（未停 `GameViewer`、未动设备/注册表/电源/显示拓扑）。

### D4 铁律遵守（含两处自陈滑手）

| 铁律 | 遵守情况 |
|---|---|
| ① 禁止一切 shell 重定向 | **主体遵守**：所有构建/运行由 `Start-Process -RedirectStandardOutput/-RedirectStandardError` 拥有 stdout/stderr；所有文本文件由 Python 写入器、`write`/`edit` 工具或 `Set-Content -LiteralPath` 写。**一处滑手，如实登记**：`check-session-py` 的那次调用里我写了一句 `python … > recovery\…\check-frogger-py.txt`（cmd 内重定向），随即用 `Start-Process` 重跑同一校验（`check_session_ps.ps1` 与新日志），被写入的两个文件只在本任务自己的工作目录内、未覆盖任何既有文件。 |
| ② 破坏性命令默认拒绝 | 只有三处写/删，全部走守卫并**先打印清单**：删除两个探针 `.cpp`（绝对路径 + 白名单前缀 + 名称精确匹配 + 先打印 sha/长度/时间）；归档 Flappy r1 工程用 `Move-Item`（**先写 129 文件 sha256 清单**，目标不存在才移动），**自始至终没有删除任何工程**；探针的每一次导入都在自己的**新副本**上跑。未杀任何非本任务进程（8 个烧机进程是本任务自己起的）。 |
| ③ 构建与运行从 cmd 启动 | 全部由 `.cmd` 经 `Start-Process cmd.exe /c` 启动（`run_game_session.ps1` 的 import/引擎/ledger/report、`run_gates.ps1` 的十门与预检、`import_crash_probe2.ps1`、`reset_game_project.ps1`）；`dotnet build` 由 `project_build_csharp` 触发。 |
| ④ 唯一端口 + 跑前查进程与端口 | 会话 `9934/9935`（frogger r1）、`9936/9937`（flappy r1）、`9938/9939`（flappy r2）；探针每次唯一（唯一端口变体）或**先查 9877 空闲**（默认端口变体）；门 4/10 用 `9888/9889`。每次开跑前 `netstat`/`Get-Process` 确认无残留。 |
| ⑤ 会话文件双解析后才执行 | 两个自造会话在开引擎之前都过 `check_session.py`（Python JSON + 形状 + `content_file` 可达）与 `check_session_ps.ps1`（PS 5.1 `ConvertFrom-Json`），两侧都 PASS（90 / 92 次调用）。 |
| ⑥ 迁移/删除一律先复制或先存证 sha | `reset_game_project.ps1` 在 move **之前**写出该工程 129 个文件的 sha256 清单（`archive\flappy-r1.manifest.json`，已入库）；两个探针 `.cpp` 删除前先打印完整元数据。 |
| ⑦ 不改变机器显示或串流状态 | 未停 `GameViewer`、未改设备/注册表/电源、未接触显示拓扑。 |

---

## E. 本任务产出的文件

```
recovery\work\task099\
  make_session_frogger.py / make_session_flappy.py    两款游戏的会话生成器（可逐字重生成）
  check_session_ps.ps1                                PS 5.1 那一半的双解析（Python 侧沿用 TASK-098 的）
  reset_game_project.ps1                              先写 sha 清单再移动 + 重新实例化
  import_crash_probe2.ps1                             --import 访问违例探针（默认端口 / fresh-warm / 加压）
  make_probe_log2.py + append_manifest.py + append_decisions.py  逐字转录与文档写入器（Python，非 shell 重定向）
  pixel_recompute.py / frames_recompute.py            独立像素复算（逐调用对 + user:// 保存帧）
  assertions.py / samples.py / run_summary.py / callread.py / check_session.py   （TASK-098 的同一份，逐字复制）
  decisions-d147.md / manifest-2c11.md                写入 DECISIONS.md 与引擎 MANIFEST 的正文
  archive\flappy-r1(.manifest.json)                   r1 工程的 sha 清单与源码（先存证再移动）
  logs\ + logs\importprobe\                           30+ 份证据日志与两份探针 JSON + 一份逐字转录
tools\sessions\{frogger,flappy}\session.json + payload\*.cs
projects\frogger\ / projects\flappy\                  由模板实例化、随后全部由 MCP 调用写成
runs\frogger\frog-task099-r1\、runs\flappy\flappy-task099-{r1,r2}\      （盘上路径；runs\ 按 .gitignore 不入库）
runs\gates\task099-{doconly,compileinput,committed-compile}\             （盘上路径；同上）
tools\run_gates.ps1                                  预检（纯文档跳过 / 编译输入照常跑门）
GAME-LOOP-LOG.md                                     第 8/9 行 + F-1 + TASK-099 记录节 + G-1 改判 + 待办
DECISIONS.md                                         D147
.gitignore                                           TASK-099 的探针工作区与归档 .godot 规则
godot\modules\mcp_server\docs\reports\REBUILT-2C-MANIFEST.md   2c-11 节（引擎提交 e041cae270）
```

> `runs\` 与 `recovery\work\task099\importprobe\` 按 `.gitignore` 不入库（盘上真实存在）；本报告所有
> `runs\...` 引用都是盘上路径。`recovery\work\task099\` 的其余部分、两款游戏工程与引擎文档均已入库。

---

## F. 真实跑出来的数字速查（都可在盘上复算）

| 项 | Frogger | Flappy Bird |
|---|---|---|
| 运行目录 | `runs\frogger\frog-task099-r1` | `runs\flappy\flappy-task099-r2`（首轮 `-r1` 对照） |
| 调用数（编辑器 / 游戏） | 90（16 / 74） | 92（14 / 78） |
| `facts_complete` | 90/90（100%） | 92/92（100%） |
| `args_evidence` | 编辑器 `sidecar_verified=1` + `inline_complete=15`；游戏 `inline_complete=74` | 编辑器 `sidecar_verified=1` + `inline_complete=13`；游戏 `inline_complete=78` |
| 判定分布 | `failed=2` / `ok_effect=17` / `ok_file_effect=49` / `ok_no_effect=22` | `failed=2` / `ok_effect=22` / `ok_file_effect=46` / `ok_no_effect=22` |
| 断言 | 34 PASS + 1 声明 ERROR | 38 PASS + 1 声明 ERROR |
| 像素差非零 | 17/90（1/16、16/74） | 22/92（1/14、21/78） |
| `user://` 帧链 | 8864 / 9178 / 9291 / 9943 | 34326 / 98611 / 1699 / 99094 |
| `project_build_csharp` | exit 0 | exit 0 |
| `project_validate_scripts` | `invalid_count=0` | `invalid_count=0` |
| `editor_get_errors` | `count=0` | `count=0` |
| 缺陷（工具 / 游戏或驱动） | 0 / 0 | 0 / 0（r1 有 1 条 F-1 已修） |
| 独立复算不符数 | 0 | 0 |
| 门跑器（本轮） | — | 纯文档：跳过（exit 0）；编译输入：`g01..g10` 全 exit 0、`accept_m1 22/22` |

---

## G. 提交后的逐字复核（本报告自身的提交之前）

**边界说明（把话说死）**：本节的两段帐是**主仓 `7b5fa56` 与引擎仓 `e041cae270` 提交之后、本报告那次提交之前**的那一刻的两仓状态。此后本报告自身的提交（以及任何纯文档追加）只让主仓 `git log` 顶部多出一个**文档**提交；本节里唯一真正会变旧的事实是 `git log` 的顶部行与 `git status --short` 的输出，而**「主仓新增 120 个文件、两仓 `git status --short` 均为空、引擎仓与远端同级」**这三点不会因为多一个文档提交而改变。

### G1 主仓 `F:\moonbit-hof-rs`（分支 `master`，无远端）

`git log --oneline -8`：

```
7b5fa56 feat(godot-mcp): TASK-099 - the 8th and 9th C# games are delivered through MCP calls only (Frogger: a 13x15 grid crossing with traffic, logs, homes and lives; Flappy Bird: one fixed 1/60 s frame of gravity, gaps, scoring and collisions, with the Flappy payload defect a 30-frame sample caught fixed and re-run), the gate runner learns to recognise a purely non-compiling submission and skip the ten gates for it while still running them the moment anything can change the compiled binary, the third live --import shutdown access violation is recorded with 24 more controlled probes at zero crashes and no engine edit, and ledger G-1 is closed at the root
5c83668 docs(godot-mcp): TASK-098 - the report: the two new C# games with their before/after runs, the section 7 alignment, the leftover accounting reconciled from a git-status entry count to a file count, the seven-row number re-read, and the import access violation recorded as unreproducible in 64 controlled runs with its static localisation
fdbbed6 feat(godot-mcp): TASK-098 - the 6th and 7th C# games are delivered through MCP calls only, MCP-TRACEABILITY section 7 is aligned with the D-1 closure, and the TASK-096 leftovers are resolved by enforcing the verdict TASK-096 had already recorded
ddc0dbb docs(godot-mcp): TASK-097 - the report's closing boundary is restated so it cannot be made stale by the task's own doc-only follow-ups: the snapshot is the state right after the report commit, and the two follow-ups that exist are listed verbatim
fc54163 docs(godot-mcp): TASK-097 - GAME-LOOP-LOG's TASK-096 re-localisation section gains the one-line closure note, so its "unavailable (D-1)" wording is read as the historical record of the runs before the cleanup rather than as the current state of the pixel column
d1ac6e6 docs(godot-mcp): TASK-097 - the report's closing section: both repositories' real git logs and status lines, the tracked-versus-untracked accounting (0 tracked changes, 136 untracked entries all left over from TASK-096), the engine branch being level with its remote at 094b071f9b, and the post-run process/port check
4e2b85b feat(godot-mcp): TASK-097 - D-3 is fixed at the root: editor_add_nodes_batch refuses a requested name the target parent already carries instead of letting the engine rename it into a duplicate, editor_save_scene reports the duplicates an explicit rename leaves behind, the duplicate layer is removed from the three older scenes and their pixel-diff column is refilled with real numbers (Pong 14/74, Breakout 14/89, Snake 13/102, independently recomputed), and the fifth C# game Space Invaders is delivered through MCP calls only (59/59 facts, 12/59 non-zero pixel diffs, first-run green)
aa64293 docs(godot-mcp): TASK-096 - the report's boundary note: the closing snapshot describes the state before this doc-only follow-up, and the follow-up carries this very sentence
```

`git status --short`：**空**（本任务的新增与改动全部随 `7b5fa56` 入库）。

### G2 引擎仓 `F:\moonbit-hof-rs\godot-mcp\godot`（分支 `feature/mcp-server-module-rebuild`）

`git log --oneline -8`：

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

`git status --short`：**空**；`git rev-parse HEAD` = `git rev-parse refs/remotes/origin/feature/mcp-server-module-rebuild` = **`e041cae270487d5c910f1e7ebe0e13982886d602`**。

### G3 收尾后的进程与端口

无残留 `Godot*` 进程；`9877`、`9934–9939` 无 **LISTENING**。**未改变机器显示或串流状态**。
