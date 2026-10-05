```json
{
 "schema": "hof-rs / bevy EFD-1 single repair: correct the false citation that the JSON key why_they_cannot_be_made_clone_safe is named in FINAL-DOC-REPORT.md's change_site; documents only, no code, test, evidence byte or measured figure changed",
 "produced_at": "2026-10-06",
 "branch": "bevy-core",
 "head_at_start": "91629f44333ec304dff5f611b4c51989830db136",
 "offline": true,
 "defect": {
  "id": "EFD-1",
  "source": ".spec/bevy/ACCEPTANCE-FD1.md, defects[0] (severity low)",
  "what": "The FD-1 repair's own record claimed the JSON key why_they_cannot_be_made_clone_safe was referenced by name in FINAL-DOC-REPORT.md's clone_safety_sentence.where AND change_site. change_site does not contain the name. The no-rename decision is sound; the stated support was false.",
  "stated_minimum_repair": "name FINAL-DOC-REPORT.md's clone_safety_sentence.where and ACCEPTANCE-FINAL-DOC.md as the references, and drop the change_site claim"
 },
 "key_name_occurrences": {
  "command": "git grep -c why_they_cannot_be_made_clone_safe",
  "literal_exit_code": 0,
  "counts": {
   ".spec/bevy/ACCEPTANCE-FD1.md": 7,
   ".spec/bevy/ACCEPTANCE-FINAL-DOC.md": 6,
   ".spec/bevy/FD1-REPORT.md": 8,
   ".spec/bevy/FINAL-DOC-REPORT.md": 1,
   ".spec/bevy/HARDENING-REPORT.md": 1,
   "DECISIONS.md": 4
  },
  "per_line_command": "grep -n why_they_cannot_be_made_clone_safe .spec/bevy/FINAL-DOC-REPORT.md",
  "final_doc_report_lines": [
   185
  ],
  "change_site_line": 195,
  "change_site_value": "\"change_site\": \"HARDENING-REPORT.md machine line 156, section 0 and section 3\"",
  "change_site_contains_the_name": false,
  "verdict": "In FINAL-DOC-REPORT.md the name occurs exactly once, at line 185 (clone_safety_sentence.where). change_site (line 195) does not name it. The name also occurs 6 times in ACCEPTANCE-FINAL-DOC.md. Both facts were re-established by this batch from the artefacts, not adopted from the acceptance.",
  "other_occurrences_are_not_citation_points": [
   "HARDENING-REPORT.md:156 is the key's own definition (the field name), not a reference to it",
   "FD1-REPORT.md:8 occurrences are this report's own subject",
   "ACCEPTANCE-FD1.md:7 and DECISIONS.md:4 are this acceptance and this correcting entry"
  ]
 },
 "citation_old_and_corrected": {
  "why_option_A": {
   "old": "FINAL-DOC-REPORT.md's `where`/`change_site` and the acceptance name that key, and renaming it",
   "new": "FINAL-DOC-REPORT.md's `clone_safety_sentence.where` (line 185) and `ACCEPTANCE-FINAL-DOC.md` (6 occurrences) name that key (`change_site` does not), and renaming it"
  },
  "RF-3_field_title": {
   "old": "the key is referenced by name in FINAL-DOC-REPORT.md (`clone_safety_sentence.where` and `change_site`) and in the acceptance itself;",
   "new": "the key is referenced by name in FINAL-DOC-REPORT.md's `clone_safety_sentence.where` (line 185) and in `ACCEPTANCE-FINAL-DOC.md` (6 occurrences) - `change_site` does not name it;",
   "note": "The same false claim occurs a THIRD time here (FD1-REPORT.md:139); EFD-1's what/reproduction and the dispatcher enumerated only why_option_A, section 2 and D311 option 3. It was corrected with the others because leaving it would leave the same false statement in a machine field of the same report."
  },
  "section_2": {
   "old": "`FINAL-DOC-REPORT.md`'s `clone_safety_sentence.where` and `change_site` and in the acceptance, and",
   "new": "`FINAL-DOC-REPORT.md`'s `clone_safety_sentence.where` (line 185) and six times in `ACCEPTANCE-FINAL-DOC.md` (`change_site` does not name it), and"
  },
  "DECISIONS_D311_option_3": {
   "old": "键名被 `FINAL-DOC-REPORT.md`（`where`/`change_site`）与验收报告按名引用",
   "disposition": "left byte-identical. DECISIONS.md is append-only, so correcting D311 in place was refused; a new entry D312 was appended that names D311's sentence and limits its wording."
  }
 },
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
  "ignored_list_literal_exit_code": 0,
  "fmt_command": "cargo fmt --all --check",
  "fmt_literal_exit_code": 0,
  "fmt_stdout_bytes": 0,
  "fmt_stderr_bytes": 0,
  "warning_colon_lines": 0,
  "no_failed_line": true,
  "tests_removed": 0,
  "hash_test_attribute_lines_worktree": 668,
  "hash_test_attribute_lines_head": 668,
  "own_build_dir": "D:/hof-efd1-target",
  "own_build_dir_size": "9.1 GiB",
  "gate_runs": 2,
  "runs_note": "The gate was run twice, sequentially, one test process at a time: once before this report existed and once on the final tree with it present (untracked; read by no test). Both runs measured identically - literal exit 0, 800 passed / 0 failed / 6 ignored over 60 test result lines, 806 listed, 6 ignored, fmt literal exit 0 with 0 bytes, 0 `warning:` lines. The second run recompiled nothing.",
  "fresh_build_evidence": "the target directory did not exist before the first run; that fresh run's stderr carried 169 `Compiling` lines and `Finished `test` profile [unoptimized + debuginfo] target(s) in 1m 21s`; D:/hof-efd1-target is 9.1 GiB",
  "free_disk_before_building": "F: 37 GiB free, D: 118 GiB free",
  "no_second_test_process": true,
  "starting_tree": "the tree this repair started from measured 800 passed / 0 failed / 6 ignored / 806 listed; the delivered tree measures the same"
 },
 "changed_files": [
  {
   "path": ".spec/bevy/FD1-REPORT.md",
   "change": "three in-line citation corrections (why_option_A, decisions_on_non_blocking_items.RF-3_field_title, section 2); no line added or removed",
   "numstat_vs_HEAD": "3 3"
  },
  {
   "path": "DECISIONS.md",
   "change": "D312 appended (18 insertions, 0 deletions), naming and limiting D311 option 3; D311 itself untouched",
   "numstat_vs_HEAD": "18 0"
  },
  {
   "path": ".spec/bevy/EFD1-REPORT.md",
   "change": "this report (new; read by no test, build script or gate)"
  }
 ],
 "not_changed": [
  "src/**, tests/**, config, .gitattributes (the line-ending pin), Cargo.toml, Cargo.lock, evidence/**, scripts/**, .githooks/** (git diff --name-only HEAD against them is empty)",
  "HARDENING-REPORT.md (including line 156 and its sha256 2893d496...) and FINAL-DOC-REPORT.md (including change_site at line 195)",
  "ACCEPTANCE-FD1.md and ACCEPTANCE-FINAL-DOC.md",
  "every measured figure: corpus 118 / 4,771,139, excluded 4 / 27,829, directory 122 / 4,798,968, the six recordings' 5,917,632 bytes",
  "no recording committed, added, copied or moved; no API key created, copied or printed; no round, engine, game, network or model call"
 ],
 "weak_statements_disposition": [
  {
   "id": "RF-6a",
   "statement": "FINAL-DOC-REPORT.md section 5 (line 329): \"The alternative's cost is now stated at all three sites\" - true only weakly, because section 0 states two of the three costs, not the evidence/-outside totals-guard escape.",
   "disposition": "left unchanged",
   "why": "correcting it means editing FINAL-DOC-REPORT.md, the very file this batch and FD1-REPORT.md's machine field not_changed declare unchanged (\"FINAL-DOC-REPORT.md itself is unchanged\"). The edit would falsify that sentence and cascade into a second edit; that is not as cheap or as isolated as the citation fix, and EFD-1's minimum repair does not ask for it."
  },
  {
   "id": "RF-6b",
   "statement": "HARDENING-REPORT.md:156, the SUPERSEDED label's bold span (the `**` delimiters render across the appended passage unlike the H-4 label).",
   "disposition": "left unchanged",
   "why": "editing line 156 changes its bytes and therefore its recorded sha256 2893d496152e475fa886b200fbb9bff8068f4dcfd0c6b25a68123d1bb1cecd6d, which is a measured figure recorded in FD1-REPORT.md's machine block and in ACCEPTANCE-FD1.md:20; the correction would turn those recorded figures into false ones and would require editing the committed acceptance record. Not as cheap or as verifiable as the citation fix."
  }
 ],
 "verified_myself": [
  "The key's name occurs in FINAL-DOC-REPORT.md exactly once, at line 185 (clone_safety_sentence.where), and change_site at line 195 is `HARDENING-REPORT.md machine line 156, section 0 and section 3`, which contains no such name - established with `git grep -c why_they_cannot_be_made_clone_safe` and `grep -n why_they_cannot_be_made_clone_safe .spec/bevy/FINAL-DOC-REPORT.md`, not read from EFD-1.",
  "The same false claim occurs in a THIRD place, FD1-REPORT.md:139 (decisions_on_non_blocking_items.RF-3_field_title), which neither EFD-1 nor the dispatcher enumerated.",
  "The three old fragments are present in HEAD:.spec/bevy/FD1-REPORT.md and absent from the worktree file; the three new fragments are present in it (asserted in the generator).",
  "DECISIONS.md is append-only: the old content is a byte-for-byte prefix of the new file (old 1,342,560 bytes / sha256 31014e76..., new 1,347,590 bytes, +5,030); git diff --numstat HEAD -- DECISIONS.md is `18 0`.",
  "The gate reproduces exactly: cargo test --offline LITERAL exit 0 with 800 passed / 0 failed / 6 ignored over 60 test result lines, 806 listed, 6 listed ignored (both literal exit 0), cargo fmt --all --check literal exit 0 with 0 bytes on both streams, 0 `warning:` lines, no FAILED, no panic, 668 #[test] lines in worktree and at HEAD, one test process at a time, fresh own build directory.",
  "No code, test, evidence, registry, battery, liveness, .gitattributes, config, Cargo or scripts path is in the diff; only .spec/bevy/FD1-REPORT.md and DECISIONS.md are modified (plus this new report)."
 ],
 "what_this_repair_did_not_do": "No engine, no game, no network, no model call, no round and no Developer call was run. Nothing was written under runs/** and no recording was committed, added, copied or moved. No rm -rf, no wildcard deletion and nothing deleted (free disk was sufficient: F: 37 GiB, D: 118 GiB). No path was built from an unexpanded variable; no git checkout --; no git add, commit, stage or push. Helper scripts live outside the repository under F:/hof-efd1-work/, logs under F:/hof-efd1-logs/, the build under D:/hof-efd1-target. No API key was created, copied or printed.",
 "single_most_important_thing_next_batch": "Do not treat a defect's enumerated list of places as the full set. EFD-1 named why_option_A, section 2 and D311 option 3; the identical false citation also sat in a machine field of the same report (RF-3_field_title, FD1-REPORT.md:139), and a correction scoped to the list would have left a false statement in the report's machine block. Re-derive every citation from the artefacts (git grep -c against the named key), and remember that line 156's recorded sha256 ties any future edit of that line to the FD1-REPORT.md machine block and ACCEPTANCE-FD1.md."
}
```

