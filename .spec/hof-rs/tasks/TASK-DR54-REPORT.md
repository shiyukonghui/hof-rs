# TASK-DR54-REPORT — §15 实现批次（DR-54 / DR-55 / DR-56）

- 任务书：`.spec/hof-rs/tasks/TASK-DR54-IMPL.md`
- 规范：`.spec/hof-rs/DESIGN-DETAIL.md` **§15（v0.10）**
- 需求：`.spec/hof-rs/REQUIREMENTS.md` v0.3；决策：`DECISIONS.md` D220/D221/D222/D223/D231、D234
- 落点：`F:\moonbit-hof-rs`（`master`）；**离线批次**：未启动 Godot、未碰任何端口、未联网、未调模型端点
- 报告日期：2026-09-29（与批次提交日期一致，未编造）
- **本批不断言 E3 已 met**；E3 只能由真机轮次判定（§15.4）

---

## 0. 结论

**三条 DR 全部实现、离线判据全绿、无可上报的无法映射项。**

| DR | 内容 | 离线判定 |
|---|---|---|
| DR-54 | E3 关键路径改建立在契约语义工具上；`execute_gdscript` 降级为只读探针 | **pass**（映射表 §2；语义工具承重被 §5/§6 证明非空洞） |
| DR-55 | 同一端点连续 2 次传输失败 ⇒ 判死，其后 `running_game_*` 立即 `UNAVAILABLE`、零重试 | **pass**（状态机 §3；5 条 test 全绿，2 条受控植入转红） |
| DR-56 | 上层重试按类别：业务错误恰尝试一次 | **pass**（分类函数 §4；3 条 test 全绿，2 条受控植入转红） |

**门（真实尾部输出与退出码）**

命令：`cargo test --offline`（工作树干净、无植入残留）：

```
     Running tests\wrap_up_budget.rs (target\debug\deps\wrap_up_budget-48d6de538feb9569.exe)
running 10 tests
test result: ok. 10 passed; 0 failed; 0 ignored; 0 measured; 0 filtered out; finished in 15.19s
     Running tests\godot_smoke.rs (target\debug\deps\godot_smoke-ca0899427b15ce87.exe)
running 7 tests
test result: ok. 0 passed; 0 failed; 7 ignored; 0 measured; 0 filtered out; finished in 0.00s
   Doc-tests hof_rs
running 0 tests
test result: ok. 0 passed; 0 failed; 0 ignored; 0 measured; 0 filtered out; finished in 0.00s

EXIT=0
```

逐 target 汇总（35 个 test target 全 `ok`，无非零 `failed`）：

| 项 | 基线（批次开始，`53f6f9d`） | 本批结束（`b3ccef9`） |
|---|---|---|
| **passed** | **328** | **342**（+14，全部是本批新增） |
| **failed** | 0 | **0** |
| **ignored** | **7** | **7**（**未增加**；仍全部来自 `tests/godot_smoke.rs` 的真机门控） |
| exit code | 0 | **0** |

新增 14 条：DR-56 在 `tests/mcp_reliability.rs` +2（并**改写** 1 条既有测试，见 §4.3）；DR-55 新建 `tests/endpoint_liveness.rs` 7 条 + `src/tools/endpoint.rs` 内 2 条单测；DR-54 在 `tests/evidence_battery.rs` +3（并**改写** 2 条既有测试，见 §4.3）。

**提交（5 个本地提交，英文信息带 DR 号，未 push）**

| commit | 内容 |
|---|---|
| `513069c` | DR-56 重试按类别 |
| `df95339` | DR-55 端点连续 2 次传输失败判死 |
| `6329e5c` | DR-54 E3 建立在语义工具上 |
| `b3ccef9` | 非空洞性受控植入-回退证据（含报告前清理） |

---

## 1. 目标

按 §15 改造 hof-rs，使：①E3 的每条关键断言由契约（177 条）的**语义专用工具**的真实调用产出，`running_game_execute_gdscript` 仅保留为只读探针；②游戏端点连续两次传输失败后快速失败；③上层重试环按类别（业务错误永不重试）。范围 `src/**`、`tests/**`；不改 `godot-mcp/**`、不改 `PRD-mario.md`、不写 `runs/smoke-t6/**`。

---

## 2. DR-54 的映射表（第一步硬要求的产出）

### 2.1 枚举方法

`rg`/`Select-String` 全仓扫 `running_game_execute_gdscript`，再逐点回溯到 E3 关键路径的调用者。E3 的关键路径 = 证据电池的 `input_channel_probe` + `input_replay` 两步（`input_replay` 的 F1/F2/F3 判定**读取** probe 的 `capability`），加上 `node_and_collision_assertions` 的 F5/F6/F13/F16。逐点结论：**改造前，全部 11 处承重调用点都在 `src/adapter/godot.rs`，全部支撑 F1/F2/F3；F5/F6/F13/F16 侧本来就不用 `execute_gdscript`**。

（下表行号取自批次起点 `53f6f9d` 的 `src/adapter/godot.rs`，用 `git show 53f6f9d:src/adapter/godot.rs` 逐行核对过。）

### 2.2 改造前：每个可达调用点 → 接替它的语义工具

