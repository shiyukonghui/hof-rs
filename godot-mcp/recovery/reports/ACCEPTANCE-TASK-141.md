# ACCEPTANCE-TASK-141 — 独立验收报告：游戏逻辑反馈机制（判据 / 工具 / 模板 / 20 款结论）

> **验收方身份**：独立验收（`TASK-141-ACCEPT.md`）。**未继承**实施者或决策者的任何结论。
> 只读 §0 判据、**代码**、**我自己跑出来的可复现证据**。任务书里的每个数字都当作"待核对转述"重算。
> **严格单线程**：本批**没有**派任何子代理（无 `subagent` / `workflow` / `ralph` 调用）。
> **只读验收**：未改任何游戏代码 / 工具 / 既有证据；所有新产物只落在 `runs/accept-141/**` 与本报告。
> **禁止 shell 重定向**：本批所有命令经 `subprocess.run(shell=False)` 或工具调用执行，
> stdout/stderr 由 Python 句柄写盘；台账 `runs/accept-141/accept141_commands.jsonl`（`source=accept141-own-run`）。
> `git status --short` 复扫：**只有 3 个既有未跟踪文件**（TASK-137 的两件 + 本任务书），**无任何 `M`/`A`**。
> 本人产出的证据目录：`godot-mcp/runs/accept-141/`（内含本报告引用的每一个数字）。
>
> **TASK-149 追加（2026-09-28，只增不改）：本报告里 `tools/playtest_player.py:NNN` 的行号指针
> 指向本报告验收当时的冻结版本，不是现在仓里的版本。** 原因与 ACCEPTANCE-TASK-137 的同类注记
> 完全相同：TASK-142 那批改动（已由 TASK-149 §B 作为「已中止支线」入库，`71f92e8`）在该文件里
> 插了几段新代码，原版字节冻结在 `tools/playtest_player_t142_prefix.py`
> （= `71f92e8^:godot-mcp/tools/playtest_player.py`，**4905 行**，277930 B）。**结论一字未变**，
> 变的是行号；而且**位移不是常数**（插了 4 段），实测分段为 **+58 / +99 / +119 / +174**。
> 本报告被点名引用过的指针，逐条实算如下：

| 本报告写的指针（冻结版） | 现在的位置 | 位移 |
|---|---|---|
| `:2286-2308` **`_pong`**（F-2 的机制代码） | `:2405` 起，同一分支 `:2476-2489` 一带 | **+119** |
| `:3804-3813` patience 提前停止（`ok_ack_and_changed` + 动作多于 1 种） | `:3978` 起 | **+174** |
| `:349` `MODEL_PLAYER_REFUSAL_FALLBACK` | `:407` | +58 |
| `:1170` `below_reporting = bool(...)` | `:1228` | **+58** |
| `:1213-1230` `verdict_context` 的写入 | `:1270` 的注释 / `:1271` 的 `ctx = {` / `:1287` 的 `out["verdict_context"] = ctx` | **+58** |
| `:1234` `def verdict_class(verdict)` | `:1292` | **+58** |
| `:387` `def step_refusal_record`；`:400-404` / `:407-416` 的字段筛选 | 分别 `:445` / `:458-462` / `:465-474` | **+58** |
| `:3253`（TASK-138 defect ⑨ 的注释） | `:3428`（`ack_state_for_verdict` 不回退 `pre_ack`） | **+175** |

> 复算任一指针：`python recovery\work\task149_stalepointers.py ACCEPTANCE-TASK-141`（打印每个
> 指针**今天**落在哪一行、该行原文、以及前后 60 行内的 `def`/`class` 符号，读者可自行比对）；
> 冻结版与当前版的符号行号对照另见 `python recovery\work\task149_frozenmap.py`。
> **本报告没有逐条改写行号**——改写等于把事后推断混进当时的验收记录。

---

## 0. 一句话结论

**`verdict: pass`** —— §0 的九条判据全部成立，**没有一条 blocker**：
`reporting_frames` / `counts_as_pass` / `UNSTABLE` / `ack` 缺失不回退 / `refusal_evidence` 来源
**都在代码里真的生效**（逐处 file:line 见 §A）；**低于 90 档拿不到 PASS**（我自己构造 11 个档位验证）；
两条分布、两个 `UNSTABLE` 触发、4 款修前→修后、`dotnet build`、P1–P7 **我都自己重算/自己复现**，数字与报告一致；
6 张全尺寸 800×600 原图 **我自己 `read_image` 读过**，与 §C.7 逐帧表+锚点一致。

发现 **0 个 blocker、7 个 major/minor 级缺陷**（§F），其中值得上报方注意的两条：

1. **报告 §I.3/§F 的命令条数自相矛盾**（同一份报告里同时写 **194** 与 **186**，两处 `186 条`），
   而权威台账切点给出的是 **194**（我独立复算一致）。**核对项"194 条 / 0 命中"成立**，
   但**报告的自我描述数字不可自洽**（见 §F-1）。
2. **我自己跑的 `pong`（脚本臂）在报告档位 w90 上并不是可复现的 PASS**：
   4 次独立运行读到 `INCONCLUSIVE` / `PASS` / `PASS(baseline only)` 三个不同类别
   （3 个类别差异只来自 `Ball.Velocity` 在采样瞬间是否为 0，从而改变了脚本策略的取动作与
   "8 步不同动作"提前停止条件；**同一字节相同的命令**）。这不是本批判据的 blocker
   （`UNSTABLE` 机制本身正确地只为"同一档两轮"而设），但它说明
   **报告 §C.2 的"20 款 w90 两轮一致"是"这两轮一致"，不是"这一档可复现"**——
   报告自己在 §G.1/§C.2 的 `breakout` 上承认了这一点，我的 pong 数据把同一结论**第二次**坐实（见 §F-2）。

---

## A. 判据机制（读代码 + 构造反例）

### A.1 `reporting_frames` / `counts_as_pass` **真的在代码里生效**

| 机制 | 落点（文件:行，本仓 HEAD `1b0ccb6`） | 我读到的实现 |
|---|---|---|
| 声明 | `tools/playability_controls.json:392` `"reporting_frames": 90`；`:395` `reporting_basis`；`:408` `not_a_loosening` 条目 | 声明存在，含实测依据，含"只能拿走"边界 |
| 读声明 | `tools/playtest_player.py:255` `load_window_declaration` → `:282-285` 读 `reporting_frames`（缺省 90）；`:302-304` 模块常量 | 工具与 gate 读**同一块** |
| 计算 | `tools/playtest_player.py:1170` `below_reporting = nominal < WINDOW_REPORTING_FRAMES`；`:1192-1198` `counts_as_pass=False` / `pass=False` / `reporting_why`；`:1176-1178` `state=BELOW_REPORTING_WINDOW`；`:1230` `qualified_verdict` | **`verdict` 字符串不被改写**（只加标签），`counts_as_pass` 被强制 false |
| 归因 | `:1213-1230` `verdict_context` = `{window_frames, round, reporting_frames, at_reporting_window, ...}`、`qualified_verdict` = `PASS @w90 r1` | 每处 verdict 带档位+轮次 |
| gate 侧 | `tools/playability_gate.py:3015-3049` 同一收口；`:2581` `record_model_player_criterion` 从 `steps.jsonl` **旁边**的 `player.json -> verdict_context` 读回；`:2617-2625` 用 `playtest_player.nominal_frames_of_run` 回退读 `session.json` | gate 不发明档位 |

### A.2 **低于 90 档能否拿到 PASS**（我自己试，反例构造）

反例脚本：`runs/accept-141/p15_counterexample.py`（我自己写的 records，不复用 shipped test），
输出 `runs/accept-141/indep_counterexamples.txt`（**62 条检查**）。逐档实测：

| 标称 `--window-frames` | 测得 verdict | `counts_as_pass` | `qualified_verdict` |
|---|---|---|---|
| `None`（未记录） | `PASS` | **True** | `PASS @w? r1` |
| 0 / 1 / 19 / 20 / 29 / 30 / 45 / 89 | `PASS` | **False** | `... [reference only: window N < reporting 90]` |
| **90** | `PASS` | **True** | `PASS @w90 r1` |
| 120 | `PASS` | **True** | `PASS @w120 r1` |

* **结论**：`0 ≤ N ≤ 89` 全部 `counts_as_pass=False`；边界 **90 不被过度收紧**。
  反向也成立：`changed=False` 的 run 在 w30 与 w90 都 **不** PASS（"只能拿走"）。
* **`None` 的例外**（`p15` 检查 A3 MISMATCH，实为**声明行为**）：未记录标称窗时 `counts_as_pass=True`。
  代码 `:1199-1202` 与声明 `playability_controls.json:408` 明写"缺测量既不加也不减"。
  **判为可接受的风险**（`risks` 第 1 条）：CLI 侧 `--window-frames` 有默认值且必被记录（`session.json`），
  所以真 run 不会走到这一支；但**一个手工构造的 `summarise()` 调用或缺失 `verdict_context`+`session.json`
  的历史 run 可以在这个档位上拿到 `counts_as_pass=True`**。
