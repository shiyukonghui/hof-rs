```json
{
 "schema": "hof-rs / bevy final document correction of defects H-1..H-4 of .spec/bevy/ACCEPTANCE-HARDENING.md plus the clone-safety sentence; documents only, no code or test change",
 "produced_at": "2026-10-06",
 "branch": "bevy-core",
 "offline": true,
 "base_head": "4a852692c34ef625ff08464162b562a851dd417d (`docs(acceptance): record the acceptance that fails the hardening batch on one unpinned hash`), whose parent is ef2b0d6cda3439c4a785ff1b3eab155e8407ad1b, the tree the acceptance judged",
 "what_this_batch_did": "corrected documents only: H-1 moved the one stale CLONE-AND-LIVE-REPORT.md sha256 pin left by the hardening batch, H-2 restated the hardening report's false 'both pins were updated' claim, H-3 labelled the four present-tense statements in TOTALS-CORRECTION-REPORT.md that the batch's own R-A1 guard made false, H-4 labelled the section-7 liveness claim, and the clone-safety sentence was restated as a deliberate scope decision rather than a theorem. No code, test, evidence byte, registry, battery, liveness step, line-ending pin or measured figure was changed; no round or Developer call was run; no recording was committed.",
 "gate": {
  "command": "cargo test --offline",
  "literal_exit_code": 0,
  "passed": 800,
  "failed": 0,
  "ignored": 6,
  "test_result_lines": 60,
  "listed": 806,
  "listed_command": "cargo test --offline -- --list",
  "listed_literal_exit_code": 0,
  "ignored_list_command": "cargo test --offline -- --list --ignored",
  "ignored_listed_literal_exit_code": 0,
  "ignored_names": 6,
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
  "git_diff_head_src_tests": "",
  "own_build_dir": "D:/hof-final-target",
  "free_disk_before_building": "F: 37 GiB free, D: 154 GiB free",
  "one_test_process_at_a_time": true,
  "note": "the five lines containing the word 'warning' in the gate stdout are test names (the_resume_warning_states_the_scope_it_applied, every_result_json_carries_the_scope_warning, and three recording tests); there are 0 'warning:' lines in either stream."
 },
 "computed_values": {
  "value_computed_myself": "423036d0b10f44fd00126f3bb4066ef1c6d303d5ceee415d733d619afebc4006 - the sha256 of .spec/bevy/CLONE-AND-LIVE-REPORT.md",
  "convention": "the file's pinned values use `sha256sum <path>` for working files (see TOTALS-CORRECTION-REPORT.md, command 'sha256sum evidence/index.json') and `git cat-file -p <blob> | sha256sum` for blobs (command 'git cat-file -p afde67da | sha256sum'). Both are SHA-256 over file content with no git blob header, so for a working file byte-identical to its blob the two agree; this path has 0 CR bytes, so they agree here.",
  "two_ways": {
   "sha256sum_working_file": "423036d0b10f44fd00126f3bb4066ef1c6d303d5ceee415d733d619afebc4006",
   "sha256_of_git_cat_file_p_HEAD_path": "423036d0b10f44fd00126f3bb4066ef1c6d303d5ceee415d733d619afebc4006",
   "sha256_of_working_file_equals_sha256_of_HEAD_blob": true,
   "cr_bytes_in_file": 0
  },
  "other_pins_verified": [
   {
    "pin": "b2053ad15ca2618a3b3b1829e66ef908fc23c6cf014922b2034f1d282f0cff9f",
    "at": "RECORD-CORRECTION-REPORT.md lines 7 and 179",
    "for": "blob 64a69937 = c00716d:.spec/bevy/CLONE-AND-LIVE-REPORT.md",
    "how": "git cat-file -p 64a69937 and git show c00716d:<path>, both sha256",
    "matches": true
   },
   {
    "pin": "eb88286c638363a7ff64e7aa1bf901159cc68bf0663707c9526f258a9bb03d2f",
    "at": "RECORD-CORRECTION-REPORT.md lines 44 and 134",
    "for": "evidence/index.json working file",
    "how": "sha256sum evidence/index.json",
    "matches": true
   },
   {
    "pin": "6ea1090bf8a11b0cbcd8d0970ba42180ad0e50da08c5211546397a4a6b4bb6f1",
    "at": "RECORD-CORRECTION-REPORT.md lines 45 and 139",
    "for": "src/adapter/bevy/prd_surfaces.rs working file",
    "how": "sha256sum src/adapter/bevy/prd_surfaces.rs",
    "matches": true
   },
   {
    "pin": "889033a5fd8914357886b28f110609dcffad571194e844d03e5db7d3fb44471e",
    "at": "RECORD-CORRECTION-REPORT.md lines 47 and 129",
    "for": "f1b9af3:.spec/bevy/CLONE-AND-LIVE-REPORT.md",
    "how": "git show f1b9af3:<path> | sha256",
    "matches": true
   },
   {
    "pin": "7c09a7ad95597453441cef6ba2c33cf73f6b00dc71a0d4b6f2fcbde68dbc66bb",
    "at": "RECORD-CORRECTION-REPORT.md lines 47 and 129",
    "for": "92870a7 and 166212f revisions of the path",
    "how": "git show 92870a7:<path> and git show 166212f:<path>, both sha256",
    "matches": true
   },
   {
    "pin": "423036d0b10f44fd00126f3bb4066ef1c6d303d5ceee415d733d619afebc4006",
    "at": "RECORD-CORRECTION-REPORT.md line 46 (and now 129)",
    "for": "ef2b0d6 and HEAD revisions and the working file",
    "how": "git show ef2b0d6:<path>, git show HEAD:<path>, sha256sum <path>",
    "matches": true
   },
   {
    "pin": "cebea19e0f955369a3a7fc8012f785c3f2d8939cde43208e5f7052af98f1d4e3",
    "at": "RECORD-CORRECTION-REPORT.md line 144",
    "for": "blob afde67da",
    "how": "git cat-file -p afde67da | sha256",
    "matches": true
   }
  ],
  "h2_diff_evidence": "git diff -U0 166212f ef2b0d6 -- .spec/bevy/RECORD-CORRECTION-REPORT.md has hunks at lines 46, 61, 114, 173, 175, 183, 342 and 372-374 only - never 129 - so the hardening batch did not touch the second pin site.",
  "evidence_totals_recomputed": {
   "how": "own read-only Python walk of evidence/",
   "corpus": "118 files / 4,771,139 bytes",
   "excluded_files": "4 files / 27,829 bytes (index.json 15,570 + README.md 4,073 + tools/build_evidence.py 4,731 + tools/keyscan.py 3,455)",
   "directory": "122 files / 4,798,968 bytes",
   "unchanged": true
  },
  "h4_liveness_strings": "COVERAGE-EVIDENCE-REPORT.md now has 3 lines / 4 occurrences of the three search strings (PENDING ITS FIRST REAL OBSERVATION / has ever been produced / never executed against a real game), all quoted-and-labelled falsified history; this matches TOTALS-CORRECTION-REPORT.md's own hits_after_the_edit."
 },
 "defects": [
  {
   "id": "H-1",
   "severity": "high",
   "file": ".spec/bevy/RECORD-CORRECTION-REPORT.md",
   "site": "changed_files[0].committed_as (line 129)",
   "old_text": "the byte-totals correction authorised by defects RD-1/RD-3 of .spec/bevy/ACCEPTANCE-RECORD.md has since changed two measured totals in this path, so the delivered working file now hashes to 7c09a7ad95597453441cef6ba2c33cf73f6b00dc71a0d4b6f2fcbde68dbc66bb",
   "corrected_text": "the byte-totals correction authorised by defects RD-1/RD-3 of .spec/bevy/ACCEPTANCE-RECORD.md has since changed two measured totals in this path, so the delivered working file now hashes to 423036d0b10f44fd00126f3bb4066ef1c6d303d5ceee415d733d619afebc4006. The values this path has carried, each beside the revision it names: aee9c92/f1b9af3 = 889033a5fd8914357886b28f110609dcffad571194e844d03e5db7d3fb44471e [SUPERSEDED]; the RD-1/RD-3 byte-totals correction (DECISIONS D308, commit 92870a7) = 7c09a7ad95597453441cef6ba2c33cf73f6b00dc71a0d4b6f2fcbde68dbc66bb [SUPERSEDED, and this line presented that value as current with no label until defect H-1 of .spec/bevy/ACCEPTANCE-HARDENING.md was corrected]; the R-A2 cross-reference labels (DECISIONS D309, commit ef2b0d6) = 423036d0b10f44fd00126f3bb4066ef1c6d303d5ceee415d733d619afebc4006 [CURRENT].",
   "value_computed_myself": "423036d0b10f44fd00126f3bb4066ef1c6d303d5ceee415d733d619afebc4006",
   "how_i_computed_it": "sha256sum of the working file and sha256 of `git cat-file -p HEAD:.spec/bevy/CLONE-AND-LIVE-REPORT.md` both give 423036d0...; the file has 0 CR bytes so the two conventions agree. `git show 166212f:<path>` = 7c09a7ad... and `git show f1b9af3:<path>` = 889033a5..., so the superseded values are correct; 7c09a7ad... and 889033a5... are kept as labelled [SUPERSEDED] history beside it."
  },
  {
   "id": "H-2",
   "severity": "medium",
   "file": ".spec/bevy/HARDENING-REPORT.md",
   "sites": [
    {
     "site": "stale_references.consequential_pin (line 109)",
     "old_text": "so both were updated to the new value and the two earlier values (`889033a5...` for the f1b9af3 revision, `7c09a7ad...` for the post-RD-1 revision) are kept as labelled history beside them - the minimum RD-2-consistent change, and the same shape the previous batch was commended for.",
     "corrected_text": "**Correction (defect H-2 of `.spec/bevy/ACCEPTANCE-HARDENING.md`): only ONE of the two was actually moved.** `gate.gate_input_sha256` (line 46) was set to `423036d0...` and its note (line 47) rewritten to name all three values; `changed_files[0].committed_as` (line 129) was left unchanged and therefore still presented `7c09a7ad...` in the present tense with no label, which is false of the tree it ships. The original claim in this field - that `both were updated to the new value` - was therefore a fresh false statement of the RD-2 class. The omission is repaired by the follow-up document correction (H-1 of the same acceptance, recorded in `.spec/bevy/FINAL-DOC-REPORT.md`), which moves line 129 to `423036d0...` and keeps `889033a5...` (f1b9af3 revision, labelled SUPERSEDED) and `7c09a7ad...` (post-RD-1 revision, labelled SUPERSEDED) beside it. This field keeps its history rather than deleting it: what this batch records is that it intended the minimum RD-2-consistent change, moved one pin, and wrongly reported both."
    },
    {
     "site": "changed_files entry for RECORD-CORRECTION-REPORT.md (line 179)",
     "old_text": "plus the two CLONE-AND-LIVE-REPORT.md sha256 pins moved to the new value with the old kept as history",
     "corrected_text": "plus ONE of the two CLONE-AND-LIVE-REPORT.md sha256 pins moved to the new value with the old kept as history (`gate.gate_input_sha256` was moved; `changed_files[0].committed_as` was NOT - defects H-1/H-2 of .spec/bevy/ACCEPTANCE-HARDENING.md, corrected by the follow-up document correction)"
    },
    {
     "site": "section 2 prose (lines 268-274)",
     "old_text": "both pins now carry the new value `423036d0...` and keep `889033a5...` (the f1b9af3 revision) and `7c09a7ad...` (the post-RD-1 revision) as labelled history beside it.",
     "corrected_text": "the two pins were meant to be moved together to the new value `423036d0...` and to keep `889033a5...` (the f1b9af3 revision) and `7c09a7ad...` (the post-RD-1 revision) as labelled history beside them. **Correction (defect H-2 of `.spec/bevy/ACCEPTANCE-HARDENING.md`): only one was actually moved.** `gate.gate_input_sha256` (`RECORD-CORRECTION-REPORT.md:46`) was set to `423036d0...` and its note at `:47` names all three values; `changed_files[0].committed_as` (`:129`) was left presenting `7c09a7ad...` in the present tense with no label, which is false, and the machine block's `consequential_pin` claimed both were updated - a fresh false statement of the RD-2 class this batch existed to close. The follow-up document correction (H-1, recorded in `.spec/bevy/FINAL-DOC-REPORT.md`) moves `:129` to `423036d0...` and keeps both earlier values there as labelled `SUPERSEDED` history."
    }
   ],
   "old_text": "so both were updated to the new value and the two earlier values (`889033a5...` for the f1b9af3 revision, `7c09a7ad...` for the post-RD-1 revision) are kept as labelled history beside them - the minimum RD-2-consistent change, and the same shape the previous batch was commended for. | plus the two CLONE-AND-LIVE-REPORT.md sha256 pins moved to the new value with the old kept as history | both pins now carry the new value `423036d0...` and keep `889033a5...` (the f1b9af3 revision) and `7c09a7ad...` (the post-RD-1 revision) as labelled history beside it.",
   "corrected_text": "**Correction (defect H-2 of `.spec/bevy/ACCEPTANCE-HARDENING.md`): only ONE of the two was actually moved.** `gate.gate_input_sha256` (line 46) was set to `423036d0...` and its note (line 47) rewritten to name all three values; `changed_files[0].committed_as` (line 129) was left unchanged and therefore still presented `7c09a7ad...` in the present tense with no label, which is false of the tree it ships. The original claim in this field - that `both were updated to the new value` - was therefore a fresh false statement of the RD-2 class. The omission is repaired by the follow-up document correction (H-1 of the same acceptance, recorded in `.spec/bevy/FINAL-DOC-REPORT.md`), which moves line 129 to `423036d0...` and keeps `889033a5...` (f1b9af3 revision, labelled SUPERSEDED) and `7c09a7ad...` (post-RD-1 revision, labelled SUPERSEDED) beside it. This field keeps its history rather than deleting it: what this batch records is that it intended the minimum RD-2-consistent change, moved one pin, and wrongly reported both. | plus ONE of the two CLONE-AND-LIVE-REPORT.md sha256 pins moved to the new value with the old kept as history (`gate.gate_input_sha256` was moved; `changed_files[0].committed_as` was NOT - defects H-1/H-2 of .spec/bevy/ACCEPTANCE-HARDENING.md, corrected by the follow-up document correction) | the two pins were meant to be moved together to the new value `423036d0...` and to keep `889033a5...` (the f1b9af3 revision) and `7c09a7ad...` (the post-RD-1 revision) as labelled history beside them. **Correction (defect H-2 of `.spec/bevy/ACCEPTANCE-HARDENING.md`): only one was actually moved.** `gate.gate_input_sha256` (`RECORD-CORRECTION-REPORT.md:46`) was set to `423036d0...` and its note at `:47` names all three values; `changed_files[0].committed_as` (`:129`) was left presenting `7c09a7ad...` in the present tense with no label, which is false, and the machine block's `consequential_pin` claimed both were updated - a fresh false statement of the RD-2 class this batch existed to close. The follow-up document correction (H-1, recorded in `.spec/bevy/FINAL-DOC-REPORT.md`) moves `:129` to `423036d0...` and keeps both earlier values there as labelled `SUPERSEDED` history.",
   "value_computed_myself": "only one of the two pin sites in RECORD-CORRECTION-REPORT.md holds the new value: line 46 = 423036d0..., line 129 was 7c09a7ad...; and `git diff -U0 166212f ef2b0d6 -- .spec/bevy/RECORD-CORRECTION-REPORT.md` has no hunk at line 129."
  },
  {
   "id": "H-3",
   "severity": "medium",
   "file": ".spec/bevy/TOTALS-CORRECTION-REPORT.md",
   "sites": [
    {
     "site": "machine block tests_that_read_the_files_this_batch_edited (line 205)",
     "old_text": "tests/evidence_reproduction.rs::the_evidence_index_names_committed_files_and_commands walks evidence/ and SKIPS README.md by name (it is not part of the corpus) and reads only its file name, never its bytes; the edit is byte-length-preserving, so even that walk's arithmetic is unchanged. No other test reads it.",
     "corrected_text": "AT THE TIME OF THIS BATCH the only test that walks evidence/ (tests/evidence_reproduction.rs::the_evidence_index_names_committed_files_and_commands) skipped README.md by name (it is not part of the corpus) and read only its file name, never its bytes, so this batch's byte-length-preserving edit was invisible to it and even the walk's arithmetic was unchanged. SUPERSEDED by the R-A1 hardening (DECISIONS D309, commit ef2b0d6): that same test now calls std::fs::read_to_string(committed('evidence/README.md')) and asserts the file's bytes contain 122 files / 4,798,968 bytes (tests/evidence_reproduction.rs:592-598), so the README's stated directory total is guarded and this sentence is no longer the present state. No other test reads it."
    },
    {
     "site": "machine block single_most_important_thing_next_batch (line 211)",
     "old_text": "The directory totals are still hand-stated and guarded by no test, so a one-line edit to any file under evidence/ can falsify them again: derive them in evidence/README.md/index.json and assert them in tests/evidence_reproduction.rs (risk R-5), or the next index edit repeats RD-1.",
     "corrected_text": "AT THE TIME THIS BATCH WROTE IT, the directory totals were still hand-stated and guarded by no test, so a one-line edit to any file under evidence/ could falsify them again; the recommendation was to derive them in evidence/README.md/index.json and assert them in tests/evidence_reproduction.rs (risk R-5), or the next index edit would repeat RD-1. SUPERSEDED by the R-A1 hardening (DECISIONS D309, commit ef2b0d6): that recommendation was carried out - the same walk in tests/evidence_reproduction.rs now accumulates and asserts the corpus, the excluded-files and the directory totals, the identity directory = corpus + excluded, and the sentence in evidence/README.md, so any byte change under evidence/ is red. Kept here as what was believed when."
    },
    {
     "site": "section 2 prose (lines 309-312)",
     "old_text": "None of them reads any edited document's bytes. `evidence/README.md` is inside `evidence/`, but the one test that walks that directory (`tests/evidence_reproduction.rs::the_evidence_index_names_committed_files_and_commands`) **skips `README.md` by name** and reads only its file name, never its content; the edit is byte-length-preserving, so even that walk's arithmetic is unchanged, and the test that re-derives the corpus (118 / 4,771,139) and the index passes inside the gate.",
     "corrected_text": "None of them reads any edited document's bytes **at the time this batch wrote this**. `evidence/README.md` is inside `evidence/`, and the one test that walked that directory (`tests/evidence_reproduction.rs::the_evidence_index_names_committed_files_and_commands`) **skipped `README.md` by name** and read only its file name, never its content; this batch's edit is byte-length-preserving, so even that walk's arithmetic was unchanged, and the test that re-derives the corpus (118 / 4,771,139) and the index passed inside the gate. **SUPERSEDED by the R-A1 hardening (DECISIONS D309, commit ef2b0d6):** the same test now reads `evidence/README.md`'s bytes with `std::fs::read_to_string` and asserts they contain `122 files / 4,798,968 bytes` (`tests/evidence_reproduction.rs:592-598`), so the sentences above describe the state this batch found, not the state of the tree."
    },
    {
     "site": "section 3 prose (lines 328-331)",
     "old_text": "**The single most important thing for the next batch is that the directory totals are still hand-stated and guarded by no test: a one-line edit to any file under `evidence/` can falsify them again, and this is the second time it has happened. Derive them, or assert them in `tests/evidence_reproduction.rs`, before the next acceptance has to find them by hand.**",
     "corrected_text": "**The single most important thing for the next batch, as this batch wrote it, was that the directory totals were still hand-stated and guarded by no test: a one-line edit to any file under `evidence/` could falsify them again, and this was the second time it had happened. The recommendation was to derive them, or assert them in `tests/evidence_reproduction.rs`, before the next acceptance had to find them by hand. SUPERSEDED by the R-A1 hardening (DECISIONS D309, commit ef2b0d6): that guard now exists - `tests/evidence_reproduction.rs` accumulates and asserts the corpus, the excluded-files and the directory totals, their arithmetic identity, and `evidence/README.md`'s stated sentence - so this paragraph is kept as what was believed when, not as the present state.**"
    }
   ],
   "old_text": "tests/evidence_reproduction.rs::the_evidence_index_names_committed_files_and_commands walks evidence/ and SKIPS README.md by name (it is not part of the corpus) and reads only its file name, never its bytes; the edit is byte-length-preserving, so even that walk's arithmetic is unchanged. No other test reads it. | The directory totals are still hand-stated and guarded by no test, so a one-line edit to any file under evidence/ can falsify them again: derive them in evidence/README.md/index.json and assert them in tests/evidence_reproduction.rs (risk R-5), or the next index edit repeats RD-1. | None of them reads any edited document's bytes. `evidence/README.md` is inside `evidence/`, but the one test that walks that directory (`tests/evidence_reproduction.rs::the_evidence_index_names_committed_files_and_commands`) **skips `README.md` by name** and reads only its file name, never its content; the edit is byte-length-preserving, so even that walk's arithmetic is unchanged, and the test that re-derives the corpus (118 / 4,771,139) and the index passes inside the gate. | **The single most important thing for the next batch is that the directory totals are still hand-stated and guarded by no test: a one-line edit to any file under `evidence/` can falsify them again, and this is the second time it has happened. Derive them, or assert them in `tests/evidence_reproduction.rs`, before the next acceptance has to find them by hand.**",
   "corrected_text": "AT THE TIME OF THIS BATCH the only test that walks evidence/ (tests/evidence_reproduction.rs::the_evidence_index_names_committed_files_and_commands) skipped README.md by name (it is not part of the corpus) and read only its file name, never its bytes, so this batch's byte-length-preserving edit was invisible to it and even the walk's arithmetic was unchanged. SUPERSEDED by the R-A1 hardening (DECISIONS D309, commit ef2b0d6): that same test now calls std::fs::read_to_string(committed('evidence/README.md')) and asserts the file's bytes contain 122 files / 4,798,968 bytes (tests/evidence_reproduction.rs:592-598), so the README's stated directory total is guarded and this sentence is no longer the present state. No other test reads it. | AT THE TIME THIS BATCH WROTE IT, the directory totals were still hand-stated and guarded by no test, so a one-line edit to any file under evidence/ could falsify them again; the recommendation was to derive them in evidence/README.md/index.json and assert them in tests/evidence_reproduction.rs (risk R-5), or the next index edit would repeat RD-1. SUPERSEDED by the R-A1 hardening (DECISIONS D309, commit ef2b0d6): that recommendation was carried out - the same walk in tests/evidence_reproduction.rs now accumulates and asserts the corpus, the excluded-files and the directory totals, the identity directory = corpus + excluded, and the sentence in evidence/README.md, so any byte change under evidence/ is red. Kept here as what was believed when. | None of them reads any edited document's bytes **at the time this batch wrote this**. `evidence/README.md` is inside `evidence/`, and the one test that walked that directory (`tests/evidence_reproduction.rs::the_evidence_index_names_committed_files_and_commands`) **skipped `README.md` by name** and read only its file name, never its content; this batch's edit is byte-length-preserving, so even that walk's arithmetic was unchanged, and the test that re-derives the corpus (118 / 4,771,139) and the index passed inside the gate. **SUPERSEDED by the R-A1 hardening (DECISIONS D309, commit ef2b0d6):** the same test now reads `evidence/README.md`'s bytes with `std::fs::read_to_string` and asserts they contain `122 files / 4,798,968 bytes` (`tests/evidence_reproduction.rs:592-598`), so the sentences above describe the state this batch found, not the state of the tree. | **The single most important thing for the next batch, as this batch wrote it, was that the directory totals were still hand-stated and guarded by no test: a one-line edit to any file under `evidence/` could falsify them again, and this was the second time it had happened. The recommendation was to derive them, or assert them in `tests/evidence_reproduction.rs`, before the next acceptance had to find them by hand. SUPERSEDED by the R-A1 hardening (DECISIONS D309, commit ef2b0d6): that guard now exists - `tests/evidence_reproduction.rs` accumulates and asserts the corpus, the excluded-files and the directory totals, their arithmetic identity, and `evidence/README.md`'s stated sentence - so this paragraph is kept as what was believed when, not as the present state.**",
   "value_computed_myself": "tests/evidence_reproduction.rs:592-598 now calls std::fs::read_to_string(committed('evidence/README.md')) and asserts the bytes contain '122 files / 4,798,968 bytes'; my own read-only walk measures corpus 118/4,771,139, excluded 4/27,829, directory 122/4,798,968, and the README statement is present (True). The measured figures are unchanged."
  },
  {
   "id": "H-4",
   "severity": "low",
   "file": ".spec/bevy/RECORD-CORRECTION-REPORT.md",
   "site": "section 7 (lines 394-395)",
   "old_text": "it still says the liveness step never ran, while the same file already records that it did.",
   "corrected_text": "it still says the liveness step never ran, while the same file already records that it did. **[SUPERSEDED 2026-10-06 by the RD-3 correction, DECISIONS D308:** the authorisation asked for here was granted, `.spec/bevy/COVERAGE-EVIDENCE-REPORT.md`'s clauses were afterwards rewritten, and that file no longer says this; the liveness sentence above, and the rest of this section's premise, was true when this section was written and is not the present state.]**",
   "value_computed_myself": "COVERAGE-EVIDENCE-REPORT.md has 3 lines / 4 occurrences of the three liveness search strings, all of them quoted and labelled falsified history; the rewrite it points at is committed as the RD-3 correction (DECISIONS D308, commit 92870a7)."
  }
 ],
 "clone_safety_sentence": {
  "where": "HARDENING-REPORT.md machine block clone_safety.why_they_cannot_be_made_clone_safe (line 156), section 0 (line ~223) and section 3 (line ~300)",
  "original_sentences": [
   "none of the five can honestly be made clone-safe",
   "None of the five can be made clone-safe here, and the reason is structural, not a choice."
  ],
  "overstates_the_finding": true,
  "why": "the two sentences state an impossibility ('cannot', 'structural, not a choice'), but the acceptance's RH-4 is right that this is a scope decision: the ~5.9 MB of needed recordings (measured here at 5,917,632 bytes across the six developer.attempt1.json files) could be committed somewhere other than evidence/ without moving the measured corpus and directory totals.",
  "disposition": "corrected at all three sites to say the five were left clone-weak by a deliberate scope decision, not because they are impossible to make clone-safe; the original wording is kept and labelled superseded.",
  "alternative_and_its_cost": "un-ignore a runs/** path (or add a new tracked directory) with the recordings and point the five tests at it. That leaves the measured totals untouched, but it is a separate decision for the owner of the evidence budget; placing the files under runs/** commits the key-shaped material the tracked tree currently excludes (the acceptance found it in runs/round1 and runs/round1b); and a directory outside evidence/ would not be covered by the R-A1 totals guard.",
  "recording_committed": false,
  "change_site": "HARDENING-REPORT.md machine line 156, section 0 and section 3"
 },
 "changed_files": [
  {
   "path": ".spec/bevy/RECORD-CORRECTION-REPORT.md",
   "what": "H-1 (line 129 pin moved to 423036d0... with 889033a5... and 7c09a7ad... kept as labelled history) and H-4 (section 7 label)"
  },
  {
   "path": ".spec/bevy/HARDENING-REPORT.md",
   "what": "H-2 (consequential_pin, changed_files and section 2 restated: only one pin was moved) and the clone-safety sentence (section 0, section 3 and the machine block) restated as a scope decision"
  },
  {
   "path": ".spec/bevy/TOTALS-CORRECTION-REPORT.md",
   "what": "H-3 (the four present-tense statements made false by the R-A1 guard are now past tense with SUPERSEDED labels and the guard named)"
  },
  {
   "path": "DECISIONS.md",
   "what": "D310 appended (21 insertions, 0 deletions): the H-1..H-4 corrections and the clone-safety qualification"
  },
  {
   "path": ".spec/bevy/FINAL-DOC-REPORT.md",
   "what": "this report (read by no test, build script or gate)"
  }
 ],
 "not_changed": [
  "src/** and tests/** (git diff HEAD -- src tests is empty; 228 #[test] attribute lines)",
  "evidence/** and every measured figure (corpus 118/4,771,139, excluded 4/27,829, directory 122/4,798,968)",
  "the coverage registry PRD_SURFACES, the battery, the liveness step, the .gitattributes line-ending pin, config/hoh.yaml and the cost machinery",
  "no recording was committed; runs/** is untouched",
  "no API key was created, copied or printed; no round, engine, game, network or model call was made"
 ],
 "single_most_important_thing_next_batch": "Do not correct documents again. Every pinned hash in RECORD-CORRECTION-REPORT.md now resolves to the revision it names, the hardening report no longer claims a change it did not make, the four R-A1-superseded statements are labelled, and the clone-weak five are honestly described as a scope decision. The one remaining open goal criterion is cost - 2.549x-2.604x the 1,500,000-token per-call target with agent.step_limit: 150 binding and the tripwire never firing - which needs a human decision, not another record correction. A fresh independent acceptance should now pass, and it should spend its budget re-deriving the pins and the evidence totals rather than re-reading the diff."
}
```


