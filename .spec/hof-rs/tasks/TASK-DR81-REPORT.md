# TASK-DR81-REPORT — 修复两处只有真机能暴露的产品缺陷：门的「编辑器基础设施失败 vs 工程缺陷」判定分离（含时间窗信号）；`secrets.rs` 赋值扫描的 span/overlap 吞并；并补越界清理模式与「标记来源必须是验收件」的闸门约束

- 实现子代理（无上游对话上下文；本文件是唯一任务来源 `F:\moonbit-hof-rs\.spec\hof-rs\tasks\TASK-DR81.md`）
- 规格来源：`TASK-SMOKE-T14-REPORT.md`（F-T14-1..F-T14-4 与原始证据）与其独立验收 `TASK-SMOKE-T14-ACCEPTANCE.md`（**T14A-1 / R5 / R6 / H8** 与建议 1/2/7），`DECISIONS.md` **D289 / D293**
- 批次性质：**离线批次**。未启动引擎、未跑任何真机轮、**未联网**；未推送
- HEAD（开工 = 收工）= `e7480b3`；`origin/master` 仍为 `03ee2e3b4a2c1ef4536ec0108afec2741ce7581a`（**与开工前逐字相同，未推送**）
- 落点：`F:\moonbit-hof-rs`；报告：`.spec/hof-rs/tasks/TASK-DR81-REPORT.md`

---

## 0. 机器可读判定（`json.dumps(..., ensure_ascii=False, indent=2)` 生成，落盘后按行锚定栅栏 `json.loads` 回读）

