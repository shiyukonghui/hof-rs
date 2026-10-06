```json
{
 "schema": "hof-rs / bevy live completion-protocol measurement — one real round from outside the repository after the format-error retry fix",
 "produced_at": "2026-10-06",
 "branch": "bevy-core",
 "head_under_test": "cbb94c0 (its code is byte-identical to the retry-fix commit 9b74379; the only later commit is the acceptance document)",
 "binary": "D:/live2-target/debug/hoh.exe, built from this tree with `cargo build --offline --bin hoh`, exit 0",
 "kind": "one live round, three iterations requested, real model calls, real game process, real battery",
 "run_exit_codes": {
  "hoh_init": {
   "command": "hoh init --adapter bevy --project D:\\live2\\project",
   "literal_exit_code": 0
  },
  "hoh_run": {
   "command": "hoh run --adapter bevy --project D:\\live2\\project --run-id completion1 --env-from-secret D:\\hof-live\\secret.env",
   "literal_exit_code": 2,
   "stderr": "hoh: contract violation: NoEngineeringWrite (no_engineering_write)",
   "runs_dir_exit_code": "2",
   "runs_dir_process_exit_code": "2",
   "started_at_local": "2026-10-06T07:06:47+0800",
   "finished_at_local": "2026-10-06T08:28:22+0800",
   "wall_clock_minutes": 81.58
  },
  "outcome": "FAILED at iteration 3: the developer stage produced no write to a file inside the project, so the round ended with NoEngineeringWrite after 2 complete iterations and a third that produced no artifact"
 },
 "round": {
  "run_id": "completion1",
  "project": "D:\\live2\\project (created empty, outside the repository)",
  "run_tree_kept": "runs/completion1 and runs/bevy-completion1",
  "key_source": "D:\\hof-live\\secret.env, the same file outside the repository the previous live round used; never read, copied, printed or written by this experiment",
  "bevy_build_target": "D:\\hof-live-run\\hof-bevy-shared-target (a warm D: cache reused so F: was not filled)"
 },
 "criterion": {
  "tokens_per_developer_call": 1500000,
  "source": "config/hoh.yaml agent.artifact_write_budget_tokens",
  "met": false
 },
 "per_iteration_cost": {
  "iter-1": {
   "ok": true,
   "failed_role": null,
   "reason": "ok",
   "roles": {
    "planner": [
     {
      "role": "planner",
      "attempt": 1,
      "calls": 6,
      "prompt_tokens": 42397,
      "completion_tokens": 2035,
      "total_tokens": 44432,
      "duration_ms": 17806,
      "wall_clock_minutes": 0.297,
      "exit_status": "Submitted",
      "artifact_valid": true,
      "ratio_to_the_1500000_criterion": 0.0296
     }
    ],
    "developer": [
     {
      "role": "developer",
      "attempt": 1,
      "calls": 150,
      "prompt_tokens": 3414645,
      "completion_tokens": 112921,
      "total_tokens": 3527566,
      "duration_ms": 1239788,
      "wall_clock_minutes": 20.663,
      "exit_status": "LimitsExceeded",
      "artifact_valid": true,
      "ratio_to_the_1500000_criterion": 2.3517,
      "baselines_beside_it": {
       "round4-iter-1": {
        "calls": 69,
        "prompt_tokens": 2544563,
        "total_tokens": 2626195,
        "ratio_this_call_to_that_baseline_total": 1.3432,
        "ratio_this_call_to_that_baseline_prompt": 1.3419
       },
       "livecost1-iter-1": {
        "calls": 150,
        "prompt_tokens": 3537843,
        "total_tokens": 3651120,
        "ratio_this_call_to_that_baseline_total": 0.9662,
        "ratio_this_call_to_that_baseline_prompt": 0.9652
       }
      }
     }
    ],
    "tester": [
     {
      "role": "tester",
      "attempt": 1,
      "calls": 98,
      "prompt_tokens": 2310975,
      "completion_tokens": 35710,
      "total_tokens": 2346685,
      "duration_ms": 730115,
      "wall_clock_minutes": 12.169,
      "exit_status": "Submitted",
      "artifact_valid": true,
      "ratio_to_the_1500000_criterion": 1.5645
     }
    ]
   }
  },
  "iter-2": {
   "ok": true,
   "failed_role": null,
   "reason": "ok",
   "roles": {
    "planner": [
     {
      "role": "planner",
      "attempt": 1,
      "calls": 6,
      "prompt_tokens": 56179,
      "completion_tokens": 3386,
      "total_tokens": 59565,
      "duration_ms": 30933,
      "wall_clock_minutes": 0.516,
      "exit_status": "Submitted",
      "artifact_valid": true,
      "ratio_to_the_1500000_criterion": 0.0397
     }
    ],
    "developer": [
     {
      "role": "developer",
      "attempt": 1,
      "calls": 150,
      "prompt_tokens": 3820462,
      "completion_tokens": 118565,
      "total_tokens": 3939027,
      "duration_ms": 1667023,
      "wall_clock_minutes": 27.784,
      "exit_status": "LimitsExceeded",
      "artifact_valid": true,
      "ratio_to_the_1500000_criterion": 2.626,
      "baselines_beside_it": {
       "round4-iter-2": {
        "calls": 125,
        "prompt_tokens": 12765478,
        "total_tokens": 13091431,
        "ratio_this_call_to_that_baseline_total": 0.3009,
        "ratio_this_call_to_that_baseline_prompt": 0.2993
       },
       "livecost1-iter-1": {
        "calls": 150,
        "prompt_tokens": 3537843,
        "total_tokens": 3651120,
        "ratio_this_call_to_that_baseline_total": 1.0789,
        "ratio_this_call_to_that_baseline_prompt": 1.0799
       }
      }
     }
    ],
    "tester": [
     {
      "role": "tester",
      "attempt": 1,
      "calls": 150,
      "prompt_tokens": 3786462,
      "completion_tokens": 53465,
      "total_tokens": 3839927,
      "duration_ms": 744762,
      "wall_clock_minutes": 12.413,
      "exit_status": "LimitsExceeded",
      "artifact_valid": true,
      "ratio_to_the_1500000_criterion": 2.56
     }
    ]
   }
  },
  "iter-3": {
   "ok": false,
   "failed_role": "developer",
   "reason": "contract_violation",
   "roles": {
    "planner": [
     {
      "role": "planner",
      "attempt": 1,
      "calls": 6,
      "prompt_tokens": 43460,
      "completion_tokens": 2605,
      "total_tokens": 46065,
      "duration_ms": 23253,
      "wall_clock_minutes": 0.388,
      "exit_status": "Submitted",
      "artifact_valid": true,
      "ratio_to_the_1500000_criterion": 0.0307
     }
    ],
    "developer": [
     {
      "role": "developer",
      "attempt": 1,
      "calls": 44,
      "prompt_tokens": 789257,
      "completion_tokens": 13770,
      "total_tokens": 803027,
      "duration_ms": 349903,
      "wall_clock_minutes": 5.832,
      "exit_status": "StepBudgetExceeded",
      "artifact_valid": true,
      "ratio_to_the_1500000_criterion": 0.5354,
      "baselines_beside_it": {
       "round4-iter-3": {
        "calls": 102,
        "prompt_tokens": 5137090,
        "total_tokens": 5223211,
        "ratio_this_call_to_that_baseline_total": 0.1537,
        "ratio_this_call_to_that_baseline_prompt": 0.1536
       },
       "livecost1-iter-1": {
        "calls": 150,
        "prompt_tokens": 3537843,
        "total_tokens": 3651120,
        "ratio_this_call_to_that_baseline_total": 0.2199,
        "ratio_this_call_to_that_baseline_prompt": 0.2231
       }
      }
     }
    ]
   }
  }
 },
 "per_role_totals": {
  "planner": {
   "calls": 18,
   "prompt_tokens": 142036,
   "completion_tokens": 8026,
   "total_tokens": 150062,
   "duration_ms": 71992,
   "wall_clock_minutes": 1.2
  },
  "developer": {
   "calls": 344,
   "prompt_tokens": 8024364,
   "completion_tokens": 245256,
   "total_tokens": 8269620,
   "duration_ms": 3256714,
   "wall_clock_minutes": 54.279
  },
  "tester": {
   "calls": 248,
   "prompt_tokens": 6097437,
   "completion_tokens": 89175,
   "total_tokens": 6186612,
   "duration_ms": 1474877,
   "wall_clock_minutes": 24.581
  }
 },
 "retry_counts_before_and_after": {
  "developer_before": {
   "round4-iter-1": {
    "calls": 69,
    "retry_turns": 20,
    "retry_prompt_tokens": 876566,
    "first_declared_finish_call": 25,
    "declared_finish_shape": "prose-only reply, no tool call, rejected as a format error"
   },
   "round4-iter-2": {
    "calls": 125,
    "retry_turns": 10,
    "retry_prompt_tokens": 1486702,
    "first_declared_finish_call": 58,
    "declared_finish_shape": "prose-only reply, no tool call, rejected as a format error"
   },
   "round4-iter-3": {
    "calls": 102,
    "retry_turns": 8,
    "retry_prompt_tokens": 416910,
    "first_declared_finish_call": 30,
    "declared_finish_shape": "prose-only reply, no tool call, rejected as a format error"
   },
   "livecost1-iter-1": {
    "calls": 150,
    "retry_turns": 0,
    "retry_prompt_tokens": 0,
    "first_declared_finish_call": null,
    "declared_finish_shape": "prose-only reply, no tool call, rejected as a format error"
   }
  },
  "developer_after": {
   "iter-1": {
    "calls": 150,
    "retry_turns": 0,
    "retry_prompt_tokens": 0,
    "retry_call_numbers": [],
    "first_declared_finish_call": null,
    "first_declared_finish_command": null,
    "exit_status": "LimitsExceeded"
   },
   "iter-2": {
    "calls": 150,
    "retry_turns": 0,
    "retry_prompt_tokens": 0,
    "retry_call_numbers": [],
    "first_declared_finish_call": null,
    "first_declared_finish_command": null,
    "exit_status": "LimitsExceeded"
   },
   "iter-3": {
    "calls": 44,
    "retry_turns": 0,
    "retry_prompt_tokens": 0,
    "retry_call_numbers": [],
    "first_declared_finish_call": null,
    "first_declared_finish_command": null,
    "exit_status": "StepBudgetExceeded"
   }
  },
  "planner_tester_before_from_recorded_rounds_on_disk": {
   "round4/iter-1/developer.attempt1": {
    "calls": 69,
    "retry_turns": 20,
    "retry_prompt_tokens": 876566,
    "first_retry_call": 25,
    "first_echo_marker_command_call": null,
    "exit_status": "RepeatedActionError"
   },
   "round4/iter-1/planner.attempt1": {
    "calls": 23,
    "retry_turns": 8,
    "retry_prompt_tokens": 89313,
    "first_retry_call": 7,
    "first_echo_marker_command_call": 12,
    "exit_status": "Submitted"
   },
   "round4/iter-1/tester.attempt1": {
    "calls": 27,
    "retry_turns": 5,
    "retry_prompt_tokens": 382706,
    "first_retry_call": 19,
    "first_echo_marker_command_call": null,
    "exit_status": "RepeatedFormatError"
   },
   "round4/iter-2/developer.attempt1": {
    "calls": 125,
    "retry_turns": 10,
    "retry_prompt_tokens": 1486702,
    "first_retry_call": 58,
    "first_echo_marker_command_call": null,
    "exit_status": "RepeatedActionError"
   },
   "round4/iter-2/planner.attempt1": {
    "calls": 11,
    "retry_turns": 2,
    "retry_prompt_tokens": 20159,
    "first_retry_call": 5,
    "first_echo_marker_command_call": 11,
    "exit_status": "Submitted"
   },
   "round4/iter-2/tester.attempt1": {
    "calls": 37,
    "retry_turns": 4,
    "retry_prompt_tokens": 213244,
    "first_retry_call": 33,
    "first_echo_marker_command_call": 34,
    "exit_status": "RepeatedFormatError"
   },
   "round4/iter-3/developer.attempt1": {
    "calls": 102,
    "retry_turns": 8,
    "retry_prompt_tokens": 416910,
    "first_retry_call": 30,
    "first_echo_marker_command_call": null,
    "exit_status": "RepeatedActionError"
   },
   "round4/iter-3/planner.attempt1": {
    "calls": 13,
    "retry_turns": 6,
    "retry_prompt_tokens": 67761,
    "first_retry_call": 6,
    "first_echo_marker_command_call": null,
    "exit_status": "RepeatedFormatError"
   },
   "round4/iter-3/tester.attempt1": {
    "calls": 45,
    "retry_turns": 1,
    "retry_prompt_tokens": 61110,
    "first_retry_call": 44,
    "first_echo_marker_command_call": 45,
    "exit_status": "Submitted"
   },
   "livecost1/iter-1/developer.attempt1": {
    "calls": 150,
    "retry_turns": 0,
    "retry_prompt_tokens": 0,
    "first_retry_call": null,
    "first_echo_marker_command_call": null,
    "exit_status": "LimitsExceeded"
   },
   "livecost1/iter-1/planner.attempt1": {
    "calls": 17,
    "retry_turns": 4,
    "retry_prompt_tokens": 33395,
    "first_retry_call": 12,
    "first_echo_marker_command_call": null,
    "exit_status": "RepeatedFormatError"
   },
   "livecost1/iter-1/tester.attempt1": {
    "calls": 124,
    "retry_turns": 3,
    "retry_prompt_tokens": 100603,
    "first_retry_call": 118,
    "first_echo_marker_command_call": 124,
    "exit_status": "Submitted"
   },
   "clonefix1/iter-1/developer.attempt1": {
    "calls": 150,
    "retry_turns": 0,
    "retry_prompt_tokens": 0,
    "first_retry_call": null,
    "first_echo_marker_command_call": null,
    "exit_status": "LimitsExceeded"
   },
   "clonefix1/iter-1/planner.attempt1": {
    "calls": 9,
    "retry_turns": 3,
    "retry_prompt_tokens": 17363,
    "first_retry_call": 4,
    "first_echo_marker_command_call": 9,
    "exit_status": "Submitted"
   },
   "clonefix1/iter-1/tester.attempt1": {
    "calls": 126,
    "retry_turns": 3,
    "retry_prompt_tokens": 116205,
    "first_retry_call": 121,
    "first_echo_marker_command_call": 126,
    "exit_status": "Submitted"
   },
   "clonefix1/iter-2/developer.attempt1": {
    "calls": 150,
    "retry_turns": 0,
    "retry_prompt_tokens": 0,
    "first_retry_call": null,
    "first_echo_marker_command_call": null,
    "exit_status": "LimitsExceeded"
   },
   "clonefix1/iter-2/planner.attempt1": {
    "calls": 9,
    "retry_turns": 4,
    "retry_prompt_tokens": 32953,
    "first_retry_call": 5,
    "first_echo_marker_command_call": null,
    "exit_status": "RepeatedFormatError"
   },
   "clonefix1/iter-2/tester.attempt1": {
    "calls": 44,
    "retry_turns": 0,
    "retry_prompt_tokens": 0,
    "first_retry_call": null,
    "first_echo_marker_command_call": null,
    "exit_status": "StepBudgetExceeded"
   },
   "clonefix1/iter-2/tester.attempt2": {
    "calls": 63,
    "retry_turns": 4,
    "retry_prompt_tokens": 88517,
    "first_retry_call": 57,
    "first_echo_marker_command_call": 63,
    "exit_status": "Submitted"
   },
   "clonefix1/iter-3/developer.attempt1": {
    "calls": 150,
    "retry_turns": 0,
    "retry_prompt_tokens": 0,
    "first_retry_call": null,
    "first_echo_marker_command_call": null,
    "exit_status": "LimitsExceeded"
   },
   "clonefix1/iter-3/planner.attempt1": {
    "calls": 9,
    "retry_turns": 4,
    "retry_prompt_tokens": 36276,
    "first_retry_call": 4,
    "first_echo_marker_command_call": 9,
    "exit_status": "Submitted"
   },
   "clonefix1/iter-3/tester.attempt1": {
    "calls": 44,
    "retry_turns": 0,
    "retry_prompt_tokens": 0,
    "first_retry_call": null,
    "first_echo_marker_command_call": null,
    "exit_status": "StepBudgetExceeded"
   },
   "clonefix1/iter-3/tester.attempt2": {
    "calls": 97,
    "retry_turns": 2,
    "retry_prompt_tokens": 76512,
    "first_retry_call": 92,
    "first_echo_marker_command_call": 97,
    "exit_status": "Submitted"
   },
   "round3/iter-1/developer.attempt1": {
    "calls": 43,
    "retry_turns": 0,
    "retry_prompt_tokens": 0,
    "first_retry_call": null,
    "first_echo_marker_command_call": null,
    "exit_status": "LimitsExceeded"
   },
   "round3/iter-1/planner.attempt1": {
    "calls": 11,
    "retry_turns": 4,
    "retry_prompt_tokens": 26450,
    "first_retry_call": 4,
    "first_echo_marker_command_call": 11,
    "exit_status": "Submitted"
   },
   "round3/iter-1/tester.attempt1": {
    "calls": 40,
    "retry_turns": 4,
    "retry_prompt_tokens": 323971,
    "first_retry_call": 33,
    "first_echo_marker_command_call": 36,
    "exit_status": "Submitted"
   },
   "round3/iter-2/developer.attempt1": {
    "calls": 43,
    "retry_turns": 0,
    "retry_prompt_tokens": 0,
    "first_retry_call": null,
    "first_echo_marker_command_call": null,
    "exit_status": "LimitsExceeded"
   },
   "round3/iter-2/planner.attempt1": {
    "calls": 9,
    "retry_turns": 3,
    "retry_prompt_tokens": 29394,
    "first_retry_call": 5,
    "first_echo_marker_command_call": 9,
    "exit_status": "Submitted"
   },
   "round3/iter-2/tester.attempt1": {
    "calls": 36,
    "retry_turns": 1,
    "retry_prompt_tokens": 54816,
    "first_retry_call": 33,
    "first_echo_marker_command_call": 36,
    "exit_status": "Submitted"
   },
   "round3/iter-3/developer.attempt1": {
    "calls": 43,
    "retry_turns": 6,
    "retry_prompt_tokens": 458370,
    "first_retry_call": 26,
    "first_echo_marker_command_call": null,
    "exit_status": "LimitsExceeded"
   },
   "round3/iter-3/planner.attempt1": {
    "calls": 12,
    "retry_turns": 3,
    "retry_prompt_tokens": 31696,
    "first_retry_call": 5,
    "first_echo_marker_command_call": 12,
    "exit_status": "Submitted"
   },
   "round3/iter-3/tester.attempt1": {
    "calls": 43,
    "retry_turns": 6,
    "retry_prompt_tokens": 335262,
    "first_retry_call": 36,
    "first_echo_marker_command_call": null,
    "exit_status": "RepeatedFormatError"
   }
  },
  "all_roles_after": {
   "iter-1": {
    "developer.1": {
     "calls": 150,
     "retry_turns": 0,
     "retry_prompt_tokens": 0,
     "retry_call_numbers": [],
     "first_declared_finish_call": null,
     "first_declared_finish_command": null,
     "exit_status": "LimitsExceeded"
    },
    "planner.1": {
     "calls": 6,
     "retry_turns": 0,
     "retry_prompt_tokens": 0,
     "retry_call_numbers": [],
     "first_declared_finish_call": 6,
     "first_declared_finish_command": "echo COMPLETE_TASK_AND_SUBMIT_FINAL_OUTPUT",
     "exit_status": "Submitted"
    },
    "tester.1": {
     "calls": 98,
     "retry_turns": 0,
     "retry_prompt_tokens": 0,
     "retry_call_numbers": [],
     "first_declared_finish_call": 98,
     "first_declared_finish_command": "echo COMPLETE_TASK_AND_SUBMIT_FINAL_OUTPUT",
     "exit_status": "Submitted"
    }
   },
   "iter-2": {
    "developer.1": {
     "calls": 150,
     "retry_turns": 0,
     "retry_prompt_tokens": 0,
     "retry_call_numbers": [],
     "first_declared_finish_call": null,
     "first_declared_finish_command": null,
     "exit_status": "LimitsExceeded"
    },
    "planner.1": {
     "calls": 6,
     "retry_turns": 0,
     "retry_prompt_tokens": 0,
     "retry_call_numbers": [],
     "first_declared_finish_call": 6,
     "first_declared_finish_command": "echo COMPLETE_TASK_AND_SUBMIT_FINAL_OUTPUT",
     "exit_status": "Submitted"
    },
    "tester.1": {
     "calls": 150,
     "retry_turns": 0,
     "retry_prompt_tokens": 0,
     "retry_call_numbers": [],
     "first_declared_finish_call": null,
     "first_declared_finish_command": null,
     "exit_status": "LimitsExceeded"
    }
   },
   "iter-3": {
    "developer.1": {
     "calls": 44,
     "retry_turns": 0,
     "retry_prompt_tokens": 0,
     "retry_call_numbers": [],
     "first_declared_finish_call": null,
     "first_declared_finish_command": null,
     "exit_status": "StepBudgetExceeded"
    },
    "planner.1": {
     "calls": 6,
     "retry_turns": 0,
     "retry_prompt_tokens": 0,
     "retry_call_numbers": [],
     "first_declared_finish_call": 6,
     "first_declared_finish_command": "echo COMPLETE_TASK_AND_SUBMIT_FINAL_OUTPUT",
     "exit_status": "Submitted"
    }
   }
  },
  "before_total_developer_retry_turns_in_the_four_recordings": 38,
  "before_total_developer_retry_prompt_tokens_in_the_four_recordings": 2780178,
  "after_total_retry_turns_across_every_role_and_iteration": 0,
  "after_total_retry_prompt_tokens": 0,
  "rejected_response_shape_captured": null,
  "why_none": "the fix's target shape did not occur: not one of the 7 recorded model-call sequences of this round contains a FormatError turn, so no rejected response exists to quote; the pre-fix shape remains documented in .spec/bevy/RETRY-FIX-REPORT.md"
 },
 "first_declared_finish": {
  "iter-1": {
   "developer": {
    "call_index": null,
    "exit_status_at_end_of_call": "LimitsExceeded",
    "total_calls": 150,
    "did_the_call_end_there": false
   },
   "planner": {
    "call_index": 6,
    "exit_status_at_end_of_call": "Submitted",
    "did_the_call_end_there": true
   },
   "tester": {
    "call_index": 98,
    "exit_status_at_end_of_call": "Submitted",
    "did_the_call_end_there": true
   }
  },
  "iter-2": {
   "developer": {
    "call_index": null,
    "exit_status_at_end_of_call": "LimitsExceeded",
    "total_calls": 150,
    "did_the_call_end_there": false
   },
   "planner": {
    "call_index": 6,
    "exit_status_at_end_of_call": "Submitted",
    "did_the_call_end_there": true
   },
   "tester": {
    "call_index": null,
    "exit_status_at_end_of_call": "LimitsExceeded",
    "did_the_call_end_there": false
   }
  },
  "iter-3": {
   "developer": {
    "call_index": null,
    "exit_status_at_end_of_call": "StepBudgetExceeded",
    "total_calls": 44,
    "did_the_call_end_there": false
   },
   "planner": {
    "call_index": 6,
    "exit_status_at_end_of_call": "Submitted",
    "did_the_call_end_there": true
   },
   "tester": {
    "call_index": null,
    "exit_status_at_end_of_call": null,
    "did_the_call_end_there": true
   }
  }
 },
 "artifact_validity_and_strength": {
  "iter-1": {
   "developer_artifact_valid": true,
   "artifact_gate": {
    "applicable": true,
    "launchable": true,
    "reasons": []
   },
   "first_battery_pass_launchable": true,
   "repair_retry_used": false,
   "battery_passes_run": 1,
   "failing_battery_steps": [],
   "candidate_game_rs_bytes": 11828,
   "write_failures": [],
   "out_of_tree_writes": []
  },
  "iter-2": {
   "developer_artifact_valid": true,
   "artifact_gate": {
    "applicable": true,
    "launchable": true,
    "reasons": []
   },
   "first_battery_pass_launchable": true,
   "repair_retry_used": false,
   "battery_passes_run": 1,
   "failing_battery_steps": [],
   "candidate_game_rs_bytes": 19134,
   "write_failures": [],
   "out_of_tree_writes": []
  },
  "iter-3": {
   "developer_artifact_valid": true,
   "artifact_gate": {
    "applicable": false,
    "launchable": false,
    "reasons": [
     "the round failed; no artifact gate was produced"
    ]
   },
   "first_battery_pass_launchable": null,
   "repair_retry_used": false,
   "battery_passes_run": 0,
   "failing_battery_steps": [],
   "candidate_game_rs_bytes": null,
   "write_failures": [
    {
     "role": "developer",
     "attempt": 1,
     "exit_status": "StepBudgetExceeded",
     "declared_artifact": "a file inside the project (the candidate increment, outside the hash-excluded paths)",
     "artifact_written": false,
     "reason": "the call ended with `StepBudgetExceeded` and the artifact tree shows no write to a file inside the project (the candidate increment, outside the hash-excluded paths)"
    }
   ],
   "out_of_tree_writes": []
  }
 },
 "artifact_strength_reference": {
  "A0_scaffold_game_rs_bytes": 4502,
  "what_the_artifact_check_verifies": "crate name, manifest, lockfile and the frozen contract paths only — nothing about whether the iteration's plan was implemented (ACCEPTANCE-RETRY-FIX C7)",
  "independent_strength_observations_i_took": [
   "iter-1 src/game.rs grew 4,502 -> 11,828 bytes and iter-2 grew it further to 19,134 bytes, so two iterations really implemented code rather than only passing the structural check",
   "iter-1 and iter-2 each passed all 12 battery steps on their first pass (10 semantic steps + editor_errors_baseline + play_scene_ready)",
   "iter-3 wrote nothing inside the project (44 calls, 46 files under .hoh/scratch only) and consumed no battery pass at all"
  ]
 },
 "identity": {
  "surviving_launch": {
   "nonce": "e42b6006-f5e2-4e69-ab48-0d37618b26ea",
   "answered_nonce": "e42b6006-f5e2-4e69-ab48-0d37618b26ea",
   "spawned_pid": 49948,
   "answering_pid": 49948,
   "listening_pid": 49948,
   "verified": true,
   "launch_image": "runs\\bevy-completion1\\launch-image\\e608b3b5-841d-4b5a-aafb-915d27f2d128\\hof_game.exe",
   "built_binary": "D:\\hof-live-run\\hof-bevy-shared-target\\debug\\hof_game.exe"
  },
  "checks": {
   "ledger_nonce_equals_answered_nonce": true,
   "nonce_equals_answered_nonce": true,
   "answering_pid_equals_spawned_pid": true,
   "listening_pid_equals_spawned_pid": true,
   "verified": true
  },
  "ledger_lines": 5,
  "ledger": [
   {
    "pid": 50340,
    "nonce": "b90abd96-e5f3-40d3-976a-5dec9449f205",
    "launched_at_seconds": 1791241637,
    "launch_image": "runs\\bevy-completion1\\launch-image\\e1b87264-a3d7-46b7-b073-385f8e5def58\\hof_game.exe"
   },
   {
    "pid": 57176,
    "nonce": "3c840cf2-00dd-42e3-beb4-edb727811980",
    "launched_at_seconds": 1791242903,
    "launch_image": "runs\\bevy-completion1\\launch-image\\ffc23b3a-7bbe-406a-8705-d459bc966902\\hof_game.exe"
   },
   {
    "pid": 41920,
    "nonce": "1e0a3828-1bdd-4341-b219-c2b5e93c4428",
    "launched_at_seconds": 1791242919,
    "launch_image": "runs\\bevy-completion1\\launch-image\\8f813845-82cf-4626-9965-e92b714a3ce6\\hof_game.exe"
   },
   {
    "pid": 49948,
    "nonce": "e42b6006-f5e2-4e69-ab48-0d37618b26ea",
    "launched_at_seconds": 1791245359,
    "launch_image": "runs\\bevy-completion1\\launch-image\\e608b3b5-841d-4b5a-aafb-915d27f2d128\\hof_game.exe"
   },
   {
    "pid": 54908,
    "nonce": "91b18063-4457-4a02-be30-edb72832341f",
    "launched_at_seconds": 1791245378,
    "launch_image": "runs\\bevy-completion1\\launch-image\\44412922-b295-4b5b-9068-9e59fc263a57\\hof_game.exe"
   }
  ],
  "meta_segments_pid": 49948,
  "per_iteration_snapshots_i_took_before_they_were_overwritten": {
   "iter-1": {
    "nonce": "3c840cf2-00dd-42e3-beb4-edb727811980",
    "answered_nonce": "3c840cf2-00dd-42e3-beb4-edb727811980",
    "spawned_pid": 57176,
    "answering_pid": 57176,
    "listening_pid": 57176,
    "verified": true
   },
   "iter-2": {
    "nonce": "e42b6006-f5e2-4e69-ab48-0d37618b26ea",
    "answered_nonce": "e42b6006-f5e2-4e69-ab48-0d37618b26ea",
    "spawned_pid": 49948,
    "answering_pid": 49948,
    "listening_pid": 49948,
    "verified": true
   }
  },
  "live_os_check_i_took_during_the_round": {
   "command": "netstat -ano | grep 15702 ; tasklist | grep hof_game",
   "listener_lines": 1,
   "line": "TCP    127.0.0.1:15702        0.0.0.0:0              LISTENING       41920",
   "hof_game_processes": 1,
   "pid": 41920,
   "matches_ledger_line": 3,
   "ledger_line_3_nonce": "1e0a3828-1bdd-4341-b219-c2b5e93c4428"
  },
  "round_stop": {
   "called_at_seconds": 1791246499,
   "ledger": "runs\\bevy-completion1\\launch-ledger.jsonl",
   "ledger_lines_at_sweep": 5,
   "evidence": "runs\\bevy-completion1\\round-stop.json",
   "recorded": [
    50340,
    57176,
    41920,
    49948,
    54908
   ],
   "reaped": [
    57176
   ],
   "still_alive": [],
   "endpoint_holder": null,
   "failure": null
  },
  "after_the_round": {
   "netstat_15702_15703": "no line",
   "hof_game_or_hoh_processes": "none"
  }
 },
 "coverage": {
  "iter-1": {
   "surfaces": {
    "total": 19,
    "verified": 15,
    "gap": 0,
    "unobservable": 4
   },
   "unobservable_ids": [
    "C5",
    "C6",
    "Q-scale",
    "Q-not-required"
   ],
   "q_startup": {
    "id": "Q-startup",
    "status": "verified",
    "evidence": "battery step(s): play_scene_ready, e3_process_liveness",
    "reason": null
   },
   "b21": {
    "id": "B2.1",
    "status": "verified",
    "evidence": "battery step(s): e3_process_liveness",
    "reason": null
   },
   "liveness_raw_frames": {
    "first_frame": 693,
    "requested": 8,
    "second_frame": 703
   },
   "liveness_observed": true
  },
  "iter-2": {
   "surfaces": {
    "total": 19,
    "verified": 15,
    "gap": 0,
    "unobservable": 4
   },
   "unobservable_ids": [
    "C5",
    "C6",
    "Q-scale",
    "Q-not-required"
   ],
   "q_startup": {
    "id": "Q-startup",
    "status": "verified",
    "evidence": "battery step(s): play_scene_ready, e3_process_liveness",
    "reason": null
   },
   "b21": {
    "id": "B2.1",
    "status": "verified",
    "evidence": "battery step(s): e3_process_liveness",
    "reason": null
   },
   "liveness_raw_frames": {
    "first_frame": 696,
    "requested": 8,
    "second_frame": 706
   },
   "liveness_observed": true
  },
  "iter-3": {
   "surfaces": {
    "total": 0,
    "verified": 0,
    "gap": 0,
    "unobservable": 0
   },
   "unobservable_ids": [],
   "q_startup": null,
   "b21": null,
   "liveness_raw_frames": null,
   "liveness_observed": null
  }
 },
 "gate": {
  "command": "cargo test --offline",
  "literal_exit_code": 0,
  "passed": 802,
  "failed": 0,
  "ignored": 6,
  "listed": 808,
  "test_result_lines": 60,
  "compiler_warning_lines": 0,
  "error_lines": 0,
  "list_command": "cargo test --offline -- --list",
  "list_exit_code": 0,
  "list_count": 808,
  "list_ignored_command": "cargo test --offline -- --list --ignored",
  "list_ignored_count": 6,
  "build_dir": "D:/live2-target (this experiment's own; the repository's own target/ was not used)",
  "baseline": {
   "passed": 802,
   "failed": 0,
   "ignored": 6,
   "listed": 808
  },
  "matches_baseline": true
 },
 "disk": {
  "before": {
   "D:": "63 G available",
   "F:": "9.1 G available (100% used)"
  },
  "after_the_round_before_the_gate": {
   "D:": "62 G available",
   "F:": "9.0 G available"
  },
  "after_the_gate": {
   "D:": "54 G available",
   "F:": "8.3 G available"
  },
  "where_it_was_spent": "the games and the harness build tree went to D: (D:/live2-target, 9.1 G including the gate's test binaries; D:/hof-live-run/hof-bevy-shared-target, 9.8 G, the warm Bevy cache reused in place); F: grew by 904 MB, which is the gitignored run tree (runs/bevy-completion1 891 MB, runs/completion1 13 MB), kept as required",
  "deletions": "none — nothing this experiment created had to be removed, so no removal was performed at all"
 },
 "constraints": {
  "round_run_from_outside_the_repository": true,
  "keys_from_outside_the_repository_only": true,
  "key_copied_printed_or_written_by_this_experiment": false,
  "rm_rf_or_wildcard_deletion_used": false,
  "path_constructed_from_an_unexpanded_variable": false,
  "git_checkout_double_dash_used": false,
  "src_tests_evidence_registry_battery_gitattributes_or_frozen_document_modified": false,
  "committed_or_pushed": false,
  "decisions_md_appended": false,
  "helper_scripts_location": "D:/live2/ (outside the repository)",
  "repository_paths_written": [
   ".spec/bevy/LIVE-COMPLETION-MEASUREMENT.md (this report)",
   "runs/completion1/** and runs/bevy-completion1/** (gitignored harness evidence, kept)"
  ],
  "working_tree_after": "no tracked file modified; the only untracked path is this report"
 },
 "measured_vs_inferred": {
  "measured": [
   "every call, token and wall-clock figure is read out of runs/completion1/iter-*/usage.json and the trajectories in runs/completion1/iter-*/traj/",
   "every retry count is a count of messages carrying extra.interrupt_type == FormatError in those trajectories",
   "the identity values are read out of runs/bevy-completion1/launch.json, its append-only ledger and my own netstat reading taken while the round ran",
   "the coverage figures are read out of runs/completion1/iter-*/result.json and the persisted raw liveness observations",
   "the gate is this repository's own cargo test --offline, run in this experiment's own build directory"
  ],
  "inferred": [
   "why the developer never declared itself finished: the recordings show the same model declaring itself finished at call 25/58/30 under the old prompt while this round's developer never ran the command, but the causal link between the prompt change and that behavioural difference is an inference from those two measurements, not itself measured",
   "whether iteration 3's no-write run would have happened without the fix: it is not attributable from one round",
   "the plan-conformance of the two completed artifacts: game.rs grew and every battery step passed, but nothing here proves the plan was fully implemented"
  ]
 },
 "single_most_important_thing": "The retry fix removes a real defect but not the cost: retries went 38 -> 0 across every role and iteration, yet the Developer still ended 2 of 3 calls at the 150-call step limit (2.35x and 2.63x the criterion) because it never ran the completion command at all — the expected tail saving is not merely smaller than projected, it is absent, and the only call that came in under 1,500,000 tokens (803,027) did so by being aborted with no artifact, which failed the round (exit 2, NoEngineeringWrite). The next decision must be about bounding call count, not about the completion protocol."
}
```

