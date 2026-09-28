# TASK-DR47-SMOKE-REPORT — 批次二：真机 T=1 冒烟（我们的 MCP 原生构建）

- 执行者：批次二执行子代理（无上游对话上下文）。
- 权威依据：`TASK-DR47-SMOKE.md`（§1–§7）、`TASK-DR47-SMOKE-ADDENDUM.md`（**优先**，取代 §2 第 3 点）、
  `DESIGN-DETAIL.md` §13（DR-43/DR-47）、`REQUIREMENTS.md` §3/§6、`DECISIONS.md` D216–D219。
- 落点：`F:\moonbit-hof-rs`（外层仓 `master`）。本报告写入前 `git status --porcelain` 为空（未 commit / 未 push / 未 stage）。
- 时间（本地 UTC+8）：2026-09-29 00:40:45 启动冒烟 → 02:32 前后结束；随后做端点集合核对。
- **总评（先说结论）**：一轮真实 T=1 循环**跑通并留下可复核证据**；活体契约准入门（D219 修正判据）**通过**；
  但 `artifact_gate.launchable=false`（exit 6），且**游戏端点注册成功后又挂死/消失**，导致 E1/E2/E3 **not_met**。
  E4/E5/E6 **met**。发现 **6 条缺陷**（2 条 major 级影响判据）。**E3 明确 not_met，未粉饰。**

---

## 1. 前置核对（§1 四项）——原始输出

工具：`Get-NetTCPConnection` / `Get-Process`（pwsh）、`curl.exe`、`cmd /c "<binary> --version"`。
**未杀死、未重启、未抢占**编辑器；除 `<binary> --version`（§1.3 明文要求）外未启动任何 Godot 进程。

### 1.1 `GET http://127.0.0.1:9877/mcp`（要求 200 且 `is_editor == true`）

```
STATUS=200
{"connections":1,"frame_count":9453,"is_editor":true,"listening":true,"pending":0,"pending_connections":0,
 "port":9877,"server":"godot-mcp-rs","status":"ok","tools":154,"transport":"streamable-http"}
```

⇒ **符合**。`tools` = **154**（D219 已裁定 154 ≠ 177 不是缺陷；本节 §9 给出集合级复核）。

### 1.2 9877 监听者 PID 的可执行体路径（要求 == 配置的 mono 二进制）

```
LocalAddress : 127.0.0.1
LocalPort    : 9877
State        : Listen
OwningProcess: 108432

Id          : 108432
ProcessName : godot.windows.editor.x86_64.mono
Path        : F:\moonbit-hof-rs\godot-mcp\godot\bin\godot.windows.editor.x86_64.mono.exe
```

⇒ **符合**：PID **108432**，路径与 `config/hoh.yaml:43` 的 `adapter.godot.editor_binary` **逐字一致**（大小写、分隔符差 `F:/` vs `F:\`，属同一路径）。
该 PID 在冒烟全程存活到本报告写成（见 §6 守护项）。

### 1.3 `<binary> --version`（要求以 `4.8.dev.mono` 开头）

mono 构建是 GUI 子系统二进制，PowerShell `& $bin` 与 pwsh 捕获都拿不到输出；改用 **cmd 重定向文件**（与本仓 `Environment` 抽象同一做法）：

```
$ cmd /c ""F:\moonbit-hof-rs\godot-mcp\godot\bin\godot.windows.editor.x86_64.mono.exe" --version > "%TEMP%\dr47_version.txt" 2>&1"
CMD_EXIT=0
--- file ---
4.8.dev.mono.custom_build.ba1587c71
```

⇒ **符合**：版本串**逐字**  `4.8.dev.mono.custom_build.ba1587c71`，退出码 0。
（旁证：`hof doctor` 也在冒烟启动时独立执行了同一命令并报 `[ok] godot.engine_version: 4.8.dev.mono.custom_build.ba1587c71`，见 §3。）

### 1.4 `.workspace/mario` 的旧通道残留（要求：无 `[editor_plugins]`、无 `addons/godot_mcp_rs`）

```
--- editor_plugins count ---
0
[application] config/features=PackedStringArray("4.8")   （project.godot 全文无 [editor_plugins] 段）
--- addons tree ---
(空：addons/ 下无任何条目)
--- addons/godot_mcp_rs exists? ---
False
--- .godot/extension_list.cfg exists? ---
False
```

⇒ **符合**（与 D218/D219 记载的调度者清理结果一致，本次复核通过）。

### 1.5 其它前置（非 §1 四项，但影响可判性）

| 项 | 值 |
|---|---|
| 模型端点 | `GET http://100.105.152.101:18080/v1/models` → **HTTP 200** |
| 9877 MCP | **HTTP 200** |
| 密钥 | 经 `config/model.secret.env` 用 **bash** 装入 `HOH_MODEL_API_KEY`，**只打印长度 = 51**（未打印值） |
| `PRD-mario.md` sha256 | `4c81c3a9995f0b3afdf01421a0c3be88573cceefc284ce9bafbfda141f0f5c3a`（§7 守护项，前后一致） |

**§1 结论：四项全部符合，准予开跑。**

---

## 2. 活体契约核对（§2）——准入门判定

方法与落盘：`initialize` → `notifications/initialized` → `tools/list`，直接对 9877 POST JSON-RPC（与 `src/tools/mcp.rs` 同形）。
**原始响应字节**落在**临时目录**（`%TEMP%\dr47_toolslist_raw.json`，56,534 B），**未写进 `runs/**`**。
另存 `%TEMP%\dr47_init_resp.json`、`%TEMP%\dr47_init_headers.txt`。

原始响应头/首部（节选）：

```
HTTP/1.1 200 OK
Content-Type: application/json
Content-Length: 181
{"id":1,"jsonrpc":"2.0","result":{"capabilities":{"logging":{},"tools":{"listChanged":false}},
 "protocolVersion":"2025-03-26","serverInfo":{"name":"godot-mcp-rs","version":"0.1.0"}}}
```

`tools/list` 原始字节：`{"id":2,"jsonrpc":"2.0","result":{"tools":[{"description":…,"inputSchema":…,"name":"project_get_info"}, …]}}`；
首 3 字节 `{"i`（**无 BOM**），末字节 `}`。

集合定义：`F` = 夹具 `tests/fixtures/mcp/tools_list.json`；`E` = 活体**编辑器端点**；`G` = 活体**游戏端点**（§9 实测）。

| 项 | 结果 |
|---|---|
| `|E|`（编辑器端点可见） | **154** |
| `|F|`（夹具） | **177** |
| `GET /mcp` 的 `tools` 字段 | **154**（与 `|E|` 一致） |
| 名字重复 | E/F 均 **0** 重复 |

### 2.1 判据 1：`E ⊆ F` —— **通过**

```
E not in F = [] (EMPTY -> PASS)
```
活体编辑器端点**没有**出现夹具里没有的名字 ⇒ 无真·合约漂移。

### 2.2 判据 2：`|F \ E| == 23` 且全为 `running_game_*` —— **通过**

