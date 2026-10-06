```json
{
 "schema": "hof-rs / bevy post-write call bound: the mechanism, the measured number, the tests and the projected effect",
 "artifact": ".spec/bevy/POST-WRITE-BOUND-REPORT.md",
 "produced_at": "2026-10-06",
 "branch": "bevy-core",
 "head_kind": "working tree on top of b6e9364 (the acceptance of the write-guaranteed exit, whose implementation is 6be54ea), uncommitted",
 "offline": true,
 "round_run": false,
 "model_call_made": false,
 "engine_started": false,
 "committed": false,
 "pushed": false,
 "criterion": {
  "tokens_per_developer_call": 1500000,
  "source": "config/hoh.yaml agent.artifact_write_budget_tokens",
  "zero_context_floor_for_a_150_call_live_developer_call": 2077238,
  "source_of_the_floor": ".spec/bevy/SPIKE-COST-LEVERS.md lever 1 cap_zero_totals.livecost1-iter-1",
  "why_the_criterion_needs_an_earlier_end": "at the zero-context floor a 150-call live call still costs 2,077,238 tokens (1.385x), so no context shrinking reaches 1,500,000 and the call has to end earlier"
 },
 "budget_mechanism": {
  "a_step_is_a_model_call": {
   "quote": "src/harness/compact.rs:302 (CountingModel::query) `self.progress.steps.increment();`",
   "why": "mini's `n_calls` and therefore `agent.step_limit` are written in model calls; round 4 was cut by a budget the prompt stated as 43 because the guard counted actions instead.  The guard's `steps()` reads this shared `StepCounter` (src/harness/guard.rs, `sharing_steps`)."
  },
  "where_the_budget_is_computed": {
   "function": "AgentLimits::effective_step_limit(has_written)",
   "file": "src/config.rs",
   "quote_before_this_batch": "if has_written || self.steps_per_artifact == 0 { return self.step_limit; } let per_artifact = (self.step_limit / self.steps_per_artifact).max(1); (self.wrap_up_steps + per_artifact).max(self.wrap_up_steps)",
   "quote_after_this_batch": "if self.steps_per_artifact == 0 { return self.step_limit; } if has_written { return self.written_step_limit(); } let per_artifact = (self.step_limit / self.steps_per_artifact).max(1); (self.wrap_up_steps + per_artifact).max(self.wrap_up_steps)",
   "new_function": "AgentLimits::written_step_limit() = if post_write_step_limit == 0 { step_limit } else { post_write_step_limit.min(step_limit) }",
   "thresholds_quoted_from_config_hoh_yaml": {
    "step_limit": 150,
    "wrap_up_steps": 25,
    "steps_per_artifact": 8,
    "post_write_step_limit": 35
   },
   "arithmetic": {
    "unwritten_before_and_after": "(wrap_up_steps + max(step_limit/steps_per_artifact, 1)) = 25 + 18 = 43 model calls  (unchanged by this batch)",
    "written_before_this_batch": "step_limit = 150 model calls",
    "written_after_this_batch": "min(post_write_step_limit, step_limit) = min(35, 150) = 35 model calls"
   }
  },
  "where_the_budget_is_enforced": {
   "function": "WriteGuardEnvironment::step_budget_exceeded()",
   "file": "src/harness/guard.rs",
   "quote": "if self.step_limit == 0 { return None; } self.step_counter.as_ref()?; let budget = self.effective_step_budget().min(self.step_limit); let steps = self.steps(); if steps > budget { Some(FailFast::StepBudget { steps, budget }) } else { None }",
   "called_from": "WriteGuardEnvironment::execute, first statement: `if let Some(fail_fast) = self.step_budget_exceeded() { return Err(...) }`",
   "semantics": "`steps > budget` means **exactly `budget` model calls may act and the (budget+1)-th is billed and then refused**, so a bound B costs the prefix sum over calls 1..=B+1.  Measured proof of the off-by-one: the unwritten budget of 43 produced 44 billed calls and StepBudgetExceeded in runs/completion1/iter-3 (44 calls, 803,027 tokens).",
   "exit_status": "StepBudgetExceeded (src/harness/guard.rs STEP_BUDGET_STATUS), accepted as a failure by runtime::write_failure::is_failure_status and as a limit by runtime::invoke::is_limits_exceeded"
  },
  "mini_flat_backstop": {
   "quote": "src/harness/mini.rs: `let flat_step_limit = inv.limits.step_limit;` ... `AgentConfig { step_limit: flat_step_limit, ... }`",
   "value": 150,
   "why_it_is_not_the_lever": "it is frozen when the agent is constructed, so a write inside the call cannot raise or lower it (round 3's defect); the guard re-reads the live value at every step, which is why the bound lives there"
  },
  "other_budgets_left_untouched": {
   "artifact_write_budget_seconds": 900,
   "artifact_write_budget_tokens": 1500000,
   "max_action_failures": 3,
   "max_repeated_actions": 15,
   "wall_time_limit_seconds": 3600,
   "max_consecutive_format_errors": 3,
   "cost_limit": 0.0,
   "repair_steps": 60
  },
  "what_a_written_call_that_hits_the_bound_costs_the_round": {
   "quote": "src/runtime/write_failure.rs::assess: `if artifact_written { return None; }` with artifact_written = (h_dev_before != h_dev_after) from src/runtime/run_loop.rs",
   "consequence": "a call cut by the bound AFTER writing its project file produces no RoleWriteFailure, and the round's NoEngineeringWrite gate does not fire (the tree hash changed).  The bound's cost is a potentially weaker artifact, not a failed round.",
   "disclosed_dr18_interaction": "the exit status is StepBudgetExceeded, which runtime::invoke::is_limits_exceeded accepts, so if the bound-cut artifact is not yet launchable the DR-18 wrap-up retry issues a SECOND Developer call (`if developer_limits && !developer_artifact_valid`).  The projections below do not include that second call; a live round must watch repair_retry_used / developer_wrap_up."
  }
 },
 "recordings": {
  "round4-iter-1": {
   "source": "evidence/cost/round4-iter-1.developer.attempt1.json",
   "model_calls": 69,
   "measured_total_tokens": 2626195,
   "measured_ratio_to_criterion": 1.7508,
   "recorded_exit_status": "RepeatedActionError",
   "first_project_write_call": 7,
   "project_write_calls": [
    7,
    8,
    9,
    13,
    14,
    18
   ],
   "scratch_write_calls": [],
   "first_declared_finish_call": 25,
   "max_call_count_under_criterion": 44,
   "prefix_at_that_call": 1476168,
   "prefix_at_next_call": 1521112
  },
  "round4-iter-2": {
   "source": "evidence/cost/round4-iter-2.developer.attempt1.json",
   "model_calls": 125,
   "measured_total_tokens": 13091431,
   "measured_ratio_to_criterion": 8.7276,
   "recorded_exit_status": "RepeatedActionError",
   "first_project_write_call": 33,
   "project_write_calls": [
    33,
    35,
    36,
    37,
    42,
    44,
    46,
    55,
    65,
    67,
    72
   ],
   "scratch_write_calls": [
    27,
    29,
    40,
    63,
    64,
    69,
    71,
    97,
    99,
    106,
    109,
    116
   ],
   "first_declared_finish_call": 58,
   "max_call_count_under_criterion": 40,
   "prefix_at_that_call": 1496626,
   "prefix_at_next_call": 1568638
  },
  "round4-iter-3": {
   "source": "evidence/cost/round4-iter-3.developer.attempt1.json",
   "model_calls": 102,
   "measured_total_tokens": 5223211,
   "measured_ratio_to_criterion": 3.4821,
   "recorded_exit_status": "RepeatedActionError",
   "first_project_write_call": 6,
   "project_write_calls": [
    6
   ],
   "scratch_write_calls": [
    50,
    70,
    73,
    74,
    80,
    84,
    86,
    90,
    93,
    97
   ],
   "first_declared_finish_call": 30,
   "max_call_count_under_criterion": 36,
   "prefix_at_that_call": 1452307,
   "prefix_at_next_call": 1502443
  },
  "livecost1-iter-1": {
   "source": "evidence/cost/livecost1-iter-1.developer.attempt1.json",
   "model_calls": 150,
   "measured_total_tokens": 3651120,
   "measured_ratio_to_criterion": 2.4341,
   "recorded_exit_status": "LimitsExceeded",
   "first_project_write_call": 6,
   "project_write_calls": [
    6,
    14,
    19,
    43
   ],
   "scratch_write_calls": [
    17
   ],
   "first_declared_finish_call": null,
   "max_call_count_under_criterion": 81,
   "prefix_at_that_call": 1484934,
   "prefix_at_next_call": 1511382
  },
  "live-completion1-iter-1": {
   "source": "runs/completion1/iter-1/traj/developer.attempt1.json",
   "model_calls": 150,
   "measured_total_tokens": 3527566,
   "measured_ratio_to_criterion": 2.3517,
   "recorded_exit_status": "LimitsExceeded",
   "first_project_write_call": 8,
   "project_write_calls": [
    8,
    26,
    40
   ],
   "scratch_write_calls": [],
   "first_declared_finish_call": null,
   "max_call_count_under_criterion": 78,
   "prefix_at_that_call": 1480801,
   "prefix_at_next_call": 1503171
  },
  "live-completion1-iter-2": {
   "source": "runs/completion1/iter-2/traj/developer.attempt1.json",
   "model_calls": 150,
   "measured_total_tokens": 3939027,
   "measured_ratio_to_criterion": 2.626,
   "recorded_exit_status": "LimitsExceeded",
   "first_project_write_call": 13,
   "project_write_calls": [
    13,
    63
   ],
   "scratch_write_calls": [],
   "first_declared_finish_call": null,
   "max_call_count_under_criterion": 74,
   "prefix_at_that_call": 1484574,
   "prefix_at_next_call": 1508821
  },
  "live-completion1-iter-3": {
   "source": "runs/completion1/iter-3/traj/developer.attempt1.json",
   "model_calls": 44,
   "measured_total_tokens": 803027,
   "measured_ratio_to_criterion": 0.5354,
   "recorded_exit_status": "StepBudgetExceeded",
   "first_project_write_call": null,
   "project_write_calls": [],
   "scratch_write_calls": [],
   "first_declared_finish_call": null,
   "max_call_count_under_criterion": 44,
   "prefix_at_that_call": 803027,
   "prefix_at_next_call": null
  }
 },
 "candidate_bounds": {
  "method": "cost at bound B = the recording's own prefix sum of extra.response.usage.total_tokens over calls 1..=B+1 (the guard allows B calls and bills one more).  This is a measured prefix sum, not a model: it reproduces the independent acceptance's maximum-prefix figures exactly.",
  "cross_check": "the same method reproduces the previous batch's independent figure (prompt tokens over calls 1..24 of round4-iter-1 = 579,603 = 2,544,563 - 1,964,960)",
  "rows": [
   {
    "bound_B": 25,
    "billed_model_calls": 26,
    "projected_cost_per_recording": {
     "round4-iter-1": {
      "billed_calls": 26,
      "cost": 705441,
      "ratio_to_criterion": 0.4703,
      "under_criterion": true
     },
     "round4-iter-2": {
      "billed_calls": 26,
      "cost": 684879,
      "ratio_to_criterion": 0.4566,
      "under_criterion": true
     },
     "round4-iter-3": {
      "billed_calls": 26,
      "cost": 971219,
      "ratio_to_criterion": 0.6475,
      "under_criterion": true
     },
     "livecost1-iter-1": {
      "billed_calls": 26,
      "cost": 382298,
      "ratio_to_criterion": 0.2549,
      "under_criterion": true
     },
     "live-completion1-iter-1": {
      "billed_calls": 26,
      "cost": 394761,
      "ratio_to_criterion": 0.2632,
      "under_criterion": true
     },
     "live-completion1-iter-2": {
      "billed_calls": 26,
      "cost": 427744,
      "ratio_to_criterion": 0.2852,
      "under_criterion": true
     },
     "live-completion1-iter-3": {
      "billed_calls": 26,
      "cost": 507705,
      "ratio_to_criterion": 0.3385,
      "under_criterion": true
     }
    },
    "call_count_only_failures_all_pass": true,
    "all_four_committed_recordings_pass": true,
    "cut_before_first_write_under_a_flat_reading": [
     "round4-iter-2"
    ]
   },
   {
    "bound_B": 30,
    "billed_model_calls": 31,
    "projected_cost_per_recording": {
     "round4-iter-1": {
      "billed_calls": 31,
      "cost": 909899,
      "ratio_to_criterion": 0.6066,
      "under_criterion": true
     },
     "round4-iter-2": {
      "billed_calls": 31,
      "cost": 885453,
      "ratio_to_criterion": 0.5903,
      "under_criterion": true
     },
     "round4-iter-3": {
      "billed_calls": 31,
      "cost": 1208548,
      "ratio_to_criterion": 0.8057,
      "under_criterion": true
     },
     "livecost1-iter-1": {
      "billed_calls": 31,
      "cost": 466141,
      "ratio_to_criterion": 0.3108,
      "under_criterion": true
     },
     "live-completion1-iter-1": {
      "billed_calls": 31,
      "cost": 491370,
      "ratio_to_criterion": 0.3276,
      "under_criterion": true
     },
     "live-completion1-iter-2": {
      "billed_calls": 31,
      "cost": 536946,
      "ratio_to_criterion": 0.358,
      "under_criterion": true
     },
     "live-completion1-iter-3": {
      "billed_calls": 31,
      "cost": 587322,
      "ratio_to_criterion": 0.3915,
      "under_criterion": true
     }
    },
    "call_count_only_failures_all_pass": true,
    "all_four_committed_recordings_pass": true,
    "cut_before_first_write_under_a_flat_reading": [
     "round4-iter-2"
    ]
   },
   {
    "bound_B": 33,
    "billed_model_calls": 34,
    "projected_cost_per_recording": {
     "round4-iter-1": {
      "billed_calls": 34,
      "cost": 1039504,
      "ratio_to_criterion": 0.693,
      "under_criterion": true
     },
     "round4-iter-2": {
      "billed_calls": 34,
      "cost": 1054857,
      "ratio_to_criterion": 0.7032,
      "under_criterion": true
     },
     "round4-iter-3": {
      "billed_calls": 34,
      "cost": 1354909,
      "ratio_to_criterion": 0.9033,
      "under_criterion": true
     },
     "livecost1-iter-1": {
      "billed_calls": 34,
      "cost": 519812,
      "ratio_to_criterion": 0.3465,
      "under_criterion": true
     },
     "live-completion1-iter-1": {
      "billed_calls": 34,
      "cost": 544208,
      "ratio_to_criterion": 0.3628,
      "under_criterion": true
     },
     "live-completion1-iter-2": {
      "billed_calls": 34,
      "cost": 595813,
      "ratio_to_criterion": 0.3972,
      "under_criterion": true
     },
     "live-completion1-iter-3": {
      "billed_calls": 34,
      "cost": 625848,
      "ratio_to_criterion": 0.4172,
      "under_criterion": true
     }
    },
    "call_count_only_failures_all_pass": true,
    "all_four_committed_recordings_pass": true,
    "cut_before_first_write_under_a_flat_reading": []
   },
   {
    "bound_B": 34,
    "billed_model_calls": 35,
    "projected_cost_per_recording": {
     "round4-iter-1": {
      "billed_calls": 35,
      "cost": 1084592,
      "ratio_to_criterion": 0.7231,
      "under_criterion": true
     },
     "round4-iter-2": {
      "billed_calls": 35,
      "cost": 1125195,
      "ratio_to_criterion": 0.7501,
      "under_criterion": true
     },
     "round4-iter-3": {
      "billed_calls": 35,
      "cost": 1403409,
      "ratio_to_criterion": 0.9356,
      "under_criterion": true
     },
     "livecost1-iter-1": {
      "billed_calls": 35,
      "cost": 538274,
      "ratio_to_criterion": 0.3588,
      "under_criterion": true
     },
     "live-completion1-iter-1": {
      "billed_calls": 35,
      "cost": 562413,
      "ratio_to_criterion": 0.3749,
      "under_criterion": true
     },
     "live-completion1-iter-2": {
      "billed_calls": 35,
      "cost": 614943,
      "ratio_to_criterion": 0.41,
      "under_criterion": true
     },
     "live-completion1-iter-3": {
      "billed_calls": 35,
      "cost": 639072,
      "ratio_to_criterion": 0.426,
      "under_criterion": true
     }
    },
    "call_count_only_failures_all_pass": true,
    "all_four_committed_recordings_pass": true,
    "cut_before_first_write_under_a_flat_reading": []
   },
   {
    "bound_B": 35,
    "billed_model_calls": 36,
    "projected_cost_per_recording": {
     "round4-iter-1": {
      "billed_calls": 36,
      "cost": 1127441,
      "ratio_to_criterion": 0.7516,
      "under_criterion": true
     },
     "round4-iter-2": {
      "billed_calls": 36,
      "cost": 1196549,
      "ratio_to_criterion": 0.7977,
      "under_criterion": true
     },
     "round4-iter-3": {
      "billed_calls": 36,
      "cost": 1452307,
      "ratio_to_criterion": 0.9682,
      "under_criterion": true
     },
     "livecost1-iter-1": {
      "billed_calls": 36,
      "cost": 558945,
      "ratio_to_criterion": 0.3726,
      "under_criterion": true
     },
     "live-completion1-iter-1": {
      "billed_calls": 36,
      "cost": 579120,
      "ratio_to_criterion": 0.3861,
      "under_criterion": true
     },
     "live-completion1-iter-2": {
      "billed_calls": 36,
      "cost": 633893,
      "ratio_to_criterion": 0.4226,
      "under_criterion": true
     },
     "live-completion1-iter-3": {
      "billed_calls": 36,
      "cost": 654384,
      "ratio_to_criterion": 0.4363,
      "under_criterion": true
     }
    },
    "call_count_only_failures_all_pass": true,
    "all_four_committed_recordings_pass": true,
    "cut_before_first_write_under_a_flat_reading": []
   },
   {
    "bound_B": 36,
    "billed_model_calls": 37,
    "projected_cost_per_recording": {
     "round4-iter-1": {
      "billed_calls": 37,
      "cost": 1170703,
      "ratio_to_criterion": 0.7805,
      "under_criterion": true
     },
     "round4-iter-2": {
      "billed_calls": 37,
      "cost": 1274639,
      "ratio_to_criterion": 0.8498,
      "under_criterion": true
     },
     "round4-iter-3": {
      "billed_calls": 37,
      "cost": 1502443,
      "ratio_to_criterion": 1.0016,
      "under_criterion": false
     },
     "livecost1-iter-1": {
      "billed_calls": 37,
      "cost": 575782,
      "ratio_to_criterion": 0.3839,
      "under_criterion": true
     },
     "live-completion1-iter-1": {
      "billed_calls": 37,
      "cost": 595190,
      "ratio_to_criterion": 0.3968,
      "under_criterion": true
     },
     "live-completion1-iter-2": {
      "billed_calls": 37,
      "cost": 653065,
      "ratio_to_criterion": 0.4354,
      "under_criterion": true
     },
     "live-completion1-iter-3": {
      "billed_calls": 37,
      "cost": 669039,
      "ratio_to_criterion": 0.446,
      "under_criterion": true
     }
    },
    "call_count_only_failures_all_pass": false,
    "all_four_committed_recordings_pass": false,
    "cut_before_first_write_under_a_flat_reading": []
   },
   {
    "bound_B": 37,
    "billed_model_calls": 38,
    "projected_cost_per_recording": {
     "round4-iter-1": {
      "billed_calls": 38,
      "cost": 1213882,
      "ratio_to_criterion": 0.8093,
      "under_criterion": true
     },
     "round4-iter-2": {
      "billed_calls": 38,
      "cost": 1350523,
      "ratio_to_criterion": 0.9003,
      "under_criterion": true
     },
     "round4-iter-3": {
      "billed_calls": 38,
      "cost": 1553323,
      "ratio_to_criterion": 1.0355,
      "under_criterion": false
     },
     "livecost1-iter-1": {
      "billed_calls": 38,
      "cost": 597869,
      "ratio_to_criterion": 0.3986,
      "under_criterion": true
     },
     "live-completion1-iter-1": {
      "billed_calls": 38,
      "cost": 611418,
      "ratio_to_criterion": 0.4076,
      "under_criterion": true
     },
     "live-completion1-iter-2": {
      "billed_calls": 38,
      "cost": 670920,
      "ratio_to_criterion": 0.4473,
      "under_criterion": true
     },
     "live-completion1-iter-3": {
      "billed_calls": 38,
      "cost": 684829,
      "ratio_to_criterion": 0.4566,
      "under_criterion": true
     }
    },
    "call_count_only_failures_all_pass": false,
    "all_four_committed_recordings_pass": false,
    "cut_before_first_write_under_a_flat_reading": []
   },
   {
    "bound_B": 40,
    "billed_model_calls": 41,
    "projected_cost_per_recording": {
     "round4-iter-1": {
      "billed_calls": 41,
      "cost": 1343382,
      "ratio_to_criterion": 0.8956,
      "under_criterion": true
     },
     "round4-iter-2": {
      "billed_calls": 41,
      "cost": 1568638,
      "ratio_to_criterion": 1.0458,
      "under_criterion": false
     },
     "round4-iter-3": {
      "billed_calls": 41,
      "cost": 1706305,
      "ratio_to_criterion": 1.1375,
      "under_criterion": false
     },
     "livecost1-iter-1": {
      "billed_calls": 41,
      "cost": 663014,
      "ratio_to_criterion": 0.442,
      "under_criterion": true
     },
     "live-completion1-iter-1": {
      "billed_calls": 41,
      "cost": 677842,
      "ratio_to_criterion": 0.4519,
      "under_criterion": true
     },
     "live-completion1-iter-2": {
      "billed_calls": 41,
      "cost": 720488,
      "ratio_to_criterion": 0.4803,
      "under_criterion": true
     },
     "live-completion1-iter-3": {
      "billed_calls": 41,
      "cost": 742171,
      "ratio_to_criterion": 0.4948,
      "under_criterion": true
     }
    },
    "call_count_only_failures_all_pass": false,
    "all_four_committed_recordings_pass": false,
    "cut_before_first_write_under_a_flat_reading": []
   },
   {
    "bound_B": 43,
    "billed_model_calls": 44,
    "projected_cost_per_recording": {
     "round4-iter-1": {
      "billed_calls": 44,
      "cost": 1476168,
      "ratio_to_criterion": 0.9841,
      "under_criterion": true
     },
     "round4-iter-2": {
      "billed_calls": 44,
      "cost": 1826312,
      "ratio_to_criterion": 1.2175,
      "under_criterion": false
     },
     "round4-iter-3": {
      "billed_calls": 44,
      "cost": 1859704,
      "ratio_to_criterion": 1.2398,
      "under_criterion": false
     },
     "livecost1-iter-1": {
      "billed_calls": 44,
      "cost": 740918,
      "ratio_to_criterion": 0.4939,
      "under_criterion": true
     },
     "live-completion1-iter-1": {
      "billed_calls": 44,
      "cost": 747420,
      "ratio_to_criterion": 0.4983,
      "under_criterion": true
     },
     "live-completion1-iter-2": {
      "billed_calls": 44,
      "cost": 787732,
      "ratio_to_criterion": 0.5252,
      "under_criterion": true
     },
     "live-completion1-iter-3": {
      "billed_calls": 44,
      "cost": 803027,
      "ratio_to_criterion": 0.5354,
      "under_criterion": true
     }
    },
    "call_count_only_failures_all_pass": false,
    "all_four_committed_recordings_pass": false,
    "cut_before_first_write_under_a_flat_reading": []
   },
   {
    "bound_B": 44,
    "billed_model_calls": 45,
    "projected_cost_per_recording": {
     "round4-iter-1": {
      "billed_calls": 45,
      "cost": 1521112,
      "ratio_to_criterion": 1.0141,
      "under_criterion": false
     },
     "round4-iter-2": {
      "billed_calls": 45,
      "cost": 1916147,
      "ratio_to_criterion": 1.2774,
      "under_criterion": false
     },
     "round4-iter-3": {
      "billed_calls": 45,
      "cost": 1910924,
      "ratio_to_criterion": 1.2739,
      "under_criterion": false
     },
     "livecost1-iter-1": {
      "billed_calls": 45,
      "cost": 760071,
      "ratio_to_criterion": 0.5067,
      "under_criterion": true
     },
     "live-completion1-iter-1": {
      "billed_calls": 45,
      "cost": 770893,
      "ratio_to_criterion": 0.5139,
      "under_criterion": true
     },
     "live-completion1-iter-2": {
      "billed_calls": 45,
      "cost": 811679,
      "ratio_to_criterion": 0.5411,
      "under_criterion": true
     },
     "live-completion1-iter-3": {
      "billed_calls": 44,
      "cost": 803027,
      "ratio_to_criterion": 0.5354,
      "under_criterion": true
     }
    },
    "call_count_only_failures_all_pass": false,
    "all_four_committed_recordings_pass": false,
    "cut_before_first_write_under_a_flat_reading": []
   },
   {
    "bound_B": 50,
    "billed_model_calls": 51,
    "projected_cost_per_recording": {
     "round4-iter-1": {
      "billed_calls": 51,
      "cost": 1790635,
      "ratio_to_criterion": 1.1938,
      "under_criterion": false
     },
     "round4-iter-2": {
      "billed_calls": 51,
      "cost": 2510296,
      "ratio_to_criterion": 1.6735,
      "under_criterion": false
     },
     "round4-iter-3": {
      "billed_calls": 51,
      "cost": 2221134,
      "ratio_to_criterion": 1.4808,
      "under_criterion": false
     },
     "livecost1-iter-1": {
      "billed_calls": 51,
      "cost": 871677,
      "ratio_to_criterion": 0.5811,
      "under_criterion": true
     },
     "live-completion1-iter-1": {
      "billed_calls": 51,
      "cost": 892220,
      "ratio_to_criterion": 0.5948,
      "under_criterion": true
     },
     "live-completion1-iter-2": {
      "billed_calls": 51,
      "cost": 932173,
      "ratio_to_criterion": 0.6214,
      "under_criterion": true
     },
     "live-completion1-iter-3": {
      "billed_calls": 44,
      "cost": 803027,
      "ratio_to_criterion": 0.5354,
      "under_criterion": true
     }
    },
    "call_count_only_failures_all_pass": false,
    "all_four_committed_recordings_pass": false,
    "cut_before_first_write_under_a_flat_reading": []
   },
   {
    "bound_B": 58,
    "billed_model_calls": 59,
    "projected_cost_per_recording": {
     "round4-iter-1": {
      "billed_calls": 59,
      "cost": 2160344,
      "ratio_to_criterion": 1.4402,
      "under_criterion": false
     },
     "round4-iter-2": {
      "billed_calls": 59,
      "cost": 3408286,
      "ratio_to_criterion": 2.2722,
      "under_criterion": false
     },
     "round4-iter-3": {
      "billed_calls": 59,
      "cost": 2647536,
      "ratio_to_criterion": 1.765,
      "under_criterion": false
     },
     "livecost1-iter-1": {
      "billed_calls": 59,
      "cost": 1017153,
      "ratio_to_criterion": 0.6781,
      "under_criterion": true
     },
     "live-completion1-iter-1": {
      "billed_calls": 59,
      "cost": 1051630,
      "ratio_to_criterion": 0.7011,
      "under_criterion": true
     },
     "live-completion1-iter-2": {
      "billed_calls": 59,
      "cost": 1099515,
      "ratio_to_criterion": 0.733,
      "under_criterion": true
     },
     "live-completion1-iter-3": {
      "billed_calls": 44,
      "cost": 803027,
      "ratio_to_criterion": 0.5354,
      "under_criterion": true
     }
    },
    "call_count_only_failures_all_pass": false,
    "all_four_committed_recordings_pass": false,
    "cut_before_first_write_under_a_flat_reading": []
   },
   {
    "bound_B": 64,
    "billed_model_calls": 65,
    "projected_cost_per_recording": {
     "round4-iter-1": {
      "billed_calls": 65,
      "cost": 2438264,
      "ratio_to_criterion": 1.6255,
      "under_criterion": false
     },
     "round4-iter-2": {
      "billed_calls": 65,
      "cost": 4127124,
      "ratio_to_criterion": 2.7514,
      "under_criterion": false
     },
     "round4-iter-3": {
      "billed_calls": 65,
      "cost": 2972690,
      "ratio_to_criterion": 1.9818,
      "under_criterion": false
     },
     "livecost1-iter-1": {
      "billed_calls": 65,
      "cost": 1131094,
      "ratio_to_criterion": 0.7541,
      "under_criterion": true
     },
     "live-completion1-iter-1": {
      "billed_calls": 65,
      "cost": 1176842,
      "ratio_to_criterion": 0.7846,
      "under_criterion": true
     },
     "live-completion1-iter-2": {
      "billed_calls": 65,
      "cost": 1259909,
      "ratio_to_criterion": 0.8399,
      "under_criterion": true
     },
     "live-completion1-iter-3": {
      "billed_calls": 44,
      "cost": 803027,
      "ratio_to_criterion": 0.5354,
      "under_criterion": true
     }
    },
    "call_count_only_failures_all_pass": false,
    "all_four_committed_recordings_pass": false,
    "cut_before_first_write_under_a_flat_reading": []
   },
   {
    "bound_B": 81,
    "billed_model_calls": 82,
    "projected_cost_per_recording": {
     "round4-iter-1": {
      "billed_calls": 69,
      "cost": 2626195,
      "ratio_to_criterion": 1.7508,
      "under_criterion": false
     },
     "round4-iter-2": {
      "billed_calls": 82,
      "cost": 6489040,
      "ratio_to_criterion": 4.326,
      "under_criterion": false
     },
     "round4-iter-3": {
      "billed_calls": 82,
      "cost": 3953474,
      "ratio_to_criterion": 2.6356,
      "under_criterion": false
     },
     "livecost1-iter-1": {
      "billed_calls": 82,
      "cost": 1511382,
      "ratio_to_criterion": 1.0076,
      "under_criterion": false
     },
     "live-completion1-iter-1": {
      "billed_calls": 82,
      "cost": 1569048,
      "ratio_to_criterion": 1.046,
      "under_criterion": false
     },
     "live-completion1-iter-2": {
      "billed_calls": 82,
      "cost": 1686529,
      "ratio_to_criterion": 1.1244,
      "under_criterion": false
     },
     "live-completion1-iter-3": {
      "billed_calls": 44,
      "cost": 803027,
      "ratio_to_criterion": 0.5354,
      "under_criterion": true
     }
    },
    "call_count_only_failures_all_pass": false,
    "all_four_committed_recordings_pass": false,
    "cut_before_first_write_under_a_flat_reading": []
   },
   {
    "bound_B": 150,
    "billed_model_calls": 151,
    "projected_cost_per_recording": {
     "round4-iter-1": {
      "billed_calls": 69,
      "cost": 2626195,
      "ratio_to_criterion": 1.7508,
      "under_criterion": false
     },
     "round4-iter-2": {
      "billed_calls": 125,
      "cost": 13091431,
      "ratio_to_criterion": 8.7276,
      "under_criterion": false
     },
     "round4-iter-3": {
      "billed_calls": 102,
      "cost": 5223211,
      "ratio_to_criterion": 3.4821,
      "under_criterion": false
     },
     "livecost1-iter-1": {
      "billed_calls": 150,
      "cost": 3651120,
      "ratio_to_criterion": 2.4341,
      "under_criterion": false
     },
     "live-completion1-iter-1": {
      "billed_calls": 150,
      "cost": 3527566,
      "ratio_to_criterion": 2.3517,
      "under_criterion": false
     },
     "live-completion1-iter-2": {
      "billed_calls": 150,
      "cost": 3939027,
      "ratio_to_criterion": 2.626,
      "under_criterion": false
     },
     "live-completion1-iter-3": {
      "billed_calls": 44,
      "cost": 803027,
      "ratio_to_criterion": 0.5354,
      "under_criterion": true
     }
    },
    "call_count_only_failures_all_pass": false,
    "all_four_committed_recordings_pass": false,
    "cut_before_first_write_under_a_flat_reading": []
   }
  ]
 },
 "bound_chosen": {
  "value": 35,
  "config_key": "agent.post_write_step_limit",
  "config_key_path": "config/hoh.yaml",
  "billed_model_calls": 36,
  "constraint_1_not_cut_before_the_write": {
   "structurally_satisfied": "the bound is consulted only while `artifact_written` is true (the same flag the write-guaranteed exit uses), so no bound can cut a call before its counted write; any B satisfies this",
   "flat_reading": "if the number were instead applied as a flat total-call budget, B >= 33 would be required to clear round4-iter-2's first project write at call 33; B = 35 >= 33"
  },
  "constraint_2_under_the_criterion_for_the_recordings_that_fail_only_on_call_count": {
   "which_recordings": [
    "round4-iter-1",
    "round4-iter-3",
    "livecost1-iter-1"
   ],
   "binding_recording": "round4-iter-3",
   "arithmetic": "prefix(36) = 1,452,307 (0.968x) is the largest prefix under the criterion for that recording, and a bound B bills B+1 calls, so B + 1 <= 36, i.e. B <= 35.  At B = 36 the same recording costs prefix(37) = 1,502,443 = 1.002x, over by 2,443 tokens.",
   "largest_b_making_all_three_pass": 35
  },
  "constraints_compatible": true,
  "feasible_window": "33, 34, 35 (lower end only under the flat reading)",
  "why_the_upper_end": "35 is the largest bound that meets both constraints, so it leaves the producing call the most post-write calls; 25 and 30 also pass but cut every recording earlier and can only buy a weaker artifact for no measured benefit.  No measured variance exists to justify inventing a smaller safety factor (single provider, single model, one project shape).",
  "residual_headroom_on_the_binding_recording": {
   "tokens": 47693,
   "fraction_of_the_criterion": 0.0318
  }
 },
 "projected_effect_at_the_chosen_bound": {
  "bound_alone_holding_the_recorded_call_sequence_fixed": {
   "round4-iter-1": {
    "ends_at_call": 36,
    "cost": 1127441,
    "ratio": 0.752
   },
   "round4-iter-2": {
    "ends_at_call": 36,
    "cost": 1196549,
    "ratio": 0.798
   },
   "round4-iter-3": {
    "ends_at_call": 36,
    "cost": 1452307,
    "ratio": 0.968
   },
   "livecost1-iter-1": {
    "ends_at_call": 36,
    "cost": 558945,
    "ratio": 0.373
   },
   "live-completion1-iter-1": {
    "ends_at_call": 36,
    "cost": 579120,
    "ratio": 0.386
   },
   "live-completion1-iter-2": {
    "ends_at_call": 36,
    "cost": 633893,
    "ratio": 0.423
   },
   "live-completion1-iter-3": {
    "ends_at_call": 44,
    "cost": 803027,
    "ratio": 0.535,
    "note": "wrote nothing, so the post-write bound never applies: it still ends on the unwritten allowance at 44 calls and still fails the round with NoEngineeringWrite"
   }
  },
  "bound_or_the_recorded_first_legitimate_exit": {
   "method": "the call ends at min(the bound's B+1 = 36, the recording's first completion request after its first write); where the role declares earlier the exit is cheaper than the bound and the bound does not bite",
   "rows": {
    "round4-iter-1": {
     "ends_at_call": 25,
     "cost": 665666,
     "ratio_to_criterion": 0.4438,
     "under_criterion": true
    },
    "round4-iter-2": {
     "ends_at_call": 36,
     "cost": 1196549,
     "ratio_to_criterion": 0.7977,
     "under_criterion": true
    },
    "round4-iter-3": {
     "ends_at_call": 30,
     "cost": 1160900,
     "ratio_to_criterion": 0.7739,
     "under_criterion": true
    },
    "livecost1-iter-1": {
     "ends_at_call": 36,
     "cost": 558945,
     "ratio_to_criterion": 0.3726,
     "under_criterion": true
    },
    "live-completion1-iter-1": {
     "ends_at_call": 36,
     "cost": 579120,
     "ratio_to_criterion": 0.3861,
     "under_criterion": true
    },
    "live-completion1-iter-2": {
     "ends_at_call": 36,
     "cost": 633893,
     "ratio_to_criterion": 0.4226,
     "under_criterion": true
    },
    "live-completion1-iter-3": {
     "ends_at_call": 36,
     "cost": 654384,
     "ratio_to_criterion": 0.4363,
     "under_criterion": true
    }
   }
  },
  "what_the_bound_rescues_that_the_exit_alone_does_not": {
   "round4-iter-2": "its first legitimate exit is call 58 and costs 3,295,369 (2.197x) - it fails on content, not only on call count - and the bound is what brings it to 1,196,549 (0.798x)",
   "live_post_fix_calls": "completion1/iter-1 and iter-2 never ran the completion command at all (150 calls, 2.352x / 2.626x); with the bound they end at 36 calls, 0.386x / 0.423x"
  }
 },
 "tests": {
  "new_files": [
   "tests/post_write_bound.rs (6 tests: 4 configuration arithmetic + 2 production-path MiniHarness tests against a 127.0.0.1 fake chat endpoint, the same pattern tests/harness_cap_wiring.rs uses)",
   "src/harness/guard.rs #[cfg(test)] (5 new tests + 1 rewritten note test that keeps every previous assertion)"
  ],
  "existing_tests_removed_or_weakened": [],
  "red": [
   {
    "phase": "increment 1 - the configuration does not carry the bound",
    "command": "cargo test --offline --test post_write_bound",
    "literal_exit_code": 101,
    "summary": "0 passed; 2 failed; 0 ignored; 0 measured; 0 filtered out",
    "failures": [
     "the_shipped_configuration_bounds_a_call_that_has_written: panicked at tests\\post_write_bound.rs:59:5: assertion `left == right` failed: a call that has written its artifact must run under the post-write bound, not the flat 150 -- left: 150, right: 35",
     "the_configuration_states_the_post_write_bound: panicked at tests\\post_write_bound.rs:80:5: config/hoh.yaml must ship the post-write bound as a named number, not leave it implicit"
    ]
   },
   {
    "phase": "increment 1 controls - against a raw-bound implementation (written_step_limit() returned post_write_step_limit unchanged); the controls exist to pin '0 disables' and 'capped by the flat limit'",
    "command": "cargo test --offline --test post_write_bound",
    "literal_exit_code": 101,
    "summary": "2 passed; 2 failed; 0 ignored; 0 measured; 0 filtered out",
    "failures": [
     "a_zero_post_write_bound_disables_the_ceiling: panicked at tests\\post_write_bound.rs:107:5: assertion `left == right` failed: 0 means no post-write ceiling, so the written budget is the flat limit -- left: 0, right: 150",
     "the_post_write_bound_is_capped_by_the_flat_limit: panicked at tests\\post_write_bound.rs:132:5: assertion `left == right` failed: a post-write bound above the flat limit must not raise the ceiling -- left: 35, right: 20"
    ]
   },
   {
    "phase": "increment 2 - the configuration number does not reach the guard (mini.rs does not pass it, the guard does not consult it)",
    "command": "cargo test --offline --test post_write_bound",
    "literal_exit_code": 101,
    "summary": "5 passed; 1 failed; 0 ignored; 0 measured; 0 filtered out",
    "failures": [
     "a_call_that_has_written_ends_at_the_post_write_bound: panicked at tests\\post_write_bound.rs:406:5: assertion `left == right` failed: a written call must be cut by the post-write bound (exit_status = LimitsExceeded) -- left: \"LimitsExceeded\" (mini's flat backstop of 8 calls), right: \"StepBudgetExceeded\""
    ],
    "why_it_is_the_claimed_reason": "the written call ran to mini's own flat step_limit instead of the post-write bound; the unwritten control in the same command passed, which is what shows the bound (not the command or the fixture) was missing"
   },
   {
    "phase": "guard boundary - the guard's own budget arithmetic ignored the wired bound (temporary mutation of WriteGuardEnvironment::limits() to pass post_write_step_limit: 0)",
    "command": "cargo test --offline --lib harness::guard::tests",
    "literal_exit_code": 101,
    "summary": "32 passed; 2 failed; 0 ignored; 0 measured; 417 filtered out",
    "failures": [
     "the_post_write_bound_applies_only_once_the_call_has_written: panicked at src\\harness\\guard.rs:1460:9: assertion `left == right` failed -- left: 150, right: 35",
     "the_post_write_bound_is_enforced_at_the_step_it_names: panicked at src\\harness\\guard.rs:1527:18: the call after the post-write bound must be refused: Output { output: \"shell output\", returncode: 0, exception_info: \"\", extra: {} }"
    ]
   }
  ],
  "green": [
   {
    "command": "cargo test --offline --test post_write_bound",
    "literal_exit_code": 0,
    "summary": "6 passed; 0 failed; 0 ignored; 0 measured; 0 filtered out"
   },
   {
    "command": "cargo test --offline --lib harness::guard::tests",
    "literal_exit_code": 0,
    "summary": "34 passed; 0 failed; 0 ignored; 0 measured; 417 filtered out"
   }
  ],
  "added_after_statement_of_green": [
   "the five guard unit tests use the new builder `with_post_write_step_limit`, so before the guard had it they could not compile; their red is the guard-boundary red above, reproduced by mutating WriteGuardEnvironment::limits() to drop the value - the two enforcement tests then fail with `left: 150, right: 35` and `the call after the post-write bound must be refused`.",
   "the two configuration control tests (zero disables; capped by the flat limit) cannot compile before the field exists either; their red is the increment-1 control red above (`left: 0, right: 150` and `left: 35, right: 20`)."
  ]
 },
 "shell_write_risk": {
  "disclosure": "the guard's `artifact_written` counts a successful `HOH_WRITE_FILE` directive to a path outside [.hoh/, .git/, target/], while the round measures the artifact with a before/after tree hash over [.hoh, .git, target].  A role that changes the project with a plain shell command satisfies the round but not the guard, so its completion request is refused (D315) and its call ends on the unwritten allowance.",
  "does_this_change_make_it_better_or_worse": "strictly neutral on that shape, and it does not widen it: the post-write bound is consulted only while `artifact_written` is true, so a shell-writing call never sees it and keeps the unwritten 43 exactly as before.  Pinned by `the_unwritten_guard_is_untouched_by_the_post_write_bound` (cut at 43, 44 billed calls) and by the MiniHarness control `a_call_that_has_not_written_keeps_the_unwritten_allowance` (5 -> 6 calls while the bound is 3).",
  "what_is_newly_at_risk": "the lever's efficacy now depends on the live model using the write directive: if a Developer writes the project only through the shell, the bound never engages and the call still spends 44 calls (and still fails the round with NoEngineeringWrite for the empty shape, or produces a refusing, `StepBudgetExceeded`-ended call for the shell-writing shape).  The recorded evidence says the directive is used (first writes at calls 7/33/6/6 and 8/13 all carry extra.hoh_write_path), but the base rate of shell-side project writes is unmeasured - the previous acceptance's D2 records four legacy recordings that declare with zero guard-visible writes, and all four predate the write directive.",
  "second_new_risk": "a bound-cut call whose artifact is not yet launchable triggers the DR-18 wrap-up retry (a second Developer call, step_limit = min(wrap_up_steps, 30) = 25), a cost the projections do not include; the recorded live round's artifacts were launchable well before call 36, but only a live round measures this.",
  "what_a_live_round_must_watch": [
   "whether the Developer's call carries a counted extra.hoh_write_path at all, and at which call (if it never does, the bound never engaged and the criterion was not moved)",
   "the count of extra.hoh_exit_refused observations - the base rate of refused completions, which is the shell-write/early-exit proxy the corpus cannot supply",
   "the call's billed model count and its own usage total, against the 36-call / 1.45 M bound projection for the binding recording (3.2 % headroom)",
   "whether the bound-cut artifact is still launchable (artifact_valid, first battery pass launchable, src/game.rs bytes) and whether repair_retry_used / developer_wrap_up fired",
   "the interaction with the wrap-up band: agent.wrap_up_steps is 25, so under a 35-call post-write bound most of the call is nominally 'wrap-up'; watch whether the Developer writes earlier than the recorded call 33, later, or not at all"
  ]
 },
 "gate": {
  "build_dir": "E:/pwb-target (this batch's own; the repository's own target/ was not used)",
  "baseline_on_the_untouched_tree_same_build_dir": {
   "command": "cargo test --offline",
   "literal_exit_code": 0,
   "passed": 813,
   "failed": 0,
   "ignored": 6,
   "listed": 819,
   "test_result_lines": 61,
   "compiler_warning_lines": 0
  },
  "command": "cargo test --offline",
  "literal_exit_code": 0,
  "passed": 824,
  "failed": 0,
  "ignored": 6,
  "listed": 830,
  "test_result_lines": 62,
  "compiler_warning_lines": 0,
  "error_lines": 0,
  "delta": "exactly the 11 new tests: 813 -> 824 passed, 819 -> 830 listed (6 integration + 5 guard unit); nothing removed or weakened",
  "list_command": "cargo test --offline -- --list",
  "list_exit_code": 0,
  "list_count": 830,
  "list_ignored_command": "cargo test --offline -- --list --ignored",
  "list_ignored_exit_code": 0,
  "list_ignored_count": 6,
  "fmt_command": "cargo fmt --all --check",
  "fmt_literal_exit_code": 0,
  "fmt_output_bytes": 0,
  "timing_sensitive_tests": "none failed in any run; no re-run was needed"
 },
 "disk": {
  "free_before_build": "F: 8.2 GiB available (100% used); E: 566 GiB available; D: 53 GiB; C: 34 GiB",
  "build_dir": "E:/pwb-target on E:",
  "deletions": "none - no file was deleted and no rm -rf or wildcard deletion was used",
  "repository_paths_written": [
   "src/config.rs",
   "config/hoh.yaml",
   "src/harness/guard.rs",
   "src/harness/mini.rs",
   "tests/post_write_bound.rs (new)",
   "DECISIONS.md (appended, D316; prefix byte-identical, grew by exactly the entry plus one newline)",
   ".spec/bevy/POST-WRITE-BOUND-REPORT.md (this report)"
  ]
 },
 "constraints": {
  "round_run": false,
  "model_call_made": false,
  "engine_started": false,
  "api_key_created_copied_or_printed": false,
  "evidence_registry_battery_liveness_gitattributes_or_frozen_document_modified": false,
  "runs_directory_written": false,
  "decisions_md_appended_only": true,
  "rm_rf_or_wildcard_deletion_used": false,
  "path_constructed_from_an_unexpanded_variable": false,
  "git_checkout_double_dash_used": false,
  "committed_or_pushed": false,
  "branch": "bevy-core",
  "helper_scripts_location": "E:/pwb/ (outside the repository; every script landed through a file write, never through multi-line Python on a shell command line)",
  "one_test_process_at_a_time": true,
  "free_disk_checked_before_building": true
 },
 "measured_vs_inferred": {
  "measured": [
   "every guard/config threshold quoted above is read out of the working tree, and config/hoh.yaml",
   "every recording figure is the recording's own extra.response.usage.total_tokens, prefix-summed; every write call is the guard's own extra.hoh_write_path observation with returncode 0, split by the same exclusion prefixes ArtifactKind::counts uses",
   "the red and green literal exit codes, summaries and panic payloads are the cargo runs quoted above, in this batch's own build directory",
   "the gate numbers are the two full runs, both --list forms and cargo fmt quoted above",
   "the off-by-one (bound B bills B+1 calls) is both derived from `steps > budget`+CountingModel::query and confirmed by the recorded 44-call StepBudgetExceeded at budget 43"
  ],
  "inferred": [
   "that a live Developer call cut at 36 calls costs what the recorded prefix to call 36 costs.  The bound cannot change the tokens of calls 1..36 (they are already recorded), but it does change what the model does next, which no offline arithmetic sees",
   "that the recorded pre-fix declarations (calls 25/58/30) would become executable completion commands post-fix at the same call; the recordings show the declaration, not post-fix behaviour",
   "that a bound-cut artifact stays launchable, and therefore that the DR-18 wrap-up retry does not fire",
   "the base rate of shell-side project writes, and therefore whether the bound's precondition (a counted directive write) is met live"
  ]
 },
 "single_most_important_thing": "The bound is measured and the arithmetic is tight at exactly one point: round4-iter-3 at 36 billed calls costs 1,452,307 tokens, 3.2 % under the criterion, and one call later costs 1,502,443 - 2,443 tokens over.  So 35 is the largest bound that passes and the margin is thin; the live round must read the Developer call's own usage and billed call count against the 36-call projection, watch whether the call carries a counted HOH_WRITE_FILE write at all (the bound never engages without one), and watch whether a bound-cut artifact is still launchable, because if it is not, the DR-18 wrap-up retry adds a second Developer call that no projection here includes."
}
```

