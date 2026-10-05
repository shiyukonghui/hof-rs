# ACCEPTANCE-FIX — structured verdict

```json
{
 "verdict": "fail",
 "task": "independent acceptance of the bevy round-5 repair batch (.spec/bevy/FIX-REPORT.md) and of the whole tree at HEAD 6290f77 on branch bevy-core: --resume semantics, the fold's landing, the spawn-ordering claims, the failed acceptance's AC-1..AC-14, the cost criterion, the gate, and the tree as a whole",
 "revision_measured": "branch bevy-core, HEAD 6290f77, working tree clean (git status --porcelain empty); 19 paths changed against HEAD~1 317cfe3",
 "measured_at": "2026-10-05, offline; no engine, no game, no network, no model call; no round run; nothing written under runs/**",
 "environment": "my build directory D:\\hof-acc6-target (F: is 100% full, so the first attempt at F:\\hof-acc6-target died on 'disk space exhausted' during linking; that failed tree was removed with a Python remove-tree over a printed path and the gate was re-run on D:); helper scripts in F:/hof-acc6-work, logs in F:/hof-acc6-logs; my only write inside the repository is this file; nothing staged, committed or pushed by me",
 "cost_criterion_passes": false,
 "cost_conclusion": "The cost criterion (below 1,500,000 total_tokens per Developer call, ROUND-2-REPORT.md:43) still fails. Independently reproduced: recorded Developer prompt tokens 20,447,131 -> projected 5,220,254 at compact_history_tail=12 (74.47%), i.e. per iteration 875,647 / 2,681,282 / 1,663,325 prompt plus the unchanged completion 81,632 / 325,953 / 86,121 = 957,279 / 3,007,235 / 1,749,446 total. iter-2 is 2.00x and iter-3 1.17x the target; only iter-1 passes. The batch did not shave the system prompt to meet the number and I re-measured enough to confirm that no shaving was taken; its refusal is honest but its supporting claim ('no context-only policy can make it pass') is stronger than the measurement (defect F-3).",
 "criteria": [
  {
   "id": "F1-gate-reproduced",
   "pass": true,
   "evidence": "cargo test --offline with CARGO_TARGET_DIR=D:\\hof-acc6-target: literal exit code 0 (F:/hof-acc6-logs/gate.exit contains '0'); 58 'test result:' lines summing to 766 passed / 0 failed / 6 ignored / 772 listed; 0 occurrences of 'warning:' in gate.out and gate.err; cargo test --offline -- --list exit 0 with 772 names; --list --ignored exit 0 listing exactly the 6 real-engine tests; cargo fmt --all --check exit 0 with 0 bytes on stdout and stderr; tasklist showed no cargo/rustc/hoh before or after. This matches FIX-REPORT's 766/0/6/772 and its delta of +12 over the previous baseline. No second test process ran at any time."
  },
  {
   "id": "F2-no-test-removed",
   "pass": true,
   "evidence": "Literal name-set diff against the previous acceptance's independently recorded 760-name list (F:/hof-acc5-logs/mynames.txt) against my own 772-name list: 0 removed, 12 added (7 resume tests, the AC-8 stored-trajectory test, the AC-9/AC-14 config tests, the AC-13 digest test, the AC-11 delivered-example test, and the new guard/counter tests). 760 + 12 = 772."
  },
  {
   "id": "F3-resume-quarantine-and-session",
   "pass": true,
   "evidence": "run_loop.rs:1128-1132 skips quarantine_previous_evidence when orchestrator.resume, so the resumed round's own .hoh stays in place; run_inner returns the fully-complete summary (line ~1336) before start_round_game (~1348), and run() (1036-1043) calls stop_round_game only when RoundGameSession::started() is true, which is set only on the adapter's Ok(Some(_)) arm (start_round_game at 973-981). Pinned by a_fully_complete_resume_runs_nothing_and_starts_no_game (0 starts, 0 stops, no quarantine dir, .hoh/scratch survives) and a_resume_with_work_restores_the_tree_and_keeps_the_rounds_own_evidence, both of which drive the real run_loop::run and both green in my gate."
  },
  {
   "id": "F4-resume-project-identity",
   "pass": true,
   "evidence": "RunMeta.project is a new #[serde(default)] PathBuf (record.rs); run_inner reads runs/<id>/meta.json and calls check_resume_project before create_dir_all(&workspace), before adapter initialize, before quarantine and before any session (run_loop.rs:1087-1090); resume_project_matches refuses an empty recorded project (an old meta) and accepts only the same absolute path or the same canonical path. Pinned by a_resume_matches_only_the_project_the_run_id_recorded and a_resume_against_another_project_is_refused (through the real run loop: no role, 0 starts, nothing quarantined), green in my gate."
  },
  {
   "id": "F5-resume-restore",
   "pass": true,
   "evidence": "resume_restore_iteration returns plan.completed (the last contiguous ok iteration, 0 when none); restore_resume_workspace reads the version index for that iteration, refuses when absent, hashes the tree before, calls VersionStore::rollback, which purges every non-excluded entry and then re-hashes the restored tree and errors on mismatch; the pre-restore hash is recorded in warnings.log when it differed. Verified at the source that VersionStore::rollback purges covered entries and re-hashes (snapshot.rs:132-155) and that HashExcludes::merged() always prepends '.hoh' and '.git' (policy.rs:38-40), which is why the round's own .hoh survives the purge. Pinned by a_resume_restores_the_interrupted_iterations_start_state (truncated file restored, unfinished file deleted, re-hash) and a_resume_without_the_start_snapshot_is_refused, green in my gate."
  },
  {
   "id": "F6-fold-lands-on-stored-history",
   "pass": true,
   "evidence": "The code moved to the prose's side. run_compacting_agent folds agent.messages itself before every step (compact.rs:431) via compact_history(&mut agent.messages, policy); CountingModel::query now only increments the step counter and forwards messages unchanged (compact.rs:286-303); the vendored DefaultAgent::query sends self.model.query(&self.messages, ...) and then pushes the response into self.messages (F:/RustProjects/mini-swe-agent-rust-mini/rust/src/agent.rs:175-183), and serialize writes self.messages (agent.rs:200-219). So the stored trajectory's prefix is exactly what the last provider call was sent, and the three prose claims (compact.rs:29-30, DECISIONS.md D300(a), COST-REPORT.md 1.1) are true rather than reworded. The AC-8 test drives the real loop with a stub model and environment; green in my gate. I did not reproduce plant P4 (see unverified)."
  },
  {
   "id": "F7-spawn-ordering-code",
   "pass": true,
   "evidence": "launch.rs:457 command.spawn() -> :468 append_ledger(..., ledger_entry(pid, ...)); the nonce is generated at :382 before the spawn and goes into the child environment. The ledger entry's own note, append_ledger/ledger_entry/reap_ledger docs and the call-site comment all say 'after the spawn'. Pinned by adapter::bevy::launch::tests::the_ledger_line_is_written_after_the_spawn_and_says_so, green in my gate."
  },
  {
   "id": "F8-spawn-ordering-documents",
   "pass": true,
   "evidence": "All three false statements are corrected in place: ROUND-4-REPORT-COMPLETE.md:73, :130 (the boolean is now false) and :131, plus ROUND-3-REPORT.md:140; git diff of those two paths is exactly 4 changed lines and nothing else in either file moved. COST-REPORT.md RA-1, FIX-REPORT AC-1, DECISIONS.md D301(c) agree with the code. The only surviving 'before the spawn' strings are (a) inside the corrections themselves, which quote the old wording, and (b) inside ACCEPTANCE-ROUNDS.md and ACCEPTANCE-COST.md, where they are the *statement of the defect*, not a claim that the ordering is that way. No false ordering stands as a claim."
  },
  {
   "id": "F9-AC2-D301-exists",
   "pass": true,
   "evidence": "grep -n '^## D30' DECISIONS.md finds D300 (line 11350) and D301 (line 11417); the three formerly dangling references (D298 twice, D299 once) now resolve to D301. DECISIONS.md is append-only: md5 of head -11414 equals md5 of git show HEAD~1:DECISIONS.md (0538080c85d040d525f8f76d11d496d4) and the diff has a single hunk (@@ -11412,3 +11412,104 @@)."
  },
  {
   "id": "F10-AC3-AC5-AC9-AC13-AC14",
   "pass": true,
   "evidence": "AC-3: D301(g) states the supersession and quotes the measured fit (-38.28 + 0.255366 x bytes, worst residual 1,347); I re-derived both from the recorded trajectories. AC-5: RA-7 is at ACCEPTANCE-ROUNDS.md:137 and COST-REPORT's disposition and not_verified item 6 now say so. AC-9: src/config.rs quotes 875,647 / 2,681,282 / 1,663,325 and '839K' is gone, pinned by the_documented_projection_is_the_measured_one. AC-13: tests/repeated_action.rs now uses hof_rs::harness::guard::output_digest (newly pub) instead of the byte length, with a synthetic equal-length control, pinned by the_round_five_counter_compares_the_guards_digest_not_the_length. AC-14: config/hoh.yaml documents compact_history and compact_history_tail (lines 91-114)."
  },
  {
   "id": "F11-AC11-old-engine-preference",
   "pass": true,
   "evidence": "EXAMPLE_PREFERENCE (src/tools/index.rs) now lists the delivered Bevy semantic tools and the generic BRP verbs; render_tools_markdown_for gained a deterministic fallback that renders the first three visible tools when nothing in the surface matches, so a role's 'Complete call examples' section is never empty. Pinned by tools::index::tests::the_complete_call_examples_are_the_delivered_bevy_tools and tests/tool_discovery.rs, both green. The previous engine's tool names survive only in the embedded tests/fixtures/mcp/tools_list.json snapshot (declared) and in #[cfg(test)] code (declared, in no build product)."
  },
  {
   "id": "F12-cost-reduction-reproduced",
   "pass": true,
   "evidence": "I reproduced the measurement two independent ways. (1) A probe crate outside the repository (F:/hof-acc6-work/probe-crate) that calls the repository's own compact_history and message_wire_bytes over runs/round4/iter-*/traj/developer.attempt1.json prints, for all three iterations and tails 0/2/4/6/8/12/16/24/32, exactly the integers the repository test prints (iter-2 tail 12 compacted 10,503,715 -> projected 2,681,282; tail 0 7,339,794 -> 1,873,629; last call 629,072 -> 98,530 -> 25,152). (2) My own Python re-implementation of compact_history (F:/hof-acc6-work/measure.py, measure2.py) matches that probe byte-for-byte on all 27 iteration/tail totals. Recorded Developer figures also check: 2,544,563 / 12,765,478 / 5,137,090 prompt, 81,632 / 325,953 / 86,121 completion, from runs/round4/iter-*/result.json. The composition the report gives for iter-2 tail 12 also reproduces exactly over the 120 calls where the fold runs: system 1,781,880 + task 163,800 + fold notes 1,812,030 + under-floor 3,011,316 + preserved tail 3,581,624 = 10,350,650, plus the 153,065 bytes of the 5 no-fold calls = 10,503,715."
  },
  {
   "id": "F13-cost-target-met",
   "pass": false,
   "evidence": "The on-record criterion is total_tokens below 1,500,000 per Developer call. Projected totals at tail 12: iter-1 957,279 (passes), iter-2 3,007,235 (2.00x), iter-3 1,749,446 (1.17x); prompt-only 875,647 / 2,681,282 / 1,663,325. The batch's own tail-0 floor, which I reproduced (699,900 / 1,873,629 / 1,430,696 prompt; 781,532 / 2,199,582 / 1,516,817 with completion), leaves iter-2 1.47x and iter-3 1.01x the target even with the verbatim tail removed. The batch does not claim the target and no context change in the batch was made to chase it. This is the criterion that has never passed and it still does not pass."
  },
  {
   "id": "F14-tree-no-keys",
   "pass": true,
   "evidence": "I scanned every non-generated file under the repository root with the repository's own rule (hof_rs::runtime::secrets::looks_key_shaped / key_shaped_tokens) through a second probe binary: 184 files scanned, exactly one finding, tests/credential_scan.rs (the declared FIXTURE_SOURCES entry), token fingerprint 3631b5f1; values were fingerprinted, never printed. config/model.secret.env does not exist. The secret-loading refusal is pinned by tests/credential_scan.rs, green in my gate. The two known gitignored historical files under runs/** were NOT re-fingerprinted in this session (see unverified)."
  },
  {
   "id": "F15-frozen-documents",
   "pass": true,
   "evidence": "git diff --stat HEAD~1 HEAD over REQUIREMENTS.md, PRD.md, DESIGN-OVERVIEW.md, DESIGN-DETAIL.md, ACCEPTANCE-ROUNDS.md, both spike reports, the B1/B2/B3 reports and acceptances, ROUND-1/2/4-REPORT.md, TRUST/STRIP/WRITE-PATH reports is empty. The only modified reports are ROUND-4-REPORT-COMPLETE.md (3 lines: 73, 130, 131) and ROUND-3-REPORT.md (1 line: 140), all of them the RA-1/AC-1 ordering correction the batch declared and this acceptance's AC-12 authorises; nothing else in either file changed."
  },
  {
   "id": "F16-scope-and-nothing-pushed",
   "pass": true,
   "evidence": "The tree is the harness plus the Bevy flow: src/adapter has bevy/, engine.rs, mcp/, mod.rs, test_adapter.rs; src/prompts/skills holds only bevy-dev.md and bevy-testing.md. git for-each-ref shows refs/heads/bevy-core 6290f77 with NO upstream, and refs/remotes/origin/master 6553afe (2026-10-04), which is older than both local branches, so no Bevy work is on the remote. Nothing was staged, committed or pushed by me. (Verified from local refs only, because the acceptance is offline.)"
  }
 ],
 "defects": [
  {
   "id": "F-1",
   "severity": "low",
   "what": "COST-REPORT.md's criterion-4-cost disposition still carries an arithmetic error: it says iter-2 'projects to 2,681,282 prompt + 325,953 completion = 3,034,063'. 2,681,282 + 325,953 = 3,007,235, which is the figure FIX-REPORT, COST-REPORT's own projected_round block and my measurement all give.",
   "reproduction": "grep -n '3,034,063' .spec/bevy/COST-REPORT.md  (line 87); compare .spec/bevy/FIX-REPORT.md's per_developer_call.iter_2.projected_total = 3,007,235; python F:/hof-acc6-work/composition.py prints projected 2,681,282 for iter-2 at tail 12 and the recorded completion is 325,953 (runs/round4/iter-2/result.json)."
  },
  {
   "id": "F-2",
   "severity": "low",
   "what": "The quoted size of the system prompt is wrong and contradicts the report's own composition. COST-REPORT.md 1.1 says '14,783 bytes of content (14,814 of wire)'; FIX-REPORT section 5, D301(g) and COST-REPORT 1.1 all repeat '14,814 wire bytes'. The measured system prompt is 14,522 bytes of content and 14,849 bytes of wire (the same message in all three recorded trajectories), and the composition the report publishes confirms it: system_prompt_bytes 1,781,880 / 120 folded calls = 14,849 exactly.",
   "reproduction": "python F:/hof-acc6-work/composition.py prints 'iter-2 system: content_bytes=14522 wire=14849'; grep -n '14,814\\|14,783' .spec/bevy/COST-REPORT.md .spec/bevy/FIX-REPORT.md DECISIONS.md; python F:/hof-acc6-work/composition.py also prints system=1781880 over folded_calls=120."
  },
  {
   "id": "F-3",
   "severity": "medium",
   "what": "The batch's central refusal argument is stronger than its measurement. FIX-REPORT section 5 and DECISIONS.md D301(e) call the tail-0 projection 'an arithmetic lower bound on any context-only policy' and conclude that 'no context-only policy can make it pass'. The tail-0 computation still replaces every superseded message with a ~200-300 byte note, so it bounds only the fold's own family. A context-only policy that dropped consumed message pairs outright, or kept only the system and task messages, would go far below it: at tail 0 for iter-2 the notes plus the under-floor messages are about 5.2 MB of the 7.34 MB compacted total, so even a crude drop-everything-except-system-and-task policy would project far under 1.5M (about 0.50M prompt + 0.33M completion). The honest statement is the one the batch's practical conclusion needs: no policy that keeps the last 12 messages verbatim and notes each folded payload meets the target, and anything aggressive enough to meet it removes history the role needs to work.",
   "reproduction": "python F:/hof-acc6-work/composition.py (tail-0 total 7,339,794; system 1,781,880 and task 163,800 of it are never foldable); .spec/bevy/FIX-REPORT.md lines 270-283 ('an arithmetic lower bound on any context-only policy') and 570-571 ('no context-only policy can make it pass'); DECISIONS.md D301(e)."
  },
  {
   "id": "F-4",
   "severity": "low",
   "what": "The call-count-lever numbers cannot be reproduced exactly with the disclosed method, and one of the report's conclusions contradicts its own figures. My values (verified Python, same fold, same tail 12, same iter-2 global ratio) are iter-2 first_60 [1,152,836, 1,478,789], first_70 [1,385,772, 1,711,725], first_80 [1,643,606, 1,969,559] against the report's [1,153,140, 1,479,093], [1,384,463, 1,710,416], [1,640,551, 1,966,504] (up to 3,055 tokens, 0.2%, apart); the full-iteration values match exactly. Separately, the text says the target 'needs roughly 85 for iter-3' while the report's own first_80 = [1,179,140, 1,265,261] is already below 1.5M; a linear crossing of its own pair (first_80 1,265,261, first_100 1,702,090) is about 91 calls. The substantive conclusion (about half the round trips) survives, which is why this is low.",
   "reproduction": "python F:/hof-acc6-work/composition.py ('call-count lever' block); .spec/bevy/FIX-REPORT.md call_count_lever (lines 284-334), especially iter_3.first_80."
  },
  {
   "id": "F-5",
   "severity": "low",
   "what": "FIX-REPORT says 'Nothing was committed, staged or pushed', but the batch's whole change set, including that report, is committed as 6290f77 on bevy-core. The statement was presumably true when it was written (the dispatcher commits after the batch), but as a statement about the tree it is now false, and a reader checking the batch's own claims will find it contradicted.",
   "reproduction": "git show --stat HEAD | head; git log -1 --format='%h %s' -> 6290f77 'fix(acceptance): correct the resume side effects, the fold claims and the false statements the acceptance found'; .spec/bevy/FIX-REPORT.md line 508."
  }
 ],
 "risks": [
  "Every number in the cost argument is a projection over recorded trajectories converted by a tokens-per-wire-byte fit calibrated on un-folded source text; the post-fold context is mostly short JSON whose token density is plausibly higher, and no live call has produced the projected tokens. The direction of that error is unmeasured.",
  "The fold replaces consumed payloads with a digest and a first line; a role that can no longer see a payload it wrote may re-derive or re-read it. This is the batch's own stated behavioural risk and cannot be settled offline.",
  "With the tripwire restricted to byte-identical results, a producing Developer call is no longer bounded by it; the binding limits are now the 150-step ceiling and the 3600 s wall clock, both of which previously allowed multi-million-token calls.",
  "The 6 ignored tests are exactly the real-engine ones (the live Bevy contract and the five behaviours, the readiness handshake, the client rebind across two launches), so the launcher's identity handshake and the resume path against a real engine round remain unexercised by the gate.",
  "identity.verified now goes false when the OS TCP table cannot be parsed (a localised Windows state word), even for a launch whose nonce was proved over the wire; the field no longer means only 'identity proved'.",
  "A copy of the repository whose ROUND-4-REPORT-COMPLETE.md line endings are CRLF: the working copy is CRLF while HEAD's blob is LF, so a future diff of that file can show whole-file changes where git's normalised diff shows 3 lines."
 ],
 "unverified": [
  "My own adversarial --resume case was not executed. I established the restore/quarantine/identity behaviour from the source and from the batch's own tests, which the gate ran green (7 new resume tests, two of them through the real run_loop::run), but I did not construct and run the attempt to make a resume land in a wrong state or lose the interrupted round's evidence; in particular I did not observe the purge-and-restore on a workspace with an interrupted round's .hoh and a real VersionStore. What I can say from the code: the rollback purges everything not excluded and re-hashes, and .hoh/.git are always excluded (policy.rs:38-40), so the round's own scratch/deterministic evidence survives the restore. Two smaller observations, not wrong-state paths: run_inner creates runs/<id>/ with create_dir_all before read_run_meta (a refused resume leaves an empty run directory), and a hand-written meta.json with a relative project path would be resolved against the process cwd.",
  "Plant P4 (putting the fold back on a copy and checking that the AC-8 test goes red) was not reproduced on a copy outside the repository. The claim is corroborated by the source (CountingModel no longer folds; the loop folds agent.messages) rather than by my own red run.",
  "The two known gitignored historical evidence files under runs/** were not re-fingerprinted in this session: the full scan of runs/** exceeded my command budget because the recorded trajectories are large, so I have only the previous acceptance's fingerprint 5cf81e8f for them. My clean result covers the browsable/tracked tree, not runs/**.",
  "Whether anything was ever pushed to the remote is verified from local refs only (bevy-core has no upstream, origin/master is 6553afe, older than both local branches).",
  "The exact tracked-file count was not re-derived (the command that would have printed git ls-files | wc -l was part of the timed-out batch); my key scan walked 184 browsable files.",
  "The remaining prose of the frozen round reports was not audited line by line, only the ordering claims this acceptance was asked about.",
  "A live Developer call: whether it produces the projected prompt tokens and whether a role works coherently with 12 verbatim messages remain unmeasured, as the batch itself states."
 ]
}
```

