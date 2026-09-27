# ACCEPTANCE-TASK-105 — 独立验收报告

**验收对象**：`F:\moonbit-hof-rs\godot-mcp` —— MCP 工具链 + 20 款 C# 经典小游戏复刻 + 可溯源标准
**验收员**：独立验收子代理（无实现者上下文，未采信任何既有结论）
**日期**：2026-09-27
**权限**：只读 + 只写本文件。所有命令均未改动被验收对象；检查脚本与临时产物一律写在 `%TEMP%\acc105\`。

**结论：`fail`** —— 工具链与溯源标准本身经得起独立复核（138 份 trace / 6565 次调用 / 20 款游戏的
像素列与台账数字**逐项复现**），但 **Snake 的「最终」运行里存在 3 条未声明的失败断言**，且**三份
文档对同一批断言的结论互相矛盾、其中两处是明确的虚假陈述**。这一条直接落在本次验收的核心命题
（「是否有作弊门 / 是否把证据缺失当通过 / 有无未声明的行为变更或未覆盖路径」）上，因此不能判 pass。

---

## 0. 一句话结论（按验收命题分列）

| # | 命题 | 判定 | 依据强度 |
|---|---|---|---|
| ① | 20 款游戏真的由 MCP 调用驱动（不是写好文件后伪装） | **成立** | 证据支持（字节级） |
| ② | 溯源标准（`MCP-TRACEABILITY.md` §2/§3）在真实 trace 里可查、台账判定可手工复核 | **成立** | 证据支持（逐字段 + 重算） |
| ③ | 是否有作弊门（恒真断言 / 改断言过门 / 静默失效的检查） | **部分不成立** | 证据支持（发现真实 FAIL；发现一处 post-hoc 改判） |
| ④ | 工具缺陷清单与其前后对比（D-3 / X-1）可信、可复现 | **成立** | 证据支持（修前修后 + 源码 + git） |
| ⑤ | 有无未声明的行为变更或未覆盖路径 | **不成立（发现 1 类 3 条）** | 证据支持 |
| ⑥ | `ok` 是否真的意味着操作有效 | **成立，但边界必须按文档读** | 证据支持 + 一处须声明的边界 |

---

## 1. 验收方法

* 以只读检查为主：解析 trace/session/report，重算 sha256，重算像素差，跑模块自带只读门脚本。
* **未修改被验收对象一个字节**（含 `.godot` 缓存、`runs\gates\`）；所有输出重定向到 `%TEMP%\acc105\`，
  用 `-OutFile` / Python 写文件，未使用 shell 重定向写日志。
* **构造反例 3 处**（都在临时副本上做，见 §4 检查 7/8/9）：证明像素复算与断言复算**不是空转**。
* 未做的事（如实声明）：**没有重新启动引擎跑一次真实会话**（会写入工程 `.godot` 缓存＝改动被验收对象）。
  因此「传一个不存在的属性是否真回错误」这一条我采信的是**运行产物里的既有反例**（每一款都有一条
  `-32001` 声明边界调用）与 **X-1 的修前/修后原始响应**，而不是我当场发出的调用。置信度见 §4 检查 10。

---

## 2. 逐项结论

### ① 20 款游戏是否真的由 MCP 调用驱动 —— 成立（字节级）

**做法**：对 20 款游戏的「最终运行」，从 `trace-editor.jsonl` 取出每一次 `project_create_script` /
`project_edit_script` 的**实际载荷**（超限载荷走 `args_sidecar` 完整旁路文件），把 `content`
做 sha256，与 `tools\sessions\<game>\payload\*.cs` 和 `projects\<game>\src\*.cs` **三方逐字节比对**。

**结果**（`check2_payload_bytes.py`，20/20 全部命中）：

```
game                 run                                      checked  byte-identical(proj+payload)
pong                 runs\pong\pong-clean-task097                 3     3 OK
breakout             runs\breakout\breakout-clean-task097         3     3 OK
snake                runs\snake\snake-clean-task097               3     3 OK
tetris               runs\tetris\tetris-task096-r2                2     2 OK
spaceinvaders        runs\spaceinvaders\si-task097-r1             1     1 OK
... （共 20 行，全部 OK）
no problems: every script call's content == session payload file == projects/<game>/src file
```

**补充证据**：

* 每一次脚本调用的 `file_effects[].after.sha256` 与**盘上文件的真实 sha256** 全部相等（20/20，
  `check13_effects_png.py`：`MISMATCHED file_effect sha vs disk: none`）。
* 每一次调用的 `before.sha256` 与 `after.sha256` 不同（写确实发生，不是"调了个空"）。
* 每款游戏的运行目录里有 **84 ~ 466 个 PNG**（`shots-editor\` + `shots-game\`）与两份 trace。
* 20 款游戏工程全部是 C#：`cs` 文件 1~3 个、`gd` 文件 **0 个**、每款都有 `.csproj`。
* trace 的 `trace_opened.version` 记录了产生该运行的引擎二进制锚点（`95aa1d898` / `cf554ef58` /
  `2385fe2fb` / `e041cae27` / `1c7f5c07a`），与 `run_gates.ps1` 预检读到的**盘上二进制**锚点吻合。

**「关键反例」复核（任务书要求的那一条）**：Pong 的 `c/e04-edit-game` 是 `project_edit_script`
（`res://src/PongGame.cs`），其 `args_bytes=9464 → args_truncated=true`，旁路文件
`runs\pong\pong-clean-task097\trace-editor.sidecar\0026-args.json`：

