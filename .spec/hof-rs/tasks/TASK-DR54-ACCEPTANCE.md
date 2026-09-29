# TASK-DR54-ACCEPTANCE — §15 批次（DR-54/55/56）独立验收报告

- 验收者：**独立验收子代理**（无上游对话上下文；结论全部由我自己复现）
- 任务书：`.spec/hof-rs/tasks/TASK-DR54-ACCEPT.md`（权威）；规范：`.spec/hof-rs/DESIGN-DETAIL.md` **§15（v0.10）**
- 实现者工件（**线索，非证据**）：`TASK-DR54-IMPL.md`、`TASK-DR54-REPORT.md`
- 被测提交（批次起点 `53f6f9d`）：`513069c`(DR-56)、`df95339`(DR-55)、`6329e5c`(DR-54)、`b3ccef9`(非空洞证据)、`9ff9cd2`(报告)
- 验收时 HEAD：**`e3a2a511fbcf21bab56f180da0e49921face4568`**（`9ff9cd2` 之上多出的 `e3a2a51` = D238 文档提交，不含 `src/**`/`tests/**` 改动；本报告的 `src/tests` 范围 diff 与之无关）
- 验收日期：2026-09-29（取自本机时钟与已入库提交）
- **验收者改动**：只做了两处受控植入-回退（§3），外加一个**临时**测试文件（用完删除）；全程 `git status --porcelain` 归于**完全空**（含 untracked）——见 §1.9。

---

## 1. 结构化结论