```
F not in E count = 23
all start running_game_ = True
non running_game_ in diff = [] (EMPTY -> PASS)
--- the 23 (listed) ---
running_game_assert_node_state, running_game_assert_screen_text, running_game_capture_frames,
running_game_capture_screenshot, running_game_capture_signal_emissions, running_game_create_input_recording,
running_game_execute_gdscript, running_game_find_nearby_nodes, running_game_find_node_when_available,
running_game_find_nodes_by_script, running_game_find_ui_elements, running_game_get_autoload_node,
running_game_get_node_properties, running_game_get_node_properties_batch, running_game_get_node_property_samples,
running_game_get_scene_tree, running_game_move_player_to_target, running_game_play_input_recording,
running_game_run_stress_test, running_game_run_test_scenario, running_game_set_node_property,
running_game_simulate_button_click_by_text, running_game_stop_input_recording
```
冲突的字典序显示为 `running_game_*` 通道；**恰为 23 条**，与 addendum §2 第 2 条完全吻合。
按明令，这 23 条**不判缺陷**（它们本就只在游戏端点）。

### 2.3 判据 3：`E ∩ F` 的 `name`/`description`/`inputSchema` 逐字比较 —— **有 2 处差异，允许开跑并逐条列出**

对 `E ∩ F` 的 **154** 条逐字段比对：
- `name`：**154/154 逐字相同**；
- `description`：**154/154 逐字相同**；
- `inputSchema`：**152/154 相同**，**2 条不同**（各对夹具与 `renamed.json` 各命中一次，故 4 个字段级差异条目）：

| # | 工具 | 字段路径 | 活体 | 离线文档（夹具/`renamed.json` 同值） |
|---|---|---|---|---|
| 1 | `editor_get_test_report` | `inputSchema.properties.clear.default` | `true` | `false` |
| 2 | `editor_simulate_input_sequence` | `inputSchema.properties.events.items` | **不存在** | 存在（`{"description": "一次或多次事件…", "properties": {...}, "type": "object"}` 等完整子 schema） |

两条工具的 `name`/`description` 逐字相同；`inputSchema` 的其余结构（顶层键 `properties/required/type`、属性名、`required`）全部一致。
⇒ 属 addendum §2 第 3 条所称「离线文档源 vs 活体」的已知风险面，**记录在案**（并见 §6 DEF-D 之外的观察：这两条恰是批次一报告 §2.4/DR-44 标注「实现先修」的工具之一）。

### 2.4 判据 4：夹具专用字段 —— **无夹具专用键（复核 D218）**

```
tool key union (renamed.json): ['description', 'inputSchema', 'name']
tool key union (fixture)     : ['description', 'inputSchema', 'name']
fixture-only tool keys = []      renamed-only tool keys = []
per-tool key diffs = 0
top-level: live=['id','jsonrpc','result']  fixture=['id','jsonrpc','result']  renamed=['_meta','id','jsonrpc','result']
```
⇒ 夹具相对 `tools_list.renamed.json`：**工具级一个键不多、一个键不少**；唯一差别是源文件**顶层** `_meta` 键被丢弃。
**再次确认 D218 的实测结论**：D217 第 3 条担心的「夹具专用字段」**确实不存在**，无需为逐字比较排除任何键。
（另：`F == R` 顺序一致、双向差集皆空、`renamed.json` 的 177 条**没有** `scope` 字段——4 个顶层键里没有它，故端点作用域无法从文档读出，只能实测。）

### 2.5 §2 结论

**准入门第 1、2 条通过 ⇒ 准予开跑**（第 3 条差异已逐条列出；第 4 条已复核；第 5 条并集判据见 §9，顺序为使「冒烟后」）。

---

## 3. 冒烟命令、真实退出码与关键日志

### 3.1 命令原文（不含密钥）

```bash
cd /f/moonbit-hof-rs
export HOH_MODEL_API_KEY=$(grep '^HOH_MODEL_API_KEY=' config/model.secret.env | cut -d= -f2- | tr -d '\r\n')
echo "key length: ${#HOH_MODEL_API_KEY}"        # 输出：key length: 51
./target/release/hoh.exe run --iterations 1 --run-id smoke-t6
```

- 未带 `--fresh-workspace`（工作区是 A_0 起点）。
- **偏离说明（唯一一处）**：任务书 §3.2 给的落点是 `$HOH_HOH_BIN` 或 `target\release\hoh.exe`，
  但本机 `HOH_HOH_BIN` 为空且**当时不存在 release 二进制**（只有 `target\debug\hoh.exe`）。
  我以 `cargo build --release --offline` 现场构建（**exit 0**，`Finished in 1m 10s`，产物 `target\release\hoh.exe` 12,253,696 B，2026-09-29 00:40:12），
  随后用 release 跑冒烟。**未改任何 `src/**`、`tests/**`、`config/hoh.yaml`**。
- 本命令由 **Git Bash** 发出（按 addendum §6 的密钥读取方式）；控制台日志写 `%TEMP%\dr47_smoke_t6_console.log`（**不在 `runs/**`**）。

### 3.2 真实退出码

```
SMOKE_EXIT=6
```
⇒ **6 = 循环完成但产物不可启动**（与 §4 的 `artifact_gate.launchable=false` 一致；任务书 §3.4 预期之一）。
`runs/smoke-t6/exit_code` 文件内容亦为 `6`。

### 3.3 关键日志片段（真实输出）

启动预检（`hof doctor`，全部来自活体）：

```
[ok] spec: .spec/hof-rs/PRD-mario.md (sha256 4c81c3a9995f0b3afdf01421a0c3be88573cceefc284ce9bafbfda141f0f5c3a)
[ok] model.identity: config `deepseek-v4.1-flash` -> wire `deepseek-v4.1-flash`
[ok] model.chat: http://100.105.152.101:18080/v1/chat/completions answered with model `deepseek-v4.1-flash`
[ok] godot.bundled_addon: .workspace/mario\addons/godot_mcp_rs must not exist: the MCP channel is the engine's native module (DR-41)
[ok] godot.extension_cache: .workspace/mario\.godot/extension_list.cfg must not reference res://addons/godot_mcp_rs/godot_mcp_rs.gdextension (DR-41)
[ok] godot.editor_scope: qa_scope: … (D7)
[ok] godot.engine_binary: F:/moonbit-hof-rs/godot-mcp/godot/bin/godot.windows.editor.x86_64.mono.exe (size 194207744 B, mtime 1790572931)
[ok] godot.engine_version: 4.8.dev.mono.custom_build.ba1587c71
[ok] tools.mcp: 154 tools available at http://127.0.0.1:9877/mcp
```

收尾行：

```
run smoke-t6 finished: 1 iteration(s), final version Some("fc78d299e6dcc9711d5d38c6d04191e586def586d9d0daec70358f3353579d3c"), total tokens Some(26805473)
prd coverage: 8/30 verified (total=derived from the Tester's claims; harness/gate describe the runtime contract, not the product)
```

`runs/smoke-t6/warnings.log`（全文）：

