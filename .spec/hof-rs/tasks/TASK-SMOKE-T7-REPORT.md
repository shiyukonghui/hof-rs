# TASK-SMOKE-T7-REPORT — 真机 T=1 复测（引擎 `035edfce7`，含 TASK-151 修复；§15/DR-54..56 之后）

- 任务书：`.spec/hof-rs/tasks/TASK-SMOKE-T7.md`
- 落点：`F:\moonbit-hof-rs`（`master`，HEAD `2e15578`，工作树干净）
- 轮次：**真机 T=1**，`target/release/hoh.exe run --iterations 1 --run-id smoke-t7`
- 报告人：执行子代理（无上游上下文；只跑与取证，**未改** `src/**`、`tests/**`、`godot-mcp/**`、`PRD-mario.md`、`runs/smoke-t6/**`）
- 时间：2026-09-29 13:26:16 → 14:41:14（+0800），墙钟 **74 分 58 秒**

---

## 1. 结论（E1..E6 逐条，附原始证据）

| 编号 | 判定 | 一句话依据 |
|---|---|---|
| **E1** | **not_met** | 三角色真跑、`D_1`/`E_1` 合法，但 **Developer 零工程增量**（`evidence_diff` 三段全空，`A_1 == A_0 == fc78d299…`） |
| **E2** | **met** | `artifact_gate.launchable = true`、`reasons = []`、**退出码 0**；`editor_errors_baseline ok=true`（唯一一行是引擎信息横幅，被 DR-48 按**确切形态**豁免） |
| **E3** | **not_met** | ①端点正常 ②语义工具**真被调用**且 6 类中 5 类成功 ③**端点未挂死**（全轮 0 次传输失败）④关键路径非 `execute_gdscript` 承重 —— **但**左右移动/跳跃/交互/终点**无一被证实**，QA 全落 gap |
| **E4** | **met** | 8 条 verified 的 `execution_records` **逐条实存**（我逐条核验 8/8 文件存在）；20 条未证者全落 gap |
| **E5** | **met（强）** | 我**自己重实现**三棵树字节级比对：workspace / candidate / 存储版本各 **17 文件、同一摘要 `528cad59…`、集合与内容差异 0** |
| **E6** | **met** | 20 条 gap 如实列出全部未达成（含 QA **自己**记下的 G20 观测缺陷）；无一条未达成被写成 verified |

### 1.1 E1（not_met）——原始证据

```
$ cat runs/smoke-t7/exit_code
0
$ python inspect.py raw runs/smoke-t7/iter-1/result.json evidence_diff
{"added": [], "modified": [], "removed": []}
$ cat runs/smoke-t7/warnings.log
qa_scope: ...
iteration 1: no_progress (the developer stage produced no change)
$ cat runs/smoke-t7/versions/index.json | grep version_id
"A0 initial artifact"   -> fc78d299e6dcc9711d5d38c6d04191e586def586d9d0daec70358f3353579d3c
"A1 after the developer and deterministic stages" -> fc78d299e6…(同一)
$ tail -2 runs/smoke-t7-console.txt
run smoke-t7 finished: 1 iteration(s), final version Some("fc78d299e6…"), total tokens Some(22424721)
prd coverage: 8/28 verified (...)
```

- `D_1` 合法：`runs/smoke-t7/iter-1/plan.md`（3187 B）含 `### Priority Order` / `### Preservation Gate` / `### Acceptance Gate`；
  `planner.attempt1.log` 的 `artifact_valid: true`。
- `E_1` 合法：`runs/smoke-t7/iter-1/evidence.json`（34880 B）`qa_status=partial`，`verified_records=8`、`gap_records=20`，绑定 `candidate_id=fc78d299…`。
- **增量缺失**：Developer 没有改变任何工程文件；`result.json.warnings` 含 `"no_progress"`。
  ⇒ E1 的"Developer 产出 Godot 工程增量"一条**不成立**，故 E1 **not_met**（与 `smoke-t6` 同型）。

### 1.2 E2（met）——原始证据

```
$ cat runs/smoke-t7/meta.json | sed -n '/artifact_gate/,/},/p'
"artifact_gate": { "applicable": true, "launchable": true, "reasons": [] }
$ python inspect.py raw runs/smoke-t7/iter-1/candidate/.hoh/deterministic/battery.json 2 record.observation
"editor reported 1 error(s): {… "count":1, "errors":["[MCP] capture=off (default; use --mcp-capture=on_error|every_call together with --mcp-trace=<path>)"], "pid":75204, "port":9877 …}
 (only the engine's own informational banner(s) were reported; 1 line(s) exempted by DR-48)"
"ok": true
```

- 同一行在 `smoke-t6` 使闸门判 false（见 §6 对照）；本轮闸门 **launchable=true**，`exit_code=0`。
- 闸门构成（`src/adapter/mod.rs:36-41`）= `editor_errors_baseline.ok && play_scene_ready.ok`：
  前者 `ok=true`（上面原文），后者 `ok=true`（`play_scene_ready` 观测："main scene booted; the game answered `running_game_get_scene_tree` after 1 poll(s) with 50 node(s)"）。
- 反例（豁免非一刀切）见 §5。

### 1.3 E4（met）——原始证据

- 8 条 verified（V1..V8）的 `execution_records` 全部指向 `candidate/` 视图下的真实文件，我逐条判存在性，**8/8 全 True**：
  `raw/{project_reload_and_open,play_scene_ready,scene_structure,scene_tree,editor_errors_baseline,editor_stop_scene}.json`、
  `battery.json`、`mcp-sync.json`、`.hoh/evidence/frame-00.png`。