# FINAL-DOC-REPORT - the H-1..H-4 document corrections and the clone-safety qualification

**Documents only.** This batch corrects the four defects `.spec/bevy/ACCEPTANCE-HARDENING.md`
recorded and the one overstatement in its risks, and changes nothing else: no code, no test, no
byte under `evidence/`, no measured figure, and no recording committed. It was **offline** - no
engine, no game, no network, no model call, no round and no Developer call. Nothing was committed
or pushed (the dispatcher does that); no `git checkout --` and no `rm -rf` was used; no path was
built from an unexpanded variable; no API key was created, copied or printed. Helper scripts live
outside the repository under `F:/hof-final-work/`, logs under `F:/hof-final-logs/`, and the build
under `D:/hof-final-target`. The machine-readable block above is
`json.dumps(..., indent=1, ensure_ascii=False)` output written by
`F:/hof-final-work/gen_final.py`, which then **parsed it back out of the written file** and failed
if it did not round-trip.

## 0. The verdict in one paragraph

**All four defects are corrected with their history kept, and the clone-safety sentence is now
honest about being a scope decision.** The one value that had to be computed rather than trusted
is the pin: `.spec/bevy/CLONE-AND-LIVE-REPORT.md` hashes to
`423036d0b10f44fd00126f3bb4066ef1c6d303d5ceee415d733d619afebc4006`, computed two ways that agree
(`sha256sum` of the working file, and `sha256` of `git cat-file -p HEAD:<path>`, with 0 CR bytes in
the file), and `RECORD-CORRECTION-REPORT.md:129` now says so while keeping `889033a5...` (f1b9af3)
and `7c09a7ad...` (the RD-1/RD-3 revision, 92870a7) as labelled `[SUPERSEDED]` history. Every other
pin in that report was recomputed and holds: `b2053ad1` (blob `64a69937` = `c00716d`), `eb88286c`
(`evidence/index.json`), `6ea1090b` (`prd_surfaces.rs`), `889033a5`, `7c09a7ad`, `423036d0` and
`cebea19e` (blob `afde67da`). `HARDENING-REPORT.md` now says plainly that only
`gate.gate_input_sha256` was moved and `changed_files[0].committed_as` was not. The four
`TOTALS-CORRECTION-REPORT.md` statements that this batch's own R-A1 guard made false are past tense
with `SUPERSEDED by the R-A1 hardening (DECISIONS D309, commit ef2b0d6)` and the guard named, and
`RECORD-CORRECTION-REPORT.md` section 7 carries the label it lacked. The gate on the delivered tree
is `cargo test --offline` **literal exit code 0** with **800 passed / 0 failed / 6 ignored** over 60
`test result:` lines, **806** listed, **6** ignored, `cargo fmt --all --check` **exit 0** with 0
bytes on both streams, **0** `warning:` lines, and **no test removed**. `evidence/` is unchanged:
my own walk re-derives 118 / 4,771,139 corpus, 4 / 27,829 excluded and 122 / 4,798,968 directory,
and `evidence/README.md` still states the directory sentence the R-A1 guard reads.

