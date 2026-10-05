```json
{
 "schema": "hof-rs / bevy cost levers, offline measurement over the committed cost corpus",
 "produced_at": "2026-10-06",
 "offline": true,
 "round_run": false,
 "model_call_made": false,
 "engine_started": false,
 "corpus": {
  "round4-iter-1": {
   "model_calls": 69,
   "sent_wire_bytes": 9896402,
   "recorded_prompt_tokens": 2544563,
   "recorded_completion_tokens": 81632,
   "recorded_total_tokens": 2626195,
   "steps": 68
  },
  "round4-iter-2": {
   "model_calls": 125,
   "sent_wire_bytes": 50007767,
   "recorded_prompt_tokens": 12765478,
   "recorded_completion_tokens": 325953,
   "recorded_total_tokens": 13091431,
   "steps": 124
  },
  "round4-iter-3": {
   "model_calls": 102,
   "sent_wire_bytes": 19753905,
   "recorded_prompt_tokens": 5137090,
   "recorded_completion_tokens": 86121,
   "recorded_total_tokens": 5223211,
   "steps": 101
  },
  "livecost1-iter-1": {
   "model_calls": 150,
   "sent_wire_bytes": 10937231,
   "recorded_prompt_tokens": 3537843,
   "recorded_completion_tokens": 113277,
   "recorded_total_tokens": 3651120,
   "steps": 149
  }
 },
 "sent_byte_composition": {
  "round4-iter-1": {
   "system": 1024581,
   "task": 94185,
   "arg_other": 469853,
   "assistant_prose": 135752,
   "obs_read": 3632896,
   "obs_other": 860290,
   "arg_write": 3612009,
   "retry": 66836
  },
  "round4-iter-2": {
   "system": 1856125,
   "task": 170625,
   "arg_other": 1700722,
   "assistant_prose": 531648,
   "obs_read": 14355976,
   "obs_other": 6678689,
   "arg_write": 24673634,
   "retry": 40348
  },
  "round4-iter-3": {
   "system": 1514598,
   "task": 139230,
   "arg_other": 1500617,
   "assistant_prose": 338386,
   "obs_read": 10583412,
   "obs_other": 919009,
   "arg_write": 4699363,
   "retry": 59290
  },
  "livecost1-iter-1": {
   "system": 2227350,
   "task": 204750,
   "arg_other": 2956475,
   "assistant_prose": 793425,
   "obs_read": 3445705,
   "obs_other": 1231721,
   "arg_write": 77805
  }
 },
 "whole_file_sub_shares": {
  "round4-iter-1": {
   "obs_all": 4493186,
   "obs_gt4k": 3253803,
   "obs_gt8k": 637296,
   "write_arg_all": 3579234,
   "write_arg_gt8k": 2425444
  },
  "round4-iter-2": {
   "obs_all": 21034665,
   "obs_gt4k": 15891664,
   "obs_gt8k": 11497498,
   "write_arg_all": 24535599,
   "write_arg_gt8k": 23944761
  },
  "round4-iter-3": {
   "obs_all": 11502421,
   "obs_gt4k": 7925848,
   "obs_gt8k": 5410792,
   "write_arg_all": 4658228,
   "write_arg_gt8k": 4381536
  },
  "livecost1-iter-1": {
   "obs_all": 4677426,
   "write_arg_all": 23408,
   "obs_gt4k": 110892,
   "obs_gt8k": 41364
  }
 },
 "gate": {
  "command": "cargo test --offline",
  "literal_exit_code": 0,
  "passed": 800,
  "failed": 0,
  "ignored": 6,
  "listed": 806,
  "test_result_lines": 60,
  "warning_lines": 0,
  "list_command": "cargo test --offline -- --list",
  "list_exit_code": 0,
  "list_count": 806,
  "list_ignored_command": "cargo test --offline -- --list --ignored",
  "list_ignored_exit_code": 0,
  "list_ignored_count": 6,
  "fmt_command": "cargo fmt --all --check",
  "fmt_exit_code": 0,
  "fmt_output_bytes": 0,
  "build_dir": "F:/lever-hw-target (this spike's own; the repository's own target/ was not used)",
  "free_disk_before": "19G available on F:",
  "free_disk_after": "9.1G available on F:",
  "reruns": "none needed: the first and only run of cargo test --offline returned the literal exit code 0",
  "baseline": "800 passed / 0 failed / 6 ignored / 806 listed",
  "matches_baseline": true,
  "no_test_removed": true,
  "head": "8f06ce69b75496736ae7e410a27d051ac5e34c37"
 },
 "job_1_corrected_byte_rows": [
  {
   "policy": "keep_last_8192_wire_bytes",
   "param_B": 8192,
   "corrected_exclusive": {
    "round4-iter-1": 464340,
    "round4-iter-2": 981753,
    "round4-iter-3": 691946,
    "livecost1-iter-1": 1256360
   },
   "corrected_inclusive": {
    "round4-iter-1": 568385,
    "round4-iter-2": 1496261,
    "round4-iter-3": 823862,
    "livecost1-iter-1": 1304352
   },
   "refuted_by_the_spike": {
    "round4-iter-1": 439638,
    "round4-iter-2": 1049758,
    "round4-iter-3": 620706,
    "livecost1-iter-1": 1042497
   },
   "corrected_all_pass_exclusive": true,
   "corrected_all_pass_inclusive": true
  },
  {
   "policy": "keep_last_16384_wire_bytes",
   "param_B": 16384,
   "corrected_exclusive": {
    "round4-iter-1": 603281,
    "round4-iter-2": 1111346,
    "round4-iter-3": 878538,
    "livecost1-iter-1": 1618917
   },
   "corrected_inclusive": {
    "round4-iter-1": 719733,
    "round4-iter-2": 1728633,
    "round4-iter-3": 1067276,
    "livecost1-iter-1": 1662549
   },
   "refuted_by_the_spike": {
    "round4-iter-1": 475707,
    "round4-iter-2": 1089968,
    "round4-iter-3": 663871,
    "livecost1-iter-1": 1111180
   },
   "corrected_all_pass_exclusive": false,
   "corrected_all_pass_inclusive": false
  },
  {
   "policy": "keep_last_32768_wire_bytes",
   "param_B": 32768,
   "corrected_exclusive": {
    "round4-iter-1": 860602,
    "round4-iter-2": 1474432,
    "round4-iter-3": 1221234,
    "livecost1-iter-1": 2248681
   },
   "corrected_inclusive": {
    "round4-iter-1": 1033899,
    "round4-iter-2": 2226809,
    "round4-iter-3": 1580478,
    "livecost1-iter-1": 2279850
   },
   "refuted_by_the_spike": {
    "round4-iter-1": 532066,
    "round4-iter-2": 1191593,
    "round4-iter-3": 728995,
    "livecost1-iter-1": 1214547
   },
   "corrected_all_pass_exclusive": false,
   "corrected_all_pass_inclusive": false
  },
  {
   "policy": "keep_last_49152_wire_bytes",
   "param_B": 49152,
   "corrected_exclusive": {
    "round4-iter-1": 1090473,
    "round4-iter-2": 1971535,
    "round4-iter-3": 1532693,
    "livecost1-iter-1": 2744312
   },
   "corrected_inclusive": {
    "round4-iter-1": 1306824,
    "round4-iter-2": 2711968,
    "round4-iter-3": 2080977,
    "livecost1-iter-1": 2766147
   },
   "refuted_by_the_spike": {
    "round4-iter-1": 582338,
    "round4-iter-2": 1443621,
    "round4-iter-3": 783839,
    "livecost1-iter-1": 1283793
   },
   "corrected_all_pass_exclusive": false,
   "corrected_all_pass_inclusive": false
  },
  {
   "policy": "keep_last_65536_wire_bytes",
   "param_B": 65536,
   "corrected_exclusive": {
    "round4-iter-1": 1358664,
    "round4-iter-2": 2485510,
    "round4-iter-3": 1871397,
    "livecost1-iter-1": 3128185
   },
   "corrected_inclusive": {
    "round4-iter-1": 1554620,
    "round4-iter-2": 3213537,
    "round4-iter-3": 2545750,
    "livecost1-iter-1": 3143544
   },
   "refuted_by_the_spike": {
    "round4-iter-1": 638631,
    "round4-iter-2": 1545769,
    "round4-iter-3": 845931,
    "livecost1-iter-1": 1350743
   },
   "corrected_all_pass_exclusive": false,
   "corrected_all_pass_inclusive": false
  },
  {
   "policy": "keep_last_131072_wire_bytes",
   "param_B": 131072,
   "corrected_exclusive": {
    "round4-iter-1": 2258021,
    "round4-iter-2": 4379763,
    "round4-iter-3": 3339626,
    "livecost1-iter-1": 3640997
   },
   "corrected_inclusive": {
    "round4-iter-1": 2421574,
    "round4-iter-2": 4981209,
    "round4-iter-3": 4237196,
    "livecost1-iter-1": 3641907
   },
   "refuted_by_the_spike": {
    "round4-iter-1": 739553,
    "round4-iter-2": 1852727,
    "round4-iter-3": 1046342,
    "livecost1-iter-1": 1530472
   },
   "corrected_all_pass_exclusive": false,
   "corrected_all_pass_inclusive": false
  },
  {
   "policy": "keep_last_262144_wire_bytes",
   "param_B": 262144,
   "corrected_exclusive": {
    "round4-iter-1": 2621902,
    "round4-iter-2": 7440904,
    "round4-iter-3": 5156676,
    "livecost1-iter-1": 3651121
   },
   "corrected_inclusive": {
    "round4-iter-1": 2621902,
    "round4-iter-2": 8013251,
    "round4-iter-3": 5156676,
    "livecost1-iter-1": 3651121
   },
   "refuted_by_the_spike": {
    "round4-iter-1": 982725,
    "round4-iter-2": 2432248,
    "round4-iter-3": 1338616,
    "livecost1-iter-1": 1770754
   },
   "corrected_all_pass_exclusive": false,
   "corrected_all_pass_inclusive": false
  },
  {
   "policy": "keep_last_524288_wire_bytes",
   "param_B": 524288,
   "corrected_exclusive": {
    "round4-iter-1": 2621902,
    "round4-iter-2": 12363691,
    "round4-iter-3": 5156676,
    "livecost1-iter-1": 3651121
   },
   "corrected_inclusive": {
    "round4-iter-1": 2621902,
    "round4-iter-2": 12693160,
    "round4-iter-3": 5156676,
    "livecost1-iter-1": 3651121
   },
   "refuted_by_the_spike": {
    "round4-iter-1": 1326728,
    "round4-iter-2": 3133257,
    "round4-iter-3": 1900597,
    "livecost1-iter-1": 2083683
   },
   "corrected_all_pass_exclusive": false,
   "corrected_all_pass_inclusive": false
  }
 ],
 "job_1_corrected_byte_band": {
  "stated_policy": "keep the last B wire bytes of steps: whole steps counted backwards from the newest until B is reached",
  "reading_exclusive_max_whole_step_suffix_le_B": {
   "max_passing_all_four": 13543,
   "binding_recording": "livecost1-iter-1",
   "binding_total": 1499796,
   "fails_at_13544": 1500020
  },
  "reading_inclusive_add_until_reaches_B": {
   "max_passing_all_four": 8443,
   "binding_recording": "round4-iter-2",
   "binding_total": 1499039,
   "fails_at_8444": 1500171
  },
  "sensitivity_0_323468_exclusive": 13543,
  "sensitivity_0_323468_inclusive": 2782,
  "refuted_value_in_the_spike": 49152,
  "refuted_sensitivity_value": 32768,
  "step_rows_confirmed": {
   "N4_total_with_completion_full_precision": {
    "round4-iter-1": 539102,
    "round4-iter-2": 1474827,
    "round4-iter-3": 752076,
    "livecost1-iter-1": 1077207
   },
   "N4_total_with_completion_ratio_0_256686": {
    "round4-iter-1": 539101,
    "round4-iter-2": 1474826,
    "round4-iter-3": 752075,
    "livecost1-iter-1": 1077207
   },
   "N5_total_with_completion_ratio_0_256686": {
    "round4-iter-1": 581360,
    "round4-iter-2": 1631524,
    "round4-iter-3": 811875,
    "livecost1-iter-1": 1114159
   },
   "acceptance_quoted": {
    "N4": [
     539101,
     1474826,
     752075,
     1077207
    ],
    "N5_round4_iter_2": 1631524
   },
   "verdict": "unaffected: N=4 passes all four, N=5 fails on round4-iter-2 alone; the only difference between conventions is +-2 tokens of rounding grain"
  }
 },
 "job_1_write_event_label_correction": {
  "round4-iter-1": {
   "successful_write_events_all_paths": 6,
   "project_only": 6,
   "scratch_only": 0,
   "edges": 6,
   "largest_gaps": [
    5,
    4,
    4,
    2,
    1,
    1
   ]
  },
  "round4-iter-2": {
   "successful_write_events_all_paths": 23,
   "project_only": 11,
   "scratch_only": 12,
   "edges": 11,
   "largest_gaps": [
    28,
    10,
    5,
    5,
    4,
    2,
    2,
    2
   ]
  },
  "round4-iter-3": {
   "successful_write_events_all_paths": 19,
   "project_only": 9,
   "scratch_only": 10,
   "edges": 9,
   "largest_gaps": [
    4,
    4,
    3,
    3,
    2,
    2,
    2,
    2
   ]
  },
  "livecost1-iter-1": {
   "successful_write_events_all_paths": 1,
   "project_only": 0,
   "scratch_only": 1,
   "edges": 0,
   "largest_gaps": []
  }
 },
 "levers": [
  {
   "id": "lever-1-size-bound",
   "name": "Cap each tool observation and each whole-file write argument at C bytes (a size bound, not a recency bound)",
   "evidence_kind": "measured curve + measured discard",
   "projected_effect": {
    "summary": "no per-message size cap passes all four recordings: the floor at C=0 (every observation and every command emptied) is livecost1-iter-1 2,077,238, already 1.38x the 1,500,000 criterion; the three unfolded recordings alone need C <= 13 bytes to pass",
    "cap_zero_totals": {
     "round4-iter-1": 554542,
     "round4-iter-2": 1438584,
     "round4-iter-3": 920851,
     "livecost1-iter-1": 2077238
    },
    "max_cap_passing_three_unfolded": 13,
    "at_that_cap": {
     "round4-iter-1": 572510,
     "round4-iter-2": 1497981,
     "round4-iter-3": 959859,
     "livecost1-iter-1": 2189535
    },
    "curve_total_with_completion": {
     "0": {
      "round4-iter-1": 554542,
      "round4-iter-2": 1438584,
      "round4-iter-3": 920851,
      "livecost1-iter-1": 2077238
     },
     "1024": {
      "round4-iter-1": 1056057,
      "round4-iter-2": 3053194,
      "round4-iter-3": 2007497,
      "livecost1-iter-1": 3622065
     },
     "4096": {
      "round4-iter-1": 1775340,
      "round4-iter-2": 5236481,
      "round4-iter-3": 2876808,
      "livecost1-iter-1": 3639304
     },
     "8192": {
      "round4-iter-1": 2340113,
      "round4-iter-2": 7108367,
      "round4-iter-3": 3505769,
      "livecost1-iter-1": 3649274
     },
     "12288": {
      "round4-iter-1": 2541859,
      "round4-iter-2": 8505380,
      "round4-iter-3": 3789594,
      "livecost1-iter-1": 3651688
     },
     "16384": {
      "round4-iter-1": 2621902,
      "round4-iter-2": 9772478,
      "round4-iter-3": 4003777,
      "livecost1-iter-1": 3651688
     },
     "32768": {
      "round4-iter-1": 2621902,
      "round4-iter-2": 12984287,
      "round4-iter-3": 4872216,
      "livecost1-iter-1": 3651688
     }
    }
   },
   "discard_cost": {
    "summary": "at a cap that would pass the three unfolded recordings (13 bytes) essentially every used line is lost; at a plausible 8 KiB cap round4-iter-2 loses 3,374 of 4,626 used lines across 11/11 edges and round4-iter-1 180 of 783 across 2/6",
    "per_cap": {
     "0": {
      "round4-iter-1": {
       "edges": 6,
       "edges_losing_content": 6,
       "used_lines": 674,
       "used_lines_lost": 674
      },
      "round4-iter-2": {
       "edges": 11,
       "edges_losing_content": 11,
       "used_lines": 4099,
       "used_lines_lost": 4099
      },
      "round4-iter-3": {
       "edges": 21,
       "edges_losing_content": 5,
       "used_lines": 22,
       "used_lines_lost": 22
      },
      "livecost1-iter-1": {
       "edges": 0,
       "edges_losing_content": 0,
       "used_lines": 0,
       "used_lines_lost": 0
      }
     },
     "256": {
      "round4-iter-1": {
       "edges": 6,
       "edges_losing_content": 6,
       "used_lines": 674,
       "used_lines_lost": 661
      },
      "round4-iter-2": {
       "edges": 11,
       "edges_losing_content": 11,
       "used_lines": 4099,
       "used_lines_lost": 4070
      },
      "round4-iter-3": {
       "edges": 21,
       "edges_losing_content": 5,
       "used_lines": 22,
       "used_lines_lost": 13
      },
      "livecost1-iter-1": {
       "edges": 0,
       "edges_losing_content": 0,
       "used_lines": 0,
       "used_lines_lost": 0
      }
     },
     "1024": {
      "round4-iter-1": {
       "edges": 6,
       "edges_losing_content": 6,
       "used_lines": 674,
       "used_lines_lost": 606
      },
      "round4-iter-2": {
       "edges": 11,
       "edges_losing_content": 11,
       "used_lines": 4099,
       "used_lines_lost": 3956
      },
      "round4-iter-3": {
       "edges": 21,
       "edges_losing_content": 2,
       "used_lines": 22,
       "used_lines_lost": 5
      },
      "livecost1-iter-1": {
       "edges": 0,
       "edges_losing_content": 0,
       "used_lines": 0,
       "used_lines_lost": 0
      }
     },
     "4096": {
      "round4-iter-1": {
       "edges": 6,
       "edges_losing_content": 5,
       "used_lines": 674,
       "used_lines_lost": 337
      },
      "round4-iter-2": {
       "edges": 11,
       "edges_losing_content": 11,
       "used_lines": 4099,
       "used_lines_lost": 3572
      },
      "round4-iter-3": {
       "edges": 21,
       "edges_losing_content": 0,
       "used_lines": 22,
       "used_lines_lost": 0
      },
      "livecost1-iter-1": {
       "edges": 0,
       "edges_losing_content": 0,
       "used_lines": 0,
       "used_lines_lost": 0
      }
     },
     "8192": {
      "round4-iter-1": {
       "edges": 6,
       "edges_losing_content": 2,
       "used_lines": 674,
       "used_lines_lost": 128
      },
      "round4-iter-2": {
       "edges": 11,
       "edges_losing_content": 11,
       "used_lines": 4099,
       "used_lines_lost": 2886
      },
      "round4-iter-3": {
       "edges": 21,
       "edges_losing_content": 0,
       "used_lines": 22,
       "used_lines_lost": 0
      },
      "livecost1-iter-1": {
       "edges": 0,
       "edges_losing_content": 0,
       "used_lines": 0,
       "used_lines_lost": 0
      }
     },
     "12288": {
      "round4-iter-1": {
       "edges": 6,
       "edges_losing_content": 2,
       "used_lines": 674,
       "used_lines_lost": 34
      },
      "round4-iter-2": {
       "edges": 11,
       "edges_losing_content": 11,
       "used_lines": 4099,
       "used_lines_lost": 2152
      },
      "round4-iter-3": {
       "edges": 21,
       "edges_losing_content": 0,
       "used_lines": 22,
       "used_lines_lost": 0
      },
      "livecost1-iter-1": {
       "edges": 0,
       "edges_losing_content": 0,
       "used_lines": 0,
       "used_lines_lost": 0
      }
     },
     "16384": {
      "round4-iter-1": {
       "edges": 6,
       "edges_losing_content": 0,
       "used_lines": 674,
       "used_lines_lost": 0
      },
      "round4-iter-2": {
       "edges": 11,
       "edges_losing_content": 10,
       "used_lines": 4099,
       "used_lines_lost": 1416
      },
      "round4-iter-3": {
       "edges": 21,
       "edges_losing_content": 0,
       "used_lines": 22,
       "used_lines_lost": 0
      },
      "livecost1-iter-1": {
       "edges": 0,
       "edges_losing_content": 0,
       "used_lines": 0,
       "used_lines_lost": 0
      }
     },
     "32768": {
      "round4-iter-1": {
       "edges": 6,
       "edges_losing_content": 0,
       "used_lines": 674,
       "used_lines_lost": 0
      },
      "round4-iter-2": {
       "edges": 11,
       "edges_losing_content": 0,
       "used_lines": 4099,
       "used_lines_lost": 0
      },
      "round4-iter-3": {
       "edges": 21,
       "edges_losing_content": 0,
       "used_lines": 22,
       "used_lines_lost": 0
      },
      "livecost1-iter-1": {
       "edges": 0,
       "edges_losing_content": 0,
       "used_lines": 0,
       "used_lines_lost": 0
      }
     }
    },
    "decisive_read_round4_iter_2_call5": {
     "read_observation_utf8_bytes": 14903,
     "used_lines_shared_with_the_write": 148,
     "used_lines_that_occur_nowhere_else_in_calls_6_32": 135,
     "surviving_unique_lines_by_cap": {
      "0": 0,
      "512": 4,
      "1024": 11,
      "2048": 19,
      "4096": 45,
      "8192": 94,
      "12288": 130,
      "13543": 134,
      "16384": 135
     }
    }
   },
   "verdict": "no size bound separates passing from discarding: the cap that passes is ~0 and the cap that preserves content is >= 14,903 bytes on the one decisive read"
  },
  {
   "id": "lever-2-prompt-caching",
   "name": "Prompt caching",
   "evidence_kind": "measured facts; the provider's caching behaviour is argued / not establishable",
   "projected_effect": {
    "summary": "unknown and probably not a token-count lever: the criterion counts total_tokens per call, and prompt caching is normally a price discount, not a reduction of prompt_tokens",
    "max_prefix_reuse_fraction_of_input_tokens": {
     "round4-iter-1": 0.9816,
     "round4-iter-2": 0.9873,
     "round4-iter-3": 0.9872,
     "livecost1-iter-1": 0.9886
    },
    "why_that_is_the_ceiling": "the prompt for call k+1 is literally the prompt for call k plus one step, so a longest-prefix cache could serve at most sum(prompt_tokens[0..k-1]) of the input tokens; measured 98.2%-98.9%"
   },
   "discard_cost": {
    "summary": "zero: caching changes what the provider charges, not what the role sees; no context is discarded",
    "note": "the only way caching moves the criterion's number is if the project redefines it to cache-miss tokens, which would be a different criterion"
   },
   "verdict": "enabling caching is the only lever measured here that discards nothing; whether it is available, and what discount it carries, cannot be read from these recordings"
  },
  {
   "id": "lever-3-working-set",
   "name": "Track the files currently in play instead of the most recent messages",
   "evidence_kind": "measured cost + measured edge preservation; the policy definition is argued",
   "projected_effect": {
    "summary": "a working-set window that keeps the latest carrier of every file touched so far costs 653,580 / 2,104,272 / 989,591 / 1,057,679 (project files only) - round4-iter-2 still fails at 1.40x; over all files it is 1,207,174 / 4,671,707 / 2,379,196 / 1,375,898",
    "project_files_only": {
     "round4-iter-1": {
      "total_with_completion": 653580,
      "ratio_to_criterion": 0.436,
      "max_prompt_per_call": 10215,
      "distinct_files": 3
     },
     "round4-iter-2": {
      "total_with_completion": 2104272,
      "ratio_to_criterion": 1.403,
      "max_prompt_per_call": 15818,
      "distinct_files": 4
     },
     "round4-iter-3": {
      "total_with_completion": 989591,
      "ratio_to_criterion": 0.66,
      "max_prompt_per_call": 27866,
      "distinct_files": 3
     },
     "livecost1-iter-1": {
      "total_with_completion": 1057679,
      "ratio_to_criterion": 0.705,
      "max_prompt_per_call": 14946,
      "distinct_files": 5
     }
    },
    "all_files": {
     "round4-iter-1": {
      "total_with_completion": 1207174,
      "ratio_to_criterion": 0.805,
      "max_prompt_per_call": 19042,
      "distinct_files": 11
     },
     "round4-iter-2": {
      "total_with_completion": 4671707,
      "ratio_to_criterion": 3.114,
      "max_prompt_per_call": 41380,
      "distinct_files": 27
     },
     "round4-iter-3": {
      "total_with_completion": 2379196,
      "ratio_to_criterion": 1.586,
      "max_prompt_per_call": 38400,
      "distinct_files": 34
     },
     "livecost1-iter-1": {
      "total_with_completion": 1375898,
      "ratio_to_criterion": 0.917,
      "max_prompt_per_call": 19137,
      "distinct_files": 16
     }
    },
    "working_set_plus_size_cap": {
     "max_cap_passing_all_four": 7665,
     "at_cap": {
      "round4-iter-1": 581177,
      "round4-iter-2": 1499982,
      "round4-iter-3": 729554,
      "livecost1-iter-1": 1054440
     },
     "at_cap_plus_1": {
      "round4-iter-1": 581188,
      "round4-iter-2": 1500014,
      "round4-iter-3": 729570,
      "livecost1-iter-1": 1054444
     }
    }
   },
   "discard_cost": {
    "summary": "zero by construction and measured: the working set keeps the latest carrier of each file, which is exactly the source of every recorded edge - 6/6, 11/11, 21/21 preserved",
    "edge_preservation": {
     "round4-iter-1": {
      "edges": 6,
      "source_kept": 6
     },
     "round4-iter-2": {
      "edges": 11,
      "source_kept": 11
     },
     "round4-iter-3": {
      "edges": 21,
      "source_kept": 21
     },
     "livecost1-iter-1": {
      "edges": 0,
      "source_kept": 0
     }
    },
    "but": "adding the size cap needed to pass (7,665 bytes) reintroduces the lever-1 discard: round4-iter-2 then loses 2,981 of 4,099 used lines across 11/11 edges"
   },
   "verdict": "the right structure for keeping what the role used, but not sufficient on its own: cost is dominated by re-sending the current file on every one of 125-150 calls"
  },
  {
   "id": "lever-4-call-count",
   "name": "Fewer calls per invocation (retries and re-reads)",
   "evidence_kind": "measured counts and replay; the behavioural effect is argued",
   "projected_effect": {
    "summary": "retries cost 34.4% / 11.6% / 8.1% / 0% of recorded prompt tokens (20/10/8/0 calls); pure re-read calls cost 8.4% / 0.7% / 18.0% / 64.4% (5/1/19/91 calls); replaying the recorded sequence with those calls deleted gives round4-iter-1 1,459,123 (0.97x) but round4-iter-2 11,045,350 (7.36x)",
    "calls_by_category": {
     "round4-iter-1": {
      "calls": 69,
      "by_category": {
       "read_only": 7,
       "other": 8,
       "build_test": 29,
       "write": 5,
       "retry_format_error": 20
      },
      "prompt_tokens_by_category": {
       "read_only": 189482,
       "other": 258920,
       "build_test": 1099353,
       "write": 120242,
       "retry_format_error": 876566
      },
      "exact_duplicate_commands": 4,
      "commands": 59,
      "distinct_commands": 55,
      "_pure_reread_calls": 5,
      "_pure_reread_tokens": 213825
     },
     "round4-iter-2": {
      "calls": 125,
      "by_category": {
       "read_only": 10,
       "other": 43,
       "write": 22,
       "build_test": 40,
       "retry_format_error": 10
      },
      "prompt_tokens_by_category": {
       "read_only": 241896,
       "other": 3444345,
       "write": 2176941,
       "build_test": 5415594,
       "retry_format_error": 1486702
      },
      "exact_duplicate_commands": 7,
      "commands": 122,
      "distinct_commands": 115,
      "_pure_reread_calls": 1,
      "_pure_reread_tokens": 95702
     },
     "round4-iter-3": {
      "calls": 102,
      "by_category": {
       "read_only": 32,
       "other": 16,
       "write": 13,
       "build_test": 33,
       "retry_format_error": 8
      },
      "prompt_tokens_by_category": {
       "read_only": 1464493,
       "other": 790661,
       "write": 717737,
       "build_test": 1747289,
       "retry_format_error": 416910
      },
      "exact_duplicate_commands": 3,
      "commands": 108,
      "distinct_commands": 105,
      "_pure_reread_calls": 19,
      "_pure_reread_tokens": 924605
     },
     "livecost1-iter-1": {
      "calls": 150,
      "by_category": {
       "read_only": 107,
       "build_test": 18,
       "other": 24,
       "write": 1
      },
      "prompt_tokens_by_category": {
       "read_only": 2591598,
       "build_test": 420865,
       "other": 509999,
       "write": 15381
      },
      "exact_duplicate_commands": 6,
      "commands": 172,
      "distinct_commands": 166,
      "_pure_reread_calls": 91,
      "_pure_reread_tokens": 2278386
     }
    },
    "pure_reread_calls_and_tokens": {
     "round4-iter-1": {
      "calls": 5,
      "prompt_tokens_at_those_calls": 213825
     },
     "round4-iter-2": {
      "calls": 1,
      "prompt_tokens_at_those_calls": 95702
     },
     "round4-iter-3": {
      "calls": 19,
      "prompt_tokens_at_those_calls": 924605
     },
     "livecost1-iter-1": {
      "calls": 91,
      "prompt_tokens_at_those_calls": 2278386
     }
    },
    "cascade_replay": {
     "round4-iter-1": {
      "minus_retries": 1716086,
      "minus_pure_rereads": 2321970,
      "minus_both": 1459123
     },
     "round4-iter-2": {
      "minus_retries": 11652939,
      "minus_pure_rereads": 12475767,
      "minus_both": 11045350
     },
     "round4-iter-3": {
      "minus_retries": 4723639,
      "minus_pure_rereads": 3782001,
      "minus_both": 3396843
     },
     "livecost1-iter-1": {
      "minus_retries": 3651121,
      "minus_pure_rereads": 784057,
      "minus_both": 784057
     }
    }
   },
   "discard_cost": {
    "summary": "a retry fix discards nothing (the retry is a format error, not content). Deleting re-reads is only free if the content they re-read is still in context - on the folded live recording it is not, which is why 91 of 150 calls are pure re-reads",
    "live_reread_facts": {
     "calls": 150,
     "read_only_calls": 107,
     "pure_reread_calls": 91,
     "shell_commands": 172,
     "distinct_shell_commands": 166,
     "re_read_events": 101,
     "src_game_rs_reads_after_the_first": 42
    }
   },
   "verdict": "the largest measured single lever, and the only one that can pass the live call (0.52x) - but it cannot rescue round4-iter-2 (7.36x), whose cost is the accumulated unlimited write arguments, not the call count"
  }
 ],
 "levers_table": [
  {
   "lever": "Cap each tool observation and each whole-file write argument at C bytes (a size bound, not a recency bound)",
   "projected_effect": "no per-message size cap passes all four recordings: the floor at C=0 (every observation and every command emptied) is livecost1-iter-1 2,077,238, already 1.38x the 1,500,000 criterion; the three unfolded recordings alone need C <= 13 bytes to pass",
   "discard_cost": "at a cap that would pass the three unfolded recordings (13 bytes) essentially every used line is lost; at a plausible 8 KiB cap round4-iter-2 loses 3,374 of 4,626 used lines across 11/11 edges and round4-iter-1 180 of 783 across 2/6",
   "measured_or_argued": "measured curve + measured discard",
   "verdict": "no size bound separates passing from discarding: the cap that passes is ~0 and the cap that preserves content is >= 14,903 bytes on the one decisive read"
  },
  {
   "lever": "Prompt caching",
   "projected_effect": "unknown and probably not a token-count lever: the criterion counts total_tokens per call, and prompt caching is normally a price discount, not a reduction of prompt_tokens",
   "discard_cost": "zero: caching changes what the provider charges, not what the role sees; no context is discarded",
   "measured_or_argued": "measured facts; the provider's caching behaviour is argued / not establishable",
   "verdict": "enabling caching is the only lever measured here that discards nothing; whether it is available, and what discount it carries, cannot be read from these recordings"
  },
  {
   "lever": "Track the files currently in play instead of the most recent messages",
   "projected_effect": "a working-set window that keeps the latest carrier of every file touched so far costs 653,580 / 2,104,272 / 989,591 / 1,057,679 (project files only) - round4-iter-2 still fails at 1.40x; over all files it is 1,207,174 / 4,671,707 / 2,379,196 / 1,375,898",
   "discard_cost": "zero by construction and measured: the working set keeps the latest carrier of each file, which is exactly the source of every recorded edge - 6/6, 11/11, 21/21 preserved",
   "measured_or_argued": "measured cost + measured edge preservation; the policy definition is argued",
   "verdict": "the right structure for keeping what the role used, but not sufficient on its own: cost is dominated by re-sending the current file on every one of 125-150 calls"
  },
  {
   "lever": "Fewer calls per invocation (retries and re-reads)",
   "projected_effect": "retries cost 34.4% / 11.6% / 8.1% / 0% of recorded prompt tokens (20/10/8/0 calls); pure re-read calls cost 8.4% / 0.7% / 18.0% / 64.4% (5/1/19/91 calls); replaying the recorded sequence with those calls deleted gives round4-iter-1 1,459,123 (0.97x) but round4-iter-2 11,045,350 (7.36x)",
   "discard_cost": "a retry fix discards nothing (the retry is a format error, not content). Deleting re-reads is only free if the content they re-read is still in context - on the folded live recording it is not, which is why 91 of 150 calls are pure re-reads",
   "measured_or_argued": "measured counts and replay; the behavioural effect is argued",
   "verdict": "the largest measured single lever, and the only one that can pass the live call (0.52x) - but it cannot rescue round4-iter-2 (7.36x), whose cost is the accumulated unlimited write arguments, not the call count"
  }
 ],
 "confidence": {
  "corrected_byte_rows": "high - the two band edges were re-derived by binary search from independently written window code and reproduce the independent acceptance's 13,543 / 8,443 / 2,782 exactly; the step rows reproduce under both rounding conventions",
  "step_rows_unaffected": "high - N=4 passes and N=5 fails on round4-iter-2 under both the full-precision and the 0.256686 ratio conventions",
  "size_bound_verdict": "high on the floor (2,077,238 at C=0 for live is arithmetic over the recorded messages) and high on the discard counts; medium on the truncation-as-summary model (a summariser might preserve more per byte, but it cannot preserve more bytes than the cap)",
  "caching": "low - the recordings contain no cache information at all; the 98.2-98.9% prefix-reuse ceiling is measured, everything about the provider is not",
  "working_set": "medium-high on the cost (it is arithmetic over the recorded files) and high on edge preservation; medium on how a live policy would decide what is 'in play'",
  "call_count": "medium - the counts and the retry token cost are exact; the cascade replay holds the rest of the sequence fixed, so the savings are a floor, and the behavioural claim (a stricter surface actually reduces calls) is untested"
 },
 "what_i_could_not_establish": [
  "No round and no model call were run, so every lever's projection holds the recorded call sequence fixed; a real role reacts to a smaller or restructured context by re-reading, re-planning or making different edits, and none of that is in the recordings.",
  "The provider's caching behaviour is not in the corpus: all 446 recorded response usage objects carry exactly completion_tokens, prompt_tokens and total_tokens, and the aggregate hoh.usage carries cache_hit_tokens: null and cache_miss_tokens: null. Nothing can be concluded about whether the endpoint (an OpenAI-compatible vLLM, system_fingerprint vllm-0.5.2-tp8-ep-ff177f0d) emits or supports prefix caching.",
  "The size-cap curve models a cap as truncation. A summariser that preserved the most relevant C bytes could do better, but it cannot retain more bytes than C, so the C=0 floor stands for any scheme that keeps the recorded messages.",
  "The working-set policy's notion of 'in play' is defined operationally here as 'has a carrier message somewhere earlier'. A live policy needs a real rule (an editing episode, a touched-in-the-last-N-actions set) and that rule is a design choice, not a measurement.",
  "The livecost1-iter-1 recording is folded, so its payloads are notes and its content analysis is impossible; it is nevertheless the binding recording for the corrected exclusive byte band and for the size cap floor.",
  "The call-count cascade deletes calls from the recorded sequence; it does not model that the deleted work would have to happen somewhere else, and it cannot show whether a stricter tool surface would reduce the number of calls at all.",
  "The three unfolded recordings and the one folded recording are four Developer calls in one project; nothing here measures a second provider, a different model or a different project shape."
 ],
 "single_most_important_thing": "No lever that keeps the recorded call sequence can meet the criterion by shrinking context alone: at C=0 - every observation and every command emptied - the folded live Developer call still costs 2,077,238 tokens (1.38x the criterion), because what remains is 150 calls each re-sending the 14,849-byte system prompt, the task, the assistant scaffolding and the accumulated history. Size bounds, recency windows and working sets all trade content for bytes; caching is the only lever that discards nothing but it does not move a token-count criterion; and the one lever that can actually pass a call (fewer calls) is a behaviour of the role that no offline replay can prove. The next decision should therefore be a live experiment on the call count and the tool surface, not another context-diet document."
}
```