```
qa_scope: MCP acts on the project open in the editor (the real workspace) while the Tester evaluates a frozen copy; the runtime binds both to one candidate identity with pre-QA and around-QA hash assertions (D7).
iteration 1: no_progress (the developer stage produced no change)
iteration 1: the artifact is not launchable after the one allowed repair retry; freezing A1 anyway (artifact_gate.launchable=false)
```

运行结构与用量（`iter-1/result.json` / `usage.json`）：三角色**各 1 次**、Developer **2 次尝试**（第二次是 `launch_gate_repair`），
全部 `exit_status=LimitsExceeded`：

| 角色 | attempts | calls | total_tokens | duration_ms |
|---|---|---|---|---|
| planner | 150 步 | 150 | 2,202,183 | 184,385 |
| developer | attempt1 150 + attempt2 60 | 210 | 15,407,542 | 1,852,719 + 932,027 |
| tester | 150 步 | 150 | 9,195,748 | 1,030,969 |
| **合计** | | | **26,805,473** | |

`repair_retry_used=true`；`secret_redactions=0`；`out_of_tree_writes=[]`；`artifact_hygiene.suspicious_files=[]`；
`evidence_diff={added:[],modified:[],removed:[]}`。

> 纪律声明：冒烟全程**未中断**。整轮约 1 小时 52 分（00:40:45 → 02:32 前后）。

---

## 4. E1..E6 逐条判定

| 编号 | 判定 | 一句话理由 |
|---|---|---|
| E1 | **not_met** | 三角色都真跑了、`D_1` 与 `E_1` 合法，但 **Developer 零工程增量**（A0 的 hash == A1 的 hash）。 |
| E2 | **not_met** | `artifact_gate.launchable=false`、exit 6；**但**同轮 play_scene 真启动成功，唯一「错误」是引擎的 MCP 提示行（见下）。 |
| E3 | **not_met** | 游戏端点注册**成功后又挂死**，所有 `running_game_*` 观测失败、输入只到编辑器侧 ⇒ 核心行为**无一条**被证实。 |
| E4 | **met** | 8 条 verified 全部指向真实存在的可复现公共记录并绑定 candidate_id；22 条未证者全部落 gap。 |
| E5 | **met** | 快照 hash 前后一致，我独立重算得同值 `fc78d299…`（workspace == candidate == 版本库三棵树逐字节同）。 |
| E6 | **met** | QA 把未达成全部如实落 gap（含「PNG 是旧的」「错误行是诊断不是脚本错误」）；我另构造 2 个反例，均未推翻。 |

### E1 —— not_met（循环跑通，但无工程增量）

- **Planner 产出合法 `D_1`：✅**。`iter-1/plan.md`（2830 B）三节齐备：`### Priority Order`、`### Preservation Gate`、`### Acceptance Gate`。
  `planner.attempt1.log`：`artifact_valid: true`。
- **QA 产出合法 `E_1`：✅**。`iter-1/evidence.json`（33,586 B）：`verified_records` 8 条（V1–V8）+ `gap_records` 22 条（G1–G22）
  + `planner_handoff{preservation_constraints,update_targets,validation_requirements}`；每条执行记录都带
  `candidate_id: fc78d299…`（R4 身份绑定；QA 原始产物 `candidate/.hoh/evidence.json` 无该字段，是 Runtime 归一化时绑定的，逐行 diff 已核）。
  `iter-1/qa_report.md`（3124 B）在。`prd_coverage = {verified: 8, gap: 22}`。
- **Developer 产出工程增量：❌**。`versions/index.json`：
  ```
  iteration 0 role=init      version_id=fc78d299e6dcc9711d5d38c6d04191e586def586d9d0daec70358f3353579d3c  note=A0 initial artifact
  iteration 1 role=developer version_id=fc78d299e6dcc9711d5d38c6d04191e586def586d9d0daec70358f3353579d3c  note=A1 after the developer and deterministic stages
  ```
  **A1 的 version_id 与 A0 完全相同**，`parent` 亦为该值（自指）。`warnings.log` 记 `no_progress`，
  `result.json.warnings` 含 `no_progress`。Developer 两轮共 210 次调用后工程**零改动**。
- ⇒ 三个子条件中第 3 条不成立，**E1 = not_met**。（`evidence_diff` 三项皆空亦与此一致。）

### E2 —— not_met（gate 判否；实质可启动，但未获认证）

- `iter-1/result.json` 的 `artifact_gate`：
  ```json
  {"applicable": true, "launchable": false,
   "reasons": ["editor_errors_baseline: editor reported 1 error(s):
     {\"available\":true,\"count\":1,\"editor\":true,\"errors\":[\"[MCP] capture=off (default; use --mcp-capture=on_error|every_call together with --mcp-trace=<path>)\"],
      \"in_process\":true,\"log_path\":\"user://logs/godot.log\",\"note\":\"\",\"pid\":108432,\"port\":9877,\"process\":\"editor\",\"source\":\"editor_log\"}
     (UNAVAILABLE: the editor is not clean)"]}
  ```
- **唯一**失败原因是 `editor_errors_baseline` 步骤：引擎 `editor_get_errors` 的 `errors` 数组里那一条
  **是 MCP 模块自身的信息性提示 `[MCP] capture=off`，不是 GDScript 编译/运行错误**。
- 二次尝试（`launch_gate_repair`，60 步）后**仍然** `launchable=false`（两轮电池 `battery_passes` 步骤表逐项相同，见下），
  故 Runtime 按设计 `freezing A1 anyway` 并 exit 6。
- **反方向证据（必须同时呈现，不得省略）**：同一轮的**活体**证据显示工程**确实能启动并运行**：
  - `editor_play_scene` → `{"endpoint":"http://127.0.0.1:65333/mcp","mcp_port":65333,"mcp_port_source":"auto_free_port","mode":"main","pid":109964,"playing":true}`；
  - 游戏端点**真的回答了** `running_game_get_scene_tree`，返回含 `Ground/Platform1-3/Wall/Player(CharacterBody2D, res://scripts/player.gd)/Coin1…` 的场景树。
- ⇒ 按任务书指定的证据形态（`result.json` 的 `artifact_gate`）判定：**E2 = not_met**（harness 自己的闸门说不可启动、进程退出码 6）；
  **但其根因是假阴性**（DEF-A），并非真的编译/脚本错误。这一区分是本报告的核心事实之一。

`battery_passes` 两轮步骤对照（`true`/`false` = 步 ok）：

| pass | 步骤序列（name=ok） |
|---|---|
| 1 | project_reload_and_open=true, scene_structure=true, **editor_errors_baseline=false**, play_scene_ready=true, scene_tree=true, screenshot=true, **input_channel_probe=false**, **input_replay=false**, **node_and_collision_assertions=false**, editor_stop_scene=true, engine_identity=true |
| 2 | **与 pass 1 完全相同的 11 项与相同的 4 个 false** |

⇒ 电池结果**可复现**；`engine_identity` 步 **true**（DR-44 闸门在真机通过）。

### E3 —— not_met（**本批最重要的诚实结论**）

任务书 §4 特别提示：新契约下 `running_game_*` 只存在于游戏端点；若 E3 依赖游戏端点而端点未登记成功，那就是 not_met（或缺陷），**不得**用编辑器端点凑近似。

