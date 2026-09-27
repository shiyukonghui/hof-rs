# ACCEPTANCE-TASK-121 — 独立验收（第二轮）：`godot-mcp` 工具覆盖里程碑（契约 177 条，修正后口径）

> 验收员身份：**独立验收子代理**，未参与实现，**未采信任何既有结论**（包括 `ACCEPTANCE-TASK-119.md`、
> `TASK-120-REPORT.md` 与 TASK-120 的台账文字）。本文的每一个数字都来自本机本轮真实命令的逐字输出；
> 凡我无法亲跑的，一律标 `unverifiable`。
>
> 被验收对象**未被修改**：`recovery/reports/ACCEPTANCE-TASK-121.md` 是本轮唯一写入仓库的文件。
> 全部复核脚本、重算产物与反例副本都写在仓库**之外**的 `%TEMP%\acc121\`（系统临时目录），跑完已删除（§7）。
> 验收前后对象文件的 sha256 **逐字节相同**（§0.2）。
>
> 与任务书的一处出入（如实记）：任务书点名的入口 `recovery/reports/TASK-119-REPORT.md` **不存在**；
> TASK-119 的验收工件实际是 `recovery/reports/ACCEPTANCE-TASK-119.md`（我读的是后者）。

---

## 0. 结论

**verdict = pass**（六项核验全部成立；未发现通过性缺陷，发现 5 条低severity 的残留问题，见 §3/§4）

### 0.1 六项核验一览

| # | 核验项 | 结果 | 关键独立证据 |
|---|---|---|---|
| ① | TASK-119 四处 fail 是否真修好（A1 读动词 / A2 晚于写 / A3 expect 带值 / A4 禁裸 `expect_absent`） | **pass** | 代码四处校验逐条定位（`tool_coverage.py:568-628`）；51/51 备案见证在我自写的同规则下全部通过、0 条被拒；把 A3 声明回退成裸键名即被拒；A1/A2/A4 反例各自被对应规则拒 |
| ② | 重判是否诚实（51 条声明、14 条补齐） | **pass** | 51 条**全量**独立复核（非抽样）：见证读调用晚于写 51/51、回包含被写值 51/51；`git diff 36b7be4..188c090` 独立数出**恰好 14 条**声明被改、全部由裸键名改为带值；抽查 5 条回原始 trace 逐字命中 |
| ③ | 17 条补边界是否真拒绝 | **pass** | 17/17 `-32602 "Unknown parameter 'undeclared_probe'"`，`suggestion` 为「Accepted parameters of …」，来自 `tool_registry.cpp::_reject_unknown_arguments`（`call_tool` 在 handler **之前**调用）；响应对应真实引擎进程（Godot 4.8.dev.mono，#9905/#9906，engine stdout + 逐调用 response JSON）；`--exclude c8-task120` 精确退回 **152/20** 且其余 155 条行**零变化** |
| ④ | 通道↔verb 一致性校验是否真会硬失败 | **pass** | 副本上四类违规（读动词→`file_effect`、读动词→`editor_state`、动作动词→`payload`、缺一条工具、未知通道名）全部 `SystemExit`，退出码语义为「拒绝运行」 |
| ⑤ | 反例自证是否属实（M2/M3 两类） | **pass** | M2（改见证回包里的字面量：值 346.0→0.0、键 x→posn）新规则**拒签**；M3（把写后读数强改回起始值 100.0）**旧规则照签 seq=2**、**新规则拒签**；原件 trace 跑前跑后 sha256 不变 |
| ⑥ | 可重算性与数字一致性 | **pass** | 重跑 `tools/tool_coverage.py` → 112 run / 182 trace / 8729 calls / distinct 172，169/3/5；177 条逐工具 `(calls, ok, boundary)` 与 `coverage.json` **0 不符**，其余 12 个字段也 **0 不符**；不经该脚本的独立解析器复算同为 8729/8057/672 |

### 0.2 声称现状的独立核对

| 声称 | 我实测 | 判定 |
|---|---|---|
| 契约 177 条 | `contract_tools` 实数 177 | ✅ |
| 出现过 172 | `corpus.distinct_tools = 172`；`buckets[">=5"] = 172` | ✅ |
| 达标 169 | `status_counts = {达标:169, 计数达标缺证据:3, 未达(0):5}` | ✅ |
| 计数达标缺证据 3 | `editor_set_auto_dismiss_dialogs` / `project_get_android_preset_info` / `os_deploy_to_android_device`（逐条原因与登记表一致） | ✅ |
| 未达 5 | `editor_simulate_*` 五条，语料内 0 次调用 | ✅ |
| scope-excluded 5 | 与上述 5 条同一集合；登记表 H7 明写「scope decision (D59 / GDR-21), not a missing subsystem」 | ✅ |
| **needs-an-external-device 2** | 登记表 `needs_an_external_device.count = 3`、`tools` 3 条；其中**未达标的是 2 条**（`project_get_android_preset_info`、`os_deploy_to_android_device`），`os_list_android_devices` 已达标 | ⚠️ 「2」只在「未达标条数」口径下成立；见缺陷 D1 |
| engine_not_implemented 1 | `count = 1`，且 `coverage.json` 里 `ledger_class` 恰 1 条 | ✅ |
| 引擎侧零改动（未动门槛） | `git diff --name-only 36b7be4 2a8ecf9 -- godot-mcp/godot/modules/mcp_server` **为空** | ✅ |

### 0.3 对象未被修改的证据

```
$ sha256sum TOOL-COVERAGE.md coverage.json tools/tool_coverage.py tools/tool_channels.json tools/tool_coverage_unreachable.json
（验收开始时 / 全部复核跑完后，两次输出逐字节相同）
5feef4fba42f5f7f2dcfda9c4ecea27226f729c0694c6a8c46ff2760955ca610 *TOOL-COVERAGE.md
48017cd5fc2339aa4ef14d3b20955b93238cf9eea7dd78eb18acf7d44e47f7fa *coverage.json
1691dd516bd6b549ab6e09a644aac4e7878821686734cebc7c6b665170f2ad5d *tools/tool_coverage.py
72a6616d98afb614a88726c8b631947521995e05e42e49048242a664a72aaf0b *tools/tool_channels.json
0856af7c58fa249f0ef06435db70fb2288486af67fed17f79979cce13834b98f *tools/tool_coverage_unreachable.json
```

反例用的通道表副本写在 `%TEMP%\acc121\roots\*`，语料副本只存在于**内存**（`copy.deepcopy`），
原始 trace `DF4783B5E2B82FC7D86B32E2F8EB4F7D8015C95CD3020336A4D219DC1EE59351` 跑前跑后一致。

---

## 1. ① TASK-119 的四处 fail：是否真修好

### 1.1 四条校验在代码里的落点（读代码，`tools/tool_coverage.py`）

| 规则 | 代码位置 | 判据 |
|---|---|---|
| **A1** 见证必须是读动词 | `verify_readback()` `:568-577` | `verb_of(witness, verbs)` 必须 ∈ `READ_VERBS`（`:113-115`，14 个动词）；且 `witness != tool` |
| **A2** 见证必须晚于写 | `:609-628` | `run_index[run][tool]["seqs"]` 里存在 `s < witness_seq`；否则给出带 `seq` 列表的 A2 拒绝理由 |
| **A3** `expect` 至少一条带值 | `:530-543`、`:601-607` | `READBACK_KEY_ONLY = ^"[A-Za-z_][A-Za-z0-9_]*"$`；全是裸键名 → 拒签 |
| **A4** 禁止裸 `expect_absent` | `:587-592` | `forbids and not expects` → 拒签，理由写明 `expect_matches([], text)` 恒真 |

四条按 A1→(无 expect)→A3→A2 的顺序检查，任一条触发都只返回 `(None, reason)`，
调用侧 `build_payload` 把该声明放进 `readback_declarations.rejected`，**不授予档位、不计通道证据**（`:861-871`）。

### 1.2 在语料里验证它生效

我**自己重写**了一遍 A1–A4（自写 trace 解析器、自写 sidecar 重哈希、自写 `expect` 匹配），
对 51 条 manifest 声明逐条判定：

```
$ PYTHONDONTWRITEBYTECODE=1 PYTHONIOENCODING=utf-8 python /tmp/acc121/verify_witness.py
manifest readback declarations found by me: 51
MY verified witnesses: 51  MY refused: 0
coverage.json accepted tools: 51  mine: 51
accepted by coverage.json but REFUSED by my rules: []
same tool, different accepted witness seq: []
=== per-verified-witness audit ===
（51 行逐条）… flagged accepted witnesses: 0
  其中 9 条我最初标 FLAG:LITERAL_NOT_IN_PAYLOAD —— 经 probe9.py 逐条查明是
  我的「只搜原文」比读者更严：原始行存的是 JSON-RPC 信封，`\"` 反转义后字面量逐字在场
  （例：editor_add_state_machine_state 在 unescaped / content[0].text 两个拼写里都命中
   `"name":"Walk"` 与 `"animation":"Anim2"`），**不是台账放宽**。