# EFD1-REPORT - the single EFD-1 repair: the false change_site citation

**Documents only, one defect, three in-line citation corrections and one appended decision entry.**
This batch repairs the one defect `.spec/bevy/ACCEPTANCE-FD1.md` recorded - **EFD-1** - and nothing
else. It was **offline**: no engine, no game, no network, no model call, no round and no Developer
call. No recording was committed, added, copied or moved; nothing was written under `runs/**`; no
measured figure changed; no code, test, `evidence/**`, registry, battery, liveness step,
`.gitattributes` pin, config or cost machinery was touched. No `rm -rf`, no wildcard deletion and
nothing deleted; no `git checkout --`; no path built from an unexpanded variable; no API key created,
copied or printed; nothing committed or pushed. Helper scripts live outside the repository under
`F:/hof-efd1-work/`, logs under `F:/hof-efd1-logs/`, the build under `D:/hof-efd1-target`. The
machine-readable block above is `json.dumps(..., indent=1, ensure_ascii=False)` output written by
`F:/hof-efd1-work/gen_report.py`, which then **parsed it back out of the written file** and refused
to finish unless it round-tripped equal.

## 0. The repair in one paragraph

EFD-1 is real and I reproduced it from the artefacts rather than from either the batch's or the
acceptance's wording. `git grep -c why_they_cannot_be_made_clone_safe` gives
`FINAL-DOC-REPORT.md:1`, `ACCEPTANCE-FINAL-DOC.md:6`, `HARDENING-REPORT.md:1` (the key's own
definition), `FD1-REPORT.md:8`, `ACCEPTANCE-FD1.md:7` and `DECISIONS.md` (4 after this entry); and
`grep -n why_they_cannot_be_made_clone_safe .spec/bevy/FINAL-DOC-REPORT.md` returns exactly line
**185**, the value of `clone_safety_sentence.where`. The `change_site` field at line 195 reads
`HARDENING-REPORT.md machine line 156, section 0 and section 3` and contains no such name. So the
decision to keep the key unrenamed stands on `where` plus `ACCEPTANCE-FINAL-DOC.md`; the claim that
`change_site` also names the key was false and is dropped. I corrected the citation in
`FD1-REPORT.md` at the two places EFD-1 named (`why_option_A`, section 2) **and at a third place
EFD-1 did not name** (`decisions_on_non_blocking_items.RF-3_field_title`), and - because
`DECISIONS.md` is append-only - I refused to edit D311 option 3 and appended **D312** to name and
limit it instead.