```
SIDECAR seq=26 tool=project_edit_script bytes=9464 sha=168da6eea2c21e28 rel=trace-editor.sidecar/0026-args.json
   file exists=True recomputed_sha_match=True recomputed_bytes=9464
RAW CALL LINE seq=26: id=125 tool=project_edit_script ok=True err=0
  file_effect_status=observed_no_change rows=1
    kind=write path=res://src/PongGame.cs changed=False failed=False
      before=dc8bf3601a828b94 after=dc8bf3601a828b94
      ACTUAL FILE sha256[:16]=DC8BF3601A828B94  ==after? True
```

即：**旁路载荷（读侧重算 sha 通过）== 会话 payload 文件 == 盘上 `src\PongGame.cs`**，并且同一行的
`file_effects` 把这次调用的落点、前后 sha、是否变化都钉死。这条链是闭合的。

### ② 溯源标准是否真的成立 —— 成立

**(a) 字段齐备性（`check1_trace_fields.py`，全量而不是抽查）**

```
trace files: 138 tools/call lines: 6565
aggregate missing-field counts: {}
files with any missing field or nonzero malformed: (空)
```

对**每一条** `tools/call` 行核对：`id`（存在且非 null）、`tool`、`args`、`method`、
`ok=true → result_json` / `ok=false → error_data_json`+`error_code`、`file_effect_status`、
`file_effects`、`capture` 对象、**同 `seq` 的 `event=capture` 行**、`duration_ms`、`ts_ms`。
**6565 条调用 0 条缺字段、0 条格式错误行**。这比 `MCP-TRACEABILITY.md` §3.1 的 `facts_complete`
口径更严（我额外要求了 `id` 非 null 与 capture 行必须存在）。

**(b) 台账判定可被 trace 原文手工复核（挑 3 条逐字段对照）**

用 `mcp_trace_ledger.py` 对同一份 trace 现场重放（写入 `%TEMP%`，不碰仓库），然后**逐字段**把
台账行与原始 JSONL 行、capture 行、sidecar 文件对照：

| seq | 工具 | 原始行 | capture 行 | 台账行 | 一致 |
|---|---|---|---|---|---|
| 8 | `editor_delete_node` | `ok=true err=0 file_effect_status=no_mutation rows=0` | `changed=True changed_pixels=465 frames_waited=3` | `scene=changed file=none verdict=ok_effect_observed facts_complete=True` | ✔ |
| 26 | `project_edit_script` | `ok=true args_bytes=9464 args_truncated=True`，`file_effects` 一行 `changed=False`，after sha 与盘上文件相等 | `changed=False changed_pixels=0` | `args_evidence=sidecar_verified file=unchanged verdict=ok_no_effect_observed facts_complete=True` | ✔ |
| 30 | `editor_add_nodes_batch` | `ok=False err=-32000`，`error_data_json` 2118 B（含 `conflicts` 8 条 + `suggestion`） | `changed=False` | `verdict=failed scene=unchanged file=none flags=['error_suggestion'] facts_complete=True` | ✔ |

我还**独立重算**了 pong 清洁轮的像素列（不调用 `report.json`）：