# ACCEPTANCE — the bevy round-5 repair batch and the tree at `6290f77`

- Verdict: **fail** (the cost criterion, the one criterion that has never passed, still does not pass;
  four smaller accuracy defects stand in the batch's own reports)
- Date: 2026-10-05
- Acceptance agent: an independent subagent; no prior context, no implementer or dispatcher conclusion inherited
- Revision measured: branch `bevy-core`, HEAD `6290f77`, working tree clean; 19 paths changed against `HEAD~1` (`317cfe3`)
- Environment: offline — **no engine, no game, no network, no model call, no round**. Nothing written under `runs/**`.
  My build directory is `D:\hof-acc6-target` (my own); helper scripts are in `F:/hof-acc6-work`, logs in `F:/hof-acc6-logs`.
  My only write inside the repository is this file. Nothing was staged, committed or pushed by me.

## 0. Environment note, and what it cost

`F:` is at 100% (`2.3 MiB` free). My first gate run, in `F:\hof-acc6-target`, died during linking with
`rustc-LLVM ERROR: IO failure on output stream: no space on device` (os error 112) and
`LINK : fatal error LNK1140`. That failed tree (6.5 GB) was removed with a Python remove-tree over a
**printed, verified** path, and the whole gate was re-run as one script in my own build directory on `D:`
(298 GB free). No other acceptance's tree was touched, and `rm -rf` was never used.

## 1. Per-item table

| # | Job | Judgement | What I established myself |
|---|---|---|---|
| 1 | reproduce the gate | **pass** | `cargo test --offline`, `CARGO_TARGET_DIR=D:\hof-acc6-target`, literal exit **0** (`$?` written straight to a file); **766 passed / 0 failed / 6 ignored / 772 listed** over **58** `test result:` lines; **0** `warning:` lines in stdout and stderr; `--list` exit 0 with 772 names; `--list --ignored` exit 0 with exactly the 6 real-engine tests; `cargo fmt --all --check` exit 0 emitting **0 bytes**; `tasklist` clean before and after. A literal name-set diff against the previous acceptance's independently recorded 760-name list: **0 removed, 12 added**. |
| 2 | `--resume` quarantine and sessions (AC-6) | **pass** | `run_loop.rs:1128-1132` skips `quarantine_previous_evidence` when resuming; the fully-complete resume returns its summary **before** `start_round_game`, and `run()` stops a session only when `RoundGameSession` was actually set on the adapter's `Ok(Some(_))` arm. Both behaviours are driven through the real `run_loop::run` by two new tests, green in my gate. |
| 3 | `--resume` project identity (AC-7b) | **pass** | `RunMeta.project` (new, `#[serde(default)]`), `read_run_meta` + `check_resume_project` run **before** the workspace is created, before `initialize`, before quarantine and before any launch. A different project is refused by name; a run whose meta predates the field is refused as unprovable. Two tests, one through the real loop (no role, 0 starts, nothing quarantined), green. |
| 4 | what `--resume` restores (AC-7a) | **pass, scope as declared** | It restores the **workspace** to `A_<last completed>` (`A0` when none) with `VersionStore::rollback`, which purges every non-excluded entry, re-hashes, and errors on mismatch; the pre-restore hash is recorded in `warnings.log` when the tree had drifted; a missing snapshot is refused. I verified `.hoh`/`.git` are always excluded (`policy.rs:38-40`), so the round's own scratch and deterministic evidence survive the purge. It does **not** restore the interrupted *call*'s internal work, and does not move this round's `.hoh`. All stated in the CLI help, the `Orchestrator::resume` doc and the round's warning. |
| 5 | the fold (AC-8) | **pass** | The **code** moved, not the prose: the loop calls `compact_history(&mut agent.messages, policy)` before every step, `CountingModel` only counts, and the vendored `DefaultAgent::query` sends `self.messages` and then pushes the response into it (the same `Vec` `save()` writes). The stored trajectory's prefix is therefore exactly what was last sent. The fold's measurement test replays **recorded** round-4 trajectories, which were produced before the fold existed, so it does not depend on the opposite of the prose being true. |
| 6 | ledger ordering (AC-1) | **pass** | `launch.rs:457 spawn` → `:468 append_ledger`; the nonce is generated at `:382`, before the spawn. The entry note, `append_ledger`/`ledger_entry`/`reap_ledger` docs and the call-site comment all say *after the spawn*, pinned by a test that spawns a real child. All three false statements are corrected in place (ROUND-4 lines 73/130/131, ROUND-3 line 140 — git diff is exactly those 4 lines); the survivors are only inside the corrections themselves and inside the two acceptance documents that state the defect. |
| 7 | the remaining failed-acceptance defects | **fixed, one arithmetic slip** | AC-2/AC-3: `D301` now exists and supersedes D298(e)'s formula; DECISIONS.md is append-only to `HEAD~1` (first 11,414 lines hash identically, one hunk). AC-4/AC-5: the RA-4 and RA-7 dispositions now state the facts. AC-9: `src/config.rs` carries the measured projection. AC-10: the like-for-like figures are in place — **but** the criterion-4-cost disposition still says `2,681,282 + 325,953 = 3,034,063` (defect **F-1**). AC-11/AC-13/AC-14 as claimed. |
| 8 | the cost criterion | **still fails** | See §2. The reduction is real and I reproduced it byte-for-byte; the target is not met and no context change was made to meet it. Two of the three Developer calls remain above 1.5 M on the projection. |
| 9 | tree as a whole | **clean, with the report caveats** | 184 browsable files scanned with the repository's own key-shape rule: **one** finding, the declared fixture source `tests/credential_scan.rs`; no `config/model.secret.env`. Every frozen document is byte-identical to `HEAD~1` except the two round reports (4 authorised lines). `bevy-core` has **no upstream**; `origin/master` is `6553afe` (2026-10-04), older than both local branches — nothing pushed. |

## 2. The cost criterion, stated exactly

**What I measured, and how.** Two independent routes, both offline:

1. A probe crate **outside** the repository (`F:/hof-acc6-work/probe-crate`) that calls the repository's own
   `compact_history` and `message_wire_bytes` over `runs/round4/iter-*/traj/developer.attempt1.json`, and
   repeats `tests/context_compaction.rs`'s arithmetic. It prints, for all three iterations and
   tails 0/2/4/6/8/12/16/24/32, exactly the integers the repository test prints.
2. My own Python re-implementation of the fold, which matches that probe **byte-for-byte on all 27
   iteration/tail totals** (my first Python run disagreed, and the discrepancy turned out to be an aliasing
   bug in my own script — the nested `tool_calls` dicts were being shared between calls; the corrected
   script matches).

Recorded Developer spend (from `runs/round4/iter-*/result.json`): prompt `2,544,563 / 12,765,478 / 5,137,090`
(total `20,447,131`), completion `81,632 / 325,953 / 86,121` (total `493,706`), total `20,940,837`.

| recorded Developer call | calls | recorded prompt | projected prompt (tail 12) | projected total | recorded total |
|---|---|---|---|---|---|
| iter-1 | 69 | 2,544,563 | **875,647** | 957,279 | 2,626,195 |
| iter-2 | 125 | 12,765,478 | **2,681,282** | **3,007,235** | 13,091,431 |
| iter-3 | 102 | 5,137,090 | **1,663,325** | **1,749,446** | 5,223,211 |
| total | 296 | 20,447,131 | **5,220,254** | 5,713,960 | 20,940,837 |

Prompt-to-prompt the reduction is **74.47 %**; adding the unchanged completion tokens back gives
**72.71 %**. Per-call means fall from 72,939 to about 18,300 prompt tokens.

**Does the criterion pass? No.** The criterion on record is `total_tokens` **below 1,500,000 per Developer
call** (`ROUND-2-REPORT.md:43`). On the projection: iter-1 passes (957,279), **iter-2 is 3,007,235 (2.00x)**
and **iter-3 is 1,749,446 (1.17x)**. The batch does not claim otherwise.

**The floor.** With the verbatim tail removed entirely (`tail = 0`), which I reproduced exactly:
prompt `699,900 / 1,873,629 / 1,430,696`, and with completion `781,532 / 2,199,582 / 1,516,817`. So the
fold's own family cannot reach the target: iter-2 stays at 1.47x and iter-3 at 1.01x. The batch's refusal to
shave the system prompt to hit the number is the right call, and I found **no** shaving in the tree: the
system prompt is unchanged, `compact_history_tail` is still 12, and the fold floor is still 512. Its
*argument* is over-stated, though: the tail-0 figure bounds only the "replace with a note" family, not
"any context-only policy" (defect **F-3**).

**Composition check (iter-2, tail 12, over the 120 calls where the fold runs):** system `1,781,880` +
task `163,800` + fold notes `1,812,030` + under-floor messages `3,011,316` + preserved tail `3,581,624`
= `10,350,650`, plus the 5 no-fold calls' `153,065` bytes = `10,503,715` — the report's composition
reproduces exactly, and it is what pins the system prompt's real wire size at `14,849` bytes (defect **F-2**).

## 3. `--resume`: exactly what it does now

1. **Before anything is touched**: `runs/<id>/meta.json` is read and its `project` must be the configured
   workspace. A different project is refused by name; a meta written before the field existed is refused as
   unprovable, with the alternatives named. `--fresh-workspace`/`--reset-workspace` are rejected by the CLI,
   which also requires the run directory to exist.
2. `plan_resume` decides: every iteration whose `result.json` says `ok: true` is not re-run and its usage,
   gate and version are carried into the summary; the first iteration that is not `ok` runs from its start.
3. **Nothing is quarantined.** `.hoh` in the workspace belongs to the round being resumed.
4. **The start state is restored and verified**: the tree is rolled back to the artifact the last completed
   iteration froze (`A0` when none), `rollback` purges untouched-by-the-snapshot files and re-hashes the
   result, a mismatch is an error, and the pre-restore hash is written into `warnings.log` when the tree had
   drifted. No snapshot → refusal.
5. **A resume with nothing to run starts and stops no game session**, and a refused resume starts nothing.

**What is not restored**, in the same places: the interrupted *call*'s internal work (there is no role-level
checkpoint), and this round's own `.hoh` scratch and raw deterministic evidence, which is deliberately left
in place.