# SPIKE — the four cost levers, measured offline over the committed cost corpus

**Scope.** Offline arithmetic and text analysis over files that already exist:
`evidence/cost/*.developer.attempt1.json`, the recorded API responses inside them, and the repository's
own reconstruction code. **No round was run, no model call was made, no engine was started, no network
was used.** Nothing under `src/**`, `tests/**`, `evidence/**`, `runs/**`, `config/**` or any frozen
document was written. The helper scripts live outside the repository at `F:/lever-hw/`. Nothing was
committed or pushed. Numbers are labelled **measured** (read or computed out of the recordings) or
**projected** (arithmetic over measured bytes, with the call sequence held fixed).

This report does two jobs: it re-measures and corrects the refuted byte rows of
`SPIKE-HISTORY-WINDOW.md` (done in place there, with the refuted values kept as labelled history), and
it measures the four cost levers that the earlier spike never considered.

## 1. Method

Reconstruction is the repository's own. A message's wire size is
`json{role, content, tool_calls, tool_call_id}` serialised compactly with the local `extra` block
excluded; a model call is located at the message carrying `extra.response.usage`, and the prompt for
call *k* is `messages[0:k]`, i.e. the system prompt, the task, then one step per earlier call. The
reconstruction reproduces the published corpus exactly:

| recording | model calls | sent wire bytes | recorded prompt | recorded completion | recorded total |
|---|---|---|---|---|---|
| round4-iter-1 | 69 | 9,896,402 | 2,544,563 | 81,632 | 2,626,195 |
| round4-iter-2 | 125 | 50,007,767 | 12,765,478 | 325,953 | 13,091,431 |
| round4-iter-3 | 102 | 19,753,905 | 5,137,090 | 86,121 | 5,223,211 |
| livecost1-iter-1 | 150 | 10,937,231 | 3,537,843 | 113,277 | 3,651,120 |

Call numbers below are **1-based** (call 1 is the first model call), matching the earlier spike and its
acceptance; message indices are 0-based. Two calibrations are used exactly as the earlier work used
them: **0.256686** prompt tokens per wire byte pooled over the three unfolded recordings (their bytes
are real content) and the live recording's own **0.323468**, which is also applied to everything as the
pessimistic sensitivity.

Three measurements are new here:

* **Sent-byte composition.** Every message of every prompt is attributed to a category (system, task,
  tool observation, tool-call argument, assistant prose, retry turn) and summed over all calls; the
  parts add exactly to the recording's sent wire bytes, which validates the attribution.
* **A per-message size cap.** For a cap *C*, every tool observation's content and every command inside
  a tool call is truncated to its first *C* UTF-8 bytes **before** the wire size is computed, the
  history is not otherwise changed, and the prompt curve is re-projected. This is a size bound, not a
  recency bound.