```
[editor]  calls=45 scene_effect={'unchanged': 42, 'changed': 3} file_effect={'none': 33, 'changed': 4, 'unchanged': 8}
[game]    calls=29 scene_effect={'unchanged': 18, 'changed': 11} file_effect={'none': 15, 'changed': 14}
```

与 `GAME-LOOP-LOG.md` 的「编辑器 3/45、游戏 11/29（合计 14/74）」**逐值一致**。

**(c) 全量台账重放 vs 台账声称的数字（`check7_all_ledgers.py`）**

20 个「最终运行」逐一现场重放 `mcp_trace_ledger.py`，`calls` / `malformed_lines` / `facts_complete` /
判定分布全部与 `GAME-LOOP-LOG.md` 对得上，例如：

```
tetris         6 + 36 = 42   facts 6/6 + 36/36      claims 42/42
spaceinvaders  15 + 44 = 59  facts 15/15 + 44/44    claims 59/59
asteroids      16 + 55 = 71  facts 16/16 + 55/55    claims 71/71
lunarlander    14 + 216 = 230 facts 14/14 + 216/216 claims 230/230
（20/20 全部一致；malformed_lines 全 0；facts_complete 全 100%）
```

**(d) 像素列全量独立复算（`check11_all_pixels.py` + `pixel_recompute.py`）**

对 20 个最终运行逐对重算 PNG 像素差（engine 规则 + 更严的 any-byte 规则），**20/20 与台账声称的
数字完全一致**，且 `reported changed_pixels != 重算值` 的条数 **editor=0、game=0**：

```
pong 3/45 11/29 | breakout 2/55 12/34 | snake 0/71 13/31 | tetris 0/6 11/36 | si 1/15 11/44
asteroids 1/16 15/55 | pacman 1/16 14/64 | frogger 1/16 16/74 | flappy 1/14 21/78
2048 1/16 25/113 | minesweeper 1/14 20/141 | sokoban 1/14 28/176 | bomberman 1/14 44/219
platformer 1/14 39/214 | match3 1/14 21/131 | td 1/14 30/131 | mc 1/14 20/113
rtype 1/14 86/209 | pb 1/14 28/143 | ll 1/14 40/216
ALL CLAIMED PIXEL COLUMNS REPRODUCED, 0 ledger-vs-recompute mismatches: True
```

**(e) 副本（D-3）与场景树**：pong / breakout / snake 的清洁前场景树分别有 16 / 40 / 74 个
`@ColorRect@`/`@Label@` 出现次数（= 8 / 20 / 37 个节点，与 D-3 的两种口径都对得上），
清洁后 **0 个**；其余 17 款最终运行的场景树里 **0 个** `@` 自动名节点。

### ③ 是否有作弊门 —— 断言门是真的能失败；但发现 1 处 post-hoc 改判

**(a) 断言门不是恒真。** 全量解析 20 个最终运行的全部响应文件（`check5_assertions.py`）：

```
TOTAL passed=1358 failed=9 errors=0
```

9 条 FAIL 里 6 条是**文件名与 note 都声明的 must-fail / boundary**（pong `g12-*-must-fail`、
`g27-screen-text-miss`；breakout `g09-*-must-fail`、`g24-*-must-fail`；snake `g04-*-must-fail`、
`g26-*-must-fail`）。允许失败的断言**确实返回 `passed:false`**，例如：

```
g12-paddle-up-2-must-fail.json → all_passed=false, failed=1,
  expected position eq {"x":24.0,"y":226.0}, found {"x":24.0,"y":8.0}
g26-wall-assert-must-fail.json → passed=false, expected "self", found "wall"
```

**(b) 工具的恒真门自带插入探针且真的响**（模块门 `check_tautologies.py`）：

```
TAUTOLOGY CHECK PASS (every hit is pinned; scanned=2 file kind(s) under 2 root(s))
PROBES: 18/18 (14 declared spelling(s) + 4 near miss(es))
```

4 条 near-miss 控制（`$a.Count -eq 0 -or $aDrained` 等）**没有**被误报，说明探针不是恒 PASS。
**须声明的边界**：该门只扫 `modules\mcp_server` 下的 `.ps1`/`.py`（docstring 自己写明
"spelling-visible only"），**不扫游戏会话里的断言**。

