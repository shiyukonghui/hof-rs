# TASK-DR68-REPORT — 打通“真机已出现增量”到“E1/E3 真的 met”之间的四件事（**离线批次**）

- 任务书：`.spec/hof-rs/tasks/TASK-DR68.md`（**唯一任务来源**）
- 落点：`F:\moonbit-hof-rs`（外层仓），执行者：**实现子代理（无上游上下文）**
- 开工 HEAD：`99c9fba`；收工 HEAD：`5baa801`（其后本报告单独一次提交）
- 提交：**9 个**（英文信息，均含 `(DR-68)`，见 §1）；**未 push**（`origin/master` 全程 `ce22e18`）
- 性质：**离线**。未启动 Godot、未碰外部端口、未联网、未调模型端点、**未跑真机轮**。
- **未声称 E1 或 E3 已 met**：这两条只有真机能定（§7）。

---

## 1. 结论 + 套件真实尾部/退出码 + `cargo fmt --check`

**门（最终一次，全部改动就位、9 处植入全部回退之后）：**

```
$ git ls-files '*.rs' | wc -l
78
$ git ls-files '*.rs' | xargs touch      # 只 touch 已存在文件
TOUCH_OK
$ cargo test --offline ; echo EXIT=$?
     Running tests\wrap_up_budget.rs (target\debug\deps\wrap_up_budget-48d6de538feb9569.exe)
test result: ok. 10 passed; 0 failed; 0 ignored; 0 measured; 0 filtered out; finished in 17.27s
     Running tests\usage_extraction.rs (…)
test result: ok. 0 passed; 0 failed; 0 ignored; 0 measured; 0 filtered out; finished in 0.00s
EXIT=0

$ awk '/^test result/{p+=$4; f+=$6; i+=$8} END{print "passed="p" failed="f" ignored="i}' <全量输出>
passed=414 failed=0 ignored=7        # 43 行 “test result”，其中 42 行 ok + 1 行 doc-test 0
```

- **`cargo test --offline` exit 0；414 passed / 0 failed / 7 ignored。**
  基线要求 **≥397 passed / 0 failed / 7 ignored** ⇒ 通过，**`ignored` 计数未增长（7）**，无既有测试被删或放宽（§4 的 9 处植入全部逐字节回退后可复现）。
- **`cargo fmt --check`：exit 0**（见下）。
- `touch` **只针对已存在文件**：`git ls-files '*.rs'` 输出 78 条，`xargs touch` 的输入全部来自 git 索引，**没有通配符**；
  施工后 `git status --porcelain -uall` 为空、`git ls-files build.rs` 为 0 ⇒ **没有造出空的 `build.rs`**（DR-67 的教训）。

**`cargo fmt --check` 的真实情况（必须先说清）：**

```
$ cargo fmt --check            # 在开工状态 99c9fba 上
FMT_EXIT=1 ; 145 个 "Diff in"，跨 30 个文件（13 处 src/**，17 处 tests/**；含我新写的几处，rustfmt 随后统一）
```

⇒ 开工时**整棵树不是 rustfmt-clean**（DR-67 的 DEF-D 只点名了 `run_loop.rs:153`，**实际范围比它大**）。
门要求 `cargo fmt --check` 通过，所以本批用**一个独立的、纯格式化的提交** `d482794`
（`cargo fmt`，30 文件 / +728 −331）把树规范化；此后每次改动都过 `cargo fmt`，**最终 `cargo fmt --check` = exit 0**。
该提交**不含任何语义改动**，其正确性由最终全量套件（414/0/7）与 §4 的植入-回退可复现性共同背书。

**9 个提交（`git log --oneline 99c9fba..HEAD`，英文信息均带 `(DR-68)`）：**

```
5baa801 docs(SMOKE-T8): correct the round report in place — left movement was never established, the
        rejected evidence lacks two fields, the battery masked a dead axis, and two facts the
        acceptance checked (DR-68)
93d20d1 fix(battery): release the previous direction inside the game process and judge replay movement
        on the action's own axis, so gravity cannot mask a dead axis (DR-68)
0c109af fix(gate): an editor-log line that the current project bytes cannot reproduce must not close
        the launch gate or burn the repair retry (DR-68)
456acf4 fix(schema-gate): deliver the evidence record shape on the first attempt, allow the one
        shape-carrying retry for a present-but-invalid artifact, and name every missing record field
        at once (DR-68)
8310941 fix(run-loop): a failed round persists the candidate identity and battery results it really
        produced instead of an empty stub (DR-68)
3459b42 fix(gate): a gate that was never evaluated is not an open gate, and every reader (is_open,
        result.json, meta.json, status) must say so (DR-68)
6b13d32 fix(prompts): name the legal completion protocol in the planner and tester prompts, which
        mini treats as the only way a call may end (DR-68)
d482794 style: normalize the tree with rustfmt so the DR-68 gate's cargo fmt --check can pass (DR-68)
ae875e5 fix(prompts): reject the single-brace HOH placeholder the format! literals left in the task
        prompts and the TOOLS.md header (DR-68)
```

**逐条结论（八项要求）：**

| 项 | 状态 | 一句话 |
|---|---|---|
| ① Tester 证据形状契约 | **已实现** | 完整形状（`claim_id` + 记录级 `type`）**首次尝试即下发**；`if limits { break; }` 改为“**存在但非法**的工件可得一次带形状的重试”；`validate_evidence_shape` **一次列全**记录级缺失字段；`tester.md` 写明形状 |
| ② 启动闸门不被过期日志关门 | **已实现** | 新增 `editor_error_is_stale`：只认**当前工程字节仍能复现**的日志行；日志残留不关门、**也不触发修复**（反向控制：当前错误照旧关门） |
| ③ 输入回放方法论 | **已实现** | 每个方向前**在游戏进程内** `pressed:false` 释放上一输入；回放后**断言轴值改变**（仅在引擎给出读数时）；报告诊断**就地更正** |
| ⑧ 位移 vs 被重力移动 | **已实现** | 位移判据改为**按目标轴**（`movement_on_intended_axis`）；目标轴零位移、另一轴有位移 ⇒ 判 `未移动` |
| ④ 失败路径 `result.json` 自证 | **已实现** | `FailureFacts` 把**真实** `battery_passes`/`candidate_id`/`version_id` 写进失败存根；冻结前的失败点仍是**如实空** |
| ⑤ 单花括号占位符 | **已实现** | 三处 `format!` 与 `TOOLS.md` 头部改为可解析；`contains_unresolved_command_var` 与 `assert_fully_rendered` **两种花括号都覆盖** |
| ⑥ 合法终止符 | **已实现** | `planner.md`/`tester.md` 写明 `COMPLETE_TASK_AND_SUBMIT_FINAL_OUTPUT`；并有**可执行**测试证明它是 mini 的唯一合法出口 |
| ⑦ 失败轮门状态自相矛盾 | **已实现** | `not_applicable` 不再报 `launchable=true`；`is_open() = applicable && launchable`；`status` 列对未评估的门报 `unknown` |

