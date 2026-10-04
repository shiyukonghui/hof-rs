# Bevy round 1 — report

```json
{
  "schema": "hof-rs / bevy round 1 report",
  "produced_at": "2026-10-04T11:31:25",
  "harness": {
    "repo": "F:\\moonbit-hof-rs",
    "adapter": "bevy",
    "engine_kind": "bevy-0.19.1",
    "frozen_hashes": {
      "contract_sha256": "792001e7e629ccc25d6c486eeb54360d83ffb208befa4ca5e430c6f0e747f4f9",
      "feature_sha256": "d6a90ba39e67b9e05fd28d97cc570dc989a03e8ec7a15ba93d077d5fe95d1f96",
      "game_lock_sha256": "660e7e17b62921ac409d0e2b023273ce1426959cbd386f21832e03745068c8df"
    }
  },
  "tasks_1_2_adapter_and_scaffold": {
    "init_command": "hoh init --project <fresh project outside the repo> --adapter bevy",
    "init_completed": true,
    "init_exit_code": 0,
    "scaffold_files": [
      ".gitignore",
      "Cargo.lock",
      "Cargo.toml",
      "src/contract.rs",
      "src/game.rs",
      "src/main.rs"
    ],
    "scaffold_satisfies": "bevy_remote feature, RemotePlugin+RemoteHttpPlugin, ScheduleRunnerPlugin, the seven reflectable surfaces, and the HOF_GAME_HEADLESS switch; `cargo build --offline` is green"
  },
  "task_3_real_round": {
    "run_command": "hoh run --project <fresh project outside the repo> --adapter bevy --run-id round1b --iterations 1",
    "run_completed": true,
    "run_exit_code": 0,
    "process_exit_code": 0,
    "result": {
      "ok": true,
      "failed_role": null,
      "reason": "ok",
      "issues": []
    },
    "roles": [
      {
        "role": "planner",
        "calls": 19,
        "duration_ms": 72330,
        "exit_status": "Submitted",
        "artifact_valid": true,
        "total_tokens": 175162
      },
      {
        "role": "developer",
        "calls": 140,
        "duration_ms": 3263828,
        "exit_status": "RepeatedFormatError",
        "artifact_valid": true,
        "total_tokens": 10379180
      },
      {
        "role": "tester",
        "calls": 150,
        "duration_ms": 534331,
        "exit_status": "LimitsExceeded",
        "artifact_valid": true,
        "total_tokens": 9658837
      }
    ],
    "developer_increment": {
      "real_increment": true,
      "A0_version_id": "b207fb2345ed210733cb702b5fadaeb7c83d1371fc1ae47d3804769e5d7c89e7",
      "A1_version_id": "f808df1b7659665c5d7a61e4ae58a745612398d56e4b16bff3240723a4de46f8",
      "A1_differs_from_A0": true,
      "A1_parent_is_A0": true,
      "fingerprints": [
        {
          "path": "src/game.rs",
          "before_sha256_16": "dfe4852c81063b3b",
          "before_size_bytes": 4502,
          "after_sha256_16": "714041cc6c8f1150",
          "after_size_bytes": 8704,
          "lines_added": 137,
          "lines_removed": 59
        }
      ],
      "files_untouched": [
        "src/contract.rs",
        "src/main.rs"
      ],
      "nature": "the scaffold's `coins == 0` guard and bare GOAL_X constant became a coin entity and an exit entity that own their own position and their one-way latch; the frozen contract is byte-identical"
    }
  },
  "task_4_five_observations": {
    "gate": {
      "applicable": true,
      "launchable": true,
      "reasons": []
    },
    "proven_by": "the adapter's deterministic battery, inside the game process, through the eight semantic tools over Bevy Remote Protocol",
    "criteria": [
      {
        "id": "P1",
        "criterion": "an injected move_dir=1 changes the player's x",
        "verdict": "observed",
        "observed": true,
        "failure": null,
        "raw_call_ids": [
          8,
          9,
          10,
          11,
          12
        ],
        "raw_call_files": [
          "runs/bevy-round1b/calls/0008-bevy_inject_move.json",
          "runs/bevy-round1b/calls/0009-bevy_wait_frames.json",
          "runs/bevy-round1b/calls/0010-bevy_player_transform.json"
        ],
        "tester_facing_raw": ".hoh/deterministic/raw/e3_movement.json"
      },
      {
        "id": "P2",
        "criterion": "the coin counter goes 0 -> positive and never reverts",
        "verdict": "observed",
        "observed": true,
        "failure": null,
        "raw_call_ids": [
          1,
          2,
          3,
          4,
          5,
          6,
          7,
          13,
          14,
          15,
          16,
          17,
          18,
          19,
          20,
          21,
          22,
          23,
          24,
          25,
          26,
          27,
          28,
          29
        ],
        "raw_call_files": [
          "runs/bevy-round1b/calls/0001-bevy_grounded.json",
          "runs/bevy-round1b/calls/0002-bevy_wait_frames.json",
          "runs/bevy-round1b/calls/0003-bevy_grounded.json"
        ],
        "tester_facing_raw": ".hoh/deterministic/raw/e3_coin_counter.json"
      },
      {
        "id": "P3",
        "criterion": "the win flag goes false -> true and never reverts",
        "verdict": "observed",
        "observed": true,
        "failure": null,
        "raw_call_ids": [
          1,
          2,
          3,
          4,
          5,
          6,
          7,
          13,
          14,
          15,
          16,
          17,
          18,
          19,
          20,
          21,
          22,
          23,
          24,
          25,
          26,
          27,
          28,
          29
        ],
        "raw_call_files": [
          "runs/bevy-round1b/calls/0001-bevy_grounded.json",
          "runs/bevy-round1b/calls/0002-bevy_wait_frames.json",
          "runs/bevy-round1b/calls/0003-bevy_grounded.json"
        ],
        "tester_facing_raw": ".hoh/deterministic/raw/e3_win_flag.json"
      },
      {
        "id": "P4",
        "criterion": "the jump rises and then falls",
        "verdict": "observed",
        "observed": true,
        "failure": null,
        "raw_call_ids": [
          30,
          31,
          32,
          33,
          34,
          35,
          36,
          37,
          38,
          39,
          40,
          41,
          42,
          43,
          44,
          45,
          46
        ],
        "raw_call_files": [
          "runs/bevy-round1b/calls/0030-bevy_grounded.json",
          "runs/bevy-round1b/calls/0031-bevy_player_transform.json",
          "runs/bevy-round1b/calls/0032-bevy_inject_jump.json"
        ],
        "tester_facing_raw": ".hoh/deterministic/raw/e3_jump_arc.json",
        "arc": {
          "falling": 8,
          "first": -200.0,
          "peak": -165.01499938964844,
          "rising": 4,
          "samples": [
            {
              "frame": 198496,
              "value": -200.0
            },
            {
              "frame": 198506,
              "value": -171.64768981933594
            },
            {
              "frame": 198508,
              "value": -168.05615234375
            },
            {
              "frame": 198510,
              "value": -165.83636474609375
            },
            {
              "frame": 198512,
              "value": -165.01499938964844
            },
            {
              "frame": 198514,
              "value": -165.5794677734375
            },
            {
              "frame": 198516,
              "value": -167.52894592285156
            },
            {
              "frame": 198518,
              "value": -170.84959411621094
            },
            {
              "frame": 198520,
              "value": -175.54161071777344
            },
            {
              "frame": 198522,
              "value": -181.58737182617188
            },
            {
              "frame": 198524,
              "value": -189.0558929443359
            },
            {
              "frame": 198526,
              "value": -197.92613220214844
            },
            {
              "frame": 198528,
              "value": -200.0
            }
          ]
        }
      },
      {
        "id": "P5",
        "criterion": "grounded is true before take-off",
        "verdict": "observed",
        "observed": true,
        "failure": null,
        "raw_call_ids": [
          1,
          2,
          3,
          4,
          5,
          6,
          7
        ],
        "raw_call_files": [
          "runs/bevy-round1b/calls/0001-bevy_grounded.json",
          "runs/bevy-round1b/calls/0002-bevy_wait_frames.json",
          "runs/bevy-round1b/calls/0003-bevy_grounded.json"
        ],
        "tester_facing_raw": ".hoh/deterministic/raw/e3_grounded.json"
      }
    ],
    "all_five_observed": true,
    "battery_calls": {
      "count": 46,
      "dir": "runs/bevy-round1b/calls/",
      "failed_calls": 0
    },
    "tester_independent_calls": {
      "count": 259,
      "tools": {
        "bevy_player_transform": 103,
        "bevy_inject_move": 63,
        "bevy_wait_frames": 57,
        "bevy_grounded": 12,
        "bevy_health": 12,
        "bevy_coin_counter": 6,
        "bevy_win_flag": 6
      },
      "source": "runs/round1b/iter-1/traj/tester.attempt1.json"
    },
    "negative_control": {
      "what": "the same battery against a build whose player spawns 1,000,000 px high, so the sampled arc is a monotone fall",
      "evidence_dir": "runs/bevy-round1-negative-control/",
      "observed": "jump verdict not observed; rising=0, falling=32; failure: the arc never rises (rise=0, fall=32): a monotone fall is not a jump",
      "reproduced_by": "cargo test --offline --test bevy_round1 -- --ignored"
    }
  },
  "task_5_evidence": {
    "round": [
      "runs/round1b/meta.json",
      "runs/round1b/exit_code",
      "runs/round1b/process_exit_code",
      "runs/round1b/game_endpoint.json",
      "runs/round1b/versions/index.json",
      "runs/round1b/TOOLS.md",
      "runs/round1b/iter-1/plan.md",
      "runs/round1b/iter-1/evidence.json",
      "runs/round1b/iter-1/qa_report.md",
      "runs/round1b/iter-1/result.json",
      "runs/round1b/iter-1/usage.json",
      "runs/round1b/iter-1/logs/{planner,developer,tester}.attempt1.log",
      "runs/round1b/iter-1/traj/{planner,developer,tester}.attempt1.json",
      "runs/round1b/iter-1/candidate/**"
    ],
    "battery": [
      "runs/bevy-round1b/meta.json",
      "runs/bevy-round1b/build.log",
      "runs/bevy-round1b/launch.json",
      "runs/bevy-round1b/gate.json",
      "runs/bevy-round1b/readings/e3-observations.json",
      "runs/bevy-round1b/calls/0001..0046-*.json",
      "runs/bevy-round1b/qa/e3-summary.txt",
      "runs/bevy-round1b/qa/pointer.json"
    ],
    "tester_facing": [
      ".hoh/deterministic/battery.json",
      ".hoh/deterministic/raw/e3_movement.json",
      ".hoh/deterministic/raw/e3_coin_counter.json",
      ".hoh/deterministic/raw/e3_win_flag.json",
      ".hoh/deterministic/raw/e3_jump_arc.json",
      ".hoh/deterministic/raw/e3_grounded.json",
      ".hoh/deterministic/raw/editor_errors_baseline.json",
      ".hoh/deterministic/raw/play_scene_ready.json",
      ".hoh/deterministic/mcp-errors.jsonl (0 bytes: no failed call)"
    ],
    "tester_verdict": {
      "qa_status": "partial",
      "verified": 8,
      "gaps": 4,
      "verified_claim_ids": [
        "BUILD",
        "BOOT",
        "P1",
        "P2",
        "P3",
        "P4",
        "P5",
        "FC"
      ],
      "gap_claim_ids": [
        "P1-left",
        "P1-release",
        "P3-position",
        "P5-gate"
      ],
      "gaps_are": "missing battery steps, not observed failures"
    }
  },
  "timings": {
    "round_wall_seconds": 3945.5,
    "planner_millis": 72330,
    "developer_millis": 3263828,
    "tester_millis": 534331,
    "battery_build_millis": 21090,
    "launch_ready_millis": 47,
    "battery_millis": 2606,
    "scaffold_cold_build_seconds": 322,
    "note": "the round built into an empty dedicated target directory; the scaffold's cold build dominates, and every rebuild after it is a one-crate rebuild"
  },
  "gate": {
    "command": "cargo test --offline",
    "exit_code": 0,
    "passed": 650,
    "failed": 0,
    "ignored": 3,
    "test_binaries_listed": 50,
    "warning_lines": 0,
    "fmt_command": "cargo fmt --all --check",
    "fmt_exit_code": 0,
    "build_dir": "F:/moonbit-hof-rs-build/target",
    "no_other_test_process": true,
    "baseline_passed": 625,
    "flakes_observed": "1 full-suite run in 3 had the pre-existing `brp::tests::a_slow_reply_that_exceeds_the_timeout_is_a_timeout` red; it passes in the measured run",
    "note": "measured after `touch src/lib.rs`, so the crate and every test target were recompiled: the zero-warning figure is a real rebuild, not a warm no-op"
  },
  "credential_hygiene": {
    "key_in_this_report": false,
    "key_in_round_evidence": true,
    "files": [
      "runs/round1b/iter-1/traj/tester.attempt1.json",
      "runs/round1/iter-1/traj/developer.attempt1.json"
    ],
    "mechanism": "the key was passed as an inline assignment on the terminal command line (`HOH_MODEL_API_KEY=... hoh run ...`).  The terminal wrapper exports the whole command as DSH_TERM_CMD into the environment of every descendant, so a role's `env | grep -i hoh` printed it.  The harness's own blanking held: HOH_MODEL_API_KEY is empty in every role shell.",
    "recommendation": "rotate the key; pass secrets through an env file or an already-exported variable, never as an inline assignment in a watched command line"
  },
  "changed_files": {
    "harness_repo_modified": [
      "config/hoh.yaml",
      "src/adapter/bevy/battery.rs",
      "src/adapter/bevy/brp.rs",
      "src/adapter/bevy/build.rs",
      "src/adapter/bevy/mod.rs",
      "src/adapter/engine.rs",
      "src/adapter/mcp/evidence.rs",
      "src/adapter/mod.rs",
      "src/cli.rs",
      "src/cli_impl.rs",
      "src/config.rs",
      "src/prompts/developer.md",
      "src/prompts/mod.rs",
      "src/prompts/planner.md",
      "src/prompts/tester.md",
      "src/runtime/engine_identity.rs",
      "src/runtime/policy.rs",
      "src/tools/bridge.rs",
      "src/tools/endpoint.rs",
      "src/tools/mod.rs",
      "tests/game_route_across_processes.rs",
      "tests/round_game_window.rs",
      "tests/tool_parameter_contract.rs"
    ],
    "harness_repo_added": [
      "src/adapter/bevy/project.rs",
      "src/adapter/bevy/round.rs",
      "src/adapter/bevy/scaffold.rs",
      "src/adapter/bevy/scaffold/",
      "src/prompts/skills/bevy-dev.md",
      "src/prompts/skills/bevy-testing.md",
      "src/tools/bevy_channel.rs",
      "tests/bevy_round1.rs"
    ],
    "round_artifact": [
      "src/game.rs"
    ],
    "frozen_documents_touched": []
  }
}
```