**My adversarial reading** (not executed — see §5): the two ways I expected to break it are closed.
(i) The purge inside `rollback` cannot eat the round's own evidence because `.hoh` is unconditionally in the
exclude set. (ii) The rollback re-hashes, so a restore that did not land is an error rather than a quiet
wrong state. Two small observations, neither a wrong-state path: `run_inner` calls
`create_dir_all(&run_dir)` *before* `read_run_meta`, so a refused resume leaves an empty `runs/<id>/`
directory in the runs dir; and a hand-written `meta.json` with a *relative* project path would be resolved
against the process cwd.

## 4. My own counterexamples and probes

1. **Can the fold's own measurement test be trusted?** Yes, and it is the one test whose method needed
   checking. It replays recorded trajectories from before the fold existed, so it cannot depend on the
   stored history being folded *or* un-folded; and its numbers reproduce in a probe that uses the
   production function, and in a Python re-implementation that shares no code with it.
2. **Does the fold land on what was sent?** Yes, at the source: the loop folds `agent.messages` before every
   step, `CountingModel` no longer folds, `DefaultAgent::query` passes `self.messages` to the model and
   pushes the response back into the same vector, and `serialize()` writes that vector.
3. **Does the ledger line exist before the spawn?** No — a pid cannot exist before the spawn, and the code
   agrees (`spawn` at `:457`, `append_ledger` at `:468`). Every document claim now matches, the four
   corrected report lines are the only changes to those files, and the surviving "before the spawn" strings
   are defect statements inside the corrections and inside the two acceptances, not claims.
