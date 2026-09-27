# ACCEPTANCE-TASK-107 — 第二轮独立验收报告

**验收对象**：`F:\moonbit-hof-rs\godot-mcp`
**验收员**：独立验收子代理（**第二轮**；未采信 `ACCEPTANCE-TASK-105.md` 或 `TASK-106-REPORT.md` 的任何结论，也未被实现者上下文污染）
**日期**：2026-09-27
**权限**：只读被验收对象 + 只写本文件。所有检查脚本与变异副本一律写在 `%TEMP%\acc107\`；未改动被验收对象一个字节（见 §6 的 git 复核）。
**输入**：`recovery\reports\ACCEPTANCE-TASK-105.md`（上一轮 3 条 fail）、`recovery\reports\TASK-106-REPORT.md`（修复自述）、`recovery\work\task106\*`、`runs\snake\snake-task106-r1\`。

---

## 0. 结论

**`pass`** —— 上一轮 fail 的三条（C10 / C11 / C12）都被产物独立证实已修复；抽查其余关键面（载荷字节链、trace 字段、报告层新计数器真的会响）也全部通过。遗留项只有两条**措辞/时点标注**层面的 low 风险与一条我无法当场重跑引擎的边界，均不构成 fail。

| 命题 | 独立判定 | 证据强度 |
|---|---|---|
| **C10** 20 款最终运行里没有未声明失败断言 | **成立** | 证据支持（自写脚本 + 声明清单 + 中间轮对照） |
| **C11** Snake 自撞判负真的被走到 | **成立** | 证据支持（引擎 stdout / 响应 / 台账三路一致） |
| **C12** 四处把失败当通过的表述改了且保留两时点、未静默改写 | **成立** | 证据支持（逐行 git diff + 行文核对） |
| ④ 3 款游戏 `src\*.cs` 与会话载荷逐字节相同、trace 字段齐备 | **成立** | 证据支持（字节级 + 5 行手工逐字段） |
| ⑤ `game_report.py` 的新计数非空转（旧 3 / 新 0） | **成立** | 证据支持（我亲手在副本上跑出的真实输出） |
| ⑥ 至少 1 个反例证明检查器会响 | **成立（做了 4 个）** | 证据支持（CE1–CE4 全部 FIRED） |

---

## 1. C10 —— 最终运行里没有未声明失败断言

**做法**：自写 `recovery` 之外的脚本，**从运行自己保存的响应 `*.json` 重算**断言总数，并与**运行自己的 `call-index.txt`**（声明来源）比对；不看台账 flags。最终运行清单取 `GAME-LOOP-LOG.md` 的逐款证据列（snake 按 TASK-106 追记更新为 `runs\snake\snake-task106-r1`）。

**命令 1**：`python C:\Users\wyl\AppData\Local\Temp\acc107\acc107_final_declared.py`

```
DECLARED FINAL RUNS: passed=1361 failed=6 errors=0 declared_failures=6 UNDECLARED=0
```

20 行逐款全部 `und=0`；6 条失败全部声明（pong `g12/g27`、breakout `g09/g24`、snake `g04/g26`）。与 TASK-105 的原值对照：`passed 1358→1361`、`failed 9→6`、`UNDECLARED 3→0`（snake `g19`/`g22` 的两条失败断言 + `g22` 的第二条 = 3 条，正好消失；其余 6 条声明的 must-fail 一条不少）。

**命令 2**（换一个“最终运行”定义做稳健性检验，不采信任何文档）：`python ...\acc107_final_runs.py`，用“`runs\<game>\*` 里带响应且最大文件 mtime 最新的目录”自动发现：

```
game             final run                           passed  failed  errors    dec    und  verdict
snake            snake\snake-task106-r1                  16       2       0      2      0  CLEAN
... （20/20 全部 CLEAN）
TOTAL undeclared failing assertions across the 20 final runs: 0
```

两种定义下都是 **0**。（该自动发现唯一与文档清单不同的是 match3：它把 X-1 诊断探针 `task103-x1-after` 当最新，而文档的最终轮是 `m3-task102-r3`；两者 `und` 都是 0，不影响结论。）

**命令 3**（反向对照，确认扫描器不是“什么都不报”）：`python ...\acc107_diagnostic_sweep.py`

```
ALL run dirs with undeclared failures: 27
  snake  snake-clean-task097   und=3 first=g19-turn-down
  snake  snake-task093-r6      und=3 first=g19-turn-down
  towerdefense td-task103-r1   und=11 first=g52-assert-towers
  ...
