# TASK-103 — 工具缺陷 X-1（GDScript 运行期错误没有结构化错误）修在根上并重建两变体、十道门全绿（真实退出码）+ `accept_m1` 22/22 + push 到 fork；第 16、17 款 C# 小游戏（Tower Defense / Missile Command）交付；四条缺陷（工具 0 / 游戏或驱动 4）在各自首轮被照出来并重跑

* 执行者：工具/游戏工程师（本会话，**有写权限，按用户指令不再委派**）
* 主仓：`F:\moonbit-hof-rs`（分支 `master`）
* 引擎仓：`F:\moonbit-hof-rs\godot-mcp\godot`（分支 `feature/mcp-server-module-rebuild`）
  * **模块提交 `1c7f5c07a1`**（X-1 的代码 + 测试 + 契约 + 生成器 + 描述字面量，6 文件 / 479 增 19 删）
  * **manifest 提交 `1f9d0cb1c9`**（`REBUILT-2C-MANIFEST.md` 的 2c-12 节，1 文件 / 175 增）
  * 起点 `e041cae270`；**已 push 到 fork**：`e041cae270..1f9d0cb1c9 feature/mcp-server-module-rebuild -> feature/mcp-server-module-rebuild`
* 脚本 / 会话 / 证据：`godot-mcp\recovery\work\task103\`、`godot-mcp\runs\`、`godot-mcp\tools\sessions\{towerdefense,missilecommand}\`
* 报告：本文件。返回值 ≤ 10 行见文末 §G。

---

## 0. 结论表（每行一句话）

| 段 | 要求 | 结论 | 关键证据 |
|---|---|---|---|
| **A①** | 脚本**运行期错误**回结构化错误：错误码 + `data.script_error`（消息 / 行列若可得 / 脚本路径）+ `data.suggestion` | **做完。** 码取 **`-32000`（`tool_state`）** 并逐条写明理由：`-32602` 意味着**参数/语法**有问题（脚本**编译通过**了），`-32603` 意味着**模块**坏了（是调用者的代码失败了）。`data.script_error` 带引擎原文 `message`、`code` 的 `line`、`generated_line`、`script_path`、`function`、`error_count`、`messages`；**列号如实为 `null`**（引擎给处理器的只有行）；`data.suggestion` 给出改法。**最小同批复现**：同一份六调用会话逐字不改跑两次 —— 修前 `ok` + `{"result":null,"result_type":"Nil"}`（无码无消息），修后 `-32000` + `data.script_error`（`line=7`、`generated_line=10`、`function=_mcp_execute`、`script_path=gdscript://-9223371989626911104.gd`、`in_generated_body=true`）+ `data.suggestion` | `runs\match3\task103-x1-before\g01-failing-addchild.json`、`runs\match3\task103-x1-after\g01-failing-addchild.json`、`runs\match3\task103-x1-after\engine-game.stderr.txt` |
| **A②** | 成功但无副作用要能被区分 | **做完。** `result` 为 `null`/`Nil` 时响应带 **`note`**（成功路径没有 JSON-RPC 的 `error.data`，所以 note 落在工具自己的结果对象里，与其余答案同处）。修后 `g05-success-null` 回 `{"note":..., "result":null, "result_type":"Nil"}`，而**有值**的 `g03` 不带 `note` | `runs\match3\task103-x1-after\g05-success-null.json`、`…\g03-control-add_child.json` |
| **A③** | 错误信息必须**同时进入 trace** | **做完且实测。** 失败的 `data` 本就进溯源：`task103-x1-after` 的调用行（`seq=1`）带 `error_code:-32000`、`error_message` 与整段 `error_data_json`（871 B，`script_error` + `suggestion` 全在里面） | `runs\match3\task103-x1-after\trace-game.jsonl` 第 1 行 |
| **A④** | 加 **doctest**：解析失败 / 运行期错误 / 成功 三种情形 | **做完。** 新增一例 `[MCPServer] running_game_execute_gdscript reports a GDScript runtime error structurally`：把三种情形分开钉住（`-32602`；`-32000` + `script_error` 与它的行映射；成功有值 / 成功无值后者带 `note`），外加一条 **`push_error()` 控制**（`ERR_HANDLER_ERROR` **不得**变成拒绝，脚本自己的诊断不能把成功调用变成失败），以及 `script_path == body_script_path` 的可审计比较；TASK-090 的挂载用例在自己的失败路径上从「已记录的边界」改成「结构化拒绝」。模块用例 **156 → 157** | `godot\modules\mcp_server\tests\test_mcp_server.h`；gate 1 输出 |
| **A⑤** | 契约描述变化用生成器 **append-only override**，六项形状不变，改动带标记并登记 manifest | **做完。** `DESCRIPTION_OVERRIDES` 的 `execute_game_script` 追加（TASK-090 的句子逐字保留在句首）；契约 **151 367 B / `64ddce9f…` → 153 330 B / `bd68e804…`**，`_meta.overrides` **仍 34**（改既有条目、不新增）；**六项形状一字未变**：`count=177`、`added_count=6`、`generator_version=1.22.0`、编辑器可见 **154**、游戏可见 **73**、**幂等**（连续两次生成同 sha256）。C++ 注册字面量由 `gen_b2_game_schema.py --in-place` 重生成，构建前用 `check_literal.py` 逐字核对。改动登记在 `REBUILT-2C-MANIFEST.md` 的 **2c-12** 节 | `docs\tools_list.renamed.json`、`scripts\gen_renamed_contract.py`、`docs\reports\REBUILT-2C-MANIFEST.md` §2c-12、`recovery\work\task103\logs\{gen-contract-01,gen-contract-02,check-literal}.txt` |
| **B①** | **Tower Defense**（C#，只用 MCP 调用开发）：路径行进、放塔、射程与攻击、波次、生命与胜负 | **做完，首轮照出 1 条会话缺陷（TD-1）与 1 条证据设计缺陷（TD-2），逐条修好重跑到 r3 后全绿。** 145 次调用（编辑器 14 / 游戏 131），`facts_complete` **145/145（100%）**，判定分布见 §B2；断言 **77 PASS + 1 条声明的边界失败**（`-32001`）= **0 失败**；像素差 **31/145 非零**（编辑器 1/14、游戏 30/131），`user://` 五帧逐对 **185084 / 8356 / 3376 / 8133 px**、五个 sha **5/5 互不相同**；独立复算 **0 处不符**；`project_build_csharp` exit 0（3796 ms）、`invalid_count=0`；树里 **279 个节点名 0 个 `@` 开头** | `runs\towerdefense\td-task103-r3`（首轮 `-r1`，中间 `-r2`）、`logs\assert-td-r3.txt`、`logs\pixel-td-r3.txt`、`logs\frames-td-r3.txt`、`logs\recompute-td-r3.txt`、`logs\facts-td.txt` |
| **B②** | **Missile Command**（C#，只用 MCP 调用开发）：来袭弹、拦截弹、爆炸范围、城市存活、波次与得分 | **做完，首轮照出 1 条载荷/驱动缺陷（MC-1）与 1 条会话缺陷（MC-2），修好重跑到 r3 后全绿。** 127 次调用（编辑器 14 / 游戏 113），`facts_complete` **127/127（100%）**；断言 **73 PASS + 1 条声明的边界失败** = **0 失败**；像素差 **21/127 非零**（1/14、20/113），五帧逐对 **15823 / 13578 / 4370 / 346 px**、五个 sha **5/5 互不相同**；独立复算 **0 处不符**；`project_build_csharp` exit 0（3815 ms）、`invalid_count=0`；树里 **270 个节点名 0 个 `@` 开头** | `runs\missilecommand\mc-task103-r3`（首轮 `-r1`，中间 `-r2`）、`logs\assert-mc-r3.txt`、`logs\pixel-mc-r3.txt`、`logs\frames-mc-r3.txt`、`logs\recompute-mc-r3.txt`、`logs\facts-mc.txt` |
| **B③** | 跑完给：调用数、判定分布、`facts_complete`、缺陷清单（分两栏）；两行加进 `GAME-LOOP-LOG.md` | **做完。** 台账续到第 16、17 行；**工具缺陷 0 条**；**游戏或驱动缺陷 4 条**（TD-1 会话漏 force、TD-2 重跑未从模板重开、MC-1 `static` 调实例方法、MC-2 断言引用错时刻）+ **取证工具自身 1 条 R-1**（明确不算模块缺陷）；`GAME-LOOP-LOG.md` 新增「TASK-103 记录」节并把 X-1 那行改成「已修」 | `GAME-LOOP-LOG.md` 台账第 16/17 行与「TASK-103 记录」；`DECISIONS.md` 的 D151 |
| **C** | 重建两变体 → `run_gates.ps1` 十道门全绿（真实退出码）+ `accept_m1` 22/22 → push 引擎仓到 fork；主仓提交；报告含两仓 `git log --oneline -8` 与 `git status --short` | **全部做完。** 两变体在**模块提交之后**重建（`4.8.dev.mono.custom_build.1c7f5c07a` / `4.8.dev.custom_build.1c7f5c07a`）；`run_gates.ps1 -RunGates` 十道门 **g01..g10 全部 `exit=0`**（g01 157/157、g02 1583/1583、g04 `3/3` + 编辑器 154/游戏 73、g09 `ANCHOR_EQUAL`、**g10 `22/22 cases passed`**）；**已 push 到 fork**；主仓提交见 §F | `runs\gates\task103\summary.txt`、`recovery\work\task103\logs\gates-task103.txt`、`git-engine-manifest.out.txt`、§F |

