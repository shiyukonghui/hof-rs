```json
{
 "schema": "hof-rs / independent acceptance of the write-guaranteed exit (a call may end at its own completion request only once its engineering write exists)",
 "artifact_under_review": ".spec/bevy/WRITE-GUARANTEED-EXIT-REPORT.md",
 "reviewed_commit": "6be54ea (the report was written against 3474cdd, where the change is absent; the tree under review is the commit containing it)",
 "review_kind": "independent; re-derived from src/**, tests/**, config/hoh.yaml, the external mini-swe-agent crate, evidence/cost/**, runs/completion1/** and a reconstructed pre-change worktree outside the repository. No round, no model call, no engine, no network.",
 "verdict": "pass",
 "headline": "The mechanism, the guarantee and the gate all hold: a Developer call can no longer end at its own completion request before its counted engineering write exists, the refusal is an ordinary observation that keeps the call alive in the same history, an exit after the write is raised unchanged, every budget and every negative guard is untouched, and a round that writes nothing still fails. The claimed red state is genuine (I reproduced it against a pre-change tree) and the green state runs the real LocalEnvironment behind the real guard and loop. The 'saves nothing on its own' conclusion is correct and exactly reproduced. The one thing that does not hold is a forward-looking sentence in the report's next-step section: the warning that a bound in the 36-81 range would have cut two of the four recorded calls before their first write is not reproducible - a flat bound in that range cuts all of them after their write, and only round4-iter-2 is reachable pre-write, via the derived unwritten gate, when the flat step_limit is lowered below 64.",
 "criteria": [
  {
   "id": "C1-mechanism",
   "pass": true,
   "claim": "the only legal self-exit is raised by the inner environment when a command's first output line is the completion marker with exit status zero; nothing on that path consults the artifact; what counts as an engineering write; the step-budget formula, its value before and after a write, and how it produced the recorded failure",
   "own_finding": "Re-derived from the code at 6be54ea and the external crate. (1) The marker is read by the inner environment's own inherent `check_finished`, called at the end of `LocalEnvironment::execute` (F:/RustProjects/mini-swe-agent-rust-mini/rust/src/environments/local.rs): `let trimmed = output.output.trim_start(); let (first_line, submission) = match trimmed.split_once('\\n') { Some((first, rest)) => (first, rest), None => (trimmed, \"\") }; if first_line.trim() == \"COMPLETE_TASK_AND_SUBMIT_FINAL_OUTPUT\" && output.returncode == 0 { return Err(FlowInterrupt::submitted(submission).into()); }`. A grep over the whole mini crate finds `FlowInterrupt::submitted` only in `environments/local.rs` and `environments/docker.rs` (plus tests), so a `Submitted` interrupt is exactly the inner environment's completion request; `agent.rs:342` only *reads* `InterruptKind::Submitted` (the `confirm_exit` path, which this harness sets false). (2) Nothing on that path consulted the artifact: the pre-change guard line was `let output = self.inner.execute(action, cwd, timeout).await?;` and `git diff 3474cdd 6be54ea -- src/` shows exactly two deleted lines - that line and the module-doc `//! Three jobs...` - so the pre-change guard propagated the interrupt untouched, and `compact.rs` only appends `interrupt.messages` and breaks when the last message role is `exit` (nothing there reads `artifact_written`). (3) An engineering write is `ArtifactKind::for_role(Role::Developer) == ArtifactKind::ProjectFile` and `counts(path) = !is_excluded_path(path)`, where `is_excluded_path` is `[\"\\\\.hoh/\", \"\\\\.git/\", \"target/\", \".hoh/\", \".git/\"]` prefix matching on the backslash-normalised path; `execute_write` sets `state.artifact_written = true` only when `counts` is true, and that flag is also what raises the step budget. (4) The budget formula, quoted: `effective_step_limit(has_written) = if has_written || steps_per_artifact == 0 { step_limit } else { (wrap_up_steps + (step_limit / steps_per_artifact).max(1)).max(wrap_up_steps) }`, enforced in `WriteGuardEnvironment::execute` at the top as `let budget = self.effective_step_budget().min(self.step_limit); let steps = self.steps(); if steps > budget { Some(FailFast::StepBudget { steps, budget }) } else { None }`. With the shipped config (`step_limit: 150`, `wrap_up_steps: 25`, `steps_per_artifact: 8`, all quoted from config/hoh.yaml:14/17/89) that is 25 + max(150/8, 1) = 25 + 18 = 43 model calls before a write and 150 after one; because the test is `steps > budget`, the 44th model call is billed and then refused. (5) That is exactly the recorded failure: runs/completion1/iter-3/traj/developer.attempt1.json has 44 model calls, 803,027 total tokens, 0 project writes, and runs/completion1/iter-3/result.json records `StepBudgetExceeded` and then the round's `NoEngineeringWrite`. The alignment of the two exclusion rules also holds: the round hashes with `HashExcludes::new(adapter.cache_excludes()).merged()` = [\".hoh\", \".git\", \"target\"] (policy.rs:38-47; bevy adapter cache_excludes = [\"target\"]) and the guard excludes the same three prefixes; my re-implementation of both found no disagreement on any recorded write path.",
   "reported_finding": "the same mechanism, the same quoted thresholds and the same 43/150 arithmetic; I found no divergence. The report's claim that `LocalEnvironment::check_finished` is 'the only place the marker is read' is true for the local environment; a DockerEnvironment has the identical rule, which does not change the conclusion.",
   "divergence": "none",
   "evidence": "F:/RustProjects/mini-swe-agent-rust-mini/rust/src/environments/{local.rs,151-160,docker.rs:110}; src/harness/guard.rs:759-767,801-814,921-923,1025-1031,955-995,1035-1110; src/config.rs:278-284; config/hoh.yaml:14,17,89; src/runtime/policy.rs:38-55; git diff 3474cdd 6be54ea -- src/; runs/completion1/iter-3/traj/developer.attempt1.json"
  },
  {
   "id": "C2-change",
   "pass": true,
   "claim": "a self-exit before a write is answered with an ordinary observation rather than raising, so the call continues; the exit is raised unchanged once the write exists; failure statuses are unaffected; the budgets that bound how long a refusal can repeat are unchanged; and the change adds a positive condition rather than removing a guard",
   "own_finding": "All four hold, read from the code and the diff. The new arm is `Err(error) if Self::is_completion_request(&error) && !self.completion_allowed() => { return Ok(self.completion_refusal()); } Err(other) => return Err(other),` where `is_completion_request(error) = matches!(error, AgentError::Interrupt(interrupt) if interrupt.kind == InterruptKind::Submitted)` and `completion_allowed() = !self.artifact_kind.gates_completion() || self.artifact_written()` with `gates_completion() = matches!(self, ArtifactKind::ProjectFile)`. A refusal is `Output::success(completion_refusal_text(...), 1)` plus `extra[hoh_exit_refused] = true`; `completion_refusal_text` names `write_failure::DECLARED_DEVELOPER` and repeats `directive_help()`, and mini merges `output.extra` into the observation (models/mod.rs:262-264), so the marker travels into the trajectory. Because the guard returns `Ok`, `run_compacting_agent` appends a normal tool observation in the same history and does not insert an `exit` message, so the call continues. With the artifact written, `is_completion_request && !completion_allowed` is false, so the interrupt is re-raised by the `Err(other)` arm byte-for-byte as before. Every other error (`LimitsExceeded`, `TimeExceeded`, `Format`) is deliberately not matched. `is_failure_status` (write_failure.rs:44-54) is not in the diff, and neither are `effective_step_limit`, `step_budget_exceeded`, `budget_exceeded`, `record_failure` or `record_success`. On 'a positive condition, not a removed guard': the diff's only deletions under src/ are the module-doc line and the `?`-propagation line; every negative guard is intact, and the round still fails when nothing is written - run_loop.rs:1843/1859 (`if h_dev_before == h_dev_after { ... NoEngineeringWrite ... }`) is unchanged, and the new integration test `the_unwritten_step_budget_guard_still_ends_a_call_that_never_writes` is green on HEAD and pins that a call that never writes is still cut with the harness's own failure status (`StepBudgetExceeded`, `is_failure_status` true).",
   "reported_finding": "identical, including the two deleted lines and the claim that no negative guard is touched. My independent read of `run_loop.rs` and `write_failure.rs` confirms the round-level empty-write failure is untouched.",
   "divergence": "none",
   "evidence": "src/harness/guard.rs:83-121,616-641,914-953,1035-1110; F:/RustProjects/mini-swe-agent-rust-mini/rust/src/models/mod.rs:229-264; src/runtime/write_failure.rs:44-54; src/runtime/run_loop.rs:1843-1860; git diff 3474cdd 6be54ea -- src/; green run of `cargo test --offline --lib harness::guard::tests`"
  },
  {
   "id": "C3-tests",
   "pass": true,
   "claim": "the claimed red state is genuine (the tests fail against the pre-change code for the stated reasons), the green state exercises the real environment rather than a stub, the assertions pin the described behaviour, and the one pre-existing test whose behaviour changed while its assertions did not is benign rather than a hidden weakening",
   "own_finding": "I reconstructed the pre-change tree outside the repository with `git archive 3474cdd | tar -x -C E:/acc-wge2-prefix`, copied the new tests/write_guaranteed_exit.rs onto it, and ran the two red commands in my own target dirs. Integration: `cargo test --offline --test write_guaranteed_exit` exits **101** with `4 passed; 2 failed; 0 ignored`, both failures being the claimed assertions - `a_completion_request_without_the_engineering_write_is_refused_and_the_call_continues` panics at tests/write_guaranteed_exit.rs:339:5 with `the refused completion must not have ended the call (steps = 1) left: 1 right: 3`, and `a_scratch_write_is_not_an_engineering_write` panics at :392:5 with `(steps = 2) left: 2 right: 4`; the next lines are exactly the report's two messages, and the file's line numbers are the report's 328/381 shifted by 11 by its own formatting pass. Unit: because the 5 guard tests are added by the change, I grafted the appended `#[cfg(test)]` block onto 3474cdd's guard.rs (script at E:/acc-wge2/graft.py; the block is self-contained) and `cargo test --offline --lib harness::guard::tests` exits **101** with `26 passed; 3 failed` - the report's `2 failed` is the same set minus the test it says was added after green. The two panics' literal payloads are the report's: `the guard refuses the completion instead of raising the interrupt: Interrupt(FlowInterrupt { kind: Submitted, messages: [Message { role: \"exit\", content: String(\"done\"), extra: Some({...}) }] })` and `a scratch write is not the declared artifact: Interrupt(FlowInterrupt { kind: Submitted, .. })`; the third failure is the post-green test's claim proving itself: `` `type marker.txt` must be refused, not accepted: agent flow interrupted: Submitted ``. Green on HEAD: `--lib harness::guard::tests` exits 0 with `29 passed`, `--test write_guaranteed_exit` exits 0 with `6 passed`. Real environment, not a stub: the integration harness builds `LocalEnvironment::new(LocalEnvironmentConfig { cwd, env: Default::default(), timeout: 60 })` behind the real `WriteGuardEnvironment` inside a real `DefaultAgent` run by the real `run_compacting_agent`; only the model is scripted, and the marker interrupt can only come from the real cmd.exe path. The assertions are behavioural, not tautological: Submitted at 2 calls after a write and at 1 call when the write and the completion share a response; one refusal with its text and the next call's view of it; a `.hoh/scratch` write earning no exit; and a never-writing call ending `StepBudgetExceeded` with `is_failure_status` true. The pre-existing test `tests/harness_cap_wiring.rs::the_harness_itself_bounds_what_the_next_request_carries` (unmodified, +0/-0) runs a Developer whose scripted second-and-later responses are the completion command while no write directive ever touches a project file, so its completion requests are now refused and the call ends on mini's flat `step_limit: 4` rather than `Submitted`; its assertions are on the second request's body (no FILLER run, truncation marker, <256 KiB) and on `outcome.role`, none of which the ending status touches, and the new tests now cover the `Submitted` ending explicitly. Benign, not a hidden weakening. Coverage gap (D4): no test drives *repeated* refusals to the step budget, which is the stated bound on the allowance.",
   "reported_finding": "the red exit codes, counts and panic payloads match exactly; the report's 2 lib failures are the 2 of the 3 that existed at its red run. The report itself discloses the changed pre-existing test and the fact that its new ending is an inference; my read agrees it is benign.",
   "divergence": "none in the claims. My lib red run shows 3 failures rather than 2 only because I grafted the post-green test as well; that test's failure is the red the report says it stands on.",
   "evidence": "E:/acc-wge2/red_int.{exit,out}, E:/acc-wge2/red_lib.{exit,out}, E:/acc-wge2/green_int.out, E:/acc-wge2/green_lib.out, E:/acc-wge2/graft.py, E:/acc-wge2-prefix/ (git archive of 3474cdd, outside the repository); tests/write_guaranteed_exit.rs; src/harness/guard.rs:2142-2399; tests/harness_cap_wiring.rs:90-247; git diff 3474cdd 6be54ea -- tests/"
  },
  {
   "id": "C4-projections",
   "pass": true,
   "claim": "re-derive the projected cost at each recording's first legitimate exit point, cross-check the method against a known figure, say which projections meet the criterion, and confirm the batch's honest 'saves nothing on its own' claim or refute it in either direction",
   "own_finding": "Re-derived from evidence/cost/*.developer.attempt1.json (read-only) by prefix-summing each recording's own per-call `extra.response.usage.total_tokens` over calls 1..N; a model call is a message carrying `extra.response` (69/125/102/150 of them, the same set hof.usage counts). Every measured figure reproduces exactly: round4-iter-1 69 calls, 2,544,563 prompt / 2,626,195 total (1.7508x), 6 write events all project, first write call 7, 20 retry turns at 25/27/32/33/35/37/38/41/46/48/50/52/53/56/58/59/61/62/66/67, first declared finish 25, projected total **665,666** (prompt 618,610) = **0.4438x**, max prefix under the criterion 44; round4-iter-2 125 calls, 12,765,478 / 13,091,431 (8.7276x), 23 writes = 11 project + 12 scratch, first write 33, first declared finish 58, projected **3,295,369** = **2.1969x**, max prefix 40; round4-iter-3 102 calls, 5,137,090 / 5,223,211 (3.4821x), 11 writes = 1 project + 10 scratch, first write 6, first declared finish 30, projected **1,160,900** = **0.7739x**, max prefix 36; livecost1-iter-1 150 calls, 3,537,843 / 3,651,120 (2.4341x), 5 writes = 4 project + 1 scratch ([6, 14, 19, 43]), first write 6, no declared finish, no legitimate exit, max prefix 81. Which meet: iteration 1 (0.4438x) and iteration 3 (0.7739x) would meet; iteration 2 (2.1969x) would not, and livecost1 has no exit point at all so it cannot meet. Method cross-check: the sum of prompt tokens over calls 1..24 of round4-iter-1 is exactly **579,603** = 2,544,563 - 1,964,960, reproducing RETRY-FIX-REPORT's independent calls-25..69 figure 1,964,960 exactly; the projection is therefore a measured prefix sum, not a model. 'Saves nothing on its own': TRUE. In all three declarations the first declared finish followed the first project write (25>7, 58>33, 30>6) and livecost1 never declared, so the gate would have refused nothing in the corpus; independently, no Developer recording anywhere under runs/** that used the write directive declares before its first counted write, and in none of the four recordings did the Developer run the marker command at all. The direction check: the gate is a permission (it can only refuse), so with zero declared-before-write it changes no recorded number, hence no saving and no recorded cost - the claim is right in both directions for the modern corpus.",
   "reported_finding": "every figure, ratio, write call, retry call and maximum in the report's JSON block matches mine; the 665,666 / 3,295,369 / 1,160,900 projections and the 0.44x / 2.20x / 0.77x ratios are exact, as is the cross-check 579,603. The 'saves nothing on its own' conclusion is correct.",
   "divergence": "none on the numbers or the conclusion (one scope point: see defect D2).",
   "evidence": "E:/acc-wge2/rederive.py and E:/acc-wge2/rederive.json (outside the repository); evidence/cost/*.developer.attempt1.json; .spec/bevy/RETRY-FIX-REPORT.md 'measurement.before' (1,964,960)"
  },
  {
   "id": "C5-next-step-warning",
   "pass": false,
   "claim": "the stated next step's warning is verifiable from the recordings: that a bound in the 36-81 range would have cut two of the four recorded calls before their first write, which two and at which call, and whether cutting there would have produced a failed round or merely a weaker artifact",
   "own_finding": "The warning as written does NOT reproduce. A flat total-call bound B in [36, 81] cannot cut any of the four corpus calls before its first write: their first project writes are calls 7, 33, 6 and 6, all <= 33 < 36, and the two live post-fix calls wrote at 8 and 13, also far below 36 - so a bound in the stated range cuts every one of them AFTER its write. The report's parenthetical ('round4-iter-2 wrote at call 33; the live calls wrote at 8 and 13') names three calls from two different corpora while the claim says two of four, and the named live calls are the ones a bound in that range would not cut. The one real pre-write hazard is a different mechanism the report gestures at but mis-attributes: the unwritten budget is *derived* from the flat limit as `25 + step_limit/8`, so lowering `step_limit` into 36-63 also lowers the unwritten gate to 29-32, which is below round4-iter-2's first write at call 33 - that single recording would be cut at calls 29-32 before its write. Consequence: a cut before the write leaves `h_dev_before == h_dev_after`, so the round fails with `NoEngineeringWrite` (exit 2), exactly completion1/iter-3; a cut after the write leaves a weaker/partial artifact and the hash gate does not fire. So the substance ('a criterion-tight bound can cut before the write and reproduce the empty failure') is real and worth carrying into the next batch, but it is ONE reachable recording via the derived gate, not two of four via the bound as stated.",
   "reported_finding": "the report says the bound would have cut two of the four recorded calls before their first write and would have reproduced iteration 3's cheap empty round.",
   "divergence": "the count and the attribution are wrong; the engineering implication (pair the bound with the write guarantee, and prefer a post-write budget over the unwritten gate) survives. Recorded as defect D1.",
   "evidence": "E:/acc-wge2/rederive.json (first_project_write_call and max_call_prefix_under_criterion per recording); E:/acc-wge2/live.py (live first writes 8 and 13, max prefix 78 and 74); src/config.rs:278-284 (the derived unwritten budget); src/runtime/run_loop.rs:1843-1860"
  },
  {
   "id": "C6-gate",
   "pass": true,
   "claim": "cargo test --offline exit 0 with the literal exit code and the passed/failed/ignored/listed counts, cargo fmt --all --check exit 0, zero warnings, and no test removed or weakened; own build directory, one test process at a time, free disk checked first, no rm -rf or wildcard deletion",
   "own_finding": "Own build directory E:/acc-wge2-target on E: (disk checked first: F: had 8.2 G, 100 % full, E: had 540 G free), one test process at a time. `cargo test --offline` -> literal exit code **0**, **813 passed / 0 failed / 6 ignored** over 61 `test result:` lines; `cargo test --offline -- --list` -> exit 0, **819** test lines; `cargo test --offline -- --list --ignored` -> exit 0, **6** test lines; `cargo fmt --all --check` -> exit 0, 0 bytes on stdout and stderr. Zero compiler warning lines (`grep -cE '^warning:'` is 0 on both streams; the only 5 lines containing 'warning' are test names) and 0 error lines. Exactly the batch's 813/0/6/819. The baseline 802/0/6/808 is the prior independent acceptance's measurement at e40c880, and `git diff e40c880 3474cdd` touches only `.spec/bevy/ACCEPTANCE-LIVE-COMPLETION.md`, so src/tests/config at 3474cdd are byte-identical; the delta is exactly the 11 new tests (5 guard unit + 6 integration). No test removed or weakened: `git diff 3474cdd 6be54ea -- tests/` is the new file only, and the src diff is additive apart from the two deleted lines named in C2. Nothing under the repository was deleted (I deleted nothing; the report says the same), no `rm -rf` and no wildcard deletion was used by me, no round and no model call was run, no engine was started, `runs/**` was read only, and I committed, staged and pushed nothing.",
   "reported_finding": "identical literal exit codes and identical counts (0 / 813 / 0 / 6, 819 listed, 6 ignored, fmt 0 with 0 bytes, 0 compiler warnings).",
   "divergence": "none. I did not re-run the full pre-change suite myself; the baseline is corroborated rather than re-measured here (see unverified).",
   "evidence": "E:/acc-wge2/test.{exit,out,err}, E:/acc-wge2/list.{exit,out}, E:/acc-wge2/listign.{exit,out}, E:/acc-wge2/fmt.{exit,out,err}; git diff e40c880 3474cdd --name-only; git diff 3474cdd 6be54ea --stat; git status --porcelain (empty)"
  }
 ],
 "defects": [
  {
   "id": "D1",
   "severity": "low",
   "what": "The stated next step's warning does not reproduce from the recordings: 'a bound ... would have cut two of the four recorded calls before their first project write (round4-iter-2 wrote at call 33; the live calls wrote at 8 and 13)'. A flat total-call bound in the stated 36-81 range cuts none of the four corpus calls (first writes 7/33/6/6) nor the two live calls (8/13) before their write; the parenthetical names three calls across two corpora while the claim counts two. The only reachable pre-write cut is round4-iter-2, and only because lowering the flat `step_limit` into 36-63 also lowers the *derived* unwritten budget `25 + step_limit/8` to 29-32, below that recording's first write at call 33.",
   "reproduction": "python E:/acc-wge2/rederive.py prints first_project_write_call and max_call_prefix_under_criterion for the four corpus recordings (7/44, 33/40, 6/36, 6/81); python E:/acc-wge2/live.py prints the two live calls' first writes (8, 13) and max prefixes (78, 74); src/config.rs:278-284 is the derived unwritten formula."
  },
  {
   "id": "D2",
   "severity": "low",
   "what": "The blanket claim 'in every recording and every live call the role's first declared finish (if any) already followed its first project write' is too broad. Four Developer recordings declare a FormatError finish with zero guard-visible writes: runs/round1b/iter-1 (140 calls, declaration at 117), runs/_legacy-attempt2-smoke-t1-qwen/iter-1 (29 calls, 24), runs/smoke-t10/iter-1 (150 calls, 108) and runs/smoke-t11/iter-1 (142 calls, 126). All four predate the HOH_WRITE_FILE directive, so they carry no `extra.hoh_write_path` at all and the counterfactual (would the gate have refused them?) is unmeasurable; the modern corpus the claim is used for is unaffected.",
   "reproduction": "python E:/acc-wge2/decl_check.py lists every Developer recording with a FormatError and its first counted write; the four DECL-BEFORE-WRITE rows have `all_writes=0`."
  },
  {
   "id": "D3",
   "severity": "informational",
   "what": "The report's constraints block says `committed: false`, but the change is now commit 6be54ea on bevy-core ('feat(guard): refuse a self-exit ...'), so the tree under review is a committed state rather than the working tree the batch described. The report's statement was true when written; the commit was made by the dispatcher, not by the batch.",
   "reproduction": "git log --oneline -3 shows 6be54ea; git show --stat 6be54ea lists src/harness/guard.rs, tests/write_guaranteed_exit.rs, DECISIONS.md D315 and the report."
  },
  {
   "id": "D4",
   "severity": "low",
   "what": "The stated bound on a refusal is not exercised by any test, and one of the two guards named as the bound is not consulted on the refusal path. A repeated completion request is a shell action that goes `step_budget_exceeded` -> `inner.execute` -> `return Ok(refusal)`, so `budget_exceeded` (the 900 s artifact-write budget, checked only after a normal inner return) is never reached on that path; the effective bound is the unwritten step budget of 43 model calls (and, at 150 flat, mini's own ceiling). No test drives a sequence of refusals to that bound.",
   "reproduction": "src/harness/guard.rs:1045-1050,1085-1087,1103-1108 (the refusal returns before `budget_exceeded`); src/runtime/write_failure.rs and the four wall-clock tests show no refusal-loop case; tests/write_guaranteed_exit.rs has one refusal per test."
  },
  {
   "id": "D5",
   "severity": "informational",
   "what": "The report's write-event detector is described as 'the same measurement ArtifactKind::counts makes, not a re-implemented regex'; strictly it is a re-implementation: a tool observation carrying `extra.hoh_write_path` with returncode 0, split into project/scratch by re-applying the exclusion prefixes. It reproduces every figure exactly (I re-implemented it independently and matched all write counts and call numbers), so the conclusion is unaffected.",
   "reproduction": "E:/acc-wge2/rederive.py (detector and split) reproduces the report's successful/project/scratch write counts and call lists for all four recordings."
  }
 ],
 "risks": [
  "The gate measures the guard's `artifact_written` (a successful counted HOH_WRITE_FILE directive), which is narrower than the round's artifact measurement (the before/after tree hash with [.hoh, .git, target] excluded). A role that changes the project with a plain shell command satisfies the round but not the gate, so its completion requests are refused and its call ends on the unwritten step budget as a failure status. This is disclosed in D315 and the report's alternatives, but its base rate is unmeasured and it is the one way this change can cost calls in the live tail.",
  "The refusal base rate in the recorded corpus is 0, so the change's runtime cost is unmeasured; the report's own estimate is about one model call (~20k tokens) per refusal, and four or more refusals per call would be needed for a prompt-level warning to have paid for itself. Only a live round can measure it.",
  "The next lever (a bound on call count) interacts with the derived unwritten budget: lowering the flat `step_limit` into 36-63 pushes the unwritten gate to 29-32 and re-creates the empty-round failure on round4-iter-2 (first write at 33). A post-write budget must therefore be added without lowering the pre-write gate below the recorded first-write calls.",
  "Even at the recorded first legitimate exit points the criterion is not met for round4-iter-2 (3,295,369 tokens, 2.1969x), and the two live post-fix calls never declared an exit at all; the largest prefix still under the criterion is 78 and 74 calls for those, so the live tail is what the next batch must measure.",
  "The projections assume the post-completion-fix prompt turns the recorded prose declaration into the documented `echo` command at the same call; the recordings show the declaration, not post-fix behaviour, so the live effect of the two changes together is still unmeasured.",
  "Single provider, single model, one project shape, and no second live round: no variance estimate exists for the read-heavy / no-write behaviour, and the round-level failure mode (empty Developer stage) is only sampled twice (round4-attempt1/iter-3 and completion1/iter-3)."
 ],
 "unverified": [
  "No round, model call, engine or network was run by this acceptance. The live behaviour of a refused completion (does the role then write, and how often is it refused?) is untestable without one.",
  "The exact exit status of tests/harness_cap_wiring.rs::the_harness_itself_bounds_what_the_next_request_carries after the change. I verified the mechanism (its scripted Developer never writes through the guard, so its completion requests are refused) and that its assertions cannot see the ending, but the test prints no status, so 'it now ends on mini's flat step_limit 4 rather than Submitted' remains a deduction - the same inference the report itself flags.",
  "The pre-change full-suite baseline 802/0/6/808 was not re-run by me. It is independently corroborated: the prior acceptance measured exactly those counts at e40c880, and `git diff e40c880 3474cdd` changes only a .spec document, so the tree is byte-identical for src/tests/config.",
  "Whether the Developers in the four legacy recordings (D2) wrote the project by shell and would therefore have been refused by the gate: those turns predate the write directive, so no guard-visible write exists to compare against.",
  "The base rate of refusals and of shell-side project writes, and the live effect of the change on the 1.5 M-token criterion.",
  "Any second provider, model or project shape."
 ],
 "what_i_did": [
  "read the artefact, LIVE-COMPLETION-MEASUREMENT.md, ACCEPTANCE-LIVE-COMPLETION.md and RETRY-FIX-REPORT.md, and re-derived the guard, mini-environment, loop and run-loop source that decides a call's end",
  "quoted every threshold from src/harness/guard.rs, src/config.rs and config/hoh.yaml rather than from the report, and confirmed the pre-change propagation line from `git diff 3474cdd 6be54ea -- src/`",
  "reconstructed the pre-change tree outside the repository (git archive 3474cdd into E:/acc-wge2-prefix), ran the new integration tests against the old guard (exit 101, 4 passed / 2 failed, the claimed assertions) and grafted the new unit tests onto the old guard (exit 101, 26 passed / 3 failed, the claimed payloads); ran the same tests green on HEAD (29 passed / 6 passed, exit 0)",
  "re-derived every projection, write event, retry turn and prefix sum from evidence/cost/*.developer.attempt1.json with scripts outside the repository, including the 579,603 cross-check, and analysed runs/completion1/iter-{1,2,3}/traj for the two live producing calls (first writes 8 and 13, max prefixes 78 and 74)",
  "censused every Developer recording under runs/** for declarations before the first counted write, and computed which recorded calls a criterion-tight bound would cut before their write",
  "ran cargo test --offline, both --list forms and cargo fmt --all --check in my own build directory E:/acc-wge2-target on E: (disk checked first: F: 8.2 G / 100 %, E: 540 G), one test process at a time",
  "wrote only .spec/bevy/ACCEPTANCE-WRITE-GUARANTEE.md in the repository; modified nothing under src/**, tests/**, evidence/**, runs/**, config/**, the registry, the battery, the liveness step, .gitattributes or any frozen document; committed, staged and pushed nothing; used no rm -rf, no wildcard deletion and no git checkout --"
 ],
 "single_most_important_thing": "The implemented guarantee is sound and adds a positive condition without removing any guard, so any future call bound can rely on it; but the next batch must not derive its bound by lowering the flat step_limit alone, because that also lowers the derived unwritten budget (25 + step_limit/8) and re-creates the empty-round failure on round4-iter-2 (first write at call 33) for any step_limit in 36-63. Bound the calls POST-write, leave the unwritten gate at 43, and measure the tail live."
}
```

# ACCEPTANCE-WRITE-GUARANTEE - independent acceptance of the write-guaranteed exit

**Who.** A fresh, independent acceptance pass. It inherited no conclusion from the implementer or the
dispatcher and treats every claim in `.spec/bevy/WRITE-GUARANTEED-EXIT-REPORT.md` as unverified until
re-derived. **No round, no model call, no engine, no network.** The structured verdict above was
produced by `json.dumps(..., indent=1, ensure_ascii=False)` in `E:/acc-wge2/write_acceptance.py` and
**parsed back out of this written file** (the parse runs after the file is written and fails unless the
block round-trips). Helper scripts live outside the repository at `E:/acc-wge2/`; the pre-change tree I
tested against is `E:/acc-wge2-prefix`, produced with `git archive 3474cdd`. My build directory is
`E:/acc-wge2-target` on `E:`.

**Verdict: `pass`.** The mechanism holds, the guarantee is real, and nothing was weakened. A Developer
call can no longer end at its own completion request before its counted engineering write exists; the
refusal is an ordinary observation that keeps the call alive; an exit after the write is raised
unchanged; every negative guard and every budget is untouched; the round still fails when nothing is
written. I reproduced the red state against a reconstructed pre-change tree, and the gate is
813 passed / 0 failed / 6 ignored / 819 listed with `cargo fmt` clean and zero warnings.

**The one thing that does not hold** is a forward-looking sentence in the report's next-step section
(defect D1): the warning that a criterion-tight bound would have cut *two of the four recorded calls
before their first write* is not reproducible. That does not touch the implemented mechanism or its
tests, and it is recorded below with the corrected arithmetic.

## 1. The mechanism, quoted from the code

The only legal self-exit is the inner environment's own:

```rust
// F:/RustProjects/mini-swe-agent-rust-mini/rust/src/environments/local.rs, check_finished
let trimmed = output.output.trim_start();
let (first_line, submission) = match trimmed.split_once('\n') { Some((first, rest)) => (first, rest), None => (trimmed, "") };
if first_line.trim() == "COMPLETE_TASK_AND_SUBMIT_FINAL_OUTPUT" && output.returncode == 0 {
    return Err(FlowInterrupt::submitted(submission).into());
}
```

called at the end of `LocalEnvironment::execute`. A grep over the whole mini crate finds
`FlowInterrupt::submitted` only in `local.rs` and `docker.rs` (plus tests), so a `Submitted` interrupt
is exactly this request, however it was spelled. Before the batch the guard simply wrote
`let output = self.inner.execute(action, cwd, timeout).await?;` - which `git diff 3474cdd 6be54ea --
src/` confirms as one of only two deleted lines - so nothing on the path consulted the artifact.

What counts as an engineering write: `ArtifactKind::for_role(Role::Developer) == ProjectFile` and
`counts(path) = !is_excluded_path(path)`, with `is_excluded_path` prefix-matching
`[".hoh/", ".git/", "target/", "\\.hoh/", "\\.git/"]`; a successful counted directive write sets
`state.artifact_written = true`. The round-level hash uses `[".hoh", ".git", "target"]`
(`policy.rs:38-47`), and my re-implementation of both found no disagreement on any recorded write path.

The step budget, quoted:

| value | expression | shipped config | result |
|---|---|---|---|
| before a write | `wrap_up_steps + max(step_limit / steps_per_artifact, 1)` | 25 + max(150/8, 1) | **43 model calls** |
| after a write | `step_limit` | 150 | **150 model calls** |
| enforcement | `let budget = effective_step_budget().min(step_limit); if steps > budget { StepBudget }` | - | the 44th call is billed, then refused |

`config/hoh.yaml` lines 14/17/89 are `step_limit: 150`, `wrap_up_steps: 25`,
`steps_per_artifact: 8`. That is exactly the recorded failure: `runs/completion1/iter-3` has 44 model
calls, 803,027 tokens, no project write, `StepBudgetExceeded`, then the round's `NoEngineeringWrite`
(exit 2).

## 2. The change, and why it is a positive condition

```rust
Err(error) if Self::is_completion_request(&error) && !self.completion_allowed() => {
    return Ok(self.completion_refusal());
}
Err(other) => return Err(other),
```

with `is_completion_request` matching only `InterruptKind::Submitted`, and
`completion_allowed() = !gates_completion() || artifact_written()` where
`gates_completion() = matches!(self, ArtifactKind::ProjectFile)`. The refusal is
`Output::success(completion_refusal_text(...), 1)` plus `extra.hoh_exit_refused = true`;
`completion_refusal_text` names the missing artifact in the runtime's own words and repeats
`directive_help()`, and mini merges `output.extra` into the observation
(`models/mod.rs:262-264`), so the key reaches the trajectory in production. Because the guard returns
`Ok`, the loop appends an ordinary tool result and does not insert an `exit` message; with the write
present the same error falls into `Err(other)` and is re-raised unchanged. Everything else
(`LimitsExceeded`, `TimeExceeded`, format errors, our own fail-fast) is not matched.

The diff's only deletions under `src/` are the module-doc line and the old `?` line. No negative guard
is touched: `is_failure_status`, `effective_step_limit`, `step_budget_exceeded`, `budget_exceeded`,
`record_failure` and `record_success` are all absent from the diff, and `run_loop.rs:1843/1859`
(`NoEngineeringWrite`) is unchanged. A round that writes nothing still fails, which
`the_unwritten_step_budget_guard_still_ends_a_call_that_never_writes` pins green.

## 3. Red and green, reproduced independently

I reconstructed the pre-change tree outside the repository and copied only the new test file onto it:

| command | reported | mine | agree |
|---|---|---|---|
| `--test write_guaranteed_exit`, pre-change guard | exit 101, 4 passed / 2 failed | **exit 101, 4 passed / 2 failed**, panics at :339 `left: 1 right: 3` and :392 `left: 2 right: 4` | yes |
| `--lib harness::guard::tests`, new tests grafted onto the pre-change guard | exit 101, 26 passed / 2 failed | **exit 101, 26 passed / 3 failed** | yes (the third is the post-green test; see below) |
| `--test write_guaranteed_exit`, HEAD | exit 0, 6 passed | **exit 0, 6 passed** | yes |
| `--lib harness::guard::tests`, HEAD | exit 0, 29 passed | **exit 0, 29 passed** | yes |

The two pre-change integral panics are literally the report's messages; the file's line numbers are
its 328/381 shifted by 11 by the formatting pass. The two guard panics carry the report's exact
payload - `Interrupt(FlowInterrupt { kind: Submitted, messages: [Message { role: "exit", ... }] })` -
which is the proof that the un-repaired guard ended the call exactly as `completion1/iter-3` did. The
third failure is the test the report says was added after green,
`the_gate_refuses_every_route_to_the_completion_interrupt`, failing with
`` `type marker.txt` must be refused, not accepted: agent flow interrupted: Submitted `` - the red it
claims to stand on.

Green is against a real environment: the integration harness builds a real `LocalEnvironment`
(`cmd.exe`) behind the real `WriteGuardEnvironment`, inside a real `DefaultAgent` run by the real
`run_compacting_agent`; only the model is scripted. The assertions are behavioural (Submitted at 2
calls after a write and at 1 when the write and the completion share a response; one refusal with its
text visible to the next call; `.hoh/scratch` earning no exit; a never-writing call ending
`StepBudgetExceeded` with `is_failure_status` true; a plain command untouched).

**The pre-existing test whose behaviour changed with unchanged assertions** is
`tests/harness_cap_wiring.rs::the_harness_itself_bounds_what_the_next_request_carries`. Its scripted
Developer never writes through the guard, so its completion requests are now refused and the call ends
on mini's flat `step_limit: 4` instead of `Submitted`. Its assertions are on the second request's body
(no `FILLER` run, truncation marker, under 256 KiB) and on `outcome.role`; none can see the ending, and
the new tests now cover the `Submitted` ending explicitly. **Benign, not a hidden weakening.**

## 4. The projections: my figures beside the report's

Re-derived by prefix-summing each recording's own `extra.response.usage.total_tokens` over calls 1..N.
Every figure below reproduces exactly.

| recording | calls | measured total | ratio | writes (project/scratch) | first project write | first declared finish | projected total at that exit | projected ratio | meets | max prefix under 1.5 M |
|---|---|---|---|---|---|---|---|---|---|---|
| round4-iter-1 | 69 | 2,626,195 | 1.7508x | 6 / 0 | 7 | 25 | **665,666** | **0.4438x** | yes | 44 |
| round4-iter-2 | 125 | 13,091,431 | 8.7276x | 11 / 12 | 33 | 58 | **3,295,369** | **2.1969x** | no | 40 |
| round4-iter-3 | 102 | 5,223,211 | 3.4821x | 1 / 10 | 6 | 30 | **1,160,900** | **0.7739x** | yes | 36 |
| livecost1-iter-1 | 150 | 3,651,120 | 2.4341x | 4 / 1 | 6 | never | none | - | no (no exit exists) | 81 |

Method cross-check: the prompt tokens over calls 1..24 of round4-iter-1 are exactly **579,603** =
2,544,563 - 1,964,960, reproducing RETRY-FIX-REPORT's independent calls-25..69 figure. So the
projection is a measured prefix sum, not a model.

**'Saves nothing on its own' is correct.** Every recorded declaration came after the first project
write (25>7, 58>33, 30>6) and livecost1 never declared; independently, no Developer recording under
`runs/**` that used the write directive declares before its first counted write, and the marker command
appears nowhere in the four recordings. The gate can only refuse, so with zero declared-before-write it
changes no recorded number - no saving and no recorded cost.

## 5. The stated next step, and the warning that does not reproduce

| recording | first project write | flat bound 36 | 36-81 cuts it ... | post-write prefix bound | pre-write cut via the derived gate (25 + B/8) |
|---|---|---|---|---|---|
| round4-iter-1 | 7 | after the write | after | 44 | never (B/8 >= 4 -> 29 > 7) |
| round4-iter-2 | **33** | after the write | after | 40 | **B in 36-63 -> unwritten 29-32 < 33** |
| round4-iter-3 | 6 | after the write | after | 36 | never |
| livecost1-iter-1 | 6 | after the write | after | 81 | never |
| completion1 iter-1/iter-2 (live) | 8 / 13 | after the write | after | 78 / 74 | never |

So a **flat total-call bound in 36-81 cuts no recorded call before its write**; the report's
"two of the four ... (round4-iter-2 wrote at call 33; the live calls wrote at 8 and 13)" names three
calls from two corpora, counts two, and the named live calls are precisely the ones such a bound would
not cut. The only reachable pre-write cut is **round4-iter-2**, and only because the unwritten budget is
derived as `25 + step_limit/8`: lowering the flat `step_limit` into **36-63** drops that gate to 29-32,
below its first write at call 33.

The distinction the question asks for is sharp. Cutting **before** the write leaves
`h_dev_before == h_dev_after`, so the round **fails** with `NoEngineeringWrite` (exit 2), exactly
`completion1/iter-3`. Cutting **after** the write leaves a weaker, partial artifact; the hash gate does
not fire, so it is a **weaker artifact**, not a failed round. The report's engineering implication
survives - pair any bound with the write guarantee, and prefer a post-write budget over the unwritten
gate - but its count and attribution do not (defect D1).

## 6. Gate

| check | literal exit code | result |
|---|---|---|
| `cargo test --offline` | **0** | **813 passed / 0 failed / 6 ignored**, 61 `test result:` lines, **0 compiler warnings**, 0 error lines |
| `cargo test --offline -- --list` | **0** | **819** test lines |
| `cargo test --offline -- --list --ignored` | **0** | **6** test lines |
| `cargo fmt --all --check` | **0** | 0 bytes on stdout and stderr |

Build directory `E:/acc-wge2-target` on `E:` (disk checked first: `F:` had 8.2 G and was 100 % full,
`E:` had 540 G), one test process at a time. The delta from the pre-change tree is exactly the 11 new
tests (5 guard unit + 6 integration); `git diff 3474cdd 6be54ea -- tests/` is the new file only and the
`src/` diff is additive apart from the two deleted lines. The 802/0/6/808 baseline is the prior
independent acceptance's measurement at `e40c880`, and `git diff e40c880 3474cdd` touches only a
`.spec` document, so the tree is byte-identical for `src/tests/config`. No `rm -rf`, no wildcard
deletion, no `git checkout --`, nothing under `runs/**` written, nothing deleted, nothing committed,
staged or pushed.

## 7. Defects, risks and what I could not establish

**D1 (low).** The next-step warning's count and attribution do not reproduce (section 5).
**D2 (low).** The blanket "every recording ... first declared finish followed its first project write"
is too broad: four legacy Developer recordings (`round1b`, `_legacy-attempt2-smoke-t1-qwen`,
`smoke-t10`, `smoke-t11`) declare with zero guard-visible writes, though all predate the write directive
so the counterfactual is unmeasurable. **D3 (informational).** The report says `committed: false`, but
the change is now `6be54ea` (the dispatcher committed it). **D4 (low).** The claim that repeated
refusals are bounded is not exercised by any test, and `budget_exceeded` (the 900 s artifact budget) is
not consulted on the refusal path - the effective bound is the 43-call unwritten step budget.
**D5 (informational).** The write detector is a re-implementation of `ArtifactKind::counts`, not the
same code, though it reproduces every figure.

The main **risk** is that the gate's `artifact_written` is narrower than the round's tree hash: a
shell-side project write satisfies the round but not the gate, so the call would be refused and end on
the unwritten step budget. D315 discloses this; its base rate is unmeasured. The next bound must also
avoid lowering the derived unwritten gate (section 5).

I could not establish: any live refusal behaviour (no round and no model call was run); the exact exit
status of the cap-wiring test after the change (deduced, not printed); the pre-change full-suite
baseline by re-running it (corroborated instead); whether the legacy recordings wrote by shell; and the
base rate of refusals or of shell-side writes.
