# TASK-129 报告 — PlayJev 视觉判定接进试玩门 + 真负面样本标定（并修 Jev 侧的 token 估计与采样缺陷）

> **状态：done**
> 执行者：TASK-129 子代理（用户裁定**严格单线程**后本仓唯一在跑的代理）
> 时间：2026-09-27 → 2026-09-28（本机时钟；三次模型扫描合计约 33 分钟门运行时）
> 报告落点：`F:\moonbit-hof-rs\godot-mcp\recovery\reports\TASK-129-REPORT.md`
> **全程只调用本机 `127.0.0.1:8080`（NeoHorse-Jev-4B）与 `127.0.0.1:8081`（PlayJev-0.8B）；
> 没有任何图像/状态发往第三方端点；未重启、未杀这两个服务；未写 `/opt/*-venv`、`F:\models\**`。**

---

## 0. 结论速览

| 项 | 结果 |
|---|---|
| A `D-B` 多状态采样 | ✅ **20/20 款各拿到 3 个哈希不同的 state**（`agent_sample_size 3/3`），每次调用连同它看到的 state（label + sha256 + 裁剪明细）逐条落 `agent.json → observations[]`；门另记"最坏观测"聚合 `aggregate_over_observations` |
| A `D-C` token 估计 + 422 重试 | ✅ 估计改为**按服务端 `usage` 实测标定的保守系数 ×2.5**（`ceil(2.5×旧估计)`，并证明"新 2000 == 旧 800"在 20 份真实 state 上逐款等价）；**真 422 自动减半重试**（上限 2 次、逐次留证、丢掉的节点逐个点名、不静默截断），并在**真实 8080 服务**上留下一次真实 422 重试记录（`client 1825 → 服务端 "state exceeds 2048 tokens: 2142" → 减半到 800 → HTTP 200`） |
| B `D-D` 负面变体 + 真帧 | ✅ `projects/_exercises/neg_input_dead / neg_black_screen / neg_frozen / neg_hud_missing` 四类**声明式**变体（全是拷贝、C# 逐字节未改、只改 `.tscn` 一行），`--headless --quit-after 60` **退出码全 0**，各自采到**真实整窗帧**（`runs/playability/negatives/<mode>/frames/*.png`，21/34/22/80 张，含 sha256） |
| C 视觉判定接进门 | ✅ `--visual-agent=playjev`：**1 图 + N 问**（`move` + `playable` + 另 2 个不变量 + `brokenness`），结果写 `gate["playjev"]` 与 `gate["agent"]` **并列**；`playjev_thresholds` 独立于 Jev 的阈值块，含 `uncalibrated:true` 与局限 |
| C `D-E` score 撤出判定 | ✅ `score` 只作 `score_observation`（`in_decision_path:false`、`direction:"suspect"`），判定只用 `playable`；**翻转图例探针**结果只写 `legend_probe`，永不进判定 |
| 正/负样本跑完 | ✅ 20 款正样本（13.4 min）+ 4 类负变体（3.4 min）+ 20 款修复前 export（16.7 min）**全部跑完，零 MCP 错误、零 429/529** |
| `V6` 用真负面帧标定 | ⚠️ **标定了，并判定"没有可用阈值"**：正类 `playable` 0.105–0.886（中位 0.445），真负类 0.125–0.748（中位 0.405）→ **完全重叠**；最佳游戏级切点仍 17 错 / 39 款。**保留先验 0.5**，理由与两个备选运行点全部写进 `playability_controls.json` |
| ★ 机制发现（实测） | **PlayJev 的 `playable` 只是像素的确定性函数**：60 张不同图像、83 次判定中，被判定过两次以上的 **22 张全部得到逐位相同**的 `playable`/`score`，其中 **20 张同时出现在"修好版"和"修复前 export"里**（另 2 张跨"修好版 ↔ 声明式负变体"）→ **不改变像素的缺陷（输入死、冻结）对它天然不可见**，这正是负类不可分离的机制 |
| `V8` 冲突登记 | ✅ 21 条逐条登记（14 条视觉误报点名、7 条视觉漏报），含"谁抓到/谁漏掉"与原因；并明确写出模型判定的语义边界 |
| 铁律 | ✅ 无 shell 重定向、无破坏性命令、未改 20 款正式工程逻辑、未动引擎模块（**不触发**重建/十道门/`accept_m1`/push）、单端口 9911、串行调用模型 |

---

## 1. 任务书事实的来源等级与更正（铁律 9：代码/数据与任务书冲突时以实测为准并显式纠正）

| # | 任务书/前序报告的说法 | 本次实测 | 证据（等级） |
|---|---|---|---|
| 1 | §0.3 "门在 3 次调用里递同一份 state → 每款只有 1 个独立观测" | **属实**，本次已修（D-B）：20/20 款 3 个哈希不同 state | 一手：`runs/playability/t129-pos/<game>/agent.json → observations[].state_sha256` |
| 2 | §2.A "`tools/playtest_agent.py`（仅在其内新增 playjev 相关行）"（文件所有权注） | **与 §2.A 交付物 A 冲突**：修 `jev_estimate_tokens` 与 422 重试必然改到 jev 侧代码。**按 §2.A 执行**，并在此显式记录这次"越出该注"的改动范围：仅 `jev_estimate_tokens/raw`、`JevAgent.shrink_state/_is_state_overflow/decide` 的重试循环、`report()` 多两个字段 | 一手：本报告 §2、`git diff tools/playtest_agent.py` |
| 3 | TASK-127 "`score` 方向反了（黑屏 2.41 < 真实 snake 帧 3.97）" | **是单对样本的轶事，按类聚合并不反转**：真帧正类中位 2.430 > 负类中位 2.359；派生帧正类中位 2.969 > 负类 2.378（都不反转）。真正的缺陷是**零分离度** | 一手：`runs/playability/t129-playjev-fit*.json → score_observation` |
| 4 | TASK-127 用**派生帧**当负面样本（黑屏/平色/内容抹掉） | 派生帧已被**真帧**取代（D-D）；派生锚点仅作对照保留 | 一手：四个 `neg_*/frames/*.png` 是运行中的游戏进程整窗截图 |
| 5 | §0.3 "`score` 零分离度"（Jev 侧） | **在 PlayJev 侧同样成立**（本任务 C 的结论），且机制被查清（像素决定性） | 一手：§5、`runs/playability/t129-frame-identity.json` |
| 6 | TASK-128 `noul_min_p_true=0.25`（20 正 / 16 负，每款 1 观测） | **只在"注入后单状态"构型下成立**：D-B 多状态构型下同一 0.25 会误报 13–14/20 款修好版。**阈值未改**，构型与重测结果写进 controls | 一手：`runs/playability/t129-playjev-fit.json → jev_multistate_fit` |
| 7 | §0.1 "两台服务共用一块 RTX 4090、并行峰值 20 493 MiB 无 OOM、串行调用" | 复用该前提：本次全程**单任务串行**、每款内的模型调用也串行（`JevAgent._lock` / `PlayJevAgent._lock`），全程 **0 次 429/529、0 次 OOM** | 一手：各 `agent.json → report.calls[*].transport.attempts` |

