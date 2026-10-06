```json
{
 "schema": "hof-rs / independent acceptance of the live completion-protocol cost measurement",
 "artifact_under_review": ".spec/bevy/LIVE-COMPLETION-MEASUREMENT.md",
 "reviewed_commit": "e40c880 (head at review time; the artefact itself is that commit's only file). The round was run at cbb94c0, whose src/** is byte-identical to the prompt-fix commit 9b74379 (git diff 9b74379 cbb94c0 -- src/ is empty; that range adds only .spec/bevy/ACCEPTANCE-RETRY-FIX.md).",
 "review_kind": "independent, re-derived from runs/completion1/**, runs/bevy-completion1/**, the earlier recorded round trees, the experiment's own captured logs at D:/live2/logs and its launch snapshots at D:/live2/snapshots, and the repository's own guard/run-loop source. No round, no model call, no engine, no network.",
 "verdict": "pass",
 "headline": "Every headline number re-derives: the round exits 2 with NoEngineeringWrite at iteration 3; retries are 0 across all 8 attempt trajectories; the two producing Developer calls are 2.3517x and 2.6260x the criterion and the round is therefore failed. My independent answer to the central question is that iteration 3's no-write failure is PRE-EXISTING FRAGILITY, not a regression from the prompt change: runs/round4-attempt1, recorded a day before the prompt-fix commit and carrying the old prompt, failed with an identical result shape at the same gate. The artefact is right about the round and over-cautious about the attribution; it is wrong (over-strong) in one sentence that calls the completion protocol irrelevant to the criterion.",
 "criteria": [
  {
   "id": "C1-headline-exit-and-failure",
   "pass": true,
   "claim": "hoh init exit 0, hoh run exit 2, the round failed at iteration 3 with contract violation NoEngineeringWrite, and iterations 1-2 completed",
   "own_finding": "runs/completion1/exit_code = '2' and process_exit_code = '2'; meta.json exit_code 2, artifact_gate applicable=false, reasons=['the round failed; no artifact gate was produced']; iter-1 and iter-2 result.json ok=true reason='ok', iter-3 result.json ok=false failed_role='developer' reason='contract_violation' with warnings ['harness_source_read','no_progress','role_write_failure: developer attempt 1 ended `StepBudgetExceeded` without writing a file inside the project ...','no_engineering_write'] and write_failures[0].artifact_written=false. The experiment's own captured logs confirm the literal codes without a re-run: D:/live2/logs/build_hoh.exit 'exit=0', init.exit 'exit=0', run.exit 'exit=2', run.err exactly 'hoh: contract violation: NoEngineeringWrite (no_engineering_write)'. run.started 2026-10-06T07:06:47+0800, run.finished 2026-10-06T08:28:22+0800 = 81.58 min.",
   "reported_finding": "the same literal codes, the same iteration, the same violation and the same 81.58 min",
   "divergence": "none",
   "evidence": "runs/completion1/{exit_code,process_exit_code,meta.json,warnings.log,iter-*/result.json}; D:/live2/logs/{build_hoh.exit,init.exit,run.exit,run.err,run.started,run.finished}"
  },
  {
   "id": "C2-headline-cost-figures",
   "pass": true,
   "claim": "per-role and per-iteration token totals, call counts and ratios, re-derived from the trajectories rather than read out of the report's table",
   "own_finding": "Re-derived by summing extra.response.usage on every message that carries it (the same set src/runtime/usage.rs::extract_usage counts). Developer iter-1 150 calls / 3,414,645 prompt / 112,921 completion / 3,527,566 total = 2.3517x; iter-2 150 / 3,820,462 / 118,565 / 3,939,027 = 2.6260x; iter-3 44 / 789,257 / 13,770 / 803,027 = 0.5354x. Planner 6/6/6 calls, 42,397 / 56,179 / 43,460 prompt, totals 44,432 / 59,565 / 46,065. Tester iter-1 98 calls / 2,310,975 / 35,710 / 2,346,685 = 1.5645x; iter-2 150 / 3,786,462 / 53,465 / 3,839,927 = 2.5600x. Per-role totals: planner 18 calls / 142,036 prompt; developer 344 / 8,024,364; tester 248 / 6,097,437. Durations: developer 1,239,788 + 1,667,023 + 349,903 = 3,256,714 ms = 54.279 min. Every one equals the report's table. The criterion is therefore unmet: two producing calls at 2.35x and 2.63x, and the only sub-criterion call is the aborted one.",
   "reported_finding": "identical to the token, the call and the millisecond",
   "divergence": "none",
   "evidence": "E:/acc-live/usage_rederive.json (my script, outside the repository); runs/completion1/iter-*/usage.json and iter-*/traj/*.attempt1.json"
  },
  {
   "id": "C3-regression-or-pre-existing",
   "pass": true,
   "claim": "determine whether iteration 3's Developer writing nothing (and the resulting NoEngineeringWrite) was caused by the prompt change or would have happened anyway",
   "own_finding": "PRE-EXISTING FRAGILITY, high confidence. runs/round4-attempt1 is a recorded round whose files are dated 2026-10-05 02:45, roughly 28 hours BEFORE the prompt-fix commit 9b74379 (2026-10-06 06:38:55), and whose delivered developer prompt is the OLD wording (no [completion] section, 'end your run with the completion protocol'). It exits 2 with artifact_gate applicable=false, and its iter-3 result.json is the same shape in every field as completion1's: ok=false, failed_role='developer', reason='contract_violation', developer exit_status 'StepBudgetExceeded' (30 model calls vs 44 here), the same three warnings verbatim, and the same write_failures entry (artifact_written=false, declared_artifact 'a file inside the project ...'). Both plans asked for real project changes. The prompt change is confined to the completion paragraph: I diffed the delivered developer system prompts (pre from runs/round4-attempt1/iter-3, post from runs/completion1/iter-3) and the only hunk is the old three-line 'end your run with the completion protocol' replaced by the new [completion] section; the delivered task prompts are byte-identical. The failing gate (config agent.steps_per_artifact: 8 -> guard budget wrap_up_steps 25 + step_limit 150 / 8 = 43 model calls, refused when steps > budget at src/harness/guard.rs:736) has nothing to do with the completion protocol, and the round-4 repair that changed the guard from counting actions to counting model calls made the cut LATER (44 calls here vs 30 in round4-attempt1), i.e. it reduced rather than increased this failure's reach.",
   "reported_finding": "the artefact reports the failure and lists the attribution as 'not established; one round cannot separate it from model variance or from the steps_per_artifact guard interacting with a read-heavy plan'",
   "divergence": "the artefact under-claims. The separating evidence is in the artefact's own run tree (runs/round4-attempt1) and its own JSON block already names the guard as the alternative cause without checking whether the guard had already produced this exact failure before the change. The report's conclusion is not wrong, only weaker than the evidence supports.",
   "evidence": "runs/round4-attempt1/{exit_code,meta.json,warnings.log,iter-3/result.json,iter-3/traj/developer.attempt1.json,iter-3/plan.md} vs runs/completion1/iter-3/**; E:/acc-live/prompt_diff.py and prompt_marker.py output; config/hoh.yaml steps_per_artifact; src/harness/guard.rs:706-737; src/runtime/run_loop.rs:1800-1919; src/runtime/write_failure.rs:44-54"
  },
  {
   "id": "C4-retry-claim",
   "pass": true,
   "claim": "format-error retries are genuinely zero in this round across every role and iteration, and the recorded rounds had the counts the earlier report attributed",
   "own_finding": "Zero. Every message of every one of the 8 attempt trajectories in runs/completion1/iter-{1,2,3}/traj (iter-1 and iter-2 have planner+developer+tester; iter-3 has planner+developer) was censused for extra.interrupt_type == 'FormatError': 0 in all 8, and no extra.interrupt_type of any kind appears. Recorded rounds reproduce the earlier attribution exactly: round4 developer 20/10/8 with 876,566 / 1,486,702 / 416,910 retry prompt tokens; round4 planner 8/2/6 (89,313 / 20,159 / 67,761) and tester 5/4/1 (382,706 / 213,244 / 61,110); livecost1 developer 0, planner 4 (33,395), tester 3 (100,603); clonefix1 developer 0/0/0, planner 3/4/4 (17,363 / 32,953 / 36,276), tester 3 and (attempt2) 4 and (attempt2) 2 (116,205 / 88,517 / 76,512); round3 planner 4/3/3, tester 4/1/6, developer 0/0/6. The four corpus recordings total 38 turns and 2,780,178 retry prompt tokens, as reported. The new completion command appears where the report says it does: 'echo COMPLETE_TASK_AND_SUBMIT_FINAL_OUTPUT' as the last call of the Planner in all three iterations (call 6 of 6) and of the Tester in iteration 1 (call 98 of 98), and nowhere in the Developer's 344 calls.",
   "reported_finding": "0 after, 38 before over the four recordings, and the same per-role before counts",
   "divergence": "one count is wrong: the artefact says 'not one of the 7 recorded model-call sequences of this round', but the round has 8 (see defect D1). The retry conclusion itself is exact.",
   "evidence": "E:/acc-live/retry_scan.py, retry_tokens.py, retry_summary.json (outside the repository)"
  },
  {
   "id": "C5-identity-and-trustworthiness",
   "pass": true,
   "claim": "on the launches where a game ran: pre-spawn ledger nonce equals the answering nonce, answering pid equals the spawned pid, the OS listener names the same pid, no other listener, and nothing survives the round",
   "own_finding": "Verified for BOTH completed iterations. Surviving launch (runs/bevy-completion1/launch.json): nonce == answered_nonce == e42b6006-f5e2-4e69-ab48-0d37618b26ea, spawned_pid == answering_pid == listening_pid == 49948, verified true, launch_image UUID e608b3b5-841d-4b5a-aafb-915d27f2d128, which is exactly launch-ledger.jsonl line 4 (launched_at_seconds 1791245359, pid 49948, same UUID). Iteration 1's launch is independently preserved at D:/live2/snapshots/iter-1/launch.json: nonce == answered_nonce == 3c840cf2-00dd-42e3-beb4-edb727811980, spawned_pid == answering_pid == listening_pid == 57176, verified true, ledger line 2. D:/live2/snapshots/iter-2/launch.json preserves the same agreement for 49948. The ledger has 5 append-only lines with 5 distinct nonces, pids and launch-image UUIDs, and all five directories exist under runs/bevy-completion1/launch-image/. round-stop.json: recorded [50340,57176,41920,49948,54908], reaped [57176], still_alive [], endpoint_holder null, failure null. As of this acceptance there is no LISTENING socket on 15702/15703 and no hof_game.exe or hoh.exe process.",
   "reported_finding": "the same three-way agreement, the same nonce/pid values, the same ledger lines and the same clean sweep",
   "divergence": "none. The report's in-round netstat reading (one LISTENING line, pid 41920 = ledger line 3) is a first-party observation that cannot be retaken; it is consistent with the ledger but is not independently verifiable.",
   "evidence": "runs/bevy-completion1/{launch.json,launch-ledger.jsonl,round-stop.json,meta.json}; D:/live2/snapshots/iter-{1,2}/launch.json; my netstat/tasklist read"
  },
  {
   "id": "C6-cheap-but-empty-call",
   "pass": true,
   "claim": "the only call under the criterion got there by being aborted with no artifact, and the pipeline's handling of a call that ends with no artifact is what failed the round",
   "own_finding": "Confirmed. The 803,027-token Developer call in iteration 3 ended 'StepBudgetExceeded' at 44 model calls after making 43 allowed calls; the guard budget is wrap_up_steps + step_limit / steps_per_artifact = 25 + 150/8 = 43 and the refusal fires when steps > budget (src/harness/guard.rs:706-737), so the 44th call is billed and refused. Its 44 calls are reads of .hoh/TASK.md, plan.md, EVIDENCE_HISTORY.md, src/*, the deterministic records and powershell JSON probes, plus two writes into .hoh/scratch (a copy of plan.md at call 34 and game_num.txt at call 36); no HOH_WRITE_FILE command against a project path appears anywhere. The pipeline then measures the artifact tree: h_dev_before == h_dev_after, so src/runtime/run_loop.rs:1843-1919 pushes 'no_progress', attaches the write_failures entry, pushes 'no_engineering_write' and calls finalize_failure(..., 'contract_violation' ...) then returns HofError::contract(NoEngineeringWrite) - literal exit 2. This is NOT the weaker-artifact risk ACCEPTANCE-RETRY-FIX C7 predicted (that risk was a 'Submitted' early end with a valid-but-unfinished artifact). It is the pre-existing no-write / step-budget failure: a call that is cheap only because it was cut off, and whose cheapness is the direct cause of the round's failure.",
   "reported_finding": "the same state and the same conclusion ('a call under the token bar that wrote no engineering file is not a win')",
   "divergence": "the artefact attributes 46 files under .hoh/scratch to iteration 3; only 2 of them are from iteration 3 (see defect D2). Its substantive claim - no write inside the project - is correct.",
   "evidence": "runs/completion1/iter-3/{usage.json,result.json,traj/developer.attempt1.json,warnings.log,plan.md}; D:/live2/project/{src/game.rs (19,134 bytes, unchanged from iteration 2),.hoh/scratch mtimes}; src/harness/guard.rs:706-737; src/runtime/run_loop.rs:1800-1919; src/runtime/write_failure.rs"
  },
  {
   "id": "C7-gate",
   "pass": true,
   "claim": "cargo test --offline exit 0 with the literal exit code and the baseline counts, fmt exit 0, zero warnings, no test removed or weakened",
   "own_finding": "Own build directory E:/acc-live-target on E: (550 G free, checked first; F: had 8.3 G), one test process at a time, no rm -rf and no wildcard. cargo test --offline: literal exit code 0; 802 passed / 0 failed / 6 ignored over 60 'test result:' lines; 0 compiler warning lines and 0 error lines on stdout+stderr. cargo test --offline -- --list: exit 0, 808 test lines. cargo test --offline -- --list --ignored: exit 0, 6 test lines. cargo fmt --all --check: exit 0, 0 bytes on stdout and stderr. Exactly the stated baseline 802/0/6/808. The delta from the pre-fix baseline 800/0/6/806 is the two tests added by the prompt fix: git diff 9d3f488 HEAD -- tests/ touches only tests/prompt_shell_contract.rs (+136/-5) and nothing was removed. git diff 9b74379 HEAD -- src/ config/ is empty, so the tree under test is the prompt-fixed tree.",
   "reported_finding": "identical literal exit codes and identical counts",
   "divergence": "none",
   "evidence": "E:/acc-live/{gate.exit,gate.out,gate.err,list.exit,list.out,listign.exit,listign.out,fmt.exit,fmt.out,fmt.err}; git diff/diff --stat"
  },
  {
   "id": "C8-next-decision-and-cost-levers",
   "pass": true,
   "claim": "assess whether the artefact's evidence supports its stated next decision (bound the call count, not the completion protocol) or closes more than it should",
   "own_finding": "The direction is supported; the phrasing closes one step too far. Supported: retries are 0 and can no longer be the lever; the Developer ran the completion command 0 times in 3 iterations and two of three calls ground to the 150-call ceiling; the precondition (bound the calls in a way that cannot be satisfied by a call that writes nothing) is not only right but is demonstrated by this round's own iteration 3. Over-closed: the sentence 'the completion protocol is now correct and irrelevant to the criterion' is not what the evidence says. The frozen spike's own zero-context floor for a 150-call live Developer call is 2,077,238 prompt tokens, already above 1,500,000, so a producing Developer call CANNOT meet the criterion at the current 150-call ceiling however small its context is - an earlier self-exit by the role and a bound on its calls are the same lever, not alternatives. And one round in which the Developer never declared itself finished cannot show the new wording did not affect that declaration, the more so because the pre-change live rounds (livecost1, clonefix1) also show a Developer that never ran the marker over four full calls. The artefact's flat statement that the live model 'will spend all 150 calls it is given' is thus true of the observed rounds but is precisely the behaviour the criterion has to change.",
   "reported_finding": "the report's section 7 and single_most_important_thing reach the same recommendation but call the protocol 'correct and irrelevant'",
   "divergence": "recommendation accepted; the 'irrelevant' characterisation is unsupported and the report does not draw the interaction it should - that any bound tight enough to meet 1.5 M is also tight enough to cut the Developer before it writes, which is exactly what failed this round",
   "evidence": ".spec/bevy/SPIKE-COST-LEVERS.md lever-1 cap_zero_totals.livecost1-iter-1 = 2,077,238 and lever-4; config/hoh.yaml step_limit 150 and steps_per_artifact 8; runs/livecost1/iter-1/traj/developer.attempt1.json and runs/clonefix1/iter-*/traj/developer.attempt1.json (marker_cmds empty, FormatError 0)"
  }
 ],
 "defects": [
  {
   "id": "D1",
   "severity": "low",
   "what": "The count of recorded sequences is wrong: the JSON 'why_none' and section 1 say 'the 7 recorded model-call sequences of this round', but the round has 8 attempt trajectories - iter-1 and iter-2 each ran planner+developer+tester, and iter-3 ran planner+developer.",
   "reproduction": "ls runs/completion1/iter-1/traj runs/completion1/iter-2/traj runs/completion1/iter-3/traj | grep -v redacted -> 8 *.attempt1.json files; my FormatError census over all 8 is 0, so the conclusion is unaffected."
  },
  {
   "id": "D2",
   "severity": "low",
   "what": "The 46 files under .hoh/scratch are the round-cumulative count 'at the gate', not iteration 3's Developer's writes. The artefact writes 'iter-3 wrote nothing inside the project (44 calls, 46 files under .hoh/scratch only)' and repeats the harness's 46, but only 2 of the 46 belong to iteration 3; the other 44 carry 07:06-08:09 mtimes from iterations 1-2.",
   "reproduction": "ls -la --time-style=full-iso D:/live2/project/.hoh/scratch -> plan_copy.md 08:22:29 and game_num.txt 08:27:43 (iteration 3 ran 08:22-08:28); the remaining 44 files are dated 07:06-08:09. The harness warning itself hedges with 'at the gate'."
  },
  {
   "id": "D3",
   "severity": "medium",
   "what": "The artefact calls the iteration-3 no-write attribution 'not established from one round' when its own run tree contains the separating evidence: runs/round4-attempt1 is a pre-change round (files dated 2026-10-05 02:45, old completion wording) that failed the same way with the same result shape. The artefact recorded the guard as a rival cause but never checked the earlier round for it.",
   "reproduction": "compare runs/round4-attempt1/iter-3/result.json with runs/completion1/iter-3/result.json: ok=false, failed_role='developer', reason='contract_violation', the same three warnings, the same write_failures entry; round4-attempt1's exit_code is 2 and its developer ended StepBudgetExceeded at 30 model calls."
  },
  {
   "id": "D4",
   "severity": "medium",
   "what": "Section 7 asserts the completion protocol is 'correct and irrelevant to the criterion', which the evidence does not support: at step_limit 150 the criterion is arithmetically unreachable without an early exit (the spike's own C=0 floor for the live 150-call Developer call is 2,077,238 prompt tokens), so the early exit is a necessary condition for the criterion, not an alternative to bounding calls. The report also treats 'the Developer never takes the new exit' as a finding of this round without noting that the two pre-change live rounds show the same non-taking.",
   "reproduction": ".spec/bevy/SPIKE-COST-LEVERS.md: lever-1 cap_zero_totals livecost1-iter-1 2,077,238; config/hoh.yaml step_limit: 150. runs/livecost1/iter-1 and runs/clonefix1/iter-* developer trajectories: FormatError 0 and no command containing COMPLETE_TASK_AND_SUBMIT_FINAL_OUTPUT in 150/150/150 and 150 calls."
  },
  {
   "id": "D5",
   "severity": "informational",
   "what": "'first_declared_finish.iter-3.tester' reports did_the_call_end_there: true with call_index null and exit_status_at_end_of_call null, but iteration 3 ran no Tester stage at all, so the record describes a call that never happened.",
   "reproduction": "runs/completion1/iter-3/result.json attempts contains planner and developer only; ls runs/completion1/iter-3/traj -> planner.attempt1.json and developer.attempt1.json only."
  },
  {
   "id": "D6",
   "severity": "informational",
   "what": "The constraints block says 'the only untracked path is this report' and committed_or_pushed false; the report has since been committed as e40c880, and the working tree is clean.",
   "reproduction": "git status --porcelain is empty; git show --stat e40c880 adds exactly .spec/bevy/LIVE-COMPLETION-MEASUREMENT.md. The statement was true when the report was written and is stale now; it is not evidence of a constraint breach by the measurement run."
  },
  {
   "id": "D7",
   "severity": "informational",
   "what": "The after-the-round claim 'netstat names no line for 15702 or 15703' is not literally what a plain query returns now, though the substance (no listener, no game process) holds.",
   "reproduction": "netstat -ano | grep 15702 now returns one non-LISTENING line (a SYN_SENT socket from an unrelated, already-gone pid); there is no LISTENING line and tasklist shows no hof_game.exe or hoh.exe."
  }
 ],
 "risks": [
  "The criterion is not reachable by any context-only lever: the spike's own zero-context floor for a 150-call live Developer call is 2,077,238 prompt tokens (1.39x), so a producing Developer call must make materially fewer calls. At this round's observed cost per call (22,764 and 25,470 prompt tokens per call over 150 calls) the two producing calls would need roughly 57-63 calls to pass - a 2.4-2.6x cut that no measured lever delivers on all recordings.",
  "Every hard call bound tight enough to matter is also tight enough to fire before the Developer writes, which is exactly how this round failed: iteration 3 was cut at 43 allowed model calls (44 billed) with no project write, and the round exited 2. The next decision must pair any call/step bound with a mechanism that guarantees the artifact write (the round itself is the worked example).",
  "Round4-attempt1 proves the no-write grind is not new but says nothing about its base rate; the criterion is judged on a single Developer call, so a rare grind can decide it. Two of three completing calls in this round were producing, but both hit the 150-call ceiling, so cost is currently decided by the ceiling, not the task.",
  "The completion protocol's behavioural half remains unmeasured: the Developer ran the documented command 0 times and never self-declared finish. Whether the new wording suppressed a self-declared finish that the old wording produced cannot be separated from the two pre-change live rounds that also never declared - so 'the protocol is irrelevant' is an inference, and a single A/B of the completion text with everything else fixed would settle it.",
  "Single provider, single model, single project shape, and one live round: no variance estimate exists for the read-heavy/no-write behaviour, and no second live round was run (by instruction)."
 ],
 "unverified": [
  "No round, model call, engine or network was run by this acceptance. The literal hoh exit codes and stderr are verified from the experiment's own captured logs (D:/live2/logs/run.exit, run.err, init.exit, build_hoh.exit) rather than from a process I ran.",
  "The report's in-round netstat reading (exactly one LISTENING line, pid 41920 = ledger line 3) is a first-party observation that cannot be retaken; only consistency with the append-only ledger can be checked, and it is consistent.",
  "The counterfactual 'would iteration 3 have written had the completion prompt been the old one' cannot be run. My C3 determination is an attribution from a pre-change round with the identical failure shape, not a re-run.",
  "Plan conformance of the two completed artifacts. Observable: artifact_valid, game.rs growth 4,502 -> 11,828 -> 19,134 bytes, and all 12 battery steps green on the first pass with repair_retry_used false. Not observable from here: whether the planner's plan was fully implemented.",
  "The artefact's wire-byte/token cascade model is outside this acceptance's scope; it was already examined in .spec/bevy/ACCEPTANCE-RETRY-FIX.md (defect D5), and this round contains no retry turns to test it against.",
  "Any effect on a second provider, model or project shape."
 ],
 "what_i_did": [
  "re-derived every per-role, per-iteration and per-round token/call figure from runs/completion1/iter-*/traj/*.attempt1.json and usage.json with scripts written outside the repository at E:/acc-live/",
  "censused extra.interrupt_type over all 8 attempt trajectories of this round and over the recorded round trees (round4, livecost1, clonefix1, round3, round4-attempt1/2/3/4/5), and re-derived every retry count and retry prompt-token figure",
  "diffed the delivered pre-change and post-change developer system/task prompts, and identified runs/round4-attempt1 (2026-10-05, old prompt) as the pre-change counterexample with an identical failure shape",
  "read the launch records, the append-only ledger, round-stop.json and the experiment's own launch snapshots at D:/live2/snapshots/iter-{1,2}, and took my own current netstat/tasklist reading",
  "read the guard, run-loop and write-failure source that turns a no-artifact role call into NoEngineeringWrite",
  "ran cargo test --offline, both --list forms and cargo fmt --all --check in my own build directory E:/acc-live-target on E: (550 G free, checked first), one test process at a time, after confirming F: had only 8.3 G",
  "wrote only .spec/bevy/ACCEPTANCE-LIVE-COMPLETION.md in the repository; modified nothing under src/**, tests/**, evidence/**, runs/**, config/**, the registry, the battery, the liveness step, .gitattributes or any frozen document; committed, staged and pushed nothing; used no rm -rf, no wildcard deletion and no git checkout --"
 ]
}
```

