```json
{
 "schema": "hof-rs / bevy hardening batch for risks R-A1, R-A2 and R-A4 of .spec/bevy/ACCEPTANCE-TOTALS.md; the cost risk R-A3 is explicitly out of scope and the cost machinery is untouched",
 "produced_at": "2026-10-06",
 "branch": "bevy-core",
 "base_head": "166212f1fc4f2e520170e19b894b28501a58235d",
 "working_tree_at_gate": "The gate ran with exactly the six tracked files of `changed_files` differing from HEAD. This report is written afterwards and is the seventh changed path; no test, build script, registry, battery step or gate reads it.",
 "offline": true,
 "what_this_batch_did_not_do": "No engine, no game, no network, no model call, no round and no Developer call was run. Nothing was written under `runs/**`. No API key was created, copied or printed. Nothing was committed, staged or pushed. No `git checkout --` was used anywhere and no path was built from an unexpanded variable. No `rm -rf` was used: the one temporary tree this batch created under `F:/hof-hard-work/` was removed by `F:/hof-hard-work/remove_tree.py`, which prints every path and the file count before `shutil.rmtree`. The frozen documents (`.spec/bevy/REQUIREMENTS.md`, `PRD.md`, `DESIGN-OVERVIEW.md`, `DESIGN-DETAIL.md`, the spike reports) were not touched; `DECISIONS.md` was only appended to (D309). No cost machinery, coverage registry, battery, liveness step, line-ending pin or measured figure was changed. Free disk was checked before building (F: 47 GiB free). Helper scripts live outside the repository under `F:/hof-hard-work/`; the gate build is this batch's own `F:/hof-hard-target`; one test process ran at a time.",
 "gate": {
  "command": "cargo test --offline",
  "literal_exit_code": 0,
  "passed": 800,
  "failed": 0,
  "ignored": 6,
  "test_result_lines": 60,
  "listed": 806,
  "listed_literal_exit_code": 0,
  "listed_ignored": 6,
  "listed_ignored_literal_exit_code": 0,
  "fmt_command": "cargo fmt --all --check",
  "fmt_literal_exit_code": 0,
  "fmt_stdout_bytes": 0,
  "fmt_stderr_bytes": 0,
  "warning_lines": 0,
  "warning_colon_lines": 0,
  "tests_removed": 0,
  "baseline_it_reproduces": "800 passed / 0 failed / 6 ignored / 806 listed, the figure the tree this batch started from measures"
 },
 "totals_guard": {
  "why": "Risk R-A1: the evidence directory totals were hand-stated and guarded by no test, so one byte added to a non-corpus file under `evidence/` falsified them while the whole gate stayed green - the same class as defect RD-1. The walk that already re-derived the corpus silently `continue`d the four excluded files.",
  "test": "tests/evidence_reproduction.rs::the_evidence_index_names_committed_files_and_commands (the walk at lines 495-598)",
  "it_now_asserts": [
   "the corpus total (118 files / 4,771,139 bytes) - the six data groups, i.e. every committed file under `evidence/` except index.json, README.md and the two evidence/tools/*.py (line 562)",
   "the excluded-files total (4 files / 27,829 bytes) - index.json + README.md + tools/build_evidence.py + tools/keyscan.py (line 569)",
   "the directory total (122 files / 4,798,968 bytes) - everything under `evidence/` (line 576)",
   "the arithmetic identity directory = corpus + excluded, files and bytes (lines 580-584)",
   "that evidence/README.md states the directory total this test measured, `122 files / 4,798,968 bytes` (line 595)",
   "the pre-existing pins: the index's own corpus block, the group-byte sum, every headline file's existence and command, and the not_reproducible list"
  ],
  "three_figures_are_distinguished": "Each assertion names its own figure in its failure message, so a failure says which total moved rather than only that a total is wrong.",
  "plant": {
   "where": "a copy of the 323 tracked files outside the repository, `F:/hof-hard-work/clone-control` (no `runs/**`)",
   "what": "appended one byte, `0x0A`, to the copy's `evidence/index.json`: 15,570 -> 15,571 bytes",
   "result": "`cargo test --offline --test evidence_reproduction` in the copy -> literal exit code 101, 6 passed / 1 failed, and the failure is the total's own message: `the excluded-files total (index.json + README.md + tools/build_evidence.py + tools/keyscan.py, which the corpus leaves out): 4 files / 27830 bytes` at tests/evidence_reproduction.rs:566",
   "caveat_disclosed": "A raw non-JSON byte (e.g. `x`) also fails that test, but at tests/evidence_reproduction.rs:43, in the JSON parse - it never reaches the total's assertion. The plant that exercises the guard must keep `index.json` parseable, so the byte used here is a trailing newline. Both are red; only the newline plant proves the total is guarded rather than the parser.",
   "restore": "the copy's `evidence/index.json` was rewritten from the repository file, sha256 equality with `eb88286c...` confirmed true, and the same command then exited 0 with 7 passed",
   "repo_untouched": "The repository's own `evidence/` was never modified: `evidence/index.json` still hashes to `eb88286c638363a7ff64e7aa1bf901159cc68bf0663707c9526f258a9bb03d2f` and the measured totals are still 122/4,798,968 directory, 4/27,829 excluded, 118/4,771,139 corpus."
  }
 },
 "stale_references": {
  "what": "Risk R-A2: present-tense cross-references inside batch reports that later corrections made false. Every one is kept as written where it records a real past state, and labelled `SUPERSEDED` at the point of the claim; none was deleted, because the project's convention is to keep what was believed and when.",
  "corrected_or_labelled": [
   {
    "file": ".spec/bevy/COVERAGE-EVIDENCE-REPORT.md",
    "at": "line 565 (machine block, corrections_after_acceptance_evidence.E-2)",
    "was": "`every claim ... now reads *implemented, pending its first real observation*` / `That is the state of the committed evidence`",
    "now": "past tense (`was rewritten to read` / `That was the state ... when E-2 was fixed`) plus a `SUPERSEDED SINCE, history kept` label naming the RD-3 correction (DECISIONS D308) and the record correction (D-3 of ACCEPTANCE-CLONE-LIVE.md)"
   },
   {
    "file": ".spec/bevy/COVERAGE-EVIDENCE-REPORT.md",
    "at": "lines 858-859 (§8)",
    "was": "`DECISIONS.md` is still append-only",
    "now": "`was append-only as this batch wrote it` plus `SUPERSEDED SINCE`: D306(c) was edited in place under authorisation and D308 appended (DECISIONS D308)"
   },
   {
    "file": ".spec/bevy/CLONE-AND-LIVE-REPORT.md",
    "at": "line 119 (machine block, defects[E-2].change)",
    "was": "`the batch report's own two are left exactly as it wrote them`",
    "now": "past tense with the RD-3 correction named and a `SUPERSEDED` pointer to RECORD-CORRECTION-REPORT.md C-3 and DECISIONS D308"
   },
   {
    "file": ".spec/bevy/CLONE-AND-LIVE-REPORT.md",
    "at": "lines 1690-1692 (§4)",
    "was": "`leaves the batch report's own two (...) exactly as that batch wrote them`",
    "now": "`left ... exactly as that batch wrote them` plus `SUPERSEDED SINCE`: those two were afterwards rewritten by the RD-3 correction (DECISIONS D308)"
   },
   {
    "file": ".spec/bevy/RECORD-CORRECTION-REPORT.md",
    "at": "lines 173-175 (C-3.what and C-3.disposition)",
    "was": "`One committed report still contradicts itself ... its machine block and several prose sections still say ...` and `disposition: left untouched`",
    "now": "the `what` keeps its history with a `SUPERSEDED 2026-10-06 by the RD-3 correction` bracket, and the `disposition` records that the authorisation was granted and the clauses were rewritten"
   },
   {
    "file": ".spec/bevy/RECORD-CORRECTION-REPORT.md",
    "at": "line 114 (D-3.deliberately_not_corrected)",
    "was": "`its machine block still carries the pre-round wording`",
    "now": "past tense plus `SUPERSEDED`: the clauses were rewritten by DECISIONS D308"
   },
   {
    "file": ".spec/bevy/RECORD-CORRECTION-REPORT.md",
    "at": "line 183 (single_most_important_thing_next_batch)",
    "was": "`COVERAGE-EVIDENCE-REPORT.md is the only committed statement left that contradicts the round's own artefacts`",
    "now": "original kept with a `SUPERSEDED 2026-10-06 by the RD-3 correction, DECISIONS D308` bracket at the end"
   },
   {
    "file": ".spec/bevy/RECORD-CORRECTION-REPORT.md",
    "at": "lines 365-372 (§6 item 2)",
    "was": "`still contradicts itself and this batch could not fix it ... left byte-for-byte as that batch wrote it`",
    "now": "original kept with a `SUPERSEDED` paragraph saying the next batch was authorised and the RD-3 correction rewrote those clauses"
   },
   {
    "file": ".spec/bevy/RECORD-CORRECTION-REPORT.md",
    "at": "line 61 (tests_that_read_the_changed_files) and line 342 (§5 prose)",
    "was": "`cannot move a byte count` - true of the corpus, read as covering the directory",
    "now": "`cannot move the *corpus* byte count`, with the directory total named as a different figure and pointed at the R-A1 guard added by this batch"
   }
  ],
  "consequential_pin": "Labelling the two CLONE-AND-LIVE-REPORT.md clauses moved that file's sha256 from `7c09a7ad...` to `423036d0b10f44fd00126f3bb4066ef1c6d303d5ceee415d733d619afebc4006`. That file is pinned in two places in `.spec/bevy/RECORD-CORRECTION-REPORT.md` (gate.gate_input_sha256 and changed_files), **Correction (defect H-2 of `.spec/bevy/ACCEPTANCE-HARDENING.md`): only ONE of the two was actually moved.** `gate.gate_input_sha256` (line 46) was set to `423036d0...` and its note (line 47) rewritten to name all three values; `changed_files[0].committed_as` (line 129) was left unchanged and therefore still presented `7c09a7ad...` in the present tense with no label, which is false of the tree it ships. The original claim in this field - that `both were updated to the new value` - was therefore a fresh false statement of the RD-2 class. The omission is repaired by the follow-up document correction (H-1 of the same acceptance, recorded in `.spec/bevy/FINAL-DOC-REPORT.md`), which moves line 129 to `423036d0...` and keeps `889033a5...` (f1b9af3 revision, labelled SUPERSEDED) and `7c09a7ad...` (post-RD-1 revision, labelled SUPERSEDED) beside it. This field keeps its history rather than deleting it: what this batch records is that it intended the minimum RD-2-consistent change, moved one pin, and wrongly reported both. No test, build script or gate reads that file, so the gate numbers and gate input set are unaffected."
 },
 "clone_safety": {
  "method": "A copy of the 323 tracked files was made outside the repository at `F:/hof-hard-work/clone-control` (`F:/hof-hard-work/copy_tracked.py`); it has no `runs/**`, which is the state a fresh clone is in. `git init -q` was then run inside it so `git check-attr` works. Disclosed harness failure: before that `git init`, the copy's full gate was exit 101 with one failure, `tests/push_gate.rs::the_shell_artifacts_keep_lf_line_endings_and_a_shebang`, because `git check-attr` needs a repository - an artefact of the copy, not a property of a real clone, and it disappeared once the copy was a repository. The copy has since been removed by the verified Python script.",
  "clone_gate": {
   "literal_exit_code": 0,
   "passed": 800,
   "failed": 0,
   "ignored": 6,
   "test_result_lines": 60,
   "listed": 806,
   "listed_ignored": 6,
   "warning_lines": 0
  },
  "the_point": "The clone's counts are identical to the working tree's, but a subset of those 800 passes asserts nothing in the clone. The acceptance's R-A4/R-2 counted three; this batch's census found five, two of which skipped in silence.",
  "clone_weak": [
   {
    "test": "tests/repeated_action.rs::the_recorded_round_two_developer_really_repeats_one_action_past_the_cap",
    "needs": "runs/round2/iter-1/traj/developer.attempt1.json",
    "was": "printed a reason and returned",
    "now": "unchanged - already printed"
   },
   {
    "test": "tests/repeated_action.rs::the_repeated_success_tripwire_fires_on_the_recorded_grind",
    "needs": "runs/round2/iter-1/traj/developer.attempt1.json",
    "was": "printed a reason and returned",
    "now": "unchanged - already printed"
   },
   {
    "test": "tests/repeated_action.rs::the_recorded_engineering_call_defines_the_upper_bound_of_the_cap",
    "needs": "runs/round2/iter-2/traj/developer.attempt1.json",
    "was": "returned in SILENCE - the acceptance did not count it",
    "now": "prints which recording is missing and why (added by this batch)"
   },
   {
    "test": "tests/repeated_action.rs::the_round_three_developer_calls_were_below_the_cap_for_a_measured_reason",
    "needs": "runs/round3/iter-{1,2,3}/traj/developer.attempt1.json",
    "was": "`continue`d in SILENCE and the whole body sits behind `if measured > 0`, so the test asserted nothing - the acceptance did not count it",
    "now": "prints, per iteration, which recording is missing and why (added by this batch)"
   },
   {
    "test": "tests/write_path_contract.rs::the_recorded_round_one_trajectory_really_carried_these_shapes",
    "needs": "runs/round1b/iter-1/traj/developer.attempt1.json",
    "was": "printed a reason and returned",
    "now": "unchanged - already printed"
   }
  ],
  "why_they_cannot_be_made_clone_safe": "All five measure recordings that are deliberately not committed - `evidence/index.json` names rounds 1-3 (and this batch's own V1 reasoning in DECISIONS D306/D309) as `not_reproducible_from_the_repository`. Committing them would add files under `evidence/` and move both the measured corpus (118 / 4,771,139) and the directory (122 / 4,798,968) totals, which this batch is forbidden to change and which is a separate decision. So the honest answer is that none of the five can be made clone-safe in this batch, and the report says so instead of leaving it to be inferred. **[SUPERSEDED 2026-10-06 by the FD-1 correction of `.spec/bevy/ACCEPTANCE-FINAL-DOC.md`, DECISIONS D311, recorded in `.spec/bevy/FD1-REPORT.md`:** the sentence above overstated a scope decision as an impossibility; it was true of what this batch chose to do, not of what is possible. The acceptance's RH-4 is right that this is a scope decision rather than a theorem: the five were left clone-weak deliberately, not because they cannot be made clone-safe. The six recordings these five tests need - measured at 5,917,632 bytes - could be committed outside `evidence/`, by un-ignoring a `runs/**` path or adding a new tracked directory and pointing the five tests at it, without moving the measured corpus (118 / 4,771,139) or directory (122 / 4,798,968) totals. That alternative's cost is real and is a separate decision for the owner of the evidence budget: a `runs/**` placement would commit the key-shaped material the tracked tree currently excludes (`runs/round1` and `runs/round1b`), and a directory outside `evidence/` would not be covered by the R-A1 totals guard. Sections 0 and 3 of this report state the same ruling; no recording was committed, and the original wording is kept above as what this batch believed.]**",
  "what_still_covers_the_mechanism_in_a_clone": "The mechanisms are unit-tested in the library, not only in these recordings: `harness::guard`'s repeated-success tripwire and step-budget tests run in the clone. The round-4 measurement is clone-safe because `evidence/cost/round4-iter-{1,2,3}.developer.attempt1.json` is committed: `repeated_action.rs::the_round_four_developer_repeats_are_measured_and_not_assumed` asserts `measured == 3` unconditionally and passes in the clone, and `tests/context_compaction.rs` and `tests/write_accounting.rs` prefer `evidence/cost/` and assert against those bytes in the clone.",
  "census": "`grep -rn skipped tests/*.rs` finds a gate-skip print in `tests/repeated_action.rs` and `tests/write_path_contract.rs` only; there is no sixth. The clone run of `repeated_action -- --nocapture` shows exactly four skip lines and `write_path_contract -- --nocapture` exactly one, naming the recordings above."
 },
 "changed_files": [
  {
   "path": "tests/evidence_reproduction.rs",
   "change": "R-A1: the evidence walk now accumulates the corpus, the excluded-files and the directory totals and asserts each, plus the identity and the README statement"
  },
  {
   "path": "tests/repeated_action.rs",
   "change": "R-A4: the two silent clone-skip branches now print which recording is missing and why"
  },
  {
   "path": ".spec/bevy/COVERAGE-EVIDENCE-REPORT.md",
   "change": "R-A2: E-2 and the §8 append-only claim put in past tense and labelled SUPERSEDED"
  },
  {
   "path": ".spec/bevy/CLONE-AND-LIVE-REPORT.md",
   "change": "R-A2: the two 'left exactly as that batch wrote them' clauses put in past tense and labelled SUPERSEDED (this moves the file's sha256, handled under stale_references.consequential_pin)"
  },
  {
   "path": ".spec/bevy/RECORD-CORRECTION-REPORT.md",
   "change": "R-A2: C-3.what/disposition, deliberately_not_corrected, single_most_important_thing_next_batch, §6 item 2 and the two 'cannot move a byte count' statements labelled or clarified; plus ONE of the two CLONE-AND-LIVE-REPORT.md sha256 pins moved to the new value with the old kept as history (`gate.gate_input_sha256` was moved; `changed_files[0].committed_as` was NOT - defects H-1/H-2 of .spec/bevy/ACCEPTANCE-HARDENING.md, corrected by the follow-up document correction)"
  },
  {
   "path": "DECISIONS.md",
   "change": "D309 appended (nothing else touched)"
  },
  {
   "path": ".spec/bevy/HARDENING-REPORT.md",
   "change": "this report"
  }
 ],
 "unverified": [
  "A real `git clone` of my own. I used a copy of the tracked files plus `git init`, not `git clone`, so I did not re-run the acceptance's green-pinned clone experiment; what I did verify is that the copy with no `runs/**` reaches the same 800/0/6/806 with the five skips above.",
  "A Linux or macOS clone, where `core.autocrlf` is false by default.",
  "That every one of the other 795 tests asserts something in a clone. I censused the skip-printing sites over `tests/*.rs` and checked the tests whose evidence source is `evidence/cost/`; I did not audit all 800 individually.",
  "Whether the cost criterion can be met, which is risk R-A3 and is out of scope for this batch."
 ],
 "single_most_important_thing_next_batch": "The cost criterion is now the only unmet goal criterion and it is untouched by this batch: 2.549x-2.604x the 1,500,000-token per-call target, each call ended by `agent.step_limit: 150`, the tripwire never firing (risk R-A3 of ACCEPTANCE-TOTALS.md). It needs a human decision, not another record correction. Secondary, and now enforced rather than merely stated: any future edit under `evidence/` must update the totals stated in `evidence/README.md` in the same change, or tests/evidence_reproduction.rs will fail the gate - the point of the R-A1 guard."
}
```

# HARDENING-REPORT - R-A1, R-A2 and R-A4 of the totals acceptance

**Offline** hardening for the three risks `.spec/bevy/ACCEPTANCE-TOTALS.md` recorded and did not fix.
Risk **R-A3 (cost) is deliberately out of scope** and nothing in the cost machinery was read, edited or
run. No engine, no game, no network, no model call, no round and no Developer call. Nothing was committed
or pushed. The machine-readable block above is `json.dumps(..., indent=1, ensure_ascii=False)` output
written by `F:/hof-hard-work/gen_hardening.py` and then **parsed back out of this written file**, which is
the last thing the generator does.

## 0. The verdict in one paragraph

**The totals are now self-guarding, the stale cross-references are labelled rather than rewritten, and
the clone's weakness is stated instead of inferred.** The gate on the tree this batch produced is
`cargo test --offline` literal exit code **0** with **800 passed / 0 failed / 6 ignored / 806 listed**
over 60 `test result:` lines, `cargo fmt --all --check` exit 0 with 0 bytes on both streams, **0 warning
lines**, and no test removed. The one test that walks `evidence/` now counts **three** figures - the
corpus (118 files / 4,771,139 bytes), the excluded files (4 files / 27,829 bytes) and the directory
(122 files / 4,798,968 bytes) - asserts each with its own message, asserts that the third is the first two
added, and asserts that `evidence/README.md` states the directory total it just measured; a controlled
plant on a copy outside the repository (one `0x0A` appended to `index.json`, 15,570 -> 15,571) makes it
exit **101** with `the excluded-files total ... 4 files / 27830 bytes`, and restoring the byte makes it
green again. Nine statements in three batch reports are labelled `SUPERSEDED` in place with the original
wording kept. The clone census found **five** clone-weak tests, not the acceptance's three - two of them
skipped **in silence** - and all five now print which recording is missing; none of the five was made clone-safe in this batch. That is a deliberate scope decision rather than a theorem (RH-4 of `.spec/bevy/ACCEPTANCE-HARDENING.md`): the needed recordings could be committed outside `evidence/` without moving the measured totals, at the cost of a separate evidence-budget decision - and, for a `runs/**` path, of committing the key-shaped material the tracked tree currently excludes. Section 3 states the alternative and its cost; the original wording, that none of the five can honestly be made clone-safe, overstated the finding and is superseded.

## 1. R-A1 - the totals are guarded where they are stated

The acceptance's reproduction was exact: `tests/evidence_reproduction.rs::the_evidence_index_names_committed_files_and_commands`
walked all of `evidence/`,
`continue`d `index.json`, `README.md` and the two `tools/*.py` by name, and asserted only the corpus - so
the directory total that `evidence/README.md` states by hand could move without the gate noticing. That
is the same class as defect **RD-1**, and it was the second time it had happened.

The fix is in the walk that already enumerated the files, exactly as the acceptance suggested: the four
skipped names are now accumulated instead of discarded, so the walk knows all three totals, and all three
are asserted (lines 562, 569, 576) with the identity `directory = corpus + excluded` (lines 580-584) and
the README's own sentence (line 595). The corpus assertion against `index.json`'s block stays; the
excluded and directory assertions are new. A one-byte edit to a non-corpus file now fails twice over
(the excluded total and the directory total), and a one-byte edit to a corpus file fails the corpus total
and the index check.

**The plant, and one caveat I am disclosing rather than hiding.** On a copy of the 323 tracked files
outside the repository (`F:/hof-hard-work/clone-control`) I appended one byte to
`evidence/index.json`. My first attempt used a raw `0x78` byte and the test exited 101 - but at
`tests/evidence_reproduction.rs:43`, inside the JSON parse, so it never reached the total's assertion:
an unparseable index proves nothing about the totals. The plant that actually exercises the guard
therefore has to keep the file valid JSON, so I used a trailing `0x0A`: 15,570 -> 15,571 bytes, and the
failure became the total's own message at line 566 -
`the excluded-files total (index.json + README.md + tools/build_evidence.py + tools/keyscan.py, which
the corpus leaves out): 4 files / 27830 bytes`. I then rewrote the copy's file from the repository file,
confirmed the sha256s are equal, and the same command exited 0 with 7 passed. The repository's own
`evidence/` was never touched: `index.json` still hashes to `eb88286c...` and the three figures are
unchanged.

## 2. R-A2 - what the reports still said in the present tense

None of these was rewritten; each was put in the tense that was true and labelled where the new truth
arrived, because the reports are the record of what was believed and when. The nine sites are listed in
the machine block; the two hardest are worth naming here.

`COVERAGE-EVIDENCE-REPORT.md:565` said every claim "now reads *implemented, pending its first real
observation*" and "That is the state of the committed evidence". That was made false for this report's own
machine block and prose by the RD-3 correction, and it had already been made false for the other two
places by the record correction. It now reads in the past tense with a `SUPERSEDED SINCE` label naming both
corrections.

`CLONE-AND-LIVE-REPORT.md:1690-1691` said this correction "leaves the batch report's own two exactly as
that batch wrote them" - also made false by RD-3. Labelling it changes that file's bytes, and that file is
pinned by sha256 in **two** places in `RECORD-CORRECTION-REPORT.md`. Leaving the pins alone would have planted a fresh RD-2-class false statement, so - following the precedent the previous acceptance called correct - the two pins were meant to be moved together to the new value `423036d0...` and to keep `889033a5...` (the f1b9af3 revision) and `7c09a7ad...` (the post-RD-1 revision) as labelled history beside them. **Correction (defect H-2 of `.spec/bevy/ACCEPTANCE-HARDENING.md`): only one was actually moved.** `gate.gate_input_sha256` (`RECORD-CORRECTION-REPORT.md:46`) was set to `423036d0...` and its note at `:47` names all three values; `changed_files[0].committed_as` (`:129`) was left presenting `7c09a7ad...` in the present tense with no label, which is false, and the machine block's `consequential_pin` claimed both were updated - a fresh false statement of the RD-2 class this batch existed to close. The follow-up document correction (H-1, recorded in `.spec/bevy/FINAL-DOC-REPORT.md`) moves `:129` to `423036d0...` and keeps both earlier values there as labelled `SUPERSEDED` history. No test, build script or gate
reads that file; I grepped `tests/`, `src/` and `scripts/` to confirm it.

The two `cannot move a byte count` statements in `RECORD-CORRECTION-REPORT.md` are true of the **corpus**
and were read as covering the **directory**; both now say corpus, and point at the R-A1 guard.

## 3. R-A4 - which tests are weaker in a clone, and why

I did not trust the acceptance's count of three. The census (`grep -rn skipped tests/*.rs` plus every
early-return branch whose evidence source is a recording) gives **five** tests that assert nothing in a
clone, and **two of them were silent**:

| test | recording it needs | before | after |
|---|---|---|---|
| `repeated_action.rs::the_recorded_round_two_developer_really_repeats_one_action_past_the_cap` | `runs/round2/iter-1/...` | printed | printed |
| `repeated_action.rs::the_repeated_success_tripwire_fires_on_the_recorded_grind` | `runs/round2/iter-1/...` | printed | printed |
| `repeated_action.rs::the_recorded_engineering_call_defines_the_upper_bound_of_the_cap` | `runs/round2/iter-2/...` | **silent return** | prints |
| `repeated_action.rs::the_round_three_developer_calls_were_below_the_cap_for_a_measured_reason` | `runs/round3/iter-{1,2,3}/...` | **silent `continue`, whole body behind `if measured > 0`** | prints |
| `write_path_contract.rs::the_recorded_round_one_trajectory_really_carried_these_shapes` | `runs/round1b/iter-1/...` | printed | printed |

The clone experiment: a copy of the tracked files with no `runs/**`, made a repository with `git init -q`,
runs the full gate green - exit 0, 800/0/6 over 60 lines, 806 listed - and the five tests print their
reasons while asserting nothing. (Disclosed harness failure: before the `git init`, one test,
`push_gate.rs::the_shell_artifacts_keep_lf_line_endings_and_a_shebang`, failed with `fatal: not a git
repository`, because `git check-attr` needs a repository. That was my copy's deficiency, not a clone
defect, and it is not a finding about the tree.)

**The five were left clone-weak by a deliberate scope decision, and that decision is not a theorem.** Their subject is `runs/round1b`, `runs/round2` and `runs/round3`, which are gitignored and which `evidence/index.json` deliberately lists as `not_reproducible_from_the_repository`. Committing them under `evidence/` would add files and move the corpus and directory totals - the very figures this batch is forbidden to change, and a decision that belongs to the owner of the evidence budget, not to a hardening batch. But the acceptance's RH-4 is right that this is a scope choice rather than an impossibility: committing the recordings somewhere other than `evidence/` (un-ignoring a `runs/**` path, or a new tracked directory, and pointing the five tests at it) would leave the measured totals untouched. What that alternative costs is real but is a cost, not a barrier: it is a separate decision the owner must take; placing the files under `runs/**` commits the key-shaped material the tracked tree currently excludes (`runs/round1` and `runs/round1b`); and a directory outside `evidence/` would not be covered by the R-A1 totals guard. The original wording here - that none of the five can be made clone-safe here and the reason is structural, not a choice - overstated a scope decision as a fact and is superseded by this paragraph. What a clone keeps is the mechanism: `harness::guard`'s tripwire and step-budget unit tests run
there, and the round-4 measurement is clone-safe because `evidence/cost/round4-iter-{1,2,3}` is committed -
`the_round_four_developer_repeats_are_measured_and_not_assumed` asserts `measured == 3` in the clone.

## 4. What I verified, and what I could not

**Verified.** The gate's literal exit code and counts on the exact tree (before the two documentation
writes that followed it and that no test reads); `--list` 806 and `--list --ignored` 6, both exit 0;
`fmt` exit 0 with 0 bytes; 0 warnings; no test removed (`git diff --stat` shows only the six tracked
files, two of them tests, and the `#[test]` count is unchanged at 806). The three totals re-derived by an
independent walk (122/4,798,968, 4/27,829, 118/4,771,139). The plant, its red message, its caveat and its
restore. The edited JSON machine blocks in all three reports still parse. `evidence/index.json` still
hashes to `eb88286c...` and no file under `evidence/` changed. The report files are read by no test.
The clone copy's gate and its five skips.

**Could not.** A real `git clone` (I used a tracked-file copy plus `git init`, not `git clone`); a
Linux/macOS clone; an audit of all 800 tests for clone-safety beyond the skip census and the
`evidence/cost/` checks; and anything at all about the cost criterion, which is out of scope. The two
documentation writes that happened after the gate (`RECORD-CORRECTION-REPORT.md`'s final C-3 label and
this report) are named here so the ordering is not implied to be something it is not: neither is a gate
input.

## 5. The one thing for the next batch

**Cost.** R-A3 is the only unmet goal criterion and this batch neither touched nor measured it: 2.549x to
2.604x the 1,500,000-token per-call target, every call ended by `agent.step_limit: 150`, the tripwire
never firing. It needs a human decision, not another record correction. The secondary consequence of this
batch is that the totals can no longer drift silently: any future edit under `evidence/` must update
`evidence/README.md`'s stated totals in the same change, or
`tests/evidence_reproduction.rs` will fail the gate.
