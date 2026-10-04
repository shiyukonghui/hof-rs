# Bevy round 2 - report

```json
{
  "schema": "hof-rs / bevy round 2 report",
  "produced_at": "2026-10-04T22:05:00+08:00",
  "branch": "bevy-core",
  "round": {
    "project": "F:/hof-bevy-r2/workspace",
    "project_outside_repository": true,
    "fresh_project": true,
    "init_command": "hoh init --project F:/hof-bevy-r2/workspace --adapter bevy",
    "init_exit_code": 0,
    "run_command": "hoh run --project F:/hof-bevy-r2/workspace --adapter bevy --run-id round2 --iterations 2",
    "run_exit_code": 0,
    "round_exit_code_file": 0,
    "process_exit_code_file": 0,
    "iterations_completed": 2,
    "headless": true,
    "endpoint_used": "http://127.0.0.1:15702/",
    "second_endpoint_15703_used": false,
    "round_total_tokens": 21619239,
    "model": "deepseek-v4.1-flash",
    "final_version_id": "cbc3d411c2360914d816524065293db92f9fb615451693469a0aa46d3fe9a805",
    "artifact_gate": {
      "applicable": true,
      "launchable": true,
      "reasons": []
    },
    "prd_coverage_line": "prd coverage: 7/12 verified (iteration 2 tester)"
  },
  "developer_cost": {
    "round_1_reference": {
      "source": ".spec/bevy/ROUND-1-REPORT.md task_3_real_round",
      "calls": 140,
      "duration_ms": 3263828,
      "duration_minutes": 54.4,
      "total_tokens": 10379180,
      "exit_status": "RepeatedFormatError"
    },
    "targets": {
      "duration": "minutes, not 54",
      "total_tokens": "below 1500000"
    },
    "round_2_iteration_1": {
      "calls": 150,
      "duration_ms": 1983386,
      "duration_minutes": 33.06,
      "prompt_tokens": 11108856,
      "completion_tokens": 194328,
      "total_tokens": 11303184,
      "tokens_per_call": 74059,
      "exit_status": "LimitsExceeded",
      "artifact_valid": true,
      "write_failures": [],
      "role_write_failure_lines_in_warnings_log": [],
      "write_directive_used": true,
      "trajectory": {
        "recorded_tool_calls": 125,
        "hoh_write_file": 22,
        "hoh_read_file": 3,
        "cat_occurrences": 0,
        "responses_without_a_tool_call": 40,
        "first_write_at_message_index": 14,
        "forbidden_shell_shapes_that_still_appear": {
          "cat": 0,
          "heredoc": 0,
          "bash -c": 0,
          "python -c": 0,
          "python -c with real newlines": 0,
          "commands with `;` on the first line": 0,
          "note": "a write payload is excluded from this judgement: Rust source carries `;`"
        },
        "model_stats": {
          "api_calls": 150,
          "instance_cost": 0.0
        }
      },
      "targets_met": {
        "duration": "partly (33.1 min is minutes, not 54, but still 33)",
        "tokens_below_1_5M": false
      }
    },
    "round_2_iteration_2": {
      "calls": 104,
      "duration_ms": 3615661,
      "duration_minutes": 60.26,
      "prompt_tokens": 8035712,
      "completion_tokens": 258409,
      "total_tokens": 8294121,
      "tokens_per_call": 77266,
      "exit_status": "TimeExceeded",
      "artifact_valid": true,
      "write_failures": [],
      "write_directive_used": true,
      "trajectory": {
        "recorded_tool_calls": 130,
        "hoh_write_file": 9,
        "hoh_read_file": 10,
        "cat_occurrences": 0,
        "responses_without_a_tool_call": 3,
        "first_write_at_message_index": 25,
        "forbidden_shell_shapes_that_still_appear": {
          "cat": 0,
          "heredoc": 0,
          "bash -c": 0,
          "python -c": 19,
          "python -c with real newlines": 11,
          "commands with `;` on the first line": 8,
          "note": "a write payload is excluded from this judgement: Rust source carries `;`"
        },
        "model_stats": {
          "api_calls": 104,
          "instance_cost": 0.0
        }
      },
      "targets_met": {
        "duration": false,
        "tokens_below_1_5M": false
      }
    },
    "round_2_developer_total": {
      "calls": 254,
      "duration_ms": 5599047,
      "duration_minutes": 93.32,
      "total_tokens": 19597305
    },
    "verdict": "The write path is reached and works; the token economics did NOT improve. 11.30M and 8.29M tokens against a 1.5M target."
  },
  "other_roles": {
    "planner_iteration_1": {
      "calls": 10,
      "total_tokens": 93851
    },
    "planner_iteration_2": {
      "calls": 8,
      "total_tokens": 70553
    },
    "tester_iteration_1": {
      "calls": 21,
      "total_tokens": 888339,
      "exit_status": "RepeatedFormatError"
    },
    "tester_iteration_2": {
      "calls": 24,
      "total_tokens": 969191,
      "exit_status": "Submitted"
    }
  },
  "warm_build": {
    "role_environment_export_proof": {
      "where": "runs/round2/iter-2/traj/developer.attempt1.json, assistant message 54 (the Developer ran `set HOH`-style env printing)",
      "observed": "CARGO_TARGET_DIR=F:/hof-bevy-r2\\hof-bevy-shared-target",
      "also_observed": "HOH_MODEL_API_KEY= (empty in the role shell: the harness blanking held)"
    },
    "target_directory_inside_the_workspace": false,
    "cold_a0_build_seconds": 298,
    "cold_a0_build_evidence": "F:/hof-bevy-r2/hof-bevy-shared-target/debug/.cargo-build-lock mtime 19:59:14 -> debug/hof_game.exe.locked (the A0 build, renamed later) mtime 20:04:12",
    "cold_figure_from_the_write_path_batch_seconds": 299.9,
    "role_command_timeout_seconds": 180,
    "battery_build_pass_1_millis": 1148,
    "battery_build_pass_2_millis": 1225,
    "battery_build_log_pass_2": "cargo build: exit Some(0), 1225 ms, warm",
    "developer_cargo_build_examples_from_the_trajectories": [
      "iteration 1: 58 `Finished ... in` lines; 16.86 s first successful build after an edit, 16.14-17.72 s after an edit, 0.92-1.08 s with nothing to do",
      "iteration 2: 14 `Finished ... in` lines; 16.23 s and 21.03/21.16 s after edits, 1.00-1.14 s with nothing to do"
    ],
    "new_friction_the_role_hit": {
      "shape": "error: failed to remove file `F:/hof-bevy-r2\\hof-bevy-shared-target\\debug\\hof_game.exe` (os error 5, Access is denied)",
      "why": "the round's own live game process holds the binary in the shared target the Developer must overwrite; the Developer worked around it by renaming the running exe to `hof_game.exe.locked` / `hof_game_old_r2.exe`",
      "cost": "7 tool results carry an error marker, ~8 of the Developer's calls in iteration 1 are the workaround"
    },
    "verdict": "The warm build is real and the export is proven: the adapter's shared target is in the role environment (CARGO_TARGET_DIR), the role's build finishes in ~17 s after an edit and ~1 s with nothing to do, no target/ appears inside the workspace, and the cold 298 s build could not have run inside the 180 s role command timeout."
  },
  "battery": {
    "steps_expected": 9,
    "gate_pass_1": {
      "applicable": true,
      "launchable": true,
      "reasons": []
    },
    "gate_pass_2": {
      "applicable": true,
      "launchable": true,
      "reasons": []
    },
    "pass_1_note": "iteration 1 pass, preserved because pass 2 replaced runs/bevy-round2; the harness also preserved it at runs/round2/quarantine/deterministic-pass-0.*",
    "pass_1_iteration_1": {
      "summary": "E3 movement=ok coins=ok win=ok jump=ok grounded=ok movement_left=ok movement_release=ok win_position=ok grounded_payload=ok",
      "steps": {
        "e3_movement": {
          "prd": "P1",
          "what": "injected move_dir=1 changes the player x",
          "observed": true,
          "failure": null,
          "call_ids": [
            9,
            10,
            11,
            12,
            13
          ],
          "call_files": [
            "runs/bevy-round2/calls/0009-bevy_inject_move.json",
            "runs/bevy-round2/calls/0010-bevy_wait_frames.json",
            "runs/bevy-round2/calls/0011-bevy_player_transform.json",
            "runs/bevy-round2/calls/0012-bevy_inject_move.json",
            "runs/bevy-round2/calls/0013-bevy_wait_frames.json"
          ]
        },
        "e3_coin_counter": {
          "prd": "P2",
          "what": "the coin counter goes 0 -> positive",
          "observed": true,
          "failure": null,
          "call_ids": [
            1,
            2,
            3,
            4,
            5,
            6,
            7,
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
            29,
            30,
            31
          ],
          "call_files": [
            "runs/bevy-round2/calls/0001-bevy_grounded.json",
            "runs/bevy-round2/calls/0002-bevy_wait_frames.json",
            "runs/bevy-round2/calls/0003-bevy_grounded.json",
            "runs/bevy-round2/calls/0004-bevy_wait_frames.json",
            "runs/bevy-round2/calls/0005-bevy_coin_counter.json",
            "runs/bevy-round2/calls/0006-bevy_win_flag.json",
            "runs/bevy-round2/calls/0007-bevy_player_transform.json",
            "runs/bevy-round2/calls/0014-bevy_coin_counter.json",
            "runs/bevy-round2/calls/0015-bevy_win_flag.json",
            "runs/bevy-round2/calls/0016-bevy_inject_move.json",
            "runs/bevy-round2/calls/0017-bevy_wait_frames.json",
            "runs/bevy-round2/calls/0018-bevy_coin_counter.json",
            "runs/bevy-round2/calls/0019-bevy_win_flag.json",
            "runs/bevy-round2/calls/0020-bevy_player_transform.json",
            "runs/bevy-round2/calls/0021-bevy_wait_frames.json",
            "runs/bevy-round2/calls/0022-bevy_coin_counter.json",
            "runs/bevy-round2/calls/0023-bevy_win_flag.json",
            "runs/bevy-round2/calls/0024-bevy_wait_frames.json",
            "runs/bevy-round2/calls/0025-bevy_coin_counter.json",
            "runs/bevy-round2/calls/0026-bevy_win_flag.json",
            "runs/bevy-round2/calls/0027-bevy_wait_frames.json",
            "runs/bevy-round2/calls/0028-bevy_coin_counter.json",
            "runs/bevy-round2/calls/0029-bevy_win_flag.json",
            "runs/bevy-round2/calls/0030-bevy_inject_move.json",
            "runs/bevy-round2/calls/0031-bevy_wait_frames.json"
          ]
        },
        "e3_win_flag": {
          "prd": "P3",
          "what": "the win flag goes false -> true",
          "observed": true,
          "failure": null,
          "call_ids": [
            1,
            2,
            3,
            4,
            5,
            6,
            7,
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
            29,
            30,
            31
          ],
          "call_files": [
            "runs/bevy-round2/calls/0001-bevy_grounded.json",
            "runs/bevy-round2/calls/0002-bevy_wait_frames.json",
            "runs/bevy-round2/calls/0003-bevy_grounded.json",
            "runs/bevy-round2/calls/0004-bevy_wait_frames.json",
            "runs/bevy-round2/calls/0005-bevy_coin_counter.json",
            "runs/bevy-round2/calls/0006-bevy_win_flag.json",
            "runs/bevy-round2/calls/0007-bevy_player_transform.json",
            "runs/bevy-round2/calls/0014-bevy_coin_counter.json",
            "runs/bevy-round2/calls/0015-bevy_win_flag.json",
            "runs/bevy-round2/calls/0016-bevy_inject_move.json",
            "runs/bevy-round2/calls/0017-bevy_wait_frames.json",
            "runs/bevy-round2/calls/0018-bevy_coin_counter.json",
            "runs/bevy-round2/calls/0019-bevy_win_flag.json",
            "runs/bevy-round2/calls/0020-bevy_player_transform.json",
            "runs/bevy-round2/calls/0021-bevy_wait_frames.json",
            "runs/bevy-round2/calls/0022-bevy_coin_counter.json",
            "runs/bevy-round2/calls/0023-bevy_win_flag.json",
            "runs/bevy-round2/calls/0024-bevy_wait_frames.json",
            "runs/bevy-round2/calls/0025-bevy_coin_counter.json",
            "runs/bevy-round2/calls/0026-bevy_win_flag.json",
            "runs/bevy-round2/calls/0027-bevy_wait_frames.json",
            "runs/bevy-round2/calls/0028-bevy_coin_counter.json",
            "runs/bevy-round2/calls/0029-bevy_win_flag.json",
            "runs/bevy-round2/calls/0030-bevy_inject_move.json",
            "runs/bevy-round2/calls/0031-bevy_wait_frames.json"
          ]
        },
        "e3_jump_arc": {
          "prd": "P4",
          "what": "a jump has rising AND falling steps",
          "observed": true,
          "failure": null,
          "call_ids": [
            41,
            42,
            43,
            44,
            45,
            46,
            47,
            48,
            49,
            50,
            51,
            52,
            53,
            54,
            55,
            56,
            57
          ],
          "call_files": [
            "runs/bevy-round2/calls/0041-bevy_grounded.json",
            "runs/bevy-round2/calls/0042-bevy_player_transform.json",
            "runs/bevy-round2/calls/0043-bevy_inject_jump.json",
            "runs/bevy-round2/calls/0044-bevy_wait_frames.json",
            "runs/bevy-round2/calls/0045-bevy_inject_jump.json",
            "runs/bevy-round2/calls/0046-bevy_player_transform.json",
            "runs/bevy-round2/calls/0047-bevy_player_transform.json",
            "runs/bevy-round2/calls/0048-bevy_player_transform.json",
            "runs/bevy-round2/calls/0049-bevy_player_transform.json",
            "runs/bevy-round2/calls/0050-bevy_player_transform.json",
            "runs/bevy-round2/calls/0051-bevy_player_transform.json",
            "runs/bevy-round2/calls/0052-bevy_player_transform.json",
            "runs/bevy-round2/calls/0053-bevy_player_transform.json",
            "runs/bevy-round2/calls/0054-bevy_player_transform.json",
            "runs/bevy-round2/calls/0055-bevy_player_transform.json",
            "runs/bevy-round2/calls/0056-bevy_player_transform.json",
            "runs/bevy-round2/calls/0057-bevy_player_transform.json"
          ]
        },
        "e3_grounded": {
          "prd": "P5",
          "what": "grounded reads true before take-off",
          "observed": true,
          "failure": null,
          "call_ids": [
            1,
            2,
            3,
            4,
            5,
            6,
            7
          ],
          "call_files": [
            "runs/bevy-round2/calls/0001-bevy_grounded.json",
            "runs/bevy-round2/calls/0002-bevy_wait_frames.json",
            "runs/bevy-round2/calls/0003-bevy_grounded.json",
            "runs/bevy-round2/calls/0004-bevy_wait_frames.json",
            "runs/bevy-round2/calls/0005-bevy_coin_counter.json",
            "runs/bevy-round2/calls/0006-bevy_win_flag.json",
            "runs/bevy-round2/calls/0007-bevy_player_transform.json"
          ]
        },
        "e3_movement_left": {
          "prd": "P1",
          "what": "injected move_dir=-1 moves x down",
          "observed": true,
          "failure": null,
          "call_ids": [
            32,
            33,
            34,
            35,
            36,
            37
          ],
          "call_files": [
            "runs/bevy-round2/calls/0032-bevy_player_transform.json",
            "runs/bevy-round2/calls/0033-bevy_inject_move.json",
            "runs/bevy-round2/calls/0034-bevy_wait_frames.json",
            "runs/bevy-round2/calls/0035-bevy_player_transform.json",
            "runs/bevy-round2/calls/0036-bevy_inject_move.json",
            "runs/bevy-round2/calls/0037-bevy_wait_frames.json"
          ]
        },
        "e3_movement_release": {
          "prd": "P1",
          "what": "after move_dir=0 the player stops",
          "observed": true,
          "failure": null,
          "call_ids": [
            38,
            39,
            40
          ],
          "call_files": [
            "runs/bevy-round2/calls/0038-bevy_player_transform.json",
            "runs/bevy-round2/calls/0039-bevy_wait_frames.json",
            "runs/bevy-round2/calls/0040-bevy_player_transform.json"
          ]
        },
        "e3_win_position": {
          "prd": "P3",
          "what": "a transform sample at or after the win frame",
          "observed": true,
          "failure": null,
          "call_ids": [
            1,
            2,
            3,
            4,
            5,
            6,
            7,
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
            29,
            30,
            31
          ],
          "call_files": [
            "runs/bevy-round2/calls/0001-bevy_grounded.json",
            "runs/bevy-round2/calls/0002-bevy_wait_frames.json",
            "runs/bevy-round2/calls/0003-bevy_grounded.json",
            "runs/bevy-round2/calls/0004-bevy_wait_frames.json",
            "runs/bevy-round2/calls/0005-bevy_coin_counter.json",
            "runs/bevy-round2/calls/0006-bevy_win_flag.json",
            "runs/bevy-round2/calls/0007-bevy_player_transform.json",
            "runs/bevy-round2/calls/0014-bevy_coin_counter.json",
            "runs/bevy-round2/calls/0015-bevy_win_flag.json",
            "runs/bevy-round2/calls/0016-bevy_inject_move.json",
            "runs/bevy-round2/calls/0017-bevy_wait_frames.json",
            "runs/bevy-round2/calls/0018-bevy_coin_counter.json",
            "runs/bevy-round2/calls/0019-bevy_win_flag.json",
            "runs/bevy-round2/calls/0020-bevy_player_transform.json",
            "runs/bevy-round2/calls/0021-bevy_wait_frames.json",
            "runs/bevy-round2/calls/0022-bevy_coin_counter.json",
            "runs/bevy-round2/calls/0023-bevy_win_flag.json",
            "runs/bevy-round2/calls/0024-bevy_wait_frames.json",
            "runs/bevy-round2/calls/0025-bevy_coin_counter.json",
            "runs/bevy-round2/calls/0026-bevy_win_flag.json",
            "runs/bevy-round2/calls/0027-bevy_wait_frames.json",
            "runs/bevy-round2/calls/0028-bevy_coin_counter.json",
            "runs/bevy-round2/calls/0029-bevy_win_flag.json",
            "runs/bevy-round2/calls/0030-bevy_inject_move.json",
            "runs/bevy-round2/calls/0031-bevy_wait_frames.json"
          ]
        },
        "e3_grounded_payload": {
          "prd": "P5",
          "what": "a Grounded payload carrying a boolean",
          "observed": true,
          "failure": null,
          "call_ids": [
            8
          ],
          "call_files": [
            "runs/bevy-round2/calls/0008-bevy_grounded.json"
          ]
        }
      }
    },
    "pass_2_iteration_2_final": {
      "summary": "E3 movement=ok coins=RED win=RED jump=ok grounded=ok movement_left=ok movement_release=ok win_position=ok grounded_payload=ok",
      "steps": {
        "e3_movement": {
          "prd": "P1",
          "what": "injected move_dir=1 changes the player x",
          "observed": true,
          "failure": null,
          "call_ids": [
            9,
            10,
            11,
            12,
            13
          ],
          "call_files": [
            "runs/bevy-round2/calls/0009-bevy_inject_move.json",
            "runs/bevy-round2/calls/0010-bevy_wait_frames.json",
            "runs/bevy-round2/calls/0011-bevy_player_transform.json",
            "runs/bevy-round2/calls/0012-bevy_inject_move.json",
            "runs/bevy-round2/calls/0013-bevy_wait_frames.json"
          ]
        },
        "e3_coin_counter": {
          "prd": "P2",
          "what": "the coin counter goes 0 -> positive",
          "observed": false,
          "failure": "the coin counter started at 1, not 0 (PRD P2 requires the count to start at 0)",
          "call_ids": [
            1,
            2,
            3,
            4,
            5,
            6,
            7,
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
            29,
            30,
            31
          ],
          "call_files": [
            "runs/bevy-round2/calls/0001-bevy_grounded.json",
            "runs/bevy-round2/calls/0002-bevy_wait_frames.json",
            "runs/bevy-round2/calls/0003-bevy_grounded.json",
            "runs/bevy-round2/calls/0004-bevy_wait_frames.json",
            "runs/bevy-round2/calls/0005-bevy_coin_counter.json",
            "runs/bevy-round2/calls/0006-bevy_win_flag.json",
            "runs/bevy-round2/calls/0007-bevy_player_transform.json",
            "runs/bevy-round2/calls/0014-bevy_coin_counter.json",
            "runs/bevy-round2/calls/0015-bevy_win_flag.json",
            "runs/bevy-round2/calls/0016-bevy_inject_move.json",
            "runs/bevy-round2/calls/0017-bevy_wait_frames.json",
            "runs/bevy-round2/calls/0018-bevy_coin_counter.json",
            "runs/bevy-round2/calls/0019-bevy_win_flag.json",
            "runs/bevy-round2/calls/0020-bevy_player_transform.json",
            "runs/bevy-round2/calls/0021-bevy_wait_frames.json",
            "runs/bevy-round2/calls/0022-bevy_coin_counter.json",
            "runs/bevy-round2/calls/0023-bevy_win_flag.json",
            "runs/bevy-round2/calls/0024-bevy_wait_frames.json",
            "runs/bevy-round2/calls/0025-bevy_coin_counter.json",
            "runs/bevy-round2/calls/0026-bevy_win_flag.json",
            "runs/bevy-round2/calls/0027-bevy_wait_frames.json",
            "runs/bevy-round2/calls/0028-bevy_coin_counter.json",
            "runs/bevy-round2/calls/0029-bevy_win_flag.json",
            "runs/bevy-round2/calls/0030-bevy_inject_move.json",
            "runs/bevy-round2/calls/0031-bevy_wait_frames.json"
          ]
        },
        "e3_win_flag": {
          "prd": "P3",
          "what": "the win flag goes false -> true",
          "observed": false,
          "failure": "the win flag was already true before the goal was reached",
          "call_ids": [
            1,
            2,
            3,
            4,
            5,
            6,
            7,
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
            29,
            30,
            31
          ],
          "call_files": [
            "runs/bevy-round2/calls/0001-bevy_grounded.json",
            "runs/bevy-round2/calls/0002-bevy_wait_frames.json",
            "runs/bevy-round2/calls/0003-bevy_grounded.json",
            "runs/bevy-round2/calls/0004-bevy_wait_frames.json",
            "runs/bevy-round2/calls/0005-bevy_coin_counter.json",
            "runs/bevy-round2/calls/0006-bevy_win_flag.json",
            "runs/bevy-round2/calls/0007-bevy_player_transform.json",
            "runs/bevy-round2/calls/0014-bevy_coin_counter.json",
            "runs/bevy-round2/calls/0015-bevy_win_flag.json",
            "runs/bevy-round2/calls/0016-bevy_inject_move.json",
            "runs/bevy-round2/calls/0017-bevy_wait_frames.json",
            "runs/bevy-round2/calls/0018-bevy_coin_counter.json",
            "runs/bevy-round2/calls/0019-bevy_win_flag.json",
            "runs/bevy-round2/calls/0020-bevy_player_transform.json",
            "runs/bevy-round2/calls/0021-bevy_wait_frames.json",
            "runs/bevy-round2/calls/0022-bevy_coin_counter.json",
            "runs/bevy-round2/calls/0023-bevy_win_flag.json",
            "runs/bevy-round2/calls/0024-bevy_wait_frames.json",
            "runs/bevy-round2/calls/0025-bevy_coin_counter.json",
            "runs/bevy-round2/calls/0026-bevy_win_flag.json",
            "runs/bevy-round2/calls/0027-bevy_wait_frames.json",
            "runs/bevy-round2/calls/0028-bevy_coin_counter.json",
            "runs/bevy-round2/calls/0029-bevy_win_flag.json",
            "runs/bevy-round2/calls/0030-bevy_inject_move.json",
            "runs/bevy-round2/calls/0031-bevy_wait_frames.json"
          ]
        },
        "e3_jump_arc": {
          "prd": "P4",
          "what": "a jump has rising AND falling steps",
          "observed": true,
          "failure": null,
          "call_ids": [
            41,
            42,
            43,
            44,
            45,
            46,
            47,
            48,
            49,
            50,
            51,
            52,
            53,
            54,
            55,
            56,
            57
          ],
          "call_files": [
            "runs/bevy-round2/calls/0041-bevy_grounded.json",
            "runs/bevy-round2/calls/0042-bevy_player_transform.json",
            "runs/bevy-round2/calls/0043-bevy_inject_jump.json",
            "runs/bevy-round2/calls/0044-bevy_wait_frames.json",
            "runs/bevy-round2/calls/0045-bevy_inject_jump.json",
            "runs/bevy-round2/calls/0046-bevy_player_transform.json",
            "runs/bevy-round2/calls/0047-bevy_player_transform.json",
            "runs/bevy-round2/calls/0048-bevy_player_transform.json",
            "runs/bevy-round2/calls/0049-bevy_player_transform.json",
            "runs/bevy-round2/calls/0050-bevy_player_transform.json",
            "runs/bevy-round2/calls/0051-bevy_player_transform.json",
            "runs/bevy-round2/calls/0052-bevy_player_transform.json",
            "runs/bevy-round2/calls/0053-bevy_player_transform.json",
            "runs/bevy-round2/calls/0054-bevy_player_transform.json",
            "runs/bevy-round2/calls/0055-bevy_player_transform.json",
            "runs/bevy-round2/calls/0056-bevy_player_transform.json",
            "runs/bevy-round2/calls/0057-bevy_player_transform.json"
          ]
        },
        "e3_grounded": {
          "prd": "P5",
          "what": "grounded reads true before take-off",
          "observed": true,
          "failure": null,
          "call_ids": [
            1,
            2,
            3,
            4,
            5,
            6,
            7
          ],
          "call_files": [
            "runs/bevy-round2/calls/0001-bevy_grounded.json",
            "runs/bevy-round2/calls/0002-bevy_wait_frames.json",
            "runs/bevy-round2/calls/0003-bevy_grounded.json",
            "runs/bevy-round2/calls/0004-bevy_wait_frames.json",
            "runs/bevy-round2/calls/0005-bevy_coin_counter.json",
            "runs/bevy-round2/calls/0006-bevy_win_flag.json",
            "runs/bevy-round2/calls/0007-bevy_player_transform.json"
          ]
        },
        "e3_movement_left": {
          "prd": "P1",
          "what": "injected move_dir=-1 moves x down",
          "observed": true,
          "failure": null,
          "call_ids": [
            32,
            33,
            34,
            35,
            36,
            37
          ],
          "call_files": [
            "runs/bevy-round2/calls/0032-bevy_player_transform.json",
            "runs/bevy-round2/calls/0033-bevy_inject_move.json",
            "runs/bevy-round2/calls/0034-bevy_wait_frames.json",
            "runs/bevy-round2/calls/0035-bevy_player_transform.json",
            "runs/bevy-round2/calls/0036-bevy_inject_move.json",
            "runs/bevy-round2/calls/0037-bevy_wait_frames.json"
          ]
        },
        "e3_movement_release": {
          "prd": "P1",
          "what": "after move_dir=0 the player stops",
          "observed": true,
          "failure": null,
          "call_ids": [
            38,
            39,
            40
          ],
          "call_files": [
            "runs/bevy-round2/calls/0038-bevy_player_transform.json",
            "runs/bevy-round2/calls/0039-bevy_wait_frames.json",
            "runs/bevy-round2/calls/0040-bevy_player_transform.json"
          ]
        },
        "e3_win_position": {
          "prd": "P3",
          "what": "a transform sample at or after the win frame",
          "observed": true,
          "failure": null,
          "call_ids": [
            1,
            2,
            3,
            4,
            5,
            6,
            7,
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
            29,
            30,
            31
          ],
          "call_files": [
            "runs/bevy-round2/calls/0001-bevy_grounded.json",
            "runs/bevy-round2/calls/0002-bevy_wait_frames.json",
            "runs/bevy-round2/calls/0003-bevy_grounded.json",
            "runs/bevy-round2/calls/0004-bevy_wait_frames.json",
            "runs/bevy-round2/calls/0005-bevy_coin_counter.json",
            "runs/bevy-round2/calls/0006-bevy_win_flag.json",
            "runs/bevy-round2/calls/0007-bevy_player_transform.json",
            "runs/bevy-round2/calls/0014-bevy_coin_counter.json",
            "runs/bevy-round2/calls/0015-bevy_win_flag.json",
            "runs/bevy-round2/calls/0016-bevy_inject_move.json",
            "runs/bevy-round2/calls/0017-bevy_wait_frames.json",
            "runs/bevy-round2/calls/0018-bevy_coin_counter.json",
            "runs/bevy-round2/calls/0019-bevy_win_flag.json",
            "runs/bevy-round2/calls/0020-bevy_player_transform.json",
            "runs/bevy-round2/calls/0021-bevy_wait_frames.json",
            "runs/bevy-round2/calls/0022-bevy_coin_counter.json",
            "runs/bevy-round2/calls/0023-bevy_win_flag.json",
            "runs/bevy-round2/calls/0024-bevy_wait_frames.json",
            "runs/bevy-round2/calls/0025-bevy_coin_counter.json",
            "runs/bevy-round2/calls/0026-bevy_win_flag.json",
            "runs/bevy-round2/calls/0027-bevy_wait_frames.json",
            "runs/bevy-round2/calls/0028-bevy_coin_counter.json",
            "runs/bevy-round2/calls/0029-bevy_win_flag.json",
            "runs/bevy-round2/calls/0030-bevy_inject_move.json",
            "runs/bevy-round2/calls/0031-bevy_wait_frames.json"
          ]
        },
        "e3_grounded_payload": {
          "prd": "P5",
          "what": "a Grounded payload carrying a boolean",
          "observed": true,
          "failure": null,
          "call_ids": [
            8
          ],
          "call_files": [
            "runs/bevy-round2/calls/0008-bevy_grounded.json"
          ]
        }
      }
    },
    "verdicts_against_the_pipeline_final_artifact": {
      "e3_movement": true,
      "e3_coin_counter": true,
      "e3_win_flag": true,
      "e3_jump_arc": true,
      "e3_grounded": true,
      "e3_movement_left": true,
      "e3_movement_release": true,
      "e3_win_position": true,
      "e3_grounded_payload": true,
      "source": "reporter-side independent replay on a clean process of version cbc3d411... (F:/hof-bevy-r2/replay/), not the adapter battery"
    }
  },
  "process_attribution_defect": {
    "summary": "Both battery passes and the Tester's live calls were answered by pid 22956, the game session started at 20:04:15 from the A0 scaffold binary - not by the processes those passes launched. No battery in round 2 observed either Developer artifact.",
    "game_processes_alive_after_the_round_exited_0": [
      {
        "pid": 22956,
        "started": "20:04:15",
        "listening_on_15702": true,
        "what": "the round's first game session (A0 scaffold binary, built 20:04:12)"
      },
      {
        "pid": 37864,
        "started": "20:38:03",
        "listening_on_15702": false,
        "what": "spawned at pass 1's battery time; also named in runs/round2/meta.json"
      },
      {
        "pid": 51500,
        "started": "21:40:36",
        "listening_on_15702": false,
        "what": "spawned at pass 2's battery time"
      }
    ],
    "launch_json_pids_that_no_longer_exist": {
      "pass_1": 49748,
      "pass_2": 53560
    },
    "proof": {
      "method": "the game's own FrameCounter read by the battery, against the process start times",
      "pass_1_first_read": {
        "frame": 118940,
        "at": "2026-10-04T20:37:57.363"
      },
      "pass_2_first_read": {
        "frame": 340386,
        "at": "2026-10-04T21:40:30.032"
      },
      "implied_rate_fps": 59.01,
      "implied_process_start": "2026-10-04T20:04:22 (pid 22956 started 20:04:15)",
      "a_process_launched_at_the_battery_start_would_read_frame": "under 200 (ready_millis is 165 and 178)"
    },
    "corollary_1": "The coin/win red verdicts of pass 2 are the stale process's one-way latches (coins and won were latched by pass 1's own contact phase, not left behind by any role); they are not a defect of the iteration-2 artifact.",
    "corollary_2": "The recorded jump arcs (first -200.0, peak -165.01) match the A0 replay (first -200.0, peak -165.27); the iteration-1 artifact's own arc is first -180.0, peak -145.0.",
    "reporter_side_replay": {
      "iteration_1_artifact_31dc47c4": {
        "coins_baseline": 0,
        "coins_max": 1,
        "win_baseline": false,
        "win_ever_true": true,
        "movement_right_delta": 63.33,
        "movement_left_delta": -60.0,
        "release_delta": 0.0,
        "jump_rising": 2,
        "jump_falling": 3,
        "jump_first": -180.0,
        "jump_peak": -145.0,
        "grounded_before_jump": true
      },
      "final_iteration_2_artifact_cbc3d411": {
        "coins_baseline": 0,
        "coins_max": 1,
        "win_baseline": false,
        "win_ever_true": true,
        "movement_right_delta": 60.0,
        "movement_left_delta": -60.0,
        "release_delta": 0.0,
        "jump_rising": 3,
        "jump_falling": 2,
        "jump_first": -180.0,
        "jump_peak": -145.0,
        "grounded_before_jump": true
      },
      "a0_scaffold_b207fb23": {
        "coins_baseline": 0,
        "coins_max": 1,
        "win_baseline": false,
        "win_ever_true": true,
        "jump_first": -200.0,
        "jump_peak": -165.27,
        "grounded_before_jump": true
      },
      "where": "F:/hof-bevy-r2/replay/*-replay.json (outside the repository)"
    }
  },
  "feedback_loop_iteration_2": {
    "moved": true,
    "iter_2_planner_view_evidence_json_equals_iter_1_evidence_json": true,
    "plan_changed": true,
    "plan_diff_lines": 29,
    "iteration_1_gap_ids": [
      "P3b-goal-contact-geometry",
      "P2b-coin-contact-geometry"
    ],
    "iteration_2_priority_2_and_3": "tie the coin pickup to a real coin body instead of a bare threshold; tie the win to a reachable goal body instead of a bare threshold",
    "iteration_2_plan_quotes_iteration_1_measurements": true,
    "iteration_2_developer_changed": {
      "added": [],
      "modified": [
        "src/contract.rs",
        "src/game.rs"
      ],
      "removed": []
    },
    "iteration_2_gap_ids": [
      "P2-coin-counter",
      "P2-coin-body-overlap",
      "P3-win-flag",
      "P3-goal-body-reachable",
      "P2-P3-regression"
    ],
    "note": "iteration 2's Tester reported the coin/win regression it read from the battery; that reading is the stale process (see process_attribution_defect), but the feedback loop itself demonstrably carried iteration 1's evidence into iteration 2's plan."
  },
  "evidence_paths": {
    "harness_run": [
      "runs/round2/meta.json",
      "runs/round2/exit_code",
      "runs/round2/process_exit_code",
      "runs/round2/warnings.log",
      "runs/round2/TOOLS.md",
      "runs/round2/versions/index.json",
      "runs/round2/role-calls/**",
      "runs/round2/quarantine/**"
    ],
    "iterations": [
      "runs/round2/iter-1/{plan.md,evidence.json,qa_report.md,result.json,usage.json}",
      "runs/round2/iter-1/logs/*.log",
      "runs/round2/iter-1/traj/*.json",
      "runs/round2/iter-1/candidate/**",
      "runs/round2/iter-2/** (same layout)"
    ],
    "battery_final": [
      "runs/bevy-round2/meta.json",
      "runs/bevy-round2/build.log",
      "runs/bevy-round2/launch.json",
      "runs/bevy-round2/gate.json",
      "runs/bevy-round2/readings/{e3-observations,coin_counter,win_flag,player_transform,grounded}.json",
      "runs/bevy-round2/calls/0001..0057-*.json",
      "runs/bevy-round2/qa/{e3-summary.txt,pointer.json}"
    ],
    "battery_pass_1_snapshot": [
      "F:/hof-bevy-r2/bevy-round2-pass1-snapshot/**",
      "runs/round2/quarantine/deterministic-pass-0.*"
    ],
    "tester_facing": [
      "<project>/.hoh/deterministic/battery.json",
      "<project>/.hoh/deterministic/raw/e3_*.json",
      "<project>/.hoh/deterministic/mcp-errors.jsonl"
    ],
    "driver_logs_outside_the_repository": [
      "F:/hof-bevy-r2/init.out",
      "F:/hof-bevy-r2/run.round2.out",
      "F:/hof-bevy-r2/run.round2.err",
      "F:/hof-bevy-r2/gate-test.log",
      "F:/hof-bevy-r2/gate-list.log",
      "F:/hof-bevy-r2/fmt.log",
      "F:/hof-bevy-r2/replay/"
    ],
    "paths_with_the_model_key": [
      "config/model.secret.env (pre-existing, gitignored, not created by this batch; the key is redacted as sk-\u2026 here)"
    ]
  },
  "gate": {
    "command": "cargo test --offline",
    "exit_code": 0,
    "passed": 694,
    "failed": 0,
    "ignored": 3,
    "tests_listed": 697,
    "test_binaries": 52,
    "list_command": "cargo test --offline -- --list",
    "tests_listed_equals_passed_plus_ignored": true,
    "tests_removed": 0,
    "warning_lines": 0,
    "fmt_command": "cargo fmt --all --check",
    "fmt_exit_code": 0,
    "build_dir": "F:/moonbit-hof-rs-build-r2/target",
    "own_build_dir": true,
    "no_other_test_process": true,
    "measured_twice": {
      "run_1": "after `touch src/lib.rs`: 169 crates compiled, 694 passed / 0 failed / 3 ignored / 697 listed, 0 warning lines, exit 0",
      "run_2": "after `touch src/lib.rs` on the final tree: 694 passed / 0 failed / 3 ignored / 697 listed, 0 warning lines, exit 0"
    },
    "start_tree_expected": "694 passed / 0 failed / 3 ignored / 697 listed",
    "head": "6ecc14f3c13113de2f5d005c1e9b0348af880c50"
  },
  "changed_files": {
    "repository_modified": [],
    "repository_added": [
      ".spec/bevy/ROUND-2-REPORT.md"
    ],
    "evidence_written_gitignored": [
      "runs/round2/**",
      "runs/bevy-round2/**"
    ],
    "outside_the_repository": [
      "F:/hof-bevy-r2/workspace/** (the round's project)",
      "F:/hof-bevy-r2/hof-bevy-shared-target/**",
      "F:/hof-bevy-r2/iter1-workspace/**",
      "F:/hof-bevy-r2/a0-workspace/**",
      "F:/hof-bevy-r2/scripts/**",
      "F:/hof-bevy-r2/replay/**",
      "F:/hof-secrets/round2.env (the key file the driver read)"
    ],
    "forbidden_documents_touched": [],
    "src_or_tests_changed": false,
    "committed": false,
    "pushed": false
  },
  "credential_hygiene": {
    "key_written_into_the_repository_by_this_batch": false,
    "key_in_this_report": false,
    "key_passed_on_any_command_line": false,
    "mechanism": "the driver script read the key from F:/hof-secrets/round2.env (outside the repository) and exported it inside the script, so no command line and no DSH_TERM_CMD ever carried it",
    "pre_existing_leak_found": "config/model.secret.env still holds HOH_MODEL_API_KEY=sk-\u2026 (gitignored, untracked); this batch did not create or read it into any evidence"
  }
}
```