---

## 2. §2.A 修 Jev 侧两处缺陷（D-B / D-C）

### 2.1 `D-B`：多状态采样——"3 次调用"现在是 3 个独立观测

**实现**（`tools/playability_gate.py`）

* 门本来就在整轮里采样很多 state（`00_settle`、每动作前/后的 `*_pre|*_ctl|*_act`、`auto*`、`post*`）。新增 `state_pool` 把它们全部收下，再由 `pick_state_samples()` **按"真正送给模型的那段文本"的 sha256 去重**（所以"两棵不同的树裁成同一份请求"只算 1 个观测），偏好顺序为 D-B 自己举的例子：
  **注入前（`00_settle`） → 注入后（最后一个 `*_act`） → 一段时间后（最后一个 `post*`）**，不够再按池序补。
* `--agent-state-samples N`（默认 3）控制要几个；**凑不够就如实记 `sample_size: 1`**（D-B 原文），
  并把 `sample_size_required` / `sample_size_is_independent` / `sample_size_note` 一起落盘。
* 每次调用写进 `gate["agent"]["observations"][i]`：`state_label / phase / state_sha256 / source_state_sha256 /
  state_for_agent（含裁剪明细与 fingerprint）/ action / threshold_verdict / evidence（逐字请求与回答）`。
* 另加 `agent_aggregate()`：一旦真的采了多个状态，"最坏观测"才是诚实的聚合（每款只有**所有**被采到的状态都过，才算过），
  写进 `gate["agent"]["aggregate_over_observations"]`；**顶层 `threshold_verdict` 保持 TASK-124 的形状（最后一次调用）**，
  两者在报告与产物里都写明哪个是哪个。

**V1 证据**

```
runs/playability/t129-pos/playability.json  ->  20 款，agent_sample_size 全部 = 3（sample_size_required = 3）
逐款样例（pong）: observations[0].state_label = 00_settle                    sha256 deb05c53…
                 observations[1].state_label = a04_pong_serve_parse_act      sha256 b742faca…
                 observations[2].state_label = 01_auto                       sha256 b675a620…
                 三次 noul 各不相同（0.6705 / 0.6981 / 0.6237 for playable_frame）
负变体（4 款）同样 3/3；修复前 export（20 款）同样 3/3。
```
> 反例对照（TASK-128 的原症状）：同一个 state 递 3 次时三次 `noul` **逐位相同**。本次 20 款里没有任何一款出现相同 state 被重复计数。

### 2.2 `D-C`：token 估计按服务端 `usage` 标定 + 真 422 自动减半重试

**（a）估计器**（`tools/playtest_agent.py`）

```python
JEV_TOKEN_SAFETY_FACTOR = 2.5                    # ceil(2.36)，取实测最坏比值向上取整
jev_estimate_tokens_raw(text)  = (ascii+3)//4 + other      # TASK-128 的旧公式（保留）
jev_estimate_tokens(text)      = (5*raw + 1)//2            # == ceil(2.5 * raw)
```

标定依据（一手，TASK-128 §3.1 逐字记录在 `JEV_TOKEN_SAFETY_BASIS` 里）：

| 样本 | 旧估计 raw | 服务端 `usage.input_tokens` | 比值 |
|---|---|---|---|
| breakout 未裁 | 1018 | 2160 | 2.12 |
| breakout 裁剪后 | 1800 | 2172 | 1.21 |
| bomberman 裁剪后 | 1791 | 4229 | **2.36（最坏）** |
| pong | 431 | 200 接受 | — |

**单位变更与桥梁（可验证）**：`ceil(2.5·raw)` 让 **`--agent-state-budget 2000` 选出的 state 与 TASK-128 的 `800` 逐款完全相同**
（2000/2.5 = 800）。已在 20 份真实 state 上逐款核对：**identical=20/20，different=0**
（`python runs\playability\_t129_check_tokens.py`，其中 bomberman 18/129、breakout 18/23 与 TASK-128 的记录一致）。
因此 TASK-128 拟合的 jev 阈值在 `2000` 下仍可比；`playability_controls.json` 的 limitations 里写明。

**（b）真 422 减半重试**（`JevAgent.decide` 里的独立循环，**不动**传输层 422 语义）

* 只在 422 且正文出现 `state ... token ... exceeds` 时触发；每次把 state **减半**（在 `nodes` 内按树序丢尾巴，逐个点名丢掉的节点），
  上限 `--max-state-retries`（默认 2），每次尝试写进 `report.calls[*].state_budget_retries`。
* **不静默截断**：丢掉的节点名字、`before/after` 估计、服务端原文都在记录里。

**V2 证据（真实服务上的一次真实重试）** — `tools/jev_422_retry_probe.py` → `runs/playability/t129-jev-422-retry.json`：

```
endpoint        : http://127.0.0.1:8080/v1/systemone      health 200 {"status":"ready","model":"NeoHorse-Jev-4B"}
探针状态         : 2800 字符的确定性伪随机 base64（token 密集型；客户端 1825 ≤ 2048 上限，客户端的保守系数看不到它）
直接 POST       : 422 {"detail":"state exceeds 2048 tokens: 2142"}      ← 真服务、真拒绝
decide() 路径    : 1 次重试 → 1825 → 800 估计，丢掉 nodes b3,b4,b5,b6（保留 3/7）
                  policy = "keep `nodes` in tree order until the estimate fits half the previous budget; name every dropped node"
最终            : HTTP 200，model NeoHorse-Jev-4B，usage {input_tokens 1147, output_tokens 435}，errors []
传输层 attempts  : 1（422 没有被当成 429/529 那样重试——TASK-124 的 D4_422_not_retried 语义保持）
```

> 顺带得到一条实测事实：这份 base64 密集状态的**真实/旧估计比值是 2.93**（2142 / (1825/2.5)），
> **高于 2.5**。所以"保守系数"也不能替代重试——两者必须同时存在（D-C 的两半正是这样设计的）。

### 2.3 回归（未破窗）

