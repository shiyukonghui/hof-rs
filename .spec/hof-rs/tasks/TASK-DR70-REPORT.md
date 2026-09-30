# TASK-DR70-REPORT — 按 D273 修"路由生命周期放错阶段"，并收掉五处 fail

- 执行者：DR-70 实现子代理（无上游对话上下文，唯一任务来源 `TASK-DR70.md`）。
- 仓库：`F:\moonbit-hof-rs`（外层仓）。离线批次。
- 被修对象：DR-69 的 7 个提交（`96b7c29..03b35dd`）在 `TASK-DR69-ACCEPTANCE.md` 判 fail 的 5 类问题。
- 本批 6 个提交（英文信息，均带 `(DR-70)`）：

```
5971d16 fix(evidence): restore the frozen smoke-t9 command dump from git history and redact only
        the truncated credential-assignment value, pinning the tree to no line-ending conversion (DR-70)
17831d3 test(harness): drive the output ceiling through MiniHarness::invoke so deleting the
        CappedEnvironment wiring can no longer leave the suite green (DR-70)
69ea374 style(tests): keep the new DR-70 test files rustfmt-clean (DR-70)
cd9c9c1 fix(tools): validate a published game route (freshness, pid liveness, reachability) before
        adopting it, so a stale route returns DR-43's explicit refusal instead of a transport failure (DR-70)
3abd14e feat(runtime): start the round's game before the first role and tear it down on every exit
        path, so the published route covers the Developer and Tester windows instead of only the battery's own step (DR-70)
f78289a docs(prompts): make the three Developer-facing sites agree with the round-wide route - the
        delivered skill gives the editor-side self-test and says why the round's game cannot confirm the
        increment, developer.md states the new window, and the contract test pins the substitute (DR-70)
```

---

## 1. 结论与门

**结论：五项全部落地，每一项都先有因当前行为而红的真实测试，再做最小实现转绿；5 处仅生产代码的受控植入各自使对应测试红，并逐字节回退。**

### 1.1 门（真实输出）

强制重编按要求**逐文件循环已存在文件**、**未用通配符**（脚本仓外 `dr70/gate.sh`）：

```
touched 87 tracked .rs files one by one        # while IFS= read -r file; do [ -f "$file" ] && touch "$file"; done < <(git ls-files '*.rs')
--- fmt ---   FMT_EXIT=0
--- test ---  cargo test --offline --no-fail-fast
              （50 条 `test result:` 行）
passed 455 failed 0 ignored 7
FAILED lines: 0
CARGO_EXIT=0
GATE_WRAPPER_EXIT=0
```

- `cargo fmt --check` **exit 0**（`FMT_EXIT=0`）。
- `cargo test --offline` **exit 0**，**455 passed / 0 failed / 7 ignored**（基线 436 → **+19 = 我新增的 19 条测试**；`ignored` **7 → 7 未增长**）。
- 未用 PowerShell 的 `Get-Content -Raw`+`Set-Content` 改任何源码：全部源码/文本编辑走编辑工具与 **UTF-8 干净的 Python 按字节读写**（脚本在仓外 `C:\Users\wyl\AppData\Local\Temp\dr70\`）。
- 既有测试未删：按"函数名 + 前 3 行内含 `#[test]`/`#[tokio::test]`"解析，`9aebbe1` → `HEAD` 测试函数 **264 → 292，`REMOVED = []`**；`tests/godot_smoke.rs` 的 `#[ignore` 出现数 **8 → 8**（7 属性 + 1 文档提及），与运行期 `ignored 7 → 7` 一致。
- 既有断言的两处改动是**需求驱动的收窄/换向**，不是放宽，逐条见 §3.3 与 §7.6。

### 1.2 一次跑通的"角色真能到达游戏端点"（本批头号目标）

`tests/round_game_window.rs::the_published_route_covers_the_developer_and_tester_windows`：
在**真实 `run_loop::run`** 的真实阶段序里，于 Developer 步与 Tester 步**内部**启动**真实 `hoh` 二进制**（`CARGO_BIN_EXE_hoh`，带 `HOH_GAME_ROUTE`），断言：

- `route_exists: true`（进入该阶段时 route 文件已存在）；
- 退出码 `Some(0)`，输出不含 `game_endpoint_unavailable`；
- 回环"游戏端点"替身**实际收到了两次** `running_game_get_scene_tree`（`game.tools() == [.., ..]`）——即角色进程**真的读到了**发布的路由；
- 编辑器端点**没有**收到任何 `running_game_*`。

反向（把发布前移的机制删掉）的开火证据见 §4 的 P3：`route_exists: false`、`exit_code: Some(5)`、stderr 逐字等于验收 D1 里真机角色拿到的 `game_endpoint_unavailable … (DR-43)`。

---

## 2. ① 的窗口包含性证据

### 2.1 事实层的改动（D273 决定 1）

