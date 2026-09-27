# TASK-106 — 修复 TASK-105 独立验收的三条 fail（Snake 自撞判负的钉板与断言、三份与产物相反的表述、报告层缺「未声明失败」一格）

* 执行者：修复工程师（本会话，**有写权限，不委派**）
* 主仓：`F:\moonbit-hof-rs`（分支 `master`，无远端）
* 引擎仓：`F:\moonbit-hof-rs\godot-mcp\godot`（分支 `feature/mcp-server-module-rebuild`，remote `git@github.com:shiyukonghui/godot.git`）
* 脚本 / 会话归档 / 证据：`godot-mcp\recovery\work\task106\`
* 输入：`godot-mcp\recovery\reports\ACCEPTANCE-TASK-105.md`（16 条判据，`fail`；D-1 blocking、D-2 medium）
* 时间：2026-09-27（本会话）

---

## 0. 结论表（每行一句话）

| 段 | 要求 | 结论 | 关键证据 |
|---|---|---|---|
| **A** | 修 Snake 的断言与自撞路径：①重设钉板让头真的撞进自身；②先在引擎 stdout 看到 `SNAKE_SELF` 再断言 `LoseReason=self`；③`g19-turn-down` 单独起钉板；④重跑并核对「只剩声明的 must-fail 两条 / 无 `scenario_assertion_failed` / `SNAKE_SELF ≥1`」；⑤补齐像素差、台账、断言证据（含独立复算） | **做完。** `g20` 的 `dir` 由 `1,0` 改 `-1,0`（头 `10,10` 撞进颈 `9,10`）、`g19` 前插入自己的钉板 `g18b-aim-turn-down`、并在断言前插入 `g20b-dump-self-board` 把同一块盘面 `Dump()` 出来。归档旧工程（sha256 清单先行、`Move-Item` 零删除）后从 `_template` 重新实例化再重跑：`runs\snake\snake-task106-r1` 里 **`SNAKE_SELF head=9,10` 出现 1 次**、`g19`/`g22`/`g25` 全绿、台账 **`scenario_assertion_failed` 2 → 0**、只剩 **2** 条 `assertion_failed`（`g04`/`g26`，都在文件名里声明）、**未声明失败 0 条**；像素差 **12/53 非零**（编辑器 1/20、游戏 11/33），两套独立复算 **0 处不符** | `tools\sessions\snake\session.json`、`runs\snake\snake-task106-r1\`、`recovery\work\task106\logs\check-snake-task106.txt`、`frames-snake-task106.txt`、`check56-task106.txt` |
| **B** | 修正四处与产物相反的表述（`TASK-093-REPORT.md`、`GAME-LOOP-LOG.md` 两处、`TASK-097-REPORT.md`），修好前写「当时为错报：该轮 ledger 已标 `scenario_assertion_failed`」、修好后写「TASK-106 重跑后自撞路径已实测覆盖」，两者不并存为同一时点的结论 | **做完（四处 + 同文件内同类的两处，共六处；均为追加时点标注，未静默改写历史）。** 20 款里程碑表**保持 TASK-104 快照不动**，只在其后加一条 TASK-106 追记 | `TASK-093-REPORT.md:19/:86/:150`、`GAME-LOOP-LOG.md:19/:260/:495+`、`TASK-097-REPORT.md:125` |
| **C** | 给报告生成层加未声明失败汇总（从运行自身保存的响应文件汇总 `passed/failed/all_passed=false`），在 `report.json` 与 `report.md` 里单列「未声明失败」一格，并做一次实测 | **做完。** `tools\game_report.py` 新增 `assertion_summary()`：读运行自己的 `*.json` 与自己的 `call-index.txt`（声明取自运行自身，不依赖会话文件名）。实测：对 TASK-097 的旧运行（**临时副本**，不动归档）给出 **未声明失败: 3** —— 与 TASK-105 的 `check6_undeclared.py` 独立算出的 3 一致；对新运行给出 **0** | `tools\game_report.py`、`recovery\work\task106\reporttest.py`、`runs\snake\snake-task106-r1\report.json` 的 `assertions` 段 |
| **D** | 改模块 → 重建两变体 + 十道门全绿 + `accept_m1` 22/22 + push；未改模块则如实说明；主仓提交；报告含两仓 `git log --oneline -8` 与 `git status --short`；列出下次验收入口；时间不够如实报告 | **做完。** 本任务**模块零改动**（引擎仓 `git status` 为空、`HEAD = origin = 1f9d0cb1c`），故**不重建、无需 push**（如实说明，见 §D1）；但仍以 `-RunGates` **强制跑完十道门**：`g01`…`g10` **全部 exit=0**，`accept_m1` **22/22**。两仓 `git log`/`git status` 见 §G；下次验收入口见 §A6 | `runs\gates\task106\summary.txt` |

---

## A. Snake 的自撞判负修在根上

### A1 事实与根因（TASK-105 已确证，本轮独立复核）

| 事实 | 证据（本轮重新读出） |
|---|---|
| 两条断言**没有**通过 | `runs\snake\snake-task093-r6`：`g19-turn-down` 的 `DirectionY` 期望 `1` 实得 `-1`；`g22-self-collision` 的 `GameOver` 期望 `true` 实得 `false`、`LoseReason` 期望 `"self"` 实得空串 |
| 两条都**没有声明** | 文件名不带 `-must-fail`，会话 note 是正向意图（`g19` = "and the other direction is accepted too"、`g22` = "self-collision is a loss and the reason names it"） |
| 该轮**已经**标出来了 | 同轮 `ledger-game.txt` 的 `seq 19 / 22` 带 `flags=scenario_assertion_failed` |
| 自撞规则**从未被走到** | `engine-game.stdout.txt` 里 `SNAKE_SELF` 出现 **0** 次（对照 r3/r4/r5 各 3 次） |
| 根因 | `g20` 钉板 `ForceTestState("10,10\|9,10\|8,10\|7,10\|6,10;dir=1,0;food=0,0")`：头在 `10,10`、颈在 `9,10`，而 `SnakeGame.cs:418-434` 的自撞判定是 `nx = HeadX + DirectionX` —— `dir=1,0` 让头走向 `11,10`，**离开**身体 |
| `g19` 的失败另有根因 | `g19` 复查 `g18-turn-up` 之后的 `dir=0,-1`，`snake_down` 是**180° 掉头**，被 `TrySetDirection`（`SnakeGame.cs:230-247`）**正确**拒绝并写进 `LastRefusedInput`；断言失败的是钉板状态，不是游戏 |

### A2 会话改动（模板本体 `tools\sessions\snake\session.json`）

`git diff` 的真实输出（9 insertions / 3 deletions，全部落在 `g18`–`g22` 之间）：

```diff
@@ -262,4 +262,7 @@
         {"type": "assert", "node_path": "Main", "property": "DirectionY", "operator": "eq", "expected": -1}
      ]}, "note": "a legal turn is accepted"},