* **The same content test the recency acceptance used.** For every successful write to a project file
  the source it was written from (the latest earlier read or write of that file) is located, the
  substantive lines of the new write that occur verbatim in that source are the content it demonstrably
  used, and the same test is then applied after truncating the source to *C* bytes. On
  `round4-iter-2` the decisive read is 14,903 bytes at call 5 and the write is at call 33, a 28-step
  gap.

## 2. Job 1 — the corrected byte rows

**Corrected values (measured, independently re-derived).** The stated policy is "whole steps counted
backwards from the newest until B is reached", which is ambiguous at the grain of one step, so both
readings are reported. Under the primary calibration the largest budget that keeps all four recorded
calls under the criterion is:

| reading | max B passing all four | binding recording | at the edge | first failing B |
|---|---|---|---|---|
| exclusive (largest whole-step suffix with byte total <= B) | **13,543** | livecost1-iter-1 | 1,499,796 | 13,544 -> 1,500,020 |
| inclusive (keep adding whole steps until the running total reaches B) | **8,443** | round4-iter-2 | 1,499,039 | 8,444 -> 1,500,171 |
| exclusive under the pessimistic 0.323468 ratio everywhere | **13,543** | livecost1-iter-1 | 1,499,796 | 13,544 -> 1,500,020 |
| inclusive under the pessimistic 0.323468 ratio everywhere | **2,782** | round4-iter-2 | 1,499,244 | 2,783 -> 1,509,795 |