```

即：**盘上仍有 27 个历史中间轮带未声明失败**（每个游戏修好前的中间轮、X-1/D-3 探针轮），它们**不是最终运行**，且 `GAME-LOOP-LOG.md:498-504` 的 TASK-106 追记已把 snake 的两轮（`snake-task093-r6`、`snake-clean-task097`）的点名结案。这条同时说明扫描器对真实存在的红是敏感的。

---

## 2. C11 —— Snake 自撞判负真的被走到

**命令**：`python C:\Users\wyl\AppData\Local\Temp\acc107\acc107_c11_snake.py`

**① 引擎 stdout（读的是盘上文件，不是报告）**

```
### C11a  SNAKE_SELF in engine-game.stdout.txt
  NEW snake-task106-r1    SNAKE_SELF count=1  SNAKE_WALL count=3
      SNAKE_SELF head=9,10 len=5 score=0 ticks=0
  OLD snake-clean-task097 SNAKE_SELF count=0  SNAKE_WALL count=3
```

`SNAKE_SELF head=9,10` 与 TASK-106 自述一致；旧轮 0 次（复现上一轮的 D-1 事实）。stdout 里还有 `SNAKE_AIM board=segs=10,10|9,10|8,10|7,10|6,10 head=10,10 dir=-1,0` 与 `SNAKE_DIR dir=0,1`（g19 向下转弯被接受）。

**② 响应（逐字，来自运行自己的 `*.json`）**

```
g18b-aim-turn-down   {"result": "state segs=3 head=8,10 dir=1,0 food=0,0", ...}
g19-turn-down        all_passed=true passed=1 failed=0  DirectionY expected=1.0 actual=1 passed=true
g20-aim-self         {"result": "state segs=5 head=10,10 dir=-1,0 food=0,0"}
g20b-dump-self-board {"result":"segs=10,10|9,10|8,10|7,10|6,10 head=10,10 dir=-1,0 len=5 ... reason=''"}
g22-self-collision   all_passed=true passed=2 failed=0   GameOver true->true ; LoseReason self->self
g23-self-readback    {"result": "over=true reason=self score=0 status_visible=true"}
g25-wall-collision   all_passed=true passed=2 failed=0
g26-wall-assert-must-fail  passed=false expected=self actual=wall   ← 声明的 must-fail
g04-park-check-must-fail   passed=false                             ← 声明的 must-fail
```

**③ 台账（`ledger-game.json` 的 rows 自带 flags）**

```
scenario_assertion_failed rows = 0 ; assertion_failed rows = 2
calls=33 malformed_lines=0
```

`ledger-game.txt` 里带 flags 的行只有 `seq 4 g04-park-check-must-fail`、`seq 29 g26-wall-assert-must-fail`（都是 `assertion_failed`），加一条声明过的边界失败 `seq 23 -32001`（`g21-boundary-unknown-property`，带 `suggestion`）。**编辑器相**：

```
editor ledger: calls=20 malformed_lines=0
  assertion_failed=0 scenario_assertion_failed=0