4. **Is the system prompt shaved?** No. `src/prompts` still carries the same system prompt text, and nothing
   in the batch reduced it; the only system-prompt *change* is a wrong figure in prose (**F-2**).
5. **Can a context-only policy pass?** Yes in principle, which is why **F-3** is a defect: the tail-0 floor
   still notes every folded message. A policy that dropped consumed pairs entirely, or kept only the system
   and task messages, would project well below 1.5 M — and would destroy the role's ability to work, which
   is the trade the batch is right to refuse, but the report claims impossibility rather than that trade.
6. **Are the call-count-lever numbers reproducible?** Approximately (within 0.2 %), not exactly, and the
   "roughly 85 for iter-3" conclusion contradicts the report's own first_80 (**F-4**).

## 5. What I could not establish

* **My own adversarial `--resume` case was not executed.** I did not build a genuinely interrupted run
  directory with a real `VersionStore`, a truncated source and a populated `.hoh` and drive it myself; the
  behaviour above comes from the source plus the batch's own tests, which the gate ran green (7 new resume
  tests, two through the real `run_loop::run`).
* **Plant P4 was not reproduced** on a copy outside the repository (I did not tamper with a copy and re-run
  the AC-8 test to see it go red).
* **The two known gitignored historical evidence files under `runs/**` were not re-fingerprinted here.**
  My full scan of `runs/**` exceeded the command budget because the recorded trajectories are large; the
  clean result covers the 184 browsable/tracked files. The known fingerprint remains the previous
  acceptance's `5cf81e8f`.
