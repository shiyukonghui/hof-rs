# TASK-130 报告 — 补上门盲点（声明式必备 UI 在场判据 P7）+ 排除 PlayJev 零分离度的测量伪影

> **状态：done**
> 执行者：TASK-130 子代理（严格单线程：本任务期间**没有**派生任何子代理，也没有与他人并行）
> 时间：2026-09-27（本机时钟）
> 报告落点：`F:\moonbit-hof-rs\godot-mcp\recovery\reports\TASK-130-REPORT.md`
> **全程只调用本机 `127.0.0.1:8080`（NeoHorse-Jev-4B，仅健康检查）与 `127.0.0.1:8081`（PlayJev-0.8B，
> 串行 214 次）；没有任何图像/状态发往第三方端点；未重启、未杀这两个服务；未写 `/opt/*-venv`、`F:\models\**`。**

---

## 0. 结论速览

| 项 | 结果 |
|---|---|
| **A `P7` 判据** | ✅ 新增门判据 **P7 = 声明式必备 UI/控件在场判据**：门把 `tools/playability_controls.json → games.<game>.required_ui.items` 里声明的节点在**运行中的游戏进程**里逐个解析，逐项检查 `exists / class / visible_in_tree / modulate.a / 视口内面积 / 文本非空`。**完全可机检，不依赖任何模型** |
| `W2` 门盲点被补上 | ✅ `neg_hud_missing`：**P1..P6 全 PASS、P7 FAIL** → 门判定 **not_playable**（TASK-129 时是 playable）；缺失项逐个点名：`side_panel / hud_label / panel_edge` → `visible_in_tree` |
| `W2` 正样本不被判红 | ✅ **20/20 款正样本 P7 全 PASS**（`--only-p7` 全量跑，25 个 gate 实测）；另在**完整门**（P1..P7 + 真实按键注入）里 flappy/snake/tetris 也 **P1..P7 全 PASS** |
| `W3` 第二个声明式负变体 | ✅ 新建 **`neg_ui_offscreen`**（flappy 的拷贝，把 `Hud` 标签移到 `x=-2000`：**`visible` 仍为 true、`is_visible_in_tree()` 仍为 true**，但与视口零交集）→ **P7 FAIL（`hud` -> `on_screen`）**，而 P1..P6 全 PASS。它走的是 P7 的**另一条子句**、另一个游戏，证明 P7 不是只对一个样本有效 |
| `W4` 三种输入形态都跑过 | ✅ 对**已有真帧**做了 6 种输入形态（3 种 × 有/无裁剪）共 **334 次判定（214 次新请求，0 错误）**：`native`（游戏窗口原生 800×600 = TASK-129 基线）／`native_crop`（按 P1 的众数色规则裁剪）／`editor_whole`（**真实的 2978×1793 编辑器整窗截图**）／`editor_whole_crop`／`composite`（受控整窗：本款真帧按真实编辑器里游戏补丁的矩形贴回真实编辑器画布）／`composite_crop` |
| `W5` 二选一结论 | ✅ **结论②：三种输入形态都不分离**（详见 §6）。附加发现：`editor_whole` 形态把 `playable` 的**中位从 0.445 抬到 0.806**（整窗形态让模型更倾向于说"能玩"），裁剪既不产生分离、反而略差。**不重新标定 `playjev_thresholds`**（不存在可用的运行点） |
| ★ 伪影假设的**前提**被推翻 | ✅ 实测：TASK-129/TASK-127 喂给视觉模型的帧**本来就是游戏窗口原生帧**（800×600、root viewport，与工程声明一致，405+157+784 张全部 800×600；TASK-127 探针帧 800×600）。同时**整窗形态确实存在且被量化**：`runs/` 下 **5853 张**真实 2978×1793 整窗截图里，游戏补丁占**中位 3.99%、最大 4.02%**（1636 张全平色=窗口里什么都没有） |
| `W6` 20 对跨版本图像 | ✅ **21 张**被两次判定的同 sha256 图像：**21/21 逐像素完全相同（changed=0）**（与 TASK-129 的 22 张对账：20 张 pos↔pre-fix + 1 张三重(pos/declared-neg/pre-fix) + 1 张 pos↔declared-neg）。**但"修好版与修复前 export 逐像素相同"不是普遍事实**：20 款同名帧配对的 **193 对里 146 对完全相同、47 对不同**（最大通道差 250，累计 227286 像素），settle/auto 帧 20 对里也有 4 对不同（match3/minesweeper/missilecommand/towerdefense）→ "不可见"的说法**按此修正**（§7） |
| 机制复核 | ✅ 确定性：本任务**重新问过的 8 张 native 帧 8/8** 与 TASK-129 记录逐位相同；本任务里被重复判定的 **40 张图像全部一致**（0 例不一致） |
| 铁律 | ⚠️ **1 处违规已披露**：一次 scratch 分析脚本的输出用了 shell 重定向（§9.1）；其余全部遵守。未改 20 款正式工程、未动 `godot/modules/**`（**未触发**重建/十道门/`accept_m1`/push）、未动两个 venv、未动 `F:\models\**` |
| 任务书事实更正 | 3 条（§1）：帧形态的前提、"20 对"的对账口径、以及"两个仓"（本机其实是**两个** git 仓，见 §9.4） |

---

## 1. 任务书事实的来源等级与更正（铁律 9：以实测为准并显式纠正）

