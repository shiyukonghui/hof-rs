```json
{
 "schema": "hof-rs / bevy mechanical corrections of defects RD-1, RD-2 and RD-3 of .spec/bevy/ACCEPTANCE-RECORD.md",
 "produced_at": "2026-10-06",
 "branch": "bevy-core",
 "head_at_start": "05cff35",
 "head_full": "05cff35cb54d1d9209667549e0fc2290a5538d7d",
 "offline": true,
 "what_this_batch_did": "three mechanical record corrections and nothing else: (RD-1) reconciled the evidence/ directory byte totals to the measured artefact in every document that stated them; (RD-2) corrected one sha256 that named the wrong revision; (RD-3) replaced the twelve sites that said the liveness step had never run with the truth, keeping the old wording as falsified history. No code, registry, battery, liveness step, .gitattributes rule or other measured figure was changed.",
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
  "tests_removed": 0,
  "build_dir": "F:/hof-rd123-target (this batch's own; one cargo process at a time; tasklist found no cargo/rustc/hoh process before either run)",
  "free_disk_before_building": "F: 56 G free, D: 180 G free (measured first, nothing deleted, no rm -rf)",
  "runs": 2,
  "run_note": "both runs report identical numbers. The second was made after every file edit except this report itself; the report is read by no test, build script or gate (grep over src/, tests/ and scripts/), so the frozen tree the gate measured is the delivered one.",
  "logs": [
   "F:/hof-rd123-logs/gate.out",
   "F:/hof-rd123-logs/gate.err",
   "F:/hof-rd123-logs/exits.txt",
   "F:/hof-rd123-logs/list.out",
   "F:/hof-rd123-logs/ignored.out",
   "F:/hof-rd123-logs/fmt.out",
   "F:/hof-rd123-logs/fmt.err",
   "F:/hof-rd123-logs/env.txt",
   "F:/hof-rd123-logs2/gate.out",
   "F:/hof-rd123-logs2/gate.err",
   "F:/hof-rd123-logs2/exits.txt",
   "F:/hof-rd123-logs2/list.out",
   "F:/hof-rd123-logs2/ignored.out",
   "F:/hof-rd123-logs2/fmt.out",
   "F:/hof-rd123-logs2/fmt.err",
   "F:/hof-rd123-logs2/env.txt"
  ]
 },
 "totals": {
  "choice": "update the totals to the measured artefact everywhere; do NOT shrink evidence/index.json's meaning back to restore the old totals",
  "why": "the index's corrected meaning is the substantive D-3 correction of a false claim, and trimming it to a byte count would let the byte count constrain the fact and would encode a hidden coupling between one paragraph's length and numbers hand-stated in four other files (risk R-5). The reconciliation edits inside evidence/ are byte-length-preserving, so the measured object does not move when it is described correctly.",
  "measured_before_edit": {
   "source": "git ls-tree -r -l HEAD evidence (committed blobs) plus git cat-file -s per file",
   "directory": {
    "files": 122,
    "bytes": 4798968
   },
   "excluded_files": {
    "count": 4,
    "bytes": 27829,
    "detail": {
     "evidence/index.json": 15570,
     "evidence/README.md": 4073,
     "evidence/tools/build_evidence.py": 4731,
     "evidence/tools/keyscan.py": 3455
    }
   },
   "corpus": {
    "files": 118,
    "bytes": 4771139
   }
  },
  "measured_after_edit": {
   "source": "python walk of the working tree after every edit",
   "directory": {
    "files": 122,
    "bytes": 4798968
   },
   "excluded_files": {
    "count": 4,
    "bytes": 27829,
    "detail": {
     "evidence/index.json": 15570,
     "evidence/README.md": 4073,
     "evidence/tools/build_evidence.py": 4731,
     "evidence/tools/keyscan.py": 3455
    }
   },
   "corpus": {
    "files": 118,
    "bytes": 4771139
   }
  },
  "directory_total_moved_only_between_the_previous_batch_and_this_one": {
   "stale_directory_total": 4798249,
   "stale_excluded_total": 27110
  },
  "corpus_unchanged": true,
  "corpus_figure": {
   "files": 118,
   "bytes": 4771139,
   "mib": 4.55
  },
  "corpus_unchanged_confirmed_by": "the gate's tests/evidence_reproduction.rs::the_evidence_index_names_committed_files_and_commands re-derives the corpus from the committed files, skips index.json and README.md by name, and passes; evidence/index.json itself was NOT edited by this batch and still hashes to eb88286c...",
  "files_reconciled": [
   "evidence/README.md",
   ".spec/bevy/CLONE-AND-LIVE-REPORT.md",
   "DECISIONS.md",
   ".spec/bevy/COVERAGE-EVIDENCE-REPORT.md"
  ],
  "left_as_history": ".spec/bevy/ACCEPTANCE-CLONE-LIVE.md and .spec/bevy/ACCEPTANCE-RECORD.md still contain 4,798,249 / 27,110; those are acceptance records of measurements that were true when taken (ACCEPTANCE-RECORD.md states them as the RD-1 defect description), and rewriting them would falsify a measurement record. The only other tracked file that still contains the old digits is DECISIONS.md, inside the appended D308 entry, where they appear only as the values being replaced (old -> new); D306(c)'s own statement now carries the corrected 4,798,968 / 27,829."
 },
 "corrected_hash": {
  "path": ".spec/bevy/RECORD-CORRECTION-REPORT.md",
  "line": 144,
  "wrong_value": "889033a5fd8914357886b28f110609dcffad571194e844d03e5db7d3fb44471e",
  "wrong_value_was": "the sha256 of .spec/bevy/CLONE-AND-LIVE-REPORT.md, not of git blob afde67da",
  "blob": "afde67da",
  "command": "git cat-file -p afde67da | sha256sum",
  "correct_value": "cebea19e0f955369a3a7fc8012f785c3f2d8939cde43208e5f7052af98f1d4e3",
  "other_pins_verified": {
   "evidence/index.json": {
    "command": "sha256sum evidence/index.json",
    "value": "eb88286c638363a7ff64e7aa1bf901159cc68bf0663707c9526f258a9bb03d2f",
    "matches_pin": true
   },
   "src/adapter/bevy/prd_surfaces.rs": {
    "command": "sha256sum src/adapter/bevy/prd_surfaces.rs",
    "value": "6ea1090bf8a11b0cbcd8d0970ba42180ad0e50da08c5211546397a4a6b4bb6f1",
    "matches_pin": true
   },
   ".spec/bevy/CLONE-AND-LIVE-REPORT.md": {
    "value_before_this_batch": "889033a5fd8914357886b28f110609dcffad571194e844d03e5db7d3fb44471e",
    "value_after_this_batch": "7c09a7ad95597453441cef6ba2c33cf73f6b00dc71a0d4b6f2fcbde68dbc66bb",
    "note": "this batch's RD-1 edit changed two byte totals in that file, so its own two pins in RECORD-CORRECTION-REPORT.md (gate.gate_input_sha256 and changed_files) were updated to the new value with the old one preserved beside it in the same report; no test, build script or gate reads that file."
   }
  }
 },
 "liveness_statements_corrected": {
  "file": ".spec/bevy/COVERAGE-EVIDENCE-REPORT.md",
  "sites_corrected": 12,
  "method": "every location whose text asserted that e3_process_liveness had never run against a real game / that no raw/e3_process_liveness.json had ever been produced, whether or not it used the acceptance's search strings",
  "site_lines_before_the_edit": [
   165,
   183,
   238,
   240,
   258,
   259,
   578,
   611,
   724,
   729,
   848,
   864
  ],
  "acceptance_reproduction": {
   "command": "git grep -n -e 'PENDING ITS FIRST REAL OBSERVATION' -e 'has ever been produced' -e 'never executed against a real game' -- .spec/bevy/COVERAGE-EVIDENCE-REPORT.md",
   "hits_before_the_edit": "5 lines / 6 occurrences on HEAD (the acceptance said 13 hits; that is not reproducible from its own command)",
   "hits_after_the_edit": "3 lines / 4 occurrences, every one of them the old wording quoted and explicitly labelled as falsified history"
  },
  "wording_used": "implemented, unit/fake-driver tested and since observed on a real game: the follow-up live round clonefix1 ran the ten-step battery in all three iterations, persisted raw/e3_process_liveness.json each time and read 15 verified / 0 gap / 4 unobservable of 19; the observation lives under the gitignored runs/ and not in the committed evidence/ corpus.",
  "defect_narrative_kept": true
 },
 "changed_files": [
  {
   "path": "evidence/README.md",
   "what": "directory total 4,798,249 -> 4,798,968 (byte-length-preserving, so the measured object is unchanged)"
  },
  {
   "path": ".spec/bevy/CLONE-AND-LIVE-REPORT.md",
   "what": "E-7 machine-block change and section 4: directory total 4,798,249 -> 4,798,968; excluded 27,110 -> 27,829"
  },
  {
   "path": ".spec/bevy/COVERAGE-EVIDENCE-REPORT.md",
   "what": "the five total sites (E-7, section 0, section 5, the table row) and the twelve RD-3 sites"
  },
  {
   "path": "DECISIONS.md",
   "what": "D306(c)'s one stale total corrected in place under the explicit authorisation (4,798,249 -> 4,798,968; 27,110 -> 27,829), and D308 appended recording these choices"
  },
  {
   "path": ".spec/bevy/RECORD-CORRECTION-REPORT.md",
   "what": "line 144 sha256 889033a5 -> cebea19e for blob afde67da, and the two CLONE-AND-LIVE-REPORT.md pins moved to its post-correction value 7c09a7ad with the old value preserved"
  },
  {
   "path": ".spec/bevy/TOTALS-CORRECTION-REPORT.md",
   "what": "this report (read by no test, build script or gate)"
  }
 ],
 "not_changed": [
  "evidence/index.json (byte-identical to the previous batch's revision; sha256 eb88286c...)",
  "src/** and tests/** (0 #[test] attributes touched; 806 listed before and after)",
  ".gitattributes and the evidence/** -text pin",
  "the liveness step, the battery, the coverage registry, config/hoh.yaml",
  "runs/** (nothing written or deleted)",
  ".spec/bevy/ACCEPTANCE-CLONE-LIVE.md, .spec/bevy/ACCEPTANCE-RECORD.md and the other acceptance records"
 ],
 "tests_that_read_the_files_this_batch_edited": {
  "evidence/README.md": "tests/evidence_reproduction.rs::the_evidence_index_names_committed_files_and_commands walks evidence/ and SKIPS README.md by name (it is not part of the corpus) and reads only its file name, never its bytes; the edit is byte-length-preserving, so even that walk's arithmetic is unchanged. No other test reads it.",
  ".spec/bevy/CLONE-AND-LIVE-REPORT.md": "no test, build script or gate reads it",
  ".spec/bevy/COVERAGE-EVIDENCE-REPORT.md": "no test reads it (tests/write_accounting.rs names it only inside an assertion's panic message text)",
  ".spec/bevy/RECORD-CORRECTION-REPORT.md": "no test reads it",
  "DECISIONS.md": "no test reads it"
 },
 "single_most_important_thing_next_batch": "The directory totals are still hand-stated and guarded by no test, so a one-line edit to any file under evidence/ can falsify them again: derive them in evidence/README.md/index.json and assert them in tests/evidence_reproduction.rs (risk R-5), or the next index edit repeats RD-1. For the immediate acceptance: the old wording that remains in COVERAGE-EVIDENCE-REPORT.md is quoted, labelled history, not a live claim, and the historical cross-references in RECORD-CORRECTION-REPORT.md (C-3, deliberately_not_corrected, section 6 item 2) and CLONE-AND-LIVE-REPORT.md section 4 are superseded by DECISIONS.md D308.",
 "prose_follows": true
}
```