* **The remote.** Whether anything was ever pushed is verified from local refs only, because the acceptance
  is offline.
* **A live call.** Whether a real Developer call produces the projected prompt tokens, and whether a role
  works coherently with 12 verbatim messages, remain unmeasured — as the batch itself states.

## 6. Independent judgement

The gate is green on a tree I built and tested myself, with the literal exit code and counts above, zero
warnings, a clean `fmt --check`, and a test set that grew by 12 names with **no** name removed. The
`--resume` defects the failed acceptance filed are fixed in the code and pinned by tests that drive the real
loop; the fold now lands on the history the agent actually stores, so the three prose claims became true
instead of being reworded; the ledger ordering is right and every false statement about it is corrected in
place; `DECISIONS.md` is append-only; AC-2/3/4/5/9/11/13/14 are genuinely fixed; and the cost reduction is
real, exactly reproducible, and was **not** bought by shaving the system prompt.

Against that, **the criterion that has never passed still does not pass**: two of the three recorded
Developer calls remain above 1.5 M on the batch's own (and my) projection, and the batch's own floor says no
value of the tail changes that. Four smaller accuracy defects stand in the batch's reports — an arithmetic
slip in the cost disposition, a wrong system-prompt size contradicted by the report's own composition, an
over-strong "no context-only policy can pass", and lever numbers that do not reproduce — plus a stale
"nothing was committed" sentence. None of them is fatal to the batch's engineering, but a `pass` here is
what authorises the **first push** of this branch, and the one criterion on record as never having passed
still fails. I therefore return **fail**.

## 7. Reproduction

* Gate: `F:/hof-acc6-logs/gate.{out,err,exit}`, `list.*`, `list-ignored.*`, `fmt.*`, `procs{,-after}.txt`;
  script `F:/hof-acc6-work/gate.sh`.
* Cost: probe crate `F:/hof-acc6-work/probe-crate` (`cargo run --offline` output in
  `F:/hof-acc6-logs/probe.out`); my fold `F:/hof-acc6-work/measure.py`, `measure2.py`, `composition.py`
  (the last prints the composition, the call-count lever and the system-prompt sizes).
* Deleted tree: `F:/hof-acc6-work/rmtree_checked.py` (prints the path, refuses without a marker, removes
  only that path).
* Keys: `F:/hof-acc6-work/probe-crate/src/bin/scan.rs` -> `F:/hof-acc6-logs/keyscan-tree.out`
  (184 files, one declared finding, fingerprint `3631b5f1`).
* Frozen documents and append-only: `git diff --stat HEAD~1 HEAD`, `head -11414 DECISIONS.md | md5sum`
  vs `git show HEAD~1:DECISIONS.md | md5sum`, `git for-each-ref`.