**(c) 反例构造：像素复算器与断言复算器都不是空转**（全在 `%TEMP%` 的副本上做）

| 反例 | 手法 | 结果 |
|---|---|---|
| `check8_mutation.py` | 把 trace 里 `changed_pixels` 512 → **999999** | 复算器报 `reported=999999 recomputed=512`，mismatch **1** |
| `check9_png_mutation.py` | 往一张原本"零差"的 after PNG 里涂 **6×6 白块（36 px）** | 复算器报 `any=36 engine=36 reported=0`，非零列 11/29 → **12/29** |
| `check10_recompute_mutation.py` | 把 `g48-assert-x` 的 `actual` 0 → **20** | 复算器报 `expected=0 actual=20 <<< MISMATCH`，`TOTAL RECOMPUTATION MISMATCHES: 1` |

`check9` 尤其关键：它证明像素差读的是**真实像素**，不是抄 trace 里的 `changed`。

**(d) 但发现一处 post-hoc 改判（详见缺陷 D-1）**：Snake 的 `g19-turn-down` 与
`g22-self-collision` 在**最终运行**里失败、文件名不带 `-must-fail`、会话 note 写的是**正向意图**，
后来在 `TASK-097-REPORT.md` 里被追认为「按设计失败」。这是"为过门而改说法"，属作弊门类。

### ④ 工具缺陷清单与前后对比（D-3、X-1）—— 可信且可复现

**D-3（同名批量默认拒绝）**

| | 证据 |
|---|---|
| 修前 | `runs\pong\d3-before`（引擎 `cf554ef58`）：`e03` 返回 `status:"ok"`；`e06` **再次同名批量仍回 ok**，并把节点改名成 `@ColorRect@20956`，该副本随后被写进场景 |
| 修后 | `runs\pong\d3-after` / `d3-after-r2`（引擎 `95aa1d898`）：`e04`/`e07` 回 `-32000` + `data.conflicts`（含 `node_path`/`existing_node_path`）+ `data.suggestion`；`e11` 显式 `on_name_conflict:"rename"` 时才改名，并在 `renamed_count`/`renamed[]`/`created[i].name_conflict` 里如实报告 |
| 代码 | `tools\editor_node_batch_write.cpp:436` `refuse_name_conflicts = p_on_name_conflict != String("rename")`、`:464 extra["on_name_conflict"]="refuse"`、`:730 result["on_name_conflict"]=...`；`editor_write_scene_editor.cpp:346-366` 报告重复 |
| git | 引擎仓 `2385fe2fb5 modules/mcp_server: task097 (D-3) - a requested node name the target parent already carries is now refused instead of silently renamed...` |
| 在当前运行里复现 | 17 款最终运行（Space Invaders 起）**每一次**第二次同名批量都回 `-32000`，`conflicts` 恰为 3 条（SI 5 条），且前后的 `project_read_text_file` sha **逐字节相同**；场景树 0 个 `@` 名 |

**X-1（GDScript 运行期错误没有结构化错误）**

| | 证据 |
|---|---|
| 修前 | `runs\match3\task103-x1-before`（引擎 `2385fe2fb`）：`g01-failing-addchild.json` = `{"result":null,"result_type":"Nil"}`，即 **ok + 空结果**；诊断只在 `engine-game.stderr.txt` |
| 修后 | `runs\match3\task103-x1-after`（引擎 `e041cae27`）：同一步回 `-32000`，`data.script_error` 带引擎原文 `"Invalid call. Nonexistent function 'addChild' in base 'Node2D (Match3Game.cs)'."`、`line=7`、`script_path=gdscript://…gd`、`function=_mcp_execute`、`error_count=1`，外加 `data.suggestion`；`g05-success-null` 也补了 `note`，明确「null 结果不是有副作用的证据」 |
| 代码 | `tools\running_game_script_execution.cpp:356-386`（`script_error` 字典、九个子字段）、描述同步进 `:458` |
| git | 引擎仓 `1c7f5c07a1 modules/mcp_server: task103 (X-1) - a GDScript body that compiles and then fails while it runs is a structured refusal now (-32000 + data.script_error + data.suggestion) instead of an ok with a null result...` |
| 二进制锚点 | `run_gates.ps1 -PreflightOnly` 实测盘上二进制 `--version` = `4.8.dev.mono.custom_build.1c7f5c07a`（= X-1 修复锚点），HEAD `1f9d0cb1c` 仅一份 `.md` 差异 → `ANCHOR_STRUCTURAL_EQUIVALENT` + `SKIP_REBUILD`；引擎仓 `git status` 为空 |