```

实证「规则不是死代码」：把 `running_game_stop_input_recording` 的声明**回退**成 TASK-119 那版
`expect: ["\"position\""]`，当前读者**当场拒签**：

```
NEW rule + old declaration : REFUSED: TASK-120 A3: every declared `expect` literal is a bare JSON key name
                             ('"position"'). … at least one literal has to carry the written VALUE
```

`expect_absent` 普查（自写扫描 51 条声明）：**4 条**携带 `expect_absent`
（`editor_remove_{state_machine_state,state_machine_transition,animation,output_log}`），
其中**裸 `expect_absent`（A4 违规）0 条**；「既无 `expect` 也无 `expect_absent`」0 条；
「全部 `expect` 都是裸键名」0 条。

### 1.3 判定

四处 fail（TASK-119 的 D1/D2/D3/R3）**均已修好且规则是活的**：
D1 由通道表修正 + 装载期交叉校验解决（见 §2 ④）；D2 由 A1 解决；D3 由 A2+A3 解决；R3 由 A4 解决。

---

## 2. ② 重判是否诚实（51 条声明 / 14 条补齐）

### 2.1 全量独立复核（不是抽样，但按要求点名了 5 条）

我自写规则对 51 条的判定与 `coverage.json` **完全一致**（集合、见证工具、见证 seq 全部相同，§1.2 输出）。
逐条审计结果：**见证读调用晚于写 51/51、回包含被写值 51/51、见证 verb 全为读动词 51/51、
至少一条带值字面量 51/51**。

另做了一次「A2 精确性」加固检查（读者把同一 run 下多个 trace 文件的 `seq` 合并比较），
对 51 条逐条回到**见证调用所在的同一个文件**寻找严格更早的写调用：

```
$ python /tmp/acc121/a2exact.py
declarations checked: 51
A2 exactness problems: 0
runs with 2 trace files were re-checked per file; all others trivially single-file
```

### 2.2 「14 条补齐」——用 git 独立数，不采信报告

```
$ git diff --stat 36b7be4 188c090 -- godot-mcp/tools/sessions/_exercises/
 ex_anim/h2-manifest.json | 14 ++++----   ex_audio/h5-manifest.json |  5 +--
 ex_nav/h4-manifest.json  | 15 ++++----   ex_particles/h6-manifest.json | 6 ++--
 ex_rec/h9-manifest.json  | 14 ++++----   ex_write/c4-manifest.json | 15 ++++----
