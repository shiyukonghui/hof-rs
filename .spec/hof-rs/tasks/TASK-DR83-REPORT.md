# TASK-DR83-REPORT — bound the drive: the jump window is driven before the windows that consume the ground, from a clean input state, and the probe bounds its own drive

- Role: implementation subagent, no upstream conversation context. **There is no `.spec/hof-rs/tasks/TASK-DR83.md`**: this batch was dispatched as a self-contained prompt, and that prompt is its only and authoritative task. Read first, as required: `TASK-SMOKE-T15-REPORT.md`, `TASK-SMOKE-T15-ACCEPTANCE.md`, `TASK-DR82-REPORT.md`, `TASK-DR82-ACCEPTANCE.md`, `TASK-DR82.md`, `DECISIONS.md` D289 / D293 / D294.
- Batch kind: **offline**. No engine was started, no round was run, no network call was made; nothing was staged, committed or pushed; **not one byte was written under `runs/**`**.
- HEAD at start = HEAD at end = `12c6e0ffcc368b74847c8d36449d1cb4e1d54ba4`; `origin/master` holds the same value (**nothing pushed**).
- Landing point `F:\moonbit-hof-rs`; every multi-line helper script lives **outside** the repository, in `C:\Users\wyl\AppData\Local\Temp\dr83\`.
- Gate headline: **594 passed / 0 failed / 7 ignored, listing 601, `cargo test --offline` exit 0** (baseline 589 / 0 / 7, listing 596, reproduced first); `cargo fmt --all --check` exit 0.

## 0. Machine-readable verdict

```json
{
  "task": "TASK-DR83",
  "kind": "implementation subagent report (offline batch: no engine, no real round, no network, nothing pushed; nothing written under runs/**)",
  "task_book": "none: this batch was dispatched as a self-contained prompt, which is its only and authoritative task. There is no .spec/hof-rs/tasks/TASK-DR83.md",
  "head": "12c6e0ffcc368b74847c8d36449d1cb4e1d54ba4",
  "origin_master": "12c6e0ffcc368b74847c8d36449d1cb4e1d54ba4",
  "pushed": false,
  "baseline": {
    "passed": 589,
    "failed": 0,
    "ignored": 7,
    "listed": 596,
    "reproduced_by_me": true,
    "how": "cargo test --offline exit 0 on the pristine HEAD; cargo test -- --list reports 596 ': test' lines; cargo test -- --list --ignored reports exactly the seven e0..e6 names, so 596 - 7 = 589 passed"
  },
  "gate": {
    "passed": 594,
    "failed": 0,
    "ignored": 7,
    "listed": 601,
    "exit": 0,
    "blocks": 60,
    "fmt_exit": 0,
    "fingerprints_removed_with_python_glob_rmtree": 61,
    "tracked_rs_files_touched_individually": 97,
    "touched_paths_are_literal": true,
    "forced_compile_line": "Compiling hof-rs v0.1.0 (F:\\moonbit-hof-rs)",
    "tests_removed": 0,
    "new_tests": 5,
    "ignored_names_unchanged": [
      "e0_initialize_workspace",
      "e1_single_iteration_smoke",
      "e2_project_boots",
      "e3_behaviour_is_evidenced",
      "e4_verified_claims_are_reproducible",
      "e5_qa_did_not_modify_the_artifact",
      "e6_report_is_honest"
    ],
    "two_log_disclosure": "the executor caps one foreground command at 10 minutes; the forced-rebuild run (gate_run.log) was killed by that cap after 270 passing tests with 0 failures, and the full suite was then re-run to completion (gate_run2.log, 594/0/7, exit 0) on the same build - the two changed files' sha256 are identical across the two runs, so the Compiling line lives in the first log, not the second"
  },
  "items": {
    "reorder": {
      "change": "src/adapter/godot.rs step_input_replay: the jump window is driven first, before move_right / move_right_release / move_left",
      "principle": "the window that needs a state runs before the windows that consume it - the rule DR-78 3 already pinned for the coin-observing window, applied to the ground the jump needs",
      "why_it_generalises": "it orders the battery's own windows by what they need and what they consume; it measures or guesses nothing about a level, and holds for any level whose floor can end",
      "test": "evidence_battery::the_jump_window_is_driven_before_the_windows_that_consume_the_ground"
    },
    "clean_state": {
      "change": "src/adapter/godot.rs step_input_replay: JUMP_STALE_ACTIONS are released inside the game process before the jump window's ground probe",
      "principle": "DR-68 3(a) - every direction is tested from a clean game input state; INTERACTION_STALE_ACTIONS already applies it to the window that observes the coin counter",
      "why_it_generalises": "a window that begins a pass must not depend on the step before it having been bounded",
      "test": "evidence_battery::the_input_replay_pass_clears_the_previous_steps_held_action_first"
    },
    "probe_bounds_its_own_drive": {
      "change": "src/adapter/godot.rs step_input_channel_probe: the probe releases PROBE_ACTION when its own frame sample is complete (released_after_probe, disclosed in the step's evidence note)",
      "why": "smoke-t15 measured the player drifting 3389.35 -> 3411.35 between the probe's last sample and the next step's first one, with the floor's last supported centre at 3412; the walk was bleeding out of the window that produced it",
      "why_it_generalises": "the bound is the probe's own reading, not a distance derived from a level",
      "test": "evidence_battery::the_channel_probe_releases_its_own_drive_when_its_reading_is_complete"
    },
    "census": {
      "question": "is the count the acceptance flagged (DR82A-1) a repository counting helper, or report prose?",
      "finding": "report prose. TASK-DR82-REPORT.md item 2 publishes real_file_census.names_as_keys_per_file = 16 and a two-method table, and both count key occurrences, which the fix preserves by design (the key is not the span). A search for census / keys_raw / keys_redacted / names_as_keys_per_file / real_file_census / raw_value across src/, tests/, scripts/, .githooks/ finds only tests/secret_hygiene.rs, whose key-counting helpers are used on the input (to prove the fixture carries the shape) and post-redaction (to prove the key is preserved), and whose value-aware helpers are what assert 0 raw values",
      "contrast_reproduced": "outside the repository, with methods copied from those helpers: on a synthetic raw/handled pair the key counts are 3 vs 3 in both encodings while the value counts are 3 vs 0",
      "decision": "note for a later cleanup; no code changed, because no repository helper publishes a key count as evidence of handling"
    },
    "untouched": {
      "arc_rule": "JumpReading::shows_an_arc is byte-identical (rise > 0.0 && !monotone_fall); plant p4 reddens its test",
      "criteria": "no criterion relaxed",
      "prd_mario_sha256": "4c81c3a9995f0b3afdf01421a0c3be88573cceefc284ce9bafbfda141f0f5c3a",
      "game_written_by_hand": false
    }
  },
  "tests": {
    "new": 5,
    "genuine_first_reds": [
      "evidence_battery::a_level_whose_ground_ends_before_the_walk_still_shows_a_grounded_jump_arc - red before the implementation at tests/evidence_battery.rs:4427:36 (a grounded jump window must carry its own reading)",
      "evidence_battery::the_jump_window_is_driven_before_the_windows_that_consume_the_ground - red before the implementation at tests/evidence_battery.rs:4477:5 (ground probe at 21, first move_right sample at 3)",
      "evidence_battery::the_input_replay_pass_clears_the_previous_steps_held_action_first - first form red at tests/evidence_battery.rs:4509:5; delivered form red before the implementation too"
    ],
    "pins_green_from_the_start": [
      "evidence_battery::a_level_with_no_usable_ground_reports_the_jump_unobserved - the honesty pin the batch was asked for, green before and after",
      "evidence_battery::the_channel_probe_releases_its_own_drive_when_its_reading_is_complete - the mechanism was added while the test was being written, so its first run was green; its red exists only under plant p5 (same class as the DR-82 jump tests' plant-red disclosure)"
    ],
    "fixture": "JumpMode::Ledge with FIXTURE_LEDGE_X = 6600: the player's own x is the interaction drive's end (60 + 29 * 220 = 6440) plus what the replay's horizontal samples have carried it; the channel probe's 30-frame sample adds 30 * 3.6056 = 108.2, so a probe taken before the pass's own walk reads 6548.2 <= 6600, while the full walk leaves 6800.6 > 6600 - the ledge sits between the two positions, so the drive order decides the verdict rather than a tuned constant",
    "existing_test_updated_not_removed": "evidence_battery::input_replay_records_a_delivered_action_without_effect now selects the move_right quadruple by its action instead of by quadruples[0], because the jump is the pass's first window; test attributes in the file went 63 -> 68 and the suite listing 596 -> 601 with 0 removed"
  },
  "plants": {
    "count": 5,
    "all_reddened_their_own_test": true,
    "all_restored_byte_exact": true,
    "entries": [
      {
        "id": "p1_jump_driven_after_the_walk",
        "file": "src/adapter/godot.rs",
        "target": "evidence_battery::a_level_whose_ground_ends_before_the_walk_still_shows_a_grounded_jump_arc",
        "exit": 101,
        "first_failure": "thread 'a_level_whose_ground_ends_before_the_walk_still_shows_a_grounded_jump_arc' (41792) panicked at tests\\evidence_battery.rs:4434:36:",
        "restored_byte_exact": true
      },
      {
        "id": "p2_ground_gate_always_resting",
        "file": "src/adapter/godot.rs",
        "target": "evidence_battery::a_level_with_no_usable_ground_reports_the_jump_unobserved",
        "exit": 101,
        "first_failure": "thread 'a_level_with_no_usable_ground_reports_the_jump_unobserved' (20972) panicked at tests\\evidence_battery.rs:4564:5:",
        "restored_byte_exact": true
      },
      {
        "id": "p3_no_clean_state_before_the_jump",
        "file": "src/adapter/godot.rs",
        "target": "evidence_battery::the_input_replay_pass_clears_the_previous_steps_held_action_first",
        "exit": 101,
        "first_failure": "thread 'the_input_replay_pass_clears_the_previous_steps_held_action_first' (37260) panicked at tests\\evidence_battery.rs:4516:5:",
        "restored_byte_exact": true
      },
      {
        "id": "p4_arc_rule_always_true",
        "file": "src/adapter/godot.rs",
        "target": "evidence_battery::a_jump_window_with_no_rise_is_rejected_too",
        "exit": 101,
        "first_failure": "thread 'a_jump_window_with_no_rise_is_rejected_too' (41400) panicked at tests\\evidence_battery.rs:4310:5:",
        "restored_byte_exact": true
      },
      {
        "id": "p5_probe_leaves_its_action_held",
        "file": "src/adapter/godot.rs",
        "target": "evidence_battery::the_channel_probe_releases_its_own_drive_when_its_reading_is_complete",
        "exit": 101,
        "first_failure": "thread 'the_channel_probe_releases_its_own_drive_when_its_reading_is_complete' (34964) panicked at tests\\evidence_battery.rs:4624:5:",
        "restored_byte_exact": true
      }
    ]
  },
  "forbidden_zones": {
    "boundary_unix": 1790941978,
    "runs_new_files": 0,
    "runs_newest": "runs/smoke-t15/evidence/COPY_MANIFEST.txt 2026-10-02 14:54:52 13079 B",
    "workspace_new_files": 0,
    "workspace_newest": ".workspace/fresh-t15/.godot/.gdignore 2026-10-02 15:14:59 1 B (pre-existing, recorded by T15A-7 and DR82A)",
    "prd_sha256": "4c81c3a9995f0b3afdf01421a0c3be88573cceefc284ce9bafbfda141f0f5c3a",
    "prd_unchanged": true,
    "decisions_sha256": "245befb7af292c379c161ddc917e996a54a4dceea5e93c5d0226816efbae4a76",
    "decisions_unchanged": true,
    "requirements_sha256": "298a948929a434a91b9088f4d566b7e387d0cfeb270f86a79d88b006821e0e54",
    "cargo_toml_sha256": "e0c4992bd828729b8514f9cf694925687b726157d45463a636390081a3dadba1",
    "cargo_lock_sha256": "d98fa91565ec72ae998fd9f6fd3838286e287e4baf8020c5114a1e2ac0bfdb36",
    "engine_binary_sha256": "08483088a4a2772841cd3b4c916b2d45b3cb6255656cf3951598a86fce7e9e6a",
    "engine_repo_head": "fc63af77c33368c4a1bb839c95d19750554f63a3",
    "engine_repo_porcelain_empty": true,
    "pushed": false,
    "line_endings_rewritten": 0,
    "changed_files_all_lf": true,
    "rm_rf_used": false,
    "git_checkout_restore_used": false,
    "paths_built_from_unexpanded_variables": false,
    "repository_scratch_files_touched": false,
    "git_status": " M src/adapter/godot.rs; M tests/evidence_battery.rs; ?? l.json ?? p2.json ?? pv.json ?? r.json (the four untracked root scratch files pre-date this batch: 151/153/62/153 B at 10:14-10:16)",
    "test_suite_sidecar_note": "tests/round_artifacts_sidecar.rs rewrites .spec/hof-rs/tasks/TASK-SMOKE-T10-evidence/analysis/redaction_defect.redacted.txt on every cargo test; git status shows no diff for it, so the rewrite is byte-identical"
  },
  "machine_block": {
    "generator": "json.dumps(..., ensure_ascii=False, indent=2)",
    "written_outside_the_repository": "C:\\Users\\wyl\\AppData\\Local\\Temp\\dr83\\machine_block_dr83.json",
    "round_trip_verified": true
  },
  "residual_risks": {
    "measured": [
      "the frozen smoke-t15 positions the decision rests on (3411.35, 3389.35, 3690.02734375, the floor's last supported centre 3412) are read from the round's own report and its acceptance, not re-measured here",
      "the whole offline gate: 594/0/7 listed 601 exit 0, 60 blocks; fmt exit 0; 61 fingerprints, 97 literal paths, Compiling line 1 of gate_run.log",
      "the five plants' reds and their byte-exact restoration (sha256 equality and cmp exit 0 for every plant)",
      "the census contrast 3 vs 3 and 3 vs 0, reproduced with methods copied from the repository's own helpers"
    ],
    "inferred": [
      "that on the frozen smoke-t15 geometry the reordered jump window is probed at 3411.35 (or, with the probe's release, at 3389.35) and that the engine's is_on_floor() holds there, so the jump is driven from the ground and records an arc. No engine was started, so this is an inference from frozen numbers, not a measurement",
      "the split of the 22 px drift between the channel probe's held action and plain game time: the frozen files only give endpoints, so the release's real margin is bounded (0.65 px without it, 22.65 px with it), not measured",
      "that a rewind-to-ground recovery would fail on a real cliff: argued from the geometry (feet below the floor's top surface mean a horizontal rewind meets the cliff face), not driven"
    ],
    "unverified": [
      "everything engine-side: the probe/arc rule, the reorder and the clean-state clear have not run against a live game process",
      "whether the fixture's Ledge physics (supported iff x <= ledge_x) matches any particular real level; the fixture exists to make the drive order decisive, not to model a specific cliff",
      "the executor-cap disclosure's cause: the first forced-rebuild run was cut off by a 10-minute command cap, and no test failed before it was cut (270 passed, 0 failed)"
    ]
  }
}
```

## 1. What was reordered or bounded, and on what principle

The failure this batch answers is `TASK-SMOKE-T15-REPORT.md` section 2.3: the jump window was a monotone free fall, `min` at index 0, `rise = 0.0`, because the drive had already walked the player off the only floor. The frozen geometry is unambiguous — the floor's last supported player centre is `x = 3412`, the player is already at `x = 3411.35` when `input_replay` starts, and the pre-DR-83 jump window was pressed at `x = 3690.03`, high above the level.

Three changes, all on the harness side, none of them a constant tuned to a level.

**(1) Reorder — the window that needs the ground runs before the windows that consume it.** In `step_input_replay` the `jump` window is now driven **first**, ahead of `move_right` / `move_right_release` / `move_left`. The principle is already load-bearing in this codebase: DR-78 3 moved the coin-observing window before the windows that consume what it observes, and pinned it with `the_coin_observing_window_runs_before_every_consuming_window`. This applies that same rule to the ground, because the jump is the one window whose evidence needs the player supported and the horizontal windows are exactly the windows that take the support away. **Why it generalises**: it orders the battery's *own* windows by what each needs and what each consumes. It does not measure the level, does not guess where the floor ends, and does not carry any number derived from one level, so it holds for every level whose ground can end.

**(2) Bound — the pass clears the action the preceding step left held, before it reads the ground** (`JUMP_STALE_ACTIONS = ["move_right", "move_left"]`, released inside the game process). The jump is now the pass's first window, so the loop's own "release the previous direction" has nothing to drain; a window that begins a pass must not depend on the step before it having been bounded. DR-68 3(a) already fixes this rule for a window's own directions ("every direction is tested from a clean game input state") and `INTERACTION_STALE_ACTIONS` already applies it to the window that observes the coin counter. **Why it generalises**: it is that self-sufficiency rule applied to the state the pass inherited — again a rule about windows, not a number about a level.

**(3) Bound — a probe bounds its own drive.** `step_input_channel_probe` pressed `PROBE_ACTION` and never released it. `smoke-t15` measured where that walk ended: the player drifted `3389.35 -> 3411.35` between that step's last sample and the next step's first one, against a last supported centre of `3412`. The probe now releases the action when its own frame sample is complete, and reports `released_after_probe` in its evidence note. **Why it generalises**: the bound is the probe's own reading — the drive stops where the reading that justified it stops — so the step can no longer leave a walk running into the step after it, whatever the level.

**What the bound is not.** No numeric bound was invented. The only ground reading the harness can take is the two-frame resting probe DR-82 added, and it is used exactly as before: as a gate, not as an estimate. When the probe does not certify the player, nothing is pressed and the window is recorded unobserved. One counter-check I deliberately did **not** take: a "cruise back to the ground" recovery after the fall. On a real cliff the body's feet are already below the floor's top surface, so a horizontal rewind pushes against the cliff face — that would be a fixture-shaped recovery, not a real one, and it is neither implemented nor claimed.

**Guardrails left untouched.** `JumpReading::shows_an_arc` is byte-identical (`rise > 0.0 && !monotone_fall`); plant p4 reddens its test to prove the rule still bites. No criterion was relaxed. `PRD-mario.md` is byte-frozen at `4c81c3a9...5c3a` and no game file was written by hand.

## 2. What the reorder buys on the level that failed

Frozen readings, quoted from the round's report and its acceptance rather than re-measured:

| reading | value |
|---|---|
| floor | `Ground` at (1700,300), `RectangleShape2D` 3400x40 => x in [0,3400]; player box 24 wide => last supported centre x = 3412 |
| interaction window end | 14 batches of `move_right`, win observed, stopped at max x = 3257.35, y constant 263.925201416016 |
| channel probe | 30 frames, x 3283.02 -> 3389.35, y constant 263.925201416016 |
| pre-DR-83 `move_right` window | 60 frames from x 3411.35 (frame 1 at x 3415.02 is already off the floor) |
| pre-DR-83 `jump` window | x constant 3690.02734375, y 1492.81433105469 -> 2552.92553710938 monotone, rise = 0.0 |
| `player.gd` | the jump is applied only when `is_on_floor()` |

With the reorder the jump window is the pass's first, so it is probed and driven at the position the channel probe left behind — the same position the old `move_right` window recorded as its first sample, `3411.35`, which is 0.65 px inside the last supported centre. With the probe's own release (change 3) the walk stops at the probe's own last sample, `3389.35`, which is 22.65 px inside it.

**Measured**: every position above. **Inferred**, and labelled so: that the engine's `is_on_floor()` holds at that x, so the probe certifies the player, the jump is driven from the ground and the arc rule can accept it. No engine was started, so this cannot be measured here. If the inference is wrong the outcome is honest failure rather than a false pass: an uncertified probe records `JUMP_NOT_DRIVEN` and attaches no `jump_reading`, and a driven window that does not rise is `JUMP_DEGENERATE_FALL` or `JUMP_NO_RISE`, never `JUMP_ARC_OBSERVED`.

## 3. Tests — genuine first reds, and what each pins

Five tests were added, all through the real entry points the previous batches used (`run_battery` -> the real adapter -> `FixtureChannel`).

**Genuine first reds** — written and run **before** the production change, on the untouched revision:

| test | first red | green now |
|---|---|---|
| `a_level_whose_ground_ends_before_the_walk_still_shows_a_grounded_jump_arc` | `tests\evidence_battery.rs:4427:36`, "a grounded jump window must carry its own reading" — the probe refused because the walk had already consumed the ground | ok; its current anchor is `4434:36`, seven lines lower because the rewritten `input_replay_records_a_delivered_action_without_effect` above it grew by seven lines |
| `the_jump_window_is_driven_before_the_windows_that_consume_the_ground` | `tests\evidence_battery.rs:4477:5` — ground probe at 21, first `move_right` sample at 3 | ok |
| `the_input_replay_pass_clears_the_previous_steps_held_action_first` | `tests\evidence_battery.rs:4509:5` | ok; current anchor `4516:5`, the same seven-line shift |

**One test was rewritten before delivery, and the reason belongs on the record**: the first form of the clean-state test asserted only that *some* `move_right` release preceded the ground probe, and the old ordering satisfied that by its own drain — so it was not measuring the new mechanism. The delivered form asserts that the pass's **first** game-process input call is the release, which the old ordering cannot satisfy.

**Pins, declared as pins** (green from their first run, not first-red evidence):

| test | status |
|---|---|
| `a_level_with_no_usable_ground_reports_the_jump_unobserved` | the honesty pin the batch was asked for: a level with no usable ground still reports `JUMP_NOT_DRIVEN`, carries no `jump_reading`, and scores no arc |
| `the_channel_probe_releases_its_own_drive_when_its_reading_is_complete` | the mechanism was added while the test was being written, so its first run was green; its red exists only under plant p5 — the same class as the DR-82 jump tests' plant-red disclosure |

**The fixture.** `JumpMode::Ledge` makes the level's floor end at `FIXTURE_LEDGE_X = 6600`, and the ground probe answers with the player's **own** position: the interaction drive's end (`60 + 29 * 220 = 6440`) plus whatever the replay's horizontal samples have carried it. The channel probe's 30-frame sample adds `30 * 3.6056 = 108.2`, so a probe taken before the pass's own walk reads `6548.2 <= 6600`, while the full walk leaves `6800.6 > 6600`. The ledge sits between the two positions — the drive order decides the verdict, not a tuned constant. The fixture's `replay_travel` is advanced by the same frozen per-frame travel the T15 `move_right` window measured (`216.33813476562 / 60`).

**Nothing was removed.** One existing test was updated: `input_replay_records_a_delivered_action_without_effect` now selects the `move_right` quadruple by its action instead of by `quadruples[0]`, because the jump is now the pass's first window and that test's subject is a delivered *horizontal* action with no effect. Test attributes in the file went 63 -> 68; the suite's listing went 596 -> 601 (+5, 0 removed); the ignored set is unchanged.

## 4. Controlled plants — five, each reddening its own test, each restored byte-exactly

| # | file | plant | target test | result | restore |
|---|---|---|---|---|---|
| p1 | `src/adapter/godot.rs` | restore the pre-DR-83 window order (jump third) | `a_level_whose_ground_ends_before_the_walk_still_shows_a_grounded_jump_arc` | exit 101, `tests\evidence_battery.rs:4434:36` | sha256 equal, cmp 0 |
| p2 | `src/adapter/godot.rs` | make the ground predicate accept every non-empty series | `a_level_with_no_usable_ground_reports_the_jump_unobserved` | exit 101, `tests\evidence_battery.rs:4564:5` | sha256 equal, cmp 0 |
| p3 | `src/adapter/godot.rs` | disable the clean-state clear | `the_input_replay_pass_clears_the_previous_steps_held_action_first` | exit 101, `tests\evidence_battery.rs:4516:5` | sha256 equal, cmp 0 |
| p4 | `src/adapter/godot.rs` | make `shows_an_arc` unconditionally true (weaken the arc rule) | `a_jump_window_with_no_rise_is_rejected_too` | exit 101, `tests\evidence_battery.rs:4310:5` | sha256 equal, cmp 0 |
| p5 | `src/adapter/godot.rs` | drop the probe's own release (pre-DR-83 state) | `the_channel_probe_releases_its_own_drive_when_its_reading_is_complete` | exit 101, `tests\evidence_battery.rs:4624:5` | sha256 equal, cmp 0 |

Every plant is a byte-exact replacement with exactly one anchor occurrence, followed by a restore from a byte backup verified with `sha256` and the external `cmp` (exit 0 for all five). No plant was left in the tree: after the plant re-run the two changed files hash to `a66c35aea642f4e3ce55ca1ec013f7a93108c84f31064280428d6e6769a630cd` (`src/adapter/godot.rs`) and `171d254a0101e94367c126911aa5b26b84ee0b9db103930e935e4ef03076e694` (`tests/evidence_battery.rs`) — the same values the gate ran on.

## 5. Gate

| item | value |
|---|---|
| baseline, reproduced first | `cargo test --offline` exit 0; `--list` 596; `--list --ignored` exactly the seven `e0..e6` names => **589 / 0 / 7** |
| final | **594 passed / 0 failed / 7 ignored**, listing **601**, exit 0, **60** result blocks, no `FAILED` or `panicked` line anywhere in the log |
| delta | **+5 tests, 0 removed**, ignored count 7 unchanged, ignored names unchanged |
| `cargo fmt --all --check` | exit 0 |
| forced rebuild | `target/debug/.fingerprint/hof-rs-*` removed with Python `glob` + `shutil.rmtree` (**61**); every path from `git ls-files '*.rs'` touched individually (**97**, `touched_paths_are_literal=True`, no shell wildcard, no path built from an unexpanded variable) |
| forced compile line | `Compiling hof-rs v0.1.0 (F:\moonbit-hof-rs)` — line 1 of `gate_run.log` |

**Disclosure about the two logs.** The executor caps a single foreground command at 10 minutes. The forced-rebuild run (`gate_run.log`) was cut off by that cap after 270 passing tests and zero failures; the full suite was then re-run to completion (`gate_run2.log`, 594/0/7, exit 0) **on the same build**, with both changed files' sha256 identical across the two runs. That is why the `Compiling` line is in the first log and the final totals are in the second. Nothing failed in the cut-off portion; the totals published here are the completed run's own.

## 6. The census the last acceptance flagged (DR82A-1)

**Finding: it is report prose, not repository code — so it is recorded as a note and no code was churned.**

- `TASK-DR82-REPORT.md` item 2 publishes `real_file_census.names_as_keys_per_file = 16` and section 2.3 publishes a two-method comparison; both count **key occurrences**. The redaction fix preserves the key by design (the key is not the span), so those numbers cannot distinguish "handled" from "still raw".
- I searched for a repository-side producer: `census`, `keys_raw`, `keys_redacted`, `names_as_keys_per_file`, `real_file_census`, `raw_value` across `src/`, `tests/`, `scripts/`, `.githooks/`. The only hits are `tests/secret_hygiene.rs`, and its key-counting helpers are used (a) on the **input**, to prove the fixture carries the shape, and (b) after redaction, to prove the key is **preserved** — both correct uses of a key count. The assertions that no raw value survives use the value-aware helpers (`key_form_raw_values`, `decoded_key_raw_value`). No repository helper publishes a key count as evidence of handling.
- The contrast is real, and I reproduced it outside the repository with methods copied from those helpers (`census_contrast.py`): on a synthetic raw/handled pair the key counts are `3` vs `3` in both encodings, while the value counts are `3` vs `0`.
- **Decision**: a note for a later documentation cleanup. The DR-82 report's census sentence is what needs the qualifier; changing the code would have added a helper nobody calls and would not have made the published claim truer.

## 7. Forbidden-zone self-check

| item | reading | basis |
|---|---|---|
| `runs/**` writes | **0** files newer than the batch boundary `1790941978` (2026-10-02 19:52:58); newest is `runs/smoke-t15/evidence/COPY_MANIFEST.txt`, 2026-10-02 14:54:52, 13079 B | `forbidden_scan.py`, single `os.walk` per directory over 7117 files |
| `.workspace/**` writes | **0** newer than the boundary; newest is `.workspace/fresh-t15/.godot/.gdignore`, 2026-10-02 15:14:59, 1 B — pre-existing, recorded by T15A-7 and DR82A | same scan |
| `PRD-mario.md` | `4c81c3a9995f0b3afdf01421a0c3be88573cceefc284ce9bafbfda141f0f5c3a`, unchanged | `sha256sum` |
| `DECISIONS.md` | `245befb7af292c379c161ddc917e996a54a4dceea5e93c5d0226816efbae4a76`, unchanged | `sha256sum` |
| `REQUIREMENTS.md` | `298a948929a434a91b9088f4d566b7e387d0cfeb270f86a79d88b006821e0e54`, unchanged | `sha256sum` |
| `Cargo.toml` / `Cargo.lock` | `e0c4992b...` / `d98fa915...`, unchanged; **no dependency added** | `sha256sum` |
| engine | binary 194216960 B `08483088...e9e6a`; nested repo HEAD `fc63af77...` with empty `git status --porcelain` | `sha256sum` + `git -C godot-mcp/godot status` |
| push | `HEAD == origin/master == 12c6e0f`, **nothing pushed** | `git rev-parse` |
| line endings | both changed files **CR = 0 / CRLF = 0** (pure LF; 302731 B and 241517 B) | byte census |
| repository status | only the two intended files modified; the four untracked root scratch files are pre-existing (151/153/62/153 B at 10:14-10:16) and were not touched | `git status --porcelain` + `stat` |
| the test suite's own sidecar write | `tests/round_artifacts_sidecar.rs` rewrites `TASK-SMOKE-T10-evidence/analysis/redaction_defect.redacted.txt` on every run; `git status` reports no diff for it, so the rewrite is byte-identical and is **not** committed as this batch's work | `git status` + `stat` |
| `rm -rf` / `git checkout --` / unexpanded-variable paths | **none used**; plants restore from byte backups with `sha256` + `cmp`; multi-line helpers live outside the repository | plant script, `force_rebuild.py` |

## 8. Residual risks — measured vs inferred

**Measured** (reproducible from this batch's own instruments):

- the offline gate on the delivered tree: 594 / 0 / 7, listing 601, exit 0, 60 blocks; `fmt` exit 0; 61 fingerprints removed with Python glob + rmtree; 97 literal tracked `.rs` paths touched; the `Compiling` line;
- the five plants' reds (each exit 101 at its own target test) and their byte-exact restoration (sha256 equality and `cmp` exit 0);
- the census contrast (key counts 3 vs 3, value counts 3 vs 0) with methods copied from the repository's helpers;
- zero writes under `runs/**` and `.workspace/**` past the boundary; every frozen hash unchanged; no push; pure LF.

**Inferred** (stated as such, no engine):

- that on the frozen T15 geometry the reordered jump window is probed at `3411.35` (or, with the probe's release, at `3389.35`) and that `is_on_floor()` holds there, so the jump is driven from the ground and the arc rule can accept it. This is the batch's central inference and it is exactly what a real round would test;
- the split of the 22 px drift between the channel probe's held action and plain game time: the frozen files give endpoints only, so the release's margin is bounded (0.65 px without it, 22.65 px with it) rather than measured;
- that a rewind-to-ground recovery would fail on a real cliff — argued from the geometry, not driven.

**Unverified / declared non-goals**:

- everything engine-side: the reorder, the clean-state clear and the probe's release have never run against a live game process;
- whether the fixture's `Ledge` physics (supported iff `x <= ledge_x`) matches any particular real level — the fixture exists to make the drive order decisive, not to model a specific cliff;
- the cause of the executor cap: the first forced-rebuild run was cut off by a 10-minute command cap, with 270 tests passed and none failed before the cut;
- the census item: no code was changed, so nothing in the repository behaves differently as a result of section 6.

## 9. Machine-readable block round-trip

The block above was produced by `json.dumps(..., ensure_ascii=False, indent=2)` in `report_dr83.py` and written **first** to `C:\Users\wyl\AppData\Local\Temp\dr83\machine_block_dr83.json`, outside the repository. It was then parsed back with `json.load` and compared to the in-memory object, re-serialised and compared byte-for-byte, placed into the report as the single `json` fence, and re-extracted from the written file by line-anchored fence search: exactly one `json` fence, `json.loads` succeeds, and the extracted bytes equal the file's bytes. The generator prints the report's byte count and sha256, and the fence verification result.

## 10. Files changed

| file | nature |
|---|---|
| `src/adapter/godot.rs` | DR-83: `jump` window driven first in `step_input_replay`; `JUMP_STALE_ACTIONS` cleared before the ground probe; `step_input_channel_probe` releases `PROBE_ACTION` when its reading is complete and reports `released_after_probe` |
| `tests/evidence_battery.rs` | `JumpMode::Ledge` + `ledge_x` / `replay_travel` / `ledge_probe_resting` fixture state, `with_ledge`, `FIXTURE_LEDGE_X`, `FIXTURE_REPLAY_PX_PER_FRAME`; five new tests; one existing test's quadruple selected by action |