* **实测真 run 的触发**（不是只有单测）：`runs/model-player/t140-w30-demo/asteroids/scripted/player.json`
  → `verdict=PASS`、`counts_as_pass=False`、`reporting_window.state=BELOW_REPORTING_WINDOW`、
  `qualified_verdict="PASS @w30 r1 [reference only: window 30 < reporting 90]"`。
  我**自己**对 `t139-scripted-w30/asteroids/scripted` 走读路径复算：`nominal_frames_of_run` →
  `(30, 'session.json->measurement_window.frames')`，`summarise` → `counts_as_pass=False`；
  gate 侧 `record_model_player_criterion` → `pass=False`、`label=PASS @w30 r? [reference only: ...]`。
  **历史 w30 run 也拦得住**（报告 §G.7 的声明成立）。

### A.3 `UNSTABLE` **真的在代码里生效**，且两个触发都能从产物复算

* 落点：`playtest_player.py:1234` `verdict_class`（`PASS` 与 `PASS(baseline only)` 是**两个类别**；
  `WINDOW_TOO_SHORT ...`、`MODEL_*` 各自成类）；`:1276` `divergence_between`（只比
  `injected`/`accepted`/`ack_missing`/`changed`/`changed_strict`/`step_verdict`，像素只作 context）；
  `:1308` `stability_summary`（<2 轮 ⇒ `INSUFFICIENT_ROUNDS`；类别全同 ⇒ `STABLE`，且**只有每一轮都是字面 `PASS`**
  才 `counts_as_pass=True`；任一不同 ⇒ `UNSTABLE` + `divergent_rounds` + `divergence_points`，`:1389` 强制 false）。
* 我**自己**重新计算（`runs/accept-141/p09_stab.py`，直接读 6 个前缀的 `player.json` + `steps.jsonl`，
  不读批次的 `t140_results_*.json`）：

| 臂 | `UNSTABLE`（我重算） | 与我用的工具给出的分歧点 |
|---|---|---|
| scripted 20×2 | **无** | — |
| jev 20×2 | **`asteroids`** | `step 6 changed_strict r1=True r2=False（pixel_diff 965 vs 968）` + `step 9/10/11/12 step_present r1=False r2=True` |
| playjev 10×2 | **无** | — |
| 跨批 breakout/scripted @w90（3 次独立完整运行） | **`UNSTABLE`** | `step 2/3/4` 的 `injected`/`accepted`/`changed`/`changed_strict`/`step_verdict`：`ok_ack_and_changed` ↔ `no_ack_no_change` |

* **分歧点核对**：任务书问"分歧点是否真是 step 6 的 `changed_strict` 差 3 像素与 ack 丢失"——
  **两条都成立**：`asteroids` 的 step 6 正是 `changed_strict`（`pixel_diff 965 vs 968`，差 **3** 像素）；
  `breakout` 的分歧点是 `no_ack_no_change` ↔ `ok_ack_and_changed`（**ack 丢失**）。
  完整 `divergence_points`：`runs/accept-141/indep_stability.txt`。
* 批次自己的产物一致：`t140_stability_model.json -> unstable_games=['asteroids']`、
  `t140_unstable_breakout.json -> state=UNSTABLE, classes={'1':'INCONCLUSIVE','2':'INCONCLUSIVE','None':'FAIL'}`。

### A.4 `ack` 缺失 ⇒ `INCONCLUSIVE_ack_missing`，**不回退 `pre_ack`**

* 落点：`playtest_player.py:3253-3293`（缺失即写 `ack_missing` 记录，`pre_ack_used_as_evidence: False`）；
  `:3300-3311`（**无条件**强制 `injected=False` / `accepted=False` / `evidence_used="ack_missing"` /
  `step_verdict=INCONCLUSIVE_ack_missing`）；`:3354-3357` `ack_pre_read.used_as_evidence=False`；
  `:1078-1096` `player.json -> ack_missing`（条数 + 逐 step + `pre_ack_fallback: False`）。
  旧实现（`inj.get("ack_result") or pre_ack`）在 `:3253-3258` 的注释里被**点名**。
* 我的反例（`p15` 检查 A6a–A6i，**9 条全 OK**）：8 个缺失 ack 的步 ⇒ `counts_as_pass=False`、
  **不是 FAIL**、`accepted_steps=0`、`accepted_and_changed_rate=None`（不是 1.0）、
  `pre_ack_recorded_only.is_action_pressed=True`（**证明"若不回退就会误判接受"**）而
  `pre_ack_used_as_evidence=False`。
* 批次的 shipped 测试也覆盖：`tools/tests/test_playability_model_player.py:4512-4571`
  （"the pre-injection reading alone WOULD have said accepted" + "the recorded step still says it was not accepted"）。
  我**自己跑**过该文件：rc=0，`task140_cases PASSED (41 assertions)`、`task139_cases PASSED (67)`、
  合计 **108 assertions**（`runs/accept-141/evidence_test_playability_model_player.stdout.txt`）。

### A.5 `refusal_evidence` 来自**游戏自己的状态导出**；"全拒绝零推进"**真的**被否

* 来源链：`playability_gate.probe_state_source()` 在游戏进程内读导出属性 → 注入前后 diff 成
  `steps.jsonl -> state_delta` → `playtest_player.step_refusal_record`（`:387-435`）只认
  **`from != to` 的项**（`:400-404`，直击 TASK-139 反例 24）且优先匹配
  `games.<game>.refusal_evidence.game_side_fields`（`:407-416`）。**模型自述不参与**。
* 声明清单（我自己从 `playability_controls.json` 读出）：**6 款**带 `game_side_fields`
  —— `bomberman[RejectedMoves,RejectedPlaces]`、`match3[RejectedMoves,InputRejectedSwaps]`、
  `minesweeper[RejectedMoves,InputRejectedCursorActions]`、`pacman[RejectedSteps]`、
  `sokoban[RejectedMoves]`、`towerdefense[InputRejectedPlaces]`。
  ⇒ 任务书 §0.7 点名的 **5 个字段全在**（第 6 个 `RejectedPlaces` 是本批为 bomberman 新加）。
  **注意**：TASK-140 §0 写"`refusal_evidence` **5 款**已声明"，而仓库里是 **6 款**——
  这是**文档陈述与实际声明不符（minor）**，不影响判据（多声明一款不放松判据，反而更严）。
* 我的反例（`p15` 检查 A8–A12，**全 OK**）：
  * 全拒绝零推进 ⇒ `refusal_only_run=True`、`verdict=FAIL`、`counts_as_pass=False`、`real_progress_step_count=0`；
  * 拒绝 + ≥4 步真实推进 ⇒ **不**被地板打成 INCONCLUSIVE；
  * 拒绝 + <4 步真实推进 ⇒ `INCONCLUSIVE`，永不 PASS；
  * **无拒绝的 run 逐位不变**（`refused_steps=[]`、rate=1.0、`PASS`）；
  * 字段"出现但没动"（`from == to`）**不算**拒绝证据；动了才算，且证据串是游戏自己的 delta。
* **边界值核对**：`model_player_refusal.min_real_progress_steps = 4`（声明 + `playtest_player.py:349` 兜底）。

---

## B. 结论可复现（我自己跑）

### B.1 我自己的运行（命令与批次**逐字相同**，端口唯一高位；输出 `runs/accept-141/run_*.out.txt`）

| # | 命令（`--steps 12 --window-frames 90 --round N --change-margin strict`） | 端口 | 我测到的 verdict |
|---|---|---|---|
| 1 | `--game pong --backend scripted --player scripted --variant V1` | 9421 | `INCONCLUSIVE @w90 r1`（6/12 可注入步） |
| 2 | 同上，第二轮 | 9422 | `INCONCLUSIVE @w90 r2` |
| 3 | `--game snake --backend scripted` | 9426 | **`PASS @w90 r1`**（8/8，rate 1.0） |
| 4 | `--game tetris --backend scripted` | 9433 | **`PASS @w90 r1`**（8/8，early stop） |
| 5 | `--game pong --backend scripted`（第 3 轮） | 9431 | **`PASS @w90 r3`**（8/8，early stop） |
| 6 | `--game pong --backend scripted`（第 4 轮） | 9432 | **`PASS(baseline only) @w90 r4`**（步 5 接受未变） |
| 7 | `--game pong --backend jev --variant V3` | 9434 | `PASS(baseline only) @w90 r1`（与批次两轮一致） |
| 8 | `--game tetris --backend jev --variant V3` | 9435 | **`PASS @w90 r1`**（与批次两轮一致） |
| 9 | `--game snake --backend jev --variant V3` | 9436 | `INCONCLUSIVE @w90 r1`（步 10 终止，与批次两轮一致） |