## What had to be built

Everything below is in the working tree (nothing is committed: the batch forbids it).

1. **The Bevy project adapter.** `BevyAdapter` now implements `ProjectAdapter`:
   `initialize` writes the scaffold, `cache_excludes` protects `target`, `build_check` is a real
   `cargo build --offline`, and `start_round_game`/`stop_round_game` own the round's headless game
   process and publish its route into `runs/<run-id>/game_endpoint.json`.
2. **`hoh init` produces a Bevy scaffold** that satisfies the frozen observability contract: the
   `bevy_remote` feature, `RemotePlugin` + `RemoteHttpPlugin`, `ScheduleRunnerPlugin::run_loop`,
   the seven reflectable surfaces in `src/contract.rs`, and the `HOF_GAME_HEADLESS` switch
   (`src/adapter/bevy/scaffold.rs` + `scaffold/game/**`, one copy, `include_str!`d).
3. **The deterministic battery for Bevy** (`src/adapter/bevy/round.rs`): a build gate, a launch
   gate, and five end-to-end criteria driven through the semantic tools. It writes the round-side
   evidence (`runs/bevy-<round>/`) **and** the workspace-side evidence the Tester reads
   (`.hoh/deterministic/**`), with the verbatim request/reply of every call.
4. **The two-layer tool surface**: `src/tools/bevy_channel.rs` exposes the eight semantic tools
   plus the generic `world.*` verbs, and enforces the role policy (`src/runtime/policy.rs`, a
   Bevy allowlist a Tester may use read-only).
