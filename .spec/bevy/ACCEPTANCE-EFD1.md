```json
{
 "verdict": "fail",
 "schema": "hof-rs / bevy independent acceptance of the EFD-1 single repair (.spec/bevy/EFD1-REPORT.md), base 91629f4, judged at 6b66da6; EFD-1 is closed and the tree is sound, but the new record carries one fresh false statement about where the key's name occurs, which is the class this cycle exists to close",
 "produced_at": "2026-10-06",
 "branch": "bevy-core",
 "head_under_acceptance": "6b66da67b4a95fe77330b791aebfbb4d6a02a53f (`docs(efd1): cite the fields that really name the key and catch the same claim in an unlisted one`), whose parent 91629f44333ec304dff5f611b4c51989830db136 is the revision EFD1-REPORT.md names as head_at_start",
 "origin_bevy_core": "166212f1fc4f2e520170e19b894b28501a58235d - the whole unpushed range (ef2b0d6..6b66da6, seven commits) is unpushed and nothing was pushed by this acceptance",
 "offline": true,
 "summary": "EFD-1 is genuinely closed. I re-derived the claim from the artefacts, not from the acceptance or the batch: `git grep -c why_they_cannot_be_made_clone_safe` gives FINAL-DOC-REPORT.md 1, ACCEPTANCE-FINAL-DOC.md 6, ACCEPTANCE-FD1.md 7, FD1-REPORT.md 8, HARDENING-REPORT.md 1, DECISIONS.md 4 (EFD1-REPORT.md now has 9 because the report itself is tracked); `grep -n` in FINAL-DOC-REPORT.md returns only line 185 (`clone_safety_sentence.where`) and line 195 (`change_site`) reads `HARDENING-REPORT.md machine line 156, section 0 and section 3` and contains no such name. The three corrected places in FD1-REPORT.md (lines 14, 139, 240) now name `where` (line 185) and ACCEPTANCE-FINAL-DOC.md and say `change_site` does not name it; the third place (139) is the one EFD-1 did not enumerate, and the batch was right that the defect's list was not the full set. The only place that still carries the false claim verbatim is DECISIONS.md D311 option 3 (line 11716), which the batch left byte-identical under the log's append-only convention and named and limited with the appended D312 (lines 11728-11744); I verified D311's whole block is byte-identical between a80db33 and the delivered HEAD and that DECISIONS.md is a byte-for-byte superset (prefix) of its content at 91629f4, a80db33 and origin/bevy-core. The gate reproduces exactly (literal exit 0, 800 passed / 0 failed / 6 ignored over 60 test result lines, 806 listed, 6 ignored, fmt exit 0 with 0 bytes, 0 `warning:` lines, no test removed at 668 `#[test]` lines), the repair is documents-only (three document paths, nothing under src, tests, evidence, config, .gitattributes, Cargo.*, scripts or .githooks), the tree is fit for a push (ledger, identity, tripwire, fold, resume and battery coherent and green; frozen documents byte-identical; one declared key-shaped fixture in 330 tracked files; two key-shaped files present but gitignored under runs/). I nevertheless return FAIL on one low-severity item: EFD1-REPORT.md's own search table (line 181) states that the key's name occurs in `D312 lines 11712/11716`, which attributes the occurrences to the wrong entry and omits D312's real lines (11731 and 11735) - a fresh false statement about where a tracked document carries the name, undisclosed, in the report written to close exactly that class of error. Everything else the batch claims reproduces.",
 "criteria": [
  {
   "id": "efd1-references-established-from-the-artefacts",
   "pass": true,
   "evidence": "My own `git grep -c why_they_cannot_be_made_clone_safe` (literal exit 0): .spec/bevy/FINAL-DOC-REPORT.md 1, .spec/bevy/ACCEPTANCE-FINAL-DOC.md 6, .spec/bevy/ACCEPTANCE-FD1.md 7, .spec/bevy/FD1-REPORT.md 8, .spec/bevy/HARDENING-REPORT.md 1, DECISIONS.md 4, .spec/bevy/EFD1-REPORT.md 9 (the batch's count omitted its own report because the report was untracked when it measured, which is consistent). `grep -n why_they_cannot_be_made_clone_safe .spec/bevy/FINAL-DOC-REPORT.md` returns exactly `185:` - the value of `clone_safety_sentence.where` - and `sed -n '195p'` returns `  \"change_site\": \"HARDENING-REPORT.md machine line 156, section 0 and section 3\"`, which contains no such name. So HARDENING-REPORT.md:156 is the key's own definition, FINAL-DOC-REPORT.md:185 is the one genuine reference there, and ACCEPTANCE-FINAL-DOC.md's six occurrences are genuine references. The batch's key_name_occurrences counts, its line-185/line-195 facts and its change_site_contains_the_name=false all re-derive."
  },
  {
   "id": "efd1-three-citations-corrected",
   "pass": true,
   "evidence": "The three old fragments are present in `git show 91629f4:.spec/bevy/FD1-REPORT.md` and absent from the worktree file; the three new fragments (which name `clone_safety_sentence.where` (line 185) and `ACCEPTANCE-FINAL-DOC.md` and state that `change_site` does not name the key) are present in the worktree file - asserted by my own substring comparison of all six fragments against the file at 91629f4 and the worktree (all six checks as claimed). Line numbers are unchanged: FD1-REPORT.md is 258 lines at 91629f4 and 258 now, and `git diff --numstat 91629f4 6b66da6` gives `3 3` for it, so the acceptance's references to lines 14 and 239-240 still point at the corrected text. The third place (line 139, `decisions_on_non_blocking_items.RF-3_field_title`) is the one EFD-1 did not enumerate, and it now carries the corrected sentence."
  },
  {
   "id": "efd1-no-other-place-carries-the-claim",
   "pass": true,
   "evidence": "I searched every tracked document for `change_site` and for the key name and classified every co-occurrence. The only place that still asserts the key is named in `change_site` is DECISIONS.md:11716 (D311 option 3, `键名被 FINAL-DOC-REPORT.md（where/change_site）与验收报告按名引用`), left byte-identical on purpose; every other occurrence is either the corrected text, a true statement of `change_site`'s value, or a quotation of the old text as labelled history (ACCEPTANCE-FD1.md and EFD1-REPORT.md quote it as the defect; FINAL-DOC-REPORT.md:195 is the field's value; ACCEPTANCE-FINAL-DOC.md:30 and :58 describe the field and the correction diff). D312 (DECISIONS.md:11728-11744) names that sentence, calls it 失实, records the real reference points and states that RF-3_field_title is the same false claim. So the false claim survives in exactly one place, disclosed and limited one entry later - see RF-2. The batch's disposition of D311 in EFD1-REPORT.md matches what the bytes show."
  },
  {
   "id": "left-statements-reasons-true",
   "pass": true,
   "evidence": "RF-6b's reason reproduces: `sed -n '156p' .spec/bevy/HARDENING-REPORT.md | sha256sum` is 2893d496152e475fa886b200fbb9bff8068f4dcfd0c6b25a68123d1bb1cecd6d, which equals FD1-REPORT.md's `line_156_sha256.worktree_after` (machine block line 61) and the value recorded in ACCEPTANCE-FD1.md:20; the file hashes to bd373b30fcd0da76a264377674962f10ac2ba4c9fa1122631075c47e774c04ac at a80db33, 91629f4, 6b66da6 and in the worktree, so any edit of line 156 changes pinned bytes and would falsify a recorded figure without editing a committed acceptance record - the reason is true, and leaving the cosmetic span is more honest than falsifying the pin. RF-6a's reason also reproduces in its own terms: `FD1-REPORT.md:128` says `FINAL-DOC-REPORT.md itself is unchanged: option A makes its three-site claim true of the delivered tree`, so editing FINAL-DOC-REPORT.md would make that recorded declaration false. No hash pins FINAL-DOC-REPORT.md's bytes, so RF-6a rests on the declaration rather than on a hash - true as stated. Whether the two statements themselves are accurate is a separate matter; see RF-4 and RF-5."
  },
  {
   "id": "append-only-log",
   "pass": true,
   "evidence": "The new entry D312 (DECISIONS.md:11728-11744) does what the batch claims: it records EFD-1, states the two real reference points, states that `change_site` does not name the key, states that `RF-3_field_title` (FD1-REPORT.md:139) is the same false claim, refuses to edit D311 and refuses to rename the key, and records the disposition of the two weak statements. The entry it corrects was not edited: D311's whole block (file lines 11709-11726 at a80db33) is byte-identical at the delivered HEAD, including option 3 at line 11716. The log is append-only across the diff: DECISIONS.md's bytes at 91629f4 (1,342,560, sha256 31014e76...) are a byte-for-byte prefix of the delivered file (1,347,590), `git diff --numstat 91629f4 6b66da6 -- DECISIONS.md` is `18 0`, and the same prefix property holds against a80db33 and origin/bevy-core. The batch's own byte counts and the 31014e76... prefix hash re-derive."
  },
  {
   "id": "no-over-reach",
   "pass": true,
   "evidence": "`git diff --name-status 91629f4 6b66da6` is exactly three document paths: A .spec/bevy/EFD1-REPORT.md (259/0), M .spec/bevy/FD1-REPORT.md (3/3), M DECISIONS.md (18/0). `git diff --name-only {91629f4,6b66da6} -- src tests config .gitattributes Cargo.toml Cargo.lock evidence scripts .githooks` is empty for both, so no code, test, evidence byte, registry, battery, liveness step, line-ending pin, config, Cargo file or script is in the diff, and no measured figure moved (the diff does not touch evidence/ or any pinned value). No recording was committed, added, copied or moved: `git ls-files runs` is empty and both key-shaped files remain ignore-matched by `.gitignore:9 runs/`."
  },
  {
   "id": "gate-reproduced",
   "pass": true,
   "evidence": "Free disk checked before building: F: 37 GiB and D: 109 GiB free; no cargo/rustc/hoh process was running; NOTHING WAS DELETED - no `rm -rf`, no wildcard, no path built from an unexpanded variable, and no space needed freeing. My own fresh build directory D:/hof-efd1acc2-target (9.1 GiB measured with `du -sh`, 169 `Compiling` lines on stderr, `Finished \\`test\\` profile [unoptimized + debuginfo] target(s) in 1m 20s`), one test process at a time. Literal exit codes read from files written by the script: `cargo test --offline` -> 0; `cargo test --offline -- --list` -> 0; `-- --list --ignored` -> 0; `cargo fmt --all --check` -> 0 with 0 bytes on stdout and stderr. Counts: 800 passed / 0 failed / 6 ignored over 60 `test result:` lines, all `ok`; 806 listed names (my own count of lines ending `: test`), 6 listed ignored; 0 lines containing `warning:` in either stream; 0 FAILED lines; 0 panics. Equal to the previous baseline (800 / 0 / 6 / 806)."
  },
  {
   "id": "no-test-removed",
   "pass": true,
   "evidence": "`^\\s*#\\[test\\]` lines over `git ls-files src tests`: 668 in the worktree, 668 at 91629f4, 668 at origin/bevy-core - identical. The listing is 806 and the run 800/0/6, the same as the recorded baseline the reports state, and the diff to the judged revision touches no file under src/ or tests/."
  },
  {
   "id": "tree-for-push",
   "pass": true,
   "evidence": "Launch ledger evidence/observation/round4/round/launch-ledger.jsonl: my own parse gives 7 lines, 7 distinct nonces, 7 distinct pids, 7 distinct launch images, no line carrying `answered_nonce` or `listening_pid`; the penultimate line (nonce faf2adda-c698-48ef-a4f5-f51d1da551c6, pid 47624) matches launch.json's identity block exactly - spawned_pid = listening_pid = answering_pid = 47624, same launch image, same endpoint, `verified: true` - re-derived myself. The mechanism tests are in the 806 and green in my gate: `adapter::bevy::round::tests::the_identity_fields_are_computed_from_the_facts_not_asserted`, the `harness::guard` repeated-action/tripwire tests and `the_repeated_success_tripwire_fires_on_the_recorded_grind`, the `harness::compact` fold tests and `the_context_fold_shrinks_every_recorded_round_four_developer_call`, all 7 `a_resume_*` tests, all 21 `adapter::bevy::battery::tests`, and the credential-scan tests (`no_key_shaped_material_is_browsable_in_the_repository_tree` and four more, all ok). Key-shaped material: my own five-pattern scan of all 330 tracked files finds the `sk-` shape only in the declared fixture tests/credential_scan.rs, and no tracked .env/.key/.pem/secret file. Two key-shaped files exist outside the tracked tree - runs/round1/iter-1/traj/developer.attempt1.json and runs/round1b/iter-1/traj/tester.attempt1.json - both present on disk, both ignore-matched by `.gitignore:9 runs/` (`git check-ignore -v`), and both therefore outside the push; I did not print their contents. Frozen documents (REQUIREMENTS.md, PRD.md, DESIGN-OVERVIEW.md, DESIGN-DETAIL.md, SPIKE-1-REPORT.md, SPIKE-2-REPORT.md) are byte-identical at 4a85269, 91629f4, 6b66da6 and in the worktree. My own read-only walk of evidence/ re-derives the three measured totals exactly - corpus 118 files / 4,771,139 bytes, excluded 4 / 27,829 (index.json 15,570 + README.md 4,073 + tools/build_evidence.py 4,731 + tools/keyscan.py 3,455), directory 122 / 4,798,968, with the identity holding, 0 CR bytes across all 122 files and evidence/README.md still stating `122 files / 4,798,968 bytes`. `.spec/` contains only `bevy`, `src/adapter/` only `bevy` and `mcp` (no second engine), `evidence/` only this engine's index/README/cost/observation/tools. The working tree is clean (`git status --porcelain` empty before I wrote this report); HEAD is 6b66da6 and origin/bevy-core is still 166212f; I staged, committed and pushed nothing."
  },
  {
   "id": "record-carries-no-fresh-false-statement",
   "pass": false,
   "evidence": "EFD1-REPORT.md's section 1 table (line 181) says of DECISIONS.md: `D311 line 11716, D312 lines 11712/11716`. That is false about what the document contains. The key's name occurs in DECISIONS.md at lines 11712 and 11716, which belong to D311 (whose block spans 11709-11726), and at lines 11731 and 11735, which belong to D312 (11728-11744); none of D312's occurrences is on 11712 or 11716, and the note omits both of D312's real lines while mentioning only one of D311's two. It is also internally inconsistent with the count it annotates (4). This is a fresh, undisclosed false statement about where a tracked document carries the key's name - the H-2/RD-2 class this cycle exists to close, in the report that closes it. Defect EFD2-1."
  }
 ],
 "defects": [
  {
   "id": "EFD2-1",
   "severity": "low",
   "what": "EFD1-REPORT.md line 181 annotates the DECISIONS.md row of its own search table as `D311 line 11716, D312 lines 11712/11716`. Lines 11712 and 11716 are D311's two occurrences; D312's two occurrences are at 11731 and 11735 and are not named. A reader using the table - whose heading is `Where the key's name actually occurs (my own search)` - to locate the residual occurrence of the false claim in the log is given the wrong entry for those line numbers and is not given D312's real lines. It is a false statement about what a tracked document contains, undisclosed, in the batch report, and it contradicts its own occurrence count of 4 (the note names three lines).",
   "reproduction": "`grep -n why_they_cannot_be_made_clone_safe DECISIONS.md` returns `11712:`, `11716:`, `11731:`, `11735:`. `sed -n '11709,11726p'` shows lines 11712 and 11716 inside D311 (heading at 11709); `sed -n '11728p'` shows D312's heading and its occurrences are two lines further in at 11731 and 11735. Compare `sed -n '181p' .spec/bevy/EFD1-REPORT.md` -> `| \\`DECISIONS.md\\` | 4 | D311 line 11716, D312 lines 11712/11716 |`. The machine block's own count for DECISIONS.md is correct (4); only the prose annotation is wrong."
  }
 ],
 "risks": [
  {
   "id": "RF-1",
   "risk": "The cost criterion remains unmet and is expected to stay unmet pending a human decision: the recorded 2.600x / 2.549x / 2.604x of the 1,500,000-token per-call target, every Developer call ended by `agent.step_limit: 150` with the repeated-success tripwire never firing. It is recorded as unmet rather than fixed, and no round or Developer call was run or attempted by this acceptance."
  },
  {
   "id": "RF-2",
   "risk": "DECISIONS.md:11716 (D311 option 3) still carries the false claim verbatim. The batch left it byte-identical under the log's append-only convention and limited it with D312 one entry later; I verified both the byte-identity and the limitation. A reader who reads D311 and stops is still misled, so the residual is real but disclosed; editing D311 in place would break the append-only property the same records rely on."
  },
  {
   "id": "RF-3",
   "risk": "The new record cites `HEAD` for the batch's own diff, and the dispatcher's commit moved HEAD past the write: EFD1-REPORT.md's `numstat_vs_HEAD` fields (lines 93, 98) and its prose at line 209 (`git diff --numstat HEAD -- DECISIONS.md` is `18 0`) and D312's parenthetical at DECISIONS.md:11738 (`git diff --numstat a80db33 HEAD -- DECISIONS.md` 为空) no longer reproduce against the delivered HEAD - the worktree is clean so the first two are empty, and the third is `18 0`. The batch pins its starting revision (`head_at_start: 91629f4`), and every substantive claim behind those commands (append-only, 3/3 and 18/0 against 91629f4) is verified true by me, so this is a stale citation rather than a false finding; but a reader running the commands literally will not see the quoted result."
  },
  {
   "id": "RF-4",
   "risk": "RF-6b's premise is not supported by the bytes it describes. EFD1-REPORT.md:121 repeats ACCEPTANCE-FD1.md's RF-6 as `the SUPERSEDED label's bold span (the ** delimiters render across the appended passage unlike the H-4 label)`. The two labels close identically: HARDENING-REPORT.md:156 renders `...FD1-REPORT.md\\`:** the sentence above...` and RECORD-CORRECTION-REPORT.md's H-4 label renders `...DECISIONS D308:** the authorisation asked...`, both a single `:**` closer; and both labels sit inside the leading ```json fenced block of their report, so neither renders as prose at all. The disposition (leave it, because editing the line falsifies its recorded sha256) is sound regardless, and the item is cosmetic."
  },
  {
   "id": "RF-5",
   "risk": "RF-6a stands as a weak statement: FINAL-DOC-REPORT.md:329 says `The alternative's cost is now stated at all three sites`, while HARDENING-REPORT.md section 0 (line 223) states two of the three costs (the evidence-budget decision and the `runs/**` key-shaped material) and not the `evidence/`-outside totals-guard escape; sections 3 and the machine field state all three. It is left in place with the reason recorded (editing it would falsify FD1-REPORT.md's `not_changed` declaration), and it does not bear on any conclusion."
  },
  {
   "id": "RF-6",
   "risk": "The five clone-weak tests remain clone-weak: in a tree without runs/round1b, runs/round2 and runs/round3 they assert nothing, so a clone's identical 800/0/6 is weaker than this tree's. This is the disclosed, deliberately uncommitted boundary carried forward from the earlier acceptances."
  },
  {
   "id": "RF-7",
   "risk": "ACCEPTANCE-TOTALS.md (a dated acceptance record) still states in the present tense that the evidence totals are guarded by no test and that both pins now state 7c09a7ad; both are false of the tree since the R-A1 and H-1 corrections. Inherited and unchanged by this batch, as recorded in FD1-REPORT.md's decisions_on_non_blocking_items and ACCEPTANCE-FD1.md's RF-3."
  }
 ],
 "unverified": [
  "A real `git clone`; I did not clone the repository and did not re-run a clone gate. I verified `git ls-files runs` is empty, the ignore rules for the two key-shaped files, the frozen documents and the working-tree gate instead.",
  "A Linux or macOS checkout, where core.autocrlf is false by default; I checked the line-ending question only through `.gitattributes` (unchanged by this diff) and the LF content of the documents I diffed, not by a cross-platform run.",
  "An audit of all 800 passing tests for clone-safety; I confirmed the named mechanism tests are present and green, not that every test asserts something in a clone.",
  "The cost figures beyond reading the reports: no round, engine, game, network or model call was made or attempted, so 2.600x / 2.549x / 2.604x is adopted from the recorded usage figures, not re-measured.",
  "The batch's own build log, timestamps and physical disk state at the instant its gate ran (its D:/hof-efd1-target, 169 Compiling lines, 1m 21s); my gate is my own run in D:/hof-efd1acc2-target.",
  "Every number in the previous batch reports other than the ones I recomputed myself: the pins and line/file hashes other than line 156's and the DECISIONS.md prefix hash, the six recording sizes and their 5,917,632-byte sum, the three evidence totals, and the D309 history.",
  "The markdown rendering of the two SUPERSEDED labels: I compared their delimiter bytes and their fenced context, but I did not run a CommonMark renderer over them, so RF-4 states what the bytes support rather than a rendered result.",
  "No tamper/plant experiment was run: none of the checks I was asked for required modifying a file, so no copy, restore or restamped timestamp exists in this acceptance."
 ],
 "what_this_acceptance_did_not_do": "No engine, no game, no network, no model call, no round and no Developer call was run. Nothing was written under runs/**. No `rm -rf`, no wildcard deletion and nothing deleted - free disk was sufficient (F: 37 GiB, D: 109 GiB) and no space was freed. No path was built from an unexpanded variable; no `git checkout --`; no `git add`, commit, stage or push. Helper scripts live outside the repository under F:/hof-efd1acc2-work/, logs under F:/hof-efd1acc2-logs/, the build under D:/hof-efd1acc2-target (9.1 GiB). The only file written inside the repository is this report. No API key was created, copied or printed; the two key-shaped run-directory files were reported by path and status only, never printed."
}
```


# ACCEPTANCE-EFD1 - independent acceptance of the EFD-1 single repair

Independent, **offline** acceptance of the batch delivered as `.spec/bevy/EFD1-REPORT.md`, judged at
**`bevy-core` / `6b66da6`** (base `91629f4`, the acceptance record that found EFD-1; `origin/bevy-core`
is still `166212f`, so the whole unpushed range `ef2b0d6..6b66da6` - seven commits - is unpushed and
nothing was pushed by me). No engine, no game, no network, no model call, no round and no Developer
call; nothing under `runs/**` written; no `rm -rf`, no wildcard deletion and nothing deleted; no
`git checkout --`; no commit, stage or push; no path built from an unexpanded variable. Helper scripts
live outside the repository under `F:/hof-efd1acc2-work/`, logs under `F:/hof-efd1acc2-logs/`, my
build under `D:/hof-efd1acc2-target`. I ran no tamper/plant experiment because none of the checks
needed one. The machine-readable verdict above is `json.dumps(..., indent=1, ensure_ascii=False)`
output written by `F:/hof-efd1acc2-work/gen_report.py`, which then **parsed it back out of the written
file** and required it to round-trip equal.

## 0. The verdict in one paragraph

**EFD-1 is genuinely closed and the tree is fit for a push, but the repair's own report carries one
fresh false statement, so I return fail on that alone.** I re-derived every fact from the artefacts:
the key's name occurs once in `FINAL-DOC-REPORT.md` (line 185, `clone_safety_sentence.where`) and its
`change_site` (line 195) does not name it; the three corrected places in `FD1-REPORT.md` - including
`RF-3_field_title` at line 139, which EFD-1 did not enumerate - now cite `where` and
`ACCEPTANCE-FINAL-DOC.md` and say `change_site` does not name the key. The one place that still carries
the false claim verbatim is `DECISIONS.md` D311 option 3 (line 11716); D311's whole block is
byte-identical between `a80db33` and the delivered HEAD, `DECISIONS.md` is a byte-for-byte prefix of
itself at `91629f4`, `a80db33` and `origin/bevy-core` (`18 0` in the repair diff), and the appended
D312 (11728-11744) names and limits the sentence - the append-only instrument this log has used
before. The repair is documents-only (three document paths; nothing under `src`, `tests`, `evidence`,
`config`, `.gitattributes`, `Cargo.*`, `scripts` or `.githooks`), and the gate reproduces exactly:
**literal exit 0, 800 passed / 0 failed / 6 ignored over 60 `test result:` lines, 806 listed, 6
ignored, `cargo fmt --all --check` exit 0 with 0 bytes, 0 `warning:` lines, no test removed** (668
`#[test]` lines at both revisions). The tree is sound: the round-4 launch ledger's penultimate line is
`launch.json`'s identity (pid 47624, nonce `faf2adda...`, `verified: true`), the identity, tripwire,
fold, resume (7) and battery (21) tests are green in the 806, the six frozen documents are
byte-identical, the only key-shaped material in the 330 tracked files is the declared fixture, and the
two key-shaped files that exist are gitignored under `runs/`. **The one blocker is EFD2-1:** the
report's own search table (line 181) says the key's name occurs in `D312 lines 11712/11716`, which
attributes D311's lines to D312 and omits D312's real lines (11731, 11735) - a false statement about
what a tracked document contains, undisclosed, in the report written to close exactly that class of
error. Everything else the batch claims reproduces, and the fix is one table cell.

## 1. Per-item results

| # | item | result | the evidence I gathered myself |
|---|---|---|---|
| 1 | EFD-1: where the key's name really occurs | **pass** | `git grep -c why_they_cannot_be_made_clone_safe`: FINAL-DOC-REPORT.md 1, ACCEPTANCE-FINAL-DOC.md 6, ACCEPTANCE-FD1.md 7, FD1-REPORT.md 8, HARDENING-REPORT.md 1, DECISIONS.md 4, EFD1-REPORT.md 9 (itself). `grep -n` in FINAL-DOC-REPORT.md returns only 185; line 195 `change_site` contains no such name. |
| 2 | the three corrected citations | **pass** | The three old fragments are in `git show 91629f4:.spec/bevy/FD1-REPORT.md` and absent from the worktree; the three new fragments are present. Lines 14, 139, 240; `numstat` `3 3`, file 258 lines at both revisions, so the acceptance's line references still hold. Line 139 is the place EFD-1 did not list. |
| 3 | no other place still carries the claim | **pass, with RF-2** | Only `DECISIONS.md:11716` (D311 option 3) still asserts it, verbatim, left on purpose; D312 names it as 失实, gives the real reference points and pins `RF-3_field_title`. Every other `change_site`/key co-occurrence is the corrected text, a true statement of the field's value, or a labelled quotation of the old text. |
| 4 | the two left statements' reasons | **pass, with RF-4/RF-5** | Line 156's sha256 is `2893d496...`, exactly the value recorded in FD1-REPORT.md's machine block (`line_156_sha256.worktree_after`) and in ACCEPTANCE-FD1.md:20, so an edit would falsify a recorded figure; the file's hash is `bd373b30...` at a80db33, 91629f4, 6b66da6 and in the worktree. RF-6a's reason is `FD1-REPORT.md:128`'s `FINAL-DOC-REPORT.md itself is unchanged` declaration, which exists as stated (no hash pins that file). |
| 5 | the append-only log | **pass** | D312 does what the batch claims; D311's block (11709-11726 at a80db33) is byte-identical at HEAD, option 3 included; DECISIONS.md at 91629f4 is a byte-for-byte prefix of the delivered file (1,342,560 / sha256 `31014e76...` -> 1,347,590; `numstat` `18 0`), and the prefix property also holds against `a80db33` and `origin/bevy-core`. |
| 6 | no over-reach | **pass** | `git diff --name-status 91629f4 6b66da6` = A `EFD1-REPORT.md`, M `FD1-REPORT.md` (3/3), M `DECISIONS.md` (18/0). The restrictive-path diff is empty against both revisions; no pinned value or evidence byte moves; no recording committed (`git ls-files runs` empty). |
| 7 | the gate | **pass** | Free disk first (F: 37 GiB, D: 109 GiB); nothing deleted, no `rm -rf`, no wildcard, no unexpanded-variable path; own fresh `D:/hof-efd1acc2-target` (9.1 GiB, 169 `Compiling` lines, 1m 20s); one test process. Literal exit 0 for test / list / list-ignored / fmt; **800/0/6** over 60 lines, **806** listed, **6** ignored, fmt 0 bytes, 0 `warning:` lines, no FAILED, no panic; 668 `#[test]` lines here, at 91629f4 and at origin. |
| 8 | the tree for a push | **pass, with the cost criterion unmet** | Ledger 7 lines / 7 nonces / 7 pids / 7 images, no `answered_nonce`/`listening_pid`; penultimate = `launch.json` identity (47624 = spawned = listening = answering, nonce `faf2adda`, `verified: true`). Identity, tripwire, fold, resume (7) and battery (21) tests green in the 806. Key-shaped material: only the declared `tests/credential_scan.rs` fixture in 330 tracked files; two gitignored key-shaped files under `runs/round1` and `runs/round1b` reported by path and status, never printed. Frozen documents byte-identical; `.spec/` bevy only, `src/adapter/` bevy+mcp, `evidence/` this engine's; clean tree; nothing pushed by me. **Fit for a push: yes on the tree - no on the record, EFD2-1.** |
| 9 | the record carries no fresh false statement | **FAIL** | EFD1-REPORT.md:181 attributes the key's DECISIONS.md occurrences to `D311 line 11716, D312 lines 11712/11716`; D312's occurrences are at 11731 and 11735 and 11712/11716 are D311's. **EFD2-1.** |

## 2. Counterexamples I looked for, and what I found

* **A place the batch says it corrected but did not.** Not found. All three places in `FD1-REPORT.md`
  (14, 139, 240) carry the corrected sentence, and the old fragments are provably in `91629f4` and
  gone from the worktree.
* **The same false claim surviving somewhere the defect did not list.** **FOUND, disclosed** -
  `DECISIONS.md:11716`, left byte-identical and limited by D312. I verified the byte-identity and the
  limitation rather than taking either on trust.
* **A fresh false statement in the new record.** **FOUND, undisclosed** - EFD2-1, the DECISIONS.md row
  annotation at `EFD1-REPORT.md:181`.
* **The log edited in place, or not append-only.** Not found. D311's block is byte-identical at
  `a80db33` and HEAD; the delivered DECISIONS.md has its `91629f4`, `a80db33` and `origin/bevy-core`
  content as a byte-for-byte prefix.
* **Over-reach hiding in the diff.** Not found. Three document paths only; the restrictive-path diff
  is empty.
* **A cited command that no longer reproduces.** **FOUND, low** - RF-3: the batch's own `HEAD`-relative
  evidence citations (EFD1-REPORT.md:93, :98, :209 and D312's parenthetical at DECISIONS.md:11738)
  were written against `HEAD = 91629f4` and read differently once the dispatcher's commit moved HEAD;
  every substantive fact they support is verified true by me.
* **A recorded hash that does not pin what it claims.** Not found. Line 156 = `2893d496...` as
  recorded; HARDENING-REPORT.md = `bd373b30...` at a80db33 / 91629f4 / HEAD / worktree; the
  DECISIONS.md prefix hash `31014e76...` re-derives from `91629f4:DECISIONS.md`.
* **A key in the tracked tree.** Not found beyond the declared fixture. My own five-pattern scan of
  the 330 tracked files finds `sk-` only in `tests/credential_scan.rs`, and the credential-scan tests
  ran green inside my gate.
* **A frozen document moved.** Not found. All six are byte-identical at `4a85269`, `91629f4`,
  `6b66da6` and in the worktree.
* **A test removed.** Not found. 668 `#[test]` lines at both revisions and at `origin/bevy-core`;
  806 listed, 800 + 6 = 806.

## 3. What still stands between this tree and the goal's five criteria

**Decidability** passes: the coverage registry is untouched by this repair and the committed
observation still decides the open gaps. **Reproducibility** passes: `.gitattributes` is not in the
diff, my own walk re-derives the corpus (118 / 4,771,139), the excluded files (4 / 27,829) and the
directory (122 / 4,798,968) with 0 CR bytes, and the five clone-weak tests remain the disclosed
boundary (RF-6). **Frozen contract** passes: the six frozen documents are byte-identical across
`4a85269`, `91629f4`, `6b66da6` and the worktree, and no key-shaped material is tracked. **Honest
record** is what this verdict fails on - not on EFD-1, which is closed at every place the defect named
plus one it did not, but on the new report's own annotation of where the key occurs (EFD2-1); the
pins, the labels, the gate, the diff, the totals, the ledger and the measurement all reproduce.
**Cost fails and is expected to remain unmet at about two and a half times the target** (2.600x /
2.549x / 2.604x of the 1,500,000-token per-call target), with `agent.step_limit: 150` binding and the
repeated-success tripwire never firing (RF-1); it is **recorded as unmet rather than fixed** and
needs a human decision, not another document correction.

The minimum repair for EFD2-1 is one table cell: in `.spec/bevy/EFD1-REPORT.md:181`, say that the
occurrences are `D311 lines 11712/11716 and D312 lines 11731/11735` (or drop the line numbers
entirely and keep the count of 4). Nothing else in this batch needs work - the citations, the
machine-field disposition, the append-only handling of D311, the diff, the gate and the tree are all
sound.