| # | 文件:行（改造前，`53f6f9d`） | 调用形态 | 支撑 E3 的哪条断言 | 接替它的语义工具 | 结果 |
|---|---|---|---|---|---|
| 1 | `src/adapter/godot.rs:1234`（`game_script`） | `return str(get_tree()…Player.position …)` | `input_channel_probe` 的"游戏进程可达" | `running_game_get_node_properties` | **已接替**（`semantic::NODE_PROPERTIES`） |
| 2 | `src/adapter/godot.rs:1247`（`game_script_bool`） | `return str(InputMap.has_action("move_right"))` | `input_channel_probe` 的 `ACTION_NOT_BOUND` 判据 | `running_game_run_test_scenario`（`input` 步骤 + `assert` 步骤；`ACTION_NOT_BOUND` 改由语义拒绝的 `-32602` **答案**得出） | **已接替** |
| 3 | `src/adapter/godot.rs:1251`（`game_script_bool`） | `return str(Input.is_action_pressed("move_right"))` | probe 的按下前置读数 | `running_game_run_test_scenario`（`input` 步骤的 `pressed`）+ `running_game_get_node_property_samples` | **已接替** |
| 4 | `src/adapter/godot.rs:1255`（`game_script_f64`） | `return str(Input.get_axis("move_left","move_right"))` | probe 的 axis-before 读数 | `running_game_get_node_property_samples`（语义轴读数） | **已接替** |
| 5 | `src/adapter/godot.rs:1262`（`game_script_present`） | `Input.action_press("move_right")` | probe 的**注入** | `running_game_create_input_recording` + `running_game_play_input_recording` + `running_game_run_test_scenario` | **已接替** |
| 6 | `src/adapter/godot.rs:1298`（`game_script_f64`） | `return str(Input.get_axis(…))`（注入后） | probe 的 axis-after 读数 | `running_game_get_node_property_samples` + `running_game_run_test_scenario` 的 `assert`/`observed_axis` | **已接替** |
| 7 | `src/adapter/godot.rs:1302`（`game_script`） | 同 #1（`player_position_after`） | probe 的"按下后位置变了" | `running_game_get_node_property_samples`（`before_position`/`after_position` 四元组） | **已接替** |
| 8 | `src/adapter/godot.rs:1311`（`game_script_present`） | `Input.action_release("move_right")` | probe 的释放（避免状态泄漏到 replay） | `running_game_run_test_scenario`（`pressed:false`）+ `running_game_stop_input_recording` | **已接替** |
| 9 | `src/adapter/godot.rs:1645`（`game_script_present`，位于 `for (label, action, frames, expect_movement)` 循环内） | `Input.action_press(<action>)`，循环 4 轮（move_right / move_right_release / jump / move_left） | `input_replay` 的 F1/F2/F3 注入 | `running_game_create_input_recording` + `running_game_play_input_recording` + `running_game_run_test_scenario` | **已接替** |
| 10 | `src/adapter/godot.rs:1774`（`game_script_f64`，同循环内） | `return str(Input.get_axis(…))`，4 轮 | replay 的动作后轴读数 | `running_game_get_node_property_samples` | **已接替** |
| 11 | `src/adapter/godot.rs:1783`（`game_script_present`，同循环内） | `Input.action_release(<action>)`，4 轮 | replay 的释放 | `running_game_run_test_scenario`（`pressed:false`）+ `running_game_stop_input_recording` | **已接替** |

（#9–#11 是**一行源码**在四轮循环里各执行一次，故"调用点"按源码行计为 3 处、按运行时调用计为 4 次/行。）

位置 `src/adapter/godot.rs`（`53f6f9d`）的 `1271-1296`（`running_game_get_node_property_samples`）与 `1874`（`editor_get_collision_info`）本来就**不是** `execute_gdscript` 调用点，列此以免误读：它们是电池原有的语义/编辑器工具调用，本批未改其承重地位。

**无法映射的调用点：0 处。** 11 个承重调用点全部有语义工具接替，无需上报。

### 2.3 改造后：剩余的 `execute_gdscript` 调用点（唯一一处，只读）

| 文件:行（改造后，`b3ccef9`） | 形态 | 地位 | 证明 |
|---|---|---|---|
| `src/adapter/godot.rs:1472`（`BatterySession::game_script`，唯一执行点） | `running_game_execute_gdscript` | 通用只读探针执行器（保留） | 它只被下面一个调用点使用 |
| `src/adapter/godot.rs:1311-1316`（`step_input_channel_probe` 内的 `read_only_player_position` 标签） | `probe_scripts::player_position()` → `return str(get_tree()…position.x) + "," + str(…)` | **只读探针**：基类是临时 Node，只读 `position`，无副作用 | §5.3 的 `a_semantic_refusal_is_not_rescued_by_the_gdscript_probe`：语义工具全部拒绝时，本探针**仍然回答成功**，而判定仍是 `ACTION_BINDING_UNKNOWN` |

`input_replay` 中不再有任何 `execute_gdscript` 调用（`tests/evidence_battery.rs` 的 `the_input_replay_injection_is_semantic_not_gdscript` 断言注入只经语义 API；`every_surviving_execute_gdscript_call_is_a_gdscript_body` 断言残留脚本既**带 `return`** 又**不含 `Input.action_press(`/`release(`**）。

### 2.4 §15.1 判据的逐条核对

| §15.1 要求 | 落实 | 证据 |
|---|---|---|
| E3 每条关键断言能指向语义工具的真实调用与其证据 | `input_channel_probe` / `input_replay` 的每次判定都由 `get_node_properties` / `get_node_property_samples` / `create_input_recording` / `play_input_recording` / `run_test_scenario` / `stop_input_recording` 产出并逐字入库 | §5.1、§5.2 |
| `execute_gdscript` 不再是关键路径承重件 | 唯一残留点是只读探针，判定函数**不读它的返回值**（`evidence_note` 只把它写进诊断文本） | §5.3 的"语义拒绝但脚本探针成功 ⇒ 仍判 UNKNOWN" |
| 凡仍在用：`code` 必须是函数体且带 `return`（DR-50A） | `probe_scripts::player_position()` 以 `return ` 开头；测试断言 | §6 的 nv7 |
| 禁止发送编译不过的 `code` | 残留 `code` 是常量（`probe_scripts` 的字符串），**不由模型生成**；`Input.action_press`/`release` 作为语句的旧写法已从关键路径删除 | §6 的 nv7（植入裸表达式 ⇒ 转红） |

---

## 3. DR-55 的状态机

### 3.1 字段名（稳定证据字段）

落点 `src/tools/endpoint.rs`：`EndpointLiveness`（`Serialize`/`Deserialize`），**逐字**字段：