### ⑤ 未声明的行为变更 / 未覆盖路径 —— **不成立**（见缺陷 D-1）

`check6_undeclared.py` 把「失败断言」按「文件名是否含 `must-fail`」与「会话 note 是否声明为边界/
注定失败」两路判定，20 款最终运行里只有 Snake 有**未声明**的失败：

```
snake  g19-turn-down       NO  scenario:DirectionY eq 1.0 -> -1
snake  g22-self-collision  NO  scenario:GameOver eq True -> False
snake  g22-self-collision  NO  scenario:LoseReason eq self ->
UNDECLARED failing assertions in final runs: 3
```

**未覆盖路径**：Snake 的**自撞判负**（`LoseReason="self"`）在最终运行里从未被走到 ——
`runs\snake\snake-task093-r6\engine-game.stdout.txt` 与清洁重放里
`SNAKE_SELF` 出现 **0 次**（对照：r3 / r4 / r5 各 3 次），只有 `SNAKE_WALL`；同轮的读回
`g23-self-readback` = `{"result":"over=false reason= score=0 status_visible=false"}`。
**同一轮**的 `runs\snake\snake-task093-r6\ledger-game.txt` 其实**已经把它标出来了**：

```
19  139  running_game_run_test_scenario  452  True  0  unchanged  changed  scenario_assertion_failed  ok_file_effect_observed
22  142  running_game_run_test_scenario  652  True  0  unchanged  changed  scenario_assertion_failed  ok_file_effect_observed
```

（清洁重放 `snake-clean-task097` 同样 4 条 flagged：2 条 must-fail + g19 + g22。）

### ⑥ `ok` 是否真的意味着操作有效 —— 成立，但必须按文档读

* **`ok` ≠ 「它断言的事成立」**：台账 `result_flags` 会把 `passed:false` 的调用标成
  `assertion_failed` / `scenario_assertion_failed`。我在 20 个最终运行的 ledger 里核到
  `td-task103-r1: 11` 条（正是 TD-1「11 条同时 FAIL」那条），以及 snake r6 的 4 条 ——
  **工具确实把「成功但结论为否」挑出来了**。
* **`ok` ≠ 「脚本执行成功」**：X-1 修前正是反例；修后同一类失败回 `-32000`。修后的成功路径还
  对 `result == null` 加 `note`，明确「不能当作副作用的证据」。
* **`ok_no_effect_observed` 不等于「这次调用没用」**：文档 §3 的读法是正确的（读工具本来就不动画面）；
  我核到的 `ok_no_effect_observed` 绝大多数是 `editor_get_node_properties` /
  `running_game_get_node_properties` 这类读调用。
* **声明的边界确实被声明而不是静默缺失**：`file_effect_status` 空串 = 无记录器；`not_tracked_deferred`
  = 延迟窗口一帧未观测；`args_sidecar_missing/mismatch` = 旁路证据不可核；失败行缺
  `error_data_json` = 旧版本 trace。这些在 138 份 trace 里都能区分，我没有找到「缺失被读成没变」的例子。
* **须声明的边界（我的判定）**：`ok` 只在**调用被应答**这一层为真；一切"有效"结论都必须落到
  `file_effects` 的 sha / capture 的像素差 / `result_json` 的 `passed` 三选一上。文档就是这么写的，
  台账也是这么算的 —— 这一条我认为**成立**。真正的问题不在读法，而在**报告层没有按这个读法写**
  （缺陷 D-1）。

---

## 3. 缺陷清单

### D-1（`blocking`）Snake 最终运行含 3 条未声明失败断言 + 自杀判负路径无证据 + 三份文档互相矛盾

