# TASK-DR75-ACCEPTANCE — independent acceptance of the mechanical push gate

```json
{
  "verdict": "pass",
  "criteria": [
    {"id": "C1", "pass": true, "evidence": "With this clone armed (core.hooksPath=F:/moonbit-hof-rs/.githooks) a push to a throwaway bare repo I created (git init --bare /tmp/dr75acc/bare1.git; git push /tmp/dr75acc/bare1.git HEAD:refs/heads/master) exited 1; for-each-ref on the bare repo printed 0 refs. First refusal was the fail-closed ledger diagnosis (ledger missing); after scripts/accept-commit.sh init it became the commit-level refusal naming the unmarked commits with subjects."},
    {"id": "C2", "pass": true, "evidence": "Refusal text names each commit and its subject, the marker source path, `scripts/accept-commit.sh mark <sha> <report.md> pass`, `scripts/accept-commit.sh list`, and the `--no-verify` warning: real output captured in /tmp/dr75acc/sb/A.err. The bare remote stayed empty (A_remote_refs=0)."},
    {"id": "C3", "pass": true, "evidence": "Sandbox /tmp/dr75acc/sb/work (armed with this checkout's installer): after mark c1,c2,c3 the push exited 0, printed `hoh pre-push gate: accepted - 3 commit(s) checked`, and the bare remote's master equalled the tip. In the real repo I deliberately did NOT write a pass record for a74ed4a (no tracked report can honestly authorise it); the mark-then-succeed step was therefore run in the sandbox, whose gate is the identical versioned .githooks/pre-push + library."},
    {"id": "C4", "pass": true, "evidence": "Sandbox case [B]: c1 and c3 marked, c2 (middle of a 3-commit range) unmarked -> push exit 1 and the refusal named ONLY c2 (grep c1=0 c2=1 c3=0), remote still empty. Plant P5 (tip-only range) reproduced the opposite and reddened this test."},
    {"id": "C5", "pass": true, "evidence": "Sandbox case [E]: after master was on the remote, a new unmarked c4 was refused naming only c4 (c1=0 c2=0 c3=0 c4=1). Case [D]: a repeat push exited 0 with `accepted - 0 commit(s) checked` and `Everything up-to-date`."},
    {"id": "C6", "pass": true, "evidence": "Fail-closed, missing: after deleting the ledger and with a pending commit that WAS already accepted, the push exited 1 with `the acceptance ledger is not usable: missing (...)` and the remote did not move (/tmp/dr75acc/sb3.sh: K_exit=1, remote stayed at the previous commit; restoring the ledger made the same push exit 0)."},
    {"id": "C7", "pass": true, "evidence": "Fail-closed, corrupt: a hand-written malformed line made the push exit 1 and the message quoted the raw line (`line 7 is malformed: unknown record kind `this` ... (raw: this line is not a record)`), remote unchanged. Writer/gate format agreement independently re-driven over 6 shapes (short sha, uppercase sha, FAIL, bad stamp, absolute report path -> both invalid; tab-separated record -> both valid; CRLF record -> both invalid quoting the same line); the suite's own 11-entry differential also passes."},
    {"id": "C8", "pass": true, "evidence": "I reproduced the fail-open plant myself: making hoh_validate_ledger return 0 for a missing ledger let a no-op push with NO ledger exit 0 (`accepted - 0 commit(s) checked`, `Everything up-to-date`). The shipped code refuses that same state (C6), so the fix closes the hole."},
    {"id": "C9", "pass": true, "evidence": "Sandbox case [F]: the same push that was refused without the flag succeeded with `git push --no-verify origin master` (exit 0, remote moved, ledger still carries no record for the commit)."},
    {"id": "C10", "pass": true, "evidence": "Judgement: recording the bypass as a documented limit is the right call. A client-side hook cannot stop `--no-verify` (git offers no hook over its own bypass), and the incident this batch answers was a plain `git pull && git push`, which the gate does stop. It is written in .githooks/README.md limit 2, in the refusal text, and in REPORT section 4.3."},
    {"id": "C11", "pass": true, "evidence": "The three limits are in .githooks/README.md section Capability limits (lines 77-87), repeated verbatim in REPORT section 4.3, pointed at from the hook header (line 10-12) and from the installer's last output line. Accuracy measured: (1) `git clone /f/moonbit-hof-rs /tmp/dr75acc/clone` has no core.hooksPath and its push to a fresh bare repo succeeded ungated (M_exit=0, remote got a74ed4a); (2) bypass measured (C9); (3) server-side recommendation, no remote setting changed by the batch (diff touches no config; remote list is still only origin)."},
    {"id": "C12", "pass": true, "evidence": "The task book's premise that CRLF breaks the shebang on this platform does NOT reproduce: a `#!/bin/sh\\r\\n` hook ran under direct execution, `sh`, `bash`, `env -i /bin/sh`, and a real `git push` (CRLF-HOOK-RAN, exit 0; a CRLF copy of the REAL pre-push also ran correctly under git push). The implementer's correction of the dispatcher's premise is right for this toolchain (MSYS bash ignores CR)."},
    {"id": "C13", "pass": true, "evidence": "But dash IS available here (/usr/bin/dash) and does not strip CR: `dash` on a CRLF copy of the real pre-push failed with `16: : not found` / `17: set: Illegal option -` (exit 2), and a minimal CRLF `if` script is a syntax error, while bash printed EQ. So the non-CR-stripping failure is MEASURED, not merely inferred. The `.gitattributes` pin is justified: with core.autocrlf=true an unpinned `scripts/plain.sh` checked out as CRLF (CR=2) while the `-text`-pinned .githooks/pre-push stayed LF (CR=0); this machine's system gitconfig sets core.autocrlf=true."},
    {"id": "C14", "pass": true, "evidence": "Final gate on the frozen tree (after a per-file touch of all 91 `git ls-files '*.rs'`, no wildcard): cargo test --offline exit 0; 54 `test result:` lines tallied to 507 passed / 0 failed / 7 ignored; 0 `failures:` blocks; `cargo test --offline -- --list` = 514; `cargo fmt --check` exit 0. Re-run once more after all plant restores: still 507/0/7, exit 0, fmt 0."},
    {"id": "C15", "pass": true, "evidence": "Attribute census over tracked *.rs: 2e0a852 has 315 `#[test]` + 181 `#[tokio::test]` = 496; HEAD has 333 + 181 = 514; `#[ignore` occurrences 9 -> 9 (7 real attributes in tests/godot_smoke.rs plus 2 in prose/doctext). Name-level diff base vs HEAD: 0 removed, exactly the 18 push_gate names added; tokio test names byte-identical (diff empty). ignored therefore did not grow and no test function was removed."},
    {"id": "C16", "pass": true, "evidence": "All six plants reproduced by me, each reddening its own test against the real files: P1 pre-push refusal exit 1->0 -> an_unmarked_push_is_refused_with_actionable_text FAILED (line 326; push log shows `new branch`); P2 missing ledger -> return 0 -> a_missing_marker_source_refuses_every_push FAILED (line 111); P3 malformed line `continue`d -> a_corrupt_marker_source_refuses_every_push FAILED (line 111) AND the_gate_and_the_writer_agree_on_ledger_validity FAILED (left true right false); P4 remote base dropped -> commits_already_on_the_remote_are_not_rechecked FAILED (line 433); P5 new-branch range narrowed to -n 1 -> one_unmarked_commit_in_a_multi_commit_range_refuses_the_whole_push FAILED (line 617, gate printed `accepted -`); P6 CR added to the shebang -> full binary 17 passed / 1 failed, only the LF invariant test."},
    {"id": "C17", "pass": true, "evidence": "After every plant: `cmp` against an out-of-repo backup identical, `git hash-object` equal to the HEAD blob (pre-push 3c671f9a..., lib 7ce54f53..., push_gate f0e06634...), `git status --porcelain -uall` empty, `git diff --stat` empty, and the reddened test green again. The plant-file hashes I recomputed match the report's."},
    {"id": "C18", "pass": true, "evidence": "Stale cargo fingerprint reproduced end to end on my own copy of tests/push_gate.rs: with case-1's assertion flipped and the file backdated to 2020-01-01, cargo printed `Finished ... in 0.38s` with no `Compiling` and the broken source reported ok (FALSE GREEN); touching only the mtime made cargo print `Compiling hof-rs` and the same bytes FAILED at line 326. Restored byte-exactly and green."},
    {"id": "C19", "pass": true, "evidence": "Trap 1: `git diff --stat 2e0a852..HEAD -- definitely/not/a/real/path` was empty with exit 0, while the same form with `-- .githooks/pre-push` showed 133 insertions. Trap 2: bash `git cat-file -e 'f3e8504^:.githooks/pre-push'` = 128 vs cmd = 0 (the caret is eaten; cmd asked f3e8504 itself). Trap 3: `git ls-files godot-mcp` = 6484 but `git ls-files godot-mcp/godot` = 0 with .gitignore:33 matching, so only the nested repo can judge the engine."},
    {"id": "C20", "pass": true, "evidence": "Canonical scheme (scripts/dr72-digest.ps1, PowerShell 5.1, culture Sort-Object; lowercased repo-relative POSIX path + byte length + lowercase SHA256, tab-joined, LF, no trailing newline, whole text UTF-8 -> SHA256) reproduces the five recorded digests exactly after all my work: t6 135/c144ef32...7a9c03, t7 115/6e4c1595...20fb7, t8 358/6d11b2c6...bdf5a7, t9 83/541e2d81...ca9d, t10 232/31955589...8b8b; `find runs -newermt '2026-10-01 00:00:00'` = 0. Self-validation: the t6 anchor c144ef32...7a9c03 is reproduced. Caveat measured: an independent Python ordinal sort reproduces t6/t7/t9 but not t8/t10 (sort order is part of the convention)."},
    {"id": "C21", "pass": true, "evidence": "PRD-mario.md sha256 4c81c3a9...f5c3a and git hash-object == HEAD blob e9e83ca0...; `.workspace/mario` diff -r (excluding .godot/.hoh/.git/.import) against runs/smoke-t10/versions/ed98d1b8... is empty (exit 0) and 0 files newer than the batch start 2026-10-01 14:50:32; nested engine fc63af77c33368c4a1bb839c95d19750554f63a3 with 0 porcelain lines."},
    {"id": "C22", "pass": true, "evidence": "`git diff --stat 2e0a852..HEAD -- Cargo.toml Cargo.lock` is empty; the batch diff is exactly 8 files (all .gitattributes/.githooks/scripts/tests/report) with 0 files under src/."},
    {"id": "C23", "pass": true, "evidence": "origin/master is still 2f605b039305a244326d429f019d94aee7c4121b, `git rev-list --count origin/master..HEAD` = 10, `git remote` lists only origin (URL-only pushes were used, never the origin remote as a target), and `git reflog show --date=iso origin/master` still has @{0} = 2f605b0 at 2026-10-01 08:13:18 with the previous entry 9e7f8ea at 2026-09-30 20:32:35. .git/FETCH_HEAD (08:13:14, 9e7f8ea) and .git/ORIG_HEAD (2f605b0) still show the pull+push four seconds apart."},
    {"id": "C24", "pass": true, "evidence": "Adjudicated: the pre-existing/unrelated conclusion is sound (mtime window empty; project tree byte-identical to the frozen artifact), but the report's framing is inaccurate - DECISIONS D267 lines 10316-10320 ALREADY explained the 259/4e494547... reading as the pre-t8 caliber (t8 used .workspace/mario as its workspace), so 'DR-68 R6 still open' is wrong; the 148 -> today's 178 step is explained by the t9/t10 rounds (147 files newer than 2026-09-30 08:00, newest 2026-09-30 18:23:08). Defect D1."},
    {"id": "C25", "pass": true, "evidence": "The report explicitly does not claim E1/E3, and the batch changes no product path (0 src/** files), so not claiming them is correct rather than a gap."}
  ],
  "defects": [
    {"id": "D1", "severity": "minor", "what": "REPORT section 7 calls the .workspace/mario digest discrepancy 'pre-existing, unexplained ... DR-68 R6, still open'. DECISIONS D267 (lines 10316-10320) had already explained it: 259/4e494547... was the pre-t8 caliber and the directory was legitimately modified by the t8 round; the implementer did not read that entry.", "reproduction": "Read DECISIONS.md:10316-10320; compare with .spec/hof-rs/tasks/TASK-DR75-REPORT.md section 7. Today's 178 files / dee0a36f... is the post-t9/t10 state (147 files newer than 2026-09-30 08:00)."},
    {"id": "D2", "severity": "minor", "what": "REPORT section 8.2 says the non-CR-stripping-shell consequence is inference because 'no such shell was available in this offline bay, and I did not test one'. A real non-CR-stripping shell IS available in this very environment: /usr/bin/dash.", "reproduction": "`dash` on a CRLF copy of .githooks/pre-push exits 2 with `16: : not found` and `17: set: Illegal option -`; a minimal CRLF if-statement is a syntax error under dash and fine under bash."},
    {"id": "D3", "severity": "minor", "what": "When the hook is run outside a git repository it still refuses (exit 1) but the message degrades to a shell error instead of the intended actionable refusal: hoh_refuse_ledger prints $HOH_LEDGER after hoh_resolve_ledger failed, and `set -u` makes it `HOH_LEDGER: unbound variable`.", "reproduction": "In an empty non-repo directory: `printf 'refs/heads/master <sha> refs/heads/master 0000...' | sh /f/moonbit-hof-rs/.githooks/pre-push origin .` -> exit 1, stderr = REFUSED line followed by `.../pre-push: line 37: HOH_LEDGER: unbound variable`. Low reachability (git does not run pre-push outside a repo) and still fail-closed."},
    {"id": "D4", "severity": "info", "what": "When the remote name git passes has no remote-tracking refs (e.g. `git push <url>`, or a remote never fetched), the new-ref branch falls back to `git rev-list <local> --not --remotes=<name>`, which excludes nothing: the range becomes the entire reachable history. Still fail-closed and explicitly documented ('errs towards refusing'), but the refusal then lists every commit in the repository and the hook does O(history) work.", "reproduction": "In the real repo, `git push /tmp/dr75acc/bare1.git HEAD:refs/heads/master` printed a refusal listing the whole repository history (thousands of lines, output spilled); a named remote with tracking refs gives the concise per-range refusal (sandbox case [A])."},
    {"id": "D5", "severity": "info", "what": "`scripts/install-hooks.sh --uninstall` removes core.hooksPath unconditionally, without checking that it is this checkout's .githooks, so it can remove an unrelated pre-existing hooks path.", "reproduction": "Temp repo with `git config core.hooksPath /some/other/hooks`; run `install-hooks.sh --uninstall` -> prints 'removed core.hooksPath' and the setting is gone (/tmp/dr75acc/unin.sh)."},
    {"id": "D6", "severity": "info", "what": "The ledger record stores a repo-root-relative report path, but `scripts/accept-commit.sh mark` validates it relative to $PWD, so running the documented command from a subdirectory rejects a valid root-relative path.", "reproduction": "From `<repo>/.spec`: `accept-commit.sh mark <sha> .spec/sub/acc.md pass` -> 'the report `.spec/sub/acc.md` does not exist relative to .../.spec' (exit 1); the same command from the root succeeds."}
  ],
  "risks": [
    "The bypass flag remains a real hole: any actor who uses `git push --no-verify`, or who pushes from a clone where the gate is not armed, is unaffected. Only server-side enforcement (branch protection/ruleset) raises that bar; the batch recommends it without touching any remote setting.",
    "The ledger is ordinary writable local state inside .git, with no tamper evidence: anyone who can write the file can authorise any commit. The README states the gate is mechanical, not cryptographic, but this makes the marker source a single low-cost point of failure.",
    "During my acceptance, .git was written by a concurrent actor (COMMIT_EDITMSG at 15:24:45 containing a DR-75 batch commit message that matches no commit, and 79 loose objects with mtime 15:38:46). HEAD, the index, the worktree and all forbidden zones were unchanged at every check, so it did not affect the artifacts under test, but this acceptance cannot attribute those writes.",
    "Tag pushes are reasoned about in the hook but not tested; no test pushes a tag.",
    "Cross-platform behaviour is only partly measured: dash proves the shell-content half of the CRLF hazard, but the Linux kernel shebang path (`/bin/sh^M`) and macOS remain inference."
  ],
  "unverified": [
    "The real remote's current state: origin/master is the local remote-tracking ref (offline rule), so 'the remote still points at 2f605b0' is not a fresh read of GitHub.",
    "Whether the implementer's session issued no network command: I can verify every push in tests/push_gate.rs targets a tempfile bare repo by reading the code, and my own runs issued none, but I cannot audit their process tree.",
    "Server-side settings (GitHub rulesets/branch protection): deliberately not read or written in an offline batch.",
    "Concurrent writers to the ledger: the append is a single printf >> with no locking; the implementer disclosed it and I did not test it.",
    "The 500+ non-push_gate tests beyond their pass/fail totals: I did not re-derive their semantics.",
    "The contents of runs/** beyond digests (DR-73/DR-74 rounds were read only as digests)."
  ]
}
```

- Task under acceptance: `.spec/hof-rs/tasks/TASK-DR75.md` (six offline cases)
- Implementer's report (a lead, never evidence): `.spec/hof-rs/tasks/TASK-DR75-REPORT.md`
- Decision log read for context: `DECISIONS.md` D283 / D284 / D285 / D286, plus D267 (R6)
- Repo: `F:\moonbit-hof-rs`; HEAD `a74ed4a09647d2d53c342bb2c16eed951abf6cb3`; batch `2e0a852..HEAD`; **nothing pushed to the real remote**
- All temporary material lives outside the repository, under `C:\Users\wyl\AppData\Local\Temp\dr75acc\**`
- Runtime: git 2.45.1.windows.1, MSYS bash 5.2.26, real `/usr/bin/dash` available, PowerShell 5.1 for the canonical digest script only (read-only)

## 0. Verdict

**pass**, on the batch's deliverables. The rule really is mechanical now: the gate refuses
today in this clone, refuses every unaccepted commit in a range including one in the middle,
does not re-judge commits the remote already has, refuses when its marker source is
missing or malformed, and lets a marked range through. Six plants each redden their own
test and were restored byte-exactly by me. The gate arithmetic (507/0/7, `--list` 514,
`fmt` clean) reproduces. The three false-green traps and the stale cargo fingerprint
reproduce. Nothing was pushed to the real remote.

The pass carries **3 minor** and **3 info** defects (D1–D6). Two of the minors are in the
report's prose, not in the machinery; D3 is a robustness edge in the hook that is still
fail-closed. None of them changes the mechanical property the batch was built to provide.

The single most important correction of my own understanding: the dispatcher's premise
about CRLF is **false on this platform**, the implementer's correction is **right**, and
the non-CR-stripping failure the implementer called inference is in fact **measurable
here** with `/usr/bin/dash` — which strengthens, rather than weakens, the LF pin.

## 1. Per-item table

| # | What the dispatcher asked | Verdict | Evidence I produced |
|---|---|---|---|
| 1 | Gate refuses right now; mark then push succeeds; every commit judged; mid-range; no re-judging | **pass** | Real repo + temp bare: exit 1, remote 0 refs (missing-ledger text); after `accept-commit.sh init`: commit-level refusal naming 10 commits. Sandbox: [A] refused (3 named), [B] only the middle c2 named, [C] after marking the push landed on the tip, [D] no-op = 0 checked, [E] only the new c4 named. |
| 2 | Fail-closed on removed/corrupt source; missing-ledger fail-open plant; malformed line; writer/gate format agreement | **pass** | Missing ledger refuses even an already-accepted pending commit (`sb3.sh`); corrupt line refuses quoting the raw line; my own P2 plant let a no-op push with no ledger exit 0; 6-shape differential: writer and gate agree. |
| 3 | `--no-verify` bypass; documented limit vs defect | **pass** | [F]: same push refused then succeeded with the flag, ledger unchanged. Judgement: a client hook cannot block its own bypass; documenting it is correct for this threat model. |
| 4 | Three capability limits findable + accurate | **pass** | README §Capability limits; REPORT §4.3; hook header; installer footer. Measured: a fresh clone has no hooksPath and pushes ungated; bypass works; no remote setting touched. |
| 5 | CRLF: what actually happens; is the correction right; is the pin justified | **pass** | CRLF hook ran via direct exec / sh / bash / env -i / real git push. dash (present!) fails on the CRLF hook and on a minimal CRLF if. With `core.autocrlf=true`, unpinned scripts check out CRLF while `-text` files stay LF. |
| 6 | Gate ≥507/0/7, `--list` consistent, ignored flat, no test removed, fmt clean; six plants; stale fingerprint; three traps; forbidden zones; remote; no deps | **pass** | 507/0/7 exit 0 (twice), 54 result lines, `--list` 514, fmt 0; 315+181=496 -> 333+181=514, `#[ignore]` 7 unchanged, 0 names removed, +18 exactly; all six plants red + byte-exact restore; stale fingerprint false-green reproduced; traps 1/2/3; five run digests identical under the canonical scheme; PRD/mario/engine unchanged; 0 src/**; origin reflog unchanged. |
| 7 | Workspace digest mismatch adjudication; E1/E3 claim | **pass with a documented inaccuracy (D1)** | Pre-existing/unrelated: sound (mtime window empty, project tree identical to the frozen artifact). But D267 had already explained the 259/4e494547 reading; the report's "still open" wording is wrong. E1/E3 not claimed — accurate and appropriate. |