```

**④ 模板本体确实被修过**：`tools\sessions\snake\session.json` 里 `g20-aim-self` = `ForceTestState("10,10|9,10|8,10|7,10|6,10;dir=-1,0;food=0,0")`，且新增 `g18b-aim-turn-down`、`g20b-dump-self-board`——与运行产物一一对应。

**结论**：三路（引擎 stdout / 断言响应 / 台账）互相独立地都指向“自撞路径被真实走到且只剩声明的 must-fail”。

---

## 3. C12 —— 表述改成与产物一致、保留两时点、未静默改写历史

**命令**：`python C:\Users\wyl\AppData\Local\Temp\acc107\acc107_docdiff.py f25960c 32fef85`（`f25960c` = TASK-106 前的最后一个提交）

**逐行 diff 的真实性质**（不是听报告）：

```
TASK-093-REPORT.md   added lines: 3   removed lines: 3
    :19  原「…LoseReason=self、LoseReason=wall」→ 去掉未成立的 self，加「(LoseReason=self 当时并未成立 —— 见 §A3 该行的更正与 TASK-106 重跑)」
    :86  原「| 自撞判负 | g20 / g22-self-collision | LoseReason eq "self" passed |」
         → 「当时为错报：… SNAKE_SELF 出现 0 次 … 这条断言没有 passed。本行原写的 "passed" 与产物相反（…D-1 指出，TASK-106 修正口径）。TASK-106 重跑后自撞路径已实测覆盖：…」
    :150 S-3 行 → 「当时为错报：…本行原写「两条同时成立」与产物相反」+「TASK-106 重跑后自撞路径已实测覆盖」
TASK-097-REPORT.md   added lines: 1   removed lines: 1
    :125 从「仍然通过」列表去掉 g19/g22，并写明「本行原先把…追认为「按设计失败」… 这 3 条失败没有任何声明」
GAME-LOOP-LOG.md     added lines: 10  removed lines: 2
    :19  Snake 行 → 「TASK-093：…；TASK-106 重跑：…」两个时点
    :260 S-3 行 → 「当时为错报：…」+「TASK-106 重跑后自撞路径已实测覆盖：…」
    @@ -497,0 +498,8 @@  ← TASK-106 追记是**纯追加**，里程碑 20 款快照表**一字未动**