## What worked

1. **The round ran end to end, from a fresh empty project outside the repository.** `hoh init
   --adapter bevy` exited 0 and wrote the six scaffold files; `hoh run --adapter bevy --iterations 2`
   exited 0, both iterations completed, the artifact gate was green and the frozen hashes came out
   identical to round 1 (`contract_sha256 792001e7…`, `feature_sha256 d6a90ba3…`, `lock_sha256
   660e7e17…`). Nothing in the harness had to be repaired to get there.

2. **The write directive is reached by the model, and it works.** The Developer used
   `HOH_WRITE_FILE src/game.rs` 22 times in iteration 1 and 9 times in iteration 2, with **zero**
   `cat ` occurrences, zero heredocs and zero `bash -c` in either trajectory. The first write in
   iteration 1 landed on message 14 (about 10% into the call) and every write round-tripped
   byte-exact ("wrote 12720 byte(s) to src/game.rs"). `HOH_READ_FILE` was used too. The round-1
   failure shape — a model fighting `cmd.exe` to get one file onto disk — is gone; what survives is
   listed under "what did not work" (2).

3. **The warm build is real and the export is proven from the role's own mouth.** In iteration 2 the
   Developer printed its environment and it contains `CARGO_TARGET_DIR=F:/hof-bevy-r2\hof-bevy-shared-target`
   — the adapter's shared target. No `target/` directory exists inside the workspace. The role's
   `cargo build --offline` finished in **16.86 s** after an edit and **0.93–1.01 s** with nothing to
   do, and the two battery builds recorded **1148 ms (pass 1)** and **1225 ms (pass 2)**, both
   labelled `warm`. The one cold build of the round was the A0 build the adapter did itself:
   **298 s** (19:59:14 → 20:04:12), against the write-path batch's 299.9 s cold figure and a 180 s
   role command timeout — which is exactly why a role must never do a cold build.

