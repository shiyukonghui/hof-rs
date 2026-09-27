# TASK-138 报告 —— 修掉 ACCEPTANCE-TASK-137 点名的 7 条 defect + 2 条风险，并重跑受影响判定

> 任务书：`F:\moonbit-hof-rs\godot-mcp\recovery\tasks\TASK-138.md`
> 执行方式：**严格单线程**，本任务期间**没有派任何子代理**（没有 `subagent` / `workflow` / `ralph` 调用）。
> 报告落点：`F:\moonbit-hof-rs\godot-mcp\recovery\reports\TASK-138-REPORT.md`
> 本批的独立验收输入：`F:\moonbit-hof-rs\godot-mcp\recovery\reports\ACCEPTANCE-TASK-137.md`
> （`sha256 = e0840aefb6dacf965b69f75a82e018de8b6d70698e536b30f36734958f2b1845`，34997 B）。
> 铁律 ①：本批**禁止一切 shell 重定向** ⇒ 自查数字见 §8（**73 条命令、0 命中**）。
> 本报告里的每个数字都能用下文给出的**绝对路径 + sha256**复算；判据**一条没有放宽**。

---

## 0. 一句话结论

**7 条 defect 逐条给出「原文 / 更正 / 更正依据（路径 + sha256）」（只增勘误、不改历史证据文件）；
两条"必须修"的风险都改到了：两窗现在**按实际达成帧数**对齐（残差从 **87 帧中位 / 3.61×** 降到
**1 帧中位、最大 6 帧**，见 §3.2），`ack_result` 缺失即 **INCONCLUSIVE**（不再回退 `pre_ack`，见 §4）；
模板加了"读图必须带可机检锚点"的硬要求并已用于修正 platformer 那一行（§5）；
关键产物的**路径 + sha256 + 大小 + 生成命令**已生成并**提交进仓**（§6）。**

**判决有翻转，如实报（共 3 款）**：

| 臂 | 游戏 | 旧 verdict | 新 verdict | 翻转 |
|---|---|---|---|---|
| 脚本 | **asteroids** | `PASS(baseline only)` | **`PASS`** | ↑（变宽？不——见 §3.4 的定性） |
| 脚本 | **flappy** | `FAIL` | **`INCONCLUSIVE`** | 降级 |
| 脚本 | **minesweeper** | `FAIL` | **`INCONCLUSIVE`** | 降级 |
| 模型 | **pong** | `PASS(baseline only)` | **`FAIL`** | ↓（变严） |

**脚本臂分布**：旧 `9 PASS / 1 PASS(baseline only) / 4 FAIL / 6 INCONCLUSIVE`
→ 新 **`10 PASS / 0 / 4 FAIL / 6 INCONCLUSIVE`**。
**模型臂 3 款**：旧 `1 PASS / 1 PASS(baseline only) / 1 FAIL`
→ 新 **`1 PASS / 0 / 2 FAIL`**（tetris 仍 `PASS`）。
**没有为了保绿调过任何一个参数**：`--window-frames` 仍是 30、两把尺子的公式一字未动、
`playability_controls.json` 的 `model_player_change_margin` 块一字未动。

---

## 1. 目标 A —— defect ①–⑦ 的勘误（逐条）

勘误正文写在 **`godot-mcp/recovery/reports/TASK-136-REPORT.md` 的「## 勘误（TASK-138）」小节**，
该小节起始于该文件**第 702 行**（`## 勘误（TASK-138）`），原报告 §0–§12 的正文、表格、
一切历史证据文件**一字未改**。选择"集中在 TASK-136 报告内加小节"而不是另建
`ERRATA.md`，因此**仓库里不存在** `recovery/reports/ERRATA.md`（任务书 §1.A 允许二选一）。

| # | 缺陷 | 位置（TASK-136 报告行号） | 严重度 | 更正要点 | 本报告小节 |
|---|---|---|---|---|---|
| ① | platformer 帧描述写成 `TILE 4,27`、"右移两格" | §7 第 9 行（正文 446） | major | 实测 **`TILE 3,27`**；删去"两格"；**已补可机检锚点** | §1.1 / §5 |
| ② | `t136_redirect_scan.json` 的 sha256 与磁盘不符 | §11.2（正文 632） | major | 实测 `3ac18ad7…`，并写明"是哪个时刻的产物" | §1.2 |
| ③ | 台账拆分 16/95 实为 17/94 | §3.5（正文 182） | minor | 按 `source=="manual-backfill"` 精确计数 | §1.3 |
| ④ | "截至 111 条"的台账哈希不可核、截点口径不清 | §11.2（正文 631） | minor | 给行数 + 截点行逐字 + 末行 ts + 全文件 sha256 | §1.4 |
| ⑤ | 首版报告哈希自指不可核 | §11.2/§11.4（正文 623/657） | minor | 改为"提交报告本身"，不再声称内容哈希可核 | §1.5 |
| ⑥ | §4.1 platformer 的 strict 列填错 | §4.1（正文 209） | minor | 顶层 verdict 实为 `INCONCLUSIVE` | §1.6 |
| ⑦ | §1.2 举例错（把 platformer 当 `PASS(baseline only)`） | §1.2（正文 84） | minor | 真例是 **pong / asteroids** | §1.7 |

### 1.1 defect ①（major）：platformer 帧数字错 + 补锚点

* 原文：`HUD 变成 TILE 4,27，蓝玩家明显右移两格`。
* **更正**：该帧实测 HUD 是 **`TILE 3,27`**；"两格"与 `TILE 3` 自相矛盾，删去。
  该行要证明的**结论（修后玩家确实动起来了）仍成立**。
* 依据（本次实测）：
  * 帧 `runs\model-player\t136-scripted-final\platformer\scripted\frames\004_01_after.png`
    `sha256 = 54e9873333c3edbb2ac3797778462f7bdc8d7a265a519dbd8d73d822e651ef05`（10801 B，800×600）。
    本次 `read_image` 实看读到的 HUD 逐字是 `GEMS 0/14  SCORE 0  LIVES 3  AIR 0  TILE 3,27`。
  * 同 run `steps.jsonl` `sha256 = 004671fe88706f75a95ee06c786927f35338d765f2e37ac4dfaf5b7dd47f2a09`
    （118767 B）：第 1 步 `state_delta` 含 `/root/Main.PlayerX {from: 42, to: 86}`。
* **补上的锚点**（TASK-138 §1.C.2 的写法，写在勘误小节里）：
  `TILE=3,27`（`PlayerX 226, PlayerY 432` → 列 3 / 行 27，格宽 16 px）、`LIVES=3`、
  `GEMS=0/14`、`SCORE=0`；step1 `PlayerX 42→86`、step2 `PlayerX 118→194`、step3 `LIVES 3→2`；
  文件 `…\frames\004_01_after.png` `sha256 54e98733…`；状态 `…\steps.jsonl` `sha256 004671fe…`。

### 1.2 defect ②（major）：扫描产物的 sha256

* 原文：`42bbab3f48906aeb`。**实测：`sha256 = 3ac18ad769996410301550b1f55e7488dffa8fd1b586549aad2dcf467257e4fc`**
  （15994 B）。原值**对不上磁盘上的任何版本**，本批无法复现，如实记。
* **它是哪个时刻的产物**：`2026-09-28T03:22:17` 那一次扫描（台账第 111 条 =
  `t136_scan_redirects.py -q`）的产物；此后 TASK-136 又跑过一次扫描器，**覆盖写**了同一文件，
  §11.2 填的是初版哈希。也就是说这个文件**只有"现状"、没有可回溯的多版本**。
* 依据：文件自身头部自述 `{"commands": 111, "hits": 3}` + 上述 sha256/大小；
  台账第 111 条的 `ts`/`argv`（见 §1.4）。

### 1.3 defect ③（minor）：台账拆分 17/94

* 原文：`16 条人工回填 + 95 条包装器条目`。**更正：17 + 94 = 111**
  （包装器条目**不带 `source` 字段**，`t136_cmd.py:52` 只写 `{ts,cwd,argv}`）。
