```json
{
 "schema": "hof-rs / bevy round-8 independent acceptance of the round-7 write-accounting batch",
 "produced_at": "2026-10-05",
 "branch": "bevy-core",
 "head_at_acceptance": "05604b9 (the batch's work is 1aeec7b; the delegating agent committed a doc-only append 05604b9 while this acceptance ran)",
 "working_tree": "CLEAN at HEAD 05604b9 (`git status --porcelain` empty) after the delegating agent closed the mid-session D304 append",
 "verdict": "pass",
 "cost_criterion_passes": false,
 "tree_fit_for_first_push_with_the_criterion_recorded_unmet": true,
 "headline": "The corrected write accounting is real, is in the tree, and I reproduced every published figure with an independent re-implementation over the raw recordings: the ten cut write directives (50, 70, 73, 74, 80, 84, 86, 90, 93, 97), the live call's shell write at call 95 and its failed attempt at 139, and round-4 iteration 3's calls 8 (real) and 22 (failed). A-1..A-6 are corrected in the record and their machine-readable blocks now agree with their prose. The withdrawn step budget is not in the shipped code, and the two bands still do not overlap - indeed the corrected accounting makes the safe floor K >= 52 rather than the K >= 43 the report states, because the live call's call-95 write is refused at the K the report calls safe. The gate is green (exit 0, 782/0/6/788, 0 warnings, no test removed). The cost criterion is 2.434x its target on the one live Developer call and is recorded as unmet, with the honest reasons. One low-severity imprecision remains (D-1); it does not affect any conclusion.",
 "criteria": [
  {
   "id": "V1-accounting-in-tree",
   "pass": true,
   "evidence": "src/harness/write_audit.rs (1,279 lines) and tests/write_accounting.rs (387 lines) are tracked and added by 1aeec7b; src/harness/mod.rs adds `pub mod write_audit;` (1 line). `git diff --name-status b9546f5 HEAD -- src/ tests/` shows only M src/harness/mod.rs, A src/harness/write_audit.rs, A tests/write_accounting.rs."
  },
  {
   "id": "V2-inputs-present-but-only-on-this-machine",
   "pass": true,
   "evidence": "All four trajectories exist with the reported byte sizes: runs/livecost1/iter-1 (1,041,144), runs/round4/iter-1 (602,673), iter-2 (1,786,110), iter-3 (736,346). `git ls-files runs` prints 0 lines, so they are not in the repository. tests/write_accounting.rs asserts each path `is_file()` and fails with the missing path named, so a clone fails loudly rather than silently. The tool is re-runnable from the repository ONLY on this machine."
  },
  {
   "id": "V3-independent-reproduction",
   "pass": true,
   "evidence": "My own Python re-implementation (F:/hof-acc8-work/audit.py; my own directive grammar, my own shell/python/script write detector, my own return-code pairing from extra.returncode) reproduces the tool on all four recordings: live directive writes [6,14,17,19,43], project writes [6,14,17,19,43,44,95], failed [(139,'src\\\\game.rs')]; iter-1 [7,8,9,13,14,18] both signals; iter-2 directives [27,29,33,35,36,37,40,42,44,46,55,63,64,65,67,69,71,72,97,99,106,109,116] and project [33,35,36,37,42,44,46,55,65,67,72,98,100,107,110] plus failed [(68,'src/game.rs')]; iter-3 directives [6,50,70,73,74,80,84,86,90,93,97] and project [6,8,75,81,85,87,91,94,98] plus failed [(22,'src\\\\game.rs'),(69,'src\\\\game.rs')] and one undecided at 72. Token totals 3,651,120 / 2,626,195 / 13,091,431 / 5,223,211 also match."
  },
  {
   "id": "V4-ten-cut-directives",
   "pass": true,
   "evidence": "My replay of the withdrawn rule at K=32 aborts iter-3 at call 39 for 1,604,038 tokens and its directive writes after the end are exactly [50,70,73,74,80,84,86,90,93,97] - the acceptance's A-1 list, reproduced."
  },
  {
   "id": "V5-live-shell-writes-95-and-139",
   "pass": true,
   "evidence": "Call 95 (dumped raw): `powershell ... $p='src\\game.rs'; ... Set-Content -NoNewline -Encoding UTF8 $p $c` with a following findstr; extra.returncode 0 and the output shows the NEW constants (MOVE_SPEED 300.0, COIN_A_X 50.0, COIN_B_X 100.0, GOAL_X 150.0). It is the live call's last project write. Call 139: the same shape, extra.returncode 1, output `Missing closing ')' in expression. (ParserError)` - PowerShell never parsed it, so it changed nothing. The report REPRODUCES 95 and REFINES 139 (the acceptance had listed 139 as a further write and said it could not decide the bytes; the recording decides it)."
  },
  {
   "id": "V6-calls-8-and-22",
   "pass": true,
   "evidence": "iter-3 call 8 (dumped raw): `$p='src\\game.rs'; ... [IO.File]::WriteAllText($p,$t); (Get-Item $p).Length`, returncode 0, output `42502` - a real edit. Call 22: the script throws `json pattern missing` before its WriteAllText, returncode 1, output `json pattern missing` - failed. Call 69 fails the same way. The report reproduces the acceptance's call 8 and refutes call 22 as an edit; the further damage is the seven script-driven edits at 75-98, each of which I verified runs .hoh/scratch/tweak{3..9}.ps1 and prints a growing `ok bytes=...`."
  },
  {
   "id": "V7-honest-about-the-undecidable",
   "pass": true,
   "evidence": "iter-3 call 72 is a malformed directive (the closing HOH_END_WRITE_FILE is not last; the harness returned its help text, returncode 1). The tool records it as `undecided` and does NOT scan its body, so neither the script write nor the `powershell -File` line counts; my independent audit reaches the same single undecided entry. No other undecided exists in the four recordings, and the report states its blind spots (unknown verbs, unbound destinations, no byte identity) instead of hiding them."
  },
  {
   "id": "V8-A1-fixed",
   "pass": true,
   "evidence": "LIVE-COST-REPORT.md JSON `replay_through_the_shipped_guard`: round4_iter_3 directive_writes_after_the_end = [50,70,73,74,80,84,86,90,93,97], project_writes_after_the_end = [75,81,85,87,91,94,98], `zero_recorded_directive_writes_lost: false`. The old empty list and `true` are kept only inside a `what_this_block_said_before_the_correction` block with the root cause (the list was gathered inside the loop that stops at the abort). Section 4's table now reads ten/seven in prose and in the JSON."
  },
  {
   "id": "V9-A2-fixed",
   "pass": true,
   "evidence": "The false derivation lives outside the repository in the withdrawn patch; the record now states it: `what_the_constant_32_was_derived_from` quotes `31 = ...`, records that iter-3 has no write at call 18, that the longest visible-write-free window is 43 (6 -> 50) and the margin is -11. I reproduced the 43-call window from the raw recording."
  },
  {
   "id": "V10-A3-fixed",
   "pass": true,
   "evidence": "LIVE-COST-REPORT.md now reads project_write_calls [6,14,17,19,43,44,95], writes_by_shell_command [17,44,95], last_project_file_change_at_call 95, calls_after 55, tokens 1,788,003, share 0.4897 (I reproduced 1,788,003/3,651,120 = 0.4897). The old value is quoted as `what_this_entry_said_before_the_correction` with the reason (directive-only detector). The old 62.7 % is correctly called unreproducible; calls 45-150 are 2,910,202/3,651,120 = 0.7971 (I reproduced 79.71 %)."
  },
  {
   "id": "V11-A5-fixed",
   "pass": true,
   "evidence": "FIX-REPORT.md's lever block and section 5 now state the convention ([projected prompt over the first N calls, that prompt + the iteration's WHOLE recorded completion]), that the pairs reproduce the acceptance's independent F:/hof-acc6-work/composition.py exactly and do NOT reproduce the batch's own cost_measure.py (iter-2 first_60 [1,152,836, 1,386,920]), and that the published crossing is the curve's own at call 61 (60 -> 1,478,789, 61 -> 1,502,016), not an interpolation. `roughly 85 for iter-3` is withdrawn. Both scripts are present on disk and neither is in the repository; I did not re-derive compact_history."
  },
  {
   "id": "V12-A6-fixed-by-append",
   "pass": true,
   "evidence": "DECISIONS.md is append-only across both appends: b9546f5 (1,282,691 bytes) is a byte prefix of 1aeec7b (1,293,073, +10,382 = D303) which is a byte prefix of HEAD 05604b9 (1,295,073, +2,000 = D304). D302's and D303's own text are byte-identical to what they were; the stale sentences are superseded by restatement in the appended entries, not rewritten. The report's `appended_bytes: 10382` is correct. The batch's 05604b9 follow-up appends D304 to record that D303's own 'not committed' sentence went stale when the delegating agent committed the set - the A-6 pattern applied to itself."
  },
  {
   "id": "V13-withdrawn-not-shipped",
   "pass": true,
   "evidence": "grep for max_write_free_steps / WriteFreeBudgetExceeded over src/, config/, Cargo.toml and tests/ returns NOTHING. config/hoh.yaml has no such key; src/config.rs has no such field; src/harness/guard.rs has no such state or status. `replay_directive_step_budget` is defined once in src/harness/write_audit.rs and called only from its own unit test and tests/write_accounting.rs - no production call site. The withdrawn patch is present outside the repository at D:/hof-live-work/write-free-budget-WITHDRAWN.patch and was not touched."
  },
  {
   "id": "V14-two-bands-do-not-overlap",
   "pass": true,
   "evidence": "Recomputed from the raw recordings: the pass edge is unchanged - the last cumulative total under 1,500,000 is call 81 at 1,484,934 (call 82 is 1,511,382), so K <= 37. The iter-3 directive-window floor is unchanged - at K=42 iter-3 aborts at call 49 and cuts the seven real edits at 75-98; at K=43 it never fires. BUT the corrected accounting moves the global 'cut no recorded project write' floor: the live call's last directive write is 43 and its last project write is 95, so the rule fires at 44+K; for every K <= 51 it fires at or before call 95 and refuses that write (at K=43 it fires at call 87 with the tool's own project_writes_after(87) = [95]). The true global floor is K >= 52 (K >= 51 under the tool's strict `> abort` convention). 37 < 43 < 52: the bands still do not overlap and the damage is larger than the report says. This is defect D-1."
  },
  {
   "id": "V15-criterion-recorded-unmet",
   "pass": true,
   "evidence": "WRITE-ACCOUNTING-REPORT.md verdict and cost_criterion block: 3,651,120 total tokens = 2.434x the 1,500,000 target (criterion at .spec/bevy/ROUND-2-REPORT.md:43), `passes: false`; D303(d) records it as a decision; the only policy measured to pass (system prompt + task only, 899,962 = 0.600x) is refused and the refusal is recorded. I reproduced the live total from the 150 usage entries (3,537,843 prompt + 113,277 completion = 3,651,120, ratio 2.4341)."
  },
  {
   "id": "V16-gate",
   "pass": true,
   "evidence": "Run in my own build directory D:/hof-acc8-target, twice (before and after the mid-session commit): `cargo test --offline` literal exit code 0, 782 passed / 0 failed / 6 ignored / 788 listed over 59 `test result:` lines, 0 `warning:` lines in stdout and stderr; `cargo fmt --all --check` exit 0 emitting 0 bytes; `-- --list` exit 0 with 788 names; `-- --list --ignored` exit 0 with the same six engine tests. No test removed: between b9546f5 and HEAD the only src/tests changes are the +1 mod.rs line and the two new files carrying 16 tests (10 unit + 6 integration), all present and passing. Baseline 766/0/6/772 -> +16 tests, 0 removed. Free space checked first (D: 261 G, F: 66 G); nothing was deleted because nothing needed to be. The second run showed no cargo/rustc/hoh before or after."
  },
  {
   "id": "V17-tree-coherent-and-clean",
   "pass": true,
   "evidence": "Launch ledger runs/bevy-livecost1/launch-ledger.jsonl holds three launches with distinct nonces/pids/launch images; the identity/nonce/reap/fold/resume/push-gate tests are all in the 782 that passed (`the_engine_identity_step_is_a_gate_step`, the a_resume_* family, the compact::tests::* fold tests, a_repeated_action_*, the launch-ledger tests, the_gate_and_the_writer_agree_on_ledger_validity). No key-shaped material in the tracked tree: my scan of all 190 tracked files using the repo's prefix rule found only the declared fixtures in tests/credential_scan.rs (my broader regex's other hits are substrings such as `...the_ta|sk_leading...`). The two known gitignored historical files exist and both 51-char key-shaped tokens hash to sha256 5cf81e8f. Frozen documents and the other batch reports are untouched: `git diff --name-status b9546f5 HEAD -- .spec/` shows only the two authorised corrections (FIX-REPORT.md, LIVE-COST-REPORT.md) and the new WRITE-ACCOUNTING-REPORT.md. Nothing was pushed: HEAD is not in any remote ref, the only remote ref is origin/master at 6553afe, and bevy-core is local-only."
  },
  {
   "id": "V18-tree-scope-and-evidence-location",
   "pass": true,
   "evidence": "190 tracked files whose top-level entries are .gitattributes, .githooks, .gitignore, .spec, Cargo.lock, Cargo.toml, DECISIONS.md, config, scripts, src, tests - the harness plus this engine's flow, nothing else. The report states plainly that every cost figure rests on runs/**, which is gitignored; I measured runs/** myself at 11,229 files / 12,775,066,006 bytes / 11.898 GiB, exactly the reported figures."
  }
 ],
 "defects": [
  {
   "id": "D-1-safe-band-floor-understated",
   "severity": "low",
   "what": "The corrected accounting moves the global 'cut no recorded work' floor, and the report does not move it. LIVE-COST-REPORT.md section 4 says 'To leave every recorded call's artifact work intact it must not fire before round-4 iter-3's call 50, so K >= 43', and both machine blocks say 'cutting nothing recorded needs K >= 43'. That is only the round-4 iter-3 directive-window bound. At K=43 the live call's rule fires at call 87 (last directive write 43, abort = 44+K) and the batch's own project_writes_after(87) is [95], so the live call's call-95 src/game.rs write - the last artifact write in the recording - is refused at the K the report calls safe. The global floor is K >= 52 (K >= 51 under the tool's strict `> abort` convention). The report half-sees this (it says the cut side is 'worse' at K=32) but leaves the bound at 43.",
   "reproduction": "My replay: for K in 1..60, live abort = 44+K; at K=43 it is call 87 with 1,651,225 cumulative tokens and the live call's project write at 95 is cut; at K=51 it is call 95 (the write itself refused); at K=52 it is call 96 and nothing recorded is cut. F:/hof-acc8-work/audit.py, section '### bands'. The effect on the conclusion is in the strong direction: 37 < 43 < 52, so the bands still do not overlap and the lever is worse than reported."
  }
 ],
 "risks": [
  {
   "id": "R-1",
   "risk": "Only one live Developer call has ever been measured (a first-iteration call on a fresh project). Whether an iteration-2-shaped call is anywhere near 1,500,000 total tokens is unmeasured; the recorded round-4 iter-2 is 13,091,431.",
   "why_it_matters": "The criterion is stated per Developer call; closing it on one iteration-1 call would not close it."
  },
  {
   "id": "R-2",
   "risk": "Every cost conclusion rests on runs/** (11.898 GiB, gitignored). A clone, a CI run or another machine cannot re-run the accounting tests or reproduce any number.",
   "why_it_matters": "The project's own criteria include reproducible evidence. The batch discloses this rather than hiding it, and the test fails loudly without the recordings, but the evidence remains a single-disk artefact."
  },
  {
   "id": "R-3",
   "risk": "The withdrawn patch still on disk (D:/hof-live-work/write-free-budget-WITHDRAWN.patch) carries the false `32 = 31 + 1` derivation in its config and config.rs doc comments, at K=32.",
   "why_it_matters": "Re-applying it without correcting the comment reproduces A-1 exactly; D303 records this."
  },
  {
   "id": "R-4",
   "risk": "A tree-fingerprint signal (the only signal that can see shell writes) is still unmeasured; no offline replay may execute the recorded shell commands.",
   "why_it_matters": "It is the project's stated next lever and needs another live round before it can be judged."
  },
  {
   "id": "R-5",
   "risk": "HEAD moved during this acceptance (1aeec7b at start, 05604b9 after the delegating agent's doc-only append). My verdict pins 05604b9.",
   "why_it_matters": "Any further commit invalidates the exact hash in this report; the gate and the accounting are unaffected because 05604b9 changes no source."
  }
 ],
 "unverified": [
  "The lever pairs and the compact_history projections (F-4/A-5): I did not re-implement the fold or re-derive the pairs from wire bytes. I confirmed the convention is now stated, the false provenance is corrected, both named scripts exist on disk, and the previous acceptance's independent composition.py reproduction. The absolute numbers are taken as given.",
  "Byte-level identity of the content written by the successful shell writes (call 95, iter-3 call 8, the seven tweak scripts): the recording proves a write ran and reported success and prints new values/lengths; it does not prove the bytes differ from what was there. The tool itself refuses to claim this.",
  "That a clone actually fails rather than silently passing the accounting tests: I verified `git ls-files runs` is empty and the test asserts `path.is_file()`, but I did not build a clone without the recordings.",
  "Whether the recorded PowerShell/python heredocs would have written what they appear to write had they parsed: no recorded command was executed.",
  "The tester's and second/third iterations' cost: the criterion is stated for the Developer call only."
 ]
}
```