* `python tools\playtest_agent.py --probe-jev` → **33/33 全 true，`failed: []`**（含 `D4_422_not_retried`、`D5_overlong_state_refused`、
  `D5_clip_declares_dropped`、`R_*` 三条回归项）→ `runs/playability/agent-probe-jev.json`
* `python tools\playtest_agent.py --probe-playjev` → **49/49 全 true**（含 TASK-127 的
  `score_only_abstain_is_not_a_pass`：score 虽退出判定路径，但"没能回答"这件事**仍然**让判定变成"无判决"）
  → `runs/playability/agent-probe-playjev.json`
* 三次全量扫描：**0 MCP 超时、0 对话框、0 OOM、0 次 429/529**。

---

## 3. §2.B 声明式负面变体 + 真实退化帧（D-D）

四个变体都在 `projects/_exercises/`，全是**现有工程的拷贝**，**C# 逐字节未改**（构建器逐文件校验并写进 `variant.json`），
只改拷贝的 `scenes/main.tscn` 里**一行声明**——因为 16/20 款游戏自己就把这个开关 `[Export]` 出来了（`PollInput`），
所以拷贝版复现的正是 TASK-128 在导出件里测到的同一种失效。构建/验证脚本：
`projects/_exercises/neg_BUILD_VARIANTS.py`（可重跑、幂等），构建记录：`runs/playability/negatives/variants-build.json`，
清单：`runs/playability/negatives/NEGATIVES-INVENTORY.json` / `.md`。

| 变体 | 失效模式 | 源工程 | 声明式改动 | 场景 sha256（改后） | headless | 期望被谁抓到 | 实测被抓到 |
|---|---|---|---|---|---|---|---|
| `neg_input_dead` | 输入断开 | minesweeper | `Main.PollInput = false` | `8f6ad289…c458` | exit 0 | P2/P5/P6 | **P2/P5/P6 FAIL**（P1/P3 PASS）✔ |
| `neg_black_screen` | 不渲染/黑屏 | snake | `Main.visible = false` | `e1f41c34…a8af` | exit 0 | P1 | **P1 FAIL**（"single flat colour, 0 content pixels", bg=[72,72,72]），其余 PASS ✔ |
| `neg_frozen` | 冻结 | breakout | `Main.process_mode = 4` | `bfa0144a…bc8e` | exit 0 | P3 | **P3 FAIL**（`frames_drawn 265 → 1519` 仍在涨，但自主状态变化 0、像素变化 0），P2/P5/P6 随之 FAIL ✔ |
| `neg_hud_missing` | UI/控件缺失 | tetris | `SidePanel/PanelEdge/HudLabel.visible = false`（240×480 px，窗口 800×600 的 24%） | `8d97a04a…06f1` | exit 0 | **声明为"没有机检能抓"** | **P1..P6 全 PASS**（门判 playable）✔ ——盲点被证实，不是被掩盖 |

**真实退化帧落盘**（`runs/playability/negatives/<mode>/frames/*.png`，均为运行中游戏进程的整窗截图，
门的 `running_game_capture_screenshot` 采集，逐帧 `sha256` 在 `frames.json`）：

| 变体 | 帧数 | settle 帧 | settle sha256 | 预期标签 |
|---|---|---|---|---|
| `neg_input_dead` | 80 | `01_settle.png` | `0e1d9002e8cd37a0…` | 画面正常、**按键全无响应** → P2 FAIL |
| `neg_black_screen` | 21 | `01_settle.png` | `1b20355e8ca4b3a3…` | 平色/零内容 → P1 FAIL；PlayJev 应给低 `playable` |
| `neg_frozen` | 34 | `01_settle.png` | `c8df2c551ae6e55c…` | 画面正常但永不推进 → P3 FAIL |
| `neg_hud_missing` | 22 | `01_settle.png` | `cac1d9e4f04dc1d9…` | 界面消失、逻辑完好 → **机检应当全过** |

四类各自跑到一条**互不相同**的判据（P2 / P1 / P3 / 无），这是 V3 想要的东西：负类不再只有一种失效模式。

---

## 4. §2.C PlayJev 视觉判定接进试玩门（`D-E`）

### 4.1 门的接口

```cmd
python tools\playability_gate.py --all --agent=jev --base-url http://127.0.0.1:8080 ^
  --agent-state-budget 2000 --visual-agent=playjev --visual-legend-probe ^
  --out-root F:\moonbit-hof-rs\godot-mcp\runs\playability\t129-pos
```

* `--visual-agent=playjev` 与 `--agent` **并列运行**（一次游戏会话里同时拿文本侧和视觉侧证据）；
  `--agent=playjev` 这条 TASK-127 的老路径照旧可用。
* **1 图 + N 问**：一次请求带 1 张整窗 PNG + 5 个 Choice（`move`、`playable`、`no_render_failure`、
  `responds_to_input`、`brokenness`）；`--visual-frames`（默认 3）决定判几张**哈希不同**的帧
  （与 D-B 同一个教训：pong 在发球前每张自动帧字节相同，若不去重就是"1 个观测报 3 次"）。
* **判定只用 `playable`**：`PlayJevAgent` 新增 `verdict_invariant_keys=["playable"]`，其余 noul 落
  `threshold_verdict.noul_observations`（`in_decision_path:false`）。
* `score`（`brokenness`）**不在判定路径**：`score_in_decision_path:false`、`direction:"suspect"`、`uncalibrated:true`，
  写入 `gate["playjev"]["score_observation"]`。
* 阈值来自 `tools/playability_controls.json → playjev_thresholds`（**独立于** `agent_thresholds`），
  含 `uncalibrated:true` 与 7 条 limitations；门把源块逐字抄进 `gate["playjev"]["thresholds_source_block"]`。
* 结果同时落 `runs/playability/<out-root>/<game>/playjev.json`，并在汇总里给 `playable_values` /
  `playable_distribution` / `frames_used[].sha256` / `legend_probe`。

**V4 证据（pong，一次真实的门运行）**：

```
gate["playjev"]["verdict"]        = {"pass": true, "why": "3/3 frames clear `playable P(true) >= 0.500`: worst 0.618540"}
gate["playjev"]["score_in_decision_path"] = false
gate["playjev"]["legend_probe"]["in_decision_path"] = false
gate["playjev"]["thresholds"]     = {"noul_min_p_true": 0.5, "score_max_expected": 2.5}
gate["playjev"]["thresholds_source_block"]["uncalibrated"] = true
逐帧原始概率（示例，settle）        : {"yes": 0.664783, "no": 0.335217}, confidence 0.329565, abstain false
```
文件：`runs/playability/t129-smoke-final/pong/playjev.json`。

### 4.2 三次扫描全部跑完（V5）

