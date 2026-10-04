# Bevy trust batch — report

**Scope.** Repair the observation path that made round 2's two batteries measure the wrong
process; make a role's `cargo build` reliable while a game runs; re-examine round 1 under the new
rule using only its recorded evidence; attack the real cost driver; close the credential leak.

**No round was run in this batch.** Everything below is either a measurement over recorded
evidence (`runs/round2/**`, `runs/round1b/**`, `runs/round1/**`, `runs/bevy-round1b/**`,
`F:/hof-bevy-r2/replay/**`) or a test in the default gate. The next batch runs round 3 once.

```json
{
  "schema": "hof-rs / bevy trust batch report",
  "branch": "bevy-core",
  "round_run_in_this_batch": false,
  "gate": {
    "command": "cargo test --offline",
    "exit_code": 0,
    "exit_code_source": "literal `$?` of the two final runs, captured with `set -o pipefail`",
    "passed": 720,
    "failed": 0,
    "ignored": 3,
    "listed": 723,
    "warning_lines": 0,
    "runs": 2,
    "run_1": {"exit_code": 0, "passed": 720, "failed": 0, "ignored": 3, "listed": 723, "warning_lines": 0},
    "run_2": {"exit_code": 0, "passed": 720, "failed": 0, "ignored": 3, "listed": 723, "warning_lines": 0},
    "list_command": "cargo test --offline -- --list",
    "list_exit_code": 0,
    "tests_listed": 723,
    "listed_equals_passed_plus_ignored": true,
    "test_targets_listed": 53,
    "ignored_tests": [
      "bevy_adapter_b1.rs: needs a real Bevy 0.19.1 app listening on 127.0.0.1:15702 (SPIKE-1/2); never in the default gate",
      "bevy_adapter_b2.rs: needs a real hof_game on 127.0.0.1:15702 with the frozen contract registered; never in the default gate",
      "bevy_round1.rs: needs a real Bevy build (minutes) and a headless launch; never in the default gate"
    ],
    "tests_added": 26,
    "tests_removed": 0,
    "tests_renamed_with_strengthened_assertions": [
      "adapter::bevy::contract::tests::the_contract_is_seven_surfaces_and_the_semantic_tools_are_fully_accounted_for -> the_contract_is_eight_surfaces_and_the_semantic_tools_are_fully_accounted_for (7 -> 8 surfaces)",
      "tests/bevy_adapter_b2.rs: the_repinned_contract_hash_covers_seven_surfaces -> the_repinned_contract_hash_covers_the_frozen_surfaces (7 -> 8, literal re-pinned)",
      "tests/credential_scan.rs: the_shape_test_catches_credentials_and_ignores_prose gained the crate-name controls (async-task is not a credential)"
    ],
    "fmt_command": "cargo fmt --all --check",
    "fmt_exit_code": 0,
    "build_dir": "F:/hof-trust-target",
    "no_other_test_process": true,
    "start_tree_gate_recorded_by_this_batch": {
      "source": "measured before any edit, same build directory",
      "passed": 694,
      "failed": 0,
      "ignored": 3,
      "listed": 697,
      "exit_code": 0
    }
  },
  "changed_files": {
    "modified": [
      "config/hoh.yaml",
      "src/adapter/bevy/contract.rs",
      "src/adapter/bevy/launch.rs",
      "src/adapter/bevy/mod.rs",
      "src/adapter/bevy/project.rs",
      "src/adapter/bevy/round.rs",
      "src/adapter/bevy/scaffold.rs",
      "src/adapter/bevy/scaffold/game/src/contract.rs",
      "src/adapter/bevy/scaffold/game/src/main.rs",
      "src/cli.rs",
      "src/cli_impl.rs",
      "src/config.rs",
      "src/harness/guard.rs",
      "src/harness/mini.rs",
      "src/runtime/secrets.rs",
      "tests/bevy_adapter_b1.rs",
      "tests/bevy_adapter_b2.rs"
    ],
    "added": ["tests/credential_scan.rs", "tests/repeated_action.rs"],
    "removed_from_the_tree": ["config/model.secret.env"],
    "not_modified_by_design": [
      ".spec/bevy/REQUIREMENTS.md",
      ".spec/bevy/DESIGN-OVERVIEW.md",
      ".spec/bevy/DESIGN-DETAIL.md",
      ".spec/bevy/PRD.md",
      ".spec/bevy/SPIKE-1-REPORT.md",
      ".spec/bevy/SPIKE-2-REPORT.md",
      ".spec/bevy/ROUND-1-REPORT.md",
      ".spec/bevy/ROUND-2-REPORT.md",
      ".spec/bevy/BATCH-*",
      "DECISIONS.md"
    ]
  },
  "new_configuration_values": {
    "agent.max_repeated_actions": {
      "old": null,
      "new": 15,
      "semantics": "the same action's total successes in one call before the call is aborted with RepeatedActionError; 0 disables",
      "justification": "measured from the recorded round-2 evidence: iteration 2 (engineering work whose last build the artifact survived) repeats its most-repeated action 14 times, iteration 1 repeats its most-repeated action 39 times. 15 is the smallest integer strictly above the clean iteration's maximum.",
      "pinned_by": "tests/repeated_action.rs::the_recorded_engineering_call_defines_the_upper_bound_of_the_cap and harness::guard::tests::the_same_successful_action_repeated_to_its_cap_aborts_the_call"
    },
    "agent.steps_per_artifact": {
      "old": null,
      "new": 8,
      "semantics": "steps a role gets per write of the artifact it declares; an unwritten call is limited to wrap_up_steps + step_limit/steps_per_artifact = 25 + 18 = 43 steps; the first project write earns the flat 150; 0 disables",
      "justification": "round 2's Developer made its first write on message 14 of a 150-step call, so 8 steps per artifact is generous for a call that is working; round 1's shape (140 calls, one file) depends on no progress gate at all",
      "pinned_by": "config::tests::the_step_budget_responds_to_progress and tests/repeated_action.rs::the_progress_gate_shortens_a_call_that_has_written_nothing"
    },
    "agent.step_limit": {"old": 150, "new": 150, "note": "unchanged; only its enforcement is now progress-gated"},
    "agent.wrap_up_steps": {"old": 25, "new": 25, "note": "unchanged"},
    "contract.CONTRACT_SHA256": {
      "old": "792001e7e629ccc25d6c486eeb54360d83ffb208befa4ca5e430c6f0e747f4f9",
      "new": "c579a742cea5f2f22b0e34c2ae6ab3bafcb56050310a5d35e95941796bdcf7e9",
      "semantics": "the frozen reflectable contract grew from seven surfaces to eight",
      "justification": "readiness must prove identity, which needs a per-launch value the game publishes; the new surface is hof_game::contract::ProcessNonce (Resource, string field `value`, fed by HOF_GAME_PROCESS_NONCE). This is a contract change by definition and is re-pinned rather than smuggled in beside an unchanged hash.",
      "pinned_by": "adapter::bevy::contract::tests::the_contract_hash_is_the_pinned_literal, the_eighth_surface_is_the_process_nonce, tests/bevy_adapter_b1.rs::the_frozen_contract_hash_and_crate_name_are_pinned, tests/bevy_adapter_b2.rs::the_repinned_contract_hash_covers_the_frozen_surfaces"
    },
    "cli.run/doctor --env-from-secret <path>": {
      "old": null,
      "new": "a CLI flag; the path is refused if it is inside the repository, if it does not exist, or if it holds no key-shaped KEY=VALUE line",
      "justification": "nothing in the harness named secret files at all, which is why config/model.secret.env could sit in the tree; the named mechanism plus its refusal is the fix",
      "pinned_by": "tests/credential_scan.rs::a_secret_file_inside_the_repository_is_refused_with_both_paths_named, a_secret_file_outside_the_repository_loads_and_is_never_printed, a_file_with_no_key_shaped_value_is_refused"
    }
  },
  "context_measurement": {
    "what_is_measured": "the recorded round-2 Developer trajectories (runs/round2/iter-{1,2}/traj/developer.attempt1.json), which carry every message and every provider usage block",
    "before": {
      "iter_1": {
        "api_calls": 150,
        "messages": 278,
        "prompt_tokens_first": 4187,
        "prompt_tokens_last": 115698,
        "prompt_tokens_total": 11108856,
        "prompt_tokens_per_call_average": 74059,
        "wire_bytes_content": 109424,
        "wire_bytes_tool_calls": 306324,
        "local_only_bytes_extra": 949357,
        "final_prompt_tokens_per_wire_byte": 0.28,
        "growth_tokens_per_message": 404
      },
      "iter_2": {
        "api_calls": 104,
        "messages": 237,
        "prompt_tokens_first": 4187,
        "prompt_tokens_last": 108388,
        "prompt_tokens_total": 8035712,
        "prompt_tokens_per_call_average": 77266,
        "wire_bytes_content": 265144,
        "wire_bytes_tool_calls": 121010,
        "local_only_bytes_extra": 579559,
        "final_prompt_tokens_per_wire_byte": 0.28,
        "growth_tokens_per_message": 443
      },
      "what_dominates": "call count multiplied by the accumulated history. The system prompt is 14117 bytes (~5% of the final prompt) so it is not the driver; the trajectory's `extra` blocks are 949357 bytes locally and never leave the process (mini's to_llm_message sends only content and tool_calls), so they are not the billed driver either. Each call adds ~400-440 tokens and re-sends everything before it: the recorded spend reconstructs as sum over calls of (4187 + 0.28 x accumulated wire bytes) = 11,108,856 tokens."
    },
    "after": {
      "note": "projection over the recorded per-call prompt tokens, not a new run",
      "iter_1_under_the_tripwire": {
        "abort_at_api_call": 50,
        "prompt_tokens_kept": 1703158,
        "fraction_of_observed": 0.153,
        "target": "below 1500000; the projection reaches the target's neighbourhood, and the step budget is the second lever"
      },
      "iter_2_under_the_tripwire": {
        "abort_at_api_call": null,
        "prompt_tokens_kept": 8035712,
        "fraction_of_observed": 1.0,
        "honest_reading": "the tripwire would NOT have helped iteration 2; its grind was coverage work spread over many different actions, which no repeat counter can see, and its repeats (14 builds) are legitimate"
      },
      "unwritten_call_under_the_progress_gate": "43 steps instead of 150 when nothing has been written, i.e. a grind cannot spend the fixed budget at all"
    }
  },
  "round_1_verdict": {
    "verdict": "round 1's five observations were NOT taken from the artifact round 1 claimed; they came from a process that was already running when the Developer started (almost certainly the round's own A0 session game), and the recorded files cannot show it because launch.json names only the process the harness hoped for",
    "arithmetic": {
      "run_started_at_unix_seconds": 1791080101,
      "battery_first_call_unix_seconds": 1791083488.844,
      "battery_first_frame_read": 198376,
      "measured_frames_per_second_in_the_battery_window": 58.96,
      "implied_process_start_unix_seconds": 1791080127,
      "implied_start_minus_run_start_seconds": 26,
      "battery_first_read_minus_run_start_seconds": 3388,
      "battery_launch_record_pid": 35436,
      "run_meta_engine_game_endpoint_pid": 6848,
      "note": "the process that answered the battery began counting frames 26 seconds after `hoh run` started, i.e. 56 minutes before the battery ran, and its pid is neither the pid the battery's own launch.json records nor the pid the run's meta.json records"
    },
    "corroborating_evidence": [
      "runs/bevy-round1b/launch.json records pid 35436 with ready_millis 47, i.e. a process this harness had just started; the answering process had ~3362 seconds of frames behind it",
      "runs/round1b/meta.json records a different pid again (6848) at started_at, with checked_at equal to the run's start",
      "the battery's recorded jump arc is first=-200.0, peak=-165.015, rising=4, falling=8; round 1's own replay of the A0 scaffold gives first=-200.0, peak=-165.274 (the report's final artifact replay gives a different arc), so the arc is consistent with the scaffold rather than with the artifact the round claimed",
      "there is no field anywhere in runs/bevy-round1b/ that names the process which answered: launch.json carries pid 35436 and a binary digest, neither checked against the responder"
    ],
    "what_this_does_not_mean": "the game is still right. Round 2's own replay with the strays killed showed the final artifact satisfies all nine battery steps, and round 1's artifact is not re-tested here. The defect is in the observation, not in the game.",
    "usage_of_round_1_evidence_from_here": "round 1's five-criterion claim must be read as unverified, not as verified; every green produced by the old readiness path (round 1 and round 2) is untrustworthy until the pass proves identity"
  },
  "credential_scan": {
    "leaked_file": {
      "path": "config/model.secret.env",
      "action": "removed from the tree (single-file removal over a printed, verified path; not rm -rf)",
      "bytes": 205,
      "file_sha256": "84233e3824225c8ab2fb84c1f46c68dc33abe302c6da0e580dd20790a0b6b2fe",
      "key_shaped_value": "one value, 51 characters, fingerprint 5cf81e8f, deliberately not printed",
      "still_gitignored_before_removal": true
    },
    "browsable_tree_after_the_removal": {
      "findings": 0,
      "scan": "every file under the repository root except .git/, target/, .workspace/, runs/ and node_modules/",
      "test": "tests/credential_scan.rs::no_key_shaped_material_is_browsable_in_the_repository_tree"
    },
    "recorded_evidence_that_still_holds_the_key": [
      "runs/round1/iter-1/traj/developer.attempt1.json (fingerprint 5cf81e8f, length 51)",
      "runs/round1b/iter-1/traj/tester.attempt1.json (fingerprint 5cf81e8f, length 51)"
    ],
    "recorded_evidence_that_does_not": [
      "runs/round1b/iter-1/traj/developer.attempt1.json: an earlier, looser shape rule reported 24 hits here, but every one of them is the substring `sk-` inside the Rust crate names async-task-... / futures-task-...; the corrected rule (a hyphen before the prefix is a token boundary) finds none",
      "runs/round1b/iter-1/traj/developer.attempt1.redacted.json: same"
    ],
    "why_the_evidence_was_not_rewritten": "those files are the recorded material the round-1 report cites; rewriting them would destroy the evidence a report has to be checked against. They are gitignored, so they are in no browsable tree and in no archive of this repository. The key must be rotated by its owner, which DECISIONS.md already records as the rollback point.",
    "reported_not_silenced": "tests/credential_scan.rs::the_historical_evidence_is_reported_with_a_fingerprint_never_the_value prints the paths and the fingerprint and never the value"
  },
  "controlled_plants": [
    {"id": "P1_nonce_never_checked", "file": "src/adapter/bevy/launch.rs", "test": "adapter::bevy::launch::tests::a_listener_that_serves_a_different_nonce_fails_readiness", "red_exit_code": 101, "red_test_ran": true, "green_exit_code": 0, "green_test_ran": true, "restore_sha256_matches": true, "mtime_restored": true},
    {"id": "P2_previous_session_not_reaped", "file": "src/adapter/bevy/launch.rs", "test": "adapter::bevy::launch::tests::a_pid_this_round_recorded_is_reaped_before_the_next_launch", "red_exit_code": 101, "red_test_ran": false, "red_shape": "compile error (a nonexistent function in the reap path); the runtime plant was rejected by this harness because a planted no-reap hangs the test, and a killed run proves nothing", "green_exit_code": 0, "green_test_ran": true, "restore_sha256_matches": true, "mtime_restored": true},
    {"id": "P3_step_budget_ignores_progress", "file": "src/config.rs", "test": "config::tests::the_step_budget_responds_to_progress", "red_exit_code": 101, "red_test_ran": true, "green_exit_code": 0, "green_test_ran": true, "restore_sha256_matches": true, "mtime_restored": true},
    {"id": "P4_repeated_success_not_counted", "file": "src/harness/guard.rs", "test": "harness::guard::tests::the_same_successful_action_repeated_to_its_cap_aborts_the_call", "red_exit_code": 101, "red_test_ran": true, "green_exit_code": 0, "green_test_ran": true, "restore_sha256_matches": true, "mtime_restored": true}
  ],
  "could_not_verify": [
    "no live Bevy process was started (offline batch), so the launcher's identity handshake has never met a real game; its wire shape (`world.get_resources` of `hof_game::contract::ProcessNonce`, whose reply is `value` -> `value` -> `<nonce>`) is the contract's own field name and was tested against a fake listener, not against the engine",
    "the launcher now refuses a launch when the endpoint is already held; no recorded round exercised a free-port preflight, so its cost on a real round is unmeasured",
    "the reason the round-2 stop path left three live games is not established; this batch makes the death verifiable and enforced (`stop.pid_dead`) and reaps what the round recorded, and it says so rather than claiming a root cause",
    "the recorded token arithmetic is an average over 150 (or 104) calls with one provider; the per-call figures are provider-reported and the fit is post-hoc",
    "`--env-from-secret` was never run end to end against `hoh run` (no model, no network); its rule and its loading are unit-tested",
    "no round was run, so the two new mechanisms have never met a real Developer"
  ],
  "single_most_important_thing_for_round_3": "Run one real iteration and read runs/<round>/launch.json before reading any battery verdict: check identity.verified true, identity.nonce equal to the nonce the launcher generated, identity.answering_pid equal to identity.spawned_pid, and stop.pid_dead true. If any of those is false or absent, the battery's greens and reds both describe an unknown process and the round must be stopped rather than read; if all four hold, round 3's economics are the first ones in this project that are worth measuring."
}
```

