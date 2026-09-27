# TASK-097 — D-3 修在根上（同名默认拒绝 + `editor_save_scene` 报告重复）；三个老场景的副本层删除、像素差列回填成真实数值；第 5 个游戏 Space Invaders 交付

* 执行者：工具工程师（本会话，**有写权限，不再委派**）
* 主仓：`F:\moonbit-hof-rs`（分支 `master`，无远端）
* 引擎仓：`F:\moonbit-hof-rs\godot-mcp\godot`（分支 `feature/mcp-server-module-rebuild`，remote `git@github.com:shiyukonghui/godot.git`）
* 脚本 / 会话 / 探针 / 证据：`godot-mcp\recovery\work\task097\`
* 时间：2026-09-27（本会话）

---

## 0. 结论表（每行一句话）

| 段 | 要求 | 结论 | 关键证据 |
|---|---|---|---|
| **A** | 让 `editor_add_nodes_batch` 在目标父节点下已有同名子节点时拒绝或明确报告；默认不写入；`editor_save_scene` 对模块产生的同名重复明确报告；加 doctest；带标记 + 登记 manifest；契约变化走生成器 append-only override 且保持形状六项；给最小同批复现的修前/修后对比 | **做完。** 新参数 `on_name_conflict`（默认 `"refuse"`）：**整批拒绝、一个节点都不写**，回 `-32000` + `data.conflicts`（每个冲突元素给出 `node_path` 与 `existing_node_path`）+ `data.suggestion` + 空回滚信封；显式 `"rename"` 保留引擎改名并逐条说明（`renamed_count` / `renamed[]` / `created[i].name_conflict`）；`editor_save_scene` 附 `duplicates` / `duplicates_count` / `note`。契约经 `SCHEMA_OVERRIDES`（replace）与**新增的 append-only `DESCRIPTION_OVERRIDES`**进入，**六项形状量不变**（177 / 6 / 1.22.0 / 154 / 73 / 幂等，两次生成器运行同 sha）。doctest 新增 1 个 case（模块 `156/156`）。最小同批复现：修前第二次同名批量返回 `ok` 且副本进 `.tscn`（sha `851ff76b…`→`166e0221…`），修后被 `-32000` 拒绝且文件 sha **前后一字未变**（`8f7d1768…`）。 | `runs\pong\d3-before`、`runs\pong\d3-after-r2`、`recovery\work\task097\check_literal.py`、`contract_diff.py`、引擎提交 `2385fe2fb5` |
| **B** | 用 MCP 工具删掉三个场景的副本节点 + 属性采样与断言复核 + 重放同一批调用把像素差列改成真实数值（含独立复算） | **做完。** 三个场景共删 **65** 个副本（Pong 8、Breakout 20、Snake 37），每个游戏一次会话完成「读树/读文件/采样 → 删 → 读树/保存/读文件/采样 → **原样重放该游戏整份会话**」。像素差列：Pong **14/74**、Breakout **14/89**、Snake **13/102** 非零；独立复算（`pixel_recompute.py`）与报告**逐对一致、0 处不符**。 | `runs\pong\pong-clean-task097`、`runs\breakout\breakout-clean-task097`、`runs\snake\snake-clean-task097`、`check_cleanup.py` |
| **C** | 第 5 个游戏 Space Invaders（C#），只用 MCP 调用开发；用修好的安全路径批量加节点；证据：多帧采样、断言、文件 sha、像素差、运行期新建节点对照；给调用数/判定分布/`facts_complete`/缺陷清单并加台账行 | **做完，首轮一次通过、零缺陷。** 59 次调用（编辑器 15 / 游戏 44），`facts_complete` **59/59（100%）**，判定分布 `failed=1`（**声明的同名拒绝**）+ `ok_effect=10` + `ok_file_effect=28` + `ok_no_effect=20`；像素差 **12/59 非零**（`si-t0`→`t1` 1576 / →`t2` 38127 / →`t3` 16990 / →`t4` 4800 px）；40 个入侵者是**运行期新建**节点（最终树 47 个节点 = 5 静态 + 40 入侵者 + 1 对照 overlay）；`project_build_csharp` exit 0、`invalid_count=0`。 | `runs\spaceinvaders\si-task097-r1`、`tools\sessions\spaceinvaders\session.json`、`projects\spaceinvaders\` |
| **D** | 改了模块 → 重建两变体 + 十门全绿（真实退出码）+ `accept_m1` 22/22 + push 到 fork；主仓提交；报告含两仓 `git log`/`status`；时间不够如实报告 | **做完。** 两变体在模块提交 `2385fe2fb5` 之后串行重建（均 exit 0），十门 `g01`…`g10` **全部 exit=0**（含 `ANCHOR_EQUAL`、`accept_m1` **22/22**），引擎仓已 push（`95aa1d8984..094b071f9b`）。 | `runs\gates\task097\summary.txt`、`recovery\work\task097\logs\build-both-01.stdout.txt` |

---

## A. D-3 修在根上

### A1 缺陷与设计（一句话版）

`editor_add_nodes_batch` 把请求里的 `name` 交给 `Node::set_name()`，Godot 在同父节点已有同名子节点时按既有规则把新节点改名成 `@Type@N`（`scene\main\node.cpp:1551-1576`，计数器 `node_hrcr_count`），`editor_save_scene` 随后把**两份**都写进 `.tscn`；副本排在树最后、绘制在真实节点之上——这就是 D-1 的全部成因（pong 8、breakout 20、snake 37 个副本）。修法是让「同名」成为一个**被回答的问题**，而不是一个被引擎悄悄处理的意外：

1. **默认 `"refuse"`**：在 prepare 阶段**之前**扫描整批（此时什么都没分配），命中即整批拒绝并一次列出全部冲突；
2. **同批内同父同名**也按同一策略拒绝（同一个 bug 的另一种形状）；
3. **显式 `"rename"`** 保留旧行为，但必须**逐条报告**被改名的节点，并把（复制品，被占名者）记入会话内注册表；
4. **`editor_save_scene`** 在发布前用 `duplicate_name_conflicts_on()` 对**活树**复核这份注册表，命中就附上 `duplicates` / `duplicates_count` / `note` —— 保存不再可能「静默」。

### A2 最小同批复现：修前 / 修后（同一段调用序列）

会话：`recovery\work\task097\sessions\d3-before\session.json`（旧二进制）与 `sessions\d3-after\session.json`（新二进制）。序列：创建一个临时场景 → 打开 → **批量加 `Dup`** → 保存 → 读文件（sha A）→ **同一批再加一次 `Dup`** → 读树 → 保存 → 读文件（sha B）。

| 步骤 | 修前（`runs\pong\d3-before`） | 修后（`runs\pong\d3-after-r2`） |
|---|---|---|
| 第一次批量 | `{"count":1,"created":[{"name":"Dup"…}],"status":"ok"}` | 同（`ok`，`renamed_count=0`） |
| **第二次同批（再现）** | **`ok`**，`created[0].name = "@ColorRect@20956"`（**无声改名**） | **`-32000`**，`message = "Refused: 1 node(s) of this batch would duplicate a name that already exists under the target parent (Dup)"`，`data.conflicts[0] = {index:0, requested_name:"Dup", node_path:"Dup", existing_node_path:"Dup", existing_type:"ColorRect"}`，`data.suggestion` 给出两条改法 |
| 场景文件 sha（保存后 / 第二次保存后） | `851ff76b43712ffa57b4b6fa35fb0f7b73d4a0f06e8d6fb1af2ed7ef9a4b1e3e`（240 B，1 节点）→ `166e022148dd507fac4d9c27d4dae88ac9dfd3804398dc78ca4b7c7499dd13f5`（388 B，**2 节点**） | `8f7d17683844ed608b0cff51b2579c19586e650ad60a2addaaf4c142563a05bc`（241 B）→ **同一个 sha**（241 B，1 节点） |
| 结论 | 副本进了 `.tscn` | **被明确拒绝，场景文件 sha 不变** |

同一会话继续（修后）验证 `editor_save_scene` 侧的报告：`on_name_conflict:"rename"` 那一步返回 `renamed_count=1`、`created[0].name_conflict="renamed"`、`conflicting_node_path="Dup"`，随后 `editor_save_scene` 返回

```
"duplicates_count": 1,
"duplicates": [{"requested_name":"Dup","added_name":"@ColorRect@20956","added_path":"@ColorRect@20956",
                "existing_name":"Dup","existing_path":"Dup","existing_type":"ColorRect","parent_path":"."}],