```json
{
  "task": "TASK-DR81",
  "kind": "implementation subagent report (offline batch: no engine, no real round, no network, no push)",
  "head": "e7480b3",
  "origin_master": "03ee2e3b4a2c1ef4536ec0108afec2741ce7581a",
  "pushed": false,
  "baseline": {
    "passed": 560,
    "failed": 0,
    "ignored": 7,
    "listed": 567,
    "exit": 0,
    "reproduced_by_me": true
  },
  "gate": {
    "passed": 575,
    "failed": 0,
    "ignored": 7,
    "listed": 582,
    "exit": 0,
    "fmt_exit": 0,
    "fingerprints_removed_with_python_glob_rmtree": 61,
    "tracked_rs_files_touched_individually": 97,
    "forced_compile_line": "Compiling hof-rs v0.1.0 (F:\\moonbit-hof-rs)",
    "tests_removed": 0,
    "new_tests": 15,
    "ignored_names_unchanged": [
      "e0_initialize_workspace",
      "e1_single_iteration_smoke",
      "e2_project_boots",
      "e3_behaviour_is_evidenced",
      "e4_verified_claims_are_reproducible",
      "e5_qa_did_not_modify_the_artifact",
      "e6_report_is_honest"
    ]
  },
  "items": {
    "item1_gate_can_separate_infrastructure_from_project": {
      "mechanism": "editor_error_is_infrastructure(line) is true only when the line names the editor cache namespace `res://.godot/` AND carries one of the named cache/write-failure phrases; the exemption is additive and runs after DR-48 banners and DR-68 staleness, before the window test",
      "infrastructure_does_not_close": "tests/launchable_gate.rs::an_editor_infrastructure_failure_does_not_close_the_gate",
      "real_script_error_still_closes": "tests/launchable_gate.rs::an_infrastructure_failure_does_not_mask_a_real_script_error plus the pre-existing DR-48 counters (a_real_editor_error_still_closes_the_gate, an_error_carrying_the_mcp_prefix_still_closes_the_gate, an_unknown_mcp_prefixed_line_still_closes_the_gate) and DR-68's a_reproducible_parse_error_still_closes_the_gate",
      "recorded_tokens": "editor_infrastructure_failures=N, project_defects_new=N in the observation; raw/editor_errors_baseline.json.channel.editor_error_window carries the window and counts"
    },
    "item2_windowed_editor_error_signal": {
      "criterion": "an editor log line closes the gate only when it is not an exact DR-48 banner, not stale by DR-68, not editor infrastructure by DR-81 1, and its occurrence count grew between the pre-reload anchor reading and the judged reading",
      "anchor": "editor_get_errors with max_lines=2000, taken immediately before project_reload_and_open",
      "judged": "editor_get_errors with max_lines=50, taken after the reload",
      "old_tail_error_does_not_close": "tests/launchable_gate.rs::an_old_editor_log_line_outside_the_window_does_not_close_the_gate",
      "new_error_still_closes": "tests/launchable_gate.rs::a_real_script_error_new_in_the_window_still_closes_the_gate",
      "fail_closed": "a failed anchor, or a payload without an errors array, leaves the anchor absent and every judged line counts as new"
    },
    "item3_assignment_scan_overlap": {
      "root_cause": "src/runtime/secrets.rs:324 guarded with `start < span.end` (a global `begins before the largest end seen so far` test) instead of a real interval overlap; because OPENAI_API_KEY is scanned before the HOH_*/DSH_TERM_CMD/PATH family, one late OPENAI_API_KEY occurrence (286080-286095) blocked every earlier occurrence of every later-scanned name",
      "fix": "real interval intersection `start < span.end && span.start < value_end`, plus containment absorption: a candidate that contains a recorded span replaces it (so a DSH_TERM_CMD line carrying an HOH_ROLE=value argument cannot leave a raw tail), while a candidate inside a recorded span keeps the earlier span (the shape the frozen DR-72 sample pins)",
      "real_entry_point_test": "tests/secret_hygiene.rs::a_repeated_environment_dump_redacts_every_variable_family drives redact_tree_traced with a SealedAreas tree and asserts the generated *.redacted.json sidecar",
      "genuine_test_first_red": "the test failed before the fix with DSH_TERM_CMD / HOH_GAME_ROUTE / HOH_ROLE / HOH_RUN_DIR / HOH_ARTIFACT_DIR / PATH raw (0 of 4 <redacted> each) while HOH_MODEL_API_KEY and the late OPENAI_API_KEY were redacted",
      "spans": "pre-fix sidecar reproduced the acceptance's mechanism exactly; post-fix every family is redacted at all 4 occurrences and the sealed original stays byte-identical"
    },
    "item4a_fresh_workspace_and_godot_editor": {
      "mechanism": "confirmed in code: purge_contents removes every entry including the whole `.godot` tree, and GodotAdapter::initialize rebuilds only project.godot/scenes/scripts and never recreates `.godot`; the editor creates that tree when it imports a project at startup, so the book's order (point the editor first, then run with --fresh-workspace) leaves the running editor writing into a directory that no longer exists",
      "pinned_by": "tests/start_state.rs::fresh_workspace_removes_the_editor_cache_and_initialize_never_rebuilds_it",
      "documented_precondition": "doc comment on runtime::start_state::fresh_workspace (either restart/close the editor after a purge, or expect that one editor-infrastructure line)"
    },
    "item4b_out_of_tree_cleanup": {
      "extension": "is_root_temporary now also accepts is_round_scratch_name: one root component, extension in {json}, stem at most 4 chars of [a-z0-9_]; clean_round_temporaries additionally refuses anything that is not a regular file and (for the scratch family) anything larger than 8192 bytes",
      "measured_names_now_handled": ["l.json", "p2.json", "pv.json", "r.json"],
      "still_excluded": ["nested paths", "directories", "non-json extensions", "stems longer than 4", "files the watch never observed", "oversized payloads"],
      "recorded": "the removal is still reported through out_of_tree_cleanup and the write still remains a fact in out_of_tree_writes",
      "tests": [
        "src/runtime/hygiene.rs::the_terse_round_scratch_names_are_round_litter",
        "src/runtime/hygiene.rs::the_cleanup_removes_only_the_observed_root_scratch"
      ]
    },
    "item5_marking_source_must_be_an_acceptance_artifact": {
      "rule": "the marking source must be a repo-root-relative .md file whose final component contains the literal token ACCEPTANCE; enforced in hoh-acceptance-lib.sh (shared by the gate and the writer) and reported by scripts/accept-commit.sh mark with a dedicated message",
      "round_report_refused": "tests/push_gate.rs::a_round_report_cannot_authorise_its_own_push",
      "acceptance_artifact_allowed": "tests/push_gate.rs::an_acceptance_artifact_is_accepted_as_the_marking_source",
      "gate_fails_closed_on_such_a_ledger": "tests/push_gate.rs::the_gate_refuses_a_ledger_whose_source_is_not_an_acceptance_artifact",
      "missing_or_wrong_kind": "tests/push_gate.rs::a_missing_or_wrong_kind_of_source_is_refused_with_its_own_reason",
      "existing_semantics_preserved": "unaccepted commits are still refused commit-by-commit with subjects; a failed verdict still authorises nothing; the gate and the writer still agree on ledger validity"
    }
  },
  "plants": [
    {
      "id": "p1_secrets_guard",
      "file": "src/runtime/secrets.rs",
      "plant": "revert the overlap test to `start < span.end`",
      "target_test": "tests/secret_hygiene.rs::a_repeated_environment_dump_redacts_every_variable_family",
      "observed": "FAILED. 0 passed; 1 failed",
      "restored": "sha256 8c65f9234ec238b3931f25504cd80f7ceb157e5e34558bbd9da3a9b43f8d8c14, cmp EQUAL"
    },
    {
      "id": "p2_infra_off",
      "file": "src/adapter/godot.rs",
      "plant": "make editor_error_is_infrastructure always false",
      "target_test": "tests/launchable_gate.rs::an_editor_infrastructure_failure_does_not_close_the_gate",
      "observed": "FAILED. 0 passed; 1 failed",
      "restored": "sha256 75b4ed4d1ce2c6ea2f30e688f3a65ae043faa0e56d03cf4c9d0051ab64e12c33, cmp EQUAL"
    },
    {
      "id": "p3_window_off",
      "file": "src/adapter/godot.rs",
      "plant": "empty the anchor multiset so every judged line counts as new",
      "target_test": "tests/launchable_gate.rs::an_old_editor_log_line_outside_the_window_does_not_close_the_gate",
      "observed": "FAILED. 0 passed; 1 failed",
      "restored": "sha256 75b4ed4d1ce2c6ea2f30e688f3a65ae043faa0e56d03cf4c9d0051ab64e12c33, cmp EQUAL"
    },
    {
      "id": "p4_acceptance_off",
      "file": ".githooks/hoh-acceptance-lib.sh",
      "plant": "accept any repo-root-relative .md again (drop the ACCEPTANCE token test)",
      "target_test": "tests/push_gate.rs::a_round_report_cannot_authorise_its_own_push",
      "observed": "FAILED. 0 passed; 1 failed",
      "restored": "sha256 3ad63dd9c530d378931fdb915208f225da56b7796b975cc5bc4107a2d40ace9b, cmp EQUAL"
    },
    {
      "id": "p5_scratch_off",
      "file": "src/runtime/hygiene.rs",
      "plant": "drop the terse round-scratch family from is_root_temporary",
      "target_test": "src/runtime/hygiene.rs::the_terse_round_scratch_names_are_round_litter",
      "observed": "FAILED. 0 passed; 1 failed",
      "restored": "sha256 e422fe2aa64cfd1e1f81ec2cb57c4d0cef11b779d7ce2bd2f326aa53f76f9f66, cmp EQUAL"
    }
  ],
  "genuine_test_first_reds": [
    "tests/secret_hygiene.rs::a_repeated_environment_dump_redacts_every_variable_family",
    "tests/push_gate.rs::a_round_report_cannot_authorise_its_own_push",
    "tests/push_gate.rs::the_gate_refuses_a_ledger_whose_source_is_not_an_acceptance_artifact"
  ],
  "compile_error_reds_not_captured": [
    "tests/launchable_gate.rs::the_infrastructure_classifier_is_narrow",
    "tests/launchable_gate.rs::an_editor_infrastructure_failure_does_not_close_the_gate",
    "tests/launchable_gate.rs::an_old_editor_log_line_outside_the_window_does_not_close_the_gate",
    "tests/launchable_gate.rs::a_real_script_error_new_in_the_window_still_closes_the_gate",
    "src/runtime/hygiene.rs::the_terse_round_scratch_names_are_round_litter",
    "src/runtime/hygiene.rs::the_cleanup_removes_only_the_observed_root_scratch"
  ],
  "forbidden_zone": {
    "runs_files_written": 0,
    "runs_newest_mtime": "2026-10-02 02:36:58 UTC (runs/smoke-t14/evidence/analysis/json_block_check.txt), older than this batch",
    "workspace_newest_mtime": "2026-10-02 02:12:24 UTC (.workspace/fresh-t14/.hoh/evidence/qa-victory.png), older than this batch",
    "pushed": false,
    "prd_sha256": "4c81c3a9995f0b3afdf01421a0c3be88573cceefc284ce9bafbfda141f0f5c3a",
    "decisions_sha256": "5621b2eaf8cbb36a81d4ed3d4257605c703bbfff0e137c698fcc7fd78e593e69",
    "cargo_toml_sha256": "e0c4992bd828729b8514f9cf694925687b726157d45463a636390081a3dadba1",
    "cargo_lock_sha256": "d98fa91565ec72ae998fd9f6fd3838286e287e4baf8020c5114a1e2ac0bfdb36",
    "new_dependencies": 0,
    "line_endings": "all 12 edited files verified pure LF (CR=0); no CR byte introduced",
    "rm_rf_used": false,
    "path_built_from_unexpanded_variable": false
  },
  "real_ledger_now_fails_closed": {
    "file": ".git/hoh-accepted-commits.txt",
    "line": 45,
    "record": "accepted 03ee2e3b4a2c1ef4536ec0108afec2741ce7581a .spec/hof-rs/tasks/TASK-SMOKE-T14-REPORT.md pass 2026-10-02T02:43:17Z",
    "effect": "scripts/accept-commit.sh verify exits 1 and the pre-push gate REFUSES every push until that record is corrected",
    "intentional": true
  },
  "risks": [
    "The window anchor asks editor_get_errors for max_lines=2000 and assumes the engine answers the whole tail; I read the engine's tail-window implementation, but no engine was started in this batch, so the real answer length is inferred, not measured.",
    "The infrastructure phrase list is derived from the one measured smoke-t14 line; other editor-infrastructure wordings (other modules, other languages) are unverified and would keep failing closed.",
    "The window comparison is fail-safe in one direction only: if the anchor tail is truncated the judged line looks new and closes the gate (conservative); the opposite cannot turn a project defect into a pass except by an occurrence count that the anchor already carried.",
    "ROOT_SCRATCH_STEM_MAX = 4 is a heuristic bound: a deliberate 1-4 character-stem .json written to the repository root after the round started would be removed. It would still be a fact in out_of_tree_writes and a line in out_of_tree_cleanup.",
    "The ACCEPTANCE token test is case-sensitive and literal; a lowercase acceptance.md would be refused (fail closed).",
    "The `.godot/editor` conclusion is a code-level mechanism plus the frozen T14 evidence; it was not reproduced against a live editor in this batch.",
    "The window's count-based rule for a failed repair that re-produces an identical error line was exercised only with synthetic fixtures, not on real hardware."
  ],
  "honest_disclosure": [
    "My first implementation merged every overlapping candidate into the union; the frozen DR-72 sample test (tests/frozen_evidence.rs) then reddened because the union swallowed the PATH tail the sample pins. I changed the rule to containment-only absorption, which still closes the DSH_TERM_CMD-carries-an-assignment leak, and the frozen sample is byte-identical again. Nothing in the sample files was edited.",
    "Six new tests were written before their implementation but their first execution happened after it, so their first observable failure would have been a compile error, which I did not capture. They are listed under compile_error_reds_not_captured and are not counted as genuine test-first reds.",
    "I edited one existing test fixture (tests/push_gate.rs::the_marker_refuses_a_missing_report_and_a_non_pass_verdict now marks a missing ACCEPTANCE-named path instead of .spec/does-not-exist.md) so that the missing-report message stays the assertion of record. No test was renamed or deleted.",
    "The strengthened gate makes the repository's real local ledger invalid at line 45 (the G5 record). That is the intended consequence and is left in place rather than hand-edited, so the dispatcher sees it fail closed.",
    "All temporary material (plant backups, scripts, run logs) lives under C:\\Users\\wyl\\AppData\\Local\\Temp\\dr81-plants; nothing temporary was created inside the repository. The only new repository file is this report.",
    "No engine was started, no round was run, no network call was made, and nothing was committed or pushed."
  ]
}
```

---

## 1. ① 门的「基础设施失败 vs 工程缺陷」判定分离

### 1.1 机制

`src/adapter/godot.rs` 新增两个**具名**常量与一个谓词，规则是**追加式**的：

- `EDITOR_CACHE_NAMESPACE = "res://.godot/"` —— 编辑器自己的缓存命名空间（DR-11 已把它排除在 hash、快照与所有视图之外，里面没有任何产出工程的文件）。
- `EDITOR_INFRASTRUCTURE_ERROR_PHRASES` —— 引擎的**逐字**写失败措辞（`cannot create file` / `cannot open file` / `can't open file` / `error opening file` / `failed to write` / `check user write permissions`，大小写不敏感）。
- `editor_error_is_infrastructure(line) := line 含缓存命名空间 && 含上述某条措辞`。

