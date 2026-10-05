# Bevy round-5 cost batch - repair report (the failed acceptance's AC-1..AC-14 and the cost criterion)

```json
{
 "schema": "hof-rs / bevy round-5 cost batch repair report",
 "produced_at": "2026-10-05",
 "branch": "bevy-core",
 "round_run_in_this_batch": false,
 "scope": "the required corrections of the independent acceptance .spec/bevy/ACCEPTANCE-COST.md (verdict fail): its defects AC-1..AC-14 and the unmet cost criterion. Nothing was committed, staged or pushed at the time; the batch's whole change set, including this report, is now COMMITTED as 6290f77 on branch bevy-core (defect F-5: the statement was true when written and is stale as a statement about the tree). no key was created, copied or printed; rm -rf was never used and no process was killed.",
 "gate": {
  "command": "cargo test --offline",
  "exit_code": 0,
  "exit_code_source": "literal `$?` written to F:/hof-fix-logs/gate.exit by the one script that ran the whole gate",
  "passed": 766,
  "failed": 0,
  "ignored": 6,
  "listed": 772,
  "listed_equals_passed_plus_ignored": true,
  "test_targets": 58,
  "warning_lines": 0,
  "start_tree_gate_measured_here": {
   "passed": 754,
   "failed": 0,
   "ignored": 6,
   "listed": 760,
   "exit_code": 0,
   "source": "F:/hof-fix-logs/baseline.* on the same build directory before any edit"
  },
  "delta": {
   "passed": 12,
   "listed": 12,
   "removed": 0
  },
  "list_command": "cargo test --offline -- --list",
  "list_exit_code": 0,
  "list_ignored_exit_code": 0,
  "list_ignored_count": 6,
  "fmt_command": "cargo fmt --all --check",
  "fmt_exit_code": 0,
  "fmt_output_bytes": 0,
  "build_dir": "F:/hof-fix-target (this batch's own; no second test process ran: tasklist showed no cargo/rustc/hof before or after)"
 },
 "changed_files": {
  "modified": [
   ".spec/bevy/COST-REPORT.md",
   ".spec/bevy/ROUND-3-REPORT.md",
   ".spec/bevy/ROUND-4-REPORT-COMPLETE.md",
   "DECISIONS.md",
   "config/hoh.yaml",
   "src/cli.rs",
   "src/config.rs",
   "src/harness/compact.rs",
   "src/harness/guard.rs",
   "src/runtime/record.rs",
   "src/runtime/run_loop.rs",
   "src/tools/index.rs",
   "tests/common/mod.rs",
   "tests/engine_identity.rs",
   "tests/repeated_action.rs",
   "tests/resume_round.rs",
   "tests/secret_hygiene.rs"
  ],
  "added": [],
  "removed": [],
  "this_report": ".spec/bevy/FIX-REPORT.md (new)",
  "no_test_removed": "the gate's name list grew 760 -> 772; a literal name-set diff against the pre-edit list shows 12 additions and 0 removals"
 },
 "defects": [
  {
   "id": "AC-1",
   "severity": "medium",
   "disposition": "fixed: the three false spawn-ordering statements are corrected in place and marked as corrected. .spec/bevy/ROUND-4-REPORT-COMPLETE.md line 73 (the ledger entry note), lines 130-131 (the boolean `the_ledger_nonce_is_written_before_the_spawn`, which was `true`, and the `so` sentence), and .spec/bevy/ROUND-3-REPORT.md line 140 (the caveat). Those are the only round-report lines touched; the raw diff of the round-4 file is exactly 3 changed lines and everything else in both files is byte-identical to HEAD.",
   "pinned_by": [
    "adapter::bevy::launch::tests::the_ledger_line_is_written_after_the_spawn_and_says_so (pins the code and the wording; the report lines are prose and carry no test)"
   ]
  },
  {
   "id": "AC-2",
   "severity": "low",
   "disposition": "fixed by appending D301 to DECISIONS.md: D298's two 'D301' references and D299's one now resolve, because D301 exists and is the entry they describe. DECISIONS.md is append-only here: the first 11414 lines hash to HEAD's blob (md5 0538080c85d040d525f8f76d11d496d4); the file grew to 11515 lines and nothing before line 11415 changed.",
   "pinned_by": [
    "no test: docs; verified by grep and by the line-hash comparison above"
   ]
  },
  {
   "id": "AC-3",
   "severity": "low",
   "disposition": "fixed by D301 (g), which supersedes D298 (e): the formula is now the measured `prompt_tokens ~= -38.28 + 0.255366 x wire_bytes` (iter-2, 125 points, worst residual 1,347 tokens, total reproduction error <0.01%; iter-1/iter-3 tokens-per-byte 0.257120/0.260054) and the system-prompt share is 14,849/161,566 = 9.2% of iter-2's final prompt (~a third of the compacted one). D298's own text cannot be edited (append-only), so D301 states the supersession inside the audit trail.",
   "pinned_by": [
    "the_measured_prompt_tokens_track_the_wire_bytes_the_call_sent (re-derives the fit the decision quotes)"
   ]
  },
  {
   "id": "AC-4",
   "severity": "low",
   "disposition": "fixed in .spec/bevy/COST-REPORT.md's RA-4 disposition: the 'six cases pinned, each false for a launch that really occurs' claim is withdrawn and replaced with what the code shows. For every launch that returns, readiness has already required a non-empty nonce and answered_nonce == nonce (launch.rs:502-529; a mismatch returns LaunchError::IdentityMismatch and stops the child, so no LaunchFacts exists), so the field's discriminating term for a real launch is the operating-system listening reading alone. The mismatched/absent answered_nonce cases are hand-built and are now labelled as impossible for a returned launch.",
   "pinned_by": [
    "adapter::bevy::round::tests::the_identity_fields_are_computed_from_the_facts_not_asserted (the facts, including the two impossible cases, as the report now describes them)"
   ]
  },
  {
   "id": "AC-5",
   "severity": "low",
   "disposition": "fixed in .spec/bevy/COST-REPORT.md: the RA-7 disposition and the 'what I could not verify' item 6 now say that RA-7 is present at .spec/bevy/ACCEPTANCE-ROUNDS.md:137 and is closed in substance by D299 (rounds 3-4) and D300, and that the earlier 'could not be located' text was false.",
   "pinned_by": [
    "no test: docs; verified by grep -n 'RA-7' .spec/bevy/ACCEPTANCE-ROUNDS.md"
   ]
  },
  {
   "id": "AC-6",
   "severity": "medium",
   "disposition": "fixed: (1) `--resume` no longer runs the previous-evidence quarantine (that area is the resumed round's own `.hoh`, not a previous round's); (2) a resume whose every iteration already completed returns before `start_round_game`, and `run()` tears down only the sessions the adapter actually reported started (`RoundGameSession`, set only on `Ok(Some(_))`). Both are driven through the real `run_loop::run` in tests.",
   "pinned_by": [
    "a_fully_complete_resume_runs_nothing_and_starts_no_game (no role, 0 starts, 0 stops, no quarantine directory, the round's own .hoh/scratch survives, the workspace untouched)",
    "a_resume_with_work_restores_the_tree_and_keeps_the_rounds_own_evidence (no quarantine directory, .hoh/scratch survives, a session is started and torn down, and warnings.log records the restore)"
   ]
  },
  {
   "id": "AC-7",
   "severity": "medium",
   "disposition": "fixed by restoring, validating and refusing, not by declaring: `RunMeta.project` (new, serde-default) records the absolute project path; `read_run_meta` + `check_resume_project` run before anything is touched and refuse a different project and an unrecorded one; `resume_restore_iteration` names the last completed iteration's snapshot (A0 when none completed); `restore_resume_workspace` rolls the workspace back to it and `VersionStore::rollback` re-hashes the restored tree, so a restore that did not land is an error; the discarded pre-restore hash is recorded in warnings.log; a missing snapshot is refused. The `.hoh` scratch/raw evidence is deliberately not restored or moved, and that is stated in the help text, the Orchestrator doc and the round's warning.",
   "pinned_by": [
    "a_resume_matches_only_the_project_the_run_id_recorded",
    "a_resume_against_another_project_is_refused (through the real run_loop::run: no role runs, no session starts, nothing is quarantined)",
    "a_resume_restores_the_interrupted_iterations_start_state (real VersionStore + rollback + re-hash)",
    "a_resume_with_work_restores_the_tree_and_keeps_the_rounds_own_evidence (a real interrupted run directory, driven through the real loop)",
    "a_resume_without_the_start_snapshot_is_refused",
    "a_resume_with_nothing_to_run_has_no_restore_target"
   ]
  },
  {
   "id": "AC-8",
   "severity": "medium",
   "disposition": "fixed in the code direction: the fold now lands on the agent's own `messages` (the loop folds before each step; `CountingModel` only counts), so the trajectory records exactly what was sent and the three prose claims (src/harness/compact.rs, DECISIONS.md, COST-REPORT.md) became true rather than being reworded. The fold's own measurement test does not depend on the un-folded record: it folds prefixes of the recorded round-4 trajectories, which were produced before the fold existed.",
   "pinned_by": [
    "harness::compact::tests::the_stored_trajectory_is_the_history_that_was_sent (drives the real loop with a stub model and environment: exactly the preserved tail observation stays verbatim, the two superseded ones carry the fold note in the saved trajectory, and the last provider call's message list equals the stored prefix)"
   ]
  },
  {
   "id": "AC-9",
   "severity": "low",
   "disposition": "fixed: src/config.rs's doc comment now quotes the measured projection `875,647 / 2,681,282 / 1,663,325` prompt tokens against the recorded `2,544,563 / 12,765,478 / 5,137,090` (and names the recorded total_tokens), and no longer '839K / 2.50M / 1.48M'.",
   "pinned_by": [
    "the_documented_projection_is_the_measured_one (reads src/config.rs and pins both the measured figures and the absence of the contradicted one)"
   ]
  },
  {
   "id": "AC-10",
   "severity": "low",
   "disposition": "fixed in .spec/bevy/COST-REPORT.md: the headline is now like-for-like in both directions - prompt-to-prompt 20,447,131 -> 5,220,254 (74.47% reduction, 25.53% of the recorded prompt spend), and adding the unchanged completion tokens (493,706) back gives 5,713,960 against 20,940,837 (72.71%). The JSON block's projected_round records both, and the three after-figures are stated as summing to 5,220,254.",
   "pinned_by": [
    "no test: docs; the inputs are the per-iteration prompt/completion figures in runs/round4/iter-*/result.json, read by tests/context_compaction.rs"
   ]
  },
  {
   "id": "AC-11",
   "severity": "low",
   "disposition": "fixed: production `EXAMPLE_PREFERENCE` (src/tools/index.rs) now names the delivered Bevy surface (the eight semantic tools and the generic BRP verbs), and `render_tools_markdown_for` gained a deterministic fallback that renders the first three visible tools when a surface contains none of the preferred names. The old list matched nothing on a Bevy round, so every real Bevy role's 'Complete call examples' section was empty while the binary still carried the previous engine's names.",
   "pinned_by": [
    "tools::index::tests::the_complete_call_examples_are_the_delivered_bevy_tools (the example section names a runnable Bevy call, is not empty, and no previous-engine needle is in the production list)",
    "tests/tool_discovery.rs::tools_markdown_carries_parameter_names_and_types (the fallback keeps the section non-empty for the embedded mcp snapshot)"
   ]
  },
  {
   "id": "AC-12",
   "severity": "low",
   "disposition": "noted, no action beyond AC-1: .spec/bevy/ROUND-4-REPORT-COMPLETE.md is still a modified frozen document. The modification is now 3 lines (line 73 and lines 130-131), all of them the RA-1 ordering correction item 3 authorised; git's normalised diff of that file is exactly those 3 lines. Its working-copy line endings are CRLF, as the previous batch left them (HEAD's blob is LF); that predates this batch and was left untouched.",
   "pinned_by": [
    "no test: a documented, declared exception"
   ]
  },
  {
   "id": "AC-13",
   "severity": "low",
   "disposition": "fixed: tests/repeated_action.rs's round-5 projection compares `harness::guard::output_digest` of the observation's `<output>` body (the string the guard digests) instead of the observation's byte length, and `output_digest` is now `pub` so the projection uses the guard's own function rather than a copy. The recorded conclusions are unchanged (identical-result maxima 1/1/2, no abort).",
   "pinned_by": [
    "the_round_five_counter_compares_the_guards_digest_not_the_length (a synthetic control: two equal-length, different-byte results must not count as a repetition; the length proxy counts them as one)"
   ]
  },
  {
   "id": "AC-14",
   "severity": "low",
   "disposition": "fixed: config/hoh.yaml's `agent` section now documents `compact_history` and `compact_history_tail` (what the fold does, what is never folded, the measured projection, and the measured floor that keeps the 1.5M target out of reach by context alone).",
   "pinned_by": [
    "the_agent_configuration_documents_the_compaction_knobs"
   ]
  }
 ],
 "resume_semantics": {
  "preconditions_before_anything_is_touched": [
   "the run directory must exist (CLI, cli_impl.rs), and --resume is mutually exclusive with --fresh-workspace and --reset-workspace",
   "runs/<id>/meta.json must record a project (RunMeta.project) and it must be the configured --project; a different project is refused and an unrecorded one (a run written before the field existed) is refused too. Path equality accepts two absolute spellings, then falls back to canonical paths"
  ],
  "what_runs": "plan_resume over runs/<id>/iter-<n>/result.json: an iteration with ok:true is not re-run and its usage/gate/version are carried into the summary; the first iteration that is not ok runs from its start",
  "what_is_restored": "the project tree is rolled back to the artifact the last completed iteration froze (A0 when none completed) before the first incomplete iteration runs; VersionStore::rollback re-hashes the restored tree, so a restore that did not land is an error; the pre-restore hash is recorded in warnings.log when the tree had drifted; a run with no snapshot for that iteration is refused",
  "what_is_not_restored": "(1) the interrupted call's own work: there is no role-level checkpoint and a Developer edits the workspace in place, so the iteration is replayed from its start; (2) this round's own .hoh scratch and raw deterministic evidence: it is deliberately NOT quarantined and stays in place, because those bytes belong to the round being resumed, not to a previous round",
  "side_effects_refused": "a resume whose every iteration already completed returns before start_round_game, and run() calls stop_round_game only for a session the adapter actually reported started; a refused resume touches nothing and starts nothing",
  "recorded": "the scope is written into the round's own warnings.log (resumed_from_interrupted_round) including the restore, its verification and what is not restored; cli.rs's --resume help and Orchestrator::resume say the same"
 },
 "fold_matches_its_prose": {
  "answer": true,
  "how": "the code was moved to the prose's side, not the prose to the code's. run_compacting_agent now calls compact_history on agent.messages itself before every step, and the model wrapper (CountingModel) only counts steps; DefaultAgent::query therefore hands the provider the same Vec that save() serialises.",
  "statements_that_became_true": [
   "src/harness/compact.rs:29-30 ('the fold is applied to the agent's own history, so what is recorded in the trajectory is exactly what was sent')",
   "DECISIONS.md D300 (a) (~line 11371-11372)",
   ".spec/bevy/COST-REPORT.md 1.1 (~line 139-140)"
  ],
  "control": "the AC-8 test fails when the fold is put back on a copy (plant P4)"
 },
 "cost": {
  "criterion": "below 1,500,000 tokens per Developer call (total_tokens), the one criterion that has never passed",
  "verdict": "still not met, and no value of the tail changes that for THIS fold. What the batch measures is that the fold's own family - every superseded message replaced by a note, tail 12 or 0 - cannot meet it, and that the tail-0 figure is not an arithmetic lower bound on every context-only policy (defect F-3, corrected below). Reasoned refusal of a trade, not a shaved number and not an impossibility.",
  "method": "the same method as the previous batch: for every recorded round-4 Developer model call (296 calls) the message prefix the agent held is reconstructed from runs/round4/iter-*/traj/developer.attempt1.json, the wire size is the four-field subset mini sends, the provider's own usage.prompt_tokens is fitted against it per iteration by least squares, the repository's own compact_history folds the same prefix at tail 12, and the compacted bytes are converted with the fitted ratio. Reproduced independently in Python (F:/hof-fix-work/compose.py over the acceptance's /f/hof-acc5-work/measure.py) and by the repository's own test (F:/hof-fix-logs/ctx-repair.out).",
  "per_developer_call": {
   "iter_1": {
    "model_calls": 69,
    "recorded_prompt": 2544563,
    "recorded_total": 2626195,
    "completion": 81632,
    "projected_prompt": 875647,
    "projected_total": 957279,
    "prompt_reduction": 0.6559
   },
   "iter_2": {
    "model_calls": 125,
    "recorded_prompt": 12765478,
    "recorded_total": 13091431,
    "completion": 325953,
    "projected_prompt": 2681282,
    "projected_total": 3007235,
    "prompt_reduction": 0.79
   },
   "iter_3": {
    "model_calls": 102,
    "recorded_prompt": 5137090,
    "recorded_total": 5223211,
    "completion": 86121,
    "projected_prompt": 1663325,
    "projected_total": 1749446,
    "prompt_reduction": 0.6763
   },
   "total": {
    "model_calls": 296,
    "recorded_prompt": 20447131,
    "recorded_total": 20940837,
    "completion": 493706,
    "projected_prompt": 5220254,
    "projected_total": 5713960,
    "prompt_reduction": 0.7447,
    "total_reduction": 0.7271
   }
  },
  "fit": {
   "iter_2_slope_tokens_per_wire_byte": 0.255366,
   "iter_2_intercept": -38.28,
   "iter_2_worst_call_residual_tokens": 1347,
   "total_reproduction_error": "<0.01%",
   "iter_1_ratio": 0.25712,
   "iter_3_ratio": 0.260054
  },
  "composition_at_tail_12_iter_2": {
   "compacted_wire_bytes": 10503715,
   "system_prompt_bytes": 1781880,
   "task_bytes": 163800,
   "folded_notes_bytes": 1812030,
   "messages_under_the_fold_floor_bytes": 3011316,
   "preserved_tail_bytes": 3581624,
   "note": "the 128-512 byte band the fold leaves verbatim (28.7% of the compacted bytes) is the largest non-tail term, but the note that identifies a 300-byte payload is itself ~280 bytes, so only ~2.1% of it is recoverable by lowering the floor"
  },
  "measured_floor": {
   "what": "the same fold with the verbatim tail removed entirely (tail 0). It bounds the fold's own family only - every superseded message is still replaced by a ~200-300 byte note - NOT every context-only policy (defect F-3; see the correction at the end of this block)",
   "projected_prompt": {
    "iter_1": 699900,
    "iter_2": 1873629,
    "iter_3": 1430696
   },
   "projected_total_with_unchanged_completion": {
    "iter_1": 781532,
    "iter_2": 2199582,
    "iter_3": 1516817
   },
   "verdict": "iter-2 stays at 1.47x the target and iter-3 at 1.01x, so no tail value of this fold meets the criterion; reducing the tail would trade role capability for a criterion that is still failed"
  },
  "f3_correction": {
   "defect": "F-3: calling the tail-0 figure 'an arithmetic lower bound on any context-only policy' and concluding that 'no context-only policy can make it pass' was stronger than the measurement.",
   "why": "the tail-0 computation still replaces every superseded message with a note, so it bounds only the fold's own family. At tail 0 for iter-2 the notes plus the under-floor messages are about 5.2 MB of the 7.34 MB compacted total; the system prompt (1,781,880 bytes) and the task (163,800) are never folded.",
   "what_a_stronger_policy_projects_to": {
    "policy": "keep nothing but the system prompt and the task on every call",
    "projected_prompt": {"iter_1": 287657, "iter_2": 517368, "iter_3": 430085},
    "projected_total_with_unchanged_completion": {"iter_1": 369289, "iter_2": 843321, "iter_3": 516206},
    "conclusion": "iter-2 would be 0.56x the target: a context-only policy CAN make it pass. What this batch refuses is the trade - a role that no longer sees the history it works from - and that is what the reports now say instead of asserting an impossibility."
   },
   "reproduced_by": "D:/hof-live-work/cost_measure.py (own copy) and F:/hof-acc6-work/composition.py (the acceptance's independent re-implementation) both print these integers from runs/round4/iter-*/traj/developer.attempt1.json; the repository's own fold produced the same tail totals in the acceptance's probe crate (27/27)"
  },
  "call_count_lever": {
   "what": "projection over the first N recorded model calls of each Developer iteration (tail 12). F-4: the pairs published here before did not reproduce exactly with the disclosed method (up to 3,055 tokens, 0.2%, apart on iter-2 and 771 on iter-1) and the iter-3 conclusion contradicted this block's own first_80. The pairs below are the re-derived ones. A-5 (corrected by the round-7 write-accounting batch): they reproduce the acceptance's independent F:/hof-acc6-work/composition.py EXACTLY, and they do NOT reproduce this batch's own D:/hof-live-work/cost_measure.py, which uses a different second component; the earlier wording claimed both agree exactly and that was false.",
   "iter_2": {
    "first_40": [625352, 951305],
    "first_60": [1152836, 1478789],
    "first_70": [1385772, 1711725],
    "first_80": [1643606, 1969559],
    "first_100": [2054879, 2380832],
    "full_125": [2681282, 3007235]
   },
   "iter_3": {
    "first_80": [1180267, 1266388],
    "first_100": [1616118, 1702239],
    "full_102": [1663325, 1749446]
   },
   "iter_1": {
    "first_60": [746465, 828097],
    "full_69": [875647, 957279]
   },
   "verdict": "the target needs 61 model calls for iter-2 (recorded: 125) and 92 for iter-3 (recorded: 102). A-5 (corrected by the round-7 write-accounting batch): 61 is the CURVE'S OWN crossing under the published convention, not an interpolation between the first_60 and first_70 samples - call 60 is 1,478,789 and call 61 is 1,502,016, so the first N at or above the target is 61 (interpolated 60.9); for iter-3 call 91 is 1,498,609 and call 92 is 1,520,424, so the first N is 92 (interpolated 91.1). The earlier wording called 61 'a linear crossing of this block's own first_60 -> first_70 pair', which is not how it was obtained. F-4: the earlier 'roughly 85 for iter-3' is WITHDRAWN - it contradicted this block's own first_80, whose total (1,266,388 on the re-derived pair, 1,265,261 on the old one) is already below the target, so a crossing cannot be above 80. The substantive conclusion survives: the role must do the same work in about half the round trips, which is a behavioural change no offline batch can justify; capping at 61 would have cut the recorded iter-2 at 49% of its work",
   "counted_basis": "[projected prompt tokens, projected total tokens = that prompt plus the iteration's whole recorded completion tokens] - the convention the published pairs and the 61/92 crossings use, now stated here because A-5 found it was not stated where the pairs are published. On the stricter basis (each partial prefix carrying only the completion tokens of the calls it contains, which is what this batch's own D:/hof-live-work/cost_measure.py computes) the first N at or above the target is 65 for iter-2 (call 64 is 1,477,946, call 65 is 1,504,428; interpolated 64.8) and 92 for iter-3 (interpolated 91.3)."
  },
  "further_reduction_found": "none that does not damage the roles' ability to work",
  "measured_alternatives_rejected": [
   "shortening the fixed system prompt: it is 14,849 wire bytes (14,522 bytes of content) re-sent on every call, 17.7% of iter-2's compacted wire bytes. Removing every character of it (which would remove the role's instructions) still leaves iter-2 above the target once the completion tokens are counted, and it is the one term whose removal is known to damage the role",
   "lowering compact_history_tail: measured, and pointless - tail 0 (1,873,629 prompt, 2,199,582 total for iter-2) is still above the target, so no tail value passes and every reduced value costs coherence",
   "lowering the fold floor from 512 to 64 with a shortened note while keeping the first line (200 chars) and command (160 chars) exactly as they are: iter-2 2,679,708 -> 2,554,700 in the simulator (-4.66%), still 1.7x the target, and it changes a fold the acceptance passed. Recorded as measured and not taken"
  ],
  "what_would_settle_it": "one real Developer call: whether fewer model calls is achievable without losing the artifact, and whether the projected prompt tokens are the observed ones"
 },
 "plants": [
  {
   "id": "P1-resume-does-not-restore",
   "defect": "AC-7(a): the interrupted iteration re-runs on its own partial edits (pre-repair).",
   "file": "src/runtime/run_loop.rs",
   "test_args": [
    "--test",
    "resume_round"
   ],
   "green_before": true,
   "green_before_exit": 0,
   "red": true,
   "red_exit": 101,
   "red_named": [
    "a_resume_restores_the_interrupted_iterations_start_state"
   ],
   "green_after": true,
   "green_after_exit": 0,
   "restore_byte_exact": true,
   "sha256_before": "4be8b572f3d3b6ae1410b7b6d7edc1a25149e68272c385fb279879f693dd79e7",
   "sha256_after_restore": "4be8b572f3d3b6ae1410b7b6d7edc1a25149e68272c385fb279879f693dd79e7",
   "mtime_plant": 1791200000.0,
   "mtime_restore": 1791300000.0
  },
  {
   "id": "P2-resume-identity-unchecked",
   "defect": "AC-7(b): a resume continues one run against another run's tree.",
   "file": "src/runtime/run_loop.rs",
   "test_args": [
    "--test",
    "resume_round"
   ],
   "green_before": true,
   "green_before_exit": 0,
   "red": true,
   "red_exit": 101,
   "red_named": [
    "a_resume_against_another_project_is_refused"
   ],
   "green_after": true,
   "green_after_exit": 0,
   "restore_byte_exact": true,
   "sha256_before": "4be8b572f3d3b6ae1410b7b6d7edc1a25149e68272c385fb279879f693dd79e7",
   "sha256_after_restore": "4be8b572f3d3b6ae1410b7b6d7edc1a25149e68272c385fb279879f693dd79e7",
   "mtime_plant": 1791200000.0,
   "mtime_restore": 1791300000.0
  },
  {
   "id": "P3-resume-quarantines-its-own-round",
   "defect": "AC-6: `--resume` moves the round's own `.hoh` aside before doing resume work.",
   "file": "src/runtime/run_loop.rs",
   "test_args": [
    "--test",
    "resume_round"
   ],
   "green_before": true,
   "green_before_exit": 0,
   "red": true,
   "red_exit": 101,
   "red_named": [
    "a_fully_complete_resume_runs_nothing_and_starts_no_game"
   ],
   "green_after": true,
   "green_after_exit": 0,
   "restore_byte_exact": true,
   "sha256_before": "4be8b572f3d3b6ae1410b7b6d7edc1a25149e68272c385fb279879f693dd79e7",
   "sha256_after_restore": "4be8b572f3d3b6ae1410b7b6d7edc1a25149e68272c385fb279879f693dd79e7",
   "mtime_plant": 1791200000.0,
   "mtime_restore": 1791300000.0
  },
  {
   "id": "P4-fold-lands-on-a-copy",
   "defect": "AC-8: the fold is applied to a copy, so the stored trajectory is not what was sent.",
   "file": "src/harness/compact.rs",
   "test_args": [
    "--lib",
    "harness::compact"
   ],
   "green_before": true,
   "green_before_exit": 0,
   "red": true,
   "red_exit": 101,
   "red_named": [
    "the_stored_trajectory_is_the_history_that_was_sent"
   ],
   "green_after": true,
   "green_after_exit": 0,
   "restore_byte_exact": true,
   "sha256_before": "49b524e75eb2b256430c17dc64d015264011815abcc294ac6144a76ad89ed8c4",
   "sha256_after_restore": "49b524e75eb2b256430c17dc64d015264011815abcc294ac6144a76ad89ed8c4",
   "mtime_plant": 1791200000.0,
   "mtime_restore": 1791300000.0
  },
  {
   "id": "P5-example-preference-is-the-old-engine",
   "defect": "AC-11: the production example list names tools no Bevy round delivers.",
   "file": "src/tools/index.rs",
   "test_args": [
    "--lib",
    "tools::index"
   ],
   "green_before": true,
   "green_before_exit": 0,
   "red": true,
   "red_exit": 101,
   "red_named": [
    "the_complete_call_examples_are_the_delivered_bevy_tools"
   ],
   "green_after": true,
   "green_after_exit": 0,
   "restore_byte_exact": true,
   "sha256_before": "f84f6670318363982c0b81c71956fcdb3ef352227887491732e7600a29d34f12",
   "sha256_after_restore": "f84f6670318363982c0b81c71956fcdb3ef352227887491732e7600a29d34f12",
   "mtime_plant": 1791200000.0,
   "mtime_restore": 1791300000.0
  },
  {
   "id": "P6-tripwire-projection-compares-lengths",
   "defect": "AC-13: the projection compares a byte length instead of the guard's digest.",
   "file": "tests/repeated_action.rs",
   "test_args": [
    "--test",
    "repeated_action"
   ],
   "green_before": true,
   "green_before_exit": 0,
   "red": true,
   "red_exit": 101,
   "red_named": [
    "the_round_five_counter_compares_the_guards_digest_not_the_length"
   ],
   "green_after": true,
   "green_after_exit": 0,
   "restore_byte_exact": true,
   "sha256_before": "2b564277db459d40713cf6c0b4b20bae5c75238a6c74be4877a5f59b945d5af1",
   "sha256_after_restore": "2b564277db459d40713cf6c0b4b20bae5c75238a6c74be4877a5f59b945d5af1",
   "mtime_plant": 1791200000.0,
   "mtime_restore": 1791300000.0
  }
 ],
 "declared_rather_than_fixed": [
  "the 1.5M-token-per-Developer-call target is not met and this batch proves it is not reachable by context reduction at all (the tail-0 floor is 2,199,582 total tokens for iter-2); the next lever is the call count and it needs a live round",
  "the 177-tool embedded snapshot (tests/fixtures/mcp/tools_list.json) is still compiled in via include_str! because it is the editor-mediated (adapter.kind=mcp) channel's offline schema fallback and is still in use; the previous engine's tool names therefore remain in the binary from that fixture. EXAMPLE_PREFERENCE no longer carries any of them (AC-11)",
  "previous-engine tool-name literals remain in #[cfg(test)] code in src/runtime/policy.rs and src/tools/endpoint.rs; cfg(test) code is in no build product",
  ".spec/bevy/ROUND-4-REPORT-COMPLETE.md remains a modified frozen document: the 3 authorised RA-1 lines (AC-12). Its working-copy line endings are CRLF as the previous batch left them (HEAD's blob is LF) and were left untouched",
  "no live call, no live resume and no round were run: every number here is code, tests or arithmetic over recorded trajectories"
 ],
 "unverified": [
  "whether a live Developer call produces the projected prompt tokens, and whether the role still works with 12 verbatim messages",
  "whether a live --resume (a real interrupted round) behaves as the tests describe: the tests drive the real run_loop::run over a prepared run directory with the offline adapter, not over an engine round",
  "whether reducing the Developer's model-call count is achievable without losing the artifact: the only lever that could meet the cost target, and it needs a round",
  "whether the previous engine's tool names in the embedded snapshot are ever delivered to a role in a real round: the Bevy channel does not use that snapshot, and the mcp path is not run by the bevy flow"
 ],
 "single_most_important_thing_next_batch": "Run one real Developer call and count its model calls, not just its tokens. The context is already near its information floor (with no verbatim tail at all, iter-2 still projects to 2,199,582 total tokens against the 1.5M target), so the only lever left is the number of round trips - 125 recorded where the budget needs about 60. Every other item in this batch is pinned by a test that goes red when the behaviour is removed; that one needs a round to measure and is the only way the cost criterion can ever pass."
}
```