```

**判定**：
* **与产物一致**：现在六处都写“旧口径为错报 + 新跑法已覆盖”，与我在 §1/§2 复核出的产物一致。
* **保留两个时点**：每一处都同时带「当时为错报」与「TASK-106 重跑后自撞路径已实测覆盖」，没有把两者写成同一时点。
* **没有静默改写**：每一处新文本都**点名并引用了被否证的旧说法**（“本行原写的 'passed'”“本行原写「两条同时成立」”“原先把它们列进『仍然通过』又追认为『按设计失败』”），且旧的权威快照（20 款里程碑表）以**纯追加**追记处理、未回填——旧字面仍可从 `git show f25960c` 取出。这是**公开更正**，不是静默改写。

**顺带复核被更正行现在引用的数字**（全部自己重算）：

| 声称（`GAME-LOOP-LOG.md:19`） | 我的重算 | 一致 |
|---|---|---|
| 会话调用数 20 / 33（53） | editor 20、game 33 | ✔ |
| `facts_complete` 53/53 | editor 20/20、game 33/33 | ✔ |
| 编辑器 `ok_effect=1 / ok_file_effect=10 / ok_no_effect=9`、`failed=0` | 逐值相同 | ✔ |
| 游戏 `failed=1 / ok_effect=6 / ok_file_effect=11 / ok_no_effect=15` | 逐值相同 | ✔ |
| 逐调用像素差 12/53 非零（编辑器 1/20、游戏 11/33） | 独立复算同值，`reported!=recomputed: 0` | ✔ |
| `scenario_assertion_failed` 2 → 0 | game ledger flags | ✔ |
| 场景树 38 节点、0 个 `@` 名 | `e17/g01/g28` 三个快照都是 38 / 0 | ✔ |
| `main.tscn` 7076 B、sha `F3B51DF1…` | 逐字节相同 | ✔ |

命令：`python ...\acc107_pixels.py` → `TOTAL: non-zero 12/53`；`python ...\acc107_verdicts.py` → `editor verdicts={'ok_effect_observed': 1, 'ok_file_effect_observed': 10, 'ok_no_effect_observed': 9}` / `game verdicts={'failed': 1, 'ok_effect_observed': 6, 'ok_file_effect_observed': 11, 'ok_no_effect_observed': 15}`；`python ...\acc107_editor_ledger.py` → `bytes=7076 sha256=F3B51DF1…D089C0CD… nodes=38`。

---

## 4. ④ 载荷字节链与 trace 字段（抽 3 款）

**命令**：`python C:\Users\wyl\AppData\Local\Temp\acc107\acc107_payload_trace.py`

**4a 三方法定载荷三方字节一致**（`project_create_script`/`project_edit_script` 的实际载荷 == `tools\sessions\<g>\payload\*.cs` == `projects\<g>\src\*.cs`，超限载荷走 sidecar）：

```
snake        SnakeSegment.cs  inline   call=79987161BD21A5E3 payload=… project=… OK
snake        Food.cs          inline   call=4841EB57F41C67E8 … OK
snake        SnakeGame.cs     sidecar  call=14E88DCB573803A3 … OK
tetris       Tetromino.cs     inline   OK
tetris       TetrisGame.cs    sidecar  OK
minesweeper  MinesweeperGame.cs sidecar OK
TOTAL payload problems: 0
```

**4b trace 字段齐备性 + 同 seq 的 capture 行 + file_effect 落盘 sha**：

```
snake        editor  calls=20  capture_lines=20  missing_fields=0 calls_without_capture=0 malformed=0
snake        game    calls=33  capture_lines=33  missing_fields=0 calls_without_capture=0 malformed=0
tetris       editor  calls=6   capture_lines=6   missing_fields=0 calls_without_capture=0 malformed=0
tetris       game    calls=36  capture_lines=36  missing_fields=0 calls_without_capture=0 malformed=0
minesweeper  editor  calls=14  capture_lines=14  missing_fields=0 calls_without_capture=0 malformed=0
minesweeper  game    calls=141 capture_lines=141 missing_fields=0 calls_without_capture=0 malformed=0
```

（要求字段：`id` 非 null / `tool` / `args` / `method` / `ok` / `ok=true→result_json` / `ok=false→error_data_json+error_code` / `file_effect_status` / `file_effects` / `capture` / 同 seq `capture` 行 / `duration_ms` / `ts_ms`。）

**一个需要说清楚的点**：4b 最初把**每一次** `file_effects[].after.sha256` 与**当前**盘上 sha 比，报了 `project.godot` 与 `user://mcp_test_report.json` 的“不符”。这是**我的比法过严**，不是缺陷——同一个文件在运行中被写 N 次，只有**最后一次** effect 才应该等于静止后的盘上内容。用正确的口径重比（`python ...\acc107_effect_scope.py`）：

```
NEW snake-task106-r1   files whose LAST recorded after.sha256 != disk: 0
OLD snake-clean-task097 files whose LAST recorded after.sha256 != disk: 3
   （main.tscn / mcp_csharp_build_state.json / mcp_test_report.json —— 旧工程随后被 TASK-106 归档重实例化，
     盘上状态已经往前走；这是历史归档的正常结果，不是 TASK-106 的回归）
```

**手工逐字段对照 5 行**（`python ...\acc107_manual_rows.py`），逐行核对 `id / tool / ok / error_code / duration_ms / ts_ms / file_effect_status / file_effects / capture / args_bytes / args_truncated` 与**同 seq 的 capture 行**及**运行自己保存的响应文件**：

