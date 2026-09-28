# TASK-DR48-REPORT — 批次二缺陷修复包（DR-48..DR-53）实现报告

- 执行者：实现子代理（**无**上游对话上下文；唯一任务来源 `.spec/hof-rs/tasks/TASK-DR48-FIX.md`）。
- 落点：`F:\moonbit-hof-rs`（外层仓 `master`）。
- 本批为**纯离线批**：未启动 Godot、未接触任何端口、未联网、未调用任何模型端点；`godot-mcp/**` 只读。
- 提交（每项一个提交，英文信息带 DR 编号，均未 push）：

| 提交 | 内容 |
|---|---|
| `9d71a17` | adapter: exempt only the engine's exact info banners in the launch gate (DR-48) |
| `777254d` | adapter: make screenshot evidence fresh, contract-shaped and fallback-safe (DR-49) |
| `d8fc107` | adapter: send GDScript *bodies* to running_game_execute_gdscript (DR-50 part A) |
| `987ef15` | identity: persist the real /mcp status and the registered game endpoint (DR-51) |
| `f6fead9` | adapter: read the engine's input-action list and audit every call's parameter shape (DR-52) |
| `d8e347e` | adapter: leave an unparseable enabled= line alone, and cover the two batch-1 gaps (DR-53) |

---

## 1. 结论

**六项（DR-48..DR-53）全部落地；`cargo test --offline` exit 0。**

五项纯 hof-rs 缺陷（DR-48/49/51/52/53）已修复并留反例测试；**DR-50 定性完成，其中
"游戏端点挂死"判为引擎侧缺陷 ⇒ 按 §14.3 停下上报 BLOCKER（见 §4），未改引擎；
同时修掉了定性过程中**被原始记录证明**的 hof-rs 侧调用形态缺陷（`execute_gdscript` 的
`code` 必须是 GDScript 函数体）——它不是挂死的原因，但不修则 E3 永远不可判定。**

真实输出（`cargo test --offline`，34 个 target 的汇总：**passed=328 / failed=0 / ignored=7**）:

```
running 10 tests
test every_role_prompt_renders_the_budget_and_the_discipline ... ok
test config_carries_the_new_budget_and_readiness_keys ... ok
test the_godot_developer_artifact_validity_needs_a_real_entry_script ... ok
test consecutive_limits_failures_stop_after_one_retry ... ok
test a_valid_artifact_does_not_trigger_the_wrap_up_retry ... ok
test a_missing_artifact_triggers_the_wrap_up_retry_with_a_reason ... ok
test limits_exceeded_then_one_wrap_up_retry_succeeds ... ok
test a_normal_finish_without_an_artifact_keeps_its_existing_retry ... ok

test result: ok. 10 passed; 0 failed; 0 ignored; 0 measured; 0 filtered out; finished in 16.14s

   Doc-tests hof_rs

running 0 tests

test result: ok. 0 passed; 0 failed; 0 ignored; 0 measured; 0 filtered out; finished in 0.00s

EXIT=0
```

`#[ignore]` / 环境门控项（唯一一处）：

```
running 0 tests
test result: ok. 0 passed; 0 failed; 7 ignored; 0 measured; 0 filtered out; finished in 0.00s
```

= `tests/godot_smoke.rs` 的 7 条：它们要求**活的编辑器 + 真实引擎二进制**（真机门控），
本批是离线批，**未运行**（批次一 D218 记录的同一组 7 条）。

---

## 2. 逐 DR 判据对照（命令 → 真实输出 → 文件:行）

### DR-48 可启动闸门假阴性

- 红（实现前，`cargo test --offline --test launchable_gate`）:
  ```
  test an_engine_info_banner_does_not_close_the_gate ... FAILED
  thread '...' panicked at tests\common\mod.rs:270:13:
  FakeHarness step #2 expects Tester but the runtime asked for Developer;
  actual sequence so far: ["planner", "developer", "developer"]
  ```
  ⇒ 闸门假阴性**真的**多烧了一次 Developer 调用（这正是 DEF-A 的代价）。
- 绿（实现后）: `test result: ok. 11 passed; 0 failed; 0 ignored; ...`
- 实现：`ENGINE_INFO_BANNERS`（常量数据，**逐字**等于 `godot-mcp/godot/modules/mcp_server/mcp_server.cpp:605`
  与 `:645`，也与 `smoke-t6` 轮里 `%APPDATA%\Godot\app_userdata\HoH Mario\logs\*.log` 的 5 行一致）
  → `src/adapter/godot.rs:3243`；具名匹配函数 `is_engine_info_banner` → `:3258`；
  过滤 `non_banner_editor_errors` → `:3267`；判定点 `step_editor_errors` → `:768`。
- 根因自证（我亲自读引擎源码）：`tools/editor_read_scene_inspector.cpp:249`
  `if (source.lines[i].to_upper().contains("ERROR")) { errors.push_back(...) }` ——
  `capture=off (…on_error…)` 因大小写无关的 `error` 命中。
- 反例（全部通过，且**在实现前就已通过**，证明我没有放宽闸门）：真 `ERROR:` 行、
  `ERROR: [MCP] SceneTree never became available; MCP server disabled.`、
  未知 `[MCP]` 行、截断横幅 `[MCP] capture=off` ⇒ 全部仍判"不干净"。