## 2. My own plants and counterexamples

Everything below was run by me against the real files, then restored from an out-of-repo
backup and checked four ways (`cmp`, `git hash-object` == HEAD blob, porcelain empty,
`git diff --stat` empty), with the reddened test re-run green.

| Plant | Where | Test that went red | Observed |
|---|---|---|---|
| P1 | `.githooks/pre-push`, refusal `exit 1` -> `exit 0` | `an_unmarked_push_is_refused_with_actionable_text` | panic at line 326; log shows the refusal followed by `* [new branch]` |
| P2 | `.githooks/hoh-acceptance-lib.sh`, missing ledger -> `return 0` | `a_missing_marker_source_refuses_every_push` | panic at line 111, "the reason must say the source is missing" |
| P3 | same file, malformed line -> `continue` | `a_corrupt_marker_source_refuses_every_push` and `the_gate_and_the_writer_agree_on_ledger_validity` | line 111 "must quote the offending line"; differential `left: true right: false` on the 39-char sha |
| P4 | `.githooks/pre-push`, remote base dropped | `commits_already_on_the_remote_are_not_rechecked` | panic at line 433, an already-on-remote commit named again |
| P5 | `.githooks/pre-push`, new-branch range -> `-n 1` | `one_unmarked_commit_in_a_multi_commit_range_refuses_the_whole_push` | panic at line 617; gate printed `accepted -` and allowed the push |
| P6 | `.githooks/pre-push`, CR at end of the shebang line | `the_shell_artifacts_keep_lf_line_endings_and_a_shebang` | full binary: 17 passed / 1 failed, only this one |