```json
{
  "verdict": "pass",
  "criteria": [
    {
      "id": "SUITE",
      "pass": true,
      "evidence": "cargo test --offline 跑两遍（pristine 树 + 全部实验回退后），两遍均 EXIT=0。自算聚合：35 个 target 的 `test result:` 行合计 passed=342 failed=0 ignored=7，大写 FAILED=0、panicked=0。唯一 ignored>0 的 target 是 tests/godot_smoke.rs（7 条真机门控），而 `git diff --stat 53f6f9d..HEAD -- tests/godot_smoke.rs` 为空 ⇒ ignored 未随本批增加。328→342 的 +14 逐项对上：mcp_reliability +2、evidence_battery +3、endpoint_liveness +7（新文件）、src/tools/endpoint.rs 单测 +2。"
    },
    {
      "id": "NON_VACUITY",
      "pass": true,
      "evidence": "实现者 7 处植入全部落在 src/** 生产代码（nonvacuity.ps1 的 -File 依次为 reliable.rs×3、endpoint.rs×2、mod.rs、godot.rs），没有一处改测试；7 份日志均 EXIT=101 且带真实断言失败（如 nv5 `assertion left == right failed: round 1: a business error is an answer and must not count / left: 1 right: 0`，行 tests/endpoint_liveness.rs:335）。恢复证明我独立核对：restored_blob 与实验当时那棵树一致（nv1/nv2/nv6 f52d3ade=HEAD reliable.rs；nv3/nv4 bb0035e2=HEAD endpoint.rs；nv5 ddf6f4e4=HEAD mod.rs；nv7 fae0060a=6329e5c 的 godot.rs，因 b3ccef9 之后只改了 godot.rs 的文档注释）。我自己另做两处设计不同的实验（§3），其中 classifier 恒真使两条目标测试同时转红。"
    },
    {
      "id": "NO_WEAKENING",
      "pass": true,
      "evidence": "`git diff -U0 53f6f9d..HEAD -- tests` 得全部删除行，逐条核对：没有任何测试被删除；tests/endpoint_liveness.rs 是纯新增 509 行。全部 4 处删除都逐条给出等价/更强的替代：the_game_probe_calls_are_gdscript_bodies→every_surviving_execute_gdscript_call_is_a_gdscript_body（保留“必须带 return”，并新增“不得含 Input.action_press(/release(”，比原来只查 mutation 分支更强）；删掉的 `readings >= 4` 与 a_usable_game_channel_makes_the_replay_green 里 `execute_gdscript >= 8`、`>= 6` 是对 DR-54 明文要拆掉的机制计数，替代品是 `play_input_recording >= 4`、`run_test_scenario >= 4`、五类工具逐字入库、`script_mutations.is_empty()` 与 quadruple>=4 且 channel=game_process（范围更强）；has_action==true 换成 pressed==true（在语义注入被接受的模型下等价且更直接）；retries_are_bounded_and_preserve_the_real_error 把触发类别 -32603→transport 是 DR-56 的设计变更而非放宽（同一测试仍断言 attempts==3 与 message 逐字存活）；AUDITED_TOOLS 15→19 只加不减。无任何为变绿而放宽的断言。"
    },
    {
      "id": "DR54",
      "pass": true,
      "evidence": "①`running_game_execute_gdscript` 只剩一个执行点 src/adapter/godot.rs:1473，唯一使用者是 1317-1323 的 read-only player_position 探针；判决 1360-1364 只读 pressed / axis_after / game_process_reachable / not_bound，probe_position 仅出现在 1324-1328 的诊断 note 与 1365-1370 的 evidence_note 文本里。②ACTION_NOT_BOUND 判据在 1353-1359 = `is_action_not_bound_code(refusal_code)`（= code == -32602，godot.rs:2773-2775）**且** refusal 文本含 ACTION_NOT_BOUND_MARKER（godot.rs:2779）——裸 -32602 落到 ACTION_BINDING_UNKNOWN。③映射表 11 处基线行号我用 `git show 53f6f9d:src/adapter/godot.rs` 逐行核对，1234/1247/1251/1255/1262/1298/1302/1311/1645/1774/1783 **全部逐字命中**，且 baseline 的 game_script* 调用点确实只有这 11 处（其余匹配是 4 个 helper 定义与 #[cfg(test)] 解析器），无不可映射项；抽样 #1(get_node_properties)、#2(-32602+文面)、#5(create/play/test_scenario)、#9-#11(input_replay 循环内 semantic_inject_action) 与代码实际一致。"
    },
    {
      "id": "DR55",
      "pass": true,
      "evidence": "①按端点分键：src/tools/mod.rs 的 `liveness: BTreeMap<String, EndpointLiveness>`，键为 JSON-RPC URL，`endpoint_state`/`observe_liveness` 都按该键读写；editor 与 game 各自成键（endpoint_liveness::the_editor_endpoint_state_is_separate 绿）。②阈值 `ENDPOINT_DEATH_THRESHOLD: u32 = 2`（src/tools/endpoint.rs:83）。③首次失败不判死：observe 只在 `count >= 2` 时标死（endpoint.rs:161-167），a_single_transport_failure_does_not_kill_the_endpoint 绿，且我的 nv4 型对照（实现者）在阈值=1 时转红。④业务错误不计入：call_with_meta 的 Err 分支只对 McpTransportError 记 Err(())，其余一律 Ok(()) 复位/不计数（mod.rs:288-297），business_errors_never_count_toward_the_streak 让真 loopback 对偶回 3 次 -32602 后 count 仍 0 且随后一次真传输失败后仍为 1。⑤**真零请求**：判死短路在 `spawn_blocking` **之前** return（mod.rs:279-285 vs 287-289），且我用自建 live counting 对偶独立证明（§3 实验 B：判死后把对偶改成完全健康，3 次调用后连接计数纹丝不动、失败仍是带 game_endpoint_unavailable 的定型拒绝）。⑥DR-20 保留：poll 只被 `failure.endpoint_verdict` 终止（reliable.rs:344），业务错误照旧轮询，既有 readiness_poll_succeeds_after_three_failures 绿。"
    },
    {
      "id": "DR56",
      "pass": true,
      "evidence": "①分类集中在单一具名函数：`is_retryable_failure(&McpFailure)`（reliable.rs:144-146）是全仓**唯一**读 `.retryable` 的地方（另一处 :158 是唯一赋值点，在 failure_from 内），消费点唯一——`another_attempt_is_allowed`（:220-230），由重试环 :263-270 调用。②业务错误恰一次：retries_are_class_aware_business_errors_are_never_retried 断言 `channel.call_count() == 1`、`failure.attempts == 1`、`code == Some(-32602)`、mcp-errors.jsonl 恰 1 行；我另核代码：mcp.rs:207 的传输层重试只对 `is_transport`（= `ureq::Error::Transport`，mcp.rs 内具名函数）成立，业务错误是 Ok 应答后被解析成 McpError ⇒ 对业务错误全链路恰 1 次 HTTP 请求。③传输失败仍重试：the_retry_classifier_is_the_single_decider 断言 call_count()==4（max_retries=3）。④“最后一次真实失败”保留：`last = Some(failure)` 每次整体覆盖（reliable.rs:260）且环结束时返回 `Err(last)`（:272），测试断言 attempts==3、code==None、message 逐字存活，实现者 nv6（只留第一次）转红。"
    },
    {
      "id": "GUARDS",
      "pass": true,
      "evidence": "godot-mcp：`git ls-files godot-mcp | count = 6484`（证明 pathspec 命中），`git diff --stat 53f6f9d..HEAD -- godot-mcp` 空、`git log --oneline 53f6f9d..HEAD -- godot-mcp` 空。runs/**：smoke-t6 = 135 文件、最新 mtime 2026/9/29 02:32:01（早于批次起点 10:58:16）、frame-00.png 4246 B sha256 bef0936daba1b16a23e7b25bd1fc432d946afaaca6d7b0636fbeafc898b67ea2（与 D223 的 bef0936d…7ea2 一致）、runs/ 下 mtime 晚于 2026-09-29 06:00 的文件数 = 0；我另自算目录摘要（口径见 §2 附注）：runs/smoke-t6 files=135 digest=c144ef3219e21dd322978e41a5531d53dee270619c026585505920f9277a9c03，runs 全域 files=4970 digest=c6d6f4ec5ba7e80d8077ea1a0de9fb5876f0229a0ca57f94e2f7061e767c6a84。PRD-mario.md sha256 = 4c81c3a9995f0b3afdf01421a0c3be88573cceefc284ce9bafbfda141f0f5c3a（逐字一致）。`git diff --stat 53f6f9d..HEAD -- Cargo.toml Cargo.lock` 空（无新依赖）。未 push/未 stage：`git diff --cached --stat` 空、ahead origin/master = 4（6329e5c/b3ccef9/9ff9cd2/e3a2a51 未推送；513069c/df95339 早在 origin，与 D238 的自我披露一致）。离线：tests/*.rs 里出现的非 loopback 主机只有 `http://remote.invalid` 与 `http://x`（前者不可解析、后者是纯解析单测），无真实外网主机。"
    },
    {
      "id": "RESIDUALS",
      "pass": true,
      "evidence": "①“传输×上层重试乘法”属实且我量化了：一次上层调用内传输层最多 1+`tools.max_retries`=3 次 HTTP 尝试（mcp.rs:207，config/hoh.yaml:53 max_retries=2），判死按**上层调用**连续 2 次计（mod.rs:288-297 每次 call_with_meta 只 observe 一次）⇒ 判死前最多约 6 次 HTTP 尝试；按 tools.timeout_seconds=120（hoh.yaml:52）计，判死前仍可能烧掉约 12 分钟。②三条仅属推断的引擎形态假设确认“只有推断”：ACTION_NOT_BOUND 依赖引擎原文含该字面量（godot.rs:2779 硬编码标记）、`input_axis` 作为非节点属性名（godot.rs:1269 semantic_axis_sample）、`events` 的 InputEventAction 形状（godot.rs:1568），离线不可证；报告另列出 run_test_scenario 步骤字段名，披露比要求更宽。③E3 未被声称 met（报告 §0/§8/§9.8 与 D238 均明写只能由真机 T=1 判定）。④DR-50B 最小复现 spike 未跑（离线批次），据实。"
    },
    {
      "id": "TRAPS",
      "pass": true,
      "evidence": "陷阱1（不存在的 pathspec 不报错）：`git diff --stat 53f6f9d..HEAD -- path/that/does/not/exist` 无输出且 exit=0，同形式的 `-- src/tools/reliable.rs` 得 91+/5- ⇒ 空 diff 只有在先证明 pathspec 命中（我对 godot-mcp 用 git ls-files=6484 证明）后才可信。陷阱2（cmd 的 ^）：`cmd /c \"echo df95339^:tests/endpoint_liveness.rs\"` 输出 `df95339:tests/endpoint_liveness.rs`（^ 被吃）；正确读法下 `git cat-file -e df95339^:tests/endpoint_liveness.rs` = exit 128（该文件由 df95339 新增，父提交没有），而经 cmd 的同一条命令 = exit 0 ⇒ 会把“本批新增的文件”伪造成“它早就在”，即凭空造出“本批什么都没加”。正确读法：用 pwsh 直传、或先 `git rev-parse <rev>^` 再拼接。"
    }
  ],
  "defects": [
    {
      "id": "DEF-1",
      "severity": "major",
      "what": "DR-55 的“判死后真的零请求”在本批自己的测试里**没有被非空洞地验证**，而报告把它当成已验证：报告 §3.2 写“断言 failure.attempts == 1 且 consecutive_transport_failures 仍为 2（计数不再增长 ⇒ 确实没再发请求）”。该推理无效——`EndpointLiveness::observe` 在 `unavailable` 时**直接 return**（src/tools/endpoint.rs:154-156），所以判死后无论是否又发了请求，计数都冻结在 2。行为本身是对的（我独立证明，见 §3 实验 B），缺的是测试的有效性。",
      "reproduction": "在 src/tools/mod.rs 的判死短路里，于 return 之前插入一次 `spawn_blocking(client.call_traced(...)).await`（即“还发一次”），然后：(a) 跑实现者的 tests/endpoint_liveness.rs::two_transport_failures_kill_the_endpoint_and_later_calls_do_not_retry ⇒ **仍然 ok / 绿**（1 passed; 6 filtered out），完全没抓到；(b) 跑我自写的 live-counting 对偶测试 ⇒ **FAILED**，`assertion left == right failed: ZERO requests may be sent after the endpoint is declared dead, but the live double saw a new connection: left: 3 right: 2`。⇒ 本批没有任何一条测试能区分“零请求”与“零重试但还发一次”。行为已由我独立确认正确，故不构成语义未达成，但报告的证据陈述必须更正，并应补一条能数请求的测试。"
    },
    {
      "id": "DEF-2",
      "severity": "minor",
      "what": "`InputChannelProbe.has_action` 现在是**恒为 None 的死字段**，但仍被序列化进发布出去的原始证据（`.hoh/deterministic/raw/input_channel_probe.json` 的 `channel.has_action`），且全仓已无任何读者（生产代码只在 godot.rs:1388 写 None，测试侧旧断言已删）。证据消费者可能把 null 误读成“动作不存在”。",
      "reproduction": "`Select-String -Path src/**/*.rs,tests/*.rs -Pattern 'has_action'`：生产侧只有 1388 的 `has_action: None` 与 probe_scripts 的遗留字符串；`channel.has_action` 无任何读取点。对照旧测试 `raw[\"channel\"][\"has_action\"] == true` 已被替换成 `pressed`。"
    },
    {
      "id": "DEF-3",
      "severity": "info",
      "what": "测试替身仍完整模拟**旧的脚本协议**：tests/evidence_battery.rs:497-516 的 execute_gdscript 分支保留 `Input.action_press(`/`action_release(`/`has_action`/`get_axis`/`is_action_pressed` 分支，其中 action_press 分支仍会真的把 `pressed_in_game` 置 true。也就是说“语义工具承重”这一结论并不是由替身强制出来的，而是靠额外的形状断言（script_mutations.is_empty() 等）兜住；替身本身并不排斥回归到拼装 GDScript。",
      "reproduction": "读 tests/evidence_battery.rs:488-527。当前有断言兜底（the_input_channel_critical_path_is_built_on_semantic_tools、every_surviving_execute_gdscript_call_is_a_gdscript_body、a_usable_game_channel_makes_the_replay_green 的反断言），所以不是活缺口；但若将来删掉那些断言，替身会默默放过脚本注入。"
    },
    {
      "id": "DEF-4",
      "severity": "info",
      "what": "报告 §6 nv7 行给出的 restored blob `fae0060a…` 与**当前 HEAD** 的 src/adapter/godot.rs blob `a65377c2…` 不一致。原因是 nv7 实验在 `6329e5c` 那棵树上做，随后 `b3ccef9` 又改了 godot.rs。报告没写明“恢复是相对实验当时的树、而非 HEAD-now”。",
      "reproduction": "`git rev-parse 6329e5c:src/adapter/godot.rs` = fae0060a…；`git rev-parse HEAD:src/adapter/godot.rs` = a65377c2…；`git diff 6329e5c..b3ccef9 -- src/adapter/godot.rs` 只有 13 行 **文档注释** 改动（无行为改动）。其余 5 份恢复 blob（f52d3ade/bb0035e2/ddf6f4e4）与 HEAD 一致。⇒ 不是未回退的植入，但足以让“拿 HEAD blob 去核对”的复核者误判。"
    },
    {
      "id": "DEF-5",
      "severity": "info",
      "what": "§15.1 列出的优先语义工具是 `get_node_property_samples`/`create_input_recording`+`play_input_recording`/`run_test_scenario`/`assert_node_state`/`move_player_to_target`；实现未使用 `running_game_assert_node_state` 与 `running_game_move_player_to_target`，且映射表未说明为何不需要它们。§15.1 的措辞是“优先”，故不构成违规。",
      "reproduction": "`git grep -n 'assert_node_state\\|move_player_to_target' HEAD -- src tests` 无命中；映射表（报告 §2.2）的“接替工具”列只出现 get_node_properties / get_node_property_samples / create_input_recording / play_input_recording / run_test_scenario / stop_input_recording。"
    }
  ],
  "risks": [
    "DR-55 判死**之前**的重试乘法仍在：按 config/hoh.yaml（tools.max_retries=2、timeout_seconds=120）估算，一次上层调用最多 3 次 HTTP 尝试，判死按上层调用连续 2 次计 ⇒ 最多约 6 次 HTTP 尝试、判死前仍可能烧掉约 12 分钟。DR-55 只把“判死之后”的干烧压到 0；“多久才判死”没有改善。且“连续 2 次传输层失败”实际是在**调用粒度**计数（每次 call_with_meta 只 observe 一次），不是 HTTP 粒度——这与 §15.2“第一次仍按配置重试一次”的措辞可以自洽，但存在解释空间。",
    "ACTION_NOT_BOUND 依赖引擎的真实拒绝文面里含字面量 ACTION_NOT_BOUND（godot.rs:2779 硬编码标记）。若真机文面不含该标记，probe 会保守地落到 ACTION_BINDING_UNKNOWN（fail-closed、不会假 verified），代价是 P3 证据缺失。",
    "godot.rs:1360-1364 的分类顺序存在未被覆盖的混合情形：若 create/play 以 -32602+标记 拒绝（not_bound=true）而 run_test_scenario 成功（pressed=true），且 NODE_PROPERTIES 的 name 非空（game_process_reachable=true），则第一个 match 分支 (true,true) 先命中 ⇒ 判 GAME_INPUT_CHANNEL_OK，把一次真实的 ACTION_NOT_BOUND 掩盖掉。现有替身的 ActionMissing 会让 create/play/scenario **一起**拒绝，故没有任何测试覆盖这个混合态。这是读码得到的情形，真机是否可发生未证。",
    "`running_game_get_node_property_samples` 是否接受非节点属性名 `input_axis`、游戏端点是否接受 events 里的 InputEventAction 形状、run_test_scenario 步骤字段名——三项都只有推断依据（契约 schema/description），离线不可证。",
    "runs/smoke-t6 的“目录摘要算法”仍未文档化（D223 遗留）。我改用与算法无关的口径（135 文件 + 最新 mtime + frame-00.png 尺寸/sha256 + 自算摘要并写明口径），但摘要算法本身仍是待办。",
    "E3 能否真正 met 未知：本批只交付结构性改造，必须由真机 T=1（引擎 4.8.dev.mono.custom_build.035edfce7，含 TASK-151 修复）判定，且不得用二进制 sha256 当引擎新鲜度判据。"
  ],
  "unverified": [
    "E3 的 met/not_met（只能由真机 T=1 轮次判定；本批正确未作断言）。",
    "引擎对“InputMap 没有该动作”的真实应答文面是否包含 ACTION_NOT_BOUND（离线不可问引擎）。",
    "running_game_get_node_property_samples 是否接受 input_axis 这类非节点属性名。",
    "游戏端点是否接受 events 里的 InputEventAction 形状（{\"type\":\"action\",\"action\":…,\"pressed\":true}）。",
    "running_game_run_test_scenario 的步骤字段名（type/action/pressed/seconds/node_path/property/expected/operator）在真机是否逐字接受。",
    "DR-50B 的最小复现 spike（离线批次禁止起引擎/碰端口，未执行）。",
    "判死前“约 12 分钟”是**由配置值推算**的最坏情形，不是实测墙钟；真实耗时未被本批计时。",
    "tests/godot_smoke.rs 的 7 条真机门控（离线批次不得运行，仅确认其断言被 ignore、文件零 diff）。",
    "5 个语义工具是否在真机被接受（本批只证明了其**参数形状**符合 177 条契约，且是对着替身跑通的）。"
  ]
}
```

**真实命令与退出码（我自己跑的）**

| # | 命令 | 真实结果 |
|---|---|---|
| 1 | `cargo test --offline`（pristine 树，首次） | `EXIT=0`；35 个 target；**342 passed / 0 failed / 7 ignored** |
| 2 | `cargo test --offline`（两处植入均已回退、临时文件已删后复验） | `EXIT=0`；35 个 target；**342 passed / 0 failed / 7 ignored**；大写 `FAILED`=0、`panicked`=0、`error[`=0 |
| 3 | `cargo test --offline --test mcp_reliability retries_are_class_aware_business_errors_are_never_retried`（植入：classifier 恒真） | `FAILED`，`left: 3 / right: 1`，退出码 1 |
| 4 | `cargo test --offline --test mcp_reliability the_retry_classifier_is_the_single_decider`（同一植入） | `FAILED`，退出码 1 |
| 5 | `cargo test --offline --test zz_acceptance_dr54_probe`（我自写，HEAD） | `1 passed; 0 failed`，`EXIT=0` |
| 6 | 同一自写测试（植入：判死后仍发一次请求） | `FAILED`，`left: 3 / right: 2` |
| 7 | `cargo test --offline --test endpoint_liveness two_transport_failures_kill_the_endpoint_and_later_calls_do_not_retry`（同一植入） | **`ok. 1 passed`（没抓到）** |

---

## 2. 逐项核对表

| # | 复核项（任务书 §1） | 结论 | 我的证据 |
|---|---|---|---|
| 1 | 套件 exit 0 / 342 / 0 / 7，ignored 未增加，328→342 自洽 | **pass** | 两遍全绿；godot_smoke.rs 在批次区间零 diff；+14 = 2+3+7+2 |
| 2 | 非空洞性（≥2 处我自做、改行为而非改测试） | **pass**（附 DEF-1） | 7 处植入全在 src/**；我另做 2 处（§3）；其中“零请求”一项本批自测无效 |
| 3 | 既有断言未被削弱 | **pass** | `git diff -U0 53f6f9d..HEAD -- tests` 的每条删除行逐条判等价/更强；无测试被删 |
| 4 | DR-54 ①只读探针且值不入判决 ②-32602**且**显式文面 ③11 处映射一致（抽样≥4） | **pass** | godot.rs:1353-1359 / 1360-1364 / 1317-1323；11 处基线行号逐字命中；抽样 4 处一致 |
| 5 | DR-55 分键 / 阈值=2 / 首次不判死 / 业务错误不计 / 真零请求 / DR-20 保留 | **pass** | endpoint.rs:83/153-170；mod.rs:279-289；live 对偶实测零请求；readiness 测试绿 |
| 6 | DR-56 单一具名分类器 / 业务错误恰一次 / 传输仍重试 / 最后一次真实失败 | **pass** | reliable.rs:144-146/158/220-230/263-270/272；call_count()==1 且 journal 1 行；call_count()==4 |
| 7 | 禁区自查（真实输出） | **pass** | 见 §1 GUARDS：godot-mcp 零 diff 零提交、runs 逐字节、PRD sha 一致、无新依赖、未 push/未 stage |
| 8 | 残留实项独立判定 | **pass** | 见 §5：乘法属实且已量化；三条推断确实只是推断；E3 未声称 met；spike 未跑 |
| 9 | 两个假绿陷阱实测 | **pass** | 陷阱1 exit=0 的空 diff + pathspec 命中对照；陷阱2 cmd 把 `rev^` 吃成 `rev`（128 → 0） |

**§2 附注（我自算的目录摘要口径，写明以便复现）**：对目标目录递归枚举**文件**（`-Force`，含隐藏文件），对每个文件取相对仓库根的路径（`\`→`/`，转小写）、字节长度、SHA256（小写 hex），按「路径」升序排序，用 `\t` 连接三列、行间用 `\n`、**不加尾随换行**，整体以 UTF-8 编码后取 SHA256。结果：`runs/smoke-t6` files=135 digest=`c144ef32…7a9c03`；`runs` 全域 files=4970 digest=`c6d6f4ec…6c6a84`。

---

## 3. 反例清单（我自己的植入 + 观测 + 是否推翻）

**实验 A —— 把具名分类器改成恒真（实现者的 nv 未覆盖这一处，§15.3 ③ 的字面要求）**

| 项 | 内容 |
|---|---|
| 植入 | `src/tools/reliable.rs::is_retryable_failure`：`error.retryable` → `let _ = error; true`（改**行为**，不是改测试） |
| 植入前 blob | `f52d3ade1d504bee46f84c6daea0ff5da32c3e54`（= HEAD） |
| 植入后 blob | `fb8866bf5e7fcb882456c99c90c5c1b58caad8de`（≠ 植入前 ⇒ 植入确实生效） |
| 观测 1 | `mcp_reliability::retries_are_class_aware_business_errors_are_never_retried` → **FAILED**，`assertion left == right failed / left: 3 / right: 1` |
| 观测 2 | `mcp_reliability::the_retry_classifier_is_the_single_decider` → **FAILED** |
| 回退三法 | `git checkout -- src/tools/reliable.rs`；`git hash-object` = `f52d3ade…` == `git rev-parse HEAD:src/tools/reliable.rs`；`git status --porcelain --untracked-files=no` 空；`git diff --stat -- src/tools/reliable.rs` 空（且同一命令形式对真实改动过的路径有输出，证明 pathspec 生效） |
| 是否推翻 | **不推翻**。§15.3 ③“把分类改成恒真 ⇒ 必须变红”成立，且是双向的（A1 业务错误被重试、A2 未分类失败被重试）。 |

**实验 B —— “判死后真的零请求”（我自建 live counting 对偶，实现者的测试在这一项上无效）**

| 项 | 内容 |
|---|---|
| 方法 | 临时新建 `tests/zz_acceptance_dr54_probe.rs`（**用后删除**）：一个**活的** loopback JSON-RPC 对偶，统计 accept 到的连接数；先让前 2 次连接**不发一个字节就关闭**（= smoke-t6 的传输失败形态：状态行不来），端点因此被判死；随后把对偶切成**完全健康**；再调 3 次并断言连接计数不动、失败仍是带 `game_endpoint_unavailable` 的定型拒绝；最后以“重注册后同一地址能正常应答且计数+1”作为计数器的对照。 |
| HEAD 上观测 | `1 passed; 0 failed`，`EXIT=0` ⇒ 判死后**确实零请求**（若发过一次，健康的对偶会应答成功而不是给定型拒绝，且计数会 +1）。 |
| 是否推翻 | **不推翻 HEAD**（DR-55⑤ 语义成立）。 |
| 但 | 同一实验的**植入版**（在 mod.rs 判死短路里 return 之前插一次 `spawn_blocking(call_traced)`）：我的测试 **FAILED**（`left: 3 / right: 2`），而实现者自己的 `two_transport_failures_kill_the_endpoint_and_later_calls_do_not_retry` **仍然绿**。⇒ **推翻**报告 §3.2 用以支撑“零请求”的推理（详见 DEF-1）。 |
| 回退证明 | 删除临时文件后 `git status --porcelain`（**含 untracked**）为**完全空**；`git status --porcelain --untracked-files=no` 空；`git diff --stat` 空；4 个受影响文件的 `git hash-object` 逐一 == `git rev-parse HEAD:<path>`（mod.rs `ddf6f4e4…`、reliable.rs `f52d3ade…`、endpoint.rs `bb0035e2…`、godot.rs `a65377c2…`）。注：该临时文件**从未入库**（HEAD 中不存在），故其“恢复”以“文件不存在 + 树全空”证明。 |

**对实现者 7 处植入的独立核对（读日志 + 核 blob，非重跑）**

| # | 植入文件（是否生产代码） | 日志真实 RED | restored blob 与哪棵树一致 |
|---|---|---|---|
| nv1 | `src/tools/reliable.rs`（生产） | `EXIT=101`，`left: 3 / right: 1` | `f52d3ade…` = HEAD ✓ |
| nv2 | `src/tools/reliable.rs`（生产） | `EXIT=101`，`left: 1 / right: 4` | `f52d3ade…` = HEAD ✓ |
| nv3 | `src/tools/endpoint.rs`（生产） | `EXIT=101`，`tests/endpoint_liveness.rs:229` panic | `bb0035e2…` = HEAD ✓ |
| nv4 | `src/tools/endpoint.rs`（生产） | `EXIT=101`，`tests/endpoint_liveness.rs:288` panic | `bb0035e2…` = HEAD ✓ |
| nv5 | `src/tools/mod.rs`（生产） | `EXIT=101`，`left: 1 / right: 0`（:335） | `ddf6f4e4…` = HEAD ✓ |
| nv6 | `src/tools/reliable.rs`（生产） | `EXIT=101`，`left: 1 / right: 3`（:206） | `f52d3ade…` = HEAD ✓ |
| nv7 | `src/adapter/godot.rs`（生产） | `EXIT=101`，`tests/evidence_battery.rs:1705` panic | `fae0060a…` = `6329e5c` 的树（**非** HEAD-now，见 DEF-4）✓ |

**没有任何一处“植入”是改测试**：7 处的 `-File` 全在生产代码；`nonvacuity.ps1` 逐条 `Assert-Clean` + `finally { git checkout -- $File }` + blob 前后比对（并断言 planted ≠ before），设计正确。

---

## 4. 对 DR-54 / DR-55 / DR-56 的独立语义结论

**DR-54 — pass。** E3 关键路径的可判定性已经**不再由调用方拼装的 GDScript 承重**：基线 11 处 `game_script*` 调用点（我把行号逐字对齐到 `1234/1247/1251/1255/1262/1298/1302/1311` + 循环内 `1645/1774/1783`）全部改由契约语义工具产出（`get_node_properties` / `get_node_property_samples` / `create_input_recording` / `play_input_recording` / `run_test_scenario` / `stop_input_recording`），残留的唯一 `execute_gdscript` 使用者是只读 `Player.position` 探针，**其值只进诊断文本、不进任何判决**（godot.rs:1360-1364 的判决表达式里没有 `probe_position`）。`ACTION_NOT_BOUND` 的收紧是正确的且比原来更严：需要**语义拒绝的 `-32602`** 与**回包显式说明**同时成立（1353-1359），裸 `-32602`（请求格式错）落到 `ACTION_BINDING_UNKNOWN`；我用“语义全拒但脚本探针仍应答 ⇒ 仍判 UNKNOWN”的既有测试与读码双向确认。**唯一保留意见**是引擎真实文面是否含该字面量（推断，见 §5/§6）。

**DR-55 — pass。** 状态按端点（JSON-RPC URL）分键（BTreeMap）；阈值常量为 **2**；`observe` 的 `Ok(())` 覆盖**一切应答**（含业务错误）并复位计数、只有 `McpTransportError` 记 `Err(())`，因此**首次失败不判死、业务错误永不计入**；判死后在 `spawn_blocking` **之前**返回定型拒绝（`UNAVAILABLE` + `game_endpoint_unavailable` + `endpoint_state=<json>` + `attempt(s)=0`），**真零请求、零重试、零等待**——我用自建 live counting 对偶独立证明（§3 实验 B），不依赖实现者的推理。DR-20 未被破坏：轮询只被 `endpoint_verdict` 终止，业务错误继续轮询（`readiness_poll_succeeds_after_three_failures` 绿）。重新注册会 `arm_endpoint` 重新武装，旧地址的判死不泄漏；编辑器端点状态独立。**一处必须更正**：本批自己的测试并不能证明“零请求”（DEF-1），是**代码 + 我的实验**证明了它。

**DR-56 — pass。** 分类收敛到一个具名函数 `is_retryable_failure`（全仓唯一读 `.retryable` 之处），赋值点唯一（`failure_from`），消费点唯一（`another_attempt_is_allowed`），无散落特例；**业务错误恰尝试 1 次**（测试断言 `call_count()==1` 与 journal 恰 1 行；我再核传输层 `post()` 只对 `ureq::Error::Transport` 重试，业务错误根本进不了重试分支 ⇒ HTTP 层面也恰 1 次）；**传输失败仍重试**（`call_count()==4`），且我自己的“分类恒真”植入把两个方向都压红；“重试从不洗白失败——返回最后一次真实失败”保留（`last` 每次整体覆盖、环结束返回 `Err(last)`，测试断言 attempts==3 与 message 逐字存活，实现者 nv6 转红）。

---

## 5. 残留实项的独立判定

| 残留项（实现者披露） | 我的独立判定 |
|---|---|
| ① 传输层 × 上层重试“乘法”仍存在 | **属实，且比披露更值得注意**。传输层最多 `1+tools.max_retries=3` 次 HTTP 尝试（mcp.rs:207，hoh.yaml:53），判死按**上层调用**连续 2 次计（mod.rs:288-297 每次 `call_with_meta` 只 observe 一次）⇒ 判死前最多约 6 次 HTTP 尝试；按 `tools.timeout_seconds=120`（hoh.yaml:52）估算，判死前仍可能烧掉**约 12 分钟**——与 §15.2 写明的动机同量级。DR-55 真正压掉的是“判死之后”的干烧。另可指出：§15.2 的“连续 2 次传输层失败”在实现里是**调用粒度**而非 HTTP 粒度；这与同段“第一次仍按配置重试一次”可以自洽，但属解释空间，建议在 DR-57 里显式定死。 |
| ② 三条仅属推断的引擎形态假设 | **属实，三条都只是推断**，且未在任何地方被写成已证：ACTION_NOT_BOUND 依赖引擎原文含该字面量（godot.rs:2779）；`input_axis` 作为非节点属性名（godot.rs:1269）；`events` 的 `InputEventAction` 形状（godot.rs:1568）。报告另列了 run_test_scenario 的步骤字段名（更宽的披露）。离线不可证，我只能确认“未被伪装成实测”。 |
| ③ E3 未被声称 met | **属实**。报告 §0/§8/§9.8 与 D238 都明写只能由真机 T=1 判定；任务书 §5 的禁令被遵守。 |
| ④ DR-50B 最小复现 spike 未跑 | **属实**（离线批次禁止起引擎/碰端口），仍在待办。 |

---

## 6. 未验证项与理由

见 §1 JSON 的 `unverified` 数组（E3 的 met 判定、引擎真实拒绝文面、`input_axis` 采样、`events` 形状、scenario 步骤字段名、DR-50B spike、判死前 12 分钟是**推算**而非实测墙钟、7 条真机门控、5 个语义工具在真机的接受度）。核心理由统一：**本批是离线批次**，凡需要引擎的都不可得；我严格遵守了“不启动 Godot、不碰任何引擎端口、不联网、不调模型”的约束。

**关于“不碰端口”的诚实披露**：我运行的测试与我的自建实验，都只在进程内 `TcpListener::bind("127.0.0.1:0")` 绑定**内核分配的临时环回端口**（这与实现者测试、以及任务书要求我“自己跑套件”不可避免），**从未**连接/探测 9877 或任何引擎端口，也没有发起任何外部网络请求（tests/ 内出现的非 loopback 主机仅 `remote.invalid` 与 `http://x`，前者不可解析、后者是纯字符串解析单测）。

---

## 7. 我没有独立复核的部分

1. **7 处植入我没有逐一重跑**：我核对了脚本、日志（真实 `EXIT=101` 与断言文本）、以及 restored blob，并**自己做**了 2 处不同设计的植入（§3）。若要 100% 独立，应把 7 处全部重跑——我判断上面三项证据已足以支撑“改的是行为不是测试”（7 处的 `-File` 全在 `src/**`，这是脚本层面可判定的）。
2. **7 条 `tests/godot_smoke.rs` 真机门控我没有运行**（离线约束），只确认了它们仍是 `ignored` 且该文件在批次区间零 diff。
3. **`runs/**` 我没有与批次之前的快照逐字节对比**：`runs/` 被 gitignore、无基线副本，我用的是“文件数 + 最新 mtime + frame-00.png 尺寸/sha256 + 批后 0 文件被改 + 我自算的全域摘要”这一组与算法无关的证据（口径见 §2 附注），并另记了摘要值以便后续轮次对照。
4. **`src/adapter/godot.rs` 的 527+/195- 我没有逐行通读**：我读了判决路径、注入路径、ACTION_NOT_BOUND 判据、映射表涉及的 11 处与 input_replay 的循环；其余部分（playbook 文档、playwright 文本、解析器）只做了针对性检查。
5. **`godot-mcp/**` 的 6484 个文件我只验证了“本批零 diff 零提交”**，没有审计引擎侧内容（明确不在本批范围）。
6. **177 条工具契约我没有重新解析**：我只确认了 `every_tool_call_hof_rs_makes_matches_the_contract_schema` 在扩充到 19 个工具后仍绿，未自己独立枚举 177 条（D223 的验收者做过这件事）。

---

## 8. 给下一批的建议（**我没有改任何代码**）

1. **（对应 DEF-1，建议最高优先）** 新增一条能**数请求**的测试来覆盖“判死后零请求”：把实现者那个用**已关闭端口**的用例换成/补上一个**活的计数对偶**（先关连接两次判死、再切成健康、断言连接数不变 + 失败仍是定型拒绝 + 重注册后计数会 +1）。我的临时实验已证明这种测试有牙、且当前套件无牙。同时**更正报告 §3.2** 那句无效推理。
2. **（残留①，记 DR-57 候选）** 把“连续 2 次传输层失败”的粒度定死（HTTP 尝试 vs 上层调用），并考虑让 `McpClient::post` 的传输重试对**已知会判死的端点**不再放大（或在 `observe_liveness` 里按 HTTP 尝试计数），使判死前的最坏耗时与 §15.2 的动机一致（当前推算仍约 12 分钟）。
3. **（DEF-2）** 决定 `InputChannelProbe.has_action` 的去留：删掉，或在 evidence 文案里显式标注“DR-54 起恒为 null，不再承载任何结论”，避免证据消费者误读。
4. **（DEF-5 / 风险 3）** 在真机轮次里顺带确认两件事：`running_game_assert_node_state` / `move_player_to_target` 是否应当承担部分断言；以及“create/play 拒绝但 scenario 接受”的混合态在真机是否可能出现（若可能，当前分类顺序会把它误判成 `GAME_INPUT_CHANNEL_OK`）。
5. **（DEF-4 / 记账）** 报告里凡引用 blob 恢复的点，写清“相对实验当时的树（`6329e5c`）而非 HEAD-now”；复核纪律里也把“用 HEAD blob 核对历史实验”这一误判陷阱记进去。
6. **（真机轮次）** 按 §15.4 执行 T=1 + 独立验收，引擎身份记 `4.8.dev.mono.custom_build.035edfce7` 并保留 `--version` 与监听者路径；**不得**用二进制 sha256 当新鲜度判据；顺带关闭 §6 的 5 项引擎形态推断与 DR-50B 的最小复现 spike。
7. **（推送）** 本报告完成时 `origin/master` 仍为 `82f2da2`，本地领先 4 个提交（`6329e5c`/`b3ccef9`/`9ff9cd2`/`e3a2a51`）。我未 push、未 stage、未改历史。我的结论是 **pass**，推送决定权在你；如推送，请按 D238 的自我约束先列 `git log origin/master..master --oneline` 确认不含待验收批次提交（本批已验收，可推）。

---

## 附：验收者行为自证

- 我全程**只读**为主；写操作仅有：①两次受控植入（`src/tools/reliable.rs`、`src/tools/mod.rs`）并各自 `git checkout --` 逐字节回退（blob 三法证明见 §3）；②一个**临时**测试文件 `tests/zz_acceptance_dr54_probe.rs`（**已删除**，从未入库）。
- 收尾状态：`git status --porcelain`（**含 untracked**）= **空**；`git status --porcelain --untracked-files=no` = 空；`git diff --stat` = 空；`git diff --cached --stat` = 空；`git rev-parse HEAD` = `e3a2a511fbcf21bab56f180da0e49921face4568`（与验收开始时一致，我未改写历史、未 rebase/force、未 push）。
- 两处植入都以 `git hash-object` == `git rev-parse HEAD:<path>` 证明（mod.rs `ddf6f4e4…`、reliable.rs `f52d3ade…`），并且我在**同一命令形式**下验证过 pathspec 确实命中（避免“空 diff 陷阱”）。
