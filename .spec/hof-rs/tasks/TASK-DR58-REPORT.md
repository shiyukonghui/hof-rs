# TASK-DR58-REPORT — 修正引擎应答的载荷形状误读（三处 + 扫描 + 真机载荷固化）

- 任务书：`.spec/hof-rs/tasks/TASK-DR58.md`（唯一任务来源）
- 落点：`F:\moonbit-hof-rs`（`master`，批次起点 `3c10663`）
- 性质：**离线批次**（未启动 Godot、未碰任何端口、未联网、未调模型端点）
- 报告人：实现子代理（无上游对话上下文）
- 时间：2026-09-29 15:0x → 15:3x（+0800）
- 真机证据来源（**只读引用，未改动**）：`runs/smoke-t7/**`、`runs/smoke-t7-experiment/**`；
  引擎 `4.8.dev.mono.custom_build.035edfce7`

---

## 1. 结论 + 门（`cargo test --offline` 真实尾部/退出码）

**结论：三处载荷形状误读已按真机载荷改对；真机载荷已逐字节固化并驱动测试；全仓同模式扫描完成；
离线门全绿。E3 是否 met 不由本批判定（也无任何本批输出可支撑该结论）。**

基线（本批开工时实测）：**342 passed / 0 failed / 7 ignored**，exit 0。
本批结束实测：

```
$ cargo test --offline 2>&1 | Tee-Object dr58-final-test.txt
...
running 38 tests                                     (tests\evidence_battery.rs)
test result: ok. 38 passed; 0 failed; 0 ignored; 0 measured; 0 filtered out; finished in 82.01s
...
test result: ok. 5 passed; 0 failed; 0 ignored; 0 measured; 0 filtered out; finished in 0.01s   (tests\dr58_payload_shapes.rs)
...
test e0_initialize_workspace ... ignored
test e1_single_iteration_smoke ... ignored
test e2_project_boots ... ignored
test e3_behaviour_is_evidenced ... ignored
test e4_verified_claims_are_reproducible ... ignored
test e5_qa_did_not_modify_the_artifact ... ignored
test e6_report_is_honest ... ignored
test result: ok. 0 passed; 0 failed; 7 ignored; 0 measured; 0 filtered out; finished in 0.00s
...
   Doc-tests hof_rs
running 0 tests
test result: ok. 0 passed; 0 failed; 0 ignored; 0 measured; 0 filtered out; finished in 0.00s
EXIT=0
```

逐二进制求和：**352 passed / 0 failed / 7 ignored**，**exit 0**。
与基线对照：**+10 passed**（`tests/dr58_payload_shapes.rs` 5 条 + `tests/evidence_battery.rs` 由 33 → 38），
**failed 0 不变**，**ignored 7 不变（未增长）**。

`cargo build --offline`：`Finished` 且**零 warning / 零 error**（`BUILD_EXIT=0`）。

---

## 2. 三处修正：真机证据 → 原逻辑错在哪 → 改成什么

### 2.1 `running_game_run_test_scenario` 的 `scene_path`（必失败 → 真形状）

**真机证据（文件 + 原始载荷）**

`runs/smoke-t7/iter-1/candidate/.hoh/deterministic/raw/input_channel_probe.json`（本轮 run 自己的记录）：

```json
// calls[4]
"args": {"scene_path":"current","steps":[{"action":"move_right","pressed":true,"type":"input"},
                                         {"seconds":0.0,"type":"wait"},
                                         {"expected":0,"node_path":"Player","property":"input_axis","type":"assert"}]},
"error": {"attempts":1,"code":-32602,
          "message":"Parameter 'scene_path' ('current') is not supported by the game-scope runner: the migration source
                     used it to make the *editor* play a scene before the steps ran, and this tool runs inside the game
                     process that is already running. Use editor_play_scene (editor endpoint) first, then run the
                     scenario against the running game"},
"ok": false
```