---

## 2. 各项落点（文件:行）与理由；③ 的诊断结论

### ① Tester 证据形状契约

| 落点 | 内容 |
|---|---|
| `src/runtime/schema.rs:81-105` | **新增** `shape_context()` / `first_attempt_context()`：把 `EVIDENCE_SKELETON` 作为**每次尝试**（含首次）的上下文下发；调用方已有的上下文（wrap-up / repair）被保留在前 |
| `src/runtime/schema.rs:259-263`、`:296-305` | Tester gate：`context` **初始即带形状**；`if limits && (shape_retry_spent \|\| !expected.is_file())` —— **只有“工件根本不存在”**或“已经花掉那一次形状重试”才 break |
| `src/runtime/schema.rs:142-149`、`:197-205` | Planner gate 应用同一条重试规则（同一缺陷的双胞胎循环），形状仍由 `retry_context` 携带（planner 的 `[output-contract]` 本来就写全了结构） |
| `src/model.rs:629-725` | `validate_evidence_shape` 增加**记录级**检查：`claim_id`/`claim`/`execution_records`/`status` 与每个执行记录的 `type`/`observation`，**并一次列全** |
| `src/prompts/tester.md:53-99` | `[output-contract]` 写出完整 record 形状（`claim_id`、执行记录的 `type` 六个取值、`observation`、`player_impact`/`recommended_update`）与“每个键都是必需的” |

**理由**：真机上 `EVIDENCE_SKELETON` **只作为 retry context 下发**（`schema.rs:241` 旧行号），而 `if limits { break; }`
（旧 `:243-245`）在 attempt1 以 `LimitsExceeded` 结束、工件**已存在但形状非法**时把它抑制掉 ⇒ 骨架一次也没送到模型手里，
日志写着 `schema failure for role Tester after 1 attempt(s)`。**只补 `type` 也会再被拒**：被拒件的 claim 层没有 `claim_id`，
而 `ClaimRecord.claim_id`（`src/model.rs:104-108`）没有 `#[serde(default)]`，serde 一次只报一个字段。
因此三件事必须同时做：**首次给形状**、**给一次可救的重试**、**一次列全缺失字段**。

### ② 启动闸门不得被过期编辑器日志行关门

| 落点 | 内容 |
|---|---|
| `src/adapter/godot.rs:3931-3944` | `res_source_position()`：解析 `res://<path>:<line>` |
| `src/adapter/godot.rs:3946-3958` | `quoted_function_name()`：解析 `Function "name()"` |
| `src/adapter/godot.rs:3980-4000` | **`editor_error_is_stale()`**：只有“能定位到文件 + 行号在范围内 + 该行**不含**错误点名的符号”才判过期；**其它一律保留（fail closed）** |
| `src/adapter/godot.rs:4003-4018` | `partition_editor_errors()`：分成 `(仍可复现, 已过期)` |
| `src/adapter/godot.rs:779-859`（`step_editor_errors`，判定块在 `:801-846`） | 闸门只用**仍可复现**的行决定 `ok`；观察文字如实写出“N 行被当作过期日志丢弃” |

**理由**：`editor_get_errors` 读的是编辑器**追加日志**，不是当前工程。`smoke-t8` 在 07:19:33 读到一条指向
`_update_facing_visual` 的解析错误，而 `player.gd` 自 07:19:25 起调用并定义的是 `_apply_facing_visual`；
闸门据此关门，白烧 60 步 / 4.02M tokens / 11 分 24 秒，且**零工程写入**。
`editor_error_is_stale` 的判据是**内容一致性**：真正的“函数未定义”错误意味着**该行确实调用了那个函数**
（所以符号应在该行上出现）；只有被改写过的行才会不满足。规则**故意很窄**（只处理真机出现过的那一种消息形状），
读不懂的行一律保留，因此“日志残留不关门”不会退化成“任何错误都不关门”——§3 ② 的反向控制正是测这个。

### ③ 输入回放方法论 —— **诊断结论：harness/引擎侧的方法论缺陷，不是游戏脚本缺陷**

| 落点 | 内容 |
|---|---|
| `src/adapter/godot.rs:1770-1789` | **新增** `semantic_release_action()`：走 `running_game_play_input_recording` 发送 `{"action": …, "pressed": false}` |
| `src/adapter/godot.rs:1934-1968` | `step_input_replay`：循环内维护 `held_in_game`，**每个方向测试前**在游戏进程内释放上一输入 |
| `src/adapter/godot.rs:2140-2156` | 回放后**断言轴值确实改变**：引擎给出读数且符号不符 ⇒ `INPUT_AXIS_NOT_CHANGED`（`ok=false`）；读数为 `null` 时不作断言（真机如此，DR-58） |
| `src/adapter/godot.rs:2791-2822` | **⑧**：`movement_on_intended_axis()` + `AxisMovement` + `intended_axis()` + `expected_axis_sign()` |
| `src/adapter/godot.rs:2085-2110` | 位移判据改用目标轴；观察文字带上 `axis=x delta=…` |
| `.spec/hof-rs/tasks/TASK-SMOKE-T8-REPORT.md` | **就地更正**（保留旧文字并加 `【DR-68 更正】` 标注） |

