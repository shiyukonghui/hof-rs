# ACCEPTANCE-TASK-137 — 独立验收报告：游戏逻辑反馈机制（判据 / 工具 / 证据）

> **验收方**：独立验收子代理（不继承实施者/决策者的任何结论）。
> **基准**：`recovery\tasks\TASK-137-ACCEPT.md` §0 的 7 条判据 + §1 的 A–E 核验事项。
> **方式**：只读验收。全部产物写在 `runs\accept-137\**`；**未修改**任何游戏代码、工具或既有证据
> （验收前后 `git -C F:\moonbit-hof-rs status --short` 都只有 `?? godot-mcp/recovery/tasks/TASK-137-ACCEPT.md`）。
> **执行**：严格单线程，**没有派任何子代理**；全部命令无 shell 重定向（Python 文件句柄 `io.open`）；
> 只用本机 8080/8081（二者 `OPEN`，未杀未重启）；串行；本验收自己的端口 **9962**；未动两个 venv、`F:\models\**`、
> `_exercises/neg_*` 与 `prefix_*`。
> **本报告里的每一个数字都是我自己重算的**：实施者报告里出现的任何数字（含任务书转述的
> "模型臂 1/1/3/15""脚本臂 9/1/4/6""111 条命令"）都只作待核对项。

---

## 0. 一句话结论

**判据没有被偷换：`strict` 在宣告层与两份代码（`playtest_player.summarise`、
`playability_gate.evaluate_model_player_steps`）里都是唯一的 PASS 判据，`PASS(baseline only)`
在 `counts_as_pass` 上真的被排除；FAIL 规则与 §0.2 一字对应，我自己构造的 6 组反例（2304 格穷举）
证明它"冻结+ack ⇒ FAIL、观测量≈1.5× ⇒ PASS(baseline only)、真实推进 ⇒ 不触发 MODEL_\*"，
且 `strict ⇒ baseline` 零违例。两条臂的判决分布我**从 `player.json`/`steps.jsonl` 自己重数**，
与实施者最后更正的口径**逐项相符**（模型 1/1/3/15、脚本 9/1/4/6）；20 张点名图我抽了 11 张
自己 `read_image`（全部 800×600），**发现报告第 9 行的一处数字描述与图上实际读数不符**（见 C-2）。
报告另有 5 处**可核数字对不上**（2 个被引用的 sha256、引用的首版报告哈希、`16/95` 的拆分、"93"），
以及 1 处**表格列填错**（platformer 的 strict 列）。这些**没有一条改变判据或可复现性**，
按 §3 的 blocker 清单（判据被偷换 / 结论无法复现 / 读图造假 / 数字不可核）我判它们为
minor/major 级**非 blocker**，故 **verdict = pass**（逐条见 §3）。

---

## 1. 逐条核验表（A1–E12）