- 未证者全落 gap：`prd_coverage = {verified: 8, gap: 20}`，`gap_ids=[G1..G20]`。
- QA 自述（`runs/smoke-t7/iter-1/qa_report.md`，第 9 行）：
  "Only battery steps marked `ok=true` were allowed to support a `verified` claim … editor-side injections (`EDITOR_SIDE_INJECTION`) were treated as non-evidence."
- **强于 `smoke-t6`**：`smoke-t6` 的 V7 依赖一张 2026-09-21 的**旧 PNG**；本轮 `frame-00.png` 是**本轮新鲜**的
  （5860 B、mtime `2026-09-29 14:32:24.889`、sha256 `480a7ce7cd67f96edc814a0fd621469900ee76b8244c37f7ea80b7edae70ecbd`），
  且旧文件被改名保留为 `frame-00.png.stale-1790663544`（4246 B、mtime `2026-09-21 17:55:00`）——DR-49 在真机上成立。

### 1.4 E5（met，强）——原始证据（我自算，不用工具自报）

我**自己重实现**了一遍"QA 有没有改 `A_1`"的检查（脚本 `hash_tree_check.py`，算法写死并打印）：
对每棵树枚举文件（排除 `.godot`/`.import`/`.hoh`，即工程树）、对每个文件自己算 sha256、
按 `"<relpath>\0<size>\0<sha256>\n"` 排序后取 sha256：

```
$ python hash_tree_check.py .workspace/mario runs/smoke-t7/iter-1/candidate \
    runs/smoke-t7/versions/fc78d299e6dcc9711d5d38c6d04191e586def586d9d0daec70358f3353579d3c
workspace        files=17   digest=528cad59ad9b8fca5237ec221733b6bb745be8ba1db340442900d396a531e1b2
candidate        files=17   digest=528cad59ad9b8fca5237ec221733b6bb745be8ba1db340442900d396a531e1b2
stored_version   files=17   digest=528cad59ad9b8fca5237ec221733b6bb745be8ba1db340442900d396a531e1b2

workspace_minus_candidate    0 []
candidate_minus_workspace    0 []
workspace_minus_version      0 []
version_minus_workspace      0 []
content differences across the three trees: 0
THREE TREES BYTE-IDENTICAL: True
```

- 三个视角（真实 workspace、QA 冻结副本 candidate、版本库存储的 `A_1`）**逐字节同一**。
- 我的摘要值（`528cad59…`）与运行时自报的 `candidate_id`（`fc78d299…`）**不同**，这是**算法不同**的正常结果，
  也正说明我的结论不依赖 `hash_tree` 的实现口径 —— 结论建立在"文件集合与字节内容逐一相等"之上。
- 原始输出留档：`runs/smoke-t7-experiment/e5_hash_tree.json`。

### 1.5 E6（met）——原始证据

- `gap_records` 20 条把**全部未达成**如实列出，措辞保守到"NOT OBSERVED / NOT EXERCISED / UNVERIFIABLE / NOT MEASURED"（节选）：
  - `G1 F1: holding move_right/move_left changes Player.position.x … NOT OBSERVED.`
  - `G2 F2: pressing jump gives upward velocity … NOT OBSERVED.`
  - `G3 F3: facing changes … NOT OBSERVED - no attributable input was delivered.`
  - `G10/G13/G14/G16/F10/F13/F14/F16: … NOT OBSERVED / NEVER EXERCISED`
  - `G19 P3/N2: the game process actually honours the InputMap actions … UNVERIFIABLE.`
- QA 甚至把**运行时自身的观测缺陷**也落成 gap（`G20`）："the node_and_collision_assertions step is scored ok=false (Player=missing …) although its own raw payloads returned resolved property dictionaries … so the runtime observability assertion that QA depends on is unreliable."
- 我构造的**反例（偏差方向）**：检查最容易被"洗白"的一族 —— 截图证据。
  结论：本轮截图确为**本轮新鲜产物**（5860 B / mtime 在电池窗口内 / 旧文件被改名），**没有**出现 `smoke-t6` 的旧 PNG 假证据；
  同时 QA 对 `input_replay ok=true`（电池层判绿）**拒绝**升级为 verified（G1-G3 仍为 gap）——偏差方向一律保守。
- ⇒ E6 **met**。

### 1.6 E3（not_met）——详见 §2

---

## 2. E3 专项（§2.3 四问逐条 + 原始输出）

### 2.1 ① `editor_play_scene` 是否仍正常返回端点/pid —— **是**

我自己的独立实验（`hoh tools call editor_play_scene --role developer`，留档 `runs/smoke-t7-experiment/play_scene_via_hoh.txt`）：

```
{"args_deduplicated":[],"args_injected":["--mcp-port=57939"],
 "endpoint":"http://127.0.0.1:57939/mcp","headless":false,"mcp_port":57939,
 "mcp_port_source":"auto_free_port","mode":"main","pid":119692,"playing":true}
```

本轮 run 内（`runs/smoke-t7/iter-1/candidate/.hoh/deterministic/raw/play_scene_ready.json`）：

```
tool: editor_play_scene ok=True args={"mode": "main"}
payload: {"args_injected":["--mcp-port=55225"],"endpoint":"http://127.0.0.1:55225/mcp",
          "mcp_port":55225,"mcp_port_source":"auto_free_port","mode":"main","pid":113088,"playing":true}
```

`meta.json.engine.mcp.game_endpoint = {"endpoint":"http://127.0.0.1:55225/mcp","pid":113088,"port":55225,"source":"auto_free_port"}`
（`smoke-t6` 此处结构性为 `null` —— DEF-D 已修，真机验证）。

### 2.2 ② `running_game_*` 语义工具是否**真被调用并成功** —— **6 类中 5 类成功，1 类必失败**