`runs/smoke-t7-experiment/scenario/scenario_summary.json`（同一引擎、同一端点的 E3 预检；报告 §2.2 的 C1..C7）：

| 用例 | 请求是否带 `scene_path` | 真实应答 |
|---|---|---|
| C2 | `"scene_path":"main"` | `-32602`：`Parameter 'scene_path' ('main') is not supported by the game-scope runner: …` |
| C3 | `"scene_path":"res://scenes/main.tscn"` | `-32602`：同上，值逐字为 `'res://scenes/main.tscn'` |
| C1 | **省略** | `{"all_passed":false,"completed_steps":1,"duration_ms":5,…,"results":[{"step":0,"type":"wait",…}],"total_steps":1}` |
| C4 | **省略**（hof-rs 自己的 steps） | `{"completed_steps":3,…,"results":[{"action":"move_right","in_input_map":true,"injected":1,"step":0,"type":"input"}, …,{"reason":"node '/root/Main/Player' does not have the property 'input_axis'","passed":false,"step":2,"type":"assert"}]}` |
| C5 | **省略** | `{"completed_steps":2,…,"results":[{"action":"move_right","in_input_map":true,"injected":1,…}, …]}` |

**原逻辑错在哪**：`src/adapter/godot.rs:1597-1604`（DR-54，`6329e5c`）把 `"scene_path":"current"` **硬写**进
`axis_args`。引擎对**任何**取值都回 `-32602` ⇒ 该调用**每次必失败**，`injected` 只能靠
`play_input_recording` 撑、`axis_after` 恒 `None`，探针落到 `ACTION_BINDING_UNKNOWN`。

**改成什么**：请求体只保留 `steps`（去掉 `scene_path`），并把「为何不传」按真实证据写进注释
（现 `src/adapter/godot.rs:1591-1615`）。另外把 Tester 证据手册里的同一错误示例一并改掉
（`src/adapter/godot.rs:3487-3492`，见 §6 第 4 条）。

### 2.2 `running_game_get_node_properties` 的键名（`game_process_reachable` 恒 false）

**真机证据**：`runs/smoke-t7/.../raw/input_channel_probe.json` 的 `calls[0].payload.content[0].text`（成功）：

```json
{"node_path":"/root/Main/Player","properties":{"auto_translate_mode":0,…,"name":"Player",…,
 "position":{"x":60.0,"y":283.998992919922},"velocity":{…}},"type":"CharacterBody2D"}
```

顶层键**只有** `node_path` / `properties` / `type`（`node_path` 是**解析后**的 `/root/Main/Player`；
节点名在 `properties.name`，且只有部分节点类型才有）。同一文件里的原始观测：

```
"game process via semantic tools: reachable=false, axis_before=None, injection accepted=true, axis_after=None,
 axis moved=false; read-only execute_gdscript probe=Some((173.666687011719, 283.998992919922)) (supplementary only, DR-54)"
```

**原逻辑错在哪**：`src/adapter/godot.rs:1253-1257`（DR-54）读**顶层 `name`**：

```rust
game_process_reachable = parsed.get("name").and_then(Value::as_str)
    .map(|name| !name.is_empty()).unwrap_or(false);   // 引擎从不返回该键 ⇒ 恒 false
```

**改成什么**：新增共享判据 `pub fn node_properties_read(payload: &Value) -> bool`
（`src/adapter/godot.rs:2969-2989`），要求**非空 `node_path` 字符串** **且** **非空 `properties` 对象**；
调用点改为 `game_process_reachable = node_properties_read(&parsed);`（现 `:1256`）。

### 2.3 同类历史误读（G20）：`node_and_collision_assertions`

**真机证据**：`runs/smoke-t7/.../raw/node_and_collision_assertions.json` 的 3 条
`running_game_get_node_properties` 调用**全部 `ok:true`**，载荷分别是
`/root/Main/Player`（`"name":"Player"`）、`/root/Main/Goal`（`"name":"Goal"`）、
`/root/Main/HUD`（`"name":"HUD"`），`properties` 字典齐全、`type` 分别为
`CharacterBody2D` / `Area2D` / `CanvasLayer`。而同一步骤写下的观测却是：

