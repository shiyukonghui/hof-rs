# TASK-DR82-REPORT — 让「跳跃」类真的是上抛弧线（E3，**只改驱动与判定**）；把脱敏补到 **JSON 键形态**（两种编码）；以**追加式**更正 `.godot` 重建机制与台账自相矛盾；并补门窗口两条未测分支与风险(a)的可执行记录

- 实现子代理（无上游对话上下文）；**本文件是唯一任务来源**：`F:\moonbit-hof-rs\.spec\hof-rs\tasks\TASK-DR82.md`
- 规格来源：`TASK-SMOKE-T15-REPORT.md`（F-T15-1/2/4 与全部原始证据）与其验收 `TASK-SMOKE-T15-ACCEPTANCE.md`、`TASK-DR81-REPORT.md` / `TASK-DR81-ACCEPTANCE.md`（DR81A-2/3/4 与风险(a)）、`DECISIONS.md` **D289/D293/D294**
- 批次性质：**离线批次**。未启动引擎、未跑任何真机轮、**未联网**；未提交、**未推送**
- 开工时 HEAD = 收工时 HEAD = `199ce37a370fa8f968d64c1bc9d4a6db2ee8340f`；`origin/master` 同值（**本批未推送**）
- 落点：`F:\moonbit-hof-rs`

---

## 0. 机器可读判定

以下块由 `json.dumps(..., ensure_ascii=False, indent=2)` 生成，**先落盘**到仓外
`machine_block_dr82.json`（13783 B，sha256 `9dad73998ecf946f…`），
再由下面这段报告文本**按行锚定栅栏回读**并 `json.loads` 复核（见 §9 的回读证明）。