## 1. Where the key's name actually occurs (my own search)

`git grep -c why_they_cannot_be_made_clone_safe` (literal exit 0):

| file | occurrences | what they are |
|---|---|---|
| `.spec/bevy/FINAL-DOC-REPORT.md` | 1 | line 185, `clone_safety_sentence.where` - a genuine reference |
| `.spec/bevy/ACCEPTANCE-FINAL-DOC.md` | 6 | the acceptance that found FD-1 - genuine references |
| `.spec/bevy/ACCEPTANCE-FD1.md` | 7 | the acceptance that found EFD-1 |
| `.spec/bevy/FD1-REPORT.md` | 8 | the report being corrected (its own subject) |
| `.spec/bevy/HARDENING-REPORT.md` | 1 | line 156, the key's own definition |
| `DECISIONS.md` | 4 | D311 line 11716, D312 lines 11712/11716 |

`change_site` is **not** among the reference points. `grep -n why_they_cannot_be_made_clone_safe
.spec/bevy/FINAL-DOC-REPORT.md` returns only `185:`; `sed -n '195p' .spec/bevy/FINAL-DOC-REPORT.md`
returns `  "change_site": "HARDENING-REPORT.md machine line 156, section 0 and section 3"`.

## 2. What was changed

* **`.spec/bevy/FD1-REPORT.md` (3 insertions / 3 deletions, no line added or removed).** The old
  citation and the corrected one, in each of the three places:

  1. `why_option_A` (line 14). **Old:** *FINAL-DOC-REPORT.md's `where`/`change_site` and the
     acceptance name that key*. **New:** *FINAL-DOC-REPORT.md's `clone_safety_sentence.where`
     (line 185) and `ACCEPTANCE-FINAL-DOC.md` (6 occurrences) name that key (`change_site` does
     not)*.
  2. `decisions_on_non_blocking_items.RF-3_field_title` (line 139) - **the place EFD-1 did not
     enumerate.** **Old:** *the key is referenced by name in FINAL-DOC-REPORT.md
     (`clone_safety_sentence.where` and `change_site`) and in the acceptance itself*. **New:** *the
     key is referenced by name in FINAL-DOC-REPORT.md's `clone_safety_sentence.where` (line 185)
     and in `ACCEPTANCE-FINAL-DOC.md` (6 occurrences) - `change_site` does not name it*.
  3. Section 2, the RF-3 paragraph (line 240). **Old:** *...`clone_safety_sentence.where` and
     `change_site` and in the acceptance...*. **New:** *...`clone_safety_sentence.where` (line 185)
     and six times in `ACCEPTANCE-FINAL-DOC.md` (`change_site` does not name it)...*.

  Line numbers are unchanged, so the acceptance's own references to lines 14 and 239-240 still
  point at the corrected text.