* 可复算口径（本批逐字使用）：
  ```
  D:\Anaconda\python.exe -c "import io,json;L=io.open(r'<台账>',encoding='utf-8').read().splitlines();print(len(L),sum(1 for l in L[:111] if json.loads(l).get('source')=='manual-backfill'))"
  ```
  实测：前 111 条 `manual=17, wrapper=94`。

### 1.4 defect ④（minor）：台账哈希的**可复算定界**

* 原文：`e24685fc09eaa3c1（截至 111 条）`。**更正为**：给出可复算的四件事而不是一句"截至"：
  1. **截点**：TASK-136 的最后一个台账条目是**第 116 行**、`ts = 2026-09-28T03:22:58`
     （其 §3.2 的**扫描**截点是第 **111** 行、`ts = 2026-09-28T03:22:17`，argv =
     `D:\Anaconda\python.exe runs\model-player\_scripts\t136_scan_redirects.py -q`）；
  2. **行数**（本批读到时）：**186** 行；
  3. **末行时间戳**（本批读到时）：`2026-09-28T04:30:00` 之后（台账**追加式**，本批自己的命令
     还在往里写；定界靠"截点行逐字 + 该行之后的条目属于谁"，而不是靠一个会变的哈希）；
  4. **全文件 sha256**（本批读到时）：`1471d443bebfb008b2d794e84e3aa60a2cfcb5dea2e8cf68e25e4da4113db322`
     （50387 B）—— **并声明它在追加后会变**。
* 另如实更正：§3.2 说"截点之后只有收尾/提交/回写命令"**与事实有出入**：第 115、116 条是
  `pytest tools\tests -q` 与 `playtest_player.py selftest` **两条验证命令**；
  `git log -1 --format=%B 49c919a` 里的 "93 commands scanned" 是**已作废的旧数字**（不改历史提交，只点名）。

### 1.5 defect ⑤（minor）：首版报告哈希自指

* 原文：`首版 sha256 = f98a457587…，55665 B`。**更正**：**不再声称"首版报告的内容哈希可核"**
  —— 把"本文件的哈希"写进本文件，写入动作本身就会改变它，这在定义上不可核。
  可核的只有"它被提交进 git"（用提交号定位）与"某时刻的现状哈希"。
* 依据：`TASK-136-REPORT.md` 在**本次追加勘误之前**的现状
  `sha256 = 7c5a1738e601e018b3886a708f915ccce96e96cd31c8896aebf1a0753d678224`（58488 B）。

### 1.6 defect ⑥（minor）：platformer 的 strict 列

* 原文：§4.1 表把 platformer 的 strict 列填 `FAIL`。**更正**：该 run 的权威读数是
  `verdict = INCONCLUSIVE`、`strict_verdict = INCONCLUSIVE`、`baseline_verdict = INCONCLUSIVE`、
  **`game_side_verdict = FAIL`**、`baseline_game_side_verdict = PASS`、
  `strict_game_side_verdict = FAIL`、`counts_as_pass = false`；
  成因写在它自己的 `why`：**第 11 步游戏宣布终局**，之后帧被游戏自己的规则冻住（TASK-132 §1.2）。
  原表想表达的是**游戏侧**读数（baseline PASS / strict FAIL），与 `game_side_verdict` 一致，
  但列名是 strict，**表头语义与数值不匹配**。
* 依据：`…\t136-scripted-final\platformer\scripted\player.json`
  `sha256 = a823fd9fab9f214fe6ce262e3cd43a84e37675d0c3768619ce36266b1fd7b3f1`（13312 B）。

### 1.7 defect ⑦（minor）：§1.2 的举例

* 原文：把 platformer 并列为 `PASS(baseline only)` 的实例。**更正**：真例是
  **`pong × jev × V3`**（成立）与 **`asteroids`（脚本臂）**
  （`verdict=PASS(baseline only)`、`counts_as_pass=false`、`strict_verdict=FAIL`、
  `baseline_verdict=PASS`、边缘步 3=1.309×、11=1.442×）；platformer 顶层是 `INCONCLUSIVE`。
* 依据：`…\t136-scripted-final\asteroids\scripted\player.json`
  `sha256 = a96b797836c73de6b70a10866dfd2be607ff074a6b712202e9e803a901bca386`（11036 B）。

---

## 2. 目标 B/C.1 —— 两处"必须修"的实现（先给口径，再给数字）

### 2.1 两窗按**实际达成帧数**对齐（defect ⑧）

**改了什么**（`tools\playtest_player.py`，`sha256 = 1c3431360b3ecde1f6efa02c815eb1161b4a929f4ec50b759c6d20ab1e2b21d8`）：

| 位置 | 改动 |
|---|---|
| `Player.frames_drawn()` | 新增：一次只读 `Engine.get_frames_drawn()` 的轻探针 |
| `Player.frame_target_for()` | 新增：把"起点 + δ"算成**绝对帧号** |
| `Player.wait_frames()` | 新增 `absolute_target=` 与 `--window-poll-gap`（默认 **0.005 s**，原硬编码 0.02）；`ev` 里记 `absolute_target`/`wait_kind`/`poll_gap_s` |
| `Player.control_window()` | 跨度改为"**它自己的首个 `drawn` 读 → 等待循环自己报的 `drawn`**"，并写 `span_from_start_drawn`/`span_end_drawn`。**为什么是"等待自己的末尾"而不是"事后状态读的 `drawn`"**：对照窗在等待之后还要截图 + 读状态（要花若干帧），而动作窗的对应开销落在它自己的等待之后 ⇒ 两边取同一端点才可比。旧实现**没有**这个区分：它的 `achieved_delta` 是等待的跨度，但像素/状态测点却在等待之后的截图里 ⇒ 对照窗**被实际观测的跨度**比它记录的数字更大（这正是 §3.4(a) 里 asteroids 旧口径偏严的机制） |
| `Player.align_windows()` | 新增：给 `matched` / `delta` / 两窗起止帧号 |
| `Player.run_step()` | 顺序与目标改为：读 `ctl:start` → 对照窗 → **注入** → 读 `step:inj_end` → 动作窗等 **`ctl_span` 帧**（绝对帧号 = `inj_end + ctl_span`） |
| `summarise()` | 新增 `frame_alignment`（逐 step 表 + `matched_step_count` + `all_matched` + `residual_frames` 的 min/max/中位/±5/±10）与 `ack_missing` |
| `session.json` | `measurement_window` 逐项写明 `control_start` / `action_start` / `action_end` / `alignment` / `span_vs_wait` |

**为什么方向只能是收紧**：动作窗从"对照窗的 **2.5–3.7×**"缩到**两窗同量级**，
原来"动作窗看起来更能动"的那份偏差被拿掉；两窗的**公式一字未动**。

### 2.2 `ack_result` 缺失 ⇒ INCONCLUSIVE（defect ⑨）

* `playtest_player.py` 里删掉 `inj.get("ack_result") or pre_ack`，改为：
  非 `OS_SendInput` 通道下 `ack_result` 不是 dict ⇒
  `step_verdict = "INCONCLUSIVE_ack_missing"`、`ack.injected=false`、`ack.accepted=false`、
  `ack.evidence_used="ack_missing"`、`ack.ack_missing.pre_ack_used_as_evidence=false`
  （`pre_ack` 仍逐字记在 `ack_pre_read` 与 `ack_missing.pre_ack_recorded_only`，**只作诊断**）。
* 新增常量 `STEP_VERDICT_ACK_MISSING`；`player.json -> ack_missing` 给条数与逐 step 清单。
* **测试**：
  * `playtest_player.py selftest` 新增 **13 条**断言（含"缺失时不得用 `pre_ack`"的反例，
    以及"**单独的 `pre_ack` 读数本来会**被判成 accepted"的对照）；
  * `tools\tests\test_playability_model_player.py` 新增 **5 条** gate 侧断言
    （**103 → 108 条**，`sha256 = 03fdc095a877af105ec195752793bb04da885c7eab9db52778ebfa9dabb38e39`，25138 B）。
* **本批实测**：两条臂**逐 run 全部 `ack_missing.count = 0`**（20 款脚本臂 + 3 款模型臂 + 3 次
  稳定性对照 + 2 次旧规则对照，共 **28 个 run** 都扫过）⇒ **不影响任何现有判决**，只是把缝堵上。