# POST-WRITE-BOUND-REPORT - a call that has written its engineering file ends at the bound

The machine-readable block above is `json.dumps(..., indent=1, ensure_ascii=False)` output written by
`E:/pwb/report.py` and then **parsed back out of this written file**; the parse is the last thing the
generator does and it fails unless the block round-trips.  Every helper script lives outside the
repository at `E:/pwb/`.  **No round was run, no model call was made, no engine was started, no real
credential was read, created or printed.**  Nothing under `evidence/**`, `runs/**`, the registry, the
battery, the liveness step, `.gitattributes` or any frozen document was touched; `DECISIONS.md` was
**appended only** (D316, prefix byte-identical, growth exactly the entry plus one newline), and nothing
was committed or pushed.

## 1. The mechanism, quoted from the code

**A step is a model call.**  `src/harness/compact.rs:302` (`CountingModel::query`) runs
`self.progress.steps.increment();` before forwarding the request, and `src/harness/mini.rs` hands that
same `StepCounter` to the guard with `.sharing_steps(steps)`.  The unit matters: round 4's first attempt
counted the guard's *actions*, so a call whose responses carried 44 actions was cut after 30 model calls
against a budget its own prompt stated as 43.

**Where the budget is computed** (`src/config.rs`, `AgentLimits::effective_step_limit`).  Before this
batch:

```rust
if has_written || self.steps_per_artifact == 0 { return self.step_limit; }
let per_artifact = (self.step_limit / self.steps_per_artifact).max(1);
(self.wrap_up_steps + per_artifact).max(self.wrap_up_steps)
```

After this batch:

```rust
if self.steps_per_artifact == 0 { return self.step_limit; }
if has_written { return self.written_step_limit(); }   // min(post_write_step_limit, step_limit)
let per_artifact = (self.step_limit / self.steps_per_artifact).max(1);
(self.wrap_up_steps + per_artifact).max(self.wrap_up_steps)
```

With `config/hoh.yaml`'s `step_limit: 150`, `wrap_up_steps: 25`, `steps_per_artifact: 8` and the new
`post_write_step_limit: 35`:

| value | expression | result |
|---|---|---|
| before a write | `25 + max(150/8, 1)` | **43 model calls** (unchanged) |
| after a write, before this batch | `step_limit` | **150 model calls** |
| after a write, after this batch | `min(35, 150)` | **35 model calls** |

**Where it is enforced** (`src/harness/guard.rs`, `step_budget_exceeded`):

```rust
if self.step_limit == 0 { return None; }
self.step_counter.as_ref()?;
let budget = self.effective_step_budget().min(self.step_limit);
let steps = self.steps();
if steps > budget { Some(FailFast::StepBudget { steps, budget }) } else { None }
```