Those four edges were found by binary search over independently written window code and reproduce the
independent acceptance's figures (13,543 / 8,443 / 2,782) exactly; the acceptance's statement that the
spike's band is wrong by 3.6x-5.8x is confirmed, not adopted. **The refuted values were 49,152
(primary) and 32,768 (sensitivity).** Every corrected row sits beside the refuted one below; the
refuted numbers are struck through and are kept as history.

| B | r4-i1 corrected | r4-i2 corrected | r4-i3 corrected | live corrected | r4-i1 refuted | r4-i2 refuted | r4-i3 refuted | live refuted |
|---|---|---|---|---|---|---|---|---|
| `8192 B` | 464,340 | 981,753 | 691,946 | 1,256,360 | ~~439,638~~ | ~~1,049,758~~ | ~~620,706~~ | ~~1,042,497~~ |
| `16384 B` | 603,281 | 1,111,346 | 878,538 | 1,618,917 | ~~475,707~~ | ~~1,089,968~~ | ~~663,871~~ | ~~1,111,180~~ |
| `32768 B` | 860,602 | 1,474,432 | 1,221,234 | 2,248,681 | ~~532,066~~ | ~~1,191,593~~ | ~~728,995~~ | ~~1,214,547~~ |
| `49152 B` | 1,090,473 | 1,971,535 | 1,532,693 | 2,744,312 | ~~582,338~~ | ~~1,443,621~~ | ~~783,839~~ | ~~1,283,793~~ |
| `65536 B` | 1,358,664 | 2,485,510 | 1,871,397 | 3,128,185 | ~~638,631~~ | ~~1,545,769~~ | ~~845,931~~ | ~~1,350,743~~ |
| `131072 B` | 2,258,021 | 4,379,763 | 3,339,626 | 3,640,997 | ~~739,553~~ | ~~1,852,727~~ | ~~1,046,342~~ | ~~1,530,472~~ |
| `262144 B` | 2,621,902 | 7,440,904 | 5,156,676 | 3,651,121 | ~~982,725~~ | ~~2,432,248~~ | ~~1,338,616~~ | ~~1,770,754~~ |
| `524288 B` | 2,621,902 | 12,363,691 | 5,156,676 | 3,651,121 | ~~1,326,728~~ | ~~3,133,257~~ | ~~1,900,597~~ | ~~2,083,683~~ |