| 扫描 | 内容 | 款数 | 门判定 | 用时 | 汇总 |
|---|---|---|---|---|---|
| `t129-pos` | 20 款修好版（工程树） | 20 | **20 playable / 0 not_playable**，P1..P6 零失败 | 801 s | `runs/playability/t129-pos/playability.json` |
| `negatives` | 4 类声明式负变体 | 4 | **1 playable（hud_missing）/ 3 not_playable** | 205 s | `runs/playability/negatives/playability.json` |
| `t129-neg-exe` | 20 款**修复前 export**（`--exe-root`） | 20 | **4 playable / 16 not_playable**（与 TASK-128 逐款一致） | 1004 s | `runs/playability/t129-neg-exe/playability.json` |

* 正样本 PlayJev 用了 **51 帧**（15 款 3 帧、1 款 2 帧、4 款 1 帧——去重后）；负变体 6 帧；修复前 export 32 帧。
* **没有一款因为"跑不了"缺失**；没有跳过任何一款。
* 门的 P1..P6 判定与 TASK-116/128 一致（20/20 与 16/20），说明新参数**没有改变机检语义**。

---

## 5. `V6` 用真负面帧标定 `playable`

工具：`tools/playjev_visual_calibrate.py`（读数只读、无网络、可重跑）。两份产物：

* `runs/playability/t129-playjev-fit-declared.json`（负类 = 4 类声明式变体）
* `runs/playability/t129-playjev-fit.json`（负类 = 声明式变体 **+** 修复前 export，
  后者按 **D-A** 才是"玩家拿到的产物"的权威；其中门自己判 playable 的 4 款与"机检也判可玩"的
  `neg_hud_missing` **不计入负类**——标签来源写进每一行的 `label_source`）

### 5.1 分布（逐帧 / 逐款最小值）

| 集合 | 帧数 | min | 中位 | max |
|---|---|---|---|---|
| 正样本（20 款修好版） | 51 | **0.104813** | 0.444876 | 0.885693 |
| 负类（声明式 3 类计数） | 3 | 0.125427 | 0.210474 | 0.448697 |
| 负类（+ 修复前 export，计数 19 帧 / 19 款） | 19 | 0.125427 | 0.404992 | **0.747749** |

**重叠判定（工具自动给）**：

```
declared-only : positive_min 0.104813  vs  negative_max 0.448697  -> gap -0.343884  可分离=false
with exports  : positive_min 0.104813  vs  negative_max 0.747749  -> gap -0.642936  可分离=false
```

### 5.2 阈值扫描的错分（不是只给平均值）

| 切点 | 正类被误报（款） | 负类被放过（款） | 游戏级错分 |
|---|---|---|---|
| **0.500（保留的先验）** | 14（bomberman, breakout, frogger, lunarlander, match3, minesweeper, missilecommand, pacman, puzzlebobble, rtype, snake, sokoban, spaceinvaders, towerdefense） | 5（asteroids, flappy, game2048, platformer, sokoban） | **19 / 39** |
| 0.218557（**游戏级最优**，含 export 负类） | 4 | 13 | **17 / 39** |
| 0.104813（帧级最优 / 声明式负类最优） | 0 | 3（全部声明式负类） | 3 / 23 |
| 0.500（**仅有声明式负类时**） | 14 | 0 | 14 / 23 |

> 帧级最优 19 错 / 70 帧；游戏级最优 17 错 / 39 款。**两个粒度都没有可用运行点**：
> 想要不漏坏游戏就要误报一半修好版；想要不误报就放过全部真负样本。

### 5.3 与 TASK-127 派生帧锚点的对比

TASK-127 的负面帧是**派生**的（把真实帧整幅涂黑 / 涂成自身背景色 / 抹掉内容 bbox）。本次把同一探测器
用真帧重测（`derived_anchor_comparison`）：

| 帧 | 来源 | `playable` | `brokenness` |
|---|---|---|---|
| 3 张真实正样本帧 | TASK-127 真捕获 | 0.564843 / … | 2.243 / 2.969 / 3.971 |
| 派生"黑屏" | 派生 | **0.202030** | 2.365953 |
| 派生"平色" | 派生 | **0.199660** | 2.378218 |
| 派生"内容抹掉" | 派生 | **0.202728** | 2.413003 |

**对比结论**：派生帧给出的 `playable ≈ 0.20` 看起来"很好分离"，但那是**我们自己在图像里涂掉了像素**的结果；
换成本任务采集的**真负面帧**后，同一探测器给出的中位是 **0.405**，与正样本（0.445）几乎重合。
→ **派生锚点高估了模型的判别力**：它测的是"探测器对一幅被我们改坏的图有没有反应"，不是"对真实坏版本有没有反应"。
这条是替换派生样本的直接收益，也解释了为什么 TASK-127 的初步锚点（0.202 vs 0.48–0.85）不能推广。

### 5.4 选定值与理由（**保留先验 0.5**，`uncalibrated` 保持 true）

`tools/playability_controls.json → playjev_thresholds.playable_min_p_true` **保持 0.5**，理由逐条写进了文件：

1. **没有任何切点分离两类**（gap 为负）；把 0.2186 写进去只是"换一个同样没根据的数"，且它在权威负类上仍是 17 错；
2. 0.5 至少在**声明式负类**上 0 漏报（3/3 全抓到），代价是 14 款误报——**对一个只记录、不自动判决的第二信号**，
   这个方向的错更安全（宁可让评审去看画面，也不要让坏样本溜过去）；
3. `uncalibrated:true` 保持，不给 ECE——几十帧上的 ECE 是噪声（与 TASK-128 的立场一致）；
4. 两个备选运行点连同它们的错分明细**都写进文件**，读者可以自己改，不需要相信我们。

### 5.5 ★ 机制发现：`playable` 是像素的确定性函数，所以"输入死/冻结"对它天然不可见

`runs/playability/_t129_frame_identity.py` → `runs/playability/t129-frame-identity.json`：

```
60 张不同图像、83 次判定；被判过两次以上的图像 22 张
→ 22/22 得到逐位相同的 `playable`（以及逐位相同的 `score`）；0 张出现不同值
其中 20 张同时出现在【修好版工程树】和【修复前 export】里，值完全一致，例如：
  tetris  fix 0.845886 / pre-fix 0.845886      game2048 fix 0.655157 / pre-fix 0.655157
  pong    fix 0.664783 / pre-fix 0.664783      snake    fix 0.482532 / pre-fix 0.482532
  flappy  fix 0.747749 / pre-fix 0.747749      minesweeper fix 0.125427 / 宣告负类 neg_input_dead 0.125427
  breakout fix 0.448697 / 宣告负类 neg_frozen 0.448697
```