# TOTALS-CORRECTION-REPORT — RD-1 (the evidence directory totals), RD-2 (one wrong sha256) and RD-3 (the liveness statements)

Independent, **offline** record correction on `bevy-core` at `05cff35`, authorised by the dispatcher after
`.spec/bevy/ACCEPTANCE-RECORD.md` returned **fail** on RD-1/RD-2/RD-3. **No engine, no game, no network, no
model call, no round and no Developer call was run.** Nothing was written under `runs/**`; no `git checkout --`
and no `rm -rf` was used (nothing was deleted); no key was created, copied or printed; nothing was committed or
pushed. Every helper script lives under `F:/hof-rd123-work/`, the logs under `F:/hof-rd123-logs/` and
`F:/hof-rd123-logs2/`, and the build under `F:/hof-rd123-target/` — all outside the repository. The
machine-readable block above is `json.dumps(..., indent=1, ensure_ascii=False)` output written by
`F:/hof-rd123-work/gen_report.py` and then **parsed back out of this written file**; that parse is the last
thing the generator does and it fails if the block does not round-trip.

## 0. The three corrections in one paragraph each

**RD-1 — the directory totals.** I measured both totals myself before changing anything, rather than adopting
the acceptance's numbers: `git ls-tree -r -l HEAD evidence` gives **122 files / 4,798,968 bytes**, and the four
files the corpus excludes are `index.json` 15,570 + `README.md` 4,073 + `tools/build_evidence.py` 4,731 +
`tools/keyscan.py` 3,455 = **27,829 bytes**. The **corpus is 118 files / 4,771,139 bytes and is unchanged** —
`index.json` was always excluded from it, which is exactly the distinction the previous batch missed. I chose to
**update the totals to the measured artefact** rather than shrink `evidence/index.json`'s corrected `meaning`
back by 719 bytes: that meaning is the substantive D-3 correction of a false claim, and trimming it to a byte
count would let the length of a paragraph dictate the record and would encode a hidden coupling between that
paragraph and four other files (risk R-5). Every edit made **inside** `evidence/` is byte-length-preserving
(`4,798,249 -> 4,798,968` and `27,110 -> 27,829` are equal-length substitutions), so the measured object did not
move while it was being described correctly. The totals were reconciled in `evidence/README.md`,
`.spec/bevy/CLONE-AND-LIVE-REPORT.md` (the E-7 machine-block `change` and section 4), `DECISIONS.md` D306(c)
(corrected in place under the explicit authorisation) and `.spec/bevy/COVERAGE-EVIDENCE-REPORT.md` (E-7, section
0, section 5 and the table row). The old numbers survive only in `.spec/bevy/ACCEPTANCE-CLONE-LIVE.md` and
`.spec/bevy/ACCEPTANCE-RECORD.md`, which are acceptance records of measurements that were true when taken; I did
not rewrite them, and ACCEPTANCE-RECORD.md itself carries them as the RD-1 defect description. Elsewhere the old
digits appear only in the appended `DECISIONS.md` D308 entry, as the values being replaced (old -> new); D306(c)'s
own statement now carries the corrected 4,798,968 / 27,829.