# ACCEPTANCE-LIVE-COMPLETION - independent acceptance of the live completion-protocol cost measurement

**Who.** A fresh, independent acceptance pass. It inherited no conclusion from the implementer or
the dispatcher, and treats every number in `.spec/bevy/LIVE-COMPLETION-MEASUREMENT.md` as unverified
until re-derived. **No round, no model call, no engine, no network.** The structured verdict is the
JSON block above, produced by `json.dumps(..., indent=1, ensure_ascii=False)` in
`E:/acc-live/write_acceptance.py` and parsed back out of this written file before the prose was
appended. Helper scripts live outside the repository at `E:/acc-live/`.

**Verdict: `pass`.** Every headline number re-derives from the raw run tree: the round exits **2**
with `NoEngineeringWrite` at iteration 3, retries are **0** across all 8 attempt trajectories, and
the two producing Developer calls are **2.3517x** and **2.6260x** the 1,500,000-token criterion, so
the criterion is genuinely unmet. The central question, however, is where the artefact is weakest:
I can separate what it says it could not. **Iteration 3's no-write failure is pre-existing
fragility, not a regression from the prompt change** - `runs/round4-attempt1`, recorded a day before
the prompt-fix commit and carrying the old prompt, failed with an identical result shape at the same
gate. The artefact is not wrong about the round; it is too cautious about the attribution, and it is
wrong (over-strong) in one sentence that calls the completion protocol irrelevant to the criterion.