**读法**：修复前 export 的缺陷是 `PollInput=false` → **画面一个像素都没变**，所以一个只读像素的模型给出的
`playable` 与修好版**完全相同**。这不是"模型偷懒"，是**任务本身对像素不可判**。
推论（也解释了 §5.1 的重叠）：
* 对**画面确实变了**的坏样本它是有反应的：`neg_black_screen 0.210`、`neg_input_dead 0.125`（同一款修好版也是 0.125）；
* 它的取值很大程度上跟着**游戏的视觉风格**走（修好的 minesweeper 0.125 < 坏的 tetris 0.85），
  因此**跨游戏比较它的绝对值没有意义**；
* 真正能看见"界面没了"（`neg_hud_missing`）的只有视觉侧，而机检 P1..P6 抓不到——两个盲点互补，但都**不能**单独当判决。

---

## 6. `V7` 翻转图例探针（声明式，永不进判定）

同一张帧、同一个问句，只把 `brokenness` 的**选项顺序**反转（1..5 → 5..1），期望值一律按**规范顺序**重算
（所以测的是模型、不是我们自己的重排）。

| 指标 | 值 |
|---|---|
| `|flipped − normal|` | 中位 **0.126**（1..5 尺度），最大 1.09 |
| `|flipped − mirror(=6−normal)|` | 中位 **1.088**（"答案跟着槽位走"的假设明显更差） |
| `playable` 在翻转请求里的取值 | 44/44 **逐位不变**（翻转只改了 score 那一问，证明各问是独立前向） |
| 是否进判定 | `legend_probe.in_decision_path = false`（代码与产物两处都写死） |

**读法**：score 既不是"纯读标签"（否则 |Δ|=0），也**不是**"纯粹跟着选项顺序"（否则 |Δ−mirror|=0），
而是**部分受措辞/图例顺序影响**（~0.13/4 = 3% 的尺度），且 §5.3 已证明它零分离度。
D-E 把 `score` 撤出判定路径因此是对的；探针的结果只回答"方向反转是不是措辞伪影"，
答案：**部分是，而且这不改变"不能拿它判决"的结论**。

---

## 7. §2.D 一致性与冲突登记（不得抹平）+ 语义边界

### 7.1 四方逐款对照

完整 44 行（20 正 + 24 负）在 `runs/playability/t129-playjev-fit.json → conflict_matrix.rows`。
每行含：`machine_P1_P6`（本次实测）、`jev_state_verdict`（本次多状态、最坏观测聚合）、
`playjev_vision_verdict`（本次）、`history`（TASK-116 修好版 / TASK-128 修复前 export 的结论）、
以及标签来源 `label_source`。摘要：

| 手段 | 正类（20 款修好版） | 权威负类（16 款真坏的 export） | 说明 |
|---|---|---|---|
| **P1–P6 机检** | 20/20 判 playable | 16/16 判 not_playable（P2/P5/P6 FAIL） | 本次与 TASK-116/128 一致 |
| **Jev 文本（多状态 @0.25，最坏观测）** | **14/20 被误报为坏**（若只算声明式负类则 13/20） | 漏放 3（frogger、puzzlebobble、spaceinvaders） | 只在"注入后单状态"构型下才有 TASK-128 的 3/36；构型一变就塌 |
| **PlayJev 视觉（@0.5）** | **14/20 被误报为坏** | **漏放 5**（asteroids、flappy、game2048、platformer、sokoban） | 机制见 §5.5：像素没变的缺陷看不见 |
| **PlayJev 视觉（声明式负类 @0.5）** | 同上 14 条误报 | 3/3 全抓到（含黑屏、冻结、输入断） | 因为其中两张帧的像素**确实变了** |

### 7.2 冲突逐条（谁抓到、谁漏掉、可能原因）

**模型误报（修好版被判坏）——14 条，全部点名**：
`bomberman, breakout, frogger, lunarlander, match3, minesweeper, missilecommand, pacman,
puzzlebobble, rtype, snake, sokoban, spaceinvaders, towerdefense`。
原因（实测，不是猜）：这些游戏的画面在 PlayJev 的偏好里就是"不像在玩的游戏"（大量静态方格/背景色），
同一个绝对值也出现在它们的**修复前 export** 上（§5.5 的 20 组同图同值）。
这是**模型的视觉偏好**，不是游戏的问题——P1..P6 对这些款全部 PASS，**每一款声明的输入动作在真实按键注入下都有响应**
（P2 逐动作 `real_key=True`，`t129-pos/<game>/gate.json → criteria.P2`）。

**模型漏报（真坏的 export 被判好）——5 条**：`asteroids, flappy, game2048, platformer, sokoban`。
原因同上：这 5 款修复前 export 的**画面与修好版逐像素相同**（同图同值），
输入死这种缺陷在像素上不存在，所以"看不见"是**任务性质**而非模型缺陷。

**Jev 文本侧漏报 2 条**：`frogger`（noul 0.3835）、`puzzlebobble`（0.3302）——TASK-128 已登记，本次多状态重测仍然漏。

**门 vs 历史结论的冲突（保留，不抹平）**：`breakout / snake / tetris` 的修复前 export 本次仍判 **playable**
（TASK-116 在工程树上判 not_playable），`pong` 三方一致。与 TASK-128 §4.3 完全相同：
**"权威度量是被测对象（工程树 vs 导出件）的函数"**，D-A 要求并列登记，本报告并列。

### 7.3 谁抓到 / 谁漏掉（对"输入死"这一真实缺陷）

| 手段 | 抓到 | 漏掉 |
|---|---|---|
| P2（真实按键 + 对照窗口 + 像素/状态双通道） | **16/16** | 0 |
| P5 / P6 | 16/16 | 0 |
| PlayJev `playable` @0.5 | **0/16**（画面没变） | 16 |
| Jev `responds_to_input` @0.25（单状态构型） | 14/16 | 2 |
| Jev @0.25（多状态最坏观测） | 13/16（但误报 14/20 修好版） | 3 |

→ **结论不变且更硬**：模型（无论文本还是视觉）都不是判决手段；作为"分诊/复核的第二信号"，
文本侧目前比视觉侧更贴我们的缺陷类型（因为它读得到 `PollInput: false` 这个**状态字段**），
视觉侧的价值在**画面类缺陷**（黑屏、界面缺失）——两者互补，且都必须与 P1..P6 并列记录。

### 7.4 模型判定的语义边界（写进 `playjev.json` 与 `playability_controls.json`）