**RD-2 — one wrong sha256.** `RECORD-CORRECTION-REPORT.md` line 144 pinned `889033a5…` for blob `afde67da`,
which is `CLONE-AND-LIVE-REPORT.md`'s hash. `git cat-file -p afde67da | sha256sum` gives
`cebea19e0f955369a3a7fc8012f785c3f2d8939cde43208e5f7052af98f1d4e3`, which is now on that line. The other pins
were recomputed and hold: `evidence/index.json` = `eb88286c…` (this batch did not touch it),
`src/adapter/bevy/prd_surfaces.rs` = `6ea1090b…`. The third one needed a consequential fix: the RD-1 edit to
`CLONE-AND-LIVE-REPORT.md` moved that file's sha256 from `889033a5…` to `7c09a7ad…`, so the two places in
`RECORD-CORRECTION-REPORT.md` that pin it (`gate.gate_input_sha256` and the `changed_files` entry) were updated
to the new value with the old value preserved in the same text. **Leaving those two pins at `889033a5…` would
have been the exact RD-2 defect reproduced by the RD-2 fix**, which is why I went one line further than the
literal instruction and said so here. No test, build script or gate reads that file, so the gate numbers are
unaffected.

**RD-3 — the liveness statements.** `.spec/bevy/COVERAGE-EVIDENCE-REPORT.md` asserted in **12 places** that
`e3_process_liveness` had never run against a real game and that no `raw/e3_process_liveness.json` had ever been
produced. Those are now the truth — implemented, unit/fake-driver tested, **and since observed on a real game**
(the follow-up live round `clonefix1` ran the ten-step battery in all three iterations, persisted the raw file
each time and read `result.json.prd_coverage.surfaces` 15 verified / 0 gap / 4 unobservable of 19) — while the
old wording is preserved in each place as **falsified history**, and the E-2 defect narrative was not deleted.
Two counting notes: the acceptance's own reproduction command
(`git grep -n -e 'PENDING ITS FIRST REAL OBSERVATION' -e 'has ever been produced' -e 'never executed against a real game'`)
matches **5 lines / 6 occurrences** on HEAD, not the 13 hits its report states — the artefact wins, and I
corrected by meaning (12 sites), not by grep. After the edit, 3 lines / 4 occurrences of those strings remain,
all of them the quoted-and-labelled old wording.