# ACCEPTANCE-ACCOUNTING — independent acceptance of the round-7 write-accounting batch

Independent, offline acceptance of `bevy-core` at **`05604b9`**. No engine, no game, no
network, no model call, no round and no Developer call was run. I did not write under
`runs/**`, did not construct a path from an unexpanded variable, did not use
`git checkout --`, did not commit, stage or push, and did not fix anything. The committed
tree was clean when I read it. The machine-readable verdict above is serialiser output and
is parsed back out of this written file before the file is considered written.

The one thing worth saying first: the exact hash moved while I worked. The batch's work was
committed as `1aeec7b`; during this acceptance the delegating agent added a doc-only append
as `05604b9` (D304 plus the `working_tree_at_end` field). The verdict pins `05604b9`; the
two commits differ in no source file, and my gate was run on both.

## 1. What I did, and with what

* I wrote my own accounting from scratch, outside the repository
  (`F:/hof-acc8-work/audit.py`): my own transcription of the directive grammar, my own
  shell / PowerShell / Python / script-run write detector, my own return-code pairing, and
  my own replay of the withdrawn rule. It shares no code with `src/harness/write_audit.rs`.
  It reproduces every published timeline and every published K number.
* I dumped the raw calls the acceptance named (`F:/hof-acc8-work/dump_calls.py`):
  live 17 / 44 / 95 / 139, iter-3 8 / 22 / 69 / 72 / 75 / 81 / 85 / 87 / 91 / 94 / 98.