```
"node properties: Player=missing, Goal=missing, HUD=missing; collision shape_count: Ground=1, Player=1, Goal=1;
 HUD visible text node(s): 2 (UNAVAILABLE: at least one required node or collision shape is missing)"
```

**原逻辑错在哪**：`src/adapter/godot.rs:2051-2055`（`00601476`，2026-09-21，**既有代码**）与 2.2 **同一模式**
——读顶层 `name` ⇒ 三个必需节点恒判 `missing`，步骤恒 `ok=false`（QA 自己已记为 gap G20）。

**改成什么**：同一个 `node_properties_read`（现 `:2064` 调用）；两处不再各写一份「假设的键名」。

---

## 3. `scene_path` 的真形状：怎么判定的；证据不足时怎么处置

**判定链（全部来自真机载荷，不读契约文档）**

1. 本轮 run 自己的记录：hof-rs 传 `"current"` ⇒ 引擎 `-32602`（§2.1 第一段）。
2. 同一引擎的实验：`"main"` 与 `"res://scenes/main.tscn"` **同样** `-32602`；错误正文逐字说明该参数
   属于「迁移来源」（旧编辑器侧语义），并给出处置：「Use editor_play_scene (editor endpoint) first,
   then run the scenario against the running game」——即**游戏态 runner 不接受任何场景播放参数**。
3. 同一实验里**省略**该成员的 C1/C4/C5 全部返回 `result`（逐步骤结果，含 `in_input_map:true`、`injected:1`）。
   ⇒ 正确形状是 **完全省略 `scene_path`**，只传 `steps`。

**「文档」为什么不能当证据（本批的教训，已固化成测试）**：契约 `tools/list` 里
`running_game_run_test_scenario.inputSchema.properties.scene_path` **确实声明**了 `scene_path`
（optional string），`tests/dr58_payload_shapes.rs::the_real_game_scope_runner_refuses_every_scene_path_value`
专门断言了「文档说有、引擎说不行」——这正是 DR-58 要禁止的推理方式。

**证据不足 ⇒ 停下上报，不换猜法**（本批两处，均**未**改）：

1. `src/adapter/godot.rs:3408`（`build_check`）向 **`editor_play_scene`** 传
   `{"scene_path": self.config.main_scene}`。该工具的**真实 schema** 是
   `extra_args` / `headless` / `mcp_port` / `mode`（**无 `scene_path`**，见
   `tests/fixtures/mcp/tools_list.json`），电池自身的调用形如 `{"mode":"main"}` 且真机成功
   （`runs/smoke-t7/.../raw/play_scene_ready.json`）。但**没有任何捕获**证明 `editor_play_scene`
   会拒绝 `scene_path`，也没有捕获过 `mode` 传 `res://…` 路径的应答 ⇒ **不改**（改就是又一次猜形状）。
   注意它不在电池路径上：`GodotAdapter` 覆写了 `evidence_battery`，`build_check` 只被 trait 默认实现
   或单测使用。
2. 证据手册里的 `"property":"position:x"`（`src/adapter/godot.rs:3490`）。真机 B5
   （`runs/smoke-t7-experiment/semantic/semantic_summary.json`）显示
   `running_game_assert_node_state` 对 `position.x` 回 `-32001
   "Property 'position.x' on node '/root/Main/Player' not found"`，而 scenario 自己的真实 assert 用的是
   `"property":"position"`。但**没有** `run_test_scenario` 带 `position:x` 的捕获 ⇒ 只**记录**，不改。

---

## 4. 固化的夹具清单（来源文件 + sha256）

全部为**逐字节拷贝**（`Copy-Item`，未做任何编辑）；清单位于
`tests/fixtures/dr58/MANIFEST.json`，由 `tests/dr58_payload_shapes.rs` 逐条校验
（夹具自身 sha256；若只读来源仍在，再逐字节比对来源）。