called as the first statement of `WriteGuardEnvironment::execute`.  `steps > budget` means **exactly
`budget` model calls may act and the `budget + 1`-th is billed and then refused**, so a bound `B` costs
the prefix sum over calls `1..=B+1`.  That off-by-one is not a deduction: the unwritten budget of 43
produced **44** billed calls and `StepBudgetExceeded` in `runs/completion1/iter-3` (44 calls, 803,027
tokens), and the new guard test `the_post_write_bound_is_enforced_at_the_step_it_names` asserts
`steps == 36` against a bound of 35.

**The other budgets are untouched**: `artifact_write_budget_seconds: 900`,
`artifact_write_budget_tokens: 1500000`, `max_action_failures: 3`, `max_repeated_actions: 15`,
`wall_time_limit_seconds: 3600`, `max_consecutive_format_errors: 3`, `repair_steps: 60`, mini's flat
`step_limit: 150`, and the round's `NoEngineeringWrite` gate.  This change *adds* a second, tighter
allowance that applies only once the write exists; no negative guard was relaxed.

## 2. What each recording first wrote at, and what each bound costs

The write call is the guard's own `extra.hoh_write_path` observation (returncode 0) attributed to the
model call that produced it, split into project/scratch by the same exclusion prefixes
`ArtifactKind::counts` uses.