* I ran the repository's own tool through its tests in my own target directory
  (`D:/hof-acc8-target`): all 6 `tests/write_accounting.rs` tests and all 10
  `harness::write_audit` unit tests pass.
* I ran the whole gate twice, parsed the counts from the captured output, and measured the
  runs tree, the tracked-file list and the key scan myself.

## 2. Per-item results

| id | item | result | evidence (abridged) |
|---|---|---|---|
| V1 | the corrected accounting is in the tree | **pass** | `write_audit.rs` + `tests/write_accounting.rs` tracked and added by `1aeec7b` |
| V2 | tool and inputs present; re-runnable | **pass** | four trajectories present at the reported sizes; `git ls-files runs` = 0; tests fail loudly without them |
| V3 | independent reproduction | **pass** | my own script matches all four timelines and totals |
| V4 | the ten cut directives | **pass** | `[50,70,73,74,80,84,86,90,93,97]` at K=32, iter-3 abort 39 |
| V5 | live shell writes 95 / 139 | **pass** | 95 rc 0 with new constants, last write; 139 rc 1 `Missing closing ')' in expression`, changed nothing |
| V6 | iter-3 calls 8 / 22 | **pass** | 8 rc 0 `42502`; 22 rc 1 `json pattern missing`; 69 likewise |
| V7 | honest about the undecidable | **pass** | only undecided is iter-3 call 72 (malformed directive); blind spots stated |
| V8 | A-1 fixed, machine/prose consistent | **pass** | after-lists now ten / seven; `zero_recorded_directive_writes_lost: false`; old values only in a before-quote |
| V9 | A-2 fixed | **pass** | no write at 18; window 43 (6→50); margin −11 |
| V10 | A-3 fixed | **pass** | last change 95; 55 calls / 1,788,003 / 48.97 %; old 62.7 % called unreproducible |
| V11 | A-5 fixed | **pass** | convention stated; composition.py yes / cost_measure.py no; crossing is call 61 |
| V12 | A-6 fixed by append | **pass** | DECISIONS.md byte-prefix chain b9546f5→1aeec7b→05604b9; D302/D303 text intact |
| V13 | withdrawn experiment not shipped | **pass** | no key, no guard state, no status, no production call site |
| V14 | the two bands do not overlap | **pass** | 37 < 43, and under the corrected accounting the safe floor is 52 (defect D-1) |
| V15 | criterion recorded as unmet | **pass** | 3,651,120 = 2.434×, `passes: false`, D303(d), refusal of the only passing policy |
| V16 | gate | **pass** | exit 0; 782 / 0 / 6 / 788; 0 warnings; fmt exit 0 with 0 bytes; no test removed |
| V17 | tree coherent, clean, unpushed, no keys | **pass** | ledger + identity + tripwire + fold + resume tests green; only `credential_scan` fixtures; nothing pushed |
| V18 | scope and evidence location | **pass** | 190 tracked files, harness only; `runs/**` 11,229 files / 11.898 GiB, gitignored |