| 夹具（`tests/fixtures/dr58/`） | 来源（`runs/**`，只读） | sha256 |
|---|---|---|
| `smoke_t7_input_channel_probe.json` | `runs/smoke-t7/iter-1/candidate/.hoh/deterministic/raw/input_channel_probe.json` | `ce9ccf9526df7a7a63c42a8f9949a9f838776fcbb44e8629c4672ca28864fdc8` |
| `smoke_t7_node_and_collision_assertions.json` | `runs/smoke-t7/iter-1/candidate/.hoh/deterministic/raw/node_and_collision_assertions.json` | `f8932726c31e0586577905d09f61dda9e97b1de858dfc070f55cbbb4c9224343` |
| `smoke_t7_scenario_summary.json` | `runs/smoke-t7-experiment/scenario/scenario_summary.json` | `9bfc568dfff305e369b39c9e760cd52956652a3934e8a04c53e79fe5339efb8e` |
| `smoke_t7_sc_02_scene_path_main.json` | `runs/smoke-t7-experiment/scenario/sc-02.json` | `a379e4cd0cc8367b0000ce784465199e64ffe3160a88f3a01dafed6c699a84c3` |
| `smoke_t7_sc_04_scene_path_omitted.json` | `runs/smoke-t7-experiment/scenario/sc-04.json` | `ecbda5b6d107160bdf994ad26b399cf5c5feb0c577f3a089ace15d9151d791ac` |
| `smoke_t7_sc_05_scene_path_omitted.json` | `runs/smoke-t7-experiment/scenario/sc-05.json` | `481c730379d708ce47a179afad2b9ee724423f89290fb4f4975944c4ba5913e8` |
| `smoke_t7_sc_07_assert_only_position.json` | `runs/smoke-t7-experiment/scenario/sc-07.json` | `03f86916d428912272a91471ab4c98961377c37c2b346648a3fe0b269f50f7e6` |

**两个必须说明的字节事实**（诚实记录）：

- 6 个 `sc-*` / `scenario_summary` 来源在磁盘上是 **CRLF**，`input_channel_probe` /
  `node_and_collision_assertions` 是 **LF**。manifest 的 sha256 就是**这些原始字节**的摘要
  （拷贝未做任何换行转换）。为避免 checkout 时被 Git 自动转换，新增 `.gitattributes`
  （`tests/fixtures/dr58/** -text`）并把索引按**精确字节**重新落库
  （`git ls-files --eol` 现为 `i/lf w/lf` 与 `i/crlf w/crlf`）。
- `runs/smoke-t7-experiment/semantic/semantic_summary.json` 同样是真机证据，但**没有**固化：
  本批测试不需要它，而它的 `label` 描述里含退役的 GDExtension 时代工具名
  （`run_test_scenario` / `assert_node_state`），会触发 DR-45 词汇守卫
  （`tests/tool_vocabulary.rs`）。**选择丢弃未使用的拷贝，而不是把文件从守卫里排除** ——
  守卫范围因此没有被人为放宽。缘由写进了 `MANIFEST.json` 的 `note`。

---

## 5. TDD 与反例证据（红 → 绿 → 重构；每处非空洞）

严格按「先红、确认因真实形状而红、最小实现转绿、全绿下重构」执行；**未放宽任何既有断言**——
相反，`FixtureChannel` 被改成**更严**（喂真实字节、执行引擎的真实拒绝）。

### 5.1 红（三处，真实失败输出）

**红 ①（scene_path）**：`cargo test --offline --test evidence_battery the_scenario_request_omits_scene_path`

```
test the_scenario_request_omits_scene_path_because_the_runner_refuses_every_value ... FAILED
thread '...' panicked at tests\evidence_battery.rs:2058:9:
the game-scope runner refuses every scene_path value (DR-58):
{"scene_path":"current","steps":[{"action":"move_right","pressed":true,"type":"input"},
 {"seconds":0.0,"type":"wait"},{"expected":0,"node_path":"Player","property":"input_axis","type":"assert"}]}
test result: FAILED. 0 passed; 1 failed; 0 ignored; 0 measured
```