这条规则**必须同时满足两个条件**，所以它既不是「`res://.godot` 通配」，也不是「任何失败措辞豁免」：`smoke-t14` pass 1 的 `ERROR: res://scripts/main.gd:8 - Parse Error` 两个条件都不满足，仍按原样关门。

判定流水线（`judge_editor_errors`）与既有语义完全一致，只在**最后**插入两段：

```
DR-48 精确横幅 → DR-68 陈旧行 → DR-81 ① 编辑器基础设施 → DR-81 ② 时间窗 → 剩余即工程缺陷
```

### 1.2 两侧证据

| 方向 | 测试 | 断言 |
|---|---|---|
| 基础设施**不**关门 | `an_editor_infrastructure_failure_does_not_close_the_gate` | `launchable=true`、`repair_retry_used=false`、角色序列 = Planner/Developer/Tester；observation 含逐字行、`editor_infrastructure_failures=1`、`project_defects_new=0`；raw 仍保留该行 |
| 真实脚本错误**仍**关门 | `an_infrastructure_failure_does_not_mask_a_real_script_error` | 混合夹具 ⇒ `launchable=false`、`repair_retry_used=true`、reason 含 `Parse Error`；observation 同时给出 `editor_infrastructure_failures=1` 与 `project_defects_new=1` |
| 判据不宽 | `the_infrastructure_classifier_is_narrow` | 缓存写失败行 = 真；解析错误行 = 假；`ERROR: [MCP] …` = 假；仅提 `.godot` 无失败措辞 = 假；仅提失败措辞但指向 `res://scripts/…` = 假 |
| 既有回归钉（全部保持绿） | `a_real_editor_error_still_closes_the_gate`、`an_error_carrying_the_mcp_prefix_still_closes_the_gate`、`an_unknown_mcp_prefixed_line_still_closes_the_gate`、`a_reproducible_parse_error_still_closes_the_gate`、`an_engine_info_banner_does_not_close_the_gate`、`a_stale_editor_log_line_does_not_close_the_gate` | 未改断言 |