Two counterexamples of my own, beyond the report's:

- **P2 fail-open, sharper form.** With the missing-ledger plant in place I pushed a *no-op*
  in a sandbox whose ledger had been deleted: exit 0, `accepted - 0 commit(s) checked`,
  `Everything up-to-date`. That is what "failed open" actually buys an attacker; the
  shipped code refuses that same state.
- **P5 blind spot, independently confirmed.** The planted tip-only gate let the 4-commit
  range through with the unmarked commit in the middle, which is exactly why the case-6
  strengthening (`1b52a19`) is load-bearing rather than cosmetic.

## 3. Independent judgement on each question

**Q1 — does the gate actually refuse right now?** Yes, both in the real repo (missing
ledger, then commit-level once `init` had run) and in the sandbox. The refusal is
actionable: commit ids with subjects, the marker source, the exact `mark` command, and the
`--no-verify` warning. The remote stayed at zero refs in the real repo, and in the sandbox
the refusal was all-or-nothing — a partly-accepted prefix never reached the bare repo. The
middle-commit case is genuinely evaluated (only c2 named when c1/c3 were marked). Commits
already on the remote are not re-judged (only the new commit named).

One nuance worth knowing: I ran the real-repo push **by URL** (`git push <bare-url> ...`),
which is the path where the remote name has no tracking refs; the range then widens to the
whole history and the refusal is enormous. With a named remote and tracking refs the
message is concise. This is fail-closed and documented, and it is D4 (info) rather than a
hole.