## 1. H-1 - the stale pin, corrected with the chain preserved

`changed_files[0].committed_as` is the second of the two sites that pin
`CLONE-AND-LIVE-REPORT.md`, and the hardening batch moved only the first (`:46`,
`gate.gate_input_sha256`). I recomputed the value rather than adopting the acceptance's:

| revision / site | sha256 of `.spec/bevy/CLONE-AND-LIVE-REPORT.md` | state |
|---|---|---|
| `f1b9af3` (`git show f1b9af3:...`) | `889033a5fd8914357886b28f110609dcffad571194e844d03e5db7d3fb44471e` | now labelled history at `:129` (already at `:47`) |
| `92870a7` / `166212f` (`git show ...`) | `7c09a7ad95597453441cef6ba2c33cf73f6b00dc71a0d4b6f2fcbde68dbc66bb` | labelled history at `:129` and `:47` |
| `ef2b0d6`, `HEAD` and the working file | `423036d0b10f44fd00126f3bb4066ef1c6d303d5ceee415d733d619afebc4006` | **current** at `:46` and now `:129` |

The file has **0 CR bytes**, so `sha256sum <path>` and `sha256` of
`git cat-file -p HEAD:<path>` agree - which is why either convention the report uses gives the same
value. Line 129 now reads `...now hashes to 423036d0...`, with both earlier values kept beside it
and each labelled with the revision it names.