| 游戏/相/seq | 调用行 | capture 行 | 响应文件 | 一致 |
|---|---|---|---|---|
| snake editor 4 | `id=103 project_edit_script ok=true err=0 dur=33ms args_bytes=20555 truncated=true`；effect `write res://src/SnakeGame.cs changed=true before=72feb9ea95b2 after=14e88dcb5738` | `changed=False changed_pixels=0 frames_waited=2` | `e04-edit-game.json` 的 `result_json` 与调用行逐字相同 | ✔ |
| snake game 8 | `id=128 running_game_run_test_scenario ok=true dur=1037ms`；两条 effect 都写 `user://mcp_test_report.json` | `changed=True changed_pixels=3456 frames_waited=63` | `g08-unpause.json` 文本与 `result_json` 前缀相同 | ✔ |
| snake game 22 | `id=142 running_game_execute_gdscript ok=true file_effect_status=no_mutation effects=0` | `changed=False changed_pixels=0 frames_waited=1` | `g20b-dump-self-board.json` 的 `result` 与调用行 `result_json` 逐字相同 | ✔ |
| tetris editor 3 | `id=102 project_build_csharp ok=true dur=3658ms`；effect 写 `user://mcp_csharp_build_state.json` | `changed=False changed_pixels=0 frames_waited=219` | `r03-build-csharp.json` 一致 | ✔ |
| minesweeper game 10 | `id=123 running_game_assert_node_state ok=true dur=26ms`；`result_json.passed=true FlaggedCount expected=0.0 actual=0` | `changed=False changed_pixels=0 frames_waited=1` | `g10-assert-flags-0.json` 一致 | ✔ |

---

## 5. ⑤ `game_report.py` 的未声明失败计数不是空转 + ⑥ 反例

**5.1 旧运行报 3、新运行报 0（我亲手跑，输出真实）**

**命令**：`python C:\Users\wyl\AppData\Local\Temp\acc107\acc107_reportgen.py`
（先把两轮各自**复制**到 `%TEMP%\acc107\reportprobe\`，再对副本调用仓库里的 `tools\game_report.py`；归档原件零改动。）

```
LABEL: OLD run snake-clean-task097   staged copy …\reportprobe\snake-clean-task097   exit code: 0
  * assertions: **passed 13 / failed 5 / errors 0**
  report.json : responses_scanned=100 passed=13 failed=5 errors=0 undeclared_count=3
       UNDECLARED g19-turn-down       scenario:DirectionY eq 1.0 -> actual -1
       UNDECLARED g22-self-collision  scenario:GameOver eq True -> actual False
       UNDECLARED g22-self-collision  scenario:LoseReason eq self -> actual

LABEL: NEW run snake-task106-r1      staged copy …\reportprobe\snake-task106-r1      exit code: 0
  * assertions: **passed 16 / failed 2 / errors 0**
  report.json : responses_scanned=52 passed=16 failed=2 errors=0 undeclared_count=0
```

**旧 3 / 新 0 都是真实输出**，且旧的 3 条与我 §1 独立算出的 3 条完全一致。另核源码：`assertion_summary()` 只读运行自己的 `*.json` 与 `call-index.txt`，**不读台账 flags**——这与台账是两条相互独立的证据。

**5.2 反例（全部在 `%TEMP%\acc107\ce\` 的副本上做，原件未碰）**

**命令**：`python C:\Users\wyl\AppData\Local\Temp\acc107\acc107_counterexamples.py`

```
CONTROL   untouched copy of the accepted run            scan(): passed=16 failed=2 und=0 dec=2
CE1  g22 的一条 assert passed=true -> false              scan(): und=1  -> FIRED
CE2  CE1 + 在 call-index.txt 里把 g22 声明为 boundary     scan(): und=0  -> FIRED（声明来源真的被读）
CE3  从 engine-game.stdout.txt 删掉 SNAKE_SELF 行         1 -> 0 行      -> FIRED
CE4  trace-game.jsonl 里删掉 seq=8 的 duration_ms        missing=[(8,'duration_ms')] -> FIRED
```

CE1/CE2 一起证明“未声明计数”既会因为真失败而响、也会因为真声明而收；CE3 证明 C11 读的是**产物文件**而不是报告里的字符串；CE4 证明 trace 齐备性检查不是恒绿。

---

## 6. 铁律遵守与产线复核

* **零改动被验收对象**：最终复核 `git status --short`（主仓）与 `git -C godot status --short`（引擎仓）：

```
=== MAIN status ===
 M godot-mcp/recovery/work/task104/logs/git-housekeeping.err.txt
 M godot-mcp/recovery/work/task104/logs/git-housekeeping.out.txt