4. **The evidence feedback loop moved.** Iteration 2's Planner was handed iteration 1's evidence
   bundle (`runs/round2/iter-2/planner-view/.hoh/evidence.json` is byte-identical to
   `runs/round2/iter-1/evidence.json`), its plan differs from iteration 1's by a 29-line diff, and
   its new priorities 2 and 3 are precisely iteration 1's two open gaps
   (`P2b-coin-contact-geometry`, `P3b-goal-contact-geometry`): "tie the coin pickup to a real coin
   body instead of a bare threshold" and "tie the win to a reachable goal body". The new plan even
   quotes iteration 1's measured numbers (54 px, 0.0 px drift). The loop is not inert.

5. **The nine-step battery ran, with raw evidence for every step.** Both passes wrote
   `readings/e3-observations.json` and 57 raw call files, one per request/response pair, and the
   four new steps are present alongside the original five (ids unchanged). The two red steps in
   pass 2 are named with verbatim reasons rather than swallowed.

6. **The gate is unchanged and green.** 694 passed / 0 failed / 3 ignored / 697 listed, 52 test
   binaries, 0 warning lines, `cargo fmt --all --check` exit 0, `cargo test --offline` **exit 0**,
   measured twice in this batch's own build directory with no other test process running.

## What did not work

1. **The economics did not improve — this is the headline.** The Developer's round-2 cost, against
   round 1's 140 calls / 54.4 min / 10.38 M tokens:

   | | calls | minutes | total tokens | exit status |
   |---|---|---|---|---|
   | round 1 | 140 | 54.4 | 10,379,180 | `RepeatedFormatError` |
   | round 2, iteration 1 | **150** | **33.1** | **11,303,184** | `LimitsExceeded` (step limit 150) |
   | round 2, iteration 2 | **104** | **60.3** | **8,294,121** | `TimeExceeded` (3600 s wall limit) |
   | round 2, both | 254 | 93.3 | 19,597,305 | — |

   The token target (< 1.5 M) was missed by 7.5× and 5.5×; the round-1 figure was not beaten at all,
   and iteration 2 took longer than round 1. Prompt tokens per call are the same in both rounds —
   ~74 k — so the write path changed *what the model fights* without changing *what a call costs*.
   `write_failures` is `[]` in both iterations and `warnings.log` carries no `role_write_failure:`
   line, which is correct by the module's own rule (the Developer *did* write its artifact) and is
   exactly why the budget never fired: `artifact_write_budget_seconds` disarms on the first project
   write, which came ~10% into each call, and `artifact_write_budget_tokens` is post-hoc.