| 字段 | 类型 | 含义 |
|---|---|---|
| `endpoint` | string | 该判定所属的端点（JSON-RPC URL） |
| `state` | `"alive"` \| `"unavailable"` | 稳定判定字段（`EndpointState`，`snake_case`） |
| `unavailable` | bool | 与 `state` 冗余但**可直接查询**的布尔（判死即 `true`） |
| `consecutive_transport_failures` | u32 | 当前**连续**传输失败计数（成功清零；业务错误不触碰） |
| `transport_failures_at_mark` | u32 | 判死**当刻**的计数（"共几次失败"永远可答） |

阈值：`pub const ENDPOINT_DEATH_THRESHOLD: u32 = 2;`（`src/tools/endpoint.rs:81`）。

### 3.2 判死条件与状态转移

```
alive --Ok(任何应答，含业务错误)--> alive（count := 0）
alive --Err(传输失败)--> alive(count := count+1)   // count < 2
alive --Err(传输失败)--> unavailable(count = at_mark = 2)   // count >= 2
unavailable --任何事件--> unavailable（count / at_mark 冻结）
```

- **只**由 `McpTransportError`（`src/tools/mcp.rs` 的具名传输失败类型）驱动 `Err`；`Ok` 覆盖**一切应答**，包括 `-32602` 这类业务错误 —— 这是 DR-55/DR-56 的接缝（§6 的 nv5 证明它非空洞）。
- 判死后 `McpChannel::call_with_meta` 在任何请求发出**之前**返回 `McpEndpointUnavailableError`（`src/tools/endpoint.rs`），其文本含 `UNAVAILABLE`、`game_endpoint_unavailable`、`endpoint_state=<json>`、`attempt(s)=0`，并**打印**"何时判死、共几次失败"（CLI 桥 `tools_call` 把该错误直接透出）。
- **零重试的证据**：判死路径不进入 `spawn_blocking` 调用，也不进入上层重试环（该失败被 `failure_from` 标为 `endpoint_verdict = true`，`another_attempt_is_allowed` 对其返回 `false`）。测试 `two_transport_failures_kill_the_endpoint_and_later_calls_do_not_retry` 用 **`max_retries = 3`** 调用三次，断言 `failure.attempts == 1`。
  - <a id="dr57-correction"></a>**DR-57 更正（本条被独立验收 DEF-1 推翻，原文与更正都留在这里，不删改）：**
    - **原文（本报告 §3.2 在 DR-57 之前的措辞，逐字引述）**：
      > 断言 `failure.attempts == 1` 且 `endpoint_state.consecutive_transport_failures` 仍为 2（**计数不再增长 ⇒ 确实没再发请求**）。
    - **更正后的措辞**：
      > `failure.attempts == 1` 只证明这条调用**不再重试**。它**不**证明"没有发请求"：要证明零请求，必须由**独立计数替身**在**传输层**（`McpClient::post` 真正建立 TCP 连接的那一层、也就是 `EndpointLiveness` 判定**之前**）计次，并断言判死后该计次**不增**。本报告写作时没有这样的计数：`tests/endpoint_liveness.rs::two_transport_failures_kill_the_endpoint_and_later_calls_do_not_retry` 用的是**已关闭端口**的对偶，因此它**根本无法**数到请求。DR-57 新增的计数测试是
      > `tests/endpoint_request_count.rs::a_dead_endpoint_sends_zero_requests_to_the_transport_layer`：活的 loopback 替身在自己的 **accept 路径**上计次（先以"收下连接、一个字节不回"的形态制造两次真实传输失败把端点判死，再把替身切成**完全健康**），随后三次调用断言 accept 计数**纹丝不动**（实测 5 == 5），并以"重注册后下一次调用恰好 +1"作为计数器的活对照。同一测试在"判死后仍发一次请求"与"判死短路被整段删除"两种受控植入下都转红（`EXIT=101`，DR-57 报告 §3）。
    - **原推理为何无效**：`EndpointLiveness::observe` 在 `unavailable` 时**第一行就 `return`**（`src/tools/endpoint.rs` 的 `if self.unavailable { return; }`），而 `call_with_meta` 也只在 `Err` 分支里调用它。所以只要端点已判死，`consecutive_transport_failures` **在构造上被冻结在 `transport_failures_at_mark`**，与"之后是否仍发请求"完全无关——它是一个恒等式，不是一个观测。用它推断因果是**循环论证**。独立验收者（`TASK-DR54-ACCEPTANCE.md` §3 实验 B）把"判死后仍发一次请求"植入后，本条测试**仍然绿**，只有验收者自写的计数测试转红；行为本身是对的，缺的是**证据有效性与覆盖**。
- **首次失败不判死**：`a_single_transport_failure_does_not_kill_the_endpoint`（`max_retries = 0`，1 次失败 ⇒ `unavailable == false`、count == 1）。
- **业务错误不计入**：`business_errors_never_count_toward_the_streak` 让真实 loopback 对偶返回 **3 次 `-32602`**，每轮断言 `failure.code == Some(-32602)`（是真业务错误，不是传输失败）且 `count == 0`；随后关掉对偶，1 次传输失败后 `count == 1`（若三次业务错误计入过，这里会是 2 或直接判死）。
- **重注册重新武装**：`register_game_endpoint` 对新地址 `arm_endpoint`（`EndpointLiveness::new`），旧地址的判死不泄漏到新端点（`registering_a_new_endpoint_re_arms_the_route`）。
- **端点各自独立**：`the_editor_endpoint_state_is_separate`（游戏端点判死后编辑器端点仍 `alive` 且照常工作）。
- **ready 轮询**：`wait_for_game_ready` 遇到 `endpoint_verdict`（未发请求的判死拒绝）立即返回；**业务错误仍继续轮询** —— 这是 DR-20 的既有性质（游戏没起来时引擎就回 `-32603 等待游戏响应超时`），我最初的实现把它一起停了，被既有测试 `readiness_poll_succeeds_after_three_failures` 抓住并改正（见 §9）。

