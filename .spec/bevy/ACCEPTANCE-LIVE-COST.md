# ACCEPTANCE-LIVE-COST — independent acceptance of the live-cost batch (round 6)

Independent, offline acceptance of `.spec/bevy/LIVE-COST-REPORT.md` on `bevy-core` @ `81c9a71`.

No engine, no game, no network, no model call, no round and no Developer call were run; every
figure below comes from raw recorded files or from my own execution of the tree's own tests.

The machine-readable verdict is the JSON block immediately below, serialised by
`F:/hof-acc7-work/write_report.py` and parsed back out of this file after writing.

```json
{
 "schema": "hof-rs / bevy round-6 independent acceptance (live cost batch)",
 "produced_at": "2026-10-05",
 "mode": "independent, offline: no engine, no game, no network, no model call, no round, no developer call",
 "accepted_revision": "81c9a71 (branch bevy-core); the batch's own start tree is fc25c32",
 "working_tree": "DIRTY: .spec/bevy/LIVE-COST-REPORT.md has one uncommitted added line",
 "verdict": "fail",
 "cost_criterion": {
  "text": "total_tokens below 1,500,000 per Developer call (.spec/bevy/ROUND-2-REPORT.md:43)",
  "live_measurement": {
   "calls": 150,
   "prompt_tokens": 3537843,
   "completion_tokens": 113277,
   "total_tokens": 3651120,
   "wall_clock_ms": 1278222,
   "ended_by": "LimitsExceeded",
   "passes": false,
   "ratio_to_target": 2.434
  },
  "projected_post_fix": {
   "lever": "the withdrawn write-free step budget, K = 32",
   "ends_at_call": 76,
   "total_tokens": 1357530,
   "passes": true,
   "ratio_to_target": 0.905,
   "shipped": false
  },
  "statement": "The criterion does NOT pass. The one live measurement fails it at 2.434x. The projected post-fix figure of 1,357,530 would pass, but the lever that produces it was withdrawn and is not in the code, so nothing in the shipped tree produces it. The two bands do not overlap (K <= 37 to pass, K >= 43 to cut no recorded work), so no shipped lever can pass it.",
  "passes": false
 },
 "criteria": [
  {
   "id": "C1-live-measurement-recorded",
   "criterion": "The recorded live Developer call's cost is what the batch reports",
   "pass": true,
   "evidence": "runs/livecost1/iter-1/traj/developer.attempt1.json has exactly 150 messages carrying extra.response.usage; their sums are prompt 3,537,843 / completion 113,277 / total 3,651,120; first call 4,269, last 40,404, max 40,501, mean 23,586. runs/livecost1/iter-1/result.json and usage.json give duration_ms 1,278,222 (= 21.30 min) and exit_status LimitsExceeded with exit_was_limits true; exit_code and process_exit_code are both 0. Measured by my own F:/hof-acc7-work/measure_traj.py over the raw files; every reported figure reproduced exactly."
  },
  {
   "id": "C2-cost-criterion",
   "criterion": "One Developer call costs under 1,500,000 total_tokens",
   "pass": false,
   "evidence": "3,651,120 total tokens = 2.434x the target. The last cumulative total under the target is call 81 at 1,484,934; call 82 is already 1,511,382. The call was ended by the step budget (LimitsExceeded), not by finishing. The criterion is stated at .spec/bevy/ROUND-2-REPORT.md:43 and is one of the two targets in its developer_cost.targets block."
  },
  {
   "id": "C3-budget-not-shipped",
   "criterion": "The write-free step budget is not in the shipped tree",
   "pass": true,
   "evidence": "grep for max_write_free_steps|WriteFreeBudgetExceeded|write_free over the whole repository returns no match; config/hoh.yaml has no such key and src/config.rs has no such field. The implementation is preserved outside the repository at D:/hof-live-work/write-free-budget-WITHDRAWN.patch (45,735 bytes). So the batch's claim 'shipped: false / withdrawn: true / what the withdrawal leaves: no behavioural change' is true of the bytes on disk."
  },
  {
   "id": "C4-rule-replay-reproduces",
   "criterion": "Replaying the rule through my own reconstruction reproduces the abort calls and the cost",
   "pass": true,
   "evidence": "F:/hof-acc7-work/replay.py re-implements parse_directive from src/harness/directive.rs and the counter/point-of-enforcement from the patch's guard.rs hunk, reading the action text from extra.actions (NOT tool_calls, which the fold replaces with a note plus a truncated preview). At K=32: live-iter-1 aborts at call 76 with 1,357,530 total; round4-iter-1 at call 51 with 1,790,635; round4-iter-2 never fires; round4-iter-3 at call 39 with 1,604,038. These match the batch's §4 table exactly."
  },
  {
   "id": "C5-zero-lost-writes",
   "criterion": "The rule loses no recorded write",
   "pass": false,
   "evidence": "FALSE. At K=32 the rule aborts round4-iter-3 at call 39, and the recording contains ten further successful write directives at calls 50, 70, 73, 74, 80, 84, 86, 90, 93, 97 - all cut. The batch's JSON field directive_writes_after_the_end is [] for round4_iter_3 and zero_recorded_directive_writes_lost is true, and the §4 table says 'none'; its own §4 prose ('the rule would have cut genuine repairs') is the correct statement. F:/hof-acc7-work/cut.py shows writes-after-abort = [] only at K>=43."
  },
  {
   "id": "C6-constant-derivation",
   "criterion": "The constant 32 is derived from a measured 31-call legitimate window, leaving margin",
   "pass": false,
   "evidence": "FALSE. The measured write-directive timeline of round4-iter-3 is [6, 50, 70, 73, 74, 80, 84, 86, 90, 93, 97] (F:/hof-acc7-work/timeline.py). There is no write at call 18, and the longest write-free window is 43 calls (6 -> 50), not 31. No trajectory in the batch contains a 31-call window: live 43->150 = 107, iter-1 18->69 = 51, iter-2 72->97 = 24, iter-3 6->50 = 43. The margin is therefore minus eleven calls, not plus one."
  },
  {
   "id": "C7-projection-direction",
   "criterion": "The offline projection understates the folded live cost",
   "pass": true,
   "evidence": "My own framing-independent check (F:/hof-acc7-work/wire.py: sum of prompt_tokens over sum of serialised prefix bytes) gives 0.2615 for round4-iter-2 and 0.3899 for the live call, i.e. the live folded context is 1.49x denser per wire byte; the batch's own framing gives 0.2554 vs 0.3235, 1.27x. The direction and the order of magnitude are confirmed; the absolute constants are framing-dependent."
  },
  {
   "id": "C8-correction-F1",
   "criterion": "iter-2's projected total is 3,007,235",
   "pass": true,
   "evidence": "2,681,282 projected prompt (reproduced by running the tree's own test: cargo test --offline --test context_compaction -- --nocapture prints 'projected_prompt_tokens=2681282') plus the recorded completion 325,953 = 3,007,235. The old 3,034,063 is gone from COST-REPORT.md and FIX-REPORT.md."
  },
  {
   "id": "C9-correction-F2",
   "criterion": "The system prompt is 14,522 content / 14,849 wire bytes",
   "pass": true,
   "evidence": "The live trajectory's system message is 14,522 bytes of content (my measure: system_content_bytes 14522), which is the figure now published. The old 14,783/14,814 appears nowhere. The derived shares check out: 14,849/98,530 wire bytes of iter-2's compacted final call x 25,152 projected tokens = 3,791 (15.1%), and 14,849 wire bytes are 17.7% of iter-2's 10,503,715 compacted wire bytes."
  },
  {
   "id": "C10-correction-F3",
   "criterion": "The over-strong claim is restated as a refused trade, not an impossibility",
   "pass": true,
   "evidence": "COST-REPORT.md line 120 and the criterion-4 disposition now say the tail-0 figure 'bounds only that family' and that a policy keeping 'only the system prompt and the task' projects to 287,657 / 517,368 / 430,085 prompt tokens (369,289 / 843,321 / 516,206 with completion) and 'would pass - what is refused is that trade ... not an impossibility'. FIX-REPORT.md §5 adds an explicit f3_correction block and ends 'So a context-only policy CAN make the criterion pass ... not \"no context-only policy can make it pass\"'. The arithmetic is exact against the recorded completions 81,632 / 325,953 / 86,121."
  },
  {
   "id": "C11-correction-F4",
   "criterion": "The call-count lever pairs are re-derived and 'roughly 85' is withdrawn",
   "pass": true,
   "evidence": "The published pairs reproduce EXACTLY the output of the previous acceptance's independent script F:/hof-acc6-work/composition.py, which I ran: iter-2 first_60 [1152836, 1478789], first_70 [1385772, 1711725], first_80 [1643606, 1969559]; iter-3 first_80 [1180267, 1266388]. 'roughly 85 for iter-3' is withdrawn in FIX-REPORT.md and D302. Caveat recorded as defect D-5: the second component is prompt + the call's FULL completion, and the batch's OWN script D:/hof-live-work/cost_measure.py emits a different second component."
  },
  {
   "id": "C12-correction-F5",
   "criterion": "The stale 'nothing was committed' statement is corrected",
   "pass": true,
   "evidence": "FIX-REPORT.md's scope field and §1 now read 'Nothing was committed, staged or pushed at the time; the batch's whole change set, including this report, is now COMMITTED as 6290f77 on branch bevy-core (defect F-5...)'. git cat-file confirms 6290f77 exists and is an ancestor of HEAD."
  },
  {
   "id": "C13-decisions-append-only",
   "criterion": "DECISIONS.md is appended only, and supersessions say so without rewriting",
   "pass": true,
   "evidence": "git show fc25c32:DECISIONS.md is a byte prefix of the current DECISIONS.md (current.startswith(previous) is True) with 8,181 bytes appended. D302 names D300's 'not committed' sentence and D301's title and §(e) as superseded and restates them, leaving D301's own text intact. The append is D302 only."
  },
  {
   "id": "C14-gate-cargo-test",
   "criterion": "cargo test --offline exits 0 with the baseline counts",
   "pass": true,
   "evidence": "My own build directory D:\\hof-acc7-target. Literal exit code 0. 58 'test result:' lines summing to 766 passed / 0 failed / 6 ignored = 772 listed. --list exit 0 with 772 names; --list --ignored exit 0 with the same 6 real-engine tests the batch names. Zero cargo/rustc/hoh processes before and after."
  },
  {
   "id": "C15-gate-fmt-warnings",
   "criterion": "cargo fmt --all --check exits 0 and there are zero warnings",
   "pass": true,
   "evidence": "fmt exit 0 with 0 bytes on stdout and 0 bytes on stderr. Zero lines containing 'warning:' in either the test stdout or stderr."
  },
  {
   "id": "C16-no-test-removed",
   "criterion": "No test was removed",
   "pass": true,
   "evidence": "Structurally guaranteed by the commit: git diff --name-only fc25c32 81c9a71 -- src tests config is EMPTY; the batch's whole change set is four markdown files. Counts equal the stated baseline exactly, and my 772 listed names are set-equal to the batch's own recorded list (D:/hof-live-logs/list.out)."
  },
  {
   "id": "C17-disk-discipline",
   "criterion": "Free space was checked first and only own regenerable targets were removed",
   "pass": true,
   "evidence": "Checked before building: D: 269 G and F: 66 G available, so no space had to be freed and none was freed from anyone else's directory. My own build directory D:\\hof-acc7-target was verified to be a cargo target directory (.rustc_info.json present AND a debug/ subtree), measured at 10,224,326,407 bytes = 9.522 GiB / 11,916 files, printed, and removed with Python shutil.rmtree over that literal path (no rm -rf, no wildcard). D: returned from 261 G to 269 G available, its pre-build value."
  },
  {
   "id": "C18-no-key-material",
   "criterion": "No key-shaped material in the tracked tree",
   "pass": true,
   "evidence": "git grep over the tracked tree for sk-[A-Za-z0-9]{16,} matches only fixtures in tests/credential_scan.rs. The only real key material is in two gitignored files, runs/round1/iter-1/traj/developer.attempt1.json and runs/round1b/iter-1/traj/tester.attempt1.json, whose 51-character tokens both hash to sha256 5cf81e8f... - the fingerprint 5cf81e8f the batch names. No key in config/hoh.yaml or in any tracked file."
  },
  {
   "id": "C19-frozen-docs",
   "criterion": "Frozen documents and other batches' reports are unmodified",
   "pass": true,
   "evidence": "git diff --stat fc25c32 81c9a71 lists only .spec/bevy/COST-REPORT.md, .spec/bevy/FIX-REPORT.md, .spec/bevy/LIVE-COST-REPORT.md and DECISIONS.md. REQUIREMENTS.md, DESIGN-OVERVIEW.md, DESIGN-DETAIL.md, PRD.md, the spike reports, the round-1/2/3/4 reports and the three acceptance documents are untouched relative to this batch's own start tree."
  },
  {
   "id": "C20-tree-coherence",
   "criterion": "The ledger, identity, tripwire, fold and resume still hold together",
   "pass": true,
   "evidence": "The batch ships no code: the mechanism can only be inherited, and it is green. runs/bevy-livecost1/launch-ledger.jsonl holds three launches with distinct nonces, pids and launch images, and the second launch's nonce f257740a is the one meta.json records as the verified game endpoint. The tests that own these mechanisms (engine_identity, resume_round, context_compaction, repeated_action, secret_hygiene, artifact_hygiene, push_gate) are all in the 766 that passed."
  },
  {
   "id": "C21-nothing-pushed",
   "criterion": "Nothing was pushed",
   "pass": true,
   "evidence": "The only remote ref is origin/master (6553afe), and no remote ref contains 81c9a71. bevy-core is a local-only branch. git remote -v shows the origin URL but no bevy-core has ever been pushed."
  },
  {
   "id": "C22-tree-matches-head",
   "criterion": "The accepted tree is the committed tree",
   "pass": false,
   "evidence": "git status --porcelain shows ' M .spec/bevy/LIVE-COST-REPORT.md'. HEAD's blob is 34,458 bytes; the worktree's is 34,714. The single uncommitted added line is the re_run_on_the_final_tree claim. A push of HEAD would omit it, so the tree this acceptance examined is not the tree that would be pushed."
  }
 ],
 "defects": [
  {
   "id": "A-1-zero-lost-writes-false",
   "severity": "high",
   "what": "The batch's headline safety claim is false: replaying the shipped rule at K=32 cuts ten recorded write directives in round4-iter-3 (calls 50, 70, 73, 74, 80, 84, 86, 90, 93, 97), not none. The JSON fields directive_writes_after_the_end ([] for round4_iter_3) and zero_recorded_directive_writes_lost (true), and the §4 table cell 'none', contradict the report's own §4 prose and its band analysis. The metric appears to be degenerate: the replay loop breaks at the abort, so a 'writes after the end' list gathered inside that loop is always empty.",
   "reproduction": "PYTHONIOENCODING=utf-8 python F:/hof-acc7-work/cut.py  ->  at K=32, round4-iter-3 abort=39, writes after abort: [50, 70, 73, 74, 80, 84, 86, 90, 93, 97]; only at K=43 is the list empty."
  },
  {
   "id": "A-2-constant-derivation-wrong",
   "severity": "high",
   "what": "The derivation of the constant 32 is factually wrong, so the constant has no margin at all. The withdrawn patch's config/hoh.yaml and src/config.rs doc comments say the longest recorded legitimate write-free stretch is round-4 iter-3's 31 calls, 'its write at call 18, its next at 50', hence '32 = 31 + 1'. Measured, iter-3 has no write at call 18 and its longest write-free window is 43 calls (6 -> 50); the live call itself has 107 (43 -> 150). 32 is eleven calls BELOW the only legitimate window in the evidence, not one above it - which is exactly why it cuts A-1's ten writes.",
   "reproduction": "PYTHONIOENCODING=utf-8 python F:/hof-acc7-work/timeline.py  ->  round4-iter-3 directive write calls [6, 50, 70, ...], longest gap 43 at bounds (6, 50); no trajectory contains a 31-call window."
  },
  {
   "id": "A-3-live-write-profile-wrong",
   "severity": "high",
   "what": "The live call's write profile is misstated in the batch report and in D302. Both say the last change to a project file was at call 44 and that calls 45-150 'changed no project file' (report: 106 calls, 62.7% of the call's tokens). extra.actions contains two further project-file writes after that: call 95 (PowerShell Set-Content on src\\game.rs rewriting COIN_A_X, COIN_B_X, GOAL_X, MOVE_SPEED) and call 139 (PowerShell Set-Content on src\\game.rs rewriting GOAL_HALF_WIDTH and adding WALK_LIMIT_X). The upstream detector D:/hof-live-work/project_writes.py only counts HOH_WRITE_FILE directives, so every shell write is invisible to it - including the call-44 write it does report, which came from a separate script. The error propagates into DECISIONS.md D302.",
   "reproduction": "PYTHONIOENCODING=utf-8 python F:/hof-acc7-work/shellwrites.py  ->  live-iter-1 hits at calls 17, 44, 95, 139; PYTHONIOENCODING=utf-8 python F:/hof-acc7-work/verify_calls.py prints the full commands."
  },
  {
   "id": "A-4-dirty-tree",
   "severity": "medium",
   "what": "The working tree is not the committed tree. .spec/bevy/LIVE-COST-REPORT.md carries one uncommitted added line ('re_run_on_the_final_tree') that is absent from HEAD 81c9a71. Because a pass verdict authorises the first push of this branch, the artefact being judged and the artefact that would be pushed are not the same bytes. The re-run it claims is at least consistent: my own independent gate run reproduces the same 766/0/6/772 on the current tree.",
   "reproduction": "git -C F:/moonbit-hof-rs status --porcelain  ->  ' M .spec/bevy/LIVE-COST-REPORT.md'; PYTHONIOENCODING=utf-8 python F:/hof-acc7-work/gitcheck.py prints the one-line diff."
  },
  {
   "id": "A-5-lever-provenance",
   "severity": "medium",
   "what": "The F-4 lever pairs are attributed to 'my own copy of the method and the acceptance's independent composition.py'. The composition.py half is true and I reproduced it. The 'own copy' half is not: the batch's own D:/hof-live-work/cost_measure.py emits a different second component, because it adds the completion tokens recorded UP TO N while the published pairs add the call's FULL completion total. For iter-2 first_60 the script gives [1152836, 1386920] against the published [1152836, 1478789]. Consequently the published 'roughly 61 calls for iter-2' is a linear interpolation of the conservative pairs, while cost_measure.py's own computed crossing is 64.8 (below at 64 = 1,477,946, above at 65 = 1,504,428). The convention is not stated where the pairs are published.",
   "reproduction": "PYTHONIOENCODING=utf-8 python D:/hof-live-work/cost_measure.py  ->  lever.iter-2 first_60 [1152836, 1386920], crossing.crossing_N 64.8; PYTHONIOENCODING=utf-8 python F:/hof-acc6-work/composition.py  ->  iter-2 first_60 = [1152836, 1478789]."
  },
  {
   "id": "A-6-stale-commit-accounting",
   "severity": "low",
   "what": "The F-5 pattern recurs. DECISIONS.md D302 (which is itself committed in 81c9a71) ends its discipline line with the claim that the batch was not committed and not pushed, which is stale now that D302 ships inside a commit. The commit's own subject, 'bound it with a write-free step budget', also asserts the opposite of its body: the commit touches no source file and the budget was withdrawn.",
   "reproduction": "git -C F:/moonbit-hof-rs log -1 --format=%s 81c9a71; git show --stat 81c9a71; PYTHONIOENCODING=utf-8 python F:/hof-acc7-work/dec.py  ->  D302's discipline line."
  }
 ],
 "risks": [
  {
   "id": "R-1",
   "risk": "Only one live Developer call has ever been measured, a first-iteration-shaped call on a fresh project. Whether an iteration-2-shaped call (round-4 iter-2: 125 calls, 24 writes, 13,091,431 tokens) is anywhere near the target is unmeasured.",
   "why_it_matters": "The criterion is stated per Developer call, and the recorded iter-2 is 8.7x the target on the old code. Closing the criterion on one iteration-1 call would not close it."
  },
  {
   "id": "R-2",
   "risk": "The only signal that can see the writes the roles actually make is a fingerprint of the artifact tree, and no offline replay may execute the recorded shell commands, so it cannot be validated without another live round.",
   "why_it_matters": "The batch's own next-step recommendation depends on a mechanism that has never been measured even once."
  },
  {
   "id": "R-3",
   "risk": "The withdrawn patch remains on disk at D:/hof-live-work/write-free-budget-WITHDRAWN.patch with the false 31-call derivation in its config and config.rs doc comments, and with K=32.",
   "why_it_matters": "Re-applying the preserved artefact without correcting A-2 reintroduces A-1 exactly."
  },
  {
   "id": "R-4",
   "risk": "The projected prompt figures (875,647 / 2,681,282 / 1,663,325) are pinned in the tree only as prose: tests/context_compaction.rs::the_documented_projection_is_the_measured_one asserts those strings appear in src/config.rs, and the replay test asserts only projected < recorded.",
   "why_it_matters": "A fold change that silently moved the projection by 20% would keep the gate green. I did reproduce the figures by running the test with --nocapture, so they are correct today, but the tree does not defend them."
  },
  {
   "id": "R-5",
   "risk": "No artifact gate was evaluated at call 76, the point the withdrawn rule would have ended the live call. Launchability is only known for the final state at call 150.",
   "why_it_matters": "The withdrawn lever's cost figure (0.905x) is only interesting if the artifact at that point was still launchable; that is untested."
  },
  {
   "id": "R-6",
   "risk": "The deadlock is real and remains open: to pass, the budget must end the live call by call 81 (K <= 37); to leave the recorded calls' artifact work alone it must not fire before round-4 iter-3's call 50 (K >= 43). 37 < 43.",
   "why_it_matters": "I independently confirmed both bounds (cumulative target crossing at calls 81/82, and the 43-call window with real shell edits to src/game.rs at calls 8 and 22). No shipped lever meets the criterion, so no code change in this batch can make the criterion pass."
  }
 ],
 "unverified": [
  "The intermediate lever pairs at N = 40/60/70/80/100. I did not write my own implementation of compact_history, so I did not re-derive them from raw wire bytes. I confirmed (a) that they equal the output of the previous acceptance's independent F:/hof-acc6-work/composition.py, (b) that their prompt components equal the batch's own cost_measure.py, and (c) that the full-call projections they are built from are exactly what the tree's own Rust test prints when I run it.",
  "Whether the PowerShell commands at live calls 95 and 139 actually changed bytes. Executing recorded shell commands is forbidden, so A-3 rests on the recorded command text (PowerShell Set-Content writing src\\game.rs) plus the fact that the harness records the action it executed. The report's claim that nothing after call 44 touched a project file is false on the write commands alone, which is enough to refute it.",
  "The absolute tokens-per-wire-byte constants (live 0.323468 vs the round-4 fit 0.255366). The wire framing is the harness's own serialiser, which I did not reproduce; my framing gives 0.3899 vs 0.2615. The direction and the order of magnitude are confirmed, the exact 26.7% is not.",
  "The re_run_on_the_final_tree claim beyond the presence of gate artefacts timestamps at 17:59 and my own reproduction of the same numbers on the current tree. I cannot distinguish a genuine second full gate run from a re-labelling.",
  "The tester's and second/third iterations' cost. The criterion is stated for the Developer call only; the tester spent 124 calls / 2,811,555 tokens and was not judged here."
 ]
}
```

