# REPORT-009 — B1 closure: the `running_game_read_scene` group + helper de-duplication + local build script

* Task: `docs/tasks/TASK-009-b1-closure-running-game-read-scene.md`
* Playbook: `docs/tasks/PLAYBOOK-group-port.md` (§3 the gates, §4 this format, §6 known deviations, §7 discipline)
* Working tree: `F:\RustProjects\godot-mcp-pro\code\godot`, branch `feature/mcp-server-module`
* Engine under test: `bin\godot.windows.editor.x86_64.console.exe`, `4.8.dev.custom_build.97d35e097`,
  sha256 `4ac19b35a6a183458f15a6400ac7ac4d52ea4b1c78ad7cdf86bfdcc90961f342` (shim; the linked engine is
  `bin\godot.windows.editor.x86_64.exe`, 190,937,088 bytes, sha256
  `21C7667810E6E9EB5799409A0E7346FBCF0B66A862211A3FBD388363511B2950`)
* Every command below was run by this implementation subagent against that binary; the raw logs live in
  `%TEMP%\task009-impl\` and the evidence bodies in `%TEMP%\mcp009-running-game-evidence\`.
* Port discipline: the user's editor on **9877 (pid 36392)** was never touched; every phase printed a
  positive pid-same guard. All test traffic used **9888** (editor) / **9889** (game) only.

## 1. status

**done — B1 is closed.** All seven gates pass, the new group is registered and contract-verbatim, the
helper hoist is proven byte-neutral on the wire, and `docs/tool-groups.json` now reports 41/41. Nothing is
blocked. Two facts that the task brief predicted differently are reported as measured instead of being
smoothed over (§8.1, §8.2, §9).

## 2. commits

| sha | one line |
|---|---|
| `f63a5b8170` | `mcp_server: TASK-009 - failing tests for the running_game_read_scene group (TDD red)` |
| `b4d29f7e52` | `mcp_server: TASK-009 - port the running_game_read_scene group (1 game-scope tool)` |
| `97d35e0971` | `mcp_server: TASK-009 - hoist the editor guard and the property helpers into tool_helpers` |
| `3dea81b3d6` | `mcp_server: TASK-009 - REPORT-009 and the corrected bottom-layer evidence project` |

No `git push` was issued. The working tree keeps only the four pre-existing untracked entries
(`.graphifyignore`, `build-m0.cmd`, `graphify-out/`, `install-deps-m0.cmd`). `3dea81b3d6` adds this report
and the one behavioural fix to the evidence script (§9, deviation 3); further documentation-only commits
record these shas and this wording, and `git log --oneline` on the branch lists the complete sequence in
order.

## 3. The tool

### 3.1 per-tool table

| new_name | migration-source location | observable contract (as implemented) | C++ landing site | differences from the migration source |
|---|---|---|---|---|
| `running_game_find_nearby_nodes` | `addons/godot_mcp_rs/mcp_runtime_agent.gd:501-546` (`_cmd_find_nearby_nodes` + `_find_nearby_recursive`); the game-process half of `godot_mcp_gdext/src/commands/runtime.rs:413`, which only forwards the arguments over IPC | params `position` (object, **required**), `radius` (number, default `100.0`), `type_filter` (string, default `""`), `group_filter` (string, default `""`), `max_results` (integer, default `50`); tree = `SceneTree::get_current_scene()`, depth-first **pre-order including the root**; a node is kept when `distance(position, node_pos) <= radius` (inclusive) and both filters pass (`and`ed, **no subtree pruning** on a filter miss); `node_pos` = `global_position` if it is a `Vector2`, else `position` if it is a `Vector2`, else `(0,0)`; result `{"nodes":[{name,path,type,distance}...],"count":N}` ascending by `(distance, pre-order index)`, truncated to `max_results`; `max_results <= 0` → `{"nodes":[],"count":0}` (not an error); no `SceneTree` / no current scene → `-32000` + `data.suggestion` | `tools/running_game_read_scene.{h,cpp}`; registered last in `tools/registration.cpp`; `channel="running_game" verb="find" scope=MCPToolScope::GAME mutating=false` | **(1)** a present parameter of the wrong type is `-32602`; the reference coerced (`position: 5` → empty dictionary, `radius: "big"` → a typed-assignment failure). PLAYBOOK §6.2 accepts the stricter rule. **(2)** the reference stops the walk after `max_results` nodes have been *discovered* (`if results.size() >= max_results: return`), i.e. it returns the first N in pre-order, not the N nearest; this implementation collects, sorts, then truncates — which is what the contract's "最大返回结果数" over a distance-sorted list means and what makes the `max_results` evidence verifiable. `max_results <= 0` still returns empty, matching the reference's short-circuit. **(3)** the order is deterministic: the reference's `sort_custom` is unstable, here the key is the total order `(distance, ... (line truncated to 2000 chars)

`description` and `inputSchema` are a byte-exact copy of the entry in `docs/tools_list.renamed.json`,
emitted by `scripts/gen_running_game_schema.py` (re-runnable, diffable) and marked
`// BEGIN generated … // END generated` in the `.cpp`.

### 3.2 component contract (inputSchema, as the live listing reports it)

```json
{"properties":{"group_filter":{"description":"节点组过滤","type":"string"},
               "max_results":{"description":"最大返回结果数","type":"integer"},
               "position":{"additionalProperties":true,"description":"中心位置，如 {\"x\": 0, \"y\": 0}","type":"object"},
               "radius":{"description":"搜索半径","type":"number"},
               "type_filter":{"description":"节点类型过滤","type":"string"}},
 "required":["position"],"type":"object"}
```

Gate 1 compares this (canonicalised) against the contract on both endpoints: `inputSchema=True`.
`accept_m1.ps1` case 12 compares it verbatim on 9889: `running_game_find_nearby_nodes: name_verbatim=True
inputSchema_verbatim=True description_verbatim=True`.

## 4. red / green

### 4.1 RED (`f63a5b8170`, before any implementation existed)

Command: `bin\godot.windows.editor.x86_64.console.exe --headless --test --test-case="[MCPServer]*"`
(raw log `%TEMP%\task009-impl\red-doctest.log`)

```
.\modules/mcp_server/tests/test_mcp_server.h(1149):
TEST CASE:  [MCPServer] the shared registration entry point registers the group

.\modules/mcp_server/tests/test_mcp_server.h(1156): ERROR: CHECK( registry.get_tool_count() == 24 ) is NOT correct!
  values: CHECK( 23 == 24 )

.\modules/mcp_server/tests/test_mcp_server.h(1161): ERROR: CHECK( registry.has_tool("running_game_find_nearby_nodes") ) is NOT correct!
  values: CHECK( false )
...
.\modules/mcp_server/tests/test_mcp_server.h(4466): ERROR: CHECK( no_scene.body.contains("\"code\":-32000") ) is NOT correct!
  values: CHECK( false )
===============================================================================
[doctest] test cases:   96 |   87 passed |  9 failed | 1429 skipped
[doctest] assertions: 1817 | 1764 passed | 53 failed |
[doctest] Status: FAILURE!
```

The nine failing cases are exactly the ones the change is about — no more, no fewer:

```
[MCPServer] the shared registration entry point registers the group
[MCPServer] tools of later batches are not registered
[MCPServer] the project_read_analysis group is registered for both processes
[MCPServer] the project_read_files group is registered for both processes
[MCPServer] the editor_read_scene_inspector group is editor-only
[MCPServer] the project_write_resource_scene tools are registered as mutating both-scope tools
[MCPServer] the editor_write_scene_editor group is editor-only and complete
[MCPServer] the running_game_read_scene group is game-only
[MCPServer] running_game_find_nearby_nodes validates its arguments and needs a running game
```

Every count assertion fails by exactly one (`23 == 24`), and the two new cases fail because the tool does
not exist (`-32601` instead of the expected `-32602`/`-32000`), which is why they are driven through
`MCPJsonRpc::handle(...)` and not only through the registry — a `registry.call_tool` on a missing tool also
answers `-32602`, and would have made a "wrong-type" case pass for the wrong reason.

### 4.2 GREEN (`b4d29f7e52`, §2.1 only)

```
[doctest] test cases:   96 |   96 passed | 0 failed | 1429 skipped     (focused, exit 0)
[doctest] assertions: 1844 | 1844 passed | 0 failed |

[doctest] test cases:   1522 | 1522 passed | 0 failed | 3 skipped     (full, exit 0)
[doctest] assertions: 426125 | 426125 passed | 0 failed |
```

### 4.3 HOIST (`97d35e0971`, §2.2 + §2.3 + §2.4 — no behaviour)

Identical to 4.2, case for case and assertion for assertion:

```
[doctest] test cases:   96 |   96 passed | 0 failed | 1429 skipped     (focused, exit 0)
[doctest] assertions: 1844 | 1844 passed | 0 failed |
[doctest] test cases:   1522 | 1522 passed | 0 failed | 3 skipped     (full, exit 0)
[doctest] assertions: 426125 | 426125 passed | 0 failed |
```

Baseline quoted by the task brief (measured by the decision-maker, *not* by this subagent) was
`94 / 1728` focused and `1520 / 426009` full; the deltas are exactly the two new cases and their 116
assertions.

## 5. gates

Every gate below was run for real; the exit code of each is the process exit code (the `cmd /c` wrapper
carries no trailing `& echo`, so it cannot report a stale `%ERRORLEVEL%`).

### 5.1 gate ① — contract subset, per endpoint (exit 0)

```
powershell -NoProfile -ExecutionPolicy Bypass -File modules\mcp_server\scripts\check_contract_subset.ps1 -Group running_game_read_scene
scope       : editor-only=17 game-only=1 both/shared=23
editor set  : 40 tool(s)
game set    : 24 tool(s)
[PASS] editor_9888_contract_subset
       editor port=9888 tools=40 order=project_get_info > ... > editor_remove_output_log | running_game_find_nearby_nodes: correctly absent on the editor endpoint
[PASS] game_9889_contract_subset
       game port=9889 tools=24 order=project_get_info > ... > running_game_find_nearby_nodes | running_game_find_nearby_nodes: name=True description=True inputSchema=True
[PASS] guard_user_port_9877
       pid_before=36392 pid_after=36392
========================== SUMMARY ==========================
PASS  editor_9888_contract_subset
PASS  game_9889_contract_subset
PASS  guard_user_port_9877
group=running_game_read_scene tools=1 contract=171
implemented_union=40 tools (editor endpoint) / 24 tools (game endpoint)
3/3 checks passed
```

`game-only=1`, verbatim on 9889, hidden on 9888 — the gate's three required properties. The full
tool-name order lists are in `%TEMP%\task009-impl\gate1.log`.

### 5.2 gate ② — three evidence classes + scope (exit 0 each)

`mcp009_running_game_evidence.ps1 -Phase game` → **25/25**; `-Phase scope` → **10/10**; `-Phase count` → **3/3**.
The bodies below are read back from the files `curl.exe -s -o` wrote (never through a pipe).

**success** — `/tmp/mcp009-running-game-evidence/game01_success_radius100.response.json` (632 bytes,
sha256 `449f22ab75aeac7a70a452a674bab2acb58564a44e569bf143ca47a0dfa250e4`):

```json
{"id":1,"jsonrpc":"2.0","result":{"content":[{"text":"{\"count\":6,\"nodes\":[{\"distance\":0.0,\"name\":\"Main\",\"path\":\"/root/Main\",\"type\":\"Node2D\"},{\"distance\":0.0,\"name\":\"Center\",\"path\":\"/root/Main/Center\",\"type\":\"Node2D\"},{\"distance\":0.0,\"name\":\"Sprite\",\"path\":\"/root/Main/Sprite\",\"type\":\"Sprite2D\"},{\"distance\":0.0,\"name\":\"Child3D\",\"path\":\"/root/Main/Sprite/Child3D\",\"type\":\"Node3D\"},{\"distance\":10.0,\"name\":\"Near\",\"path\":\"/root/Main/Near\",\"type\":\"Node2D\"},{\"distance\":90.0,\"name\":\"Far\",\"path\":\"/root/Main/Far\",\"type\":\"Node2D\"}]}","type":"text"}]}}
```

**missing parameter** — `game10_missing_position.response.json` (98 bytes, sha256
`87bc418a75b23ae697ca47402b4c59c44962161d13ecee2ed91b1f2798f8a26a`):

```json
{"error":{"code":-32602,"message":"Missing required parameter: position"},"id":10,"jsonrpc":"2.0"}
```

**bottom-layer failure** — `game16_no_current_scene.response.json` (156 bytes, sha256
`cb63401a21b941f8a1dc3e8027e4f59172e962f14ec7be89f1b7707beca08dfc`):

```json
{"error":{"code":-32000,"data":{"suggestion":"Use editor_open_scene to open a scene first"},"message":"No scene is currently open"},"id":16,"jsonrpc":"2.0"}
```

Full check list of `-Phase game` (all PASS, exit 0):

```
game_success_radius100            count=6 nodes=6 names=[Main,Center,Sprite,Child3D,Near,Far] distances=[0,0,0,0,10,90] ascending=True
game_success_root_included        Main -> path=/root/Main type=Node2D
game_success_out_of_radius_excluded  TooFar (250,0) present in the nodes list: 0
game_group_filter_markers         count=2 names=[Center,Near]
game_type_filter_node3d           count=1 names=[Child3D]
game_filter_does_not_prune_subtree  Child3D was found below a non-matching Sprite2D parent
game_type_filter_node2d           count=5 names=[Main,Center,Sprite,Near,Far]
game_max_results_2_keeps_nearest  count=2 names=[Main,Center]
game_max_results_0_is_an_empty_result / game_max_results_0_is_not_an_error
game_max_results_negative_is_an_empty_result
game_boundary_radius_90_includes_far   count=6 (Far at exactly 90 is included)
game_boundary_radius_89_9_excludes_far count=5 (Far is dropped)
game_missing_position_is_-32602 / game_missing_position_has_no_result
game_scalar_position_is_-32602    "Parameter 'position' must be an object, got float"
game_mistyped_radius_is_-32602    "Parameter 'radius' must be a number, got String"
game_mistyped_position_component_is_-32602  "Parameter 'position.x' must be a number, got String"
game_mistyped_max_results_is_-32602  "Parameter 'max_results' must be an integer, got String"
game_mistyped_group_filter_is_-32602 "Parameter 'group_filter' must be a string, got float"
game_cleared_scene_endpoint_is_really_a_running_game  engine pid=48460 still running
game_no_current_scene_is_-32000 / game_no_current_scene_has_suggestion / game_no_current_scene_has_no_result
guard_user_port_9877              port 9877 pid_before=36392 pid_after=36392
=== phase game: 25/25 checks passed ===
```

**The three evidence classes and what could not be constructed.** The success, missing-parameter and
bottom-layer classes all exist and are quoted above. The reference distinguishes *two* null cases and both
are covered, one on each side of the wire, so nothing is unconstructible here:

* `SceneTree::get_singleton() == nullptr` — **not** constructible as a live endpoint (any process that runs
  an engine has a SceneTree; a process without a scene loop never binds a port). It **is** the case the
  doctest process hits: `gate3.log` contains `ERROR: [MCP] SceneTree never became available; MCP server
  disabled.`, and the new doctest drives the `-32000` + `data.suggestion` refusal through
  `MCPJsonRpc::handle` there.
* `get_current_scene() == nullptr` — constructed on the wire (§8.2) with a *live* game whose current scene
  is cleared; the engine stays up (`pid=48460 still running`) and answers the `-32000` above.

**`-Phase scope` (10/10, exit 0)** — the full two-endpoint comparison is §7.

### 5.3 gate ③ — module doctest (exit 0)

```
bin\godot.windows.editor.x86_64.console.exe --headless --test --test-case="[MCPServer]*"
[doctest] test cases:   96 |   96 passed | 0 failed | 1429 skipped
[doctest] assertions: 1844 | 1844 passed | 0 failed |
[doctest] Status: SUCCESS!
```

### 5.4 gate ④ — full engine regression (exit 0)

```
bin\godot.windows.editor.x86_64.console.exe --headless --test
[doctest] test cases:   1522 | 1522 passed | 0 failed | 3 skipped
[doctest] assertions: 426125 | 426125 passed | 0 failed |
[doctest] Status: SUCCESS!
```

`passed` only grew (94→96 cases, 1520→1522 full), `failed` is 0.

### 5.5 gate ⑤ — `accept_m1.ps1` twice (exit 0 both times)

```
run 1: 22/22 cases passed
run 2: 22/22 cases passed
Compare-Object of the two "PASS  <case>" lists: differences = 0  (22 lines each)
```

```
implemented tools      : 41 / contract 171
process split          : editor endpoint 40 tool(s), game endpoint 24 tool(s), editor-only 17, game-only 1
equality gate coverage : 40 tool(s) compared verbatim on the editor endpoint
PASS  case1_GET_mcp_200
PASS  case2_initialize
PASS  case3_tools_list_fixture          tools=40; game_scope_leaked=[]
PASS  case4_tools_call_project_info
PASS  case5_tools_call_invalid_params
PASS  case6_unknown_method
PASS  case7_parse_error
PASS  case8_concurrent_100
PASS  case9_keep_alive_two_requests
PASS  case10_half_packet
PASS  case11_body_too_large
PASS  case15_connection_reaping
PASS  case16_expect_100_continue
PASS  case17_header_too_large_431
PASS  case18_bare_lf_terminator_400
PASS  case19_invalid_utf8_body_warns
PASS  case20_tools_list_cross_process_restart
PASS  case12_game_process_endpoint        running_game_find_nearby_nodes: name_verbatim=True inputSchema_verbatim=True description_verbatim=True
PASS  case13_game_without_port
PASS  case14_port_occupied
PASS  guard_user_port_9877
PASS  gate_scope_declared
```

### 5.6 gate ⑥ — tool-groups manifest (exit 0)

```
python modules\mcp_server\docs\scripts\check_tool_groups.py
GROUP   running_game_read_scene      channel=running_game mutating=False implemented=True  tools=1
ASSERT  distinct tools in manifest = 41
ASSERT  B1 tools to port        = 41
ASSERT  every B1 tool appears exactly once: PASS (duplicates=0, missing=0, foreign=0)
ASSERT  every name exists in the 171 entry contract: PASS
ASSERT  every group is one channel + one mutating value: PASS
ASSERT  41 == 42 - 1: PASS
TOOL-GROUPS CHECK PASS
```

### 5.7 gate ⑦ — `scripts/build_local.cmd` (exit 0)

```
modules\mcp_server\scripts\build_local.cmd
build_local: exit code = 0
build_local: log = C:\Users\wyl\AppData\Local\Temp\mcp_server_build_local.log

COMMAND: D:\Anaconda\Scripts\scons.exe platform=windows target=editor module_mono_enabled=no tests=yes -j8
scons: Reading SConscript files ...
Building for platform "windows", architecture "x86_64", target "editor".
scons: done building targets.
EXIT_CODE=0
```

The log records the command line (so the `tests=yes` flag is auditable) and the true SCons exit code; the
build output is redirected, never piped. The script's header documents both traps the task brief required:
(i) `env["tests"]` defaults to `False` (`SConstruct:254`), so a build without `tests=yes` aborts with
`--test was specified on the command line, but this Godot binary was compiled without support for unit
tests`; (ii) after editing `tests/test_mcp_server.h` the stale objects
`bin/obj/modules/mcp_server/tests/test_mcp_server.windows.editor.x86_64.obj` and
`bin/obj/tests/test_main.windows.editor.x86_64.obj` must be deleted, because `modules/SCsub:55` pulls the
header in through `CommandNoCache` and SCons therefore has no dependency edge back to it. (The brief named
the objects without the `windows.editor.x86_64` suffix; that suffix is part of the real file names.) This
subagent deleted them by hand before every rebuild that followed a header change, exactly as documented.

## 6. the new group's three evidence classes (summary)

| class | request | response | where |
|---|---|---|---|
| success | `{"position":{"x":0,"y":0},"radius":100}` on 9889 | `count:6`, ascending, `Main/Center/Sprite/Child3D/Near/Far` | `game01` (above) |
| missing parameter | `{}` on 9889 | `-32602 Missing required parameter: position`, no `result` | `game10` (above) |
| bottom-layer failure | `{"position":{"x":0,"y":0}}` on a live game with a cleared current scene | `-32000` + `data.suggestion`, no `result` | `game16` (above) |

Filters, `max_results` (including `0` and a negative value), the inclusive radius boundary and the four
mistyped-parameter refusals are additionally recorded in `%TEMP%\mcp009-running-game-evidence\` (one
`.request.json` + `.response.json` pair per check) and listed in §5.2.

## 7. game-only must be absent from the editor endpoint — first end-to-end evidence

This is the direction that had no real object before TASK-009. Both endpoints were started against the
same scratch project, and **both full tool-name lists** were recorded.

| | editor endpoint 9888 | game endpoint 9889 |
|---|---|---|
| tools served | **40** (41 registered in an editor process, minus the 1 game-only tool) | **24** (23 both-scope + the 1 game-only) |
| `running_game_find_nearby_nodes` | **absent** (0 occurrences) | **present** (1 occurrence) |
| `editor_get_errors` | present | **absent** (0 occurrences) |
| calling the other side's tool | `{"error":{"code":-32601,"message":"Method not found: running_game_find_nearby_nodes"},"id":2,"jsonrpc":"2.0"}` — no `result`, no `nodes` | `{"error":{"code":-32601,"message":"Method not found: editor_get_errors"},"id":4,"jsonrpc":"2.0"}` |

```
editor 9888 (40 tools): project_get_info > ... > editor_remove_output_log
game   9889 (24 tools): project_get_info > ... > running_game_find_nearby_nodes
editor-only tools (present on 9888, absent on 9889): editor_get_errors, editor_get_output_log, editor_get_open_scripts,
  editor_get_scene_tree, editor_get_selection, editor_get_viewport_3d_camera, editor_analyze_signal_flow, editor_open_scene,
  editor_save_scene, editor_reload_plugin, editor_rescan_project_filesystem, editor_set_node_selection,
  editor_remove_node_selection, editor_add_resource_to_node_property, editor_set_viewport_3d_camera,
  editor_capture_screenshot, editor_remove_output_log
game-only tools   (present on 9889, absent on 9888): running_game_find_nearby_nodes
[PASS] scope_the_editor_game_split_is_exactly_the_scopes :: editor-only=17 game-only=1
```

Measured detail the brief predicted differently: the brief expected **41** tools on the editor endpoint.
The wire says **40**: `ToolBuilder::register_into` skips only `scope = EDITOR` tools in a game process, so
an editor process does *carry* the game-only tool in its registry (41 entries, `status.tools` would still
report 40 visible), but `MCPToolRegistry::build_tools_list`/`is_tool_visible` filter it out, so it is never
served. `41` is the editor process's registered table; `40` is what `tools/list` returns. Both numbers are
reported rather than one being called "the" count.

## 8. B1 closure (41/41) and the equivalence proof

### 8.1 B1 closure count — machine-checked

`-Phase count` (logs: `%TEMP%\task009-impl\gate2-count.log`) prints the checker's full output plus its own
per-group arithmetic:

```
project_read_template          project      implemented tools=6
project_read_analysis          project      implemented tools=7
project_read_files             project      implemented tools=6
project_write_resource_scene   project      implemented tools=4
editor_read_scene_inspector    editor       implemented tools=7
editor_write_scene_editor      editor       implemented tools=10
running_game_read_scene        running_game implemented tools=1
[PASS] count_b1_closure_41_distinct :: implemented=true groups = 7; distinct tools = 41; duplicated = 0; B1 closure = 41/41
[PASS] count_running_game_read_scene_contributes_one :: group running_game_read_scene: implemented=True tools=1 [running_game_find_nearby_nodes]
[PASS] count_check_tool_groups_exit_zero :: python .../check_tool_groups.py exit=0
=== phase count: 3/3 checks passed ===
```

6+7+6+4+7+10+1 = 41 distinct tools, no duplicates, and the checker independently re-derives 41 from
`DESIGN-DETAIL.md` §10 minus the GDR-17 merge (`ASSERT 41 == 42 - 1: PASS`).

### 8.2 the §2.2 hoist, proven on the wire

Decision-maker's capture procedure (`%TEMP%\task009\capture_wire.ps1`), 38 manifest lines: 1 status probe,
22 editor requests, 1 status probe, 13 game requests, 1 port guard. Response bodies are written by
`curl.exe -s -o` (or `-w '%{http_code}'`), never through a pipe.

```
before : C:\Users\wyl\AppData\Local\Temp\task009\wire-before\manifest.txt
         sha256 0660ecc2fbc22354550eefe5f5357b1617482139d72ecc2f887d8ec59f165d42  (7787 bytes, 38 lines)
after  : C:\Users\wyl\AppData\Local\Temp\task009\wire-after\manifest.txt
         sha256 976349121b825978a3808b5997d65cfcf8c5931c2addf57ab0466f1b091b9634  (7787 bytes, 38 lines)
identical lines: 35 of 38
```

The three differing lines, complete:

```
BEFORE g01_tools_list|port=9889|...|resp_sha256=b5022e9a8e309dabae70bcbc9de0aaf793f44740adc5213ba4b093000f284569|resp_bytes=6697
AFTER  g01_tools_list|port=9889|...|resp_sha256=a0daaf8c0afe1c499e587be6d1577bc8f7b9e907b5a8b6d4a8e3d307a84f8971|resp_bytes=7256
BEFORE status_9888|resp_sha256=7cde9d0c05f18b92aef716704fb45f8f9dde535a16554ce054458f94c61e5369
AFTER  status_9888|resp_sha256=dddc7e8e2e9b24813f3b637c7b98d76ddb3839e28bbe318b506882d309d0e226
BEFORE status_9889|resp_sha256=6224d02b738e2de0444f3c0f2ed3855b8836d3f7ed5863c24862a1b7c23c359f
AFTER  status_9889|resp_sha256=ef5615145ecf04c4d2b8eb337e7ce2cc307c647cadc5a441f527108ec0dbe93a
```

Every one of the **35 request/response pairs is byte-identical**, including all six writing-tool calls
whose property helpers moved (`e08_create_resource`, `e09_edit_resource`, `e10`, `e11`, `g08`, `g09`,
`g12`), the editor guard's 13 call sites' two observable tools (`e12`/`e13`/`e17`) and
`e21_game_only_refused`. The three differing lines are explained, not waved away:

* `g01_tools_list` 6697 → 7256 bytes — **new functionality**: the game endpoint serves 23 tools before and
  24 after (the new group). Expected; the only `tools/list` that changes.
* `status_9889` — `"tools":23` → `"tools":24` (same new functionality) **plus** `frame_count`, a free-running
  per-process counter.
* `status_9888` — `"tools":40` **unchanged**; the only difference is `frame_count` (1204 vs 1220), a
  per-run counter with no behavioural meaning.

So the hoist itself changed **nothing** that any request can observe; the four `.cpp` bodies are not just
"equivalent by reasoning" but byte-equivalent on the wire.

Note on the brief's expectation: it predicted that both `e01` and `g01` would differ. Measured, `e01`
(the **editor** endpoint's `tools/list`) is byte-identical — its only difference from before is nothing at
all, because the new tool is game-only and therefore hidden there:
`e01_tools_list.resp.json` sha256 `db1ceacafb680b95d7137d07b968e01fb15c6143d469c275d58246696807035c`
in both captures. Only `g01` differs.

### 8.3 one definition per hoisted helper (the negative proof)

The brief asks for `rg -n "require_editor_ui|property_value_from_json|coerce_to_property_type|property_type_of" modules/mcp_server/tools`.
`rg` is **not installed** on this machine (`Get-Command rg` → not found), so the equivalent search was run
with the session's ripgrep-backed search tool over the same directory. Result: 39 matches, of which every
*definition* is in `tools/tool_helpers.{h,cpp}` and every other match is a call site or a comment. No
`_`-prefixed local copy survives.

```
tool_helpers.h   166: bool require_editor_ui(MCPToolError &r_error, const String &p_what, const String &p_hint);
tool_helpers.h   188: Variant property_value_from_json(const Variant &p_value, Variant::Type p_target_type);
tool_helpers.h   198: bool coerce_to_property_type(...);
tool_helpers.h   209: Variant::Type property_type_of(const Object *p_object, const StringName &p_name);
tool_helpers.cpp 308: bool require_editor_ui(...)                       <- definition
tool_helpers.cpp 334: Variant property_value_from_json(...)             <- definition
tool_helpers.cpp 396: bool coerce_to_property_type(...)                 <- definition
tool_helpers.cpp 413: Variant::Type property_type_of(...)               <- definition

editor_read_scene_inspector.cpp  217/315/376: if (!require_editor_ui(r_error, "editor inspectors outside a running editor", ...))
editor_write_scene_editor.cpp    226/304/373/433/521/590/673/754/858/953: if (!require_editor_ui(r_error, "editor writes outside a running editor", ...))
editor_write_scene_editor.cpp    704: property_type_of(resource_ref.ptr(), key)
editor_write_scene_editor.cpp    706: coerce_to_property_type(property_value_from_json(...), ..., "resource_properties")
project_write_resource_scene.cpp 228/461: property_type_of(resource, key)
project_write_resource_scene.cpp 230/463: coerce_to_property_type(property_value_from_json(...), ..., "properties")
```

13 guard call sites (3 + 10) plus the three property helpers, one definition each.

## 9. decisions (the four the brief prescribed, plus where the code had to deviate)

D1 — **the group's shape.** One tool, its own one-tool group `running_game_read_scene`, `scope=GAME`,
registered last, matching the channel rule (a group is one channel) and the manifest order. The group is
the first and only game-scope group of B1, which is why the editor-absent direction becomes observable now.

D2 — **which tree.** `SceneTree::get_current_scene()`, the running game's scene, never the edited scene —
that is the reference's `get_tree().current_scene` and the only tree that exists in a game process. Both
null paths (`get_singleton() == nullptr`, `get_current_scene() == nullptr`) are `-32000`, never a
dereference.

D3 — **deterministic ordering.** The reference's `sort_custom` is unstable; the contract says nothing about
tie order, but PLAYBOOK §6.8 requires reproducibility, so the key is the total order
`(distance, pre-order discovery index)`. The reference's "stop after `max_results` discoveries" is also
replaced by "collect, sort, truncate" so that `max_results=k` really means the k nearest (see §3.1).

D4 — **the hoist as a two-file, one-definition refactor.** The editor guard keeps two parameterised
messages (so both groups keep their own wording); the property helpers hoist the *superset* with the
caller's parameter name passed in, so every wire string is preserved. Proven by §8.2.

Deviations from the task brief / the design brief, stated explicitly (nothing was changed silently):

1. **`accept_m1.ps1` needed more than the one added line** the brief prescribed. Adding
   `running_game_find_nearby_nodes` to `$ToolNames` makes that array the union of all 41 implemented tools,
   but `case1_GET_mcp_200`, `case3_tools_list_fixture` (through `Compare-ToolListToFixture`'s default) and
   `case20_tools_list_cross_process_restart` compare the **editor** endpoint against it. A derived
   `$EditorToolNames` (the union minus `scope = game`) was added next to the existing
   `$EditorOnlyToolNames`/`$GameToolNames`, the three editor-side comparisons now use it, and case 3 also
   asserts `game_scope_leaked=[]` — the mirror of case 12's editor-scope leak check. Without this, gate ⑤
   fails on the editor count (40 vs 41) even though the server is correct. Two summary lines were adjusted
   to print both endpoints' counts.
2. **`check_contract_subset.ps1` had the same latent assumption.** It passed `$implementedTools` (all 41) as
   the editor endpoint's expectation, which was only ever correct while no game-only tool existed. It now
   derives `$editorTools` (implemented minus game-only) and asserts the game-only set is hidden there — which
   is exactly what gate ①'s "`MUST be hidden`" requirement needs. Only the scope block and one summary line
   changed; the 41-tool invariant is untouched.
3. **The bottom-layer project is not the one the brief described.** A project with `run/main_scene` absent
   is not usable: Godot binds 9889, then `Main::start()` fails to load a main scene and the process exits
   (measured: the endpoint accepts one connection and the engine is gone). The evidence therefore uses a
   *live* game whose `_ready()` sets `get_tree().current_scene = null` — the same null `get_current_scene()`
   the tool must refuse, but with a process that stays up to answer the request. Both the old attempt and its
   measurement are recorded in §5.2.
4. **`SceneTree::get_singleton() == nullptr` is not constructible on the wire**; it is covered by the doctest
   process instead (which logs `SceneTree never became available`) — §5.2.
5. **The editor/writer guard's non-editor `data.suggestion` string changes** for the 13 call sites: the brief
   parameterises a *single* hint per group, so the writers' non-editor branch now says
   `"Start the MCP server inside the Godot editor to write editor state"` instead of
   `"Run the MCP server inside the Godot editor: the editor_* tools are editor-only"` (and the inspectors'
   analogously). The brief's table claims the resulting strings are identical for every call site; they are
   identical for the editor branch (the reachable one) but not for the non-editor branch. That branch is
   **unreachable on the wire** for these tools — they are `scope = EDITOR`, so a non-editor process never
   registers them (it answers `-32601` instead) — which is also why the byte-equivalence proof of §8.2 cannot
   cover it. The doctest only asserts that a suggestion exists, so nothing regressed; the old wording is
   recorded here rather than silently dropped.
6. **`gen_running_game_schema.py` was added to the repository** so the byte-exact contract copy can be
   regenerated and diffed instead of trusted; the brief only required that a script be used to produce it.
   It is not a specification document (PLAYBOOK §7.2 is untouched).
7. **`project_write_resource_scene.cpp`** also lost the now-unused `core/variant/variant_utility.h` include
   (the only user of `VariantUtilityFunctions` moved to `tool_helpers.cpp`), and its two call sites hoist
   the `target_type` local instead of looking the type up twice — the same no-op the brief required at the
   `editor_write_scene_editor.cpp` site, where the lookup was already a single local. §8.2 confirms both are
   byte-neutral.
8. **`rg` is not installed on this machine**; the one-definition proof used the session's ripgrep-backed
   search instead (§8.3).
9. **Correction (independent verification round 1): the hoisted `property_value_from_json` `FLOAT` → `INT`
   fold was UB for an out-of-range finite double.** The kept editor-copy guard tested
   `Math::is_finite(number) && (double)(int64_t)number == number`, i.e. it converted *before* checking range;
   for a finite double outside the `int64` range the cast is undefined behaviour in C++ (x86-64/MSVC happens to
   yield `INT64_MIN`, so the test failed and the double was returned — incidentally correct, but unguaranteed).
   The hoist carried this over from the editor copy while the `project_write_resource_scene.cpp` copy it was
   merged with had range-checked first. It now uses that range test
   (`number >= -9.0e15 && number <= 9.0e15`) before the single `truncated` cast, so every value in
   `-9.0e15 .. 9.0e15` is folded exactly as before and no cast is formed outside it. The guard is
   *stricter* than the expression it replaced, not merely a definitional rewrite of it: for
   `9.0e15 < |x| <= ~9.22e18` the old `(double)(int64_t)number == number` test was itself true, so the
   old code would sometimes have folded such a finite double to an integer where the new code refuses
   the fold and returns the double. **That is a wording defect in this round-1 correction, not a
   behaviour change**: the converted property value is nevertheless the same, because
   `coerce_to_property_type` then converts the returned double back for an `INT`-typed target —
   measured end to end on the wire, `background_mode 1e16 -> 1874919424`, the same stored value either
   way. The wire comparison of §8.2/round-2 capture is unchanged (Fix 2 changed no response). Verifier
   **risk 3** is closed by fix 2 of round 1; the *description* of the new guard is corrected here.

## 10. sha256 of every file changed

```
9d9bae8f80b283de4af86ad019d60517c9e2c58a36a1624f7d0b2488f28a5cea  194665  modules/mcp_server/tests/test_mcp_server.h
0cfcac80f0d999fa7db713ae48f43febe96ae52e2c93633257eeed00ffdfbfac    5682  modules/mcp_server/docs/tool-groups.json
a1abac1ced6652490b5a5e4847e8c46fb4f7b1536b7540c62283946b70d34266   60382  modules/mcp_server/scripts/accept_m1.ps1
5ddad88daba158eadecc7455e252077b7db0532a73027fe785998dd6aa2509e9   23784  modules/mcp_server/scripts/check_contract_subset.ps1
8bdfb1bbeb89348c0c74b9fe74b9286a568ac3ebcc37fadac0030d2a967ceaa0    3890  modules/mcp_server/scripts/gen_running_game_schema.py
742ae4fa4e4aea0438081e31f6a332b42c2048bbf4c409872642c9cefa01dbc2    2983  modules/mcp_server/scripts/build_local.cmd
172b5190b7f48990e58425b542e8dee498d4d569eb1c555e78f9afac615f88a6   34664  modules/mcp_server/scripts/mcp009_running_game_evidence.ps1
2b7a64ab27047897791e81eae1662cf3a98ed6d8fd2680da6c92e976af9f292b    3501  modules/mcp_server/tools/running_game_read_scene.h
7f71db88309e2c3e2937e31d9ae5143735427e83033757840c52c50925b1f897   15138  modules/mcp_server/tools/running_game_read_scene.cpp
97f2422380a71a0bdc6a69aa78336039e9f50b03e9a293584b05391f0b26c497    3248  modules/mcp_server/tools/registration.cpp
83a046037cc0a10e69021b812ebc8d329556e5f06abe03d914d2963f8a88466a   12579  modules/mcp_server/tools/tool_helpers.h
b4ecf53f04173da733861a40d3367da32ef9c35d7ef7a42bc917d6eadde7d8ae   15225  modules/mcp_server/tools/tool_helpers.cpp
dc7af3a8fcaccaec6e0290b7bbe8398ade85f69cdb98468ce21614147ea60a8d   27699  modules/mcp_server/tools/editor_read_scene_inspector.cpp
a41acac2605b64b174d73ed696791a041bf6f024873762fed4dd30aead7dd670   46353  modules/mcp_server/tools/editor_write_scene_editor.cpp
d48770f51c391ffce4047a4bba6c111a4687c4858be865696c669ec668d0b026   24693  modules/mcp_server/tools/project_write_resource_scene.cpp
```

The contract (`docs/tools_list.renamed.json`), the rename map (`docs/tool-rename-map.json`) and the doc
generators were **not** modified. `docs/tool-groups.json` changed only by setting
`running_game_read_scene.implemented` to `true`.

## 11. deviations / blockers / next_step_recommendation

**deviations** — all listed in §9: (1) `accept_m1.ps1` needed a derived editor-side list, not the single
line the brief described; (2) `check_contract_subset.ps1` carried the same latent whole-union assumption and
was corrected; (3) the brief's `run/main_scene`-absent bottom-layer project is not viable (the engine exits),
so a cleared-current-scene project is used; (4) the null-`SceneTree` branch is doctest-only; (5) the guard's
non-editor `data.suggestion` wording changes for the 13 call sites and is unreachable on the wire; (6) a
generator script was added to the repository; (7) `project_write` lost an unused include and hoists its
`target_type` local; (8) `rg` was unavailable, an equivalent search was used. Additionally, the brief's
expected numbers for the evidence scene (`count == 4`, "the four Node2Ds", 41 tools on the editor endpoint,
`e01` differing) did not survive contact with the real tree and are reported as measured: 6 / 5 / 40 /
`e01` identical.

**blockers** — none.

**next_step_recommendation**
1. `MCPToolError::no_scene()` is editor-worded (`"Use editor_open_scene to open a scene first"`), which is
   what a *game* tool now returns (see `game16`). The brief prescribed the factory, so it was used verbatim;
   a game-specific message is a contract decision (GDR-14 wording), not an implementation one — take it up
   with the decision-maker/contract rather than patching it here.
2. `--import` runs as an editor process and therefore tries to bind the **default editor port 9877**. It only
   ever fails (the user's editor owns it), and no gate is affected, but any future evidence script that runs
   `--import` while 9877 is free would quietly take the user's port. Worth an explicit `--mcp-port` (or a
   "do not listen" flag) inside `build_local`/the evidence scripts, or a module-level guard. **Reproduced by
   the independent verifier** (defect 2): every `--import` run logs
   `WARNING: [MCP] bind failed on 127.0.0.1:9877; MCP server disabled` (and `[MCP] bind failed on
   127.0.0.1:9877 (error=22)`), and 9877 stayed on pid 36392 — nothing was disturbed, but the bind is
   attempted. Verifier report:
   `C:\Users\wyl\AppData\Local\Temp\task009\verify\VERIFY-009-INDEPENDENT.md`.
3. `accept_m1.ps1` case 1/case 3/case 20 now depend on `$EditorToolNames`; the next game-only group should
   extend `$GameToolNames` only, and this is documented in the script's comment block.
4. `bin\godot.windows.editor.x86_64.console.exe` is a ~300 KB shim; the code under test is
   `bin\godot.windows.editor.x86_64.exe`. Any future report should record both hashes (as §0 does here) so
   "the binary I tested" is unambiguous.

## 12. independent verification round 1

A fresh, read-only verifier re-measured TASK-009 at `9cb594be4f` and returned verdict **pass**: all five
claims reproduced with its own measurements, every gate exit 0 and matching this report, and the
96/1844 + 1522/426125 doctest numbers re-measured. Report:
`C:\Users\wyl\AppData\Local\Temp\task009\verify\VERIFY-009-INDEPENDENT.md`.

**Where this report and the verifier disagree, the verifier's findings win** — specifically the claim
that the `(0,0)` measurement of a `Node3D` is "the reference's own fallback (`Vector2.ZERO`) made explicit
instead of a silent type error" (now corrected in the code comment and in §3.1 (4) — round 2 later showed
that round-1 correction was itself wrong; see §12.4) and the understated `FLOAT`→`INT` cast (now corrected
in §9 (9)).

**Two low-severity defects** (neither changes the tool's observable contract):

1. inaccurate migration-source justification for the `Vector3` rule — the reference aborts loudly, it does
   not fall back; round 1 rewrote the comment and §3.1 (4) but the rewrite **still overstated**: it
   claimed the error aborts the whole recursion, which the round-2 verifier measured to be false.
   Defect 1 is therefore closed **only by the round-2 correction round** (`cd5f53c221`), not by round 1
   (see §12.4);
2. `--import` attempts to bind `127.0.0.1:9877` (`source=default`), failing only because the user's editor
   holds the port; **not addressed** by this fix round (pre-existing, outside the three prescribed fixes).

**Eight residual risks** recorded by the verifier, one line each:

1. the 34 shared wire pairs exercise the property helpers only with a bool-valued property and an empty
   `properties` dict, so the `INT`/`FLOAT`, `#rrggbb`, `Vector2(...)`, Dictionary/Array recursion and
   non-finite-number branches are not covered by the capture; **still open** (the `FLOAT` logic is now at
   least defined, but still not wire-covered);
2. `property_type_of`'s current-value→declared-type merge is only observable for a `nil` current value and no
   captured request does that, so it is neither proven nor disproven; **still open**;
3. the `FLOAT`→`INT` guard cast an out-of-range double before range-checking (UB, no observed difference on
   x86-64/MSVC); **addressed by this fix round** — see §9 (9);
4. `require_editor_ui`'s non-editor branch returns the group's editor-UI suggestion instead of the old shared
   string — unreachable on the wire (`scope=EDITOR` answers `-32601` in a game process) and unasserted, so
   neither the capture nor the suite covers it; **still open** (disclosed as §9 (5));
5. the before-capture predates the group-port commit (23 game tools), so the before/after comparison spans
   four commits and the hoist-specific isolation rests on the source diff, not on the wire; **still open**;
6. "nothing was pushed" is not verifiable in the verifier's sandbox (no upstream, no remote-tracking ref for
   the branch); **still open**, not falsifiable from here either;