* **与报告逐项对照（telex 抽 same 部分）**：
  * `snake` 脚本：批次 r1/r2 = `PASS`；**我的 r1 = `PASS`**，且 **8 步逐字段与批次一致**
    （`snake_right ×3 → snake_up → snake_left ×3`，`px=2880/2880/2880/3456…`，`mv=146.0/146.0/146.0/899.303…`
    —— 见 `runs/accept-141/indep_cmp_pong.txt` 的"逐 step"段，我把它与 `t140-scripted-w90-r1/snake` 并排）。
  * `tetris` 脚本/模型：批次 = `PASS`；**我的 = `PASS`**。
  * `pong` 模型臂：批次两轮 = `PASS(baseline only)`；**我的 = `PASS(baseline only)`**（步 2 接受未变，`why` 逐字相同）。
  * `pong` **脚本臂：批次两轮都 `PASS`（8 步提前停止）；我的 4 次运行读到 3 个不同类别**（见表）；
    机制已定位到脚本策略在状态采样瞬间 `Ball.Velocity==0` 时永远选 `pong_serve`
    （`playtest_player.py:2286-2308` 的 `_pong`），于是"8 步里动作需多于 1 种"的提前停止条件
    （`:3804-3813`）不成立、run 走满 12 步、可注入步 **6 < 8** ⇒ `INCONCLUSIVE`。
    **同一字节相同的命令、同一份代码**。详见 §F-2。
* **`UNSTABLE` 两轮检验**：我对同款同档跑了 **2 轮以上**（pong ×4、snake ×2、tetris ×2）。
  对我自己的 pong 4 轮调用 `stability_summary` ⇒ `UNSTABLE`（`INCONCLUSIVE`/`PASS`/`PASS(baseline only)`）；
  即"同款同档 ≥2 轮不一致 ⇒ `UNSTABLE`、不计入 PASS"这条规则在我自己的数据上**确实会触发**。

### B.2 两条分布——**我自己重算**（`runs/accept-141/p08_distrib.py`，从每个 run 的 `player.json` 读，不看批次汇总）

| run 前缀 | 我的重算（PASS / baseline-only / FAIL / INCONCLUSIVE） | 报告声称 | 一致？ |
|---|---|---|---|
| `t140-scripted-w90-r1` | **17 / 1 / 0 / 2**（20 款） | `17/1/0/2` | ✅ |
| `t140-scripted-w90-r2` | **17 / 1 / 0 / 2** | `17/1/0/2` | ✅ |
| `t140-jev-v3-w90-r1` | **2 / 1 / 2 / 15** | `2/1/2/15` | ✅ |
| `t140-jev-v3-w90-r2` | **1 / 2 / 2 / 15** | `1/2/2/15` | ✅ |
| `t140-playjev-v3-w90-r1` | **4 / 0 / 1 / 5**（10 款） | `4/0/1/5` | ✅ |
| `t140-playjev-v3-w90-r2` | **4 / 0 / 1 / 5** | 同上 | ✅ |
| `t139-scripted-w30` | 15 / 1 / 0 / 4 | `15/1/0/4` | ✅ |
| `t139-scripted-w90` | 15 / 0 / 1 / 4 | `15/0/1/4` | ✅ |
| `t139-jev-v3-w90` | 1 / 1 / 2 / 16 | `1/1/2/16` | ✅ |
| `t139-playjev-v3-w30` | 3 / 0 / 1 / 6 | `3/0/1/6` | ✅ |

* **`counts_as_pass=True` 的款数也逐臂一致**：scripted 17 / jev 2(r1)→1(r2) / playjev 4；
  与 §C.4 的"脚本 17"和"模型 r1→r2 的差额来自 `asteroids`"逐条吻合。
* **批次自己的稳定性产物我也读了**：`t140_stability_{scripted,model,playjev}.json` 的 `distributions`
  与报告三张表**逐格相同**，`unstable_games` / `sensitive_games` / `cross_batch_differing_games`
  也与报告文字相同（`runs/accept-141/p30` 输出）。

### B.3 4 款修复的"修前缺陷 → 修后消失"（我自己复现 ≥2 款）+ build + P1–P7

**(a) `asteroids` 重生 —— 我用自己的定向探针复现（`runs/accept-141/p18_respawn.py`，
`runs/accept-141/respawn-probe/probe.json`）**：不用批次的 `ForceTestState("ship=650,130")` 触发撞击，
只把船放到空地 (520,130) 并给它 **320 px/s** 的速度，让它**自己飞进**游戏自己放在 (650,130) 的岩石
（岩石位置由游戏自己的 `RockList()` 读出：`0:s3@150,140|1:s3@650,130|2:s3@180,470|3:s3@640,460`）。

| case（走游戏自己的开关） | 撞击样本 | 之后 `ShipAlive` 序列 | `Respawns` | `RespawnTimer` | 最长连续 `pixel_diff=0` | 结论 |
|---|---|---|---|---|---|---|
| `RespawnDelay=0`（= 修前行为） | 第 3 样本 `Lives 3→2` | `F,F,F,…`（**24/24 全 F**） | `0` | 全 0 | **23** | **修前的"死亡即冻结"被按需复现** |
| 出厂默认 `1.0 / 1.5` | 第 3 样本 `Lives 3→2` | `T,T,F,F,F,**T**,T,…` | **`0→1`（第 6 样本）** | `0.808 → 0.508 → 0.225 → 0` | 4 | **撞 → 掉一命 → 约 1 s 后重生，画面重新变化** |

* 默认 case 的重生后像素序列出现 `484 / 484 / 0 / 484 / 0`（护盾闪烁）——**画面重新动起来**。
* `read_image`：`runs/model-player/t140-respawn-probe/asteroids/frames/032_default_respawn_1s_05.png`
  = HUD `SCORE 0  LIVES 2  ROCKS 4` + **青色飞船回到场地中心**；死亡窗口帧
  `003_variant_respawn_delay_0_01.png` = `SCORE 0  LIVES 2  ROCKS 4` + **画面里没有飞船**。
* **跨批逐字节复核**：`t140-prefix4-w90-r1/asteroids/scripted`（修前）8 步里 `real=8/rate=1.0` 是**跑测**读数；
  而 taskbook 点名的"连续 7 步零变化"来自 TASK-139 模型臂。我核对了它的两帧 sha256：
  `t139-jev-v3-w90/asteroids/jev/frames/016_05_after.png` 与 `037_12_after.png`
  **都是 `c09b58739e8d3094b081f997554e29ca6e602b55d2acdc757664aaa92ddefe4d`（10111 B, 800×600）**，
  且 `read_image` 实看：两帧**都没有飞船**（HUD `SCORE 0 LIVES 2 ROCKS 4`）。**修前缺陷成立。**

**(b) `frogger` 单次注入不连丢命 —— 从 `steps.jsonl` 逐 step 复算**

| | 注入步数 | 每步位移 | `Lives` | `GameOver` | verdict |
|---|---|---|---|---|---|
| 修前 `t140-prefix4-w90-r1/frogger/scripted` | **1** | 青蛙**没离开出生格** | **`3 → 0`**（一步丢 3 命） | `False → True` | `INCONCLUSIVE` |
| 修后 `t140-postfix4-w90-r2/frogger/scripted` | **8** | 每步**恰好一格**（`FrogRow 14→13→12`、`FrogCol 6→7`、…），每步 `px=1152` | **`3` 全程不变**（0 掉命） | `False` | **`PASS`**（`counts_as_pass=True`） |

* 修前那一步的 `LastEvent`：`lives lost reason=hit by car at=6,13 lives=0 game over`——即**出生格正上方 (6,13)
  有车**。修后出生列正上方那辆车被挪到 col 1（读图复核，见 §C）。
* `read_image` 修前 `004_01_after.png`：HUD `SCORE 0 LIVES 0 HOMES 0/5` + `GAME OVER`，
  绿青蛙仍在**最底部绿色出生带**；修后同帧：HUD `SCORE 0 LIVES 3 HOMES 0/5`，
  青蛙**已上移一行**（y≈530–538），同车道黄车在 **col 1**。
* **"修后一次注入恰好掉 1 命"没有实测帧**——这一条报告 §G.5 **自己承认了**（我复核 `steps.jsonl`：
  修后 run 全程 `Lives 3`）。**未被掩盖**。

**(c) `bomberman` 炸弹可见 + 拒绝留痕**（我逐 step 复算 + 读图）

| | 步 1 | 步 3 | 步 5/7/9 |
|---|---|---|---|
| 修前 `t140-prefix4-w90-r1` | `BombsActive 0→1`、`BombList ''→'1,1,3'`、**`px=138`**、**无** `BombsVisible` | `BombsActive 1→2` | `bomb_place` **`px=0`、`refused=False`、状态差分为空**（静默丢弃） |
| 修后 `t140-postfix4-w90-r3` | 同 + **`BombsVisible 0→1`**、**`BombMinContrast 0.0→0.79999995`** | 同 + `BombsVisible 1→2` | **`refused=True`**，`RejectedMoves` 递增 **且新增 `RejectedPlaces`**（`0→1→2→3`） |

* `read_image`（全尺寸 800×600）：修前 `007_02_after.png` = 玩家 (1,2) 的**上一格 (1,1) 是空地板**；
  修后同帧 = **同一格有一颗橙红炸弹**（像素位置 [178,126,26,26] 与状态逐字吻合）。**修前→修后差异肉眼可辨。**
* `AutoClock` 取舍：代码 `projects/bomberman/src/BombermanGame.cs:248` `[Export] public float AutoClock = 0.0f;`，
  注释 `:43-53` 明写"保持 0 + 代价是 `Detonations` 在 playtest 里恒 0"。**取舍已写明，未掩盖。**

**(d) `flappy` 两窗都在"世界在跑"下成立**（我逐 step 复算，用正确的字段名 `control_diff.pixel_diff`）

