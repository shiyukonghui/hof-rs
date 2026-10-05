```json
{
 "schema": "hof-rs / bevy bounded-history-window measurement spike",
 "produced_at": "2026-10-06",
 "offline": true,
 "round_run": false,
 "model_call_made": false,
 "engine_started": false,
 "corpus": {
  "path": "evidence/cost/*.json (committed, byte-identical to runs/**)",
  "recordings": {
   "round4-iter-1": {
    "kind": "unfolded",
    "model_calls": 69,
    "sent_wire_bytes": 9896402,
    "recorded_prompt_tokens": 2544563,
    "recorded_completion_tokens": 81632,
    "recorded_total_tokens": 2626195,
    "tokens_per_wire_byte_ratio_of_totals": 0.25712
   },
   "round4-iter-2": {
    "kind": "unfolded",
    "model_calls": 125,
    "sent_wire_bytes": 50007767,
    "recorded_prompt_tokens": 12765478,
    "recorded_completion_tokens": 325953,
    "recorded_total_tokens": 13091431,
    "tokens_per_wire_byte_ratio_of_totals": 0.25527
   },
   "round4-iter-3": {
    "kind": "unfolded",
    "model_calls": 102,
    "sent_wire_bytes": 19753905,
    "recorded_prompt_tokens": 5137090,
    "recorded_completion_tokens": 86121,
    "recorded_total_tokens": 5223211,
    "tokens_per_wire_byte_ratio_of_totals": 0.260054
   },
   "livecost1-iter-1": {
    "kind": "folded",
    "model_calls": 150,
    "sent_wire_bytes": 10937231,
    "recorded_prompt_tokens": 3537843,
    "recorded_completion_tokens": 113277,
    "recorded_total_tokens": 3651120,
    "tokens_per_wire_byte_ratio_of_totals": 0.323468
   }
  }
 },
 "reconstructed_composition": {
  "message_wire_subset": "json{role, content, tool_calls, tool_call_id} as serde_json::to_string; the local-only `extra` block is excluded (exactly mini's to_llm_message)",
  "order_sent": "[system, task] then, for each model call k, the (assistant tool_call(s) + tool observation(s)) produced by steps 1..k-1",
  "system_prompt": {
   "content_chars": 14490,
   "wire_bytes": 14849,
   "identical_across_the_four": "yes except the literal iteration number in the role header (iter 1/2/3)"
  },
  "task_prompt": {
   "content_chars": 1279,
   "wire_bytes": 1365,
   "identical_across_the_four": "yes except the literal iteration number"
  },
  "first_model_call_wire_bytes": 16214,
  "first_model_call_prompt_tokens": 4269,
  "largest_single_messages": {
   "round4-iter-2": [
    "tool idx21 42467 B",
    "assistant idx150 32443 B",
    "assistant idx140 32175 B"
   ],
   "round4-iter-3": [
    "assistant idx17 45807 B",
    "tool idx10 34689 B"
   ],
   "livecost1-iter-1": [
    "tool idx314 10341 B",
    "tool idx319 8227 B (folded history: payloads replaced by notes)"
   ]
  }
 },
 "token_per_byte": {
  "primary_calibration": {
   "value": 0.256686,
   "unit": "prompt tokens per wire byte",
   "derived_from": "sum(recorded prompt_tokens)/sum(sent wire bytes) over all 296 round-4 model calls (the three UNFOLDED recordings), recomputed here from the committed corpus",
   "supporting_least_squares": {
    "slope": 0.254403,
    "intercept": 614.36,
    "worst_single_call_residual_tokens": 1159
   },
   "per_recording_ratio_of_totals": {
    "round4-iter-1": 0.25712,
    "round4-iter-2": 0.25527,
    "round4-iter-3": 0.260054
   }
  },
  "folded_live_calibration": {
   "value": 0.323468,
   "derived_from": "the livecost1 recording, whose stored history is already folded; its payloads are short JSON notes with a higher token density",
   "used_for": "the livecost1 rows only, and as the pessimistic sensitivity ratio for all rows"
  },
  "sensitivity": {
   "value": 0.323468,
   "why": "the highest density measured anywhere; applying it to the unfolded recordings is an upper bound on their cost"
  }
 },
 "policies": [
  {
   "policy": "keep_last_1_steps",
   "kind": "steps",
   "param": 1,
   "projection": {
    "round4-iter-1": {
     "total_prompt": 330007,
     "total_with_recorded_completion": 411639,
     "mean_prompt_per_call": 4783,
     "max_prompt_per_call": 8326,
     "passes_1_5m": true
    },
    "round4-iter-2": {
     "total_prompt": 677551,
     "total_with_recorded_completion": 1003504,
     "mean_prompt_per_call": 5420,
     "max_prompt_per_call": 15125,
     "passes_1_5m": true
    },
    "round4-iter-3": {
     "total_prompt": 485255,
     "total_with_recorded_completion": 571376,
     "mean_prompt_per_call": 4757,
     "max_prompt_per_call": 16063,
     "passes_1_5m": true
    },
    "livecost1-iter-1": {
     "total_prompt": 833372,
     "total_with_recorded_completion": 946649,
     "mean_prompt_per_call": 5556,
     "max_prompt_per_call": 8656,
     "passes_1_5m": true
    }
   }
  },
  {
   "policy": "keep_last_2_steps",
   "kind": "steps",
   "param": 2,
   "projection": {
    "round4-iter-1": {
     "total_prompt": 372534,
     "total_with_recorded_completion": 454166,
     "mean_prompt_per_call": 5399,
     "max_prompt_per_call": 11809,
     "passes_1_5m": true
    },
    "round4-iter-2": {
     "total_prompt": 834698,
     "total_with_recorded_completion": 1160651,
     "mean_prompt_per_call": 6678,
     "max_prompt_per_call": 18009,
     "passes_1_5m": true
    },
    "round4-iter-3": {
     "total_prompt": 545796,
     "total_with_recorded_completion": 631917,
     "mean_prompt_per_call": 5351,
     "max_prompt_per_call": 20307,
     "passes_1_5m": true
    },
    "livecost1-iter-1": {
     "total_prompt": 879834,
     "total_with_recorded_completion": 993111,
     "mean_prompt_per_call": 5866,
     "max_prompt_per_call": 12026,
     "passes_1_5m": true
    }
   }
  },
  {
   "policy": "keep_last_4_steps",
   "kind": "steps",
   "param": 4,
   "projection": {
    "round4-iter-1": {
     "total_prompt": 457470,
     "total_with_recorded_completion": 539102,
     "mean_prompt_per_call": 6630,
     "max_prompt_per_call": 14088,
     "passes_1_5m": true
    },
    "round4-iter-2": {
     "total_prompt": 1148874,
     "total_with_recorded_completion": 1474827,
     "mean_prompt_per_call": 9191,
     "max_prompt_per_call": 24611,
     "passes_1_5m": true
    },
    "round4-iter-3": {
     "total_prompt": 665955,
     "total_with_recorded_completion": 752076,
     "mean_prompt_per_call": 6529,
     "max_prompt_per_call": 33731,
     "passes_1_5m": true
    },
    "livecost1-iter-1": {
     "total_prompt": 963930,
     "total_with_recorded_completion": 1077207,
     "mean_prompt_per_call": 6426,
     "max_prompt_per_call": 16337,
     "passes_1_5m": true
    }
   }
  },
  {
   "policy": "keep_last_8_steps",
   "kind": "steps",
   "param": 8,
   "projection": {
    "round4-iter-1": {
     "total_prompt": 625724,
     "total_with_recorded_completion": 707356,
     "mean_prompt_per_call": 9068,
     "max_prompt_per_call": 19341,
     "passes_1_5m": true
    },
    "round4-iter-2": {
     "total_prompt": 1774887,
     "total_with_recorded_completion": 2100840,
     "mean_prompt_per_call": 14199,
     "max_prompt_per_call": 37423,
     "passes_1_5m": false
    },
    "round4-iter-3": {
     "total_prompt": 903055,
     "total_with_recorded_completion": 989176,
     "mean_prompt_per_call": 8853,
     "max_prompt_per_call": 38607,
     "passes_1_5m": true
    },
    "livecost1-iter-1": {
     "total_prompt": 1106173,
     "total_with_recorded_completion": 1219450,
     "mean_prompt_per_call": 7374,
     "max_prompt_per_call": 17649,
     "passes_1_5m": true
    }
   }
  },
  {
   "policy": "keep_last_12_steps",
   "kind": "steps",
   "param": 12,
   "projection": {
    "round4-iter-1": {
     "total_prompt": 792589,
     "total_with_recorded_completion": 874221,
     "mean_prompt_per_call": 11487,
     "max_prompt_per_call": 27489,
     "passes_1_5m": true
    },
    "round4-iter-2": {
     "total_prompt": 2396089,
     "total_with_recorded_completion": 2722042,
     "mean_prompt_per_call": 19169,
     "max_prompt_per_call": 48863,
     "passes_1_5m": false
    },
    "round4-iter-3": {
     "total_prompt": 1134967,
     "total_with_recorded_completion": 1221088,
     "mean_prompt_per_call": 11127,
     "max_prompt_per_call": 40894,
     "passes_1_5m": true
    },
    "livecost1-iter-1": {
     "total_prompt": 1241726,
     "total_with_recorded_completion": 1355003,
     "mean_prompt_per_call": 8278,
     "max_prompt_per_call": 18656,
     "passes_1_5m": true
    }
   }
  },
  {
   "policy": "keep_last_16_steps",
   "kind": "steps",
   "param": 16,
   "projection": {
    "round4-iter-1": {
     "total_prompt": 957185,
     "total_with_recorded_completion": 1038817,
     "mean_prompt_per_call": 13872,
     "max_prompt_per_call": 32505,
     "passes_1_5m": true
    },
    "round4-iter-2": {
     "total_prompt": 3011702,
     "total_with_recorded_completion": 3337655,
     "mean_prompt_per_call": 24094,
     "max_prompt_per_call": 59329,
     "passes_1_5m": false
    },
    "round4-iter-3": {
     "total_prompt": 1362451,
     "total_with_recorded_completion": 1448572,
     "mean_prompt_per_call": 13357,
     "max_prompt_per_call": 42365,
     "passes_1_5m": true
    },
    "livecost1-iter-1": {
     "total_prompt": 1373362,
     "total_with_recorded_completion": 1486639,
     "mean_prompt_per_call": 9156,
     "max_prompt_per_call": 19689,
     "passes_1_5m": true
    }
   }
  },
  {
   "policy": "keep_last_24_steps",
   "kind": "steps",
   "param": 24,
   "projection": {
    "round4-iter-1": {
     "total_prompt": 1279014,
     "total_with_recorded_completion": 1360646,
     "mean_prompt_per_call": 18536,
     "max_prompt_per_call": 38888,
     "passes_1_5m": true
    },
    "round4-iter-2": {
     "total_prompt": 4220830,
     "total_with_recorded_completion": 4546783,
     "mean_prompt_per_call": 33767,
     "max_prompt_per_call": 75731,
     "passes_1_5m": false
    },
    "round4-iter-3": {
     "total_prompt": 1801551,
     "total_with_recorded_completion": 1887672,
     "mean_prompt_per_call": 17662,
     "max_prompt_per_call": 44599,
     "passes_1_5m": false
    },
    "livecost1-iter-1": {
     "total_prompt": 1624927,
     "total_with_recorded_completion": 1738204,
     "mean_prompt_per_call": 10833,
     "max_prompt_per_call": 21511,
     "passes_1_5m": false
    }
   }
  },
  {
   "policy": "keep_last_32_steps",
   "kind": "steps",
   "param": 32,
   "projection": {
    "round4-iter-1": {
     "total_prompt": 1589020,
     "total_with_recorded_completion": 1670652,
     "mean_prompt_per_call": 23029,
     "max_prompt_per_call": 41905,
     "passes_1_5m": false
    },
    "round4-iter-2": {
     "total_prompt": 5379072,
     "total_with_recorded_completion": 5705025,
     "mean_prompt_per_call": 43033,
     "max_prompt_per_call": 84057,
     "passes_1_5m": false
    },
    "round4-iter-3": {
     "total_prompt": 2218890,
     "total_with_recorded_completion": 2305011,
     "mean_prompt_per_call": 21754,
     "max_prompt_per_call": 47240,
     "passes_1_5m": false
    },
    "livecost1-iter-1": {
     "total_prompt": 1861896,
     "total_with_recorded_completion": 1975173,
     "mean_prompt_per_call": 12413,
     "max_prompt_per_call": 23344,
     "passes_1_5m": false
    }
   }
  },
  {
   "policy": "keep_last_8192_wire_bytes",
   "kind": "bytes",
   "param": 8192,
   "corrected_projection_exclusive_reading": {
    "meaning": "the largest whole-step suffix whose byte total is <= B",
    "projection": {
     "round4-iter-1": {
      "total_prompt": 382708,
      "total_with_recorded_completion": 464340,
      "max_prompt_per_call": 6258,
      "mean_prompt_per_call": 5546,
      "passes_1_5m": true
     },
     "round4-iter-2": {
      "total_prompt": 655800,
      "total_with_recorded_completion": 981753,
      "max_prompt_per_call": 6261,
      "mean_prompt_per_call": 5246,
      "passes_1_5m": true
     },
     "round4-iter-3": {
      "total_prompt": 605825,
      "total_with_recorded_completion": 691946,
      "max_prompt_per_call": 6264,
      "mean_prompt_per_call": 5939,
      "passes_1_5m": true
     },
     "livecost1-iter-1": {
      "total_prompt": 1143083,
      "total_with_recorded_completion": 1256360,
      "max_prompt_per_call": 7894,
      "mean_prompt_per_call": 7621,
      "passes_1_5m": true
     }
    },
    "passes_1_5m_all_four": true
   },
   "corrected_projection_inclusive_reading": {
    "meaning": "keep adding whole steps until the running byte total reaches B",
    "projection": {
     "round4-iter-1": {
      "total_prompt": 486753,
      "total_with_recorded_completion": 568385,
      "max_prompt_per_call": 10282,
      "mean_prompt_per_call": 7054,
      "passes_1_5m": true
     },
     "round4-iter-2": {
      "total_prompt": 1170308,
      "total_with_recorded_completion": 1496261,
      "max_prompt_per_call": 17000,
      "mean_prompt_per_call": 9362,
      "passes_1_5m": true
     },
     "round4-iter-3": {
      "total_prompt": 737741,
      "total_with_recorded_completion": 823862,
      "max_prompt_per_call": 17778,
      "mean_prompt_per_call": 7233,
      "passes_1_5m": true
     },
     "livecost1-iter-1": {
      "total_prompt": 1191075,
      "total_with_recorded_completion": 1304352,
      "max_prompt_per_call": 8656,
      "mean_prompt_per_call": 7940,
      "passes_1_5m": true
     }
    },
    "passes_1_5m_all_four": true
   },
   "refuted_projection_kept_as_history": {
    "round4-iter-1": 439638,
    "round4-iter-2": 1049758,
    "round4-iter-3": 620706,
    "livecost1-iter-1": 1042497
   },
   "why_refuted": "the helper accumulated a cumulative slice into an already-inflated counter, so the loop broke early and the window actually kept was smaller than the policy names; every byte row below was optimistic,"
  },
  {
   "policy": "keep_last_16384_wire_bytes",
   "kind": "bytes",
   "param": 16384,
   "corrected_projection_exclusive_reading": {
    "meaning": "the largest whole-step suffix whose byte total is <= B",
    "projection": {
     "round4-iter-1": {
      "total_prompt": 521649,
      "total_with_recorded_completion": 603281,
      "max_prompt_per_call": 8358,
      "mean_prompt_per_call": 7560,
      "passes_1_5m": true
     },
     "round4-iter-2": {
      "total_prompt": 785393,
      "total_with_recorded_completion": 1111346,
      "max_prompt_per_call": 8333,
      "mean_prompt_per_call": 6283,
      "passes_1_5m": true
     },
     "round4-iter-3": {
      "total_prompt": 792417,
      "total_with_recorded_completion": 878538,
      "max_prompt_per_call": 8366,
      "mean_prompt_per_call": 7769,
      "passes_1_5m": true
     },
     "livecost1-iter-1": {
      "total_prompt": 1505640,
      "total_with_recorded_completion": 1618917,
      "max_prompt_per_call": 10543,
      "mean_prompt_per_call": 10038,
      "passes_1_5m": false
     }
    },
    "passes_1_5m_all_four": false
   },
   "corrected_projection_inclusive_reading": {
    "meaning": "keep adding whole steps until the running byte total reaches B",
    "projection": {
     "round4-iter-1": {
      "total_prompt": 638101,
      "total_with_recorded_completion": 719733,
      "max_prompt_per_call": 12309,
      "mean_prompt_per_call": 9248,
      "passes_1_5m": true
     },
     "round4-iter-2": {
      "total_prompt": 1402680,
      "total_with_recorded_completion": 1728633,
      "max_prompt_per_call": 19250,
      "mean_prompt_per_call": 11221,
      "passes_1_5m": false
     },
     "round4-iter-3": {
      "total_prompt": 981155,
      "total_with_recorded_completion": 1067276,
      "max_prompt_per_call": 20077,
      "mean_prompt_per_call": 9619,
      "passes_1_5m": true
     },
     "livecost1-iter-1": {
      "total_prompt": 1549272,
      "total_with_recorded_completion": 1662549,
      "max_prompt_per_call": 12026,
      "mean_prompt_per_call": 10328,
      "passes_1_5m": false
     }
    },
    "passes_1_5m_all_four": false
   },
   "refuted_projection_kept_as_history": {
    "round4-iter-1": 475707,
    "round4-iter-2": 1089968,
    "round4-iter-3": 663871,
    "livecost1-iter-1": 1111180
   },
   "why_refuted": "the helper accumulated a cumulative slice into an already-inflated counter, so the loop broke early and the window actually kept was smaller than the policy names; every byte row below was optimistic,"
  },
  {
   "policy": "keep_last_32768_wire_bytes",
   "kind": "bytes",
   "param": 32768,
   "corrected_projection_exclusive_reading": {
    "meaning": "the largest whole-step suffix whose byte total is <= B",
    "projection": {
     "round4-iter-1": {
      "total_prompt": 778970,
      "total_with_recorded_completion": 860602,
      "max_prompt_per_call": 12554,
      "mean_prompt_per_call": 11289,
      "passes_1_5m": true
     },
     "round4-iter-2": {
      "total_prompt": 1148479,
      "total_with_recorded_completion": 1474432,
      "max_prompt_per_call": 12571,
      "mean_prompt_per_call": 9188,
      "passes_1_5m": true
     },
     "round4-iter-3": {
      "total_prompt": 1135113,
      "total_with_recorded_completion": 1221234,
      "max_prompt_per_call": 12572,
      "mean_prompt_per_call": 11129,
      "passes_1_5m": true
     },
     "livecost1-iter-1": {
      "total_prompt": 2135404,
      "total_with_recorded_completion": 2248681,
      "max_prompt_per_call": 15843,
      "mean_prompt_per_call": 14236,
      "passes_1_5m": false
     }
    },
    "passes_1_5m_all_four": false
   },
   "corrected_projection_inclusive_reading": {
    "meaning": "keep adding whole steps until the running byte total reaches B",
    "projection": {
     "round4-iter-1": {
      "total_prompt": 952267,
      "total_with_recorded_completion": 1033899,
      "max_prompt_per_call": 16645,
      "mean_prompt_per_call": 13801,
      "passes_1_5m": true
     },
     "round4-iter-2": {
      "total_prompt": 1900856,
      "total_with_recorded_completion": 2226809,
      "max_prompt_per_call": 21965,
      "mean_prompt_per_call": 15207,
      "passes_1_5m": false
     },
     "round4-iter-3": {
      "total_prompt": 1494357,
      "total_with_recorded_completion": 1580478,
      "max_prompt_per_call": 23948,
      "mean_prompt_per_call": 14651,
      "passes_1_5m": false
     },
     "livecost1-iter-1": {
      "total_prompt": 2166573,
      "total_with_recorded_completion": 2279850,
      "max_prompt_per_call": 16541,
      "mean_prompt_per_call": 14444,
      "passes_1_5m": false
     }
    },
    "passes_1_5m_all_four": false
   },
   "refuted_projection_kept_as_history": {
    "round4-iter-1": 532066,
    "round4-iter-2": 1191593,
    "round4-iter-3": 728995,
    "livecost1-iter-1": 1214547
   },
   "why_refuted": "the helper accumulated a cumulative slice into an already-inflated counter, so the loop broke early and the window actually kept was smaller than the policy names; every byte row below was optimistic,"
  },
  {
   "policy": "keep_last_49152_wire_bytes",
   "kind": "bytes",
   "param": 49152,
   "corrected_projection_exclusive_reading": {
    "meaning": "the largest whole-step suffix whose byte total is <= B",
    "projection": {
     "round4-iter-1": {
      "total_prompt": 1008841,
      "total_with_recorded_completion": 1090473,
      "max_prompt_per_call": 16743,
      "mean_prompt_per_call": 14621,
      "passes_1_5m": true
     },
     "round4-iter-2": {
      "total_prompt": 1645582,
      "total_with_recorded_completion": 1971535,
      "max_prompt_per_call": 16779,
      "mean_prompt_per_call": 13165,
      "passes_1_5m": false
     },
     "round4-iter-3": {
      "total_prompt": 1446572,
      "total_with_recorded_completion": 1532693,
      "max_prompt_per_call": 16774,
      "mean_prompt_per_call": 14182,
      "passes_1_5m": false
     },
     "livecost1-iter-1": {
      "total_prompt": 2631035,
      "total_with_recorded_completion": 2744312,
      "max_prompt_per_call": 21139,
      "mean_prompt_per_call": 17540,
      "passes_1_5m": false
     }
    },
    "passes_1_5m_all_four": false
   },
   "corrected_projection_inclusive_reading": {
    "meaning": "keep adding whole steps until the running byte total reaches B",
    "projection": {
     "round4-iter-1": {
      "total_prompt": 1225192,
      "total_with_recorded_completion": 1306824,
      "max_prompt_per_call": 20380,
      "mean_prompt_per_call": 17756,
      "passes_1_5m": true
     },
     "round4-iter-2": {
      "total_prompt": 2386015,
      "total_with_recorded_completion": 2711968,
      "max_prompt_per_call": 25380,
      "mean_prompt_per_call": 19088,
      "passes_1_5m": false
     },
     "round4-iter-3": {
      "total_prompt": 1994856,
      "total_with_recorded_completion": 2080977,
      "max_prompt_per_call": 28554,
      "mean_prompt_per_call": 19557,
      "passes_1_5m": false
     },
     "livecost1-iter-1": {
      "total_prompt": 2652870,
      "total_with_recorded_completion": 2766147,
      "max_prompt_per_call": 21662,
      "mean_prompt_per_call": 17686,
      "passes_1_5m": false
     }
    },
    "passes_1_5m_all_four": false
   },
   "refuted_projection_kept_as_history": {
    "round4-iter-1": 582338,
    "round4-iter-2": 1443621,
    "round4-iter-3": 783839,
    "livecost1-iter-1": 1283793
   },
   "why_refuted": "the helper accumulated a cumulative slice into an already-inflated counter, so the loop broke early and the window actually kept was smaller than the policy names; every byte row below was optimistic,"
  },
  {
   "policy": "keep_last_65536_wire_bytes",
   "kind": "bytes",
   "param": 65536,
   "corrected_projection_exclusive_reading": {
    "meaning": "the largest whole-step suffix whose byte total is <= B",
    "projection": {
     "round4-iter-1": {
      "total_prompt": 1277032,
      "total_with_recorded_completion": 1358664,
      "max_prompt_per_call": 20964,
      "mean_prompt_per_call": 18508,
      "passes_1_5m": true
     },
     "round4-iter-2": {
      "total_prompt": 2159557,
      "total_with_recorded_completion": 2485510,
      "max_prompt_per_call": 20974,
      "mean_prompt_per_call": 17276,
      "passes_1_5m": false
     },
     "round4-iter-3": {
      "total_prompt": 1785276,
      "total_with_recorded_completion": 1871397,
      "max_prompt_per_call": 20975,
      "mean_prompt_per_call": 17503,
      "passes_1_5m": false
     },
     "livecost1-iter-1": {
      "total_prompt": 3014908,
      "total_with_recorded_completion": 3128185,
      "max_prompt_per_call": 26443,
      "mean_prompt_per_call": 20099,
      "passes_1_5m": false
     }
    },
    "passes_1_5m_all_four": false
   },
   "corrected_projection_inclusive_reading": {
    "meaning": "keep adding whole steps until the running byte total reaches B",
    "projection": {
     "round4-iter-1": {
      "total_prompt": 1472988,
      "total_with_recorded_completion": 1554620,
      "max_prompt_per_call": 24529,
      "mean_prompt_per_call": 21348,
      "passes_1_5m": false
     },
     "round4-iter-2": {
      "total_prompt": 2887584,
      "total_with_recorded_completion": 3213537,
      "max_prompt_per_call": 29339,
      "mean_prompt_per_call": 23101,
      "passes_1_5m": false
     },
     "round4-iter-3": {
      "total_prompt": 2459629,
      "total_with_recorded_completion": 2545750,
      "max_prompt_per_call": 32657,
      "mean_prompt_per_call": 24114,
      "passes_1_5m": false
     },
     "livecost1-iter-1": {
      "total_prompt": 3030267,
      "total_with_recorded_completion": 3143544,
      "max_prompt_per_call": 26770,
      "mean_prompt_per_call": 20202,
      "passes_1_5m": false
     }
    },
    "passes_1_5m_all_four": false
   },
   "refuted_projection_kept_as_history": {
    "round4-iter-1": 638631,
    "round4-iter-2": 1545769,
    "round4-iter-3": 845931,
    "livecost1-iter-1": 1350743
   },
   "why_refuted": "the helper accumulated a cumulative slice into an already-inflated counter, so the loop broke early and the window actually kept was smaller than the policy names; every byte row below was optimistic,"
  },
  {
   "policy": "keep_last_131072_wire_bytes",
   "kind": "bytes",
   "param": 131072,
   "corrected_projection_exclusive_reading": {
    "meaning": "the largest whole-step suffix whose byte total is <= B",
    "projection": {
     "round4-iter-1": {
      "total_prompt": 2176389,
      "total_with_recorded_completion": 2258021,
      "max_prompt_per_call": 37745,
      "mean_prompt_per_call": 31542,
      "passes_1_5m": false
     },
     "round4-iter-2": {
      "total_prompt": 4053810,
      "total_with_recorded_completion": 4379763,
      "max_prompt_per_call": 37793,
      "mean_prompt_per_call": 32430,
      "passes_1_5m": false
     },
     "round4-iter-3": {
      "total_prompt": 3253505,
      "total_with_recorded_completion": 3339626,
      "max_prompt_per_call": 37799,
      "mean_prompt_per_call": 31897,
      "passes_1_5m": false
     },
     "livecost1-iter-1": {
      "total_prompt": 3527720,
      "total_with_recorded_completion": 3640997,
      "max_prompt_per_call": 47561,
      "mean_prompt_per_call": 23518,
      "passes_1_5m": false
     }
    },
    "passes_1_5m_all_four": false
   },
   "corrected_projection_inclusive_reading": {
    "meaning": "keep adding whole steps until the running byte total reaches B",
    "projection": {
     "round4-iter-1": {
      "total_prompt": 2339942,
      "total_with_recorded_completion": 2421574,
      "max_prompt_per_call": 41591,
      "mean_prompt_per_call": 33912,
      "passes_1_5m": false
     },
     "round4-iter-2": {
      "total_prompt": 4655256,
      "total_with_recorded_completion": 4981209,
      "max_prompt_per_call": 46032,
      "mean_prompt_per_call": 37242,
      "passes_1_5m": false
     },
     "round4-iter-3": {
      "total_prompt": 4151075,
      "total_with_recorded_completion": 4237196,
      "max_prompt_per_call": 49596,
      "mean_prompt_per_call": 40697,
      "passes_1_5m": false
     },
     "livecost1-iter-1": {
      "total_prompt": 3528630,
      "total_with_recorded_completion": 3641907,
      "max_prompt_per_call": 47923,
      "mean_prompt_per_call": 23524,
      "passes_1_5m": false
     }
    },
    "passes_1_5m_all_four": false
   },
   "refuted_projection_kept_as_history": {
    "round4-iter-1": 739553,
    "round4-iter-2": 1852727,
    "round4-iter-3": 1046342,
    "livecost1-iter-1": 1530472
   },
   "why_refuted": "the helper accumulated a cumulative slice into an already-inflated counter, so the loop broke early and the window actually kept was smaller than the policy names; every byte row below was optimistic,"
  },
  {
   "policy": "keep_last_262144_wire_bytes",
   "kind": "bytes",
   "param": 262144,
   "corrected_projection_exclusive_reading": {
    "meaning": "the largest whole-step suffix whose byte total is <= B",
    "projection": {
     "round4-iter-1": {
      "total_prompt": 2540270,
      "total_with_recorded_completion": 2621902,
      "max_prompt_per_call": 46997,
      "mean_prompt_per_call": 36816,
      "passes_1_5m": false
     },
     "round4-iter-2": {
      "total_prompt": 7114951,
      "total_with_recorded_completion": 7440904,
      "max_prompt_per_call": 71418,
      "mean_prompt_per_call": 56920,
      "passes_1_5m": false
     },
     "round4-iter-3": {
      "total_prompt": 5070555,
      "total_with_recorded_completion": 5156676,
      "max_prompt_per_call": 64902,
      "mean_prompt_per_call": 49711,
      "passes_1_5m": false
     },
     "livecost1-iter-1": {
      "total_prompt": 3537844,
      "total_with_recorded_completion": 3651121,
      "max_prompt_per_call": 51910,
      "mean_prompt_per_call": 23586,
      "passes_1_5m": false
     }
    },
    "passes_1_5m_all_four": false
   },
   "corrected_projection_inclusive_reading": {
    "meaning": "keep adding whole steps until the running byte total reaches B",
    "projection": {
     "round4-iter-1": {
      "total_prompt": 2540270,
      "total_with_recorded_completion": 2621902,
      "max_prompt_per_call": 46997,
      "mean_prompt_per_call": 36816,
      "passes_1_5m": false
     },
     "round4-iter-2": {
      "total_prompt": 7687298,
      "total_with_recorded_completion": 8013251,
      "max_prompt_per_call": 78196,
      "mean_prompt_per_call": 61498,
      "passes_1_5m": false
     },
     "round4-iter-3": {
      "total_prompt": 5070555,
      "total_with_recorded_completion": 5156676,
      "max_prompt_per_call": 64902,
      "mean_prompt_per_call": 49711,
      "passes_1_5m": false
     },
     "livecost1-iter-1": {
      "total_prompt": 3537844,
      "total_with_recorded_completion": 3651121,
      "max_prompt_per_call": 51910,
      "mean_prompt_per_call": 23586,
      "passes_1_5m": false
     }
    },
    "passes_1_5m_all_four": false
   },
   "refuted_projection_kept_as_history": {
    "round4-iter-1": 982725,
    "round4-iter-2": 2432248,
    "round4-iter-3": 1338616,
    "livecost1-iter-1": 1770754
   },
   "why_refuted": "the helper accumulated a cumulative slice into an already-inflated counter, so the loop broke early and the window actually kept was smaller than the policy names; every byte row below was optimistic,"
  },
  {
   "policy": "keep_last_524288_wire_bytes",
   "kind": "bytes",
   "param": 524288,
   "corrected_projection_exclusive_reading": {
    "meaning": "the largest whole-step suffix whose byte total is <= B",
    "projection": {
     "round4-iter-1": {
      "total_prompt": 2540270,
      "total_with_recorded_completion": 2621902,
      "max_prompt_per_call": 46997,
      "mean_prompt_per_call": 36816,
      "passes_1_5m": false
     },
     "round4-iter-2": {
      "total_prompt": 12037738,
      "total_with_recorded_completion": 12363691,
      "max_prompt_per_call": 138736,
      "mean_prompt_per_call": 96302,
      "passes_1_5m": false
     },
     "round4-iter-3": {
      "total_prompt": 5070555,
      "total_with_recorded_completion": 5156676,
      "max_prompt_per_call": 64902,
      "mean_prompt_per_call": 49711,
      "passes_1_5m": false
     },
     "livecost1-iter-1": {
      "total_prompt": 3537844,
      "total_with_recorded_completion": 3651121,
      "max_prompt_per_call": 51910,
      "mean_prompt_per_call": 23586,
      "passes_1_5m": false
     }
    },
    "passes_1_5m_all_four": false
   },
   "corrected_projection_inclusive_reading": {
    "meaning": "keep adding whole steps until the running byte total reaches B",
    "projection": {
     "round4-iter-1": {
      "total_prompt": 2540270,
      "total_with_recorded_completion": 2621902,
      "max_prompt_per_call": 46997,
      "mean_prompt_per_call": 36816,
      "passes_1_5m": false
     },
     "round4-iter-2": {
      "total_prompt": 12367207,
      "total_with_recorded_completion": 12693160,
      "max_prompt_per_call": 148899,
      "mean_prompt_per_call": 98938,
      "passes_1_5m": false
     },
     "round4-iter-3": {
      "total_prompt": 5070555,
      "total_with_recorded_completion": 5156676,
      "max_prompt_per_call": 64902,
      "mean_prompt_per_call": 49711,
      "passes_1_5m": false
     },
     "livecost1-iter-1": {
      "total_prompt": 3537844,
      "total_with_recorded_completion": 3651121,
      "max_prompt_per_call": 51910,
      "mean_prompt_per_call": 23586,
      "passes_1_5m": false
     }
    },
    "passes_1_5m_all_four": false
   },
   "refuted_projection_kept_as_history": {
    "round4-iter-1": 1326728,
    "round4-iter-2": 3133257,
    "round4-iter-3": 1900597,
    "livecost1-iter-1": 2083683
   },
   "why_refuted": "the helper accumulated a cumulative slice into an already-inflated counter, so the loop broke early and the window actually kept was smaller than the policy names; every byte row below was optimistic,"
  }
 ],
 "passing_band": {
  "primary_calibration": {
   "max_steps_passing_all_four": 4,
   "binding_recording_steps": "round4-iter-2",
   "max_bytes_passing_all_four_EXCLUSIVE_reading": 13543,
   "max_bytes_passing_all_four_INCLUSIVE_reading": 8443,
   "binding_recording_bytes_exclusive": "livecost1-iter-1",
   "binding_recording_bytes_inclusive": "round4-iter-2",
   "refuted_value_for_max_bytes_passing_all_four": 49152,
   "byte_band_correction": "the stated policy is ambiguous at the grain of one step; both readings are reported. Exclusive = the largest whole-step suffix whose byte total is <= B (13,543; live 1,499,796, fails at 13,544 with 1,500,020). Inclusive = keep adding whole steps until the running total reaches B (8,443; iter-2 1,499,039, fails at 8,444 with 1,500,171). The 49,152 this file claimed came from an accumulator that over-counted, so the window it actually kept was smaller than the policy it named.",
   "note": "the band edges are the largest values where every recording passes; independently re-measured in .spec/bevy/SPIKE-COST-LEVERS.md"
  },
  "sensitivity_ratio_0.323468": {
   "max_steps_passing_all_four": 2,
   "max_bytes_passing_all_four_EXCLUSIVE_reading": 13543,
   "max_bytes_passing_all_four_INCLUSIVE_reading": 2782,
   "refuted_value_for_max_bytes_passing_all_four": 32768,
   "binding_recording_bytes_inclusive": "round4-iter-2",
   "byte_band_correction": "the sensitivity byte band is 13,543 (exclusive) or 2,782 (inclusive), not 32,768; the exclusive edge is set by livecost1-iter-1 (1,499,796, fails at 13,544 with 1,500,020) and the inclusive edge by round4-iter-2 (1,499,244, fails at 2,783 with 1,509,795)"
  },
  "criterion": "total_tokens (prompt + completion) per Developer role call < 1,500,000",
  "completion_tokens_are_recorded_and_held_fixed": true
 },
 "dependency_edges_successful_writes_only": {
  "round4-iter-1": {
   "successful_write_events_all_paths": 6,
   "successful_project_write_events": 6,
   "scratch_write_events": 0,
   "read_or_write_to_write_edges": 6,
   "largest_gaps_steps": [
    {
     "file": "src/game.rs",
     "from": 3,
     "from_kind": "read",
     "write": 8,
     "gap_steps": 5,
     "write_kind": "directive"
    },
    {
     "file": "src/contract.rs",
     "from": 3,
     "from_kind": "read",
     "write": 7,
     "gap_steps": 4,
     "write_kind": "directive"
    },
    {
     "file": "src/game.rs",
     "from": 14,
     "from_kind": "write",
     "write": 18,
     "gap_steps": 4,
     "write_kind": "directive"
    },
    {
     "file": "src/game.rs",
     "from": 11,
     "from_kind": "read",
     "write": 13,
     "gap_steps": 2,
     "write_kind": "directive"
    }
   ]
  },
  "round4-iter-2": {
   "successful_write_events_all_paths": 23,
   "successful_project_write_events": 11,
   "scratch_write_events": 12,
   "label_correction": "the 23 this file reported as successful_project_write_events is not project-only: it is 11 project writes (all src/game.rs) plus 12 .hoh/scratch/** writes (dump.py, dump2.py, empty.json, timeline.md, geometry.md, patch.py, final_geom.md, patch2.py..patch5.py, iteration2-summary.md). The old value is kept by the previously-named key as history.",
   "read_or_write_to_write_edges": 11,
   "largest_gaps_steps": [
    {
     "file": "src/game.rs",
     "from": 5,
     "from_kind": "read",
     "write": 33,
     "gap_steps": 28,
     "write_kind": "directive"
    },
    {
     "file": "src/game.rs",
     "from": 55,
     "from_kind": "write",
     "write": 65,
     "gap_steps": 10,
     "write_kind": "directive"
    },
    {
     "file": "src/game.rs",
     "from": 37,
     "from_kind": "write",
     "write": 42,
     "gap_steps": 5,
     "write_kind": "directive"
    },
    {
     "file": "src/game.rs",
     "from": 67,
     "from_kind": "write",
     "write": 72,
     "gap_steps": 5,
     "write_kind": "directive"
    }
   ]
  },
  "round4-iter-3": {
   "successful_write_events_all_paths": 19,
   "successful_project_write_events": 9,
   "scratch_write_events": 10,
   "label_correction": "19 is all-path, not project-only: 9 project writes (1 directive + 1 shell + 7 script-mediated) plus 10 .hoh/scratch/** writes. The old value is kept by the previously-named key as history.",
   "read_or_write_to_write_edges": 9,
   "largest_gaps_steps": [
    {
     "file": "src/game.rs",
     "from": 71,
     "from_kind": "read",
     "write": 75,
     "gap_steps": 4,
     "write_kind": "script:tweak3.ps1"
    },
    {
     "file": "src/game.rs",
     "from": 87,
     "from_kind": "write",
     "write": 91,
     "gap_steps": 4,
     "write_kind": "script:tweak7.ps1"
    },
    {
     "file": "src/game.rs",
     "from": 3,
     "from_kind": "read",
     "write": 6,
     "gap_steps": 3,
     "write_kind": "directive"
    },
    {
     "file": "src/game.rs",
     "from": 91,
     "from_kind": "write",
     "write": 94,
     "gap_steps": 3,
     "write_kind": "script:tweak8.ps1"
    }
   ]
  },
  "livecost1-iter-1": {
   "successful_write_events_all_paths": 1,
   "successful_project_write_events": 0,
   "scratch_write_events": 1,
   "label_correction": "1 is all-path, not project-only: the single detected event is a .hoh/scratch/notes.md write; this recording is folded and 0 project writes are detected. The old value is kept by the previously-named key as history.",
   "read_or_write_to_write_edges": 0,
   "largest_gaps_steps": []
  }
 },
 "what_each_policy_would_cut": {
  "method": "for every successful write to a project file, the most recent earlier message that still carried that file (a read of it, or the write that last produced it) is located; the edge is 'dropped' when that step is outside the window at that write's call",
  "dropped_edges_by_policy": {
   "N2": {
    "round4-iter-1": [
     {
      "file": "src/game.rs",
      "from": 3,
      "from_kind": "read",
      "write": 8,
      "gap_steps": 5
     },
     {
      "file": "src/contract.rs",
      "from": 3,
      "from_kind": "read",
      "write": 7,
      "gap_steps": 4
     },
     {
      "file": "src/game.rs",
      "from": 14,
      "from_kind": "write",
      "write": 18,
      "gap_steps": 4
     }
    ],
    "round4-iter-2": [
     {
      "file": "src/game.rs",
      "from": 5,
      "from_kind": "read",
      "write": 33,
      "gap_steps": 28
     },
     {
      "file": "src/game.rs",
      "from": 55,
      "from_kind": "write",
      "write": 65,
      "gap_steps": 10
     },
     {
      "file": "src/game.rs",
      "from": 37,
      "from_kind": "write",
      "write": 42,
      "gap_steps": 5
     },
     {
      "file": "src/game.rs",
      "from": 67,
      "from_kind": "write",
      "write": 72,
      "gap_steps": 5
     },
     {
      "file": "src/game.rs",
      "from": 51,
      "from_kind": "read",
      "write": 55,
      "gap_steps": 4
     }
    ],
    "round4-iter-3": [
     {
      "file": "src/game.rs",
      "from": 71,
      "from_kind": "read",
      "write": 75,
      "gap_steps": 4
     },
     {
      "file": "src/game.rs",
      "from": 87,
      "from_kind": "write",
      "write": 91,
      "gap_steps": 4
     },
     {
      "file": "src/game.rs",
      "from": 3,
      "from_kind": "read",
      "write": 6,
      "gap_steps": 3
     },
     {
      "file": "src/game.rs",
      "from": 91,
      "from_kind": "write",
      "write": 94,
      "gap_steps": 3
     }
    ]
   },
   "N4": {
    "round4-iter-1": [
     {
      "file": "src/game.rs",
      "from": 3,
      "from_kind": "read",
      "write": 8,
      "gap_steps": 5
     }
    ],
    "round4-iter-2": [
     {
      "file": "src/game.rs",
      "from": 5,
      "from_kind": "read",
      "write": 33,
      "gap_steps": 28
     },
     {
      "file": "src/game.rs",
      "from": 55,
      "from_kind": "write",
      "write": 65,
      "gap_steps": 10
     },
     {
      "file": "src/game.rs",
      "from": 37,
      "from_kind": "write",
      "write": 42,
      "gap_steps": 5
     },
     {
      "file": "src/game.rs",
      "from": 67,
      "from_kind": "write",
      "write": 72,
      "gap_steps": 5
     }
    ],
    "round4-iter-3": []
   },
    "B13543_exclusive_corrected": {
     "round4-iter-1": [
      {
       "file": "src/game.rs",
       "from": 3,
       "from_kind": "read",
       "write": 8,
       "gap_steps": 5,
       "write_kind": "directive"
      },
      {
       "file": "src/contract.rs",
       "from": 3,
       "from_kind": "read",
       "write": 7,
       "gap_steps": 4,
       "write_kind": "directive"
      },
      {
       "file": "src/game.rs",
       "from": 14,
       "from_kind": "write",
       "write": 18,
       "gap_steps": 4,
       "write_kind": "directive"
      },
      {
       "file": "src/game.rs",
       "from": 13,
       "from_kind": "write",
       "write": 14,
       "gap_steps": 1,
       "write_kind": "directive"
      }
     ],
     "round4-iter-2": [
      {
       "file": "src/game.rs",
       "from": 5,
       "from_kind": "read",
       "write": 33,
       "gap_steps": 28,
       "write_kind": "directive"
      },
      {
       "file": "src/game.rs",
       "from": 55,
       "from_kind": "write",
       "write": 65,
       "gap_steps": 10,
       "write_kind": "directive"
      },
      {
       "file": "src/game.rs",
       "from": 37,
       "from_kind": "write",
       "write": 42,
       "gap_steps": 5,
       "write_kind": "directive"
      },
      {
       "file": "src/game.rs",
       "from": 67,
       "from_kind": "write",
       "write": 72,
       "gap_steps": 5,
       "write_kind": "directive"
      },
      {
       "file": "src/game.rs",
       "from": 51,
       "from_kind": "read",
       "write": 55,
       "gap_steps": 4,
       "write_kind": "directive"
      },
      {
       "file": "src/game.rs",
       "from": 33,
       "from_kind": "write",
       "write": 35,
       "gap_steps": 2,
       "write_kind": "directive"
      },
      {
       "file": "src/game.rs",
       "from": 42,
       "from_kind": "write",
       "write": 44,
       "gap_steps": 2,
       "write_kind": "directive"
      },
      {
       "file": "src/game.rs",
       "from": 44,
       "from_kind": "write",
       "write": 46,
       "gap_steps": 2,
       "write_kind": "directive"
      },
      {
       "file": "src/game.rs",
       "from": 65,
       "from_kind": "write",
       "write": 67,
       "gap_steps": 2,
       "write_kind": "directive"
      },
      {
       "file": "src/game.rs",
       "from": 35,
       "from_kind": "write",
       "write": 36,
       "gap_steps": 1,
       "write_kind": "directive"
      },
      {
       "file": "src/game.rs",
       "from": 36,
       "from_kind": "write",
       "write": 37,
       "gap_steps": 1,
       "write_kind": "directive"
      }
     ],
     "round4-iter-3": [
      {
       "file": "src/game.rs",
       "from": 3,
       "from_kind": "read",
       "write": 6,
       "gap_steps": 3,
       "write_kind": "directive"
      },
      {
       "file": "src/game.rs",
       "from": 6,
       "from_kind": "write",
       "write": 8,
       "gap_steps": 2,
       "write_kind": "shell"
      }
     ]
    },
    "B8443_inclusive_corrected": {
     "round4-iter-1": [
      {
       "file": "src/game.rs",
       "from": 3,
       "from_kind": "read",
       "write": 8,
       "gap_steps": 5,
       "write_kind": "directive"
      },
      {
       "file": "src/contract.rs",
       "from": 3,
       "from_kind": "read",
       "write": 7,
       "gap_steps": 4,
       "write_kind": "directive"
      }
     ],
     "round4-iter-2": [
      {
       "file": "src/game.rs",
       "from": 5,
       "from_kind": "read",
       "write": 33,
       "gap_steps": 28,
       "write_kind": "directive"
      },
      {
       "file": "src/game.rs",
       "from": 55,
       "from_kind": "write",
       "write": 65,
       "gap_steps": 10,
       "write_kind": "directive"
      }
     ],
     "round4-iter-3": [
      {
       "file": "src/game.rs",
       "from": 3,
       "from_kind": "read",
       "write": 6,
       "gap_steps": 3,
       "write_kind": "directive"
      }
     ]
    },
    "B16384_and_B32768_refuted_windows_kept_as_history": {
     "why": "the rows this file published for B16384/B32768 were produced by the over-counting accumulator, so they are not the policy they name; at the corrected B=13543 exclusive iter-2 drops 11 of 11 edges (the file claimed 6 at B32768) and iter-1 drops 4 of 6",
     "claim_deleted": {
      "B16384_iter2": 9,
      "B32768_iter2": 6,
      "B16384_iter1": 3,
      "B32768_iter1": 2
     }
    }
  },
  "the_decisive_case": {
   "recording": "round4-iter-2",
   "read_call": 5,
   "write_call": 33,
   "gap_steps": 28,
   "evidence": "call 5 runs `type src\\game.rs` and the recorded observation is the whole 14,902-byte file; calls 6..32 contain no other read of src/game.rs (only an `echo HOH_WRITE_FILE src/game.rs` probe at call 13 and the bevy-dev.md skill text at call 32); call 33 is a full `HOH_WRITE_FILE src/game.rs` whose recorded content is that same file evolved (same header, same constants, COIN_XS widened to two coins). Any window that passes iter-2 keeps at most 4 steps, so this read is not in context at call 33."
  },
  "other_dropped_edges_at_the_passing_edge": {
   "N4": {
    "round4-iter-1": [
     "src/game.rs read@3 -> write@8 (gap 5)"
    ],
    "round4-iter-2": [
     "src/game.rs read@5 -> write@33 (gap 28)",
     "src/game.rs write@55 -> write@65 (gap 10)",
     "src/game.rs write@37 -> write@42 (gap 5)",
     "src/game.rs write@67 -> write@72 (gap 5)"
    ],
    "round4-iter-3": []
   },
   "B13543_exclusive_corrected": {
    "round4-iter-1": [
     "src/game.rs read@3 -> write@8 (gap 5)",
     "src/contract.rs read@3 -> write@7 (gap 4)",
     "src/game.rs write@14 -> write@18 (gap 4)",
     "src/game.rs write@13 -> write@14 (gap 1)"
    ],
    "round4-iter-2": [
     "src/game.rs read@5 -> write@33 (gap 28)",
     "src/game.rs write@55 -> write@65 (gap 10)",
     "src/game.rs write@37 -> write@42 (gap 5)",
     "src/game.rs write@67 -> write@72 (gap 5)",
     "src/game.rs read@51 -> write@55 (gap 4)",
     "src/game.rs write@33 -> write@35 (gap 2)",
     "src/game.rs write@42 -> write@44 (gap 2)",
     "src/game.rs write@44 -> write@46 (gap 2)",
     "src/game.rs write@65 -> write@67 (gap 2)",
     "src/game.rs write@35 -> write@36 (gap 1)",
     "src/game.rs write@36 -> write@37 (gap 1)"
    ],
    "round4-iter-3": [
     "src/game.rs read@3 -> write@6 (gap 3)",
     "src/game.rs write@6 -> write@8 (gap 2)"
    ]
   },
   "B8443_inclusive_corrected": {
    "round4-iter-1": [
     "src/game.rs read@3 -> write@8 (gap 5)",
     "src/contract.rs read@3 -> write@7 (gap 4)"
    ],
    "round4-iter-2": [
     "src/game.rs read@5 -> write@33 (gap 28)",
     "src/game.rs write@55 -> write@65 (gap 10)"
    ],
    "round4-iter-3": [
     "src/game.rs read@3 -> write@6 (gap 3)"
    ]
   },
   "B16384_and_B32768_refuted_windows_kept_as_history": {
    "why": "computed with the over-counting accumulator; not the policy they name",
    "B16384_round4-iter-2_claim_deleted": "9 dropped edges (the corrected policy at 16,384 bytes drops 11 of 11)",
    "B32768_round4-iter-2_claim_deleted": "6 dropped edges, 'the gap-28 edge and five more' (kept only as history)"
   }
  }
 },
 "verdict": {
  "any_bounded_history_policy_projected_to_pass": true,
  "any_bounded_history_policy_projected_to_pass_without_discarding_used_content": false,
  "confidence": "high on the discard finding (the recorded gaps are >= the passing window by construction of the same measurement); medium on the projection (it holds the recorded call sequence fixed and assumes a dropped message is the only change)",
  "single_most_important_thing": "The passing band and the recorded read->edit dependency distance do not overlap: to come under 1.5M the window must keep at most 4 steps (2 under the measured folded token density), while the recorded developer read src/game.rs whole at iter-2 call 5 and rewrote it at call 33 with no other read in between (28 steps), and still had content-relevant reads 5-10 steps before the writes at iter-1 and iter-3. A recency window that passes is exactly a window that discards information the role used."
 },
  "correction_record": {
   "date": "2026-10-06",
   "what_changed": "the byte-window policy table, passing_band.max_bytes_passing_all_four and the byte side of the sensitivity band were re-measured and corrected; the write-event count columns were relabelled",
   "byte_band_before": {
    "primary": 49152,
    "sensitivity": 32768
   },
   "byte_band_after": {
    "primary_exclusive": 13543,
    "primary_inclusive": 8443,
    "sensitivity_exclusive": 13543,
    "sensitivity_inclusive": 2782
   },
   "cause": "the helper accumulated a cumulative slice into an already-inflated counter, so the window actually kept was smaller than the policy names; every byte row was optimistic",
   "unaffected": "the step policy table and its boundary (N=4 passes by 25,174 tokens on round4-iter-2; N=5 fails at 1,631,524-1,631,527 depending on rounding), the token-per-byte calibration, the reconstructed corpus and the decisive 28-step read->write case",
   "label_defect": "successful_project_write_events was not project-only: 6/23/19/1 all-path = 6/11/9/0 project + 0/12/10/1 scratch",
   "re_measured_by": ".spec/bevy/SPIKE-COST-LEVERS.md (independent offline re-measurement)"
 },
 "gate": {
  "command": "cargo test --offline",
  "exit_code": 0,
  "build_dir": "F:/spike-hw-target (this spike's own; the repository's own target/ was not used)",
  "passed": 800,
  "failed": 0,
  "ignored": 6,
  "listed": 806,
  "test_result_lines": 60,
  "listed_equals_passed_plus_ignored": true,
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
  "first_run_says_what": "the first execution of the same command returned exit 101 with 440 passed / 1 failed / 0 ignored / 441 listed (cargo stops at the first failing target): adapter::bevy::brp::tests::a_slow_reply_that_exceeds_the_timeout_is_a_timeout failed with `expected a timeout, got Transport { ... }`. That test passed in isolation immediately afterwards and the whole gate then returned exit 0 with the start-tree numbers above, so the failure is a timing flake of that test under load, not a tree change; both runs are reported rather than only the clean one.",
  "working_tree": "git status --porcelain was empty before the gate and before this report was added; this spike committed and pushed nothing"
 },
 "what_i_could_not_establish": [
  "No live call was made, so the projection is not confirmed against a real windowed prompt. The projection holds the recorded call sequence fixed and changes only the size of each prompt; a role that no longer sees what it dropped would plausibly issue re-reads and take more calls, which the projection cannot show.",
  "The round-4 recordings are unfolded and the livecost1 recording is folded (the fold shipped after round 4). There is no recording of a run that used a bounded window instead of the fold, or of one that used both. The live rows are therefore 'a window applied on top of an already-folded history', and its content analysis is impossible: its payloads are notes (live call 6's write is `superseded tool call folded: fb568db0754e (9005 byte(s))`).",
  "The dependency measurement covers explicit file reads and successful writes it can see (directive writes, shell write primitives, and scripts the role wrote and then ran). A read that arrived inside a command's output without naming the path (a build error quoting source, a diff, a `findstr` context) is not counted; the analysis is therefore a lower bound on the content that was used later, not an upper bound.",
  "Whether a windowed role would re-read each file just in time (cheap per call, but it moves the call count and can hit the 150-step limit) is a behavioural question the recorded data can only suggest, not answer: the live call ran 172 shell commands, 166 distinct, most of them reads of the role's own files.",
  "The pass/fail edge is a fitness against a fixed 1,500,000-token criterion; the completion tokens are held at their recorded values because no history policy changes what the model answers."
 ],
 "method_limits": [
  "A 'step' is one provider response plus the observation messages that follow it, located by the message carrying extra.response.usage; the prompt for model call k is messages[0:k], i.e. the system prompt, the task, and steps 1..k-1.",
  "A window keeps whole steps, so a tool call and its result can never be split (the provider validates the pairing). A message-granular implementation would differ by at most one partially kept step.",
  "The window keeps the system prompt and the task unconditionally, per the task's statement of the policy.",
  "'keep the last N steps' at call k keeps steps k-N..k-1. An implementation that additionally counted the current step would behave like N+1 here.",
  "The step limit (150) and the tripwire of .spec/bevy/COST-REPORT.md are not part of this replay; the recorded call counts are used as recorded."
 ]
}
```