**Q2 — fail-closed.** Measured three ways: missing ledger refuses even an otherwise fully
accepted push (the strongest form); a malformed line refuses and quotes the offending line;
the writer and the gate agree on six record shapes I drove through both, including
tab-separated (valid) and a CRLF-terminated record (invalid for both). The reported plant
is true in substance — with the plant the missing-ledger state allowed an empty-range push
— and the fix closes it.

**Q3 — the bypass.** `--no-verify` really does bypass. Recording it as a documented limit
is the right call: no client-side hook can prevent it, the incident this batch answers was
a plain `git pull && git push` that the gate *would* have stopped, and the README/refusal
text/report all say so plainly. The residual risk is unavoidable without server-side
enforcement, which the batch correctly recommends but does not apply.

**Q4 — the capability limits.** Stated in `.githooks/README.md`, repeated in the report,
referenced from the hook's own header and the installer's output. All three are accurate as
far as an offline check can go: the clone test shows a local hook binds nothing elsewhere
(the clone had no `core.hooksPath` and pushed ungated), the bypass is measured, and the
server-side statement is a recommendation with no remote change. The only thing I cannot
verify is GitHub's actual configuration.

**Q5 — CRLF.** The dispatcher's premise does not hold here: I built a CRLF hook and ran it
through direct execution, `sh`, `bash`, `env -i /bin/sh`, and a real `git push` — every one
ran it, and a CRLF copy of the real gate ran correctly under git. So the implementer's
correction is right. Where the implementer is too modest is the word "inference": a genuine
non-CR-stripping shell, `dash`, is installed on this very machine, and the CRLF hook dies
under it (`set: Illegal option -`, `: not found`) while the same script under bash is fine.
The pin is still justified — `core.autocrlf=true` is set machine-wide, and without `-text`
the hook would be checked out CRLF (I reproduced exactly that with a pinned vs unpinned
pair). The honest framing is: *this* platform's git hides the hazard because MSYS bash
ignores CR, but the pin is what keeps the artifact correct for shells that do not.