**事实：端点登记成功了，但随后挂死。** 逐项：

| 子项 | 判定 | 依据（真实 payload / 原始记录） |
|---|---|---|
| 玩家**左右移动** | **not_met** | 无任何游戏进程内的位移证据。唯一「注入成功」的是 `editor_simulate_input_action`，其返回 `{"action":"move_right","in_input_map":true,"pressed":true,"simulated":"action","strength":1.0,"**target":"editor**"}` —— 注入对象是**编辑器**，不是游戏进程（DR-35 的 `EDITOR_SIDE_INJECTION`）。配套的 `running_game_get_node_property_samples`（记录 `Player.position`，60/10/60/30 帧）**三次尝试全部失败**：`Connection Failed: … 由于目标计算机积极拒绝 (os error 10061)`。 |
| **跳跃** | **not_met** | 同上：`jump:EDITOR_SIDE_INJECTION` 只在编辑器侧被确认，`running_game_get_node_property_samples(node_path=Player, properties=[position], frame_count=30)` 三次连接被拒。 |
| ≥1 **可交互对象** | **not_met（仅「静态存在」为 met）** | 场景树确有 `Coin1-4`、`Enemy1-2`、`QuestionBlock`、`Brick1`、`Goal(Area2D)` 等节点与碰撞体（V4/V8 已证「存在」）；但**没有一次交互被驱动或观测**（F7–F12 全在 gap）。「可交互」= 行为，未证。 |
| **终点/胜负条件** | **not_met** | `Goal` 节点 + `Result` Label 只是**声明**存在（`scene_structure.json`：`Result` label `text` 为空）；无胜利/失败/重开状态被观测（F13–F15 全在 gap）。 |
| N2 截图 | not_met | `running_game_capture_screenshot` 三次 `-32602`：`Parameter 'save_path' must start with 'res://' or 'user://', got '.workspace/mario\\.hoh/evidence/frame-00.png'`；录像 PNG 是 **2026-09-21 17:55** 的旧文件（见 DEF-B）。 |

**游戏端点的时间线（两轮一致，可复现）**：

```
pass1: play_scene pid=109964 port=65333 -> get_scene_tree OK(50 nodes)
       screenshot 3×(-32602)
       execute_gdscript 3× timeout(os 10060)         [1:20:56, 1:26:58, 1:33:00]
       get_node_property_samples / get_node_properties 全部 refused(os 10061)
pass2: play_scene pid=101872 port=63698 -> get_scene_tree OK(50 nodes)
       screenshot 3×(-32602)
       execute_gdscript timeout(os 10060)            [1:58:41]
       后续 get_node_property_samples / execute_gdscript 全部 refused(os 10061)
```

`mcp-errors.jsonl` 逐行（共 43 行）即上述错误的原始流；其中 `-32602` 是**契约/参数**错误（截图），`10060/10061` 是**游戏端点进程**层面的不可达。

⇒ **E3 = not_met**，且这是**引擎/集成缺陷（DEF-C）造成的阻塞**，不是模型没写代码，也不是我用编辑器端点凑数。
（与 `smoke-t5` 的「exit 0 但 E3 不可判定」属同类诚实结论；本批更进一步：**游戏端点曾经短暂可用**，可用来定位。）

### E4 —— met

逐条对照 8 条 verified（`iter-1/evidence.json`）与其引用的公共记录，**每条引用的文件都真实存在且内容支持该 claim 的限定范围**：

| claim | 引用记录 | 我的复核 |
|---|---|---|
| V1 N1 可重载/打开 | `.hoh/deterministic/raw/project_reload_and_open.json` | 实读：`editor_rescan_project_filesystem` `reloaded=true`；`editor_open_scene` `opened=true,path=res://scenes/main.tscn`；步 ok=true ✔ |
| V2 N1 可启动并接受 MCP | `raw/play_scene_ready.json` | 实读：`playing=true,pid=101872,endpoint=…:63698`；随后 `running_game_get_scene_tree` ok（我数得 **50** 节点）✔ |
| V3 N1 场景结构合法 | `raw/scene_structure.json` | `project_read_scene_file_content` ok，步 ok=true ✔ |
| V4 节点树稳定 | `raw/scene_tree.json` | 实读 50 节点，含 Player/Camera/Ground/Goal/HUD/Enemy1/Coin1 ✔ |
| V5 干净停止 | `raw/editor_stop_scene.json` | 实读：`{"message":"Playback stopped","stopped":true}`，且 `game_endpoint_invalidated={endpoint:…:63698,pid:101872,port:63698,source:auto_free_port}` ✔ |
| V6 HUD 字段（**显式「static presence only」**） | `raw/scene_structure.json` | 与限定一致；claim 自陈「不是 live update」✔ |
| V7 PNG 文件存在（**自陈 mtime 是旧的**） | `.hoh/evidence/frame-00.png` | 文件存在、4246 B、mtime 2026-09-21 17:55；claim 内已写明「cannot confirm it depicts this battery run」✔（但其限定见 §4-E6 反例 R1） |
| V8 碰撞体存在（structural only） | `raw/node_and_collision_assertions.json` | 实读：三次 `editor_get_collision_info` ok=true（Ground/Player/Goal shape_count=1）；步 ok=false 但 claim **自陈**这一点与来源 ✔ |

22 条 gap（G1–G22）覆盖了所有未被证明者：F1–F17 行为、N1 的 launchable=false、N2 截图缺失、N3 稳定性、N4 回归基线。
并集 = 30 条、verified ∩ gap = ∅（与 `prd_coverage 8/22` 一致）。
⇒ **E4 = met。**

### E5 —— met（含真实 hash 值）

- Runtime 在执行 Tester **前**取 `h_cand_before = hash_tree(candidate)`、`h_ws_before = hash_tree(workspace)`（`src/runtime/run_loop.rs:1007-1010`），
  Tester 执行**后**取 `h_cand_after`/`h_ws_after`（`:1095-1096`）并 `assert_unchanged`（`:1097`、`:1114`）；
  不等则 `fail_contract`（`QaContaminatedCandidate` / `ReadOnlyRoleWroteArtifact`）并**提前返回**。
  本轮的 `result.json` 正常落盘（含 qa_report/evidence/usage）、无 contract violation ⇒ **两次比较都相等**。
- 这两个值**不是**直接落盘的字段，我按 `src/runtime/policy.rs:68` 的算法（sha256 over sorted `relpath\n{len}\n{bytes}\n`，excludes = {`.hoh`,`.git`}∪{`.godot`,`.import`}）
  **独立重算**，得到：

```
workspace .workspace/mario                 files= 17 sha256=fc78d299e6dcc9711d5d38c6d04191e586def586d9d0daec70358f3353579d3c  matches_recorded=True
candidate runs/smoke-t6/iter-1/candidate   files= 17 sha256=fc78d299e6dcc9711d5d38c6d04191e586def586d9d0daec70358f3353579d3c  matches_recorded=True
version   runs/smoke-t6/versions/fc78d299… files= 17 sha256=fc78d299e6dcc9711d5d38c6d04191e586def586d9d0daec70358f3353579d3c  matches_recorded=True
recorded candidate_id/version_id         = fc78d299e6dcc9711d5d38c6d04191e586def586d9d0daec70358f3353579d3c
```