## 0. Verdict in one paragraph

**Fail**, and not because of the process — because of the number. The live measurement is real and
recorded exactly as reported (150 calls / 3,537,843 prompt / 113,277 completion / 3,651,120 total /
1,278,222 ms / ended by `LimitsExceeded` / artifact written and launchable), and it fails the one
criterion this batch was built to close by 2.434x. The batch then did the honest thing: it implemented
a write-free step budget, measured it through its own guard, found it would cut real work, and withdrew
it before shipping. The repository therefore carries no behavioural change and the criterion cannot
pass on it. On top of that I found three substantive reporting defects — the headline "zero lost
writes" claim is false, the `32 = 31 + 1` derivation of the constant is wrong (the real window is 43,
so the margin is −11), and the live call's write profile is misstated. A pass here would authorise a
push of a tree that fails the criterion it exists to meet, and a tree that is not even the committed one.

## 1. Per-item results

| id | criterion | result | evidence |
|---|---|---|---|
| C1-live-measurement-recorded | The recorded live Developer call's cost is what the batch reports | **pass** | runs/livecost1/iter-1/traj/developer.attempt1.json has exactly 150 messages carrying extra.response.usage; their sums are prompt 3,537,843 / completion 113,277 / total 3,651,120; first call 4,269, last 40,404, max 40,501, mean 23,586. runs/livecost1/iter-1/result.json and usage.json give duration_ms 1,278,222 (= 21.30 min) and exit_status LimitsExceeded with exit_was_limits true; exit_code and process_exit_code are both 0. Measured by my own F:/hof-acc7-work/measure_traj.py over the raw files; every reported figure reproduced exactly. |
| C2-cost-criterion | One Developer call costs under 1,500,000 total_tokens | **FAIL** | 3,651,120 total tokens = 2.434x the target. The last cumulative total under the target is call 81 at 1,484,934; call 82 is already 1,511,382. The call was ended by the step budget (LimitsExceeded), not by finishing. The criterion is stated at .spec/bevy/ROUND-2-REPORT.md:43 and is one of the two targets in its developer_cost.targets block. |
| C3-budget-not-shipped | The write-free step budget is not in the shipped tree | **pass** | grep for max_write_free_steps\|WriteFreeBudgetExceeded\|write_free over the whole repository returns no match; config/hoh.yaml has no such key and src/config.rs has no such field. The implementation is preserved outside the repository at D:/hof-live-work/write-free-budget-WITHDRAWN.patch (45,735 bytes). So the batch's claim 'shipped: false / withdrawn: true / what the withdrawal leaves: no behavioural change' is true of the bytes on disk. |
| C4-rule-replay-reproduces | Replaying the rule through my own reconstruction reproduces the abort calls and the cost | **pass** | F:/hof-acc7-work/replay.py re-implements parse_directive from src/harness/directive.rs and the counter/point-of-enforcement from the patch's guard.rs hunk, reading the action text from extra.actions (NOT tool_calls, which the fold replaces with a note plus a truncated preview). At K=32: live-iter-1 aborts at call 76 with 1,357,530 total; round4-iter-1 at call 51 with 1,790,635; round4-iter-2 never fires; round4-iter-3 at call 39 with 1,604,038. These match the batch's §4 table exactly. |
| C5-zero-lost-writes | The rule loses no recorded write | **FAIL** | FALSE. At K=32 the rule aborts round4-iter-3 at call 39, and the recording contains ten further successful write directives at calls 50, 70, 73, 74, 80, 84, 86, 90, 93, 97 - all cut. The batch's JSON field directive_writes_after_the_end is [] for round4_iter_3 and zero_recorded_directive_writes_lost is true, and the §4 table says 'none'; its own §4 prose ('the rule would have cut genuine repairs') is the correct statement. F:/hof-acc7-work/cut.py shows writes-after-abort = [] only at K>=43. |
| C6-constant-derivation | The constant 32 is derived from a measured 31-call legitimate window, leaving margin | **FAIL** | FALSE. The measured write-directive timeline of round4-iter-3 is [6, 50, 70, 73, 74, 80, 84, 86, 90, 93, 97] (F:/hof-acc7-work/timeline.py). There is no write at call 18, and the longest write-free window is 43 calls (6 -> 50), not 31. No trajectory in the batch contains a 31-call window: live 43->150 = 107, iter-1 18->69 = 51, iter-2 72->97 = 24, iter-3 6->50 = 43. The margin is therefore minus eleven calls, not plus one. |
| C7-projection-direction | The offline projection understates the folded live cost | **pass** | My own framing-independent check (F:/hof-acc7-work/wire.py: sum of prompt_tokens over sum of serialised prefix bytes) gives 0.2615 for round4-iter-2 and 0.3899 for the live call, i.e. the live folded context is 1.49x denser per wire byte; the batch's own framing gives 0.2554 vs 0.3235, 1.27x. The direction and the order of magnitude are confirmed; the absolute constants are framing-dependent. |
| C8-correction-F1 | iter-2's projected total is 3,007,235 | **pass** | 2,681,282 projected prompt (reproduced by running the tree's own test: cargo test --offline --test context_compaction -- --nocapture prints 'projected_prompt_tokens=2681282') plus the recorded completion 325,953 = 3,007,235. The old 3,034,063 is gone from COST-REPORT.md and FIX-REPORT.md. |
| C9-correction-F2 | The system prompt is 14,522 content / 14,849 wire bytes | **pass** | The live trajectory's system message is 14,522 bytes of content (my measure: system_content_bytes 14522), which is the figure now published. The old 14,783/14,814 appears nowhere. The derived shares check out: 14,849/98,530 wire bytes of iter-2's compacted final call x 25,152 projected tokens = 3,791 (15.1%), and 14,849 wire bytes are 17.7% of iter-2's 10,503,715 compacted wire bytes. |
| C10-correction-F3 | The over-strong claim is restated as a refused trade, not an impossibility | **pass** | COST-REPORT.md line 120 and the criterion-4 disposition now say the tail-0 figure 'bounds only that family' and that a policy keeping 'only the system prompt and the task' projects to 287,657 / 517,368 / 430,085 prompt tokens (369,289 / 843,321 / 516,206 with completion) and 'would pass - what is refused is that trade ... not an impossibility'. FIX-REPORT.md §5 adds an explicit f3_correction block and ends 'So a context-only policy CAN make the criterion pass ... not "no context-only policy can make it pass"'. The arithmetic is exact against the recorded completions 81,632 / 325,953 / 86,121. |
| C11-correction-F4 | The call-count lever pairs are re-derived and 'roughly 85' is withdrawn | **pass** | The published pairs reproduce EXACTLY the output of the previous acceptance's independent script F:/hof-acc6-work/composition.py, which I ran: iter-2 first_60 [1152836, 1478789], first_70 [1385772, 1711725], first_80 [1643606, 1969559]; iter-3 first_80 [1180267, 1266388]. 'roughly 85 for iter-3' is withdrawn in FIX-REPORT.md and D302. Caveat recorded as defect D-5: the second component is prompt + the call's FULL completion, and the batch's OWN script D:/hof-live-work/cost_measure.py emits a different second component. |
| C12-correction-F5 | The stale 'nothing was committed' statement is corrected | **pass** | FIX-REPORT.md's scope field and §1 now read 'Nothing was committed, staged or pushed at the time; the batch's whole change set, including this report, is now COMMITTED as 6290f77 on branch bevy-core (defect F-5...)'. git cat-file confirms 6290f77 exists and is an ancestor of HEAD. |
| C13-decisions-append-only | DECISIONS.md is appended only, and supersessions say so without rewriting | **pass** | git show fc25c32:DECISIONS.md is a byte prefix of the current DECISIONS.md (current.startswith(previous) is True) with 8,181 bytes appended. D302 names D300's 'not committed' sentence and D301's title and §(e) as superseded and restates them, leaving D301's own text intact. The append is D302 only. |
| C14-gate-cargo-test | cargo test --offline exits 0 with the baseline counts | **pass** | My own build directory D:\hof-acc7-target. Literal exit code 0. 58 'test result:' lines summing to 766 passed / 0 failed / 6 ignored = 772 listed. --list exit 0 with 772 names; --list --ignored exit 0 with the same 6 real-engine tests the batch names. Zero cargo/rustc/hoh processes before and after. |
| C15-gate-fmt-warnings | cargo fmt --all --check exits 0 and there are zero warnings | **pass** | fmt exit 0 with 0 bytes on stdout and 0 bytes on stderr. Zero lines containing 'warning:' in either the test stdout or stderr. |
| C16-no-test-removed | No test was removed | **pass** | Structurally guaranteed by the commit: git diff --name-only fc25c32 81c9a71 -- src tests config is EMPTY; the batch's whole change set is four markdown files. Counts equal the stated baseline exactly, and my 772 listed names are set-equal to the batch's own recorded list (D:/hof-live-logs/list.out). |
| C17-disk-discipline | Free space was checked first and only own regenerable targets were removed | **pass** | Checked before building: D: 269 G and F: 66 G available, so no space had to be freed and none was freed from anyone else's directory. My own build directory D:\hof-acc7-target was verified to be a cargo target directory (.rustc_info.json present AND a debug/ subtree), measured at 10,224,326,407 bytes = 9.522 GiB / 11,916 files, printed, and removed with Python shutil.rmtree over that literal path (no rm -rf, no wildcard). D: returned from 261 G to 269 G available, its pre-build value. |
| C18-no-key-material | No key-shaped material in the tracked tree | **pass** | git grep over the tracked tree for sk-[A-Za-z0-9]{16,} matches only fixtures in tests/credential_scan.rs. The only real key material is in two gitignored files, runs/round1/iter-1/traj/developer.attempt1.json and runs/round1b/iter-1/traj/tester.attempt1.json, whose 51-character tokens both hash to sha256 5cf81e8f... - the fingerprint 5cf81e8f the batch names. No key in config/hoh.yaml or in any tracked file. |
| C19-frozen-docs | Frozen documents and other batches' reports are unmodified | **pass** | git diff --stat fc25c32 81c9a71 lists only .spec/bevy/COST-REPORT.md, .spec/bevy/FIX-REPORT.md, .spec/bevy/LIVE-COST-REPORT.md and DECISIONS.md. REQUIREMENTS.md, DESIGN-OVERVIEW.md, DESIGN-DETAIL.md, PRD.md, the spike reports, the round-1/2/3/4 reports and the three acceptance documents are untouched relative to this batch's own start tree. |
| C20-tree-coherence | The ledger, identity, tripwire, fold and resume still hold together | **pass** | The batch ships no code: the mechanism can only be inherited, and it is green. runs/bevy-livecost1/launch-ledger.jsonl holds three launches with distinct nonces, pids and launch images, and the second launch's nonce f257740a is the one meta.json records as the verified game endpoint. The tests that own these mechanisms (engine_identity, resume_round, context_compaction, repeated_action, secret_hygiene, artifact_hygiene, push_gate) are all in the 766 that passed. |
| C21-nothing-pushed | Nothing was pushed | **pass** | The only remote ref is origin/master (6553afe), and no remote ref contains 81c9a71. bevy-core is a local-only branch. git remote -v shows the origin URL but no bevy-core has ever been pushed. |
| C22-tree-matches-head | The accepted tree is the committed tree | **FAIL** | git status --porcelain shows ' M .spec/bevy/LIVE-COST-REPORT.md'. HEAD's blob is 34,458 bytes; the worktree's is 34,714. The single uncommitted added line is the re_run_on_the_final_tree claim. A push of HEAD would omit it, so the tree this acceptance examined is not the tree that would be pushed. |