+    {"tag": "g18b-aim-turn-down", "port": "game", "tool": "running_game_execute_gdscript",
+     "arguments": {"code": "var m = get_parent()\nreturn m.ForceTestState(\"8,10|7,10|6,10;dir=1,0;food=0,0\")"},
+     "note": "test hook (TASK-106, D-1): g19 used to inherit g18's dir=0,-1, so snake_down was a 180-degree reversal that TrySetDirection rightly refused and DirectionY stayed -1. g19 now starts from its own board heading right, where down is a legal turn"},
     {"tag": "g19-turn-down", ...
@@ -267,9 +270,12 @@
         {"type": "assert", "node_path": "Main", "property": "DirectionY", "operator": "eq", "expected": 1}
-     ]}, "note": "and the other direction is accepted too"},
+     ]}, "note": "and the other direction is accepted too (from g18b's own board, so the turn is legal rather than a refusal)"},
 
     {"tag": "g20-aim-self", "port": "game", "tool": "running_game_execute_gdscript",
-     "arguments": {"code": "var m = get_parent()\nreturn m.ForceTestState(\"10,10|9,10|8,10|7,10|6,10;dir=1,0;food=0,0\")"},
-     "note": "test hook: the head at 10,10 heading right straight into its own neck at 9,10"},
+     "arguments": {"code": "var m = get_parent()\nreturn m.ForceTestState(\"10,10|9,10|8,10|7,10|6,10;dir=-1,0;food=0,0\")"},
+     "note": "test hook: the head at 10,10 heading LEFT straight into its own neck at 9,10 -- dir=1,0 (the pre-TASK-106 value) walked the head AWAY from the body to 11,10, which is why the engine's stdout carried SNAKE_SELF zero times and g22 failed"},
+    {"tag": "g20b-dump-self-board", "port": "game", "tool": "running_game_execute_gdscript",
+     "arguments": {"code": "return get_parent().Dump()"},
+     "note": "the exact cells the self-collision test is about to step from (D-1 evidence: the aim and the ending are read from the same board)"},
```

**铁律 5（会话双解析）**：开引擎之前，同一份会话经 Python 与 PowerShell 5.1 各自解析，两侧都 PASS 且**两侧都列出 5 块钉板**：

```
file      : F:\moonbit-hof-rs\godot-mcp\tools\sessions\snake\session.json
bytes     : 26601
calls     : 54 (editor 21 / game 33)
utf8 json : OK
ForceTestState boards in session order:
  g05-aim-pause                      8,10|7,10|6,10;dir=1,0;food=0,0
  g12-aim-growth                     8,10|7,10|6,10;dir=1,0;food=9,10
  g18b-aim-turn-down                 8,10|7,10|6,10;dir=1,0;food=0,0
  g20-aim-self                       10,10|9,10|8,10|7,10|6,10;dir=-1,0;food=0,0
  g24-aim-wall                       23,5|22,5|21,5;dir=1,0;food=0,0
CHECK_SESSION OK

PS_PARSE OK snake-task106 calls=54 editor=21 game=33 unique_tags=54
  board g05-aim-pause  ...  board g20-aim-self  10,10|9,10|8,10|7,10|6,10;dir=-1,0;food=0,0  ...
