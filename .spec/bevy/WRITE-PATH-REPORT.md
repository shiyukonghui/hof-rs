# Bevy round-1 write-path report

```json
{
  "schema": "hof-rs / bevy round-1 write-path report",
  "branch": "bevy-core",
  "round_measured": "round1b/iter-1 (recorded transcript; no round was run in this batch)",
  "gate": {
    "command": "cargo test --offline",
    "exit_code": 0,
    "passed": 694,
    "failed": 0,
    "ignored": 3,
    "tests_listed": 697,
    "list_command": "cargo test --offline -- --list",
    "tests_listed_equals_passed_plus_ignored": true,
    "test_targets_listed": 52,
    "warning_lines": 0,
    "fmt_command": "cargo fmt --all --check",
    "fmt_exit_code": 0,
    "build_dir": "F:/moonbit-hof-rs-build-impl/target",
    "no_other_test_process": true,
    "rebuilt_after_touch_of_src_lib_rs": true,
    "ignored_tests": [
      "bevy_adapter_b1.rs: needs a real Bevy 0.19.1 app on 127.0.0.1:15702",
      "bevy_adapter_b2.rs: needs a real hof_game on 127.0.0.1:15702",
      "bevy_round1.rs: needs a real Bevy build (minutes) and a headless launch"
    ],
    "start_tree_gate_recorded_by_the_previous_batch": {
      "source": ".spec/bevy/ROUND-1-REPORT.md gate.passed/passed/failed/ignored",
      "passed": 650,
      "failed": 0,
      "ignored": 3
    },
    "tests_added": 44,
    "tests_removed": 0,
    "tests_renamed_with_strengthened_assertions": [
      "adapter::bevy::round::tests::the_five_e3_steps_name_the_prds_five_behaviours -> the_nine_e3_steps_name_the_prds_behaviours_and_keep_the_original_five (5 -> 9 steps)",
      "adapter::bevy::tests::the_battery_observes_all_five_e3_behaviours_in_order -> the_battery_observes_every_e3_behaviour_in_order (5 -> 9 criteria)",
      "adapter::bevy::tests::a_battery_that_cannot_read_aborts_and_gaps_all_five -> a_battery_that_cannot_read_aborts_and_gaps_every_criterion (5 -> 9 gaps)"
    ]
  },
  "round_one_cost_targeted": {
    "source": "runs/round1b/iter-1/usage.json + logs (as recorded in .spec/bevy/ROUND-1-REPORT.md)",
    "developer_calls": 140,
    "developer_duration_ms": 3263828,
    "developer_duration_minutes": 54.4,
    "developer_total_tokens": 10379180,
    "developer_exit_status": "RepeatedFormatError",
    "developer_tokens_per_call_average": 74137,
    "planner_calls": 19,
    "planner_duration_ms": 72330,
    "planner_total_tokens": 175162,
    "tester_calls": 150,
    "tester_duration_ms": 534331,
    "tester_total_tokens": 9658837,
    "round_wall_seconds": 3945.5,
    "battery_build_millis": 21090,
    "scaffold_cold_build_seconds": 322
  },
  "configuration": {
    "old": {
      "agent.max_consecutive_format_errors": 3,
      "agent.max_action_failures": null,
      "agent.artifact_write_budget_seconds": null,
      "agent.artifact_write_budget_tokens": null
    },
    "new": {
      "agent.max_consecutive_format_errors": 3,
      "agent.max_action_failures": 3,
      "agent.artifact_write_budget_seconds": 900,
      "agent.artifact_write_budget_tokens": 1500000
    },
    "semantics": {
      "agent.max_consecutive_format_errors": "mini's own counter, consecutive and reset by any success; unchanged, and still the only tripwire for format errors (they happen above the environment)",
      "agent.max_action_failures": "failures of one action, cleared only when that same action succeeds",
      "agent.artifact_write_budget_seconds": "live, enforced inside the role environment",
      "agent.artifact_write_budget_tokens": "post-hoc, judged by the runtime on the recorded attempt"
    }
  },
  "changed_files": {
    "modified": [
      "config/hoh.yaml",
      "src/adapter/bevy/battery.rs",
      "src/adapter/bevy/mod.rs",
      "src/adapter/bevy/project.rs",
      "src/adapter/bevy/round.rs",
      "src/adapter/mod.rs",
      "src/config.rs",
      "src/harness/mini.rs",
      "src/harness/mod.rs",
      "src/prompts/developer.md",
      "src/prompts/mod.rs",
      "src/prompts/planner.md",
      "src/prompts/tester.md",
      "src/prompts/skills/bevy-dev.md",
      "src/prompts/skills/bevy-testing.md",
      "src/runtime/invoke.rs",
      "src/runtime/mod.rs",
      "src/runtime/record.rs",
      "src/runtime/run_loop.rs",
      "src/runtime/shell.rs",
      "tests/role_paths.rs"
    ],
    "added": [
      "src/harness/directive.rs",
      "src/harness/guard.rs",
      "src/runtime/write_failure.rs",
      "tests/role_write_failure.rs",
      "tests/write_path_contract.rs"
    ],
    "forbidden_documents_touched": [],
    "committed": false
  },
  "write_recipe": {
    "shape": "HOH_WRITE_FILE <relative path>\\n<whole file content>HOH_END_WRITE_FILE",
    "read_shape": "HOH_READ_FILE <relative path>",
    "where_it_is_executed": "src/harness/guard.rs, before the command reaches cmd.exe",
    "documented_in": [
      "src/prompts/mod.rs ({{shell_truth}}, delivered in all three role system prompts)",
      "src/prompts/skills/bevy-dev.md"
    ],
    "hostile_content_round_tripped": "quotes, parentheses, percent signs, dollar signs, backslashes, CRLF and raw newlines"
  },
  "target_directory_timings_measured": {
    "method": "F:/moonbit-hof-rs-build-impl/measure_target_timings.py, on a copy of the round-1 project (F:/hof-bevy-round1/workspace), cargo 1.x offline",
    "warm_shared_target_already_built_seconds": 1.5,
    "warm_shared_target_after_one_file_edit_seconds": 24.4,
    "cold_fresh_target_seconds": 299.9,
    "round_one_command_timeout_seconds": 180,
    "note": "299.9 s > 180 s: the cold build a role ran without CARGO_TARGET_DIR cannot finish inside the command timeout, which is the timeout failure recorded in the round-1 Developer trajectory",
    "shared_target": "F:/hof-bevy-round1/hof-bevy-shared-target"
  },
  "battery": {
    "steps_before": 5,
    "steps_after": 9,
    "added_step_ids": [
      "e3_movement_left",
      "e3_movement_release",
      "e3_win_position",
      "e3_grounded_payload"
    ],
    "round_one_gaps_closed": [
      "P1-left",
      "P1-release",
      "P3-position",
      "P5-gate"
    ],
    "existing_steps_weakened_or_removed": []
  },
  "plants": [
    {
      "id": "P1_write_directive_not_handled",
      "file": "src/harness/guard.rs",
      "test": "write_path_contract::the_documented_write_directive_round_trips_through_the_real_shell",
      "green_before": 0,
      "red": 101,
      "green_after": 0,
      "restore_sha256_matches": true,
      "mtime_restored": true
    },
    {
      "id": "P2_target_directory_not_exported",
      "file": "src/runtime/invoke.rs",
      "test": "runtime::invoke::tests::role_env_exports_the_adapters_target_directory",
      "green_before": 0,
      "red": 101,
      "green_after": 0,
      "restore_sha256_matches": true,
      "mtime_restored": true
    },
    {
      "id": "P3_write_failure_never_classified",
      "file": "src/runtime/write_failure.rs",
      "test": "role_write_failure::a_failed_developer_call_that_wrote_nothing_is_recorded_as_a_write_failure",
      "green_before": 0,
      "red": 101,
      "green_after": 0,
      "restore_sha256_matches": true,
      "mtime_restored": true
    },
    {
      "id": "P4_leftward_criterion_accepts_any_change",
      "file": "src/adapter/bevy/battery.rs",
      "test": "adapter::bevy::battery::tests::leftward_movement_is_the_negative_direction_and_not_merely_a_change",
      "green_before": 0,
      "red": 101,
      "green_after": 0,
      "restore_sha256_matches": true,
      "mtime_restored": true
    }
  ]
}
```