## 2. What I verified myself, and how

### 2.1 The live measurement (item 1)

From `runs/livecost1/iter-1/traj/developer.attempt1.json` I counted the messages carrying
`extra.response.usage` and summed them: **150** calls, **3,537,843** prompt, **113,277** completion,
**3,651,120** total; first call 4,269, last 40,404, maximum 40,501, mean 23,586. The system message is
**14,522 bytes** of content. `result.json`/`usage.json` give `duration_ms 1,278,222` (21.30 min) and
`exit_status LimitsExceeded` with `exit_was_limits true`; `exit_code` and `process_exit_code` are both
**0**. The artifact was written: `evidence_diff` added `src/sim_tests.rs` and modified `src/game.rs`
and `src/main.rs`, `artifact_valid true`, and the artifact gate recorded `launchable true` at the end
of the call. **Every figure the batch reports is exactly what the raw files show.**

One correction to *when* the artifact was written: the report says the last change to a project file
was at call 44 and that calls 45–150 changed nothing. That is false — see defect A-3.

**The criterion fails on this measurement: 3,651,120 ≥ 1,500,000, ratio 2.434.** The last cumulative
total under the target is call **81** (1,484,934); call **82** is already 1,511,382.

### 2.2 The write-free step budget — not in the code (item 2)