The JSON above is serialiser output; it was parsed back out of this file before the rest of the report was
written.

---

## 1. Binding a pass to the process it launched

**What was wrong.** Round 2's readiness probe accepted *any* process that answered `rpc.discover` on
15702. A stale game holds the port (Windows `SO_REUSEADDR` lets the new one bind beside it), and the
probe cannot tell which one replied, so the battery read the A0 scaffold's frame counter and reported
it as the candidate's behaviour — twice.

**What changed.**

1. **A per-launch nonce, proved over the wire.** `launch::new_process_nonce()` generates a UUIDv4 per
   launch *before* the spawn; the launcher puts it in the game's environment as
   `HOF_GAME_PROCESS_NONCE`; `Readiness` is now `rpc.discover` **and** a `world.get_resources` read of
   the contract's new eighth surface, `hof_game::contract::ProcessNonce`. A value that is not this
   launch's nonce is `LaunchError::IdentityMismatch`, and the process is stopped before returning.
2. **The endpoint must be free to launch on it.** `port_is_free` binds the port and releases it
   without `SO_REUSEADDR`; `listener_pid` reads the OS's own TCP table for a second, independent
   reading. A held port is `LaunchError::EndpointBusy` and the pass is refused at once instead of
   waiting out the readiness budget.
3. **The previous session is reaped and its death verified.** Every launch appends
   `{pid, endpoint, port, nonce, launch_image}` to `runs/bevy-<round>/launch-ledger.jsonl` **before**
   the spawn; the next launch kills each recorded pid that is still alive (`taskkill /F /T /PID`) and
   polls until it is gone. Only pids this round recorded are touched.