| | 对照窗 `pixel_diff` | 对照窗 `movement` | 动作窗 `pixel_diff` | 动作窗 `movement` | 结论 |
|---|---|---|---|---|---|
| 修前 `t140-prefix4-w90-r1` | **0**（全 12 步） | `0.0` | **0**（步 2–12） | `0.0` | 世界不自走，`real=1`、`rate=0.0833` |
| 修后 `t140-postfix4-w90-r2` | `45590 … 74290`（管子真的在滚） | `2464 … 2494` | `103172 … 128294` | `792 … 3005` | 两窗都在运行；`real=8`、`rate=0.8889`、`PASS(baseline only)` |

* 报告 §B.4 引的 `ctl_px=45590..74290` / `cmv=2476..2494` / `px=109135..128294` **逐字可复算**（我上面同源）；
  它的措辞把"对照窗的像素计数字段"称作 `ctl_px`，我一开始按 `control_diff.changed_pixels` 读得到 `None`，
  实际字段名是 **`control_diff.pixel_diff`**——**不是伪造，是命名不同**（`change.control_pixels` 同样持有该值）。
* `read_image`（全尺寸）：修前 `002_01_before.png` = HUD `SCORE 0 PASSED 0/5 FRAME 0`、黄鸟**悬在近地空中**；
  修后 `002_01_before.png` = HUD `SCORE 20 PASSED 2/5 FRAME 291`、黄鸟**栖在底部深绿触地条上**。
* **`flappy` 仍不是 PASS**（`PASS(baseline only)`、`counts_as_pass=False`），报告 §G.2/D208 承认并给了结构性原因。
  我复核了 strict 的失败原因：步 1 的 `pixel_wins=False`（`128294 < 2.5×74290=185725`）
  且 `gameplay_wins=False`（`2980.556 vs 2494.0`，ratio 1.195 < 2.0）——**与报告一致**。

**(e) `dotnet build`（我自己跑，`runs/accept-141/p23_build.py`）**

| 项目 | exit | 错误 | 告警 | 生成物 |
|---|---|---|---|---|
| `projects/asteroids` | 0 | 0 | 0 | `asteroids.dll` |
| `projects/frogger` | 0 | 0 | 0 | `frogger.dll` |
| `projects/bomberman` | 0 | 0 | 0 | `bomberman.dll` |
| `projects/flappy` | 0 | 0 | 0 | `flappy.dll`（`已成功生成`、`0 个警告 / 0 个错误`） |

`BUILD CLEAN: 4/4 clean (exit 0, 0 errors, 0 warnings)`。日志逐份落在 `runs/accept-141/build/*.txt`。

**(f) P1–P7 抽一款复核（我自己跑 `tools/playability_gate.py`）**

* `--games asteroids --port 9451 --model-player-steps <t140-scripted-w90-r1/asteroids/scripted/steps.jsonl>`
  ⇒ `P1=PASS P2=PASS P3=PASS P4=PASS P5=PASS P6=PASS P7=PASS`、`per_criterion_fail` 全 0、exit 0；
  gate 侧模型判据：`pass=True PASS @w90 r1`。
* `--only-p7` 同款 ⇒ `P7=PASS`、`criteria_covered=["P7"]`、exit 0。
* 我也读了批次自己的 4 款产物 `t140-gate-4/playability.json`：
  **4/4 款 `P1..P7` 全 PASS、`verdict=playable`**（报告 §E.Y8 的 ✅ 成立）。
* 顺带核实了报告 §E.Y8 的**反例**：该文件里 flappy 的 flap 步 `GameOver False→True`
  （`Status.text: PIPES 3/5 → GAME OVER`，`bird_y=564.0`），**证明"悬停"变体确实还在、默认已改**。

---

## C. 读图与诚实性

### C.1 我**自己 `read_image` 实看**的全尺寸 800×600 帧（≥4 张，每行含可机检锚点）

所有帧的 sha256 / 字节 / 尺寸我都**自己重算**（`runs/accept-141/p25_framehash.py`）——
**§C.7 表引用的 11 个 sha256 前缀全部命中**，尺寸全部 `(800,600)`。

| # | 帧（`godot-mcp/` 起的相对路径） | 我用 `read_image` 看到的 | 与报告 §C.7 的对照 | 锚点（sha256 前 16 / 该步声明字段实测值） |
|---|---|---|---|---|
| 1 | `runs/model-player/t140-prefix4-w90-r1/frogger/scripted/frames/004_01_after.png` | HUD `SCORE 0 LIVES 0 HOMES 0/5` + 右上 `GAME OVER`；绿青蛙仍在**最底部绿色出生带**（col 6 位置） | ✅ 逐条吻合 | `sha256:bf3db4758b74fcaf`；`Lives 3→0`、`GameOver False→True`、`LastEvent='lives lost reason=hit by car at=6,13 lives=0 game over'` |
| 2 | `runs/model-player/t140-postfix4-w90-r2/frogger/scripted/frames/004_01_after.png` | HUD `SCORE 0 LIVES 3 HOMES 0/5`；青蛙**上移一行**（y≈530–538）；同车道黄车在 **col 1** | ✅，仅 `y≈536` 我读到 ≈530–538（24 px 格内），**位置表述不精确但方向正确** | `sha256:fa3cc225e8b609e8`；`FrogRow 14→13`、`Lives` 全程 3 |
| 3 | `runs/model-player/t140-prefix4-w90-r1/bomberman/scripted/frames/007_02_after.png` | HUD `BOMBS 1`；蓝玩家 (1,2)；**上一格 (1,1) 是空地板** | ✅ 逐条吻合 | `sha256:a18448cdbe95a7ed`；该 run 无 `BombsVisible` 导出 |
| 4 | `runs/model-player/t140-postfix4-w90-r3/bomberman/scripted/frames/007_02_after.png` | 同 HUD、同玩家位置；**上一格有一颗橙红炸弹** | ✅ 逐条吻合 | `sha256:bf25a2a153d9096a`；`BombsVisible 0→1`、`BombMinContrast 0→0.79999995`、`Bomb_0.pos [0,0,26,26]→[178,126,26,26]` |
| 5 | `runs/model-player/t140-prefix4-w90-r1/flappy/scripted/frames/002_01_before.png` | HUD `SCORE 0 PASSED 0/5 FRAME 0`；黄色小鸟**悬在近地空中**（x≈195,y≈313）；一列管子 | ✅ 逐条吻合（`FRAME 0` = 世界不自走） | `sha256:0f53a0d32ceb9ad2` |
| 6 | `runs/model-player/t140-postfix4-w90-r2/flappy/scripted/frames/002_01_before.png` | HUD（被管子遮住首字母）`S…E 20 PASSED 2/5 FR…291`；黄鸟**栖在底部深绿触地条上**；多列管子位置各异 | ⚠️ **部分不符**：我数到 **4 列**管子在屏，报告写"**三组**管子"（应为 4 组；属**描述性小错**，不影响结论） | `sha256:9082895f8df88d99`；该步 `frame_count=526`、`control_diff.pixel_diff=74290` |
| 7 | `runs/model-player/t139-jev-v3-w90/asteroids/jev/frames/016_05_after.png` | HUD `SCORE 0 LIVES 2 ROCKS 4`；四角四块米色岩石；**画面里没有飞船** | ✅ 逐条吻合 | `sha256:c09b58739e8d3094`（10111 B） |
| 8 | `runs/model-player/t140-respawn-probe/asteroids/frames/032_default_respawn_1s_05.png` | 同 HUD 与四块岩石；**青色飞船回到场地中心** | ✅ 逐条吻合 | `sha256:d60ff4811ea97444`；`Respawns 0→1`、`InvulnTimer 1.32`、该样本 `pixel_diff=484` |
| 9 | `runs/model-player/t140-respawn-probe/asteroids/frames/003_variant_respawn_delay_0_01.png` | 同 #7：无飞船 | ✅ 与 #7 **同一 sha256**（`c09b58739e8d3094`） | 变体 `RespawnDelay=0`；24 样本 `ShipAlive=False` |

* 我没有把缩略图当成"没变化"的依据；上表 9 行全部是**全尺寸 800×600**。
* **我自己的探针帧**（`runs/accept-141/respawn-probe/frames/`）也读了 2 张，用于 §B.3(a) 的独立复现。

### C.2 报告声明的 **9 条未达标项**（§G）是否**真的**未被掩盖 —— 逐条复核