- 即：**QA 前后的快照 hash 都是 `fc78d299e6dcc9711d5d38c6d04191e586def586d9d0daec70358f3353579d3c`**，
  且 QA 冻结视图（candidate）与版本库 A_1、与运行后 workspace **三棵树逐字节相同**（17 个非排除文件）。
  另：`result.json.out_of_tree_writes=[]`、`evidence_diff` 三项皆空。
- ⇒ **E5 = met**。（附带说明：A0 == A1 == 同一 hash，即 E1 的「无增量」也由此得到独立佐证。）

### E6 —— met（含 2 个我构造的反例）

**人工复核**：`iter-1/qa_report.md` 与 `iter-1/evidence.json` 逐条读。QA 的核心诚实动作有 3 个，都是「明知不利仍如实写」：
1. **不把不可读通道读成「动作未绑定」**：报 `ACTION_BINDING_UNKNOWN`，并写下
   「the channel was unreadable, **NOT** a missing action」「do NOT change project.godot on the basis of the unreadable channel」（G1/G20）。
2. **主动交出对自己不利的证据**：G21 自陈「读录 PNG 是 2026-09-21 的旧文件、本次 live 截图 -32602 失败」，
   并且**没有**把它算成「见过画面」（V7 仅限「文件存在」）。
3. **不把 launchable 失败粉饰**：G18 如实写 `launchable=false … although one boot succeeded`，并点名那条错误是
   「a harness diagnostic, not a script error」。

**反例构造（任务书 §4 E6 要求 ≥1 个）**：

- **R1 — 攻击 V7**：V7 的 claim「a visual evidence file is present in the candidate」由证据「文件存在（4246 B，PNG 签名/IHDR 正确）」支持吗？
  **支持「某文件存在」，但不支持「本候选轮产出了视觉证据」**：同一条 observation 自己就写了
  `cannot confirm it depicts this battery run: its mtime is 2026-09-21 17:55, older than the 2026-09-29 battery`。
  ⇒ 这是 8 条 verified 里**最弱的一环**。**但它不推翻 E6**：claim 的文字限于「文件存在」，且陈旧性在**claim 内部**与 G21 双重披露，
  证据本身真实可复现（我实测该文件确为 4246 B、mtime 2026/9/21 17:55）。
- **R2 — 攻击 V8 与 QA 自定规则的一致性**：`qa_report.md` 第 7 行声明
  「Only the battery steps marked `ok=true` were allowed to support a `verified` claim; `ok=false` steps were turned into gaps」，
  而 **V8 恰恰引用了 `ok=false` 的 `node_and_collision_assertions` 步**（其 observation 自陈「battery step … ok=false … but the collision_info sub-calls ok=true supply the shape counts」）。
  ⇒ **报告的自述规则与其实际判定存在口径不一致**。
  **但它不推翻 E6**：① 该不一致被**显式披露**在同一句 observation 里；② 我实读 `node_and_collision_assertions.json`，
     三条 `editor_get_collision_info` 调用的 `ok=true`、payload 数据真实（shape_count 1/1/1），故 V8 的**结论**有据；
  ③ 若按更严的口径，V7/V8 也应降为 gap —— 那只会让 E4 更保守，不会造成「未达成被谎报为达成」。

**结论**：本轮的失误方向是**保守**（把可证的写成静态/结构），**不存在**把 F1–F17 任一未观测行为写成 verified 的情形。⇒ **E6 = met。**

---

## 5. `engine` 块原文 + sha256 对照

`runs/smoke-t6/meta.json` 的 `engine` 块（**最终落盘版**，原文）：

```json
"engine": {
  "binary": {
    "mtime_unix": 1790572931,
    "path": "F:/moonbit-hof-rs/godot-mcp/godot/bin/godot.windows.editor.x86_64.mono.exe",
    "reason": null,
    "sha256": "25d29eb4fbaf48c00911bcb18b491d5a7305542e00557e70a05f185b935bb468",
    "size_bytes": 194207744
  },
  "checked_at": 1790613647,
  "kind": "godot",
  "listener": {
    "matches_binary": true,
    "path": "F:\\moonbit-hof-rs\\godot-mcp\\godot\\bin\\godot.windows.editor.x86_64.mono.exe",
    "pid": 108432,
    "reason": null
  },
  "mcp": {
    "editor_endpoint": "http://127.0.0.1:9877/mcp",
    "editor_status": null,
    "editor_status_reason": "no `GET /mcp` body was recorded for the editor endpoint in this run",
    "game_endpoint": null,
    "game_endpoint_reason": "the game endpoint does not exist until `editor_play_scene` has created it"
  },
  "version_reason": null,
  "version_string": "4.8.dev.mono.custom_build.ba1587c71"
}
```

**我自己算的对照**（`Get-Item` + `Get-FileHash`）：

| 字段 | meta.json | 我独立计算 | 判定 |
|---|---|---|---|
| `binary.path` | `F:/moonbit-hof-rs/godot-mcp/godot/bin/godot.windows.editor.x86_64.mono.exe` | 同一文件（`Test-Path` 真） | ✔ |
| `binary.size_bytes` | 194207744 | **194207744** | ✔ 逐字一致 |
| `binary.sha256` | `25d29eb4…bb468` | `25d29eb4fbaf48c00911bcb18b491d5a7305542e00557e70a05f185b935bb468` | ✔ 逐字一致 |
| `binary.mtime_unix` | 1790572931 | 1790572932（`[DateTime]::ToUnixTimeSeconds` 口径） | ⚠ 差 **1 s**（取整/口径差，非缺陷；文件本身未变） |
| `version_string` 以 `4.8.dev.mono` 开头 | `4.8.dev.mono.custom_build.ba1587c71` | `cmd /c "<binary> --version"` → 同串 | ✔ |
| `listener.pid` | 108432 | `Get-NetTCPConnection` → 108432 | ✔ |
| `listener.path` | `…mono.exe` | `Get-Process -Id 108432` → 同一路径 | ✔ |
| `listener.matches_binary` | `true` | 路径逐字一致 | ✔ |
| `mcp.editor_endpoint` | `http://127.0.0.1:9877/mcp` | 实测 200 / 154 tools | ✔ |
| `mcp.game_endpoint` | `null` + `game_endpoint_reason` | 本轮**实际存在过** 65333 / 63698 两个游戏端点并被成功调用 | ⚠ **reason 与事实不符**（DEF-D） |
| `mcp.editor_status` | `null` + `editor_status_reason` | 本轮 `GET /mcp` 可读（doctor 已读、我亦读过） | ⚠ 未落盘（DEF-D） |
| 字段缺失 / `null` 无 `reason` | 无 | — | ✔ 按任务书 §5 字面规则**不是**缺陷（两个 null 都带 reason），但 reason 内容见 DEF-D |

---

## 6. 缺陷清单（含复现步骤与影响）

**无 blocker 级「必须停止」缺陷**（准入门通过、循环跑通）；以下 6 条按严重度排列。**我不修任何一条**（禁项）。