**原始证据（我自己从冻结的轮内 raw 重算，只读；脚本 `%TEMP%\dr68\t8_inputs.py`）：**

```
#2  running_game_play_input_recording label=move_right:play_input_recording
    payload=[{"action":"move_right","pressed":true,"type":"action"}]
#3  running_game_run_test_scenario label=move_right:test_scenario
    payload=[{"action":"move_right","pressed":true,…},…]
#8  editor_simulate_input_action label=move_right:EDITOR_SIDE_INJECTION:release
    args={"action":"move_right","pressed":false}          <-- 编辑器进程，到不了游戏
#10 move_right_release:play_input_recording  [{"pressed":true}]      (又是 press)
#18 jump:play_input_recording                [{"action":"jump","pressed":true}]
#22 QUADRUPLE jump  before=(470.696, 269.996) after=(577.030, 242.607)
    velocity={"x":3.6666870117189774,"y":4.5}              <-- 跳跃期间 x 仍以 3.6667 px/帧增加
#26 move_left:play_input_recording           [{"action":"move_left","pressed":true}]
#30 QUADRUPLE move_left before.x=584.363037109375 after.x=584.363037109375
    before.y=270.940612792969 after.y=283.994659423828 velocity={"x":0.0,"y":0.0}
#31 move_left:game_axis  {"samples":[{"frame":0,"input_axis":null}]}
```

**读法（第一性原理）**：轮内**每一次游戏通道注入都是 `pressed=true`**；**四个 release 全部走
`editor_simulate_input_action`**（`#8/#16/#24/#32`），而本报告自己承认“编辑器侧到不了游戏”。
于是 `move_right` 在游戏进程内**始终被按住**：`Input.get_axis("move_left","move_right")` = **0**，
`velocity.x` 必为 0，**左移实现无论对错都不会产生水平位移**。`#22` 是最硬的反证——跳跃窗口里 x 仍在以
`3.6667 px/帧` 增加，说明采样时 `move_right` 仍被按住。**故 `move_left` 的读数是注入时序假象，
“左移被证否”不成立，产品结论未知**（`.spec` 报告已按此更正，见 C1）。
**归因：harness 的输入回放方法 + 电池判据，而不是游戏脚本**。另有同一根因的第二处缺陷（⑧）：
旧判据 `before_position != after_position` 是**整向量**比较，`#30` 的 `y` 从 270.94 变到 283.99（重力），
于是这条 `x` 60 帧零位移的记录被电池判成 **`ok=true`** —— 掩蔽型假绿。

### ④ 失败路径 `result.json` 必须自证

| 落点 | 内容 |
|---|---|
| `src/runtime/run_loop.rs:289-302` | **新增** `FailureFacts { candidate_id, version_id, battery_passes }` |
| `src/runtime/run_loop.rs:245`、`:262-276` | `finalize_failure(…, facts)` 把三个字段写进 `IterResult` |
| `src/runtime/run_loop.rs:1417-1425` | **Tester schema 失败**（`smoke-t8` 的失败类）传入真实 `version.candidate_id` / `version.version_id` / `battery_passes` |
| `src/runtime/run_loop.rs:1238-1245`、`:1362-1370` | Tester 的后冻结契约失败（pre-QA drift、candidate/workspace 被改）同样传真实事实 |
| `src/runtime/run_loop.rs:711`、`:756`、`:966` | 冻结前/电池前的失败点传 `FailureFacts::default()`，并注明“这里空是**如实**，不是存根” |

**理由**：真机上失败轮 `iter-1/result.json` 是 `battery_passes: []`、`candidate_id: null`、`version_id: null`，
而同一轮**电池 11/11 全绿且 `A_1` 已冻结**。任何只读 `result.json` 的读者（启动器、`status`、下一批）
都会得出“什么都没发生”，关系判据(4) 的可复现性正好在最需要它的路径上失效。

### ⑤ 单花括号占位符

| 落点 | 内容 |
|---|---|
| `src/prompts/mod.rs:75`、`:96`、`:124`（`:139` 是文档注释） | `format!` 里改为 `{{{{HOH_*}}}}`（渲染后得到 `%HOH_*%` / `$HOH_*`） |
| `src/tools/index.rs:165-167` | `TOOLS.md` 头部同样修正 |
| `src/runtime/shell.rs:96-112`、`:144-149` | `contains_unresolved_command_var` 覆盖**两种**花括号：`{{HOH_X}}` 与 `{HOH_X}` |
| `src/runtime/invoke.rs:162-192` | `assert_fully_rendered` 增加“未解析的 shell 占位符”判据（`{{`/`{%` 之外的新增面） |
| `tests/role_shell_contract.rs` | 新增“**任何交付文本**都不得含不可解析占位符”的断言（三份 system prompt + 三份 task prompt + skills + playbook + 两种角色的 `TOOLS.md`） |

**理由**：模板写在 `format!` 字面量里时，`{{HOH_X}}` 会被 `format!` 折成 `{HOH_X}`，而
`render_command_vars` 只匹配双花括号 ⇒ 角色收到一个**谁都不解析**的占位符。旧的完整性断言只查 `{{`/`{%`，
所以这一类残留**结构上不可能被发现**。真机实测的残留清单见 §3 ⑤。

### ⑥ 提示词缺合法终止符

| 落点 | 内容 |
|---|---|
| `src/prompts/planner.md:94-101` | 新增 `[completion]`：`COMPLETE_TASK_AND_SUBMIT_FINAL_OUTPUT` 是唯一合法出口；**submit 不是终点** |
| `src/prompts/tester.md:146-153` | 同上 |
| `tests/prompt_shell_contract.rs` | 新增**可执行**测试：`echo COMPLETE_TASK_AND_SUBMIT_FINAL_OUTPUT` 在真实 `LocalEnvironment` 里产生 `AgentError::Interrupt(InterruptKind::Submitted)`，而 `echo submit` 不会 |

**理由**：mini 的合法终止只有一条（`mini-swe-agent-rust-mini/rust/src/environments/local.rs:118-128`：
命令首行恰为 `COMPLETE_TASK_AND_SUBMIT_FINAL_OUTPUT` 且 returncode 0）。`planner.md`/`tester.md` 从未提它，
真机上 planner 在第 35 步提交后 `RepeatedFormatError` 死亡。新的测试**执行**了该机制，所以“写了这句话”不是空断言。