本轮 run 的原始证据里，按工具逐条点算（我的 `tally_calls.py` 直接从 `raw/*.json` 的 `calls` 结构化条目里抽）：

`raw/input_channel_probe.json`（8 条调用）：

| 工具 | 结果 | 逐字入参 |
|---|---|---|
| `running_game_get_node_properties` | **ok** | `{"node_path":"Player"}` |
| `running_game_get_node_property_samples` | **ok** | `{"frame_count":1,"frame_interval":1,"node_path":"Player","properties":["input_axis"]}` |
| `running_game_create_input_recording` | **ok** | `{}` |
| `running_game_play_input_recording` | **ok** | `{"events":[{"action":"move_right","pressed":true,"type":"action"}],"speed":1.0}` |
| `running_game_run_test_scenario` | **FAILED** | `{"scene_path":"current","steps":[input move_right / wait / assert …]}` |
| `running_game_stop_input_recording` | **ok** | `{}` |
| `running_game_get_node_property_samples` | **ok** | `{…,"properties":["position"],"frame_count":30}` |
| `running_game_execute_gdscript` | **ok** | `{"code":"return str(get_tree().current_scene.get_node_or_null(\"Player\").position.x) + …"}` |

`raw/input_replay.json`（13 条调用）：`editor_get_input_actions` ×1、`editor_simulate_input_action` ×8（**编辑器侧**）、
`running_game_get_node_property_samples` ×4（**ok，game 通道**）。**没有**任何 `running_game_create/play_input_recording`、`run_test_scenario`。

`raw/node_and_collision_assertions.json`（6 条调用）：`running_game_get_node_properties` ×3（**ok**，Player/Goal/HUD）、
`editor_get_collision_info` ×3（ok）。

**唯一的失败是 `running_game_run_test_scenario`，且失败原因在 hof-rs 传的入参上，不是引擎挂死**：

```
$ python e3_scenario2.py http://127.0.0.1:57939/mcp runs/smoke-t7-experiment/scenario
C1 steps-only (no scene_path)                       0.03s  OK {"all_passed":false,"completed_steps":1,…}
C2 scene_path=main                                  0.00s  JSONRPC_ERROR code=-32602 msg=Parameter 'scene_path' ('main') is not supported by the game-scope runner: … Use editor_play_scene (editor endpoint) first…
C3 scene_path=res://scenes/main.tscn                0.00s  JSONRPC_ERROR code=-32602 msg=Parameter 'scene_path' ('res://scenes/main.tscn') is not supported by the game-scope runner: …
C4 hof-rs steps, scene_path omitted                 0.02s  OK {"completed_steps":3,"failed":1,…[{"action":"move_right","in_input_map":true,"injected":1,…}]}
C5 input+wait only                                  0.02s  OK {…"in_input_map":true,"injected":1…}
C6 assert-only input_axis                           0.02s  OK {"…,"reason":"node '/root/Main/Player' does not have the property 'input_axis'","passed":false…}
C7 assert-only position                             0.01s  OK {"actual":{"x":874.758…,"y":283.925…},"passed":false…}
```

⇒ 引擎**任何** `scene_path` 值都拒绝（游戏态 runner 不接受该参数），而 `src/adapter/godot.rs:1597-1604`（DR-54，commit `6329e5c`）
的 `axis_args` **硬写** `"scene_path":"current"` ⇒ 每次必得 `-32602`。

另有一条同类问题（**同一"键名/形状假设"错误**，属 DR-54 新增）：

```
$ python inspect.py a7    # running_game_get_node_properties {"node_path":"Player"} 的真实回包
top-level keys: ['node_path', 'properties', 'type']
name = None
```

`src/adapter/godot.rs:1253-1257`（`6329e5c`，DR-54）把"游戏进程可达"判为
`parsed.get("name")` 非空 —— 引擎**不返回顶层 `name`**（节点名在 `properties.name`，且只在部分节点类型上存在）
⇒ `game_process_reachable` 恒 `false`。这就是本轮探针的原始观测：

```
"game process via semantic tools: reachable=false, axis_before=None, injection accepted=true,
 axis_after=None, axis moved=false; read-only execute_gdscript probe=Some((173.666687011719, 283.998992919922))
 (supplementary only, DR-54)"

⇒ capability = ACTION_BINDING_UNKNOWN（不是 ACTION_NOT_BOUND：-32602 的文面说的是 scene_path，不含 ACTION_NOT_BOUND 标记）
```

**同一个键名假设还命中了 `node_and_collision_assertions`**（该处代码 `src/adapter/godot.rs:2051-2055` 来自 **`00601476`，2026-09-21，属既有代码**，非 DR-54）：

```
"node properties: Player=missing, Goal=missing, HUD=missing; collision shape_count: Ground=1, Player=1, Goal=1;
 HUD visible text node(s): 2 (UNAVAILABLE: at least one required node or collision shape is missing)"
```

而它**自己的原始回包**是成功的、`node_path` 解析到了 `/root/Main/Player`、`/root/Main/Goal`、`/root/Main/HUD`
（`properties` 字典齐全；HUD 的 `properties.name == "HUD"`）。⇒ 判 `missing` 是**误读**，不是节点不存在。
（QA 自己也把这一条记为 `G20`。）

### 2.3 ③ 游戏端点在"编译不过/被拒绝的调用"之后是否仍然存活 —— **是（TASK-151 验收点在真机上转绿）**

**(a) 我构造的主动实验**（基线 `editor_play_scene` 起游戏 → 直连游戏端点 `http://127.0.0.1:57939/mcp` 发 JSON-RPC，
与 hof-rs 同形：`{"jsonrpc":"2.0","id":N,"method":"tools/call","params":{"name":…,"arguments":…}}`，见 `src/tools/mcp.rs:389/393`）：