`grep` for `max_write_free_steps|WriteFreeBudgetExceeded|write_free` over the entire repository
returns **no match**; `config/hoh.yaml` has no such key and `src/config.rs` has no such field. The
batch's own summary is right: implemented, measured, **withdrawn**, preserved outside the repository at
`D:/hof-live-work/write-free-budget-WITHDRAWN.patch`. So there is no shipped rule to attack — what there
is to attack is the *withdrawn* rule's justification, and the batch's report of what it measured.

I reconstructed the rule from the patch's **code** (its `guard.rs` hunk), not from its prose:

1. one model call = one step, and the shared `StepCounter` is incremented before the call's actions run;
2. `write_free_budget_exceeded()` fires when the budget is non-zero **and** an artifact has been written
**and** `steps_since_last_write > budget`;
3. it is consulted for every action that is **not** a write directive — a write action is never refused;
4. **any** successful write directive sets `steps_at_last_write = steps()`; only a write whose path is not
under `.hoh/`, `.git/` or `target/` sets `artifact_written`.

A reproduction trap worth recording: the action text must be read from **`extra.actions`**, not from
`tool_calls[*].function.arguments`. The round-5 fold replaces a superseded payload in `tool_calls` with
`{"[hoh]": "superseded tool call folded: ..."}` plus a **161-character truncated preview**, so the
large write directives parse as `Malformed` and never reset the counter. My first replay, on the wrong
source, put the live call's last write at call 17 instead of 43.