### ⑦ 失败轮门状态自相矛盾

| 落点 | 内容 |
|---|---|
| `src/model.rs:295-317` | `not_applicable` 现在写 `launchable: false`；**`is_open() = applicable && launchable`** |
| `src/cli_impl.rs:853-868` | `status` 的门列：`applicable=false` ⇒ `unknown`（不再是 `ok`） |
| `tests/result_semantics.rs`、`tests/e1_increment.rs` | 单元级 + 端到端（`iter-1/result.json` 与 `meta.json`）双重断言 |

**理由**：`smoke-t8` 的失败轮持久化的是 `{"applicable": false, "launchable": true}`（`not_applicable` 的旧形状），
而 `is_open()` 只看 `launchable` ⇒ **失败读成了通过**。改成“未评估就不是打开”之后，`run_exit_code`
（`applicable && !launchable`）的语义不变（不适用仍不产生退出码 6）。

---

## 3. TDD 证据（先红 → 后绿，均为真实输出）

每项都是**先写会失败的最小测试**、贴真实失败输出，再最小实现转绿。所有“绿”都由最终全量套件（414/0/7）覆盖。

### ① Tester 证据形状契约（3 个测试同时红）

```
$ cargo test --offline --test schema_gate
test the_tester_prompt_documents_the_evidence_record_shape ... FAILED
test the_first_tester_attempt_is_told_the_evidence_record_shape ... FAILED
test a_present_but_invalid_artifact_still_gets_one_shape_retry ... FAILED

---- the_tester_prompt_documents_the_evidence_record_shape stdout ----
DR-68 ①(c): tester.md must document `claim_id` in its output contract

---- the_first_tester_attempt_is_told_the_evidence_record_shape stdout ----
DR-68 ①: the first attempt must already carry `claim_id` in its shape block; it received: ""

---- a_present_but_invalid_artifact_still_gets_one_shape_retry stdout ----
the shape retry must be allowed to recover the present artifact: schema failure for role Tester after 1 attempt(s)

test result: FAILED. 3 passed; 3 failed; 0 ignored; 0 measured; 0 filtered out; finished in 0.03s
```

第三条的失败串 `schema failure for role Tester after 1 attempt(s)` **与真机日志逐字相同**。
测试用的 `t8_evidence()` 就是真机形状：顶层键齐全、`execution_records[*]` 只有 `{path, observation}`、
claim 层缺 `claim_id`。

**绿**：`cargo test --offline --test schema_gate` → `6 passed; 0 failed`。

### ② 启动闸门（红：日志残留真的烧掉了修复）

```
$ cargo test --offline --test launchable_gate a_stale_editor_log_line
---- a_stale_editor_log_line_does_not_close_the_gate stdout ----
thread '…' panicked at tests\common\mod.rs:270:13:
FakeHarness step #2 expects Tester but the runtime asked for Developer; actual sequence so far:
["planner", "developer", "developer"]
test result: FAILED. 0 passed; 1 failed; 0 ignored; 13 filtered out; finished in 8.94s
```

失败信息本身就是缺陷：**闸门关门并索要了一次定向修复（第二个 Developer）**，而那行日志描述的是
当前文件没有的符号。反向控制 `a_reproducible_parse_error_still_closes_the_gate` 在修复前后都通过（它测“不许过度放宽”）。

**绿**：`--test launchable_gate` → `14 passed; 0 failed`（含 4 个 DR-48/DR-68 反向例）。

### ③ 输入回放释放（红）

```
$ cargo test --offline --test evidence_battery the_input_replay_releases
thread '…' panicked at tests\evidence_battery.rs:2717:5:
DR-68 ③(a): the replay must release the previous input inside the game: [ … 整份 calls 数组 … ]
```

同一份红输出里可直接看到假象链条：`move_left:test_scenario` 的 `observed_axis` 是 **0.0**；
`move_left` 的 quadruple 是 `before.x = 100.0, after.x = 100.0`（x 死）而 `y` 从 `283.0` 走到 `342.0`（重力）；
`move_left:game_axis = 0.0`。

### ⑧ 位移判据（红）

```
$ cargo test --offline --test evidence_battery a_dead_target_axis
thread '…' panicked at tests\evidence_battery.rs:2811:5:
a dead `x` axis is not movement, however much `y` moved: input replay: … move_left: 60 frame(s)
channel=game_process {"action":"move_left","after_position":{"x":60.0,"y":342.0},
"before_position":{"x":60.0,"y":283.0},"channel":"game_process","velocity":{"x":0.0,"y":1.0}} …
```

`velocity.x = 0.0` 且 x 前后相同，旧的整向量判据却让这一步 **`ok=true`**。

**绿**：`--test evidence_battery` → `41 passed; 0 failed`（含两个新测试与全部既有电池测试）。

### ④ 失败存根（红）

```
$ cargo test --offline --test evidence_battery a_failed_rounds_result_json
thread '…' panicked at tests\evidence_battery.rs:3239:28:
candidate_id must be the real A_1, not null: {"artifact_gate":{"applicable":false,"launchable":false,…},
  …,"battery_passes":[],"candidate_id":null,…,"version_id":null,"reason":"schema_failure",…}
```

**绿**：1 passed（修前/修后真实内容见 §5）。

### ⑤ 单花括号占位符（红）

```
$ cargo test --offline --test role_shell_contract
test the_unresolved_placeholder_detector_sees_both_brace_forms ... FAILED
test no_delivered_document_carries_an_unresolvable_command_placeholder ... FAILED

---- the_unresolved_placeholder_detector_sees_both_brace_forms stdout ----
DR-68 ⑤: the single-brace form the `format!` literals left behind must be reported too

---- no_delivered_document_carries_an_unresolvable_command_placeholder stdout ----
delivered documents still carry unresolvable placeholders:
["developer_task: {HOH_HOH_BIN}", "developer_task: {HOH_SCRATCH_DIR}", "planner_task: {HOH_HOH_BIN}",
 "tester_task: {HOH_HOH_BIN}", "TOOLS.md (developer): {HOH_HOH_BIN}",
 "TOOLS.md (developer): {HOH_ARTIFACT_DIR}", "TOOLS.md (developer): {HOH_SCRATCH_DIR}",
 "TOOLS.md (tester): {HOH_HOH_BIN}", "TOOLS.md (tester): {HOH_ARTIFACT_DIR}",
 "TOOLS.md (tester): {HOH_SCRATCH_DIR}"]

test result: FAILED. 5 passed; 2 failed; 0 ignored; 0 measured; 0 filtered out; finished in 0.08s
```

