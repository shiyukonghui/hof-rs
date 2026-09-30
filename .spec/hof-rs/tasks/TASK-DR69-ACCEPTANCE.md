# TASK-DR69-ACCEPTANCE — DR-69 的独立验收（端点跨进程发布 / 矛盾 / 输出上限 / E3 证据形态 / 携带项）

- 判据来源：`.spec/hof-rs/tasks/TASK-DR69.md`（唯一任务书）+ 调度者本轮追加的验收条目（八项，含"自己植入反例"）。
- 被验收对象：`.spec/hof-rs/tasks/TASK-DR69-REPORT.md`（**只是线索**）+ 提交 `96b7c29..03b35dd` 的 7 个 DR-69 提交。
- 性质：**独立验收、离线、只读为主 + 受控植入**。我无上游对话上下文；报告的任何结论都不作证据，下列每条都是我自己复算/复现的。
- **硬约束遵守**：未启动 Godot；未联网；未调模型端点；未跑真机轮；**未向 `runs/**` 写入任何字节（连临时文件都没有）**；未修改 `.workspace/mario/**`、`.spec/hof-rs/PRD-mario.md`、`DECISIONS.md`、`godot-mcp/**`；未 push、未 stage；未重写任何本地提交；未委派他人（独自完成）。
  仓外工作目录：`C:\Users\wyl\AppData\Local\Temp\dr69acc\`（`digest.ps1`、`ws_check.py`、`plants.py`、`stale_route.py`、`redaction_diff.py`、`secret_scan.py`、`testnames.py`、`summarize.py`、`suite-final.txt`、`suite-PB2.txt`、`bak/P*.bak`）。**植入全部在 `src/**` 生产代码**，每一次都用仓外逐字节备份还原。
- **仓库状态在我验收期间发生变化（并发活动，非被验收对象所为）**：我开工时 `HEAD=03b35dd`（7 个 DR-69 提交）；验收中新增 **`6ebb75d`（2026-09-30 13:14:51，`docs(spec): D272`）**，由**调度者**把 `TASK-DR69-REPORT.md` 与 D272 入库 ⇒ 我的门/守卫是在 `03b35dd` 上测的，文件/摘要判定在 `6ebb75d` 上复核过（`03b35dd..6ebb75d` 只加报告与 `DECISIONS.md`，不动任何被验收的 `src/tests` 字节）。`origin/master` 全程 `9aebbe15…`（未 push），ahead 7 → 8。
- 摘要口径见 §7.1（PowerShell 5.1 / zh-CN / 文化排序 / 仓根相对小写 POSIX 路径 + 字节数 + SHA256）。

---

## 0. 结构化结论（机器可读）

```json
{
  "verdict": "fail",
  "verdict_scope": "fail 由**一条 major** 与**三条 minor/一条 moderate** 支撑，且**不否定**本批的大部分工程量：(a) 工具结果上限、矛盾在 developer.md 一侧的消除、可执行失败定稿、卫生扫描扩到目录、E3 证据形态（前后帧 + 位置断言）、门与守卫，我都独立复现为真且为绿；(b) major 只有一条——**跨进程路由在真实轮次里从来没有与任何角色进程共存过**：路由只由 harness 的电池在 `step_play_scene` 发布、又在同一 pass 的最后一步 `step_stop_scene` 撤下（`godot.rs:613-631`、`:2534`），而角色（Planner/Developer/Tester）全部在电池之前或之后运行（`run_loop.rs:673/884/1111/1263/1373`）⇒ 任务书①的字面判据只在**测试自己手写的 route 文件**上成立，角色在真机上的 `hoh tools call running_game_*` 仍会（在正常流程里）拿到 `game_endpoint_unavailable`。这正是验收条目要求我判定的『sound for the real system 还是 merely satisfies a test』。(c) 其余缺陷是证据保全的原样性、覆盖缺口与残留矛盾，均不影响已通过的那几项。",
  "criteria": [
    {"id": "C1-route-mechanism", "pass": true, "evidence": "① 机制与报告所述一致且可被执行证伪：我的植入 P-A 删掉 `src/cli_impl.rs` 的唯一一行 `bridge::adopt_published_game_route(&channel, None);` ⇒ `game_route_across_processes::a_role_shell_reaches_the_published_game_endpoint_across_processes` **RED**（panicked at `tests/game_route_across_processes.rs:219`，`left: Some(5) right: Some(0)`，stderr 逐字为 `hoh: game_endpoint_unavailable: … Falling back to the editor endpoint is not allowed (DR-43).`）——**与被验收报告 §2.1『改前左侧 Some(5)』逐字一致**，即该测试确实由生产的采纳调用承重。② 测试用**真实二进制、真实新进程**（`Command::new(env!(\"CARGO_BIN_EXE_hoh\"))`），不是我写的替身调用；游戏/编辑器两条都是回环替身。③ 反向守卫 `without_a_published_route_the_game_call_still_fails_loudly` 与 DR-43 未放宽一致（我植入 P-A 时它仍绿，因为无 route 时本来就 bail）。④ 撤下机制也承重：植入 P-C 删掉 `clear_game_endpoint` 里的 `withdraw_game_route` ⇒ `registering_publishes_the_route_and_stopping_withdraws_it` **RED**（`tests/game_route_across_processes.rs:316`『a stopped game must not stay resolvable across processes』）。"},
    {"id": "C1-route-realflow", "pass": false, "evidence": "**角色 CLU 在正常流程里仍然够不到游戏端点。** 发布点是 `src/adapter/godot.rs:903` 的 `register_game_endpoint`（`grep -rn register_game_endpoint src/` 只此一处），它只在电池的 `step_play_scene()`（`godot.rs:623`）里发生；撤下点是同一 pass 的最后一步 `step_stop_scene()`（`:629`，`clear_game_endpoint` 无条件调用，`:2528-2534`）。`BatterySession::run` 的步序是 `project_reload_open → scene_structure → editor_errors → play_scene → scene_tree → screenshot → input_channel_probe → input_replay → node_assertions → stop_scene`（`:613-631`），而 `run_loop.rs` 的阶段序是 Planner(`:673`) → Developer(`:884`) → **电池(`:1111`)** → 冻结(`:1263`) → Tester(`:1373`)。⇒ 正常路径下**没有任何角色进程在 route 文件存在期间运行**（角色进程是串行的独立 `hoh` 进程）。另：`McpChannel::call`（`src/tools/mod.rs:329-358`）在 `editor_play_scene` 之后**不做**注册，所以角色自己也**无法**引导出 route（这与 `godot-dev.md` 让角色调 `editor_play_scene` 的配方直接冲突，见 D5）。唯一例外是**电池中途出错**（`input_replay` 等返回 Err ⇒ `step_stop_scene` 被 `?` 跳过 ⇒ 文件留下、游戏仍在跑），此时后续角色才会碰巧看到一个可用的 route——这是错误路径的副产品，不是设计。报告 §6『推断 1（≈0.85）真机上的 running_game_* 会经由发布的路由成功』**没有披露『发布窗口与角色执行窗口在当前流程里不相交』这一事实**。"},
    {"id": "C1-route-scope-cleanup", "pass": false, "evidence": "**范围正确、清理不完整、且陈旧 route 会被采纳。** 范围：文件落在 `<run dir>/game_endpoint.json`（`endpoint::game_route_path`），不在工件树/角色视图/`runs` 之外，只有运行时写它——这一半成立。清理：`editor_stop_scene` 撤下（我以 P-C 证明该分支承重），但**（a）一轮结束时不清理**（`grep withdraw_game_route src/` 只有 `clear_game_endpoint` 一处调用），**（b）`use_game_route_file` 在启动/采纳时无条件 `install_game_route`，不校验 `pid`、不校验新鲜度**。我亲手反例（仓外 `stale_route.py`，未碰外部端口，只用一个我自己 bind 后立刻 close 的回环端口 58325）：把一个陈旧 route 文件经 `HOH_GAME_ROUTE` 交给真实 `hoh.exe tools call running_game_get_scene_tree --role developer` ⇒ **exit 5**、输出为 `MCP transport failure to http://127.0.0.1:58325/mcp: … Connection Failed: Connect error: … (os error 10061)`，**输出中不含 `game_endpoint_unavailable`**（`game_endpoint_unavailable in output: False`）⇒ 『陈旧 route 会把一次调用从 DR-43 的明确拒绝变成一次传输失败，而不是拒绝』为**实测**。`run_loop.rs:537` 用的是**同一个** `use_game_route_file`，所以复用 `--run-id`（默认 run id 带 uuid4 前 8 位，故需显式指定）或上一轮崩溃留下的文件，会让 harness 自身也路由到死端点。"},
    {"id": "C2-contradiction-developer-md", "pass": true, "evidence": "**两半都做了。** 删：`[definition-of-done]` 第 4 条不再要求用 `running_game_get_node_property_samples` 自证，改成结构性要求（命名节点 + 会变的属性 + 让移动代码为真）；`src/prompts/developer.md` 全文 `grep running_game` 只剩 `:31-36` 一段（解释通道存在、可能不可用、禁止绕道）。补：`[policy]` 新增『**Change the project code first.**』+『**Observing the running game in this round is NOT your prerequisite.**』+ 明确禁止 `build an MCP client of your own` / `hand-roll JSON-RPC` / `probe ports`；`[separation of duties]` 新增『**Your order of work.**』；`[self-test]` 把可自证通道**限定为编辑器侧**（`editor_get_errors`/`editor_play_scene`/`editor_simulate_input_action`/`editor_get_collision_info`）。测试：`developer_contract.rs` 新增正向 4 needle + 反向 8 个禁用串（`the_developer_changes_the_code_first_and_leaves_observation_to_the_tester`）；`e1_increment.rs` 的旧断言按需求变更为 `!prompt.contains(\"running_game_get_node_property_samples\")`（报告已逐条披露，我核为**极性反转而非放宽**：一侧删除、另一侧新增正向断言）。新占位符 `{{HOH_GAME_ROUTE}}` 走既有渲染管线且被 `role_shell_contract::no_delivered_document_carries_an_unrendered_shell_placeholder` 覆盖。"},
    {"id": "C2-contradiction-delivered-skills", "pass": false, "evidence": "**同一矛盾在『交付给 Developer 的技能』里仍然完整存在**（见 D5）：`src/prompts/skills/godot-dev.md:65-78` 的 §5 标题就是『Self-test the behaviour before you finish』，正文用 `{{HOH_HOH_BIN}} tools call editor_simulate_input_action …` + `{{HOH_HOH_BIN}} tools call running_game_get_node_property_samples …` 并要求 `samples[*].position.x must change while the key is held`；§6（`:80-92`）又要求 `editor_play_scene` 后调 `running_game_get_scene_tree`。技能在运行时被注入 `.hoh/skills/**` 并交付给角色（`src/prompts/mod.rs:33-36`、`tests/prompt_shell_contract.rs`/`role_shell_contract.rs` 按『delivered』口径测）。而 `tests/developer_contract.rs:121` 仍然**要求** `godot-dev.md` 含 `running_game_get_node_property_samples`（本批未改该测试）。⇒ 『移除指令』只发生在 `developer.md`，交付材料里的正向指令仍在，且因 `editor_play_scene` 不发布 route，它照样是一条够不到的路径。"},
    {"id": "C3-cap-truncate-annotate", "pass": true, "evidence": "上限 = 64 KiB（`DEFAULT_MAX_TOOL_OUTPUT_BYTES`），超限保留**头部**、按 UTF-8 边界切、追加含 `TRUNCATION_MARKER` + `<shown> of <total> bytes … the remaining N bytes were dropped` 的显式标注，并把 `hoh_output_truncated/original_bytes/limit_bytes` 写进 `Output::extra`（`src/harness/cap.rs:71-139`）。我植入 P-B（把 `if original_bytes <= limit` 短路成 `if true`）⇒ `tests/tool_output_ceiling.rs` **3 条 RED**，真实输出含 `the observation a request would carry must be bounded, got 15570803`（真机事故的字节数）与 `a real 2 MiB result must be capped, got 2097152`。还原后 4/4 绿。"},
    {"id": "C3-no-replay-into-later-request", "pass": true, "evidence": "**上限落在唯一的那条边界上。** mini 的 observation 由 `Output.output` 渲染（`mini-swe-agent/rust/src/models/mod.rs:229-283`：`raw_output` = `output.output.clone()`，模板也由序列化后的 `Output` 渲染，`extra` 被并入 message extra），而 `CappedEnvironment` 正是包在 `DefaultAgent::execute_actions` 调用的 `env.execute`（`agent.rs:187-198`）之外 ⇒ 被截断的字符串就是进入下一次请求的有效载荷。`cap_tool_output` 的输出里**不存在**超限的连续字节串（测试断言 `!text.contains(&\"x\".repeat(limit+1))`）。⇒ 『不可回放』成立，且由 P-B 的 15,570,803 字节反例证明该保护真的是上限函数在起作用。"},
    {"id": "C3-wiring-coverage", "pass": false, "evidence": "**生产侧接线无任何测试覆盖（见 D4）。** 我植入 P-B2：删掉 `src/harness/mini.rs:66-69` 的 `CappedEnvironment::new(Box::new(environment), …)` 包装 ⇒ `cargo test --offline --test tool_output_ceiling` **4/4 全绿**；随后全量 `cargo test --offline --no-fail-fast` 在该植入下跑到 36/46 个 target、**0 failed**（被执行器 600s 上限截断），我又补跑缺失的 8 个 target（含 `tool_output_ceiling`）⇒ 全绿、`CARGO_EXIT=0`。`grep -rn MiniHarness tests/` 只命中 `godot_smoke.rs`（7 条全 `#[ignore]`，需真机）与 `model_identity_config.rs`（只验 wire 名，未到环境层）。⇒ 报告 §3.2『真 `LocalEnvironment` 测试证明改的是 harness 真正用的那个环境边界』**不准确**：那条测试自己 `CappedEnvironment::new`，从未经过 `MiniHarness::invoke`。"},
    {"id": "C4-evidence-form", "pass": true, "evidence": "`input_replay` 每个窗口现在产出 before/after 帧与位置断言，且**不依赖 `input_axis`**：`capture_replay_frame`（`godot.rs:1491-1567`，沿用 DR-49：不带 `save_path`、先 `invalidate_artifact`、内联 base64 落 `.hoh/evidence/replay-<label>-<phase>.png`、`running_game_capture_frames` 兜底）与 `assert_replay_moved`（`:1583-1618`，`running_game_assert_node_state`，`node_path=Player`/`property=position`/`operator=neq`/`expected=`窗口首样本）；三种诚实失败 `REPLAY_FRAME_MISSING`/`POSITION_UNCHANGED`/`POSITION_ASSERTION_UNAVAILABLE`。我植入 P-D 让 `assert_replay_moved` 直接 `return None` ⇒ `evidence_battery::the_input_replay_produces_before_and_after_frames_and_a_positional_assertion` **RED**（`tests/evidence_battery.rs:3344`），打印出的 label 序列真实显示每窗口顺序为 `…:replay_frame_before → create/play/run_test_scenario/stop_input_recording → EDITOR_SIDE_INJECTION → …:replay_frame_after → …:game_axis → release`，P-D 后 `replay_assert_moved` 消失 ⇒ 该标签确实由生产调用产生。"},
    {"id": "C4-sampling-lag", "pass": true, "evidence": "**没有任何『按总位移』的承重断言**（这正是验收条目设的条件）。唯一承重的位置判据是 `movement_on_intended_axis`（`godot.rs:2992-3002`：`axis=位移轴`、`moved = delta != 0.0`，**只判是否为零、不判幅度**）与 `assert_replay_moved`（`operator=neq`，期望值 = 该窗口 `before_position` = **首样本**，即与观测同窗口）。⇒ 上一轮验收测得的 ~14 帧系统性滞后**不会**改变任一 pass/fail；报告 §6『校准记录』与我一致。残余（非缺陷，已记风险）：观测文本里的 `delta=` 仍是**窗口内**位移，会系统性低估总位移约 14 帧；下一批若要用总量必须先标定。"},
    {"id": "C5-executable-finalisation", "pass": true, "evidence": "失败定稿分支搬进 `cli_impl::run_round_and_finalize`（`src/cli_impl.rs:694-711`），`run` 只调它（`:614`）。我植入 P-E（删掉 `let _ = finalize_run(run_dir, &failed);`）⇒ `e1_increment::the_real_round_path_persists_a_failing_rounds_verdict` **RED**（panicked at `tests/common/mod.rs:687` 的 `read: Os { code: 2, kind: NotFound }`，即 `runs/run-1/exit_code` 未被写出）⇒ 该分支真的被离线测试执行到，DR-67 DEF-A 的可执行化成立。"},
    {"id": "C5-hygiene-directories", "pass": true, "evidence": "`hygiene::suspicious_directories`（`src/runtime/hygiene.rs:173-213`）覆盖目录名 `-*`/`_*`/`tmp_*`/`*.bak`/`*.tmp`/含 `%`/含 `$`，`hygiene_ignored` 只跳过 `.hoh/.git/.godot/.import`（`:33-35`）⇒ 工程根的 `-p` 会被命中；已接进 `result.json`（`run_loop.rs:1590-1592`，字段 `model.rs:346` `#[serde(default)]`）。单测 `suspicious_directories_sees_the_shell_accident_a_file_scan_misses` 断言 `-p`/`scripts/_helpers`/`%TEMP%` 命中且 `suspicious_files(root).is_empty()`（**证明文件扫描对目录是盲的**）——该单测我实测在门里绿。"},
    {"id": "C5-p-directory-removed", "pass": false, "evidence": "**`-p` 仍在**（见 D7）：`F:\\moonbit-hof-rs\\.workspace\\mario` 根下 `-p` 目录 mtime `2026-09-30 10:51:57`，仍在、仍空。调度者的验收条目问『is it gone』⇒ **没有**。实现者在报告 §3.4/§7.4 明确披露并给出理由（任务书 §3 禁止改 `.workspace/mario/**`，冲突时服从任务书），调度者已在 `D272` 裁定认可该做法并把清理推给拥有该工作区的批次。"},
    {"id": "C5-redaction", "pass": false, "evidence": "**密钥明文确实没有入库，但脱敏破坏了一条冻结证据记录，且 REDACTION.md 的自述与字节事实不符（见 D2）。** 我用 `config/model.secret.env` 里的真值（51 字符）扫全部 tracked 文件：**0 个文件含明文**（与 T9 验收一致）。但 `experiment/dev1_commands.txt` 被改写的方式不是『只删 53 字节』：52200 → 52359 B、**LF 184 → CRLF 183**（新增 183 个 `\\r`）、**记录数 184 → 183**——`s008` 的两条记录被**合并成一行**，`dir /b -p` 这个字符串在**全文里消失**（我 python 计数 `lines-with-dir-/b/-p`：OLD 1 → NEW 0）。即脱敏吃掉了记录边界与 `dir /b -p` 这条命令的文本（它正是 D3/`-p` 缺陷的证据）。`keyval.txt` 仍留在**已入库**的 `TASK-SMOKE-T9-ACCEPTANCE.md:73/:102` 与 `TASK-SMOKE-T9-REPORT.md:421`（实现者已披露，见下条）。"},
    {"id": "C5-keypath-committed", "pass": false, "evidence": "验收条目要求『no credential and no key path remains in anything committed』。**credential：通过（0 命中）。key path：不通过**——`git grep -n keyval` 命中 `TASK-SMOKE-T9-ACCEPTANCE.md:73`（含完整 `…/smoke-t9/keyval.txt`）、`:102`、`TASK-SMOKE-T9-REPORT.md:421`（`%TEMP%\\smoke-t9\\keyval.txt`），三者都在 HEAD 里。此外 `src/runtime/secrets.rs:65/160/185/191` 也含 `keyval.txt` 字面（本轮新写的文档注释与测试夹具，路径是 `/secret/path/keyval.txt` 之类的假值，非真实路径，不计）。实现者已把这两处列为『未闭合、交调度者裁量』（报告 §6 未验证 6、`REDACTION.md` §Residual），调度者 `D272` 裁定保留；**故这是被披露的未达标项，不是静默遗漏**。"},
    {"id": "C6-gates", "pass": true, "evidence": "**我自跑、仓外 target、`CARGO_INCREMENTAL=0`、从零编译**：`CARGO_TARGET_DIR=C:\\Users\\wyl\\AppData\\Local\\Temp\\dr69acc\\target CARGO_INCREMENTAL=0 cargo test --offline --no-fail-fast` ⇒ **46 条 `test result:` 行、passed=436 / failed=0 / ignored=7、`EXIT=0`**（与报告逐字相同）；`cargo fmt --check` ⇒ **`FMT_EXIT=0`**。`ignored` 未增长：`tests/godot_smoke.rs` 的 `#[ignore` 出现数 `9aebbe1` 与 `HEAD` **都为 8**（7 属性 + 1 文档注释），套件口径 7→7。无既有测试被删：我按『函数名 + 前 3 行内有 `#[test]`/`#[tokio::test]`』解析全仓，`9aebbe1`→`HEAD` 测试函数 **389 → 398**，**删除集合为空**（新增 9 条：hygiene 1、secrets 2、developer_contract 1、e1_increment 1、evidence_battery 4）。三条被改动的既有断言我逐条判**非放宽**（一条是需求驱动的极性反转、一条是把全电池计数收窄到被测步自己的 raw 记录且 `==1` 不变、一条是把排除集扩到 4 个）。`git ls-files '*.rs'` = 83（与报告一致）。"},
    {"id": "C6-plants-production", "pass": true, "evidence": "**我自己的 5 次植入全部在 `src/**` 生产代码**，各自使对应测试转红（P-A/P-B/P-C/P-D/P-E，逐条见 §6），且**每一次还原都四重判据齐全**：`cmp` 对仓外备份 `BYTE-IDENTICAL` + `git hash-object` == `HEAD:<path>` blob + `git status --porcelain` 空 + `git diff --stat` 空。其中 `src/harness/cap.rs=7409c96425…`、`src/tools/mod.rs=a6ad52a029…`、`src/adapter/godot.rs=8e0968454e…`、`src/cli_impl.rs=c8f5381fb9…` 四个 blob 与被验收报告 §4 的 P2/P1/P3(+P5)、P4/P1 还原哈希**逐字相同**，构成对实现者还原记录的一致性佐证。P-B2 不是「植入使测试红」而是**反向证据**：它使门保持全绿，从而证明接线无覆盖。**我没有重跑实现者自报的 9 处植入**（见 §9 未验证）。"},
    {"id": "C7-guards", "pass": true, "evidence": "**四条 `runs/**` 基线逐字未变**（口径与自证见 §7.1）：t6 `135 files c144ef32…7a9c03`（= 任务书自证值）、t7 `115 files 6e4c1595…20fb7`、t8 `358 files 6d11b2c6…bdf5a7`、t9 `83 files 541e2d81…36ca9d`。**写-删检查**：`runs/smoke-t6|t7|t8|t9` 下**晚于 `2026-09-30 11:27:30`** 的文件数与目录数**全为 0**（比报告的 12:00 切点更严）。`PRD-mario.md` sha256 `4c81c3a9…5c3a` 未变。**无新依赖**：`git diff 9aebbe1..HEAD -- Cargo.toml Cargo.lock` 空。**未 stage / 未 push**：`git diff --cached` 空、`origin/master=9aebbe15…`、ahead 8（7 个 DR-69 提交 + 调度者的 `6ebb75d`）。**引擎未改**：嵌套仓 `git -C godot-mcp/godot rev-parse HEAD = fc63af77c33368c4a1bb839c95d19750554f63a3`、`status --porcelain -uall` **0 行**；外层 pathspec 真命中对照 `ls-files godot-mcp = 6484` vs `ls-files godot-mcp/godot = 0`。**`.workspace/mario` 未改**：我按运行时排除集 `{.hoh,.git,.godot,.import}` 逐字节比对，**活体工程树（17 文件）与 `runs/smoke-t9/versions/1f3d20ed…`、`iter-1/planner-view` 完全一致**；批次窗口（>12:14）内无任何被排除集之外的文件写入（最新工程文件仍是 t8 的 `player.gd 07:19:25`）。**仓内无临时物**：`git status --porcelain -uall` 空，批次受控清单 31 项（含报告与 `DECISIONS.md`）之外无新增（`%DST%` 是 2026-09-24 的既有已跟踪异物，T8 验收 D8 已登记；`target/` 被 gitignore）。**三个假绿陷阱全部亲手复现**（§7.4）。"},
    {"id": "C8-honesty", "pass": false, "evidence": "**大部分诚实项成立**：未声称 E1/E3 met（§0 表、§6 未验证 2、§7.6 逐条核对）；明确把 Tester 证据形状修复列为『从未在真机被走到』（§6 未验证 3）；披露了 `-p` 未删的冲突、密钥管道入库、~14 帧滞后、`touch` 只针对已存在文件、③ 的『红』是编译级红、两处既有断言的改动、以及『本批没有度量真机成功』。**两处实质失准**：(1) 报告**未披露**路由发布窗口与角色执行窗口不相交（D1 的 major，报告 §6 推断 1 反而给出 ≈0.85 的『真机将成功』）；(2) 与报告同批交付的 `REDACTION.md` 写『**53 bytes** were removed. **Nothing else in the file was touched**』，而字节事实是 +159 B、LF→CRLF 全量改写、一条记录被合并且 `dir /b -p` 消失（D2）。这两条都属『自述与实测不符』，故本项判 fail。"}
  ],
  "defects": [
    {
      "id": "D1",
      "severity": "major",
      "what": "**跨进程路由在正常轮次里没有与任何角色进程共存过 ⇒ 任务书①要修的『角色够不到游戏端点』在真实系统里没有被修掉，判据测试只在一个真实流程中不会出现的场景（别人已经写好的 route 文件）上成立。** 发布只在 harness 电池的 `step_play_scene`（`src/adapter/godot.rs:623` → `:903` `register_game_endpoint`），撤下在同一 pass 的最后一步 `step_stop_scene`（`:629` → `clear_game_endpoint`，无条件）；角色全部在电池之前（Planner/Developer）或之后（Tester）运行（`src/runtime/run_loop.rs:673/884/1111/1263/1373`），角色进程彼此串行且不跨越电池。角色自己 `hoh tools call editor_play_scene` 也不会注册/发布（`McpChannel::call` 不注册，`src/tools/mod.rs:329-358`）。⇒ 真机正常路径下 `hoh tools call running_game_*` 依旧 `game_endpoint_unavailable`；唯一会看到 route 的情况是电池中途 Err 导致 `step_stop_scene` 被跳过（错误路径副产品）。因此报告标题『打通角色够不到游戏端点』与本批 ① 的实际效力被高估；真正缓解 t9 症状的是 ② 的提示词改动。",
      "reproduction": "读 `src/adapter/godot.rs:613-631`（步序）与 `:2528-2540`（无条件 clear）；`grep -rn register_game_endpoint src/`（只 `godot.rs:903`）；`grep -rn clear_game_endpoint src/`（调用点只 `godot.rs:2534`）；`sed -n '673p;884p;1111p;1263p;1373p' src/runtime/run_loop.rs`；再看我的植入 P-A 输出的 `game_endpoint_unavailable` 文案——它正是真机角色会得到的文案。"
    },
    {
      "id": "D2",
      "severity": "moderate",
      "what": "**对已入库冻结证据的脱敏破坏了记录边界与一条命令记录，且改写范围远超自述。** `experiment/dev1_commands.txt`：52200 → 52359 B（+159，而 `REDACTION.md` 说删了 53 B）；行尾 LF→CRLF（0 → 183 个 `\\r`）——本仓工作树原本是纯 LF；记录数 184 → 183（`s008` 两条被合并）；`dir /b -p` 在全文消失（1 → 0 行命中）。原因是脱敏脚本从 `HOH_MODEL_API_KEY=` 匹配到**下一个 `\"` 字符**，而原文件在该处**本来就是被截断的行**（`…/AppD\\n` 结尾），于是把换行与下一条记录的前缀一起吞掉。⇒ 『redaction did not destroy the evidence's usefulness』不成立：`-p` 缺陷的那条命令证据被吃掉，且『只删 53 字节、别的没动』是错的（即便审计链可从 `git revert 3adab37` 恢复）。",
      "reproduction": "仓外 `python redaction_diff.py`：OLD（`git show 9aebbe1:…/dev1_commands.txt`）bytes 52200 / cr 0 / records 184 / `dir /b -p` 命中 1；NEW（工作树）bytes 52359 / cr 183 / records 183 / 命中 0；`python inspect_redaction.py` 打印新旧 `s008` 段落原文。"
    },
    {
      "id": "D3",
      "severity": "minor",
      "what": "**密钥文件路径仍留在已入库文件里**（验收条目要求『no key path remains in anything committed』）。`TASK-SMOKE-T9-ACCEPTANCE.md:73/:102`（含完整 `/c/Users/wyl/AppData/Local/Temp/smoke-t9/keyval.txt`）与 `TASK-SMOKE-T9-REPORT.md:421`。密钥**明文 0 命中**，且该残留被实现者与调度者显式裁定保留（D272 裁定 2：那是缺陷披露本身，就地删除等于销毁审计痕迹）。",
      "reproduction": "`git grep -n keyval`（tracked）；仓外 `python secret_scan.py`：用 `config/model.secret.env` 的 51 字符真值扫全部 tracked 文件 ⇒ `CREDENTIAL-VALUE` 命中 0，`keyval.txt` 命中 3 行（上述两个文件）。"
    },
    {
      "id": "D4",
      "severity": "minor",
      "what": "**输出上限的生产接线没有任何测试覆盖。** 删掉 `src/harness/mini.rs:66-69` 的 `CappedEnvironment` 包装后：`tool_output_ceiling` 4/4 全绿；全量套件在该植入下执行到的 36/46 个 target **0 failed**；补跑剩余 8 个 target 全绿、`CARGO_EXIT=0`。`grep -rn MiniHarness tests/` 只命中 `godot_smoke.rs`（7 条 `#[ignore]`，需真机）与 `model_identity_config.rs`（只验 wire 名）。⇒ 报告 §3.2 把『真 `LocalEnvironment` 测试』当作『harness 真正用的那个环境边界』的证明**不成立**：该测试自己构造 `CappedEnvironment`。后果：未来有人删掉这层包装，门会保持全绿，而 15.5 MB 回放事故原样复活。",
      "reproduction": "`python plants.py apply P-B2` ⇒ `cargo test --offline --test tool_output_ceiling`（4 passed）与全量套件（36 targets, 0 failed；`suite-PB2.txt`）+ 8 个补充 target（全绿，`CARGO_EXIT=0`）；`python plants.py restore P-B2` 后 `cmp` 逐字节一致。"
    },
    {
      "id": "D5",
      "severity": "minor",
      "what": "**② 的矛盾只在 `developer.md` 一侧消除，交付给 Developer 的技能里仍在教它用够不到的通道自证。** `src/prompts/skills/godot-dev.md:65-78` §5『Self-test the behaviour before you finish』给出 `editor_simulate_input_action` + `running_game_get_node_property_samples` 的完整配方（并断言 `samples[*].position.x must change`）；§6 又要求 `editor_play_scene` 后调 `running_game_get_scene_tree`。该技能会被注入 `.hoh/skills/**` 交付角色；`tests/developer_contract.rs:121` 还**要求**这段字符串存在（本批未改该测试）。因为角色自己调 `editor_play_scene` 不发布 route（D1），这条配方在真机上仍然必然失败——正是 t9 烧预算的同型路径。",
      "reproduction": "`sed -n '65,92p' src/prompts/skills/godot-dev.md`；`sed -n '108,125p' tests/developer_contract.rs`（needle 列表含 `running_game_get_node_property_samples`）；`grep -rn 'register_game_endpoint' src/`（无 CLI 路径）。"
    },
    {
      "id": "D6",
      "severity": "minor",
      "what": "**陈旧 route 会被无条件采纳，没有 `pid`/新鲜度/存活校验**；`pid` 字段记录但从不使用。后果：一次 `running_game_*` 调用从 DR-43 的明确拒绝（`game_endpoint_unavailable`）变成传输失败；若该端口事后被另一个 MCP 服务占用，调用会被**另一个**端点应答。触发面：显式复用 `--run-id`、上一轮崩溃/电池中途 Err 留下的文件（默认 run id 带 uuid 前 8 位，故非默认路径）。",
      "reproduction": "仓外 `python stale_route.py`：自建后立刻关闭的回环端口 `127.0.0.1:58325`，route 文件写进仓外 temp，真实 `hoh.exe tools call running_game_get_scene_tree --role developer` ⇒ `exit code: 5`、`game_endpoint_unavailable in output: False`、输出为 `MCP transport failure to http://127.0.0.1:58325/mcp: … (os error 10061)`。"
    },
    {
      "id": "D7",
      "severity": "minor",
      "what": "**被点名的 `-p` 目录仍在工程树里**（仍是空目录，仍会被复制进 A_0/planner-view）。卫生检查现在会**报告**它（`artifact_hygiene.suspicious_directories`），但运行时不删任何东西。此为**被披露的需求冲突**：任务书 §3 禁止改 `.workspace/mario/**`，而调度者的追加指令要求删除；实现者服从任务书并显式点名，调度者 D272 已裁定认可。",
      "reproduction": "`ls -la .workspace/mario`（`-p`，mtime `2026-09-30 10:51:57`）；`python ws_check.py`（工程树 17 文件与 A_0 快照逐字节同一，空目录对文件级哈希不可见）。"
    },
    {
      "id": "D8",
      "severity": "info",
      "what": "**『被中止尝试的证据保全』落在电池 pass 这一层，而不是它引用的那次事故。** `preserve_then_clear` 保护的是 `.hoh/deterministic` 被第二遍电池重建的场景（`runs/<id>/quarantine/deterministic-pass-1.stale-<ts>`）；t9 的真实事故是**操作者把整个 `runs/smoke-t9` 目录删掉**（16.4 MB 轨迹不可恢复），运行时没有任何钩子能覆盖该行为。实现者在报告 §3.2 以『运行时也有同样形状』如实说明，未夸大为已解决。",
      "reproduction": "`src/runtime/run_loop.rs:360-437`（`preserve_then_clear`/`copy_dir_recursive`/`run_battery_pass` 调用点）；对照 `TASK-DR69.md` §1-③ 与 D270 对事故的描述。"
    },
    {
      "id": "D9",
      "severity": "info",
      "what": "**E3 的『证据形式』用的是游戏进程语义 API，不是 `REQUIREMENTS.md:114` 字面写的 `simulate_sequence`。** `grep -rn simulate_sequence src/` = 0 命中；电池走 `running_game_create_input_recording`/`play_input_recording`/`run_test_scenario` + `running_game_assert_node_state`，编辑侧只留 `editor_simulate_input_action` 作 `EDITOR_SIDE_INJECTION` 补充。按 T9 验收的判定口径（游戏进程内语义工具强于编辑器侧注入）这不构成缺陷，但它说明『形式达标』依赖对需求措辞的解释，下一批若要引用 E3 met 需把该口径写实。",
      "reproduction": "`grep -rn simulate_sequence src/`（0）；P-D 打印的 label 序列；`REQUIREMENTS.md:114`。"
    },
    {
      "id": "D10",
      "severity": "info",
      "what": "**调度者自己的 `D272` 有两处小失准**（不属于被验收对象的产物，仅登记）：(1) 写『**6 个提交**』，实际本批 7 个（`96b7c29/84725c8/94f5c23/b8bde1e/4257a80/3adab37/03b35dd`）；(2) 写路由文件『**不在 Developer 可写目录**』——运行目录路径经 `HOH_RUN_DIR` 交给每个角色，OS 层面该用户当然可写，这是设计意图而非强制（见风险 R4）。此外 `D272` 在报告入库的同一提交里把结论写成定论，仍带有 T9 验收 R8 的『验收前先落决策日志』次序问题。",
      "reproduction": "`git log --oneline 9aebbe1..HEAD | wc -l`（8，含 D272 那一个）；`sed -n '10447p;10450p' DECISIONS.md`；`grep -n HOH_RUN_DIR src/runtime/invoke.rs`。"
    }
  ],
  "risks": [
    "R1（最重要）**① 的效力问题会把下一批引向错误判断**：报告与 D272 都把『角色 CLI 够不到游戏端点』记为已修，但真机正常路径下角色仍会拿到 `game_endpoint_unavailable`。若下一批据此认为『Developer 现在能观测游戏了』而复用 t8/t9 那种把可观测性钉在 `running_game_*` 上的 plan，零增量很可能原样重演（D270 的结构性根因并未消除，只是不再由角色直接承担）。**建议**：要么让发布跨角色窗口存活（例如本轮第一次 publish 后直到轮末才撤、或把 route 随 Tester/battery 之外的阶段也保留），要么让角色侧 `editor_play_scene` 也走注册路径，要么在 plan/判据层显式禁止角色直连（把 (B) 也写进任务书），三者选一并写进文档。",
    "R2 **E3 的位置断言是弱形式的『变了吗』**：`position:neq <窗口首样本>` + 轴上 `delta != 0`，没有幅度/方向/速率的引擎侧判据。真机上若有任何非注入位移（重力、碰撞、上一次动作未释放、断言与首样本之间又跑了几帧）也可能通过 neq；`INPUT_HAD_NO_EFFECT` 与窗口内 release 逻辑是主要防线，但整套判据的强度依赖电池自己的采样实现，不依赖引擎的裁决。",
    "R3 **E3/E1 仍未由任何真机证据支持**：本批全部为离线，`running_game_capture_screenshot` 的内联图片形状、`running_game_assert_node_state` 的 `position:neq` 参数接受度（`assertion_expectation_for` 的 `{x,y}`→`Vector2` 归一化）都只在源码注释与回环替身上对过，报告自评 ≈0.6，我同意这一保守度。",
    "R4 **route 文件是一个角色可写的信任边界**：`HOH_RUN_DIR` 交给每个角色，因此角色（在 OS 权限允许时）可以改写 `<run dir>/game_endpoint.json`，让自己后续的 `hoh tools call running_game_*` 打到任意回环端点。它不改变『角色本来就能自造证据文件』的基本面，但会把『这条观测来自游戏进程』这一推断变弱——任何以角色 CLI 输出为游戏观测证据的判据都不应依赖于它。",
    "R5 **采样滞后仍未标定**：报告的处置（期望值取同窗口首样本）是对的，但观测文本里每窗口 `delta=…` 会被下一批当作位移总量读（系统低估约 14 帧 ≈ 51 px）。建议在观测文本里加一句『本值是采样窗内位移，注入后前 ~14 帧不在窗内』，或直接在同一轮里量一次滞后。",
    "R6 **`preserve_then_clear` 的命名/时序**：`label` 用 `pass-1` 表示『被替换的那一遍』，而 `rename` 目标时间戳只到秒；同一秒内连续两次同名 pass 会撞名（当前 pass 编号递增，实际不会撞）。另：`rename` 成功即视为保全，若 `runs/<id>/quarantine` 与 `.hoh/deterministic` 跨卷（同盘时不会），才走复制分支。",
    "R7 **流程次序**：调度者在验收落地前就把 `TASK-DR69-REPORT.md` 与 `D272` 一并入库（`6ebb75d`，13:14:51，我验收期间），使我的验收若判 fail 就必须回改已入库的决策定论——与 T9 验收 R8 同族，仍未解决。"
  ],
  "unverified": [
    "U1 **我没有重跑实现者自报的 9 处生产植入 + 1 处测试载体植入**：我只复核了 4 个被改文件的还原 blob 与报告哈希逐字一致（`cap.rs 7409c96425`、`mod.rs a6ad52a029`、`godot.rs 8e0968454e`、`cli_impl.rs c8f5381fb9`），并用我自己的 5 次植入独立证明对应机制各自承重。报告 §4 的 `plants-output.txt` 我没有逐行重放。",
    "U2 **真机行为一律未验证**（离线硬约束）：游戏端点上的路由采纳、`running_game_assert_node_state` 的参数接受度、内联截图的形状、`capture_frames` 兜底、以及 D1 的『窗口不相交』在真实引擎时序下是否完全如代码所示（我依据的是纯代码步序，没有观测过一次真实电池）。",
    "U3 **`.workspace/mario` 的 `.hoh/**` 与 `.godot/**` 我没有逐文件审计**：只做了『工程树逐字节等于 A_0』与 mtime 普查（批次窗口内无写入）；`.hoh/args/editor_get_errors.json` 停在 `11:27:26`（T9 轮内），`.godot/editor/*.cfg` 停在 `11:36:30`（T9 验收期），都不是本批。",
    "U4 **`_p`/目录卫生在真实轮次里的落地未验证**：我只核了函数、接线与单测；没有跑过一轮含 `-p` 的真实轮次去看 `result.json.artifact_hygiene.suspicious_directories` 的实际内容（离线跑不了需要模型端点的 `run`）。",
    "U5 **门的『先强制重编』我没有复现报告的做法**：我用的是**仓外全新 target + `CARGO_INCREMENTAL=0`**（从零编译，等效于无陈旧 rlib），比 `touch` 更强；我因此没有去跑 `git ls-files '*.rs' | xargs touch`（它会改变工作树 mtime，且对我的结论无增益）。报告称 `Compiling hof-rs` 出现 1 次，我没有核它的日志。",
    "U6 **`TASK-SMOKE-T9-evidence/**` 其余文件我未逐字节审计**：只对 `dev1_commands.txt`、`REDACTION.md`、`prerun_state.txt`、`play_scene.json`/`experiment/` 里与密钥、`-p`、路由相关的部分做了检查。",
    "U7 **`publish_game_route` 的原子性未做并发压测**：代码是 temp+remove+rename（`endpoint.rs:102-113`），Windows 上 `rename` 覆盖需先 `remove_file`，存在极窄的 TOCTOU 窗口（读者在 remove 与 rename 之间读到『无文件』⇒ 回落到 `game_endpoint_unavailable`）。我未构造并发反例。",
    "U8 **D4 的『无覆盖』结论有一个边界**：我证的是**当前测试集**在删掉 `mini.rs` 接线后全绿；我没有证明『不存在任何其它路径能把未截断字符串送进请求』（例如 `exception_info`、模板变量、`get_template_vars`）——我只核了 `Output.output` 这条主路径与 `extra` 的记录方式。"
  ]
}
```

---

## 1. 逐项判定表（验收条目 → 我的判定）

| # | 条目 | 判定 | 我的关键证据（自产） |
|---|---|---|---|
| 1 | 跨进程路由：角色 shell 真能到达 / 机制如报告所述 / 停用即红 / 是否只满足测试 / 范围与清理 / 陈旧 route | **机制 pass；真实系统效力 fail** | P-A 植入 ⇒ 标题测试 RED 且文案逐字等于 t9 的 `game_endpoint_unavailable`（`left Some(5)`）；`godot.rs:613-631` + `:903` + `:2534` + `run_loop.rs:673/884/1111/1263/1373` ⇒ 发布窗口与角色窗口不相交；仓外 `stale_route.py` 实测陈旧 route 被采纳（exit 5、os error 10061、无 `game_endpoint_unavailable`） |
| 2 | 矛盾：developer.md 不再让角色经够不到的通道自证，且补了替代 | **developer.md pass；交付技能侧 fail** | 报告 §3.1 的改动我逐行核过（删 #4、加顺序/禁令、自证限定编辑器侧）；但 `godot-dev.md:65-92` 仍在教 `running_game_*` 自证且 `developer_contract.rs:121` 仍要求该串 ⇒ D5 |
| 3 | 工具输出上限：截断 + 显式标注 + **不可回放进后续请求**（含反例） | **pass** | P-B 植入 ⇒ 3 条 RED，含 `got 15570803` / `got 2097152`；`Output.output` 就是 observation 源（mini `models/mod.rs:229-283`），`CappedEnvironment` 是 `env.execute` 唯一包装点；`cap_tool_output` 输出里不存在超限连续字节串 |
| 4 | E3 轮内证据形态（前后帧 + 节点断言）**且不得在未标定滞后下断言总位移** | **pass** | P-D 植入 ⇒ 该测试 RED 并打印真实 label 序列；承重判据是 `movement_on_intended_axis`（只判零）与 `position:neq 窗口首样本`（`godot.rs:2286-2315`、`:2992-3002`）⇒ 无总位移断言 |
| 5a | 可执行的失败定稿 | **pass** | P-E 植入 ⇒ `run_round_and_finalize` 测试 RED（`/exit_code` NotFound） |
| 5b | `-p` 目录是否已消失 / 卫生是否扩到目录 | **目录仍在（fail）；卫生扩到目录 pass** | `ls -la .workspace/mario` 有 `-p`（10:51:57）；`suspicious_directories` + `run_loop.rs:1590-1592` + 单测证明文件扫描对目录是盲的 |
| 5c | 环境转储脱敏：committed 里无凭据、无 key 路径、且未毁掉证据可用性 | **fail（三个子项里两个不满足）** | 明文 0 命中（51 字符真值全树比对）；`keyval.txt` 仍在两个 committed 报告；`dev1_commands.txt` 记录 184→183、LF→CRLF、`dir /b -p` 消失、+159 B（`REDACTION.md` 说删 53 B、别的没动） |
| 6 | 门：`cargo test --offline` exit 0 ≥ 414/0/7 且 ignored 不增 + `fmt --check`；仓外 target + `CARGO_INCREMENTAL=0`；植入在生产代码且逐字节还原 | **pass** | 436/0/7 EXIT=0（46 targets，仓外全新 target、增量 0）；`FMT_EXIT=0`；测试函数 389→398 无删除、`#[ignore` 8==8；我的 5 次植入均在 `src/**`，每次四重还原判据齐全 |
| 7 | 守卫：四棵 runs 树逐字节不变 + 写-删检查 + mario/PRD 不变 + 无新依赖 + 未 stage/push + 嵌套引擎未改 + 无仓内临时物 + 三个假绿陷阱 | **pass** | 摘要与自证 §7.1；写-删 `>11:27:30` 全为 0/0；工程树等于 A_0 快照；`Cargo.*` 零 diff；`origin` 未变；`fc63af77…` 0 行；`status -uall` 空；三陷阱亲手复现 |
| 8 | 诚实：报告 caveat 与未验证清单的裁定 | **fail（两处实质失准）** | 未声称 E1/E3 met、Tester 修复仍未上真机（成立）；但未披露 D1 的窗口问题、且 `REDACTION.md` 的字节自述不实 ⇒ D1/D2 |

**总判：`fail`**（1 major + 1 moderate + 5 minor + 3 info）。fail **不表示本批白做**：①②（developer.md 一侧）③④ 与门/守卫/植入纪律都经我独立复现为真；fail 的核心是 **(a) ① 对它声称的根因在真实系统里无效**（D1）、**(b) 脱敏破坏了它声称保全的证据**（D2）。这两条都能在小范围内修好：把路由的发布窗口延到角色可见（或明确改走 (B) 并写进任务书）、给采纳加 `pid`/新鲜度校验；脱敏改为**旁注**并把 `dev1_commands.txt` 的 `dir /b -p` 记录恢复（或回滚 `3adab37` 后只改那一行的值、保留 LF）。

---

## 2. ① 的诊断复算（我自己看代码，不看报告）

| 事实 | 落点（我读到的） |
|---|---|
| 游戏路由是进程内状态 | `src/tools/mod.rs` `McpChannel { game: Arc<Mutex<Option<GameRoute>>>, game_history, … }` |
| 无注册即硬 bail、禁止回落编辑器 | `src/tools/mod.rs` `client_for()` 的 `ToolScope::Game` 分支（文案：`game_endpoint_unavailable: … Falling back to the editor endpoint is not allowed (DR-43).`） |
| 谁发布 | 只有 `src/adapter/godot.rs:903`（电池 `step_play_scene`，`:623`） |
| 为什么 `hoh tools call` 走另一条路 | `src/cli_impl.rs:52-56` 每次新建 `bridge::channel_for(&config)` → `McpChannel::new`（`game` 初值 `None`）→ 进程退出 |
| 编辑器是否知道端口 | 是（`editor_play_scene` 回包带 `endpoint/mcp_port/pid`），但编辑器端点**不提供**任何 `running_game_*` 工具（报告引的 t9 冻结证据；我未重跑真机，按报告与 T9 验收一致） |
| 本批如何跨进程 | `src/tools/endpoint.rs`：`GAME_ROUTE_FILE`/`GAME_ROUTE_ENV`/`publish_game_route`（temp+rename）/`load_game_route`（坏 JSON ⇒ None，不猜端口）/`withdraw_game_route`；`McpChannel::use_game_route_file` 设路径并采纳；`register_game_endpoint` 先发布再注册；`clear_game_endpoint` 撤文件；`cli_impl.rs:55` 采纳；`runtime/invoke.rs` 给每个角色 `HOH_GAME_ROUTE`（绝对路径）；`run_loop.rs:537` 绑定路径 |

**选路 (A) 的理由**（报告 §2.2）我认同其立论：根因是路由的进程局部性，且 `running_game_*` 在编辑器端点为 0 条（改引擎被禁），所以『经编辑器中转』不可行。**但路线正确 ≠ 效果已达**：见 D1。

---

## 3. ② 的复算

- **删掉的一半**：`developer.md` 的 `[definition-of-done]` #4 旧文 `Prove this yourself with the live path (editor_simulate_input_action + running_game_get_node_property_samples) and report what you observed.` 已被结构性要求取代（我 `grep -n running_game src/prompts/developer.md` 只余 `:31-36` 一段）。
- **补上的一半**：顺序指令 + 观测归 Tester/电池 + 编辑器侧自证通道 + 禁止自造客户端/裸探端口（§0 C2 证据原文）。`tests/developer_contract.rs` 的正/反向断言与 `tests/role_shell_contract.rs` 的未渲染占位符检查共同把它钉住。
- **残留**：`godot-dev.md` §5/§6（delivered skill）仍是旧指令，且 `developer_contract.rs:121` 仍要求该字符串 —— D5。这就是『移除指令而别处仍有』的一半没做完。

---

## 4. ③ 的复算（含我自己的反例）

- 上限 64 KiB；截断保头、UTF-8 安全、标注含 `shown of total` 与『剩余已丢弃』；`extra` 记 `hoh_output_truncated/original_bytes/limit_bytes`。
- **不可回放**：`mini` 的 observation 就是 `Output.output`（`mini-swe-agent/rust/src/models/mod.rs:245-249` 的 `raw_output` 与模板渲染的 `output_value`），而 `CappedEnvironment` 是 `env.execute` 的唯一包装（`agent.rs:187-198`）。
- **我的反例 P-B**：短路上限 ⇒ `tool_output_ceiling` 三条 RED，含 `the observation a request would carry must be bounded, got 15570803`（= 真机事故字节数）与 `a real 2 MiB result must be capped, got 2097152`。
- **短板 D4**：删掉 `mini.rs` 的接线，`tool_output_ceiling` 4/4 绿、其余 target 全绿 ⇒ 接线无覆盖。

---

## 5. ④ 的复算与采样滞后裁定

- **产物侧**：每窗口 before/after PNG（无 `save_path`、内联 base64、进候选视图）与 `running_game_assert_node_state(position:neq 窗口首样本)`；三种诚实失败分开。
- **反例 P-D**（`assert_replay_moved` 直接 `return None`）⇒ 标题测试 RED，并在失败信息里打印真实 label 序列（before → 录制/回放 → 编辑器侧注入 → after → game_axis → release），证明标签由生产代码产生、且 `replay_assert_moved` 不再出现。
- **采样滞后（验收条目的关键判断）**：承重判据是 `movement_on_intended_axis` 的 `delta != 0.0`（只判零、不判幅度）+ `neq 窗口首样本`（期望与观测同窗口）。**没有任何按总位移的断言** ⇒ 按条目给的条件，**不构成缺陷**。我把它记为风险 R5（观测文本里的 `delta=` 仍会被误读为总量）。

---

## 6. 我自己的植入与反例（全部生产代码，全部逐字节还原）

驱动：`python plants.py apply|restore|verify <id>`（脚本与备份在仓外 `dr69acc/`）。

| 植入 | 文件（生产代码） | 被禁用的机制 | 结果 | 还原判据 |
|---|---|---|---|---|
| **P-A** | `src/cli_impl.rs` | 新进程不再采纳已发布的 route（删 `bridge::adopt_published_game_route(&channel, None);`） | `game_route_across_processes::a_role_shell_reaches_the_published_game_endpoint_across_processes` **RED**：`left Some(5) right Some(0)`，stderr 逐字 `game_endpoint_unavailable … (DR-43)` | `cmp` **BYTE-IDENTICAL**；`hash-object = c8f5381fb9…` == HEAD；status/diff 空 |
| **P-B** | `src/harness/cap.rs` | 上限短路（`if original_bytes <= limit` → `if true`） | `tool_output_ceiling` **3 RED**（`got 15570803` / `got 2097152`） | `cmp` BYTE-IDENTICAL；`7409c96425…` == HEAD；status/diff 空 |
| **P-B2**（反向证据） | `src/harness/mini.rs` | 删掉 `CappedEnvironment` 包装 | `tool_output_ceiling` **4/4 绿**；全量套件 36/46 target **0 failed**；补跑 8 target 全绿、`CARGO_EXIT=0` ⇒ **接线无覆盖** | `cmp` BYTE-IDENTICAL；`85b0eef0bf…` == HEAD；status/diff 空 |
| **P-C** | `src/tools/mod.rs` | `clear_game_endpoint` 不再撤下发布的 route | `registering_publishes_the_route_and_stopping_withdraws_it` **RED**（`:316`） | `cmp` BYTE-IDENTICAL；`a6ad52a029…` == HEAD；status/diff 空 |
| **P-D** | `src/adapter/godot.rs` | `assert_replay_moved` 直接返回 `None`（位置断言不再发生） | `the_input_replay_produces_before_and_after_frames_and_a_positional_assertion` **RED**（`:3344`） | `cmp` BYTE-IDENTICAL；`8e0968454e…` == HEAD；status/diff 空 |
| **P-E** | `src/cli_impl.rs` | 失败轮次不再持久化判决（删 `finalize_run`） | `e1_increment::the_real_round_path_persists_a_failing_rounds_verdict` **RED**（`read: NotFound`，`tests/common/mod.rs:687`） | `cmp` BYTE-IDENTICAL；`c8f5381fb9…` == HEAD；status/diff 空 |

另两个**行为反例**（不修改仓库）：
- **陈旧 route**（`stale_route.py`）：自建后关闭的回环端口 + 陈旧 route 文件 ⇒ 真实 `hoh.exe` exit 5、**无 `game_endpoint_unavailable`**、报 `os error 10061`。
- **脱敏破坏证据**（`redaction_diff.py` / `inspect_redaction.py`）：`dev1_commands.txt` 52200→52359 B、LF→CRLF（0→183）、记录 184→183、`dir /b -p` 命中 1→0。

验收结束后：`git status --porcelain -uall` **空**、`git diff --stat` **空**、`git diff --cached --stat` **空**（除本报告未跟踪外）。

---

## 7. 门、守卫、陷阱的原始读法

### 7.1 摘要口径（自证）

**PowerShell 5.1（`PSVersion=5.1.26100.6584`，`Culture=zh-CN`）；`Get-ChildItem -Recurse -Force -File`；每文件取仓根相对 POSIX **小写**路径 + 字节数 + 小写 SHA256；三列 `\t` 连接、`\n` 分行、整体 UTF-8 取 SHA256；行序 `Sort-Object`（文化排序）。**

```
runs/smoke-t6 files=135 hash=c144ef3219e21dd322978e41a5531d53dee270619c026585505920f9277a9c03 newest=2026-09-29 02:32:01
runs/smoke-t7 files=115 hash=6e4c1595753c2cdefb16e4d2e5f05242ca202c70c81a93e98ae2b9c92b520fb7 newest=2026-09-29 14:41:14
runs/smoke-t8 files=358 hash=6d11b2c61ec507b5f02525ddc0e7f7adb08763cd2439a4b08788b7fe51bdf5a7 newest=2026-09-30 07:58:28
runs/smoke-t9 files=83  hash=541e2d814e563ba667c95bde49765d05e44cf11aa5ab90b2f44931f30136ca9d newest=2026-09-30 11:27:29
```

**自证**：`runs/smoke-t6 = c144ef32…7a9c03` **命中任务书 §4 点名要求的值** ✓。**文化排序是口径的一部分**（我实测）：换 `StringComparer::Ordinal` 后 t6 仍 `c144ef32…`、t8 变 `c347bd637ab481b1ec357cbb534c1330bad18cfab85c113038fa0878e6b3d3f5`（与 T8/T9 验收记录逐字相同）⇒ 该口径与历史记录可比。

### 7.2 门（真实尾部）

```
$ cargo fmt --check                       FMT_EXIT=0
$ CARGO_TARGET_DIR=<仓外全新> CARGO_INCREMENTAL=0 cargo test --offline --no-fail-fast
  46 条 test result；passed=436 failed=0 ignored=7；EXIT=0；（`test result: FAILED` 行 = 0）
$ 测试函数集合 9aebbe1→HEAD：389 → 398；REMOVED = {}
$ tests/godot_smoke.rs `#[ignore` 出现数：9aebbe1 = 8、HEAD = 8（7 属性 + 1 文档注释）⇒ 运行期 ignored 7→7
$ git ls-files '*.rs' | wc -l  = 83
```

### 7.3 守卫

```
PRD-mario.md sha256 = 4c81c3a9995f0b3afdf01421a0c3be88573cceefc284ce9bafbfda141f0f5c3a
git diff 9aebbe1..HEAD -- Cargo.toml Cargo.lock   -> 空
git diff --cached --stat                          -> 空
origin/master = 9aebbe15f13508d1ee5063505b2827ee59cc041a（未 push）；HEAD=6ebb75dd…；ahead 8
nested engine: git -C godot-mcp/godot rev-parse HEAD = fc63af77c33368c4a1bb839c95d19750554f63a3 ; status --porcelain -uall = 0 行
outer pathspec: ls-files godot-mcp = 6484（真命中） vs ls-files godot-mcp/godot = 0（空判）
live artifact tree (17 files, excludes {.hoh,.git,.godot,.import}) == runs/smoke-t9/versions/1f3d20ed… AND == iter-1/planner-view（逐字节）
写-删：runs/smoke-t6|t7|t8|t9 中 mtime > 2026-09-30 11:27:30 的文件/目录 = 0/0、0/0、0/0、0/0
仓内临时物：git status --porcelain -uall 空；批次受控清单 31 项（含 REPORT 与 DECISIONS.md）
```

### 7.4 三个假绿陷阱（我亲手复现）

```
① git diff 对不存在的 pathspec 不报错：git diff --stat -- definitely/not/a/real/path → 输出空, exit=0
   读法：先证 pathspec 真命中（6484 vs 0 的对照就是那一步）
② cmd 里 ^ 是转义，返回值不携带信息：
   bash: cat-file -e '9aebbe1^:TASK-DR69.md' → 0 ；'9aebbe1:TASK-DR69.md' → 0 ；'9aebbe1^:definitely/not/here' → 128 ；'9aebbe1:definitely/not/here' → 128
   cmd : cat-file -e fe129a1^:<有> → %errorlevel%=0 ；fe129a1^:<无> → 0 ；fe129a1:<无> → 0 ；git rev-parse fe129a1^ → fe129a1（^ 被吃掉）
   读法：有证据力的只有 bash（探针用 9aebbe1，因为被验收提交里 fe129a1 已非 HEAD）
③ 外层仓不跟踪引擎树 / 工作区 / 轮目录：
   check-ignore -v runs/smoke-t9/meta.json → .gitignore:12:runs/
   check-ignore -v .workspace/mario/project.godot → .gitignore:11:.workspace/
   check-ignore -v godot-mcp/godot → .gitignore:33:godot-mcp/godot/
   git diff --stat -- godot-mcp/godot/bin → 空 + exit 0（什么都没说）
```

---

## 8. 我没查的

- 未审计 `TASK-SMOKE-T9-evidence/**` 的全部文件（只查了 `dev1_commands.txt`、`REDACTION.md`、`prerun_state.txt` 与路由/密钥/`-p` 相关项）。
- 未逐条重放实现者报告 §4 的 9 处植入与 `%TEMP%\dr69\plants-output.txt`（U1）。
- 未在 `9aebbe1` 上 checkout/重跑基线以复算 `414/0/7`（我只证 HEAD 上 436/0/7、且无测试被删/加 ignore；报告 414 与我独立跑出的 436 的差值（+22 passed vs +9 测试函数）可由 `tests/common/mod.rs` 被 27 个集成 target 共同编译解释的**假设未逐一验证**——我没有逐 target 对照两个版本的计数）。
- 未跑任何真机轮（硬约束），未启动 Godot，未碰任何外部端口/网络/模型端点。
- 未审计 `runs/smoke-t4..t8` 的轨迹内容（只算摘要与 mtime）。
- 未验证 `D4` 之外是否还有别的「生产接线无测试」的例子。
- 未核实现者报告里的历史转述（DR-65/66/67/68 的旧账）。

---

## 9. 给下一批的建议

1. **先裁决 ① 的效力，再谈"端点已打通"**（D1）：要么把 route 的存活期延到整个 run（例如首次 publish 后不再由 `editor_stop_scene` 撤、改由轮末统一撤，并配 TTL/`pid` 校验），要么让角色侧 `editor_play_scene` 也走注册/发布路径，要么显式选 (B) 并把「禁止把轮内游戏观测当 Developer 前置」写进任务书与 plan 判据。**任一选择都要在 `DECISIONS.md` 里以「角色执行窗口与发布窗口的关系」为第一条事实写清**，否则下一批仍会以为根因已消除。
2. **给 route 采纳加校验**（D6）：`load_game_route` 返回后校验 `pid` 存活/文件新鲜度（例如 mtime 或与 run 的 session id 绑定），并让 harness 启动时**先撤下**同目录里的旧文件而不是直接采纳；补一条「陈旧 route 不得被采纳」的测试。
3. **给输出上限的接线补一条回归测试**（D4）：最有价值的是让测试真正穿过 `MiniHarness::invoke`（可用一个只回一条超大 observation 的假 model/环境），或在 `MiniHarness` 上暴露可断言的 `limit()`；否则这层保护可被静默删除。
4. **修 D5**：`godot-dev.md` §5/§6 与 `developer_contract.rs:121` 必须同时改（把自证改成编辑器侧配方，或明确标注该通道只对 Tester/电池可用）；否则 `developer.md` 的禁令与技能的配方互相拆台。
5. **把脱敏改为旁注**（D2/D3）：不要就地重写冻结证据；删掉 `3adab37` 重做为「只替换值、保留 LF、保留记录边界」的最小编辑并核对记录数不变；若要保留 `keyval.txt` 的两处披露，就把它写成不携带绝对路径的形式（例如 `<temp-key-file>`）并在 `REDACTION.md` 记录真实字节数变化。
6. **补 `-p` 的清理**（D7）：由拥有 `.workspace/mario` 的批次删除并复核 `A_0` 内容哈希不变；同时在运行时的卫生报告里把它作为**需要人工处置**的项显式列出（现在只是报告）。
7. **真机轮的判据次序**：先让 Developer 产出增量（本批 ② 应降低绕道概率），电池跑完后再看 `input_replay` 的 6+2 张 PNG、每个窗口的 `POSITION_ASSERT_PASSED`、以及 `assert_node_state` 的接受度；`input_axis` 恒 `null` 不要再作为判据。E3 若要判 met，还需把「使用游戏进程语义 API 而非 `simulate_sequence`」的口径写实（D9）。
8. **流程**：验收结论先于 `D272` 这类"已成定论"的决策日志（R7）；追加指令不得与任务书硬约束冲突，若必须冲突应先更新任务书（`-p` 一例已由调度者自己记下该教训）。

---

## 10. 一句话

**机制是真的、门是绿的、守卫全过、我的 5 次生产植入各自红且逐字节还原——但本批的头号目标在真实系统里没有达成：路由只在 harness 电池的 `play_scene→stop_scene` 窗口里存在，正常流程下没有任何角色进程与之共存（D1，major），角色 CLI 在真机上仍会拿到 `game_endpoint_unavailable`；此外对冻结证据的脱敏把两条 `s008` 记录合并、吃掉了 `dir /b -p`、并把 LF 全量改成 CRLF（D2，moderate，`REDACTION.md` 的字节自述不实），密钥文件路径仍留在两个已入库报告里，输出上限的生产接线无任何测试覆盖，而交付给 Developer 的 `godot-dev.md` 仍在教它用那条够不到的通道自证。故判 `fail`：修 ①的效力与脱敏的原样性即可转绿。**
