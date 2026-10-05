```json
{
 "schema": "hof-rs / bevy independent acceptance of the DEFFRAGILISE batch - the removal of the fragile-citation class from .spec/bevy/EFD1-REPORT.md, judged on the working tree of bevy-core at c3f6f94 plus one uncommitted documents-only revision of the batch's own report; every citation re-derived from the files, the gate reproduced in my own build directory, no code/test/evidence/config/measured figure in the diff",
 "verdict": "pass",
 "produced_at": "2026-10-06",
 "branch": "bevy-core",
 "judged_revision": "the working tree of bevy-core: HEAD c3f6f946ac7b62657c29b85dfb448876ce95625a, plus one uncommitted 18-insertion/14-deletion revision of .spec/bevy/DEFFRAGILISE-REPORT.md (sha256 f563614a...). The committed revision carries an earlier revision of that report (sha256 of c3f6f94's blob is 31596 bytes); the delta and its consequence are risks R1 and R3.",
 "head_under_acceptance": "c3f6f946ac7b62657c29b85dfb448876ce95625a (`docs(citations): replace line numbers that drift with identifiers and quoted fragments`)",
 "origin_bevy_core": "166212f1fc4f2e520170e19b894b28501a58235d - 9 commits unpushed, nothing pushed by me",
 "offline": true,
 "summary": "The fragile class is genuinely gone from the report it was aimed at, and every citation either batch touched re-derives from the files. The cell ACCEPTANCE-EFD1.md failed the previous batch on now names the D entries and their fields - `D311 (its trigger and option 3) and D312 (its trigger and option 3 ...)` - and I re-derived the ownership myself: `git grep -n why_they_cannot_be_made_clone_safe -- DECISIONS.md` returns exactly 11712 and 11716 inside D311's block (heading at 11709) and 11731 and 11735 inside D312's block (heading at 11728), with 11712/11731 the Trigger lines and 11716/11735 option 3. Every `HEAD`-relative citation in EFD1-REPORT.md now names both pinned revisions (91629f4 -> 6b66da6): the two numstat fields are `3 3` and `18 0` under that exact range, the restricted-path diff is empty, `HEAD:` became `91629f4:`, `hash_test_attribute_lines_head` became `hash_test_attribute_lines_head_at_start` (668 at 91629f4, 6b66da6, 263d6f9 and in the worktree), and the occurrence counts are scoped by a `measured_against` field whose numbers I re-derived at all four revisions. The de-fragilisation kept the numbers it argued were load-bearing (HARDENING-REPORT.md line 156 and its sha256 2893d496..., FINAL-DOC-REPORT.md's `clone_safety_sighting.where` line 185 and `change_site` line 195, FD1-REPORT.md's corrected lines 14/139/240, ACCEPTANCE-FD1.md's pin line) and I verified every one of those still resolves: line 185 is the only line of FINAL-DOC-REPORT.md carrying the key name, line 195 is the `change_site` value that does not, HARDENING-REPORT.md:156 is the key's own definition, and FD1-REPORT.md is 258 lines at 91629f4 and now with a line-neutral `3 3` diff. Nothing load-bearing was dropped: the report diff is 19/19 on unchanged line count (259), the pinned bytes are untouched (HARDENING-REPORT.md bd373b30... and its line 156 2893d496..., FINAL-DOC-REPORT.md 19251477..., all six frozen documents byte-identical from 4a85269 to the worktree), and the batch's diff is three document paths. No over-reach: `git diff --name-status 263d6f9 c3f6f94` is exactly A .spec/bevy/DEFFRAGILISE-REPORT.md, M .spec/bevy/EFD1-REPORT.md, M DECISIONS.md, and the restricted-path diff against src/tests/config/.gitattributes/Cargo.*/evidence/scripts/.githooks is empty. The gate reproduces in my own fresh D:/hof-defragacc-target (169 Compiling lines, Finished in 1m 19s): cargo test --offline LITERAL exit 0, 800 passed / 0 failed / 6 ignored over 60 test result lines, 806 listed, 6 listed ignored, cargo fmt --all --check literal exit 0 with 0 bytes on both streams, 0 warning: lines in either test stream, 0 FAILED, 0 panic, 668 #[test] lines with src/ and tests/ untouched by this batch. The tree is otherwise fit for a push: 332 tracked files = harness + this engine's evidence/flow (evidence 122, src 72, tests 81, .spec only bevy, config 1), the round-4 ledger is 7 lines / 7 nonces / 7 pids / 7 images with the penultimate line equal to launch.json's identity (47624 = spawned = listening = answering, nonce faf2adda, verified true), the identity/tripwire/fold/resume(7)/battery(21) tests are all in the 806 and green, the evidence totals re-derive exactly (118 / 4,771,139 corpus, 4 / 27,829 excluded, 122 / 4,798,968 directory, 0 CR), no key-shaped material is trackable beyond the declared tests/credential_scan.rs fixture in 332 files, the two known key-shaped files live only under gitignored runs/, and origin/bevy-core is still 166212f. The one thing a pusher must handle is that the working tree is NOT clean: one documents-only revision of the batch's own report is uncommitted, and the report now discloses that in its own `commit_state` field - recorded as risk R1. Cost remains unmet at about two and a half times the target and is recorded as unmet rather than fixed.",
 "criteria": [
  {
   "id": "efd2-1-cell-true-and-non-fragile",
   "pass": true,
   "evidence": "The row the previous acceptance failed (EFD1-REPORT.md section 1's `DECISIONS.md` row) now reads `D311 (its trigger and option 3) and D312 (its trigger and option 3 - the entry that corrects D311): the false claim and its labelled correction, not reference points`. I re-derived it from the file, not from either batch: my own `grep -n why_they_cannot_be_made_clone_safe DECISIONS.md` returns exactly 11712, 11716, 11731, 11735; reading the `## D` headings gives D311 at 11709 and D312 at 11728, so two occurrences are D311's and two are D312's; the four lines are D311's Trigger and its `3. **同时...` option and D312's Trigger and its `3. **因此改掉...` option. The removed cell (verbatim in the 263d6f9 blob, `git diff 263d6f9 c3f6f94` shows it) said `D311 line 11716, D312 lines 11712/11716`, which attributed D311's lines to D312 and omitted D312's real ones. The count of 4 is unchanged, D313's block (heading 11746) deliberately does not spell the key name (grep confirms DECISIONS.md still has exactly 4), and the cell no longer contains a number that can drift."
  },
  {
   "id": "numstat-and-revision-anchors-re-derive",
   "pass": true,
   "evidence": "I re-ran every command the batch's citations_changed names. `git diff --numstat 91629f4 6b66da6 -- .spec/bevy/FD1-REPORT.md` -> `3 3`; for DECISIONS.md -> `18 0`; `git diff --name-only 91629f4 6b66da6` restricted to src tests config .gitattributes Cargo.toml Cargo.lock evidence scripts .githooks -> empty; `git diff --name-status 91629f4 6b66da6` -> A EFD1-REPORT.md, M FD1-REPORT.md, M DECISIONS.md. DECISIONS.md's blob is 1,342,560 bytes / sha256 31014e76... at 91629f4 and 1,347,590 / e6e136ef... at 6b66da6, +5,030, and I confirmed by bytes that the 91629f4 blob is a prefix of the 6b66da6 blob and of the file now (1,353,845 / 765f2a8b...); the same prefix property holds 6b66da6 -> 263d6f9 -> worktree. EFD1-REPORT.md's own `batch_committed_as` field names 6b66da67b4a95fe77330b791aebfbb4d6a02a53f (git rev-parse agrees) and its `starting_tree` names (head_at_start 91629f4) / (batch_committed_as 6b66da6). The old fragments (why_option_A, RF-3_field_title, section 2) are provably in `git show 91629f4:.spec/bevy/FD1-REPORT.md` and absent from the worktree; the three new fragments are present at FD1-REPORT.md lines 14, 139 and 240. `hash_test_attribute_lines_head_at_start` = 668 and 668 at 91629f4, 6b66da6, 263d6f9 and in the worktree. `git grep -c why_they_cannot_be_made_clone_safe` at 91629f4 gives exactly the batch's six files (FINAL-DOC-REPORT.md 1, ACCEPTANCE-FINAL-DOC.md 6, ACCEPTANCE-FD1.md 7, FD1-REPORT.md 8, HARDENING-REPORT.md 1, DECISIONS.md 2) and no EFD1-REPORT.md; at 6b66da6 it adds EFD1-REPORT.md 9 and DECISIONS.md 4; at 263d6f9 it also adds ACCEPTANCE-EFD1.md 4. No value needed correcting."
  },
  {
   "id": "kept-numbers-still-resolve",
   "pass": true,
   "evidence": "Every number the batch chose to keep resolves. FINAL-DOC-REPORT.md:185 is `clone_safety_sentence.where` and is the only line of that file carrying the key name; line 195 is `\"change_site\": \"HARDENING-REPORT.md machine line 156, section 0 and section 3\"` and contains no such name; line 329 carries `The alternative's cost is now stated at all three`. HARDENING-REPORT.md:156 is the `why_they_cannot_be_made_clone_safe` field itself and is the only line carrying the name; its sha256 over the line plus newline is 2893d496152e475fa886b200fbb9bff8068f4dcfd0c6b25a68123d1bb1cecd6d, exactly the value FD1-REPORT.md's `line_156_sha256.worktree_after` and ACCEPTANCE-FD1.md line 20 record, and the file hashes to bd373b30... at 91629f4, 6b66da6, 263d6f9 and in the worktree (bcb77c4d... at 4a85269, before the FD-1 repair). FD1-REPORT.md is 258 lines at 91629f4 and in the worktree with numstat 3 3. ACCEPTANCE-FD1.md line 20 records the same line-156 sha256 and that file has 7 occurrences of the key name. So the report's `why_the_number_stays` reasons are true of the bytes, and it kept a number only where a recorded hash is taken over that exact line or a field name travels with it."
  },
  {
   "id": "residual-fragility-scanned-and-reported",
   "pass": true,
   "evidence": "I searched the batch's documents for the two shapes it was chartered to remove. In EFD1-REPORT.md there is now no `HEAD` token at all and no line number into DECISIONS.md (grep for HEAD returns nothing; the only DECISIONS.md references are D-entry names, plus the quoted value of FINAL-DOC-REPORT.md's `change_site` which is data). In the working-tree DEFFRAGILISE-REPORT.md the earlier `numstat_worktree_vs_HEAD` field names are now `numstat_worktree_vs_263d6f9` and the two `the current HEAD` phrases are gone (`263d6f9` and `the batch's head_at_start` instead); the remaining `HEAD` tokens are quotations of the removed text and the explanation of the previous batch's RF-3. One residual of the class is outside the batch's target and unlisted by it: FD1-REPORT.md line 227 (and its JSON key `D309_line_11686`) cites DECISIONS.md by line number, and section 2 asserts the class `cannot arise` from the numbers that remain - an under-report, recorded as R2. I verified that citation is currently accurate: DECISIONS.md line 11686 is D309's `预期影响与回滚点` line and it carries `两处（gate.gate_input_sha256 与 changed_files）已更新为新值`; D309's block is bounded by its heading at 11670 and D310's heading at 11688. So it does not mislead today, and DECISIONS.md's append-only property (verified by the prefix check at every step) means it cannot drift without an insertion."
  },
  {
   "id": "nothing-load-bearing-lost-and-pins-intact",
   "pass": true,
   "evidence": "The repair to EFD1-REPORT.md is line-for-line: 259 lines at 6b66da6 and now, numstat `19 19` against 263d6f9, every change a replacement on an existing line, and I read the whole diff - it replaces one table cell, two `numstat_vs_HEAD` field names, one `HEAD:` fragment path, one field name, several `at HEAD` phrases, the starting/delivered-tree sentence, the diff sentence and the line-numbers-unchanged sentence, and adds `batch_committed_as`, `de_fragilised` and `measured_against` on existing lines. No citation a reader needs was dropped: the three FD1-REPORT.md places, the FINAL-DOC-REPORT.md fields, HARDENING-REPORT.md's line and its sha256, ACCEPTANCE-FD1.md's pin and the occurrence counts all survive, and the ones that kept a number are explained in a dedicated `citations_kept_with_a_number` block (five cases). The bytes the batch was forbidden to edit are unchanged: HARDENING-REPORT.md (whole file bd373b30..., line 156 2893d496...) and FINAL-DOC-REPORT.md (19251477...) are byte-identical at 91629f4, 6b66da6, 263d6f9 and in the worktree; the six frozen documents (REQUIREMENTS.md, PRD.md, DESIGN-OVERVIEW.md, DESIGN-DETAIL.md, SPIKE-1-REPORT.md, SPIKE-2-REPORT.md) are byte-identical at 4a85269, 91629f4, 6b66da6, 263d6f9, c3f6f94 and in the worktree; no document pinned by a recorded hash was edited (the whole batch diff is three documents, none of them pinned)."
  },
  {
   "id": "no-over-reach",
   "pass": true,
   "evidence": "`git diff --name-status 263d6f9 c3f6f94` is exactly `A .spec/bevy/DEFFRAGILISE-REPORT.md`, `M .spec/bevy/EFD1-REPORT.md`, `M DECISIONS.md`, numstat 379/0, 19/19, 21/0. `git diff --name-only 263d6f9 c3f6f94 -- src tests config .gitattributes Cargo.toml Cargo.lock evidence scripts .githooks` is empty. Worktree against the batch's base `263d6f9` is the same three paths (383/0, 19/19, 21/0). Nothing under runs/** is tracked (`git ls-files runs` empty) and no measured figure moved: the evidence totals still re-derive as 118 / 4,771,139, 4 / 27,829 and 122 / 4,798,968 with 0 CR bytes, and the diff touches no file that states them. The batch's own report claims no source, test, registry, battery, liveness, .gitattributes, config or cost file is in the diff, and the diff says the same."
  },
  {
   "id": "gate-reproduced",
   "pass": true,
   "evidence": "Free disk was checked first (F: 37 GiB, D: 91 GiB) and was sufficient, so nothing was deleted. I waited for zero cargo/rustc processes before starting and ran one test process at a time in my own fresh `D:/hof-defragacc-target` (it did not exist before the run; 169 `Compiling` lines, `Finished \\`test\\` profile [unoptimized + debuginfo] target(s) in 1m 19s`; 9.1 GiB afterwards). Literal exit codes read from files written by my own script: `cargo test --offline` -> 0; `cargo test --offline -- --list` -> 0; `-- --list --ignored` -> 0; `cargo fmt --all --check` -> 0 with 0 bytes on stdout and stderr. Counts: 800 passed / 0 failed / 6 ignored over 60 `test result:` lines, every line `0 failed`; 806 listed names ending `: test`, 6 of them ignored; 0 `warning:` lines in the test stdout or stderr (the only stderr lines are Compiling/Finished/Running/Doc-tests), 0 FAILED lines, 0 panics. No test removed: `^\\s*#\\[test\\]` lines over `git ls-files src tests` are 668 here and 668 at 91629f4, 6b66da6, 263d6f9, and `git diff --name-only 91629f4 c3f6f94` touches no file under src/ or tests/. Identical to the 800/0/6/806 baseline."
  },
  {
   "id": "tree-for-push",
   "pass": true,
   "evidence": "Composition: 332 tracked files = 1 .gitattributes + 3 .githooks + 1 .gitignore + 46 .spec (all .spec/bevy) + 1 Cargo.lock + 1 Cargo.toml + 1 DECISIONS.md + 1 config + 122 evidence + 2 scripts + 72 src + 81 tests - the harness plus this engine's evidence and flow, nothing else. Ledger/identity: my own parse of evidence/observation/round4/round/launch-ledger.jsonl gives 7 lines, 7 distinct nonces, 7 distinct pids, 7 distinct launch images, no `answered_nonce` and no `listening_pid` key; the penultimate line (nonce faf2adda-c698-48ef-a4f5-f51d1da551c6, pid 47624, image `runs\\\\bevy-round4\\\\launch-image\\\\8d228a52-...\\\\hof_game.exe`, endpoint http://127.0.0.1:15702/) is exactly launch.json's identity block (spawned_pid = listening_pid = answering_pid = 47624, same image, same endpoint, `verified: true`). Mechanism tests in the 806 and green in my gate: `adapter::bevy::round::tests::the_identity_fields_are_computed_from_the_facts_not_asserted` (1), `the_repeated_success_tripwire_fires_on_the_recorded_grind` (1), 24 `harness::guard::tests`, `the_context_fold_shrinks_every_recorded_round_four_developer_call` (1), 7 `a_resume_*`, 21 `adapter::bevy::battery::tests`, `no_key_shaped_material_is_browsable_in_the_repository_tree` (1). Key-shaped material: my own scan of all 332 tracked files with the rule's ten prefixes (16-char body, token-boundary) and the assignment shapes finds the `sk-` shape only in the declared fixture `tests/credential_scan.rs`; the two known key-shaped files - `runs/round1/iter-1/traj/developer.attempt1.json` (418,684 B) and `runs/round1b/iter-1/traj/tester.attempt1.json` (986,970 B) - exist on disk, are ignore-matched by `.gitignore:9:runs/`, and were not opened or printed. Frozen documents byte-identical (see the pins row). The worktree is clean except for one documents-only revision of the batch's own report, which that report itself discloses in `commit_state` (risk R1); origin/bevy-core is still 166212f with 9 unpushed commits and nothing was pushed by me."
  },
  {
   "id": "record-carries-no-fresh-false-statement",
   "pass": true,
   "evidence": "I re-derived the batch's own machine block instead of reading it. It parses as JSON (17 keys) and its new `commit_state` field is accurate: `git rev-parse c3f6f94` is c3f6f946ac7b62657c29b85dfb448876ce95625a with the subject it quotes, `git show --stat c3f6f94` carries exactly EFD1-REPORT.md, DECISIONS.md and an earlier revision of this report, and `git rev-parse origin/bevy-core` is 166212f1fc4f2e520170e19b894b28501a58235d. Its `changed_files` byte and hash figures re-derive (EFD1-REPORT.md 259 lines, 88814941... before / c49ee8e6... after; DECISIONS.md 1,347,590 / e6e136ef... before and 1,353,845 / 765f2a8b... after, +6,255 bytes on 21 appended lines). Its `line_numbers_in_this_report` claim holds: the only line number it prints is the quoted removed text `D311 line 11716, D312 lines 11712/11716`. Its two `numstat_worktree_vs_263d6f9` values reproduce (`19 19`, `21 0`), its `worktree` statement reproduces (`git diff --name-status 263d6f9` is the three documents), and its `no carriage return in any of the three documents` claim reproduces (0 CR bytes in each of DEFFRAGILISE-REPORT.md, EFD1-REPORT.md and DECISIONS.md). I found no false statement about the product, the tree or the record; the residual imperfections are an unlisted citation in an untouched file, a shelf-life sentence and one cosmetic miscount, all recorded as risks R2-R4."
  },
  {
   "id": "working-tree-state-disclosed",
   "pass": true,
   "evidence": "The working tree is NOT literally clean, and I say so plainly: `git status --porcelain` reports ` M .spec/bevy/DEFFRAGILISE-REPORT.md`, an 18-insertion/14-deletion documents-only revision made at 04:34:09 and 04:39:04, after the dispatcher's 04:28:41 commit c3f6f94. The delivered report itself discloses this in `commit_state` (`The worktree holds one later revision of this report on top of that commit, which renames this report's own two numstat_worktree_vs_HEAD fields to numstat_worktree_vs_263d6f9 and names that commit here`) and in its prose (`nothing staged, committed or pushed by this batch's own work - the dispatcher committed the batch as c3f6f94 while this report was being finalised`), so a reader is told rather than misled. The delta is documents-only and cannot move the gate or any measured figure; it is carried as risk R1 for the pusher. My own report is the second uncommitted file and is expected."
  }
 ],
 "defects": [],
 "risks": [
  {
   "id": "R1",
   "risk": "The working tree is not clean: one documents-only revision of the batch's own report (18 insertions / 14 deletions, sha256 f563614a42e579bbaba79fe4c9b6257ff388a643523c75bbb2bacb0a762a79f2, mtime 04:39:04) sits on top of c3f6f94, whose copy of that report is the earlier 31,596-byte revision. Consequence for the pusher: the committed revision still carries the class in its own report - `numstat_worktree_vs_HEAD` fields (whose `git diff --numstat HEAD --` re-run in a clean tree now prints nothing), the phrases `the current HEAD`, `the gate was run twice ... both runs` (its own `gate.runs` says the gate was run repeatedly), and `nothing staged, committed or pushed` - while the working-tree revision removes all of these and adds `commit_state`. Pushing c3f6f94 without committing the later revision pushes the staler record; committing it makes the tree clean. This is a state for the dispatcher to resolve, not a false statement about the product or the tree, and the delivered file describes it."
  },
  {
   "id": "R2",
   "risk": "Under-report of the residual class: FD1-REPORT.md (untouched, closed) still cites DECISIONS.md by line number - `D309:11686` at line 227, the JSON key `D309_line_11686` in `decisions_on_non_blocking_items`, and ACCEPTANCE-FINAL-DOC.md line 50 - which is exactly the shape `not_changed`/`citations_kept_with_a_number` describe as fragile ('a number is fragile when the document it indexes grows'), but the batch neither changed it nor listed it, and its section 2 concludes `the class ... cannot arise from them`. The citation is currently accurate (DECISIONS.md line 11686 is D309's `预期影响与回滚点` line, which carries `两处（gate.gate_input_sha256 与 changed_files）已更新为新值`, and D309's block spans heading 11670 to D310 at 11688), and DECISIONS.md's append-only property - verified byte-wise at every step - means the number cannot drift without an insertion, so no reader is misled today. It is an incompleteness in the batch's inventory of what it left standing, not a false claim."
  },
  {
   "id": "R3",
   "risk": "Shelf-life statement: the working-tree report's new `commit_state` says `The worktree holds one later revision of this report on top of that commit`. That is true only until the dispatcher commits that revision; afterwards a reader of the committed record finds the worktree clean and the sentence false of it. It is a disclosure of a transient state and the substance around it (which commit carries which files, nothing pushed, which fields were renamed) is verified; recorded so the next batch knows the sentence belongs to the uncommitted state, not to the pushed one."
  },
  {
   "id": "R4",
   "risk": "Cosmetic miscount in the new report's gate note: `the -- --list output contains 4 test NAMES whose text includes the word 'warning'`. The listing has 5 distinct names containing `warning` (`the_resume_warning_states_the_scope_it_applied`, `every_result_json_carries_the_scope_warning`, `reading_harness_sources_is_recorded_as_a_warning`, `a_recursive_hoh_search_is_recorded_as_a_warning`, `enumerating_the_harness_root_is_recorded_as_a_warning`); 4 lines contain the substring `warning:` and 4 is what a naive `grep -c 'warning:'` returns, which is the number the note exists to explain. The gate's real warning count is 0, so no reader's understanding of the gate changes."
  },
  {
   "id": "R5",
   "risk": "The cost criterion remains unmet and is recorded as unmet rather than fixed: 2.600x / 2.549x / 2.604x of the 1,500,000-token per-Developer-call target, every call ended by `agent.step_limit: 150` with the repeated-success tripwire never firing. It is the one goal criterion that fails and it needs a human decision, not another document correction. No round, engine, game, network or model call was run or attempted by this acceptance, so the figures are adopted from the recorded usage numbers, not re-measured."
  },
  {
   "id": "R6",
   "risk": "Inherited and unchanged: DECISIONS.md D311 option 3 still carries the false `where`/`change_site` claim verbatim (RF-2 of ACCEPTANCE-EFD1.md), limited by D312 and named by D313, because the log is append-only; and the five clone-weak tests remain clone-weak in a tree without runs/round1b, runs/round2 and runs/round3 (RF-6). Both are disclosed in the records and neither is this batch's to fix."
  },
  {
   "id": "R7",
   "risk": "Inherited, cosmetic, and not a rendering defect: ACCEPTANCE-EFD1.md's machine block contains a literal three-backtick fence marker plus the word json inside its RF-4 text (it describes the two labels as sitting inside the leading fenced block of their report). The JSON itself is valid (13 keys; it parses when the real closing fence is used) and a CommonMark renderer is unaffected because the embedded marker is not at the start of a line, but a naive 'first fence to next fence' extractor cuts the block early and reports invalid JSON. The batch did not touch that file."
  }
 ],
 "unverified": [
  "No engine, game, network, model call, round or Developer call was run or attempted, and nothing was written under runs/**; the cost figures (2.600x / 2.549x / 2.604x, `agent.step_limit: 150`, tripwire never firing), the six recordings' 5,917,632 bytes and every other recorded measurement this acceptance did not re-derive are read from the records, not re-measured.",
  "No real `git clone` and no Linux or macOS checkout: the line-ending question was checked only as byte facts (0 CR in the three batch documents, 0 CR across evidence/'s 122 files) and by `.gitattributes`, which the diff does not touch. Clone-safety of all 800 passing tests was not audited - only the counts (800 / 0 / 6 / 806, 668 `#[test]`) and the named mechanism tests' presence in the listing.",
  "No CommonMark renderer was run over any document; the fence claims above are from byte positions, not from a rendered view.",
  "The two key-shaped files under `runs/**` were not opened or printed and no API key was read or handled; only their existence, sizes and ignore status were checked.",
  "The batch's own historical build and its earlier gate runs (D:/hof-defrag-target, its 169 Compiling run) were not re-run or inspected beyond the diffs; my gate is my own run in D:/hof-defragacc-target. The delivered report was edited twice while this acceptance was running (mtime 04:34:09 and 04:39:04, i.e. after the 04:28:41 commit); I judge the 04:39:04 bytes (sha256 f563614a...), which were also the bytes the gate ran on, and I did not examine the intermediate state except as its git diff.",
  "No tamper or plant experiment was run: none of the checks required modifying a file, so no copy, restore or restamped timestamp exists in this acceptance, and there is no backup whose equality I asserted.",
  "Whether more edits to the batch's report will follow, and whether the dispatcher will commit the uncommitted revision, are outside what I can establish."
 ],
 "what_this_acceptance_did_not_do": "No engine, no game, no network, no model call, no round and no Developer call was run. Nothing was written under runs/**. Nothing was deleted: free disk was sufficient (F: 37 GiB, D: 91 GiB before building) so no space was freed, and no `rm -rf` and no wildcard deletion were used. No path was built from an unexpanded variable; no `git checkout --`; no `git add`, stage, commit or push. Helper scripts live outside the repository under F:/hof-defrag-acc-work/ and logs under F:/hof-defrag-acc-logs/; the build is my own fresh D:/hof-defragacc-target (9.1 GiB). The only file written inside the repository is this report. No API key was created, copied or printed; the two key-shaped run-directory files were reported by path and status only, never printed.",
 "artifact_hashes_at_acceptance": {
  ".spec/bevy/DEFFRAGILISE-REPORT.md": "f563614a42e579bbaba79fe4c9b6257ff388a643523c75bbb2bacb0a762a79f2",
  ".spec/bevy/EFD1-REPORT.md": "c49ee8e6b1a555d3b567a7a0d7f0ff2272fe1f7c92e90c2ec9f204ed2d21b050",
  "DECISIONS.md": "765f2a8b5b80fe356747db8aae6daf66005fe55fd944f594e1ce33d0a4cd1fc8",
  ".spec/bevy/HARDENING-REPORT.md": "bd373b30fcd0da76a264377674962f10ac2ba4c9fa1122631075c47e774c04ac",
  ".spec/bevy/FINAL-DOC-REPORT.md": "192514775105557de8bdc24c5ffb56ebaef85a9abe0228d1da5b942e69b7170b"
 }
}
```


# ACCEPTANCE-DEFFRAGILISE - independent acceptance of the de-fragilisation batch

Independent, **offline** acceptance of the batch delivered as `.spec/bevy/DEFFRAGILISE-REPORT.md`, judged
on the **working tree** of `bevy-core`: `HEAD` `c3f6f94`, plus one uncommitted documents-only revision of
the batch's own report (`origin/bevy-core` is still `166212f`, nine commits unpushed, nothing pushed by
me). No engine, no game, no network, no model call, no round and no Developer call; nothing written under
`runs/**`; nothing deleted (free disk was sufficient, no `rm -rf`, no wildcard); no `git checkout --`; no
path built from an unexpanded variable; no commit, stage or push. Helper scripts live outside the
repository under `F:/hof-defrag-acc-work/`, logs under `F:/hof-defrag-acc-logs/`, my build under
`D:/hof-defragacc-target` (fresh, 169 `Compiling` lines, 1m 19s, 9.1 GiB). The machine-readable verdict
above is `json.dumps(..., indent=1, ensure_ascii=False)` output written by
`F:/hof-defrag-acc-work/gen_report.py`, which then **parsed it back out of the written file** and required
it to round-trip equal. I ran no tamper or plant experiment because none of the checks needed one.

## 0. The verdict in one paragraph

**The fragile class is gone from the report it was aimed at, and the tree is fit for a push - with one
loose end the pusher must handle: the working tree is not clean.** The cell `ACCEPTANCE-EFD1.md` failed
the previous batch on is now an entry-and-field citation - `D311 (its trigger and option 3) and D312 (its
trigger and option 3 ...)` - and I re-derived the ownership myself rather than from either batch: the
key's name occurs in `DECISIONS.md` at exactly 11712, 11716 (inside D311, heading 11709) and 11731,
11735 (inside D312, heading 11728), and those are the Trigger and option-3 lines. Every `HEAD`-relative
citation in `EFD1-REPORT.md` now names both pinned revisions (`91629f4` -> `6b66da6`), and every one of
those commands reproduces: `3 3` and `18 0`, the empty restricted-path diff, the `91629f4:` fragment
path, `668` `#[test]` lines at all four revisions, and the occurrence counts scoped by a
`measured_against` field whose numbers I re-derived at `91629f4`, `6b66da6`, `263d6f9` and in the
worktree. The numbers the batch kept because a recorded hash is taken over the exact line, or because a
field name travels with them, all still resolve; the pinned bytes are untouched; nothing a reader needs
was dropped (the edit is line-for-line, 19/19, 259 -> 259 lines). The diff is three documents and the
restricted-path diff is empty. The gate reproduces in my own build directory: **literal exit 0, 800
passed / 0 failed / 6 ignored over 60 `test result:` lines, 806 listed, 6 ignored, `cargo fmt --all
--check` exit 0 with 0 bytes, 0 `warning:` lines, no test removed** (668 `#[test]` lines, `src/` and
`tests/` untouched by this batch). The tree is otherwise sound: 332 tracked files of harness plus this
engine's evidence and flow, the round-4 ledger's penultimate line equal to `launch.json`'s identity
(47624, nonce `faf2adda`, `verified: true`), the identity, tripwire, fold, resume (7) and battery (21)
tests green in the 806, the evidence totals re-derived exactly, no key-shaped material trackable beyond
the declared fixture, the two known key-shaped files gitignored under `runs/`. **What a pusher must
resolve:** the working tree carries one uncommitted revision of the batch's own report (sha256
`f563614a...`, +18/-14, written after the `c3f6f94` commit), and the committed revision still has that
report's own `HEAD`-relative field names and its "run twice" sentence while the worktree removes both -
recorded as R1, and disclosed by the report itself in `commit_state`. **Cost still fails and is recorded
as unmet at about two and a half times the target.**

## 1. Per-item results

| # | item | result | the evidence I gathered myself |
|---|---|---|---|
| 1 | the cell EFD2-1 named | **pass** | The row now names `D311 (trigger, option 3)` and `D312 (trigger, option 3)`. My `grep -n` returns exactly 11712/11716/11731/11735; the `## D` headings at 11709 (D311) and 11728 (D312) own two each, and the lines are the Trigger and option-3 lines. The old cell `D311 line 11716, D312 lines 11712/11716` is gone; the count 4 is unchanged. |
| 1 | every citation the batch says it changed | **pass** | All eleven re-derived: `3 3`, `18 0`, empty restricted diff, `896...` prefix +5,030, `91629f4:` fragments present and the corrected ones at 14/139/240, 668 `#[test]` at four revisions, the six-file `git grep -c` counts at 91629f4 and their 6b66da6/263d6f9 additions, and `batch_committed_as` = `6b66da67...`. Nothing needed a corrected value. |
| 1 | the numbers the batch kept | **pass** | FINAL-DOC-REPORT.md:185 is the only line carrying the key name and line 195 the `change_site` that does not; HARDENING-REPORT.md:156 is the field itself with the recorded sha256 `2893d496...`; FD1-REPORT.md is 258 lines at both revisions with a line-neutral `3 3`; ACCEPTANCE-FD1.md:20 records the same line hash. |
| 2 | residual fragility | **pass, with R1/R2/R3** | `EFD1-REPORT.md` no longer contains the token `HEAD` or a line number into `DECISIONS.md`. The working-tree report renamed its own `numstat_worktree_vs_HEAD` fields to `numstat_worktree_vs_263d6f9` and dropped the two `the current HEAD` phrases (the committed revision still has them - R1). `FD1-REPORT.md:227`'s `D309:11686` is an unlisted line number into the growing log - accurate today and non-drifting while the log stays append-only - R2. |
| 3 | nothing load-bearing lost | **pass** | The report edit is 19/19 on a 259-line file; I read the whole diff and no citation was dropped. Every kept number is explained in a dedicated block. |
| 3 | the pinned bytes unchanged | **pass** | HARDENING-REPORT.md `bd373b30...` (line 156 `2893d496...`) and FINAL-DOC-REPORT.md `19251477...` byte-identical at 91629f4, 6b66da6, 263d6f9 and in the worktree; the six frozen documents byte-identical from `4a85269` to the worktree. |
| 4 | no over-reach | **pass** | `git diff --name-status 263d6f9 c3f6f94` = A `DEFFRAGILISE-REPORT.md`, M `EFD1-REPORT.md`, M `DECISIONS.md`; the restricted-path diff (src, tests, config, `.gitattributes`, `Cargo.*`, evidence, scripts, `.githooks`) is empty; `git ls-files runs` is empty; no measured figure moved. |
| 5 | the gate | **pass** | Free disk first (F: 37 GiB, D: 91 GiB), nothing deleted; waited for zero cargo/rustc, one test process; own fresh `D:/hof-defragacc-target` (169 `Compiling`, 1m 19s, 9.1 GiB). Literal exit 0 for test / list / list-ignored / fmt; **800 / 0 / 6** over 60 lines, **806** listed, **6** ignored, fmt 0 bytes, 0 `warning:`, no FAILED, no panic; 668 `#[test]` lines. |
| 6 | the tree for a push | **pass, with R1** | 332 tracked files = harness + this engine's evidence/flow; ledger 7/7/7/7 with the penultimate line = `launch.json` identity (47624 = spawned = listening = answering, `verified: true`); identity, tripwire, 24 guard, fold, 7 resume and 21 battery tests in the 806; evidence totals 118/4,771,139, 4/27,829, 122/4,798,968, 0 CR; only the declared `tests/credential_scan.rs` fixture is key-shaped in 332 files, two known key-shaped files gitignored under `runs/`; frozen documents intact; `origin/bevy-core` = 166212f, nothing pushed. **The working tree is not clean** (R1). |
| 6 | the working tree clean | **NOT clean - disclosed** | `git status --porcelain` = ` M .spec/bevy/DEFFRAGILISE-REPORT.md` (+18/-14, applied after the 04:28:41 commit). The file's own `commit_state` and prose say so, so a reader is told; carried as R1 for the pusher. |
| 7 | the record carries no fresh false statement | **pass, with R2/R3/R4** | The block parses (17 keys); `commit_state`'s commit, its three paths and the unpushed `origin` verify; the byte/hash figures, the two `numstat_worktree_vs_263d6f9` values, the "no carriage return" claim and the "only line number is the quotation" claim all reproduce. Residuals are an unlisted citation in an untouched file, a shelf-life sentence and one cosmetic miscount. |

## 2. Counterexamples I looked for, and what I found

* **A citation the batch says it fixed but did not.** Not found. All eleven `citations_changed` entries
  re-derive, and the three `FD1-REPORT.md` fragments are provably present at `91629f4` and absent from
  the worktree.
* **A citation that still cannot be re-derived.** Not found in the two batch documents. Every command
  they quote reproduces on this checkout, because each range and revision is named.
* **A citation dropped that a reader needs.** Not found. The report's diff is 19/19 on an unchanged
  259-line shape, and the five `citations_kept_with_a_number` cases still carry their numbers with the
  reason attached.
* **Pinned bytes edited.** Not found. `HARDENING-REPORT.md` (whole file and line 156) and
  `FINAL-DOC-REPORT.md` hash identically at every revision of interest, and the six frozen documents are
  byte-identical from `4a85269` to the worktree.
* **Over-reach hiding in the diff.** Not found. Three document paths; the restricted-path diff is empty;
  no evidence byte, registry, battery, liveness step, line-ending pin, config or measured figure moved.
* **A second test process or a deleted test.** Not found. I waited for zero cargo/rustc before starting;
  my run is the only test process; 668 `#[test]` lines here and at four revisions; 800 + 6 = 806.
* **A key in the tracked tree.** Not found beyond the declared fixture. My own scan of all 332 tracked
  files matches only `tests/credential_scan.rs`; the two known files are outside the tree and outside the
  push.
* **A fresh false statement in the new record.** Not found. What I found instead are three imperfections
  that do not change a reader's understanding: the unlisted `D309:11686` line number (R2), the
  worktree-revision sentence's shelf life (R3), and the "4 test NAMES" versus 5 names containing
  `warning` (R4 - 4 is the correct naive-grep count, which is what the note explains).
* **The working tree clean.** **FOUND** - one uncommitted documents-only revision of the batch's own
  report. It is disclosed by the report itself, so it is a pusher's decision (R1), not a misleading
  claim.
* **The committed revision judged instead of the worktree.** **FOUND, disclosed** - `c3f6f94` carries an
  earlier revision of the report whose own `HEAD`-relative field names and "run twice" sentence the
  worktree removes. I judge the worktree; R1 states what pushing the commit alone would keep.

## 3. What still stands between this tree and the goal's five criteria

**Decidability** passes: the coverage registry is untouched by this batch, and the committed observation
(not re-run here) still decides the open gaps. **Reproducibility** passes: `.gitattributes` is not in the
diff, the evidence corpus re-derives exactly (118 / 4,771,139; excluded 4 / 27,829; directory
122 / 4,798,968; 0 CR bytes), and the five clone-weak tests remain the disclosed boundary (R6).
**Frozen contract** passes: the six frozen documents are byte-identical from `4a85269` to the worktree,
`PRD.md`'s pin is untouched, and no key-shaped material is trackable. **Honest record** passes: the cell
that failed the previous batch is corrected in a form that cannot drift, every citation re-derives, and
the only residual imperfections are disclosed here. **Cost fails and is expected to remain unmet at about
two and a half times the target** (2.600x / 2.549x / 2.604x of the 1,500,000-token per-call target, with
`agent.step_limit: 150` binding and the repeated-success tripwire never firing); it is recorded as unmet
rather than fixed and needs a human decision, not another document correction.

**One action for the dispatcher, not a correction:** the working tree is not clean. Either commit the
later revision of `.spec/bevy/DEFFRAGILISE-REPORT.md` (sha256 `f563614a...`) together with this report,
which makes the tree clean and pushes the revision whose own `HEAD`-relative fields are named, or push
`c3f6f94` knowingly, which keeps the earlier revision's `numstat_worktree_vs_HEAD` fields, its
"run twice" sentence and its "nothing staged, committed or pushed" line in the pushed record. Both are
documents-only; the choice does not change the gate, the product or any measured figure.

## 4. What I could not establish

No engine, game, network, model call, round or Developer call was run or attempted, so the cost figures
and every other recorded measurement this acceptance did not re-derive are read from the records rather
than re-made. I ran no `git clone` and no non-Windows checkout, so the line-ending question is a byte
fact (0 CR in the three batch documents and across `evidence/`) plus an untouched `.gitattributes`, not a
cross-platform run; clone-safety of all 800 tests was not audited. No CommonMark renderer was run over
any document. The two key-shaped files under `runs/**` were reported by path, size and ignore status
only. The batch's own historical build was not re-run - my gate is my own - and the delivered report was
edited twice while this acceptance was running (04:34:09 and 04:39:04, after the 04:28:41 commit); I
judge the 04:39:04 bytes, which are also the bytes the gate ran on. No tamper or plant experiment was
run, so no copy, restore or restamped timestamp exists here. Whether further edits will follow, and
whether the dispatcher commits the uncommitted revision, are outside what I can establish.