| recording | calls | measured tokens | ratio | first project write | project writes | scratch writes | max calls under 1.5 M | tokens there | one call later |
|---|---|---|---|---|---|---|---|---|---|
| round4-iter-1 | 69 | 2,626,195 | 1.751x | **7** | 7,8,9,13,14,18 | - | 44 | 1,476,168 | 1,521,112 |
| round4-iter-2 | 125 | 13,091,431 | 8.728x | **33** | 33,35,36,37,42,44,46,55,65,67,72 | 27,29,40,63,64,69,71,97,99,106,109,116 | 40 | 1,496,626 | 1,568,638 |
| round4-iter-3 | 102 | 5,223,211 | 3.482x | **6** | 6 | 10 scratch writes | 36 | 1,452,307 | 1,502,443 |
| livecost1-iter-1 | 150 | 3,651,120 | 2.434x | **6** | 6,14,19,43 | 1 | 81 | 1,484,934 | 1,511,382 |
| live completion1/iter-1 | 150 | 3,527,566 | 2.352x | **8** | 3 project writes | - | 78 | 1,480,801 | 1,503,171 |
| live completion1/iter-2 | 150 | 3,939,027 | 2.626x | **13** | 2 project writes | - | 74 | 1,484,574 | 1,508,821 |
| live completion1/iter-3 | 44 | 803,027 | 0.535x | **none** | 0 | scratch only | 44 | 803,027 | - |