### DEF-A（major，直接决定 E2 / exit 6）—— `editor_errors_baseline` 把引擎的 MCP 提示行当错误，使可启动闸门假阴性

- **现象**：`artifact_gate.launchable=false`，唯一 reason 是
  `editor_errors_baseline: editor reported 1 error(s): … "errors":["[MCP] capture=off (default; use --mcp-capture=on_error|every_call together with --mcp-trace=<path>)"] … (UNAVAILABLE: the editor is not clean)`。
- **本质**：该串是**引擎 MCP 模块自身打印的信息性提示**（`capture=off` 的默认说明），不是 GDScript 编译/运行错误。
  引擎把它放进了 `editor_get_errors` 的 `errors` 数组（`count=1`），hof-rs 据此把编辑器判为「not clean」。
- **复现**：`hoh run --iterations 1 --run-id <any>`；`runs/<id>/iter-1/result.json` → `artifact_gate.launchable=false`；
  `…/raw/editor_errors_baseline.json`；两轮电池（含 60 步 repair）结果相同。
- **影响**：① exit 6（`RESULT_NOT_LAUNCHABLE`）；② E2 无法通过；③ 任何真实编译错误都被这条噪声混淆，闸门失去判别力；
  ④ 触发一次 60 步、6.4M tokens 的无效 repair（本批真金白银的浪费）。
- **候选处置（留给实现批裁决，非本批）**：hof-rs 侧按 `source/process/pid` + 文案白名单过滤引擎自身的 MCP 诊断行，
  或转为 warning；**不可**改 `godot-mcp/**`。若认为应属引擎侧修，则需另开引擎批次。

### DEF-B（major，直接决定 E3 的 N2 与「证据完整性」）—— `running_game_capture_screenshot` 的 `save_path` 契约不匹配，且失败被「旧文件存在」掩盖成成功

- **现象 1（契约）**：`running_game_capture_screenshot` 被以 `.workspace/mario\.hoh/evidence/frame-00.png` 调用，
  引擎拒绝 3 次：`code=-32602, "Parameter 'save_path' must start with 'res://' or 'user://', got '.workspace/mario\\.hoh/evidence/frame-00.png'"`（两轮电池均如此）。
- **现象 2（更严重，假证据）**：该步骤在 `battery_passes`/`screenshot.json` 里被记为 **`ok=true`**，
  且 `deterministic.json` 写下 **`screenshot written to .hoh/evidence/frame-00.png (4246 byte(s))`** —— 但**本次运行从未写入任何 PNG**；
  4246 B 的文件是 **2026-09-21 17:55** 的旧文件（`smoke-t5` 时代），路径上「已存在」使存在性检查通过。
- **复现**：`.hoh/deterministic/raw/screenshot.json`（唯一调用 `ok=false`，步 `ok=true`）；
  `mcp-errors.jsonl` 前 3 行；`Get-Item .hoh/evidence/frame-00.png` → `LastWriteTime 2026/9/21 17:55`。
- **影响**：① E3/N2 无本期画面证据（**仅** QA 的 G21 诚实捕获了它）；② 「step ok=true + 文案 written」会污染 E_1 与后续轮次的信任；
  ③ 若无人细读，会把旧帧当成新帧 —— 这正是 E6 要防的自欺，本批由 QA 的 G21 拦住。
- **候选处置**：把证据输出路径映射为 `user://`（或引擎接受的可写虚拟路径）并在写失败时**删除/不认**旧文件、步骤判 false。

### DEF-C（major，直接决定 E3）—— 游戏端点注册成功后挂死并消失（两轮可复现）

- **现象**：`editor_play_scene` 成功回 `endpoint`/`mcp_port`/`pid`/`mcp_port_source=auto_free_port`，
  且**首个** `running_game_get_scene_tree` 成功（50 节点）；此后
  ① `running_game_execute_gdscript` 超时（`os error 10060`，无响应）；
  ② 其后所有游戏端点调用被拒（`os error 10061`），直至消失。
- **复现（两轮不同端口/PID，轨迹一致）**：
  - pass1：pid 109964 / port 65333；`get_scene_tree` OK → screenshot `-32602` → `execute_gdscript` 10060 ×3 → 其余 10061。
  - pass2：pid 101872 / port 63698；同样模式。
  - 我在**冒烟后**用 harness 自己的 `editor_play_scene` 又起了一个（pid 115716 / port 56438），
    它**活着**并回答了 `tools/list`（73 条）——即「起得来、能应答」，与「跑一会儿就挂」并存，见 §9。
- **影响**：所有 `F1..F17` 行为证据归零 ⇒ **E3 = not_met**；DR-43 的「登记游戏端点」在真机**成功**，
  但「注入了输入 → 能读回」这条链在**游戏进程侧**断裂。
- **候选处置**：需判定是引擎游戏进程的 MCP 服务死锁/退出，还是 hof-rs 的调用形态（例如 `execute_gdscript` 的 script 体在游戏进程内阻塞主循环）触发。
  本批只提供证据，不给结论。

### DEF-D（minor→moderate，DR-44 设计意图未达成）—— `engine.mcp.game_endpoint` 与 `editor_status` 未按事实落盘

- `game_endpoint: null`，reason = 「the game endpoint does not exist until `editor_play_scene` has created it」；
  但本轮 `editor_play_scene` **确实创建了**它（65333、63698 两个，且被成功调用）。**reason 与事实矛盾**。
- `editor_status: null`，reason = 「no `GET /mcp` body was recorded for the editor endpoint in this run」；
  但 `hof doctor` 本轮**已经** `GET /mcp`（并读出 `154 tools`），运行期也一直可读 —— 本可原样入库。
  这与 `DESIGN-DETAIL.md` §13.4 期望的 `"editor_status": { "…": "GET /mcp 的原样响应体" }` 不符。
- 按任务书 §5 的字面规则（null 必须带 reason）**不构成缺陷**；但 DR-44 的目标是「把用的是哪个引擎/哪个端点变成可验证事实」，
  此处只实现了一半。复现：读 `runs/smoke-t6/meta.json` 的 `engine.mcp`。

### DEF-E（minor）—— `deterministic.json` 的输入诊断与自己的原始记录矛盾

- `deterministic.json` 的 replay observation 写：
  「EDITOR_SIDE_INJECTION: **the editor InputMap does not list ["move_left", "move_right", "jump"]** — that is the editor's own map, not the game's (DR-35)」。
- 但**同一步**的原始记录 `raw/input_replay.json` 里，`editor_get_input_actions` 返回 **92** 个动作，
  **前三个恰是 `jump`, `move_left`, `move_right`**（`ok=true`）。
- 复现：对比 `runs/smoke-t6/iter-1/candidate/.hoh/deterministic/deterministic.json` 的该条与 `raw/input_replay.json` 第 1 个调用。
- 影响：诊断文案误导后续决策（可能让人以为工程 InputMap 有问题）；不影响 E3 结论（游戏侧确实不可读）。

### DEF-F（minor，与 DEF-B 同源）—— 电池步骤 `ok` 语义允许「旧文件」冒充「本次产物」