4. **The death is verified at the other end too.** After `stop`, `round::run` records
   `stop.pid_dead`, killing a survivor and re-verifying — "we asked it to stop" is no longer the same
   value as "it stopped".
5. **The launch record says which process answered.** `launch.json` now carries an `identity` object:
   `spawned_pid`, `nonce`, `launch_image`, `built_binary`, `listening_pid`, `reaped_pids`, `ledger`,
   `answering_pid`, `verified`. `binary` also carries the executed image's digest and
   `executed_matches_built`, so "the observations belong to the built binary" is checkable rather than
   assumed.

**The test that pins it (the competing-listener test).**
`adapter::bevy::launch::tests::a_competing_listener_on_the_endpoint_refuses_the_launch` plants a real
loopback listener that answers `rpc.discover` exactly as BRP does and serves *a different nonce*; the
launch is refused with `EndpointBusy` in under 300 ms, i.e. without waiting for the readiness budget.
The identity half is pinned by
`a_listener_that_serves_a_different_nonce_fails_readiness`, which plants a listener that holds the port
silently, releases it after the launch's preflight has passed, and answers with the previous session's
nonce: readiness fails with `IdentityMismatch` carrying both values and the spawned pid. The positive
control is `a_listener_that_serves_the_launch_nonce_is_accepted` — without it, "readiness checks
identity" would be satisfied by a check that always refuses. Reaping is pinned by
`a_pid_this_round_recorded_is_reaped_before_the_next_launch` (and its control,
`a_pid_the_ledger_never_named_is_left_alone`).