> 视觉后端只判断**一张整窗帧**："这一帧看起来像不像一个能玩的游戏？"
> 它**不判断**游戏逻辑是否正确、控制是否可发现、是否好玩；它也**看不到**这一帧之前或之后发生了什么。
> 文本后端只判断**一份被裁剪过的状态文本**（不含像素）。
> 二者都是 P1–P6 之外的**第二信号**，永远不是替代品。

---

## 8. `V9` 可重跑命令（逐条，单行 cmd，无重定向）

```cmd
:: 0) 前置：两台服务都在（不重启、不杀）
curl.exe -s http://127.0.0.1:8080/health
curl.exe -s http://127.0.0.1:8081/health
netstat -ano | findstr /R /C:":9911 "        :: 端口 9911 必须空闲（避开 9877/9888/9889/8080/8081）

:: 1) 建/验负面变体（幂等；--verify 追加 --headless --quit-after 60 的退出码）
D:\Anaconda\python.exe projects\_exercises\neg_BUILD_VARIANTS.py --verify

:: 2) 20 款正样本：多状态 Jev + 视觉 PlayJev + 翻转图例探针（约 13.5 min）
D:\Anaconda\python.exe tools\playability_gate.py --all --agent=jev --base-url http://127.0.0.1:8080 --agent-state-budget 2000 --agent-state-samples 3 --visual-agent=playjev --visual-legend-probe --out-root F:\moonbit-hof-rs\godot-mcp\runs\playability\t129-pos --port 9911

:: 3) 4 类声明式负变体（约 3.5 min）—— 帧落在 runs\playability\negatives\<mode>\frames\
D:\Anaconda\python.exe tools\playability_gate.py --exercise neg_input_dead neg_black_screen neg_frozen neg_hud_missing --games neg_input_dead neg_black_screen neg_frozen neg_hud_missing --agent=jev --base-url http://127.0.0.1:8080 --agent-state-budget 2000 --visual-agent=playjev --visual-legend-probe --out-root F:\moonbit-hof-rs\godot-mcp\runs\playability\negatives --port 9911

:: 4) 20 款修复前 export（D-A 的权威负类；约 17 min）
D:\Anaconda\python.exe tools\playability_gate.py --all --agent=jev --base-url http://127.0.0.1:8080 --agent-state-budget 2000 --visual-agent=playjev --visual-legend-probe --exe-root F:\moonbit-hof-rs\godot-mcp\dist\exe-task109-pre-fix --out-root F:\moonbit-hof-rs\godot-mcp\runs\playability\t129-neg-exe --port 9911

:: 5) 视觉阈值标定与冲突矩阵（只读、无网络）
D:\Anaconda\python.exe tools\playjev_visual_calibrate.py --pos-root runs\playability\t129-pos --neg-root runs\playability\negatives --out runs\playability\t129-playjev-fit-declared.json
D:\Anaconda\python.exe tools\playjev_visual_calibrate.py --pos-root runs\playability\t129-pos --neg-root runs\playability\negatives runs\playability\t129-neg-exe --out runs\playability\t129-playjev-fit.json

:: 6) 真实 422 减半重试的探针（真打 8080）
D:\Anaconda\python.exe tools\jev_422_retry_probe.py --base-url http://127.0.0.1:8080

:: 7) 回归 + 单位桥梁 + 像素决定性
D:\Anaconda\python.exe tools\playtest_agent.py --probe-jev
D:\Anaconda\python.exe tools\playtest_agent.py --probe-playjev
D:\Anaconda\python.exe runs\playability\_t129_check_tokens.py
D:\Anaconda\python.exe runs\playability\_t129_frame_identity.py
```

> 环境变量等价写法（注意引号，避免 TASK-128 踩过的尾随空格）：
> `set "PLAYTEST_BASE_URL=http://127.0.0.1:8080"` 后 `--base-url` 可省；
> 视觉侧 `set "PLAYTEST_PLAYJEV_BASE_URL=http://127.0.0.1:8081"` 后 `--playjev-base-url` 可省。
> **`--agent-state-budget` 的单位变了**：`2000`（新）= `800`（TASK-128 旧），见 §2.2。

---

## 9. `V10` 铁律、文件所有权与提交

### 9.1 铁律逐条

| 铁律 | 遵守情况 |
|---|---|
| 1. 禁止一切 shell 重定向 | ✅ 全程无 `>`/`>>`/`*>`/`2>&1`/`> nul`。命令输出直接进终端；所有落盘走工具的 `write_json` / Python `io.open` 句柄。**未出现任何一次违规。** |
| 2. 破坏性命令默认拒绝；不改 20 款正式工程逻辑 | ✅ 未执行任何删除/格式化命令；唯一被删的是门自己的输出目录（`--fresh` 默认行为，`assert_inside` 限定在 `RUNS` 前缀内）。`projects/<game>/` 下 **一个字节未改**（负变体全是拷贝，且构建器逐文件校验 C# 未变并写进 `variant.json`）。 |
| 3. 命令尽量从 cmd 启动；中文防乱码 | ✅ 所有命令由 cmd 启动；报告与 JSON 由 Python UTF-8 句柄写入；`DECISIONS.md` 以文件原有的 CRLF 追加（99/99 行 CRLF）。 |
| 4. 禁止任何第三方端点 | ✅ 全部 HTTP 只发往 `127.0.0.1:8080`（模型）、`127.0.0.1:8081`（模型）、`127.0.0.1:9911`（门自己的游戏进程）。无任何外部请求。 |
| 5. 不得杀 8080/8081、不得动 `/opt/*-venv`、`F:\models\**` | ✅ 未重启/未杀两个服务（`/health` 全程 200）；未写 venv；未写权重目录；未在 `F:\models\**` 下创建任何文件（对比 TASK-128 曾在那里放辅助脚本，本次全部放在 `runs/playability/_t129_*.py`，**`runs/` 不入库**）。 |
| 6. 唯一高位端口，跑前查占用 | ✅ 全程只用 **9911**（跑前 `netstat` 查空；`run_gate` 每次再 `kill_what_holds` 自检）。未使用 9877/9888/9889/8080/8081 作为门端口。 |
| 7. 串行调用模型；429/529 退避计数；注意显存 | ✅ 单任务串行 + 每款内 agent 自带锁串行；三次扫描 **0 次 429/529**、**0 次 OOM**；显存前提（两服务已占 ~17 GB）未触碰（未启动任何新模型进程）。 |
| 8. 改引擎模块才触发重建/十道门/`accept_m1`/push | ✅ **未触发**。依据：本次只改 `godot-mcp/tools/**` 与 `godot-mcp/projects/_exercises/neg_*`，`godot/modules/mcp_server/**` 一个字节未动（`git status` 可证）。 |
| 9. 事实标来源等级；代码与任务书冲突以代码为准并显式纠正 | ✅ 见 §1（7 条更正表）。 |