| 事项 | DR-69 | DR-70 |
|---|---|---|
| 发布时机 | 电池 `step_play_scene` 内（`godot.rs:903`），即 Developer **之后** | **轮次启动时**（`run_loop.rs:718`，第一个角色之前） |
| 撤下时机 | 同一 pass 末 `step_stop_scene`，唯一调用点 | **`run()` 包装层在每条退出路径上**撤（`run_loop.rs:571-579`）+ 各阶段边界 + 保留 `stop_scene` 自身的撤下 |
| 陈旧 route | 无条件采纳 | 采纳前校验新鲜度/pid 存活/可达性（②），且轮次启动先撤掉同目录旧文件（`run_loop.rs:600`） |

阶段级排布（`src/runtime/run_loop.rs`）：

- `571` `pub async fn run(...)`：先 `run_inner`，**再无条件** `stop_round_game`（`578`）。
- `600`：轮次启动先 `withdraw_game_route`，再 `use_game_route_file`（旧文件**不被继承**）。
- `718`：**第一个角色之前** `start_round_game` → 游戏为本轮启动，route 发布。
- `1187`：电池 pass(es) 之前 `stop_round_game`（电池必须在**冻结候选**上启动自己的游戏，两次 `editor_play_scene` 不得重叠）。
- `1229`：launch-gate 修复 Developer（仍是 Developer 角色）之前 `start_round_game`。
- `1281`：第二遍电池之前 `stop_round_game`。
- `1308`：电池块之后、冻结与 Tester 之前 `start_round_game`。

`start_round_game`/`stop_round_game`（`run_loop.rs:526`/`548`）：适配器侧实现见 `src/adapter/mod.rs:200`/`:213`（默认 no-op）与 `src/adapter/godot.rs:3839`/`:3886`（`editor_play_scene` + **就绪轮询** + `register_game_endpoint`（发布）；`editor_stop_scene` + `clear_game_endpoint`（撤下））。启动失败**不致命**（写 warning，电池仍是闸门），撤下失败也写 warning，且包装层**无论适配器是否成功**都直接 `withdraw_game_route`。

### 2.2 "发布窗口 ⊇ 角色窗口"的可核断言

测试同时钉住两侧：

1. **进入 Developer 阶段时 route 存在**：`RouteProbe.route_exists == true`（由角色 shell 探针在步内实测，不是读代码推断）。
2. **角色进程实际读到了它**：回环游戏替身收到 2 次 `running_game_get_scene_tree`；`!editor.tools().any(running_game_)`。
3. **窗口被显式开/关**：`stub.starts() >= 2`（Developer 窗口一次、Tester 窗口一次）、`stub.stops() >= 2`（电池自启不得与轮次会话重叠）。
4. **异常路径**：`a_failing_round_still_withdraws_the_published_route` —— Developer 触发 `NoEngineeringWrite` 契约闸门、`run` 返回 `Err`，仍然断言 `route_exists: true`（Developer 期间）+ `stub.stops() >= 1` + `!route.exists()`（错误路径也撤）。
5. **不继承**：`a_route_left_by_another_round_is_not_inherited` —— 预先放一个**任何检查都合格**的旧 route（活端口 + 活 pid + 新鲜），断言角色侧看到 `route_exists: false`、调用以 `game_endpoint_unavailable` 收场、且那个"上一轮的游戏"**一个请求都没收到**。

---

## 3. ②③④⑤ 的落点与红→绿

### 3.1 ② 采纳时校验新鲜度、pid 与可达性

**生产落点**：`src/tools/endpoint.rs` `ROUTE_MAX_AGE_SECONDS:142`、`RouteRefusal:151`、`process_is_alive:208`、`destination_refuses_connections:303`、`route_age_seconds:329`、`validate_published_route:348`；`src/tools/mod.rs` `route_refusal` 字段 `:162`、`client_for` 的"found and **refused**"分支 `:226-236`、`use_game_route_file:429`（校验失败即拒绝并把理由记到通道上）。

**拒绝语义**：`use_game_route_file` 返回 `None` ⇒ `client_for` 以 `game_endpoint_unavailable: … the published route was found and **refused**: <理由> … No request was sent, so this is an explicit refusal, not a transport failure …` 硬 bail（DR-43 的明确拒绝，**不是**传输失败）。

**三项检查与它们各自的诚实边界**（都写进了代码注释）：

- **过期**：文件 mtime 超过 `ROUTE_MAX_AGE_SECONDS = 6h`。这是三者中最弱的一项（长轮次不能失效），文档里已声明。
- **pid 存活**：Windows 用三个手写 `kernel32` 声明（`OpenProcess`/`GetExitCodeProcess`/`CloseHandle`）的 FFI；Unix 用 `kill(pid, 0)`；其它平台返回"无法判定"。**没有引入依赖**。`pid == None` 的记录跳过该项（不凭猜测制造拒绝）。
- **可达性**：只对**回环**目的地做阻塞 `connect`，且**只有 `ConnectionRefused`** 才判死；超时/解析失败等一律"无法判定"。实测依据：本平台 `TcpStream::connect_timeout` 把**被拒绝的回环连接**报成 `TimedOut raw=None`（所以它看不见这个检查要的分辨），阻塞形式报 `ConnectionRefused raw=Some(10061)`、约 2s。