（另有 ex_bound/c8-* 为新增批次）
$ python /tmp/acc121/gitdelta.py
declarations that differ (tool, file, before, after): 14
changed count: 14
REMOVED: 无     ADDED: 无
```

14 条被改声明的「旧 → 新」（逐字来自 git）：

| tool | 旧 `expect` | 新 `expect` |
|---|---|---|
| `editor_add_state_machine_state` | `["\"Walk\""]` | `["\"name\":\"Walk\"", "\"animation\":\"Anim2\""]` |
| `editor_add_state_machine_transition` | `["\"Idle\""]` | `["\"from\":\"Jump\"", "\"to\":\"Walk\""]` |
| `editor_create_animation` | `["\"Anim5\""]` | `["\"animations\":[\"Anim1\",\"Anim2\",\"Anim3\",\"Anim4\",\"Anim5\""]` |
| `editor_add_audio_bus` | `["\"Music\""]` | `["\"name\":\"Music\"", "\"index\":2"]` |
| `editor_setup_navigation_agent` | `["\"max_speed\""]` | `["\"path\":\"Player/NA3\"", "\"max_speed\":320.0"]` |
| `editor_setup_navigation_region` | `["\"RegionA\""]` | `["\"path\":\"RegionA\"", "\"type\":\"NavigationRegion2D\""]` |
| `running_game_move_player_to_target` | `["\"position\""]` | `["\"x\":220.86", "\"y\":394.86"]` |
| `editor_set_particle_material` | `["\"damping_min\""]` | `["\"node_path\":\"P1\"", "\"initial_velocity_min\":40.0", "\"initial_velocity_max\":90.0"]` |
| `running_game_create_input_recording` | `["\"event_count\":2"]` | `["\"x\":346.0"]` |
| `running_game_play_input_recording` | `["\"position\""]` | `["\"x\":151.0"]` |
| `running_game_stop_input_recording` | `["\"position\""]` | `["\"x\":346.0"]` |
| `editor_add_scene_instance` | `["\"Sub1\""]` | `["/Main/Sub1/C4Node2", "\"name\":\"Sub1\""]` |
| `editor_set_node_groups` | `["\"ex_host\""]` | `["\"node_path\":\"Host\"", "\"groups\":[\"ex_host\"]"]` |
| `editor_setup_physics_body` | `["\"PB1\""]` | `["/Main/PB1/CollisionShape2D", "\"name\":\"PB1\""]` |

TASK-119 点名的 7 条**全部**在这 14 条之内；另外 7 条是 TASK-119 没抓到的同类裸名/裸键
（`"Walk"` / `"Idle"` / `"Music"` / `"RegionA"` / `"Sub1"` / `"ex_host"` / `"PB1"` / `"Anim5"`），
说明补强**比验收发现的更彻底**，不是正好补 7 条了事。删／增声明均为 0，即「0 条降级」不是靠删声明做出来的。

### 2.3 抽查 5 条：见证真的在写之后、回包真的含被写的值

原始 trace 逐字（`/tmp/acc121/check12.py`，写调用 vs 见证调用）：

```
editor_add_audio_bus          <- editor_get_audio_bus_layout  run=ex_audio/h5-task113
  写: seq=2 {"name":"Music"} …（后续 Sfx/Ambient/Voice/Ui，seq=7/8 为拒绝）
  见证: seq=22 ok=True 命中 | …"index":2,…"name":"Music"…
