# TASK-DR75-REPORT — the push rule as a mechanical gate: a versioned `pre-push` hook, an acceptance ledger, an idempotent installer and an offline suite

- Task book: `.spec/hof-rs/tasks/TASK-DR75.md` (**sole task source**)
- Upstream: `DECISIONS.md` **D283** / **D284** (the out-of-gate push of 2026-10-01 08:13:18 and the user's choice (A)) → **D285** (DR-74 acceptance `pass`, push unblocked)
- Repo: `F:\moonbit-hof-rs` (outer). **Offline batch**: no Godot, no external port, no network, no model endpoint, no real-machine round
- Batch start: `2e0a852` (HEAD when this session began); batches end at `1b52a19` + the commit carrying this report
- Commits (all local, **nothing pushed**): `6c21b5c` (red suite) → `f3e8504` (gate + ledger + installer + pin) → `64ba17f` (`cargo fmt`) → `1b52a19` (case-6 strengthened) → this report
- **E1 / E3 are not touched by this batch and are not claimed.** No product path (`src/**`) was changed: the diff is `.gitattributes`, `.githooks/**`, `scripts/*.sh`, `tests/push_gate.rs`.

## 1. Conclusion + the real gate

**The rule is now mechanical.** A versioned `pre-push` hook refuses any commit that has no `pass`
record in the acceptance ledger, whoever runs `git push`. Git hands the hook the refs it is about to
update; the hook resolves the commit range each of them adds, looks each commit up in the ledger, and
exits non-zero with an actionable refusal if any of them is unrecorded. The gate is armed in this
repository (`core.hooksPath = F:/moonbit-hof-rs/.githooks`), and it refuses today (`§4`).

### 1.1 The gate, verbatim (final run on the frozen tree)

```
$ git ls-files '*.rs' | wc -l
91
$ cargo fmt --check                                    # FMT_EXIT=0
$ for f in $(git ls-files '*.rs'); do touch "$f"; done  # 91 files, one by one, no glob
touched=91
$ cargo test --offline                                  # CARGO_EXIT=0
...
test result: ok. 18 passed; 0 failed; 0 ignored; 0 measured; 0 filtered out; finished in 8.90s   <- tests/push_gate.rs
...
test result: ok. 0 passed; 0 failed; 0 ignored; 0 measured; 0 filtered out; finished in 0.00s    <- doc-tests
$ grep -c '^test result:' suite-final.txt
54
$ awk tally over the 54 result lines
passed=507 failed=0 ignored=7
$ cargo test --offline -- --list | grep -c ': test'
514                                                    # 514 = 507 + 7
$ grep -c '^failures:' suite-final.txt
0
```

- **507 passed / 0 failed / 7 ignored, exit 0**, and `cargo fmt --check` exit 0. Baseline was
  **489 / 0 / 7**; the difference is exactly the **18** new tests in `tests/push_gate.rs`.
- **`ignored` did not grow** (7 before and after; they are the seven `e0_..e6_` functions of
  `tests/godot_smoke.rs`), and **no test function was removed** — recomputed from the trees, not
  trusted:

```
rev 2e0a852 (batch start): attributes=496 ignored_attrs=7
  distinct names = 496
worktree: attributes=514 ignored_attrs=7
  distinct names = 514
removed names (in 2e0a852, not in the worktree) = 0
added names (in the worktree, not in 2e0a852) = 18
```

- **Rebuild discipline**: the per-file `touch` loop over `git ls-files '*.rs'` (91 files, **no
  wildcard**), run immediately before the final gate. Files were written only with the file tools'
  literal replacement (plus `cargo fmt` for the Rust test file); **no PowerShell 5.1
  `Get-Content -Raw`/`Set-Content` was used anywhere in this batch**, and no file's line endings were
  rewritten. Raw-byte check of every artifact this batch touches:

```
$ python -c "…b.count(b'\r')…"
.githooks/pre-push                     bytes=  5994 CR=0 CRLF=0 LF=133 line1=b'#!/bin/sh'
.githooks/hoh-acceptance-lib.sh        bytes=  5853 CR=0 CRLF=0 LF=181 line1=b'#!/bin/sh'
.githooks/README.md                    bytes=  4544 CR=0 CRLF=0 LF=102 line1=b'# `.githooks/` …'
scripts/install-hooks.sh               bytes=  3791 CR=0 CRLF=0 LF=97  line1=b'#!/bin/sh'
scripts/accept-commit.sh               bytes=  7717 CR=0 CRLF=0 LF=185 line1=b'#!/bin/sh'
tests/push_gate.rs                     bytes= 40176 CR=0 CRLF=0 LF=1117 line1=b'//! DR-75 …'
```

### 1.2 What was delivered

| # | Deliverable | Landing |
|---|---|---|
| ① | versioned, fail-closed `pre-push` gate | `.githooks/pre-push` (133 lines, mode `100755`) |
|  | its shared ledger logic (single source of truth) | `.githooks/hoh-acceptance-lib.sh` (181 lines) |
| ② | marker mechanism (writer + verifier + cross-check) | `scripts/accept-commit.sh` (185 lines, `100755`), ledger in the git directory |
| ③ | idempotent install + the limits in writing | `scripts/install-hooks.sh` (97 lines, `100755`), `.githooks/README.md` (102 lines) |
|  | line-ending pin | `.gitattributes` (`.githooks/** -text`, `scripts/*.sh -text`) |
| ④ | offline suite | `tests/push_gate.rs` (1117 lines, 18 tests, all green, none ignored) |

## 2. ① The hook, and the `pre-push` stdin protocol

### 2.1 Protocol handling

`git push` writes one line per ref to be updated:

```
<local ref> <local sha> <remote ref> <remote sha>
```

The hook reads stdin line by line, splits each line into exactly four fields (`set -f` is on, so
untrusted text can never glob-expand), and refuses a line that does not have four fields rather than
skipping it. For each line it computes **the commits the push would add to that remote**:

| shape | range evaluated | why |
|---|---|---|
| `local sha = 0000…0` | **none** — allowed, explicitly, with a logged line | a deletion adds no commit; there is nothing an acceptance could cover |
| `remote sha = 0000…0` (ref the remote does not have) | `git rev-list <local> --not --remotes=<target remote>` | the reference remote's tracking refs say what that remote already contains, so commits it already has are **not re-judged**; a stale tracking set only *widens* the range, i.e. it errs towards refusing |
| both non-zero | `git rev-list <remote sha>..<local sha>` | the book's range: exactly what this push adds |
| the range cannot be computed (the advertised remote base is not in this repository) | **refuse**, naming `git fetch <remote>` | an unevaluable push is refused, never assumed acceptable (fail closed) |

Every commit in the resulting range is looked up in the ledger; a commit is accepted only if it
carries a validated `accepted <sha> … pass …` record. Duplicated commits across several ref lines are
judged once (a `seen` list), and the failure is **all-or-nothing at the git level** — git aborts the
whole push when `pre-push` exits non-zero, which the suite asserts by checking that the remote is
still empty after a refusal.

### 2.2 Fail-closed decisions, and why

- **The marker source is judged before the refs are read.** If the ledger is missing, unreadable, a
  directory, or carries any malformed record line, the hook refuses *every* push — including a
  deletion. Reason: a gate whose marker source is broken is not a working gate, and "the ledger is
  broken" must never be a state in which pushes succeed. The cost is stated and tested: the refusal
  in that case names the source, not the commits (the tests assert both the presence of the source
  diagnosis and the absence of any commit name).
- **The library is not optional.** If `.githooks/hoh-acceptance-lib.sh` is missing or unreadable next
  to the hook, the hook refuses with a distinct message instead of running without its rules.
- **Format is strict and exact:** 40 lowercase hex, a repo-root-relative report path ending in `.md`,
  the verdict exactly `pass` (case-sensitive), an ISO-8601 UTC stamp `YYYY-MM-DDTHH:MM:SSZ`, an
  optional single-space-separated note. Comment lines (`#`) and blank lines are ignored. A hand-edited
  CRLF ledger therefore fails closed with the offending line quoted; the writer always writes LF.
- **No environment-variable override** of the ledger path: it is derived from
  `git rev-parse --absolute-git-dir`, so there is no second, quieter way to point the gate somewhere
  else. (`--no-verify` remains the one documented hole, §5.)

### 2.3 Refusal text (real output, from the arm-in-place check)

```
hoh pre-push gate (DR-75): REFUSED - these commits have no passing acceptance record:

    39c2c21cd4ae16a1b6c066da15c321b83c4c5b48  the acceptance report
  remote: origin (/tmp/dr75demo.cSbGGn)
  marker source: ……/.git/hoh-accepted-commits.txt
  Once an independent acceptance passes, record it for each commit:
      scripts/accept-commit.sh mark <sha> <report.md> pass
  See what is already recorded: scripts/accept-commit.sh list
  This is the repository's hard constraint: nothing is pushed before an acceptance
  passes.  Do not bypass the gate with `git push --no-verify`; that flag is a
  documented hole in this gate, not an authorisation (.githooks/README.md).
```

It names the unrecorded commits **with their subjects**, the marker source, how to record an
acceptance, and the warning about the bypass flag.

## 3. ② The marker mechanism, and the commit → report → push cross-check

### 3.1 Form chosen: a repository-local record file in the git directory

```
<absolute git dir>/hoh-accepted-commits.txt

accepted <40-hex-commit> <report.md> pass <YYYY-MM-DDTHH:MM:SSZ> [note]
```

**Why this and not `git notes` or a versioned list.** A *versioned* ledger cannot authorise its own
tip: the commit that recorded "X was accepted" would itself be unrecorded, and every way of closing
that gap needs an exemption from the gate — which is how gates rot. A local file also makes
"missing/corrupt marker source" an unambiguous, fail-closed condition (a notes ref is *legitimately*
absent, so "absent" could not mean "refuse"). The honesty cost is stated as a capability limit in §4
and in `.githooks/README.md`: **the ledger does not travel with a clone**, so a fresh clone must
re-record the acceptances of the commits it intends to push.

`scripts/accept-commit.sh` writes and checks it:

```
$ scripts/accept-commit.sh init
accept-commit: created ……/.git/hoh-accepted-commits.txt
accept-commit: 0 record(s); ledger: ……/.git/hoh-accepted-commits.txt
accept-commit: no commit is marked yet, so every push is refused until one is
$ scripts/accept-commit.sh mark 39c2c21… .spec/hof-rs/tasks/TASK-DR75-DEMO-ACCEPTANCE.md pass "DR-75 demo"
accept-commit: recorded accepted 39c2c21cd4ae16a1b6c066da15c321b83c4c5b48 .spec/hof-rs/tasks/TASK-DR75-DEMO-ACCEPTANCE.md pass 2026-10-01T07:13:47Z DR-75 demo
$ scripts/accept-commit.sh show 39c2c21…
record: accepted 39c2c21… .spec/hof-rs/tasks/TASK-DR75-DEMO-ACCEPTANCE.md pass 2026-10-01T07:13:47Z DR-75 demo
report: .spec/hof-rs/tasks/TASK-DR75-DEMO-ACCEPTANCE.md
report verdict line: verdict: pass
report commit: 39c2c21 the acceptance report
$ od -c .git/hoh-accepted-commits.txt | tail -2
…   D   R   -   7   5       d   e   m   o  \n
```

`mark` refuses, by construction: any verdict other than `pass` (and `PASS` is not `pass`); a report
path that is not a repo-root-relative `.md`; a report that does not exist, is empty, or is **not
tracked by git**; a target that is not a commit. It is idempotent for an identical record and refuses
a second, different report for the same commit. `verify` reports structural validity (and says
explicitly when zero commits are marked, so "valid" is not mistaken for "the gate will let you push").
`list` prints the records; `show` prints the record **next to the cited report's own verdict line and
the report's commit**, which is the human cross-check.

### 3.2 The chain is checkable in both directions

- commit → report: the record's second field is the report path, and the suite asserts the cited
  report is **tracked by git** and that `git log -1 --format=%s -- <report>` finds the report's commit.
- report → commit: the report names the batch; `scripts/accept-commit.sh show <sha>` prints the
  record, the report's `verdict:` line and the report's own commit; the ledger line carries the
  commit so a `git log` reader can go either way.
- push → the pair: the ledger lives in the git directory, untouched by any checkout, and each record
  carries the stamp of when it was written.

Single source of truth: the hook and the writer **both source**
`.githooks/hoh-acceptance-lib.sh`, and `tests/push_gate.rs::the_gate_and_the_writer_agree_on_ledger_validity`
drives an 11-entry corpus (valid record, tab-separated record, blank line, comment, 39-char sha,
uppercase sha, `fail` verdict, bad stamp, misspelled kind, report without a path, missing stamp)
through **both** and requires their verdicts to agree — so the two cannot drift apart silently.

## 4. ③ Enabling it, verifying it, and its capability limits

### 4.1 Enable (idempotent)

```sh
scripts/install-hooks.sh          # sets core.hooksPath to <this checkout>/.githooks
scripts/install-hooks.sh --uninstall   # one-command rollback
```

Real output in this repository, run twice:

```
install-hooks: core.hooksPath: <unset> -> F:/moonbit-hof-rs/.githooks
install-hooks: every push made here now passes through F:/moonbit-hof-rs/.githooks/pre-push
install-hooks: verify with: git config --get core.hooksPath
install-hooks: this is a local, bypassable control - see .githooks/README.md for its limits
$ scripts/install-hooks.sh          # second run
install-hooks: already installed: core.hooksPath = F:/moonbit-hof-rs/.githooks
install-hooks: nothing to do (this command is idempotent)
```

It writes only this repository's local git config, never a remote setting, and never touches the
network. It refuses to arm a hooks directory that lacks `pre-push`/`hoh-acceptance-lib.sh`, and it
fails if it is not run inside a repository. `core.hooksPath` is set to an **absolute** path (via
`pwd -W` on this platform) so the gate is found from any subdirectory; the book's **relative**
spelling works too — measured in a sandbox: `core.hooksPath = .githooks` read back as `.githooks` and
the hook ran and refused (`relative_hooksPath_push_exit=1`).

### 4.2 One-line proof that it is really in effect

```sh
printf 'refs/heads/master %s refs/heads/master %s\n' "$(git rev-parse HEAD)" "$(git rev-parse HEAD)" | .githooks/pre-push origin .
```

Measured here (read-only; the hook cannot write anything):

```
$ git config --get core.hooksPath
F:/moonbit-hof-rs/.githooks
$ ls .git/hoh-accepted-commits.txt
ls: cannot access '.git/hoh-accepted-commits.txt': No such file or directory
$ printf 'refs/heads/master %s refs/heads/master %s\n' "$(git rev-parse HEAD)" "$(git rev-parse HEAD)" | .githooks/pre-push origin .
hoh pre-push gate (DR-75): REFUSED - the acceptance ledger is not usable: missing (F:/moonbit-hof-rs/.git/hoh-accepted-commits.txt)
  … (how to create it, and the --no-verify warning) …
one_liner_exit=1
```

**Operational consequence for the dispatcher**: the gate is armed in this clone, so the DR-75 push
will be **refused** until every commit in `origin/master..HEAD` has a record. After the independent
acceptance passes:

```sh
scripts/accept-commit.sh init
for c in $(git rev-list origin/master..HEAD); do
    scripts/accept-commit.sh mark "$c" .spec/hof-rs/tasks/TASK-DR75-ACCEPTANCE.md pass
done
git push origin master
```

### 4.3 Capability limits (stated verbatim, and in `.githooks/README.md`)

1. **钩子是本地性的** ⇒ **从另一个克隆/另一台机器推送时本钩子不生效**。
   The hook is local: pushing from another clone or another machine does not go through this gate at
   all. (This includes the acceptance ledger: it lives in this clone's git directory and does not
   travel.)
2. **`git push --no-verify` 可绕过** ⇒ **它不是密码学保证，只是机械防呆**。
   The bypass flag exists: this is mechanical discipline, not a cryptographic guarantee, and it
   cannot stop anyone who decides to route around it.
3. **真正的强制需要服务端**（GitHub 分支保护/ruleset、部署密钥最小权限等）——**给出建议但不要替用户改远端设置**。
   Real enforcement belongs on the server side (GitHub branch protection/rulesets, a least-privilege
   deploy key). That is the recommended fix for an actor you cannot control; **no remote setting was
   changed by this batch**.

## 5. ④ The six offline cases — real output

All of them run against a `tempfile::TempDir` bare repository that stands in for `origin`, through
**real `git push`**, with `core.hooksPath` pointed at this checkout's versioned `.githooks`. Nothing
touches the network, the real remote, `runs/**`, Godot or a model endpoint. The whole binary:

```
$ cargo test --offline --test push_gate
running 18 tests
… 18 lines, all ok …
test result: ok. 18 passed; 0 failed; 0 ignored; 0 measured; 0 filtered out; finished in 8.90s
```

**Before the implementation (the red-first evidence, commit `6c21b5c`)** — the same file, with no hook
in the tree:

```
$ cargo test --offline --test push_gate -- --exact a_missing_marker_source_refuses_every_push
thread 'a_missing_marker_source_refuses_every_push' panicked at tests\push_gate.rs:462:5:
a missing marker source must refuse the push:
To C:/Users/wyl/AppData/Local/Temp/.tmp2WJLyl/origin.git
 * [new branch]      master -> master
test result: FAILED. 0 passed; 1 failed; 17 filtered out
```

(i.e. an unaccepted commit reached the throwaway remote), and the whole red suite was
`0 passed; 18 failed`. That is the behaviour DR-75 exists to remove.

| # | case required by the book | test | real evidence |
|---|---|---|---|
| 1 | unmarked ⇒ refused | `an_unmarked_push_is_refused_with_actionable_text` | non-zero exit; refusal names the commit **and its subject**, the marker source, `scripts/accept-commit.sh mark`, and `--no-verify`; the remote is asserted still empty |
| 2 | marked ⇒ allowed | `a_marked_push_succeeds` | push exit 0 and `git -C origin.git rev-parse master` == the marked sha |
| 3 | already-on-remote not re-judged | `commits_already_on_the_remote_are_not_rechecked`, `a_push_with_nothing_new_is_allowed` | a history that predates the gate (seeded with the documented hole) is **not named** when the new range is judged; after marking the range the push lands; a second (no-op) push is exit 0 with no refusal |
| 4 | fail closed | `a_missing_marker_source_refuses_every_push`, `a_corrupt_marker_source_refuses_every_push` | deleted ledger ⇒ refuse (`missing`, names the path); a garbage line ⇒ refuse and **quotes the offending line**; the remote stays empty in both |
| 5 | `--no-verify` is a known limit, not a failure | `the_bypass_flag_is_a_recorded_known_limit` | the same push is first refused without the flag, then **succeeds with it** (`* [new branch]`), and the ledger still carries no record — recorded as a documented limit of a local hook |
| 6 | one unmarked commit in a range ⇒ whole push refused | `one_unmarked_commit_in_a_multi_commit_range_refuses_the_whole_push` | the unmarked commit sits **in the middle** of a 4-commit range with a marked tip; the refusal names it, does not name the accepted neighbours, the remote is still empty; marking it then pushes to the tip |

Boundaries the book demanded be handled explicitly, also covered:

- `deleting_a_remote_branch_is_allowed_and_carries_no_commit_check` — `0000…0` local sha ⇒ allowed,
  the hook says so, and the remote branch really disappears;
- `a_new_remote_branch_checks_every_commit_it_adds` — the zero-remote-sha path checks the new branch's
  commits and excludes what the target remote already has;
- `an_unknown_remote_object_refuses_instead_of_skipping` — a remote base this clone does not have ⇒
  refuse with "run `git fetch`";
- `the_hook_can_be_run_by_hand_on_a_synthetic_ref_line` — the protocol itself: accepted no-op allowed,
  deletion allowed, empty stdin allowed, a three-field line refused as malformed;
- `the_install_step_is_idempotent_and_arms_the_gate`,
  `the_installer_refuses_a_checkout_without_the_versioned_hooks`,
  `the_marker_refuses_a_missing_report_and_a_non_pass_verdict`,
  `the_ledger_records_the_report_path_and_the_pass_verdict`,
  `the_gate_and_the_writer_agree_on_ledger_validity`,
  `the_shell_artifacts_keep_lf_line_endings_and_a_shebang`.

## 6. Non-emptiness: six controlled plants, each red, each restored byte-exactly

Method: an out-of-repo copy (`cp` → `/tmp/dr75/backups/`), a literal one-place edit with the file
tools, the targeted test run, then `cp` back. Restore is proved four ways each time — `cmp` against
the backup, `git hash-object` equal to the `HEAD:` blob, `git status --porcelain -uall` empty,
`git diff --stat` empty — and the test is then shown green again. The plants are all in shell files,
so **no compilation is involved**: the bytes under test are exactly the bytes on disk.

| plant | file / place | its own test goes red with | restore proof |
|---|---|---|---|
| **P1** | `pre-push` — the unaccepted-commit refusal's `exit 1` → `exit 0` | `an_unmarked_push_is_refused_with_actionable_text`: panicked at `"an unmarked commit must not reach the remote"`, and the log shows the refusal text **followed by** `* [new branch] master -> master` | `cmp` identical; hash `3c671f9a…` == `HEAD`; status/diff empty; test green again |
| **P2** | `hoh-acceptance-lib.sh` — a missing ledger returns 0 (treated as empty) | `a_missing_marker_source_refuses_every_push`: panicked at `"the reason must say the source is missing"`, refusal became the commit-level one | `cmp` identical; hash `7ce54f53…` == `HEAD`; status/diff empty; green |
| **P3** | `hoh-acceptance-lib.sh` — a malformed record line is `continue`d instead of refused | `a_corrupt_marker_source_refuses_every_push`: panicked at `"the reason must quote the offending line"`; **and** `the_gate_and_the_writer_agree_on_ledger_validity`: `the writer's verdict on 'accepted a7e5d9b1…(39 chars)…'` → `left: true right: false` | `cmp` identical; hash `7ce54f53…` == `HEAD`; status/diff empty; green |
| **P4** | `pre-push` — the remote base is dropped (range widened to all history) | `commits_already_on_the_remote_are_not_rechecked`: panicked at `"a commit already contained by the remote must not be named again"` | `cmp` identical; hash `3c671f9a…` == `HEAD`; status/diff empty; green |
| **P5** | `pre-push` — the new-branch range narrowed to `git rev-list -n 1` (tip only) | `one_unmarked_commit_in_a_multi_commit_range_refuses_the_whole_push`: the gate printed `accepted - 1 commit(s) checked` and **allowed** the push, leaking the unmarked mid-range commit | `cmp` identical; hash `3c671f9a…` == `HEAD`; status/diff empty; green |
| **P6** | `pre-push` — a single CR added to the shebang line (`sed -i '1s/$/\r/'`) | `the_shell_artifacts_keep_lf_line_endings_and_a_shebang` failed; **the other 17 tests stayed green** (see §8.2) | `cmp` identical; hash `3c671f9a…` == `HEAD`; status/diff empty; green |

Two notes on the plant methodology itself, in the interest of non-vacuity:

- **P5 had to be retargeted.** The first attempt patched the `remote sha..local sha` branch, and no
  test went red — because the case-6 test pushes a **new** remote branch and therefore exercises the
  *other* branch of the condition. Rather than accept a plant that proved nothing, I retargeted it to
  the exercised path (and it then went red). Verifying the red, instead of assuming it, is the point.
- Because of P5, **the case-6 test was strengthened** in the same batch: the unmarked commit now sits
  in the *middle* of the range with a marked tip (`1b52a19`). A gate that only ever looked at the tip
  passed the old shape; it cannot pass the new one. The old shape was a real blind spot (a tip-only
  gate would leak every mid-range commit), so this is a test strengthened by a plant, not a test bent
  to fit one.

## 7. Forbidden-zone self-check (raw output)

**Five `runs/**` baselines, before and after the whole batch, with the canonical digest convention**
(`scripts/dr72-digest.ps1`: PowerShell 5.1, recursive `-Force -File`, repo-root-relative lowercased
POSIX path + byte length + lowercase SHA256, tab-joined, LF, no trailing newline, `Sort-Object`
culture order, whole text UTF-8 → SHA256):

```
runs/smoke-t6   135  c144ef3219e21dd322978e41a5531d53dee270619c026585505920f9277a9c03  newest 2026-09-29 02:32:01
runs/smoke-t7   115  6e4c1595753c2cdefb16e4d2e5f05242ca202c70c81a93e98ae2b9c92b520fb7  newest 2026-09-29 14:41:14
runs/smoke-t8   358  6d11b2c61ec507b5f02525ddc0e7f7adb08763cd2439a4b08788b7fe51bdf5a7  newest 2026-09-30 07:58:28
runs/smoke-t9    83  541e2d814e563ba667c95bde49765d05e44cf11aa5ab90b2f44931f30136ca9d  newest 2026-09-30 11:27:29
runs/smoke-t10  232  319555896964ce1526f72a33cb239bf389fe29bcde23841764d13c57dfb38b8b  newest 2026-09-30 18:23:08
```

- **Convention self-validation**: `smoke-t6` reproduces the anchor value quoted across DR-54/57/59/61/
  62/64/66/67 and DR-72/74 (`c144ef32…7a9c03`), and t7/t8/t9/t10 reproduce the DR-72/DR-74 recorded
  values verbatim — so a "nothing changed" reading is being taken with the right ruler.
- **Write/delete check** (a delete would show up as a missing file in the digest, but the window
  matters too): nothing under `runs/**` has an mtime at or after the batch start, and nothing at all
  for the day:

```
$ find runs -newermt '2026-10-01 14:50:32' | wc -l     # batch start 6c21b5c
0
$ find runs -newermt '2026-10-01 00:00:00' | wc -l
0
$ find .workspace/mario -newermt '2026-10-01 14:50:32' | wc -l
0
```

**`.workspace/mario/**`**: not modified. The strongest available statement is the one the DR-74
acceptance used — the live project tree under the runtime exclusion set is byte-identical to the
frozen round artifact:

```
$ find .workspace/mario -type f -not -path '*/.godot/*' -not -path '*/.hoh/*' -not -path '*/.git/*' -not -path '*/.import/*' | wc -l
17
$ diff -r -x .godot -x .hoh -x .git -x .import .workspace/mario runs/smoke-t10/versions/ed98d1b8…
mario_diff_exit=0      # identical
```

**Honest caveat about the older mario digest**: the canonical-convention digest of the *raw* mario
tree now reads `178 files / dee0a36f357c440d078c652d4d4b8990af1a63b88d282c1e36c04a16d006cc94`, whereas
DR-59/61/62/64/66/67 recorded `259 files / 4e494547416b2e87ba025d686afef9447d4f92c027917d1790e6fc9deaeaa84a`.
This discrepancy is **not** mine and is **not new**: DR-68 §R6 already recorded "D264 says 259 /
`4e494547…`; I now read 148 files and could not reproduce it with four sort orders or two BOM
combinations" and asked the dispatcher to confirm the original scope and moment. I cannot resolve it
in an offline batch (I have no "before" snapshot of today). What the batch *can* prove, and does:
the mtime window is empty, and the project tree (the part the batch's prohibitions are about) is
byte-identical to the frozen artifact. The `178`-vs-`259` question is logged here as a
**pre-existing, unexplained** measurement difference, not as a claim about this batch.

**`PRD-mario.md`**: untouched —

```
$ sha256sum .spec/hof-rs/PRD-mario.md
4c81c3a9995f0b3afdf01421a0c3be88573cceefc284ce9bafbfda141f0f5c3a   # the recorded value
mtime 2026-09-20 23:21:21
$ git hash-object .spec/hof-rs/PRD-mario.md ; git rev-parse HEAD:.spec/hof-rs/PRD-mario.md
e9e83ca03e589c97fc1c2ee313526d582e7fe47b
e9e83ca03e589c97fc1c2ee313526d582e7fe47b
```

**`DECISIONS.md`**: not modified by this batch — `git diff --stat HEAD -- DECISIONS.md` is empty and
none of my four commits touches it (the entries `D283`–`D286` are the dispatcher's: `348c668`,
`18e7f95`, `0392d2e`, `2e0a852`). I have no write access to it and did not write to it.

**Nested engine tree** (trap ③ done properly): the outer repo does not track it, so the outer `git
diff` is a *null judgment* — checked with both a matching and a non-matching pathspec:

```
$ git -C godot-mcp/godot rev-parse HEAD
fc63af77c33368c4a1bb839c95d19750554f63a3
$ git -C godot-mcp/godot status --porcelain -uall | wc -l
0
$ git ls-files godot-mcp | wc -l          # the pathspec really matches
6484
$ git ls-files godot-mcp/godot | wc -l    # the outer repo tracks nothing there
0
$ git check-ignore -v godot-mcp/godot
.gitignore:33:godot-mcp/godot/	godot-mcp/godot
```

**No new dependency**: `git diff --stat 2e0a852..HEAD -- Cargo.toml Cargo.lock` is empty. The batch
diff is `7 files changed, 1824 insertions(+)` (`.gitattributes`, 3 `.githooks` files, 2 `scripts`, the
test file) — no `src/**`.

**Not pushed to the real remote**:

```
$ git rev-parse origin/master
2f605b039305a244326d429f019d94aee7c4121b
$ git rev-list --count origin/master..HEAD
9
$ git reflog show origin/master | head -1
2f605b0 refs/remotes/origin/master@{0}: update by push     # still the 08:13:18 entry of D284
$ git remote -v | head -1
origin	https://github.com/shiyukonghui/hof-rs.git (fetch)
```

`origin/master` is unchanged and its reflog still carries exactly the `2f605b0 … update by push` entry
that D283/D284 traced; the 9 local commits are all unpushed. **No network command was issued in this
batch** — every `git push` the tests perform goes to a `tempfile` bare repository.

**No temporary object left in the repository**: `git status --porcelain -uall` is empty (this report
is the only file that will be added), `git diff --cached --stat` is empty, and all scratch work for
this batch lives under `/tmp/dr75/**` (outside the repository): backups, red outputs, name lists and
the guard logs.

## 8. The false-green traps and the two batch-specific hazards (measured)

### 8.1 The three named false-green traps, reproduced

```
### trap ①: git diff with a pathspec that matches nothing
$ git diff --stat 2e0a852..HEAD -- definitely/not/a/real/path
trap1_exit=0                       # empty output AND exit 0
$ git diff --stat 2e0a852..HEAD -- .githooks/pre-push
 .githooks/pre-push | 133 ++++++++   # the same command form, with a pathspec that really matches
```

Reading: an empty diff only means "unchanged" **after** the pathspec is shown to match something.

```
### trap ②: cmd eats the caret
bash : git cat-file -e 'f3e8504^:.githooks/pre-push'  -> 128
       fatal: path '.githooks/pre-push' exists on disk, but not in 'f3e8504^'
cmd  : git cat-file -e f3e8504^:.githooks/pre-push    -> 0     (the ^ is eaten; it asked f3e8504)
control both revisions have DECISIONS.md : bash 0 / cmd 0
control neither revision has the path    : bash 128
```

Reading: `rev^` queries are done in bash only; a `0` from cmd does not carry evidence here. (All
revision queries in this report were run in bash.)

```
### trap ③: the outer repository does not track the engine tree
$ git ls-files godot-mcp | wc -l        -> 6484   (the pathspec matches)
$ git ls-files godot-mcp/godot | wc -l  -> 0      (nothing is tracked there)
$ git check-ignore -v godot-mcp/godot   -> .gitignore:33:godot-mcp/godot/
```

Reading: "the engine tree is unchanged" can only be shown with the **nested** repository
(`fc63af77…`, 0 porcelain lines), never with an outer `git diff`.

### 8.2 The CRLF hazard, measured honestly

The book names this as the batch's high-risk trap: *"故意让钩子脚本保持 LF 行尾（Windows 下 CRLF 会让
shebang 失效——这是本批的高危陷阱，必须实测并说明）"*. **Measured: on this toolchain it does not do
that.** With `#!/bin/sh\r\n` (confirmed byte-wise by `od -c`: `# ! / b i n / s h \r \n`):

```
file : …hooks/pre-push: POSIX shell script, ASCII text executable, with CRLF line terminators
direct execution  : CRLF-HOOK-RAN   direct_exec_exit=0
sh  <script>      : CRLF-HOOK-RAN   sh_exit=0
real git push with a +x CRLF hook : CRLF-HOOK-RAN ; * [new branch] master -> master
```

and the controlled plant P6 confirms it at suite level: the planted CRLF shebang turned **only** the
LF-invariant test red, while **all 17 functional tests — including six real `git push` flows through
that very hook — stayed green**. The mechanism is that Git for Windows runs hooks through its own
`sh.exe` (MSYS2), which strips CR at end of line.

So the pin is not a fix for an observed failure here; it is a **portability and invariant guard**, and
I am reporting it as such rather than repeating a claim I could not reproduce. On a `sh` that does not
strip CR (a plain POSIX shell on Linux/WSL or in CI) the last token of every line would carry the CR —
`exit 0\r`, a `case` pattern, a comparison — so the file must be LF to be portable. **That consequence
is inference, not measurement**: no such shell was available in this offline bay, and I did not test
one. What *is* measured: this machine's system gitconfig (`C:/Program Files/Git/etc/gitconfig`) sets
`core.autocrlf=true`, `git check-attr` reports `text: unset` for all five paths, and
`git ls-files --eol` shows `i/lf w/lf attr/-text` — so the committed blob is LF and a checkout will
not convert it.

### 8.3 The stale cargo fingerprint, reproduced end to end

The hazard: an old binary answers for new source, so a "green" or a "red" belongs to the wrong bytes.
Reproduced with the file I own, so nothing else is at risk:

```
# 1) the suite is green and built
# 2) a semantic plant is written into tests/push_gate.rs (case 1's assertion flipped to expect success)
$ touch -d '2020-01-01T00:00:00' tests/push_gate.rs
mtime: 2020-01-01 00:00:00
$ cargo test --offline --test push_gate -- --exact an_unmarked_push_is_refused_with_actionable_text
    Finished `test` profile [unoptimized + debuginfo] target(s) in 0.37s      # no recompile
test an_unmarked_push_is_refused_with_actionable_text ... ok                  # FALSE GREEN
# 3) the bytes are unchanged; only the mtime is refreshed
$ touch tests/push_gate.rs
    Compiling hof-rs v0.1.0 (F:\moonbit-hof-rs)
thread '…' panicked at tests\push_gate.rs:326:5:
test result: FAILED. 0 passed; 1 failed
```

Same bytes, only the mtime moved: cargo skipped the rebuild and ran the old binary, which reported
`ok` for a source that cannot pass. That is exactly the mechanism recorded in DR-66 §7-8 (and DR-72's
`sealed` incident), and it is why this batch's gate was taken after the per-file `touch` loop:
`Cargo.toml`/`Cargo.lock` are untouched, and the relevant sources were re-stamped immediately before
the run. Restore was byte-exact (`cmp` identical; hash `f0e06634…` == `HEAD` blob; status/diff empty;
green again).

### 8.4 One measurement of my own that was wrong, and how it was caught

While checking line endings I initially used `grep -c $'\r'` and `awk index($0,"\r")`. In this
harness those produced **false zeros**: they reported `0` for `runs/…`-clean files *and* for a file
whose bytes demonstrably contained a CR (`od -c` showed `\r \n`). The authoritative checks are the
Rust test (`std::fs::read` + `bytes.contains(&b'\r')`, which caught the P6 plant) and raw-byte tools
(`od -c`, `file`, `python … .count(b'\r')`). Every CR claim in this report uses the latter, not the
former.

## 9. Residual risk and unverified items (measured vs inferred)

**Measured**

- `cargo test --offline` exit 0 on the frozen tree: 507/0/7, 54 result lines, `--list` = 514,
  `cargo fmt --check` exit 0, 91 `.rs` files touched one by one.
- The 18 new tests pass; the red-first run (`0 passed; 18 failed`) and the pre-implementation
  case-1 failure (an unaccepted commit reaching the bare remote) are quoted above.
- Six plants, each red on its own test, each restored with `cmp`/`hash-object`/`status`/`diff` proof.
- The gate works with this checkout's absolute `core.hooksPath` **and** with the relative spelling;
  the ledger path is resolved through `git rev-parse --absolute-git-dir`; the gate is armed here and
  refuses today (exit 1).
- The three named false-green traps, the CRLF behaviour, and the stale-fingerprint false green.
- The forbidden zones (five runs baselines, mario project tree, PRD, nested engine, dependencies,
  remote, working tree) as quoted in §7.

**Unverified / not measured**

1. **Cross-platform behaviour**: every measurement is on git 2.45.1.windows.1 with MSYS2 `sh`. The
   hook and its library are POSIX `sh` and avoid `local`, but I cannot claim a Linux/macOS run.
   In particular the CRLF consequence in §8.2 is inference.
2. **A server-side control**: not attempted by design (limit ③); no remote setting was read or
   written. `origin/master` is verified only as this clone knows it — a fetch was not performed, so
   "the remote still points at `2f605b0`" is a statement about the local remote-tracking ref, not a
   fresh read of GitHub. (The offline rule makes that unavoidable; D285 flagged the same limit.)
3. **The `runs/smoke-t10` evidence of DR-73/DR-74** was read only as digests; I did not re-verify the
   rounds' contents.
4. **The older mario digest** (`259/4e494547…` vs today's `178/dee0a36f…`) is unexplained here; it is
   DR-68's R6, still open. What this batch proves is the mtime window and the frozen-artifact
   identity.
5. **Tag pushes**: the range logic handles them through the same `rev-list` path, but no test pushes a
   tag, so tag behaviour is reasoned about, not measured.
6. **`--no-verify` is a hole**: measured (case 5), and deliberately not closed.
7. **Concurrency**: the ledger append is a single `printf >>` without locking. Two simultaneous
   `mark` runs for different commits could interleave; I did not test concurrent writers. The hook
   itself only reads, so concurrent pushes are safe.

**E1 / E3**: not claimed met. This batch changes no product code path; it is an offline
infrastructure and test batch.

## 10. Disclosure

- I did not push anything anywhere. Every push in this batch went to a `tempfile` bare repository;
  the real remote URL was never used as a push target.
- I did not modify `.workspace/mario/**`, `.spec/hof-rs/PRD-mario.md`, `DECISIONS.md` or
  `godot-mcp/**`, and no file under `runs/**` was created, modified or deleted (not even a temporary
  file that was later removed).
- I did not use PowerShell's raw-read/raw-write pair, and no file's line endings were rewritten; the
  one deliberate CR is the P6 plant, which was restored from a byte copy and proved with `cmp`.
- I armed the gate in this repository as a deliberate act (the deliverable is only real once
  `core.hooksPath` points at it). It is reversible with `scripts/install-hooks.sh --uninstall`, and it
  will refuse the DR-75 push until the acceptance is recorded (§4.2).
- The case-6 test was strengthened because plant P5 exposed that the old shape could not detect a
  tip-only gate; that is a test getting stricter, not a test being bent to fit a plant.
- I added no dependency, removed no test, and grew no `ignored`.
- The hand-written prose of this report states the numbers that the machine-readable block below
  repeats; the block was validated with a fence-aware `json.loads` before this file was committed.

## 11. Machine-readable summary

```json
{
  "task": "DR-75",
  "verdict_scope": "the deliverables of the task book are implemented and green offline; this is the implementer's report, not an acceptance",
  "batch_start": "2e0a852",
  "commits": ["6c21b5c", "f3e8504", "64ba17f", "1b52a19"],
  "pushed": false,
  "remote_master": "2f605b039305a244326d429f019d94aee7c4121b",
  "commits_ahead_of_remote": 9,
  "deliverables": {
    "hook": ".githooks/pre-push",
    "library": ".githooks/hoh-acceptance-lib.sh",
    "marker_cli": "scripts/accept-commit.sh",
    "installer": "scripts/install-hooks.sh",
    "docs": ".githooks/README.md",
    "line_ending_pin": ".gitattributes",
    "tests": "tests/push_gate.rs"
  },
  "ledger": {
    "path": "<absolute git dir>/hoh-accepted-commits.txt",
    "record": "accepted <40-hex-commit> <report.md> pass <YYYY-MM-DDTHH:MM:SSZ> [note]",
    "travels_with_clone": false,
    "fail_closed_on": ["missing", "unreadable", "not a regular file", "malformed record line"]
  },
  "gate": {
    "command": "cargo test --offline",
    "exit": 0,
    "passed": 507,
    "failed": 0,
    "ignored": 7,
    "result_lines": 54,
    "list_total": 514,
    "fmt_check_exit": 0,
    "rs_files_touched_individually": 91,
    "baseline_at_batch_start": {"attributes": 496, "ignored_attributes": 7, "names": 496},
    "worktree": {"attributes": 514, "ignored_attributes": 7, "names": 514},
    "test_names_removed": 0,
    "test_names_added": 18
  },
  "push_gate_suite": {"tests": 18, "passed": 18, "failed": 0, "ignored": 0, "red_first_run": "0 passed; 18 failed"},
  "cases": [
    {"id": "1", "name": "unmarked_refused", "pass": true},
    {"id": "2", "name": "marked_allowed", "pass": true},
    {"id": "3", "name": "already_on_remote_not_rechecked", "pass": true},
    {"id": "4", "name": "fail_closed_on_marker_source", "pass": true},
    {"id": "5", "name": "no_verify_recorded_as_known_limit", "pass": true},
    {"id": "6", "name": "one_unmarked_in_range_refuses_all", "pass": true}
  ],
  "plants": [
    {"id": "P1", "file": ".githooks/pre-push", "reddens": "an_unmarked_push_is_refused_with_actionable_text", "restored": {"cmp": true, "hash_equals_head": true, "status_clean": true, "diff_clean": true}},
    {"id": "P2", "file": ".githooks/hoh-acceptance-lib.sh", "reddens": "a_missing_marker_source_refuses_every_push", "restored": {"cmp": true, "hash_equals_head": true, "status_clean": true, "diff_clean": true}},
    {"id": "P3", "file": ".githooks/hoh-acceptance-lib.sh", "reddens": "a_corrupt_marker_source_refuses_every_push + the_gate_and_the_writer_agree_on_ledger_validity", "restored": {"cmp": true, "hash_equals_head": true, "status_clean": true, "diff_clean": true}},
    {"id": "P4", "file": ".githooks/pre-push", "reddens": "commits_already_on_the_remote_are_not_rechecked", "restored": {"cmp": true, "hash_equals_head": true, "status_clean": true, "diff_clean": true}},
    {"id": "P5", "file": ".githooks/pre-push", "reddens": "one_unmarked_commit_in_a_multi_commit_range_refuses_the_whole_push", "restored": {"cmp": true, "hash_equals_head": true, "status_clean": true, "diff_clean": true}, "note": "first attempt hit the non-exercised branch of the range condition and produced no red; retargeted"},
    {"id": "P6", "file": ".githooks/pre-push", "reddens": "the_shell_artifacts_keep_lf_line_endings_and_a_shebang (17/18 others stayed green)", "restored": {"cmp": true, "hash_equals_head": true, "status_clean": true, "diff_clean": true}}
  ],
  "traps": {
    "empty_pathspec_git_diff": "empty output + exit 0; contrast with a matching pathspec showing 133 insertions",
    "cmd_eats_caret": "bash 128 vs cmd 0 on f3e8504^:.githooks/pre-push",
    "outer_repo_untracked_engine": "ls-files godot-mcp=6484 vs godot-mcp/godot=0; .gitignore:33",
    "crlf": "measured: this toolchain tolerates a CRLF shebang (direct exec, sh, and real git push all ran it; the plant reddened only the LF invariant test); the LF pin is a portability guard, and the failure on a non-CR-stripping sh is inference, not measurement",
    "stale_cargo_fingerprint": "reproduced: broken source backdated to 2020 was never recompiled and the old binary reported ok; refreshing only the mtime made the same bytes fail"
  },
  "capability_limits": [
    "The hook is local: pushing from another clone or another machine does not go through this gate at all.",
    "git push --no-verify bypasses it: this is mechanical discipline, not a cryptographic guarantee.",
    "Real enforcement belongs on the server side (GitHub branch protection/rulesets, least-privilege deploy keys); recommended, but no remote setting was changed."
  ],
  "forbidden_zones": {
    "runs_baselines": {
      "runs/smoke-t6": [135, "c144ef3219e21dd322978e41a5531d53dee270619c026585505920f9277a9c03"],
      "runs/smoke-t7": [115, "6e4c1595753c2cdefb16e4d2e5f05242ca202c70c81a93e98ae2b9c92b520fb7"],
      "runs/smoke-t8": [358, "6d11b2c61ec507b5f02525ddc0e7f7adb08763cd2439a4b08788b7fe51bdf5a7"],
      "runs/smoke-t9": [83, "541e2d814e563ba667c95bde49765d05e44cf11aa5ab90b2f44931f30136ca9d"],
      "runs/smoke-t10": [232, "319555896964ce1526f72a33cb239bf389fe29bcde23841764d13c57dfb38b8b"]
    },
    "runs_changed_since_batch_start": 0,
    "mario_project_tree": "diff -r (excluding .godot/.hoh/.git/.import) against runs/smoke-t10/versions/ed98d1b8… identical; 0 files newer than the batch start",
    "mario_raw_digest_today": [178, "dee0a36f357c440d078c652d4d4b8990af1a63b88d282c1e36c04a16d006cc94"],
    "mario_raw_digest_recorded_by_older_batches": [259, "4e494547416b2e87ba025d686afef9447d4f92c027917d1790e6fc9deaeaa84a"],
    "mario_digest_discrepancy": "pre-existing and unexplained; already logged as DR-68 R6; not attributed to this batch",
    "prd_mario_sha256": "4c81c3a9995f0b3afdf01421a0c3be88573cceefc284ce9bafbfda141f0f5c3a",
    "decisions_md_touched_by_this_batch": false,
    "engine_nested_head": "fc63af77c33368c4a1bb839c95d19750554f63a3",
    "engine_nested_porcelain_lines": 0,
    "new_dependencies": 0,
    "working_tree_clean": true,
    "ledger_in_repo": false
  },
  "e1_met": "not claimed (offline infrastructure batch; no product code path changed)",
  "e3_met": "not claimed (offline infrastructure batch; no product code path changed)"
}
```