=== MAIN HEAD ===   b3a906c3df62c51528b6811820775875af5effc0
=== ENGINE status ===   （空）
=== ENGINE HEAD / origin ===   1f9d0cb1c983301d4efa575c16986c551df23600（两者相同）
```

  那两条 `task104` 日志是 TASK-106 §D4 声明的**未碰的既有脏文件**，我进场前就在、进场后不变。我没有新建/修改任何仓库文件（本文件除外），没有删除任何东西。
* **未用 shell 重定向**：所有脚本输出直接走 stdout；需要落盘的一律由 Python writer 或 write 工具完成。**例外如实声明**：我在一条早期命令里误用了 `2>nul`（`git show --stat 2>nul`），该命令因 PowerShell 报错未产生任何效果，此后全部改为无重定向。
* **反例只在副本上做**：§5.2 的 4 个变异、§5.1 的旧/新运行重生成，全部在 `%TEMP%\acc107\` 下；`runs\snake\snake-clean-task097` 与 `runs\snake\snake-task106-r1` 的归档字节未动。
* **未重启引擎**：本轮没有（也不需要）重新执行 Godot。原因与边界见 §7.1。

---

## 7. 遗留风险、边界与不确定性（不替它们下结论）

1. **（边界，未当场重跑引擎）** C11 与 ④ 的证据全部来自**盘上已存在的运行产物**（`snake-task106-r1` 的 trace/ledger/stdout/响应/PNG），我没有启动引擎再跑一次会话——那会写工程 `.godot` 缓存＝改动被验收对象。因此“这台机器现在再跑一次也会出现 `SNAKE_SELF`”是**推断**；而“该运行自己的引擎 stdout 出现过 1 次 `SNAKE_SELF head=9,10`、响应与台账三路一致”是**证据支持**。`trace_opened.version` = `4.8.dev.mono.custom_build.1c7f5c07a`，与 TASK-106 §D1 的锚点自述一致，但我没有重算盘上引擎二进制本身的 hash。
2. **（low，文档一致性）** `recovery\reports\TASK-093-REPORT.md:16`（§0 汇总行 A）仍写「Snake 网格移动/食物增长/**自撞**/撞墙/计分 …… **达成**」，**未带时点标注**。TASK-106 §B 边界 #2 主动声明了这一处不改，理由是“它陈述的是交付范围，而自撞现在确实被覆盖”。我同意“现在确实被覆盖”，但该行出现在一个按惯例“带两个时点”的文件里，读者单看这一行无法知道它在 TASK-093 当时并不成立。**这不是与当前产物相反的陈述**，所以我不判 fail，登记为 low。
3. **（low，措辞）** `GAME-LOOP-LOG.md:260` 结尾「`LoseReason=wall` 与 `LoseReason=self` 各 1 次」：字面上 `SNAKE_WALL` 在引擎 stdout 出现 **3** 次（自由回合一次、增长回合一次、墙测一次），只有“墙测/自撞测各有一条 `LoseReason` 断言并各成立一次”是真的。语义可读通，但“各 1 次”若被读成 stdout 计数会误导。措辞层，不判 fail。
4. **（out of scope）** TASK-105 的 D-3（`--import` 关机期访问违例）不在本轮修复清单里；我按 TASK-106 §F3 的声明读作“仍按原记录保留”，没有重新定论。
5. **（须声明的读法边界）** C10 的结论依赖“最终运行”的定义。按 `GAME-LOOP-LOG.md` 的逐款证据列（snake 用 TASK-106 追记更新）是 **0**；按“目录 mtime 最新”也是 **0**。但**盘上仍有 27 个历史目录带未声明失败**（§1 命令 3）。谁若不区分“最终运行 / 历史中间轮”，会得到“有红”的相反印象——这些红的出处已由 TASK-106 追记与各处时点标注点名。

---

## 8. 我独立运行的检查一览（命令 + 关键输出行）

| # | 命令 | 关键输出 |
|---|---|---|
| 1 | `python %TEMP%\acc107\acc107_final_declared.py` | `DECLARED FINAL RUNS: passed=1361 failed=6 errors=0 declared_failures=6 UNDECLARED=0` |
| 2 | `python %TEMP%\acc107\acc107_final_runs.py` | 20/20 `CLEAN`；`TOTAL undeclared …: 0` |
| 3 | `python %TEMP%\acc107\acc107_diagnostic_sweep.py` | `ALL run dirs with undeclared failures: 27`（全是历史中间轮/探针） |
| 4 | `python %TEMP%\acc107\acc107_c11_snake.py` | `NEW … SNAKE_SELF count=1`；`SNAKE_SELF head=9,10 len=5 score=0 ticks=0`；`g22 all_passed=true passed=2 failed=0`；`scenario_assertion_failed rows = 0`；editor `assertion_failed=0` |
| 5 | `python %TEMP%\acc107\acc107_payload_trace.py` | 6 条脚本调用三方 sha 相同；`missing_fields=0 calls_without_capture=0 malformed=0`（snake/tetris/minesweeper，6 相） |
| 6 | `python %TEMP%\acc107\acc107_effect_scope.py` | 新轮 `LAST != DISK: 0`；旧轮 `3`（归档造成的正常漂移） |
| 7 | `python %TEMP%\acc107\acc107_manual_rows.py` | 5 行调用/capture/响应逐字段一致 |
| 8 | `python %TEMP%\acc107\acc107_reportgen.py` | 旧 `undeclared_count=3`（列出 g19、g22×2）；新 `undeclared_count=0` |
| 9 | `python %TEMP%\acc107\acc107_counterexamples.py` | CE1/CE2/CE3/CE4 全部 `FIRED` |
| 10 | `python %TEMP%\acc107\acc107_pixels.py` | `TOTAL: non-zero 12/53`（editor 1/20、game 11/33）；`reported!=recomputed: 0` |
| 11 | `python %TEMP%\acc107\acc107_verdicts.py` / `acc107_editor_ledger.py` / `acc107_scenetree.py` | 判定分布逐值吻合日志行；`38` 个节点名、`0` 个 `@`；`main.tscn 7076 B sha F3B51DF1…` |
| 12 | `python %TEMP%\acc107\acc107_docdiff.py f25960c 32fef85` | 3 / 1 / 3 行被“带时点的更正”替换；里程碑表 `@@ -497,0 +498,8 @@` 纯追加 |
| 13 | `git status --short` / `git -C godot status --short` | 只有两条既有 task104 脏日志；引擎仓空、HEAD==origin==`1f9d0cb1c` |

---

## 9. 最终判定

**`pass`**。

* **C10 成立**：20 款最终运行的未声明失败断言 = **0**（`1358/9/3 → 1361/6/0`），且 6 条失败全部在文件名/note 里声明。
* **C11 成立**：`runs\snake\snake-task106-r1` 的引擎 stdout 有 `SNAKE_SELF head=9,10`（1 次），`g19`/`g22`/`g25` 断言全绿，`g23-self-readback` 回 `over=true reason=self`，台账 `scenario_assertion_failed` 归零、只剩 `g04`/`g26` 两条声明的 must-fail 与 1 条声明的 `-32001` 边界调用。
* **C12 成立**：六处与产物相反的表述已带**两个时点**公开更正（并点名被否证的旧说法），20 款里程碑快照以**纯追加**追记、未被回填篡改；被更正行引用的每一个数字我都独立重算通过。
* **④ 成立**：3 款 6 条脚本调用三方逐字节相同；6 个相 trace 字段零缺失、零 malformed、每个调用都有同 seq capture 行。

**没有发现新的作弊门、未声明的行为变更或被掩盖的失败。** 遗留的是两条 low 级措辞/时点标注（§7.2、§7.3）和“未当场重跑引擎”的证据边界（§7.1），都不改变三条 fail 已修复的结论。