---

## A. 工具缺陷 X-1（本轮唯一一次动模块）

### A1 现场与修法

现场是 TASK-102 的 `m3-task102-r1/g115-runtime-overlay`（**逐字取自该轮 trace 的 `args` 字段**）：

```
var main = get_parent()
var c = ColorRect.new()
c.name = StringName("ProbeOverlay")
c.position = Vector2(20, 556)
c.size = Vector2(120, 30)
c.color = Color(0.95, 0.35, 0.95, 1.0)
main.addChild(c)          <- C# 的拼写，打在一个 C# Node2D 上
return "overlay added"
```

GDScript **编译通过了**（这个调用是动态派发的），VM 在这一行中止该帧，`Callable::callp` 仍然回 `CALL_OK` 并给返回类型的默认值 ——
于是工具回 `ok` + `{"result":null,"result_type":"Nil"}`，**没有错误码、没有消息、没有建议**，而引擎 stderr 上有完整的一行
`SCRIPT ERROR: Invalid call. Nonexistent function 'addChild' in base 'Node2D (Match3Game.cs)'.`。
TASK-102 那轮真正抓住它的是**像素差 0** 与**场景树里没有 `ProbeOverlay`**。

修法用的是**引擎自己的错误处理器**（解析捕获已经在用的同一个 `add_error_handler` 钩子）：`GDScriptFunction::call()` 把中止的帧经
`_err_print_error(err_func, err_file, err_line, err_text, false, ERR_HANDLER_SCRIPT)` 报出来
（`modules/gdscript/gdscript_vm.cpp:3988`）。窗口恰好是**一次** `Callable::callp`（工具是同步的、在主线程），所以窗口里每一条
`ERR_HANDLER_SCRIPT` 都是这次调用造成的；用 `ERR_HANDLER_SCRIPT` 而不是 `ERR_HANDLER_ERROR`，正是为了**不**把脚本自己的
`push_error()` 算成失败（doctest 里有一条控制专门钉这一点）。引擎自己的打印**一字不少**（错误处理器列表在默认打印**之后**才被走，
`core/error/error_macros.cpp:125-141`），所以这是**纯追加**的捕获。