# LIVE-COMPLETION-MEASUREMENT — one real round after the format-error retry fix

The machine-readable block above is `json.dumps(..., indent=1, ensure_ascii=False)` output written by
`D:/live2/write_report.py` and then **parsed back out of this written file**; the parse is the last
thing the generator does and it fails if the block does not round-trip. Every helper script lives
outside the repository at `D:/live2/`; the run tree is kept at `runs/completion1/` and
`runs/bevy-completion1/`.

**What was run.** `hoh init --adapter bevy --project D:\live2\project` (exit **0**) and then `hoh run
--adapter bevy --project D:\live2\project --run-id completion1 --env-from-secret
D:\hof-live\secret.env` from `F:\moonbit-hof-rs`, headless, model `deepseek-v4.1-flash`, with the
binary built from this tree (`cargo build --offline --bin hoh`, exit 0). The project was created empty
outside the repository; the key came from the same file outside the repository that the previous live
round used and was never read, copied, printed or written by this experiment. The games and the build
trees went to `D:` — `F:` had 9.1 G free and 100 % used before the round.

**The headline: the round failed.** `hoh run` returned literal exit code **2** after 81.6 minutes with
`hoh: contract violation: NoEngineeringWrite (no_engineering_write)`. Iterations 1 and 2 completed
(`ok: true`); iteration 3's Developer spent 44 calls reading and wrote only `.hoh/scratch` files, so
the engineering-write gate stopped the round and iteration 3 produced no artifact, no battery pass and
no coverage. Per instruction this is reported as the result; I did not re-run it.