```
$ python e3_survival.py http://127.0.0.1:57939/mcp runs/smoke-t7-experiment/raw
A1 baseline get_scene_tree                           OK         0.04s  OK
A2 compile-failing code (TASK-151 trigger)           JSONRPC_ERROR 0.01s code=-32602 msg=Parameter 'code' does not compile at line 1 of 'code': Parse Error: Identifier "this" not declared in the current scope.
A3 get_scene_tree AFTER the compile failure          OK         0.00s  OK
A4 valid read-only probe                             OK         0.00s  OK
A5 semantic refusal (no recording)                   JSONRPC_ERROR 0.00s code=-32602 msg=Parameter 'events' must not be empty: there is nothing to replay …
A6 get_scene_tree AFTER the refusal                  OK         0.01s  OK
A7 semantic get_node_properties                      OK         0.00s  OK
A8 semantic get_node_property_samples                OK         0.08s  OK
A9 semantic create_input_recording                   OK         0.00s  OK
A10 semantic stop_input_recording                    OK         0.00s  OK
A11 final get_scene_tree                             OK         0.02s  OK
```

- `A2`：TASK-151 的字面触发形态（编译不过的 `code`）在 **0.01 s** 内得到契约规定的 `-32602`；
  `smoke-t6` 在同一形态下是**状态行始终不来**（`10060`，重试 3×120 s，随后 `10061`，首→末约 730 s）。
- `A3/A6/A11`：编译不过**之后**、语义拒绝**之后**、以及全流程**之后**，端点都照常回答。
- `A5` 是**业务错误**（`-32602`），端点同样存活。

**(b) 本轮 run 内**：整轮 MCP 错误日志**只有一行**，且 `attempt=1`：

```
$ wc -l .workspace/mario/.hoh/deterministic/mcp-errors.jsonl
1
$ cat .workspace/mario/.hoh/deterministic/mcp-errors.jsonl
{"attempt":1,"code":-32602,"message":"Parameter 'scene_path' ('current') is not supported by the game-scope runner: …","timestamp":1790663544,"tool":"running_game_run_test_scenario"}
$ grep -c "10060\|10061\|status line\|Connection Failed" .workspace/mario/.hoh/deterministic/mcp-errors.jsonl runs/smoke-t7/iter-1/candidate/.hoh/deterministic/mcp-errors.jsonl
0  0
```

⇒ **全轮 0 次传输层失败、0 次端点判死**；游戏端点从未挂死（TASK-151 修复在真机端到端成立）。
同时这**实测**了 DR-56：同一个 `-32602` 现在**恰好尝试 1 次**（`smoke-t6` 是 3 次）。

**(c) 收尾**：本轮游戏进程 `pid 113088` 已消失、`55225` 无 LISTENING；我实验的 `pid 119692` 亦已消失、`57939` 无 LISTENING；
`9877` 仍由编辑器 `pid 75204` 监听（**未被我触碰**）。

### 2.4 ④ 关键断言是否由**语义工具**产出、`execute_gdscript` 是否**只**做只读探针 —— **结构上是；但关键断言本身没有产出**

- **`execute_gdscript` 只做只读探针**：证据有两条。
  1. 全轮只剩 1 个 `execute_gdscript` 调用点，入参是常量函数体且带 `return`（见 §2.2 表末行）。
  2. **非空洞性在真机上被直接观测到**：探针**返回了值**（`Some((173.666687011719, 283.998992919922))`），
     而判定**仍是** `ACTION_BINDING_UNKNOWN`（观测文本明写 `(supplementary only, DR-54)`）
     ⇒ 判决不依赖它的值。
- **但"关键断言"没有产出**：E3 要求的行为（左右移动、跳跃、≥1 可交互对象、终点/胜负）**一条都没被证实**，
  QA 把它们全部落 gap（G1-G3、G5-G6、G10-G16）。可判定的部分只有：
  - **右向位移存在**（语义读数 `running_game_get_node_property_samples`：`before 181.00 → after 397.33`、`404.67→437.67`、`441.33→547.67`、`555.00→771.33`）；
  - **跳跃没有位移证据**（4 个 quadruple 的 `y` 恒为 `283.998992919922`，`velocity.y = 0.0`）；
  - **左向移动未被证实**（标为 `move_left` 的那一段 `x` 反而**递增** `554.99 → 771.33`，`velocity.x = +3.667`）；
  - QA 对这段数字的定性与我一致："notably the `move_left` attempt still shows x increasing (555 -> 771) with velocity.x=+3.667, so those numbers cannot be attributed to the action"。
- 因此 E3 **not_met**：不是"被证伪"，而是**未被证明**；且其中"输入通道可不可读/动作是否绑定"这一层
  在本轮**不可判定**（通道判 `ACTION_BINDING_UNKNOWN`，见 G19）。

---

## 3. 退出码与 tokens/耗时；`artifact_gate.launchable`