* **事实**（全部可复现）
  * `runs\snake\snake-task093-r6`（`GAME-LOOP-LOG.md` 与 `TASK-093-REPORT.md` 共同引用的
    **Snake 最终轮**）与 `runs\snake\snake-clean-task097` 里：
    `g19-turn-down`（`DirectionY eq 1.0` 实得 `-1`）FAIL、
    `g22-self-collision`（`GameOver eq true` 实得 `false`；`LoseReason eq "self"` 实得 `""`）FAIL 2 条。
  * 两条的文件名**不带** `-must-fail`；会话 note 是**正向意图**：
    g19 = "and the other direction is accepted too"；
    g22 = "self-collision is a loss and the reason names it"。
  * 该轮 `SNAKE_SELF` 在引擎 stdout 里出现 **0 次**（r3/r4/r5 各 3 次），
    `g23-self-readback` 回 `over=false reason= score=0` → **自撞判负这条规则在最终证据里没有被走到**。
  * 该轮自己的 `ledger-game.txt` 已把 seq 19 / 22 标为 `scenario_assertion_failed`。
  * 会话的钉板本身也不成立：`g20-aim-self` 传
    `ForceTestState("10,10|9,10|8,10|7,10|6,10;dir=1,0;food=0,0")`，头在 `10,10`、颈在 `9,10`，
    而 `dir=1,0` 让头走向 `11,10` —— **离开自己的身体**，不可能自撞
    （`SnakeGame.cs:418-434` 的自撞判定用的是 `nx = HeadX + DirectionX`）。
* **矛盾陈述**
  1. `recovery\reports\TASK-093-REPORT.md:86`：
     `| 自撞判负 | g20 / g22-self-collision | LoseReason eq "self" passed |` ← **与产物相反**。
  2. `GAME-LOOP-LOG.md:19`（Snake 行）：
     「网格移动/食物增长/**自撞**/撞墙/计分全部由断言钉住（… `LoseReason=self`、`LoseReason=wall`）」
     ← **自撞那一半没有证据**。
  3. `GAME-LOOP-LOG.md:260`（S-3 行）：
     「r6：墙测 `LoseReason=wall`、自撞测 `LoseReason=self`，两条同时成立」← **与 r6 产物相反**
     （`g25-wall-collision` 确实 PASS，`g22` 没有）。
  4. `recovery\reports\TASK-097-REPORT.md:125`：
     「Snake `g04/g06/g08/g13/g14/g15/g17/g18/g19/g22/g25/g26`（含…Snake 的 `g19/g22/g26`）」
     —— 一边说这些断言"仍然通过"，一边把 `g19/g22` 追认为「按设计失败」。
     这与 (1) 直接冲突，也与会话 note 的正向意图冲突，且**违背了本仓库自己的命名约定**
     （其余每一处故意失败都写在文件名里：`g12-paddle-up-2-must-fail`、
     `g09-assert-paddle-original-must-fail`、`g24-assert-win-must-fail`、
     `g04-park-check-must-fail`、`g26-wall-assert-must-fail`）。
* **建议**：(a) 把 `g20` 的 `dir` 改成 `-1,0`（或改成头正对颈的布局）并**先确认引擎 stdout 出现
  `SNAKE_SELF`**，再让 `g22` 断言 `LoseReason="self"`；(b) `g19` 单独起一块 `ForceTestState`
  盘面（当前它复用了 `g18-turn-up` 之后的 `dir=0,-1` 状态，向下＝180° 掉头被 `TrySetDirection`
  拒绝，这才是实得 `-1` 的原因）；(c) 两条修好后重跑并更新 `GAME-LOOP-LOG.md:19`、
  `TASK-093-REPORT.md:86`、`TASK-097-REPORT.md:125`、以及 S-3 行的表述；
  (d) 若产品决定"自撞不测"，则把文件名改成 `*-must-fail`、note 写清"本会话不覆盖"，并**同时**
  把台账里「自撞由断言钉住」删掉 —— 二者不能并存。

### D-2（`medium`）`TASK-093-REPORT.md` 的断言计数没有把未声明失败计入，读者无法从报告发现它们

`TASK-093-REPORT.md` §A3/A4 给出 Snake 的「断言」表与台账表，但该表的断言口径只统计
`passed:true` 与「声明的边界失败」，**没有任何一格记录 `scenario_assertion_failed`**；
而同一轮的 `ledger-game.txt` 已经带 4 条 flagged、`report.json`/`report.md` 里也没有断言汇总段
（`tools\game_report.py` 的 report.json 只有 `defects/endpoints/game/observable/pillow/run/…`）。
**建议**：让 `game_report.py` 从响应文件里汇总 `passed/failed/all_passed=false`（它本来就存了全部响应），
并在报告里单列"未声明失败"一格；这样 D-1 这类问题会在生成的报告里直接可见，而不是靠人写表。