**What it does not cover.** The launcher has never met a real Bevy game in this batch: the real
`world.get_resources` reply shape comes from the contract and was tested against a fake. The two
defences are also not independent of each other in time — the preflight is best-effort (a listener can
appear after it) and the nonce is the proof, which is why both are recorded.

**One design point worth stating.** The new surface changes the frozen contract hash from
`792001e7…` to `c579a742…`. That is deliberate and is re-pinned in three places plus a literal in
`bevy_adapter_b2.rs`; the alternative — a nonce that is not reflectable — would have made identity
unprovable against a game whose source we do not own.

## 2. Building from a role while a game runs

**What was wrong.** A running Windows executable cannot be opened for writing, so `cargo` fails with
`failed to remove file … hof_game.exe (os error 5, Access is denied)` when it relinks the binary the
round's own game is running from. Round 2 measured the rename workaround at about eight calls.

**What changed.** `launch::stage_image` copies the built binary into
`runs/bevy-<round>/launch-image/<launch-uuid>/` and the launcher executes **that** copy. The file
cargo must replace is therefore never the file that is running, and the round records the executed
path and both digests. The game's own working directory remains the executable's directory, which is
the closest thing to "where cargo would have run it" that the launcher can know.

**The test that pins it.**
`adapter::bevy::launch::tests::the_launched_image_is_a_staged_copy_and_the_built_binary_is_left_alone`
asserts the executed path is under the stage root, that the staged bytes equal the built bytes, that
the built binary's mtime is untouched, and — the point of the whole task — that the built binary can
be **overwritten while the game is running**.