These first-write calls reproduce the previous batch's independently accepted figures exactly
(`7 / 33 / 6 / 6` for the corpus, `8 / 13` for the live post-fix calls).  Note the shape the acceptance's
defect D1 warned about: **every** first write is at or before call 33, so a bound can only be a
post-write ceiling — and the recorded `round4-iter-2`, which wrote at call 33, is the one call where a
35-call ceiling leaves only three calls of room.

Candidate bounds, cost = the recording's own prefix sum at `B + 1` billed calls (`P` = under the
criterion, `F` = over):

| bound B | billed calls | r4-i1 | r4-i2 | r4-i3 | livecost1 | live-i1 | live-i2 | call-count-only failures pass | all four corpus pass | cut before write (flat reading) |
|---|---|---|---|---|---|---|---|---|---|---|
| 25 | 26 | 705,441 P | 684,879 P | 971,219 P | 382,298 P | 394,761 P | 427,744 P | yes | yes | round4-iter-2 |
| 30 | 31 | 909,899 P | 885,453 P | 1,208,548 P | 466,141 P | 491,370 P | 536,946 P | yes | yes | round4-iter-2 |
| 33 | 34 | 1,039,504 P | 1,054,857 P | 1,354,909 P | 519,812 P | 544,208 P | 595,813 P | yes | yes | none |
| 34 | 35 | 1,084,592 P | 1,125,195 P | 1,403,409 P | 538,274 P | 562,413 P | 614,943 P | yes | yes | none |
| 35 | 36 | 1,127,441 P | 1,196,549 P | 1,452,307 P | 558,945 P | 579,120 P | 633,893 P | yes | yes | none |
| 36 | 37 | 1,170,703 P | 1,274,639 P | 1,502,443 F | 575,782 P | 595,190 P | 653,065 P | **no** | **no** | none |
| 37 | 38 | 1,213,882 P | 1,350,523 P | 1,553,323 F | 597,869 P | 611,418 P | 670,920 P | **no** | **no** | none |
| 40 | 41 | 1,343,382 P | 1,568,638 F | 1,706,305 F | 663,014 P | 677,842 P | 720,488 P | **no** | **no** | none |
| 43 | 44 | 1,476,168 P | 1,826,312 F | 1,859,704 F | 740,918 P | 747,420 P | 787,732 P | **no** | **no** | none |
| 44 | 45 | 1,521,112 F | 1,916,147 F | 1,910,924 F | 760,071 P | 770,893 P | 811,679 P | **no** | **no** | none |
| 50 | 51 | 1,790,635 F | 2,510,296 F | 2,221,134 F | 871,677 P | 892,220 P | 932,173 P | **no** | **no** | none |
| 58 | 59 | 2,160,344 F | 3,408,286 F | 2,647,536 F | 1,017,153 P | 1,051,630 P | 1,099,515 P | **no** | **no** | none |
| 64 | 65 | 2,438,264 F | 4,127,124 F | 2,972,690 F | 1,131,094 P | 1,176,842 P | 1,259,909 P | **no** | **no** | none |
| 81 | 82 | 2,626,195 F | 6,489,040 F | 3,953,474 F | 1,511,382 F | 1,569,048 F | 1,686,529 F | **no** | **no** | none |
| 150 | 151 | 2,626,195 F | 13,091,431 F | 5,223,211 F | 3,651,120 F | 3,527,566 F | 3,939,027 F | **no** | **no** | none |

