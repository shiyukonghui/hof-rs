# LIVE-COST-REPORT — the live Developer call, the five corrections, and the call-count reduction that was measured and withdrawn

```json
{
 "schema": "hof-rs / bevy round-6 live cost report",
 "produced_at": "2026-10-05",
 "branch": "bevy-core",
 "head_at_start": "fc25c32",
 "working_tree_at_start": "clean",
 "gate": {
  "command": "cargo test --offline",
  "exit_code": 0,
  "exit_code_source": "literal `$?` written to D:/hof-live-logs/gate.exit by D:/hof-live-work/gate.sh, the one script that ran the whole gate",
  "passed": 766,
  "failed": 0,
  "ignored": 6,
  "listed": 772,
  "listed_equals_passed_plus_ignored": true,
  "test_result_lines": 58,
  "start_tree_measured_here": {"passed": 766, "failed": 0, "ignored": 6, "listed": 772},
  "delta_to_start_tree": {"passed": 0, "listed": 0, "removed": 0},
  "list_command": "cargo test --offline -- --list",
  "list_exit_code": 0,
  "list_count": 772,
  "list_ignored_exit_code": 0,
  "list_ignored_count": 6,
  "list_ignored_names": [
   "the_pinned_endpoint_answers_discover_with_the_23_methods_of_bevy_0191",
   "the_real_machine_smoke_proves_the_contract_on_a_live_bevy_game",
   "the_five_behaviours_are_observed_on_a_real_bevy_game_process",
   "a_client_rebuilt_for_the_new_process_answers_on_its_first_call",
   "the_adapter_rebinds_its_observing_client_at_every_launch",
   "the_round_three_transport_failure_reproduces_through_one_client"
  ],
  "warning_lines_stdout": 0,
  "warning_lines_stderr": 0,
  "fmt_command": "cargo fmt --all --check",
  "fmt_exit_code": 0,
  "fmt_output_bytes": 0,
  "build_dir": "D:\\hof-live-target (this batch's own; the repository's own target/ was not used)",
  "no_second_test_process": "tasklist showed no cargo/rustc/hoh before and after (D:/hof-live-logs/gate.procs-before.txt and gate.procs-after.txt are both empty)",
  "re_run_on_the_final_tree": "the whole gate was run a second time after this report and the D302 append existed, and returned the same literal numbers (exit 0, 766/0/6/772, 58 test-result lines, 0 warnings, fmt exit 0 with 0 bytes, no stray processes)",
  "tests_removed": 0
 },
 "live_developer_call": {
  "what_was_run": "one real Developer call from a project outside the repository, with the current code: `hoh init --adapter bevy --project D:\\hof-live-run\\workspace` then `hoh run --adapter bevy --project D:\\hof-live-run\\workspace --run-id livecost1 --iterations 1 --env-from-secret D:\\hof-live-work\\live.env`, from F:\\moonbit-hof-rs, binary D:\\hof-live-target\\debug\\hoh.exe",
  "headless": true,
  "endpoint": "http://127.0.0.1:15702/ (the game's own port); the second endpoint 15703 was never used",
  "run_exit_code": 0,
  "run_id": "livecost1",
  "iterations_requested": 1,
  "model_calls": 150,
  "prompt_tokens": 3537843,
  "completion_tokens": 113277,
  "total_tokens": 3651120,
  "wall_clock_ms": 1278222,
  "wall_clock_minutes": 21.3,
  "stopped_by": "LimitsExceeded",
  "exit_was_limits": true,
  "step_limit_in_force": 150,
  "artifact_written": true,
  "artifact_valid": true,
  "artifact_gate": {"applicable": true, "launchable": true, "reasons": []},
  "evidence_diff": {"added": ["src/sim_tests.rs"], "modified": ["src/game.rs", "src/main.rs"], "removed": []},
  "first_call_prompt_tokens": 4269,
  "last_call_prompt_tokens": 40404,
  "max_call_prompt_tokens": 40501,
  "mean_prompt_tokens_per_call": 23586,
  "where_the_calls_went": {
   "hoh_write_file_directives": 5,
   "hoh_write_file_calls": [6, 14, 17, 19, 43],
   "project_file_writes_by_directive": [6, 14, 19, 43],
   "excluded_path_writes_by_directive": [17],
   "hoh_read_file_directives": 9,
   "shell_commands": 172,
   "distinct_shell_commands": 166,
   "last_project_file_change_at_call": 44,
   "how_that_change_happened": "a PowerShell `Set-Content` on src/main.rs (adding `mod sim_tests;`), invisible to the guard's directive-write counter",
   "calls_after_it_that_changed_no_project_file": 106,
   "note": "the shape the round-5 tripwire cannot see: 166 distinct commands, so there is no repeated action to count"
  },
  "the_round_it_belongs_to": {
   "planner": {"calls": 17, "prompt": 129823, "completion": 3674, "total": 133497},
   "developer": {"calls": 150, "prompt": 3537843, "completion": 113277, "total": 3651120},
   "tester": {"calls": 124, "prompt": 2781243, "completion": 30312, "total": 2811555},
   "round_total_tokens": 6596172
  },
  "measured_by": "the harness's own record (runs/livecost1/iter-1/result.json) and the provider's own per-call usage inside runs/livecost1/iter-1/traj/developer.attempt1.json (150 usage entries); D:/hof-live-work/live_measure.py and D:/hof-live-logs/live_measure.json"
 },
 "against_the_criterion_and_the_baseline": {
  "criterion": "below 1,500,000 total_tokens per Developer call (.spec/bevy/ROUND-2-REPORT.md:43)",
  "live_total": 3651120,
  "criterion_passes": false,
  "ratio_to_criterion": 2.434,
  "baseline": "296 Developer calls / 20,447,131 prompt / 493,706 completion / 20,940,837 total / 98.6 minutes across the three recorded round-4 iterations",
  "live_call_as_a_share_of_the_baseline": {
   "calls": 0.507,
   "total_tokens": 0.174,
   "note": "it is one call against a three-call baseline, so the share is not a like-for-like comparison; it is stated because the task asks for the comparison"
  },
  "like_for_like_against_the_recorded_iter_1": {
   "recorded_round4_iter_1": {"calls": 69, "prompt": 2544563, "completion": 81632, "total": 2626195, "ended_by": "RepeatedActionError"},
   "live": {"calls": 150, "prompt": 3537843, "completion": 113277, "total": 3651120, "ended_by": "LimitsExceeded"},
   "mean_prompt_per_call_recorded": 36878,
   "mean_prompt_per_call_live": 23586,
   "prompt_per_call_reduction": 0.360
  },
  "the_projection_versus_the_measurement": {
   "recorded_round4_fit_tokens_per_wire_byte_iter_2": 0.255366,
   "live_measured_tokens_per_wire_byte": 0.323468,
   "live_is_higher_by": 0.267,
   "why": "the fold replaces superseded payloads with short JSON notes, whose token density is higher than the prose the round-4 fit was calibrated on. The direction of this error was listed as unmeasured risk in ACCEPTANCE-FIX.md; it is now measured, and the offline projections UNDERSTATE the post-fold cost by about a quarter per wire byte.",
   "fold_effect_on_the_live_call": "the stored trajectory is already folded (the fold lands on the agent's own history, AC-8), so re-applying the fold to it is a no-op and no 'unfolded' counterfactual can be read from it; what is measurable is the per-call mean above"
  }
 },
 "corrected_inaccuracies": {
  "F-1_arithmetic": {"was": "iter-2 projects to 2,681,282 prompt + 325,953 completion = 3,034,063", "now": "3,007,235", "where": ".spec/bevy/COST-REPORT.md"},
  "F-2_system_prompt_size": {"was": "14,783 bytes of content (14,814 of wire)", "now": "14,522 bytes of content / 14,849 bytes of wire, which the live call reproduces exactly (system_content_bytes 14522, system_wire_bytes 14849); 17.7 % of iter-2's compacted wire bytes and 3,791 of the compacted final call's 25,152 projected prompt tokens (15.1 %)", "where": ".spec/bevy/COST-REPORT.md and .spec/bevy/FIX-REPORT.md"},
  "F-3_over_strong_claim": {"was": "the tail-0 figure is 'an arithmetic lower bound on any context-only policy, so no context-only policy can make it pass'", "now": "the tail-0 figure bounds only the fold's own family (every superseded message replaced by a ~200-300 byte note). A policy that keeps nothing but the system prompt and the task projects to 287,657 / 517,368 / 430,085 prompt tokens (369,289 / 843,321 / 516,206 with completion) for the three recorded calls and WOULD pass. What the batch refuses is that TRADE - a role that no longer sees the history it works from - not an impossibility", "where": ".spec/bevy/FIX-REPORT.md cost block, measured_floor, the new f3_correction block, section 5 and the 'does not pass' paragraph; .spec/bevy/COST-REPORT.md; DECISIONS.md D302 (append-only, so D301's own title and section (e) are superseded there rather than edited)"},
  "F-4_call_count_arithmetic": {"was": "iter-2 first_60 [1,153,140, 1,479,093], first_70 [1,384,463, 1,710,416], first_80 [1,640,551, 1,966,504], 'roughly 85 for iter-3'", "now": "re-derived pairs iter-2 first_60 [1,152,836, 1,478,789], first_70 [1,385,772, 1,711,725], first_80 [1,643,606, 1,969,559]; iter-3 first_80 [1,180,267, 1,266,388]; 'roughly 85 for iter-3' WITHDRAWN (its own first_80 is already below the target), crossing about 61 calls for iter-2 and about 91 for iter-3", "reproduced_by": "D:/hof-live-work/cost_measure.py and the acceptance's independent F:/hof-acc6-work/composition.py agree exactly", "where": ".spec/bevy/FIX-REPORT.md"},
  "F-5_stale_not_committed": {"was": "'Nothing was committed, staged or pushed'", "now": "committed as 6290f77 on bevy-core; the sentence was true when written and is stale as a statement about the tree", "where": ".spec/bevy/FIX-REPORT.md (scope field and section 1)"}
 },
 "call_count_reduction": {
  "implemented": true,
  "measured": true,
  "shipped": false,
  "withdrawn": true,
  "why_withdrawn": "its own replay through the shipped guard shows it would cut real artifact work in round-4 iter-3",
  "constant": {"name": "agent.max_write_free_steps", "value_implemented": 32, "zero_means": "off (the round-5 behaviour exactly)"},
  "rule": "once a call has written the artifact it declares, it may make at most N model calls without writing ANY file; the next one is refused with the status WriteFreeBudgetExceeded. A successful write directive restarts the run; a *shell* write cannot be seen by the guard at all.",
  "what_counts_as_a_write": "any successful HOH_WRITE_FILE directive - the artifact, a .hoh scratch note, or a script. Counting any write rather than only the artifact is what makes the rule conservative: the round-4 iterations whose artifact edits go through the shell (iter-2's .hoh/scratch/patch{2..5}.py, iter-3's .hoh/scratch/tweak{1..9}.ps1) always write the script before running it, so their runs restart.",
  "what_resets_it": "any successful write directive; the first write also arms the rule (before that, agent.steps_per_artifact governs)",
  "enforcement_point": "WriteGuardEnvironment::execute, at the step, against the live value; a write action is never refused by the budget it would restart",
  "distribution": "the implementation is preserved outside the repository at D:/hof-live-work/write-free-budget-WITHDRAWN.patch (45,735 bytes; 753 insertions, 6 deletions across src/harness/guard.rs, src/config.rs, src/harness/mini.rs, config/hoh.yaml, tests/context_compaction.rs). The repository was restored byte-exactly from HEAD blobs (`git show HEAD:<path>`, sha256 compared, `git diff --exit-code` clean for each of the five paths); `git checkout --` was not used.",
  "replay_through_the_shipped_guard": {
   "how": "every recorded model call is fed to the real WriteGuardEnvironment (shipped step_limit 150, wrap_up_steps 25, steps_per_artifact 8, max_write_free_steps 32), a FakeShell standing in for the shell so no recorded command executes, the real write path for the directives, and a shared StepCounter incremented once per call exactly as CountingModel does; the token totals are the provider's own recorded per-call usage. It ran as src/harness/guard.rs::tests::the_write_free_budget_replayed_over_the_recorded_developer_calls before the implementation was withdrawn.",
   "live_iter_1": {"recorded_calls": 150, "ends_at_call": 76, "total_tokens_at_the_end": 1357530, "ratio_to_criterion": 0.905, "directive_writes_after_the_end": []},
   "round4_iter_1": {"recorded_calls": 69, "ends_at_call": 51, "recorded_total_tokens_at_the_end": 1790635, "directive_writes_after_the_end": []},
   "round4_iter_2": {"recorded_calls": 125, "ends_at_call": null, "directive_writes_after_the_end": []},
   "round4_iter_3": {"recorded_calls": 102, "ends_at_call": 39, "directive_writes_after_the_end": []},
   "zero_recorded_directive_writes_lost": true
  },
  "the_caveat_that_withdrew_it": {
   "round4_iter_3": "the rule fires at call 39, in the run that starts at its last visible write (call 6) and reaches the next (call 50) - 43 calls. Inside that run the role edited src/game.rs at calls 8 and 22 with `powershell [IO.File]::ReadAllText` + `[IO.File]::WriteAllText`; the guard sees neither. So 'zero lost writes' is true only of the guard's own signal: the rule would have cut genuine repairs.",
   "round4_iter_2_variant": "a stricter variant that counted only artifact writes fires at call 105, before calls 107 and 110 run .hoh/scratch/patch4.py and patch5.py, which edit src/game.rs - the same damage by a different route."
  },
  "why_the_30000_token_window_the_task_expected_does_not_exist": "round-4 iter-3's write-free window is 43 visible-write-free calls (6 -> 50), not 31: the 31 came from counting .hoh scratch writes as artifact progress. The 43 is the binding safety bound.",
  "the_two_bands_do_not_overlap": {
   "to_meet_the_criterion": "K <= 37: the live call's last cumulative total under 1,500,000 is call 81 (1,484,934; call 82 is 1,511,382), and the abort call is last_visible_write + K + 1 = 43 + K + 1, so K <= 81 - 44 = 37",
   "to_cut_no_recorded_work": "K >= 43: round-4 iter-3's 43-call run after its last visible write contains two real src/game.rs edits",
   "gap": "37 < 43; the same rule cannot both meet the criterion and leave every recorded call's artifact work intact",
   "source": "D:/hof-live-work/bands.py, D:/hof-live-logs/bands.txt"
  },
  "the_other_context_policy_that_would_pass": {
   "policy": "keep nothing but the system prompt and the task on every call",
   "live_projection": {"calls": 150, "prompt": 786685, "completion": 113277, "total": 899962, "ratio_to_criterion": 0.600},
   "refused_because": "it removes what the role just did and was told back. The live call re-read its own files constantly (9 HOH_READ_FILE directives and 172 shell commands, most of them type/Get-Content/more/findstr), so removing the history would plausibly raise the call count; and it is a worse version of the prompt-shaving the task forbids."
  },
  "what_the_withdrawal_leaves": "no behavioural change in the repository; the measurement, the two bands and the reason are the deliverable"
 },
 "disk_work": {
  "why": "the volume holding the build cache (F:) was at 100 % twice in the last day and both times a first build died on a disk-space error",
  "state_before": "F: 1.2 T, 5.6 G available, 100 % used",
  "method": "D:/hof-live-work/rmtree_targets.py: a LITERAL list of paths, each verified to be a cargo target directory (`.rustc_info.json` present AND a `debug/` subtree), each printed with its measured size and file count BEFORE removal, removed with `shutil.rmtree` over that verified literal path. No `rm -rf`, no wildcard, no path built from an unexpanded variable, nothing that is not a cargo target directory.",
  "removed": [
   {"path": "F:\\hof-acc-target", "bytes": 9754385523, "files": 11630},
   {"path": "F:\\hof-acc5-target", "bytes": 10114472524, "files": 11855},
   {"path": "F:\\hof-cost-target", "bytes": 10275289714, "files": 11858},
   {"path": "F:\\hof-fix-target", "bytes": 10689479026, "files": 13405},
   {"path": "F:\\hof-r3-target", "bytes": 9486426998, "files": 11424},
   {"path": "F:\\hof-r4-target", "bytes": 10833498167, "files": 14100},
   {"path": "F:\\hof-trust-target", "bytes": 9621161880, "files": 11427}
  ],
  "total_bytes": 70774713832,
  "total_gib": 65.91,
  "state_after": "F: 67 G available (95 % used)",
  "log": "D:/hof-live-logs/rmtree.txt",
  "everything_after_that": "built and ran on D: (D:\\hof-live-target for the harness, D:\\hof-live-run for the round), so the live round did not depend on the reclaimed space"
 },
 "plants": [
  {"id": "P1-the-fold-is-short-circuited-off", "file": "src/harness/compact.rs", "defect": "compact_history returns without folding (the round-4 behaviour)", "test": "cargo test --offline --test context_compaction", "red_named": "the_context_fold_shrinks_every_recorded_round_four_developer_call", "green_before_exit": 0, "red_exit": 101, "green_after_exit": 0, "restore_byte_exact": true, "sha256_before": "49b524e75eb2b256430c17dc64d015264011815abcc294ac6144a76ad89ed8c4", "mtime_plant": 1791200000.0, "mtime_restore": 1791400000.0, "result": "ok"},
  {"id": "P2-example-list-is-the-previous-engine", "file": "src/tools/index.rs", "defect": "the production example list names a tool no Bevy round delivers", "test": "cargo test --offline --lib tools::index", "red_named": "the_complete_call_examples_are_the_delivered_bevy_tools", "green_before_exit": 0, "red_exit": 101, "green_after_exit": 0, "restore_byte_exact": true, "sha256_before": "f84f6670318363982c0b81c71956fcdb3ef352227887491732e7600a29d34f12", "mtime_plant": 1791200000.0, "mtime_restore": 1791400000.0, "result": "ok"},
  {"id": "P3-documented-projection-is-the-wrong-number", "file": "src/config.rs", "defect": "src/config.rs documents a projection that is not the measured one", "test": "cargo test --offline --test context_compaction the_documented_projection_is_the_measured_one", "red_named": "the_documented_projection_is_the_measured_one", "green_before_exit": 0, "red_exit": 101, "green_after_exit": 0, "restore_byte_exact": true, "sha256_before": "1eeb379d7c4b3dbd47b387ef62a2be6f9c3b5499cdc54bc587d02b7e705c5d38", "mtime_plant": 1791200000.0, "mtime_restore": 1791400000.0, "result": "ok"},
  {"id": "P4-repetition-counts-every-success-again", "file": "src/harness/guard.rs", "defect": "the round-4 rule: every success of the key counts, whatever its result", "test": "cargo test --offline --lib harness::guard", "red_named": "a_repeated_action_whose_result_changes_is_not_unproductive_repetition", "green_before_exit": 0, "red_exit": 101, "green_after_exit": 0, "restore_byte_exact": true, "sha256_before": "a1311a1ed58853df1993d311d15ca969244c2a5bc2bb8baa764097b84c8c9a1e", "mtime_plant": 1791200000.0, "mtime_restore": 1791400000.0, "result": "ok"}
 ],
 "plants_note": "four controlled plants, each green -> red -> green with a byte-exact restore (sha256 compared) and both mtimes set explicitly (1791200000.0 for the plant, a newer 1791400000.0 for the restore, so cargo cannot skip the rebuild); every red run reported `test result:` so the test really ran, and named the intended test. Record: D:/hof-live-logs/plants.json, D:/hof-live-logs/plants.table, logs D:/hof-live-logs/P<n>-*.log. The runner's own summary predicate was self-contradictory and was recomputed from the recorded exits by D:/hof-live-work/fix_plants.py - the phases were never wrong.",
 "changed_files": {
  "modified": [
   ".spec/bevy/FIX-REPORT.md (F-1..F-5 corrections only: the cost block, the measured floor plus the new f3_correction block, the call-count lever, the system-prompt size, section 5, the 'does not pass' paragraph, and the two stale 'nothing was committed' sentences)",
   ".spec/bevy/COST-REPORT.md (F-1, F-2, the F-3 restatement in the criterion-4-cost disposition and in not_verified item 4, the 'what dominates' paragraph)"
  ],
  "appended": ["DECISIONS.md (D302 only; append-only, verified by hashing the prefix)"],
  "added": [".spec/bevy/LIVE-COST-REPORT.md (this file)"],
  "source_code": "none: the one code change this batch implemented was withdrawn and the tree was restored byte-exactly to HEAD",
  "run_evidence_untracked": ["runs/livecost1/**", "runs/bevy-livecost1/**"],
  "not_modified": "REQUIREMENTS.md, DESIGN-OVERVIEW.md, DESIGN-DETAIL.md, PRD.md, the spike reports, the round-1/2/3/4 reports and the three acceptance documents are untouched"
 },
 "unverified": [
  "Only one Developer call was measured. It is a first-iteration-shaped call on a fresh project; whether an iteration-2-shaped call (round-4 iter-2: 125 calls, 24 writes) now costs under the criterion is not measured and is not claimed.",
  "The tester and the second/third iterations were not run: the harness has no role-selective entry point, so `--iterations 1` ran planner + developer + tester, and the developer measurement is unaffected by the tester's 124 calls / 2,811,555 tokens.",
  "The tree-fingerprint variant of the write-free rule (the only signal that can see shell writes) was not implemented or measured, because no offline replay may execute the recorded shell commands that produced the tree changes; it needs another live round.",
  "Whether the live call's artifact would have been launchable at the point the withdrawn rule would have ended it (call 76) is not known: the artifact gate recorded launchable=true at call 150, and the last project-file change was call 44, but no gate was evaluated at call 76.",
  "The two known gitignored historical evidence files under runs/** were not re-fingerprinted; the key scan of this batch covers only the browsable tree, and no key was written into the repository, config/hoh.yaml or runs/**."
 ],
 "single_most_important_thing_next_batch": "Build the write-free budget on a signal that can see shell writes - a fingerprint of the artifact tree - because the guard's directive counter is blind to the writes the roles actually make (the live call edited src/main.rs with PowerShell at call 44, and round-4 iter-3 edited src/game.rs with [IO.File]::WriteAllText at calls 8 and 22). The cost criterion cannot be met by the visible-write signal without cutting real work: meeting it needs K <= 37 and leaving the recorded calls intact needs K >= 43. That signal, not a smaller number, is the next step, and it needs one live round to measure."
}
```