**The step-window rows are unaffected (measured).** Under the acceptance's rounding convention the N = 4
row is 539,101 / 1,474,826 / 752,075 / 1,077,207 and N = 5 fails on `round4-iter-2` at 1,631,524; under
the full-precision ratio the same row is 539,102 / 1,474,827 / 752,076 / 1,077,207 and N = 5 is
1,631,526. The two conventions differ only by the rounding grain (+/-2 tokens) and the boundary is
identical under both:

| N | r4-i1 full-prec | r4-i2 full-prec | r4-i3 full-prec | live full-prec | r4-i1 0.256686 | r4-i2 0.256686 | r4-i3 0.256686 | live 0.256686 |
|---|---|---|---|---|---|---|---|---|
| 1 | 411,639 | 1,003,504 | 571,376 | 946,649 | 411,639 | 1,003,503 | 571,376 | 946,649 |
| 2 | 454,166 | 1,160,651 | 631,917 | 993,111 | 454,166 | 1,160,650 | 631,917 | 993,111 |
| 3 | 496,654 | 1,317,759 | 692,083 | 1,036,844 | 496,653 | 1,317,758 | 692,082 | 1,036,844 |
| 4 | 539,102 | 1,474,827 | 752,076 | 1,077,207 | 539,101 | 1,474,826 | 752,075 | 1,077,207 |
| 5 | 581,361 | 1,631,526 | 811,876 | 1,114,159 | 581,360 | 1,631,524 | 811,875 | 1,114,159 |