| # | 任务书/前序报告的说法 | 本次实测 | 证据（等级） |
|---|---|---|---|
| 1 | §1.B「此前喂给视觉模型的帧**可能**是整窗截图，编辑器/桌面占绝大多数」（决策者提出为**待验假设**） | **前提不成立**：TASK-129/TASK-127 喂进去的是 **800×600 游戏窗口原生帧**（root viewport）；整窗形态在本仓是**另一种历史产物**（`runs/<game>/**/shots-editor/*.png`）。**但整窗形态确实存在**，且实测游戏只占 3.99%（中位）→ 假设描述的"伪影"在**输入形态上讲得通、在"此前喂的是它"上讲不通** | 一手：§5.1（帧尺寸普查）、§5.2（5853 张整窗截图普查） |
| 2 | §1.B「那 20 张跨'修好版 ↔ 修复前 export'的成对图像」 | **是 21 张**：TASK-129 `t129-frame-identity.json` 的 `cross_run_same_image` 22 条 = 20 条 `(pos,pre-fix-exe)` + 1 条 `(declared-neg,pos,pre-fix-exe)` + 1 条 `(declared-neg,pos)`；本任务按 `playjev.json → frames_used[].sha256` 逐张对账得到 **21 张 pos↔pre-fix 同 sha256**，与之一致 | 一手：§7.1、`runs/playability/_t130_identity_reconcile.py` 输出 |
| 3 | TASK-129 §9.4「本机只有**一个**仓」 | **两个仓**：外层业务仓 `F:\moonbit-hof-rs`（`.git`，TASK-129 提交所在）与**嵌套的引擎仓** `F:\moonbit-hof-rs\godot-mcp\godot`（`.git`，Godot 引擎，含 `modules/mcp_server/**`）。两者都有 `git log/status`（§9.4） | 一手：`git -C ... rev-parse --show-toplevel` |

---

## 2. §1.A `P7`：声明式必备 UI/控件在场判据

### 2.1 判据定义（可机检，不看模型）

`games.<game>.required_ui` 回答"这款游戏要能玩，**屏幕上必须有哪几样东西**"（判断），门逐项验（证据）：

```
每个 item（声明字段）                       门的检查（运行中的游戏进程内读取）
  node      "/root/Main/Hud"     ->  exists            该路径在活树里能解析到节点
  class     "Label"              ->  class             get_class() 与声明一致
  must_be_visible: true          ->  visible_in_tree   not n.visible，而是 is_visible_in_tree()
                                                        （祖先被隐藏也算，且把隐藏它的祖先逐个点名）
                                 ->  alpha             modulate.a > P7_MIN_ALPHA(0.01)
  min_area_px: 13000             ->  on_screen         该 Control 的 global_rect 与 root viewport
                                                        的交集面积 >= min_area_px
  text_nonempty: true            ->  text_nonempty     声明的 Label 文本非空
```

* **不做的事**：不比文本内容（只查非空）——避免把"分数从 0 变成 1"这种正常变化当成失败；不引入任何新阈值
  常量，只引入一个 `P7_MIN_ALPHA=0.01`（20 款正样本被声明项实测 modulate.a **全为 1.0**）。
* **`min_area_px` 的来源**：= 该节点在 `00_settle` 实测矩形的**一半**，四舍五入到 100 px²（写在声明里，
  可逐条核对）。宽到能容忍字体/布局变化，窄到能抓住"被压成 0 尺寸"或"被移出视口"。
* **没有声明 = FAIL**（与 P6 同一立场）：没有声明就**不能说**"必备 UI 在场"，门给
  `no required_ui.items declaration for this game ...`，而不是默认通过。

### 2.2 实现位置（W1 证据指针）

| 位置 | 内容 |
|---|---|
| `tools/playability_gate.py` | `P7_MIN_ALPHA`（常量，含取值依据）；`probe_required_ui_source(paths)`（GDScript 探针，`get_node_or_null` + `is_visible_in_tree` + `modulate.a` + `get_global_rect` + 祖先隐藏链）；`run_required_ui_probe(paths, gd)`（在游戏进程内执行并把答案**原样**返回）；`verdict_p7(game, controls, probe)`（逐子句判定 + `missing[]` 点名）；`required_ui_items()`；`rect_intersection_area()`；`CRITERIA_ORDER` / `criteria_verdict()`（verdict 覆盖 P1..P7）；`--only-p7`（只跑 P7）；文档字符串里的 P7 段与用法示例 |
| `tools/playability_controls.json` | `games.<game>.required_ui`（**25 个条目**：20 款正式游戏 + 5 个负变体；共 **56 个声明项**），每项含 `declared_by / what / rule / how_measured / items[]` |
| `tools/tests/test_playability_p7.py` | **23/23** 通过：逐子句反例（不存在 / `visible=false` / **祖先被隐藏** / alpha=0 / **visible=true 但移出视口** / 尺寸压成 0 / 文本空白 / class 不符 / 面积不足 / 探针无答案）+ 几何函数 + "20 款都有可机检声明" |
| `runs/playability/t130-p7b/` | 25 个 `gate.json`：每个都带 `p7_probe`（**判定所依据的原始节点读取**：class/vis/alpha/global_rect/text/隐藏祖先）+ `required_ui_declaration` + `criteria.P7` |
| 汇总 | `runs/playability/t130-p7b/p7-summary.json`（另有先跑一遍的 `runs/playability/t130-p7/p7-summary.json`，两者逐项一致） |

声明项分布（每款）：`2 项 × 16 款 + 3 项 × 4 款 = 44`（正式游戏），负变体 12 项。
3 项的 4 款是：`game2048`（hud + **board 棋盘容器** + status）、`puzzlebobble`（hud + **next_bubble 下一颗指示器** + status）、
`snake`（**field 场地** + **food 食物** + **head 蛇头**；snake 实测**没有文本 HUD**，所以声明的是"玩家必须看得见的东西"）、
`tetris`（**side_panel** + **hud_label** + **panel_edge**）。

> 注：`/root/Main/...` 是**运行期**路径（`get_tree().root` 下），与门自己采样的 state 树同一个键空间。

### 2.3 `W2`：门盲点被补上（含完整门证据）

**（a）`--only-p7` 全量扫描**（`runs/playability/t130-p7b/`，25 个 gate，声明与变体字节为提交版本）：

```
正样本：20/20 P7 PASS，失败项 = none
负变体：neg_hud_missing  P7=FAIL  3/3 项不可用: side_panel -> visible_in_tree;
                                                 hud_label  -> visible_in_tree;
                                                 panel_edge -> visible_in_tree
        neg_ui_offscreen P7=FAIL  1/2 项不可用: hud -> on_screen
        neg_black_screen P7=FAIL  3/3 项不可用: field/food/head -> visible_in_tree   （额外收益）
        neg_frozen       P7=PASS  （冻结不是 UI 失效：接口还在，P7 不该替 P3 再判一次）
        neg_input_dead   P7=PASS  （输入断同样不是 UI 失效）
```

