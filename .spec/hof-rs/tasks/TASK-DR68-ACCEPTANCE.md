# TASK-DR68-ACCEPTANCE — DR-68（离线修复批：① 证据形状 / ② 启动闸门 / ③⑧ 输入回放与轴判据 / ④ 失败存根 / ⑤⑥⑦ / 报告就地更正）的独立验收

- 被验收对象：`.spec/hof-rs/tasks/TASK-DR68-REPORT.md` + `99c9fba..5baa801` 的 9 个提交（含报告就地更正）
  + 本批产出的生产代码/测试；判据来源：`.spec/hof-rs/tasks/TASK-DR68.md`（八项要求）。
- 对照：`.spec/hof-rs/tasks/TASK-SMOKE-T8-ACCEPTANCE.md`（上一轮 adverse acceptance，D266）、`DECISIONS.md` D265/D266/D267。
- 性质：**独立、离线、只读为主**。我无上游对话上下文，报告只当**线索**；下列每条结论都是我自己重算/重读/自己复现的。
- **硬约束遵守**：未启动 Godot；未碰任何端口（只做进程表**读取**）；未联网；未调模型端点；未跑真机轮；
  **未写、未删、未重命名任何 `runs/**` 路径（连临时文件都没有）**；未修改 `.workspace/mario/**`、`.spec/hof-rs/PRD-mario.md`、
  `DECISIONS.md`、`godot-mcp/**`；未 push；未 stage；**未改写任何本地提交**。
  仓外临时物：`C:\Users\wyl\AppData\Local\Temp\dr68acc\`（digest.ps1、digest_ord.ps1、hashtree.py、assertdiff.py、plants.py、verify.sh、backup/、full_test.txt、clean_test.txt、plantI.txt）。
  仓内唯一新增文件是本报告。
- **并发活动（非实现者所为，也不是我）**：我开工时 HEAD `5baa801`、工作树只有未跟踪的报告；验收期间**调度者**落了
  `e715ed4`（把 DR-68 报告入库）与 `7cb53eb`（D267）；收工时 HEAD `7cb53eb…`、`origin/master` 全程 `ce22e18…`（ahead，未 push）。
  我验收的是 **`99c9fba..5baa801` 的 DR-68 产物**，与调度者的两个文档提交无关。

---

## 0. 结构化结论

```json
{
  "verdict": "pass",
  "scope": "pass 针对 TASK-DR68 的八项要求：全部落地、全部由我独立复现（套件 414/0/7 exit 0 + fmt 干净 + 11 处我自植的反例各自红 + 三条 runs 基线摘要未动）。同时登记 1 处 medium 缺陷（③(a) 的『轴值改变』断言无任何测试覆盖：我删掉它，41 个电池测试全绿）与 3 处 minor/信息级不准确（报告 §5 的 max_schema_retries 值、D267 的摘要尾串、报告更正声明『一字未删』的字面口径）。这些都不使任何一项要求失效。",
  "criteria": [
    {
      "id": "ITEM-1 掩蔽假绿（⑧）",
      "pass": true,
      "evidence": "判据已按目标轴：`movement_on_intended_axis`（src/adapter/godot.rs:2791-2801）取 `intended_axis`（jump→y，其余→x）的 `after-before`，`moved = delta != 0.0`；调用点 godot.rs:2085。我的反例 A（把 `moved` 还原成整向量 `quadruple[\"before_position\"] != quadruple[\"after_position\"]`）使目标测试 `a_dead_target_axis_is_not_movement_even_when_the_other_axis_moves` **红**，其失败串逐字为 `a dead \\`x\\` axis is not movement, however much \\`y\\` moved: … axis=x delta=0.000000`，且四元组 `before.x=60.0 after.x=60.0 before.y=283.0 after.y=342.0` —— 目标轴零位移、另一轴有位移，被整向量判成『移动』；还原后该测试绿（我最终全量套件 414/0/7，其中该测试 ok）。"
    },
    {
      "id": "ITEM-2 输入回放（③a/③b）",
      "pass": true,
      "evidence": "释放确实在**游戏进程内**：`semantic_release_action`（godot.rs:1770-1780）走 `semantic::PLAY_INPUT_RECORDING = \"running_game_play_input_recording\"`（godot.rs:2993），经 `record_semantic_call`→`self.call` 与**按下**完全同一条路径（godot.rs:1637-1654 对 `semantic_inject_action_detailed` 用同一 `self.call(PLAY_INPUT_RECORDING,…)`），前缀 `running_game_` 由 `src/tools/endpoint.rs:19-24` 路由到游戏端点；参数为 `{\"type\":\"action\",\"action\":X,\"pressed\":false}`。循环 `held_in_game.drain(..)`（godot.rs:1960-1968）在每个方向测试前释放上一输入。测试 `the_input_replay_releases_the_previous_direction_before_the_next_one` 断言事件确实带 `pressed=false` 且 release 在 move_left press 之前、并断言 `move_left` 的 `after.x < before.x`；我的反例 B（用 `held_in_game.clear()` 顶掉释放）使该测试在 tests/evidence_battery.rs:2717 **红**，红输出里直接复现了 t8 假象：`move_left:test_scenario observed_axis=0.0`、`move_left:game_axis=0.0`、x 恒 100 而 y 283→342。⇒ 该测试**不会**在轴死掉时通过。**保留（见 DEF-1）**：③(a) 的第二半『断言轴值确实改变』（godot.rs:2148-2156 的 `INPUT_AXIS_NOT_CHANGED`）由我读代码确认存在，但**无任何测试覆盖**。"
    },
    {
      "id": "ITEM-3 Tester 证据形状（①）",
      "pass": true,
      "evidence": "(a) **首次尝试即下发形状**：`shape_context`/`first_attempt_context`（src/runtime/schema.rs:81-101）在 gate 的 attempt 1 就作为 `invocation.retry_context` 发出（schema.rs:259-263）；且 `src/harness/mini.rs:87-90` 把 `retry_context` 拼进模型真正收到的 `task_text`（`format!(\"{}\\n\\n---\\n\\n{}\", task_prompt, context)`）⇒ 不只是夹具字段。我的反例 C1（从 `EVIDENCE_SKELETON` 删掉两处 `\"claim_id\"`）使 `the_first_tester_attempt_is_told_the_evidence_record_shape` **红**，失败信息打印出 attempt 1 的完整形状块（含 `\"type\": \"screenshot|replay|…\"`、`execution_records`），证明形状确实在**第一次**尝试里。(b) **两个字段都在**：`EVIDENCE_SKELETON`（src/model.rs:449-478）含 `claim_id` 与执行记录的 `type`；`tester.md:53-99` 的输出契约含二者；`validate_evidence_shape`（src/model.rs:629-725）**一次列全**记录级 `claim_id/claim/execution_records/status` 与每条执行记录的 `type/observation`。(c) **可救的违约不被提前 break**：schema.rs:296 `if limits && (shape_retry_spent || !expected.is_file())`；我的反例 C2（还原为 `if limits`）使 `a_present_but_invalid_artifact_still_gets_one_shape_retry` **红**，失败串逐字为真机的 `schema failure for role Tester after 1 attempt(s)`。"
    },
    {
      "id": "ITEM-4 启动闸门（②）",
      "pass": true,
      "evidence": "`editor_error_is_stale`（godot.rs:3980-3996）只对『能定位 `res://file:line` + `Function \"X()\"` + 当前该行不含 X』判过期，其余 fail-closed；`partition_editor_errors`（:4003-4016）；闸门只用仍可复现的行决定 ok（:801-851）。**对真机那一行直接验证**：`runs/smoke-t8/versions/1f3d20ed…/scripts/player.gd` 第 31 行是 `_apply_facing_visual()`，全文 `_update_facing_visual` 命中 **0** ⇒ 该日志行判为过期。反例 D1（`editor_error_is_stale` 恒 false）使 `a_stale_editor_log_line_does_not_close_the_gate` **红**（`FakeHarness step #2 expects Tester but the runtime asked for Developer`，即日志残留又烧掉一次修复）。**反向控制同样成立**：反例 D2（恒 true）使 `a_reproducible_parse_error_still_closes_the_gate` **红** ⇒ 闸门不会退化成『永不关门』。两个测试在未植入时都绿（我的全量套件含二者 ok）。"
    },
    {
      "id": "ITEM-5 报告就地更正（③c）",
      "pass": true,
      "evidence": "`.spec/hof-rs/tasks/TASK-SMOKE-T8-REPORT.md` 在 `5baa801` 就地更正（`2c47727..5baa801`：+80/−7）。文件头 16-41 行是『⚠ 就地更正声明』索引 C1..C8，C1 的『原文字』列逐字引了旧旗舰论断 `move_left 被实测证否（左移不产生位移）`。**『被证否』→『not established』**：C1 + §0/§1.3/§2/§2.2/§2.3/§3.1/§5/§6.4/§10 各就地位置都有 `【DR-68 更正 Cn】`；§2.2 标题改为『是"没被证到"还是"被证否"』并写明『正确读法是 not established（未证到），不是 falsified（被证否）』。**缺失字段清单**：C2 与 §1.3 第 3 条均写明**同时缺 `type` 与 `claim_id`**。**验收点名的另外两处**：C3（『只有 `.workspace/mario/.hoh` 留证』改为『冻结的 `runs/smoke-t8/iter-1/candidate/.hoh/deterministic/**` 同样留证』）与 C4（`origin/master` 由 `079cf82` 更正为 `ce22e18`；我 `git rev-parse origin/master` = `ce22e181b1619c8fa5cf6adc670f7de48d2a3198`）。7 个被替换的行都保留了原句并追加标注（diff 的 7 条删除行逐条核对）。"
    },
    {
      "id": "ITEM-6 其余四项（⑤⑥⑦④）",
      "pass": true,
      "evidence": "⑤ 单花括号：`src/prompts/mod.rs:75/96/124` 与 `src/tools/index.rs:165-167` 的 `{{{{HOH_*}}}}` 在 `format!` 后成双花括号、可被 `render_command_vars` 解析；`contains_unresolved_command_var`（src/runtime/shell.rs:107-111）覆盖 `{{HOH_X}}` 与 `{HOH_X}` 两种；`assert_fully_rendered`（src/runtime/invoke.rs:178-193）新增该判据；我的反例 H（把 planner task 退回单花括号）使 `no_delivered_document_carries_an_unresolvable_command_placeholder` **红**（`[\"planner_task: {HOH_HOH_BIN}\"]`），并使旧的 `no_delivered_document_carries_an_unrendered_shell_placeholder` 同时红。⑥ 终止符：`planner.md:98`/`tester.md:150` 写明 `COMPLETE_TASK_AND_SUBMIT_FINAL_OUTPUT`；反例 G（删 tester.md 的终止符）使 `every_role_prompt_names_the_legal_completion_protocol` **红**；`only_a_first_line_completion_protocol_ends_a_role_call` 用真实 `LocalEnvironment` 执行，证明它是 mini 唯一合法出口（我全量套件里两测试都 ok）。⑦ 门状态：`ArtifactGate::not_applicable` 现在 `applicable=false, launchable=false`（src/model.rs:301-307）、`is_open() = applicable && launchable`（:314-316）、`status` 列对 `applicable=false` 打印 `unknown`（src/cli_impl.rs:853-869）；`failed_run_summary`（src/runtime/run_loop.rs:138-151）用 `not_applicable` ⇒ meta.json 不再报 launchable=true；反例 E（`is_open` 退回 `self.launchable`）使 `a_gate_that_did_not_apply_is_not_open` **红**（`applicability decides, even when launchable=true`）；端到端 `e1_increment.rs:307-321/371-375` 同时断言 `result.json` 与 `meta.json`。④ 失败路径：`FailureFacts`（run_loop.rs:288-296）在 Tester schema 失败点（run_loop.rs:1417-1421）与后冻结契约失败点（:1362-1366）写入真实 `candidate_id/version_id/battery_passes`；反例 F（退回 `FailureFacts::default()`）使 `a_failed_rounds_result_json_carries_the_real_battery_and_candidate` **红**，红输出正是 t8 存根 `\"battery_passes\":[],\"candidate_id\":null,\"version_id\":null`；未改代码时我另跑 `-- --nocapture` 得到报告 §5『修后』的同一行：`candidate_id=4f76c437c39720781c4d481fe13409baedfc17f4e49fbf2170b8c51ee0ab016d version_id=4f76c437…016d battery_passes=1 steps=10`。"
    },
    {
      "id": "ITEM-7 套件与门（§3）",
      "pass": true,
      "evidence": "先 `git ls-files '*.rs' | xargs touch`（**78 个已存在文件、无通配符**；施工后 `git ls-files build.rs` = 0）强制重编。仓库内 target：`cargo test --offline` ⇒ **EXIT=0，43 行 `test result` 汇总 414 passed / 0 failed / 7 ignored**（= 报告值）。**另跑仓外干净构建**：`CARGO_TARGET_DIR=%TEMP%\\dr68acc\\clean_target`、`CARGO_INCREMENTAL=0`，从零编译（169 行 `Compiling`）后同样 **EXIT=0 / 414 / 0 / 7** ⇒ **不存在陈旧产物**。`cargo fmt --check` ⇒ **exit 0**。测试未被删/放宽：`tests/` 下测试函数名集合在 `99c9fba`→`5baa801` **无删除**（522→547，25 个新增）；`#[ignore` 属性数两版均 **8**（运行期 ignored=7，未增长）。"
    },
    {
      "id": "ITEM-8 非空洞性（§2/§4 的 9 处植入）",
      "pass": true,
      "evidence": "报告的 P1..P9 目标文件全部是**生产代码**（`src/runtime/schema.rs`、`src/adapter/godot.rs`、`src/model.rs`、`src/runtime/run_loop.rs`、`src/prompts/tester.md`、`src/prompts/mod.rs`）；**无一处**落在测试里（其测试替身改动已在报告 §8.2 披露）。我**逐处重植并复现红**（见 §3）：P1↔C1、P2↔C2、P3↔A、P4↔B、P5↔D1、P6↔E、P7↔F、P8↔G、P9↔H，失败测试名与失败点（tests/schema_gate.rs:190/228、evidence_battery.rs:2818/2717/3239、common/mod.rs:270、result_semantics.rs:136、prompt_shell_contract.rs:375、role_shell_contract.rs:507）与实现者 `%TEMP%\\dr68\\plant\\P*-red.txt` **逐字一致**。**恢复证明**：实现者留在 `%TEMP%\\dr68\\plant\\` 的 6 个字节备份与当前工作树文件 `cmp` **全部 CMP_OK**（godot.rs/mod.rs/model.rs/run_loop.rs/schema.rs/tester.md）；我自己的 11 次植入也各自用**仓外备份 + `cmp` + `git status --porcelain` 空 + `git diff --stat` 空 + `git hash-object` == `HEAD:<file>`** 四重回退（§3）。⇒ 逐字节回退成立。"
    },
    {
      "id": "ITEM-9 守卫与基线（§3/§6/§1.8）",
      "pass": true,
      "evidence": "摘要口径（PowerShell 5.1 / zh-CN，仓根相对小写 POSIX 路径 + 字节长度 + 小写 sha256，`\\t` 连接、`\\n` 分行、无尾随换行，行序 **`Sort-Object`（文化排序）**，整体 UTF-8 取 sha256）**自证**：`runs/smoke-t6` = `c144ef3219e21dd322978e41a5531d53dee270619c026585505920f9277a9c03`（= 任务书自证值）。三基线现状：smoke-t6 135 文件/`c144ef32…7a9c03`；smoke-t7 115/`6e4c1595…20fb7`；smoke-t8 358/`6d11b2c6…bdf5a7`。**未写入 `runs/**`**：`runs/` 下**任何**文件/目录的最新 mtime 是 `2026-09-30 08:15:39`（`runs/smoke-t8-experiment/prompts`），**早于**本批首次提交（09:09:33）与我的会话；smoke-t6/7/8 三棵树最新 mtime 分别是 09-29 02:32:01 / 09-29 14:41:14（t7 的 `iter-1/traj` 目录为 09-30 06:56:47——上一轮写后删的**历史**违反，摘要已复原）/ 09-30 07:58:28；`runs/smoke-t7` 下 `*analysis*` 命中 0。`.workspace/mario` **工程树**（排除 `.godot/.import/.hoh/.git`）用我自实现的 `hash_tree` 重算 = `1f3d20ed…` = 候选树 = 存储 `A_1`（17 文件/18397 B），`A_0` = `fc78d299…`（17/16113 B）；`PRD-mario.md` sha256 `4c81c3a9…5c3a` 未变；`Cargo.toml/Cargo.lock` 在 `99c9fba..5baa801` **零 diff**；`git diff --cached --stat` 空；**嵌套**引擎仓 `git -C godot-mcp/godot` HEAD `fc63af77…`、`status --porcelain -uall` 0 行；外层 `git ls-files godot-mcp` = 6484（真命中）而 `godot-mcp/godot` = 0；仓内无临时物（`git status --porcelain -uall` 空，仓内 08:44 后新文件只有本批产物、报告、`DECISIONS.md` 与 3 个 `.godot` 缓存）。**三个假绿陷阱我自己复现**：① `git diff --stat -- definitely/not/a/real/path` → 空 + exit 0；② bash `git cat-file -e ef74c60^:<path>` → **128**、`ef74c60:<path>` → **0**，cmd 同一 `^` 查询 → **0**（`^` 被 cmd 吃掉）；③ 外层仓不跟踪引擎树（`git ls-files godot-mcp/godot` = 0，`git check-ignore -v godot-mcp/godot/bin` → `.gitignore:33`），③′ `runs/**` 亦被 `.gitignore:12:runs/` 排除 ⇒ 外层 `git status/diff` 对它们都是空判。"
    }
  ],
  "defects": [
    {
      "id": "DEF-1",
      "severity": "medium",
      "what": "③(a) 的第二半『回放后断言轴值确实改变』**没有任何测试覆盖**。生产代码 `INPUT_AXIS_NOT_CHANGED`（src/adapter/godot.rs:2148-2156）确实存在，`tests/` 里对 `INPUT_AXIS_NOT_CHANGED` 的引用 **0 处**；我把该分支整段删掉，41 个 `evidence_battery` 测试**全部通过**（exit 0）。⇒ 该断言目前是**未被测试钉住**的代码：未来的回归不会被任何测试发现，报告 §3 ③ 的 TDD 绿只覆盖了『释放』那一半。",
      "reproduction": "`git grep -n INPUT_AXIS_NOT_CHANGED -- src tests` ⇒ 仅 `src/adapter/godot.rs:2152`；我把它替换为 `let _ = expected_axis_sign(action);`（plants.py 键 `I`）后 `cargo test --offline --test evidence_battery` ⇒ `41 passed; 0 failed`；随后从仓外备份 `cmp` 还原（CMP_OK / status 空 / diff 空 / hash == HEAD）。"
    },
    {
      "id": "DEF-2",
      "severity": "minor",
      "what": "`TASK-DR68-REPORT.md` §5 写『被 schema gate 拒绝（`max_schema_retries = 0`，一次尝试）』——**值错了**。真机轮自己的配置是 **`max_schema_retries: 2`**（`runs/smoke-t8/iter-1/traj/developer.attempt1.json` 里开发者当时跑 `hoh doctor` 打印的配置块，与 `config/hoh.yaml:24` 一致）；『只有 1 次尝试』的正因是 attempt1 `LimitsExceeded` 撞上 `if limits { break; }`，不是重试预算为 0。机制结论不变（而且该修复因此**更**承重：预算本是 2，重试是被 break 吃掉的）。",
      "reproduction": "`grep -rn 'max_schema_retries' runs/smoke-t8/` ⇒ 只有 `traj/developer.attempt1.json` 里的 `max_schema_retries: 2`；`config/hoh.yaml:24` 同为 2；`.spec/hof-rs/tasks/TASK-SMOKE-T8.md` 无 CLI 覆盖。"
    },
    {
      "id": "DEF-3",
      "severity": "info",
      "what": "报告头部『⚠ 就地更正声明』写『本文件的原始文字一字未删』；字面上 `2c47727..5baa801` 对 `TASK-SMOKE-T8-REPORT.md` 有 **7 条删除行**（E1/E2/E3 行、§1.3 小结句、`move_left` 表行、`repair_retry_used` 行、`origin/master` 行），是**就地替换**。语义上成立（每个替换行都保留原句并追加 `【DR-68 更正 Cn】`，且 C1 的『原文字』列逐字引了旗舰论断），但『一字未删』的**字面**口径与 diff 不符。",
      "reproduction": "`git diff 2c47727 5baa801 -- .spec/hof-rs/tasks/TASK-SMOKE-T8-REPORT.md | grep -c '^-[^-]'` ⇒ 7，且 7 行的原文都能在新行里逐字找到。"
    },
    {
      "id": "DEF-4",
      "severity": "info",
      "what": "`ArtifactGate::is_open()` 的 `applicable` 修复仍**没有生产调用方**（`git grep 'is_open()'` 只在 `src/model.rs` 定义与 `tests/result_semantics.rs` 使用）。失败轮的不再假绿实际由字段值（`not_applicable` → `launchable=false`）、`status` 列与 `result.json`/`meta.json` 承担；`is_open()` 只是把『未来读者』的正确性备好。",
      "reproduction": "`git grep -n 'is_open()' -- src tests` ⇒ `src/model.rs:314`（定义）+ `tests/result_semantics.rs:125/137/143/144`。"
    },
    {
      "id": "DEF-5",
      "severity": "info",
      "what": "调度者台账 `DECISIONS.md` D267 把 `runs/smoke-t8` 的摘要尾串写成 `…ff5a7`；真值是 `6d11b2c61ec507b5f02525ddc0e7f7adb08763cd2439a4b08788b7fe51bdf5a7`（尾 `…bdf5a7`）。仅台账排版笔误，不影响判定（我不修改 `DECISIONS.md`）。",
      "reproduction": "`DECISIONS.md:10313` 对比我的 `digest.ps1 runs/smoke-t8`；t6/t7 两串该行与我的重算逐字相同。"
    },
    {
      "id": "DEF-6",
      "severity": "info",
      "what": "`.workspace/mario/.godot/editor/{editor_layout,script_editor_cache,shader_editor_cache}.cfg` 在我验收期间被 **2026-09-30 09:55:09** 重写（进程表里 `godot.windows.editor.x86_64.mono` pid **75204** 存活）。这是**活的 Godot 编辑器自己**写的编辑器缓存，不是实现者、也不是我；`.godot` 属于 `hash_tree` 排除集，**工程树 17 文件仍 = `1f3d20ed…`**。⇒『`.workspace/mario/**` 未改』只能按**工程树**口径说；整目录摘要天然不稳定（与上一轮验收 R4 同因）。",
      "reproduction": "`find .workspace/mario -type f -newermt '2026-09-30 08:44'` ⇒ 恰好这 3 个 `.cfg`；`python hashtree.py .workspace/mario` ⇒ 17 文件/18397 B/`1f3d20ed…`；`tasklist` ⇒ pid 75204。"
    }
  ],
  "risks": [
    "R-1 真机未验证：`semantic_release_action` 发的 `{\"type\":\"action\",\"pressed\":false}` 是否被引擎的 `running_game_play_input_recording` 接受，本批**只在夹具里**验证（夹具把引擎建模成『收到 release 就释放』）。真机若拒绝，观察文字会写 `accepted=false` 且轴值断言会兜底，但『左移是否有效』仍未被证——E1/E3 仍只能由真机判定（报告 R1/R2 已如实标注）。",
    "R-2 轴值断言在真机大概率不触发：t8 的 `input_axis` 每次都是 `null`（DR-58），所以 ③(a) 的 `INPUT_AXIS_NOT_CHANGED` 在真机上很少有机会说话；真机承重的是按目标轴的**位置**断言（这一点是实测）。叠加 DEF-1（该断言无测试），『断言轴值改变』的净保障比报告读起来弱。",
    "R-3 过期日志规则**故意很窄**：只处理 `… res://<file>:<line> … Function \"X()\" not found in base self.`；其它陈旧形态一律 fail-closed（仍会关门、仍可能烧修复）。这是设计取舍（报告 R4），但下一轮若出现另一种陈旧形状，会重演 F1 的浪费。",
    "R-4 失败路径仍不完整：`evidence_diff` 在 Tester schema 失败时仍是 `{added:[],modified:[],removed:[]}`（报告 R7 已披露，超出本批范围）；读 `result.json` 现在能知道**身份与电池**，但仍不知道**改了什么**。",
    "R-5 共享测试替身被改：`tests/evidence_battery.rs` 的 `FixtureChannel` 由单个 `bool` 改成 held-action 集合 + 按轴位移（报告 §8.2 披露）。我用『归一化断言集合比对』证明 `tests/**` 在本批前后**没有删改任何 `assert!`/`assert_eq!`/`assert_ne!`**（7 个文件只有新增），但没有逐句证明夹具改造对所有既有用例**行为等价**（夹具改动在方向上是收紧的，且 41/41 通过）。",
    "R-6 `cargo fmt` 规范化是一次 30 文件/+728−331 的**非任务书点名**改动（`d482794`）。`cargo fmt --check` 现在 exit 0、无断言改动、全套件绿；但 rustfmt 会增删尾逗号，我**没有**逐 hunk 证明它是纯格式（按构造应如此）。",
    "R-7 `runs/**` 证据不入 git：三条基线现在有摘要（我复算一致），但摘要只活在本报告与工作树；一轮清理即可让证据消失（上一轮验收 R6 同忧）。",
    "R-8 本批**未**处理风险旗 1（`godot.rs` 的 `GAME_INPUT_CHANNEL_OK` 判定与其文档注释矛盾，`axis_before=axis_after=null` 仍可单独抬到 OK）——报告 R8 如实保留，我未复核该判定，也未用它做任何证据。"
  ],
  "unverified": [
    "U1 我没有亲眼看到实现者**执行回退**的过程；我验证的是**终态**：其仓外备份与当前工作树 6 文件 `cmp` 全部相同 + 6 文件 `git hash-object == HEAD:<file>` + 我自己 11 次植入的回退四件套。『他们回退的那一刻逐字节相同』是由终态与备份的字节比较推得的。",
    "U2 我没有在 `99c9fba` 上跑基线以复算 `397`（或 `baseline_count.txt` 的 `399`）。我能证的是 `99c9fba..5baa801` 无测试删除、`#[ignore` 数不变，以及 HEAD 上 414/0/7 exit 0 ≥ 397。",
    "U3 `runs/smoke-t8-experiment/**` 我只做摘要/mtime 级核查（未变），未逐帧重算其 e3 实验。",
    "U4 我没有联网、没有调模型端点、没有启动 Godot、没有跑真机轮，因此『首次给形状后模型能否提交合法 `E_1`』『引擎是否接受 release 事件』『E1/E3 是否 met』全部**未验证**（属真机范畴）。",
    "U5 `%TEMP%\\dr68\\base\\src` 与 `99c9fba` 的 6 个文件不一致（errors.rs/model.rs/bridge.rs/endpoint.rs/mod.rs/reliable.rs），像是 09:06 的**工作中副本**而非干净基线；报告没有引用它做任何断言，我也未据此下结论。",
    "U6 我没有审计 `tests/common/mod.rs` 里 `FakeHarness` 的全部改动语义；只证了断言集合未减、套件全绿。"
  ]
}
```

---

## 1. 逐项判定表（八项要求）

| 项 | 要求（TASK-DR68） | 我的判定 | 关键证据（自产） |
|---|---|---|---|
| ① | Tester 证据形状：首次即下发 + 可救的违约不提前 break + 提示词写明 | **通过** | schema.rs:81-101/259-263/296；mini.rs:87-90；model.rs:449-478/629-725；tester.md:53-99；反例 C1/C2 红 |
| ② | 闸门不被过期日志关门；**且**真实当前错误仍关门 | **通过** | godot.rs:3980-4016/801-851；真机 `player.gd:31` = `_apply_facing_visual()`（`_update_facing_visual` 命中 0）；反例 D1/D2 各红一边 |
| ③ | (a) 游戏进程内释放上一输入 + 断言轴值改变；(b) 按目标轴判位移；(c) 报告就地更正 | **通过**（含 DEF-1） | godot.rs:1770-1780/1960-1968/2085/2148-2156/2791-2801；反例 A/B；报告 §5 更正索引；**但**轴值断言无测试（DEF-1） |
| ⑧ | 目标轴零位移、另一轴有位移 ⇒ 判未移动 | **通过** | `movement_on_intended_axis`；反例 A：整向量版把 `x` 死/`y` 动判成移动（红），现行版判未移动（测试绿） |
| ④ | 失败路径写真实 battery/candidate/version | **通过** | run_loop.rs:288-296/1417-1421/1362-1366；反例 F 红出 t8 存根；未改代码时 `--nocapture` 得到 `4f76c437…016d` / `battery_passes=1 steps=10` |
| ⑤ | 单花括号占位符修掉 + 完整性断言覆盖两种形态 | **通过** | prompts/mod.rs:75/96/124；tools/index.rs:165-167；shell.rs:107-111；invoke.rs:178-193；反例 H 红两个测试 |
| ⑥ | planner/tester 提示词写明合法终止符 | **通过** | planner.md:98；tester.md:150；反例 G 红；`only_a_first_line_completion_protocol_ends_a_role_call` 用真实 `LocalEnvironment` 执行并通过 |
| ⑦ | 失败轮门状态自洽；`is_open()` 考虑 `applicable` | **通过**（DEF-4） | model.rs:301-316；cli_impl.rs:853-869；run_loop.rs:138-151；反例 E 红；e1_increment 端到端断言 result.json 与 meta.json |
| 报告更正 | 就地更正、旧文字保留并标注；『被证否』→『未证到』；缺失字段清单；另两处不准确 | **通过**（DEF-3 字面口径） | C1..C8 索引；7 条替换行保留原句；C2 两字段；C3/C4 |
| 门 | `cargo test --offline` exit 0 ≥397/0/7；`fmt --check`；无测试删/放宽 | **通过** | 仓内 target：**414/0/7 exit 0**；仓外干净 target（增量 0、169 次 Compiling）：**414/0/7 exit 0**；`cargo fmt --check` exit 0；测试函数名集合无删除；`#[ignore` 恒 8 |
| 非空洞性 | ≥4 处仅生产代码植入，各自红、逐字节回退 | **通过** | 9 处全在 `src/**`；我逐处重植复现红（失败点与实现者 P*-red.txt 逐字一致）；其备份 6 文件 `cmp` CMP_OK；我的 11 次植入四件套回退 |
| 守卫 | `runs/**` 逐字节未动（三基线）、mario/PRD/无依赖/未 stage/引擎嵌套仓/无临时物、三陷阱 | **通过** | 三基线摘要 `c144ef32…`/`6e4c1595…`/`6d11b2c6…` 与记录一致；`runs/` 最新 mtime 08:15:39 < 首次提交 09:09:33；mario 工程树 `1f3d20ed…`；PRD sha；Cargo 零 diff；嵌套仓干净；三陷阱复现 |

