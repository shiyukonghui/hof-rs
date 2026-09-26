
## D147 — TASK-099：第 8、9 款 C# 游戏（Frogger / Flappy Bird）交付；`run_gates.ps1` 识别纯文档提交并跳过重建；`--import` 关机期访问违例第 3 次现场复现（不动引擎）

**日期**：2026-09-27　**触发问题**：D146 留下三件事 —— ①台账只到第 7 行（D138 的目标是至少 20 款 C# 游戏）；②TASK-098 §D1 自己写下的取舍「源未变就别空跑十道门」需要一个**机制**，而不是每轮靠人记（台账工具缺陷 G-1）；③`--import` 的关机期访问违例只有 2/11 的观测率，TASK-098 的 64 次受控复现全 0，定位方向停在静态推断。

**考虑过的选项**

| 决策点 | 选项 | 选择 | 理由 |
|---|---|---|---|
| ① 门跑器的纯文档跳过怎么判 | (a) 在 `run_gates.ps1` 里再抄一份编译/非编译白名单；(b) **dot-source 模块自己的 `check_engine_anchor.ps1`** | **(b)** | 分类规则只能有一份。模块的锚点判据已经把「什么能改变编译产物」写成显式白名单 + fail-closed（未识别的一律红）；复制一份必然漂移，而且门 9 与预检会各说各话 |
| ② 锚点从哪里来 | (a) 沿用 `-VersionText` 的硬编码默认值；(b) **默认读二进制自己的 `--version`** | **(b)** | 旧默认是 TASK-090 的 `8604fcf9e`，每个新提交都把它变成 stale（G-1 的根因）。门 9 应该判「磁盘上那个二进制」，不是「某个历史字符串」；`-VersionText` / `-Anchor` 仍可显式覆盖 |
| ③ 工作树算不算 diff | (a) 只看 `git diff A..H`；(b) **committed 区间 + 工作树一起看** | **(b)** | 一个未提交的 `.cpp` 同样能改变（下次）编译产物；只看 committed 区间会给「改了还没提交」放行 |
| ④ 跳过时怎么收口 | (a) 静默退出；(b) **打印 verdict / reason / 非编译文件清单，写 `summary.txt`，`exit 0`** | **(b)** | 跳过也是一次判定，必须留下可核对的账；`GATES_SKIPPED=1` 让下游一眼看出这是「跳过」而不是「跑过」 |
| ⑤ 门跑器改动要不要重建两变体 | (a) 重建；(b) **不重建，并在 manifest 里说明为何不影响** | **(b)** | `tools\run_gates.ps1` 在**主仓**里，根本不在引擎仓的树内：引擎仓 `git status` 前后均为空，改动进不了 `2385fe2fb..HEAD`，碰不到任何 `.cpp`/`.h`，两个二进制一个字节都没变 |
| ⑥ Frogger 的交通怎么保证确定性 | (a) 让车按墙钟自己跑；(b) **`CarSpeed` 默认 0 + 固定步长钩子 `StepTraffic(n)` + 增量属性 `LastTrafficSteps`** | **(b)** | 与前七款同一条确定性规则。P-1 的教训直接写进载荷：任何「钩子做了多少」都必须是**与帧率无关的增量**，而不是被时钟污染过的总数 |
| ⑦ Flappy 的重力怎么保证确定性 | (a) 让 `_Process` 自己积分；(b) **`AutoRun` 默认 false + `StepFrames(n)` / `StepUntilPass(n)`** | **(b)** | 1/60 s 的固定步长把「第 164 帧通过第一根管子」变成一个可断言的确切数（实测 164/100/100/100/100） |
| ⑧ `--import` 崩溃怎么处置 | (a) 按台账待办直接改引擎埋点 / 换掉 `ERR_FAIL_NULL_V`；(b) **先现场记录 + 受控探针统计，不动引擎** | **(b)** | 任务书自己写了条件：「若无法稳定复现，就只做埋点与统计，不要凭推测改引擎」。本轮有 1 次现场复现（frogger 首次导入），但**对照组不崩**（同轮 flappy 同为全新工程首次导入 `exit=0`），24 次受控探针（含 8 个 CPU 烧机进程加压）仍全 0 → 没有可证的根因，就没有可回滚的改动 |

**最终选择与理由**：交付 **Frogger**（第 8 款）与 **Flappy Bird**（第 9 款），两款都沿用已固化的模板：**静态节点用一次 `editor_add_nodes_batch` 建好、动态对象在运行期新建、`ForceTestState` 一个调用钉死整盘状态、多帧采样先于会改变状态的那一步、建场景那一步故意再跑一次同名批量让 D-3 的 `-32000` 留在每轮证据里**。Frogger 是格点过马路 + 过河（车流 / 浮木 / 到家计分 / 生命与胜负），Flappy 是重力与点击上升 + 管道间隙 + 通过计分 + 碰撞判负。两款首轮即 90/90 与 92/92 facts、像素差真实非零、独立复算 0 处不符：

