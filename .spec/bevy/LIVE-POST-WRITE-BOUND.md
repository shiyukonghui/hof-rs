```json
{
 "schema": "hof-rs / bevy live round under the post-write call bound — one real round from outside the repository",
 "artifact": ".spec/bevy/LIVE-POST-WRITE-BOUND.md",
 "produced_at": "2026-10-06",
 "branch": "bevy-core",
 "head_under_test": "15c7f7e1e597373de926a646839c43c5fea3b962 (docs(acceptance): record the acceptance that passes the post-write bound); src/** is byte-identical to the post-write-bound implementation e900262, and this commit adds only the acceptance document",
 "binary": {
  "path": "E:\\pwb-target\\debug\\hoh.exe",
  "built_before_the_round_at_local": "2026-10-06T10:55:45 (the round started at 10:56:09; the file's mtime changed again when the later gate relinked into the same target dir)",
  "how_built": "cargo build --offline --bin hoh, literal exit code 0",
  "build_dir": "E:/pwb-target (own dir; the repository's own target/ was not used)"
 },
 "kind": "one live round, three iterations requested, real model calls, real game process, real battery",
 "run_exit_codes": {
  "hoh_init": {
   "command": "hoh init --adapter bevy --project E:\\live3\\project",
   "literal_exit_code": 0
  },
  "hoh_run": {
   "command": "hoh run --adapter bevy --project E:\\live3\\project --run-id postwrite1 --env-from-secret D:\\hof-live\\secret.env",
   "literal_exit_code": 0,
   "stderr": "",
   "runs_dir_exit_code": 0,
   "runs_dir_process_exit_code": 0,
   "started_at_local": "2026-10-06T10:56:09+0800",
   "finished_at_local": "2026-10-06T11:49:09+0800",
   "wall_clock_minutes": 53.0
  },
  "outcome": "COMPLETED: three iterations, every iteration ok, every iteration's artifact gate launchable, exit 0"
 },
 "criterion": {
  "tokens_per_developer_call": 1500000,
  "source": "config/hoh.yaml agent.artifact_write_budget_tokens",
  "met": true,
  "measured_basis": "all three Developer calls of this round are under it: 563,813 / 679,401 / 854,890",
  "tightest_call_of_the_round": {
   "iteration": 3,
   "tokens": 854890,
   "ratio": 0.5699,
   "headroom_tokens": 645110
  }
 },
 "round": {
  "run_id": "postwrite1",
  "project": "E:\\live3\\project (created empty, outside the repository)",
  "run_tree_kept": "runs/postwrite1 (12 MB) and runs/bevy-postwrite1 (1.3 GB), gitignored, kept",
  "key_source": "D:\\hof-live\\secret.env (outside the repository; never read, copied, printed or written by this experiment)",
  "bevy_build_target": "D:\\hof-live-run\\hof-bevy-shared-target",
  "hoh_build_target": "E:/pwb-target on E:"
 },
 "post_write_bound_mechanism_in_force": {
  "step_is_a_model_call": true,
  "unwritten_allowance_model_calls": 43,
  "written_bound_model_calls": 35,
  "billed_calls_at_the_bound": 36,
  "billed_calls_at_the_unwritten_allowance": 44,
  "config": {
   "step_limit": 150,
   "wrap_up_steps": 25,
   "steps_per_artifact": 8,
   "post_write_step_limit": 35
  }
 },
 "developer_calls": [
  {
   "iteration": 1,
   "trajectory": "runs\\postwrite1\\iter-1\\traj\\developer.attempt1.json",
   "counted_HOH_WRITE_FILE_project_write": true,
   "first_counted_project_write_call_index": 6,
   "counted_project_write_call_indices": [
    6,
    29
   ],
   "n_counted_project_writes": 2,
   "scratch_HOH_WRITE_FILE_calls": [],
   "billed_model_calls": 36,
   "exit_status": "StepBudgetExceeded",
   "exit_was_limits": true,
   "post_write_bound_engaged": true,
   "ended_on": "the post-write bound (35 allowed, 36 billed)",
   "total_tokens": 563813,
   "prompt_tokens": 512467,
   "completion_tokens": 51346,
   "ratio_to_the_criterion": 0.3759,
   "margin_tokens_under_the_criterion": 936187,
   "headroom_fraction_of_the_criterion": 0.6241,
   "prefix_tokens_if_it_had_stopped_at_35_calls": 551444,
   "prefix_tokens_at_36_calls": 563813,
   "prefix_tokens_at_37_calls": null,
   "ratio_of_this_call_to_each_projected_36_call_figure": {
    "round4-iter-1": 0.5001,
    "round4-iter-2": 0.4712,
    "round4-iter-3 (the binding recording)": 0.3882,
    "livecost1-iter-1": 1.0087,
    "live-completion1-iter-1": 0.9736,
    "live-completion1-iter-2": 0.8894
   }
  },
  {
   "iteration": 2,
   "trajectory": "runs\\postwrite1\\iter-2\\traj\\developer.attempt1.json",
   "counted_HOH_WRITE_FILE_project_write": true,
   "first_counted_project_write_call_index": 8,
   "counted_project_write_call_indices": [
    8
   ],
   "n_counted_project_writes": 1,
   "scratch_HOH_WRITE_FILE_calls": [],
   "billed_model_calls": 36,
   "exit_status": "StepBudgetExceeded",
   "exit_was_limits": true,
   "post_write_bound_engaged": true,
   "ended_on": "the post-write bound (35 allowed, 36 billed)",
   "total_tokens": 679401,
   "prompt_tokens": 639075,
   "completion_tokens": 40326,
   "ratio_to_the_criterion": 0.4529,
   "margin_tokens_under_the_criterion": 820599,
   "headroom_fraction_of_the_criterion": 0.5471,
   "prefix_tokens_if_it_had_stopped_at_35_calls": 653311,
   "prefix_tokens_at_36_calls": 679401,
   "prefix_tokens_at_37_calls": null,
   "ratio_of_this_call_to_each_projected_36_call_figure": {
    "round4-iter-1": 0.6026,
    "round4-iter-2": 0.5678,
    "round4-iter-3 (the binding recording)": 0.4678,
    "livecost1-iter-1": 1.2155,
    "live-completion1-iter-1": 1.1732,
    "live-completion1-iter-2": 1.0718
   }
  },
  {
   "iteration": 3,
   "trajectory": "runs\\postwrite1\\iter-3\\traj\\developer.attempt1.json",
   "counted_HOH_WRITE_FILE_project_write": false,
   "first_counted_project_write_call_index": null,
   "counted_project_write_call_indices": [],
   "n_counted_project_writes": 0,
   "scratch_HOH_WRITE_FILE_calls": [],
   "billed_model_calls": 44,
   "exit_status": "StepBudgetExceeded",
   "exit_was_limits": true,
   "post_write_bound_engaged": false,
   "ended_on": "the unwritten allowance (43 allowed, 44 billed) — no counted write existed",
   "total_tokens": 854890,
   "prompt_tokens": 839333,
   "completion_tokens": 15557,
   "ratio_to_the_criterion": 0.5699,
   "margin_tokens_under_the_criterion": 645110,
   "headroom_fraction_of_the_criterion": 0.4301,
   "prefix_tokens_if_it_had_stopped_at_35_calls": 680522,
   "prefix_tokens_at_36_calls": 707030,
   "prefix_tokens_at_37_calls": 734642,
   "ratio_of_this_call_to_each_projected_36_call_figure": {
    "round4-iter-1": 0.7583,
    "round4-iter-2": 0.7145,
    "round4-iter-3 (the binding recording)": 0.5886,
    "livecost1-iter-1": 1.5295,
    "live-completion1-iter-1": 1.4762,
    "live-completion1-iter-2": 1.3486
   }
  }
 ],
 "projected_36_call_figures_from_POST_WRITE_BOUND_REPORT": {
  "round4-iter-1": 1127441,
  "round4-iter-2": 1196549,
  "round4-iter-3 (the binding recording)": 1452307,
  "livecost1-iter-1": 558945,
  "live-completion1-iter-1": 579120,
  "live-completion1-iter-2": 633893
 },
 "refused_exit_base_rate": {
  "extra_hoh_exit_refused_observations_total": 0,
  "billed_model_calls_censused": 329,
  "attempt_trajectories_censused": 11,
  "refusals_per_100_billed_calls": 0.0,
  "per_attempt": [
   {
    "iteration": 1,
    "attempt": "developer.attempt1",
    "billed_model_calls": 36,
    "total_tokens": 563813,
    "exit_status": "StepBudgetExceeded",
    "refused_exits": 0
   },
   {
    "iteration": 1,
    "attempt": "planner.attempt1",
    "billed_model_calls": 6,
    "total_tokens": 34481,
    "exit_status": "Submitted",
    "refused_exits": 0
   },
   {
    "iteration": 1,
    "attempt": "tester.attempt1",
    "billed_model_calls": 36,
    "total_tokens": 681729,
    "exit_status": "StepBudgetExceeded",
    "refused_exits": 0
   },
   {
    "iteration": 2,
    "attempt": "developer.attempt1",
    "billed_model_calls": 36,
    "total_tokens": 679401,
    "exit_status": "StepBudgetExceeded",
    "refused_exits": 0
   },
   {
    "iteration": 2,
    "attempt": "planner.attempt1",
    "billed_model_calls": 9,
    "total_tokens": 73003,
    "exit_status": "Submitted",
    "refused_exits": 0
   },
   {
    "iteration": 2,
    "attempt": "tester.attempt1",
    "billed_model_calls": 44,
    "total_tokens": 955120,
    "exit_status": "StepBudgetExceeded",
    "refused_exits": 0
   },
   {
    "iteration": 2,
    "attempt": "tester.attempt2",
    "billed_model_calls": 36,
    "total_tokens": 608683,
    "exit_status": "StepBudgetExceeded",
    "refused_exits": 0
   },
   {
    "iteration": 3,
    "attempt": "developer.attempt1",
    "billed_model_calls": 44,
    "total_tokens": 854890,
    "exit_status": "StepBudgetExceeded",
    "refused_exits": 0
   },
   {
    "iteration": 3,
    "attempt": "planner.attempt1",
    "billed_model_calls": 10,
    "total_tokens": 81699,
    "exit_status": "Submitted",
    "refused_exits": 0
   },
   {
    "iteration": 3,
    "attempt": "tester.attempt1",
    "billed_model_calls": 36,
    "total_tokens": 507594,
    "exit_status": "StepBudgetExceeded",
    "refused_exits": 0
   },
   {
    "iteration": 3,
    "attempt": "tester.attempt2",
    "billed_model_calls": 36,
    "total_tokens": 668586,
    "exit_status": "StepBudgetExceeded",
    "refused_exits": 0
   }
  ],
  "reading": "zero refusals anywhere: no role of this round asked to finish before writing, so the write guarantee fired zero times and its base rate is 0/329 in this round"
 },
 "artifact_validity_and_strength": {
  "1": {
   "ok": true,
   "artifact_valid": true,
   "artifact_gate": {
    "applicable": true,
    "launchable": true,
    "reasons": []
   },
   "first_battery_pass_launchable": true,
   "battery_passes_run": 1,
   "first_battery_pass_failing_steps": [
    "e3_win_flag",
    "e3_win_position"
   ],
   "repair_retry_used": false,
   "wrap_up_retry_used": false,
   "wrap_up_retry_reason": "not_triggered",
   "developer_attempt2_exists": false,
   "surfaces": {
    "total": 19,
    "verified": 14,
    "gap": 1,
    "unobservable": 4
   },
   "gap_ids": [
    "P3"
   ],
   "unobservable_ids": [
    "C5",
    "C6",
    "Q-scale",
    "Q-not-required"
   ],
   "evidence_diff": {
    "added": [],
    "modified": [
     "src/game.rs"
    ],
    "removed": []
   },
   "write_failures": [],
   "out_of_tree_writes": []
  },
  "2": {
   "ok": true,
   "artifact_valid": true,
   "artifact_gate": {
    "applicable": true,
    "launchable": true,
    "reasons": []
   },
   "first_battery_pass_launchable": true,
   "battery_passes_run": 1,
   "first_battery_pass_failing_steps": [],
   "repair_retry_used": false,
   "wrap_up_retry_used": false,
   "wrap_up_retry_reason": "not_triggered",
   "developer_attempt2_exists": false,
   "surfaces": {
    "total": 19,
    "verified": 15,
    "gap": 0,
    "unobservable": 4
   },
   "gap_ids": [],
   "unobservable_ids": [
    "C5",
    "C6",
    "Q-scale",
    "Q-not-required"
   ],
   "evidence_diff": {
    "added": [],
    "modified": [
     "src/game.rs"
    ],
    "removed": []
   },
   "write_failures": [],
   "out_of_tree_writes": []
  },
  "3": {
   "ok": true,
   "artifact_valid": true,
   "artifact_gate": {
    "applicable": true,
    "launchable": true,
    "reasons": []
   },
   "first_battery_pass_launchable": true,
   "battery_passes_run": 1,
   "first_battery_pass_failing_steps": [],
   "repair_retry_used": false,
   "wrap_up_retry_used": false,
   "wrap_up_retry_reason": "not_triggered",
   "developer_attempt2_exists": false,
   "surfaces": {
    "total": 19,
    "verified": 15,
    "gap": 0,
    "unobservable": 4
   },
   "gap_ids": [],
   "unobservable_ids": [
    "C5",
    "C6",
    "Q-scale",
    "Q-not-required"
   ],
   "evidence_diff": {
    "added": [
     "ok"
    ],
    "modified": [],
    "removed": []
   },
   "write_failures": [],
   "out_of_tree_writes": []
  }
 },
 "wrap_up_retry": {
  "developer_attempt2_exists_in_any_iteration": false,
  "repair_retry_used_any_iteration": false,
  "wrap_up_retry_used_any_iteration": false,
  "wrap_up_retry_reason_any_iteration": "not_triggered",
  "added_developer_cost": 0,
  "tester_retries": {
   "iter-2": {
    "tester.attempt1_calls": 44,
    "tester.attempt1_artifact_valid": false,
    "tester.attempt2_calls": 36,
    "tester.attempt2_tokens": 608683
   },
   "iter-3": {
    "tester.attempt1_calls": 36,
    "tester.attempt1_artifact_valid": false,
    "tester.attempt2_calls": 36,
    "tester.attempt2_tokens": 668586
   },
   "added_tester_cost_tokens": 1277269,
   "note": "these are Tester retries, not the Developer wrap-up retry the projections were worried about"
  }
 },
 "shell_side_write_the_counted_detector_missed": {
  "iteration": 3,
  "counted_hoh_write_path_observations_in_the_developer_call": 0,
  "what_appeared_on_disk": {
   "path": "E:\\live3\\project\\ok",
   "bytes": 664,
   "mtime_local": "11:36",
   "first_line": "battery.json -=true"
  },
  "command_issued_at_call_36": "powershell -NoProfile -Command \"Get-ChildItem .hoh\\deterministic\\*.json | ForEach-Object { ...; \\\"$($_.Name) -> ok=$ok\\\" }\"",
  "controlled_reproduction_outside_the_repository": {
   "directory": "E:\\live3\\shape-test",
   "command": "the same command shape",
   "literal_exit_code": 0,
   "stdout": "",
   "file_created": "ok",
   "file_bytes": 21,
   "file_content": "battery.json -=true",
   "reading": "the unescaped `->` inside the PowerShell one-liner is parsed by cmd.exe as a redirection to a file literally named `ok`; the same accident created E:\\live3\\project\\ok in the live round"
  },
  "consequence": "the round's evidence_diff for iteration 3 is added:['ok'], modified:[] — the NoEngineeringWrite gate was satisfied by that accident, and the post-write bound never engaged, so the call kept the 44-call unwritten allowance (risk R3, materialised)"
 },
 "identity": {
  "surviving_launch": {
   "nonce": "a8f82206-420c-4826-aa88-3927ffabd70e",
   "answered_nonce": "a8f82206-420c-4826-aa88-3927ffabd70e",
   "spawned_pid": 58160,
   "answering_pid": 58160,
   "listening_pid": 58160,
   "verified": true,
   "launch_image": "runs\\bevy-postwrite1\\launch-image\\5678469d-def8-498d-9057-d3336facb60c\\hof_game.exe",
   "built_binary": "D:\\hof-live-run\\hof-bevy-shared-target\\debug\\hof_game.exe",
   "built_sha256": "aba49a5a509053fb15738049106b23216cc431254c1d00fe51d76f3f1a4c3214",
   "executed_sha256": "aba49a5a509053fb15738049106b23216cc431254c1d00fe51d76f3f1a4c3214"
  },
  "checks": {
   "ledger_nonce_equals_answered_nonce": true,
   "spawned_pid_equals_answering_pid": true,
   "listening_pid_equals_spawned_pid": true,
   "verified": true
  },
  "ledger_line_count": 7,
  "ledger": [
   {
    "line": 1,
    "pid": 29148,
    "nonce": "52cd7119-9257-4c51-add9-a3c82de7b119",
    "launched_at_seconds": 1791255394,
    "launch_image": "runs\\bevy-postwrite1\\launch-image\\66da7e4c-41da-400b-b27d-a4ce9e751fe7\\hof_game.exe"
   },
   {
    "line": 2,
    "pid": 20716,
    "nonce": "4327b1ae-dae6-4947-82b6-80111df8d1b4",
    "launched_at_seconds": 1791255940,
    "launch_image": "runs\\bevy-postwrite1\\launch-image\\e129c5d8-979f-418a-9d4b-6d32f4e77065\\hof_game.exe"
   },
   {
    "line": 3,
    "pid": 38264,
    "nonce": "f4432f37-1aec-4903-9c25-27364314a39a",
    "launched_at_seconds": 1791255958,
    "launch_image": "runs\\bevy-postwrite1\\launch-image\\d9691959-052a-4011-943d-402e20b1a453\\hof_game.exe"
   },
   {
    "line": 4,
    "pid": 54728,
    "nonce": "5ac2c20e-c4d5-4c7f-a532-eb6df6719d97",
    "launched_at_seconds": 1791256930,
    "launch_image": "runs\\bevy-postwrite1\\launch-image\\fbb6ad44-b426-4356-8a42-1911a63ae0ff\\hof_game.exe"
   },
   {
    "line": 5,
    "pid": 48944,
    "nonce": "31b287c3-a662-4dfc-a13d-1b10f1ab5e22",
    "launched_at_seconds": 1791256948,
    "launch_image": "runs\\bevy-postwrite1\\launch-image\\cb6cb323-640c-433b-8527-60707d8a9949\\hof_game.exe"
   },
   {
    "line": 6,
    "pid": 58160,
    "nonce": "a8f82206-420c-4826-aa88-3927ffabd70e",
    "launched_at_seconds": 1791257845,
    "launch_image": "runs\\bevy-postwrite1\\launch-image\\5678469d-def8-498d-9057-d3336facb60c\\hof_game.exe"
   },
   {
    "line": 7,
    "pid": 49068,
    "nonce": "b730718f-dd2b-437d-bd0c-188e869c8ce4",
    "launched_at_seconds": 1791257863,
    "launch_image": "runs\\bevy-postwrite1\\launch-image\\9620342e-ea8e-419b-ac2c-195f80010df0\\hof_game.exe"
   }
  ],
  "poller_snapshots": [
   {
    "file": "launch.148.json",
    "nonce": "5ac2c20e-c4d5-4c7f-a532-eb6df6719d97",
    "answered_nonce": "5ac2c20e-c4d5-4c7f-a532-eb6df6719d97",
    "spawned_pid": 54728,
    "answering_pid": 54728,
    "listening_pid": 54728,
    "verified": true
   },
   {
    "file": "launch.233.json",
    "nonce": "a8f82206-420c-4826-aa88-3927ffabd70e",
    "answered_nonce": "a8f82206-420c-4826-aa88-3927ffabd70e",
    "spawned_pid": 58160,
    "answering_pid": 58160,
    "listening_pid": 58160,
    "verified": true
   },
   {
    "file": "launch.56.json",
    "nonce": "4327b1ae-dae6-4947-82b6-80111df8d1b4",
    "answered_nonce": "4327b1ae-dae6-4947-82b6-80111df8d1b4",
    "spawned_pid": 20716,
    "answering_pid": 20716,
    "listening_pid": 20716,
    "verified": true
   }
  ],
  "my_own_OS_reading_during_the_round": {
   "what": "netstat -ano and tasklist for 15702/15703 and hof_game.exe, taken every 10 s for the whole round",
   "poll_lines": 296,
   "lines_naming_a_listener": 289,
   "distinct_listener_pids": [
    20716,
    29148,
    38264,
    48944,
    49068,
    54728,
    58160
   ],
   "lines_naming_more_than_one_listener": 0,
   "ledger_pid_set_equals_observed_listener_pid_set": true,
   "first_listener_line": "2026-10-06T10:56:41+0800 netstat=[ TCP 127.0.0.1:15702 0.0.0.0:0 LISTENING 29148; TCP 127.0.0.1:56284 127.0.0.1:15702 TIME_WAIT 0;] hof_game=[hof_game.exe 29148 Console 1 108,076 K;]",
   "last_listener_line": "2026-10-06T11:49:00+0800 netstat=[ TCP 127.0.0.1:15702 0.0.0.0:0 LISTENING 49068;] hof_game=[hof_game.exe 49068 Console 1 109,384 K;]"
  },
  "round_stop": {
   "called_at_seconds": 1791258546,
   "ledger": "runs\\bevy-postwrite1\\launch-ledger.jsonl",
   "ledger_lines_at_sweep": 7,
   "evidence": "runs\\bevy-postwrite1\\round-stop.json",
   "recorded": [
    29148,
    20716,
    38264,
    54728,
    48944,
    58160,
    49068
   ],
   "reaped": [],
   "still_alive": [],
   "endpoint_holder": null,
   "failure": null
  },
  "after_the_round": {
   "netstat_15702_15703": "no line",
   "hof_game_processes": "none",
   "hoh_processes": "none"
  }
 },
 "coverage": {
  "frozen_registry_surfaces": 19,
  "per_iteration": {
   "1": {
    "verified": 14,
    "gap": 1,
    "unobservable": 4,
    "gap_ids": [
     "P3"
    ],
    "unobservable_ids": [
     "C5",
     "C6",
     "Q-scale",
     "Q-not-required"
    ],
    "failing_battery_steps": [
     "e3_win_flag",
     "e3_win_position"
    ]
   },
   "2": {
    "verified": 15,
    "gap": 0,
    "unobservable": 4,
    "gap_ids": [],
    "unobservable_ids": [
     "C5",
     "C6",
     "Q-scale",
     "Q-not-required"
    ]
   },
   "3": {
    "verified": 15,
    "gap": 0,
    "unobservable": 4,
    "gap_ids": [],
    "unobservable_ids": [
     "C5",
     "C6",
     "Q-scale",
     "Q-not-required"
    ],
    "note": "scored the unchanged iteration-2 game.rs, since iteration 3 changed nothing"
   }
  },
  "two_formerly_open_items": {
   "Q-startup": {
    "status": "verified",
    "evidence": "battery step(s): play_scene_ready, e3_process_liveness"
   },
   "B2.1": {
    "status": "verified",
    "evidence": "battery step(s): e3_process_liveness"
   },
   "raw_persisted_liveness_observations": {
    "iter-1": {
     "first_frame": 707,
     "requested": 8,
     "second_frame": 717
    },
    "iter-2": {
     "first_frame": 718,
     "requested": 8,
     "second_frame": 728
    },
    "iter-3": {
     "first_frame": 708,
     "requested": 8,
     "second_frame": 718
    }
   },
   "reading": "still decided by a real persisted observation of the game's own FrameCounter advancing"
  }
 },
 "gate": {
  "command": "cargo test --offline",
  "literal_exit_code": 0,
  "passed": 824,
  "failed": 0,
  "ignored": 6,
  "listed": 830,
  "test_result_lines": 62,
  "compiler_warning_lines": 0,
  "list_command": "cargo test --offline -- --list",
  "list_literal_exit_code": 0,
  "list_count": 830,
  "list_ignored_command": "cargo test --offline -- --list --ignored",
  "list_ignored_literal_exit_code": 0,
  "list_ignored_count": 6,
  "fmt_command": "cargo fmt --all --check",
  "fmt_literal_exit_code": 0,
  "build_dir": "E:/pwb-target (own dir)",
  "baseline": {
   "passed": 824,
   "failed": 0,
   "ignored": 6,
   "listed": 830
  },
  "matches_baseline": true
 },
 "disk": {
  "free_before": {
   "C": "34.17 GB",
   "D": "53.82 GB",
   "E": "518.59 GB",
   "F": "8.30 GB",
   "G": "347.63 GB"
  },
  "free_after_the_round_before_the_gate": {
   "C": "34.12 GB",
   "D": "53.76 GB",
   "E": "518.51 GB",
   "F": "7.07 GB",
   "G": "347.63 GB"
  },
  "where_it_was_spent": "F: lost 1.23 GB to the gitignored run trees (runs/bevy-postwrite1 1.3 GB, runs/postwrite1 12 MB); the games and every build tree lived on E:/D:, and F:'s repository target/ was not used",
  "deletions": "none — nothing this experiment created had to be removed, so no removal was performed at all"
 },
 "constraints": {
  "round_run_from_outside_the_repository_project": true,
  "keys_from_outside_the_repository_only": true,
  "key_read_copied_printed_or_written_by_this_experiment": false,
  "rm_rf_or_wildcard_deletion_used": false,
  "path_constructed_from_an_unexpanded_variable": false,
  "git_checkout_double_dash_used": false,
  "src_tests_evidence_registry_battery_gitattributes_or_frozen_document_modified": false,
  "committed_or_pushed": false,
  "decisions_md_appended": false,
  "helper_scripts_location": "E:\\live3\\ (outside the repository; every script landed through a file write, never multi-line Python on a shell command line)",
  "repository_paths_written": [
   ".spec/bevy/LIVE-POST-WRITE-BOUND.md (this report)",
   "runs/postwrite1/** and runs/bevy-postwrite1/** (gitignored harness evidence, kept)"
  ],
  "working_tree_after": "no tracked file modified; the only untracked path is this report"
 },
 "measured_vs_inferred": {
  "measured": [
   "every call count, token figure, write observation, refusal count and exit status is read out of runs/postwrite1/iter-*/traj/*.attempt1.json and the runtime's own runs/postwrite1/iter-*/usage.json and result.json",
   "the bound's engagement is the call's own billed model-call count and its own runtime exit_status",
   "the identity values are read out of runs/bevy-postwrite1/launch.json, its append-only ledger and my own netstat/tasklist readings taken every 10 s while the round ran",
   "the coverage figures are read out of runs/postwrite1/iter-*/result.json (battery_passes[0].surfaces) and the persisted raw liveness observations",
   "the `ok` file's existence, size and content, and the controlled reproduction of the command that creates it, are measurements taken outside the repository",
   "the gate is this repository's own cargo test --offline, run in this experiment's own build directory"
  ],
  "inferred": [
   "that iteration 3's Developer intended no write and that the `ok` file is what carried the round past the NoEngineeringWrite gate: the file, its content, the command and the zero counted writes are measured, but the model's intent is not",
   "that the bound, rather than some other behavioural change, is what ended iterations 1 and 2 at 36 calls: the end is measured (billed calls and StepBudgetExceeded) and the config value is read, but one round cannot separate the bound from the model's own choice",
   "plan conformance of the delivered artifact: A3's src/game.rs is byte-identical to A2's and the battery scores 15/0/4, but whether the plans were fully implemented is not something this measurement decides",
   "any effect on a second provider, model or project shape; and there was no refusal to quote"
  ]
 },
 "single_most_important_thing": "The criterion is met live for the first time — 563,813 / 679,401 / 854,890 tokens, 0.38x / 0.45x / 0.57x — and the bound is what did it in iterations 1 and 2 (36 billed calls, StepBudgetExceeded, 62.4 % and 54.7 % headroom) without weakening the delivered game (15 verified / 0 gap / 4 unobservable, all 12 battery steps green on the first pass, artifact gate launchable, no Developer retry). But the bound's precondition failed in iteration 3: the Developer emitted no counted HOH_WRITE_FILE write at all, kept the 44-call unwritten allowance, and the round passed the NoEngineeringWrite gate only because an unescaped `->` in a PowerShell one-liner made cmd.exe create a stray file named `ok`. The next decision must make the counted-write detector agree with the round's tree-hash measurement, otherwise the bound is optional in exactly the case where it matters."
}
```