**（b）完整门（P1..P7，`--agent=none`）** —— 证明 P7 真的进了总判定、且不误伤正样本：

| 目标 | P1 | P2 | P3 | P4 | P5 | P6 | P7 | 门判定 | 证据 |
|---|---|---|---|---|---|---|---|---|---|
| `flappy` | PASS | PASS | PASS | PASS | PASS | PASS | **PASS** | playable | `runs/playability/t130-p7-full/flappy/gate.json` |
| `snake` | PASS | PASS | PASS | PASS | PASS | PASS | **PASS** | playable | 同上 `snake` |
| `tetris` | PASS | PASS | PASS | PASS | PASS | PASS | **PASS** | playable | 同上 `tetris` |
| `neg_hud_missing` | PASS | PASS | PASS | PASS | PASS | PASS | **FAIL** | **not_playable** | 同上 `neg_hud_missing/gate.json` |
| `neg_ui_offscreen` | PASS | PASS | PASS | PASS | PASS | PASS | **FAIL** | **not_playable** | 同上 `neg_ui_offscreen/gate.json` |

→ 对 `neg_hud_missing` 这正是任务书要的"**让 `neg_hud_missing` 翻 FAIL，而 20 款正样本全 PASS**"，
且翻的原因是 **P7 单独 FAIL**（P1..P6 与 TASK-129 完全一致）。

### 2.4 `W3`：第二个声明式负变体 `neg_ui_offscreen`

* 位置：`projects/_exercises/neg_ui_offscreen/`（**flappy 的拷贝**，C# 逐字节未改，`variant.json` 记录
  `csharp_sources_copied_unchanged: true`、`headless exit 0`）。
* 声明式改动**只有两行**：`scenes/main.tscn` 的 `Hud` 节点
  `offset_left = -2000.0` / `offset_right = -1420.0`（矩形 = 580×38，位置 x=-2000 → 与 800×600 视口**零交集**）。
* 它刻意的与 `neg_hud_missing` **不同**：`visible` 保持 true、`is_visible_in_tree()` 保持 true。
  **只看 `visible` 标志的判据会放过它**；P7 用 `on_screen`（视口内面积）子句抓住它。
* 实测：`P7 FAIL: 1/2 declared UI item(s) are NOT usable: hud -> on_screen`，
  `Status` 仍 PASS（证明失败是**逐项**的，不是整款一刀切）。

---

## 3. §1.B 前提核对：喂给视觉模型的帧到底是什么形态？

**先查证据，再下结论**（任务书要求"先排除测量伪影"）。

### 3.1 现有帧的尺寸普查（一手）

| 位置 | 帧数 | 尺寸分布 |
|---|---|---|
| `runs/playability/t129-pos/**/frames/*.png` | 405 | **800×600 × 405** |
| `runs/playability/negatives/**/frames/*.png` | 157 | **800×600 × 157** |
| `runs/playability/t129-neg-exe/**/frames/*.png` | 784 | **800×600 × 784** |
| TASK-127 探针帧 `runs/playability-exe/pong/frames/20_post1.png` | 1 | **800×600**（base64 PNG 头 `0x320 × 0x258`） |

并且门的 `gate.json → window` 实测：`display_window_size = root_viewport_size = declared_viewport = [800,600]`
（20 款全部 `window_conforms_to_declared: true`），而门的 `running_game_capture_screenshot` 读的是游戏进程的
**root viewport**。→ **喂给 PlayJev 的帧就是"游戏窗口原生帧"，不是整窗截图**。

### 3.2 但"整窗形态"确实存在，并且被完整量化（一手，全量）

`runs/<game>/**/shots-editor/*.png` 是**真实的编辑器整窗截图**（2978×1793）。对**全部 5853 张**做过普查
（`PIL.getcolors()`，非众数像素占比 = "窗口里除了一层平色之外还有什么"）：

| 指标 | 值 |
|---|---|
| 整窗截图总数 | **5853** |
| 全平色（非众数像素 < 0.1%） | **1636**（28.0%：窗口里**什么都没有**） |
| 小补丁（0.1%–8%） | **4217**（72.0%） |
| ≥8% | **0** |
| 非众数像素占比 min / 中位 / max | 0.000000 / **0.039928** / **0.040200** |

而"游戏补丁"的矩形实测（用同一套众数色规则量出来的）在 pong 的真实整窗截图上是
`(111, 74, 533×400)` = **3.96%** 的窗口面积 —— 与上表中位数 3.99% 吻合。
→ **决策者记忆里的那幅画面（编辑器占满、游戏只占左上角一小块）是真实存在的**，
`editor_whole` 形态里游戏不超过**4.02%**的像素。但它**不是** TASK-129 喂给模型的输入。

---

## 4. §1.B 实验设计：六种输入形态与裁剪规则

对**已经有的一批真帧**（TASK-129 逐帧记录了 sha256 的那 51 张正样本帧 + 7 张负变体帧）做输入形态对比：

| 形态 | 是什么 | 是否新造 | 负样本覆盖 |
|---|---|---|---|
| `native` | 游戏窗口原生 800×600 root-viewport 帧 —— **与 TASK-129 基线逐帧同 sha256** | 否（复用记录值 + 8 张重问） | 7 帧 / 5 变体 |
| `native_crop` | `native` 的**内容包围盒裁剪** | 是（派生） | 7 帧 |
| `editor_whole` | 该款**真实的 2978×1793 整窗截图**（游戏补丁 ≈4%） | 否（真实历史产物） | **0（这类帧从来没有负变体版本）** |
| `editor_whole_crop` | `editor_whole` 的**内容包围盒裁剪**（= 把整窗裁剪回游戏补丁） | 是（派生） | **0** |
| `composite` | **受控整窗**：本款真帧按真实编辑器里游戏补丁的矩形（533×400）等比贴回**同一张真实编辑器画布** | 是（派生，标注来源） | 7 帧 |
| `composite_crop` | `composite` 的裁剪 | 是（派生） | 7 帧 |