```

### A3 归档与从模板重新实例化（铁律 6 / TD-2）

**先落 sha256 清单，再移动，全程零删除**：

| 对象 | 清单 | 文件数 | 字节 |
|---|---|---|---|
| `projects\snake`（旧工程） | `recovery\work\task106\manifests\projects-snake-pre-task106.json` | 217 | 10 229 425 |
| `runs\snake\snake-clean-task097`（TASK-097 最终轮） | `recovery\work\task106\manifests\run-snake-clean-task097.json` | 447 | 14 749 663 |
| `runs\snake\snake-task093-r6`（TASK-093 最终轮） | `recovery\work\task106\manifests\run-snake-task093-r6.json` | 241 | 5 384 753 |

* 两个旧跑法**原地未动**（只加了清单），它们仍然是 TASK-093 / TASK-097 的证据。
* `projects\snake` 被 **`Move-Item`** 到 `recovery\work\task106\archive\snake-20260927-080911\`（同时写 `<archive>.manifest.json`），随后由 `tools\new_game.ps1` 从 `projects\_template` 重新实例化（`NEWGAME_EXIT=0`、`placeholder files left: 0`）。**没有任何删除**。
* 理由（TD-2）：在上一轮的工程上重跑，编辑器相的第一步会在已有同名节点上被 `-32000` 拒绝，「一次批量建好静态节点」这一步就不会发生。本轮重跑后编辑器相 20 条调用 **`failed=0`**、`editor_add_nodes_batch` 真的做出 213 200 px 的变化 —— 证明这一步确实发生了。

### A4 重跑 `runs\snake\snake-task106-r1`（端口 9930 / 9931）

跑前 / 跑后 `netstat` + `tasklist`：

```
--- processes named Godot* / dotnet ---   (none)
  9888 free   9889 free   9930 free   9931 free
PORT_CHECK: all wanted ports free
```

`run_game_session.ps1` 的真实收尾（`recovery\work\task106\logs\run-snake-snake-task106-r1.out.txt`）：

```
import   : exit 0 (echoed) / 0 (process)
report: exit 0
RUN_EXIT=0   （包装进程 exit 0，stderr 0 字节）
```

**两相台账（`ledger-editor.txt` / `ledger-game.txt`）**

| 相 | 调用数 | `malformed_lines` | `facts_complete` | 判定分布 | `args_evidence` |
|---|---|---|---|---|---|
| 编辑器 | 20 | 0 | **20/20** | `ok_effect_observed=1`、`ok_file_effect_observed=10`、`ok_no_effect_observed=9`、`failed=0` | `inline_complete=18`、`sidecar_verified=2` |
| 游戏 | 33 | 0 | **33/33** | `failed=1`（**声明的边界调用**，`-32001`）、`ok_effect_observed=6`、`ok_file_effect_observed=11`、`ok_no_effect_observed=15` | `inline_complete=33` |
| 合计 | **53** | 0 | **53/53（100%）** | — | — |

**带 flags 的行（这是本任务的核心判据）**：

```
seq 4   g04-park-check-must-fail       assertion_failed            ← 声明的 must-fail
seq 29  g26-wall-assert-must-fail      assertion_failed            ← 声明的 must-fail
（scenario_assertion_failed: 0 行）
```

（旧轮对照：`snake-clean-task097` 是 `4 / 19 / 22 / 27` 四行 —— 2 条必须失败 + **2 条 `scenario_assertion_failed`**。）

**引擎 stdout（自撞真的被走到）**：

```
SNAKE_SELF head=9,10 len=5 score=0 ticks=0
SNAKE_AIM board=segs=10,10|9,10|8,10|7,10|6,10 head=10,10 dir=-1,0 len=5 score=0 over=False reason='' ticks=0 food=0,0 held=[l=True r=False u=True d=True]
SNAKE_DIR dir=0,1                     ← g19 的向下转弯被接受
```

**关键调用的原始响应**（逐字，来自运行自己保存的 `*.json`）：

```
g19-turn-down      all_passed=true  passed=1 failed=0
                   DirectionY expected=1.0 actual=1 passed=true