**Q6 — gates, plants, guards.** Everything the dispatcher listed reproduces (see the table
and C14–C23). Note on the run digests: the canonical convention includes PowerShell's
culture sort, and an independent ordinal sort diverges on t8/t10 — I self-validated against
the t6 anchor `c144ef32…7a9c03` and then used the repository's own read-only script for the
canonical values, which matched all five records.

**Q7 — the two adjudications.** (a) The digest-mismatch reasoning is sound on its
conclusion and incomplete on its provenance: "pre-existing and unrelated to this batch" is
right, and the empty mtime window plus the byte-identical frozen project tree are the right
proofs; but "unexplained / DR-68 R6 still open" is wrong, because D267 already explained
the 259/4e494547 reading as the pre-t8 caliber, and today's 178 is the post-t9/t10 state
(147 files newer than 2026-09-30 08:00, newest 2026-09-30 18:23:08). (b) "Did not claim E1
or E3" is accurate — the report disclaims both, and the batch touches no `src/**`, so the
disclaimer is the correct posture rather than a missing claim.

## 4. Defects (detail)

- **D1 (minor, documentation).** `TASK-DR75-REPORT.md` §7 calls the mario digest discrepancy
  "pre-existing, unexplained … DR-68's R6, still open". `DECISIONS.md` D267 (lines
  10316–10320) had already resolved R6: the 259/`4e494547…` reading is the pre-t8 caliber,
  and the change is expected because the t8 round used `.workspace/mario` as its workspace.
  What remains genuinely new is only the 148 → 178 step, and that is the t9/t10 rounds.
  No functional impact.