---

## 2. 头号问题的独立判断

### 2.1 掩蔽假绿（头号）——**已修，且我用自己的反例钉住了它**
`movement_on_intended_axis` 只比较 `intended_axis(action)` 这一轴的分量，`move_left/move_right→x`、`jump→y`，`delta != 0.0`。我把判据还原成整向量后，目标测试红；红输出里的四元组正是掩蔽形态（`x` 前后同为 60.0、`y` 283→342，`axis=x delta=0.000000`）。**目标轴不变而另一轴变 ⇒ 判为未移动**，这一点由现行代码的测试绿与该反例红两面夹住。

### 2.2 输入回放——**释放确实在游戏进程内；轴值断言存在但未被测试钉住**
释放与按下走**同一个** `self.call(\"running_game_play_input_recording\")`（前者 `pressed:false`、后者 `pressed:true`），前缀路由把它们都送进游戏端点；这是**结构性**结论，不是夹具自证。测试 `the_input_replay_releases_…` 不仅断言『存在带 `pressed:false` 的 release』与『release 早于 move_left press』，还断言 `move_left` 的 `x` 真的变小——而夹具把 `x` 的移动绑在 `Input.get_axis` 上（两向同时按住 ⇒ 0 ⇒ x 钉死），所以**该测试不会在轴死掉时通过**；反例 B 正是这样把它变红的。
**但**：(i) 该测试不能证明**真引擎**会应用 `pressed:false`（夹具假设了它；报告 R2 已承认）；(ii) 生产代码里那条 `INPUT_AXIS_NOT_CHANGED` 断言**没有任何测试**——删掉它，41 个电池测试全绿（DEF-1）。真机上 `input_axis` 恒 `null`（DR-58），承重的其实是按轴的位置断言。