**判定分离的记录**：observation 里两个**独立 token**（`editor_infrastructure_failures=N` 与 `project_defects_new=N`）使「基建」与「工程缺陷」在同一份证据里可分辨；raw 文档的 `channel.editor_error_window` 再给出窗口判据与各项计数。原始 payload 不改一字。

## 2. ② `editor_get_errors` 的时间窗判据

### 2.1 判据与窗口

`editor_get_errors` 读的是**编辑器日志尾部**（`_log_tail_lines` + `max_lines` 窗口 + `contains("ERROR")`），日志是 append-only。因此：

- **窗口锚定**：在 `project_reload_and_open` **之前**（即编辑器被强制重新读取磁盘工程之前）用 `max_lines=2000` 读一次，存为 `editor_error_anchor`（宽窗口，是判定读数可能内容的超集）。
- **判定读数**：步骤内以 `max_lines=50` 读一次，与锚做**多重集**比较；某个行串的出现次数**超过**锚里同串的出现次数，才算「本轮窗口内新增」。
- **计数而非集合**是关键：一次失败的重试修复会**再次**产生同一条错误行，计数器因此 +1，「新增」成立；只按集合去重会把这种真实回归误判为残留。
- **fail-closed**：锚缺失（调用失败 / payload 不是编辑器报告）时，所有行都算「新增」。
- 判据与窗口写入 raw：`channel.editor_error_window.{criterion,anchor,anchor_line_count,anchor_request_and_answer,banners,stale,editor_infrastructure_failures,pre_existing_lines,project_defects_new}`。