这 10 处正是真机 `smoke-t8` 的残留类别。对冻结轮做只读统计（`grep -rEo "\{HOH_[A-Z_]+\}" runs/smoke-t8`
去掉 `{{…}}` 形态后按出现次数计）：

```
48 处，分布：{HOH_HOH_BIN} 19、{HOH_SCRATCH_DIR} 16、{HOH_ARTIFACT_DIR} 13
文件：runs/smoke-t8/TOOLS.md、iter-1/candidate/.hoh/TOOLS.md、iter-1/planner-view/.hoh/TOOLS.md，
      以及 planner/developer/tester 的 6 份轨迹（交付文本的副本）
```

即：三份 task prompt（planner/developer/tester）与 `TOOLS.md` 头部是残留来源，与 §2 ⑤ 的落点一一对应。

**绿**：`--test role_shell_contract` → `7 passed; 0 failed`；`--lib` 亦含 `a_single_brace_shell_placeholder_is_not_fully_rendered`。

### ⑥ 终止符（红）

```
$ cargo test --offline --test prompt_shell_contract
---- every_role_prompt_names_the_legal_completion_protocol stdout ----
thread '…' panicked at tests\prompt_shell_contract.rs:375:9:
planner.md does not name the only legal completion protocol
```

同一次运行里 `only_a_first_line_completion_protocol_ends_a_role_call` **已经通过**——它执行了真实
`LocalEnvironment`，证明“这句话确实是唯一合法出口”，所以提示词断言不是空洞的字符串匹配。

**绿**：`--test prompt_shell_contract` → `5 passed; 0 failed`。

### ⑦ 门状态（红，单元 + 端到端）

```
$ cargo test --offline --test result_semantics
test a_gate_that_did_not_apply_is_not_open ... FAILED
test status_does_not_report_an_unevaluated_gate_as_ok ... FAILED
---- a_gate_that_did_not_apply_is_not_open ----
DR-68 ⑦: a gate that did not apply must not report launchable=true
---- status_does_not_report_an_unevaluated_gate_as_ok ----
an unevaluated gate is unknown, not ok: # run demo-run
iter-1   harness=fail  gate=ok       prd=0/0 (total=derived) ok=false reason=schema_failure  candidate=- roles=0
```

端到端（`tests/e1_increment.rs`，零工程写入的失败轮）：
`DR-68 ⑦: a failed round must not report a launchable gate: {"artifact_gate":{"applicable":false,"launchable":true,…}}`。

**绿**：`--test result_semantics` → `9 passed`；`--test e1_increment` → `13 passed`。

### ③(c) 报告就地更正

`.spec/hof-rs/tasks/TASK-SMOKE-T8-REPORT.md`：**旧文字一字未删**，在文件头加“⚠ 就地更正声明”索引表
（C1..C8），并在 §0 E1/E2/E3 行、§1.3、§2、§2.2、§2.3、§3.1、§5、§6.4、§10 的就地位置加
`【DR-68 更正 Cn】` 标注。核心改动：
`左移被实测证否` → **`左移 not established；既有观测是注入时序假象的产物，产品结论未知`**；
缺失字段清单 → **`type` 与 `claim_id` 两个**；E2 的“只留在 workspace” → **冻结的 run 目录同样留证**；
`origin/master = 079cf82` → **`ce22e18`**。

---

## 4. 非空洞性：**9 处仅生产代码的受控植入**（要求 ≥4），逐处红 + 逐字节回退

植入**全部落在 `src/**`**，**没有**落在承载不变量的测试里（因此不需要 D253 那种“植入在测试中”的说明）。
每处植入的运行、回退与验证流程完全一致：

```
$ # 植入 → 运行对应测试 → 贴红 → 回退：
$ cp %TEMP%\dr68\plant\<file> <file>
$ cmp %TEMP%\dr68\plant\<file> <file> && echo CMP_OK
$ git status --porcelain -uall ; git diff --stat
$ git hash-object <file> ; git rev-parse HEAD:<file>
```

| # | 植入（文件） | 植入内容 | 红掉的测试（自己的那条） | 红输出（真实、已归档） |
|---|---|---|---|---|
| P1 | `src/runtime/schema.rs` | 首次尝试的 context 退回 `base.retry_context.clone()`（形状只在 retry） | `the_first_tester_attempt_is_told_the_evidence_record_shape` | `DR-68 ①: the first attempt must already carry \`claim_id\` in its shape block; it received: ""` |
| P2 | `src/runtime/schema.rs` | `if limits { break; }` 退回（抑制形状重试） | `a_present_but_invalid_artifact_still_gets_one_shape_retry` | `schema failure for role Tester after 1 attempt(s)` |
| P3 | `src/adapter/godot.rs` | 判据退回整向量不等 | `a_dead_target_axis_is_not_movement_even_when_the_other_axis_moves` | ``a dead `x` axis is not movement, however much `y` moved: …`` |
| P4 | `src/adapter/godot.rs` | 去掉游戏进程内释放（`held_in_game.clear()` 代替） | `the_input_replay_releases_the_previous_direction_before_the_next_one` | `DR-68 ③(a): the replay must release the previous input inside the game` |
| P5 | `src/adapter/godot.rs` | `editor_error_is_stale` 恒 `false`（任何日志行都算） | `a_stale_editor_log_line_does_not_close_the_gate` | `FakeHarness step #2 expects Tester but the runtime asked for Developer …` |
| P6 | `src/model.rs` | `is_open()` 退回 `self.launchable` | `a_gate_that_did_not_apply_is_not_open` | `applicability decides, even when launchable=true` |
| P7 | `src/runtime/run_loop.rs` | Tester schema 失败传 `FailureFacts::default()` | `a_failed_rounds_result_json_carries_the_real_battery_and_candidate` | `candidate_id must be the real A_1, not null: …"battery_passes":[]…` |
| P8 | `src/prompts/tester.md` | 去掉 `[completion]` 的终止符正文 | `every_role_prompt_names_the_legal_completion_protocol` | `tester.md does not name the only legal completion protocol` |
| P9 | `src/prompts/mod.rs` | 把 planner task 的 `{{{{HOH_HOH_BIN}}}}` 退回 `{{HOH_HOH_BIN}}` | `no_delivered_document_carries_an_unresolvable_command_placeholder` | `delivered documents still carry unresolvable placeholders: ["planner_task: {HOH_HOH_BIN}"]` |