| §G | 报告写的未达标 | 我的独立复核 | 是否被掩盖 |
|---|---|---|---|
| 1 | w90 不是零方差（`breakout` 第三次读数与前两次不一致） | 我 3 次并排 `stability` ⇒ `UNSTABLE`，分歧点 `step 2/3/4` 的 ack 丢失 | **没有**（§C.2 单列 `CROSS-BATCH` 列） |
| 2 | `flappy` 脚本臂仍是 `PASS(baseline only)` | 我复算 4 个 run，全部 `counts_as_pass=False`；strict 原因（pixel 2.5002× 擦线 + gameplay 1.195×）可复算 | **没有** |
| 3 | `asteroids` 的撞击→重生在跑测/模型臂里没自然触发 | 我逐 step 复核 4 个 asteroids run：无 `Lives` 变化；且我**自己的自然撞击探针成功**（§B.3a） | **没有**（且被我的探针补强） |
| 4 | `AutoRun=true` 副作用（管子越过鸟 x 也记分） | 代码 `FlappyBirdGame.cs:480-483` 确认计分规则；我的探针/gate 数据可见 `passed` 自增 | **没有**（代码与数据都成立） |
| 5 | `frogger` 的"≤1 命"没有修后实测帧 | 我复算修后 run：`Lives 3` 全程不变，确实没有"掉 1 命"的帧 | **没有**（如实写为未达标） |
| 6 | `bomberman` 的 `Detonations` 在 playtest 里仍恒 0 | 代码 `AutoClock=0`；我复算的 step 数据无 `Detonations` 变化 | **没有** |
| 7 | 历史 run 的标称窗回退读取 | 我自己走 read 路径：`t139-scripted-w30` → `(30,'session.json->measurement_window.frames')` → `counts_as_pass=False`（gate 侧同） | **没有** |
| 8 | `UNSTABLE` 的轮次标签对 TASK-139 run 显示 `None` | 我读 `t140_unstable_breakout.json`：`classes={'1':..,'2':..,'None':'FAIL'}` —— 确实显示 `None`、不猜编号 | **没有** |
| 9 | 工具修订与 run 的对应关系（链后修改只影响回退路径） | 台账里 `playtest_player.py` 的 `resummarise`/回退相关命令与 sweep 命令的时间戳我抽查过；`t140_cut_probe.py`(09:49:10) 在末次扫描之后 | **没有** |

### C.3 重定向自查 —— 我**自己重扫台账**（`runs/accept-141/p05_ledger_scan.py`，独立写的扫描器）

* 台账 `runs/model-player/_scripts/t136_commands.jsonl`：**710 行**（验收时），
  `source` 直方图 `{"manual-backfill":39, "(none)":184, "t139-wrapper-call":278, "t140-wrapper-call":209}`。
* **独立切点**（`source == "t140-wrapper-call"` 首条）：index **501**（ts `2026-09-28T07:02:21`），
  与批次产物 `t140_redirect_scan.json -> cut.first_task140_index=501` **一致**。
* **"194 条 / 0 命中"核对**：我用 8 组 token（`2>&1` `2>/dev/null` `1>NUL` `> nul` `>>` `>` `<` `|`）
  独立扫切点后的命令，**命中 0 条**。批次的 194 对应**末次扫描器运行时点**的记录数：
  我按"末次 `t140_scan_redirects.py` 条目之前"重数 = **194**（现在切点后有 **209** 条，
  多出的 **15** 条是扫描之后的收尾命令：`t140_cut_probe.py`、`git add/commit ×7`、
  `t140_tests.py`、`t140_reorder_report.py`、`t140_build_info.py` —— 逐条见
  `runs/accept-141/indep_tail_entries.txt`）。**⇒ "194 / 0 命中"成立。**
* **"2 处台账外命令"核对**：报告 §I.3 声明两处 —— ①包装器出现前约 30 条只读侦察命令；
  ②一条 `python -c` 直接正则改写 `projects/flappy/src/FlappyBirdGame.cs` 的 `Ready→BirdReady`。
  我能核的：台账里 `manual-backfill` 有 **39** 条（与①的说法量级一致）；②的**结果**可核
  ——当前源码导出属性名是 `BirdReady`（`FlappyBirdGame.cs:143`），`dotnet build` 0 警告。
  **⇒ "2 处"这一声明与台账/代码不矛盾（其中①的条数无法逐条复原，属可接受）。**
* **发现的矛盾（major）**：报告 §I.3 两处写"**186 条**"、§F 表也写"**186 条命令**"，
  而 §I 顶部/§E.Y10 写 **194**；我重算的权威切点数字是 **194**。
  **⇒ 报告内部数字不自洽**（详见 §F-1）。

---

## D. 对抗性检查（可能让结论虚高之处）

| # | 检查项 | 我的方法 | 结果 |
|---|---|---|---|
| 1 | 对照窗与动作窗是否**同帧数** | 对 6 个前缀的 **1053 个 step** 重算 `frame_alignment` | `matched=564 (53.6%)`；`residual` 直方图 `{0:564, +1:379, +2:105, +3:4, +23:1}`；`within_5=1052/1053`。**只有 1 步 `|Δ|>5`**，且那一步（`t140-scripted-w90-r2/sokoban step 5`，`control=91 action=114`）**判为"未变化"**（对游戏不利）。⇒ **两窗没有系统性不等长；唯一大偏差反向，不构成虚高**。逐 run 的 `player.json -> frame_alignment.reading` 也随产物落盘（如批次 pong r1：`3/8 matched, max residual 2`）。**报告正文未给出这组聚合数字** ⇒ 记为 minor 漏报（§F-6）。 |
| 2 | `wait` / 合法拒绝是否被当有效动作 | 扫 6 个前缀的全部 step | **`wait` 被 `accepted` 的步数 = 0**；非接受步 187 个（都是无可注入动作）。合法拒绝步**不计入接受率分母、也不计为推进**（代码 `:1520-1533`，我的反例 A8/A9 复核）。⇒ **无虚高**。 |
| 3 | `ack` 是否可能被先前按键污染 | 读 `:3253-3311` 与记录字段；扫全部 866 个 `accepted` 步 | **0 个** accepted 步的 `ack.evidence_used` 不是注入后读数（无 `pre_ack` 回退）。`ack_pre_read.used_as_evidence=False` 逐步落盘。另：我的 `pong` 脚本 run 第 7–12 步 `action=None` ⇒ `injected=False`/`accepted=False`，**没有**把"没注入"混进通过数。⇒ **无污染**。 |
| 4 | 两轮一致是否**掩盖** `SENSITIVE` | 读批次稳定性产物 + 我自己重算 | 三张表的 `SENSITIVE` 与 `UNSTABLE` **并列**；`t140_stability_model.json` 的 `sensitive_games=['asteroids','flappy','pong','spaceinvaders']`、`unstable_games=['asteroids']`；脚本臂 `sensitive=['bomberman','flappy','frogger','platformer','pong']`、`unstable=[]`；playjev `sensitive=['asteroids']`、`unstable=[]` —— **与报告三张表逐格一致**。**未被掩盖**。 |
| 5 | 判据是否被"换尺子/调参"放宽 | 读声明与代码 diff | 两把尺子的公式常量未动（`CHANGE_CONTROL_FACTOR=2.5`、`CHANGE_STRICT_CONTROL_FACTOR=2.0`、`CHANGE_STRICT_MIN_MOVEMENT=1.0`）；`min_frames` / `--window-frames` 语义未动；`reporting_frames` 与 `UNSTABLE` **只能拿走 PASS**（我的 11 档反例 + `UNSTABLE` 反例证实）。4 款修法全部**有开关**（`RespawnDelay` / `RepeatHold`+`DeathGrace` / `AutoClock` / `IdleHover`+`GroundIsFatal`），且我**实测开关的另一半**（asteroids `RespawnDelay=0`）。⇒ **无放宽**。 |
| 6 | 有没有"低于报告档位的读数混进通过数" | 扫 4 个 w30 前缀的 `counts_as_pass` | 4 个 w30 前缀里 `counts_as_pass=True` 的 run 数 = **0**（`player.json` 里历史值为 `True`，但**读路径**一律重判为 reference；gate 侧同）。批次 w90 臂 100 run 全部 `at_reporting_window=true`。⇒ **无混入**。 |
| 7 | 报告是否把"本批两轮一致"说成"这一档可复现" | 读 §C.2/§G.1 | **报告明确纠正了自己**（§C.2 末：`reporting_frames=90` 是必要纪律、不是"这一档可复现"的保证；`UNSTABLE` 应在所有可得的同档运行上算）；模板反例 32 也写了。**但**：报告的三张两轮表仍以"T140 w90 r1 / r2"两列呈现，读者若只看表会得到"两轮一致=稳定"的印象；我**自己的 pong 4 轮数据**说明这不是可复现性保证（§F-2）。 |

---

## E. 与 §0/§3 判据逐条结论