The "call-count-only failures" column is the constraint the task asked for: `round4-iter-1`,
`round4-iter-3` and `livecost1-iter-1`, the recordings that are over the criterion **only** because the
call kept going (at their own first legitimate exit they project to 0.444x / 0.774x, and `livecost1`
never declared at all).  `round4-iter-2` is *not* in that set: its first legitimate exit is call 58 and
still costs 3,295,369 (2.197x), so it fails on content too.

## 3. The bound chosen, and the arithmetic

**`agent.post_write_step_limit: 35`** — 36 billed model calls.

* **"Not cut before its write."**  For a post-write budget this is *structural*: the value is consulted
  only while `artifact_written` is true, the same flag the write-guaranteed exit uses, so no value of
  this key can cut a call before its counted write.  Even under a flat reading of the same number, `B >=
  33` clears round4-iter-2's first write at call 33, and 35 does.
* **"Under the criterion for the recordings that fail only on call count."**  The binding recording is
  `round4-iter-3`: `prefix(36) = 1,452,307` (0.968x) is its largest prefix under the criterion and
  `prefix(37) = 1,502,443` (1.002x) is over.  A bound `B` bills `B + 1` calls, so `B + 1 <= 36`, i.e.
  **`B <= 35`**.  `B = 36` misses by 2,443 tokens; `B = 35` is the largest value that passes.
* **The two constraints are compatible** — the feasible window is 33..35 (the lower end only under the
  flat reading) — so there was no reason to stop, and the upper end 35 was taken because it leaves the
  producing call the most post-write calls.  25 and 30 also pass but cut every recording earlier and can
  only buy a weaker artifact for no measured benefit; there is no measured variance in the corpus (one
  provider, one model, one project shape) from which to justify inventing a smaller safety factor.
* **The honest caveat**: on the binding recording the headroom is 47,693 tokens, **3.2 %** of the
  criterion.  `35` is defensible as "the largest bound the recordings support", not as "a bound with a
  proven margin".