## 1. What was run, and what it cost

One real Developer call, driven from a project outside the repository with the tree at `fc25c32`
(clean) and the harness built in this batch's own directory (`D:\hof-live-target`):

```
hoh init --adapter bevy --project D:\hof-live-run\workspace            -> exit 0
hoh run --adapter bevy --project D:\hof-live-run\workspace \
        --run-id livecost1 --iterations 1 \
        --env-from-secret D:\hof-live-work\live.env                    -> exit 0
```

The Developer call, from the harness's own record and the provider's own per-call usage:

| quantity | value |
|---|---|
| model calls | **150** (the `agent.step_limit`, exactly) |
| prompt tokens | **3,537,843** |
| completion tokens | **113,277** |
| **total tokens** | **3,651,120** |
| wall clock | **1,278,222 ms (21.30 min)** |
| ended by | **`LimitsExceeded`** — it ran out of steps, it did not finish |
| wrote the artifact | **yes**: `artifact_valid=true`, gate `launchable=true`, `evidence_diff` added `src/sim_tests.rs` and modified `src/game.rs`, `src/main.rs` |
| first call / last call prompt | 4,269 / 40,404 tokens |

**Against the criterion — 1,500,000 `total_tokens` per Developer call — this is 2.43x and it fails.**
Against the baseline it is one call among 296: 17.4 % of the baseline round's 20,940,837 developer
tokens at 50.7 % of its calls; per call it is *cheaper* than the recorded round-4 iter-1
(23,586 mean prompt tokens against 36,878, −36.0 %), because the fold works, but it is **longer**:
69 calls there, 150 here.

