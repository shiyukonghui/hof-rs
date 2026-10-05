```json
{
 "schema": "hof-rs / bevy DEFFRAGILISE: remove the fragile-citation class from .spec/bevy/EFD1-REPORT.md - line numbers into the append-only DECISIONS.md and diffs against the moving symbol HEAD are replaced by entry/field identifiers, quoted fragments and pinned revisions; documents only, no code, test, evidence byte, registry, battery, liveness step, line-ending pin, config or measured figure changed",
 "produced_at": "2026-10-06",
 "branch": "bevy-core",
 "head_at_start": "263d6f94e31c02800a997caa4a9fe7242b55281c",
 "origin_bevy_core": "166212f1fc4f2e520170e19b894b28501a58235d",
 "report_repaired": ".spec/bevy/EFD1-REPORT.md",
 "report_repaired_was_committed_as": "6b66da67b4a95fe77330b791aebfbb4d6a02a53f",
 "offline": true,
 "line_numbers_in_this_report": "Apart from (a) the quotations of removed text inside citations_changed[].said and (b) the counts and gate figures, this report cites no line number of any document: every location it gives is a file name plus a field or entry identifier. That restriction is the point of the batch, so it applies to this report too.",
 "gate": {
  "test_command": "cargo test --offline",
  "test_literal_exit_code": 0,
  "passed": 800,
  "failed": 0,
  "ignored": 6,
  "test_result_lines": 60,
  "list_command": "cargo test --offline -- --list",
  "list_literal_exit_code": 0,
  "listed": 806,
  "ignored_list_command": "cargo test --offline -- --list --ignored",
  "ignored_list_literal_exit_code": 0,
  "ignored_listed": 6,
  "fmt_command": "cargo fmt --all --check",
  "fmt_literal_exit_code": 0,
  "fmt_stdout_bytes": 0,
  "fmt_stderr_bytes": 0,
  "compiler_warning_lines": 0,
  "warning_like_test_names": "the -- --list output contains 4 test NAMES whose text includes the word 'warning' (for example every_result_json_carries_the_scope_warning); they are names in a listing, not diagnostics, and are the only reason a naive grep for 'warning:' is non-zero",
  "failed_lines": 0,
  "panics": 0,
  "tests_removed": 0,
  "test_attribute_lines": {
   "worktree": 668,
   "91629f4": 668,
   "6b66da6": 668,
   "263d6f9": 668
  },
  "starting_tree": "800 passed / 0 failed / 6 ignored / 806 listed - identical to this batch's measurement",
  "free_disk_before_building": "F: 37 GiB free, D: 100 GiB free; no cargo, rustc or hoh process was running",
  "own_build_dir": "D:/hof-defrag-target",
  "fresh_build_evidence": "the target directory did not exist before the first run; that run's stderr carried 169 `Compiling` lines, and each later run recompiled 1",
  "one_test_process_at_a_time": true,
  "runs": "sequentially, one test process at a time: a fresh first run (169 `Compiling` lines) before this report existed, then a run after the document edits, then runs with this report present; every run gave literal exit 0 with 800 passed / 0 failed / 6 ignored, 806 listed and 6 ignored, and the last run was made on these exact bytes"
 },
 "citations_changed": [
  {
   "id": "efd2-1-decisions-row",
   "where": "the `DECISIONS.md` row of section 1's search table in .spec/bevy/EFD1-REPORT.md (the cell the acceptance called the minimum repair)",
   "said": "quoted removed text: `D311 line 11716, D312 lines 11712/11716`",
   "says_now": "`D311 (its trigger and option 3) and D312 (its trigger and option 3 - the entry that corrects D311): the false claim and its labelled correction, not reference points`",
   "re_derived": "`grep -n why_they_cannot_be_made_clone_safe DECISIONS.md` returns four lines; I read the `## D` headings around them and both candidate blocks, and two of the four are inside D311's block and two inside D312's. The old cell gave D312 one of D311's lines and never named D312's real two. The ownership, not the acceptance's transcription, is what the new cell states. The count (4) is unchanged and still correct."
  },
  {
   "id": "rf3-numstat-fd1-report",
   "where": "`changed_files[.spec/bevy/FD1-REPORT.md].numstat_vs_HEAD` in EFD1-REPORT.md's machine block",
   "said": "`\"numstat_vs_HEAD\": \"3 3\"` - the upper bound was the moving symbol HEAD",
   "says_now": "`\"numstat_91629f4_to_6b66da6\": \"3 3\"`",
   "re_derived": "`git diff --numstat 91629f4 6b66da6 -- .spec/bevy/FD1-REPORT.md` prints `3 3` (literal exit 0). The value was never wrong; only its upper bound was unnamed and moving."
  },
  {
   "id": "rf3-numstat-decisions",
   "where": "`changed_files[DECISIONS.md].numstat_vs_HEAD` in EFD1-REPORT.md's machine block",
   "said": "`\"numstat_vs_HEAD\": \"18 0\"`",
   "says_now": "`\"numstat_91629f4_to_6b66da6\": \"18 0\"`",
   "re_derived": "`git diff --numstat 91629f4 6b66da6 -- DECISIONS.md` prints `18 0` (literal exit 0)."
  },
  {
   "id": "rf3-section2-numstat",
   "where": "section 2 of EFD1-REPORT.md, the `DECISIONS.md` bullet",
   "said": "`git diff --numstat HEAD -- DECISIONS.md` is `18 0`",
   "says_now": "`git diff --numstat 91629f4 6b66da6 -- DECISIONS.md` is `18 0`",
   "re_derived": "Same command as above; it reproduces on any checkout now."
  },
  {
   "id": "rf3-verified-myself-numstat-and-bytes",
   "where": "`verified_myself` of EFD1-REPORT.md's machine block, the append-only sentence",
   "said": "`git diff --numstat HEAD -- DECISIONS.md` is `18 0`, with `(old 1,342,560 bytes / sha256 31014e76..., new 1,347,590 bytes, +5,030)`",
   "says_now": "`git diff --numstat 91629f4 6b66da6 -- DECISIONS.md` is `18 0`, with `(at head_at_start 91629f4: 1,342,560 bytes / sha256 31014e76...; at batch_committed_as 6b66da6: 1,347,590 bytes, +5,030)`",
   "re_derived": "`git cat-file -s 91629f4:DECISIONS.md` is 1342560 and its sha256 is 31014e76...; `git cat-file -s 6b66da6:DECISIONS.md` is 1347590; 1347590-1342560 = 5030. A Python startswith check confirms the 91629f4 blob is a byte-prefix of the 6b66da6 blob. Every figure is unchanged; only the revision each belongs to is now named."
  },
  {
   "id": "rf3-restricted-name-only",
   "where": "`not_changed[0]` of EFD1-REPORT.md's machine block",
   "said": "`git diff --name-only HEAD against them is empty`",
   "says_now": "`git diff --name-only head_at_start batch_committed_as against them is empty`",
   "re_derived": "`git diff --name-only 91629f4 6b66da6 -- src tests config .gitattributes Cargo.toml Cargo.lock evidence scripts .githooks` prints nothing (literal exit 0)."
  },
  {
   "id": "rf3-revision-path",
   "where": "`verified_myself`, the old-fragments sentence",
   "said": "the three old fragments are present in `HEAD:.spec/bevy/FD1-REPORT.md`",
   "says_now": "the three old fragments are present in `91629f4:.spec/bevy/FD1-REPORT.md`",
   "re_derived": "`git show 91629f4:.spec/bevy/FD1-REPORT.md` carries the `where`/`change_site` wording in the three places and the worktree file carries the corrected wording (checked with grep on both)."
  },
  {
   "id": "rf3-test-attribute-revision",
   "where": "`gate.hash_test_attribute_lines_head` and the two prose mentions of the same count",
   "said": "`hash_test_attribute_lines_head`; `668 #[test] lines in worktree and at HEAD`; `668 at HEAD`",
   "says_now": "`hash_test_attribute_lines_head_at_start`; `668 #[test] lines in the worktree and at head_at_start (91629f4)`; `668 at head_at_start (91629f4)`",
   "re_derived": "`git grep -c` for `#[test]` summed over `src tests` gives 668 at 91629f4, at 6b66da6, at 263d6f9 and in the worktree - the figure is unchanged and no test was removed."
  },
  {
   "id": "revision-scoped-occurrence-counts",
   "where": "`key_name_occurrences` of EFD1-REPORT.md's machine block, and the same counts restated in section 0 and at the head of section 1",
   "said": "the counts, with no statement of the revision they were measured at",
   "says_now": "the machine field `measured_against` says they were measured in the working tree based on head_at_start (91629f4) with this batch's edits and this report untracked; section 0 and section 1 repeat that qualification",
   "re_derived": "`git grep -c` at 91629f4 gives FINAL-DOC-REPORT.md 1, ACCEPTANCE-FINAL-DOC.md 6, ACCEPTANCE-FD1.md 7, FD1-REPORT.md 8, HARDENING-REPORT.md 1, DECISIONS.md 2 and no EFD1-REPORT.md; at 6b66da6 it adds EFD1-REPORT.md 9 and DECISIONS.md 4; at the current HEAD it also adds ACCEPTANCE-EFD1.md 4. So the table's DECISIONS.md value of 4 is the post-D312 working-tree value, not the 91629f4 commit value, which is exactly why the revision had to be named."
  },
  {
   "id": "revision-anchor-and-scope",
   "where": "the top of EFD1-REPORT.md's machine block (`batch_committed_as`, `de_fragilised`), `gate.starting_tree`, `verified_myself`'s diff sentence, and section 2's `Line numbers are unchanged` sentence",
   "said": "`head_at_start` alone; `the tree this repair started from` / `the delivered tree`; `is in the diff`; `Line numbers are unchanged`",
   "says_now": "`batch_committed_as` names 6b66da6 alongside `head_at_start`; the starting tree is `(head_at_start 91629f4)` and the delivered tree `(batch_committed_as 6b66da6)`; the diff is `the batch's diff (head_at_start -> batch_committed_as)`; the line numbers are `unchanged by the batch (head_at_start -> batch_committed_as)`; and a `de_fragilised` field records this batch's edit",
   "re_derived": "`git rev-parse 6b66da6` is 6b66da67b4a95fe77330b791aebfbb4d6a02a53f, and `git diff --name-status 91629f4 6b66da6` shows that commit is the batch's own (add EFD1-REPORT.md; modify FD1-REPORT.md and DECISIONS.md)."
  }
 ],
 "citations_kept_with_a_number": [
  {
   "id": "hardening-key-definition-line",
   "where": "the key-definition line of `HARDENING-REPORT.md`, that is the machine field `clone_safety.why_they_cannot_be_made_clone_safe`",
   "which_number_is_meant": "the line number EFD1-REPORT.md already carries; not restated here, to avoid adding a new line-number citation",
   "why_the_number_stays": "It is load-bearing and the number is the only honest way to express it. The citation exists to say that that line's bytes are pinned: a recorded sha256 is taken over exactly that line (the convention is `sed -n '<n>p' | sha256sum`), and the whole file has a second recorded hash. A pin over 'the line' cannot be recomputed without the line number, and the pin is also the reason no batch may edit it. This is the documented exception, not an oversight."
  },
  {
   "id": "final-doc-report-field-lines",
   "where": "the `clone_safety_sentence.where` and `change_site` lines of `FINAL-DOC-REPORT.md`",
   "which_number_is_meant": "the numbers EFD1-REPORT.md already carries; not restated here",
   "why_the_number_stays": "`FINAL-DOC-REPORT.md` is a closed per-batch report, not an append-only document, so its numbering cannot drift without someone editing it; both lines are identified by field name in the same sentence as the number, so a moved number could not mislead a reader; and the numbers are how the FD-1/EFD-1 defect and the acceptances cross-reference it."
  },
  {
   "id": "fd1-report-corrected-places",
   "where": "the three places EFD-1 corrected in `FD1-REPORT.md`: `why_option_A`, `decisions_on_non_blocking_items.RF-3_field_title`, and the section 2 paragraph",
   "which_number_is_meant": "the numbers EFD1-REPORT.md already carries; not restated here",
   "why_the_number_stays": "Each is named by field or entry identifier in the same sentence; `FD1-REPORT.md` is a closed record that is 258 lines at both revisions of interest with a line-neutral `3 3` diff; and the numbers are the acceptance's own cross-reference handles for the three corrections."
  },
  {
   "id": "acceptance-pin-line",
   "where": "the line of `ACCEPTANCE-FD1.md` that records the key-definition line's sha256",
   "which_number_is_meant": "the number EFD1-REPORT.md already carries; not restated here",
   "why_the_number_stays": "It locates a recorded measured figure (the line hash) inside a closed acceptance record, and it is the same load-bearing pin as the first entry above."
  },
  {
   "id": "closesite-value",
   "where": "the literal value of `FINAL-DOC-REPORT.md`'s `change_site` field, quoted inside EFD1-REPORT.md's machine block",
   "which_number_is_meant": "not a citation at all - it is the field's own text, which names a line of `HARDENING-REPORT.md`; it is quoted verbatim and must not be altered",
   "why_the_number_stays": "It is data, not a citation: changing it would misquote the field whose value the whole defect turns on."
  }
 ],
 "revision_scoped_statements": [
  {
   "statement": "the `key_name_occurrences` counts and the same counts in sections 0 and 1",
   "revision_now_named": "the working tree based on head_at_start 91629f4 with this batch's edits, this report untracked; the machine field `measured_against` says so, with what changes at 6b66da6 and later"
  },
  {
   "statement": "both `numstat` values for the batch's changed files (`3 3`, `18 0`)",
   "revision_now_named": "head_at_start 91629f4 -> batch_committed_as 6b66da6, in the field names and in section 2"
  },
  {
   "statement": "the restricted-path name-only diff is empty",
   "revision_now_named": "`head_at_start batch_committed_as`"
  },
  {
   "statement": "the three old fragments are in the committed report and the corrected ones in the worktree",
   "revision_now_named": "`91629f4:`"
  },
  {
   "statement": "DECISIONS.md's byte counts, prefix property and sha256",
   "revision_now_named": "91629f4 for the old blob, 6b66da6 for the new one"
  },
  {
   "statement": "668 `#[test]` lines in the worktree and in the committed report",
   "revision_now_named": "`head_at_start` (91629f4)"
  },
  {
   "statement": "the tree this repair started from and the delivered tree measure the same gate",
   "revision_now_named": "`(head_at_start 91629f4)` and `(batch_committed_as 6b66da6)`"
  },
  {
   "statement": "the batch's diff contains no code, test, evidence, config or script path",
   "revision_now_named": "`the batch's diff (head_at_start -> batch_committed_as)`"
  },
  {
   "statement": "the line numbers of FD1-REPORT.md are unchanged",
   "revision_now_named": "`by the batch (head_at_start -> batch_committed_as)`"
  },
  {
   "statement": "everything else in the repaired report that names a revision",
   "revision_now_named": "`head_at_start` already carried the full 40-character sha; `batch_committed_as` now carries the other end"
  }
 ],
 "changed_files": [
  {
   "path": ".spec/bevy/EFD1-REPORT.md",
   "change": "de-fragilised: the DECISIONS.md table row names D311/D312 instead of line numbers; `batch_committed_as` (6b66da6) names the delivered revision and a `de_fragilised` field records this edit; both `numstat_vs_HEAD` fields became `numstat_91629f4_to_6b66da6`; `HEAD:` became `91629f4:`; every `at HEAD` became `at head_at_start (91629f4)` or the two-commit range; `hash_test_attribute_lines_head` became `hash_test_attribute_lines_head_at_start`; revision scoping was added to the occurrence counts, the starting/delivered tree, the diff sentence and the line-numbers-unchanged sentence",
   "numstat_worktree_vs_HEAD": "19 19",
   "lines_before": 259,
   "lines_after": 259,
   "sha256_before": "88814941e8390777642a603350b1c84e497b87ef413559676f29e302887ff9ac",
   "sha256_after": "c49ee8e6b1a555d3b567a7a0d7f0ff2272fe1f7c92e90c2ec9f204ed2d21b050",
   "note": "line-for-line: the added machine fields (`batch_committed_as`, `de_fragilised`, `measured_against`) sit on existing lines rather than on new ones, so no line was added or removed and the acceptance's references to this report still land on the same fields and the same table cell. The block still parses as JSON; it was parsed back out of the written file."
  },
  {
   "path": "DECISIONS.md",
   "change": "D313 appended (21 insertions, 0 deletions), recording this de-fragilisation, naming the real reference points and naming and limiting D312's HEAD-relative parenthetical; D311 and D312 are byte-identical to before",
   "numstat_worktree_vs_HEAD": "21 0",
   "bytes_before": 1347590,
   "bytes_after": 1353845,
   "sha256_before": "e6e136efe0fbd3c08928d8b41a2d9254d907bb8f8ed188d86efa8b8a62035805",
   "sha256_after": "765f2a8b5b80fe356747db8aae6daf66005fe55fd944f594e1ce33d0a4cd1fc8",
   "append_only_prefix_holds": true,
   "key_occurrence_count_unchanged": true,
   "note": "D313 deliberately does not spell the key name, so the recorded DECISIONS.md occurrence count is still 4 in the working tree"
  },
  {
   "path": ".spec/bevy/DEFFRAGILISE-REPORT.md",
   "change": "this report (new; read by no test, build script or gate)"
  }
 ],
 "not_changed": [
  "src/**, tests/**, config, .gitattributes (the line-ending pin), Cargo.toml, Cargo.lock, evidence/**, scripts/**, .githooks/**, runs/** - `git diff --name-only` against the worktree restricted to those paths is empty, and `git ls-files runs` is empty",
  "the recorded measured figures elsewhere were left alone rather than re-measured: the gate counts, the evidence totals (118 / 4,771,139; 4 / 27,829; 122 / 4,798,968), the six recordings' 5,917,632 bytes, the cost figures and the recorded pins are untouched, and this batch re-derived only the citations named above",
  "no test removed or added: 668 `#[test]` lines at 91629f4, 6b66da6, 263d6f9 and in the worktree",
  "no recording committed, added, copied or moved; no round, engine, game, network or model call; no API key created, copied or printed",
  "nothing deleted: no `rm -rf`, no wildcard deletion, no path built from an unexpanded variable, no `git checkout --`",
  "nothing staged, committed or pushed"
 ],
 "pinned_documents_left_alone": [
  "`HARDENING-REPORT.md` was not touched at all: it is pinned by a recorded whole-file sha256 and by a recorded sha256 of the key-definition line (both in `FD1-REPORT.md`'s machine block, the line hash also in `ACCEPTANCE-FD1.md`), so editing it would falsify recorded figures",
  "`FINAL-DOC-REPORT.md` was not touched: the EFD1 batch's `not_changed` declaration and `FD1-REPORT.md`'s depend on it being unchanged",
  "`FD1-REPORT.md`, `ACCEPTANCE-FD1.md` and `ACCEPTANCE-FINAL-DOC.md` were not touched: they are closed records",
  "the byte corpus under `evidence/**` and the pinned shell/PRD files named in `.gitattributes` were not touched",
  "no document whose bytes are pinned by a recorded hash was edited; if one had to change, this report would have stopped and said so instead"
 ],
 "verified": [
  "`git grep -c why_they_cannot_be_made_clone_safe` was re-run at 91629f4, 6b66da6 and the current HEAD, and the ownership of the four DECISIONS.md lines was re-derived from the `## D` headings and the two blocks - not from the acceptance, and not from the previous batch",
  "`git diff --numstat 91629f4 6b66da6` was re-run: `3 3` for FD1-REPORT.md, `18 0` for DECISIONS.md, and no argument needed a corrected value",
  "the append-only property was re-checked by bytes, not by trust: the 91629f4 blob is a byte-prefix of the 6b66da6 blob and of the file now, and D313 is 21 insertions / 0 deletions",
  "`git diff --name-only 91629f4 6b66da6` and the same against the worktree restricted to src/tests/config/.gitattributes/Cargo.*/evidence/scripts/.githooks are empty",
  "the repaired report is 259 lines at 6b66da6 and now, and its worktree diff is `19 19`, so the edit is line-for-line",
  "the gate was run twice with one test process at a time in this batch's own D:/hof-defrag-target, and both runs gave literal exit 0 and the same counts; free disk was checked before building",
  "the worktree contains no carriage return in either edited document, and its only tracked changes are the two documents named above"
 ],
 "unverified": [
  "The measured figures this batch did not touch were not re-measured: the evidence totals, the six recordings' 5,917,632 bytes, the cost figures (2.600x / 2.549x / 2.604x of the per-call target and the `agent.step_limit: 150` behaviour) and the recorded pins are read from the records, not remade here. What is verified is that this batch edited none of them and no document that pins them.",
  "No real `git clone` and no Linux or macOS checkout was run; the line-ending question was checked only as a byte fact (0 carriage returns in the two edited documents) and by the untouched `.gitattributes`.",
  "The clone-safety of all 800 passing tests was not audited; only the counts (800 passed, 6 ignored, 806 listed, 668 `#[test]` lines) and the absence of failures were reproduced.",
  "No CommonMark renderer was run over the repaired report or over this one; the line-for-line property is asserted from byte, line and numstat counts, not from a rendered view.",
  "The two key-shaped files under `runs/**` were not opened or printed, and no API key was read or handled; only their ignore status and the tracked-file scan were checked, as the earlier acceptances did."
 ],
 "what_this_batch_did_not_do": "No engine, no game, no network, no model call, no round and no Developer call was run. Nothing was written under runs/** and no recording was committed, added, copied or moved. Nothing was deleted: free disk was sufficient (F: 37 GiB, D: 100 GiB) and no space was freed, no `rm -rf` and no wildcard deletion were used. No path was built from an unexpanded variable; no `git checkout --`; no `git add`, stage, commit or push. Helper scripts live outside the repository under F:/hof-defrag-work/, logs under F:/hof-defrag-logs/, the build under D:/hof-defrag-target. No API key was created, copied or printed. The wrong table cell was not corrected - it was replaced by an entry-identifier form - and no other defect, risk or document was worked on.",
 "single_most_important_thing_next_batch": "A line number is not a fact about a document, it is a fact about a revision of it. `DECISIONS.md` is the one document here that grows without bound, so no report should cite a line in it again: name the `D` entry, or quote the sentence. Everything that still carries a number in the repaired report does so because a recorded hash is taken over that exact line or because a field name travels with the number - do not 'finish the job' by deleting those, and never edit the pinned line. And keep the repaired report line-for-line if you touch it: its 259-line shape is what keeps the acceptance's references landing on the same field and the same cell."
}
```

# DEFFRAGILISE-REPORT - remove the fragile-citation class from the EFD-1 record

**Documents only. The wrong cell was not corrected; the class it belongs to was removed.** This batch
repairs `.spec/bevy/EFD1-REPORT.md` so that no citation in it can drift without anyone lying. Where the
report gave a location as a **line number in the append-only `DECISIONS.md`**, it now gives the **entry
identifiers** and what those occurrences are. Where it measured a diff against the **moving symbol
`HEAD`**, it now names **both pinned revisions**. `DECISIONS.md` was **appended to** (D313); nothing in
it was edited, and the recorded occurrence count did not move.

Offline: no engine, no game, no network, no model call, no round and no Developer call. No recording was
committed, added, copied or moved; nothing under `runs/**` was written; **nothing was deleted** (no
`rm -rf`, no wildcard, no need); no `git checkout --`; no path built from an unexpanded variable; no API
key created, copied or printed; nothing staged, committed or pushed. Helper scripts live outside the
repository under `F:/hof-defrag-work/`, logs under `F:/hof-defrag-logs/`, and the build under
`D:/hof-defrag-target`. The machine block above is `json.dumps(..., indent=1, ensure_ascii=False)` output
written by `F:/hof-defrag-work/gen_report.py`, which then parsed it back out of the written file and
required equality.

## 0. The defect, and what "the class" is

The acceptance recorded one defect, **EFD2-1**, in the `DECISIONS.md` row of the report's section-1
search table. That row annotated the key's occurrences as line numbers belonging to D311 and D312, but it
gave D312 one of D311's lines and never named D312's own two, so a reader using the table to find the
residual false claim in the log was sent to the wrong entry. The count was right; the attribution was
not. The acceptance's own repair note offered "correct the numbers, or drop the line numbers and keep the
count".

I dropped the numbers. The row now names **D311 (its trigger and option 3)** and **D312 (its trigger and
option 3 - the entry that corrects D311)**, and says what those occurrences are: the false claim and its
labelled correction, neither of them a reference point to the key. Those identifiers cannot move when the
log grows, which the numbers could and did.

The same fragility has two more faces in the same report, and RF-3 named them. Two machine fields were
called `numstat_vs_HEAD`, and section 2 ran `git diff --numstat HEAD -- DECISIONS.md`; both were written
when `HEAD` was the batch's base and the changes were uncommitted. The dispatcher's commit moved `HEAD`,
so a reader running the command literally no longer sees the quoted result. Those now name the base
(`head_at_start`) and the commit that carried the batch (`batch_committed_as`), and the commands are
two-commit diffs that reproduce on any checkout.

A third face is disclosed rather than edited: D312's decision (b) contains the same shape
(`git diff --numstat a80db33 HEAD -- DECISIONS.md` is empty). `DECISIONS.md` is append-only by its own
rule - D310 option 5, D311 option 5 and D312 option 1 all invoke it - so it is not edited; **D313** names
that sentence and limits it, exactly as D312 named D311's.

## 1. What I verified, and how

* **The repaired report is line-for-line.** `.spec/bevy/EFD1-REPORT.md` is 259 lines at `6b66da6` and 259
  lines now, and its worktree diff is `19 19`: every change is a replacement on an existing line. The
  three machine fields this batch adds (`batch_committed_as`, `de_fragilised`, `measured_against`) are
  placed on existing lines rather than on new ones for exactly that reason, so nothing moved and
  `ACCEPTANCE-EFD1.md`'s own references to that report still land on the same fields and on the very cell
  it called the minimum repair. The block still parses as JSON; the generator parsed it back out.
* **The entry ownership was re-derived, not assumed.** `grep -n` for the key in `DECISIONS.md` returns
  four lines; I read the `## D` headings around them and both candidate blocks, and two of the four are
  inside D311's block and two inside D312's. The old cell's attribution was false in exactly the way the
  acceptance said. The count stayed 4, and D313 deliberately does not spell the key, so it is still 4 in
  the working tree now.
* **Every revision-scoped number was re-derived against the revision it names.**
  `git diff --numstat 91629f4 6b66da6 -- .spec/bevy/FD1-REPORT.md` is `3 3` and for `DECISIONS.md` is
  `18 0`; `git diff --name-only 91629f4 6b66da6 -- src tests config .gitattributes Cargo.toml Cargo.lock
  evidence scripts .githooks` is empty; `git show 91629f4:.spec/bevy/FD1-REPORT.md` carries the three old
  fragments and the worktree file carries the three corrected ones.
* **The append-only property holds and was extended by bytes.** `DECISIONS.md`'s blob at `91629f4`
  (1,342,560 bytes, sha256 `31014e76...`) is a byte-prefix of its blob at `6b66da6` (1,347,590) and of the
  file now (1,353,845); D313 is 21 insertions / 0 deletions, and D311's and D312's bytes are untouched.
* **No test was removed and the gate is unchanged in shape.** 668 `#[test]` lines at `91629f4`,
  `6b66da6`, the current `HEAD` and in the worktree; the gate is still 800 passed / 0 failed / 6 ignored
  over 60 `test result:` lines, 806 listed, 6 listed ignored.
* **Nothing outside the documents moved.** The only tracked files changed in the worktree are
  `.spec/bevy/EFD1-REPORT.md` and `DECISIONS.md`; the restricted-path diff is empty, and no measured
  figure in any report was edited.
* **The pinned documents were left alone.** The key-definition line of `HARDENING-REPORT.md` is pinned by
  a recorded line hash and a recorded whole-file hash, so `HARDENING-REPORT.md` was not touched at all;
  `FINAL-DOC-REPORT.md`, `FD1-REPORT.md`, `ACCEPTANCE-FD1.md` and `ACCEPTANCE-FINAL-DOC.md` were not
  touched either. No document whose bytes are pinned by a recorded hash was edited.

## 2. What kept its number, and why

Not every number was removed, and the difference is deliberate. A number is fragile when the document it
indexes **grows**, or when it is relative to a **moving symbol**. The numbers that remain index documents
that are closed, and one of them is load-bearing.

* **The key-definition line of `HARDENING-REPORT.md` keeps its number, and it is load-bearing.** The
  point of that citation is that the line's bytes are pinned: a recorded sha256 is taken over exactly
  that line (the convention is `sed -n '<n>p' | sha256sum`), and the whole file has a second recorded
  hash. A pin over "the line" cannot be recomputed without the line number, and the pin is also the
  reason no batch may edit it. This is the case the instruction anticipated: the number is the only
  honest way to say it, so it stays.
* **`FINAL-DOC-REPORT.md`'s two field lines keep their numbers** (`clone_safety_sentence.where` and
  `change_site`). Both are named by field in the same sentence as the number, so a moved number could not
  mislead, and `FINAL-DOC-REPORT.md` is a closed report, not an append-only one.
* **`FD1-REPORT.md`'s three corrected places keep their numbers.** Each is named by its field or entry
  identifier in the same breath, and the file is 258 lines at both revisions of interest with a
  line-neutral `3 3` diff.
* **The acceptance's pin line keeps its number** for the same pin reason, and because the acceptance is a
  closed record.

None of those documents is appended to after it closes, so the class this batch closes - a line number
that can move without anyone lying - cannot arise from them.

## 3. The gate

`cargo test --offline` -> **literal exit code 0**, **800 passed / 0 failed / 6 ignored** over **60**
`test result:` lines; `cargo test --offline -- --list` -> literal exit 0, **806** listed;
`-- --list --ignored` -> literal exit 0, **6**; `cargo fmt --all --check` -> **literal exit 0** with
**0 bytes** on both streams; **0** compiler-warning lines; 0 `FAILED`; 0 panic. (The `--list` output
contains four test *names* with the word "warning" in them - for example
`every_result_json_carries_the_scope_warning` - which are names in a listing, not diagnostics, and are
the only reason a naive grep for `warning:` is non-zero.) Free disk was checked first (F: 37 GiB,
D: 100 GiB), the build directory is this batch's own `D:/hof-defrag-target`, and one test process ran at
a time. The gate was run repeatedly, one test process at a time - a fresh first run before this report
existed (169 `Compiling` lines), then a run after the document edits, then runs with this report
present - and every run measured identically; the last run was made on these exact bytes.

## 4. The single most important thing for the next batch

**A line number is not a fact about a document; it is a fact about a revision of it.** The one document
here that grows without bound is `DECISIONS.md`, so no report should ever cite a line in it again - name
the `D` entry, or quote the sentence. Everything that still carries a number in the repaired report does
so because a recorded hash is taken over that exact line, or because a field name travels with the
number; do not "finish the job" by deleting those, and never edit the pinned line. And if you touch the
repaired report, keep it line-for-line: its 259-line shape is what keeps the acceptance's references
landing on the same field and the same cell.