| 判据（§0/§3） | 我的结论 | 我的证据 |
|---|---|---|
| A1 `reporting_frames`/`counts_as_pass` 真生效 | ✅ | `playtest_player.py:1170,1192-1198`；`playability_gate.py:3015-3049`；档位 0–89 全 false、90 true；真 run `t140-w30-demo` |
| A2 `UNSTABLE` 真生效、不进 PASS、有分歧点 | ✅ | `:1234,1276,1308`；`asteroids`（step 6 `changed_strict` 差 3 px + step 9–12 长度差）；`breakout`（ack 丢失） |
| A3 `refusal_evidence` 来自游戏导出、全拒绝零推进非 PASS | ✅ | `step_refusal_record :387-435`；6 款声明；反例 A8–A12；`min_real_progress_steps=4` |
| A4 `ack` 缺失 ⇒ INCONCLUSIVE、不回退 `pre_ack` | ✅ | `:3253-3311`；反例 A6a–A6i；shipped test 反例；无 accepted 步用旧读数 |
| B5 ≥3 款自己跑（报告档位、脚本+模型、≥1 款两轮） | ✅ | 9 次自跑（4 款 × 两臂），`runs/accept-141/run_*.out.txt` |
| B6 自己重算两条分布 | ✅ | `p08_distrib.py`：`17/1/0/2` ×2、`4/0/1/5` ×2，与报告逐格一致 |
| B7 4 款修前→修后 + build + P1–P7 | ✅ | §B.3；`asteroids`/`frogger` 我独立复现；build 4/4 clean；gate P1–P7 全 PASS |
| C8 ≥4 张全尺寸 `read_image` 对照逐帧表+锚点 | ✅ | §C.1 共 **9 张**（+ 我自己的探针帧），sha256 全部自己重算命中 |
| C9 9 条未达标项未被掩盖 | ✅ | §C.2 逐条；无一项被说成已达成 |
| C10 重扫台账（194/0、2 处台账外） | ✅（含 1 处报告数字不自洽） | §C.3；独立扫描器 0 命中；194 = 末次扫描时点；15 条扫描后命令已列出 |
| 硬约束：只读 / 无重定向 / 只用 8080/8081 / 串行 / 唯一高位端口 / 不碰 venv 与 `F:\models` / 不派子代理 | ✅ | 未改任何被保护文件；`git status --short` 仅 3 个既有未跟踪文件；端口 9411–9452 唯一且串行；只调 `127.0.0.1:8080`（jev）/`:8081`（playjev）健康检查与 `playtest_player.py` 自身；**本会话无 subagent/workflow/ralph 调用** |

---

## F. 缺陷与风险

### 缺陷

| id | 内容 | 严重度 | 证据 |
|---|---|---|---|
| **F-1** | **报告的命令条数自相矛盾**：同一份 `TASK-140-REPORT.md` 里 §I 顶部/§E.Y10 写 **194**，§I.3 两处与 §F 表写 **186**；权威台账切点重算 = **194**。§I.3 还写"186 条"作为"本批所有写盘与启动游戏的命令"的总数，与 §I 的 194 互相冲突。 | **major** | 报告 §I（L626/L634）、§I.3（L653/L658）、§F（L536）；我的 `indep_ledger_scan.json`（切点 501、208→209 条）、`indep_tail_entries.txt`（194 + 15） |
| **F-2** | **报告档位下的"两轮一致"不是可复现性保证，且报告未用本批数据把这一点坐实**：我自己对 `pong`（脚本臂，**与批次逐字相同的命令**，w90）跑了 **4 轮**，读到 `INCONCLUSIVE`（r1/r2）/ `PASS`（r3）/ `PASS(baseline only)`（r4）**三个类别**。机制：脚本策略在采样瞬间读到 `Ball.Velocity==0` 就永远返回 `pong_serve`，于是"8 步里动作需 >1 种"的提前停止条件不成立、run 走满 12 步、可注入步 6<8 ⇒ `INCONCLUSIVE`。报告 §C.2 因此把 pong 标成"两轮 PASS、STABLE"，**这个"稳定"只属于那两次抽样**。 | **major**（判据可靠性认知，不推翻 Y1–Y10） | `runs/accept-141/run_scripted-pong*.out.txt`、`indep_cmp_pong.txt`、`accept-141-scripted-w90/pong/scripted/player.json`（`verdict_context.round=2`，12 步）；机制代码 `playtest_player.py:2286-2308` + `:3804-3813` |
| **F-3** | **`task140_cases` 的分段断言条数写错**：报告 §A.1/§A.2 与 `DECISIONS.md` D205/D206 都写"unstable 段 **22 条**"、"reporting 段 14 条"。我按 `check(` 调用逐段数：总数 **41** ✅，但分段是 **5 / 9 / 5 / 16 / 6**（声明 / below-reporting / attribution / unstable / gate）⇒ unstable 段是 **16 条**，reporting 段是 **14 条**（5+9）。"22" 与 "GBATE 6 条" 对不上任何分段。 | minor | `tools/tests/test_playability_model_player.py:706-837`；我的 `p04_count_asserts.py` 输出；报告 §A.1（L68-71）、§A.2（L92）、`DECISIONS.md:7969` |
| **F-4** | **"`refusal_evidence` 5 款已声明"与实际不符**：实际是 **6 款**（多 `towerdefense[InputRejectedPlaces]`；另 bomberman 新增 `RejectedPlaces` 使字段总数 6 个）。任务书/TASK-140 §0 的"5 款/5 字段"是过去时陈述，但报告 §A/§D 未更新口径。 | minor | `tools/playability_controls.json` 的 6 个 `game_side_fields` 块；我的 `probe_refusal.py` 输出 |
| **F-5** | **§C.7 两处描述与图不完全吻合**：(a) 第 2 行"青蛙上移一格（**y≈536**）"，我读到 ≈530–538（24 px 格内，方向正确）；(b) 第 6 行"**三组**管子"，我数到 **4 列**管子在屏。 | minor | §C.1 第 2、6 行；帧 sha256 逐字命中，属描述精度问题 |
| **F-6** | **报告正文没有"两窗同帧数"的聚合读数**：模板 §1.2/§1.2d 要求"报告必须给：对齐方式、目标/达成对照、**相等步数与差值分布**"。报告只给了机制说明与模板/单测引用，**未给本批 1053 步的 `matched=564 (53.6%)`、`max|Δ|=23`、差值分布**（我算了）。 | minor | 报告无 `matched`/`residual` 字样（我 grep 过：0 命中）；我的 `indep_adversarial.txt` |
| **F-7** | **`--steps 12` 被"耐心提前停止"截断会让"步数"含义漂移**：批次 pong 脚本 run 实际只跑 8 步（`early stop`），报告写"8 步 run"，但同一命令的另一次运行会跑满 12 步（我的 run），于是"注入步数/可注入步数"在两个 run 间不可直接比。这本身是工具既有设计，但报告在 §B.1/§G.3 用"8 步全变化"描述"修后证据"时没有点出这个截断条件。 | minor | `playtest_player.py:3804-3813`；`t140_t140-scripted-w90-r1_pong.out.txt` 的 `early stop` 行 vs 我的 `run_scripted-pong.out.txt` |

### 风险（`risks`）

1. **未记录标称窗（`nominal_frames is None`）时不判 `BELOW_REPORTING_WINDOW`**（代码 `:1199-1202`、声明 `:408` 明写）。
   实测路径不会走到（CLI 必记录 `--window-frames`），但**手工 `summarise()` 或缺失
   `verdict_context`+`session.json` 的历史 run 可以在"档位不明"下 `counts_as_pass=True`**。
   建议后续把 `at_reporting_window` 的 `None` 也当作**不可作为 PASS 依据**（而不是"既不加也不减"）。
2. **`UNSTABLE` 只在"喂进去的那些同档 run"之间算**：批次把跨批不一致单列成 `CROSS-BATCH` 列而未进工具自动判定
   （报告 §G.1 自己承认）。我的 pong 4 轮数据说明**同批内也可能不稳**，而本批只跑了 2 轮/款；
   "两轮一致"不足以支撑"这一档可复现"。
3. **`frame_alignment` 的一步大偏差（+23 帧）来自 `wait_achieved_delta=114` vs `absolute_target` 1573
   而 `after_state_drawn` 跳得更远**（`polls=11` 的一次慢往返）。该步判"未变化"（反向），
   没有虚高；但**这种偏差的方向不保证永远对游戏不利**，建议把 `|Δ|>N` 的步单独点名。
4. **我自己的 pong 脚本 run 出现"策略永远选 serve"的新观察**：`Ball.Velocity` 在采样瞬间恒 0
   是**脚本臂的策略/采样时序**问题（不是游戏缺陷，`px=3788/461/337/491/4630/512` 说明画面确实在动），
   但它会让脚本臂在 pong 上给出假 `INCONCLUSIVE`。这是**测量侧**问题，应与游戏结论分开。

### 无法核实（`unverifiable`）

* 报告 §I.3 ①的"约 30 条预台账只读侦察命令"的**逐条原文**无法复原（台账只有 `manual-backfill=39` 这一计数）；
  我确认的是"台账里确有 39 条 `manual-backfill`，且我独立扫描 0 命中"。
* `t140_hash_table.md` 里 115 个 run / 921 个文件的**全量** sha256 我只抽了 11 个证据帧 + 关键 JSON 复核（全部命中），
  未逐文件重算 921 个 hash；`t140_index.py` 生成的 `_index/ARTIFACTS-TASK-140.{json,md}` 我核对了
  其存在与关键字段（`verdict_context` / `qualified_verdict` / `reporting_window`）而非全量内容。
* 我**没有**独立复核 4 个 w30 前缀之外的历史 run 的标称窗回退行为（只验了 `t139-scripted-w30/asteroids/scripted`）。

---

## G. 我跑过的命令（可重跑；完整 argv 见 `runs/accept-141/accept141_commands.jsonl`）