### 2.3 Tester schema 路径——**首次即达模型；两个字段都在；可救违约确实能拿到一次重试**
- **首次**：attempt 1 的 `retry_context` 就是 shape 块（反例 C1 的失败信息把它整块打了出来），且 `mini.rs` 把它拼进模型收到的 task 文本 ⇒ 不是只在夹具里的假象。
- **两个字段**：`EVIDENCE_SKELETON` 与 `tester.md` 都写出 `claim_id` 与执行记录的 `type`；`validate_evidence_shape` 记录级检查会在一次错误里列全。
- **不被提前 break**：反例 C2 把条件退回 `if limits`，目标测试立刻红出真机原话 `schema failure for role Tester after 1 attempt(s)`。
- 另：报告 §5『(max_schema_retries = 0)』失实（真值 2，见 DEF-2），但这只**加强**了该重试修复的意义。

### 2.4 启动闸门——**过期日志不再关门；真实错误仍然关门**
正反两面都有独立测试：`a_stale_editor_log_line_does_not_close_the_gate`（用 t8 的那一行原文）与 `a_reproducible_parse_error_still_closes_the_gate`（同名符号仍在第 31 行，必须关门并消耗那一次定向修复）。我的 D1/D2 两个反例分别把两边变红，证明这对测试**不是**同义反复。**额外**：我拿真机 `A_1` 的 `player.gd` 字节直接核对——第 31 行是 `_apply_facing_visual()`，全文 `_update_facing_visual` 命中 0 ⇒ 现行规则对真机那一行判过期。

