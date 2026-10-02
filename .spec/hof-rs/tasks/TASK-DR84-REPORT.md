# TASK-DR84-REPORT — the jump window runs before every window that consumes the ground; the level's goal position no longer decides whether the jump is grounded

- Role: implementation subagent, no upstream conversation context. **There is no
  `.spec/hof-rs/tasks/TASK-DR84.md`**: this batch was dispatched as a self-contained prompt, which is its
  only and authoritative task. Read first, as required: `TASK-DR83-ACCEPTANCE.md`, `TASK-DR83-REPORT.md`,
  `TASK-DR82-REPORT.md`, `TASK-DR82-ACCEPTANCE.md`, `TASK-SMOKE-T15-REPORT.md`,
  `TASK-SMOKE-T15-ACCEPTANCE.md`, `DECISIONS.md` D289 / D293 / D294.
- Batch kind: **offline**. No engine was started, no round was run, no network call was made; nothing was
  staged, committed or pushed; **not one byte was written under `runs/**`**.
- HEAD at start = HEAD at end = `e56b712da0cbd8f7c4fe3a83bfaaec24315320ae`; `origin/master` holds the same
  value (**nothing pushed**).
- Landing point `F:\moonbit-hof-rs`; every multi-line helper script lives **outside** the repository, in
  `C:\Users\wyl\AppData\Local\Temp\dr84\`.
- Gate headline: **599 passed / 0 failed / 7 ignored, listing 606, `cargo test --offline` exit 0**, with
  `Compiling hof-rs v0.1.0 (F:\moonbit-hof-rs)` on line 1 of the gate log after 61 fingerprint directories
  were removed and all 97 tracked `.rs` paths were touched; `cargo fmt --all --check` exit 0. Baseline
  **594 / 0 / 7, listing 601** reproduced first.
- Changed files (four): `src/adapter/godot.rs`
  `884b43dcd76c678876384a4401ec74b5fdcad570fa28c3513349259295a84ee5` (315,816 B);
  `tests/evidence_battery.rs` `5d5d0c117735af3ae2a41ec2d60fb61b0b917b2fdf3f4880eb300d026396768d` (257,235 B);
  `tests/append_only_guard.rs` `1557ef8d6a8a4758f4306d88f1adb548d5e68e0a4fd64ed0aa38aea6bd316121` (24,657 B);
  `.spec/hof-rs/tasks/TASK-DR82-REPORT.md` `ee88185054acaade384fd47d2c7ae164606e21f65c0dd1969efdda593fbef691`
  (46,014 B). All pure LF.

## 0. Machine-readable verdict

```json
{
  "task": "TASK-DR84",
  "kind": "implementation subagent report (offline batch: no engine, no real round, no network, nothing staged, committed or pushed; nothing written under runs/**)",
  "task_book": "none: this batch was dispatched as a self-contained prompt, which is its only and authoritative task. There is no .spec/hof-rs/tasks/TASK-DR84.md",
  "head": "e56b712da0cbd8f7c4fe3a83bfaaec24315320ae",
  "origin_master": "e56b712da0cbd8f7c4fe3a83bfaaec24315320ae",
  "pushed": false,
  "baseline": {
    "passed": 594,
    "failed": 0,
    "ignored": 7,
    "listed": 601,
    "reproduced_by_me": true,
    "how": "the four DR-84 files were backed up byte-exactly and replaced with their HEAD blobs (git show, read-only; no git checkout --), cargo test --offline then exited 0 with 594/0/7 over 60 result blocks, -- --list counted 601, -- --list --ignored named exactly the seven e0..e6 tests, and the four files were restored from the byte backups with sha256 equality and cmp exit 0 (docs: baseline_run.log, baseline_manifest.json)"
  },
  "gate": {
    "passed": 599,
    "failed": 0,
    "ignored": 7,
    "listed": 606,
    "exit": 0,
    "blocks": 60,
    "fmt_exit": 0,
    "fingerprints_removed_with_python_glob_rmtree": 61,
    "fingerprints_left": 0,
    "tracked_rs_files_touched_individually": 97,
    "touched_paths_are_literal": true,
    "forced_compile_line": "Compiling hof-rs v0.1.0 (F:\\moonbit-hof-rs)",
    "finished_line": "Finished `test` profile [unoptimized + debuginfo] target(s) in 55.35s",
    "tests_removed": 0,
    "new_test_functions": 5,
    "renamed_test_functions": 1,
    "ignored_names_unchanged": [
      "e0_initialize_workspace",
      "e1_single_iteration_smoke",
      "e2_project_boots",
      "e3_behaviour_is_evidenced",
      "e4_verified_claims_are_reproducible",
      "e5_qa_did_not_modify_the_artifact",
      "e6_report_is_honest"
    ],
    "interruption": "none: the forced-rebuild run was NOT cut by the executor cap this time. The whole suite ran in one command; its log carries both the Compiling line (line 1) and the final totals, so build identity is checkable without cross-log inference"
  },
  "items": {
    "reorder": {
      "change": "src/adapter/godot.rs: the `jump` window moved out of step_input_replay into its own battery step `input_jump`, which run() now drives BEFORE step_interaction_evidence, step_input_channel_probe and step_input_replay",
      "principle": "the window that needs a state runs before the windows that consume it - DR-78 3's rule, applied to the ground the jump needs at the battery-step level (DR-83 had applied it only to the windows inside input_replay)",
      "why_it_generalises": "the jump is probed at the position the level starts the player at, so grounding no longer depends on where the goal sits, how far one interaction batch overshoots it, or how long the channel probe walks. It measures nothing about a level and carries no level constant",
      "why_not_a_bound": "a bound on the interaction drive or the channel probe cannot guarantee grounding: the second-or-so of that drive ends on a whole-batch boundary up to 220 px past the goal trigger (INTERACTION_BATCH_FRAMES x FIXTURE_PX_PER_BATCH on the frozen geometry), so a goal inside that span is walked off by the interaction window itself before any probe bound can act. Only running the jump first removes the dependency",
      "road_chosen_why": "it keeps the battery's own semantics readable - one named step per behaviour, the ordering rule as a named list, and the replay pass left with exactly the horizontal windows it names; the bound road would have had to invent a cap on the interaction travel that no shaft of the harness reads"
    },
    "window_bounds_its_own_drive": {
      "change": "src/adapter/godot.rs run_replay_windows: every window releases, inside the game process, the action it pressed, when its own frame sample is complete",
      "why": "the jump step is the only window of its pass, so no successor window exists to drain it; without this a `jump` would stay held through the interaction drive, the channel probe and the horizontal replay",
      "principle": "DR-83's rule for the channel probe (`the drive ends where the reading that justified it ends`) applied to every window; DR-68 3(a)'s clean-input-state rule becomes a property of each window boundary instead of a duty of the next window",
      "test": "evidence_battery::the_jump_step_releases_its_own_action_when_its_reading_is_complete"
    },
    "jump_pass_reads_its_own_channel": {
      "change": "run_replay_windows takes the channel verdict as an Option: the jump pass (which runs before the channel probe) is given None and reads the verdict from its own first injection via semantic_inject_action_detailed",
      "why": "before this the pass gated injection on self.channel.capability, whose default is ActionBindingUnknown; a jump step running first would have been silently not driven. The classification keeps DR-35/DR-54's discipline (the engine's own refusal code AND the ACTION_NOT_BOUND marker), so an unreadable channel stays ACTION_BINDING_UNKNOWN",
      "test": "evidence_battery::green_battery_records_every_step_and_copies_into_the_candidate (the jump step is green in the default fixture) plus the existing input_replay_reports_an_action_that_is_not_bound"
    },
    "ordering_named_list": {
      "change": "src/adapter/godot.rs now names the rule: GROUND_NEEDING_BATTERY_STEP = INPUT_JUMP_STEP_ID and GROUND_CONSUMING_BATTERY_STEPS = [interaction_evidence, input_channel_probe, input_replay]; the ordering test reads those constants off the battery's own record order",
      "why": "the DR-83 pin keyed on the literal action name `move_right` inside the replay pass, so a future ground-consuming window would not have been covered. This is the same shape as COIN_OBSERVING_BATTERY_STEP / COIN_CONSUMING_BATTERY_STEPS",
      "test": "evidence_battery::the_jump_window_is_driven_before_the_windows_that_consume_the_ground + evidence_battery::the_ground_ordering_rule_is_a_named_list_not_a_re_encoded_literal"
    },
    "dr82_prose_correction": {
      "defect": "DR83A-1 (raised from DR82A-1): TASK-DR82-REPORT.md item 2 published real_file_census.names_as_keys_per_file = 16 without saying that a key count is identical before and after a redaction that preserves keys, and without naming the frozen sidecars whose key values are still raw",
      "change": "an APPEND-ONLY correction section was appended to TASK-DR82-REPORT.md (heading `# 附：DR-84 更正（**追加式**，2026-10-02）——第 2 项的键计数不是「取值已处理」的证据`); the 44,184 bytes above it are byte-identical to the reviewed revision (sha256 319397fdb369ea95c63e2eac7d4eaacd25b7825e73313e9afe863f5eb1a8e406)",
      "why_not_sidecar_only": "the qualifier has to sit where the claim is read; even though the DR-76 acceptance prefers a sidecar for acceptance reports, nothing in the repository pins this report's prefix and an append keeps the original bytes verbatim, which the new guard test checks",
      "test": "append_only_guard::the_dr82_census_claim_carries_its_dr84_qualifier (whole-line heading + the qualifier words + the claim still readable above it)"
    }
  },
  "tests": {
    "new": 5,
    "genuine_first_reds": [
      {
        "name": "evidence_battery::a_level_whose_goal_sits_near_the_floor_edge_still_shows_a_grounded_jump_arc",
        "first_red": "exit 101, tests\\common\\mod.rs:867:35 - the run's own helper could not read `.hoh/deterministic/raw/input_jump.json`, because the battery had no jump step: the window was still inside input_replay, after the interaction drive and the channel probe, which is exactly the shape the test forbids",
        "line_note": "the line is from the pre-implementation revision; later edits shifted it, and plant p1 re-reddens the same test at tests\\evidence_battery.rs:4787:10"
      },
      {
        "name": "evidence_battery::the_jump_window_is_driven_before_the_windows_that_consume_the_ground",
        "first_red": "exit 101, tests\\evidence_battery.rs:4814:13 - `the ground-needing window input_jump must run` panicked: GROUND_NEEDING_BATTERY_STEP was absent from the battery's record order"
      },
      {
        "name": "evidence_battery::the_jump_step_releases_its_own_action_when_its_reading_is_complete",
        "first_red": "exit 101, tests\\common\\mod.rs:867:35 - the same missing `raw/input_jump.json`: the step did not exist, so neither did its self-release",
        "line_note": "same pre-implementation anchor as the near-edge test; plant p2 is its red now"
      },
      {
        "name": "evidence_battery::the_jump_windows_ground_probe_precedes_every_horizontal_sample_of_the_run",
        "first_red": "exit 101, tests\\common\\mod.rs:867:35 - the same missing `raw/input_jump.json`"
      },
      {
        "name": "append_only_guard::the_dr82_census_claim_carries_its_dr84_qualifier",
        "first_red": "exit 101, tests\\append_only_guard.rs:455:9 - `the DR-84 correction heading must own a whole line: ... is absent`; the report's census claim still carried no qualifier"
      }
    ],
    "declared_pins": [
      "evidence_battery::the_ground_ordering_rule_is_a_named_list_not_a_re_encoded_literal - the constants and the two window lists exist from the moment the constants were added, so its first run was green; it is a structural pin (a wrong needing-step name or a jump window in the horizontal list reddens it, demonstrated by plant p4)"
    ],
    "adapted_not_removed": [
      "the_input_replay_pass_clears_the_previous_steps_held_action_first -> the_jump_window_clears_the_previous_steps_held_action_first: same claim (the pass's first game-process input call is a release, before the ground probe), pointed at the step that now begins the battery's drive. A rename, not a removal; 0 test functions were removed and the count went 601 -> 606",
      "the_jump_window_is_driven_before_the_windows_that_consume_the_ground: the DR-83 body was replaced by the named-list form; the DR-83 window-level assertion was kept under the new name the_jump_windows_ground_probe_precedes_every_horizontal_sample_of_the_run",
      "seven jump tests now read raw/input_jump.json instead of raw/input_replay.json (the same assertions, the document moved with the window): a_jump_window_over_a_gap_is_rejected_instead_of_passed, a_monotone_fall_is_not_recorded_as_an_observed_jump, a_jump_driven_from_the_ground_is_recorded_as_an_arc, an_airborne_start_and_an_unreadable_probe_both_fail_closed, a_jump_window_with_no_rise_is_rejected_too, a_level_whose_ground_ends_before_the_walk_still_shows_a_grounded_jump_arc, a_level_with_no_usable_ground_reports_the_jump_unobserved",
      "green_battery_records_every_step_and_copies_into_the_candidate now expects input_jump in the step list and reads the jump sentence from the jump step (the moved assertion, not a dropped one)",
      "the_input_replay_injection_is_semantic_not_gdscript, the_input_replay_produces_before_and_after_frames_and_a_positional_assertion: the jump half reads input_jump.json and the positional-assertion count is now 4 (three horizontal windows plus the jump), i.e. stricter than before"
    ],
    "fixture": "JumpMode::Ledge with FIXTURE_LEDGE_X = 6600 is unchanged; the new near-edge level derives its ledge from the fixture's own constants: interaction_drive_end_x() = FIXTURE_SPAWN_X + ceil((FIXTURE_GOAL_TRIGGER_X - FIXTURE_SPAWN_X) / FIXTURE_PX_PER_BATCH) * FIXTURE_PX_PER_BATCH = 6440, the position the goal drive stops at. The jump window is probed at the spawn (x=60) with the reorder, and at 6440 + 30 * 3.6056 = 6548.2 without it"
  },
  "plants": {
    "count": 5,
    "all_reddened_their_own_test": true,
    "all_restored_byte_exact": true,
    "run_on": "src/adapter/godot.rs sha256 884b43dcd76c678876384a4401ec74b5fdcad570fa28c3513349259295a84ee5 (315,816 B), the exact delivered revision the final gate ran on",
    "entries": [
      {
        "id": "p1_jump_step_driven_after_the_interaction_drive_and_the_probe",
        "target": "evidence_battery::a_level_whose_goal_sits_near_the_floor_edge_still_shows_a_grounded_jump_arc",
        "exit": 101,
        "first_failure": "tests\\evidence_battery.rs:4787:10",
        "mutated_sha256": "594e8f94543cc90f195d36db65f0a8bafc27218735f10bc6c2e4c6039eeac6bc",
        "cmp_exit": 0
      },
      {
        "id": "p2_window_does_not_bound_its_own_drive",
        "target": "evidence_battery::the_jump_step_releases_its_own_action_when_its_reading_is_complete",
        "exit": 101,
        "first_failure": "tests\\evidence_battery.rs:4966:5",
        "mutated_sha256": "3d6b08179f90f87f5ddf06223bf4bb8351428d61ccf4cd4879143345583f1aad",
        "cmp_exit": 0
      },
      {
        "id": "p3_ground_probe_fails_open",
        "target": "evidence_battery::a_level_with_no_usable_ground_reports_the_jump_unobserved",
        "exit": 101,
        "first_failure": "tests\\evidence_battery.rs:4687:5",
        "mutated_sha256": "9d987ff8b33a3dcde3512959b8eb90c2082fadb59527f53b4b538b2d66997b42",
        "cmp_exit": 0
      },
      {
        "id": "p4_ground_rule_re_encoded_to_the_wrong_step",
        "target": "evidence_battery::the_ground_ordering_rule_is_a_named_list_not_a_re_encoded_literal",
        "exit": 101,
        "first_failure": "tests\\evidence_battery.rs:4892:5",
        "mutated_sha256": "40efafa224931fcd67b840ffecee52ad07ea594d8e243d2e2b5ce9dd6f60bff0",
        "cmp_exit": 0
      },
      {
        "id": "p5_arc_rule_always_true",
        "target": "evidence_battery::a_jump_window_with_no_rise_is_rejected_too",
        "exit": 101,
        "first_failure": "tests\\evidence_battery.rs:4371:5",
        "mutated_sha256": "6f129c761293ddd9ea7897cb34aea1a745a7480926b76b014a3f3df813b4ac0b",
        "cmp_exit": 0
      }
    ],
    "restore_proof": "each plant restored src/adapter/godot.rs from the byte backup; sha256 back to 884b43dc... and external `cmp` exit 0 for all five"
  },
  "forbidden_zones": {
    "boundary_unix": 1790954845,
    "boundary_note": "the commit time of e56b712, the HEAD this batch started from",
    "runs_new_files": 0,
    "runs_files_walked": 7117,
    "runs_newest": "runs/smoke-t15/evidence/COPY_MANIFEST.txt 2026-10-02 14:54:52 (pre-existing)",
    "workspace_new_files": 0,
    "workspace_files_walked": 743,
    "workspace_newest": ".workspace/fresh-t15/.godot/.gdignore 2026-10-02 15:14:59 1 B (pre-existing, recorded by T15A-7/DR82A/DR83A)",
    "prd_sha256": "4c81c3a9995f0b3afdf01421a0c3be88573cceefc284ce9bafbfda141f0f5c3a",
    "prd_unchanged": true,
    "decisions_sha256": "245befb7af292c379c161ddc917e996a54a4dceea5e93c5d0226816efbae4a76",
    "decisions_unchanged": true,
    "requirements_sha256": "298a948929a434a91b9088f4d566b7e387d0cfeb270f86a79d88b006821e0e54",
    "requirements_unchanged": true,
    "cargo_toml_sha256": "e0c4992bd828729b8514f9cf694925687b726157d45463a636390081a3dadba1",
    "cargo_lock_sha256": "d98fa91565ec72ae998fd9f6fd3838286e287e4baf8020c5114a1e2ac0bfdb36",
    "dependency_added": false,
    "engine_binary_sha256": "08483088a4a2772841cd3b4c916b2d45b3cb6255656cf3951598a86fce7e9e6a",
    "engine_repo_head": "fc63af77c33368c4a1bb839c95d19750554f63a3",
    "engine_repo_porcelain_empty": true,
    "game_written_by_hand": false,
    "pushed": false,
    "line_endings_rewritten": 0,
    "changed_files_all_lf": true,
    "rm_rf_used": false,
    "git_checkout_restore_used": false,
    "paths_built_from_unexpanded_variables": false,
    "git_status": " M .spec/hof-rs/tasks/TASK-DR82-REPORT.md; M src/adapter/godot.rs; M tests/append_only_guard.rs; M tests/evidence_battery.rs; ?? l.json ?? p2.json ?? pv.json ?? r.json (the four untracked root scratch files pre-date this batch)",
    "test_suite_sidecar_note": "tests/round_artifacts_sidecar.rs rewrites .spec/hof-rs/tasks/TASK-SMOKE-T10-evidence/analysis/redaction_defect.redacted.txt on every cargo test; git diff shows no diff for it, so the rewrite is byte-identical"
  },
  "false_confirmations": {
    "arc_with_no_preceding_ground_probe": "not made possible: the probe is taken inside the jump window's own iteration, before the injection, and jump_reading is written only for a window whose injection was accepted (jump_driven). Two tests assert the probe is present in the same document as the reading",
    "injection_the_engine_refused": "not made possible: the new None-channel path classifies the refusal and skips the window (needs_p3, ok=false, no jump_reading); a refused jump can never be scored",
    "the_engines_position_assertion_alone": "unchanged: POSITION_ASSERT_PASSED is still necessary and insufficient, and this batch adds no criterion anywhere",
    "a_produced_level_that_jumps_in_mid_air": "not made possible: the fail-closed predicate player_is_resting_on_ground is byte-identical, and plant p3 shows that weakening it reddens a_level_with_no_usable_ground_reports_the_jump_unobserved. The two-frame flat-y proxy can still be fooled at an apex or on a moving platform (pre-existing risk, unchanged here)",
    "new_shape_this_batch_could_introduce": "the jump window now runs at the scene's first frames, so a level that spawns the player a few pixels above its floor would be refused (honest JUMP_NOT_DRIVEN) where the old order let it settle during the drive. No engine ran, so this is unmeasured; it fails closed, never open"
  },
  "residual_risks": {
    "measured": [
      "the offline gate on the delivered tree: 599 passed / 0 failed / 7 ignored, listing 606, 60 result blocks, exit 0, with the Compiling line and Finished 55.35s in the same log after 61 fingerprint directories were removed and all 97 tracked .rs paths touched",
      "the pre-DR-84 baseline: 594 / 0 / 7, listing 601, exit 0, reproduced by reverting the four files to HEAD blobs and restoring them byte-exactly (sha256 + cmp exit 0)",
      "the five plants: each reddened its own test at the published line, and each restore was byte-exact",
      "zero files newer than the batch boundary under runs/** (7117 walked) and .workspace/** (743 walked); every frozen hash unchanged; pure LF in all four changed files; nothing pushed",
      "the near-edge fixture arithmetic: interaction_drive_end_x() = 6440, the probe's 30-frame walk = 108.17 px, so the same level is refused with the old order and grounded with the reorder"
    ],
    "inferred": [
      "that on a real level the engine's is_on_floor() holds at the position the level spawns the player at, so the two-frame probe certifies it and the jump is driven from the ground moving first. No engine ran, so this is an inference from the fixture's model, not a measurement",
      "that a real player is settled within the first frames of a level. If a level spawns the player above its floor, the honest outcome is JUMP_NOT_DRIVEN",
      "that the per-window in-game release does not disturb real physics: the frozen player.gd zeroes velocity.x when the axis reads 0, and a release through this API was observed taking effect in smoke-t15 (post-jump:reset x constant to twelve significant figures), but the release-after-every-window shape is new",
      "that writing the jump window's raw document as its own step does not confuse any downstream consumer: no repository reader was found that keys on `input_replay` for the jump reading, but a real round's Tester reads the battery artifact and could assume one document per criterion"
    ],
    "unverified": [
      "everything engine-side: the probe, the arc rule, the reorder and the self-release have never run against a live game process",
      "whether a real round can still find the jump undriven: YES in three shapes - (i) a level that spawns the player unsupported or still falling (the probe refuses, honestly); (ii) an engine that answers the two-frame sample with a moving y for float-noisy reasons; (iii) a channel that refuses the jump injection before the probe has classified it, which is now recorded from the jump step's own injection. In every one of those shapes the harness reports JUMP_NOT_DRIVEN and scores no arc; criterion 3 would then still not be met, and the failure would be visible rather than a false pass",
      "the pre-fix first-red line numbers: they were captured before the implementation and the later edits shifted them; the plants re-redden the same tests on the final bytes",
      "the fixture's Ledge physics is a step function of x, not physics"
    ]
  },
  "machine_block": {
    "generator": "json.dumps(..., ensure_ascii=False, indent=2)",
    "written_outside_the_repository": "C:\\Users\\wyl\\AppData\\Local\\Temp\\dr84\\machine_block_dr84.json",
    "round_trip_verified": true
  }
}
```
## 0. What this file is

Implementation subagent report for the **DR-84** offline batch, written by a fresh subagent with no
upstream conversation context. There is **no `.spec/hof-rs/tasks/TASK-DR84.md`**: this batch was
dispatched as a self-contained prompt, which is its only and authoritative task. The machine-readable
block above was produced by `json.dumps(..., ensure_ascii=False, indent=2)`, written **first** to
`C:\Users\wyl\AppData\Local\Temp\dr84\machine_block_dr84.json` (outside the repository), parsed back
with `json.loads`, re-serialised and compared byte-for-byte (`machine_block_round_trip=True`).

The batch is **offline**: no engine was started, no round was run, no network call was made; nothing
was staged, committed or pushed; **not one byte was written under `runs/**`**. HEAD at start = HEAD at
end = `e56b712da0cbd8f7c4fe3a83bfaaec24315320ae`; `origin/master` holds the same value.

**Headline.** The DR-83 acceptance said plainly that its reorder does **not** close criterion 3: the
interaction drive and the channel probe still ran before `input_replay`, and together they could carry
the player a whole interaction batch plus the probe's own sample past the goal, so a level whose goal
sits near its floor's edge still lost the ground before the jump and was honestly reported
`JUMP_NOT_DRIVEN`. This batch closes that by applying **the same ordering rule one level up**: the jump
window is now a battery step of its own, `input_jump`, and `run()` drives it **before every window that
consumes the ground** — `interaction_evidence`, `input_channel_probe`, `input_replay`. The rule is a
named list (`GROUND_NEEDING_BATTERY_STEP` / `GROUND_CONSUMING_BATTERY_STEPS`), and the pin that reads it
is no longer keyed on a literal action name.

## 1. What was reordered, and on what principle

**Principle, not a special case.** DR-78 ③ pinned the rule "the window that needs a state runs before the
windows that consume it" for the coin counter (`COIN_OBSERVING_BATTERY_STEP` before
`COIN_CONSUMING_BATTERY_STEPS`, pinned by
`the_coin_observing_window_runs_before_every_consuming_window`). DR-83 applied it one level down, to the
windows inside `input_replay`. This batch applies it at the battery-step level, to the state the jump
needs: the ground.

**Why the jump must be first, not merely earlier.** The ground-consuming steps are not merely "later";
the *interaction* drive is itself one of them. It holds `move_right` for one-second batches and only
reads the goal flag **after** a whole batch, so it stops on a batch boundary up to
`INTERACTION_BATCH_FRAMES × FIXTURE_PX_PER_BATCH` = 220 px past the goal trigger. On the new near-edge
fixture the goal drive stops at `interaction_drive_end_x()` = 6440; the channel probe's 30-frame sample
then adds `30 × FIXTURE_REPLAY_PX_PER_FRAME` = 108.17 px. Any level whose floor ends inside those ~108 px
— and, for a goal closer to its edge, inside the interaction's own 220 px overshoot — lost the ground
even with DR-83's release and reorder. The jump window is the one window whose evidence needs the ground;
running it **before all of them** removes the dependency on the goal's position altogether: the probe is
taken at the position the level itself starts the player at.

**The road not taken, and why.** The prompt offered a second road: bound the interaction drive and the
channel probe. It was rejected as *insufficient*, not as inelegant: a bound can only shorten a drive that
has already been decided by a batch boundary, and the interaction window's own overshoot is up to a whole
batch. A cap that moved with the goal would be a new special case derived from a level reading the
harness does not take; a cap that did not move would be a tuned constant, which the prompt forbids. The
reorder needs no bound at all, keeps one named step per behaviour, and leaves `input_replay` with exactly
the three horizontal windows it names. Since the two roads do not both close the criterion, this is the
choice that satisfies it.

**What moved, exactly.**

* `step_input_replay` was refactored into a reusable pass, `run_replay_windows(step_id, supports,
  windows, known_channel)`. Two thin wrappers call it: `step_input_jump` (one window: `jump`) and
  `step_input_replay` (three windows: `move_right`, `move_right_release`, `move_left`, now the named
  `REPLAY_HORIZONTAL_WINDOWS`). The loop body, the arc rule, the ground probe and every semantic call are
  the same code, not a copy.
* `run()` now drives `step_input_jump()` **first** of the driving steps, before `step_interaction_evidence`,
  `step_input_channel_probe` and `step_input_replay`. The coin rule is untouched: the observing window
  still runs before the probe and the horizontal pass, which are the windows that sweep coins. The jump
  window drives only `jump`, so it consumes neither coins nor ground.
* The jump pass runs before the channel probe, so it cannot be handed the probe's verdict. It is given
  `None` and reads the channel from **its own first injection** (`semantic_inject_action_detailed`,
  classified with the engine's own refusal code **and** the `ACTION_NOT_BOUND` marker — DR-35/DR-54's
  discipline, so an unreadable channel stays `ACTION_BINDING_UNKNOWN` and is never downgraded to "the
  action does not exist").
* **A window bounds its own drive.** The jump window is the only window of its pass, so no successor
  window exists to release what it pressed; the pass now releases, inside the game process, the action it
  pressed when its own frame sample is complete — DR-83's rule for the channel probe applied at the window
  level. This also makes DR-68 ③(a)'s clean-input-state rule a property of **each** window boundary rather
  than a duty of the next window.

## 2. Nothing was weakened

| rule | status |
|---|---|
| `JumpReading::shows_an_arc` = `rise > 0.0 && !monotone_fall` | **byte-identical**; plant p5 (`true` unconditionally) reddens `a_jump_window_with_no_rise_is_rejected_too` at `tests\evidence_battery.rs:4371:5` |
| `player_is_resting_on_ground` (fail closed on `None`, on fewer than two samples, and on any `y` moving by more than `JUMP_GROUND_EPSILON`) | **byte-identical**; plant p3 (fail open) reddens `a_level_with_no_usable_ground_reports_the_jump_unobserved` at `:4687:5` |
| `JUMP_NOT_DRIVEN` for a window the probe refuses, with **no** `jump_reading` | unchanged and still tested (same test, and the two airborne/unreadable modes) |
| every criterion | unchanged; no criterion text was touched |
| `.spec/hof-rs/PRD-mario.md` (byte-frozen product requirements) | `4c81c3a9…5c3a`, **untouched** |
| `DECISIONS.md` / `REQUIREMENTS.md` / `Cargo.toml` / `Cargo.lock` | `245befb7…a76` / `298a9489…` / `e0c4992b…` / `d98fa915…`, all untouched, **no dependency added** |
| any game | **none written by hand**; nothing under `runs/**` or `.workspace/**` is newer than the batch boundary |
| tests | 0 test functions removed; 601 → 606 listing (+5 new, 1 rename, net +5); ignored stays exactly the seven `e0..e6` names |

The one adaptation that changes a test's **name** is disclosed in the machine block: DR-83's
`the_input_replay_pass_clears_the_previous_steps_held_action_first` becomes
`the_jump_window_clears_the_previous_steps_held_action_first`, with the same claim pointed at the step
that now begins the battery's drive. The DR-83 ordering pin's name is **kept**
(`the_jump_window_is_driven_before_the_windows_that_consume_the_ground`) and its body now reads the named
constants; the old window-level assertion survives as
`the_jump_windows_ground_probe_precedes_every_horizontal_sample_of_the_run`.

## 3. Tests — genuine first reds, declared pins, and the fixture

All tests run through the real entry points (`run_battery` → the real `Orchestrator` + `godot_adapter`,
with only the MCP transport replaced by `FixtureChannel`) and read the raw documents the production
adapter wrote.

### 3.1 Genuine first reds (written and run **before** the production change, inherited constants only)

| test | first red |
|---|---|
| `a_level_whose_goal_sits_near_the_floor_edge_still_shows_a_grounded_jump_arc` | exit 101, `tests\common\mod.rs:867:35` — the run's helper could not read `.hoh/deterministic/raw/input_jump.json`: the battery had no jump step, the window was still inside `input_replay` after the interaction drive and the probe. Plant p1 re-reddens this test on the final bytes (`tests\evidence_battery.rs:4787:10`) |
| `the_jump_window_is_driven_before_the_windows_that_consume_the_ground` | exit 101, `tests\evidence_battery.rs:4814:13` — `the ground-needing window input_jump must run`: the step was absent from the record order |
| `the_jump_step_releases_its_own_action_when_its_reading_is_complete` | exit 101, `tests\common\mod.rs:867:35` — the same missing document; the step, and therefore its self-release, did not exist |
| `the_jump_windows_ground_probe_precedes_every_horizontal_sample_of_the_run` | exit 101, `tests\common\mod.rs:867:35` — same missing document |
| `append_only_guard::the_dr82_census_claim_carries_its_dr84_qualifier` | exit 101, `tests\append_only_guard.rs:455:9` — the correction heading was absent; the census claim carried no qualifier |

The line numbers are from the **pre-implementation** revision (later edits shifted them, and the
pre-fix reds file was overwritten by the post-fix verification run); the claim being made is the
mechanism, and the plants re-demonstrate it on the final bytes. **No first red was a compile error** —
the constants had been added first (so the tests compile) but the step, the order and the prose did not
exist, which is why every red is a missing-behaviour failure.

### 3.2 Declared pin

`the_ground_ordering_rule_is_a_named_list_not_a_re_encoded_literal` is green from its first run (the
constants and the two window lists exist as soon as the constants were added). It is a **structural**
pin, not a behavioural one, and it is load-bearing: plant p4 (needing-step renamed to the replay step)
reddens it at `tests\evidence_battery.rs:4892:5`.

### 3.3 The near-edge fixture is derived, not tuned

`interaction_drive_end_x()` computes the interaction drive's stop from the fixture's own constants:
`FIXTURE_SPAWN_X + ceil((FIXTURE_GOAL_TRIGGER_X − FIXTURE_SPAWN_X) / FIXTURE_PX_PER_BATCH) ×
FIXTURE_PX_PER_BATCH` = `60 + 29 × 220` = **6440**. The new test builds the `Ledge` level with
`with_ledge(interaction_drive_end_x())`, i.e. the floor ends exactly where the goal drive stops. With the
reorder the jump is probed at the spawn (`x = 60`); without it the probe would read `6440 + 108.17 =
6548.17 > 6440`, a fall — which is exactly what DR-83's limit described. Nothing here is read back from a
level; the ledge is a function of the fixture's own model.

## 4. Controlled plants — five, each reddening its own test, each restored byte-exactly

All plants ran on the **delivered** revision, `src/adapter/godot.rs`
`884b43dcd76c678876384a4401ec74b5fdcad570fa28c3513349259295a84ee5` (315,816 B) — the same file the final
gate compiled.

| # | plant | target test | result | restore |
|---|---|---|---|---|
| p1 | drive `input_jump` **after** the interaction drive and the probe (the pre-DR-84 order) | `a_level_whose_goal_sits_near_the_floor_edge_still_shows_a_grounded_jump_arc` | exit 101, `tests\evidence_battery.rs:4787:10` | sha256 = `884b43dc…`, `cmp` exit 0 |
| p2 | drop the per-window in-game release | `the_jump_step_releases_its_own_action_when_its_reading_is_complete` | exit 101, `:4966:5` | sha256 = `884b43dc…`, `cmp` exit 0 |
| p3 | make `player_is_resting_on_ground` accept every non-empty series (fail **open**) | `a_level_with_no_usable_ground_reports_the_jump_unobserved` | exit 101, `:4687:5` | sha256 = `884b43dc…`, `cmp` exit 0 |
| p4 | re-encode the rule: `GROUND_NEEDING_BATTERY_STEP = INPUT_REPLAY_STEP_ID` | `the_ground_ordering_rule_is_a_named_list_not_a_re_encoded_literal` | exit 101, `:4892:5` | sha256 = `884b43dc…`, `cmp` exit 0 |
| p5 | make `shows_an_arc` unconditionally `true` | `a_jump_window_with_no_rise_is_rejected_too` | exit 101, `:4371:5` | sha256 = `884b43dc…`, `cmp` exit 0 |

Every plant is a byte-exact literal replacement with exactly one anchor occurrence, followed by a restore
from a byte backup verified with `sha256` and the external `cmp` (`plants_result.json`, `plants_run2.log`).
No plant was left in the tree. This plant set was run **twice**: once on the revision before the Playbook
doc-table row was added, and again on the final bytes — the second run is the published one.

## 5. Gate

| item | value |
|---|---|
| baseline reproduced first | **594 passed / 0 failed / 7 ignored**, listing **601**, `cargo test --offline` exit 0, 60 blocks. Reproduced by replacing the four DR-84 files with their HEAD blobs (`git show`, read-only), running the suite, and restoring them byte-exactly (`sha256` equality + `cmp` exit 0 for all four) |
| final | **599 passed / 0 failed / 7 ignored**, listing **606**, exit 0, **60** result blocks, no `FAILED` and no `panicked` line anywhere in the log |
| delta | **+5 tests, 0 removed**; listing 601 → 606; ignored count 7 unchanged, ignored names exactly the seven `e0..e6` |
| `cargo fmt --all --check` | **exit 0** |
| forced rebuild | `target/debug/.fingerprint/hof-rs-*` removed with Python `glob` + `shutil.rmtree` (**61**, 0 left); every path from `git ls-files '*.rs'` touched individually (**97**, `touched_paths_are_literal=True`; no shell wildcard, no path built from an unexpanded variable) |
| forced compile line | `Compiling hof-rs v0.1.0 (F:\moonbit-hof-rs)` — **line 1** of `gate_run.log`, followed by `Finished \`test\` profile [unoptimized + debuginfo] target(s) in 55.35s` |
| executor cap | **not hit this time.** The forced-rebuild run completed in a single command, so the log carries both the `Compiling` line and the final totals and build identity needs no cross-log inference |

## 6. The two follow-ups the DR-83 acceptance left

**(a) The prose defect it reclassified (DR83A-1 ← DR82A-1).** The DR-82 report's item 2 published
`real_file_census.names_as_keys_per_file = 16` with two methods that both count **key occurrences**. This
batch **appends** a correction to `TASK-DR82-REPORT.md` (never an in-place edit):

* a key count is identical before and after a redaction that preserves the key and replaces only the
  value — the out-of-repository contrast gives **keys 3 vs 3** while **values 3 vs 0** in both encodings
  — so "16" is not evidence that a value was handled; the value-aware count (`raw = 0`) is;
* the frozen `runs/smoke-t15/iter-1/traj/*.redacted.json` sidecars still carry the raw values behind
  those keys (`keys_raw = 12`, `keys_redacted = 0`, plus the assignment form of the two newly declared
  names), so this is a **named, accepted leftover**, not something this batch repaired;
* the 44,184 bytes above the correction heading are byte-identical to the reviewed revision
  (`319397fdb369ea95c63e2eac7d4eaacd25b7825e73313e9afe863f5eb1a8e406`), which the new guard test checks
  by whole-line offset.

**(b) The ordering pin generalised.** The DR-83 form keyed on the literal action name `move_right`
*inside* the replay pass, so a future ground-consuming window would not have been covered. The rule is now
two named constants plus a test that reads them off the battery's own record order — the same shape as
`COIN_OBSERVING_BATTERY_STEP` / `COIN_CONSUMING_BATTERY_STEPS`, and the structural pin (3.2) keeps the list
honest.

## 7. Forbidden-zone self-check

| item | reading | basis |
|---|---|---|
| `runs/**` writes | **0** files newer than the boundary `1790954845`; 7117 walked; newest `runs/smoke-t15/evidence/COPY_MANIFEST.txt` 2026-10-02 14:54:52 (pre-existing) | `forbidden_scan.py` (single `os.walk`) |
| `.workspace/**` writes | **0** newer; 743 walked; newest `.workspace/fresh-t15/.godot/.gdignore` 2026-10-02 15:14:59, 1 B (pre-existing, recorded by T15A-7/DR82A/DR83A) | same scan |
| `PRD-mario.md` | `4c81c3a9…5c3a`, unchanged | `sha256sum` |
| `DECISIONS.md` / `REQUIREMENTS.md` | `245befb7…a76` / `298a9489…`, unchanged — **`DECISIONS.md` was not modified by this batch** | `sha256sum` |
| `Cargo.toml` / `Cargo.lock` | `e0c4992b…` / `d98fa915…`, unchanged; **no dependency added** | `sha256sum` |
| engine | binary 194,216,960 B `08483088…e9e6a`; nested repo HEAD `fc63af77…`, `git status --porcelain` empty | `sha256sum` + `git -C godot-mcp/godot status` |
| push | `HEAD == origin/master == e56b712d…`, **nothing staged, committed or pushed** | `git rev-parse`, `git status` |
| line endings | all four changed files **CR = 0 / CRLF = 0** (pure LF) | byte census |
| repository status | only the four intended files modified; the four untracked root scratch files (`l.json`, `p2.json`, `pv.json`, `r.json`) pre-date this batch | `git status --porcelain` |
| the suite's own sidecar write | `tests/round_artifacts_sidecar.rs` rewrites `TASK-SMOKE-T10-evidence/analysis/redaction_defect.redacted.txt` byte-identically on every run; `git diff` shows no diff | `git diff` |
| `rm -rf` / `git checkout --` / unexpanded-variable paths | **none used**; restores came from byte backups with `sha256` + `cmp`; all helper scripts live outside the repository (`C:\Users\wyl\AppData\Local\Temp\dr84\`) | plant and baseline scripts |

## 8. Residual risks — measured vs inferred

**Measured** (reproducible from this batch's own instruments): the offline gate on the delivered tree
(599/0/7, listing 606, exit 0, 60 blocks, `fmt` exit 0, 61 fingerprints removed, 97 literal paths
touched, the `Compiling` line and `Finished` in the same log); the pre-DR-84 baseline 594/0/7 with
listing 601 and the byte-exact revert/restore; the five plants' reds at their published lines and their
byte-exact restores; zero writes past the boundary under `runs/**` and `.workspace/**`; every frozen hash
unchanged; pure LF; nothing pushed; and the near-edge arithmetic (6440 vs 6548.17).

**Inferred** (stated as such, no engine): that a real player standing at a real level's spawn is
certified by the two-frame probe so the jump is driven from the ground; that the per-window in-game
release does not disturb real physics; that writing the jump reading in its own raw document confuses no
downstream reader.

**Can a real round still find the jump undriven? Yes**, in three shapes, and in all three the harness
says so honestly rather than scoring an arc:

1. **A level that spawns the player unsupported or still falling.** The probe is now taken at the
   scene's first frames, so a level that drops the player a few pixels onto its floor — or spawns it in
   the air — is refused, where the old order let the player settle during the drive. Outcome:
   `JUMP_NOT_DRIVEN`, no `jump_reading`, no arc. Honest, but criterion 3 would not be met.
2. **A probe the engine answers with a moving `y` for float-noisy reasons.** Same outcome. The
   two-frame flat-`y` proxy is unchanged and still brittle by design.
3. **A channel that refuses the jump injection.** The jump step now classifies that refusal itself: a
   `-32602` + marker refusal is `ACTION_NOT_BOUND` + P3 with no reading, and any other failure is
   `ACTION_BINDING_UNKNOWN` with no reading. Same honest outcome.

The old pre-replay failure shape — *the interaction drive and the channel probe walked the player off a
floor whose goal was near its edge* — is **removed by construction**: those steps cannot run before the
jump any more, and the ordering is pinned by a named list.

## 9. False confirmations: could this change make one look like a pass?

* **An arc with no preceding ground probe** — no. The probe is taken inside the jump window's own
  iteration before the injection, and a `jump_reading` is written only for a window whose injection was
  accepted (`jump_driven`). Two tests assert the probe and the reading live in the same document.
* **An injection the engine refused** — no. The new `None`-channel path classifies the refusal and skips
  the window (`needs_p3`, `ok = false`, no `jump_reading`); a refused jump can never be scored.
* **The engine's position assertion alone** — unchanged: `POSITION_ASSERT_PASSED` remains necessary and
  insufficient, and no criterion moved.
* **A produced level that jumps in mid-air** — no. `player_is_resting_on_ground` and the arc rule are
  byte-identical, and plant p3/p5 show that weakening either reddens a test. The pre-existing
  false-positive shape (two flat frames at a jump apex, or a moving platform) is unchanged — but note
  that the jump window now runs **first**, so an apex from a previous jump cannot precede it.
* **The one shape this batch could introduce** is shape (1) of §8: an unsettled spawn is now refused
  where it used to be driven. That is a **false negative**, not a false positive — the failure direction
  the discipline is supposed to have.

## 10. Files changed

| file | nature |
|---|---|
| `src/adapter/godot.rs` | DR-84: `INPUT_JUMP_STEP_ID`, `GROUND_NEEDING_BATTERY_STEP`, `GROUND_CONSUMING_BATTERY_STEPS`, `JUMP_REPLAY_FRAMES`, `REPLAY_HORIZONTAL_WINDOWS`; `step_input_replay` refactored into `run_replay_windows` + `step_input_jump` / `step_input_replay` wrappers; `run()` drives the jump step first; the pass reads its own channel when it runs before the probe; every window releases its own action when its reading is complete; the Playbook step table gains an `input_jump` row and `input_replay`'s row no longer claims the jump |
| `tests/evidence_battery.rs` | `jump_calls` + `interaction_drive_end_x` helpers; four new tests (near-edge grounded arc, the named-list ordering pin, the structural constant pin, the jump self-release) plus the renamed window-level order test; seven jump tests and two mixed tests read `raw/input_jump.json` for the jump half |
| `tests/append_only_guard.rs` | the DR-82 report + DR-84 correction heading constants and `the_dr82_census_claim_carries_its_dr84_qualifier` |
| `.spec/hof-rs/tasks/TASK-DR82-REPORT.md` | **append-only**: the DR-84 correction of the census claim (the 44,184 bytes above it are byte-identical) |