**红 ②（G20）**：把 `FixtureChannel` 的 `running_game_get_node_properties` 应答换成
`smoke_t7_node_and_collision_assertions.json` 里的**原样 payload** 后：

```
test green_battery_records_every_step_and_copies_into_the_candidate ... FAILED
thread '...' panicked at tests\evidence_battery.rs:912:9:
step node_and_collision_assertions failed: ExecRecord { ... observation:
"node properties: Player=missing, Goal=missing, HUD=missing; collision shape_count: Ground=1, Player=1, Goal=1;
 HUD visible text node(s): 1 (UNAVAILABLE: at least one required node or collision shape is missing)" }
```

这正是 G20 的**原样复现**：载荷成功、却被读成 `missing`。

**红 ③（reachability）**：`cargo test --offline --test evidence_battery a_real_node_properties_reply_makes_the_game_process_reachable`

```
test a_real_node_properties_reply_makes_the_game_process_reachable ... FAILED
thread '...' panicked at tests\evidence_battery.rs:1333:5:
assertion `left == right` failed: the real node-properties reply proves the game process:
"the game-process probe could not be read (no semantic reading arrived) ; project.godot declares none of
 move_left/move_right/jump; game process via semantic tools: reachable=false, axis_before=None,
 injection accepted=true, axis_after=None, axis moved=false; read-only execute_gdscript probe=Some((80.0, 283.999))
 (supplementary only, DR-54)"
  left: Bool(false)   right: Bool(true)
```

测试夹具在该模式下改用**真实**的 `input_axis:null` 采样与**真实**的 scenario 应答
（`smoke_t7_sc_04_...`），因此 `axis_before=axis_after=None` —— reachability 只能来自
`get_node_properties`，红即来自该处误读。

### 5.2 绿

三处分别转绿后：

```
test result: ok. 38 passed; 0 failed; 0 ignored; 0 measured; 0 filtered out; finished in 82.01s   (tests\evidence_battery.rs)
test result: ok. 5 passed; 0 failed; 0 ignored; 0 measured; 0 filtered out; finished in 0.01s    (tests\dr58_payload_shapes.rs)
```

全量：**352 passed / 0 failed / 7 ignored**，exit 0（§1）。

### 5.3 重构

- 两处重复的「顶层 `name`」判据（`:1253`、`:2051`）收敛为**同一个** `node_properties_read`，无第二份形状假设。
- `FixtureChannel` 的 scene_path 拒绝、节点应答、`input_axis:null` 采样、scenario 应答全部改为
  **执行引擎的真实字节/真实语义**，杜绝「双份形状」漂移。
- 新增 `.gitattributes` 固定夹具字节。

### 5.4 非空洞反例（每处一条；把判据改成恒真/恒假 ⇒ 必变红）

| 修正 | 反例（测试） | 反例断言（判据不能是常量） |
|---|---|---|
| scene_path | `the_scenario_request_omits_scene_path_because_the_runner_refuses_every_value` | 部强制的双份改为「带 `scene_path` 的**错误**形状必须被拒」，并逐字要求引擎原话 `scene_path_refusal("current")`；若把判据改成恒真（照发 `scene_path`），该测试立刻红（红①即其反例形态） |
| 节点键名 / G20 | `an_unresolved_or_malformed_node_read_is_not_a_resolved_read`（11 种畸形：`{}`、`{"name":"Player"}`、退役扁平夹具、缺 `properties`、空 `properties`、缺 `node_path`、空白 `node_path`、`node_path` 非字符串、`properties` 非对象、`null`、`[]`）+ `a_malformed_node_properties_payload_is_still_scored_as_missing` | 同一调用点：真实载荷 ⇒ `true`；上述任一 ⇒ `false`，且步骤仍 `Player=missing`、`ok=false`。恒 true 会让第二条红；恒 false 会让真实载荷那条红 |
| reachability | `a_malformed_node_properties_reply_does_not_prove_the_game_process` | 同样的真实 `input_axis:null` + scenario 应答下，畸形节点回包 ⇒ `game_process_reachable=false` 且 `capability=ACTION_BINDING_UNKNOWN`。**没有**为了「让 E3 好看」把 reachable 改成恒 true |

