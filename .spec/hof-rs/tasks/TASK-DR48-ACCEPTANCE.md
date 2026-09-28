# TASK-DR48-ACCEPTANCE — 修复包（DR-48..DR-53）独立验收报告

- 验收者：**独立验收子代理**（无上游对话上下文；唯一任务来源 `.spec/hof-rs/tasks/TASK-DR48-ACCEPT.md`）。
- 落点：`F:\moonbit-hof-rs`（外层仓 `master`，验收时 `HEAD = 4fe077d`，`origin/master = 4b9bd44`，`master` 领先 21）。
- **不继承任何结论**：本报告里的每一条证据都是我自己跑出来/读出来的；实现者的
  `TASK-DR48-REPORT.md`（`.spec/hof-rs/tasks/TASK-DR48-REPORT.md`）只当线索。
- 本批为**离线**验收：**未**启动 Godot、**未**接触 9877 或任何端口（编辑器 PID 108432 全程未被触碰）、
  **未**联网、**未**调用任何模型端点；除任务书 §3 授权的**植入-回退**实验外全程只读。
- 唯一产物即本文件。**回报父代理只有一行：本报告路径。**

---

## 1. 结构化结论 + 真实命令与退出码

```json
{
  "verdict": "pass",
  "criteria": [
    {
      "id": "DR-48",
      "pass": true,
      "evidence": "`cargo test --offline` 全集 34 target passed=328/failed=0/ignored=7（我自己跑的，见 §2.0）。豁免集合是常量数据 `ENGINE_INFO_BANNERS`（src/adapter/godot.rs:3243-3246）+ 具名匹配函数 `is_engine_info_banner`（:3258-3261，逐字 trim 后 contains，非前缀）+ 过滤函数 `non_banner_editor_errors`（:3267-3277）；判定点 src/adapter/godot.rs:790-817，未命中走原语义 `(false, \"…UNAVAILABLE: the editor is not clean\")`（:803-808）。两条横幅逐字等于引擎字面量：`godot-mcp/godot/modules/mcp_server/mcp_server.cpp:605` 与 `:645`；真错误行 `ERROR: [MCP] SceneTree never became available; MCP server disabled.` 也存在（同文件 :223）且**不在**豁免表内。头号目标（非空洞）用受控实验证伪：把 `is_engine_info_banner` 临时改成恒真后 `cargo test --offline --test launchable_gate` 得 `test result: FAILED. 9 passed; 3 failed`（三条反例测试同时红，见 §3 E1）；把 `ENGINE_INFO_BANNERS[1]` 末尾加一个空格（只多一个尾空格）后 `an_engine_info_banner_does_not_close_the_gate` FAILED（test result: FAILED. 11 passed; 1 failed，见 §3 E2）。两次实验均已 `git checkout --` 回退，`git status --porcelain` 与 `git diff --stat` 双空、`git hash-object src/adapter/godot.rs == git rev-parse HEAD:src/adapter/godot.rs == 606c1f4d3b3a46a8137c519d7dac657162488f58`。"
    },
    {
      "id": "DR-49",
      "pass": true,
      "evidence": "①调用形态：src/adapter/godot.rs:1101 `let args = json!({});` 后 :1102 调 `running_game_capture_screenshot`；测试 `the_screenshot_call_carries_no_filesystem_path`（tests/evidence_battery.rs:1932-1964）除断言 `calls[0] == json!({})` 外，还在替身里把引擎取值域变成硬约束（tests/evidence_battery.rs:448-456：非 `res://`/`user://` 的 `save_path` 直接返回 -32602）。引擎侧依据我自己读过：`godot-mcp/godot/modules/mcp_server/tools/running_game_capture.cpp:62` `save_path accepts res:// or user:// only`、:81 同义。②调用前作废旧文件：src/adapter/godot.rs:1087-1097（`artifact_fingerprint` → `invalidate_artifact` 改名 `*.stale-<ts>`，失败则删除，:2214-2240）。③`ok` 由新鲜度决定：src/adapter/godot.rs:1160-1188（`artifact_is_fresh`，:2195-2204）。④回退不再被旧文件压制：:1130 `if !materialized`。⑤反例测试三条（tests/evidence_battery.rs:1932 / :1969 / :2005）。受控实验：把 `invalidate_artifact` 临时改成恒 `Ok(None)`（空操作）后 `cargo test --offline --test evidence_battery` 得 `test result: FAILED. 29 passed; 1 failed`，失败点正是 `a_stale_png_is_never_mistaken_for_this_runs_screenshot` panicked at tests\\evidence_battery.rs:1995（“the stale file must have been invalidated before the call (DR-49)”，见 §3 E3）⇒ DR-49② 有牙。回退后同样双空 + blob 一致。"
    },
    {
      "id": "DR-50A",
      "pass": true,
      "evidence": "契约依据我自己读了引擎源码：`godot-mcp/godot/modules/mcp_server/tools/running_game_script_execution.cpp:57-59` “`code` (string, required, must not be blank) is a GDScript **function body**”，:80-82 “a body without `return` answers {\"result\": null, \"result_type\": \"Nil\"}”，:83 “`code` that does not compile is `-32602`”；void 当值确为编译错误：`godot-mcp/godot/modules/gdscript/gdscript_analyzer.cpp:3498`（另有 :3549、:3732 同一条）`Cannot get return value of call to \"%s()\" because it returns \"void\".`。hof-rs 侧修复后读值脚本 `return str(...)`、副作用保持语句（src/adapter/godot.rs `probe_scripts`），并被 `the_game_probe_calls_are_gdscript_bodies`（tests/evidence_battery.rs:1543-1596）与 `check_arguments` 的 void-当值规则（tests/evidence_battery.rs:1359-1382）双重覆盖。该测试非空洞：我的替身（我自己读的，tests/evidence_battery.rs:488-527）忠实模拟引擎 body 语义，任何读值脚本一旦去掉 `return` 即得 Nil，测试末尾的 `GAME_INPUT_CHANNEL_OK` 断言（:1588-1595）会失败。"
    },
    {
      "id": "DR-50B.characterisation",
      "pass": true,
      "evidence": "我自己从 `runs/smoke-t6/**` 原始文件复算（脚本只读、跑完即删），六条判据全部支持“引擎侧可用性缺陷”：(1) 第 5 次 `running_game_execute_gdscript` 确实是**第一条编译不过**的 code —— raw/input_channel_probe.json 里 8 条 execute_gdscript 按文件顺序为 ok,ok,ok,ok,**not_ok**,…（前四条 code 分别是 `str(get_tree()…position.x) + …`、`str(InputMap.has_action(\"move_right\"))`、`str(Input.is_action_pressed(\"move_right\"))`、`str(Input.get_axis(\"move_left\", \"move_right\"))`，第五条 `str(Input.action_press(\"move_right\"))`）。(2) 失败在传输层：mcp-errors.jsonl 39 行，`running_game_execute_gdscript` 10060 ×3（timestamp 1790618321 / 1790618683 / 1790619044，间隔 362s/361s），报“有正确答复的主机没有反应，连接尝试失败。(os error 10060)”。(3) 随后监听消失：同文件 10061 ×9（`running_game_get_node_properties` ×9、`running_game_get_node_property_samples` ×15），首条 10061 在 1790619051，晚于首条 10060 **730 s**；我用 `Select-String` 抽 10060/10061 行里的端口，36 行**全部**指向 `127.0.0.1:63698`。(4) 编辑器端点同轮全程健康：raw 记录里 editor 侧调用 req=26..43 全部 `ok=true`（editor_rescan/open_scene 26-27、editor_get_errors 29、editor_play_scene 30、editor_get_input_actions 31、editor_simulate_input_action 32-39、editor_get_collision_info 40-42、editor_stop_scene 43），其中 editor_stop_scene（raw/editor_stop_scene.json）还带真实记录 `game_endpoint_invalidated = {endpoint http://127.0.0.1:63698/mcp, pid 101872, port 63698, source auto_free_port}`，ok=true。(5) 两轮端口/pid：pass1 65333/109964 与 pass2 63698/101872 都在 traj/developer.attempt2.json 里能找到（65333 与 109964 确实出现于该文件；63698/101872 是隔代 pass2 的登记值，贯穿 19 个工件）。(6) `godot-mcp/**` 在 `4d3ff58..HEAD` **零改动**（`git diff --stat` 与 `git log --oneline 4d3ff58..HEAD -- godot-mcp` 双空）。置信度：对“故障在引擎那一侧”**高**；对引擎内部机制**未定**（离线不可证）——与 D222 的自我标注一致。详见 §4。"
    },
    {
      "id": "DR-51",
      "pass": true,
      "evidence": "`editor_status` 由真实 `GET <endpoint>` 填充：src/tools/mcp.rs:49-59（`fetch_editor_status`，ureq GET，一次请求、失败返回 String），接入 src/runtime/engine_identity.rs:34-50（`editor_status_for`：不驱动引擎则**完全不发请求**并返回 `Value::Null`；驱动则取值、失败退化 null）与 :71-73（`probe` 真实调用）。`game_endpoint` 在**登记当刻**回写：src/tools/mod.rs:256-262（`game_history` 在注册时写入，`clear_game_endpoint`(:264-268) 只清 `game` 不清 `game_history`）。测试证据两条路径我读了：有端点 —— `the_run_meta_keeps_the_game_endpoint_the_battery_registered`（tests/launchable_gate.rs:531-572）断言 route 已被清（:544-551）而 `meta.json.engine.mcp.game_endpoint` 仍是 `http://127.0.0.1:9878/mcp` / port 9878 / source auto_free_port / reason null；无端点 —— `an_unreachable_endpoint_yields_no_status_and_no_failure`（tests/engine_identity.rs:600-623）断言 `editor_status == null` 且 reason 是字符串；驱动/非驱动分岔 —— `the_status_fetch_is_gated_on_the_adapter_driving_an_engine`（:629-647，`false` 分支的 fetch 闭包是 `|_| panic!(...)`，即“多一次网络请求就炸”）；真响应逐字入库 —— `the_editor_status_is_the_verbatim_get_mcp_body`（:581-595，回环 HTTP 替身，tools=154）。`{}`→`null` 的收紧：`EngineIdentity::unavailable` 的 `editor_status` 由 `Value::Object(Default::default())` 改为 `Value::Null`（src/adapter/engine.rs），全仓消费者自查 `grep` 无依赖 `{}` 者，且全集 328 测试全绿。"
    },
    {
      "id": "DR-52",
      "pass": true,
      "evidence": "①诊断自洽：`the_editor_input_map_diagnostic_agrees_with_its_own_record`（tests/evidence_battery.rs:1248-1303）同时断言“与记录一致”（observation 含 `lists all three actions`）、**反例**（不得再含 `does not list`，即 D220/DEF-E 那处自相矛盾必须消失）、以及“公布自己读到的条数”（`{names.len()} action(s)`），并反向再跑一遍 `RealEditorMap`（真的缺失时仍必须说 `does not list` 且给出条数）。解析侧 `parse_input_actions` 读名字数组（引擎真实形态 `{\"actions\":[名字…],\"count\":N}`）。②参数形状独立抽样：**不是**只用实现者的表——我写了独立脚本，交叉核对三方：(a) `godot-mcp/recovery/TEST-CASES.md` 的 **177** 条 `TC-TOOL-*` 行里解析出的 `必填=` 集合；(b) 仓库内嵌夹具 `tests/fixtures/mcp/tools_list.json` 的 `inputSchema.required`（177 条；`src/tools/index.rs:18` 用 `include_str!` 内嵌同一文件）；(c) `src/adapter/godot.rs` 里 hof-rs **真正发送**的参数。结果：**177/177 必填集合完全一致，0 处不匹配**。真实调用点（我自己脚本抽出的 `self.call(\"<tool>\", args)` 与构造它的 `json!`）：`editor_get_collision_info{node_path}`、`editor_get_errors{max_lines:50}`、`editor_get_input_actions{}`、`editor_open_scene{path}`、`editor_play_scene{mode:\"main\"}`、`editor_rescan_project_filesystem{}`、`editor_simulate_input_action{action,pressed}`、`editor_stop_scene{}`、`project_read_scene_file_content{path}`、`running_game_capture_frames{count:1,frame_interval:10}`、`running_game_capture_screenshot{}`、`running_game_execute_gdscript{code}`、`running_game_get_node_properties{node_path}`、`running_game_get_node_property_samples{node_path,properties,frame_count,frame_interval}`、`running_game_get_scene_tree{max_depth:-1}` —— 共 **15** 条，覆盖 hof-rs 真正调用的**每一个游戏态工具**（capture_screenshot / capture_frames / execute_gdscript / get_node_properties / get_node_property_samples / get_scene_tree）与 9 条编辑器态。逐条与 `TEST-CASES.md` 行号：`editor_get_errors`(=:166, req 0/opt 1, 默认 max_lines=50)、`running_game_capture_screenshot`(=`godot-mcp/recovery/TEST-CASES.md` 内 `TC-TOOL-running_game_capture_screenshot` 行, req 0/opt 1 save_path)、`running_game_get_scene_tree`(req 0/opt 4, max_depth 默认 -1)、`running_game_get_node_properties`(req 1 node_path)、`running_game_capture_frames`(req 0/opt 3, count 默认 5、frame_interval 默认 10)、`editor_get_collision_info`(req 0/opt 1 node_path)、`editor_simulate_input_action`(req 1 action/opt pressed、strength)、`editor_get_input_actions`(req 0/opt 0, 应答 `{actions,count}`)、`editor_rescan_project_filesystem`(req 0/opt 0)、`editor_play_scene`(req 0/opt 4)、`editor_open_scene`(req 1 path)、`project_read_scene_file_content`(req 1 path)、`editor_stop_scene`(req 0/opt 0)、`running_game_get_node_property_samples`(req 2 node_path+properties/opt 3，与 my 抽样一致)、`running_game_execute_gdscript`(req 1 code/opt 0)；全部一致。脚本化审计（tests/evidence_battery.rs:1310-1522）另把每次真实调用的 args 逐个过 `inputSchema`，并以 `AUDITED_TOOLS`（:1473-1489，15 条）作为覆盖下限。"
    },
    {
      "id": "DR-53",
      "pass": true,
      "evidence": "①畸形 `enabled=` 不改文件：`PackedArrayEdit::Unrecognised`（src/adapter/godot.rs:2749-2760；缺 `(`、缺 `)`、`close <= open`、关键字不认识、`)` 后有多余内容五种情况全部落此，:2764-2782）→ `AddonCleanup::Unparseable(reason)`（:2805-2815、:2869-2873）→ `initialize` 用 `tracing::warn!` 写 reason。两种畸形写法各有一次受控覆盖：(a) `enabled=true`（无括号）—— lib 测试 `a_malformed_enabled_line_leaves_the_project_untouched`（src/adapter/godot.rs:3574-3598，断言 `!outcome.changed()` + reason 含 `PackedStringArray`/`enabled` + 文件逐字节相同）与 CLI 端到端 `init_leaves_a_malformed_enabled_line_untouched_and_says_why`（tests/cli_init.rs:160-194，跑真 `hoh init` 二进制，断言 exit 0 + 文件 byte-identical + stdout/stderr 含 `PackedStringArray` 与 `left untouched`）；(b) 缺 `)` 的截断形 `enabled=PackedStringArray` 与尾随垃圾 `enabled=PackedStringArray()extra`（src/adapter/godot.rs:3647-3662，逐条断言 `Unrecognised`）。②两条回归测试确在：`an_endpoint_without_a_declared_port_source_is_undeclared`（tests/dual_endpoint.rs:353 起）、`the_gate_closes_when_the_listener_cannot_be_read`（tests/engine_identity.rs:413-474，断言 `matches_binary == None` 关闸、observation 点名 `no TCP listener`、与 mismatch 文本不同、`evaluate_launchable` 判不可启动）。③过期测试名已改且断言**收紧**：`the_snapshot_is_the_real_174_tool_list` → `the_snapshot_is_the_real_177_tool_contract`（src/tools/index.rs:264-269），断言由 `schemas.len() >= 100` 变为 `== 177`（`git diff -U0` 的删除行可见旧名与旧断言）。"
    },
    {
      "id": "GUARDS",
      "pass": true,
      "evidence": "7 条 ignored 仍是既有的真机门控且未被新增/扩大：`grep '#\\[ignore'` 全仓只命中 `tests/godot_smoke.rs` 的 :108/142/233/254/283/350/370（与 `cargo test` 的 `0 passed; 0 failed; 7 ignored` 吻合，e0..e6 七条真机用例）；`git diff --stat 4d3ff58..HEAD -- tests/godot_smoke.rs` **空** ⇒ 该文件一字未动。`src/**` 内无 `#[ignore]`。既有断言未被放宽：`git diff -U0 4d3ff58..HEAD -- tests/ src/tools/index.rs` 的全部删除行只有两处是断言相关 —— `the_snapshot_is_the_real_174_tool_list` 的旧名/旧 `>= 100`（已收紧为 `== 177`），以及 launchable_gate 替身的 `if self.scene_valid()`（替身实现细节，非断言）—— 其余删除行是把旧截图替身 `ScreenshotMode::WritesFile`（它替 hof-rs 自己写文件、替缺陷背书）换成**更严格**的取值域替身，把旧 `str(Input.action_press(...))` 语料换成 body 语义替身。未删除任何测试；本批 diff 只触及 `src/adapter/engine.rs`、`src/adapter/godot.rs`、`src/runtime/engine_identity.rs`、`src/runtime/run_loop.rs`、`src/tools/index.rs`、`src/tools/mcp.rs`、`src/tools/mod.rs` 与 5 个 tests 文件（`git log --name-only 4d3ff58..HEAD` 逐提交可见）。"
    }
  ],
  "defects": [
    {
      "id": "DEF-1",
      "severity": "minor",
      "what": "DR-49 的 `artifact_is_fresh` 里 `(Some(before), Some(after)) => before != after` 这条分支（src/adapter/godot.rs:2202）**没有任何测试能证伪**。",
      "reproduction": "受控植入：把该分支临时改成恒 `true`（`(Some(_before), Some(_after)) => true`），`cargo test --offline --test evidence_battery` 仍然 `test result: ok. 30 passed; 0 failed`（见 §3 E4）。原因：所有截图反例测试都会先作废目标文件，因此 `before == None`，`after` 要么 `None`（失败）要么 `Some`（成功），永远走不到 `(Some, Some)`；即“目标路径上早有一张旧文件、调用后文件仍在但内容不同”这一场景在测试里不存在。功能实现本身正确（我读过 :2195-2204），且 DR-49 ② 的作废机制**有**牙（§3 E3），故不构成放宽也不构成空洞。影响：该行若将来被误改/误删，测试不会报警；同时“`ok` 基于新鲜度而非 `is_file()`”这一条的**字面**判据在反例测试里未得到独立证伪（②的作废把③的前提抹掉了）。建议下一批补：预置旧文件 + 让替身在**不作废**的前提下返回一张与旧文件**字节相同**的图，断言步骤仍判失败/不认领路径。",
      "severity_note": "minor：实现正确、DR-49② 有独立反例、我做了源码复核（§3 E3/E4 两次实验）。"
    },
    {
      "id": "DEF-2",
      "severity": "minor",
      "what": "DR-49 ④ 的判据“旧文件不再压制 capture_frames 回退”同样无法被单独证伪：`a_stale_png_does_not_suppress_the_frames_fallback`（tests/evidence_battery.rs:2005-2037）之所以红→绿，是靠 DR-49 ② 的在先作废，而不是靠 :1130 的 `if !materialized`。",
      "reproduction": "受控植入：把 `if !materialized {` 临时改成 `if !materialized || absolute.is_file() {`（即把旧 `is_file()` 压制语义加回来），`cargo test --offline --test evidence_battery` 仍然 `test result: ok. 30 passed; 0 failed`（见 §3 E5）。因为作废总在调用前发生，`absolute.is_file()` 恒为 false，该子句成了死分支。功能本身正确（我读了 :1087-1097 与 :1130），且该测试确实能抓住“作废整段被删”的回归（§3 E3 就是它一起红的），故不构成空洞。建议与 DEF-1 合并补一条不做作废的实验。"
    },
    {
      "id": "DEF-3",
      "severity": "info",
      "what": "任务书 §2.7 要求的“受控实验：两种畸形写法各跑一次”里的“`enabled=`（无括号）”被实现成两种**不同的**畸形写法（`enabled=true` 与缺 `)` 的 `enabled=PackedStringArray`），而不是同一个字面量 `enabled=`。",
      "reproduction": "`grep 'enabled=' tests/cli_init.rs` 只命中 `:165` 的 `enabled=true`；`enabled=PackedStringArray`（缺 `)`）在 src/adapter/godot.rs:3647-3662 并被断言 `Unrecognised`。我按任务书 §2.7 的字面定义做受控复核（读代码而非改代码）：`packed_string_array_without(\"enabled=\")` 走 src/adapter/godot.rs:2764-2766 `line.find('(')` 为 `None` ⇒ `PackedArrayEdit::Unrecognised` ⇒ 文件不改动，故**判据满足**。仅为措辞与覆盖面的细微出入，非缺陷证据。"
    },
    {
      "id": "DEF-4",
      "severity": "info",
      "what": "`TASK-DR48-REPORT.md` §4.1 第 3 条把“首次 10060 到首次 10061 之间约 730 s”的区间描述成“‘能连、不答’，之后彻底消失”，措辞与时间线略有出入（那 730 s 是三次 10060 重试的窗口，首条 10061 距最后一次 10060 实际只有 7 s）。",
      "reproduction": "我自己解析 `runs/smoke-t6/iter-1/candidate/.hoh/deterministic/mcp-errors.jsonl` 的 timestamp：1790618321 → 1790618683 → 1790619044（10060），随后 1790619051 起全为 10061。1790619051 − 1790618321 = 730 s（该数字本身正确），1790619051 − 1790619044 = 7 s。纯措辞问题，不影响定性。"
    }
  ],
  "risks": [
    "DR-48 的豁免集合是**逐字常量**，与引擎字面量绑定。若引擎改字符串（哪怕只改标点）而 hof-rs 未同步，闸门会退回假阴性——这是有意的保守方向（宁多关不放行），但需要有朝一日的同步机制；本轮已由 §3 E2 证明“单个尾空格就会让豁免失效并让测试变红”，因此不会静默。",
    "DR-49 的“内联图像落地”路径未活体验证：`running_game_capture_screenshot` 不带 `save_path` 时引擎是否真的回 `image_base64`，只能等下一轮真机 T=1；实现者的备选（`user://`）未实施。若真机回的是 `saved_path` 而无内联图，DR-49 的新鲜度逻辑会把该步判失败（保守，不伪造），但 E2/N2 仍会受影响。",
    "DR-51 的 `GET /mcp` 只在“驱动引擎的 adapter”上发起（src/runtime/engine_identity.rs:39-43），真机 9877 的应答形态本轮未复核（离线批）。字段是 `Value`、不做形状断言，故应答形态变化不会打破它，但也意味着 `editor_status` 的形状正确性无守卫。",
    "DR-50 的定性只到“故障在引擎那一侧”；“编译不过的 code ⇒ 游戏进程主线程卡死 / 监听消失”的**内部机制**仍是假设（离线不可证）。最小化复现（editor_play_scene 后第一件事就发 `running_game_execute_gdscript{code:\"this is not gdscript\"}`，预期 -32602）尚未执行——D222 已把这个 spike 列为决策者亲自执行项。",
    "`meta.json.engine.mcp.game_endpoint` 现在来自 `game_history`，它**不会**被 `clear_game_endpoint` 清掉（设计如此，DR-51）。若将来有第三方消费者把该字段当成“当前仍有游戏端点”的活体信号，会读到一个已失效的端点；本轮仓内无此消费者。",
    "实现者报告自述曾两次“临时改回旧语义取红证据”（DR-52/DR-53）——我核对了 `git status --porcelain`（空）与 `git show --stat`（六提交只触及声明过的文件），**没有**在提交里发现残留的临时状态；但这类工作方式本身会引入“红证据来自篡改后的树”的风险，下一批应要求红证据在**干净树上**用 `git stash` / 独立 worktree 取得。"
  ],
  "unverified": [
    "引擎活体：未启动 Godot、未碰 9877（PID 108432 全程未被触碰）、未联网，因此本轮所有修复的**真机**效果（E2 闸门是否真的打开、E3 是否真的可判定）均未验证——这是离线批的定义所限，不是缺陷。",
    "`running_game_capture_screenshot` 不带 `save_path` 的真机应答形态（是否真带 `image_base64`）：只按引擎源码 `running_game_capture.cpp:56-60` 推断，未实测。",
    "`GET 127.0.0.1:9877/mcp` 的真机应答（tools=154 那份）未复核；我只复核了回环替身测试与仓库内记录。",
    "`artifact_is_fresh` 的 `(Some, Some)` 分支（DEF-1）与 `if !materialized` 的单独守护力（DEF-2）：代码已复核，但**未能**用会变红的测试证伪。",
    "任务书 §2.6 要求“至少 3 条编辑器态”抽样中，我做了 9 条编辑器态（见 DR-52 条），但我**没有**连线引擎 `tools/list` 逐字复核取值域/默认值（离线批），只是三方（TEST-CASES.md / 内嵌夹具 / 真实调用）交叉——其中 (a)(b) 两份契约文本同源。",
    "`runs/smoke-t6` 的目录摘要：我算出的 `path+sha256` 串接摘要（135 文件）为 `20aca752edd62862b2d7c78424031424030cea0e9463c73c5c489c382414c082`，与实现者报告里的 `3ce19752eb0273546687dd0bec3716b5640d00b687b6de71e9815ea15cf025b9` **不一致**；我另外试了三种常见串接方式也都对不上，说明双方摘要算法不同。我改用**不依赖算法**的独立判据：文件数 135、最新 mtime `2026-09-29 02:32:01`（早于本批起点 `4d3ff58` 的提交时间）、`runs/` 被 `.gitignore:12` 忽略（`git check-ignore runs/smoke-t6/meta.json` 命中）且 `git ls-files runs/smoke-t6` 为 0、`it-1/candidate/.hoh/evidence/frame-00.png` 仍是 4246 B / sha256 `bef0936daba1b16a23e7b25bd1fc432d946afaaca6d7b0636fbeafc898b67ea2`（与 D221 记录的旧 PNG 逐字节一致）。⇒ 我支持“未被改动”，但**不能**替实现者复现它那个具体摘要值。"
  ]
}
```

**真实命令与退出码（全集，我自己跑的）**

- 命令：`cargo test --offline > .accept-full.log 2>&1`（工作树干净时执行；日志随后删除）。
- 退出码：**0**。34 个 target 汇总：`passed=328 failed=0 ignored=7`（逐条 `test result:` 行的机器汇总；例如 lib `ok. 102 passed`、`evidence_battery` `ok. 30 passed`、`launchable_gate` `ok. 12 passed`、`--test engine_identity` `ok. 18 passed`、`--test dual_endpoint` `ok. 8 passed`、`--test cli_init` `ok. 5 passed`、`godot_smoke` `ok. 0 passed; 0 failed; 7 ignored`）。⇒ 与实现者自述的 `328 / 0 / 7` **属实**，7 条 ignored 是既有真机门控（`tests/godot_smoke.rs`，该文件在 `4d3ff58..HEAD` 无 diff）。
- 我另跑过 9 次靶向 `cargo test --offline --test <target>`（含 5 次植入实验，全部已回退）；每次的退出码与 `test result:` 都在 §3 逐条列出。

---

## 2. 逐项核对表

### 2.0 环境与身份（实测）

| 项 | 我测到的 | 判据 |
|---|---|---|
| `HEAD` | `4fe077d` | `git rev-parse --short HEAD` |
| 六提交 | `9d71a17` `777254d` `d8fc107` `987ef15` `f6fead9` `d8e347e` | `git log --oneline -12` |
| `origin/master` | `4b9bd44`（未 push；`master...origin/master [ahead 21]`） | `git rev-parse --short origin/master` / `git status -sb` |
| 工作树 | `git status --porcelain` 空、`git diff --stat` 空、`git diff --cached --stat` 空 | 三个命令 |
| `core.autocrlf` | `true` | `git config core.autocrlf` |

### 2.1 DR-48（可启动闸门假阴性）

| 判据（任务书 §2.3） | 结果 | 证据 |
|---|---|---|
| ①常量数据 + 具名匹配函数，非特例 `if`、非 `[MCP]` 前缀 | ✅ | `ENGINE_INFO_BANNERS` src/adapter/godot.rs:3243-3246；`is_engine_info_banner` :3258-3261（`line.trim()` 后 `contains`，无前缀规则）；`non_banner_editor_errors` :3267-3277；唯一消费点 :793 |
| 豁免形态逐字等于引擎字面量 | ✅ | `godot-mcp/godot/modules/mcp_server/mcp_server.cpp:605`（trace=off）、`:645`（capture=off）——与常量表两行**逐字**一致 |
| ②非空洞：反例测试真的会红 | ✅ | §3 E1（恒真 → 3 条反例测试 FAILED）、§3 E2（常量加一个尾空格 → 正例测试 FAILED） |
| ③引擎真错误行不被豁免 | ✅ | `ERROR: [MCP] SceneTree never became available; MCP server disabled.` 在 `mcp_server.cpp:223`；不在常量表内；`an_error_carrying_the_mcp_prefix_still_closes_the_gate`（tests/launchable_gate.rs:686-714）在 E1 里同步变红 |
| 未命中即按原语义判“不干净” | ✅ | src/adapter/godot.rs:803-808（`(false, "…UNAVAILABLE: the editor is not clean")`），对应删除行可见旧语义之一字未改 |
| 根因（引擎用大小写无关 `contains("ERROR")` 过滤日志） | ✅ | `godot-mcp/godot/modules/mcp_server/tools/editor_read_scene_inspector.cpp:249` `if (source.lines[i].to_upper().contains("ERROR")) {` |

### 2.2 DR-49（截图证据必须“本轮真实”）

| 判据 | 结果 | 证据 |
|---|---|---|
| ①不再传文件系统路径 | ✅ | src/adapter/godot.rs:1101 `json!({})`；测试 tests/evidence_battery.rs:1952-1956 断言 `calls[0] == json!({})`；替身强制取值域 :448-456；引擎 `running_game_capture.cpp:62,81` |
| ②调用前作废既有文件 | ✅ | src/adapter/godot.rs:1087-1097 + `invalidate_artifact` :2214-2240；反例测试 tests/evidence_battery.rs:1995-1998；**有牙**（§3 E3：空操作植入 → 该测试 FAILED） |
| ③`ok` 基于新鲜度而非 `is_file()` | ⚠️ 实现✅ / 证伪覆盖不足 | src/adapter/godot.rs:1160-1188、`artifact_is_fresh` :2195-2204；`(Some, Some)` 分支无测试可达（DEF-1、§3 E4） |
| ④旧文件不再压制 `capture_frames` 回退 | ⚠️ 实现✅ / 单独证伪不足 | src/adapter/godot.rs:1130 `if !materialized`；测试 tests/evidence_battery.rs:2016-2020；加回 `|| is_file()` 不会变红（DEF-2、§3 E5） |
| 反例：预置旧文件断言步骤不判成功 | ✅ | tests/evidence_battery.rs:1969-1999（`!record.ok`、`path.is_none()`、observation 含 `UNAVAILABLE`、旧文件已被作废） |
| 内联图像落地 | ✅（离线替身层面） | `extract_inline_image` + `write_png`，`screenshot_materializes_an_inline_base64_png`（:1893-1913）断言解码字节**逐字节相等** |

### 2.3 DR-50（先定性后修复）

| 判据（任务书 §2.8） | 我的独立结果 | 证据 |
|---|---|---|
| ①第 5 次调用是第一条编译不过的 code | ✅ 支持 | raw/input_channel_probe.json 的 8 条 execute_gdscript：4 ok → 第 5 条 `str(Input.action_press(\"move_right\"))` not_ok；前 4 条只是无 `return`（可编译） |
| ②失败在传输层（10060，状态行缺失） | ✅ 支持 | mcp-errors.jsonl：10060 ×3，ts 1790618321/683/9044（间隔 362/361 s）；报文“有正确答复的主机没有反应…(os error 10060)” |
| ③随后监听消失（10061） | ✅ 支持 | 同文件 10061 ×33（首条 ts 1790619051，晚于首条 10060 **730 s**）；36 条传输错误**全部**指向 `127.0.0.1:63698` |
| ④编辑器端点同轮全程健康 | ✅ 支持 | raw 记录 req=26..43 的 editor 调用**全部** ok=true（含 editor_stop_scene 43，带真实 `game_endpoint_invalidated`） |
| ⑤两轮端口/pid 如报告所列 | ✅ 支持（措辞略有出入） | 63698/101872 贯穿 19 个工件（pass2）；65333/109964 出现于 traj/developer.attempt2.json（那是 pass1/早前 editor_play_scene 的值，报告“attempt2.json mentions”字面成立，见 DEF-4 相邻说明） |
| ⑥`godot-mcp/**` 一个字节未改 | ✅ | `git diff --stat 4d3ff58..HEAD -- godot-mcp` 空 且 `git log --oneline 4d3ff58..HEAD -- godot-mcp` 空 |
| 引擎对“编译不过的 code”的书面答案是 -32602 而非挂死 | ✅ | `running_game_script_execution.cpp:83` “`code` that does not compile is `-32602`”；void 当值为编译错误 `gdscript_analyzer.cpp:3498/3549/3732` |
| 定性未完成前不得“修”引擎 | ✅ | `godot-mcp/**` 零改动即证 |

### 2.4 DR-51（端点身份真正持久化）

| 判据 | 结果 | 证据 |
|---|---|---|
| `editor_status` 用真实 `GET /mcp` 响应体填充 | ✅ | src/tools/mcp.rs:49-59、src/runtime/engine_identity.rs:34-50/71-73；`the_editor_status_is_the_verbatim_get_mcp_body`（tests/engine_identity.rs:581-595） |
| 失败 → `null` + reason | ✅ | `an_unreachable_endpoint_yields_no_status_and_no_failure`（:600-623） |
| 不驱动引擎就不发请求 | ✅ | `the_status_fetch_is_gated_on_the_adapter_driving_an_engine`（:629-647，false 分支 `|_| panic!`） |
| `game_endpoint` 在登记当刻回写、stop 后不空 | ✅ | src/tools/mod.rs:256-262、:264-268；`the_run_meta_keeps_the_game_endpoint_the_battery_registered`（tests/launchable_gate.rs:531-572） |
| `{}`→`null` 未破坏消费者 | ✅ | `EngineIdentity::unavailable` src/adapter/engine.rs；全集 328 测试全绿；仓内无消费者依赖 `{}` |

### 2.5 DR-52（诊断自洽 + 参数形状）

| 判据 | 结果 | 证据 |
|---|---|---|
| 诊断文本与自己的原始记录一致，InputMap 矛盾已消 | ✅ | `the_editor_input_map_diagnostic_agrees_with_its_own_record`（tests/evidence_battery.rs:1248-1303）双向断言 |
| 抽样 ≥12 条（含每个游戏态工具 + ≥3 条编辑器态） | ✅ 15 条（6 游戏态 + 9 编辑器态） | §1 的 DR-52 条；**177/177 必填集合零不匹配**（我自己的三方交叉脚本） |
| 在 `TEST-CASES.md` 里自己找依据 | ✅ | 逐条对照 `TC-TOOL-*` 行的 `合法=…（req N / opt M）; 必填=…; 可选=…; 默认=…` |

### 2.6 DR-53（批次一遗留 minor）

| 判据 | 结果 | 证据 |
|---|---|---|
| 畸形 `enabled=` 不改文件（写 reason） | ✅ | src/adapter/godot.rs:2749-2760/:2764-2782/:2805-2815/:2869-2873；`a_malformed_enabled_line_leaves_the_project_untouched`（:3574-3598）；`init_leaves_a_malformed_enabled_line_untouched_and_says_why`（tests/cli_init.rs:160-194，真二进制端到端） |
| 两条回归测试（`undeclared` 分支、`None` 关闸） | ✅ | tests/dual_endpoint.rs:353；tests/engine_identity.rs:413-474 |
| 174 → 177 改名 + 收紧断言 | ✅ | src/tools/index.rs:264-269（`== 177`），旧 `>= 100` 见 `git diff -U0` 删除行 |

### 2.7 禁令自查（全部实测）

| 禁令 | 结果 | 证据（我的命令/输出） |
|---|---|---|
| `godot-mcp/**` 未改 | ✅ | `git diff --stat 4d3ff58..HEAD -- godot-mcp` 空；`git log --oneline 4d3ff58..HEAD -- godot-mcp` 空 |
| `runs/smoke-t6/**` 逐字节未变 | ✅（算法无关判据） | 135 文件、最新 mtime `2026-09-29 02:32:01`、frame-00.png 4246 B/sha256 `bef0936d…7ea2`（与 D221 记录一致）、`runs/` 被忽略且未跟踪（见 §1 unverified 第 6 条说明摘要算法差异） |
| `PRD-mario.md` sha256 | ✅ | `4c81c3a9995f0b3afdf01421a0c3be88573cceefc284ce9bafbfda141f0f5c3a`（逐字一致） |
| 无新依赖 | ✅ | `git diff --stat 4d3ff58..HEAD -- Cargo.toml Cargo.lock` 空 |
| 未 push | ✅ | `origin/master = 4b9bd44`；`master...origin/master [ahead 21]` |
| 未 stage `runs/**` / `.workspace/**` / `config/*.secret*` | ✅ | `git diff --cached --stat` 空；`git diff --name-only 4d3ff58..HEAD -- runs .workspace config` 空；这三个路径均在 `.gitignore` 内 |
| 未启动 Godot / 未碰端口 / 未联网 / 未调模型 | ✅ | 全程只有 `cargo test --offline`、`git`、只读文件命令与 python 只读脚本；无 `hoh run`、无网络调用、无端口探测 |
| 未打印密钥 | ✅ | 全程未读 `config/*.secret*` |

---

## 3. 反例清单（我构造了什么、观测到什么、是否推翻）

> 所有植入都只改 `src/adapter/godot.rs`，改后一律 `git checkout -- src/adapter/godot.rs` 回退，并用
> `git status --porcelain`（空）+ `git diff --stat`（空）+ `git hash-object` == `git rev-parse HEAD:src/adapter/godot.rs`
> （`606c1f4d…8f58`，`core.autocrlf=true` 下仍逐字节一致）三重证明已恢复。

| # | 实验（植入） | 命令 | 真实观测 | 结论 |
|---|---|---|---|---|
| **E1** | `is_engine_info_banner` 恒 `true`（DR-48 反向） | `cargo test --offline --test launchable_gate` | `test result: FAILED. 9 passed; 3 failed; 0 ignored`；失败者 `a_real_editor_error_still_closes_the_gate` / `an_error_carrying_the_mcp_prefix_still_closes_the_gate` / `an_unknown_mcp_prefixed_line_still_closes_the_gate`，panicked at `tests\common\mod.rs:270:13` “FakeHarness step #2 expects Developer but the runtime asked for Tester” | **未推翻**。三条反例测试**真的会红**，且红的方式正确（注入真 ERROR 时闸门不再关 ⇒ 假阴性被测试抓住）。若这里“注入真 `ERROR:` 后闸门不再失败”而无测试变红，才是 fail；实测有测试变红 ⇒ 非空洞。 |
| **E2** | `ENGINE_INFO_BANNERS[1]` 末尾加**一个空格**（豁免变成非逐字） | `cargo test --offline --test launchable_gate` | `test result: FAILED. 11 passed; 1 failed`；失败者 `an_engine_info_banner_does_not_close_the_gate` | **未推翻**。正例测试也**真的会红**，说明豁免确实由常量逐字驱动（连 `trim()` 都能吃掉的那一个空格也会被测试发现）。 |
| **E3** | `invalidate_artifact` 恒 `Ok(None)`（DR-49② 空操作） | `cargo test --offline --test evidence_battery` | `test result: FAILED. 29 passed; 1 failed`；失败者 `a_stale_png_is_never_mistaken_for_this_runs_screenshot` panicked at `tests\evidence_battery.rs:1995`（“the stale file must have been invalidated before the call (DR-49)”）；同一植入下 `a_stale_png_does_not_suppress_the_frames_fallback` **也**在失败集里被牵连 | **未推翻**。DR-49 ② 的反例机制有牙，且“旧文件压制回退”的回归会被同一条实验抓到（只是归因到作废而非 :1130 那一行，见 DEF-2）。 |
| **E4** | `artifact_is_fresh` 的 `(Some, Some)` 分支恒 `true`（DR-49③ 反向） | `cargo test --offline --test evidence_battery` | `test result: ok. 30 passed; 0 failed`（无任何测试变红） | **反例部分成立** ⇒ **DEF-1**。该分支无测试可达；DR-49③ 的字面判据未被证伪。实现本身正确（源码复核），故为 minor 而非空洞：受控实验证明的是“无测试能到达该分支”，不是“守卫恒真”。 |
| **E5** | `if !materialized` → `if !materialized \|\| absolute.is_file()`（把旧 `is_file()` 压制语义加回） | `cargo test --offline --test evidence_battery` | `test result: ok. 30 passed; 0 failed`（无任何测试变红） | **反例部分成立** ⇒ **DEF-2**。因为作废总在调用前发生，该子句恒 false，成为死分支；DR-49④ 不能被单独证伪（把它删掉不会红，把它加回来也不会红）。 |
| **E6** | 交付树的复现（无植入） | `cargo test --offline` | `EXITCODE=0`；34 target 汇总 `passed=328 failed=0 ignored=7`；`godot_smoke` `0 passed; 0 failed; 7 ignored` | **未推翻**。实现者自述的测试结论属实。 |
| **E7** | 干净树 + 我的全部植入回退后 | `git status --porcelain` / `git diff --stat` / `git hash-object` | 双空；`606c1f4d3b3a46a8137c519d7dac657162488f58` == `git rev-parse HEAD:src/adapter/godot.rs` | **未推翻**。仓库回到 HEAD 的逐字节状态。 |

**原始工件层面的反例也做了**：我从 `runs/smoke-t6/**` 独立重算 DR-50 的六条判据（§2.3），并检查了 `TEST-CASES.md`
177 条与内嵌夹具 177 条的 `required` 集合（**0 处不匹配**）与 15 个真实调用点——没有找到与报告相悖的证据。

---

## 4. 对 DR-50 定性的独立结论与置信度

**我的独立结论：支持“引擎侧可用性缺陷”。**

- **判据链（全部由我自己从原始文件复算，非转述）**：
  1. 第 5 次 `running_game_execute_gdscript` 是**第一条编译不过**的 code（raw/input_channel_probe.json 顺序：ok,ok,ok,ok,not_ok,…；前四条只是无 `return`，能编译）。
  2. 失败在**传输层**：`os error 10060`，“有正确答复的主机没有反应，连接尝试失败” ×3（ts 1790618321/683/9044，间隔 362/361 s）。
  3. 随后**监听消失**：`os error 10061`（连接被拒）×33，首条 ts 1790619051，距首条 10060 **730 s**；36 条传输错误**全部**指向 `127.0.0.1:63698`，与 `editor_stop_scene` 记录的 `game_endpoint_invalidated.port=63698/pid=101872` **同一个端点**。
  4. **编辑器端点同轮全程健康**：raw 记录里 editor 侧 req=26..43 全部 `ok=true`；故障局限在游戏进程。
  5. **两轮可复现**：pass2 `63698/101872` 贯穿 19 个工件；pass1 的 `65333/109964` 也在同一 traj 文件中留下记录。
  6. 引擎对“编译不过的 code”的**书面答案**是 `-32602`（`running_game_script_execution.cpp:83`），且 void-当值确为编译错误（`gdscript_analyzer.cpp:3498`）——**绝不是一个不答的挂死**。
- **置信度**：
  - “故障发生在引擎那一侧（游戏进程的 MCP 服务）” —— **高**（传输层证据 + 编辑器端点对照 + 两轮复现 + hof-rs 请求合规）。
  - “内部机制 = 编译错误捕获路径把游戏主线程/监听卡住” —— **未定**（离线不可证；D222 也把机制标为推断）。
  - “**不是** hof-rs 调用形态造成的挂死” —— **高**，但我保留一条诚实的保留意见：唯一与挂死同时出现的差别恰是“第一条编译不过的 code”，因此“某种调用形态触发了引擎 bug”这一**因果方向**在离线证据下无法排除；能排除的是“hof-rs 的 JSON-RPC 不合规/没被应答过”（前 4 次同形态请求都被正常应答）。
- **是否推翻**：**没有**推翻 D222 的定性；四个 minor/info 级措辞或覆盖面问题见 §1 `defects`。

---

## 5. 未验证项与理由

见 §1 `unverified` 六条。核心两类：

1. **一切活体项**（真机 E2/E3、内联 `image_base64` 应答、真机 `GET /mcp` 形态）——本批是**离线**验收，任务书硬禁令；且 9877 上有必须保护的编辑器（PID 108432），我从头到尾没有碰它。
2. **两条无测试可达的判定分支**（DEF-1/DEF-2）——我做了源码复核但没有能变红的实验，因此按“证据支持 / 推断”区分：实现**读过**（证据），其守护力**无测试**（推断/缺口）。

---

## 6. 我没有独立复核的部分

- 引擎 `tools/list` 的**活体**取值域与默认值（离线）。我只做了三方文本交叉（`TEST-CASES.md` / 内嵌夹具 / 真实调用），其中前两者同源，故“契约文本本身是否有错”不在我的结论范围内。
- 除 `godot.rs` 之外的调用点是否有参数形状问题：我的脚本只覆盖 `src/adapter/godot.rs`（hof-rs 的工具调用几乎全在这），另有 `src/tools/mcp.rs:232/289` 的 `PROBE_TOOL` 同步探针（`project_get_info`，req 0/opt 0，与契约一致，已读）。`src/tools/reliable.rs`、`src/tools/bridge.rs` 等未逐行核对调用形状。
- 实现者报告 §3 表格里“修复前”的参数形状：我只从 `git diff -U0` 的删除行确认了 `{"save_path": <文件系统绝对路径>}` 与 `str(Input.action_press(...))` 两处，未重建修复前的完整树。
- `runs/smoke-t6` 里那些 **`.hoh/scratch/*.py`** 脚本（`full.py`/`gen.py`/`rep.py` 等）的内容我没有审阅（它们是上一轮执行者留下的，属 `runs/**` 只读区，且与 DR-48..DR-53 的判据无关）。
- `DECISIONS.md` D221/D222 的**结论**我读了，但没复核其引用的历史轮次（`smoke-t5`、D218/D219/D220 的原始工件）——超出本批范围。

---

## 7. 给下一批的建议（**不要**自己改代码）

1. **补 DR-49 的两条“有牙”测试**（DEF-1/DEF-2）：在**不作废**的前提下预置旧文件并让替身回一张**字节相同**的图，断言步骤仍判失败且不认领路径；以及在不作废的前提下让替身只回 `frames`，断言回退仍被触发。这样 `artifact_is_fresh` 的 `(Some, Some)` 分支与 `if !materialized` 才各自有独立守护力。
2. **统一 `runs/smoke-t6` 的目录摘要算法并把它写进工件**（我复现不出 `3ce19752…`）：建议改用 `git hash-object` 逐文件 + 排序清单，或直接记录“文件数 + 最新 mtime + 每个关键文件的 sha256”，避免下一批再出现“摘要对不上但内容没变”的解释成本。
3. **DR-50 的最小化复现 spike 值得优先执行**（D222 已列为决策者亲自执行项）：`editor_play_scene` 后**第一件事**发 `running_game_execute_gdscript{code:"this is not gdscript"}`。预期 `-32602`；若挂死 ⇒ 引擎缺陷被孤立确认，且能一次性把“编译错误路径”与“长时/坐标探测路径”分开。**这需要真机与端口，必须由用户/决策者在获批窗口内做，不是离线批能做的。**
4. **红证据纪律**：下一批任务书里请要求“红证据必须在**干净树**上取得（`git stash` 或独立 worktree），不得靠临时篡改生产代码取红”——本批实现者自述做了两次，虽未在提交里留残渣，但这类工作方式无法被 `git status` 之外的证据审计。
5. **DR-48 的豁免同步**：建议在任务书里加一条“豁免常量必须与 `mcp_server.cpp` 的字面量在同一个提交里更新，且必须附一条‘引擎改一个字符则测试变红’的说明”——本轮 E2 已证明单字符漂移会被测试发现，把这个性质写成显式要求可避免未来有人用 `contains`/前缀来“顺手放宽”。
6. **DR-51 的消费者审计**：`game_endpoint` 现在是一个“历史事实”字段而非“活体信号”。若设计文档要把它当活体用，请在任务书里明确区分 `game_endpoint`（历史）与 `game_endpoint_live`（活体），不要靠读者从实现推。

---

*报告落点：`.spec/hof-rs/tasks/TASK-DR48-ACCEPTANCE.md`。验收者全程只读；除 §3 授权的五组植入-回退实验外未改动仓库任何受控文件，实验后 `git status --porcelain`、`git diff --stat`、`git diff --cached --stat` 三空，`src/adapter/godot.rs` 的 `git hash-object` 与 `HEAD` blob 一致。*