## 1. What this batch changed, per task

The diagnosis in the task book was verified from the files before anything was
changed. `runs/round1b/iter-1/traj/developer.attempt1.json` really contains
`cat .hoh/TASK.md` and `cat .hoh/plan.md` (69 occurrences of `cat `), the shell
really is `cmd.exe` (`mini-swe-agent-rust-mini/rust/src/environments/local.rs:66-76`,
`process.arg("/C"); process.raw_arg(command)`), `RepeatedFormatError` really
appears nowhere under `src/`, and `config/hoh.yaml` really had no
per-action tripwire and no artifact budget.

### Task 1 — a reliable write path

**What changed.** A role command whose first line is `HOH_WRITE_FILE <path>` is
intercepted **before it reaches `cmd.exe`** by
[`WriteGuardEnvironment`](<src/harness/guard.rs>), which parses it with
[`directive`](<src/harness/directive.rs>) and performs the write in Rust. No
shell parses the content at all, so quotes, parentheses, `%`, `$`, `\`, CRLF and
raw newlines are literal. The canonical shape is

```text
HOH_WRITE_FILE src/game.rs
use bevy::prelude::*;
fn main() { println!("100% \"done\" (really) $HOME C:\\x"); }
HOH_END_WRITE_FILE
```

and it is delivered to every role through a single `{{shell_truth}}` section
(`src/prompts/mod.rs`) that all three system prompts carry. A directive whose
closing line is missing is refused with an explanation — it is never guessed at
and never half-written.

Why a directive and not a "cmd recipe": DR-66 already rendered the *variable
syntax* for the real shell, and that cannot fix this half. `cmd.exe` has no
escape for a literal `%`, no heredoc, and no way to carry a raw newline inside an
argument, so any recipe that puts a whole source file on a `cmd.exe` command line
has to survive the same parser that ate round 1.

**The tests that pin it.**

| test | what it proves |
|---|---|
| `harness::directive::tests::hostile_multiline_content_round_trips_byte_for_byte` | the parser/writer round-trip on content carrying `"`, `'`, `(`, `)`, `%`, `$`, `\`, `&`, `|`, `>` |
| `harness::directive::tests::a_directive_is_not_a_shell_command_and_has_no_reserved_characters` | the same over a table that includes empty content and content with no trailing newline |
| `harness::directive::tests::an_unterminated_write_is_malformed_never_truncated_content` | a missing terminator is refused, never written short |
| `write_path_contract::the_documented_write_directive_round_trips_through_the_real_shell` | the **whole stack** (`LocalEnvironment` → `CappedEnvironment` → guard) over a real `cmd.exe`, byte-exact |
| `write_path_contract::the_documented_read_directive_returns_the_bytes_unchanged` | byte-exact read-back, CRLF included |
| `harness::guard::tests::a_directive_never_reaches_the_shell` | ordinary commands still reach the shell and directives never do |