```json
{
  "task": "TASK-DR82",
  "kind": "implementation subagent report (offline batch: no engine, no real round, no network, nothing pushed; nothing written under runs/**)",
  "head": "199ce37a370fa8f968d64c1bc9d4a6db2ee8340f",
  "origin_master": "199ce37a370fa8f968d64c1bc9d4a6db2ee8340f",
  "pushed": false,
  "baseline": {
    "passed": 575,
    "failed": 0,
    "ignored": 7,
    "listed": 582,
    "reproduced_by_me": true,
    "note": "the first run of this batch reddened two pre-existing hygiene tests because the test binaries were stale; the same two passed once the crate was rebuilt, so the book's 575/0/7 is reproduced"
  },
  "gate": {
    "passed": 589,
    "failed": 0,
    "ignored": 7,
    "listed": 596,
    "exit": 0,
    "fmt_exit": 0,
    "fingerprints_removed_with_python_glob_rmtree": 61,
    "tracked_rs_files_touched_individually": 97,
    "touched_paths_are_literal": true,
    "forced_compile_line": "Compiling hof-rs v0.1.0 (F:\\moonbit-hof-rs)",
    "seconds": 1376.0,
    "tests_removed": 0,
    "new_tests": 14,
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
    "item1_jump_is_an_arc": {
      "side_only": "driving and judging only; the level and PRD-mario.md are untouched",
      "ground_check": "a 2-frame game-process position sample immediately before the jump injection; player_is_resting_on_ground requires the y series to be flat within 1e-3, and an unreadable probe fails closed",
      "degenerate_rejection": "a driven jump window is recorded as an observed jump only when JumpReading::shows_an_arc() holds: rise > 0 (first - min) and y not monotone; otherwise the window is recorded as unobserved (JUMP_DEGENERATE_FALL / JUMP_NO_RISE) and the run is marked failed",
      "not_driven_token": "JUMP_NOT_DRIVEN",
      "raw_record_field": "jump_reading",
      "tests": [
        "evidence_battery::a_jump_window_over_a_gap_is_rejected_instead_of_passed",
        "evidence_battery::a_monotone_fall_is_not_recorded_as_an_observed_jump",
        "evidence_battery::a_jump_driven_from_the_ground_is_recorded_as_an_arc",
        "evidence_battery::an_airborne_start_and_an_unreadable_probe_both_fail_closed",
        "evidence_battery::a_jump_window_with_no_rise_is_rejected_too",
        "evidence_battery::the_arc_rule_rejects_the_t15_series_and_accepts_a_real_one",
        "evidence_battery::the_probe_frame_count_matches_the_production_constant"
      ],
      "real_round_threat": "smoke-t15's window is reproduced verbatim in the_arc_rule_rejects_the_t15_series_and_accepts_a_real_one: rise = 0.0, monotone, JUMP_DEGENERATE_FALL, never an observed jump"
    },
    "item2_json_key_shape": {
      "encodings_covered": [
        "\"NAME\": \"value\" (a real member key; the encoding the frozen files use)",
        "\\\"NAME\\\": \\\"value\\\" (the same key inside a JSON string)"
      ],
      "declared_before_dr82": 10,
      "newly_declared": [
        "HOH_TOOLS_POLICY",
        "HOH_WORKSPACE"
      ],
      "real_file_census": {
        "method": "a JSON-aware walk of the decoded keys over the frozen runs/smoke-t15 and runs/smoke-t14 trajectories (read-only)",
        "names_as_keys_per_file": 16,
        "present": "12 HOH_* names + the 4 credential names, each exactly once",
        "absent": [
          "DSH_TERM_CMD",
          "HOH_SECRET_PATH",
          "PATH",
          "Path"
        ],
        "credential_values": "the 4 credential keys carry the empty string",
        "pre_existing": "the same 16 keys appear in t14's files as well, so the vector is pre-existing and not a DR-81 regression"
      },
      "two_methods": {
        "escaped_fixture": {
          "M1_raw_bytes_escaped": "16 per family x 4 dumps = 64 occurrences seen",
          "M2_json_aware_decoded_walk": 64,
          "agree": true,
          "why": "every occurrence lives inside the host string, which is the one encoding both methods can see; the methods are the same occurrences through two encodings"
        },
        "unescaped_fixture": {
          "M1_raw_bytes_unescaped": 16,
          "M2_json_aware_key_walk": 16,
          "agree": true,
          "why": "the names are real object keys, so both views see them"
        },
        "frozen_round": {
          "M3_json_aware_key_walk": "16 keys in every file",
          "M4_raw_bytes_escaped_spelling": 0,
          "agree": false,
          "why": "the frozen files carry the names as unescaped real keys, so the escaped spelling never occurs.  This disagreement is the finding that made the batch widen the scan: an implementation that only knew the escaped spelling reported the frozen files clean while they were raw"
        },
        "naive_scan_trap": {
          "method": "the guarded byte scan (?<![A-Za-z0-9_])NAME=",
          "planner.attempt1.json": "1 reported vs 28 real",
          "developer.attempt1.json": "0 reported vs 26 real (fully false-green)",
          "tester.attempt1.json": "15 reported vs 15 real",
          "why": "inside the JSON string the escape is the two bytes backslash + n, so the byte before the name is the letter n and the guard rejects real occurrences"
        }
      },
      "tests": [
        "secret_hygiene::the_json_key_shape_of_the_environment_dump_is_redacted_too",
        "secret_hygiene::the_unescaped_role_config_dump_is_redacted_too",
        "secret_hygiene::a_repeated_environment_dump_redacts_every_variable_family"
      ],
      "sealed_originals_unchanged": true
    },
    "item3_godot_rebuild_claim": {
      "corrected_claim": "DR-81 4 asserted that an already-running editor does not rebuild .godot; smoke-t15 measured that this round's running editor did rebuild it (11 files, 14:05-14:30, after the 13:52:17 purge, including filesystem_cache10).  The mechanism is not determined here",
      "append_only": true,
      "correction_heading": "附：DR-82 ③ 更正",
      "sealed_prefix": {
        "bytes": 41045,
        "sha256": "7834f2d71d970d5a27b95c6fcc5a339525616c3a08bfe23dbf20e9ac8048efc8",
        "equals_dr81_acceptance_review_sha": true
      },
      "judgements_depending_on_the_claim": 0,
      "doc_comment_corrected": "src/runtime/start_state.rs::fresh_workspace",
      "test": "append_only_guard::the_dr81_report_prefix_before_the_dr82_correction_is_frozen"
    },
    "item4_leftovers": {
      "A-2": {
        "change": ".githooks/hoh-acceptance-lib.sh: the case pattern */*.md became *.md, so a repo-root-relative ACCEPTANCE.md is accepted as the marking source, matching the rule's own wording and its refusal message",
        "open_direction_disclosed": "accepting a root-level file widens the accepted set by one shape; the token test and the no-separator/absolute-path refusals are unchanged",
        "test": "push_gate::a_repo_root_level_acceptance_artifact_is_accepted_as_the_marking_source"
      },
      "A-3": {
        "change": "an append-only correction was added to TASK-DR81-REPORT.md for the contradiction between honest_disclosure item 4 and section 5.4 about the real ledger; the current reading (exit 0, 48 records, line 45 repointed) is recorded as the authority",
        "machine_block_left_frozen": true,
        "test": "append_only_guard::the_dr81_report_prefix_before_the_dr82_correction_is_frozen"
      },
      "A-4": {
        "count_growth_branch": {
          "test": "launchable_gate::a_repair_that_reproduces_the_same_line_still_closes_the_gate",
          "measured": "anchor [E], judged [E,E,E]; project_defects_new=2, 1 pre-existing"
        },
        "anchor_absent_branch": {
          "test": "launchable_gate::an_absent_window_anchor_fails_closed",
          "measured": "the wide anchor call fails, every judged line counts as new"
        }
      },
      "risk_a_window_can_mask": {
        "handling": "recorded as an executable fact, not prose: the new test drives a project that is broken on disk whose error line the reload never re-emits, and asserts launchable == true with the anchor carrying the line while project_defects_new == 0",
        "test": "launchable_gate::the_window_can_still_open_on_a_project_that_is_broken_on_disk",
        "why_accepted": "the window's anchor is the only baseline available offline; the limitation is now pinned, so adding a disk-side probe would redden the test on purpose instead of quietly changing behaviour"
      }
    }
  },
  "plants": {
    "count": 6,
    "all_reddened_their_own_test": true,
    "all_restored_byte_exact": true,
    "entries": [
      {
        "id": "p1_ground_always_resting",
        "file": "src/adapter/godot.rs",
        "target": "evidence_battery::a_jump_window_over_a_gap_is_rejected_instead_of_passed",
        "why": "make the pre-jump ground probe say 'resting' unconditionally, so an airborne window is driven and scored",
        "exit": "101",
        "first_failure": "thread 'a_jump_window_over_a_gap_is_rejected_instead_of_passed' (40732) panicked at tests\\evidence_battery.rs:4044:5:",
        "seconds": "26.4",
        "restored_byte_exact": "True"
      },
      {
        "id": "p2_arc_always_true",
        "file": "src/adapter/godot.rs",
        "target": "evidence_battery::a_jump_window_with_no_rise_is_rejected_too",
        "why": "make shows_an_arc unconditionally true, so a rise-zero window is scored as an observed jump",
        "exit": "101",
        "first_failure": "thread 'a_jump_window_with_no_rise_is_rejected_too' (39024) panicked at tests\\evidence_battery.rs:4197:5:",
        "seconds": "26.3",
        "restored_byte_exact": "True"
      },
      {
        "id": "p3_json_key_off",
        "file": "src/runtime/secrets.rs",
        "target": "secret_hygiene::the_unescaped_role_config_dump_is_redacted_too",
        "why": "disable the JSON-key splice, so the key shape survives raw again (the DR-82 defect) in the encoding the frozen files really use",
        "exit": "101",
        "first_failure": "thread 'the_unescaped_role_config_dump_is_redacted_too' (19484) panicked at tests\\secret_hygiene.rs:740:5:",
        "seconds": "7.6",
        "restored_byte_exact": "True"
      },
      {
        "id": "p4_acceptance_separator",
        "file": ".githooks/hoh-acceptance-lib.sh",
        "target": "push_gate::a_repo_root_level_acceptance_artifact_is_accepted_as_the_marking_source",
        "why": "restore the */*.md separator requirement, so a repo-root-level ACCEPTANCE.md is refused again",
        "exit": "101",
        "first_failure": "thread 'a_repo_root_level_acceptance_artifact_is_accepted_as_the_marking_source' (31496) panicked at tests\\push_gate.rs:101:5:",
        "seconds": "7.7",
        "restored_byte_exact": "True"
      },
      {
        "id": "p5_anchor_fail_open",
        "file": "src/adapter/godot.rs",
        "target": "launchable_gate::an_absent_window_anchor_fails_closed",
        "why": "make an absent anchor dismiss every judged line instead of counting them as new",
        "exit": "101",
        "first_failure": "thread 'an_absent_window_anchor_fails_closed' (39784) panicked at tests\\common\\mod.rs:312:13:",
        "seconds": "20.4",
        "restored_byte_exact": "True"
      },
      {
        "id": "p6_window_set_not_count",
        "file": "src/adapter/godot.rs",
        "target": "launchable_gate::a_repair_that_reproduces_the_same_line_still_closes_the_gate",
        "why": "compare the window as a set instead of by occurrence count, so a re-produced line is dismissed as residue",
        "exit": "101",
        "first_failure": "thread 'a_repair_that_reproduces_the_same_line_still_closes_the_gate' (20352) panicked at tests\\common\\mod.rs:312:13:",
        "seconds": "20.9",
        "restored_byte_exact": "True"
      }
    ]
  },
  "forbidden_zones": {
    "runs_new_files": 0,
    "workspace_new_files_excluding_preexisting": 0,
    "prd_sha256": "4c81c3a9995f0b3afdf01421a0c3be88573cceefc284ce9bafbfda141f0f5c3a",
    "prd_unchanged": true,
    "decisions_sha256": "245befb7af292c379c161ddc917e996a54a4dceea5e93c5d0226816efbae4a76",
    "decisions_unchanged": true,
    "requirements_sha256": "298a948929a434a91b9088f4d566b7e387d0cfeb270f86a79d88b006821e0e54",
    "engine_binary_sha256": "08483088a4a2772841cd3b4c916b2d45b3cb6255656cf3951598a86fce7e9e6a",
    "engine_repo_head": "fc63af77c33368c4a1bb839c95d19750554f63a3",
    "engine_repo_porcelain_empty": true,
    "cargo_toml_sha256": "e0c4992bd828729b8514f9cf694925687b726157d45463a636390081a3dadba1",
    "cargo_lock_sha256": "d98fa91565ec72ae998fd9f6fd3838286e287e4baf8020c5114a1e2ac0bfdb36",
    "pushed": false,
    "line_endings_rewritten": 0,
    "repository_line_endings_all_lf": true,
    "rm_rf_used": false,
    "git_checkout_restore_used": false,
    "paths_built_from_unexpanded_variables": false
  },
  "machine_block": {
    "generator": "json.dumps(..., ensure_ascii=False, indent=2)",
    "round_trip_verified": true
  },
  "unverified": [
    "no engine was started, no round was run, no network call was made",
    "the improved jump rule is proved on the fixture that reproduces the T15 readings; it has not been driven against a real level",
    "the cruise job (walking the player back to ground and re-driving a refused jump) is a deliberate non-goal of this batch",
    "the production redactor was not applied to the frozen runs/** files: they are read-only evidence.  The defect and its census were measured with an independent Python implementation instead",
    "the .godot rebuild mechanism remains unattributed: smoke-t14 did not rebuild, smoke-t15 did, and no instrumentation exists for why"
  ]
}
```