# LIVE-POST-WRITE-BOUND — one real round under the post-write call bound

The machine-readable block above is `json.dumps(..., indent=1, ensure_ascii=False)` output written by
`E:/live3/write_report.py` and then **parsed back out of this written file**; the parse is the last thing
the generator does and it fails unless the block round-trips. Every helper script lives outside the
repository at `E:/live3/`. The run tree is kept at `runs/postwrite1/` and `runs/bevy-postwrite1/`.

**Measured** below means read out of the round's own trajectories, `usage.json`, `result.json`, its
launch record and ledger, or a reading I took myself while it ran. **Inferred** means it is not — every
such statement is labelled.

## 1. What was run, and how

| step | command | literal exit code |
|---|---|---|
| build | `cargo build --offline --bin hoh` (target dir `E:/pwb-target`) | **0** |
| init | `hoh init --adapter bevy --project E:\live3\project` | **0** |
| run | `hoh run --adapter bevy --project E:\live3\project --run-id postwrite1 --env-from-secret D:\hof-live\secret.env` | **0** |

Headless, model `deepseek-v4.1-flash`, binary built from this tree at HEAD `15c7f7e`, whose `src/**` is
byte-identical to the post-write-bound implementation `e900262` (`15c7f7e` adds only the acceptance
document). The project was created empty **outside** the repository; the key came from the same file
outside the repository the previous live rounds used and was **never read, copied, printed or written**
by this experiment. The round ran `2026-10-06T10:56:09+0800` → `2026-10-06T11:49:09+0800` =
**53.00 minutes**.

