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
   "projection": {
    "round4-iter-1": {
     "total_prompt": 358006,
     "total_with_recorded_completion": 439638,
     "mean_prompt_per_call": 5188,
     "max_prompt_per_call": 8326,
     "passes_1_5m": true
    },
    "round4-iter-2": {
     "total_prompt": 723805,
     "total_with_recorded_completion": 1049758,
     "mean_prompt_per_call": 5790,
     "max_prompt_per_call": 15125,
     "passes_1_5m": true
    },
    "round4-iter-3": {
     "total_prompt": 534585,
     "total_with_recorded_completion": 620706,
     "mean_prompt_per_call": 5241,
     "max_prompt_per_call": 16063,
     "passes_1_5m": true
    },
    "livecost1-iter-1": {
     "total_prompt": 929220,
     "total_with_recorded_completion": 1042497,
     "mean_prompt_per_call": 6195,
     "max_prompt_per_call": 8656,
     "passes_1_5m": true
    }
   }
  },
  {
   "policy": "keep_last_16384_wire_bytes",
   "kind": "bytes",
   "param": 16384,
   "projection": {
    "round4-iter-1": {
     "total_prompt": 394075,
     "total_with_recorded_completion": 475707,
     "mean_prompt_per_call": 5711,
     "max_prompt_per_call": 8326,
     "passes_1_5m": true
    },
    "round4-iter-2": {
     "total_prompt": 764015,
     "total_with_recorded_completion": 1089968,
     "mean_prompt_per_call": 6112,
     "max_prompt_per_call": 15125,
     "passes_1_5m": true
    },
    "round4-iter-3": {
     "total_prompt": 577750,
     "total_with_recorded_completion": 663871,
     "mean_prompt_per_call": 5664,
     "max_prompt_per_call": 16063,
     "passes_1_5m": true
    },
    "livecost1-iter-1": {
     "total_prompt": 997903,
     "total_with_recorded_completion": 1111180,
     "mean_prompt_per_call": 6653,
     "max_prompt_per_call": 8656,
     "passes_1_5m": true
    }
   }
  },
  {
   "policy": "keep_last_32768_wire_bytes",
   "kind": "bytes",
   "param": 32768,
   "projection": {
    "round4-iter-1": {
     "total_prompt": 450434,
     "total_with_recorded_completion": 532066,
     "mean_prompt_per_call": 6528,
     "max_prompt_per_call": 8846,
     "passes_1_5m": true
    },
    "round4-iter-2": {
     "total_prompt": 865640,
     "total_with_recorded_completion": 1191593,
     "mean_prompt_per_call": 6925,
     "max_prompt_per_call": 15125,
     "passes_1_5m": true
    },
    "round4-iter-3": {
     "total_prompt": 642874,
     "total_with_recorded_completion": 728995,
     "mean_prompt_per_call": 6303,
     "max_prompt_per_call": 16063,
     "passes_1_5m": true
    },
    "livecost1-iter-1": {
     "total_prompt": 1101270,
     "total_with_recorded_completion": 1214547,
     "mean_prompt_per_call": 7342,
     "max_prompt_per_call": 12026,
     "passes_1_5m": true
    }
   }
  },
  {
   "policy": "keep_last_49152_wire_bytes",
   "kind": "bytes",
   "param": 49152,
   "projection": {
    "round4-iter-1": {
     "total_prompt": 500706,
     "total_with_recorded_completion": 582338,
     "mean_prompt_per_call": 7257,
     "max_prompt_per_call": 11948,
     "passes_1_5m": true
    },
    "round4-iter-2": {
     "total_prompt": 1117668,
     "total_with_recorded_completion": 1443621,
     "mean_prompt_per_call": 8941,
     "max_prompt_per_call": 15777,
     "passes_1_5m": true
    },
    "round4-iter-3": {
     "total_prompt": 697718,
     "total_with_recorded_completion": 783839,
     "mean_prompt_per_call": 6840,
     "max_prompt_per_call": 16172,
     "passes_1_5m": true
    },
    "livecost1-iter-1": {
     "total_prompt": 1170516,
     "total_with_recorded_completion": 1283793,
     "mean_prompt_per_call": 7803,
     "max_prompt_per_call": 12026,
     "passes_1_5m": true
    }
   }
  },
  {
   "policy": "keep_last_65536_wire_bytes",
   "kind": "bytes",
   "param": 65536,
   "projection": {
    "round4-iter-1": {
     "total_prompt": 556999,
     "total_with_recorded_completion": 638631,
     "mean_prompt_per_call": 8072,
     "max_prompt_per_call": 12661,
     "passes_1_5m": true
    },
    "round4-iter-2": {
     "total_prompt": 1219816,
     "total_with_recorded_completion": 1545769,
     "mean_prompt_per_call": 9759,
     "max_prompt_per_call": 16023,
     "passes_1_5m": false
    },
    "round4-iter-3": {
     "total_prompt": 759810,
     "total_with_recorded_completion": 845931,
     "mean_prompt_per_call": 7449,
     "max_prompt_per_call": 16823,
     "passes_1_5m": true
    },
    "livecost1-iter-1": {
     "total_prompt": 1237466,
     "total_with_recorded_completion": 1350743,
     "mean_prompt_per_call": 8250,
     "max_prompt_per_call": 14959,
     "passes_1_5m": true
    }
   }
  },
  {
   "policy": "keep_last_131072_wire_bytes",
   "kind": "bytes",
   "param": 131072,
   "projection": {
    "round4-iter-1": {
     "total_prompt": 657921,
     "total_with_recorded_completion": 739553,
     "mean_prompt_per_call": 9535,
     "max_prompt_per_call": 14630,
     "passes_1_5m": true
    },
    "round4-iter-2": {
     "total_prompt": 1526774,
     "total_with_recorded_completion": 1852727,
     "mean_prompt_per_call": 12214,
     "max_prompt_per_call": 20217,
     "passes_1_5m": false
    },
    "round4-iter-3": {
     "total_prompt": 960221,
     "total_with_recorded_completion": 1046342,
     "mean_prompt_per_call": 9414,
     "max_prompt_per_call": 21928,
     "passes_1_5m": true
    },
    "livecost1-iter-1": {
     "total_prompt": 1417195,
     "total_with_recorded_completion": 1530472,
     "mean_prompt_per_call": 9448,
     "max_prompt_per_call": 16725,
     "passes_1_5m": false
    }
   }
  },
  {
   "policy": "keep_last_262144_wire_bytes",
   "kind": "bytes",
   "param": 262144,
   "projection": {
    "round4-iter-1": {
     "total_prompt": 901093,
     "total_with_recorded_completion": 982725,
     "mean_prompt_per_call": 13059,
     "max_prompt_per_call": 19847,
     "passes_1_5m": true
    },
    "round4-iter-2": {
     "total_prompt": 2106295,
     "total_with_recorded_completion": 2432248,
     "mean_prompt_per_call": 16850,
     "max_prompt_per_call": 25420,
     "passes_1_5m": false
    },
    "round4-iter-3": {
     "total_prompt": 1252495,
     "total_with_recorded_completion": 1338616,
     "mean_prompt_per_call": 12279,
     "max_prompt_per_call": 26449,
     "passes_1_5m": true
    },
    "livecost1-iter-1": {
     "total_prompt": 1657477,
     "total_with_recorded_completion": 1770754,
     "mean_prompt_per_call": 11050,
     "max_prompt_per_call": 17846,
     "passes_1_5m": false
    }
   }
  },
  {
   "policy": "keep_last_524288_wire_bytes",
   "kind": "bytes",
   "param": 524288,
   "projection": {
    "round4-iter-1": {
     "total_prompt": 1245096,
     "total_with_recorded_completion": 1326728,
     "mean_prompt_per_call": 18045,
     "max_prompt_per_call": 24029,
     "passes_1_5m": true
    },
    "round4-iter-2": {
     "total_prompt": 2807304,
     "total_with_recorded_completion": 3133257,
     "mean_prompt_per_call": 22458,
     "max_prompt_per_call": 34495,
     "passes_1_5m": false
    },
    "round4-iter-3": {
     "total_prompt": 1814476,
     "total_with_recorded_completion": 1900597,
     "mean_prompt_per_call": 17789,
     "max_prompt_per_call": 38791,
     "passes_1_5m": false
    },
    "livecost1-iter-1": {
     "total_prompt": 1970406,
     "total_with_recorded_completion": 2083683,
     "mean_prompt_per_call": 13136,
     "max_prompt_per_call": 19416,
     "passes_1_5m": false
    }
   }
  }
 ],
 "passing_band": {
  "primary_calibration": {
   "max_steps_passing_all_four": 4,
   "max_bytes_passing_all_four": 49152,
   "binding_recording_steps": "round4-iter-2",
   "note": "see final.json for the full grid; the band edges are the largest values where every recording passes"
  },
  "sensitivity_ratio_0.323468": {
   "max_steps_passing_all_four": 2,
   "max_bytes_passing_all_four": 32768
  },
  "criterion": "total_tokens (prompt + completion) per Developer role call < 1,500,000",
  "completion_tokens_are_recorded_and_held_fixed": true
 },
 "dependency_edges_successful_writes_only": {
  "round4-iter-1": {
   "successful_project_write_events": 6,
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
   "successful_project_write_events": 23,
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
   "successful_project_write_events": 19,
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
   "successful_project_write_events": 1,
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
   "B16384": {
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
     },
     {
      "file": "src/game.rs",
      "from": 33,
      "from_kind": "write",
      "write": 35,
      "gap_steps": 2
     },
     {
      "file": "src/game.rs",
      "from": 42,
      "from_kind": "write",
      "write": 44,
      "gap_steps": 2
     },
     {
      "file": "src/game.rs",
      "from": 44,
      "from_kind": "write",
      "write": 46,
      "gap_steps": 2
     },
     {
      "file": "src/game.rs",
      "from": 65,
      "from_kind": "write",
      "write": 67,
      "gap_steps": 2
     }
    ],
    "round4-iter-3": [
     {
      "file": "src/game.rs",
      "from": 3,
      "from_kind": "read",
      "write": 6,
      "gap_steps": 3
     },
     {
      "file": "src/game.rs",
      "from": 6,
      "from_kind": "write",
      "write": 8,
      "gap_steps": 2
     }
    ]
   },
   "B32768": {
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
     },
     {
      "file": "src/game.rs",
      "from": 65,
      "from_kind": "write",
      "write": 67,
      "gap_steps": 2
     }
    ],
    "round4-iter-3": [
     {
      "file": "src/game.rs",
      "from": 3,
      "from_kind": "read",
      "write": 6,
      "gap_steps": 3
     },
     {
      "file": "src/game.rs",
      "from": 6,
      "from_kind": "write",
      "write": 8,
      "gap_steps": 2
     }
    ]
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
   "B32768": {
    "round4-iter-1": [
     "src/game.rs read@3 -> write@8 (gap 5)",
     "src/contract.rs read@3 -> write@7 (gap 4)"
    ],
    "round4-iter-2": [
     "the gap-28 read@5 -> write@33 edge and five more"
    ],
    "round4-iter-3": [
     "src/game.rs read@3 -> write@6 (gap 3)",
     "src/game.rs write@6 -> write@8 (gap 2)"
    ]
   }
  }
 },
 "verdict": {
  "any_bounded_history_policy_projected_to_pass": true,
  "any_bounded_history_policy_projected_to_pass_without_discarding_used_content": false,
  "confidence": "high on the discard finding (the recorded gaps are >= the passing window by construction of the same measurement); medium on the projection (it holds the recorded call sequence fixed and assumes a dropped message is the only change)",
  "single_most_important_thing": "The passing band and the recorded read->edit dependency distance do not overlap: to come under 1.5M the window must keep at most 4 steps (2 under the measured folded token density), while the recorded developer read src/game.rs whole at iter-2 call 5 and rewrote it at call 33 with no other read in between (28 steps), and still had content-relevant reads 5-10 steps before the writes at iter-1 and iter-3. A recency window that passes is exactly a window that discards information the role used."
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
| `8192 B` | 439,638 | 1,049,758 | 620,706 | 1,042,497 | pass |
| `16384 B` | 475,707 | 1,089,968 | 663,871 | 1,111,180 | pass |
| `32768 B` | 532,066 | 1,191,593 | 728,995 | 1,214,547 | pass |
| `49152 B` | 582,338 | 1,443,621 | 783,839 | 1,283,793 | pass |
| `65536 B` | 638,631 | 1,545,769 FAIL | 845,931 | 1,350,743 | FAIL |
| `131072 B` | 739,553 | 1,852,727 FAIL | 1,046,342 | 1,530,472 FAIL | FAIL |
| `262144 B` | 982,725 | 2,432,248 FAIL | 1,338,616 | 1,770,754 FAIL | FAIL |
| `524288 B` | 1,326,728 | 3,133,257 FAIL | 1,900,597 FAIL | 2,083,683 FAIL | FAIL |

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
| `8192 B` | 5,188 / 8,326 | 5,790 / 15,125 | 5,241 / 16,063 | 6,195 / 8,656 |
| `16384 B` | 5,711 / 8,326 | 6,112 / 15,125 | 5,664 / 16,063 | 6,653 / 8,656 |
| `32768 B` | 6,528 / 8,846 | 6,925 / 15,125 | 6,303 / 16,063 | 7,342 / 12,026 |
| `49152 B` | 7,257 / 11,948 | 8,941 / 15,777 | 6,840 / 16,172 | 7,803 / 12,026 |
| `65536 B` | 8,072 / 12,661 | 9,759 / 16,023 | 7,449 / 16,823 | 8,250 / 14,959 |
| `131072 B` | 9,535 / 14,630 | 12,214 / 20,217 | 9,414 / 21,928 | 9,448 / 16,725 |
| `262144 B` | 13,059 / 19,847 | 16,850 / 25,420 | 12,279 / 26,449 | 11,050 / 17,846 |
| `524288 B` | 18,045 / 24,029 | 22,458 / 34,495 | 17,789 / 38,791 | 13,136 / 19,416 |

**The passing band (projected).** Under the primary calibration, the largest window that keeps *all
four* recorded calls under the criterion is **N = 4 steps** or **B = 49,152 wire bytes**; the binding
recording is **round4-iter-2** (N=4 -> 1,474,827 total; N=5 -> 1,631,526). Under the pessimistic
0.323468-everywhere sensitivity it shrinks to **N = 2** or **B = 32,768**, again bound by iter-2
(N=2 -> 1,378,000; N=3 -> 1,576,000). N = 1 and B = 8 KiB pass everywhere with room to spare (iter-2
projects to 1,003,504 at N=1). For reference, iter-2's recorded total is **13,091,431** and the live
call's is **3,651,120**, so a passing window is a ~90 percent cut of the prompt spend.

## 4. What each policy would actually cut (edges measured, consequence projected)

For every **successful** write to a project file (`src/**`, `tests/**`, `Cargo.toml`) — directive writes,
shell writes (`Set-Content`, `WriteAllText`, ...) and scripts the role wrote and then ran — I located the
most recent earlier message that still carried that file: a read of it, or the write that last produced
it. That pair is the content the role had in hand when it edited the file. A window "drops" the edge
when that source step is outside the window at the write's call.

| recording | successful project writes | read/write->write edges | largest gap |
|---|---|---|---|
| round4-iter-1 | 6 | 6 | src/game.rs read@3 -> write@8, 5 steps |
| round4-iter-2 | 23 | 11 | src/game.rs read@5 -> write@33, 28 steps |
| round4-iter-3 | 19 | 9 | src/game.rs read@71 -> write@75, 4 steps |
| livecost1-iter-1 | 1 | 0 | - |

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
| `B16384` | round4-iter-1 | 3 | src/game.rs read@3->8 (5); src/contract.rs read@3->7 (4); src/game.rs write@14->18 (4) |
| `B16384` | round4-iter-2 | 9 | src/game.rs read@5->33 (28); src/game.rs write@55->65 (10); src/game.rs write@37->42 (5); src/game.rs write@67->72 (5) |
| `B16384` | round4-iter-3 | 2 | src/game.rs read@3->6 (3); src/game.rs write@6->8 (2) |
| `B32768` | round4-iter-1 | 2 | src/game.rs read@3->8 (5); src/contract.rs read@3->7 (4) |
| `B32768` | round4-iter-2 | 6 | src/game.rs read@5->33 (28); src/game.rs write@55->65 (10); src/game.rs write@37->42 (5); src/game.rs write@67->72 (5) |
| `B32768` | round4-iter-3 | 2 | src/game.rs read@3->6 (3); src/game.rs write@6->8 (2) |

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