### A2 修前 / 修后并列（最小同批复现）

同一份六调用会话（`recovery\work\task103\sessions\session-x1.json`，其失败脚本是上面那段的**逐字**拷贝）**逐字不改**跑两次：

| tag | 修前（`runs\match3\task103-x1-before`） | 修后（`runs\match3\task103-x1-after`） |
|---|---|---|
| `g01-failing-addchild` | `ok` + `{"result":null,"result_type":"Nil"}`；`error_code:0`；无 `error_data_json` | **`-32000`** + `data.script_error`{`message`=引擎原文、`line`=7、`generated_line`=10、`function`=`_mcp_execute`、`script_path`=`gdscript://-9223371989626911104.gd`、`in_generated_body`=true、`error_count`=1、`column`=null、`messages`=[同一句]} + `data.suggestion` |
| `g03-control-add_child`（正控：同一段只把 `addChild` 改成 `add_child`） | `ok` + `{"result":"overlay added","result_type":"String"}` | **完全相同** —— 没有过度报错 |
| `g05-success-null`（无 `return` 的脚本） | `ok` + `{"result":null,"result_type":"Nil"}` | `ok` + `{"note":"…不是「有副作用」的证据…","result":null,"result_type":"Nil"}` |
| `g06-parse-fail` | `-32602` + `parse_error`{`line`=1、`generated_line`=4、`message`=Parse Error…} | **逐字相同** |
| `g02` / `g04`（场景树） | 失败后**没有** `ProbeOverlay`；成功后有 | 同 |
| 引擎 stderr | `SCRIPT ERROR: Invalid call. Nonexistent function 'addChild'…` / `at: _mcp_execute (gdscript://…:10)` | **仍然有同样的两行**（处理器是追加的） |
| trace 调用行（`seq=1`） | `ok:true`、`error_code:0`、无 `error_data_json` | `ok:false`、`error_code:-32000`、`error_message`、`error_data_json`（871 B，含 `script_error` + `suggestion`） |

### A3 两个必须写下来的决定

* **码取 `-32000`（`MCP_ERR_TOOL_STATE`）**，不是 `-32602`（那意味着**参数/语法**有问题，而脚本编译通过了 —— 会让调用者去修正确的语法），
  也不是 `-32603`（那意味着**本模块**坏了，而事实是调用者的代码失败、模块正确地观察到了它）。
  `-32000` 是本模块既有的「调用形式没问题、是这次执行没成」的约定（`not_implemented` / `no_scene` 同为 `-32000`），且 GDR-14 要求它带 `data.suggestion`。理由逐条写在源码里拒绝分支的旁边。
* **生成脚本的身份是「按 GDScript 自己的造法重建」，不是读 `Script::get_path()`**：后者是 `Resource::get_path()`、答的是**路径缓存**
  （`core/io/resource.cpp:118-120`），对未从资源加载的脚本恒为空 —— 本轮**实测**：运行时错误点名 `gdscript://-9223371484028730203.gd`，
  而 `get_path()` 答 `""`。引擎真正用的是 `GDScript::path`（无路径脚本在自己的构造函数里用实例 id 造出来，`gdscript.cpp:1337`），
  `GDScriptFunction::source` 就是它（`gdscript_compiler.cpp:3291`），所以从同一个对象按同样方式重建。
  答复里 `script_path` 与 `body_script_path` **两个字符串都给**，`in_generated_body` 的比较可审计。

### A4 两条仍然存在的边界（写下来，而不是假设）

* **没有列号**：引擎给错误处理器的只有行（`core/error/error_macros.h:63-77`），所以 `data.script_error.column` 与解析期的 `parse_error_column` 都是 `null`。这是钩子的性质，不是可以两选一的决定。
* **release 模板什么都看不到**：两个 VM 报错点都在 `#ifdef DEBUG_ENABLED` 里，而本模块所有门跑的都是 `target=editor`（`SConstruct:550/566-569`）。
  在 `target=template_release` 上 VM 什么都不打，本捕获会答「没看到错误」。这条边界写进了工具的注释与描述。

### A5 范围边界（有意不做）

`editor_execute_gdscript` **没有**接这条捕获。TASK-103 的范围就是 X-1 点名的那个工具；助手函数被提升进 `tool_helpers.{h,cpp}`，
正是为了让后续任务**一行**接线，而不是抄第二份规则。这条边界登记在 manifest §M-2。