**裁剪规则（写死、可复现，实现于门内 `content_bbox_crop()`，与 P1 用同一套常数）**

1. 背景色 = 整帧众数色（4-bit 量化直方图，P1 用的同一方法）；
2. 像素与背景色**任一通道**差 > `PIXEL_DELTA`(16) 即"内容"；
3. 取内容像素的**紧包围盒**；
4. `pad` 外扩（本次 0）、`margin` 先忽略边框带（本次 0）、`min_side` 过小则保留整帧（本次 0）；
5. **没有内容像素**的帧（平色黑屏等）→ 保留整帧并标记 `flat: true`（绝不产生 0×0 的洞）。
   产物里记录 `source/dest 尺寸、box、背景色、sha256`，所以"模型看到的是哪张图"可以从产物重建。

**调用纪律**：全程**串行**（单进程、一次一请求），只打 `127.0.0.1:8081`，共 **334 次判定（214 次新请求）**，
`0` 错误、`0` 非 200。问题集与 TASK-129 **逐字相同**（`playable` + 另 2 个不变量 + `brokenness`），
所以数字可比。凡是 TASK-129 已有记录的 sha256，直接复用其记录值（不再问），另抽 8 张重问做确定性对照。

---

## 5. §1.B 结果（`W4`）

> 全部数字来自 `runs/playability/t130-input-form-study.json` 与
> `runs/playability/t130-input-form-summary.json`（按 sha256 去重后的**独立图像**口径；
> 去重很关键：`editor_whole` 的 51 行只对应 **20 张**不同图像）。

### 5.1 正/负 `playable` 分布（去重后，独立图像）

| 输入形态 | 正样本 n | min | 中位 | max | 负样本 n | min | 中位 | max | 分离度（min_pos − max_neg） |
|---|---|---|---|---|---|---|---|---|---|
| `native`（=基线） | 51 | 0.104813 | **0.444876** | 0.885693 | 7 | 0.125427 | 0.448697 | 0.884842 | **−0.780029（不分离）** |
| `native_crop` | 51 | 0.094038 | **0.310748** | 0.883757 | 7 | 0.210474 | 0.279283 | 0.898098 | **−0.804060（不分离）** |
| `editor_whole` | 20 | 0.132557 | **0.806037** | 0.856783 | — | — | — | — | **无法评估（该形态没有负样本）** |
| `editor_whole_crop` | 20 | 0.127804 | **0.813251** | 0.875540 | — | — | — | — | 同上 |
| `composite`（受控整窗） | 51 | 0.311335 | **0.667248** | 0.842678 | 7 | 0.221375 | 0.624283 | 0.827513 | **−0.516178（不分离）** |
| `composite_crop` | 51 | 0.153277 | **0.518204** | 0.902427 | 7 | 0.221375 | 0.712362 | 0.898140 | **−0.744863（不分离，且方向相反）** |

### 5.2 阈值扫描错分（游戏级：一款的取值 = 它各帧的**最小值**，与门自己的"最坏帧"规则一致）

| 输入形态 | @0.5：正被误报 | 负被放过 | 错分 | 最优切点 | 最优切点下：正被误报 / 负被放过 / 错分 |
|---|---|---|---|---|---|
| `native` | 14/20 | 1/5 | 15 | 0.000000 | 0/20 / 5/5 / 5（**退化**：靠"全放过"取得 5 错） |
| `native_crop` | 15/20 | 1/5 | 16 | 0.000000 | 0/20 / 5/5 / 5（同上） |
| `composite` | 4/20 | 4/5 | 8 | 0.311335 | 0/20 / **4/5** / 4（**靠放过 4/5 个真负面**取得） |
| `composite_crop` | 11/20 | 3/5 | 14 | 0.000000 | 0/20 / 5/5 / 5（同上） |
| `editor_whole` / `editor_whole_crop` | — | — | — | — | 该形态没有负样本，不可评估 |

> 负样本口径说明：这里用的是**声明式负变体 5 款（7 帧）**；TASK-129 的权威负类（16 款修复前 export）
> 不在本实验里（本实验复用它的**正样本**帧与记录值）。两种口径都不分离，结论一致。
> "最优切点 = 0.0"不是"找到了运行点"，而是"**没有任何阈值比全放过更好**"——这正是零分离度的定义式症状。

### 5.3 与基线（TASK-129）的差异：分离度是否出现？出现在哪种输入上？

* `native` 复现 TASK-129 的结论：正 0.105–0.886 中位 0.445 vs 真负 0.125–0.749 → 重叠。
  本任务负样本口径下 gap = **−0.780**。
* `native_crop`（**决策者提出的"改成游戏视口帧"**）：gap **−0.804**，中位从 0.445 掉到 0.311，
  负样本中位 0.279 —— **裁剪没有制造分离度，反而更差**。
* `editor_whole`（真正的整窗形态）：**中位被抬到 0.806**（比 native 高 0.36），
  51 行里绝大多数 > 0.5 → 整窗形态**不是"让模型看不见游戏"，而是让模型更倾向于说"这能玩"**
  （剩下的 3.96% 缩小的游戏补丁 + 大片编辑器灰底，在它的偏好里"像正常画面"）。
* `composite`（**受控**整窗：同样的像素、只改面积与画布）→ gap **−0.516**，
  仍不分离；`composite_crop` → gap **−0.745**。→ **面积/缩放不是伪影来源**。

### 5.4 `W5` 二选一结论