### DR-49 截图证据必须"本轮真实"

- 红（实现前）:
  ```
  test a_stale_png_is_never_mistaken_for_this_runs_screenshot ... FAILED
    panicked at tests\evidence_battery.rs:1546:
    a PNG that was already on disk is not this run's evidence (DR-49):
    ExecRecord { kind: Screenshot, path: Some(".hoh/evidence/frame-00.png"),
                 observation: "screenshot written to .hoh/evidence/frame-00.png (46 byte(s))", ... }

  test the_screenshot_call_carries_no_filesystem_path ... FAILED
    panicked at tests\evidence_battery.rs:1510:
    a filesystem `save_path` is a contract violation (DR-49):
    C:\Users\wyl\AppData\Local\Temp\.tmphCvRbq\workspace\.hoh/evidence/frame-00.png

  test a_stale_png_does_not_suppress_the_frames_fallback ... FAILED
    panicked at tests\evidence_battery.rs:1582: left: 0  right: 1   (capture_frames 调用次数)
  ```
  ⇒ 三条缺陷各自独立复现：**旧文件伪造成功**、**传文件系统路径**、**旧文件压制回退**。
- 绿: `test result: ok. 30 passed; 0 failed; 0 ignored; 0 measured; 0 filtered out`（`--test evidence_battery`）
- 实现：`step_screenshot` → `src/adapter/godot.rs:1064`（不再传 `save_path`，改用内联图像落地；
  调用前作废旧文件；`ok` 由新鲜度决定；回退由"本轮还没有图像"决定）；
  `ArtifactFingerprint` → `:2159`；`artifact_fingerprint` → `:2167`；`artifact_is_fresh` → `:2195`；
  `invalidate_artifact`（改名到 `*.stale-<unix>`，失败则删除，绝不留在原地）→ `:2214`。
- 契约依据（引擎源码）：`tools/running_game_capture.cpp:56-61`（无 `save_path` 时答案内联）、
  `:62-63` 的取值域规则（实现点是 `:93` 的 `normalize_screenshot_path`）。测试替身现在**自己执行这条取值域**，
  任何回归到文件系统路径都会被 `-32602` 挡住。

### DR-50 游戏端点挂死（定性 + hof-rs 侧形态修复）

见 §4（完整判据、原始输出与结论）。

- 红（`--test evidence_battery`，把替身改成忠实模拟引擎的"无 `return` ⇒ Nil"后）:
  ```
  4 failed: the_game_probe_calls_are_gdscript_bodies, a_usable_game_channel_makes_the_replay_green,
            input_replay_reports_an_action_that_is_not_bound, green_battery_records_every_step...
  FAILED input channel probe: ACTION_BINDING_UNKNOWN (the game-process probe could not be read
  (the game process could not be read: {"note":"The body returned no value (result is null /
  result_type \"Nil\"). ...","result":null,"result_type":"Nil"}); ...
  ```
  ⇒ **替身端到端复现了真机 `smoke-t6` 的原句**。
- 绿: `test result: ok. 30 passed; 0 failed; ...`
- 实现：`probe_scripts`（读值用 `return str(...)`，`press`/`release` 保持语句）→ `src/adapter/godot.rs:2474`。

### DR-51 端点身份必须真正持久化

- 红（`--test launchable_gate`，缺 API 的编译失败）:
  ```
  error[E0407]: method `game_endpoint_history` is not a member of trait `ToolChannel`
  error: could not compile `hof-rs` (test "launchable_gate") due to 1 previous error
  ```
  以及实现中间态的真实失败（`initialize` 路径把 `editor_status` 写成 `{}` 而非 `null`）:
  ```
  test the_run_meta_keeps_the_game_endpoint_the_battery_registered ... FAILED
    panicked at tests\launchable_gate.rs:570: assertion `left == right` failed
      left: Object {}    right: Null
  ```
- 绿: `--test launchable_gate` 12 passed；`--test dual_endpoint` 8 passed；`--test engine_identity` 18 passed。
- 实现：`fetch_editor_status`（真实 `GET <endpoint>`）→ `src/tools/mcp.rs:49`；
  `editor_status_for`（**只有"驱动引擎"的 adapter 才发 GET**，失败退化为 `null`）→
  `src/runtime/engine_identity.rs:34`，接入点同文件 `probe`；`record_game_endpoint` →
  `src/adapter/engine.rs:498`；`ToolChannel::game_endpoint_history` → `src/tools/mod.rs:88`，
  `McpChannel` 在**登记当刻**写入且**不被 clear 清掉** → `:277`；回写点 `src/runtime/run_loop.rs:791`
  与第二遍 `:863`（电池结束后立刻、且在电池自己的 stop 清掉之后仍取得到）。
- `EngineIdentity::unavailable` 的 `editor_status` 由 `{}` 改为 `null`
  （`src/adapter/engine.rs:119`），使 §13.4 的 "`null` + reason" 在两条路径上一致。
- 端到端判据：这次的 `meta.json.engine.mcp.game_endpoint` 是
  `http://127.0.0.1:9878/mcp` / `port=9878` / `source=auto_free_port` / `reason=null`，
  **而电池的 `editor_stop_scene` 确实清掉了 route**（测试同时断言 route 为 `None`）。