Two things the round records that the offline batches could not:

* **The offline projection understates the folded cost.** The live context runs at
  **0.323468 tokens per wire byte** against the round-4 iter-2 fit of **0.255366** (+26.7 %). The
  fold leaves short JSON notes, which are denser per byte than the prose the fit was calibrated on.
  `ACCEPTANCE-FIX.md` listed the direction of this error as unmeasured; it is now measured.
* **The call count is not a repetition.** The call made **172 shell commands, 166 of them distinct**,
  so the round-5 repeated-success tripwire (which counts one action succeeding with a byte-identical
  result) has nothing to count — and it never fired.

## 2. Where the 150 calls went

| calls | what happened |
|---|---|
| 1–5 | orientation |
| 6, 14, 17, 19 | `HOH_WRITE_FILE` directives; 17 is `.hoh/scratch/notes.md` (hash-excluded, not artifact progress) |
| 43 | the last `HOH_WRITE_FILE` directive (`src/sim_tests.rs`) |
| **44** | **the last change to a project file at all**, made with a PowerShell `Set-Content` on `src/main.rs` — a shell write, invisible to the guard |
| 45–150 | **106 calls that changed no project file**: re-reading its own sources (`Get-Content`, `type`, `more`, `findstr`), rebuilding, re-checking. 62.7 % of the call's tokens |