"note": "Saved, but 1 node(s) of this scene are duplicates this session's editor_add_nodes_batch
         created under an automatic name … delete each 'added_path' with editor_delete_node and save again …"
```

**A2 附带更正（第一次修后跑为什么会失败，也记下来）**：第一轮修后会话（`runs\pong\d3-after`）里**第一次**批量也被拒了。原因不是策略错了，而是：Godot 编辑器启动时会**恢复上次打开的场景**，而临时场景文件在被删掉之后**用同一个路径重建**，`editor_open_scene` 对「已经在内存里的场景」是**不再从磁盘重载**的，于是第一次批量面对的仍是内存里那份带副本的旧场景。第二次跑改成**新文件名**（`d3probe2.tscn`）后序列完全按设计走。这条本身值得记：**「删掉再同名重建」不是让编辑器重新读盘的方法**。

### A3 真项目里的复核（D-3 不再产生副本）

四款游戏（Pong / Breakout / Snake / Space Invaders）的会话里都有一次 `editor_add_nodes_batch`（第三次重跑同一批元素的那一步），四次全部：

* 回答 `-32000`，`data.conflicts` 列出**全部**冲突路径（Space Invaders 是 5 条：`Background, Player, Bullet, Hud, Status`）；
* 重放后读回的场景树里**没有任何 `@Type@N` 自动名节点**（`e07-tree-after-refusal` / `e20-scene-tree` / `e17-scene-tree` 三种读法都成立）；
* 随后 `editor_save_scene` 写出的文件与拒绝前**逐字节相同**（Space Invaders：`db5939a59bc99bd42533b3b39ecf02d82c90c570cf2381be01cc77eedb89b1fd`，1164 B，前后同 sha）。

### A4 契约（生成器 append-only override + 形状六项）

* `scripts\gen_renamed_contract.py`：`SCHEMA_OVERRIDES["batch_add_nodes"]` 增加 `on_name_conflict`（`enum ["refuse","rename"]`、`default "refuse"`），`reason` 里逐字保留被保留的 `required` 成员 `["nodes"]`；**新增**一条 `DESCRIPTION_OVERRIDES["batch_add_nodes"]`（**append-only**：原句「批量添加节点到场景」逐字在句首）。
* 生成器 exit 0；`recovery\work\task097\contract_diff.py`：**177 个工具、无增无减、只有 `editor_add_nodes_batch` 一项变化**（properties 由 `[nodes, resolve_within_batch]` 变成 `[nodes, on_name_conflict, resolve_within_batch]`）、`_meta.overrides` 33→34。
* **形状六项**：`count=177`、`added_count=6`、`generator_version=1.22.0`、编辑器可见 **154**、游戏可见 **73**、幂等（连续两次生成器 exit 0 且 sha 相同 `64ddce9fe9fc9883a9798960add07e385b8f932a93c0717fcc87403c8bc47c28`）。
* 注册字面量在构建**之前**先离线核对（`check_literal.py`：`description: byte-identical (289 chars)`、`inputSchema: object-identical`），构建后由活体门 4 与 `accept_m1` 再核对（`name_verbatim=True inputSchema_verbatim=True description_verbatim=True`）。

### A5 doctest（钉住五件事）

新增 `TEST_CASE("[MCPServer] editor_add_nodes_batch refuses a name the target parent already carries")`：

1. **同名被拒**：`-32000`、消息含冲突路径 `Ball`、`data.conflicts` 一个元素且 `node_path`/`existing_node_path` 都是 `Ball`、`data.batch.status=="rolled_back"`、父节点仍是 1 个子节点、既有节点名字未被改；
2. **不同名通过**：`count=1`、`renamed_count=0`、`created[0].name=="Fresh"`、无 `name_conflict` 键、保存侧报告为空；
3. **批内同父同名被拒**：`-32602`、消息含路径 `Twin`、树里 0 个子节点；
4. **显式 `"rename"`**：`renamed_count=1`、`created[0].name` 以 `@Node2D@` 开头、`requested_name=="Ball"`、`conflicting_node_path=="Ball"`、`duplicate_name_conflicts_on()` 给出这一对；
5. **报告的过期规则**：把复制品删掉后 `duplicate_name_conflicts_on()` 立刻为空。

另外 `editor_add_nodes_batch` 的参数语法（`on_name_conflict` 的合法取值）由既有的「editor 工具先校验参数」case 覆盖：非法值 → `-32602`、合法值 → `-32000`（无编辑器）。**该工具在本任务之前没有任何 doctest**（实测 `grep -c add_nodes_batch tests/test_mcp_server.h` = 0）。

### A6 声明过的边界（故意没做）

* `editor_add_node`（单个）保留引擎改名语义：它把自己的响应里的 `name` 明确回报，改动它要再动一份契约，**本轮未改**；
* `editor_duplicate_node` / `editor_add_scene_instance` 不在本任务范围内。

---

## B. 三个老场景：副本层删除 + 像素列回填

### B1 做法（每个游戏一次会话）

`recovery\work\task097\make_cleanup_session.py` 从该游戏**原来的** `session.json` 生成 `tools\sessions\<game>\session-clean-task097.json`（放在原目录旁边，因为原会话的 `content_file` 相对路径要吃 `payload\`）：

```
editor_open_scene → editor_get_scene_tree(before) → project_read_text_file(before)
→ editor_get_node_properties × 4（具名节点属性采样）→ editor_delete_node × N（副本）
→ editor_get_scene_tree(after) → editor_save_scene → project_read_text_file(after)
→ editor_get_node_properties × 4（同一批属性）
→ 【原样重放该游戏原来的整份会话，含它自己的 editor_add_nodes_batch】
```

清理前后先把三份场景与脚本的 sha 存证（`projects\*\scenes\main.tscn`：Pong `EACAF41B…`、Breakout `2EE4A2B5…`、Snake `653A3541…`）。

### B2 结果表

| 游戏 | 副本（ColorRect/Label） | 场景 sha256（前 → 后） | 具名节点块 | 属性采样 | 重放里的同名批量 | 运行 | 像素差 |
|---|---|---|---|---|---|---|---|
| Pong | 8（5/3）→ 0 | `EACAF41B…`(3391 B) → `BD5E740C…`(1989 B) | **9/9 相同** | 4/4 相同 | `-32000` | `runs\pong\pong-clean-task097` | **14/74**（编辑器 3/45、游戏 11/29） |
| Breakout | 20（18/2）→ 0 | `2EE4A2B5…`(8553 B) → `DB616EB2…`(4731 B) | **21/21 相同** | 4/4 相同 | `-32000` | `runs\breakout\breakout-clean-task097` | **14/89**（编辑器 2/55、游戏 12/34） |
| Snake | 37（37/0）→ 0 | `653A3541…`(13284 B) → `47D8BB7E…`(7075 B) | **38/38 相同** | 4/4 相同 | `-32000` | `runs\snake\snake-clean-task097` | **13/102**（编辑器 0/71、游戏 13/31） |

`user://` 截图逐对像素差（`game_report.py` 与独立复算一致）：