---

## B. 第 16、17 款游戏（C#，只用 MCP 调用开发）

### B1 形态与开发方式（同一套脚手架，固化模板照用）

两款都从模板实例化（`tools\new_game.ps1 -Name towerdefense -Class TowerDefenseGame` / `-Name missilecommand -Class MissileCommandGame`），
**游戏内容全部由 MCP 调用写成**：`project_edit_script`（C# 载荷替换模板桩）、`editor_add_nodes_batch`（3 个静态节点一次建好）、
`editor_add_input_action`、`editor_save_scene`、`project_build_csharp`、`project_validate_scripts`；游戏相全部是 `running_game_*`。

| 游戏 | 场景里的静态节点 | 运行期新建的东西 |
|---|---|---|
| Tower Defense | `Background` / `Hud` / `Status` | **101 个路径格**（每条路径格一个 `ColorRect`，颜色沿路径渐变）+ 塔（放一座建一个）+ 32 个敌人精灵池 |
| Missile Command | `Background` / `Hud` / `Status` | 6 座城市 + 3 个炮台 + 三种精灵池（来袭弹 40 / 拦截弹 40 / 爆炸 40） |

两款都**故意重跑同名批量**（`e06`），`-32000` + 3 条 `conflicts`，且 `e05`/`e09` 读回的 `.tscn` **逐字节相同**
（TD `41de249a…` / 860 B；MC 同款做法）。两款都声明了一个输入动作（`td_auto_step` / `mc_auto_fire`），
并用 `running_game_run_test_scenario` 的**按键沿**证明它真的起作用（`InputSteps=1` / `InputShots=1`）。

### B2 调用数、判定分布、`facts_complete`（取自各自那一轮的 `report.json`）

| 游戏 | 相 | 调用 | 判定分布 | `facts_complete` |
|---|---|---|---|---|
| Tower Defense | 编辑器 | 14 | `failed=1`（声明的同名拒绝）、`ok_effect_observed=1`、`ok_file_effect_observed=4`、`ok_no_effect_observed=8` | **14/14** |
| Tower Defense | 游戏 | 131 | `failed=1`（声明的边界调用 `-32001`）、`ok_effect_observed=26`、`ok_file_effect_observed=78`、`ok_no_effect_observed=26` | **131/131** |
| Missile Command | 编辑器 | 14 | 同上 | **14/14** |
| Missile Command | 游戏 | 113 | `failed=1`（`-32001`）、`ok_effect_observed=17`、`ok_file_effect_observed=74`、`ok_no_effect_observed=21` | **113/113** |

两款每一轮的非 `ok` 判定都是**声明过的**：编辑器相那一次同名批量（D-3 的证据）与一条故意打在不存在属性上的边界断言（`-32001`，其 `expected` 在 manifest 里标了 `declared_boundary`）。

### B3 断言与「独立复算」

* **断言**：TD **77 PASS + 1 条声明的边界失败** = 0 失败；MC **73 PASS + 1 条声明的边界失败** = 0 失败（`logs\assert-{td,mc}-r3.txt`，逐属性分栏）。
* **Python 第二实现**：两款各有一份**从规则重写**的模拟器（`make_session_towerdefense.py` 的 `TSim`、`make_session_missilecommand.py` 的 `MSim`）。
  会话里每一个 `expected` 都取自它们 —— 生成器同时导出一份 `expectations-*.json` 清单，事后复算脚本把清单与响应里**实际回报的 `expected`** 逐条对齐：
  TD **75/75 + 1 条声明边界**、MC **71/71 + 1 条声明边界**，合计 **0 处不符**。
* **独立复算（后验，不 import 生成器、不看 `report.json`）**：
  * `recompute_readbacks.py` 只吃载荷**打印出来的** `Dump()`：TD 的 `MapHash` 由 ASCII 重推、`PathHash` 由**重新走一遍**导出的路径重推；
    MC 的 `CityHash` / `WorldHash` 由打印出来的城市位、两张导弹表、爆炸表与 `score`/`wave`/`steps` 重推。**两款 0 处不符**
    （TD：`MapHash=26299736`、`PathLength=101`、`PathHash=-577587427`；MC：`CityHash=29583456`、`WorldHash` `852442047` → 终局 `-1116815080`）。
  * `task102\pixel_recompute.py`（逐调用前后 PNG 对）与 `task102\frames_recompute.py`（保存帧链）：**报告与复算 0 处分歧**。

### B4 帧率无关的步进与「一个属性一个写者」

两款都是**浮点累加器**（`_autoAccum += delta * AutoClock`，不是 `(int)(delta*rate)`），`Elapsed` 是每帧 `+= delta` 的浮点秒表；
每款各有**两个生产者、两个属性**：`LastHookSteps`（`StepFrames` 钩子这次调用做了多少）与 `LastAutoSteps`（这一帧的时钟走了多少）。
两款都在时钟跑过 12 帧之后断言 `LastHookSteps` **仍是钩子写下的那个值**（TD `g84`、MC `g63`）。
**M3-4 的教训被写进断言本身**：两款的采样后面都跟着 `Steps gt 0` / `EnemiesSpawned(Spawned) gt 0` / `AutoTicks gte 1` 三条**会 FAIL 的硬断言** ——
「时钟在走而世界冻住」不再是一串常数，而是一条红。多帧采样：冻结基线 12 帧（各属性只有 1 个值、`Elapsed`/`Ticks` 各 12 个不同值）对自动时钟 30 帧。

