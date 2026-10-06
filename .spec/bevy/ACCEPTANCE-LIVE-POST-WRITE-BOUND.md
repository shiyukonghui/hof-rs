```json
{
 "schema": "hof-rs / bevy live round under the post-write call bound: independent acceptance",
 "artifact": ".spec/bevy/ACCEPTANCE-LIVE-POST-WRITE-BOUND.md",
 "subject": ".spec/bevy/LIVE-POST-WRITE-BOUND.md — the live round `postwrite1` (raw tree runs/postwrite1 + runs/bevy-postwrite1)",
 "produced_at": "2026-10-06",
 "reviewer": "fresh independent acceptance subagent; no implementer, dispatcher or earlier-acceptance context inherited",
 "verdict": "pass",
 "verdict_basis": "The headline reproduces exactly from the raw trajectories: exit code 0, three iterations all ok:true with a launchable artifact gate, and Developer calls of 563,813 / 679,401 / 854,890 tokens over 36 / 36 / 44 billed model calls, against the criterion's own source config/hoh.yaml:47 artifact_write_budget_tokens: 1500000. I re-derived every prefix sum from extra.response.usage.total_tokens and every count from the response-bearing messages; all match hoh.usage in the same file. The bound's engagement is not inferred from the call count: the last message of iteration 1 and 2 is the guard's own refusal, 'this call has made 36 model call(s) and its live step budget is 35', and iteration 3's is '44 ... live step budget is 43' — so the bound bit twice and did not bite once. The DR-18 wrap-up retry did not fire in any iteration (no developer.attempt2.json anywhere; wrap_up_retry_used false / not_triggered in all three), so the reported per-call figures are the whole Developer stage (2,098,104 tokens) — nothing is excluded that the earlier acceptance warned about. Identity is intact: the answering nonce, spawned, answering and listening pids all agree at 58160, the ledger's 7 pids are exactly the 7 pids my own reading of the round's stored 10-second netstat poll ever saw listening, never two at once, and nothing survives. The gate reproduces on my own build directory: cargo test --offline exit 0 with 824 passed / 0 failed / 6 ignored / 830 listed, cargo fmt --all --check exit 0, zero compiler warnings. Three defects are recorded and none touches a figure the verdict rests on: the artefact's shell-side-write census is incomplete (a second uncounted project write, iteration 1 call 31, is visible in the raw tree and in version A1), the `ok` redirection is attributed to call 36 when it is the 37th billed call, and the round's own prd_coverage block is degenerate and unreported. The caveat a reader must carry is not about the numbers but about what they certify: one of the three calls never exercised the lever (no counted write, 44-call unwritten allowance, zero engineering change), one was cut mid-plan and left the first completed live iteration with a frozen-surface gap (P3), and the round's third iteration cleared the NoEngineeringWrite gate only because an unescaped `->` made cmd.exe write a stray file named `ok`. The criterion is met on the evidence for this round's three Developer calls; it is not yet evidence that the pipeline reliably delivers under it.",
 "criteria": [
  {
   "id": "C1",
   "question": "The headline, from the raw tree: exit codes, per-iteration outcome, per-Developer-call tokens, and whether the round really completed three iterations with a launchable artifact in each.",
   "pass": true,
   "evidence": "runs/postwrite1/exit_code = 0 and runs/postwrite1/process_exit_code = 0 (literal file contents), and meta.json carries exit_code 0 / iterations 3 / project E:\\live3\\project. Every iteration's result.json has ok:true, failed_role:null, reason:'ok', and artifact_gate {applicable:true, launchable:true, reasons:[]}. Developer cost re-derived by me from runs/postwrite1/iter-*/traj/developer.attempt1.json: 36 / 36 / 44 response-bearing messages (extra.response.usage present) summing extra.response.usage.total_tokens to 563,813 / 679,401 / 854,890, each equal to that file's own hoh.usage.total_tokens and hoh.usage.calls, with prompt+completion also equal. Prefix sums re-derived: iter-1 P(35)=551,444 P(36)=563,813; iter-2 P(35)=653,311 P(36)=679,401; iter-3 P(35)=680,522 P(36)=707,030 P(37)=734,642 P(44)=854,890 — every one equal to the artefact's figures. Ratios 0.3759 / 0.4529 / 0.5699, margins 936,187 (62.41 %) / 820,599 (54.71 %) / 645,110 (43.01 %) under 1,500,000. Criterion source read in this tree: config/hoh.yaml:47 artifact_write_budget_tokens: 1500000. No figure differs, so the verdict is unchanged."
  },
  {
   "id": "C2",
   "question": "★ Was it cheaper *because* it was weaker? Artifact validity, battery result, first-pass launchability, repair retry, and the size/content of the engineering change against earlier rounds.",
   "pass": true,
   "evidence": "The delivered game is not weaker on any frozen measure, but the per-call work is genuinely reduced and one iteration is not producing work at all. Measured from the version tree: A0 game.rs 4,502 B (hash dfe4852c...) -> A1 15,538 B (cbc8b926..., = iter-1 candidate) -> A2 20,619 B (39a7f69f..., = iter-2 candidate) -> A3 = A2's game.rs byte-identical (iter-3 candidate adds only `ok`). Battery, read from iter-*/result.json battery_passes[0]: iter-1 has 1 pass, launchable true, and two failing steps e3_win_flag + e3_win_position (raw reason: 'the win flag never became true (5 readings, all false)'), giving surfaces 14 verified / 1 gap (P3) / 4 unobservable; iter-2 and iter-3 have all 12 steps true and 15 / 0 / 4. artifact_valid is true in all three and repair_retry_used is false everywhere. Same frozen PRD (meta.json spec sha256 93b2ed85... identical in livecost1, completion1, clonefix1, round4, postwrite1), same model deepseek-v4.1-flash, same ablation flags. Earlier post-fix live rounds: completion1 A1 11,828 B / A2 19,134 B (both 15/0/4) then iter-3 failed; clonefix1 A1 9,587 B / A2 = A3 19,980 B (15/0/4); round4 (pre-fix) A1 14,858 / A2 32,342 / A3 46,472. So the round's end state (20,619 B, 15/0/4, every battery step green) is comparable to or larger than the earlier live end states at 1/5 to 1/6 the Developer tokens. THE REDUCTION IS REAL AND MUST BE STATED: iteration 1's plan.md names 'Reachable coin pickup and one-way win flag' as priority 3, the call was cut at 36 while its last three actions were read-only inspection, and P3 was left unimplemented — the first completed live iteration in this corpus with a frozen-surface gap; iteration 2's plan is headed 'Reachable win condition (P3, blocker)' and closes it. Iteration 3 changed nothing engineering-wise. So: not a weaker delivered game, but a cheaper call that did less work, absorbed by a fourth iteration's worth of plan."
  },
  {
   "id": "C3",
   "question": "Did the mechanism do what it claims? Bound engagement, refused-exit base rate, and any uncounted shell-side project write.",
   "pass": true,
   "evidence": "Engagement is read from the guard's own words, not from arithmetic: the final message (role 'exit') of iter-1 and iter-2 developer.attempt1.json is 'HOH_FAIL_FAST StepBudgetExceeded: this call has made 36 model call(s) and its live step budget is 35 (`agent.steps_per_artifact` and `agent.post_write_step_limit`...)' and iter-3's is the same with '44 ... 43'. Config read in this tree: step_limit 150, wrap_up_steps 25, steps_per_artifact 8, post_write_step_limit 35, so the unwritten allowance is 25+max(150/8,1)=43 and a bound of 35 bills 36. Counted writes (extra.hoh_write_path, non-null): iter-1 calls 6 and 29 (src/game.rs, 8,688 and 15,126 bytes), iter-2 call 8 (src/game.rs, 20,619 bytes), iter-3 none of any kind — matching the artefact. extra.hoh_exit_refused does not occur in any of the 11 non-redacted trajectories (0 refusals over 329 billed calls; the key is absent, not null), matching the artefact's 0/329. ONE CLAIM IS UNDERSTATED (defect D1): the detector missed *two* shell-side project writes, not one. Iteration 1's Developer at billed call 31 ran `powershell -Command \"(Get-Content src\\game.rs) -replace 'app.insert_resource\\(Time::default\\(\\)\\);','app.insert_resource(Time::<()>::default());' | Set-Content src\\game.rs\"` — a project-root edit the counted detector never sees, and its effect is in version A1 (line 253, Time::<()>::default()). It does not change iteration 1's bound (a counted write already existed at call 6) or any token figure, but it means the hole is recurring, and the round itself answers the artefact's 'base rate of shell-side project writes is unmeasured': at least 2 in 3 Developer calls."
  },
  {
   "id": "C4",
   "question": "The wrap-up retry risk: did a second Developer call fire, and do the reported per-call figures include or exclude it?",
   "pass": true,
   "evidence": "It did not fire. `find runs/postwrite1 -name '*attempt2*'` returns only iter-2 and iter-3 tester.attempt2 files; there is no developer.attempt2.json under any iteration. result.json says wrap_up_retry_used false, wrap_up_retry_reason 'not_triggered' and repair_retry_used false in all three, and the attempts[] arrays contain a single developer entry each. The code path agrees (src/runtime/run_loop.rs:1708 developer_limits = is_limits_exceeded(...), :1735 `if developer_limits && !developer_artifact_valid`, :1740 wrap_base.limits.step_limit = min(wrap_up_steps=25, WRAP_UP_RETRY_MAX_STEPS=30) = 25): all three calls ended limits-exceeded (exit_was_limits true) but developer_artifact_valid was true in all three — iteration 3 inherited iteration 2's launchable artifact — so the retry was correctly skipped. Therefore the reported per-call figures are the complete Developer stage of this round: 563,813 + 679,401 + 854,890 = 2,098,104 tokens, with nothing excluded. Had it fired the addition would be one call of <= 26 billed calls (min(35,25)=25 written budget); the artefact's 0.38M-0.97M proxy from the recorded 26-call prefixes is consistent with that. Note what this means for the reading: a retry would be a separate Developer *call*, so it would not breach a per-call 1.5M criterion — it would only inflate the per-iteration Developer stage."
  },
  {
   "id": "C5",
   "question": "Identity and trustworthiness; coverage of the frozen 19 surfaces; the two formerly open items.",
   "pass": true,
   "evidence": "runs/bevy-postwrite1/launch.json: nonce a8f82206-420c-4826-aa88-3927ffabd70e = answered_nonce; spawned_pid = answering_pid = listening_pid = 58160; verified true; built and executed sha256 both aba49a5a509053fb15738049106b23216cc431254c1d00fe51d76f3f1a4c3214; endpoint http://127.0.0.1:15702/. launch-ledger.jsonl has 7 lines whose (pid, nonce, launch_image) triples match the artefact's table exactly, including line 6 = (58160, a8f82206-..., 5678469d-...). My own parse of the round's stored 10-second poll (E:\\live3\\logs\\os-poll.log, written while the round ran) gives 296 lines, 289 naming a listener, exactly the 7 ledger pids {29148,20716,38264,54728,48944,58160,49068}, zero lines naming more than one listener, and only port 15702 ever appearing; first listener line 10:56:41 pid 29148, last 11:49:00 pid 49068. round-stop.json records all 7 with reaped [] / still_alive [] / endpoint_holder null / failure null; measured.json's after_the_round_netstat and after_the_round_tasklist_{hof_game,hoh} are all the empty string; and my own netstat/tasklist now show no line for 15702/15703 and no hof_game.exe or hoh.exe. Coverage: the frozen registry is src/adapter/bevy/prd_surfaces.rs with exactly 19 ids (P1-P5, C1-C6, Q-scale, Q-startup, Q-not-required, Q-perf, B2.1-B2.4); per-iteration surfaces are 14/1/4 (gap P3), 15/0/4, 15/0/4, the four unobservables being C5, C6, Q-scale, Q-not-required in every iteration. The two formerly open items are still decided by persisted raw BRP reads of the game's own FrameCounter: raw/e3_process_liveness.json frames first_frame->second_frame 707->717, 718->728, 708->718 for requested 8, observed true, failure null."
  },
  {
   "id": "C6",
   "question": "Gate: cargo test --offline exit 0 with literal counts, cargo fmt exit 0, zero warnings, own build directory, one test process at a time, disk checked, no rm -rf.",
   "pass": true,
   "evidence": "Run by me on my own build directory E:/pwb-acc2-target (E: 519 GiB free; F: 7.1 GiB free, 100 % used, checked before and after and unchanged — the repository target/ was not used), the four commands strictly one after another. cargo test --offline: literal exit 0, 62 'test result:' lines summing to 824 passed / 0 failed / 6 ignored / 0 measured (= 830), 0 compiler-warning lines and 0 error lines in the whole log. cargo test --offline -- --list: exit 0, 830 test lines. cargo test --offline -- --list --ignored: exit 0, 6 test lines. cargo fmt --all --check: exit 0 with 0 bytes on stdout and 0 bytes on stderr. This is exactly the 824 / 0 / 6 / 830 baseline. I wrote no file under runs/**, deleted nothing, used no rm -rf and no wildcard deletion, committed nothing."
  }
 ],
 "defects": [
  {
   "id": "D1",
   "severity": "medium",
   "what": "The artefact's shell-side census is incomplete and its R3 base-rate claim is answerable from its own round but left open. It records exactly one uncounted shell-side project write (iteration 3's stray `ok`) and says 'The counted detector missed one shell-side project write'. In the same round, iteration 1's Developer made a second uncounted project-root write at billed call 31 — a PowerShell `(Get-Content src\\game.rs) -replace ... | Set-Content src\\game.rs` edit — and its effect is present in version A1 (a0ceef4e... game.rs line 253, Time::<()>::default(), which A0 does not contain). It did not change iteration 1's bound engagement (counted writes already existed at call 6) and changes no token figure, so the verdict is unaffected; but the same mechanism that hid iteration 3's write is shown to recur in a call that did real work, and the round supplies the base rate the artefact lists as unmeasured (>= 2 uncounted project writes in 3 Developer calls).",
   "reproduction": "python read of runs/postwrite1/iter-1/traj/developer.attempt1.json message index 71 (actions[0]) shows the Set-Content command; grep 'Time::' runs/postwrite1/versions/a0ceef4e987c7213cabc759d4dcdc76e00e9c3ca39e7dadb333a165d4e2686ac/src/game.rs -> '253: app.insert_resource(Time::<()>::default());' and the same grep on the A0 version 638057ca... returns nothing; src/harness/guard.rs:1092-1098 is_excluded_path is what makes a shell write invisible."
  },
  {
   "id": "D2",
   "severity": "low",
   "what": "The command that created `ok` is attributed to call 36 in both the structured block ('command_issued_at_call_36') and the prose ('At call 36 the role ran ...'). It is the 37th billed model call: the assistant message carrying it is messages[91] of iter-3 developer.attempt1.json (timestamp 11:36:33, usage total 27,612) and its tool result (empty stdout, returncode 0) is messages[92] at 11:36:34, while the 36th billed call is messages[89] ('dir /b /s .hoh\\deterministic\\readings 2>nul & echo === & dir /s /b .hoh\\deterministic'). The file's identity, content (664 B, first line 'battery.json -=true'), size and effect are unaffected — only the index in the narrative is off by one.",
   "reproduction": "python: load runs/postwrite1/iter-3/traj/developer.attempt1.json, count response-bearing messages (extra.response.usage), print messages[89] and messages[91] with their running counts -> 36 and 37; the trajectory's final message says '44 model call(s)', fixing the numbering at 1..44."
  },
  {
   "id": "D3",
   "severity": "low",
   "what": "Every iteration's runs/postwrite1/iter-*/result.json carries a prd_coverage block with verified: 0, gap: 1 and placeholder gap ids — ['P3'], ['TMP'], ['P1'] — including the two iterations the artefact calls 15/0/4. In the earlier live rounds the same block names 6-10 verified_ids (e.g. completion1 iter-1: 9 verified, gap P5-air). The artefact's coverage claim is taken from battery_passes[0].surfaces, which is correct and reproduces, and it never mentions prd_coverage; a reader comparing the round's own bookkeeping to the claim would find a second, unexplained 'gap: 1'. Not a contradiction of the frozen-surface claim, but an unreported, degenerate field.",
   "reproduction": "python read of runs/postwrite1/iter-{1,2,3}/result.json -> prd_coverage == {verified:0, gap:1, verified_ids:[], gap_ids:[P3|TMP|P1]} while battery_passes[0].surfaces == {verified:14|15, gap:1|0, unobservable:4}."
  }
 ],
 "risks": [
  {
   "id": "R1",
   "risk": "Durability: n = 3 Developer calls, only 2 of which exercised the bound, one model, one provider, one project shape, one round. Nothing here estimates variance, and the binding recording the bound was fitted to (round4-iter-3, 1,452,307 at 36 calls) still sits 3.2 % under the bar.",
   "mitigating": "The two bound-cut live calls cleared the bar by 62.4 % and 54.7 %, not 3.2 %, so the live cost per call is far below the fitted worst case; but one round cannot turn that into a rate."
  },
  {
   "id": "R2",
   "risk": "The efficacy hole is not closed. The bound engages only on a counted HOH_WRITE_FILE write to a non-.hoh path (guard.rs:1092-1098, ArtifactKind::ProjectFile). This round shows the uncounted shell path twice: once as a junk `ok` file that happened to satisfy the round's tree-hash gate, and once as a real Set-Content edit to src/game.rs. The identical shell edit to a source file, with no counted write, would satisfy NoEngineeringWrite with genuine engineering content and keep the 44-call unwritten allowance — the bound optional exactly where it matters (the artefact's R3).",
   "mitigating": "The artefact discloses the hole and names the fix direction (reconcile the detector with the tree-hash measurement)."
  },
  {
   "id": "R3",
   "risk": "The wrap-up retry is still untested for its own trigger. It did not fire only because developer_artifact_valid was true in all three calls (iteration 3 rode iteration 2's artifact). A bound-cut call whose project no longer builds fires a second Developer call of <= 26 billed calls; the artefact's proxy is +0.38M-0.97M. On a per-call reading of the criterion that second call is still under 1.5M; on a per-iteration reading it is an addition.",
   "mitigating": "Code path verified; not fired in this or any recorded round."
  },
  {
   "id": "R4",
   "risk": "Truncation converts into failure rather than saving when a later iteration is not productive. Iteration 1 was cut with P3 unimplemented and iteration 2 repaired it, but the previous live round's iteration 3 produced no write at all and the round exited 2 (NoEngineeringWrite). Here iteration 3 produced no engineering change either and cleared the gate only through the `ok` accident; on the previous round's behaviour the same shape ends the round.",
   "mitigating": "The truncation did not prevent this round reaching 15/0/4; iteration 2's A2 alone is the complete artifact."
  },
  {
   "id": "R5",
   "risk": "Reading ambiguity the reader should be told about: the criterion is '1,500,000 tokens per Developer *call*'. This round also had three iterations, so a per-iteration or per-round reading would give different answers (Developer stage total 2,098,104, round total 5,708,999 including testers and planners), and a fired retry would add a second call to one iteration.",
   "mitigating": "The artefact states the criterion per call and reports only the three Developer calls."
  }
 ],
 "unverified": [
  "That the binary at E:\\pwb-target\\debug\\hoh.exe was built from this tree at 10:55:45: the file's mtime is now 11:57 because the artefact's own later gate relinked into the same target dir (the artefact discloses this). What I could verify is weaker but direct: git diff e900262 HEAD -- src is empty (src/** is byte-identical to the post-write-bound implementation) and the running binary emitted the new guard's own refusal text naming `agent.post_write_step_limit`, which only the post-write-bound code produces.",
  "Whether the model would have ended calls 1 and 2 earlier than 36 on its own. The bound definitively capped those calls (the refusal names budget 35 at 36 calls), but one round cannot separate 'the bound ended it' from 'the model chose to keep working until refused'.",
  "Plan conformance of the delivered game. The frozen measure (battery + 19 surfaces) is reproduced, but 'the iteration's plan was fully implemented' is not decided by it — iteration 1's P3 gap shows the two can disagree.",
  "Any effect on another provider, another model, or another project shape; and any refusal base rate, since extra.hoh_exit_refused is absent from the corpus entirely (0/329 is an absence, not a rate).",
  "The historical free-space readings (F: 8.30 -> 7.07 GB, E: 518.59 -> 518.51 GB): F: is 7.1 GiB now, 100 % used, but a past value cannot be re-read. My own gate's F: reading was 7.1 GiB before and after.",
  "The meaning and correct value of the prd_coverage block (defect D3); no frozen document I read in the report's scope defines it.",
  "The controlled reproduction at E:\\live3\\shape-test was performed by the same author after the round. I did reproduce the mechanism independently (E:\\pwb-acc2\\shapetest2, same command shape via cmd.exe: exit 0, empty stdout, a 21-byte file named `ok` containing 'battery.json -=true'), which is what makes this item only partly unverified — the accident is real and reproducible; that it is the same accident that produced the round's 664-byte `ok` remains an inference from file content, size scaling with 26 inputs, and timing."
 ],
 "own_figures_beside_reported": [
  {
   "figure": "criterion tokens per Developer call",
   "reported": 1500000,
   "mine": 1500000,
   "matches": true
  },
  {
   "figure": "iter-1 Developer total tokens",
   "reported": 563813,
   "mine": 563813,
   "matches": true
  },
  {
   "figure": "iter-2 Developer total tokens",
   "reported": 679401,
   "mine": 679401,
   "matches": true
  },
  {
   "figure": "iter-3 Developer total tokens",
   "reported": 854890,
   "mine": 854890,
   "matches": true
  },
  {
   "figure": "iter-1 Developer billed model calls",
   "reported": 36,
   "mine": 36,
   "matches": true
  },
  {
   "figure": "iter-2 Developer billed model calls",
   "reported": 36,
   "mine": 36,
   "matches": true
  },
  {
   "figure": "iter-3 Developer billed model calls",
   "reported": 44,
   "mine": 44,
   "matches": true
  },
  {
   "figure": "iter-1 prefix(35) / prefix(36)",
   "reported": "551444 / 563813",
   "mine": "551444 / 563813",
   "matches": true
  },
  {
   "figure": "iter-2 prefix(35)",
   "reported": 653311,
   "mine": 653311,
   "matches": true
  },
  {
   "figure": "iter-3 prefix(35) / (36) / (37)",
   "reported": "680522 / 707030 / 734642",
   "mine": "680522 / 707030 / 734642",
   "matches": true
  },
  {
   "figure": "live step budget named in the refusal (iter-1, iter-2, iter-3)",
   "reported": "35 / 35 / n.a.",
   "mine": "35 / 35 / 43",
   "matches": true
  },
  {
   "figure": "counted hoh_write_path observations, iter-1 / iter-2 / iter-3 Developer",
   "reported": "2 / 1 / 0",
   "mine": "2 / 1 / 0",
   "matches": true
  },
  {
   "figure": "first counted project write, iter-1 / iter-2",
   "reported": "call 6 / call 8",
   "mine": "call 6 / call 8",
   "matches": true
  },
  {
   "figure": "uncounted shell-side project writes in the round",
   "reported": 1,
   "mine": 2,
   "matches": false
  },
  {
   "figure": "billed call index of the command that created `ok`",
   "reported": 36,
   "mine": 37,
   "matches": false
  },
  {
   "figure": "extra.hoh_exit_refused observations over the round",
   "reported": 0,
   "mine": 0,
   "matches": true
  },
  {
   "figure": "billed calls censused / attempt trajectories censused",
   "reported": "329 / 11",
   "mine": "329 / 11",
   "matches": true
  },
  {
   "figure": "tester retry added cost (iter-2 608683 + iter-3 668586)",
   "reported": 1277269,
   "mine": 1277269,
   "matches": true
  },
  {
   "figure": "developer.attempt2.json anywhere",
   "reported": "none",
   "mine": "none",
   "matches": true
  },
  {
   "figure": "A1 / A2 / A3 game.rs bytes",
   "reported": "15538 / 20619 / 20619 (A3 = A2)",
   "mine": "15538 / 20619 / 20619 (hashes cbc8b926 / 39a7f69f / 39a7f69f)",
   "matches": true
  },
  {
   "figure": "iter-1 battery failing steps / surfaces",
   "reported": "e3_win_flag, e3_win_position / 14-1-4",
   "mine": "same, raw reason 'never became true (5 readings)' / 14-1-4",
   "matches": true
  },
  {
   "figure": "iter-2, iter-3 battery steps green",
   "reported": 12,
   "mine": 12,
   "matches": true
  },
  {
   "figure": "surviving launch nonce / spawned / answering / listening",
   "reported": "a8f82206-... / 58160 / 58160 / 58160",
   "mine": "same",
   "matches": true
  },
  {
   "figure": "ledger lines / distinct pids",
   "reported": "7 / 7",
   "mine": "7 / 7, set == observed listener set",
   "matches": true
  },
  {
   "figure": "OS poll lines / lines naming a listener / lines naming two listeners",
   "reported": "296 / 289 / 0",
   "mine": "296 / 289 / 0",
   "matches": true
  },
  {
   "figure": "free disk where the run trees and builds landed",
   "reported": "F: 8.30 -> 7.07 GB; games and builds on E:/D:",
   "mine": "F: 7.1 GiB now and before/after my gate (untouched); my build E:/pwb-acc2-target used E:",
   "matches": true
  },
  {
   "figure": "gate passed / failed / ignored / listed",
   "reported": "824 / 0 / 6 / 830",
   "mine": "824 / 0 / 6 / 830",
   "matches": true
  },
  {
   "figure": "cargo test / list / list-ignored / fmt literal exit codes",
   "reported": "0 / 0 / 0 / 0",
   "mine": "0 / 0 / 0 / 0",
   "matches": true
  },
  {
   "figure": "compiler warnings",
   "reported": 0,
   "mine": 0,
   "matches": true
  },
  {
   "figure": "round wall clock",
   "reported": "53.00 minutes (10:56:09 -> 11:49:09)",
   "mine": "started_at 1791255370, round-stop 1791258546 = 3176 s = 52.9 min",
   "matches": true
  }
 ]
}
```

# ACCEPTANCE-LIVE-POST-WRITE-BOUND — an independent look at the round that first met the cost criterion

The machine-readable block above is `json.dumps(..., indent=1, ensure_ascii=False)` output; it was written by
`E:/pwb-acc2/write_acceptance.py` and then **parsed back out of this written file** before the script exited
(the parse is the last thing the generator does and it fails unless the block round-trips). I am a fresh
independent acceptance subagent: I inherited no conclusion from the implementer, from the dispatcher, or from
`ACCEPTANCE-POST-WRITE-BOUND.md`. Every number below was re-derived from the raw run tree, from the code, or from
a check I ran myself.

**No round was run, no model call was made, no engine was started, no network was used.** I did not modify
`src/**`, `tests/**`, `evidence/**`, the registry, the battery, `.gitattributes` or any frozen document; I wrote
nothing under `runs/**`, committed nothing, staged nothing, pushed nothing, and fixed nothing. Helper scripts live
outside the repository at `E:/pwb-acc2/` and every one landed through a file write (never multi-line Python on a
shell command line). No `rm -rf`, no wildcard deletion, no path built from an unexpanded variable, no
`git checkout --`. The gate used its own build directory `E:/pwb-acc2-target` on `E:`, after checking `F:` (7.1 GiB
free, 100 % used), with one test process at a time.

## 1. Item-by-item result

| # | item | result | the evidence that decides it |
|---|---|---|---|
| 1 | the headline, re-derived from the raw tree | **pass** | `exit_code` and `process_exit_code` both `0`; all three `result.json` `ok:true` with `artifact_gate.launchable:true`; Developer totals 563,813 / 679,401 / 854,890 over 36 / 36 / 44 response-bearing model calls, each equal to the file's own `hoh.usage`; all prefix sums reproduce exactly |
| 2 | ★ cheaper because weaker? | **pass, with a stated reduction** | end state 20,619 B / 15 verified / 0 gap / 4 unobservable with all 12 battery steps green — comparable to the earlier live rounds at 1/5–1/6 the Developer tokens; but iteration 1 was cut with its plan's P3 unimplemented (14/1/4, `e3_win_flag` "never became true (5 readings)"), iteration 2 was the repair, and iteration 3 changed nothing engineering-wise |
| 3 | did the mechanism do what it claims? | **pass; one claim understated (D1)** | the guard's own final message names the live budget: `36 model call(s) ... budget is 35` twice and `44 ... 43` once; `extra.hoh_exit_refused` absent from all 11 trajectories (0/329); counted writes 2 / 1 / 0 at calls (6,29) / (8) / none — all as reported, but the detector missed **two** shell-side project writes, not one |
| 4 | the wrap-up retry risk | **pass — it never fired** | no `developer.attempt2.json` under any `iter-*/traj/`; `wrap_up_retry_used:false`, reason `not_triggered` everywhere; `artifact_valid:true` in all three calls, and the code fires only when `developer_limits && !developer_artifact_valid`; so the figures are the complete Developer stage (2,098,104), nothing excluded |
| 5 | identity, trust, coverage | **pass** | nonce = answered nonce = `a8f82206-...`; spawned = answering = listening = `58160`; built = executed sha256; 7 ledger lines = the 7 pids my parse of the round's own poll saw listening, never two at once; nothing survives; 19 frozen surfaces at 14/1/4, 15/0/4, 15/0/4; `Q-startup` and `B2.1` still decided by persisted raw `FrameCounter` frames 707→717 / 718→728 / 708→718 |
| 6 | the gate | **pass** | my own `cargo test --offline` literal exit **0**, 824 passed / 0 failed / 6 ignored / 830 listed over 62 result lines, 0 warnings, 0 errors; `-- --list` 830 (exit 0); `-- --list --ignored` 6 (exit 0); `cargo fmt --all --check` exit 0 with 0 bytes out |

## 2. The headline I re-derived, beside the reported one

| figure | reported | mine | matches |
|---|---|---|---|
| criterion (`config/hoh.yaml:47`) | 1,500,000 | 1,500,000 | yes |
| iter-1 / iter-2 / iter-3 Developer total tokens | 563,813 / 679,401 / 854,890 | same | yes |
| iter-1 / iter-2 / iter-3 billed model calls | 36 / 36 / 44 | same | yes |
| live budget named in the guard's refusal | 35 / 35 / — | **35 / 35 / 43** | yes (iter-3 is the unwritten allowance) |
| prefix(35): iter-1 / iter-2 / iter-3 | 551,444 / 653,311 / 680,522 | same | yes |
| prefix(36) / prefix(37): iter-3 | 707,030 / 734,642 | same | yes |
| margin under the criterion | 936,187 / 820,599 / 645,110 (62.4 % / 54.7 % / 43.0 %) | same | yes |
| `extra.hoh_exit_refused` over the round | 0 | 0 (the key does not occur) | yes |
| counted `hoh_write_path` writes, Developer | 2 / 1 / 0 | 2 / 1 / 0 | yes |
| uncounted shell-side project writes | 1 | **2** | **no — D1** |
| billed call that created `ok` | 36 | **37** | **no — D2** |
| `developer.attempt2.json` | none | none | yes |
| A1 / A2 / A3 `game.rs` | 15,538 / 20,619 / 20,619 | same, hashes `cbc8b926` / `39a7f69f` / `39a7f69f` | yes |
| iter-1 battery | `e3_win_flag`, `e3_win_position` failing; 14/1/4 | same; raw reason "the win flag never became true" | yes |
| gate | 824 / 0 / 6 / 830, fmt 0, 0 warnings | same, on my own build dir | yes |

**Nothing in the headline differs.** The two mismatches are in supporting narrative (D1, D2) and neither moves a
token figure, a call count, or the verdict.

## 3. ★ Was the round cheaper because it was weaker?

This is the question the goal turns on, and my answer has three parts.

**The delivered game is not weaker.** The round's final version (A3) is A2's `game.rs`, 20,619 bytes, scoring 15
verified / 0 gap / 4 unobservable with all 12 battery steps green on the first battery pass and the artifact gate
launchable. That is the same frozen-surface result as every completed iteration of the previous post-fix live
rounds (`completion1` A1 11,828 B and A2 19,134 B, `clonefix1` A1 9,587 B and A2 = A3 19,980 B, both 15/0/4), on
the same frozen PRD (`93b2ed85…`, identical in all five runs) and the same model. The round's total engineering
change, A0 → A2, is +16,117 bytes of `game.rs`; `completion1`'s was +14,632 and `clonefix1`'s +15,478 (plus its
`src/snapshot.rs`, which the PRD does not require — C6 says screenshots are not required). So the same measured
game, for 2,098,104 Developer tokens instead of 7.5M–11.7M.

**But the work per call is genuinely less, and the round needed a fourth iteration's worth of plan to absorb it.**
Iteration 1's `plan.md` lists "Reachable coin pickup and one-way win flag" as priority 3. The call was cut at 36
calls, and its last three actions are read-only inspection; the battery then recorded the win flag never becoming
true, so P3 was left unimplemented. That is the **first completed live iteration in this corpus with a
frozen-surface gap** — `completion1`'s and `clonefix1`'s completed iterations are all 15/0/4. Iteration 2's plan is
headed "Reachable win condition (P3, blocker)" and closes it. So the low per-call figure is partly the price of a
truncated call, and the pipeline recovered only because a further iteration existed. That is the reading a reader
must be told.

**And one of the three calls did no engineering work at all.** Iteration 3 emitted zero counted writes, changed
`game.rs` not at all (A3's hash equals A2's), and its 854,890-token call is a read-only grind that scored the
inherited artifact. It passed the round's `NoEngineeringWrite` gate only because of the `ok` file. The artefact
says all of this itself and declines to call the round a win for the pipeline; I agree with that reading.

Net: **not a weaker delivered game, but a cheaper call that did less work.** Whether that is acceptable is a
question about the pipeline's iteration budget, not about the token figures — and on a two-iteration budget this
round would still have delivered the complete A2.

## 4. Did the mechanism do what it claims, and what did the detector miss?

The engagement claim is not an inference. The final message of each Developer trajectory is the guard's own refusal
text, which names the live budget at the point of enforcement:

```
HOH_FAIL_FAST StepBudgetExceeded: this call has made 36 model call(s) and its live step budget is 35
  (`agent.steps_per_artifact` and `agent.post_write_step_limit`, re-read here, at the point of enforcement).