### 2.2 反例（先红一侧 + 回归钉）

| 场景 | 测试 | 结果 |
|---|---|---|
| 旧日志尾部含错误、窗口内无新错误 | `an_old_editor_log_line_outside_the_window_does_not_close_the_gate` | 锚与判定读数都是 `main.gd:8` ⇒ `launchable=true`、`repair_retry_used=false`、`project_defects_new=0`、observation 含 `pre-existing` 与逐字行、raw 给出窗口判据 |
| 窗口内新增真实错误 | `a_real_script_error_new_in_the_window_still_closes_the_gate` | 锚 `[旧行]`、判定 `[旧行, 新行]` ⇒ `launchable=false`、`repair_retry_used=true`、reason 含 `main.gd:12`、`project_defects_new=1` |
| 退出码与冻结（前后对照） | T14 的反例：H7 显示同一 `editor_get_errors` 在 48 分钟后返回**非错误行** | 新判定不再把「尾部读数」直接当硬判决：AL 的既有红线（真实脚本错误）由窗口内的「新增」承担，附着在工程侧的旧残留被显式记为 `pre-existing` |

## 3. ③ `secrets.rs` span/overlap 吞并 —— 机制定位与真实入口红→绿

### 3.1 机制（**为何单测绿而真实路径红**）

`src/runtime/secrets.rs` 的 `splice_assignments` 以**名字为外层循环**扫描（`SECRET_ENV_VARS` 先，`HARNESS_ENV_VARS` 后），旧的防重入判据是：

```rust
if spans.iter().any(|span| start < span.end) { cursor = start + needle.len(); continue; }
```

这不是区间重叠，而是**「起点是否早于目前见过的最大 span 终点」**的全局前向判据。真实轨迹把整条环境转储**重复了 4 次**，其中 `OPENAI_API_KEY` 的最后一次出现在文件尾部（286080–286095）；它**先于**整族 `HOH_*` / `DSH_TERM_CMD` / `PATH` 被扫描，于是**每一个更晚被扫描的名字的每一次更早出现**都被报 `SKIP(overlap)` 而原文存活。

单测（`src/runtime/secrets.rs:1348/:1384`）之所以绿：两个夹具都只有**单个赋值、没有重复转储**，构造上不可能触发「更晚出现的更早扫描名」这条路径。T14 验收的 R5/R6 用逐字节移植与最小植入证明了这一点；本批次把它变成一条**走真实入口**的回归测试。

### 3.2 修法

```rust
// 真区间相交
let absorbed: Vec<usize> = spans.iter().enumerate()
    .filter(|(_, span)| start <= span.start && span.end <= value_end && start < span.end)
    .map(|(index, _)| index).collect();
if !absorbed.is_empty() {
    // 候选吞并已记录 span：用更宽的候选替换（否则命令行的头/尾会原文存活）
} else if !spans.iter().any(|span| start < span.end && span.start < value_end) {
    // 无交集：记录候选
}
// 候选落在已记录 span 内部：保留原 span（DR-73/DR-74 冻结样本把这种形状的残余尾部钉为已记录成本）
```

- **区间相交**取代全局前向判据 ⇒ 一处 span 不再吞掉「起点更早、实际不相关」的赋值。
- **吞并（containment absorption）**解决另一半泄漏：`DSH_TERM_CMD` 的命令行里带 `HOH_ROLE=<value>` 时，`HOH_ROLE` 先被扫描并记录，若把更宽的候选跳过，命令行的头/尾会原文存活；吞并后整行被替换（`src/runtime/secrets.rs::a_command_line_containing_an_assignment_absorbs_it` 钉住）。