| 编号 | 结论 | 证据指针（我自己跑的产物 / 文件:行） | 证据等级 |
|---|---|---|---|
| **A1** `strict` 是否真是 PASS 默认 | **成立** | `tools/playability_controls.json:312` `"default_margin": "strict"`；`tools/playtest_player.py:211-214` 用**声明文件**覆盖常量、`:152-157` 兜底 = strict；`tools/playability_gate.py:2550-2578` gate 读同一份声明；我自己 import 后打印 `CHANGE_MARGIN_DEFAULT='strict'`、`load_change_margins()['default_margin']='strict'`（`runs\accept-137\counterexamples2.py` 输出） | **证据支持** |
| **A1b** `PASS(baseline only)` 是否真被排除在计数外 | **成立** | `playtest_player.py:785-793`（仅 `margin=="strict"` 分支写 verdict；`counts_as_pass = (verdict=="PASS")`，而 baseline-only 的字符串是 `"PASS(baseline only)"` ⇒ False）；`playability_gate.py:2797-2828` 同构；20/20 个模型 run 的 `player.json` 里 `pass_criterion=strict`、只有 tetris 的 `counts_as_pass=true`；我的合成用例 C3 输出 `verdict='PASS(baseline only)', counts_as_pass=False`，gate 侧同为 `PASS(baseline only)/counts_as_pass=False` | **证据支持** |
| **A1c** 有没有"strict 失败却被写成 PASS"的路径 | **不成立（无此路径）** | 逐处读过 `summarise()`（`playtest_player.py:722-801`）与唯一的结构化出口 `_summarise_core()`（`:881-1048`）：`_summarise_core` 写的 `out["verdict"]` 在 `summarise` 里**只在 `margin=="strict"` 时被三种情形之一覆盖**（`:785-791`）；当 `margin != "strict"` 时顶层 verdict 就是 `margin` 自己的读数。gate 侧 `evaluate_model_player_steps` 的 `pass_criterion` 取自声明，链上无第二处能改写 verdict | **证据支持** |
| **A2** FAIL 规则用的是游戏的 ack 还是模型自述 | **成立（用的是游戏自己的 InputMap）** | `ack_verdict()`（`playtest_player.py:469-525`）只认 `is_action_pressed`（游戏进程内 `Input.is_action_pressed()` 的读回）等游戏侧证据，`note` 明写"the model's own statement is never used as evidence"；注入后 ack 是**注入之后**重读的（`:2298-2311` `ack_after_inject`），不是模型文本 | **证据支持** |
| **A2b** "画面变化"用的是对照窗还是比较绝对像素差 | **成立（对照窗）** | `_margin_reading()`（`:217-263`）里 `pixel_wins = px > max(ctl*2.5, 40)`；`decide_changed()` 只拿 `(pixel_diff, control_pixels, gameplay_movement, control_movement)` 四个数；对照窗由 `control_window()`（`:2459-2479`）在**同一次采样**里测出 | **证据支持** |
| **A3-①** 冻结画面 + 有 ack ⇒ 必须 FAIL | **成立** | 我的合成用例 `C1_frozen+ack+varied_actions`（8 步、`px=ctl=0`、动作各不相同）⇒ `verdict='FAIL'`, `strict_fail_steps=[1..8]`, `counts_as_pass=False`；`C1b`（帧也各不相同）同样 `FAIL`；gate 侧 `evaluate_model_player_steps` 同输入 ⇒ `FAIL/pass=False`。产物 `runs\accept-137\counterexamples2.json` | **证据支持** |
| **A3-②** 有真实推进 ⇒ 不触发 `MODEL_*` | **成立** | `C2_real_progress`（`mv=30..37 vs cmv=1`，`px≈2010..2070 vs ctl=40`）⇒ `verdict='PASS'`, `MODEL_FIXED_POINT=False`, `MODEL_NO_PROGRESS=False` | **证据支持** |
| **A3-③** 观测量只到 ≈1.5× ⇒ 必须 `PASS(baseline only)`、`counts_as_pass=false` | **成立** | `C3_ratio_1.5x`（第 4 步 `mv=150, cmv=100`，`px=50, ctl=100`）⇒ `verdict='PASS(baseline only)'`, `baseline_verdict='PASS'`, `strict_verdict='FAIL'`, `strict_fail_steps=[4]`, `margin_ratio=1.5`, `counts_as_pass=False`；同一批记录用 `margin='baseline'` 读回 ⇒ `verdict='PASS'`（旧口径与严格口径**并列留痕**） | **证据支持** |
| **A3-④** 规则是否过松/过紧（穷举） | **成立** | 2304 组 `(px,ctl,mv,cmv)` 穷举：`strict.changed ⇒ baseline.changed` **违例 0**；两把尺子的**像素项分歧 0**。产物 `counterexamples2.json -> C5_*` | **证据支持** |
| **A3-⑤** 严格规则的**唯一** INCONCLUSIVE 缺口 | **成立且已声明** | 冻结+ack 且**动作与帧都相同**的 8 步 ⇒ `INCONCLUSIVE`（`one_action_loop`/`same_action_fixed_point` 先于 rate 分支，`playtest_player.py:950-981`）。这是 §0 已有的 MODEL 侧 carve-out，**不是**"strict 失败被写成 PASS"；`counts_as_pass` 仍为 False。我**点名**它，并确认方向是"更保守"而非"更宽松" | **证据支持**（边界） |
| **B4** 自己复跑 ≥3 款并逐项对照 | **部分一致，1 处偏差已定位** | 我自己跑（`--player scripted --variant V1 --steps 12 --change-margin strict`，端口 9962，`runs\accept-137\rerun_scripted_results.json`）：**snake 完全一致**（8/8/8, rate 1.0, PASS, 9.871 vs 9.858s）；**tetris 完全一致**（8/8/8, PASS, 9.498 vs 9.235s）；**pong 一致但步数 9 vs 10**（rate 1.0、verdict PASS 均一致；差异来自 `--no-patience` 的"8 连续变化后提前停"在两次 run 里落在不同步上）。**逐项对照见 §2** | **证据支持**（含偏差） |
| **B5** 独立重算两条臂分布 | **成立，与最后认口径逐项相符** | 我从 `runs\model-player\t136-jev-v3\<game>\jev\player.json` 与 `t136-scripted-final\<game>\scripted\player.json` **自己数**（`runs\accept-137\recount.json`）：**模型臂 = 1 PASS / 1 PASS(baseline only) / 3 FAIL / 15 INCONCLUSIVE**；**脚本臂 = 9 PASS / 1 PASS(baseline only) / 4 FAIL / 6 INCONCLUSIVE**。作废的"9/1/8/2"我**不复现**（我的重数也不支持它） | **证据支持** |
| **B5b** 逐款数字与报告表格 | **20/20 款全对** | 脚本臂 20 行的 注入/接受/变化/rate/玩法推进步/strict 失败步/边缘步(比值)/对局时长 与我重算**逐格相同**（含 asteroids 边缘步 3=1.309×、11=1.442×；platformer 5=1.536×、7=1.896×、9=1.536×） | **证据支持** |
| **B6** 脚本臂 20/20 是否存在 | **成立** | `t136-scripted`、`t136-scripted-final` 各 **20 个** `<game>\scripted\player.json`（`recount.json -> scripted_dir_existence`）；`t136-scripted-pre` 只有 flappy/platformer（即"修前"两款，符合报告 §6） | **证据支持** |
| **C7** 抽 ≥4 张图 + 全尺寸 + sha + 自己读图 | **成立，但发现 1 处描述与图不符** | 抽 **11 张**自己 `read_image`（全部 `800x600 px`）：报告第 1/2/3/4/5/8/9/**14**/15 行 + 追加的 frogger/asteroids/lunarlander。19/20 个点名文件的 `sha16` 与报告可查项**逐一致**；冻结对（flappy 第 5/6 行）**sha 相同**已复现。**报告第 9 行**声称"`TILE 4,27`、右移两格"，图上实际读数是 **`TILE 3,27`**（见 §3 D-7） | **证据支持**（含缺陷） |
| **C8** "没变化"必须看原尺寸 | **成立** | 我对 flappy 第 5/6 行、asteroids、frogger 的"无变化/已终局"判定都看了 **800×600 原尺寸**；缩略图**没有**被用作任何"没变化"的依据（我另用 `frame_budget`/`state_delta` 的原始读数交叉验证） | **证据支持** |
| **D9** 重定向自查自己重扫 | **成立（命中数与逐条原文全对）；拆分的 16/95 与"93"对不上** | 我自己扫 `t136_commands.jsonl`（`runs\accept-137\my_redirect_scan.json`）：**前 111 条里命中 3 条** —— #2 `2>&1`、#13 `2>nul`（两条都是 `source=manual-backfill`，与报告 §3.3 原文**逐字相同**）、#65 `struct.unpack('>II'…)` 的 Python 大端格式符（**确认是真假阳性**，且该条经包装器 `shell=False` 执行 ⇒ shell 根本没参与）。台账**当前 116 条**。包装器条目里真实重定向 **0** | **证据支持** |
| **D10** 至少复现 2 项"未修的游戏侧阻塞" | **成立（我复现了 3 项 + 附加证据）** | ① **frogger**：`InputRepeat=0.12s`（`FroggerGame.cs:160`）+ `_Process` 里 `_inputAccum>=InputRepeat ⇒ StepFrog`（`:411-444`），注入 `hold_ms=350` ⇒ **一次按键约 3 次迈步**；记录 `state_delta` 显示唯一一次 `frog_up` 后 `Lives 3→0`、`GameOver false→true`、`LastEvent="lives lost reason=hit by car at=6,13 lives=0 game over"`、`FrogCol/FrogRow` 始终 6/14；两条臂（`t136-scripted` 与 `t136-scripted-final`）的该步 sha 相同。② **bomberman**：`AutoClock=0.0f`（`:203`、`:414`、`:1457`）⇒ `Detonations` 12 步恒 0、引信永不燃烧；`Bomb_i` 的 `ColorRect` 建好后 `Visible=false`（`:492-501`），全文件**再无**把它置 true 的路径（对照 `Enemy_/Player` 在 `:547`/`:562`）⇒ 已放的炸弹画面上不可见。③ **flappy**：`AutoRun=false`（`:113`）且 `_PhysicsProcess` 在 `:310` `if (!AutoRun || GameOver) return;` ⇒ `FrameCount` 恒 0、`BirdY` 12 步恒 300，`flap` 只改 `BirdVelocity`（12 步里 11 步 `px=0`）。三者都是**游戏侧**、与策略无关 | **证据支持** |
| **D11** 20 款正式工程是否只改了声明的那几款 | **成立** | `git -C F:\moonbit-hof-rs log --name-only 3ede4f2..HEAD -- godot-mcp/projects` 只列 `godot-mcp/projects/platformer/src/PlatformerGame.cs`；`git show --stat 49c919a` 只有 9 个路径（1 个游戏工程文件）；`git status --short` 在我验收前后都**干净**（只有未跟踪的 TASK-137-ACCEPT.md）；flappy 源码 sha16 = `9d47d77954592036` = 报告声称的 HEAD 版本 | **证据支持** |
| **E12-a** 对照窗是否与动作窗同帧预算 | **名义同预算成立；实测动作窗系统性更长** | 409 个 step 的 `frame_budget.target_delta` 与 `control_diff.frame_budget.target_delta` **全部 = 30，零不匹配**（`runs\accept-137\adversarial.json`）。但**实测达成帧数**：模型臂动作窗 中位 138 / 对照窗 中位 51（中位比值 **2.48×**，`action>control` 出现在 **213/213** 步）；脚本臂动作窗 中位 119 / 对照窗 中位 33（**3.68×**，196/196）。**点名**：动作窗里包含 `hold_ms` 注入期间累积的帧，工具自己的注释（`playtest_player.py:2476-2478`）称两窗"same length in game frames"——**该断言在实测上不成立**（`mx`/`px` 因此对动作窗有利）。缓解事实：`changed` 要求动作窗**超过自己对照窗**的倍数，strict 甚至要 ≥2×（动作窗已多 2.5–3.7× 帧，故 strict 是**更保守**的门槛）；判据收紧方向与偏差方向一致。**不是 blocker**（见 §5 风险 R1） | **证据支持** |
| **E12-b** "球本来就在动"会不会被算成"响应" | **已被对照窗结构挡住** | `ack_verdict` 里 `state_moved` 只在 `injected` 时才算（`:507-508`）；`step_made_progress` 对未注入步返回 `None` 并**打断** `MODEL_NO_PROGRESS` 计数（`:662-665`）；`change` 的分母恒为**自己的**对照窗 | **证据支持** |
| **E12-c** `wait` 是否被当成有效动作 | **不成立（"wait"没有被算作动作）** | 两臂 409 步里 **74 步 `action=None`**（模型 63 / 脚本 11），它们 `evidence_used='nothing'`、`injected=false`、`accepted=false`，被排除出 rate 分母（`playtest_player.py:824-826`）；**没有任何** `injected=false ∧ accepted=true` 的步（`adversarial.json -> accepted_but_not_injected = 0`） | **证据支持** |
| **E12-d** `ack` 会不会被先前按键污染 | **可核证据里不成立；代码里留有一条窄缝** | 409 个注入步 **全部** `evidence_used='action_pressed'`、`accepted_without_evidence=0`；两臂 **0 个** `Input.parse_input_event` 步缺 `injection.ack_result`，即 ack 恒为**注入后**的重读。**窄缝**：`:2326` `ack_state_for_verdict = inj.get("ack_result") or pre_ack`，而 `pre_ack`（`:2275-2277`）是**注入前**读的 ⇒ 若注入工具返回但缺 `ack_result`，会退回到注入前的读（那可能是上一步残留的按下态）。两臂 409/409 步都没走到这条兜底 | **证据支持**（含边界） |