### 9.2 文件所有权自查（提交前 `git status --short`）

本次**独占清单**内被修改/新建的文件（**只有这些**被暂存）：

```
 M godot-mcp/tools/playability_gate.py              独占
 M godot-mcp/tools/playability_controls.json        独占
 M godot-mcp/tools/playtest_agent.py                独占（§2.A 的 jev 侧修正，见 §1 第 2 条）
?? godot-mcp/tools/playjev_visual_calibrate.py      新（本次标定工具）
?? godot-mcp/tools/jev_422_retry_probe.py           新（本次 422 重试探针）
?? godot-mcp/projects/_exercises/neg_BUILD_VARIANTS.py   新（变体构建器）
?? godot-mcp/projects/_exercises/neg_input_dead/         新（独占 neg_*）
?? godot-mcp/projects/_exercises/neg_black_screen/       新
?? godot-mcp/projects/_exercises/neg_frozen/             新
?? godot-mcp/projects/_exercises/neg_hud_missing/        新
?? godot-mcp/recovery/reports/TASK-129-REPORT.md         本报告
 M DECISIONS.md                                      D168/D169/D170
```
**禁触清单**核查：`dist/**`、`F:\models\**`、`/opt/*-venv`、`recovery/reports/TASK-12{4..8}-REPORT.md`、
`projects/<game>/**`、`godot/modules/**` —— **均未出现在 `git status` 里，也未被写入**。
`runs/**` 全部是运行产物且被 `.gitignore` 忽略（`runs/`），**不入库**。

### 9.3 代提交点名（用户裁定严格单线程后由我收口的、**不是我的产出**的文件）

以下 9 份是**其它任务的遗留未提交文件**。按"严格单线程"下的新裁定由我**代为提交**，
在此逐一点名（**原任务书只要求 TASK-12{4..9}.md；两份 REPORT 是决策者追加的指示**）：

| 文件 | 原作者/任务 | 我的处理 |
|---|---|---|
| `godot-mcp/recovery/tasks/TASK-124.md` … `TASK-129.md`（6 份） | TASK-124…129 的任务书 | 入库（原任务书 §2.E 明确要求） |
| `godot-mcp/recovery/reports/TASK-125-REPORT.md` | TASK-125 子代理 | **代提交**（盘上一直是未跟踪状态） |
| `godot-mcp/recovery/reports/TASK-126-REPORT.md` | TASK-126 子代理 | **代提交** |

**未动**：`godot-mcp/recovery/tasks/README.md` 与 `.gitignore`——按决策者指示归其本人管理
（`f01d23f`/`90ac351`/`5ccbcc3` 已处理），本次 `git status` 里它们也没有改动。

### 9.4 仓库与提交（本机只有**一个**仓）