---

## 1. ① E3：让「跳跃」类真的是上抛弧线（**只改驱动与判定**）

### 1.1 真机事实与根因（承重）

`TASK-SMOKE-T15-REPORT.md` §2.3 的原始读数：跳跃窗口（`raw/input_replay.json` call 31，30 采样）
满足 `x unique=1`、`y` 从 `1492.81433105469` **严格递增**到 `2552.92553710938`、**最小值在 index 0**、
**`rise=0.0`**、`velocity.y=+42.0` ⇒ 是**自由落体**；引擎的 `position:neq` 之所以 `passed=true`
**只因位置变了**（`injected != moved`）。验收把它升级为几何事实：**唯一地板 x∈[0,3400]，跳跃窗口在
x=3690.03**，而 `player.gd` 的 `is_on_floor()` 守卫使「空中按跳跃」**结构上不可能**起跳。

⇒ 缺陷在**驱动与判定**两侧，**不在关卡、不在 PRD**。

### 1.2 修复（`src/adapter/godot.rs`，只改驱动/判定）

1. **驱动前核实玩家下方有地面。** 跳跃窗口注入**之前**，用引擎语义工具
   `running_game_get_node_property_samples` 取 **2 帧** `Player.position`（标签 `jump:ground_probe`），
   由 [`player_is_resting_on_ground`] 判定：`y` 在 `JUMP_GROUND_EPSILON = 1e-3` 内**不变化**才算「站在地上」。
   - 读不到（工具失败、样本不足）⇒ **fail closed**，记为未观测，**绝不当成「大概在地上」**。
   - 不在空中才注入；否则**根本不注入**，并在观测里写
     **`JUMP_NOT_DRIVEN`** 与理由（不是 `INPUT_HAD_NO_EFFECT`——那会把驱动方的选择算成工程的缺陷）。
2. **拒绝退化结果。** 真的被驱动的跳跃窗口，只有
   [`JumpReading::shows_an_arc`] 为真才记为「观察到跳跃」：**`rise = first − min > 0`**（玩家确实跃过窗口起点）
   **且 `y` 非单调**。否则记 `JUMP_DEGENERATE_FALL` / `JUMP_NO_RISE`，`ok=false`，窗口标为**未观测**。
   - 原始件里逐窗口写入 `jump_reading: {rise, monotone_fall, shows_an_arc, verdict}`，**且只对被驱动的窗口写**
     （`jump_driven` 守卫）——未观测的窗口**没有可被打分的读数**。
3. **关卡未被改写。** 本批只改 `src/adapter/godot.rs` 的驱动/判定与测试；`PRD-mario.md` 逐字节未动（§8）。

### 1.3 「拒绝退化结果」的证明