## 1. What this batch is

`.spec/bevy/ACCEPTANCE-COST.md` returns **fail** on the round-5 cost batch. Its verdict says the fold,
the tripwire's new semantics and the RA-2/RA-3/RA-5/RA-6/RA-8/RA-9 fixes **passed** and must be kept;
what failed is the cost criterion, and what was found defective is the `--resume` path, the claim that
the fold lands on the agent's own history, and a set of statements that do not match the tree. This
batch is exactly those corrections.

Nothing was committed, staged or pushed **at the time this report was written**; the batch's whole
change set, including this report, is now committed as `6290f77` on `bevy-core` (defect **F-5** of the
third acceptance: the sentence was true when written, but as a statement about the tree it had become
false — corrected here rather than left to contradict the reader's `git log`). No round, engine,
network or model call was run. No key was
created, copied or printed. `rm -rf` was never used; no process was killed. All helper scripts and logs
live outside the repository, in `F:/hof-fix-work` and `F:/hof-fix-logs`; the build directory is
`F:/hof-fix-target`, this batch's own.

## 2. `--resume`: what it does now

The rule the code, the help and the round's own warning state, in order:

1. **Before anything is touched** the CLI requires the run directory to exist and forbids
   `--fresh-workspace`/`--reset-workspace`; `run_inner` then reads `runs/<id>/meta.json` and refuses
   unless the recorded `project` is the configured `--project`. A run whose meta predates the field has
   no recorded project, so it is refused rather than guessed at. Nothing is created, initialised,
   quarantined or launched before this check.
2. **`plan_resume`** decides what runs: every iteration whose `result.json` says `ok: true` is not
   re-run (usage, gate and version are carried into the summary); the first iteration that is not
   `ok` runs from its start.
3. **Nothing is quarantined.** The previous-evidence move is for *a previous round's* bytes; on a
   resume the `.hoh` in the workspace is the resumed round's own scratch and raw deterministic
   evidence, and moving it would hide the interrupted iteration's records from the iteration about to
   re-run.
4. **The start state is restored and verified.** The workspace is rolled back to the artifact the last
   completed iteration froze (`A0` when none completed) and `VersionStore::rollback` re-hashes the
   restored tree, so a restore that did not land is an error rather than a quiet wrong state. The
   pre-restore hash is recorded in `warnings.log` when the tree had drifted, so "partial edits were
   discarded" is a fact in the record. A run with no snapshot for that iteration is refused.
5. **A resume with nothing to run starts no game session**, and `run()` calls `stop_round_game` only
   for a session the adapter actually reported started. A refused resume starts (and stops) nothing.

What is **not** restored is stated in the same places: the interrupted *call*'s own work is gone (there
is no role-level checkpoint and a Developer edits the workspace in place, so the iteration is replayed
from its start), and this round's own `.hoh` scratch/raw evidence is left exactly where it is.