---

## 4. DR-56

### 4.1 分类函数落点（集中在一个具名函数里）

| 项 | 落点 |
|---|---|
| 分类判据（**唯一**决定者） | `src/tools/reliable.rs::is_retryable_failure(&McpFailure) -> bool`（读 `McpFailure.retryable`） |
| 分类的**赋值点**（唯一） | `src/tools/reliable.rs::failure_from`（`McpError` ⇒ 不重试；`McpTransportError` ⇒ 重试；`McpEndpointUnavailableError` ⇒ 不重试且 `endpoint_verdict = true`；其它 ⇒ 不重试） |
| 消费点（唯一） | `src/tools/reliable.rs::another_attempt_is_allowed(attempt, total, last)`，由 `call_with_retries_traced` 调用 |
| 传输失败的具名类型 | `src/tools/mcp.rs::McpTransportError { endpoint, message }`（`post()` 的传输失败路径构造它） |

`is_retryable_failure` 只回答"能否再试一次"，不散落特例；`call_with_retries_traced` 在每次失败后由该函数决定继续或结束。

### 4.2 判据核对（§15.3 / §4）

| 判据 | 测试 | 结果 |
|---|---|---|
| ①业务错误恰尝试 1 次（断言真实调用次数） | `mcp_reliability::retries_are_class_aware_business_errors_are_never_retried`：`-32602`，`max_retries = 2`，断言 `channel.call_count() == 1`、`failure.attempts == 1`、`failure.code == Some(-32602)`、`mcp-errors.jsonl` 恰 1 行 | 绿 |
| ②传输失败仍重试（次数 > 1） | `mcp_reliability::the_retry_classifier_is_the_single_decider`：传输失败，`max_retries = 3`，断言 `call_count() == 4` | 绿 |
| ③分类函数有独立单测 + 反例 | 同 ② 的**双向**断言：传输失败可重试；无分类的普通错误**不**重试（`call_count() == 1`）；非空洞由 nv1/nv2/nv6 证明 | 绿 |
| ④"返回最后一次真实失败"未被破坏 | `retries_are_bounded_and_preserve_the_real_error`：3 次传输失败后 `attempts == 3`、`message` 含最后一次的真实文本、`code == None` | 绿 |

### 4.3 被改动的既有断言（逐条"原/新/为什么语义等价"）

| 文件:测试 | 原断言 | 新断言 | 为什么语义等价 / 为什么必须改 |
|---|---|---|---|
| `tests/mcp_reliability.rs:retries_are_bounded_and_preserve_the_real_error` | 三次 `McpError(-32603, …)` 重试 3 次，`failure.code == Some(-32603)` | 三次 `McpTransportError`（同一 `message`）重试 3 次，`failure.code == None`、`message` 含真实文本 | **这是 DR-56 的设计变更**，不是放宽：`-32603` 是业务错误，DR-56 后**恰尝试 1 次**。受测性质（"重试有界 + 保留最后一次真实失败"）**原样保留**，只把触发类别换成唯一还能耗尽预算的类别（传输）。**注意**：本测试的 `message` 仍逐字取自捕获件 `editor_errors_failure.txt`，未改写证据文本 |
| `tests/evidence_battery.rs:the_game_probe_calls_are_gdscript_bodies` | 探针必须**跑 `execute_gdscript`**（`scripts` 非空、`readings >= 4`、变异体不带 `return` 不带 `str(`） | 改名 `every_surviving_execute_gdscript_call_is_a_gdscript_body`；断言残留调用非空、**每个都带 `return`**、且**不含** `Input.action_press(`/`release(` | 前两条（"值必须靠 `return` 传出"、"void 调用不得作值"）**逐字保留**；第三条被**加强**为"注入已不再是脚本"。原测试的 `readings >= 4` 在 DR-54 后本就不该成立（承重读数已改由语义工具产出），保留它会迫使实现继续用脚本承重 —— 与 §15.1 直接冲突 |
| `tests/evidence_battery.rs:a_usable_game_channel_makes_the_replay_green` | `execute_gdscript` 调用数 ≥ 8；`channel.has_action == true`；探针内 `execute_gdscript` 条目 ≥ 6 | 语义注入调用数 ≥ 4（`play_input_recording`/`run_test_scenario`）；`channel.pressed == true`；**五类工具都逐字入库**；并**新增**"没有任何脚本变异体"的反断言 | `has_action` 字段现在恒为 `None`（无语义读者能表达它），`pressed` 与语义注入是等价（更强）的"注入被接受"证据；`execute_gdscript` 计数断言换成"语义工具都在场"+"脚本不承重"。**DR-57 补记**：该恒 `None` 的字段随后被**删除**（DEF-2 处置，见 §3.2 的 DR-57 更正块与 `src/adapter/godot.rs` 的 `InputChannelProbe` 文档注释）——它无读者却仍进原始证据，`null` 会被误读成"动作不存在" |
| `tests/evidence_battery.rs:input_replay_reports_an_action_that_is_not_bound` 的对偶错误文本 | 对偶回 `-32602 "no such action in this InputMap: ..."` | 同一 `-32602`，文本加 `ACTION_NOT_BOUND` 前缀 | **不是放宽**：新实现要求"`-32602` **且**文面明说是 InputMap 没有该动作"才算 `ACTION_NOT_BOUND`，比原来更严（裸 `-32602` 判 `ACTION_BINDING_UNKNOWN`）。对偶必须提供一个"引擎真的明说没这个动作"的回答，否则测的不是这条路径 |
| `tests/evidence_battery.rs:every_tool_call_hof_rs_makes_matches_the_contract_schema` 的 `AUDITED_TOOLS` | 15 个工具 | 19 个（+ 5 个语义工具、去重后 +4） | **只加不减**：新增调用点必须在契约参数形状审计的覆盖之内 |