### 3.3 真实入口的测试红→绿

测试：`tests/secret_hygiene.rs::a_repeated_environment_dump_redacts_every_variable_family`
入口：**`redact_tree_traced` + `SealedAreas`**（运行时真正生成 `*.redacted.json` 旁路副本的那条路径）。夹具是一个含 4 次重复环境转储的 JSON 轨迹，第 4 次转储尾部带一条 `OPENAI_API_KEY=`（验收的最小植入）。

**修复前的真实（非编译错误）红**（实测，直接引用失败输出）：

```
left: 0
right: 4   (DSH_TERM_CMD must be redacted at every occurrence, with_late_openai_key=true)
DSH_TERM_CMD=cd /f/moonbit-hof-rs ...            ← 原文存活
HOH_GAME_ROUTE=F:\moonbit-hof-rs\runs\...        ← 原文存活
HOH_ROLE=developer / HOH_RUN_DIR=F:\... / HOH_ARTIFACT_DIR=F:\... / PATH=C:\...  ← 原文存活
HOH_MODEL_API_KEY=<redacted>                     ← 早扫描的名字照旧被脱敏
OPENAI_API_KEY=<redacted>                        ← 晚出现的名字照旧被脱敏
```

修复后：六个名字各 **4/4** 被脱敏（`NAME=<redacted>`），原始赋值形态 0 命中，密封原文件逐字节未变，旁路副本仍是合法 JSON；同时 `with_late_openai_key=false` 的对照也在同一测试里被断言（证明结果不依赖那条后置行）。

## 4. ④ 机制结论与模式扩展

### 4.1 `--fresh-workspace` 与 `.godot/editor`（T14 留白项）

**结论（代码级机制，已钉为测试）**：

1. `src/runtime/start_state.rs::purge_contents` 遍历并删除工作区的**每一个条目**（含整个 `.godot/` 缓存树；软链接只删链接本身）。
2. `GodotAdapter::initialize` 只重建 `A₀` 产品：`project.godot`、`scenes/`、`scripts/` —— **从不重建 `.godot`**。
3. Godot 只在**项目导入/编辑器启动**时创建 `.godot/**`。任务书要求的顺序是「先建空目录 → `init` → 让编辑器指向该工程 → `run`」，而 `--fresh-workspace` 在编辑器已指向该工程之后把目录从它脚下删掉 ⇒ 运行中的编辑器**不会**重新导入，它下一次写缓存时父目录已不存在，于是报 `Cannot create file 'res://.godot/editor/filesystem_cache10'. Check user write permissions.`（`smoke-t14` 的 fresh-t14 整目录缺失，而 fresh-t13 在 04:54 重建过 —— 与「编辑器在清空之后才（重新）指向该工程」一致）。

**前置条件已写进代码与交付文本**：`fresh_workspace` 的文档注释明确「清空工作区后需重启/关闭编辑器，或预期那条基础设施日志行」，并指出门已按 ① 分类它，不得据此冻结干净工程。

测试：`tests/start_state.rs::fresh_workspace_removes_the_editor_cache_and_initialize_never_rebuilds_it`（写入 `.godot/editor/filesystem_cache10` 后 `fresh_workspace` ⇒ `.godot` 与 `.godot/editor` 均不存在，而 `project.godot` 存在）。

### 4.2 越界清理模式扩展

DR-79 只匹配 `.tmp_*`/`tmp_*`/`*.tmp`/`*.bak`，因此 T14 的 `l.json`/`p2.json`/`pv.json`/`r.json` 未被清理。扩展为：

- **既有四族**不变；
- 新增 `is_round_scratch_name`：**单段**、扩展名 ∈ `{"json"}`、词干 ≤ **4** 字符且仅 `[a-z0-9_]`（`ROOT_SCRATCH_EXTENSIONS` / `ROOT_SCRATCH_STEM_MAX`）；
- `clean_round_temporaries` 追加两道界：必须是**普通文件**；命中 scratch 族时大小 ≤ **8192 B**（`ROOT_SCRATCH_MAX_BYTES`）。

**仍有界、仍留记录、仍保事实**：路径必须来自 `OutOfTreeWatch::observed()`（只含本轮相对开工时新增/变化的路径），只删文件、不删目录、不通配、不 `rm`，且复核父目录就是扫描根；删除结果仍由 `run_loop` 写成 `out_of_tree_cleanup: removed N round-temporary file(s) …`，`out_of_tree_writes` 仍保留「写过」的事实。

**非破坏性**：未观测到的（本轮之前就存在的）、嵌套的、目录的、非 `.json` 的、词干 > 4 的、超 8 KiB 的都不动；测试 `the_cleanup_removes_only_the_observed_root_scratch` 逐一钉住这些生存者（含磁盘上存在但不在 `observed` 里的 `old.json`）。

## 5. 门读数与禁区自查

### 5.1 门