### B5 缺陷清单

**工具缺陷（`modules\mcp_server`）：0 条。** 本轮唯一的模块改动是 A 段**主动**修 X-1（不是新发现），修完两变体重建、十道门重跑。

**游戏或驱动缺陷：4 条**

| id | 层 | 现象（证据） | 根因 | 处置 → 重跑结果 |
|---|---|---|---|---|
| **MC-1** | MC **载荷** | r1 的 `g02-assert-field-w` 回 `-32001`（`Property 'FieldW' on node '/root/Main' not found`）、`g12-readback-t0` 回 `-32000`「`Nonexistent function 'Dump' in base 'Node2D'`」 | `PosAt` 是实例方法却被 `static AddMissiles` 调用 → `CS0120` → `project_build_csharp` **exit 1**、`invalid_count=1` → **脚本没挂上**、根节点退化成裸 `Node2D` | `PosAt` 改 `static`；r2/r3 编译 exit 0、脚本挂上、全部断言通过 |
| **MC-2** | MC **会话** | r2 的 `g18b` 期望 `city` 实得 `ground`、`g19b` 期望 `battery` 实得 `ground`，而同刻 `ProbeValue` 两条全 PASS | 三条 `ProbeState` 断言写在探针循环**之后**，读到的是**最后**那次探针的状态 —— 与 PL-3 / K-1 / M1 同源：期望值必须引用它断言的那**一刻** | 每次探针后立刻断言它的两个属性；r3 全 PASS |
| **TD-1** | TD **会话** | r1 的 **11 条断言同时 FAIL**：`TowersPlaced` 期望 3 实得 0、`Gold` 期望 850 实得 0、`Won` 期望 true 实得 false、`Steps` 实得 544、`Lives` 实得 0、`Wave` 实得 1 | 「一整局」那一段**漏了 `ForceTestState` 调用**：三座塔建在上一段钉住的 `gold=0` 上、全部被 `no_gold` 拒绝，`StepFrames(4000)` 于是在无塔场地上把 5 条命跑光 | 补上 `g49-play-setup` 的 force 调用；r2/r3 全 PASS（`TowersPlaced=3`、`Gold=850`、`Won=true`、`Steps=306`、`Killed=15`、`Leaked=0`） |
| **TD-2** | TD **会话 / 证据设计** | r2 编辑器相像素列 **0/14**（`editor_add_nodes_batch` 任一方向都是 0），而 r1 是 1/14（213 012 px） | r2 **没有从模板重新实例化**：工程里已有上一轮建的三个静态节点 → 首次同名批量被 `-32000` 拒绝 → 「一次批量建好三个静态节点」这一步在本轮**根本没发生** | 归档（**先写 sha256 清单再 `Move-Item`**，全程零删除）+ 重新实例化后重跑；r3 恢复 1/14（213 012 px） |

**取证工具自身 1 条（`R-1`，明确**不是**模块缺陷）**：`recompute_readbacks.py` 第一版把 `Dump()` 行里 `last=<LastEvent>` 的片段也当成字段，
而 MC 的 `StepFrames` readback 恰好含 `incoming=0`，它覆盖了真正的 `incoming=<列表>`，解析器随后在 `m[1]` 上抛 `IndexError`。
修法：只取 `last=` 之前的部分，并让列表解析对字段数做断言；修后两款各 **0 处不符**。

---

## C. 收尾：重建、十道门、`accept_m1`、push

### C1 两变体重建（在模块提交之后）

| 变体 | 命令 | 真实退出码 | 自报版本 |
|---|---|---|---|
| mono | `modules\mcp_server\scripts\mcp057_build_mono.cmd` | **0**（952 s） | `4.8.dev.mono.custom_build.1c7f5c07a` |
| plain | `modules\mcp_server\scripts\build_local.cmd -Force` | **0**（1011 s） | `4.8.dev.custom_build.1c7f5c07a` |

两者都**串行**构建（D62），日志 `recovery\work\task103\logs\build-{mono,plain}.{out,err}.txt`（stderr 都是 0 字节）。

### C2 十道门（`tools\run_gates.ps1 -Tag task103 -RunGates`）

用 `-RunGates` 强制跑门（否则本轮 HEAD == 锚点、预检会判 `SKIP_REBUILD`，本条**必须**跑门）。

| 门 | 命令 | 真实退出码 | 读数 |
|---|---|---|---|
| g01 | mono `--headless --test --test-case=[MCPServer]*` | **0** | **157/157 passed, 0 failed** |
| g02 | mono `--headless --test` | **0** | **1583/1583 passed, 0 failed** |
| g03 | `check_tool_groups.py` | **0** | `TOOL-GROUPS CHECK PASS`（5681 B，sha256 `b83d79d3…`） |
| g04 | `check_contract_subset.ps1` | **0** | **`3/3 checks passed`**；编辑器 **154** / 游戏 **73**（契约 177） |
| g05 | `check_rename_map.py` | **0** | `RESULT: PASS (all checks green)` |
| g06 | `check_tautologies.py` | **0** | `TAUTOLOGY CHECK PASS`（每处命中都已 pinned） |
| g07 | `check_exit_propagation.py --probes` | **0** | — |
| g08 | `check_hardcoded_counts.py` | **0** | 116 处出现，`UNCLASSIFIED 0` |
| g09 | `check_engine_anchor.ps1 -VersionText 4.8.dev.mono.custom_build.1c7f5c07a` | **0** | `VERDICT=ANCHOR_EQUAL`、`DIFF_COUNT=0`、`RESULT PASS` |
| g10 | `accept_m1.ps1` | **0** | **`22/22 cases passed`** |