Replayed over all four recorded Developer calls, the rule (K = 32) gives:

| recorded call | calls | last write | abort at | total tokens at abort | vs target | writes the rule cuts |
|---|---|---|---|---|---|---|
| live-iter-1 | 150 | 43 | **76** | **1,357,530** | 0.905 — passes | directive: none; **shell: calls 95 and 139** |
| round4-iter-1 | 69 | 18 | 51 | 1,790,635 | — | none |
| round4-iter-2 | 125 | 116 | never | — | — | none |
| round4-iter-3 | 102 | 6 | **39** | 1,604,038 | — | **directive: 50, 70, 73, 74, 80, 84, 86, 90, 93, 97 (ten)** |

**"Zero lost writes" is refuted** (defect A-1): the rule fires at iter-3's call 39 and the recording
contains ten further successful write directives. The batch's JSON `directive_writes_after_the_end` is
`[]` and `zero_recorded_directive_writes_lost` is `true`; both are wrong for iter-3. Its own §4 prose is
the correct statement — the rule "would have cut genuine repairs". The `[]` looks degenerate: a replay
loop that breaks at the abort can only ever collect an empty "after the end" list.

**The counterexample the task asked for** is the one the batch already stumbled onto, and its size is
misreported. Round-4 iter-3's write-free window runs from its write at call **6** to its next at call
**50** — **43** calls, not 31 — and inside it the role really edits `src\game.rs` at calls **8** and
**22** with `[IO.File]::ReadAllText` + `[IO.File]::WriteAllText`, which the guard cannot see. I also
found a second, independent one the batch did not report: the **live** call's own post-abort tail
contains project-file writes at calls **95** and **139**, so even the live call, whose directive writes
all land before the abort, would lose shell-visible artifact work.

