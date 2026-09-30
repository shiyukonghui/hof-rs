# TASK-DR71-ACCEPTANCE — independent acceptance of the DR-71 route-lifetime batch

- Judge: a fresh acceptance subagent with **no upstream conversation context**. Nothing in
  `TASK-DR71-REPORT.md` was treated as evidence; every number below was produced by me, with my own
  command/plugin runs, my own out-of-repo probe crate, and my own production-code plants.
- Object: outer repo `F:\moonbit-hof-rs`. **Audited tree: `HEAD = 6b317568db06434ab0e8f81a72c6ba652a0df56c`.**
  The *code/test/evidence* content is frozen at `77c46fe`; every commit after it is docs-only
  (`git diff --stat 77c46fe..HEAD` = the report, `DECISIONS.md` D275, and the two whole-line-anchoring
  files `scripts/byte_claims.py` / `tests/byte_claims.rs`). The task book named `HEAD = 77c46fe`; while I
  was auditing, the coordinator landed `f6681ef`, `3e62c38`, `9af301f`, `6b31756` (report + D275). I
  re-ran the gate and every plant against the later tree; no `src/**` byte differs from `77c46fe`.
- Offline: **no Godot, no external port, no network, no model endpoint, no real-machine round.** The only
  sockets are the shipped tests' and my probe's `127.0.0.1` loopback doubles. I wrote **zero bytes under
  `runs/**`** (digest + mtime, §C6), and nothing under `.workspace/mario/**`,
  `.spec/hof-rs/PRD-mario.md`, `DECISIONS.md`, or `godot-mcp/**`. All my scripts, backups and probe
  material live outside the repo in `C:\Users\wyl\AppData\Local\Temp\dr71acc\` and the reused
  `...\dr70acc\probe\` (I added one test file there). My five plants are restored byte-exactly.
- **Verdict: `pass`** — all four task-book items and all seven jobs are independently reproduced. I found
  **two minor residual gaps** (D1: the round-game readiness predicate accepts a *successful non-scene-tree*
  answer while the battery refuses it; D2: no shipped test observes the round route *during* the readiness
  poll, so a "publish early, clear on failure" reversion passes all eight round-game tests), plus the
  disclosed content-vs-presence race and a gate-flake caveat (§C6). None of these falsifies the batch's
  stated property ("a **failed** start leaves no route"), which my own plants show is now real and
  load-bearing. I did **not** fix anything I found.

---

## 0. Structured verdict (machine-readable)

```json
{
  "verdict": "pass",
  "object": {
    "repo": "F:\\moonbit-hof-rs",
    "audited_head": "6b317568db06434ab0e8f81a72c6ba652a0df56c",
    "code_frozen_at": "77c46fe",
    "batch_baseline": "553dec2",
    "commit_count_after_baseline": 9,
    "worktree_at_end": "git status --porcelain -uall = 0 lines, git diff --stat = 0 lines"
  },
  "criteria": [
    {"id": "J1-route-never-lies", "pass": true, "evidence": "Mechanism: GodotAdapter::start_round_game src/adapter/godot.rs:3898 installs the announced record for IN-PROCESS routing only, polls readiness at :3901-3910, and publishes at :3931 only after ready.ok; the not-ready branch (:3919) clears the route then bails, and a publish failure (:3931-3937) clears and returns Err. run_loop::start_round_game src/runtime/run_loop.rs:542-548 withdraws the in-process route AND the file on ANY Err, independently of what the adapter did. My plant MP1 (delete that wrapper withdraw) reddens tests/round_game_window.rs:441 with RoleProbe { route_exists: true, exit_code: Some(0) } - a real hoh subprocess ADOPTING the lying route, the exact DR-70 A1 symptom. My plant MP2 (revert :3898 to publish-before-ready AND drop the :3919 clear) reddens tests/round_game_start.rs:262 with the published record Ok(...). Both restored byte-exactly. The previous acceptance's case (endpoint announced, readiness refused, route survives) is therefore closed at the source: before readiness not even a temporary file exists, because install cannot write."},
    {"id": "J1-closes-vs-narrows", "pass": true, "evidence": "CLOSES for the stated failure mode, with one predicate caveat. The ordering genuinely eliminates the publish-before-ready window (install = in-process only; publish is a separate call placed after the predicate). Two independent layers withdraw on failure. My MP2a-only plant (publish early but KEEP the failure-path clear) still passes a_start_that_never_becomes_ready_publishes_no_route, because that test only inspects the end state - so the ordering is not independently pinned there (that is D2). The predicate itself is weaker on this path than in the battery: wait_for_game_ready returns ok=true for ANY successful JSON-RPC response (src/tools/reliable.rs:311-320), while the battery additionally requires describe_scene_tree_shape. My external probe (real GodotAdapter, loopback doubles) showed a game answering running_game_get_scene_tree with {\"tree\":\"not a scene tree at all\"} yields start_round_game -> Ok and a PUBLISHED route, whereas the shipped battery test an_unconfirmed_battery_play_never_exposes_a_route refuses exactly that answer. That is D1."},
    {"id": "J2-publish-loud", "pass": true, "evidence": "McpChannel::publish_game_endpoint (src/tools/mod.rs:439-463) returns the io::Error mapped to anyhow with path and endpoint instead of the DR-70 let _ =; start_round_game turns it into a failed start and clears (:3931-3937); publish_game_route cleans its .json.tmp-publish on failure (src/tools/endpoint.rs:117-120). My plant MP3 restored let _ = endpoint::publish_game_route(...); Ok(()) and tests/round_game_start.rs::a_publish_failure_is_reported_instead_of_swallowed went RED at :344 ('a route that could not be published must fail the start, not be swallowed: Ok(Some(GameEndpointRecord {...}))'). The consequence is observable, not assumed: that test places a DIRECTORY at the route path so publication genuinely fails, then asserts the start is Err, the in-process route is empty, and no tmp-publish file remains. Restored byte-exactly (mod.rs blob fdf44b92198a == HEAD)."},
    {"id": "J3-failure-path-in-suite", "pass": true, "evidence": "The double genuinely fails after publishing: tests/common/mod.rs:579-587 RoundGameStub::failing_after_publish makes FakeAdapter::start_round_game call tools.register_game_endpoint(record) (which publishes through the PRODUCTION path) and then anyhow::bail! - not an Ok(None)/Ok(Some) arm. tests/round_game_window.rs::a_failed_round_game_start_leaves_no_route_and_the_round_proceeds drives the REAL run_loop::run and, inside the Developer step, spawns the REAL hoh binary with HOH_GAME_ROUTE (probe_as_role, :165-190). It asserts all three: (a) probes[0].route_exists == false and !route.exists() after the round (:441-449); (b) result.is_ok() (:432); (c) exit_code != Some(0), the output contains game_endpoint_unavailable, and the game double served zero calls (:453-468). MP1 reddens exactly this test, so the coverage is load-bearing, not decorative."},
    {"id": "J4-scene-ruling-unified", "pass": true, "evidence": "developer.md's [self-test] (:109-115) and [definition-of-done] #3 (:137-143) now carry the same verbatim ruling 'do not start a game of your own' and forbid the self-boot; src/prompts/skills/godot-dev.md section 5 (:88-91) already said it; tests/delivered_materials.rs:157-181 checks BOTH the delivered prompt and the skill for the verbatim ruling and rejects any sentence naming editor_play_scene without a negation (imperative_play_scene_sentence, :93-113); :190-207 (the old audience-aware guard) now checks the PROMPT as well as the skill for 'tools call editor_play_scene'. tests/e1_increment.rs:782-802 replaces the old 'prompt contains editor_play_scene' needle with 'the [definition-of-done] section must carry the prohibition verbatim' and 'must not contain boot the scene with'. My plant MP4 restored the old imperative 'Check editor_get_errors ... and boot the scene with editor_play_scene before you end the turn.' into developer.md and the guard went RED at delivered_materials.rs:174 naming developer.md - i.e. the previous blind spot (guard saw only the skill) is closed. Restored byte-exactly (developer.md blob 2126a2e64fdf == HEAD)."},
    {"id": "J5-byte-claims-computed", "pass": true, "evidence": "My independent recomputation from the two git blobs and the worktree: original 52200 B / CR 0 / LF 184 / records 184 / dir_b_p 1; dr69 52176 / 0 / 183 / 183 / 0; worktree 52205 / 0 / 184 / 184 / 1; dr69 substitution 52 -> 28 and worktree 23 -> 28; deltas -24 / +5. Every value equals the generated block in REDACTION.md, TASK-DR70-REPORT.md and TASK-DR71-REPORT.md. Mechanism is real, not a hand-typed table: python scripts/byte_claims.py --emit prints exactly those keys, --check reports ok for all three documents, the script computes from git objects + the worktree, and tests/byte_claims.rs recomputes every key in Rust and compares key-by-key and in order. My plant MP5 hand-edited dr69_replaced_bytes = 52 -> 54 in REDACTION.md and the test went RED at tests/byte_claims.rs:250 showing left ('54') vs right ('52'). Restored byte-exactly (REDACTION.md blob bc1fc2ca5bf3 == HEAD). No third recurrence of 'self-report vs byte fact'."},
    {"id": "J6-gates-plants-guards-race", "pass": true, "evidence": "Clean gate (my run3): cargo test --offline --no-fail-fast -> 465 passed / 0 failed / 7 ignored, CARGO_EXIT=0; cargo fmt --check -> exit 0; tests/** test functions 330 (553dec2) -> 340 (HEAD), REMOVED = [] and the 10 added are the new DR-71 tests; #[ignore occurrences 8 == 8; ignored 7 == 7. All five of my plants (MP1 src/runtime/run_loop.rs, MP2 src/adapter/godot.rs, MP3 src/tools/mod.rs, MP4 src/prompts/developer.md, MP5 the committed evidence note) are byte==my backup, git hash-object == HEAD blob, and empty porcelain/diff per path; final worktree git status --porcelain -uall = 0 and git diff --stat = 0. runs/smoke-t6|t7|t8|t9 digests unchanged with smoke-t6 = c144ef32...7a9c03 (scheme self-validated), 0 entries newer than 2026-09-30 11:27:30 in any tree. .workspace/mario 17 files byte-identical to runs/smoke-t9/versions/1f3d20ed...; PRD-mario.md sha256 4c81c3a9...f5c3a; no Cargo.toml/lock change; origin/master 9aebbe15... and nothing pushed or staged; nested engine git -C godot-mcp/godot HEAD fc63af77... with 0 porcelain lines; outer pathspec control ls-files godot-mcp = 6484 vs godot-mcp/godot = 0. All three false-green traps reproduced (nonexistent pathspec -> empty + exit 0; cmd ^ eaten and %errorlevel% parse-time-expanded to 0 after a fatal; check-ignore shows runs/, .workspace/, godot-mcp/godot/ are ignored so an empty diff there proves nothing). Race: my own probe (real publish_game_route, one writer one reader) observed 9658 reads with 7074 misses (73.2%) and 0 corrupt/torn reads - content atomic, presence not; no shipped test exercises it (grep: no concurrency around publish in tests/**). I judge that acceptable-but-incomplete: the loss mode is DR-43's explicit game_endpoint_unavailable, not a transport error, and the harness is effectively the only publisher; the report discloses this as R3."},
    {"id": "J7-honesty", "pass": true, "evidence": "The report states no real-machine probability (grep for probability/percent finds only R2, which declines to give one), does not claim E1 or E3 met (section 7.1 explicitly says neither was run and the strong DR-70 phrasing is not reused), and does not claim the route problem is fully solved (7.1 limits the claim to 'start failed => route does not lie'; 6.2 keeps R3/R5). Its caveats are otherwise accurate: R1 engine-level inference, R3 presence race untested, R4 role-writable trust boundary, R5 no whole-round liveness proof, R6 expiry/pid reuse, R7 git dependency of byte_claims, R8 panic path and non-Windows pid. It discloses the empty-battery-test self-catch, the commit-history mishap, and (in the addendum) a concurrent-cargo environment incident. The one honest omission is D1/D2 below."}
  ],
  "defects": [
    {"id": "D1", "severity": "minor", "what": "The round-game readiness predicate is weaker than the battery's: start_round_game accepts any successful JSON-RPC response (reliable.rs:311-320) and does NOT apply describe_scene_tree_shape. A game that answers running_game_get_scene_tree with a successful but non-scene-tree payload is treated as confirmed-ready and its route is published, while the battery refuses exactly that answer (shipped test an_unconfirmed_battery_play_never_exposes_a_route / play_scene_ready_refuses_a_payload_that_is_not_a_scene_tree). The route still points at an endpoint that answers, so this is not the DR-70 'route to a dead game' defect; it is a readiness-semantics asymmetry, untested, and not listed in the report's residual risks.", "reproduction": "My out-of-repo probe C:\\Users\\wyl\\AppData\\Local\\Temp\\dr70acc\\probe\\tests\\dr71_ready_shape.rs (drives the real GodotAdapter::start_round_game against loopback doubles; no Godot, no network): the non-tree answer prints 'start_round_game -> ok=true', 'route exists: true', 'route bytes: {\"endpoint\":\"http://127.0.0.1:49415/mcp\",...}'. Control with a real scene-tree answer also publishes (2 passed). Code: src/adapter/godot.rs:3901-3938 vs :975-1028."},
    {"id": "D2", "severity": "minor", "what": "No shipped test observes the round-game route DURING the readiness poll: a_start_that_never_becomes_ready_publishes_no_route only inspects the end state, so it cannot distinguish 'never published' from 'published then cleared'. The battery has that discriminator (RpcDouble::watching / sightings); the round-game path does not. A reversion to publish-early-with-clear-on-failure would pass the whole round-game suite while reintroducing the transient window the batch set out to eliminate.", "reproduction": "My plant MP2c (insert an immediate publish_game_endpoint() after the install at src/adapter/godot.rs:3898, with clear-on-failure handling) makes all 4 tests of round_game_start.rs and all 4 of round_game_window.rs PASS (8/8 green), yet a concurrent reader could see the route on disk during the poll - the same window the shipped battery test catches with its watching mechanism. Source: src/adapter/godot.rs:3898-3938; tests/round_game_start.rs:241-279."},
    {"id": "D3", "severity": "informational", "what": "Audit-window bookkeeping, not a delivered defect: while I audited, HEAD advanced 77c46fe -> 3e62c38 -> 6b31756 and the worktree was transiently dirty (the report itself modified) and the report's own generated block was, in the intermediate revision, an EMPTY marker pair that the first-marker locator skipped in favour of a quoted sample. Commit f6681ef fixed the locator to whole-line anchoring and the final report carries exactly one real generated block, so this is resolved at the audited HEAD.", "reproduction": "git reflog; the intermediate report revision had two DR-71-BYTE-CLAIMS pairs, one inside a pasted --emit sample; the final .spec/hof-rs/tasks/TASK-DR71-REPORT.md has exactly one anchored pair (my compare2.py: anchored_blocks=1 in all three documents, values equal to --emit modulo Python's stdout CRLF translation)."}
  ],
  "risks": [
    "R1 (highest, inherited) Engine-level behaviour is still inference: nothing offline shows that a real Godot accepts a round-wide editor_play_scene on an empty project, that the game survives the Developer's writes/reloads, or that it refuses a second play. The containment proof is real at the orchestration/channel level (real run_loop, real hoh subprocess, real route file); the game and the editor are loopback doubles.",
    "R2 (new, D1) The round-game readiness predicate accepts any successful RPC response, so 'answering but not a scene tree' is published as ready while the battery refuses it. Untested and undisclosed.",
    "R3 (new, D2) The round-game ordering is not pinned by an in-poll observation; a publish-early-with-clear reversion passes all eight round-game tests.",
    "R4 The publish/adopt path is content-atomic but not presence-atomic (my probe: 7074/9658 reads saw no route, 0 torn). Safe in loss mode (explicit game_endpoint_unavailable) but unsynchronised and untested.",
    "R5 The route file remains a role-writable trust boundary (validate_published_route never establishes that the endpoint is THIS round's game).",
    "R6 start_round_game proves only that the game answered once at start, not that it is alive for the whole round; 6-hour expiry and Windows pid reuse remain the weakest of the DR-70 checks.",
    "R7 The gate needs an uncontended workspace: my first two full runs both hit tests/evidence_battery.rs::readiness_timeout_fails_the_step_and_is_journalled (run1 the harness aborted, run2 FAILED with 'the battery never fails the round by itself: ... (os error 32)'). In isolation that test passed 3/3 (18-19 s each) and my clean run3 gave 465/0/7. Two agents ran cargo in this workspace simultaneously (the report's addendum section 7.9 documents the same incident from its side), which is the cause; the finding is environmental, not a code regression, but a future gate must run alone."
  ],
  "unverified": [
    "U1 Real-machine behaviour of every kind: no Godot, no engine, no external service, no model endpoint, no real round. Everything engine-level is inference.",
    "U2 I did not re-run the implementer's own plant transcripts or their gate log (their evidence, not mine). I verified the shipped tests with my own five plants and reproduced the gate myself.",
    "U3 I did not byte-audit the rest of .spec/hof-rs/tasks/TASK-SMOKE-T9-evidence/** beyond REDACTION.md, dev1_commands.txt and the .gitattributes pin.",
    "U4 I did not verify the batch's historical narrative (DR-65..DR-70 accounts, the amend/reset story) beyond what git shows.",
    "U5 I did not test a panic between the round-game start and run()'s wrapper (the wrapper covers Err and the normal return; a panic would skip it).",
    "U6 Non-Windows pid-liveness and the Unix kill(pid,0) branch are unexercised here.",
    "U7 The race judgement is my probe-level observation (one writer, one reader), not a formal analysis of the real multi-process publish/adopt interleavings.",
    "U8 I did not prove describe_scene_tree_shape is the ONLY battery-only readiness strictness, nor exhaustively enumerate every path that can publish a route."
  ]
}
```

---

## 1. Per-item table (the seven jobs)

| # | Job | Verdict | My key evidence (self-produced) |
|---|---|---|---|
| 1 | Route must never lie (headline) | **pass** | install-only at `godot.rs:3898`, publish after readiness at `:3931`, clear on every failure, wrapper withdraws on any Err (`run_loop.rs:542-548`); MP1 -> `route_exists: true, exit_code: Some(0)` red; MP2 -> published record red |
| 2 | Publish failures loud | **pass** | MP3 restores `let _ =` and `a_publish_failure_is_reported_instead_of_swallowed` reddens at `:344`; the test uses a directory obstacle so the failure is real and checks the temp file is gone |
| 3 | Failure path in the shipped suite | **pass** | `RoundGameStub::failing_after_publish` publishes then `bail!`; the test runs the real `run_loop` and a real `hoh` subprocess and asserts no route / round proceeds / explicit `game_endpoint_unavailable`; MP1 reddens it |
| 4 | Scene-start ruling unified | **pass** | both documents carry the verbatim prohibition; the guard (`delivered_materials.rs:157`, `:190`) now checks the prompt; MP4 reddens at the prompt side (`:174`) |
| 5 | Byte claims computed, not handwritten | **pass** | my recompute 52->28 / 23->28 and 52200/52176/52205 etc. match all three blocks; `--emit` and `--check` agree; the Rust test recomputes; MP5 (52->54) reddens |
| 6 | Gates, plants, guards, race | **pass** (one caveat) | clean 465/0/7 exit 0, fmt 0, 330->340 tests no removal, ignored 8 and 7 unchanged, five plants byte-exact, runs/mario/PRD/nested engine unchanged, no new deps, not pushed, three traps reproduced, race 9658/7074/0; caveat R7 (concurrent-cargo flake) |
| 7 | Honesty | **pass** | no real-machine probability, no E1/E3 met, no "fully solved"; R1-R8 accurate; the only omission is D1/D2 |

---

## 2. My plants and counterexamples (all restored byte-exactly)

Driver: `python C:\Users\wyl\AppData\Local\Temp\dr71acc\plants.py apply|restore|verify <id>`; backups in
`...\dr71acc\bak\`. Restore criterion for each: `bytes == backup` (byte comparison), `git hash-object ==
HEAD:<path>`, empty `git status --porcelain -uall -- <path>`, empty `git diff --stat -- <path>`.

| Plant | Where (production) | Disabled mechanism | Result | Restore |
|---|---|---|---|---|
| **MP1** | `src/runtime/run_loop.rs:545-548` | wrapper's `clear_game_endpoint` + `withdraw_game_route` on Err | `round_game_window` **RED**: `tests/round_game_window.rs:441` `RoleProbe { route_exists: true, exit_code: Some(0) }` (the real `hoh` adopted the lying route) | backup byte-equal, `d50638e81f1d == HEAD`, porcelain/diff empty |
| **MP2** | `src/adapter/godot.rs:3898` + `:3919` | round game publishes-before-ready and does not clear on failure (DR-70 shape) | `round_game_start` **RED**: `:262` `the record must not be published before readiness is confirmed; found Ok(...)` | backup byte-equal, `fef2ac7b9299 == HEAD`, `cmp` OK |
| **MP3** | `src/tools/mod.rs:457-462` | publish error mapped back to `let _ = ...; Ok(())` (A5 shape) | `round_game_start` **RED**: `:344` `... not be swallowed: Ok(Some(GameEndpointRecord {...}))` | backup byte-equal, `fdf44b92198a == HEAD` |
| **MP4** | `src/prompts/developer.md:137-143` | prompt contradiction restored (`boot the scene with editor_play_scene`) | `delivered_materials` **RED at the prompt side**: `:174` names `developer.md` | backup byte-equal, `2126a2e64fdf == HEAD` |
| **MP5** | `.../TASK-SMOKE-T9-evidence/REDACTION.md` (generated block) | hand-written `dr69_replaced_bytes = 54` | `byte_claims` **RED**: `tests/byte_claims.rs:250` left `("dr69_replaced_bytes","54")` right `("52")` | backup byte-equal, `bc1fc2ca5bf3 == HEAD`, `cmp` OK |
| **MP2a-only** | `src/adapter/godot.rs:3898` | publish-before-ready but keep the failure-path clear | the ordering test still **passes**; `a_publish_failure_is_reported_instead_of_swallowed` reddens (in-process route left) -> the end-state test cannot see order | backup byte-equal |
| **MP2c** | `src/adapter/godot.rs:3898` | publish early **with** clear-on-failure | **all 8 round-game tests green** -> D2 (no in-poll discriminator on the round path) | backup byte-equal |

Non-mutating external probes (no repo edits; `...\dr70acc\probe`, run with `cargo test --offline`,
CARGO_TARGET_DIR warm, tempdirs only):

* `publish_race.rs` — **9658 reads, 7074 misses (73.2%), 0 corrupt**: content atomic, presence not.
* `dr71_ready_shape.rs` (mine) — the real `GodotAdapter::start_round_game` against a game double answering
  `{"tree":"not a scene tree at all"}`: `ok=true`, `route exists: true` (D1); the real-scene-tree control
  also publishes (`2 passed`).

---

## 3. Independent judgement on each headline question

1. **Does a failed start now leave no route?** Yes, for every failure I can drive. The exact previous case
   (announced endpoint, readiness refused) cannot leave a route because publication is a *separate* step
   placed after the predicate, and `install` cannot write; my MP2 reverting that order reddens the adapter
   test, and MP1 reverting the wrapper reddens the run-level test with the previous acceptance's own symptom.
2. **Does the mechanism close or merely narrow the window?** It **closes** the ordering window at the
   source (nothing is on disk before the predicate is true) and adds a second, adapter-independent
   withdrawal. It **narrows but does not close the readiness predicate**: `start_round_game` treats any
   successful RPC response as ready, so a successful non-scene-tree answer is published where the battery
   would refuse it (D1) - and the ordering itself has no in-poll test on this path (D2).
3. **Are publish failures loud?** Yes. The value is now a result; the adapter fails the start and clears;
   the temp file is cleaned. MP3 shows a hand-revert is caught.
4. **Is the failure path in the shipped suite?** Yes, with a double that genuinely fails *after* publishing,
   the real runtime and the real `hoh` binary, asserting no route / graceful round / explicit refusal.
5. **Is the scene-start ruling unified?** Yes - prompt, skill and the two enforcing tests agree, and the
   audience-aware guard now sees the prompt, which I verified by planting the old contradiction back.
6. **Are the byte claims computed, not handwritten?** Yes. My independent arithmetic matches; the values
   are produced by a script, quoted, and re-derived by a Rust test; a single hand-typed number reddens.
7. **The race.** Real and reproduced (73.2% of reads miss the route). Acceptable given the loss mode is an
   explicit `game_endpoint_unavailable` and the harness is effectively the sole publisher - but it is
   unsynchronised and untested, exactly as the report's R3 says. I agree with the report's judgement.

---

## 4. Digest scheme, self-validation, guard raw output

Scheme (identical to DR-69/DR-70 so values are comparable): Windows PowerShell 5.1
(`powershell.exe -NoProfile`), `Get-ChildItem -Recurse -Force -File`; per file the repo-root-relative
**lowercased POSIX** path + byte length + lowercased SHA256, tab-joined, `\n`-joined, the whole string
UTF-8 hashed with SHA256; line order by `Sort-Object`.

```
runs/smoke-t6 files=135 hash=c144ef3219e21dd322978e41a5531d53dee270619c026585505920f9277a9c03 newest=09/29/2026 02:32:01
runs/smoke-t7 files=115 hash=6e4c1595753c2cdefb16e4d2e5f05242ca202c70c81a93e98ae2b9c92b520fb7 newest=09/29/2026 14:41:14
runs/smoke-t8 files=358 hash=6d11b2c61ec507b5f02525ddc0e7f7adb08763cd2439a4b08788b7fe51bdf5a7 newest=09/30/2026 07:58:28
runs/smoke-t9 files=83  hash=541e2d814e563ba667c95bde49765d05e44cf11aa5ab90b2f44931f30136ca9d newest=09/30/2026 11:27:29
```

**Self-validation:** `runs/smoke-t6` reproduces the required anchor `c144ef32...7a9c03` and t7/t8/t9 match
every prior record. **Write-then-delete:** entries with `LastWriteTime > 2026-09-30 11:27:30` = 0 files /
0 dirs in all four trees (re-run after all plants and probes).

Guards:

```
PRD-mario.md sha256 = 4c81c3a9995f0b3afdf01421a0c3be88573cceefc284ce9bafbfda141f0f5c3a
live .workspace/mario (17 files, excl .hoh/.git/.godot/.import) == runs/smoke-t9/versions/1f3d20ed... (0 differing)
git diff --numstat 95b3f9b..HEAD -- .workspace/mario PRD-mario.md godot-mcp Cargo.toml Cargo.lock -> empty
git diff --numstat 95b3f9b..HEAD -- DECISIONS.md -> 38 added lines (D275 only, written by the coordinator after the batch; no implementation edit)
origin/master = 9aebbe15f13508d1ee5063505b2827ee59cc041a ; git rev-list --count origin/master..HEAD = 29 ; nothing staged/pushed
git status --porcelain -uall = 0 lines ; git diff --stat = 0 lines (audited HEAD 6b31756)
nested: git -C godot-mcp/godot rev-parse HEAD = fc63af77c33368c4a1bb839c95d19750554f63a3 ; porcelain = 0 lines
outer pathspec control: ls-files godot-mcp = 6484 vs ls-files godot-mcp/godot = 0
```

Three false-green traps, reproduced: (1) `git diff --stat -- definitely/not/a/real/path` -> empty,
exit 0, so an empty diff is meaningless before the pathspec is shown to match; (2) `cmd /c "git rev-parse
dc9d350^"` -> `dc9d350dff...` (the caret never reached git) and `cmd /c "... & echo errorlevel=%errorlevel%"`
printed `0` after a fatal (parse-time expansion), while bash gives 0 for the real path and 128 for the fake
one; (3) `git check-ignore -v` shows `runs/`, `.workspace/`, `godot-mcp/godot/` are ignored, so an empty
diff over them proves nothing (hence digests, the nested-repo status and the flat byte comparison).