editor_set_node_groups        <- editor_get_node_groups        run=ex_write5/c4-v5-task111
  写: seq=80 {"groups":["ex_host"],"node_path":"Host"}
  见证: seq=143 ok=True | {"count":1,"groups":["ex_host"],"node_path":"Host"}
editor_set_particle_material  <- editor_get_particle_info      run=ex_particles/h6-task113
  写: seq=17 {"material_params":{"initial_velocity_max":90.0,"initial_velocity_min":40.0},"node_path":"P1"}
  见证: seq=34 ok=True | …"node_path":"P1"…（含 40.0 / 90.0）
editor_add_scene_instance     <- editor_get_scene_tree         run=ex_write5/c4-v5-task111
  写: seq=21 {"name":"Sub1","parent_path":".","scene_path":"res://scenes/c4_sub.tscn"}
  见证: seq=132 ok=True | …/Main/Sub1/C4Node2…"name":"Sub1"…
running_game_stop_input_recording <- running_game_get_node_properties  run=ex_rec/h9-task113
  写: seq=5/8/11/14/17/25/27（stop）；见证: seq=18 ok=True | "position":{"x":346.0,"y":300.0}
  （同工具 seq=2 的读是 100.0 起始值，**已被 A2/A3 排除**，不再被采用）
```

### 2.4 判定

重判**诚实**：14 这个数字能被 git 独立数出；51 条声明的「见证晚于写 + 回包含值」被逐条独立复核；
被 TASK-119 判为伪见证的 3 条 input recording 确实改用了写后真读（seq=18/22 的 346.0 / 151.0）。

---

## 3. ③ 17 条补边界是否是真拒绝

### 3.1 17/17 都是「未声明参数门」的拒绝

```
$ python /tmp/acc121/check3.py
c8 tools/call rows: 17     c8 ok=true calls: 0
error_code counter: Counter({-32602: 17})
all codes == -32602: True
all args carry undeclared_probe only: True
（逐条）
trace-editor.jsonl seq=1  editor_open_scene  -32602
   msg : Unknown parameter 'undeclared_probe' for tool 'editor_open_scene'
   data: {"suggestion":"Accepted parameters of editor_open_scene: path"}
…
trace-game.jsonl   seq=4  running_game_stop_input_recording -32602
   data: {"suggestion":"running_game_stop_input_recording accepts no parameters"}