Disk, checked before and after: **F: 8.30 GB → 7.07 GB free** (the 1.23 GB is the gitignored run tree —
`runs/bevy-postwrite1` 1.3 GB, `runs/postwrite1` 12 MB — which is kept); D: 53.82 → 53.76; E: 518.59 →
518.51; C: 34.17 → 34.12; G: unchanged. The games, the warm Bevy cache
(`D:\hof-live-run\hof-bevy-shared-target`) and the hoh build tree all lived away from F:.

## 2. ★ The answers only a live round could settle

| iteration | counted `HOH_WRITE_FILE` project write? | first write call | counted project writes | billed model calls | exit status | **post-write bound engaged?** | total tokens | ratio | margin under 1,500,000 |
|---|---|---|---|---|---|---|---|---|---|
| 1 | **yes** | **call 6** | calls 6, 29 | **36** | `StepBudgetExceeded` | **yes** | **563,813** | **0.376x** | **936,187 (62.4 %)** |
| 2 | **yes** | **call 8** | call 8 | **36** | `StepBudgetExceeded` | **yes** | **679,401** | **0.453x** | **820,599 (54.7 %)** |
| 3 | **no — none at all** | — | — | **44** | `StepBudgetExceeded` | **no** | **854,890** | **0.570x** | 645,110 (43.0 %) |

