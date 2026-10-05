```json
{
  "schema": "hof-rs / bevy round 4 report",
  "produced_at": "2026-10-05T09:13:21.691599",
  "branch": "bevy-core",
  "head": "1c1aaefdf42c37e75a92133a50a15d7f58c152fc",
  "report_scope_note": "This report was written while round 4 was still running (the parent asked for it at 09:10, thirteen minutes into a round that took 68 minutes in round 3). Everything about the inherited work, the two cost controls, the stop, attribution, the transport gap, the gate and the plants is finished and measured; the round's own identity fields, battery steps, economics, fingerprints and PRD coverage were **not yet available** and are reported as null with the live snapshot that existed at write time. The round continues.",
  "inherited_work_triage": {
    "how_to_read": "Every tracked file the dead agent left modified, plus both files it added. `kept` = sound as it stood; `finished` = sound but with a claim or measurement I re-measured and corrected; `fixed` = wrong or misleading and repaired.",
    "tracked_files_modified_by_the_dead_agent": 19,
    "files": [
      {
        "file": "config/hoh.yaml",
        "dead_agent": "Documented the model-call unit of `step_limit`, the rewrite of `max_repeated_actions` (fold + restart-on-write) and the per-step enforcement of `steps_per_artifact`.",
        "verdict": "kept, finished",
        "reason": "The mechanism descriptions are right; two evidence claims were not measured and are now measured and corrected: round 3's iteration 1 emitted 15 `cargo build` calls in 12 distinct spellings (14 carrying a `| tail` filter), not '9 builds in three spellings'; and the window figure is a maximum over post-write windows, not 'the last write'. The values themselves (15, 8, 150) are unchanged."
      },
      {
        "file": "src/adapter/bevy/launch.rs",
        "dead_agent": "Lifted the test-only `launch_stand_in` helper to `pub(crate)` so `mod.rs`'s real-process tests can reuse it; the launch tests call through.",
        "verdict": "kept",
        "reason": "Pure refactor of test scaffolding, no behaviour change, and it is what lets the round-game and sweep tests hold a real pid."
      },
      {
        "file": "src/adapter/bevy/mod.rs",
        "dead_agent": "Added `shared_launch` (a peer's launch facts visible to the runtime's adapter), `client_generation`, `take_started_process`/`set_round_game_process`/`take_round_game_process`, `reap_round_processes`, `verified_game_endpoint`, `rebind_observing_client`, and five real-process tests.",
        "verdict": "kept",
        "reason": "It fixes the round-3 field mix-up (`start` writes `process`, the window read an always-empty `round_game` slot) and adds the ledger-wide sweep. Load-bearing: plants P4 and P5 turn two of its tests red, and the byte-exact restore turns them green again. The one link not pinned by a gate test is `start_round_game`'s call to `take_started_process`; that wiring's evidence is the round itself."
      },
      {
        "file": "src/adapter/bevy/project.rs",
        "dead_agent": "`start_round_game` now hands `start`'s own process to the window; `stop_round_game` sweeps the whole launch ledger, verifies the deaths and bails naming survivors; new `RoundStopReport` written to `runs/bevy-<round>/round-stop.json`; role-announced endpoints carry no nonce claim.",
        "verdict": "kept",
        "reason": "This is the round-3 stray's fix and it is the right layer: the ledger is written before every spawn for battery and role-session launches alike, so the sweep does not depend on the slot being right. `verified: None` for a role-announced endpoint is honest rather than borrowing a proof it does not have."
      },
      {
        "file": "src/adapter/bevy/round.rs",
        "dead_agent": "(untouched by the dead agent; this is this batch's own change)",
        "verdict": "fixed",
        "reason": "Round 3 wrote `identity.verified: true` as a literal and `identity.answering_pid` as a copy of `spawned_pid`, so two of the four gate fields were true by construction. They are now computed: `answering_pid` is the OS TCP table's own listener reading and `verified` is true only when the launch carries a non-empty proved nonce, with the rule written into the record as `verified_rule`. Also added `client_generation` to `launch.json` so a real pass records that the observing client was rebuilt at the process boundary. New test `the_identity_fields_are_computed_from_the_facts_not_asserted`."
      },
      {
        "file": "src/adapter/mod.rs",
        "dead_agent": "`ProjectAdapter::verified_game_endpoint()` defaulting to `None`.",
        "verdict": "kept",
        "reason": "An adapter that proves no identity must not have one invented for it; the runtime keeps its old fallback for those."
      },
      {
        "file": "src/config.rs",
        "dead_agent": "Rewrote the `max_repeated_actions` and `steps_per_artifact` docs for the new window and the per-step enforcement.",
        "verdict": "kept, finished",
        "reason": "The claims are now the measured ones: the legitimate window maximum is 7 and the grind's is 22 (the old prose said 'after its last write', which the measurement does not support \u2014 it is a maximum over windows). `default_max_repeated_actions` is still 15."
      },
      {
        "file": "src/harness/guard.rs",
        "dead_agent": "Added `StepCounter` (a step is a model call), `STEP_BUDGET_STATUS`, per-step `step_budget_exceeded` re-reading `effective_step_budget`; extended the action key to fold `| tail`/`| head` and trailing redirections; made a counted artifact write clear the repeated-action counter; `ArtifactKind::counts`; six tests.",
        "verdict": "kept, finished",
        "reason": "This is the round-3 headline fix and it is enforced where it applies. Load-bearing: plants P1, P2 and P3 turn its three tests red. Finished here: the abort message and its two assertions said 'succeeded N times in this call', which is no longer the rule; they now say 'since this call last wrote the artifact it declares', and the stale `FailFast::RepeatedSuccess` doc says the same."
      },
      {
        "file": "src/harness/mini.rs",
        "dead_agent": "`CountingModel` counts model calls where they are made and shares the count with the guard; `AgentConfig.step_limit` is fed the flat ceiling, not the gated value; the `[budget]` note is rendered from the live and flat values.",
        "verdict": "kept",
        "reason": "This is the precise inverse of round 3's one-line defect at the old line 115. It is also what makes the note's numbers true: the body's 150 is the ceiling mini itself enforces, the note's 43 is what the guard re-reads, and a write raises the second one inside the call."
      },
      {
        "file": "src/runtime/invoke.rs",
        "dead_agent": "`StepBudgetExceeded` is classified as a limit by `is_limits_exceeded`.",
        "verdict": "kept",
        "reason": "The wrap-up retry logic asks 'did this call run out of budget?'; the guard's own step abort is exactly that, and keeping a distinct status is what lets a round say which budget ran out."
      },
      {
        "file": "src/runtime/run_loop.rs",
        "dead_agent": "Both battery meta write-backs prefer `adapter.verified_game_endpoint()` over the channel's 'last endpoint ever registered' history.",
        "verdict": "kept",
        "reason": "Directly answers round 3's pid 34124, which was a pid and no proof. The dead agent's own attempt-1 meta already shows the result: `source: launch_verified`, a nonce, and `answering_pid`."
      },
      {
        "file": "src/runtime/write_failure.rs",
        "dead_agent": "`StepBudgetExceeded` is a failure status.",
        "verdict": "kept",
        "reason": "A call that exhausted its live step budget did not finish its work; the write-failure accounting must see it."
      },
      {
        "file": "src/tools/endpoint.rs",
        "dead_agent": "`GameEndpointRecord` gained optional `nonce`, `answering_pid`, `verified` and a new `SOURCE_LAUNCH_VERIFIED` provenance.",
        "verdict": "kept",
        "reason": "All three fields are `skip_serializing_if = none`, so existing records serialise byte-identically; the new provenance is a distinct value because 'the engine's default port' and 'proved by this launch's nonce' are different claims."
      },
      {
        "file": "tests/cold_start_grace.rs",
        "dead_agent": "Three new `None` fields at the `GameEndpointRecord` construction site.",
        "verdict": "kept",
        "reason": "Mechanical consequence of the record's new fields. Same for tests/common/mod.rs, tests/endpoint_liveness.rs, tests/endpoint_request_count.rs, tests/engine_identity.rs and tests/game_route_across_processes.rs (two sites)."
      },
      {
        "file": "tests/repeated_action.rs",
        "dead_agent": "Re-derived the cap from the recorded trajectories under the round-4 rule and added a round-3 test; loosened the iter-1 projection assertion to `fraction < 0.95`.",
        "verdict": "fixed",
        "reason": "The measurement was wrong in a way that mattered: `most_repeated_current_window` was the counts of the **last** window, so round 2's iteration 1 printed a window maximum of 1 while its own `abort_at` said a window had reached the cap \u2014 one measurement contradicting itself, and it is the number the cap is derived from. It is now the maximum over all post-write windows, and the figures are pinned: 22 (window) / 54 (whole call) for the grind, 7 for the legitimate call, 5/2/4 for round 3's three Developer calls. The loosened bound is replaced by the measured 75-80%, because `fraction < 0.95` would pass even if the tripwire saved nothing."
      },
      {
        "file": "tests/brp_connection_pool.rs",
        "dead_agent": "New file: a real loopback peer that answers `Connection: keep-alive` and then closes with `SO_LINGER 0` (a reset), proving a pooled socket to a dead peer fails the next call at the transport layer, plus the control that a rebuilt client succeeds.",
        "verdict": "kept, with one defect reported and not fixed",
        "reason": "Nobody had run it; I ran it in the gate twice (exit 0 both times) and it is the right shape: it reproduces the mechanism with real sockets instead of mocking it. Defect: the module doc says 'Off Windows the helper is a no-op and the test says it measured nothing', but only the first test says so \u2014 the second has no `cfg!(windows)` guard, so elsewhere it would assert a Windows behaviour. Not fixed because the fix would have landed after the gate measurement and made the reported counts describe a tree that no longer exists; it is a one-line guard for the next batch."
      },
      {
        "file": "tests/brp_real_handover.rs",
        "dead_agent": "New file: three `#[ignore]`d tests that drive a real staged `hof_game.exe` through two launches, including one that reads `adapter.client_generation()` after each launch to pin that `start` really rebinds.",
        "verdict": "kept",
        "reason": "It is a no-op without `HOF_BEVY_GAME_IMAGE` and says so, so it can never pass vacuously in the default gate. It is the only pin of the rebind's **call site**: the dead agent's own plant P5 removed `self.rebind_observing_client();` from `start` and this test went red (exit 101, test ran) with a real image and `--ignored`. I did not re-run it, because it starts games on 15702 and round 4 holds the endpoint."
      }
    ]
  },
  "task_verdicts": {
    "step_budget": {
      "verdict": "follows progress, and is enforced where it applies",
      "mechanism": "A step is one **model call** (`CountingModel` increments before each model call; `agent.step_limit` and mini's own `n_calls` are the same unit). The guard re-reads `effective_step_budget()` inside `Environment::execute`, i.e. at the point the next step's actions are refused, so a counted artifact write inside the call raises it immediately. mini's own `AgentConfig.step_limit` is the flat ceiling (150), not the gated value.",
      "numbers_the_prompt_states_and_what_is_enforced": {
        "body": "`{{step_limit}}` renders the configured flat ceiling, 150; the note names it as the ceiling.",
        "note": "`[budget] The flat limit in the instructions above (150) is this call's ceiling. Until this call writes the artifact it declares, the budget actually enforced on it is 43; the first successful project write raises it to 150. That limit is re-read at every step ...`",
        "enforced": "43 model calls while nothing counted has been written, 150 after the first counted write, re-read at every step; mini's flat interrupt at 150 remains the backstop."
      },
      "evidence": "plant P1 (the budget frozen at the unwritten 43, which is round 3's defect in another dress) turns `harness::guard::tests::the_step_budget_is_re_read_where_it_is_enforced` red (exit 101, test ran) and the restore turns it green; the guard test drives the three cases directly (refused after the live budget, refused in model-call units when one response carries several actions, allowed past the old cap after a write inside the call); a real run already falsified the first attempt's action-unit version (attempt 1, exit 2, `StepBudgetExceeded` after 30 model calls).",
      "honest_limit": "Not yet confirmed by a live pass in this report's round: the round was still in its first iteration when this was written."
    },
    "tripwire": {
      "verdict": "reachable, and weak; not inert, and not doing anything in normal operation",
      "what_was_wrong": "The accounting. Round 3's iteration 1 emitted 15 `cargo build` calls in 12 distinct spellings (14 with a `| tail` filter); the old key folded only `| more`/`| findstr`, so it counted the most repeated action as 3 and the cap of 15 was never near. The dead agent's fold is the fix and it is proven by plant P3.",
      "threshold": "15 is measured: it is more than twice the highest legitimate post-write window count in all recorded Developer calls (7, round 2's iteration 2; 5/2/4 for round 3's).",
      "consideration": "The restart-on-write is a deliberate choice, not an accounting fix, and it is what keeps the tripwire silent on round 3: whole-call counting with the folded key would have reached exactly 15 on round 3's iteration 1 and aborted a call that was interleaving writes with rebuilds. I kept the choice and state its cost: on every recorded call that was producing, the tripwire does nothing.",
      "measured_behaviour": {
        "round_2_iter_1_grind": {
          "window_max": 22,
          "whole_call_max": 54,
          "abort_at_api_call": 126,
          "of_api_calls": 150,
          "prompt_tokens_kept_fraction": 0.773
        },
        "round_2_iter_2_clean": {
          "window_max": 7,
          "whole_call_max": 15,
          "abort_at_api_call": null
        },
        "round_3_iter_1": {
          "window_max": 5,
          "whole_call_max": 15,
          "abort_at_api_call": null,
          "api_calls": 43
        },
        "round_3_iter_2": {
          "window_max": 2,
          "whole_call_max": 8,
          "abort_at_api_call": null,
          "api_calls": 43
        },
        "round_3_iter_3": {
          "window_max": 4,
          "whole_call_max": 9,
          "abort_at_api_call": null,
          "api_calls": 43
        },
        "reading": "It fires on the recorded grind, late (call 126 of 150, keeping 77% of that call's prompt tokens), and on no recorded normal call. Whether a live round ever trips it is still unmeasured; round 3's value came from saying so."
      },
      "evidence": "tests/repeated_action.rs (prints each figure and pins 22/54/7), harness::guard::tests::a_write_of_the_artifact_restarts_the_repeated_action_counter and the_same_action_spelled_with_a_filter_or_a_redirection_is_one_action (plants P2 and P3)."
    },
    "role_session_stop": {
      "verdict": "closed in code; end-to-end confirmation was still in flight at report time",
      "mechanism": "The window now owns the process `start` really produced (`start_round_game` moves `BevyAdapter::process` into the window slot). Independently, `stop_round_game` sweeps every pid the round's launch ledger records \u2014 the ledger is appended before every spawn, for battery and role-session launches alike \u2014 kills survivors, verifies each death, writes `runs/bevy-<round>/round-stop.json`, and returns an error naming any pid that is still alive. `run()` calls the stop on every exit path of the round.",
      "test_that_pins_it": [
        "adapter::bevy::tests::the_round_game_window_receives_the_process_start_produced (real child process; plant P5 reddens it)",
        "adapter::bevy::tests::the_round_stop_sweep_reaps_every_recorded_process_and_writes_its_evidence (two real children; plant P4 reddens it)",
        "adapter::bevy::tests::the_round_stop_sweep_leaves_a_process_the_ledger_never_named (control: never kill what this round did not start)",
        "tests/brp_real_handover.rs::the_adapter_rebinds_its_observing_client_at_every_launch (ignored; real engine; also asserts both launches are on the ledger and both are verified dead)"
      ],
      "residual_risk": "The ledger sweep kills a recorded pid on liveness alone. Inside one round the pids are minutes old and a recycled pid is unlikely, but the sweep is not image-checked; a long round on a busy machine is the case where that could matter."
    },
    "run_level_attribution": {
      "verdict": "yes \u2014 the run's metadata now names a proved identity, and the battery's own gate fields are no longer tautological",
      "mechanism": "`BevyAdapter::verified_game_endpoint()` returns the last launch's facts (per-launch nonce + the OS TCP table's listener reading, `source: launch_verified`) from a slot shared with the peers, and both meta write-backs prefer it over the channel's endpoint history. In `launch.json`, `answering_pid` is that OS reading (not a copy of `spawned_pid`) and `verified` is derived from the non-empty proved nonce, with the rule written next to it.",
      "evidence": "the dead agent's attempt-1 `runs/round4-attempt1/meta.json` already shows the new shape \u2014 `source: launch_verified`, `nonce: 0fe243a7-\u2026`, `answering_pid: 46784` equal to `pid: 46784`, `verified: true` \u2014 where round 3's `runs/round3/meta.json` had `source: engine_default`, `pid: 34124` and nothing else; plus the new unit test for the derivation.",
      "caveat": "The identity still rests on the nonce proof (readiness refuses a reply serving another nonce) plus the OS reading; `verified` does not itself test the OS table, deliberately, so an unreadable TCP table cannot turn a proof into a coin toss."
    },
    "transport_gap": {
      "verdict": "real fragility, not a probe-ordering artefact \u2014 and the inherited connection-pool test is an attempt at exactly this, and a sound one",
      "mechanism": "`BrpClient` is `Clone` over one `ureq::Agent`, whose connection pool is shared by every clone. `round_peer()` clones the runtime adapter's client, so every battery pass starts with the pool of whatever talked last. Round 3's pass 1 had never talked to anything (clean first call); passes 2 and 3 inherited a pooled keep-alive socket to the previous, now-dead game and their **first** call failed at the transport layer, while the retry (on a fresh connection) succeeded. That is the recorded shape exactly: one failure, at frame 0, in the first sequenced call of each pass after the first.",
      "fix": "`BevyAdapter::start` rebuilds the observing client \u2014 and the MCP server built over it \u2014 at every launch, so the observing client is bound to the process observed. The launch record now carries `client_generation` so a real round's evidence shows the rebuild happened.",
      "pins": [
        "tests/brp_connection_pool.rs (client level, real sockets, in the default gate)",
        "tests/brp_real_handover.rs::the_adapter_rebinds_its_observing_client_at_every_launch (call site, ignored, real engine; proven load-bearing by the dead agent's plant P5)"
      ],
      "not_verified": "No live pass in this report's round confirms it yet; the round had not reached its first battery when this was written."
    }
  },
  "round_4": {
    "status": "in_flight_at_report_time",
    "project": "F:/hof-bevy-r4-run/workspace",
    "project_outside_repository": true,
    "fresh_empty_project": true,
    "fresh_project_proof": "created empty by F:/hof-r4-work/py/prepare_round.py, which refuses a directory that already exists; the previous two partial round-4 attempts were moved (never deleted) to runs/round4-attempt2 and runs/bevy-round4-attempt2",
    "init_command": "F:/hof-r4-target/debug/hoh.exe init --adapter bevy --project F:/hof-bevy-r4-run/workspace",
    "init_exit_code": 0,
    "init_exit_code_source": "literal `$?` written to F:/hof-r4-logs/r4m.init.exit by F:/hof-r4-work/run_round4.sh",
    "run_command": "F:/hof-r4-target/debug/hoh.exe run --adapter bevy --project F:/hof-bevy-r4-run/workspace --run-id round4 --env-from-secret F:/hof-secrets/round4.env",
    "run_exit_code": null,
    "run_exit_code_source": "literal `$?` written to F:/hof-r4-logs/r4m.run.exit by the driver; the file did not exist at write time because the process had not exited",
    "as_of": "2026-10-05T09:11:09.966309",
    "run_started_at_unix": 1791161942,
    "iterations_requested": 3,
    "iterations_started": [
      "iter-1"
    ],
    "headless": true,
    "model": "deepseek-v4.1-flash",
    "endpoint_used": "http://127.0.0.1:15702/",
    "second_endpoint_15703_used": false,
    "cli_binary": {
      "path": "F:/hof-r4-target/debug/hoh.exe",
      "sha256": "e8862581d7ed485cbef48d8ee949d38a0bf29e33433683ef63c6645f1710d277",
      "built_at": "2026-10-05T08:58:29",
      "note": "built from this tree; unlike round 3's first attempt the binary is younger than the code it runs"
    },
    "pre_run_stale_check": {
      "when": "2026-10-05T08:58:47",
      "method": "netstat -ano filtered on 15702/15703 and tasklist /FI \"IMAGENAME eq hof_game.exe\"",
      "observed": "no line for either port and no hof_game.exe process",
      "engine_second_endpoint_used": false
    },
    "live_snapshot": {
      "netstat_15702_15703": "(no line)",
      "tasklist_hof_game": "INFO: No tasks are running which match the specified criteria.",
      "run_stdout_tail": [
        "[ok] bevy.lockfile: F:/hof-bevy-r4-run/workspace\\Cargo.lock sha256 660e7e17b62921ac409d0e2b023273ce1426959cbd386f21832e03745068c8df",
        "[ok] bevy.contract: 8 frozen semantic surface(s); contract sha256 c579a742cea5f2f22b0e34c2ae6ab3bafcb56050310a5d35e95941796bdcf7e9; endpoint http://127.0.0.1:15702/",
        "[ok] tools.mcp: 31 tools available at http://127.0.0.1:15702/"
      ],
      "warnings_log": [
        "qa_scope: MCP acts on the project open in the editor (the real workspace) while the Tester evaluates a frozen copy; the runtime binds both to one candidate identity with pre-QA and around-QA hash assertions (D7).",
        "DR-70: the round's game session could not be started (the game could not be started: the game binary `F:/hof-bevy-r4-run\\hof-bevy-shared-target\\debug\\hof_game.exe` does not exist: the build did not produce it); the game route stays withdrawn until the battery starts its own game, so every `running_game_*` call from a role shell fails with `game_endpoint_unavailable` (DR-43) for this window"
      ],
      "bevy_round4_files": [],
      "note": "no game process existed at this instant because the round was in its Planner stage; every launch is recorded in runs/bevy-round4/launch-ledger.jsonl when it happens"
    },
    "identity_gate": {
      "status": "not_available_at_report_time",
      "rule": "a round's observations may be read only if runs/bevy-round4/launch.json shows identity.verified true, identity.nonce equal to the nonce that launch generated, identity.answering_pid equal to identity.spawned_pid, and stop.pid_dead true; any false or absent means the round produced no usable observation",
      "raw_identity_fields": null,
      "raw_stop_fields": null,
      "gate": null,
      "reason": "runs/bevy-round4/ did not exist at write time; the round had not reached its first battery pass. No battery verdict is quoted anywhere in this report."
    },
    "developer_economics": {
      "round_3": {
        "iterations": [
          {
            "iteration": 1,
            "role": "developer",
            "exit_status": "LimitsExceeded",
            "calls": 43,
            "duration_ms": 1402327,
            "total_tokens": 1619423
          },
          {
            "iteration": 2,
            "role": "developer",
            "exit_status": "LimitsExceeded",
            "calls": 43,
            "duration_ms": 1092932,
            "total_tokens": 2232476
          },
          {
            "iteration": 3,
            "role": "developer",
            "exit_status": "LimitsExceeded",
            "calls": 43,
            "duration_ms": 656894,
            "total_tokens": 2547916
          }
        ],
        "total": {
          "calls": 129,
          "duration_ms": 3152153,
          "duration_minutes": 52.5,
          "total_tokens": 6399815
        },
        "source": "runs/round3/iter-{1,2,3}/result.json (usage and durations_ms), read by F:/hof-r4-work/py/run_economics.py",
        "caveat": "all three ended at exactly 43 calls with LimitsExceeded because the gated value was frozen before the call: the economics are the economics of a truncated call"
      },
      "round_4": null,
      "reason_not_available": "no iteration had completed at write time"
    },
    "increment_fingerprints": null,
    "prd_coverage": null,
    "battery": {
      "status": "not_available_at_report_time",
      "steps_expected": 9,
      "steps": null,
      "reason": "runs/bevy-round4/launch.json and runs/bevy-round4/calls/ did not exist; the nine battery steps and their proving call ids are the round's to produce, and nothing here infers them"
    },
    "how_to_read_it_when_it_finishes": [
      "runs/bevy-round4/launch.json \u2014 identity fields and stop.pid_dead; apply the gate before reading any battery verdict",
      "runs/bevy-round4/calls/NNNN-*.json \u2014 the raw request/response pairs; the call ids are the file prefixes",
      "runs/bevy-round4/round-stop.json \u2014 the round-stop sweep: every pid recorded, reaped, still alive, and who held the endpoint",
      "runs/round4/game_endpoint.json and meta.json.engine.mcp.game_endpoint \u2014 the run-level identity (`source: launch_verified`)",
      "runs/round4/iter-*/result.json \u2014 usage, durations, prd_coverage, battery_passes, write_failures",
      "runs/round4/iter-*/traj/developer.attempt1.json \u2014 the Developer's own calls; F:/hof-r4-work/py/run_economics.py and census.py read them"
    ]
  },
  "gate": {
    "final_tree": {
      "command": "cargo test --offline",
      "exit_code": 0,
      "exit_code_source": "literal `$?` captured into F:/hof-r4-logs/final-gate.exit",
      "passed": 734,
      "failed": 0,
      "ignored": 6,
      "listed": 740,
      "listed_equals_passed_plus_ignored": true,
      "warning_lines": 0,
      "test_targets_reported": 56,
      "list_command": "cargo test --offline -- --list",
      "list_exit_code": 0,
      "fmt_command": "cargo fmt --all --check",
      "fmt_exit_code": 0,
      "build_dir": "F:/hof-r4-target (this batch's own; no second test process)"
    },
    "inherited_tree_as_received": {
      "command": "cargo test --offline",
      "exit_code": 0,
      "passed": 733,
      "failed": 0,
      "ignored": 6,
      "listed": 739,
      "warning_lines": 0,
      "note": "measured by this batch before any edit of its own: the dead agent's work already compiled, warned nothing and passed"
    },
    "start_tree_given_by_the_parent": {
      "passed": 720,
      "failed": 0,
      "ignored": 3,
      "listed": 723,
      "corroboration": "ROUND-3-REPORT.md records the same 720/0/3/723 for the committed tree"
    },
    "tests_removed": 0,
    "tests_added_this_batch": 2,
    "ignored_tests": [
      "tests/bevy_adapter_b1.rs: needs a real Bevy 0.19.1 app listening on 127.0.0.1:15702",
      "tests/bevy_adapter_b2.rs: needs a real hof_game on 127.0.0.1:15702 with the frozen contract registered",
      "tests/bevy_round1.rs: needs a real Bevy build and a headless launch",
      "tests/brp_real_handover.rs (x3): needs a real game image via HOF_BEVY_GAME_IMAGE and two headless launches"
    ]
  },
  "controlled_plants": [
    {
      "id": "P1_budget_frozen_at_the_unwritten_value",
      "task_under_test": "the step budget is re-read where it is enforced (round 3's flat 43)",
      "file": "src/harness/guard.rs",
      "test": "harness::guard::tests::the_step_budget_is_re_read_where_it_is_enforced",
      "red_exit_code": 101,
      "red_test_ran": true,
      "red_test_failed": true,
      "green_exit_code": 0,
      "green_ok": true,
      "sha256_before": "8297ceca573713af06780ec83f966ed6c3df73dead175e16b001451ddff7830a",
      "sha256_planted": "b58e8a54cd643890f8fc107b9ace922a65b3c51dd61e2c84317ee3d6e46f9971",
      "restore_sha256_matches": true,
      "mtime_ns_recorded": 1791161336041302900,
      "mtime_restored_ns": 1791161336041302900,
      "mtime_restored": true,
      "verdict": "green-red-green"
    },
    {
      "id": "P2_write_no_longer_restarts_the_tripwire",
      "task_under_test": "the repeated-action counter restarts at a counted artifact write",
      "file": "src/harness/guard.rs",
      "test": "harness::guard::tests::a_write_of_the_artifact_restarts_the_repeated_action_counter",
      "red_exit_code": 101,
      "red_test_ran": true,
      "red_test_failed": true,
      "green_exit_code": 0,
      "green_ok": true,
      "sha256_before": "8297ceca573713af06780ec83f966ed6c3df73dead175e16b001451ddff7830a",
      "sha256_planted": "e6b696c16c1d134c7d8b3b2fbc8ac11b069f373183d958b3a1ab1a29e9baf7bf",
      "restore_sha256_matches": true,
      "mtime_ns_recorded": 1791161336041302900,
      "mtime_restored_ns": 1791161336041302900,
      "mtime_restored": true,
      "verdict": "green-red-green"
    },
    {
      "id": "P3_filter_folding_loses_tail_and_head",
      "task_under_test": "the action key folds `| tail -N` / `| head -N` (round 3's accounting)",
      "file": "src/harness/guard.rs",
      "test": "harness::guard::tests::the_same_action_spelled_with_a_filter_or_a_redirection_is_one_action",
      "red_exit_code": 101,
      "red_test_ran": true,
      "red_test_failed": true,
      "green_exit_code": 0,
      "green_ok": true,
      "sha256_before": "8297ceca573713af06780ec83f966ed6c3df73dead175e16b001451ddff7830a",
      "sha256_planted": "a79f452136f670b56d35bdb54fc438c2586d6710519c79ff43b606ce4eb7399c",
      "restore_sha256_matches": true,
      "mtime_ns_recorded": 1791161336041302900,
      "mtime_restored_ns": 1791161336041302900,
      "mtime_restored": true,
      "verdict": "green-red-green"
    },
    {
      "id": "P4_round_stop_sweep_disabled",
      "task_under_test": "every pid the round's ledger records is reaped and verified dead",
      "file": "src/adapter/bevy/mod.rs",
      "test": "adapter::bevy::tests::the_round_stop_sweep_reaps_every_recorded_process_and_writes_its_evidence",
      "red_exit_code": 101,
      "red_test_ran": true,
      "red_test_failed": true,
      "green_exit_code": 0,
      "green_ok": true,
      "sha256_before": "b1d6e2e98c8a0fea019033c87a95c526e31cfb35f82ead7ffe61450c39bd5a16",
      "sha256_planted": "b7907f818bc0443f9c629e7f9f7d9c89cfbe4c8f9a3a00a5b5a1120cd0435662",
      "restore_sha256_matches": true,
      "mtime_ns_recorded": 1791134812762189100,
      "mtime_restored_ns": 1791134812762189100,
      "mtime_restored": true,
      "verdict": "green-red-green"
    },
    {
      "id": "P5_round_game_slot_handoff_dropped",
      "task_under_test": "the round-game window receives the process `start` really produced",
      "file": "src/adapter/bevy/mod.rs",
      "test": "adapter::bevy::tests::the_round_game_window_receives_the_process_start_produced",
      "red_exit_code": 101,
      "red_test_ran": true,
      "red_test_failed": true,
      "green_exit_code": 0,
      "green_ok": true,
      "sha256_before": "b1d6e2e98c8a0fea019033c87a95c526e31cfb35f82ead7ffe61450c39bd5a16",
      "sha256_planted": "a5ed8925e74a8eaf4520c94eb727bf8c9ca92e01a2b0fad9da794195636af11e",
      "restore_sha256_matches": true,
      "mtime_ns_recorded": 1791134812762189100,
      "mtime_restored_ns": 1791134812762189100,
      "mtime_restored": true,
      "verdict": "green-red-green"
    }
  ],
  "plants_driver": "F:/hof-r4-work/py/plants.py (records sha256 and mtime before and after, restores in a finally, re-verifies the bytes, writes F:/hof-r4-work/plants.json)",
  "inherited_plants_cross_check": {
    "source": "F:/hof-r4-scripts/plants-result.json and F:/hof-r4-scripts/plants.json (the dead agent's own record)",
    "reading": "Its P5 is the one that matters to this batch's triage: it removed `self.rebind_observing_client();` from `BevyAdapter::start` and ran tests/brp_real_handover.rs::the_adapter_rebinds_its_observing_client_at_every_launch with a real staged image and `--ignored`, and the test went red (exit 101, test ran). That is what makes the transport fix's call site a pinned rule rather than an intention.",
    "not_re_run_here": "it starts games on 127.0.0.1:15702, which round 4 must own while it runs"
  },
  "changed_files": {
    "modified": [
      "config/hoh.yaml",
      "src/adapter/bevy/launch.rs",
      "src/adapter/bevy/mod.rs",
      "src/adapter/bevy/project.rs",
      "src/adapter/bevy/round.rs",
      "src/adapter/mod.rs",
      "src/config.rs",
      "src/harness/guard.rs",
      "src/harness/mini.rs",
      "src/runtime/invoke.rs",
      "src/runtime/run_loop.rs",
      "src/runtime/write_failure.rs",
      "src/tools/endpoint.rs",
      "tests/cold_start_grace.rs",
      "tests/common/mod.rs",
      "tests/endpoint_liveness.rs",
      "tests/endpoint_request_count.rs",
      "tests/engine_identity.rs",
      "tests/game_route_across_processes.rs",
      "tests/repeated_action.rs"
    ],
    "added": [
      "tests/brp_connection_pool.rs",
      "tests/brp_real_handover.rs"
    ],
    "added_by_this_batch": [
      ".spec/bevy/ROUND-4-REPORT.md"
    ],
    "diff_of_this_tree": "20 files changed, 1836 insertions(+), 232 deletions(-) (git diff --stat, HEAD 1c1aaef)",
    "not_modified_by_design": [
      ".spec/bevy/REQUIREMENTS.md",
      ".spec/bevy/DESIGN-OVERVIEW.md",
      ".spec/bevy/DESIGN-DETAIL.md",
      ".spec/bevy/PRD.md",
      ".spec/bevy/SPIKE-1-REPORT.md",
      ".spec/bevy/SPIKE-2-REPORT.md",
      ".spec/bevy/BATCH-B1-REPORT.md",
      ".spec/bevy/BATCH-B2-RECONSTRUCTION.md",
      ".spec/bevy/BATCH-B3-REPORT.md",
      ".spec/bevy/ROUND-1-REPORT.md",
      ".spec/bevy/ROUND-2-REPORT.md",
      ".spec/bevy/ROUND-3-REPORT.md",
      ".spec/bevy/TRUST-REPORT.md",
      "DECISIONS.md"
    ],
    "committed": false,
    "pushed": false,
    "note": "src/adapter/bevy/round.rs is modified by this batch, not by the dead agent; the other 19 were the dead agent's"
  },
  "evidence_paths": {
    "this_batch_outside_the_repository": [
      "F:/hof-r4-work/inherited.diff (the dead agent's full diff as received)",
      "F:/hof-r4-work/py/*.py (the readers, the plant driver, the fact collector, this writer)",
      "F:/hof-r4-work/plants.json, F:/hof-r4-work/facts.json",
      "F:/hof-r4-logs/final-gate.out, final-gate.exit, final-list.out, final-list.exit, final-fmt.out, final-fmt.exit",
      "F:/hof-r4-logs/gate-baseline.out, gate-baseline.exit (the inherited tree as received)",
      "F:/hof-r4-logs/r4m.* (round-4 driver logs: init/run out, err, exit)",
      "F:/hof-r4-logs/r4m.pre.txt (endpoint free before the round)"
    ],
    "round_4_evidence_in_the_repository": [
      "runs/round4/**",
      "runs/bevy-round4/**",
      "runs/round4-attempt2/**, runs/bevy-round4-attempt2/** (the dead agent's second attempt, moved here, never deleted)",
      "runs/round4-attempt1/**, runs/bevy-round4-attempt1/** (its first attempt: exit 2, StepBudgetExceeded)"
    ],
    "round_3_reference_used_for_the_comparison": [
      "runs/round3/iter-{1,2,3}/result.json",
      "runs/round3/iter-{1,2,3}/traj/developer.attempt1.json",
      "runs/bevy-round3/launch.json, launch-ledger.jsonl",
      ".spec/bevy/ROUND-3-REPORT.md"
    ]
  },
  "credential_hygiene": {
    "key_file": "F:/hof-secrets/round4.env (outside the repository, one `HOH_MODEL_API_KEY` line, 51 characters, fingerprint 5cf81e8f)",
    "loaded_by": "--env-from-secret; the value never appears on a command line and is never printed",
    "key_on_any_command_line": false,
    "key_in_this_report": false,
    "key_written_inside_the_repository_by_this_batch": false,
    "note": "the fingerprint matches the key TRUST-REPORT.md already records as leaked into two gitignored round-1 evidence files; that key still needs rotation by its owner, which this batch neither did nor hid"
  },
  "could_not_verify": [
    "The round's identity fields, nine battery steps, proving call ids, economics, increment fingerprints and PRD coverage: the round was still in its first iteration. Nothing here infers them; the gate must be applied to runs/bevy-round4/launch.json before any of them is read.",
    "That the progress-following budget lifts inside a live call: pinned by the guard test and by plant P1, and falsified only across two real runs of which one (attempt 1) was built with the wrong unit. The live confirmation needs an iteration to finish.",
    "That the transport gap is closed in a live pass: the client-level reproduction and the call-site plant are both real, but round 3's failure was only ever observed in a real pass.",
    "Whether the tripwire ever fires in a real round: it fired in zero of round 3's calls and fires late on the only recorded grind; one clean round is one observation.",
    "The portability of tests/brp_connection_pool.rs's second test (no cfg(windows) guard).",
    "The end-to-end wiring of `start_round_game` -> `take_started_process` -> window slot: pinned in its two halves with real processes, but only the round exercises the whole line."
  ]
}
```

# Bevy round 4 — report

The JSON above is serialiser output written by `F:/hof-r4-work/py/write_report.py`; it was parsed back
out of this file, and compared with the block that was written, before this prose was appended.

---

## 1. The inherited work: what I kept, finished and fixed

A dead agent did this job before me and left nineteen tracked files modified and two new test files,
with no report. I read the whole diff (`F:/hof-r4-work/inherited.diff`), judged each file, and then
ran its tree through the gate before touching anything: **733 passed / 0 failed / 6 ignored / 739
listed, 0 warning lines, exit 0**. So the starting point was not broken — it was *unverified*, and in
two places it was wrong.

**Kept because they are right and load-bearing.** The guard's per-step enforcement of the
progress-responsive budget (with `StepCounter` counting model calls, not actions); `CountingModel`
feeding `AgentConfig.step_limit` the flat ceiling instead of the gated value; the round-game slot fix
plus the launch-ledger sweep for the role-session stop; the run-level preference for
`verified_game_endpoint()`; the optional identity fields on `GameEndpointRecord`; the folding of
`| tail`/`| head`/redirects into the action key; the counting of `StepBudgetExceeded` as a limit and a
failure; the `pub(crate)` test helper in `launch.rs`; and the six mechanical `None` additions at the
other `GameEndpointRecord` construction sites. Five plants (below) confirm that four of these
mechanisms are what their tests are red on.

**Finished — sound, but with numbers that were not measured.** `tests/repeated_action.rs` measured
"the current window" as the counts of the *last* window, so round 2's iteration 1 printed a window
maximum of **1** while its own `abort_at` said a window had reached the cap of 15. Since the cap is
derived from exactly that figure, the defect mattered: the file claimed 22 in its prose and could not
show it. It now reports the maximum over all post-write windows and pins the numbers — 22 (window)
and 54 (whole call) for the grind, 7 for the legitimate call, 5/2/4 for round 3's three Developer
calls. The assertion for the projection was `fraction < 0.95`, which would pass even if the tripwire
saved nothing; it is now the measured 75–80%. The same correction was carried into
`config/hoh.yaml` and `src/config.rs`, whose prose said "after its last write" where the measurement
is "in a post-write window", and whose round-3 evidence said "nine builds in three spellings" where
the census says **15 `cargo build` calls in 12 distinct spellings, 14 carrying a `| tail` filter**
(`F:/hof-r4-work/py/census.py`). The guard's abort message and the two assertions on its text still
said "succeeded N times in this call", which stopped being the rule when the counter was made to
restart at a write; all three now say "since this call last wrote the artifact it declares".

**Fixed — wrong as it stood.** `src/adapter/bevy/round.rs` wrote two of the four identity-gate fields
as literals: `identity.verified` was the constant `true` and `identity.answering_pid` a **copy** of
`identity.spawned_pid`. Round 3's report flagged this and the dead agent did not fix it, so the gate
the parent told me to apply before reading any battery verdict was half tautology. They are now
computed: `answering_pid` is the OS TCP table's own listener reading (an independent witness that can
be absent and can disagree), `verified` is true only when the launch carries the non-empty per-launch
nonce that readiness read back, and the rule is written into the record as `verified_rule`. A new unit
test pins the four cases. I also added `client_generation` to `launch.json`, so a real pass records
whether the observing client was rebuilt at the process boundary.

**The new connection-pool test nobody had run.** `tests/brp_connection_pool.rs` is sound and I kept
it: it binds a real loopback listener, answers each request with `Connection: keep-alive` and then
kills the socket with `SO_LINGER 0` (a reset, not a FIN), and proves that the *next* call through the
same pooled client fails at the transport layer while a client rebuilt for the "new process" succeeds.
It ran green in both of my gate runs. One defect is reported and deliberately **not** fixed: the
module doc promises "Off Windows the helper is a no-op and the test says it measured nothing", but
only the first of its two tests says so — the second has no `cfg!(windows)` guard and would assert a
Windows behaviour elsewhere. I first fixed it, then reverted the fix, because a change made after the
gate measurement would have made the reported counts describe a tree that no longer exists. It is a
one-line guard for the next batch, and it is in `could_not_verify`.

**Reverted: nothing.** No inherited change was wrong enough to remove.

## 2. The step budget now follows progress — and the numbers agree

A step is one **model call**, counted by `CountingModel` at the point the call is made, which is the
unit `agent.step_limit` is written in and the unit mini's own `n_calls` uses. mini's
`AgentConfig.step_limit` is the **flat ceiling** (150). The progress gate is enforced by the guard, in
`Environment::execute`, against a value it re-reads every time.

The three numbers the report has to keep apart are now consistent and each is labelled:

* the prompt **body** renders `{{step_limit}}` = 150, and the note calls it the ceiling;
* the **note** states the ceiling (150), the budget actually enforced *at this moment* (43 while
  nothing counted has been written), and the rule — "the first successful project write raises it to
  150. That limit is re-read at every step";
* the **enforced** value is 43 model calls while unwritten, 150 after a counted write, with mini's
  flat interrupt at 150 as the backstop.

This is the exact inverse of round 3's one-line defect, where `mini.rs:115` read
`effective_step_budget()` once before the call and froze 43 into the agent. Plant P1 plants that
defect back in another dress (the budget computed as the unwritten value regardless of
`artifact_written()`), and
`harness::guard::tests::the_step_budget_is_re_read_where_it_is_enforced` goes red (exit 101, test ran)
and green again after a byte-exact restore. The guard test drives all three cases: the call after the
live budget is refused; the count is model calls, not actions (a response carrying two actions must
not consume two steps — that mismatch is what cut round 4's first attempt after 30 model calls
against a stated 43); and a write **inside** the call raises the budget so the steps after it are
allowed. The dead agent's attempt 1 is a real-run falsification of the wrong unit: it ended
`exit 2` with `StepBudgetExceeded` after 30 model calls, and the fix moved the count to the model
layer.

**Not declared fixed on evidence I do not have:** the live lift inside a real call. The round had not
completed an iteration when this was written.

## 3. The repeated-action tripwire: reachable, late, and useless in normal operation

The accounting was wrong, not the mechanism and not the threshold.

* **Accounting.** Round 3's iteration 1 emitted **15** `cargo build` calls in **12 distinct
  spellings** — `… 2>&1 | tail -20`, `… 2>&1 | tail -5 &`, `… | findstr … | head -20 &` and so on —
  and the pre-round-4 key folded only `| more` and `| findstr`, so its most-repeated action counted
  **3**. That is why the tripwire "never fired" in round 3: on the accounting it was invisible. Plant
  P3 removes `tail`/`head` from the fold and the key test goes red.
* **Threshold.** 15 is measured and is more than twice the highest legitimate post-write window count
  in any recorded Developer call: **7** for round 2's clean iteration 2, **5/2/4** for round 3's three
  calls, against **22** for round 2's iteration 1 grind.
* **Mechanism.** The counter restarts at every counted write — a deliberate choice. It is also what
  keeps the tripwire silent on round 3: whole-call counting with the folded key reaches *exactly 15*
  on round 3's iteration 1, i.e. it would have aborted a call that was interleaving writes with
  rebuilds. Plant P2 removes the restart, and the restart test goes red.

Measured behaviour under the round-4 rule: it **does** fire on the recorded grind, at API call **126
of 150**, keeping **77.3%** of that call's prompt tokens — a saving of 22.7%, late. It fires on **no
recorded normal call**, round 3's included. So the honest verdict is *reachable and weak*: not inert,
but contributing nothing to the rounds we have actually run. I did not declare it inert because the
recorded grind proves it can fire; I also did not call it a fix for round 2's cost, because the
numbers say it removes the tail and not the middle.

## 4. The role-session stop is closed in code, with tests that hold real pids

Round 3 ended with `hof_game.exe` **pid 54568** (the iteration-3 Tester's session game, the last line
of the launch ledger) still `LISTENING` on 15702 after `hoh run` exited 0. The cause is now named: a
field mix-up in `src/adapter/bevy/project.rs`. `start` puts the process in `BevyAdapter::process`,
while `start_round_game` filled the window's `round_game` slot from a reader of **that same empty
slot**, so the window owned nothing and `stop_round_game` stopped nothing.

Two independent layers now close it:

1. `start_round_game` moves `start`'s own process into the window
   (`take_started_process` → `set_round_game_process`), so the owned stop is real.
2. `stop_round_game` sweeps **every pid the round's launch ledger records** — the ledger is appended
   before every spawn, for battery and role-session launches alike — kills survivors, verifies each
   death, writes `runs/bevy-round4/round-stop.json` (recorded / reaped / still_alive /
   endpoint_holder), and returns an error naming any pid that survived. `run()` calls it on every
   exit path of the round, so the sweep runs even when `run_inner` returns early.

Pinned by tests that hold **real child processes**: the window-handoff test (plant P5 reddens it), the
sweep test with two recorded children (plant P4 reddens it), its control that a pid the ledger never
named is left alone, and the ignored real-engine handover test which asserts both launches are on the
ledger and both are verified dead. The wiring line in `start_round_game` itself has no gate test; its
evidence is the round.

**Residual risk stated plainly:** the sweep kills a recorded pid on liveness alone, without checking
the image. Within one round the pids are minutes old, so a recycled pid is unlikely — but it is the
thing that would make this dangerous rather than merely wrong, and it is not pinned.

## 5. Run-level attribution now names a proved identity

Round 3's `runs/round3/meta.json` named pid **34124** — an iteration-2 session, neither the final
battery's process nor alive at the end — because the field was copied from the channel's "last
endpoint ever registered" history, which is a pid and nothing else.

Now both write-backs prefer `adapter.verified_game_endpoint()`, which returns the last launch's facts
from a slot shared with the peers (the battery observes through a peer, so the runtime's own adapter
never saw the launch). The record carries `source: launch_verified`, the per-launch nonce, and the OS
TCP table's own `answering_pid`. The dead agent's attempt-1 meta already shows the new shape —
`{"nonce": "0fe243a7-d19a-4097-b855-cbdf2faf5960", "pid": 46784, "answering_pid": 46784,
"source": "launch_verified", "verified": true}` — where round 3's had none of those fields. The
history is kept only as a fallback for an adapter that proves nothing, and a role-announced endpoint
records `verified: None` rather than borrowing a proof it does not have.

## 6. The transport gap: real fragility, and the inherited test is the right attempt at it

`G-transport` — round 3's only PRD gap, the first sequenced call of passes 2 and 3 failing with `BRP
transport failure … at frame zero` — is **not** a probe-ordering artefact.

`BrpClient` is `Clone` over a single `ureq::Agent`, whose connection pool every clone shares.
`round_peer()` clones the runtime adapter's client, so each battery pass starts with the pool of
whatever talked last. Round 3's pass 1 had never talked to anything and its first call was clean;
passes 2 and 3 inherited a pooled keep-alive socket to the previous, now-dead game, their **first**
call failed at the transport layer before reaching anything, and the immediate retry (on a fresh
connection) succeeded. That is precisely the recorded shape: one failure, at frame 0, in each pass
after the first.

The fix: `BevyAdapter::start` rebuilds the observing client — and the MCP server built over it — at
every launch, so the client is bound to the process being observed. `launch.json` now records
`client_generation` so a real pass can be read for it. The inherited `tests/brp_connection_pool.rs`
is an attempt at exactly this and a sound one; the call site is pinned by the ignored real-engine test
`the_adapter_rebinds_its_observing_client_at_every_launch`, which the dead agent's plant P5 proved
load-bearing (removing the call from `start` turned it red with a real image). I did not re-run that
plant: it starts games on 15702, and round 4 owns the endpoint while it runs.

## 7. The round: init exited 0; the run was still going when this report was due

`hoh init --adapter bevy` from a genuinely empty project outside the repository
(`F:/hof-bevy-r4-run/workspace`, created by a script that refuses a directory that already exists)
exited **0**. `hoh run --adapter bevy --run-id round4 --env-from-secret F:/hof-secrets/round4.env`
started at 08:59:02 with the CLI built from this tree (`hoh.exe` sha256 `e8862581…`, younger than the
code it runs, unlike round 3's first attempt), the preflight passed every check including the frozen
contract hash `c579a742…` and the lockfile `660e7e17…`, and the endpoint was verified free before the
launch (`netstat` silent, no `hof_game.exe`).

**At the time this report had to be written the run was 13 minutes into its first iteration** —
Planner stage, no `runs/bevy-round4/` yet. The parent asked for the report at that point, so:

* **`run` exit code: not available.** The driver writes the literal `$?` to
  `F:/hof-r4-logs/r4m.run.exit`; the file did not exist at write time.
* **Identity fields: not available.** `runs/bevy-round4/launch.json` did not exist, so the gate
  (`identity.verified` true, nonce equal to the generated nonce, `answering_pid` equal to
  `spawned_pid`, `stop.pid_dead` true) **could not be applied**, and in consequence **no battery
  verdict of round 4 appears anywhere in this report**. There are no nine steps, no proving call ids,
  no round-4 economics, no increment fingerprints and no round-4 PRD coverage quoted here — not even
  inferred. The round-3 values are quoted only as the comparison baseline.
* The round was **not** abandoned: its driver is still running and will write `runs/round4/**` and
  `runs/bevy-round4/**`. §7 of the JSON names exactly which files to read and in which order, and the
  gate must be applied before any verdict is read.

I ran round 4 twice before this one, and both earlier attempts belong to the dead agent: attempt 1
exited **2** with `NoEngineeringWrite` after three iterations, and its warnings log is what proves the
action-unit bug in a real run; attempt 2 died mid-iteration-1 with the agent. Their bytes are
preserved at `runs/round4-attempt1/`, `runs/round4-attempt2/`, `runs/bevy-round4-attempt1/` and
`runs/bevy-round4-attempt2/` — moved, never deleted.

## 8. The gate and the plants

Final tree: `cargo test --offline` **exit 0**, **734 passed / 0 failed / 6 ignored**, **740 listed**
(734+6), 56 test targets, **0 warning lines**; `cargo test --offline -- --list` exit 0, 740 listed;
`cargo fmt --all --check` exit 0. All three numbers are from the literal exit codes captured in
`F:/hof-r4-logs/final-*.exit`, with no second test process running, in this batch's own build
directory `F:/hof-r4-target`. The tree as received measured **733 passed / 0 failed / 6 ignored / 739
listed / 0 warnings / exit 0**; the committed tree the parent named is 720/0/3/723, which round 3's
report also records. No test was removed. Six ignored tests are listed in the JSON block (three
pre-existing, three new in `brp_real_handover.rs`).

Five controlled plants, each **green–red–green** with the sha256 recorded before and after and the
timestamp restored explicitly (`F:/hof-r4-work/plants.json`, driver `F:/hof-r4-work/py/plants.py`,
which restores in a `finally` and re-verifies the bytes):

| plant | mechanism it disables | test | red | green | restore |
|---|---|---|---|---|---|
| P1 | the live budget re-read at the step (round 3's frozen 43) | `the_step_budget_is_re_read_where_it_is_enforced` | 101, test ran | 0 | sha256 + mtime exact |
| P2 | the counter restarting at a counted write | `a_write_of_the_artifact_restarts_the_repeated_action_counter` | 101, test ran | 0 | sha256 + mtime exact |
| P3 | folding `\| tail -N` / `\| head -N` | `the_same_action_spelled_with_a_filter_or_a_redirection_is_one_action` | 101, test ran | 0 | sha256 + mtime exact |
| P4 | the ledger-wide round-stop sweep | `the_round_stop_sweep_reaps_every_recorded_process_and_writes_its_evidence` | 101, test ran | 0 | sha256 + mtime exact |
| P5 | handing `start`'s process to the round-game window | `the_round_game_window_receives_the_process_start_produced` | 101, test ran | 0 | sha256 + mtime exact |

## 9. What still does not work, and what I could not verify

* **The round is unresolved.** Everything downstream of identity — the nine steps, economics,
  fingerprints, coverage — is unknown at write time. This is the largest single gap in this report.
* **The budget's live lift is proven by a test and a plant, not by a finished real call.**
* **The transport fix is proven at the client level and at its call site, not by a live pass.**
* **The tripwire is reachable but weak**: it fires late (call 126/150, 77% kept) and on no recorded
  normal call; one clean round is one observation, not a proof that 15 is the right number.
* **The ledger sweep does not check the process image** before killing a recorded pid.
* **`tests/brp_connection_pool.rs`'s second test has no `cfg!(windows)` guard** (reported, not fixed,
  for the reason in §1).
* **`start_round_game`'s wiring line** is exercised only by a real round.
* **I did not re-run the real-engine handover test**, because it starts games on 15702 and round 4
  owns the endpoint; its load-bearing property rests on the dead agent's plant record, which I read
  and cross-checked but did not reproduce.

## 10. The single most important thing for the next batch

**Read `runs/bevy-round4/launch.json` before anything else, apply the four-field gate, and only then
read the round.** That is not boilerplate this time: the round was still running when this report was
due, so the identity fields and every battery verdict are unread, and the value of this batch is
exactly the two things that *are* measured — the budget now follows progress in the unit the prompt
states (model calls, re-read at the step, raised by a write inside the call), and the role-session
stop is closed two independent ways with real-pid tests behind each. If the identity fields hold, the
first number to look at is the Developer's call count per iteration: round 3's was a flat **43** three
times over because the gate was frozen before the call, and a budget that actually follows progress
should show a *different* number per iteration — one that reaches 150 when the call is writing. If it
does not, the gate is still mislabelled and the mechanism, not the measurement, is what failed.