## 2. H-2 - the report's false claim restated, not deleted

`HARDENING-REPORT.md` said in three places that **both** pins were updated. Only one was. All three
sites (the machine block's `stale_references.consequential_pin`, the `changed_files` entry, and
section 2) keep the original wording and state what actually happened: `gate.gate_input_sha256`
(`:46`) was moved to `423036d0...` and its note rewritten; `changed_files[0].committed_as` (`:129`)
was left presenting `7c09a7ad...` in the present tense with no label, which is false; that is defect
H-1, and the follow-up correction of this batch moves it. The acceptance's own repro is reproduced:
`git diff -U0 166212f ef2b0d6 -- .spec/bevy/RECORD-CORRECTION-REPORT.md` has hunks at lines 46, 61,
114, 173, 175, 183, 342 and 372-374 only - never 129.

## 3. H-3 - the four statements the batch's own guard made false

The R-A1 hardening added exactly the guard that these statements said did not exist, and made the
walk read exactly the bytes they said it never read:

* `:205` and `:309-312` said the walk `skips README.md by name` and `reads only its file name,
  never its bytes/content`. The test now calls
  `std::fs::read_to_string(committed("evidence/README.md"))` and asserts the bytes contain
  `122 files / 4,798,968 bytes` (`tests/evidence_reproduction.rs:592-598`).