### DR-52 诊断自洽 + 参数形状核对

- 红（把解析改回旧语义后重跑，真输出）:
  ```
  test adapter::godot::tests::the_input_action_list_is_read_from_the_engine_shape ... FAILED
    panicked at src\adapter\godot.rs:3596: assertion `left == right` failed
      left: 0    right: 5

  test the_editor_input_map_diagnostic_agrees_with_its_own_record ... FAILED
    panicked at tests\evidence_battery.rs:1273:
    the diagnostic must agree with the record it quotes (DR-52): ...
    EDITOR_SIDE_INJECTION: the editor InputMap does not list ["move_left", "move_right", "jump"]
    (0 action(s) read) — ... 
  ```
  ⇒ 与 `smoke-t6` 的 DEF-E 原句**逐字同形**。
- 绿: `--test evidence_battery` 30 passed；`--lib` 102 passed。
- 实现：`parse_input_actions` 现在读**名字数组**（引擎真实形态）→ `src/adapter/godot.rs:2281`；
  `EDITOR_SIDE_INJECTION` 诊断句改为与自己的解析结果同源，并公布读到的动作条数（同文件 `:1597-1611`）。
- 参数形状核对：见 §3；机器化审计在 `tests/evidence_battery.rs`
  （`check_arguments` + `the_parameter_shape_checker_rejects_the_smoke_t6_violations` +
  `every_tool_call_hof_rs_makes_matches_the_contract_schema`）。

### DR-53 批次一遗留 minor

- 红（把 `Unrecognised` 临时改回旧语义 `Emptied` 后重跑 `--test cli_init`，真输出）:
  ```
  test init_leaves_a_malformed_enabled_line_untouched_and_says_why ... FAILED
    panicked at tests\cli_init.rs:181: assertion `left == right` failed:
    the file must be byte-identical (DR-53)
      left:  "config_version=5\n\n[application]\n\nconfig/name=\"x\"\n\n[rendering]\n\n..."
      right: "config_version=5\n\n[application]\n\nconfig/name=\"x\"\n\n[editor_plugins]\n\nenabled=true\n\n[rendering]\n\n..."
  ```
  ⇒ 整段 `[editor_plugins]` 被删（DEF-2 的复现）。