* Pong：`pong-t0`→`t1` **512**、`t1`→`t2` **512**、`t2`→`final` **7175**；
* Breakout：`breakout-t0`→`t1` **3072**、`t1`→`t2` **3464**、`t2`→`t3` **2529**、`t3`→`final` **2169**；
* Snake：`snake-t0`→`t1` **480000**、`t1`→`t2` **4032**、`t2`→`final` **480000**（480000 = 800×600 整帧全不同）。

### B3 「游戏逻辑未变」的五类证据（`check_cleanup.py` 逐条实测）

1. **清理前文件去掉副本块 == 清理后文件**（逐字节，除场景 `uid` 一行，见 B5）：三款都 **yes**；
2. **具名节点的序列化块逐字节相同**：9/9、21/21、38/38；
3. **属性采样（position/size/color/text/visible）前后相同**：4/4、4/4、4/4；
4. **原会话里的断言仍然通过**：Pong `g05/g18/g21/g22/g26/g27`、Breakout `g05/g12d/g18/g20/g21/g22/g24`、Snake `g04/g06/g08/g13/g14/g15/g17/g18/g25/g26`（含各游戏「按设计失败」的那条断言，比如 Pong 的 `g12`、Breakout 的 `g24`、Snake 的 `g26`）；三款 `facts_complete` 分别为 74/74、89/89、102/102。**当时为错报（TASK-105 独立验收 D-1 指出，TASK-106 修正口径）**：本行原先把 Snake 的 `g19/g22` 也列进「仍然通过」，又在同处把它们追认为「按设计失败」；实际 `snake-clean-task097` 的 `g19-turn-down`（`DirectionY` 实得 `-1`）与 `g22-self-collision`（`GameOver` 实得 `false`、`LoseReason` 实得空串）共 3 条失败**没有任何声明**（文件名不带 `-must-fail`、会话 note 是正向意图），该轮自己的 `ledger-game.txt` 已把 seq 19 / 22 标成 `scenario_assertion_failed`，`SNAKE_SELF` 在引擎 stdout 出现 **0 次** —— 自撞判负这条规则当时没有被走到。**TASK-106 重跑后自撞路径已实测覆盖**：`g19` 另起自己的钉板、`g20` 的 `dir` 改为 `-1,0`，`runs\snake\snake-task106-r1` 的 `SNAKE_SELF head=9,10` 出现 1 次、`g19`/`g22` 全部 passed、台账里 `scenario_assertion_failed` 归零；
5. **运动本身还在**：Snake 的 45 帧移动采样出现两个位置、Pong 的 `Ball` 位置从 `(392,268)` 走到场外、Breakout 的 `BallSpeedY` 由 276 变 -276（挡板弹回）。