- **D2 (minor, documentation).** §8.2 says the non-CR-stripping failure is inference
  because no such shell was available. `/usr/bin/dash` is available and fails on the CRLF
  hook. The conclusion survives; the evidence is stronger than the report claims.
- **D3 (minor, robustness).** Running the hook outside a git repository exits 1 (good) but
  prints `HOH_LEDGER: unbound variable` instead of the intended refusal text, because
  `hoh_refuse_ledger` dereferences `$HOH_LEDGER` under `set -u` after `hoh_resolve_ledger`
  failed. Reachability is low; still fail-closed.
- **D4–D6 (info).** Range widening on a remote name without tracking refs; `--uninstall`
  removing an unrelated `core.hooksPath`; `mark` validating the report path relative to
  `$PWD` although the ledger stores it root-relative.

## 5. Unverified / what I did not check

- The real remote's actual state (offline): `origin/master` is the local tracking ref. The
  reflog is unchanged and still carries only the 08:13:18 entry, but "the remote still
  points at 2f605b0" is not a fresh read of GitHub.
- Whether the implementer issued no network command: the test code only ever pushes to
  `tempfile` bare repos and my own runs were offline, but I cannot audit their process.
- Server-side GitHub settings.
- Tag pushes, concurrent ledger writers, the semantics of the ~496 other tests, and the
  contents of `runs/**` beyond their digests.
- Attribution of the concurrent `.git` writes I observed (COMMIT_EDITMSG 15:24:45, 79 loose
  objects 15:38:46). HEAD, index, worktree and forbidden zones were unchanged throughout.

## 6. Advice for the next batch

1. Correct D1/D2 in the record (a short addendum in the report is enough; `DECISIONS.md`
   already holds the truth for D1).
2. Decide whether D3 deserves a two-line fix (`HOH_LEDGER=${HOH_LEDGER:-<unresolved>}` in
   `hoh_refuse_ledger`) — it is cheap and removes a confusing failure mode.
3. Treat D4 as a UX item, not a hole: consider having the hook cap the printed commit list
   ("and N more") and/or refuse with a single line when the range exceeds a threshold.
4. When the gate is used for real, remember that the ledger must be re-created in any clone
   the dispatcher pushes from, and that `--no-verify` remains available to anyone.
5. Before the next real push, record the acceptances for `origin/master..HEAD` with
   `scripts/accept-commit.sh mark <sha> .spec/hof-rs/tasks/TASK-DR75-ACCEPTANCE.md pass`
   (this file), then push — and add the ledger line to the decision log as D283's rule 2
   requires.