---

## 2. B4 逐项对照（我自己跑的 vs 报告）

| 游戏 | 项 | 报告 | 我自己的复跑 | 判定 |
|---|---|---|---|---|
| **snake** | 注入/接受/变化 / rate / verdict / 对局时长 | 8 / 8 / 8 · 1.0 · PASS · 9.858s | **8 / 8 / 8 · 1.0 · PASS · 9.871s** | **逐项一致** |
| **tetris** | 同上 | 8 / 8 / 8 · 1.0 · PASS · 9.235s | **8 / 8 / 8 · 1.0 · PASS · 9.498s** | **逐项一致** |
| **pong** | 同上 | 10 / 10 / 10 · 1.0 · PASS · 13.898s | **9 / 9 / 9 · 1.0 · PASS · 11.636s** | rate/verdict 一致；**步数 9≠10**，成因：`--steps 12` + 早停（8 连续"接受且变化"后停）在两次 run 落在不同步（我逐 step 比对了两次 run 的 `px/mv/strict` 读数，形态相同、数值随实时帧数抖动） |
| **platformer** | 注入/变化/rate/严格失败步/边缘步 | 11 / 8 / 0.7273 / [5,7,9] / 5=1.536×,7=1.896×,9=1.536× | 从 `t136-scripted-final` 产物重算：**11 / 8 / 0.7273 / [5,7,9] / 同上** | **逐项一致** |
| **asteroids** | 12/10/0.8333 / 边缘步 3,11 | `t136-scripted-final` 重算：**12/10/0.8333 / 3=1.309×,11=1.442×** | **逐项一致** |
| **frogger** | 注入 1 / 变化 1 / INCONCLUSIVE | 重算：**1 / 1 / INCONCLUSIVE**（`frames\` 只有 4 个文件，证实"只跑了 1 个注入步"） | **一致** |
| **bomberman** | 12/6/0.5 / FAIL | 重算：**12/6/0.5 / FAIL** | **一致** |

> 我对 platformer/asteroids/frogger/bomberman 是**从记录产物重算**（未重跑），对 pong/snake/tetris 是**自己重跑**。
> 报告里 platformer 行的 **strict 列**填的是 `FAIL`，而该 run 的 `player.json -> verdict` 实为
> `INCONCLUSIVE`（`strict_verdict=FAIL`、`game_side_verdict=FAIL`、`baseline_verdict=PASS`、
> `counts_as_pass=False`）——**列填错**，见 §3 D-6。

---

## 3. 缺陷清单（我点名，逐条给定性）

| # | 缺陷 | 严重度 | 证据 |
|---|---|---|---|
| D-1 | **报告 §7 第 9 行**称 platformer 帧是 `TILE 4,27` 且"向右跑了两格"；我 `read_image` 该图（800×600）读到的 HUD 是 **`TILE 3,27`**，且同句的"两格"与 `TILE 3` 自相矛盾 | **major** | 图：`runs\model-player\t136-scripted-final\platformer\scripted\frames\004_01_after.png`（sha16 `54e9873333c3edbb`）；**同帧的 `steps.jsonl` 第 1 步 `plat_right` 允许 1 格**（`readable_state.values` 起始列 1）。"修后玩家真的动了"这个**结论仍然成立**（`px=599→737→1088`，`LIVES 3→2→1`），错的是那句数字 |
| D-2 | 报告 §11.2 引用的 `t136_redirect_scan.json` sha256 前缀 `42bbab3f48906aeb` **与磁盘现状不符**：实测 `3ac18ad769996410`（15994 B，mtime 03:22:17），比 §3 声称的扫描截点（03:22:17 的那次）**晚** | **major** | `runs\accept-137\artifact_hashes.json` |
| D-3 | 报告 §3.5 称"台账 111 = 16 条人工回填 + 95 条包装器条目"；我按 `source=="manual-backfill"` 精确计数得 **17 + 94 = 111**（包装器条目**不带 `source` 字段**，是"非 manual"的余数） | minor | `runs\accept-137\my_redirect_scan.json`；`t136_cmd.py:52` 写 `{ts,cwd,argv}`，**没有** source 字段 |
| D-4 | 报告 §11.2 称 `t136_commands.jsonl` 的哈希"截至 111 条"，但台账是**追加式**、且**台账自身还在长**：当前 116 条。§3.2 说截点之后的条目"只有收尾/提交/回写命令"也与事实有出入——我看到的 112–116 条包含 `pytest tools\tests -q` 与 `playtest_player.py selftest` 两条**验证命令** | minor（报告已自己声明台账是追加式、哈希会变；`git log -1 --format=%B 49c919a` 里"93 commands scanned"是**已作废**的旧数字） | 台账逐条列出：112 `git add`、113 `git commit --amend`、114 `git status`、115 `pytest`、116 `selftest` |
| D-5 | 报告 §11.2 的"本报告（首版）sha256 `f98a4575876a0d81`，55665 B"**不能核**：磁盘现版是 **`7c5a1738e601e018`，58488 B**（docs-only 提交改了同一文件，自指） | minor（报告 §11.4 自己声明首版哈希写进文件会自指） | `runs\accept-137\artifact_hashes.json` |
| D-6 | 报告 §4.1 脚本臂表的 **strict 列**把 platformer 填成 `FAIL`，与 `player.json -> verdict = INCONCLUSIVE` 不符 | minor | `recount.json -> scripted_final.rows[platformer]`；`t136-scripted-final\platformer\scripted\player.json` |
| D-7 | 报告 §1.2 把 platformer 描述为"baseline PASS / strict FAIL ⇒ 顶层 PASS(baseline only)"，而该 run 的**顶层 verdict 实为 INCONCLUSIVE**；它真正被证明的是"**strict FAIL 且没有被记成 PASS**"，以及顶层分布口径（9/1/4/6）本身 | minor | 同上；我核对了 §1.2 引的 asteroids（确为 `PASS(baseline only)`，`counts_as_pass=false`，边缘步 3/11）**成立** |
| D-8 | 报告 §3.1 称"包装器自身的调用（`python t136_cmd.py -- <argv>`）不在台账里"——成立；但**因此对台账扫描的 111 条**只能覆盖"被包装的命令"，**"包装器调用本身"绕过台账**（这是设计取舍，我在 §5 列为风险而非缺陷） | minor | `t136_cmd.py:52`（只记 `argv`）；台账里 `argv[0]` 为 `D:\Anaconda\python.exe` 或 `git`，无一条是包装器自身 |

**我确认不成立的"疑似缺陷"（查过，点名）**：
* 报告 §9.3 的 `EXCEPTION: AttributeError: 'ScriptedAgent' object has no attribute 'last_evidence'`
  **真的存在**（`t136-gate-platformer\summary.txt:18`，`gate.json -> errors`），且**真的预存在**
  （`t135-gate2\{game2048,puzzlebobble,snake}\gate.json` 与 `t135-gate2b\game2048\gate.json` 各 1 条同文本）；
  P1–P7 仍全 PASS（`summary.txt:19-22`，`per_criterion_fail` 全 0）。报告的"预存在、不影响判定"**成立**。
* 截图缩略图冒充看图：报告 §7 的 20 张全部在磁盘上存在且都是 **800×600**，我实读的 11 张与描述**基本相符**（唯一不符是 D-1）。

---

## 4. 判据有没有被偷换（§0 逐条的最终裁定）

1. **Jev 当模拟真人玩家**（看图 → 出操作 → 脚本注入 → 记录画面变化）：**成立**。`run_step` 先 `capture` 画面再 `agent.decide([frame_for_model], …)`，请求里必须带图（缺图会被记为 error，`playtest_player.py:2264-2270`），随后 `Input.parse_input_event` 注入并前后截图。
2. **FAIL = 模型出操作 ∧ 游戏接受 ∧ 画面没动态变化**：**成立且与我自己的实现一致**（§A2/A3，6 组反例 + 2304 格穷举）。
3. **PASS = 连续 ≥8 步里"接受 ∧ 变化"比例 ≥75%**：**成立**（`PASS_MIN_STEPS=8`、`PASS_MIN_RATE=0.75`，`playtest_player.py:927`；两条臂同阈值）。**"读前后图判定变化符合游戏逻辑"这一半我没有条件整体复核**（需要 409 步的逐帧读图）——只核了报告点名的 20 张，列为 `unverifiable`。
4. **strict 余量 ≥2× 对照窗且 ≥1.0，且只有 strict 通过才算 PASS**：**成立**（`gameplay_control_factor=2.0`、`gameplay_min_movement=1.0`；`PASS(baseline only)` + `counts_as_pass=false`）。
5. **`MODEL_FIXED_POINT` / `MODEL_NO_PROGRESS` 与 FAIL 分开、不得用于判 PASS**：**成立**。两者只在 `_summarise_core` 里**降级为 INCONCLUSIVE** 或**只记录**；`gate` 侧同样不把 `mp_noprog` 放进任何 `pass` 分支（`playability_gate.py:2747-2750` 的注释与代码一致）。
6. **必须读图**：报告点名的 20 帧**全部存在且全尺寸**；我实读 11 张，其中 1 张描述错（D-1）。**不是"数字冒充看图"**（报告给了帧路径、尺寸、sha 与逐帧描述）。
7. **P1–P7 不用于可玩性判定**：**成立**。`MODEL_PLAYER_CRITERION_NOTE`（`playability_gate.py:2529-2547`）在 `gate.json` 里明写这点；报告也只在"代码能跑"口径下用它。

---

## 5. 遗留风险（不改变本次 verdict，但决策者应知道）

| # | 风险 | 事实 |
|---|---|---|
| R1 | **对照窗与动作窗实测长度不等**，动作窗中位长 2.5–3.7× | 见 E12-a。`target_delta` 相同（30）但**达成帧数**不同；`playtest_player.py:2476-2478` 的注释断言两窗"same length in game frames"在实测上不成立。方向是让"动作窗看起来更能动"，但 `changed` 要求的是**相对自己对照窗**的倍数（strict ≥2×），故收紧方向与偏差方向一致 ⇒ 不会虚高 PASS；**但"变化率"的绝对量级不能与"等帧数"的直觉互换** |
| R2 | `ack` 的**窄缝**：`inj.ack_result` 缺失时回退到**注入前**的 `pre_ack` | `playtest_player.py:2326`。本批 409/409 步都未触发，但实现上存在"上一步残留按下态被当成本步 ack"的可能 |
| R3 | 报告的"变化率"含 reproduce 抖动 | 我复跑 pong 得 9 步 vs 报告 10 步（同为 PASS）。任何依赖**步数**的绝对数字都应视作"随实时帧数抖动"，而依赖 verdict/rate 的结论稳定 |
| R4 | `runs/**` 被 `.gitignore:43` 忽略 ⇒ 一切证据**只在本机** | 报告 §12 自己声明；我的重算产物同样在 `runs\accept-137\**`，进不了 git |
| R5 | "合法拒绝未被判据识别"的声明层待办 | 报告 §12 第 5 条自认（match3/minesweeper/pacman/sokoban/towerdefense 的拒绝计数器不在 `refusal_evidence.keys`）。我确认它**没有**被偷偷加进去（`playability_controls.json` 的 `refusal_evidence.keys` 仍是 `LastRefusedInput|Rejected`） |
| R6 | 模型臂 15/20 是 `INCONCLUSIVE` | 报告没有把它说成"能玩 N 款"（§5.1 与 §12 第 3 条都明确写了"不得这么说"）。我重算的分布支持这一克制表述 |

---

## 6. 结构化输出（§3 要求）

```json
{
  "verdict": "pass",
  "criteria": [
    {"id": "A1", "pass": true, "evidence": "tools/playability_controls.json:312 default_margin=strict; tools/playtest_player.py:211-214 (declaration overrides the constant), :152-157 fallback=strict; tools/playability_gate.py:2550-2578 reads the same declaration; my printout CHANGE_MARGIN_DEFAULT='strict' in runs/accept-137/counterexamples2.json; all 20 runs of t136-jev-v3 have player.json pass_criterion='strict'"},
    {"id": "A1b", "pass": true, "evidence": "playtest_player.py:785-793 verdict/ counts_as_pass; playability_gate.py:2797-2828; my synthetic case C3 -> 'PASS(baseline only)' + counts_as_pass=false (runs/accept-137/counterexamples2.json); gate side same; only tetris has counts_as_pass=true out of 20 model runs"},
    {"id": "A1c", "pass": true, "evidence": "no code path writes PASS when strict fails: the only three ways summarise() sets the top-level verdict are playtest_player.py:785-791; _summarise_core's own verdict is overwritten only there"},
    {"id": "A2", "pass": true, "evidence": "ack_verdict() playtest_player.py:469-525 uses only the game's own Input.is_action_pressed; ack is re-read AFTER injection at :2298-2311; 409/409 injected steps across both arms have evidence_used='action_pressed' (runs/accept-137/adversarial.json)"},
    {"id": "A2b", "pass": true, "evidence": "pixel term in _margin_reading() playtest_player.py:234-235 is px > max(ctl*2.5,40); decide_changed only receives the four numbers incl. the control values measured by control_window() :2459-2479"},
    {"id": "A3-frozen", "pass": true, "evidence": "C1_frozen+ack+varied_actions -> verdict=FAIL, strict_fail_steps=[1..8], counts_as_pass=false; C1b same; gate evaluate_model_player_steps -> FAIL/pass=false. runs/accept-137/counterexamples2.json"},
    {"id": "A3-real", "pass": true, "evidence": "C2_real_progress -> verdict=PASS with MODEL_FIXED_POINT=false and MODEL_NO_PROGRESS=false"},
    {"id": "A3-edge", "pass": true, "evidence": "C3_ratio_1.5x -> verdict='PASS(baseline only)', baseline='PASS', strict='FAIL', strict_fail_steps=[4], margin_ratio=1.5, counts_as_pass=false; same records with margin='baseline' read 'PASS'"},
    {"id": "A3-tightness", "pass": true, "evidence": "2304-case grid: strict.changed => baseline.changed violations=0; pixel-term disagreements between the two margins=0 (C5_* in runs/accept-137/counterexamples2.json)"},
    {"id": "B4", "pass": true, "evidence": "own reruns on port 9962 (runs/accept-137/rerun_scripted_results.json): snake and tetris match the report exactly (8/8/8, rate 1.0, PASS, 9.871 vs 9.858 s / 9.498 vs 9.235 s); pong matches on verdict/rate (PASS, 1.0) but 9 injected steps vs 10 (early-stop landing on a different step); platformer/asteroids/frogger/bomberman recomputed from their artifacts match cell-for-cell"},
    {"id": "B5", "pass": true, "evidence": "my own tally from runs/model-player/t136-jev-v3/<g>/jev/player.json and t136-scripted-final/<g>/scripted/player.json (runs/accept-137/recount.json): model = 1 PASS / 1 PASS(baseline only) / 3 FAIL / 15 INCONCLUSIVE; scripted = 9 PASS / 1 PASS(baseline only) / 4 FAIL / 6 INCONCLUSIVE - both match the corrected wording exactly"},
    {"id": "B6", "pass": true, "evidence": "t136-scripted and t136-scripted-final each hold 20 <game>/scripted/player.json; t136-scripted-pre holds only flappy+platformer (recount.json -> scripted_dir_existence)"},
    {"id": "C7", "pass": true, "evidence": "11 images read with read_image, all 800x600, sha256 of 19/20 named files matching the report; one description defect (D-1): platformer row 9 reads 'TILE 3,27' on screen, the report says 'TILE 4,27' and 'two tiles'; the frame files are runs/model-player/t136-scripted-final/platformer/scripted/frames/004_01_after.png etc."},
    {"id": "C8", "pass": true, "evidence": "the 'nothing changed' claims (flappy 004_01_after sha 0f53a0d32ceb9ad2 twice, asteroids, frogger GameOver) were all checked at 800x600 and cross-checked against frame_budget/state_delta raw readings"},
    {"id": "D9", "pass": true, "evidence": "my own scan of runs/model-player/_scripts/t136_commands.jsonl (runs/accept-137/my_redirect_scan.json): 3 hits in the first 111 entries - #2 '2>&1', #13 '2>nul' (both source=manual-backfill, verbatim as quoted), #65 struct.unpack('>II',...) confirmed a false positive (Python big-endian format char, executed shell=False through the wrapper); 0 real redirects inside the wrapper entries; ledger is now 116 lines; the 16/95 split is really 17/94"},
    {"id": "D10", "pass": true, "evidence": "3 unfixed game-side blockers reproduced: frogger (InputRepeat=0.12 at FroggerGame.cs:160 + accumulate/StepFrog at :411-444 with hold_ms=350 -> one keypress = ~3 hops; the single frog_up step went Lives 3->0 with FrogCol/Row still 6/14); bomberman (AutoClock=0.0 at :203/:414/:1457 -> Detonations stays 0 for 12 steps; Bomb_i ColorRect Visible=false at :492-501 and never shown anywhere); flappy (AutoRun=false at :113, _PhysicsProcess returns at :310 -> FrameCount stays 0 and BirdY stays 300 for 12 steps, 11 of them px=0)"},
    {"id": "D11", "pass": true, "evidence": "git log --name-only 3ede4f2..HEAD -- godot-mcp/projects lists only godot-mcp/projects/platformer/src/PlatformerGame.cs; git show --stat 49c919a lists 9 paths; git status --short is clean; flappy source sha16=9d47d77954592036 == HEAD"},
    {"id": "E12", "pass": true, "evidence": "409/409 steps have action and control target_delta=30 with zero mismatches; 74 steps carry action=null and none of them is injected/accepted; 0 accepted-but-not-injected; ack is the post-injection read in 409/409 steps (no pre_ack fallback taken) - runs/accept-137/adversarial.json"},
    {"id": "S3-note", "pass": true, "evidence": "the P1..P7 are explicitly declared not to be the playability verdict in playability_gate.py:2529-2547 and in gate.json/model_player_criterion.note"}
  ],
  "defects": [
    {"what": "Report section 7 row 9: the platformer frame is described as 'TILE 4,27' and 'moved two tiles right'; the image read at full 800x600 shows TILE 3,27 (and 'two tiles' contradicts TILE 3); the same frame's steps.jsonl step 1 is one plat_right", "severity": "major", "evidence": "F:\\moonbit-hof-rs\\godot-mcp\\runs\\model-player\\t136-scripted-final\\platformer\\scripted\\frames\\004_01_after.png sha16=54e9873333c3edbb, read_image shows 'GEMS 0/14 SCORE 0 LIVES 3 AIR 0 TILE 3,27'; the underlying conclusion (the player moves after the fix) still holds (px 599->737->1088)"},
    {"what": "Report section 11.2 quotes t136_redirect_scan.json sha256 prefix 42bbab3f48906aeb; the file on disk is 3ac18ad769996410 (15994 B, mtime 2026-09-28 03:22:17)", "severity": "major", "evidence": "runs/accept-137/artifact_hashes.json"},
    {"what": "Report section 3.5 says the 111-entry ledger splits into 16 manual-backfill + 95 wrapper entries; the real split is 17 + 94 (wrapper entries carry no source field)", "severity": "minor", "evidence": "runs/accept-137/my_redirect_scan.json; t136_cmd.py:52 writes {ts,cwd,argv} only"},
    {"what": "The ledger hash quoted 'as of 111 entries' cannot be checked and the entry after the cutoff are not only wrap-up commands: entries 112-116 include pytest tools/tests -q and playtest_player.py selftest; the commit message of 49c919a still says '93 commands scanned'", "severity": "minor", "evidence": "t136_commands.jsonl rows 105-116; git log -1 --format=%B 49c919a"},
    {"what": "The 'first version' report hash f98a4575876a0d81 / 55665 B cannot be verified: the file on disk is 7c5a1738e601e018 / 58488 B (the self-referential docs-only commit changed it)", "severity": "minor", "evidence": "runs/accept-137/artifact_hashes.json; report section 11.4"},
    {"what": "Report section 4.1 puts 'FAIL' in the strict column for the scripted platformer row; that run's player.json verdict is INCONCLUSIVE (strict_verdict=FAIL, game_side_verdict=FAIL, baseline_verdict=PASS)", "severity": "minor", "evidence": "runs/model-player/t136-scripted-final/platformer/scripted/player.json; runs/accept-137/recount.json"},
    {"what": "Report section 1.2 lists platformer as a baseline-PASS/strict-FAIL run whose top-level verdict is PASS(baseline only); its top-level verdict is actually INCONCLUSIVE (the real PASS(baseline only) instances are pong and asteroids)", "severity": "minor", "evidence": "as above; asteroids verified to be the genuine PASS(baseline only) with counts_as_pass=false"}
  ],
  "risks": [
    "R1: the action window is measured over 2.5x-3.7x more drawn frames than its own control window (target_delta is equal at 30 for 409/409 steps, but achieved_delta median 138 vs 51 for the model arm and 119 vs 33 for the scripted arm), so the tool's own claim that the two windows are 'the same length in game frames' (playtest_player.py:2476-2478) does not hold in practice; the direction favours 'changed' but the strict margin (>=2x one's own control) keeps the bar conservative.",
    "R2: ack has a narrow fallback - playtest_player.py:2326 uses inj.ack_result or pre_ack, and pre_ack is read BEFORE injection, so a residual key-down from the previous step could in principle be credited as this step's ack; 409/409 recorded steps avoided that path.",
    "R3: step counts and match seconds jitter between runs (my pong rerun: 9 vs the recorded 10 steps); only the verdict/rate are stable.",
    "R4: runs/** is gitignored, so every piece of evidence cited here (and my recomputation) exists only on this machine.",
    "R5: the 'legitimate refusal is not recognised by the criterion' backlog is unchanged and was not quietly patched (refusal_evidence.keys is still LastRefusedInput|Rejected).",
    "R6: 15 of the 20 model-arm runs are INCONCLUSIVE; the report says so explicitly and does not claim the model can play 20 games - my recount supports that restraint."
  ],
  "unverifiable": [
    "The 'the reader looked at the before/after frames and judged the changes match the game's logic' half of criterion 3 (section 0.3) cannot be fully re-verified here: it would require reading all 409 step frame pairs, and /recovery/reports only quotes 20 named frames. I verified those 20 exist at 800x600 and read 11 of them myself; the remaining per-step reader judgements are unverifiable.",
    "Report section 11.2's 'first version' report hash (f98a4575876a0d81, 55665 B) is unverifiable because the docs-only commit rewrote the same file; the only checkable fact is the current on-disk hash 7c5a1738e601e018 / 58488 B.",
    "The exact ledger hash e24685fc09eaa3c1 'as of 111 entries' cannot be reproduced: the ledger is append-only and now has 116 lines, and jsonl line order/timestamps cannot be rewound. I re-verified the 111-entry SCAN RESULT (3 hits, verbatim text) instead.",
    "I did not re-run the 20-game model arm (it needs the 8080 service for 20 games x 12 steps); I recomputed its distribution from the recorded player.json/steps.jsonl, which is sufficient for the distribution claim but not for a fresh end-to-end model run.",
    "The 20-game scripted sweep as a whole was not re-run (I re-ran 3 games); the other 17 rows were recomputed from their artifacts."
  ]
}
```

---

*报告结束（ACCEPTANCE-TASK-137）。*