- 绿: `--test cli_init` 5 passed；`--lib` 102 passed（含 `the_snapshot_is_the_real_177_tool_contract`）。
- 实现：`PackedArrayEdit`（Absent/Updated/Emptied/**Unrecognised**）→ `src/adapter/godot.rs:2750`；
  `packed_string_array_without` → `:2763`；`AddonCleanup`（Untouched/Removed/**Unparseable(reason)**）
  → `:2807`；`ensure_bundled_addon_disabled` → `:2845`；`initialize` 用 `tracing::warn!` 写出 reason。
- 两条回归测试：`tests/dual_endpoint.rs::an_endpoint_without_a_declared_port_source_is_undeclared`
  （缺字段 / 未知取值 → `undeclared`；两个文档化取值仍逐字记录）；
  `tests/engine_identity.rs::the_gate_closes_when_the_listener_cannot_be_read`
  （`matches_binary == None` → 关闸、observation 点名"no TCP listener"、与 mismatch 文本不同、
  `evaluate_launchable` 判不可启动）。
- 测试改名收紧：`the_snapshot_is_the_real_174_tool_list` → `the_snapshot_is_the_real_177_tool_contract`
  （`src/tools/index.rs:264`），断言由 `>= 100` 收紧为 `== 177` + 每条必须有名字。

---

## 3. DR-52 完整参数形状核对表

核对基准：`tests/fixtures/mcp/tools_list.json`（177 条，即 `docs/tools_list.renamed.json` 的仓库内快照，
也就是 `godot-mcp/recovery/TEST-CASES.md` §2 的 177 条 `TC-TOOL-*` 逐工具输入形式；两者对下述 15 条
的 `必填/可选/默认` 逐字一致，我逐条比对过 §2 的行）。
"hof-rs 现状"= 本批**修复后**实际发送的参数（由 `every_tool_call_hof_rs_makes_matches_the_contract_schema`
从替身记录的**真实调用**中取得，不是照抄代码字面量）。

| # | 工具 | 契约形状（必填 / 可选 / 默认 / 取值域） | hof-rs 现状（调用点） | 一致 | 处理 |
|---|---|---|---|---|---|
| 1 | `editor_rescan_project_filesystem` | req 0 / opt 0 | `{}`（`godot.rs:651`） | ✅ | — |
| 2 | `editor_open_scene` | req `path:string` | `{"path": main_scene}`（`:664`） | ✅ | — |
| 3 | `project_read_scene_file_content` | req `path:string` | `{"path": scene}`（`:710`） | ✅ | — |
| 4 | `editor_get_errors` | opt `max_lines:integer`=50 | `{"max_lines": 50}`（`:775`） | ✅ | 等于默认值，显式传无害 |
| 5 | `editor_play_scene` | opt `extra_args:array`=[]、`headless:boolean`=false、`mcp_port:integer`、`mode:string`="main"（取值域 main/current/res:// 路径） | `{"mode":"main"}`（`:821`） | ✅ | — |
| 6 | `running_game_get_scene_tree` | opt `max_depth:integer`=-1、`named_only:boolean`=false、`script_filter:string`、`type_filter:string` | `{"max_depth":-1}`（`:887`、`:968`） | ✅ | — |
| 7 | `running_game_capture_screenshot` | opt `save_path:string`；**取值域 `res://`\|`user://`**（`running_game_capture.cpp:62-63`，schema 表达不出） | **修复前** `{"save_path": "<文件系统绝对路径>"}` ⇒ 三次 `-32602`；**修复后** `{}`（内联图像落地） | ❌→✅ | **DR-49 修复**；审计里加了取值域规则 + 反例 |
| 8 | `running_game_capture_frames` | opt `count:integer`=5、`frame_interval:integer`=10、`half_resolution:boolean`=true | `{"count":1,"frame_interval":10}`（`:1205`） | ✅ | 用默认 `half_resolution` |
| 9 | `running_game_get_node_property_samples` | req `node_path:string`、`properties:array`；opt `frame_count:integer`=60、`frame_interval:integer`=1、`sample_stride:integer`=1 | `{"node_path":"Player","properties":["position"],"frame_count":N,"frame_interval":1}`（`:1228`、`:1650`） | ✅ | 未传 `sample_stride`（默认 1，与旧行为同） |
| 10 | `running_game_execute_gdscript` | req `code:string`；**取值域：GDScript 函数体**（`running_game_script_execution.cpp:57-59`，schema 表达不出） | **修复前** `str(...)` 裸表达式 / `str(Input.action_press(...))`（void 当值，编译不了）；**修复后** 读值 `return str(...)`、副作用保持语句 | ❌→✅ | **DR-50(A) 修复**；审计里加了"void 当值 / 空 body"规则 + 反例 |
| 11 | `editor_get_input_actions` | req 0 / opt 0（应答形态 `{"actions":[名字…],"count":N}`） | `{}`（`:1523`） | ✅ | 应答**解析**曾错（DR-52）；调用形态本就对 |
| 12 | `editor_simulate_input_action` | req `action:string`；opt `pressed:boolean`=true、`strength:number`=1.0 | `{"action":…,"pressed":true}`（`:1606`） | ✅ | — |
| 13 | `running_game_get_node_properties` | req `node_path:string`；opt `properties:array` | `{"node_path": node}`（`:1790`） | ✅ | 用默认全属性 |
| 14 | `editor_get_collision_info` | opt `node_path:string` | `{"node_path": node}`（`:1821`） | ✅ | — |
| 15 | `editor_stop_scene` | req 0 / opt 0 | `{}`（`:1934`） | ✅ | — |

补充说明：

- 表覆盖的是 hof-rs **真正调用**的 15 个工具（`src/**` 里另外 23 个四通道名字只出现在策略表 / 提示词 /
  索引示例中，不在调用路径上——它们由 `tests/tools_policy.rs` 与 `tests/tool_vocabulary.rs` 负责）。
- 修复前的两处不一致**都不在"名字"上**（DR-42 的改名是对的），而在**取值域 / 值形态**上——
  这正是 D220 第 3 条点名的漏迁面。
- 审计测试的守护力：`AUDITED_TOOLS` 列表是覆盖下限；新增/改名调用点会让测试**红**，直到它被列入。

---

## 4. DR-50 定性结论（**BLOCKER + 上报**）

### 4.1 判据与原始输出（只读、可复现）

复现脚本：一段只读 Python（读 `runs/smoke-t6/**` 与引擎源码，不写任何东西），输出如下（逐字）：

```
### 1. game-endpoint request ids of the second battery pass (raw/*.json)
  play_scene_ready       req=  30 editor_play_scene ok
  play_scene_ready       req=   1 running_game_get_scene_tree ok
  scene_tree             req=   2 running_game_get_scene_tree ok
  screenshot             req=None running_game_capture_screenshot ERR://', got '.workspace/mario\.hoh/evidence
  input_channel_probe    req=   6 running_game_execute_gdscript ok code='str(get_tree().current_scene.get_node_or_null("Player").posi'
  input_channel_probe    req=   7 running_game_execute_gdscript ok code='str(InputMap.has_action("move_right"))'
  input_channel_probe    req=   8 running_game_execute_gdscript ok code='str(Input.is_action_pressed("move_right"))'
  input_channel_probe    req=   9 running_game_execute_gdscript ok code='str(Input.get_axis("move_left", "move_right"))'
  input_channel_probe    req=None running_game_execute_gdscript ERR:...(os [10060]) code='str(Input.action_press("move_right"))'
  input_channel_probe    req=None running_game_get_node_property_samples ERR:...(os error 10061)
  input_channel_probe    req=None running_game_execute_gdscript ERR:...(os error 10061) code='str(Input.get_axis("move_left", "move_right"))'
  input_channel_probe    req=None running_game_execute_gdscript ERR:...(os error 10061) code='str(get_tree().current_scene.get_node_or_null("Player").posi'
  input_channel_probe    req=None running_game_execute_gdscript ERR:...(os error 10061) code='str(Input.action_release("move_right"))'

### 2. transport timeline (mcp-errors.jsonl)
  running_game_capture_screenshot           -32602 x3
  running_game_execute_gdscript              10060 x3
  running_game_execute_gdscript              10061 x9
  running_game_get_node_properties           10061 x9
  running_game_get_node_property_samples     10061 x15

### 3. the four successful execute_gdscript answers (verbatim, truncated)
  successful calls: 4
    req=6 code='str(get_tree().current_scene.get_node_or_null("Playe'
      -> result=None result_type='Nil' note=yes
    req=7 code='str(InputMap.has_action("move_right"))'
      -> result=None result_type='Nil' note=yes
    req=8 code='str(Input.is_action_pressed("move_right"))'
      -> result=None result_type='Nil' note=yes
    req=9 code='str(Input.get_axis("move_left", "move_right"))'
      -> result=None result_type='Nil' note=yes
  first failing call:
    code='str(Input.action_press("move_right"))'
    error.attempts=3
    error.message='MCP request to http://127.0.0.1:63698/mcp failed: ... Error encountered in the
      status line: ... (os error 10060)'

### 4. the two rounds (ports/pids)
  developer.attempt2.json mentions '65333': 211x ; '109964': 4x
  developer.attempt2.json mentions 'os error 10060': 8x ; 'os error 10061': 88x
  editor_stop_scene: {"args": {}, "game_endpoint_invalidated":
    {"endpoint": "http://127.0.0.1:63698/mcp", "pid": 101872, "port": 63698,
     "source": "auto_free_port"}, "ok": true, ...}
```

时间线（`mcp-errors.jsonl` 的 `timestamp`，秒）：`t=1790618321 / 683 / 9044` 三次 `10060`
（间隔 362 s、361 s，= `tools.timeout_seconds=120` × 3 次尝试），随后 `t=1790619051` 起全部 `10061`。

### 4.2 我的定性

**A. hof-rs 侧调用形态缺陷（已证，已修，置信度：高）**

`code` 是 GDScript **函数体**（`tools/running_game_script_execution.cpp:57-59`），值只能靠 `return`
传出。hof-rs 发的是裸表达式，于是 4 次传输成功的调用**全部**回答
`{"result":null,"result_type":"Nil"}`（引擎还附了 "body with no `return`" 的 note）；
第 5 个 body `str(Input.action_press("move_right"))` 更进一步：`Input.action_press` 返回 `void`，
用它作值在本引擎里是**编译错误**（`modules/gdscript/gdscript_analyzer.cpp:3498`:
`Cannot get return value of call to "%s()" because it returns "void".`）。
引擎自己的游戏态脚本一律写 `return …`（例：`scripts/mcp013_editor_input_evidence.ps1:626`
`$probeCode = 'return InputMap.has_action("mcp013_probe_action")'`），这就是契约的活证据。
⇒ 这是 hof-rs 的调用形态缺陷，**与挂死无关**，但不修则游戏态读数永远拿不到（E3 不可判定）。
已在 DR-50(A) 修复（§2）。

**B. 游戏端点挂死 = 引擎侧缺陷（BLOCKER；根因未定，置信度：对"故障在引擎那一侧"为高，
对"引擎内部具体机制"为未定）**

判据：

1. hof-rs 发的是**合规** JSON-RPC `tools/call`（`id`、`method`、`params.name`、`params.arguments` 齐备，
   参数 `code:string` 满足契约的必填项）；同一形态前 4 次都被正常应答。
2. 失败点是**传输层**：连接建立后请求已发出、**状态行始终没来**（`10060`，ureq 报文
   "Error encountered in the status line"），重试 3 次 × 每 3 次之间 120 s 均如此。
3. 随后**监听消失**：`10061`（连接被拒 = 端口关闭）——即游戏进程的 MCP 监听器不复存在。
   首次 `10060` 到首次 `10061` 之间约 **730 s**，期间"能连、不答"，之后彻底消失。
4. **编辑器端点全程健康**：同一轮 ids 31–43 的 `editor_get_input_actions` /
   `editor_simulate_input_action` / `editor_get_collision_info` / `editor_stop_scene` 全部 `ok`，
   且 `editor_stop_scene` 自己回报告了 `game_endpoint_invalidated` 的真实记录 ⇒ 编辑器与
   harness 进程都没问题，故障**只局限在游戏进程**。
5. **两轮可复现**：pass1 `65333/pid 109964`（`10060` ×8、`10061` ×88），pass2 `63698/pid 101872`。
6. 唯一与挂死**同时出现的**差别是：第 5 次调用是**第一条 code 编译不通过**的请求
   （前 4 条只是没有 `return`，能编译）。引擎对"`code` 编译不过"的**书面答案**是 `-32602`
   （`data.parse_error_line` 一套），绝不是一个不答的挂死。因此
   "编译错误路径 ⇒ 不答 ⇒ 进程/监听消失"在证据上高度可疑，但**离线无法证明其内部机制**
   ——这正是我标为根因未定的原因。

结论：**按 §14.3 的硬要求，停下并上报 BLOCKER：游戏端点在收到一个 `code` 无法编译的请求后
不再应答并最终失去监听，这是引擎侧的可用性缺陷（`godot-mcp/**` 未做任何修改）。**
建议用户把它作为引擎侧缺陷单独立项（复现步骤即上述原始记录 + 一条最小化复现：
在 `editor_play_scene` 后**第一件事**就用 `running_game_execute_gdscript{code:"this is not gdscript"}`，
预期 `-32602`，实测若挂死则引擎缺陷被孤立确认）。

**hof-rs 侧绕行方案（不改引擎，本次只给方案不实施——它涉及设计取舍）**

1. **绝不再发送编译不过的 `code`**（本批已修：读值 `return`、void 调用保持语句）；把
   `execute_gdscript` 的返回值缺失当作"通道不可读"而不是"动作不存在"（DR-35 已有该语义）。
2. **把 E3 的关键路径从 `execute_gdscript` 上移走**，改用语义专用工具（都是 `running_game_*`，
   已在 177 契约内、且不依赖调用方拼 GDScript）：`running_game_get_node_property_samples`
   （逐帧采样，已在用）、`running_game_create_input_recording` + `running_game_play_input_recording`
   （录制/回放输入）、`running_game_run_test_scenario`、`running_game_assert_node_state`、
   `running_game_move_player_to_target`。本批**未**改这条路径（那要先回阶段二/三改设计并更新
   `DESIGN-DETAIL.md`，属于决策者的动作）。
3. **给游戏端点加"不可用即放弃"的快速失败**：一旦同一端点连续两次传输失败，后续
   `running_game_*` 调用可以直接判 `UNAVAILABLE`（省掉 120 s × 3 的重试，本轮在
   `input_replay` + `node_and_collision_assertions` 上白烧了约 12 分钟）。这同样是"是否
   值得"的决策，未在本批实施。
4. **重试策略**：`-32602` 这类 JSON-RPC 业务错误当前也被重试 3 次（`smoke-t6` 的截图调用就是
   3 次同样的 `-32602`）。这与本批 DR-49 相关但独立，未改（会改变既有重试语义，需决策）。

### 4.3 我**没有**做的事（遵守禁令）

- 未修改 `godot-mcp/**`（§6 有真实输出）。
- 未启动 Godot、未做任何活体复现（本批是离线批；9877 上的编辑器 PID 108432 全程未被触碰，
  我只做了两次**只读**的身份查询）。
- 未"修"挂死本身：任何超时/重试/端点相关的改动都没做（上面绕行方案 2/3/4 全部只给方案）。

---

## 5. 被修改的既有断言（逐条：原断言 / 新断言 / 为什么语义等价）

| # | 位置 | 原断言 | 新断言 | 为什么语义等价（或为何必须变） |
|---|---|---|---|---|
| 1 | `src/adapter/godot.rs`（原 `the_probe_scripts_are_single_expression_readings` → 现 `the_probe_scripts_are_single_line_bodies`） | 所有脚本 `starts_with("str(")` 且 `!contains("return ")`；断言来源写的是**已退役插件**的 `Expression::execute` 语义 | 读值脚本 `starts_with("return str(")` 且无换行；`press`/`release` `starts_with("Input.action_")` 且无换行；`has_action("jump")` 逐字 `return str(InputMap.has_action("jump"))`；`player_position()` 仍必含 `get_tree()` 且不含 `Engine` | **不等价，是必须变**：原断言的语义主体（"插件用 Expression 求值"）在换代后已不存在；`smoke-t6` 的原始记录证明旧形态产出 4 个 `Nil`。仍然被断言的部分（单行、`get_tree()` 可达性、无引擎单例、`has_action("jump")` 的精确文本）一条都没删；新增的"读值/副作用"区分比原断言**更强**（原断言把 `press` 也当成 `str(...)` 读值，那正是编译不过的写法）。 |
| 2 | `src/tools/index.rs::the_snapshot_is_the_real_174_tool_list` → `the_snapshot_is_the_real_177_tool_contract` | 名字写 174；断言 `schemas.len() >= 100` | 名字写 177；断言 `== 177` + 每条 entries 必须有非空 `name` + 三个代表工具存在 | **收紧**：`>= 100` 对 174→177 的变化永不敏感；`== 177` 与夹具/守卫（`tests/tool_vocabulary.rs` 的同一条数）一致。零放松。 |
| 3 | `src/adapter/godot.rs::editor_errors_are_parsed_as_json` | 未改动（DR-48 只改 `step_editor_errors` 的闸门判定） | 同前 | 该测试走 `build_check`（Tester 侧的信息性记录），其语义未变，保持全绿。 |
| 4 | `tests/evidence_battery.rs` 的 `ScreenshotMode::WritesFile` → `InlineImage`（含替身行为） | 替身按 `save_path` **自己写文件**并用 `is_file()` 通过 | 替身按契约：有 `save_path` 时先做取值域校验（非法 → `-32602`），无 `save_path` 时返回内联图像 | 不是放松而是**更严格**：替身现在会拒绝非 `res://`/`user://` 的 `save_path`，即把引擎的取值域变成测试的一部分；旧替身会替 hof-rs 掩盖这个缺陷。 |
| 5 | `tests/evidence_battery.rs` 的 `running_game_execute_gdscript` 替身分支 | 无条件按脚本内容返回读数 | 先按引擎的 body 语义：无 `return` 的读值 → `{"result":null,"result_type":"Nil"}`（引擎原句 note）；void 副作用仍按语句处理 | 不是放松而是**更严格**：它使端到端电池能复现真机缺陷（红证据），而旧替身无论 hof-rs 发什么都给读数，等于替缺陷背书。 |
| 6 | `tests/evidence_battery.rs` 的 `InputActionsMode` | 无 `EngineArray` 变体 | 新增 `EngineArray`（`smoke-t6` 真机的名字数组形态）；`input_actions_payload` 相应扩展 | 纯新增；原有 `Bound`/`Missing`/`RealEditorMap` 三个变体与它们的断言一字未动。 |
| 7 | `src/adapter/engine.rs::EngineIdentity::unavailable`（非断言的**被断言对象**） | `editor_status: Value::Object(Default::default())`（`{}`） | `editor_status: Value::Null` | 与 §13.4 "取不到 ⇒ `null` + reason" 一致；`engine.rs` 的既有测试只检查**键存在**，`tests/engine_identity.rs` 的既有测试只检查未探测块的整体形状，均未依赖 `{}`。这是我主动修正的一处契约不一致（见 §7 风险）。 |

未删除任何测试；`git diff --stat` 全程只有 `src/**`（7 文件）与 `tests/**`（5 文件）。

---

## 6. 禁区自查（真实输出）

```
=== PRD sha256 ===
4c81c3a9995f0b3afdf01421a0c3be88573cceefc284ce9bafbfda141f0f5c3a        ← 与要求逐字一致

=== git status --porcelain ===
(空)                             ← 写下本报告之前的最后一次自查（见下方说明）

=== 本批改了哪些顶层目录（4d3ff58..HEAD）===
Name  Count
src       7
tests     5

=== any godot-mcp change? ===            0        ← 5863 个受控文件，0 处改动
=== any Cargo change (no new deps)? ===  0        ← Cargo.toml / Cargo.lock 均未动
=== runs/ 或 .workspace 或 config/ 改动? === 0
=== git diff --cached --stat ===         (空，无暂存内容)
=== git status -sb ===
## master...origin/master [ahead 20]
=== origin/master ===
4b9bd44054ccfefdb4b96a342a133a4896769b76        ← 仍是旧值：**未 push**

=== runs/smoke-t6 字节不变 ===
文件数 = 135（与验收报告一致）
最新 mtime = 2026/9/29 2:32:01        ← 早于本批起点（4d3ff58 = 2026-09-29 02:52:08）
tree_sha256(135 个文件按相对路径排序 + 各自 sha256 串接)
  = 3ce19752eb0273546687dd0bec3716b5640d00b687b6de71e9815ea15cf025b9

=== 9877 上的编辑器（只做只读进程身份查询，未接触端口）===
   Id ProcessName                          StartTime
108432 godot.windows.editor.x86_64.mono     2026/9/29 0:36:03     ← PID 与启动时间均未变：未被杀/重启/抢占
```

其它：未使用 `web_search`（无联网）；所有 cargo 命令均带 `--offline`；未运行
`target/**/hoh.exe run`（无模型端点调用）；未 stage `runs/**`、`.workspace/**`、`config/*.secret*`；
`git commit` 均为显式路径 `git add`，从未 `git add -A`。

> 说明：上面 `git status --porcelain (空)` 的那次自查是在写下本报告**之前**跑的。
> 写完本报告后唯一多出的未跟踪文件就是本报告自身
> （`?? .spec/hof-rs/tasks/TASK-DR48-REPORT.md`）；我**没有**提交它——任务书只要求"写到"该路径，
> `.spec/**` 的入库应与 `DECISIONS.md` 的裁决一起由决策者提交。

---

## 7. 遗留风险与未验证项（区分「实测」与「推断」）

**实测（有原始输出支撑）**

1. 六项修复的离线判据全部为实测；反例测试（真 `ERROR:` 行仍关闸、旧 PNG 不再伪造成功、
   旧 PNG 不再压制回退、畸形 `enabled=` 不再改文件、`-32602` 型调用形状被审计拒绝）均为实测。
2. DR-50 的传输时间线、请求编号、两次成功的端口/pid、编辑器端点的健康——均来自 `runs/smoke-t6` 原始文件。
3. `runs/smoke-t6` 未被改动、`godot-mcp/**` 未改、PRD 未改、无新依赖、未 push——§6 的输出。

**未验证 / 推断（必须如实标注）**

1. **DR-50 的挂死根因未定**（推断）："第 5 次调用是第一条编译不过的 code，且它是挂死的那一条"
   是实测的相关性；"引擎的编译错误捕获路径在游戏进程里把主线程卡住"是我的**假设**，
   **离线不可验证**。挂死是引擎侧缺陷这个结论本身，依据是传输层证据（能连不答 → 监听消失）
   与 hof-rs 请求合规，置信度高但不是"活体复现"。
2. **本轮所有修复都没有真机验证**：E2（闸门）、E3（游戏侧证据）能否真正 met，必须等下一轮
   真机 T=1 冒烟 + 独立验收。特别是：
   - `running_game_capture_screenshot` **不带** `save_path` 的内联应答是否真如源码所写
     （`running_game_capture.cpp:56-60`）返回 `image_base64` —— 我按源码与 `capture_frames` 的同族形态
     判断，**未活体验证**；
   - `running_game_get_input_actions` 的 `{"actions":[名字…]}` 是我从 `smoke-t6` 原始 payload
     直接读出的（**实测**），但"编辑器 InputMap 是否真的含这三个动作"只在这一轮的记录里成立。
3. **`User://` 备选路径未实施**：设计允许"传 `user://` 或把内联图像落地"，我选了内联落地
   （更少假设，不需要推算 Godot 的 `user://` 目录映射）。若真机发现内联应答不落地或体积受限，
   需要回阶段三改设计。
4. **`EngineIdentity::unavailable` 的 `editor_status` 由 `{}` 改为 `null`** 是我主动做的一处
   契约收紧（§13.4 要求 `null`）。它改变了"未探测块"的字节形态；若某个外部消费者依赖 `{}`，
   需要回退——仓内没有任何测试或代码依赖它（实测：全套测试绿）。
5. **未改 `-32602` 被重试 3 次**：`smoke-t6` 的截图调用把同一个业务错误重试了 3 次
   （每次 1 s 间隔，代价小但语义可疑）。属独立缺陷，未在本批处理（会改重试语义，需决策）。
6. **未做参数形状的"活体"核对**：本批是按仓库内 177 夹具 + `TEST-CASES.md` 的逐工具输入形式核对；
   `docs/tools_list.renamed.json` 与 `TEST-CASES.md` 对 15 条的 `req/opt/default` 我逐条比对一致，
   但**未**连线引擎的 `tools/list` 逐字复核（离线批）；D220 已经记录过 `inputSchema` 有 2 处
   与夹具不同（`editor_get_test_report.clear.default`、`editor_simulate_input_sequence.events.items`）——
   这两个工具 hof-rs 都不调用，故不影响本表。
7. **`editor_status` 的 `GET /mcp` 未活体验证**：我用回环 HTTP 替身证明"取到就逐字记录、失败就
   `null`+reason、不驱动引擎就不发请求"，但真机 `GET 127.0.0.1:9877/mcp` 的应答形态只在
   D220/验收报告的记录里（`200` + JSON）。字段是 `Value`（不做形状断言），因此真机应答形态变化
   不会打破它。

---

## 8. 诚实披露（返工、猜错、绕过的尝试）

1. **第一次 baseline `cargo test` 是废的**：我在后台启动 baseline 的**同时**开始编辑
   `tests/launchable_gate.rs`，cargo 在编辑中途编译了半成品（`GateChannel` 已加字段但构造函数还没
   改），于是那次 exit 1 是**我自己造成的竞争**，不是批次前就有的失败。我重跑了一次干净的
   baseline 才拿到可信的红证据（DR-48）。教训：先跑完 baseline 再动手。
2. **DR-50 里我改了"看起来不该由我改"的东西**：`probe_scripts`（`code` 的函数体形态）。
   我的判断依据是：DR-50 要求"定性"，而定性过程中**被原始记录直接证明**的 hof-rs 侧调用形态缺陷
   必须修，否则下一次真机仍然拿不到 E3；挂死本身我**没有碰**（只上报）。如果决策者认为
   "DR-50 只能定性、任何改动都越界"，`d8fc107` 可以单独 revert，六项里其余五项不受影响。
3. **一次猜错**：DR-53 的单元测试里我写了 `json!([],)`（多余逗号）导致 lib 编译失败，
   白跑一次；已修正并重跑红证据。
4. **两次"临时改回旧语义"来取红证据**：DR-52（把 `item.as_str()` 分支临时 `continue`）与
   DR-53（把 `Unrecognised` 临时改成 `Emptied`）都是我先实现、后为了拿到**真实红输出**而临时
   回退、跑完立刻恢复。恢复后都重跑了绿色（lib 102 / evidence_battery 30 / cli_init 5）。
   我**没有**把这两次临时状态留在任何提交里（§6 的 `git status` 为空）。
5. **测试替身被我加强了两次**（DR-49 的 `save_path` 取值域、DR-50 的 body 语义）。
   这两处是我主动"让替身更难通过"，而不是让测试更容易通过；但它意味着
   `tests/evidence_battery.rs` 的替身不再与旧行为兼容——如果别处有依赖旧替身行为的假设，
   会在下一轮真机里显现。
6. **`cargo test --offline` 的 stderr**：PowerShell 5.1 会把 cargo 写到 stderr 的进度行
   变成 `NativeCommandError`，使某些命令的 `[exit code: 1]` 只是**输出管道的假象**。
   我最终判定 green 用的是把输出重定向到文件后的 `EXIT=0` 与各 target 的 `test result: ok`
   （§1），不是 shell 的退出码。
7. **未经我验证、只能"推断"的一条**：DR-52 的表格是"修复后"的真实参数；"修复前"的两处不一致
   我是从红测试的**实际失败输出**里读到的（`save_path` 的文件系统路径、`str(Input.action_press(...))`），
   不是从代码推断的。

---

### 报告落点

本文件即 `.spec/hof-rs/tasks/TASK-DR48-REPORT.md`。**回报给父代理只有一行：本报告路径。**