**回退证明（逐处，实测输出摘录）——每个文件都满足四项：`cmp` 通过、`git status --porcelain -uall` 为空、
`git diff --stat` 为空、`git hash-object` == HEAD blob：**

```
P1  schema.rs    CMP_OK ; status=<空> ; diff=<空> ; ebf05c797a645aaaf5ac53fc6c6498b5e9f54041 == HEAD
P2  schema.rs    CMP_OK ; status=<空> ; diff=<空> ; ebf05c797a645aaaf5ac53fc6c6498b5e9f54041 == HEAD
P3  godot.rs     CMP_OK ; status=<空> ; diff=<空> ; cbcf11abbcb4ddd355f3f80edcd7efc0ea6342ea == HEAD
P4  godot.rs     CMP_OK ; status=<空> ; diff=<空> ; cbcf11abbcb4ddd355f3f80edcd7efc0ea6342ea == HEAD
P5  godot.rs     CMP_OK ; status=<空> ; diff=<空> ; cbcf11abbcb4ddd355f3f80edcd7efc0ea6342ea == HEAD
P6  model.rs     CMP_OK ; status=<空> ; diff=<空> ; e0ebea4190d3af0b611f1427f0694adb8e571fa7 == HEAD
P7  run_loop.rs  CMP_OK ; status=<空> ; diff=<空> ; 01e08d3c123618e8051e6be095367a11a2783ece == HEAD
P8  tester.md    CMP_OK ; status=<空> ; diff=<空> ; c7a10e2f1728df523fa9d83b8a57f11bf8d01a7e == HEAD
P9  prompts/mod.rs CMP_OK ; status=<空> ; diff=<空> ; 4b36486d2562d32a2047d97e4f8b1c6ce6c3c18e == HEAD
```

**为什么 `cmp` 是必需的（本仓 CRLF 敏感）**：`core.autocrlf=true`，工作树是 LF、索引也是 LF；
若用 `git checkout -- <file>` 回退，git 可能把文件物化成 CRLF —— 此时 `git status`/`git diff` **仍然干净**、
`git hash-object` **仍等于 HEAD blob**（git 在 hash 前会做行尾规范化），但**文件字节已经变了**。
所以本批的回退一律用**仓外字节备份 + `cmp`**，并以 `%TEMP%\dr68\plant\` 里的 9 个备份为唯一参照物。

---

## 5. 失败路径 `result.json` 的修前/修后真实内容（三个字段）

场景：真机 `smoke-t8` 的失败类 —— Developer 产生了工程增量、`A_t` 已冻结、电池 11 步全绿，
Tester 提交的证据**存在但形状非法**，被 schema gate 拒绝（`max_schema_retries = 0`，一次尝试）。

**修前（来自未修复代码的真实红输出，`artifact_gate` 已含 DR-68 ⑦ 的修复）**

```
"artifact_gate":{"applicable":false,"launchable":false,"reasons":["no launchable gate was evaluated for this iteration"]},
"battery_passes":[],
"candidate_id":null,
"version_id":null,
"failed_role":"tester","reason":"schema_failure","ok":false
```

**修后（同一场景，`cargo test --nocapture` 由做出断言的同一次运行打印）**

```
DR-68 failure stub (after): candidate_id=4f76c437c39720781c4d481fe13409baedfc17f4e49fbf2170b8c51ee0ab016d
                            version_id=4f76c437c39720781c4d481fe13409baedfc17f4e49fbf2170b8c51ee0ab016d
                            battery_passes=1 steps=10