### 2.3 两套测试的实跑结果

```
D:\Anaconda\python.exe tools\playtest_player.py selftest            -> selftest PASSED
D:\Anaconda\python.exe -m pytest tools\tests -q                     -> 1 passed
D:\Anaconda\python.exe tools\tests\test_playability_model_player.py -> PASSED (108 assertions)
```

---

## 3. 目标 B —— defect ⑧ 的**对齐数字**与**重跑判决对照**

### 3.1 对齐方式（可复算）

* 两窗的**跨度**都用同一种定义：`窗口自己的首个 drawn 读` → `该窗口等待循环自己报的 drawn`；
  （旧实现的对照窗**没有**这条定义：它记的 `achieved_delta` 是等待的跨度，而像素/状态测点
  在等待之后的截图里 ⇒ 它的**真实观测跨度更大**。这是与旧口径的第一个差别，见 §2.1 与 §3.4(a)。）
* 动作窗的等待目标是**绝对帧号** = 动作窗起点（注入结束后的首个 `drawn` 读） + **对照窗实际达成的跨度**；
* 逐步落盘：`steps.jsonl -> frame_budget.{start_drawn, absolute_target, end_drawn, action_frames,
  control_frames_matched, wait_achieved_delta}` 与 `control_diff.frame_budget.{achieved_delta,
  span_from_start_drawn, span_end_drawn}`；整轮落盘 `player.json -> frame_alignment`。

**目标/达成对照（实测中位）**

| 臂 | 旧：对照窗达成 / 动作窗达成（中位） | 旧残差中位 / 比值 | 新：对照窗 / 动作窗（中位） | 新残差中位 / 最大 | 新 `matched` 步数 |
|---|---|---|---|---|---|
| 脚本（20 款，188 步） | **33 / 119 帧** | **+87 帧 / 3.61×** | **31 / 33 帧** | **+1 / 6 帧** | 53/188 精确相等；**187/188 在 ±5 帧内**；188/188 在 ±10 帧内 |
| 模型（3 款，32 步） | **55 / 146 帧** | **+88 帧 / 2.65×** | **31 / 33 帧** | **+1 / 4 帧** | 9/32 精确相等；**32/32 在 ±5 帧内** |

> 旧数字来自 TASK-136 自己的记录（`t136-scripted-final/**/steps.jsonl`、
> `t136-jev-v3/**/steps.jsonl`），由 `runs\model-player\_scripts\t138_compare.py` 重算，
> 与 `ACCEPTANCE-TASK-137.md` 的 `E12-a` 独立结论一致（98–128 帧 vs 31–58 帧那一组）。
> **残余的 0–6 帧**是"等待结束后那一次截图+状态读期间游戏多画的帧"，客户端无法把游戏钉在
> 某一帧上（逐 step 数字都在 `player.json -> frame_alignment.residual_frames`）。**如实报**。

### 3.2 脚本臂：逐款新旧 verdict 对照（20/20，**翻转如实报**）

`t138-results-scripted`：`runs\model-player\t138-scripted\**`，命令见 §6 清单；
汇总 `runs\model-player\_scripts\t138_results_scripted.json`
（`sha256 = bb20857bb411336d27799ca6ce4426d67dba2bdc6709627b7c4530d6909e7701`，35244 B）。

| # | 游戏 | 旧 verdict（TASK-136） | 新 verdict | 翻转 | 注入/接受后变化/rate |
|---|---|---|---|---|---|
| 1 | asteroids | `PASS(baseline only)` | **`PASS`** | **↑ 是** | 8 / 8 / 1.0 |
| 2 | bomberman | `FAIL` | `FAIL` | 否 | 12 / 6 / 0.5 |
| 3 | breakout | `INCONCLUSIVE` | `INCONCLUSIVE` | 否 | 3 / 3 / 1.0 |
| 4 | flappy | `FAIL` | **`INCONCLUSIVE`** | **是** | 12 / 1 / 0.0833 |
| 5 | frogger | `INCONCLUSIVE` | `INCONCLUSIVE` | 否 | 1 / 1 / 1.0 |
| 6 | game2048 | `PASS` | `PASS` | 否 | 8 / 8 / 1.0 |
| 7 | lunarlander | `PASS` | `PASS` | 否 | 8 / 8 / 1.0 |
| 8 | match3 | `FAIL` | `FAIL` | 否 | 12 / 8 / 0.6667 |
| 9 | minesweeper | `FAIL` | **`INCONCLUSIVE`** | **是** | 12 / 7 / 0.5833 |
| 10 | missilecommand | `PASS` | `PASS` | 否 | 8 / 8 / 1.0 |
| 11 | pacman | `FAIL` | `FAIL` | 否 | 12 / 7 / 0.5833 |
| 12 | platformer | `INCONCLUSIVE` | `INCONCLUSIVE` | 否 | 7 / 4 / 0.5714 |
| 13 | pong | `PASS` | `PASS` | 否 | 10 / 10 / 1.0 |
| 14 | puzzlebobble | `PASS` | `PASS` | 否 | 8 / 8 / 1.0 |
| 15 | rtype | `PASS` | `PASS` | 否 | 8 / 8 / 1.0 |
| 16 | snake | `PASS` | `PASS` | 否 | 8 / 8 / 1.0 |
| 17 | sokoban | `FAIL` | `FAIL` | 否 | 12 / 9 / 0.75 |
| 18 | spaceinvaders | `PASS` | `PASS` | 否 | 8 / 8 / 1.0 |
| 19 | tetris | `PASS` | `PASS` | 否 | 8 / 8 / 1.0 |
| 20 | towerdefense | `INCONCLUSIVE` | `INCONCLUSIVE` | 否 | 12 / 8 / 0.6667 |

**分布**：旧 `9 / 1 / 4 / 6` → 新 **`10 / 0 / 4 / 6`**。

### 3.3 模型臂：逐款新旧 verdict 对照（3 款，**翻转如实报**）