**What it does not cover.** The real cargo relink was not reproduced (no engine build in this batch);
the lock's shape is pinned by the write-the-running-binary assertion, which is the operation cargo
performs at link time. Staging also means the round now measures two digests; if they disagree, the
round says so instead of deciding.

## 3. Round 1 under the new rule

**Verdict: round 1's five observations were not taken from the artifact round 1 claimed.** They came
from a process that was already running when the Developer started — almost certainly the round's own
A0 session game — and no file in `runs/bevy-round1b/` can show it, because `launch.json` recorded only
the pid the harness hoped for.

The arithmetic, all of it from recorded evidence:

| quantity | value | source |
|---|---|---|
| `hoh run` start | `1791080101` | `runs/round1b/meta.json.started_at` |
| first battery call | `1791083488.844` | `runs/bevy-round1b/calls/0001-bevy_grounded.json.timestamp_ms` |
| first frame read | `198376` | same call's `world.get_resources` reply |
| frames/second in the battery window | `58.96` | `198376 -> 198528` over `2.578 s` (46 calls) |
| implied process start | `1791080127` | `first_call - 198376/58.96` |
| implied start − run start | **`+26 s`** | |
| first read − run start | `+3388 s` (56 min) | |
| battery `launch.json` pid | `35436` (`ready_millis: 47`) | `runs/bevy-round1b/launch.json` |
| run `meta.json` game pid | `6848` | `runs/round1b/meta.json.engine.mcp.game_endpoint.pid` |