**How much margin really exists: none — the constant is below the evidence.** The patch derives 32 as
"31 + 1" from "round-4 iter-3's write at call 18, its next at 50". Measured, iter-3's write-directive
timeline is `[6, 50, 70, 73, 74, 80, 84, 86, 90, 93, 97]`: there is **no write at call 18**, and the
longest write-free window is **43**. No trajectory in the evidence contains a 31-call window at all
(live 43→150 = 107, iter-1 18→69 = 51, iter-2 72→97 = 24, iter-3 **6→50 = 43**). The true margin is
**−11 calls**. The batch report's own band analysis uses the right 43; only the patch and the D302/§4
derivation line still carry the 31. Only at **K ≥ 43** does the rule cut nothing recorded.

**The bands, re-derived from raw usage:** to pass, the abort must be no later than call 81, and the
abort is `last_visible_write + K + 1 = 43 + K + 1`, so **K ≤ 37**; to leave round-4 iter-3 intact the
rule must not fire before its call 50, so **K ≥ 43**. 37 < 43. I confirm the batch's own conclusion on
its own numbers: the same rule cannot both meet the criterion and leave the recorded work alone.

### 2.3 The five corrected statements (item 3)

* **F-1** — iter-2's projected total is **3,007,235**: 2,681,282 projected prompt + 325,953 recorded
  completion. I reproduced the prompt figure by running the tree's own test:
  `cargo test --offline --test context_compaction -- --nocapture` prints
  `iter-2: ... projected_prompt_tokens=2681282`, and `iter-1: ... =875647`, `iter-3: ... =1663325`,
  plus `tail= 0: ... projected_tokens=1873629`. The old 3,034,063 is gone. **Correct.**
* **F-2** — the system prompt is **14,522 bytes of content**, which the live trajectory's own system
  message measures at exactly 14,522. The old 14,783/14,814 appears nowhere. **Correct**, and the
  derived 17.7% / 3,791-of-25,152 figures check out against the measured wire bytes.
