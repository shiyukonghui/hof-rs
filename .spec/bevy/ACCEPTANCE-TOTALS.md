```json
{
 "schema": "hof-rs / bevy independent acceptance of the totals/hash/liveness correction batch (.spec/bevy/TOTALS-CORRECTION-REPORT.md) against defects RD-1, RD-2 and RD-3 of .spec/bevy/ACCEPTANCE-RECORD.md",
 "produced_at": "2026-10-06",
 "branch": "bevy-core",
 "head_under_acceptance": "92870a75ebd3344c3ad513d75043f3ed10eaf52e (`docs(totals): reconcile the evidence directory totals with the measurement and guard the record against the same drift`); `git status --porcelain` was empty at that HEAD before, during and after every check below, and at revision 05cff35 the batch's base",
 "offline": true,
 "what_this_acceptance_did_not_do": "No engine, no game, no network, no model call, no round and no Developer call was run. Nothing was written under `runs/**`. No `git checkout --` and no `rm -rf` was used anywhere; nothing was deleted. No key was created, copied or printed. Nothing was committed, staged or pushed. No path was built from an unexpanded variable. No file of the repository was tampered with, and no existing file was modified: the only thing written inside the repository is this report. All helper scripts live under `F:/hof-acc12-work/`, all logs under `F:/hof-acc12-logs/`, the gate build under `D:/hof-acc12-target/`.",
 "verdict": "pass",
 "headline": "The three defects are fixed, and I re-derived every corrected value from the committed artefacts rather than from the batch's report: `git ls-tree -r -l HEAD evidence` gives 122 files / 4,798,968 bytes, the four excluded files are 15,570 + 4,073 + 4,731 + 3,455 = 27,829 bytes, and the corpus is 118 files / 4,771,139 bytes; every live statement of those three numbers in the tree now agrees, and the old 4,798,249 / 27,110 survive only in the two acceptance records, in the batch's own old->new table and in the appended DECISIONS D308, which is exactly where the same 4,798,249 was independently true at 71dcebd. Blob afde67da really hashes to cebea19e (RD-2), the two places that pinned CLONE-AND-LIVE-REPORT.md at 889033a5 were correctly moved to its post-edit 7c09a7ad with the old value preserved beside them, and the other pins (eb88286c, 6ea1090b, b2053ad1/64a69937) hold. The liveness correction replaced twelve semantic sites and left only three lines / four occurrences of the old wording, every one of them quoted and labelled falsified; the previous acceptance's claim of 13 is not reproducible from its own command (5 lines / 6 occurrences), so the batch's dispute is correct. The diff is six documents and nothing else - no code, no registry, no battery, no liveness step, no .gitattributes line, no index.json, no test. The gate reproduces on this exact HEAD: `cargo test --offline` literal exit code 0, 800 passed / 0 failed / 6 ignored over 60 `test result:` lines, 806 listed, 6 ignored, `cargo fmt --all --check` exit 0 with 0 bytes, 0 warnings, 0 tests removed. The working tree is clean, the tracked tree is 322 files of harness plus this engine's evidence and flow, `git ls-files runs` is empty, no key-shaped material is browsable, and origin/bevy-core is still 5f526d2, so nothing is pushed. The batch's own closing risk is real and I reproduced it: the directory totals are hand-stated and guarded by no test, so one byte added to a non-corpus file under evidence/ falsifies them while the gate stays green. That is a risk, not a defect of this correction. The cost criterion still fails at 2.600x / 2.549x / 2.604x the 1,500,000-token target with agent.step_limit: 150 binding and the tripwire never firing, and it is recorded honestly. Four of the goal's five criteria pass; the fifth is recorded as unmet rather than fixed. **The branch is fit for a push on that basis.**",
 "criteria": [
  {
   "id": "A1-rd1-totals",
   "pass": true,
   "evidence": "Measured by me, not adopted from any document. `git ls-tree -r -l HEAD evidence | awk '{n++; s+=$4} END {print n, s}'` -> `122 4798968`; `git cat-file -s HEAD:<path>` for the four excluded files -> index.json 15570, README.md 4073, tools/build_evidence.py 4731, tools/keyscan.py 3455, sum 27829; a Python walk of the working tree gives the same 122 / 4798968 and 118 / 4771139, and `git ls-tree -r -l HEAD evidence` and the working-tree walk agree byte for byte. At 71dcebd the same command gives 122 / 4798249 (index.json was 14851), so the old figure was true when the records that carry it were written; at 05cff35, the batch's base, it was already 122 / 4798968, so the batch's edits inside evidence/ are byte-length-preserving as it claims. Every statement carrying any of these numbers was enumerated by normalising the digits of every numeric token in all 322 tracked files: the live documents (evidence/README.md:25,30; evidence/index.json's corpus block; tests/evidence_reproduction.rs:8; .spec/bevy/CLONE-AND-LIVE-REPORT.md:154,1695-1696; .spec/bevy/COVERAGE-EVIDENCE-REPORT.md:570,623,626,758,769; DECISIONS.md:11604,11628,11633,11648) all state 4,798,968 / 27,829 / 4,771,139 and nothing else. The old 4,798,249 / 27,110 remain only in .spec/bevy/ACCEPTANCE-CLONE-LIVE.md (14,19,34,167,170) and .spec/bevy/ACCEPTANCE-RECORD.md (10,52,53,138) - acceptance records of measurements that were true when taken, with ACCEPTANCE-RECORD.md stating them as the RD-1 defect description - in TOTALS-CORRECTION-REPORT.md as labelled old->new pairs and as `stale_directory_total`/`stale_excluded_total`, and in DECISIONS.md:11654,11662 inside D308, where they are named as the values being replaced. No file states an old total as a current one."
  },
  {
   "id": "A2-rd2-hash",
   "pass": true,
   "evidence": "`git cat-file -t afde67da` -> blob; `git cat-file -p afde67da | sha256sum` -> cebea19e0f955369a3a7fc8012f785c3f2d8939cde43208e5f7052af98f1d4e3, which is now exactly what .spec/bevy/RECORD-CORRECTION-REPORT.md line 144 pins for that blob. The old value it replaces, 889033a5..., is CLONE-AND-LIVE-REPORT.md's hash: `git show 05cff35:.spec/bevy/CLONE-AND-LIVE-REPORT.md | sha256sum` reproduces it. The consequential fix is real and correct: the RD-1 edit moved that file's hash to 7c09a7ad..., and both places that pinned it were updated - gate_input_sha256['.spec/bevy/CLONE-AND-LIVE-REPORT.md'] (line 46) and the changed_files entry (line 129) - each now carrying 7c09a7ad as the current value and 889033a5 as the superseded one, while `git show HEAD:...CLONE-AND-LIVE-REPORT.md | sha256sum` and `sha256sum` of the working file both give 7c09a7ad, i.e. the pin belongs to the revision it names. The other pins hold: evidence/index.json = eb88286c (unchanged blob 264bb053, identical at f1b9af3 and HEAD), src/adapter/bevy/prd_surfaces.rs = 6ea1090b, and the earlier report's c00716d pin 64a69937 -> b2053ad1 verifies against `git ls-tree -r c00716d`."
  },
  {
   "id": "A3-rd3-liveness",
   "pass": true,
   "evidence": "I re-ran the acceptance's own command on the base revision: `git grep -n -e 'PENDING ITS FIRST REAL OBSERVATION' -e 'has ever been produced' -e 'never executed against a real game' 05cff35 -- .spec/bevy/COVERAGE-EVIDENCE-REPORT.md` -> 5 lines (165, 183, 238, 240, 578) / 6 occurrences, not 13; at HEAD the same command -> 3 lines / 4 occurrences. I then enumerated by meaning, not by those regexes, over the whole old file: the claims that the step had not run or that no raw observation existed sat at 165, 183, 238, 240, 258, 259, 578, the criterion-1 paragraph at 611-613, section 4 at 724/729-730, the workability paragraph at 848, and 'Could not verify' at 864-870 - twelve corrected sites, matching the batch's list. The three remaining occurrences are all quoted history inside corrected sentences, each labelled ('The earlier wording here ... is falsified by that round'); the 8-hit grep of the whole tree for never-ran phrases returns no live claim: evidence/index.json's meaning reads 'is implemented and unit/fake-driver tested AND has executed against a real game' and prd_surfaces.rs's RESIDUALS reads 'OBSERVED, no longer pending', and the round's own artefacts exist and are true - the three runs/clonefix1/iter-{1,2,3}/candidate/.hoh/deterministic/raw/e3_process_liveness.json files exist (3220 bytes each) and result.json.prd_coverage.surfaces reads 15 verified / 0 gap / 4 unobservable of 19 in all three. Settled from the files: the acceptance's 13 is not reproducible from its own command (its figure came from no command it states), the batch's '12 sites' is the count of edited sites (eleven distinct prose clusters if the section-4 heading and paragraph are counted together), and its 5 lines / 6 occurrences is exactly what the command returns."
  },
  {
   "id": "A4-no-over-correction",
   "pass": true,
   "evidence": "`git diff --name-only 05cff35 92870a7` is exactly the six files the batch lists: .spec/bevy/CLONE-AND-LIVE-REPORT.md (3+/3-), .spec/bevy/COVERAGE-EVIDENCE-REPORT.md (34+/27-), .spec/bevy/RECORD-CORRECTION-REPORT.md (4+/4-), .spec/bevy/TOTALS-CORRECTION-REPORT.md (334+/0-), DECISIONS.md (20+/1-), evidence/README.md (1+/1-). `git diff --name-only 05cff35 92870a7 -- src tests config .gitattributes Cargo.toml Cargo.lock` is empty, `git diff 05cff35 92870a7 -- src tests | grep -c '^[+-].*#\\[test\\]'` is 0, and evidence/index.json is the same git blob (264bb053) at f1b9af3 and at HEAD, so no registry entry, no battery step, no liveness step, no line-ending pin and no index meaning moved. DECISIONS.md's single deleted line is D306(c), the one in-place correction the dispatcher authorised, and everything else is the appended D308; the four RECORD-CORRECTION-REPORT.md lines are the hash pins RD-1's byte edit made stale. The only pins that moved are the two that name the file RD-1 edited, which is the minimum RD-2-consistent change, and the batch disclosed going one line beyond the literal instruction."
  },
  {
   "id": "A5-directory-totals-are-unguarded",
   "pass": true,
   "evidence": "The batch's closing advice is true and I reproduced the mechanism on a copy outside the repository: `git grep -n -e 4798968 -e 4,798,968 -e 27829 -e 27,829 -- tests src scripts` returns nothing, and `git grep -n evidence/README -- tests src scripts` returns nothing, so no test reads the directory total. The one test that walks evidence/ (tests/evidence_reproduction.rs::the_evidence_index_names_committed_files_and_commands, lines 495-543) sums only the corpus: it skips, by name, evidence/index.json and evidence/README.md (parent == evidence/) and build_evidence.py / keyscan.py (by basename), and asserts index['corpus']['files'|'bytes'] plus the group sum against what it counted. I copied evidence/index.json to F:/hof-acc12-work/demo-index/index.json and appended one byte: 15570 -> 15571, so the directory total becomes 4,798,969 while the corpus stays 118 / 4,771,139 and every assertion in that test still passes. So a one-line edit to any non-corpus file under evidence/ falsifies the totals stated in evidence/README.md:30, COVERAGE-EVIDENCE-REPORT.md:570,623,758, CLONE-AND-LIVE-REPORT.md:154,1695 and DECISIONS.md:11628 and the gate stays green. A test could assert it: the same walk already enumerates every file and knows exactly which four it skipped, so summing the skipped bytes and the total and comparing them to a pinned constant (or to the number evidence/README.md states) is a two-line addition. Reported as risk R-A1, not fixed."
  },
  {
   "id": "A6-gate",
   "pass": true,
   "evidence": "Free disk checked before building: F: 47 G free, D: 180 G free, so nothing needed deleting and nothing was deleted; `tasklist` found no cargo/rustc/hoh process before I started and I ran one test command at a time, in my own `CARGO_TARGET_DIR=D:/hof-acc12-target` (measured 9.1 G afterwards; D: 171 G free). On the frozen tree at 92870a7: `cargo test --offline` -> literal exit code **0**, **800 passed / 0 failed / 6 ignored** over 60 `test result:` lines; `cargo test --offline -- --list` -> exit 0 with **806** names; `cargo test --offline -- --list --ignored` -> exit 0 with **6** names, the same real-engine tests; `cargo fmt --all --check` -> exit 0 with **0 bytes** on stdout and stderr; **0** lines beginning `warning` and **0** lines containing `warning:` in either stream (the five 'warning' matches are test names). No test removed: src/ and tests/ are byte-identical to 05cff35 and 806 equals the stated baseline. The mechanisms are in the list and green, including adapter::bevy::launch::tests::the_ledger_line_is_written_after_the_spawn_and_says_so, adapter::bevy::round::tests::the_identity_fields_are_computed_from_the_facts_not_asserted, adapter::bevy::tests::the_verified_endpoint_carries_the_nonce_and_the_listeners_pid, the_context_fold_shrinks_every_recorded_round_four_developer_call, the_repeated_success_tripwire_fires_on_the_recorded_grind, the_gate_and_the_writer_agree_on_ledger_validity, the 7 a_resume_* tests and 21 adapter::bevy::battery::tests. The batch's own logs exist outside the repository (F:/hof-rd123-logs/, F:/hof-rd123-logs2/): both exits.txt files are all zero and logs2's gate reports the same 800/0/6 over 60 lines, 0 warnings and a 0-byte fmt, so its numbers are reproducible rather than merely asserted."
  },
  {
   "id": "A7-tree-for-a-push",
   "pass": true,
   "evidence": "322 tracked files whose only top-level entries are .gitattributes, .githooks, .gitignore, .spec, Cargo.lock, Cargo.toml, DECISIONS.md, config, evidence, scripts, src, tests; `git ls-files runs` is empty; the frozen documents (PRD.md, REQUIREMENTS.md, DESIGN-OVERVIEW.md, DESIGN-DETAIL.md and both spike reports) are byte-identical across 05cff35..92870a7, and the only batch reports the correction touched are the three the defects named plus its own new report. DECISIONS.md is append-only apart from the one authorised in-place total correction (20 insertions, 1 deletion, and that deletion is D306(c)). No key-shaped material: my own transcription of src/runtime/secrets.rs's rule (KEY_PREFIXES with a token-start boundary and body >= 16, plus the assignment shape with value >= 32) over all 322 tracked files finds 0 findings outside the one declared fixture source, tests/credential_scan.rs. Launch ledger and identity: runs/bevy-clonefix1/launch-ledger.jsonl has 7 lines with 7 distinct nonces, 7 distinct pids and 7 distinct launch images, no line carries answered_nonce or listening_pid, and the penultimate line is verbatim the surviving launch.json identity (nonce ff44b5f7..., pid 57592, identity.verified true, nonce == answered_nonce, spawned == answering == listening). The working tree is clean (`git status --porcelain` empty) at the HEAD whose report this is, so the tree judged is the tree that would be pushed; origin/bevy-core is still 5f526d2 while refs/heads/bevy-core is 92870a7, and I committed, staged and pushed nothing."
  },
  {
   "id": "A8-what-stands-between-the-tree-and-the-goal",
   "pass": true,
   "evidence": "Four of the goal's five criteria pass and the fifth is recorded as unmet rather than fixed, and nothing about that recording is the blocker here. DECIDABILITY: the registry still holds its 19 frozen ids and the two gaps the recorded round could not decide are decided by the persisted iteration-3 observation. REPRODUCIBILITY: `evidence/** -text` is committed (`git check-attr` -> text: unset for evidence/index.json and .spec/bevy/PRD.md), the working tree's evidence/ has 0 CR bytes across 122 files, and evidence_reproduction.rs re-derives the 118-file / 4,771,139-byte corpus inside the green gate (I did not re-clone). COST: FAILS and is honestly recorded - from runs/clonefix1/iter-{1,2,3}/usage.json the Developer calls are 150 calls / 3,900,735, 3,823,313 and 3,905,662 tokens, exit_status LimitsExceeded in all three, i.e. 2.600x / 2.549x / 2.604x the 1,500,000-token target in config/hoh.yaml with agent.step_limit: 150 binding, and result.json.write_failures and issues are [] in all three, so the tripwire never fired. FROZEN CONTRACT: the frozen documents are byte-identical and no key-shaped material is committed. HONEST RECORD: the three defects are corrected against the artefacts, the values I re-derived match, and the residual stale cross-references (R-A2) are disclosed in the batch's own report and superseded by DECISIONS.md D308."
  }
 ],
 "defects": [],
 "risks": [
  {
   "id": "R-A1",
   "risk": "The evidence/directory totals are hand-stated and guarded by no test, exactly as the batch's own closing advice says: a one-line edit under evidence/ to a file outside the corpus changes the directory total while leaving the corpus assertion green, so the same RD-1 class returns on the next index or README edit.",
   "why_it_matters": "This is the second time it has happened. The totals are stated in five files (evidence/README.md:30, COVERAGE-EVIDENCE-REPORT.md:570,623,758, CLONE-AND-LIVE-REPORT.md:154,1695, DECISIONS.md:11628) and no gate reads any of them.",
   "reproduction": "`git grep -n -e 4798968 -e 4,798,968 -e 27829 -e 27,829 -- tests src scripts` -> nothing. Copy evidence/index.json to a location outside the repository, append one byte (15570 -> 15571), and the directory total becomes 4,798,969 while the corpus stays 118 / 4,771,139; tests/evidence_reproduction.rs:495-543 skips index.json by name, so the gate stays green. A test could assert it by summing, in that same walk, the four files it already skips."
  },
  {
   "id": "R-A2",
   "risk": "Several present-tense self-descriptions inside the batch reports are now false because the corrections they describe have been superseded; the batch disclosed the class in its report section 3 and in DECISIONS D308 but deliberately did not rewrite the reports.",
   "why_it_matters": "They are historical records, not live claims, but a reader who takes a batch report's present tense literally is misled. The sharpest one is undisclosed as a line: .spec/bevy/COVERAGE-EVIDENCE-REPORT.md:565 says every claim 'now reads implemented, pending its first real observation - in this report's machine block and prose' and 'That is the state of the committed evidence', which this batch's own RD-3 edit made false for the machine block and prose (the index.json and prd_surfaces.rs clauses were already false before this batch, made so by aee9c92). Others: same file:858-859 'DECISIONS.md is still append-only' (D306(c) was edited in place under authorisation); .spec/bevy/CLONE-AND-LIVE-REPORT.md:1690-1691 'leaves the batch report's own two exactly as that batch wrote them'; .spec/bevy/RECORD-CORRECTION-REPORT.md:173-175 (C-3), :183 (single_most_important_thing_next_batch) and :365-371 (section 6 item 2), all of which say COVERAGE-EVIDENCE-REPORT.md still contradicts itself; and :61's 'cannot move a byte count', which is true of the corpus and was read as covering the directory.",
   "reproduction": "`sed -n '565p;858,859p' .spec/bevy/COVERAGE-EVIDENCE-REPORT.md`; `sed -n '1690,1691p' .spec/bevy/CLONE-AND-LIVE-REPORT.md`; `sed -n '173,175p;183p;365,371p' .spec/bevy/RECORD-CORRECTION-REPORT.md`; compare each with the corrected text at COVERAGE-EVIDENCE-REPORT.md:165,183,238,240,258 and DECISIONS.md D308."
  },
  {
   "id": "R-A3",
   "risk": "The cost criterion remains unmet, now measured three more times: 2.549x-2.604x the 1,500,000-token per-call target, every call ended by the 150-call step limit, the tripwire never firing.",
   "why_it_matters": "It is the one goal criterion that still fails and it is unchanged by this batch; a push carries it forward as recorded-unmet, not as fixed.",
   "reproduction": "`python` over runs/clonefix1/iter-{1,2,3}/usage.json: the Developer rows are 150 / 3,900,735, 150 / 3,823,313 and 150 / 3,905,662, all LimitsExceeded; config/hoh.yaml:14 step_limit: 150, :47 artifact_write_budget_tokens: 1500000."
  },
  {
   "id": "R-A4",
   "risk": "A clone's gate is weaker than this machine's for three recorded-evidence tests that print a reason and return when their gitignored recording is absent, and four of nineteen surfaces remain unobservable by construction (C5, C6, Q-scale, Q-not-required), so 15/19 is the ceiling.",
   "why_it_matters": "Disclosed and unchanged by this batch, but the clone figure must not be read as covering those assertions, and any round scoring below 15/19 has a real gap.",
   "reproduction": "Carried forward from .spec/bevy/ACCEPTANCE-RECORD.md R-2/R-4; I did not re-clone and did not re-run those three tests against an absent recording."
  }
 ],
 "unverified": [
  "A fresh clone at 92870a7. The correction touched no evidence/** file and no .gitattributes rule, the pin reads text: unset, evidence/ has 0 CR bytes, and the corpus assertion is green in this machine's gate; the previous acceptance's own green-pinned / red-control clone experiment is the evidence I rely on, not my own.",
  "A Linux or macOS clone, where core.autocrlf is false by default.",
  "What was physically on disk when the batch's own gate ran under F:/hof-rd123-logs2. I confirmed that log's exit codes (all zero), its 800/0/6 over 60 lines, 0 warning lines and 0-byte fmt, and that every hash it pins holds in the delivered tree, but not the input state at that instant.",
  "Whether the 7th ledger line (pid 39664, nonce 7bf34e0c) corresponds to a further pass: it did not overwrite launch.json and nothing in this correction depends on it.",
  "Byte-level identity of what the round's successful shell writes put on disk.",
  "Whether every number in every batch report other than the three totals and the hashes I checked is still true: I enumerated every statement carrying the total figures and every never-ran statement, not every number in the tree."
 ],
 "fit_for_push": "FIT for a push, with the cost criterion recorded as unmet rather than fixed. The three defects are corrected and independently re-derived (122/4,798,968 directory, 4/27,829 excluded, 118/4,771,139 corpus, blob afde67da = cebea19e, 7c09a7ad for the file RD-1 moved, 12 liveness sites with the old wording kept only as labelled history), nothing was over-corrected, the gate reproduces green on the exact clean HEAD, no key-shaped material is browsable, and nothing is pushed. The two things a next batch should own are stated as risks rather than blockers: the hand-stated, untested directory totals (R-A1, with a reproduction), and the stale present-tense cross-references inside batch reports (R-A2, disclosed and superseded by D308)."
}
```

# ACCEPTANCE-TOTALS - independent acceptance of the totals/hash/liveness correction

Independent, **offline** acceptance of the batch delivered as
`.spec/bevy/TOTALS-CORRECTION-REPORT.md`, judged at **`bevy-core` / `92870a7`** against defects
**RD-1 / RD-2 / RD-3** of `.spec/bevy/ACCEPTANCE-RECORD.md`. No engine, no game, no network, no model
call, no round and no Developer call was run. Nothing was written under `runs/**`; no `git checkout --`;
no `rm -rf`; nothing deleted; no commit, stage or push; no existing repository file was modified. Helper
scripts are under `F:/hof-acc12-work/`, logs under `F:/hof-acc12-logs/`, the build under
`D:/hof-acc12-target/` - all outside the repository. The machine-readable verdict is the JSON block
above: it is `json.dumps(..., indent=1, ensure_ascii=False)` output written by
`F:/hof-acc12-work/gen_acceptance.py` and then **parsed back out of this written file**, and that parse is
the last thing the generator does.

## 0. The verdict in one paragraph

**The three defects are fixed, and every corrected value is one I re-derived from the artefacts.**
`git ls-tree -r -l HEAD evidence` gives **122 files / 4,798,968 bytes**; the four excluded files
(index.json 15,570 + README.md 4,073 + tools/build_evidence.py 4,731 + tools/keyscan.py 3,455) total
**27,829**; the corpus is **118 files / 4,771,139 bytes**. The 4,798,249 / 27,110 that the previous
acceptance found are gone from every live document and survive only as measurement history, and I
confirmed the old figure was independently true at `71dcebd`. Blob `afde67da` really hashes to
`cebea19e`, and the RD-1 byte edit really did move `CLONE-AND-LIVE-REPORT.md`'s hash from `889033a5` to
`7c09a7ad`, which both pins that named it now state with the old value kept beside it. The liveness
correction replaced **twelve** semantic sites and left **three lines / four occurrences**, every one quoted
and labelled falsified; the previous acceptance's **13 is not reproducible from its own command** (which
returns **5 lines / 6 occurrences**), so the batch's dispute is right. The diff is **six documents and
nothing else**. The gate on this exact HEAD is green: **exit 0, 800 passed / 0 failed / 6 ignored / 806
listed**, `fmt` exit 0 with 0 bytes, **0 warnings**, no test removed. The worker's own closing risk is real
and I reproduced it: the directory totals are hand-stated and no test guards them, so one byte added to a
non-corpus file under `evidence/` falsifies them and the gate stays green - recorded as **R-A1**, not fixed.
The cost criterion still fails at **2.600x / 2.549x / 2.604x** with `agent.step_limit: 150` binding and the
tripwire never firing, recorded honestly. **Fit for a push on that basis.**

## 1. Per-item results

| # | item | result | the evidence I gathered myself |
|---|---|---|---|
| 1 | RD-1, the totals | **pass** | `git ls-tree -r -l HEAD evidence | awk '{n++; s+=$4} END {print n, s}'` -> `122 4798968`; excluded 15,570 + 4,073 + 4,731 + 3,455 = **27,829**; a Python walk of the working tree agrees and gives the corpus **118 / 4,771,139**. Every numeric token in all 322 tracked files was normalised and matched against the three figures: the live documents state only the new values, and the old ones survive only in the two acceptance records, the batch's labelled old->new pairs and D308. At `71dcebd` the directory really was 122 / 4,798,249. |
| 2 | RD-2, the hash | **pass** | `git cat-file -p afde67da | sha256sum` -> `cebea19e...`, now on line 144. `889033a5` is `CLONE-AND-LIVE-REPORT.md` at `f1b9af3`; RD-1 moved it to `7c09a7ad`, and lines 46-47 and 129 were updated to the new value with the old preserved. `eb88286c`, `6ea1090b` and the earlier `64a69937 -> b2053ad1` pin all verify. |
| 3 | RD-3, the liveness statements | **pass** | The acceptance's command returns **5 lines / 6 occurrences** on the base revision, not 13; HEAD has **3 lines / 4 occurrences**, all quoted history inside corrected sentences. By meaning I count **12 corrected sites** (eleven prose clusters plus the section-4 heading). The round's three raw files exist and `result.json` reads 15 / 0 gap / 4 unobservable of 19 in all three iterations. |
| 4 | no over-correction | **pass** | Six files, all documents; `src`, `tests`, `config`, `.gitattributes`, `Cargo.lock`, `evidence/index.json` and `runs/**` untouched; 0 `#[test]` lines changed; DECISIONS.md is D308 plus the one authorised in-place D306(c) line; the only moved pins are the two that name the file RD-1 edited. |
| 5 | the unguarded totals | **pass, with R-A1** | No test references 4,798,968 or 27,829 (`git grep` over tests/src/scripts is empty), and the one walk over `evidence/` asserts only the corpus. I appended one byte to a copy of `index.json` outside the repository: the directory total becomes 4,798,969, the corpus is unchanged, and the gate would stay green. |
| 6 | reproduce the gate | **pass** | Free disk first (F: 47 G, D: 180 G; nothing deleted), own `D:/hof-acc12-target` (9.1 G), no second test process. `cargo test --offline` **exit 0**, **800/0/6** over 60 lines, **806** listed, 6 ignored, `cargo fmt --all --check` **exit 0** / 0 bytes, **0 warning lines**, 0 tests removed. The batch's own logs (F:/hof-rd123-logs2) agree. |
| 7 | the tree as a whole | **pass** | 322 tracked files, harness plus `.spec` plus `evidence` only; `git ls-files runs` empty; frozen docs byte-identical; 7 ledger lines with 7 distinct nonces/pids/images and the penultimate line verbatim the surviving `launch.json` identity; 0 key-shaped findings outside the declared fixture; clean tree; `origin/bevy-core` still `5f526d2`; nothing pushed by me. |
| 8 | what stands between tree and goal | **pass with the cost criterion unmet** | Decidability, reproducibility and the frozen contract pass; cost fails at 2.600x / 2.549x / 2.604x with `step_limit: 150` binding and `write_failures: []`, recorded honestly; the honest record passes on the three corrected defects with the residuals disclosed as R-A2. |

## 2. Counterexamples I looked for

* **A stale number in a live document.** Not found. I did not trust the batch's `left_as_history` list: I
  normalised the digits of every numeric token in all 322 tracked files and classified every hit. The old
  directory total appears nowhere as a current value.
* **A statement whose history reading is itself false.** Not found: at `71dcebd` the directory really was
  122 / 4,798,249, so leaving the old figure in the acceptance records is history, not an error.
* **A pin left on the old hash after RD-1 moved it.** Not found: `889033a5` survives only as the labelled
  superseded value; the operational pins read `7c09a7ad`, which is what both `git show HEAD:...` and the
  working file hash to.
* **A never-ran claim still live.** Not found. Every remaining occurrence of the three strings is inside a
  corrected sentence that names it as the earlier, falsified wording; `index.json` and `prd_surfaces.rs` both
  now say the step has executed.
* **An edit that moved a measured object.** Not found: the working tree and `HEAD` agree on 122 / 4,798,968,
  and the same total already held at the batch's base `05cff35`, so the edits inside `evidence/` are
  byte-length-preserving.
* **Over-correction hiding in the diff.** Not found: the six changed files are the ones the three defects
  name plus the batch's own report, and no code, registry, battery, liveness step or line-ending pin moved.
* **A key in the tracked tree.** Not found: 0 findings under my transcription of the shape rule outside the
  one declared fixture source.
* **A gate run on a moving tree.** Not found this time: `git status --porcelain` was empty before, during and
  after the gate, at `92870a7`, and the log-redirect files live outside the repository.

## 3. What I could not establish

See `unverified` in the JSON block: no fresh clone of my own, no Linux/macOS clone, no attestation of the
disk state at the instant the batch's own gate ran, the unexplained 7th ledger line, the byte-level identity
of the round's shell writes, and the general statement that no number in the tree other than the ones this
correction could have moved is stale.

## 4. Fit for a push

**Fit, with the cost criterion recorded as unmet rather than fixed.** The correction is what authorised it to
be: three mechanical record defects, each re-derived from the artefact here, nothing else in the diff, and a
green gate on the exact clean HEAD that would be pushed. The two things the next batch should own are named as
risks, not blockers - **R-A1** (the hand-stated directory totals, guarded by no test, with a reproduction)
and **R-A2** (the stale present-tense cross-references inside batch reports, disclosed in the batch's own
report and in D308). The cost criterion remains the one goal criterion that fails, and the record says so.