| 项 | 值 | 证据 |
|---|---|---|
| 退出码 | **0** | `runs/smoke-t7/exit_code` = `0`；`meta.json.exit_code = 0` |
| `artifact_gate` | `{"applicable":true,"launchable":true,"reasons":[]}` | `runs/smoke-t7/meta.json` |
| 理由 | 闸门只由 `editor_errors_baseline.ok && play_scene_ready.ok` 决定，两者皆 `ok=true`；被 DR-48 豁免的确切形态是引擎横幅 `[MCP] capture=off …`（唯一 1 行，引擎 `pid=75204`、`port=9877`） | `src/adapter/mod.rs:36-41`；`raw/editor_errors_baseline.json` 观测原文 |
| 电池分步 | 11 步中 **9 步 ok**；失败两步是 `input_channel_probe`、`node_and_collision_assertions`（**均不在闸门判据内**，属产品可观测性，落 gap） | `runs/smoke-t7/iter-1/result.json.battery_passes[0]` |
| tokens（本轮总计） | **22,424,721** | 控制台尾行；`usage.json.summary` |
| tokens（分角色） | planner 2,511,163（150 调用）/ developer 11,495,447（150）/ tester 8,418,111（150） | `runs/smoke-t7/iter-1/usage.json` |
| attempt | **3 次，全部 `LimitsExceeded`**（planner 1 / developer 1 / tester 1） | `result.json.attempts`；`logs/*.log` 的 `exit_status` |
| 耗时 | 墙钟 **74 分 58 秒**（13:26:16 → 14:41:14）；分角色 planner 866.2 s / developer 3095.2 s / tester 524.2 s | `result.json.durations_ms`；文件 mtime |
| repair_retry | **未触发**（`repair_retry_used=false`），因闸门首轮即 `launchable=true` | `result.json.repair_retry_used` |
| 密钥卫生 | `runs/smoke-t7` 下密钥明文出现 **0** 个文件；`result.json.secret_redactions = 0` | `grep -rlF <key>` 计 0 |

### 3.1 "判死前的重试乘法"是否出现 —— **本轮未出现（且这正是被压掉的部分）**

- 全轮 MCP 错误日志**仅 1 行**且 `attempt=1`（§2.3b）：`-32602` 是业务错误 ⇒ DR-56 使其**恰一次**，
  不再有"上层重试 × 传输层重试"的放大（`smoke-t6` 同一个 `-32602` 被重试 3 次）。
- 全轮**没有任何传输层失败** ⇒ DR-55 的端点判死路径**未被触发**，也就没有"判死前最多约 6 次 HTTP 尝试"的干烧。
- 诚实边界：因此本轮**不能**证实 DR-55 的判死阈值/零重试在真机上的行为（它是"没被用到"，不是"被验证"），
  这一点在 §7 列为未验证项。D239 记的"判死前乘法"仍是**未关闭**的设计问题（`mcp.rs` 未改）。

---

## 4. 引擎身份（判据 / 记录严格分开）

| 项 | 值 | 性质 |
|---|---|---|
| **`version_string`** | **`4.8.dev.mono.custom_build.035edfce7`** | **判据**：与任务书要求的引擎身份**逐字相符**（`meta.json.engine.version_string`） |
| `binary.sha256` | `08483088a4a2772841cd3b4c916b2d45b3cb6255656cf3951598a86fce7e9e6a` | **仅记录**（引擎构建非位级可复现；不得当"新鲜/一致"判据） |
| `binary.size_bytes` / `mtime_unix` | 194,216,960 / 1790641862 | 记录 |
| `binary.path` | `F:/moonbit-hof-rs/godot-mcp/godot/bin/godot.windows.editor.x86_64.mono.exe` | 记录 |
| 监听者 | `listener.pid = 75204`，`matches_binary = true`，path 同上 | `meta.json.engine.listener` |
| 编辑器端点 | `GET http://127.0.0.1:9877/mcp` → `{"status":"ok","is_editor":true,"listening":true,"tools":154,"port":9877,"server":"godot-mcp-rs","frame_count":301350}` | 本轮前后各测一次，均 ok |
| 编辑器命令行 | `godot.windows.editor.x86_64.mono.exe -e --path .workspace/mario --mcp-port=9877`（`Win32_Process.CommandLine`） | 确认编辑器打开的就是 `.workspace/mario` |
| `--version` | `godot.windows.editor.x86_64.mono.console.exe --version` → `4.8.dev.mono.custom_build.035edfce7` | 与 `version_string` 一致 |

### 4.1 `hoh` 二进制新鲜度（硬要求，先证明后运行）

```
$ git log -1 --format=%ci 9ff9cd2
2026-09-29 12:42:09 +0800
$ cargo build --release --offline            # 串行，无并发构建
    Compiling hof-rs v0.1.0 (F:\moonbit-hof-rs)
    Finished `release` profile [optimized] target(s) in 20.16s
BUILD_EXIT=0
$ ls -l --time-style=full-iso target/release/hoh.exe
-rwxr-xr-x 2 wyl 197609 12303360 2026-09-29 13:22:54.874837800 +0800 target/release/hoh.exe
$ sha256sum target/release/hoh.exe
dde1421886545529f44e693119c88626d8335c59181581494a71e34765b49c8f
$ python -c "…比较 mtime 与提交 %ct…"
binary_mtime 1790659374.8748379 ; commit_ctime 1790656929 ; binary_newer True
```

- 构建前：`target/release/hoh.exe` mtime **2026-09-29 00:40:12**（早于 §15 全部提交）⇒ 确实陈旧，必须先建。
- 构建后：mtime **13:22:54** > `9ff9cd2` 的 **12:42:09** ⇒ **新鲜性成立**，run 用的是含 DR-54/55/56 的二进制。

### 4.2 连通性前置

```
$ ./target/release/hoh.exe doctor
[ok] model.chat: http://100.105.152.101:18080/v1/chat/completions answered with model `deepseek-v4.1-flash`
[ok] godot.engine_version: 4.8.dev.mono.custom_build.035edfce7
[ok] tools.mcp: 154 tools available at http://127.0.0.1:9877/mcp
[ok] spec: … sha256 4c81c3a9995f0b3afdf01421a0c3be88573cceefc284ce9bafbfda141f0f5c3a
DOCTOR_EXIT=0
```

密钥只报**长度 51**，全程未打印明文。

---

## 5. E2 豁免的**非空洞性**反例