A process that begins counting frames 26 seconds after the run starts is not the process the battery
launched 56 minutes later; and the pid the battery recorded is not the pid the run recorded either.
Three different pids for one window is the round-2 pattern, one round earlier.

Two pieces of corroboration. First, the recorded jump arc: the battery's own arc is
`first = -200.0`, `peak = -165.015`, `rising = 4`, `falling = 8` — the A0 scaffold's replay gives
`first = -200.0`, `peak = -165.274`, and round 1's own final-artifact replay gives a different arc.
Second, `ready_millis: 47` says the process the launcher started answered in 47 ms; the process that
answered in practice had 3362 seconds of frames behind it.

**What this does not mean.** The game is still right: round 2's independent replay, with the strays
killed, showed the final artifact satisfies all nine battery steps, and nothing here re-tests round 1's
artifact. What fails is the *claim*: round 1's five-criterion success must be re-read as unverified,
and every green ever produced by the old readiness path is untrustworthy until a pass proves identity.

## 4. The cost driver

**The measurement.** `tests/repeated_action.rs` and the census scripts over
`runs/round2/iter-{1,2}/traj/developer.attempt1.json`:

| quantity | iter-1 | iter-2 |
|---|---|---|
| api calls | 150 | 104 |
| prompt tokens/call, first → last | 4,187 → 115,698 | 4,187 → 108,388 |
| prompt tokens/call, average | **74,059** | **77,266** |
| prompt tokens, total | 11,108,856 | 8,035,712 |
| system prompt | 14,117 B (~5% of the final prompt) | same |
| wire bytes (`content` + `tool_calls`) | 415,748 | 386,154 |
| local-only bytes (`extra`, never sent) | 949,357 | 579,559 |
| final prompt tokens per wire byte | 0.28 | 0.28 |
| growth per message | 404 tokens | 443 tokens |