## 1. What I verified, and how

* **The totals, from git and from the filesystem.** `git ls-tree -r -l HEAD evidence` -> 122 / 4,798,968; the
  four excluded blobs' sizes via `git cat-file -s`; then the same walk over the working tree with Python. Before
  and after the edits the working tree and HEAD agree, because every edit inside `evidence/` preserves byte
  length. The corpus 118 / 4,771,139 is unchanged, and the gate re-derives it green (section 2).
* **The hash, and the revision it names.** `git cat-file -t afde67da` is a blob; hashing its content gives
  `cebea19e…`. The delivered revision of `RECORD-CORRECTION-REPORT.md` and the four other files were hashed
  separately; every value pinned in the tree was recomputed rather than trusted.
* **The liveness claim, against the artefacts.** The round's own files are the authority: the three
  `runs/clonefix1/iter-{1,2,3}/candidate/.hoh/deterministic/raw/e3_process_liveness.json` files exist and are
  observed true, and I relied on the acceptance's and the previous batch's independent derivation of them (this
  batch ran no round and read no new artefact beyond what the record already rests on). The corrected sentences
  therefore cite the round, not a re-measurement.
* **The JSON block of each edited machine-readable file still parses** (`RECORD-CORRECTION-REPORT.md`,
  `COVERAGE-EVIDENCE-REPORT.md`, `CLONE-AND-LIVE-REPORT.md`, `ACCEPTANCE-RECORD.md` and `evidence/index.json`),
  because the edits went inside those blocks.