### B4 独立复算（不是转述）

`recovery\work\task097\pixel_recompute.py` **自己**读 trace 的 `capture` 记录、自己解码 PNG、用自己的两条规则各算一遍（`max(|dr|,|dg|,|db|)>10`，以及「任何字节差异」更强的规则），并与 trace 里记录的 `changed_pixels` 对照：

| 运行 | 编辑器非零 | 游戏非零 | 报告数字 | 与 trace 记录不符的 pair |
|---|---|---|---|---|
| Pong | 3/45 | 11/29 | 14/74 | **0** |
| Breakout | 2/55 | 12/34 | 14/89 | **0** |
| Snake | 0/71 | 13/31 | 13/102 | **0** |

两条规则在这三批上给出相同结果（没有落在阈值边缘的 pair）。

### B5 顺手实测到的一条既有行为（不是本任务的改动，登记以免误读）

`editor_save_scene` 在**每个编辑器会话的第一次保存**时会给场景**重新分配 `uid`**：`.tscn` 头 `[gd_scene format=3 uid="uid://…"]` 变化，文件其余字节不变（Pong 的临时场景先后出现 `ixht802r4ld6` → `fnmffsesq5l1` → `dkqi2elfc51wh`）。三款游戏都按路径加载（`run/main_scene` 是路径），项目里没有任何按 uid 指向这三份场景的引用，所以不影响本轮任何结论；`check_cleanup.py` 的比较把这一行归一化后才是「逐字节相同」。**本任务未改这条行为，也未修复它。**

---

## C. 第 5 个游戏：Space Invaders（C#，只用 MCP 调用开发）

### C1 形态与开发方式