## 3. The corrected accounting, reproduced

Three signals, and the recording itself decides the effect. What I confirmed on the raw
recordings:

* **The ten cut write directives.** At K=32 the withdrawn rule ends round-4 iteration 3 at
  call 39 for 1,604,038 tokens, and the successful write directives after that point are
  `50, 70, 73, 74, 80, 84, 86, 90, 93, 97`. The old JSON said `[]`; the old `true` was a
  loop degeneracy, exactly as the acceptance found.
* **The live call's late shell write.** Call 95 is a real write and is the *last* project
  change: return code 0, and the `findstr` it runs prints the new values. Call 139 is a
  write *command* whose recorded return code is 1 with a PowerShell parse error: it changed
  nothing. The report refines the acceptance here, and the recording supports the
  refinement.
* **The window that is not idle.** Iteration 3's 43-call visible-write-free window (6→50)
  contains call 8, which ran `[IO.File]::WriteAllText($p,$t)` with `$p='src\game.rs'` and
  returned `42502`; call 22 threw `json pattern missing` before its write and call 69 did
  the same; call 72 is a malformed directive the harness never executed. The real further
  edits are the seven script-driven ones at 75-98, each of which runs a
  `.hoh/scratch/tweak{3..9}.ps1` that the role wrote on an earlier call and prints a
  growing `ok bytes=...`.