* `:211` and `:328-331` said the directory totals are `still hand-stated and guarded by no test`.
  The R-A1 guard is precisely the test that now guards them.

Each site is now past tense with a `SUPERSEDED by the R-A1 hardening (DECISIONS D309, commit
ef2b0d6)` label and the guard named; the history of what was believed when is kept. This is a
document change only, so no measured figure moves: my own read-only walk still measures the corpus,
the four excluded files and the directory at the same numbers.

## 4. H-4 - the section-7 label

`RECORD-CORRECTION-REPORT.md:394-395` put the liveness contradiction in the present tense with its
only label twenty lines earlier in item 2. The claim now carries
`**[SUPERSEDED 2026-10-06 by the RD-3 correction, DECISIONS D308:** ...]**` at the point of the
claim, saying the authorisation was afterwards granted, the file's clauses were rewritten, and the
sentence - and the rest of the section's premise - was true when it was written.

## 5. The clone-safety sentence

The acceptance's RH-4 is right, and I have corrected the record rather than leaving the stronger
claim standing. "None of the five can honestly be made clone-safe" and "None of the five can be
made clone-safe here, and the reason is structural, not a choice" state an impossibility. What is
true is narrower: the five were **left clone-weak by a deliberate scope decision**, because
committing their recordings under `evidence/` would move the measured corpus and directory totals
this batch was forbidden to change. It is a scope decision and not a theorem because the six
needed recordings - measured here at 5,917,632 bytes in total - could be committed somewhere other
than `evidence/` without moving those totals. The alternative's cost is now stated at all three
sites: it is a separate decision for the owner of the evidence budget; a `runs/**` placement would
commit the key-shaped material the tracked tree currently excludes (found in `runs/round1` and
`runs/round1b`); and a directory outside `evidence/` would not be covered by the R-A1 totals guard.
**No recording was committed**, and the original wording is kept and labelled superseded.