## 1. Did the retry fix work? Yes — and that is all it did

| role / recording | calls | retry turns before | retry prompt tokens before | retry turns after | first declared finish, after |
|---|---|---|---|---|---|
| developer, round4-iter-1 | 69 | **20** | 876,566 | **0** | never declared |
| developer, round4-iter-2 | 125 | **10** | 1,486,702 | **0** | never declared |
| developer, round4-iter-3 | 102 | **8** | 416,910 | **0** | never declared |
| developer, livecost1-iter-1 | 150 | 0 | 0 | **0** | never declared |
| planner, three recorded pre-fix rounds | 23 / 11 / 13, 17, 9 / 9 / 9 | **8 / 2 / 6, 4, 3 / 4 / 4** | 89,313 / 20,159 / 67,761 / 33,395 / 17,363 / 32,953 / 36,276 | **0 / 0 / 0** | call **6** every time, by the command |
| tester, three recorded pre-fix rounds | 27 / 37 / 45, 124, 126 / 63 / 97 | **5 / 4 / 1, 3, 3 / 4 / 2** | 382,706 / 213,244 / 61,110 / 100,603 / 116,205 / 88,517 / 76,512 | **0 / 0** | call **98** (iter-1, by the command) / never (iter-2) |

Every one of the 7 recorded model-call sequences of this round contains **zero** `FormatError` turns,
against 38 in the four committed Developer recordings and 3–8 per Planner/Tester call in the recorded
pre-fix rounds. `COMPLETE_TASK_AND_SUBMIT_FINAL_OUTPUT` was executed as `echo
COMPLETE_TASK_AND_SUBMIT_FINAL_OUTPUT` — the exact command the new shared `[completion]` section
documents — by the Planner in all three iterations (each call ending there, at call 6 of 6) and by the
Tester in iteration 1 (call 98 of 98). **Because no retry occurred, no rejected response exists to
quote; there is no failure-shape artefact to capture from this round.**