---

## 5. What I did not check

* Any real-machine behaviour (U1), including whether a real engine accepts a round-wide play/stop sequence
  or returns a successful non-scene-tree readiness answer.
* The implementer's own failure transcripts and gate log (U2); I verified the tests with my own plants and
  reproduced the gate myself.
* The rest of `TASK-SMOKE-T9-evidence/**` (U3); the pre-DR-71 git archaeology (U4); the panic path (U5);
  non-Windows pid liveness (U6); a formal multi-process race analysis (U7); an exhaustive enumeration of
  every route-publishing path (U8).

---

## 6. Advice for the next batch

1. **Give `start_round_game` the battery's readiness check** (D1): after `ready.ok`, require
   `describe_scene_tree_shape` to succeed before publishing, or factor the predicate into one shared
   helper. Otherwise the round path can publish a route the battery would call unconfirmed.
2. **Add an in-poll discriminator to the round-game test** (D2): reuse the battery's `watching`/`sightings`
   pattern (or a concurrent reader) so a publish-early-with-clear reversion cannot pass; my MP2c shows the
   current suite is blind to it.
3. **Make publication presence-atomic if cheap, or document it as accepted**: `remove_file` + `rename`
   leaves a no-file window (my probe: 73.2% of reads). This is only safe because the loss mode is an
   explicit refusal, which should be stated next to the function.
4. **Keep the gate uncontended.** Two agents running `cargo test` in this workspace made the same
   environment-sensitive test fail twice (abnormal exit; `os error 32` sharing violation) while it passes
   3/3 in isolation and the clean full run is 465/0/7. A gate claim is only evidence when nothing else is
   compiling or running tests in the tree.
5. **Do not treat the containment tests as engine evidence.** The real-machine round (SMOKE-T10) should
   record what `editor_play_scene` does on an empty project, whether the round-wide session survives the
   Developer's writes, and what a successful-but-non-tree readiness reply looks like; until then do not
   claim E1/E3 and do not reuse a `running_game_*`-pinned observability plan.