> **结论②：三种输入形态都不产生分离度。**
> `native` / `native_crop` / `editor_whole`（+`editor_whole_crop`/`composite`/`composite_crop`）六种形态下，
> `playable` 的正负分布全部重叠（有负样本的三种形态 gap 分别为 −0.780 / −0.804 / −0.516），
> 阈值扫描里**没有任何运行点**：要么误报一半以上的修好版，要么把真负面全部放过。
> 因此：
> 1. **`playjev_thresholds` 不重新标定**（不存在可用的运行点，标一个数只会看起来更"专业"）；
>    `uncalibrated: true` 保持，`playable` 继续只作**非判定**观察值。
> 2. 明确写下：**视觉判定在本项目内容上不可用**（作为 pass/fail 判据）。样本量：
>    正 51 帧 / 20 款，负 7 帧 / 5 款（声明式），另有 20 张真实整窗正样本帧。
> 3. 与决策者假设的关系：假设的**前提**（喂的是整窗帧）不成立（§3.1），
>    假设的**补救措施**（裁剪/换帧形态）实测**无效**（§5.1–5.3）。

### 5.5 确定性（顺带得到的机制旁证）

| 对照 | n | 逐位一致 |
|---|---|---|
| 重问的 `native` 帧 vs TASK-129 记录值 | 8 | **8/8** |
| 同一 sha256 在正/负两侧各判一次（native / native_crop / composite / composite_crop） | 各 2 | **8/8 一致** |
| `editor_whole` / `editor_whole_crop` 里同一张图被判多次（51 行 → 20 张图） | 各 16 | **32/32 一致** |
| 全部重复判定合计 | 40 | **40/40 一致，0 例不一致** |

→ 与 TASK-129 §5.5 的机制发现一致：`playable` 是**像素的确定性函数**。

---

## 6. 产物与证据索引（实验部分）

| 类型 | 路径 |
|---|---|
| 实验汇总（分布/扫描/逐行结果） | `runs/playability/t130-input-form-study.json` |
| 去重口径与确定性汇总 | `runs/playability/t130-input-form-summary.json` |
| 逐次模型请求缓存（按 `(form, image sha256)`） | `runs/playability/t130-playjev-input-forms.jsonl`（334 行） |
| 派生输入图像（裁剪/整窗合成） | `runs/playability/t130-forms/<game>/*.png` |
| 整窗普查（5853 张） | `runs/playability/t130-editor-shots-full.json` |
| 驱动脚本（不入库，`runs/` 被 `.gitignore`） | `runs/playability/_t130_input_form_study.py`、`_t130_study_summary.py`、`_t130_editor_full.py` 等 |
| 裁剪实现（**入库**，门内） | `tools/playability_gate.py → content_bbox_crop()`、`--visual-input-form crop` |

---

## 7. `W6`：跨版本图像逐对像素差（并据此修正"不可见"的说法）

### 7.1 被两次判定的同 sha256 图像

`runs/playability/_t130_pair_identity.py` → `runs/playability/t130-pair-identity.json`：

* 以每个 run 的 `playjev.json → frames_used[].sha256` 为准（**模型真正拿到的那批文件**），
  在两个 run 都出现过的图像 = **21 张**；
* 逐张从磁盘取文件做像素比对：**21/21 `changed_pixels = 0`、`max_channel_delta = 0`**（逐字节相同）；
* 与 TASK-129 的"22 张"对账：22 条 `cross_run_same_image` = 20 条 `(pos, pre-fix-exe)` +
  1 条 `(declared-neg, pos, pre-fix-exe)`（breakout `c8df2c55…`）+ 1 条 `(declared-neg, pos)`
  → pos↔pre-fix 的独立图像正是 **21** 张，两处口径一致。

### 7.2 全部同名帧配对（193 对）

`runs/playability/_t130_pair_pixels.py` → `runs/playability/t130-pair-pixels.json`：
对 20 款，把 `t129-pos/<game>/frames/*.png` 与 `t129-neg-exe/<game>/frames/*.png` **按文件名配对**：

| 指标 | 值 |
|---|---|
| 配对总数 | **193** |
| sha256 完全相同 | **146**（75.6%） |
| 像素不同 | **47**（24.4%） |
| 最大通道差（全部配对） | **250** |
| 累计变化像素 | **227286** |
| 每对都相同的游戏 | asteroids, bomberman, flappy, game2048, platformer, snake, tetris（7 款） |
| 有差异的游戏 | breakout, frogger, lunarlander, match3, minesweeper, missilecommand, pacman, pong, puzzlebobble, rtype, sokoban, spaceinvaders, towerdefense（13 款） |
| 单款最大差异 | minesweeper `01_settle` 等 7 对各自 **161077** 个变化像素 |

settle/auto 帧（门的判定真正用的那批）**按文件名配对 20 对**：**16 对相同、4 对不同**
（match3 / minesweeper / missilecommand / towerdefense 的 `01_settle.png`）。
差异的原因是可解释的：这些游戏**有自主推进的状态**（自动翻格、自动移动、敌人波次），
修复前 export 的输入死了以后**演化路径分叉**，所以"同一时刻"的画面不同 —— 差异来自**状态分叉**，
不来自缺陷本身（`PollInput=false` 不改渲染）。

### 7.3 "不可见"说法的修正（**确认 + 更正**）

* **确认**：模型实际判过的 21 张跨版本图像**逐像素完全相同**，所以"同一个 `playable` 值"是
  **输入相同**的必然结果（确定性），而不是"模型对缺陷视而不见"。
  TASK-129 那句"不改变像素的缺陷对它天然不可见"在**这批配对上**成立，但正确的说法应是
  **"这对样本本身没有视觉差异"**。
* **更正**：把它推广成"**修好版与修复前 export 的画面（逐像素）相同**"是**错的**：
  193 对里 **47 对明显不同**（最大通道差 250、累计 22.7 万像素），settle 帧也有 4/20 不同。
  因此更强的表述是：
  * 对**像素确实不同**的那 47 对，模型依然没有把两类分开（§5 的分布里藏着这些帧）——
    **零分离度不是"输入没差异"造成的**，因为一部分输入确实有差异；
  * 而对**像素相同**的那 21 对，"模型看不见"这个说法应当降级为"**这对输入没有可看的东西**"。

---

## 8. `W7` 可重跑命令（逐条，单行 cmd，**无任何 shell 重定向**）