**Reproduced**: the ten directives, the live 95/139 pair, iter-3's 8/22 pair (with 22
refuted as an edit), the abort calls and token totals at K=32 for all four recordings
(live 76 / 1,357,530; iter-1 51 / 1,790,635; iter-2 never; iter-3 39 / 1,604,038), the
43-call window, the 66-call project window, and the live tail of 55 calls / 1,788,003 /
0.4897.

**Cannot be decided by anyone offline**: byte-level identity of what a successful shell
write put on disk. The tool refuses to claim it and so do I.

## 4. The withdrawn experiment

The rule is not in the shipped code. `max_write_free_steps` and `WriteFreeBudgetExceeded`
appear nowhere under `src/`, `config/`, `Cargo.toml` or `tests/`; there is no config key, no
guard state and no status. The only implementation in the tree is
`write_audit::replay_directive_step_budget`, a measurement function called only by tests.

The two bands, recomputed from the raw recordings:

| bound | value | derivation |
|---|---|---|
| to meet the criterion | **K ≤ 37** | last cumulative under 1,500,000 is call 81 at 1,484,934; call 82 is 1,511,382 |
| to cut no directive write / leave iter-3 intact | **K ≥ 43** | at K=42 iter-3 fires at 49 and cuts 75-98; at K=43 it never fires |
| to cut no recorded **project** write anywhere | **K ≥ 52** | the live call fires at 44+K; K ≤ 51 refuses its call-95 write |