**我要证明的命题**：`launchable=true` 不是"把含 `error` 的行一律忽略"的一刀切。

**(a) 代码级（只读）**：`src/adapter/godot.rs:3575-3593` 的豁免是**常量表 + 精确匹配**：

```rust
pub const ENGINE_INFO_BANNERS: &[&str] = &[
    "[MCP] trace=off (default; use --mcp-trace=<path> or godot_mcp/trace_file to enable)",
    "[MCP] capture=off (default; use --mcp-capture=on_error|every_call together with --mcp-trace=<path>)",
];
pub fn is_engine_info_banner(line: &str) -> bool { let line = line.trim(); ENGINE_INFO_BANNERS.contains(&line) }
```

两条常量与引擎当前 checkout 的 `mcp_server.cpp` 字面量逐字一致；`[MCP]` **前缀**式白名单被显式禁止。

**(b) 执行级（我自己跑的，真实输出）**：

```
$ cargo test --offline --test launchable_gate
running 12 tests
test an_engine_info_banner_does_not_close_the_gate ... ok
test a_real_editor_error_still_closes_the_gate ... ok                     <- 反例①：真 ERROR:
test an_error_carrying_the_mcp_prefix_still_closes_the_gate ... ok        <- 反例②：ERROR: [MCP] SceneTree never became available; MCP server disabled.
test an_unknown_mcp_prefixed_line_still_closes_the_gate ... ok            <- 反例③：其它 [MCP] 前缀行
test result: ok. 12 passed; 0 failed; 0 ignored; 0 measured; 0 filtered out; finished in 24.39s
GATE_TEST_EXIT=0
```

- 这三条反例用的错误文本取自引擎**自己的**字面量/日志（`tests/launchable_gate.rs:52-58`），
  走的是**生产**谓词与闸门判定路径（`FakeChannel` 只提供编辑器日志应答，不改判定代码）。
- **边界（诚实）**：我**没有**在活体项目里植入一个真错误来测闸门 —— 那会改动 `.workspace/mario`，
  从而污染本轮 `A_1` 与 E5 的三树比对。所以这一条是"生产谓词 + 引擎真实错误串"的执行级反例，
  **不是**活体注入实验。
- 活体侧的配套事实（不是反例，是同一豁免在真机上的正向证据）：本轮 `editor_get_errors` 仍返回 `count=1`，
  闸门却判 `ok=true`；而同一轮里失败的 `node_and_collision_assertions` 等步骤**并未**因此变绿 ⇒ 豁免的作用域是窄的。

---

## 6. 与 `smoke-t6` 的逐项对照

| 维度 | `smoke-t6`（基线，未改动：135 文件、最新 mtime `2026-09-29 02:32:01`） | `smoke-t7`（本轮） | 变了？为什么 |
|---|---|---|---|
| 引擎 | `4.8.dev.mono.custom_build.ba1587c71`，sha256 `25d29eb4…`，size 194,207,744 | **`4.8.dev.mono.custom_build.035edfce7`**，sha256 `08483088…`，size 194,216,960 | 变了：换到含 TASK-151 修复的构建 |
| 退出码 | **6**（工件不可启动） | **0** | 变了：闸门不再假阴性 |
| `artifact_gate.launchable` | `false`，reason=引擎信息横幅 | **`true`，reasons=[]** | 变了：DR-48 生效 |
| `editor_errors_baseline` | `ok=false`（"the editor is not clean"） | **`ok=true`**（"1 line(s) exempted by DR-48"） | 变了：DR-48 |
| `play_scene_ready` | ok=true（游戏真起来了） | ok=true（50 节点） | 没变 |
| `input_channel_probe` | `ok=false`；端点**挂死并消失**（`10060`×3 → `10061`），`has_action=None` 全空 | `ok=false`；**0 次传输失败**；语义工具真被调用，判 `ACTION_BINDING_UNKNOWN`，原因是 **`scene_path` 入参被拒** + `name` 键不存在 | **表象同（都 false），根因完全不同**：引擎挂死 → 消失，改为 **hof-rs 入参/键名假设错** |
| `input_replay` | `ok=false`（端点死） | **`ok=true`**（4 个 quadruple 来自 game 通道语义采样；但注入是 `EDITOR_SIDE_INJECTION`） | 变了：**但这条 ok=true 的可归因性弱**（见 §2.4；QA 未升级为 verified） |
| `node_and_collision_assertions` | `ok=false`（`Player=FAILED, Goal=FAILED, HUD=FAILED`，端点死） | `ok=false`（`Player=missing, Goal=missing, HUD=missing`，**回包其实成功**） | **表象同，根因不同**：调不通 → **调通了但被误读** |
| `editor_stop_scene` | ok=true（还回了 `game_endpoint_invalidated`） | ok=true（`Playback stopped`） | 没变 |
| `meta.engine.mcp.game_endpoint` | **`null`**（DEF-D） | `{"endpoint":"http://127.0.0.1:55225/mcp","pid":113088,…}` | 变了：DR-51 生效 |
| `meta.engine.mcp.editor_status` | **`null`**（DEF-D） | 真实 `GET /mcp` 应答体（DR-51） | 变了：DR-51 生效 |
| 截图证据 | 4246 B 的 **2026-09-21 旧 PNG**（假证据 DEF-B） | **5860 B 本轮新鲜**，`mtime 14:32:24`，旧文件改名 `.stale-…` | 变了：DR-49 生效 |
| MCP 传输错误 | 36 条（全指向已死的 `63698`），首个 `10060` → 首个 `10061` 约 **730 s** | **0 条** | 变了：TASK-151 + DR-54（不再发编译不过的 body） |
| `-32602` 重试次数 | **3** | **1**（`mcp-errors.jsonl` 的 `attempt=1`） | 变了：DR-56 生效 |
| attempts | **4**（planner/developer/developer_repair/tester），全 `LimitsExceeded` | **3**（planner/developer/tester），全 `LimitsExceeded` | 变了：闸门首轮即过，**60 步定向修复未被消耗** |
| `repair_retry_used` | `true` | `false` | 变了：同因 |
| 工程增量 | `A_1 == A_0 == fc78d299…`（零增量） | `A_1 == A_0 == fc78d299…`（零增量） | **没变**：`no_progress` 警告两轮都出现 |
| tokens | 26,805,473 | **22,424,721**（−4.38M） | 变了：主要来自省掉的修复 attempt |
| 墙钟 | ≈112 分钟（含挂死等待） | **74 分 58 秒** | 变了：挂死与重试放大消失 |
| `E_1` | 8 verified + 22 gap | 8 verified + **20** gap（`G20` 是 QA 自己发现的运行时观测缺陷） | 结构同，内容不同 |
| E1/E2/E3/E4/E5/E6 | not_met / not_met / not_met / met / met / met | **not_met / met / not_met / met / met / met** | **E2 转 met**；**E3 仍 not_met 但根因换了**；E1 未变 |