**The bound engaged.** In iterations 1 and 2 the call's own billed model-call count is exactly **36** —
35 allowed, the 36th billed and refused — and its own runtime exit status is `StepBudgetExceeded`. The
round's config is `step_limit: 150`, `wrap_up_steps: 25`, `steps_per_artifact: 8`,
`post_write_step_limit: 35`.

**In iteration 3 it did not engage.** That call made **44** billed calls — the *unwritten* allowance
(`25 + max(150/8, 1) = 43`, billed 44) — because it carried **zero** counted `HOH_WRITE_FILE` writes of
any kind, project or scratch. This is risk **R3** ("the lever only works if the live model emits a counted
`HOH_WRITE_FILE` directive write") materialising in the first live round that could show it.

**Cost against the projected 36-call figure.**

| this call | measured | against the projections at 36 billed calls |
|---|---|---|
| iter-1 (36 calls) | **563,813** | 0.973x live-completion1-iter-1 (579,120); 0.889x live-completion1-iter-2 (633,893); 1.009x livecost1-iter-1 (558,945); **0.388x** the binding recording round4-iter-3 (1,452,307) |
| iter-2 (36 calls) | **679,401** | 1.173x / 1.072x / 1.216x the three live 36-call projections; **0.468x** the binding recording |
| iter-3 (44 calls, bound never applied) | **854,890** | not comparable — the bound never bit; 0.589x the binding recording's 36-call figure |

**The single most important number.** On the two calls the bound actually cut, the margin against
1,500,000 is **936,187 tokens (62.4 %)** and **820,599 tokens (54.7 %)** — twelve to nineteen times the
3.2 % headroom the binding *recording* left. The round's tightest Developer call is iteration 3's
**854,890 (43.0 % headroom)**, and that is precisely the one the bound did **not** cut.

**The criterion is met live for the first time.** Three Developer calls, 0.376x / 0.453x / 0.570x, none
over the bar; `write_failures` is empty in all three iterations, so no call was flagged by the token half
of the budget either.

## 3. Did the write guarantee fire? And what did the counted detector miss?

**`extra.hoh_exit_refused`: zero, everywhere.** Across all **11** attempt trajectories and **329** billed
model calls of this round (three roles, three iterations, plus two Tester retries) there is **not one**
refused exit; **0 refusals / 329 billed calls = 0.0 per 100**. No role ever asked to finish before
writing, so the write guarantee never had to fire. The previous acceptance noted the corpus could not
supply this base rate; this round supplies it for its own shape only — zero refusals is an absence, and
one round cannot turn it into a rate. *(Measured.)*

**The counted detector missed one shell-side project write — and it is what decided iteration 3.**
Iteration 3's Developer call contains **zero** `extra.hoh_write_path` observations, yet a **664-byte file
named `ok` appeared in the project root at 11:36** whose 26 lines read `battery.json -=true`,
`e3_coin_counter.json -=true`, `e3_grounded.json -=true`, … `record-11.json -=n/a`.

The cause is measured, not inferred. At call 36 the role ran

```
powershell -NoProfile -Command "Get-ChildItem .hoh\deterministic\*.json | ForEach-Object { ...; \"$($_.Name) -> ok=$ok\" }"
```

and I reproduced that exact command shape in a directory **outside** the repository (`E:\live3\shape-test`,
one input file): cmd.exe parsed the unescaped `->` as a **redirection to a file literally named `ok`**,
exited 0 with empty stdout, and wrote `battery.json -=true` (21 bytes) into `ok`. The live round's file is
the same accident with 26 input files.

The consequence is direct and measured: iteration 3's `evidence_diff` is
`{"added": ["ok"], "modified": [], "removed": []}`, and version A3's `src/game.rs` is byte-identical to
A2's (20,619 bytes, same hash). So **iteration 3's `NoEngineeringWrite` gate was satisfied by an
accidental stray file, not by an engineering change** — and the same absence of a counted write is why the
bound never engaged. The round's third iteration was a read-only grind that got lucky.

## 4. ★ Did the artifact survive the cut? Is the round a weaker game?

| iteration | developer `artifact_valid` | artifact gate | first battery pass launchable | failing steps on that first pass | repair retry | developer attempt 2 | surfaces |
|---|---|---|---|---|---|---|---|
| 1 | true | `launchable: true` | **true** | **`e3_win_flag`, `e3_win_position`** | false | **none** | **14 verified / 1 gap / 4 unobservable** (gap `P3`) |
| 2 | true | `launchable: true` | **true** | none | false | **none** | 15 / 0 / 4 |
| 3 | true | `launchable: true` | **true** | none | false | **none** | 15 / 0 / 4 (re-scoring iteration 2's `game.rs`) |

**The Developer wrap-up retry never fired.** There is no `developer.attempt2.json` anywhere under
`runs/postwrite1/iter-*/traj/`; `wrap_up_retry_used` is `false` with reason `not_triggered` in all three
iterations and `repair_retry_used` is `false` everywhere. The **+0.38 M–0.97 M** second-call cost the
projections could not include was therefore **not paid**. *(Measured.)* What was paid is a Tester-side
retry the projections also did not include: the same bound cut the Tester in every iteration, and in
iterations 2 and 3 its attempt-1 artifact was invalid, so `tester.attempt2` ran — 36 calls / 608,683
tokens in iteration 2 and 36 calls / 668,586 in iteration 3, **+1,277,269 tokens** in all. That is Tester
cost, not the Developer cost the criterion measures, but it is a real addition to the round.

**The artifact survived the cut; the delivered game is not weaker — but the bound did cost iteration 1
real work, and iteration 3 is not a producing iteration at all.** Every gate is launchable, every first
battery pass is launchable, all three `artifact_valid` are true, and the delivered final version (A3)
scores **15 verified / 0 gap / 4 unobservable** with all 12 battery steps green — the same figure as the
completed iterations of the two previous live rounds, and grown from the 4,502-byte scaffold to 15,538
(A1) then 20,619 bytes (A2). But that is the *end state*, and the per-iteration reading is not uniform:

* Cutting iteration 1 at 36 calls left two real semantic steps failing (`e3_win_flag`, `e3_win_position`)
  — a **`P3` gap** that no completed live iteration had before — and it took **iteration 2** to close it.
  The bound shortened iteration 1's work. *(Measured: the first battery pass's own step list.)*
* Iteration 3 delivered **A3 = A2's `game.rs` + the accidental `ok` file**. Its 854,890-token Developer
  call, its battery pass and its 15/0/4 coverage are a re-scoring of iteration 2's artifact;
  `src/game.rs` is byte-identical. *(Measured.)*

So the round is not a weaker *delivered* game, and the criterion was met without one — but one of its
three iterations contributed no engineering change and the round's success on that iteration rests on a
redirection accident. I will not call that a win for the pipeline.

## 5. Is the round real and trustworthy?

| reading | value |
|---|---|
| surviving launch nonce (generated before the spawn, carried only in the child's environment) | `a8f82206-420c-4826-aa88-3927ffabd70e` |
| `answered_nonce` (served back over BRP when readiness read `ProcessNonce`) | `a8f82206-420c-4826-aa88-3927ffabd70e` |
| `spawned_pid` / `answering_pid` / `listening_pid` | `58160` / `58160` / `58160` |
| `verified` | `true` |
| the ledger line carrying that nonce, pid and launch image | **line 6** of `runs/bevy-postwrite1/launch-ledger.jsonl`, `launched_at_seconds 1791257845`, image `5678469d-def8-498d-9057-d3336facb60c` |
| built vs executed binary sha256 | both `aba49a5a509053fb15738049106b23216cc431254c1d00fe51d76f3f1a4c3214`, `executed_matches_built: true` |

**My own OS reading, taken every 10 s for the whole round** (`netstat -ano` on 15702/15703 and `tasklist`
for `hof_game.exe`): **296 readings, 289 of them naming exactly one `LISTENING` socket on 15702, and
never once naming two.** The set of pids that ever held that listener —
`{20716, 29148, 38264, 48944, 49068, 54728, 58160}` — is **exactly** the ledger's pid set (7 lines, 7
distinct nonces, pids and launch-image UUIDs), and every one of them was named `hof_game.exe`. First
listener line `2026-10-06T10:56:41+0800 … LISTENING 29148`; last `2026-10-06T11:49:00+0800 …
LISTENING 49068`.

The launch record is overwritten per launch, so my poller snapshotted it three times before each
overwrite; every snapshot shows the same three-way agreement:

| snapshot | nonce = answered_nonce | spawned = answering = listening | verified | ledger line |
|---|---|---|---|---|
| `launch.56.json` (11:05:56) | `4327b1ae-dae6-4947-82b6-80111df8d1b4` | `20716` / `20716` / `20716` | true | line 2 |
| `launch.148.json` (11:22:27) | `5ac2c20e-c4d5-4c7f-a532-eb6df6719d97` | `54728` / `54728` / `54728` | true | line 4 |
| `launch.233.json` (11:37:42) | `a8f82206-420c-4826-aa88-3927ffabd70e` | `58160` / `58160` / `58160` | true | line 6 |

**Nothing survives the round.** `round-stop.json` records all seven pids
`[29148, 20716, 38264, 54728, 48944, 58160, 49068]`, `reaped: []`, `still_alive: []`,
`endpoint_holder: null`, `failure: null`; after the round, `netstat` returns **no line** for 15702 or
15703, `tasklist` shows **no** `hof_game.exe` and **no** `hoh.exe`. The seven ledger launches are the
opening session plus a pair per battery pass; the launch `launch.json` names (line 6, pid 58160) is the
iteration-3 battery-pass launch, and the last process observed (line 7, pid 49068) is the round's final
session.

## 6. Coverage

| iteration | frozen surfaces | gap | unobservable | `Q-startup` / `B2.1` |
|---|---|---|---|---|
| 1 | **14 verified / 1 gap / 4 unobservable of 19** | 1 (`P3`, from `e3_win_flag` and `e3_win_position`) | `C5`, `C6`, `Q-scale`, `Q-not-required` | both `verified` |
| 2 | **15 verified / 0 gap / 4 unobservable of 19** | 0 | same four | both `verified` |
| 3 | **15 verified / 0 gap / 4 unobservable of 19** (iteration 2's artifact) | 0 | same four | both `verified` |

The two formerly open items are **still decided by a real persisted observation** of the game's own
`FrameCounter` advancing, read over BRP from the process this round launched: iteration 1 **707 → 717**,
iteration 2 **718 → 728**, iteration 3 **708 → 718**, each for a requested 8 frames
(`raw/e3_process_liveness.json`, `criterion: e3_process_liveness`, `observed: true`, `failure: null`).
The iteration-1 `P3` gap is the one new coverage fact of this round: it is exactly the two win-condition
steps, and iteration 2 closed them.

## 7. Exit code, wall clock, and is this the honest successor?

`hoh run` returned literal **exit 0** after **53.00 minutes**, with all three iterations `ok: true`, no
`NoEngineeringWrite`, no warning of a write failure, `write_failures: []` everywhere and
`out_of_tree_writes: []` everywhere. The previous live round (`completion1`) exited **2** after 81.58
minutes with its third iteration failing to write and no artifact for it.

**Yes, in outcome — and no, in the shape that mattered.** Three iterations completed and the round exited
0, which the previous round did not achieve. But the previous round's pathology was "the third iteration's
Developer wrote nothing inside the project", and this round **reproduces that pathology exactly**: the
iteration-3 Developer again made zero counted project writes, and again only the tree-change gate stood
between it and `NoEngineeringWrite`. What changed is that the gate was satisfied this time — by an
accidental `ok` file. So this round is the honest successor of the previous one in its exit code, and a
continuation of its third-iteration defect in its substance.

## 8. The gate, the disk, the constraints

`cargo test --offline` in this experiment's own build directory `E:/pwb-target`: literal exit code
**0**, **824 passed / 0 failed / 6 ignored / 830 listed** over 62 `test result:` lines, with **0**
compiler-warning lines and 0 error lines — exactly the baseline 824 / 0 / 6 / 830.
`cargo test --offline -- --list` returns **830** (exit 0), `--list --ignored` returns **6** (exit 0), and
`cargo fmt --all --check` exits **0** with 0 bytes on stdout and stderr.

**Nothing was deleted** — nothing this experiment created needed removing, so there was no `rm -rf`, no
wildcard deletion and no removal of any kind. No path was constructed from an unexpanded variable; no
`git checkout --`; nothing under `src/**`, `tests/**`, `evidence/**`, the registry, the battery,
`.gitattributes` or any frozen document was touched; nothing was committed or pushed. The only repository
paths written are this report and the gitignored run trees. **I appended nothing to `DECISIONS.md`**: the
decision this finding drives — how to make the counted-write detector agree with the round's tree-hash
measurement before tuning 35 again — belongs to the dispatcher, and this report carries the evidence it
needs. All helper scripts live at `E:/live3/` and every one of them landed through a file write.

## 9. What is measured, what is inferred, and what remains open

**Measured:** every call count, token figure, write observation, refusal count and exit status (the
round's own trajectories, `usage.json`, `result.json`); the bound's engagement (the call's own billed
count and its own runtime exit status); the identity values (launch.json, the append-only ledger, and my
own 10-second netstat/tasklist readings); the coverage figures and the raw liveness frames; the existence,
size and content of `E:\live3\project\ok` and the controlled reproduction of the command that creates it;
and the gate.

**Inferred:** (a) that the `ok` file is what carried iteration 3 past the `NoEngineeringWrite` gate — the
file, its content, the command and the zero counted writes are measured, but the model's intent is not;
(b) that the bound, rather than some other behavioural change, is what ended iterations 1 and 2 at 36
calls — the ending is measured and the config value is read, but one round cannot separate the bound from
the model's own choice; (c) plan conformance of the delivered artifact — it grew, scored 15/0/4 and
passed every battery step, but "the plans were fully implemented" is not something this measurement
decides; (d) any effect on a second provider, model or project shape.

**What remains open, in the terms the acceptance set:**

* **R1 (thin margin) is now measured to be a projection artefact, not a live constraint.** The live
  bound-cut calls cleared the bar by 62.4 % and 54.7 %, not 3.2 %. But the *tightest live call* was the
  one the bound did not cut, so the recorded 1,452,307 at 36 calls remains the only 36-call figure that
  has ever come close to 1.5 M.
* **R2 (the wrap-up retry) did not fire** for the Developer in any iteration; it remains unmeasured for a
  bound-cut artifact that is not launchable. It did fire in substance for the **Tester** (two retries,
  +1.28 M tokens).
* **R3 (efficacy requires a counted directive write) is confirmed live, twice over**: iteration 3's
  Developer emitted none, kept the 44-call unwritten allowance, and the round still passed only because of
  an accidental shell-side file. Until the detector and the round's tree-hash gate agree on what a
  project write is, the bound is optional in exactly the case where it matters.
* **R4 (the instruction change is behavioural)** is still unmeasured; the calls did end at 36, which is
  consistent with the bound biting, but nothing here separates that from the model's own behaviour.

The single most important thing for the next decision-maker: **the lever works when the write is counted,
and the criterion is met for the first time — 0.376x / 0.453x / 0.570x, with the two bound-cut calls at
62.4 % and 54.7 % headroom and no Developer retry, no unlaunchable artifact and no coverage loss in the
delivered game. The one live failure is the precondition: a Developer that changes the project through
the shell is invisible to the counted detector, escapes the bound, and can satisfy the round's tree-hash
gate with an accident (a stray `ok` file). Close that gap before tuning 35 further.**
