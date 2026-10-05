```json
{
 "schema": "hof-rs / bevy round-7 write-accounting batch",
 "produced_at": "2026-10-05",
 "branch": "bevy-core",
 "head_at_start": "b9546f5",
 "head_subject": "docs(acceptance): record the independent acceptance that refutes the zero-lost-writes claim and confirms the cost criterion cannot be met",
 "working_tree_at_start": "CLEAN: the one uncommitted line the round-6 acceptance found (defect A-4 / criterion C22) was committed by b9546f5, which also committed that acceptance document",
 "working_tree_at_end": "COMMITTED: the delegating agent committed this change set as 1aeec7b on bevy-core (`git status --porcelain` empty at that commit). This batch did not run git add/commit/push itself, by instruction; the commit is the delegating agent's. Any later commit of a correction to this file is likewise the delegating agent's, and DECISIONS.md D304 records that D303's own 'not committed' sentence was true when written and is stale as a statement about the tree - the same pattern A-6 found in D302.",
 "verdict": "the cost criterion is NOT met on this tree (2.434x the target on the one live Developer call); the measuring blindness that produced two false statements in the round-6 report is fixed, and the corrected account is now a repository capability",
 "cost_criterion": {
  "text": "total_tokens below 1,500,000 per Developer call (.spec/bevy/ROUND-2-REPORT.md:43)",
  "live_measurement": {
   "calls": 150,
   "prompt_tokens": 3537843,
   "completion_tokens": 113277,
   "total_tokens": 3651120,
   "ratio_to_target": 2.434,
   "passes": false
  },
  "shipped_tree": "no shipped lever changes this: the repository carries no behavioural change from the round-6 batch and this batch adds none",
  "only_policy_measured_to_pass": "keep nothing but the system prompt and the task: live projection 786,685 prompt + 113,277 completion = 899,962 (0.600x) - REFUSED by the project, because it removes what the role just did and this role re-read its own files constantly",
  "statement": "The criterion is not met on the shipped tree. The withdrawn step-budget family cannot meet it without cutting recorded work (K <= 37 to pass; K >= 43 for round-4 iteration 3's directive window, and K >= 52 globally, or K >= 51 under the strict convention, to cut no recorded PROJECT write - restated for defect D-1 of .spec/bevy/ACCEPTANCE-ACCOUNTING.md; the corrected accounting makes the cut side worse than the round-6 report said). The only policy measured to pass is the context-narrowing one this project refuses. That is the honest state of the project and D303 records it as the decision."
 },
 "gate": {
  "command": "cargo test --offline",
  "exit_code": 0,
  "exit_code_source": "the literal $? of that command, written to F:/hof-acct-work/final.exit by the runner",
  "passed": 782,
  "failed": 0,
  "ignored": 6,
  "listed": 788,
  "measured": 0,
  "test_result_lines": 59,
  "listed_equals_passed_plus_ignored": true,
  "start_tree_measured_by_the_round_6_acceptance": {
   "passed": 766,
   "failed": 0,
   "ignored": 6,
   "listed": 772
  },
  "delta_to_start_tree": {
   "passed": 16,
   "listed": 16,
   "removed": 0,
   "added": 16
  },
  "tests_added": {
   "src/harness/write_audit.rs unit tests": 10,
   "tests/write_accounting.rs": 6
  },
  "tests_removed": 0,
  "list_command": "cargo test --offline -- --list",
  "list_exit_code": 0,
  "list_count": 788,
  "list_ignored_exit_code": 0,
  "list_ignored_count": 6,
  "list_ignored_names": [
   "a_client_rebuilt_for_the_new_process_answers_on_its_first_call",
   "the_adapter_rebinds_its_observing_client_at_every_launch",
   "the_five_behaviours_are_observed_on_a_real_bevy_game_process",
   "the_pinned_endpoint_answers_discover_with_the_23_methods_of_bevy_0191",
   "the_real_machine_smoke_proves_the_contract_on_a_live_bevy_game",
   "the_round_three_transport_failure_reproduces_through_one_client"
  ],
  "fmt_command": "cargo fmt --all --check",
  "fmt_exit_code": 0,
  "fmt_stdout_bytes": 0,
  "fmt_stderr_bytes": 0,
  "warning_lines_stdout_and_stderr": 0,
  "build_dir": "D:\\hof-wacct-target (this batch's own; the repository's own target/ was not used)",
  "no_second_test_process": "tasklist showed no cargo/rustc/hoh before and after THIS batch's own gate run",
  "confirmation_run": {
   "counts": "identical: 782 passed / 0 failed / 6 ignored / 788 listed, exit 0, 788 listed names, fmt exit 0 with 0 bytes",
   "note": "it was run again after the machine-readable block was regenerated; only .md files had changed since the first run, so the code bytes are the same. Its own AFTER process check saw a DIFFERENT agent's cargo/rustc build running on this machine, so that check is not evidence - the first run's clean before/after check is."
  },
  "round_and_developer_call": "none was run: the criterion is answered from the recorded trajectory, not from a new call"
 },
 "evidence_location": {
  "why_this_is_here": "every figure in this report and in the cost reports rests on the recorded trajectories; they are NOT in the repository",
  "tracked": "no - `runs/` is in .gitignore, so no clone, CI run or other machine contains this evidence",
  "runs_root": "F:\\moonbit-hof-rs\\runs",
  "runs_total_files": 11229,
  "runs_total_bytes": 12775066006,
  "runs_total_gib": 11.898,
  "trajectories_used_here": {
   "runs/livecost1/iter-1/traj/developer.attempt1.json": 1041144,
   "runs/round4/iter-1/traj/developer.attempt1.json": 602673,
   "runs/round4/iter-2/traj/developer.attempt1.json": 1786110,
   "runs/round4/iter-3/traj/developer.attempt1.json": 736346
  },
  "trajectories_total_bytes": 4166273,
  "what_is_lost_if_this_disk_is_lost": "every measurement in LIVE-COST-REPORT.md, COST-REPORT.md, FIX-REPORT.md, ROUND-4-REPORT-COMPLETE.md, this report and D303 becomes un-reproducible: the provider's own per-call usage, the recorded action text and the recorded return codes all live only there. tests/write_accounting.rs fails with the missing path named rather than passing silently.",
  "note_on_the_repository_criteria": "the project's own criteria include keeping the evidence and being reproducible; a gitignored 11.9 GiB evidence tree on one volume meets neither, and that is recorded here rather than left implicit"
 },
 "corrected_write_accounting": {
  "tool": {
   "module": "src/harness/write_audit.rs",
   "tests": "tests/write_accounting.rs",
   "re_run": "cargo test --offline --test write_accounting (and `cargo test --offline --lib harness::write_audit`)",
   "decides": "for each recorded model call, whether it wrote a file inside the project",
   "signals": [
    "HOH_WRITE_FILE directives, classified by the REAL parser (src/harness/directive.rs), so a directive the harness refused is never counted",
    "shell commands, from the recorded command text: the write verb and its destination operand, with literal $var='...' and name='...' assignments resolved",
    "scripts a command runs, when the recording carries the script's own text - the write is attributed to the call that RAN the script"
   ],
   "scope_rule": "delegated to the guard's own ArtifactKind::ProjectFile (a path under .hoh/, .git/ or target/ is not progress)",
   "outcome_rule": "the recording's own <returncode> decides: 0 = the command ran and reported success; non-zero = Failed, so it did not write; absent = NotRecorded",
   "refuses": "an unbound destination (reported, never guessed); a malformed directive (reported as undecided, and NOT scanned as if it had run); byte-level identity of the written content (never claimed)"
  },
  "trajectories": {
   "live-iter-1": {
    "recorded_calls": 150,
    "total_tokens": 3651120,
    "directive_write_calls": [
     6,
     14,
     17,
     19,
     43
    ],
    "project_write_calls": [
     6,
     14,
     17,
     19,
     43,
     44,
     95
    ],
    "failed_project_writes": [
     [
      139,
      "src\\game.rs",
      1
     ]
    ],
    "undecided": [],
    "last_project_write": 95,
    "longest_project_write_free_window": [
     95,
     151,
     55
    ],
    "calls_after_the_last_project_write": 55,
    "tokens_in_those_calls": 1788003,
    "share_of_the_call_tokens": 0.4897,
    "what_the_round_6_report_said": {
     "last_project_write": 44,
     "write_free_calls_after_it": 106,
     "share": 0.627
    }
   },
   "round4-iter-1": {
    "recorded_calls": 69,
    "total_tokens": 2626195,
    "directive_write_calls": [
     7,
     8,
     9,
     13,
     14,
     18
    ],
    "project_write_calls": [
     7,
     8,
     9,
     13,
     14,
     18
    ],
    "failed_project_writes": [],
    "undecided": [],
    "longest_project_write_free_window": [
     18,
     70,
     51
    ],
    "both_signals_agree": true
   },
   "round4-iter-2": {
    "recorded_calls": 125,
    "total_tokens": 13091431,
    "directive_write_calls": [
     27,
     29,
     33,
     35,
     36,
     37,
     40,
     42,
     44,
     46,
     55,
     63,
     64,
     65,
     67,
     69,
     71,
     72,
     97,
     99,
     106,
     109,
     116
    ],
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
     72,
     98,
     100,
     107,
     110
    ],
    "script_driven_project_writes": [
     98,
     100,
     107,
     110
    ],
    "failed_project_writes": [
     [
      68,
      "src/game.rs",
      1
     ]
    ],
    "undecided": [],
    "note": "call 68 is a `python - <<\"PY\"` heredoc that cmd.exe answered with `<< was unexpected at this time`; calls 98/100/107/110 run .hoh/scratch/patch{2..5}.py, whose recorded text opens src/game.rs for writing"
   },
   "round4-iter-3": {
    "recorded_calls": 102,
    "total_tokens": 5223211,
    "directive_write_calls": [
     6,
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
    "project_write_calls": [
     6,
     8,
     75,
     81,
     85,
     87,
     91,
     94,
     98
    ],
    "script_driven_project_writes": [
     75,
     81,
     85,
     87,
     91,
     94,
     98
    ],
    "failed_project_writes": [
     [
      22,
      "src\\game.rs",
      1
     ],
     [
      69,
      "src\\game.rs",
      1
     ]
    ],
    "undecided": [
     [
      72,
      "a directive the harness refused as malformed: HOH_WRITE_FILE .hoh/scratch/tweak.ps1"
     ]
    ],
    "longest_project_write_free_window": [
     8,
     75,
     66
    ],
    "visible_write_free_window": [
     6,
     50,
     43
    ],
    "what_the_acceptance_said": {
     "edits_proving_the_43_call_window_is_not_idle": [
      8,
      22
     ],
     "correction": "call 8 succeeded (the file grew to 42,502 bytes); call 22's script threw (`json pattern missing`) before its [IO.File]::WriteAllText, and call 69 did too. The real further edits are the script-driven ones at 75-98."
    }
   }
  },
  "the_ten_cut_write_directives": [
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
  "the_seven_cut_project_edits": [
   75,
   81,
   85,
   87,
   91,
   94,
   98
  ],
  "the_two_shell_writes_in_the_live_call_that_the_acceptance_named": [
   {
    "call": 95,
    "command_excerpt": "powershell -NoProfile -Command \"$p='src\\game.rs'; $c=Get-Content -Raw -Encoding UTF8 $p; $c=$c -replace 'pub const COIN_A_X: f32 = 70\\.0;','pub const COIN_A_X: f32 = 50.0;' ... Set-Content -NoNewline -Encoding UTF8 $p $c\" && findstr ... src\\game.rs",
    "recorded_returncode": 0,
    "recorded_output": "pub const MOVE_SPEED: f32 = 300.0; / pub const COIN_A_X: f32 = 50.0; / pub const COIN_B_X: f32 = 100.0; / pub const GOAL_X: f32 = 150.0;",
    "disposition": "a real project write, and the LAST one in the live call; the round-6 detector could not see it because it counts directives only"
   },
   {
    "call": 139,
    "command_excerpt": "powershell -NoProfile -Command \"$p='src\\game.rs'; $c=Get-Content -Raw -Encoding UTF8 $p; $c=$c.Replace('const GOAL_HALF_WIDTH: f32 = 25.0;','const GOAL_HALF_WIDTH: f32 = 10.0;'); ... Set-Content -NoNewline -Encoding UTF8 $p $c\"; findstr /n \"GOAL_HALF_WIDTH WALK_LIMIT_X clamp(-GROUND\" src\\game.rs",
    "recorded_returncode": 1,
    "recorded_output": "Missing closing ')' in expression. (ParserError, MissingEndParenthesisInExpression)",
    "disposition": "a shell write COMMAND naming src\\game.rs, but PowerShell never parsed it, so it changed nothing; the acceptance listed it as a further project-file write and explicitly said it could not decide whether the bytes changed - the recording decides it"
   }
  ],
  "the_two_shell_writes_in_round4_iter_3_that_the_acceptance_named": [
   {
    "call": 8,
    "recorded_returncode": 0,
    "recorded_output": "42502",
    "disposition": "succeeded: [IO.File]::WriteAllText($p,$t) ran and the file length was printed as 42,502 bytes"
   },
   {
    "call": 22,
    "recorded_returncode": 1,
    "recorded_output": "json pattern missing",
    "disposition": "FAILED: the script threw before its write, so src/game.rs was not changed"
   }
  ],
  "the_withdrawn_step_budget_replayed_at_k_32": {
   "implemented_somewhere": false,
   "replay_function": "write_audit::replay_directive_step_budget (measurement only; no configuration key, no guard state, no production call site)",
   "live-iter-1": {
    "ends_at_call": 76,
    "cumulative_tokens": 1357530,
    "ratio_to_target": 0.905,
    "directive_writes_after": [],
    "project_writes_after": [
     95
    ]
   },
   "round4-iter-1": {
    "ends_at_call": 51,
    "cumulative_tokens": 1790635,
    "directive_writes_after": [],
    "project_writes_after": []
   },
   "round4-iter-2": {
    "ends_at_call": null,
    "directive_writes_after": [],
    "project_writes_after": []
   },
   "round4-iter-3": {
    "ends_at_call": 39,
    "cumulative_tokens": 1604038,
    "directive_writes_after": [
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
    "project_writes_after": [
     75,
     81,
     85,
     87,
     91,
     94,
     98
    ]
   }
  },
  "the_two_bands": {
   "to_meet_the_criterion": "K <= 37 (K = 37 ends the live call at call 81 for 1,484,934 tokens; call 82 is 1,511,382)",
   "to_cut_no_directive_write": "K >= 43 (at K = 42 and below it cuts real src/game.rs edits in round-4 iteration 3; at K = 43 the rule does not fire in that iteration at all)",
   "to_cut_no_recorded_project_write": "K >= 52, or K >= 51 under this replay's own strict `> abort` convention: the live call's last directive write is call 43 and its last PROJECT write is call 95, so the rule fires at call 44 + K, and every K <= 51 refuses a recorded project write (K = 50 fires at 94 and cuts the write at 95; K = 51 fires at 95 and refuses the write itself)",
   "gap": "37 < 43 < 52; the bands do not overlap, and the corrected accounting makes the losing side worse than the round-6 report said",
   "restated_for_defect_d_1": "This block originally read `to_cut_no_recorded_work: K >= 43`, which is round-4 iteration 3's DIRECTIVE window only. Defect D-1 of .spec/bevy/ACCEPTANCE-ACCOUNTING.md found it and returned pass anyway, because the error is in the conservative direction - it understates how bad the lever is. The bound is restated here and in .spec/bevy/LIVE-COST-REPORT.md; it is pinned by tests/write_accounting.rs::the_global_safe_floor_is_fifty_two_and_not_forty_three and ::the_two_bands_do_not_overlap.",
   "recomputed": true
  },
  "the_false_constant_derivation": {
   "claimed": "32 = 31 + 1, from round-4 iter-3 'write at call 18, its next at 50'",
   "where_the_claim_is": "D:/hof-live-work/write-free-budget-WITHDRAWN.patch - its config/hoh.yaml and src/config.rs doc comments (outside the repository, not modified by this batch)",
   "measured": "iter-3 has no write at call 18; its visible-write-free window is 43 calls (6 -> 50); 32 is ELEVEN calls below the only legitimate window in the evidence",
   "margin": -11,
   "consequence": "re-applying the preserved patch without correcting this comment reproduces defect A-1 exactly (D303 records this)"
  }
 },
 "defects": [
  {
   "id": "A-1-zero-lost-writes-false",
   "severity": "high",
   "disposition": "FIXED",
   "what": "the round-6 replay reported `directive_writes_after_the_end: []` and `zero_recorded_directive_writes_lost: true`, and the section-4 table said 'none', while the report's own prose said the rule cuts genuine repairs",
   "root_cause": "the value was gathered inside the replay loop, which stops at the abort, so it could only ever be empty",
   "measured_now": {
    "round4_iter_3": {
     "aborted_at_call": 39,
     "directive_writes_after_the_end": [
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
     "project_writes_after_the_end": [
      75,
      81,
      85,
      87,
      91,
      94,
      98
     ],
     "zero_lost": false
    }
   },
   "reproduction": "cargo test --offline --test write_accounting the_withdrawn_budget_at_k_32_cuts_ten_directives_and_seven_project_edits",
   "corrections": [
    ".spec/bevy/LIVE-COST-REPORT.md JSON (replay_through_the_shipped_guard, the caveat block), its section-2 and section-4 tables and prose",
    "DECISIONS.md D303"
   ],
   "pinned_by": "plant P3-the-degenerate-after-lists"
  },
  {
   "id": "A-2-constant-derivation-wrong",
   "severity": "high",
   "disposition": "FIXED IN THE RECORD; the patch on disk still carries the false comment",
   "what": "the constant 32 was derived as '31 + 1' from a 31-call legitimate window that does not exist",
   "measured_now": {
    "round4_iter_3_visible_write_free_window": 43,
    "window_bounds": [
     6,
     50
    ],
    "write_at_call_18": false,
    "margin_vs_the_constant": -11
   },
   "cannot_be_fixed_here": "the false derivation lives in D:/hof-live-work/write-free-budget-WITHDRAWN.patch's config/hoh.yaml and src/config.rs doc comments, outside the repository and outside this batch's remit; D303 records that re-applying the artefact without correcting it reproduces A-1",
   "corrections": [
    ".spec/bevy/LIVE-COST-REPORT.md JSON (the_two_bands_do_not_overlap)",
    "DECISIONS.md D303"
   ]
  },
  {
   "id": "A-3-live-write-profile-wrong",
   "severity": "high",
   "disposition": "FIXED (and the acceptance's own reading was refined)",
   "what": "the report and D302 said the live call's last project-file change was call 44 and calls 45-150 (106 calls, 62.7 % of the tokens) changed nothing",
   "root_cause": "D:/hof-live-work/project_writes.py counts HOH_WRITE_FILE directives only, so every project file changed by a shell command is invisible to it",
   "measured_now": {
    "project_write_calls": [
     6,
     14,
     17,
     19,
     43,
     44,
     95
    ],
    "last_project_write": 95,
    "failed_attempt_at_139": true,
    "calls_after_the_last_project_write": 55,
    "share_of_tokens": 0.4897,
    "the_old_62_7_percent_is_reproducible": false
   },
   "refinement_of_the_acceptance": "the acceptance named calls 95 and 139 as the further project writes and said it could not decide whether they changed bytes. The recording does decide: call 95's own findstr output shows the new constants (it changed src/game.rs and is the last change), and call 139 returned 1 with `Missing closing ')' in expression` (it changed nothing).",
   "reproduction": "cargo test --offline --test write_accounting the_live_calls_write_profile_is_the_corrected_one",
   "corrections": [
    ".spec/bevy/LIVE-COST-REPORT.md JSON (where_the_calls_went), its section 2 table and section 6",
    "DECISIONS.md D303"
   ]
  },
  {
   "id": "A-4-dirty-tree",
   "severity": "medium",
   "disposition": "ALREADY CLOSED BEFORE THIS BATCH",
   "what": "the accepted tree was not the committed tree: one added line in .spec/bevy/LIVE-COST-REPORT.md",
   "measured_now": "commit b9546f5 committed that line together with the acceptance document; `git status --porcelain` was EMPTY at this batch's start",
   "note": "this batch leaves its own edits uncommitted because it was instructed not to commit; committing them is the delegating agent's action (see working_tree_at_end)"
  },
  {
   "id": "A-5-lever-provenance",
   "severity": "medium",
   "disposition": "FIXED",
   "what": "the published lever pairs were attributed to this batch's own cost_measure.py and the acceptance's composition.py 'agreeing exactly', and the published crossing was given as a linear interpolation",
   "measured_now": {
    "published_pairs_reproduce": "F:/hof-acc6-work/composition.py exactly",
    "published_pairs_reproduce_cost_measure_py": false,
    "cost_measure_py_iter_2_first_60": [
     1152836,
     1386920
    ],
    "published_iter_2_first_60": [
     1152836,
     1478789
    ],
    "convention": "[projected prompt over the first N calls, that prompt + the iteration's WHOLE recorded completion]",
    "crossing_published_convention": {
     "first_n_at_or_above": 61,
     "below_at": [
      60,
      1478789
     ],
     "above_at": [
      61,
      1502016
     ],
     "interpolated": 60.9
    },
    "crossing_published_convention_iter_3": {
     "first_n_at_or_above": 92,
     "below_at": [
      91,
      1498609
     ],
     "above_at": [
      92,
      1520424
     ],
     "interpolated": 91.1
    },
    "crossing_cost_measure_convention_iter_2": {
     "first_n_at_or_above": 65,
     "below_at": [
      64,
      1477946
     ],
     "above_at": [
      65,
      1504428
     ],
     "interpolated": 64.8
    }
   },
   "corrections": [
    ".spec/bevy/LIVE-COST-REPORT.md JSON (corrected_inaccuracies.F-4)",
    ".spec/bevy/FIX-REPORT.md (the lever block's `what`/`verdict`/`counted_basis` and the section-5 prose)"
   ],
   "not_interpolated": "the published crossing is the curve's own crossing at call 61, a recorded call, not an interpolation between the 60 and 70 samples"
  },
  {
   "id": "A-6-stale-commit-accounting",
   "severity": "low",
   "disposition": "FIXED BY APPEND (DECISIONS.md is append-only)",
   "what": "D302 ends its discipline line claiming the batch was not committed, while D302 itself ships inside a commit; and 81c9a71's subject, 'bound it with a write-free step budget', asserts the opposite of its body (that commit contains no source change and the budget was withdrawn)",
   "measured_now": {
    "D302_committed_in": "81c9a71",
    "b9546f5_commit": "commits the acceptance document and the LIVE-COST-REPORT.md line",
    "tree_at_this_batch_start": "clean"
   },
   "correction": "DECISIONS.md D303 section (c) restates the truth and names what D302 said; D302 is not rewritten"
  },
  {
   "id": "A-7-not-found-by-the-acceptance-a-false-negation-about-the-shipped-tree",
   "severity": "low",
   "disposition": "RECORDED, and the conclusion re-grounded on code",
   "what": "the acceptance's criterion C3 proved 'the budget is not in the shipped tree' with `grep -rn \"max_write_free_steps|WriteFreeBudgetExceeded|write_free\"` over the whole repository returning no match. That was already inaccurate at 81c9a71: .spec/bevy/LIVE-COST-REPORT.md lines 129-130 contain both strings, in the JSON that discusses the withdrawn patch.",
   "conclusion_is_still_true": "measured on code facts rather than grep: src/config.rs has no such field, config/hoh.yaml has no such key, src/harness/guard.rs has no such state and no such status, and no production call site exists. The only implementation of the rule in the tree is write_audit::replay_directive_step_budget, an offline measurement function nothing calls.",
   "why_this_belongs_here": "C3's method would have produced a false PASS on a repository that had shipped the lever and described it in a report; the next acceptance should grep the code, not the tree"
  }
 ],
 "plants": [
  {
   "id": "P1-a-switch-treated-as-a-value-flag",
   "file": "src/harness/write_audit.rs",
   "defect": "`-NoNewline` is treated as a flag that eats its value, so `Set-Content -NoNewline src\\game.rs` names no destination and the live call's shell writes vanish",
   "test": "cargo test --offline --test write_accounting the_live_calls_write_profile_is_the_corrected_one",
   "green_before_exit": 0,
   "red_exit": 101,
   "red_ran": true,
   "red_named_test": true,
   "green_after_exit": 0,
   "restore_byte_exact": true,
   "sha256_before": "17d1dc4abe5f63ba9da679954bcc7a35bb216dcff195da52256d44e10afe8179",
   "mtime_plant": 1791200000.0,
   "mtime_restore": 1791400000.0,
   "result": "ok"
  },
  {
   "id": "P2-every-path-is-project-progress",
   "file": "src/harness/write_audit.rs",
   "defect": "the scope rule stops delegating to the guard, so a copy *into* `.hoh/` counts as a project write",
   "test": "cargo test --offline --test write_accounting the_command_shapes_the_recordings_contain_are_classified_as_the_recording_says",
   "green_before_exit": 0,
   "red_exit": 101,
   "red_ran": true,
   "red_named_test": true,
   "green_after_exit": 0,
   "restore_byte_exact": true,
   "sha256_before": "17d1dc4abe5f63ba9da679954bcc7a35bb216dcff195da52256d44e10afe8179",
   "mtime_plant": 1791200000.0,
   "mtime_restore": 1791400000.0,
   "result": "ok"
  },
  {
   "id": "P3-the-degenerate-after-lists",
   "file": "src/harness/write_audit.rs",
   "defect": "the replay reports its after-lists as empty, which is the exact degeneracy the acceptance found in the round-6 JSON",
   "test": "cargo test --offline --test write_accounting the_withdrawn_budget_at_k_32_cuts_ten_directives_and_seven_project_edits",
   "green_before_exit": 0,
   "red_exit": 101,
   "red_ran": true,
   "red_named_test": true,
   "green_after_exit": 0,
   "restore_byte_exact": true,
   "sha256_before": "17d1dc4abe5f63ba9da679954bcc7a35bb216dcff195da52256d44e10afe8179",
   "mtime_plant": 1791200000.0,
   "mtime_restore": 1791400000.0,
   "result": "ok"
  },
  {
   "id": "P4-the-return-code-is-ignored",
   "file": "src/harness/write_audit.rs",
   "defect": "the recorded <returncode> is ignored, so a command PowerShell never parsed counts as a write",
   "test": "cargo test --offline --test write_accounting the_recorded_iteration_three_write_timeline_is_the_corrected_one",
   "green_before_exit": 0,
   "red_exit": 101,
   "red_ran": true,
   "red_named_test": true,
   "green_after_exit": 0,
   "restore_byte_exact": true,
   "sha256_before": "17d1dc4abe5f63ba9da679954bcc7a35bb216dcff195da52256d44e10afe8179",
   "mtime_plant": 1791200000.0,
   "mtime_restore": 1791400000.0,
   "result": "ok"
  }
 ],
 "withdrawn_experiment": {
  "stays_withdrawn": true,
  "re_introduced": false,
  "evidence": "no configuration key, no guard field, no status, no production call site; the implementation is still preserved outside the repository at D:/hof-live-work/write-free-budget-WITHDRAWN.patch and was NOT modified by this batch",
  "the_evaluation_still_in_force": "the bands do not overlap: reaching the cost criterion needs K <= 37, round-4 iteration 3's directive window starts at K >= 43, and cutting no recorded PROJECT write anywhere needs K >= 52 (K >= 51 under the strict convention) - defect D-1 of .spec/bevy/ACCEPTANCE-ACCOUNTING.md, restated",
  "recomputed_after_the_correction": "the numbers are unchanged (37 and 43) and the losing side is stronger: at K = 32 the live call loses its call-95 project write as well as the ten directives, and round-4 iter-3 loses seven real src/game.rs edits at 75-98",
  "what_the_recomputation_did_not_change_and_what_it_did": "K <= 37 is unchanged, and round-4 iteration 3's binding bound stays 43, because the rule can only see directives. What the corrected accounting DOES move is the GLOBAL floor: the live call's last project write is call 95, so every K <= 51 refuses it and the global floor is K >= 52. The round-6 wording said the recomputation changed nothing; that was only true of the directive window"
 },
 "decision_entry": {
  "file": "DECISIONS.md",
  "id": "D303",
  "appended_bytes": 10382,
  "superseded_in_part_by": "DECISIONS.md D304 (appended when the delegating agent committed this change set as 1aeec7b): D303's discipline line said the batch was not committed and not pushed, which was true when written and is stale as a statement about the tree - the D302/A-6 pattern, recorded rather than rewritten",
  "append_only_verified": "DECISIONS.md at HEAD is a byte prefix of the current file; D302's own text is intact",
  "states": [
   "the cost criterion is NOT met on the shipped tree (2.434x the target on the one live Developer call)",
   "the step-budget family cannot meet it without cutting recorded work (K <= 37 to pass; K >= 43 for round-4 iteration 3's directive window and K >= 52 globally to cut no recorded project write)",
   "the only policy measured to pass is the context-narrowing one the project refuses",
   "the accounting defect that hid this is now fixed, in the tree, with four plants pinning it",
   "the evidence lives under the gitignored runs/** and is on this disk only"
  ]
 },
 "changed_files": {
  "added": [
   "src/harness/write_audit.rs (the durable accounting: directive/shell/script write detection, the guard's own scope rule, the recorded return code as the effect verdict, and a measurement-only replay of the withdrawn rule)",
   "tests/write_accounting.rs (the accounting measured on the four recorded Developer calls, plus the two-band property and the command-shape classification)",
   ".spec/bevy/WRITE-ACCOUNTING-REPORT.md (this file)"
  ],
  "modified": [
   "src/harness/mod.rs (one line: `pub mod write_audit;`)",
   ".spec/bevy/LIVE-COST-REPORT.md (only where the acceptance found it factually wrong: the JSON write profile, the replay's after-lists, the constant's derivation, the lever provenance, sections 2, 4 and 6, and a header note)",
   ".spec/bevy/FIX-REPORT.md (only where the acceptance found it factually wrong: the lever block's provenance, the crossing's derivation, and the section-5 prose)",
   "DECISIONS.md (D303 appended only)"
  ],
  "not_modified": "REQUIREMENTS.md, DESIGN-OVERVIEW.md, DESIGN-DETAIL.md, PRD.md, the spike reports, the round-1/2/3/4 reports, ACCEPTANCE-COST.md, ACCEPTANCE-FIX.md, ACCEPTANCE-LIVE-COST.md, ACCEPTANCE-ROUNDS.md, the BATCH reports, COST-REPORT.md, config/hoh.yaml and every other source file",
  "new_dependencies": "none: the regex crate could not be added offline (`cargo metadata --offline` after adding it reported `attempting to make an HTTP request, but --offline was specified`), so the parsers are hand-written scanners over chars",
  "source_code_behaviour_change": "none: no production call site uses the new module"
 },
 "unverified": [
  "Whether an iteration-2-shaped Developer call is under the criterion now: only one live call has ever been measured (this batch ran none).",
  "The absolute tokens-per-wire-byte constants and the fold's own projections: this batch did not re-derive them and takes the acceptance's reproduction as given.",
  "Whether a tree-fingerprint signal would reach the target: no offline replay may execute the recorded shell commands, so it cannot be measured without another live round.",
  "The intermediate lever pairs at N = 40/90/100 for the crossing computation: the crossings are computed call by call from the same fold and ratio the published pairs use, but the fold implementation itself is the acceptance's Python (F:/hof-acc6-work/measure2.py), not the repository's Rust compact_history.",
  "The tool's blind spots, stated rather than hidden: a write verb it does not know (Set-ItemProperty, a git command that rewrites a tracked file, a hand-rolled writer) is not seen; a destination computed at run time is reported undecided only when a KNOWN verb has an unbound operand; and it decides from the command text, so it can never claim byte-level identity of the written content. No such case occurs in the four recorded calls."
 ],
 "what_the_tool_cannot_decide": [
  "an unbound destination: reported through NamedWrite::target = None and counted as undecided, never guessed (there is no such case in the recordings)",
  "a command whose recorded result is absent: Outcome::NotRecorded, which counts toward 'changed' only for a directive the harness itself executed",
  "whether a successful Set-Content that replaced nothing actually changed bytes: the file IS written, but content equality is not claimed",
  "anything a role does outside the recorded action text: no action text means no signal, and the accounting says so instead of assuming"
 ]
}
```

# WRITE-ACCOUNTING-REPORT — the corrected write accounting, the six defects it closes, and the cost criterion that is still not met

Independent, offline work on `bevy-core` at **`b9546f5`** (clean tree). No engine, no game, no network,
no model call, no round and no Developer call was run. Every figure comes from the recorded
trajectories under `runs/**`, from code in this tree, or from this batch's own gate run.

The machine-readable block is the first thing in this file. It is serialiser output (Python
`json.dumps` over a dict, `indent=1`), written into this file by `F:/hof-acct-work/write_report.py` and
then **parsed back out of the written file** — the parse is the last thing the generator does, and it
fails the run if it does not round-trip.

## 0. Verdict in one paragraph

The criterion this project has never met still is not met: **3,651,120 total tokens against a 1,500,000
target on the one live Developer call, 2.434x**. Nothing in this batch changes that, and nothing in the
shipped tree changes it. What this batch does change is the *measuring instrument* every cost conclusion
rests on. The round-6 batch reported that the live call's last project-file change was call 44 and that
calls 45–150 changed nothing; both numbers came from a detector that counts `HOH_WRITE_FILE` directives
only, so a project file changed by a PowerShell command did not exist for it. The corrected account puts
the last change at **call 95**, with **55** calls — **48.97 %** of the call's tokens — after it, and it
puts the withdrawn budget's losses at **ten write directives and seven real `src/game.rs` edits** rather
than the empty list the round-6 JSON published. The account is no longer a script outside the
repository: it is `src/harness/write_audit.rs`, exercised by `tests/write_accounting.rs`, and four
controlled plants show it goes red when the accounting is broken. The answer to "does the cost criterion
pass" is unchanged and is now recorded as a decision: **no**, this family of levers cannot make it pass
without cutting recorded work, and the only policy measured to pass is the context-narrowing one the
project refuses.

## 1. The accounting, and why it lives in the tree

The root cause of defect A-3 is not a wrong sentence; it is that **the instrument was blind and the
instrument was not in the repository**. `D:/hof-live-work/project_writes.py` reads
`tool_calls[*].function.arguments` — which the round-5 fold replaces with a note plus a truncated
preview, so large directives parse as malformed there — and it counts write directives only. Anything a
role does through a shell command is invisible.

`src/harness/write_audit.rs` replaces it with three signals read from the recording:

1. **Directives**, classified by the *real* parser (`crate::harness::directive::parse_directive`), so a
   directive the harness refused is never counted as a write. Round-4 iteration 3's call 72 is exactly
   that case: the role put the `powershell -File .hoh\scratch\tweak.ps1` line *inside* the directive
   body, the harness answered with its help text, and neither the script write nor the command that
   would have run it happened.
2. **Shell commands**, decided from the recorded command text: the write verb and its **destination
   operand**, with literal variable assignments resolved (`$p='src\game.rs'` for PowerShell,
   `p = 'src/game.rs'` for Python). Counting every path a command mentions is not enough — `copy /Y
   src\game.rs .hoh\scratch\game_a.rs` mentions a project file as its **source**, and the live call's
   calls 65 and 103 are exactly that.
3. **Scripts a command runs**, when the recording carries the script's own text. This is not a nicety:
   seven of round-4 iteration 3's project edits and all four of iteration 2's late ones are made by
   running a `.hoh/scratch/*.ps1` or `*.py` whose content is recorded, and the write never appears on
   the command line that ran it.

The scope rule is **delegated to the guard's own** `ArtifactKind::ProjectFile`, so the accounting and
the enforcement cannot drift apart, and the effect verdict is the recording's own `<returncode>`: a
command that failed did not change a file. Where the recording does not settle something, the tool says
so — a destination the text never binds is `undecided`, and byte-level identity of the written content
is never claimed. Section 7 lists what it cannot decide.

## 2. The corrected per-call account

Reproduced from the four recorded Developer calls
(`cargo test --offline --test write_accounting`, and `--lib harness::write_audit`):

| recorded call | calls | guard-visible write directives | **project writes** | failed project-write attempts | last project write |
|---|---|---|---|---|---|
| live-iter-1 | 150 | 6, 14, 17, 19, 43 | **6, 14, 17, 19, 43, 44, 95** | 139 (`src\game.rs`, rc 1) | **95** |
| round4-iter-1 | 69 | 7, 8, 9, 13, 14, 18 | 7, 8, 9, 13, 14, 18 | none | 18 |
| round4-iter-2 | 125 | 27, 29, 33, 35, 36, 37, 40, 42, 44, 46, 55, 63, 64, 65, 67, 69, 71, 72, 97, 99, 106, 109, 116 | 33, 35, 36, 37, 42, 44, 46, 55, 65, 67, 72, **98, 100, 107, 110** | 68 (`src/game.rs`, rc 1) | 110 |
| round4-iter-3 | 102 | 6, 50, 70, 73, 74, 80, 84, 86, 90, 93, 97 | 6, 8, **75, 81, 85, 87, 91, 94, 98** | 22 and 69 (`src\game.rs`, rc 1) | 98 |

Bold entries are writes the directive-only detector cannot see at all. Round-4 iter-3 also carries one
**undecided** action, call 72, and the tool reports it rather than guessing.

### 2.1 The two shell writes the acceptance named in the live call

Both are shell writes naming `src\game.rs`, and the recording decides what each did:

* **call 95** — `powershell -NoProfile -Command "$p='src\game.rs'; ... Set-Content -NoNewline -Encoding
  UTF8 $p $c" && findstr ...`. Recorded `<returncode>0</returncode>`, and the `findstr` output shows the
  **new** values (`MOVE_SPEED 300.0`, `COIN_A_X 50.0`, `COIN_B_X 100.0`, `GOAL_X 150.0`). This is the
  live call's **last** project write.
* **call 139** — the same shape, rewriting `GOAL_HALF_WIDTH` and adding `WALK_LIMIT_X`. Recorded
  `<returncode>1</returncode>`, output `Missing closing ')' in expression.` — PowerShell never parsed
  it, so **it changed nothing**. The acceptance listed it as a further project-file write and explicitly
  said it could not decide whether the bytes changed; the recording decides it.

The same refinement applies to the acceptance's round-4 iter-3 counterexample: **call 8** ran
`[IO.File]::ReadAllText` + `[IO.File]::WriteAllText` and returned `42502` (the file grew), so it is a
real edit; **call 22** threw `json pattern missing` before its write, and so did call 69. The window is
still not idle — call 8 proves it — but the further damage is not there; it is at calls 75–98.

## 3. Defects, one at a time

| defect | disposition | where it is fixed | pinned by |
|---|---|---|---|
| **A-1** the replay's "zero lost writes" | **fixed** — the after-lists were gathered inside the loop that stops at the abort, so they could only ever be empty | `LIVE-COST-REPORT.md` JSON + §4, D303 | plant P3 |
| **A-2** the constant's derivation | **fixed in the record** — no write at call 18 exists; the window is 43 and the margin is **−11**, not +1. The false comment itself is in the withdrawn patch *outside* the repository and is untouched; D303 records that re-applying it reproduces A-1 | `LIVE-COST-REPORT.md` JSON, D303 | the band test (K = 42 fires, K = 43 does not) |
| **A-3** the live call's write profile | **fixed, and the acceptance's reading refined** — last change 95, not 44; 55 calls / 48.97 %, not 106 / 62.7 %; call 95 landed, call 139 failed | `LIVE-COST-REPORT.md` JSON + §2 + §6, D303 | plants P1, P4 |
| **A-4** the dirty tree | **already closed by `b9546f5`** — the tree was clean at this batch's start | — | `git status --porcelain` empty |
| **A-5** the lever provenance | **fixed** — the pairs reproduce `composition.py` exactly and `cost_measure.py` not at all; the convention is stated; the published crossing is the curve's own at call **61** (60 → 1,478,789, 61 → 1,502,016), not an interpolation | `LIVE-COST-REPORT.md` JSON, `FIX-REPORT.md` | the crossing recomputation |
| **A-6** the stale commit accounting | **fixed by append** — D303 (c) states that D302 is committed in `81c9a71`, that `b9546f5` closed A-4, and that `81c9a71`'s subject contradicts its body; D302 is not rewritten | D303 | the byte-prefix check on `DECISIONS.md` |

### 3.1 One more thing the acceptance got wrong (A-7, recorded here)

Criterion **C3** proved "the write-free step budget is not in the shipped tree" with a `grep` over the
whole repository for `max_write_free_steps|WriteFreeBudgetExceeded|write_free`, reporting no match.
That was **already inaccurate at `81c9a71`**: `.spec/bevy/LIVE-COST-REPORT.md` lines 129–130 contain
both of the first two strings, inside the JSON that discusses the withdrawn patch. The conclusion is
nevertheless true, and this batch re-grounds it on **code facts** rather than grep: no such field in
`src/config.rs`, no such key in `config/hoh.yaml`, no such state or status in
`src/harness/guard.rs`, no production call site. The method matters: a grep-based proof would return
PASS on a repository that had shipped the lever and documented it. The next acceptance should grep the
code.

## 4. The withdrawn experiment stays withdrawn, recomputed

Nothing in this batch implements, configures or calls the step budget: no key, no guard state, no
status, no production call site, and `D:/hof-live-work/write-free-budget-WITHDRAWN.patch` was not
modified. The one place the rule appears in the tree is `write_audit::replay_directive_step_budget`, an
offline measurement function nothing calls — it exists so the withdrawn lever's own safety claim can be
re-run against the corrected accounting.

Recomputed at K = 32 (the constant the patch shipped):

| recorded call | ends at | cumulative tokens | guard-visible writes cut | **project writes cut** |
|---|---|---|---|---|
| live-iter-1 | call 76 | 1,357,530 | none | **95** |
| round4-iter-1 | call 51 | 1,790,635 | none | none |
| round4-iter-2 | never fires | — | none | none |
| round4-iter-3 | call 39 | 1,604,038 | **50, 70, 73, 74, 80, 84, 86, 90, 93, 97** | **75, 81, 85, 87, 91, 94, 98** |

The cost/cut edges are **unchanged where the rule can see**: reaching the criterion needs **K ≤ 37**
(K = 37 ends the live call at call 81 for 1,484,934, the last cumulative total under 1,500,000; call 82
is 1,511,382), and round-4 iteration 3's binding bound is **K ≥ 43** (at K = 42 and below it cuts real
`src/game.rs` edits; at K = 43 it never fires in round-4 iter-3). What this block got wrong is that
`K ≥ 43` is *that iteration's* bound and not the **global** one: the rule fires in the live call at call
`44 + K`, so every K ≤ 51 refuses the live call's call-95 `src/game.rs` write — the last artifact write
in the recording — and the global floor is **K ≥ 52** (K ≥ 51 under this replay's strict `> abort`
convention). That is defect **D-1** of `.spec/bevy/ACCEPTANCE-ACCOUNTING.md`, restated here. So
**37 < 43 < 52**: the bands still do not overlap, and the corrected accounting makes the losing side
*worse* than the round-6 report said, not better. What the correction changes in the table above is the
*damage*: the "none" column was empty because the instrument could not see a shell write, and the live
call loses a real project write too.

## 5. Gate, plants, files

* **Gate**, in this batch's own build directory `D:\hof-wacct-target`, with free space checked first
  (D: 269 G free, F: 66 G free) and no cargo/rustc/hoh process before or after:
  `cargo test --offline` → **literal exit code 0**, **782 passed / 0 failed / 6 ignored / 788 listed**
  over **59** `test result:` lines; `-- --list` exit 0 with 788 names; `-- --list --ignored` exit 0 with
  the same six real-engine tests; **0** `warning:` lines in stdout and stderr; `cargo fmt --all --check`
  exit **0** emitting **0 bytes**. The start tree measured 766/0/6/772 — **16 tests added, 0 removed**,
  because no existing test's name or body was touched.
* **Plants.** Four controlled plants, each green → red → green, each a single-occurrence literal edit of
  `src/harness/write_audit.rs`, each restored **byte-exactly** (sha256 compared) with both mtimes set
  explicitly (`1791200000.0` for the plant, a newer `1791400000.0` for the restore, so cargo cannot skip
  the rebuild). Every green run exited **0**; every red run exited **101**, really ran (a `test result:`
  line was present) and **named the intended test**:
  * **P1** — `-NoNewline` treated as a flag that eats its value → the live call's shell writes vanish.
  * **P2** — the scope rule stops delegating to the guard → a copy *into* `.hoh/` counts as progress.
  * **P3** — the replay's after-lists become empty again → **A-1's exact degeneracy**.
  * **P4** — the recorded `<returncode>` is ignored → call 139 and calls 22/69 count as changes.

  Record: `F:/hof-acct-work/plants_accounting.json`, red logs `F:/hof-acct-work/PLANT-P*.log`.
  `src/harness/write_audit.rs` was byte-identical (sha256 `17d1dc4a…`) before and after all four.
* **Files.** Added `src/harness/write_audit.rs`, `tests/write_accounting.rs`, this report. Modified
  `src/harness/mod.rs` (one `pub mod` line), `.spec/bevy/LIVE-COST-REPORT.md` and
  `.spec/bevy/FIX-REPORT.md` **only where the acceptance found them factually wrong**, and
  `DECISIONS.md` (**D303 appended only**; `DECISIONS.md` at HEAD is a byte prefix of the current file).
  No new dependency: `regex` cannot be added offline (`cargo metadata --offline` after adding it
  reported `attempting to make an HTTP request, but --offline was specified`), so the parsers are
  hand-written scanners over chars.
* **Committed?** Yes — **by the delegating agent**, as `1aeec7b` on `bevy-core`
  ("fix(accounting): count shell project writes, correct the false claims, and record that the cost
  criterion is unmet"), with a clean `git status --porcelain` at that commit. This batch was instructed
  **not** to commit, stage or push, and did not: no `git add`, no `git commit`, no `git push`, and
  `bevy-core` is still local-only. The tree was **clean** when this batch started (defect A-4 was closed
  by `b9546f5`), so nothing pre-existing was left dirty either. `DECISIONS.md` **D304** records that
  D303's own "not committed" sentence is superseded by this fact — D302's stale counterpart is what
  defect A-6 found, and this batch would not repeat it.

## 6. The evidence lives on one disk, and not in the repository

Every number in this report, in `LIVE-COST-REPORT.md`, in `COST-REPORT.md`, in `FIX-REPORT.md`, in
`ROUND-4-REPORT-COMPLETE.md` and in `D303` is derived from the recorded trajectories under `runs/**`,
and **`runs/` is in `.gitignore`**. No clone, no CI run and no other machine contains them.

* `F:\moonbit-hof-rs\runs` — **11,229 files, 12,775,066,006 bytes = 11.898 GiB**.
* The four Developer trajectories this accounting reads — **4,166,773 bytes**: `livecost1/iter-1`
  (1,041,144), `round4/iter-1` (602,673), `round4/iter-2` (1,786,110), `round4/iter-3` (736,346).

If this disk is lost, the provider's own per-call usage, the recorded action text and the recorded
return codes are gone with it, and every cost conclusion in this repository becomes un-reproducible —
including the ones that say the criterion fails. The project's own criteria include keeping the
evidence and being reproducible; an 11.9 GiB gitignored evidence tree on a single volume meets neither.
This batch did not move the evidence (it is not this batch's to move, and it is not in the repository's
remit), and `tests/write_accounting.rs` fails with the missing path named rather than passing silently.

## 7. What worked, what does not, what I could not verify

**Worked.** The corrected accounting reproduces the acceptance's own findings exactly where they were
right — the ten cut directives `50, 70, 73, 74, 80, 84, 86, 90, 93, 97`; the abort calls and their
totals at K = 32 (live 76 / 1,357,530; iter-1 51 / 1,790,635; iter-2 never; iter-3 39 / 1,604,038); the
43-call window 6 → 50; the live call's last guard-visible write at 43 — and it refines them where the
recording has more to say: call 8 is the real edit and call 22 failed; call 95 is the live call's last
project write and call 139 never parsed. It is a plain Rust module with no new dependency, it reuses the
harness's own directive parser and the guard's own scope rule, and four plants show it breaks when the
accounting is broken. The gate is green and the tree was clean at the start.

**Does not work.** The cost criterion: **3,651,120 total tokens against 1,500,000, 2.434x** on the one
live Developer call, and it was ended by the step budget rather than by finishing. No shipped lever
changes it, the step-budget family cannot reach it without cutting recorded work (K ≤ 37 to pass,
K ≥ 43 for round-4 iteration 3's own directive window, and K ≥ 52 globally to cut no recorded project
write — the bound defect D-1 found missing; the corrected accounting makes the cut side worse), and the
project refuses the one policy measured to pass. **This is the state the project ships in, and it is now
recorded as such.**

**Could not verify.** Whether an iteration-2-shaped call is under the target (one live call has ever
been measured; this batch ran none); the absolute tokens-per-wire-byte constants and the fold's own
projections (this batch did not re-derive them); whether a tree-fingerprint signal reaches the target
(no offline replay may execute the recorded shell commands). And the tool's own limits, stated rather
than hidden: it cannot see a write verb it does not know (`Set-ItemProperty`, a `git` command that
rewrites a tracked file, a hand-rolled writer), it reports an unresolvable destination as undecided
rather than guessing, and it never claims that a successful command changed bytes — only that it wrote.
No such case occurs in the four recorded calls, but the next batch should not read "no project write at
call N" as stronger than it is.

## 8. The single most important thing for the next batch

**Do not compute another cost number from a detector that reads directives.** The two error directions
this batch found are the same defect: the round-6 report could not see a project file changed by a shell
command, so it both overstated how idle the live call was (calls 45–150 "changed nothing") and
understated what the withdrawn budget would destroy (`zero_recorded_directive_writes_lost: true`). Use
`src/harness/write_audit.rs`, or extend it — and when a script is involved, remember that the write is
inside the script, not on the command line. If a future batch tries to make the criterion pass by
ending calls that have stopped writing, it must first answer the question that killed the last attempt:
**what, exactly, does the signal see that the role can see?** For the directive counter the answer is
"less than the role writes"; for a tree fingerprint it is unmeasured and needs one live round.

And the honest headline for whoever reads this next: **the criterion is not met, and on the evidence in
this repository no shipped lever meets it.**