**没有任何既有测试被删除**；`1` 个测试改名并收紧，`1` 个测试的两条断言被替换（等价的更强形式），`1` 个测试的错误文本前置了一个标记，`1` 个审计清单扩充。

### 4.4 "重试从未洗白失败"未被破坏的证据

`call_with_retries_traced` 的返回仍是 `Err(last)`（`last` 在每次失败时被**整体覆盖**，不在业务错误/超时路径上提早返回"合成成功"）；`failure.observation()` 仍含 `FAILED` 与 `UNAVAILABLE`。测试侧：
- `retries_are_bounded_and_preserve_the_real_error`（`attempts == 3`、真实 message 存活、`code == None`）
- `readiness_timeout_is_recorded_verbatim`（`wait_for_game_ready` 的真实失败逐字进 `mcp-errors.jsonl`，未被改写）
- nv6（植入"只留第一次失败" ⇒ 该测试**转红**，证明这条性质被测到）

---

## 5. TDD 证据（红 → 绿 → 重构）

每一步都先跑**只含新测试的 target**，捕获真实失败输出，再写最小实现。原始输出留档在 `.spec/hof-rs/tasks/nonvacuity/*.txt`（受控实验）与本节引文（红/绿阶段）。

### 5.1 DR-56

1. **红**：先只加 `McpTransportError`/`is_retryable_failure` 的**声明**，测试编译不过：

```
error[E0432]: unresolved import `hof_rs::tools::mcp::McpTransportError`
  --> tests\mcp_reliability.rs:13:36
error[E0432]: unresolved import `hof_rs::tools::reliable::is_retryable_failure`
  --> tests\mcp_reliability.rs:15:24
error: could not compile `hof-rs` (test "mcp_reliability") due to 2 previous errors
EXIT=101
```

2. **红（行为级）**：接上最小类型与分类器后，`retries_are_class_aware_business_errors_are_never_retried` 的**真实断言失败**（这才是"因缺行为而失败"）：

```
thread 'retries_are_class_aware_business_errors_are_never_retried' panicked at tests\mcp_reliability.rs:275:5:
assertion `left == right` failed: a business error is attempted once
  left: 3
 right: 1
```

（`left: 3` 正是 `smoke-t6` 的现象：同一个 `-32602` 被重试了 3 次。）

3. **绿**：把分类接到 `another_attempt_is_allowed` 后：

```
running 7 tests
test the_retry_classifier_is_the_single_decider ... ok
test retries_are_class_aware_business_errors_are_never_retried ... ok
test retries_are_bounded_and_preserve_the_real_error ... ok
test readiness_timeout_is_recorded_verbatim ... ok
test readiness_poll_succeeds_after_three_failures ... ok
test the_documented_intervals_are_not_negotiable ... ok
test args_file_resolution_is_absolute_and_diagnosable ... ok
test result: ok. 7 passed; 0 failed; 0 ignored; 0 measured; 0 filtered out; finished in 0.05s
```

4. **重构（全绿下）**：把"是否允许再试"抽成 `another_attempt_is_allowed`，并把"业务错误不重试"的必要性写进 `is_retryable_failure` 的文档；随后 `cargo test --offline` 全绿（330 passed / 0 failed / 7 ignored，EXIT=0）。

### 5.2 DR-55

1. **红**：先写 `tests/endpoint_liveness.rs`（7 条），只加实现前编译不过：

```
error[E0599]: no method named `endpoint_state` found for struct `McpChannel` in the current scope
   --> tests\endpoint_liveness.rs:387:14
error: could not compile `hof-rs` (test "endpoint_liveness") due to 10 previous errors
EXIT=101
```

2. **绿**：实现 `EndpointLiveness` + `McpChannel` 的按端点记录 + 判死短路 + `McpEndpointUnavailableError` 后：

```
running 7 tests
test a_single_transport_failure_does_not_kill_the_endpoint ... ok
test business_errors_never_count_toward_the_streak ... ok
test the_endpoint_state_is_a_stable_evidence_field ... ok
test a_dead_endpoint_stops_the_readiness_poll ... ok
test two_transport_failures_kill_the_endpoint_and_later_calls_do_not_retry ... ok
test the_editor_endpoint_state_is_separate ... ok
test registering_a_new_endpoint_re_arms_the_route ... ok
test result: ok. 7 passed; 0 failed; 0 ignored; 0 measured; 0 filtered out; finished in 4.20s
```

3. **红（被既有测试抓住的回归）**：我第一版让 `wait_for_game_ready` 在"任何不可重试失败"上停止，**破坏了 DR-20**（`readiness_poll_succeeds_after_three_failures` 是 DR-20 的既有测试：三次 `-32603` 后成功）：

```
thread 'readiness_poll_succeeds_after_three_failures' panicked at tests\mcp_reliability.rs:120:5:
the poll must succeed: ReadyOutcome { ok: false, attempts: 1, payload: None,
failure: Some(McpFailure { tool: "running_game_get_scene_tree", code: Some(-32603), … attempts: 1, retryable: false … }) }
```

**改正**：只有"未发请求的端点判死拒绝"（`endpoint_verdict`）才终止轮询，业务错误照旧轮询。改正后两 target 与全仓都绿。

4. **重构（全绿下）**：把该分支收敛为 `failure.endpoint_verdict` 一个条件、并把原因写进 `wait_for_game_ready` 的文档。

### 5.3 DR-54

1. **红**：先写 3 条新测试（+ 收紧 2 条既有），此时 `evidence_battery` 5 条转红，且失败原因正确（语义工具根本还没被调用）：

```
test a_failed_probe_is_unknown_never_not_bound ... FAILED
test a_usable_game_channel_makes_the_replay_green ... FAILED
test input_replay_reports_an_action_that_is_not_bound ... FAILED
test the_input_replay_injection_is_semantic_not_gdscript ... FAILED
test the_editor_input_map_can_never_claim_an_action_is_not_bound ... FAILED
test result: FAILED. 28 passed; 5 failed; 0 ignored; 0 measured; 0 filtered out; finished in 77.73s
```