5. **The Bevy prompt and skill layer** (`src/prompts/*.md`, `src/prompts/skills/bevy-*.md`). This
   is the part that made the round *work*: the previous prompts were written for the removed
   engine (`.tscn`, `editor_*`, a HUD `Label`, an exported `reached` flag), and the Planner's own
   plan came out Bevy-shaped only after the rewrite.
6. **Two wiring defects that only a real round could expose**:
   - a role's `hoh tools call` could not resolve `config/hoh.yaml` from a project *outside* the
     repository, so every role-side tool call failed before it reached the surface. Fixed by
     exporting the absolute path the run loaded (`HOH_CONFIG_FILE`, `src/cli.rs`, `src/config.rs`,
     `src/cli_impl.rs`).
   - a role's write to `.hoh/deterministic/**` is what the Tester cites, and the adapter was only
     writing `runs/bevy-<round>/`. The workspace copy now exists, and the Tester's eight verified
     claims cite it.

## What failed and why

**Attempt 1 (`runs/round1/**`) was aborted by me, deliberately.** The Developer could not make a
single tool call: `hoh: could not find config file for config/hoh.yaml` (exit 5), because the
project lived outside the repository and the config spec was relative. It spent ~65 model calls
exploring the filesystem instead, and had not written any project file. I stopped it, fixed the
wiring (item 6.1 above), re-verified the suite and started attempt 2. Its artifacts are kept as
evidence, and one of its trajectories is where the credential leak below was recorded.