```
python runs/accept-141/p03_tests.py                     # shipped test + selftest
python runs/accept-141/p05_ledger_scan.py               # 独立台账扫描
python runs/accept-141/p08_distrib.py                   # 分布重算
python runs/accept-141/p09_stab.py                      # UNSTABLE 重算
python runs/accept-141/p15_counterexample.py            # 62 条判据反例
python runs/accept-141/p18_respawn.py                   # asteroids 自然撞击探针
python runs/accept-141/p23_build.py                     # dotnet build ×4
python runs/accept-141/p24_gate.py                      # P1-P7 + --only-p7（asteroids）
python runs/accept-141/p26_adversarial.py               # 对抗性
python runs/accept-141/p10_run.py scripted-pong ...
python runs/accept-141/p13_run2.py pong-s3 pong-s4 tetris-s1
python runs/accept-141/p13_run2.py jev-pong jev-tetris jev-snake
```
（`playtest_player.py run` 与 `playability_gate.py` 的**逐字命令**在 `p10_run.py`/`p13_run2.py`/`p24_gate.py` 里，
并经 `accept141_commands.jsonl` 记录；**全程无 shell 重定向**。）

---

## 3. 结构化输出

```json
{ "verdict": "pass",
  "criteria": [
    {"id":"A1","pass":true,"evidence":"reporting_frames 声明 tools/playability_controls.json:392=90（含 reporting_basis:395）; 生效 tools/playtest_player.py:1170 below_reporting -> :1192-1198 counts_as_pass/pass=False, :1176-1178 state=BELOW_REPORTING_WINDOW, :1230 qualified_verdict; gate 侧 tools/playability_gate.py:3015-3049。我自己构造 11 个档位（runs/accept-141/p15_counterexample.py, 输出 indep_counterexamples.txt）：标称 0/1/19/20/29/30/45/89 全部 counts_as_pass=False，90/120 为 True；真 run runs/model-player/t140-w30-demo/asteroids/scripted/player.json verdict=PASS 而 counts_as_pass=False、qualified_verdict=\"PASS @w30 r1 [reference only: window 30 < reporting 90]\"；历史 run t139-scripted-w30 经 nominal_frames_of_run -> (30,'session.json->measurement_window.frames') 也重判为 counts_as_pass=False（gate 侧 pass=False）。"},
    {"id":"A2","pass":true,"evidence":"playtest_player.py:1234 verdict_class（PASS 与 PASS(baseline only) 是两个类别）/ :1276 divergence_between（只比 injected/accepted/ack_missing/changed/changed_strict/step_verdict）/ :1308 stability_summary（<2 轮 INSUFFICIENT_ROUNDS；类别不同 UNSTABLE 且 :1389 counts_as_pass=False）。我自己从 6 个前缀的 player.json+steps.jsonl 重算（runs/accept-141/p09_stab.py, indep_stability.txt）：jev 臂 asteroids=UNSTABLE，分歧点 step 6 changed_strict r1=True r2=False（pixel_diff 965 vs 968，差 3 像素）+ step 9/10/11/12 step_present；跨批 breakout/scripted @w90 三次运行 UNSTABLE，分歧点 step 2/3/4 的 injected/accepted/changed/changed_strict/step_verdict（ok_ack_and_changed vs no_ack_no_change = ack 丢失）。脚本臂与 playjev 臂 UNSTABLE=(none)。批次产物 t140_stability_model.json.unstable_games=['asteroids']、t140_unstable_breakout.json.state=UNSTABLE 一致。"},
    {"id":"A3","pass":true,"evidence":"来源=游戏自己的状态导出：playability_gate.probe_state_source -> steps.jsonl->state_delta -> playtest_player.py:387-435 step_refusal_record（:400-404 只认 from!=to；:407-416 优先匹配 games.<game>.refusal_evidence.game_side_fields）。声明共 6 款（bomberman/match3/minesweeper/pacman/sokoban/towerdefense），含任务书点名的 5 个字段 + 本批新增 RejectedPlaces。反例（p15 A8-A12 全 OK）：全拒绝零推进 => refusal_only_run=True / verdict=FAIL / counts_as_pass=False / real_progress_step_count=0；拒绝+>=4 步真实推进不被地板打成 INCONCLUSIVE；拒绝+<4 步 => INCONCLUSIVE 永不 PASS；无拒绝 run 逐位不变（refused_steps=[] rate=1.0 PASS）；from==to 的字段不算证据。边界 min_real_progress_steps=4 见声明与 playtest_player.py:349。注：实际 6 款 vs 任务书口径 5 款（minor F-4）。"},
    {"id":"A4","pass":true,"evidence":"playtest_player.py:3253-3293 缺失即记 ack_missing（pre_ack_used_as_evidence=False）、:3300-3311 无条件 injected=False/accepted=False/evidence_used='ack_missing'/step_verdict=INCONCLUSIVE_ack_missing、:3354-3357 ack_pre_read.used_as_evidence=False、:1078-1096 player.json->ack_missing(count/pre_ack_fallback=False)。我的反例 p15 A6a-A6i（9 条 OK）：8 个缺失 ack 步 => counts_as_pass=False、非 FAIL、accepted_steps=0、rate=None，而 pre_ack_recorded_only.is_action_pressed=True（若不回退就会误判接受）。shipped test tools/tests/test_playability_model_player.py:4512-4571 含同一反例；我自跑该文件 rc=0，task140_cases 41 assertions / 合计 108。全批 866 个 accepted 步中 0 个使用注入前读数（p26_adversarial.py）。"},
    {"id":"B5","pass":true,"evidence":"我自跑 9 次、逐字相同的命令、唯一高位端口（9411-9452 串行），输出 runs/accept-141/run_*.out.txt：pong scripted w90 r1 INCONCLUSIVE@w90 r1 / r2 INCONCLUSIVE@w90 r2 / r3 PASS@w90 r3 / r4 PASS(baseline only)@w90 r4；snake scripted PASS@w90 r1；tetris scripted PASS@w90 r1；pong jev PASS(baseline only)@w90 r1；tetris jev PASS@w90 r1；snake jev INCONCLUSIVE@w90 r1（步 10 终止）。与报告对照：snake/tetris（脚本+模型）与 pong 模型臂逐项一致，snake 脚本 8 步逐字段逐值一致（runs/accept-141/indep_cmp_pong.txt）。pong 脚本臂与报告不一致（见 defects F-2）。"},
    {"id":"B6","pass":true,"evidence":"runs/accept-141/p08_distrib.py 只读每个 run 的 player.json（不读批次 t140_results_*.json）：t140-scripted-w90-r1 17/1/0/2、r2 17/1/0/2；t140-jev-v3-w90-r1 2/1/2/15、r2 1/2/2/15；t140-playjev-v3-w90-r1/r2 4/0/1/5（各 10 款）；counts_as_pass_true = 17/17/2/1/4/4。报告 §C.4 声称逐格一致；t139 的 15/1/0/4、15/0/1/4、1/1/2/16、3/0/1/6 也一致。批次 t140_stability_*.json.distributions 与报告三张表逐格相同（runs/accept-141/p30 输出）。"},
    {"id":"B7","pass":true,"evidence":"(a) asteroids：我自己的探针 runs/accept-141/p18_respawn.py + respawn-probe/probe.json，只把船放到空地并给 320px/s 让它自己飞进游戏自己放在 (650,130) 的岩石（位置由 RockList() 读出）：RespawnDelay=0（=修前）撞击后 ShipAlive 24/24 全 F、Respawns=0、最长连续 pixel_diff=0 = 23；出厂默认(1.0/1.5) 第 6 样本 ShipAlive 回 T、Respawns 0->1、RespawnTimer 0.808->0.508->0.225->0、pixel_diff 出现 484/484/0/484。跨批逐字节对照：t139-jev-v3-w90/asteroids/jev frames 016_05_after.png 与 037_12_after.png 同为 c09b58739e8d3094b081f997554e29ca6e602b55d2acdc757664aaa92ddefe4d（10111B,800x600），read_image 实看两帧都无飞船。(b) frogger：修前 t140-prefix4-w90-r1 1 个注入步 Lives 3->0、LastEvent='lives lost reason=hit by car at=6,13 lives=0 game over'、GameOver F->T；修后 t140-postfix4-w90-r2 8 步每步恰好一格（FrogRow 14->13->12、FrogCol 6->7…）px=1152、Lives 全程 3、verdict=PASS(counts_as_pass=True)。(c) bomberman 修前 007_02_after 无炸弹、步5/7/9 px=0 且 state_delta 为空；修后 BombsVisible 0->1、BombMinContrast 0->0.79999995、Bomb_0.pos [0,0,26,26]->[178,126,26,26]、步5/7/9 refused=True 且 RejectedPlaces 0->1->2->3，verdict=PASS。(d) flappy 修前对照窗 pixel_diff=0/movement=0（real=1 rate=0.0833），修后对照窗 pixel_diff 45590..74290/movement 2464..2494、动作窗 103172..128294（real=8 rate=0.8889，PASS(baseline only)）。dotnet build 我自跑 4/4 exit=0 errors=0 warnings=0（runs/accept-141/build/*.txt）。P1-P7 我自跑 asteroids（9451）全 PASS、per_criterion_fail 全 0、exit 0；--only-p7（9452）P7=PASS；批次 t140-gate-4/playability.json 4/4 款 P1..P7 全 PASS、verdict=playable。"},
    {"id":"C8","pass":true,"evidence":"我自己 read_image 实看 9 张全尺寸 800x600 原图（runs/accept-141/p25_framehash.py 自算 sha256/尺寸，§C.7 引用的 11 个 sha256 前缀全部命中、尺寸全部 (800,600)）：frogger 修前/修后 004_01_after、bomberman 修前/修后 007_02_after、flappy 修前/修后 002_01_before、asteroids 016_05_after、respawn-probe 032_default_respawn_1s_05、003_variant_respawn_delay_0_01。逐条与报告 §C.7 对照：HUD 文本、物体位置、与状态锚点的一致性全部成立；两处描述精度问题（青蛙 y≈536 我读到 530-538；\"三组管子\"我数到 4 列）见 defects F-5。"},
    {"id":"C9","pass":true,"evidence":"§C.2 逐条复核报告 §G 的 9 条：w90 非零方差(F-1 类)/flappy 仍 PASS(baseline only)/asteroids 自然撞击未在跑测触发/计分副作用/frogger 无\"恰好掉1命\"帧/Detonations 恒 0/历史标称窗回退/UNSTABLE 轮次显示 None/工具修订与 run 对应关系 —— 9 条全部为真、且报告都以\"未达标/限制\"写法呈现，没有一条被说成已达成。"},
    {"id":"C10","pass":true,"evidence":"我独立写的扫描器 runs/accept-141/p05_ledger_scan.py 重扫 runs/model-player/_scripts/t136_commands.jsonl（710 行，source 直方图 {manual-backfill:39,(none):184,t139-wrapper-call:278,t140-wrapper-call:209}）：切点 source=='t140-wrapper-call' 首条 index 501 / ts 2026-09-28T07:02:21（与批次 cut.first_task140_index=501 一致）；8 组 token 独立扫描命中 0 条 => \"0 命中\"成立；按末次扫描器条目重数 = 194（现切点后 209，多出的 15 条是扫描后的收尾命令，逐条列在 runs/accept-141/indep_tail_entries.txt）=> \"194 条\"成立。\"2 处台账外命令\"：台账 manual-backfill=39 与声明①量级一致，②的代码结果可核（FlappyBirdGame.cs:143 BirdReady，build 0 警告）。但报告 §I.3/§F 又写 186（见 defects F-1）。"},
    {"id":"D11","pass":true,"evidence":"runs/accept-141/p26_adversarial.py：6 个前缀 1053 步重算 frame_alignment => matched 564 (53.6%)、residual 直方图 {0:564,+1:379,+2:105,+3:4,+23:1}、within_5=1052/1053；唯一 |Δ|>5 的步是 t140-scripted-w90-r2/sokoban step5（control 91/action 114）且判为\"未变化\"（反向，不虚高）。wait 被 accepted 的步数=0（非接受 187 步）。866 个 accepted 步里 0 个使用注入前 ack 读数。SENSITIVE 与 UNSTABLE 在三张表与批次稳定性产物里并列且与报告一致（model sensitive=['asteroids','flappy','pong','spaceinvaders'] unstable=['asteroids']；scripted sensitive=['bomberman','flappy','frogger','platformer','pong'] unstable=[]；playjev sensitive=['asteroids'] unstable=[]）。4 个 w30 前缀里 counts_as_pass=True 的 run 数=0。两把尺子常量与 --window-frames/min_frames 语义未动，reporting_frames/UNSTABLE 只拿不补（11 档反例 + UNSTABLE 反例）。"}
  ],
  "defects": [
    {"what":"报告命令条数自相矛盾：同一份报告同时写 194（§I 顶部/§E.Y10）与 186（§I.3 两处、§F 表）；权威台账切点重算=194","severity":"major","evidence":"recovery/reports/TASK-140-REPORT.md L626/L634（194）、L653/L658 与 L536（186）；我 runs/accept-141/indep_ledger_scan.json（cut=501、独立扫描 0 命中、末次扫描前 194 条）与 indep_tail_entries.txt"},
    {"what":"报告档位下的\"两轮一致\"不是可复现性保证：同一字节相同的 pong scripted @w90 命令，我自己 4 轮读到 INCONCLUSIVE/PASS/PASS(baseline only) 三个类别；机制是脚本策略在 Ball.Velocity 采样为 0 时永远选 pong_serve，令\"8 步动作>1 种\"的提前停止不成立、注入步 6<8","severity":"major","evidence":"runs/accept-141/run_scripted-pong.out.txt / run_scripted-pong2.out.txt / run_pong-s3.out.txt / run_pong-s4.out.txt；indep_cmp_pong.txt；playtest_player.py:2286-2308 与 :3804-3813；报告 §C.2 把 pong 列为两轮 PASS/STABLE"},
    {"what":"task140_cases 的分段断言条数写错：报告 §A.1/§A.2 与 DECISIONS D205/D206 写 unstable 段 22 条、reporting 段 14 条；逐 check( 计数为 41 总数下的 5/9/5/16/6，unstable 段实为 16 条","severity":"minor","evidence":"tools/tests/test_playability_model_player.py:706-837；runs/accept-141/p04_count_asserts.py 输出；TASK-140-REPORT.md L68-71/L92；DECISIONS.md:7969"},
    {"what":"\"refusal_evidence 5 款已声明\"与实际不符：实际 6 款（多 towerdefense[InputRejectedPlaces]，bomberman 新增 RejectedPlaces）","severity":"minor","evidence":"runs/accept-141/probe_refusal.py 输出（6 款、6 个字段）；tools/playability_controls.json 各 games.*.refusal_evidence.game_side_fields"},
    {"what":"§C.7 两处逐帧描述与全尺寸原图不完全吻合：青蛙位置写作 y≈536（实测 530-538，24px 格内方向正确）；flappy 修后写作\"三组管子\"（在屏为 4 列）","severity":"minor","evidence":"§C.1 第 2/6 行；帧 sha256 fa3cc225…/9082895f… 与我的 read_image 记录"},
    {"what":"报告正文未给模板 §1.2/§1.2d 要求的\"两窗相等步数与差值分布\"聚合读数（只给机制与单测引用）","severity":"minor","evidence":"TASK-140-REPORT.md 中 grep 'matched'/'residual'/'frame_alignment' = 0 命中；我重算 1053 步 matched=564(53.6%)、max|residual|=23、分布 {0:564,+1:379,+2:105,+3:4,+23:1}（runs/accept-141/indep_adversarial.txt）"},
    {"what":"--steps 12 会被\"8 步全变化且动作>1 种\"的耐心提前停止截断，导致\"步数\"在同命令不同 run 间不可比（报告用 \"8 步 run\" 描述修后证据时未点出该条件）","severity":"minor","evidence":"playtest_player.py:3804-3813；batch t140_t140-scripted-w90-r1_pong.out.txt 的 'early stop' 行 vs 我的 run_scripted-pong.out.txt（走满 12 步）"}
  ],
  "risks": [
    "未记录标称窗（nominal_frames is None）时不判 BELOW_REPORTING_WINDOW，此时 counts_as_pass 可为 True（playtest_player.py:1199-1202、playability_controls.json:408 的声明）。CLI 路径必记录 --window-frames，真 run 走不到；但手工 summarise() 或缺失 verdict_context+session.json 的历史 run 可以在\"档位不明\"下拿到 counts_as_pass=True。建议把 at_reporting_window=None 也视为不可作 PASS 依据。",
    "UNSTABLE 只在\"喂进去的同档 run\"之间计算；批次把跨批不一致单列成 CROSS-BATCH 而未进工具自动判定（报告 §G.1 自认）。我的 pong 4 轮数据说明同批内也可能不稳，而本批每款只跑 2 轮；\"两轮一致\"不足以支撑\"这一档可复现\"。",
    "frame_alignment 存在一步 +23 帧的大偏差（t140-scripted-w90-r2/sokoban step5：control 91 / action 114，polls=11 的一次慢往返）。该步判\"未变化\"（方向对游戏不利），但偏差方向不保证永远如此；建议对 |Δ|>N 的步单独点名。",
    "我自己的 pong 脚本 run 出现\"策略永远选 serve\"（Ball.Velocity 采样恒 0）导致假 INCONCLUSIVE。这是测量侧（脚本策略 + 采样时序）问题，不是游戏缺陷（同期 px=3788/461/337/491/4630/512 说明画面确在动），但它提醒脚本臂的结论也依赖时序。",
    "报告 §I.3 ①的\"约 30 条预台账只读侦察命令\"无法逐条复原（台账只留 manual-backfill=39 这一计数）；本报告只确认了该计数与我独立扫描 0 命中。"
  ],
  "unverifiable": [
    "报告 §I.3 ①约 30 条预台账侦察命令的逐条原文（台账仅有 manual-backfill=39 计数）。",
    "t140_hash_table.md 的 115 run / 921 文件全量 sha256 未逐文件重算（我只抽了 11 张证据帧 + 关键 JSON，全部命中）。",
    "TASK-140 之前的全部历史 run 的标称窗回退行为（只验了 t139-scripted-w30/asteroids/scripted 一条）。"
  ] }
```

---

*报告落点：`F:\moonbit-hof-rs\godot-mcp\recovery\reports\ACCEPTANCE-TASK-141.md`*
*验收方证据目录：`F:\moonbit-hof-rs\godot-mcp\runs\accept-141\`*