| 测试 | 它钉住什么 | 关键读数 |
|---|---|---|
| `evidence_battery::a_jump_window_over_a_gap_is_rejected_instead_of_passed` | **任务书要求的回归**：地面已结束的窗口被**拒绝而不是通过** | 有 `jump:ground_probe`；被驱动并被打分的弧 = **0**；观测含 `JUMP_NOT_DRIVEN` 且**不含** `JUMP_ARC_OBSERVED` |
| `evidence_battery::a_monotone_fall_is_not_recorded_as_an_observed_jump` | T15 那种单调自由落体**永不被记成观测到的跳跃** | 被打分的弧 = 0；观测含 `JUMP_NOT_DRIVEN` |
| `evidence_battery::a_jump_driven_from_the_ground_is_recorded_as_an_arc` | **绿方向**：地上起跳被记为弧，且原始件带可复核的读数 | `shows_an_arc=true`、`verdict=JUMP_ARC_OBSERVED`、`rise>0`、`monotone_fall=false` |
| `evidence_battery::an_airborne_start_and_an_unreadable_probe_both_fail_closed` | 空中起跳**与**探针不可读，两条都 fail closed | 两者都被驱动的弧 = 0、都含 `JUMP_NOT_DRIVEN` |
| `evidence_battery::a_jump_window_with_no_rise_is_rejected_too` | 弧规则两半是**分开**的两条判据 | `rise=0.0`、`monotone_fall=false` ⇒ `JUMP_NO_RISE`（只有 `rise>0` 那一半能拒它） |
| `evidence_battery::the_arc_rule_rejects_the_t15_series_and_accepts_a_real_one` | 用 **T15 验收公布的逐点数值**验证规则本身 | 30 点原序列 ⇒ `rise=0.0`、单调、`JUMP_DEGENERATE_FALL`、**不 show_an_arc**；真实弧 ⇒ `rise>0`、非单调、`JUMP_ARC_OBSERVED` |
| `evidence_battery::the_probe_frame_count_matches_the_production_constant` | 夹具用帧数区分「探针」与「被判定窗口」，该帧数必须等于生产常量 | `JUMP_PROBE_FRAMES == JUMP_GROUND_PROBE_FRAMES` |

**回归钉**：左右移动与金币/胜利类的既有断言全部保持绿——`input_replay` 的
`move_right` / `move_right_release` / `move_left` 三个窗口在同一轮里仍各带
`position:neq` 的 `POSITION_ASSERT_PASSED`，`interaction_evidence` 的 `Coins 0→1` 与
`Goal.reached false→true` 未改（§7 的整轮读数）。

### 1.4 与真机威胁的对应

T15 的窗口是**关卡地面在 x≈3411 结束**之后被驱动的。本批的做法：驱动前探针若读到 `y` 在变化
⇒ **不驱动**；即便被驱动，单调下落也**只**记成未观测。两条独立防线都在夹具里各有其红（§6 的植入 p1/p2）。

---

## 2. ② 脱敏：**JSON 键形态**，以及两种计数法的交叉

### 2.1 要做的事与实现

把 `HOH_*` / `DSH_TERM_CMD` 的脱敏从「赋值形」扩到 **JSON 键形**，并纳入先前**未声明的两个名字**
`HOH_TOOLS_POLICY` / `HOH_WORKSPACE`（`src/runtime/secrets.rs`）。

- 新增 `UNDECLARED_HARNESS_ENV_VARS = ["HOH_TOOLS_POLICY", "HOH_WORKSPACE"]`（与既有声明族**分开列**，
  使「DR-82 之前声明了什么」仍可读）与 `redactable_env_vars()`（凭据名 ∪ 声明族 ∪ 未声明族）。
- 新增 `splice_json_keys`：把**键之后的取值**替换为 `<redacted>`，**键、冒号与标点逐字节保留**；
  空串取值（T15 的四个凭据键）**不动**，因为「把空值改写」会报告一次什么都没保护的脱敏。
- `redact_secret_assignments_traced` 现在**只**调用合并入口 `redact_named_assignments_and_keys_traced`：
  两种形态在**同一份 span 列表**里按同一条「真实区间重叠 / 包含吸收」规则合并，DR-72 ③ 的
  「不许产出不可解析 JSON」后检对合并结果只做一次。

### 2.2 🔴 一个由计数交叉发现的**更严重的缺口**（诚实披露，见 §9.4）

我最初只匹配**转义拼写** `\"NAME\"`（键写在 JSON 字符串里的形态）。在做本节要求的**计数交叉**时，
我把两种方法跑在**冻结的真机文件**上，才发现 `runs/smoke-t15/iter-1/traj/*.json` 与
`runs/smoke-t14/…` 里的名字是**真正的对象键**（**未转义**）：那样我的实现会把这些文件报成**干净**，
而它们**原文存活**——正是本轮要消灭的假绿形态。

⇒ 已扩展为**两种编码都扫**（`"NAME"` 与 `\"NAME\"`），并**补了一条针对未转义编码的测试**
（`secret_hygiene::the_unescaped_role_config_dump_is_redacted_too`）。这条补测在实现扩展**之前**
跑过一次、**是红的**（§5 的红基线），扩展后转绿。

### 2.3 两种计数法（**可能不一致**，并解释为何一致或不一致）

**方法 A（原始字节）**：在**编码后的文档**里数字节串 `\"NAME\":`（转义编码）或 `"NAME":`（未转义编码）。
**方法 B（JSON 感知）**：把文档解析成对象，**逐键遍历**并数名字等于目标集合的键。
第三法**naive 守卫生扫描** `(?<![A-Za-z0-9_])NAME=` 也被跑过——它正是 T15 自曝的假绿手法。

**(a) 夹具（转义编码）**：A = B = **64**（12 族 × 4 次转储）。一致，**理由**：该夹具的每一次出现都
落在宿主 JSON 字符串**内部**，这是两种方法**都能看见**的唯一编码；两者是**同一批出现的两种视角**。

**(b) 夹具（未转义编码，= 冻结文件的真实编码）**：A = B = **16**。一致，**理由**：名字是真正的对象键，
原始视图与解码视图看到同一批 16 次出现。

**(c) 冻结真机文件（只读）**：B = **16**，A（转义拼写）= **0** ⇒ **不一致**。**理由**：这些文件的键
**未转义**，所以转义拼写根本不存在。**这个不一致就是上面 §2.2 那个缺口的机械证据**——两法交叉
才把它逼出来。逐名普查（`planner.attempt1.json` 与其 sidecar，`runs/smoke-t15`）：