* **Scope.** `git diff --stat` over the delivered tree lists exactly the six files in `changed_files` above;
  `evidence/index.json`, `src/**`, `tests/**`, `.gitattributes`, `config/hoh.yaml` and `runs/**` are untouched.

## 2. The gate, on the frozen tree

Free space was checked first (F: 56 G, D: 180 G free), the build directory is this batch's own
(`F:/hof-rd123-target`), and `tasklist` found **no** `cargo`/`rustc`/`hoh` process before either run, so no
second test process existed. The gate was run twice and both runs report identical numbers; the second was made
after every edit except this report.

| check | command | literal exit code | result |
|---|---|---|---|
| full gate | `cargo test --offline` | **0** | **800 passed / 0 failed / 6 ignored** over 60 `test result:` lines |
| listing | `cargo test --offline -- --list` | **0** | **806** names |
| ignored | `cargo test --offline -- --list --ignored` | **0** | **6** names, the same six real-engine tests |
| formatting | `cargo fmt --all --check` | **0** | 0 bytes on stdout and stderr |
| warnings | both streams | - | **0** `warning:` lines |
| tests removed | `git diff -- src tests` | - | **0** `#[test]` attributes changed; 806 listed before and after |

**Which tests read the files I edited.** None of them reads any edited document's bytes. `evidence/README.md` is
inside `evidence/`, but the one test that walks that directory
(`tests/evidence_reproduction.rs::the_evidence_index_names_committed_files_and_commands`) **skips `README.md` by
name** and reads only its file name, never its content; the edit is byte-length-preserving, so even that walk's
arithmetic is unchanged, and the test that re-derives the corpus (118 / 4,771,139) and the index passes inside
the gate. `tests/write_accounting.rs` mentions `COVERAGE-EVIDENCE-REPORT.md` only inside an assertion's panic
message text. `CLONE-AND-LIVE-REPORT.md`, `COVERAGE-EVIDENCE-REPORT.md`, `RECORD-CORRECTION-REPORT.md`,
`DECISIONS.md` and this report are read by no test, build script or gate — which is also why a green gate cannot
catch a mistake in them, and why every figure above was reconciled by hand.

## 3. What is left, and the one thing for the next batch

The numbers now stated in the tree match the artefacts, and the historical records that carry the old numbers
are left intact as history rather than rewritten. One consequence is worth naming: `DECISIONS.md` D306(c) is no
longer a pure append, so the sentence in `COVERAGE-EVIDENCE-REPORT.md` section 8 that `DECISIONS.md` "is still
append-only" is a superseded historical claim, as are the cross-references in `RECORD-CORRECTION-REPORT.md`
(`C-3`, `deliberately_not_corrected`, `single_most_important_thing_next_batch`, section 6 item 2) and
`CLONE-AND-LIVE-REPORT.md` section 4 that say the coverage report was left as that batch wrote it. The
dispatcher's task scoped this batch to the three named corrections, so I did not rewrite those; `DECISIONS.md`
D308 replaces them. **The single most important thing for the next batch is that the directory totals are still
hand-stated and guarded by no test: a one-line edit to any file under `evidence/` can falsify them again, and
this is the second time it has happened. Derive them, or assert them in `tests/evidence_reproduction.rs`, before
the next acceptance has to find them by hand.**

**The artefact wins where a document disagrees with it** — that is the rule this batch applied to both the byte
totals and the liveness claim, and it is the rule the next reader should apply to the quoted history above.