### 2.5 报告更正——**成立**（旧文字保留 + 标注；四点都改到）
`TASK-SMOKE-T8-REPORT.md` 头部有 C1..C8 索引；『左移被实测证否』在原位被标注为 **not established / 注入时序假象**；缺失字段清单改为 **`type` + `claim_id`**；『只有 workspace 留证』更正为『冻结的 run 目录同样留证』；`origin/master` 由 `079cf82` 更正为 `ce22e18`（我已 `git rev-parse` 复核）。唯一保留是字面口径（DEF-3）。

---

## 3. 我自己的植入与反例（11 处，全部生产代码，全部四件套回退）

口径：`cargo test --offline --test <target> <filter>`；每处植入前把文件复制到 `%TEMP%\dr68acc\backup\`，植入后跑测试，随后 `cp` 回退并验
`cmp`（对备份）+ `git status --porcelain` 空 + `git diff --stat` 空 + `git hash-object` == `git rev-parse HEAD:<file>`。

| # | 文件 | 植入（还原旧行为） | 目标测试 | 结果 |
|---|---|---|---|---|
| A | src/adapter/godot.rs | `moved: quadruple[before]!=quadruple[after]`（整向量） | `a_dead_target_axis_is_not_movement_even_when_the_other_axis_moves` | **红**：`a dead \`x\` axis is not movement…: … axis=x delta=0.000000` |
| B | src/adapter/godot.rs | 释放循环换成 `held_in_game.clear()` | `the_input_replay_releases_the_previous_direction_before_the_next_one` | **红**：`DR-68 ③(a): the replay must release the previous input inside the game`（红输出内 `observed_axis=0.0`、x 恒 100、y 283→342） |
| C1 | src/model.rs | 从 `EVIDENCE_SKELETON` 删掉两处 `claim_id` | `the_first_tester_attempt_is_told_the_evidence_record_shape` | **红**：`the first attempt must already carry \`claim_id\`…`（并把 attempt1 形状块整块打印） |
| C2 | src/runtime/schema.rs | `if limits && (shape_retry_spent \|\| !expected.is_file())` → `if limits` | `a_present_but_invalid_artifact_still_gets_one_shape_retry` | **红**：`schema failure for role Tester after 1 attempt(s)` |
| D1 | src/adapter/godot.rs | `editor_error_is_stale` 末尾恒 `false` | `a_stale_editor_log_line_does_not_close_the_gate` | **红**：`FakeHarness step #2 expects Tester but the runtime asked for Developer` |
| D2 | src/adapter/godot.rs | `editor_error_is_stale` 末尾恒 `true` | `a_reproducible_parse_error_still_closes_the_gate` | **红**：同一 FakeHarness 断言（**反向控制**：闸门不允许被放宽成永不关门） |
| E | src/model.rs | `is_open()` 退回 `self.launchable` | `a_gate_that_did_not_apply_is_not_open` | **红**：`applicability decides, even when launchable=true` |
| F | src/runtime/run_loop.rs | Tester schema 失败点传 `FailureFacts::default()` | `a_failed_rounds_result_json_carries_the_real_battery_and_candidate` | **红**：`candidate_id must be the real A_1, not null: {…\"battery_passes\":[],\"candidate_id\":null,\"version_id\":null}` |
| G | src/prompts/tester.md | 删掉 `COMPLETE_TASK_AND_SUBMIT_FINAL_OUTPUT` | `every_role_prompt_names_the_legal_completion_protocol` | **红**：`tester.md does not name the only legal completion protocol` |
| H | src/prompts/mod.rs | planner task 退回单花括号 `{{HOH_HOH_BIN}}` | `no_delivered_document_carries_an_unresolvable_command_placeholder` | **红**：`[\"planner_task: {HOH_HOH_BIN}\"]`（旧测试 `…unrendered_shell_placeholder` 同红） |
| I | src/adapter/godot.rs | 删掉 `INPUT_AXIS_NOT_CHANGED` 分支 | `--test evidence_battery`（全 41 个） | **全绿** ⇒ 该断言无覆盖（DEF-1） |