37 < 43 < 52. The bands do not overlap, and the corrected accounting makes the losing side
worse than the report says — which is defect D-1, not a rescue.

## 5. Defects

**D-1 (low) — the safe-band floor is understated.** See the machine block. The report's "K
≥ 43 to cut nothing recorded" is the round-4 iteration-3 bound only. At K=43 the live call's
budget fires at call 87 and its own `project_writes_after(87)` is `[95]`, so the live call's
last artifact write is refused at the K the report calls safe; the global floor is K ≥ 52. I
return **pass** anyway, because the error is in the conservative direction — it understates
how bad the lever is, and the headline ("the bands do not overlap") is true and stronger
than reported. It is a residual imprecision of exactly the kind this batch was fixing, and a
future batch should restate the bound rather than leave it.

No other defect was found. In particular, I checked for the failure modes the previous
acceptance named: a degenerate metric (none — the after-lists come from the whole
recording), a constant derived from a non-existent window (corrected in the record, margin
−11), a restated write profile (consistent with the prose), lever provenance (convention
stated, the right script named), and a "not committed" entry that was committed (superseded
by an appended D304, D303's own text untouched).

## 6. Counterexamples I looked for and did not find

* A project write after the live call's call 95. My completeness scan flags every command
  that names a project path with a write-ish token and is not accounted; the only hits are
  false positives (`copy /Y src\game.rs .hoh\scratch\game_a.rs` copies *out* of the
  project; `dir`/`Select-String`/`Get-Item` reads). No unaccounted write.
* An unaccounted write in round-4 iterations 1 and 2. My first pass missed call 68 (a
  `python - <<"PY"` heredoc carrying `open(p,'w')` for `p='src/game.rs'`, which `cmd.exe`
  refused with `<< was unexpected at this time`); on inspection the recording supports the
  tool's failed-write entry, so the tool is the more complete instrument here.
* A test name that disappeared. The only src/tests changes since the 772-test baseline are
  one `mod` line and two new files; the 16 new tests are enumerated in the ignored/list
  run.
* A key in the tracked tree. My scan of all 190 tracked files found only the declared
  fixtures in `tests/credential_scan.rs`; every other hit is a substring of an identifier
  (`...the_ta|sk_leading...`).

## 7. What I could not establish

The lever pairs and the `compact_history` projections — I did not re-implement the fold, and
I take the previous acceptance's reproduction of `composition.py` as given. Byte identity of
the successful shell writes — the recording proves a write ran and prints new values, not
that the bytes changed. That a clone fails rather than silently passing — I verified the
empty `git ls-files runs` and the `is_file()` assertion, but did not build a clone without
the recordings.

## 8. Does the cost criterion pass? Is the tree fit for its first push?

**The cost criterion does not pass.** 3,651,120 total tokens against 1,500,000 is 2.434×,
the call was ended by its step budget rather than by finishing, and no shipped lever changes
it. The only policy measured to pass is the context-narrowing one the project refuses. This
is now written down as a decision (D303(d)) instead of being papered over.

**The tree is fit for its first push with that criterion recorded as unmet rather than
fixed.** The accounting blindness that produced the false write profiles is fixed, is in the
tree, is independently reproducible on this machine, and is pinned by tests that go red when
it is broken. The false statements are corrected in the record, with the previous wording
quoted rather than erased. The withdrawn experiment stays withdrawn and its two bands do not
overlap. The gate is green with no test removed. Nothing is pushed, the tree is clean, and
the one caveat a reviewer must carry forward is stated in the report itself: the evidence
lives only under the gitignored `runs/**` on this disk, so the cost conclusions are
reproducible here and nowhere else.