* **F-3** — the over-strong claim is restated. `COST-REPORT.md` and `FIX-REPORT.md` now say the tail-0
  figure "bounds only that family", that a policy keeping "only the system prompt and the task"
  projects to 287,657 / 517,368 / 430,085 prompt (369,289 / 843,321 / 516,206 with completion) and
  **would pass**, and that what is refused is the *trade*, not an impossibility. The arithmetic is exact
  against the recorded completions 81,632 / 325,953 / 86,121. **Correct — this is the correction done
  properly.**
* **F-4** — the pairs reproduce **exactly** the previous acceptance's independent `composition.py`,
  which I ran. "roughly 85 for iter-3" is withdrawn. **Correct on its face**; defect A-5 records that the
  provenance sentence is inaccurate about the batch's own script and that the pairs' second component is
  `prompt + full completion`.
* **F-5** — the stale sentence is corrected and names its own staleness. **Correct.**

The decision entries are **appended only**: `git show fc25c32:DECISIONS.md` is a byte prefix of the
current file (8,181 bytes appended), and **D302** supersedes D300's "not committed" sentence and
D301's title and §(e) by **restating** them, leaving D301's own text untouched. Verified by
`F:/hof-acc7-work/gitcheck.py`.

### 2.4 The gate (item 4)

Run in my own build directory `D:\hof-acc7-target`, after checking free space first (D: 269 G, F: 66 G —
nothing had to be freed and nothing was freed from anyone else's directory). No second test process:
no cargo/rustc/hoh before or after.

| check | result |
|---|---|
| `cargo test --offline` | literal exit code **0**; **766 passed / 0 failed / 6 ignored / 772 listed** over 58 `test result:` lines |
| `cargo test --offline -- --list` | exit 0, **772** names |
| `cargo test --offline -- --list --ignored` | exit 0, the same **6** real-engine tests the batch names |
| `cargo fmt --all --check` | exit 0, **0 bytes** on stdout, 0 on stderr |
| warnings | **0** lines containing `warning:` in test stdout or stderr |
| tests removed | **0** — the batch's entire change set is four markdown files; `git diff --name-only fc25c32 81c9a71 -- src tests config` is empty |
| names equal to the batch's own list | yes, set-equal to all 772 in `D:/hof-live-logs/list.out` |

The gate therefore reproduces the stated baseline exactly (766/0/6/772).

### 2.5 The tree as a whole (item 5)

* **Launch ledger / identity.** `runs/bevy-livecost1/launch-ledger.jsonl` holds three launches, each
  with its own nonce, pid and launch image, each written immediately after the spawn; the second
  launch's nonce `f257740a` is the one `meta.json` records as the verified game endpoint on 15702.
  Coherent.
* **Tripwire, history fold, resume.** The batch ships no source change at all, so these mechanisms can
  only be inherited — and they are green: the tests that own them (`repeated_action`, `context_compaction`,
  `resume_round`, `engine_identity`, `secret_hygiene`, `artifact_hygiene`, `push_gate`) are all inside
  the 766 that passed. There is no patch-shaped drift from *this* batch, because there is no code in it.
* **Key material.** A tracked-tree `git grep` for key shapes matches only fixtures in
  `tests/credential_scan.rs`. The only real key material is in the two known gitignored files,
  `runs/round1/iter-1/traj/developer.attempt1.json` and `runs/round1b/iter-1/traj/tester.attempt1.json`,
  whose 51-character tokens both hash to `5cf81e8f…` — the fingerprint the batch names. No key in
  `config/hoh.yaml` or in any tracked file.
* **Frozen documents.** `git diff --stat fc25c32 81c9a71` is exactly the four markdown files. The
  requirements, designs, PRD, spike reports, round reports and the three earlier acceptance documents
  are untouched relative to this batch's own start tree.
* **DECISIONS.md** is append-only, verified above.
* **Nothing pushed.** The only remote ref is `origin/master`; no remote contains `81c9a71`; `bevy-core`
  is local-only.
* **Disk.** Checked first. My own `D:\hof-acc7-target` was verified a cargo target directory, measured
  at 10,224,326,407 bytes = 9.522 GiB / 11,916 files, printed, and removed with Python `shutil.rmtree`
  over that literal path — no `rm -rf`, no wildcard. D: returned to its pre-build 269 G.
* **But the tree is dirty** (defect A-4): one uncommitted line in `.spec/bevy/LIVE-COST-REPORT.md`.

## 3. Defects

### A-1-zero-lost-writes-false — high

The batch's headline safety claim is false: replaying the shipped rule at K=32 cuts ten recorded write directives in round4-iter-3 (calls 50, 70, 73, 74, 80, 84, 86, 90, 93, 97), not none. The JSON fields directive_writes_after_the_end ([] for round4_iter_3) and zero_recorded_directive_writes_lost (true), and the §4 table cell 'none', contradict the report's own §4 prose and its band analysis. The metric appears to be degenerate: the replay loop breaks at the abort, so a 'writes after the end' list gathered inside that loop is always empty.

Reproduce: PYTHONIOENCODING=utf-8 python F:/hof-acc7-work/cut.py  ->  at K=32, round4-iter-3 abort=39, writes after abort: [50, 70, 73, 74, 80, 84, 86, 90, 93, 97]; only at K=43 is the list empty.

### A-2-constant-derivation-wrong — high

The derivation of the constant 32 is factually wrong, so the constant has no margin at all. The withdrawn patch's config/hoh.yaml and src/config.rs doc comments say the longest recorded legitimate write-free stretch is round-4 iter-3's 31 calls, 'its write at call 18, its next at 50', hence '32 = 31 + 1'. Measured, iter-3 has no write at call 18 and its longest write-free window is 43 calls (6 -> 50); the live call itself has 107 (43 -> 150). 32 is eleven calls BELOW the only legitimate window in the evidence, not one above it - which is exactly why it cuts A-1's ten writes.

Reproduce: PYTHONIOENCODING=utf-8 python F:/hof-acc7-work/timeline.py  ->  round4-iter-3 directive write calls [6, 50, 70, ...], longest gap 43 at bounds (6, 50); no trajectory contains a 31-call window.

### A-3-live-write-profile-wrong — high

The live call's write profile is misstated in the batch report and in D302. Both say the last change to a project file was at call 44 and that calls 45-150 'changed no project file' (report: 106 calls, 62.7% of the call's tokens). extra.actions contains two further project-file writes after that: call 95 (PowerShell Set-Content on src\game.rs rewriting COIN_A_X, COIN_B_X, GOAL_X, MOVE_SPEED) and call 139 (PowerShell Set-Content on src\game.rs rewriting GOAL_HALF_WIDTH and adding WALK_LIMIT_X). The upstream detector D:/hof-live-work/project_writes.py only counts HOH_WRITE_FILE directives, so every shell write is invisible to it - including the call-44 write it does report, which came from a separate script. The error propagates into DECISIONS.md D302.

Reproduce: PYTHONIOENCODING=utf-8 python F:/hof-acc7-work/shellwrites.py  ->  live-iter-1 hits at calls 17, 44, 95, 139; PYTHONIOENCODING=utf-8 python F:/hof-acc7-work/verify_calls.py prints the full commands.

### A-4-dirty-tree — medium