# SPIKE — the bounded-history window, replayed offline over the committed cost corpus

> **Correction, 2026-10-06.** The byte-window half of this report was independently re-measured and is
> wrong by 3.6x-5.8x: the stated policy passes all four recordings at **B = 13,543 wire bytes**
> (exclusive) or **8,443** (inclusive), not 49,152, and at **13,543 / 2,782** under the pessimistic
> ratio, not 32,768. The cause was a byte-window accumulator that over-counted; the refuted values are
> kept below as labelled history. The **step-window** table, its boundary, the token-per-byte
> calibration and the 28-step decisive case are unaffected and were reproduced to the token. The
> write-event column was also mislabelled (it is not project-only). See section 9 and
> `.spec/bevy/SPIKE-COST-LEVERS.md` for the re-measurement and for the four further cost levers.

**Scope.** Offline arithmetic over files that already exist. No round was run, no model call was made,
no engine started, no network was used. Nothing under `src/**`, `tests/**`, `evidence/**`, `runs/**`,
`config/**` or any frozen document was written; the only file this spike added to the repository is
this report. The helper scripts live outside the repository, at `F:/spike-history-window/`. Nothing was
committed or pushed. Numbers are labelled **measured** (read out of the recordings or the code) or
**projected** (arithmetic over measured bytes).