**The write-event label is wrong (measured).** `successful_project_write_events` is not project-only: the
detector counts every write event and only filters by path when it builds the edges. Re-run with the
split, the counts are **6 / 23 / 19 / 1** all-path, of which **6 / 11 / 9 / 0 are project writes** and
**0 / 12 / 10 / 1 are `.hoh/scratch/**` writes**. Only `round4-iter-1` is all-project. The edges and
their gaps are unaffected and were reproduced exactly (iter-1 6 edges, gaps 5,4,4,2,...; iter-2 11
edges, gaps 28,10,5,5,4,...; iter-3 9 project edges at the detector's grain, gaps 4,4,3,3,2,...; live
0). At the corrected passing byte edge the consequence is *worse* than the file claimed: at
`B = 13,543` exclusive `round4-iter-2` drops 11 of 11 edges and `round4-iter-1` drops 4 of 6.

## 3. The composition the levers act on (measured)

Observations and whole-file write arguments are almost the whole prompt on the unfolded recordings:

| recording | sent wire bytes | composition by category (share of sent bytes) |
|---|---|---|
| round4-iter-1 | 9,896,402 | tool observations (file reads) 36.7%, write arguments 36.5%, system prompt 10.4%, tool observations (other) 8.7%, other tool-call arguments 4.7%, assistant prose 1.4%, task prompt 1.0%, format-error retry turns 0.7% |
| round4-iter-2 | 50,007,767 | write arguments 49.3%, tool observations (file reads) 28.7%, tool observations (other) 13.4%, system prompt 3.7%, other tool-call arguments 3.4%, assistant prose 1.1%, task prompt 0.3%, format-error retry turns 0.1% |
| round4-iter-3 | 19,753,905 | tool observations (file reads) 53.6%, write arguments 23.8%, system prompt 7.7%, other tool-call arguments 7.6%, tool observations (other) 4.7%, assistant prose 1.7%, task prompt 0.7%, format-error retry turns 0.3% |
| livecost1-iter-1 | 10,937,231 | tool observations (file reads) 31.5%, other tool-call arguments 27.0%, system prompt 20.4%, tool observations (other) 11.3%, assistant prose 7.3%, task prompt 1.9%, write arguments 0.7% |

Tool observations plus whole-file write arguments are 81.9% / 91.4% / 82.0% / 43.5% of the sent bytes on round4-iter-1 / round4-iter-2 / round4-iter-3 / livecost1-iter-1.

Whole-file items dominate within those categories: on `round4-iter-2`, tool observations over 8 KiB are
11,497,498 of the 21,034,665 observation bytes re-sent, and write arguments over 8 KiB are 23,944,761 of
the 24,535,599 write-argument bytes. The largest single messages are a 45,807-byte `HOH_WRITE_FILE
src/game.rs` argument (iter-3) and a 42,467-byte whole-file observation (iter-2). The live recording's
write arguments are only 23,408 bytes in total, because the fold already replaced them with notes.

## 4. The four levers

Each lever below is stated with its projected effect, its discard cost and whether that is measured or
argued.

### Cap each tool observation and each whole-file write argument at C bytes (a size bound, not a recency bound)

| lever | projected effect | discard cost | measured or argued |
|---|---|---|---|
| Cap each tool observation and each whole-file write argument at C bytes (a size bound, not a recency bound) | no per-message size cap passes all four recordings: the floor at C=0 (every observation and every command emptied) is livecost1-iter-1 2,077,238, already 1.38x the 1,500,000 criterion; the three unfolded recordings alone need C <= 13 bytes to pass | at a cap that would pass the three unfolded recordings (13 bytes) essentially every used line is lost; at a plausible 8 KiB cap round4-iter-2 loses 3,374 of 4,626 used lines across 11/11 edges and round4-iter-1 180 of 783 across 2/6 | measured curve + measured discard |

**Verdict.** no size bound separates passing from discarding: the cap that passes is ~0 and the cap that preserves content is >= 14,903 bytes on the one decisive read

| cap C | r4-i1 | r4-i2 | r4-i3 | live | all four |
|---|---|---|---|---|---|
| `0 B` | 554,542 | 1,438,584 | 920,851 | 2,077,238 FAIL | FAIL |
| `1024 B` | 1,056,057 | 3,053,194 FAIL | 2,007,497 FAIL | 3,622,065 FAIL | FAIL |
| `4096 B` | 1,775,340 FAIL | 5,236,481 FAIL | 2,876,808 FAIL | 3,639,304 FAIL | FAIL |
| `8192 B` | 2,340,113 FAIL | 7,108,367 FAIL | 3,505,769 FAIL | 3,649,274 FAIL | FAIL |
| `12288 B` | 2,541,859 FAIL | 8,505,380 FAIL | 3,789,594 FAIL | 3,651,688 FAIL | FAIL |
| `16384 B` | 2,621,902 FAIL | 9,772,478 FAIL | 4,003,777 FAIL | 3,651,688 FAIL | FAIL |
| `32768 B` | 2,621,902 FAIL | 12,984,287 FAIL | 4,872,216 FAIL | 3,651,688 FAIL | FAIL |

### Prompt caching

| lever | projected effect | discard cost | measured or argued |
|---|---|---|---|
| Prompt caching | unknown and probably not a token-count lever: the criterion counts total_tokens per call, and prompt caching is normally a price discount, not a reduction of prompt_tokens | zero: caching changes what the provider charges, not what the role sees; no context is discarded | measured facts; the provider's caching behaviour is argued / not establishable |

**Verdict.** enabling caching is the only lever measured here that discards nothing; whether it is available, and what discount it carries, cannot be read from these recordings

### Track the files currently in play instead of the most recent messages