- `screenshot` 步 `ok=true` 而其唯一调用 `ok=false`；`input_channel_probe` 步 `ok=false` 却包含 4 条 `ok=true` 的调用。
- 即步骤级 `ok` **不是**「所有调用成功」，而是某种更弱的口径，且**未**把「目标文件已存在但本次写入失败」判否。
- 影响：DEF-B 的假证据得以进入 `battery.json`/`deterministic.json`。复现：`iter-1/result.json.battery_passes` 对照 `raw/*.json`。

### 观察（不计缺陷）

- `result.json.warnings` 含 **`harness_source_read`**：DR-38 的气味检测器在某个角色的**工具调用**里匹配到 harness 仓库根路径（`src/runtime/run_loop.rs:210-229`）。它是**警告**，不阻断；本批未追查是哪个角色、哪一次调用。
- `meta.json.engine.binary.mtime_unix` 与我的口径差 1 s（见 §5）。

---

## 7. 遗留风险与不确定项

1. **游戏端点为何挂死未定因**（DEF-C）：可能是引擎游戏进程的 MCP 服务死锁/退出，也可能是 hof-rs 的 `execute_gdscript` 调用形态。
   本批只给时间线，不做归因。**这是 E3 的直接阻塞。**
2. **`[MCP] capture=off` 到底是引擎错误级日志还是 hof-rs 的分类**：我只看到引擎响应体里 `errors:["[MCP] capture=off …"]`，
   **未**审阅引擎源码（`godot-mcp/**` 只读且未读内部实现）。修复方向取决于此判定（DEF-A）。
3. **D219/addendum 的端点集合数字**：实测 `|G|=73`、`|E∩G|=50`、editor-only 104、game-only 23（见 §9），
   与 addendum 的 `69 / 46 / 108 / 23` 在**交集与端点总数**上差 4，但**并集恰为 177**。需调度者裁定是文档勘误还是真有作用域变更。
4. **零增量是否属「模型能力」或「A_0 已完备」**：`.workspace/mario` 的 A_0 已含完整 Mario（main.tscn 7434 B、8 个 .gd），
   Developer 210 次调用后**一字未改**。无法在离线断言其原因是「无活可干」还是「模型陷入空转」。
5. **夹具 vs 活体的 2 处 `inputSchema` 差异**（`editor_get_test_report` 的 `clear.default`；`editor_simulate_input_sequence` 缺 `events.items`）
   来源未查（引擎文档 vs 引擎实现二者之一先变），**只记录**。
6. **DEF-A/B/C 的修复属另一批实现**（D218 已把 DEF-2/3/4 排队到批次二验收后，现在又多 6 条）。
   **本批未修任何代码**；未改 `src/**`、`tests/**`、`config/hoh.yaml`、`godot-mcp/**`、`PRD-mario.md`。
7. **`prd_coverage 8/30`**：8 条全是 N1/N2/P2/P4 的结构性/可启动性，22 条 gap 中 17 条是产品行为（F1–F17）。
   本轮的「8」**不代表**产品达成度，只反映可观测通道的可用性上限。

---

## 8. 诚实披露（任何中断、重跑、猜错、绕过尝试）

1. **未中断冒烟**。整轮一次跑完（00:40:45 → 02:32 前后，约 1h52m）。中途我因「长时间无文件写入」做过**只读**观察
   （列目录、看 PID、看 CPU），**未**杀进程、**未**重启、**未**抢占 9877。
2. **一次偏离**：任务书 §3.2 的 `target\release\hoh.exe` 起初不存在，我先 `cargo build --release --offline`（exit 0）再跑。
   这是构建，不是改代码；`HOH_HOH_BIN` 为空已如实记录。
3. **`<binary> --version` 由我直接执行**（§1.3 明文要求）。它是瞬时查询、不绑端口、不打开工程；
   且 `hof doctor` 同时独立执行了同一命令给出同串。**没有**启动第二个编辑器或游戏。
4. **唯一一次「起游戏」是 §9 的端点核对**，且**只用** harness 的 `editor_play_scene` 路径（addendum §3 允许），
   发生在**冒烟之后**，随后立即 `editor_stop_scene`（`stopped=true`），并已核实：56438/63698/65333 **不再监听**、
   只剩编辑器 PID 108432（见 §9.7）。**没有**手起任何进程、**没有**占用其它端口验证集合。
5. **读了我本不该改的东西，只读**：为复现 E5 我通读了 `src/runtime/policy.rs`、`src/runtime/run_loop.rs`、`src/runtime/hygiene.rs`、`src/tools/mcp.rs`（**只读**，未改一字节）。
6. **一次猜错并自我纠正**：我一开始用 `bash -lc` 想读 `config/model.secret.env`，结果落到 **WSL** 而非 Git Bash（报 `cd: /f/...: No such file`）；
   改用工具自带的 Git Bash 终端后成功。**未**因此把密钥打出来（任何地方只出现长度 51）。
7. **未把密钥写进任何输出/日志/报告/`runs/**`**：`grep -rlF <key>` 在 `runs/smoke-t6`、`runs`、`.spec/hof-rs/tasks` 的命中数均为 **0**；`result.json.secret_redactions=0`。
8. **落盘纪律**：`tools/list` 原始字节与控制台日志都写在 `%TEMP%`，**未**进 `runs/**`；报告只引用片段。
9. **未 commit / 未 push / 未 stage**：写报告前 `git status --porcelain` 为空。
10. **未删改 `runs/smoke-t1..t5`**：其目录 mtime 仍为 2026/09/21（11:20:17 / 12:51:02 / 15:29:03 / 16:37:35 / 18:06:38）。
11. **未改 `PRD-mario.md`**：前后两次 sha256 均为 `4c81c3a9…5c3a`。
12. **guard 复核（写报告前）**：编辑器 PID **108432** 仍 LISTEN 9877（活得比整轮长）；除它之外**无**其它 godot 进程；
    `git status --porcelain` 为空。
13. 本报告**唯一**新增文件即自身；`%TEMP%` 下的分析与原始字节脚本/记录不属仓库产物。

---

## 9. 端点集合核对（D219 修正判据）

> **顺序声明（addendum §3 要求）**：判据 5 需要 `G`，而 `G` 只能由 `editor_play_scene` 产生。
> 按 addendum 明令，我**没有**在冒烟前取 `G`；本节第 5 项为**冒烟之后**判定（顺序：先 §2 判据 1–4 → 跑冒烟 → 再做本节的 5–6）。
> 第 1–4 项用的是**冒烟前**捕获的编辑器端点原始字节（`%TEMP%\dr47_toolslist_raw.json`）。
> `G` 的取得：**冒烟后**用 9877 上的 `editor_play_scene`（harness 自己的路径）拿到 `endpoint=http://127.0.0.1:56438/mcp`、`pid=115716`、
> `mcp_port_source=auto_free_port`，再对该端点 `initialize` + `tools/list`（原始字节 `%TEMP%\dr47_game_toolslist_raw.json`），随后 `editor_stop_scene`。

