```json
{
 "verdict": "fail",
 "schema": "hof-rs / bevy independent acceptance of the FD-1 single repair (.spec/bevy/FD1-REPORT.md), base 69a65d8, judged at a80db33",
 "produced_at": "2026-10-06",
 "branch": "bevy-core",
 "head_under_acceptance": "a80db335a4f78611cedf818eeaded79b2fdea7dd (`docs(fd1): close the last overstated site claim by correcting the machine field it named`), whose parent 69a65d8265e6006b3bf3bc368b740c0779632001 is the revision FD1-REPORT.md names as its start",
 "origin_bevy_core": "166212f1fc4f2e520170e19b894b28501a58235d - so the whole unpushed range (ef2b0d6..a80db33, five commits) is unpushed and nothing was pushed by this acceptance",
 "offline": true,
 "summary": "FD-1 is genuinely closed: the machine field at .spec/bevy/HARDENING-REPORT.md:156 was the one site the earlier correction (4a85269 -> 96acd34) did not touch, and it now keeps its original wording verbatim under a SUPERSEDED label that names the RH-4 alternative, its measured 5,917,632 bytes and its three real costs, so FINAL-DOC-REPORT.md's three-site claim is true of this tree. The measurement reproduces, both named costs are real, DECISIONS.md is append-only with D309 untouched and D311 naming and limiting its sentence, the repair is documents-only, and the gate reproduces exactly (literal exit 0, 800/0/6 over 60 lines, 806 listed, fmt 0, 0 warnings, no test removed). I nevertheless return FAIL on one thing: the repair's own record (FD1-REPORT.md in two machine-readable places, and DECISIONS.md D311) states that the JSON key is `referenced by name` in FINAL-DOC-REPORT.md's `clone_safety_sentence.where` **and** `change_site`; `change_site` contains no such name (it reads `HARDENING-REPORT.md machine line 156, section 0 and section 3`). That is a fresh false statement about what a tracked document contains - the H-2/RD-2 class this line of batches exists to close - in the batch that closed FD-1, and it is the only blocker. Everything else the batch claims reproduces.",
 "criteria": [
  {
   "id": "fd1-sites-from-the-revisions",
   "pass": true,
   "evidence": "Established from the revisions, not from the claim. My own `git diff -U0 4a85269 96acd34 -- .spec/bevy/HARDENING-REPORT.md` has exactly five hunks - `@@ -109 +109 @@`, `@@ -179 +179 @@`, `@@ -223,3 +223 @@`, `@@ -270,4 +268 @@`, `@@ -300,6 +295 @@` - and no hunk at 156; `git diff 4a85269 96acd34 -- .spec/bevy/HARDENING-REPORT.md | grep -c why_they_cannot_be_made_clone_safe` is 0; `git show 4a85269:... | sed -n '156p' | sha256sum` equals `git show 96acd34:... | sed -n '156p' | sha256sum` equals c1508735134bcdf1ef69c95d42087995043da6c8c19a9b6fcab83df50feb6422. So the earlier correction touched the two clone-safety prose sites (section 0, the -223,3 hunk; section 3, the -300,6 hunk) and did not touch the machine-block field at line 156. The measured recording total in that diff's sections is the same figure the repair re-states: 5,917,632 bytes."
  },
  {
   "id": "fd1-machine-field-corrected-at-the-point-of-the-claim",
   "pass": true,
   "evidence": "Line 156 is now the only hunk of the repair against 96acd34 (`@@ -156 +156 @@`, numstat 1/1) and now hashes to 2893d496152e475fa886b200fbb9bff8068f4dcfd0c6b25a68123d1bb1cecd6d, which equals FD1-REPORT.md's `line_156_sha256.worktree_after` and `file_sha256.worktree_after` (bd373b30fcd0da76a264377674962f10ac2ba4c9fa1122631075c47e774c04ac is the file's sha256, verified now). The leading JSON block of HARDENING-REPORT.md parses (I parsed it in Python). The field `clone_safety.why_they_cannot_be_made_clone_safe` begins with the old value byte-for-byte - I compared it to the value parsed out of `git show 96acd34:...` (571 chars old, 1798 chars new, old is a verbatim prefix, and the appended text is the field's exact suffix) - and the appended `**[SUPERSEDED 2026-10-06 by the FD-1 correction of `.spec/bevy/ACCEPTANCE-FINAL-DOC.md`, DECISIONS D311 ...]**` label names the scope-decision ruling, the 5,917,632-byte alternative, the separate evidence-budget decision, the `runs/**` key-shaped-material cost and the R-A1 totals-guard escape. The field is still one line and still line 156."
  },
  {
   "id": "fd1-three-site-claim-true-of-this-tree",
   "pass": true,
   "evidence": "FINAL-DOC-REPORT.md's `clone_safety_sentence.disposition` (`corrected at all three sites ...`) and `change_site` (`HARDENING-REPORT.md machine line 156, section 0 and section 3`) were false of 96acd34 and are now true of a80db33. I checked each of the three sites in the delivered file: the machine field and section 3 state all three costs (budget decision, `runs/**` key-shaped material, `evidence/`-outside totals-guard escape); section 0 states the same scope-decision ruling and two of the three (budget decision, `runs/**` key-shaped material). The two prose sites are the 96acd34 hunks and are untouched by this repair; the third site is the new 156 hunk. The acceptance's own authorised option A was `correct HARDENING-REPORT.md:156 ... and keep the report's three-site claim`."
  },
  {
   "id": "clone-weak-alternative-measured",
   "pass": true,
   "evidence": "My own read-only stat of the six files the five clone-weak tests need: runs/round1b/iter-1/traj/developer.attempt1.json 1,072,407 + runs/round2/iter-1/... 1,495,115 + runs/round2/iter-2/... 1,093,652 + runs/round3/iter-1/... 680,974 + runs/round3/iter-2/... 818,938 + runs/round3/iter-3/... 756,546 = 5,917,632 bytes exactly. All six are ignore-matched by `.gitignore:9:runs/` (`git check-ignore -v` on each) and `git ls-files runs` is empty, so no recording is committed and the measured totals (118 / 4,771,139 corpus, 4 / 27,829 excluded, 122 / 4,798,968 directory) are unchanged and re-derived by my own walk."
  },
  {
   "id": "alternative-costs-real",
   "pass": true,
   "evidence": "Both named costs reproduce. (a) A `runs/**` placement would commit key-shaped material: tests/credential_scan.rs, run inside my gate and again on its own (`cargo test --offline --test credential_scan -- --nocapture`, literal exit 0, 7 passed / 0 failed), reports exactly 2 key-shaped files with 1 distinct fingerprint 5cf81e8f(len 51) - runs/round1/iter-1/traj/developer.attempt1.json and runs/round1b/iter-1/traj/tester.attempt1.json - i.e. precisely the `runs/round1` and `runs/round1b` the label names, and that material is currently outside the tracked tree only because `runs/` is ignored. (b) A directory outside `evidence/` escapes the R-A1 totals guard: tests/evidence_reproduction.rs:515 roots the totals walk at `repo_root().join(\"evidence\")` and nowhere else, so files committed elsewhere cannot move the three asserted figures. The `evidence/`-outside placement also leaves the measured totals untouched by construction, as the label says."
  },
  {
   "id": "decisions-log-append-only",
   "pass": true,
   "evidence": "DECISIONS.md's content at 166212f, 69a65d8 and 96acd34 is a byte-for-byte prefix of the working file (1,336,933 bytes at 96acd34 vs 1,342,560 now; `git diff --numstat 96acd34 a80db33 -- DECISIONS.md` is `19 0`), so the whole unpushed diff and the repair are append-only; line 11686 (the line D311 and FD1-REPORT name, inside D309's `预期影响与回滚点`, which contains `两处（gate.gate_input_sha256 与 changed_files）已更新为新值`) is byte-identical at ef2b0d6, 96acd34 and now. D311 begins at line 11709 and is the file's last entry."
  },
  {
   "id": "d311-names-and-limits-d309",
   "pass": true,
   "evidence": "D311 does what FD1-REPORT's `changed_files` claims: it names option A and B (rejecting B), rejects renaming the JSON key, quotes D309's `两处…已更新为新值` sentence, pins it to `:11686`, and limits it - `该句写出时只动了 gate.gate_input_sha256 一处 ... 它如今对树碰巧为真（H-1 已把第二处也移到 423036d0…）... 故不就地改，而由本条记录真实历史并限定其措辞`. The underlying history fact reproduces from git: at ef2b0d6 `RECORD-CORRECTION-REPORT.md:46` contains 423036d0 and `:129` contains 7c09a7ad (so the sentence was false of what D309 did), while at 96acd34 and now both lines contain 423036d0 (so it is accidentally true of the tree)."
  },
  {
   "id": "non-renamed-key-reasoning",
   "pass": true,
   "evidence": "Keeping the key name is justified on the merits: the name occurs as a literal in FINAL-DOC-REPORT.md's `clone_safety_sentence.where` (line 185) and six times in ACCEPTANCE-FINAL-DOC.md, both documents this repair deliberately leaves alone (`git grep -c why_they_cannot_be_made_clone_safe` finds 1 and 6), so a rename would leave those references pointing at a key that no longer exists - a fresh false reference of the same class. The residual cost of keeping it is disclosed rather than hidden: FD1-REPORT.md's `decisions_on_non_blocking_items.RF-3_field_title` and its section 2 record RF-3 as a residual risk that still stands, including that a reader who reads only the key name still sees the old impossibility framing while the value contradicts it. (The one supporting detail that is wrong is filed separately as EFD-1.)"
  },
  {
   "id": "no-fresh-false-claim-in-the-repair-record",
   "pass": false,
   "evidence": "FD1-REPORT.md's machine-readable `why_option_A` and its section 2 both assert that the key `why_they_cannot_be_made_clone_safe` is `referenced by name in FINAL-DOC-REPORT.md's where and change_site`, and DECISIONS.md D311's option 3 repeats it (`键名被 FINAL-DOC-REPORT.md（where/change_site）... 按名引用`). `change_site`'s value is `HARDENING-REPORT.md machine line 156, section 0 and section 3`, which contains no such name; the whole file contains the name once, on line 185 (`where`). The claim is false and it is in a machine field of the new report. Defect EFD-1."
  },
  {
   "id": "no-over-reach",
   "pass": true,
   "evidence": "The repair diff `69a65d8 -> a80db33` is exactly three paths: A `.spec/bevy/FD1-REPORT.md` (258/0), M `.spec/bevy/HARDENING-REPORT.md` (1/1), M `DECISIONS.md` (19/0). `git diff --name-only BASE a80db33 -- src tests config .gitattributes Cargo.toml Cargo.lock evidence scripts .githooks` is empty for BASE in {69a65d8, 96acd34, 4a85269}. No registry, battery, liveness step, line-ending pin or config path is in the diff; `.gitattributes` (with the `evidence/** -text` pin) is unchanged; `evidence/**` has 0 modified files and 0 CR bytes, and my own walk reproduces the three totals the guard asserts. The whole unpushed range's only non-document changes are the earlier, separately accepted hardening commit ef2b0d6 (tests/evidence_reproduction.rs 68/2, tests/repeated_action.rs 22/1)."
  },
  {
   "id": "gate-reproduced",
   "pass": true,
   "evidence": "Free disk first: F: 37 GiB and D: 127 GiB free, so nothing needed freeing and NOTHING WAS DELETED - no `rm -rf`, no wildcard, no path built from an unexpanded variable. No cargo/rustc/hoh process was running before I started; my own build directory D:/hof-fd1acc-target (9.84 GiB, built from scratch, 169 `Compiling` lines on stderr) and one test process at a time. On the clean tree (`git status --porcelain` empty before and after): `cargo test --offline` -> LITERAL exit code 0, 800 passed / 0 failed / 6 ignored over 60 `test result:` lines; `cargo test --offline -- --list` -> exit 0 with 806 `: test` names (924 raw lines); `-- --list --ignored` -> exit 0 with 6 names; `cargo fmt --all --check` -> exit 0 with 0 bytes on stdout and stderr; 0 lines containing `warning:` in either stream (the 5 stdout lines containing the word are test names); no FAILED and no panic. Equals the previous baseline exactly."
  },
  {
   "id": "no-test-removed",
   "pass": true,
   "evidence": "`^\\s*#\\[test\\]` lines are 668 across src+tests at both 96acd34 and a80db33 (228 of them in tests/), identical; the test listing is 806 and the run is 800/0/6 at both the baseline the reports state and my own run. The diff to the judged revision touches no file under src/ or tests/."
  },
  {
   "id": "tree-for-push",
   "pass": true,
   "evidence": "Launch ledger evidence/observation/round4/round/launch-ledger.jsonl: my own parse gives 7 lines, 7 distinct nonces, 7 distinct pids, 7 distinct launch images, no line carrying `answered_nonce` or `listening_pid`, and the penultimate line (nonce faf2adda-c698-48ef-a4f5-f51d1da551c6, pid 47624) is exactly `launch.json`'s identity: spawned_pid = listening_pid = answering_pid = 47624, verified true. The mechanism tests are in the 806 and green: the ledger-after-spawn test, `the_identity_fields_are_computed_from_the_facts_not_asserted`, the nonce/endpoint tests, the context-fold tests, the repeated-success tripwire tests, all 7 `a_resume_*` tests and all 21 `adapter::bevy::battery::tests`. Key-shaped material: the credential-scan test ran in the gate (7 passed) and my own 5-pattern scan of all 328 tracked files finds the `sk-` shape only in the declared fixture tests/credential_scan.rs, and no tracked `.env`/`.key`/`.pem`/secret file. Frozen documents (REQUIREMENTS.md, PRD.md, DESIGN-OVERVIEW.md, DESIGN-DETAIL.md, SPIKE-1-REPORT.md, SPIKE-2-REPORT.md) are byte-identical at 4a85269, 96acd34 and 69a65d8 and now. `.spec/` contains only `bevy`, `evidence/` only this engine's index/README/cost/observation/tools, `src/adapter/` only `bevy` and `mcp` (no second engine). Working tree clean; HEAD a80db33, origin/bevy-core still 166212f; I staged, committed and pushed nothing. Fit for a push: NO - see EFD-1 (and the cost criterion stays unmet, RF-1)."
  }
 ],
 "defects": [
  {
   "id": "EFD-1",
   "severity": "low",
   "what": "The repair's own record makes a false claim about what a tracked document contains - the H-2/RD-2 class. FD1-REPORT.md's `why_option_A` says the JSON key `why_they_cannot_be_made_clone_safe` is `referenced by name in FINAL-DOC-REPORT.md's clone_safety_sentence.where and change_site and in the acceptance itself`, and its section 2 repeats it; DECISIONS.md D311's rejected option 3 repeats it. `where` does name the key (FINAL-DOC-REPORT.md:185) and ACCEPTANCE-FINAL-DOC.md does name it (6 occurrences), so the no-rename decision is still justified - but `change_site` contains no such name (its value is `HARDENING-REPORT.md machine line 156, section 0 and section 3`), so the justification as written overstates the references and a reader checking it would find the claim false. This is the only false statement I found in the delivered record, and it is why the verdict is fail.",
   "reproduction": "`git grep -c why_they_cannot_be_made_clone_safe` -> 6 in .spec/bevy/ACCEPTANCE-FINAL-DOC.md, 1 in .spec/bevy/FINAL-DOC-REPORT.md, 1 in .spec/bevy/HARDENING-REPORT.md, 8 in .spec/bevy/FD1-REPORT.md, 2 in DECISIONS.md. The single FINAL-DOC-REPORT.md occurrence is line 185 (`where`); `grep -n why_they_cannot_be_made_clone_safe .spec/bevy/FINAL-DOC-REPORT.md` returns only line 185, and the `change_site` field at line 195 is `HARDENING-REPORT.md machine line 156, section 0 and section 3`. Compare FD1-REPORT.md lines 14 and 239-240 and DECISIONS.md D311 option 3. The two facts a reader would use, `where` and the acceptance, are real, so the fix is to correct the claim (name `where` and the acceptance, and drop `change_site`), not to rename the key."
  }
 ],
 "risks": [
  {
   "id": "RF-1",
   "risk": "The cost criterion remains unmet and is expected to stay unmet pending a human decision: the recorded 2.600x / 2.549x / 2.604x of the 1,500,000-token per-call target, every Developer call ended by `agent.step_limit: 150` with the repeated-success tripwire never firing. It is recorded as unmet rather than fixed, and no round or Developer call was run or attempted by this acceptance."
  },
  {
   "id": "RF-2",
   "risk": "The machine-block key name still asserts an impossibility (`why_they_cannot_be_made_clone_safe`). The value now contradicts it in the reader's face, and FD1-REPORT.md records this as RF-3 standing after the repair, but a reader or tool that reads only the key name still meets the old framing."
  },
  {
   "id": "RF-3",
   "risk": "Inherited and untouched, as the acceptance scoped it: ACCEPTANCE-TOTALS.md (a dated acceptance record scoped to 92870a7) still states in the present tense that the directory totals are `guarded by no test` (`:57`, `:173`) and that both pins `now state 7c09a7ad` (`:114`, `:146`); both are false of the tree since R-A1 and H-1. This batch carried the earlier judgement forward without labelling them."
  },
  {
   "id": "RF-4",
   "risk": "FD-1's three-site claim is now true of the delivered tree, but it remains false of the judged revision 96acd34 itself - the repair retro-fitted the third site. The batch discloses this plainly (FD1-REPORT.md section 3, DECISIONS D311 decision (b)), so it is a disclosed history rather than a hidden one."
  },
  {
   "id": "RF-5",
   "risk": "The five clone-weak tests remain clone-weak: in a tree without runs/round1b, runs/round2 and runs/round3 they assert nothing (five tests), so a clone's identical 800/0/6 is weaker than the working tree's. This is the disclosed, deliberately uncommitted boundary (RF-4 of the prior acceptance)."
  },
  {
   "id": "RF-6",
   "risk": "Two cosmetic/partial items I did not raise to defects: the SUPERSEDED label on line 156 opens `**` and closes only at the end of the appended text, so the whole appended passage renders bold, unlike the H-4 label that closes at `:**`; and FINAL-DOC-REPORT.md section 5's `the alternative's cost is now stated at all three sites` is true only in the weak sense that each site states some of the cost - section 0 states two of the three items, not the totals-guard escape."
  }
 ],
 "unverified": [
  "A real `git clone`; I did not clone the repository and did not re-run a clone gate. I verified `git ls-files runs` is empty, the ignore rules for all six recordings, and the working-tree gate instead.",
  "A Linux or macOS checkout, where core.autocrlf is false by default; I checked the line-ending question only through `.gitattributes` (unchanged, `evidence/** -text` present) and a 0-CR-byte scan of `evidence/`.",
  "An audit of all 800 passing tests for clone-safety; I confirmed the named mechanism tests are present and green, not that every test asserts something in a clone.",
  "The cost figures beyond reading the reports: no round, engine, game, network or model call was made or attempted, so 2.600x / 2.549x / 2.604x is adopted from the recorded usage figures, not re-measured.",
  "The batch's own build log, timestamps and the physical disk state at the instant its gate ran (its `D:/hof-fd1-target`, 169 Compiling lines, 1m 18s); my gate is my own run in D:/hof-fd1acc-target.",
  "Every number in the batch reports other than the ones I recomputed myself: the pins and line/file hashes, the six recording sizes and their 5,917,632-byte sum, the three evidence totals, the diff path lists, the JSON-block parses, the gate exit codes and counts, and the D309 history.",
  "No tamper/plant experiment was run: none of the checks I was asked for required modifying a file, so no copy, restore or restamped timestamp exists in this acceptance."
 ],
 "what_this_acceptance_did_not_do": "No engine, no game, no network, no model call, no round and no Developer call was run. Nothing was written under `runs/**`. No `rm -rf`, no wildcard deletion and nothing deleted (free disk was sufficient: F: 37 GiB, D: 127 GiB). No path was built from an unexpanded variable; no `git checkout --`; no `git add`, commit, stage or push. Helper scripts live outside the repository under F:/hof-fd1acc-work/, logs under F:/hof-fd1acc-logs/, the build under D:/hof-fd1acc-target. The only file written inside the repository is this report."
}
```


# ACCEPTANCE-FD1 - independent acceptance of the FD-1 single repair

Independent, **offline** acceptance of the batch delivered as `.spec/bevy/FD1-REPORT.md`, judged at
**`bevy-core` / `a80db33`** (base `69a65d8`, the acceptance record of the `ACCEPTANCE-FINAL-DOC.md` failure; its
parent `96acd34` is the revision that acceptance judged; `origin/bevy-core` is still `166212f`, so the whole
unpushed range is unpushed). No engine, no game, no network, no model call, no round and no Developer call;
nothing under `runs/**` written; no `rm -rf`, no wildcard deletion and nothing deleted; no `git checkout --`;
no commit, stage or push; no path built from an unexpanded variable. Helper scripts live outside the repository
under `F:/hof-fd1acc-work/`, logs under `F:/hof-fd1acc-logs/`, my build under `D:/hof-fd1acc-target`. I ran no
tamper/plant experiment because none of the required checks needed one. The machine-readable verdict above is
`json.dumps(..., indent=1, ensure_ascii=False)` output written by `F:/hof-fd1acc-work/gen_report.py`, which then
**parsed it back out of the written file** and required it to round-trip equal.

## 0. The verdict in one paragraph

**FD-1 is genuinely closed, and I still return fail on one sentence in the repair's own record.** Judged from the
revisions rather than from the claim: `4a85269 -> 96acd34` has five hunks in `HARDENING-REPORT.md` - 109, 179, 223,
268, 295 - and none at 156, and line 156 hashes to `c1508735...` at both revisions, so the earlier correction
touched section 0 and section 3 and not the machine field. The repair touches exactly one line, at 156
(`2893d496...`), keeps the old value byte-for-byte as a prefix, and appends a `SUPERSEDED` label naming the
scope-decision ruling, the **5,917,632**-byte alternative (I re-measured the six recordings myself), the
evidence-budget decision, the `runs/**` key-shaped-material cost (real: the credential scan finds the fingerprint
`5cf81e8f` in `runs/round1/iter-1/traj/developer.attempt1.json` and `runs/round1b/iter-1/traj/tester.attempt1.json`)
and the totals-guard escape (real: the guard's walk is rooted at `evidence/` only). `DECISIONS.md` is append-only
across the whole diff, D309's line 11686 is untouched, and D311 names and limits its false sentence. The repair is
documents-only, and the gate reproduces exactly: **literal exit 0, 800 passed / 0 failed / 6 ignored over 60
`test result:` lines, 806 listed, 6 ignored, `cargo fmt --all --check` exit 0 with 0 bytes, 0 warnings, no test
removed**. **The one false statement is in the new record**: FD1-REPORT.md states (in its machine-readable
`why_option_A` and again in section 2) and DECISIONS D311 repeats that the JSON key is `referenced by name` in
`FINAL-DOC-REPORT.md`'s `where` **and** `change_site`. `where` does name it and the acceptance names it six times -
so the no-rename decision is sound - but `change_site` contains no such name, so the claim as written is false of
this tree. That is the H-2/RD-2 class this line of batches exists to close, in the batch that closed FD-1, so I
return **fail** on it and nothing else.

## 1. Per-item results

| # | item | result | the evidence I gathered myself |
|---|---|---|---|
| 1 | FD-1, the sites the earlier correction touched | **pass** | `git diff -U0 4a85269 96acd34 -- .spec/bevy/HARDENING-REPORT.md` has hunks at 109, 179, 223, 268, 295 only, none at 156; the field name appears 0 times in that diff; line 156 is `c1508735...` at both revisions. Touched clone-safety sites: section 0 (`-223,3`) and section 3 (`-300,6`); untouched: the machine field at 156. |
| 2 | the machine field is now corrected at the point of the claim | **pass** | Only hunk against 96acd34 is `@@ -156 +156 @@` (1/1); current line `2893d496...`, file `bd373b30...`; the leading JSON block parses; the field's old 571 bytes are a verbatim prefix of the new 1798; the label names the alternative, 5,917,632 bytes, the budget decision, the `runs/**` key-shaped cost and the totals-guard escape. |
| 3 | the report's "three sites" claim is now true of this tree | **pass** | Machine field (156), section 0 and section 3 all carry the scope-decision ruling; the field and section 3 state all three costs, section 0 two of them (see RF-6). The two prose sites are the 96acd34 hunks; the third is the new one. The acceptance's allowed option A was exactly this. |
| 4 | the alternative's measurement and costs | **pass** | Six recordings = 1,072,407 + 1,495,115 + 1,093,652 + 680,974 + 818,938 + 756,546 = **5,917,632** bytes; all six ignore-matched by `.gitignore:9:runs/`, `git ls-files runs` empty. Credential scan (exit 0, 7 passed) reports 2 key-shaped files, fingerprint `5cf81e8f(len 51)`, in `runs/round1` and `runs/round1b` - the cost is real. The totals guard's walk is `repo_root().join("evidence")` only - the escape is real. |
| 5 | the append-only decision log | **pass** | Prefix property holds against 166212f, 69a65d8 and 96acd34 (1,336,933 -> 1,342,560 bytes; numstat `19 0`); line 11686 byte-identical at ef2b0d6, 96acd34 and now; D311 (11709+) names option A/B, rejects the rename, quotes D309's `两处…已更新为新值` and limits it; the D309 history fact reproduces (ef2b0d6: 46 = 423036d0, 129 = 7c09a7ad; now both 423036d0). |
| 6 | the non-renamed key | **pass, with EFD-1** | The reasoning holds on the merits: the key is a literal in `FINAL-DOC-REPORT.md:185` (`where`) and 6 times in `ACCEPTANCE-FINAL-DOC.md`, both untouched, so a rename would dangle them; RF-3 is explicitly recorded as standing in FD1-REPORT.md's `RF-3_field_title` and section 2. But the stated support includes `change_site`, which does not name it - **EFD-1**. |
| 7 | no over-reach | **pass** | Repair diff `69a65d8 -> a80db33` is A `.spec/bevy/FD1-REPORT.md` (258/0), M `.spec/bevy/HARDENING-REPORT.md` (1/1), M `DECISIONS.md` (19/0). `git diff --name-only {69a65d8,96acd34,4a85269} a80db33 -- src tests config .gitattributes Cargo.toml Cargo.lock evidence scripts .githooks` is empty. No measured figure moved: my walk re-derives 118/4,771,139, 4/27,829, 122/4,798,968; `.gitattributes` unchanged; 0 CR bytes under `evidence/`. |
| 8 | the gate | **pass** | Free disk first (F: 37 GiB, D: 127 GiB); nothing deleted, no `rm -rf`, no wildcard, no unexpanded-variable path; own `D:/hof-fd1acc-target` (9.84 GiB, 169 `Compiling` lines); one test process. `cargo test --offline` **literal exit 0** with **800/0/6** over 60 lines, 806 listed, 6 ignored, fmt exit 0 with 0 bytes, 0 `warning:` lines, no test removed (668 `^\s*#\[test\]` lines at both revisions). |
| 9 | the tree for a push | **pass, with the cost criterion unmet** | Ledger 7 lines / 7 nonces / 7 pids / 7 launch images, no `answered_nonce`/`listening_pid`, penultimate = `launch.json` identity (`faf2adda`, pid 47624, answering = listening = spawned, verified true); tripwire, identity, fold, resume (7) and battery (21) tests green in the 806; credential scan green and my own 5-pattern scan finds the `sk-` shape only in the declared fixture; frozen documents byte-identical; `.spec/` bevy only, `evidence/` this engine only, `src/adapter/` bevy+mcp; clean tree; nothing pushed by me. **Fit for a push: no - EFD-1.** |

## 2. Counterexamples I looked for, and what I found

* **A site the batch claims to have corrected but did not.** Not found this time. The machine field at 156 is the
  only line the repair changes and it is the line FD1-REPORT and D311 name; the other two sites are the hunks
  `4a85269 -> 96acd34` really contains.
* **The original wording deleted instead of labelled.** Not found. The old field value is a verbatim prefix of the
  new one (`original_text_kept_verbatim` equals the value parsed out of `git show 96acd34:...`; my own comparison).
* **A report asserting a reference that is not there.** **FOUND** - EFD-1, `change_site`.
* **A cost stated that is not real.** Not found. Both named costs reproduce: key-shaped material in `runs/round1`
  and `runs/round1b` (fingerprint `5cf81e8f`), and the guard rooted only at `evidence/`.
* **A recording committed, or a measured figure moved.** Not found. `git ls-files runs` empty, all six ignore-matched,
  and my walk of `evidence/` gives the same three totals; `evidence/index.json` is untouched by the diff.
* **An edited log entry, or a non-append-only log.** Not found. The prefix property holds against three revisions,
  including `origin/bevy-core`, and line 11686 is byte-identical since `ef2b0d6`.
* **Over-reach hiding in the diff.** Not found. Three document paths only; nothing under `src`, `tests`, `evidence`,
  `config`, `.gitattributes`, `scripts`, `Cargo.*`.
* **A key in the tracked tree.** Not found beyond the declared fixture source. The credential-scan binary ran inside
  my gate (7 passed) and again on its own (exit 0).

## 3. What still stands between this tree and the goal's five criteria

**Decidability** passes: the coverage registry is untouched by this repair and the committed observation still
decides the open gaps. **Reproducibility** passes: `.gitattributes` still pins `evidence/** -text`, `evidence/` has
0 CR bytes, the corpus re-derives to 118 / 4,771,139 inside my gate, and the five clone-weak tests remain the
disclosed boundary (RF-5). **Frozen contract** passes: the six frozen documents are byte-identical across
`4a85269`, `96acd34`, `69a65d8` and now, and no key-shaped material is tracked. **Honest record** is what this
verdict fails on - not on FD-1, which is closed at both halves, but on the new record's claim that the key is named
in `change_site` (EFD-1); the pins, the labels, the gate, the diff, the totals and the clone-safety measurement
all reproduce. **Cost** fails and is expected to remain unmet at about two and a half times the target
(2.600x / 2.549x / 2.604x of the 1,500,000-token per-call target), with `agent.step_limit: 150` binding and the
repeated-success tripwire never firing (RF-1); it is recorded as unmet rather than fixed and needs a human decision,
not another document correction.

The minimum repair for EFD-1 is document-only and one sentence: in `FD1-REPORT.md` (its `why_option_A` and section
2) and in `DECISIONS.md` D311 option 3, name `FINAL-DOC-REPORT.md`'s `clone_safety_sentence.where` and
`ACCEPTANCE-FINAL-DOC.md` as the references, and drop the claim that `change_site` names the key (or, less
desirably, add the key name to `change_site`). Nothing else in the repair needs work: the machine field, the
three-site claim, the measurement, both costs, the append-only log, the diff and the gate are all sound.