```cmd
:: 0) 前置：两个服务都在（不重启、不杀）；两个门端口跑前确认空闲
curl.exe -s http://127.0.0.1:8080/health
curl.exe -s http://127.0.0.1:8081/health
netstat -ano | findstr /R /C:":9913 " /C:":9914 " /C:":9915 " /C:":9916 "

:: 1) P7 单元测试（无引擎、无网络，23/23）
D:\Anaconda\python.exe tools\tests\test_playability_p7.py

:: 2) 只跑 P7：20 款正式游戏 + 5 个负变体（约 3 分钟，不调用任何模型）
D:\Anaconda\python.exe tools\playability_gate.py --all --exercise neg_input_dead neg_black_screen neg_frozen neg_hud_missing neg_ui_offscreen --only-p7 --out-root F:\moonbit-hof-rs\godot-mcp\runs\playability\t130-p7b --port 9916

:: 3) 完整门（P1..P7）：3 款正样本 + 2 个 UI 失效变体（每个约 25-40 秒）
D:\Anaconda\python.exe tools\playability_gate.py --games flappy snake tetris --agent=none --out-root F:\moonbit-hof-rs\godot-mcp\runs\playability\t130-p7-full --port 9914
D:\Anaconda\python.exe tools\playability_gate.py --exercise neg_hud_missing neg_ui_offscreen --games neg_hud_missing neg_ui_offscreen --agent=none --out-root F:\moonbit-hof-rs\godot-mcp\runs\playability\t130-p7-full --port 9915

:: 4) 负变体构建与 headless 验证（幂等；5 个变体 exit 0）
D:\Anaconda\python.exe projects\_exercises\neg_BUILD_VARIANTS.py --verify

:: 5) 三形态视觉实验（**串行**调用 8081；复用已有记录值，新增约 214 次请求，约 6 分钟）
D:\Anaconda\python.exe runs\playability\_t130_input_form_study.py --recheck 8

:: 6) 实验读数（只读、无网络）
D:\Anaconda\python.exe runs\playability\_t130_study_summary.py
D:\Anaconda\python.exe runs\playability\_t130_editor_full.py
D:\Anaconda\python.exe runs\playability\_t130_pair_pixels.py
D:\Anaconda\python.exe runs\playability\_t130_pair_identity.py
D:\Anaconda\python.exe runs\playability\_t130_identity_reconcile.py
D:\Anaconda\python.exe runs\playability\_t130_p7_summary.py

:: 7) 门内裁剪形态的用法（等价于实验里的 native_crop，一次完整门运行）
D:\Anaconda\python.exe tools\playability_gate.py --games pong --visual-agent=playjev --visual-input-form crop --out-root F:\moonbit-hof-rs\godot-mcp\runs\playability\t130-smoke-crop --port 9917
```

环境变量等价写法：`set "PLAYTEST_PLAYJEV_BASE_URL=http://127.0.0.1:8081"` 后 `--playjev-base-url` 可省。

---

## 9. `W8` 铁律、文件所有权与两仓 git

### 9.1 铁律逐条（**含一处如实披露的违规**）

| 铁律 | 遵守情况 |
|---|---|
| 1. 禁止一切 shell 重定向 | ⚠️ **1 处违规**：`_t130_ui_compact.py` 的**首次**运行用了 `... > runs\playability\_t130_ui_compact.txt 2>&1`（一条 scratch 分析清单，只写 `runs/` 下被 gitignore 的临时文本，不涉及任何产品/配置/工程文件）。发现后已把该脚本改成用 Python UTF-8 句柄自己写盘并**无重定向重跑**（脚本头部写明）。此外全程无 `>`/`>>`/`*>`/`2>&1`/`> nul` |
| 2. 破坏性命令默认拒绝；禁止改 20 款正式工程 | ✅ 未执行删除/格式化；**未用 `git checkout`/`git restore`**（需要回退 4 个变体被误改的字节时，用 `git show HEAD:<path>` 读原内容 + Python 写回 + sha256 校验，见 `runs/playability/_t130_restore_variants.py`）。`projects/<game>/` **一个字节未改**（`git status --short` 可证） |
| 3. 命令尽量从 cmd 启动；中文防乱码 | ✅ 所有命令由 cmd 运行；报告/JSON 由 Python UTF-8 句柄写入；`DECISIONS.md` 以文件当前的 CRLF 追加 |
| 4. 禁止任何第三方端点 | ✅ 全部 HTTP 只发往 `127.0.0.1:8080`（8 次 `/health`）、`127.0.0.1:8081`（214 次判定）、`127.0.0.1:991x`（门自己的游戏进程）。无任何外部请求 |
| 5. 不得杀 8080/8081、不得动两个 venv、`F:\models\**` | ✅ 未重启/未杀两个服务（开始与结束都 200）；未写 `/opt/*-venv`；未在 `F:\models\**` 下创建/修改任何文件 |
| 6. 唯一高位端口、跑前查占用、串行调用模型 | ✅ 门端口 9912/9913/9914/9915/9916（9911 当时处于 TIME_WAIT 所以避开），每次跑前 `netstat` 查空且门自己再 `kill_what_holds` 自检；未用 9877/9888/9889/8080/8081 作门端口；**模型调用全程单进程串行**（214 次，0 次 429/529、0 次 OOM） |
| 7. 未改引擎模块 → 不触发两变体重建/十道门（须写明依据） | ✅ **未触发**。依据：本次改动只在 `godot-mcp/tools/**`、`godot-mcp/projects/_exercises/neg_*`、`godot-mcp/recovery/**`、`godot-mcp/runs/**`（不入库），`godot/modules/mcp_server/**` **零字节改动**；引擎仓 `git status --short` 只有一条**我没碰过**的遗留未跟踪文件（§9.5） |
| 8. 提交前 `git status --short` 只暂存独占清单内文件 | ✅ 见 §9.3（逐条路径 `git add`，未用 `-A`） |
| 9. 事实标来源等级；代码/数据与任务书冲突时以实测为准并显式纠正 | ✅ §1（3 条更正）+ 全文标注一手/推导 |