```

三个字段都变成**本轮真实产生的值**：`candidate_id` 是 `A_t` 的内容哈希（64 位十六进制，与
`versions/index.json` 中同一条 `version_id`/`candidate_id` 相符，测试做了这项交叉核对），
`battery_passes` 是那次电池的真实逐步骤判定（该夹具 10 步全 `ok`；真机的 11/11 会写成 11）。
两个退出码位置（`runs/<id>/exit_code`、`meta.json.exit_code`）仍由 DR-67 的路径写，
本批未改动，测试里既有断言继续通过。

---

## 6. 禁区自查（真实输出）

**6.1 三条 `runs/**` 基线未动 + 摘要口径自证**

摘要口径（与 `TASK-SMOKE-T8-ACCEPTANCE.md` §0 一致）：PowerShell，**仓根相对**小写 POSIX 路径 +
字节长度 + 小写 sha256，`\t` 连接、`\n` 分行、无尾随换行，行序 `Sort-Object`，整体 UTF-8 取 sha256。
**自证**：该口径对两条**已知参考值**都逐字命中：

```
runs\smoke-t6   sort_fullname  c144ef3219e21dd322978e41a5531d53dee270619c026585505920f9277a9c03  <== MATCH
runs\smoke-t7   sort_fullname  6e4c1595753c2cdefb16e4d2e5f05242ca202c70c81a93e98ae2b9c92b520fb7  <== MATCH
```

三条基线的现状（**只读计算，未做任何写入**）：

```
runs\smoke-t6: files=135 newest=2026/9/29 2:32:01  (meta.json)   digest(c144ef32…7a9c03) == DR-66/67/验收记录
runs\smoke-t7: files=115 newest=2026/9/29 14:41:14 (meta.json)   digest(6e4c1595…20fb7)  == 上表参考值
runs\smoke-t8: files=358 newest=2026/9/30 7:58:28  (meta.json)   digest(6d11b2c61ec507b5f02525ddc0e7f7adb08763cd2439a4b08788b7fe51bdf5a7)
```

- `smoke-t8` 的 358 文件与最新 mtime `2026-09-30 07:58:28`（= 那一轮的收工时刻）说明**没有任何文件在我施工期间被写**；
  我施工的第一次写发生在 **08:44 之后**（`git log` 首个提交 `ae875e5` 是 `09:09:33`）。
- **`runs/**` 全程零写入**：没有临时分析文件、没有删除、没有“写完再删”。本批的全部分析产物都在
  `%TEMP%\dr68\`（§8）。

**6.2 `mario` 未改**

```
$ git ls-files .workspace | wc -l          -> 0            # .workspace 不被外层仓跟踪
$ git diff --name-only 99c9fba..HEAD | grep -c '^\.workspace'  -> 0   # 我的 9 个提交没有一项落在 .workspace
$ git status --porcelain -uall             -> <空>
$ .workspace\mario: files=148 newest=2026/9/30 8:09:00 (.godot\editor\editor_layout.cfg)
```

⇒ `mario` 里**没有任何文件的 mtime 落在我的施工窗口内**（最新是 08:09:00，早于我施工），
且我的提交集合与工作树都不含 `.workspace` 的任何路径。
**但必须如实说明一处对不上**：`DECISIONS.md` D264 记的是 `mario 259 / 4e494547…`，我现在读到 **148 文件**，
且我试了四种排序/两种 BOM 组合都**没有**复现 `4e494547…`（见 §7 遗留风险 R6）。这一差异**不是我的写入造成的**
（无 mtime 落在窗口内、提交集合为空），但它**早于也不能由我的会话解释**，故原样披露。

**6.3 `PRD-mario.md` 的 sha256**

```
$ sha256sum .spec/hof-rs/PRD-mario.md
4c81c3a9995f0b3afdf01421a0c3be88573cceefc284ce9bafbfda141f0f5c3a  *.spec/hof-rs/PRD-mario.md
```

与报告/验收记录的 `4c81c3a9…5c3a` 逐字一致 ⇒ 未改。

**6.4 引擎树未改（用嵌套仓证明，并用 pathspec 自证命中）**

```
$ git -C godot-mcp/godot rev-parse HEAD
fc63af77c33368c4a1bb839c95d19750554f63a3          # == D264 记录的 fc63af77…，嵌套仓 HEAD 未变
$ git -C godot-mcp/godot status --porcelain       # 空 ⇒ 嵌套仓工作树干净
$ git ls-files godot-mcp | wc -l                  -> 6484   # pathspec 真命中
$ git ls-files godot-mcp/godot | wc -l            -> 0      # 外层仓不跟踪引擎树（假绿陷阱③）
$ find godot-mcp/godot -newermt "2026-09-30 08:44" -type f | wc -l -> 0   # 我施工窗口内零文件
```

⇒ “引擎树未改”这条断言**只由嵌套仓 + mtime 支撑**，因为外层 `git diff` 在引擎树上是“什么都没说”。

**6.5 无新依赖 / 未 push / 仓内无临时物**

```
$ git diff --stat 99c9fba..HEAD -- Cargo.toml Cargo.lock      -> <空>   # 无新依赖
$ git rev-parse origin/master                                 -> ce22e181b1619c8fa5cf6adc670f7de48d2a3198
$ git log --oneline origin/master..HEAD | wc -l               -> 15     # 本地领先，未 push
$ git status --porcelain -uall                                -> <空>   # 仓内无未跟踪/临时物
$ git diff --name-only 99c9fba..HEAD -- .spec/                -> 仅 TASK-SMOKE-T8-REPORT.md（报告更正）
```

**6.6 其它硬约束**

- **未改** `DECISIONS.md`、`godot-mcp/**`、`.workspace/mario/**`、`.spec/hof-rs/PRD-mario.md`（§6.2–6.4）。
- **未启动 Godot、未碰外部端口、未联网、未调模型端点、未跑真机轮**（全部证据为离线夹具/单元测试）。
- 新增测试计数：最终 414 vs 门要求 ≥397；`ignored` 7 未增长；**没有删除或放宽既有测试**——
  以测试标注数与断言数为证（`git grep` 实测）：

  ```
  tests/ 的 #[test]/#[tokio::test] 数：99c9fba = 285  →  HEAD = 299   (+14，全部是新增测试)
  src/   的 #[test]/#[tokio::test] 数：99c9fba = 119  →  HEAD = 122   (+3，全部是新增单元测试)
  tests/ 的 assert!/assert_eq!/assert_ne! 行数：99c9fba = 1237 → HEAD = 1291   (+54)
  ```

  `git diff 99c9fba..HEAD --stat -- tests/` 中的既有文件改动来自 `d482794` 的 **rustfmt 纯格式化**
  （提交 `d482794` 不含语义改动，其正确性由 414/0/7 的最终套件背书）。

---

## 7. 遗留风险与未验证项（严格区分实测 / 推断）

**实测（本轮有证据）**

1. ①的机制三处都在代码里就位，且有三个独立测试覆盖（首次形状、可救的重试、缺失字段一次列全）。
2. ②的过期判定对**真机那一行**（`res://scripts/player.gd:31` + `Function "_update_facing_visual()"`）判为过期；
   对当前仍可复现的错误仍关门（反向控制通过）。
3. ③/⑧：把真机的注入序列在夹具里复现后，旧判据把 `x` 死、`y` 动的 `move_left` 判成 `ok=true`（红）；
   新判据判为未移动，并且“先释放再测”的断言在修复后才成立。
4. ④：失败轮 `result.json` 的三个字段在同样的失败路径上由 `null/[]` 变成真实值（§5）。
5. ⑤：交付文本里 10 处不可解析占位符全部消失；两种花括号都有断言与单元测试。
6. ⑥：终止符文本进入 planner/tester 提示词；终结合法性由真实 `LocalEnvironment` 执行证明。
7. ⑦：`not_applicable`/`is_open`/`status`/`result.json`/`meta.json` 五个读者口径一致。
8. 门：414/0/7 + `cargo fmt --check` exit 0；9 处植入逐字节回退可复现。

**推断（不得当作已证）**

1. **R1 — 真机上的形状自愈尚未验证。** 本批只证明“首次就带形状 + 有一次带形状的重试 + 缺失字段一次列全”
   都在离线夹具里生效；**模型是否因此提交出合法 `E_1`，只有真机能答**。**E1 仍 not_met。**
2. **R2 — `semantic_release_action` 的可用性未在真机验证。** 它用 `running_game_play_input_recording` 发
   `{"action":…,"pressed":false}`；真机 t8 的 release 之所以没到游戏，是因为它们走了**编辑器**工具，
   不是因为这个形状被引擎拒绝——但“引擎接受 release 事件”这一点**本轮未实测**（离线约束）。
   若引擎拒绝，观察文字会写 `accepted=false`，且轴值断言会兜底（`INPUT_AXIS_NOT_CHANGED`）。
3. **R3 — ⑧的轴值断言在真机上大概率不触发。** t8 的 `input_axis` 每次都是 `null`（DR-58），
   所以“断言轴值改变”只在引擎给出读数时才生效；真机上的**承重断言是按目标轴的位移**（这一点是实测）。
4. **R4 — ②的规则故意很窄。** 只处理 `... res://<file>:<line> ... Function "X()" not found in base self.`
   这一种形状；**其它种类的过期日志行仍会关门**（fail closed）。这是设计取舍，不是遗漏；
   若下一轮真机出现另一种陈旧形状，需要在这一处扩展而不是放宽整体。
5. **R5 — ⑥只是文本契约。** 没有真实模型调用，因此“planner 不再 `RepeatedFormatError`”属未验证。
6. **R6 — `mario` 计数不一致（实测的不一致，原因未知）。** D264 记 259 文件 / `4e494547…`；
   我实测 148 文件、四种排序两种 BOM 都不匹配。我的窗口内证据（mtime、提交集合、git status）都指向
   “我没有写它”，但**我无法证明 08:09 之后没有第三方删除过文件**（删除不更新 mtime）。
   **需要调度者确认**：D264 的 259/`4e494547…` 是用什么根目录/口径、在什么时刻测的。
7. **R7 — 失败路径的 `evidence_diff` 仍是空。** ④只覆盖了任务书点名的三个字段；
   `iter-1/result.json.evidence_diff` 在 Tester schema 失败时仍是 `{added:[],modified:[],removed:[]}`，
   尽管该轮真的改了 3 个工程文件。这不在 DR-68 范围内，保留为下一批的候选。
8. **R8 — 风险旗 1 的代码/文档矛盾未处理。** `src/adapter/godot.rs` 的
   `GAME_INPUT_CHANNEL_OK` 判据与其文档注释（“with a semantic reading arriving”）仍然矛盾（t8 报告 §2.4）。
   本批未改动该判定。
9. **R9 — 报告更正的具体措辞是我的判断。** C1 的“−3.667 px 反证”来自 t8 报告 §2.2 实验 #2 的**文字记录**
   （D=375.333、F=371.666），我读的是报告，不是原始回包（`runs/smoke-t8-experiment/**` 我只做只读引用，
   未逐帧重算该实验）。**该反证是“支持性”的，不是本批的新证据**；C1 的主证据是本批 §2 重算的冻结 raw。
10. **基线计数的口径说明。** 开工时我并行测到过一次 `passed=399 / 0 failed / 7 ignored`，但那一次运行
    与我对 `tests/` 的第一次编辑有重叠，**不是干净的基线**；能够干净的只有 `99c9fba` 上 `cargo test --offline` **exit 0**
    这一点。门要求 ≥397 由最终 **414** 满足，与本说明无关。

---

## 8. 诚实披露

1. **`cargo fmt` 规范化是一次大范围改动**（30 文件 / +728 −331，提交 `d482794`）。它不是任务书点名的改动，
   而是 `cargo fmt --check` 入门口的必要条件：**开工状态本身有 145 处格式差异**。
   我把它单独提交，并如实说明 **DR-67 的 DEF-D（“只有 `run_loop.rs:153` 一处格式损坏”）是不完整的**。
2. **我修改了共享的测试替身** `FixtureChannel`（`tests/evidence_battery.rs`）：把“游戏进程内按住的输入”从一个
   `bool` 换成**动作集合**，并让位移分轴。这是**测试夹具**改动，不是生产代码植入；不做这一步就无法复现
   验收 D1/D3 指出的假象与假绿。它的正确性由 41 个电池测试（含全部既有用例）背书。
3. **我另加了一行 `println!`** 到 `a_failed_rounds_result_json_carries_the_real_battery_and_candidate`
   （`--nocapture` 时输出修后的三个字段），作为 §5 的可复现证据来源。它不参与断言。
4. **植入做了 9 处**（要求 ≥4），**全部在生产代码**，**没有**落在承载不变量的测试里；每处都用
   `cmp` + `git status` + `git diff` + `hash-object` 四重回退证明（§4）。
5. **我没有声称 E1 或 E3 已 met**；本批是离线批次，真机判定不在我的权限内（§7 R1）。
6. **我没有写任何 `runs/**` 路径**：连临时分析文件都没有，全部分析脚本与红/证据落在
   `%TEMP%\dr68\`（`digest*.ps1`、`t8_inputs.py`、`red-item*.txt`、`plant/*`、`final_test.txt`、`baseline_count.txt`）。
7. **我没有改** `DECISIONS.md`、`godot-mcp/**`、`.workspace/mario/**`、`.spec/hof-rs/PRD-mario.md`。
8. **我保留了两处“我也不能解释”的事实而不是掩盖**：`mario` 148 vs 259（R6）、以及 ② 的 narrow 规则
   对其它陈旧形状仍会关门（R4）。此外我明确指出 §7 R9：C1 报告更正里“−3.667 px”的反证引自 t8 报告的文字，
   不是我这批重算的原始回包。
9. **没有 push**；本地 15 个提交领先 `ce22e18`。