| 项 | 读数 |
|---|---|
| 基线（我自己复现） | `cargo test --offline` **exit 0**，**560 passed / 0 failed / 7 ignored**，`--list` **567** |
| 终态（强制重建后） | **exit 0**，**575 passed / 0 failed / 7 ignored**，`--list` **582** |
| 新增测试 | **15**（见下），**删除 0**，ignored 计数与名字不变（同一组 7 条 smoke e0..e6） |
| 格式化 | `cargo fmt --all --check` **exit 0** |
| 强制重建 | 先以 **Python glob + `shutil.rmtree`** 清掉 61 个 `target/debug/.fingerprint/hof-rs-*`；再**逐文件** `touch` **97** 个 `git ls-files '*.rs'`（无通配符）；日志出现 `Compiling hof-rs v0.1.0 (F:\moonbit-hof-rs)` |

新增 15 条测试：
`src/runtime/secrets.rs`（2）`a_late_occurrence_of_an_early_scanned_name_does_not_hide_an_earlier_candidate`、`a_command_line_containing_an_assignment_absorbs_it`；
`src/runtime/hygiene.rs`（2）`the_terse_round_scratch_names_are_round_litter`、`the_cleanup_removes_only_the_observed_root_scratch`；
`tests/secret_hygiene.rs`（1）`a_repeated_environment_dump_redacts_every_variable_family`；
`tests/launchable_gate.rs`（5）`the_infrastructure_classifier_is_narrow`、`an_editor_infrastructure_failure_does_not_close_the_gate`、`an_infrastructure_failure_does_not_mask_a_real_script_error`、`an_old_editor_log_line_outside_the_window_does_not_close_the_gate`、`a_real_script_error_new_in_the_window_still_closes_the_gate`；
`tests/start_state.rs`（1）`fresh_workspace_removes_the_editor_cache_and_initialize_never_rebuilds_it`；
`tests/push_gate.rs`（4）`a_missing_or_wrong_kind_of_source_is_refused_with_its_own_reason`、`a_round_report_cannot_authorise_its_own_push`、`an_acceptance_artifact_is_accepted_as_the_marking_source`、`the_gate_refuses_a_ledger_whose_source_is_not_an_acceptance_artifact`。

### 5.2 受控植入（5 处，各自红、逐字节回退）

| # | 文件 | 植入 | 目标测试 | 红 | 回退 |
|---|---|---|---|---|---|
| p1 | `src/runtime/secrets.rs` | 重叠判据退回 `start < span.end` | `a_repeated_environment_dump_redacts_every_variable_family` | `FAILED. 0 passed; 1 failed` | sha256 `8c65f923…8c14`，`cmp` EQUAL |
| p2 | `src/adapter/godot.rs` | `editor_error_is_infrastructure` 恒假 | `an_editor_infrastructure_failure_does_not_close_the_gate` | `FAILED. 0 passed; 1 failed` | sha256 `75b4ed4d…2c33`，`cmp` EQUAL |
| p3 | `src/adapter/godot.rs` | 锚多重集清空（全部算新增） | `an_old_editor_log_line_outside_the_window_does_not_close_the_gate` | `FAILED. 0 passed; 1 failed` | sha256 `75b4ed4d…2c33`，`cmp` EQUAL |
| p4 | `.githooks/hoh-acceptance-lib.sh` | 恢复「任意 `.md` 即可」 | `a_round_report_cannot_authorise_its_own_push` | `FAILED. 0 passed; 1 failed` | sha256 `3ad63dd9…ce9b`，`cmp` EQUAL |
| p5 | `src/runtime/hygiene.rs` | 去掉 scratch 族 | `the_terse_round_scratch_names_are_round_litter` | `FAILED. 0 passed; 1 failed` | sha256 `e422fe2a…9f66`，`cmp` EQUAL |

每个植入都以二进制方式（`read_bytes`/`write_bytes`）施加与回退，**绝不整文件重写行尾**；回退后再用 `cmp` 与备份逐字节比较，5/5 EQUAL。

### 5.3 禁区自查（全部实测）

| 项 | 证据 |
|---|---|
| `runs/**` 零写入 | Python 递归扫描：`runs` 6886 个文件，最新 mtime = `2026-10-02 02:36:58 UTC`（上批的分析产物），**早于本批次开工（约 03:50 UTC）** |
| 工作区零写入 | `.workspace` 583 个文件，最新 mtime = `2026-10-02 02:12:24 UTC`，同样早于本批 |
| 未推送 | `git rev-parse origin/master` = `03ee2e3…`；`git reflog show origin/master` 最新条目仍是上批的 `update by push`，本批 0 次 push |
| 冻结件未动 | `PRD-mario.md` `4c81c3a9…5c3a`；`DECISIONS.md` `5621b2ea…e69`（= T14 验收公布值）；`Cargo.toml` `e0c4992b…ba1`；`Cargo.lock` `d98fa915…6b7`；`godot-mcp/**` 与任何 `.workspace/**` 未出现于 `git status` |
| 未加依赖 | `Cargo.toml`/`Cargo.lock` 在 diff 中不存在 |
| 无新增临时物 | `git status --porcelain` 只列出本批 12 个被改文件 + 4 个**上批遗留**未跟踪文件（`l.json`/`p2.json`/`pv.json`/`r.json`，T14 验收的 G7，本批未触碰）+ 本报告；所有临时材料在 `C:\Users\wyl\AppData\Local\Temp\dr81-plants` |
| 无 `rm -rf`、无未展开变量构造路径 | 删除只用 `shutil.rmtree`（限定 `target/debug/.fingerprint/hof-rs-*` 的 glob 结果）与 `std::fs::remove_file`；无任何 `rm -rf`；无 `$VAR/...` 拼接 |
| 行尾未重写 | 12 个被改文件全部 CR=0（纯 LF） |
| 历史报告未改 | 只新建本报告；`tests/append_only_guard.rs` 钉住的三份文件未出现在 diff |