g20-aim-self       {"result":"state segs=5 head=10,10 dir=-1,0 food=0,0"}
g20b-dump-self-board {"result":"segs=10,10|9,10|8,10|7,10|6,10 head=10,10 dir=-1,0 len=5 score=0
                     over=False reason='' ticks=0 food=0,0 held=[l=True r=False u=True d=True]"}

g22-self-collision all_passed=true  passed=2 failed=0
                   GameOver   expected=true  actual=true  passed=true
                   LoseReason expected=self  actual=self  passed=true
g23-self-readback  {"result":"over=true reason=self score=0 status_visible=true"}

g25-wall-collision all_passed=true  passed=2 failed=0 （GameOver=true、LoseReason=wall）
g26-wall-assert-must-fail  passed=false  expected=self actual=wall   ← 声明的 must-fail，仍然失败
```

**场景树**（`g28-scene-tree-final`）：**38** 个节点名、**0** 个以 `@` 开头（新一轮没有副本层）。
`projects\snake\scenes\main.tscn`：38 个 `[node name=`、0 个 `@` 名、**7076 B**、sha256 `F3B51DF1D089C0CD933378A806EA908AB9CFEB4B2BF95CBC1B5FAA78BF78306D`（旧轮是 7075 B / `47D8BB7E…`，差异来自重新实例化后新的场景 `uid`）。

**载荷字节链**（`recovery\work\task106\logs\payload-chain-task106.txt`）：

```
SnakeSegment.cs    inline   call=79987161BD21A5E3 payload=79987161BD21A5E3 project=79987161BD21A5E3 OK
Food.cs            inline   call=4841EB57F41C67E8 payload=4841EB57F41C67E8 project=4841EB57F41C67E8 OK
SnakeGame.cs       sidecar  call=14E88DCB573803A3 payload=14E88DCB573803A3 project=14E88DCB573803A3 OK
checked: 3 ; problems: 0        PAYLOAD_CHAIN OK
```

### A5 独立复算（不是转述）

**(a) 逐调用像素差** —— `recovery\work\task097\pixel_recompute.py`（**不 import `game_report.py`**，自己读 trace、自己解码 PNG、两套规则各算一遍）与 `recovery\work\task106\frames_t106.py` 给出同一组数：

```
trace-editor.jsonl: pairs=20 comparable=20 non-zero=1
  seq=8  editor_add_nodes_batch   engine=213200 any=213200 reported=213200
trace-game.jsonl:   pairs=33 comparable=33 non-zero=11
  seq=5   running_game_execute_gdscript           engine=480000 any=480000 reported=480000
  seq=8   running_game_run_test_scenario          engine=3456   any=3456   reported=3456
  seq=10  running_game_get_node_property_samples  engine=480000 any=480000 reported=480000
  seq=12  running_game_execute_gdscript           engine=480000 any=480000 reported=480000
  seq=14  running_game_run_test_scenario          engine=4032   any=4032   reported=4032
  seq=17  running_game_run_test_scenario          engine=2880   any=2880   reported=2880
  seq=19  running_game_execute_gdscript           engine=4032   any=4032   reported=4032
  seq=20  running_game_run_test_scenario          engine=3456   any=3456   reported=3456
  seq=21  running_game_execute_gdscript           engine=4608   any=4608   reported=4608
  seq=26  running_game_execute_gdscript           engine=480000 any=480000 reported=480000
  seq=28  running_game_run_test_scenario          engine=480000 any=480000 reported=480000
  reported != recomputed: 0（两相都是 0）
```

**像素差 = 12/53 非零**（编辑器 **1/20**、游戏 **11/33**）；两套规则（engine>10 与 any-difference）在这批上给出相同结果。

**(b) `user://` 保存帧**（只取本轮会话写的那四个名字，不含 `user://` 里的历史探针）：

| 帧 | 大小 | 字节 | sha256（前 16） | 与前一帧（engine / any） |
|---|---|---|---|---|
| `snake-t0.png` | 800×600 | 3075 | `B74C75D6CDB2038B` | — |
| `snake-t1.png` | 800×600 | 3074 | `8F4D29281A8F8744` | **480000 / 480000** |
| `snake-t2.png` | 800×600 | 3083 | `5D24C01A6840BB88` | **4032 / 4032** |
| `snake-final.png` | 800×600 | 3071 | `40AF9C63130EF566` | **480000 / 480000** |

四个帧 sha **4/4 互不相同**。**边界声明**：`user://` 目录里还留着 `recovery\work\task094..096` 时期的探针 PNG（`diag-*` / `probe*` / `mirror-*` / `host-*`），`report.md` 的「Saved frames」表按 mtime 把它们也列进来了（同一大小的帧两两相比），所以那张表里 `snake-t0` 的「previous same-size frame」是 `host-c.png` 而不是本轮的帧。本轮不动那些文件（它们是前序任务的证据），上面这张表只取本轮会话的四个名字。

**(c) 断言与未声明失败** —— `recovery\work\task106\check_snake_task106.py`（读运行自己的 `*.json` 与自己的 `call-index.txt`）全绿：

```
A1 SNAKE_SELF lines: 1     SNAKE_SELF head=9,10 ...
A2/A3 rows with scenario_assertion_failed: 0 ; rows with assertion_failed: 2
      seq=4  tag=g04-park-check-must-fail   declared=YES
      seq=29 tag=g26-wall-assert-must-fail  declared=YES
A4 assertions: passed=16 failed=2 errors=0 ; UNDECLARED failing assertions: 0
A5 g19/g20/g20b/g22/g25/g26/g04 全部 OK
   场景树 38 个名字、0 个 '@'
   report.json assertions: passed=16 failed=2 undeclared=0
CHECK_SNAKE_TASK106 OK
```

**(d) 把 TASK-105 自己的两条检查逻辑指向新跑法** —— `recovery\work\task106\check56_undeclared_task106.py` 是 `check5_assertions.py` + `check6_undeclared.py` 的同一份逻辑，**只改了一行**（`snake` → `runs\snake\snake-task106-r1`；验收方的脚本留在 `%TEMP%\acc105\` 未动）：

```
TOTAL passed=1361 failed=6 errors=0
（snake 16 / 2：g04-park-check-must-fail、g26-wall-assert-must-fail）
g12/g27（pong）、g09/g24（breakout）、g04/g26（snake）—— 6 条失败全部 YES（都声明过）
UNDECLARED failing assertions in final runs: 0
CHECK56_TASK106 OK
```

对照 TASK-105 的原值：`TOTAL passed=1358 failed=9`、`UNDECLARED … : 3`。**3 条未声明失败全部消失，其余 6 条声明的 must-fail 一条不少。**

### A6 给下一次独立验收的入口（要读什么、要跑什么）

**要读**

1. `recovery\reports\TASK-106-REPORT.md`（本文件）与 `recovery\reports\ACCEPTANCE-TASK-105.md`（被判 `fail` 的原文，D-1 的三条事实与四处矛盾陈述）。
2. `GAME-LOOP-LOG.md`：第 3 行（Snake 行，含 TASK-106 重跑的口径）、S-3 行（`_eventDriven` 那条）、§「里程碑：20 款」后面的 **TASK-106 追记**。
3. `tools\sessions\snake\session.json`（修好的模板本体）与 `tools\game_report.py`（`assertion_summary()` / `DECLARED_NOTE_KEYS`）。
4. 运行产物：`runs\snake\snake-task106-r1\`（`engine-game.stdout.txt`、`ledger-*.txt`、`ledger-*.json`、`report.json` 的 `assertions` 段、`report.md` 的「未声明失败」一节、`g19/g20b/g22/g23/g25/g26` 的响应）。
5. 归档与清单：`recovery\work\task106\archive\snake-20260927-080911\` + 同名 `.manifest.json`；`recovery\work\task106\manifests\*.json`。

**要跑**（都在 `F:\moonbit-hof-rs\godot-mcp`，`cmd` 终端；验收方建议一律写到 `%TEMP%`，不要覆盖仓库里的归档）

```
python recovery\work\task106\check_snake_task106.py runs\snake\snake-task106-r1
python recovery\work\task106\frames_t106.py runs\snake\snake-task106-r1 "%APPDATA%\Godot\app_userdata\snake"
python recovery\work\task106\payload_bytes_t106.py runs\snake\snake-task106-r1 tools\sessions\snake\payload
python recovery\work\task106\check56_undeclared_task106.py
python recovery\work\task097\pixel_recompute.py runs\snake\snake-task106-r1
findstr /c:"SNAKE_SELF" runs\snake\snake-task106-r1\engine-game.stdout.txt
```

或者：把 TASK-105 自己的 `check5_assertions.py` / `check6_undeclared.py` / `check11_all_pixels.py` / `check7_all_ledgers.py` 的 `FINAL["snake"]` 改成 `runs\snake\snake-task106-r1` 后原样重跑（**这是最可追责的做法**：验收方的脚本，只改路径）。**预期**：`check5` TOTAL `passed=1361 failed=6 errors=0`；`check6`「UNDECLARED failing assertions in final runs: 0」；`check11` 的 Snake 列变成 12/53。

**要独立确认的三件事**（不要采信本报告）

1. `runs\snake\snake-task106-r1\engine-game.stdout.txt` 里 `SNAKE_SELF` 至少 1 次，且那一行的 `head=9,10`。
2. 同目录 `ledger-game.txt` 里 `scenario_assertion_failed` **0** 行、`assertion_failed` **2** 行，且那两行的 tag 是 `g04-park-check-must-fail` / `g26-wall-assert-must-fail`。
3. 六处文档表述现在都**同时带着两个时点**（「当时为错报…」+「TASK-106 重跑后…」），且没有一处把两者写成同一时点的结论。

---

## B. 六处与产物相反的表述（四处是任务点，另两处是同文件内的同类）

规则：修好前的口径写成「**当时为错报**：该轮 ledger 已标 `scenario_assertion_failed`」；修好后的口径写「**TASK-106 重跑后自撞路径已实测覆盖**」；两者以**时点**分开，不并存为同一时点的结论。

| # | 文件:位置 | 原文（错） | 改成 |
|---|---|---|---|
| B1 | `recovery\reports\TASK-093-REPORT.md:86`（§A3 表） | `\| 自撞判负 \| g20 / g22-self-collision \| LoseReason eq "self" passed \|` | 「**当时为错报**：`r6` 的 `g20` 钉板 `dir=1,0` 让头从 `10,10` 走向 `11,10`（离开身体），`SNAKE_SELF` 出现 **0** 次，同轮 `ledger-game.txt` 已把 `seq 19/22` 标成 `scenario_assertion_failed` —— **这条断言没有 passed**」+「**TASK-106 重跑后自撞路径已实测覆盖**：`dir=-1,0`、`SNAKE_SELF head=9,10`、`g22` 两条断言全部 passed」 |
| B2 | `GAME-LOOP-LOG.md:19`（Snake 行） | 「网格移动/食物增长/**自撞**/撞墙/计分全部由断言钉住（… `LoseReason=self`、`LoseReason=wall`）」+ 调用数/判定分布/缺陷数/证据路径仍是 TASK-093 口径 | 列改成「TASK-093：…；**TASK-106 重跑：…**」（20/33、53/53、判定分布、`scenario_assertion_failed` 2→0），缺陷数 **0 / 5**（S-1..S-4 + D-1），证据路径加 `runs\snake\snake-task106-r1\`，备注里删掉「自撞…由断言钉住」的错口径、换成两个时点的表述 + 新的像素差（12/53、480000/4032/480000） |
| B3 | `GAME-LOOP-LOG.md:260`（S-3 行） | 「`r6`：墙测 `LoseReason=wall`、自撞测 `LoseReason=self`，两条同时成立」 | 「**当时为错报**：`r6` 里只有墙测成立…（同轮 ledger 已标 `scenario_assertion_failed`），`_eventDriven` 修好的是 S-3 本身，但 `g20` 的钉板让头离开身体、`SNAKE_SELF` 出现 0 次」+「**TASK-106 重跑后自撞路径已实测覆盖**：…两条同时成立」 |
| B4 | `recovery\reports\TASK-097-REPORT.md:125`（§B3 第 4 条） | 「Snake `g04/g06/g08/g13/g14/g15/g17/g18/**g19/g22**/g25/g26`（含…Snake 的 `g19/g22/g26`）」 | 「仍然通过」的列表里**去掉 `g19/g22`**，并说明「**当时为错报**：原先把它们列进『仍然通过』又追认为『按设计失败』，与产物和命名约定都冲突」+「**TASK-106 重跑后自撞路径已实测覆盖**」 |
| B5 | `recovery\reports\TASK-093-REPORT.md:19`（§0 汇总行 A） | 「Snake：…、`LoseReason=self`、`LoseReason=wall`」 | 去掉未成立的 `LoseReason=self`，加「（**`LoseReason=self` 当时并未成立 —— 见 §A3 该行的更正与 TASK-106 重跑**）」 |
| B6 | `recovery\reports\TASK-093-REPORT.md:150`（§A4 缺陷表 S-3 行） | 「`r6` 墙测 `LoseReason=wall`、自撞测 `LoseReason=self` 同时成立」 | 同 B3 的两个时点口径 |
| （不改写） | `GAME-LOOP-LOG.md` §「里程碑：20 款（TASK-104 收口）」的 20 款一览表 | 第 3 行仍是 `20 / 31（51）`、`51/51`、`13/102`，合计仍是 2 554 次调用 | **整表保持 TASK-104 快照不动**（改它就会与它的合计行矛盾，也等于篡改历史快照）；在其后**追加**一条「**TASK-106 追记**」，写明当前最终轮与新数字 |

**B 段的两条边界（如实声明）**

1. B5/B6 不在任务点名的四处之内，但它们是**同一个错误陈述在同一个文件里的另外两处**。留着它们会让 TASK-093 报告自相矛盾，所以一并改，并按同一规则加时点标注 —— 这是**追加**，不是改写：每一处旧口径仍可读出来。
2. `TASK-093-REPORT.md:16` 的「Snake 网格移动/食物增长/**自撞**/撞墙/计分 …… **达成**」**未改**：它陈述的是交付范围，而自撞这条路在 TASK-106 重跑后**确实**被覆盖了。这一条我核对过，不再与产物相反。

---

## C. 报告生成层的「未声明失败」一格

### C1 改了什么（`tools\game_report.py`）

* 新增 `DECLARED_NOTE_KEYS` —— 与 `check6_undeclared.py` 同一组关键词，保证报告与独立判定用同一把尺。
* 新增 `declared_tags(run)` —— 声明从**运行自己的 `call-index.txt`**（驱动为每次调用写的 `tag|port|req_bytes|resp_bytes|note`）读出，而不是从某个会话文件名猜。
* 新增 `response_body()` / `assertion_summary(run)` —— 汇总运行自己保存的 `*.json`：`all_passed` 形状数 `passed/failed/errors`，`passed` 形状单条计数；逐条失败记为 `{tag, what, declared_because}`，`declared_because` 为 `None` 的就是**未声明失败**。
* `report.json` 增 `assertions` 段；`report.md` 增 `## 未声明失败 (undeclared failing assertions)`，**无论有没有都单列一格**：`* **未声明失败: N**`，有失败就逐条列出并标 `**NOT DECLARED**`。
* 它**不读台账的 flags**，所以「报告说没有未声明失败」与「台账没有 `scenario_assertion_failed`」是两条互相独立的证据。

### C2 实测（旧运行必须真的响）

`recovery\work\task106\reporttest.py` 把 TASK-097 的运行**复制到 `%TEMP%`** 后在新代码上生成报告（**归档的 `runs\snake\snake-clean-task097` 一个字节都没动**）：

```
scratch   : C:\Users\wyl\AppData\Local\Temp\task106-reporttest\snake-clean-task097 (234 files copied)
exit      : 0
## 未声明失败 (undeclared failing assertions)
* responses scanned (this run's own `*.json`): **100**
* assertions: **passed 13 / failed 5 / errors 0**
* declared failures (`-must-fail` tag or a note that says so): **2** — g04-park-check-must-fail, g21-boundary-unknown-property, g26-wall-assert-must-fail
* **未声明失败: 3**

| tag | what | declared because |
|---|---|---|
| `g04-park-check-must-fail` | node_state:position eq {'x': 120.0, 'y': 240.0} -> actual {'x': 576.0, 'y': 240.0} | tag carries -must-fail |
| `g19-turn-down` | scenario:DirectionY eq 1.0 -> actual -1 | **NOT DECLARED** |
| `g22-self-collision` | scenario:GameOver eq True -> actual False | **NOT DECLARED** |
| `g22-self-collision` | scenario:LoseReason eq self -> actual  | **NOT DECLARED** |
| `g26-wall-assert-must-fail` | node_state:LoseReason eq self -> actual wall | tag carries -must-fail |
```

**它数出来的 3 条，与 TASK-105 的 `check6_undeclared.py` 独立数出的 3 条完全一致**；对新跑法它给出 **未声明失败: 0**（`report.json` 的 `assertions.undeclared_count = 0`，`passed=16 failed=2`）。

> 生成文件的字节是 UTF-8（`report.md` 由 Python writer 以 `encoding="utf-8"` 写）；上面控制台里的中文乱码是 `cmd` 代码页的显示问题，不是文件内容问题 —— 已用码点核对：`## ` 后面是 `U+672A U+58F0 U+660E U+5931 U+8D25`（未声明失败）。

---

## D. 收尾

### D1 模块零改动 → 不重建、不 push（如实说明）

```
git -C godot status --short          → （空）
git -C godot rev-parse HEAD          → 1f9d0cb1c983301d4efa575c16986c551df23600
git -C godot rev-parse refs/remotes/origin/feature/mcp-server-module-rebuild
                                     → 1f9d0cb1c983301d4efa575c16986c551df23600
git -C godot branch --show-current   → feature/mcp-server-module-rebuild
```

本任务改的是：会话 JSON、`tools\game_report.py`、三份/四处文档 + `DECISIONS.md`、以及 `projects\snake` 的场景文件（由 MCP 调用重写）。**没有任何一行落在 `godot\modules\mcp_server\` 下**，因此没有编译输入变化 → **不重建两变体、没有可 push 的提交**（`HEAD` 与 `origin` 同级）。这与 TASK-104 §C 的免跑判定同源，但本轮**仍然把十道门跑满**（下节），不靠判定省事。

### D2 十道门（强制 `-RunGates`，真实退出码）

`powershell -NoProfile -ExecutionPolicy Bypass -File tools\run_gates.ps1 -Tag task106 -RunGates` → `runs\gates\task106\summary.txt`：

| # | 门 | exit | 关键输出 |
|---|---|---|---|
| g01 | 模块 doctests | **0** | `test cases: 157 \| 157 passed \| 0 failed`、`assertions: 6724 \| 6724 passed \| 0 failed`、`SUCCESS!`（9.1 s） |
| g02 | 全量 doctests | **0** | `1583 / 1583 passed / 3 skipped`、`assertions: 431037 \| 431037 passed`（32.4 s） |
| g03 | 组 manifest | **0** | `TOOL-GROUPS CHECK PASS`、`BYTES 5681`、`SHA256 b83d79d3e3d080ce460b61ca99a46a126d6a6c45eb3d51d7977a52a991b7fbc7` |
| g04 | 契约子集（活体） | **0** | `3/3 checks passed`（编辑器 9888 `tools=154`、游戏 9889 `tools=73`、`contract=177`、`guard_user_port_9877 pid_before=-1 pid_after=-1`） |
| g05 | 改名映射 | **0** | `RESULT: PASS (all checks green)`、`CONTRACT bytes=153330 sha256=bd68e80472c8e15d674c45bf5816ee708ea08cf71f209a0e0114373d6067b640` |
| g06 | 恒真断言 | **0** | `TAUTOLOGY CHECK PASS (every hit is pinned; scanned=2 file kind(s) under 2 root(s))` |
| g07 | 退出码传播 | **0** | `PROBES: 10/10` |
| g08 | 硬编码计数 | **0** | `BUCKET UNCLASSIFIED = 0`、`RESULT: PASS` |
| g09 | 引擎锚点 | **0** | `ANCHOR_JUDGE VERDICT=ANCHOR_STRUCTURAL_EQUIVALENT`、`ANCHOR=1c7f5c07a HEAD=1f9d0cb1c DIFF_COUNT=1 SAFE_COUNT=1 RED_COUNT=0`、`RESULT PASS` |
| g10 | `accept_m1` | **0** | **`22/22 cases passed`**（41.6 s） |

预检（同一份 `summary.txt`）：`VERSION_TEXT=4.8.dev.mono.custom_build.1c7f5c07a`、`VERDICT=RUN_GATES`、`REASON="-RunGates was given"`、`GATES_SKIPPED=0`、`WORKING_TREE_RED=0`。

门后进程与端口：无 `Godot*`/`dotnet*` 残留，9888 / 9889 / 9930 / 9931 均无监听。

### D3 铁律遵守

| 铁律 | 遵守情况 |
|---|---|
| ① 禁止一切 shell 重定向 | **全程零 shell 重定向**。所有构建/运行/门由 `Start-Process -RedirectStandardOutput/-RedirectStandardError` 拥有 stdout/stderr（`run_game_session.ps1`、`run_gates.ps1`、`run_one.ps1`、`new_game_run.ps1`、`reset_game_project.ps1`）；所有文本文件由 Python writer 或 `edit` 工具写（`check_*.py` 的输出、`report.md`/`report.json`、`reporttest.py` 的副本）。本任务没有出现一次 `>` / `>>` / `2>&1` |
| ② 破坏性命令默认拒绝 | **零删除**。唯一的目录移动是 `projects\snake` → `recovery\work\task106\archive\snake-20260927-080911\`（`Move-Item`，前提是 sha256 清单已落盘）；两个旧跑法原地未动；`reporttest.py` 只在 `%TEMP%` 的副本上重生成报告。未杀任何非本任务进程、未改设备/注册表/电源/显示拓扑 |
| ③ 构建与运行从 cmd 启动 | 所有 `term` 调用都在 `cmd` 终端；引擎由生成的 `.cmd` 经 `Start-Process cmd.exe /c` 启动；`dotnet build` 由 `project_build_csharp`（MCP 调用）触发 |
| ④ 唯一端口 + 跑前查进程与端口 | 本次只用 **9930 / 9931**（会话）与门的 **9888 / 9889**；跑前跑后各做一次 `tasklist` + `netstat`，`PORT_CHECK: all wanted ports free` |
| ⑤ 会话文件先 Python + PS 5.1 双解析 | `check_session.py`（JSON + 形状 + `content_file` 可达 + 5 块钉板）与 `check_session_ps.ps1`（PS 5.1 `ConvertFrom-Json` + 同一批钉板）在开引擎前都 PASS，且两侧列出的钉板逐字一致 |
| ⑥ 不改变机器显示或串流状态 | 未停 `GameViewer`、未动设备/注册表/电源、未接触显示拓扑 |

**一处未预料的读数（如实登记，不作为缺陷）**：编辑器相有 3 行带 `flags=result_unparseable`（`project_validate_scripts`、`editor_add_nodes_batch`、`editor_get_scene_tree`）。这不是本轮引入的：TASK-093 r6 与 TASK-097 的编辑器相同样带这个 flag（同一批工具）。已核对，只记录。

### D4 一处**未动的既有脏文件**（如实说明，避免下游误读）

`git status --short` 里有两条**本任务完全没碰**的已跟踪改动：

```
 M godot-mcp/recovery/work/task104/logs/git-housekeeping.err.txt   (+4 行)
 M godot-mcp/recovery/work/task104/logs/git-housekeeping.out.txt   (+11 行)
```

它们是 TASK-104 收口时"先提交日志、日志随后又被那次 git 操作追加"的产物（TASK-104 §F4 记过同类现象）。**本任务没有改它们，也没有把它们纳入本次提交**；`git status --short` 因此不是全空。要不要把它们归到 TASK-104 的收尾里，留给下一轮决定，我不替它做。

---

## E. 本任务产出的文件

```
tools\sessions\snake\session.json          修好的会话模板（+9 −3）
tools\game_report.py                       assertion_summary() / DECLARED_NOTE_KEYS / report 的「未声明失败」一格
projects\snake\scenes\main.tscn            归档后从模板重新实例化、再由 MCP 调用重写的场景（38 节点、0 个 @ 名）

GAME-LOOP-LOG.md                           第 3 行重写 + S-3 行更正 + TASK-106 追记
recovery\reports\TASK-093-REPORT.md        §A3:86、§0:19、§A4:150 三处时点标注
recovery\reports\TASK-097-REPORT.md        §B3:125 时点标注
recovery\reports\TASK-106-REPORT.md        本文件
recovery\reports\ACCEPTANCE-TASK-105.md    TASK-105 的验收报告（上一轮未提交，本轮纳入提交）
DECISIONS.md                               D153

recovery\work\task106\
  hash_tree.py                             目录 sha256 清单（铁律 6）
  check_session.py / check_session_ps.ps1  会话双解析（Python + PS 5.1）
  check_ports.ps1                          跑前跑后进程与端口
  new_game_run.ps1 / reset_game_project.ps1 / run_one.ps1   统一走 cmd 的运行器
  check_snake_task106.py                   本轮 5 条判据的机械核对
  frames_t106.py                           保存帧 + 逐调用对的独立复算
  payload_bytes_t106.py                    三方法定载荷字节链
  check56_undeclared_task106.py            TASK-105 的 check5+check6，只改 snake 路径
  reporttest.py                            在 %TEMP% 副本上验证「未声明失败」一格真的会响
  manifests\projects-snake-pre-task106.json / run-snake-clean-task097.json / run-snake-task093-r6.json
  archive\snake-20260927-080911\ + 同名 .manifest.json      旧工程（Move-Item，零删除）
  logs\                                    check-snake / frames / payload-chain / check56 / run / hash / new-game
runs\snake\snake-task106-r1\               新最终轮（trace ×2、ledger ×2、53 条响应、report.json/md、引擎 stdout/stderr、shots-*）
runs\gates\task106\                        十道门的 summary.txt 与 g01..g10 的 stdout/stderr
```

> `runs\` 按 `.gitignore` 不入库（盘上真实存在，本文所有 `runs\...` 引用都是盘上路径）；`recovery\work\task106\`（`.godot` 缓存被忽略）与其余产出入库。

---

## F. 边界与遗留（如实列，不替它们下结论）

1. **`g20` 的钉板让头撞进「颈格」而不是「尾格」**：`SimulateStep()` 的自撞检查覆盖 `i = 1..Length-1`（含颈与尾），且检查发生在身体移动**之前**（`SnakeGame.cs:421-434` 的注释说明「头进入尾格不算死」是有意设计）。本轮的 `10,10 → 9,10` 撞的是 `i=1`（颈），**不是** `i=Length-1`（尾）。「头进入尾格不死」这条规则**仍未被子会话钉住** —— 它属于未覆盖路径，本轮没有声明要测它，也没有把它写进台账。
2. **`user://` 目录的前序探针 PNG 仍在**（见 §A5(b)）：`report.md` 的 Saved frames 表会列出它们，读表时要按名字挑本轮的四个。本轮选择不动它们（那是 task094–096 的证据），代价就是那张表不"干净"。
3. **TASK-105 的另一条 medium（D-3：`--import` 关机期访问违例）** 不在本任务范围。本轮 `IMPORT_EXIT=0`、`import` 进程 exit 0，`import.stderr.txt` 见运行目录；累计口径仍按 `GAME-LOOP-LOG.md` 的原记录读，本轮不重新定论。
4. **`snake-clean-task097` 会话文件（`tools\sessions\snake\session-clean-task097.json`）未改**：它是 TASK-097 生成的历史工件（清理副本层 + 原样重放），它的重放里嵌着**旧版**的 `g19/g20`。本轮不再重放它（那需要先把工程重新做成"带 37 个副本"的状态），因此它作为**历史证据**保留；当前最终轮是 `runs\snake\snake-task106-r1`，由模板本体 `session.json` 直接产生。
5. **我无法证明 `report.md` 的中文在别人的终端上不乱码**（本轮已用码点核对文件字节是 UTF-8，见 §C2 的注）。
6. **本报告 §G 的两仓账是"本报告提交之后、任何纯文档追加之前"的时刻**：此后若再有纯文档追加提交（包括携带 §G 的那一次），只会让主仓 `git log` 顶部多出文档提交，不会改变 §D4 说的那两条脏文件与 §D1 的引擎锚点。

---

## G. 提交后的逐字复核（两仓）

> **边界说明**：本节的两段账是**本报告那次提交之后、携带本节的纯文档提交之前**的那一刻。此后任何纯文档追加都只让主仓 `git log` 顶部多出文档提交；`§D1` 的引擎锚点（`1f9d0cb1c`）与 `§D4` 的两条脏文件不会因此改变。

（待提交后回填 —— 见本次提交之后的追加。）