```

**来源是门、不是 handler**：`godot/modules/mcp_server/tool_registry.cpp`
`_reject_unknown_arguments()`（`:809-855`）生成的消息与 `suggestion` 与 trace **逐字相同**；
`MCPToolRegistry::call_tool()`（`:857-...`）在取到 `MCPToolDef` 之后第一件事就是
`if (!_reject_unknown_arguments(*def, p_args, r_error)) return Variant();`，
注释明写「The check runs *before* the handler」。

**是引擎真实回答，不是手写 trace**：同目录存在逐调用的 `c8-00N-*.request.json` / `c8-00N-*.json`
（`{"error":{"code":-32602,…, "id":101,"jsonrpc":"2.0"}`），`engine-editor.stdout.txt` 为真实
`Godot Engine v4.8.dev.mono.custom_build.3fdabe2d9`、`[MCP] listening on 127.0.0.1:9905 (editor=true, tools=154)`，
两份 trace 各有 1 条 `trace_opened`（含 pid 106096 / 62536、端口 9905/9906）。

### 3.2 可逆性：排除该批后精确退回 152/20

```
$ PYTHONDONTWRITEBYTECODE=1 python tools/tool_coverage.py --exclude c8-task120 \
      --md /tmp/acc121/m4.md --json /tmp/acc121/m4.json
tool_coverage: mode=all-runs runs=111 trace_files=180 calls=8712 distinct=172
  buckets: 0=5 1-4=0 >=5=172 | status: 达标=152 缺证据=20 未达1-4=0 未达0=5
```

`coverage.json`（含 c8）与 `m4.json`（排除 c8）逐条对拍：

```
$ python /tmp/acc121/check3b.py
all 17 tools: boundary 1 -> 0 ; status 达标 -> 计数达标缺证据 ; calls 各 +1
tools outside c8 whose row changed (should be 0): 0 []
```

17 条清单（manifest 中 17 条唯一工具，与台账 17 条一致）：`editor_open_scene`、`editor_save_scene`、
`editor_delete_node`、`editor_set_node_property`、`editor_get_errors`、`editor_capture_screenshot`、
`project_edit_script`、`editor_add_input_action`、`project_build_csharp`、`project_validate_scripts`、
`running_game_capture_screenshot`、`running_game_get_scene_tree`、`running_game_get_node_property_samples`、
`running_game_stop_input_recording`、`running_game_run_test_scenario`、`running_game_assert_screen_text`、
`running_game_run_stress_test`。

### 3.3 判定

**17 条是真拒绝、可逆性说法成立、门槛未动**（引擎目录 0 字节改动；`boundary >= 1` 的判据未改）。
但必须写清它的**强度上限**（§4 R1）：这 17 条各自的边界证据是同一种注册器门探测，
满足的是「`ok=false` 至少一次」这个计数门，不是各工具自身的错误语义。

---

## 4. ④ 通道↔verb 一致性校验是否真会硬失败

在 `%TEMP%\acc121\roots\<case>\tools\tool_channels.json` 的**副本**上构造违规，调用被测模块的
`load_channels(root, names, verbs)`：

```
$ python /tmp/acc121/check45.py
[baseline]                  LOADED OK (no hard failure)  entries=177
picked read tool project_get_info verb=get ; action tool editor_open_scene verb=open
[read_as_file_effect]  SystemExit: channel table contradicts the tool verb (TASK-120 item B):
     - project_get_info (verb `get` is a read verb: its answer IS the measurement) declares `file_effect`
[read_as_editor_state] SystemExit: … declares `editor_state`
[action_as_payload]    SystemExit: … editor_open_scene (verb `open` is an action verb) declares `payload`:
     `read_payload` only ever counts read-verb tools, so this tool's evidence gate could never be satisfied
[missing_one]          SystemExit: channel table does not cover the contract: missing=['editor_open_scene'] extra=[]
[unknown_channel]      SystemExit: channel table declares an unknown channel for: ['editor_open_scene']
```

四类违规都**加载期硬失败**（`raise SystemExit`，`tool_coverage.py:337-352`），不是警告。
另外我用**自己的**谓词对现行表做了一次全量扫描（不经过被测代码）：

```
$ python /tmp/acc121/crosscheck.py
violations: 0
read-verb tools: 76  declared payload: 76
os_deploy channel: file_effect | editor_capture_screenshot channel: payload
editor_capture_screenshot row: chev=25 calls=26 bnd=1 status=达标
os_deploy row: calls=6 bnd=6 chev=0 status=计数达标缺证据
```

即：TASK-119 的 D1 两条误声明（`os_deploy_to_android_device` → `file_effect`、
`editor_capture_screenshot` → `payload`）已改，且 76 个读类动词工具**全部**声明 `payload`，
动作类动词**无一**声明 `payload`。

**判定：pass。**

---

## 5. ⑤ 反例自证：M2 / M3 两类独立复刻

**不采信 `witness_records_selftest.py` 的自报**，我在内存副本上用自己的反例复刻。
副本做法：调用被测 `build_rows()` 生成真实 `run_index`，再 `copy.deepcopy` 出副本改字面量；
原件 trace 只读、跑完重哈希验证未变。

```
$ python /tmp/acc121/check45.py
get_node_properties seqs: [2, 18, 20, 22, 28]
stop_input_recording seqs: [5, 8, 11, 14, 17, 25, 27]

--- baseline ---
NEW rule, real corpus      : seq=18
OLD rule + old declaration : seq=2                       <- TASK-119 的 D3：写之前的读
NEW rule + old declaration : REFUSED: TASK-120 A3: … bare JSON key name ('"position"') …

--- M2：改见证回包里的字面量 ---
M2 value mutated (346.0 -> 0.0)    touched=1  NEW: REFUSED: none of the 5 substantive
                                                 `running_game_get_node_properties` payload(s) satisfies expect '"x":346.0'
M2 key renamed   (x -> posn)       touched=1  NEW: REFUSED: 同上

--- M3：把写后的读强改回起始值（“玩家一步没动”） ---
mutation count=3
OLD rule on mutated corpus: STILL SIGNED seq=2  <-- TASK-119 的缺陷可复现
NEW rule on mutated corpus: REFUSED: none of the 5 … satisfies expect '"x":346.0'

--- 单规则反例 ---
A1 witness is a write tool   -> REFUSED: TASK-120 A1: … is not a read call (verb=stop) …
A2 no call of the tool before-> REFUSED: TASK-120 A2: … not later than any of the 0 call(s) of `editor_get_node_info` …
A3 expect reverted to bare key-> REFUSED: TASK-120 A3: …
A4 bare expect_absent        -> REFUSED: TASK-120 A4: `expect_absent` is declared without `expect` …

original trace sha256 before/after: DF4783…9351 DF4783…9351 UNCHANGED: True
```

**判定：pass。** M2/M3 两类「旧口径签、新口径拒」的自证属实；
「新规则只是把门槛换了个地方装样子」被 M3 的对照直接否掉（旧规则在**同一份**被篡改语料上仍然签）。

---

## 6. ⑥ 可重算性与数字一致性

### 6.1 重跑真实脚本（输出到 scratch，不覆盖被验收工件）

```
$ PYTHONDONTWRITEBYTECODE=1 python tools/tool_coverage.py \
      --md /tmp/acc121/recompute.md --json /tmp/acc121/recompute.json
tool_coverage: mode=all-runs runs=112 trace_files=182 calls=8729 distinct=172
  buckets: 0=5 1-4=0 >=5=172 | status: 达标=169 缺证据=3 未达1-4=0 未达0=5
  registry: 74 members, 69 drift
```

### 6.2 与 `coverage.json` 逐条对拍

```
$ python /tmp/acc121/cmp_rows.py
base tools 177  recomputed tools 177
tool set equal: True
MISMATCH on (calls,ok,boundary): 0
OTHER differing row fields: 0          (status/status_legacy/tier/channel/chev/effective/bucket/verb/scope
                                        /pixel+file+read_payload_calls 全部逐条相等)
corpus equal: True        buckets equal: True      status_counts equal: True
tier_counts equal: True   channel_counts equal: True
verified_by_tool equal: True     rejected equal: True   fingerprints equal: True
generated_utc base/new: 2026-09-27T07:12:22Z / 2026-09-27T07:19:40Z   （唯一差异）
sum calls over 177 tools: 8729
```

### 6.3 不经该脚本的独立复算（自写解析器）

```
$ python /tmp/acc121/verify_witness.py
malformed lines: 0
sidecars re-hashed and verified by me: 221
independent totals calls=8729 ok=8057 failed=672 distinct=172
tools in contract with 0 calls: ['editor_simulate_key','editor_simulate_mouse_click','editor_simulate_mouse_move',
                                'editor_simulate_input_action','editor_simulate_input_sequence']
INDEPENDENT vs coverage.json  (calls,ok,boundary) MISMATCHES: 0
```

`corpus.sidecars_verified = 277` 也对得上（我一度按「仅 result sidecar」数出 221，经复核是其计数口径为
「args 或 result sidecar 通过」）：

```
$ python /tmp/acc121/sidecar.py
args sidecars verified: 63   result sidecars verified: 221   error_data sidecars verified: 2
rows with args OR result sidecar verified (the ledger's counter): 277
```

### 6.4 其余口径核对

```
$ python /tmp/acc121/delta.py
promoted_from_legacy_rule: 45      demoted_from_legacy_rule: 0      still_short: 8
channel_counts_declared == computed: {payload:76, file_effect:22, pixel_effect:28, editor_state:51}
channel_status: payload 75达标/1缺证据；file_effect 21/1；pixel_effect 28/0；editor_state 45/1/5未达0
tier_counts: readback 111, file_effect 24, pixel_effect 34, count_only 3, no_calls 5
basis_scope: channel_template
ledger_class census: {None:176, engine_not_implemented:1}
```

`still_short` 8 条 = 3 条缺证据 + 5 条 0 次，逐条理由与 §0.2 一致；
`engine_not_implemented`（`editor_set_auto_dismiss_dialogs`）被台账单列为「引擎未实现」而非「缺证据」，
其 trace 实测切分与报告 §D 的更正一致：

```
$ python /tmp/acc121/crosscheck.py
calls: 7 ok: 0   codes: Counter({-32000: 5, -32602: 2})
  seq=74..78 args={"enabled":true/false} -32000 Not implemented
  seq=79 args={} -32602 Missing required parameter 'enabled'
  seq=80 args={"enabled":"yes"} -32602 Parameter 'enabled' must be a boolean, got String
```

Android 三工具实测与登记表 `measured` 字段逐字一致：

```
('os_list_android_devices',        ok=True,  0)      ×5
('os_list_android_devices',        ok=False, -32602) ×1
('project_get_android_preset_info',ok=False, -32000) ×5   / -32001 ×1
('os_deploy_to_android_device',    ok=False, -32001) ×5   / -32602 ×1
```

### 6.5 判定

**pass。177 条逐工具 `(calls, ok, boundary)` 与 `coverage.json` 0 不符；没有任何对不上的地方。**

---

## 7. 缺陷（均不阻断通过）

| ID | 严重度 | 内容 | 归属 |
|---|---|---|---|
| **D1** | low | 任务书声称「needs-an-external-device **2**」，而登记表 `count = 3`（3 条 `tools`、3 条 `items`）。台账本身**没有隐瞒**：`items[]` 逐条给出 `os_list_android_devices = 达标`，未达标的恰 2 条。属**任务书措辞与工件口径的差异**，不是工件缺陷。 | 任务书 |
| **D2** | low（潜在） | `verify_readback()` 的 A2 把同一 run 下**多个 trace 文件**（editor/game）的 `seq` 合并比较，而 `seq` 只在单文件/单 generation 内可比。当前 51 条**全部**在见证调用所在文件内找得到严格更早的写调用（0 例外，见 §2.1 `a2exact.py`），但这是一个**未被语料触发**的潜在不健全点，将来跨端点声明可能被误签。 | `tools/tool_coverage.py` |
| **D3** | low | `editor_state` 通道的证据被硬编码为**最多 1**（`channel_evidence_count` 命中即 `return 1`）：30 次写与 6 次写在证据强度上不可区分，单次见证即授 `达标`。TASK-119 的 R2 指出过，本轮未变（属已披露的设计取舍）。 | `tools/tool_coverage.py` |
| **D4** | low | `expect` 证明的是「被写的值能从引擎回包里逐字读出来」，**不是**「该值由这次写产生」。可复现的例子：`editor_create_animation` 的 `"animations":["Anim1",…,"Anim5"` 前缀命中了一个同时含 `Anim6~Anim8` 的列表——字面量在场，但不能单独证明 Anim5 是这次调用建的。这是 A2/A3 的固有强度上限（TASK-120 §A3 已自述），不是造假。 | 规则强度 |
| **D5** | info | 任务书点名的入口 `recovery/reports/TASK-119-REPORT.md` **不存在**；TASK-119 的工件实为 `recovery/reports/ACCEPTANCE-TASK-119.md`（TASK-120 报告引用它时也没写对文件名）。 | 任务书/文档 |

---

## 8. 风险与不确定项

* **R1（17 条边界的语义强度）**：17 次补边界是同一种「未声明参数」探测。它们让 `boundary >= 1`
  的**计数门**成立，但没有测各工具自身的错误路径（例如 `editor_save_scene` 无场景可存时的拒绝）。
  台账与报告**已如实披露**（`c8-manifest` purpose 明写「no threshold is moved」），
  但阅读「达标 169」时应知道其中 17 条的边界证据是**注册器门**，不是工具语义边界。
* **R2（三条 input recording 的证明上限）**：契约里没有可读录制器内部状态的读工具，
  所以这三条的 `editor_state` 见证证明的是「被录下的输入真的驱动了游戏（写后位置 ≠ 起始值）」，
  而不是「录制器内部状态」。TASK-120 §A3/§E4-1 已披露；我复核其 `expect` 与 seq 关系后确认
  **规则层面无违规**，只是**语义上限**。
* **R3（我未重启引擎复跑）**：`unverifiable` —— 我没有启动 Godot 去真实重放这 177 条工具。
  c8 的「真拒绝」结论建立在：逐调用 response JSON + engine stdout（真实 build/端口/pid）+
  trace `trace_opened` + 注册器源码顺序。这是**证据支持**，不是本轮线上实测。
* **R4（`basis` 是通道级模板）**：`basis_scope = channel_template`，同通道 22/28/51/76 条
  `basis` 逐字相同，只有 `subject` 逐条不同。台账 §0.0 已把它作为引用块打印并说明
  （TASK-119 D6 的整改到位），但读者若只看 `basis` 仍会以为每条都做过个案论证。
* **R5（独立验收的边界）**：本报告的所有「比对一致」结论都是**证据支持**；
  凡属过程陈述（如 TASK-120「M1 用 classify 级等价检查替代语料级复刻」）我**未采信**，
  也未用它作为通过理由。

---

## 9. 独立运行的检查（命令 + 关键输出行）

| # | 命令 | 关键输出 |
|---|---|---|
| 1 | `python tools/tool_coverage.py --md/--json <scratch>` | `runs=112 trace_files=182 calls=8729 distinct=172`；`达标=169 缺证据=3 未达0=5` |
| 2 | `python /tmp/acc121/cmp_rows.py` | `MISMATCH on (calls,ok,boundary): 0`；`OTHER differing row fields: 0` |
| 3 | `python /tmp/acc121/verify_witness.py` | `calls=8729 ok=8057 failed=672`；`MISMATCHES: 0`；`MY verified witnesses: 51  MY refused: 0` |
| 4 | `python /tmp/acc121/probe9.py` | 9 条「原文未命中」实为信封反转义后逐字命中（`MATCH in unescaped`） |
| 5 | `python /tmp/acc121/check3.py` | `17` 条全 `-32602`、`Unknown parameter 'undeclared_probe'`、`all args carry undeclared_probe only: True` |
| 6 | `python tools/tool_coverage.py --exclude c8-task120 …` | `runs=111 trace_files=180 calls=8712`；`达标=152 缺证据=20 未达0=5` |
| 7 | `python /tmp/acc121/check3b.py` | 17 条 `boundary 1->0 达标->计数达标缺证据 calls+1`；其他行变化 `0` |
| 8 | `python /tmp/acc121/check45.py` | 4 类装载期 `SystemExit`；M2 拒签、M3 旧签 seq=2 / 新拒签；trace 哈希前后一致 |
| 9 | `python /tmp/acc121/check12.py` | 51 条声明；`expect_absent` 4 条、裸 `expect_absent` 0 条；5 条抽样的写/见证 seq 与字面量命中 |
| 10 | `python /tmp/acc121/crosscheck.py` | 通道↔verb `violations: 0`；`read-verb tools: 76 declared payload: 76`；引擎未实现 trace `5×-32000 + 2×-32602` |
| 11 | `python /tmp/acc121/a2exact.py` | `A2 exactness problems: 0` |
| 12 | `git diff 36b7be4 188c090` + `python /tmp/acc121/gitdelta.py` | `declarations that differ … : 14`；`REMOVED: 无 ADDED: 无` |
| 13 | `sed -n '795,870p' tool_registry.cpp` | `_reject_unknown_arguments()` 在 `call_tool()` 里先于 handler |
| 14 | `cat runs/_exercises/ex_grid/c8-task120/engine-editor.stdout.txt`、`c8-002-*.json` | 真实 `Godot Engine v4.8.dev.mono`、`listening on 127.0.0.1:9905`、引擎自己的 `-32602` 响应 |
| 15 | `python /tmp/acc121/sidecar.py` | `rows with args OR result sidecar verified = 277` = `corpus.sidecars_verified` |
| 16 | `sha256sum`（前/后各一次） | 五个对象文件哈希逐字节相同 |

---

## 10. 现场清理

全部复核脚本、重算产物、通道表副本均位于仓库之外的 `%TEMP%\acc121\`，验收结束后已 `rm -rf` 删除。
仓库内本轮**只新增** `recovery/reports/ACCEPTANCE-TASK-121.md`；
被验收对象（`coverage.json`、`TOOL-COVERAGE.md`、`tools/**`、`runs/**`、`godot/modules/mcp_server/**`）
未做任何写入（§0.3 哈希与 `git status` 可查）。