**回答任务书的核心问题**：
- **E2**：**是**，`not_met → met`（闸门假阴性已消除，真机验证）。
- **E3**：**否**，仍为 `not_met`。原因不是引擎端点冻结（那已被 TASK-151 修好，本轮 0 次传输失败），
  而是 §15 改造后的关键路径在**真机形态上有两处形状假设错误**（`scene_path` 恒被拒；`get_node_properties` 无顶层 `name`），
  使探针只能保守落到 `ACTION_BINDING_UNKNOWN`，且 `node_and_collision_assertions` 把成功的回包误读为 `missing`。

---

## 7. 仍未验证 / 不可判定项（严格区分"实测"与"推断"）

**实测（本轮真有证据）**

1. 引擎 `035edfce7` 上，`execute_gdscript` 的编译不过 `code` **0.01 s 得 `-32602`**，其后端点三次仍应答（§2.3a）。
2. 全轮 **0 次传输失败**；游戏端点从未挂死；`-32602` 恰尝试 **1** 次（§2.3b）。
3. 闸门 `launchable=true` / 退出码 0；`editor_errors_baseline` 由 DR-48 豁免后转绿（§1.2）。
4. `create_input_recording` / `play_input_recording`（`InputEventAction` 形状，`injected=1`）/ `get_node_properties` /
   `get_node_property_samples` / `stop_input_recording` 在游戏端点**真机可用**（§2.2）。
5. `run_test_scenario` 对**任何** `scene_path` 值都回 `-32602`（C2/C3 两值实测），去掉该参数即成功（C1/C4/C5）。
6. `get_node_properties` 的顶层键是 `{node_path, properties, type}`，**无 `name`**（A7 实测）。
7. 三树字节级同一（E5）；截图本轮新鲜（E4/E6）。
8. `runs/smoke-t6` 未被覆盖（135 文件、最新 mtime `2026-09-29 02:32:01`，与本轮批次前记录一致）。

**推断（不得当作已证）**

1. **DR-55 端点判死在真机上的行为未验证**：本轮没有传输失败，判死路径**没被走到**。
   离线 7 条测试仍是我方对其语义的唯一证据。
2. **`ACTION_NOT_BOUND` 的真机文面**仍未见到：本轮 `-32602` 说的是 `scene_path`；
   引擎对"InputMap 没有该动作"的原文措辞仍未知（TASK-DR54-REPORT §8.2 的推断项仍然成立）。
3. **`input_axis` 作为采样属性**：`get_node_property_samples` 接受它但每帧回 `null`；
   `run_test_scenario` 的 assert 则直说 "does not have the property 'input_axis'"。
   ⇒ 引擎是否**有**该属性，取决于节点实现（推断：没有），本轮只能证"读不到"。
4. **`input_replay ok=true` 的归因**：4 个 quadruple 都显示 `x` 单调递增（含 `move_left` 段），
   `velocity.x` 恒 `+3.667`；我**推断**这是早先注入的 `move_right` 未被释放造成的残留漂移，
   但本轮**没有**做"释放后归零/反向"的实验，故这只是推断。
5. **`node_and_collision_assertions` 的 `missing` 判定**：我实测到"回包成功但被判 missing"，
   并从代码（`godot.rs:2051` 取顶层 `name`）解释其机制；但"引擎**永不**返回顶层 `name`"这一点，
   我只在 Player/Goal/HUD 三个节点上实测（以及 HUD 的 `properties.name` 存在）——不等于对 177 条契约全量成立。

**未关闭（应回上游/回设计，不在本报告内修）**

1. `src/adapter/godot.rs:1597-1604`（DR-54 / `6329e5c`）硬传 `"scene_path":"current"` ⇒ `run_test_scenario` 必失败。
2. `src/adapter/godot.rs:1253-1257`（DR-54 / `6329e5c`）用顶层 `name` 判"游戏进程可达" ⇒ 恒 false。
3. `src/adapter/godot.rs:2051-2055`（`00601476`，2026-09-21，**既有代码**）同一键名误解 ⇒ 三个必需节点恒判 `missing`。
4. `input_replay` 在"注入是编辑器侧"时仍可 `ok=true`（`godot.rs:1936-1961`）：电池语义与"动作被送达并产生效应"之间存在缺口。
5. 跨轮**陈旧证据**污染：本轮开工时 `.workspace/mario/.hoh/deterministic/**` 仍是 `smoke-t6` 的产物
   （我开工前留档 `runs/smoke-t7-experiment/smoke-t6-workspace-baseline/`，其 `battery.json` mtime `2026-09-29 02:14:48`）；
   开发者轨迹里确实读到了它们（`developer.attempt1.json` `.messages[54]` 逐字含 `pid: 108432`、"the editor is not clean"、
   `os error 10061` 等**上一轮**文本）。⇒ 开发者可能被上一轮的失败证据误导。**本轮未清理该目录。**