* **`DECISIONS.md` (18 insertions / 0 deletions).** D311 option 3 keeps the false citation
  verbatim; the file is append-only (`git diff --numstat HEAD -- DECISIONS.md` is `18 0`, and the
  old content is a byte-for-byte prefix of the new file: 1,342,560 -> 1,347,590 bytes). **D312** is
  appended and does the correcting: it names D311 option 3's sentence and limits it, records the
  real reference points, states that `RF-3_field_title` is the same false claim, and records the
  disposition of the two weak statements.

## 3. The two weak statements: left, with reasons

Neither is a defect, and neither is as cheap or as verifiable as the citation fix, so both are left
exactly as they were.

* **"stated at all three sites" (`FINAL-DOC-REPORT.md:329`, prose section 5).** True only weakly -
  section 0 states two of the three costs. Correcting it means editing `FINAL-DOC-REPORT.md`, the
  file `FD1-REPORT.md`'s `not_changed` field and this batch both declare unchanged; the edit would
  make *that* sentence false and cascade. Out of the minimum repair.
* **The SUPERSEDED label's bold span (`HARDENING-REPORT.md:156`).** Correcting the `**` delimiters
  changes line 156's bytes, and its sha256 `2893d496...` is a recorded figure in `FD1-REPORT.md`'s
  machine block and `ACCEPTANCE-FD1.md:20`. The fix would falsify recorded hashes and require
  editing the committed acceptance. Not cheap, not verifiable in the required sense.