| 名字 | 出现 |
|---|---|
| `HOH_ARTIFACT_DIR`, `HOH_GAME_ROUTE`, `HOH_HOH_BIN`, `HOH_ITERATION`, `HOH_MODEL_API_KEY`, `HOH_ROLE`, `HOH_RUN_DIR`, `HOH_RUN_ID`, `HOH_SCRATCH_DIR`, `HOH_TOOLS_ENDPOINT`, `HOH_TOOLS_POLICY`, `HOH_VIEW_DIR`, `HOH_WORKSPACE`, `LITELLM_API_KEY`, `MSWEA_MODEL_API_KEY`, `OPENAI_API_KEY` | 各 1 |
| **present = 16 names；total = 16** | |
| `DSH_TERM_CMD`, `HOH_SECRET_PATH`, `PATH`, `Path` | **0（该形态里不存在）** |

四个凭据键的取值是**空串**（与 T15 验收的读数一致）；无任何凭据值。

**(d) naive 守卫法 vs 真实出现（赋值形，冻结文件，只读）**：

| 文件 | naive 守卫法 | 真实出现（不守卫） | 结论 |
|---|---|---|---|
| `planner.attempt1.json` | **1** | 28 | 27 次被吞 |
| `developer.attempt1.json` | **0** | 26 | **全假绿** |
| `tester.attempt1.json` | 15 | 15 | 一致（该文件的出现前面是引号） |

**理由**（T15 披露的陷阱）：JSON 字符串化的转储把 `\n` 的**字母 `n` 紧接在 `NAME=` 之前**，
守卫 `(?<![A-Za-z0-9_])` 因此拒绝真实出现。**这就是「必须两种方法交叉」的原因**：单一方法
（尤其是守卫法）会给出**假绿零**。两法在 `tester` 上一致是**巧合于内容**而非巧合于规则，所以本批
把三种读数都留档。

### 2.4 封印原件仍含原文（可比较性）

测试断言：密封原件**逐字节未改**（`assert_eq!(read(path), original)`），且旁路是
`scrubbed.redacted` 生成的新文件。因此「原件仍含原文形态」的可比较性**保持**。

---

## 3. ③ 纠正 `.godot` 重建机制的说法（**追加式**）

- 触发：DR-81 ④ 曾说「**已在运行的**编辑器不会重建 `.godot`」；`smoke-t15` 实测**削弱**了它——
  本轮**运行中的**编辑器**确实重建了**（11 个文件、`14:05:10–14:30:51`，均在 `13:52:17` 清空之后，
  含 `filesystem_cache10` 911 B），于是那条缓存写失败**根本没出现**（`anchor_line_count=0`、判定 `count=0`）。
- **处置（追加式，原文逐字节未动）**：在 `TASK-DR81-REPORT.md` **末尾追加**
  `# 附：DR-82 ③ 更正（**追加式**，2026-10-02）…`，写明：实测到的两种结果（t14 不重建、t15 重建）、
  **机制未定**（无插桩，保持推断）、以及**仍成立**的代码级事实（`purge_contents` 删整个 `.godot/`、
  `GodotAdapter::initialize` **从不**重建 `.godot`）。
- **没有任何门或判定依赖该假设**：更正文里逐条列表——基建分类只在**该行出现时**生效；时间窗比较
  **出现次数**；`fresh_workspace` 的前置条件在两种结果下都安全。唯一**依赖**它的地方是
  `src/runtime/start_state.rs::fresh_workspace` 的**文档注释**，已改写为实测结论并写明机制未定。
- **机械钉**：`tests/append_only_guard.rs::the_dr81_report_prefix_before_the_dr82_correction_is_frozen`
  钉住更正标题**之前 41,045 字节**的 sha256 = `7834f2d7…8efc8`——**该值正是
  `TASK-DR81-ACCEPTANCE.md` 记的 `report_sha256_at_review`**，所以这条 pin 同时固定了「更正所取代的
  那一版」。此后再改上方原文会直接使该测试变红。

---

## 4. ④ DR81A-2 / A-3 / A-4 与风险(a)

### 4.1 A-2 — 验收来源规则比自己文档更严

`hoh_is_acceptance_report` 的 case 模式是 `*/*.md`（要求**至少一个目录分隔符**），而规则文字与**报错
文字**都说「仓库根相对 `.md`、文件名含 `ACCEPTANCE`」⇒ 仓库根级 `ACCEPTANCE.md` 被**拒绝**，
却收到一条把它描述为合法的报错。

- **选择**：**让实现与文档一致**（任务书给的两条路之一），把 `*/*.md` 改为 `*.md`。
- **未过授权的方向披露**：这**放宽**了接受集一个形状（根级 `.md`）。token 测试不变、
  `/*`（绝对路径）与 `*\*`（反斜杠）仍拒、`.` 仍拒；`*-REPORT.md` 仍因不含 token 而被拒。
  即使是 fail-closed 的一侧，放宽也需明说——上面就是。
- **测试**：`push_gate::a_repo_root_level_acceptance_artifact_is_accepted_as_the_marking_source`
  （正：根级 `ACCEPTANCE.md` 可标记、`verify` 一致、推送成功；**对照**：根级 `NOTES.md` 仍被拒并提到 token）。

### 4.2 A-3 — DR-81 修订报告自相矛盾

机器可读块 `honest_disclosure[3]`（现时态：台账**仍然无效**、**未被手改**）与 §5.4（「其后…当前读数
⇒ exit 0, OK: 42 record(s)」）互斥。

- **处置**：**仅追加**第二个更正节
  `# 附：DR-82 ④（A-3）更正（**追加式**，2026-10-02）…`，给出矛盾表、**本轮只读实测**
  （`verify` ⇒ exit 0、`OK: 48 record(s)`、第 45 行来源已是 `…TASK-SMOKE-T14-ACCEPTANCE.md`）、
  并声明**当前状态以该节为准**；同时**不改机器可读块**（DR-82 的追加式纪律要求块与证据字符串冻结）。
- **本子代理未改 `.git/hoh-accepted-commits.txt`，未推送**；上面是只读观测。
- **测试**：同一条 pin 测试里新增两个断言（A-3 标题存在、含 `OK: 48 record(s)`）。