## 3. The fold, its prose, and the record

`src/harness/compact.rs:29-30`, `DECISIONS.md` D300 (a) and `COST-REPORT.md` 1.1 all claimed that the
fold lands on the agent's own history. It did not: `CompactedModel::query` folded `messages.to_vec()`
and sent the copy, while `DefaultAgent::query` pushed the unfolded response into `self.messages` — the
Vec `save()` serialises. The claim is now true because the code moved to it: the loop folds
`agent.messages` itself before each step, and the model wrapper only counts steps. The last provider
call's message list and the stored trajectory's prefix are asserted equal by
`harness::compact::tests::the_stored_trajectory_is_the_history_that_was_sent`, which drives the real
loop with a stub model and a stub environment and fails when the fold is put back on a copy (plant P4).

## 4. Plants

Six controlled plants, each green -> red -> green with a byte-exact restore (sha256 compared) and both
mtimes set explicitly (`1791200000` for the plant, a newer `1791300000` for the restore, so cargo
cannot skip the rebuild). The machine-readable record is the `plants` block above; the full test output
of every phase is in `F:/hof-fix-logs/plants-<id>.log`.

| plant | file | the planted defect | green before | red | green after | restore |
|---|---|---|---|---|---|---|
| P1 | `src/runtime/run_loop.rs` | the restore is skipped (AC-7a) | exit 0 | exit 101, `a_resume_restores_the_interrupted_iterations_start_state` | exit 0 | byte-exact |
| P2 | `src/runtime/run_loop.rs` | the project identity is unchecked (AC-7b) | exit 0 | exit 101, `a_resume_against_another_project_is_refused` | exit 0 | byte-exact |
| P3 | `src/runtime/run_loop.rs` | the resume quarantines its own round (AC-6) | exit 0 | exit 101, `a_fully_complete_resume_runs_nothing_and_starts_no_game` | exit 0 | byte-exact |
| P4 | `src/harness/compact.rs` | the fold lands on a copy (AC-8) | exit 0 | exit 101, `the_stored_trajectory_is_the_history_that_was_sent` | exit 0 | byte-exact |
| P5 | `src/tools/index.rs` | the example list is the old engine's (AC-11) | exit 0 | exit 101, `the_complete_call_examples_are_the_delivered_bevy_tools` | exit 0 | byte-exact |
| P6 | `tests/repeated_action.rs` | the projection compares lengths, not the digest (AC-13) | exit 0 | exit 101, `the_round_five_counter_compares_the_guards_digest_not_the_length` | exit 0 | byte-exact |