### D-3（`low`）`--import` 关机期访问违例仍是未结案的公开遗留

`GAME-LOOP-LOG.md` / `DECISIONS.md` D146–D152 反复记到 `0xC0000005`、累计口径
`3/48`，而 `TASK-104` 的 `import.stderr.txt` 并**不是** 0 字节（例如
`runs\pong\pong-clean-task097\import.stderr.txt` 307 B）。文档自己声明了"只记录、不改引擎"、
"`IMPORT_EXIT` 不能当健康信号"，因此**不构成隐瞒**；但它确实是 20 款游戏的复现链条上唯一
未定性的环境噪声，建议在结案口径里保留。

### 非缺陷（明确排除，避免下游误读）

* `pong`/`breakout`/`snake` 的**清洁轮** `c02-tree-before` 里有 `@` 名节点、`c03-read-before` 与
  `c08-read-after` 的 sha 不同 —— 这正是**清理动作本身**，`c06-tree-after` 起 0 个 `@` 名，
  不是缺陷。
* `snake-clean-task097` 编辑器相像素非零数 = **0/71**（`nondistinct_digests=1`），
  即 71 个 capture pair 的 PNG **全同 sha**。这不是"画面冻住"，而是**编辑器相本来就不该动画面**
  （71 个调用里 66 个是读工具）；游戏相 13/31 非零。台账数字与之一致，无需修正。

---

## 4. 我独立运行的检查（命令 + 关键输出摘录）

| # | 命令 | 关键输出 |
|---|---|---|
| 1 | `python check1_trace_fields.py`（扫全部 `runs\**\trace-*.jsonl`） | `trace files: 138 tools/call lines: 6565`；`aggregate missing-field counts: {}`；无一条文件有缺字段或 malformed |
| 2 | `python check2_payload_bytes.py` | 20/20 游戏：`project_*_script` 的 `content` == 会话 payload == `projects\<game>\src\*.cs`；`no problems` |
| 3 | `python godot\modules\mcp_server\scripts\mcp_trace_ledger.py runs\...\trace-editor.jsonl`（20 个最终运行 × 2 相，见 `check7_all_ledgers.py`） | `calls=45 malformed_lines=0`…`facts 45/45`；20/20 与台账声称的调用数/判定分布一致 |
| 4 | `python check4_rows.py` | 逐字段对照 seq 8 / 26 / 30：`LEDGER matches raw: verdict_ok=True scene=True file=True`；sidecar `recomputed_sha_match=True` |
| 5 | `python check3_ledger_counts.py` | 独立重算 pong 清洁轮：editor `changed=3`、game `changed=11` → 与「3/45、11/29」一致 |
| 6 | `python check5_assertions.py` + `python check6_undeclared.py` | `TOTAL passed=1358 failed=9 errors=0`；`UNDECLARED failing assertions in final runs: 3`（全部在 snake） |
| 7 | `python recovery\work\task097\pixel_recompute.py runs\pong\pong-clean-task097 runs\snake\... runs\breakout\...`（并在 `check11_all_pixels.py` 里扩到 20 款） | pong `3/45 + 11/29`、snake `0/71 + 13/31`、breakout `2/55 + 12/34`；`0` 处 reported≠recomputed；全量 `ALL CLAIMED PIXEL COLUMNS REPRODUCED … True` |
| 8 | **反例**：`python check8_mutation.py`（改 trace 的 `changed_pixels` 512→999999） | `pairs whose reported changed_pixels != the recomputed engine number: 1`；`seq=6 … reported=999999 recomputed=512` |
| 9 | **反例**：`python check9_png_mutation.py`（往 after PNG 涂 36 px） | `any=36 engine=36 reported=0`；非零列 11/29 → **12/29**；mismatch 2 |
| 10 | **反例**：`python check10_recompute_mutation.py`（`g48-assert-x` 的 actual 0→20） | `g48-assert-x … expected=0 actual=20 <<< MISMATCH`；`TOTAL RECOMPUTATION MISMATCHES: 1` |
| 11 | 检查 D-3 / X-1 修前修后原始响应 + 源码 + git | `d3-before e06 → status:"ok", @ColorRect@20956` vs `d3-after e04 → error -32000 + conflicts`；`x1-before → {"result":null}` vs `x1-after → -32000 + data.script_error`；git `2385fe2fb5` / `1c7f5c07a1`；源码 `editor_node_batch_write.cpp:436/464`、`running_game_script_execution.cpp:356-386` |
| 12 | `python check12_d3_evidence.py` + `check13_effects_png.py` | 17 款运行里第二次同名批量全部 `-32000` + 恰 3 条 `conflicts` + 前后 sha 相同 + 0 个 `@` 名；20/20 的 `file_effects[].after.sha256` == 盘上文件 sha；每款 84~466 张 PNG |
| 13 | `powershell -File tools\run_gates.ps1 -PreflightOnly -OutDir %TEMP%\acc105\gates-preflight` | `VERSION_TEXT=…1c7f5c07a`、`VERDICT=ANCHOR_STRUCTURAL_EQUIVALENT`、`NONCOMPILING_COUNT=1`、`RESULT=SKIP_REBUILD`、`GATES_SKIPPED=1`（**十道门本次未跑**，与 D152 的自述一致） |
| 14 | `python godot\modules\mcp_server\scripts\check_tautologies.py` / `--probes` | `TAUTOLOGY CHECK PASS (…scanned=2 file kind(s) under 2 root(s))`；`PROBES: 18/18 (14 declared + 4 near miss)` |
| 15 | 引擎版本锚点抽取（每个最终运行的 `trace_opened.version`） | `95aa1d898`/`cf554ef58`/`2385fe2fb`/`e041cae27`/`1c7f5c07a`；rtype/pb/ll = `1c7f5c07a` = 盘上二进制锚点 |