**红（先红，真实输出）**：`tests/game_route_across_processes.rs` 三条新测试，在实现前全红，含验收 D6 的逐字症状：

```
a_route_pointing_at_a_closed_port_is_refused_explicitly ... FAILED
  the refusal must be DR-43's explicit one: hoh: MCP transport failure to http://127.0.0.1:51109/mcp:
  ... Connection Failed: Connect error: 由于目标计算机积极拒绝，无法连接。 (os error 10061)
a_route_whose_recorded_game_process_is_gone_is_refused_even_when_the_port_answers ... FAILED
  assertion `left != right` failed ... left: Some(0) right: Some(0)      # 陈旧 route 被采纳，调用"成功"
an_expired_route_is_refused_even_when_it_still_answers ... FAILED       # 同上
```

**绿**：`cargo test --offline --test game_route_across_processes` → **6 passed / 0 failed**。非空洞性：反向仍是"活端口 + 活 pid 的 route ⇒ 真实子进程 exit 0"，且 `endpoint.rs` 新增 4 条单测（被释放的回环端口被识别为拒绝；能应答/无法判定的目的地不被拒；活 pid 与被收割子进程的 pid 判然不同；拒绝理由含具体数字）。既有直接通道测试 `registering_publishes_the_route_and_stopping_withdraws_it` 按新契约改用**活**端点与**本进程** pid（**契约变更**，非放宽，已披露）。

### 3.2 ① 的落点与红→绿

见 §2.1 的落点表。红→绿：
- **红**：`tests/round_game_window.rs` 三条测试在 DR-69 的代码上不可能通过——本批里由植入 P3/P4 各自复现（§4）。
- **绿**：`cargo test --offline --test round_game_window` → **3 passed / 0 failed**。
- 测试基建（测试侧，非生产）：`tests/common/mod.rs` 的 `FakeStep::probing`（步内副作用）、`RoundGameStub`、`FakeAdapter::with_round_game`、`run_scenario_with_tools`（用真实 `McpChannel` 驱动真实 `run_loop::run`）。

### 3.3 ③ 三处交付材料同步 + 新扫描测试

三处**同一矛盾**的落点：

| 处 | DR-69 状态 | DR-70 |
|---|---|---|
| `src/prompts/skills/godot-dev.md:65-78`（§5） | `editor_simulate_input_action` + `running_game_get_node_property_samples`，并要求 `samples[*].position.x` 变化 | 改为**编辑器侧自证**（`editor_get_errors` / `editor_get_output_log` / `project_read_script`），并写明**为什么**本轮的游戏进程不能自证："was started **before you changed the code**" |
| 同文件 `:80-92`（§6） | `editor_play_scene` → `running_game_get_scene_tree` → `editor_stop_scene` | 只留 `editor_get_errors`，并写明运行时owns轮次会话 |
| `tests/developer_contract.rs:121` | **要求**该技能含 `running_game_get_node_property_samples` | 换为要求 `editor_get_errors` + `before you changed the code`（正反两侧详见文件内注释：一个具体工具名离开清单、两个具体要求进入清单） |
| `src/prompts/developer.md:31-37` | 断言"该 route 只由电池的 `editor_play_scene` 注册，**你的调用期间可能不可用**" —— ① 之后**成为假事实** | 改为"route **for the whole round**"+"the game it names was started **before your edits**" |

**新测试**：`tests/delivered_materials.rs`（**audience-aware**，不是一刀切禁令）：

- `no_developer_facing_material_sends_the_role_to_the_game_process`：Developer 面材料（`developer.md` + `godot-dev.md`）不得出现**具体** `running_game_<tool>` 名（`running_game_*` 通配形式允许，因为禁止本身需要解释）。
- `the_developer_skill_explains_why_the_game_process_is_not_its_self_test`：技能须含编辑器侧替代且**不含** `tools call editor_play_scene`。
- `the_tester_facing_materials_still_receive_the_game_process_recipe`：**非空洞性那一半**——`godot-testing.md` 必须仍然带着具体游戏进程工具名（否则"修好"可以靠把通道从所有文档里删光）。
- `the_generated_tool_index_is_a_catalogue_not_an_instruction`：生成的 `TOOLS.md` 不得携带祈使式 `tools call running_game_`。
- `the_developer_prompt_states_the_round_wide_route_and_its_staleness`：`developer.md` 须陈述新窗口事实，且不得残留 `during your call it may be unavailable`。

**红**：实现前 5 条中 3 条红（§1 之外的原始输出见下），**绿**：5 passed / 0 failed。