回退证明（每个都实测；`src/adapter/godot.rs` 的 blob `cbcf11ab…`、`src/model.rs` `e0ebea41…`、`src/runtime/schema.rs` `ebf05c79…`、`src/runtime/run_loop.rs` `01e08d3c…`、`src/prompts/tester.md` `c7a10e2f…`、`src/prompts/mod.rs` `4b36486d…` 与报告 §4 表逐字相同）：

```
A/B/D1/D2/I  src/adapter/godot.rs     CMP_OK ; status=<空> ; diffstat=<空> ; hash=cbcf11abbcb4ddd355f3f80edcd7efc0ea6342ea == HEAD
C1/E         src/model.rs             CMP_OK ; status=<空> ; diffstat=<空> ; hash=e0ebea4190d3af0b611f1427f0694adb8e571fa7 == HEAD
C2           src/runtime/schema.rs    CMP_OK ; status=<空> ; diffstat=<空> ; hash=ebf05c797a645aaaf5ac53fc6c6498b5e9f54041 == HEAD
F            src/runtime/run_loop.rs  CMP_OK ; status=<空> ; diffstat=<空> ; hash=01e08d3c123618e8051e6be095367a11a2783ece == HEAD
G            src/prompts/tester.md    CMP_OK ; status=<空> ; diffstat=<空> ; hash=c7a10e2f1728df523fa9d83b8a57f11bf8d01a7e == HEAD
H            src/prompts/mod.rs       CMP_OK ; status=<空> ; diffstat=<空> ; hash=4b36486d2562d32a2047d97e4f8b1c6ce6c3c18e == HEAD
```