| # | addendum §2 判据 | 结论 | 实测 / 未做 |
|---|---|---|---|
| 1 | `E ⊆ F` | **PASS** | **实测**：`E not in F = []` |
| 2 | `|F \ E| == 23` 且全 `running_game_*` | **PASS** | **实测**：差集恰好 23 条、全 `running_game_*`（23 条已逐条列出，见 §2.2） |
| 3 | `E ∩ F` 的 `name`/`description`/`inputSchema` 逐字 | **2 处差异（允许开跑，已逐条列出）** | **实测**：见 §2.3（`editor_get_test_report`、`editor_simulate_input_sequence`） |
| 4 | 夹具专用字段 | **无夹具专用键** | **实测**：工具级键集合与 `renamed.json` 完全相同；仅源文件顶层 `_meta` 被丢弃（复核 D218） |
| 5 | 并集判据 `|E ∪ G| == 177` 且 `|G| == 69` | **`|E ∪ G| == 177` PASS；`|G| == 69` FAIL（实测 73）** | **实测**（冒烟后）：见下 9.5 |
| 6 | 记录 `E`/`G`/`GET /mcp` 的 `tools` 与 23 条 game-only | **已记录** | 见下 |

### 9.5 并集判据的原始输出

```
=== gate 5: union criterion ===
|E| = 154   |F| = 177   |G| = 73
|E union G| = 177   (expected 177: True)
|G| == 69: False
G subset of F: True
editor-game intersection |E intersect G| = 50 (expected 46: False)
F not in (E union G) = []
(E union G) not in F = []
game-only (G not in E) count = 23  all running_game_ = True
```

以及端点公告原文（`editor_play_scene` 响应逐字）：

```json
{"args_deduplicated":[],"args_injected":["--mcp-port=56438"],"endpoint":"http://127.0.0.1:56438/mcp",
 "headless":false,"mcp_port":56438,"mcp_port_source":"auto_free_port","mode":"main","pid":115716,"playing":true}
```

游戏端点 `tools/list`：**HTTP 200，count = 73**。

### 9.6 端点集合的实测分区（**与 addendum 的等式不同**）

活体实测得到的分区是**严格按通道前缀**的，且并集恰好等于契约总数：

| 集合 | 大小 | 成员 |
|---|---|---|
| 契约总数 `F` | **177** | 夹具全部 |
| **编辑器端点 `E`** | **154** | `editor_*` 104 + `project_*` 48 + `os_*` 2 |
| **游戏端点 `G`** | **73** | `project_*` 48 + `os_*` 2 + `running_game_*` 23 |
| `E ∩ G`（两端共有） | **50** | 恰为 `project_*`（48）+ `os_*`（2） |
| `E \ G`（仅编辑器） | **104** | 恰为全部 `editor_*` |
| `G \ E`（仅游戏） | **23** | 恰为全部 `running_game_*` |
| `E ∪ G` | **177** | = `F`（双向差集皆空） |

程序化断言（全部为 True）：

```
E&G == exactly project_* plus os_* : True
Es-Gs == exactly editor_*          : True
Gs-Es == exactly running_game_*    : True
```

**与 addendum / D219 的差异（必须如实上报）**：addendum 的恒等式是
「177 = **108** editor-only + **46** 两端共有 + 23 game-only」，编辑器端点 154、游戏端点 **69**。
实测为「177 = **104** editor-only + **50** 两端共有 + 23 game-only」，编辑器端点 154、游戏端点 **73**。

- **一致的部分**：契约总数 177；编辑器端点 154；game-only = 23（全 `running_game_*`）；`E ⊆ F`；`E ∪ G = F = 177`。
- **不一致的部分**：**两端共有 46 → 实测 50**；由此 game-only 23 + 共有 50 = **73**（而非 69），editor-only 108 → **104**。
  即 4 条 addendum 以为 editor-only 的工具，实际**在游戏端点也可见**。
- **注意**：`tools_list.renamed.json` 的工具对象**只有 `name`/`description`/`inputSchema` 三个键，没有 `scope` 字段**，
  所以 addendum 的 108/46 不可能来自该文档；端点作用域只能实测。
  我**无法**从本批证据判定是「addendum 抄录 M 线旧数字有误」还是「引擎作用域真的变了」——**留给调度者裁定**（见 §7 风险 3）。
- **不影响准入门**：addendum §2 的**硬判据 1、2**（`E ⊆ F`；`|F \ E| == 23` 且全 `running_game_*`）**均通过**，
  且 `E ∪ G == F` 说明契约被两个端点**完整覆盖、无缺无溢**。故 §2 第 5 条的不符**不构成合约漂移**，只是该条自带的期望数字需要勘误。

### 9.7 端点归属与清理（守护项复核）

```
=== godot procs after stop ===
Id 108432  StartTime 2026/9/29 0:36:03      （唯一存活：编辑器；PID 与 9877 监听者一致）
=== ports 56438/63698/65333 ===
56438 listening=False    63698 listening=False    65333 listening=False
=== 9877 editor ===
108432
```

⇒ 我经 harness 路径创建的游戏进程**已全部退出**、端口已释放；编辑器 108432 全程存活；`GET /mcp` 仍为 200 / `is_editor:true`。

### 9.8 与冒烟内部端点的交叉印证

冒烟自身的两轮电池也各自通过 `editor_play_scene` 创建并登记了游戏端点，且**首个** `running_game_*` 调用成功：

| pass | `endpoint` | `pid` | `mcp_port_source` | 首个 `running_game_*` | 之后 |
|---|---|---|---|---|---|
| 1 | `http://127.0.0.1:65333/mcp` | 109964 | `auto_free_port` | `running_game_get_scene_tree` **ok** | `-32602` / `10060` / `10061`（DEF-B/C） |
| 2 | `http://127.0.0.1:63698/mcp` | 101872 | `auto_free_port` | `running_game_get_scene_tree` **ok** | 同上 |

⇒ **DR-43 的「解析并登记游戏端点」在真机成立**（`editor_stop_scene` 记录里亦带回
`game_endpoint_invalidated={"endpoint":…:63698,"pid":101872,"port":63698,"source":"auto_free_port"}`，失效语义正确）；
断裂点在游戏进程侧的**持续可用性**（DEF-C），不在端点路由。

---

## 10. 给调度者的一句话汇总

准入门（D219 修正版）**通过**；一轮真实 T=1 **跑完并留下完整证据**；
`E4/E5/E6 met`，`E1/E2/E3 not_met`；exit 6。三个阻塞性事实是：
① 引擎 MCP 提示行 `[MCP] capture=off` 被当错误 ⇒ 可启动闸门假阴性（DEF-A）；
② 截图 `save_path` 契约不匹配 + 旧文件使步骤假成功（DEF-B）；
③ **游戏端点注册成功后挂死/消失**，两轮可复现（DEF-C）——这是 E3 无法达成的根因。
另：实测端点分区为 **104 / 50 / 23**（并集 177），与 D219/addendum 的 **108 / 46 / 23（game 69）** 差 4，建议勘误或另开裁决。
**本批未改任何代码、未 commit、未 push；编辑器 PID 108432 存活；`PRD-mario.md` 与 `runs/smoke-t1..t5` 未被触碰。**