## 1. Headline: the exit codes, the failing iteration and the cost, re-derived

The literal codes come from the experiment's own captured logs, which is stronger than a summary:
`D:/live2/logs/build_hoh.exit` `exit=0`, `init.exit` `exit=0`, `run.exit` `exit=2`, and `run.err`
reads exactly

```
hoh: contract violation: NoEngineeringWrite (no_engineering_write)
```

with `run.started` `2026-10-06T07:06:47+0800` and `run.finished` `2026-10-06T08:28:22+0800`
(81.58 minutes). `runs/completion1/exit_code` and `process_exit_code` both hold `2`.
Iterations 1 and 2 have `ok: true, reason: "ok"`; iteration 3's `result.json` has `ok: false`,
`failed_role: "developer"`, `reason: "contract_violation"` and the warnings
`no_progress` / `role_write_failure` / `no_engineering_write`.

Cost, re-derived by summing `extra.response.usage` over every message that carries it (the same set
`src/runtime/usage.rs::extract_usage` counts) rather than read from the report's table:

| call | report | mine | agree |
|---|---|---|---|
| developer iter-1 | 150 calls, 3,414,645 prompt, 112,921 completion, 3,527,566 total, **2.3517x** | identical | yes |
| developer iter-2 | 150 calls, 3,820,462 prompt, 118,565 completion, 3,939,027 total, **2.6260x** | identical | yes |
| developer iter-3 | 44 calls, 789,257 prompt, 13,770 completion, 803,027 total, 0.5354x | identical | yes |
| planner iter-1/2/3 | 6/6/6 calls; 42,397 / 56,179 / 43,460 prompt; 44,432 / 59,565 / 46,065 total | identical | yes |
| tester iter-1/iter-2 | 98 / 150 calls; 2,310,975 / 3,786,462 prompt; 2,346,685 / 3,839,927 total | identical | yes |
| per-role totals | planner 18 / developer 344 / tester 248 calls | identical | yes |
| developer wall clock | 20.663 / 27.784 / 5.832 min, 54.279 total | identical | yes |

