# TASK-DR72-ACCEPTANCE — independent acceptance of the DR-72 redaction batch

> Judge: a fresh acceptance subagent with **no upstream context**. Nothing in
> `TASK-DR72-REPORT.md` was treated as evidence; every number and every counterexample
> below was produced by me, with my own commands, my own out-of-repo probe crate and
> my own production-code plants.
> Object: outer repo `F:\moonbit-hof-rs`. **Code/test content audited at `04abf5f`**
> (`git diff 04abf5f..HEAD -- src tests Cargo.toml Cargo.lock` is empty); HEAD advanced
> while I audited (`adc3a19` → `53e0c0f`, docs-only: `d731d54` = D280, `53e0c0f` =
> `TASK-DR73.md`, both by the dispatcher). Working tree clean at the end
> (`git status --porcelain -uall` = 0 lines). `origin/master = 9e7f8ea`; nothing pushed
> or staged.
> Offline: no Godot, no external port, no network, no model endpoint, no real-machine
> round. I wrote **zero bytes under `runs/**`** (my own read-only digests of all five
> baselines reproduce the historical values; no file under `runs/` is newer than
> 2026-09-30 18:23:08), nothing under `.workspace/mario/**`, `.spec/hof-rs/PRD-mario.md`,
> `DECISIONS.md` or `godot-mcp/**`. All probe material, backups and scripts live outside
> the repo in `C:\Users\wyl\AppData\Local\Temp\dr72acc\`.
> **Verdict: `fail`** — items ②③④⑤ and the gates hold, but the headline item ① is
> **not correctly fixed**: the escape predicate misfires on JSON **escaped backslashes**
> (the shape the real dump actually uses), the shipped cross-check for exactly that is
> vacuous, and the residual is disclosed with a **false claim** ("no user name survives").
> I fixed nothing I found.

## 0. Structured verdict (machine-readable)

```json
{
  "verdict": "fail",
  "object": {
    "repo": "F:/moonbit-hof-rs",
    "code_frozen_at": "04abf5f",
    "audited_head": "53e0c0f8870f54aac8c3f62ec46cf6acefd12912",
    "worktree_at_end": "clean (git status --porcelain -uall = 0 lines)",
    "origin_master": "9e7f8ea27a4fb928acb34b0a117246c81d1f8def",
    "batch_commits": ["04abf5f", "f4b4463", "adc3a19"]
  },
  "criteria": [
    {"id": "C1-adversarial-escaped-newline", "pass": true, "evidence": "My probe p1 (out-of-repo crate, production `redact_secret_assignments_traced`) on an assignment inside a JSON string followed by the two characters backslash+n: refused=None, serde_json parses the output, `bytes_changed_outside_spans == Some(0)`, the spans reassemble the output, the closing quote + comma + `\"extra\":{\"returncode\":0}` survive, and the span end points at the backslash (not consumed)."},
    {"id": "C2-escape-predicate-correctness", "pass": false, "evidence": "My probe p14: a valid JSON document whose value is a JSON-escaped Windows path `F:\\\\moonbit-hof-rs\\\\runs\\\\smoke-t10\\\\iter-1` (the exact encoding of the real `runs/smoke-t10/iter-1/traj/*.json` dumps, which I read byte-wise). The scan stops at the SECOND backslash of the `\\\\r` pair, deletes the first, and the surviving `\\r` becomes a real JSON escape: decoded value = `HOH_ARTIFACT_DIR=<redacted>` + CR + `uns\\smoke-t10\\iter-1`. So (i) the path tail survives, (ii) a raw control character is injected into a decoded string, (iii) the (c) gate does not refuse because the result is still parseable JSON. The shipped test that claims to cover this is vacuous (C3/p15)."},
    {"id": "C3-shipped-doubled-backslash-test-not-vacuous", "pass": false, "evidence": "My probe p15 runs the exact fixture of `secrets.rs::a_windows_path_value_is_not_mistaken_for_an_escape` through production: span = `PATH [9..37)`, terminator byte = 59 (`;`). The value ends at the semicolon before any escape is consulted, so the test proves nothing about the escape predicate."},
    {"id": "C4-refusal-path", "pass": true, "evidence": "My probe p8: an already-invalid JSON file is left byte-identical, `report.refusals` names it, `rewritten` is empty; with a known credential value (p8b/p12) the file is written by the value rule while the refusal is still reported, so the refusal is neither silent nor a total no-op. `run_loop::redaction_sweep` (src/runtime/run_loop.rs:428-437) pushes every refusal into `warnings`. Plant A reproduces the implementer's red output verbatim (`the splice must be accepted for this shape: Some(\"… no longer valid JSON (control character …)\")`), confirming the (a)-removed → refused → assignment-redaction-lost reasoning."},
    {"id": "C5-sealed-copy-mechanism", "pass": true, "evidence": "My probe p6: a sealed `versions/env.json` is byte-identical after the pass, its `<name>.redacted.<ext>` copy exists and is clean, the copy is in `report.copies` and not in `report.rewritten`, the non-sealed `live.txt` is rewritten in place, `hits()==2`. p7: `SealedAreas::contains` is component-wise (`candidate-evil` is not sealed). An in-place edit is caught by the byte comparison that p6 asserts (and by the shipped test at tests/frozen_evidence.rs:200-204)."},
    {"id": "C6-production-sealed-root-wiring-tested", "pass": false, "evidence": "My plant C removed `roots.push(iter_dir.join(\"traj\"))` from `run_loop::frozen_evidence_roots` (production, src/runtime/run_loop.rs:405): lib 139 + frozen_evidence 6 + secret_isolation 3 + secret_hygiene 3 + record_symmetry 5 + evidence_isolation 2 all PASS. The only test that constructs `SealedAreas` is tests/frozen_evidence.rs, and it builds its own list. A future edit that unseals trajectories (the headline property of item ②) is invisible to the suite."},
    {"id": "C7-planner-view-exception", "pass": true, "evidence": "`frozen_evidence_roots` deliberately omits `iter-*/planner-view` and says why (run_loop.rs:394-399); the exception is load-bearing and pinned end-to-end by `tests/secret_isolation.rs::a_leaked_secret_is_erased_and_counted` (a planner writes `env-dump.txt` into planner-view through the real run loop; the file must contain `<redacted>` after the round — sealing planner-view reddens it). I grepped `src/**` for readers of planner-view: only path construction/cwd/env, no parser. So the \\\"nothing parses it\\\" premise holds today."},
    {"id": "C8-evidence-diff", "pass": true, "evidence": "Production: `iteration_start_manifest` captured after rollback and before the Developer (run_loop.rs:1077), the success path computes `iteration_evidence_diff` from it to the frozen `versions/<version_id>` (run_loop.rs:1794-1804). Frozen artifact check: `runs/smoke-t10/iter-1/result.json` really has `{\"added\":[],\"modified\":[],\"removed\":[]}` while `version_id=ed98d1b8…` ≠ A0 `1f3d20ed…` (F-T10-3 confirmed real). The shipped test asserts the exact lists on a round that returns Ok, and its companion pins the empty case, so an always-empty or always-non-empty field cannot pass."},
    {"id": "C9-parameter-contract", "pass": true, "evidence": "From the captured fixture (not from the report): `tests/fixtures/mcp/tools_list.json` has 177 tools; `editor_get_node_properties.inputSchema` = `{properties:{path,properties}, required:[path]}`, while `editor_get_collision_info` really declares `node_path` — the sibling spelling difference is genuine, and the fixture is untouched by this batch (last touched by DR-42). `accepted_parameters` reads that same `include_str!` snapshot (src/tools/index.rs:18,47-57); `bridge.rs:276-281` installs/clears the hint around the CLI call only; `mod.rs:413` augments on the caller thread; `is_unknown_parameter_error` requires code -32602 AND the text `unknown parameter` (so DR-54 `ACTION_NOT_BOUND` is untouched) and `McpError::new(inner.code, …)` preserves the code; `exit_code_of` still yields 5 for a non-HofError."},
    {"id": "C10-one-readiness-predicate", "pass": true, "evidence": "`src/adapter/godot.rs:511-525` (battery `ready()`), `:3914-3924` (round `start_round_game`) both call `wait_for_ready_matching(…, scene_tree_readiness)`, and `scene_tree_readiness` = `describe_scene_tree_shape(unwrap_mcp_payload(payload))` (:2700-2704). The permissive `wait_for_game_ready` now only serves tests. The two shipped tests that fed a payload the battery rejects (nodes without `type`) were changed to a real scene tree — visible in `git diff 9e7f8ea..HEAD -- tests/round_game_start.rs`."},
    {"id": "C11-in-poll-discriminator-catches-reversion", "pass": true, "evidence": "My plant B re-added `let _ = tools.publish_game_endpoint().await;` immediately after `install_game_endpoint` (the DR-70 publish-at-install shape) in production: `tests/round_game_start.rs::the_round_readiness_poll_never_exposes_the_route_while_it_runs` went RED (7 sightings all `existed=true`), while the other 5 round tests stayed green — exactly the DR-71 blind spot, now genuinely covered. This is stronger than the report's own §6.3.3, which admits it never reverted the historical code."},
    {"id": "C12-race-test-genuine", "pass": true, "evidence": "tests/game_route_across_processes.rs:483-619: one writer publishing every round (with a `withdraw` every 3rd), 4 readers, 400 ms, 4 KiB payload; a reader records a miss only on `None`, a torn record only when `serde_json` fails or the pid is not this process; asserts reads>0, hits>0, `torn.is_empty()`, and that after `withdraw_game_route` both `use_game_route_file` and `load_game_route` return None (explicit refusal, never an invented port). I ran it 3/3 green; it also passed the full gate."},
    {"id": "C13-gate", "pass": true, "evidence": "My own clean run after a per-file `touch` over `git ls-files '*.rs'` (90 files, no wildcard): `cargo test --offline --no-fail-fast` → CARGO_EXIT=0, and my own sum over the 53 `test result:` lines (52 test binaries + 1 doctest line) = **484 passed / 0 failed / 7 ignored**. `cargo fmt --check` → exit 0. This is ABOVE the required 475; see D3 for why the report says 475."},
    {"id": "C14-ignored-and-removals", "pass": true, "evidence": "Ignored = 7, exactly the 7 `#[ignore]` functions in tests/godot_smoke.rs (8 `#[ignore` occurrences in tests+src, one of them in a doc comment). Test-function names: baseline 9e7f8ea → HEAD = **0 removed**, 19 added (per-file: secrets.rs +7, e1_increment +2, frozen_evidence +3, game_route +1, round_game_start +2, tool_parameter_contract +4). Total `cargo test -- --list` = 491 = 484 + 7."},
    {"id": "C15-plant-restore-proof", "pass": true, "evidence": "Their out-of-repo backup still exists: `diff -r src /f/dr72-backup/src` and `diff -r tests /f/dr72-backup/tests` both return 0 lines; `grep -rl PLANT src tests` finds nothing; every source file's `git hash-object` equals its HEAD blob. My own three plants (A: secrets.rs escape arm; B: publish-at-install; C: unsealed traj) were each restored with `cp -p`, verified with `cmp` against my own out-of-repo backup, and the bytes/hashes match HEAD exactly."},
    {"id": "C16-stale-fingerprint-false-red", "pass": true, "evidence": "Reproduced the trap deliberately: after plant A I restored with `cp -p` (pre-plant mtime, older than the built artifact) and re-ran without touching: cargo reported the planted binary's FAILED even though the source was byte-correct. `touch src/runtime/secrets.rs` then `cargo test` → ok. So the implementer's disclosure is accurate and load-bearing; my own gate was taken after a forced per-file touch, so my numbers are from fresh binaries."},
    {"id": "C17-runs-baselines", "pass": true, "evidence": "My own PowerShell 5.1 script (repo-root-relative lowercased POSIX path + byte length + lowercased SHA256, tab-joined, newline-joined, no trailing newline, `Sort-Object` order, whole string UTF-8-hashed) reproduces all five: t6 135 = c144ef32…7a9c03 (self-validating anchor), t7 115 = 6e4c1595…20fb7, t8 358 = 6d11b2c6…bdf5a7, t9 83 = 541e2d81…36ca9d, t10 232 = 31955589…b38b8b (newest 2026-09-30 18:23:08). No file under `runs/` is newer than 18:23:08 (session time 22:24)."},
    {"id": "C18-forbidden-zones", "pass": true, "evidence": "PRD sha256 = 4c81c3a9…f5c3a; `git diff 9e7f8ea..HEAD -- Cargo.toml Cargo.lock` empty (no new dependency); origin/master unchanged at 9e7f8ea; nested `git -C godot-mcp/godot rev-parse HEAD` = fc63af77…f63a3 with 0 porcelain lines, outer `ls-files godot-mcp` = 6484 vs `ls-files godot-mcp/godot` = 0 (pathspec really matches); live `.workspace/mario` (17 files, runtime exclusion set) is byte-identical to `runs/smoke-t10/versions/ed98d1b8…` (the round's A1), so this batch did not touch the project; `DECISIONS.md` was changed only by the dispatcher's `d731d54` (D280), not by the three batch commits."},
    {"id": "C19-false-green-traps", "pass": true, "evidence": "(1) `git diff --stat -- definitely/not/a/real/path` → empty, exit 0 (control: the same command on `src/runtime/secrets.rs` prints the diff). (2) cmd: `git rev-parse 9e7f8ea^` printed 9e7f8ea itself (the caret never reached git; bash resolves its parent 5603f32), and `git rev-parse definitelynotarev & echo AFTER_FATAL_EXIT=%errorlevel%` printed 0 after the fatal (parse-time expansion). (3) `git check-ignore -v runs/ .workspace/ godot-mcp/godot/` → `.gitignore:12/11/33` match, so an empty diff over those paths proves nothing."},
    {"id": "C20-disclosure-accuracy", "pass": false, "evidence": "F-DR72-2 claims the user name never survives (report line 50: '用户名/凭据值不残留，但目录结构残留') and D280 accepted the `\\r` edge on that premise; my p10/p11/p13 show user names surviving, and p13 shows the old scanner removed what the new one leaves (a regression). The report's gate tally is wrong (D3), and two shipped documents contradict the shipped planner-view decision (D4/D5)."}
  ],
  "defects": [
    {"id": "D1", "severity": "major", "what": "The escape-aware terminator fires on the second byte of a JSON-escaped (doubled) backslash when the next character is `n` or `r`. Because every Windows path in a trajectory is written with doubled backslashes, any component named `runs`/`node_modules`/… cuts the value there: one backslash is deleted, the surviving `\\r`/`\\n` becomes a real JSON escape decoding to CR/LF, and the rest of the path stays visible. The (c) JSON gate cannot catch it (the result still parses). This is the headline item's target shape (`runs/smoke-t10/iter-1/traj/*.json` really contain `HOH_GAME_ROUTE=F:\\\\moonbit-hof-rs\\\\runs\\\\…`). The predicate must only start an escape when the backslash is not itself escaped (even count of preceding backslashes).", "reproduction": "OUT-OF-REPO probe test p14 (C:/Users/wyl/AppData/Local/Temp/dr72acc/probe/tests/dr72_probe2.rs): input `{\"env\": \"HOH_ARTIFACT_DIR=F:\\\\moonbit-hof-rs\\\\runs\\\\smoke-t10\\\\iter-1\"}` (valid JSON) → refused=None, output `{\"env\": \"HOH_ARTIFACT_DIR=<redacted>\\\\runs\\\\\\\\smoke-t10\\\\\\\\iter-1\"}`, decoded env = `<redacted>` + CR + `uns\\smoke-t10\\iter-1`. Byte layout of the real dump confirmed with a read-only Python slice of `runs/smoke-t10/iter-1/traj/tester.attempt1.json`."},
    {"id": "D2", "severity": "major", "what": "The disclosed residual is wrong where it matters most. F-DR72-2 says only directory structure survives and no user name does; in fact a user name survives (a) whenever it appears in a later element of a `;`-separated PATH (only the first element is redacted — p10) and (b) whenever the path contains a `\\r`/`\\n` component before the user directory (p11). Case (b) is a REGRESSION introduced by the escape-aware terminator: the old scanner ran to the physical line end and removed the whole value (p13). D280's decision (c) — accept the `\\r` edge because no credential and no user name survives — rests on the false premise.", "reproduction": "p10: `PATH=C:\\Windows\\system32;C:\\Program Files\\nodejs;C:\\Users\\wyl\\AppData\\Roaming\\npm` → `PATH=<redacted>;C:\\Program Files\\nodejs;C:\\Users\\wyl\\AppData\\Roaming\\npm`. p11: `HOH_ARTIFACT_DIR=F:\\repo\\Users\\wyl\\runs\\run-1` → `HOH_ARTIFACT_DIR=<redacted>\\repo\\Users\\wyl\\runs\\run-1`. p13: the simulated old scanner on the same input yields `HOH_ARTIFACT_DIR=<redacted>\\n` (user name gone). The batch's own `redaction_defect.txt` shows the real leak shape is exactly a `;`-separated PATH tail containing `C:\\Users\\wyl\\node_modules`. All probe tests pass; my plants are restored byte-exactly."},
    {"id": "D3", "severity": "minor", "what": "The report's gate arithmetic is wrong: it claims 475 passed / baseline 458 / net +17 (lib +5). The committed tree yields 484 passed / 0 failed / 7 ignored (my full run, CARGO_EXIT=0, and `cargo test -- --list` = 491 = 484+7); the correct pre-batch baseline is 465 (the task book's own number and exactly the number of distinct test-function names at 9e7f8ea), and the real net is +19 with lib +7. The error understates the gate, so C13 still passes, but the number in the report and in D280 is not reproducible from the tree.", "reproduction": "cargo test --offline --no-fail-fast (fresh, after per-file touch) → 484/0/7, exit 0; my tally script over the 53 result lines; `git grep -c '^#\\[test\\]' 9e7f8ea` per file vs HEAD."},
    {"id": "D4", "severity": "minor", "what": "Two shipped documents contradict the shipped planner-view decision. `TASK-DR72-evidence/REDACTION-POLICY.md` §2 lists `iter-*/planner-view/**` in the 'generated copy' row, and `src/runtime/record.rs:305` says the sweep seals planner-view — while `run_loop::frozen_evidence_roots` deliberately does NOT seal it (and the report says so). A reader of the batch's own controlled evidence would believe the opposite of the code.", "reproduction": "read the two files against src/runtime/run_loop.rs:400-408; my plant C run shows nothing enforces the list either way."},
    {"id": "D5", "severity": "minor", "what": "The stated reason for not consuming the terminator is false, and it is repeated in the code comment and in REDACTION-POLICY.md §3: 'deleting its backslash is what turned a valid string into a control character'. My p2 spliced the same input with end=backslash index, index+1 and index+2: all three parse and none leaves a control character in the string; the old damage's control character came from the PHYSICAL newline being left inside an unterminated string (p3's parse error). Not consuming is still the right choice — for content fidelity (the escaped newline survives) — but the documented rationale is wrong.", "reproduction": "p2: `consume-backslash(end=bs+1)` → `…<redacted>n</output>`, parses, no control char; `consume-both` → `…<redacted></output>`, parses. p3: the old simulation's output is invalid with 'control character (\\u0000-\\u001F) found while parsing a string'."},
    {"id": "D6", "severity": "minor", "what": "Any JSON escape family other than `\\n`/`\\r` (`\\t`, `\\uXXXX`, `\\\"`) still runs the value to the physical line end, so the assignment splice is refused and the assignment redaction — the DR-69 'where the credential lives' rule — is silently dropped for a perfectly legitimate JSON file, leaving `HOH_MODEL_API_KEY=` (or any harness assignment) in the evidence. It is reported as a warning, and a known credential value is still removed by the value rule, so it is not a total no-op; but the report only mentions 'not exhaustive over escape families' and never states this consequence.", "reproduction": "p4/p12: `{\"a\": \"HOH_MODEL_API_KEY=sk-abcdef\\tX\"}` → refused, and the file-level pass writes it back with `HOH_MODEL_API_KEY=` intact (value redacted)."},
    {"id": "D7", "severity": "minor", "what": "tests/frozen_evidence.rs:326-332 says `the_redacted_sample_is_regenerable_from_the_production_pass` is 'not part of the suite's verdict … runs only when the sample is deliberately regenerated', but it carries no `#[ignore]`; it runs in every gate (frozen_evidence = 6 passed, 0 ignored in my run) and writes `target/dr72-redaction-sample/`. Harmless (it passes, and it is good that the sample is checked), but the claim is inaccurate.", "reproduction": "grep -n ignore tests/frozen_evidence.rs → only the doc line; the gate's frozen_evidence line is 6 passed / 0 ignored."},
    {"id": "D8", "severity": "minor", "what": "The e1_increment test's doc says it 're-derives the diff … equal to that independent computation', but the expected `added`/`modified` lists are hardcoded literals; the only independent checks are the frozen snapshot's bytes and the count of `versions/` entries. The production mechanism and the non-vacuity companion are sound, so this is a documentation overstatement.", "reproduction": "tests/e1_increment.rs:936-968 (expected_added/expected_modified literals)."},
    {"id": "D9", "severity": "info", "what": "`the_wrong_parameter_name_is_refused_with_the_accepted_names` asserts the literal `` `path` `` rather than the fixture-derived list, so it would pass if `accepted_parameters` were hardcoded to the right value; test 1 and test 2 do derive their names from the fixture, which is what makes the fix non-hardcoded. Minor, because test 1 (`the_captured_contract_declares_path_for_the_property_tool`) is the derivation guard and it is load-bearing.", "reproduction": "tests/tool_parameter_contract.rs:278-281 vs :203-223."}
  ],
  "risks": [
    "The generated `.redacted.<ext>` copies are written INSIDE sealed areas (`traj/`, `versions/`). `VersionStore::rollback` does `copy_tree(source, workspace, excludes)` (src/runtime/snapshot.rs:133-148) and `snapshot_role` only copies when the version directory does not exist (:85-90), so a copy created under `versions/<id>/` can be rolled back into the workspace on a later iteration and then enter the next snapshot/hash. The report flags this as unverified (its §6.4.2); I confirmed the mechanism by reading the store and did not run it.",
    "The planner-view in-place rewrite is only safe while nothing parses planner-view. Today true (I grepped src), pinned by secret_isolation.rs; a future consumer reopens D276's rule.",
    "The unsupported-escape refusal (D6) leaves harness assignments in legitimate evidence while only warning; a reader who skims warnings.log will not notice the assignment rule did not run.",
    "The thread-local parameter hint is correct only because the CLI's root future is polled on one `block_on` thread. If a future call path wraps `call_with_meta` in `tokio::spawn`, the guidance silently degrades to 'the harness has no schema' — there is no test for that path.",
    "Presence of the route file is still not atomic; the loss mode remains DR-43's explicit refusal (unchanged, and now pinned by the race test).",
    "The `runs/` digest scheme is culture-order dependent; the five values only compare within that scheme (the report states this, and I reproduced it with the same scheme)."
  ],
  "unverified": [
    "Real-machine behaviour of every kind (no Godot, no network, no model endpoint): the redaction shapes I analysed come from frozen files, not from a live round.",
    "The `versions/` copy → rollback → next snapshot interaction: reasoned from src/runtime/snapshot.rs and run_loop.rs, not exercised.",
    "The implementer's four plants exactly as described: I verified the byte-exact restoration against their out-of-repo backup and reproduced equivalent plants (escape arm, D2 reversion, unsealed traj), but I did not replay their red transcripts.",
    "Their claim that every reported red was taken after clearing stale cargo fingerprints: I reproduced the false-red mechanism itself, but their transcripts are their evidence, not mine.",
    "The sidecar for `.spec/hof-rs/tasks/TASK-SMOKE-T10-evidence/analysis/redaction_defect.txt`: the file still carries environment values (I read it); D280 assigned the sidecar to a later batch, so it is out of DR-72's scope.",
    "E1/E3 and all product behaviour: out of scope for this offline batch."
  ],
  "notes": {
    "plants": "A secrets.rs:167 escape arm -> false (target test red, implementer's red text reproduced verbatim); B godot.rs:3909 publish-at-install reversion (D2 test red, 5 siblings green); C run_loop.rs:405 traj root unsealed (all sealing-related tests green -> coverage gap). All three restored with cmp against out-of-repo backups; git hash-object == HEAD for every touched file.",
    "report_block_parses": true
  }
}
```

## 1. Per-item table (the seven jobs, my own evidence)

| # | Job | Verdict | Decisive evidence I produced |
|---|---|---|---|
| 1 | Redactor fix (headline) | **partial / fail** | p1 confirms the exact shape is fixed (valid JSON, pure splice, quote+comma+field survive). But p14 shows the predicate misfires on JSON-escaped `\\` before `n`/`r` — the shape the real trajectories use — leaving path tails and injecting a CR/LF; p15 shows the shipped cross-check ends at a `;` and proves nothing; p2 shows the non-consumption rationale is false |
| 2 | Refused-splice path | **pass (with D6)** | p8 refusal leaves the file byte-identical and is reported; run_loop pushes it into `warnings.log`; plant A confirms removing (a) turns the assignment rule into a refusal/no-op; p4/p12 show the residual cost for other escape families |
| 3 | Sealed evidence + exception | **pass (mechanism) / fail (wiring)** | p6/p7: sealed originals byte-identical, copies generated, in-place edit caught; planner-view exception is sound and pinned by secret_isolation e2e. Plant C: dropping the `traj` root from production leaves all sealing tests green (C6 fail); two shipped docs contradict the decision (D4) |
| 4 | `evidence_diff` | **pass** | T10's frozen result.json really is empty while the version changed (F-T10-3 confirmed); production sets it on the success path (run_loop.rs:1794) from the iteration-start manifest (:1077); exact-lists test + honest-empty companion |
| 5 | Parameter contract | **pass** | Fixture says `path` for `editor_get_node_properties` and `node_path` for `editor_get_collision_info`; names come from that `include_str!` snapshot; code preserved, classification unchanged (`-32602` + `unknown parameter`, code retained, exit 5) |
| 6 | Carried gaps | **pass** | One shared predicate (battery :514 and round :3914 both `scene_tree_readiness`); plant B reddens the in-poll discriminator under the DR-70 reversion while 5 siblings stay green; race test genuine, 3/3 green, torn=0 assertion, explicit-refusal loss mode |
| 7 | Gates/plants/guards/honesty | **pass on the facts, fail on disclosure** | 484/0/7 exit 0, fmt 0, ignored 7, 0 removals; five digests reproduce with the t6 anchor; PRD/mario/engine/deps/push all clean; three false-green traps + the false-red trap reproduced; but the report's tally is wrong (D3) and F-DR72-2's user-name claim is false (D2) |

## 2. My plants and counterexamples

Driver: edits through the file tools; backups in
`C:\Users\wyl\AppData\Local\Temp\dr72acc\bak\`. Every restore criterion: `cmp` against the
backup equal, `git hash-object` == `HEAD:<path>`, `git status --porcelain -uall` empty.

| Plant | Where (production) | What I disabled | Result | Restore |
|---|---|---|---|---|
| **A** | `src/runtime/secrets.rs:167` | `b'\\' => matches!(…)` → `false` | `an_assignment_inside_a_json_string_survives_an_escaped_newline` **RED**, with the implementer's quoted text verbatim | `cmp` equal; sha256 `ef76206dcaabbf52` = backup = pre-plant; blob `aa1ffa06fe6d633c` = HEAD |
| **B** | `src/adapter/godot.rs:3909` | re-added `publish_game_endpoint()` right after install (DR-70 shape) | `the_round_readiness_poll_never_exposes_the_route_while_it_runs` **RED** (`sightings` all true); the other 5 round tests green | `cmp` equal; blob `10af219493661a3f` = HEAD |
| **C** | `src/runtime/run_loop.rs:405` | removed the `iter-*/traj` sealed root | lib + frozen_evidence + secret_isolation + secret_hygiene + record_symmetry + evidence_isolation **all GREEN** → the production sealed-root list is untested | `cmp` equal; blob `f36f0b611cee1673` = HEAD |

Counterexamples (out-of-repo probe crate, 14 tests, all passing; it reads the repo
read-only and uses tempdirs only):

* `p14` — doubled backslash before `r`/`n` is mistaken for an escape (D1).
* `p15` — the shipped doubled-backslash fixture is decided by a `;` (C3 fail).
* `p10`, `p11`, `p13` — user names survive; `p13` shows the old scan removed what the new one leaves (D2).
* `p2` — consuming vs not consuming: all three variants parse, none injects a control character (D5).
* `p3` — the old scanner's real damage reproduced (invalid JSON, closing quote and comma gone, next field's text unreachable).
* `p4`, `p12` — the `\t` family is refused and the assignment stays (D6).
* `p5` — plain-text `\repo\…` is cut at `F:` (F-DR72-2 as a behaviour).
* `p6`, `p7` — sealed copy mechanism and component-wise containment.
* `p9` — the committed sample is exactly the production pass's output, spans included, and its input is synthetic (`F:\stand-in\…`, `C:\stand-in\user\…`).
* `p16` (implicit) — `runs/**` was only read; digests and mtimes prove zero writes.

## 3. Independent judgement on each question

1. **Is the redactor fix real?** For the exact single-escape adversarial shape, yes —
   and the byte-level claims (valid JSON, zero bytes changed outside the spans, closing
   quote/comma/following field intact) are reproducible (p1). For the shape the real
   dumps actually contain, no (D1). The claim that "the fatal terminator is the escape
   itself rather than the physical newline" is defensible as a statement of the missing
   terminator; the accompanying claim that not consuming it is what avoids a raw control
   character is **false** (D5), and the predicate is under-specified about escaped
   backslashes.
2. **Refused splice.** It is refused and reported, never silently written — but only
   when the resulting JSON is broken. The install of a legitimate file whose assignment
   is followed by `\t`/`\u`/`\"` is refused, the assignment rule is dropped, and the file
   may still be written by the value rule (D6). The implementer's "without (a) the whole
   redaction becomes a no-op" reasoning is verified for the assignment rule (plant A);
   it overstates "whole" when a credential value is known.
3. **Sealed evidence and the exception.** The mechanism holds and is testable; the
   exception for `planner-view` is sound (nothing parses it; an existing e2e test pins
   in-place erasure and would redden if it were sealed). What is **not** sound is the
   paperwork: the policy document and a code comment describe the opposite rule (D4).
4. **`evidence_diff`.** Real on the success path, honestly-empty pinned by a companion,
   and the frozen T10 artifact really exhibits the original defect. The test's doc calls
   its hardcoded expectations an "independent derivation" (D8, cosmetic).
5. **Parameter contract.** Verified from the fixture itself; the sibling tool genuinely
   differs; the fix keeps the error class and verbatim engine text and derives the names
   from the same snapshot `TOOLS.md` uses. One assertion is literal rather than derived
   (D9).
6. **Carried gaps.** D1 is closed (one predicate). D2 is genuinely closed — I proved it
   by planting the historical reversion, which the implementer did not. The race test is
   real and stable.
7. **Gates, plants, guards, honesty.** The gate is *better* than reported (484 vs 475);
   plants are restored byte-exactly (their backup still matches the tree, and my own
   three plants restore with `cmp`); the runs/mario/PRD/engine/deps/push guards hold;
   all three false-green traps and the false-red trap are reproduced. The honesty
   problem is concentrated in D2/D3/D4/D5.
8. **The `\r`/`\n` edge (adjudication).** **Not an acceptable documented cost.** The
   documented cost is wrong on its own terms: user names do survive (p10/p11), and for
   plain-text dumps the new terminator is a regression that leaves content the old scan
   removed (p13). D280 accepted the edge on a premise my evidence falsifies, so the
   decision should be reopened; the fix is to require an unescaped backslash (even run
   of preceding backslashes), which also fixes D1, or to drive `.json` files through a
   parse-rewrite path.

## 4. What I did not check

* Any live engine, port, model endpoint or real round (hard constraint).
* The implementer's own transcripts (their gate log, their four plant sessions) — I
  reproduced the mechanisms instead of trusting them.
* The rest of `TASK-DR72-evidence/**` beyond the three sample files, the README and the
  policy; the historical DR-69/DR-70 redaction incidents; the DR-73 material.
* Whether the dispatcher's concurrent commits (D280, `TASK-DR73.md`) changed anything I
  audited — they touch only docs, and `git diff 04abf5f..HEAD -- src tests` is empty.

## 5. Advice for the next batch

1. **Fix the predicate, not the comment**: treat `\` as starting an escape only when it
   is not preceded by an odd run of backslashes (equivalently: count the run). Add a
   probe of the exact real shape (`HOH_GAME_ROUTE=F:\\…\\runs\\…` inside a JSON string)
   and assert the decoded value carries no CR/LF and no path tail; the current
   `a_windows_path_value_is_not_mistaken_for_an_escape` must stop being `;`-decided
   (p15).
2. **Retract F-DR72-2's user-name claim** and re-open decision (c) with the `;`-PATH and
   `\r`-component counterexamples (p10/p11/p13). If PATH values matter, redact the whole
   assignment through the next real delimiter, not just the first element.
3. **Pin the production sealed-root list**: a test must go through `run_loop` (or expose
   `frozen_evidence_roots`) so that dropping `traj`/`versions`/`quarantine` reddens
   (plant C).
4. **Recompute the gate tally from the tree** (484/0/7, baseline 465, +19) and correct
   the report and D280; keep the per-file `touch` and the fingerprint caveat.
5. **Reconcile the two documents that contradict the planner-view decision**
   (`REDACTION-POLICY.md` §2 and `record.rs:305`), and drop the physically impossible
   "control character from deleting the backslash" explanation in both the code comment
   and the policy.
6. **Bound the refusal loss**: for a legitimate JSON file, a refused assignment splice
   should be loud enough to be unmissable (or the file should be routed through a
   parse-rewrite path), and the report should state that the assignment rule — not just
   the value rule — is what fails.
7. **Keep the sample test but fix its doc** (it runs every gate), and re-enable the
   `versions/` copy → rollback experiment the report already flags.

---

### Acceptance-judge honesty statement

* I did **not** modify anything under `runs/**` (not one byte, not a temporary file),
  `.workspace/mario/**`, `PRD-mario.md`, `DECISIONS.md` or `godot-mcp/**`.
* I made exactly three temporary edits to production sources (plants A/B/C) and restored
  each with `cp -p` + `cmp` against out-of-repo backups; `git status --porcelain -uall`
  is empty and `git hash-object` equals `HEAD` for every touched file. I fixed nothing
  I found.
* I staged nothing, pushed nothing, started no engine, touched no port, used no network
  and called no model endpoint.
* All my scripts, the probe crate and its output and the backup tree live outside the
  repository in `C:\Users\wyl\AppData\Local\Temp\dr72acc\`.
* This file is written once; I will not edit it afterwards. (If I do, I will say so.)