### 4.3 A-4 — 门窗口两条分支补测

1. **计数增长分支**：`launchable_gate::a_repair_that_reproduces_the_same_line_still_closes_the_gate`。
   夹具让**锚恒为 `[E]`**、**每次判定读数各多一份 `E`**（第 1 次 `[E,E]`、修后第 2 次 `[E,E,E]`）⇒
   **同一行文本、只有出现次数增长**仍然关门。实测观测：
   `2 line(s) reproducible and new in this window; … 1 pre-existing line(s) …; project_defects_new=2`。
   这正是**集合比较会放过**的形态（植入 p6 把它改成集合比较 ⇒ 该测试红）。
2. **锚缺失分支**：`launchable_gate::an_absent_window_anchor_fails_closed`。夹具让**宽读（锚）调用直接失败**
   ⇒ 判定侧 `None` ⇒ **每一行都算新**、关门、触发一次修复。植入 p5 把 `None` 改成 fail-open ⇒ 该测试红。

### 4.4 风险(a) — 窗口**可能掩盖仍然损坏的工程**

- **处置：加一条可执行的记录**（不是写在散文里）。测试
  `launchable_gate::the_window_can_still_open_on_a_project_that_is_broken_on_disk` 构造：磁盘上
  `scripts/project.gd` **确实**仍带冲突声明（`class_name Ground`），而 `project_reload_and_open`
  **没有把该行重新 emit** ⇒ 门**开**。测试断言这份「极限」是可复算的事实：
  `anchor_line_count=1`（锚**确实**带过该行）、`project_defects_new=0`、`pre_existing_lines=0`
  （**什么都没被 dismiss**）、`launchable=true`。
- **为何可接受**：离线批次的窗口**只有锚**这一个基线；**该极限现在被钉住**，所以将来若加「磁盘侧
  可复现探针」，这条测试会**按设计变红**，而不是被悄悄调绿。
- **DR-68 只覆盖 `Function "X()"` 形态**这一点未变；本批未扩展 staleness 规则（不在任务书范围）。

---

## 5. 红基线（**如实区分「真先红」与「植入红」**）

### 5.1 真先红（测试先写、先执行、因缺行为而红）

| 测试 | 红的方式 | 是否真先红 |
|---|---|---|
| `secret_hygiene::the_json_key_shape_of_the_environment_dump_is_redacted_too` | **先写测试**，再把 `splice_json_keys` 的扫描**关闭**（等价于修复前的行为）后运行 ⇒ 红（`HOH_ARTIFACT_DIR ... compact=0 spaced=0`，left 0 / right 4）；随后开启 ⇒ 绿 | **是**（红由**缺行为**造成，且红发生在实现生效之前） |
| `secret_hygiene::the_unescaped_role_config_dump_is_redacted_too` | 该测试**先写、先跑**（当时实现只认转义编码）⇒ **红**（`the sealed trajectory must get a generated sidecar: TreeRedactionReport { rewritten: [], copies: [], refusals: [] }`）；随后把扫描扩到两种编码 ⇒ 绿 | **是** |
| `secret_hygiene::the_json_key_shape_…` 与 `the_unescaped_…` 的**关闭再确认** | 在最终实现上把 `splice_json_keys` 整体关闭，**逐条**再确认两测试都红 | 补充的红证据（不是首红） |

**必须如实标注的一点**：①（跳跃）那七条测试**不是**「先写测试再看它红」的顺序——因为我先实现了
驱动/判定，再写测试并只做过**植入红**。它们的首红是**植入造成的**（§6 的 p1/p2），**不计入真先红**。
④ 的三条门测试同理：首红是**植入红**（p5/p6）。A-2 的 push_gate 测试首红也是**植入红**（p4）。
**没有任何一条测试的「首红」只是编译错误**（本批新增测试在写下时，其引用的符号都已存在；
唯一一次编译失败是我自己诊断期插入的临时调试语句，与交付的测试无关）。

### 5.2 未捕获的编译错误红

**无。** 本批没有「测试先写但实现符号尚不存在」的情形。

---

## 6. 受控植入（**6 处**，各自红自己的测试，逐字节回退）

| # | 文件 | 植入 | 目标测试 | 结果 | 回退 |
|---|---|---|---|---|---|
| p1 | `src/adapter/godot.rs` | `player_is_resting_on_ground` 的谓词恒 `true` ⇒ 空中窗口被驱动 | `evidence_battery::a_jump_window_over_a_gap_is_rejected_instead_of_passed` | **exit 101**，FAILED 0 passed / 1 failed | 逐字节 |
| p2 | `src/adapter/godot.rs` | `shows_an_arc()` 恒 `true` ⇒ `rise=0` 也被记成弧 | `evidence_battery::a_jump_window_with_no_rise_is_rejected_too` | **exit 101** | 逐字节 |
| p3 | `src/runtime/secrets.rs` | 关闭 `splice_json_keys` 的扫描 | `secret_hygiene::the_unescaped_role_config_dump_is_redacted_too` | **exit 101** | 逐字节 |
| p4 | `.githooks/hoh-acceptance-lib.sh` | 把 `*.md` 还原成 `*/*.md` | `push_gate::a_repo_root_level_acceptance_artifact_is_accepted_as_the_marking_source` | **exit 101** | 逐字节 |
| p5 | `src/adapter/godot.rs` | 锚缺失分支改成 fail-open | `launchable_gate::an_absent_window_anchor_fails_closed` | **exit 101** | 逐字节 |
| p6 | `src/adapter/godot.rs` | 时间窗改成**集合比较**而非计数 | `launchable_gate::a_repair_that_reproduces_the_same_line_still_closes_the_gate` | **exit 101** | 逐字节 |

**回退证据**（每次植入后都做，`sha256` + **逐字节 `cmp`**，`plant.py verify` 打印 `cmp_EQUAL=True`）：

- `.githooks/hoh-acceptance-lib.sh`：7,603 B，`ac260ec354650e4c269c63eff4b9befd3d501610fb40d38b427969b17ac045a0`
- `src/adapter/godot.rs`：297,412 B，`cca12db4a49d5f4d582a839d4f0534754890f44de99a6d00fe9fcb3f8c5ae57e`
- `src/runtime/secrets.rs`：78,976 B，`8796f204b6291c2a08b005bb9927dd6a159204d6b2fe97c562f482f60ec4277a`