汇总：`runs\gates\task103\summary.txt`；日志 `recovery\work\task103\logs\gates-task103.txt`（父进程 exit 0）。

### C3 push 到 fork

```
git push origin feature/mcp-server-module-rebuild
To github.com:shiyukonghui/godot.git
   e041cae270..1f9d0cb1c9  feature/mcp-server-module-rebuild -> feature/mcp-server-module-rebuild
```

### C4 收尾后的进程与端口

无残留 `Godot*` 进程；本轮用过的端口对（9958/9959、9960/9961、9962/9963）无 **LISTENING**。**未改变机器显示或串流状态。**

---

## D. 铁律执行记录

| 铁律 | 本轮做法 |
|---|---|
| 1 **禁止一切 shell 重定向** | 所有日志由 `Start-Process -RedirectStandardOutput/-RedirectStandardError` 拥有（`capture.ps1` / `capture_ps.ps1` / `run_one.ps1` / `build_variant.ps1` / `run_engine.ps1` / `git_commit.ps1` / `new_game_run.ps1`），所有文本文件由 Python 写入器或编辑器工具写；**没有一处 `>` 或 `\|`-into-file** |
| 2 **破坏性命令默认拒绝** | 唯一的删除是 `recovery\work\task103\logs\` 下**具名绝对路径**的日志覆盖（每个助手自己那一份）；两个游戏工程是**移动**不是删除 —— `reset_game_project.ps1` 先写完整 sha256 清单再 `Move-Item` |
| 3 **构建与运行必须从 cmd 启动** | 两次构建、六次游戏会话、X-1 前后两次、十道门父进程、两次 git 提交全部经 `cmd.exe` |
| 4 **唯一端口 + 跑前查进程与端口** | 每次运行前 `tasklist` + `netstat` 清点；X-1 用 9958/9959、TD 用 9960/9961、MC 用 9962/9963，各轮不重叠 |
| 5 **会话文件先 Python + PS 5.1 双解析** | `check_session.py`（JSON/UTF-8/唯一 tag/`content_file` 可达/`code` 非空）与 `check_session_ps.ps1`（PS 5.1 自带解析器 + 计数）都在**起引擎之前**跑过；日志 `logs\check-session-{td,mc}*.txt` |
| 6 **迁移与删除先写 sha 清单存证** | `hash_tree.py` 为每次归档写出 `archive\*.manifest.json`（逐文件 size + sha256），然后才 `Move-Item`（TD 归档 1 次、MC 归档 2 次） |

---

## E. 遗留（不阻塞）

1. **`--import` 的关机期访问违例**本轮 **0 次**（六次导入全部 `IMPORT_EXIT=0`、`import.stderr.txt` 0 字节）；累计口径 **3/34**（待办 2 不变）。
2. TD 的塔**没有升级/出售**、MC 的炮台**不能选择**，两款都是各自经典规则的**最小完整子集**。
3. `ForceTestState` 仍允许钉出游戏本身到不了的状态（B-3 的成因），本轮以「会话不这么钉」处置，未在载荷里加防护。
4. X-1 的运行期捕获在 `target=template_release` 上看不到任何错误（两个 VM 报错点都在 `#ifdef DEBUG_ENABLED` 里）；该边界写进了工具注释与描述，本模块所有门跑的都是 `target=editor`。
5. `editor_execute_gdscript` **没有**接同一条运行时捕获（有意，见 §A5 与 manifest §M-2）：助手已提升到 `tool_helpers`，后续任务一行接线即可。

---

## F. 两仓 `git log --oneline -8` 与 `git status --short`

### F1 引擎仓 `F:\moonbit-hof-rs\godot-mcp\godot`（分支 `feature/mcp-server-module-rebuild`）

```
1f9d0cb1c9 modules/mcp_server: task103 - REBUILT-2C-MANIFEST gains the 2c-12 section: the runtime-error contract of running_game_execute_gdscript (the -32000 code and why the two neighbouring codes are wrong for it, the reconstructed script identity and why Script::get_path() cannot be it, the two boundaries that remain - no column from the handler, and a release template reporting nothing because both VM sites are inside DEBUG_ENABLED), the append-only description override with the contract's six shape quantities unchanged (177/6/1.22.0/154/73/idempotent, sha bd68e804), the minimal same-batch reproduction with its before/after answers and its three controls, the ten gates with their real exit codes and accept_m1 22/22 on the binary rebuilt at 1c7f5c07a, the deliberate boundary that leaves the editor executor alone, and the iron rules as they were actually followed
1c7f5c07a1 modules/mcp_server: task103 (X-1) - a GDScript body that compiles and then fails while it runs is a structured refusal now (-32000 + data.script_error + data.suggestion) instead of an ok with a null result, and a successful body that returned no value carries a note, so "ok" can no longer be read as "the script ran"
e041cae270 modules/mcp_server: task099 - REBUILT-2C-MANIFEST gains the 2c-11 section: ...
0fbd5ec4cb modules/mcp_server: task098 - MCP-TRACEABILITY section 7 is aligned with the D-1 closure
094b071f9b modules/mcp_server: task097 - REBUILT-2C-MANIFEST gains the 2c-10 section: ...
2385fe2fb5 modules/mcp_server: task097 (D-3) - a requested node name the target parent already carries is now refused instead of silently renamed, ...
95aa1d8984 modules/mcp_server: task096 - MCP-TRACEABILITY gains section 7: ...
8b9dd9a72b modules/mcp_server: task094 - D-2 is a load-sensitive readiness predicate, not a defect: ...
```