## 2. Did the round get cheaper without getting weaker? It got neither clearly cheaper nor safely cheaper

Developer cost, per iteration, beside the two baselines that apply to it:

| iteration | calls | prompt | completion | total tokens | wall clock | ended by | vs 1,500,000 | vs its round4 baseline | vs livecost1 (3,651,120) |
|---|---|---|---|---|---|---|---|---|---|
| iter-1 | 150 | 3,414,645 | 112,921 | **3,527,566** | 20.66 min | `LimitsExceeded` | **2.352x** | round4-iter-1: 1.343x | **0.966x** |
| iter-2 | 150 | 3,820,462 | 118,565 | **3,939,027** | 27.78 min | `LimitsExceeded` | **2.626x** | round4-iter-2: 0.301x | **1.079x** |
| iter-3 | 44 | 789,257 | 13,770 | **803,027** | 5.83 min | `StepBudgetExceeded` | **0.535x** | round4-iter-3: 0.154x | 0.220x |
| **total** | **344** | 8,024,364 | 245,256 | **8,269,620** | 54.28 min | — | **5.513x** | — | 2.265x |

The criterion — one Developer call under 1,500,000 tokens — is **not met**: two of the three calls
are 2.35x and 2.63x it, and the third is under it only because the harness's no-write guard aborted it
at 44 calls with nothing written. Against the only like-for-like baseline (the recorded
`livecost1-iter-1` Developer call, also 150 calls) the round is 3.4 % cheaper in iteration 1 and 7.9 %
**more** expensive in iteration 2. That is the size of the retry fix in a producing call: the rejected
turns are not saved (they move to being ordinary turns); what disappears is the `FormatError` history
message and every later re-send of it.