**What dominates.** Call count times accumulated history. The per-call prompt *is* the accumulated
history (`4187 + 0.28 × wire bytes`): summing that over iteration 1's 150 calls reproduces the
provider-reported 11,108,856 exactly. Two candidate explanations are eliminated by measurement: the
system prompt is about 5% of the final prompt, so it cannot be the 74k; and the 949,357 bytes in
`message.extra` are local — mini's `to_llm_message` sends only `content` and `tool_calls`, so the
billed driver is not the trajectory's serialization. A fixed step budget multiplied by a growing
history is the whole arithmetic.

**What changed.**

1. **The repeated-action tripwire fires on successes.** `agent.max_repeated_actions = 15` counts the
   same action's **total successes in one call** (not a consecutive run: the recorded loop spelled
   itself with `| more`, `| findstr …` and `& echo …=%ERRORLEVEL%`, so no consecutive run is long).
   On the cap, the call aborts with the runtime's own first-class `RepeatedActionError`. The number is
   measured, not chosen: iteration 2 — engineering work whose last build the artifact survived —
   repeats its most-repeated action 14 times, iteration 1 repeats its most-repeated action 39 times,
   so 15 cannot fire on the clean call and does fire on the grind. Projected over the recorded
   per-call prompt tokens, an abort at api call 50 keeps **1,703,158 of 11,108,856 (15.3%)**.
2. **The step budget responds to progress.** `agent.steps_per_artifact = 8`: a call that has written
   nothing gets `25 + 150/8 = 43` steps; the first successful project write earns the flat 150. The
   prompt is told the number it is really held to, with the rule that produced it
   (`guard::state_the_effective_budget`). Round 2's Developer made its first write on message 14 of a
   150-step call, so the gate cannot fire on a call that is working; round 1's shape (140 calls, one
   file, no increment for 54 minutes) cannot spend the budget at all.

**Honest negative result.** The tripwire would **not** have helped iteration 2 (its most-repeated
action is 14 legitimate rebuilds, and its grind was coverage work spread over many *different*
actions, which no repeat counter can see), and it fires late in iteration 1 (call 50, not call 10)
because the recorded Developer's first ~50 calls contain real edits. What it removes is the tail — the
~70 verification calls that produced nothing — which is exactly the tail that ended in
`LimitsExceeded`. The progress gate is the mechanism that bounds a call which produces nothing; the
tripwire bounds one that repeats itself. Both are needed and neither alone reaches the 1.5M target.

**What it does not cover.** The projection is post-hoc arithmetic over provider-reported per-call
tokens, not a measured run. `max_tool_output_bytes` (64 KiB) was left alone: the two 65 KB evidence
dumps in iteration 2 are a real but secondary cost, and lowering the cap would truncate evidence a
Tester cites — a decision for a batch that can measure it without destroying evidence.

## 5. The credential leak

- `config/model.secret.env` (205 bytes, file sha256 `84233e38…`, one 51-character key-shaped value with
  fingerprint `5cf81e8f`) was **removed from the tree**. The removal was a single-file delete over a
  path that was printed and verified first; `rm -rf` was not used anywhere in this batch. The file was
  gitignored and untracked, so nothing in version control changed.
- The browsable tree is clean: `tests/credential_scan.rs::no_key_shaped_material_is_browsable_in_the_repository_tree`
  scans every file under the repository root except `.git/`, `target/`, `.workspace/`, `runs/`,
  `node_modules/` and reports **0 findings**.