`node_properties_read` 的**非空洞性**另由 `tests/dr58_payload_shapes.rs` 直接锁住（真实 3 节点 + probe 的
Player 载荷全 `true`；11 种畸形全 `false`）。

---

## 6. 全仓「同一模式」误读扫描结果

扫描口径：引擎应答层的**顶层键名/参数名假设**（`grep -n '\.get("…")' src/**`、`grep -n 'get("name")' src/**`、
`grep -n 'scene_path' src/**`）。

| 位置（本批后行号） | 读取/假设 | 判定 | 处置 |
|---|---|---|---|
| `src/adapter/godot.rs:1256`（原 `:1253`） | 顶层 `name` 判可达 | **同模式缺陷**（DR-54） | **已修**（`node_properties_read`） |
| `src/adapter/godot.rs:2064`（原 `:2051`） | 顶层 `name` 判节点存在 | **同模式缺陷**（G20 / `00601476`） | **已修**（同一判据） |
| `src/adapter/godot.rs:3487-3492`（证据手册文本） | `scenario.json` 示例含 `"scene_path":"current"` | **同模式误读的文档形态**（会让 Tester 照抄必失败形状） | **已修**（同一条真机证据；纯文本） |
| `src/adapter/godot.rs:3408`（`build_check`） | 向 `editor_play_scene` 传 `{"scene_path": …}` | **同模式候选（参数名假设）** | **未改**：无任何捕获证明 `editor_play_scene` 会拒绝该参数、也无捕获过 `mode=res://…`。按任务书「证据不足 ⇒ 停下上报」。另：`GodotAdapter` 覆写了 `evidence_battery`，该函数不在电池路径上 |
| `src/adapter/godot.rs:3490`（证据手册文本） | assert 示例 `"property":"position:x"` | **候选（键值域假设）** | **未改**：B5 只证明 `running_game_assert_node_state` 拒绝 `position.x`；scenario 的真实 assert 用的是 `position`。无 `run_test_scenario` 侧的 `position:x` 捕获 ⇒ 记录不改 |
| `src/adapter/godot.rs:2912-2917`（`scenario_axis`）、`:2948`（`observed_after`） | 多候选键 `results/steps/observations`、`observed/actual/value` | **非缺陷**：宽容读法只可能读不到（`None`），不会产出错误结论 | 不改 |
| `src/adapter/godot.rs:2528`（`editor_get_input_actions` 解析） | 数组元素 `name`/`action`，且先接受字符串数组 | **已在 DR-52 修过**的同族问题；现为双形状且缺键只跳过 | 不改 |
| `src/adapter/godot.rs:2215-2239`（`editor_play_scene` 应答）、`:2257-2292`/`:3056-3076`（scene tree） | `endpoint/mcp_port/pid`、`tree/children/path/type` | 与真机载荷一致（`play_scene_ready.json`、`scene_tree.json` 实测） | 不改 |
| `src/tools/index.rs:36`、`src/tools/mcp.rs:359/379` | `tools/list` 条目 `name` | **不是误读**：这正是真实形状（`tests/fixtures/mcp/tools_list.json`） | 不改 |

**结论**：DR-58 的两处代码缺陷已消除；扫描额外发现**两处**同模式位置（1 处文档形态已修，1 处参数名候选上报）；
其余 `.get(...)` 读法要么与真机载荷一致，要么只可能保守地读不到。

---

## 7. 禁区自查（真实输出）