`godot-mcp\` 不是独立仓库（无 `.git`），它是 `F:\moonbit-hof-rs` 的子目录（与 TASK-128 §8.3 一致）：

```
> git -C F:\moonbit-hof-rs rev-parse --show-toplevel
F:/moonbit-hof-rs
> git -C F:\moonbit-hof-rs log --oneline -5     （提交本任务之前）
5ccbcc3 chore(repo): TASK-125/127 follow-up - weight ignore rules and the parallel-ownership rule
c6138d7 feat(godot-mcp): TASK-127 - deploy PlayJev 0.8B locally ...
a023eaa docs(godot-mcp): TASK-124 - the report (33/33 dumb-service checks, J1-J9 evidence) ...
13cd1d8 feat(godot-mcp): TASK-124 (D166) - add the --agent=jev native NeoHorse-Jev decision backend ...
cc57989 feat(godot-mcp): TASK-128 (D167) - fit the jev playability thresholds ...
```

> 顶部还有两条本次执行前由决策者落下的提交：`90ac351 docs(tasks): require git worktrees…` 与
> `f01d23f docs(tasks): strict single-threading supersedes the worktree plan`（后者推翻前者，即 D169）。

**本任务的提交**：见本报告末尾 §12 的"提交后追记"。

---

## 10. 产物清单

| 类型 | 路径 | 说明 |
|---|---|---|
| 报告 | `recovery/reports/TASK-129-REPORT.md` | 本文件 |
| 代码 | `tools/playability_gate.py` | `--agent-state-samples`、`--visual-agent`、`--exercise`、`agent_aggregate`、`run_visual_agent` |
| 代码 | `tools/playtest_agent.py` | 标定后的 `jev_estimate_tokens` + `shrink_state`/422 重试；PlayJev `playable`/`verdict_invariant_keys`/score 观察值/`legend_flipped` |
| 配置 | `tools/playability_controls.json` | `playjev_thresholds`（新，含 fitted/rejected 证据）、`agent_thresholds.task129_multistate_recheck`、4 个 `neg_*` 能力表 |
| 工具 | `tools/playjev_visual_calibrate.py` | 视觉阈值拟合 + 派生锚点对比 + 冲突矩阵 + jev 多状态重测 |
| 工具 | `tools/jev_422_retry_probe.py` | 真 422 + 减半重试探针 |
| 变体 | `projects/_exercises/neg_BUILD_VARIANTS.py` + `neg_input_dead|neg_black_screen|neg_frozen|neg_hud_missing/` | 声明式负变体（含 `variant.json` 构造与预期） |
| 正样本产物 | `runs/playability/t129-pos/` | 20 款；`agent.json`（3 状态 + 聚合）、`playjev.json`、`gate.json`、`frames/`、`playability.json` |
| 负变体产物 | `runs/playability/negatives/` | 4 款真帧 + `NEGATIVES-INVENTORY.json/.md` + `variants-build.json` |
| 权威负类产物 | `runs/playability/t129-neg-exe/` | 20 款修复前 export |
| 标定 | `runs/playability/t129-playjev-fit.json` / `t129-playjev-fit-declared.json` | 分布 + 扫描 + 锚点 + 冲突矩阵 + jev 多状态 |
| 机制证据 | `runs/playability/t129-frame-identity.json` | **同图同值 22/22**（像素决定性） |
| 重试证据 | `runs/playability/t129-jev-422-retry.json` | 真 422 + 1 次减半重试 + 200 |
| 回归 | `runs/playability/agent-probe-jev.json` / `agent-probe-playjev.json` | 33/33、49/49 |
| 决策记录 | `DECISIONS.md` D168（本任务）、D169（严格单线程）、D170（来源等级） | |
| 只读分析器（不入库） | `runs/playability/_t129_*.py` | token 桥梁核对、帧一致性、清单、报告取数、CRLF 追加 |

---

## 11. 遗留与待决

| # | 事项 | 现状 | 建议 |
|---|---|---|---|
| Q1 | PlayJev `playable` 无分离度，且机制是"只读像素" | 已用真帧证明（§5.5） | 若要让视觉侧有用，需要**会改变的像素**：动画中帧、错误对话框、渲染损坏；或者改用能读状态的模型（像素+状态联合） |
| Q2 | 视觉侧对**界面缺失**（`neg_hud_missing`）是唯一可能有反应的信号，但机检抓不到 | 已构造真帧（22 张），门判 playable | 需要一条**新的机检判据**（例如"README 声明的 HUD/控件节点是否可见"）或把 `playable` 当**人工复核触发** |
| Q3 | Jev `noul_min_p_true=0.25` 只在"注入后单状态"构型下成立 | 已写进 controls（regime + 重测） | 若要跨状态可用，需要一个**按构型**标定的阈值，或用 `playable_frame`（本次多状态下中位 0.63–0.71，比 `responds_to_input` 稳） |
| Q4 | 修复前 export vs 工程树的权威性（breakout/snake/tetris） | 与 TASK-128 一致，并列登记 | 需要人定夺（D-A 说以 export 为权威时，TASK-116 的 19/20 需修订） |
| Q5 | 负类样本仍然偏少（真负 16 款 + 4 声明式） | 三次扫描全部落盘 | 若要概率标定（而不是分离度），需要 ≥ 数百个独立样本；现在不给 ECE 是对的 |
| Q6 | 三个变体各自只渲染出 1 张哈希不同的帧（`neg_input_dead/black/frozen`） | 门如实记 `visual_sample_size=1`，未虚报 | 想要更多视觉样本，需要**会动的**负变体（例如"每 30 帧闪一次黑屏"） |

---

## 12. `V1`–`V10` 逐条对照

| 编号 | 判据 | 结论 | 证据位置 |
|---|---|---|---|
| **V1** | 多状态采样：每款 ≥3 个哈希不同 state，三次调用全留证 | ✅ 20/20 与 4/4 与 20/20 全部 `sample_size 3/3` | §2.1；`t129-pos/<game>/agent.json → observations[]`（label+sha256+裁剪+逐字请求/回答） |
| **V2** | token 估计按 `usage` 标定 + 422 自动减半重试有界（标定数据 + 一次真实重试） | ✅ | §2.2：标定表（1018→2160 / 1791→4229，×2.5）；`t129-jev-422-retry.json`（client 1825 → 真 422 "exceeds 2048 tokens: 2142" → 减半 800 → 200，1 次重试，丢 4 节点点名） |
| **V3** | 四种失效模式变体建好且采到真实整窗退化帧（路径/哈希/预期标签） | ✅ | §3：四条变体表 + `NEGATIVES-INVENTORY.json/.md`；帧目录 `runs/playability/negatives/<mode>/frames/`（80/21/34/22 张） |
| **V4** | 门 PlayJev 路径可用（1 图 + N 问）、score 不在判定路径、`playjev_thresholds` 有 `uncalibrated` 与局限 | ✅ | §4.1；`t129-smoke-final/pong/playjev.json`（`verdict` 只用 `playable`、`score_in_decision_path:false`、`legend_probe.in_decision_path:false`）；`playability_controls.json → playjev_thresholds`（`uncalibrated:true` + 7 条 limitations） |
| **V5** | 20 正样本 + 四类负样本全部跑完 | ✅ **另加** 20 款修复前 export | §4.2 三次扫描表（20 / 4 / 20 全部完成，零错误） |
| **V6** | 用真负面帧标定 `playable`（分布 + 扫描错分 + 与派生锚点对比） | ✅（结论是"无可用阈值"，先验保留） | §5：分布表、扫描表、派生锚点对比表、选定理由、`t129-playjev-fit*.json` |
| **V7** | 翻转图例探针有结果且明确标注不进判定 | ✅ | §6：中位 |Δ| 0.126 / |Δ−mirror| 1.088、`playable` 44/44 不变、`in_decision_path:false` |
| **V8** | 冲突逐条登记（PlayJev vs Jev vs 机检 vs TASK-116），含具体误报/漏报 | ✅ 21 条 | §7：误报 14 款点名、漏报 5 款点名、Jev 漏报 2 款、门 vs 历史 3 款并列；`conflict_matrix.rows` 44 行 |
| **V9** | 可重跑命令（逐条，含环境变量/端口/预算参数） | ✅ | §8（7 组单行 cmd，含端口 9911、`--agent-state-budget 2000` 的单位说明、环境变量等价写法） |
| **V10** | 铁律遵守 + 文件所有权核对（只暂存自己的）+ 任务书已入库 | ✅ | §9（9 条铁律逐条；独占/禁触核查；代提交 9 份遗留文件逐一点名；任务书 TASK-124…129 入库） |

---

## 13. 提交记录（提交后追记）

**本任务的实质提交：`b5ce09d`**

```
feat(godot-mcp): TASK-129 (D168/D169/D170) - wire PlayJev into the gate, sample independent
states, fix the token estimate, add real negative variants
```

提交前用 `git status --short` 逐项核对：**只暂存了 §9.2 列出的独占文件 + §9.3 点名的 9 份遗留文件**
（`git add` 的路径逐个显式给出，未用 `-A` 全量暂存；`git status --short` 显示的 72 条全部是本次
预期的那 72 条，没有多出任何第三方改动）。负变体目录里被 `.gitignore` 的 `.godot/`、`bin/`、`obj/`
没有进入提交（`git add --dry-run` 已确认只加源码/场景/`variant.json`，共 53 个文件）。

提交后：

```
> git -C F:\moonbit-hof-rs status --short
（空 —— 工作区干净）

> git -C F:\moonbit-hof-rs log --oneline -5
b5ce09d feat(godot-mcp): TASK-129 (D168/D169/D170) - wire PlayJev into the gate, sample independent states, fix the token estimate, add real negative variants
f01d23f docs(tasks): strict single-threading supersedes the worktree plan
90ac351 docs(tasks): require git worktrees for concurrent subagents
887640c docs(godot-mcp): TASK-128 - record the final commit id in the report
cc57989 feat(godot-mcp): TASK-128 (D167) - fit the jev playability thresholds on 20 fixed games vs 16 pre-fix negatives, keep uncalibrated=true
```

> 说明：`f01d23f`/`90ac351` 是决策者在本次执行前落下的两条"任务纪律"提交（后者推翻前者的 worktree 方案，
> 即 D169 的来源），**不是我的产出**，我没有改动它们。