- Secrets now load only from outside the repository. `--env-from-secret <path>` is the named
  mechanism; the path is refused if it is inside the repository, if it does not exist, or if it holds
  no key-shaped `KEY=VALUE` line, and the value is returned and exported but never printed.
- **Reported, not rewritten:** the recorded evidence still holds the key in exactly two files —
  `runs/round1/iter-1/traj/developer.attempt1.json` and `runs/round1b/iter-1/traj/tester.attempt1.json`
  (fingerprint `5cf81e8f`, length 51). They are gitignored evidence that the round-1 report cites, so
  they are in no browsable tree and in no archive of this repository; rewriting them would destroy the
  evidence a report has to be checked against. **The key must be rotated by its owner.**
- **A correction to the round-2 report's own census.** An earlier, looser shape rule reported 24
  `sk-` hits in `runs/round1b/iter-1/traj/developer.attempt1.json`. All 24 are the substring `sk-`
  inside the Rust crate names `async-task-…` and `futures-task-…`; they are not credential material.
  The corrected rule (a hyphen before the prefix is a token boundary) finds **none** there, and this
  correction is itself pinned by
  `tests/credential_scan.rs::the_crate_names_in_the_recorded_evidence_are_not_credentials`.

## 6. Controlled plants

Four plants, each green-red-green with a byte-exact restore and an explicitly restored mtime
(`F:/hof-trust-scripts/plants.json`):

| plant | file | test | red | green |
|---|---|---|---|---|
| P1 fallback that accepts any listener | `src/adapter/bevy/launch.rs` | `a_listener_that_serves_a_different_nonce_fails_readiness` | 101, test ran | 0 |
| P2 reap path not implemented | `src/adapter/bevy/launch.rs` | `a_pid_this_round_recorded_is_reaped_before_the_next_launch` | 101, compile error | 0 |
| P3 step gate removed | `src/config.rs` | `config::tests::the_step_budget_responds_to_progress` | 101, test ran | 0 |
| P4 repeated-success counter disabled | `src/harness/guard.rs` | `the_same_successful_action_repeated_to_its_cap_aborts_the_call` | 101, test ran | 0 |

Every restore is `restore_sha256_matches: true` and `mtime_restored: true`. P2 is the one plant whose
red is a **compile error** rather than a failing assertion: the runtime version of it (a reap path that
does nothing) leaves the stand-in process alive and hangs the test, and this harness records a killed
run as "did not run" rather than as a red — a hung test proves nothing about the assertion. The red
still demonstrates that the test is load-bearing on the reap code; the runnable plant lives one line
away in `reap_ledger` and is exercised by the green/red of
`a_pid_this_round_recorded_is_reaped_before_the_next_launch` against a live process.

## 7. What could not be verified

- **No live engine.** The identity handshake has never met a real Bevy process; the wire shape is the
  contract's own field name and was tested against a fake listener. The reason the round-2 stop left
  three live games is **not** established — this batch makes the death verifiable and enforced
  (`stop.pid_dead`) and reaps what the round recorded, and says so instead of claiming a root cause.
- **The new preflight's cost** on a real round is unmeasured: no recorded round exercised a free-port
  check.
- **The projection is arithmetic**, not a run; provider-reported per-call tokens, one provider, a
  post-hoc fit.
- **`--env-from-secret` was never run end to end** against `hoh run` (no model, no network); its rule
  and its loading are unit-tested.
- **Neither new mechanism has met a real Developer**, because no round was run.

## 8. The single most important thing for the next batch

**Run one real iteration and read `runs/<round>/launch.json` before reading any battery verdict.**
Check four fields: `identity.verified == true`, `identity.nonce` equal to the nonce the launcher
generated, `identity.answering_pid == identity.spawned_pid`, and `stop.pid_dead == true`. If any is
false or absent, both the greens and the reds describe an unknown process and the round must be
stopped rather than read. If all four hold, round 3's economics are the first ones in this project
worth measuring — and the first number to look at is not the artifact but the Developer's call count,
because that is what the 74k-per-call arithmetic multiplies.