---

## 5. 遗留风险与边界（如实列，不替它们下结论）

1. **我无法当场重跑引擎**（会写工程 `.godot` 缓存 = 改动被验收对象）。因此
   「当场传一个不存在的属性看是否真回错」只是**被既有产物**覆盖（每款一条 `-32001` 声明边界调用 +
   X-1 修前修后原始响应），**不是我发出的活调用**。置信度：`supported` 但非 `verified-live`。
2. **`args` 上限 4096 B 之外的旁路证据我只核到「被裁的那些载荷」**；未裁的载荷没有 sidecar（按设计），
   我按 §2.6 的规则读作 inline 完整，未找到反例。
3. **`error_message` 仍是纯截断（512 B）**：`MCP-TRACEABILITY.md` §3.2 明说了，机器可读的那一半在
   `error_data_json` 里。我没有找到因它丢结论的调用，但这条边界是真实存在的。
4. **`check_tautologies.py` 是 spelling-visible 的**（它自己声明了），因此**游戏会话里的恒真断言不在它管辖内**；
   我对会话侧只做了"失败是否被声明"的判定（`check6`），没有做逐条断言的语义恒真审计。
5. **Snake 的 g19 失败根因我给出的解释**（g18 之后方向已是 `0,-1`，`snake_down` 触发 180° 掉头被
   `TrySetDirection` 拒绝）是**推断**（读码 + 会话顺序），不是我重跑验证的；D-1 的**事实部分**
   （3 条 FAIL、0 次 `SNAKE_SELF`、三处矛盾陈述）是**证据支持**的。
6. D-2/D-3 的严重度是我按"是否掩盖了不该通过的东西"给的，不是按实现者自述。

---

## 6. 最终判定

**`fail`**，原因是 D-1：Snake 的**最终运行**里有 3 条未声明失败断言，自撞判负这条规则**在证据里从未被走到**，
而三份文档（含本任务的权威台账 `GAME-LOOP-LOG.md`）对同一批断言给出了**互相矛盾且与产物相反**的结论，
同时该轮自己的 `ledger-game.txt` 已经把这些标成 `scenario_assertion_failed`。

**除此之外的部分经得起独立复核**：6565 次调用的字段齐备性、20 款游戏的载荷-磁盘字节一致性、
20 款游戏的台账数字与像素列的全量重放、D-3 与 X-1 的修前修后与源码/提交锚点、旁路证据的重算、
以及像素/断言复算器在 3 个构造反例下"真的会响"。修掉 D-1（改钉板 + 单独起盘面 + 改口径）后可重验，
我预期只需重跑 Snake 一款。