2. **The POSIX prohibitions are not fully obeyed — but they are now cheap.** Iteration 2's Developer
   still reached for two of the forbidden shapes: one `python -c "` with **real newlines** (message
   35) and two `python -c … ; type <file>` command lines (messages 69 and 71). Every one of them
   produced **empty output at exit 0** — the `;` is not a `cmd.exe` separator and the newlines never
   survive — and the model moved on, losing one call each. Compare round 1, where the same shapes
   cost the whole call. The write path is what makes them harmless now: nothing that matters has to
   go through the shell.

3. **The new grind shape is "it never stops".** Iteration 1: 125 recorded tool calls of which 22
   were full 12 KB rewrites of `src/game.rs` and 63 were `cargo build`/`cargo check`. From message
   ~140 to the end it did nothing but repeat the same verification loop
   (`cargo build … & echo LAUNCHABLE_EXIT=%ERRORLEVEL%` plus a `findstr` over the contract
   constants) some 70 times, until `LimitsExceeded`. Iteration 2 was the same shape at a lower call
   count but a longer wall clock (60.3 min), ending `TimeExceeded`. The repeated-action tripwire
   (`max_action_failures: 3`) never fires for an action that *succeeds* every time, and the
   zero-progress loop is invisible to every counter the round currently has.

4. **Both battery passes observed the wrong process, so the round's E3 verdicts describe neither
   Developer artifact.** This is the most surprising finding and it is proven, not inferred:

   * After the round exited 0, three `hof_game.exe` processes were still alive: **pid 22956**
     (started 20:04:15, the round's first game session, built from the **A0 scaffold** binary),
     pid 37864 (20:38:03) and pid 51500 (21:40:36). Only 22956 was `LISTENING` on 15702.
   * Both battery passes read the game's own `FrameCounter`: pass 1 first read frame **118940** at
     20:37:57.363, pass 2 first read frame **340386** at 21:40:30.032. That is **59.01 fps** between
     them and implies one and the same process started at **20:04:22** — pid 22956. A process
     launched at the battery's own start (its `ready_millis` are 178 and 165) would have been at
     frame < 200.
   * The `pids` recorded in `launch.json` (49748, 53560) no longer exist; the process that answered
     answers for both passes and for the Tester's own live calls (`bevy_coin_counter` → `frame
     345107`, timestamped 21:41:49, i.e. again pid 22956).
   * The recorded jump arcs corroborate it: both passes measured first `-200.0`, peak `-165.01`,
     which is the A0 scaffold's arc (replayed here: `-200.0` / `-165.27`); the iteration-1
     artifact's own arc is first `-180.0`, peak `-145.0`.
   * Consequence: pass 1's "all nine green" describes A0, and pass 2's "coins RED (started at 1) /
     win RED (already true)" describes the *same A0 process*, whose one-way latches had been fired
     by pass 1's own contact phase. The Tester, whose playbook promises "it is running the frozen
     candidate, so a call you make now is evidence about the artifact you are judging", reported a
     regression that the candidate does not have. Round 1's report recorded the same class of event
     as an environmental accident after a killed `hoh`; here it happens **inside a normal
     two-iteration round**, because Windows `SO_REUSEADDR` lets the new game bind 15702 while the
     stale one keeps answering it, and nothing reaps the previous session.

5. **Reporter-side replay: both Developer artifacts are actually fine.** With the port free and
   three stale processes killed, I launched each artifact's own binary and drove the nine steps over
   the same BRP wire (`F:/hof-bevy-r2/replay/`). Version `31dc47c4` (iteration 1) and version
   `cbc3d411…` (iteration 2, the round's final artifact) both give coins `0 → 1`, win `false → true`,
   right/left movement of ±60 px, a release delta of 0.0, a jump arc with both rising and falling
   steps (peak `-145.0`, first `-180.0`) and `Grounded = true` before take-off. **The round's final
   artifact satisfies all five original criteria and all four new steps** — the adapter's red
   verdicts are an attribution failure, not a game defect. (This replay is my verification, not the
   round's criterion evidence; the round's own evidence remains the recorded battery.)

6. **The exit code does not reflect the E3 verdicts.** `runs/round2/exit_code` is 0 and the artifact
   gate is `launchable: true` even for the pass whose battery reported two red E3 steps. `DR-27`
   judges the artifact by build+boot only, so a run can finish "green" while the observations that
   are the point of the PRD are red.

7. **A new friction the warm target introduced.** Because the round's own live game process holds
   `<target>/debug/hof_game.exe`, the Developer's `cargo build` fails with
   `error: failed to remove file … hof_game.exe (os error 5, Access is denied)` until it renames the
   running binary. Iteration 1 lost ~8 calls (7 error-marked tool results) to this.

## What I could not verify

* **Which of the three leftover processes the harness thought it had stopped.** The pids recorded in
  `launch.json` (49748, 53560) are gone, two *other* game processes started at exactly the two
  battery moments (37864, 51500) are alive, and `meta.json` names a third (37864) as the published
  route. I can prove which process *answered*; I cannot prove from the recorded files which process
  the stop path believed it was terminating.
* **Whether the harness would have reaped the stale session on a machine without `SO_REUSEADDR`**
  (Linux). The port-sharing behaviour that hides the stale listener is Windows-specific; the
  missing stop is not.
* **`SO_REUSEADDR` itself is inferred**, not read from Bevy's source in this batch: the evidence is
  that a newly spawned game reports `ready` in 165–178 ms while its own frame counter is never the
  one that answers.
* **The negative control on a real game** (`a monotone fall must fail`) was not re-run in round 2;
  it lives in `tests/bevy_round1.rs` and is `#[ignore]`d. The round's own artifacts all show a real
  two-direction arc, so the negative control was not exercised here.
* **Round-1's own evidence has the same attribution problem.** Its recorded first read was frame
  198496, ~55 min into a round whose Developer window was 54.4 min — consistent with the same
  stale-process pattern. I did not re-run round 1.
* **The `HOH_WRITE_FILE` directive is exercised by two agents only** (both Developers). The Planner
  wrote its plan and the Tester wrote its evidence with it too, but a role that has to write many
  small files, or edit in place, is still untested.

## The single most important thing the next batch should do

**Bind a battery pass to the process it launched, and kill the previous session before starting the
next one — then re-measure the economics.**

Everything else in round 2 is downstream of this. Because 15702 was answered by a stale A0 process:

* the nine-step battery, both times, measured a game that is not the candidate (and round 1's
  five-criterion claim is open to the same doubt);
* the Tester reported a regression the candidate does not have, and the iteration-2 Planner and
  Developer spent their whole call chasing it — which is plausibly a large part of why the round
  cost 19.6 M tokens instead of the targeted sub-1.5 M;
* and no reader of `runs/bevy-round2/` can tell any of that from the files, because `launch.json`
  records a pid and a binary hash, neither of which is checked against the process that answers.

Concretely: (a) stop and *verify the death of* the previous round's game process before launching a
new one (and fail the pass if anything else is listening on 15702); (b) make the readiness check
prove identity, not reachability — e.g. a nonce resource that the newly launched process must serve,
or compare the answering process's `FrameCounter`/start time against the pid the harness spawned;
(c) record the answering pid and its creation time in `launch.json`, not the pid it hoped for. Only
then is it worth measuring the Developer's cost again, because until then "the battery is green" and
"the battery is red" are both statements about an unknown process.

## Reproduce

```text
hoh init --project F:/hof-bevy-r2/workspace --adapter bevy                       # exit 0
hoh run  --project F:/hof-bevy-r2/workspace --adapter bevy --run-id round2 --iterations 2   # exit 0
cargo test --offline        # exit 0, 694 passed / 0 failed / 3 ignored / 697 listed
cargo fmt --all --check     # exit 0
```

The model key was read from an out-of-repository file (`F:/hof-secrets/round2.env`) inside the driver
script, so it never appeared on a command line, in `DSH_TERM_CMD`, in `config/hoh.yaml`, or anywhere
under `runs/**`. `HOH_MODEL_API_KEY` reads empty in the role shells, as the Developer's own `set`
output shows. The pre-existing `config/model.secret.env` still contains the key (`sk-…`, gitignored);
I did not copy it anywhere.