## 4. The projected effect

Holding each recorded call sequence fixed — which is exact for calls `1..36`, since the bound cannot
change tokens that were already spent — the bound alone gives:

| recording | without the bound | with the bound (36 calls) | the recording's own first legitimate exit |
|---|---|---|---|
| round4-iter-1 | 2,626,195 (1.751x) | 1,127,441 (0.752x) | call 25 -> **665,666 (0.444x)** — cheaper than the bound, so the bound does not bite |
| round4-iter-2 | 13,091,431 (8.728x) | **1,196,549 (0.798x)** | call 58 -> 3,295,369 (2.197x) — the exit alone *fails*; the bound is what rescues it |
| round4-iter-3 | 5,223,211 (3.482x) | **1,452,307 (0.968x)** | call 30 -> 1,160,900 (0.774x) — the exit is cheaper, the bound does not bite |
| livecost1-iter-1 | 3,651,120 (2.434x) | **558,945 (0.373x)** | never declared |
| live completion1/iter-1 | 3,527,566 (2.352x) | **579,120 (0.386x)** | never declared |
| live completion1/iter-2 | 3,939,027 (2.626x) | **633,893 (0.423x)** | never declared |
| live completion1/iter-3 | 803,027 (0.535x) | 803,027 (0.535x) | wrote nothing: the bound never applies, the call still ends at 44 calls on the unwritten allowance and the round still fails |

So the bound is the only lever that rescues `round4-iter-2` and the three recordings that never took the
completion exit, and it costs nothing on the two that declared earlier than 36 calls.  Combined with the
write-guaranteed exit (the call ends at whichever comes first) the projections are: r4-i1 0.444x,
r4-i2 0.798x, r4-i3 0.774x, livecost1 0.373x, live i1/i2 0.386x / 0.423x — **every recorded producing
Developer call under the criterion**.

## 5. The tests: red, then green

Four red states, each with its literal exit code and payload:

| red | command | exit | summary | literal failure |
|---|---|---|---|---|
| the configuration does not carry the bound | `cargo test --offline --test post_write_bound` | **101** | `0 passed; 2 failed` | `:59:5` `left: 150 right: 35`; `:80:5` `config/hoh.yaml must ship the post-write bound as a named number` |
| the controls, against a raw-bound implementation | same | **101** | `2 passed; 2 failed` | `:107:5` `left: 0 right: 150`; `:132:5` `left: 35 right: 20` |
| the number does not reach the guard (production path) | same | **101** | `5 passed; 1 failed` | `:406:5` `left: "LimitsExceeded" right: "StepBudgetExceeded"` — the written call ran to mini's flat backstop instead of the bound |
| the guard's own arithmetic ignores the wired value | `cargo test --offline --lib harness::guard::tests` | **101** | `32 passed; 2 failed` | `src\harness\guard.rs:1460:9` `left: 150 right: 35`; `:1527:18` `the call after the post-write bound must be refused: Output { ... returncode: 0 ... }` |

Green: `--test post_write_bound` exits **0** with `6 passed`; `--lib harness::guard::tests` exits **0**
with `34 passed` (29 before this batch's five new guard tests).  No existing test was removed or
weakened: `git diff -- tests/` is empty (the new file is untracked), and the only pre-existing test text
that changed is the **call sites** of `state_the_effective_budget`, whose every assertion is unchanged
(`the_effective_budget_is_stated_in_the_prompt_exactly_once` still asserts "ceiling", "150", "43",
"re-read at every step", "wrap-up discipline begins 25", one `[budget]` marker, the silent-prompt
passthrough and the ungated wording), beside one new test that pins the note's new duty.

The production-path tests do not build the guard themselves: they drive the real `MiniHarness::invoke`
against a `127.0.0.1` fake chat endpoint (the same pattern `tests/harness_cap_wiring.rs` uses), because
the defect class this guards against is exactly "the value exists but the harness never passes it on".
They assert that the written call ends at 4 calls with `StepBudgetExceeded` where the bound is 3, that
the endpoint was asked exactly as often as the call billed model calls, that `src/game.rs` really landed
on disk and its observation reached a later request, and — as the control — that a call which never
writes still gets the wider unwritten allowance (6 calls where the unwritten budget is 5, strictly more
than the bound).

## 6. The shell-write risk, and what a live round must watch

The disclosure the task named is real: the guard's write detector is a successful **directive** write
inside the project (`extra.hoh_write_path`, outside `.hoh/`, `.git/`, `target/`), while the round's
measurement is a before/after tree hash with `[.hoh, .git, target]` excluded.  A role that changes the
project through the shell satisfies the round but not the guard, so its completion requests are refused
and its call ends on the **unwritten** allowance.

**The disposition: neutral, and not widened.**  The post-write bound is consulted only while
`artifact_written` is true, so a shell-writing call never sees it and keeps the 43-call unwritten
allowance byte-for-byte as before this batch.  Two tests pin it: the guard-level
`the_unwritten_guard_is_untouched_by_the_post_write_bound` (with the bound configured, a never-writing
call is refused only after call 43, i.e. 44 billed calls, with `live step budget is 43` in the message)
and the MiniHarness control `a_call_that_has_not_written_keeps_the_unwritten_allowance`.

**What is newly at stake**: the lever's *efficacy* now depends on the live model using the write
directive at all.  If the Developer writes the project only through the shell, the bound never engages,
the call still spends 44 calls, and the criterion does not move; the round's shape in that case is
unchanged (the tree changed, so `write_failure::assess` reports nothing and the round proceeds).  The
recorded evidence says the directive is used — every first write at calls 7/33/6/6 and 8/13 carries
`extra.hoh_write_path` — but the base rate of shell-side project writes is unmeasured, and the previous
acceptance's defect D2 records four legacy recordings that declare with zero guard-visible writes (all
predating the write directive).

**The second new cost** is that a bound-cut call whose artifact is not yet launchable is a
`StepBudgetExceeded`, which `is_limits_exceeded` accepts, so the DR-18 wrap-up retry issues a second
Developer call (25 steps).  No projection above includes it.  The recorded live artifacts were launchable
long before call 36, but that is a measurement of a different call length.

A live round must therefore watch: (1) whether the Developer's call carries a counted
`hoh_write_path` at all and at which call; (2) the count of `extra.hoh_exit_refused` observations, i.e.
the refused-completion base rate the corpus cannot supply; (3) the call's billed model count and its own
usage total against the 36-call / 1.45 M projection for the binding recording; (4) whether the bound-cut
artifact is still launchable and whether `repair_retry_used` / `developer_wrap_up` fired; (5) the
wrap-up interaction, since `wrap_up_steps: 25` means most of a 36-call call is nominally "wrap-up".

## 7. The gate

| check | literal exit code | result |
|---|---|---|
| `cargo test --offline` | **0** | **824 passed / 0 failed / 6 ignored**, 62 `test result:` lines, **830 listed**, 0 compiler warnings, 0 error lines |
| `cargo test --offline -- --list` | **0** | **830** test lines |
| `cargo test --offline -- --list --ignored` | **0** | **6** test lines |
| `cargo fmt --all --check` | **0** | 0 bytes on stdout and stderr |

Build directory `E:/pwb-target` on `E:` (disk checked first: `F:` had 8.2 GiB and was 100 % full, `E:`
had 566 GiB), one test process at a time.  The untouched-tree baseline in the same directory is
**813 / 0 / 6 / 819**, so the delta is exactly the 11 new tests (6 integration + 5 guard unit).  No
timing-sensitive test failed in any run, so no re-run was needed.  Nothing was deleted (no `rm -rf`, no
wildcard deletion), no `git checkout --`, no path built from an unexpanded variable, nothing under
`runs/**` written, nothing committed or pushed.

## 8. What I could not establish, and the one thing for the next batch

I could not establish anything live.  Every projection holds the recorded call sequence fixed; the bound
changes what the model does *after* call 36, and no offline arithmetic sees that.  I could not measure
the base rate of refused completions or of shell-side project writes, and I could not measure whether a
bound-cut artifact is still launchable — the three facts a live round decides.  The 3.2 % headroom on the
binding recording is the honest form of "this passes": it passes the recordings, once, with no variance
estimate behind it.

**The single most important thing**: the bound's precondition is a **counted directive write**.  Without
one the bound never engages and the criterion does not move, so the next live round should read the
Developer trajectory for `extra.hoh_write_path` first — if the write is there and the call still spends
its 36, the lever is confirmed; if the write is absent or shell-side, the next batch has to make the
write detector agree with the round's tree-hash measurement before any further tuning of 35.