```
test no_developer_facing_material_sends_the_role_to_the_game_process ... FAILED
test the_developer_prompt_states_the_round_wide_route_and_its_staleness ... FAILED
test the_developer_skill_explains_why_the_game_process_is_not_its_self_test ... FAILED
test result: FAILED. 2 passed; 3 failed
```

同批**必须**同步的既有文本契约（都实测转绿）：`tool_vocabulary`（我新增注释里出现过裸 `play_scene` 整词，已改为 `editor_play_scene`；**该测试在第一次全量套件里真的抓住过我**——见 §7.8）、`developer_contract`、`e1_increment`、`role_shell_contract`、`prompt_shell_contract`、`tool_discovery`、`artifact_hygiene`。

### 3.4 ④ 生产接线必须有覆盖

**生产落点（被保护对象）**：`src/harness/mini.rs:66-69` 的 `CappedEnvironment::new(Box::new(environment), inv.limits.max_tool_output_bytes as usize)`。

**新测试**：`tests/harness_cap_wiring.rs::the_harness_itself_bounds_what_the_next_request_carries` —— 对回环假模型端点跑**真实 `MiniHarness::invoke`**：第一次响应给出一个产出 2 MiB 结果的 shell 工具调用，然后**检查紧随其后的那次请求的原始 body**（`smoke-t9` 事故跨越的正是这条边界）。

- 断言：第 2 次请求 body 内**不存在** 64 KiB 连续填充字节；**包含** `TRUNCATION_MARKER`（显式标注而非静默截断）；body < 256 KiB。
- **红（删掉包装的植入 P1，见 §4）**：`the request that follows the 2 MiB tool result must not carry it: 2097786 bytes were sent` —— 2,097,786 B 的整段回放，正是 D4 说"删掉包装仍全绿"的那个洞。
- **绿**：1 passed / 0 failed。

### 3.5 ⑤ 恢复被毁证据 + 更正失实自述

**选择**：任务书给了"外科式脱敏"或"旁注"二选一。**选外科式**，理由：D2 的伤害不是"文件里存在敏感字节"而是"脱敏破坏了记录边界"，旁注虽然最保真却会把**凭据通道**原样留在入库证据里（任务书 §3 也要求被提交证据不得含环境转储）；外科式能做到"记录数/行尾/其它每个字节不变"且同时移掉通道。取回原文用 `git show dc9d350:<path>`（== `3adab37^`）。

**字节级前后对比**（全部我自己复算）：

| 事实 | 原始 `dc9d350`（=`3adab37^`） | DR-69 后 `3adab37` blob | DR-69 后**工作树**（`core.autocrlf=true`） | DR-70 后 |
|---|---|---|---|---|
| 字节数 | **52200** | 52176（−24） | **52359**（+183 CR） | **52205**（+5） |
| LF | **184** | **183** | 183 | **184** |
| CR | **0** | 0 | **183** | **0** |
| 记录数（非空 LF 段） | **184** | **183**（`s008` 两条被并成一行） | 183 | **184** |
| `dir /b -p` 命中 | **1** | **0** | 0 | **1** |

**根因（我复算出的精确机制）**：DR-69 的规则从 `HOH_MODEL_API_KEY=` 匹配到**下一个 `"`**；而原记录本来就在 `…/AppD` 处**被截断**（该行没有闭合引号），于是匹配穿过换行、吃掉了下一条记录的前缀 `s008 rc=0 | dir /b -p; echo "`：`$(cat /c/Users/wyl/AppD`(25 B) + LF + 30 B 被 30 B 的占位符替换 ⇒ **−24 B、少一条记录、少一个 LF、`dir /b -p` 消失**。工作树的 +183 CR 纯粹是 `core.autocrlf` 把 52176 字节重新落盘成 CRLF（52176+183=52359，与验收的 52200→52359 完全吻合）。 **（DR-71 更正：这句里的 `25 B` / `30 B` / `30 B` 失实，被替换的字节跨度与被写入的占位符实测为 `dr69_replaced_bytes` / `dr69_marker_bytes`，见 §3.5b 的生成块；净差 −24 与其余结构事实不变。）**

**DR-70 的外科式编辑（逐字节证明）**：`git show dc9d350:<path>` 原样取回后，**只**把 `$(cat /c/Users/wyl/AppD`（25 B，全文唯一，`HOH_MODEL_API_KEY=` 也全文唯一）换成 `<redacted-key-path-by-DR-69>`（30 B）： **（DR-71 更正：`25 B`/`30 B` 两处失实——实测 `worktree_replaced_bytes` / `worktree_marker_bytes`，见 §3.5b。）**

```
current == original-with-one-substitution: True
common prefix 2736  common suffix 49441
replaced original bytes b'$(cat /c/Users/wyl/AppD'
replaced current bytes  b'<redacted-key-path-by-DR-69>'
everything else identical: True
len 52205  cr 0  lf 184  records 184  dirb-p 1
sha256 141fda10599534d7e6e30d5716178c859e650f80a2636ba99a1f04fe3623752c
git hash-object 763a3a3e4f847efadc820efbf584461ced591c17   # == HEAD:<path> 提交后
```