6. D239 的"判死前重试乘法"（`mcp.rs` 传输层 × 上层重试）仍未关闭；本轮**没有**触发它，故无新证据。
7. `DR-50B` 的最小复现 spike 形态：我在 §2.3a 用的是**等价形态**（编译不过的 body）；
   与 D222 字面（`str(Input.action_press("move_right"))`）不同，我称之为**等价而非逐字**复现。

---

## 8. 诚实披露

1. **我遵守了"不改 `src/**`/`tests/**`"**：本批只跑与取证。§7"未关闭"里的 3 处代码缺陷，
   我**没有**修（也不该修）——按任务书"若你发现必须改代码，停下上报"，这里即上报。
   工作树 `git status --porcelain --untracked-files=no` 为空；`godot-mcp/**` 相对 `9ff9cd2` **零 diff**；
   `PRD-mario.md` sha256 仍 `4c81c3a9…5c3a`；`Cargo.toml`/`Cargo.lock` 未动；未 push。
2. **我先做了"E3 预检"再跑正式轮**：因为上一轮的端点冻结意味着 2 小时可能白烧。
   预检起过一次游戏（`pid 119692`）并在实验后 `editor_stop_scene` 收尾，已核实进程消失、端口无 LISTENING（§2.3c）。
   `stop_scene` 返回 `{"message":"Playback stopped","stopped":true}`。
3. **我搞错过一次并改正（E5）**：第一次三树比对我把 `.hoh/**` 也算进了"工程树"，
   于是报出"220 处内容差异 / THREE TREES BYTE-IDENTICAL: False"。核对后确认 hof-rs 的 `hash_tree`/版本快照
   只覆盖**工程文件**（存储版本 17 个文件，不含 `.hoh`），我把 `.hoh` 加入排除集后重跑，得"17 文件、同摘要、0 差异"。
   **两个结果都保留**（脚本与 JSON 在 `runs/smoke-t7-experiment/`），因为"第一次为何错"本身是可复核的。
4. **"我预测到了两处 DR-54 形状错误"这件事我要说清来源**：我在正式轮之前用 E3 预检**独立实测**到了
   `run_test_scenario` 拒绝 `scene_path`、以及 `get_node_properties` 无顶层 `name`；
   正式轮的原始证据（`raw/input_channel_probe.json` 的 `reachable=false` + `-32602` 原文）**与预检一致**。
   这不构成"预检替代实测"——报告的 E3 结论全部引用**本轮 run 自己的**证据。
5. **`input_replay ok=true` 我一开始当作 E3 的好消息，随后收回**：读它的 `observation` 后确认
   注入是 `EDITOR_SIDE_INJECTION`，且 `move_left` 段 `x` 反而递增，无法归因。所以我没有把它写成 E3 达标，
   只写成"电池层转绿但可归因性弱"，并把这条列为候选缺陷（§7.4）。
6. **未做/做不到的事**：
   - 没有跑活体 E2 反例注入（会污染 `A_1`，理由见 §5）；
   - 没有验证 DR-55 判死（本轮没有传输失败可触发）；
   - 没有逐字复现 DR-50B 的最小 spike 字面（用了等价形态，§7.7）；
   - 我没有清理 `.workspace/mario/.hoh/deterministic/**` 的跨轮陈旧证据（发现于事后；清理它会破坏"本轮未改 workspace 之外的东西"的可核性，故如实记录而不动手）。
7. **未把推断写成实测**：§7 已逐条分栏；本报告所有数字与引文均可用文中命令在当前工作树重跑得到。
8. **收尾状态**：编辑器 `pid 75204` **仍在** 9877 上监听（我未杀、未重启）；本轮游戏进程与我实验的游戏进程均已消失；
   无遗留监听（`55225`、`57939` 均无 LISTENING）；`runs/smoke-t6` 未被写。

---

## 9. 工件索引

| 类别 | 路径 |
|---|---|
| 本轮基线 | `runs/smoke-t7/**`（115 文件；`exit_code`、`meta.json`、`iter-1/{result.json,evidence.json,qa_report.md,plan.md,usage.json,candidate/,traj/,logs/}`、`versions/`） |
| 控制台原始输出 | `runs/smoke-t7-console.txt` |
| E3 预检（我起的游戏，已释放） | `runs/smoke-t7-experiment/{play_scene_via_hoh.txt,stop_scene_via_hoh.txt,e3_survival_console.txt,raw/,e3_semantic_console.txt,semantic/,e3_scenario_console.txt,scenario/}` |
| E5 独立重算 | `runs/smoke-t7-experiment/e5_hash_tree.json` |
| 开工前 workspace 快照 / smoke-t6 `.hoh` 留档 | `runs/smoke-t7-experiment/pre_run_workspace_{inventory,sha256}.txt`、`runs/smoke-t7-experiment/smoke-t6-workspace-baseline/` |
| 上一轮基线（**未改动**） | `runs/smoke-t6/**`（135 文件，最新 mtime `2026-09-29 02:32:01`） |
| 规范/需求 | `.spec/hof-rs/{REQUIREMENTS.md v0.3,DESIGN-DETAIL.md §15 v0.10,ACCEPTANCE.md v2}`、`DECISIONS.md` D216..D239 |
| 设计-15 实现报告 | `.spec/hof-rs/tasks/TASK-DR54-REPORT.md` |