**The decisive new number is the tail, and it did not happen.** The four recordings' Developers each
first declared themselves finished at call **25 / 58 / 30**, and the fix was supposed to make that
declaration executable so the call would end there. In this round **the Developer never declared
itself finished in any iteration**: no completion command, no prose-only completion reply, no
`FormatError`; it read and wrote until the step limit (iterations 1 and 2, `LimitsExceeded` at 150)
or until the 43-step no-artifact guard fired (iteration 3, `StepBudgetExceeded` at 44). The Planner
and the Tester did exactly what the fix intends — they ran the command and their calls ended there —
so the mechanism is confirmed for two of the three roles and measurably absent for the one whose cost
the criterion is about.

**And the round is weaker.** The previous live round (`clonefix1`) exited **0** with three `ok`
iterations; this one exits **2** with a failed third iteration and no artifact for it. The two
completed iterations look sound: `artifact_valid: true` for every attempt, the first battery pass
`launchable: true` in both with **no repair retry consumed** (`repair_retry_used: false`, one battery
pass each, no failing step), `write_failures: []`, `out_of_tree_writes: []`, and `src/game.rs` grown
from the 4,502-byte scaffold to 11,828 then 19,134 bytes. But the round as a whole is a failure, and
the cheap iteration is exactly the one that produced nothing — a call under the token bar that wrote
no engineering file is not a win.