**行尾陷阱的结构性修复**：`.gitattributes` 新增 `.spec/hof-rs/tasks/TASK-SMOKE-T9-evidence/** -text`（与既有 `tests/fixtures/dr58/** -text` 同一模式、同一理由），使**任何人的检出**都不会再把这份证据改写成 CRLF。

**测试（先红）**：`tests/frozen_evidence.rs` 三条：

```
the_frozen_command_dump_keeps_its_line_endings_and_record_count ... FAILED
  ... must stay pure LF ...  left: 183  right: 0
the_frozen_command_dump_keeps_the_record_that_documents_the_p_directory ... FAILED
  ... `dir /b -p` ...  left: 0  right: 1
the_frozen_command_dump_carries_no_credential_channel ... ok
```

绿：3 passed / 0 failed。第三条断言赋值行的**行尾位置未移动**（该行仍以 `HOH_MODEL_API_KEY="<redacted-key-path-by-DR-69>` 结束）、不含 `HOH_MODEL_API_KEY="$(cat`、且不含任何由 `runtime::secrets::known_secrets` 解析出的凭据明文。

**`REDACTION.md` 的更正方式**：**旧文字保留并置于"Superseded DR-69 text (retained verbatim, marked corrected)"小节**，顶部加 "CORRECTION (DR-70)" 框，逐条写清：真实字节变化表（上表）、DR-69 那句 "**53 bytes** were removed. Nothing else in the file was touched" 为**不实**及其机制、DR-70 恢复原文的方式与原样字节、`.gitattributes` 的钉住、以及哪条测试守它。

### 3.5b DR-71 更正：字节声明**由命令计算**，不再手写

<!-- DR-71-CORRECTED-BEGIN -->
本节 §3.5 的叙述把两处**被替换的字节跨度**写成了手写数字，其中两处失实（DR-70 的验收用脚本复算后判为 A2）。更正**不在这里手写数字**：正确值就是生成块里的 `dr69_replaced_bytes`、`dr69_marker_bytes`、`worktree_replaced_bytes`、`worktree_marker_bytes` 四个键；原 blob、DR-69 blob 与工作树的字节总数、行尾、记录数、`dir /b -p` 计数也在同一块里，由 `scripts/byte_claims.py` 从 git 对象与工作树**计算**并写入，`tests/byte_claims.rs` 独立复算并逐键比较。 §3.5 里已经正确的净差与全部结构事实不变，且**旧文字逐字保留**、原处标注 "DR-71 更正"。 本区域刻意不含任何手写字节计数；出现即由 `tests/byte_claims.rs` 判红。
<!-- DR-71-CORRECTED-END -->

<!-- DR-71-BYTE-CLAIMS-BEGIN -->
DR-71 generated byte claims - written by `python scripts/byte_claims.py --write`, re-computed by tests/byte_claims.rs.  Do not edit by hand.
path = .spec/hof-rs/tasks/TASK-SMOKE-T9-evidence/experiment/dev1_commands.txt
original_blob = dc9d350
original_bytes = 52200
original_cr = 0
original_lf = 184
original_records = 184
original_dir_b_p = 1
dr69_blob = 3adab37
dr69_bytes = 52176
dr69_delta_bytes = -24
dr69_lf = 183
dr69_cr = 0
dr69_records = 183
dr69_dir_b_p = 0
dr69_replaced_bytes = 52
dr69_marker_bytes = 28
worktree_bytes = 52205
worktree_delta_bytes = 5
worktree_cr = 0
worktree_lf = 184
worktree_records = 184
worktree_dir_b_p = 1
worktree_replaced_bytes = 23
worktree_marker_bytes = 28
<!-- DR-71-BYTE-CLAIMS-END -->

---

## 4. 非空洞性：5 处仅生产代码的受控植入

驱动脚本在仓外（`C:\Users\wyl\AppData\Local\Temp\dr70\plants.py`，每次植入前把目标文件**逐字节**备份到仓外 `bak/`）。全部植入只落**生产代码**（`src/**`，其中 `godot-dev.md` 是 `include_str!` 进二进制并被注入每个角色视图的交付材料，属生产资产）。