**The criterion is unmet**, by 2.35x and 2.63x on the two producing calls; the only call under
1,500,000 is the iteration-3 call that wrote nothing and failed the round.

## 2. The central question: regression or pre-existing fragility?

**Pre-existing fragility - this would have happened anyway.** Confidence: high.

The separating evidence is a run tree the artefact already names in its own evidence, and never
checked: `runs/round4-attempt1`.

| | `runs/round4-attempt1/iter-3` | `runs/completion1/iter-3` |
|---|---|---|
| recorded | 2026-10-05 02:45 (old prompt) | 2026-10-06 08:28 (new `[completion]`) |
| round `exit_code` | **2** | **2** |
| `ok` / `failed_role` / `reason` | `false` / `developer` / `contract_violation` | `false` / `developer` / `contract_violation` |
| developer `exit_status` | `StepBudgetExceeded` (30 model calls) | `StepBudgetExceeded` (44 model calls) |
| project write | none | none |
| warnings | `no_progress`, `role_write_failure`, `no_engineering_write` | identical |
| `write_failures` | one entry, `artifact_written: false` | byte-identical entry |
| planner plan | asked for real code changes | asked for real code changes |

The prompt change is confined to the completion paragraph. Diffing the delivered system
prompts - `runs/round4-attempt1/iter-3` (pre) against `runs/completion1/iter-3` (post) - produces
exactly one hunk: the old three-line *"end your run with the completion protocol"* replaced by the
new `[completion]` section; the delivered task prompts are byte-identical. The gate that actually
failed is unrelated to that text: `agent.steps_per_artifact: 8` gives
`wrap_up_steps + step_limit / steps_per_artifact = 25 + 150/8 = 43` model calls, enforced
in-call at `src/harness/guard.rs:706-737` (`steps > budget`), and a Developer that spends that
budget reading never writes, so `src/runtime/run_loop.rs:1843-1919` records `no_progress` and
returns `NoEngineeringWrite`.

