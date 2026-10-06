```json
{
 "schema": "hof-rs / bevy write-guaranteed exit: the mechanism, the tests, the policy and the projected cost",
 "produced_at": "2026-10-06",
 "branch": "bevy-core",
 "head_at_start": "3474cdd",
 "offline": true,
 "round_run": false,
 "model_call_made": false,
 "engine_started": false,
 "committed": false,
 "pushed": false,
 "criterion": {
  "tokens_per_developer_call": 1500000,
  "source": "config/hoh.yaml agent.artifact_write_budget_tokens",
  "step_limit": 150,
  "zero_context_floor_for_a_150_call_live_developer_call": 2077238,
  "source_of_the_floor": ".spec/bevy/SPIKE-COST-LEVERS.md lever-1 cap_zero_totals.livecost1-iter-1"
 },
 "mechanism_from_the_code": {
  "what_decides_a_role_call_is_finished": [
   "mini's inner environment raises the one legal self-exit as a flow interrupt: mini-swe-agent-rust-mini/rust/src/environments/local.rs:118-128 reads the first line of a command's output and, `if first_line.trim() == \"COMPLETE_TASK_AND_SUBMIT_FINAL_OUTPUT\" && output.returncode == 0`, returns `Err(FlowInterrupt::submitted(submission).into())`.  The marker is therefore read by the INNER environment's own inherent `check_finished`, called at local.rs:154 inside `LocalEnvironment::execute` - not by the wrapper this repository owns.",
   "the harness's own loop ends the call when the last message is an `exit` message: src/harness/compact.rs::run_compacting_agent iterates `agent.step()`, saves the trajectory, and breaks on `agent.messages.last().map(|message| message.role == \"exit\")`.  mini's exit statuses are `Submitted`, `LimitsExceeded`, `TimeExceeded`, `RepeatedFormatError` (lib.rs:204-213, agent.rs:161-173 and 495-499); the harness's own fail-fast statuses are the other way a call can end.",
   "so a Developer call was, until this batch, finished by exactly two kinds of event: the role running a command whose first output line is the marker (Submitted), or a budget/guard/mode failure (LimitsExceeded at the flat `step_limit`, TimeExceeded, RepeatedFormatError, or the guard's StepBudgetExceeded / ArtifactBudgetExceeded / RepeatedActionError).  Nothing in either path consulted the artifact."
  ],
  "what_counts_as_an_engineering_write": {
   "rule": "src/harness/guard.rs: `ArtifactKind::for_role(Role::Developer) == ArtifactKind::ProjectFile` and `ArtifactKind::counts(path) = !is_excluded_path(path)`; `is_excluded_path` is `[\"\\\\.hoh/\", \"\\\\.git/\", \"target/\", \".hoh/\", \".git/\"]` prefix matching, so `.hoh/scratch/**` is NOT an engineering write.",
   "where_it_is_set": "src/harness/guard.rs::execute_write: on a successful directive write, `if counts { state.artifact_written = true; state.successes.clear(); }` - the first counted write of the call, which is also the flag that raises the step budget and disarms the artifact-write budgets.",
   "what_it_is_not": "not the number of writes, not the agent's claim, and not the tree hash.  The round separately measures the tree (hash_tree before/after the Developer stage); the guard's flag is the only artifact measurement that exists INSIDE the call, which is why the exit gate uses it."
  },
  "the_no_artifact_guards_and_their_thresholds": [
   {
    "guard": "WriteGuardEnvironment::step_budget_exceeded (src/harness/guard.rs), the guard that cut the measured round",
    "quote": "if self.step_limit == 0 { return None; } self.step_counter.as_ref()?; let budget = self.effective_step_budget().min(self.step_limit); let steps = self.steps(); if steps > budget { Some(FailFast::StepBudget { steps, budget }) } else { None }",
    "threshold": "config/hoh.yaml: agent.step_limit: 150, agent.wrap_up_steps: 25, agent.steps_per_artifact: 8, and AgentLimits::effective_step_limit(has_written) = if has_written || steps_per_artifact == 0 { step_limit } else { (wrap_up_steps + max(step_limit / steps_per_artifact, 1)).max(wrap_up_steps) }",
    "arithmetic": "unwritten: 25 + max(150/8, 1) = 25 + 18 = 43 model calls; written: 150; enforced at `steps > budget`, so the 44th model call is billed and its actions refused - which is exactly the measured `StepBudgetExceeded` at 44 calls",
    "where_enforced": "src/harness/guard.rs::execute, at the top, before the action runs: `if let Some(fail_fast) = self.step_budget_exceeded() { return Err(AgentError::other(...)) }`"
   },
   {
    "guard": "WriteGuardEnvironment::budget_exceeded (wall clock on producing the artifact)",
    "quote": "let budget = self.artifact_budget?; let written = self.artifact_written(); if written { return None; } let elapsed = self.started.elapsed(); if elapsed >= budget { Some(FailFast::ArtifactBudget { .. }) }",
    "threshold": "config/hoh.yaml: agent.artifact_write_budget_seconds: 900 (15 minutes); 0 disables it"
   },
   {
    "guard": "per-action failure tripwire and the repeated-success tripwire",
    "quote": "record_failure: `let entry = state.failures.entry(command).or_insert(0); *entry += 1; if failures >= self.max_action_failures { .. }`; record_success: `if run.repeats < self.max_repeated_actions { return None; }`",
    "threshold": "config/hoh.yaml: agent.max_action_failures: 3, agent.max_repeated_actions: 15 (successes of one action with byte-identical results since the last counted write)"
   },
   {
    "guard": "mini's own budgets, which the guard does not override",
    "quote": "AgentConfig { step_limit: flat_step_limit, cost_limit, wall_time_limit_seconds, max_consecutive_format_errors } (src/harness/mini.rs)",
    "threshold": "config/hoh.yaml: agent.step_limit: 150 (flat ceiling), agent.wall_time_limit_seconds: 3600, agent.max_consecutive_format_errors: 3, agent.cost_limit: 0.0 (disabled)"
   },
   {
    "guard": "the runtime's token half of the same budget (measured after the attempt, not inside the environment)",
    "quote": "src/runtime/write_failure.rs::assess: `if token_budget > 0 { if let Some(tokens) = total_tokens.filter(|tokens| *tokens >= token_budget) { return Some(RoleWriteFailure { .. }) } }`; and `is_failure_status` accepts `LimitsExceeded | TimeExceeded | RepeatedFormatError | RepeatedActionError | ArtifactBudgetExceeded | StepBudgetExceeded`",
    "threshold": "config/hoh.yaml: agent.artifact_write_budget_tokens: 1500000 - the criterion itself"
   }
  ],
  "what_a_round_does_with_a_call_that_produced_no_artifact": {
   "measurement": "src/runtime/run_loop.rs brackets the whole Developer stage with `hash_tree(&workspace, &excludes)` (`h_dev_before` / `h_dev_after`), with `.hoh/**` hash-excluded, so equality means not one byte of the project changed because of the stage",
   "quote": "`if h_dev_before == h_dev_after { let warning = ContractViolation::NoProgress.code(); iter_warnings.push(warning.to_string()); .. }` then `if h_dev_before == h_dev_after { let violation = ContractViolation::NoEngineeringWrite; .. finalize_failure(&run_dir, iteration, Role::Developer, \"contract_violation\", ..); return Err(HofError::contract(violation).into()); }`",
   "observed": "recorded in runs/completion1/iter-3/result.json as ok=false, failed_role=\"developer\", reason=\"contract_violation\", warnings [harness_source_read, no_progress, role_write_failure: developer attempt 1 ended `StepBudgetExceeded` without writing ..., no_engineering_write]; `hoh run` exits 2 with `hoh: contract violation: NoEngineeringWrite (no_engineering_write)`",
   "consequence_for_this_batch": "the guard is NOT weakened: a Developer stage that changed nothing still fails the round.  What this batch adds is that such a call can no longer END cleanly by the role's own request - the request is refused and the call continues."
  },
  "where_the_new_gate_sits": {
   "site": "src/harness/guard.rs::WriteGuardEnvironment::execute, the first place in this repository that sees the completion interrupt",
   "why_not_the_command_text": "the marker is read by the inner environment's own `check_finished`, so the guard cannot see the output that carried it; matching the command's text would miss `type <a file holding the marker>`, a batch file, or a PowerShell `Write-Output`, i.e. every route other than the documented `echo`",
   "why_not_the_loop": "workable and complete, but it needs the artifact flag shared from the guard into `run_compacting_agent` plus a hand-built, shape-correct tool observation for the refused action (the interrupt aborts mini's action loop before observations are appended, so popping the exit message would leave a dangling tool_call)",
   "why_not_the_round": "a repair call doubles the cost the criterion is about and duplicates the existing DR-24/DR-37 wrap-up retry; and the round-level NoEngineeringWrite gate must stay"
  }
 },
 "recordings": {
  "source": "evidence/cost/*.developer.attempt1.json (read-only, byte-unchanged)",
  "write_event_detector": "a tool observation carrying extra.hoh_write_path (the guard's own record of a write it performed), returncode 0 - the same measurement ArtifactKind::counts makes, not a re-implemented regex",
  "declared_finish_detector": "a message carrying extra.interrupt_type == \"FormatError\" (the pre-fix declaration was a prose-only reply that was rejected), attributed to the model call whose response it rejected",
  "projection_method": "the prefix sum of the recording's own per-call usage.total_tokens over calls 1..N, i.e. the recording's exact measured cost had the call ended at call N.  Cross-check: for round4-iter-1 the sum of prompt tokens over calls 1..24 re-derives the RETRY-FIX-REPORT's independent figure 2,544,563 - 1,964,960 = 579,603 exactly.",
  "per_recording": [
   {
    "recording": "round4-iter-1.developer.attempt1.json",
    "label": "round-4 iteration 1, pre-completion-fix prompt",
    "model_calls": 69,
    "measured_prompt_tokens": 2544563,
    "measured_total_tokens": 2626195,
    "measured_ratio_to_the_criterion": 1.7508,
    "successful_write_events": 6,
    "project_write_events": 6,
    "scratch_write_events": 0,
    "first_project_write_call": 7,
    "project_write_calls": [
     7,
     8,
     9,
     13,
     14,
     18
    ],
    "retry_turn_calls": [
     25,
     27,
     32,
     33,
     35,
     37,
     38,
     41,
     46,
     48,
     50,
     52,
     53,
     56,
     58,
     59,
     61,
     62,
     66,
     67
    ],
    "first_declared_finish_call": 25,
    "first_legitimate_exit_call": 25,
    "projected_calls": 25,
    "projected_prompt_tokens": 618610,
    "projected_total_tokens": 665666,
    "projected_ratio_to_the_criterion": 0.4438,
    "projected_meets_the_criterion": true
   },
   {
    "recording": "round4-iter-2.developer.attempt1.json",
    "label": "round-4 iteration 2, pre-completion-fix prompt",
    "model_calls": 125,
    "measured_prompt_tokens": 12765478,
    "measured_total_tokens": 13091431,
    "measured_ratio_to_the_criterion": 8.7276,
    "successful_write_events": 23,
    "project_write_events": 11,
    "scratch_write_events": 12,
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
    "retry_turn_calls": [
     58,
     85,
     87,
     91,
     92,
     95,
     115,
     120,
     122,
     123
    ],
    "first_declared_finish_call": 58,
    "first_legitimate_exit_call": 58,
    "projected_calls": 58,
    "projected_prompt_tokens": 3065944,
    "projected_total_tokens": 3295369,
    "projected_ratio_to_the_criterion": 2.1969,
    "projected_meets_the_criterion": false
   },
   {
    "recording": "round4-iter-3.developer.attempt1.json",
    "label": "round-4 iteration 3, pre-completion-fix prompt",
    "model_calls": 102,
    "measured_prompt_tokens": 5137090,
    "measured_total_tokens": 5223211,
    "measured_ratio_to_the_criterion": 3.4821,
    "successful_write_events": 11,
    "project_write_events": 1,
    "scratch_write_events": 10,
    "first_project_write_call": 6,
    "project_write_calls": [
     6
    ],
    "retry_turn_calls": [
     30,
     47,
     49,
     56,
     58,
     61,
     64,
     66
    ],
    "first_declared_finish_call": 30,
    "first_legitimate_exit_call": 30,
    "projected_calls": 30,
    "projected_prompt_tokens": 1124831,
    "projected_total_tokens": 1160900,
    "projected_ratio_to_the_criterion": 0.7739,
    "projected_meets_the_criterion": true
   },
   {
    "recording": "livecost1-iter-1.developer.attempt1.json",
    "label": "livecost1 iteration 1, the live recording",
    "model_calls": 150,
    "measured_prompt_tokens": 3537843,
    "measured_total_tokens": 3651120,
    "measured_ratio_to_the_criterion": 2.4341,
    "successful_write_events": 5,
    "project_write_events": 4,
    "scratch_write_events": 1,
    "first_project_write_call": 6,
    "project_write_calls": [
     6,
     14,
     19,
     43
    ],
    "retry_turn_calls": [],
    "first_declared_finish_call": null,
    "first_legitimate_exit_call": null,
    "projected_calls": null,
    "projected_prompt_tokens": null,
    "projected_total_tokens": null,
    "projected_ratio_to_the_criterion": null,
    "projected_meets_the_criterion": false
   }
  ],
  "max_call_count_whose_prefix_stays_under_the_criterion": {
   "livecost1-iter-1.developer.attempt1.json": 81,
   "round4-iter-1.developer.attempt1.json": 44,
   "round4-iter-2.developer.attempt1.json": 40,
   "round4-iter-3.developer.attempt1.json": 36
  },
  "live_post_fix_calls": {
   "source": "runs/completion1/iter-*/traj/developer.attempt1.json (read out, never written to)",
   "why_they_are_here": "they are the only post-completion-fix live Developer calls, and they show the other half of the problem: the artifact existed early but the role never asked to exit",
   "calls": [
    {
     "trajectory": "runs/completion1/iter-1/traj/developer.attempt1.json",
     "model_calls": 150,
     "total_tokens": 3527566,
     "ratio_to_the_criterion": 2.3517,
     "project_write_events": 3,
     "first_project_write_call": 8,
     "completion_command_calls": [],
     "asked_to_exit_at_any_point": false,
     "first_legitimate_exit_call": null,
     "recorded_exit_status": "LimitsExceeded"
    },
    {
     "trajectory": "runs/completion1/iter-2/traj/developer.attempt1.json",
     "model_calls": 150,
     "total_tokens": 3939027,
     "ratio_to_the_criterion": 2.626,
     "project_write_events": 2,
     "first_project_write_call": 13,
     "completion_command_calls": [],
     "asked_to_exit_at_any_point": false,
     "first_legitimate_exit_call": null,
     "recorded_exit_status": "LimitsExceeded"
    },
    {
     "trajectory": "runs/completion1/iter-3/traj/developer.attempt1.json",
     "model_calls": 44,
     "total_tokens": 803027,
     "ratio_to_the_criterion": 0.5354,
     "project_write_events": 0,
     "first_project_write_call": null,
     "completion_command_calls": [],
     "asked_to_exit_at_any_point": false,
     "first_legitimate_exit_call": null,
     "recorded_exit_status": "StepBudgetExceeded"
    }
   ]
  },
  "gate_alone_changes_none_of_these_numbers": {
   "statement": "the write-guaranteed exit is a PERMISSION and a GUARANTEE, not a saving.  It refuses an exit that lacks the write; it does not make a role ask to exit.  In every recording and every live call the role's first declared finish (if any) already followed its first project write, so this change would have refused nothing in the measured corpus: 0 refusals projected.",
   "what_actually_produces_the_saving": "a bound on the call count.  The numbers above are the size of that bound's prize, and the refusals this batch adds are what make the bound safe.",
   "the_bounds_already_in_place_today": "the unwritten step budget (43 model calls) and the 900 s artifact-write budget; both fire only while the artifact is missing, and both are failures rather than clean ends."
  }
 },
 "tests": {
  "new_files": [
   "tests/write_guaranteed_exit.rs (6 tests, the production path: DefaultAgent + run_compacting_agent + WriteGuardEnvironment + a real LocalEnvironment/cmd.exe)",
   "src/harness/guard.rs #[cfg(test)] (5 tests, the guard alone with a fake inner environment)"
  ],
  "existing_tests_removed_or_weakened": [],
  "red": [
   {
    "command": "cargo test --offline --test write_guaranteed_exit",
    "literal_exit_code": 101,
    "summary": "4 passed; 2 failed; 0 ignored; 0 measured; 0 filtered out",
    "failures": [
     "a_completion_request_without_the_engineering_write_is_refused_and_the_call_continues: panicked at tests\\\\write_guaranteed_exit.rs:328:5 (line numbers as recorded on the red run, before the formatting pass): assertion `left == right` failed: the refused completion must not have ended the call (steps = 1) -- left: 1, right: 3",
     "a_scratch_write_is_not_an_engineering_write: panicked at tests\\\\write_guaranteed_exit.rs:381:5 (before the formatting pass): assertion `left == right` failed: the scratch write must not satisfy the exit gate (steps = 2) -- left: 2, right: 4"
    ],
    "confirmed_reason": "both failures are the claimed assertion, not a compile or setup error: the same invocation compiled and ran four other tests green in the same command, and the two red tests passed after the implementation"
   },
   {
    "command": "cargo test --offline --lib harness::guard::tests",
    "literal_exit_code": 101,
    "summary": "26 passed; 2 failed; 0 ignored; 0 measured; 417 filtered out",
    "failures": [
     "a_completion_request_without_the_artifact_is_refused_not_ended: panicked at src/harness/guard.rs:2095:10 (before the formatting pass): the guard refuses the completion instead of raising the interrupt: Interrupt(FlowInterrupt { kind: Submitted, messages: [Message { role: \"exit\", content: String(\"done\"), extra: Some({\"exit_status\": String(\"Submitted\"), \"submission\": String(\"done\")}), fields: {} }] })",
     "a_scratch_write_does_not_earn_the_completion: panicked at src/harness/guard.rs:2165:18 (before the formatting pass): a scratch write is not the declared artifact: Interrupt(FlowInterrupt { kind: Submitted, .. })"
    ],
    "confirmed_reason": "the literal panic shows what the un-repaired guard did with the claim: it propagated the Submitted interrupt, i.e. the call ended exactly as the measured round's iteration 3 did"
   }
  ],
  "green": [
   {
    "command": "cargo test --offline --test write_guaranteed_exit",
    "literal_exit_code": 0,
    "summary": "6 passed; 0 failed; 0 ignored; 0 measured; 0 filtered out"
   },
   {
    "command": "cargo test --offline --lib harness::guard::tests",
    "literal_exit_code": 0,
    "summary": "29 passed; 0 failed; 0 ignored; 0 measured; 417 filtered out"
   }
  ],
  "added_after_green": [
   "the_gate_refuses_every_route_to_the_completion_interrupt (src/harness/guard.rs): the guard is handed an inner environment that raises the interrupt for ANY command, so the completeness claim (the gate keys on the interrupt, not on the command's text) is pinned rather than argued.  It was written after the implementation; the red for its claim is the first guard failure above, whose literal payload is the same `Interrupt(FlowInterrupt { kind: Submitted, .. })` that a text-matching guard would have let through."
  ]
 },
 "change": {
  "kind": "add a positive condition at the one place a role's own exit is decidable; no negative guard is touched",
  "files": [
   "src/harness/guard.rs: module doc says four jobs; `pub const COMPLETION_MARKER` and `pub const COMPLETION_REFUSED_KEY = \"hoh_exit_refused\"`; `pub fn completion_refusal_text(declared_artifact: &str) -> String`; `ArtifactKind::gates_completion()` and `ArtifactKind::declared_artifact()`; `WriteGuardEnvironment::completion_allowed()`, `is_completion_request()`, `completion_refusal()`; and the `execute` branch that catches `Err(AgentError::Interrupt(interrupt))` for `InterruptKind::Submitted` when the gate says no",
   "tests/write_guaranteed_exit.rs: new"
  ],
  "diffstat": "src/harness/guard.rs 391 insertions, 2 deletions (the two deletions are the module-doc line 'Three jobs' -> 'Four jobs' and the `self.inner.execute(..).await?;` line the match replaced); tests/write_guaranteed_exit.rs new; no other tracked file changed",
  "not_changed": "run_loop.rs, write_failure.rs, compact.rs, mini.rs, cap.rs, all of src/prompts/**, config/hoh.yaml, the external mini-swe-agent crate, evidence/**, runs/**, the registry, the battery, the liveness step and .gitattributes"
 },
 "policy": {
  "permit": "a call may end at the role's own completion request (`InterruptKind::Submitted`) exactly when the call has already written the artifact it declares - for `ArtifactKind::ProjectFile` (the Developer) a successful directive write to a path outside `.hoh/**`, `.git/**`, `target/**`.  The earliest legitimate exit is therefore the first completion request after the first counted write, and nothing else is required: no minimum call count, no confirmation, no extra turn.",
  "guarantee": "every other way a call can end is a failure status the runtime already treats as one (`LimitsExceeded`, `TimeExceeded`, `RepeatedFormatError`, `StepBudgetExceeded`, `ArtifactBudgetExceeded`, `RepeatedActionError`).  `is_failure_status` accepts all of them, `write_failure::assess` turns a no-artifact end into a `RoleWriteFailure`, and the round turns an unchanged Developer tree into `NoEngineeringWrite` (exit 2).  A call therefore cannot end SUCCESSFULLY without the write, and a call that cannot write is still bounded and still fails loudly - which is the existing contract, untouched.",
  "when_the_role_asks_to_exit_without_one": "refusing the exit and continuing in the same call: the completion request is answered with an ordinary tool observation (returncode 1, `extra.hoh_exit_refused = true`) that says the request was refused, names the missing artifact in the runtime's own words, and repeats the write directive and the completion command.  The role keeps the call, the same history and the same budget; the refusal costs one model call.  The allowance is bounded by the guards that were already there: the unwritten step budget (43 model calls) and the 900 s artifact-write budget end the call if the role never writes, and either end is a failure the round records.",
  "why_refuse_and_continue": "compared with the alternatives: it is the cheapest (no extra call, no attempt bookkeeping, no second Developer round), it keeps the call's own history and budget so the role can still finish, and it is the only option that makes an EMPTY end impossible rather than merely detectable.  A bounded number of allowances would add a number the recorded corpus cannot calibrate (the recorded refusal count is 0); one targeted repair call would double the cost the criterion is about; refusing without instructing would leave the role to guess."
 },
 "alternatives_rejected": [
  {
   "option": "match the completion command's text in the guard",
   "rejected_because": "the marker is read by the inner environment's own `check_finished`, so a text match misses every route other than the documented `echo` (`type` of a file holding the marker, a batch file, PowerShell `Write-Output`).  The selected rule keys on the interrupt itself and therefore covers all of them; this is pinned by the_gate_refuses_every_route_to_the_completion_interrupt."
  },
  {
   "option": "gate the exit in run_compacting_agent (the loop)",
   "rejected_because": "complete but larger: it needs the artifact flag shared from the guard into the loop and a hand-built tool observation for the refused action (the interrupt aborts mini's action loop before observations are appended), with no guarantee the guard-level rule does not already give."
  },
  {
   "option": "one targeted repair call at the round level for a Developer stage that wrote nothing",
   "rejected_because": "it doubles the cost the criterion measures and duplicates the existing DR-24/DR-37 wrap-up retry; and the round-level NoEngineeringWrite gate must keep deciding the round, not be softened."
  },
  {
   "option": "state the rule in the prompt (a sentence in COMPLETION_PROTOCOL)",
   "rejected_because": "measurable arithmetic: all three recorded declared finishes already followed a project write (calls 25/58/30 vs first writes 7/33/6), so the expected refusal count per call is about 0; the sentence costs about 120 bytes of every prompt (about 4.6 k prompt tokens over a 150-call context, about 0.31 % of the criterion) while one refused call costs about 20 k tokens - it would need four or more refusals per call to pay for itself.  The refusal text teaches the rule at the moment it matters."
  },
  {
   "option": "arm the gate for every role",
   "rejected_because": "the Planner's and Tester's declared artifacts live under `.hoh/**` and are counted as `ArtifactKind::AnyFile`, so the gate would be satisfiable by any write at all; arming it would change two roles the measurement never implicated.  The gate takes its scope from the artifact kind - the same quantity the round's NoEngineeringWrite gate measures."
  },
  {
   "option": "leave the completion request alone and bound the call count only",
   "rejected_because": "that is the measured failure mode: the only sub-criterion Developer call in the live round was under the bar because it was cut off with nothing written (44 calls, 803,027 tokens, NoEngineeringWrite, exit 2).  A bound without this condition can be satisfied by cutting the write."
  }
 ],
 "gate": {
  "build_dir": "E:/wge-target (this batch's own; the repository's own target/ was not used)",
  "baseline_on_the_untouched_tree_same_build_dir": {
   "command": "cargo test --offline",
   "literal_exit_code": 0,
   "passed": 802,
   "failed": 0,
   "ignored": 6,
   "listed": 808,
   "test_result_lines": 60,
   "compiler_warning_lines": 0
  },
  "command": "cargo test --offline",
  "literal_exit_code": 0,
  "passed": 813,
  "failed": 0,
  "ignored": 6,
  "test_result_lines": 61,
  "compiler_warning_lines": 0,
  "error_lines": 0,
  "delta": "exactly the 11 new tests: 802 -> 813 passed, 808 -> 819 listed (5 guard unit tests + 6 integration tests); nothing removed or weakened",
  "list_command": "cargo test --offline -- --list",
  "list_exit_code": 0,
  "list_count": 819,
  "list_ignored_command": "cargo test --offline -- --list --ignored",
  "list_ignored_exit_code": 0,
  "list_ignored_count": 6,
  "fmt_command": "cargo fmt --all --check",
  "fmt_literal_exit_code": 0,
  "fmt_output_bytes": 0,
  "reruns": "four full runs, every one exit 0 with 0 failures and identical counts where comparable: the untouched-tree baseline (802/0/6/808), the change plus its new tests (813/0/6, 819 listed), one after this report and DECISIONS.md D315 were on disk (813/0/6), and one after this report's final prose edit (813/0/6).  No timing-sensitive test failed in any run, so no re-run needed reporting.",
  "existing_test_whose_behaviour_changed": "tests/harness_cap_wiring.rs::the_harness_itself_bounds_what_the_next_request_carries runs MiniHarness with Role::Developer and a scripted endpoint whose second and later responses are `echo COMPLETE_TASK_AND_SUBMIT_FINAL_OUTPUT` while the role never writes a project file, so its completion requests are now refused and the call ends on mini's flat `step_limit: 4` instead of `Submitted`.  It is green (its assertions are on the second request's body and on `outcome.role`), and it was not modified.",
  "rerun_after_this_report_and_decisions_md_were_written": {
   "when": "after this report and the appended DECISIONS.md entry D315 existed on disk",
   "command": "cargo test --offline",
   "literal_exit_code": 0,
   "passed": 813,
   "failed": 0,
   "ignored": 6,
   "test_result_lines": 61,
   "compiler_warning_lines": 0,
   "identical_counts_to_the_run_above": true
  },
  "final_run_after_the_last_write": {
   "when": "after the last write to the repository other than this report's own prose (the change, the new test file, DECISIONS.md D315 and this report all on disk)",
   "command": "cargo test --offline",
   "literal_exit_code": 0,
   "passed": 813,
   "failed": 0,
   "ignored": 6,
   "test_result_lines": 61,
   "compiler_warning_lines": 0,
   "identical_counts_to_every_run_above": true
  }
 },
 "disk": {
  "free_before_build": "F: 8.3 G available (100% used); E: 549 G available",
  "build_dir_size_after_the_gate": "E:/wge-target 9.3 G",
  "free_after_the_gate": "F: 8.3 G available; E: 540 G available",
  "deletions": "none - no file was deleted and no rm -rf or wildcard deletion was used",
  "wrote_to_the_repository": [
   "src/harness/guard.rs (the change)",
   "tests/write_guaranteed_exit.rs (new)",
   "DECISIONS.md (appended, D315)",
   ".spec/bevy/WRITE-GUARANTEED-EXIT-REPORT.md (this report)"
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
  "helper_scripts_location": "E:/wge/ (outside the repository; every script landed through a file write, never through multi-line Python on a shell command line)",
  "one_test_process_at_a_time": true,
  "free_disk_checked_before_building": true
 },
 "measured_vs_inferred": {
  "measured": [
   "every guard threshold and quote above is read out of the working tree at head 3474cdd (src/harness/guard.rs, src/config.rs, src/runtime/run_loop.rs, src/runtime/write_failure.rs) and config/hoh.yaml",
   "every recorded per-call figure is the recording's own usage block; write events are the guard's own extra.hoh_write_path observations; declared finishes are the recorded FormatError turns",
   "the red and green literal exit codes and summaries are the runs quoted above, in this batch's own build directory",
   "the gate numbers are the two runs quoted above (baseline and after), with --list and --list --ignored and fmt"
  ],
  "inferred": [
   "that the recorded roles would have run the documented `echo` command at their first declared finish.  The recordings show the declaration, not the post-fix behaviour, so the projections hold the recorded call sequence fixed - the same limitation every offline figure in this repository carries.  Only a live round can measure the tail.",
   "that the existing cap-wiring test now ends on mini's flat limit rather than Submitted: it is green and its own scripted Developer writes nothing, which by the mechanism above means its completion requests are refused; the test does not print an exit status, so this is an inference from the mechanism, not a read-out.",
   "that the gate would have refused nothing in the recorded corpus: the counting is measured (first write before first declared finish in all three), but the counterfactual behaviour of the model when refused is not."
  ]
 },
 "single_most_important_thing": "This batch does not save a single token on its own: it refuses an exit that lacks the engineering write, and in every recording and every live call the first declared finish already followed the first project write (7/33/6 vs 25/58/30; live: never declared at all), so the projected refusal count is 0.  What it does is make the saving possible: the criterion is arithmetically unreachable at 150 calls (2,077,238-token floor) so the next batch must bound the call count, and the bound that meets the criterion is 36-81 calls depending on the recording - a bound that would have cut two of the four recorded calls before their first project write (round4-iter-2 wrote at call 33; the live calls wrote at 8 and 13) and would have reproduced iteration 3's cheap empty round.  The next batch should therefore lower the POST-write budget (the step budget after `artifact_written`, or the flat `step_limit` once the write exists) and pair it with this gate, and it must be measured live: the projected cost at the recorded first legitimate exit points is 665,666 / 3,295,369 / 1,160,900 tokens for round4-iter-1/2/3 (0.44x / 2.20x / 0.77x the criterion), i.e. even the recorded exit points are not enough on their own for iteration 2."
}
```

# WRITE-GUARANTEED-EXIT-REPORT - a call may end at its own completion request only once its engineering write exists

The machine-readable block above is `json.dumps(..., indent=1, ensure_ascii=False)` output written by
`E:/wge/write_report.py` and then **parsed back out of this written file**; the parse is the last thing
the generator does and it fails if the block does not round-trip.  Every helper script lives outside the
repository at `E:/wge/`.  **No round was run, no model call was made, no engine was started.**  Nothing
under `evidence/**`, `runs/**`, `config/**`, the registry, the battery, the liveness step,
`.gitattributes` or any frozen document was touched; `DECISIONS.md` was appended to (D315) and nothing
was committed or pushed.

## 1. The mechanism, established from the code and the recordings

**What decides that a Developer call is finished.**  There is one legal self-exit, and it is raised by
mini's *inner* environment, not by any wrapper this repository owns:
`mini-swe-agent-rust-mini/rust/src/environments/local.rs:118-128` reads the first line of a command's
output and, when it is `COMPLETE_TASK_AND_SUBMIT_FINAL_OUTPUT` and the exit code is 0, returns
`Err(FlowInterrupt::submitted(...))`.  Our loop (`src/harness/compact.rs::run_compacting_agent`) ends the
call when the last message has role `exit`.  Until this batch, **nothing in either path consulted the
artifact**: a Developer could run the marker command having written nothing, and the call ended
`Submitted` with an empty increment.  The other endings are `LimitsExceeded` (mini's flat `step_limit`),
`TimeExceeded`, `RepeatedFormatError`, and the guard's own `StepBudgetExceeded`,
`ArtifactBudgetExceeded` and `RepeatedActionError`.

**What counts as an engineering write.**  `ArtifactKind::ProjectFile` plus
`counts(path) = !is_excluded_path(path)`, where `is_excluded_path` prefix-matches `.hoh/`, `.git/` and
`target/`.  A successful write directive to a counted path sets `state.artifact_written = true` - the
first such write, and the same flag that raises the step budget and disarms the artifact budgets.  A
`.hoh/scratch/**` write is *not* an engineering write, which is why the tests pin that case separately.

**The guards and their thresholds.**  The one that cut the measured round is the unwritten step budget:
with `step_limit: 150`, `wrap_up_steps: 25` and `steps_per_artifact: 8`,
`effective_step_limit(has_written = false) = 25 + max(150/8, 1) = 43`, enforced in
`WriteGuardEnvironment::execute` as `steps > budget` - so the 44th model call is billed and its actions
refused, which is exactly the recorded `StepBudgetExceeded` at 44 calls.  Beside it:
`artifact_write_budget_seconds: 900`, `max_action_failures: 3`, `max_repeated_actions: 15`,
mini's `step_limit: 150` / `wall_time_limit_seconds: 3600` / `max_consecutive_format_errors: 3`, and the
runtime's `artifact_write_budget_tokens: 1500000` (the criterion) in `write_failure::assess`.

**What a round does with a call that produced no artifact.**  `run_loop.rs` hashes the project before and
after the whole Developer stage with `.hoh/**` excluded.  Equality pushes `no_progress`, records the
`role_write_failure`, pushes `no_engineering_write`, calls `finalize_failure(..., "contract_violation")`
and returns `HofError::contract(NoEngineeringWrite)` - the literal exit 2 and
`hoh: contract violation: NoEngineeringWrite (no_engineering_write)` that `runs/completion1` recorded.

**When the recorded calls first held a valid artifact - the number this design lives on.**  From the
guard's own `hoh_write_path` observations: `round4-iter-1` wrote `src/game.rs` at call **7**,
`round4-iter-2` at call **33**, `round4-iter-3` at call **6**, `livecost1-iter-1` at call **6**.  Their
first *declared* finishes were calls **25 / 58 / 30** and (livecost1) never; so in all three recordings
the declaration came after the write.  That is the design's licence to refuse an early exit without a
write, and it is also why this change refuses nothing in the recorded corpus.

## 2. The tests, red then green

Red, with the literal exit codes and messages: `cargo test --offline --test
write_guaranteed_exit` exits **101** with `4 passed; 2 failed`, both failures being the claimed
assertion - the refused-completion test failed because the call *did* end (steps = 1 instead of 3), and
the scratch test for the same reason (steps = 2 instead of 4).  `cargo test --offline --lib
harness::guard::tests` exits **101** with `26 passed; 2 failed`, and the panic payload is the honest
evidence: with no gate the guard propagated `Interrupt(FlowInterrupt { kind: Submitted, .. })`, i.e. the
call ended exactly as the measured iteration 3 did.  Green: the same two commands exit **0** with
`6 passed` and `29 passed`.  No existing test was removed or weakened.

The integration file drives the production path end to end: a real `DefaultAgent`, the real
`run_compacting_agent`, the real `WriteGuardEnvironment`, and a **real** `LocalEnvironment` (`cmd.exe`) -
the only thing that raises the `Submitted` interrupt, so the gate is proved against the real mechanism
rather than against a fake.  The five guard unit tests cover the rule at its own boundary, including one
added after green that hands the guard an inner environment raising the interrupt for *any* command: that
is what makes the guarantee complete rather than a spelling check.

## 3. The policy, and why not the alternatives

**Permit.**  A call may end at the role's own completion request exactly when the call has already
written the artifact it declares.  The earliest legitimate exit is the first completion request after the
first counted write; nothing else is required.

**Refuse and continue, in the same call.**  A completion request without the write is answered with an
ordinary tool observation (returncode 1, `extra.hoh_exit_refused = true`) that says the request was
refused, names the missing artifact in the runtime's own words, and repeats the write directive and the
completion command.  The role keeps the call, the history and the budget.  The allowance is bounded by
guards that already existed - the 43-call unwritten step budget and the 900 s artifact-write budget -
both of which end the call as *failures* the round records, so the round-level guarantee is unchanged.

**Guarantee.**  Every other ending is a failure status: `is_failure_status` accepts them all,
`write_failure::assess` turns a no-artifact end into a `RoleWriteFailure`, and an unchanged Developer
tree is still `NoEngineeringWrite` (exit 2).  A call cannot end *successfully* without the write; it just
cannot end *cheaply and emptily* either.

**Rejected**: matching the command's text (misses `type`, batch files, PowerShell - and the marker is
read by the inner environment, not by us); the loop-level gate (complete but needs cross-layer state and
a hand-built tool observation); a round-level repair call (doubles the cost the criterion measures);
a prompt sentence (all three recorded declarations already followed a write, so the expected refusal
count is 0, and the sentence would cost about 4.6 k prompt tokens over a 150-call context against about
20 k for one refused call); arming the gate for every role (the Planner's and Tester's artifacts are
`.hoh/**` and would be satisfied by any write); and bounding the calls without this condition (which is
the measured iteration-3 failure).

## 4. The projected effect, and what still needs a live round

Had each recorded call ended at its first legitimate exit point, its cost would have been the prefix sum
of its own measured usage:

| recording | measured total | first write | declared finish | first legitimate exit | projected total | projected ratio | meets criterion |
|---|---|---|---|---|---|---|---|
| round4-iter-1 | 2,626,195 (1.75x) | call 7 | call 25 | call 25 | **665,666** | 0.44x | yes |
| round4-iter-2 | 13,091,431 (8.73x) | call 33 | call 58 | call 58 | **3,295,369** | 2.20x | no |
| round4-iter-3 | 5,223,211 (3.48x) | call 6 | call 30 | call 30 | **1,160,900** | 0.77x | yes |
| livecost1-iter-1 | 3,651,120 (2.43x) | call 6 | never | none | 3,651,120 | 2.43x | no |

The cross-check is that the same method re-derives the previous batch's independent figure exactly
(prompt tokens over calls 1..24 of round4-iter-1 = 579,603 = 2,544,563 - 1,964,960).  The two live
post-fix calls are worse news and the honest headline: `runs/completion1` iterations 1 and 2 wrote at
calls **8** and **13** and then spent all 150 calls without ever running the completion command, and
iteration 3 never wrote at all.  **This change therefore saves nothing on its own** - it would have
refused nothing in the corpus - and the saving depends entirely on the bound the next batch must set.
That bound is not generous: the largest call count whose prefix stays under the criterion is 44 / 40 / 36
for round4-iter-1/2/3 and 81 for livecost1, and 78 / 74 for the two live producing calls.  Any such bound
would have cut two of the four recorded calls before their first write.

## 5. The gate, the disk and the constraints

`cargo test --offline` in this batch's own build directory `E:/wge-target` (E: had 549 G free; F: had
8.3 G and was 100 % full, so nothing was built on F:): literal exit code **0**, **813 passed / 0 failed /
6 ignored** over 61 `test result:` lines, **0 compiler warning lines**.  `--list` returns **819**,
`--list --ignored` returns **6**, `cargo fmt --all --check` exits **0** with 0 bytes of output.  The
untouched-tree baseline in the same directory is **802 / 0 / 6 / 808**, so the delta is exactly the 11 new
tests (5 guard unit + 6 integration).  The only tracked file changed is `src/harness/guard.rs`
(391 insertions, 2 deletions); `tests/write_guaranteed_exit.rs` is new.

The gate was run four times in total, all exit 0 with 0 failures: the untouched-tree baseline
(802 / 0 / 6 / 808), the change with its new tests (813 / 0 / 6, 819 listed), and once more after this
report and `DECISIONS.md` D315 existed on disk - 813 / 0 / 6, byte-identical counts, because the new
`.spec` document is visible to the tests that read `.spec/**` and nothing changed; and once more after this
report's final prose edit, again 813 / 0 / 6.  No timing-sensitive
test failed in any of the three runs, so no re-run needed reporting.

Nothing was deleted (no `rm -rf`, no wildcard deletion, no deletion at all).  Nothing under `evidence/**`,
`runs/**`, `config/**`, the registry, the battery, the liveness step, `.gitattributes` or any frozen
document was written.  `DECISIONS.md` was appended to only (D315), and the append was verified byte for
byte: the prefix hash before and after is identical and the file grew by exactly the entry's length.
Nothing was committed and nothing was pushed.

## 6. What I could not verify, and the single most important thing

I could not verify any of it live.  The projections hold the recorded call sequence fixed and assume the
role would have run the documented command at the moment it declared itself finished; the recordings show
the declaration, not post-fix behaviour, and the two live post-fix calls declared nothing at all.  I
could not measure the base rate of refusals because the corpus contains none.  And one existing test's
behaviour changed without its assertions changing: `tests/harness_cap_wiring.rs::the_harness_itself_bounds_what_the_next_request_carries`
runs a Developer that writes nothing and completes by command, so it now ends on mini's flat `step_limit`
rather than `Submitted` - it is green, and its assertions are on the second request's body and on the
role, but the new ending is an inference from the mechanism rather than a printed exit status.

**The single most important thing for the next batch:** the early self-exit and a call bound are one
lever, and this batch supplied only the guarantee half.  Bound the calls *after* the write - lower the
post-`artifact_written` step budget (or the flat limit once the write exists) rather than the unwritten
43-call gate - and measure it live, because the recorded exit points alone are not enough for iteration 2
(3,295,369 tokens, 2.20x) and the live calls never took the exit at all.