```text
$ git status --porcelain godot-mcp
(空)
$ git diff --stat 3c10663 HEAD -- godot-mcp
(空)
$ git diff --stat 3c10663 HEAD -- .spec/hof-rs/PRD-mario.md
(空)
$ (Get-FileHash -Algorithm SHA256 '.spec\hof-rs\PRD-mario.md').Hash.ToLower()
4c81c3a9995f0b3afdf01421a0c3be88573cceefc284ce9bafbfda141f0f5c3a      # 与 doctor/T7 报告记录一致
$ git diff --stat 3c10663 HEAD -- Cargo.toml Cargo.lock
(空)                                                                    # 无新依赖
$ foreach ($d in 'runs\smoke-t6','runs\smoke-t7') { …count/latest mtime… }
runs\smoke-t6 files=135 latest=2026-09-29 02:32:01 (meta.json)          # 与 T7 报告 §6 记录逐字一致
runs\smoke-t7 files=115 latest=2026-09-29 14:41:14 (meta.json)          # 与我开工前记录一致
$ git ls-files runs | Measure-Object | Select-Object -ExpandProperty Count
0
$ git check-ignore -v runs
.gitignore:12:runs/	runs                                              # runs/ 不受版本管理，故以上计数/时间戳为证
$ git status -sb
## master...origin/master [ahead 7]                                     # 未 push
```

- **未改** `godot-mcp/**`、`.spec/hof-rs/PRD-mario.md`、`runs/**`（后者只读引用：`Copy-Item` 单向拷出、
  只读 hash 校验；`smoke-t6` 135 文件 / `smoke-t7` 115 文件与记录一致）。
- **无新依赖**（`Cargo.toml`/`Cargo.lock` 零 diff；sha256 用仓内已有的 `sha2`/`hof_rs::runtime::policy::sha256_hex`）。
- **未 push**（`ahead 7`，7 条本批提交）。
- **离线**：本批只跑 `cargo`（offline）、`git`、文件读写；**未**启动 Godot、**未**触碰任何端口、
  **未**联网、**未**调任何模型端点。
- **未编造**：本报告所有引文与数字均来自上列文件/命令的真实输出。

### 本批提交（每条带 `(DR-58)`，英文信息，串行构建）

```
a345ac9 fix(DR-58): omit scene_path from running_game_run_test_scenario, whose real game-scope runner refuses every value
eb2c4ca chore(DR-58): pin the frozen real-machine fixtures against CRLF conversion
4501d15 chore(DR-58): store the frozen fixtures as the exact bytes they hash to
5232769 fix(DR-58): judge a node-properties read by the real node_path+properties shape (G20)
5809f2a fix(DR-58): prove game-process reachability from the real node-properties shape
99ab7c7 docs(DR-58): stop teaching the rejected scene_path shape in the Tester playbook
856e9df chore(DR-58): do not freeze the unused semantic_summary capture
```

---

## 8. 遗留风险与未验证项（严格区分「实测」/「推断」）

**本批实测（有本批可复核输出）**

1. 三处形状均按真机载荷改对；全文 352/0/7、exit 0；构建零 warning。
2. 夹具逐字节等于只读来源（`tests/dr58_payload_shapes.rs` 在来源存在时再比对一次）。
3. `runs/**`、`godot-mcp/**`、PRD、`Cargo.*` 均未被本批改动；未 push。
4. `FixtureChannel` 现在会**拒绝**带 `scene_path` 的请求（双份与真机一致），旧形状在测试里必红。

**推断（不得当作已证）**

1. **E3 依旧未判定**：`running_game_run_test_scenario` 现在会**真的被接受**（推断），但
   `input_axis` 属性在真机上每帧回 `null`、scenario 的 assert 明说
   `node '/root/Main/Player' does not have the property 'input_axis'` ⇒ `axis_before/axis_after`
   仍会是 `None`、`moved_while_pressed` 仍为 `false`。修好 ①② 后探针**可能**判
   `GAME_INPUT_CHANNEL_OK`（`injection accepted=true` + `in_game_process_reachable=true`），
   但**这只能由下一次真机轮次确认**；本报告**不声称 E3 met**。