* **Frogger** `runs\frogger\frog-task099-r1`：90 次调用（编辑器 16 / 游戏 74），`facts_complete` **90/90（100%）**，像素差 **17/90 非零**，`user://` 五帧 8864/9178/9291/9943 px；缺陷 **0/0**。
* **Flappy Bird** `runs\flappy\flappy-task099-r2`：92 次调用（编辑器 14 / 游戏 78），`facts_complete` **92/92（100%）**，像素差 **22/92 非零**，`user://` 五帧 34326/98611/1699/99094 px；缺陷 **0/1**（下面是 F-1）。
* `run_gates.ps1` 新增预检：纯非编译（文档）提交 → `ANCHOR_STRUCTURAL_EQUIVALENT` + `GATES_SKIPPED=1` + 打印非编译文件清单 + 不跑门；有编译输入（committed 或工作树）→ 照常跑门。实测两情形：doc-only `exit 0` 跳过（`runs\gates\task099-doconly\`）；工作树放一个未跟踪 `.cpp` 后 `g01..g10` 全 `exit=0`、`accept_m1 22/22`（`runs\gates\task099-compileinput\summary.txt`）。**G-1 结案。**
* `--import` 关机期访问违例第 3 次现场复现（`runs\frogger\frog-task099-r1\import.stderr.txt`，症状与 TASK-097/098 一字不差）；受控探针 24 次（默认端口 9877 × fresh/warm × 是否加压）**全 0**，累计受控 88 次全 0 对 13 次会话导入 3 次崩溃。**不动引擎、不加埋点**，如实留档。

**预期影响与回滚点**：主仓新增 `projects\frogger\`、`projects\flappy\`、`tools\sessions\{frogger,flappy}\`、`recovery\work\task099\`（含归档的某个 r1 工程与 sha 清单），并修改 `tools\run_gates.ps1` 与 `GAME-LOOP-LOG.md`；引擎仓只有一份**文档**提交（manifest 2c-11 节）。回滚 = `git revert` 对应提交；`run_gates.ps1` 的回滚是纯脚本回退（旧默认锚点会立刻让门 9 变红，这正是旧行为）。风险敞口：①预检把「工作树里任何未识别/可编译文件」当红是**故意 fail-closed**，代价是引擎仓里常年留着的临时文件会让门照跑（宁可多跑，不可漏跑）；②`--import` 的间歇性退出码仍在，`IMPORT_EXIT` 依旧**不能**当健康信号；③Flappy 的 `PipesToClear=5` 是本轮定义的通关条件（原版没有胜利条件），已在源码注释与台账里写明。

**验证（真实输出）**：
* **Frogger**（`runs\frogger\frog-task099-r1`）：90 次调用（16/74），`facts_complete` **90/90**，判定分布 `failed=2`（两条都是**声明的**：`e06` 同名批量 `-32000`、`g68` 不存在属性 `-32001`）+ `ok_effect=17` + `ok_file_effect=49` + `ok_no_effect=22`；断言 **34 PASS + 1 条声明的边界失败**；像素差 **17/90**（编辑器 1/16、游戏 16/74）；`user://` 五帧逐对 **8864 / 9178 / 9291 / 9943 px**，五帧 sha 互不相同；独立复算（`pixel_recompute.py` 逐调用对 + `frames_recompute.py` 保存帧）与 `report.json` **0 处不符**；`project_build_csharp` exit 0、`invalid_count=0`、`editor_get_errors count=0`；`e05`/`e09` 文件 sha 与拒绝前**一字未变**；声明的 `frog_up` 动作真的把 `FrogRow` 推过 14（`all_passed=true`）。
* **Flappy Bird**（`runs\flappy\flappy-task099-r2`，首轮 r1 对照）：92 次调用（14/78），`facts_complete` **92/92**，判定分布 `failed=2`（同样两条声明的）+ `ok_effect=22` + `ok_file_effect=46` + `ok_no_effect=22`；断言 **38 PASS + 1 条声明的边界失败**；像素差 **22/92**（编辑器 1/14、游戏 21/78）；`user://` 五帧逐对 **34326 / 98611 / 1699 / 99094 px**；独立复算 **0 处不符**；r2 的五个帧与 r1 **逐字节相同**；`StepUntilPass` 的确切帧数 **164 / 100 / 100 / 100 / 100**、`Score` 10→50、第五根通过时 `Won`+`GameOver`；`g44` 的 30 帧滚动采样在 r2 里 `Pipe0X` **17 个不同值（576→492）**而 `BirdY` 恒定（r1 里是**恒定 582** —— F-1 的证据）。
* **F-1（Flappy 载荷缺陷，已修并重跑）**：r1 的 `g44` 显示 `Ticks` 从 31 走到 101 而 `Pipe0X` 恒定 → 根因是 `frames = (int)(delta * FixedFps)` 在 144 fps 下截断成 0，`StepFrames(0)` 永不发生；改成累加器 `_autoAccum` 后 r2 通过。**所有断言在 r1 里也全 PASS** —— 这条缺陷是多帧采样照出来的，不是断言照出来的。
* **门跑器**：`runs\gates\task099-compileinput\summary.txt` 的 `g01`..`g10` **全部 `exit=0`**（`accept_m1` 行给 `22/22 cases passed`）；`runs\gates\task099-doconly\summary.txt` 给 `ANCHOR_STRUCTURAL_EQUIVALENT` + `RESULT=SKIP_REBUILD` + `GATES_SKIPPED=1` + 两个非编译文件路径。
* **`--import`**：现场 1 次崩溃 / 2 次会话导入（另一对照组 `exit=0`）；受控 `probe2-frog-load0.json` 12/12 `exit=0`、`probe2-frogload-load8.json` 12/12 `exit=0`；累计受控 88 次全 0。

**遗留（不阻塞）**：①`--import` 的关机期访问违例仍未结案（本轮把「现场记录 + 受控统计」做完，三个判别器都要动引擎，留待拿到可复现配方或用户明确授权重建）；②`editor_add_node`（单个）仍保留引擎改名语义、`editor_save_scene` 每会话重发场景 `uid` 的行为未修（沿用 TASK-097 的声明边界）；③Frogger/Flappy 都用了 `ForceTestState` + 固定步长钩子，`AutoRun` / `CarSpeed` 这类自重跑路径**默认关闭**，因此它们只在测试显式开启时参与证据。