## 6. What I verified, and how

* **Every pin in `RECORD-CORRECTION-REPORT.md`.** Recomputed from git and from the filesystem, not
  read from the report: `b2053ad1` for blob `64a69937` and for `c00716d:<path>`; `eb88286c` for
  `evidence/index.json`; `6ea1090b` for `prd_surfaces.rs`; `889033a5` for `f1b9af3`; `7c09a7ad` for
  `92870a7` and `166212f`; `423036d0` for `ef2b0d6`, `HEAD` and the working file; `cebea19e` for
  blob `afde67da`. All match the values the report pins, and the two conventions agree because the
  pinned files carry no CR bytes.
* **The evidence totals, unchanged.** An independent read-only Python walk of `evidence/` gives
  118 / 4,771,139 corpus, 4 / 27,829 excluded (`index.json` 15,570 + `README.md` 4,073 +
  `tools/build_evidence.py` 4,731 + `tools/keyscan.py` 3,455) and 122 / 4,798,968 directory, and
  `evidence/README.md` contains the sentence the guard reads.
* **The documents I edited still parse.** The leading JSON block of each of the three edited
  reports was re-parsed after the edits, and this report's own block is parsed back out of the
  written file as the generator's last act.
* **Only documents changed.** `git status --porcelain` lists the three reports, `DECISIONS.md` and
  this report; `git diff HEAD -- src tests` is empty; `DECISIONS.md` is append-only (`21 0` in
  `git diff --numstat`).
