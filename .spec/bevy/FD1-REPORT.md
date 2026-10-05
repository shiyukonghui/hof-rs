```json
{
 "schema": "hof-rs / bevy FD-1 single repair: correct the machine-block clone-safety sentence of .spec/bevy/HARDENING-REPORT.md so its SUPERSEDED label and its RH-4 alternative are present; documents only, no code, test, evidence byte or measured figure changed",
 "produced_at": "2026-10-06",
 "branch": "bevy-core",
 "offline": true,
 "starting_head": "69a65d8265e6006b3bf3bc368b740c0779632001 (`docs(acceptance): record the acceptance that fails the final document pass on one overstated site claim`), whose parent 96acd342ae424eff34fd9a72792f09713739e79f is the revision .spec/bevy/ACCEPTANCE-FINAL-DOC.md judged; origin/bevy-core is still 166212f",
 "defect": {
  "id": "FD-1",
  "source": ".spec/bevy/ACCEPTANCE-FINAL-DOC.md (`verdict: fail`, defects[0])",
  "what": "FINAL-DOC-REPORT.md claimed the overstated clone-safety sentence was corrected at all three sites, naming HARDENING-REPORT.md machine line 156 with sections 0 and 3, but only sections 0 and 3 were changed; line 156 was byte-identical to base 4a85269 and still ended `So the honest answer is that none of the five can be made clone-safe in this batch` with no SUPERSEDED label and only the `evidence/` route as the reason. The record thus both overstated what was done and left the impossibility framing standing at the field whose name asserts it."
 },
 "option_chosen": "A",
 "why_option_A": "A is the only one of the two allowed repairs that closes both halves of FD-1. The acceptance's own `what` says the record `both overstates what was done and leaves the impossibility framing standing at the field whose name asserts it`. Option B (retract the report's three-site claim) would only remove the overstatement and would leave the machine block - the summary a reader or tool is likeliest to take - still asserting an impossibility with only the `evidence/` route. Option A makes the three-site claim true of the delivered tree, keeps the original wording as history per the D308/D309/D310 convention, and puts the RH-4 ruling and its priced alternative (5,917,632 bytes of recordings committable outside `evidence/`, a separate evidence-budget decision, a `runs/**` placement committing key-shaped material, a directory outside `evidence/` escaping the R-A1 totals guard) where the machine block lives. The JSON key name `why_they_cannot_be_made_clone_safe` was deliberately NOT renamed: FINAL-DOC-REPORT.md's `where`/`change_site` and the acceptance name that key, and renaming it while leaving FINAL-DOC-REPORT.md untouched would create a fresh false reference of the same class. The acceptance already files the surviving key name as the non-blocking risk RF-3; this repair leaves RF-3 standing and records it as a residual risk rather than silently expanding scope.",
 "gate": {
  "command": "cargo test --offline",
  "literal_exit_code": 0,
  "passed": 800,
  "failed": 0,
  "ignored": 6,
  "test_result_lines": 60,
  "listed_command": "cargo test --offline -- --list",
  "listed": 806,
  "listed_literal_exit_code": 0,
  "ignored_list_command": "cargo test --offline -- --list --ignored",
  "ignored_listed": 6,
  "ignored_listed_literal_exit_code": 0,
  "fmt_command": "cargo fmt --all --check",
  "fmt_literal_exit_code": 0,
  "fmt_stdout_bytes": 0,
  "fmt_stderr_bytes": 0,
  "warning_lines_stdout": 0,
  "warning_colon_lines_stdout": 0,
  "warning_lines_stderr": 0,
  "warning_colon_lines_stderr": 0,
  "tests_removed": 0,
  "hash_test_attribute_lines": 228,
  "own_build_dir": "D:/hof-fd1-target",
  "free_disk_before_building": "F: 37 GiB free, D: 136 GiB free",
  "one_test_process_at_a_time": true,
  "fresh_build_evidence": "the target directory did not exist before the run; stderr of the first command carries 169 `Compiling` lines and `Finished `test` profile [unoptimized + debuginfo] target(s) in 1m 18s`; D:/hof-fd1-target/debug is 9.1 GiB",
  "starting_tree": "the tree this repair started from measured 800 passed / 0 failed / 6 ignored / 806 listed; the delivered tree measures the same, so no test was removed and none was added",
  "literal_exit_codes_read_from_files": {
   "test": "0",
   "list": "0",
   "list_ignored": "0",
   "fmt": "0"
  }
 },
 "diff_computed": {
  "method": "`git diff -U0 4a85269 96acd34 -- .spec/bevy/HARDENING-REPORT.md` (the acceptance's own comparison, base -> judged revision) and `git diff -U0 96acd34 -- .spec/bevy/HARDENING-REPORT.md` (judged revision -> delivered worktree); line 156 hashed with `sed -n '156p' | sha256sum`, i.e. over the line plus its trailing newline, which is the convention the acceptance used",
  "file_sha256": {
   "4a85269": "bcb77c4df3fc13dc0e43bda4c127f7e12c5598fae7efe876bb12aedbefa548c1",
   "96acd34": "72216de0b42a85d7648c1d41cd732a307f8162122013f3e344ca20fccd5d4813",
   "worktree_after": "bd373b30fcd0da76a264377674962f10ac2ba4c9fa1122631075c47e774c04ac"
  },
  "line_156_sha256": {
   "4a85269": "c1508735134bcdf1ef69c95d42087995043da6c8c19a9b6fcab83df50feb6422",
   "96acd34": "c1508735134bcdf1ef69c95d42087995043da6c8c19a9b6fcab83df50feb6422",
   "byte_identical_before_my_change": true,
   "worktree_after": "2893d496152e475fa886b200fbb9bff8068f4dcfd0c6b25a68123d1bb1cecd6d"
  },
  "hunks_4a85269_to_96acd34": [
   "@@ -109 +109 @@",
   "@@ -179 +179 @@",
   "@@ -223,3 +223 @@",
   "@@ -270,4 +268 @@",
   "@@ -300,6 +295 @@"
  ],
  "hunk_count_4a85269_to_96acd34": 5,
  "hunk_at_line_156": false,
  "grep_count_why_they_cannot_be_made_clone_safe_in_that_diff": 0,
  "sites_touched_before_my_change": [
   "section 0 (hunk @@ -223,3 +223 @@, the scope-decision wording)",
   "section 3 (hunk @@ -300,6 +295 @@, the RH-4 alternative and its cost)"
  ],
  "sites_NOT_touched_before_my_change": [
   "the machine block field clone_safety.why_they_cannot_be_made_clone_safe at line 156"
  ],
  "hunks_96acd34_to_worktree": [
   "@@ -156 +156 @@"
  ],
  "hunk_count_after_my_change": 1,
  "numstat_96acd34_to_worktree": {
   "`.spec/bevy/HARDENING-REPORT.md`": "1 1 (one line replaced; still line 156)",
   "`DECISIONS.md`": "19 0 (appended only)"
  },
  "conclusion": "before my change the machine block was provably untouched: the base->96acd34 diff has no hunk at 156, both revisions' line 156 hash to c1508735..., and the string is absent from the diff. After my change the only hunk in HARDENING-REPORT.md is at line 156."
 },
 "corrected_text": {
  "file": ".spec/bevy/HARDENING-REPORT.md",
  "site": "machine block clone_safety.why_they_cannot_be_made_clone_safe, line 156 (single-line field, still line 156)",
  "original_text_kept_verbatim": "All five measure recordings that are deliberately not committed - `evidence/index.json` names rounds 1-3 (and this batch's own V1 reasoning in DECISIONS D306/D309) as `not_reproducible_from_the_repository`. Committing them would add files under `evidence/` and move both the measured corpus (118 / 4,771,139) and the directory (122 / 4,798,968) totals, which this batch is forbidden to change and which is a separate decision. So the honest answer is that none of the five can be made clone-safe in this batch, and the report says so instead of leaving it to be inferred.",
  "appended": " **[SUPERSEDED 2026-10-06 by the FD-1 correction of `.spec/bevy/ACCEPTANCE-FINAL-DOC.md`, DECISIONS D311, recorded in `.spec/bevy/FD1-REPORT.md`:** the sentence above overstated a scope decision as an impossibility; it was true of what this batch chose to do, not of what is possible. The acceptance's RH-4 is right that this is a scope decision rather than a theorem: the five were left clone-weak deliberately, not because they cannot be made clone-safe. The six recordings these five tests need - measured at 5,917,632 bytes - could be committed outside `evidence/`, by un-ignoring a `runs/**` path or adding a new tracked directory and pointing the five tests at it, without moving the measured corpus (118 / 4,771,139) or directory (122 / 4,798,968) totals. That alternative's cost is real and is a separate decision for the owner of the evidence budget: a `runs/**` placement would commit the key-shaped material the tracked tree currently excludes (`runs/round1` and `runs/round1b`), and a directory outside `evidence/` would not be covered by the R-A1 totals guard. Sections 0 and 3 of this report state the same ruling; no recording was committed, and the original wording is kept above as what this batch believed.]**",
  "corrected_field_value": "All five measure recordings that are deliberately not committed - `evidence/index.json` names rounds 1-3 (and this batch's own V1 reasoning in DECISIONS D306/D309) as `not_reproducible_from_the_repository`. Committing them would add files under `evidence/` and move both the measured corpus (118 / 4,771,139) and the directory (122 / 4,798,968) totals, which this batch is forbidden to change and which is a separate decision. So the honest answer is that none of the five can be made clone-safe in this batch, and the report says so instead of leaving it to be inferred. **[SUPERSEDED 2026-10-06 by the FD-1 correction of `.spec/bevy/ACCEPTANCE-FINAL-DOC.md`, DECISIONS D311, recorded in `.spec/bevy/FD1-REPORT.md`:** the sentence above overstated a scope decision as an impossibility; it was true of what this batch chose to do, not of what is possible. The acceptance's RH-4 is right that this is a scope decision rather than a theorem: the five were left clone-weak deliberately, not because they cannot be made clone-safe. The six recordings these five tests need - measured at 5,917,632 bytes - could be committed outside `evidence/`, by un-ignoring a `runs/**` path or adding a new tracked directory and pointing the five tests at it, without moving the measured corpus (118 / 4,771,139) or directory (122 / 4,798,968) totals. That alternative's cost is real and is a separate decision for the owner of the evidence budget: a `runs/**` placement would commit the key-shaped material the tracked tree currently excludes (`runs/round1` and `runs/round1b`), and a directory outside `evidence/` would not be covered by the R-A1 totals guard. Sections 0 and 3 of this report state the same ruling; no recording was committed, and the original wording is kept above as what this batch believed.]**",
  "requirements_met": [
   "past tense (`it was true of what this batch chose to do`)",
   "marked superseded (`**[SUPERSEDED 2026-10-06 by the FD-1 correction ...]**`)",
   "names the alternative and its size (`could be committed outside `evidence/` ... measured at 5,917,632 bytes`)",
   "names the separate evidence-budget decision",
   "names the `runs/**` key-shaped-material cost",
   "names the `evidence/`-outside totals-guard escape"
  ],
  "json_block_still_parses": true
 },
 "changed_files": [
  {
   "path": ".spec/bevy/HARDENING-REPORT.md",
   "change": "line 156 (single line): the machine-block field keeps its original text and gains the SUPERSEDED label, the RH-4 scope-decision ruling, the 5,917,632-byte alternative and its three costs",
   "numstat_vs_96acd34": "1 1"
  },
  {
   "path": "DECISIONS.md",
   "change": "D311 appended (19 insertions, 0 deletions): records the FD-1 repair, names the option chosen, rejects renaming the JSON key, and names/limits D309's `两处...已更新为新值` sentence",
   "numstat_vs_96acd34": "19 0"
  },
  {
   "path": ".spec/bevy/FD1-REPORT.md",
   "change": "this report (read by no test, build script or gate)"
  }
 ],
 "not_changed": [
  "src/** and tests/** (git diff 96acd34 -- src tests is empty; 228 #[test] attribute lines)",
  "evidence/** and every measured figure (corpus 118 / 4,771,139, excluded 4 / 27,829, directory 122 / 4,798,968)",
  "the coverage registry PRD_SURFACES, the battery, the liveness step, the .gitattributes line-ending pin, config/hoh.yaml and the cost machinery",
  "no recording was committed and none was added: `git ls-files runs` is empty and all six recordings match `.gitignore:9 runs/`",
  "no API key was created, copied or printed; no round, engine, game, network or model call was made",
  "FINAL-DOC-REPORT.md itself is unchanged: option A makes its three-site claim true of the delivered tree"
 ],
 "decisions_on_non_blocking_items": {
  "D309_line_11686": {
   "question": "leave D309's `两处...已更新为新值` unlabelled, or append a correcting entry?",
   "decision": "append a correcting entry (D311) and leave D309 itself untouched",
   "why": "when D309 was written (commit ef2b0d6) only `gate.gate_input_sha256` (`RECORD-CORRECTION-REPORT.md:46`) carried 423036d0 while `changed_files[0].committed_as` (`:129`) still carried 7c09a7ad, so the sentence was false of what D309 did; my own check of the two lines at ef2b0d6/92870a7/96acd34 reproduces that. It happens to have become true of the tree only because H-1 moved the second pin. A false statement of what a decision did is exactly the RD-2 class this line of batches exists to close, so it is not honest enough to leave unrecorded; but this file is append-only by its own convention (D310 rejected editing D309 in place for the same reason), so the correct instrument is an appended entry that names the sentence and limits it. D311 does that (its option 5 and decision (c))."
  },
  "RF-3_field_title": {
   "question": "rename the JSON key `why_they_cannot_be_made_clone_safe`, which still asserts impossibility?",
   "decision": "no - keep the key, correct only its value; record RF-3 as a residual risk",
   "why": "the key is referenced by name in FINAL-DOC-REPORT.md (`clone_safety_sentence.where` and `change_site`) and in the acceptance itself; this repair deliberately does not touch FINAL-DOC-REPORT.md, so renaming the key would leave those references pointing at a key that no longer exists - a fresh H-2-class false reference swapped for the old impossibility framing. The acceptance files RF-3 explicitly as a risk that survives the FD-1 fix, not as part of the minimum repair, so it is disclosed here rather than silently resolved. It remains true after this repair that a reader who looks only at the key name still sees the old framing; the value now contradicts it in the reader's face."
  },
  "RF-1_ACCEPTANCE_TOTALS_scope": {
   "question": "label the stale present tense in ACCEPTANCE-TOTALS.md?",
   "decision": "out of scope, unchanged",
   "why": "the acceptance itself scoped it out (RF-1) as a dated acceptance record that the previous acceptance ruled history; touching it would contradict that ruling and expand this single-defect repair. Recorded as inherited and untouched."
  },
  "RF-4_RF-5": {
   "decision": "unchanged",
   "why": "RF-4 is the disclosed, deliberately uncommitted boundary (no recording may be committed by this task either) and RF-5 is the unmet cost criterion needing a human decision, not a document correction."
  }
 },
 "verified_myself": [
  "line 156 was byte-identical before the change under the acceptance's own hashing convention (c1508735... at both 4a85269 and 96acd34), and the base->96acd34 diff has exactly five hunks (109, 179, 223, 268, 295) with none at 156 and zero occurrences of the field name",
  "the six needed recordings total exactly 5,917,632 bytes (1,072,407 + 1,495,115 + 1,093,652 + 680,974 + 818,938 + 756,546), all six are ignore-matched by `.gitignore:9 runs/`, and `git ls-files runs` is empty - so no measured figure moved and no recording is in the repository",
  "the leading JSON block of HARDENING-REPORT.md parses before and after the edit, and the field is still on line 156 of a single-line field",
  "DECISIONS.md is append-only against 96acd34 (the judged revision's content is a byte-for-byte prefix of the delivered file; 19 added lines, 0 deleted)",
  "no sensitive path changed: `git diff --name-only 96acd34 -- src tests config .gitattributes Cargo.toml Cargo.lock evidence scripts .githooks` is empty, and the only modified worktree files are HARDENING-REPORT.md and DECISIONS.md",
  "the gate on the delivered tree: cargo test --offline literal exit 0 with 800 passed / 0 failed / 6 ignored over 60 `test result:` lines, 806 listed, 6 listed ignored, cargo fmt --all --check literal exit 0 with 0 bytes on both streams, 0 `warning:` lines on either stream, 228 #[test] lines (no test removed), one test process, own build directory D:/hof-fd1-target built fresh in 1m 18s",
  "the D309 sentence's truth-value history, from the artefact rather than the report: at ef2b0d6 line 46 carried 423036d0 and line 129 carried 7c09a7ad (so `both updated` was false when written); at 96acd34 and in the worktree both carry 423036d0 (so it is accidentally true now)"
 ],
 "what_this_repair_did_not_do": "No engine, no game, no network, no model call, no round and no Developer call was run. Nothing was written under `runs/**` and no recording was committed, added, copied or moved. No `rm -rf`, no wildcard deletion and nothing deleted (free disk was sufficient: F: 37 GiB, D: 136 GiB). No path was built from an unexpanded variable; no `git checkout --`; no `git add`, commit, stage or push. Helper scripts live outside the repository under F:/hof-fd1-work/, logs under F:/hof-fd1-logs/, the build under D:/hof-fd1-target. No API key was created, copied or printed. The files written inside the repository are the one corrected line, the DECISIONS.md append and this report.",
 "single_most_important_thing_next_batch": "FD-1 is now closed at both halves, and the tree is documents-only. The one thing the next batch must not assume is that FINAL-DOC-REPORT.md's three-site claim was true of commit 96acd34: it was not - 96acd34 left line 156 untouched, and this repair is what makes the claim true of the delivered tree. A fresh acceptance should therefore verify the corrected line against 4a85269/96acd34 itself (hash c1508735... at both for the old line, one hunk at 156 versus 96acd34) rather than reading the claim, and should otherwise spend its budget on the live criterion: cost, 2.600x / 2.549x / 2.604x of the 1,500,000-token per-call target with agent.step_limit: 150 binding, which needs a human decision and not another document correction. RF-3 (the machine-block key name) and RF-1 (dated ACCEPTANCE-TOTALS.md present tense) remain open, disclosed and untouched."
}
```


# FD1-REPORT - the single FD-1 repair: the machine-block clone-safety sentence

**Documents only, one defect, option A.** This batch repairs the one defect
`.spec/bevy/ACCEPTANCE-FINAL-DOC.md` recorded - `FD-1` - and nothing else. It was **offline**: no
engine, no game, no network, no model call, no round and no Developer call. No recording was
committed, added, copied or moved; nothing was written under `runs/**`; no measured figure was
changed; no code, test, `evidence/**`, registry, battery, liveness step, `.gitattributes` pin,
config or cost machinery was touched. No `rm -rf`, no wildcard deletion and nothing deleted; no
`git checkout --`; no path built from an unexpanded variable; no API key created, copied or printed;
nothing committed or pushed (the dispatcher does that). Helper scripts live outside the repository
under `F:/hof-fd1-work/`, logs under `F:/hof-fd1-logs/`, the build under `D:/hof-fd1-target`. The
machine-readable block above is `json.dumps(..., indent=1, ensure_ascii=False)` output written by
`F:/hof-fd1-work/gen_report.py`, which then **parsed it back out of the written file** and failed
unless it round-tripped equal.

## 0. The repair in one paragraph

I chose **option A** and corrected `HARDENING-REPORT.md:156`, the machine-block field
`clone_safety.why_they_cannot_be_made_clone_safe`. The field keeps its original wording
byte-for-byte and gains a `**[SUPERSEDED 2026-10-06 by the FD-1 correction ...]**` label that says
the old sentence overstated a scope decision as an impossibility, that the five tests were left
clone-weak deliberately rather than being impossible to fix, that their six needed recordings
(measured again here at **5,917,632** bytes) could be committed outside `evidence/`, and what that
alternative costs: a separate evidence-budget decision, the key-shaped material a `runs/**`
placement would commit, and the R-A1 totals guard a directory outside `evidence/` would escape.
The field is still line 156 and still a single line; the leading JSON block still parses. Option B
was rejected because it would have removed only the overstatement and left the impossibility
framing standing in the machine block, which is one of the two halves FD-1 names.

## 1. What I verified, and how

* **The defect is real and it is exactly as described.** `git diff -U0 4a85269 96acd34 --
  .spec/bevy/HARDENING-REPORT.md` has five hunks - `@@ -109 +109 @@`, `@@ -179 +179 @@`,
  `@@ -223,3 +223 @@`, `@@ -270,4 +268 @@`, `@@ -300,6 +295 @@` - none at 156, and zero
  occurrences of `why_they_cannot_be_made_clone_safe`. `sed -n '156p' | sha256sum` gives
  `c1508735134bcdf1ef69c95d42087995043da6c8c19a9b6fcab83df50feb6422` at **both** 4a85269 and
  96acd34. Before my change the only two corrected clone-safety sites were section 0 (the `-223,3`
  hunk) and section 3 (the `-300,6` hunk). After my change the only hunk in the file against
  96acd34 is `@@ -156 +156 @@`, numstat `1 1`.
* **The figures in the corrected text are the measured ones, checked independently.** I re-walked
  the six `developer.attempt1.json` files read-only: 1,072,407 + 1,495,115 + 1,093,652 + 680,974 +
  818,938 + 756,546 = **5,917,632** bytes, and `git check-ignore -v` shows all six matched by
  `.gitignore:9 runs/` while `git ls-files runs` is empty. Nothing was committed and no measured
  figure moved.
* **No over-reach.** `git diff --name-only 96acd34 -- src tests config .gitattributes Cargo.toml
  Cargo.lock evidence scripts .githooks` is empty; the worktree has exactly two modified files
  (`HARDENING-REPORT.md` 1/1, `DECISIONS.md` 19/0) plus this new report; `DECISIONS.md`'s 96acd34
  content is a byte-for-byte prefix of the delivered file (append-only); the `#[test]` count is 228.
* **The gate reproduces on the delivered tree.** `cargo test --offline` gives **literal exit code
  0** with **800 passed / 0 failed / 6 ignored** over 60 `test result:` lines, **806** listed and
  **6** listed ignored (both literal exit 0); `cargo fmt --all --check` gives literal exit 0 with
  **0 bytes** on stdout and stderr; there are **0** `warning:` lines on either stream; the tree
  started at 800/0/6/806, so no test was removed or added. Free disk was checked first (F: 37 GiB,
  D: 136 GiB), no cargo/rustc process was running, the build directory was this batch's own
  `D:/hof-fd1-target` (built fresh, 169 `Compiling` lines, `Finished ... in 1m 18s`), and one test
  process ran at a time.
* **The JSON block survives.** I parsed the leading block of `HARDENING-REPORT.md` before and after
  the edit and read the field back; the corrected line is still line 156, still one line.

## 2. The two non-blocking items, decided

**D309:11686 (`两处...已更新为新值`). An appended correcting entry is better than leaving it.** I
checked the artefact: at `ef2b0d6` - the commit D309 describes - `RECORD-CORRECTION-REPORT.md:46`
already carried `423036d0...` while `:129` still carried `7c09a7ad...`, so the sentence was false of
what D309 did. It is now accidentally true of the tree only because H-1 moved the second pin, which
means it no longer misleads about the current value but remains a false record of D309's own action
- the RD-2 class these batches exist to close. Leaving it silently would be the same species of
defect this repair is fixing, one level up. Since `DECISIONS.md` is append-only by its own
convention (D310's option 5 rejected editing D309 in place for exactly this reason), the honest
instrument is an appended entry that names the sentence and limits it; **D311 does that** and D309
itself is untouched.

**RF-3 (the surviving key name). Keep the key; record it as residual risk.** I did not rename
`why_they_cannot_be_made_clone_safe`. The key is referenced **by name** in
`FINAL-DOC-REPORT.md`'s `clone_safety_sentence.where` and `change_site` and in the acceptance, and
this repair deliberately does not edit `FINAL-DOC-REPORT.md`; renaming the key would leave those
references pointing at a key that no longer exists, i.e. swap the old impossibility framing for a
fresh H-2-class false reference. The acceptance files RF-3 as a risk that survives the FD-1 fix,
not as part of the minimum repair, so the key keeps its name and its value now contradicts it
openly. RF-1 (dated `ACCEPTANCE-TOTALS.md` present tense) stays out of scope, as the acceptance
scoped it; RF-4 and RF-5 are unchanged and are not document-correction material.

## 3. The single most important thing for the next batch

**Do not assume FINAL-DOC-REPORT.md's three-site claim was true of `96acd34`.** It was not:
`96acd34` left line 156 untouched, and this repair is what makes the claim true of the delivered
tree. Option A was authorised to let the claim stand, but the honest reading of the history is that
the claim was retro-fitted rather than satisfied at the judged revision, and the next acceptance
should verify the corrected line against `4a85269`/`96acd34` itself - old line `c1508735...` at
both, exactly one hunk at 156 against `96acd34` - instead of reading the claim. Everything else in
this repair is deliberately minimal; the only open goal criterion remains **cost** (2.600x /
2.549x / 2.604x of the 1,500,000-token per-call target with `agent.step_limit: 150` binding), which
needs a human decision, not another document.
