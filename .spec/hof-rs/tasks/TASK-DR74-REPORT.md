# TASK-DR74-REPORT — the escape predicate on **unescaped** backslashes, the whole-`PATH` rule, every JSON escape family, two tests that now really test something, and six false statements corrected

- Task book: `.spec/hof-rs/tasks/TASK-DR74.md` (**sole task source**)
- Upstream: `.spec/hof-rs/tasks/TASK-DR72-ACCEPTANCE.md` (verdict `fail`, D1..D9/C2/C3/C6/C20) →
  `.spec/hof-rs/tasks/TASK-DR72-REPORT.md` → `DECISIONS.md` **D279/D280/D281**
- Repo: `F:\moonbit-hof-rs` (outer). **Offline**: no Godot, no external port, no network, no
  model endpoint, no real-machine round
- Commits: `42ecc2a` (implementation/tests/docs/evidence) + the commit that carries this report;
  start HEAD `e01d801`; nothing pushed
- Controlled evidence: `.spec/hof-rs/tasks/TASK-DR72-evidence/samples/env-real.*` (new pair)

## 1. Conclusion + gate

### 1.1 Verdict per item

| # | Item | Verdict | Landing |
|---|---|---|---|
| ① | Double-backslash predicate | **fixed** (`escape_starts_at`: an escape starts only at a backslash preceded by an **even** run) | `src/runtime/secrets.rs` |
| ② | user-name leaks (a) `;`-PATH tail, (b) `\r`-component regression | **fixed** (whole-value rule for `PATH`/`Path`; escape awareness scoped to JSON) + disclosure corrected | `src/runtime/secrets.rs`, `TASK-DR72-REPORT.md` |
| ③ | other escape families | **generalized** (any real escape ends the value; `\\` does not) — not a silent refusal any more | `src/runtime/secrets.rs` |
| ④ | vacuous escape-predicate test | **rewritten**; reverting ① makes it red (plant P1) | `src/runtime/secrets.rs` tests |
| ⑤ | sealed-root wiring untested | **tested against production** `frozen_evidence_roots`; deleting the `traj` push makes it red (plant P5) | `src/runtime/run_loop.rs` tests |
| ⑥ | D3/D4/D5/D7/D8/D9 | **corrected** (numbers recomputed from the tree; D2's false disclosure corrected too) | code comments + shipped docs |

### 1.2 Gate (real output)

```
$ for f in $(git ls-files '*.rs'); do touch "$f"; done      # 90 tracked files, no glob
$ cargo test --offline
...
test result: ok. 0 passed; 0 failed; 7 ignored; 0 measured; 0 filtered out; finished in 0.00s
（53 个 `test result:` 行，全部 0 failed）
$ echo $?                  # CARGO_EXIT=0
$ cargo fmt --check        # FMT_EXIT=0
```

- **Tally (sum over the 53 result lines): `489 passed / 0 failed / 7 ignored`, exit 0.**
  `cargo test --offline -- --list` = **496 = 489 + 7**. Ignored did **not** grow (still the 7
  `#[ignore]` functions of `tests/godot_smoke.rs`), and **0 test functions were removed**.
- **Reproducible arithmetic** (all recomputed here, nothing transcribed):
  - test-function **names** extracted from the test attributes:
    `9e7f8ea` = **465**, `e01d801` = **484** (measured run: 484/0/7), working tree = **489**;
  - test **attributes**: 472 / 491 / **496**; attributes − ignored = passed (7 ignored throughout);
  - `comm -23`/`comm -13` on the name lists: **0 removed, 24 added**
    (DR-72's 19 + DR-74's 5: four in `src/runtime/secrets.rs`, one in `src/runtime/run_loop.rs`);
  - lib: `src` attributes `9e7f8ea` = **132** → `e01d801` = **139** = **+7** (DR-72), → worktree = 144.
- **Baseline source**: `9e7f8ea` is the pre-DR-72 commit the acceptance names (its "correct baseline
  465" is reproduced here as 465 distinct names, not taken on trust). The DR-72 report's
  `475/458/+17` (and D280's transcription) is **wrong** — see §4 (D3).
- **Rebuild discipline**: per-file `touch` loop over `git ls-files '*.rs'` (90 files), **no
  wildcard**; sources edited only with the file tools' literal replacement plus `cargo fmt`; **no**
  PowerShell 5.1 `Get-Content -Raw`/`Set-Content`; every edited file checked `CR=0` (no line-ending
  rewrite). The stale-fingerprint caveat is addressed in §5: I cleared
  `target/debug/.fingerprint/hof-rs-*` before plant P1 and say so there.

## 2. ① Real-encoding adversarial evidence

The frozen (read-only) trajectory proves the shape: `runs/smoke-t10/iter-1/traj/tester.attempt1.json`
has, in raw bytes,
`48 4f 48 5f 47 41 4d 45 5f 52 4f 55 54 45 3d 46 3a 5c 5c 6d …` — i.e.
`HOH_GAME_ROUTE=F:\\moonbit-hof-rs\\runs\\…\\game_endpoint.json` — and the dump line ends with a
**real** escape, `5c 6e` (`\` + `n`, verified by hexdump, read-only). No byte under `runs/**` was
written (see §6).

**Before the fix** (red, real output of the new test):

```
---- runtime::secrets::tests::a_doubled_backslash_path_does_not_inject_a_control_character stdout ----
assertion `left == right` failed: a carriage return was injected into the decoded value:
  "HOH_GAME_ROUTE=<redacted>\runs\\smoke-t10\\iter-1\\node_modules\\pkg\\index.js\n
   HOH_HOH_BIN=<redacted>\release\\hoh.exe\n</output>"
  left: 2
 right: 0
```

⇒ one backslash was deleted at the `\\runs` pair, the surviving `\r` decoded to CR, and the path tail
(`runs\smoke-t10\…\node_modules\…`) stayed visible while the JSON gate could not refuse it (the
result still parsed).

**After the fix**, the same test asserts, on the same bytes: `refused == None`; the decoded value
carries **no CR/LF beyond the ones it started with** (`\r` count 0, `\n` count unchanged); the value
is exactly `HOH_GAME_ROUTE=<redacted>` and none of `runs`, `smoke-t10`, `node_modules`,
`moonbit-hof-rs\runs` survives; `</output>` is untouched; and
`bytes_changed_outside_spans(&report) == Some(0)` (the output is exactly the input with the reported
span replaced). The acceptance's exact `p14` shape (value is the last thing in the string) is also
asserted: the **unescaped closing quote** bounds it ⇒ decoded `HOH_ARTIFACT_DIR=<redacted>`, no
refusal, no injected control character.

A committed artifact carries the same proof in the controlled-evidence area:
`TASK-DR72-evidence/samples/env-real.*` (spans `HOH_ARTIFACT_DIR [51..124)` and `PATH [126..187)`).

## 3. ②③④⑤ landing and red→green

- **②(a) `;`-separated `PATH`.** Decision: **the whole value of `PATH`/`Path` is one sensitive
  value** (`WHOLE_VALUE_VARS`), so every `;`-separated element is inside one span. Reason: `PATH` is
  a single environment value whose disclosure is the whole list; segment-wise redaction would emit
  one span per element for the same assignment and still leave the element count readable, while the
  other assignments already follow "the variable's value is the sensitive thing". Red (before) →
  green (after):
  `the user name must not survive anywhere in the value: PATH=<redacted>;C:\Program Files\nodejs;C:\Users\wyl\AppData\Roaming\npm`.
- **②(b) `\r`-component regression.** Escape awareness is now **limited to JSON**
  (`looks_like_json`); in a plain-text dump a backslash is just a byte, so the value runs to the
  physical line ending and the user name goes, exactly as the pre-DR-72 scanner did. Red → green:
  `the whole plain-text value must go, as the pre-DR-72 scanner did: HOH_ARTIFACT_DIR=<redacted>\repo\Users\wyl\runs\run-1`.
- **Disclosure corrected.** `TASK-DR72-REPORT.md`'s F-DR72-2 ("用户名/凭据值不残留") is marked false
  in a DR-74 correction block at the top of that report; D280's rewritten decision cannot be
  corrected here because `DECISIONS.md` is out of this batch's write scope (the dispatcher must
  record the supersession — D281 already did for the verdict).
- **③ Escape families.** `\t`, `\"`, `\uXXXX` (and every other real escape) now **end** the value
  because an unescaped backslash whose next byte is not a backslash is a terminator; `\\` (a path
  separator) is not. Red (before, verbatim): `the \t family must be handled, not refused: Some("the
  secret-assignment splice was refused because the result is no longer valid JSON (control character
  (\u0000-\u001F) found while parsing a string at line 2 column 0); the original text is left
  byte-for-byte unchanged")`. The DR-69 quoted shape (`NAME=\"$(cat …)\"` inside JSON) is handled as
  a quoted value.
  **Verbatim statement of the consequence that existed before this fix**: for a perfectly legitimate
  JSON file whose assignment was followed by `\t`, `\uXXXX` or `\"`, the assignment splice was
  **refused**, the DR-69 assignment rule was therefore **dropped**, the file could still be written
  by the (stronger) known-value rule, and `HOH_MODEL_API_KEY=` (or any harness assignment) could
  remain in the evidence with only a `warnings.log` line. It is now generalized, so that
  degradation no longer happens for these families.
- **④ The vacuous test.** `a_windows_path_value_is_not_mistaken_for_an_escape` was decided by a `;`
  (`span = PATH [9..37)`, terminator byte 59 — acceptance p15). It now uses a fixture whose value
  crosses a `;` and ends at a **real escape**, asserts the span ends on `\` + `n` (so the predicate
  was consulted), and asserts the decoded value is exactly `PATH=<redacted>\nnext`. Non-vacuity:
  reverting the predicate (plant P1) makes it **FAILED** again (`§5`). Red (before): `the whole path
  value must be gone and only the field after the escape must survive: left: "PATH=<redacted>\node_modules\\.bin;C:\\stand-in\\bin\\runs\\run-1\nnext"`.
- **⑤ Production sealed roots.** New unit test `the_production_sealed_areas_cover_every_frozen_root`
  drives `run_loop::frozen_evidence_roots` itself: `versions/**`, `quarantine/**`,
  `iter-{1,2}/candidate/**`, `iter-{1,2}/traj/**` must be sealed; `iter-*/planner-view/**`,
  `candidate-evil`, `versions-evil` and an out-of-range iteration must not. Deleting
  `roots.push(iter_dir.join("traj"))` (plant P5) makes it **FAILED**:
  `` `iter-1/traj/tester.attempt1.json` is frozen evidence and must be sealed by the production list ``.
  This closes acceptance C6 (DR-72 plant C was green everywhere).

## 4. ⑥ Corrections and consistency proofs

- **D3 gate arithmetic.** `TASK-DR72-REPORT.md` §1.1 said `475 passed / baseline 458 / +17 (lib +5)`.
  Recomputed from the tree: **484/0/7 at `e01d801`**, `--list` 491, **baseline 465**, net **+19**,
  **lib +7** (132→139). The wrong figure is marked corrected in that report; D280's copy cannot be
  edited (out of scope) and is superseded here.
- **D4 two documents vs code.** `record.rs::iteration_directories`'s comment now says
  `iter-*/{candidate,traj}` and states that `planner-view` is deliberately **not** sealed;
  `REDACTION-POLICY.md` §2 now has a separate `iter-*/planner-view/**` row ("in-place rewrite") and
  keeps the superseded row as a quoted block marked superseded. All three (code, policy, README) now
  say the same thing, and the code is the reference.
- **D5 false rationale.** The code comment and `REDACTION-POLICY.md` §3 no longer claim that deleting
  a backslash created a control character. The superseded sentence is preserved verbatim in the
  policy under "Rationale corrected by DR-74 ⑥(D5)", followed by the true reason: **content
  fidelity**, and the historical control character came from a **physical newline left inside an
  unterminated string** (the scan ran past the escape). The probe spliced the same input with the
  span ending at the backslash, at backslash+1 and at backslash+2: all three parsed and none left a
  control character in the string.
- **D7 sample-test claim.** `tests/frozen_evidence.rs` now states the test **does** run in every gate
  (not `#[ignore]`d — the ignored count must not grow), takes part in the verdict, and writes to
  `target/dr72-redaction-sample/`, an untracked build directory, which is acceptable for that
  purpose.
- **D8 e1_increment claim.** The doc and the inline comment now say the expected `added`/`modified`
  lists are **hardcoded literals of the fixture**; the independent evidence is the frozen snapshot's
  bytes and the existence of both `A_0`/`A_t` snapshots.
- **D9 parameter-name assertion.** Both assertions that named the literal `` `path` `` now iterate
  over the list derived from the captured `tools/list` fixture
  (`hof_rs::tools::index::accepted_parameters(TOOL)`), so a hardcoded parameter list cannot pass.
- **Sample classification and regeneration** (dispatcher caution, answered explicitly):
  `samples/env.original.txt` is an **authored synthetic input**, not frozen machine evidence; its
  stand-in values carry no real environment value and no user name. DR-74 nevertheless **does not
  edit it**: an intermediate edit was made and then **reverted before any commit** (see §8 for the
  byte proof), and the corrected real encoding is contributed as the **new pair**
  `samples/env-real.original.txt` / `.redacted.txt` / `.spans.txt`. Every `*.redacted.txt` and
  `*.spans.txt` is regenerated by the documented command
  `cargo test --offline --test frozen_evidence -- --exact the_redacted_sample_is_regenerable_from_the_production_pass`,
  which rewrites them into `target/dr72-redaction-sample/` and **asserts the committed bytes equal
  that output**; the committed bytes were copied from exactly that directory (`cp`, byte-for-byte).
  `env.redacted.txt` now carries one span (`HOH_ARTIFACT_DIR [53..172)`) because the DR-69 rule ends
  an assignment at `;` for this input; the real-encoding pair is the one with two spans and no
  carriage return.

## 5. Non-vacuity: five production-only plants, each with its own red

Rule: each plant touched **production code only** (`src/**`, never `tests/**`), and was restored
byte-exactly (`cmp` against the out-of-repo snapshot `/f/dr74-work`, created after the fix and before
the first plant). Before plant P1 I cleared `target/debug/.fingerprint/hof-rs-*`; the other runs
followed a fresh edit (mtime bumped) and each red matched the planted change.

| # | Plant (production) | Test that went red | Red output (verbatim excerpt) | Restore |
|---|---|---|---|---|
| **P1** | `secrets.rs::is_value_terminator` escape arm → the DR-72 predicate (`\` + `n`/`r` regardless of escaping) | `a_doubled_backslash_path_does_not_inject_a_control_character`; also `a_windows_path_value_is_not_mistaken_for_an_escape`, `other_json_escape_families_…` | `a carriage return was injected into the decoded value: "HOH_GAME_ROUTE=<redacted>\runs\\smoke-t10\\…"`, `left: 2 right: 0` | `cmp` equal; `diff -r` clean |
| **P2** | `splice_assignments` whole-value argument → `false` | `a_user_name_in_a_semicolon_separated_path_tail_is_redacted` (and ④) | `the user name must not survive anywhere in the value: PATH=<redacted>;C:\Program Files\nodejs;C:\Users\wyl\AppData\Roaming\npm` | `cmp` equal |
| **P3** | `splice_assignments` `json` → forced `true` (escape awareness on plain text) | `a_path_with_a_backslash_r_component_still_redacts_the_user_name` (+2 older ones) | `the whole plain-text value must go, as the pre-DR-72 scanner did: HOH_ARTIFACT_DIR=<redacted>\repo\Users\wyl\runs\run-1` | `cmp` equal |
| **P4** | escape arm restricted back to `n`/`r` **but keeping the even-count rule** | `other_json_escape_families_do_not_drop_the_assignment_redaction` | `the \t family must not eat what followed the escape: HOH_MODEL_API_KEY=<redacted>` | `cmp` equal |
| **P5** | **delete `roots.push(iter_dir.join("traj"))`** from `frozen_evidence_roots` | `the_production_sealed_areas_cover_every_frozen_root` | `` `iter-1/traj/tester.attempt1.json` is frozen evidence and must be sealed by the production list `` | `cmp` equal |

After P5: `diff -r src /f/dr74-work/src` → **identical**, `diff -r tests /f/dr74-work/tests` →
**identical**, `grep -rn PLANT src tests` → **0**. After the single commit: `git status --porcelain
-uall` = **0 lines**, `git diff --stat` empty, `git hash-object <path>` == `HEAD:<path>` for every
edited source, and `cmp` of each against `/f/dr74-work` (plus `cmp` of `env.original.txt` against the
pre-DR-74 backup) is equal. ④ is proved non-vacuous by P1 and ⑤ by P5, as the task requires.

## 6. Forbidden-zone self-check (real output)

- **Five `runs/**` baselines unchanged** (read-only `scripts/dr72-digest.ps1`, PowerShell 5.1,
  convention: repo-root-relative lowercase POSIX path + byte length + lowercase SHA256, tab-joined,
  newline-separated, no trailing newline, culture `Sort-Object`, whole text UTF-8 → SHA256):

  ```
  runs/smoke-t6  135  c144ef3219e21dd322978e41a5531d53dee270619c026585505920f9277a9c03  newest 2026-09-29 02:32:01
  runs/smoke-t7  115  6e4c1595753c2cdefb16e4d2e5f05242ca202c70c81a93e98ae2b9c92b520fb7  newest 2026-09-29 14:41:14
  runs/smoke-t8  358  6d11b2c61ec507b5f02525ddc0e7f7adb08763cd2439a4b08788b7fe51bdf5a7  newest 2026-09-30 07:58:28
  runs/smoke-t9   83  541e2d814e563ba667c95bde49765d05e44cf11aa5ab90b2f44931f30136ca9d  newest 2026-09-30 11:27:29
  runs/smoke-t10 232  319555896964ce1526f72a33cb239bf389fe29bcde23841764d13c57dfb38b8b  newest 2026-09-30 18:23:08
  ```

  All five hit the recorded values (including the self-validating `smoke-t6 = c144ef32…7a9c03`);
  `find runs -newermt "2026-10-01" -type f` → **empty**; the corrupted `tester.attempt1.json` was
  only **read** (slices/hexdumps). No temp file was created under `runs/**`.
- **`.workspace/mario`**: content (17 files, excluding the runtime-only `.godot`/`.hoh`) is
  byte-identical to `runs/smoke-t10/versions/ed98d1b8…` (`diff -r -x .godot -x .hoh` → equal), and
  no file under it is newer than 2026-10-01.
- **PRD-mario.md**: `sha256 = 4c81c3a9995f0b3afdf01421a0c3be88573cceefc284ce9bafbfda141f0f5c3a`
  (unchanged; `git diff HEAD -- .spec/hof-rs/PRD-mario.md` empty).
- **`DECISIONS.md`**: `git diff HEAD --stat -- DECISIONS.md` **empty** (not edited by me).
- **Nested engine**: `git -C godot-mcp/godot rev-parse HEAD = fc63af77c33368c4a1bb839c95d19750554f63a3`,
  `status --porcelain -uall` = 0 lines; outer `git ls-files godot-mcp` = **6484** vs
  `git ls-files godot-mcp/godot` = **0** (the pathspec really matches, empty result is a true zero).
- **No new dependency**: `git diff HEAD --stat -- Cargo.toml Cargo.lock` empty.
- **Not pushed**: `HEAD = 42ecc2a…` (commit A) vs `origin/master = 9e7f8ea…`; nothing staged after
  the commit.
- **No temp files in the repo**: `git status --porcelain -uall` contained only the 13 intended
  entries before commit A and 0 after it; no `*.tmp*`/debug relics; the only untracked directory
  used is `target/` (gitignored).
- **Three false-green traps measured**:
  1. `git diff --stat -- definitely/not/a/real/path` → **empty, exit 0**, while the same command on
     `src/runtime/secrets.rs` prints a diff ⇒ an empty diff over a wrong path proves nothing;
  2. cmd: `git rev-parse 9e7f8ea^` printed **9e7f8ea itself** (the caret never reached git; bash
     resolves the parent `5603f32`), and `git rev-parse definitelynotarev & echo AFTER_FATAL_EXIT=%errorlevel%`
     printed the fatal **and** `AFTER_FATAL_EXIT=0` (parse-time expansion);
  3. `git check-ignore -v runs/ .workspace/ godot-mcp/godot/` → `.gitignore:12/11/33` ⇒ those paths
     are ignored and an empty diff over them proves nothing.
- **Stale fingerprint**: cleared `target/debug/.fingerprint/hof-rs-*` before plant P1; later reds
  followed a fresh edit and each matched its planted change, and every gate run in §1 was taken
  after a per-file `touch`.
- **No engine/port/network/model**: the only processes run were `cargo`, `git`, `powershell.exe`
  (read-only digest), `cmp`/`diff`/`find`/`sed`. No loopback server was needed.

## 7. Residual risks and unverified items (measured vs inferred)

Measured:

- ① is fixed for the real encoding (unit test + committed `env-real.*` artifact); the closing-quote
  shape is bounded rather than refused.
- ②(a)/(b) are fixed and pinned by tests that die under plants P2/P3.
- ③'s families are handled and pinned by a test that dies under P4.
- ④/⑤ are non-vacuous (P1/P5).
- Gate and arithmetic are as reported in §1; plants restored byte-exactly.

Inferred / unverified (not to be read as measured):

- **The `;`-tail bound is not removed.** For a non-`PATH` assignment, `;` still terminates the value
  (DR-69 requires it so `set OPENAI_API_KEY=abc123; echo hi` keeps `echo hi`). Therefore a shape such
  as `HOH_MODEL_API_KEY=<redacted>;C:\Users\wyl\…` — which occurs in the already-committed
  `TASK-SMOKE-T10-evidence/analysis/redaction_defect.txt` — can still leave that tail. This is a
  **bound of the fix, not a claim of coverage**; closing it would need a per-line policy for
  command-shaped text, which DR-74 does not decide.
- `looks_like_json` decides the whole document by its first non-space byte; a JSON document with a
  non-JSON preamble would lose escape awareness (not exercised by any real artifact I have).
- The DR-72 residual risk of a `.redacted.<ext>` copy inside `versions/**` being rolled back into the
  workspace on a later iteration is carried over unchanged (reasoned from
  `snapshot.rs`/`run_loop.rs`, not exercised; out of DR-74's scope).
- Real-machine behaviour of every kind (no Godot/network/model endpoint). No real-machine
  probability is stated here, because any such number would need a premise this offline batch cannot
  supply.
- The implementer transcripts of the DR-72 batch are not treated as evidence; only reproduced facts.

## 8. Honest disclosure

- **The `env.original.txt` edit is disclosed and reverted.** While working I rewrote
  `samples/env.original.txt` to the real encoding, before the dispatcher's caution arrived. That edit
  was **never committed**: I restored the file byte-exactly from the pre-DR-74 backup
  (`cmp` equal; `git hash-object` = `git rev-parse HEAD:.spec/.../env.original.txt` = `4e37d349…`),
  and the corrected form went into the **new** `env-real.*` files instead. `git show 42ecc2a
  --name-only` does not contain `env.original.txt`. The report-writer's rule "evidence is not
  rewritten in place" was upheld in the final tree.
- Docs under `TASK-DR72-evidence/` were corrected **without silently replacing** the superseded
  wording: the old policy row and the old D5 sentence are preserved as quoted, marked-superseded
  blocks, and the DR-72 report keeps its original text with a correction block at the top.
- **What I changed**: `src/runtime/secrets.rs`, `src/runtime/run_loop.rs`, `src/runtime/record.rs`,
  `tests/frozen_evidence.rs`, `tests/e1_increment.rs`, `tests/tool_parameter_contract.rs`,
  `TASK-DR72-REPORT.md`, `TASK-DR72-evidence/{README.md,REDACTION-POLICY.md,samples/*}`; no
  `DECISIONS.md`, no `.workspace/mario/**`, no `PRD-mario.md`, no `godot-mcp/**`, no dependency, no
  push, no byte under `runs/**`.
- **I do not claim E1 or E3 are met**, and I give no real-machine probability (no premise available
  offline).
- The report's machine-readable block is validated fence-aware with `json.loads` before commit, and
  this file is **written once**: no edit after the commit that carries it.

---

## Machine-readable conclusion block

```json
{
  "task": "TASK-DR74",
  "head_at_start": "e01d80119b3d1867c77030b66a4111cbc02eed2c",
  "commit_implementation": "42ecc2a2ce152031a94878642980fc8a89294b07",
  "commit_report": "the commit that carries this file (recorded in the completion message)",
  "gate": {
    "cargo_test_offline_exit": 0,
    "passed": 489,
    "failed": 0,
    "ignored": 7,
    "list_total": 496,
    "ignored_grew": false,
    "test_functions_removed": 0,
    "test_functions_added": 24,
    "cargo_fmt_check_exit": 0,
    "forced_rebuild": "per-file touch over git ls-files '*.rs' (90 files, no glob)",
    "baseline_9e7f8ea": {"test_function_names": 465, "attributes": 472, "ignored": 7},
    "start_head_e01d801": {"passed": 484, "ignored": 7},
    "dr72_net": {"tests": 19, "lib": 7},
    "fingerprint_cleared_before_plant_p1": true
  },
  "items": {
    "1_double_backslash_predicate": {"done": true, "rule": "an escape starts only at a backslash preceded by an even run", "evidence": "secrets.rs::a_doubled_backslash_path_does_not_inject_a_control_character + samples/env-real.*"},
    "2_user_name_leaks": {"done": true, "paths": "whole-value PATH/Path; escape awareness scoped to JSON; DR-72 false disclosure corrected", "bound": "non-PATH assignment still ends at ';' (DR-69 rule)"},
    "3_escape_families": {"done": true, "rule": "any real escape ends the value; '\\\\' does not", "old_consequence_stated": true},
    "4_vacuous_test": {"done": true, "non_vacuity": "plant P1 reddens it"},
    "5_sealed_root_wiring": {"done": true, "non_vacuity": "plant P5 (traj push removed) reddens it"},
    "6_doc_and_arithmetic": {"done": true, "items": ["D2", "D3", "D4", "D5", "D7", "D8", "D9"]}
  },
  "plants": [
    {"id": "P1", "where": "secrets.rs::is_value_terminator escape arm", "red": ["a_doubled_backslash_path_does_not_inject_a_control_character", "a_windows_path_value_is_not_mistaken_for_an_escape"], "restore": "cmp_equal"},
    {"id": "P2", "where": "splice_assignments whole_value -> false", "red": ["a_user_name_in_a_semicolon_separated_path_tail_is_redacted"], "restore": "cmp_equal"},
    {"id": "P3", "where": "splice_assignments json -> true", "red": ["a_path_with_a_backslash_r_component_still_redacts_the_user_name"], "restore": "cmp_equal"},
    {"id": "P4", "where": "escape arm restricted to n/r with even-count kept", "red": ["other_json_escape_families_do_not_drop_the_assignment_redaction"], "restore": "cmp_equal"},
    {"id": "P5", "where": "run_loop.rs frozen_evidence_roots: traj push removed", "red": ["the_production_sealed_areas_cover_every_frozen_root"], "restore": "cmp_equal"}
  ],
  "plant_restores": {"cmp_vs_out_of_repo_snapshot": "equal", "diff_r_src": "identical", "diff_r_tests": "identical", "plant_markers_left": 0, "git_status_porcelain": "0 lines", "git_diff_stat": "empty", "hash_object_equals_head": true},
  "env_original_edit": {"made": true, "reverted_before_commit": true, "cmp_against_pre_dr74_backup": "equal", "blob": "4e37d3493f791ae26ab7a3421a09afb6061a2c7a", "in_commit_42ecc2a": false},
  "runs_baseline": {
    "smoke-t6": [135, "c144ef3219e21dd322978e41a5531d53dee270619c026585505920f9277a9c03"],
    "smoke-t7": [115, "6e4c1595753c2cdefb16e4d2e5f05242ca202c70c81a93e98ae2b9c92b520fb7"],
    "smoke-t8": [358, "6d11b2c61ec507b5f02525ddc0e7f7adb08763cd2439a4b08788b7fe51bdf5a7"],
    "smoke-t9": [83, "541e2d814e563ba667c95bde49765d05e44cf11aa5ab90b2f44931f30136ca9d"],
    "smoke-t10": [232, "319555896964ce1526f72a33cb239bf389fe29bcde23841764d13c57dfb38b8b"]
  },
  "forbidden": {"prd_sha256": "4c81c3a9995f0b3afdf01421a0c3be88573cceefc284ce9bafbfda141f0f5c3a", "nested_engine_head": "fc63af77c33368c4a1bb839c95d19750554f63a3", "nested_engine_porcelain_lines": 0, "new_dependencies": false, "pushed": false, "runs_writes": 0, "decisions_md_edited": false, "mario_unchanged": true},
  "not_claimed": ["E1 met", "E3 met", "real-machine probability"],
  "unverified": ["';'-tail after a non-PATH assignment (bounded, not fixed)", "JSON detection by first non-space byte", "versions/ .redacted copy rolled back on a later iteration", "all real-machine behaviour"]
}
```