**如实标注 p5/p6 的红形态**：这两条门测试的红**表现为运行期 harness 的角色序列 panic**，而不是
测试自己的最终断言——
`FakeHarness step #2 expects Developer but the runtime asked for Tester; actual sequence so far: ["planner", "developer", "tester"]`
——因为**被植入的分支改变了门的判定**，判定一变，DR-24 的修复重试就不再被触发，脚本化的
「修复用 Developer」那一步便无人消费。**这是该分支被翻转的直接后果**，所以是对**目标测试**有效的红；
但它不是断言红，读者应知道这个区别。

**一次回退重试（如实记录）**：批量核对植入锚点时，有一次 `restore` 因 Windows 文件锁抛
`OSError: [Errno 22]`，脚本中途退出；**立即重跑 restore 并 verify**，三个文件均 `cmp_EQUAL=True`
且 sha256 与备份一致 ⇒ **最终状态逐字节还原**，没有留下植入。

---

## 7. 门读数（**基线自行复现**）

| 项 | 值 |
|---|---|
| 基线（任务书） | **575 passed / 0 failed / 7 ignored**，`--list` 582 |
| 本批终态 | **589 passed / 0 failed / 7 ignored**，`--list` **596** |
| `cargo test --offline` | **exit 0** |
| `cargo fmt --all --check` | **exit 0** |
| 强制重建 | `target/debug/.fingerprint/hof-rs-*` 用 **Python glob + `shutil.rmtree`** 清 **61** 个；**逐文件** touch `git ls-files '*.rs'` 列出的 **97** 个（**Python 枚举，禁 shell 通配符**；`touched_paths_are_literal=True`） |
| 强制编译行 | `Compiling hof-rs v0.1.0 (F:\moonbit-hof-rs)` |
| 套件耗时 | 1376.0 s |
| 测试名被删 | **0** |
| 新增测试 | **14** 条（575 + 14 = 589；582 + 14 = 596，两条算术都成立） |
| `ignored` 名单 | **未变**：`e0_initialize_workspace` / `e1_single_iteration_smoke` / `e2_project_boots` / `e3_behaviour_is_evidenced` / `e4_verified_claims_are_reproducible` / `e5_qa_did_not_modify_the_artifact` / `e6_report_is_honest`（用 `cargo test -- --list --ignored` 逐名核过） |

**基线复现的一段曲折（如实记录）**：本批**第一次**跑 `cargo test --offline` 时，两条**既有**测试是红的——
`runtime::hygiene::tests::the_terse_round_scratch_names_are_round_litter` 与
`...::the_cleanup_removes_only_the_observed_root_scratch`。根因是**测试二进制陈旧**（crate 源码已被
HEAD 更新过，测试二进制是旧的；我当时的 `cargo build --offline` 只重建 lib，不重建测试二进制）。
按任务书要求做**强制重建**后，**同两条测试转绿**，基线 **575/0/7** 得以复现。
我把这段写出来是因为它影响「基线是否真被复现」的判定，而不是把它掩盖成「一开始就是绿的」。

**新增的 14 条测试**：① 7 条（跳跃）；② 2 条（JSON 键，两种编码）；④ 4 条（A-2 1 条、
A-4 2 条、风险(a) 1 条）；③ 1 条（`append_only_guard` 的 DR-81 pin）。共 14 条。

---

## 8. 禁区自查

| 项 | 读数 | 依据 |
|---|---|---|
| `runs/**` 写入 | **0**（7117 个文件，最新 `14:54:52`，晚于本批边界 `15:02:08` 的文件 **0** 个） | 单遍 `os.scandir` 遍历 + 边界比较 |
| `.workspace/**` | **0 个属于本批**（743 个文件，最新 `15:14:59`） | 唯一新于边界的文件是 `.workspace/fresh-t15/.godot/.gdignore`（`15:14:59`）——**T15 验收（mtime `15:27:34`，早于本批任何写入）已经在 T15A-7 里记录过它**，且本批**未起引擎** |
| `PRD-mario.md` | `4c81c3a9995f0b3afdf01421a0c3be88573cceefc284ce9bafbfda141f0f5c3a` | 与 T15 记录的开工值**逐字节相同** ⇒ **未动** |
| `DECISIONS.md` | `245befb7af292c379c161ddc917e996a54a4dceea5e93c5d0226816efbae4a76` | 同上 ⇒ **未动** |
| `REQUIREMENTS.md` | `298a948929a434a91b9088f4d566b7e387d0cfeb270f86a79d88b006821e0e54` | 未动 |
| `Cargo.toml` / `Cargo.lock` | `e0c4992b…` / `d98fa915…` | **未动**；本批**未加任何依赖** |
| 引擎树 | 二进制 194,216,960 B sha256 `08483088…e9e6a`；嵌套仓 HEAD `fc63af77…`、`git status --porcelain` **空** | 未动 |
| 既有 `.workspace/**` 目录 | **未被本批写入**（见上） | |
| 推送 | `HEAD == origin/master == 199ce37a…`；`origin/master` reflog 最新项是**本批之前**的推送 | **未推送** |
| 仓内新增临时物 | `git status --porcelain` 只有本批的 **10 个已跟踪文件**改动 + **4 个本批之前就存在的**根级 `l.json`/`p2.json`/`pv.json`/`r.json`（T14 残留，mtime `10:14–10:16`，非本批）；无 `.tmp_*` / `tmp_*` / `*.tmp` / `*.bak` | |
| 行尾 | 本批 10 个文件全部 **CR=0 / CRLF=0**（纯 LF） | 逐文件字节统计 |
| `rm -rf` / `git checkout --` 还原 / 未展开变量构造路径 | **均未使用**；植入回退用**字节备份 + `sha256` + `cmp`** | |

---

## 9. 机器可读块的回读证明

- **生成**：`machine_block.py` 用 `json.dumps(block, ensure_ascii=False, indent=2)` 生成并**先落盘**
  到仓外 `machine_block_dr82.json`，13783 B，sha256
  `9dad73998ecf946f58755076adb53898ddea52e6db827bedded7d582c5a06d62`。