**The developer call is the bottleneck.** 140 model calls, 54.4 minutes, 10.4M prompt tokens, and
it ended with `RepeatedFormatError` rather than a completion protocol. Its failure mode is
mechanical, not conceptual: the role's shell is `cmd.exe`, and the model tried, repeatedly, to
write multi-line Rust through mechanisms that do not survive that shell (a `bash -c` heredoc, a
`python -c` with real newlines inside a triple-quoted string, `echo` appends). It truncated
`src/game.rs` to 0 bytes at one point and only recovered because it had backed the file up itself
into `.hoh/scratch/`. The artifact it eventually left is *good* — the battery observed all five
criteria on it — but the cost of getting there is the single clearest thing to fix.

**The role environment does not carry the adapter's target directory.** The Developer ran
`cargo build --offline` in the project, which built a second, full target tree inside the project
(~8.5 GB) instead of reusing the warm shared one. `cache_excludes` keeps it out of the artifact
hash, so the round stays correct — but a cold build is ~5 minutes against a 180-second command
timeout, and one command-timeout failure is visible in the Developer's trajectory.

**Two full-suite runs were red before cleanup**, both for an environmental reason: a stray
`hof_game.exe` was still listening on 127.0.0.1:15702, which makes
`launch::tests::a_process_that_never_binds_the_endpoint_gives_up_on_its_budget` succeed where it
must fail, and perturbs the pre-existing (and independently flaky)
`brp::tests::a_slow_reply_that_exceeds_the_timeout_is_a_timeout`. Killing the strays and
re-running yields the measured green gate. A `hof_game.exe` can outlive the harness that started
it: killing the `hoh` process (as I did when aborting attempt 1) leaves the child alive, and the
adapter has no reap-on-drop.