The working tree is not the committed tree. .spec/bevy/LIVE-COST-REPORT.md carries one uncommitted added line ('re_run_on_the_final_tree') that is absent from HEAD 81c9a71. Because a pass verdict authorises the first push of this branch, the artefact being judged and the artefact that would be pushed are not the same bytes. The re-run it claims is at least consistent: my own independent gate run reproduces the same 766/0/6/772 on the current tree.

Reproduce: git -C F:/moonbit-hof-rs status --porcelain  ->  ' M .spec/bevy/LIVE-COST-REPORT.md'; PYTHONIOENCODING=utf-8 python F:/hof-acc7-work/gitcheck.py prints the one-line diff.

### A-5-lever-provenance — medium

The F-4 lever pairs are attributed to 'my own copy of the method and the acceptance's independent composition.py'. The composition.py half is true and I reproduced it. The 'own copy' half is not: the batch's own D:/hof-live-work/cost_measure.py emits a different second component, because it adds the completion tokens recorded UP TO N while the published pairs add the call's FULL completion total. For iter-2 first_60 the script gives [1152836, 1386920] against the published [1152836, 1478789]. Consequently the published 'roughly 61 calls for iter-2' is a linear interpolation of the conservative pairs, while cost_measure.py's own computed crossing is 64.8 (below at 64 = 1,477,946, above at 65 = 1,504,428). The convention is not stated where the pairs are published.

Reproduce: PYTHONIOENCODING=utf-8 python D:/hof-live-work/cost_measure.py  ->  lever.iter-2 first_60 [1152836, 1386920], crossing.crossing_N 64.8; PYTHONIOENCODING=utf-8 python F:/hof-acc6-work/composition.py  ->  iter-2 first_60 = [1152836, 1478789].

### A-6-stale-commit-accounting — low

The F-5 pattern recurs. DECISIONS.md D302 (which is itself committed in 81c9a71) ends its discipline line with the claim that the batch was not committed and not pushed, which is stale now that D302 ships inside a commit. The commit's own subject, 'bound it with a write-free step budget', also asserts the opposite of its body: the commit touches no source file and the budget was withdrawn.

Reproduce: git -C F:/moonbit-hof-rs log -1 --format=%s 81c9a71; git show --stat 81c9a71; PYTHONIOENCODING=utf-8 python F:/hof-acc7-work/dec.py  ->  D302's discipline line.

## 4. Risks

* **R-1** — Only one live Developer call has ever been measured, a first-iteration-shaped call on a fresh project. Whether an iteration-2-shaped call (round-4 iter-2: 125 calls, 24 writes, 13,091,431 tokens) is anywhere near the target is unmeasured.
  *Why it matters:* The criterion is stated per Developer call, and the recorded iter-2 is 8.7x the target on the old code. Closing the criterion on one iteration-1 call would not close it.
* **R-2** — The only signal that can see the writes the roles actually make is a fingerprint of the artifact tree, and no offline replay may execute the recorded shell commands, so it cannot be validated without another live round.
  *Why it matters:* The batch's own next-step recommendation depends on a mechanism that has never been measured even once.
* **R-3** — The withdrawn patch remains on disk at D:/hof-live-work/write-free-budget-WITHDRAWN.patch with the false 31-call derivation in its config and config.rs doc comments, and with K=32.
  *Why it matters:* Re-applying the preserved artefact without correcting A-2 reintroduces A-1 exactly.
* **R-4** — The projected prompt figures (875,647 / 2,681,282 / 1,663,325) are pinned in the tree only as prose: tests/context_compaction.rs::the_documented_projection_is_the_measured_one asserts those strings appear in src/config.rs, and the replay test asserts only projected < recorded.
  *Why it matters:* A fold change that silently moved the projection by 20% would keep the gate green. I did reproduce the figures by running the test with --nocapture, so they are correct today, but the tree does not defend them.
* **R-5** — No artifact gate was evaluated at call 76, the point the withdrawn rule would have ended the live call. Launchability is only known for the final state at call 150.
  *Why it matters:* The withdrawn lever's cost figure (0.905x) is only interesting if the artifact at that point was still launchable; that is untested.
* **R-6** — The deadlock is real and remains open: to pass, the budget must end the live call by call 81 (K <= 37); to leave the recorded calls' artifact work alone it must not fire before round-4 iter-3's call 50 (K >= 43). 37 < 43.
  *Why it matters:* I independently confirmed both bounds (cumulative target crossing at calls 81/82, and the 43-call window with real shell edits to src/game.rs at calls 8 and 22). No shipped lever meets the criterion, so no code change in this batch can make the criterion pass.

## 5. What I could not establish

* The intermediate lever pairs at N = 40/60/70/80/100. I did not write my own implementation of compact_history, so I did not re-derive them from raw wire bytes. I confirmed (a) that they equal the output of the previous acceptance's independent F:/hof-acc6-work/composition.py, (b) that their prompt components equal the batch's own cost_measure.py, and (c) that the full-call projections they are built from are exactly what the tree's own Rust test prints when I run it.
* Whether the PowerShell commands at live calls 95 and 139 actually changed bytes. Executing recorded shell commands is forbidden, so A-3 rests on the recorded command text (PowerShell Set-Content writing src\game.rs) plus the fact that the harness records the action it executed. The report's claim that nothing after call 44 touched a project file is false on the write commands alone, which is enough to refute it.
* The absolute tokens-per-wire-byte constants (live 0.323468 vs the round-4 fit 0.255366). The wire framing is the harness's own serialiser, which I did not reproduce; my framing gives 0.3899 vs 0.2615. The direction and the order of magnitude are confirmed, the exact 26.7% is not.
* The re_run_on_the_final_tree claim beyond the presence of gate artefacts timestamps at 17:59 and my own reproduction of the same numbers on the current tree. I cannot distinguish a genuine second full gate run from a re-labelling.
* The tester's and second/third iterations' cost. The criterion is stated for the Developer call only; the tester spent 124 calls / 2,811,555 tokens and was not judged here.

## 6. Does the cost criterion pass?

**No.** Distinguishing the two figures the task asks me to distinguish:

* the **live measurement** — the one call that was actually run — is **3,651,120 total tokens**
  against a 1,500,000 target: **2.434x, it fails**;
* the **projected post-fix figure** — the withdrawn write-free budget at K = 32 — would end that call at
  **call 76** for **1,357,530 tokens (0.905x) and would pass**, and would pass nothing else that has been
  measured, because no second live call exists;
* and that lever is **not in the shipped tree**: `grep` finds no trace of it in `src/` or
  `config/hoh.yaml`.

So the projected figure passes and the criterion does not. On top of that, the rule that produces the
projected figure was correctly withdrawn because it cuts real work, and the same rule cannot be tuned
into safety: **K ≤ 37 to pass, K ≥ 43 to cut nothing recorded.**

A `pass` verdict would authorise the first push of this branch. I return **fail**: the criterion is
unmet on the shipped tree, the headline safety claim of the batch that tried to meet it is false, the
constant's stated derivation is wrong by eleven calls, and the tree is not the committed one.