2. `editor_play_scene` 的 `scene_path` 参数是否真被拒绝 = **未知**（无捕获）；`mode=res://…` 是否可行 = **未知**。
3. 手册示例 `"property":"position:x"` 在 `run_test_scenario` 下是否被拒 = **未知**（B5 只覆盖 `assert_node_state`）。
4. 测试替身的默认 `AxisMode::Value` 仍带合成的 `observed`（既有行为，本批未动）；只有 `AxisMode::Unreadable`
   用真实字节。即：默认绿路径的 scenario 应答**不是**真机字节。

**未关闭（应回上游/回设计）**

1. `build_check` 的 `editor_play_scene {"scene_path": …}`（上表候选）——需要一次活体捕获才能定形状。
2. 旧的扁平形状夹具 `tests/fixtures/mcp/{player,goal,hud}_properties.json`（含顶层 `name`/`node_path`，
   与真机形状不一致）：本批后**只剩** `player_properties.json` 仍被 `tests/mcp_desync.rs:371` 当作应答
   使用（`goal_/hud_properties.json` 已无任何引用）。它们**不再**被任何「节点是否存在」的判据读取
   （本批已切断调用），但作为历史捕获与真机形状不一致，建议上游决定是否退役。
3. T7 报告 §7 其它未关闭项（`input_replay` 可归因性、跨轮陈旧证据 DR-59、D239）本批**未触及**。

---

## 9. 诚实披露

1. **基线首跑异常，如实记录**：本批开工时的第一次 `cargo test --offline`
   （输出经 `Select-Object -Last 40` 截断）返回 **exit 1**；我用同样命令重跑一次，得到
   **342/0/7、exit 0**，并以该次为基线。首跑我**没有**保留完整日志，因此**无法**指出是哪一个测试
   失败；它没有在随后任何一次全量/定向运行中复现。这是一个**未能定性的偶发**，不是被掩盖的红。
2. **我一开始多固化了 `semantic_summary.json`**，随后被 `tests/tool_vocabulary.rs`（DR-45 守卫）判红：
   其 `label` 里含退役工具名。我选择**删除这个未被任何测试使用的拷贝**，而不是把文件加入守卫的
   排除名单——后者会实质放宽现有守卫。缘由写进 `MANIFEST.json` 的 `note`。
3. **CRLF 事件**：6 个来源本身是 CRLF，第一次提交时 Git 按 autocrlf 归一了索引，导致索引与工作树
   字节不一致。我新增 `.gitattributes`（`tests/fixtures/dr58/** -text`）并把索引按精确字节重新落库
   （`git ls-files --eol` 已确认 `w/crlf` 与 `i/crlf` 一致）。**两个额外提交**（`eb2c4ca`、`4501d15`）
   就是为此，属"为保住逐字节冻结"的必要修正。
4. **本批改了第 4 处同模式位置**（证据手册里的 `scene_path` 示例，`99ab7c7`）：它是任务书要求的
   「顺便扫描」发现的，同一工具、同一条真机证据、纯文本改动，不涉及新形状假设。
   §6 另两条候选（`build_check`、`position:x`）我**按纪律不猜、只上报**。
5. **我没有改** `DECISIONS.md`/设计文档（那是决策者的工件）；本批只动
   `src/adapter/godot.rs` 的三处读法 + 一段手册文本、测试、夹具、`.gitattributes`。
6. **禁止事项声明**：未启动 Godot、未碰端口、未联网、未调模型端点、未 push、未改 `godot-mcp/**`、
   未改 `runs/**`、未新增依赖、未放宽任何既有断言。
7. **报告本身也是一次提交**（`docs(DR-58): implementation report`），因此 `git status` 会多一条本批提交；
   §7 的 `ahead 7` 是报告落库前的读数。