Iteration 3 is worth stating precisely because it is the risk the acceptance named, in the opposite
direction: its Planner wrote a real plan (fix the air/ground transition, place the coin and the goal),
its Developer spent 44 calls reading `src/game.rs`, the deterministic records and the plan, ran
`head`/`ConvertFrom-Json` probes, copied the plan into `.hoh/scratch`, and wrote nothing into the
project before the `steps_per_artifact: 8` guard ended it at 43 steps.

## 3. Is the round real and trustworthy?

The observations belong to the process this round launched. `runs/bevy-completion1/launch.json`
identifies the launch that survived (iteration 2's battery pass, the one `meta.json` also names):

| reading | value |
|---|---|
| nonce (generated before the spawn, carried only in the child's environment) | `e42b6006-f5e2-4e69-ab48-0d37618b26ea` |
| answered_nonce (what the endpoint served back when readiness read `ProcessNonce`) | `e42b6006-f5e2-4e69-ab48-0d37618b26ea` |
| spawned_pid / answering_pid / listening_pid | `49948` / `49948` / `49948` |
| verified | `true` |
| ledger line for that nonce and pid | line 4 of `runs/bevy-completion1/launch-ledger.jsonl`, `launched_at_seconds 1791245359`, same launch-image UUID `e608b3b5-841d-4b5a-aafb-915d27f2d128` |

The pre-spawn ledger nonce equals the answering nonce, the answering pid equals the spawned pid, and
the harness's own OS reading of the listening pid equals the spawned pid. I also took my own OS
reading while the round ran: `netstat -ano` returned **exactly one** line for 15702 —
`TCP 127.0.0.1:15702  0.0.0.0:0  LISTENING  41920` — and `tasklist` returned exactly one
`hof_game.exe`, pid **41920**, which is ledger line 3 (`1e0a3828-1bdd-4341-b219-c2b5e93c4428`); no
other listener held the port. The same three-way agreement holds for iteration 1's launch, which I
snapshotted out before it was overwritten: nonce `3c840cf2-00dd-42e3-beb4-edb727811980` =
`answered_nonce`, pid `57176` = `answering_pid` = `listening_pid`, `verified: true`, ledger line 2.
Five launches were recorded in all (two per completed battery pass plus the round's opening session);
the ledger is append-only and every line has a distinct nonce, pid and launch image.

**Nothing survives the round.** `round-stop.json` recorded 5 pids, `still_alive: []`,
`endpoint_holder: null`, `failure: null` (pid 57176 was still alive at the sweep and was reaped);
after the exit code, `netstat` names no line for 15702 or 15703 and `tasklist` shows no `hof_game.exe`
and no `hoh.exe`.

## 4. Coverage

| iteration | frozen surfaces | gap | unobservable | `Q-startup` / `B2.1` |
|---|---|---|---|---|
| iter-1 | **15 verified / 0 gap / 4 unobservable of 19** | 0 | C5, C6, Q-scale, Q-not-required | both `verified`, evidence `battery step(s): e3_process_liveness` (+ `play_scene_ready`), raw file observed `FrameCounter` **693 -> 703** for a requested 8 |
| iter-2 | **15 verified / 0 gap / 4 unobservable of 19** | 0 | C5, C6, Q-scale, Q-not-required | both `verified`, same evidence, raw file observed **696 -> 706** |
| iter-3 | none — the developer stage failed before any battery pass (the figure it reports is 0/0/0/0) | — | — | not decided |

So the figure is **15 verified / 0 gap / 4 unobservable of 19** in both completed iterations and there
is no coverage figure at all in the failed one, and the two formerly
open items (`Q-startup`, `B2.1`) are still decided by a **real persisted observation** of the game's
own frame counter advancing, once per completed pass.

## 5. What I could not establish

* **Why the Developer never declared itself finished.** This is the round's central measurement and it
  is a measurement of an absence. The same model, on the same task shape, declared itself finished at
  call 25/58/30 under the old prompt; under the new prompt it ran to the step limit or the no-write
  guard without ever issuing the command. Whether that is because the new prompt's "prose is allowed —
  but always with a tool call" wording suppresses the "I am done" moment, because those recorded
  declarations were themselves sustained by the retry loop, or because this round's task simply had
  more left to do, cannot be separated from one round. It is an inference, not a measurement.
* **Attribution of iteration 3's no-write run to the fix.** Not established; one round cannot separate
  it from model variance or from the `steps_per_artifact: 8` guard interacting with a read-heavy plan.
* **Plan conformance of the two completed artifacts.** `artifact_valid` checks the crate name, the
  manifest, the lockfile and the frozen contract paths — nothing about whether the plan was
  implemented. I can show the artifact grew and that all 12 battery steps passed on the first pass,
  but "the plan was implemented" is not something this measurement decides.
* **Any effect on a second provider, model or project shape**; and, as always, a retry shape that did
  not occur cannot be quoted.

## 6. The gate, the disk and the constraints

`cargo test --offline` in this experiment's own build directory `D:/live2-target`: literal exit code
**0**, **802 passed / 0 failed / 6 ignored / 808 listed** over 60 `test result:` lines, 0 compiler
warning lines — exactly the baseline. `--list` returns 808, `--list --ignored` returns 6. Disk: `D:`
63 G -> 54 G (9.1 G of that is this experiment's own build tree `D:/live2-target`, most of it the
gate's test binaries, plus the 9.8 G warm Bevy cache at `D:/hof-live-run/hof-bevy-shared-target` which
was reused in place) and `F:` 9.1 G -> 8.3 G, which is the 904 MB gitignored run tree that is kept.
**Nothing was deleted** — nothing
this experiment created needed removing, so no `rm -rf`, no wildcard and no removal at all was used.
No path was constructed from an unexpanded variable; no `git checkout --`; nothing under `src/**`,
`tests/**`, `evidence/**`, the registry, the battery, `.gitattributes` or any frozen document was
touched; nothing was committed or pushed; the only repository paths written are this report and the
gitignored run trees. **I appended nothing to `DECISIONS.md`** — I judge the decision this finding
drives (what to bound next) to belong to the dispatcher, and the report carries the evidence it needs.

## 7. The single most important thing for the next decision-maker

**The retry fix cures the retry and not the cost — and the reason is that the Developer never takes
the new exit.** Retries went 38 -> 0 across every role and every iteration, and the Planner and the
Tester now end exactly where the recordings predicted they would (call 6 and call 98, by the
documented `echo` command). But the Developer never ran it once: two calls ground to the 150-call step
limit at 2.35x and 2.63x the criterion, and the only call under 1,500,000 tokens was the one the
no-write guard aborted with an empty artifact, which is what failed the round. So the completion
protocol is now **correct and irrelevant to the criterion**: the 1.5 M target is decided by how many
calls a producing Developer call makes and how much context each re-sends, and the live model will
spend all 150 calls it is given. The next decision should bound the call count (or the context per
call) directly, and it must do so in a way that cannot be satisfied by a call that writes nothing —
this round contains a worked example, in iteration 3, of a cheap call that produced a failed round.