| 植入 | 文件（生产） | 禁用的机制 | 红（真实输出） | 回退判据 |
|---|---|---|---|---|
| **P1-cap-wrapper** | `src/harness/mini.rs` | 删掉 `CappedEnvironment::new(...)` 包装 | `harness_cap_wiring` RED：`must not carry it: 2097786 bytes were sent` | 字节比较 `BYTE-IDENTICAL`；`hash-object 85b0eef0bf472000b152997db0f41cc18464a13c` == HEAD blob；porcelain 只剩未跟踪任务书；`diff --stat` 空 |
| **P2-route-validation** | `src/tools/mod.rs` | 采纳前不校验（`validate_published_route` 结果丢弃） | `game_route_across_processes` **3 RED**（陈旧 route 被采纳、调用"成功" `left Some(0) right Some(0)`） | `BYTE-IDENTICAL`；`7831f3593fcdbb9d0fa38f43b04d8cc937b8015e` == HEAD |
| **P3-no-round-game-start** | `src/runtime/run_loop.rs` | 删掉"第一个角色之前启动轮次游戏" | `round_game_window` **2 RED**：`entering the Developer phase the published route must already exist: RoleProbe { route_exists: false, exit_code: Some(5), stderr: "hoh: game_endpoint_unavailable … (DR-43)" }` | `BYTE-IDENTICAL`；`d2e1d3d8276d5bab008ca757987d83da46826227` == HEAD |
| **P4-no-round-teardown** | `src/runtime/run_loop.rs` | 删掉包装层的无条件收尾 | `round_game_window` **2 RED**（`route must be withdrawn when the round ends` / `a round that failed before the battery must still withdraw its published route`） | `BYTE-IDENTICAL`；同上 blob |
| **P5-skill-game-recipe** | `src/prompts/skills/godot-dev.md` | 把被删的 `running_game_get_node_property_samples` 自证配方塞回 §5 | `delivered_materials` RED（`no_developer_facing_material_sends_the_role_to_the_game_process`） | `BYTE-IDENTICAL`；`578cce712ec175770f7d1677d26bce360a532198` == HEAD |

每次回退的**四重判据**（见 plants.py 的 `verify`）：① Python **逐字节**与仓外备份比较 `BYTE-IDENTICAL`（本仓 `core.autocrlf=true`，行尾改写对 git 不可见，`cmp` 强制）；② `git hash-object == HEAD:<path>` blob；③ `git status --porcelain` 为空——植入运行期间它显示的唯一一条是**开工前就已存在**的未跟踪任务书 `.spec/hof-rs/tasks/TASK-DR70.md`（不是任何植入改动），任务书随后已随本报告一并提交，故本批最终状态下 `git status --porcelain -uall` **字面为空**；④ `git diff --stat` 为空。

**植入若落在承载不变量的测试里**：**没有**。P1..P5 全部落在 `src/**`；植入期间我仅运行"对应"的测试 target，`P5` 未触碰任何测试文件。

---

## 5. 禁区自查（真实输出）

```
# 四条 runs/** 基线（口径与验收 §7.1 相同：PowerShell 5.1 / zh-CN / Get-ChildItem -Recurse -Force -File /
# 仓根相对小写 POSIX 路径 + 字节数 + 小写 SHA256 / 三列 \t 连接、\n 分行、整体 UTF-8 取 SHA256 / Sort-Object）
runs/smoke-t6 files=135 hash=c144ef3219e21dd322978e41a5531d53dee270619c026585505920f9277a9c03 newest=2026-09-29 02:32:01
runs/smoke-t7 files=115 hash=6e4c1595753c2cdefb16e4d2e5f05242ca202c70c81a93e98ae2b9c92b520fb7 newest=2026-09-29 14:41:14
runs/smoke-t8 files=358 hash=6d11b2c61ec507b5f02525ddc0e7f7adb08763cd2439a4b08788b7fe51bdf5a7 newest=2026-09-30 07:58:28
runs/smoke-t9 files=83  hash=541e2d814e563ba667c95bde49765d05e44cf11aa5ab90b2f44931f30136ca9d newest=2026-09-30 11:27:29
```