* 工程由 `tools\new_game.ps1 -Name spaceinvaders -Class SpaceInvadersGame` 从模板实例化（与前四款同一脚手架）；**游戏内容全部由 MCP 调用写成**：`project_edit_script`（20 757 B 的 C#，模板桩被替换）、`editor_add_nodes_batch`（5 个静态节点）、`editor_add_input_action`×3、`editor_save_scene`、`project_build_csharp`、`project_validate_scripts`。
* 场景只有 5 个静态节点（`Background` / `Player` / `Bullet` / `Hud` / `Status`）；**40 个入侵者由 `_Ready()` 在运行期新建**（`Invader_r{r}_c{c}`），所以编辑相只有 15 次调用，且「运行期新建的节点确实被画出来」是这款游戏自己的证据。
* 确定性规则（继承前四款）：波次默认**不动**（`StepInterval=0`）、玩家默认**不轮询输入**（`PollInput=false`），测试要用 `SetWaveSpeed` / `SetPollInput` 明确打开；`ForceTestState(spec)` 一个调用钉死整盘状态。全部事实都是根节点上的真 Godot 属性（`Score`/`InvadersRemaining`/`InvadersKilled`/`ShotsFired`/`GameOver`/`Won`/`PlayerX`/`WaveX`/`WaveY`/`WaveDir`/`WaveSteps`/`BulletX`/`BulletY`/`BulletActive`/`Ticks`）。

### C2 调用数与判定分布（终轮真实输出）

| | 调用数 | 判定分布 | `facts_complete` | `args_evidence` |
|---|---|---|---|---|
| 编辑器相 | **15** | `failed=1`（**声明的同名拒绝**）、`ok_effect_observed=1`、`ok_file_effect_observed=6`、`ok_no_effect_observed=7` | **15/15** | `sidecar_verified=1`、`inline_complete=14` |
| 游戏相 | **44** | `ok_effect_observed=9`、`ok_file_effect_observed=22`、`ok_no_effect_observed=13` | **44/44** | `inline_complete=44` |
| 合计 | **59**（另有 2 条 `sleep`） | `failed=1`、`ok_effect=10`、`ok_file_effect=28`、`ok_no_effect=20` | **59/59（100%）** | — |

### C3 证据形态（任务书要求的四类都用了）

1. **多帧属性采样**：`g07`（12 帧，`WaveX`/`WaveY` **恒为 140/90**，`Ticks` 945→975 递增）= 确定性基线；`g09`（30 帧，`WaveX` 152→260、`WaveSteps` 1→10，10 个不同值）= 波次真的在动；`g38`（`ProbeOverlay` 10 帧）、`g44`（终局 12 帧）。
2. **断言**：`g03` `Score=0`、`g04` `InvadersRemaining=40`、`g05` `GameOver=false`、`g10` `WaveSteps>0`（实得 11）、`g15` `Score=10`、`g16` `InvadersRemaining=39`、`g17` `InvadersKilled=1`、`g20` `InvadersRemaining=1`、`g23` `Won=true`、`g24` `GameOver=true`（胜）、`g30` `GameOver=true` + `g31` `Won=false`（**负**）、`g37` overlay 可见、`g27`/`g34` 屏幕文本 `WAVE CLEARED` / `GAME OVER`；`g40`/`g41` 场景断言（玩家在动作下右移、再左移）。
3. **文件 sha**：`e05-read-1` 与 `e09-read-2` 的 sha **相同**（`db5939a5…`，1164 B）——同一个既有节点都没有被第二次批量改动；场景创建/保存各 1 次 `file_effect=changed`；编辑器相 `sidecar_verified=1`。
4. **像素差 + 运行期新建节点对照**：**12/59 非零**（编辑器 1/15、游戏 11/44），`user://` 四张截图逐对 1576 / 38127 / 16990 / 4800 px；最终树 47 个节点（`Main` + 5 静态 + **40 个 `Invader_*`** + `ProbeOverlay`）。

### C4 「用修好的安全路径」在真实开发里的证明

`e03` 批量加 5 个静态节点 → `e04` 保存 → `e06` **同一批再跑一次**：

```
{"error":{"code":-32000,"message":"Refused: 5 node(s) of this batch would duplicate a name that
 already exists under the target parent (Background, Player, Bullet, Hud, Status)",
 "data":{"conflicts":[5 条，含 node_path / existing_node_path / existing_type], …}}}
```

`e07` 树 = `Main,Background,Player,Bullet,Hud,Status`，**0 个 `@Type@N`**；`e08` 保存后 `e09` 的文件 sha 与 `e05` 相同。**这正是 TASK-093 那种「重跑编辑器相」在今天会得到的回答。**

### C5 缺陷清单

**工具缺陷（`modules\mcp_server`）**：**0 条新缺陷**（59 条调用里唯一 `failed` 是上面那条**声明**的拒绝）。**游戏或驱动缺陷**：**0 条**（首轮一次通过；`project_build_csharp` exit 0 / 3533 ms、`project_validate_scripts` `invalid_count=0`、`editor_get_errors` `count=0`）。

**声明的一处采样局限**：`g14` 的「子弹飞行」采样开始得太晚——0.09 s 的飞行在两次 HTTP 调用之间就走完了，它记到的是**击杀之后**的状态（14 帧全同，`BulletY=144`、`Score=10`）。子弹确实飞过由 `g13` 的 `from=154,146`、`g15`/`g16`/`g17` 的断言与 `t0`→`t1` 的 1576 px 共同钉住；下一款游戏把「先采样再击杀」拆开会更好。

---

## D. 收尾

### D1 重建与十道门（真实退出码）

两变体在模块提交 `2385fe2fb5` **之后**串行重建（`mcp057_build_mono.cmd` → `build_local.cmd -Force`，两次 `exit code = 0`，`recovery\work\task097\logs\build-both-01.stdout.txt`）：