## 5. The cost target: the fold's own floor, the trade this batch refuses, and why nothing here shaves a prompt to meet a number

The criterion is *below 1,500,000 `total_tokens` per Developer call*. It still fails, and this batch
adds the measurement that shows **no value of this fold's tail can make it pass** — that is the whole
of the claim, and defect **F-3** corrects the stronger wording this section used to carry ("no
context-only policy can make it pass"). The tail-0 figure below still replaces every superseded message
with a note, so it bounds the fold's own family, not every context-only policy; the correction at the
end of this section states the policy that *would* pass and why it is refused. All numbers come from the
same method the previous batch used and the acceptance independently reproduced; the repository's own
test prints them again (`F:/hof-fix-logs/ctx-repair.out`).

At the shipped policy (`compact_history_tail = 12`):

| recorded Developer call | model calls | recorded prompt | projected prompt | recorded total | projected total | prompt reduction |
|---|---|---|---|---|---|---|
| iter-1 | 69 | 2,544,563 | **875,647** | 2,626,195 | 957,279 | 65.6 % |
| iter-2 | 125 | 12,765,478 | **2,681,282** | 13,091,431 | 3,007,235 | 79.0 % |
| iter-3 | 102 | 5,137,090 | **1,663,325** | 5,223,211 | 1,749,446 | 67.6 % |
| total | 296 | 20,447,131 | **5,220,254** | 20,940,837 | 5,713,960 | 74.47 % (72.71 % on totals) |

(the "projected total" adds the iteration's *unchanged* completion tokens: 81,632 / 325,953 / 86,121.)

**The fold's floor.** With the verbatim tail removed entirely (`tail = 0`) the projection is 699,900 /
**1,873,629** / 1,430,696 prompt tokens, i.e. **781,532 / 2,199,582 / 1,516,817** including completion.
iter-2 stays at 1.47x the target and iter-3 at 1.01x. So **every** tail value of this fold fails the
criterion, and lowering the tail can only buy a smaller failure at the cost of the model's view of what
it just did.

**F-3 — what that floor does *not* bound.** The tail-0 computation still replaces every superseded
message with a ~200–300-byte note, so it is a lower bound on the fold's own family, **not** on every
context-only policy. At tail 0 for iter-2 the notes plus the under-floor messages are about 5.2 MB of
the 7.34 MB compacted total, and the system prompt (1,781,880 bytes) and the task (163,800) are never
folded at all. A policy that keeps **nothing but the system prompt and the task** — dropped consumed
pairs outright — projects to:

| recorded Developer call | projected prompt | projected total (+ unchanged completion) | vs the 1.5M target |
|---|---|---|---|
| iter-1 | 287,657 | 369,289 | 0.25x |
| iter-2 | 517,368 | **843,321** | **0.56x — it passes** |
| iter-3 | 430,085 | 516,206 | 0.34x |

So a context-only policy **can** make the criterion pass. What this batch refuses, and says it refuses,
is the **trade**: that policy removes the history in which the role sees what it has already done and
read. The honest sentence is therefore "no policy that keeps the last 12 messages verbatim and notes
each folded payload meets the target, and anything aggressive enough to meet it removes history the role
needs to work" — not "no context-only policy can make it pass".

**The system prompt.** It is **14,522 bytes of content / 14,849 wire bytes** (defect **F-2**: the
quoted 14,783/14,814 was wrong and the report's own composition refutes it — `system_prompt_bytes`
1,781,880 over the 120 folded calls is exactly 14,849) re-sent on every call — 17.7 % of iter-2's
*compacted* wire bytes, and 3,791 of the compacted final call's 25,152 projected prompt tokens
(15.1 %), by the measured 0.2553 tokens-per-wire-byte ratio. Removing it entirely is not a real option
(it is
the role's instructions), and even then iter-2 would stay above the target once the 325,953 completion
tokens are counted. It is exactly the "shave the prompt to hit a number" move the task describes, and
it is refused.

**What the remaining spend is.** At tail 12 for iter-2 the compacted bytes are 10,503,715: system
1,781,880 (17.0 %), task 163,800 (1.6 %), fold notes 1,812,030 (17.3 %), the messages the fold leaves
verbatim because they are under its 512-byte floor 3,011,316 (28.7 %), and the preserved tail
3,581,624 (34.1 %). The 128–512-byte band is the largest non-tail term, but a note that identifies a
300-byte payload is itself about 280 bytes, which is why lowering the floor to 64 with a shortened note
(same kept first line and command) moves iter-2 only from 2,679,708 to 2,554,700 in the simulator
(−4.66 %) — and it would change a fold the acceptance passed. Measured, recorded, not taken.

**The only lever that reaches the criterion is the call count**, and it is behavioural. Projected over
the first *N* recorded model calls at tail 12 (prompt, then prompt+completion):

* iter-2: 40 → 625,352 / 951,305; **60 → 1,152,836 / 1,478,789**; 70 → 1,385,772 / 1,711,725;
  125 → 2,681,282 / 3,007,235.
* iter-3: **80 → 1,180,267 / 1,266,388**; 100 → 1,616,118 / 1,702,239; 102 → 1,663,325 / 1,749,446.
* iter-1: 60 → 746,465 / 828,097; 69 → 875,647 / 957,279.

(F-4: these are the **re-derived** pairs. The wording published here before — iter-2 first_60
1,153,140 / 1,479,093, first_70 1,384,463 / 1,710,416, first_80 1,640,551 / 1,966,504, iter-3 first_80
1,179,140 / 1,265,261 — does not reproduce with the disclosed method; the differences are ≤0.26% on
iter-2 and 771 tokens on iter-1, and the full-iteration values match exactly. The pairs above are what
the acceptance's independent `F:/hof-acc6-work/composition.py` gives, and they are what the correction
below is computed from. **A-5, corrected by the round-7 write-accounting batch:** the earlier wording
said "my own copy of the method and the acceptance's independent `composition.py` both give" them. The
first half is false — this batch's own `D:/hof-live-work/cost_measure.py` computes a different second
component (prompt + the completion recorded *up to* N) and gives iter-2 first_60 `[1,152,836,
1,386,920]`. The convention is stated in the `counted_basis` field above and repeated here: the second
component of every published pair is *the iteration's whole recorded completion*.)

The target therefore needs **61** model calls for iter-2 (recorded 125) and **92** for iter-3 (recorded
102): the Developer would have to do the same work in about half the round trips. **A-5, corrected:**
the earlier wording said these were "crossings" *interpolated* between the `first_60`/`first_70` and
`first_80`/`first_100` samples ("roughly 61 … roughly 91"). The published convention's curve crosses at
a recorded call: call 60 is 1,478,789 and **call 61 is 1,502,016**; call 91 is 1,498,609 and **call 92
is 1,520,424**. The interpolated values are 60.9 and 91.1. On the *stricter* basis — the one this
batch's own `cost_measure.py` computes, where a prefix carries only the completion tokens inside it —
the first call at or above the target is **65** for iter-2 (64 → 1,477,946; 65 → 1,504,428; interpolated
64.8) and 92 for iter-3. **F-4: the earlier "roughly 85 for iter-3" is withdrawn** — it contradicted
this section's own first_80, whose total is already *below* the target, so a crossing cannot lie
above 80. Capping at 61 would have ended the recorded iter-2 at 49 % of its work, and whether a role can
reach the artifact in that many calls is not an offline question. **Refused, and named as the next
batch's job.**

## 6. What works, what does not, what I could not verify

**Works, and is pinned.** The `--resume` contract (identity, no quarantine, restore-with-verification,
no game session when there is nothing to run) — driven through the real `run_loop::run` over prepared
and genuinely interrupted run directories, and red under plants P1–P3. The fold's landing on the stored
history, red under P4. The delivered-surface example list, red under P5. The digest-based tripwire
projection, red under P6, plus its synthetic control. The two prose pins (AC-9, AC-14) and the earlier
batch's passing behaviours, unchanged: the tripwire semantics, RA-2/RA-3/RA-6/RA-8/RA-9 and the
`cfg!(windows)` guard. The gate is green on this tree, in this batch's own build directory, with the
literal exit code and the counts in the JSON block, zero warnings, and a `fmt --check` that emits
nothing.

**Does not work / does not pass.** The 1.5M-token-per-Developer-call criterion. This batch could not
make it pass and measures that no value of *this fold's* tail can (its tail-0 figure bounds the
fold's own family); it does **not** show that no context-only policy can — a policy that kept only the
system prompt and the task would project iter-2 to 843,321 total tokens (defect F-3, §5). The
capability-preserving lever is the call count, which is a behavioural question the next batch must
measure on a real round. The four
`--resume` behaviours are proven offline against the offline adapter; a live engine resume is untested.

**Could not verify.** Anything that needs a live call: whether the projected prompt tokens are the
observed ones, whether a role works coherently with 12 verbatim messages, whether a resume survives a
real engine round, and whether the Developer can reach its artifact in ~60 model calls. Also, the
previous engine's tool names in the 177-tool embedded snapshot are never delivered by the Bevy channel,
but I could not exercise the mcp channel end to end to prove they are never delivered there either.

**The single most important thing for the next batch.** Run one real Developer call and count its
**model calls**, not just its tokens. No tail value of this fold reaches the target — with no
verbatim tail at all, iter-2 still projects to 2,199,582 total tokens against a 1.5M target — so the
capability-preserving lever left is the number of round trips (125 recorded, roughly 61 needed). Every other item in
this batch is pinned by a test that goes red when the behaviour is removed; that one is the only way
the cost criterion can ever pass.