## 1. Method, and the per-call composition that could be reconstructed (measured)

Read: `evidence/cost/{livecost1-iter-1,round4-iter-1,round4-iter-2,round4-iter-3}.developer.attempt1.json`;
`src/harness/compact.rs` (`message_wire_bytes`, `compact_history`), `src/harness/mini.rs`,
`src/harness/guard.rs`, `config/hoh.yaml` (`step_limit: 150`, `compact_history: true`,
`compact_history_tail: 12`), and the trajectory reader the existing measurement uses,
`tests/context_compaction.rs`; plus `.spec/bevy/COST-REPORT.md`, `.spec/bevy/LIVE-COST-REPORT.md`,
`.spec/bevy/FIX-REPORT.md`, `.spec/bevy/WRITE-ACCOUNTING-REPORT.md` and `DECISIONS.md`
D298(e), D299, D301(g), D302, D303(d), D304.

I recomputed the wire size of every message with the same subset the repository uses — the JSON object
`{role, content, tool_calls, tool_call_id}` serialised compactly, with the local-only `extra` block
excluded — and located each model call at the message that carries `extra.response.usage`. The prompt
for model call *k* is therefore `messages[0:k]`: the **system prompt**, the **task prompt**, then one
**step** per earlier model call, where a step is that call's assistant tool-call message(s) followed by
their tool observation(s). This reconstruction reproduces the repository's own published numbers
exactly, which is the check that it is the same measurement (measured):