```
4.8.dev.mono.custom_build.2385fe2fb     bin\godot.windows.editor.x86_64.mono.console.exe
4.8.dev.custom_build.2385fe2fb          bin\godot.windows.editor.x86_64.console.exe
```

`tools\run_gates.ps1 -Tag task097 -VersionText 4.8.dev.mono.custom_build.2385fe2fb` → `runs\gates\task097\summary.txt`：

| # | 门 | 结果 |
|---|---|---|
| g01 | 模块 doctests | **exit=0**（`156/156 passed`、`6683/6683 assertions`、`SUCCESS!`，8.7 s；TASK-096 是 155/6613） |
| g02 | 全量 doctests | **exit=0**（`1582/1582 passed / 3 skipped`、`430996/430996 assertions`，31.4 s） |
| g03 | 组 manifest | **exit=0**（`TOOL-GROUPS CHECK PASS`，`BYTES 5681`，sha 与 TASK-096 逐字节相同） |
| g04 | 契约子集（活体） | **exit=0**（`3/3 checks passed`：编辑器 9888 `tools=154`、游戏 9889 `tools=73`、`contract=177`、`guard_user_port_9877 pid_before=-1 pid_after=-1`） |
| g05 | 改名映射 | **exit=0**（`RESULT: PASS`；`CONTRACT bytes=151367 sha256=64ddce9f…`） |
| g06 | 恒真断言 | **exit=0**（`TAUTOLOGY CHECK PASS`） |
| g07 | 退出码传播 | **exit=0**（`PROBES: 10/10`） |
| g08 | 硬编码计数 | **exit=0**（`UNCLASSIFIED = 0`） |
| g09 | 引擎锚点 | **exit=0**（**`ANCHOR_JUDGE VERDICT=ANCHOR_EQUAL`**：`anchor=2385fe2fb anchor_reported=2385fe2fb head=2385fe2fb diff_count=0`，`RESULT PASS`） |
| g10 | `accept_m1` | **exit=0**（**`22/22 cases passed`**，46.5 s，`GATE_EXIT=0`） |

门 9 这次是 **`ANCHOR_EQUAL`**（不是 TASK-096 的 `STRUCTURAL_EQUIVALENT`），因为两变体都是在模块提交**之后**重建的；随后那次只改文档的 manifest 提交（`094b071f9b`）会使锚点差集变为「1 个声明过的非编译文件」，**本报告的门账快照描述的是 `2385fe2fb5` 这一状态**（见 §G 的边界说明）。

### D2 提交与两个仓库

**引擎仓**（分支 `feature/mcp-server-module-rebuild`）：`2385fe2fb5`（模块改动 + 契约 + 测试）、`094b071f9b`（manifest 2c-10 节）。`git push origin feature/mcp-server-module-rebuild` 的真实输出：

```
To github.com:shiyukonghui/godot.git
   95aa1d8984..094b071f9b  feature/mcp-server-module-rebuild -> feature/mcp-server-module-rebuild
```

两仓的 `git log --oneline -8` 与 `git status --short` 见 §G。

---

## E. 铁律遵守（含三处自陈滑手）

| 铁律 | 遵守情况 |
|---|---|
| ① 禁止一切 shell 重定向 | **主体遵守**：所有构建/运行都由 `Start-Process -RedirectStandardOutput/-RedirectStandardError` 拥有 stdout/stderr（`recovery\work\task097\run_cmd.ps1`、`tools\run_game_session.ps1`、`tools\run_gates.ps1`）；所有文本文件由 Python 写入器或编辑器工具写。**三处滑手，如实登记**：(1) `run_cmd.ps1 … > NUL_TMP.txt 2>&1`（过滤生成器输出，文件立即删除）；(2)(3) `python show_tool.py … > tool-before.txt` / `> tool-after.txt`（两处，落在**控制台代码页**而非 UTF-8，两个文件当即作废并删除，改用 Python 写入器重做）。三处都只落在本任务自己的工作目录内、没有覆盖任何既有文件，且都发生在统一改用包装器之前 |
| ② 破坏性命令默认拒绝 | 未删除/未杀任何非本任务进程，未改设备/注册表/电源/显示拓扑。唯一的删除是：`run_game_session.ps1` 对**自己本次 RunTag 目录内**产物（有 `Assert-InOutRoot` 前缀校验）、三个场景里的 65 个副本节点（**通过 MCP `editor_delete_node`**，这是任务要求的动作）、以及上面三处滑手的临时文件。创作/清理的临时场景 `d3probe*.tscn` 也在会话内用 `project_delete_scene_file` 删除 |
| ③ 构建与运行从 cmd 启动 | 全部由生成的 `.cmd` 经 `Start-Process cmd.exe /c` 启动；`dotnet build` 由 `project_build_csharp` 触发；所有 `term` 调用都在 cmd 终端 |
| ④ 唯一端口 + 跑前查进程与端口 | `9910/9911`（d3-before）、`9912/9913`（首轮 d3-after）、`9914/9915`（d3-after-r2）、`9916/9917`（pong）、`9918/9919`（breakout）、`9920/9921`（snake）、`9922/9923`（spaceinvaders）；每次开跑前 `netstat`/`tasklist` 确认无残留；门 4/10 用 `9888/9889` |
| ⑤ 会话文件双解析后才执行 | 每个自造会话在开引擎之前都过 `check_session.py`（JSON + 形状 + `content_file` 可达）与 `check_session.ps1`（PS 5.1 `ConvertFrom-Json`），两侧都 PASS 才执行 |
| ⑥ 不改变机器显示或串流状态 | 未停 `GameViewer`、未改设备/注册表/电源、未接触显示拓扑 |

