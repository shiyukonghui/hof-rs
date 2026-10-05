```json
{
 "schema": "hof-rs / bevy independent acceptance of the record-correction batch for ACCEPTANCE-CLONE-LIVE defects D-1..D-4 (.spec/bevy/RECORD-CORRECTION-REPORT.md)",
 "produced_at": "2026-10-06",
 "branch": "bevy-core",
 "head_under_acceptance": "f1b9af3ab163f211db62aca233e97e229b7ffd10 (`docs(record): correct the launch identity, the pass attribution and the stale residual entries to match the artefacts`), whose only difference from aee9c92 is the correction report's own final revision. The corrective batch was committed in two steps while it was still working: aee9c92 mid-flight, then f1b9af3 at 00:40:23. The working tree was DIRTY during this acceptance (RECORD-CORRECTION-REPORT.md modified at 00:34:45) and was clean again at f1b9af3 when the acceptance finished; see defect P-1. `git status --porcelain` is empty at f1b9af3.",
 "offline": true,
 "what_this_acceptance_did_not_do": "No engine, no game, no network, no model call, no round and no Developer call was run. Nothing was written under `runs/**`. No `git checkout --` was used. Nothing was committed, staged or pushed. Nothing was fixed. No path was constructed from an unexpanded variable. No `rm -rf` was used anywhere; nothing was deleted. No file in the repository was tampered with or restored; every helper script lives under `F:/hof-acc11-work/` and every log and build artefact under `F:/hof-acc11-logs/` and `D:/hof-acc11-target/`, outside the repository.",
 "verdict": "fail",
 "headline": "The four record defects the previous acceptance named are corrected, and I verified every corrected value against the artefacts rather than against either document: the launch artefact really is nonce ff44b5f7 / pid 57592 / image eb328de6, the ten-step table really is the 70-call iteration-3 pass with jump 28 at [41..68] and liveness at [69,70], each pass's liveness is attributed to its own ledger launch with the whole pass window bracketed between that ledger line and the next, and evidence/index.json and prd_surfaces.rs::RESIDUALS no longer say the step never ran. The gate is green on this exact HEAD: `cargo test --offline` exit 0, 800 passed / 0 failed / 6 ignored / 806 listed over 60 `test result:` lines, `cargo fmt --all --check` exit 0 with 0 bytes, 0 warning lines, 0 test attributes added or removed. I nevertheless return fail, because the correction introduced two fresh false statements into the committed record and left one old one in place: (RD-1) the correction grew evidence/index.json by 719 bytes, so `evidence/` as a directory is now 122 files / 4,798,968 bytes and the four non-corpus files total 27,829 bytes, while `evidence/README.md` (unchanged by the correction), `CLONE-AND-LIVE-REPORT.md` and `DECISIONS.md` still state 4,798,249 and 27,110 - and the batch's own gate analysis asserted the meaning-string edit `cannot move a byte count`; (RD-2) the correction report's `changed_files` entry for itself states that the aee9c92 revision (git blob afde67da) has sha256 889033a5..., which is CLONE-AND-LIVE-REPORT.md's hash - afde67da's sha256 is cebea19e...; (RD-3) `.spec/bevy/COVERAGE-EVIDENCE-REPORT.md` still asserts, 13 times, that the liveness step never ran, which the round's own artefacts falsify (disclosed by the batch, and left in place by its instructions). The cost criterion still fails at 2.55-2.60x the 1,500,000-token per-call target with `agent.step_limit: 150` binding, and that is recorded honestly.",
 "criteria": [
  {
   "id": "A1-d1-launch-identity",
   "pass": true,
   "evidence": "Read from the artefact, not from either document. `runs/bevy-clonefix1/launch.json` identity: nonce = answered_nonce = ff44b5f7-ed96-43b2-8942-1dec7f6b54b8, spawned_pid = answering_pid = listening_pid = 57592, launch_image runs\\bevy-clonefix1\\launch-image\\eb328de6-7379-4cb4-a965-92563b0b2d41\\hof_game.exe, verified true. `runs/bevy-clonefix1/meta.json` segments.pid = 57592. `runs/bevy-clonefix1/launch-ledger.jsonl` has 7 lines, and line 2 holds exactly the nonce/pid the old prose had named (fb53d29e / 51360) and carries NEITHER `answered_nonce` NOR `listening_pid` - I checked the keys of all 7 ledger lines; none has either field. The corrected prose (CLONE-AND-LIVE-REPORT.md lines 1623-1632) and the machine block's identity_gate (lines 196-227) now both state ff44b5f7 / 57592 / eb328de6 and agree with each other and with the artefact, and both state that no earlier pass keeps those fields. The machine block also adds identity_gate.pass (iteration 3) and identity_gate.earlier_passes."
  },
  {
   "id": "A2-d2-d4-per-pass-attribution",
   "pass": true,
   "evidence": "I derived each pass from its own raw directory under runs/clonefix1/iter-{1,2,3}/candidate/.hoh/deterministic/raw/ and from the embedded timestamp_ms of every call. iteration 1 (ledger pid 51360, launched_at 1791206961): distinct sequence ids 1..64 with none missing, e3_jump_arc 22 calls at ids 41..62, e3_process_liveness at ids 63/64 with frames 753 -> 763 and timestamp_ms 1791206975774/1791206975944; its whole pass window is 1791206972198..1791206975944, inside the ledger interval 51360@1791206961 -> 46120@1791206980. iteration 2 (pid 45996, 1791209819): ids 1..70, jump 28 at 41..68, liveness 69/70, 712 -> 722 at 1791209832571/1791209832740, window 1791209828774..1791209832740 inside 45996@1791209819 -> 35364@1791209836. iteration 3 (pid 57592, 1791212646): ids 1..70, jump 28 at 41..68, liveness 69/70, 712 -> 722 at 1791212659847/1791212660017, window 1791212656053..1791212660017 inside 57592@1791212646 -> 39664@1791212664. The machine block's live_round.liveness (lines 891-1016) points at iteration 3's own file with those exact frames/calls and adds attribution_by_pass carrying all three with each raw path, frames, two calls, pass window and ledger pid/launched_at - every value matches what I derived, and each observation is paired with its own launch, not another pass's. Prose lines 1638-1660 agree. Separately, runs/bevy-clonefix1/readings/e3-observations.json holds 70 distinct ids 1..70 with none missing (movement 5 [9..13], coins/win/win_position 25 [1..7,14..31], jump 28 [41..68], grounded 7 [1..7], movement_left 6 [32..37], movement_release 3 [38,39,40], grounded_payload 1 [8], liveness 2 [69,70] frames 712 -> 722 at the same two timestamps as iteration 3's raw file), and runs/bevy-clonefix1/calls holds 70 files whose 0063/0064 are bevy_player_transform and 0069/0070 bevy_wait_frames - so the corrected sentence's `70 call files`, `e3_jump_arc [41..68]` and `e3_process_liveness [69,70]` are exactly what the file it names says, and the `64-call layout` it attributes to iteration 1 is iteration 1's own coverage (1..64)."
  },
  {
   "id": "A3-d3-index-and-residuals",
   "pass": true,
   "evidence": "`git show aee9c92 -- evidence/index.json src/adapter/bevy/prd_surfaces.rs` is one replaced `meaning` line in index.json and 16+/11- lines in prd_surfaces.rs (a doc comment plus the one `S1-deterministic-step` RESIDUALS entry). Neither file now contains `never executed against a real game`, `has ever been produced` or `never run against a real game` as a live claim. index.json's `coverage.with_the_new_step.value` ({verified 15, total 19, gap 0, unobservable 4, decidable 15}), its `files` and `command` and its `repo_independent: true` are all unchanged by the diff; only the prose meaning grew, and it keeps the honest boundary that the round's recordings live under the gitignored runs/ and that the figure stays the repository-reproducible projection. prd_surfaces.rs's `PRD_SURFACES` registry (19 ids, which I counted in EXPECTED_IDS) is untouched. Of the two RESIDUALS, `P3-goal-x` is unchanged and is genuinely still open with its reason (the goal entity's own position is not one of the seven frozen surfaces and an eighth would be a contract change), and `S1-deterministic-step` is now labelled OBSERVED while still carrying its disposition and the caveat that the observation is not part of the committed evidence/ corpus - i.e. the list is not used to claim the residual was closed. Nothing in either file was weakened to make a claim true; the observation the new text cites is real (A2)."
  },
  {
   "id": "A4-no-over-correction",
   "pass": true,
   "evidence": "aee9c92 touches exactly 4 paths (.spec/bevy/CLONE-AND-LIVE-REPORT.md, .spec/bevy/RECORD-CORRECTION-REPORT.md new, evidence/index.json, src/adapter/bevy/prd_surfaces.rs) and f1b9af3 touches only the correction report; `git diff --name-only 71dcebd f1b9af3` is those same 5 paths. `.gitattributes`, config/hoh.yaml, src/adapter/bevy/battery.rs, the PRD_SURFACES registry, the ten-step battery, and every frozen document (PRD.md, REQUIREMENTS.md, DESIGN-OVERVIEW.md, DESIGN-DETAIL.md, both spike reports) are byte-identical across the correction; DECISIONS.md was not touched at all. The one measured number the diff DOES move is the e3_jump_arc row in the report's machine block (22 calls / ids 41..62 -> 28 / 41..68, plus 6 more player_transform tool entries in the raw_call_ids), and that is a change to match the artefact the sentence names (e3-observations.json, and iteration 3's raw file), not a document - it is disclosed in RECORD-CORRECTION-REPORT.md section 2 and in its `contradictions_found.C-2`, and I confirmed 28 is what the artefact says. So no measured figure was adjusted to match a document. However, the batch's index.json edit moved a measured figure it did not reconcile: see defect RD-1, which is why A4 passes on the diff but A7 fails."
  },
  {
   "id": "A5-gate",
   "pass": true,
   "evidence": "Free disk checked first (D: 180-189 G, F: 56 G free at every point); nothing was deleted and no `rm -rf` was used, so there was nothing to free. Own build directory `D:/hof-acc11-target` (measured 9.1 G), no second test process: the two other cargo/rustc processes I saw (a `cargo test --offline -- --list --ignored`, created 00:32:14) belonged to another agent, finished before I started, and my own commands ran strictly one at a time. On the frozen tree at f1b9af3: `CARGO_TARGET_DIR=D:/hof-acc11-target cargo test --offline` -> literal exit code **0**, **800 passed / 0 failed / 6 ignored** over 60 `test result:` lines; `cargo test --offline -- --list` -> exit 0 with **806** `: test$` names; `cargo test --offline -- --list --ignored` -> exit 0 with the same **6** real-engine names; `cargo fmt --all --check` -> exit 0 with **0 bytes** on stdout and stderr; **0** `warning:` lines in both streams. No test removed: `git diff aee9c92^ aee9c92 -- src tests | grep -c '^[+-].*#\\[test\\]'` is 0, 806 listed equals the previous baseline, and `the_full_battery_scores_the_registry`, `a_liveness_observation_counts_as_measured`, `the_identity_fields_are_computed_from_the_facts_not_asserted`, `the_context_fold_shrinks_every_recorded_round_four_developer_call`, `the_repeated_success_tripwire_fires_on_the_recorded_grind`, the `a_resume_*` family and `a_process_that_never_binds_the_endpoint_gives_up_on_its_budget` are all present in the 806-name list. A first identical run was made before the tree went dirty mid-acceptance and an identical second run on f1b9af3; all three runs of the gate (the batch's logs3, my first, my second) report 800/0/6/806, 0 warnings, fmt 0 bytes, and the gate inputs (evidence/index.json, prd_surfaces.rs, and src/tests) are byte-identical across all of them."
  },
  {
   "id": "A6-tree-for-a-push",
   "pass": true,
   "evidence": "320 tracked files whose only top-level entries are .gitattributes, .githooks, .gitignore, .spec, Cargo.lock, Cargo.toml, DECISIONS.md, config, evidence, scripts, src, tests; `git ls-files runs` is empty. The launch ledger runs/bevy-clonefix1/launch-ledger.jsonl holds 7 launches with 7 distinct nonces, 7 distinct pids and 7 distinct images (I enumerated them), and its penultimate line is verbatim the surviving launch.json identity. Identity computation, the tripwire, the history fold, resume and battery coherence are inside the green gate (`the_identity_fields_are_computed_from_the_facts_not_asserted`, `the_verified_endpoint_carries_the_nonce_and_the_listeners_pid`, `the_ledger_line_is_written_after_the_spawn_and_says_so`, `the_pid_a_ledger_never_named_is_left_alone`, `the_context_fold_shrinks_every_recorded_round_four_developer_call`, `the_repeated_success_tripwire_fires_on_the_recorded_grind`, `the_gate_and_the_writer_agree_on_ledger_validity`, 7 `a_resume_*` tests, 30 battery tests - all present in the list and all green). No key-shaped material in the tracked tree: my own transcription of keys.rs's rule (KEY_PREFIXES with body >= 16, boundary rules) over all 320 tracked files finds exactly one prefixed token, the 27-character `sk-...` literal inside tests/credential_scan.rs, which declares `FIXTURE_SOURCES = [\"tests/credential_scan.rs\"]`; my positive control fires and the `async-task-...` negative control does not. Frozen documents are byte-identical across 71dcebd..f1b9af3 and the only batch report the correction touched is the one it was authorised to correct (CLONE-AND-LIVE-REPORT.md, per the previous acceptance's D-1/D-2/D-4). DECISIONS.md was not modified by the correction, so it remains append-only. Nothing is pushed: refs/heads/bevy-core is f1b9af3 while refs/remotes/origin/bevy-core is still 5f526d2, and I neither committed, staged nor pushed. The working tree IS clean at f1b9af3, but it was not clean while this acceptance ran (P-1)."
  },
  {
   "id": "A7-what-stands-between-the-tree-and-the-goal",
   "pass": false,
   "evidence": "Four of the goal's five criteria still pass and one still fails, but the record-accuracy criterion does not pass cleanly for the reasons below. DECIDABILITY: passes - the registry still holds 19 frozen ids (I counted EXPECTED_IDS), the denominator is a function of the PRD, and Q-startup and B2.1 are decided by the persisted iteration-3 observation. REPRODUCIBILITY: passes - `evidence/** -text` is committed (`git check-attr` -> text: unset), the working tree's evidence/ has 0 CR bytes, and `tests/evidence_reproduction.rs` re-derives the 118-file / 4,771,139-byte corpus green in the gate (I did not re-clone; see unverified). COST: FAILS and is recorded honestly - from runs/clonefix1/iter-{1,2,3}/usage.json the Developer calls are 150 calls / 3,900,735, 3,823,313, 3,905,662 tokens, exit_status LimitsExceeded in all three, i.e. 2.600x / 2.549x / 2.604x the 1,500,000 target (config/hoh.yaml artifact_write_budget_tokens) with `agent.step_limit: 150` binding; result.json.write_failures and issues are [] in all three, so the tripwire never fired. The corrected report's section 3, section 6 and `single_most_important_thing_next_batch` all state this, and RECORD-CORRECTION-REPORT.md repeats it. FROZEN CONTRACT: passes - PRD.md and the other frozen documents are byte-identical, DECISIONS.md is append-only (untouched), and no key-shaped material is committed. HONEST RECORD: does not pass cleanly - the two new false statements RD-1 and RD-2 sit in the committed tree, and RD-3 remains in a committed batch report."
  }
 ],
 "defects": [
  {
   "id": "RD-1",
   "severity": "medium",
   "what": "The correction's edit to `evidence/index.json` falsified the directory byte total stated in the file it never touched and in its own deliverable, and the batch's gate analysis asserted it could not. `evidence/index.json` grew from 14,851 bytes at aee9c92^ to 15,570 bytes at HEAD (+719), so `evidence/` as a directory is now **122 files / 4,798,968 bytes** and the four non-corpus files (index.json 15,570 + README.md 4,073 + tools/build_evidence.py 4,731 + tools/keyscan.py 3,455) total **27,829 bytes**. `evidence/README.md` line 30 (unchanged by the correction) still says the directory `holds 122 files / 4,798,249 bytes`; `CLONE-AND-LIVE-REPORT.md` line 154 (the E-7 `change`) and lines 1695-1696 (§4) still say `122 files / 4,798,249 bytes ... (4 files / 27,110 bytes)`; `DECISIONS.md` D306 line 11628 and COVERAGE-EVIDENCE-REPORT.md repeat it. The 118-file corpus figure the tests pin, 4,771,139 bytes, is still exactly right - only the directory total and the excluded-files total are now false. The batch's own reasoning in RECORD-CORRECTION-REPORT.md is the source of the miss: `index.json itself is excluded from that corpus count, so the corrected meaning string cannot move a byte count` is true of the corpus and false of the directory, while the batch's `not_touched` list claims `every measured number in any report` is untouched.",
   "reproduction": "`git ls-tree -r -l HEAD evidence | awk '{n++; s+=$4} END {print n, s}'` -> `122 4798968` (this is the committed, would-be-pushed total, not a working-tree artefact). `git cat-file -s aee9c92^:evidence/index.json` -> 14851; `git cat-file -s HEAD:evidence/index.json` -> 15570. `git diff --stat aee9c92^ aee9c92 -- evidence/README.md` is empty, so README.md was true before the correction and false after it. `sed -n '27,33p' evidence/README.md` still prints 4,798,249. No test reads evidence/README.md or those totals (grep over tests/, src/, scripts/ finds no byte-count reference), which is why the green gate does not catch it."
  },
  {
   "id": "RD-2",
   "severity": "low",
   "what": "The correction report's own `changed_files` entry for itself mis-states a hash. Line 144 says aee9c92 committed an earlier revision of RECORD-CORRECTION-REPORT.md, `(blob afde67da, sha256 889033a5fd8914357886b28f110609dcffad571194e844d03e5db7d3fb44471e)`. 889033a5... is CLONE-AND-LIVE-REPORT.md's sha256 (correctly used on line 129 and in gate.gate_input_sha256); git blob afde67da's sha256 is cebea19e0f955369a3a7fc8012f785c3f2d8939cde43208e5f7052af98f1d4e3. The delivered revision (blob 19333a53..., the f1b9af3 content) is a third value. Every other hash the report pins is correct: I recomputed evidence/index.json = eb88286c..., src/adapter/bevy/prd_surfaces.rs = 6ea1090b..., CLONE-AND-LIVE-REPORT.md = 889033a5..., and all three match the working tree and HEAD.",
   "reproduction": "`git cat-file -p afde67da | sha256sum` -> cebea19e0f955369a3a7fc8012f785c3f2d8939cde43208e5f7052af98f1d4e3; `sed -n '144p' .spec/bevy/RECORD-CORRECTION-REPORT.md` names 889033a5... for that same blob. `sha256sum evidence/index.json src/adapter/bevy/prd_surfaces.rs .spec/bevy/CLONE-AND-LIVE-REPORT.md` reproduces the other three exactly."
  },
  {
   "id": "RD-3",
   "severity": "low",
   "what": "`.spec/bevy/COVERAGE-EVIDENCE-REPORT.md` still asserts, 13 times, that e3_process_liveness never ran against a real game (`PENDING ITS FIRST REAL OBSERVATION`, `no raw/e3_process_liveness.json has ever been produced`, `it has never executed against a real game`), while the same file's own disposition at line 565 already records that the follow-up round produced the observation. The round's artefacts refute the live wording (three persisted raw files, observed true). The correction batch disclosed this in `contradictions_found.C-3` and left it untouched because its instructions forbade editing batch reports and the previous acceptance's D-3 named only evidence/index.json and prd_surfaces.rs. It is recorded here as a real, disclosed inconsistency in the committed tree rather than as a failure of this batch's mandate.",
   "reproduction": "`git grep -n -e 'PENDING ITS FIRST REAL OBSERVATION' -e 'has ever been produced' -e 'never executed against a real game' HEAD -- .spec/bevy/COVERAGE-EVIDENCE-REPORT.md` -> 13 hits; `sed -n '565p'` of that file records the opposite; the three raw files exist at runs/clonefix1/iter-{1,2,3}/candidate/.hoh/deterministic/raw/e3_process_liveness.json and are observed true."
  },
  {
   "id": "P-1",
   "severity": "low",
   "what": "Process defect, disclosed by the batch itself: the artefact under acceptance was not fixed while I accepted it. RECORD-CORRECTION-REPORT.md was modified at 00:34:45 (during this acceptance; its sha256 went from cebea19e... to 19333a53...), and the dispatcher committed f1b9af3 at 00:40:23 - the same mid-flight commit that produced aee9c92 while this and the previous batch were still working. `git status --porcelain` showed ` M .spec/bevy/RECORD-CORRECTION-REPORT.md` for the first ten minutes of my run. It is now clean at f1b9af3, I re-ran the whole gate on that HEAD, and the three gate-input files are byte-identical across every revision, so the numbers above belong to the tree that would be pushed; but a verdict could not be pinned to a single revision for the whole run.",
   "reproduction": "`git log --oneline -3` shows f1b9af3 on top of aee9c92; `git show --stat f1b9af3` touches only .spec/bevy/RECORD-CORRECTION-REPORT.md; `git diff --name-only aee9c92 f1b9af3` is that one path. Observed live: status ` M ...` at 00:39:44-00:40:15, empty from 00:40:25."
  }
 ],
 "risks": [
  {
   "id": "R-1",
   "risk": "The cost criterion remains unmet and is now measured three more times: 2.55-2.60x the 1,500,000-token per-call target, every call ended by the 150-call step limit, the tripwire never firing.",
   "why_it_matters": "It is the one goal criterion that still fails, and the round shows the withdrawn write-free budget does not address the binding constraint; a push would carry an unmet criterion into the next stage."
  },
  {
   "id": "R-2",
   "risk": "A clone's green gate is weaker than this machine's: three recorded-evidence tests (two round-2, one round-1) print a reason and return when their gitignored recording is absent, so a clean checkout exercises 800 passes of which three assert nothing.",
   "why_it_matters": "It is disclosed, but the clone figure must not be read as covering those assertions."
  },
  {
   "id": "R-3",
   "risk": "The identity evidence survives for only one launch per round: launch.json is overwritten by each battery pass, so a round's earlier passes have no persisted answered_nonce/listening_pid and can be attributed only by ledger line and timestamps.",
   "why_it_matters": "It is what produced D-1/D-4; a future claim that every pass of a multi-pass round was nonce-verified still cannot be checked from the record."
  },
  {
   "id": "R-4",
   "risk": "Four of nineteen surfaces (C5, C6, Q-scale, Q-not-required) are undecidable by this harness by construction, so 15/19 is the ceiling.",
   "why_it_matters": "Any round scoring below 15/19 has a real gap; the ceiling must be stated beside the figure."
  },
  {
   "id": "R-5",
   "risk": "The correction edited a live byte-count-bearing file (evidence/index.json) without reconciling the directory totals that depend on it, and no test guards those totals.",
   "why_it_matters": "The same class of error will recur on the next index edit; either the totals should be derived rather than hand-stated, or a test should assert them."
  }
 ],
 "unverified": [
  "A fresh clone at f1b9af3: I did not re-clone, because the correction touched no file under evidence/** and no .gitattributes rule; I verified the pin (`text: unset` for evidence/index.json and .spec/bevy/PRD.md), 0 CR bytes in the working tree's evidence/, and the corpus assertion green inside the gate. The previous acceptance's independent clone reproduction (green pinned clone / exit-101 unpinned control) is the evidence I rely on, not my own.",
  "A Linux or macOS clone, where core.autocrlf is false by default.",
  "What was physically on disk when the batch's own gate ran under F:/hof-rc-work/logs3: I confirmed logs3/exits.txt is all zero, its counts are 800/0/6/806 with 0 warnings and 0-byte fmt, and that the three files the report pins have those hashes in the delivered tree, but I cannot attest to the input state at that moment.",
  "Whether the 7th ledger line (pid 39664, launched_at 1791212664) corresponds to a further pass: it did not overwrite launch.json/meta.json/gate.json and nothing in the correction depends on it; neither I nor the batch chased it.",
  "Byte-level identity of what the round's successful shell writes put on disk.",
  "Whether a byte total other than the ones I checked is also stale; I checked the figures the correction could plausibly have moved, not every number in the tree."
 ],
 "fit_for_push": "NOT fit for a push as it stands, with the cost criterion recorded as unmet rather than fixed. Everything the previous acceptance asked to be corrected is corrected and independently confirmed against the artefacts, the gate is green on the exact HEAD, and the cost criterion is honestly recorded; but a pass here would push a tree whose `evidence/README.md` and whose own corrected deliverable state a byte total their committed contents refute (RD-1), and whose correction report pins a false sha256 for its own committed revision (RD-2). The repair is small and mechanical - either shrink or reconcile the index.json meaning and update the directory totals to 4,798,968 / 27,829 in evidence/README.md and CLONE-AND-LIVE-REPORT.md, and fix one hash on RECORD-CORRECTION-REPORT.md line 144 - after which the same gate is the check."
}
```

# ACCEPTANCE-RECORD - independent acceptance of the record-correction batch

Independent, **offline** acceptance of the corrective batch delivered as `.spec/bevy/RECORD-CORRECTION-REPORT.md`,
judged at **`bevy-core` / `f1b9af3`**. No engine, no game, no network, no model call, no round and no Developer call was
run. Nothing was written under `runs/**`; no `git checkout --`; no commit, stage or push; no `rm -rf`; nothing was
fixed. The machine-readable verdict is the JSON block above: it is `json.dumps(..., indent=1, ensure_ascii=False)`
output written by `F:/hof-acc11-work/write_acceptance.py` and then **parsed back out of this written file**, and the
parse is the last thing the generator does. All helper scripts live under `F:/hof-acc11-work/`, the logs under
`F:/hof-acc11-logs/` and the build under `D:/hof-acc11-target/` - all outside the repository.

## 0. The verdict in one paragraph

**The four defects the previous acceptance named are genuinely corrected, and I verified every corrected value from the
artefacts rather than from either document.** `runs/bevy-clonefix1/launch.json` really carries nonce
`ff44b5f7` / pid `57592` / image `eb328de6` and `verified: true`, and the ledger line for `fb53d29e` / `51360` really
has no `answered_nonce` and no `listening_pid`; `e3-observations.json` really is the 70-call iteration-3 pass with
`e3_jump_arc` 28 calls at `41..68` and `e3_process_liveness` at `69/70` with frames `712 -> 722`, and iteration 1 really
is the 64-call pass with liveness at `63/64` with frames `753 -> 763`; each pass's observation is now bound to its own
ledger launch by the whole pass window, not one timestamp; and `evidence/index.json` and `prd_surfaces.rs::RESIDUALS` no
longer say the step never ran, while the registry, the genuinely open `P3-goal-x` residual and the coverage value are
untouched. The gate on this exact HEAD is green: **exit 0, 800 passed / 0 failed / 6 ignored / 806 listed**, `fmt` exit 0
with 0 bytes, **0** warnings, no test removed. **I still return `fail`**, because the correction introduced two fresh
false statements into the committed record and left one old one in place. (RD-1) Its `evidence/index.json` meaning edit
grew index.json by 719 bytes, so `evidence/` as a directory is now **122 files / 4,798,968 bytes** and the four excluded
files total **27,829** - while `evidence/README.md`, the corrected `CLONE-AND-LIVE-REPORT.md` and `DECISIONS.md` still state
**4,798,249 / 27,110**, and the batch's own reasoning claimed the edit `cannot move a byte count`. (RD-2) The correction
report pins sha256 `889033a5...` for its own aee9c92 revision (blob `afde67da`), but that hash belongs to
`CLONE-AND-LIVE-REPORT.md`; blob `afde67da` hashes to `cebea19e...`. (RD-3) `COVERAGE-EVIDENCE-REPORT.md` still says 13
times that the liveness step never ran, disclosed and left in place. The cost criterion still fails at 2.55-2.60x with
`agent.step_limit: 150` binding, and that is recorded honestly.

## 1. Per-item results

| # | item | result | the evidence I gathered myself |
|---|---|---|---|
| 1 | D-1, the launch identity | **pass** | `runs/bevy-clonefix1/launch.json`: nonce = answered_nonce = `ff44b5f7...`, spawned = answering = listening = `57592`, image `...eb328de6...`, verified true; `meta.json` pid `57592`; all 7 ledger lines checked - line 2 is `fb53d29e` / `51360` and **no** ledger line has `answered_nonce` or `listening_pid`. Prose and machine block now agree with the artefact and with each other. |
| 2 | D-2 and D-4, per-pass attribution | **pass** | I derived all three passes from their own raw directories and `timestamp_ms`: iter-1 ledger `51360`@1791206961, ids 1..64, jump 22 at `41..62`, liveness `63/64` 753->763, window 1791206972198..1791206975944; iter-2 `45996`@1791209819, 1..70, jump 28, liveness `69/70` 712->722; iter-3 `57592`@1791212646, 1..70, jump 28, liveness `69/70` 712->722. Each window sits inside its own ledger interval. The machine block's `liveness` + `attribution_by_pass` match all of it exactly; `e3-observations.json` is iter-3 (70 ids, none missing) and `calls/` has 70 files with 0063/0064 transform, 0069/0070 wait_frames. |
| 3 | D-3, index and residuals | **pass** | The diff is one `meaning` string in index.json and 16+/11- lines in prd_surfaces.rs; no live `never executed` / `has ever been produced` claim remains in either; the 19-id registry, index.json's `value`/`files`/`command`/`repo_independent`, and `P3-goal-x` are untouched; `S1` is labelled OBSERVED with its caveat, not used to claim closure. |
| 4 | nothing over-corrected | **pass, with the knock-on below** | Exactly 5 paths differ from `71dcebd`; `.gitattributes`, `config/hoh.yaml`, `battery.rs`, the registry and every frozen doc are byte-identical; DECISIONS.md untouched. The only measured row the diff moves is the report's `e3_jump_arc` entry (22/`41..62` -> 28/`41..68`), which matches `e3-observations.json` and is disclosed as an extension - an artefact, not a document. But the index edit made RD-1's totals stale. |
| 5 | reproduce the gate | **pass** | Own dir `D:/hof-acc11-target` (9.1 G), one test process at a time, free disk checked first and nothing deleted. On f1b9af3: `cargo test --offline` **exit 0**, **800/0/6** over 60 result lines, **806** listed, 6 ignored, `cargo fmt --all --check` **exit 0** / 0 bytes, **0 warning lines**. 0 `#[test]` attributes changed. Mechanism tests (identity, ledger, tripwire, fold, 7 resume, battery) all present and green. |
| 6 | the tree as a whole | **pass, with a process defect** | 320 tracked files, harness + `.spec` + `evidence` only, `git ls-files runs` empty; 7-launch ledger with 7 distinct nonces/pids/images; one key-shaped token, the declared `tests/credential_scan.rs` fixture (positive control fires, `async-task-` does not); frozen docs byte-identical; DECISIONS.md append-only (untouched); nothing pushed (`origin/bevy-core` still `5f526d2`); tree **clean** at f1b9af3 - but it was dirty for the first ten minutes of this run (P-1). |
| 7 | what stands between tree and goal | **fail** | Decidability, reproducibility and frozen contract pass; cost FAILS at 2.600x / 2.549x / 2.604x with `step_limit: 150` binding and `write_failures: []`, recorded honestly; honest record does not pass cleanly because of RD-1 and RD-2 (and RD-3). |

## 2. Counterexamples I looked for

* **A corrected value that still disagrees with its artefact.** Not found for D-1, D-2, D-4. I re-derived each pass from
  its own raw directory rather than trusting either the prose or the previous acceptance, and every corrected number
  matches the artefact - including the sharpest check, that ids `0063`/`0064` are liveness waits in iteration 1's layout
  and `bevy_player_transform` calls in the 70-call layout.
* **An observation paired with another pass's launch.** Not found. The surviving `launch.json` is iteration 3's, and the
  machine block's `liveness` is iteration 3's own file; the three observations each carry their own ledger pid and window.
* **A residual kept open that is actually closed, or closed to hide something.** Not found. `P3-goal-x` is unchanged and
  genuinely open (a contract change this harness cannot make); `S1-deterministic-step` is listed with a disposition, not
  removed, and its new text keeps the boundary that the observation is outside the committed corpus.
* **A measured figure quietly adjusted to match prose.** Not found in the diff - the one moved measured row (jump 22->28)
  was moved to match the recording. **But the inverse happened:** a prose edit moved a measured figure and the figure's
  own documents were not updated (RD-1). That is the finding this acceptance turns on.
* **A gate run on a moving tree.** Found, in the previous batch's shape: this batch's own report moved at 00:34:45 and was
  committed at 00:40:23 while I accepted it (P-1). My gate was therefore re-run on the frozen `f1b9af3` tree.
* **A key in the tracked tree.** Not found: exactly one `sk-`-shaped 27-character literal, in the file that declares itself
  its fixture source.

## 3. What I could not establish

* A fresh clone at `f1b9af3`. The correction touched no `evidence/**` file and no `.gitattributes` rule, and the corpus
  assertion is green in the working tree's gate, so I verified the pin (`text: unset`) and the 0-CR census instead of
  re-cloning; the previous acceptance's own green-pinned/red-control clone experiment is the evidence, not mine.
* A Linux or macOS clone, where `core.autocrlf` is false by default.
* What was physically on disk when the batch's own gate ran under `F:/hof-rc-work/logs3`. I confirmed that log's exit codes
  and counts and that the three hashes it pins hold in the delivered tree, but not the input state at that instant.
* The 7th ledger line (`pid 39664`): unexplained, and nothing in the correction depends on it.
* Byte-level identity of what the round's successful shell writes put on disk.

## 4. Fit for a push

**Not fit as it stands, with the cost criterion recorded as unmet rather than fixed.** The mechanisms and the four named
corrections are sound and the gate is green on the exact HEAD; what blocks a `pass` is that the committed record now
contains two false statements this batch created (RD-1's byte totals, RD-2's self-referential hash) and one it was told
not to touch (RD-3). The cost criterion is expected to still fail and is honestly recorded, so it is not the blocker. The
repair is mechanical: reconcile `evidence/index.json`'s meaning with the directory totals - update `evidence/README.md`
and `CLONE-AND-LIVE-REPORT.md` to **122 files / 4,798,968 bytes** and **27,829 bytes** excluded, or restore a total the
documented figure matches - and correct one sha256 on `RECORD-CORRECTION-REPORT.md` line 144, after which the identical
`cargo test --offline` gate is the check.