**What it does not cover.** It does not exercise mini's model→tool-call parsing
(no model may be called offline); it is pinned instead by the fact that mini
passes the tool-call `command` string through as `Action.command` unchanged
(`llm_connector.rs`, `ApiMode::ToolCalls`). It does not prove the model will
*choose* the directive; that is the prompt's job and can only be measured by a
real round (round 2).

### Task 2 — a reliable read path

`HOH_READ_FILE <path>` is the counterpart, with the same interception. `type
<file>` also works and is named in the prompt; `cat` is explicitly **not**
recommended, and the prompt no longer lets a role believe it can.

`write_path_contract::the_shell_shapes_that_ate_round_one_are_replaced_by_the_directives`
executes the difference: `echo one; echo two` prints the literal text (so
`cat a; cat b` never runs `b`), and a file written through `echo` cannot carry a
literal `%` while the directive can. `cat` itself is deliberately **not**
asserted to be missing — on a machine whose `PATH` includes Git's
`usr/bin` (`where cat` → `C:\Program Files\Git\usr\bin\cat.exe` here) it works,
which is exactly the trap. The round-1 *before* is pinned from the recording by
`write_path_contract::the_recorded_round_one_trajectory_really_carried_these_shapes`,
which asserts the recorded trajectory carries `cat .hoh/TASK.md`,
`cat .hoh/plan.md` and `=====PLAN=====`, and does **not** carry `HOH_WRITE_FILE`.

### Task 3 — the shell truth, stated in the prompts

`{{shell_truth}}` (`src/prompts/mod.rs`, rendered by
`runtime::invoke::render_prompt_for_shell`) is now part of `developer.md`,
`planner.md` and `tester.md`. It states, for the target shell:

- the shell is `cmd.exe`, not POSIX `sh`;
- variables are `%NAME%`, `$NAME` is not expanded;
- chaining is `&&`, never `;`;
- only double quotes group; single quotes are literal;
- `cat` does not exist and `type`/the read directive replaces it;
- the forbidden shapes: `cat <file>`; `a; b`; `bash -c "…"`; a heredoc
  (`<< EOF`); an inline interpreter one-liner with real newlines; `echo … >> file`
  used to build a multi-line file.

It also names the write directive and shows the executable
`{{HOH_HOH_BIN}} tools call … --args-file {{HOH_ARTIFACT_DIR}}/…` form.
The whole delivered set is checked by `prompt_shell_contract.rs` (no unresolved
placeholder, the extracted command really runs in a real `LocalEnvironment`).

### Task 4 — the adapter's target directory, exported