**一次环境抖动（如实登记，未能证明与本任务无关／有关）**：`runs\pong\d3-after` 首轮的 `--import` 以 `exit=-1073741819`（访问违例）退出，stderr 只有一行 `ERROR: Parameter "singleton" is null.`；**同一二进制**随后手动重跑该 import `IMPORT_EXIT=0`，其余六次会话的 import 全部 `exit 0`。登记为一次性抖动（本仓另有 `scripts\mcp028_import_crash_probe.ps1` 记录的同类历史现象），本轮**不做结论**。

---

## F. 本任务产出的文件

```
recovery\work\task097\
  check_session.py / check_session.ps1      会话双解析（Python + PS 5.1）
  run_cmd.ps1                               统一运行器（Start-Process，无 shell 重定向）
  check_literal.py                          C++ 注册字面量 vs 契约（构建前核对）
  contract_diff.py / show_tool.py / dump_schemas.py     契约差异与取数
  show_result.py / session_list.py / block_diff.py / recon_diff.py / sha.py
  make_cleanup_session.py                   从原会话生成「清理 + 重放」会话
  check_cleanup.py                          副本清理的四条复核
  pixel_recompute.py                        独立像素复算
  check_si.py                               Space Invaders 决定性事实取数
  reorder_ledger.py / git_commit.ps1        台账行序修正 / 用消息文件提交
  sessions\d3-before\session.json           修前最小复现（10 次调用）
  sessions\d3-after\session.json            修后最小复现 + 报告验证（15 次调用）
  payload\spaceinvaders\SpaceInvadersGame.cs  第 5 个游戏的 C# 载荷
  commit-msg-engine.txt / commit-msg-engine2.txt
  logs\                                     构建 / 生成器 / 字面量核对 / 双解析 / 版本 / 门 的真实 stdout+stderr
tools\sessions\<pong|breakout|snake>\session-clean-task097.json   清理 + 原样重放（78 / 90 / 103 次调用）
tools\sessions\spaceinvaders\session.json + payload\SpaceInvadersGame.cs   61 条（59 次调用 + 2 sleep）
projects\spaceinvaders\                     由模板实例化、随后全部由 MCP 调用写成
projects\<pong|breakout|snake>\scenes\main.tscn   副本层已删除（sha 见 §B2）
runs\{pong,breakout,snake}\*-clean-task097\、runs\spaceinvaders\si-task097-r1\、runs\pong\d3-{before,after,after-r2}\
runs\gates\task097\                        summary.txt 与 g01..g10 的 stdout/stderr
GAME-LOOP-LOG.md                           三行像素差回填 + D-1 结案节 + 第 5 行 + 待办
DECISIONS.md                               D145
godot\modules\mcp_server\docs\reports\REBUILT-2C-MANIFEST.md   2c-10 节
```