2. **绿**：接入语义 API（`create_input_recording` → `play_input_recording` → `run_test_scenario` → `stop_input_recording`）与语义读数（`get_node_property_samples`、`get_node_properties`）、把 `execute_gdscript` 降为只读探针、并把 `ACTION_NOT_BOUND` 收紧为"`-32602` **且**文面明说"后：

```
test result: ok. 33 passed; 0 failed; 0 ignored; 0 measured; 0 filtered out; finished in 74.39s
```

（同轮 `every_tool_call_hof_rs_makes_matches_the_contract_schema` 在扩充 `AUDITED_TOOLS` 到 19 个工具后仍绿 ⇒ 5 个语义工具的**参数形状**逐条符合 177 条契约。）

3. **重构（全绿下）**：删掉已无调用者的 `game_script_bool`/`game_script_f64`/`game_script_present`（保留测试用的两个解析器为 `#[cfg(test)]`）、把语义工具名集中进 `pub mod semantic`、把"语义轴读数"抽成 `semantic_axis_sample`、把注入抽成 `semantic_inject_action_detailed`、更新 playbook 与文档注释。随后 `cargo build` **零 warning**，`cargo test --offline` 全绿（342 / 0 / 7，EXIT=0）。

---

## 6. 非空洞性证据（受控植入-回退）

脚本：`.spec/hof-rs/tasks/nonvacuity.ps1`（可复跑；每次先校验工作树**无 tracked 改动**，植入后只跑**一条**测试，`finally` 里 `git checkout --`，再用 `git hash-object` 证明恢复，并断言"植入后的 blob ≠ 植入前的 blob"）。原始输出：`.spec/hof-rs/tasks/nonvacuity/*.txt`；汇总：`nonvacuity/results.json`。

**七条全部 RED（exit 101）＝七条都不是空洞测试。**

| # | 植入（受控改动） | 目标测试 | 真实失败输出（摘） | 恢复证明 |
|---|---|---|---|---|
| nv1 | `failure_from` 把业务错误也标 `retryable = true`（即 `smoke-t6` 的缺陷本身） | `mcp_reliability::retries_are_class_aware_business_errors_are_never_retried` | `assertion left == right failed: a business error is attempted once` / `left: 3, right: 1` | planted `9c34ee50…` → restored `f52d3ade…`（= HEAD） |
| nv2 | 传输失败标 `retryable = false` | `mcp_reliability::the_retry_classifier_is_the_single_decider` | `assertion left == right failed: a transport failure is retryable, so the ring really retries (DR-56 ②)` / `left: 1, right: 4` | planted `511fd93d…` → restored `f52d3ade…` |
| nv3 | `ENDPOINT_DEATH_THRESHOLD = u32::MAX`（端点永生） | `endpoint_liveness::two_transport_failures_kill_the_endpoint_and_later_calls_do_not_retry` | `two consecutive transport failures must kill the endpoint: EndpointLiveness { state: Alive, unavailable: false, consecutive_transport_failures: 2, transport_failures_at_mark: 0 }` | planted `0c7d772e…` → restored `bb0035e2…` |
| nv4 | `ENDPOINT_DEATH_THRESHOLD = 1`（首次即判死） | `endpoint_liveness::a_single_transport_failure_does_not_kill_the_endpoint` | `one failure is not a verdict — the first failure must still retry: EndpointLiveness { state: Unavailable, unavailable: true, consecutive_transport_failures: 1 }` | planted `a2910ec7…` → restored `bb0035e2…` |
| nv5 | `McpChannel::call_with_meta` 把业务错误也记为传输失败（`Err(())`） | `endpoint_liveness::business_errors_never_count_toward_the_streak` | `assertion left == right failed: round 1: a business error is an answer and must not count: EndpointLiveness { state: Alive, consecutive_transport_failures: 1 }` / `left: 1, right: 0` | planted `e14e2266…` → restored `ddf6f4e4…` |
| nv6 | 重试环只保留**第一次**失败（`if last.is_none()`） | `mcp_reliability::retries_are_bounded_and_preserve_the_real_error` | `assertion left == right failed: 1 try + 2 retries` / `left: 1, right: 3` | planted `ea7f5531…` → restored `f52d3ade…` |
| nv7 | `probe_scripts::player_position()` 去掉 `return `（DR-50 的缺陷形态） | `evidence_battery::every_surviving_execute_gdscript_call_is_a_gdscript_body` | `a value-reading body must `return` its reading (DR-50A): str(get_tree().current_scene.get_node_or_null("Player").position.x) + "," + …` | planted `423752e2…` → restored `fae0060a…` |

**恢复的三法证明**：①脚本内 `git hash-object` 前后 blob 相等（见上表两列，`restored_blob` 与各自文件的 HEAD blob 一致）；②脚本跑完后 `git status --porcelain --untracked-files=no` **为空**；③脚本跑完后再跑一次全仓 `cargo test --offline` = **342 passed / 0 failed / 7 ignored, EXIT=0**（§0）。每份日志的 `EXIT=101` 与植入 blob 同文件同次运行，可逐条核对。

**第 5 条必测（"分类改成恒真 ⇒ 必须变红"）**：nv1 与 nv2 是两个方向的"恒真/恒假"，nv5 是 DR-55/DR-56 接缝上的恒真式误记；三者都转红。

---

## 7. 禁区自查（真实输出）