* round4-iter-2 sent wire bytes **50,007,767** = `COST-REPORT.md` `tail_curve_wire_bytes_iter_2.sent`;
  recorded prompt **12,765,478**; system prompt **14,849 wire bytes** (`F-2`);
* round4-iter-1 **9,896,402** B, round4-iter-3 **19,753,905** B (the report's "9.90 MB" / "19.75 MB").

| recording | history | model calls | sent wire B | recorded prompt | completion | recorded total | tokens/wire-byte |
|---|---|---|---|---|---|---|---|
| round4-iter-1 | unfolded | 69 | 9,896,402 | 2,544,563 | 81,632 | 2,626,195 | 0.257120 |
| round4-iter-2 | unfolded | 125 | 50,007,767 | 12,765,478 | 325,953 | 13,091,431 | 0.255270 |
| round4-iter-3 | unfolded | 102 | 19,753,905 | 5,137,090 | 86,121 | 5,223,211 | 0.260054 |
| livecost1-iter-1 | folded | 150 | 10,937,231 | 3,537,843 | 113,277 | 3,651,120 | 0.323468 |

The **system prompt** is 14,490 characters / **14,849 wire bytes**; the **task prompt** is 1,279
characters / **1,365 wire bytes**. The two are byte-identical across all four recordings except for the
literal iteration number in the role header (`Developer (iteration 1/2/3)`), so the first model call is
the same **16,214 wire bytes -> 4,269 recorded prompt tokens** in all four.

Per-message sizes are extremely skewed (measured): the largest single message is 45,807 B in iter-3
(an `HOH_WRITE_FILE src/game.rs` argument carrying the whole file) and 42,467 B in iter-2 (a tool
observation dumping a file). The live recording has no message over 10,341 B: it is **folded**, so its
payloads are notes (live call 6's write is literally
`"superseded tool call folded: fb568db0754e (9005 byte(s)) of arguments were sent and acted on ..."`).
That difference is why the live recording cannot answer whether a window discards *content*. There is no
"completion bytes" figure in the recordings — the provider records completion *tokens* (the column
above), and this spike holds them fixed because a history policy does not change what the model answers.

## 2. The token-per-byte relation, computed here (measured)

There is no one number; there are two regimes, and both are in the corpus.

* **Unfolded real content (the round-4 corpus, three recordings, 296 model calls):**
  `sum(prompt_tokens) / sum(wire_bytes) = 20,447,131 / 79,658,074` = **0.256686 tokens per wire byte**.
  Per recording the ratio-of-totals is 0.257120 / 0.255270 / 0.260054, and a least-squares fit over the
  pooled 296 calls gives slope **0.254403**, intercept 614.36, worst single-call residual **1,159**
  tokens. Fitted on iter-2 alone the slope is **0.255366** with intercept -38.28 and worst residual
  1,347 — which reproduces the repository's own quoted figure (`D301(g)`, `COST-REPORT.md`) exactly.
* **Folded notes (the live recording):** 0.323468 tokens per wire byte (the repository measured this as
  26.7 percent over the round-4 fit, `LIVE-COST-REPORT.md`; I recomputed 3,537,843 / 10,937,231 = the
  same).

A direct, model-free check of the scale: the first call carries only the system prompt and the task,
16,214 wire bytes -> 4,269 recorded prompt tokens = **0.2633 tokens/byte**.

I use **0.256686** as the primary calibration for the three unfolded recordings (their bytes are real
content), the live recording's own **0.323468** for the live rows, and 0.323468 applied to everything as
a pessimistic sensitivity — it is the densest text measured anywhere, so it is an upper bound on the
unfolded rows.

## 3. The replay (projected)

For every recorded model call *k* I recompute the prompt's wire bytes under:

* **keep the last N steps**: `system + task + steps k-N ... k-1`; and
* **keep the last B wire bytes of steps**: whole steps counted backwards from the newest until B is
  reached (a step is never split, because a tool call and its result must stay paired).

Then `projected_prompt = ratio x windowed_wire_bytes`, and
`projected_total = sum(projected_prompt) + the recording's whole recorded completion`. The criterion is
**total_tokens per Developer role call < 1,500,000**.

Totals per policy (**projected**; `FAIL` = above 1,500,000):

| policy | r4-i1 | r4-i2 | r4-i3 | live | all four |
|---|---|---|---|---|---|
| `1 steps` | 411,639 | 1,003,504 | 571,376 | 946,649 | pass |
| `2 steps` | 454,166 | 1,160,651 | 631,917 | 993,111 | pass |
| `4 steps` | 539,102 | 1,474,827 | 752,076 | 1,077,207 | pass |
| `8 steps` | 707,356 | 2,100,840 FAIL | 989,176 | 1,219,450 | FAIL |
| `12 steps` | 874,221 | 2,722,042 FAIL | 1,221,088 | 1,355,003 | FAIL |
| `16 steps` | 1,038,817 | 3,337,655 FAIL | 1,448,572 | 1,486,639 | FAIL |
| `24 steps` | 1,360,646 | 4,546,783 FAIL | 1,887,672 FAIL | 1,738,204 FAIL | FAIL |
| `32 steps` | 1,670,652 FAIL | 5,705,025 FAIL | 2,305,011 FAIL | 1,975,173 FAIL | FAIL |
| `8192 B` | 464,340 | 981,753 | 691,946 | 1,256,360 | pass |
| `16384 B` | 603,281 | 1,111,346 | 878,538 | 1,618,917 FAIL | FAIL |
| `32768 B` | 860,602 | 1,474,432 | 1,221,234 | 2,248,681 FAIL | FAIL |
| `49152 B` | 1,090,473 | 1,971,535 FAIL | 1,532,693 FAIL | 2,744,312 FAIL | FAIL |
| `65536 B` | 1,358,664 | 2,485,510 FAIL | 1,871,397 FAIL | 3,128,185 FAIL | FAIL |
| `131072 B` | 2,258,021 FAIL | 4,379,763 FAIL | 3,339,626 FAIL | 3,640,997 FAIL | FAIL |
| `262144 B` | 2,621,902 FAIL | 7,440,904 FAIL | 5,156,676 FAIL | 3,651,121 FAIL | FAIL |
| `524288 B` | 2,621,902 FAIL | 12,363,691 FAIL | 5,156,676 FAIL | 3,651,121 FAIL | FAIL |

The rows above are the **exclusive** reading, corrected by re-measurement. Under the **inclusive**
reading (`keep adding whole steps until the running total reaches B`) the same policies give:

| policy | r4-i1 | r4-i2 | r4-i3 | live | all four |
|---|---|---|---|---|---|
| `8192 B` | 568,385 | 1,496,261 | 823,862 | 1,304,352 | pass |
| `16384 B` | 719,733 | 1,728,633 FAIL | 1,067,276 | 1,662,549 FAIL | FAIL |
| `32768 B` | 1,033,899 | 2,226,809 FAIL | 1,580,478 FAIL | 2,279,850 FAIL | FAIL |
| `49152 B` | 1,306,824 | 2,711,968 FAIL | 2,080,977 FAIL | 2,766,147 FAIL | FAIL |
| `65536 B` | 1,554,620 FAIL | 3,213,537 FAIL | 2,545,750 FAIL | 3,143,544 FAIL | FAIL |
| `131072 B` | 2,421,574 FAIL | 4,981,209 FAIL | 4,237,196 FAIL | 3,641,907 FAIL | FAIL |
| `262144 B` | 2,621,902 FAIL | 8,013,251 FAIL | 5,156,676 FAIL | 3,651,121 FAIL | FAIL |
| `524288 B` | 2,621,902 FAIL | 12,693,160 FAIL | 5,156,676 FAIL | 3,651,121 FAIL | FAIL |

Mean / **max** prompt tokens per model call (**projected**):

| policy | r4-i1 mean/max | r4-i2 mean/max | r4-i3 mean/max | live mean/max |
|---|---|---|---|---|
| `1 steps` | 4,783 / 8,326 | 5,420 / 15,125 | 4,757 / 16,063 | 5,556 / 8,656 |
| `2 steps` | 5,399 / 11,809 | 6,678 / 18,009 | 5,351 / 20,307 | 5,866 / 12,026 |
| `4 steps` | 6,630 / 14,088 | 9,191 / 24,611 | 6,529 / 33,731 | 6,426 / 16,337 |
| `8 steps` | 9,068 / 19,341 | 14,199 / 37,423 | 8,853 / 38,607 | 7,374 / 17,649 |
| `12 steps` | 11,487 / 27,489 | 19,169 / 48,863 | 11,127 / 40,894 | 8,278 / 18,656 |
| `16 steps` | 13,872 / 32,505 | 24,094 / 59,329 | 13,357 / 42,365 | 9,156 / 19,689 |
| `24 steps` | 18,536 / 38,888 | 33,767 / 75,731 | 17,662 / 44,599 | 10,833 / 21,511 |
| `32 steps` | 23,029 / 41,905 | 43,033 / 84,057 | 21,754 / 47,240 | 12,413 / 23,344 |
| `8192 B` | 5,546 / 6,258 | 5,246 / 6,261 | 5,939 / 6,264 | 7,621 / 7,894 |
| `16384 B` | 7,560 / 8,358 | 6,283 / 8,333 | 7,769 / 8,366 | 10,038 / 10,543 |
| `32768 B` | 11,289 / 12,554 | 9,188 / 12,571 | 11,129 / 12,572 | 14,236 / 15,843 |
| `49152 B` | 14,621 / 16,743 | 13,165 / 16,779 | 14,182 / 16,774 | 17,540 / 21,139 |
| `65536 B` | 18,508 / 20,964 | 17,276 / 20,974 | 17,503 / 20,975 | 20,099 / 26,443 |
| `131072 B` | 31,542 / 37,745 | 32,430 / 37,793 | 31,897 / 37,799 | 23,518 / 47,561 |
| `262144 B` | 36,816 / 46,997 | 56,920 / 71,418 | 49,711 / 64,902 | 23,586 / 51,910 |
| `524288 B` | 36,816 / 46,997 | 96,302 / 138,736 | 49,711 / 64,902 | 23,586 / 51,910 |

**The passing band (projected).** Under the primary calibration, the largest window that keeps *all
four* recorded calls under the criterion is **N = 4 steps** or **B = 13,543 wire bytes** (the
*exclusive* reading of "until B is reached"; **8,443** under the *inclusive* reading); the binding
recording is **round4-iter-2** for the step side (N=4 -> 1,474,827 total; N=5 -> 1,631,526) and
**livecost1-iter-1** (1,499,796; fails at 13,544 with 1,500,020) for the exclusive byte side.
Under the pessimistic 0.323468-everywhere sensitivity the step band shrinks to **N = 2** and the byte
band to **B = 13,543 exclusive / 2,782 inclusive**, the latter bound by iter-2 (1,499,244; fails at
2,783 with 1,509,795). N = 1 and B = 8 KiB pass everywhere with room to spare (iter-2 projects to
1,003,504 at N=1). For reference, iter-2's recorded total is **13,091,431** and the live call's is
**3,651,120**, so a passing window is a ~90 percent cut of the prompt spend.
**[CORRECTED 2026-10-06: this paragraph said `B = 49,152` and `B = 32,768`. Those two values came
from a byte-window accumulator that over-counted and closed the loop early, so the window it kept was
smaller than the policy it named; every byte row in this report was optimistic by 3.6x-5.8x. The
refuted values are kept as labelled history in the machine block and in section 9. The step side of
this paragraph is unaffected and reproduces to the token.]**

## 4. What each policy would actually cut (edges measured, consequence projected)

For every **successful** write to a project file (`src/**`, `tests/**`, `Cargo.toml`) — directive writes,
shell writes (`Set-Content`, `WriteAllText`, ...) and scripts the role wrote and then ran — I located the
most recent earlier message that still carried that file: a read of it, or the write that last produced
it. That pair is the content the role had in hand when it edited the file. A window "drops" the edge
when that source step is outside the window at the write's call.

| recording | write events, all paths | of which project | of which scratch | read/write->write edges | largest gap |
|---|---|---|---|---|---|
| round4-iter-1 | 6 | 6 | 0 | 6 | src/game.rs read@3 -> write@8, 5 steps |
| round4-iter-2 | 23 | 11 | 12 | 11 | src/game.rs read@5 -> write@33, 28 steps |
| round4-iter-3 | 19 | 9 | 10 | 9 | src/game.rs read@71 -> write@75, 4 steps |
| livecost1-iter-1 | 1 | 0 | 1 | 0 | - |

**[CORRECTED 2026-10-06: the second column was headed `successful project writes`, but the detector
counts every write event and only filters by path for the edges. 23 is 11 project + 12
`.hoh/scratch/**`; 19 is 9 + 10; 1 is 0 + 1; only iter-1 (6) is all-project. The edge counts and the
gaps are unaffected and were reproduced independently.]**

**The decisive case (measured).** In round4-iter-2, call 5 runs `type src\game.rs` and the recorded
observation is the whole **14,902-byte** file. Calls 6-32 contain **no other read of `src/game.rs`** —
only an `echo HOH_WRITE_FILE src/game.rs` probe at call 13 and the bevy-dev.md skill text at call 32.
Call 33 is a full `HOH_WRITE_FILE src/game.rs` whose recorded content is that same file evolved (same
header, same constants, `COIN_XS` widened to two coins). That is a **28-step** gap between reading the
file and rewriting it, and the passing window keeps **at most 4 steps**. The same shape is smaller
elsewhere: iter-1 read `src/game.rs` at call 3 and wrote it at call 8 (5 steps), iter-3 read it at
call 71 and its script rewrote it at call 75 (4 steps). Preserving every recorded edge in iter-2 would
need N >= 28, and N = 24 already projects to **4,546,783** tokens (3.0x the criterion) — the band and the
dependencies do not overlap at any window size.

Dropped edges at the passing edge (**projected** consequence of the **measured** edges):

| policy | recording | dropped edges | the edges |
|---|---|---|---|
| `N2` | round4-iter-1 | 3 | src/game.rs read@3->8 (5); src/contract.rs read@3->7 (4); src/game.rs write@14->18 (4) |
| `N2` | round4-iter-2 | 5 | src/game.rs read@5->33 (28); src/game.rs write@55->65 (10); src/game.rs write@37->42 (5); src/game.rs write@67->72 (5) |
| `N2` | round4-iter-3 | 4 | src/game.rs read@71->75 (4); src/game.rs write@87->91 (4); src/game.rs read@3->6 (3); src/game.rs write@91->94 (3) |
| `N4` | round4-iter-1 | 1 | src/game.rs read@3->8 (5) |
| `N4` | round4-iter-2 | 4 | src/game.rs read@5->33 (28); src/game.rs write@55->65 (10); src/game.rs write@37->42 (5); src/game.rs write@67->72 (5) |
| `N4` | round4-iter-3 | 0 | none |
| `B13543_exclusive_corrected` | round4-iter-1 | 4 | src/game.rs read@3->8 (5); src/contract.rs read@3->7 (4); src/game.rs write@14->18 (4); src/game.rs write@13->14 (1) |
| `B13543_exclusive_corrected` | round4-iter-2 | 11 | src/game.rs read@5->33 (28); src/game.rs write@55->65 (10); src/game.rs write@37->42 (5); src/game.rs write@67->72 (5); src/game.rs read@51->55 (4); src/game.rs write@33->35 (2); src/game.rs write@42->44 (2); src/game.rs write@44->46 (2); src/game.rs write@65->67 (2); src/game.rs write@35->36 (1); src/game.rs write@36->37 (1) |
| `B13543_exclusive_corrected` | round4-iter-3 | 2 | src/game.rs read@3->6 (3); src/game.rs write@6->8 (2) |
| `B8443_inclusive_corrected` | round4-iter-1 | 2 | src/game.rs read@3->8 (5); src/contract.rs read@3->7 (4) |
| `B8443_inclusive_corrected` | round4-iter-2 | 2 | src/game.rs read@5->33 (28); src/game.rs write@55->65 (10) |
| `B8443_inclusive_corrected` | round4-iter-3 | 1 | src/game.rs read@3->6 (3) |

**[CORRECTED 2026-10-06: the `B16384` / `B32768` rows that stood here (iter-2 claimed 9 and 6
dropped edges) were computed with the over-counting accumulator, so they were not the policy they
named. They are kept as labelled history in the machine block. At the corrected passing edges the
picture is *worse* than the file claimed, never better: at `B = 13,543` exclusive iter-2 drops 11 of
11 edges and iter-1 drops 4 of 6.]**

The edges that survive at N = 4 are the tight ones (iter-3's 1-step script edits). What is lost is the
older working set: the file as it was before the incremental edits began.

## 5. Verdict, and confidence

**A bounded-history window is projected to pass the criterion. No passing window is projected to pass
without discarding information the role demonstrably used.**

Confidence: **high** on the discard finding, because both sides are the same measurement made the same
way — the projection says which steps the band keeps, and the recordings say how far back the content
the role edited actually was (28 steps against a 4-step maximum). **Medium** on the projection itself,
because it holds the recorded call sequence fixed: a role that no longer sees a file it is about to edit
will plausibly re-read it (the live call ran 172 shell commands, 166 distinct, most of them reads of its
own files), which raises call count and cost in a way this replay cannot price. So the projection is an
optimistic number for any policy that discards content, and the discard finding is the one that decides
the question.

This is a **clean negative result for the bounded-history family, not for the criterion**: the criterion
is reachable by context narrowing — this spike projects it, and the repository already measured the
system-prompt-and-task-only policy at 0.60x live — but reachable only by a window so small that it is
the same trade under a different name.

## 6. What I could not establish

* No live call was made, so the projection is not confirmed against a real windowed prompt. The projection holds the recorded call sequence fixed and changes only the size of each prompt; a role that no longer sees what it dropped would plausibly issue re-reads and take more calls, which the projection cannot show.
* The round-4 recordings are unfolded and the livecost1 recording is folded (the fold shipped after round 4). There is no recording of a run that used a bounded window instead of the fold, or of one that used both. The live rows are therefore 'a window applied on top of an already-folded history', and its content analysis is impossible: its payloads are notes (live call 6's write is `superseded tool call folded: fb568db0754e (9005 byte(s))`).
* The dependency measurement covers explicit file reads and successful writes it can see (directive writes, shell write primitives, and scripts the role wrote and then ran). A read that arrived inside a command's output without naming the path (a build error quoting source, a diff, a `findstr` context) is not counted; the analysis is therefore a lower bound on the content that was used later, not an upper bound.
* Whether a windowed role would re-read each file just in time (cheap per call, but it moves the call count and can hit the 150-step limit) is a behavioural question the recorded data can only suggest, not answer: the live call ran 172 shell commands, 166 distinct, most of them reads of the role's own files.
* The pass/fail edge is a fitness against a fixed 1,500,000-token criterion; the completion tokens are held at their recorded values because no history policy changes what the model answers.

## 7. The single most important thing for the next decision-maker

**Recency is not a proxy for what the role still needs, and the recorded gaps say so directly: the
window that passes must keep at most 4 steps while the developer read `src/game.rs` at call 5 and
rewrote it at call 33 with no other read in between.** The next lever should therefore be one that keeps
the working set — the files currently in play — rather than the last N steps, or one that reduces the
call count; and any such change has to be measured on a live call, because the only reason the
projection looks attractive is that it assumes a windowed role behaves like the recorded one.

## 8. Gate (measured)

`cargo test --offline`, in this spike's own build directory `F:/spike-hw-target`:

* **exit code 0**; **800 passed / 0 failed / 6 ignored / 806 listed**, 60 `test result:` lines,
  **0** `warning:` lines;
* `cargo test --offline -- --list` exit 0 with **806** names;
  `cargo test --offline -- --list --ignored` exit 0 with **6**;
* `cargo fmt --all --check` exit 0 emitting **0 bytes**.

Identical to the stated start tree (800 / 0 / 6 / 806). **One honest exception**: the *first* run of the
same command returned exit **101** — 440 passed / 1 failed / 0 ignored / 441 listed, because cargo stops
at the first failing target — on
`adapter::bevy::brp::tests::a_slow_reply_that_exceeds_the_timeout_is_a_timeout`
(`expected a timeout, got Transport { ... }`). That test passed in isolation immediately after, and the
full gate then returned the exit-0 numbers above. It is a timing flake of that test under load; both runs
are reported rather than only the clean one. `git status --porcelain` was empty before the gate and
before this report was added — this spike changed nothing measurable and committed nothing.


## 9. Correction (independent re-measurement, 2026-10-06)

`SPIKE-COST-LEVERS.md` re-measured the byte-window policies with corrected logic and the values this
file published are refuted. Nothing about the spike's *conclusion* changes: the corrected byte band
is smaller than the one claimed, so it discards **more** of the content the role used, not less.

**What was wrong.** The byte window counted a step's bytes as the whole slice from that step to the
current call and added that cumulative figure to a counter that had already been inflated by the
previous slice, so the loop reached the budget early and kept fewer steps than the policy names. Every
byte row was therefore optimistic. A faithful implementation gives:

| reading of "until B is reached" | max B passing all four | binding recording | at the edge | first failing B |
|---|---|---|---|---|
| exclusive: largest whole-step suffix with byte total <= B | **13,543** | livecost1-iter-1 | 1,499,796 | 13,544 -> 1,500,020 |
| inclusive: keep adding whole steps until the running total reaches B | **8,443** | round4-iter-2 | 1,499,039 | 8,444 -> 1,500,171 |
| exclusive, pessimistic ratio 0.323468 on every recording | **13,543** | livecost1-iter-1 | 1,499,796 | 13,544 -> 1,500,020 |
| inclusive, pessimistic ratio 0.323468 on every recording | **2,782** | round4-iter-2 | 1,499,244 | 2,783 -> 1,509,795 |

The refuted values were **49,152** (primary) and **32,768** (sensitivity). The two readings are not a
1.6x rounding difference: because the recorded steps are large, the exclusive reading can keep *no*
step above the budget while the inclusive reading keeps at least one whole step, so they differ in
which content survives as well as in cost.

**What is unaffected.** The step-window table and its boundary reproduce: N = 4 passes all four
(round4-iter-1 539,101 / iter-2 1,474,826 / iter-3 752,075 / live 1,077,207 with the ratio rounded to
0.256686 as the acceptance used, or 539,102 / 1,474,827 / 752,076 / 1,077,207 at full precision) and
N = 5 fails on iter-2 alone (1,631,524 / 1,631,526 depending on the rounding grain). The
token-per-byte calibration, the reconstructed corpus totals and the decisive 28-step
`src/game.rs` read->write gap all reproduce.

**The label defect.** `successful_project_write_events` is **not** project-only. The detector counts
every write event and only filters by path when it builds the edges. Re-run with a project/scratch
split, the counts are 6 / 23 / 19 / 1 all-path, of which **6 / 11 / 9 / 0** are project writes and
**0 / 12 / 10 / 1** are `.hoh/scratch/**` writes. Only iter-1 is all-project.

**The consequence for this report's verdict.** The verdict stands and is strengthened: the corrected
byte band (13.5 KiB exclusive, 8.4 KiB inclusive) is 3.6x-5.8x smaller than the one this file claimed,
so a passing byte window drops *more* of the recorded read->write content. At the corrected
`B = 13,543` exclusive edge, round4-iter-2 loses 11 of its 11 recorded edges and round4-iter-1 loses 4
of 6. The next decision should read `SPIKE-COST-LEVERS.md`, which measures the four levers this spike
left out: per-message size bounds, prompt caching, a working set instead of recency, and the
per-invocation call count.
