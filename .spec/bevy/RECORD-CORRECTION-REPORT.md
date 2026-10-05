```json
{
 "schema": "hof-rs / bevy record correction of the clone-pin and first-live-round batch (defects D-1, D-2, D-3, D-4 of .spec/bevy/ACCEPTANCE-CLONE-LIVE.md)",
 "produced_at": "2026-10-06",
 "branch": "bevy-core",
 "offline": true,
 "head_at_start": "c00716d (`docs(acceptance): record the acceptance that passes decidability and reproducibility and fails only on three sentences`). The batch's deliverable .spec/bevy/CLONE-AND-LIVE-REPORT.md is committed at that HEAD (blob 64a69937, sha256 b2053ad15ca2618a3b3b1829e66ef908fc23c6cf014922b2034f1d282f0cff9f); the working tree was clean when this correction started.",
 "what_this_batch_did": "corrected the record to the artefacts that already existed, and nothing else: no re-run of the round, no new measurement, no engine, no network, no model call, no change to .gitattributes, to the liveness step, to the coverage registry, to the battery, or to any measured number outside D-1/D-2/D-4. The three corrected files and an earlier revision of this report were committed by the dispatcher as aee9c92 while this batch was still working; the delivered revision of this report is the only uncommitted path, and this batch itself ran no `git add`, `git commit` and no `git push`.",
 "gate": {
  "command": "cargo test --offline",
  "literal_exit_code": 0,
  "passed": 800,
  "failed": 0,
  "ignored": 6,
  "listed": 806,
  "test_result_lines": 60,
  "listed_command": "cargo test --offline -- --list",
  "listed_exit_code": 0,
  "listed_names": 806,
  "ignored_list_command": "cargo test --offline -- --list --ignored",
  "ignored_list_exit_code": 0,
  "ignored_names": 6,
  "fmt_command": "cargo fmt --all --check",
  "fmt_exit_code": 0,
  "fmt_stdout_bytes": 0,
  "fmt_stderr_bytes": 0,
  "warning_lines_stdout": 0,
  "warning_lines_stderr": 0,
  "tests_added_or_removed_test_attributes": 0,
  "build_dir": "D:/hof-rc-target (this correction's own; one cargo process at a time, no second test process)",
  "free_disk_before_building": "F: 56 G free, D: 198 G free; nothing was deleted and `rm -rf` was not used",
  "logs": [
   "F:/hof-rc-work/logs3/fmt.out",
   "F:/hof-rc-work/logs3/fmt.err",
   "F:/hof-rc-work/logs3/gate.out",
   "F:/hof-rc-work/logs3/gate.err",
   "F:/hof-rc-work/logs3/exits.txt",
   "F:/hof-rc-work/logs3/targeted.out",
   "F:/hof-rc-work/logs3/libprd.out",
   "F:/hof-rc-work/logs3/list.out",
   "F:/hof-rc-work/logs3/ignored.out"
  ],
  "gate_input_sha256": {
   "evidence/index.json": "eb88286c638363a7ff64e7aa1bf901159cc68bf0663707c9526f258a9bb03d2f",
   "src/adapter/bevy/prd_surfaces.rs": "6ea1090bf8a11b0cbcd8d0970ba42180ad0e50da08c5211546397a4a6b4bb6f1",
   ".spec/bevy/CLONE-AND-LIVE-REPORT.md": "423036d0b10f44fd00126f3bb4066ef1c6d303d5ceee415d733d619afebc4006",
   "note": "src/** and tests/** are otherwise exactly as committed at c00716d (git status shows no other tracked change), so these three hashes, with HEAD, fix the whole gate input set. This file's own hash is not pinned and is not a gate input. The .spec/bevy/CLONE-AND-LIVE-REPORT.md value above is that path's CURRENT hash, and it has moved twice: the logs3 run and the f1b9af3 tree used 889033a5fd8914357886b28f110609dcffad571194e844d03e5db7d3fb44471e, the byte-totals correction authorised by defects RD-1/RD-3 of .spec/bevy/ACCEPTANCE-RECORD.md made it 7c09a7ad95597453441cef6ba2c33cf73f6b00dc71a0d4b6f2fcbde68dbc66bb, and the R-A2 cross-reference correction (DECISIONS D309) made it 423036d0b10f44fd00126f3bb4066ef1c6d303d5ceee415d733d619afebc4006 by labelling the two E-2 clauses that this report's C-3/D-3 record had made stale. Each earlier value is kept above and in the notes because it was true of the revision it names. No test, build script or gate reads that file, so neither the gate numbers nor the gate input set depend on any of the three."
  },
  "gate_tree": "the numbers above are from the run logged under F:/hof-rc-work/logs3. The gate was run three times and all three runs report the same numbers (exit 0, 800/0/6/806, 0 warnings, fmt 0 bytes); the first two were superseded because something changed afterwards - first the report file itself, then only the log paths recorded here. Neither is a gate input: grep over src/, tests/ and scripts/ finds no reference to the corrected report, and no test reads it. The three hashes under gate_input_sha256 are the gate inputs that this correction did change, and they are byte-identical between the logs3 run and the delivered tree, so the logs3 numbers are the delivered tree's numbers."
 },
 "tests_that_read_the_changed_files": [
  {
   "changed_file": "evidence/index.json",
   "tests": [
    "tests/evidence_reproduction.rs"
   ],
   "command": "cargo test --offline --test evidence_reproduction --test prd_coverage",
   "literal_exit_code": 0,
   "passed": 12,
   "failed": 0,
   "detail": "evidence_reproduction 7 passed / prd_coverage 5 passed; the test that reads the index is `the_evidence_index_names_committed_files_and_commands`, which re-derives the corpus (118 files / 4,771,139 bytes) and checks that every headline file exists. index.json itself is excluded from that corpus count, so the corrected `meaning` string cannot move the *corpus* byte count; the *directory* total, which does include index.json, is a different figure, stated by hand in `evidence/README.md` and asserted separately by the same test since the R-A1 hardening of DECISIONS D309 (the walk now accumulates the corpus, the excluded-files and the directory totals and fails if any byte under `evidence/` moves without all three agreeing)."
  },
  {
   "changed_file": "src/adapter/bevy/prd_surfaces.rs",
   "tests": [
    "tests/prd_coverage.rs",
    "src/adapter/bevy/prd_surfaces.rs unit tests (via --lib)"
   ],
   "command": "cargo test --offline --lib prd_surfaces",
   "literal_exit_code": 0,
   "passed": 5,
   "failed": 0,
   "detail": "the registry constant PRD_SURFACES and its deciders are unchanged; only the doc comment and the RESIDUALS constant changed, and no test reads RESIDUALS (grep over src/ and tests/ finds only its definition), which is why it was corrected without touching the registry."
  },
  {
   "changed_file": ".spec/bevy/CLONE-AND-LIVE-REPORT.md",
   "tests": [],
   "detail": "no test, build script or gate reads this file; grep over src/, tests/ and scripts/ finds no reference to it. The full `cargo test --offline` gate above was run with this file already corrected."
  }
 ],
 "defects": [
  {
   "id": "D-1",
   "severity": "high",
   "status": "CORRECTED",
   "artefact_says": "runs/bevy-clonefix1/launch.json: identity.nonce = identity.answered_nonce = ff44b5f7-ed96-43b2-8942-1dec7f6b54b8, spawned_pid = answering_pid = listening_pid = 57592, launch_image = runs\\bevy-clonefix1\\launch-image\\eb328de6-7379-4cb4-a965-92563b0b2d41\\hof_game.exe, verified true. The value the prose named instead (nonce fb53d29e-8fcf-469c-82b8-cd760543212d, pid 51360, image ...ee494002...) is the SECOND line of runs/bevy-clonefix1/launch-ledger.jsonl and that line carries neither answered_nonce nor listening_pid. Read back by this batch from both files.",
   "record_said": "CLONE-AND-LIVE-REPORT.md prose, section 2, bullet `Identity, applied before any battery verdict` (was line 1509): `... nonce fb53d29e-8fcf-469c-82b8-cd760543212d, answered_nonce the same value, spawned_pid = answering_pid = listening_pid = 51360, launch_image runs\\bevy-clonefix1\\launch-image\\ee494002-e119-4b38-be2b-89e113fe65e7\\hof_game.exe, and a 7-line launch ledger.`",
   "corrected_text": "`runs/bevy-clonefix1/launch.json` carries `verified: true`, nonce `ff44b5f7-ed96-43b2-8942-1dec7f6b54b8`, `answered_nonce` the same value, `spawned_pid = answering_pid = listening_pid = 57592`, `launch_image` `runs\\bevy-clonefix1\\launch-image\\eb328de6-7379-4cb4-a965-92563b0b2d41\\hof_game.exe`, and a 7-line launch ledger. That surviving launch is **iteration 3, the final battery pass** - the same `pid: 57592` that `runs/bevy-clonefix1/meta.json` names for the pass that wrote the readings. `launch.json` is overwritten by every pass, so **no earlier pass keeps an `answered_nonce` or a `listening_pid`**: the ledger's line for iteration 1's pass (`fb53d29e-8fcf-469c-82b8-cd760543212d`, pid 51360) carries neither field, and that pass is attributable only by its own ledger line and timestamps.",
   "also_corrected": "the machine block's identity_gate gained `pass` (iteration 3, with meta.json's pid 57592) and `earlier_passes` (launch.json is overwritten per pass; iterations 1 and 2 keep no answered_nonce/listening_pid)"
  },
  {
   "id": "D-2",
   "severity": "low",
   "status": "CORRECTED",
   "artefact_says": "runs/bevy-clonefix1/readings/e3-observations.json is iteration 3's pass and holds 70 distinct sequence ids, 1..70 fully covered: movement [9..13], coins and win and win_position [1..7,14..31], jump [41..68] (28 calls), grounded [1..7], grounded_payload [8], movement_left [32..37], movement_release [38,39,40], liveness [69,70] with frame_after 712 and 722. runs/bevy-clonefix1/calls holds 70 files, 0063/0064 bevy_player_transform and 0069/0070 bevy_wait_frames - the same mtime, 2026-10-05 23:04:20, as runs/clonefix1/iter-3's raw directory. Iteration 1's own pass is the 64-call layout: its raw calls stop at seq 64 and its liveness is at [63,64].",
   "record_said": "the same section's bullet `The ten battery steps and their raw call ids` (was line 1526): `from runs/bevy-clonefix1/readings/e3-observations.json, 64 call files in total`, and `e3_process_liveness [63,64]`, with `e3_jump_arc [41..62]`.",
   "corrected_text": "`from runs/bevy-clonefix1/readings/e3-observations.json, 70 call files in total`: ... `e3_jump_arc [41..68]` ... `e3_process_liveness [69,70]` ... plus `That file is the iteration-3 pass, the same pass that wrote runs/bevy-clonefix1/calls (70 files, 0063/0064 bevy_player_transform and 0069/0070 bevy_wait_frames). Iteration 1's pass is the 64-call layout instead - its e3_jump_arc ends at 62 and its e3_process_liveness is at [63,64] - and its call ids belong to that pass alone, not to the ids above.`",
   "scope_note": "the acceptance's D-2 named the call-file count and the liveness indices. The jump row had to move too (22 calls / [41..62] -> 28 / [41..68]) because the same sentence cites e3-observations.json as the source of the WHOLE table, and that file says jump is 28 calls at [41..68]; leaving it would have kept the sentence contradicting the file it names. It is the acceptance's own D-2 reproduction that records `jump 28 (seqs 41..68)`.",
   "also_corrected": "the machine block's live_round.battery_steps was verbatim iteration 1's pass (jump 22 calls at [41..62] with iter-1's exact tool list; liveness ids [63,64]); it was regenerated from e3-observations.json, and the machine block's E-2 `evidence` string now says the round produced the raw file in each of the three passes"
  },
  {
   "id": "D-3",
   "severity": "medium",
   "status": "CORRECTED",
   "artefact_says": "runs/clonefix1/iter-{1,2,3}/candidate/.hoh/deterministic/raw/e3_process_liveness.json exist and each is observed true with failure null (753 -> 763, 712 -> 722, 712 -> 722), and runs/clonefix1/iter-{1,2,3}/result.json carries prd_coverage.surfaces 15 verified / 0 gap / 4 unobservable of 19. So the ten-step battery HAS run against a real game and a raw observation file HAS been produced.",
   "record_said": "evidence/index.json's coverage.with_the_new_step meaning: `... e3_process_liveness is implemented and unit/fake-driver tested but has never executed against a real game, so no committed round has produced this figure (defect E-2).` And src/adapter/bevy/prd_surfaces.rs, RESIDUALS: `... pending its first real observation, because no round has run the ten-step battery and no raw/e3_process_liveness.json has ever been produced`, with the doc comment above it reading `it has **never run against a real game**`.",
   "corrected_text": "a CODE PROJECTION of the ten-step battery, not an independent observation: it is what a round that runs every registered step scores when every step reports ok=true. The four unobservable items are C5, C6, Q-scale, Q-not-required and are named gaps, not missing claims. `e3_process_liveness` is implemented and unit/fake-driver tested AND has executed against a real game: the live round `clonefix1` (2026-10-05, recorded under the gitignored `runs/`) ran the ten-step battery in all three iterations, and `result.json.prd_coverage.surfaces` read 15 verified / 0 gap / 4 unobservable of 19 in every one of them, with `runs/clonefix1/iter-{1,2,3}/candidate/.hoh/deterministic/raw/e3_process_liveness.json` persisted each time (observed true; frames 753 -> 763, 712 -> 722, 712 -> 722) - which is what verifies `Q-startup` and `B2.1`. That observation lives outside `evidence/` and is not what this entry's own command replays, so the figure above stays the repository-reproducible projection; the earlier wording that said the step had never executed against a real game was falsified by that round (defect D-3 of .spec/bevy/ACCEPTANCE-CLONE-LIVE.md).",
   "corrected_text_residual": "implemented by the e3_process_liveness battery step, which decides Q-startup and B2.1. OBSERVED, no longer pending: the live round clonefix1 (2026-10-05, its recordings under the gitignored runs/) ran the ten-step battery in all three iterations and persisted raw/e3_process_liveness.json in every one of them - frames 753 -> 763 in iteration 1 and 712 -> 722 in iterations 2 and 3, observed true with failure null throughout. The earlier wording here, which called this pending because no round had run the ten-step battery and no raw/e3_process_liveness.json had ever been produced, is falsified by that round; the observation itself is not part of the committed evidence/ corpus",
   "residual_still_open": [
    "P3-goal-x is a residual that is STILL GENUINELY OPEN and it was left exactly as written, because its reason has not changed: the goal entity's own position is not one of the seven frozen surfaces, and adding an eighth would be a contract change this harness has no authority to make. It stays an Unobservable item outside the PRD denominator.",
    "S1-deterministic-step is no longer pending, but it stays listed with its disposition because it is not a PRD surface: it is one of the two ids the round-4 Tester authored that are not surfaces, and the residual list exists to carry such ids with their disposition. Its corrected text says OBSERVED and states that the observation lives under the gitignored runs/, so the committed evidence/ corpus does not itself carry it."
   ],
   "also_corrected": "the report's own E-2 entries in CLONE-AND-LIVE-REPORT.md (the machine block's defects[E-2].change/evidence and section 4's prose) said the wording `now reads *implemented, pending its first real observation*` in all four places; after this correction that is no longer true of the two places outside the batch report, so both were updated to past tense with a pointer to what changed",
   "deliberately_not_corrected": ".spec/bevy/COVERAGE-EVIDENCE-REPORT.md is a separate committed batch report and this task forbade modifying batch reports; its machine block carried the pre-round wording while its own disposition section already recorded the observation. **SUPERSEDED:** the RD-3 correction of DECISIONS D308 afterwards rewrote those clauses, so `.spec/bevy/COVERAGE-EVIDENCE-REPORT.md` no longer carries the never-ran wording as a present state; this field is kept as the scope decision that was taken at the time. See contradictions_found."
  },
  {
   "id": "D-4",
   "severity": "low",
   "status": "CORRECTED",
   "artefact_says": "the surviving runs/bevy-clonefix1/launch.json (and meta.json, and gate.json) belongs to iteration 3: pid 57592, ledger launched_at_seconds 1791212646, and the whole iteration-3 raw pass sits at 1791212656053..1791212660017, inside the ledger interval (57592 @1791212646, 39664 @1791212664). That pass's own liveness is 712 -> 722 at seq 69/70. Iteration 1's liveness (753 -> 763, seq 63/64) belongs to the launch of pid 51360 (@1791206961, pass window 1791206972198..1791206975944), and iteration 2's (712 -> 722, seq 69/70) to pid 45996 (@1791209819, pass window 1791209828774..1791209832740).",
   "record_said": "the machine block's live_round.liveness pointed at runs/clonefix1/iter-1/... with frames 753/763 and calls seq 63/64, i.e. it paired the iteration-3 verified launch in identity_gate with iteration 1's observation, and the machine block carried no per-pass attribution at all.",
   "corrected_text": "live_round.liveness is now the verified launch's own pass: path runs/clonefix1/iter-3/candidate/.hoh/deterministic/raw/e3_process_liveness.json, frames {first_frame 712, requested 8, second_frame 722}, advance 10, calls seq 69 (frame 712) and 70 (frame 722), with a `pass` string naming iteration 3 and ledger pid 57592; and a new live_round.liveness.attribution_by_pass array carries all three passes, each with its own raw path, frames, advance, two calls, measured pass window and ledger pid/launched_at. Section 2's prose bullet was rewritten the same way, and section 0 now names both advances (753 -> 763 in iteration 1, 712 -> 722 in iterations 2 and 3) instead of headlining one pass's number unlabelled."
  }
 ],
 "changed_files": [
  {
   "path": ".spec/bevy/CLONE-AND-LIVE-REPORT.md",
   "what": "D-1 prose, D-2 prose and machine block, D-4 machine block and prose, plus the sentences that described the E-2 wording",
   "committed_as": "aee9c92 (`docs(record): correct the three statements that disagreed with their own artefacts`); the aee9c92/f1b9af3 revision of this path hashed to 889033a5fd8914357886b28f110609dcffad571194e844d03e5db7d3fb44471e and the delivery this report covers was byte-identical to it; the byte-totals correction authorised by defects RD-1/RD-3 of .spec/bevy/ACCEPTANCE-RECORD.md has since changed two measured totals in this path, so the delivered working file now hashes to 7c09a7ad95597453441cef6ba2c33cf73f6b00dc71a0d4b6f2fcbde68dbc66bb"
  },
  {
   "path": "evidence/index.json",
   "what": "D-3: coverage.with_the_new_step.meaning",
   "committed_as": "aee9c92; HEAD's blob is byte-identical to the delivered working file, sha256 eb88286c638363a7ff64e7aa1bf901159cc68bf0663707c9526f258a9bb03d2f"
  },
  {
   "path": "src/adapter/bevy/prd_surfaces.rs",
   "what": "D-3: the S1-deterministic-step doc comment and the RESIDUALS entry (registry constant PRD_SURFACES untouched)",
   "committed_as": "aee9c92; HEAD's blob is byte-identical to the delivered working file, sha256 6ea1090bf8a11b0cbcd8d0970ba42180ad0e50da08c5211546397a4a6b4bb6f1"
  },
  {
   "path": ".spec/bevy/RECORD-CORRECTION-REPORT.md",
   "what": "this report",
   "committed_as": "aee9c92 committed an earlier revision (blob afde67da, sha256 cebea19e0f955369a3a7fc8012f785c3f2d8939cde43208e5f7052af98f1d4e3) while this batch was still correcting the log paths and pinning the gate-input hashes; the delivered revision is the only uncommitted path when this report is written, and the dispatcher commits it"
  }
 ],
 "dispatcher_commits": {
  "aee9c92": "`docs(record): correct the three statements that disagreed with their own artefacts` - the dispatcher committed all four paths (201 lines changed in CLONE-AND-LIVE-REPORT.md, 2 in evidence/index.json, 27 in prd_surfaces.rs, plus this report) while this batch was still working, so this batch's own deliverable shows the same mid-flight commit the previous one did. This batch ran no `git add`, `git commit` and no `git push`. The three corrected files are byte-identical between HEAD and the delivered tree, so nothing about the gate above depends on the commit timing; only the log-path/hash-pinning revision of this report is newer than aee9c92."
 },
 "not_touched": [
  ".gitattributes and the `evidence/** -text` pin",
  "the liveness step and its decider (src/adapter/bevy/battery.rs)",
  "the coverage registry PRD_SURFACES and its 19 ids",
  "the battery and its ten steps",
  "every measured number in any report other than the D-1/D-2/D-4 values above",
  "REQUIREMENTS.md, PRD.md, DESIGN-OVERVIEW.md, DESIGN-DETAIL.md, the spike reports, COVERAGE-EVIDENCE-REPORT.md and every other batch report",
  "DECISIONS.md (nothing needed appending: no option was chosen between alternatives here - this batch copied values out of artefacts that already existed)",
  "no file was deleted; `rm -rf` was not used; no API key was created, copied or printed; no network, engine, game or model call was made; no helper script was written inside the repository"
 ],
 "contradictions_found": [
  {
   "id": "C-1",
   "what": "No artefact contradicts both the prose and the acceptance. Every value the acceptance's D-1/D-2/D-4 cite was re-read from the artefact by this batch and matches the artefact, so the acceptance is right about all three and no judgement call between competing records was needed.",
   "how": "launch.json, launch-ledger.jsonl, meta.json, the three raw e3_process_liveness.json files, e3-observations.json, runs/bevy-clonefix1/calls and the file mtimes were all read directly."
  },
  {
   "id": "C-2",
   "what": "Found beyond the acceptance: the machine block's live_round.battery_steps was ALSO iteration 1's pass, verbatim - its e3_jump_arc entry (22 calls, ids 41..62, tool list) reproduces iteration 1's own e3_jump_arc raw call list call-for-call, and its liveness ids are [63,64]. The acceptance's D-2 named only the call-file count and the liveness indices, so correcting the cited sentence to e3-observations.json without also moving the jump row would have left the sentence contradicting the file it names.",
   "how": "compared the block's jump entry with runs/clonefix1/iter-{1,2,3}/.../raw/e3_jump_arc.json: iter-1 is 22 calls at 41..62, iter-2 and iter-3 are 28 at 41..68, and the block matched iter-1 exactly."
  },
  {
   "id": "C-3",
   "what": "One committed report still contradicts itself and it is one this batch was forbidden to edit: .spec/bevy/COVERAGE-EVIDENCE-REPORT.md's machine block and several prose sections still say e3_process_liveness is `PENDING ITS FIRST REAL OBSERVATION` and that `no raw/e3_process_liveness.json has ever been produced (defect E-2)`, while the same file's own disposition section (around line 565) already records that the follow-up live round produced the step's first real observation and that the surfaces read 15/19. [SUPERSEDED 2026-10-06 by the RD-3 correction, DECISIONS D308 - the clauses described as still saying this were afterwards rewritten, so they no longer do; kept as the state when C-3 was written. See `disposition`.]",
   "how": "grep -n for `pending its first real observation` / `has ever been produced` / `never executed against a real game` over .spec/bevy/COVERAGE-EVIDENCE-REPORT.md.",
   "disposition": "left untouched, because the task forbids modifying batch reports and the acceptance's D-3 named only evidence/index.json and prd_surfaces.rs::RESIDUALS. Flagged for explicit authorisation - see below. **SUPERSEDED:** the authorisation was granted after this batch; the RD-3 correction (DECISIONS D308) rewrote those clauses in `.spec/bevy/COVERAGE-EVIDENCE-REPORT.md`, so the untouched state described above is history rather than the state of the tree."
  },
  {
   "id": "C-4",
   "what": "The report's machine block still carries `working_tree_at_end` and changed_files.uncommitted_at_write_time describing the report as uncommitted, which was true when the batch wrote it and stopped being true when the dispatcher committed it as c00716d (blob 64a69937, sha256 b2053ad1...). Those fields are the batch's own history and were left as written.",
   "how": "git log/rev-parse/rev-parse HEAD:path compared with the file's sha256."
  }
 ],
 "single_most_important_thing_next_batch": "The record now agrees with its artefacts on every point the acceptance named, so the next step is to authorise ONE more correction or to declare C-3 out of scope: `.spec/bevy/COVERAGE-EVIDENCE-REPORT.md` is the only committed statement left that contradicts the round's own artefacts (its machine block still calls e3_process_liveness `pending its first real observation` and says no `raw/e3_process_liveness.json` has ever been produced, while the same file's disposition around line 565 already records the observation). This batch was forbidden to edit batch reports and the acceptance's D-3 did not name that file, so it cannot be closed by a correction of this shape - give it an explicit owner or an explicit exclusion before the next acceptance reads it, or the identical defect will be found again in a file nobody was allowed to fix. (After that, the only open goal criterion is still cost: 2.55-2.60x the 1,500,000-token per-call target, each call ended by agent.step_limit: 150 with the tripwire never firing.) [**SUPERSEDED 2026-10-06 by the RD-3 correction, DECISIONS D308:** `.spec/bevy/COVERAGE-EVIDENCE-REPORT.md`'s machine block and prose were rewritten to record the observation, so it is no longer a committed statement that contradicts its own artefacts. This paragraph is kept because it is what this batch's record said at the time and because it is why the authorisation was asked for.]",
 "prose_follows": true
}
```

# RECORD-CORRECTION-REPORT - correcting the clone-pin + first-live-round record to its own artefacts

Independent of the round: **no engine, no game, no network, no model call, no round and no Developer call
was run, and no measurement was constructed**. This batch exists only to make the committed record agree
with artefacts that already exist. The machine-readable block above is `json.dumps(..., indent=1,
ensure_ascii=False)` output written by `F:/hof-rc-work/fix_report.py` / `F:/hof-rc-work/gen_report.py` and
then **parsed back out of the file that was written**; the parse is the last thing the generator does and
it fails if the block does not round-trip. Every helper script lives under `F:/hof-rc-work/`, outside the
repository. Nothing was deleted, `rm -rf` was not used, and no API key was created, copied or printed.

## 0. The verdict in one paragraph

**The acceptance was right on all three record defects, and the record now says what its artefacts say.**
I read `runs/bevy-clonefix1/launch.json`, `meta.json`, `gate.json`, the seven-line ledger, the three raw
`e3_process_liveness.json` files, `e3-observations.json`, the seventy files in `runs/bevy-clonefix1/calls`
and the file mtimes myself before changing a word, and I did not simply adopt either the prose's numbers or
the acceptance's: every corrected value below is a value I read out of an artefact. The gate is green on the
corrected tree - `cargo test --offline` **exit 0**, **800 passed / 0 failed / 6 ignored / 806 listed** over
60 `test result:` lines, `cargo fmt --all --check` **exit 0** with 0 bytes, **0** compiler warnings, 0 test
attributes added or removed - and the tests that actually read the two changed non-report files were run
separately and pass. I did not touch the `.gitattributes` pin, the liveness step, the coverage registry,
the battery, or any measured number other than the D-1/D-2/D-4 values.

## 1. D-1 - the launch identity the prose named does not exist

`runs/bevy-clonefix1/launch.json` says, verbatim: `nonce` and `answered_nonce` both
`ff44b5f7-ed96-43b2-8942-1dec7f6b54b8`, `spawned_pid = answering_pid = listening_pid = 57592`,
`listening_pid 57592`, `launch_image runs\bevy-clonefix1\launch-image\eb328de6-7379-4cb4-a965-92563b0b2d41`
`\hof_game.exe`, `verified: true`. `runs/bevy-clonefix1/meta.json` independently names `"pid": 57592` for
the pass that wrote the readings.

The prose named `fb53d29e-8fcf-469c-82b8-cd760543212d` / `51360` / `...ee494002...`. I checked where those
come from: they are the **second** line of `runs/bevy-clonefix1/launch-ledger.jsonl`, and that line has
only `endpoint`, `launch_image`, `launched_at_seconds`, `nonce`, `note`, `pid`, `port` - it carries **no**
`answered_nonce` and **no** `listening_pid`. So the sentence asserted a verified-identity record that does
not exist anywhere, while the same file's own machine block already carried the right values. The prose now
names the artefact's launch, states that it is iteration 3's pass, and states plainly that no earlier pass
keeps an `answered_nonce` or a `listening_pid`.

## 2. D-2 - the call corpus the prose cited is a different pass

`runs/bevy-clonefix1/readings/e3-observations.json` holds sequence ids 1..70 with **none missing**:
movement `[9..13]`, coins / win / win_position `[1..7,14..31]`, jump `[41..68]`, grounded `[1..7]`,
grounded_payload `[8]`, movement_left `[32..37]`, movement_release `[38,39,40]`, and **liveness `[69,70]`**
with `frame_after` 712 then 722. `runs/bevy-clonefix1/calls` holds 70 files, and `0063`/`0064` are
`bevy_player_transform` while `0069`/`0070` are `bevy_wait_frames` - which is exactly what the two liveness
waits are. The prose said `64 call files in total` with liveness at `[63,64]`.

I did not have to take the acceptance's word for which pass is which. Iteration 1's raw directory covers
only ids 1..64 (`e3_jump_arc` 22 calls at `41..62`, `e3_process_liveness` at `63/64`), while iterations 2
and 3 both cover 1..70. And the mtimes settle it: `runs/bevy-clonefix1/launch.json`, `meta.json`,
`gate.json`, `readings/e3-observations.json` and the raw file
`runs/clonefix1/iter-3/candidate/.hoh/deterministic/raw/e3_process_liveness.json` are all stamped
**2026-10-05 23:04:20**, while iteration 1's raw file is 21:29:36 and iteration 2's is 22:17:13. The
observations file, the calls directory and the surviving launch are one and the same pass - **iteration
3** - and the 64-call layout the prose printed is iteration 1's. The `0063`/`0064` distinction is the
sharpest single check: in iteration 1 those ids were the liveness waits, and in the 70-call pass they are
`bevy_player_transform` calls belonging to `e3_jump_arc`, with the waits moved to `0069`/`0070`.

**One extension beyond the acceptance's wording, disclosed.** The acceptance's D-2 names the call-file
count and the liveness indices; I also moved the `e3_jump_arc` row from `[41..62]` (22 calls) to `[41..68]`
(28 calls), and regenerated the machine block's `live_round.battery_steps` from `e3-observations.json`. The
reason is that the sentence cites `e3-observations.json` as the source of **the whole table**, and that file
says jump is 28 calls at `41..68`; correcting the count and the liveness indices while leaving the jump row
would have left the corrected sentence still contradicting the file it names. The acceptance's own D-2
reproduction records `jump 28 (seqs 41..68)`, so this is the defect record's own figure, not a new claim.
Nine of the ten rows were already identical to the artefact; only jump and liveness moved.

## 3. D-3 - the E-2 repair still said the step had never run

Both sites the acceptance named were corrected, and neither is a measured number:

* `evidence/index.json`'s `coverage.with_the_new_step.meaning` now says the projection has been observed,
  cites the round's `result.json.prd_coverage.surfaces` (15 verified / 0 gap / 4 unobservable of 19 in all
  three iterations) and the three persisted raw files, and keeps the honest boundary that the round's
  recordings live under the gitignored `runs/` so this entry's own command still replays the projection.
* `src/adapter/bevy/prd_surfaces.rs::RESIDUALS`'s `S1-deterministic-step` entry, and the doc comment above
  it, now say **OBSERVED** and quote the three passes. The registry constant `PRD_SURFACES` and its 19 ids
  are untouched. No test reads `RESIDUALS` (`grep` over `src/` and `tests/` finds only its definition), so
  this constant was corrected without going near the registry.

**The residual that is still genuinely open was left open, with its reason.** `P3-goal-x` is unchanged: the
goal entity's own world position is not one of the seven frozen surfaces and adding an eighth would be a
contract change this harness has no authority to make, so it stays an Unobservable item outside the PRD
denominator. `S1-deterministic-step` is no longer pending but stays listed: it is one of the two ids the
round-4 Tester authored that are **not** PRD surfaces, and the list exists to carry such ids with their
disposition - now `OBSERVED`, with the note that the observation itself is not in the committed corpus.

Correcting this also forced two sentences in `CLONE-AND-LIVE-REPORT.md` (the machine block's `defects[E-2]`
entry and section 4's prose) that said the wording "now reads *implemented, pending its first real
observation* in all four places". That is no longer true of the two places outside the batch report, so both
were put in the past tense with a pointer to what changed.

## 4. D-4 - the machine block paired a launch with another pass's observation

The surviving `launch.json` is iteration 3's (`meta.json` pid 57592, ledger `launched_at_seconds`
1791212646), but the machine block's `live_round.liveness` pointed at iteration 1's file with frames
753 -> 763 and calls 63/64. It now points at iteration 3's own file: frames `712 -> 722`, advance 10, calls
seq 69 (712) and 70 (722), with a `pass` string naming iteration 3 and ledger pid 57592.

The other passes are now attributed to their own launches rather than dropped, and I established that
attribution more strongly than the acceptance's single-timestamp argument did. I bracketed **each
iteration's whole battery pass** - every embedded `timestamp_ms` in that iteration's raw directory - between
its own launch and the next ledger line:

| pass | ledger pid | launched_at (s) | the pass's own call window (ms) | frames |
|---|---|---|---|---|
| iteration 1 | 51360 | 1791206961 | 1791206972198 .. 1791206975944 | 753 -> 763, seq 63/64 |
| iteration 2 | 45996 | 1791209819 | 1791209828774 .. 1791209832740 | 712 -> 722, seq 69/70 |
| iteration 3 | 57592 | 1791212646 | 1791212656053 .. 1791212660017 | 712 -> 722, seq 69/70 |

Each window sits entirely inside its own ledger interval (`51360 -> 46120`, `45996 -> 35364`,
`57592 -> 39664`), so the attribution does not rest on one timestamp. The machine block carries all three
under `live_round.liveness.attribution_by_pass` with each raw path, its frames, its two calls, its measured
pass window and its ledger pid and `launched_at`; section 2's prose bullet says the same thing; and section
0 now names both observed advances instead of headlining one pass's number with no label.

## 5. The gate, on the corrected tree

Free space was checked before building (F: 56 G, D: 198 G; nothing was deleted and `rm -rf` was not used).
Build directory `D:/hof-rc-target` is this correction's own, one cargo process ran at a time, and no second
test process existed at any point.

These numbers come from the run logged under `F:/hof-rc-work/logs3`, and the two earlier runs are
disclosed rather than hidden. I first ran the gate while I was still editing `CLONE-AND-LIVE-REPORT.md`,
which is the same moving-artefact mistake the acceptance recorded as D-7; I ran it again after finishing
every edit, but then changed only the log paths recorded in this report. All three runs report identical
numbers, and **neither the report nor its log paths is a gate input**: `grep` over `src/`, `tests/` and
`scripts/` finds no reference to the corrected report and no test reads it. What the gate does read, and what
this correction did change, is `evidence/index.json` and `src/adapter/bevy/prd_surfaces.rs` - plus
`CLONE-AND-LIVE-REPORT.md`, which no test reads either. Those three hashes are pinned in
`gate.gate_input_sha256` and are byte-identical between the `logs3` run and the delivered tree, and
`src/**` and `tests/**` carry no other change at all (the only `src/` edit is that one file, and it adds or
removes no `#[test]`); that is what makes the `logs3` numbers the delivered tree's numbers. I stopped editing
when this report was regenerated with those paths.

| check | command | literal exit code | result |
|---|---|---|---|
| full gate | `cargo test --offline` | **0** | **800 passed / 0 failed / 6 ignored** over 60 `test result:` lines |
| listing | `cargo test --offline -- --list` | **0** | **806** names |
| ignored | `cargo test --offline -- --list --ignored` | **0** | **6** names, the same six real-engine tests |
| formatting | `cargo fmt --all --check` | **0** | 0 bytes on stdout and stderr |
| warnings | both streams | - | **0** `warning:` lines; stderr is 11,744 bytes of pure `Compiling` lines |
| tests removed | `git diff HEAD -- src tests \| grep -c '^[+-].*#\[test\]'` | - | **0** |

**The tests that read the changed files**, run separately because this batch changes records and one
registry constant:

* `cargo test --offline --test evidence_reproduction --test prd_coverage` -> **exit 0**, **12 passed /
  0 failed** (`evidence_reproduction` 7, `prd_coverage` 5). `evidence/index.json` is read by
  `tests/evidence_reproduction.rs`, and the test that matters is
  `the_evidence_index_names_committed_files_and_commands`: it re-derives the corpus (118 files /
  4,771,139 bytes), checks every headline file exists and every headline has a command, and checks the
  group bytes add up. `index.json` is deliberately excluded from that corpus scan, so the corrected
  "meaning" string cannot move a byte count - and the test passes. (The *directory* total does include `index.json`; since the R-A1 hardening of DECISIONS D309 the same test asserts the corpus, the excluded-files and the directory totals separately, so a one-byte edit anywhere under `evidence/` now fails the gate.)
* `cargo test --offline --lib prd_surfaces` -> **exit 0**, **5 passed / 0 failed**. `prd_surfaces.rs` is
  read by `tests/prd_coverage.rs` and by its own unit tests; the registry itself is unchanged, and no test
  reads `RESIDUALS`.
* `.spec/bevy/CLONE-AND-LIVE-REPORT.md` is read by **no** test, build script or gate - `grep` over `src/`,
  `tests/` and `scripts/` finds no reference to it - so the full gate above was run with the corrected
  report already in place.

## 6. What I found contradictory

**No artefact contradicts both the prose and the acceptance.** Every value D-1, D-2 and D-4 turn on was
re-read from its artefact by this batch and matches the acceptance, so no judgement call between competing
records was needed: `fb53d29e`/`51360` really is a ledger line with no `answered_nonce`; `e3-observations.json`
really holds 70 calls with liveness at 69/70; iteration 1 really is the 64-call pass; and the surviving
`launch.json` really is pid 57592's pass. I adopt the artefacts and the acceptance together.

Three things the acceptance did not name, all disclosed above:

1. **`live_round.battery_steps` was iteration 1's pass too** - its jump entry reproduces iteration
   1's raw `e3_jump_arc.json` call-for-call (22 calls, ids `41..62`, identical tool list) and its liveness
   ids were `[63,64]`. Correcting only the numbers D-2 named would have left the report's own
   machine-readable record still describing the wrong pass, so it was regenerated from
   `e3-observations.json`.
2. **`.spec/bevy/COVERAGE-EVIDENCE-REPORT.md` still contradicts itself and this batch could not fix it.**
   Its machine block and several prose sections still call `e3_process_liveness` `PENDING ITS FIRST REAL
   OBSERVATION` and say `no raw/e3_process_liveness.json has ever been produced (defect E-2)`, while its own
   disposition section (around line 565) already records that the follow-up round produced the observation
   and that the surfaces read 15/19. It is a committed batch report, this task forbids modifying batch
   reports, and the acceptance's D-3 named only `evidence/index.json` and `prd_surfaces.rs::RESIDUALS`. It is
   left byte-for-byte as that batch wrote it, and flagged as the next batch's decision.
   **SUPERSEDED:** the next batch was authorised, and the RD-3 correction (DECISIONS D308) rewrote
   those clauses; the paragraph above is the history of this batch's scope decision, not the present
   state of `.spec/bevy/COVERAGE-EVIDENCE-REPORT.md`.
3. **The report's `working_tree_at_end` field and `changed_files.uncommitted_at_write_time` still describe
   the report as uncommitted.** That was true when the batch wrote them; the dispatcher's `c00716d` made it
   false. Those fields are the batch's own history and I left them as written rather than rewriting
   history - the commit is visible in `git log` and in the corrected head note above.

Two smaller notes. `D-7` is settled the same way it was for the previous batch, and this batch must disclose
that the dispatcher did the same thing again: **`aee9c92` committed all four paths while this batch was still
working**, so the delivered revision of this report is newer than the commit. The three corrected files are
byte-identical between `HEAD` and the delivered tree (hashes pinned above), so nothing about the gate depends
on the timing, and the only uncommitted path when this report is written is this report itself - I did not
commit or push anything, as instructed, and I stopped editing when the artefacts were correct. And the 7th
ledger line (`pid 39664`, `launched_at 1791212664`) is still unexplained: it is about four seconds after
iteration 3's pass window ends and it did not overwrite `launch.json`, `meta.json` or `gate.json`. Nothing in
this correction depends on it, and I did not chase it, exactly as the acceptance's `unverified` list did not.

## 7. The single most important thing for the next batch

**Authorise one more correction, or explicitly rule the file out.** The record now agrees with its artefacts
on every point the acceptance named, and the mechanisms it verified were not re-litigated. The only
committed statement left that contradicts the round's own artefacts is inside
`.spec/bevy/COVERAGE-EVIDENCE-REPORT.md` (item 2 above): it still says the liveness step never ran, while the
same file already records that it did. This batch could not lawfully edit it, and the acceptance's D-3 did
not name it, so it will be found again by the next reader unless the dispatcher either gives it an explicit
owner or explicitly excludes it. After that, the only open goal criterion is still cost - 2.55-2.60x the
1,500,000-token per-call target, every call ended at `agent.step_limit: 150` with the tripwire never firing.