| 项 | 命令 | 真实输出 | 判定 |
|---|---|---|---|
| 未碰 `godot-mcp/**` | `git diff --stat 53f6f9d… -- godot-mcp` + `git log --oneline 53f6f9d….HEAD -- godot-mcp` | 两条均**无输出** | 未改、未提交 |
| 未写 `runs/**` | `git status --porcelain --untracked-files=all -- runs`（`runs/` 被 gitignore，故另做文件级核对） | 空；`runs/smoke-t6` 递归 **135** 文件、最新 mtime **2026/9/29 2:32:01**（批次开始前）；`runs/` 下 mtime 晚于 `2026-09-29 12:00` 的文件数 = **0**；`frame-00.png` sha256 `bef0936daba1b16a23e7b25bd1fc432d946afaaca6d7b0636fbeafc898b67ea2`（与 D223 记录的 `bef0936d…7ea2` 一致，4246 B） | 未写、未覆盖 |
| PRD sha 未变 | `(Get-FileHash .spec/hof-rs/PRD-mario.md -Algorithm SHA256).Hash.ToLower()` | `4c81c3a9995f0b3afdf01421a0c3be88573cceefc284ce9bafbfda141f0f5c3a` | 与要求逐字一致 |
| 无新依赖 | `git diff --stat 53f6f9d… -- Cargo.toml Cargo.lock` | 无输出 | `Cargo.toml` / `Cargo.lock` 零 diff |
| 未 push | `git remote -v`；`git rev-parse origin/master`；`git rev-list --count origin/master..HEAD` | remote `https://github.com/shiyukonghui/hof-rs.git`；`origin/master = 82f2da21e0cf7a4088a9aab257c3a86b3a9b3bfb`；ahead = **1** | **我（本子代理）未执行任何 `git push`**。见 §9 的诚实披露：`origin/master` 在本批进行中由**上游编排者**推进过，因此它已包含 `513069c`/`df95339` 与 DR-54 的早期一次提交；我最后的报告提交 `b3ccef9` 仍只在本地（ahead=1） |
| 未编造输出/日期 | 本报告引用的每段输出均可由文中命令在当前工作树重跑得到；目录 mtime/文件计数/hash 均由 `Get-ChildItem`/`Get-FileHash` 实测；日期 2026-09-29 取自本机时钟与已入库提交 | — | 无编造 |
| 离线 | 全批未执行任何 `editor_*`/`running_game_*` 真机调用；未启动 Godot（`godot.windows.editor…` 零次启动）；未连接 9877 或任何端口（`tests/endpoint_liveness.rs` 与 `tests/mcp_desync.rs` 仅用 `TcpListener::bind("127.0.0.1:0")` 的自有端口）；未联网（`cargo test --offline`）；未调用模型端点 | — | 离线成立 |
| 工作树干净 | `git status --porcelain --untracked-files=no` | 空 | 无植入残留 |

---

## 8. 遗留风险与未验证项（严格区分实测与推断）

**实测（本批真有证据的）**

1. 离线判据全绿：`cargo test --offline` EXIT 0、342 passed / 0 failed / 7 ignored（ignored 未随本批增加）。
2. 5 个语义工具的**参数形状**逐条符合 177 条契约（`every_tool_call_hof_rs_makes_matches_the_contract_schema` 扩充覆盖后仍绿）。
3. 端点在**真实 transport failure**（loopback 端口 bind 后关闭 ⇒ 立即 connection refused）下按 DR-55 判死、零重试（7 条测试用的是真 `ureq` 传输路径，不是打桩）。
4. 七条新行为全部非空洞（§6）。

**推断（未被本批证据覆盖，不得当作已证）**

1. **E3 本身是否 met 完全未验证** ⇒ 必须由真机 T=1 轮次判定（§15.4）。本批**不作**此断言。
2. **引擎对"InputMap 没有该动作"的实际应答文面**：`ACTION_NOT_BOUND` 现要求"`-32602` + 文面含 `ACTION_NOT_BOUND`"。现有 `tools_list.json` 的 `description` 只说 `running_game_play_input_recording` 在本进程无可用录制时回 `-32602`，**未**给出"动作不在 InputMap"的原文。若真机文面不含该标记，probe 会保守地落在 `ACTION_BINDING_UNKNOWN`（诚实 gap，**不是**假 verified），代价是 P3 证据缺失。这是**主动选择的保守方向**；真机轮次应把它定为"文面待核"。
3. **`running_game_get_node_property_samples` 是否接受 `input_axis` 这样的非节点属性名**：契约 `description` 未禁止，`TEST-CASES.md` 亦未列反例。语义路径的**承重**其实是"注入被接受 **且** 游戏进程有语义读数"（`get_node_properties` 的 `name` 非空亦可满足），因此即使 `input_axis` 采样被拒，`input_channel_probe` 仍可为 `GAME_INPUT_CHANNEL_OK`；但**轴读数会缺失**（`axis_before/axis_after` 为 `null`）。真机形态待核。
4. **`running_game_play_input_recording` 的 `events` 是否接受 `InputEventAction` 形状（`{"type":"action","action":…,"pressed":true}`）**：契约的 `events` 是 `array` 且无 `items` 约束，`editor_simulate_input_sequence` 的 `events` 文档明确含 `type:"action"`+`action`，故形状选择有依据；但**游戏端点**对同一形状的接受度未在离线可证。
5. **`running_game_run_test_scenario` 的步骤字段名**：我按契约 schema 用 `type`/`action`/`pressed`/`seconds`/`node_path`/`property`/`expected`/`operator`。契约文档另记"`waited_seconds` 是**回显**字段不是入参"，我遵此未发送它。真机是否逐字接受整套步骤未证。
6. **重试放大**：`mcp.rs::post()` 仍在传输层内部按 `tools.max_retries` 重试，上层重试环也会对传输失败再试 ⇒ 一次逻辑调用在传输失败下最多 `(1+max_retries)²` 次 HTTP 尝试。DR-55 把"端点已判死"的路径压到 1 次尝试，但**未判死之前**的放大仍在。本批未改 `mcp.rs` 的重试语义（§15.3 明确"传输层已正确"），**如实记为本批未处理项**。
7. **`artifact_is_fresh` 不可达分支、DR-49④ 单独不可证伪**（D223 的 DEF-1/DEF-2）本批未触碰。