- **写入报告**：上面 §0 的 ```` ```json ```` 栅栏之间就是该文件的**逐字节内容**。
- **回读**：写完报告后，脚本按**行锚定栅栏**把块抠出来，`json.loads` 一次，再与落盘文件的
  **UTF-8 字节**比较 ⇒ **逐字节相同、且是唯一一个 `json` 栅栏**（§9 的脚本输出见报告生成终端；
  三个断言：`round_trip_bytes_equal=True`、`json_fences=1`、`loads_ok=True`）。

---

## 10. 遗留风险与未验证项（**严格区分实测 / 推断**）

### 10.1 实测

- 门终态 589/0/7、`--list` 596、exit 0；`fmt` exit 0；**逐字节**回退的三份备份 sha256；6 处植入各自 exit 101。
- 冻结真机文件里 **16 个键形名字**（含两个未声明名）在原件与旁路**都在**；同一批在 t14 里**同形存在** ⇒ **既有向量，非 DR-81 回归**。
- 跳跃两半判据、地面探针、fail-closed、`JUMP_NOT_DRIVEN`、`jump_reading` 均有测试与原始件读数。
- `runs/**` 零写入；PRD/`DECISIONS.md`/`REQUIREMENTS.md`/Cargo/引擎树 sha 未变；未推送。

### 10.2 推断 / 未验证

1. **跳跃修复只被夹具证明**：本批**未起引擎**，所以「在有地面的位置才驱动跳跃」在**真机**上的效果未测；
   真机验证属于下一轮（判据侧已就位：退化窗口会以 `JUMP_NOT_DRIVEN` / `JUMP_DEGENERATE_FALL` 现形）。
2. **`AirborneThenBallistic` 的「落地后重试」未实现**：本批选择**fail closed**（拒绝并记为未观测），
   而不是「巡航回到地面再驱动」。前者是任务书允许的两条路之一；后者作为**非目标**明记在此。
3. **`.godot` 重建机制的归因仍未定**：t14 不重建、t15 重建，**无插桩**；只把说法改为实测结论。
4. **生产脱敏器未施加到冻结的 `runs/**` 文件**：它们是只读证据。我用**独立的 Python 实现**测出缺陷
   及其普查（§2.3），而「生产实现能修好这些文件」是由**走真实入口**的测试（`redact_tree_traced`）
   在等价夹具上证明的；两者之间是**形状等价**，不是同一份数据被执行。
5. **A-2 的放宽**（接受根级 `.md`）在**真实台账/真实推送**上未演练——本批**不推送**；它由
   `push_gate` 的沙箱仓库演练。
6. **两条新门测试的红是 harness-shape red**（§6），不是断言红；已在植入表里标注。
7. 植入 p5/p6 的红**没有**同时验证「正确路径下断言逐条命中」以外的更强性质（例如真实编辑器行为）。

---

## 11. 诚实披露

1. **最重要的自曝**：我**最初实现错了编码**——只匹配转义拼写 `\"NAME\"`。若我照 T15 报告的字面描述
   （`"HOH_GAME_ROUTE": "F:\…"`）写测试并只跑**那个**夹具，它会**绿**，而冻结文件里 16 个键形名字
   会**在旁路里继续原文存活**——正是本任务要消灭的假绿。是**任务书要求的两种计数法交叉**把它逼出来的
   （§2.3(c)）。这条更正**没有**改变交付物的方向，但改变了实现的范围。
2. **基线不是一开始就绿的**（两条 hygiene 测试因**陈旧测试二进制**先红），按任务书**强制重建**后转绿；
   §7 如实写出，而不是把它写成「一开始就绿」。
3. **①（跳跃）与 ④（门）的测试不是真先红**，其首红是**植入红**；§5.1 明说，且声明**没有任何首红只是编译错误**。
4. **p5/p6 的红是运行期角色序列 panic**，不是断言红；§6 明说。
5. **一次植入回退因文件锁失败后重试**；最终 `cmp_EQUAL=True`，但**失败发生过**，§6 明说。
6. **`AirborneThenBallistic` 测试的语义被我改过**：我最初写它是「落地后应重试成功」，但实现选择
   fail closed，于是我把测试改成断言**两条都 fail closed**，并把它登记为**非目标**（§10.2）。
   这是**改了测试以匹配实现**，方向是我主动收窄承诺（更诚实的一侧），但读者应知道这个改动。
7. **未声明的两个名字**（`HOH_TOOLS_POLICY` / `HOH_WORKSPACE`）我按任务书纳入；它们**不含凭据值**。
8. 本批**未**改 `DECISIONS.md`（任务书禁止），因此**没有**在台账里登记 D 条目；所有决策都写在本报告与
   `start_state.rs` 的注释里。若派遣方要台账条目，需由派遣方在其仓库空闲窗口落盘。

---

## 12. 附：本批改动的文件清单

| 文件 | 性质 |
|---|---|
| `src/adapter/godot.rs` | ① 跳跃地面探针 + 弧判据 + `jump_reading` 原始件字段；`JUMP_NOT_DRIVEN` / `JUMP_GROUND_PROBE_FRAMES` / `JUMP_GROUND_EPSILON` |
| `src/runtime/secrets.rs` | ② 两种编码的 JSON 键脱敏、`UNDECLARED_HARNESS_ENV_VARS`、`redactable_env_vars()`、合并入口、共享 span 规则 |
| `src/runtime/start_state.rs` | ③ `fresh_workspace` 文档注释改为实测结论（机制未定） |
| `.githooks/hoh-acceptance-lib.sh` | ④ A-2 `*/*.md` → `*.md`，并更新注释 |
| `tests/evidence_battery.rs` | ① 7 条测试 + `JumpMode` 夹具 |
| `tests/secret_hygiene.rs` | ② 2 条测试（两种编码）+ 两种计数法 |
| `tests/launchable_gate.rs` | ④ A-4 2 条 + 风险(a) 1 条 |
| `tests/push_gate.rs` | ④ A-2 1 条 |
| `tests/append_only_guard.rs` | ③ DR-81 pin + ④ A-3 断言 |
| `.spec/hof-rs/tasks/TASK-DR81-REPORT.md` | ③ 与 ④ A-3 的**追加式**更正（原文逐字节未动；§3 的 pin 钉住） |