## 4. The gate

On the delivered tree, in this batch's own `D:/hof-efd1-target` (fresh, 169 `Compiling` lines,
`Finished` in 1m 21s), one test process at a time, free disk checked first (F: 37 GiB, D: 118 GiB),
and nothing deleted. The gate was run twice, sequentially, with identical results: once before this
report existed, once on the final tree with it present (untracked; read by no test); the second run
recompiled nothing.

* `cargo test --offline` -> **literal exit code 0**, **800 passed / 0 failed / 6 ignored** over
  **60** `test result:` lines; 0 `FAILED`, 0 panic.
* `cargo test --offline -- --list` -> literal exit 0, **806** listed; `-- --list --ignored` ->
  literal exit 0, **6** listed ignored.
* `cargo fmt --all --check` -> **literal exit 0** with **0 bytes** on stdout and stderr.
* **0** `warning:` lines across all four streams; `#[test]` lines **668** in the worktree and
  **668** at `HEAD` - no test removed.

This is identical to the starting measurement (800 / 0 / 6 / 806).

## 5. The single most important thing for the next batch

**Do not treat a defect's enumerated list of places as the full set.** EFD-1 - and the task built
from it - named `why_option_A`, section 2 and D311 option 3. The identical false citation also sat
in a machine field of the same report, `RF-3_field_title` (`FD1-REPORT.md:139`), and a correction
scoped to the stated list would have left a false statement in the very machine block this line of
batches exists to keep honest. Every citation should be re-derived from the artefacts - a
`git grep -c` against the named string - rather than trusted from a list. Whatever the next batch
does with `HARDENING-REPORT.md:156`, note that its recorded sha256 ties any edit of that line to the
`FD1-REPORT.md` machine block and `ACCEPTANCE-FD1.md:20`, so the label's cosmetic span stays for
the same reason it is recorded. The open goal criterion remains **cost** (2.600x / 2.549x / 2.604x
of the 1,500,000-token per-call target with `agent.step_limit: 150` binding), which needs a human
decision, not another document.