**该批 9 处植入的位置核查**：P1/P2=`src/runtime/schema.rs`，P3/P4/P5=`src/adapter/godot.rs`，P6=`src/model.rs`，P7=`src/runtime/run_loop.rs`，P8=`src/prompts/tester.md`，P9=`src/prompts/mod.rs` —— **全部生产代码，无一在测试**；其测试替身改动（`tests/evidence_battery.rs` 的 `FixtureChannel`）已在报告 §8.2 显式披露，故不需要 D253『植入在承载不变量的测试里』的额外说明。其仓外备份与当前文件 6/6 `cmp` 相同。

---

## 4. 套件与门（真实输出）

```
$ git ls-files '*.rs' | wc -l              -> 78
$ git ls-files '*.rs' | xargs touch        -> TOUCH_OK   # 只 touch 已存在文件
$ cargo test --offline ; echo EXIT=$?      -> EXIT=0
$ awk '/^test result/{p+=4;f+=6;i+=8} …'   -> passed=414 failed=0 ignored=7 (43 行 test result)
$ cargo fmt --check ; echo FMT_EXIT=$?     -> FMT_EXIT=0

$ CARGO_TARGET_DIR=%TEMP%\dr68acc\clean_target CARGO_INCREMENTAL=0 cargo test --offline
   -> 169 行 Compiling（从零编依赖+lib+测试）; EXIT=0 ; passed=414 failed=0 ignored=7
```