**The role-side call record lost history.** A role's calls are written to
`runs/<run-id>/role-calls/`, but the file name used the per-process session counter, which
restarts at 1 for every `hoh tools call` invocation; the second call of a tool overwrote the
first. Round 1's roles made ~295 calls between them and 10 files survived. The name is now
stamped with the call's timestamp (with a collision guard) and a unit test pins it. The full
history is not lost — every call is in the role trajectories — but the adapter-side copy now
keeps it too.

**A live credential sits in the working tree.** `config/model.secret.env` (gitignored,
untracked, dated 21 Sep) still holds `HOH_MODEL_API_KEY=sk-…` with its own comment saying it
should have been deleted after the smoke test. The role prompts now list `config/**` as a
forbidden source, but nothing prevents a role from listing the directory, and the Developer did.

## What I could not verify

- **Four Tester gaps are open by construction, not by failure**: leftward movement, the
  release/stall rule, a transform sample taken at the win frame, and a ground-state payload that
  stands on its own. All four are *missing battery steps*; none is a behaviour that was observed
  to be wrong. They are the natural first additions to the battery.
- **The negative direction is not part of the round's own battery.** "A monotone fall must fail"
  is demonstrated by `tests/bevy_round1.rs`'s negative control (`runs/bevy-round1-negative-control/`:
  `rising=0, falling=32`), which runs the same battery against a deliberately broken
  spectator-only build. The round's own evidence is the positive arc (`rising=4, falling=8`).
- **Everything after iteration 1**: warm start, evidence feedback into iteration 2, and the
  Planner reacting to the Tester's gaps were not exercised (`--iterations 1`).
- **Windowed mode and the second endpoint (15703)** are out of scope by design; the round is
  headless, and the launch record's stderr shows the known headless render warnings.
- **The `exit_code` field inside `runs/bevy-round1b/meta.json` is `null`** by construction — the
  battery runs before the round ends — with the round's real exit code in
  `runs/round1b/exit_code` (0). The field says so in its own `exit_code_source` note.

## The single most important thing for the next batch

**Give a role a reliable way to write a file before anything else.** The round's whole cost
profile is set by the Developer's 54-minute, 140-call, 10.4M-token attempt that ended in
`RepeatedFormatError` while it fought `cmd.exe` to write one Rust file it had already designed.
Export the adapter's target directory to the role environment (so `cargo build` is warm) and add
a first-class write path — a `write_file`-style tool, or a documented, tested single-command
recipe for multi-line content on this shell — and the same round should cost a fraction of the
time with a better artifact. The four open gaps are a small, well-specified follow-up; the
Developer's write path is the thing that decides whether the next round is affordable at all.