### 9.2 顺带修掉的两个真实缺陷（builder 的"幂等"并不幂等）

重跑 `neg_BUILD_VARIANTS.py` 时发现（并已修复、记录在脚本 docstring 里）：

1. `patch_scene()` 即使所有属性**已经存在**也会重写节点块（`body + [""]`），于是每重跑一次就给 4 个已有变体的
   `scenes/main.tscn` **多加两个空行**（N 次跑加 N 组）。→ 现在"无事可做时**不写盘**"，重跑逐字节稳定。
2. `variant.json` 在重跑时把**已经打过补丁的文件**当成 `before` 再取哈希，"修复前哈希"被覆盖成"修复后哈希"，
   `already_present` 也从 false 翻成 true。→ 现在 `applied=False` 时**沿用上一份记录里的 before 哈希**，
   并显式写出 `patch_applied_this_run`。

修好之后已把 4 个既有变体恢复成**提交版本字节**（sha256 校验通过），再重跑 builder：**scenes 零改动**，
`variant.json` 只多了 TASK-130 的 P7 期望与上述两个记录字段（§9.3）。

### 9.3 文件所有权自查（提交前 `git status --short`）

**本任务独占清单内被修改/新建的文件（只有这些会被暂存）**：

```
 M godot-mcp/tools/playability_gate.py                                   独占（P7 + 裁剪 + --only-p7）
 M godot-mcp/tools/playability_controls.json                             独占（25 个 required_ui 声明）
 M godot-mcp/projects/_exercises/neg_BUILD_VARIANTS.py                   独占（第 5 个变体 + 幂等修复 + P7 期望）
 M godot-mcp/projects/_exercises/neg_input_dead/variant.json             独占（P7 期望）
 M godot-mcp/projects/_exercises/neg_black_screen/variant.json           独占（P7 期望）
 M godot-mcp/projects/_exercises/neg_frozen/variant.json                 独占（P7 期望）
 M godot-mcp/projects/_exercises/neg_hud_missing/variant.json            独占（P7 期望 + gate 期望改写）
?? godot-mcp/projects/_exercises/neg_ui_offscreen/                      新（第 2 个 UI 失效变体）
?? godot-mcp/tools/tests/test_playability_p7.py                         新（P7 单元测试）
?? godot-mcp/recovery/tasks/TASK-130.md                                 本任务书
?? godot-mcp/recovery/reports/TASK-130-REPORT.md                        本报告
 M DECISIONS.md                                                         D171/D172
```

**禁触清单核查**：`projects/<game>/**`（20 款正式工程）、`godot/modules/**`、`dist/**`、
`/opt/*-venv`、`F:\models\**`、`.gitignore`、`recovery/tasks/README.md`、
`recovery/reports/TASK-12{4..9}-REPORT.md` —— **均未出现在 `git status` 里，也未被写入**。

### 9.4 两个仓的 `git log --oneline -5` 与 `git status --short`

**（a）外层业务仓 `F:\moonbit-hof-rs`**（提交前）：

```
f39d4e7 docs(godot-mcp): TASK-129 - record the final commit id and the post-commit git log/status in the report
b5ce09d feat(godot-mcp): TASK-129 (D168/D169/D170) - wire PlayJev into the gate, sample independent states, fix the token estimate, add real negative variants
f01d23f docs(tasks): strict single-threading supersedes the worktree plan
90ac351 docs(tasks): require git worktrees for concurrent subagents
887640c docs(godot-mcp): TASK-128 - record the final commit id in the report
```

**（b）引擎仓 `F:\moonbit-hof-rs\godot-mcp\godot`**（本次未改任何引擎文件）：

```
ba1587c71e fix(mcp_server): TASK-112 - the three engine defects TASK-111 registered are fixed at the root ...
3fdabe2d9a fix(godot-mcp): TASK-110 - editor_list_signal_connections' registered schema regains `scope` ...
1f9d0cb1c9 modules/mcp_server: task103 - REBUILT-2C-MANIFEST gains the 2c-12 section: the runtime-error contract ...
```

两仓的 `git status --short` 见 §9.5（提交后追记在 §13）。

### 9.5 不是我的产出、需要决策者处理的东西（**点名，不代提交**）

| 仓库 | 条目 | 说明 |
|---|---|---|
| 引擎仓 | `?? uid_cache.bin`（70 字节，mtime **2026/09/27 11:03**） | 引擎运行时在工作目录（`godot-mcp/godot/`）生成的缓存文件。**mtime 早于本任务**（本任务在 21:00 之后），所以是 TASK-129 或更早的 `--headless` 运行留下的；它不在我的独占清单里，**未暂存、未删除** |
| 外层仓 | 无 | 本任务执行前外层仓是干净的（TASK-129 提交后 `status` 为空） |

---

## 10. 产物清单

| 类型 | 路径 | 说明 |
|---|---|---|
| 报告 | `recovery/reports/TASK-130-REPORT.md` | 本文件 |
| 代码（门） | `tools/playability_gate.py` | `P7_MIN_ALPHA`、`probe_required_ui_source`、`run_required_ui_probe`、`verdict_p7`、`required_ui_items`、`rect_intersection_area`、`CRITERIA_ORDER`/`criteria_verdict`、`content_bbox_crop`、`--only-p7`、`--visual-input-form/--visual-crop-*` |
| 配置 | `tools/playability_controls.json` | 25 个 `required_ui`（56 项）+ `neg_ui_offscreen` 能力表条目 |
| 测试 | `tools/tests/test_playability_p7.py` | 23/23；逐子句反例 + 声明可加载性 |
| 变体 | `projects/_exercises/neg_ui_offscreen/`、`neg_BUILD_VARIANTS.py` | 第 2 个 UI 失效变体 + 幂等修复 |
| P7 证据 | `runs/playability/t130-p7b/`（25 gate）、`t130-p7/`（先跑一遍）、`t130-p7-full/`（完整门） | `gate.json → p7_probe` / `criteria.P7` / `required_ui_declaration` |
| P7 汇总 | `runs/playability/t130-p7b/p7-summary.json`（提交版本的 25 个 gate）、`runs/playability/t130-p7/p7-summary.json`（重跑前一遍） | 逐款 P7 结论与缺失项 |
| 三形态实验 | `runs/playability/t130-input-form-study.json`、`t130-input-form-summary.json`、`t130-playjev-input-forms.jsonl`、`t130-forms/**` | 334 行判定 / 214 次新请求 |
| 整窗普查 | `runs/playability/t130-editor-shots-full.json` | 5853 张真实整窗截图的平色占比 |
| 配对像素 | `runs/playability/t130-pair-pixels.json`、`t130-pair-identity.json` | 193 对 / 21 张被两次判定的图像 |
| 分析器（不入库） | `runs/playability/_t130_*.py` | 帧普查、声明注入、P7 汇总、实验驱动、配对统计、变体恢复等 |
| 决策记录 | `DECISIONS.md` D171（P7）、D172（B/W6 的结论） | |