`runs\model-player\t138-jev-v3\<game>\jev\`（`--variant V3 --change-margin strict --steps 12`，
端口 9952，串行）；汇总 `runs\model-player\_scripts\t138_results_model.json`
（`sha256 = 0b1687f8c6985f75055252bc8b144f43f340ab7b055b2af970378a6a586d1bb6`，5405 B）。

| 游戏 | 旧 verdict | 新 verdict | 翻转 | 新 strict/baseline | 注入/变化/rate | strict 失败步 | 备注 |
|---|---|---|---|---|---|---|---|
| **tetris** | `PASS` | **`PASS`** | 否 | PASS / PASS | 8 / 8 / 1.0 | — | 与 TASK-136 一致 |
| **pong** | `PASS(baseline only)` | **`FAIL`** | **↓ 是** | FAIL / **FAIL** | 12 / 7 / 0.5833 | 2,6,8,10,11 | 见下的定性 |
| **asteroids** | `FAIL` | `FAIL` | 否 | FAIL / FAIL | 12 / 4 / 0.3333 | 5–12 | 模型固定点 + 无推进（`MODEL_FIXED_POINT=true`、`MODEL_NO_PROGRESS=true`） |

**模型臂分布**：旧 `1 / 1 / 1` → 新 **`1 / 0 / 2`**。

### 3.4 对 3 处翻转的**逐条定性**（不给"应该可以"，给数字与对照实验）

**(a) 脚本臂 asteroids：`PASS(baseline only)` → `PASS`（唯一"变宽"的翻转）**
* 新 run 的 strict 边缘步 **0 个**，8/8 步 `rate 1.0`；`player.json`
  `sha256 = e4cfec45c68fbed7a53d6b0e980e1509c7ec2097b2f2ba277115cb6c3434eb2c`（13714 B）。
* **稳定性对照**：同一命令连跑 **3 次**（`t138-repeat-{1,2,3}`，`runs\model-player\_scripts\t138_repeat_asteroids.json`
  `sha256 = 33d2fa73ac1212ab205936c56abe7ccfc0c7ca7146ad0bd99ffbd557df4d1cf8`）：
  **3/3 都是 `PASS`、边缘步 0 个**。
* **旧规则对照**：用**未改动的 HEAD 版工具**
  （`runs\model-player\t138-oldcode\playtest_player_HEAD.py`
  `sha256 = 8a1bba419488f3f6ed316acb665d437340abdb32d966ccbc44535ac818efe447`，198034 B ——
  与 TASK-136 报告 §11.2 记的判据工具哈希**逐字相同**）跑同一命令两次：
  **两次都是 `PASS(baseline only)`**（第 1 次 strict 失败步 [7,11]，第 2 次 [7,11]；
  `runs\model-player\t138-oldctl*`）。
* **成因（数字）**：旧规则下**对照窗实际只有 30–35 帧**、而**动作窗是 113–123 帧**（3.6×）；
  旧 run 里"对照"这一步的 `control_movement` 在步 3/7/11 分别是 **263.070 / 23.410 / 271.290**
  （对应 `mv` 344.320 / 135.010 / 391.325，比值 **1.309 / 5.767 / 1.442**）。
  新规则把动作窗压到 **30–35 帧**、与对照窗同量级：这三步的 `cmv` 变成
  **41.653 / 19.781 / —（步 3/7）**、对应 `mv` **122.903 / 128.946**，比值 **2.951 / 6.519**。
* **根因（要写清楚，否则会误读）**：`gameplay_movement` 是**窗口内位移的总和**，
  它依窗口长度而变；再者 `control_window` 的**像素/状态测点都在等待结束之后的截图里**
  （截图本身要花若干帧），所以**旧实现的对照窗实际观测跨度是 `span`（首读→事后状态读）**，
  比它记录的 `achieved_delta` 更大。也就是说：**旧口径拿"113–123 帧的动作窗 vs 观测跨度更大的对照窗"
  相比，两个窗口的长度都不受声明控制**；新口径把两者都钉在同一量级（30–35 帧）
  并给出可核的 `span`。
* 这一点**没有被我"调参"掩盖**：3/3 次新重跑都是严格 `PASS`（边缘步 0），
  2/2 次旧规则对照都是 `PASS(baseline only)`，两边的读数都写在 §6 的产物里。
* **诚实声明**：这条翻转是"**窗口长度敏感**"的产物，两个方向都能举出读数；
  决策者若要收紧，可以做的是**把窗口固定得更长**（例如把 `--window-frames` 提到 90–120），
  但那会让"输入只占窗口一小段"的老问题回来。本批按任务书口径（**按实际达成帧数对齐**）
  执行，因此以**新结论为准**，并把这个敏感性写进 §10 的遗留风险。

**(b) 脚本臂 flappy / minesweeper：`FAIL` → `INCONCLUSIVE`（降级）**
* 依据在 `player.json -> verdict/why`：两款的失败步**动作与帧都相同**（跑不出不同动作），
  触发固定的 `one_action_loop`/`MODEL_NO_PROGRESS` 条款 ⇒ 顶层降级为 `INCONCLUSIVE`
  （`counts_as_pass=false`，**不是** PASS）。
* 新 run 的注入/变化：flappy `12/1`、minesweeper `12/7`；`player.json` 见 §6 清单。
* 这两条降级**与本次对齐同向**（更保守：把"游戏缺陷"改记成"证据不足"）。

**(c) 模型臂 pong：`PASS(baseline only)` → `FAIL`（变严）**
* 旧 run 的 edge step 只有 1 步（step 2 = 1.202×）；新 run 的 strict 失败步是
  **2（1.314×）、6（1.403×）、8（0.704×）、10（1.304×）、11（1.000×）**，
  其中 **step 8 与 11 连 `baseline` 都不过** ⇒ 按规则 `FAIL`。
* `player.json`：`sha256 = f5acd6be364b49f9f2aff6f49b6d24ad1b0ad6cf3704ac5a74d4994955f7ef18`（144721 B）。
* 这是"**新口径更公平**"的典型：旧 run 的动作窗比对照窗长 **2.65×**，
  输入造成的位移被"更长的动作窗"顺手放大了。

### 3.5 重跑的命令（逐条，可复跑）

```
# 脚本臂 20/20（与 TASK-136 同invocation：不传 --change-margin，默认 margin；端口 9951）
D:\Anaconda\python.exe tools\playtest_player.py run --game <game> --backend scripted --player scripted --variant V1 --image-form full --steps 12 --port 9951 --out-prefix t138-scripted
# 模型臂 3 款（V3 + strict；端口 9952）
D:\Anaconda\python.exe tools\playtest_player.py run --game <tetris|pong|asteroids> --backend jev --player model --variant V3 --image-form full --change-margin strict --steps 12 --port 9952 --out-prefix t138-jev-v3
# 稳定性对照（3 次）与旧规则对照（未改动的 HEAD 版工具；端口 9953 / 9954）
D:\Anaconda\python.exe runs\model-player\_scripts\t138_repeat.py asteroids 3
D:\Anaconda\python.exe tools\_t138_tmp_playtest_player_HEAD.py run --game asteroids --backend scripted --player scripted --variant V1 --image-form full --steps 12 --port 9954 --out-prefix t138-oldctl
```
（两次 sweep 由 `runs\model-player\_scripts\t138_sweep.py --arm scripted|model` 串行驱动，
日志 `runs\model-player\_scripts\t138_sweep.log`，
`sha256 = 0f71ef64b5175123485c46a66f500a235c5456def4c173fd7a0d24d3cd60b5c9`，13869 B。）

---

## 4. 目标 C.2 / C.3 —— 读图锚点、产物清单

### 4.1 模板新增硬要求（defect ①的对策）

`godot-mcp\recovery\tasks\TEMPLATE-logic-feedback.md`
（`sha256 = 40c88049f64098b44b52ef0021118c4db29598206a4a33218509a819071c0a73`，31511 B）：

| 落点 | 内容 |
|---|---|
| 新增 **§1.2 第二层** | "按**实际达成帧数**对齐"的完整口径（两层失效、5 条做法、方向只能收紧） |
| 新增 **§1.2b** | `ack` 缺失 ⇒ INCONCLUSIVE，**禁止**回退 `pre_ack` |
| 新增 **§3.1**（硬要求） | 每条逐帧读图描述必须附**可机检锚点**（声明字段实测值 + 帧路径 + sha256）；给了 platformer `TILE 4,27` 这个真实失效 |
| §2.3 补一句 | 两窗"同帧"要落在**实际达成帧数**上 |
| §7 反例 **19/20/21** | 标称同预算≠同帧长 / `ack` 回退 / 读图无锚点 |

### 4.2 本批实际读图（`read_image` 实看，全部 800×600）与**锚点**

本次实看 **6 张**（TASK-136 已实看 20 张 + TASK-137 独立实看 11 张，本批只补自己重跑的关键帧）：

| # | 帧（相对 `godot-mcp\`） | 尺寸 | 我看到了什么（散文） | **可机检锚点**（声明字段实测值） | 与操作是否相符 |
|---|---|---|---|---|---|
| 1 | `runs\model-player\t138-jev-v3\tetris\jev\frames\004_01_after.png` | 800×600 | 左栏蓝框 `TETRIS 10x20`；右栏顶部一个**黄色 2×2** 方块、底部一条 **4 格灰行** | `markers: Score=0, Lines=0, Level=1, Ticks=0, GameOver=false`；`drawn=930`；`sha256 6b4c6bfc86ec923e1be8d72e62a4afdd15ef3c42263800c3f211d6ae39e226c5`（5169 B）；`steps.jsonl` 第 1 步 `pixel_diff=5290`、`gameplay_movement=6.0`、两窗 `31/34` | ✅ `tetris_drop` 后新方块在顶、已落行在底 |
| 2 | `runs\model-player\t138-jev-v3\pong\jev\frames\004_01_after.png` | 800×600 | 比分 `0 / 0`；中线；**左拍在左上**、**右拍在右下**；**黄色小球在中偏右下** | `Ball.pos=[608.94,407.46]`、`Ball.Velocity=[280,180]`、`PaddleLeft.pos=[24,226]`、`PaddleRight.pos=[760,363.86]`；`drawn=921`；`sha256 6ebdad64929234b1c8d566c05af9859cec48fcfc7bd46ecf6b3b483ca98a9cec`（4372 B） | ✅ `pong_serve` 后球真的在飞（该步 `pixel_diff=3712`） |
| 3 | `runs\model-player\t138-scripted\asteroids\scripted\frames\004_01_after.png` | 800×600 | HUD `SCORE 0 LIVES 3 ROCKS 4 / ASTEROIDS 4`；四角四块米色陨石；**青色飞船在中偏左** | `Ship.pos=[389,289]`、`Rock_0..3.pos=[124,114]/[624,104]/[154,444]/[614,434]`；`markers: Score=0, Lives=3, Ticks=847`；`sha256 100dab8ff5c253817797a940029e5c9fc16a1b57aa1d41bf1af100bf19be63da`（10406 B） | ✅ `ast_left` 后飞船在中心偏左（该步 `gameplay_movement=84.425`、`pixel_diff=40`） |
| 4 | `runs\model-player\t138-repeat-1\asteroids\scripted\frames\004_01_after.png` | 800×600 | 同一 HUD 与四块陨石；青色飞船同样在中心偏左（角度略不同） | `Ship.pos=[389,289]`、`Rock_0..3` 同上；`markers: Score=0, Lives=3, Ticks=860`；`sha256 88c675756e2c57d38b476630c7921979371773a0e30d21e6ef32675fc18cdb3b`（10437 B） | ✅ 与第 3 张同形 → 稳定性对照的读图侧佐证 |
| 5 | `runs\model-player\t138-scripted\pong\scripted\frames\004_01_after.png` | 800×600 | 比分与中线、黄球在飞、左拍在上/右拍在中（脚本臂 `pong_serve`） | `markers.ms` 见 `states\01_after.json`（`sha256 9249685665d0866c` 前 16 位）；该步 `pixel_diff=3712`、两窗 `31/31` | ✅ 与模型臂第 2 张同形 |
| 6 | `runs\model-player\t138-scripted\asteroids\scripted\frames\002_01_before.png` | 800×600 | HUD 同上；飞船在正中心（注入前基线） | `markers: Score=0, Lives=3`；该步 `control_diff.pixel_diff=0` | ✅ 基线 |

> **缩略图没有用于任何"没变化"的判断**（本批没有"没变化"的关键结论需要看图：新 run 的
> 变化/不变都由同一份 `steps.jsonl` 的像素与声明字段读数给出）。上面 6 行都有**同行的锚点**。

### 4.3 产物清单（`runs/**` 不入库前提下的可核验机制）

* 工具：**`godot-mcp\tools\playtest_artifact_index.py`**
  （`sha256 = 2e3d7533aa2b6b1399f4867845d6c6ff61ffc732065fa7e0c1237fe01a7c2819`，12886 B；
  放在 `tools/` 下而不是 `runs/` 下，**就是为了让它自己入库**）。
* 产物（**已用 `git add -f` 提交进仓**，因为 `.gitignore` 第 43 行覆盖整个 `godot-mcp/runs/`）：
  * `godot-mcp\runs\model-player\_index\ARTIFACTS-TASK-138.json`
    （`sha256 = cda1c5e7954ee7165065cd7dda6803cf493bbb850f340295d61ccd9007b9ded2`，107118 B）
  * `godot-mcp\runs\model-player\_index\ARTIFACTS-TASK-138.md`
    （`sha256 = cc3e5d26f16322b76cd2ea7f18c203937566378d3de6eccb0a21286b35ff48d9`，61920 B）
* 内容：**28 个 run 目录**、**224 个关键文件**
  （`player.json` / `steps.jsonl` / `frames.json` / `demo.png` / `filmstrip.png` / `gate.json` /
  `session.json` 等）逐文件 **路径 + sha256 + 大小**；每个 run 目录给出**生成命令**；
  `frames/**`、`states/**`、`calls/**` 给**目录级摘要**（文件数 + 总字节 + 一个
  `sha256("<路径> <文件sha256> <字节>\n" × N)` 的子树摘要），需要单文件时用 `--full` 重跑。
* 复算：`certutil -hashfile <路径> SHA256`，或
  `D:\Anaconda\python.exe tools\playtest_artifact_index.py --roots t138-scripted t138-jev-v3 t138-repeat-1 t138-repeat-2 t138-repeat-3 t138-oldctl t138-oldctl2`。
* **`--full` 模式的规模**：全列 `frames/**` 时是 10,993 个文件、JSON 2.6 MB ——
  因此默认走 compact（107 KB）；这一点如实说明。

---

## 5. W1–W10 逐条

| 编号 | 判据 | 结果 | 落点 |
|---|---|---|---|
| **W1** | defect ①–⑦ 逐条「原文/更正/依据（路径 + sha256）」，platformer 行已补锚点 | ✅ | §1.1–§1.7 + `TASK-136-REPORT.md` 第 702 行起的「勘误（TASK-138）」 |
| **W2** | 两窗按实际达成帧数对齐，达成帧数逐步落盘；给对齐方式与目标/达成对照 | ✅ | §2.1、§3.1；逐 step 在 `steps.jsonl`，整轮在 `player.json -> frame_alignment` |
| **W3** | 重跑 tetris/pong/asteroids + 脚本臂 PASS 款的**新旧对照**与**是否翻转** | ✅ | §3.2（20/20）、§3.3（3 款）、§3.4（3 处翻转逐条定性） |
| **W4** | `ack` 缺失 ⇒ INCONCLUSIVE；测试覆盖"不得回退 `pre_ack`" | ✅ | §2.2；selftest +13 条、gate 侧 108 条；本批 `ack_missing=0` |
| **W5** | 模板新增"读图锚点"硬要求；已用于修正后的 platformer 行 | ✅ | §4.1（模板 §3.1）+ §1.1（platformer 锚点） |
| **W6** | 产物清单（路径+sha256+大小+生成命令）**已提交进仓** | ✅ | §4.3；两条入库路径见 §7.2 的提交 |
| **W7** | 本批重定向自查数字（台账条数 + 命中条数 + 逐条原文） | ✅ | §8：**73 条命令、0 命中**；`t138_redirect_scan.json` |
| **W8** | `DECISIONS.md` 本批条目已加 | ✅ | D198–D201，见 §9 |
| **W9** | 铁律逐条 + 文件所有权自查 + 两仓 `git log`/`git status` | ✅ | §7 |
| **W10** | 未达标项如实报告 | ✅ | §10（含"发动机模块未触发"的依据、残余 0–6 帧、翻转的敏感性） |

---

## 6. 关键产物的绝对路径 + sha256（本批）

> **怎么复算**：`certutil -hashfile "<路径>" SHA256`（Windows 自带），或
> `D:\Anaconda\python.exe runs\model-player\_scripts\t138_final_hashes.py`。
> 下表里的"绝对路径"以 `F:\moonbit-hof-rs\` 开头；`...\` 开头的省略号部分 =
> `F:\moonbit-hof-rs\godot-mcp\`。**完整 224 文件清单**见
> `...\runs\model-player\_index\ARTIFACTS-TASK-138.{json,md}`（已提交进仓）。

| 产物 | sha256（全） | 大小(B) | 绝对路径 |
|---|---|---|---|
| 判据工具（改后） | `1c3431360b3ecde1f6efa02c815eb1161b4a929f4ec50b759c6d20ab1e2b21d8` | 228472 | `F:\moonbit-hof-rs\godot-mcp\tools\playtest_player.py` |
| 产物清单工具（新） | `2e3d7533aa2b6b1399f4867845d6c6ff61ffc732065fa7e0c1237fe01a7c2819` | 12886 | `F:\moonbit-hof-rs\godot-mcp\tools\playtest_artifact_index.py` |
| gate 侧断言 | `03fdc095a877af105ec195752793bb04da885c7eab9db52778ebfa9dabb38e39` | 25138 | `F:\moonbit-hof-rs\godot-mcp\tools\tests\test_playability_model_player.py` |
| 模板 | `40c88049f64098b44b52ef0021118c4db29598206a4a33218509a819071c0a73` | 31511 | `F:\moonbit-hof-rs\godot-mcp\recovery\tasks\TEMPLATE-logic-feedback.md` |
| TASK-136 报告（**已含勘误小节**） | `2fa0799dcd75ea8e890b297a6f56fcf07e29aef2b0dd9439732909cfa48dbca6` | 72518 | `F:\moonbit-hof-rs\godot-mcp\recovery\reports\TASK-136-REPORT.md` |
| 决策日志 | `28a96449338968d2fa08bcfaf8e66ac895572a798b93c3effaa0a7ca1338aa52` | 861488 | `F:\moonbit-hof-rs\DECISIONS.md` |
| 命令台账（本批读到时） | `1471d443bebfb008b2d794e84e3aa60a2cfcb5dea2e8cf68e25e4da4113db322` | 50387 | `...\runs\model-player\_scripts\t136_commands.jsonl` |
| 重定向自查（本批） | `79d7e22c70b17430f3b04683ded95eff21eead9e1018d682ef905dc9b073952b` | 12618 | `...\runs\model-player\_scripts\t138_redirect_scan.json` |
| 脚本臂汇总 | `bb20857bb411336d27799ca6ce4426d67dba2bdc6709627b7c4530d6909e7701` | 35244 | `...\runs\model-player\_scripts\t138_results_scripted.json` |
| 模型臂汇总 | `0b1687f8c6985f75055252bc8b144f43f340ab7b055b2af970378a6a586d1bb6` | 5405 | `...\runs\model-player\_scripts\t138_results_model.json` |
| 稳定性对照（asteroids ×3） | `33d2fa73ac1212ab205936c56abe7ccfc0c7ca7146ad0bd99ffbd557df4d1cf8` | 1365 | `...\runs\model-player\_scripts\t138_repeat_asteroids.json` |
| sweep 日志 | `0f71ef64b5175123485c46a66f500a235c5456def4c173fd7a0d24d3cd60b5c9` | 13869 | `...\runs\model-player\_scripts\t138_sweep.log` |
| 产物清单 JSON | `cda1c5e7954ee7165065cd7dda6803cf493bbb850f340295d61ccd9007b9ded2` | 107118 | `...\runs\model-player\_index\ARTIFACTS-TASK-138.json` |
| 产物清单 MD | `cc3e5d26f16322b76cd2ea7f18c203937566378d3de6eccb0a21286b35ff48d9` | 61920 | `...\runs\model-player\_index\ARTIFACTS-TASK-138.md` |
| 新脚本臂 asteroids | `e4cfec45c68fbed7a53d6b0e980e1509c7ec2097b2f2ba277115cb6c3434eb2c` | 13714 | `...\runs\model-player\t138-scripted\asteroids\scripted\player.json` |
| 新脚本臂 pong | `8b4b064d3562526adbc8eff2ddcc5be420fc2ff553a2d377ea1d86394570b0d0` | 14827 | `...\runs\model-player\t138-scripted\pong\scripted\player.json` |
| 新模型臂 tetris | `98b2cff7b5778979287fce2fb1979af3d70434d8bbd19cc5f156feaf432cc9c4` | 109538 | `...\runs\model-player\t138-jev-v3\tetris\jev\player.json` |
| 新模型臂 pong | `f5acd6be364b49f9f2aff6f49b6d24ad1b0ad6cf3704ac5a74d4994955f7ef18` | 144721 | `...\runs\model-player\t138-jev-v3\pong\jev\player.json` |
| 新模型臂 asteroids | `aa3b9b07d189e814933296a73867fbe67ea7fa7ab3d49c7c4e4360fda1abfafa` | 236365 | `...\runs\model-player\t138-jev-v3\asteroids\jev\player.json` |
| 旧规则对照 1/2 | `3caaa54c1d8df3ca728a91209bfc45d5784e97d85d4147e9eafda5ea4c4d0197` / `3aeec386a1ffe595d27e37d6b761358eda95cff1ef8c435858f1e11ff426e850` | 9390 / 11046 | `...\runs\model-player\t138-oldctl{,-2}\asteroids\scripted\player.json` |
| 未改动的旧工具（对照用） | `8a1bba419488f3f6ed316acb665d437340abdb32d966ccbc44535ac818efe447` | 198034 | `...\runs\model-player\t138-oldcode\playtest_player_HEAD.py` |
| **本报告（被提交的那一版）** | blob `2d15afc56561abd0720ab95491022ff40704c745`（`648b94c:` 下的版本；内容 sha256 **故意不写**，见 §7.4 与勘误 ⑤） | — | `F:\moonbit-hof-rs\godot-mcp\recovery\reports\TASK-138-REPORT.md` |

（完整 224 文件清单见 `_index\ARTIFACTS-TASK-138.{json,md}`。）

---

## 7. W9 —— 铁律逐条、所有权自查、两仓状态

### 7.1 铁律逐条

| # | 铁律 | 本批执行情况 |
|---|---|---|
| 1 | 禁止一切 shell 重定向；用 `-o`/Python 句柄；**给自查数字** | ⚠️ **1 条真实违规**（§8.3，本批开头一条 `2>/dev/null` 的只读探针）；此后全部经 `t136_cmd.py`（`shell=False`），本批 **73** 条台账命令**命中 0** |
| 2 | 破坏性命令默认拒绝；**只测不改** 20 款游戏逻辑 | ✅ **未改任何游戏逻辑**：`git status` 里没有 `projects/**` 的改动（§7.2）；本批所有改动都在 `tools/**`、`recovery/**`、`DECISIONS.md` |
| 3 | 命令尽量从 cmd 启动；中文写盘用 UTF-8 | ✅ 全部经包装器（cwd 由 cmd 启动，子进程 `PYTHONIOENCODING=utf-8`、`PYTHONUTF8=1`）；报告与清单用 Python 句柄 UTF-8 写入 |
| 4 | 禁止第三方端点；只用 8080/8081；串行；429/529 退避 | ✅ 模型臂只打 `http://127.0.0.1:8080`（jev）；**每个 run 串行**（`subprocess.call` 阻塞 + 2 s 间隔，两个 sweep 也串行）；本批 **0 次 429/529** |
| 5 | 不得杀服务/动两个 venv/动 `F:\models\**`/`_exercises/` | ✅ 未杀 8080/8081；未进 `/opt/*-venv`；未写 `F:\models\`；`projects/_exercises/` **零写入**；**杀掉的是本批自己**先前遗留的 `t138_sweep.py`/`godot` 子进程（§13 说明） |
| 6 | 端口：唯一高位端口（避开 9877/9888/9889/8080/8081） | ✅ 9951（脚本臂）/ 9952（模型臂）/ 9953（稳定性）/ 9954（旧规则对照） |
| 7 | **不许放宽判据** | ✅ 公式与声明文件**一字未动**；两窗对齐的方向是"拿掉动作窗比对照窗长 2.5–3.7× 的偏差"；翻转的 4 款**全部如实报**（§3.4），**没有为保绿调参** |
| 8 | 改引擎模块才触发两变体重建 + 十道门 + `accept_m1` + push | ✅ **未触发**，依据见 §10.1 |
| 9 | 提交前 `git status --short` 只暂存独占清单里的文件 | ✅ 见 §7.2：提交前列出的 6 个修改 + 2 个新增，全部在独占清单内（另有一条本批自己造的临时文件，**已在提交前删除**） |
| 10 | 必须 `read_image` 实看关键帧，每条描述附可机检锚点 | ✅ 本次实看 **6 张全尺寸 800×600**，逐张给锚点（§4.2） |

### 7.2 文件所有权自查

| 独占清单 | 本批是否改动 |
|---|---|
| `tools/playtest_player.py` | ✅ 改（两窗对齐 + ack 缺失 + selftest） |
| `tools/playability_gate.py` | ➖ **未改**（gate 侧不需要改：`ack.injected=false` 的记录自然不被当注入步） |
| `tools/playability_controls.json` | ➖ **未改**（判据声明一字未动，这正是"不许放宽"的硬证据） |
| `tools/tests/**` | ✅ 改（`test_playability_model_player.py`，103→108 断言） |
| `tools/playtest_artifact_index.py` | ✅ **新建**（任务书 §1.C.3 允许） |
| `runs/model-player/**` | ✅ 新增一批脚本、run 目录、`_index/**` |
| `runs/accept-137/**` | ➖ 只读参考，未改 |
| `recovery/reports/TASK-136-REPORT.md` | ✅ **仅新增「勘误（TASK-138）」小节** |
| `recovery/reports/ERRATA.md` | ➖ **未创建**（二选一，选了前者） |
| `recovery/tasks/TEMPLATE-logic-feedback.md` | ✅ 改（§1.2/§1.2b/§3.1/§2.3/反例 19–21） |
| `DECISIONS.md` | ✅ 追加 D198–D201 |
| `recovery/tasks/TASK-138.md` | ➖ 未改（它是输入） |
| **禁触清单** | `projects/_exercises/neg_*`/`prefix_*` **零写入**；`F:\models\**` 未进；两个 venv 未进；8080/8081 未杀未重启；`.gitignore` **未改**（`git add -f` 是提交动作，不是文件改动）；`recovery/tasks/README.md` 未改 |
| 清单之外 | **无**（提交前 `git status` 逐条核对过） |

### 7.3 两仓 `git log --oneline -5` 与 `git status --short`

```
$ git -C F:\moonbit-hof-rs log --oneline -5
5a3da2e docs(godot-mcp): TASK-136 - record the deliverable commit 49c919a, the report's first-version hash and the final two-repository git state (docs-only)
49c919a feat(godot-mcp): TASK-136 - make the strict change margin the PASS criterion, cover all 20 games with the scripted arm, and make the no-redirection claim countable
3ede4f2 docs(godot-mcp): TASK-135 - record the deliverable commit 6999626, the report's first-version hash and the final two-repository git state (docs-only)
6999626 feat(godot-mcp): TASK-135 - fix the three game-side hard blockers the scripted arm exposed, add a declarative strict change margin beside the V3 baseline, and record D187-D191
84103ae docs(godot-mcp): TASK-134 - correct the read_image count in the report (16 images, 15 at full 800x600) and say exactly which table rows are not separate pictures

$ git -C F:\moonbit-hof-rs status --short   （提交前）
 M DECISIONS.md
 M godot-mcp/recovery/reports/TASK-136-REPORT.md
 M godot-mcp/recovery/tasks/TEMPLATE-logic-feedback.md
 M godot-mcp/tools/playtest_player.py
 M godot-mcp/tools/tests/test_playability_model_player.py
?? godot-mcp/recovery/reports/ACCEPTANCE-TASK-137.md     <- 上一批的输入，不是本批的
?? godot-mcp/recovery/tasks/TASK-137-ACCEPT.md           <- 上一批的输入，不是本批的
?? godot-mcp/recovery/tasks/TASK-138.md                  <- 本批的任务输入
?? godot-mcp/tools/_t138_tmp_playtest_player_HEAD.py     <- 本批的临时对照工具，提交前删除
?? godot-mcp/tools/playtest_artifact_index.py            <- 本批新增（入库）
（另有 runs/model-player/_index/** 两个文件，被 .gitignore 忽略，用 git add -f 入库）

$ git -C F:\moonbit-hof-rs\godot-mcp\godot log --oneline -3
ba1587c71e fix(mcp_server): TASK-112 - ...（引擎克隆未动）
$ git -C F:\moonbit-hof-rs\godot-mcp\godot status --short
?? uid_cache.bin        <- 仍然只在原地，未提交（非本轮引入）
```

**提交**：本批的交付提交只暂存**本批独占清单**里的路径
（6 个修改 + `tools/playtest_artifact_index.py` + `_index/**` 两个文件 + `TASK-138.md`），
**没有**代提交 `ACCEPTANCE-TASK-137.md` / `TASK-137-ACCEPT.md`（它们是上一位决策者的输入）。
`_t138_tmp_playtest_player_HEAD.py` 在提交前**删除**（保留 `runs/model-player/t138-oldcode/` 里的副本，
其 sha256 与 TASK-136 报告记录的判据工具哈希逐字相同）。

### 7.4 交付提交

```
$ git -C F:\moonbit-hof-rs commit -F ...\t138_commit_msg.txt
[master 648b94c] TASK-138: align the two measurement windows on ACTUAL drawn frames, forbid the pre-injection ack fallback, require a machine-checkable anchor for every image read, and commit the run-artifact index
 10 files changed, 5528 insertions(+), 33 deletions(-)
 create mode 100644 godot-mcp/recovery/reports/TASK-138-REPORT.md
 create mode 100644 godot-mcp/recovery/tasks/TASK-138.md
 create mode 100644 godot-mcp/runs/model-player/_index/ARTIFACTS-TASK-138.json
 create mode 100644 godot-mcp/runs/model-player/_index/ARTIFACTS-TASK-138.md
 create mode 100644 godot-mcp/tools/playtest_artifact_index.py
```

* 交付提交号：**`648b94c`**（父提交 `5a3da2e` = TASK-136 的收尾文档提交）。
* **第 2 次提交（docs-only）`417dbc9`**：只改本报告，把上面这段"交付提交号 + blob 身份"写回
  （与 TASK-136 的 `5a3da2e` 同一做法）。**它自己的哈希不写进本报告**——写了就自指（勘误 ⑤）。
* 提交后 `git status --short` 只剩 `?? godot-mcp/recovery/reports/ACCEPTANCE-TASK-137.md`
  与 `?? godot-mcp/recovery/tasks/TASK-137-ACCEPT.md`（**上一位决策者的输入，本批不代提交**）。
* **本报告自己的可核身份**：用**提交号 `648b94c` + git blob 哈希**定位，
  **不再声称"报告的内容 sha256 可核"**（勘误 ⑤ 就是这么定的）：
  `git rev-parse 648b94c:godot-mcp/recovery/reports/TASK-138-REPORT.md` 给出**被提交的那一版**
  的 blob 哈希 = **`2d15afc56561abd0720ab95491022ff40704c745`**（本 §7.4 追加前的版本）；
  同一提交里判据工具的 blob 哈希 =
  `git rev-parse 648b94c:godot-mcp/tools/playtest_player.py` = `cc0ba53b08c4610a2ab07924fdb00e7f8bd377a5`，
  完整提交 =
  `648b94c960b2c2274c36be0c2d96cc983600ac0e`。
  本报告此后若被追加改写，blob 哈希会变，而 `648b94c` 里的那一版**永远可复得**。
  另：**产出本报告引用的那批 run 的工具版本**就是上表的
  `playtest_player.py sha256 = 1c343136…`（工作树版 = 提交版的内容，仅行尾在 git 侧会被归一）。

---

## 8. W7 / 铁律 ① —— **本批重定向自查数字**

### 8.1 机制（沿用 TASK-136）

* **台账**：本批命令经 `runs\model-player\_scripts\t136_cmd.py` 执行（执行前把逐字
  `argv + cwd + ts` 追加进 `t136_commands.jsonl`，`shell=False`，stdout/stderr 各走一条 Python 管道）；
* **扫描器**：本批新增 `runs\model-player\_scripts\t138_scan_redirects.py`（扫**本批自己的窗口**
  与本批的驱动脚本），沿用 `t136_scan_redirects.py` 的模式表。

### 8.2 结果（本批自己的窗口）

```
COMMANDS SCANNED (this batch): 73   COMMANDS WITH A REDIRECTION HIT: 0
REAL HITS: 0   false positives: 0
DRIVER SCRIPTS SCANNED: 11   shell=True: 0   literal redirect tokens: 34 (code:10 comment/string:24)
```

* **批界（可复算）**：TASK-136 的最后一个台账条目是**第 116 行**、`ts = 2026-09-28T03:22:58`；
  本批条目 = 它之后的一切（首条 `ts = 2026-09-28T03:44:30`，末条见扫描器输出）；
  台账本批读到时 **186 行**、`sha256 = 1471d443bebfb008b2d794e84e3aa60a2cfcb5dea2e8cf68e25e4da4113db322`（50387 B）。
* 产物：`runs\model-player\_scripts\t138_redirect_scan.json`
  （`sha256 = 79d7e22c70b17430f3b04683ded95eff21eead9e1018d682ef905dc9b073952b`，12618 B）。
* **10 处 `code` 分类的源码命中**（逐条原文，本批自己的实现）：
  ```
  t138_artifact_index.py:14   Per run directory (`<prefix>/<game>/<backend>/`):      <- docstring（分类器局限，见下）
  t138_compare.py:89          ov = (o or {}).get("verdict") if o else "<no old run>" <- 字符串里的 `<...>`
  t138_compare.py:90          nv = (n or {}).get("verdict") if n else "<no new run>" <- 同上
  t138_repeat.py:29           n = int(argv[1]) if len(argv) > 1 else 3              <- 比较运算符 `>`
  t138_windows.py:30          print("player.json -> frame_alignment: %s" % ...)      <- 字符串里的 `->`
  playtest_artifact_index.py:14（同一行 docstring 的 3 个 `<...>`）
  ```
  **全部是假阳性**：`<placeholder>` 写法、字符串里的 `->`、以及 Python 的比较运算符 `>`；
  `shell=True` **0 处**，真正的重定向令牌（`2>&1`/`2>/dev/null`/`1>NUL`/`> nul`/`*>`/`>>`）
  **0 处**（扫描器的 `code`/`comment` 分类是**近似**，它把三引号 docstring 里的行归到 `code`；
  这一点如实说明，与 TASK-136 §3.4 同）。

### 8.3 本批的**真实违规 1 条**（如实报）

在本批开头，我（在把包装器接上之前）用 `term` 跑过一条**只读**环境探针，命令里带了
`2>/dev/null`：

```
D:\Anaconda\python.exe -c "..." 2>/dev/null
```

它把该 Python 进程的 stderr 丢进空设备（当时用于探测服务健康）。该命令**不在台账里**
（包装器尚未接手），因此**不在 73 条扫描范围内**——按任务书 §2.1 的字面要求
**就是违规，如实计 1 条**。它只影响我自己的控制台，没有参与任何测量或判决，
但**不因为"没影响结论"抹掉**。此后本批**全部 73 条命令命中 0**。

---

## 9. W8 —— `DECISIONS.md` 本批条目（D198–D201）

`F:\moonbit-hof-rs\DECISIONS.md`（`sha256 = 28a96449338968d2fa08bcfaf8e66ac895572a798b93c3effaa0a7ca1338aa52`，
861488 B）追加在 D197 之后：

| 编号 | 题目 |
|---|---|
| **D198** | TASK-138 defect ⑧：两窗按**实际达成帧数**对齐（含 4 个被否决的方案与"为什么宽括号方案实测被否"） |
| **D199** | TASK-138 defect ⑨：`ack_result` 缺失 ⇒ INCONCLUSIVE，**禁止**回退 `pre_ack` |
| **D200** | TASK-138 §1.C.2：逐帧读图描述**必须带可机检锚点**（模板硬要求） |
| **D201** | TASK-138 §1.C.3：产物清单**提交进仓**（`runs/**` 不入库前提下的可核验机制） |

---

## 10. W10 —— 未达标项 / 未做项 / 遗留风险（**不用"应该可以"**）

### 10.1 §2.8「改引擎模块才触发两变体重建 + 十道门 + `accept_m1` + push」

**未触发**。依据：本批改动的全部文件都在 `godot-mcp/tools/**`、`godot-mcp/recovery/**`
与 `DECISIONS.md`（§7.2 的清单），**没有** `godot/modules/mcp_server/**` 或任何引擎模块；
`git -C godot-mcp\godot status --short` 只有一条**非本轮引入**的 `?? uid_cache.bin`。
`--window-poll-gap` 等新参数是**客户端**行为，没有新增/修改任何 Godot 工具。

### 10.2 对齐的**残余**与它的成因（如实报）

* 两窗跨度**精确相等**的步只有 53/188（脚本）+ 9/32（模型）；**其余相差 0–6 帧**
  （中位 1、最大 6；±5 内 187/188 与 32/32）。
* 成因：等待循环走的是**客户端轮询**，而一次 MCP 往返推进游戏多少帧**不受控**
  （同一段代码在动作窗与对照窗的往返耗时不同 ⇒ 各自超出目标 1–6 帧）。
  客户端**无法把游戏钉在某一帧**；要做到 0 帧差需要"暂停世界 + 按帧推进"的引擎侧钩子，
  那属于选项 4（改 `godot/` 克隆 → 触发两变体重建 + 十道门），**超出本批范围**。
* 这个残余**不改变比较的有效性**：`gameplay_movement` 是位移之和、随窗口长度增长，
  而两窗现在是同一量级的 30–35 帧（旧的是 119 vs 33），残余 0–6 帧对应 ≤20% 的窗口长度差，
  且**方向随机**（不像旧口径那样系统性偏向动作窗）。

### 10.3 asteroids 翻转的**敏感性**（决策者需要知道）

* 新口径：3/3 次重跑都是 `PASS`（边缘步 0）；旧口径：2/2 次对照都是 `PASS(baseline only)`
  （strict 失败步都在 [7,11]）。
* **两个都是真读数**，差别来自**对照窗长度**：短对照窗量到的 `control_movement` 更小，
  长对照窗量到的更大（steps 3/5/7/11 上尤其明显）。
* 因此这条翻转不是"修好了游戏"，而是"**换了测量口径**"。本批按任务书
  §0 第 8 条（"按实际达成的帧数对齐：取两窗较小者，或补采/裁到相等"）执行，
  并如实把这个敏感性登记为遗留风险：**若要更保守，应固定一个更长的窗口长度并重跑全批**。

### 10.4 其它未做/未修（承接 TASK-136，本批未变）

| # | 项 | 状态 |
|---|---|---|
| 1 | 3 款游戏侧硬阻塞（flappy 世界不自走 / bomberman 引信不燃 / frogger 一次按键三条命） | **仍未修**（本批只测不改）；本批对 flappy/minesweeper 的记录是**降级为 INCONCLUSIVE**，不是"修好了" |
| 2 | 模型臂 4 款的端点 12288 token 上限 | 未修（不在本批范围） |
| 3 | 合法拒绝未被判据识别（match3/minesweeper/pacman/sokoban/towerdefense 的拒绝计数器不在 `refusal_evidence.keys`） | 未改声明（**会动到其它批次的读数**） |
| 4 | `runs/**` 被忽略 | 已用 `_index/ARTIFACTS-TASK-138.*` 缓解（**本批新增**），但**原始 run 产物仍只在本机** |
| 5 | 本批**没有**重跑脚本臂以外的 17 款模型臂 | 任务书只要求 tetris/pong/asteroids（模型臂）+ 脚本臂 PASS 款；**其余 17 款模型臂的旧结论未复核** |
| 6 | 本批**没有**把 `--window-frames` 提高后重跑 | 见 §10.3 的敏感性登记；这是留给决策者的下一步选项 |
| 7 | 勘误只加了 TASK-136 报告一份 | 未创建 `ERRATA.md`（二选一） |

### 10.5 环境与过程说明（如实）

* 本批在启动 20 款 sweep 前，曾因**终止信号没有传到包装器的子进程**而让两批
  `t138_sweep.py` 同时存活（日志交错、`rc=1`）。处置：用 `psutil` 逐个杀掉**本批自己**的
  `t138_sweep.py` 与其 `godot` 子进程（**没有**杀 8080/8081），然后**重新完整跑一遍**
  并核对日志（`t138_sweep.log` 的 START/DONE 一一配对，20/20 + 3/3）。
  这次重跑**产出的就是本报告引用的那一批数据**（`ts 2026-09-28T04:00:26` 起）。
* 本批曾误把产物清单写到库外的 `F:\runs\...`（工具从 `_scripts` 移到 `tools` 后根目录算错一层），
  已**删除**该库外目录并修正路径（`tools\playtest_artifact_index.py` 的 `ROOT = HERE\..`）。

---

*报告结束（TASK-138）。*