`git status --short`：**空**；`git rev-parse HEAD` = `1f9d0cb1c983301d4efa575c16986c551df23600`；
`git rev-parse refs/remotes/origin/feature/mcp-server-module-rebuild` = `1f9d0cb1c9…`（**与远端同级，push 已生效**）。

### F2 主仓 `F:\moonbit-hof-rs`（分支 `master`）

本轮**一个提交**：`--- rev-parse HEAD `（236 个文件 / 21784 行增 / 2 行删）—— 两款游戏工程与它们的会话、载荷、生成器，
`recovery\work\task103\` 的全部脚本与日志，`GAME-LOOP-LOG.md` 与 `DECISIONS.md` 的追加，以及本报告。
提交后立刻取的两仓快照逐字存放在 `recovery\work\task103\logs\git-final-main.txt`。

`git log --oneline -8`（主仓）：

```
  --- log --oneline -8 
  5a36457 feat(godot-mcp): TASK-103 (D151) - tool defect X-1 is fixed at its root and both engine variants are rebuilt at the module commit, and the 16th and 17th C# games are delivered through MCP calls only
  9733cae docs(godot-mcp): TASK-102 - the report's closing boundary is restated so it cannot be made stale by the task's own doc-only follow-ups: the snapshot right after the report commit still has the six helper-owned log entries, they are committed by the report commit itself, the housekeeping commit that follows cleans the two lines the commit helper writes after its own commit, and the working tree is empty from then on
  b365654 docs(godot-mcp): TASK-102 - the helper-owned logs of the commit and two-repo capture scripts are committed after the fact so the working tree is clean; no content change
  3b2958e docs(godot-mcp): TASK-102 - the report: the two new C# games with their real call counts, verdict distributions, assertion tallies and independently recomputed pixel columns, the seven defects their first runs caught (a payload whose world-edge collision reused a tile-relative formula that C# integer truncation turns into a two-tile bounce, a payload whose jump did not clear OnGround, a session whose pinned goal made the expected hash describe a different state than the one it asserted, a session that guessed the default board's cell value instead of recomputing the LCG that generates it, a session that modelled three refusals on three fresh boards while the run accumulated them on one, a session whose positive-control GDScript used the C# method name addChild, and a session whose auto-clock board had exactly one legal swap so thirty frames of sampling watched a frozen board while every assertion still passed), each with its fix and re-run, the tool observation that a script error inside running_game_execute_gdscript returns ok with a null result and reaches only the engine's stderr (recorded, not fixed, because fixing it would change the module and force a rebuild plus the ten gates), and the gate runner's doc-only preflight that skipped the ten gates because not one module byte changed
  3b9d55c feat(godot-mcp): TASK-102 (D150) - the 14th and 15th C# games are delivered through MCP calls only (Platformer: a 40x30 course of 20-pixel tiles with integer kinematics -- x += vx, resolve the horizontal overlap, vy += 1 clamped to 16, y += vy, resolve the vertical overlap -- so a jump arc is an exact integer sequence, with left/right running, gravity, landing, an optional mid-air second jump, platform collision, collectibles that score, a pit that costs a life and respawns, and a goal tile that wins; Match-3: an 8x8 six-colour board with an orthogonal swap that a line of three or more accepts and a board-identical refusal otherwise, a run scan in both directions, per-column gravity, a linear congruential refill, chain-weighted scoring and a target/move-limit pair that ends the game either way), both with a float-accumulator clock, both with two single-writer increment properties, both replaying the D-3 duplicate-name batch for its -32000 refusal, both with a second Python implementation of their own rules whose outputs are the session's assertion literals, both with a post-hoc recomputation that derives the printed map's and the printed board's hash from the printed ASCII alone, and both with the frame-by-frame parabola (Platformer) and the exact post-cascade board (Match-3) recomputed independently
  af12574 docs(godot-mcp): TASK-101 - the two run logs the commit helper itself owns are committed after the fact so the working tree is clean; no content change
  5e43af0 docs(godot-mcp): TASK-101 - the report: the two new C# games with their real call counts, verdict distributions, assertion tallies and independently recomputed pixel columns, the four defects their first runs caught (a session that read a fact from the wrong moment, a payload that consumed the enemy it walked into, a session that asserted a probe it never made, and a pinned board whose fuse had already decided the level so the 30-frame sample watched a frozen board while every assertion still passed), each with its fix and re-run, and the gate runner's doc-only preflight that skipped the ten gates because not one module byte changed
  26553df feat(godot-mcp): TASK-101 (D149) - the 12th and 13th C# games are delivered through MCP calls only (Sokoban: a grid push game with box and goal counts, the classic corner plus 2x2 simple deadlock test, level completion and an undo that rolls the player and the box back together; Bomberman: a 13x9 field of hard walls, ten destructible bricks and two enemies, grid movement, a fixed-fuse bomb, a blast that is stopped by a wall and takes the FIRST brick each way, a chain reaction, a deterministic greedy enemy chase, lives and respawn, and a win that one blast can deliver), both with a float-accumulator clock, both with two single-writer increment properties, both replaying the D-3 duplicate-name batch for its -32000 refusal, both with a second Python implementation of their own rules whose outputs are the session's assertion literals, and both with a post-hoc recomputation that derives the printed board's hash and every blast cell from the printed ASCII alone