HOH_FAIL_FAST StepBudgetExceeded: this call has made 36 model call(s) and its live step budget is 35
HOH_FAIL_FAST StepBudgetExceeded: this call has made 44 model call(s) and its live step budget is 43
```

with `agent.wrap_up_steps: 25`, `agent.steps_per_artifact: 8`, `agent.post_write_step_limit: 35` and
`step_limit: 150` read in this tree, so `25 + max(150/8, 1) = 43` and a bound of 35 bills 36. Two calls were capped
by the bound; one never had a counted write and ran the unwritten allowance instead.

`extra.hoh_exit_refused` does not occur anywhere in the round's 11 trajectories, so the write guarantee fired zero
times and the refused-exit base rate for this shape is 0/329 billed calls — matching the artefact's own census
exactly. That remains an absence, not a rate.

**The detector missed two shell-side project writes, not one.** The artefact records only iteration 3's stray `ok`.
In the same round, iteration 1's Developer at billed call 31 ran

```
powershell -Command "(Get-Content src\game.rs) -replace 'app.insert_resource\(Time::default\(\)\);',
  'app.insert_resource(Time::<()>::default());' | Set-Content src\game.rs"
```

which is a project-root edit invisible to the counted detector (`.hoh/**` is excluded at
`src/harness/guard.rs:1092-1098`, and only `HOH_WRITE_FILE` directives are counted at all), and whose effect is
present in version A1 (`a0ceef4e…/src/game.rs:253`); A0 contains no `Time::` line at all. It changed no token
figure and did not affect the bound (a counted write already existed at call 6), but it shows the hole is a
recurring behaviour rather than one accident, and it answers the artefact's open R3 base-rate question from its own
round: at least 2 uncounted project writes in 3 Developer calls.

I also reproduced the redirection accident myself, outside the repository, with the same command shape run by
`cmd.exe` over one input file: exit code 0, empty stdout, and a 21-byte file literally named `ok` containing
`battery.json -=true` (`E:/pwb-acc2/shapetest2/`). The artefact's mechanism is real and stands.

## 5. The wrap-up retry

It did not fire, and I checked it three ways: no `developer.attempt2.json` anywhere under the run tree; each
`result.json` says `wrap_up_retry_used:false` / `wrap_up_retry_reason:"not_triggered"` / `repair_retry_used:false`;
and `src/runtime/run_loop.rs:1735` fires the retry only when `developer_limits && !developer_artifact_valid`, while
all three calls ended with `exit_was_limits:true` and `artifact_valid:true` (iteration 3 inherited iteration 2's
launchable project).

So the reported per-call figures **include** everything: they are not prefixes of a call that continued elsewhere,
and no second Developer call is hidden. The round's Developer stage is 2,098,104 tokens; its whole round is
5,708,999 tokens including three planners and five Tester attempts. What *was* paid and is not in the artefact's
criterion is the Tester-side retry the same bound caused: `tester.attempt2` in iterations 2 and 3, +1,277,269
tokens (608,683 + 668,586), which the artefact discloses and which my read of the trajectories confirms. It is
Tester cost, not Developer cost, but it is a real addition to the round and a sign that a call bound sized for one
role lands on all of them.

## 6. Identity, coverage, and the gate

Identity is intact and, unusually, independently readable: the round left the poll it took while running
(`E:/live3/logs/os-poll.log`). Parsing it myself gives 296 lines, 289 of them naming a `LISTENING` socket on 15702,
**never one line naming two**, and exactly the ledger's pid set `{29148, 20716, 38264, 54728, 48944, 58160, 49068}`
— with the launch record, the append-only ledger, the three poller snapshots, `round-stop.json` and the empty
after-the-round netstat/tasklist all agreeing. The surviving launch is nonce `a8f82206-…`, pid 58160, built =
executed `aba49a5a…`, on ledger line 6.

Coverage of the frozen registry (19 ids in `src/adapter/bevy/prd_surfaces.rs`, matching the result ids exactly) is
14 verified / 1 gap / 4 unobservable, then 15 / 0 / 4 twice; the four unobservables are `C5`, `C6`, `Q-scale`,
`Q-not-required` in every iteration. The two formerly open items are still decided by persisted raw BRP reads of the
game's own `FrameCounter`, not by a summary: `raw/e3_process_liveness.json` records first→second frame 707→717,
718→728 and 708→718 for 8 requested, `observed:true`, `failure:null`.

The gate reproduces on my own build directory: `cargo test --offline` **exit 0** with **824 passed / 0 failed / 6
ignored / 830 listed** across 62 `test result:` lines, **0** compiler warning lines and **0** error lines;
`-- --list` 830 (exit 0); `-- --list --ignored` 6 (exit 0); `cargo fmt --all --check` exit 0 with 0 bytes on both
streams. Exactly the baseline, and `F:` was untouched by my build (7.1 GiB free before and after).

One thing the gate does **not** establish: `E:/pwb-target/debug/hoh.exe` now has mtime 11:57 because the artefact's
own gate relinked into the same target directory (the artefact discloses the earlier 10:55:45 build). I could not
re-read the historical mtime; what I could verify is that `git diff e900262 HEAD -- src` is empty and that the
running binary printed the post-write-bound guard's own new refusal text, which is behavioural proof of provenance
rather than a byte-for-byte rebuild.

## 7. Is the criterion met on the evidence, or only under a reading?

**Met on the evidence**, and by a wide margin: all three Developer calls are under 1,500,000 by 62.4 %, 54.7 % and
43.0 %, the figures are read from the trajectories that produced them, and the mechanism that capped two of the
three says so in its own refusal text. There is no reading under which one of these calls exceeds the bar.

But a reader must be told three things, because they change what the round certifies:

1. **One of the three calls never exercised the lever.** Iteration 3 had no counted write, ran the 44-call
   unwritten allowance, and delivered no engineering change. Its compliance is evidence about the model, not about
   the bound.
2. **One bound-cut call was cut mid-plan.** Iteration 1 left a frozen surface (P3) unimplemented, the first
   completed live iteration to do so; the round recovered only because iteration 2 existed. The saving is partly
   less work per call, and on the previous round's third-iteration behaviour the same shape ends the round with
   `NoEngineeringWrite` rather than a cheaper round.
3. **The round's third iteration cleared the gate by accident.** The unescaped `->` in a PowerShell one-liner made
   `cmd.exe` write a stray file named `ok` at the project root; `evidence_diff` for iteration 3 is
   `added:["ok"]`. The cost criterion does not depend on this, but the round's exit 0 does — and the same shell path
   applied to a real source edit would satisfy the gate with genuine content while leaving the bound disengaged.

**What would have to be true across several rounds before the cost could be called durable rather than one good
round:** every Developer call emits a counted project write (so the bound is exercised every time); no project write
goes uncounted through the shell, or the tree-hash measurement and the counted detector agree on what a write is;
the first battery pass is green after a bound cut, with no later iteration carrying the repair; `developer_artifact_valid`
stays true so the wrap-up retry does not fire, or its cost is counted if it does; the third iteration is producing
work rather than a re-scoring; and the same per-call range appears with another provider, model or project shape.
None of those six holds universally on the evidence of this one round.

## 8. Defects, and what I could not establish

| id | severity | what | reproduction |
|---|---|---|---|
| D1 | medium | the shell-side-write census is incomplete — two uncounted project writes in the round, not one (iteration 1 call 31 `Set-Content src\game.rs`, visible in version A1), and the R3 base rate is left unmeasured although this round answers it | `iter-1/traj/developer.attempt1.json` messages[71].extra.actions[0]; `grep 'Time::' …/versions/a0ceef4e…/src/game.rs` → line 253, absent in A0; `guard.rs:1092-1098` |
| D2 | low | the command that created `ok` is attributed to call 36; it is the 37th billed call (messages[91], 11:36:33, empty stdout at messages[92]); the 36th is messages[89] | count response-bearing messages in `iter-3/traj/developer.attempt1.json`; the final message says "44 model call(s)" |
| D3 | low | `result.json`'s `prd_coverage` is `{verified:0, gap:1}` with placeholder ids `P3`/`TMP`/`P1` in all three iterations while the artefact reports 15/0/4; earlier live rounds carry 6–10 real `verified_ids`; the field is never mentioned | `iter-{1,2,3}/result.json` → `prd_coverage` beside `battery_passes[0].surfaces` |

What I could not establish is carried in the structured `unverified` list: the historical binary mtime; whether the
model would have ended calls 1 and 2 before 36 unaided; plan conformance of the delivered game; any effect on a
second provider/model/project shape or a true refusal base rate; the historical free-space readings; the meaning of
`prd_coverage`; and the last inch of the `ok` reproduction (the mechanism is independently reproduced, that it is
the same accident that produced the round's 664-byte file is an inference from content, scale and timing).

## 9. Conclusion

**pass.** The headline reproduces exactly from the raw trajectories, the bound's engagement is proven by the
guard's own refusal text rather than inferred, the wrap-up retry did not fire so no Developer cost is hidden, the
identity and the round's own OS poll are internally consistent and independently parseable, the delivered game is
not weaker on any frozen measure, and the gate reproduces at 824 / 0 / 6 / 830 with exit 0, fmt exit 0 and zero
warnings. The three defects recorded above are real but none of them touches a figure the verdict rests on, and one
of them (D1) strengthens the artefact's own risk R3 rather than contradicting its numbers.

The honest summary is the artefact's own, and I endorse it: **the lever works when the write is counted, and the
criterion is met for the first time — but one of the three calls never had a counted write, one was cut mid-plan,
and the round's third iteration passed only because an unescaped `->` wrote a file called `ok`.** Before the cost
can be called durable, the counted-write detector has to agree with the round's own tree-hash measurement, and
several rounds have to show the same figures with every call actually bounded.