**未关闭的上游项（与 D223 一致，本批不碰）**

- DR-50B 的**最小复现 spike**（`editor_play_scene` 后第一件事发编译不过的 `code`）本批**未执行**（离线批次：不得碰端口、不得起引擎）。
- `runs/smoke-t6` 目录摘要算法仍未文档化（本报告改用与算法无关的"135 文件 + mtime + `frame-00.png` sha256"口径）。
- `godot-mcp/**` 仍**未改、不改**（引擎侧由 `035edfce7` 等另线处理）。

---

## 9. 诚实披露

1. **我最初的 `wait_for_game_ready` 实现是错的，被既有测试抓住。** 我把它写成"不可重试失败就停止轮询"，把 DR-20 的 `readiness_poll_succeeds_after_three_failures` 弄红（真实输出见 §5.2）。DR-55 的快速失败**已经**由端点判死覆盖（判死拒绝是 `endpoint_verdict`，与业务错误可区分），不需要也不应该动 `wait_for_game_ready` 的业务错误语义。已改正并把理由写进函数文档。**这是本批最有价值的一次自我纠正**：如果我当时"为了让新测试过"去改那条既有测试，就会把 DR-20 悄悄拆掉。
2. **`ACTION_NOT_BOUND` 的第一版判据太宽，已被自己收紧。** 我最初只按 `-32602` 判 `ACTION_NOT_BOUND`；写"语义全部拒绝但脚本探针成功"的反例测试时，对偶的合成 `-32602` 让 probe 输出了 `ACTION_NOT_BOUND`，测试立刻转红。事实是 `-32602` 同时也是"参数畸形"的码，只凭它判"动作没绑定"正是 DR-35 存在的理由。改正为"`-32602` **且**文面明说"。**该失败发生在我的 TDD 循环内，未进入任何提交的最终状态。**
3. **我一开始把 `probe_scripts` 模块整体计划删除（"不再需要 GDScript"），后来放弃该方案。** 原因：四组既有单测（`the_probe_scripts_are_single_line_bodies`、`the_game_script_readings_are_parsed_strictly` 等）依赖它，硬删就必须删/改这些测试 —— 而任务书禁止"放宽/删除既有测试换绿"。改成"保留只读探针与解析器，但把它们从**判定路径**移出"：同样满足 §15.1（"只可用于只读探针，且其返回值不得作为任何关键断言的**唯一**证据"），代价是 `game_script_bool`/`game_script_f64` 只剩测试调用，我把它们标注为 `#[cfg(test)]` 以保持零 warning。
4. **一次 PowerShell 失效把实验脚本的第一次运行打断，留下了一个被植入的文件。** `$ErrorActionPreference='Stop'` 遇上 cargo 的 stderr 让我第一轮在 revert 之前就退出。我核对了 `git status` 发现 `src/tools/reliable.rs` 处于植入态，用 `git checkout --` 恢复后才重跑，并给脚本加了 `try/finally` 与"运行前必须无 tracked 改动"的前置断言。**最终交付的工作树是干净且 blob 可核的；那次残留只存在于被中断的运行里，从未进入提交或测试结论。**
5. **`origin/master` 在本批进行中被上游推进过，不是我 push 的。** 我从未执行 `git push`。实测：`origin/master = 82f2da2`，`git rev-list --count origin/master..HEAD = 1`，而 `82f2da2` 的作者是 `starsliving`、内容是本批之外的 `docs(spec): D235–D237`；`git reflog` 显示这四个提交鳞次插在我的三个提交之间，且 `82f2da2` 的 reflog 条目出现在 `df95339` 之后。⇒ 上游编排者在我工作期间创建了这些提交并把远端推进到了含我前两个提交的位置。**这是编排者的动作，不是我的；我未越权 push。** 我的报告提交 `b3ccef9` 目前仍只在本地。
6. **推断 vs 实测**：§8 已逐条区分；特别是"引擎对'InputMap 无此动作'的实际文面""`input_axis` 能否被 `get_node_property_samples` 采样""`events` 的 action 形状被游戏端点接受"三项都**只有推断**，本报告不把它们写成已实现。
7. **未复现的东西我不写成已实现**：DR-50B 的最小复现 spike 本批**未执行**（离线批次禁止起引擎/碰端口），因此本报告不声称引擎缺陷已孤立确认 —— 那需要真机。
8. **未断言 E3 已 met**：本批只交付"E3 的关键断言不再由调用方拼装的 GDScript 承重"这一结构性改造；E3 的 met/not_met 只能由带 `4.8.dev.mono.custom_build.035edfce7`（含 TASK-151 修复）的真机 T=1 轮次判定，且该轮**不得**用二进制 sha256 当引擎新鲜度判据（§15.4）。

---

## 10. 工件索引

| 类别 | 路径 |
|---|---|
| 本报告 | `.spec/hof-rs/tasks/TASK-DR54-REPORT.md` |
| 任务书 | `.spec/hof-rs/tasks/TASK-DR54-IMPL.md` |
| 非空洞性脚本 | `.spec/hof-rs/tasks/nonvacuity.ps1` |
| 非空洞性原始输出 | `.spec/hof-rs/tasks/nonvacuity/*.txt`、`nonvacuity/results.json`、`nonvacuity_run.txt` |
| 改动（生产代码） | `src/adapter/godot.rs`、`src/tools/reliable.rs`、`src/tools/mcp.rs`、`src/tools/mod.rs`、`src/tools/endpoint.rs` |
| 改动（测试） | `tests/mcp_reliability.rs`、`tests/endpoint_liveness.rs`（新）、`tests/evidence_battery.rs` |
| 批次提交 | `513069c`（DR-56）、`df95339`（DR-55）、`6329e5c`（DR-54）、`b3ccef9`（非空洞性证据） |
| 批次起点 | `53f6f9d82d057df111fadd4fe7a124569f1ced36` |