```

`git status --short`（取快照那一刻）：

```
  --- status --short 
   M godot-mcp/recovery/work/task103/logs/git-main.err.txt
   M godot-mcp/recovery/work/task103/logs/git-main.out.txt
  ?? godot-mcp/recovery/work/task103/final_snapshot.ps1
  ?? godot-mcp/recovery/work/task103/logs/git-final-main.cmd
  ?? godot-mcp/recovery/work/task103/logs/git-final-main.err.txt
  ?? godot-mcp/recovery/work/task103/logs/git-final-main.txt
```

那 6 条是**收尾助手自己写的**（`git_commit.ps1` 在提交之后才写自己的 stdout/stderr 日志，`final_snapshot.ps1` 写自己的脚本与输出），
由紧随其后的 housekeeping 提交收进仓；从那次提交起工作树为空。

### F3 引擎仓最终快照（同一次快照里的另一段，逐字）

`git rev-parse HEAD` = `--- rev-parse HEAD `
`git rev-parse refs/remotes/origin/feature/mcp-server-module-rebuild` = `--- rev-parse refs/remotes/origin/feature/mcp-server-module-rebuild `（**与远端同级，push 已生效**）

`git log --oneline -8`（引擎仓）：

```
  --- log --oneline -8 
  1f9d0cb1c9 modules/mcp_server: task103 - REBUILT-2C-MANIFEST gains the 2c-12 section: the runtime-error contract of running_game_execute_gdscript (the -32000 code and why the two neighbouring codes are wrong for it, the reconstructed script identity and why Script::get_path() cannot be it, the two boundaries that remain - no column from the handler, and a release template reporting nothing because both VM sites are inside DEBUG_ENABLED), the append-only description override with the contract's six shape quantities unchanged (177/6/1.22.0/154/73/idempotent, sha bd68e804), the minimal same-batch reproduction with its before/after answers and its three controls, the ten gates with their real exit codes and accept_m1 22/22 on the binary rebuilt at 1c7f5c07a, the deliberate boundary that leaves the editor executor alone, and the iron rules as they were actually followed
  1c7f5c07a1 modules/mcp_server: task103 (X-1) - a GDScript body that compiles and then fails while it runs is a structured refusal now (-32000 + data.script_error + data.suggestion) instead of an ok with a null result, and a successful body that returned no value carries a note, so "ok" can no longer be read as "the script ran"
  e041cae270 modules/mcp_server: task099 - REBUILT-2C-MANIFEST gains the 2c-11 section: the gate runner's doc-only preflight (one classifier, dot-sourced from the module's own anchor judge, anchor taken from the built binary's --version, committed range plus working tree, and the two measured cases with all ten gates green in the compile-input one), the third live --import shutdown access violation with its 24 controlled probes at 0 crashes, and the explicit reason why the change to tools/run_gates.ps1 cannot reach either variant (it is a main-repository script, so the engine tree has no byte to rebuild)
  0fbd5ec4cb modules/mcp_server: task098 - MCP-TRACEABILITY section 7 is aligned with the D-1 closure
  094b071f9b modules/mcp_server: task097 - REBUILT-2C-MANIFEST gains the 2c-10 section: the name-conflict policy the section registers (the default refusal with its complete conflict list, its error code and its opt-in rename), the contract's six shape quantities after the append-only override (177/6/1.22.0/154/73/idempotent, sha 64ddce9f), the ten gates and accept_m1 22/22 with their real exit codes, and the three iron-rule deviations of this task recorded rather than hidden
  2385fe2fb5 modules/mcp_server: task097 (D-3) - a requested node name the target parent already carries is now refused instead of silently renamed, so a replayed editor phase can no longer write a whole duplicate node layer into a scene; editor_save_scene reports the duplicates a batch made under an explicit rename instead of saving them silently
  95aa1d8984 modules/mcp_server: task096 - MCP-TRACEABILITY gains section 7: what the evidence chain is when the pixel diff is unavailable, and how the ledger is to be read then; the section also carries the re-localisation of D-1 (the duplicate node layer a replayed editor phase writes into a scene), which is why the three older games' pixel column says unavailable rather than 0
  8b9dd9a72b modules/mcp_server: task094 - D-2 is a load-sensitive readiness predicate, not a defect: the accept_m1 wait now asks the main loop to advance (frame_count strictly increasing six samples in a row) instead of asking it to be faster than 20 fps, so the suite is 22/22 solo and 22/22 under eight CPU burners
```

`git status --short`（引擎仓）：**--- status --short **

### F4 快照之后

快照记录的是「提交完成、housekeeping 尚未发生」的那一瞬。§F2 列出的那 6 条助手自有文件由 housekeeping 提交收尾；
之后两仓的工作树都为空，两仓 HEAD 分别是主仓 `5a364575641a6eff7422fbc990348ca8ca781dee` 与引擎仓
`1f9d0cb1c983301d4efa575c16986c551df23600`（= 远端）。