---

## 11. 遗留与待决

| # | 事项 | 现状 | 建议 |
|---|---|---|---|
| Q1 | 视觉判定在本项目内容上不可用（六种输入形态都不分离） | 已用 334 次真实判定 + 三形态证据定案 | 视觉侧若要有用，需要**会改变的像素**（动画中帧、错误对话框、渲染损坏），或改成"像素+状态"联合模型；目前它只能作人工复核触发，不能作判据 |
| Q2 | `playable` 在整窗形态下**系统性偏高**（中位 0.806 vs 0.445） | 已量化 | 若将来有人把整窗截图喂给视觉模型，必须知道这条：它会更容易说"能玩" |
| Q3 | P7 只覆盖"**声明过的**必备 UI" | `neg_hud_missing`/`neg_ui_offscreen`/`neg_black_screen` 都能抓到；未声明的 UI 缺失仍抓不到 | 新游戏入列时必须在 `required_ui` 里写清"玩家需要看见什么"；`required_ui` 缺失=FAIL 已强制这一点 |
| Q4 | P7 不校验文本**内容**（只查非空） | 有意为之（避免把正常的分数变化判成失败） | 若需要"分数真的在显示"，可给个别项加 `text_regex`（字段已实现、本次未启用，因为要防止过拟合） |
| Q5 | `snake` 没有文本 HUD，它的声明是"场地/食物/蛇头" | 已按实测声明 | 这类"没有 HUD"的游戏是 `required_ui` 用法的一次压力测试；将来新游戏照此办理 |
| Q6 | 47/193 对不同像素的跨版本配对，差异来自状态分叉 | 已登记 | 若要把"修复前 vs 修复后的画面差异"当成信号，必须先控制**同一游戏时刻**（例如同一 tick 采样），否则测的是状态分叉 |
| Q7 | 引擎仓遗留 `uid_cache.bin`（非本任务产出） | 未动 | 由决策者决定忽略/删除 |

---

## 12. `W1`–`W8` 逐条对照

| 编号 | 判据 | 结论 | 证据位置 |
|---|---|---|---|
| **W1** | P7 判据已实现且可机检（定义 + 实现位置 + 证据指针） | ✅ | §2.1（定义）、§2.2（实现位置表 + 56 个声明项）、`tools/playability_gate.py`（`verdict_p7` 等）、`tools/playability_controls.json`、`tools/tests/test_playability_p7.py`（23/23）、`runs/playability/t130-p7b/*/gate.json → p7_probe` |
| **W2** | P7 让 `neg_hud_missing` FAIL 并列出缺失项；20 款正样本 P7 全 PASS | ✅ | §2.3：`neg_hud_missing` → `side_panel/hud_label/panel_edge -> visible_in_tree`（完整门里 P1..P6 全 PASS、P7 FAIL → not_playable）；`--only-p7` 全量 20/20 PASS |
| **W3** | 新增第二个声明式负变体验证 P7 通用 | ✅ | §2.4：`neg_ui_offscreen`（另一个游戏 flappy、另一条子句 `on_screen`、`visible` 仍为 true）→ P7 FAIL，其余全 PASS；headless exit 0 |
| **W4** | 三种输入形态都跑过，各自给出正负分布与阈值扫描错分 | ✅ | §4（六种形态与裁剪规则）、§5.1（分布）、§5.2（扫描）；备注：`editor_whole` 形态**没有负样本**（历史产物里没有变体的整窗截图），所以它的分离度以受控 `composite` 形态给出并对齐说明 |
| **W5** | 明确二选一结论 | ✅ | §5.4：**结论②**（三种形态都不分离：gap −0.780 / −0.804 / −0.516；无可用运行点），保留证据与样本量，`playjev_thresholds` 不重标定 |
| **W6** | 那 20 对的逐对像素差/sha256 统计，并据此修正或确认"不可见" | ✅ | §7：21 张被两次判定的图像 **21/21 逐像素相同**；193 对里 **146 同 / 47 不同**（max delta 250 / 227286 像素）；说法修正为"这批配对没有视觉差异（确定性的必然）"而**不是**"跨版本画面本来就相同" |
| **W7** | 可重跑命令（逐条，含环境变量/端口/裁剪参数） | ✅ | §8（8 组单行 cmd，端口 9913–9917、`--only-p7`、`--visual-input-form crop`、`--recheck 8`） |
| **W8** | 铁律 + 文件所有权自查 + 两仓 `git log --oneline -5` 与 `git status --short` | ✅（含 1 处违规披露） | §9.1（铁律逐条）、§9.3（独占/禁触核查）、§9.4/§13（两仓 log/status）、§9.5（非本任务遗留点名） |

---

## 13. 提交记录（提交后追记）

**本任务的提交：见本节末尾（提交后回填）。**

提交前用 `git status --short` 逐项核对，`git add` 的路径**逐个显式给出**（未用 `-A`）；
`runs/**` 全部是运行产物且被 `.gitignore` 忽略，不入库；
`godot-mcp/godot/uid_cache.bin`（引擎仓遗留）未暂存。

提交后：

```
（提交后回填：git log --oneline -5 / git status --short，两仓各一份）
```