7. `MCPToolError::no_scene()` returns the *editor*-worded suggestion from a game-only tool where
   `editor_open_scene` is not served at all; the wording is already escalated as a contract decision (§11
   next-step 1); **still open**;
8. the reference's `Vector3` failure cannot be observed through the reference's own wire (it aborts without
   answering), so the reference side of defect 1 rests on a GDScript replication of lines 535-539 rather than
   the addon actually running; **still open** (inherent).

This fix round (round 1) therefore closes **risk 3** — the `FLOAT`→`INT` guard, see §9 (9), which the
round-2 correction below restates more precisely. **It did *not* close defect 1**: round 1 replaced one
false claim about the reference's `Vector3` error with a different false claim, and defect 1 is closed
only by the round-2 correction round (`cd5f53c221`; see §12.4). Defect 2 and
risks 1, 2, 4, 5, 6, 7 and 8 remain open and are handed back to the decision-maker.

### 12.1 the wire comparison of this fix round — earlier narrative retracted and re-measured

**Retraction (PLAYBOOK §7.3).** The previous version of this subsection asserted that `capture_wire.ps1`
leaves stale `tmp\` scratch state behind, that a naive `wire-before` vs `wire-afterfix` diff therefore
shows **11** differing lines, and that its own first row was `frame_count 1224 vs 1222`. Independent
verification round 2 and this correction round re-derived everything from the surviving captures, and
**that narrative could not be reproduced from them**. It is withdrawn explicitly here, not deleted:

* the committed `wire-before` capture is **not stale**: its `e08_create_resource` response is
  byte-identical to the final capture's (`755ae7bb2bc215b5…` — a success, not an "already exists"
  refusal) and to that response in every other surviving capture (`wire-beforefresh`, `wire-after`,
  `wire-afterfix`, `wire-afterfix-fresh`, `wire-afterfinal`);
* `wire-before` vs `wire-afterfix` differs in **3** ids — `g01_tools_list`, `status_9888`, `status_9889`
  — not 11;
* the pair `1224 vs 1222` matches no surviving capture. The `status_9888` `frame_count` values on record
  are `1204` (`wire-before`), `1161` (`wire-beforefresh`), `1220` (`wire-after`), `1244`
  (`wire-afterfix`), `1222` (`wire-afterfix-fresh`) and `1160` (`wire-afterfinal`).

What **is** reproducible — re-measured here from the raw files rather than repaired from the old numbers
— is the structural conclusion this fix round needs, with the pre-round-1 binary (`wire-beforefresh`,
pristine) against the post-round-1 binary (`wire-afterfix`, pristine):

| comparison | identical | differing ids |
|---|---|---|
| `wire-beforefresh` vs `wire-afterfix` | **37 of 38 lines** | `status_9888` only (`frame_count` 1161 vs 1244, volatile) |
| `wire-before` vs `wire-afterfix` | 35 of 38 lines | `g01_tools_list` (23 → 24 tools, a TASK-009 change) and `status_9888`/`status_9889` (`frame_count`) |

**Fix 2 changed no response.** `g01_tools_list` is byte-identical between the two captures (sha256
`a0daaf8c0afe1c499e587be6d1577bc8f7b9e907b5a8b6d4a8e3d307a84f8971`, 7256 bytes in both); the only
changed line is the `/mcp` status snapshot, whose only differing field is the volatile `frame_count`
(`tools` stays 40 on 9888 and 24 on 9889). **No baseline was adjusted, and the fix was not tuned to a
baseline.**

Recommendation (for the decision-maker; not applied here, as it is outside the prescribed fixes): make
`capture_wire.ps1` delete `tmp\` under both scratch projects before it starts, or stamp the scratch state
into the manifest, so a repeated capture cannot silently compare unequal states. The decision-maker did
adopt this for the out-of-repository harness copy (§12.2); nothing in §12.2 depends on the retracted
numbers above.

### 12.2 the canonical equivalence proof (decision-maker, after the fix; scratch state now reset)

The decision-maker applied the recommendation above to the *capture harness only* (a copy outside the
repository, `%TEMP%\task009\capture_wire.ps1`, now deletes `tmp\` under both scratch projects before it
imports them), re-ran the capture against the final binary, and re-derived the comparison from the raw
files. This is the canonical statement of the §2.2 proof; §12.1's retracted rows are the history of how it
was established, and §12.1's re-measured table reaches the same conclusion from the pre/post-round-1
binaries.

```
before : C:\Users\wyl\AppData\Local\Temp\task009\wire-before\manifest.txt
         sha256 0660ecc2fbc22354550eefe5f5357b1617482139d72ecc2f887d8ec59f165d42  (38 lines, pre-TASK-009 binary)