### 5.4 ⑤ 对**真实台账**的即时验证（G5 的机械闭环）

`.git/hoh-accepted-commits.txt` 第 45 行正是 T14 的 G5 缺陷：

```
accepted 03ee2e3b4a2c1ef4536ec0108afec2741ce7581a .spec/hof-rs/tasks/TASK-SMOKE-T14-REPORT.md pass 2026-10-02T02:43:17Z
```

强化后：

- `sh scripts/accept-commit.sh verify` ⇒ **exit 1**，输出 `INVALID: line 45 is malformed: … is not an acceptance artifact …`；
- `pre-push`（合成 no-op ref 行，真实台账）⇒ **REFUSED**，逐字指出该记录与 ACCEPTANCE 要求 ⇒ **fail closed，每条推送都被拒**。

这是「被审对象不得自我授权」在**真实状态**上的闭环证明。**该行仍留在台账里**（未手改），以便派遣方看到闸门确实咬住。

## 6. 遗留风险与未验证项（严格区分实测 / 推断）

**实测**：门读数（560→575，ignored 恒 7，567→582）、`fmt` 0、强制重建、5 处植入各自红且逐字节回退、真实入口测试的真实红与绿、真实台账 verify/ gate 的 fail-closed、`runs/**` 与 `.workspace/**` 的 mtime、`origin/master` 未动、冻结件哈希、纯 LF。

**推断（未在真机复现）**：

1. 窗口锚 `max_lines=2000` 假设引擎返回整条尾部。我只读了引擎 `_log_tail_lines` 的实现（`max_lines` 大于总行数时 `start=0`），**没有启动引擎**验证真实返回长度。
2. `.godot/editor` 的机制是**代码级**结论 + 冻结件形状，未在活体编辑器上插桩复现。
3. 基础设施措辞表来自**唯一一条**实测行；其他模块/语言的基础设施文案未验证（会继续 fail-closed）。
4. 窗口的多重集规则对「失败修复重复产生同一行」的场景只在合成夹具上演练，未在真机验证。
5. `ROOT_SCRATCH_STEM_MAX=4` 是启发式界：词干 ≤4 的、**故意**写在仓根的 `.json` 会被清理（仍留 `out_of_tree_cleanup` 记录与 `out_of_tree_writes` 事实）。
6. ACCEPTANCE token 为**区分大小写**的字面匹配；小写 `acceptance.md` 会被拒（fail closed）。

## 7. 诚实披露

1. **我改过的规则**：第一版把**所有**相交候选合并进并集，`tests/frozen_evidence.rs::the_redacted_sample_is_regenerable_from_the_production_pass` 随即变红（并集吞掉了 DR-73/DR-74 冻结样本钉住的 `PATH` 尾部）。我改为**仅吞并被候选包含的 span**：既闭合 `DSH_TERM_CMD` 携带 `HOH_ROLE=` 的泄漏，又让冻结样本逐字节不变；**未修改任何样本文件**。
2. **弱红如实登记**：6 条新测试虽然先写，但首次执行发生在实现之后，其首次可观察失败本应是**编译错误**，我**没有**捕获到；它们在机器块中列在 `compile_error_reds_not_captured`，**不计入真先红**。真先红只有 3 条（`a_repeated_environment_dump_redacts_every_variable_family`、`a_round_report_cannot_authorise_its_own_push`、`the_gate_refuses_a_ledger_whose_source_is_not_an_acceptance_artifact`）。
3. 我修改了**一条既有测试的夹具路径**（`the_marker_refuses_a_missing_report_and_a_non_pass_verdict` 现在标记一个缺失的 ACCEPTANCE 命名路径，以保住「缺失 ⇒ 明确报不存在」这条断言）；**没有测试被改名或删除**。
4. **真实台账现在无效**（第 45 行），这是**有意的**：闸门必须在此 fail closed，而不是被绕过。派遣方在推送前需要修正该记录（改用一个真正的验收件，或删除该行）。
5. 未跑真机轮、未起引擎、未联网、未提交、未推送；`runs/**` 与 `.workspace/**` 一字节未写；临时物全在仓外。