`ProjectAdapter::build_target_dir()` is new; the Bevy adapter answers with
`project::target_dir_for(workspace)` (the same shared directory the round builds
into). `runtime::invoke::role_env` now exports it under **both** `HOH_TARGET_DIR`
(the harness's name, for the prompt) and `CARGO_TARGET_DIR` (the name cargo
itself reads), absolute, for every role.

Timings measured with `measure_target_timings.py` on a copy of the round-1
project against the round's own shared target tree:

| build | seconds |
|---|---|
| warm shared target, nothing to do | 1.5 |
| warm shared target, one source file edited | 24.4 |
| cold, fresh empty target directory | 299.9 |

`agent.command_timeout_seconds` is 180. The cold build **cannot finish inside
the timeout**, which is why round 1's Developer recorded a timeout failure while
building a second tree inside the project. Pinned by
`runtime::invoke::tests::role_env_exports_the_adapters_target_directory`,
`write_path_contract::the_exported_target_directory_is_where_the_build_really_goes`
(no `target/` appears inside the project) and its control
`...::without_the_export_the_build_lands_inside_the_project`.

### Task 5 — the grind is impossible

1. **Fail fast on a repeated failing action.** `WriteGuardEnvironment` counts
   failures **per action** in `agent.max_action_failures`. The same command
   failing three times aborts the call, and an unrelated success in between does
   not clear the counter — which is exactly what mini's
   `max_consecutive_format_errors` did wrong. Pinned by
   `harness::guard::tests::the_same_failing_action_aborts_the_call_per_action_not_consecutively`
   and `...::a_success_of_the_same_action_clears_its_own_counter`.
2. **A per-artifact budget, tokens and wall-clock.** The wall-clock half
   (`agent.artifact_write_budget_seconds`, 900 s) is enforced **live**: a role
   that has not written its declared artifact is aborted with the first-class
   status `ArtifactBudgetExceeded`. The token half
   (`agent.artifact_write_budget_tokens`, 1,500,000) cannot be measured inside
   the environment — usage is known only when a model call returns — so it is
   judged by the runtime on the recorded attempt in
   `runtime::write_failure::assess`. Pinned by
   `harness::guard::tests::the_artifact_budget_aborts_a_call_that_never_writes`,
   `...::a_project_write_disarms_the_artifact_budget`,
   `...::a_planner_or_tester_artifact_disarms_the_budget_through_hoh` and
   `runtime::write_failure::tests::an_unknown_status_is_not_reclassified_unless_the_token_budget_was_blown`.
3. **The tripwire counts per action.** `agent.max_action_failures: 3`. Every
   value in `config/hoh.yaml` now carries its justification in the file itself.

**What it does not cover.** Mini's *format* errors are produced inside mini's
own loop, above the environment, so the guard cannot see them and cannot count
them per action; `max_consecutive_format_errors` remains the only tripwire for
that class. The fix for round 1's `RepeatedFormatError` is therefore structural
(the write path removes the reason the model fought the shell) plus the
wall-clock budget, not a per-action counter on format errors. The token budget is
also post-hoc by nature: it makes the cost a judgeable fact, it does not stop the
call it describes.

### Task 6 — it is our own judgement

`runtime/write_failure.rs` turns the runtime's own measurement ("did the artifact
tree change?" / "is the declared file non-empty?") plus the attempt's recorded
exit status and tokens into a `RoleWriteFailure`, persisted in
`iter-<n>/result.json` under `write_failures` **and** in `runs/<id>/warnings.log`
as a `role_write_failure:` line. It is produced on the Developer stage (including
the `no_engineering_write` failure path), on the Planner's schema failure and on
the Tester's, and it is carried through `FailureFacts` so a later failure cannot
erase a fact the runtime measured.

`RepeatedFormatError` is no longer only an external string:
`harness::mini::classify_run_result` maps a fail-fast abort across mini's opaque
`AgentError::Other` into a first-class `RoleOutcome::exit_status`, and
`write_failure::is_failure_status` classifies it like our own
`RepeatedActionError` / `ArtifactBudgetExceeded`.

Pinned by `tests/role_write_failure.rs` (4 tests, driving the real `run_loop` with
a fake harness): the round-1 shape produces exactly one entry with
`exit_status = "RepeatedFormatError"` and a warning-log line; our own fail-fast
status produces the same fact; a Developer that *did* write produces none; and
the assessment rules are checked directly. Also
`harness::mini::tests::a_fail_fast_abort_becomes_a_first_class_exit_status` and
`...::an_infrastructure_failure_is_still_an_error`.