| lever | projected effect | discard cost | measured or argued |
|---|---|---|---|
| Track the files currently in play instead of the most recent messages | a working-set window that keeps the latest carrier of every file touched so far costs 653,580 / 2,104,272 / 989,591 / 1,057,679 (project files only) - round4-iter-2 still fails at 1.40x; over all files it is 1,207,174 / 4,671,707 / 2,379,196 / 1,375,898 | zero by construction and measured: the working set keeps the latest carrier of each file, which is exactly the source of every recorded edge - 6/6, 11/11, 21/21 preserved | measured cost + measured edge preservation; the policy definition is argued |

**Verdict.** the right structure for keeping what the role used, but not sufficient on its own: cost is dominated by re-sending the current file on every one of 125-150 calls

| policy | r4-i1 | r4-i2 | r4-i3 | live | all four |
|---|---|---|---|---|---|
| working set, project files only | 653,580 | 2,104,272 FAIL | 989,591 | 1,057,679 | FAIL |
| working set, every file touched | 1,207,174 | 4,671,707 FAIL | 2,379,196 FAIL | 1,375,898 | FAIL |
| working set + 7,665-byte cap | 581,177 | 1,499,982 | 729,554 | 1,054,440 | pass |

### Fewer calls per invocation (retries and re-reads)

| lever | projected effect | discard cost | measured or argued |
|---|---|---|---|
| Fewer calls per invocation (retries and re-reads) | retries cost 34.4% / 11.6% / 8.1% / 0% of recorded prompt tokens (20/10/8/0 calls); pure re-read calls cost 8.4% / 0.7% / 18.0% / 64.4% (5/1/19/91 calls); replaying the recorded sequence with those calls deleted gives round4-iter-1 1,459,123 (0.97x) but round4-iter-2 11,045,350 (7.36x) | a retry fix discards nothing (the retry is a format error, not content). Deleting re-reads is only free if the content they re-read is still in context - on the folded live recording it is not, which is why 91 of 150 calls are pure re-reads | measured counts and replay; the behavioural effect is argued |

**Verdict.** the largest measured single lever, and the only one that can pass the live call (0.52x) - but it cannot rescue round4-iter-2 (7.36x), whose cost is the accumulated unlimited write arguments, not the call count

| recording | calls | retry calls | retry prompt tokens | pure re-read calls | re-read prompt tokens | replay minus both |
|---|---|---|---|---|---|---|
| round4-iter-1 | 69 | 20 | 876,566 | 5 | 213,825 | 1,459,123 |
| round4-iter-2 | 125 | 10 | 1,486,702 | 1 | 95,702 | 11,045,350 |
| round4-iter-3 | 102 | 8 | 416,910 | 19 | 924,605 | 3,396,843 |
| livecost1-iter-1 | 150 | 0 | 0 | 91 | 2,278,386 | 784,057 |


## 5. What I could not establish

* **No live confirmation exists for any lever.** Every projection holds the recorded call sequence fixed
  and changes one dimension of the prompt. A role that sees less will behave differently; the recordings
  cannot say how.
* **The provider's caching behaviour is simply absent from the corpus.** All 446 recorded response
  `usage` objects carry exactly `completion_tokens`, `prompt_tokens`, `total_tokens`; the aggregate
  `hoh.usage` carries `cache_hit_tokens: null` and `cache_miss_tokens: null`. The measured 98.2%-98.9%
  prefix-reuse ceiling says caching *could* serve almost the whole prompt, but nothing here says whether
  the endpoint (OpenAI-compatible, `system_fingerprint vllm-0.5.2-tp8-ep-ff177f0d`) does.
* **Truncation is not summarisation.** The size-cap curve truncates; a summariser could preserve the
  most useful C bytes. It cannot preserve more bytes than C, so the C = 0 floor (live 2,077,238) stands
  for any scheme that keeps the recorded messages, but the mid-range rows are a pessimistic model.
* **"In play" is a design decision.** The working-set rows define it operationally as "has a carrier
  message earlier in the history". A live policy needs a real rule, and the rule changes the cost.
* **The call-count cascade is not a behavioural model.** Deleting recorded calls and replaying the rest
  measures the recorded work, not what the role would do instead. Whether a stricter tool surface or a
  retry fix actually reduces the call count is exactly what must be measured live.
* **The folded live recording cannot answer content questions.** Its payloads are notes, yet it is the
  binding recording for both the corrected exclusive byte band and the size-cap floor.
* **One project, one provider, four calls.** No claim here generalises to a different model, provider or
  project shape.

## 6. The single most important thing for the next decision-maker

**No lever that keeps the recorded call sequence meets the criterion by shrinking context alone.** The
cleanest statement of why is the floor: with every observation and every command emptied, the folded
live Developer call still costs **2,077,238** tokens, 1.38x the criterion, because what survives is 150
calls each re-sending the 14,849-byte system prompt, the 1,365-byte task, the assistant scaffolding and
the accumulated history. Recency windows, size caps and working sets all trade content for bytes - the
working set at least trades in the right direction, preserving all 38 recorded edge sources, but it
still fails `round4-iter-2` at 1.40x until a size cap is added, and that cap discards 2,981 of 4,099
used lines. Caching is the only lever that discards nothing, and it does not move a *token-count*
criterion. The one lever that can actually pass a call is **fewer calls**, and that is a behaviour of
the role - rewriting the replay without the retries and pure re-reads passes the live call at 0.52x but
leaves `round4-iter-2` at 7.36x, because iter-2's cost is the accumulated unlimited whole-file write
arguments, not the call count. **The next step should be a live experiment on the tool surface and the
call count, with the retry fix first because it is free: it discards no context and it is worth 34.4% of
`round4-iter-1`'s prompt tokens.**

## 7. Gate (measured)

`cargo test --offline`, in this spike's own build directory `F:/lever-hw-target`:

* **literal exit code 0**; **800 passed / 0 failed / 6 ignored / 806 listed**, 60 `test result:` lines,
  **0** `warning:` lines;
* `cargo test --offline -- --list` exit 0 with **806** names; `cargo test --offline -- --list --ignored`
  exit 0 with **6**;
* `cargo fmt --all --check` exit 0 emitting **0 bytes** of output;
* identical to the stated baseline (800 / 0 / 6 / 806), so no test was removed; free disk on `F:`
  19G before and 9.1G after the build; one test process at a time; no `rm -rf`, no wildcards;
* the first and only run of `cargo test --offline` returned exit 0, so no re-run was needed and no flake
  is being hidden.

## 8. Files, commands and what was not touched

Helper scripts (outside the repository): `F:/lever-hw/core.py` (reconstruction and replay),
`compose.py` (sent-byte composition), `caps.py` (size-cap curve), `content.py` and `deps_mine.py`
(edges and the content test), `relabel.py` (the spike's write-event detector, re-run with the
project/scratch split), `bands.py` and `byte_table.py` (corrected byte edges and rows), `ws.py`
(working set), `lever4_cascade.py` (call categories and the call-count replay), `patch_doc.py` and
`patch_prose.py` (the in-place correction of `SPIKE-HISTORY-WINDOW.md`), `make_report.py` (this file).

Changed in the repository: `.spec/bevy/SPIKE-HISTORY-WINDOW.md` (the correction above, with the
refuted values kept as labelled history in the machine block and in a new section 9) and this new file.
Nothing else: `git status --porcelain` shows only the modified spike document and this new report
(plus the pre-existing untracked `ACCEPTANCE-SPIKE-HISTORY.md`), no file under `src/**`, `tests/**`,
`evidence/**`, `runs/**`, `config/**`, the registry, the battery, the liveness step, `.gitattributes`
or any frozen document was written, no API key was created, copied or printed, nothing was committed
and nothing was pushed.