- **摘要口径自证**：`runs/smoke-t6 = c144ef32…7a9c03` **命中任务书 §3 点名要求的值**；四条与验收 §7.1 **逐字相同**。
- **写-删检查（连"写过再删"也不放过，用 mtime）**：切点 `2026-09-30 13:53:00`（本批开工时间）之后，`runs/smoke-t6|t7|t8|t9` 下**新文件数 = 0**、**新目录数 = 0**（四棵树全部 `newer_files=0 newer_dirs=0`）⇒ **本批对 `runs/**` 零写入、零临时物**。
- **`.workspace/mario` 未改**：按运行时排除集 `{.hoh,.git,.godot,.import}` 逐字节比对，活体工程树 **17 文件与 `runs/smoke-t9/versions/1f3d20ed…` 完全一致**，且与 `iter-1/planner-view` 完全一致；`-p` 目录仍在，mtime `2026-09-30 10:51:57`（**未触碰**，清理归拥有该工作区的批次）。
- **`PRD-mario.md`**：`sha256 = 4c81c3a9995f0b3afdf01421a0c3be88573cceefc284ce9bafbfda141f0f5c3a`（与验收 §7.3 逐字相同）。
- **嵌套引擎未改**：`git -C godot-mcp/godot rev-parse HEAD = fc63af77c33368c4a1bb839c95d19750554f63a3`，`status --porcelain -uall` **0 行**；外层 pathspec 真命中对照 `ls-files godot-mcp = 6484` vs `ls-files godot-mcp/godot = 0`。
- **无新依赖**：`git diff --numstat 9aebbe1..HEAD -- Cargo.toml Cargo.lock` **空**。
- **未 push / 未 stage**：`origin/master = 9aebbe15f13508d1ee5063505b2827ee59cc041a`（全程未变）；`git diff --cached --stat` 空；本批 6 个提交全部本地。
- **`DECISIONS.md` / `.workspace/mario` / `PRD-mario.md` / `godot-mcp` 在我这 6 个提交里零改动**：`git diff --numstat a58bd72..HEAD -- DECISIONS.md .workspace/mario .spec/hof-rs/PRD-mario.md godot-mcp` **空**。
- **仓内无临时物**：本批最终状态下 `git status --porcelain -uall` **字面为空**（任务书 `TASK-DR70.md` 开工时未跟踪、现已随本报告一并入库；`TASK-DR69.md` 本来就是跟踪的，故这符合本仓既有惯例）。分析产物与脚本全部在仓外 `C:\Users\wyl\AppData\Local\Temp\dr70\`，仓内**零**临时文件。
- **三个假绿陷阱各实测并给正确读法**：
  1. `git diff --stat -- definitely/not/a/real/path` ⇒ 输出空、`exit=0`。**读法**：空 diff 什么都不证明，必须先证 pathspec 真命中（`ls-files godot-mcp = 6484` vs `godot-mcp/godot = 0`）。
  2. cmd 吃 `^`、且 `&` 链里的 `%errorlevel%` 在解析期展开：`cmd /c "git rev-parse dc9d350^"` ⇒ `dc9d350dff7357fec88d532ed5d2661a6ce7de18`（`^` 根本没到 git，解析成 `dc9d350` 自己）；`cmd /c "git cat-file -e dc9d350^:definitely/not/here & echo errorlevel=%errorlevel%"` ⇒ 命令确实 `fatal:` 了，却打印 `errorlevel=0`。bash 侧同题：真命中 `exit=0`、真未命中 `exit=128`。**读法**：只有 bash 的结果有证据力。
  3. 外层仓不跟踪引擎树/工作区/轮目录：`check-ignore -v runs/smoke-t9/meta.json` ⇒ `.gitignore:12:runs/`；`.workspace/mario/project.godot` ⇒ `.gitignore:11:.workspace/`；`godot-mcp/godot` ⇒ `.gitignore:33:godot-mcp/godot/`；`git diff --stat -- godot-mcp/godot/bin` ⇒ 空 + `exit=0`。**读法**：对忽略路径的空 diff 什么都没说。

---

## 6. 遗留风险与未验证项（严格区分实测/推断）

### 6.1 未验证（离线硬约束，**一律不是实测**）

1. **真机时序**：本批**没有跑任何真机轮**，未启动 Godot、未碰外部端口、未联网、未调模型端点。所有"运行时会这样跑"的结论都来自**离线替身 + 真实 `run_loop::run` + 真实 `hoh` 子进程**，不是引擎观测。
2. **轮次级 `editor_play_scene` 在"已经有一局在跑"时的引擎行为未验证**（推断，非实测）：本批每轮最多触达 **3 次**游戏生命周期（轮首为 Developer；电池在冻结候选上自启；电池之后为 Tester）。**前提**是引擎的 `editor_play_scene` 在**已有游戏运行时**不会被接受（所以本批总在启动前先 `editor_stop_scene`，且电池前必先停轮次会话）。若该前提不成立，多余的一次 stop/play 只是浪费几秒；若引擎反而允许"两个游戏"，则两局会争同一端口——**这是本批最大的真机不确定性**，我无法离线证伪，也**不给出"真机会成功"的概率**：该断言需要真机轮证据。
3. **Developer 自己 `editor_play_scene` 的后果未验证**：`developer.md` 的自证工具清单（DR-69 加入、`e1_increment:780` 要求）仍含 `editor_play_scene`。若 Developer 在角色内自启动一局，轮次会话可能被替换 ⇒ 之后 adopt 到的 route 指向已死端口，**按 ② 的设计会以 `game_endpoint_unavailable` 明确拒绝**（而不是传输失败）；电池随后仍会重启并在冻结候选上取证据。技能（`godot-dev.md`）已明确禁止这么做，但提示词层面未禁止（改动它会牵动 `e1_increment` 的既有断言，本批按"最小一致"处理并在此披露）。
4. **pid 重用**：Windows 的 pid 会被复用，`process_is_alive` 对"被复用的死 pid"会答"活"。这正是**可达性检查**存在的理由（两者同时满足才放行）。
5. **`run_loop.rs:537` 的历史语义**：任务书点名的 `run_loop.rs:537`（旧版本的 `use_game_route_file`）现在位于 `:600` 一带；它受**同一个** `use_game_route_file` 约束（已在 `endpoint.rs` 的单测与三条集成测试里覆盖采纳路径），但"harness 自身复用 `--run-id` 时是否会采纳上一轮遗留"只有 `a_route_left_by_another_round_is_not_inherited` 这条**离线**证据，没有真机证据。
6. **`CappedEnvironment` 之外是否还有别的路径能把未截断字符串送进下一次请求**：我只证了 `MiniHarness::invoke` 这条主路径（D4 的那条）现在**有覆盖**，并仍沿用验收 U8 的边界（未穷举 `exception_info`、模板变量等）。
7. **`REDACTION.md` 之外还有没有别的"自述与字节不符"**：我只审计了任务书点名的这一处。
8. **`TASK-SMOKE-T9-evidence/**` 其余文件未逐字节审计**（只审计了 `dev1_commands.txt`/`REDACTION.md` 与本批相关的部分）。
9. **`-p` 目录仍在**：任务书 §3 禁止改 `.workspace/mario/**`，该清理归拥有该工作区的批次（验收 D7 / D272 已裁定）。本批**没有**动它。

### 6.2 已实测的风险/代价

- **采纳期的可达性探测在"被拒绝"时要等约 2s**（本平台实测 `ConnectionRefused raw=Some(10061) elapsed≈2.0s`）。后果：一条**陈旧** route 的调用会先用 ~2s 得到**明确拒绝**，而不是用同样量级的时间得到传输失败——时间不增，信息量增。**活**端点是瞬时的。
- **FFI 的引入**：`src/tools/endpoint.rs` 新增 `#[cfg(windows)]` 的 `kernel32` 声明与 `#[cfg(unix)]` 的 `kill(0)`。这是本仓第一处 `unsafe`；范围极小（一个布尔判定、句柄在所有路径关闭），并有单测（活 pid vs 被收割子进程的 pid）。**不引入依赖**是硬约束，`tasklist`/PowerShell 子进程会让**每次** `hoh tools call` 依赖一个带区域设置的子进程，故不取。
- **信任边界未变**：route 文件仍是"角色可写"的（验收 R4）。② 不能也不声称能解决它——文件是否被伪造不在三项检查的射程内（已在 `validate_published_route` 的文档里写明）。

---

## 7. 诚实披露

1. **不声称 E1/E3 met**。本批没有任何真机证据；E1（增量）与 E3（轮内证据形态）的状态与本批无关。
2. **不 push**（按要求）；`origin/master` 全程未变。
3. **我改了两处既有断言，逐条交代、逐条判"非放宽"**：
   - `tests/game_route_across_processes.rs::registering_publishes_the_route_and_stopping_withdraws_it`：由"死端口 63999 + pid 11 也被采纳"改为"活回环端点 + 本进程 pid 被采纳"。这是 **② 的契约变更**（旧断言断言的正是被判定为缺陷的行为），不是放宽；同文件同时**新增**三条"陈旧 ⇒ 必须明确拒绝"。
   - `tests/developer_contract.rs::godot_dev_skill_is_a_real_recipe_book` 的 needle 清单：**一个具体工具名离场**（`running_game_get_node_property_samples`，正是 D5 的病灶）、**两个具体要求入场**（`editor_get_errors`、`before you changed the code`），并在文件内注明理由。同一批新增的 `tests/delivered_materials.rs` 用**audience-aware** 规则把正反两侧都钉住。
4. **`developer.md` 的 [policy] 段在 DR-69 之后已经是假事实**（"该 route 只由电池注册、你的调用期间可能不可用"）。这不是 D5 点名的那一处，但它是 ① 的直接后果；我把它一起改成新事实并加了测试（`the_developer_prompt_states_the_round_wide_route_and_its_staleness`）。**如果验收认为 `developer.md` 不该在本批被动**，这是我的越界，我在此显式交出。
5. **我的第一次全量套件是 449 passed / 1 failed**：`tool_vocabulary::the_retired_vocabulary_is_gone` 抓到我新增注释里的**整词 `play_scene`**（旧 GDExtension 词汇），改成 `editor_play_scene` 后转绿。我把这次失败当作**守卫真的在工作**的证据登记，而不是悄悄修掉。
6. **`TASK-DR70.md` 开工时是未跟踪的**（调度者留下），本批在报告定稿时把它**与本报告一并提交**（`TASK-DR69.md` 本来就是跟踪的，属本仓惯例）。因此**植入回退时**的 `git status --porcelain` 显示过这一条未跟踪任务书，而它**不是**任何植入改动；本批最终状态下 porcelain **字面为空**，我在 §4/§5 两处都如实标注。
7. **本批没有声明"路由问题已彻底解决"**：① 修的是**窗口包含性**（可离线证）；**正常的真机轮里 Developer/Tester 是否真的用上这条通道、以及引擎是否接受轮次级 play/stop 序列，只能由真机答**（§6.1-2）。
8. **⑤ 的选择是二选一里的一个**：我选了外科式而非旁注，理由已在 §3.5 写清；若验收更看重"原文一字不动"，这条可以回退成旁注（原文已可从 `dc9d350` 逐字节取回）。
9. **本报告写完后未再修改**（除本句所述的定稿动作）。