**What it does not cover.** The full `MiniHarness::invoke` path (a real model
call) is not exercised offline; what is pinned is the pure classification plus
the guard's sentinel. The Planner's and Tester's entries on the *success* path are
not produced (a role that wrote has nothing to report), which is the intended
rule.

### Task 7 — the four missing battery steps

`E3_STEPS` grew from 5 to 9 and `E3Observations` from 5 to 9 fields; the
**original five ids, order and PRD mapping are unchanged** (asserted by
`round::tests::the_nine_e3_steps_name_the_prds_behaviours_and_keep_the_original_five`).

| new step | PRD | what it measures | why it could not be a gap |
|---|---|---|---|
| `e3_movement_left` | P1 | injecting `move_dir = -1` moves `x` **down** | `movement_changed` accepts a rightward move; `leftward_movement` does not |
| `e3_movement_release` | P1 | after `move_dir = 0`, `x` stops (no residual velocity) | the Developer's own definition of done promises it and nothing checked it |
| `e3_win_position` | P3 | a `PlayerTransform` sample at or after the frame the win flag turned true | a win with no position is not located in the world |
| `e3_grounded_payload` | P5 | a `Grounded` payload carrying a boolean, read at rest as its own observation | it previously existed only as the jump's supporting basis |

Each new step gets its own `raw/e3_*.json` (the payload writer is now driven by
`E3_STEPS` rather than a second hard-coded list), and the four run **before** the
jump phase so a measured stop cannot cost the round a win (the left/release phase
deliberately runs after the coin/win phase for that reason). The playbook
(`project.rs`) and `bevy-testing.md` name all nine.

Pinned by `adapter::bevy::tests::the_battery_observes_every_e3_behaviour_in_order`
(all nine hold over the fake socket, with the negative-x, stopped-x, frame-order
and payload-shape properties asserted), the three new predicate unit tests, and
`round::tests::a_failed_build_closes_the_gate_and_still_names_every_criterion`
(11 records).

**What it does not cover.** The four new steps have not been observed on a **real
game**: the only engine-driving test is `#[ignore]`d
(`bevy_round1::the_five_behaviours_are_observed_on_a_real_bevy_game_process`),
and this batch may not run a round. The fake game is the evidence here, and round
2 is what will show whether the round-1 artifact satisfies the two movement
additions.

## 2. Before/after evidence for the recipe

| | before (round 1, recorded) | after (executed here) |
|---|---|---|
| how a file is written | file content inside a `cmd.exe` command line (`bash -c` heredoc, `python -c`, `echo` appends) | `HOH_WRITE_FILE <path>` … `HOH_END_WRITE_FILE`, executed by the harness |
| POSIX read | `cat .hoh/TASK.md; echo "=====PLAN====="; cat .hoh/plan.md` — in the recording | `HOH_READ_FILE` / `type` |
| `;` | treated as a separator by the model, literal text to `cmd.exe` | not needed |
| `%` in content | expanded by the shell | literal |
| outcome | 140 calls / 54.4 min / 10.4M tokens / `RepeatedFormatError` | byte-exact write in one action (`write_path_contract`) |

## 3. What I could not verify

- **No real round was run** (forbidden for this batch), so nothing here is
  evidence that a model will *use* the directive, that the Developer's round-1
  artifact satisfies `e3_movement_left` / `e3_movement_release`, or that the new
  budget fires in production. Round 2 is the measurement.
- **`MiniHarness::invoke` end to end** needs a model call; only the pure pieces on
  either side of it are pinned.
- **Format errors cannot be counted per action** from outside mini (see Task 5).
- **The four new battery steps on a real game**: the only engine test is ignored.
- **The `cat` failure** is machine dependent (Git's `cat.exe` is on `PATH` here);
  the round-1 *before* is therefore pinned from the recording, not from the live
  shell.
- **The timings for a *Bevy* cold build** are measured on the round's project and
  its shared target tree; the 24.4 s one-file-edit figure is for that project on
  this machine, not a promise about another machine. The recorded round-1 battery
  build was 21,090 ms.

## 4. The single most important thing the next batch should do when it runs round 2

**Run one real iteration and read the Developer's `write_failures`, `attempts`
and wall-clock first — before looking at the artifact.** The whole point of this
batch is that a 54-minute grind must become impossible and visible; if round 2's
Developer still ends a call with a failure status and no engineering write, the
`write_failures` entry and the `ArtifactBudgetExceeded` status will name it in
`result.json`, and the two values to watch are the Developer's duration (target:
minutes, not 54) and its token total (target: below 1.5M, against 10.4M). If the
write directive is *not* what the model reaches for — the prompt is the only
thing that can make it — that is the finding to fix next, and it will be more
valuable than any further harness-side budget.