- `touch` 输入全部来自 `git ls-files`，**无通配符**；施工后 `git ls-files build.rs` = 0、`git status --porcelain -uall` 空。
- **无既有测试被删**：`tests/*.rs` 的函数名集合 `99c9fba`→`5baa801` 无删除（522→547）；`#[ignore` 属性两版均 8；运行期 ignored=7 未增长。
- **无既有断言被删/改**：我用 `assertdiff.py` 抽取每个测试文件的 `assert!/assert_eq!/assert_ne!` 调用、归一化空白后做集合差：**只有新增、零删除**（7 个文件受影响）。
- 仓外干净重编**独立复现 414/0/7** ⇒ 排除陈旧产物。

---

## 5. 守卫与基线（摘要口径与自证）

摘要口径（PowerShell 5.1 / culture zh-CN；`Get-ChildItem -Recurse -Force -File`；**仓根相对**小写 POSIX 路径 + 字节长度 + 小写 sha256；`\t` 连接、`\n` 分行、无尾随换行；行序 **`Sort-Object`（文化排序）**；整体 UTF-8 取 sha256）：

```
runs/smoke-t6  files=135 newest=2026-09-29 02:32:01  c144ef3219e21dd322978e41a5531d53dee270619c026585505920f9277a9c03   <== 自证 MATCH
runs/smoke-t7  files=115 newest=2026-09-29 14:41:14  6e4c1595753c2cdefb16e4d2e5f05242ca202c70c81a93e98ae2b9c92b520fb7
runs/smoke-t8  files=358 newest=2026-09-30 07:58:28  6d11b2c61ec507b5f02525ddc0e7f7adb08763cd2439a4b08788b7fe51bdf5a7
```