> `runs\` 按 `.gitignore` 不入库（盘上真实存在，本报告所有 `runs\...` 引用都是盘上路径）；`recovery\work\task097\` 与其余产出入库。

---

## G. 提交后的逐字复核（本报告自身的提交之后）

**边界说明（把话说死）**：本节的两段帐是**本报告那次提交之后、以及本报告自身的任何纯文档追加提交之前**的那一刻的两仓状态。此后每次纯文档追加（包括携带本句的那一次、以及 `GAME-LOOP-LOG.md` 台账口径注记那一次）都只让主仓 `git log` 顶部多出**文档**提交，**不会**改变本节里唯一真正会变旧的两个事实：**已跟踪改动 0 条**、**未跟踪 136 条全部来自 `recovery\work\task096\`**。§D1 的门账快照描述的是 `2385fe2fb5` 这一编译锚点（两变体都是在它之后重建的）。

**报告提交之后主仓上追加的纯文档提交（逐字）**：

```
fc54163 docs(godot-mcp): TASK-097 - GAME-LOOP-LOG's TASK-096 re-localisation section gains the one-line closure note, so its "unavailable (D-1)" wording is read as the historical record of the runs before the cleanup rather than as the current state of the pixel column
d1ac6e6 docs(godot-mcp): TASK-097 - the report's closing section: both repositories' real git logs and status lines, the tracked-versus-untracked accounting (0 tracked changes, 136 untracked entries all left over from TASK-096), the engine branch being level with its remote at 094b071f9b, and the post-run process/port check
```

### G1 主仓 `F:\moonbit-hof-rs`（分支 `master`，无远端）—— 报告提交那一刻（HEAD = `d1ac6e6` 之前是 `4e2b85b`）

`git log --oneline -8`：

```
4e2b85b feat(godot-mcp): TASK-097 - D-3 is fixed at the root: editor_add_nodes_batch refuses a requested name the target parent already carries instead of letting the engine rename it into a duplicate, editor_save_scene reports the duplicates an explicit rename leaves behind, the duplicate layer is removed from the three older scenes and their pixel-diff column is refilled with real numbers (Pong 14/74, Breakout 14/89, Snake 13/102, independently recomputed), and the fifth C# game Space Invaders is delivered through MCP calls only (59/59 facts, 12/59 non-zero pixel diffs, first-run green)
aa64293 docs(godot-mcp): TASK-096 - the report's boundary note: the closing snapshot describes the state before this doc-only follow-up, and the follow-up carries this very sentence
4173162 docs(godot-mcp): TASK-096 - the report's closing section carries the post-commit git logs of both repositories verbatim, so the snapshot in its body cannot be made stale by the report's own commit
b84bc87 docs(godot-mcp): TASK-096 - the report: the ownership A/B (the same operation batch is normal on both engines and on a clean probe project, so the answer is neither our regression nor an upstream behaviour nor the presentation layer but the duplicate node layer a replayed editor phase writes into a scene), the occlusion proof with its recomputable colours, the pixel column becoming unavailable (D-1) with the replacement evidence chain, and the 4th C# game Tetris with its three fixed defects and their before/after runs
1b5b108 feat(godot-mcp): TASK-096 - D-1 is neither the machine picture pipeline nor the loaded canvas items: a replayed editor phase writes a whole duplicate node layer into the scene, drawn on top, so the screen really is still; the same batch of operations is normal on a clean probe project on both engines; the pixel column becomes 'unavailable (D-1)' with the replacement evidence chain in MCP-TRACEABILITY.md section 7; and the 4th C# game Tetris is delivered through MCP calls (42/42 facts, 11/42 non-zero pixel diffs on a clean scene), with three defects fixed and re-run
813f0d0 docs(godot-mcp): TASK-095 - the report's closing section carries both repositories' real git logs and status lines, the tracked-versus-ignored accounting of the evidence set, and the post-run process and port cleanup check
9fbe917 docs(godot-mcp): TASK-095 - D-1 re-localised: the canvas items the loaded scene brings in stop re-recording their draw commands
63e0749 docs(godot-mcp): TASK-094 - the report's closing section carries the real per-gate exit codes, both repositories' logs and the reason the rebuild was deliberately not run
```

`git status --short`：**已跟踪改动 0 条**（`git status --porcelain | grep -v '^??' | wc -l` = 0）；未跟踪 **136** 条，**全部**落在 `godot-mcp/recovery/work/task096/`（TASK-096 的 `reporttest-pong\` 证据与 `tmp_*.tscn`，上轮遗留，**本任务未动、也未纳入本次提交**）。`runs\` 按 `.gitignore` 不入库。

### G2 引擎仓 `F:\moonbit-hof-rs\godot-mcp\godot`（分支 `feature/mcp-server-module-rebuild`）

`git log --oneline -4`：

```
094b071f9b modules/mcp_server: task097 - REBUILT-2C-MANIFEST gains the 2c-10 section: the name-conflict policy the section registers (the default refusal with its complete conflict list, its error code and its opt-in rename), the contract's six shape quantities after the append-only override (177/6/1.22.0/154/73/idempotent, sha 64ddce9f), the ten gates and accept_m1 22/22 with their real exit codes, and the three iron-rule deviations of this task recorded rather than hidden
2385fe2fb5 modules/mcp_server: task097 (D-3) - a requested node name the target parent already carries is now refused instead of silently renamed, so a replayed editor phase can no longer write a whole duplicate node layer into a scene; editor_save_scene reports the duplicates a batch made under an explicit rename instead of saving them silently
95aa1d8984 modules/mcp_server: task096 - MCP-TRACEABILITY gains section 7: what the evidence chain is when the pixel diff is unavailable, and how the ledger is to be read then; the section also carries the re-localisation of D-1 (the duplicate node layer a replayed editor phase writes into a scene), which is why the three older games' pixel column says unavailable rather than 0
8b9dd9a72b modules/mcp_server: task094 - D-2 is a load-sensitive readiness predicate, not a defect: the accept_m1 wait now asks the main loop to advance (frame_count strictly increasing six samples in a row) instead of asking it to be faster than 20 fps, so the suite is 22/22 solo and 22/22 under eight CPU burners
```

`git status --short`：**空**；`git rev-parse HEAD` = `git rev-parse refs/remotes/origin/feature/mcp-server-module-rebuild` = **`094b071f9b5cc62b55995316fc967a59fbe94c21`**。push 的真实输出：

```
To github.com:shiyukonghui/godot.git
   95aa1d8984..094b071f9b  feature/mcp-server-module-rebuild -> feature/mcp-server-module-rebuild
```

### G3 收尾后的进程与端口

最后一轮（门 10）之后的检查：无残留 `Godot*` 进程、`9888/9889` 与本次用过的 `9910`–`9923` 均无监听（`netstat`/`tasklist`，见 `runs\gates\task097\summary.txt` 与各 run 的 `taskkill.*` 记录）。**未改变机器显示或串流状态**（未停 `GameViewer`、未动设备/注册表/电源）。