The same shape also appears in the pre-change live rounds in a milder form: `livecost1` and
`clonefix1` Developer calls ran to 150 with zero format errors and never ran the completion command,
and `round4-attempt1/iter-3`'s last prose was *"Now I have the full picture. Let me check the tools
doc briefly, then write the change."* - it was about to write when the budget cut it. Two further
points cut against a regression: the round-4 repair made the guard count model calls instead of
actions, which gave the Developer **more** room (44 vs 30 calls) before the cut; and the delivered
task prompt still contains the unchanged *"write a real file in the project early"* instruction.

**What the evidence cannot separate** (and what would): the *base rate*. `round4-attempt1` proves
the failure mode is not new, not that the new wording leaves its probability unchanged, and one
round cannot estimate a rate. The run that would separate the residual question is an A/B of the
completion text alone - the same task, model and project, one arm with the old three-line
completion paragraph and one with the new `[completion]` section - repeated enough times to compare
how often the Developer writes before it is cut. Nothing in this round does that, and the artefact
does not claim it does; it simply concludes too little rather than too much on this point.

## 3. The retry claim

**Confirmed, with one count wrong.** Across all **8** attempt trajectories of this round (not the
artefact's 7), no message carries `extra.interrupt_type` of any kind; the `FormatError` count is 0
for every role and iteration. The recorded rounds carry exactly the counts the earlier report
attributed, re-derived from their own messages:

| recording | calls | retry turns | retry prompt tokens |
|---|---|---|---|
| round4 dev iter-1/2/3 | 69 / 125 / 102 | **20 / 10 / 8** | 876,566 / 1,486,702 / 416,910 |
| round4 planner | 23 / 11 / 13 | **8 / 2 / 6** | 89,313 / 20,159 / 67,761 |
| round4 tester | 27 / 37 / 45 | **5 / 4 / 1** | 382,706 / 213,244 / 61,110 |
| livecost1 dev / planner / tester | 150 / 17 / 124 | **0 / 4 / 3** | 0 / 33,395 / 100,603 |
| clonefix1 planner | 9 / 9 / 9 | **3 / 4 / 4** | 17,363 / 32,953 / 36,276 |
| clonefix1 tester (a1/a2/a2) | 126 / 63 / 97 | **3 / 4 / 2** | 116,205 / 88,517 / 76,512 |
| completion1 all roles | 610 across 8 sequences | **0** | **0** |

The four corpus recordings total 38 turns and 2,780,178 retry prompt tokens, as reported. The new
exit is used where the report says: `echo COMPLETE_TASK_AND_SUBMIT_FINAL_OUTPUT` is the last call of
the Planner in all three iterations (call 6 of 6) and of the Tester in iteration 1 (call 98 of 98),
and appears nowhere in the Developer's 344 calls.

## 4. Trustworthiness of the observation

A string of identity checks hold for **both** launches that actually served a game, not just the
surviving one - the experiment's own snapshots preserve iteration 1's record, so this is verifiable
rather than merely asserted:

| reading | iteration 1 | iteration 2 (surviving) |
|---|---|---|
| nonce (generated pre-spawn, child env only) | `3c840cf2-00dd-42e3-beb4-edb727811980` | `e42b6006-f5e2-4e69-ab48-0d37618b26ea` |
| answered_nonce (BRP `ProcessNonce`) | same | same |
| spawned / answering / listening pid | `57176` / `57176` / `57176` | `49948` / `49948` / `49948` |
| `verified` | `true` | `true` |
| ledger line (nonce, pid, launch image) | line 2, `ffc23b3a-...` | line 4, `e608b3b5-...` |

The ledger holds 5 append-only lines with 5 distinct nonces, pids and launch-image UUIDs, and all
five image directories exist. `round-stop.json` recorded `[50340,57176,41920,49948,54908]`, reaped
`[57176]`, `still_alive: []`, `endpoint_holder: null`, `failure: null`. Nothing survives the round:
as of this acceptance there is no LISTENING socket on 15702/15703 and no `hof_game.exe` or
`hoh.exe`. The only unverifiable identity datum is the report's in-round `netstat` line naming pid
41920 (ledger line 3); it is consistent with the ledger but is a first-party reading.

## 5. The "cheap but empty" call

The only sub-criterion Developer call (803,027 tokens) is iteration 3's, and it is cheap **because
it was aborted**: `StepBudgetExceeded`, 44 model calls against the 43-call budget, `artifact_written:
false`. Its 44 calls are reads (`TASK.md`, `plan.md`, `EVIDENCE_HISTORY.md`, `src/*`, the
deterministic records, powershell `ConvertFrom-Json` probes) plus two writes into `.hoh/scratch`;
no `HOH_WRITE_FILE` against a project path appears anywhere, and `D:/live2/project/src/game.rs` is
still 19,134 bytes - iteration 2's artifact, byte-unchanged. The pipeline then measures the tree
`h_dev_before == h_dev_after`, attaches the `write_failures` entry, and returns
`HofError::contract(NoEngineeringWrite)`.

**This is not the weaker-artifact risk made concrete.** `ACCEPTANCE-RETRY-FIX` C7 predicted a
`Submitted` early end carrying a valid-but-unfinished artifact. What happened is the older, harder
failure: a call that was cut off before writing anything, which fails the round outright. The
distinction is the important one for the next decision: a cheap call produced by cutting the role
short is not a cheap *producing* call, and any future bound must not be satisfiable by one.

## 6. Gate

Own build directory `E:/acc-live-target` on `E:` (550 G free, checked before anything; `F:` had
8.3 G), one test process at a time, no `rm -rf` and no wildcard deletion.

| check | literal exit code | result |
|---|---|---|
| `cargo test --offline` | **0** | **802 passed / 0 failed / 6 ignored**, 60 `test result:` lines, **0** warning lines, 0 error lines |
| `cargo test --offline -- --list` | **0** | 808 test lines |
| `cargo test --offline -- --list --ignored` | **0** | 6 test lines |
| `cargo fmt --all --check` | **0** | 0 bytes of output |

Exactly the stated baseline 802/0/6/808. No test was removed or weakened: `git diff 9d3f488 HEAD --
tests/` touches only `tests/prompt_shell_contract.rs` (+136/-5), the two tests the prompt fix added,
and `git diff 9b74379 HEAD -- src/ config/` is empty.

## 7. Cost levers: what remains open, and is the criterion reachable?

The artefact's recommendation - bound the call count, and do it in a way a writing-nothing call
cannot satisfy - is supported, but it closes one step too far when it calls the completion protocol
"correct and irrelevant to the criterion".

* **Reachable at all?** Not by context alone, and not at the current ceiling. The spike's own
  zero-context floor for the 150-call live Developer call is **2,077,238** prompt tokens, already
  1.39x the criterion; this round's producing calls re-send 22,764 and 25,470 prompt tokens per call
  over 150 calls. To pass, a producing call has to end after roughly **57-63** calls - the same
  mechanism the completion protocol was meant to provide. An early self-exit and a call bound are
  therefore one lever, not a choice between two.
* **Closed:** size caps (floor 2.08 M at C = 0), and prompt caching as a *token-count* lever (it
  moves price, not `prompt_tokens`).
* **Open but insufficient alone:** the working-set window (round4-iter-2 still 1.40x; the ~7.7 KiB
  cap that makes it pass reintroduces the content discard).
* **Open and decisive, with a demonstrated failure mode:** call count. The one bounded call in this
  round is the proof that a bound tight enough to cut cost is also tight enough to cut the write -
  unless the bound is paired with a guarantee that the artifact is written first.

## 8. What I could not establish

* Whether iteration 3 would have written under the old completion prompt - the counterfactual
  cannot be run; my C3 finding is attribution from a pre-change round with the identical shape.
* The base rate of the read-only grind, and whether the new wording changed it; the separating
  experiment is an A/B of the completion text alone, repeated.
* The report's in-round `netstat` reading; only its consistency with the ledger is checkable.
* Plan conformance of the two completed artifacts (they are valid, grew, and passed the 12-step
  battery on the first pass, but that is not the same as implementing the plan).
* Any second provider, model or project shape.