after  : C:\Users\wyl\AppData\Local\Temp\task009\wire-afterfinal\manifest.txt
         sha256 aac2efc8cf67cd3bada311c0e3bc0595062d3df3c163ce343cb2b1b21583be0f  (38 lines, final binary)
identical lines: 35 of 38
differing ids  : g01_tools_list, status_9888, status_9889
```

Every difference is accounted for and none of them is an effect of the hoist or of the fix round:

| id | before → after | field that differs | why |
|---|---|---|---|
| `g01_tools_list` | 6697 → 7256 bytes, sha256 `b5022e9a…` → `a0daaf8c…` | the game listing | **new functionality**: 23 → 24 tools, the new group's tool |
| `status_9888` | sha256 `7cde9d0c…` → `4459277b…` | `frame_count` 1204 → 1160 only | a free-running per-process frame counter; `tools` stays **40** |
| `status_9889` | sha256 `6224d02b…` → `b3d6168a…` | `frame_count` 1211 → 1212, `tools` 23 → 24 | new functionality (24) plus the same volatile counter |

The raw response files agree field by field — these were recomputed with `Get-FileHash` on both
captures, not read from the manifest:

```
e08_create_resource                        755ae7bb2bc215b5 755ae7bb2bc215b5 True
e09_edit_resource                          3ab8bb30d83ec63b 3ab8bb30d83ec63b True
e11_create_scene_file                      b807135b374cbec7 b807135b374cbec7 True
e12_editor_get_scene_tree                  b2b56ed34a15a5f1 b2b56ed34a15a5f1 True
e17_editor_set_node_selection_no_scene     b2b56ed34a15a5f1 b2b56ed34a15a5f1 True
e21_game_only_refused                      78d2da5a09b79bcf 78d2da5a09b79bcf True
g08_create_resource                        755ae7bb2bc215b5 755ae7bb2bc215b5 True
g09_edit_resource                          3ab8bb30d83ec63b 3ab8bb30d83ec63b True
g12_project_create_scene_file              b807135b374cbec7 b807135b374cbec7 True
e01_tools_list before/after identical = True
```

So: **of the 35 shared request ids, 34 request/response pairs are byte-identical — `g01_tools_list` is
the exception, because the game endpoint gained the one tool this task ported (6697 → 7256 bytes) — the
editor endpoint's whole `tools/list` is byte-identical, and the only other changed lines are the volatile
`frame_count` fields in the two `/mcp` status snapshots.** The hoist of §2.2 and the fix round of §12
therefore changed nothing any request can observe. Port discipline held in this run too:
`pid_before == pid_after == 36392` on 9877.

### 12.3 findings from verification round 2 that this round does not fix

Verification round 2 (fresh verifier, code at `54a21edb3a`) found, besides the false *claims* this round
corrects above, three medium findings that lie **outside this correction's scope**. They are recorded here
*as findings for the decision-maker*, not as work items: no code is changed for them in this round.

1. **`tool_builder.cpp:162-177` — `_integral_value` casts a double to `int64` with no finiteness/range
   guard.** This helper is exactly what `require_int` (line 193) and `optional_int` (line 220) use, and it
   does `const int64_t truncated = (int64_t)number;` on an unchecked `double` — the same UB class round 1
   removed from `tool_helpers.cpp`. It is **pre-existing** (`tool_builder.cpp` is not in TASK-009's change
### 12.4 round-2 verification note — which claims were false, and where defect 1 closes

Verification round 2 re-measured TASK-009 at `54a21edb3a`: the code and every gate pass, but **three
written claims were false** — the `Node3D`/`Vector3` comment and §3.1 (4) said the reference's error
"aborts the whole recursion" (measured: it aborts only the raising node's own frame and subtree, and the
rest of the tree is still answered); §9 (9) said an out-of-range finite double "still returns the
double … the same value as before" (imprecise for `9.0e15 < |x| <= ~9.22e18`); and §12 said defect 1 was
closed by round 1, which it was not. §12.1's "11 differing lines / stale scratch state" narrative was also
shown not to be reproducible and is retracted in place, and §12.2's "35 shared request/response pairs are
byte-identical" is corrected to 35 shared request ids / 34 byte-identical pairs. This correction round
fixes exactly those claims and nothing else — comment and report text only, no behaviour change.

**Defect 1 is closed by this round's commit `cd5f53c221`**, subject
`mcp_server: TASK-009 - correct the Vector3/Vector2 claim and retract REPORT-009 12.1 (verification round 2)`:
the rewritten comment in `tools/running_game_read_scene.cpp` and §3.1 (4) now state the measured
behaviour — the reference's error aborts only the raising node's own frame and subtree, the rest of the
tree is still answered, and this implementation deliberately diverges by measuring the `Node3D` at `(0,0)`
and including it.

### 12.5 verification round 3 — verdict and the one residual wording defect

A third fresh verifier re-measured the corrected state at `bd633b936b` and returned verdict **pass** for
all four items it was charged with: the rewritten `Node3D`/`Vector3` comment is true (it re-derived the
GDScript probe itself: `N3` raises, `Z` is still visited, answer `[Root, A, Z]`) and the commit is
comment-only (31 changed lines, 0 non-comment); §12.1's retraction and every number in §12.1/§12.2/§9 (9)
reproduce; §12.3's three out-of-scope findings are accurate at the cited lines and wire-reachable; and
all five gates pass with the stated counts while the change set stays inside `modules/mcp_server/**`.

It also found one **low-severity wording defect**, which this section answers: §12.2's closing sentence
lumped the two `/mcp` status snapshots together as "the volatile `frame_count` fields", but
`status_9889` also differs in `tools 23 → 24` (the new tool, counted a second time) — only
`status_9888`'s difference is `frame_count`-only. The sentence is corrected in place. That one-clause
report edit was made directly by the decision-maker rather than through another delegation round,
because it is text-only, changes no artifact under test, and re-opening the (expensive) delegation
channel for a single clause is disproportionate; every measurement it cites was independently
re-verified by rounds 1–3.

Standing verification status: **round 1 pass, round 2 fail (claims), round 3 pass.** The remaining
open items are the round-1 residual risks (still listed in §12) and the round-2 findings recorded
unfixed in §12.3; none of them changes the tool's observable contract, and all are handed back to the
decision-maker.

### 12.6 the final artifact and how it relates to the verified binaries

`running_game_read_scene.cpp` changed once more after the binary described in §0 — comment only, in
`cd5f53c221`, plus the report-only edits of `bd633b936b` and the decision-maker's `49e52afaf4` — so the
binary under test was rebuilt once at `54a21edb3a` (the commit whose only module-file change is that
comment, relative to the round-1 binary). Final artifact:

```
bin\godot.windows.editor.x86_64.console.exe  sha256 0f7c0752a9e87df7861f6f07f3dd84bf8e618932fef0fee02a3e3a6a925294d5
bin\godot.windows.editor.x86_64.exe          sha256 0cc74887e4e77e490317939744ab7c3bea24c5df331ce07f03ed1bad17820a9a
version 4.8.dev.custom_build.54a21edb3
[MCPServer]* : 96 cases / 1844 assertions / 0 failed   (re-run on this artifact by the decision-maker)
```

The binary each verification round reports (§0's `97d35e0` build for round 1, and this one for
round 3) therefore differs only by a comment: **the executable behaviour is the same artifact line**,
and the focused suite reports the same `96 / 1844 / 0 failed` on both. This is stated explicitly
because the two sha256 pairs differ and a reader must not conclude that round 3 verified a different
engine.