- **文化排序确是口径的一部分（我实测）**：换成序数排序（`StringComparer::Ordinal`）后 `runs/smoke-t8` 变为 `c347bd63…`，而 `runs/smoke-t6` **仍** `c144ef32…` ⇒ 分歧只在含 `_`/数字相邻项的树上出现，不具普遍性（与上一轮验收一致）。
- **『写过再删』检查**：`runs/` 下**目录**的最新 mtime 是 `runs/smoke-t8-experiment/prompts` = `2026-09-30 08:15:39`，`runs/` 下**文件**没有晚于 `08:20` 的。三棵基线树里唯一的『晚点』是 `runs/smoke-t7/iter-1/traj` 目录 = `2026-09-30 06:56:47`——即上一轮**已披露的**写后删（3 个 `*.analysis.json`）；该目录 `*analysis*` 命中 0，且 t7 摘要等于历史基线 ⇒ 内容确已复原。**本批（08:44 起）与我（09:5x 起）都没有任何 `runs/**` 写入**（我连临时文件都没建在那里；分析脚本全在 `%TEMP%\dr68acc\`）。
- 其余守卫：`PRD-mario.md` sha256 `4c81c3a9…5c3a`；`Cargo.toml/Cargo.lock` 零 diff；`git diff --cached --stat` 空；`origin/master` = `ce22e18…`（未 push，ahead 17）；嵌套引擎仓 `fc63af77…` + `status -uall` 0 行、`ls-files` 15049；外层 `git ls-files godot-mcp`=6484 而 `godot-mcp/godot`=0；仓内无临时物；`%DST%` 是 09-24 的历史异物（未动）。
- **`.workspace/mario`**：工程树（排除 `.godot/.import/.hoh/.git`）17 文件/18397 B/`1f3d20ed…` = `A_1` = 候选树；只有 3 个 `.godot` 编辑器缓存被**存活的编辑器进程**（pid 75204）在 09:55:09 重写（DEF-6）。

---

## 6. 我没查的 / 做不到的

- 未联网、未调模型端点、未启动 Godot、未探端点、未跑真机轮（真机判定不在本验收权限内）。
- 未审计 `runs/smoke-t8/iter-1/traj/**` 的全部约 3.3 MB 轨迹；只按需检索 schema 错误、配置块、坐标回包。
- 未在 `99c9fba` 上跑基线套件（只证测试集合不缩、ignore 数不变、HEAD ≥ 397）。
- 未逐 hunk 证明 `d482794` 是纯格式（只证 `fmt --check` 干净、断言集合不缩、全套件绿）。
- 未逐句证明 `FixtureChannel` 改造对所有既有用例行为等价（只证断言集合不减 + 41/41 通过）。
- 未复核风险旗 1（`GAME_INPUT_CHANNEL_OK` 判定与文档矛盾）与 `runs/smoke-t8-experiment/**` 的内容细节。

---

## 7. 对下一批的建议

1. **给 ③(a) 的轴值断言补一个红测试**（DEF-1）：构造『release 被接受但轴读数仍为 0（或符号不对）』的夹具场景，断言步骤 `ok=false` 且观察里出现 `INPUT_AXIS_NOT_CHANGED`。否则这条断言会在未来任何重构里静默消失。
2. **真机验证 release 事件形状**（R-1）：优先用一条短夹具/半真机路径确认 `running_game_play_input_recording` 接受 `{\"type\":\"action\",\"pressed\":false}`；若引擎拒绝，观察里的 `accepted=false` 与轴断言就是唯一兜底。
3. **把过期规则扩成一张表**（R-3）：现在只覆盖 `Function \"X()\" not found in base self.`；下一轮若出现另一种陈旧形状，应按『错误来源文件 + 行号 + 符号一致性』推广，而不是放宽整体。
4. **补失败路径的 `evidence_diff`**（R-4）：`FailureFacts` 已经把身份与电池带进失败存根，`evidence_diff` 是同类问题的最后一块。
5. **台账口径**：凡引用 `.workspace/mario` 摘要必须注明『t8 前/后』（D267 已定）；D267 里 `runs/smoke-t8` 的摘要尾串 `…ff5a7` 建议改成 `…bdf5a7`（DEF-5）。报告 §5 的 `max_schema_retries = 0` 建议改成 **2**（DEF-2）。
6. **真机重跑前先落一条 E1 类『零增量』路径的红证据**：本批与本轮都还是 schema 类失败，`NoEngineeringWrite` 契约类 2 仍未在真机走到。

---

## 8. 结论一句话

**TASK-DR68 的八项要求全部落地，并由我独立复现：仓内与仓外干净 target 各得 `414/0/7 exit 0`、`cargo fmt --check` exit 0、11 处自植反例各自红且逐字节回退、三条 `runs/**` 基线摘要与记录一致且本批零写入、三个假绿陷阱全部复现；唯一实质缺陷是 ③(a)『断言轴值改变』的代码无任何测试覆盖（删掉它 41 个电池测试仍全绿），另有三处 minor/信息级不准确。E1/E3 是否 met 仍需真机，本批正确地把这一裁决留给了真机。**