* **No test reads these documents.** `grep` over `tests/` and `src/` finds one comment mentioning
  `HARDENING-REPORT.md` (`tests/repeated_action.rs:583`) and only path-name mentions of
  `DECISIONS.md`; no test, build script or gate reads any of the corrected files, which is also why
  a green gate cannot catch a mistake in them.

## 7. The gate

Free disk was checked before building (F: 37 GiB, D: 154 GiB free), `tasklist` found no
`cargo`/`rustc`/`hoh` process before the run, the build directory is this batch's own
`D:/hof-final-target`, and one test process ran at a time. On the tree carrying the three
corrected reports and the `DECISIONS.md` append:

| check | command | literal exit code | result |
|---|---|---|---|
| full gate | `cargo test --offline` | **0** | **800 passed / 0 failed / 6 ignored** over 60 `test result:` lines |
| listing | `cargo test --offline -- --list` | **0** | **806** names |
| ignored | `cargo test --offline -- --list --ignored` | **0** | **6** names |
| formatting | `cargo fmt --all --check` | **0** | 0 bytes on stdout and stderr |
| warnings | both streams | - | **0** `warning:` lines (the five stdout lines containing the word are test names) |
| tests removed | `git diff HEAD -- src tests` | - | empty; 228 `#[test]` attribute lines at HEAD and here |

This report is the only write after the gate, and no test, build script or gate reads it. The gate
was run twice (the first run predates the `DECISIONS.md` append); both runs report identical
numbers, and the table above is the second run, on the delivered tree.

## 8. The single most important thing for the next batch

**Stop correcting documents; the one open criterion is cost.** Every pinned hash in
`RECORD-CORRECTION-REPORT.md` now resolves to the revision it names, the hardening report no longer
claims a change it did not make, the four R-A1-superseded statements are labelled in place, and the
clone-weak five are honestly described as a scope decision with the alternative priced. A fresh
independent acceptance should now pass, and it should spend its budget re-deriving the pins and the
evidence totals rather than re-reading this diff. The goal's only unmet criterion remains cost -
2.600x / 2.549x / 2.604x the 1,500,000-token per-call target, every call ended by
`agent.step_limit: 150` with the repeated-success tripwire never firing - and that needs a human
decision, or it will be re-reported by every future acceptance for as long as it stands.
