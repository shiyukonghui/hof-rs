```json
{
 "verdict": "fail",
 "schema": "hof-rs / bevy independent acceptance of the H-1..H-4 document correction and the clone-safety qualification of .spec/bevy/FINAL-DOC-REPORT.md, base 4a85269, judged at 96acd34",
 "produced_at": "2026-10-06",
 "branch": "bevy-core",
 "head_under_acceptance": "96acd342ae424eff34fd9a72792f09713739e79f (`docs(final): move the last stale pin and label the statements later corrections falsified`), whose parent and base is 4a85269 (`docs(acceptance): record the acceptance that fails the hardening batch on one unpinned hash`)",
 "origin_bevy_core": "166212f1fc4f2e520170e19b894b28501a58235d - so the two commits under judgement here are unpushed, and nothing was pushed by this acceptance",
 "offline": true,
 "answer_to_the_question_asked": "The one-line document correction H-1..H-4 asked for is genuinely made: the pin is right, the H-2 claim is restated against the real diff, the four R-A1-superseded statements are labelled in place, and the section-7 liveness sentence carries its label at the point of the claim. The measured clone-weak figure (5,917,632 bytes) and the no-recording-committed claim are both true, and the tree reproduces the gate exactly. I nevertheless return FAIL on one thing: FINAL-DOC-REPORT.md states that the overstated clone-safety sentence was corrected at three sites including the machine block at HARDENING-REPORT.md:156, and that line is byte-identical to the base revision - it still reads `none of the five can be made clone-safe in this batch` with no SUPERSEDED label. That is a fresh false claim about a change that was not made, i.e. the H-2 class this batch existed to close, in the batch that closed H-2.",
 "criteria": [
  {
   "id": "H-1-pin-sites",
   "pass": true,
   "evidence": "Computed myself, not read from the report. `sha256sum .spec/bevy/CLONE-AND-LIVE-REPORT.md` and `git cat-file -p HEAD:.spec/bevy/CLONE-AND-LIVE-REPORT.md | sha256sum` both give 423036d0b10f44fd00126f3bb4066ef1c6d303d5ceee415d733d619afebc4006, and the file has 0 CR bytes, so the two conventions in use agree. `git show f1b9af3:...` and `git show aee9c92:...` give 889033a5fd8914357886b28f110609dcffad571194e844d03e5db7d3fb44471e; `git show 92870a7:...` and `git show 166212f:...` give 7c09a7ad95597453441cef6ba2c33cf73f6b00dc71a0d4b6f2fcbde68dbc66bb; `git show ef2b0d6:...` gives 423036d0. Site 1 RECORD-CORRECTION-REPORT.md:46 is 423036d0 and its note at :47 names all three values as CURRENT vs earlier. Site 2 :129 now reads `now hashes to 423036d0...` and carries each earlier value beside the revision it names, 889033a5 tagged [SUPERSEDED] and 7c09a7ad tagged [SUPERSEDED] (with the history that the line presented it as current until H-1), the new value tagged [CURRENT]. Every other pinned hash in that file was recomputed and holds: b2053ad1 for blob 64a69937 and for `c00716d:.spec/bevy/CLONE-AND-LIVE-REPORT.md` (line 7); eb88286c for evidence/index.json (lines 44 and 134) and for its HEAD blob 264bb053; 6ea1090b for src/adapter/bevy/prd_surfaces.rs (45 and 139); cebea19e for blob afde67da (144)."
  },
  {
   "id": "H-2-report-statement",
   "pass": true,
   "evidence": "HARDENING-REPORT.md now says at all three sites that only ONE of the two pins was moved and names which: `stale_references.consequential_pin` (:109), the `changed_files` entry (:179) and section 2 (prose at :268) each keep the original wording and add the correction. The statement matches my own reproduction of the diff: `git diff -U0 166212f ef2b0d6 -- .spec/bevy/RECORD-CORRECTION-REPORT.md` has hunks at 46, 61, 114, 173, 175, 183, 342 and 372-374 only, and never at 129 - exactly the list the report gives."
  },
  {
   "id": "H-3-H-4-labels",
   "pass": true,
   "evidence": "TOTALS-CORRECTION-REPORT.md:205 and :211 (machine block) and the section-2 and section-3 prose that carried the same belief are now past tense, name `SUPERSEDED by the R-A1 hardening (DECISIONS D309, commit ef2b0d6)`, and keep the belief (skipped README.md by name / read only its file name / guarded by no test) rather than deleting it; the guard they said did not exist is named. RECORD-CORRECTION-REPORT.md:396 now carries `[SUPERSEDED 2026-10-06 by the RD-3 correction, DECISIONS D308: ...]` at the point of the liveness claim, and the label explicitly extends to `the rest of this section's premise`. The leading JSON block of each of the four edited reports still parses (I parsed it in Python), and the corrected text is quoted in FINAL-DOC-REPORT.md's old_text fields."
  },
  {
   "id": "clone-safety-claim",
   "pass": false,
   "evidence": "Three of the four things asked are true; one is not. TRUE: the measured figure - my own walk measures the six needed recording files at 1,072,407 + 1,495,115 + 1,093,652 + 680,974 + 818,938 + 756,546 = 5,917,632 bytes, matching the report. TRUE: no recording was committed - `git ls-files runs` is empty (the six files are ignored under `.gitignore:9 runs/`), and `git diff --name-status 4a85269 96acd34` contains no runs/ path. TRUE and accurate: the corrected wording at HARDENING-REPORT.md section 0 and section 3 now says the five were left clone-weak by a deliberate scope decision, prices the alternative (un-ignore a runs/** path or add a tracked directory, point the five tests at it, leave the measured totals untouched) and its costs (a separate evidence-budget decision; a runs/** placement commits the key-shaped material the tracked tree excludes; a directory outside evidence/ escapes the R-A1 totals guard). FALSE: FINAL-DOC-REPORT.md `clone_safety_sentence` says the overstatement was `corrected at all three sites`, `change_site` names `HARDENING-REPORT.md machine line 156, section 0 and section 3`, and the prose in section 5 says the alternative's cost `is now stated at all three sites` - but `git diff 4a85269 96acd34 -- .spec/bevy/HARDENING-REPORT.md` has no hunk at line 156, and `git show 4a85269:... | sed -n '156p'` is byte-identical to the current line 156 (both sha256 c1508735134bcdf1ef69c95d42087995043da6c8c19a9b6fcab83df50feb6422). The field `why_they_cannot_be_made_clone_safe` therefore still ends `So the honest answer is that none of the five can be made clone-safe in this batch` with no SUPERSEDED label, and the machine block still presents only the evidence/ route as the reason."
  },
  {
   "id": "no-over-reach",
   "pass": true,
   "evidence": "`git diff --name-status 4a85269 96acd34` is exactly five paths: A .spec/bevy/FINAL-DOC-REPORT.md, M .spec/bevy/HARDENING-REPORT.md, M .spec/bevy/RECORD-CORRECTION-REPORT.md, M .spec/bevy/TOTALS-CORRECTION-REPORT.md, M DECISIONS.md. `git diff --name-only 4a85269 96acd34 -- src tests config .gitattributes Cargo.toml Cargo.lock evidence scripts .githooks` is empty - no src/**, tests/**, evidence/**, registry, battery, liveness step, line-ending pin, config or cost machinery. DECISIONS.md numstat is `21 0`: appended to only, no line deleted. Every `fn` name under tests/ and src/ is identical between the two revisions (123 .rs files compared), and `#[test]` attribute lines are 228 at both."
  },
  {
   "id": "gate-reproduced",
   "pass": true,
   "evidence": "Free disk checked before building: F: 37 GiB and D: 145 GiB free, so nothing needed freeing and NOTHING WAS DELETED - no `rm -rf`, no wildcard, no path built from an unexpanded variable. Own build directory D:/hof-acc-fd-target, no cargo/rustc/hoh process present before I started, one test process at a time. On the clean tree at 96acd34 (`git status --porcelain` empty before, during and after): `cargo test --offline` -> LITERAL exit code 0, 800 passed / 0 failed / 6 ignored over 60 `test result:` lines; `cargo test --offline -- --list` -> exit 0 with 806 `: test` names (924 raw lines); `cargo test --offline -- --list --ignored` -> exit 0 with 6 names; `cargo fmt --all --check` -> exit 0 with 0 bytes on stdout and stderr; 0 lines starting `warning` and 0 containing `warning:` in either stream; no test removed."
  },
  {
   "id": "tree-for-push",
   "pass": true,
   "evidence": "Launch ledger evidence/observation/round4/round/launch-ledger.jsonl: 7 lines, 7 distinct nonces, 7 distinct pids, 7 distinct launch images, no line carrying `answered_nonce` or `listening_pid`; its penultimate line (nonce faf2adda-c698-48ef-a4f5-f51d1da551c6, pid 47624, image ...8d228a52...) is the identity launch.json carries (answering_pid = listening_pid = spawned_pid = 47624, verified true). Mechanism tests are green inside the gate: the ledger-after-spawn test, the identity-computed-from-facts test, the verified-endpoint-nonce test, the context-fold test, the repeated-success-tripwire test, the 7 `a_resume_*` tests and the 21 `adapter::bevy::battery::tests`. Key-shaped material: my own read-only scan of all 326 tracked files for 9 key patterns finds only the declared fixture source tests/credential_scan.rs, which ran in the gate (Running at test.err:184, its two tests ok) with no failure; no .env/.key/.secret is tracked. Frozen documents (REQUIREMENTS.md, PRD.md, DESIGN-OVERVIEW.md, DESIGN-DETAIL.md, SPIKE-1-REPORT.md, SPIKE-2-REPORT.md) are unchanged across 4a85269..96acd34 and across 166212f..96acd34. The tracked tree is the harness plus this engine only: `.spec/` has only `bevy`, `evidence/` only cost/observation/round4/tools/index/README, and `src/adapter/` only bevy + mcp + engine (no second engine). Working tree clean, nothing staged or committed by me, `origin/bevy-core` still 166212f while `refs/heads/bevy-core` is 96acd34."
  },
  {
   "id": "wide-search-live-present-tense",
   "pass": true,
   "evidence": "Beyond the batch's own list I searched the tracked tree for the falsified classes: `7c09a7ad`, `both pins`/`两处`, `guarded by no test`, `never its bytes`/`never its content`/`skips README.md by name`, and the three liveness strings. In LIVE batch reports nothing false remains unlabelled except the machine-block clone-safety sentence of criterion 3. The liveness strings survive as 3 lines / 4 occurrences in COVERAGE-EVIDENCE-REPORT.md, all quoted and labelled falsified history, matching the report. Two unlabelled present-tense survivors are outside batch-report scope and are recorded as risks, not defects: ACCEPTANCE-TOTALS.md (a dated acceptance record, `head_under_acceptance: 92870a7`, which the previous acceptance already ruled history as its RH-2) still says the totals are `guarded by no test` (:57, :173) and that both pins `now state 7c09a7ad` (:114, :146); and DECISIONS.md D309:11686 says both pins `已更新为新值`, which was false when written (only one had moved) and happens to have become true of the tree only because H-1 moved the second one."
  }
 ],
 "defects": [
  {
   "id": "FD-1",
   "severity": "high",
   "what": "FINAL-DOC-REPORT.md claims a document correction it did not make, which is the H-2 class it was written to close. The `clone_safety_sentence` object names `HARDENING-REPORT.md machine line 156` as one of the three sites of the overstated clone-safety sentence and states it was `corrected at all three sites`; the changed_files entry and prose section 5 repeat that the machine block was restated. Only two of the three were touched: HARDENING-REPORT.md:156 (`clone_safety.why_they_cannot_be_made_clone_safe`) is byte-identical to the base revision and still ends `So the honest answer is that none of the five can be made clone-safe in this batch`, unlabelled, with only the evidence/ route given as the reason and no mention of the RH-4 alternative. So the corrected record both overstates what was done and leaves the impossibility framing standing at the field whose name asserts it.",
   "reproduction": "`git diff 4a85269 96acd34 -- .spec/bevy/HARDENING-REPORT.md` shows hunks at 106-109, 176-179, 220-223, 267-269 and 297-300 only; `git diff 4a85269 96acd34 -- .spec/bevy/HARDENING-REPORT.md | grep -c why_they_cannot_be_made_clone_safe` -> 0. `git show 4a85269:.spec/bevy/HARDENING-REPORT.md | sed -n '156p' | sha256sum` and `sed -n '156p' .spec/bevy/HARDENING-REPORT.md | sha256sum` both give c1508735134bcdf1ef69c95d42087995043da6c8c19a9b6fcab83df50feb6422. Compare FINAL-DOC-REPORT.md lines 185, 192-195 (`where`, `disposition`, `change_site`) and its prose at lines 322-333."
  }
 ],
 "risks": [
  {
   "id": "RF-1",
   "risk": "unresolved and out of this batch's scope: ACCEPTANCE-TOTALS.md, a dated acceptance record scoped by `head_under_acceptance: 92870a7`, still states in the present tense that the directory totals are `guarded by no test` (:57, :173) and that the two pins `now state 7c09a7ad` (:114, :146); both are false of the tree since R-A1 and since H-1. The previous acceptance recorded these as its RH-2 and judged dated acceptance records history rather than defects; this batch carried the judgement forward without labelling them, so a strict reader still meets unlabelled false present tense in a tracked file."
  },
  {
   "id": "RF-2",
   "risk": "DECISIONS.md D309 (:11686) states that both pin sites `已更新为新值`; when written that was false (only gate.gate_input_sha256 had moved). D310 records the true history for HARDENING-REPORT.md but does not name that sentence in D309, and D309 is left unlabelled under the append-only rule. It has accidentally become true of the tree now that H-1 moved both sites, so it no longer misleads about the current value - but it is a false record of what D309 did."
  },
  {
   "id": "RF-3",
   "risk": "even if FD-1 is fixed, the machine-block field is still titled `why_they_cannot_be_made_clone_safe` and its body still gives only the evidence/ route; RH-4's ruling (a scope decision, not a theorem) is recorded at sections 0, 2 and 3 but not in the machine block that a reader or tool is most likely to take as the summary."
  },
  {
   "id": "RF-4",
   "risk": "the five clone-weak tests remain clone-weak: in a tree without runs/round1b, runs/round2 and runs/round3 they still assert nothing (five tests), so a clone's identical 800/0/6 is weaker than the working tree's. This is the disclosed, deliberately uncommitted boundary, not something this batch changed."
  },
  {
   "id": "RF-5",
   "risk": "the cost criterion remains unmet at 2.600x / 2.549x / 2.604x of the 1,500,000-token per-call target, every Developer call ended by `agent.step_limit: 150` with the repeated-success tripwire never firing - expected to remain so pending a human decision, and recorded as unmet rather than fixed."
  }
 ],
 "unverified": [
  "A real `git clone`; I did not clone the repository and did not re-run the clone gate. I verified the file set (`git ls-files runs` empty), the ignore rules and the working-tree gate instead.",
  "A Linux or macOS checkout, where core.autocrlf is false by default; I checked the line-ending question only by the `.gitattributes` pins, `git check-attr` and a 0-CR-byte scan of evidence/.",
  "An audit of all 800 passing tests for clone-safety; I confirmed the named mechanism tests are present and green, not that every test asserts something in a clone.",
  "The cost figures beyond reading the reports: no round, engine, game, network or model call was made and none was attempted, so 2.600x / 2.549x / 2.604x is adopted from the recorded usage.json figures, not re-measured.",
  "The batch's own logs and the physical disk state at the instant its gate ran; my gate is my own run in D:/hof-acc-fd-target.",
  "Every number in the batch reports other than the ones I recomputed myself (the four pins, the three evidence totals, the six recording files and their 5,917,632-byte sum, the diff path list, the test counts and the gate exit codes).",
  "No tamper/plant experiment was run: none of the checks I was asked for required modifying a file, so no copy, restore or restamped timestamp exists in this acceptance."
 ],
 "what_this_acceptance_did_not_do": "No engine, no game, no network, no model call, no round and no Developer call was run. Nothing was written under `runs/**`. No `rm -rf`, no wildcard deletion and nothing deleted (free disk was sufficient). No path was built from an unexpanded variable; no `git checkout --`; no `git add`, commit, stage or push. Helper scripts live outside the repository under F:/hof-acc-fd-work/, logs under F:/hof-acc-fd-logs/, the build under D:/hof-acc-fd-target. The only file written inside the repository is this report."
}
```

# ACCEPTANCE-FINAL-DOC - independent acceptance of the H-1..H-4 document correction and the clone-safety qualification

Independent, **offline** acceptance of the batch delivered as `.spec/bevy/FINAL-DOC-REPORT.md`, judged at
**`bevy-core` / `96acd34`** (base `4a85269`, which itself is the acceptance record that failed the hardening
batch; `origin/bevy-core` is still `166212f`). No engine, no game, no network, no model call, no round and no
Developer call; nothing under `runs/**` written; no `rm -rf`, no wildcard deletion and nothing deleted; no
`git checkout --`; no commit, stage or push; no path built from an unexpanded variable. Helper scripts live
outside the repository under `F:/hof-acc-fd-work/`, logs under `F:/hof-acc-fd-logs/`, the build under
`D:/hof-acc-fd-target`. I ran no tamper/plant experiment because none of the required checks needed one. The
machine-readable verdict above is `json.dumps(..., indent=1, ensure_ascii=False)` output written by
`F:/hof-acc-fd-work/gen_report.py`, which then **parsed it back out of the written file** and failed unless it
round-tripped byte-for-byte.

## 0. The verdict in one paragraph

**The correction H-1..H-4 asked for is genuinely made, but the batch's own report now claims a correction it
did not make, so this fails.** I recomputed the pin rather than adopting it: `CLONE-AND-LIVE-REPORT.md` hashes
to `423036d0...` two ways (0 CR bytes), and `RECORD-CORRECTION-REPORT.md:129` now presents
it as current with both earlier values labelled `SUPERSEDED`; `:46` was already right, and every other pin in
that file recomputes correctly. `HARDENING-REPORT.md` now says only one of the two pins was moved and matches
`git diff -U0 166212f ef2b0d6` exactly. The four `TOTALS-CORRECTION-REPORT.md` statements and the section-7
liveness sentence carry their `SUPERSEDED` labels at the point of the claim with the earlier belief kept. The
clone-weak figure is right (my own walk: **5,917,632** bytes over the six recordings) and **no recording was
committed** (`git ls-files runs` empty; the diff is documents only). The gate reproduces on the clean tree:
`cargo test --offline` **literal exit 0**, **800 passed / 0 failed / 6 ignored** over 60 `test result:` lines,
**806** listed, **6** ignored, `cargo fmt --all --check` exit 0 with 0 bytes, **0 warnings**, no test removed,
and the diff is five documents with `DECISIONS.md` appended to (21/0). **The one false statement is in the new
report**: it says the overstated clone-safety sentence was corrected at three sites including the machine block
at `HARDENING-REPORT.md:156`, but that line is byte-identical to the base revision and still ends `none of the
five can be made clone-safe in this batch`, unlabelled, giving only the `evidence/` route. That is a fresh
claim about a change that was not made - the H-2 defect class itself - so I return **fail**.

## 1. Per-item results

| # | item | result | the evidence I gathered myself |
|---|---|---|---|
| 1 | H-1, the two pin sites | **pass** | `sha256sum` of the working file and `git cat-file -p HEAD:...` both give `423036d0...` (0 CR bytes); `f1b9af3`/`aee9c92` = `889033a5...`, `92870a7`/`166212f` = `7c09a7ad...`, `ef2b0d6` = `423036d0...`. `:46` current with the note at `:47` naming all three; `:129` now current, with both earlier values beside the revision they name and tagged `[SUPERSEDED]`. Every other pin in the file recomputes: `b2053ad1` (blob `64a69937`, `c00716d:<path>`), `eb88286c` (`evidence/index.json` and blob `264bb053`), `6ea1090b` (`prd_surfaces.rs`), `cebea19e` (blob `afde67da`). |
| 2 | H-2, the report's claim | **pass** | `HARDENING-REPORT.md` `:109`, `:179` and section 2 all state only `gate.gate_input_sha256` moved and `changed_files[0].committed_as` did not; my own `git diff -U0 166212f ef2b0d6 -- .spec/bevy/RECORD-CORRECTION-REPORT.md` has hunks at 46, 61, 114, 173, 175, 183, 342 and 372-374 and never at 129. |
| 3 | H-3 and H-4, the named statements | **pass** | `TOTALS-CORRECTION-REPORT.md:205`, `:211`, `:309-312` and `:328-331` are past tense with `SUPERSEDED by the R-A1 hardening (DECISIONS D309, commit ef2b0d6)`, the guard named, and the earlier belief kept; `RECORD-CORRECTION-REPORT.md:396` carries the `[SUPERSEDED ... DECISIONS D308]` label at the claim and extends it to the section's premise. The four edited JSON blocks still parse. Widening the search (see section 3) found no other false present tense in a live batch report. |
| 4 | the clone-safety claim | **fail** | Figure and no-commit confirmed (`5,917,632` bytes; `git ls-files runs` empty; no `runs/` in the diff); the corrected section 0 and section 3 wording is accurate and prices the RH-4 alternative and its costs; **but** the machine block at `HARDENING-REPORT.md:156` was not touched (sha256 identical to the base) while `FINAL-DOC-REPORT.md` claims it was one of three corrected sites. Defect **FD-1**. |
| 5 | no over-reach | **pass** | Five paths, all documents; `git diff --name-only 4a85269 96acd34 -- src tests config .gitattributes Cargo.toml Cargo.lock evidence scripts .githooks` empty; `DECISIONS.md` numstat `21 0`; every `fn` name identical across 123 .rs files; `#[test]` lines 228 at both revisions. |
| 6 | the gate reproduced | **pass** | Free disk first (F: 37 GiB, D: 145 GiB); nothing deleted, no `rm -rf`, no wildcard, no unexpanded-variable path; own `D:/hof-acc-fd-target`; one test process. `cargo test --offline` **literal exit 0**, **800 / 0 / 6** over 60 lines, **806** listed, **6** ignored, `fmt --all --check` exit 0 with 0 bytes, **0 warnings**, no test removed. |
| 7 | the tree for a push | **pass, with the cost criterion unmet** | Ledger 7 lines / 7 nonces / 7 pids / 7 images, no `answered_nonce` or `listening_pid`, penultimate line = `launch.json.identity` (`faf2adda` / 47624); tripwire, fold, resume (7) and battery (21) tests green; my own 9-pattern key scan of 326 tracked files finds only the declared `tests/credential_scan.rs` fixture, which ran green in the gate; frozen documents byte-identical; `.spec/` is bevy only, `evidence/` is this engine's only, `src/adapter/` holds no second engine; working tree clean; nothing pushed by me. **Fit for a push: no** - FD-1 is a false statement in the record. |

## 2. The clone-safety claim, checked piece by piece

| claim | my measurement | state |
|---|---|---|
| the six needed recordings total ~5.9 MB | `runs/round1b/iter-1` 1,072,407 + `runs/round2/iter-1` 1,495,115 + `runs/round2/iter-2` 1,093,652 + `runs/round3/iter-1` 680,974 + `runs/round3/iter-2` 818,938 + `runs/round3/iter-3` 756,546 = **5,917,632** bytes | **true**, matches FINAL-DOC-REPORT exactly |
| no recording was committed | `git ls-files runs` = 0 entries; the six files ignore-match `.gitignore:9 runs/`; `git diff --name-status 4a85269 96acd34` has no `runs/` path | **true** |
| the overstated sentence was corrected at section 0 and section 3 | both diffs present; each keeps the original wording and labels it superseded | **true** |
| the overstated sentence was corrected at the machine block (`:156`) | `git diff ... \| grep -c why_they_cannot_be_made_clone_safe` = 0; base and current line 156 both sha256 `c1508735...` | **false - defect FD-1** |

The corrected wording is otherwise accurate and does not understate the costs it prices: a `runs/**`
placement would indeed commit the key-shaped material the tracked tree currently excludes, a directory
outside `evidence/` would indeed escape the R-A1 totals guard, and the budget decision is indeed the
owner's. It does not mention that committing ~5.9 MB grows every future clone, which is a real but minor
omission. Where it *overstates by surviving* is the machine block, whose field is still named
`why_they_cannot_be_made_clone_safe` and whose body still presents only the `evidence/` route.

## 3. Counterexamples I looked for, and what I found

* **A pin left on the old hash, or a pin right for the wrong revision.** Not found: both sites name the
  current value, both earlier values are present and each is tied to `f1b9af3`/`aee9c92` and
  `92870a7`/`166212f`, and the values reproduce from git.
* **A pinned hash elsewhere in `RECORD-CORRECTION-REPORT.md` that no longer resolves.** Not found: all
  seven pins (including the blob pins) recompute from `git cat-file`/`git show`/`sha256sum`.
* **A report asserting a change it did not make.** **FOUND** - FD-1, the clone-safety machine block.
* **The earlier belief deleted rather than kept.** Not found in the four H-3 sites or the H-4 sentence:
  each keeps the old claim (verbatim in the prose sites, restated in the machine-block fields) and the
  batch report quotes the originals in its `old_text` fields.
* **A remaining present-tense statement a later correction made false, beyond the batch's list.** Found
  only outside batch-report scope: `ACCEPTANCE-TOTALS.md` (`guarded by no test` at `:57`/`:173`; both pins
  `now state 7c09a7ad` at `:114`/`:146`) and `DECISIONS.md` D309's `两处...已更新为新值`, recorded as risks
  RF-1/RF-2. The liveness strings survive only as 3 lines / 4 quoted, labelled occurrences.
* **A recording committed or a measured figure moved.** Not found: no `runs/` path in the diff,
  `evidence/` untouched at 118 / 4,771,139 corpus, 4 / 27,829 excluded, 122 / 4,798,968 directory, and
  `evidence/index.json` still `eb88286c...`.
* **Over-reach hiding in the diff.** Not found: documents only, `DECISIONS.md` append-only, all `fn`
  names and the 228 `#[test]` lines unchanged.
* **A key in the tracked tree.** Not found beyond the declared fixture source; the credential-scan binary
  ran inside the full gate and passed.

## 4. What still stands between this tree and the goal's five criteria

**Decidability** passes (the registry is untouched by this batch and the persisted observation still
decides the open gaps). **Reproducibility** passes (`evidence/** -text` holds, 0 CR bytes, the corpus is
re-derived green inside the gate; the round-1b/round-2/round-3 trajectories remain the disclosed boundary,
and five tests still assert nothing in a clone - RF-4). **Frozen contract** passes (the frozen documents
are byte-identical across the range I checked and no key-shaped material is tracked). **Honest record** is
what this verdict fails on: not the pin or the H-2/H-3/H-4 labels, which are fixed, but the new report's
claim that it corrected the machine-block clone-safety sentence when that line is byte-identical to the
base. **Cost** fails and is expected to remain unmet pending a human decision: 2.600x / 2.549x / 2.604x of
the 1,500,000-token per-call target with `agent.step_limit: 150` binding and the repeated-success tripwire
never firing (RF-5), recorded as unmet rather than fixed.

The minimum repair for FD-1 is a document-only change: either correct
`HARDENING-REPORT.md:156` (past tense, `SUPERSEDED`, and the RH-4 alternative named) and keep the report's
three-site claim, or retract the report's claim that the machine block was corrected and say which two
sites were. The pins, the labels, the gate, the diff, the totals and the clone-safety measurement need no
further work.