The grind shape is therefore not "the same action again" (round 4's problem) but "**many different
actions that change nothing**".

## 3. The five corrections

All five are applied in place, in the two batch reports, only where they were factually wrong:

* **F-1** `COST-REPORT.md`: iter-2's projected total is **3,007,235**, not 3,034,063.
* **F-2** the system prompt is **14,522 bytes of content / 14,849 bytes of wire** (it was 14,783/14,814
  in three places). The live call confirms it exactly: `system_content_bytes 14522`,
  `system_wire_bytes 14849`. The "about a third of the compacted prompt" sentence that depended on the
  wrong figure was corrected too: 14,849 wire bytes is **17.7 %** of iter-2's compacted wire bytes and
  **3,791 of the compacted final call's 25,152 projected prompt tokens (15.1 %)**.
* **F-3, restated as a trade.** The tail-0 projection is **not** "an arithmetic lower bound on any
  context-only policy": it still replaces every superseded message with a note, so it bounds that
  family only. A policy that keeps nothing but the system prompt and the task projects to
  287,657 / **517,368** / 430,085 prompt tokens (369,289 / **843,321** / 516,206 with completion) for
  the three recorded calls and **would pass**. What the batch refuses is the **trade** — a role that no
  longer sees what it just did — not an impossibility. Because `DECISIONS.md` is append-only, D301's
  title and §(e) are superseded in the appended **D302** rather than edited.
* **F-4, re-derived or withdrawn.** The lever pairs now reproduce exactly with the acceptance's own
  method (`iter-2 first_60 [1,152,836, 1,478,789]`, `first_70 [1,385,772, 1,711,725]`,
  `first_80 [1,643,606, 1,969,559]`; `iter-3 first_80 [1,180,267, 1,266,388]`). The claim "roughly 85
  calls for iter-3" is **withdrawn** — its own first_80 is already *below* the target; the linear
  crossings are about **61** calls for iter-2 and about **91** for iter-3.
* **F-5** the batch is **committed** as `6290f77`; both "nothing was committed" sentences are corrected.

## 4. The call-count reduction: implemented, measured, **withdrawn**

**What was implemented.** `agent.max_write_free_steps = 32`: once a call has written its declared
artifact, it may make at most 32 model calls **without writing any file at all** — artifact, `.hoh`
scratch note or script. The next one is refused with the new status `WriteFreeBudgetExceeded`, enforced
by `WriteGuardEnvironment` at the step, against the live value. **Any** successful write directive
restarts the run (counting any write, not only the artifact, is the conservative choice: the
iterations whose artifact edits go through the shell always write the script first). The rule is inert
until the first write, because that phase belongs to `steps_per_artifact`.

**How it was measured: through the shipped guard, not a model of it.** Every recorded model call was
fed to the real `WriteGuardEnvironment` (shipped limits, `FakeShell` standing in for the shell so no
recorded command executes, the real write path for directives, a shared `StepCounter` incremented once
per call exactly as `CountingModel` does), with the provider's own recorded per-call usage as the
cost. Over **all four recorded Developer calls**:

| recorded call | calls | the rule ends it at | total tokens at the end | vs criterion | recorded directive writes lost |
|---|---|---|---|---|---|
| **live-iter-1** | 150 | **call 76** | **1,357,530** | **0.91x — it passes** | **none** |
| round4-iter-1 | 69 | call 51 | 1,790,635 (recorded, unfolded) | — | none |
| round4-iter-2 | 125 | never fires | — | — | none |
| round4-iter-3 | 102 | call 39 | — | — | none |

**The caveat that made me withdraw it, stated loudly.** "Zero lost writes" is true only of the guard's
own signal, and the guard's signal is blind. Round-4 **iter-3** fires at call 39, inside the run that
begins at its last visible write (call 6) and reaches the next (call 50) — **43 calls**, not the 31
the previous analysis assumed (the 31 counted `.hoh` scratch writes as artifact progress). Inside that
run the role edited `src/game.rs` at **calls 8 and 22** with
`powershell [IO.File]::ReadAllText` + `[IO.File]::WriteAllText`. The rule would have cut genuine
repairs. The same is true of the stricter variant that counted only artifact writes: it fires at
round-4 iter-2's call 105, before calls 107 and 110 run `.hoh/scratch/patch4.py` and `patch5.py`,
which edit `src/game.rs`.

**And the two bands do not overlap.** To meet the criterion the budget must end the live call by call
81 (the last cumulative total under 1,500,000 is 1,484,934; call 82 is 1,511,382), and the abort call
is `43 + K + 1`, so **K ≤ 37**. To leave every recorded call's artifact work intact it must not fire
before round-4 iter-3's call 50, so **K ≥ 43**. 37 < 43: *the same rule cannot both meet the criterion
and leave the recorded work alone.* The honest answer is therefore not "unreachable in principle" —
it is that the only signal this guard has is the wrong one, and the signal that would work (a
fingerprint of the artifact tree) cannot be validated offline, because the tree changes were produced
by shell commands no replay may execute.

**So the repository carries no behavioural change.** The implementation is preserved outside the
repository at `D:/hof-live-work/write-free-budget-WITHDRAWN.patch` (45,735 bytes; 753 insertions), and
the five files it touched were restored **byte-exactly** from their HEAD blobs (`git show HEAD:<path>`,
sha256 compared, `git diff --exit-code` clean for each) — `git checkout --` was not used.

The one context policy that *would* pass is worth stating too, because it is the refusal the previous
batch was reaching for: keeping only the system prompt and the task projects the live call to
**786,685 prompt + 113,277 completion = 899,962** (0.60x). It is refused, and the live call is the
evidence for why: this role re-read its own files constantly (9 `HOH_READ_FILE` directives and 172
shell commands, most of them `type`/`Get-Content`/`more`/`findstr`), so removing what it just did is
more likely to raise the call count than to lower the cost.

## 5. Disk, gate, plants, files

* **Disk.** F: was at 100 % with 5.6 G free. Seven directories belonging to this project's own effort
  were each verified to be a cargo target directory (`.rustc_info.json` + `debug/`), printed with
  their measured size, and removed with `shutil.rmtree` over the literal verified path — never
  `rm -rf`, never a wildcard: `hof-acc-target` 9.08 GiB, `hof-acc5-target` 9.42, `hof-cost-target`
  9.57, `hof-fix-target` 9.96, `hof-r3-target` 8.83, `hof-r4-target` 10.09, `hof-trust-target` 8.96 —
  **70,774,713,832 bytes = 65.91 GiB**, taking F: from 5.6 G to 67 G available. Everything afterwards
  ran on D:.
* **Gate.** `cargo test --offline` → **literal exit code 0**; **766 passed / 0 failed / 6 ignored /
  772 listed** over 58 `test result:` lines; `--list` exit 0 with 772 names; `--list --ignored` exit 0
  with exactly the 6 real-engine tests; **0** `warning:` lines in stdout and stderr;
  `cargo fmt --all --check` exit 0 emitting **0 bytes**; no cargo/rustc/hoh process before or after;
  build directory `D:\hof-live-target`. This is identical to the start tree (766/0/6/772) —
  no test was added or removed, because no behaviour was shipped.
* **Plants.** Four controlled plants, each green → red → green with a byte-exact restore (sha256
  compared) and both mtimes set explicitly: the fold short-circuited off (`compact.rs`), the example
  list reverted to the previous engine (`tools/index.rs`), the documented projection falsified
  (`config.rs`), and the round-4 repetition rule restored (`guard.rs`). Every green-before and
  green-after run exited 0; every red run exited **101**, really ran (`test result:` present) and
  named the intended test.

## 6. What worked, what does not, what I could not verify

**Worked.** The gate reproduces the start tree exactly on a tree I built myself. The five corrections
are in place and both report JSON blocks parse. The live call itself worked end to end: a fresh Bevy
project outside the repository, headless, the game on 15702 only, the developer wrote three project
files and the round exited 0 with a launchable artifact gate. The fold is real and measurable on a live
call (per-call prompt down 36 % against the recorded iter-1). The disk work was clean and reversible by
nature. The reduction was implemented and *honestly falsified by its own replay*.

**Does not work.** The criterion: **3,651,120 total tokens against 1,500,000**, 2.43x, and the call was
ended by the step budget rather than by finishing. And the lever that would meet it — ending a call
that has stopped writing — is not safe with the signal the guard has, because the roles write through
the shell where the guard cannot see them. The two bands (K ≤ 37 to meet the criterion, K ≥ 43 to cut
no recorded work) do not overlap.

**Could not verify.** Whether an iteration-2-shaped call (24 writes, 125 calls) is now under the
target — one call was measured, not three. Whether the withdrawn rule's end point would have left a
launchable artifact (the last project change was call 44 and the abort would have been call 76, but no
gate was evaluated there). Whether a tree-fingerprint signal reaches the target at all, since no
offline replay can execute the recorded shell commands that changed the tree. And the tester's and
round's cost: the tester spent 124 calls / 2,811,555 tokens, but the criterion is stated for the
Developer call only.

**The single most important thing for the next batch.** Build the write-free budget on a signal that
can see shell writes — a fingerprint of the artifact tree — because the guard's directive counter is
blind to the writes the roles actually make (the live call edited `src/main.rs` with PowerShell at call
44; round-4 iter-3 edited `src/game.rs` with `[IO.File]::WriteAllText` at calls 8 and 22). The
measurement is in §4: meeting the criterion needs the budget to end the live call by call 81, and
leaving the recorded calls intact needs it not to fire before round-4 iter-3's call 50 — the signal,
not a smaller number, is the next step, and it needs one live round to measure.
